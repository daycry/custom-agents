"""Ledger mutations use the canonical parser, lock and atomic publication."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "agent-kits/shared/ledger-write.py"

BASE = """---
verificacion: obligatoria
---
# Tasks fixture

> Ledger canónico de progreso. Fuente única.

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 — Fixture | 0 | 2 | 0.0% |
| **TOTAL** | **0** | **2** | **0.0%** |

## Fase 1 — Fixture

### T-01 — First

- **Estado**: en-progreso
- **Changelog**: First change.
- **Verificación**: python check.py → exit 0

**Criterios de aceptación**
- [x] First verified criterion.

**Notas**: consumer content must remain verbatim.

### T-02 — Second

- **Estado**: borrador
- **Changelog**: Second change.
- **Verificación**: python check.py → exit 0

**Criterios de aceptación**
- [ ] Still pending.
"""


def call(path, *args):
    return subprocess.run([sys.executable, str(SCRIPT), *args[:1], str(path), *args[1:], "--json"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=False)


def lint(text, path):
    spec = importlib.util.spec_from_file_location("write_test_lint", ROOT / "agent-kits/shared/ledger-lint.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.lint(str(path), text=text)


@pytest.mark.parametrize("newline,bom", [("\n", b""), ("\r\n", b"\xef\xbb\xbf")])
def test_state_changes_only_selected_task_and_summary_with_original_encoding(tmp_path, newline, bom):
    path = tmp_path / "tasks.md"
    path.write_bytes(bom + BASE.replace("\n", newline).encode())
    result = call(path, "state", "--task", "T-01", "--state", "completado")
    assert result.returncode == 0, result.stderr
    receipt = json.loads(result.stdout)
    raw = path.read_bytes()
    assert raw.startswith(bom)
    if newline == "\r\n":
        assert b"\n" not in raw.replace(b"\r\n", b"")
    text = raw.decode("utf-8-sig").replace("\r\n", "\n")
    expected = BASE.replace("- **Estado**: en-progreso", "- **Estado**: completado", 1)
    expected = expected.replace("| Fase 1 — Fixture | 0 | 2 | 0.0% |", "| Fase 1 — Fixture | 1 | 2 | 50.0% |")
    expected = expected.replace("| **TOTAL** | **0** | **2** | **0.0%** |", "| **TOTAL** | **1** | **2** | **50.0%** |")
    assert text == expected
    assert lint(text, path) == ([], [])
    assert receipt["schema_version"] == 1 and receipt["changed"] is True
    assert receipt["output_sha256"] == hashlib.sha256(raw).hexdigest()
    again = call(path, "state", "--task", "T-01", "--state", "completado")
    assert again.returncode == 0 and json.loads(again.stdout)["changed"] is False


def test_red_and_review_are_canonical_and_idempotent(tmp_path):
    path = tmp_path / "tasks.md"
    path.write_text(BASE, encoding="utf-8")
    red = ("red", "--task", "T-02", "--test", "tests/test_feature.py::test_feature", "--error", "missing implementation", "--date", "2026-10-30")
    result = call(path, *red)
    assert result.returncode == 0, result.stderr
    text = path.read_text(encoding="utf-8")
    assert "RED: `tests/test_feature.py::test_feature` falló con missing implementation · 2026-10-30." in text.split("### T-02", 1)[1]
    assert call(path, *red).returncode == 0
    assert path.read_text(encoding="utf-8") == text

    review = ("review", "--attempt", "1", "--tasks", "T-01,T-02", "--summary", "Fixture phase")
    result = call(path, *review)
    assert result.returncode == 0, result.stderr
    text = path.read_text(encoding="utf-8")
    assert "## Revisión de dos lentes — intento 1: Fixture phase (T-01, T-02)" in text
    assert lint(text, path) == ([], [])
    assert call(path, *review).returncode == 0
    assert path.read_text(encoding="utf-8") == text


@pytest.mark.parametrize("args,status", [
    (("state", "--task", "T-02", "--state", "completado"), 1),
    (("state", "--task", "T-99", "--state", "en-progreso"), 2),
    (("state", "--task", "T-01", "--state", "invalid"), 2),
    (("red", "--task", "T-02", "--test", "case", "--error", "first\n## injected", "--date", "2026-10-30"), 2),
    (("red", "--task", "T-02", "--test", "case", "--error", "failed", "--date", "2026-02-30"), 2),
    (("red", "--task", "T-02", "--test", "case", "--error", "failed", "--date", "20261030"), 2),
    (("red", "--task", "T-02", "--test", "case", "--error", "failed\u2028## injected", "--date", "2026-10-30"), 2),
    (("state", "--task", "T-01", "--state", "completado", "--expected-sha256", "0" * 64), 3),
])
def test_rejected_input_never_changes_ledger_or_creates_a_lock(tmp_path, args, status):
    path = tmp_path / "tasks.md"
    raw = BASE.encode()
    path.write_bytes(raw)
    result = call(path, *args)
    assert result.returncode == status, result.stdout + result.stderr
    assert path.read_bytes() == raw
    assert not (tmp_path / ".ledger-write").exists()


def test_dry_run_is_read_only_and_reports_real_planned_hash(tmp_path):
    path = tmp_path / "tasks.md"
    path.write_text(BASE, encoding="utf-8")
    before = path.read_bytes()
    result = call(path, "state", "--task", "T-01", "--state", "completado", "--dry-run")
    assert result.returncode == 0, result.stderr
    row = json.loads(result.stdout)
    assert row["changed"] and row["dry_run"]
    assert row["input_sha256"] == hashlib.sha256(before).hexdigest()
    assert row["input_sha256"] != row["output_sha256"]
    assert path.read_bytes() == before
    assert not (tmp_path / ".ledger-write").exists()


def test_invalid_ledger_is_not_repaired_incidentally(tmp_path):
    path = tmp_path / "tasks.md"
    raw = BASE.replace("### T-02", "### T-01").encode()
    path.write_bytes(raw)
    result = call(path, "state", "--task", "T-01", "--state", "en-progreso")
    assert result.returncode == 1
    assert path.read_bytes() == raw


def test_shared_hardlink_is_rejected_without_writes(tmp_path):
    path = tmp_path / "tasks.md"
    path.write_text(BASE, encoding="utf-8")
    os.link(path, tmp_path / "other.md")
    result = call(path, "state", "--task", "T-01", "--state", "completado")
    assert result.returncode == 2
    assert path.read_text(encoding="utf-8") == BASE
    assert not (tmp_path / ".ledger-write").exists()


def test_cooperative_writers_preserve_each_others_red_evidence(tmp_path):
    path = tmp_path / "tasks.md"
    path.write_text(BASE, encoding="utf-8")
    children = [subprocess.Popen([sys.executable, str(SCRIPT), "red", str(path), "--task", "T-02",
                "--test", "case_" + str(i), "--error", "missing", "--date", "2026-10-30", "--json"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE) for i in range(3)]
    try:
        for child in children:
            stdout, stderr = child.communicate(timeout=20)
            assert child.returncode == 0, stdout + stderr
        text = path.read_text(encoding="utf-8")
        assert all(text.count("RED: `case_" + str(i) + "`") == 1 for i in range(3))
        assert lint(text, path) == ([], [])
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=5)


def test_review_counter_cannot_be_reset_or_skipped_for_the_same_tasks(tmp_path):
    path = tmp_path / "tasks.md"
    path.write_text(BASE, encoding="utf-8")
    for attempt in (1, 2, 3):
        result = call(path, "review", "--attempt", str(attempt), "--tasks", "T-01,T-02", "--summary", "Fixture")
        assert result.returncode == 0, result.stdout + result.stderr
    before = path.read_bytes()
    for attempt in (1, 2, 4):
        result = call(path, "review", "--attempt", str(attempt), "--tasks", "T-01", "--summary", "Reset attempt")
        assert result.returncode != 0
        assert path.read_bytes() == before


def test_completion_requires_at_least_one_explicit_checked_criterion(tmp_path):
    path = tmp_path / "tasks.md"
    raw = BASE.replace("- [x] First verified criterion.\n", "").encode()
    path.write_bytes(raw)
    result = call(path, "state", "--task", "T-01", "--state", "completado")
    assert result.returncode == 1
    assert path.read_bytes() == raw


def test_idempotent_state_does_not_reformat_existing_summary_spacing(tmp_path):
    path = tmp_path / "tasks.md"
    raw = BASE.replace("| Fase 1 — Fixture | 0 | 2 | 0.0% |", "| Fase 1 — Fixture |   0   |  2  |  0%  |").encode()
    path.write_bytes(raw)
    result = call(path, "state", "--task", "T-01", "--state", "en-progreso")
    assert result.returncode == 0
    assert json.loads(result.stdout)["changed"] is False
    assert path.read_bytes() == raw


def test_lock_metadata_ignores_itself_and_preserves_an_existing_ignore_file(tmp_path):
    path = tmp_path / "tasks.md"
    path.write_text(BASE, encoding="utf-8")
    result = call(path, "state", "--task", "T-01", "--state", "completado")
    assert result.returncode == 0
    state = tmp_path / ".ledger-write"
    assert (state / ".lock").is_file()
    assert (state / ".gitignore").read_text(encoding="utf-8") == "*\n"
    (state / ".gitignore").write_text("# consumer policy\n", encoding="utf-8")
    assert call(path, "state", "--task", "T-01", "--state", "en-progreso").returncode == 0
    assert (state / ".gitignore").read_text(encoding="utf-8") == "# consumer policy\n"


@pytest.mark.skipif(os.name == "nt", reason="POSIX permission bits")
def test_atomic_publication_preserves_existing_file_permissions(tmp_path):
    import stat
    path = tmp_path / "tasks.md"
    path.write_text(BASE, encoding="utf-8")
    path.chmod(0o640)
    assert call(path, "state", "--task", "T-01", "--state", "completado").returncode == 0
    assert stat.S_IMODE(path.stat().st_mode) == 0o640


def test_uncooperative_edit_before_publish_is_preserved(tmp_path, monkeypatch, capsys):
    spec = importlib.util.spec_from_file_location("writer_race_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    path = tmp_path / "tasks.md"
    path.write_text(BASE, encoding="utf-8")
    external = BASE + "\nConsumer edit after the prepared snapshot.\n"
    publish = module.IO.write

    def changed(*args, **kwargs):
        path.write_text(external, encoding="utf-8")
        return publish(*args, **kwargs)

    monkeypatch.setattr(module.IO, "write", changed)
    code = module.main(["state", str(path), "--task", "T-01", "--state", "completado", "--json"])
    assert code != 0, capsys.readouterr().out
    assert path.read_text(encoding="utf-8") == external
    assert not list(tmp_path.glob(".tmp-*"))


def test_atomic_publish_failure_keeps_original_and_cleans_its_temporary(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("writer_publish_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    path = tmp_path / "tasks.md"
    path.write_text(BASE, encoding="utf-8")

    def fail(*args):
        raise OSError("fixture publication rejected")

    monkeypatch.setattr(module.STATE.os, "replace", fail)
    assert module.main(["state", str(path), "--task", "T-01", "--state", "completado", "--json"]) == 2
    assert path.read_text(encoding="utf-8") == BASE
    assert not list(tmp_path.glob(".tmp-*"))


def test_redaction_rejects_secret_evidence_without_echoing_it(tmp_path):
    path = tmp_path / "tasks.md"
    path.write_text(BASE, encoding="utf-8")
    secret = "ghp_" + "A" * 36
    result = call(path, "red", "--task", "T-01", "--test", "case", "--error", secret, "--date", "2026-10-30")
    assert result.returncode == 2
    assert secret not in result.stdout + result.stderr
    assert path.read_text(encoding="utf-8") == BASE


def test_symbolic_parent_is_rejected(tmp_path):
    owned, link = tmp_path / "owned", tmp_path / "linked"
    owned.mkdir()
    path = owned / "tasks.md"
    path.write_text(BASE, encoding="utf-8")
    try:
        link.symlink_to(owned, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks unavailable")
    result = call(link / "tasks.md", "state", "--task", "T-01", "--state", "completado")
    assert result.returncode == 2
    assert path.read_text(encoding="utf-8") == BASE
    assert not (owned / ".ledger-write").exists()


def test_explicit_hash_allows_only_one_concurrent_writer(tmp_path):
    path = tmp_path / "tasks.md"
    path.write_text(BASE, encoding="utf-8")
    expected = hashlib.sha256(path.read_bytes()).hexdigest()
    children = [subprocess.Popen([sys.executable, str(SCRIPT), "red", str(path), "--task", "T-02",
                "--test", "case_" + str(i), "--error", "missing", "--date", "2026-10-30",
                "--expected-sha256", expected, "--json"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                for i in range(2)]
    try:
        for child in children:
            child.communicate(timeout=20)
        assert sorted(child.returncode for child in children) == [0, 3]
        assert path.read_text(encoding="utf-8").count("RED:") == 1
    finally:
        for child in children:
            if child.poll() is None:
                child.kill()
            child.wait(timeout=5)


def test_state_preserves_an_unrelated_phases_summary_bytes(tmp_path):
    path = tmp_path / "tasks.md"
    row = "| Fase 2 — Other |   0   |  1  |  0%  |\n"
    text = BASE.replace("| **TOTAL**", row + "| **TOTAL**", 1)
    text += "\n## Fase 2 — Other\n\n### T-03 — Other\n\n- **Estado**: borrador\n- **Changelog**: Other.\n- **Verificación**: check\n\n**Criterios de aceptación**\n- [ ] Pending.\n"
    path.write_text(text, encoding="utf-8")
    result = call(path, "state", "--task", "T-01", "--state", "completado")
    assert result.returncode == 0, result.stdout
    assert row in path.read_text(encoding="utf-8")
