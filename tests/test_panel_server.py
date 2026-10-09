"""Local HTTP capability and canonical ledger projection contracts."""
import hashlib
import http.client
import importlib.util
import json
from pathlib import Path
import threading
import types

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def service():
    path = ROOT / 'skills/plugin-panel/scripts/serve_panel.py'
    spec = importlib.util.spec_from_file_location('tested_panel_service', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ledger(project, folder='2026-10-09-example', title='Build feature', state='en-progreso'):
    path = project / 'docs/roadmap' / folder / 'tasks.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    text = ('---\nestado: en-progreso\n---\n# Work\n## Fase 1 — Build\n'
            '### T-01 — Completed\n- **Estado**: completado\n'
            f'### T-02 — {title}\n- **Estado**: {state}\n')
    path.write_text(text, encoding='utf8', newline='\n')
    return path, text


def test_projection_reuses_canonical_counts_and_content_identity(service, tmp_path):
    path, text = ledger(tmp_path)
    result = service.progress_snapshot(tmp_path)
    assert result['source'] == 'canonical_ledger' and result['complete'] is True
    assert result['status'] == 'ok' and result['version'] == 1
    row, = result['initiatives']
    assert (row['total'], row['completadas'], row['pct']) == (2, 1, 50)
    assert row['en_progreso'] == [{'id': 'T-02', 'titulo': 'Build feature'}]
    assert row['fase'] == {'indice': 1, 'total': 1, 'nombre': 'Build'}
    assert row['source_sha256'] == hashlib.sha256(text.encode()).hexdigest()
    body = json.dumps(result)
    assert str(path) not in body and '### T-01' not in body
    assert set(row) == {'id', 'title', 'estado', 'total', 'completadas', 'pct',
                       'fase', 'en_progreso', 'source_sha256'}


def test_projection_redacts_before_truncating_and_removes_controls(service, tmp_path):
    secret = 'ghp_' + 'A' * 32
    ledger(tmp_path, title=secret + '\u202e' + '<script>alert(1)</script>' + 'x' * 250)
    result = service.progress_snapshot(tmp_path)
    title = result['initiatives'][0]['en_progreso'][0]['titulo']
    assert secret not in json.dumps(result) and '\u202e' not in title and len(title) <= 160


def test_projection_absence_empty_and_malformed_are_distinct(service, tmp_path):
    assert service.progress_snapshot(tmp_path)['status'] == 'not_found'
    roadmap = tmp_path / 'docs/roadmap'; roadmap.mkdir(parents=True)
    assert service.progress_snapshot(tmp_path)['status'] == 'ok'
    bad = roadmap / 'broken/tasks.md'; bad.parent.mkdir(); bad.write_text('# no tasks', encoding='utf8')
    result = service.progress_snapshot(tmp_path)
    assert result['status'] == 'partial' and not result['complete']
    assert result['initiatives'] == [] and result['issues'] == [{'status': 'malformed'}]


def test_projection_bom_changes_and_no_caching_in_pure_compositor(service, tmp_path):
    path, text = ledger(tmp_path)
    path.write_bytes(b'\xef\xbb\xbf' + text.encode())
    first = service.progress_snapshot(tmp_path)['initiatives'][0]
    path.write_text(text.replace('en-progreso', 'completado'), encoding='utf8')
    second = service.progress_snapshot(tmp_path)['initiatives'][0]
    assert first['source_sha256'] != second['source_sha256']
    assert first['pct'] == 50 and second['pct'] == 100


def test_projection_incomplete_listing_stays_partial(service, tmp_path, monkeypatch):
    ledger(tmp_path)
    real = service._load_shared
    reader = real('local-read.py')
    reader.list_names = lambda *a, **k: {'status': 'incomplete', 'complete': False, 'names': ['2026-10-09-example']}
    monkeypatch.setattr(service, '_load_shared', lambda name: reader if name == 'local-read.py' else real(name))
    result = service.progress_snapshot(tmp_path)
    assert result['status'] == 'partial' and result['complete'] is False and len(result['initiatives']) == 1


def test_projection_total_read_budget_is_enforced(service, tmp_path, monkeypatch):
    real = service._load_shared; calls = []
    text = ledger(tmp_path)[1]
    def read(*a, **k):
        calls.append(k['max_bytes']); return {'status': 'ok', 'text': text, 'bytes': k['max_bytes']}
    reader = types.SimpleNamespace(list_names=lambda *a, **k: {'status': 'ok', 'complete': True,
                                    'names': ['item' + str(n) for n in range(128)]}, read_text=read)
    monkeypatch.setattr(service, '_load_shared', lambda name: reader if name == 'local-read.py' else real(name))
    result = service.progress_snapshot(tmp_path)
    assert sum(calls) <= 1024 * 1024 and len(calls) == 4
    assert not result['complete'] and {'status': 'scan_budget'} in result['issues']


