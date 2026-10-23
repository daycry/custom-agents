"""Additional portability oracles, authored but not executed during active QA.

Reuses the initial contract fixtures and actual owner. Size fixtures are valid
notes, not extra JSON fields/padding. CLI children run only when this test is
later explicitly executed, with raw file streams and guaranteed scoped cleanup.
"""
import base64
from contextlib import contextmanager, ExitStack
import errno
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from test_knowledge_portability import (
    HERE, IMPORT_BASE, PENDING, canonical, export, import_, interrupt, note,
    project, receipt, result, roots, row, service, sha, transfer, tree,
)


def packet(service, source, originals, project_id="p"):
    _, policy_sha = service._policy(str(source))
    entries = [{"id": source_id, "version": 7, "category": "GOTCHA",
                "relative_path": "approved/gotchas/" + key + ".md",
                "bytes": len(raw), "raw_sha256": sha(raw),
                "content_base64": base64.b64encode(raw).decode("ascii")}
               for key, source_id, raw in sorted(originals)]
    return {"schema_version": 1, "kind": "approved_knowledge_export",
            "source": {"project_id": project_id, "identity_basis": "declared",
                       "id_prefix": "src", "policy_sha256": policy_sha},
            "selection": {"ids": [entry["id"] for entry in entries],
                          "scope": {"category": None, "area": None}},
            "entries": entries}


def original_note(source, key, body_bytes):
    source_id, base = note(source, key)
    # UTF-8 body content, outside the frontmatter. The body is always nonempty.
    raw = base + b"\nObserved evidence details: " + b"e" * body_bytes + b"\n"
    (source / f"docs/knowledge/approved/gotchas/{key}.md").write_bytes(raw)
    return key, source_id, raw


def exact_package(service, source, target_size):
    fixed = [original_note(source, key, 180_000) for key in ("a", "b", "c")]
    _, base = note(source, "d")
    maximum = service.MAX_BYTES - len(base) - len(b"\nObserved evidence details: \n")
    low, high = 0, maximum
    best = None
    # Base64 grows in four-byte units. A declared source label of length 1..4
    # accounts for the remaining bytes using a real allowed field, not padding.
    while low <= high:
        amount = (low + high) // 2
        last = original_note(source, "d", amount)
        value = packet(service, source, fixed + [last])
        size = len(canonical(value))
        if size <= target_size:
            best = amount, value, size
            low = amount + 1
        else:
            high = amount - 1
    assert best is not None
    amount, value, size = best
    residual = target_size - size
    assert 0 <= residual <= 3, (target_size, size)
    original_note(source, "d", amount)
    value["source"]["project_id"] += "x" * residual
    raw = canonical(value)
    assert len(raw) == target_size
    assert all(entry["bytes"] <= service.MAX_BYTES for entry in value["entries"])
    return value, raw


@pytest.mark.parametrize("extra", [0, 1])
def test_valid_json_package_real_exact_and_plus_one_byte(service, roots, extra):
    source, destination = roots
    assert service.MAX_OPERATION_BYTES == 1024 * 1024
    value, raw = exact_package(service, source, service.MAX_OPERATION_BYTES)
    if extra:
        # A second legitimate declared label gives a valid package exactly +1.
        value["source"]["project_id"] += "y"
        raw = canonical(value)
    assert len(raw) == service.MAX_OPERATION_BYTES + extra
    before_source = tree(source)
    exported, code = service.export_package(str(source), source_id=value["source"]["project_id"],
        ids=value["selection"]["ids"], out="artifacts/boundary.json")
    if extra:
        assert code != 0 and tree(source) == before_source, exported
    else:
        assert code == 0, exported
        assert (source / exported["ruta"]).read_bytes() == raw
    (destination / "transfer.json").write_bytes(raw)
    before_destination = tree(destination)
    imported, code = import_(service, destination, raw)
    if extra:
        assert code != 0 and tree(destination) == before_destination, imported
    else:
        assert code == 0 and imported["complete"] is True, imported
        for entry in imported["entries"]:
            receipt(destination, entry)


