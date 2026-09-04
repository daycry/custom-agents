#!/usr/bin/env python3
"""Tests de `scripts/export-skills.py` (distribution T-01): paquete portable «solo skills».

Sobre un mini-plugin sintético (tmp_path) y sobre el repo real:
formatos, exclusiones, reescritura de `find`, determinismo + hash, `--check` positivo/negativo,
frontmatter de Cursor y AGENTS.md completo.

Ejecutar: python3 -m pytest -q tests/test_export_skills.py
"""
import importlib.util
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "export-skills.py")


def _mod():
    spec = importlib.util.spec_from_file_location("export_skills", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ES = _mod()

SKILL_A = """---
name: alpha
description: Hace alfa con el ledger. Úsala cuando el usuario diga "haz alfa".
---
# alpha
SHAREDKIT="$(find "$PWD/.claude" "$HOME/.claude" -type d -path '*agent-kits/shared' 2>/dev/null | head -1)"
Lee `references/detalle.md` en el paso 2 y ejecuta `scripts/alpha.py`.
Usa `"$SHAREDKIT/frag.md"` y `agent-kits/shared/util.py`.
"""
SKILL_B = """---
name: beta
description: Hace beta. Úsala cuando el usuario diga "haz beta".
---
# beta
REV="$(find "$PWD/.claude" "$PWD/skills" "$HOME/.claude" -type d -path '*skills/beta' 2>/dev/null | head -1)"
Plantilla en `references/<tema>.md` (placeholder, no se comprueba).
"""


@pytest.fixture
def plugin(tmp_path):
    """Mini-plugin: 2 skills que viajan + quick-implement (excluida) + shared con cierre .py→.py."""
    root = tmp_path / "plugin"
    (root / ".claude-plugin").mkdir(parents=True)
    (root / ".claude-plugin" / "plugin.json").write_text('{"name": "x", "version": "7.7.7"}')
    a = root / "skills" / "alpha"
    (a / "references").mkdir(parents=True)
    (a / "scripts" / "__pycache__").mkdir(parents=True)
    (a / "SKILL.md").write_text(SKILL_A, encoding="utf-8")
    (a / "references" / "detalle.md").write_text("# detalle\n")
    (a / "scripts" / "alpha.py").write_text("print('a')\n")
    (a / "scripts" / "test_alpha.py").write_text("def test(): pass\n")
    (a / "scripts" / "__pycache__" / "alpha.pyc").write_bytes(b"\x00")
    b = root / "skills" / "beta"
    b.mkdir(parents=True)
    (b / "SKILL.md").write_text(SKILL_B, encoding="utf-8")
    q = root / "skills" / "quick-implement"
    q.mkdir(parents=True)
    (q / "SKILL.md").write_text("---\nname: quick-implement\ndescription: atajo\n---\n")
    sh = root / "agent-kits" / "shared"
    sh.mkdir(parents=True)
    (sh / "frag.md").write_text("fragmento\n")
    (sh / "util.py").write_text('import os\nP = os.path.join(HERE, "base.py")\n')
    (sh / "base.py").write_text("x = 1\n")
    (sh / "no-citado.md").write_text("no viaja\n")
    (root / "agents").mkdir()
    (root / "agents" / "a.md").write_text("---\nname: a\n---\n")
    return root


def _run(*args):
    return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True, text=True, encoding="utf-8", errors="replace")


# ------------------------------------------------------------------ formatos y exclusiones

def test_format_all_genera_el_arbol_completo(plugin, tmp_path):
    out = tmp_path / "out"
    info = ES.exportar(str(plugin), str(out), "all", quiet=True)
    rels = ES.listar(str(out))
    assert info["skills"] == ["alpha", "beta"]                    # quick-implement excluida
    assert "README.md" in rels and "AGENTS.md" in rels
    assert ".cursor/rules/custom-agents-skills.mdc" in rels
    assert "skills/alpha/SKILL.md" in rels and "skills/alpha/references/detalle.md" in rels
    assert "skills/alpha/scripts/alpha.py" in rels
    assert not any("quick-implement" in r or "__pycache__" in r or "test_alpha" in r for r in rels)
    assert not any(r.startswith("agents/") for r in rels)


def test_format_claude_solo_skills_y_shared(plugin, tmp_path):
    out = tmp_path / "out"
    ES.exportar(str(plugin), str(out), "claude", quiet=True)
    rels = ES.listar(str(out))
    assert "AGENTS.md" not in rels and not any(r.startswith(".cursor/") for r in rels)
    assert "README.md" in rels and "skills/alpha/SKILL.md" in rels
    assert "agent-kits/shared/frag.md" in rels


