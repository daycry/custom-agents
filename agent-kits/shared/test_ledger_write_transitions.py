"""Task handoffs through the public plugin entry points."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

KIT = Path(__file__).resolve().parent
SLUG = "2026-11-24-fixture"
BASE = """# Fixture

> Ledger canónico.

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 — Fixture | 0 | 2 | 0.0% |
| **TOTAL** | **0** | **2** | **0.0%** |

## Fase 1 — Fixture

**Estado**: borrador · **Est.**: 1h

### T-01 — First

- **Estado**: borrador

**Criterios de aceptación**
- [x] Verified.

### T-02 — Second

- **Estado**: borrador

**Criterios de aceptación**
- [ ] Pending.
"""


@pytest.fixture
def ledger(tmp_path):
    path = tmp_path / "docs" / "roadmap" / SLUG / "tasks.md"
    path.parent.mkdir(parents=True)
    path.write_text(BASE, encoding="utf-8")
    return path


def cli(ledger, script, *args):
    return subprocess.run([sys.executable, str(KIT / (script + ".py")), *args],
                          cwd=ledger.parents[3], capture_output=True, encoding="utf-8", timeout=15)


def writer(ledger, operation, *args):
    return cli(ledger, "ledger-write", operation, str(ledger), *args, "--json")


def source(ledger):
    return ledger.read_text(encoding="utf-8")


def test_transicion_review_opens_header_with_states_and_phase(ledger):
    args = ("--tasks", "T-01,T-02", "--attempt", "1", "--summary", "Fixture")
    result = writer(ledger, "review", *args)
    assert result.returncode == 0, result.stderr
    assert source(ledger).count("- **Estado**: en-revision") == 2
    assert "**Estado**: en-revision · **Est.**: 1h" in source(ledger)
    assert "sin veredicto" in source(ledger)
    assert json.loads(writer(ledger, "review", *args).stdout)["changed"] is False


def test_verdict_clean_is_all_or_nothing_and_updates_summary(ledger):
    tasks = ("--tasks", "T-01,T-02", "--attempt", "1")
    assert writer(ledger, "review", *tasks, "--summary", "Fixture").returncode == 0
    before = ledger.read_bytes()
    failed = writer(ledger, "verdict", *tasks, "--result", "limpio")
    assert failed.returncode == 1, failed.stderr
    assert ledger.read_bytes() == before
    ledger.write_text(source(ledger).replace("- [ ] Pending.", "- [x] Pending."), encoding="utf-8")
    clean = writer(ledger, "verdict", *tasks, "--result", "limpio")
    assert clean.returncode == 0, clean.stdout + clean.stderr
    assert source(ledger).count("- **Estado**: completado") == 2
    assert "**Estado**: completado · **Est.**: 1h" in source(ledger)
    assert "| **TOTAL** | **2** | **2** | **100.0%** |" in source(ledger)
    assert json.loads(writer(ledger, "verdict", *tasks, "--result", "limpio").stdout)["changed"] is False


def test_verdict_gaps_reopens_only_selected_tasks(ledger):
    tasks = ("--tasks", "T-01,T-02", "--attempt", "1")
    assert writer(ledger, "review", *tasks, "--summary", "Fixture").returncode == 0
    result = writer(ledger, "verdict", *tasks, "--result", "gaps", "--gap-tasks", "T-02")
    assert result.returncode == 0, result.stdout + result.stderr
    first, second = source(ledger).split("### T-02")
    assert "- **Estado**: en-revision" in first
    assert "- **Estado**: en-progreso" in second
    assert "sin veredicto" not in source(ledger)
    assert json.loads(writer(ledger, "verdict", *tasks, "--result", "gaps", "--gap-tasks", "T-02").stdout)["changed"] is False


def test_transicion_brief_only_writes_on_explicit_dispatch(ledger):
    args = (str(ledger.parent), "T-01", "--runtime", "codex", "--extensions-project-only")
    assert cli(ledger, "task-brief", *args).returncode == 0
    assert source(ledger) == BASE
    result = cli(ledger, "task-brief", *args, "--dispatch")
    assert result.returncode == 0, result.stderr
    assert "- **Estado**: en-progreso" in source(ledger)
    again = cli(ledger, "task-brief", *args, "--dispatch")
    assert again.returncode == 0
    assert source(ledger).count("- **Estado**: en-progreso") == 1


def test_transicion_reconcile_uses_latest_review_without_inventing_one(ledger):
    ledger.write_text(BASE + """