def test_projection_output_and_rows_remain_bounded(service, tmp_path):
    for n in range(65):
        path, text = ledger(tmp_path, folder=f'2026-10-09-item-{n:03}', title='🙂' * 160)
        text += ''.join(f'### T-{t:02} — ' + '🙂' * 160 + '\n- **Estado**: en-progreso\n' for t in range(3, 10))
        path.write_text(text, encoding='utf8')
    result = service.progress_snapshot(tmp_path)
    assert len(json.dumps(result, ensure_ascii=False).encode()) <= 65536
    assert len(result['initiatives']) <= 64 and not result['complete']


def test_projection_fails_closed_without_trusted_helper(service, tmp_path, monkeypatch):
    monkeypatch.setattr(service, '_load_shared', lambda name: (_ for _ in ()).throw(ImportError('/private/path')))
    result = service.progress_snapshot(tmp_path)
    assert result['status'] == 'unavailable' and result['issues'] == [{'status': 'reader_unavailable'}]
    assert '/private/path' not in json.dumps(result)


def test_projection_nonregular_ledger_is_not_absence_but_index_file_is_skipped(service, tmp_path):
    roadmap = tmp_path / 'docs/roadmap'; roadmap.mkdir(parents=True)
    (roadmap / 'README.md').write_text('index', encoding='utf8')
    assert service.progress_snapshot(tmp_path)['complete'] is True
    (roadmap / '2026-10-09-broken/tasks.md').mkdir(parents=True)
    result = service.progress_snapshot(tmp_path)
    assert result['status'] == 'partial' and {'status': 'not_regular'} in result['issues']


def test_review_b1_title_budget_marks_projection_partial(service, tmp_path):
    ledger(tmp_path, title='x' * 220)
    result = service.progress_snapshot(tmp_path)
    assert len(result['initiatives'][0]['en_progreso'][0]['titulo']) == 160
    assert result['status'] == 'partial' and not result['complete']
    assert {'status': 'text_budget'} in result['issues']


def test_review_b1_unknown_task_state_is_explicit(service, tmp_path):
    ledger(tmp_path, state='bloqueado')
    result = service.progress_snapshot(tmp_path)
    assert result['initiatives'][0]['total'] == 2
    assert result['status'] == 'partial' and not result['complete']
    assert {'status': 'unknown_task_state'} in result['issues']


@pytest.fixture
def http_server(service, tmp_path):
    ledger(tmp_path)
    builder = service._load_builder()
    inventory = builder.build_inventory(tmp_path, project=None)
    server = service.create_server(tmp_path, inventory)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    yield server
    server.shutdown(); server.server_close(); thread.join(timeout=5)
    assert not thread.is_alive()


def request(server, suffix='', method='GET', headers=None, target=None):
    conn = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
    conn.request(method, target if target is not None else server.access_prefix + suffix, headers=headers or {})
    response = conn.getresponse(); body = response.read()
    result = response.status, dict(response.getheaders()), body
    conn.close(); return result


def test_http_bind_capability_headers_and_canonical_update(http_server):
    server = http_server
    assert server.server_address[0] == '127.0.0.1' and len(server.access_prefix.split('/')[1]) >= 43
    status, headers, body = request(server)
    assert status == 200 and b'id="operations"' in body
    assert headers['Cache-Control'] == 'no-store' and headers['Referrer-Policy'] == 'no-referrer'
    assert headers['X-Content-Type-Options'] == 'nosniff'
    assert "frame-ancestors 'none'" in headers['Content-Security-Policy']
    assert "connect-src 'self'" in headers['Content-Security-Policy']
    assert "script-src 'nonce-" in headers['Content-Security-Policy']
    assert 'Access-Control-Allow-Origin' not in headers and 'Set-Cookie' not in headers
    status, _, raw = request(server, 'api/progress')
    assert status == 200 and json.loads(raw)['initiatives'][0]['pct'] == 50
    assert server.access_prefix.encode() not in raw


@pytest.mark.parametrize('target', ['/', '/bad/', '/api/progress', '/.claude/settings.json',
                                     '/%2e%2e/', 'http://outside.invalid/'])
def test_http_untrusted_targets_never_serve_files(http_server, target):
    status, headers, body = request(http_server, target=target)
    assert status in (400, 403, 404) and b'Build feature' not in body
    assert headers['Cache-Control'] == 'no-store'


