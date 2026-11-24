"""Task handoffs through the public plugin entry points."""
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
