#!/usr/bin/env python3
"""Tests de retro-gate.py (memory-retrieval T-17; spec CA-23): la retro es una PUERTA del cierre de una
iniciativa, no un aviso que se pueda ignorar (`LES-012`). Ejecutar: python3 -m pytest -q agent-kits/shared/test_retro_gate.py"""
import importlib.util
import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "retro-gate.py")

spec = importlib.util.spec_from_file_location("retro_gate", SCRIPT)
rg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rg)

CABECERA = ("# CALIBRATION\n\n| Fecha | Iniciativa | Desv. producción | Desv. tokens | tokens/hora (medido) | Causa principal | "
            "Ajuste sugerido |\n|---|---|---|---|---|---|---|\n")


def proyecto(tmp_path, slug="2026-01-01-demo", retro=False, fila=False, estado="completado", cal=True, fila_slug="`demo`"):
    proj = tmp_path / "proj"
    carpeta = proj / "docs" / "roadmap" / slug
    carpeta.mkdir(parents=True)
    (carpeta / "tasks.md").write_text(f"---\ntasks: demo\nestado: {estado}\n---\n# Checklist\n", encoding="utf-8")
    if retro:
        (carpeta / "retro.md").write_text("---\nretro: demo\nfecha: 2026-01-02\n---\n# Retro — demo\n\ncausas…\n", encoding="utf-8")
    if cal:
        filas = f"| 2026-01-02 | {fila_slug} | −10 % | −5 % | 400000 | causa | ajuste |\n" if fila else ""
        (proj / "docs" / "roadmap" / "CALIBRATION.md").write_text(CABECERA + filas, encoding="utf-8")
    return proj, carpeta


def run(*args, root=None):
    cmd = [sys.executable, SCRIPT, *args]
    if root is not None:
        cmd += ["--root", str(root)]
    r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    return r.returncode, r.stdout, r.stderr


def test_sin_retro_ni_fila_la_puerta_esta_cerrada_y_dice_el_comando_exacto(tmp_path):
    proj, carpeta = proyecto(tmp_path)
    rc, out, _ = run(str(carpeta))
    assert rc == 1 and "❌" in out
    assert "retro.md" in out and "CALIBRATION.md" in out and "/retro docs/roadmap/2026-01-01-demo" in out


def test_con_retro_pero_sin_fila_sigue_cerrada(tmp_path):
    proj, carpeta = proyecto(tmp_path, retro=True)
    rc, out, _ = run(str(carpeta))
    assert rc == 1 and "fila" in out and "retro.md" in out           # la línea de retro.md sale como ✅ y la fila como ❌
    v = rg.veredicto(str(proj), str(carpeta))
    assert v["abierta"] is False and v["faltan"] == ["fila en CALIBRATION.md"]


def test_con_retro_y_fila_la_puerta_abre(tmp_path):
    proj, carpeta = proyecto(tmp_path, retro=True, fila=True)
    rc, out, _ = run(str(carpeta))
    assert rc == 0 and "✅" in out and "❌" not in out
    assert rg.veredicto(str(proj), str(carpeta))["faltan"] == []


def test_la_fila_casa_con_o_sin_acentos_graves_y_con_la_carpeta_completa(tmp_path):
    for i, fila_slug in enumerate(("demo", "`demo`", "2026-01-01-demo", " `2026-01-01-demo` ")):
        proj, carpeta = proyecto(tmp_path / f"caso{i}", retro=True, fila=True, fila_slug=fila_slug)
        assert run(str(carpeta))[0] == 0, fila_slug
    proj, carpeta = proyecto(tmp_path / "otra", retro=True, fila=True, fila_slug="`demo-2`")   # otra iniciativa NO vale
    assert run(str(carpeta))[0] == 1


def test_acepta_slug_ruta_relativa_o_absoluta_con_root(tmp_path):
    proj, carpeta = proyecto(tmp_path, retro=True, fila=True)
    assert run("2026-01-01-demo", root=proj)[0] == 0
    assert run("docs/roadmap/2026-01-01-demo", root=proj)[0] == 0
    assert run(str(carpeta), root=proj)[0] == 0
    assert run("demo", root=proj)[0] == 0                              # slug sin fecha: una sola carpeta que termine así


def test_sin_calibration_md_la_puerta_esta_cerrada_y_lo_dice(tmp_path):
    proj, carpeta = proyecto(tmp_path, retro=True, cal=False)
    rc, out, _ = run(str(carpeta))
    assert rc == 1 and "CALIBRATION.md" in out and "no existe" in out


def test_retro_vacia_o_sin_frontmatter_no_cuenta(tmp_path):
    proj, carpeta = proyecto(tmp_path, fila=True)
    (carpeta / "retro.md").write_text("", encoding="utf-8")
    assert run(str(carpeta))[0] == 1
    (carpeta / "retro.md").write_text("# solo un título\n", encoding="utf-8")
    rc, out, _ = run(str(carpeta))
    assert rc == 1 and "frontmatter" in out


def test_ledger_no_completado_informa_sin_cambiar_el_veredicto(tmp_path):
    proj, carpeta = proyecto(tmp_path, retro=True, fila=True, estado="en-progreso")
    rc, out, _ = run(str(carpeta))
    assert rc == 0 and "en-progreso" in out and "ℹ️" in out


def test_carpeta_inexistente_es_error_de_uso(tmp_path):
    proj, _ = proyecto(tmp_path)
    rc, out, err = run("no-existe", root=proj)
    assert rc == 2 and "no-existe" in err


def test_json(tmp_path):
    proj, carpeta = proyecto(tmp_path, retro=True)
    rc, out, _ = run(str(carpeta), "--json")
    data = json.loads(out)
    assert rc == 1 and data["abierta"] is False and data["slug"] == "demo" and data["faltan"] == ["fila en CALIBRATION.md"]
    assert data["comando"] == "/retro docs/roadmap/2026-01-01-demo" and data["retro"] is True and data["fila"] is False


def test_sin_argumentos_es_error_de_uso():
    assert run()[0] == 2


if __name__ == "__main__":
    sys.exit(pytest.main(["-q", __file__]))
