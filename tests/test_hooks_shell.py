#!/usr/bin/env python3
"""Suite de SHELL de los hooks (`hooks/*.sh`) y la statusline (debt-cleanup T-06).

Hasta hoy la evidencia de los hooks era la simulación manual de stdin anotada en los ledgers
(live-visibility, deterministic-guardrails). Aquí pytest lanza cada hook con `bash` sobre un
PROYECTO TEMPORAL (ledger de fixture copiado de docs/roadmap/ del repo, puesto en `en-progreso`) con
un entorno controlado (CLAUDE_PLUGIN_ROOT, CLAUDE_PROJECT_DIR, HOME, PATH) y afirma:
  - el JSON de salida sigue el contrato oficial (`systemMessage` / `hookSpecificOutput`);
  - el debounce de progress-line (2.ª idéntica → vacío) y su ATOMICIDAD con 6 invocaciones
    concurrentes (T-01a): con `flock` exactamente UNA systemMessage; sin `flock` la aserción
    honesta es «≥ 1 y nunca ninguna» (el rename es atómico; dos lectores pueden ver el estado viejo);
  - la degradación sin `python3` (guardrail: aviso una vez, nunca bloqueo);
  - `exit 0` SIEMPRE, también con stdin vacío.
Se salta entera si no hay `bash`. Ejecutar: python3 -m pytest -q tests/test_hooks_shell.py
(el bucle de la CI también la ejecuta como script: `python tests/test_hooks_shell.py`).
"""
import json
import os
import shutil
import stat
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HOOKS = os.path.join(ROOT, "hooks")
STATUSLINE = os.path.join(ROOT, "statusline", "roadmap-statusline.sh")
LEDGER_FUENTE = os.path.join(ROOT, "docs", "roadmap", "2026-09-02-adversarial-review", "tasks.md")

try:
    import pytest
except ImportError:  # el bucle de la CI ejecuta el fichero como script; sin pytest solo informa
    pytest = None

BASH = shutil.which("bash")
if pytest is not None:
    pytestmark = pytest.mark.skipif(BASH is None, reason="sin bash en PATH: la suite de shell no aplica")


# ------------------------------------------------------------------ helpers ----

def proyecto(tmp_path, activa=True, slug="2026-01-01-demo"):
    """Proyecto temporal con un ledger de fixture (copia real del repo) en-progreso o completado."""
    proj = tmp_path / "proj"
    led = proj / "docs" / "roadmap" / slug / "tasks.md"
    led.parent.mkdir(parents=True)
    text = open(LEDGER_FUENTE, encoding="utf-8").read()
    if activa:
        # frontmatter + tabla de cabecera a en-progreso y una tarea abierta → iniciativa ACTIVA
        text = text.replace("estado: completado", "estado: en-progreso", 1)
        text = text.replace("| **Estado** | completado |", "| **Estado** | en-progreso |", 1)
        text = text.replace("- **Estado**: completado\n- **Tiempo humano**: est. 0,9h", "- **Estado**: en-progreso\n- **Tiempo humano**: est. 0,9h", 1)
    led.write_text(text, encoding="utf-8")
    (proj / ".claude").mkdir()
    return proj, led


def env_de(proj, tmp_path, sin_python=False, plugin_root=ROOT):
    """Entorno mínimo y controlado. `sin_python` → PATH con solo bash/coreutils (sin python3)."""
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    path = os.environ.get("PATH", "/usr/bin:/bin")
    if sin_python:
        bindir = tmp_path / "bin"
        bindir.mkdir(exist_ok=True)
        for tool in ("bash", "cat", "mkdir", "printf", "find", "head", "grep", "sed", "rm", "mv", "mktemp", "flock", "dirname"):
            src = shutil.which(tool)
            if src:
                dst = bindir / tool
                if not dst.exists():
                    os.symlink(src, dst)
        path = str(bindir)
    return {"CLAUDE_PLUGIN_ROOT": str(plugin_root), "CLAUDE_PROJECT_DIR": str(proj),
            "HOME": str(home), "PATH": path, "LC_ALL": "C.UTF-8", "LANG": "C.UTF-8"}


