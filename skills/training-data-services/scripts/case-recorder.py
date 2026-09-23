#!/usr/bin/env python3
"""
case-recorder.py — recorder determinista de casos de `training-data-services`.

Estado (T-02): solo expone la REDACCION de secretos que el recorder aplicara a `request`,
`context` y `trajectory` ANTES de tocar disco (CA-09). La redaccion NO se define aqui: se delega
en `agent-kits/shared/redact.py` (`redactar`, `REDACTADO`), fuente unica de los patrones de
secretos del plugin (`session-end-durable-capture` T-02). Si `redact.py` no esta disponible
(paquete parcial), `cargar_redact()` levanta `RedaccionNoDisponible`: el recorder se niega a
grabar antes que escribir un caso sin redactar o con una copia divergente de los patrones.

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


_redact = cargar_redact()
redactar = _redact.redactar
REDACTADO = _redact.REDACTADO


def redactar_estructura(valor):
    """Copia de `valor` con `redactar` aplicado a cada cadena (valores de dicts y elementos de
    listas, recursivo). Las claves y los valores no textuales no se tocan; la entrada no muta."""
    if isinstance(valor, str):
        return redactar(valor)
    if isinstance(valor, dict):
        return {k: redactar_estructura(v) for k, v in valor.items()}
    if isinstance(valor, list):
        return [redactar_estructura(v) for v in valor]
    return valor