## Revisión de dos lentes — intento 1: Fase 1 (T-01) — 1 Important

| # | Grado | Gap | Tarea | Corrección | Evidencia |
| 1 | Important | Missing check | T-01 | pendiente | — |

## Revisión de dos lentes — intento 2: Fase 1 (T-01) — 0 Critical, 0 Important
""", encoding="utf-8")
    result = writer(ledger, "reconcile", "--tasks", "T-01,T-02")
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["states"] == {"T-01": "completado", "T-02": "borrador"}
    assert source(ledger).count("## Revisión de dos lentes") == 2


def load_script(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def review_table(cell, correction):
    return ("\n| # | Grado | Gap | Tarea | Corrección | Evidencia |\n"
            f"| 1 | Important | Missing check | {cell} | {correction} | — |\n")


def test_fix1_gap4_reconcile_requires_later_verification_covering_task(ledger):
    active = BASE.replace("- **Estado**: borrador", "- **Estado**: en-progreso", 1)
    attempt = "\n## Revisión de dos lentes — intento "
    ledger.write_text(active + attempt + "1: Fase 1 (T-01) — 1 Important\n"
                      + review_table("T-01", "corregido en fix24")
                      + attempt + "2: Fase 2 (T-02) — 0 Critical, 0 Important\n", encoding="utf-8")
    args = ("--tasks", "T-01", "--dry-run")
    assert json.loads(writer(ledger, "reconcile", *args).stdout)["states"] == {"T-01": "en-progreso"}
    ledger.write_text(source(ledger) + attempt + "3: Fase 1 (T-01) — 0 Critical, 0 Important\n", encoding="utf-8")
    assert json.loads(writer(ledger, "reconcile", *args).stdout)["states"] == {"T-01": "completado"}


def test_fix1_gap5_start_and_dispatch_preserve_open_review(ledger):
    review = ("--tasks", "T-01", "--attempt", "1")
    assert writer(ledger, "review", *review, "--summary", "Fixture").returncode == 0
    pending = source(ledger)
    commands = [("task-brief", str(ledger.parent), "T-01", "--sin-lint", "--dispatch", "--runtime", "codex"),
                ("usage-meter", "start", "--artefacto", f"{SLUG}/T-01-fix1", "--state", "usage.json")]
    for script, *args in commands:
        result = cli(ledger, script, *args)
        assert result.returncode == 0, result.stderr
        assert source(ledger) == pending
        assert "review_open" in result.stdout + result.stderr
    assert writer(ledger, "verdict", *review, "--result", "gaps", "--gap-tasks", "T-01").returncode == 0
    assert writer(ledger, "handoff", "--task", "T-01", "--state", "en-revision", "--source", "usage-meter").returncode == 0
    assert cli(ledger, *commands[0]).returncode == 0
    assert "- **Estado**: en-progreso" in source(ledger)


def test_fix1_gap6_review_rejects_summary_with_undeclared_task(ledger):
    args = ("--tasks", "T-01", "--attempt", "1")
    result = writer(ledger, "review", *args, "--summary", "A reference to T-02")
    assert result.returncode == 2
    assert "summary_task_outside_tasks" in result.stdout
    assert source(ledger) == BASE
    assert writer(ledger, "review", *args, "--summary", "A check for T-01").returncode == 0
    assert writer(ledger, "verdict", *args, "--result", "limpio").returncode == 0


def test_fix1_gap7_reconcile_writes_closing_date(ledger):
    ledger.write_text(BASE + "\n## Revisión de dos lentes — intento 1: Fase 1 (T-01) — sin gaps\n",
                      encoding="utf-8")
    args = ("--tasks", "T-01")
    assert writer(ledger, "reconcile", *args).returncode == 0
    assert "- **Cerrada**: " in source(ledger).split("### T-02")[0]
    assert json.loads(writer(ledger, "reconcile", *args).stdout)["changed"] is False


@pytest.mark.parametrize("script", ["agent-kits/shared/ledger-lint.py", "agent-kits/shared/task-brief.py",
                                    "skills/jira-sync/scripts/jira-flow.py"])
def test_fix1_gap8_task_cell_context_does_not_participate_in_review(script):
    module = load_script(KIT.parents[1] / script)
    text = "## Revisión de dos lentes — intento 1: Fase 1 (T-21)\n"
    sections = module.secciones_revision(text + review_table("`T-21`/T-04 (origen T-03)", "pendiente"))
    assert module.ultimo_intento_para(sections, {"T-03"}) is None
    assert module.filas_pendientes_de_tarea(sections, "T-03") == (None, [])
    assert module.ultimo_intento_para(sections, {"T-04"}) == 1
    assert len(module.filas_pendientes_de_tarea(sections, "T-04")[1]) == 1


@pytest.mark.parametrize("states,expected", [
    (("borrador", "en-revision"), "en-progreso"), (("borrador", "completado"), "en-progreso"),
    (("borrador", "en-progreso"), "en-progreso"),
    (("en-revision", "completado"), "en-revision"), (("en-revision", "cancelado"), "en-revision"),
    (("borrador", "borrador"), "borrador"),
])
def test_fix1_gap9_phase_state_uses_all_nonterminal_tasks(states, expected):
    module = load_script(KIT / "ledger-write.py")
    assert module.phase_state([{"estado": state} for state in states]) == expected


def test_fix1_gap10_writer_validates_each_input_snapshot_once(ledger, monkeypatch):
    module = load_script(KIT / "ledger-write.py")
    calls = []
    lint = module.LINT.lint

    def counted(path, *, text, **kwargs):
        calls.append(text)
        return lint(path, text=text, **kwargs)

    monkeypatch.setattr(module.LINT, "lint", counted)
    assert module.main(["state", str(ledger), "--task", "T-01", "--state", "en-progreso"]) == 0
    assert calls == [BASE, source(ledger)]


def test_fix1_gap1_implementer_docs_describe_plugin_owned_states():
    root = KIT.parents[1]
    doc = (root / "docs/agents/implementer.md").read_text(encoding="utf-8")
    for fragment in ("`en-progreso`", "`en-revision`", "`completado`", "`ledger-write.py verdict`", "`Cerrada`"):
        assert fragment in doc
    assert "checkbox + estado" not in doc
    for rel in ("docs/PLUGIN-PANEL.md", "docs/en/PLUGIN-PANEL.md"):
        panel = (root / rel).read_text(encoding="utf-8").split("### `ledger-view.py`", 1)[0]
        closing_field = panel.rsplit("\n### ", 1)[-1]
        assert all(fragment in closing_field for fragment in ("`Cerrada`", "`ledger-write.py`", "`reconcile`"))


def test_fix1_gap11_shared_readme_documents_runtime_handoffs():
    rows = (KIT / "README.md").read_text(encoding="utf-8").splitlines()
    writer_row = next(row for row in rows if row.startswith("| `ledger-write.py`"))
    brief_row = next(row for row in rows if row.startswith("| `task-brief.py`"))
    assert all(f"`{operation}`" in writer_row for operation in ("handoff", "verdict", "reconcile"))
    assert "`--dispatch`" in brief_row and "`--runtime`" in brief_row


def test_fix2_gap1_ledger_records_verification():
    path = KIT.parents[1] / "docs/roadmap/2026-11-10-plugin-audit-2/tasks.md"
    task = source(path).split("### T-40 —", 1)[1].split("\n## Fase 4", 1)[0]
    _, separator, block = task.partition("**Fix2**")
    assert separator, "missing T-40 Fix2 block"
    assert len((separator + block.strip()).encode("utf-8")) <= 2500
    assert "passed" in block and "export-interop --check" in block
    receipt = next(json.loads(line.strip("`")) for line in block.splitlines() if line.startswith('`{"'))
    assert receipt["operation"] == "reconcile" and receipt["dry_run"] is True
    assert receipt["status"] == "ok" and receipt["input_sha256"] and receipt["output_sha256"]
    assert set(receipt["states"]) == {f"T-{n:02}" for n in range(12, 24)} | {"T-40"}
    assert isinstance(receipt["warnings"], list)


def test_fix2_gap6_ledger_discloses_concurrent_doc_assertion():
    path = KIT.parents[1] / "docs/roadmap/2026-11-10-plugin-audit-2/tasks.md"
    task = source(path).split("### T-40 —", 1)[1].split("\n## Fase 4", 1)[0]
    assert "TDD n/a: aserción de texto añadida con su doc" in task


@pytest.mark.parametrize("cell,expected", [
    ("T-01; T-02", {"T-01", "T-02"}), ("T-01 + T-02", {"T-01", "T-02"}),
    ("T-01 → T-02", {"T-01", "T-02"}), ("(T-01)", {"T-01"}),
    ("Fase 1 (T-01)", {"T-01"}), ("T-21 (origen T-03)", {"T-21"}),
    ("T-01 (mensaje de `T-02`) (ver T-03) (cf. T-04)", {"T-01"}),
    ("T-01 (origen T-02; T-03)", {"T-01", "T-02", "T-03"}),
])
def test_fix2_gap2_task_cells_count_ids_unless_explicit_context(cell, expected):
    for script in (KIT / "ledger-lint.py", KIT / "task-brief.py",
                   KIT.parents[1] / "skills/jira-sync/scripts/jira-flow.py"):
        assert load_script(script).ids_de_celda_tarea(cell) == expected, script.name


@pytest.mark.parametrize("cell", ["T-02; T-01", "T-02 + T-01", "T-02 → T-01", "(T-01)", "Fase 1 (T-01)"])
def test_fix2_gap2_critical_cell_blocks_clean_verdict_brief_and_jira(ledger, cell):
    review = ("--tasks", "T-01", "--attempt", "1")
    assert writer(ledger, "review", *review, "--summary", "Fixture").returncode == 0
    content = source(ledger).replace("- [ ] Pending.", "- [x] Verified.")
    content += review_table(cell, "pendiente").replace("| Important |", "| Critical |")
    ledger.write_text(content, encoding="utf-8")
    result = writer(ledger, "verdict", *review, "--result", "limpio")
    assert json.loads(result.stdout)["status"] == "blocking_gaps"
    assert source(ledger) == content
    brief = load_script(KIT / "task-brief.py")
    sections = brief.secciones_revision(content)
    assert len(brief.filas_pendientes_de_tarea(sections, "T-01")[1]) == 1
    jira = load_script(KIT.parents[1] / "skills/jira-sync/scripts/jira-flow.py")
    approved, reason = jira.evidencia_aprobado(content, ["T-01"], qa_verde=True)
    assert approved is None and "1 gap(s)" in reason


@pytest.mark.parametrize("current,target,open_review,status", [
    ("en-progreso", "en-progreso", False, "ok"),
    ("en-revision", "en-revision", False, "ok"),
    ("en-revision", "en-progreso", True, "review_open"),
])
def test_fix2_gap3_noop_handoff_only_reads_once(ledger, monkeypatch, capsys,
                                               current, target, open_review, status):
    content = BASE.replace("- **Estado**: borrador", f"- **Estado**: {current}", 1)
    if open_review:
        content += "\n## Revisión de dos lentes — intento 1: Fixture (T-01)\n\nPendiente de revisión; sin veredicto.\n"
    ledger.write_text(content, encoding="utf-8")
    module = load_script(KIT / "ledger-write.py")
    read = module.IO.read
    reads = []

    def counted(path, *args, **kwargs):
        reads.append(path)
        return read(path, *args, **kwargs)

    def unexpected(*args, **kwargs):
        pytest.fail("full parse, lint or lock on a no-op handoff")

    monkeypatch.setattr(module.IO, "read", counted)
    monkeypatch.setattr(module.LINT, "parse_ledger", unexpected)
    monkeypatch.setattr(module.LINT, "lint", unexpected)
    monkeypatch.setattr(module.IO, "locked", unexpected)
    rc = module.main(["handoff", str(ledger), "--task", "T-01", "--state", target,
                      "--source", "usage-meter", "--json"])
    assert rc == (0 if status == "ok" else 1)
    assert json.loads(capsys.readouterr().out)["status"] == status
    assert reads == [ledger] and source(ledger) == content


def test_fix2_gap3_changed_handoff_validates_once(ledger, monkeypatch):
    module = load_script(KIT / "ledger-write.py")
    lint = module.LINT.lint
    calls = []

    def counted(*args, **kwargs):
        calls.append(kwargs["text"])
        return lint(*args, **kwargs)

    monkeypatch.setattr(module.LINT, "lint", counted)
    assert module.main(["handoff", str(ledger), "--task", "T-01", "--state", "en-progreso",
                        "--source", "usage-meter"]) == 0
    assert "- **Estado**: en-progreso" in source(ledger)
    assert len(calls) == 1


@pytest.mark.parametrize("states,expected", [
    (("cancelado", "cancelado"), "cancelado"), (("completado", "cancelado"), "completado"),
    (("borrador", "cancelado"), "borrador"),
])
def test_fix2_gap4_phase_state_respects_cancellation(states, expected):
    module = load_script(KIT / "ledger-write.py")
    assert module.phase_state([{"estado": state} for state in states]) == expected