def rendered_candidate(service, value, package_raw):
    entry = value["entries"][0]
    original = base64.b64decode(entry["content_base64"], validate=True).decode("utf-8")
    local = service._module("knowledge-local.py")
    fm = local._frontmatter(original)
    body = local._FRONTMATTER_RE.sub("", original, count=1)
    fm = {key: val for key, val in fm.items()
          if key not in {"id", "version", "estado", "proposed_by"} and not key.startswith("import_")}
    fm.update(proposed_by="import", import_source_project=value["source"]["project_id"],
              import_source_id=entry["id"], import_source_version="7",
              import_source_path=entry["relative_path"], import_source_sha256=entry["raw_sha256"],
              import_package_sha256=sha(package_raw),
              import_source_policy_sha256=value["source"]["policy_sha256"],
              import_source_proposed_by="documenter")
    # Reuse the existing canonical renderer; do not install a writer substitute.
    return service._render(fm, body).encode("utf-8")


@pytest.mark.parametrize("extra", [0, 1])
def test_proposal_final_utf8_size_exact_and_plus_one(service, roots, extra):
    source, destination = roots
    assert service.MAX_BYTES == 256 * 1024
    base = original_note(source, "a", 0)
    value = packet(service, source, [base])
    initial = canonical(value)
    base_size = len(rendered_candidate(service, value, initial))
    amount = service.MAX_BYTES - base_size + extra
    assert amount > 0
    original = original_note(source, "a", amount)
    value = packet(service, source, [original])
    raw = canonical(value)
    expected_candidate = rendered_candidate(service, value, raw)
    assert len(expected_candidate) == service.MAX_BYTES + extra
    assert len(original[2]) <= service.MAX_BYTES and len(raw) < service.MAX_OPERATION_BYTES
    (destination / "transfer.json").write_bytes(raw)
    before = tree(destination)
    imported, code = import_(service, destination, raw)
    if extra:
        assert code != 0 and tree(destination) == before, imported
    else:
        assert code == 0, imported
        entry = imported["entries"][0]
        assert (destination / entry["candidate_path"]).read_bytes() == expected_candidate
        assert entry["candidate_sha256"] == sha(expected_candidate)


@pytest.mark.parametrize("extra", [0, 1])
def test_original_raw_markdown_limit_is_independent_of_final_proposal(service, roots, extra):
    source, destination = roots
    source_id, base = note(source)
    # A legitimate older import_* field is preserved in the original package,
    # but replaced by immediate-hop provenance. This leaves the final proposal
    # below its own limit while testing the ORIGINAL raw-byte limit exactly.
    base = base.replace(b"---\n", b"---\nimport_old_hop: " + b"h" * 4000 + b"\n", 1)
    raw_note = base + b"e" * (service.MAX_BYTES + extra - len(base))
    assert len(raw_note) == service.MAX_BYTES + extra
    (source / "docs/knowledge/approved/gotchas/a.md").write_bytes(raw_note)
    value = packet(service, source, [("a", source_id, raw_note)])
    raw = canonical(value)
    assert len(rendered_candidate(service, value, raw)) < service.MAX_BYTES
    before_source = tree(source)
    exported, code = service.export_package(str(source), source_id="p", ids=[source_id],
                                            out="artifacts/original-limit.json")
    if extra:
        assert code != 0 and tree(source) == before_source, exported
    else:
        assert code == 0 and (source / exported["ruta"]).read_bytes() == raw, exported
    (destination / "transfer.json").write_bytes(raw)
    before_destination = tree(destination)
    imported, code = import_(service, destination, raw)
    if extra:
        assert code != 0 and tree(destination) == before_destination, imported
    else:
        assert code == 0, imported
        assert (destination / imported["entries"][0]["candidate_path"]).read_bytes() == rendered_candidate(service, value, raw)


