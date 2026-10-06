"""Contracts for the portable Node hook launcher and its security traversal."""
import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_node_launcher_only_needs_read_permission(tmp_path, monkeypatch):
    lint = load(ROOT / "scripts/lint_plugin.py", "launcher_lint")
    script = tmp_path / "hooks" / "run-hook.mjs"
    script.parent.mkdir()
    script.write_text("console.log('ok');", encoding="utf8")
    monkeypatch.setattr(lint.os, "access", lambda *_: False)
    command = 'node "${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.mjs" session-context.sh'
    assert lint.lint_hook_commands(str(tmp_path), [command], "fixture") == ([], [])


def test_security_traverses_launcher_and_rejects_network_mutation(tmp_path):
    security = load(ROOT / "tests/test_graphiti_security.py", "launcher_security")
    root = security._repo_minimo(tmp_path, hooks_json={"hooks": {"SessionStart": [{"hooks": [{
        "command": 'node "${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.mjs" session-context.sh'
    }]}]}}, ficheros={"hooks/run-hook.mjs": "fetch('https://example.invalid');\n",
                     "hooks/session-context.sh": "echo ok\n"})
    reached, unresolved = security._recorrido_hooks(root)
    assert "hooks/run-hook.mjs" in reached
    assert "hooks/session-context.sh" in reached
    assert not unresolved
    assert any(path == "hooks/run-hook.mjs" and "fetch" in reason
               for path, reason in security._ofensores_de_red(root))


@pytest.mark.parametrize("code", [
    "import https from 'https'; https.get('https://example.invalid');",
    "import {spawnSync} from 'node:child_process'; spawnSync('curl', ['https://example.invalid']);",
    "fetch ('https://example.invalid');",
    "import {spawnSync as run} from 'node:child_process'; run('curl', ['https://example.invalid']);",
])
def test_node_launcher_network_mutants_do_not_pass(tmp_path, code):
    security = load(ROOT / "tests/test_graphiti_security.py", "launcher_network_mutants")
    root = security._repo_minimo(tmp_path, hooks_json={"hooks": {"SessionStart": [{"hooks": [{
        "command": 'node "${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.mjs"'
    }]}]}}, ficheros={"hooks/run-hook.mjs": code})
    assert security._ofensores_de_red(root)


def test_foreign_node_launcher_path_is_never_replaced_by_local_source(tmp_path):
    security = load(ROOT / "tests/test_graphiti_security.py", "launcher_foreign_mutant")
    command = """node -e "const p=require('path');require('child_process').spawnSync('node',[p.join('/tmp/foreign','hooks','run-hook.mjs')]);" """
    root = security._repo_minimo(tmp_path, hooks_json={"hooks": {"SessionStart": [{"hooks": [{
        "command": command
    }]}]}}, ficheros={"hooks/run-hook.mjs": "console.log('clean local source');"})
    reached, unresolved = security._recorrido_hooks(root)
    assert "hooks/run-hook.mjs" not in reached
    assert unresolved


def test_foreign_root_variable_does_not_resolve_to_local_launcher(tmp_path):
    security = load(ROOT / "tests/test_graphiti_security.py", "launcher_foreign_variable")
    root = security._repo_minimo(tmp_path, hooks_json={"hooks": {"SessionStart": [{"hooks": [{
        "command": 'node "${FOREIGN_ROOT}/hooks/run-hook.mjs"'
    }]}]}}, ficheros={"hooks/run-hook.mjs": "console.log('clean local source');"})
    reached, unresolved = security._recorrido_hooks(root)
    assert "hooks/run-hook.mjs" not in reached
    assert unresolved
