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
    ("T-01 → T-02", {"T-01", "T-02"}), ("(T-01)", None),
    ("Fase 1 (T-01)", None), ("T-21 (origen T-03)", {"T-21"}),
    ("T-01 (mensaje de `T-02`) (ver T-03) (cf. T-04)", {"T-01"}),
    ("T-01 (origen T-02; T-03)", None),
])
def test_fix2_gap2_task_cells_count_ids_unless_explicit_context(cell, expected):
    for script in (KIT / "ledger-lint.py", KIT / "task-brief.py",
                   KIT.parents[1] / "skills/jira-sync/scripts/jira-flow.py"):
        assert load_script(script).ids_de_celda_tarea(cell) == expected, script.name


@pytest.mark.parametrize("cell", ["T-02; T-01", "T-02 + T-01", "T-02 → T-01", "(T-01)",
                                  "Fase 1 (T-01)", "T-01 (origen T-02; T-03)"])
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
    if cell == "T-01 (origen T-02; T-03)":
        assert brief.tareas_de_fila(sections[-1]["filas"][0]) == {"T-01", "T-02", "T-03"}
    assert len(brief.filas_pendientes_de_tarea(sections, "T-01")[1]) == 1
    jira = load_script(KIT.parents[1] / "skills/jira-sync/scripts/jira-flow.py")
    approved, reason = jira.evidencia_aprobado(content, ["T-01"], qa_verde=True)
    assert approved is None and "1 gap(s)" in reason


@pytest.mark.parametrize("cell,expected", [
    ("T-01..T-03", {"T-01", "T-02", "T-03"}),
    ("T-01 a T-03", {"T-01", "T-02", "T-03"}),
    ("T-01–T-03", {"T-01", "T-02", "T-03"}),
    ("T-01-T-03", {"T-01", "T-02", "T-03"}),
    ("`T-03-fix2` & T-01/T-02 y T-04, T-05 + T-06; T-07 → T-08",
     {f"T-{n:02}" for n in range(1, 9)}),
    ("T-01 (origen T-09), `T-02` (ver T-10) (mensaje de T-11) (cf. T-12)",
     {"T-01", "T-02"}),
    ("todas", set()), ("Fase 3", set()),
    ("", None), ("T-01/02", None), ("T-01, 02", None),
    ("(T-01)", None), ("Fase 1 (T-01)", None), ("T-01 (alcance)", None),
    ("T-03..T-01", None), ("T-01…T-03", None), ("T-01—T-03", None),
    ("T-01 al T-03", None), ("T-01 hasta T-03", None),
    ("T-01 (origen T-02; T-03)", None), ("T-01 (origen T-02", None),
    ("T-01 y", None), ("y T-01", None), ("T-01 T-02", None),
    ("T-01 && T-02", None), ("T-01foo", None), ("pre T-01", None),
    ("T-01-fixx", None), ("`T-01", None), ("(ver T-01)", None),
    ("T-16 (alcance), T-01..T-15", None),
])
def test_fix3_gap1_task_cell_whitelist(cell, expected):
    for script in (KIT / "ledger-lint.py", KIT / "task-brief.py",
                   KIT.parents[1] / "skills/jira-sync/scripts/jira-flow.py"):
        assert load_script(script).ids_de_celda_tarea(cell) == expected, script.name


