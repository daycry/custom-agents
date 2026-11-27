#!/usr/bin/env python3
"""No regresion de la retirada de los backends de memoria (plugin-audit-2 T-41).

Los adaptadores Kwipu (`markdown-export`) y Graphiti se retiraron en 4.0.0 y el usuario decidio
(2026-11-26) borrar todo rastro del codigo vivo. Este test es el UNICO sitio vivo que puede
nombrarlos: recorre el arbol (ficheros versionados y nuevos sin ignorar) y falla con la lista de
rutas que aun los citan. Solo quedan como se escribieron los registros fechados de la
`LISTA_BLANCA` (roadmap, memoria del proyecto, CHANGELOG y la copia literal de una tarea historica
que usa `test_task_brief.py`).

Ejecutar: python -m pytest -q -p no:xdist tests/test_retired_backends_absent.py
"""
import os
import re
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PATRON = re.compile(r"kwipu|graphiti|markdown[-_]export", re.IGNORECASE)

# Registros fechados: se conservan tal como se escribieron. Prefijos con `/` final = carpeta.
LISTA_BLANCA = (
    "docs/roadmap/",
    "docs/knowledge/",
    "CHANGELOG.md",
    "CHANGELOG.es.md",
    "tests/test_retired_backends_absent.py",
    "agent-kits/shared/fixtures/task-brief-historical-t08.md",
)

# Sin git (tarball exportado): recorrido del disco sin lo que nunca es fuente del plugin.
_DIRS_FUERA = {".git", ".venv", "venv", "node_modules", "dist", "__pycache__", ".pytest_cache", ".claude"}


def _en_lista_blanca(ruta):
    return any(ruta == p or (p.endswith("/") and ruta.startswith(p)) for p in LISTA_BLANCA)


def _ficheros_vivos():
    try:
        salida = subprocess.run(
            ["git", "-C", ROOT, "ls-files", "-z", "--cached", "--others", "--exclude-standard"],
            capture_output=True, check=True, timeout=60).stdout
        rutas = [r.decode("utf-8", "replace") for r in salida.split(b"\0") if r]
    except (OSError, subprocess.SubprocessError):
        rutas = []
        for base, dirs, ficheros in os.walk(ROOT):
            dirs[:] = [d for d in dirs if d not in _DIRS_FUERA]
            rutas += [os.path.relpath(os.path.join(base, f), ROOT).replace(os.sep, "/") for f in ficheros]
    # `.claude/` es la configuracion local del proyecto consumidor, no codigo del plugin.
    return sorted(r for r in rutas if not r.startswith(".claude/"))


def _nombra_retirados(ruta):
    try:
        with open(os.path.join(ROOT, ruta), "rb") as f:
            datos = f.read()
    except OSError:          # borrado en el arbol de trabajo pero aun en el indice
        return False
    return bool(PATRON.search(datos.decode("utf-8", "replace")))


def test_ningun_fichero_vivo_nombra_los_backends_retirados():
    vivos = [r for r in _ficheros_vivos() if not _en_lista_blanca(r)]
    assert len(vivos) > 100, "el recorrido no encontro el arbol del plugin"
    culpables = [r for r in vivos if _nombra_retirados(r)]
    assert culpables == [], "rutas vivas que aun nombran un backend retirado:\n" + "\n".join(culpables)


def test_la_lista_blanca_solo_tiene_rutas_historicas_existentes():
    """Una entrada que ya no existe es una puerta abierta sin uso: se quita de la lista."""
    for entrada in LISTA_BLANCA:
        assert os.path.exists(os.path.join(ROOT, entrada.rstrip("/"))), entrada


def test_el_patron_reconoce_las_tres_formas():
    for texto in ("Kwipu", "GRAPHITI", "markdown-export", "markdown_export"):
        assert PATRON.search(texto), texto
    assert not PATRON.search("markdown export de un backend propio")