def test_shared_solo_lo_citado_con_cierre(plugin, tmp_path):
    out = tmp_path / "out"
    info = ES.exportar(str(plugin), str(out), "claude", quiet=True)
    # frag.md ($SHAREDKIT/…), util.py (agent-kits/shared/…) y base.py (cargado por util.py); no-citado.md no
    assert info["shared"] == ["agent-kits/shared/base.py", "agent-kits/shared/frag.md", "agent-kits/shared/util.py"]


# ------------------------------------------------------------------ reescritura

def test_reescribe_find_pwd_claude(plugin, tmp_path):
    out = tmp_path / "out"
    info = ES.exportar(str(plugin), str(out), "claude", quiet=True)
    a = (out / "skills" / "alpha" / "SKILL.md").read_text(encoding="utf-8")
    b = (out / "skills" / "beta" / "SKILL.md").read_text(encoding="utf-8")
    assert 'find "${PORTABLE_ROOT:-.}" -type d -path \'*agent-kits/shared\'' in a
    assert 'find "${PORTABLE_ROOT:-.}" -type d -path \'*skills/beta\'' in b   # también con "$PWD/skills"
    assert info["reescritos"] == 2
    for rel in ES.listar(str(out)):
        assert 'find "$PWD/.claude"' not in (out / rel).read_text(encoding="utf-8", errors="replace"), rel
    readme = (out / "README.md").read_text(encoding="utf-8")
    assert "PORTABLE_ROOT" in readme and "2 occurrence(s)" in readme       # documentado


# ------------------------------------------------------------------ determinismo

def test_determinista_mismo_arbol_y_hash(plugin, tmp_path):
    i1 = ES.exportar(str(plugin), str(tmp_path / "o1"), "all", quiet=True)
    i2 = ES.exportar(str(plugin), str(tmp_path / "o2"), "all", quiet=True)
    assert i1["hash"] == i2["hash"]
    for rel in ES.listar(str(tmp_path / "o1")):
        assert (tmp_path / "o1" / rel).read_bytes() == (tmp_path / "o2" / rel).read_bytes(), rel
    assert f"hash: {i1['hash']}" in (tmp_path / "o1" / "README.md").read_text(encoding="utf-8")
    # regenerar sobre la misma carpeta (paquete nuestro) es idempotente
    i3 = ES.exportar(str(plugin), str(tmp_path / "o1"), "all", quiet=True)
    assert i3["hash"] == i1["hash"]


def test_no_pisa_una_carpeta_ajena(plugin, tmp_path):
    out = tmp_path / "ajena"
    out.mkdir()
    (out / "mio.txt").write_text("no borrar")
    with pytest.raises(SystemExit):
        ES.exportar(str(plugin), str(out), "claude", quiet=True)
    assert (out / "mio.txt").exists()


def test_readme_falsificado_sin_marcador_no_basta_para_borrar(plugin, tmp_path):
    """Revisión intento 1 (Minor 6): la 1.ª línea del README es falsificable; sin el fichero-marcador
    dedicado `.custom-agents-portable` no se borra nada."""
    out = tmp_path / "falsa"
    out.mkdir()
    (out / "README.md").write_text(f"<!-- {ES.MARCADOR} · hash: {'0' * 64} -->\n# fake\n", encoding="utf-8")
    (out / "mio.txt").write_text("no borrar")
    with pytest.raises(SystemExit):
        ES.exportar(str(plugin), str(out), "claude", quiet=True)
    assert (out / "mio.txt").exists() and (out / "README.md").exists()
    # marcador sin hash tampoco
    (out / ES.MARCADOR_FICHERO).write_text(f"{ES.MARCADOR}\nsin hash\n", encoding="utf-8")
    with pytest.raises(SystemExit):
        ES.exportar(str(plugin), str(out), "claude", quiet=True)
    assert (out / "mio.txt").exists()
    # un paquete real sí se regenera y lleva el marcador con el hash
    ok = tmp_path / "ok"
    info = ES.exportar(str(plugin), str(ok), "claude", quiet=True)
    marca = (ok / ES.MARCADOR_FICHERO).read_text(encoding="utf-8")
    assert marca.startswith(ES.MARCADOR) and f"hash: {info['hash']}" in marca
    assert ES.es_paquete_nuestro(str(ok))
    (ok / ES.MARCADOR_FICHERO).unlink()
    assert any("fichero-marcador" in p for p in ES.check(str(ok)))


# ------------------------------------------------------------------ --check

