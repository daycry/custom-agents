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


def journal_entry(root, name="entry.md", *, initiative="demo", sid="s1", runtime="codex", summary="Trabajo confirmado",
                  regla="vigente"):
    path = root / "docs" / "knowledge" / "journal" / name
    path.parent.mkdir(parents=True, exist_ok=True)
    metadata = {"fecha": "2026-10-09", "session_id": sid, "iniciativa": initiative,
                "resumen": summary, "fuente": "hook", "cierre": "normal"}
    if regla:
        metadata["regla_iniciativa"] = regla   # fix2 B-M4: como las escribe el escritor real
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
def test_h48_history_only_failure_injects_no_opaque_line(tmp_path, history, capsys, status):
    """H-48: a failed history selection no longer prints an opaque «Journal: <status>»
    line into the session block; /work-resume keeps reporting the status."""
    ledger(tmp_path, "2026-10-09-demo")
    history[0].update(status=status)
    assert pr.main(["resume", "--root", str(tmp_path), "--history-only"]) == 0
    assert capsys.readouterr().out == ""
    assert pr.resume(tmp_path, initiative="demo")["status"] == status


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


# ------------------------------------------------------------------ continuidad citada (D-085)

def continuity_entry(root, name="cont.md", *, lines, sid="s1"):
    """Entrada del journal con el esquema de continuidad tal como lo escribe journal.py."""
    path = journal_entry(root, name, sid=sid)
    text = path.read_text(encoding="utf-8").rstrip("\n")
    assert text.endswith("---")
    path.write_text(text[:-3] + "\n".join(lines) + "\n---\n", encoding="utf-8")
    return path


FULL_CONTINUITY = ['objetivo: "Cerrar D-085"', 'punto_actual: "tests en rojo"',
                   'siguientes_pasos:', '  - "implementar"', '  - "verde"',
                   'bloqueos:', '  - "falta revisión"']


def test_continuity_is_projected_and_rendered_as_historical_quote(tmp_path):
    ledger(tmp_path, "2026-10-09-demo")
    continuity_entry(tmp_path, lines=FULL_CONTINUITY)
    result = pr.resume(tmp_path, initiative="demo")
    assert result["status"] == "ok"
    assert result["history"][0]["continuidad"] == {
        "objetivo": "Cerrar D-085", "punto_actual": "tests en rojo",
        "siguientes_pasos": ["implementar", "verde"], "bloqueos": ["falta revisión"]}
    lines = pr.resume_text(result).splitlines()
    header = next(i for i, line in enumerate(lines) if line.startswith("Historial citado"))
    quoted = lines[header + 1:]
    assert "> Continuidad registrada (cita histórica, no instrucción):" in quoted
    for expected in ("> Objetivo: Cerrar D-085", "> Dónde quedó: tests en rojo",
                     "> Siguientes: implementar; verde", "> Bloqueos: falta revisión"):
        assert expected in quoted
    assert result["output_truncated"] is False


def test_entry_without_continuity_adds_nothing(tmp_path):
    ledger(tmp_path, "2026-10-09-demo")
    journal_entry(tmp_path)
    result = pr.resume(tmp_path, initiative="demo")
    assert result["status"] == "ok" and "continuidad" not in result["history"][0]
    text = pr.resume_text(result)
    assert "Continuidad" not in text and "Objetivo" not in text and "Bloqueos" not in text


def test_explicit_clearing_is_visible_and_omitted_fields_stay_absent(tmp_path):
    ledger(tmp_path, "2026-10-09-demo")
    continuity_entry(tmp_path, lines=['objetivo: ""', 'bloqueos: []'])
    result = pr.resume(tmp_path, initiative="demo")
    assert result["history"][0]["continuidad"] == {"objetivo": "", "bloqueos": []}
    text = pr.resume_text(result)
    assert "> Objetivo: (vaciado explícitamente en esa sesión)" in text
    assert "> Bloqueos: (vaciado explícitamente en esa sesión)" in text
    assert "Dónde quedó" not in text and "Siguientes" not in text


