"""Public retrieval contract for approved-only consumer fixtures.

These tests never use the repository's memory or the user's configuration.
Each CLI invocation has its own project, HOME and bytecode-disabled process.
No backend service is started: optional router behavior uses fixture adapters.
"""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "agent-kits/shared/knowledge-find.py"
ENTRY_ID = "fixture.ADR-200"
PEER_ID = "fixture.ADR-201"


def _write_entry(project, entry_id=ENTRY_ID, version=7, folder="adr", body=None):
    path = project / "docs/knowledge/approved" / folder / (entry_id + ".md")
    path.parent.mkdir(parents=True, exist_ok=True)
    text = (
        "---\n"
        f"id: {entry_id}\n"
        "category: DECISION\n"
        f"version: {version}\n"
        "estado: aprobado\n"
        "evidencia: validated_case\n"
        "fuentes:\n  - fixture-contract.md\n"
        "tags:\n  - area:recuperacion\n"
        "iniciativa: fixture-retrieval\n"
        "fecha: 2026-10-08\n"
        "---\n\n"
        "# Recuperacion aprobada\n\n"
        + (body or "El corpus aprobado conserva decisiones de recuperacion locales.")
        + "\n"
    )
    path.write_text(text, encoding="utf-8", newline="")
    return path, text


def _write_taxonomy(project, folder="adr", backend_type=None):
    data = {
        "version": 1,
        "id_prefix": "fixture",
        "categories": [{"key": "DECISION", "folder": folder,
                        "min_evidence": "validated_case"}],
    }
    if backend_type:
        data["backends"] = {
            "fixture-backend": {
                "type": backend_type, "enabled": True,
                "config": {"group_id": "fixture-only",
                           "router": {"intents": {"temporal": True}}},
            }
        }
    path = project / ".claude/knowledge-services/taxonomy.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


@pytest.fixture
def consumer(tmp_path):
    project = tmp_path / "consumer"
    project.mkdir()
    home = tmp_path / "isolated-home"
    home.mkdir()
    _write_taxonomy(project)
    path, text = _write_entry(project)
    _write_entry(project, PEER_ID, version=3)
    return project, home, path, text


