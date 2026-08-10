#!/usr/bin/env python3
"""Tests de lint_plugin.py con fixtures sintéticas. Ejecuta: python tests/test_lint_plugin.py"""
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPT = os.path.join(ROOT, "scripts", "lint_plugin.py")

AGENT_OK = """---
name: {name}
description: Hace algo útil. Úsalo cuando el usuario diga "haz X".
model: sonnet
tools: Read, Grep, Glob, Bash, Write, Edit
dependencies:
  skills:
    - my-skill
  kits:
    - agent-kits/my-kit
  agents: []
---
# {name}
Cuerpo del agente.
"""


def make_plugin(tmp, agents):
    """agents: dict name -> frontmatter string (ya formateado)."""
    os.makedirs(os.path.join(tmp, "agents"))
    os.makedirs(os.path.join(tmp, "skills", "my-skill"))
    open(os.path.join(tmp, "skills", "my-skill", "SKILL.md"), "w").write("x")
    os.makedirs(os.path.join(tmp, "agent-kits", "my-kit"))
    for name, body in agents.items():
        open(os.path.join(tmp, "agents", name + ".md"), "w", encoding="utf-8").write(body)


def run(tmp):
    r = subprocess.run([sys.executable, SCRIPT, "--root", tmp],
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def main():
    # 1) Plugin válido → exit 0
    with tempfile.TemporaryDirectory() as tmp:
        make_plugin(tmp, {"alpha": AGENT_OK.format(name="alpha")})
        code, out = run(tmp)
        assert code == 0, f"esperaba 0, fue {code}\n{out}"
        assert "0 errores" in out, out

    # 2) Falta el campo model → error
    with tempfile.TemporaryDirectory() as tmp:
        body = AGENT_OK.format(name="alpha").replace("model: sonnet\n", "")
        make_plugin(tmp, {"alpha": body})
        code, out = run(tmp)
        assert code == 1, f"esperaba 1\n{out}"
        assert "requerido `model`" in out, out

    # 3) model inválido → error
    with tempfile.TemporaryDirectory() as tmp:
        body = AGENT_OK.format(name="alpha").replace("model: sonnet", "model: gpt-turbo")
        make_plugin(tmp, {"alpha": body})
        code, out = run(tmp)
        assert code == 1 and "no es válido" in out, out

    # 4) dependencia a agente inexistente → error
    with tempfile.TemporaryDirectory() as tmp:
        body = AGENT_OK.format(name="alpha").replace("agents: []", "agents:\n    - fantasma")
        make_plugin(tmp, {"alpha": body})
        code, out = run(tmp)
        assert code == 1 and "handoff inexistente" in out, out

    # 5) skill inexistente → error
    with tempfile.TemporaryDirectory() as tmp:
        body = AGENT_OK.format(name="alpha").replace("- my-skill", "- no-existe")
        make_plugin(tmp, {"alpha": body})
        code, out = run(tmp)
        assert code == 1 and "skill declarada inexistente" in out, out

    # 6) ciclo entre agentes → error
    with tempfile.TemporaryDirectory() as tmp:
        a = AGENT_OK.format(name="alpha").replace("agents: []", "agents:\n    - beta")
        b = AGENT_OK.format(name="beta").replace("agents: []", "agents:\n    - alpha")
        make_plugin(tmp, {"alpha": a, "beta": b})
        code, out = run(tmp)
        assert code == 1 and "Ciclo" in out, out

    # 7) name != fichero → error
    with tempfile.TemporaryDirectory() as tmp:
        make_plugin(tmp, {"alpha": AGENT_OK.format(name="otro-nombre")})
        code, out = run(tmp)
        assert code == 1 and "no coincide con el nombre de fichero" in out, out

    # 8) description sin trigger → aviso (no error)
    with tempfile.TemporaryDirectory() as tmp:
        body = AGENT_OK.format(name="alpha").replace(
            'description: Hace algo útil. Úsalo cuando el usuario diga "haz X".',
            'description: Solo describe qué hace sin gatillo.')
        make_plugin(tmp, {"alpha": body})
        code, out = run(tmp)
        assert code == 0, f"el trigger es aviso, no error\n{out}"
        assert "frase-gatillo" in out, out

    print("test_lint_plugin: 8/8 OK")


if __name__ == "__main__":
    main()