@pytest.mark.parametrize("cell,warns", [
    ("T-01..T-03", False), ("todas", False), ("Fase 1", False),
    ("T-01 (alcance), T-01..T-03", True), ("T-01/03", True), ("(ver T-01)", True),
])
def test_fix3_gap1_section_wide_or_range_blocks_all_consumers(ledger, cell, warns):
    review = ("--tasks", "T-01,T-02,T-03", "--attempt", "1")
    third = BASE[BASE.index("### T-02"):].replace("T-02", "T-03")
    content = (BASE + "\n" + third).replace("| 0 | 2 |", "| 0 | 3 |").replace("**2**", "**3**")
    ledger.write_text(content.replace("- [ ] Pending.", "- [x] Verified."), encoding="utf-8")
    assert writer(ledger, "review", *review, "--summary", "Fixture").returncode == 0
    content = source(ledger) + review_table(cell, "pendiente").replace("| Important |", "| Critical |")
    ledger.write_text(content, encoding="utf-8")
    result = writer(ledger, "verdict", *review, "--result", "limpio")
    assert json.loads(result.stdout)["status"] == "blocking_gaps"
    assert source(ledger) == content
    brief = load_script(KIT / "task-brief.py")
    lint = load_script(KIT / "ledger-lint.py")
    jira = load_script(KIT.parents[1] / "skills/jira-sync/scripts/jira-flow.py")
    sections = brief.secciones_revision(content)
    for task in ("T-01", "T-02", "T-03"):
        assert lint.blocking_tasks(sections[-1], {task}) == {task}
        assert len(brief.filas_pendientes_de_tarea(sections, task)[1]) == 1
        approved, reason = jira.evidencia_aprobado(content, [task], qa_verde=True)
        assert approved is None and "1 gap(s)" in reason
    line = next(i for i, text in enumerate(content.splitlines(), 1) if f"| {cell} |" in text)
    warnings = lint.lint(ledger)[1]
    assert any(f"línea {line}:" in warning and cell in warning for warning in warnings) == warns


def test_fix4_gap1_real_panel_redesign_cell_blocks_T16_and_the_section():
    path = KIT.parents[1] / "docs/roadmap/2026-10-15-panel-redesign/tasks.md"
    lint = load_script(KIT / "ledger-lint.py")
    sections = lint.secciones_revision(source(path))
    section, row = next((section, row) for section in sections for row in section["filas"]
                        if row["tarea"] == "T-16 (alcance), T-01..T-15")
    assert lint.ids_de_celda_tarea(row["tarea"]) is None
    assert lint.blocking_tasks(
        {**section, "filas": [{**row, "correccion": "pendiente"}]}, {"T-07", "T-16"}
    ) == {"T-07", "T-16"}


@pytest.mark.parametrize("cell,extra", [
    ("T-03 (regresión)", {"T-03"}), ("T-03/T-01 (#1)", {"T-03"}),
    ("T-03 al T-04", {"T-03", "T-04"}),
])
def test_fix4_gap1_ambiguous_cell_blocks_its_ids_and_section(cell, extra):
    text = BASE + """\n### T-03 — Third
### T-04 — Fourth
### T-05 — Fifth
## Revisión de dos lentes — intento 1: Fase 2 (T-03) — sin gaps
**Veredicto del plugin**: limpio
## Revisión de dos lentes — intento 2: Fase 1 (T-01, T-02)
"""
    text += review_table(cell, "pendiente").replace("| Important |", "| Critical |")
    text += "\n| 2 | Minor | Cross-reference | T-05 | corregido | a.py:2 |\n"
    lint = load_script(KIT / "ledger-lint.py")
    brief = load_script(KIT / "task-brief.py")
    jira = load_script(KIT.parents[1] / "skills/jira-sync/scripts/jira-flow.py")
    affected = {"T-01", "T-02", "T-05"} | extra
    section = lint.secciones_revision(text)[-1]
    assert lint.blocking_tasks(section, affected) == affected
    sections = brief.secciones_revision(text)
    for task in affected:
        assert brief.filas_pendientes_de_tarea(sections, task)[0] == 2
        approved, reason = jira.evidencia_aprobado(text, [task], qa_verde=True)
        assert approved is None and "1 gap(s)" in reason


