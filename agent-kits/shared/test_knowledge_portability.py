"""Future portability contract: real temporary files and the actual owner.

Preparation only: not collected/imported/executed when authored. No fake writer,
services, CLI children, models or backend calls. Missing owner APIs must fail,
never skip or substitute an implementation. Faults use durable-boundary hooks.
"""
import base64
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest


HERE = Path(__file__).resolve().parent
PENDING = "docs/knowledge/candidates/pending"
IMPORT_BASE = "docs/knowledge/candidates/.curation/import-v1"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def load(path, name):
    assert path.is_file(), f"missing real module: {path.name}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def service():
    return load(HERE / "knowledge-curation.py", "portability_curation_test")


def project(path, prefix):
    config = path / ".claude/knowledge-services"
    config.mkdir(parents=True)
    # Local selection must work with remote routing explicitly disabled.
    tax = {"version": 1, "id_prefix": prefix, "categories": [
        {"key": "GOTCHA", "folder": "gotchas", "min_evidence": "validated_case",
         "routing": {"remote": False}}],
        "backends": {"remote": {"type": "markdown-export", "enabled": False}},
        "denylist": ["chain-of-thought"]}
    (config / "taxonomy.json").write_bytes(canonical(tax))
    (path / "docs/knowledge/journal").mkdir(parents=True)
    (path / "docs/knowledge/journal/neighbor.md").write_bytes(b"journal unchanged\n")
    (path / "docs/knowledge/lessons").mkdir(parents=True)
    (path / "docs/knowledge/lessons/neighbor.md").write_bytes(b"legacy unchanged\n")
    return path


@pytest.fixture
def roots(tmp_path):
    return project(tmp_path / "source", "src"), project(tmp_path / "destination", "dst")


def note(root, key="a", *, area="testing", raw_windows=False):
    text = (f"---\nid: src.gotcha.{key}\nversion: 7\nestado: aprobado\n"
            f"category: GOTCHA\narea: {area}\nevidencia: validated_case\n"
            "fuentes: [docs/evidence.md]\ntags: [area:testing]\n"
            "proposed_by: documenter\n---\n\n# Evidencia\nCaso reproducible: café.\n")
    raw = ("\ufeff" + text.replace("\n", "\r\n")).encode("utf-8") if raw_windows else text.encode("utf-8")
    target = root / f"docs/knowledge/approved/gotchas/{key}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    return f"src.gotcha.{key}", raw


def tree(root):
    # Include empty directories: preflight must not create lock/store infrastructure.
    return {p.relative_to(root).as_posix(): p.read_bytes() if p.is_file() else None
            for p in root.rglob("*")}


def result(returned, code=0):
    payload, actual = returned
    assert isinstance(payload, dict), returned
    assert actual == code, payload
    assert isinstance(payload["errores"], list) and isinstance(payload["avisos"], list)
    if code == 0:
        assert not payload["errores"], payload
    else:
        assert payload["errores"] or payload["avisos"], payload
    return payload


def export(service, source, ids, **kwargs):
    return result(service.export_package(str(source), source_id="source-project",
        ids=ids, out="artifacts/transfer.json", **kwargs))


def transfer(service, roots, keys=("a",)):
    source, destination = roots
    ids = [note(source, key)[0] for key in keys]
    exported = export(service, source, ids)
    raw = (source / exported["ruta"]).read_bytes()
    assert exported["sha256"] == sha(raw)
    package = destination / "transfer.json"
    package.write_bytes(raw)
    return ids, raw


def import_(service, destination, raw, *, check=False):
    return service.import_package(str(destination), destination_id="destination-project",
        package="transfer.json", expected_sha256=sha(raw), check=check)


def row(payload, source_id):
    matches = [entry for entry in payload["entries"] if entry["source_id"] == source_id]
    assert len(matches) == 1, payload
    return matches[0]