def _run(consumer, *args):
    project, home, _path, _text = consumer
    env = dict(os.environ)
    env.update(HOME=str(home), USERPROFILE=str(home),
               CLAUDE_CONFIG_DIR=str(home / ".claude"),
               PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8")
    env.pop("CLAUDE_PROJECT_DIR", None)
    env.pop("PYTHONPATH", None)
    result = subprocess.run(
        [sys.executable, "-B", str(SCRIPT), "--root", str(project), "--json", *args],
        cwd=project, env=env, capture_output=True, encoding="utf-8", errors="replace",
        timeout=20,
    )
    return result, json.loads(result.stdout) if result.stdout.strip() else None


def _assert_record(record, entry_id=ENTRY_ID, version=7):
    assert record["id"] == entry_id
    assert record["version"] == version
    assert record["estado"] == "aprobado"
    assert record["evidencia"] == "validated_case"
    assert record["ruta"] == f"docs/knowledge/approved/adr/{entry_id}.md"


def test_approved_only_query_preserves_exact_identity_and_metadata(consumer):
    result, data = _run(consumer, "--area", "recuperacion", "--limit", "0")
    assert result.returncode == 0, result.stderr
    records = {item["id"]: item for item in data["aciertos"]}
    assert set(records) == {ENTRY_ID, PEER_ID}, data
    _assert_record(records[ENTRY_ID])
    _assert_record(records[PEER_ID], PEER_ID, 3)


def test_show_resolves_exact_namespaced_approved_id_and_original_content(consumer):
    result, data = _run(consumer, "--show", ENTRY_ID)
    assert result.returncode == 0, result.stderr
    assert data["id"] == ENTRY_ID
    assert data["version"] == 1  # Existing JSON envelope version remains compatible.
    assert data["knowledge_version"] == 7
    assert data["evidencia"] == "validated_case"
    assert data["estado"] == "aprobado"
    assert data["ruta"] == f"docs/knowledge/approved/adr/{ENTRY_ID}.md"
    assert data["contenido"] == consumer[3]


def test_related_resolves_approved_id_and_preserves_peer_metadata(consumer):
    result, data = _run(consumer, "--related", ENTRY_ID)
    assert result.returncode == 0, result.stderr
    _assert_record(data["entrada"])
    related = data["relaciones"]["area"]["aciertos"]
    assert [item["id"] for item in related] == [PEER_ID]
    _assert_record(related[0], PEER_ID, 3)


def test_unavailable_backend_falls_back_to_approved_local_entry(consumer):
    _write_taxonomy(consumer[0], backend_type="fixture-adapter-unavailable")
    result, data = _run(consumer, "--intent", "temporal", "recuperacion")
    assert result.returncode == 0, result.stderr
    assert data["router"]["origen"] == "local"
    assert data["router"]["motivo"]
    records = {item["id"]: item for item in data["aciertos"]}
    assert ENTRY_ID in records, data
    _assert_record(records[ENTRY_ID])


def test_cache_and_flat_results_match_and_approved_edit_invalidates_cache(consumer):
    _first_result, first = _run(consumer, "--area", "recuperacion", "--limit", "0")
    assert first["total"] == 2, first
    _cached_result, cached = _run(consumer, "--area", "recuperacion", "--limit", "0")
    _flat_result, flat = _run(consumer, "--no-index", "--area", "recuperacion", "--limit", "0")
    assert cached["aciertos"] == flat["aciertos"]
    assert cached["indice"] == "cache"
    _write_entry(consumer[0], version=8, body="La decision cambia y conserva la procedencia.")
    _changed_result, changed = _run(consumer, "--area", "recuperacion", "--limit", "0")
    assert changed["indice"] == "reconstruido"
    records = {item["id"]: item for item in changed["aciertos"]}
    _assert_record(records[ENTRY_ID], version=8)
    _changed_flat_result, changed_flat = _run(consumer, "--no-index", "--area", "recuperacion", "--limit", "0")
    assert changed["aciertos"] == changed_flat["aciertos"]


def test_taxonomy_folder_change_invalidates_approved_cache(consumer):
    _result, initial = _run(consumer, "--area", "recuperacion", "--limit", "0")
    assert initial["total"] == 2, initial
    _run(consumer, "--area", "recuperacion", "--limit", "0")
    _write_taxonomy(consumer[0], folder="decisions")
    _result, after = _run(consumer, "--area", "recuperacion", "--limit", "0")
    assert after["aciertos"] == []
    _result, flat = _run(consumer, "--no-index", "--area", "recuperacion", "--limit", "0")
    assert after["aciertos"] == flat["aciertos"]


def test_pending_candidates_never_enter_local_retrieval(consumer):
    pending = consumer[0] / "docs/knowledge/candidates/pending/fixture.PENDING-999.md"
    pending.parent.mkdir(parents=True)
    pending.write_text(
        "---\nid: fixture.PENDING-999\ncategory: DECISION\nversion: 1\n"
        "estado: aprobado\nevidencia: validated_case\ntags: [area:recuperacion]\n"
        "---\n\n# Recuperacion candidata\n\nCandidate content must remain a proposal.\n",
        encoding="utf-8",
    )
    result, data = _run(consumer, "--area", "recuperacion", "--limit", "0")
    assert result.returncode == 0, result.stderr
    assert {item["id"] for item in data["aciertos"]} == {ENTRY_ID, PEER_ID}, data
    result, _data = _run(consumer, "--show", "fixture.PENDING-999")
    assert result.returncode == 1
    assert pending.exists()


def test_router_preserves_backend_knowledge_version(consumer):
    project = consumer[0]
    _write_taxonomy(project, backend_type="fixture-version")
    adapter_dir = project / "fixture-adapters"
    adapter_dir.mkdir()
    record = {
        "id": ENTRY_ID, "version": 7, "estado": "aprobado",
        "evidencia": "validated_case",
        "ruta": f"docs/knowledge/approved/adr/{ENTRY_ID}.md",
        "tipo": "adr", "area": "recuperacion", "titular": "Recuperacion aprobada",
    }
    adapter = (
        "def health(cfg): return {'estado': 'sano'}\n"
        "def plan(entries, cfg, force=False): return []\n"
        "def apply(ops, cfg): return {'aplicados': 0}\n"
        "def verify(cfg): return {'ok': True}\n"
        "def rebuild(entries, cfg): return {'aplicados': 0}\n"
        "def revoke(knowledge_id, cfg): return None\n"
        "def puede_leer(cfg): return {'puede': True}\n"
        f"def consultar(cfg, consulta): return {{'aciertos': [{record!r}]}}\n"
    )
    (adapter_dir / "fixture_version.py").write_text(adapter, encoding="utf-8")
    result, data = _run(consumer, "--intent", "temporal", "--backends-dir", str(adapter_dir), "recuperacion")
    assert result.returncode == 0, result.stderr
    assert data["router"]["origen"] == "backend", data
    assert len(data["aciertos"]) == 1
    _assert_record(data["aciertos"][0])


def _write_legacy(project, entry_id="ADR-100"):
    path = project / "docs/knowledge/adr" / (entry_id + ".md")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"---\nid: {entry_id}\nestado: aceptada\narea: recuperacion\n---\n\n"
        "# Legacy decision\n\nExisting accepted knowledge remains readable.\n", encoding="utf-8",
    )