def test_fix4_gap2_range_expansion_is_bounded_and_warns(ledger):
    cell = "T-01..T-9999"
    text = BASE + "\n## Revisión de dos lentes — intento 1: (T-01)\n"
    text += review_table(cell, "pendiente")
    lint = load_script(KIT / "ledger-lint.py")
    section = lint.secciones_revision(text)[0]
    assert lint.ids_de_celda_tarea("T-01..T-500") == {f"T-{n:02}" for n in range(1, 501)}
    assert lint.ids_de_celda_tarea("T-01..T-501") is None
    assert lint.blocking_tasks(section, {"T-01", "T-02", "T-9999"}) == {"T-01", "T-02", "T-9999"}
    line = next(i for i, row in enumerate(text.splitlines(), 1) if f"| {cell} |" in row)
    assert any(f"línea {line}:" in w and cell in w and "no reconocida" in w
               for w in lint.lint(ledger, text=text)[1])


def test_fix4_gap2_brief_queries_do_not_reparse_review_rows(monkeypatch):
    brief = load_script(KIT / "task-brief.py")
    parse = brief.ids_de_celda_tarea
    calls = 0

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return parse(*args, **kwargs)

    monkeypatch.setattr(brief, "ids_de_celda_tarea", counted)
    text = BASE + "\n## Revisión de dos lentes — intento 1: (T-01)\n"
    text += review_table("T-01..T-500", "pendiente")
    text += "".join(f"| {n} | Critical | Gap | T-01..T-9999 | pendiente | a.py:1 |\n"
                    for n in range(2, 101))
    sections = brief.secciones_revision(text)
    parsed_calls = calls
    for number in range(1, 41):
        brief.filas_pendientes_de_tarea(sections, f"T-{number:02}")
    assert calls == parsed_calls
    assert parsed_calls <= 100


@pytest.mark.parametrize("cell,expected", [
    ("T-001", {"T-01"}), ("T-1", {"T-01"}), ("T-001..T-2", {"T-01", "T-02"}),
    ("T-01–T-03–T-05", {"T-01", "T-02", "T-03", "T-04", "T-05"}),
])
def test_fix4_gap3_numeric_aliases_and_chained_ranges(cell, expected):
    text = BASE + """\n### T-03 — Third
### T-04 — Fourth
### T-05 — Fifth
## Revisión de dos lentes — intento 1: (T-004)
"""
    text += review_table(cell, "pendiente")
    lint = load_script(KIT / "ledger-lint.py")
    section = lint.secciones_revision(text)[-1]
    assert lint.tareas_de_fila(section["filas"][0]) == expected
    assert "T-04" in lint.latest_reviews([section])
    assert ("linea_tarea_no_reconocida" in section["filas"][0]) == ("–" in cell)


def test_fix4_gap3_unknown_id_warns_with_its_line(ledger):
    text = BASE + "\n## Revisión de dos lentes — intento 1: (T-99)\n"
    text += review_table("T-0999 (revisar)", "pendiente")
    lint = load_script(KIT / "ledger-lint.py")
    warnings = lint.lint(ledger, text=text)[1]
    for fragment, task in (("(T-99)", "T-99"), ("T-0999 (revisar)", "T-0999")):
        line = next(i for i, row in enumerate(text.splitlines(), 1) if fragment in row)
        assert any(f"línea {line}:" in warning and "desconocido" in warning and task in warning
                   for warning in warnings)


def test_fix4_gap4_header_range_is_a_mention_without_rows():
    text = BASE + """\n### T-03 — Third
## Revisión de dos lentes — intento 1: (T-01..T-03) — sin gaps
**Veredicto del plugin**: limpio
## Revisión de dos lentes — intento 1: (T-03)
"""
    text += review_table("T-02", "corregido")
    lint = load_script(KIT / "ledger-lint.py")
    brief = load_script(KIT / "task-brief.py")
    jira = load_script(KIT.parents[1] / "skills/jira-sync/scripts/jira-flow.py")
    for parser in (lint, brief, jira):
        own, other = parser.secciones_revision(text)
        assert parser.menciones(own) == {"T-01", "T-02", "T-03"}
        assert parser.seleccionar_seccion([own, other], 1, ["T-02"]) == (own, None)
        assert parser.filas_pendientes_de_tarea([own], "T-02") == (1, [])
    own_review = text.rsplit("## Revisión", 1)[0]
    assert jira.evidencia_aprobado(own_review, ["T-02"], qa_verde=True)[0] is not None


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