@pytest.mark.parametrize("count", [0, 32, 33])
def test_selection_and_import_entry_count_closed_bounds(service, roots, count):
    source, destination = roots
    originals = [original_note(source, f"s{number:02d}", 0) for number in range(count)]
    ids = [entry[1] for entry in originals]
    before_source = tree(source)
    exported, code = service.export_package(str(source), source_id="p", ids=ids,
                                            out="artifacts/count.json")
    value = packet(service, source, originals)
    raw = canonical(value)
    if count == 32:
        assert code == 0 and len(json.loads((source / exported["ruta"]).read_bytes())["entries"]) == 32
    else:
        assert code != 0 and tree(source) == before_source, exported
    (destination / "transfer.json").write_bytes(raw)
    before_destination = tree(destination)
    imported, code = import_(service, destination, raw)
    if count == 32:
        assert code == 0 and len(imported["entries"]) == 32, imported
        assert len(list((destination / PENDING).glob("*.md"))) == 32
    else:
        assert code != 0 and tree(destination) == before_destination, imported


def test_export_secret_redaction_fails_before_output_without_leaking_diagnostic(service, roots):
    source, _ = roots
    source_id, raw = note(source)
    secret = "ghp_a1B2c3D4e5F6g7H8i9J0k1L2m3N4o5P6q7R8s9T0"
    (source / "docs/knowledge/approved/gotchas/a.md").write_bytes(raw + secret.encode("ascii"))
    before = tree(source)
    failed, code = service.export_package(str(source), source_id="p", ids=[source_id],
                                         out="artifacts/secret.json")
    assert code != 0 and tree(source) == before, failed
    assert secret not in json.dumps(failed, ensure_ascii=False)


@pytest.mark.parametrize("operation,path", [("export", "../escape.json"),
    ("export", "docs/knowledge/export.json"), ("export", "artifacts/existing.json"),
    ("import", "../outside.json")])
def test_paths_and_existing_output_never_write_neighbors(service, roots, operation, path):
    source, destination = roots
    ids, raw = transfer(service, roots)
    existing = source / "artifacts/existing.json"
    existing.write_bytes(b"foreign output must remain\n")
    outside = destination.parent / "outside.json"
    outside.write_bytes(raw)
    before_source, before_destination = tree(source), tree(destination)
    if operation == "export":
        failed, code = service.export_package(str(source), source_id="p", ids=ids, out=path)
    else:
        failed, code = service.import_package(str(destination), destination_id="destination-project",
                                             package=path, expected_sha256=sha(raw))
    assert code != 0, failed
    assert tree(source) == before_source and tree(destination) == before_destination
    assert outside.read_bytes() == raw and existing.read_bytes() == b"foreign output must remain\n"
    assert not (source.parent / "escape.json").exists()


@pytest.mark.parametrize("state", ["pending", "needs_changes", "rejected", "approved"])
def test_casefold_import_name_reserved_across_all_states(service, roots, state):
    source, destination = roots
    ids, raw = transfer(service, roots)
    filename = "import-" + sha(canonical(["source-project", ids[0]])) + ".md"
    parent = destination / ("docs/knowledge/approved/gotchas" if state == "approved"
                            else "docs/knowledge/candidates/" + state)
    parent.mkdir(parents=True)
    occupant = parent / filename.upper()
    original = (source / "docs/knowledge/approved/gotchas/a.md").read_bytes()
    occupant.write_bytes(original.replace(b"src.gotcha.a", b"dst.gotcha.neighbor"))
    before = tree(destination)
    failed, code = import_(service, destination, raw)
    assert code != 0 and tree(destination) == before, failed
    assert occupant.is_file()


def link_or_skip(kind, target, link):
    try:
        if kind == "hard":
            os.link(target, link)
        else:
            os.symlink(target, link)
    except (NotImplementedError, AttributeError) as exc:
        pytest.skip(f"actual OWN fixture link capability absent: {type(exc).__name__}")
    except OSError as exc:
        unsupported = {errno.ENOSYS, errno.EPERM, errno.EACCES, errno.EOPNOTSUPP, errno.ENOTSUP}
        if exc.errno in unsupported or getattr(exc, "winerror", None) == 1314:
            pytest.skip(f"actual OWN fixture {kind} link denied/unsupported: errno={exc.errno}")
        raise


