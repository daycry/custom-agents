"""Contrato B23: persistencia real de propuestas y decisiones, sin juicio semántico.

Todos los corpus son fixtures tmp_path. No ejecuta CLIs, red, modelos ni Git.
El loader es lazy: la ausencia del servicio falla como capacidad ausente, sin
romper colección ni sustituir el baseline por un writer ficticio.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import threading

import pytest


HERE = Path(__file__).resolve().parent
SERVICE = HERE / "knowledge-curation.py"
GATE = HERE.parent / "knowledge-curator" / "curator-gate.py"
PENDING = "docs/knowledge/candidates/pending"
APPROVED = "docs/knowledge/approved/gotchas"
TEXT = """---
category: GOTCHA
evidencia: validated_case
fuentes: [docs/evidence.md]
tags: [area:testing]
---

# Evidencia concreta
El caso reproducible conserva su referencia.
"""
META = {"id": "ca.gotcha.sample", "category": "GOTCHA", "version": 1, "estado": "aprobado"}


def _load(path, name):
    assert path.is_file(), f"capacidad de persistencia compartida ausente: {path.name}"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def service():
    return _load(SERVICE, "knowledge_curation_contract_test")


@pytest.fixture
def root(tmp_path):
    project = tmp_path / "project"
    config = project / ".claude/knowledge-services"
    config.mkdir(parents=True)
    tax = {"version": 1, "id_prefix": "ca", "categories": [
        {"key": "GOTCHA", "folder": "gotchas", "min_evidence": "validated_case"}],
        "denylist": ["chain-of-thought"]}
    (config / "taxonomy.json").write_text(json.dumps(tax), encoding="utf-8")
    return project


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _tree(root):
    return {p.relative_to(root).as_posix(): p.read_bytes()
            for p in root.rglob("*") if p.is_file()}


def _result(returned, code=None):
    result, actual = returned
    assert isinstance(result, dict) and isinstance(result.get("status"), str)
    assert isinstance(result.get("errores"), list) and isinstance(result.get("avisos"), list)
    assert actual in (0, 1, 2)
    if code is not None:
        assert actual == code, result
    if actual == 0:
        assert result["errores"] == [], result
    else:
        assert result["errores"] or result["avisos"], result
    return result, actual


def _propose(service, root, name="sample.md", text=TEXT):
    result, _ = _result(service.propose(str(root), name, text, producer="documenter"), 0)
    expected = f"{PENDING}/{name}"
    assert result["ruta"] == expected
    assert result["sha256"] == _sha((root / expected).read_bytes())
    return expected, result["sha256"]


def _apply(service, root, candidate, sha, decision="approve", metadata=None,
           reason="Evidencia examinada.", replacement_text=None):
    return service.apply_decision(str(root), candidate, decision, expected_sha256=sha,
                                  metadata=dict(META) if metadata is None else metadata,
                                  reason=reason, decider="knowledge-curator", replacement_text=replacement_text)


def _approved(root, name="sample.md"):
    return root / APPROVED / name


@pytest.mark.parametrize("record_folder", ["operations", "receipts"])
def test_review_b23_b1_recovers_record_link_before_staging_cleanup(service, root, monkeypatch, record_folder):
    candidate, digest = _propose(service, root)
    policy_before = (root / ".claude/knowledge-services/taxonomy.json").read_bytes()
    real_link = service.os.link
    interrupted = []

    def link_then_interrupt(source, target, **kwargs):
        real_link(source, target, **kwargs)
        relative = Path(target).relative_to(root).as_posix()
        record_base = service.OPERATIONS if record_folder == "operations" else service.RECEIPTS
        if relative.startswith(record_base + "/") and relative.endswith(".json"):
            interrupted.append((Path(source), Path(target)))
            raise OSError("synthetic interruption after record publication")

    monkeypatch.setattr(service.os, "link", link_then_interrupt)
    result, code = _result(_apply(service, root, candidate, digest))
    assert code != 0 and len(interrupted) == 1
    staged, published = interrupted[0]
    assert staged.read_bytes() == published.read_bytes()
    assert published.stat().st_nlink == 2
    assert result["operation_id"] == published.stem
    if record_folder == "operations":
        assert (root / candidate).exists() and not _approved(root).exists()
    else:
        assert not (root / candidate).exists() and _approved(root).exists()
    monkeypatch.setattr(service.os, "link", real_link)
    recovered, _ = _result(service.recover(str(root), result["operation_id"]), 0)
    assert recovered["status"] == "complete"
    assert not staged.exists() and published.stat().st_nlink == 1
    assert not (root / candidate).exists()
    assert _sha(_approved(root).read_bytes()) == recovered["sha256"]
    stable = _tree(root)
    assert _result(service.recover(str(root), result["operation_id"]), 0)[0] == recovered
    assert _tree(root) == stable
    assert (root / ".claude/knowledge-services/taxonomy.json").read_bytes() == policy_before


@pytest.mark.parametrize("record_folder", ["operations", "receipts"])
def test_review_b23_b1_does_not_adopt_foreign_record_hardlink(service, root, record_folder):
    candidate, digest = _propose(service, root)
    applied, _ = _result(_apply(service, root, candidate, digest), 0)
    directory = root / (service.OPERATIONS if record_folder == "operations" else service.RECEIPTS)
    records = list(directory.rglob(applied["operation_id"] + ".json"))
    assert len(records) == 1
    record = records[0]
    foreign = root / ("foreign-" + record_folder + ".json")
    os.link(record, foreign)
    before = _tree(root)
    result, code = _result(service.recover(str(root), applied["operation_id"]))
    assert code != 0 and _tree(root) == before, result
    assert foreign.exists() and record.stat().st_nlink == 2


def test_review_d23_d1_apply_does_not_reload_unrelated_completed_history(service, root, monkeypatch):
    operations = []
    text = TEXT + "\n" + "Historical evidence. " * 3200
    for number in range(4):
        candidate, digest = _propose(service, root, f"history-{number}.md", text=text)
        result, _ = _result(_apply(service, root, candidate, digest, decision="reject"), 0)
        operations.append(result["operation_id"])
    history = _tree(root)
    candidate, digest = _propose(service, root, "next.md")
    real_read = service._read
    unrelated_reads = []

    def measured_read(project, relative, *args, **kwargs):
        if relative.startswith(service.OPERATIONS + "/") and Path(relative).stem in operations:
            unrelated_reads.append(relative)
        return real_read(project, relative, *args, **kwargs)

    monkeypatch.setattr(service, "_read", measured_read)
    _result(_apply(service, root, candidate, digest), 0)
    assert unrelated_reads == [], "new decisions must not read historical payloads of other candidates"
    for relative, raw in history.items():
        assert (root / relative).read_bytes() == raw
    for operation_id in operations:
        stable = _tree(root)
        _result(service.recover(str(root), operation_id), 0)
        assert _tree(root) == stable


@pytest.mark.parametrize("duplicate", [False, True])
def test_review_d23_d1_recovery_rejects_misplaced_or_duplicate_intent(service, root, duplicate):
    candidate, digest = _propose(service, root)
    result, _ = _result(_apply(service, root, candidate, digest), 0)
    operation_id = result["operation_id"]
    records = list((root / service.OPERATIONS).rglob(operation_id + ".json"))
    assert len(records) == 1
    record = records[0]
    wrong_directory = root / service.OPERATIONS / ("0" * 64)
    wrong_directory.mkdir()
    wrong = wrong_directory / record.name
    if duplicate:
        wrong.write_bytes(record.read_bytes())
    else:
        record.rename(wrong)
    before = _tree(root)
    result, code = _result(service.recover(str(root), operation_id))
    assert code != 0 and _tree(root) == before, result


@pytest.mark.parametrize("field,expected_status", [("category", "invalid_category"), ("id", "invalid_final_id")])
def test_review_b23_b4_invalid_metadata_diagnostics_redact_secrets(service, root, field, expected_status):
    candidate, digest = _propose(service, root)
    secret = "ghp_a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8s9T0"
    metadata = dict(META, **{field: secret})
    before = _tree(root)
    result, code = _result(_apply(service, root, candidate, digest, metadata=metadata), 1)
    assert result["status"] == expected_status and code == 1
    assert secret not in json.dumps(result, ensure_ascii=False)
    assert "[secreto redactado]" in json.dumps(result, ensure_ascii=False)
    assert _tree(root) == before


@pytest.mark.parametrize("state", ["pending", "needs_changes", "rejected", "approved"])
def test_review_b23_b3_comparison_aliases_reserve_legacy_names(service, root, state):
    legacy = "caso-" + "a" * 138 + "-0123456789.md"
    directory = root / (APPROVED if state == "approved" else "docs/knowledge/candidates/" + state)
    directory.mkdir(parents=True)
    (directory / legacy.upper()).write_text(TEXT, encoding="utf-8")
    before = _tree(root)
    result, code = _result(service.propose(str(root), "compact.md", TEXT, producer="documenter", reserved_aliases=[legacy]))
    assert code != 0 and result["status"] == "name_already_reserved", result
    assert _tree(root) == before


def test_review_b23_b3_comparison_alias_is_not_a_destination(service, root):
    legacy = "caso-" + "a" * 138 + "-0123456789.md"
    result, _ = _result(service.propose(str(root), "compact.md", TEXT, producer="documenter", reserved_aliases=(legacy,)), 0)
    assert result["ruta"] == PENDING + "/compact.md"
    assert not any(path.name == legacy for path in root.rglob("*"))


@pytest.mark.parametrize("aliases", ["single.md", ["../escape.md"], ["CON.md"], ["a" * 253 + ".md"], ["valid.md"] * 9])
def test_review_b23_b3_invalid_comparison_aliases_have_no_effect(service, root, aliases):
    before = _tree(root)
    result, code = _result(service.propose(str(root), "compact.md", TEXT, producer="documenter", reserved_aliases=aliases))
    assert code != 0 and _tree(root) == before, result


def test_propose_materializes_redacted_pending_and_hash_only(service, root):
    secret = "ghp_a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8s9T0"
    text = TEXT.replace("docs/evidence.md", "docs/" + secret + ".md") + "\nToken " + secret
    candidate, digest = _propose(service, root, text=text)
    data = (root / candidate).read_bytes()
    assert secret.encode() not in data and b"[secreto redactado]" in data
    assert digest == _sha(data) and data.decode("utf-8")
    assert b"estado:" not in data
    assert not (root / "docs/knowledge/approved").exists()
    assert {p.name for p in (root / PENDING).iterdir()} == {"sample.md"}


@pytest.mark.parametrize("state", ["aprobado", "propuesta", "pending", ""])
def test_propose_rejects_any_declared_estado(service, root, state):
    before = _tree(root)
    result, code = _result(service.propose(str(root), "sample.md", TEXT.replace(
        "category: GOTCHA", f"category: GOTCHA\nestado: {state}"), producer="implementer"))
    assert code != 0 and _tree(root) == before, result


@pytest.mark.parametrize("name", ["../escape.md", "sub/a.md", "sub\\a.md", "C:evil.md",
                                  "file.md:stream", "CON.md", "NUL.md", "COM1.md", "LPT9.md",
                                  "a..md ", ".", "..", "README.md", "readme.MD",
                                  "résumé.md", "a" * 126 + ".md"])
def test_propose_rejects_nonportable_name_without_writing(service, root, name):
    before = _tree(root)
    result, code = _result(service.propose(str(root), name, TEXT, producer="planner"))
    assert code != 0 and _tree(root) == before, result


def test_propose_size_limit_and_missing_body_have_no_effect(service, root):
    for text in (TEXT + "x" * (256 * 1024), "---\ncategory: GOTCHA\n---\n"):
        before = _tree(root)
        result, code = _result(service.propose(str(root), "sample.md", text, producer="qa"))
        assert code != 0 and _tree(root) == before, result


@pytest.mark.parametrize("producer", ["", " ", None, "../implementer", "qa/../../root",
                                      "ghp_a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8s9T0"])
def test_propose_rejects_invalid_producer_without_persisting_or_echoing_it(service, root, producer):
    before = _tree(root)
    result, code = _result(service.propose(str(root), "sample.md", TEXT, producer=producer))
    assert code != 0 and _tree(root) == before, result
    if producer and producer.startswith("ghp_"):
        assert producer not in json.dumps(result)


@pytest.mark.parametrize("text", [b"\xff\xfe", TEXT + "\ud800"])
def test_propose_rejects_non_utf8_payload_without_creating_candidate(service, root, text):
    before = _tree(root)
    result, code = _result(service.propose(str(root), "sample.md", text, producer="documenter"))
    assert code != 0 and _tree(root) == before, result


@pytest.mark.parametrize("folder", ["candidates/pending", "candidates/needs_changes",
                                    "candidates/rejected", "approved/gotchas"])
def test_propose_name_is_reserved_across_states(service, root, folder):
    occupied = root / "docs/knowledge" / folder / "sample.md"
    occupied.parent.mkdir(parents=True)
    occupied.write_bytes(b"original bytes\n")
    before = _tree(root)
    _, code = _result(service.propose(str(root), "sample.md", TEXT, producer="retro"), 1)
    assert code == 1 and _tree(root) == before


def test_propose_existing_case_variant_does_not_bypass_portable_collision(service, root):
    _propose(service, root, "Sample.md")
    before = _tree(root)
    result, code = _result(service.propose(str(root), "sample.md", TEXT, producer="architect"))
    assert code != 0 and _tree(root) == before, result


def test_apply_requires_exact_original_sha_and_never_deletes_modified_source(service, root):
    candidate, digest = _propose(service, root)
    changed = (root / candidate).read_bytes() + b"\nChanged externally.\n"
    (root / candidate).write_bytes(changed)
    result, code = _result(_apply(service, root, candidate, digest), 1)
    assert (root / candidate).read_bytes() == changed and not _approved(root).exists(), result


@pytest.mark.parametrize("sha", [None, "", "x" * 64, "a" * 63])
def test_apply_requires_well_formed_sha(service, root, sha):
    candidate, _ = _propose(service, root)
    before = (root / candidate).read_bytes()
    result, code = _result(_apply(service, root, candidate, sha))
    assert code != 0 and (root / candidate).read_bytes() == before
    assert not _approved(root).exists(), result


@pytest.mark.parametrize("candidate", ["../outside.md", "docs/knowledge/approved/gotchas/a.md",
                                      "docs/knowledge/candidates/pending/../pending/sample.md",
                                      "docs/knowledge/candidates/pending/sample.md:stream"])
def test_apply_rejects_noncanonical_candidate_paths(service, root, candidate):
    actual, digest = _propose(service, root)
    before = (root / actual).read_bytes()
    result, code = _result(_apply(service, root, candidate, digest))
    assert code != 0 and (root / actual).read_bytes() == before and not _approved(root).exists(), result


@pytest.mark.parametrize("meta", [
    {"category": "GOTCHA", "version": 1},
    dict(META, id="other.gotcha.sample"), dict(META, id="ca.bad/name"),
    dict(META, version=0), dict(META, version=2), dict(META, version=True),
    dict(META, category="NO-EXISTE"), dict(META, estado="accepted"),
])
def test_approve_requires_final_id_prefix_category_and_initial_version(service, root, meta):
    candidate, digest = _propose(service, root)
    before = (root / candidate).read_bytes()
    result, code = _result(_apply(service, root, candidate, digest, metadata=meta))
    assert code != 0 and (root / candidate).read_bytes() == before and not _approved(root).exists(), result


@pytest.mark.parametrize("text", [TEXT.replace("validated_case", "observation"),
                                 TEXT.replace("fuentes: [docs/evidence.md]\n", ""),
                                 TEXT.replace("tags: [area:testing]", "tags: [testing]"),
                                 TEXT + "\nA chain-of-thought account.\n"])
def test_approve_uses_existing_gate_content_rules(service, root, text):
    candidate, digest = _propose(service, root, text=text)
    result, _ = _result(_apply(service, root, candidate, digest), 1)
    assert (root / candidate).exists() and not _approved(root).exists(), result


def test_approve_publishes_complete_frontmatter_and_removes_only_verified_source(service, root):
    candidate, digest = _propose(service, root)
    result, _ = _result(_apply(service, root, candidate, digest), 0)
    assert result["operation_id"]
    assert not (root / candidate).exists()
    body = _approved(root).read_text(encoding="utf-8")
    local = _load(HERE / "knowledge-local.py", "curation_local_test")
    fm = local._frontmatter(body)
    for key, value in META.items():
        assert str(fm[key]) == str(value)
    assert fm["fuentes"] == ["docs/evidence.md"] and fm["tags"] == ["area:testing"]
    assert "El caso reproducible conserva su referencia." in body
    index, errors = local.build_index(str(root))
    assert errors == [] and index["ca.gotcha.sample"]["version"] == 1


def test_approve_rejects_id_collision_even_with_different_filename(service, root):
    first, digest = _propose(service, root, "first.md")
    _result(_apply(service, root, first, digest), 0)
    preserved = _approved(root, "first.md").read_bytes()
    second, digest = _propose(service, root, "second.md")
    result, _ = _result(_apply(service, root, second, digest), 1)
    assert _approved(root, "first.md").read_bytes() == preserved
    assert not _approved(root, "second.md").exists() and (root / second).exists(), result


def test_approve_blocks_broken_existing_index(service, root):
    candidate, digest = _propose(service, root)
    bad = _approved(root, "bad.md")
    bad.parent.mkdir(parents=True)
    bad.write_text("---\nid: ca.bad\nestado: aprobado\nversion: 1\n---\nBroken category", encoding="utf-8")
    before = bad.read_bytes()
    result, code = _result(_apply(service, root, candidate, digest))
    assert code != 0 and bad.read_bytes() == before
    assert (root / candidate).exists() and not _approved(root).exists(), result


def test_destination_created_after_proposal_is_never_overwritten(service, root):
    candidate, digest = _propose(service, root)
    target = _approved(root)
    target.parent.mkdir(parents=True)
    target.write_bytes(b"foreign destination\n")
    result, code = _result(_apply(service, root, candidate, digest))
    assert code != 0 and target.read_bytes() == b"foreign destination\n" and (root / candidate).exists(), result


@pytest.mark.parametrize("decision, folder", [("reject", "rejected"), ("needs_changes", "needs_changes")])
def test_nonapproval_preserves_original_bytes_and_redacted_reason(service, root, decision, folder):
    candidate, digest = _propose(service, root, text=TEXT.replace("evidencia: validated_case\n", ""))
    source = (root / candidate).read_bytes()
    secret = "ghp_a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8s9T0"
    result, _ = _result(_apply(service, root, candidate, digest, decision=decision,
                               metadata={}, reason="Falta evidencia. Token " + secret), 0)
    target = root / f"docs/knowledge/candidates/{folder}/sample.md"
    assert target.read_bytes() == source and not (root / candidate).exists()
    assert not _approved(root).exists() and result["operation_id"]
    all_bytes = b"\n".join(_tree(root).values())
    assert secret.encode() not in all_bytes and b"Falta evidencia." in all_bytes


def test_rejected_is_terminal_and_repeat_reject_is_idempotent(service, root):
    candidate, digest = _propose(service, root)
    _result(_apply(service, root, candidate, digest, decision="reject", metadata={}), 0)
    rejected = "docs/knowledge/candidates/rejected/sample.md"
    preserved = (root / rejected).read_bytes()
    for decision in ("approve", "needs_changes"):
        result, code = _result(_apply(service, root, rejected, _sha(preserved), decision=decision))
        assert code != 0 and (root / rejected).read_bytes() == preserved, result
    _result(_apply(service, root, rejected, _sha(preserved), decision="reject", metadata={}), 0)
    assert (root / rejected).read_bytes() == preserved and not _approved(root).exists()


def test_needs_changes_can_approve_corrected_representation_without_raw_edit(service, root):
    incomplete = TEXT.replace("evidencia: validated_case\n", "")
    candidate, digest = _propose(service, root, text=incomplete)
    original = (root / candidate).read_bytes()
    _result(_apply(service, root, candidate, digest, decision="needs_changes", metadata={}), 0)
    candidate = "docs/knowledge/candidates/needs_changes/sample.md"
    assert (root / candidate).read_bytes() == original
    secret = "ghp_a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8s9T0"
    result, _ = _result(_apply(service, root, candidate, digest, metadata=dict(META, source="Token " + secret),
        replacement_text=TEXT + "\nCorrected token " + secret), 0)
    body = _approved(root).read_bytes()
    assert secret.encode() not in body and b"[secreto redactado]" in body
    assert b"evidencia: validated_case" in body and b"estado: aprobado" in body
    assert not (root / candidate).exists() and result["operation_id"]


def test_corrected_representation_still_requires_original_sha(service, root):
    candidate, digest = _propose(service, root, text=TEXT.replace("evidencia: validated_case\n", ""))
    original = (root / candidate).read_bytes()
    replacement_digest = _sha(TEXT.encode("utf-8"))
    assert replacement_digest != digest
    result, code = _result(_apply(service, root, candidate, replacement_digest, replacement_text=TEXT), 1)
    assert (root / candidate).read_bytes() == original and not _approved(root).exists(), result


@pytest.mark.parametrize("decision", ["reject", "needs_changes"])
def test_replacement_text_is_only_valid_for_approve(service, root, decision):
    candidate, digest = _propose(service, root)
    original = (root / candidate).read_bytes()
    result, code = _result(_apply(service, root, candidate, digest, decision=decision,
                                 metadata={}, replacement_text=TEXT + "\nDifferent body."))
    assert code != 0 and (root / candidate).read_bytes() == original
    assert not (root / f"docs/knowledge/candidates/{decision}/sample.md").exists(), result


@pytest.mark.parametrize("reason", ["", "   ", None])
def test_decision_requires_a_reason(service, root, reason):
    candidate, digest = _propose(service, root)
    source = (root / candidate).read_bytes()
    result, code = _result(_apply(service, root, candidate, digest, reason=reason))
    assert code != 0 and (root / candidate).read_bytes() == source and not _approved(root).exists(), result


def test_only_declared_curator_role_can_apply_or_recover(service, root):
    candidate, digest = _propose(service, root)
    source = (root / candidate).read_bytes()
    result, code = _result(service.apply_decision(str(root), candidate, "approve", expected_sha256=digest,
        metadata=dict(META), reason="Reviewed.", decider="qa"))
    assert code != 0 and (root / candidate).read_bytes() == source and not _approved(root).exists(), result
    result, code = _result(service.recover(str(root), "not-an-operation", decider="implementer"))
    assert code != 0 and (root / candidate).read_bytes() == source, result


def _cut(service, monkeypatch, stage):
    captured = []

    def checkpoint(actual, operation):
        if actual == stage:
            assert isinstance(operation, dict) and operation["operation_id"]
            captured.append(operation["operation_id"])
            raise OSError("fixture interruption")

    monkeypatch.setattr(service, "_checkpoint", checkpoint)
    return captured


@pytest.mark.parametrize("stage", ["prepared", "published", "source_removed"])
def test_interrupted_approval_recovers_idempotently(service, root, monkeypatch, stage):
    candidate, digest = _propose(service, root)
    source = (root / candidate).read_bytes()
    captured = _cut(service, monkeypatch, stage)
    result, _ = _result(_apply(service, root, candidate, digest), 2)
    assert captured == [result["operation_id"]]
    assert (root / candidate).exists() == (stage != "source_removed")
    assert _approved(root).exists() == (stage != "prepared")
    if (root / candidate).exists():
        assert (root / candidate).read_bytes() == source
    monkeypatch.setattr(service, "_checkpoint", lambda *_: None)
    recovered, _ = _result(service.recover(str(root), result["operation_id"], decider="knowledge-curator"), 0)
    assert recovered["operation_id"] == result["operation_id"]
    assert _approved(root).is_file() and not (root / candidate).exists()
    final = _tree(root)
    _result(service.recover(str(root), result["operation_id"], decider="knowledge-curator"), 0)
    assert _tree(root) == final


@pytest.mark.parametrize("stage", ["prepared", "published"])
def test_recovery_conserves_externally_changed_source(service, root, monkeypatch, stage):
    candidate, digest = _propose(service, root)
    _cut(service, monkeypatch, stage)
    operation, _ = _result(_apply(service, root, candidate, digest), 2)
    changed = (root / candidate).read_bytes() + b"\nexternal edit\n"
    (root / candidate).write_bytes(changed)
    monkeypatch.setattr(service, "_checkpoint", lambda *_: None)
    result, code = _result(service.recover(str(root), operation["operation_id"], decider="knowledge-curator"))
    assert code != 0 and (root / candidate).read_bytes() == changed, result
    assert _approved(root).exists() == (stage == "published")


def test_recovery_before_publication_blocks_changed_policy(service, root, monkeypatch):
    candidate, digest = _propose(service, root)
    _cut(service, monkeypatch, "prepared")
    operation, _ = _result(_apply(service, root, candidate, digest), 2)
    taxpath = root / ".claude/knowledge-services/taxonomy.json"
    tax = json.loads(taxpath.read_text(encoding="utf-8"))
    tax["categories"][0]["min_evidence"] = "multiple_validated_cases"
    taxpath.write_text(json.dumps(tax), encoding="utf-8")
    monkeypatch.setattr(service, "_checkpoint", lambda *_: None)
    result, code = _result(service.recover(str(root), operation["operation_id"], decider="knowledge-curator"))
    assert code != 0 and (root / candidate).exists() and not _approved(root).exists(), result


def test_recovery_does_not_adopt_foreign_destination(service, root, monkeypatch):
    candidate, digest = _propose(service, root)
    _cut(service, monkeypatch, "prepared")
    operation, _ = _result(_apply(service, root, candidate, digest), 2)
    target = _approved(root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"foreign bytes after preparation")
    monkeypatch.setattr(service, "_checkpoint", lambda *_: None)
    result, code = _result(service.recover(str(root), operation["operation_id"], decider="knowledge-curator"))
    assert code != 0 and target.read_bytes() == b"foreign bytes after preparation"
    assert (root / candidate).exists(), result


def test_recovery_does_not_adopt_modified_published_destination(service, root, monkeypatch):
    candidate, digest = _propose(service, root)
    _cut(service, monkeypatch, "published")
    operation, _ = _result(_apply(service, root, candidate, digest), 2)
    target = _approved(root)
    changed = target.read_bytes() + b"\nforeign edit after publish\n"
    target.write_bytes(changed)
    monkeypatch.setattr(service, "_checkpoint", lambda *_: None)
    result, code = _result(service.recover(str(root), operation["operation_id"], decider="knowledge-curator"))
    assert code != 0 and target.read_bytes() == changed and (root / candidate).exists(), result


def test_cooperating_writer_is_rejected_while_apply_holds_lock(service, root, monkeypatch):
    candidate, digest = _propose(service, root)
    reached, release = threading.Event(), threading.Event()
    outputs = []

    def checkpoint(stage, operation):
        if stage == "prepared":
            reached.set()
            assert release.wait(5), "fixture release timeout"

    def apply_worker():
        try:
            outputs.append(_apply(service, root, candidate, digest))
        except BaseException as exc:
            outputs.append(exc)

    monkeypatch.setattr(service, "_checkpoint", checkpoint)
    worker = threading.Thread(target=apply_worker, daemon=True)
    worker.start()
    try:
        assert reached.wait(5), "writer never reached prepared checkpoint"
        result, code = _result(service.propose(str(root), "parallel.md", TEXT, producer="planner"))
        assert code != 0 and not (root / PENDING / "parallel.md").exists(), result
    finally:
        release.set()
        worker.join(5)
    assert not worker.is_alive() and len(outputs) == 1
    assert not isinstance(outputs[0], BaseException), outputs
    _result(outputs[0], 0)
    _propose(service, root, "after.md")


def test_process_lock_excludes_a_separate_python_writer(service, root, monkeypatch):
    candidate, digest = _propose(service, root)
    reached, release = threading.Event(), threading.Event()
    outputs = []

    def checkpoint(stage, operation):
        if stage == "prepared":
            reached.set()
            assert release.wait(15), "fixture release timeout"

    def apply_worker():
        try:
            outputs.append(_apply(service, root, candidate, digest))
        except BaseException as exc:
            outputs.append(exc)

    monkeypatch.setattr(service, "_checkpoint", checkpoint)
    worker = threading.Thread(target=apply_worker, daemon=True)
    worker.start()
    child = """import importlib.util,json,sys
