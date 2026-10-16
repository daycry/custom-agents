#!/usr/bin/env python3
"""
ledger-view.py — PROYECCIÓN pura de un `tasks.md` (agent-kits/shared: la consume el panel local,
`skills/plugin-panel/scripts/panel_data.py`, para la página Plan; panel-redesign T-21/T-22).

Dueño único de «qué dice el ledger de cada tarea» para los consumidores de vista: no valida (eso es de
`ledger-lint.py`) ni resume (eso es de `progress-report.py`), y NO crea un segundo lector de nada. Reutiliza
los parsers de `ledger-lint.py` (`parse_ledger`, `secciones_revision`, `ultimo_intento_para`,
`seleccionar_seccion`, `filas_pendientes_de_tarea`, `gap_pendiente`; ADR-016) y el formato del archivado de
`ledger-archive.py` (`PUNTERO`, `HISTORIAL_HDR`). Lo que `parse_ledger` no daba (descripción, dependencias,
horas humanas y de supervisión, casilla de cada criterio, salida de la verificación, `Cerrada`) se lee ahí,
en el parser único.

Contrato (JSON; un dato ausente es `null`, NUNCA 0):
  {"version": 1, "status": "ok", "vocabulario": [estados del ledger, en orden],
   "fases": [{"nombre", "tareas": [ids]}], "desconocidos": [{"id", "literal"}],
   "tareas": [{"id", "titulo", "fase", "estado" (del vocabulario o null), "literal" (estado fuera del
               vocabulario, o null), "horas": {"ia": {"real", "est", "fuente": "medido|estimado|null"},
               "supervision": {"real", "est"}, "humano": {"real", "est"}},
               "criterios": [{"texto", "marcado"}], "descripcion",
               "verificacion": {"texto" (≤ VERIFICACION_MAX), "recortada", "ejecutada", "salida"} | null,
               "dependencias": ["T-NN"], "archivado": {"enlace": "execution-history.md"} | null,
               "cerrada": "AAAA-MM-DD" | null, "cerrada_invalida": texto | null,
               "revision": {"intento", "cabecera", "abiertos"} | null, "gaps": [{"intento", "num",
               "grado", "gap", "correccion"}]}]}
  `status`: ok · fuera_de_tope (> 256 KiB, sin cifras) · ilegible · sin_ledger · sin_tareas · sin_lectura
  (las demás claves son `null` salvo `version`, `status` y `vocabulario`).
El contenido de `execution-history.md` NUNCA se lee ni se mezcla: una tarea con historia archivada solo
lleva el enlace (CA-10).

Uso:
  python3 ledger-view.py <carpeta-iniciativa | tasks.md> [--json]
Exit: 0 siempre que la ruta sea utilizable (el estado va en `status`) · 2 uso incorrecto.
"""
import argparse
import importlib.util
import json
import os
import re
import sys

# Consola Windows (cp1252) o tuberías: reconfigurar ANTES de leer o imprimir nada (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

# Project-local kits must remain read-only even when the caller omits Python -B.
sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))


def _cargar(nombre, fichero):
    spec = importlib.util.spec_from_file_location(nombre, os.path.join(HERE, fichero))
    if spec is None or spec.loader is None:
        raise ImportError(fichero)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


_ll = _cargar("ledger_view_ledger_lint", "ledger-lint.py")
_la = _cargar("ledger_view_ledger_archive", "ledger-archive.py")
_lr = _cargar("ledger_view_local_read", "local-read.py")

parse_ledger = _ll.parse_ledger
secciones_revision = _ll.secciones_revision
ultimo_intento_para = _ll.ultimo_intento_para
seleccionar_seccion = _ll.seleccionar_seccion
filas_pendientes_de_tarea = _ll.filas_pendientes_de_tarea
VERIFICACION_MAX = _ll.VERIFICACION_MAX
TOPE_LECTURA_BYTES = _lr.MAX_BYTES

_ORDEN = ("borrador", "en-progreso", "en-revision", "completado", "cancelado")
# El vocabulario es el de `ledger-lint.ESTADOS`: este orden solo lo presenta (columnas del kanban).
ESTADOS = tuple(e for e in _ORDEN if e in _ll.ESTADOS) + tuple(sorted(_ll.ESTADOS - set(_ORDEN)))