@pytest.mark.parametrize("kind", ["hard", "symbolic"])
@pytest.mark.parametrize("operation", ["export", "import"])
def test_physical_links_are_rejected_without_touching_target(service, roots, kind, operation):
    source, destination = roots
    ids, raw = transfer(service, roots)
    target = (source / "docs/knowledge/approved/gotchas/a.md" if operation == "export"
              else destination / "transfer.json")
    external = destination.parent / (operation + "-link-original.bin")
    external.write_bytes(target.read_bytes())
    target.unlink()
    link_or_skip(kind, external, target)
    original = external.read_bytes()
    before_source, before_destination = tree(source), tree(destination)
    if operation == "export":
        failed, code = service.export_package(str(source), source_id="p", ids=ids,
                                             out="artifacts/linked.json")
    else:
        failed, code = import_(service, destination, raw)
    assert code != 0, failed
    assert external.read_bytes() == original and target.read_bytes() == original
    assert tree(source) == before_source and tree(destination) == before_destination


def test_policy_drift_between_preflight_and_lock_prevents_publication(service, roots, monkeypatch):
    _, destination = roots
    _, raw = transfer(service, roots)
    config = destination / ".claude/knowledge-services/taxonomy.json"
    updated = json.loads(config.read_bytes())
    updated["denylist"].append("another-local-rule")
    changed_raw = canonical(updated)
    before = tree(destination)
    actual_lock = service._locked
    entered = []

    @contextmanager
    def drift(root):
        entered.append(True)
        config.write_bytes(changed_raw)
        with actual_lock(root):
            yield

    monkeypatch.setattr(service, "_locked", drift)
    failed, code = import_(service, destination, raw)
    assert code != 0 and entered == [True], failed
    after = tree(destination)
    # Only the intentional policy change and existing lock infrastructure may remain.
    assert after[".claude/knowledge-services/taxonomy.json"] == changed_raw
    for path, content in before.items():
        if path != ".claude/knowledge-services/taxonomy.json":
            assert after[path] == content
    assert set(after) - set(before) <= {"docs/knowledge/candidates", "docs/knowledge/candidates/.curation-lock"}


def test_policy_drift_invalidates_unfinished_intent_without_adoption(service, roots, monkeypatch):
    ids, raw = transfer(service, roots)
    _, destination = roots
    seen, original = interrupt(monkeypatch, service, "import_candidate_published", ids[0])
    result(import_(service, destination, raw), 2)
    assert len(seen) == 1
    config = destination / ".claude/knowledge-services/taxonomy.json"
    changed = json.loads(config.read_bytes())
    changed["denylist"].append("another-local-rule")
    config.write_bytes(canonical(changed))
    before = tree(destination)
    monkeypatch.setattr(service, "_checkpoint", original)
    failed, code = import_(service, destination, raw)
    assert code != 0 and tree(destination) == before, failed


@pytest.mark.parametrize("when", ["before_link", "after_link"])
def test_receipt_publication_failure_reports_real_effects_and_retry(service, roots, monkeypatch, when):
    ids, raw = transfer(service, roots)
    _, destination = roots
    actual_link = service.os.link
    attempts = []

    def fault(source, target, **kwargs):
        relative = Path(target).relative_to(destination).as_posix()
        if relative.startswith(IMPORT_BASE + "/receipts/") and relative.endswith(".json"):
            attempts.append((Path(source), Path(target)))
            if when == "after_link":
                actual_link(source, target, **kwargs)
            raise OSError("receipt publication interruption: " + when)
        return actual_link(source, target, **kwargs)

    monkeypatch.setattr(service.os, "link", fault)
    failed = result(import_(service, destination, raw), 2)
    assert failed["complete"] is False and len(attempts) == 1
    entry = row(failed, ids[0])
    candidate_raw = (destination / entry["candidate_path"]).read_bytes()
    assert sha(candidate_raw) == entry["candidate_sha256"]
    assert entry["import_receipt_sha256"] is None
    staged, published = attempts[0]
    if when == "after_link":
        assert staged.read_bytes() == published.read_bytes()
        assert staged.stat().st_ino == published.stat().st_ino and published.stat().st_nlink == 2
    else:
        assert staged.is_file() and not published.exists()
    monkeypatch.setattr(service.os, "link", actual_link)
    retry = result(import_(service, destination, raw))
    completed = row(retry, ids[0])
    receipt(destination, completed)
    assert (destination / entry["candidate_path"]).read_bytes() == candidate_raw
    assert len(list((destination / PENDING).glob("*.md"))) == 1
    if when == "after_link":
        assert not staged.exists()  # Published record proves ownership for settlement.
    else:
        # An unpublished receipt staging file is an actual prior effect. Do not
        # require adopting/deleting it to pretend the failed attempt was atomic.
        assert staged.is_file()