@pytest.mark.parametrize("problem", ["duplicate", "version", "state", "category", "broken-link"])
def test_invalid_approved_corpus_degrades_to_legacy_with_diagnostic(consumer, problem):
    project, _home, path, text = consumer
    _write_legacy(project)
    if problem == "duplicate":
        (path.parent / "duplicate.md").write_text(text, encoding="utf-8")
    elif problem == "version":
        path.write_text(text.replace("version: 7", "version: invalid"), encoding="utf-8")
    elif problem == "state":
        path.write_text(text.replace("estado: aprobado", "estado: propuesta"), encoding="utf-8")
    elif problem == "category":
        path.write_text(text.replace("category: DECISION", "category: UNKNOWN"), encoding="utf-8")
    else:
        path.write_text(text.replace("fecha: 2026-10-08", "enlaces: [fixture.MISSING]\nfecha: 2026-10-08"), encoding="utf-8")
    result, data = _run(consumer, "--area", "recuperacion", "--limit", "0")
    assert result.returncode == 0, result.stderr
    assert [item["id"] for item in data["aciertos"]] == ["ADR-100"]
    assert "approved" in result.stderr.lower(), result.stderr
    assert len(result.stderr) <= 1200


@pytest.mark.parametrize("mode", ["--show", "--related"])
def test_legacy_approved_exact_id_collision_is_ambiguous(consumer, mode):
    project = consumer[0]
    _write_legacy(project, entry_id="ADR-200")
    _write_entry(project, entry_id="ADR-200")
    result, data = _run(consumer, mode, "ADR-200")
    assert result.returncode == 1, data
    assert "ambigu" in result.stderr.lower(), result.stderr


@pytest.mark.parametrize("problem", ["endpoint", "config-shape", "enabled"])
def test_invalid_service_config_does_not_remove_valid_local_approved(consumer, problem):
    project = consumer[0]
    _write_taxonomy(project, backend_type="graphiti")
    path = project / ".claude/knowledge-services/taxonomy.json"
    taxonomy = json.loads(path.read_text(encoding="utf-8"))
    backend = taxonomy["backends"]["fixture-backend"]
    if problem == "endpoint":
        backend["config"]["endpoint"] = "invalid-url"
    elif problem == "config-shape":
        backend["config"] = "invalid"
    else:
        backend["enabled"] = "invalid"
    path.write_text(json.dumps(taxonomy), encoding="utf-8")
    result, data = _run(consumer, "--area", "recuperacion", "--limit", "0")
    assert result.returncode == 0, result.stderr
    records = {item["id"]: item for item in data["aciertos"]}
    assert ENTRY_ID in records, data
    _assert_record(records[ENTRY_ID])


def test_declared_folder_escape_is_rejected_with_legacy_fallback(consumer):
    _write_legacy(consumer[0])
    _write_taxonomy(consumer[0], folder="../candidates/pending")
    result, data = _run(consumer, "--area", "recuperacion", "--limit", "0")
    assert result.returncode == 0, result.stderr
    assert [item["id"] for item in data["aciertos"]] == ["ADR-100"]
    assert "approved" in result.stderr.lower(), result.stderr


