#!/usr/bin/env python3
"""roadmap-sync.py — el plugin mantiene el roadmap al día por sí mismo (plugin-audit-2 T-42).

Deriva el estado de cada iniciativa de `docs/roadmap/` a partir de los estados de sus tareas y de sus
artefactos, con la tabla de transiciones de `agent-kits/dev-cycle/references/phase6-close.md`
(reglas 7-8 de CONVENTIONS), y lo escribe:

- ledger (`tasks.md`): tareas todas `completado`/`cancelado` → `completado`; alguna empezada → `en-progreso`;
- con la puerta de retro abierta (`retro.md` + fila en `CALIBRATION.md`, `retro-gate.py`) y el ledger
  `completado` → plan `completado` y spec `implementada`;
- spec `aprobada`/`implementada` → evaluación `completado` (la puerta go ya se cruzó);
- la fila de la iniciativa en `docs/roadmap/README.md`: marca `· estado: <etiqueta>` al final de la celda
  «Iniciativa» y enlaces a los artefactos que existen (solo su fila; si falta, la añade; el índice no se crea).

Nunca rebaja un estado: si un artefacto va por delante de lo derivado lo REPORTA (aviso `adelantado`) y no
lo toca. Una iniciativa con el ledger `completado` y sin retro sale como aviso `retro-pendiente` (no es un
desfase: la retro la escribe quien conoce las causas, `/retro`). Idempotente. Reutiliza las primitivas de
`ledger-write.py` (lectura acotada, escritura atómica, cerrojo del ledger) y la puerta de `retro-gate.py`.

Disparadores: `ledger-write.py verdict` (cuando deja el ledger al 100 %), `retro-gate.py --sync`, la puerta
de `/pm-cycle` (`gate`) y, solo para AVISAR, el bloque de sesión de `progress-report.py` (`comprobar`).

Uso:
  roadmap-sync.py <docs/roadmap | docs/roadmap/<fecha>-<slug>> [--check | --dry-run] [--json]
  roadmap-sync.py gate <docs/roadmap/<fecha>-<slug>> --decision go|no-go [--descartar] [--dry-run] [--json]
Exit: 0 ok · 1 `--check` con desfases, cambio no aplicado o puerta ya decidida · 2 uso/E-S.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys
import time

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — streams may not support reconfigure

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, HERE / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


LW = _load("roadmap_sync_ledger_write", "ledger-write.py")
RG = _load("roadmap_sync_retro_gate", "retro-gate.py")
LINT = LW.LINT

# (clave, fichero, etiqueta del enlace en el índice) en el orden canónico de la cadena de artefactos.
ARTEFACTOS = (("spec", "spec.md", "spec"), ("evaluacion", "evaluation.md", "eval"), ("design", "design.md", "design"),
              ("plan", "improvement-plan.md", "plan"), ("ledger", "tasks.md", "tasks"), ("retro", "retro.md", "retro"))
FICHERO = {clave: fichero for clave, fichero, _ in ARTEFACTOS}
RANGO = {"borrador": 0, "aprobado": 0, "aprobada": 0, "en-progreso": 1, "en-revision": 2, "completado": 3}
RANGO_SPEC = {"borrador": 0, "aprobada": 1, "implementada": 2}
TERMINALES = {"cancelado", "obsoleta", "obsoleto"}
PREFIJO = 64 * 1024
MARCA = " · estado: "
SEPARADORES = (" · ", " / ", " ? ")
_TABLA_ESTADO = re.compile(r"^\|[ \t]*(?:\*\*)?Estado(?:\*\*)?[ \t]*\|[ \t]*([^|\n]*?)[ \t]*\|", re.M)
_FM_ESTADO = re.compile(r"^estado:[ \t]*([^\s#]+)", re.M)
_CABECERA_INDICE = re.compile(r"^\|\s*Fecha\s*\|\s*Iniciativa\s*\|")


class SyncError(Exception):
    def __init__(self, status, code=2):
        self.status, self.code = status, code
        super().__init__(status)


# ---------------------------------------------------------------- lectura y campos de estado

def _leer(path):
    """(texto con LF, bom, salto, raw, identidad) o None si no existe. Lectura acotada sin seguir enlaces."""
    if not os.path.lexists(path):
        return None
    if os.lstat(path).st_size > LW.MAX_BYTES:
        # Ledger histórico > 256 KiB: su cabecera basta para leer el estado; no se deriva ni se escribe.
        row = LW.READER.read_text(Path(path).parent, Path(path).name, max_bytes=PREFIJO, prefix=True)
        if row["status"] != "ok":
            raise SyncError(row["status"])
        return {"text": row["text"].replace("\r\n", "\n"), "grande": True, "path": Path(path)}
    raw, identity = LW.IO.read(Path(path), LW.MAX_BYTES, changed_status="conflict")
    text, bom, newline = LW.decode(raw)
    return {"text": text, "bom": bom, "newline": newline, "raw": raw, "identity": identity, "path": Path(path)}


def campos_estado(text):
    """Spans (inicio, fin) del valor de `estado:` del frontmatter y de la fila `| **Estado** |` de la cabecera
    (antes del primer `## `), con el estado leído (el del frontmatter manda)."""
    spans, estado = [], None
    if text.startswith("---\n"):
        fin = re.search(r"^---[ \t]*$", text[4:], re.M)
        if fin:
            m = _FM_ESTADO.search(text, 4, 4 + fin.start())
            if m:
                spans.append(m.span(1))
                estado = LINT.norm_estado(m.group(1))
    seccion = re.search(r"^##[ \t]", text, re.M)
    m = _TABLA_ESTADO.search(text, 0, seccion.start() if seccion else len(text))
    if m and m.group(1).strip():
        spans.append(m.span(1))
        estado = estado or LINT.norm_estado(m.group(1))
    return estado, spans


def con_estado(text, nuevo):
    _, spans = campos_estado(text)
    for inicio, fin in sorted(spans, reverse=True):
        text = text[:inicio] + nuevo + text[fin:]
    return text


def _subir(actual, objetivo, rango):
    """El objetivo solo si SUBE el estado actual (nunca rebaja, nunca toca un terminal ni un desconocido)."""
    if objetivo is None or actual == objetivo or actual in TERMINALES:
        return None
    if actual is None or actual not in rango:
        return None
    return objetivo if rango[objetivo] > rango[actual] else None


def objetivo_ledger(text):
    tareas = LINT.parse_ledger(text)["tareas"]
    estados = [t["estado"] or "borrador" for t in tareas]
    abiertas = [e for e in estados if e not in ("completado", "cancelado")]
    if estados and not abiertas and "completado" in estados:
        return "completado", 0
    if any(e in ("en-progreso", "en-revision", "completado") for e in estados):
        return "en-progreso", len(abiertas)
    return None, len(abiertas)


def titulo_de(text):
    m = re.search(r"^#\s+(.+)$", text, re.M)
    if not m:
        return None
    titulo = re.sub(r"^(?:Checklist de Tareas|Checklist)\s*[—-]\s*", "", m.group(1).strip())
    return titulo.replace("|", "/").strip() or None


# ---------------------------------------------------------------- análisis de una iniciativa

def analizar(carpeta, root):
    """Plan de cambios de UNA iniciativa: {'nombre', 'textos', 'cambios', 'avisos', 'etiqueta', 'enlaces', 'titulo'}."""
    nombre = carpeta.name
    docs, avisos, cambios = {}, [], []
    for clave, fichero, _ in ARTEFACTOS:
        try:
            docs[clave] = _leer(carpeta / fichero)
        except (SyncError, LW.WriteError, OSError, UnicodeError, ValueError) as error:
            docs[clave] = None
            avisos.append({"iniciativa": nombre, "tipo": "ilegible",
                           "detalle": f"{fichero}: {getattr(error, 'status', error.__class__.__name__)}"})
    estados = {clave: (campos_estado(d["text"])[0] if d else None) for clave, d in docs.items()}
    nuevos = dict(estados)

    def proponer(clave, objetivo, rango):
        nuevo = _subir(estados[clave], objetivo, rango)
        if nuevo and docs[clave].get("grande"):
            avisos.append({"iniciativa": nombre, "tipo": "no-escrito",
                           "detalle": f"{FICHERO[clave]} > 256 KiB: debería ser `{nuevo}` (archívalo con ledger-archive.py)"})
        elif nuevo:
            nuevos[clave] = nuevo
            cambios.append({"iniciativa": nombre, "tipo": clave, "artefacto": FICHERO[clave],
                            "de": estados[clave], "a": nuevo})
        elif objetivo and estados[clave] is None and docs[clave]:
            avisos.append({"iniciativa": nombre, "tipo": "sin-estado",
                           "detalle": f"{FICHERO[clave]} sin campo `estado` legible "
                                      f"(debería ser `{objetivo}`)"})

    abiertas = 0
    if docs["ledger"] and not docs["ledger"].get("grande"):
        objetivo, abiertas = objetivo_ledger(docs["ledger"]["text"])
        proponer("ledger", objetivo, RANGO)
        if estados["ledger"] == "completado" and abiertas:
            avisos.append({"iniciativa": nombre, "tipo": "adelantado",
                           "detalle": f"tasks.md `completado` con {abiertas} tarea(s) abiertas: no se rebaja"})
    retro = False
    if nuevos["ledger"] == "completado" and not abiertas:
        retro = RG.veredicto(str(root), str(carpeta))["abierta"]
        if retro:
            proponer("plan", "completado", RANGO)
            proponer("spec", "implementada", RANGO_SPEC)
        else:
            avisos.append({"iniciativa": nombre, "tipo": "retro-pendiente",
                           "detalle": f"ledger `completado` sin retro: /retro docs/roadmap/{nombre}"})
    elif docs["ledger"] and estados["spec"] == "implementada":
        avisos.append({"iniciativa": nombre, "tipo": "adelantado",
                       "detalle": "spec `implementada` con el ledger sin cerrar: no se rebaja"})
    if nuevos["spec"] in ("aprobada", "implementada"):
        proponer("evaluacion", "completado", RANGO)
    return {"nombre": nombre, "docs": docs, "cambios": cambios, "avisos": avisos, "nuevos": nuevos,
            "etiqueta": etiqueta(nuevos, docs, retro),
            "enlaces": [(fichero, label) for clave, fichero, label in ARTEFACTOS if docs.get(clave)],
            "titulo": next((titulo_de(docs[c]["text"]) for c in ("spec", "ledger", "plan", "evaluacion")
                            if docs.get(c) and titulo_de(docs[c]["text"])), None)}


def etiqueta(estados, docs, retro):
    if estados["ledger"] == "cancelado" or estados["evaluacion"] == "cancelado" or estados["spec"] == "obsoleta":
        return "cancelada"
    if estados["ledger"] == "completado":
        return "cerrada" if retro else "completada, retro pendiente"
    if estados["ledger"] in ("en-progreso", "en-revision"):
        return "en curso"
    if docs.get("plan") or docs.get("ledger"):
        return "planificada"
    if docs.get("evaluacion"):
        return "evaluada"
    return "solo spec" if docs.get("spec") else None


# ---------------------------------------------------------------- índice docs/roadmap/README.md

def _celdas(linea):
    return LINT.split_fila_md(linea)


def _fila(celdas):
    return "| " + " | ".join(celdas) + " |"


def editar_indice(text, planes):
    """(texto nuevo, cambios) con la fila de cada iniciativa al día; el resto del índice intacto."""
    lineas = text.split("\n")
    cabecera = next((i for i, l in enumerate(lineas) if _CABECERA_INDICE.match(l)), None)
    if cabecera is None or cabecera + 1 >= len(lineas):
        return text, [], ["README.md sin tabla `| Fecha | Iniciativa |`"]
    columnas = len(_celdas(lineas[cabecera]))
    cambios = []
    for plan in planes:
        if not plan["etiqueta"]:
            continue
        nombre = plan["nombre"]
        fila_i = next((i for i, l in enumerate(lineas) if l.startswith("|") and f"({nombre}/" in l), None)
        enlaces = [(f, label) for f, label in plan["enlaces"]]
        if fila_i is None:
            titulo = plan["titulo"] or nombre[11:]
            celdas = [nombre[:10], f"{nombre[11:]} — {titulo}{MARCA}{plan['etiqueta']}"]
            celdas += ["No estimado", "No medido"][:max(columnas - 3, 0)] + ["—"] * max(columnas - 5, 0)
            celdas.append(" · ".join(f"[{label}]({nombre}/{f})" for f, label in enlaces))
            lineas.insert(cabecera + 2, _fila(celdas))
            cambios.append({"iniciativa": nombre, "tipo": "indice", "artefacto": "README.md",
                            "de": "sin fila", "a": plan["etiqueta"]})
            continue
        celdas = _celdas(lineas[fila_i])
        if len(celdas) < 3:
            continue
        actual = celdas[1]
        corte = actual.rfind(MARCA)
        previa = actual[corte + len(MARCA):] if corte >= 0 else None
        celdas[1] = (actual[:corte] if corte >= 0 else actual) + MARCA + plan["etiqueta"]
        faltan = [(f, label) for f, label in enlaces if f"({nombre}/{f})" not in lineas[fila_i]]
        if faltan:
            ultima = celdas[-1]
            sep = next((s for s in SEPARADORES if s in ultima), " · ")
            nuevos = sep.join(f"[{label}]({nombre}/{f})" for f, label in faltan)
            celdas[-1] = nuevos if ultima in ("", "—", "-") else ultima + sep + nuevos
        nueva = _fila(celdas)
        if nueva != lineas[fila_i]:
            lineas[fila_i] = nueva
            de = previa if previa is not None else "sin marca"
            if faltan:
                de += " · faltan " + ", ".join(label for _, label in faltan)
            cambios.append({"iniciativa": nombre, "tipo": "indice", "artefacto": "README.md",
                            "de": de, "a": plan["etiqueta"]})
    return "\n".join(lineas), cambios, []


# ---------------------------------------------------------------- escritura

def _escribir(doc, nuevo_texto, deadline, ledger=False):
    output = doc["bom"] + nuevo_texto.replace("\n", doc["newline"]).encode("utf-8")
    if output == doc["raw"]:
        return
    path = doc["path"]

    def publicar():
        raw, identity = LW.IO.read(path, LW.MAX_BYTES, changed_status="conflict")
        if raw != doc["raw"]:
            raise SyncError("conflict", 1)
        mode = path.lstat().st_mode & 0o777 if os.name != "nt" else None
        LW.IO.write(path, output, deadline, expected=identity, mode=mode)

    if not ledger:
        publicar()
        return
    state = path.parent / ".ledger-write"     # el mismo cerrojo cooperativo que ledger-write.py
    state.mkdir(exist_ok=True)
    with LW.IO.locked(state, deadline, True, wait=2):
        try:
            with (state / ".gitignore").open("xb") as handle:
                handle.write(b"*\n")
        except FileExistsError:
            pass
        publicar()


def _carpetas(objetivo):
    """(raíz del proyecto, [carpetas de iniciativa]) desde `docs/roadmap` o una carpeta de iniciativa."""
    objetivo = Path(os.path.abspath(objetivo))
    if not objetivo.is_dir() or objetivo.is_symlink():
        raise SyncError("not_found")
    if objetivo.name == "roadmap" and objetivo.parent.name == "docs":
        carpetas = []
        for entrada in sorted(os.scandir(objetivo), key=lambda e: e.name):
            if not LINT.INITIATIVE_FOLDER.fullmatch(entrada.name):
                continue
            info = os.lstat(entrada.path)
            if stat.S_ISDIR(info.st_mode) and not LW.READER._redirected(info):
                carpetas.append(Path(entrada.path))
        return objetivo.parent.parent, carpetas
    root = RG.raiz_de(str(objetivo))
    if root is None or not LINT.INITIATIVE_FOLDER.fullmatch(objetivo.name):
        raise SyncError("not_initiative")
    return Path(root), [objetivo]


def sincronizar(objetivo, *, escribir=True, deadline=None):
    """Analiza (y, con `escribir`, aplica) la sincronización. Devuelve el informe (dict)."""
    deadline = deadline or time.monotonic() + 20
    root, carpetas = _carpetas(objetivo)
    planes = [p for p in (analizar(c, root) for c in carpetas)
              if any(p["docs"].get(k) for k in ("spec", "evaluacion", "plan", "ledger"))]
    desfases = [c for p in planes for c in p["cambios"]]
    avisos = [a for p in planes for a in p["avisos"]]
    indice_path = root / "docs" / "roadmap" / "README.md"
    indice, indice_nuevo = None, None
    try:
        indice = _leer(indice_path)
    except (LW.WriteError, OSError, UnicodeError, ValueError):
        avisos.append({"iniciativa": "-", "tipo": "ilegible", "detalle": "docs/roadmap/README.md"})
    if indice is not None:
        indice_nuevo, cambios_indice, problemas = editar_indice(indice["text"], planes)
        desfases += cambios_indice
        avisos += [{"iniciativa": "-", "tipo": "indice", "detalle": p} for p in problemas]
    pendientes = []
    if escribir:
        for p in planes:
            for clave, fichero, _ in ARTEFACTOS:
                if p["docs"].get(clave) and p["nuevos"][clave] != campos_estado(p["docs"][clave]["text"])[0] \
                        and any(c["artefacto"] == fichero for c in p["cambios"]):
                    try:
                        _escribir(p["docs"][clave], con_estado(p["docs"][clave]["text"], p["nuevos"][clave]),
                                  deadline, ledger=clave == "ledger")
                    except (SyncError, LW.WriteError, OSError) as error:
                        pendientes.append(f"{p['nombre']}/{fichero}: {getattr(error, 'status', 'unavailable')}")
        if indice is not None and indice_nuevo != indice["text"]:
            try:
                _escribir(indice, indice_nuevo, deadline)
            except (SyncError, LW.WriteError, OSError) as error:
                pendientes.append(f"README.md: {getattr(error, 'status', 'unavailable')}")
    avisos += [{"iniciativa": "-", "tipo": "no-escrito", "detalle": p} for p in pendientes]
    return {"schema_version": 1, "status": "ok", "desfases": desfases, "avisos": avisos,
            "cambios": desfases, "changed": bool(escribir and desfases and not pendientes),
            "pendientes": pendientes, "iniciativas": len(planes)}


def comprobar(root_proyecto, deadline=None):
    """Solo lectura (para el bloque de sesión): el mismo análisis, sin escribir nada."""
    return sincronizar(Path(root_proyecto) / "docs" / "roadmap", escribir=False, deadline=deadline)


# ---------------------------------------------------------------- puerta de /pm-cycle

def puerta(carpeta, decision, descartar=False, escribir=True):
    """Transición de la puerta go/no-go de `/pm-cycle` (spec + evaluación) y fila del índice."""
    root, (carpeta,) = _carpetas(carpeta)
    spec, ev = _leer(carpeta / "spec.md"), _leer(carpeta / "evaluation.md")
    if spec is None or ev is None:
        raise SyncError("missing_spec_or_evaluation")
    s_est, e_est = campos_estado(spec["text"])[0], campos_estado(ev["text"])[0]
    if decision == "go":
        if e_est == "cancelado" or s_est == "obsoleta":
            raise SyncError("decision_already_taken", 1)
        objetivos = {"evaluacion": "completado", "spec": s_est if s_est in ("aprobada", "implementada") else "aprobada"}
    else:
        if e_est == "completado" or s_est == "implementada":
            raise SyncError("decision_already_taken", 1)
        objetivos = {"evaluacion": "cancelado", "spec": "obsoleta" if descartar else s_est}
    cambios = []
    for clave, doc, actual in (("spec", spec, s_est), ("evaluacion", ev, e_est)):
        if objetivos[clave] and objetivos[clave] != actual:
            cambios.append({"iniciativa": carpeta.name, "tipo": clave, "artefacto": doc["path"].name,
                            "de": actual, "a": objetivos[clave]})
            if escribir:
                _escribir(doc, con_estado(doc["text"], objetivos[clave]), time.monotonic() + 10)
    informe = sincronizar(carpeta, escribir=escribir)
    informe["desfases"] = cambios + informe["desfases"]
    informe["cambios"] = informe["desfases"]
    informe["changed"] = bool(escribir and informe["cambios"])
    return informe


# ---------------------------------------------------------------- CLI

def _texto(informe, check):
    verbo = "desfase" if check else "sincronizado"
    out = [f"{verbo} {c['tipo']}: {c['iniciativa']} {c['artefacto']} {c['de']} → {c['a']}" for c in informe["desfases"]]
    out += [f"aviso {a['tipo']}: {a['iniciativa']} — {a['detalle']}" for a in informe["avisos"]]
    retro = sum(a["tipo"] == "retro-pendiente" for a in informe["avisos"])
    out.append(f"roadmap-sync: {len(informe['desfases'])} desfase(s) · {retro} retro(s) pendiente(s) · "
               f"{len(informe['avisos']) - retro} aviso(s) más · {informe['iniciativas']} iniciativa(s)")
    return "\n".join(out)


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    gate = bool(argv) and argv[0] == "gate"
    parser = argparse.ArgumentParser(prog="roadmap-sync.py" + (" gate" if gate else ""),
                                     description=__doc__.splitlines()[0])
    parser.add_argument("objetivo", help="docs/roadmap o docs/roadmap/<fecha>-<slug>")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    if gate:
        parser.add_argument("--decision", choices=("go", "no-go"), required=True)
        parser.add_argument("--descartar", action="store_true", help="no-go: la spec pasa a `obsoleta`")
    else:
        parser.add_argument("--check", action="store_true", help="solo comprobar: exit 1 si hay desfases")
    args = parser.parse_args(argv[1:] if gate else argv)
    check = not gate and args.check
    try:
        if gate:
            informe = puerta(args.objetivo, args.decision, args.descartar, escribir=not args.dry_run)
        else:
            informe = sincronizar(args.objetivo, escribir=not (check or args.dry_run))
        if check:
            informe["cambios"] = []
        code = 1 if (check and informe["desfases"]) or informe["pendientes"] else 0
    except SyncError as error:
        informe, code = {"schema_version": 1, "status": error.status}, error.code
    except (LW.WriteError, OSError, UnicodeError, ValueError) as error:
        informe, code = {"schema_version": 1, "status": getattr(error, "status", "unavailable")}, 2
    informe["dry_run"], informe["check"] = args.dry_run, check
    if args.json:
        print(json.dumps(informe, ensure_ascii=False, sort_keys=True))
    elif informe.get("status") == "ok":
        print(_texto(informe, check or args.dry_run))
    else:
        print(f"roadmap-sync: {informe['status']}", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