@pytest.mark.parametrize("binding", ["destination_label", "root_identity"])
def test_receipt_cannot_be_reused_for_another_destination_binding(service, roots, binding):
    _, raw = transfer(service, roots)
    _, destination = roots
    result(import_(service, destination, raw))
    label = "another-destination" if binding == "destination_label" else "destination-project"
    if binding == "root_identity":
        copied = destination.parent / "copied-destination"
        shutil.copytree(destination, copied)
        assert copied.stat().st_ino != destination.stat().st_ino
        destination = copied
    before = tree(destination)
    failed, code = service.import_package(str(destination), destination_id=label,
                                         package="transfer.json", expected_sha256=sha(raw))
    assert code != 0 and tree(destination) == before, failed


def cli_pair(destination, raw, evidence, phase):
    """Two real CLI owners, raw file streams; no launcher/driver product substitute."""
    evidence.mkdir(parents=True, exist_ok=True)
    home = evidence / "home"
    home.mkdir(exist_ok=True)
    env = {"HOME": str(home), "USERPROFILE": str(home), "TMP": str(evidence),
           "TEMP": str(evidence), "TMPDIR": str(evidence),
           "PATH": str(Path(sys.executable).parent), "PYTHONUTF8": "1",
           "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"}
    for key in ("SystemRoot", "WINDIR"):
        if key in os.environ:
            env[key] = os.environ[key]
    argv = [sys.executable, "-I", "-X", "utf8", "-B", str(HERE / "knowledge-curation.py"),
            "import", "--root", str(destination), "--destination-id", "destination-project",
            "--package", "transfer.json", "--expected-sha256", sha(raw)]
    # Exact closed copied inputs, not a broad filesystem inventory.
    names = ["knowledge-curation.py", "knowledge-local.py", "knowledge-curation-rules.py",
             "knowledge-schema.py", "knowledge-taxonomy-local.py", "local-read.py",
             "redact.py", "templates/taxonomy.json"]
    inputs = {name: sha((HERE / name).read_bytes()) for name in names}
    pure_codec = HERE / "knowledge-portability.py"
    codec_present = pure_codec.is_file()
    if codec_present:
        inputs[pure_codec.name] = sha(pure_codec.read_bytes())
    inputs["test_knowledge_portability.py"] = sha((HERE / "test_knowledge_portability.py").read_bytes())
    inputs[Path(__file__).name] = sha(Path(__file__).read_bytes())
    children = []
    observations = []
    with ExitStack() as streams:
        try:
            for number in range(2):
                stem = evidence / f"{phase}-{number}"
                assert pure_codec.is_file() == codec_present, "changed prelaunch codec availability"
                for name, expected in inputs.items():
                    assert sha((HERE / name).read_bytes()) == expected, f"changed prelaunch input: {name}"
                prelaunch = {"argv": argv, "env": env, "cwd": str(evidence), "inputs": inputs,
                             "executable_sha256": sha(Path(sys.executable).read_bytes()),
                             "pure_codec_present": codec_present, "stdin": "DEVNULL",
                             "stdout": str(stem) + ".stdout.bin", "stderr": str(stem) + ".stderr.bin"}
                Path(str(stem) + ".prelaunch.json").write_bytes(canonical(prelaunch))
                out = streams.enter_context(open(str(stem) + ".stdout.bin", "wb"))
                err = streams.enter_context(open(str(stem) + ".stderr.bin", "wb"))
                child = subprocess.Popen(argv, cwd=evidence, env=env, stdin=subprocess.DEVNULL,
                                         stdout=out, stderr=err)
                children.append((child, stem))
                Path(str(stem) + ".pid.json").write_bytes(canonical({"pid": child.pid, "owned": True}))
            for child, stem in children:
                # Test cleanup guard only; no product latency/deadline claim.
                child.wait(timeout=120)
            for child, stem in children:
                stdout = Path(str(stem) + ".stdout.bin").read_bytes()
                stderr = Path(str(stem) + ".stderr.bin").read_bytes()
                observations.append((child.returncode, stdout, stderr))
        finally:
            active_failure = sys.exc_info()[1]
            cleanup_errors = []
            # Kill all outstanding owned children before draining any one; an
            # error for child 1 must not skip child 2 (including failed setup).
            for child, stem in children:
                try:
                    if child.poll() is None:
                        child.kill()
                except OSError as exc:
                    cleanup_errors.append(exc)
            for child, stem in children:
                try:
                    child.wait(timeout=10)
                except (OSError, subprocess.TimeoutExpired) as exc:
                    cleanup_errors.append(exc)
                finally:
                    try:
                        terminal = {"pid": child.pid, "returncode": child.poll(),
                                    "terminal": child.poll() is not None,
                                    "stdout_sha256": sha(Path(str(stem) + ".stdout.bin").read_bytes()),
                                    "stderr_sha256": sha(Path(str(stem) + ".stderr.bin").read_bytes())}
                        Path(str(stem) + ".terminal.json").write_bytes(canonical(terminal))
                    except OSError as exc:
                        cleanup_errors.append(exc)
            if cleanup_errors:
                if active_failure is not None:
                    active_failure.add_note("Scoped child cleanup also failed: " + repr(cleanup_errors))
                else:
                    raise RuntimeError("Scoped child cleanup failed") from cleanup_errors[0]
    return observations


