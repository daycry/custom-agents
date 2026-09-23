#!/usr/bin/env python3
"""
case-recorder.py — recorder determinista de casos de `training-data-services`.

Estado (T-02): solo expone la REDACCION de secretos que el recorder aplicara a `request`,
`context` y `trajectory` ANTES de tocar disco (CA-09). La redaccion NO se define aqui: se delega
en `agent-kits/shared/redact.py` (`redactar`, `REDACTADO`), fuente unica de los patrones de
secretos del plugin (`session-end-durable-capture` T-02). `redact.py` se carga la primera vez que
se redacta (no al importar): si no esta disponible (paquete parcial), redactar levanta
`RedaccionNoDisponible` y el recorder se niega a grabar antes que escribir un caso sin redactar o
con una copia divergente de los patrones.

El recorder completo (ID estable, nunca sobrescribir `case_id`+version, conservar rechazados,
puerta `--approved-by-human`, indice) llega en T-04..T-06.
"""
import importlib.util
import os
import sys

# Consola no UTF-8 (Windows cp1252) o tuberias: reconfigurar ANTES de leer/imprimir (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leido o None (capsys, pythonw)

HERE = os.path.dirname(os.path.abspath(__file__))


class RedaccionNoDisponible(RuntimeError):
    """`agent-kits/shared/redact.py` no se encuentra: no se puede grabar ningun caso."""


def _dirs_redact():
    """Donde buscar `redact.py`: el arbol del plugin (skills/ y agent-kits/ son hermanos, en el repo
    y en la instalacion) y, si el runtime lo exporta, `CLAUDE_PLUGIN_ROOT`."""
    dirs = [os.path.normpath(os.path.join(HERE, "..", "..", "..", "agent-kits", "shared"))]
    raiz = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if raiz:
        dirs.append(os.path.join(raiz, "agent-kits", "shared"))
    return dirs


def cargar_redact(dirs=None):
    """Carga `redact.py` desde el primer directorio de `dirs` que lo contenga."""
    for d in dirs if dirs is not None else _dirs_redact():
        ruta = os.path.join(d, "redact.py")
        if os.path.isfile(ruta):
            spec = importlib.util.spec_from_file_location("tds_redact", ruta)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    raise RedaccionNoDisponible(
        "no se encuentra agent-kits/shared/redact.py (fuente unica de la redaccion de secretos); "
        "reinstala el plugin completo: el recorder no graba casos sin redactar")


_REDACT = None


def _redact_mod():
    """`redact.py` cargado la PRIMERA vez que se redacta (gap #8): importar este modulo nunca
    falla por su ausencia; redactar (y por tanto grabar) si, con `RedaccionNoDisponible`."""
    global _REDACT
    if _REDACT is None:
        _REDACT = cargar_redact()
    return _REDACT


def __getattr__(nombre):
    """`redactar`/`REDACTADO` son los de `redact.py` (mismo objeto, no una copia), resueltos
    perezosamente (PEP 562)."""
    if nombre in ("redactar", "REDACTADO"):
        return getattr(_redact_mod(), nombre)
    raise AttributeError(f"module {__name__!r} has no attribute {nombre!r}")


def redactar_estructura(valor):
    """Copia de `valor` con la redaccion de `redact.py` aplicada a cada cadena: valores y CLAVES
    textuales de dicts, elementos de listas, tuplas, sets y frozensets (recursivo, gap #8). Lo no
    textual no se toca; la entrada no muta. Sin `redact.py` -> `RedaccionNoDisponible`."""
    redactar_txt = _redact_mod().redactar

    def _rec(v):
        if isinstance(v, str):
            return redactar_txt(v)
        if isinstance(v, dict):
            return {_rec(k) if isinstance(k, str) else k: _rec(x) for k, x in v.items()}
        if isinstance(v, (list, tuple, set, frozenset)):
            return type(v)(_rec(x) for x in v)
        return v

    return _rec(valor)