def hook(nombre, payload, env, cwd=None):
    """Lanza hooks/<nombre> con el payload por stdin. Devuelve (rc, stdout, stderr)."""
    script = STATUSLINE if nombre == "statusline" else os.path.join(HOOKS, nombre)
    data = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
    r = subprocess.run([BASH, script], input=data, capture_output=True, text=True, env=env,
                       cwd=cwd or env["CLAUDE_PROJECT_DIR"], timeout=60)
    return r.returncode, r.stdout, r.stderr


def post_tool(path):
    return {"tool_name": "Edit", "tool_input": {"file_path": path, "old_string": "a", "new_string": "b"},
            "tool_response": {"filePath": path}}


def un_json(stdout):
    lineas = [l for l in stdout.splitlines() if l.strip()]
    assert len(lineas) == 1, f"esperaba UN objeto JSON en stdout, hubo {len(lineas)}: {stdout!r}"
    return json.loads(lineas[0])


# --------------------------------------------------------------- progress-line ----

def test_progress_line_emite_system_message_json(tmp_path):
    proj, led = proyecto(tmp_path)
    rc, out, _ = hook("progress-line.sh", post_tool(str(led)), env_de(proj, tmp_path))
    assert rc == 0
    msg = un_json(out)["systemMessage"]
    assert msg.startswith("📋 demo") and "T-03/4" in msg and "IA est." in msg, msg
    assert (proj / ".claude" / ".progress-last").read_text(encoding="utf-8") == msg


def test_progress_line_debounce_segunda_identica_vacia(tmp_path):
    proj, led = proyecto(tmp_path)
    env = env_de(proj, tmp_path)
    rc1, out1, _ = hook("progress-line.sh", post_tool(str(led)), env)
    rc2, out2, _ = hook("progress-line.sh", post_tool(str(led)), env)
    assert rc1 == 0 and rc2 == 0
    assert out1.strip() and out2 == "", (out1, out2)
    # cambia el estado del ledger → vuelve a emitir
    led.write_text(led.read_text(encoding="utf-8").replace("- **Estado**: en-progreso", "- **Estado**: completado", 1), encoding="utf-8")
    rc3, out3, _ = hook("progress-line.sh", post_tool(str(led)), env)
    assert rc3 == 0 and out3.strip() and out3 != out1


def test_progress_line_ruta_windows_con_backslashes(tmp_path):
    proj, led = proyecto(tmp_path)
    win = str(led).replace("/", "\\")
    rc, out, _ = hook("progress-line.sh", post_tool(win), env_de(proj, tmp_path))
    assert rc == 0 and "systemMessage" in un_json(out)


def test_progress_line_multiedit_edits_lista(tmp_path):
    proj, led = proyecto(tmp_path)
    payload = {"tool_name": "MultiEdit", "tool_input": {"file_path": str(proj / "src" / "a.py"),
                                                        "edits": [{"file_path": str(led), "old_string": "a", "new_string": "b"}]}}
    rc, out, _ = hook("progress-line.sh", payload, env_de(proj, tmp_path))
    assert rc == 0 and "systemMessage" in un_json(out)


def test_progress_line_stdin_vacio_y_fichero_ajeno_exit_0_vacio(tmp_path):
    proj, _ = proyecto(tmp_path)
    env = env_de(proj, tmp_path)
    assert hook("progress-line.sh", "", env) == (0, "", "")
    rc, out, _ = hook("progress-line.sh", post_tool(str(proj / "src" / "app.py")), env)
    assert (rc, out) == (0, "")


def test_progress_line_seis_concurrentes_debounce_atomico(tmp_path):
    """T-01a. Con `flock`: exactamente UNA systemMessage (sección crítica serializada). Sin `flock`
    (macOS sin coreutils): el rename sigue siendo atómico pero dos lectores pueden ver el estado
    viejo a la vez → aserción honesta: al menos una, nunca cero, y el fichero de estado íntegro."""
    proj, led = proyecto(tmp_path)
    env = env_de(proj, tmp_path)
    payload = post_tool(str(led))
    with ThreadPoolExecutor(max_workers=6) as ex:
        res = list(ex.map(lambda _: hook("progress-line.sh", payload, env), range(6)))
    assert all(rc == 0 for rc, _, _ in res)
    emitidas = [un_json(out)["systemMessage"] for _, out, _ in res if out.strip()]
    if shutil.which("flock"):
        assert len(emitidas) == 1, f"con flock debe emitirse exactamente 1, fueron {len(emitidas)}"
    else:
        assert 1 <= len(emitidas) <= 6 and len(set(emitidas)) == 1
    assert (proj / ".claude" / ".progress-last").read_text(encoding="utf-8") == emitidas[0]
    # sin temporales huérfanos del rename
    assert not [f for f in os.listdir(proj / ".claude") if f.startswith(".progress-last.") and f != ".progress-last.lock"]


