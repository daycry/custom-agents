"""Retoma dirigida: ledger vigente, selección inequívoca e historial acotado."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

HERE = Path(__file__).parent
SPEC = importlib.util.spec_from_file_location("work_resume_progress", HERE / "progress-report.py")
pr = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(pr)


def ledger(root, folder, *, state="en-progreso", title="Continuar implementación"):
    path = root / "docs" / "roadmap" / folder / "tasks.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\nestado: {state}\n---\n## Fase 1 — Trabajo\n"
                    f"### T-01 — {title}\n\n- **Estado**: {state}\n", encoding="utf-8")
    return path


def journal_entry(root, name="entry.md", *, initiative="demo", sid="s1", runtime="codex", summary="Trabajo confirmado"):
    path = root / "docs" / "knowledge" / "journal" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    metadata = {"fecha": "2026-10-09", "session_id": sid, "iniciativa": initiative,
                "resumen": summary, "fuente": "hook", "cierre": "normal"}
    if runtime is not None:
        metadata["runtime"] = runtime
    path.write_text("---\n" + "\n".join(key + ": " + json.dumps(value, ensure_ascii=False)
                                          for key, value in metadata.items()) + "\n---\n",
                    encoding="utf-8")
    return path


@pytest.fixture
def history(monkeypatch):
    calls = []
    response = {"status": "empty", "entries": [], "candidates": [], "issues": [], "complete": True}
    def select(root, **kwargs):
        calls.append(kwargs)
        return response.copy()
    def public(value, limit=240):
        return " ".join(str(value).replace("\u202e", "").split())[:limit].replace("SECRET", "[redacted]")
    def selected(result, **kwargs):
        if result["status"] != "ok":
            return "Journal: " + result["status"]
        return "Journal de sesión (historial citado): " + ", ".join(e["entry"] for e in result["entries"])
    original = pr._load_module
    def load(name, filename):
        if filename == "journal.py":
            return SimpleNamespace(select_entries=select, public_text=public, selected_text=selected)
        assert filename != "usage-meter.py", "La retoma no debe cargar el meter"
        return original(name, filename)
    monkeypatch.setattr(pr, "_load_module", load)
    monkeypatch.setattr(pr.subprocess, "run", lambda *a, **k: pytest.fail("Retoma ejecutó subprocess"))
    return response, calls


def test_unique_active_ledger_history_is_filtered(tmp_path, history):
    ledger(tmp_path, "2026-10-09-demo")
    ledger(tmp_path, "2026-10-08-done", state="completado")
    result = pr.resume(tmp_path)
    assert result["status"] == "ok"
    assert result["ledger"]["slug"] == "demo"
    assert history[1][-1]["initiative"] == "demo"
    assert result["history"] == []


def test_explicit_missing_session_with_ledger_retains_failure_status(tmp_path):
    ledger(tmp_path, '2026-10-09-demo')
    journal_entry(tmp_path)
    result = pr.resume(tmp_path, initiative='demo', session_id='missing')
    assert result['status'] == 'not_found' and result['history'] == []
    assert result['ledger']['slug'] == 'demo'


def test_partial_bundle_reports_missing_reader_without_exception_text(tmp_path, monkeypatch):
    original = pr._load_module
    def partial(name, filename):
        if filename == 'local-read.py':
            raise FileNotFoundError('private filename must not be echoed')
        return original(name, filename)
    monkeypatch.setattr(pr, '_load_module', partial)
    result = pr.resume(tmp_path)
    assert result['status'] == 'reader_unavailable'
    assert 'private filename' not in json.dumps(result)


def test_multibyte_projection_reports_truncation_and_changed_identity(tmp_path):
    jr = pr._load_module('projection_test_journal', 'journal.py')
    path = ledger(tmp_path, '2026-10-09-demo')
    summary = pr.resumir(str(path))
    summary['slug'] = '漢' * 80
    entry = jr._public_entry({'session_id': 's' * 150, 'iniciativa': 'demo'}, 'one.md')
    result = pr._public_resume(pr._resume_result('ok', ledger=summary, history=[entry]), jr)
    assert result['output_truncated'] is True
    assert result['history'][0]['output_truncated'] is True
    assert result['history'][0]['identity_resolvable'] is False
    only_ledger = pr._public_resume(pr._resume_result('ok', ledger=summary), jr)
    assert only_ledger['output_truncated'] is True


def test_multiple_active_requires_selection(tmp_path, history):
    ledger(tmp_path, "2026-10-09-one")
    ledger(tmp_path, "2026-10-09-two")
    result = pr.resume(tmp_path)
    assert result["status"] == "ambiguous"
    assert result["ledger"] is None
    assert set(result["candidates"]) == {"2026-10-09-one", "2026-10-09-two"}
    assert not history[1]


def test_exact_folder_can_select_completed_initiative(tmp_path, history):
    ledger(tmp_path, "2026-10-09-demo", state="completado")
    assert pr.resume(tmp_path, initiative="2026-10-09-demo")["ledger"]["estado"] == "completado"


def test_slug_collision_is_ambiguous(tmp_path, history):
    ledger(tmp_path, "2026-10-08-demo")
    ledger(tmp_path, "2026-10-09-demo")
    result = pr.resume(tmp_path, initiative="demo")
    assert result["status"] == "ambiguous" and result["ledger"] is None


@pytest.mark.parametrize("selection", ["../outside", "/absolute", "C:\\private", "demo/sub", ""])
def test_invalid_initiative_never_falls_back(tmp_path, history, selection):
    ledger(tmp_path, "2026-10-09-demo")
    result = pr.resume(tmp_path, initiative=selection)
    assert result["status"] == "invalid_selection"
    assert result["ledger"] is None and not history[1]


def test_missing_explicit_initiative_does_not_take_active(tmp_path, history):
    ledger(tmp_path, "2026-10-09-demo")
    result = pr.resume(tmp_path, initiative="other")
    assert result["status"] == "not_found" and result["ledger"] is None
    assert not history[1]


@pytest.mark.parametrize("status", ["ambiguous", "incomplete", "malformed", "unreadable", "not_found"])
def test_session_failure_never_uses_active(tmp_path, history, status):
    ledger(tmp_path, "2026-10-09-demo")
    history[0]["status"] = status
    history[0]["complete"] = status not in {"incomplete", "unreadable"}
    result = pr.resume(tmp_path, session_id="s-one", runtime="codex")
    assert result["status"] == status and result["ledger"] is None
    assert history[1][0]["session_id"] == "s-one"
    assert history[1][0]["runtime"] == "codex"


def test_selected_session_can_infer_its_initiative(tmp_path, history):
    ledger(tmp_path, "2026-10-09-current")
    ledger(tmp_path, "2026-10-08-old", state="completado")
    history[0].update(status="ok", entries=[{"entry": "chosen.md", "iniciativa": "old", "session_id": "s1"}])
    result = pr.resume(tmp_path, entry="chosen.md")
    assert result["status"] == "ok"
    assert result["ledger"]["slug"] == "old"
    assert result["history"][0]["entry"] == "chosen.md"


def test_selected_session_without_initiative_is_explicit(tmp_path, history):
    ledger(tmp_path, "2026-10-09-demo")
    history[0].update(status="ok", entries=[{"entry": "unknown.md", "session_id": "s1"}])
    result = pr.resume(tmp_path, session_id="s1")
    assert result["status"] == "initiative_unknown" and result["ledger"] is None


def test_truncated_session_identity_never_infers_initiative(tmp_path, history):
    ledger(tmp_path, "2026-10-09-demo")
    history[0].update(status="ok", entries=[{"entry": "e.md", "iniciativa": "demo", "output_truncated": True}])
    result = pr.resume(tmp_path, entry="e.md")
    assert result["status"] == "initiative_unknown" and result["ledger"] is None


def test_runtime_only_filters_the_unique_current_initiative(tmp_path, history):
    ledger(tmp_path, "2026-10-09-demo")
    result = pr.resume(tmp_path, runtime="codex")
    assert result["status"] == "ok" and result["ledger"]["slug"] == "demo"
    assert history[1] == [{"initiative": "demo", "session_id": None, "runtime": "codex", "entry": None}]


def test_explicit_folder_with_session_uses_canonical_slug_filter(tmp_path, history):
    ledger(tmp_path, "2026-10-09-demo")
    history[0].update(status="ok", entries=[{"entry": "e.md", "iniciativa": "demo", "session_id": "s1"}])
    result = pr.resume(tmp_path, initiative="2026-10-09-demo", session_id="s1")
    assert result["status"] == "ok"
    assert history[1] == [{"initiative": "demo", "session_id": "s1", "runtime": None, "entry": None}]


def test_historical_candidate_objects_render_without_execution(tmp_path, history):
    ledger(tmp_path, "2026-10-09-demo")
    history[0].update(status="ambiguous", candidates=[{"entry": "one.md", "runtime": "codex", "iniciativa": "demo"}])
    result = pr.resume(tmp_path, session_id="s1")
    assert "one.md" in pr.resume_text(result)


def test_empty_roadmap_is_not_global_history_absence(tmp_path, history):
    result = pr.resume(tmp_path)
    assert result["status"] == "not_found" and result["ledger"] is None
    assert result["issues"] and not history[1]


def test_malformed_ledger_blocks_implicit_selection(tmp_path, history):
    ledger(tmp_path, "2026-10-09-demo")
    broken = tmp_path / "docs" / "roadmap" / "2026-10-09-broken" / "tasks.md"
    broken.parent.mkdir()
    broken.write_text("not a ledger", encoding="utf-8")
    result = pr.resume(tmp_path)
    assert result["status"] == "incomplete" and result["ledger"] is None


def test_large_ledger_blocks_implicit_selection(tmp_path, history):
    ledger(tmp_path, "2026-10-09-demo")
    huge = tmp_path / "docs" / "roadmap" / "2026-10-09-huge" / "tasks.md"
    huge.parent.mkdir()
    huge.write_bytes(b"x" * (256 * 1024 + 1))
    result = pr.resume(tmp_path)
    assert result["status"] == "incomplete" and result["ledger"] is None


def test_history_failure_preserves_explicit_current_ledger(tmp_path, history):
    ledger(tmp_path, "2026-10-09-demo")
    history[0].update(status="incomplete", complete=False)
    result = pr.resume(tmp_path, initiative="2026-10-09-demo")
    assert result["status"] == "incomplete"
    assert result["ledger"]["slug"] == "demo"


def test_pure_text_summary_does_not_read_or_load_meter(tmp_path, history, monkeypatch):
    path = ledger(tmp_path, "2026-10-09-demo")
    text = path.read_text() + "\n- **Tiempo IA (ejec.)**: est. 1h · real 1h (medido)\n"
    path.unlink()
    result = pr.resumir(str(path), text=text)
    assert result["total"] == 1 and result["ia_real_fmt"] == "1h"


def test_output_strings_are_sanitized_redacted_and_bounded(tmp_path, history):
    ledger(tmp_path, "2026-10-09-demo", title="SECRET\u202e" + "x" * 3000)
    history[0].update(status="ok", entries=[{"entry": "e.md", "iniciativa": "demo", "resumen": "SECRET\n" + "x" * 20000}])
    result = pr.resume(tmp_path, initiative="demo")
    output = json.dumps(result, ensure_ascii=False)
    assert "SECRET" not in output and "\u202e" not in output
    assert len(output.encode("utf-8")) <= 12000
    assert result["output_truncated"] is True
    rendered = pr.resume_text(result)
    assert len(rendered) <= 6000 and len(rendered.splitlines()) <= 32


def test_cli_resume_json_is_same_compositor(tmp_path, history, capsys):
    ledger(tmp_path, "2026-10-09-demo")
    assert pr.main(["resume", "--root", str(tmp_path), "--initiative", "demo", "--json"]) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["ledger"]["slug"] == "demo"


def test_readonly_history_only_projects_common_selection(tmp_path, history, capsys):
    ledger(tmp_path, "2026-10-09-demo")
    history[0].update(status="ok", entries=[{"entry": "e.md", "iniciativa": "demo"}])
    assert pr.main(["resume", "--root", str(tmp_path), "--history-only"]) == 0
    assert "Journal de sesión" in capsys.readouterr().out
    assert history[1][-1]["initiative"] == "demo"


def test_history_only_no_history_injects_nothing(tmp_path, history, capsys):
    ledger(tmp_path, "2026-10-09-demo")
    assert pr.main(["resume", "--root", str(tmp_path), "--history-only"]) == 0
    assert capsys.readouterr().out == ""


@pytest.mark.parametrize("status", ["ambiguous", "incomplete", "malformed"])
def test_history_only_failure_has_status_and_no_transcription(tmp_path, history, capsys, status):
    ledger(tmp_path, "2026-10-09-demo")
    history[0].update(status=status)
    assert pr.main(["resume", "--root", str(tmp_path), "--history-only"]) == 0
    assert capsys.readouterr().out.strip() == "Journal: " + status


def test_large_history_summary_with_resolvable_identity_can_select_ledger(tmp_path, history):
    ledger(tmp_path, "2026-10-09-demo")
    history[0].update(status="ok", entries=[{"entry": "e.md", "iniciativa": "demo", "output_truncated": True,
                                           "identity_resolvable": True}])
    result = pr.resume(tmp_path, entry="e.md")
    assert result["status"] == "ok" and result["ledger"]["slug"] == "demo"


def test_changed_identity_never_infers_even_if_not_truncated(tmp_path, history):
    ledger(tmp_path, "2026-10-09-demo")
    history[0].update(status="ok", entries=[{"entry": "e.md", "iniciativa": "demo", "identity_resolvable": False}])
    result = pr.resume(tmp_path, entry="e.md")
    assert result["status"] == "initiative_unknown" and result["ledger"] is None


def test_real_selector_filters_initiative_and_runtime_and_is_readonly(tmp_path, monkeypatch):
    ledger(tmp_path, "2026-10-09-demo")
    journal_entry(tmp_path, "ours.md")
    journal_entry(tmp_path, "other.md", initiative="other")
    journal_entry(tmp_path, "legacy.md", runtime=None)
    before = {str(path.relative_to(tmp_path)): (path.read_bytes(), path.stat().st_mtime_ns)
              for path in tmp_path.rglob("*") if path.is_file()}
    monkeypatch.setattr(pr.subprocess, "run", lambda *a, **k: pytest.fail("La retoma ejecutó un subprocess"))
    result = pr.resume(tmp_path, initiative="demo", runtime="codex")
    assert result["status"] == "ok" and [e["entry"] for e in result["history"]] == ["ours.md"]
    after = {str(path.relative_to(tmp_path)): (path.read_bytes(), path.stat().st_mtime_ns)
             for path in tmp_path.rglob("*") if path.is_file()}
    assert before == after


def test_real_selector_session_runtime_collision_is_ambiguous(tmp_path):
    ledger(tmp_path, "2026-10-09-demo")
    journal_entry(tmp_path, "codex.md", runtime="codex")
    journal_entry(tmp_path, "claude.md", runtime="claude")
    result = pr.resume(tmp_path, session_id="s1")
    assert result["status"] == "ambiguous" and result["ledger"] is None
    assert "codex.md" in pr.resume_text(result)
    assert pr.resume(tmp_path, session_id="s1", runtime="codex")["ledger"]["slug"] == "demo"


def test_real_selector_exact_missing_entry_never_substitutes(tmp_path):
    ledger(tmp_path, "2026-10-09-demo")
    journal_entry(tmp_path)
    result = pr.resume(tmp_path, entry="absent.md")
    assert result["status"] == "not_found" and result["ledger"] is None and result["history"] == []


def test_explicit_ledger_missing_explicit_history_is_not_a_success(tmp_path):
    ledger(tmp_path, "2026-10-09-demo")
    journal_entry(tmp_path)
    result = pr.resume(tmp_path, initiative="demo", entry="absent.md")
    assert result["status"] == "not_found"
    assert result["ledger"]["slug"] == "demo" and result["history"] == []


def test_real_selector_large_identity_is_not_inferred_from_truncated_metadata(tmp_path):
    ledger(tmp_path, "2026-10-09-demo")
    journal_entry(tmp_path, initiative="demo" + "x" * 300)
    result = pr.resume(tmp_path, entry="entry.md")
    assert result["status"] == "initiative_unknown" and result["ledger"] is None


def test_real_selector_unicode_json_budget_and_controls(tmp_path):
    ledger(tmp_path, "2026-10-09-demo", title="漢" * 2000)
    journal_entry(tmp_path, summary="漢" * 10000 + "\u202e\nexit")
    result = pr.resume(tmp_path, initiative="demo")
    assert len(json.dumps(result, ensure_ascii=False).encode("utf-8")) <= 12000
    assert "\u202e" not in json.dumps(result, ensure_ascii=False)
    assert result["output_truncated"]


def test_real_roadmap_scan_limit_cannot_certify_unique_active(tmp_path):
    ledger(tmp_path, "2026-10-09-demo")
    directory = tmp_path / "docs" / "roadmap"
    for n in range(128):
        (directory / f"note-{n}.txt").write_text("note", encoding="utf-8")
    result = pr.resume(tmp_path)
    assert result["status"] == "incomplete" and result["ledger"] is None
    assert pr.resume(tmp_path, initiative="2026-10-09-demo")["ledger"]["slug"] == "demo"
