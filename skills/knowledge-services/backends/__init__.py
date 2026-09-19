#!/usr/bin/env python3
"""
backends/__init__.py — cargador del CONTRATO DE ADAPTADOR de `knowledge-services`
(ADR-018, T-07). No es un paquete Python normal (no reexporta nada de los adaptadores): es el
único punto donde `knowledge-sync.py` resuelve `type -> módulo` sin que el núcleo conozca ningún
backend concreto (CA-12). Ver `backends/README.md` para el contrato completo de las 6 funciones.

Convención de nombre de fichero: `type` en `taxonomy.json` -> `backends/<type con "-" por "_">.py`
(p. ej. `"markdown-export"` -> `markdown_export.py`). Un adaptador nuevo es un fichero nuevo en
este directorio (o en el directorio extra que pase el llamador, ver `directorios`); el núcleo
(`knowledge-sync.py`) no cambia.

Sin dependencias externas; solo stdlib (`importlib.util`).
"""
import importlib.util
import os
import re
import sys

# Consola no UTF-8 (Windows cp1252) o tuberías: reconfigurar ANTES de leer/imprimir (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

# gap 95 (CWE-94/22): `type` compone un nombre de fichero y se carga con `importlib` — sin esta
# forma, un `type` como `../../algo` o `algo; rm -rf` podría intentar cargar (o, en `_localizar`,
# comprobar existencia de) rutas fuera de los directorios declarados. Mismo alfabeto que `id` en
# `knowledge-index.py`, sin barras.
_TIPO_VALIDO_RE = re.compile(r"^[a-z][a-z0-9-]*$")

HERE = os.path.dirname(os.path.abspath(__file__))

# Las 6 funciones del contrato de adaptador (design.md, "Contrato de adaptador"). Todas
# obligatorias: `revoke` puede ser un no-op DECLARADO (una función que exista y no haga nada),
# pero tiene que existir — un adaptador que no la define no cumple el contrato.
FUNCIONES_OBLIGATORIAS = ("health", "plan", "apply", "verify", "rebuild", "revoke")


class AdaptadorNoDisponible(Exception):
    """El `type` pedido no tiene fichero de adaptador, o el fichero existe pero no implementa
    el contrato completo (falta una función, o no es invocable). Fail-closed: `knowledge-sync.py`
    convierte esto en un `exit 2` con mensaje claro, nunca en un traceback de `importlib`."""


def _nombres_candidatos(tipo):
    """Dos convenciones de nombre válidas para el mismo `type` (ninguna hardcodea un backend
    concreto): `<type>.py` (los adaptadores reales del plugin, p. ej. `markdown_export.py`) y
    `backend_<type>.py` (fixtures de test, p. ej. `backend_test.py` — evita que un `type: "test"`
    de fixture choque de nombre con un futuro módulo real `test.py`)."""
    base = tipo.replace('-', '_')
    return (f"{base}.py", f"backend_{base}.py")


def _localizar(tipo, directorios):
    for d in directorios:
        for nombre in _nombres_candidatos(tipo):
            ruta = os.path.join(d, nombre)
            if os.path.isfile(ruta):
                return ruta
    return None


def cargar_adaptador(tipo, directorios=None):
    """Carga y valida el adaptador de `type=tipo`. `directorios` es la lista de carpetas donde
    buscar `<tipo>.py` (en orden; la primera que lo tenga gana); por defecto solo este directorio
    (`skills/knowledge-services/backends/`). Un llamador (tests, CA-12) puede añadir una carpeta
    de fixtures SIN tocar este fichero ni `knowledge-sync.py`. Devuelve el módulo ya cargado y
    verificado, o levanta `AdaptadorNoDisponible`."""
    if not tipo or not isinstance(tipo, str):
        raise AdaptadorNoDisponible(f"`type` inválido o ausente: {tipo!r}")
    if not _TIPO_VALIDO_RE.match(tipo):
        raise AdaptadorNoDisponible(
            f"`type` (`{tipo}`) no cumple la forma `[a-z][a-z0-9-]*` (sin `/`, `\\`, `.` ni "
            "espacios) — se rechaza antes de componer una ruta de fichero con él")
    dirs = list(directorios) if directorios else [HERE]
    ruta = _localizar(tipo, dirs)
    if ruta is None:
        raise AdaptadorNoDisponible(
            f"no se encontró un adaptador para type=`{tipo}` (buscado como "
            f"{' o '.join('`' + n + '`' for n in _nombres_candidatos(tipo))} en {dirs})")
    nombre_modulo = f"ks_backend_{tipo.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(nombre_modulo, ruta)
    if spec is None or spec.loader is None:
        raise AdaptadorNoDisponible(f"no se pudo preparar la carga de `{ruta}`")
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:  # noqa: BLE001 - cualquier fallo de carga degrada, no tumba el CLI
        raise AdaptadorNoDisponible(f"el adaptador `{ruta}` no cargó: {type(e).__name__}: {e}") from e
    faltan = [f for f in FUNCIONES_OBLIGATORIAS if not callable(getattr(mod, f, None))]
    if faltan:
        raise AdaptadorNoDisponible(
            f"el adaptador `{ruta}` no implementa el contrato completo; falta(n): {', '.join(faltan)}")
    return mod