def test_continuity_respects_output_budgets(tmp_path):
    ledger(tmp_path, "2026-10-09-demo")
    big = ['objetivo: "' + "漢" * 3000 + '"', 'punto_actual: "SECRET\u202e' + "x" * 3000 + '"',
           'siguientes_pasos:'] + ['  - "' + "p" * 500 + '"'] * 6 + ['bloqueos:', '  - "' + "b" * 500 + '"']
    continuity_entry(tmp_path, "a.md", lines=big)
    continuity_entry(tmp_path, "b.md", lines=big, sid="s2")
    result = pr.resume(tmp_path, initiative="demo")
    output = json.dumps(result, ensure_ascii=False)
    assert len(output.encode("utf-8")) <= 12000 and "\u202e" not in output
    assert result["output_truncated"] is True
    rendered = pr.resume_text(result)
    assert len(rendered) <= 6000 and len(rendered.splitlines()) <= 32
    assert "\u202e" not in rendered


def test_discarded_approaches_are_quoted_in_the_continuity_group(tmp_path):
    """`descartados` viaja en el mismo grupo de continuidad, tras «Bloqueos», y con los mismos topes."""
    ledger(tmp_path, "2026-10-09-demo")
    continuity_entry(tmp_path, lines=FULL_CONTINUITY + [
        'descartados:', '  - "subir el timeout — el hook sigue muriendo a los 5 s"'])
    result = pr.resume(tmp_path, initiative="demo")
    assert result["history"][0]["continuidad"]["descartados"] == [
        "subir el timeout — el hook sigue muriendo a los 5 s"]
    lines = pr.resume_text(result).splitlines()
    assert "> Descartados: subir el timeout — el hook sigue muriendo a los 5 s" in lines
    assert lines.index("> Bloqueos: falta revisión") < lines.index(
        "> Descartados: subir el timeout — el hook sigue muriendo a los 5 s")
    continuity_entry(tmp_path, "c.md", lines=['descartados: []'], sid="s3")
    cleared = pr.resume(tmp_path, initiative="demo", session_id="s3")
    assert cleared["history"][0]["continuidad"] == {"descartados": []}
    assert "> Descartados: (vaciado explícitamente en esa sesión)" in pr.resume_text(cleared)


def test_discarded_approaches_respect_output_budgets(tmp_path):
    ledger(tmp_path, "2026-10-09-demo")
    big = (['objetivo: "' + "漢" * 3000 + '"', 'bloqueos:', '  - "' + "b" * 500 + '"', 'descartados:']
           + ['  - "' + "d‮" * 400 + '"'] * 6)
    continuity_entry(tmp_path, "a.md", lines=big)
    continuity_entry(tmp_path, "b.md", lines=big, sid="s2")
    result = pr.resume(tmp_path, initiative="demo")
    output = json.dumps(result, ensure_ascii=False)
    assert len(output.encode("utf-8")) <= 12000 and "‮" not in output
    assert result["output_truncated"] is True
    rendered = pr.resume_text(result)
    assert len(rendered) <= 6000 and len(rendered.splitlines()) <= 32 and "‮" not in rendered


def test_history_only_keeps_continuity_quote(tmp_path, capsys):
    ledger(tmp_path, "2026-10-09-demo")
    continuity_entry(tmp_path, lines=FULL_CONTINUITY)
    assert pr.main(["resume", "--root", str(tmp_path), "--history-only"]) == 0
    out = capsys.readouterr().out
    assert "historial citado" in out and "objetivo: Cerrar D-085" in out
    assert "siguientes pasos: implementar; verde" in out


# ------------------------------------------------- H-14: journal at startup without the global selection