@pytest.mark.parametrize("component", ["approved", "folder"])
def test_symlink_or_junction_outside_project_is_rejected(consumer, component):
    project = consumer[0]
    _write_legacy(project)
    outside = project.parent / "outside-fixture"
    source, _text = _write_entry(outside)
    approved = project / "docs/knowledge/approved"
    link = approved if component == "approved" else approved / "adr"
    target = source.parent.parent if component == "approved" else source.parent
    link.rename(link.with_name(link.name + "-original"))
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        if os.name != "nt":
            raise
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(link), str(target)],
                                capture_output=True, encoding="utf-8", errors="replace")
        if result.returncode:
            pytest.skip("Fixture filesystem cannot create symlinks or junctions")
    result, data = _run(consumer, "--area", "recuperacion", "--limit", "0")
    assert result.returncode == 0, result.stderr
    assert [item["id"] for item in data["aciertos"]] == ["ADR-100"]
    assert "approved" in result.stderr.lower(), result.stderr


def test_approved_source_with_crlf_is_returned_without_normalization(consumer):
    path = consumer[2]
    raw = consumer[3].replace("\n", "\r\n")
    path.write_bytes(raw.encode("utf-8"))
    result, data = _run(consumer, "--show", ENTRY_ID)
    assert result.returncode == 0, result.stderr
    assert data["contenido"] == raw


