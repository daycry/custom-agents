"""Strong documentary read gates, using synthetic owned exports and loopback only."""
import contextlib
import copy
import hashlib
import importlib.util
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import time

import pytest


@pytest.fixture
def adapter():
    path = Path(__file__).parents[1] / "backends" / "markdown_export.py"
    spec = importlib.util.spec_from_file_location("read_fixture_adapter", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def corpus(adapter, tmp_path):
    entries = []
    for number in (1, 2):
        id_ = f"owned.DECISION.D00{number}"
        raw = (f"---\nid: {id_}\nversion: {number}\ncategory: DECISION\n"
               "estado: aprobado\nevidencia: validated_case\n---\n\n"
               f"# Owned fixture {number}\n\nSynthetic document {number}.\n")
        relative = f"docs/knowledge/approved/decision/D00{number}.md"
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw.encode())
        entries.append({"id": id_, "version": number, "category": "DECISION",
                        "estado": "aprobado", "evidencia": "validated_case",
                        "titulo": f"Owned fixture {number}", "folder": "decision",
                        "tags": ["owned"], "ruta": relative, "modo": "completo",
                        "cuerpo": raw.split("---", 2)[2].strip(), "resumen": None,
                        "canonical_path": relative, "canonical_text": raw,
                        "canonical_sha256": hashlib.sha256(raw.encode()).hexdigest()})
    cfg = {"_root": str(tmp_path.resolve()), "_backend_id": "owned",
           "export_dir": "published", "router": {"intents": {"semantico": True}},
           "read": {"enabled": True, "timeout_ms": 1500}}
    adapter.apply(adapter.plan(entries, cfg), cfg)
    ctx = {"root": str(tmp_path.resolve()), "backend_id": "owned",
           "backend_enabled": True, "intent": "semantico", "entries": entries,
           "filters": {"tipo": None, "area": None, "iniciativa": None, "claves": []},
           "fingerprint": "1" * 64, "deadline": time.monotonic() + 1.5}
    ctx["refresh"] = lambda: ctx
    cfg["_read_context"] = ctx
    return cfg


def graph(adapter, cfg):
    nodes = []
    for entry in cfg["_read_context"]["entries"]:
        hash_ = adapter._hash_contenido(entry["id"], entry["version"], entry["category"],
                                       adapter._cuerpo_segun_modo(entry))
        nodes.append({"id": "chunk-" + entry["id"], "type": "chunk",
                      "file_name": entry["id"] + ".md", "file_path": entry["id"] + ".md",
                      "fm": {"knowledge_id": entry["id"], "version": str(entry["version"]),
                             "hash": hash_, "project": "owned", "scope": "project",
                             "category": entry["category"]}})
    nodes.append({"id": "entity-one", "type": "entity", "file_name": None, "fm": {}})
    return {"schema_version": "1.0", "nodes": nodes, "links": [],
            "stats": {"total_nodes_raw": len(nodes), "kept_nodes": len(nodes),
                      "kept_links": 0, "skipped_noisy": 0, "skipped_malformed_nodes": 0,
                      "skipped_malformed_relations": 0}}


def answer(snapshot, **changes):
    chunks = [node for node in snapshot["nodes"] if node["type"] == "chunk"]
    return {"schema_version": "1.0", "answer": "Synthetic generated answer.",
            "citations": [{"node_id": node["id"], "file_name": None, "score": 0.7}
                          for node in chunks], "cited_node_ids": [node["id"] for node in chunks],
            "cited_files": [], "highlight_node_ids": [], **changes}


@contextlib.contextmanager
def bridge(cfg, snapshots, response=None, on_query=None, options=None):
    calls = []
    options = options or {}
    snapshot_reads = 0

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            nonlocal snapshot_reads
            calls.append(("GET", self.path))
            if self.path.endswith("/health"):
                body = options.get('health', {"schema_version": "1.0", "status": "ok"})
            elif self.path.startswith("/prefix/graph/snapshot?"):
                body = snapshots[min(snapshot_reads, len(snapshots) - 1)]
                snapshot_reads += 1
            else:
                self.send_response(404)
                self.end_headers()
                return
            self.send_response(200)
            self.end_headers()
            self.wfile.write(json.dumps(body).encode())

        def do_POST(self):
            body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
            calls.append(("POST", self.path, json.loads(body)))
            if on_query:
                on_query()
            code = options.get("code", 200)
            self.send_response(code)
            for key, value in options.get("headers", {}).items():
                self.send_header(key, value)
            self.end_headers()
            data = options.get("raw", json.dumps(response or {}).encode())
            try:
                step = options.get("step", len(data) or 1)
                for i in range(0, len(data), step):
                    self.wfile.write(data[i:i + step])
                    self.wfile.flush()
                    time.sleep(options.get("interval", 0))
            except (OSError, BrokenPipeError):
                pass

        def log_message(self, *args):
            pass

    srv = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=srv.serve_forever)
    worker.start()
    cfg["health"] = {"url": f"http://127.0.0.1:{srv.server_port}/prefix/health"}
    try:
        yield calls
    finally:
        srv.shutdown()
        srv.server_close()
        worker.join(3)
        assert not worker.is_alive()


