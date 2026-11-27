#!/usr/bin/env python3
"""roadmap-sync.py — el plugin mantiene el roadmap al día por sí mismo (plugin-audit-2 T-42).

Deriva el estado de cada iniciativa de `docs/roadmap/` a partir de los estados de sus tareas y de sus
artefactos, con la tabla de transiciones de `agent-kits/dev-cycle/references/phase6-close.md`
(reglas 7-8 de CONVENTIONS), y lo escribe:

- ledger (`tasks.md`): alguna tarea empezada → `en-progreso`; tareas todas `completado`/`cancelado` →
  `completado` con `--cerrar` (Fase 6 de `/dev-cycle`, tras qa verde: el veredicto de la Fase 3 no
  cierra el ledger) o con la retro ya hecha (la retro solo existe tras qa verde: sin `--cerrar` es el
  desfase `cierre-olvidado`). Al 100 % sin retro ni `--cerrar`: aviso `cierre-pendiente`. Si un ledger
  `completado` tiene una tarea reabierta o una tarea nueva en `borrador`, vuelve a `en-progreso`: única
  excepción a «nunca rebaja», con esa tarea como evidencia (`motivo: reabierta`). Un ledger sin campo
  `estado` es el desfase `sin-estado` (no se escribe; `--cerrar` sale 1 `sin_estado`);
- con la puerta de retro abierta (`retro.md` + fila en `CALIBRATION.md`, `retro-gate.py`) y el ledger
  `completado` → plan `completado` y spec `implementada`;
- la evaluación NO se deriva: solo la puerta go/no-go (`gate`) la pasa a `completado`/`cancelado`;
- la fila de la iniciativa en `docs/roadmap/README.md` (dueño único de esa fila), en la tabla `| Fecha |
  Iniciativa | … | Artefactos |` o en la de versiones anteriores `| Fecha | Slug | Estado | … | Spec |
  Evaluación | Plan |`: la que enlaza a su carpeta en una columna de enlaces (o, si ninguna, la que la nombra en
  la celda de identidad sin ser de otra); marca `· estado: <etiqueta>` en la celda de identidad (solo el
  valor de la marca: el texto del autor se conserva) o, si la tabla tiene columna `Estado`, esa celda; y
  enlaces a los artefactos que existen. Si falta, la añade; con dos filas candidatas avisa y no escribe;
  el índice no se crea.

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
abiertas, sin campo `estado`, con un ledger no verificable (> 256 KiB o ilegible: `too_large`/`unreadable_ledger`)
o con una escritura fallida (restaurada) · 2 uso/E-S · 3 `gate` o `--cerrar` a medias (no se pudo restaurar:
`escritos`/`no_escritos`). `--cerrar` escribe todo o nada (fix3).
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import secrets
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
_ENLACE_CARPETA = re.compile(r"\((\d{4}-\d{2}-\d{2}-[^/)\s]+)/")
_ESCAPADO = "\x00"

# Comprobación de sesión (gap 6 del fix1): mismo tope que la instantánea de progress-report, caché por firma
# en la caché privada del usuario, fuera del proyecto (fix2: el bloque de sesión no cambia ningún fichero del
# proyecto; fix3: `~/.cache/custom-agents/roadmap-sync/`, propia, real y 0o700).
TOPE_SESION = 128
PLAZO_SESION = 2.0
CACHE_NOMBRE = ".roadmap-sync.cache"   # nombre histórico (fix1); la caché vive fuera del proyecto (fix2)
CACHE_ENV = "CUSTOM_AGENTS_CACHE_DIR"
CACHE_VERSION = 4   # fix3: caché de usuario, sha de los bytes de la instantánea y vocabulario cerrado
CACHE_MAX = 4 * 1024 * 1024   # tope del fichero de caché (128 iniciativas ocupan decenas de KB)


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
    return _doc_de_bytes(path, raw)


def _doc_de_bytes(path, raw):
    """El documento de `_leer` a partir de bytes ya leídos (el bloque de sesión reutiliza los de la instantánea de
    `progress-report.py`: una apertura por ledger y arranque, H-28)."""
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
    estados = [e or "borrador" for e in LINT.estados_tareas(text)]   # fix2 (gap 9): parser canónico ligero
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

def _retro_abierta(root, carpeta):
    """La puerta de retro (`retro.md` con cuerpo + fila en CALIBRATION) con las comprobaciones de `retro-gate.py`,
    sin `veredicto()`: este vuelve a abrir `tasks.md` para un aviso que aquí no se usa (H-28)."""
    return bool(RG.retro_ok(str(carpeta))[0] and RG.fila_calibracion(str(root), str(carpeta))[0])


def analizar(carpeta, root, cerrar=False, presentes=None, previos=None):
    """Plan de cambios de UNA iniciativa (ver `_resumen` para la parte serializable). `presentes`: los ficheros que
    ya se sabe que existen (la comprobación de sesión los lista con un `scandir`); los demás no se leen."""
    nombre = carpeta.name
    docs, avisos, cambios = {}, [], []
    for clave, fichero, _ in ARTEFACTOS:
        if presentes is not None and fichero not in presentes:
            docs[clave] = None
            continue
        try:
            if previos is not None and fichero == "tasks.md" and nombre in previos:
                docs[clave] = _doc_de_bytes(carpeta / fichero, previos[nombre])
                continue
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

    ledger, cerrable, retro = docs["ledger"], False, None
    # Un ledger > 256 KiB no se deriva: su cabecera `completado` se acepta tal cual (ya cerrado y archivable).
    cerrado = bool(ledger and ledger.get("grande") and estados["ledger"] == "completado")
    if ledger and ledger.get("grande"):
        if estados["ledger"] not in ("completado", "cancelado"):
            avisos.append({"iniciativa": nombre, "tipo": "no-escrito",
                           "detalle": "tasks.md > 256 KiB: estado de la iniciativa no derivado "
                                      "(archívalo con ledger-archive.py)"})
            retro = _retro_abierta(root, carpeta)
            if retro:
                # fix3 (gap 3): retro hecha y un ledger que no se puede verificar (no se sabe si quedan tareas
                # abiertas): el cierre está bloqueado; es un desfase, no un aviso. No se escribe nada.
                cambios.append({"iniciativa": nombre, "tipo": "ledger", "artefacto": "tasks.md",
                                "de": estados["ledger"], "a": "completado", "motivo": "no-verificable"})
    elif ledger:
        objetivo, abiertas = objetivo_ledger(ledger["text"])
        cerrable = objetivo == "completado"
        if cerrable:
            retro = _retro_abierta(root, carpeta)
        if estados["ledger"] is None and not info["ledger"]["spans"] and not info["ledger"]["sin_token"]                 and objetivo:
            # fix2 (gap 5): sin campo `estado` no hay dónde escribir: es un desfase (lo arregla una persona).
            cambios.append({"iniciativa": nombre, "tipo": "ledger", "artefacto": "tasks.md", "de": None,
                            "a": "completado" if cerrable and (cerrar or retro) else "en-progreso",
                            "motivo": "sin-estado"})
        elif estados["ledger"] == "completado" and abiertas:
            # Excepción documentada a «nunca rebaja»: una tarea reabierta, o una tarea nueva en `borrador`, es
            # trabajo abierto y la evidencia (fix2, gap 10).
            if info["ledger"]["spans"]:
                nuevos["ledger"] = "en-progreso"
                cambios.append({"iniciativa": nombre, "tipo": "ledger", "artefacto": "tasks.md",
                                "de": "completado", "a": "en-progreso", "motivo": "reabierta"})
        elif cerrable and (cerrar or retro):
            # fix2 (gap 2): la retro (que solo existe tras qa verde) basta como autorización del cierre; un
            # `--cerrar` olvidado es un DESFASE (`cierre-olvidado`), no un aviso que se pueda ignorar.
            proponer("ledger", "completado", RANGO)
            if not cerrar and cambios and cambios[-1]["tipo"] == "ledger":
                cambios[-1]["motivo"] = "cierre-olvidado"
        elif cerrable:
            proponer("ledger", "en-progreso", RANGO)
            if estados["ledger"] not in ("completado",) and estados["ledger"] not in TERMINALES:
                avisos.append({"iniciativa": nombre, "tipo": "cierre-pendiente",
                               "detalle": f"tareas al 100 %: el cierre lo autoriza la Fase 6 "
                                          f"(roadmap-sync.py docs/roadmap/{nombre} --cerrar)"})
        else:
            proponer("ledger", objetivo, RANGO)
    cerrado = cerrado or (cerrable and nuevos["ledger"] == "completado")
    if retro is None:
        retro = cerrado and _retro_abierta(root, carpeta)
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


# Columnas del índice (gap 11 del fix2): el formato vigente `| Fecha | Iniciativa | … | Artefactos |` y el de
# versiones anteriores del plugin `| Fecha | Slug | Estado | Coste estimado | Spec | Evaluación | Plan |`.
_IDENTIDAD = ("iniciativa", "slug", "initiative")
_COLUMNA_ENLACE = {"artefactos": None, "artifacts": None, "spec": "spec.md", "evaluación": "evaluation.md",
                   "evaluacion": "evaluation.md", "evaluation": "evaluation.md", "eval": "evaluation.md",
                   "design": "design.md", "diseño": "design.md", "plan": "improvement-plan.md",
                   "tasks": "tasks.md", "ledger": "tasks.md", "retro": "retro.md"}
_VACIA = ("", "—", "-")


def _nombre_columna(celda):
    return celda.replace("*", "").strip().lower()


def _disposicion(cabecera):
    """{'ident', 'estado', 'enlaces': {índice: fichero|None}, 'n', 'nombres'} o None si no es la tabla del índice.
    Sin columnas de enlace reconocibles, la última hace de Artefactos (formato vigente)."""
    nombres = [_nombre_columna(c) for c in _celdas(cabecera)]
    if len(nombres) < 3 or nombres[0] not in ("fecha", "date"):
        return None
    ident = next((i for i, n in enumerate(nombres) if n in _IDENTIDAD), None)
    if ident is None:
        return None
    enlaces = {i: _COLUMNA_ENLACE[n] for i, n in enumerate(nombres) if n in _COLUMNA_ENLACE and i != ident}
    estado = next((i for i, n in enumerate(nombres) if n in ("estado", "status")), None)
    return {"ident": ident, "estado": estado, "enlaces": enlaces or {len(nombres) - 1: None},
            "n": len(nombres), "nombres": nombres}


def _es_el_indice(lineas, cabecera, disp):
    """fix3 (gap 8): una tabla `| Fecha | Iniciativa/Slug | … |` es el índice solo si alguna fila enlaza a una carpeta
    de iniciativa, o si su cabecera es la completa conocida (vigente: … | Artefactos; anterior: Slug + Estado + Spec +
    Evaluación + Plan). Una leyenda o una tabla de otra cosa antes del índice no lo secuestra."""
    nombres = disp["nombres"]
    if nombres[-1] in ("artefactos", "artifacts") and nombres[disp["ident"]] in ("iniciativa", "initiative"):
        return True
    if disp["estado"] is not None and {"spec", "plan"} <= set(nombres) and \
            {"evaluación", "evaluacion", "evaluation", "eval"} & set(nombres):
        return True
    i = cabecera + 2
    while i < len(lineas) and lineas[i].startswith("|"):
        if _ENLACE_CARPETA.search(lineas[i]):
            return True
        i += 1
    return False


def _texto_plano(celda):
    return re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", celda).replace("`", "").replace("*", "").strip()


def _celda_nueva(nombre, plan, columna, disp, i):
    """Celda `i` de una fila nueva en un índice con columnas propias (formato con Slug/Estado)."""
    if i == 0:
        return nombre[:10]
    if i == disp["ident"]:
        return nombre[11:]
    if i == disp["estado"]:
        return plan["etiqueta"]
    if i in disp["enlaces"]:
        fichero = disp["enlaces"][i]
        enlaces = [(f, label) for f, label in plan["enlaces"] if fichero is None or f == fichero]
        return " · ".join(f"[{label}]({nombre}/{f})" for f, label in enlaces) or "—"
    if "coste" in columna or "cost" in columna:
        return "No estimado"
    return "No medido" if "tiempo" in columna or "horas" in columna else "—"


def editar_indice(text, planes):
    """(texto nuevo, cambios, avisos) con la fila de cada iniciativa al día; el resto del índice intacto.

    La tabla se reconoce por su cabecera `| Fecha | Iniciativa |` o `| Fecha | Slug |` (gap 11). La fila propia es
    la que enlaza a la carpeta en una columna de enlaces (Artefactos, o Spec/Evaluación/Plan…), no la primera
    que la cita; si ninguna lo hace, la que no pertenece a otra iniciativa y la nombra en la celda de identidad
    (enlace, o slug + fecha; gap 3). Dos candidatas → aviso, sin escribir. Con columna `Estado` el estado va a
    esa celda (es su sitio: una marca en otra celda la dejaría desfasada y contradictoria); sin ella, la marca
    `· estado:` en la celda de identidad. El formato vigente conserva su fila nueva y su celda de Artefactos."""
    lineas = text.split("\n")
    cabecera, disp = None, None
    for i, linea in enumerate(lineas[:-1]):
        if linea.startswith("|") and _SEPARADOR_TABLA.match(lineas[i + 1].strip()) and "-" in lineas[i + 1]:
            candidata = _disposicion(linea)
            if candidata and _es_el_indice(lineas, i, candidata):
                cabecera, disp = i, candidata
                break
    if cabecera is None:
        return text, [], ["README.md sin tabla `| Fecha | Iniciativa |` ni `| Fecha | Slug |`"]
    ident, columnas = disp["ident"], disp["n"]
    vigente = disp["enlaces"] == {columnas - 1: None} and disp["estado"] is None
    filas, sin_duenyo = {}, []
    i = cabecera + 2
    while i < len(lineas) and lineas[i].startswith("|"):
        celdas = _celdas(lineas[i])
        duenyos = {n for c in disp["enlaces"] if c < len(celdas) for n in _ENLACE_CARPETA.findall(celdas[c])}
        for nombre in duenyos:
            filas.setdefault(nombre, []).append(i)
        if not duenyos and ident < len(celdas):
            sin_duenyo.append((i, celdas))
        i += 1
    cambios, problemas, nuevas = [], [], []
    for plan in planes:
        if not plan["etiqueta"]:
            continue
        nombre = plan["nombre"]
        propias = filas.get(nombre, [])
        donde, por_identidad = "en sus columnas de enlaces", not propias
        if not propias:
            propias = [i for i, celdas in sin_duenyo
                       if f"({nombre}/" in celdas[ident]
                       or (_texto_plano(celdas[ident]) in (nombre, nombre[11:]) and celdas[0].strip() == nombre[:10])]
            donde = "en la celda de identidad"
        if len(propias) > 1:
            problemas.append(f"{nombre}: {len(propias)} filas la nombran {donde}; no se escribe")
            continue
        if not propias:
            if vigente:
                titulo = plan["titulo"] or nombre[11:]
                celdas = [nombre[:10], f"{nombre[11:]} — {titulo}{MARCA}{plan['etiqueta']}"]
                celdas += ["No estimado", "No medido"][:max(columnas - 3, 0)] + ["—"] * max(columnas - 5, 0)
                celdas.append(" · ".join(f"[{label}]({nombre}/{f})" for f, label in plan["enlaces"]))
            else:
                celdas = [_celda_nueva(nombre, plan, col, disp, n) for n, col in enumerate(disp["nombres"])]
            nuevas.append(_fila(celdas))
            cambios.append({"iniciativa": nombre, "tipo": "indice", "artefacto": "README.md",
                            "de": "sin fila", "a": plan["etiqueta"]})
            continue
        fila_i = propias[0]
        celdas = _celdas(lineas[fila_i])
        if len(celdas) < 3 or len(celdas) <= max([ident, disp["estado"] or 0] + list(disp["enlaces"])):
            problemas.append(f"{nombre}: su fila tiene menos columnas que la cabecera; no se escribe")
            continue
        if disp["estado"] is not None:
            previa = celdas[disp["estado"]].strip()
            celdas[disp["estado"]] = plan["etiqueta"]
        else:
            celdas[ident], previa = _con_marca(celdas[ident], plan["etiqueta"])
        puestos = []
        for col, fichero in sorted(disp["enlaces"].items()):
            # Un enlace ya citado en la fila (p. ej. la retro en la prosa de la celda de identidad) no se duplica;
            # pero si la fila se reconoció solo por su celda de identidad (gap 3), los enlaces van a su columna
            # para que la próxima vez se reconozca por ella.
            faltan = [(f, label) for f, label in plan["enlaces"] if f"({nombre}/{f})" not in celdas[col]
                      and (por_identidad or f"({nombre}/{f})" not in lineas[fila_i])]
            if fichero is None:
                if faltan:
                    ultima = celdas[col]
                    sep = next((s for s in SEPARADORES if s in ultima), " · ")
                    nuevos = sep.join(f"[{label}]({nombre}/{f})" for f, label in faltan)
                    celdas[col] = nuevos if ultima in _VACIA else ultima + sep + nuevos
                    puestos += faltan
            else:
                propio = [(f, label) for f, label in faltan if f == fichero]
                if propio and celdas[col].strip() in _VACIA:
                    celdas[col] = f"[{propio[0][1]}]({nombre}/{fichero})"
                    puestos += propio
        nueva = _fila(celdas)
        if nueva != lineas[fila_i]:
            lineas[fila_i] = nueva
            de = previa if previa not in (None, "") else "sin marca"
            if puestos:
                de += " · faltan " + ", ".join(label for _, label in puestos)
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
    for n, (doc, texto, *ledger) in enumerate(salidas):
        try:
            output = _escribir(doc, texto, deadline, ledger=bool(ledger and ledger[0]))
        except (SyncError, LW.WriteError, OSError) as error:
            sin_restaurar = []
            for previo, bytes_escritos in reversed(escritos):
                try:
                    _restaurar(previo, bytes_escritos, deadline)
                except (SyncError, LW.WriteError, OSError):
                    sin_restaurar.append(previo["path"].name)
            if sin_restaurar:
                raise SyncError("partial", 3, escritos=sorted(sin_restaurar),
                                no_escritos=[d["path"].name for d, *_ in salidas[n:]]) from error
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
            if os.path.lexists(carpetas[0] / "tasks.md"):
                # fix3 (gap 3): un ledger que existe pero no se puede leer no se da por cerrado.
                raise SyncError("unreadable_ledger", 1, detalle="tasks.md ilegible (enlace, no regular o E/S): no "
                                                                "se puede verificar que todas las tareas estén cerradas")
            raise SyncError("not_found", 2)
        if plan["docs"]["ledger"].get("grande"):
            raise SyncError("too_large", 1, detalle="ledger > 256 KiB: archívalo con ledger-archive.py antes de "
                                                    "cerrar (no se puede verificar que todas las tareas estén cerradas)")
        if not plan["cerrable"]:
            raise SyncError("open_tasks", 1)
        if any(c.get("motivo") == "sin-estado" for c in plan["cambios"]):
            raise SyncError("sin_estado", 1, detalle="tasks.md sin campo `estado:` (frontmatter) ni celda "
                                                    "`| Estado |`: añádelo y repite --cerrar")
    desfases = [c for p in planes for c in p["cambios"]]
    avisos = [a for p in planes for a in p["avisos"]]
    indice, indice_nuevo, cambios_indice = _indice(root, planes, avisos)
    desfases += cambios_indice
    pendientes = []
    if escribir:
        pendientes += [f"{c['iniciativa']}/tasks.md: sin campo `estado` (añádelo a mano)"
                       for c in desfases if c.get("motivo") == "sin-estado"]
        pendientes += [f"{c['iniciativa']}/tasks.md > 256 KiB con la retro hecha: archívalo con ledger-archive.py "
                       f"y repite" for c in desfases if c.get("motivo") == "no-verificable"]
        salidas = []      # (doc, texto nuevo, ¿ledger?, etiqueta para pendientes)
        for p in planes:
            for clave, fichero, _ in ARTEFACTOS:
                doc = p["docs"].get(clave)
                if doc and not doc.get("grande") and any(c["artefacto"] == fichero and c.get("motivo") not in
                                                         ("sin-estado", "no-verificable") for c in p["cambios"]):
                    salidas.append((doc, con_estado(doc["text"], p["nuevos"][clave]), clave == "ledger",
                                    f"{p['nombre']}/{fichero}"))
        if indice is not None and indice_nuevo != indice["text"]:
            salidas.append((indice, indice_nuevo, False, "README.md"))
        if cerrar:
            # fix3 (gap 5): el cierre de una iniciativa es todo o nada (restaura lo escrito; si no puede, exit 3).
            _escribir_todos([(doc, texto, es_ledger) for doc, texto, es_ledger, _ in salidas], deadline)
        else:
            for doc, texto, es_ledger, nombre in salidas:
                try:
                    _escribir(doc, texto, deadline, ledger=es_ledger)
                except (SyncError, LW.WriteError, OSError) as error:
                    pendientes.append(f"{nombre}: {getattr(error, 'status', 'unavailable')}")
    avisos += [{"iniciativa": "-", "tipo": "no-escrito", "detalle": p} for p in pendientes]
    return _informe(planes, desfases, avisos, pendientes, escribir)


# ---------------------------------------------------------------- comprobación de sesión (solo lectura)

def _firma(path):
    try:
        info = os.lstat(path)
    except OSError:
        return None
    return [info.st_mtime_ns, info.st_size]


def _firma_carpeta(carpeta):
    """(firma, presentes): la firma de los artefactos de una iniciativa con UN `scandir` (en Windows el `stat` de
    cada entrada viene con el listado, sin una llamada por fichero) y el conjunto de los que existen."""
    vistos = {}
    try:
        with os.scandir(carpeta) as entradas:
            for entrada in entradas:
                if entrada.name in FICHERO.values():
                    info = entrada.stat(follow_symlinks=False)
                    vistos[entrada.name] = [info.st_mtime_ns, info.st_size]
    except OSError:
        return [None] * len(ARTEFACTOS), set()
    return [vistos.get(fichero) for _, fichero, _ in ARTEFACTOS], set(vistos)


_CLAVES_CAMBIO = ("iniciativa", "tipo", "artefacto", "de", "a")
_CLAVES_AVISO = ("iniciativa", "tipo", "detalle")
# fix3 (gap 4): vocabulario cerrado de lo que una entrada de caché puede traer; lo que llega al aviso de sesión sale
# de las carpetas reales (la entrada debe ser de SU carpeta), nunca de un texto libre de la caché.
_ESTADOS = frozenset(RANGO) | frozenset(RANGO_SPEC) | TERMINALES
_MOTIVOS = frozenset({"reabierta", "cierre-olvidado", "sin-estado", "no-verificable"})
_TIPOS_AVISO = frozenset({"ilegible", "no-escrito", "sin-estado", "cierre-pendiente", "retro-pendiente", "adelantado"})
_ETIQUETAS = frozenset({None, "cancelada", "cerrada", "completada, retro pendiente", "en curso", "planificada",
                        "evaluada", "solo spec"})
_ENLACES = frozenset((fichero, label) for _, fichero, label in ARTEFACTOS)
_DE = re.compile(r"[\w-]{1,40}")


def _texto_corto(valor, tope=400):
    return isinstance(valor, str) and len(valor) <= tope and "\n" not in valor and "\r" not in valor


def _cambio_valido(c, nombre):
    return (isinstance(c, dict) and all(k in c for k in _CLAVES_CAMBIO) and set(c) <= {*_CLAVES_CAMBIO, "motivo"}
            and c["iniciativa"] == nombre and c["tipo"] in FICHERO and c["artefacto"] == FICHERO[c["tipo"]]
            and c["a"] in _ESTADOS and (c["de"] is None or (isinstance(c["de"], str) and bool(_DE.fullmatch(c["de"]))))
            and c.get("motivo", "reabierta") in _MOTIVOS)


def _aviso_valido(a, nombre):
    return (isinstance(a, dict) and set(a) == set(_CLAVES_AVISO) and a["iniciativa"] == nombre
            and a["tipo"] in _TIPOS_AVISO and _texto_corto(a["detalle"]))


def _plan_valido(plan, nombre=None):
    """¿Una entrada de la caché tiene la forma de `_resumen` y es de la carpeta `nombre`? (fix2, gap 4; fix3, gap 4:
    tipos y vocabulario cerrados). Una entrada incompleta, de otra versión, de otra carpeta o manipulada se descarta
    y se recalcula: nunca rompe ni silencia el aviso de la sesión, ni pone su texto en él."""
    if not isinstance(plan, dict) or not isinstance(plan.get("nombre"), str):
        return False
    nombre = plan["nombre"] if nombre is None else nombre
    cambios, avisos, enlaces = plan.get("cambios"), plan.get("avisos"), plan.get("enlaces")
    if plan["nombre"] != nombre or not all(isinstance(x, list) for x in (cambios, avisos, enlaces)):
        return False
    if not (all(_cambio_valido(c, nombre) for c in cambios) and all(_aviso_valido(a, nombre) for a in avisos)):
        return False
    if not all(isinstance(e, list) and len(e) == 2 and tuple(e) in _ENLACES for e in enlaces):
        return False
    return (plan.get("etiqueta") in _ETIQUETAS and (plan.get("titulo") is None or _texto_corto(plan.get("titulo")))
            and all(isinstance(plan.get(k), bool) for k in ("retro", "cerrable", "vigente")))


def _mkdir_private(path, **kwargs):
    """0o700 en POSIX. En Windows se heredan los permisos del padre: Python 3.13 convierte
    0o700 en una ACL explícita que deja fuera al usuario restringido del sandbox de Codex."""
    if os.name == 'nt':
        path.mkdir(**kwargs)
    else:
        path.mkdir(mode=0o700, **kwargs)


def _base_cache():
    """(directorio base de la caché, None) o (None, motivo). fix3 (gaps 2 y 7): la convención de estado privado del
    plugin para cachés por usuario (`~/.cache/custom-agents/`, como el índice de Codex de `usage-meter.py`):
    `$XDG_CACHE_HOME` en POSIX, `%LOCALAPPDATA%` en Windows; `$CUSTOM_AGENTS_CACHE_DIR` la sustituye (tests).
    Siempre una ruta ABSOLUTA: sin ella no hay caché (nunca el cwd)."""
    override = os.environ.get(CACHE_ENV)
    if override:
        return (Path(override), None) if os.path.isabs(override) else (None, f"${CACHE_ENV} no es una ruta absoluta")
    if os.name == "nt" and os.path.isabs(os.environ.get("LOCALAPPDATA") or ""):
        raiz = Path(os.environ["LOCALAPPDATA"])
    elif os.name != "nt" and os.path.isabs(os.environ.get("XDG_CACHE_HOME") or ""):
        raiz = Path(os.environ["XDG_CACHE_HOME"])
    else:
        home = os.path.expanduser("~")
        if not os.path.isabs(home):
            return None, "sin directorio de usuario absoluto (HOME / LOCALAPPDATA)"
        raiz = Path(home) / ".cache"
    return raiz / "custom-agents", None


def _ubicacion_cache(root):
    """(ruta del fichero de caché o None, motivo)."""
    base, motivo = _base_cache()
    if base is None:
        return None, motivo
    try:
        real_base, real_root = os.path.realpath(base), os.path.realpath(str(root))
        if os.path.commonpath([real_base, real_root]) == real_root:
            return None, "el directorio de caché está dentro del proyecto"
    except ValueError:
        pass   # unidades distintas en Windows: fuera del proyecto
    clave = hashlib.sha256(os.path.abspath(str(root)).encode("utf-8")).hexdigest()[:24]
    return base / "roadmap-sync" / f"{clave}.json", None


def cache_path(root):
    """Caché de la comprobación de sesión FUERA del proyecto, en la caché privada del usuario (fix3):
    `<caché de usuario>/custom-agents/roadmap-sync/<sha256 de la raíz>.json` (es una caché: si se borra, se recalcula).
    None si no hay un directorio absoluto fuera del proyecto."""
    return _ubicacion_cache(root)[0]


def _uid_actual():
    """El usuario dueño de la caché (POSIX); función propia para poder simular un directorio ajeno en los tests."""
    return os.getuid()


def _dir_seguro(path, estricto):
    """¿`path` es un directorio propio de verdad? Directorio real (ni enlace ni junction) y, en POSIX, del usuario
    actual y sin escritura de grupo/otros; `estricto` (el directorio de la caché): sin NINGÚN permiso de grupo/otros.
    En Windows la propiedad se hereda del perfil (`_mkdir_private`) y se exige que no sea un punto de reanálisis."""
    info = os.lstat(path)
    if not stat.S_ISDIR(info.st_mode) or LW.READER._redirected(info):
        return False
    if hasattr(os, "getuid"):
        return info.st_uid == _uid_actual() and not info.st_mode & (0o077 if estricto else 0o022)
    return True


def _crear_privado(d):
    _mkdir_private(d)
    if os.name != "nt":
        os.chmod(d, 0o700)        # el umask recorta el modo de mkdir; el chmod no (fix3, gap 2)


def _preparar_dir(ruta, crear):
    """Verifica (y con `crear`, crea con `_mkdir_private` + `chmod 0o700`) los componentes propios del directorio de la
    caché antes de leer o escribir: `roadmap-sync/` (estricto) y, sin override, `custom-agents/` (lo comparte el
    índice de Codex de usage-meter: sin escritura ajena). True si es utilizable."""
    directorio = ruta.parent
    propios = [directorio] if os.environ.get(CACHE_ENV) else [directorio.parent, directorio]
    try:
        for d in propios:
            if os.path.lexists(d):
                continue
            if not crear:
                return False
            if not os.path.isdir(d.parent):
                # Solo se crea la raíz estándar que falte (`~/.cache` en un perfil nuevo), nunca una cadena arbitraria.
                if d.parent.name != ".cache" or not os.path.isdir(d.parent.parent):
                    return False
                _crear_privado(d.parent)
            _crear_privado(d)
        return all(_dir_seguro(d, estricto=d == directorio) for d in propios)
    except OSError:
        return False


def _leer_cache(path, clave):
    """La caché, solo si es un fichero regular propio y acotado: `O_NOFOLLOW` (donde existe), `O_NONBLOCK` (un FIFO no
    cuelga), `fstat` del descriptor abierto y tope de tamaño. Cualquier duda → {} (se recalcula)."""
    if path is None or not _preparar_dir(path, crear=False):
        return {}
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_BINARY", 0)
    try:
        if os.name == "nt":
            info = os.lstat(path)
            if not stat.S_ISREG(info.st_mode) or LW.READER._redirected(info):
                return {}
        fd = os.open(path, flags)
        with os.fdopen(fd, "rb") as handle:
            info = os.fstat(handle.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size > CACHE_MAX:
                return {}
            if hasattr(os, "getuid") and (info.st_uid != _uid_actual() or info.st_mode & 0o022):
                return {}
            raw = handle.read(CACHE_MAX + 1)
        if len(raw) > CACHE_MAX:
            return {}
        datos = json.loads(raw.decode("utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(datos, dict) or datos.get("version") != CACHE_VERSION or datos.get("clave") != clave:
        return {}
    inic = datos.get("inic")
    return inic if isinstance(inic, dict) else {}


def _escribir_cache(path, clave, inic):
    """Escritura atómica en la caché privada (fichero 0o600 creado en exclusiva, sin seguir enlaces). Nunca dentro del
    proyecto. False si no hay directorio privado utilizable (el informe lo avisa)."""
    if path is None or not _preparar_dir(path, crear=True):
        return False
    datos = json.dumps({"version": CACHE_VERSION, "clave": clave, "inic": inic}, ensure_ascii=False).encode("utf-8")
    if len(datos) > CACHE_MAX:
        return False
    tmp = path.with_name(f"{path.name}.{os.getpid()}.{secrets.token_hex(4)}.tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    try:
        fd = os.open(tmp, flags, 0o600)
        with os.fdopen(fd, "wb") as handle:
            handle.write(datos)
        os.replace(tmp, path)
    except OSError:
        try:
            os.unlink(tmp)
        except OSError:
            pass
    return True


def comprobar(root_proyecto, deadline=None, tope=TOPE_SESION, previos=None):
    """Solo lectura (bloque de sesión): el mismo análisis, acotado. Las `tope` carpetas más recientes; caché
    por firma (ruta + `mtime_ns` + tamaño de cada artefacto, y la de `CALIBRATION.md`; con los bytes de la
    instantánea, también su sha256, H-28): solo se reanaliza la iniciativa cuya firma cambió. Con la caché completa no
    se consulta el plazo: el plazo acota solo `analizar`, y lo pendiente se omite (`omitida`) sin romper nada."""
    root = Path(os.path.abspath(str(root_proyecto)))
    roadmap = root / "docs" / "roadmap"
    limite = time.monotonic() + PLAZO_SESION if deadline is None else deadline
    nombres = _nombres(roadmap)
    recortadas = max(len(nombres) - tope, 0)
    nombres = nombres[recortadas:]
    clave = [str(root), _firma(roadmap / "CALIBRATION.md")]
    ruta_cache, sin_cache = _ubicacion_cache(root)
    memo = _leer_cache(ruta_cache, clave)
    planes, inic, omitida = [], {}, False
    for nombre in nombres:
        carpeta = roadmap / nombre
        firma, presentes = _firma_carpeta(carpeta)
        bytes_previos = previos.get(nombre) if previos else None
        # fix3 (gap 6): con los bytes de la instantánea, la entrada vale solo para ESOS bytes (si el ledger cambió
        # entre la instantánea y la firma, la siguiente comprobación no hereda un plan de otros bytes).
        sha = hashlib.sha256(bytes_previos).hexdigest() if isinstance(bytes_previos, bytes) else None
        previo = memo.get(nombre)
        if (isinstance(previo, dict) and previo.get("firma") == firma and previo.get("sha") == sha
                and _plan_valido(previo.get("plan"), nombre)):
            plan = previo["plan"]
        elif time.monotonic() > limite:
            omitida = True
            continue
        else:
            plan = _resumen(analizar(carpeta, root, presentes=presentes, previos=previos))
        inic[nombre] = {"firma": firma, "sha": sha, "plan": plan}
        if plan["vigente"]:
            planes.append(plan)
    if inic != memo and not _escribir_cache(ruta_cache, clave, inic):
        sin_cache = sin_cache or "sin directorio privado utilizable (propio, real y sin permisos de grupo/otros)"
    desfases = [c for p in planes for c in p["cambios"]]
    avisos = [a for p in planes for a in p["avisos"]]
    if sin_cache:
        avisos.append({"iniciativa": "-", "tipo": "sin-cache", "detalle": f"comprobación sin caché: {sin_cache}"})
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
        detalle += f" — {informe['detalle']}" if informe.get("detalle") else ""
        print(f"roadmap-sync: {informe['status']}{detalle}", file=sys.stderr)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