SALIDA_MAX = 1000          # caracteres de la salida de una verificación ejecutada
DESCRIPCION_MAX = 1500
CRITERIO_MAX = 400
GAP_MAX = 400
GRADOS = ("Critical", "Important", "Minor")
_ID_RE = re.compile(r"\bT-\d+\b")
# Rango de tareas en una cabecera de revisión o en el historial archivado: `T-01..T-15`, `T-01–T-15`, `T-01…T-15`
# (con `..`/`…` el segundo `T-` es opcional; con guion es obligatorio: `T-01 — 5 gaps` no es un rango). Se expande a la lista de ids para que cubra las intermedias.
_RANGO_RE = re.compile(r"\bT-(\d{1,4})[ \t]{0,3}(?:(?:\.{2,3}|…)[ \t]{0,3}(?:T-)?|[–—-][ \t]{0,3}T-)(\d{1,4})\b")
RANGO_MAX = 500


def _expandir(texto):
    """`texto` con cada rango `T-a..T-b` sustituido por `T-a, …, T-b` (anchura del primer extremo): los parsers de
    ledger-lint solo ven los extremos. Un rango invertido o de más de `RANGO_MAX` ids se deja tal cual."""
    def lista(m):
        a, b = int(m.group(1)), int(m.group(2))
        if not 0 <= b - a < RANGO_MAX:
            return m.group(0)
        ancho = len(m.group(1))
        return ", ".join(f"T-{n:0{ancho}d}" for n in range(a, b + 1))
    return _RANGO_RE.sub(lista, texto)


def _secciones_expandidas(secciones):
    """Copias de las secciones de revisión con los rangos de la cabecera y de la celda `Tarea` expandidos, solo para
    ELEGIR sección y filas; `_original` conserva la cabecera tal como está escrita (es lo que se muestra)."""
    return [dict(s, cabecera=_expandir(s["cabecera"]), _original=s["cabecera"],
                 filas=[dict(f, tarea=_expandir(f["tarea"])) for f in s["filas"]]) for s in secciones]


def _vacio(status):
    return {"version": 1, "status": status, "vocabulario": list(ESTADOS), "fases": None,
            "desconocidos": None, "tareas": None}


def _tope(texto, n):
    return texto if len(texto) <= n else texto[:n]


def _par(real, est):
    return {"real": real, "est": est}


def _grado(celda):
    """Severidad de la fila de gap: una de `GRADOS` (sin énfasis ni mayúsculas) o `otro`."""
    limpio = re.sub(r"[`*_]", "", celda or "").strip().lower()
    return next((g for g in GRADOS if g.lower() == limpio), "otro")


def _archivadas(texto):
    """IDs citados en `## Historial archivado` (lo que `ledger-archive.py` deja al trasladar revisiones)."""
    ids, dentro = set(), False
    for ln in _ll.sin_vallas(texto).split("\n"):
        if re.match(r"^##\s", ln):
            dentro = ln.strip() == _la.HISTORIAL_HDR
            continue
        if dentro:
            ids |= set(_ID_RE.findall(_expandir(ln)))
    return ids


def _verificacion(t):
    if t["verificacion"] is None:
        return None
    texto = t["verificacion"]
    salida = t["verificacion_salida"]
    ejecutada = t["verificacion_ejecutada"]
    return {"texto": _tope(texto, VERIFICACION_MAX), "recortada": len(texto) > VERIFICACION_MAX,
            "ejecutada": _tope(ejecutada, SALIDA_MAX) if ejecutada else None,
            "salida": _tope(salida, SALIDA_MAX) if salida else None}


def _cerrada(t):
    """(fecha válida, texto inválido): una `Cerrada` mal formada no se publica como fecha."""
    crudo = t["cerrada"]
    if crudo is None:
        return None, None
    if _ll.CERRADA_FECHA_RE.match(crudo) and _ll._fecha_real(crudo):
        return crudo, None
    return None, _tope(crudo, 48)