@pytest.mark.parametrize('headers', [{'Host': 'outside.invalid'}, {'Origin': 'null'},
                                     {'Origin': 'https://outside.invalid'}, {'Sec-Fetch-Site': 'cross-site'},
                                     {'Transfer-Encoding': 'chunked'}, {'Content-Length': '1'}])
def test_http_rejects_cross_origin_and_request_bodies(http_server, headers):
    assert request(http_server, 'api/progress', headers=headers)[0] in (400, 403)


def test_http_duplicate_host_rejected(http_server):
    server = http_server; conn = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
    conn.putrequest('GET', server.access_prefix, skip_host=True)
    conn.putheader('Host', f'127.0.0.1:{server.server_port}'); conn.putheader('Host', 'outside.invalid')
    conn.endheaders(); response = conn.getresponse()
    assert response.status == 403; response.read(); conn.close()


@pytest.mark.parametrize('suffix', ['api/progress?path=secret', '../secret', '%2e%2e/secret', 'api/%70rogress', 'secret'])
def test_http_only_exact_routes(http_server, suffix):
    assert request(http_server, suffix)[0] == 404


@pytest.mark.parametrize('method', ['POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'])
def test_http_mutating_methods_unavailable(http_server, method):
    status, _, body = request(http_server, 'api/progress', method=method)
    assert status == 405 and b'Build feature' not in body


def test_http_head_and_no_access_logging(http_server, capsys):
    status, headers, body = request(http_server, method='HEAD')
    assert status == 200 and body == b'' and int(headers['Content-Length']) > 0
    assert capsys.readouterr().err == ''


def test_http_bad_port_never_binds(service, tmp_path):
    for port in (-1, 65536, True, '9999'):
        with pytest.raises(ValueError):service.create_server(tmp_path, {}, port=port)


def test_builder_serve_is_explicit_project_only_and_separate_from_exports(service, tmp_path, monkeypatch):
    builder = service._load_builder(); calls = []
    monkeypatch.setattr(builder, 'build_inventory', lambda *a, **kw: calls.append(kw) or {'own': 'inventory'})
    monkeypatch.setattr(builder, '_load_server', lambda: types.SimpleNamespace(run=lambda project, data, **kw: 0))
    assert builder.main(['--serve', '--project', str(tmp_path), '--port', '0']) == 0
    assert calls[0]['include_user'] is False


@pytest.mark.parametrize('args', [['--serve'], ['--serve', '--project', '.', '--html', 'file.html'],
    ['--serve', '--project', '.', '--json'], ['--serve', '--project', '.', '--home', '.'],
    ['--serve', '--project', '.', '--user-root', 'codex=.'], ['--port', '1234'],
    ['--serve', '--project', '.', '--port', '-1']])
def test_builder_invalid_serve_options_fail_before_inventory(service, monkeypatch, args):
    builder = service._load_builder()
    monkeypatch.setattr(builder, 'build_inventory', lambda *a, **k: pytest.fail('unexpected inventory read'))
    with pytest.raises(SystemExit) as error:builder.main(args)
    assert error.value.code == 2


def test_http_non_ascii_capability_is_opaque_rejection(http_server):
    import socket
    server = http_server
    with socket.create_connection(('127.0.0.1', server.server_port), timeout=5) as sock:
        sock.sendall(b'GET /\xff/ HTTP/1.1\r\nHost: 127.0.0.1:' + str(server.server_port).encode() + b'\r\n\r\n')
        response = sock.recv(4096)
    assert b'404' in response and b'Build feature' not in response


def test_bundled_service_shutdown_closes_owned_port_and_reports_only_operator_url(service, tmp_path, monkeypatch, capsys):
    import socket

    builder = service._load_builder()
    bundled = builder._load_server()
    inventory = builder.build_inventory(tmp_path, project=None, include_user=False)
    owned = []

    def stop_after_start(server, *, poll_interval):
        assert server.server_address[0] == '127.0.0.1'
        owned.append(server)
        raise KeyboardInterrupt

    monkeypatch.setattr(bundled.PanelServer, 'serve_forever', stop_after_start)
    assert bundled.run(tmp_path, inventory) == 0
    message = json.loads(capsys.readouterr().out)
    server = owned[0]
    assert message == {'status': 'serving',
                       'url': f'http://127.0.0.1:{server.server_port}' + server.access_prefix,
                       'catalog': 'startup_snapshot', 'progress': 'canonical_ledger'}
    assert server.socket.fileno() == -1
    with socket.socket() as probe:
        probe.settimeout(1)
        assert probe.connect_ex(('127.0.0.1', server.server_port)) != 0