def read(adapter, cfg, **query):
    function = getattr(adapter, "consultar", None)
    assert callable(function), "optional documentary read API is not implemented"
    return function(cfg, {"texto": "Synthetic question?", **query})


def permission(adapter, cfg):
    function = getattr(adapter, "puede_leer", None)
    assert callable(function), "optional documentary permission API is not implemented"
    return function(cfg)


@pytest.mark.parametrize('remaining', [1, 8])
def test_shared_reader_overflow_guard_never_exceeds_local_read_budget(adapter, corpus, monkeypatch, remaining):
    allocated = []
    def failed_read(root, relative, *, max_bytes, include_digest):
        allocated.append(max_bytes + 1)
        return {'status': 'changed_path', 'text': None, 'bytes': max_bytes + 1}
    monkeypatch.setattr(adapter, '_READ_LOCAL_READER', failed_read)
    budget = [remaining]
    with pytest.raises(adapter._ReadRejected):
        adapter._read_file(corpus['_root'], 'owned.md', budget, time.monotonic() + 1)
    assert sum(allocated) <= remaining and budget[0] >= 0
    if remaining == 1:
        assert allocated == []


def test_native_chunks_null_citations_and_unverified_answer(adapter, corpus):
    snap = graph(adapter, corpus)
    extra = copy.deepcopy(snap["nodes"][0])
    extra["id"] += "-second"
    snap["nodes"].append(extra)
    snap["stats"]["total_nodes_raw"] = snap["stats"]["kept_nodes"] = 4
    with bridge(corpus, [snap], answer(snap)) as calls:
        result = read(adapter, corpus, limit=1)
    assert result["motivo"] == ""
    assert len(result["aciertos"]) == 2
    generated = result["respuesta_generada"]
    assert generated["verificacion"] == "no_verificada"
    assert generated["autoridad"] == "ninguna"
    assert generated["citas_por_afirmacion"] is False
    assert generated["generation_consistency"] == "observed_stable_not_atomic"
    assert len(generated["source_nodes"]) == 3
    assert all(hit["estado"] == "aprobado" for hit in result["aciertos"])
    assert [call[1] for call in calls if call[0] == "POST"] == ["/prefix/query"]
    assert calls[2][2] == {"q": "Synthetic question?"}
    assert "include_chunks=true" in calls[1][1] and "min_degree=0" in calls[1][1]
    assert "drop_noisy=false" in calls[1][1]


@pytest.mark.parametrize("gate", ["disabled", "intent", "context", "enabled_string", "empty",
                                   "unknown_key", "bool_limit", "oversize_limit", "pending",
                                   "canon", "revoked", "projection", "manifest", "filter"])
def test_local_gate_blocks_all_network(adapter, corpus, gate):
    ctx = corpus["_read_context"]
    if gate == "disabled": corpus.pop("read")
    elif gate == "intent": corpus["router"]["intents"]["semantico"] = False
    elif gate == "context": corpus.pop("_read_context")
    elif gate == "enabled_string": corpus["read"]["enabled"] = "true"
    elif gate == "empty": ctx["entries"] = []
    elif gate == "unknown_key": corpus["read"]["unknown"] = True
    elif gate == "bool_limit": corpus["read"]["max_request_bytes"] = True
    elif gate == "oversize_limit": corpus["read"]["max_snapshot_bytes"] = 2097153
    elif gate == "pending": (Path(ctx["root"]) / "published/manifest.pending.json").write_text("invalid")
    elif gate == "canon": (Path(ctx["root"]) / ctx["entries"][0]["canonical_path"]).write_text("revoked")
    elif gate == "revoked": ctx["entries"][0]["estado"] = "revocado"
    elif gate == "projection": (Path(ctx["root"]) / "published/owned.DECISION.D001.md").write_text("tampered")
    elif gate == "manifest":
        p = Path(ctx["root"]) / "published/manifest.json"
        m = json.loads(p.read_text()); m["entries"].pop("owned.DECISION.D002");p.write_text(json.dumps(m))
    elif gate == "filter": ctx["filters"]["tipo"] = "decision"
    with bridge(corpus, [graph(adapter, {**corpus, "_read_context": ctx})]) as calls:
        assert permission(adapter, corpus)["puede"] is False
        assert not read(adapter, corpus).get("respuesta_generada")
    assert calls == []


