#!/usr/bin/env python3
"""Tests de retro-gate.py (memory-retrieval T-17; spec CA-23): la retro es una PUERTA del cierre de una
iniciativa, no un aviso que se pueda ignorar (`LES-012`). Ejecutar: python3 -m pytest -q agent-kits/shared/test_retro_gate.py"""
import glob
import importlib.util
import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "retro-gate.py")
ROOT = os.path.dirname(os.path.dirname(HERE))
RETROS_REALES = sorted(glob.glob(os.path.join(ROOT, "docs", "roadmap", "*", "retro.md")))
# El formato REAL que escribe `/retro` (las 7 retros del repo): título + secciones, SIN frontmatter.
RETRO_REAL = "# Retro — demo\n\n## Estimado vs real\n\n| | est | real |\n|---|---|---|\n| horas | 2 | 1 |\n\n## Causas\n\n- una\n"

spec = importlib.util.spec_from_file_location("retro_gate", SCRIPT)
rg = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rg)

CABECERA = ("# CALIBRATION\n\n| Fecha | Iniciativa | Desv. producción | Desv. tokens | tokens/hora (medido) | Causa principal | "
            "Ajuste sugerido |\n|---|---|---|---|---|---|---|\n")


def proyecto(tmp_path, slug="2026-01-01-demo", retro=False, fila=False, estado="completado", cal=True, fila_slug="`demo`",
             retro_texto=RETRO_REAL):
    proj = tmp_path / "proj"
    carpeta = proj / "docs" / "roadmap" / slug
    carpeta.mkdir(parents=True)
    (carpeta / "tasks.md").write_text(f"---\ntasks: demo\nestado: {estado}\n---\n# Checklist\n", encoding="utf-8")
    if retro:
        (carpeta / "retro.md").write_text(retro_texto, encoding="utf-8")
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


def test_retro_vacia_solo_titulos_o_frontmatter_sin_cerrar_no_cuenta(tmp_path):
    proj, carpeta = proyecto(tmp_path, fila=True)
    (carpeta / "retro.md").write_text("", encoding="utf-8")
    assert run(str(carpeta))[0] == 1
    (carpeta / "retro.md").write_text("# solo un título\n\n## y otro\n", encoding="utf-8")
    rc, out, _ = run(str(carpeta))
    assert rc == 1 and "sin cuerpo" in out
    (carpeta / "retro.md").write_text("texto suelto sin título\n", encoding="utf-8")
    rc, out, _ = run(str(carpeta))
    assert rc == 1 and "sin título" in out
    # frontmatter sin cerrar: una regla horizontal `----` NO es el cierre (gap B5)
    (carpeta / "retro.md").write_text("---\nr: 1\n# Retro sin cerrar\n\n----\nmas cuerpo\n", encoding="utf-8")
    rc, out, _ = run(str(carpeta))
    assert rc == 1 and "sin cerrar" in out
    assert rg.retro_ok(str(carpeta)) == (False, "retro.md con frontmatter sin cerrar (`---` … `---`)")
    # con frontmatter bien cerrado y cuerpo, también vale
    (carpeta / "retro.md").write_text("---\nretro: demo\n---\n# Retro\n\ncausas\n", encoding="utf-8")
    assert run(str(carpeta))[0] == 0
    (carpeta / "retro.md").write_text("---\nretro: demo\n---\n", encoding="utf-8")
    assert run(str(carpeta))[0] == 1


def test_el_formato_real_de_retro_sin_frontmatter_abre_la_puerta(tmp_path):
    """Gap B1 (Critical): la primera versión exigía frontmatter y `/retro` nunca lo escribe — la puerta no
    habría abierto para ninguna retro real y su propio arreglo la volvía a cerrar."""
    proj, carpeta = proyecto(tmp_path, retro=True, fila=True)              # RETRO_REAL: `# Retro — …`, sin `---`
    rc, out, _ = run(str(carpeta))
    assert rc == 0 and "título y cuerpo" in out


@pytest.mark.skipif(not RETROS_REALES, reason="sin retros reales en docs/roadmap/")
@pytest.mark.parametrize("retro", RETROS_REALES, ids=[os.path.basename(os.path.dirname(r)) for r in RETROS_REALES])
def test_las_retros_reales_del_repo_cumplen_el_contrato(retro):
    ok, motivo = rg.retro_ok(os.path.dirname(retro))
    assert ok, motivo


def test_una_carpeta_con_tasks_md_fuera_de_docs_roadmap_es_error_de_uso(tmp_path):
    """Gap B4: antes abría la puerta contra el CALIBRATION.md de otro proyecto y devolvía rutas inexistentes."""
    proj, _ = proyecto(tmp_path, retro=True, fila=True)                     # el `--root` ajeno tiene una fila para `demo`
    suelta = tmp_path / "suelta"
    suelta.mkdir()
    (suelta / "tasks.md").write_text("---\nestado: completado\n---\n", encoding="utf-8")
    (suelta / "retro.md").write_text(RETRO_REAL, encoding="utf-8")
    rc, out, err = run(str(suelta), root=proj)
    assert rc == 2 and "fuera de docs/roadmap/" in err and out == ""


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