def test_two_actual_cli_processes_cooperate_on_lock_and_same_request(service, roots, tmp_path):
    ids, raw = transfer(service, roots)
    _, destination = roots
    evidence = tmp_path / "cli-evidence"
    # A real parent lock makes both child's lock attempts observable, with no
    # sleep, injected deadline, guessed overlap or invented writer.
    def under_lock_tree():
        # Windows denies reading the locked byte. Preserve every other byte and
        # directory, and observe the lock's identity/size without reading it.
        snapshot = {}
        for path in destination.rglob("*"):
            relative = path.relative_to(destination).as_posix()
            if relative == "docs/knowledge/candidates/.curation-lock":
                info = path.stat()
                snapshot[relative] = (info.st_dev, info.st_ino, info.st_size)
            else:
                snapshot[relative] = path.read_bytes() if path.is_file() else None
        return snapshot

    # Initialize with the actual owner, then capture lock bytes while unlocked.
    with service._locked(str(destination)):
        pass
    unlocked_before = tree(destination)
    with service._locked(str(destination)):
        before = under_lock_tree()
        busy = cli_pair(destination, raw, evidence, "held-lock")
        assert len(busy) == 2
        for code, stdout, stderr in busy:
            payload = json.loads(stdout.decode("utf-8"))
            assert code == 2 and payload["status"] == "writer_busy", (payload, stderr)
        assert under_lock_tree() == before
    assert tree(destination) == unlocked_before
    concurrent = cli_pair(destination, raw, evidence, "same-request")
    assert any(code == 0 for code, _, _ in concurrent), concurrent
    for code, stdout, stderr in concurrent:
        payload = json.loads(stdout.decode("utf-8"))
        assert code in (0, 2), (payload, stderr)
        if code == 2:
            assert payload["status"] == "writer_busy", payload
        else:
            assert payload["complete"] is True
    assert len(list((destination / PENDING).glob("*.md"))) == 1
    before_retry = tree(destination)
    retried = result(import_(service, destination, raw))
    receipt(destination, row(retried, ids[0]))
    assert tree(destination) == before_retry