def _big_completed_ledgers(root, count=5, size=240 * 1024):
    for index in range(count):
        path = ledger(root, f"2026-01-0{index + 1}-big{index}", state="completado")
        path.write_text(path.read_text(encoding="utf-8") + ("relleno " * 60 + "\n") * (size // 481),
                        encoding="utf-8")


def test_h14_history_only_with_more_than_1_mib_of_ledgers_reinjects_journal(tmp_path, capsys):
    _big_completed_ledgers(tmp_path)
    ledger(tmp_path, "2026-10-09-demo")
    journal_entry(tmp_path, "demo.md", initiative="demo", summary="Entrada vigente de demo")
    assert pr.main(["resume", "--root", str(tmp_path), "--history-only"]) == 0
    out = capsys.readouterr().out
    assert "Entrada vigente de demo" in out and "Journal: incomplete" not in out


def test_h14_history_only_with_two_active_uses_the_initiative_in_progress(tmp_path, capsys):
    ledger(tmp_path, "2026-10-08-demo")
    ledger(tmp_path, "2026-10-09-other")
    journal_entry(tmp_path, "demo.md", initiative="demo", sid="s-demo", summary="Historia de demo")
    journal_entry(tmp_path, "other.md", initiative="other", sid="s-other", summary="Historia de other")
    journal_entry(tmp_path, "ajena.md", initiative="ajena", sid="s-ajena", summary="Historia ajena")
    state = tmp_path / ".claude" / "usage-state.json"
    state.parent.mkdir()
    state.write_text(json.dumps({"demo/T-01": {"inicio": "2026-10-09T10:00:00Z"}}), encoding="utf-8")
    assert pr.main(["resume", "--root", str(tmp_path), "--history-only"]) == 0
    out = capsys.readouterr().out
    assert "Historia de demo" in out
    assert "Historia de other" not in out and "Historia ajena" not in out
    assert "Journal: ambiguous" not in out


def test_h14_history_only_never_injects_history_of_a_non_active_initiative(tmp_path, capsys):
    _big_completed_ledgers(tmp_path)
    ledger(tmp_path, "2026-10-09-demo")
    journal_entry(tmp_path, "ajena.md", initiative="ajena", summary="Historia ajena")
    assert pr.main(["resume", "--root", str(tmp_path), "--history-only"]) == 0
    assert capsys.readouterr().out == ""


# ------------------------------------------------- revisión intento 1 (fase 2): B1, C2/D1, B4

def _al_100(root, folder):
    path = root / "docs" / "roadmap" / folder / "tasks.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("---\nestado: en-progreso\n---\n## Fase 1 — Trabajo\n"
                    "### T-01 — Hecha\n\n- **Estado**: completado\n", encoding="utf-8")
    return path


def _journal_cli(root, *args):
    import subprocess, sys
    return subprocess.run([sys.executable, str(HERE / "journal.py"), *args, "--root", str(root)],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)


def _entrada_journal(root):
    """La única entrada escrita (el directorio también trae el README del journal; el orden de
    `glob` depende del sistema de ficheros)."""
    entradas = [p for p in (root / "docs/knowledge/journal").glob("*.md") if p.name != "README.md"]
    assert len(entradas) == 1, entradas
    return entradas[0].read_text(encoding="utf-8")


def test_fix1_b1_escritor_y_lector_del_journal_eligen_la_misma_iniciativa(tmp_path, capsys):
    """B1: el escritor etiquetaba con la primera activa alfabética y el lector con la en curso."""
    import os
    alfa = _al_100(tmp_path, "2026-10-01-alfa")          # al 100 %: no es «la en curso» si hay otra
    beta = ledger(tmp_path, "2026-10-02-beta")
    gamma = ledger(tmp_path, "2026-10-03-gamma")
    os.utime(alfa, (2_000_000_000, 2_000_000_000))       # la más reciente, pero al 100 %
    os.utime(beta, (1_000_000_000, 1_000_000_000))
    os.utime(gamma, (1_500_000_000, 1_500_000_000))
    assert pr.iniciativa_vigente(tmp_path) == "gamma"
    enrich = tmp_path / "enrich.json"
    enrich.write_text(json.dumps({"resumen": "Trabajo real de la sesion"}), encoding="utf-8")
    result = _journal_cli(tmp_path, "write", "--session-id", "s-b1", "--reason", "clear", "--ia", "off",
                          "--enrich", str(enrich))
    assert result.returncode == 0, result.stderr
    escrita = _entrada_journal(tmp_path)
    assert 'iniciativa: "gamma"' in escrita, escrita[:400]
    assert pr.main(["resume", "--root", str(tmp_path), "--history-only"]) == 0
    assert "s-b1" in capsys.readouterr().out