def receipt(destination, entry):
    path = entry["import_receipt_path"]
    assert path.startswith(IMPORT_BASE + "/receipts/")
    raw = (destination / path).read_bytes()
    assert sha(raw) == entry["import_receipt_sha256"]
    record = json.loads(raw)
    assert record["kind"] == "import_proposal_receipt"
    assert record["status"] == "proposed"
    assert record["source_id"] == entry["source_id"]
    assert record["candidate_sha256"] == entry["candidate_sha256"]
    return record


def interrupt(monkeypatch, service, stage, source_id):
    observed = []
    original = service._checkpoint

    def hook(current, operation):
        if current == stage and operation["source_id"] == source_id:
            observed.append(dict(operation))
            raise OSError("test interruption at " + stage)
        return original(current, operation)

    monkeypatch.setattr(service, "_checkpoint", hook)
    return observed, original


def test_export_exact_ids_local_scope_and_original_bytes(service, roots):
    source, _ = roots
    selected, original = note(source, "a", raw_windows=True)
    note(source, "b", area="other")
    pending = source / PENDING / "not-approved.md"
    pending.parent.mkdir(parents=True)
    pending.write_bytes(b"not approved\n")
    before = tree(source)
    exported = export(service, source, [selected], scope_category="GOTCHA", scope_area="testing")
    package_raw = (source / exported["ruta"]).read_bytes()
    package = json.loads(package_raw)
    assert package_raw == canonical(package)
    assert package["selection"] == {"ids": [selected], "scope": {"category": "GOTCHA", "area": "testing"}}
    assert len(package["entries"]) == 1
    entry = package["entries"][0]
    assert base64.b64decode(entry["content_base64"], validate=True) == original
    assert entry["raw_sha256"] == sha(original) and entry["bytes"] == len(original)
    assert package["source"]["identity_basis"] == "declared"
    after = tree(source)
    assert all(after[path] == raw for path, raw in before.items())
    assert set(after) - set(before) == {"artifacts", exported["ruta"]}


@pytest.mark.parametrize("selection,area", [(["src.gotcha.missing"], None),
    (["src.gotcha.a", "src.gotcha.a"], None), (["src.gotcha.a"], "other")])
def test_export_selection_failure_has_no_effects(service, roots, selection, area):
    source, _ = roots
    note(source)
    before = tree(source)
    failed = result(service.export_package(str(source), source_id="source-project",
        ids=selection, out="artifacts/transfer.json", scope_area=area), 1)
    assert failed["status"] in {"invalid_selection", "scope_mismatch"}
    assert tree(source) == before


@pytest.mark.parametrize("mutation", ["extra", "bool_schema", "version", "bad_base64",
                                      "bytes", "entry_id", "duplicate_key", "wrong_sha"])
def test_entire_package_is_validated_before_any_write(service, roots, mutation):
    _, raw = transfer(service, roots, ("a", "b"))
    _, destination = roots
    package = json.loads(raw)
    last = package["entries"][-1]
    if mutation == "extra":
        last["unexpected"] = "reject me"
    elif mutation == "bool_schema":
        package["schema_version"] = True
    elif mutation == "version":
        package["schema_version"] = 2
    elif mutation == "bad_base64":
        last["content_base64"] = "!!!"
    elif mutation == "bytes":
        last["bytes"] += 1
    elif mutation == "entry_id":
        last["id"] = "src.gotcha.foreign"
    damaged = canonical(package)
    if mutation == "duplicate_key":
        damaged = damaged.replace(b'"schema_version":1', b'"schema_version":1,"schema_version":1')
        assert damaged != raw
    (destination / "transfer.json").write_bytes(damaged)
    before = tree(destination)
    expected = sha(raw) if mutation == "wrong_sha" else sha(damaged)
    if mutation == "wrong_sha":
        expected = "0" * 64
    failed = result(service.import_package(str(destination), destination_id="destination-project",
        package="transfer.json", expected_sha256=expected), 1)
    assert failed["status"] in {"invalid_package", "package_integrity"}
    assert tree(destination) == before