def _tarea(t, fase, secciones, archivadas):
    estado = t["estado"] if t["estado"] in ESTADOS else None
    literal = t["estado"] if t["estado"] is not None and estado is None else None
    ident = t["id"]
    intento, abiertas = filas_pendientes_de_tarea(secciones, ident)
    ultimo = ultimo_intento_para(secciones, [ident])
    revision = None
    if ultimo is not None:
        seccion, _aviso = seleccionar_seccion(secciones, ultimo, [ident])
        revision = {"intento": ultimo,
                    "cabecera": _tope(seccion["_original"], 160) if seccion else None,
                    "abiertos": len(abiertas)}
    verificacion = _verificacion(t)
    cerrada, invalida = _cerrada(t)
    archivado = bool(verificacion and _la.PUNTERO in t["verificacion"]) or ident in archivadas
    deps = _ID_RE.findall(t["dependencias"] or "")
    return {"id": ident, "titulo": t["titulo"], "fase": fase, "estado": estado, "literal": literal,
            "horas": {"ia": {"real": t["ia_real_h"], "est": t["ia_est_h"], "fuente": t["ia_real_fuente"]},
                      "supervision": _par(t["sup_real_h"], t["sup_est_h"]),
                      "humano": _par(t["humano_real_h"], t["humano_est_h"])},
            "criterios": [{"texto": _tope(c, CRITERIO_MAX), "marcado": m}
                          for c, m in zip(t["criterios"], t["criterios_marcados"])],
            "descripcion": _tope(t["descripcion"], DESCRIPCION_MAX) if t["descripcion"] else None,
            "verificacion": verificacion,
            "dependencias": list(dict.fromkeys(deps)),
            "archivado": {"enlace": _la.HISTORICO} if archivado else None,
            "cerrada": cerrada, "cerrada_invalida": invalida,
            "revision": revision,
            "gaps": [{"intento": f["intento"], "num": f["num"], "grado": _grado(f["grado"]),
                      "gap": _tope(f["gap"], GAP_MAX), "correccion": _tope(f["correccion"], GAP_MAX)}
                     for f in abiertas]}


def proyectar(text):
    """Proyección de un texto de ledger. Pura: no lee ni escribe ficheros."""
    try:
        parsed = parse_ledger(text)
        secciones = _secciones_expandidas(secciones_revision(text))
    except (ValueError, TypeError, KeyError, OverflowError, RecursionError):
        return _vacio("ilegible")
    if not parsed["tareas"]:
        return _vacio("sin_tareas")
    fase_de = {id(t): f["nombre"] for f in parsed["fases"] for t in f["tareas"]}
    archivadas = _archivadas(text)
    tareas = [_tarea(t, fase_de.get(id(t)), secciones, archivadas) for t in parsed["tareas"]]
    return {"version": 1, "status": "ok", "vocabulario": list(ESTADOS),
            "fases": [{"nombre": f["nombre"], "tareas": [t["id"] for t in f["tareas"]]} for f in parsed["fases"]],
            "desconocidos": [{"id": t["id"], "literal": t["literal"]} for t in tareas if t["estado"] is None],
            "tareas": tareas}


def leer(ruta):
    """Lee `tasks.md` de una carpeta de iniciativa (o el fichero) con el tope de lectura acotada de
    `local-read.py` y lo proyecta. Nunca abre `execution-history.md`."""
    ruta = os.path.abspath(str(ruta))
    if os.path.isfile(ruta):
        raiz, relativo = os.path.dirname(ruta), os.path.basename(ruta)
    else:
        raiz, relativo = ruta, "tasks.md"
    lectura = _lr.read_text(raiz, relativo, max_bytes=TOPE_LECTURA_BYTES)
    estado = lectura["status"]
    if estado == "ok":
        return proyectar(lectura["text"].lstrip("﻿"))
    if estado == "not_found":
        return _vacio("sin_ledger")
    if estado == "too_large":
        return _vacio("fuera_de_tope")
    if estado in ("invalid_encoding", "not_regular", "redirected_path"):
        return _vacio("ilegible")
    return _vacio("sin_lectura")


def _texto(datos):
    if datos["status"] != "ok":
        return f"ledger-view: {datos['status']}"
    lineas = []
    for t in datos["tareas"]:
        estado = t["estado"] or ("«" + (t["literal"] or "sin estado") + "»")
        cierre = f" · cerrada {t['cerrada']}" if t["cerrada"] else ""
        lineas.append(f"{t['id']} · {estado} · {t['titulo']}{cierre} · gaps abiertos: {len(t['gaps'])}")
    return "\n".join(lineas)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Proyección de solo lectura de un tasks.md")
    ap.add_argument("ruta", help="carpeta de la iniciativa o ruta a tasks.md")
    ap.add_argument("--json", action="store_true", help="salida JSON")
    args = ap.parse_args(argv)
    datos = leer(args.ruta)
    print(json.dumps(datos, ensure_ascii=False, indent=2) if args.json else _texto(datos))
    return 0


if __name__ == "__main__":
    sys.exit(main())
