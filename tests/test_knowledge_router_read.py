"""Explicit documentary routing and generated output, with owned local fixtures only."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture
def router():
    path = Path(__file__).parents[1] / "agent-kits/shared/knowledge-find.py"
    spec = importlib.util.spec_from_file_location("documentary_router_fixture", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def project(tmp_path):
    backend = {"export_dir": "projection", "health": {"url": "http://127.0.0.1:1/health"},
               "read": {"enabled": True, "timeout_ms": 3000},
               "router": {"intents": {"documental": True}}}
    config = {"version": 1, "id_prefix": "synthetic",
              "backends": {"docs": {"type": "markdown-export", "enabled": True, "config": backend}},
              "categories": [{"key": "DECISION", "folder": "adr", "min_evidence": "observation",
                              "routing": {"docs": True}}]}
    policy = tmp_path / ".claude/knowledge-services/taxonomy.json"
    policy.parent.mkdir(parents=True)
    policy.write_text(json.dumps(config), encoding="utf-8")
    entries = []
    for name, version in (("one", 7), ("two", 11)):
        id_ = "synthetic.DECISION." + name
        raw = (f"---\nid: {id_}\nversion: {version}\ncategory: DECISION\n"
               "estado: aprobado\nevidencia: observation\ntags: [area:billing]\n"
               "iniciativa: demo\n---\n\n# Owned decision\n\nCanonical body.\n")
        relative = f"docs/knowledge/approved/adr/{name}.md"
        file = tmp_path / relative
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(raw.encode())
        entries.append({"id": id_, "version": version, "category": "DECISION", "ruta": relative,
                        "canonical_path": relative, "canonical_sha256": hashlib.sha256(raw.encode()).hexdigest(),
                        "cuerpo": raw.split("---", 2)[2].strip(), "modo": "completo"})
    return tmp_path, config, policy, entries


def response(entries):
    hits, sources = [], []
    for entry in entries:
        id_ = entry["id"]
        body = entry["cuerpo"]
        projection_hash = hashlib.sha256(f"{id_}\n{entry['version']}\nDECISION\n{body}".encode()).hexdigest()
        hits.append({"id": id_, "version": entry["version"], "estado": "aprobado",
                     "evidencia": "observation", "ruta": entry["canonical_path"],
                     "category": "DECISION", "categoria": "adr", "area": "billing",
                     "titular": "Owned decision", "iniciativa": "demo", "puntuacion": 1})
        sources.append({"node_id": "native-" + id_, "file_name": id_ + ".md", "score": 0.7,
                        "canonical_id": id_, "knowledge_version": entry["version"],
                        "canonical_path": entry["canonical_path"],
                        "canonical_sha256": entry["canonical_sha256"], "projection_hash": projection_hash,
                        "project": "synthetic", "scope": "project", "category": "DECISION"})
    return {"aciertos": hits, "motivo": "", "respuesta_generada": {
        "texto": "Generated synthetic response.", "verificacion": "no_verificada", "autoridad": "ninguna",
        "citas_por_afirmacion": False, "source_nodes": sources,
        "generation_consistency": "observed_stable_not_atomic"}}


def spy_backend(router, monkeypatch, entries, output=None):
    calls = []
    real_load = router._cargar_modulo
    class Adapter:
        def puede_leer(self, cfg):
            calls.append(("permission", cfg))
            return {"puede": True}
        def consultar(self, cfg, query):
            calls.append(("query", cfg, query))
            return copy.deepcopy(output if output is not None else response(
                cfg.get("_read_context", {}).get("entries", entries)))
    def load_adapter(*args, **kwargs):
        calls.append(("adapter",))
        return Adapter()
    def load(path, name):
        if Path(path).name == "__init__.py":
            calls.append(("contract",))
            return SimpleNamespace(cargar_adaptador=load_adapter)
        if Path(path).name == "knowledge-read-context.py":
            calls.append(("prepare_module",))
        return real_load(path, name)
    monkeypatch.setattr(router, "_cargar_modulo", load)
    return calls


def test_documentary_routing_has_canonical_context_before_adapter_without_group(router, project, monkeypatch):
    root, config, policy, entries = project
    calls = spy_backend(router, monkeypatch, entries)
    monkeypatch.setattr(router, "_group_id_por_defecto", lambda _: "")
    hits, info = router.consultar_intent(root, "documental", texto="owned question", limit=1)
    assert info["origen"] == "backend", info
    assert len(hits) == 1 and hits[0]["id"] == entries[0]["id"]
    assert hits[0]["tipo"] == "adr" and hits[0]["area"] == "billing"
    assert len(info["respuesta_generada"]["source_nodes"]) == 2
    names = [call[0] for call in calls]
    assert names.index("prepare_module") < names.index("adapter")
    cfg = next(call[1] for call in calls if call[0] == "permission")
    assert cfg["_read_context"]["backend_enabled"] is True
    assert cfg["_backend_id"] == "docs" and cfg["_root"] == str(root.resolve())
    assert cfg["_read_context"]["refresh"]()["deadline"] == cfg["_read_context"]["deadline"]
    assert "group_id" not in cfg


@pytest.mark.parametrize("phase", ["envelope", "hit_filter", "hit_redaction"])
def test_documentary_deadline_includes_final_normalization(router, project, monkeypatch, phase):
    root, config, policy, entries = project
    clock = [100.0]
    monkeypatch.setattr(router.time, "monotonic", lambda: clock[0])
    calls = spy_backend(router, monkeypatch, entries)
    attribute = {"envelope": "_normalizar_respuesta_generada", "hit_filter": "_aciertos_del_backend",
                 "hit_redaction": "_generado_seguro"}[phase]
    original = getattr(router, attribute)
    def crosses_deadline(*args, **kwargs):
        result = original(*args, **kwargs)
        clock[0] = 103.001
        return result
    monkeypatch.setattr(router, attribute, crosses_deadline)
    hits, info = router.consultar_intent(root, "documental", texto="owned question")
    assert len([item for item in calls if item[0] == "query"]) == 1
    assert hits is None and info["origen"] == "local", info
    assert "respuesta_generada" not in info
    assert "deadline" in info["motivo"]


def test_documentary_adapter_score_is_preserved_in_canonical_hits(router, project, monkeypatch):
    root, config, policy, entries = project
    output = response(entries)
    for hit in output["aciertos"]:
        hit.pop("puntuacion")
        hit["score"] = 0.7
    spy_backend(router, monkeypatch, entries, output)
    hits, info = router.consultar_intent(root, "documental", texto="owned question")
    assert info["origen"] == "backend", info
    assert [hit["puntuacion"] for hit in hits] == [0.7, 0.7]
    assert [node["score"] for node in info["respuesta_generada"]["source_nodes"]] == [0.7, 0.7]


@pytest.mark.parametrize("defect", ["disabled", "old_config", "truthy_read", "unknown_read", "partial",
                                    "routing", "version", "private", "nested_private", "stale_policy"])
def test_documentary_policy_fails_before_loading_adapter(router, project, monkeypatch, defect):
    root, config, policy, entries = project
    raw = config["backends"]["docs"]["config"]
    if defect == "disabled": raw["read"]["enabled"] = False
    elif defect == "old_config": raw.pop("read")
    elif defect == "truthy_read": raw["read"]["enabled"] = 1
    elif defect == "unknown_read": raw["read"]["unsafe"] = True
    elif defect == "partial":
        file = root / "docs/knowledge/approved/adr/unreadable.md"
        file.write_bytes(b"\xff\xff")
    elif defect == "routing": config["categories"][0]["routing"]["docs"] = False
    elif defect == "version":
        file = root / entries[0]["canonical_path"]
        file.write_bytes(file.read_bytes().replace(b"version: 7", b"version: 0"))
    elif defect == "private": raw["_read_context"] = {"entries": ["forged"]}
    elif defect == "nested_private": raw["health"]["_root"] = "forged"
    elif defect == "stale_policy":
        policy.write_text(json.dumps(config), encoding="utf-8")
        config = copy.deepcopy(config)
        config["backends"]["docs"]["config"]["export_dir"] = "changed"
    if defect != "stale_policy": policy.write_text(json.dumps(config), encoding="utf-8")
    calls = spy_backend(router, monkeypatch, entries)
    hits, info = router.consultar_intent(root, "documental", texto="owned", config=config)
    assert hits is None and info["origen"] == "local"
    assert not [call for call in calls if call[0] in ("adapter", "permission", "query")]


@pytest.mark.parametrize("filters", [{"area": "operations"}, {"tipo": "gotcha"},
                                     {"iniciativa": "other"}, {"claves": ["operations"]}])
def test_filters_require_entire_canonical_corpus_before_import(router, project, monkeypatch, filters):
    root, config, policy, entries = project
    calls = spy_backend(router, monkeypatch, entries)
    hits, info = router.consultar_intent(root, "documental", texto="owned", **filters)
    assert hits is None and info["origen"] == "local"
    assert not [call for call in calls if call[0] in ("adapter", "permission", "query")]


def test_matching_filters_use_existing_canonical_semantics(router, project, monkeypatch):
    root, config, policy, entries = project
    calls = spy_backend(router, monkeypatch, entries)
    hits, info = router.consultar_intent(root, "documental", texto="owned", tipo="adr", area="billing",
                                       iniciativa="demo", claves=["billing"])
    assert info["origen"] == "backend" and len(hits) == 2
    ctx = next(call[1]["_read_context"] for call in calls if call[0] == "permission")
    assert ctx["filters_authorized"] is True and ctx["filters"]["claves"] == ["billing"]


@pytest.mark.parametrize("kind", ["graphiti", "legacy-stub"])
def test_historical_types_still_require_group(router, project, monkeypatch, kind):
    root, config, policy, entries = project
    config["backends"]["docs"]["type"] = kind
    calls = spy_backend(router, monkeypatch, entries)
    monkeypatch.setattr(router, "_group_id_por_defecto", lambda _: "")
    hits, info = router.consultar_intent(root, "documental", texto="owned", config=config)
    assert hits is None and info["origen"] == "local"
    assert not [call for call in calls if call[0] in ("adapter", "permission", "query")]


@pytest.mark.parametrize("defect", ["authority", "verified", "claims", "atomic", "missing_sources", "duplicate",
                                    "hash", "path", "id", "version", "score", "huge_answer", "extra_key"])
def test_bad_generated_envelope_suppresses_whole_response(router, project, monkeypatch, defect):
    root, config, policy, entries = project
    output = response(entries);generated = output["respuesta_generada"]
    if defect == "authority": generated["autoridad"] = "aprobada"
    elif defect == "verified": generated["verificacion"] = "verificada"
    elif defect == "claims": generated["citas_por_afirmacion"] = True
    elif defect == "atomic": generated["generation_consistency"] = "atomic"
    elif defect == "missing_sources": generated["source_nodes"] = []
    elif defect == "duplicate": generated["source_nodes"].append(copy.deepcopy(generated["source_nodes"][0]))
    elif defect == "hash": generated["source_nodes"][0]["canonical_sha256"] = "bad"
    elif defect == "path": generated["source_nodes"][0]["canonical_path"] = "docs/knowledge/approved/adr/foreign.md"
    elif defect == "id": generated["source_nodes"][0]["canonical_id"] = "foreign"
    elif defect == "version": generated["source_nodes"][0]["knowledge_version"] = True
    elif defect == "score": generated["source_nodes"][0]["score"] = float("nan")
    elif defect == "huge_answer": generated["texto"] = "x" * 65537
    elif defect == "extra_key": generated["execute"] = "untrusted"
    calls = spy_backend(router, monkeypatch, entries, output)
    hits, info = router.consultar_intent(root, "documental", texto="owned")
    assert hits is None and info["origen"] == "local" and "respuesta_generada" not in info


def test_generic_envelope_is_redacted_with_lossless_identities(router, project, monkeypatch):
    root, config, policy, entries = project
    config["backends"]["docs"]["type"] = "legacy-stub"
    config["backends"]["docs"]["config"]["group_id"] = "owned"
    id_ = "synthetic.DECISION." + "a" * 240
    path = "docs/knowledge/approved/adr/" + "b" * 240 + ".md"
    entries = [dict(entries[0], id=id_, canonical_path=path, ruta=path)]
    output = response(entries)
    output["respuesta_generada"]["texto"] = "Answer token=Abcd12345678\x1b[31m\u202e"
    spy_backend(router, monkeypatch, entries, output)
    hits, info = router.consultar_intent(root, "documental", texto="owned", config=config)
    assert info["origen"] == "backend" and hits[0]["id"] == id_ and hits[0]["ruta"] == path
    generated = info["respuesta_generada"]
    assert generated["source_nodes"][0]["canonical_id"] == id_
    assert generated["source_nodes"][0]["canonical_path"] == path
    assert "Abcd12345678" not in generated["texto"] and "\x1b" not in generated["texto"]
    assert "\u202e" not in generated["texto"]


@pytest.mark.parametrize("defect", ["project", "filename", "projection_filename", "hit_score", "hit_category"])
def test_documentary_sources_match_canonical_project_and_projection_name(router, project, monkeypatch, defect):
    root, config, policy, entries = project
    output = response(entries)
    source = output["respuesta_generada"]["source_nodes"][0]
    if defect == "project": source["project"] = "foreign"
    elif defect == "filename": source["file_name"] = "foreign.md"
    elif defect == "projection_filename":
        source["file_name"] = None
        source["projection_filename"] = "foreign.md"
    elif defect == "hit_score": output["aciertos"][0]["puntuacion"] = "Sensitive12345"
    else: output["aciertos"][0]["category"] = "OTHER"
    spy_backend(router, monkeypatch, entries, output)
    hits, info = router.consultar_intent(root, "documental", texto="owned")
    assert hits is None and info["origen"] == "local" and "respuesta_generada" not in info


@pytest.mark.parametrize("defect", ["filename", "hit_score", "hit_category"])
def test_generic_generated_bindings_reject_internal_contradictions(router, project, monkeypatch, defect):
    root, config, policy, entries = project
    config["backends"]["docs"]["type"] = "legacy-stub"
    config["backends"]["docs"]["config"]["group_id"] = "owned"
    output = response(entries)
    if defect == "filename":
        extra = copy.deepcopy(output["respuesta_generada"]["source_nodes"][0])
        extra["node_id"] = "other-chunk"
        extra["file_name"] = "other.md"
        output["respuesta_generada"]["source_nodes"].append(extra)
    elif defect == "hit_score": output["aciertos"][0]["puntuacion"] = "Sensitive12345"
    else: output["aciertos"][0]["category"] = "OTHER"
    spy_backend(router, monkeypatch, entries, output)
    hits, info = router.consultar_intent(root, "documental", texto="owned", config=config)
    assert hits is None and info["origen"] == "local" and "respuesta_generada" not in info


def test_generated_multiple_chunks_and_null_names_are_preserved(router, project, monkeypatch):
    root, config, policy, entries = project
    output = response(entries)
    extra = copy.deepcopy(output["respuesta_generada"]["source_nodes"][0])
    extra["node_id"] = "second-chunk"
    extra["file_name"] = None
    output["respuesta_generada"]["source_nodes"].append(extra)
    spy_backend(router, monkeypatch, entries, output)
    hits, info = router.consultar_intent(root, "documental", texto="owned")
    assert len(hits) == 2 and info["origen"] == "backend"
    assert len(info["respuesta_generada"]["source_nodes"]) == 3
    assert info["respuesta_generada"]["source_nodes"][-1]["file_name"] is None


def test_cli_json_and_text_keep_separate_unverified_answer(router, project, monkeypatch, capsys):
    root, config, policy, entries = project
    spy_backend(router, monkeypatch, entries)
    hits, info = router.consultar_intent(root, "documental", texto="owned")
    args = SimpleNamespace(json=True)
    query = {"texto": "owned token=Abcd12345678", "limit": 1}
    router._imprimir_resultado(args, {"indice": "n/a"}, "proyecto", query, len(hits), hits, router=info)
    payload = json.loads(capsys.readouterr().out)
    assert payload["respuesta_generada"]["verificacion"] == "no_verificada"
    assert "Abcd12345678" not in payload["consulta"]["texto"]
    args.json = False
    router._imprimir_resultado(args, {"indice": "n/a"}, "proyecto", query, len(hits), hits, router=info)
    text = capsys.readouterr().out
    assert "Respuesta generada no verificada" in text and "sin autoridad" in text


@pytest.mark.parametrize("defect", ["oversize", "duplicate", "nan", "depth", "not_object"])
def test_taxonomy_read_is_bounded_strict_and_does_not_echo_raw_errors(router, project, defect):
    root, config, policy, entries = project
    if defect == "oversize": policy.write_text(json.dumps({"padding": "x" * 262144}), encoding="utf-8")
    elif defect == "duplicate": policy.write_text('{"backends":{},"backends":{"evil":1}}', encoding="utf-8")
    elif defect == "nan": policy.write_text('{"token":"Sensitive12345","v":NaN}', encoding="utf-8")
    elif defect == "depth": policy.write_text('{"deep":' + '[' * 70 + '0' + ']' * 70 + '}', encoding="utf-8")
    elif defect == "not_object": policy.write_text('[]', encoding="utf-8")
    loaded, reason = router.taxonomia(root)
    assert loaded is None and reason and "Sensitive12345" not in reason


def test_taxonomy_symlink_is_not_read(router, project):
    root, config, policy, entries = project
    moved = policy.with_name("owned-policy.json")
    policy.rename(moved)
    try:
        policy.symlink_to(moved)
    except OSError:
        pytest.skip("symlink creation is unavailable on this platform")
    loaded, reason = router.taxonomia(root)
    assert loaded is None and reason


@pytest.mark.parametrize("race", [False, True])
def test_router_with_actual_documentary_adapter_and_loopback_post(router, project, race):
    root, config, policy, entries = project
    helper_path = Path(__file__).parents[1] / "skills/knowledge-services/scripts/test_backend_markdown_read.py"
    spec = importlib.util.spec_from_file_location("owned_read_http_fixture", helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    adapter = helper.adapter.__wrapped__()
    core = router._cargar_modulo(Path(router.HERE) / "knowledge-read-context.py", "owned_router_integration_context")
    cfg = config["backends"]["docs"]["config"]
    prepared = core.prepare(root, "docs", "documental", expected_config=cfg)
    assert prepared["status"] == "ok", prepared
    runtime = dict(cfg, _root=str(root.resolve()), _read_context=prepared["context"])
    adapter.apply(adapter.plan(prepared["context"]["entries"], runtime), runtime)
    snapshot = helper.graph(adapter, runtime)
    for node in snapshot["nodes"]:
        if node["type"] == "chunk": node["fm"]["project"] = "synthetic"
    def mutate():
        if race:
            target = root / entries[0]["canonical_path"]
            target.write_bytes(target.read_bytes().replace(b"version: 7", b"version: 8"))
    with helper.bridge(cfg, [snapshot], helper.answer(snapshot), on_query=mutate) as calls:
        policy.write_text(json.dumps(config), encoding="utf-8")
        hits, info = router.consultar_intent(root, "documental", texto="Owned integration question", limit=1)
    assert len([call for call in calls if call[0] == "POST"]) == 1
    # Permission observes one snapshot; query observes its own pre/post pair.
    assert len([call for call in calls if call[0] == "GET" and "snapshot?" in call[1]]) == 3
    if race:
        assert hits is None and info["origen"] == "local" and "respuesta_generada" not in info
    else:
        assert info["origen"] == "backend" and len(hits) == 1
        assert len(info["respuesta_generada"]["source_nodes"]) == 2
        assert info["respuesta_generada"]["autoridad"] == "ninguna"
