#!/usr/bin/env python3
"""Tests de guardrail-check.py (hook PreToolUse del implementer). Ejecuta: pytest -q."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(HERE, "guardrail-check.py")

spec = importlib.util.spec_from_file_location("guardrail_check", SCRIPT)
gc = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gc)

PROJ = "/proy"


def write(path, tool="Write"):
    return {"tool_name": tool, "tool_input": {"file_path": path, "content": "x"}}


def bash(cmd):
    return {"tool_name": "Bash", "tool_input": {"command": cmd}}


def decide(payload, branch="feature/x", cfg=None):
    return gc.decide(payload, PROJ, cfg, branch=branch)


# ------------------------------------------------------------- alcance ----
def test_alcance_deny_plan_en_roadmap():
    r = decide(write("docs/roadmap/2026-01-01-x/improvement-plan.md"))
    assert r and "solo toca tasks.md" in r


def test_alcance_allow_tasks_md():
    assert decide(write("docs/roadmap/2026-01-01-x/tasks.md", "Edit")) is None


def test_alcance_deny_testing_es_de_qa():
    r = decide(write("docs/roadmap/2026-01-01-x/testing/tasks.md"))
    assert r and "qa" in r


def test_alcance_deny_security_scan():
    r = decide(write("docs/security-scan/STATE.md", "MultiEdit"))
    assert r and "security-scan" in r


def test_alcance_allow_knowledge():
    assert decide(write("docs/knowledge/adr/ADR-009-x.md")) is None


def test_alcance_ruta_absoluta_relativa_al_proyecto():
    r = decide(write(PROJ + "/docs/roadmap/2026-01-01-x/spec.md"))
    assert r and "docs/roadmap/2026-01-01-x/spec.md" in r


def test_alcance_ruta_windows():
    r = decide(write(r"C:\proy\docs\roadmap\2026-01-01-x\evaluation.md"))
    assert r and "solo toca tasks.md" in r
    assert decide(write(r"C:\proy\docs\roadmap\2026-01-01-x\tasks.md")) is None


def test_alcance_multiedit_edits_y_notebook():
    p = {"tool_name": "MultiEdit", "tool_input": {"edits": [{"file_path": "src/a.py"},
                                                            {"file_path": "docs/roadmap/x/spec.md"}]}}
    assert decide(p)
    nb = {"tool_name": "NotebookEdit", "tool_input": {"notebook_path": "docs/roadmap/x/nb.ipynb"}}
    assert decide(nb)


def test_alcance_allow_codigo_normal():
    assert decide(write("src/app.py")) is None
    assert decide(write("docs/README.md")) is None


def test_cleanup_alcance_case_insensitive():
    """Deuda de deterministic-guardrails saldada en debt-cleanup T-02a: mayúsculas en la ruta."""
    r = decide(write("Docs/Roadmap/2026-01-01-x/Spec.md"))
    assert r and "solo toca tasks.md" in r
    assert decide(write("DOCS/ROADMAP/2026-01-01-x/TASKS.md", "Edit")) is None
    r = decide(write("Docs/Security-Scan/STATE.md"))
    assert r and "security-scan" in r
    r = decide(write("docs/roadmap/x/Testing/tasks.md"))
    assert r and "qa" in r


def test_cleanup_raiz_roadmap_readme_permitido_resto_deny():
    """T-02b: docs/roadmap/README.md (índice) permitido; CALIBRATION/DRIFT/BACKLOG deny por diseño
    (los escriben /retro, /spec-drift, /pm-backlog — comandos, no el implementer)."""
    assert decide(write("docs/roadmap/README.md", "Edit")) is None
    assert decide(write("/proy/docs/roadmap/readme.md", "Edit")) is None
    for f in ("CALIBRATION.md", "DRIFT.md", "BACKLOG.md"):
        r = decide(write(f"docs/roadmap/{f}"))
        assert r and "raíz de docs/roadmap/" in r and "/retro" in r, (f, r)
    # el README de una INICIATIVA no es el índice → deny como cualquier otro fichero de la carpeta
    r = decide(write("docs/roadmap/2026-01-01-x/README.md"))
    assert r and "solo toca tasks.md" in r
    # en rama principal, el índice cuenta como ledger (no dispara ramaPrincipal)
    assert decide(write("docs/roadmap/README.md"), branch="main") is None


# ----------------------------------------------------------------- git ----
def test_git_deny_push_force_variantes():
    for cmd in ("git push --force", "git push -f origin main", "git push --force-with-lease",
                "git -C /r push -uf origin x", "npm test && git push --force"):
        assert decide(bash(cmd)), cmd


def test_git_allow_push_normal_y_otros():
    for cmd in ("git push", "git push -u origin feature/x", "git status", "git checkout -b feature/y",
                "grep -rf pat .", "rm -rf build/", "rm -rf ./dist node_modules"):
        assert decide(bash(cmd)) is None, cmd


def test_git_checkout_main_solo_desde_feature():
    assert decide(bash("git checkout main"), branch="feature/x")
    assert decide(bash("git switch master"), branch="feature/x")
    assert decide(bash("git checkout main"), branch="main") is None
    assert decide(bash("git checkout main"), branch=None) is None       # sin git → no aplica
    assert decide(bash("git checkout -b main-fix"), branch="feature/x") is None
    assert decide(bash("git checkout main -- src/a.py"), branch="feature/x") is None  # restaura fichero, no cambia de rama


def test_git_deny_branch_D_y_rm_rf_peligroso():
    assert decide(bash("git branch -D feature/x"))
    assert decide(bash("git branch --delete --force old"))
    assert decide(bash("git branch -d feature/x")) is None
    for cmd in ("rm -rf /", "rm -rf ~", "rm -rf .git", "rm -fr $HOME", "rm -rf /tmp/x/.git"):
        assert decide(bash(cmd)), cmd


def test_fix1_evasiones_git_refspec_mas_shell_c_y_rm_punto():
    # (2a) refspec con `+` = force
    assert decide(bash("git push origin +main"))
    assert decide(bash("git push origin main")) is None
    assert decide(bash("echo '+ok' | git push")) is None            # `+` no es un refspec de push
    # (2b) cadenas entrecomilladas que son comandos: sh -c / bash -c / eval
    for cmd in ('sh -c "git push --force"', "bash -c 'git push -f origin x'",
                "eval 'rm -rf .git'", 'bash -c "cd /r && git branch -D x"'):
        assert decide(bash(cmd)), cmd
    assert decide(bash('sh -c "ls -la"')) is None
    # intento 2 (regresión): texto con git/rm dentro de un argumento NO es un comando
    assert decide(bash('git commit -m "rm -rf . x"')) is None
    assert decide(bash('git commit -m "git push --force no es un comando aquí"')) is None
    assert decide(bash('echo "git push --force"')) is None
    assert decide(bash("sh -c 'cd x && rm -rf .'"))
    assert decide(bash('bash -lc "git push -f"'))
    assert decide(bash('zsh -c "git branch -D x"'))
    # (2c) rm -rf . / ./ (desde la raíz destruye .git); ./dist sigue permitido
    assert decide(bash("rm -rf .")) and decide(bash("rm -rf ./")) and decide(bash("rm -rf *"))
    assert decide(bash("rm -rf ./dist")) is None and decide(bash("rm -rf .cache")) is None


def test_fix1_normpath_resuelve_dotdot_sin_falsos_positivos():
    # (3) `..` hacia fuera de docs/roadmap → NO es roadmap (antes: deny falso)
    assert decide(write("docs/roadmap/x/../../src/a.py")) is None
    assert gc.normalize_path("docs/roadmap/x/../../src/a.py", PROJ) == "docs/src/a.py"
    # `..` hacia dentro sigue en deny
    assert decide(write("src/../docs/roadmap/x/spec.md"))
    assert decide(write(PROJ + "/src/../docs/roadmap/x/spec.md"))
    assert decide(write("./docs/roadmap/x/tasks.md")) is None
    assert gc.normalize_path("", PROJ) == "" and gc.normalize_path(".", PROJ) == ""


# ------------------------------------------------------- rama principal ----
def test_rama_principal_deny_codigo_allow_ledger():
    r = decide(write("src/app.py"), branch="main")
    assert r and "feature/<slug>" in r
    assert decide(write("docs/roadmap/2026-01-01-x/tasks.md"), branch="master") is None
    assert decide(write("src/app.py"), branch="feature/x") is None
    assert decide(write("src/app.py"), branch=None) is None     # sin git → no aplica


def test_config_apaga_reglas_individuales():
    cfg = {"alcance": False, "git": True, "ramaPrincipal": False}
    assert decide(write("docs/roadmap/x/spec.md"), branch="main", cfg=cfg) is None
    assert decide(bash("git push --force"), cfg=cfg)


# --------------------------------------------------------------- config ----
def test_load_config_defaults_off_y_corrupto():
    with tempfile.TemporaryDirectory() as tmp:
        assert gc.load_config(tmp) == (gc.DEFAULTS, True)               # ausente
        os.makedirs(os.path.join(tmp, ".claude"))
        p = os.path.join(tmp, ".claude", "dev.json")
        open(p, "w").write("{ no json")
        assert gc.load_config(tmp) == (gc.DEFAULTS, True)               # corrupto
        open(p, "w").write(json.dumps({"tdd": True, "guardrails": False}))
        cfg, activo = gc.load_config(tmp)
        assert not activo and not any(cfg.values())
        open(p, "w").write(json.dumps({"guardrails": {"git": False}}))
        cfg, activo = gc.load_config(tmp)
        assert activo and cfg == {"alcance": True, "git": False, "ramaPrincipal": True}


# ------------------------------------------------------------------ CLI ----
def run_cli(payload, cwd, env_extra=None):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=cwd)
    env.update(env_extra or {})
    r = subprocess.run([sys.executable, SCRIPT, "pre-tool"], input=payload, cwd=cwd,
                       capture_output=True, text=True, env=env)
    return r.returncode, r.stdout, r.stderr


def _git(cwd, *args):
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True,
                   env=dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                            GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t"))


def test_cli_json_invalido_y_vacio_permiten():
    with tempfile.TemporaryDirectory() as tmp:
        code, out, err = run_cli("{ esto no es json", tmp)
        assert code == 0 and out == "" and "se permite" in err
        code, out, _ = run_cli("", tmp)
        assert code == 0 and out == ""


def test_cli_deny_contrato_oficial_y_sin_git():
    with tempfile.TemporaryDirectory() as tmp:
        # sin git: alcance sigue aplicando; rama principal no
        code, out, _ = run_cli(json.dumps(write(tmp + "/docs/roadmap/x/spec.md")), tmp)
        assert code == 0
        d = json.loads(out)["hookSpecificOutput"]
        assert d["hookEventName"] == "PreToolUse" and d["permissionDecision"] == "deny"
        assert d["permissionDecisionReason"]
        code, out, _ = run_cli(json.dumps(write(tmp + "/src/a.py")), tmp)
        assert code == 0 and out == ""


def test_cli_rama_principal_con_git_real():
    with tempfile.TemporaryDirectory() as tmp:
        _git(tmp, "init", "-q", "-b", "main")
        open(os.path.join(tmp, "a"), "w").write("a")
        _git(tmp, "add", "a")
        _git(tmp, "commit", "-qm", "init")
        code, out, _ = run_cli(json.dumps(write(tmp + "/src/a.py")), tmp)
        assert code == 0 and "feature/<slug>" in out
        code, out, _ = run_cli(json.dumps(write(tmp + "/docs/roadmap/x/tasks.md")), tmp)
        assert code == 0 and out == ""
        _git(tmp, "checkout", "-qb", "feature/x")
        code, out, _ = run_cli(json.dumps(write(tmp + "/src/a.py")), tmp)
        assert code == 0 and out == ""
        code, out, _ = run_cli(json.dumps(bash("git checkout main")), tmp)
        assert code == 0 and "feature/x" in out


def test_cli_guardrails_off_avisa_una_vez():
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, ".claude"))
        open(os.path.join(tmp, ".claude", "dev.json"), "w").write(json.dumps({"guardrails": False}))
        code, out, _ = run_cli(json.dumps(bash("git push --force")), tmp)
        assert code == 0 and "systemMessage" in out and "DESACTIVADOS" in out
        code, out, _ = run_cli(json.dumps(bash("git push --force")), tmp)
        assert code == 0 and out == ""


# ---------------------------------------------- modo architect (parity-core T-fix1) ----
def arch(payload, branch="main"):
    return gc.decide(payload, PROJ, None, branch=branch, agent="architect")


def edit(path, old, new):
    return {"tool_name": "Edit", "tool_input": {"file_path": path, "old_string": old, "new_string": new}}


def test_architect_allow_design_adr_e_indice_knowledge():
    assert arch(write("docs/roadmap/2026-01-01-x/design.md")) is None
    assert arch(write("docs/knowledge/adr/ADR-010-x.md")) is None
    assert arch(write("docs/knowledge/README.md", "Edit")) is None


def test_architect_deny_codigo_y_tasks_y_evaluation():
    r = arch(write("src/app.py"))
    assert r and "architect" in r and "design.md" in r
    r = arch(write("docs/roadmap/2026-01-01-x/tasks.md", "Edit"))
    assert r and "architect" in r
    assert arch(write("docs/roadmap/2026-01-01-x/evaluation.md", "Edit"))
    assert arch(write("docs/knowledge/gotchas/GOT-009-x.md"))          # solo adr/ + README
    assert arch(write("docs/security-scan/x.md"))


def test_architect_spec_y_plan_solo_edit_de_frontmatter_design():
    spec = "docs/roadmap/2026-01-01-x/spec.md"
    assert arch(edit(spec, "plan: pendiente", "design: design.md\nplan: pendiente")) is None
    assert arch(edit(spec, "> **Evaluación:**", "> **Diseño:** [`design.md`](design.md)\n> **Evaluación:**")) is None
    r = arch(edit(spec, "## Alcance", "## Alcance ampliado"))
    assert r and "design:" in r
    r = arch(write(spec))                                              # Write completo → deny
    assert r and "Edit" in r
    plan = "docs/roadmap/2026-01-01-x/improvement-plan.md"
    assert arch(edit(plan, "| **Evaluación** |", "| **Diseño** | design.md |\n| **Evaluación** |")) is None


def test_architect_no_aplica_rama_principal_pero_si_git():
    assert arch(write("docs/roadmap/2026-01-01-x/design.md"), branch="main") is None
    assert arch(bash("git push --force origin feature/x"))
    assert arch(bash("git status")) is None


def test_architect_razon_de_deny_nombra_a_architect_no_a_planner():
    r = arch(write("docs/roadmap/2026-01-01-x/tasks.md", "Edit"))
    assert "planner" not in r and "architect" in r


def test_implementer_razon_design_nombra_a_architect():
    r = decide(write("docs/roadmap/2026-01-01-x/design.md"))
    assert r and "architect" in r and "solo toca tasks.md" in r


def test_cli_agent_flag_y_env(tmp_path):
    payload = json.dumps(write("src/app.py"))
    r = subprocess.run([sys.executable, SCRIPT, "pre-tool", "--agent", "architect", "--project-dir", str(tmp_path)],
                       input=payload, capture_output=True, text=True)
    assert r.returncode == 0 and '"deny"' in r.stdout and "architect" in r.stdout
    env = dict(os.environ, CLAUDE_AGENT_NAME="architect")
    r = subprocess.run([sys.executable, SCRIPT, "pre-tool", "--project-dir", str(tmp_path)],
                       input=payload, capture_output=True, text=True, env=env)
    assert r.returncode == 0 and '"deny"' in r.stdout
    r = subprocess.run([sys.executable, SCRIPT, "pre-tool", "--project-dir", str(tmp_path)],
                       input=payload, capture_output=True, text=True, env={k: v for k, v in os.environ.items() if k != "CLAUDE_AGENT_NAME"})
    assert r.returncode == 0 and r.stdout.strip() == "", "implementer por defecto: src/app.py permitido en rama (sin git → sin ramaPrincipal)"