s=importlib.util.spec_from_file_location('curation_lock_child',sys.argv[1])
m=importlib.util.module_from_spec(s);sys.modules[s.name]=m;s.loader.exec_module(m)
r,c=m.propose(sys.argv[2],'parallel.md',sys.argv[3],producer='planner')
print(json.dumps({'result':r,'code':c}))
"""
    try:
        assert reached.wait(5), "writer never reached prepared checkpoint"
        completed = subprocess.run([sys.executable, "-I", "-B", "-c", child, str(SERVICE), str(root), TEXT],
            capture_output=True, encoding="utf-8", timeout=10)
        assert completed.returncode == 0, completed.stderr
        result = json.loads(completed.stdout)
        assert result["code"] != 0 and not (root / PENDING / "parallel.md").exists(), result
    finally:
        release.set()
        worker.join(5)
    assert not worker.is_alive() and len(outputs) == 1 and not isinstance(outputs[0], BaseException), outputs
    _result(outputs[0], 0)


def test_apply_preserves_all_legacy_and_journal_bytes(service, root):
    legacy = {"adr/ADR-001-old.md": b"id: ADR-001\nestado: aceptada (validada: usuario, 2020-01-01)\n",
              "gotchas/GOT-001-old.md": b"estado: propuesta\n",
              "lessons/LES-001-old.md": b"estado: obsoleta\n",
              "journal/2020-01-01-demo.md": b"captured_at: 2020-01-01T10:00:00Z\n",
              "README.md": b"legacy manual index\n"}
    for relative, data in legacy.items():
        path = root / "docs/knowledge" / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    candidate, digest = _propose(service, root)
    _result(_apply(service, root, candidate, digest), 0)
    for relative, data in legacy.items():
        assert (root / "docs/knowledge" / relative).read_bytes() == data


def test_gate_remains_read_only_and_does_not_materialize_approved(service, root):
    candidate, _ = _propose(service, root)
    gate = _load(GATE, "curation_existing_gate_test")
    before = _tree(root)
    result, code = gate.evaluar(str(root / candidate), "approve", root=str(root), id_override=META["id"])
    assert code == 0 and result["errores"] == []
    assert _tree(root) == before and not _approved(root).exists()


def _symlink_or_skip(target, link, directory=False):
    try:
        if directory and os.name == "nt":
            import _winapi
            _winapi.CreateJunction(str(target), str(link))
        else:
            os.symlink(target, link, target_is_directory=directory)
    except (OSError, NotImplementedError, AttributeError) as exc:
        pytest.skip(f"fixture OS no admite este enlace: {type(exc).__name__}")


def test_propose_rejects_redirected_pending_without_writing_external(service, root, tmp_path):
    external = tmp_path / "external"
    external.mkdir()
    pending = root / PENDING
    pending.parent.mkdir(parents=True)
    _symlink_or_skip(external, pending, directory=True)
    result, code = _result(service.propose(str(root), "sample.md", TEXT, producer="documenter"))
    assert code != 0 and list(external.iterdir()) == [], result


def test_apply_rejects_symlink_candidate_without_touching_target(service, root, tmp_path):
    external = tmp_path / "external.md"
    external.write_text(TEXT, encoding="utf-8")
    pending = root / PENDING
    pending.mkdir(parents=True)
    _symlink_or_skip(external, pending / "sample.md")
    data = external.read_bytes()
    result, code = _result(_apply(service, root, f"{PENDING}/sample.md", _sha(data)))
    assert code != 0 and external.read_bytes() == data and not _approved(root).exists(), result


def test_apply_rejects_hardlinked_candidate_without_touching_other_name(service, root, tmp_path):
    candidate, digest = _propose(service, root)
    external = tmp_path / "external.md"
    try:
        os.link(root / candidate, external)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"fixture OS no admite hardlink: {type(exc).__name__}")
    data = external.read_bytes()
    result, code = _result(_apply(service, root, candidate, digest))
    assert code != 0 and external.read_bytes() == data and (root / candidate).read_bytes() == data
    assert not _approved(root).exists(), result


def test_apply_rejects_redirected_approved_directory(service, root, tmp_path):
    candidate, digest = _propose(service, root)
    external = tmp_path / "external"
    external.mkdir()
    approved = root / "docs/knowledge/approved"
    _symlink_or_skip(external, approved, directory=True)
    result, code = _result(_apply(service, root, candidate, digest))
    assert code != 0 and list(external.iterdir()) == [] and (root / candidate).exists(), result


def test_propose_rejects_redirected_taxonomy_config(service, root, tmp_path):
    config = root / ".claude/knowledge-services/taxonomy.json"
    external = tmp_path / "external-taxonomy.json"
    external.write_bytes(config.read_bytes())
    config.unlink()
    _symlink_or_skip(external, config)
    before = external.read_bytes()
    result, code = _result(service.propose(str(root), "sample.md", TEXT, producer="documenter"))
    assert code != 0 and external.read_bytes() == before
    assert not (root / PENDING / "sample.md").exists(), result


def test_incomplete_duplicate_scan_fails_closed(service, root, monkeypatch):
    occupied = _approved(root, "occupied.md")
    occupied.parent.mkdir(parents=True)
    occupied.write_bytes(b"existing")
    real_scandir = os.scandir

    def incomplete(path):
        if Path(path) == occupied.parent:
            raise PermissionError("fixture unreadable scan")
        return real_scandir(path)

    monkeypatch.setattr(os, "scandir", incomplete)
    result, code = _result(service.propose(str(root), "new.md", TEXT, producer="retro"))
    assert code != 0 and occupied.read_bytes() == b"existing" and not (root / PENDING / "new.md").exists(), result