@pytest.mark.parametrize("defect", ["hash", "version", "scope", "project", "missing_id", "alias",
                                     "entity_source", "extra_doc", "missing_doc", "duplicate_id",
                                     "missing_hash", "category", "truncated_stats", "node_not_object",
                                     "fm_not_object", "node_hash", "node_filename", "raw_count",
                                     "dangling_link", "links_not_array", "zero_version"])
def test_every_chunk_binding_is_required_before_post(adapter, corpus, defect):
    snap = graph(adapter, corpus)
    response = answer(snap)
    node = snap["nodes"][0]
    if defect in ("hash", "version", "scope", "project", "category"): node["fm"][defect] = "wrong"
    elif defect == "missing_id": node["fm"].pop("knowledge_id")
    elif defect == "alias": node["fm"]["id"] = "contradictory"
    elif defect == "entity_source": node["type"] = "entity"
    elif defect == "extra_doc": node["fm"]["knowledge_id"] = "foreign.DECISION.X"
    elif defect == "missing_doc": snap["nodes"].pop(0);snap["stats"]["kept_nodes"] -= 1
    elif defect == "duplicate_id": snap["nodes"][1]["id"] = node["id"]
    elif defect == "missing_hash": node["fm"].pop("hash")
    elif defect == "truncated_stats": snap["stats"]["skipped_malformed_nodes"] = 1
    elif defect == "node_not_object": snap['nodes'][0] = None
    elif defect == "fm_not_object": node['fm'] = []
    elif defect == "node_hash": node['hash'] = 'wrong'
    elif defect == "node_filename": node['file_name'] = 'foreign.md'
    elif defect == "raw_count": snap['stats']['total_nodes_raw'] += 1
    elif defect == "dangling_link":
        snap['links'] = [{'source': node['id'], 'target': 'absent'}]
        snap['stats']['kept_links'] = 1
    elif defect == "links_not_array": snap['links'] = {}
    elif defect == "zero_version": node['fm']['version'] = '0'
    with bridge(corpus, [snap], response) as calls:
        result = read(adapter, corpus)
    assert not result.get("respuesta_generada")
    assert not [c for c in calls if c[0] == "POST"]


@pytest.mark.parametrize("defect", ["entity", "unknown", "contradictory_name", "no_sources", "nan",
                                     "too_many_sources", "overlong_answer", "bad_schema", "score_bool",
                                     "citation_not_object", "duplicate_citation", "missing_cited_ids",
                                     "foreign_cited_file", "sanitized_empty"])
def test_bad_query_sources_suppress_whole_answer(adapter, corpus, defect):
    snap = graph(adapter, corpus); response = answer(snap)
    if defect == "entity": response["citations"][0]["node_id"] = "entity-one"
    elif defect == "unknown": response["citations"][0]["node_id"] = "unknown"
    elif defect == "contradictory_name": response["citations"][0]["file_name"] = "foreign.md"
    elif defect == "no_sources": response["citations"] = [];response["cited_node_ids"] = []
    elif defect == "nan": response["citations"][0]["score"] = float("nan")
    elif defect == "too_many_sources": corpus["read"]["max_source_nodes"] = 1
    elif defect == "overlong_answer": corpus["read"]["max_answer_chars"] = 8
    elif defect == "bad_schema": response["schema_version"] = "2.0"
    elif defect == "score_bool": response['citations'][0]['score'] = True
    elif defect == "citation_not_object": response['citations'][0] = None
    elif defect == "duplicate_citation": response['citations'].append(copy.deepcopy(response['citations'][0]))
    elif defect == "missing_cited_ids": response['cited_node_ids'] = []
    elif defect == "foreign_cited_file": response['cited_files'] = ['foreign.md']
    elif defect == "sanitized_empty": response['answer'] = '\x1b[31m\u202e\x00'
    with bridge(corpus, [snap], response) as calls:
        result = read(adapter, corpus)
    assert not result.get("respuesta_generada")
    assert len([c for c in calls if c[0] == "POST"]) == 1


