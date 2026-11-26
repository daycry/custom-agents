#!/usr/bin/env python3
"""roadmap-sync.py — el plugin mantiene el roadmap al día por sí mismo (plugin-audit-2 T-42).

Deriva el estado de cada iniciativa de `docs/roadmap/` a partir de los estados de sus tareas y de sus
artefactos, con la tabla de transiciones de `agent-kits/dev-cycle/references/phase6-close.md`
(reglas 7-8 de CONVENTIONS), y lo escribe:

- ledger (`tasks.md`): alguna tarea empezada → `en-progreso`; tareas todas `completado`/`cancelado` →
  `completado` SOLO con `--cerrar` (Fase 6 de `/dev-cycle`, tras qa verde: el veredicto de la Fase 3 no
  cierra el ledger). Sin `--cerrar`, un ledger al 100 % sale como aviso `cierre-pendiente`. Si un ledger
  `completado` tiene una tarea reabierta (qa en rojo), vuelve a `en-progreso`: única excepción a «nunca
  rebaja», con la tarea reabierta como evidencia (`motivo: reabierta`);
- con la puerta de retro abierta (`retro.md` + fila en `CALIBRATION.md`, `retro-gate.py`) y el ledger
  `completado` → plan `completado` y spec `implementada`;
- la evaluación NO se deriva: solo la puerta go/no-go (`gate`) la pasa a `completado`/`cancelado`;
- la fila de la iniciativa en `docs/roadmap/README.md` (dueño único de esa fila): la que enlaza a su carpeta
  en la última columna (Artefactos); marca `· estado: <etiqueta>` en la celda «Iniciativa» (solo el valor
  de la marca: el texto del autor se conserva) y enlaces a los artefactos que existen. Si falta, la añade;
  con dos filas candidatas avisa y no escribe; el índice no se crea.

Solo se sustituye el TOKEN de estado (frontmatter `estado:` y celda `| Estado |` de la cabecera): el resto
de la celda, las comillas y los comentarios se conservan; una fila cabecera `| Estado | Significado |` no
se toca y una celda sin estado reconocible es un aviso. Nunca rebaja un estado (salvo la tarea reabierta):
lo que va por delante sale como aviso `adelantado`. Un ledger `completado` sin retro es aviso
`retro-pendiente` (no desfase: la retro la escribe `/retro`). Idempotente. Reutiliza las primitivas de
`ledger-write.py` (escritura atómica, cerrojo del ledger, parser) y la puerta de `retro-gate.py`.

Disparadores: `ledger-write.py verdict` (cuando deja las tareas al 100 %), `retro-gate.py --sync`, la
puerta go/no-go de `/pm-cycle` y `/dev-cycle` (`gate`), la Fase 6 (`--cerrar`) y, solo para AVISAR, el
bloque de sesión de `progress-report.py` (`comprobar`: caché por firma, 128 carpetas, plazo).

Uso:
  roadmap-sync.py <docs/roadmap | docs/roadmap/<fecha>-<slug>> [--check | --dry-run] [--json]
  roadmap-sync.py docs/roadmap/<fecha>-<slug> --cerrar [--dry-run] [--json]
  roadmap-sync.py gate <docs/roadmap/<fecha>-<slug>> --decision go|no-go [--descartar] [--dry-run] [--json]
Exit: 0 ok · 1 `--check` con desfases, cambio no aplicado, puerta ya decidida o `--cerrar` con tareas
abiertas · 2 uso/E-S · 3 `gate` a medias (escrito un artefacto y no el otro: `escritos`/`no_escritos`).
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
_TOKEN = re.compile(r"(?<![\w-])(en-progreso|en-revision|completado|cancelado|borrador|aprobada|aprobado|"
                    r"implementada|obsoleta|obsoleto)(?![\w-])")
_TABLA_ESTADO = re.compile(r"^\|[ \t]*(?:\*\*)?Estado(?:\*\*)?[ \t]*\|([^|\n]*)\|", re.M)
_SEPARADOR_TABLA = re.compile(r"^\|?[ \t]*:?-{3,}:?[ \t]*(?:\|[ \t]*:?-{3,}:?[ \t]*)*\|?[ \t]*$")
_FM_ESTADO = re.compile(r"^estado:[ \t]*([^\s#]+)", re.M)
_CABECERA_INDICE = re.compile(r"^\|\s*Fecha\s*\|\s*Iniciativa\s*\|")
_ENLACE_CARPETA = re.compile(r"\((\d{4}-\d{2}-\d{2}-[^/)\s]+)/")
_ESCAPADO = "\x00"

# Comprobación de sesión (gap 6 del fix1): mismo tope que la instantánea de progress-report, caché por firma
# en el estado privado del proyecto (`.claude/`, como `skill-index.py`; nunca dentro de `docs/`).
TOPE_SESION = 128
PLAZO_SESION = 2.0
CACHE_NOMBRE = ".roadmap-sync.cache"
CACHE_VERSION = 2


class SyncError(Exception):
    def __init__(self, status, code=2, **extra):
        self.status, self.code, self.extra = status, code, extra
        super().__init__(status)


# ---------------------------------------------------------------- lectura y campos de estado

def _leer(path):
    """(texto con LF, bom, salto, raw) o None si no existe. Lectura simple y acotada: un `lstat` del propio
    fichero (no se siguen enlaces) y una lectura de, como mucho, 256 KiB + 1. La escritura vuelve a leer con
    la identidad completa de `ledger-write.py` antes de publicar."""
    path = Path(path)
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return None
    if LW.READER._redirected(info) or not stat.S_ISREG(info.st_mode):
        raise SyncError("redirected_path")
    with open(path, "rb") as handle:
        raw = handle.read(LW.MAX_BYTES + 1)
    if len(raw) > LW.MAX_BYTES:
        # Fichero > 256 KiB: su cabecera basta para leer el estado; no se deriva ni se escribe.
        texto = raw[:PREFIJO].decode("utf-8", errors="replace").lstrip("﻿").replace("\r\n", "\n")
        return {"text": texto, "grande": True, "path": path}
    text, bom, newline = LW.decode(raw)
    return {"text": text, "bom": bom, "newline": newline, "raw": raw, "path": path}


def _es_separador(text, desde):
    """¿La línea siguiente a la que contiene `desde` es un separador `|---|---|`? (fila cabecera)."""
    fin = text.find("\n", desde)
    if fin < 0:
        return False
    siguiente = text[fin + 1:text.find("\n", fin + 1) if text.find("\n", fin + 1) >= 0 else len(text)]
    return bool(_SEPARADOR_TABLA.match(siguiente.strip())) and "-" in siguiente


def campos(text):
    """{'estado', 'spans', 'sin_token'}: spans (inicio, fin) del TOKEN de estado del frontmatter y de la primera
    fila `| Estado |` de datos antes del primer `## ` (el frontmatter manda). Una fila cabecera (seguida de
    `|---|`) no cuenta; una celda sin token reconocible marca `sin_token` y no se toca."""
    spans, estado, sin_token = [], None, False
    if text.startswith("---\n"):
        fin = re.search(r"^---[ \t]*$", text[4:], re.M)
        if fin:
            m = _FM_ESTADO.search(text, 4, 4 + fin.start())
            if m:
                token = _TOKEN.search(m.group(1))
                if token:
                    spans.append((m.start(1) + token.start(1), m.start(1) + token.end(1)))
                    estado = token.group(1)
                else:
                    estado = LINT.norm_estado(m.group(1)) or None
    seccion = re.search(r"^##[ \t]", text, re.M)
    for m in _TABLA_ESTADO.finditer(text, 0, seccion.start() if seccion else len(text)):
        if _es_separador(text, m.start()) or not m.group(1).strip():
            continue
        token = _TOKEN.search(m.group(1))
        if token:
            spans.append((m.start(1) + token.start(1), m.start(1) + token.end(1)))
            estado = estado or token.group(1)
        else:
            sin_token = True
            estado = estado or LINT.norm_estado(m.group(1)) or None
        break
    return {"estado": estado, "spans": spans, "sin_token": sin_token}


def campos_estado(text):
    """(estado, spans) — compatibilidad: ver `campos`."""
    info = campos(text)
    return info["estado"], info["spans"]


def con_estado(text, nuevo):
    """El texto con SOLO los tokens de estado sustituidos por `nuevo`."""
    for inicio, fin in sorted(campos(text)["spans"], reverse=True):
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

def analizar(carpeta, root, cerrar=False):
    """Plan de cambios de UNA iniciativa (ver `_resumen` para la parte serializable)."""
    nombre = carpeta.name
    docs, avisos, cambios = {}, [], []
    for clave, fichero, _ in ARTEFACTOS:
        try:
            docs[clave] = _leer(carpeta / fichero)
        except (SyncError, LW.WriteError, OSError, UnicodeError, ValueError) as error:
            docs[clave] = None
            avisos.append({"iniciativa": nombre, "tipo": "ilegible",
                           "detalle": f"{fichero}: {getattr(error, 'status', error.__class__.__name__)}"})
    info = {clave: (campos(d["text"]) if d else None) for clave, d in docs.items()}
    estados = {clave: (i["estado"] if i else None) for clave, i in info.items()}
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
            if info[clave]["sin_token"]:
                avisos.append({"iniciativa": nombre, "tipo": "sin-estado",
                               "detalle": f"{FICHERO[clave]}: celda `| Estado |` sin estado reconocible; "
                                          f"no se toca (debería ser `{nuevo}`)"})
        elif objetivo and docs[clave] and estados[clave] != objetivo and (
                estados[clave] is None or (estados[clave] not in rango and estados[clave] not in TERMINALES)):
            avisos.append({"iniciativa": nombre, "tipo": "sin-estado",
                           "detalle": f"{FICHERO[clave]} sin campo `estado` legible "
                                      f"(debería ser `{objetivo}`)"})

    ledger, cerrable = docs["ledger"], False
    # Un ledger > 256 KiB no se deriva: su cabecera `completado` se acepta tal cual (ya cerrado y archivable).
    cerrado = bool(ledger and ledger.get("grande") and estados["ledger"] == "completado")
    if ledger and ledger.get("grande"):
        if estados["ledger"] not in ("completado", "cancelado"):
            avisos.append({"iniciativa": nombre, "tipo": "no-escrito",
                           "detalle": "tasks.md > 256 KiB: estado de la iniciativa no derivado "
                                      "(archívalo con ledger-archive.py)"})
    elif ledger:
        objetivo, abiertas = objetivo_ledger(ledger["text"])
        cerrable = objetivo == "completado"
        if estados["ledger"] == "completado" and abiertas:
            # Excepción documentada a «nunca rebaja»: una tarea reabierta (qa en rojo) es la evidencia.
            if info["ledger"]["spans"]:
                nuevos["ledger"] = "en-progreso"
                cambios.append({"iniciativa": nombre, "tipo": "ledger", "artefacto": "tasks.md",
                                "de": "completado", "a": "en-progreso", "motivo": "reabierta"})
        elif cerrable and not cerrar:
            proponer("ledger", "en-progreso", RANGO)
            if estados["ledger"] not in ("completado",) and estados["ledger"] not in TERMINALES:
                avisos.append({"iniciativa": nombre, "tipo": "cierre-pendiente",
                               "detalle": f"tareas al 100 %: el cierre lo autoriza la Fase 6 "
                                          f"(roadmap-sync.py docs/roadmap/{nombre} --cerrar)"})
        else:
            proponer("ledger", objetivo, RANGO)
    cerrado = cerrado or (cerrable and nuevos["ledger"] == "completado")
    retro = bool(cerrable or cerrado) and bool(RG.veredicto(str(root), str(carpeta))["abierta"])
    if cerrado:
        if retro:
            proponer("plan", "completado", RANGO)
            proponer("spec", "implementada", RANGO_SPEC)
        else:
            avisos.append({"iniciativa": nombre, "tipo": "retro-pendiente",
                           "detalle": f"ledger `completado` sin retro: /retro docs/roadmap/{nombre}"})
    elif ledger and estados["spec"] == "implementada" and nuevos["ledger"] != "completado":
        avisos.append({"iniciativa": nombre, "tipo": "adelantado",
                       "detalle": "spec `implementada` con el ledger sin cerrar: no se rebaja"})
    return {"nombre": nombre, "docs": docs, "cambios": cambios, "avisos": avisos, "nuevos": nuevos,
            "cerrable": cerrable, "retro": retro,
            "etiqueta": etiqueta(nuevos, docs, retro),
            "enlaces": [[fichero, label] for clave, fichero, label in ARTEFACTOS if docs.get(clave)],
            "titulo": next((titulo_de(docs[c]["text"]) for c in ("spec", "ledger", "plan", "evaluacion")
                            if docs.get(c) and titulo_de(docs[c]["text"])), None),
            "vigente": any(docs.get(k) for k in ("spec", "evaluacion", "plan", "ledger"))}


def _resumen(plan):
    """La parte serializable de un plan (la que guarda la caché de la comprobación de sesión)."""
    return {k: plan[k] for k in ("nombre", "cambios", "avisos", "etiqueta", "enlaces", "titulo", "retro",
                                 "cerrable", "vigente")}


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
    """Celdas de una fila; un `\\|` escapado no parte la celda (gap 7)."""
    return [c.replace(_ESCAPADO, "\\|") for c in LINT.split_fila_md(linea.replace("\\|", _ESCAPADO))]


def _fila(celdas):
    return "| " + " | ".join(celdas) + " |"


def _con_marca(actual, valor):
    """(celda con la marca al día, marca previa o None): solo cambia el VALOR de la marca; el texto que la
    sigue (` · …`) se conserva (gap 9)."""
    corte = actual.rfind(MARCA)
    if corte < 0:
        return actual + MARCA + valor, None
    resto = actual[corte + len(MARCA):]
    fin = resto.find(" · ")
    previa, cola = (resto, "") if fin < 0 else (resto[:fin], resto[fin:])
    return actual[:corte] + MARCA + valor + cola, previa


def editar_indice(text, planes):
    """(texto nuevo, cambios, avisos) con la fila de cada iniciativa al día; el resto del índice intacto.
    La fila propia es la que enlaza a la carpeta en la ÚLTIMA columna (Artefactos), no la primera que la cita."""
    lineas = text.split("\n")
    cabecera = next((i for i, l in enumerate(lineas) if _CABECERA_INDICE.match(l)), None)
    if cabecera is None or cabecera + 1 >= len(lineas):
        return text, [], ["README.md sin tabla `| Fecha | Iniciativa |`"]
    columnas = len(_celdas(lineas[cabecera]))
    filas = {}
    i = cabecera + 2
    while i < len(lineas) and lineas[i].startswith("|"):
        for nombre in set(_ENLACE_CARPETA.findall(_celdas(lineas[i])[-1])):
            filas.setdefault(nombre, []).append(i)
        i += 1
    cambios, problemas, nuevas = [], [], []
    for plan in planes:
        if not plan["etiqueta"]:
            continue
        nombre = plan["nombre"]
        enlaces = [(f, label) for f, label in plan["enlaces"]]
        propias = filas.get(nombre, [])
        if len(propias) > 1:
            problemas.append(f"{nombre}: {len(propias)} filas enlazan a la carpeta en Artefactos; no se escribe")
            continue
        if not propias:
            titulo = plan["titulo"] or nombre[11:]
            celdas = [nombre[:10], f"{nombre[11:]} — {titulo}{MARCA}{plan['etiqueta']}"]
            celdas += ["No estimado", "No medido"][:max(columnas - 3, 0)] + ["—"] * max(columnas - 5, 0)
            celdas.append(" · ".join(f"[{label}]({nombre}/{f})" for f, label in enlaces))
            nuevas.append(_fila(celdas))
            cambios.append({"iniciativa": nombre, "tipo": "indice", "artefacto": "README.md",
                            "de": "sin fila", "a": plan["etiqueta"]})
            continue
        fila_i = propias[0]
        celdas = _celdas(lineas[fila_i])
        if len(celdas) < 3:
            continue
        celdas[1], previa = _con_marca(celdas[1], plan["etiqueta"])
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
    if nuevas:
        lineas[cabecera + 2:cabecera + 2] = list(reversed(nuevas))
    return "\n".join(lineas), cambios, problemas


# ---------------------------------------------------------------- escritura

def _escribir(doc, nuevo_texto, deadline, ledger=False):
    """Publica `nuevo_texto` si cambia; devuelve los bytes escritos (None si no hubo cambio)."""
    output = doc["bom"] + nuevo_texto.replace("\n", doc["newline"]).encode("utf-8")
    if output == doc["raw"]:
        return None
    path = doc["path"]

    def publicar():
        raw, identity = LW.IO.read(path, LW.MAX_BYTES, changed_status="conflict")
        if raw != doc["raw"]:
            raise SyncError("conflict", 1)
        mode = path.lstat().st_mode & 0o777 if os.name != "nt" else None
        LW.IO.write(path, output, deadline, expected=identity, mode=mode)

    if not ledger:
        publicar()
        return output
    state = path.parent / ".ledger-write"     # el mismo cerrojo cooperativo que ledger-write.py
    state.mkdir(exist_ok=True)
    with LW.IO.locked(state, deadline, True, wait=2):
        try:
            with (state / ".gitignore").open("xb") as handle:
                handle.write(b"*\n")
        except FileExistsError:
            pass
        publicar()
    return output


def _restaurar(doc, escrito, deadline):
    """Devuelve `doc` a sus bytes originales si nadie lo tocó tras escribir `escrito` (gap 10)."""
    path = doc["path"]
    raw, identity = LW.IO.read(path, LW.MAX_BYTES, changed_status="conflict")
    if raw != escrito:
        raise SyncError("conflict", 1)
    mode = path.lstat().st_mode & 0o777 if os.name != "nt" else None
    LW.IO.write(path, doc["raw"], deadline, expected=identity, mode=mode)


def _escribir_todos(salidas, deadline):
    """Todo o nada: si falla uno, restaura los ya escritos; si no puede, `partial` (exit 3) con el detalle."""
    escritos = []
    for n, (doc, texto) in enumerate(salidas):
        try:
            output = _escribir(doc, texto, deadline)
        except (SyncError, LW.WriteError, OSError) as error:
            sin_restaurar = []
            for previo, bytes_escritos in reversed(escritos):
                try:
                    _restaurar(previo, bytes_escritos, deadline)
                except (SyncError, LW.WriteError, OSError):
                    sin_restaurar.append(previo["path"].name)
            if sin_restaurar:
                raise SyncError("partial", 3, escritos=sorted(sin_restaurar),
                                no_escritos=[d["path"].name for d, _ in salidas[n:]]) from error
            raise SyncError(getattr(error, "status", "unavailable"), 1) from error
        if output is not None:
            escritos.append((doc, output))


def _carpetas(objetivo):
    """(raíz del proyecto, [carpetas de iniciativa], ¿es docs/roadmap?) desde `docs/roadmap` o una carpeta."""
    objetivo = Path(os.path.abspath(objetivo))
    if not objetivo.is_dir() or objetivo.is_symlink():
        raise SyncError("not_found")
    if objetivo.name == "roadmap" and objetivo.parent.name == "docs":
        return objetivo.parent.parent, [objetivo / n for n in _nombres(objetivo)], True
    root = RG.raiz_de(str(objetivo))
    if root is None or not LINT.INITIATIVE_FOLDER.fullmatch(objetivo.name):
        raise SyncError("not_initiative")
    return Path(root), [objetivo], False


def _nombres(roadmap):
    nombres = []
    for entrada in os.scandir(roadmap):
        if not LINT.INITIATIVE_FOLDER.fullmatch(entrada.name):
            continue
        info = os.lstat(entrada.path)
        if stat.S_ISDIR(info.st_mode) and not LW.READER._redirected(info):
            nombres.append(entrada.name)
    return sorted(nombres)


def _indice(root, planes, avisos):
    """(doc del índice o None, texto nuevo, cambios) — degrada con aviso si falta, es ilegible o > 256 KiB."""
    try:
        indice = _leer(root / "docs" / "roadmap" / "README.md")
    except (SyncError, LW.WriteError, OSError, UnicodeError, ValueError):
        avisos.append({"iniciativa": "-", "tipo": "ilegible", "detalle": "docs/roadmap/README.md"})
        return None, None, []
    if indice is None:
        return None, None, []
    if indice.get("grande"):
        avisos.append({"iniciativa": "-", "tipo": "no-escrito",
                       "detalle": "docs/roadmap/README.md > 256 KiB: índice no actualizado (divídelo o archívalo)"})
        return None, None, []
    texto, cambios, problemas = editar_indice(indice["text"], planes)
    avisos += [{"iniciativa": "-", "tipo": "indice", "detalle": p} for p in problemas]
    return indice, texto, cambios


def _informe(planes, desfases, avisos, pendientes, escribir, **extra):
    informe = {"schema_version": 1, "status": "ok", "desfases": desfases, "avisos": avisos,
               "cambios": desfases, "changed": bool(escribir and desfases and not pendientes),
               "pendientes": pendientes, "iniciativas": len(planes),
               "retro_abiertas": sorted(p["nombre"] for p in planes if p["retro"]),
               "omitida": False, "recortadas": 0}
    informe.update(extra)
    return informe


def sincronizar(objetivo, *, escribir=True, deadline=None, cerrar=False):
    """Analiza (y, con `escribir`, aplica) la sincronización. Devuelve el informe (dict)."""
    deadline = deadline or time.monotonic() + 20
    root, carpetas, es_roadmap = _carpetas(objetivo)
    if cerrar and es_roadmap:
        raise SyncError("cerrar_needs_initiative", 2)
    planes = [p for p in (analizar(c, root, cerrar=cerrar) for c in carpetas) if p["vigente"]]
    if cerrar:
        plan = planes[0] if planes else None
        if plan is None or not plan["docs"].get("ledger"):
            raise SyncError("not_found", 2)
        if plan["docs"]["ledger"].get("grande"):
            raise SyncError("too_large", 1)
        if not plan["cerrable"]:
            raise SyncError("open_tasks", 1)
    desfases = [c for p in planes for c in p["cambios"]]
    avisos = [a for p in planes for a in p["avisos"]]
    indice, indice_nuevo, cambios_indice = _indice(root, planes, avisos)
    desfases += cambios_indice
    pendientes = []
    if escribir:
        for p in planes:
            for clave, fichero, _ in ARTEFACTOS:
                if p["docs"].get(clave) and any(c["artefacto"] == fichero for c in p["cambios"]):
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
    return _informe(planes, desfases, avisos, pendientes, escribir)


# ---------------------------------------------------------------- comprobación de sesión (solo lectura)

def _firma(path):
    try:
        info = os.lstat(path)
    except OSError:
        return None
    return [info.st_mtime_ns, info.st_size]


def _leer_cache(path, clave):
    try:
        with open(path, encoding="utf-8") as handle:
            datos = json.load(handle)
    except (OSError, ValueError):
        return {}
    if not isinstance(datos, dict) or datos.get("version") != CACHE_VERSION or datos.get("clave") != clave:
        return {}
    inic = datos.get("inic")
    return inic if isinstance(inic, dict) else {}


def _escribir_cache(path, clave, inic):
    """Solo si el proyecto ya tiene `.claude/` (como `skill-index.py`); nunca bajo `docs/`. Degrada callado."""
    if not path.parent.is_dir():
        return
    tmp = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as handle:
            json.dump({"version": CACHE_VERSION, "clave": clave, "inic": inic}, handle, ensure_ascii=False)
        os.replace(tmp, path)
    except OSError:
        try:
            os.unlink(tmp)
        except OSError:
            pass


def comprobar(root_proyecto, deadline=None, tope=TOPE_SESION):
    """Solo lectura (bloque de sesión): el mismo análisis, acotado. Las `tope` carpetas más recientes; caché
    por firma (ruta + `mtime_ns` + tamaño de cada artefacto, y la de `CALIBRATION.md`): solo se reanaliza la
    iniciativa cuya firma cambió; con el plazo vencido lo pendiente se omite (`omitida`) sin romper nada."""
    root = Path(os.path.abspath(str(root_proyecto)))
    roadmap = root / "docs" / "roadmap"
    limite = time.monotonic() + PLAZO_SESION if deadline is None else deadline
    nombres = _nombres(roadmap)
    recortadas = max(len(nombres) - tope, 0)
    nombres = nombres[recortadas:]
    clave = [str(root), _firma(roadmap / "CALIBRATION.md")]
    cache_path = root / ".claude" / CACHE_NOMBRE
    memo = _leer_cache(cache_path, clave)
    planes, inic, omitida = [], {}, False
    for nombre in nombres:
        carpeta = roadmap / nombre
        firma = [_firma(carpeta / fichero) for _, fichero, _ in ARTEFACTOS]
        previo = memo.get(nombre)
        if isinstance(previo, dict) and previo.get("firma") == firma and isinstance(previo.get("plan"), dict):
            plan = previo["plan"]
        elif time.monotonic() > limite:
            omitida = True
            continue
        else:
            plan = _resumen(analizar(carpeta, root))
        inic[nombre] = {"firma": firma, "plan": plan}
        if plan["vigente"]:
            planes.append(plan)
    if inic != memo:
        _escribir_cache(cache_path, clave, inic)
    desfases = [c for p in planes for c in p["cambios"]]
    avisos = [a for p in planes for a in p["avisos"]]
    if not omitida:
        _, _, cambios_indice = _indice(root, planes, avisos)
        desfases += cambios_indice
    return _informe(planes, desfases, avisos, [], False, omitida=omitida, recortadas=recortadas,
                    analizadas=sorted(inic))


# ---------------------------------------------------------------- puerta go/no-go (/pm-cycle y /dev-cycle)

def puerta(carpeta, decision, descartar=False, escribir=True):
    """Transición de la puerta go/no-go (spec + evaluación, todo o nada) y fila del índice."""
    root, (carpeta,), _ = _carpetas(carpeta)
    spec, ev = _leer(carpeta / "spec.md"), _leer(carpeta / "evaluation.md")
    if spec is None or ev is None:
        raise SyncError("missing_spec_or_evaluation")
    s_est, e_est = campos(spec["text"])["estado"], campos(ev["text"])["estado"]
    if decision == "go":
        if e_est == "cancelado" or s_est == "obsoleta":
            raise SyncError("decision_already_taken", 1)
        objetivos = {"evaluacion": "completado", "spec": s_est if s_est in ("aprobada", "implementada") else "aprobada"}
    else:
        if e_est == "completado" or s_est == "implementada":
            raise SyncError("decision_already_taken", 1)
        objetivos = {"evaluacion": "cancelado", "spec": "obsoleta" if descartar else s_est}
    cambios, salidas = [], []
    for clave, doc, actual in (("spec", spec, s_est), ("evaluacion", ev, e_est)):
        if objetivos[clave] and objetivos[clave] != actual:
            if doc.get("grande"):
                raise SyncError("too_large", 1)
            cambios.append({"iniciativa": carpeta.name, "tipo": clave, "artefacto": doc["path"].name,
                            "de": actual, "a": objetivos[clave]})
            salidas.append((doc, con_estado(doc["text"], objetivos[clave])))
    if escribir:
        _escribir_todos(salidas, time.monotonic() + 10)
    informe = sincronizar(carpeta, escribir=escribir)
    informe["desfases"] = cambios + informe["desfases"]
    informe["cambios"] = informe["desfases"]
    informe["changed"] = bool(escribir and informe["cambios"])
    return informe


# ---------------------------------------------------------------- CLI

def _texto(informe, check):
    verbo = "desfase" if check else "sincronizado"
    out = [f"{verbo} {c['tipo']}: {c['iniciativa']} {c['artefacto']} {c['de']} → {c['a']}"
           + (f" ({c['motivo']})" if c.get("motivo") else "") for c in informe["desfases"]]
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
        modo = parser.add_mutually_exclusive_group()
        modo.add_argument("--check", action="store_true", help="solo comprobar: exit 1 si hay desfases")
        modo.add_argument("--cerrar", action="store_true",
                          help="Fase 6: cierra el ledger de UNA iniciativa con todas sus tareas cerradas")
    args = parser.parse_args(argv[1:] if gate else argv)
    check = not gate and args.check
    try:
        if gate:
            informe = puerta(args.objetivo, args.decision, args.descartar, escribir=not args.dry_run)
        else:
            informe = sincronizar(args.objetivo, escribir=not (check or args.dry_run), cerrar=args.cerrar)
        if check:
            informe["cambios"] = []
        code = 1 if (check and informe["desfases"]) or informe["pendientes"] else 0
    except SyncError as error:
        informe, code = {"schema_version": 1, "status": error.status, **error.extra}, error.code
    except (LW.WriteError, OSError, UnicodeError, ValueError) as error:
        informe, code = {"schema_version": 1, "status": getattr(error, "status", "unavailable")}, 2
    informe["dry_run"], informe["check"] = args.dry_run, check
    if args.json:
        print(json.dumps(informe, ensure_ascii=False, sort_keys=True))
    elif informe.get("status") == "ok":
        print(_texto(informe, check or args.dry_run))
    else:
        detalle = "".join(f" · {k}: {', '.join(v)}" for k, v in informe.items() if k in ("escritos", "no_escritos"))
        print(f"roadmap-sync: {informe['status']}{detalle}", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
