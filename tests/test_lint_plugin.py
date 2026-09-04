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
effort: medium
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
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
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

    # 3b) falta el campo effort → error (parity-core T-01)
    with tempfile.TemporaryDirectory() as tmp:
        body = AGENT_OK.format(name="alpha").replace("effort: medium\n", "")
        make_plugin(tmp, {"alpha": body})
        code, out = run(tmp)
        assert code == 1 and "requerido `effort`" in out, out

    # 3c) effort inválido → error (valores oficiales low|medium|high|xhigh|max)
    with tempfile.TemporaryDirectory() as tmp:
        body = AGENT_OK.format(name="alpha").replace("effort: medium", "effort: ultra")
        make_plugin(tmp, {"alpha": body})
        code, out = run(tmp)
        assert code == 1 and "`effort: ultra` no es válido" in out, out
    with tempfile.TemporaryDirectory() as tmp:
        body = AGENT_OK.format(name="alpha").replace("effort: medium", "effort: xhigh")
        make_plugin(tmp, {"alpha": body})
        code, out = run(tmp)
        assert code == 0, out

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
effort: medium
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

    # 19) [activation-reliability T-04] cobertura en evals/cases/: pieza sin caso positivo → AVISO (no error);
    #     con positivo → sin aviso; sin carpeta evals/cases/ → sin aviso (plugin consumidor)
    import shutil
    with tempfile.TemporaryDirectory() as tmp:
        make_plugin(tmp, {"alpha": AGENT_OK.format(name="alpha")})
        code, out = run(tmp)
        assert code == 0 and "sin caso positivo" not in out, f"sin evals/cases no se avisa\n{out}"
        os.makedirs(os.path.join(tmp, "evals", "cases"))
        shutil.copy(os.path.join(ROOT, "evals", "check.py"), os.path.join(tmp, "evals", "check.py"))
        # solo el agente tiene caso positivo; la skill `my-skill` no tiene fichero
        open(os.path.join(tmp, "evals", "cases", "agent-alpha.json"), "w", encoding="utf-8").write(json.dumps({
            "target": "agent:alpha", "cases": [{"id": "alpha-literal", "prompt": "haz X por favor", "trigger": "literal",
                                                "expect": {"activates": True}}]}))
        # fichero con SOLO negativos → también cuenta como sin positivo
        open(os.path.join(tmp, "evals", "cases", "skill-my-skill.json"), "w", encoding="utf-8").write(json.dumps({
            "target": "skill:my-skill", "cases": [{"id": "my-skill-neg", "prompt": "otra cosa", "expect": {"activates": False}}]}))
        code, out = run(tmp)
        assert code == 0, out
        assert "skill:my-skill: sin caso positivo en evals/cases/skill-my-skill.json" in out, out
        assert "agent:alpha: sin caso positivo" not in out, out
        # añadido el positivo → desaparece el aviso
        open(os.path.join(tmp, "evals", "cases", "skill-my-skill.json"), "w", encoding="utf-8").write(json.dumps({
            "target": "skill:my-skill", "cases": [{"id": "my-skill-pos", "prompt": "usa my-skill", "trigger": "parafrasis",
                                                   "expect": {"activates": True}}]}))
        code, out = run(tmp)
        assert code == 0 and "sin caso positivo" not in out, out

    # 20) [activation-reliability T-04] description > 1.200 caracteres → AVISO token-diet (agente, y skill con
    #     bloque plegado `>` leído por el lector local cuando no hay evals/check.py); ≤ 1.200 → sin aviso
    with tempfile.TemporaryDirectory() as tmp:
        larga = ("Hace algo útil. " * 82).strip()          # ≈1.300 caracteres, con gatillo al final
        larga += ' Úsalo cuando el usuario diga "haz X".'
        assert len(larga) > 1200
        body = AGENT_OK.format(name="alpha").replace(
            'description: Hace algo útil. Úsalo cuando el usuario diga "haz X".', f"description: {larga}")
        make_plugin(tmp, {"alpha": body})
        open(os.path.join(tmp, "skills", "my-skill", "SKILL.md"), "w", encoding="utf-8").write(
            "---\nname: my-skill\ndescription: >\n  " + ("palabra " * 200).strip() + "\n---\n# skill\n")
        code, out = run(tmp)
        assert code == 0, out
        assert f"agent:alpha: description de {len(larga)} caracteres (> 1200)" in out, out
        assert "skill:my-skill: description de 1599 caracteres (> 1200)" in out, out
        # corta → sin aviso
        make_plugin(tmp + "/b", {"alpha": AGENT_OK.format(name="alpha")})
        code, out = run(tmp + "/b")
        assert code == 0 and "caracteres (>" not in out, out

    # 21) [plan-and-diet T-01] SKILL.md > 200 líneas → AVISO token-diet (skills cortas + references/);
    #     de 150 líneas → sin aviso. El umbral duro (250) lo impone tests/test_skill_size.py, no el linter.
    with tempfile.TemporaryDirectory() as tmp:
        make_plugin(tmp, {"alpha": AGENT_OK.format(name="alpha")})
        open(os.path.join(tmp, "skills", "my-skill", "SKILL.md"), "w", encoding="utf-8").write(
            "---\nname: my-skill\ndescription: Corta. Úsala cuando el usuario diga \"x\".\n---\n" + "línea\n" * 197)
        code, out = run(tmp)
        assert code == 0, out
        assert "skill `my-skill`: SKILL.md de 201 líneas (> 200)" in out, out
        assert "references/<tema>.md" in out, out
        open(os.path.join(tmp, "skills", "my-skill", "SKILL.md"), "w", encoding="utf-8").write(
            "---\nname: my-skill\ndescription: Corta. Úsala cuando el usuario diga \"x\".\n---\n" + "línea\n" * 146)
        code, out = run(tmp)
        assert code == 0 and "SKILL.md de" not in out, out

    # 22) [plan-and-diet T-03] el aviso de copia manual está generalizado a TODO `*.yml.MANUAL-COPY`:
    #     headless.yml.MANUAL-COPY ≠ .github/workflows/headless.yml → aviso con el `cp` exacto; idénticos → nada
    with tempfile.TemporaryDirectory() as tmp:
        make_plugin(tmp, {"alpha": AGENT_OK.format(name="alpha")})
        os.makedirs(os.path.join(tmp, ".github", "workflows"))
        open(os.path.join(tmp, "headless.yml.MANUAL-COPY"), "w").write("name: Headless\n")
        open(os.path.join(tmp, ".github", "workflows", "headless.yml"), "w").write("name: Headless\n# atrasada\n")
        code, out = run(tmp)
        assert code == 0, out
        assert "cp headless.yml.MANUAL-COPY .github/workflows/headless.yml" in out, out
        open(os.path.join(tmp, ".github", "workflows", "headless.yml"), "w").write("name: Headless\n")
        code, out = run(tmp)
        assert code == 0 and "difieren" not in out, out

    # 23) [roles-and-jira-flow T-01] disparador literal entrecomillado duplicado entre DOS piezas
    #     distintas → AVISO (heurístico ADR-011, no error, no bloquea); frases distintas → sin aviso
    with tempfile.TemporaryDirectory() as tmp:
        body = AGENT_OK.format(name="alpha").replace(
            'description: Hace algo útil. Úsalo cuando el usuario diga "haz X".',
            'description: Hace algo útil. Úsalo cuando el usuario diga "haz algo especial".')
        make_plugin(tmp, {"alpha": body})
        open(os.path.join(tmp, "skills", "my-skill", "SKILL.md"), "w", encoding="utf-8").write(
            '---\nname: my-skill\ndescription: Otra cosa. Úsala cuando el usuario diga "haz algo especial".\n---\n# skill\n')
        code, out = run(tmp)
        assert code == 0, f"es aviso, no error\n{out}"
        assert 'disparador duplicado "haz algo especial" en agent:alpha, skill:my-skill' in out, out
        # frase distinta entre las dos piezas → sin aviso
        open(os.path.join(tmp, "skills", "my-skill", "SKILL.md"), "w", encoding="utf-8").write(
            '---\nname: my-skill\ndescription: Otra cosa. Úsala cuando el usuario diga "haz otra cosa".\n---\n# skill\n')
        code, out = run(tmp)
        assert code == 0 and "disparador duplicado" not in out, out

    # 24) [roles-and-jira-flow T-fix1] el aviso de disparador duplicado, afinado:
    #     (a) plega ACENTOS y mayúsculas («revisión de código» ≡ «Revision de codigo»);
    #     (b) solo mira las frases de ≥3 palabras que siguen a «Úsalo/Úsala cuando…»
    #         → una cita corta, o una cita fuera de esa cola, ya NO avisan (era ruido).
    with tempfile.TemporaryDirectory() as tmp:
        body = AGENT_OK.format(name="alpha").replace(
            'description: Hace algo útil. Úsalo cuando el usuario diga "haz X".',
            'description: Hace algo útil. Úsalo cuando el usuario diga "revisión de código".')
        make_plugin(tmp, {"alpha": body})
        open(os.path.join(tmp, "skills", "my-skill", "SKILL.md"), "w", encoding="utf-8").write(
            '---\nname: my-skill\ndescription: Otra cosa. Úsala cuando el usuario diga '
            '"Revision de codigo".\n---\n# skill\n')
        code, out = run(tmp)
        assert code == 0, f"es aviso, no error\n{out}"
        assert 'disparador duplicado "revision de codigo" en agent:alpha, skill:my-skill' in out, out
        assert "sin acentos" in out, out

    with tempfile.TemporaryDirectory() as tmp:
        # cita CORTA (2 palabras) repetida en las dos piezas → sin aviso
        body = AGENT_OK.format(name="alpha").replace(
            'description: Hace algo útil. Úsalo cuando el usuario diga "haz X".',
            'description: Lee el "ledger canónico". Úsalo cuando el usuario diga "ledger canónico".')
        make_plugin(tmp, {"alpha": body})
        open(os.path.join(tmp, "skills", "my-skill", "SKILL.md"), "w", encoding="utf-8").write(
            '---\nname: my-skill\ndescription: Otra cosa. Úsala cuando el usuario diga '
            '"ledger canónico".\n---\n# skill\n')
        code, out = run(tmp)
        assert code == 0 and "disparador duplicado" not in out, out

    with tempfile.TemporaryDirectory() as tmp:
        # frase larga compartida pero ANTES del marcador de disparadores → sin aviso
        body = AGENT_OK.format(name="alpha").replace(
            'description: Hace algo útil. Úsalo cuando el usuario diga "haz X".',
            'description: Escribe el "informe de revisión adversarial" del ciclo. '
            'Úsalo cuando el usuario diga "audita el diseño".')
        make_plugin(tmp, {"alpha": body})
        open(os.path.join(tmp, "skills", "my-skill", "SKILL.md"), "w", encoding="utf-8").write(
            '---\nname: my-skill\ndescription: Lee el "informe de revisión adversarial". '
            'Úsala cuando el usuario diga "pásalo a PDF".\n---\n# skill\n')
        code, out = run(tmp)
        assert code == 0 and "disparador duplicado" not in out, out

    # 25) `.py` con símbolos y SIN el snippet de consola → aviso (no error) [windows-console T-01]
    with tempfile.TemporaryDirectory() as tmp:
        make_plugin(tmp, {"alpha": AGENT_OK.format(name="alpha")})
        os.makedirs(os.path.join(tmp, "scripts"))
        with open(os.path.join(tmp, "scripts", "grita.py"), "w", encoding="utf-8") as f:
            f.write('import sys\nprint("✅ listo")\n')
        code, out = run(tmp)
        assert code == 0, f"es aviso, no error\n{out}"
        assert "grita.py" in out and "no reconfigura los streams AL ARRANCAR" in out, out
        assert "UnicodeEncodeError" in out and "GOT-005" in out, out

    # 26) el mismo fichero CON el snippet → sin aviso; y un `.py` solo-ASCII tampoco avisa
    with tempfile.TemporaryDirectory() as tmp:
        make_plugin(tmp, {"alpha": AGENT_OK.format(name="alpha")})
        os.makedirs(os.path.join(tmp, "scripts"))
        with open(os.path.join(tmp, "scripts", "grita.py"), "w", encoding="utf-8") as f:
            f.write('import sys\nfor _s in (sys.stdin, sys.stdout, sys.stderr):\n'
                    '    try: _s.reconfigure(encoding="utf-8", errors="replace")\n'
                    '    except Exception: pass\nprint("✅ listo")\n')
        with open(os.path.join(tmp, "scripts", "mudo.py"), "w", encoding="utf-8") as f:
            f.write('print("plain ascii")\n')
        # las suites (`test_*.py`) y los fixtures del consumidor quedan fuera del criterio
        with open(os.path.join(tmp, "scripts", "test_grita.py"), "w", encoding="utf-8") as f:
            f.write('print("✅ suite")\n')
        os.makedirs(os.path.join(tmp, "evals", "fixtures", "project"))
        with open(os.path.join(tmp, "evals", "fixtures", "project", "app.py"), "w", encoding="utf-8") as f:
            f.write('print("✅ código del consumidor simulado")\n')
        code, out = run(tmp)
        assert code == 0 and "no reconfigura los streams" not in out, out

    # 27) la marca DENTRO de `main()`, con un print de símbolos a nivel de módulo antes → aviso.
    #     Antes se buscaba por subcadena (`CONSOLE_MARK in data`) y daba 0 avisos mientras el script
    #     reventaba igual bajo cp1252 [windows-console T-04].
    with tempfile.TemporaryDirectory() as tmp:
        make_plugin(tmp, {"alpha": AGENT_OK.format(name="alpha")})
        os.makedirs(os.path.join(tmp, "scripts"))
        with open(os.path.join(tmp, "scripts", "tarde.py"), "w", encoding="utf-8") as f:
            f.write('import sys\nprint("⚠️  a nivel de módulo")\n\n\ndef main():\n'
                    '    for _s in (sys.stdin, sys.stdout, sys.stderr):\n'
                    '        try: _s.reconfigure(encoding="utf-8", errors="replace")\n'
                    '        except Exception: pass\n')
        code, out = run(tmp)
        assert code == 0, f"es aviso, no error\n{out}"
        assert "tarde.py" in out and "AL ARRANCAR" in out, out

    # 28) la marca SOLO citada en un docstring → aviso (no es una llamada, no protege nada) [T-04]
    with tempfile.TemporaryDirectory() as tmp:
        make_plugin(tmp, {"alpha": AGENT_OK.format(name="alpha")})
        os.makedirs(os.path.join(tmp, "scripts"))
        with open(os.path.join(tmp, "scripts", "cita.py"), "w", encoding="utf-8") as f:
            f.write('"""Debería llamar a reconfigure(encoding="utf-8", errors="replace").\n"""\n'
                    'print("⚠️  sin snippet de verdad")\n')
        code, out = run(tmp)
        assert code == 0 and "cita.py" in out and "AL ARRANCAR" in out, out

    # 29) lado PADRE: capturar un subproceso en modo texto sin `encoding=` → aviso; con él, no [T-04]
    with tempfile.TemporaryDirectory() as tmp:
        make_plugin(tmp, {"alpha": AGENT_OK.format(name="alpha")})
        os.makedirs(os.path.join(tmp, "scripts"))
        with open(os.path.join(tmp, "scripts", "padre.py"), "w", encoding="utf-8") as f:
            f.write('import subprocess\nr = subprocess.run(["git", "log"], capture_output=True, text=True)\n')
        code, out = run(tmp)
        assert code == 0, f"es aviso, no error\n{out}"
        assert "padre.py" in out and "modo texto SIN `encoding=`" in out and "línea 2" in out, out

        # el mismo fichero CON encoding, y uno que solo mira el returncode (bytes: no decodifica)
        with open(os.path.join(tmp, "scripts", "padre.py"), "w", encoding="utf-8") as f:
            f.write('import subprocess\nr = subprocess.run(["git", "log"], capture_output=True, '
                    'text=True, encoding="utf-8", errors="replace")\n'
                    'ok = subprocess.run(["git", "status"], capture_output=True).returncode == 0\n')
        code, out = run(tmp)
        assert code == 0 and "modo texto SIN" not in out, out

    # 30) lector de `stdin` ASCII PURO → aviso, aunque su fuente no tenga un solo símbolo. El lado
    #     que LEE no depende del fuente sino del payload: era el caso de `pick_asset.py`, la 28.ª
    #     pieza del repo, invisible para el criterio de T-04 [windows-console T-05].
    with tempfile.TemporaryDirectory() as tmp:
        make_plugin(tmp, {"alpha": AGENT_OK.format(name="alpha")})
        os.makedirs(os.path.join(tmp, "scripts"))
        with open(os.path.join(tmp, "scripts", "lector.py"), "w", encoding="utf-8") as f:
            f.write('import json, sys\nprint(json.load(sys.stdin)["url"])\n')
        code, out = run(tmp)
        assert code == 0, f"es aviso, no error\n{out}"
        assert "lector.py" in out and "lee de `sys.stdin`" in out, out
        assert "imprime caracteres no ASCII" not in out, (
            f"el motivo del aviso debe ser SOLO la lectura de stdin\n{out}")

        # el mismo lector CON el snippet → sin aviso
        with open(os.path.join(tmp, "scripts", "lector.py"), "w", encoding="utf-8") as f:
            f.write('import json, sys\nfor _s in (sys.stdin, sys.stdout, sys.stderr):\n'
                    '    try: _s.reconfigure(encoding="utf-8", errors="replace")\n'
                    '    except Exception: pass\nprint(json.load(sys.stdin)["url"])\n')
        code, out = run(tmp)
        assert code == 0 and "no reconfigura los streams" not in out, out

    # 31) `sys.stdin` citado en un comentario o dentro de una cadena NO cuenta como lectura: el
    #     criterio es `ast`, no `grep`, y un fichero ASCII sin lectura real queda fuera [T-05].
    with tempfile.TemporaryDirectory() as tmp:
        make_plugin(tmp, {"alpha": AGENT_OK.format(name="alpha")})
        os.makedirs(os.path.join(tmp, "scripts"))
        with open(os.path.join(tmp, "scripts", "menciona.py"), "w", encoding="utf-8") as f:
            f.write('# algun dia leera de sys.stdin\nprint("usa sys.stdin")\n')
        code, out = run(tmp)
        assert code == 0 and "no reconfigura los streams" not in out, out

    # 32) los dos motivos a la vez → el aviso los NOMBRA a los dos (el mensaje no miente) [T-05]
    with tempfile.TemporaryDirectory() as tmp:
        make_plugin(tmp, {"alpha": AGENT_OK.format(name="alpha")})
        os.makedirs(os.path.join(tmp, "scripts"))
        with open(os.path.join(tmp, "scripts", "ambos.py"), "w", encoding="utf-8") as f:
            f.write('import sys\nprint("⚠️ ", sys.stdin.read())\n')
        code, out = run(tmp)
        assert code == 0, f"es aviso, no error\n{out}"
        assert "imprime caracteres no ASCII y lee de `sys.stdin`" in out, out

    print("test_lint_plugin: 32/32 OK")


if __name__ == "__main__":
    main()