def test_progress_line_sin_flock_degrada_a_rename_atomico(tmp_path):
    """Sin `flock` en PATH el hook sigue funcionando (1.ª emite, 2.ª idéntica calla) y no crea el lock."""
    proj, led = proyecto(tmp_path)
    env = env_de(proj, tmp_path, sin_python=True)
    os.unlink(tmp_path / "bin" / "flock") if (tmp_path / "bin" / "flock").exists() else None
    os.symlink(sys.executable, tmp_path / "bin" / "python3")   # con python3 pero sin flock
    rc1, out1, _ = hook("progress-line.sh", post_tool(str(led)), env)
    rc2, out2, _ = hook("progress-line.sh", post_tool(str(led)), env)
    assert rc1 == 0 and "systemMessage" in un_json(out1)
    assert (rc2, out2) == (0, "")
    assert not (proj / ".claude" / ".progress-last.lock").exists()


# ----------------------------------------------------------- subagent-progress ----

def test_subagent_progress_con_activa_emite_system_message(tmp_path):
    proj, _ = proyecto(tmp_path)
    rc, out, _ = hook("subagent-progress.sh", {"hook_event_name": "SubagentStop", "agent_type": "implementer"}, env_de(proj, tmp_path))
    assert rc == 0
    assert "demo" in un_json(out)["systemMessage"]


def test_subagent_progress_sin_activas_vacio(tmp_path):
    proj, _ = proyecto(tmp_path, activa=False)
    assert hook("subagent-progress.sh", {"hook_event_name": "SubagentStop"}, env_de(proj, tmp_path)) == (0, "", "")


# ------------------------------------------------------------- session-context ----

def test_session_context_con_activa_additional_context_anidado(tmp_path):
    proj, _ = proyecto(tmp_path)
    rc, out, _ = hook("session-context.sh", {"hook_event_name": "SessionStart", "source": "resume"}, env_de(proj, tmp_path))
    assert rc == 0
    d = un_json(out)
    assert set(d) == {"hookSpecificOutput"}                     # additionalContext SOLO anidado
    hso = d["hookSpecificOutput"]
    assert hso["hookEventName"] == "SessionStart" and "demo" in hso["additionalContext"]


def test_session_context_sin_activas_vacio(tmp_path):
    proj, _ = proyecto(tmp_path, activa=False)
    assert hook("session-context.sh", {"hook_event_name": "SessionStart", "source": "startup"}, env_de(proj, tmp_path)) == (0, "", "")


# -------------------------------------------------------- implementer-guardrail ----

def test_guardrail_deny_spec_md_contrato_oficial(tmp_path):
    proj, _ = proyecto(tmp_path)
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(proj / "docs" / "roadmap" / "2026-01-01-demo" / "spec.md"), "content": "x"}}
    rc, out, _ = hook("implementer-guardrail.sh", payload, env_de(proj, tmp_path))
    assert rc == 0
    hso = un_json(out)["hookSpecificOutput"]
    assert hso["hookEventName"] == "PreToolUse" and hso["permissionDecision"] == "deny"
    assert "tasks.md" in hso["permissionDecisionReason"]


def test_guardrail_allow_tasks_md_sin_stdout(tmp_path):
    proj, led = proyecto(tmp_path)
    payload = {"tool_name": "Edit", "tool_input": {"file_path": str(led), "old_string": "a", "new_string": "b"}}
    assert hook("implementer-guardrail.sh", payload, env_de(proj, tmp_path)) == (0, "", "")


def test_guardrail_deny_git_push_force(tmp_path):
    proj, _ = proyecto(tmp_path)
    payload = {"tool_name": "Bash", "tool_input": {"command": "git push --force origin feature/x"}}
    rc, out, _ = hook("implementer-guardrail.sh", payload, env_de(proj, tmp_path))
    assert rc == 0
    hso = un_json(out)["hookSpecificOutput"]
    assert hso["permissionDecision"] == "deny" and "forzado" in hso["permissionDecisionReason"]