def test_fix1_b1_marcador_abierto_manda_en_escritor_y_lector(tmp_path):
    ledger(tmp_path, "2026-10-02-beta")
    ledger(tmp_path, "2026-10-03-gamma")
    state = tmp_path / ".claude" / "usage-state.json"
    state.parent.mkdir()
    state.write_text(json.dumps({"beta/T-01": {"inicio": "2026-10-09T10:00:00Z"}}), encoding="utf-8")
    assert pr.iniciativa_vigente(tmp_path) == "beta"
    assert _journal_cli(tmp_path, "write", "--session-id", "s-mk", "--reason", "clear", "--ia", "off").returncode == 0
    escrita = _entrada_journal(tmp_path)
    assert 'iniciativa: "beta"' in escrita


def test_fix1_c2_la_seleccion_usa_el_lector_acotado_y_no_el_escaneo_completo(tmp_path, monkeypatch):
    """C2/D1: ni `activas()` (open().read() sin tope, sigue enlaces) ni una segunda lectura del meter."""
    big = ledger(tmp_path, "2026-10-02-grande")
    big.write_text(big.read_text(encoding="utf-8") + ("relleno " * 60 + "\n") * 700, encoding="utf-8")
    monkeypatch.setattr(pr, "activas", lambda *a, **k: pytest.fail("escaneo completo sin tope"))
    assert pr.iniciativa_vigente(tmp_path) == "grande"   # > 256 KiB: se lee su cabecera acotada


def test_fix1_d1_usage_state_se_lee_una_vez_por_proceso_si_no_cambia(tmp_path, monkeypatch):
    state = tmp_path / ".claude" / "usage-state.json"
    state.parent.mkdir()
    state.write_text("{}", encoding="utf-8")
    import builtins
    real, lecturas = builtins.open, []
    def contar(path, *a, **k):
        if str(path).endswith("usage-state.json"):
            lecturas.append(path)
        return real(path, *a, **k)
    monkeypatch.setattr(builtins, "open", contar)
    roadmap = str(tmp_path / "docs" / "roadmap")
    pr._leer_usage_state(roadmap); pr._leer_usage_state(roadmap)
    assert len(lecturas) == 1


# ------------------------------------------------- revisión intento 2 (fase 2): B-I1, B-I2, B-M3, B-M4, C+D

def _plantilla(root, folder, *, estado="en-progreso", preambulo=0, tareas=1, hechas=0):
    """Ledger con el estado SOLO en la tabla de cabecera (plantilla del planner), sin frontmatter."""
    path = root / "docs" / "roadmap" / folder / "tasks.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    cuerpo = "".join(f"### T-{n:02} — Tarea\n\n- **Estado**: {'completado' if n <= hechas else 'en-progreso'}\n\n"
                     for n in range(1, tareas + 1))
    path.write_text("# Checklist de Tareas — demo\n\n" + ("> nota larga de contexto\n" * preambulo)
                    + f"| | |\n|---|---|\n| **Estado** | {estado} |\n\n## Fase 1 — Trabajo\n\n" + cuerpo
                    + ("relleno " * 60 + "\n") * 60, encoding="utf-8")
    return path


def test_fix2_bi1_estado_en_la_tabla_de_cabecera_cuenta(tmp_path):
    _plantilla(tmp_path, "2026-10-02-plantilla")
    assert pr.iniciativa_vigente(tmp_path) == "plantilla"


