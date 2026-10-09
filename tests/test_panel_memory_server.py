"""Explicit memory query transport validates input before invoking its owner."""
import http.client
import importlib.util
import json
from pathlib import Path
import socket
import threading
import time
import types

import pytest


@pytest.fixture
def memory_server(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[1] / 'skills/plugin-panel/scripts/serve_panel.py'
    spec = importlib.util.spec_from_file_location('memory_transport', path)
    service = importlib.util.module_from_spec(spec); spec.loader.exec_module(service)
    validator = service._load_shared('knowledge-view.py')
    calls = []
    def query(root, **args):
        assert root == tmp_path
        calls.append(args)
        return {'version': 1, 'source': 'canonical_knowledge', 'observed_at': '2026-10-09T10:00:00Z',
                'operation': args.get('operation', 'search'), 'status': 'ok', 'complete': True,
                'issues': [], 'entries': [], 'selected': None, 'related': None,
                'budget': {'files': 0, 'bytes': 0, 'entries': 0}}
    monkeypatch.setattr(service, '_load_memory', lambda: types.SimpleNamespace(
        query=query, valid_request=validator.valid_request), raising=False)
    data = {'counts': dict.fromkeys(('agents', 'skills', 'commands', 'tools', 'hooks'), 0),
            'agents': [], 'skills': [], 'commands': [], 'tools': [], 'hooks': [],
            'runtimes': {}, 'memory': {}, 'warnings': [], 'workflow': {'roles': {}}}
    server = service.create_server(tmp_path, data)
    server.test_service = service; server.test_calls = calls
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    yield server
    server.shutdown(); server.server_close(); thread.join(timeout=5)
    assert not thread.is_alive()


def send(server, payload=None, *, method='POST', suffix='api/memory', headers=None, raw=None, early=False):
    body = (json.dumps(payload).encode() if method == 'POST' else None) if raw is None else raw
    conn = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
    request_headers = {'Content-Type': 'application/json', **(headers or {})}
    if early:
        # Rejected framing/origin needs only headers; leave no unread TCP payload.
        request_headers['Content-Length'] = str(len(body))
    conn.request(method, server.access_prefix + suffix, body=None if early else body,
                 headers=request_headers)
    response = conn.getresponse(); data = response.read()
    result = response.status, dict(response.getheaders()), data
    conn.close(); return result


def test_memory_query_is_explicit_and_delegated_to_shared_owner(memory_server):
    server = memory_server
    status, headers, raw = send(server, {'operation': 'search', 'text': 'routing'})
    assert status == 200 and json.loads(raw)['source'] == 'canonical_knowledge'
    assert server.test_calls == [{'operation': 'search', 'text': 'routing'}]
    assert headers['Cache-Control'] == 'no-store' and headers['Referrer-Policy'] == 'no-referrer'
    assert 'Access-Control-Allow-Origin' not in headers and 'Set-Cookie' not in headers


@pytest.mark.parametrize('operation', ['show', 'related'])
def test_selected_operations_preserve_full_id(memory_server, operation):
    identity = 'owned-project.DECISION.storage-policy.v2'
    assert send(memory_server, {'operation': operation, 'id': identity})[0] == 200
    assert memory_server.test_calls[-1]['id'] == identity


@pytest.mark.parametrize('payload', [None, [], 'query', {'root': '/outside'},
    {'operation': 'sync'}, {'operation': 'search', 'backend': 'arbitrary'},
    {'operation': 'search', 'text': []}, {'operation': 'search', 'text': 'x' * 1001},
    {'operation': 'search', 'limit': True}, {'operation': 'search', 'limit': 0},
    {'operation': 'search', 'limit': 21}, {'operation': 'show', 'id': []},
    {'operation': 'show', 'id': 'x' * 257}, {'operation': 'related', 'id': ''},
    {'operation': 'show', 'id': 'ADR-001', 'text': 'unexpected'}])
def test_invalid_request_never_invokes_query(memory_server, payload):
    assert send(memory_server, payload)[0] == 400
    assert memory_server.test_calls == []


@pytest.mark.parametrize('raw', [b'{broken', b'{"text":"\xff"}',
    b'{"operation":"search","operation":"show"}', b'{"limit":NaN}',
    b'[' * 1100 + b']' * 1100, b'{"text":"' + b'x' * 4096 + b'"}'])
def test_malformed_or_oversized_json_never_invokes_query(memory_server, raw):
    assert send(memory_server, raw=raw, early=len(raw) > 4096)[0] in (400, 413)
    assert memory_server.test_calls == []


@pytest.mark.parametrize('headers', [{'Origin': 'null'}, {'Origin': 'https://outside.invalid'},
    {'Host': 'outside.invalid'}, {'Sec-Fetch-Site': 'cross-site'}, {'Content-Type': 'text/plain'},
    {'Transfer-Encoding': 'chunked'}])
def test_memory_request_origin_and_encoding_are_checked(memory_server, headers):
    assert send(memory_server, {'operation': 'search'}, headers=headers, early=True)[0] in (400, 403, 415)
    assert memory_server.test_calls == []


@pytest.mark.parametrize('method', ['GET', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'])
def test_memory_route_cannot_mutate_or_query_via_other_methods(memory_server, method):
    assert send(memory_server, {'operation': 'search'}, method=method)[0] in (400, 404, 405)
    assert memory_server.test_calls == []


def test_wrong_capability_never_queries(memory_server):
    conn = http.client.HTTPConnection('127.0.0.1', memory_server.server_port, timeout=5)
    conn.request('POST', '/wrong/api/memory', headers={'Content-Type': 'application/json'})
    response = conn.getresponse(); assert response.status == 404
    response.read(); conn.close(); assert memory_server.test_calls == []


def test_reader_unavailable_degrades_opaquely(memory_server, monkeypatch):
    def absent():raise ImportError('PRIVATE_EXPLANATION')
    monkeypatch.setattr(memory_server.test_service, '_load_memory', absent)
    status, _, raw = send(memory_server, {'operation': 'search'})
    assert status == 200 and json.loads(raw)['status'] == 'unavailable'
    assert b'PRIVATE_EXPLANATION' not in raw and memory_server.test_calls == []


def test_response_budget_never_sends_oversized_data(memory_server, monkeypatch):
    monkeypatch.setattr(memory_server.test_service, '_load_memory',
                        lambda: types.SimpleNamespace(valid_request=lambda **kw: True,
                            query=lambda *a, **kw: {'oversized': 'x' * 70000}))
    status, _, raw = send(memory_server, {'operation': 'search'})
    assert status == 200 and len(raw) <= 65536
    assert json.loads(raw)['status'] == 'unavailable'


def test_duplicate_length_rejected_before_reader(memory_server):
    server = memory_server
    with socket.create_connection(('127.0.0.1', server.server_port), timeout=5) as sock:
        sock.sendall(('POST ' + server.access_prefix + 'api/memory HTTP/1.1\r\n'
            + f'Host: 127.0.0.1:{server.server_port}\r\nContent-Type: application/json\r\n'
            + 'Content-Length: 2\r\nContent-Length: 2\r\n\r\n').encode())
        raw = sock.recv(4096)
    assert b'400' in raw and server.test_calls == []


def test_accumulated_body_deadline_rejects_dribbling_without_query(memory_server, monkeypatch):
    server = memory_server
    monkeypatch.setattr(server.test_service, 'BODY_TIMEOUT', 0.12, raising=False)
    with socket.create_connection(('127.0.0.1', server.server_port), timeout=1) as sock:
        start = time.monotonic()
        sock.sendall(('POST ' + server.access_prefix + 'api/memory HTTP/1.1\r\n'
            + f'Host: 127.0.0.1:{server.server_port}\r\nContent-Type: application/json\r\n'
            + 'Content-Length: 10\r\n\r\n{').encode())
        time.sleep(0.08)
        sock.sendall(b' ')
        raw = sock.recv(4096)
    assert b'400' in raw and time.monotonic() - start < 0.8
    assert server.test_calls == []


@pytest.mark.parametrize('operation', ['search', 'show', 'related'])
def test_real_shared_reader_runs_from_http_without_cache_or_writes(memory_server, monkeypatch, operation):
    server = memory_server
    path = server.project / 'docs/knowledge/adr/ADR-001-store.md'
    path.parent.mkdir(parents=True)
    source = ('---\nid: project.ADR-001.store\nestado: aceptada\narea: storage\n'
              'version: 2\nevidencia: owned-fixture\n---\n# Storage policy\n\nUse canonical storage.\n')
    path.write_text(source, encoding='utf8')
    before = {p.relative_to(server.project).as_posix(): p.read_bytes()
              for p in server.project.rglob('*') if p.is_file()}
    monkeypatch.setattr(server.test_service, '_load_memory',
                        lambda: server.test_service._load_shared('knowledge-view.py'))
    payload = {'operation': operation}
    if operation == 'search': payload['text'] = 'storage'
    else: payload['id'] = 'project.ADR-001.store'
    status, _, raw = send(server, payload)
    result = json.loads(raw)
    assert status == 200 and result['source'] == 'canonical_knowledge'
    assert result['complete'] and result['status'] == 'ok'
    if operation == 'search':
        assert result['entries'][0]['id'] == 'project.ADR-001.store'
        assert 'texto' not in result['entries'][0]
    elif operation == 'show':
        assert result['selected']['version'] == 2
        assert 'canonical storage' in result['selected']['texto']
    else:
        assert result['related'] is not None and result['selected'] is None
    assert before == {p.relative_to(server.project).as_posix(): p.read_bytes()
                      for p in server.project.rglob('*') if p.is_file()}
    assert server.test_calls == []