def test_check_ok_en_paquete_integro(plugin, tmp_path):
    out = tmp_path / "out"
    ES.exportar(str(plugin), str(out), "all", quiet=True)
    assert ES.check(str(out)) == []
    r = _run("--check", str(out))
    assert r.returncode == 0 and "0 problema(s)" in r.stdout


def test_check_detecta_referencia_ausente_y_find_colgando(plugin, tmp_path):
    out = tmp_path / "out"
    ES.exportar(str(plugin), str(out), "all", quiet=True)
    (out / "skills" / "alpha" / "references" / "detalle.md").unlink()
    problemas = ES.check(str(out))
    assert any("references/detalle.md" in p and "no existe" in p for p in problemas)
    assert any("hash" in p for p in problemas)                      # el árbol cambió
    # find colgando
    ES.exportar(str(plugin), str(out), "all", quiet=True)
    p = out / "skills" / "beta" / "SKILL.md"
    p.write_text(p.read_text(encoding="utf-8") + '\nX="$(find "$PWD/.claude" -type f)"\n', encoding="utf-8")
    problemas = ES.check(str(out))
    assert any("sin reescribir" in x for x in problemas)
    assert _run("--check", str(out)).returncode == 1


def test_check_detecta_agents_md_incompleto(plugin, tmp_path):
    out = tmp_path / "out"
    ES.exportar(str(plugin), str(out), "agents-md", quiet=True)
    ag = out / "AGENTS.md"
    ag.write_text(ag.read_text(encoding="utf-8").replace("`skills/beta/SKILL.md`", "`skills/gamma/SKILL.md`"), encoding="utf-8")
    assert any("no lista la skill `beta`" in p for p in ES.check(str(out)))


# ------------------------------------------------------------------ formatos externos

def test_cursor_mdc_frontmatter_y_agents_md_indice(plugin, tmp_path):
    out = tmp_path / "out"
    ES.exportar(str(plugin), str(out), "all", quiet=True)
    mdc = (out / ".cursor" / "rules" / "custom-agents-skills.mdc").read_text(encoding="utf-8")
    fm = mdc.split("---")[1]
    assert fm.strip().startswith("description:") and "alwaysApply: false" in fm     # modo Agent-Selected
    assert "globs:" not in fm                                                        # sin auto-attach por fichero
    ag = (out / "AGENTS.md").read_text(encoding="utf-8")
    assert not ag.startswith("---")                                                  # markdown plano, sin frontmatter
    for s in ("alpha", "beta"):
        assert f"`skills/{s}/SKILL.md`" in ag and f"`skills/{s}/SKILL.md`" in mdc
    assert "Hace alfa con el ledger" in ag                                           # resumen de skill-index
    assert "v7.7.7" in ag                                                            # versión de plugin.json


def test_readme_del_paquete_tabla_y_bilingue(plugin, tmp_path):
    out = tmp_path / "out"
    ES.exportar(str(plugin), str(out), "all", quiet=True)
    readme = (out / "README.md").read_text(encoding="utf-8")
    assert readme.startswith(f"<!-- {ES.MARCADOR}")
    assert "| `skills/alpha/` | ✅ |" in readme and "| `skills/quick-implement/` | ❌ |" in readme
    assert "`agents/`" in readme and "`commands/`" in readme and "hooks/" in readme
    assert "Spawn ALL 8 agents" in readme and "degrada" in readme and "en secuencia" in readme   # Minor 7
    assert "## Español (resumen)" in readme and "**English**" in readme


# ------------------------------------------------------------------ repo real

def test_repo_real_exporta_y_pasa_el_check(tmp_path):
    out = tmp_path / "portable"
    r = _run("--out", str(out), "--format", "all")
    assert r.returncode == 0, r.stderr
    assert "skills/adversarial-review/SKILL.md" in r.stdout and "hash:" in r.stdout
    rels = ES.listar(str(out))
    assert not any(r_.startswith(("skills/quick-implement/", "skills/plugin-dev/", "agents/", "commands/", "hooks/")) for r_ in rels)
    assert "agent-kits/shared/ledger-lint.py" in rels        # cierre: scope-check.py lo carga por nombre
    assert ES.check(str(out)) == []
    esperadas = sorted(d for d in os.listdir(os.path.join(ROOT, "skills"))
                       if os.path.isfile(os.path.join(ROOT, "skills", d, "SKILL.md")) and d not in ES.EXCLUIR_SKILLS)
    ag = (out / "AGENTS.md").read_text(encoding="utf-8")
    assert all(f"`skills/{s}/SKILL.md`" in ag for s in esperadas)
    shutil.rmtree(out)
