#!/usr/bin/env python3
"""Tests de `changelog-sync.py` (superiority T-02). Sin red, sin modelo: fixtures en tmp."""
import importlib.util
import json
import os
import subprocess
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "changelog-sync.py")


def _mod():
    spec = importlib.util.spec_from_file_location("changelog_sync", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


cs = _mod()

EN = """# Changelog

## [Unreleased]

## [1.0.0] - 2026-01-01

### Added

- algo previo con `viejo-slug`

[1.0.0]: https://example.invalid/releases/tag/v1.0.0
"""
ES = EN.replace("## [Unreleased]", "## [Sin publicar]")

LEDGER = """---
tasks: {slug}
descripcion: {desc}
estado: {estado}
{extra}---

# Checklist de Tareas — {slug}

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase única — x | 1 | 1 | 100% |

## Fase única — x

**Estado**: completado

### T-01 — Hacer la cosa

- **Descripción**: Primera frase de la tarea. Segunda frase que NO debe salir.
- **Estado**: completado
- **Archivos**: `a.py` (nuevo), `b.md`, `c.json`, `d.sh`, `e.txt`, `f.ini`
- **Verificación**: `pytest -q` → verde

**Criterios de aceptación**
- [x] hecho
"""


def proyecto(tmp, slug="demo", estado="completado", desc="Añade la cosa nueva.", extra="", fecha="2026-05-05"):
    d = os.path.join(tmp, "docs", "roadmap", f"{fecha}-{slug}")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "tasks.md"), "w", encoding="utf-8") as fh:
        fh.write(LEDGER.format(slug=slug, estado=estado, desc=desc, extra=extra))
    for fn, body in (("CHANGELOG.md", EN), ("CHANGELOG.es.md", ES)):
        p = os.path.join(tmp, fn)
        if not os.path.exists(p):
            open(p, "w", encoding="utf-8").write(body)
    return tmp


def run(*args, root=None):
    cmd = [sys.executable, SCRIPT] + (["--root", root] if root else []) + list(args)
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")


def test_genera_en_y_es_con_un_bullet_por_tarea(tmp_path):
    root = proyecto(str(tmp_path))
    r = run(root=root)
    assert r.returncode == 0, r.stdout + r.stderr
    en = open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read()
    es = open(os.path.join(root, "CHANGELOG.es.md"), encoding="utf-8").read()
    assert "### Added — `demo` initiative (2026-05-05)" in en
    assert "### Added — iniciativa `demo` (2026-05-05)" in es
    assert "**T-01 — Hacer la cosa** Primera frase de la tarea." in en
    assert "Segunda frase" not in en, "solo la primera frase de la Descripción"
    # como mucho 5 archivos, sin la anotación entre paréntesis
    assert "`a.py`, `b.md`, `c.json`, `d.sh`, `e.txt`" in en and "`f.ini`" not in en
    assert "(nuevo)" not in en.split("### Added")[1].split("\n\n")[1]
    # la entrada va DENTRO de la sección abierta, antes de la versión publicada
    assert en.index("### Added — `demo`") < en.index("## [1.0.0]")


def test_idempotente_segunda_ejecucion_no_cambia_nada(tmp_path):
    root = proyecto(str(tmp_path))
    run(root=root)
    antes = open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read()
    r = run(root=root)
    assert r.returncode == 0 and "sin entradas pendientes" in r.stdout
    assert open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read() == antes


def test_dry_run_no_escribe_pero_muestra(tmp_path):
    root = proyecto(str(tmp_path))
    antes = open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read()
    r = run("--dry-run", root=root)
    assert r.returncode == 0 and "--dry-run" in r.stdout and "`demo` initiative" in r.stdout
    assert open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read() == antes


def test_check_exit_1_pendiente_y_0_tras_sincronizar(tmp_path):
    root = proyecto(str(tmp_path))
    r = run("--check", root=root)
    assert r.returncode == 1 and "PENDIENTES" in r.stdout
    run(root=root)
    r = run("--check", root=root)
    assert r.returncode == 0 and "sin entradas pendientes" in r.stdout


def test_slug_ya_presente_no_se_duplica(tmp_path):
    root = proyecto(str(tmp_path), slug="viejo-slug")   # ya citado en el CHANGELOG fixture
    r = run("--check", root=root)
    assert r.returncode == 0, r.stdout


def test_ledger_no_cerrado_se_ignora(tmp_path):
    root = proyecto(str(tmp_path), estado="en-progreso")
    r = run("--check", root=root)
    assert r.returncode == 0 and "sin entradas pendientes" in r.stdout


def test_only_limita_a_una_iniciativa_y_slug_inexistente_es_uso(tmp_path):
    root = proyecto(str(tmp_path), slug="uno", fecha="2026-05-05")
    proyecto(root, slug="dos", fecha="2026-05-06")
    r = run("--only", "uno", root=root)
    assert r.returncode == 0
    en = open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read()
    assert "`uno`" in en and "`dos`" not in en
    r = run("--only", "fantasma", root=root)
    assert r.returncode == 2 and "fantasma" in r.stderr


def test_categoria_heuristica_y_override(tmp_path):
    r1 = proyecto(str(tmp_path / "a"), slug="fx", desc="Corrige el bug del parser.")
    assert run("--check", "--json", root=r1).stdout.count('"categoria": "Fixed"') == 1
    r2 = proyecto(str(tmp_path / "b"), slug="ch", desc="Retira el agente duplicado.")
    assert run("--check", "--json", root=r2).stdout.count('"categoria": "Changed"') == 1
    r3 = proyecto(str(tmp_path / "c"), slug="ov", desc="Corrige el bug.", extra="changelog: Added\n")
    assert run("--check", "--json", root=r3).stdout.count('"categoria": "Added"') == 1


def test_sin_changelog_es_error_de_uso(tmp_path):
    root = proyecto(str(tmp_path))
    os.remove(os.path.join(root, "CHANGELOG.es.md"))
    r = run("--check", root=root)
    assert r.returncode == 2 and "CHANGELOG.es.md" in r.stderr


def test_ledger_legacy_sin_frontmatter_avisa_y_no_rompe(tmp_path):
    root = proyecto(str(tmp_path))
    d = os.path.join(root, "docs", "roadmap", "2026-01-01-legacy")
    os.makedirs(d)
    open(os.path.join(d, "tasks.md"), "w", encoding="utf-8").write("# Checklist\n\n### T-01 — x\n")
    r = run("--check", root=root)
    assert "legacy" in r.stdout and r.returncode == 1


def test_json_coherente_con_el_texto(tmp_path):
    root = proyecto(str(tmp_path))
    r = run("--check", "--json", root=root)
    d = json.loads(r.stdout)
    assert d["pendientes"][0]["slug"] == "demo" and d["pendientes"][0]["tareas"] == 1
    assert d["pendientes"][0]["ficheros"] == ["CHANGELOG.md", "CHANGELOG.es.md"]


def test_orden_por_fecha_lo_mas_reciente_arriba(tmp_path):
    root = proyecto(str(tmp_path), slug="viejo", fecha="2026-05-01")
    proyecto(root, slug="nuevo", fecha="2026-05-09")
    run(root=root)
    en = open(os.path.join(root, "CHANGELOG.md"), encoding="utf-8").read()
    assert en.index("`nuevo`") < en.index("`viejo`")


def test_primera_frase_no_corta_abreviaturas():
    assert cs.primera_frase("Usa `p. ej.` esto. Y otra cosa.") == "Usa `p. ej.` esto."


def main():
    sys.exit(pytest.main([os.path.abspath(__file__), "-q"]))


if __name__ == "__main__":
    main()