def test_guardrail_sin_python3_avisa_una_vez_y_no_bloquea(tmp_path):
    proj, _ = proyecto(tmp_path)
    env = env_de(proj, tmp_path, sin_python=True)
    payload = {"tool_name": "Write", "tool_input": {"file_path": str(proj / "docs" / "roadmap" / "x" / "spec.md")}}
    rc1, out1, _ = hook("implementer-guardrail.sh", payload, env)
    assert rc1 == 0
    d = un_json(out1)
    assert set(d) == {"systemMessage"} and "python3" in d["systemMessage"]   # aviso, NO deny
    assert (proj / ".claude" / ".guardrail-nopython").exists()
    assert hook("implementer-guardrail.sh", payload, env) == (0, "", "")        # 2.ª vez: silencio


# -------------------------------------------- mark-docs-pending · ledger-lint-warn ----

def test_mark_docs_pending_marca_con_docs_y_no_con_security_scan(tmp_path):
    proj, led = proyecto(tmp_path)
    env = env_de(proj, tmp_path)
    assert hook("mark-docs-pending.sh", post_tool(str(proj / "docs" / "security-scan" / "STATE.md")), env) == (0, "", "")
    assert not (proj / ".claude" / ".confluence-pending").exists()
    assert hook("mark-docs-pending.sh", post_tool(str(led)), env) == (0, "", "")
    assert (proj / ".claude" / ".confluence-pending").exists()


def test_ledger_lint_warn_exit_0_con_ledger_coherente_e_incoherente(tmp_path):
    proj, led = proyecto(tmp_path)
    env = env_de(proj, tmp_path)
    rc, out, _ = hook("ledger-lint-warn.sh", post_tool(str(led)), env)
    assert rc == 0 and "Traceback" not in out
    # ledger roto (tarea completada con criterio sin marcar) → sigue exit 0, informa por stdout
    led.write_text(led.read_text(encoding="utf-8").replace("- [x] `skills/adversarial-review/SKILL.md` con frontmatter", "- [ ] `skills/adversarial-review/SKILL.md` con frontmatter", 1), encoding="utf-8")
    rc, out, _ = hook("ledger-lint-warn.sh", post_tool(str(led)), env)
    assert rc == 0 and "T-01" in out, out


# ------------------------------------------------------------------ statusline ----

def test_statusline_json_oficial_una_linea_con_modelo_coste_y_roadmap(tmp_path):
    proj, _ = proyecto(tmp_path)
    payload = {"model": {"display_name": "Opus"}, "cost": {"total_cost_usd": 0.01234}, "context_window": {"used_percentage": 8}}
    rc, out, _ = hook("statusline", payload, env_de(proj, tmp_path))
    assert rc == 0
    lineas = out.splitlines()
    assert len(lineas) == 1 and lineas[0].startswith("[Opus] $0.01 ctx 8%"), out
    assert "📋 demo T-03/4" in lineas[0], out


def test_statusline_stdin_vacio_exit_0(tmp_path):
    proj, _ = proyecto(tmp_path, activa=False)
    rc, out, _ = hook("statusline", "", env_de(proj, tmp_path))
    assert rc == 0 and out.strip() == ""


def test_todos_los_hooks_son_bash_valido_y_ejecutables():
    for fn in sorted(os.listdir(HOOKS)):
        p = os.path.join(HOOKS, fn)
        if fn.endswith(".sh"):
            assert subprocess.run([BASH, "-n", p], capture_output=True).returncode == 0, fn
            assert os.stat(p).st_mode & stat.S_IXUSR, f"{fn} sin bit ejecutable"
        elif fn.endswith(".json"):
            assert not os.stat(p).st_mode & stat.S_IXUSR, f"{fn} no debería ser ejecutable (T-01c)"


def main():
    if pytest is None:
        print("test_hooks_shell: pytest no instalado — suite omitida (pip install pytest)")
        return 0
    if BASH is None:
        print("test_hooks_shell: sin bash — suite omitida")
        return 0
    return pytest.main(["-q", __file__])


if __name__ == "__main__":
    sys.exit(main())