def test_hook_style_approved_retrieval_cannot_import_network_modules(consumer):
    project, home, _path, _text = consumer
    guard = (
        "import sys, runpy\n"
        "class NoNetworkImports:\n"
        " def find_spec(self, fullname, path=None, target=None):\n"
        "  if fullname.split('.')[0] in ('socket', 'requests') or fullname == 'http.client' or (fullname.startswith('urllib.') and fullname != 'urllib.parse'):\n"
        "   raise AssertionError('network-capable import: ' + fullname)\n"
        "sys.meta_path.insert(0, NoNetworkImports())\n"
        "def no_network_operations(event, args):\n"
        " if event.startswith('socket.') or event in ('urllib.Request', 'http.client.connect', 'http.client.send'):\n"
        "  raise AssertionError('network operation: ' + event)\n"
        "sys.addaudithook(no_network_operations)\n"
        "sys.argv = sys.argv[1:]\n"
        "runpy.run_path(sys.argv[0], run_name='__main__')\n"
    )
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home),
               CLAUDE_CONFIG_DIR=str(home / ".claude"), PYTHONDONTWRITEBYTECODE="1")
    result = subprocess.run(
        [sys.executable, "-B", "-c", guard, str(SCRIPT), "--root", str(project),
         "--json", "--limit", "0", "--contexto", "Recuperacion aprobada", "--iniciativa", "fixture-retrieval"],
        cwd=project, env=env, capture_output=True, encoding="utf-8", errors="replace", timeout=20,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert {item["id"] for item in data["aciertos"]} == {ENTRY_ID, PEER_ID}, data
    assert "network-capable import" not in result.stderr
    assert "network operation" not in result.stderr


def test_portable_export_closes_local_helper_dependencies():
    import importlib.util
    root = SCRIPT.parents[2]
    spec = importlib.util.spec_from_file_location("export_approved_fixture", root / "scripts/export-skills.py")
    exporter = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(exporter)
    included = set(exporter.fragmentos_shared(str(root), ["agent-kits/shared/knowledge-find.py"]))
    assert {"agent-kits/shared/knowledge-local.py",
            "agent-kits/shared/knowledge-taxonomy-local.py"} <= included


@pytest.mark.parametrize("category,expected_type", [("DECISION", "adr"), ("CUSTOM", "custom")])
def test_custom_folder_category_filter_and_approved_rank(consumer, category, expected_type):
    project = consumer[0]
    _write_taxonomy(project, folder="decisions/history")
    taxonomy_path = project / ".claude/knowledge-services/taxonomy.json"
    cfg = json.loads(taxonomy_path.read_text(encoding="utf-8"))
    cfg["categories"][0]["key"] = category
    taxonomy_path.write_text(json.dumps(cfg), encoding="utf-8")
    path, text = _write_entry(project, folder="decisions/history")
    path.write_text(text.replace("category: DECISION", f"category: {category}"), encoding="utf-8")
    _write_legacy(project)
    legacy = project / "docs/knowledge/adr/ADR-100.md"
    legacy.write_text(legacy.read_text(encoding="utf-8").replace("aceptada", "propuesta"), encoding="utf-8")
    result, data = _run(consumer, "--area", "recuperacion", "--limit", "0")
    assert result.returncode == 0, result.stderr
    assert data["aciertos"][0]["id"] == ENTRY_ID
    record = data["aciertos"][0]
    assert record["tipo"] == expected_type
    assert record["category"] == category
    assert record["estado"] == "aprobado"
    _r, filtered = _run(consumer, "--tipo", expected_type, "--area", "recuperacion", "--limit", "0")
    assert ENTRY_ID in {x["id"] for x in filtered["aciertos"]}
    _r, flat = _run(consumer, "--no-index", "--tipo", expected_type, "--area", "recuperacion", "--limit", "0")
    assert filtered["aciertos"] == flat["aciertos"]


def test_related_explicit_namespaced_links_are_not_succession(consumer):
    path, text = _write_entry(consumer[0], PEER_ID, version=3)
    path.write_text(text.replace("area:recuperacion", "area:otras").replace("fixture-retrieval", "unrelated"), encoding="utf-8")
    consumer[2].write_text(consumer[3].replace("fecha:", f"enlaces: [{PEER_ID}]\nfecha:"), encoding="utf-8")
    _r, data = _run(consumer, "--related", ENTRY_ID)
    assert data["relaciones"]["sucesion"] == []
    assert data["relaciones"]["iniciativa"]["aciertos"] == []
    assert data["relaciones"]["area"]["aciertos"] == []
    _assert_record(data["relaciones"]["enlaces"]["aciertos"][0], PEER_ID, 3)
    _r, flat = _run(consumer, "--no-index", "--related", ENTRY_ID)
    assert data["relaciones"] == flat["relaciones"]


@pytest.mark.parametrize("version", [True, [], {}, "\x1b[31m7", "7\nforged"])
def test_remote_invalid_version_is_rejected_without_control_leak(version):
    import importlib.util
    spec = importlib.util.spec_from_file_location("find_version_fixture", SCRIPT)
    finder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(finder)
    record = {"id": ENTRY_ID, "estado": "aprobado", "evidencia": "validated_case", "ruta": "docs/knowledge/approved/adr/entry.md", "version": version}
    assert finder.acierto_remoto(record, "fixture") is None


@pytest.mark.parametrize("version", [7, "7", "v7"])
def test_remote_valid_version_keeps_type_and_value(version):
    import importlib.util
    spec = importlib.util.spec_from_file_location("find_valid_version_fixture", SCRIPT)
    finder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(finder)
    record = {"id": ENTRY_ID, "estado": "aprobado", "evidencia": "validated_case", "ruta": "docs/knowledge/approved/adr/entry.md", "version": version}
    result = finder.acierto_remoto(record, "fixture")
    assert result["version"] == version
    assert type(result["version"]) is type(version)


def test_approved_root_link_to_candidates_is_not_approval(consumer):
    project = consumer[0]
    _write_legacy(project)
    candidates = project / "docs/knowledge/candidates/pending"
    candidates.mkdir(parents=True)
    source, _text = _write_entry(project)
    target = candidates / "adr"
    target.mkdir()
    (target / source.name).write_bytes(source.read_bytes())
    approved = project / "docs/knowledge/approved"
    approved.rename(approved.with_name("approved-original"))
    try:
        approved.symlink_to(candidates, target_is_directory=True)
    except OSError:
        if os.name != "nt":
            raise
        result = subprocess.run(["cmd", "/c", "mklink", "/J", str(approved), str(candidates)], capture_output=True)
        if result.returncode:
            pytest.skip("Fixture filesystem cannot create symlinks or junctions")
    result, data = _run(consumer, "--area", "recuperacion", "--limit", "0")
    assert [x["id"] for x in data["aciertos"]] == ["ADR-100"]
    assert "approved" in result.stderr.lower()


@pytest.mark.parametrize("field", ["area", "titulo", "iniciativa", "fecha", "fuente", "evidencia"])
@pytest.mark.parametrize("flat", [False, True])
def test_b1_optional_lists_degrade_approved_and_preserve_legacy(consumer, field, flat):
    project, _home, path, text = consumer
    _write_legacy(project)
    # Preserve full-index shape policy: optional retrieval labels are not approval criteria.
    lines = [line for line in text.splitlines() if not line.startswith(field + ":")]
    lines.insert(1, f"{field}: [invalid-label]")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    import importlib.util
    spec = importlib.util.spec_from_file_location("b1_full_index_fixture", SCRIPT.with_name("knowledge-index.py"))
    indexer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(indexer)
    _index, errors = indexer.build_index(str(project))
    assert errors == []
    result, data = _run(consumer, *( ["--no-index"] if flat else []), "--area", "recuperacion", "--limit", "0")
    assert result.returncode == 0, result.stderr
    assert [record["id"] for record in data["aciertos"]] == ["ADR-100"]
    assert "approved" in result.stderr.lower()
    assert "Traceback" not in result.stderr
    assert len(result.stderr) <= 1200


@pytest.mark.parametrize("script,missing", [
    ("knowledge-schema.py", "knowledge-taxonomy-local.py"),
    ("knowledge-index.py", "knowledge-taxonomy-local.py"),
    ("knowledge-index.py", "knowledge-local.py"),
])
def test_b2_partial_shared_kit_cli_and_api_fail_closed_without_traceback(consumer, script, missing):
    import importlib.util
    import shutil
    project, home, _path, _text = consumer
    kit = project / "partial-shared"
    kit.mkdir()
    for name in ("knowledge-schema.py", "knowledge-index.py", "knowledge-local.py", "knowledge-taxonomy-local.py"):
        if name != missing:
            shutil.copyfile(SCRIPT.with_name(name), kit / name)
    spec = importlib.util.spec_from_file_location("b2_partial_fixture", kit / script)
    wrapper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wrapper)
    if script == "knowledge-schema.py":
        _config, _origin, _path, errors = wrapper.cargar_taxonomia(str(project))
        assert wrapper.validar({})
        argv = ["--default"]
    else:
        index, errors = wrapper.build_index(str(project))
        assert index == {}
        argv = ["--root", str(project)]
    assert errors and errors[0]["campo"] == "$"
    assert missing in errors[0]["mensaje"]
    env = dict(os.environ, HOME=str(home), USERPROFILE=str(home), CLAUDE_CONFIG_DIR=str(home / ".claude"), PYTHONDONTWRITEBYTECODE="1")
    result = subprocess.run([sys.executable, "-B", str(kit / script), *argv], cwd=project, env=env, capture_output=True, encoding="utf-8", errors="replace", timeout=20)
    assert result.returncode in (1, 2)
    assert "Traceback" not in result.stdout + result.stderr
    assert missing in result.stdout + result.stderr