@pytest.mark.parametrize("race", ["snapshot", "canon", "pending", "fingerprint", "policy"])
def test_changes_during_generation_suppress_everything_without_retry(adapter, corpus, race):
    snap = graph(adapter, corpus); after = copy.deepcopy(snap)
    ctx = corpus["_read_context"]
    def mutate():
        if race == "canon": (Path(ctx["root"]) / ctx["entries"][0]["canonical_path"]).write_text("changed")
        elif race == "pending": (Path(ctx["root"]) / "published/manifest.pending.json").write_text("{}")
        elif race == "fingerprint": ctx["fingerprint"] = "2" * 64
        elif race == "policy": corpus["router"]["intents"]["semantico"] = False
    if race == "snapshot": after["nodes"][-1]["name"] = "graph reloaded"
    with bridge(corpus, [snap, after], answer(snap), on_query=mutate) as calls:
        result = read(adapter, corpus)
    assert not result.get("respuesta_generada")
    assert result["aciertos"] == []
    assert len([c for c in calls if c[0] == "POST"]) == 1


@pytest.mark.parametrize("mode", ["redirect", "503", "malformed", "truncated", "oversize"])
def test_post_transport_is_bounded_closed_and_never_redirects(adapter, corpus, mode):
    snap = graph(adapter, corpus); response = answer(snap);options = {}
    if mode == "redirect": options = {"code": 307, "headers": {"Location": "/prefix/query-again"}}
    elif mode == "503": options = {"code": 503}
    elif mode == "malformed": options = {"raw": b"not JSON"}
    elif mode == "truncated": options = {"headers": {"Content-Length": "999999"}}
    elif mode == "oversize": corpus["read"]["max_response_bytes"] = 64
    with bridge(corpus, [snap], response, options=options) as calls:
        result = read(adapter, corpus)
    assert not result.get("respuesta_generada")
    assert len([c for c in calls if c[0] == "POST"]) == 1


def test_dribbling_post_cannot_extend_its_absolute_transport_deadline(adapter, corpus):
    # Exercise the POST budget directly: corpus preflight and starting an owned
    # server can exhaust 100ms before consultar has any opportunity to POST.
    # No deadline is renewed during transport, including after each received byte.
    snap = graph(adapter, corpus)
    with bridge(corpus, [snap], answer(snap), options={'step': 1, 'interval': 0.02}) as calls:
        base = adapter._base_url_snapshot(corpus['health']['url'])
        started = time.monotonic()
        with pytest.raises(TimeoutError):
            adapter._read_json(base + '/query', started + 0.1, 4096, data=b'{"q":"Synthetic?"}')
        elapsed = time.monotonic() - started
    assert elapsed < 0.3
    assert [(call[0], call[1]) for call in calls] == [('POST', '/prefix/query')]


def test_expired_total_query_deadline_during_preflight_prevents_all_transport(adapter, corpus, monkeypatch):
    corpus['health'] = {'url': 'http://127.0.0.1:1/health'}
    corpus['read']['timeout_ms'] = 100
    clock = [100.0]
    corpus['_read_context']['deadline'] = 100.1
    original = adapter._read_local
    checked = []
    def slow_preflight(*args, **kwargs):
        before = original(*args, **kwargs)
        checked.append(before[5])
        clock[0] += 0.101
        return before
    monkeypatch.setattr(adapter.time, 'monotonic', lambda: clock[0])
    monkeypatch.setattr(adapter, '_read_local', slow_preflight)
    transport = []
    def forbidden(*args, **kwargs):
        transport.append(args)
        raise AssertionError('expired total deadline reached transport')
    monkeypatch.setattr(adapter, '_urlopen_local', forbidden)
    result = read(adapter, corpus)
    assert checked == [100.1] and corpus['_read_context']['deadline'] == 100.1
    assert result['aciertos'] == [] and 'respuesta_generada' not in result
    assert result['motivo'] == 'deadline_read_agotado' and transport == []


