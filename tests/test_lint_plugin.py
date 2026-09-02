#!/usr/bin/env python3
"""Tests de lint_plugin.py con fixtures sintéticas. Ejecuta: python tests/test_lint_plugin.py"""
import json
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

    # 9) hooks/hooks.json: JSON válido y cada `command` apunta a un fichero existente y ejecutable
    with tempfile.TemporaryDirectory() as tmp:
        make_plugin(tmp, {"alpha": AGENT_OK.format(name="alpha")})
        os.makedirs(os.path.join(tmp, "hooks"))
        hook = os.path.join(tmp, "hooks", "ok.sh")
        open(hook, "w").write("#!/usr/bin/env bash\nexit 0\n")
        os.chmod(hook, 0o755)
        open(os.path.join(tmp, "hooks", "hooks.json"), "w").write(json.dumps({"hooks": {
            "PostToolUse": [{"matcher": "Write|Edit", "hooks": [
                {"type": "command", "command": 'bash "${CLAUDE_PLUGIN_ROOT}/hooks/ok.sh"'}]}],
            "SessionStart": [{"matcher": "startup|resume|compact", "hooks": [
                {"type": "command", "command": 'bash "${CLAUDE_PLUGIN_ROOT}/hooks/ok.sh"'}]}],
            "SubagentStop": [{"hooks": [
                {"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/ok.sh"}]}],
        }}))
        code, out = run(tmp)
        assert code == 0 and "0 errores" in out, out

    # 10) hook cuyo command referencia un fichero inexistente → error
    with tempfile.TemporaryDirectory() as tmp:
        make_plugin(tmp, {"alpha": AGENT_OK.format(name="alpha")})
        os.makedirs(os.path.join(tmp, "hooks"))
        open(os.path.join(tmp, "hooks", "hooks.json"), "w").write(json.dumps({"hooks": {
            "PostToolUse": [{"matcher": "Write", "hooks": [
                {"type": "command", "command": 'bash "${CLAUDE_PLUGIN_ROOT}/hooks/fantasma.sh"'}]}]}}))
        code, out = run(tmp)
        assert code == 1 and "fantasma.sh" in out and "no existe" in out, out

    # 11) hook existente pero NO ejecutable → AVISO (no error); hooks.json inválido → error
    with tempfile.TemporaryDirectory() as tmp:
        make_plugin(tmp, {"alpha": AGENT_OK.format(name="alpha")})
        os.makedirs(os.path.join(tmp, "hooks"))
        hook = os.path.join(tmp, "hooks", "noexec.sh")
        open(hook, "w").write("exit 0\n")
        os.chmod(hook, 0o644)
        open(os.path.join(tmp, "hooks", "hooks.json"), "w").write(json.dumps({"hooks": {
            "PostToolUse": [{"hooks": [{"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/noexec.sh"}]}]}}))
        code, out = run(tmp)
        assert code == 0 and "no es ejecutable" in out, f"ejecutable es aviso, no error\n{out}"
        open(os.path.join(tmp, "hooks", "hooks.json"), "w").write("{ esto no es json")
        code, out = run(tmp)
        assert code == 1 and "hooks.json" in out and "JSON" in out, out

    # 12) campos nativos `skills:` + `hooks:` válidos (skill existe y está en dependencies; hook existe) → 0 errores
    NATIVO = """---
name: alpha
description: Hace algo útil. Úsalo cuando el usuario diga "haz X".
model: sonnet
tools: Read, Write
skills:
  - my-skill
hooks:
  PreToolUse:
    - matcher: "Write|Edit|Bash"
      hooks:
        - type: command
          command: 'f="${{CLAUDE_PLUGIN_ROOT}}/hooks/{hook}"; [ -f "$f" ] && exec bash "$f"; exit 0'
dependencies:
  skills:
    - my-skill
  kits: []
  agents: []
---
# alpha
"""
    with tempfile.TemporaryDirectory() as tmp:
        make_plugin(tmp, {"alpha": NATIVO.format(hook="guard.sh")})
        os.makedirs(os.path.join(tmp, "hooks"))
        hook = os.path.join(tmp, "hooks", "guard.sh")
        open(hook, "w").write("#!/usr/bin/env bash\nexit 0\n")
        os.chmod(hook, 0o755)
        code, out = run(tmp)
        assert code == 0 and "0 errores" in out, out

    # 13) `skills:` con skill inexistente → error; existente pero NO en dependencies.skills → error
    with tempfile.TemporaryDirectory() as tmp:
        make_plugin(tmp, {"alpha": NATIVO.format(hook="guard.sh").replace("skills:\n  - my-skill", "skills:\n  - fantasma")})
        os.makedirs(os.path.join(tmp, "hooks")); open(os.path.join(tmp, "hooks", "guard.sh"), "w").write("exit 0\n")
        code, out = run(tmp)
        assert code == 1 and "precargada" in out and "fantasma" in out, out
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "skills", "otra"))
        open(os.path.join(tmp, "skills", "otra", "SKILL.md"), "w").write("x")
        make_plugin(tmp, {"alpha": NATIVO.format(hook="guard.sh").replace("skills:\n  - my-skill", "skills:\n  - otra")})
        os.makedirs(os.path.join(tmp, "hooks")); open(os.path.join(tmp, "hooks", "guard.sh"), "w").write("exit 0\n")
        code, out = run(tmp)
        assert code == 1 and "no está en `dependencies.skills`" in out, out

    # 14) `hooks:` del frontmatter cuyo command referencia un fichero inexistente → error
    with tempfile.TemporaryDirectory() as tmp:
        make_plugin(tmp, {"alpha": NATIVO.format(hook="no-existe.sh")})
        code, out = run(tmp)
        assert code == 1 and "no-existe.sh" in out and "[hooks]" in out, out

    # 15) `skills:` que precarga > 16 KB → AVISO token-diet (no error); precarga pequeña → sin aviso
    with tempfile.TemporaryDirectory() as tmp:
        make_plugin(tmp, {"alpha": NATIVO.format(hook="guard.sh")})
        os.makedirs(os.path.join(tmp, "hooks")); open(os.path.join(tmp, "hooks", "guard.sh"), "w").write("exit 0\n")
        code, out = run(tmp)
        assert code == 0 and "token-diet" not in out, out
        open(os.path.join(tmp, "skills", "my-skill", "SKILL.md"), "w").write("x" * (17 * 1024))
        code, out = run(tmp)
        assert code == 0 and "token-diet" in out and "precarga 17 KB" in out, out

    # 16) [debt-cleanup T-01c] hooks/*.json con bit ejecutable → AVISO (no error); sin bit → sin aviso
    with tempfile.TemporaryDirectory() as tmp:
        make_plugin(tmp, {"alpha": AGENT_OK.format(name="alpha")})
        os.makedirs(os.path.join(tmp, "hooks"))
        hook = os.path.join(tmp, "hooks", "ok.sh")
        open(hook, "w").write("exit 0\n"); os.chmod(hook, 0o755)
        hj = os.path.join(tmp, "hooks", "hooks.json")
        open(hj, "w").write(json.dumps({"hooks": {"PostToolUse": [{"hooks": [
            {"type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/hooks/ok.sh"}]}]}}))
        os.chmod(hj, 0o644)
        code, out = run(tmp)
        assert code == 0 and "no debería ser ejecutable" not in out, out
        os.chmod(hj, 0o755)
        code, out = run(tmp)
        assert code == 0 and "hooks/hooks.json: un .json no debería ser ejecutable" in out, out
        # 16b) versionado en git con modo 100644 pero bit ejecutable en el FS (montajes OneDrive/
        # Windows/WSL muestran todo como ejecutable) → manda el ÍNDICE: sin aviso.
        import subprocess as _sp
        if _sp.run(["git", "--version"], capture_output=True).returncode == 0:
            g = ["git", "-C", tmp]
            _sp.run(g + ["init", "-q"], check=True)
            _sp.run(g + ["-c", "core.fileMode=true", "add", "hooks/hooks.json"], check=True)
            _sp.run(g + ["update-index", "--chmod=-x", "hooks/hooks.json"], check=True)
            os.chmod(hj, 0o755)
            code, out = run(tmp)
            assert code == 0 and "no debería ser ejecutable" not in out, f"el índice manda\n{out}"

    # 17) [debt-cleanup T-04b] nombre genérico: skill compuesta `adversarial-review` sin aviso;
    #     skill `review` con aviso; command `setup` con aviso (regla original para commands)
    with tempfile.TemporaryDirectory() as tmp:
        make_plugin(tmp, {"alpha": AGENT_OK.format(name="alpha")})
        for sk in ("adversarial-review", "review"):
            os.makedirs(os.path.join(tmp, "skills", sk))
            open(os.path.join(tmp, "skills", sk, "SKILL.md"), "w").write("x")
        os.makedirs(os.path.join(tmp, "commands"))
        open(os.path.join(tmp, "commands", "setup.md"), "w").write("# setup\n")
        open(os.path.join(tmp, "commands", "roadmap-status.md"), "w").write("# rs\n")
        code, out = run(tmp)
        assert code == 0, out
        assert "skill `adversarial-review`" not in out, out
        assert "skill `review`: nombre genérico" in out, out
        assert "command `setup`: nombre genérico" in out, out
        assert "command `roadmap-status`: nombre genérico" in out, out
        assert "3 avisos" in out, out

    # 18) [debt-cleanup T-04a] ci.yml.MANUAL-COPY vs .github/workflows/ci.yml: iguales → sin aviso;
    #     distintos → AVISO con el `cp` a ejecutar; sin copia en .github → sin aviso
    with tempfile.TemporaryDirectory() as tmp:
        make_plugin(tmp, {"alpha": AGENT_OK.format(name="alpha")})
        open(os.path.join(tmp, "ci.yml.MANUAL-COPY"), "w").write("name: CI\n")
        code, out = run(tmp)
        assert code == 0 and "MANUAL-COPY" not in out, out
        os.makedirs(os.path.join(tmp, ".github", "workflows"))
        open(os.path.join(tmp, ".github", "workflows", "ci.yml"), "w").write("name: CI\n")
        code, out = run(tmp)
        assert code == 0 and "MANUAL-COPY" not in out, out
        open(os.path.join(tmp, ".github", "workflows", "ci.yml"), "w").write("name: CI\n# viejo\n")
        code, out = run(tmp)
        assert code == 0 and "difieren" in out and "cp ci.yml.MANUAL-COPY .github/workflows/ci.yml" in out, out

    print("test_lint_plugin: 18/18 OK")


if __name__ == "__main__":
    main()
