"""Directorios de estado privados: 0o700 en POSIX y permisos heredados en Windows.

Python 3.13 en Windows convierte `mkdir(mode=0o700)` en una ACL explícita (usuario,
Administradores, SYSTEM) que sustituye a la heredada y deja fuera al usuario restringido
del sandbox de Codex: `plan-review.py consume` fallaba con `invalid_input` dentro de Codex.
"""
import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULOS = {
    "plan-review": ROOT / "agent-kits/shared/plan-review.py",
    "agent-activity-store": ROOT / "agent-kits/shared/agent-activity-store.py",
    "knowledge-curation": ROOT / "agent-kits/shared/knowledge-curation.py",
    "graphiti_publication": ROOT / "skills/knowledge-services/backends/graphiti_publication.py",
    "graphiti_rebuild": ROOT / "skills/knowledge-services/backends/graphiti_rebuild.py",
}


def cargar(nombre):
    ruta = MODULOS[nombre]
    sys.path.insert(0, str(ruta.parent))
    try:
        spec = importlib.util.spec_from_file_location("private_dir_" + nombre.replace("-", "_"), ruta)
        modulo = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modulo)
    finally:
        sys.path.remove(str(ruta.parent))
    return modulo


def test_ninguna_pieza_crea_directorios_con_0o700_directo():
    for nombre, ruta in MODULOS.items():
        texto = ruta.read_text(encoding="utf-8")
        assert "def _mkdir_private(" in texto, nombre
        assert texto.count("mkdir(mode=0o700") == 1, f"{nombre}: crea directorios con _mkdir_private"


@pytest.mark.parametrize("nombre", sorted(MODULOS))
@pytest.mark.skipif(os.name != "nt" or shutil.which("icacls") is None, reason="ACL de Windows")
def test_windows_el_directorio_hereda_los_permisos_del_padre(tmp_path, nombre):
    destino = tmp_path / "estado"
    cargar(nombre)._mkdir_private(destino)
    acl = subprocess.run(["icacls", str(destino)], capture_output=True, text=True,
                         encoding="utf-8", errors="replace").stdout
    entradas = [linea for linea in acl.splitlines()[:-2] if ":(" in linea]
    assert entradas and all("(I)" in linea for linea in entradas), acl


@pytest.mark.parametrize("nombre", sorted(MODULOS))
@pytest.mark.skipif(os.name == "nt", reason="modo POSIX")
def test_posix_el_directorio_es_privado(tmp_path, nombre):
    destino = tmp_path / "estado"
    cargar(nombre)._mkdir_private(destino)
    assert destino.stat().st_mode & 0o777 == 0o700
