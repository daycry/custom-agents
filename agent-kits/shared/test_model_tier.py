#!/usr/bin/env python3
"""Tests de model-tier.py (parity-core T-01): resolutor DETERMINISTA del tier efectivo de un agente
(frontmatter `model`/`effort` + override parcial por agente en `.claude/dev.json` → `modelos`).

Ejecutar: python3 -m pytest -q agent-kits/shared/test_model_tier.py
"""
import importlib.util
import json
import os
import sys

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "model-tier.py")


def _mod():
    spec = importlib.util.spec_from_file_location("model_tier", SCRIPT)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


mt = _mod()

AGENT = """---
name: {name}
description: Hace algo. Úsalo cuando el usuario diga "x".
model: {model}
{effort}tools: Read
dependencies:
  skills: []
  kits: []
  agents: []
---
# {name}
"""


@pytest.fixture
def plugin(tmp_path):
    root = tmp_path / "plugin"
    (root / "agents").mkdir(parents=True)
    (root / "agents" / "architect.md").write_text(
        AGENT.format(name="architect", model="opus", effort="effort: high\n"), encoding="utf-8")
    (root / "agents" / "pdfy.md").write_text(
        AGENT.format(name="pdfy", model="haiku", effort=""), encoding="utf-8")
    proj = tmp_path / "proj"
    (proj / ".claude").mkdir(parents=True)
    return str(root), str(proj)


def _dev(proj, data):
    p = os.path.join(proj, ".claude", "dev.json")
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(data if isinstance(data, str) else json.dumps(data))


def test_sin_dev_json_devuelve_frontmatter(plugin):
    root, proj = plugin
    r = mt.resolver("architect", root=root, project=proj)
    assert (r["model"], r["effort"]) == ("opus", "high")
    assert r["fuente"] == {"model": "frontmatter", "effort": "frontmatter"}
    assert r["avisos"] == []


def test_dev_json_override_model_y_effort(plugin):
    root, proj = plugin
    _dev(proj, {"modelos": {"architect": {"model": "sonnet", "effort": "medium"}}})
    r = mt.resolver("architect", root=root, project=proj)
    assert (r["model"], r["effort"]) == ("sonnet", "medium")
    assert r["fuente"] == {"model": "dev.json", "effort": "dev.json"}


def test_override_parcial_solo_effort(plugin):
    root, proj = plugin
    _dev(proj, {"modelos": {"architect": {"effort": "xhigh"}}})
    r = mt.resolver("architect", root=root, project=proj)
    assert (r["model"], r["effort"]) == ("opus", "xhigh")
    assert r["fuente"] == {"model": "frontmatter", "effort": "dev.json"}


def test_valor_invalido_se_ignora_con_aviso(plugin):
    root, proj = plugin
    _dev(proj, {"modelos": {"architect": {"model": "gpt-9", "effort": "ultra"}}})
    r = mt.resolver("architect", root=root, project=proj)
    assert (r["model"], r["effort"]) == ("opus", "high")
    assert r["fuente"] == {"model": "frontmatter", "effort": "frontmatter"}
    assert len(r["avisos"]) == 2 and all("inválido" in a for a in r["avisos"])


def test_model_id_completo_es_valido(plugin):
    root, proj = plugin
    _dev(proj, {"modelos": {"architect": {"model": "claude-opus-4-1-20250805"}}})
    r = mt.resolver("architect", root=root, project=proj)
    assert r["model"] == "claude-opus-4-1-20250805" and r["fuente"]["model"] == "dev.json"


def test_dev_json_corrupto_degrada_a_frontmatter(plugin):
    root, proj = plugin
    _dev(proj, "{ esto no es json")
    r = mt.resolver("architect", root=root, project=proj)
    assert (r["model"], r["effort"]) == ("opus", "high")
    assert any("dev.json" in a for a in r["avisos"])


def test_dev_json_raiz_no_objeto_avisa(plugin):
    root, proj = plugin
    _dev(proj, "[1, 2, 3]")
    r = mt.resolver("architect", root=root, project=proj)
    assert (r["model"], r["effort"]) == ("opus", "high")
    assert any("no es un objeto" in a for a in r["avisos"])


def test_sin_effort_en_frontmatter_hereda(plugin):
    root, proj = plugin
    r = mt.resolver("pdfy", root=root, project=proj)
    assert r["model"] == "haiku"
    assert r["effort"] == "inherit" and r["fuente"]["effort"] == "heredado"


def test_agente_inexistente_exit_1(plugin, capsys):
    root, proj = plugin
    assert mt.main(["fantasma", "--root", root, "--project", proj]) == 1
    assert "fantasma" in capsys.readouterr().err


def test_json_y_texto(plugin, capsys):
    root, proj = plugin
    _dev(proj, {"modelos": {"architect": {"model": "sonnet"}}})
    assert mt.main(["architect", "--root", root, "--project", proj, "--json"]) == 0
    data = json.loads(capsys.readouterr().out)
    assert set(data) >= {"agente", "model", "effort", "fuente", "avisos"}
    assert data["model"] == "sonnet"
    assert mt.main(["architect", "--root", root, "--project", proj]) == 0
    out = capsys.readouterr().out
    assert "architect" in out and "model=sonnet" in out and "dev.json" in out


def test_all_lista_todos_los_agentes(plugin, capsys):
    root, proj = plugin
    assert mt.main(["--all", "--root", root, "--project", proj]) == 0
    out = capsys.readouterr().out
    assert "architect" in out and "pdfy" in out and "opus" in out and "haiku" in out


def test_plugin_no_localizado_exit_2(tmp_path, capsys):
    assert mt.main(["architect", "--root", str(tmp_path / "nada"), "--project", str(tmp_path)]) == 2


def test_cli_real_del_repo():
    """Sobre el repo real: architect resuelve a opus/high sin dev.json (sanidad del script en sitio)."""
    import subprocess
    repo = os.path.dirname(os.path.dirname(HERE))
    if not os.path.isfile(os.path.join(repo, "agents", "architect.md")):
        pytest.skip("agents/architect.md aún no existe")
    r = subprocess.run([sys.executable, SCRIPT, "architect", "--root", repo, "--project", str(os.devnull),
                        "--json"], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    assert data["model"] == "opus" and data["effort"] == "high"