def test_preview_is_readonly_and_import_needs_a_fresh_curator_decision(service, roots):
    ids, raw = transfer(service, roots)
    _, destination = roots
    before = tree(destination)
    preview = result(import_(service, destination, raw, check=True))
    assert preview["status"] == "checked" and preview["written"] is False
    assert row(preview, ids[0])["import_receipt_path"] is None
    assert tree(destination) == before
    imported = result(import_(service, destination, raw))
    candidate = row(imported, ids[0])
    candidate_raw = (destination / candidate["candidate_path"]).read_bytes()
    assert sha(candidate_raw) == candidate["candidate_sha256"]
    fm = service._module("knowledge-local.py")._frontmatter(candidate_raw.decode("utf-8"))
    assert not {"id", "version", "estado"} & set(fm)
    assert fm["proposed_by"] == "import" and fm["import_source_id"] == ids[0]
    assert fm["import_source_version"] == "7" and fm["import_package_sha256"] == sha(raw)
    assert candidate["destination_id"] is None
    assert receipt(destination, candidate)["status"] == "proposed"
    index, errors = service._module("knowledge-local.py").build_index(root=str(destination))
    assert not errors and index == {}
    gate = load(HERE.parent / "knowledge-curator/curator-gate.py", "portability_gate_test")
    verdict, code = gate.evaluar(str(destination / candidate["candidate_path"]), "approve",
                               root=str(destination), id_override="dst.gotcha.imported")
    assert code == 0 and verdict["errores"] == [], verdict
    applied = result(service.apply_decision(str(destination), candidate["candidate_path"], "approve",
        expected_sha256=candidate["candidate_sha256"], reason="Caso examinado explícitamente.",
        metadata={"id": "dst.gotcha.imported", "version": 1, "category": "GOTCHA", "estado": "aprobado"}))
    assert applied["status"] == "complete"
    approved = (destination / applied["ruta"]).read_bytes()
    final = service._module("knowledge-local.py")._frontmatter(approved.decode("utf-8"))
    assert final["id"] == "dst.gotcha.imported" and str(final["version"]) == "1"


def test_completed_retry_recognizes_own_reservation_before_collision(service, roots):
    ids, raw = transfer(service, roots)
    _, destination = roots
    first = result(import_(service, destination, raw))
    before = tree(destination)
    second = result(import_(service, destination, raw))
    assert second["complete"] is True
    assert row(first, ids[0])["import_receipt_sha256"] == row(second, ids[0])["import_receipt_sha256"]
    assert tree(destination) == before


@pytest.mark.parametrize("stage", ["import_intent_published", "import_candidate_published"])
def test_pending_retry_uses_verified_intent_and_does_not_self_collide(service, roots, monkeypatch, stage):
    ids, raw = transfer(service, roots)
    _, destination = roots
    seen, original = interrupt(monkeypatch, service, stage, ids[0])
    failed = result(import_(service, destination, raw), 2)
    assert failed["status"] == "persistence_pending" and len(seen) == 1
    assert not list((destination / (IMPORT_BASE + "/receipts")).glob("*.json"))
    monkeypatch.setattr(service, "_checkpoint", original)
    retried = result(import_(service, destination, raw))
    candidate = row(retried, ids[0])
    assert candidate["import_operation_id"] == seen[0]["import_operation_id"]
    assert sha((destination / candidate["candidate_path"]).read_bytes()) == candidate["candidate_sha256"]
    receipt(destination, candidate)
    assert len(list((destination / PENDING).glob("*.md"))) == 1


def test_identical_foreign_candidate_is_never_adopted(service, roots):
    _, raw = transfer(service, roots)
    _, destination = roots
    known = result(import_(service, destination, raw))
    candidate = known["entries"][0]
    original = (destination / candidate["candidate_path"]).read_bytes()
    foreign = project(destination.parent / "foreign", "dst")
    (foreign / "transfer.json").write_bytes(raw)
    target = foreign / candidate["candidate_path"]
    target.parent.mkdir(parents=True)
    target.write_bytes(original)
    before = tree(foreign)
    failed = result(import_(service, foreign, raw), 1)
    assert failed["status"] == "reservation_conflict"
    assert tree(foreign) == before