def test_fix6_gap1_real_reclassified_counts(monkeypatch):
    roadmap = KIT.parents[1] / "docs/roadmap"
    jira = load_script(KIT.parents[1] / "skills/jira-sync/scripts/jira-flow.py")
    brief = load_script(KIT / "task-brief.py")
    monkeypatch.setattr(jira, "_cargar_ledger_lint", lambda: None)
    for slug, tasks in (
        ("2026-09-03-windows-console", ["T-04"]),
        ("2026-11-09-plugin-audit-remediation", [f"T-{n:02}" for n in range(17, 22)]),
    ):
        text = source(roadmap / slug / "tasks.md")
        sections = brief.secciones_revision(text)
        for task in tasks:
            assert not brief.filas_pendientes_de_tarea(sections, task)[1], (slug, task)
            assert jira.evidencia_aprobado(text, [task], qa_verde=True)[0] is not None, (slug, task)
            assert jira.evidencia_aprobado(text, [task], qa_verde=False)[0] is None


@pytest.mark.parametrize("heading,rows,warns", [
    ("2 Important, 1 Minor", [("Important", "pendiente")], True),
    ("1 Important", [("Minor", "pendiente")], True),
    ("1 Critical", [], True),
    ("1 Important", [("Important", "corregido")], False),
    ("1 Important", [("Important", "pendiente")], False),
    ("0 Critical, 1 Minor", [], False),
    ("1 Critical, 1 Important", [("Critical", "corregido")] * 2, False),
])
def test_fix6_gap1_counts_only_warn(ledger, heading, rows, warns):
    text = BASE.replace("- [ ] Pending.", "- [x] Verified.")
    text += f"\n## Revisión de dos lentes — intento 1: (T-01..T-02) — {heading}\n"
    header_line = len(text.splitlines())
    for severity, correction in rows:
        text += review_table("T-01", correction).replace("| Important |", f"| {severity} |")
    ledger.write_text(text, encoding="utf-8")
    lint = load_script(KIT / "ledger-lint.py")
    brief = load_script(KIT / "task-brief.py")
    jira = load_script(KIT.parents[1] / "skills/jira-sync/scripts/jira-flow.py")
    assert not brief.filas_pendientes_de_tarea(brief.secciones_revision(text), "T-02")[1]
    assert jira.evidencia_aprobado(text, ["T-02"], qa_verde=True)[0] is not None
    assert any(f"línea {header_line}:" in w and "recuento" in w for w in lint.lint(ledger)[1]) == warns
    blocked = ("Important", "pendiente") in rows
    result = writer(ledger, "verdict", "--tasks", "T-01,T-02", "--attempt", "1", "--result", "limpio")
    assert (result.returncode != 0) == blocked, result.stdout + result.stderr
    if blocked:
        assert json.loads(result.stdout)["status"] == "blocking_gaps" and source(ledger) == text


@pytest.mark.parametrize("heading", ["2 Important", "dos Important", "2 Importantes", "Important: 2"])
@pytest.mark.parametrize("correction", ["pendiente", "corregido"])
def test_fix6_gap2_count_wording_preserves_rows(heading, correction, monkeypatch):
    brief = load_script(KIT / "task-brief.py")
    jira = load_script(KIT.parents[1] / "skills/jira-sync/scripts/jira-flow.py")
    monkeypatch.setattr(jira, "_cargar_ledger_lint", lambda: None)
    text = BASE + f"\n## Revisión de dos lentes — intento 1: (T-01) — {heading}\n"
    text += review_table("T-01", correction)
    rows = brief.filas_pendientes_de_tarea(brief.secciones_revision(text), "T-01")[1]
    assert [row["num"] for row in rows] == (["1"] if correction == "pendiente" else [])
    assert (jira.evidencia_aprobado(text, ["T-01"], qa_verde=True)[0] is None) == bool(rows)