def test_request_secret_redacted_and_controls_removed_without_persistence(adapter, corpus):
    snap = graph(adapter, corpus); response = answer(snap, answer="Generated\x1b[31m\u202esecret token=Abcd12345678")
    root = Path(corpus["_root"])
    before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}
    with bridge(corpus, [snap], response) as calls:
        result = read(adapter, corpus, texto="Question token=Abcd12345678\x1b[31m\u202e?")
    post = next(c for c in calls if c[0] == "POST")
    assert "Abcd12345678" not in post[2]["q"]
    text = result["respuesta_generada"]["texto"]
    assert "Abcd12345678" not in text and "\x1b" not in text and "\u202e" not in text
    assert {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()} == before


def test_query_filter_cannot_bypass_preflight_context(adapter, corpus):
    snap = graph(adapter, corpus)
    with bridge(corpus, [snap], answer(snap)) as calls:
        result = read(adapter, corpus, tipo="foreign")
    assert not result.get("respuesta_generada") and calls == []


def test_request_budget_rejects_before_any_network(adapter, corpus):
    snap = graph(adapter, corpus);corpus["read"]["max_request_bytes"] = 12
    with bridge(corpus, [snap], answer(snap)) as calls:
        result = read(adapter, corpus)
    assert not result.get("respuesta_generada") and calls == []


def test_bom_canonical_bytes_have_separate_authority_from_decoded_text(adapter, corpus):
    entry = corpus["_read_context"]["entries"][0]
    path = Path(corpus["_root"]) / entry["canonical_path"]
    raw = b"\xef\xbb\xbf" + path.read_bytes()
    path.write_bytes(raw)
    entry["canonical_sha256"] = hashlib.sha256(raw).hexdigest()
    snap = graph(adapter, corpus)
    with bridge(corpus, [snap], answer(snap)):
        result = read(adapter, corpus)
    assert result["motivo"] == ""
    binding = result["respuesta_generada"]["source_nodes"][0]
    assert binding["canonical_sha256"] == hashlib.sha256(raw).hexdigest()
    assert binding["canonical_sha256"] != hashlib.sha256(entry["canonical_text"].encode()).hexdigest()


def test_context_deadline_cannot_expand_configured_budget(adapter, corpus):
    corpus["read"]["timeout_ms"] = 50
    snap = graph(adapter, corpus)
    with bridge(corpus, [snap], answer(snap)) as calls:
        result = read(adapter, corpus)
    assert not result.get("respuesta_generada") and calls == []


def test_direct_read_redacts_local_display_metadata(adapter, corpus):
    entry = corpus["_read_context"]["entries"][0]
    entry["titulo"] = "Owned token=Abcd12345678\x1b[31m\u202e"
    entry["tags"] = ["owned", "token=Abcd12345678\u202e"]
    snap = graph(adapter, corpus)
    with bridge(corpus, [snap], answer(snap)):
        result = read(adapter, corpus)
    assert result["motivo"] == ""
    metadata = json.dumps(result["aciertos"], ensure_ascii=False)
    assert "Abcd12345678" not in metadata and "\u202e" not in metadata
    assert result["aciertos"][0]["id"] == entry["id"]
    assert result["aciertos"][0]["ruta"] == entry["canonical_path"]


@pytest.mark.parametrize('defect', ['config_not_object', 'read_not_object', 'wrong_root', 'wrong_backend',
    'unknown_router', 'router_default', 'intent_not_bool', 'fingerprint', 'deadline_nan',
    'unknown_filter', 'oversize_filters', 'duplicate_entry', 'bad_version', 'bad_folder',
    'canonical_path', 'body_not_text', 'manifest_shape', 'extra_manifest_entry'])