def test_corrupt_receipt_does_not_exempt_a_reservation(service, roots):
    _, raw = transfer(service, roots)
    _, destination = roots
    imported = result(import_(service, destination, raw))
    path = destination / imported["entries"][0]["import_receipt_path"]
    record = json.loads(path.read_bytes())
    record["source_id"] = "src.gotcha.foreign"
    path.write_bytes(canonical(record))
    before = tree(destination)
    failed, code = import_(service, destination, raw)
    assert code != 0 and failed["complete"] is False
    assert tree(destination) == before


def test_staging_without_intent_is_reported_as_unrecoverable_orphan(service, roots, monkeypatch):
    ids, raw = transfer(service, roots)
    _, destination = roots
    seen, original = interrupt(monkeypatch, service, "import_stage_prepared", ids[0])
    failed = result(import_(service, destination, raw), 2)
    assert failed["status"] == "orphan_unrecoverable" and failed["written"] is True
    entry = row(failed, ids[0])
    assert len(seen) == 1 and entry["staging_path"] == seen[0]["staged"]
    orphan = destination / entry["staging_path"]
    assert orphan.is_file() and sha(orphan.read_bytes()) == entry["staging_sha256"]
    assert entry["import_operation_id"] is None and entry["import_receipt_path"] is None
    assert not list((destination / PENDING).glob("*.md"))
    assert not list((destination / IMPORT_BASE).rglob("*.json"))
    before = tree(destination)
    monkeypatch.setattr(service, "_checkpoint", original)
    retry = result(import_(service, destination, raw), 2)
    assert retry["status"] == "unrecoverable_import"
    assert tree(destination) == before


def test_partial_batch_retry_recognizes_completed_and_incomplete_own_entries(service, roots, monkeypatch):
    ids, raw = transfer(service, roots, ("a", "b", "c"))
    _, destination = roots
    seen, original = interrupt(monkeypatch, service, "import_candidate_published", ids[1])
    failed = result(import_(service, destination, raw), 2)
    assert failed["complete"] is False and len(seen) == 1
    first = row(failed, ids[0])
    receipt(destination, first)
    assert row(failed, ids[1])["status"] == "persistence_pending"
    assert row(failed, ids[2])["status"] == "not_started"
    first_before = (destination / first["candidate_path"]).read_bytes()
    first_receipt = (destination / first["import_receipt_path"]).read_bytes()
    monkeypatch.setattr(service, "_checkpoint", original)
    retry = result(import_(service, destination, raw))
    assert retry["complete"] is True and len(list((destination / PENDING).glob("*.md"))) == 3
    assert (destination / first["candidate_path"]).read_bytes() == first_before
    assert (destination / first["import_receipt_path"]).read_bytes() == first_receipt
    for source_id in ids:
        receipt(destination, row(retry, source_id))


def test_import_records_are_not_apply_receipts_and_retry_never_resurrects(service, roots):
    ids, raw = transfer(service, roots)
    _, destination = roots
    imported = result(import_(service, destination, raw))
    entry = row(imported, ids[0])
    before = tree(destination)
    observed = service.inspect_reference(str(destination), entry["candidate_path"], entry["candidate_sha256"])
    assert observed["status"] == "pending" and observed["reason"] == "candidate_observed"
    assert "receipt_path" not in observed and tree(destination) == before
    recovered, code = service.recover(str(destination), entry["import_operation_id"])
    assert code != 0 and recovered["status"] != "complete"
    assert not (destination / service.RECEIPTS / (entry["import_operation_id"] + ".json")).exists()
    rejected = result(service.apply_decision(str(destination), entry["candidate_path"], "reject",
        expected_sha256=entry["candidate_sha256"], reason="Decisión explícita de Curator."))
    assert rejected["status"] == "complete"
    after_rejection = tree(destination)
    retried = result(import_(service, destination, raw))
    assert row(retried, ids[0])["candidate_current"] == "missing_or_moved"
    assert not (destination / entry["candidate_path"]).exists()
    assert tree(destination) == after_rejection