def test_a1_compatibility_fallback_is_forwarded_without_new_definition(consumer):
    import importlib.util
    import shutil
    schema_path = SCRIPT.with_name("knowledge-schema.py")
    spec = importlib.util.spec_from_file_location("a1_schema_forwarding_fixture", schema_path)
    schema = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(schema)
    assert schema._TAXONOMY_FALLBACK is schema._LOCAL._TAXONOMY_FALLBACK
    assert "_TAXONOMY_FALLBACK" not in schema.__dict__
    root = SCRIPT.parents[2]
    lint_spec = importlib.util.spec_from_file_location("a1_linter_fixture", root / "scripts/lint_plugin.py")
    linter = importlib.util.module_from_spec(lint_spec)
    lint_spec.loader.exec_module(linter)
    fixture_root = consumer[0] / "lint-fixture"
    for rel in ("agent-kits/shared/knowledge-schema.py", "agent-kits/shared/knowledge-taxonomy-local.py", "agent-kits/shared/copias.json"):
        dest = fixture_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(root / rel, dest)
    assert linter.comprobar_copias_declaradas(str(fixture_root)) == ([], [])


@pytest.mark.parametrize("tags", [[[]], [{"area": "recuperacion"}], [7]])
def test_b1_local_reader_rejects_non_scalar_tags_without_changing_full_index(consumer, monkeypatch, tags):
    import importlib.util
    spec = importlib.util.spec_from_file_location("b1_local_tags_fixture", SCRIPT.with_name("knowledge-local.py"))
    reader = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(reader)
    original = reader._frontmatter
    def parsed(text):
        fm = original(text)
        fm["tags"] = tags
        return fm
    monkeypatch.setattr(reader, "_frontmatter", parsed)
    _full, full_errors = reader.build_index(str(consumer[0]))
    assert full_errors == []
    _local, local_errors = reader.build_index(str(consumer[0]), include_source=True)
    assert local_errors and local_errors[0]["campo"] == "tags"