def test_forged_or_incomplete_local_authority_never_opens_transport(adapter, corpus, monkeypatch, defect):
    corpus['health'] = {'url': 'http://127.0.0.1:1/health'}
    ctx = corpus['_read_context']
    entry = ctx['entries'][0]
    if defect == 'config_not_object': corpus = []
    elif defect == 'read_not_object': corpus['read'] = []
    elif defect == 'wrong_root': ctx['root'] = str(Path(ctx['root']) / 'absent')
    elif defect == 'wrong_backend': ctx['backend_id'] = 'foreign'
    elif defect == 'unknown_router': corpus['router']['unknown'] = True
    elif defect == 'router_default': corpus['router']['default'] = True
    elif defect == 'intent_not_bool': corpus['router']['intents']['semantico'] = 1
    elif defect == 'fingerprint': ctx['fingerprint'] = 'INVALID'
    elif defect == 'deadline_nan': ctx['deadline'] = float('nan')
    elif defect == 'unknown_filter': ctx['filters']['unknown'] = ''
    elif defect == 'oversize_filters': ctx['filters']['claves'] = ['owned'] * 129
    elif defect == 'duplicate_entry': ctx['entries'].append(copy.deepcopy(entry))
    elif defect == 'bad_version': entry['version'] = True
    elif defect == 'bad_folder': entry['folder'] = '../decision'
    elif defect == 'canonical_path': entry['canonical_path'] = 'docs/knowledge/candidates/pending/D001.md'
    elif defect == 'body_not_text': entry['cuerpo'] = None
    elif defect in ('manifest_shape', 'extra_manifest_entry'):
        path = Path(ctx['root']) / 'published/manifest.json'
        manifest = json.loads(path.read_text())
        if defect == 'manifest_shape': manifest['version'] = True
        else: manifest['entries']['foreign.DECISION.EXTRA'] = {}
        path.write_text(json.dumps(manifest), encoding='utf-8')
    calls = []
    def forbidden(*args, **kwargs):
        calls.append(args)
        raise AssertionError('unauthorized transport opened')
    monkeypatch.setattr(adapter, '_urlopen_local', forbidden)
    assert permission(adapter, corpus)['puede'] is False
    result = read(adapter, corpus)
    assert result['aciertos'] == [] and 'respuesta_generada' not in result
    assert calls == []


@pytest.mark.parametrize('url', ['http://user:secret@127.0.0.1/health',
    'http://169.254.169.254/health', 'http://8.8.8.8/health', 'http://[2002:0808:0808::]/health',
    'http://127.0.0.1:0/health', 'http://127.0.0.1/health?token=secret'])
def test_disallowed_address_or_url_never_probes_dns_or_transport(adapter, corpus, monkeypatch, url):
    corpus['health'] = {'url': url}
    monkeypatch.setattr(adapter.socket, 'getaddrinfo', lambda *_: pytest.fail('rejected URL reached DNS'))
    monkeypatch.setattr(adapter, '_urlopen_local', lambda *_a, **_kw: pytest.fail('rejected URL reached transport'))
    result = read(adapter, corpus)
    assert result['aciertos'] == [] and result['motivo'] == 'health_url_invalida'
    assert 'secret' not in json.dumps(result)


def test_permission_gate_accepts_verified_bindings_without_sending_a_query(adapter, corpus):
    snap = graph(adapter, corpus)
    with bridge(corpus, [snap]) as calls:
        assert permission(adapter, corpus) == {'puede': True}
    assert len(calls) == 2 and all(call[0] == 'GET' for call in calls)


@pytest.mark.parametrize('health', [{'schema_version': '1.0', 'status': 'degraded'},
    {'schema_version': '1.0', 'status': 'ok', 'ollama': {'status': 'error'}},
    {'schema_version': '1.0', 'status': 'ok', 'property_graph': []}])
def test_unhealthy_dependencies_stop_before_snapshot_or_query(adapter, corpus, health):
    with bridge(corpus, [graph(adapter, corpus)], options={'health': health}) as calls:
        result = read(adapter, corpus)
    assert result['aciertos'] == [] and result['motivo'] == 'health_no_sano'
    assert len(calls) == 1 and calls[0][1].endswith('/health')


def test_permission_denial_is_read_only_and_never_exposes_filesystem_error(adapter, corpus, monkeypatch):
    corpus['health'] = {'url': 'http://127.0.0.1:1/health'}
    root = Path(corpus['_root'])
    before = {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}
    original = adapter.os.open
    target = root / 'published/manifest.json'
    def denied(path, *args, **kwargs):
        if Path(path) == target: raise PermissionError('PRIVATE_FILESYSTEM_DETAIL')
        return original(path, *args, **kwargs)
    monkeypatch.setattr(adapter.os, 'open', denied)
    monkeypatch.setattr(adapter, '_urlopen_local', lambda *_a, **_kw: pytest.fail('denied local IO reached transport'))
    result = read(adapter, corpus)
    assert result['aciertos'] == [] and result['motivo'] == 'lectura_local_inestable'
    assert 'PRIVATE_' not in json.dumps(result)
    assert {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()} == before