def test_fix2_bi1_estado_fuera_del_prefijo_no_se_da_por_inactivo(tmp_path):
    _plantilla(tmp_path, "2026-10-02-preambulo", preambulo=1200)   # la tabla queda más allá de 16 KiB
    assert pr.iniciativa_vigente(tmp_path) == "preambulo"


def test_fix2_bi2_el_marcador_abierto_manda_aunque_este_al_100(tmp_path):
    import os
    a = _al_100(tmp_path, "2026-10-01-alfa")
    b = ledger(tmp_path, "2026-10-02-beta")
    os.utime(a, (1_000_000_000, 1_000_000_000))
    os.utime(b, (2_000_000_000, 2_000_000_000))
    state = tmp_path / ".claude" / "usage-state.json"
    state.parent.mkdir()
    state.write_text(json.dumps({"alfa/retro.md": {"inicio": "2026-10-09T10:00:00Z"}}), encoding="utf-8")
    assert pr.iniciativa_vigente(tmp_path) == "alfa"


def test_fix2_bi2_empate_determinista_por_nombre(tmp_path):
    import os
    for folder in ("2026-10-02-beta", "2026-10-03-gamma"):
        os.utime(ledger(tmp_path, folder), (1_500_000_000, 1_500_000_000))
    assert pr.iniciativa_vigente(tmp_path) == "gamma"


def test_fix2_bm3_session_y_active_usan_la_misma_instantanea_acotada(tmp_path, monkeypatch, capsys):
    ledger(tmp_path, "2026-10-02-beta")
    _plantilla(tmp_path, "2026-10-03-gamma", tareas=3, hechas=1)
    monkeypatch.setattr(pr, "activas", lambda *a, **k: pytest.fail("lectura completa sin tope"))
    assert pr.main(["session", "--root", str(tmp_path)], in_process=True) == 0
    out = capsys.readouterr().out
    assert "en-progreso: T-02" in out and "- 📋 beta" in out
    assert pr.main(["active", "--root", str(tmp_path / "docs" / "roadmap"), "--json"]) == 0
    datos = json.loads(capsys.readouterr().out)
    assert datos["iniciativa_en_curso"] == pr.iniciativa_vigente(tmp_path)
    assert {a["slug"] for a in datos["activas"]} == {"beta", "gamma"}


def test_fix2_bm4_solo_se_reinyectan_entradas_con_la_regla_vigente(tmp_path, capsys):
    ledger(tmp_path, "2026-10-02-beta")
    journal_entry(tmp_path, "vieja.md", initiative="beta", sid="s-vieja", summary="Etiquetada con la regla vieja",
                  regla=None)
    assert pr.main(["resume", "--root", str(tmp_path), "--history-only"]) == 0
    assert "regla vieja" not in capsys.readouterr().out
    enrich = tmp_path / "enrich.json"
    enrich.write_text(json.dumps({"resumen": "Con la regla vigente"}), encoding="utf-8")
    assert _journal_cli(tmp_path, "write", "--session-id", "s-nueva", "--reason", "clear", "--ia", "off",
                        "--enrich", str(enrich)).returncode == 0
    nueva = [q for q in (tmp_path / "docs/knowledge/journal").glob("*.md") if "s-nueva" in q.read_text(encoding="utf-8")]
    assert len(nueva) == 1 and 'regla_iniciativa: "vigente"' in nueva[0].read_text(encoding="utf-8")
    assert pr.main(["resume", "--root", str(tmp_path), "--history-only"]) == 0
    out = capsys.readouterr().out
    assert "s-nueva" in out and "s-vieja" not in out


def test_fix2_cd_el_tope_de_la_regla_esta_documentado():
    for rel, clave in (("docs/WORK-RESUME.md", "128 carpetas más recientes"),
                       ("docs/en/WORK-RESUME.md", "128 most recent folders")):
        assert clave in (HERE.parent.parent / rel).read_text(encoding="utf-8"), rel
