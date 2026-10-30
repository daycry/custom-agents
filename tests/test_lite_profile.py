"""Lite changes execution cost while retaining every quality gate."""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT / "agent-kits/shared"


def profile_module():
    spec = importlib.util.spec_from_file_location("lite_profile_test", SHARED / "execution-profile.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def config(project, data):
    (project / ".claude").mkdir(exist_ok=True)
    path = project / ".claude/dev.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def test_normal_defaults_and_explicit_lite_effective_flags(tmp_path):
    module = profile_module()
    normal = module.resolve(tmp_path)
    assert normal["perfil"] == "normal" and normal["brief_max_chars"] == 10000
    assert normal["subagentes"] is False and normal["blocked"] is False
    config(tmp_path, {"perfil": "lite", "subagentes": True, "paralelismo": True,
                      "tdd": True, "worktree": True})
    lite = module.resolve(tmp_path)
    assert lite["perfil"] == "lite" and lite["brief_max_chars"] == 6000
    assert lite["subagentes"] is False and lite["paralelismo"] is False
    assert lite["tdd"] is True and lite["worktree"] is True
    assert lite["reviewers"] == "fresh_sequential"
    assert lite["qa_gate"] is True and lite["review_required"] is True
    assert lite["writer_required"] is True and lite["blocked"] is False


@pytest.mark.parametrize("perfil", ["small", "LITE", True, [], None])
def test_invalid_declared_profile_blocks_without_guessing(tmp_path, perfil):
    config(tmp_path, {"perfil": perfil})
    row = profile_module().resolve(tmp_path)
    assert row["blocked"] and row["warnings"]


def test_partial_bundle_blocks_lite_but_preserves_normal_fallback(tmp_path):
    partial = tmp_path / "partial"
    partial.mkdir()
    module = profile_module()
    config(tmp_path, {"perfil": "lite"})
    assert module.resolve(tmp_path, shared_dir=partial)["blocked"]
    config(tmp_path, {"perfil": "normal"})
    normal = module.resolve(tmp_path, shared_dir=partial)
    assert not normal["blocked"] and normal["warnings"]


def brief_fixture(project, payload=""):
    folder = project / "docs/roadmap/fixture"
    folder.mkdir(parents=True)
    (folder / "tasks.md").write_text("""# Tasks
## Fase 1 — Fixture
### T-01 — Implement
- **Estado**: en-progreso
- **Verificación**: python verify.py → exit 0
**Criterios de aceptación**
- [ ] Keep this entire criterion.
""" + payload, encoding="utf-8")
    return folder


def run_brief(folder):
    return subprocess.run([sys.executable, str(SHARED / "task-brief.py"), str(folder), "T-01",
                           "--sin-lint", "--constitucion", str(folder / "absent.md"),
                           "--extensions-project-only"], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=30)


def test_lite_brief_preserves_contract_tdd_and_budget(tmp_path):
    config(tmp_path, {"perfil": "lite", "tdd": True})
    result = run_brief(brief_fixture(tmp_path))
    assert result.returncode == 0, result.stderr
    assert "## Perfil lite" in result.stdout
    assert len(result.stdout) <= 6000
    for value in ("Keep this entire criterion.", "python verify.py", "TDD", "RED:",
                  "DONE_WITH_CONCERNS", "NEEDS_CONTEXT", "BLOCKED", "ledger-write.py", "lite"):
        assert value in result.stdout


def test_lite_overflow_emits_no_partial_dispatch(tmp_path):
    config(tmp_path, {"perfil": "lite"})
    payload = "\n- [ ] " + "Mandatory criterion " * 500 + "END-CRITERION\n"
    result = run_brief(brief_fixture(tmp_path, payload))
    assert result.returncode == 2
    assert result.stdout == ""
    assert "6000" in result.stderr and "lite" in result.stderr


def test_lite_missing_writer_does_not_emit_a_brief(tmp_path):
    folder = brief_fixture(tmp_path)
    config(tmp_path, {"perfil": "lite"})
    bundle = tmp_path / "bundle"
    shutil.copytree(SHARED, bundle, ignore=shutil.ignore_patterns("__pycache__", "test_*"))
    (bundle / "ledger-write.py").unlink()
    result = subprocess.run([sys.executable, str(bundle / "task-brief.py"), str(folder), "T-01",
                             "--sin-lint"], capture_output=True, text=True,
                            encoding="utf-8", errors="replace", timeout=30)
    assert result.returncode == 2 and result.stdout == ""
    assert "writer" in result.stderr.lower()


def test_doctor_recognizes_profile_and_reports_effective_lite(tmp_path):
    spec = importlib.util.spec_from_file_location("lite_doctor_test", SHARED / "doctor.py")
    doctor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(doctor)
    data = {"perfil": "lite", "subagentes": True, "paralelismo": True}
    config(tmp_path, data)
    assert not any(row["estado"] == "aviso" for row in doctor._dev_valida(data))
    rows = doctor._dev(str(ROOT), str(tmp_path))
    row = next(row for row in rows if row.get("perfil") == "lite")
    assert row["subagentes"] is False and row["paralelismo"] is False
    assert row["brief_max_chars"] == 6000 and row["writer_available"] is True
    assert row["reviewers"] == "fresh_sequential" and row["qa_gate"] is True


def test_lite_preserves_full_verification_even_above_normal_section_cap(tmp_path):
    config(tmp_path, {"perfil": "lite"})
    folder = brief_fixture(tmp_path)
    path = folder / "tasks.md"
    command = "python verify.py --case=" + "a" * 1200 + "LAST-ARGUMENT"
    path.write_text(path.read_text(encoding="utf-8").replace("python verify.py", command), encoding="utf-8")
    result = run_brief(folder)
    assert result.returncode == 0, result.stderr
    assert command in result.stdout and len(result.stdout) <= 6000


def test_profile_cli_is_read_only_and_emits_ascii_json(tmp_path):
    config(tmp_path, {"perfil": "lite", "ignored": "\u2603"})
    before = {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    result = subprocess.run([sys.executable, str(SHARED / "execution-profile.py"), "--project", str(tmp_path), "--json"],
                            capture_output=True, timeout=10)
    assert result.returncode == 0 and json.loads(result.stdout)["perfil"] == "lite"
    result.stdout.decode("ascii")
    assert before == {p.relative_to(tmp_path): p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}


def test_normal_can_disable_parallelism_without_disabling_review(tmp_path):
    config(tmp_path, {"perfil": "normal", "paralelismo": False, "subagentes": True})
    row = profile_module().resolve(tmp_path)
    assert row["subagentes"] is True and row["paralelismo"] is False
    assert row["reviewers"] == "fresh_sequential" and row["review_required"] is True


@pytest.mark.parametrize("raw", [b'{broken', b'[]', b'{"a":' * 10000 + b'0' + b'}' * 10000],
                         ids=["syntax", "non-object", "deep"])
def test_bad_json_warns_without_claiming_lite(tmp_path, raw):
    path = config(tmp_path, {})
    path.write_bytes(raw)
    row = profile_module().resolve(tmp_path)
    assert row["perfil"] == "normal" and row["warnings"] and not row["blocked"]


def test_brief_missing_profile_resolver_preserves_only_undeclared_normal_fallback(tmp_path):
    folder = brief_fixture(tmp_path)
    bundle = tmp_path / "bundle"
    shutil.copytree(SHARED, bundle, ignore=shutil.ignore_patterns("__pycache__", "test_*"))
    (bundle / "execution-profile.py").unlink()
    args = [sys.executable, str(bundle / "task-brief.py"), str(folder), "T-01", "--sin-lint",
            "--constitucion", str(folder / "absent.md")]
    normal = subprocess.run(args, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
    assert normal.returncode == 0 and normal.stdout and "fallback" in normal.stderr
    config(tmp_path, {"perfil": "lite"})
    lite = subprocess.run(args, capture_output=True, timeout=30)
    assert lite.returncode == 2 and lite.stdout == b""


def test_lite_keeps_the_entire_project_persona_or_rejects_dispatch(tmp_path):
    config(tmp_path, {"perfil": "lite"})
    folder = brief_fixture(tmp_path)
    path = folder / "tasks.md"
    path.write_text(path.read_text(encoding="utf-8").replace("- **Estado**", "- **Tipo**: backend\n- **Estado**"), encoding="utf-8")
    personas = tmp_path / ".claude/personas"
    personas.mkdir()
    content = "Mandatory domain rule.\n" * 90 + "END-OF-PERSONA"
    (personas / "backend.md").write_text(content, encoding="utf-8")
    result = run_brief(folder)
    assert result.returncode == 0, result.stderr
    assert content in result.stdout and len(result.stdout) <= 6000
    (personas / "backend.md").write_text(content * 4, encoding="utf-8")
    overflow = run_brief(folder)
    assert overflow.returncode == 2 and overflow.stdout == ""


def test_lite_never_truncates_a_long_pending_gap_into_a_small_brief(tmp_path):
    config(tmp_path, {"perfil": "lite"})
    folder = brief_fixture(tmp_path)
    path = folder / "tasks.md"
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n## Revisión de dos lentes — intento 1: Fase 1 (T-01)\n\n"
                     "| # | Grado | Gap | Tarea | Corrección | Evidencia |\n"
                     "|---|---|---|---|---|---|\n"
                     "| 1 | Important | " + "Mandatory gap " * 500 + " | T-01 | pendiente: Fix entirely | fixture |\n")
    result = run_brief(folder)
    assert result.returncode == 2 and result.stdout == ""


def test_doctor_partial_writer_warns_that_lite_dispatch_is_blocked(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("lite_partial_doctor_test", SHARED / "doctor.py")
    doctor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(doctor)
    config(tmp_path, {"perfil": "lite"})
    partial = tmp_path / "partial"
    partial.mkdir()
    for name in ("execution-profile.py", "local-read.py"):
        shutil.copyfile(SHARED / name, partial / name)
    monkeypatch.setattr(doctor, "HERE", str(partial))
    row = next(row for row in doctor._dev(None, str(tmp_path)) if row.get("perfil") == "lite")
    assert row["estado"] == "aviso" and row["blocked"] is True
    assert row["writer_available"] is False and "writer" in row["arreglo"]