@pytest.mark.parametrize("later, warns", [
    ("(T-01)\n\n**Veredicto del plugin**: limpio\n", True),
    ("(T-01..T-02)\n\n**Veredicto del plugin**: limpio\n", False),
    ("(T-01..T-02)\n\nPendiente de revisión; sin veredicto.\n", True),
    ("(T-01)\n" + review_table("T-01,T-02", "pendiente"), False),
])
def test_fix6_gap2_later_evidence_covers_warning(ledger, later, warns):
    text = BASE + "\n## Revisión de dos lentes — intento 9: (T-01..T-02) — 2 Important\n"
    header_line = len(text.splitlines())
    text += f"\n## Revisión de dos lentes — intento 1: {later}"
    lint = load_script(KIT / "ledger-lint.py")
    warnings = lint.lint(ledger, text=text)[1]
    assert (f"línea {header_line}: recuento de gaps sin filas legibles suficientes" in warnings) == warns


def test_fix6_gap2_archived_attempt_no_synthetic_block():
    ledger = KIT.parents[1] / "docs/roadmap/2026-11-10-plugin-audit-2/tasks.md"
    lint = load_script(KIT / "ledger-lint.py")
    sections = lint.secciones_revision(source(ledger))
    archived = next(s for s in sections if s["intento"] == 18)
    for task in ("T-06", "T-07", "T-23"):
        assert not lint.blocking_tasks(archived, {task})
        assert all(row["intento"] != 18 for row in lint.filas_pendientes_de_tarea(sections, task)[1])


def test_fix6_gap4_attempt18_archived_task_results():
    ledger = KIT.parents[1] / "docs/roadmap/2026-11-10-plugin-audit-2/tasks.md"
    lint = load_script(KIT / "ledger-lint.py")
    text = source(ledger)
    attempt = next(s for s in lint.secciones_revision(text) if s["intento"] == 18)
    assert "Resultado archivado por tarea" in attempt["resumen"]
    assert "T-07 sin gaps" in attempt["resumen"]
    assert [(r["num"], r["tarea"], r["correccion"]) for r in attempt["filas"]] == [
        ("1", "T-06", "corregido en fix18"), ("2", "T-06", "corregido en fix18"),
        ("3", "T-23", "corregido en fix18"), ("4", "T-23", "corregido en fix18"),
        ("5", "T-06", "límite conocido"),
    ]
    line = text[:attempt["inicio"]].count("\n") + 1
    assert not any(w.startswith((f"línea {line}:", "T-07:")) for w in lint.lint(ledger)[1])


@pytest.mark.parametrize("cell", ["T-05..T-01", "T-01–T-03–T-05", "nota T-01..T-05",
                                  "T-01..T-99999999999999999999"])
def test_fix5_gap3_embedded_ranges(cell):
    text = BASE + "\n### T-03 — Third\n### T-04 — Fourth\n### T-05 — Fifth\n"
    text += "## Revisión de dos lentes — intento 1: (T-01)\n" + review_table(cell, "pendiente")
    lint = load_script(KIT / "ledger-lint.py")
    tasks = {f"T-{n:02}" for n in range(1, 6)}
    assert lint.blocking_tasks(lint.secciones_revision(text)[0], tasks) == tasks


@pytest.mark.parametrize("alias", ["T-001", "T-1", "T-01"])
def test_fix5_gap4_ambiguous_alias(ledger, alias):
    text = BASE + "\n### T-1 — Duplicate number\n## Revisión de dos lentes — intento 1: (T-02)\n"
    text += review_table(alias, "pendiente")
    lint = load_script(KIT / "ledger-lint.py")
    section = lint.secciones_revision(text)[0]
    assert lint.blocking_tasks(section, {"T-01", "T-1"}) == {"T-01", "T-1"}
    line = len(text.rstrip().splitlines())
    assert any(f"línea {line}:" in w and "ambigu" in w and "T-01" in w and "T-1" in w
               for w in lint.lint(ledger, text=text)[1])
