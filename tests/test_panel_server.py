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


@pytest.mark.parametrize('args', [['--serve'], ['--serve', '--project', '.', '--export', 'salida'],
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


# --- T-11: servidor multi-página, activos de lista blanca y nonce en todo <script> -----------------------

import re
import shutil

PAGINAS = ['index.html', 'iniciativas.html', 'plan.html', 'agentes.html', 'memoria.html', 'catalogo.html', 'diagnostico.html']
ACTIVOS_ESTATICOS = ['assets/panel.css', 'assets/panel-core.js', 'assets/panel-charts.js', 'assets/page-catalogo.js',
                     'assets/page-diagnostico.js', 'assets/panel-live.js', 'assets/panel-memory.js',
                     'assets/panel-activity.js', 'assets/page-cartera.js', 'assets/page-inicio.js',
                     'assets/page-iniciativas.js', 'assets/page-plan.js', 'vendor/chart.js/chart.umd.min.js']


@pytest.mark.parametrize('pagina', PAGINAS)
def test_http_sirve_cada_pagina_con_su_csp_y_el_nonce_en_cada_script(http_server, pagina):
    status, headers, body = request(http_server, pagina)
    assert status == 200 and headers['Content-Type'] == 'text/html; charset=utf-8'
    html = body.decode('utf8')
    csp = headers['Content-Security-Policy']
    nonce = re.search(r"script-src 'nonce-([A-Za-z0-9_-]+)'", csp).group(1)
    assert csp == ("default-src 'none'; style-src 'self' 'unsafe-inline'; script-src 'nonce-" + nonce
                   + "'; img-src data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
    etiquetas = re.findall(r'<script\b[^>]*>', html)
    assert etiquetas and all(f'nonce="{nonce}"' in etiqueta for etiqueta in etiquetas)
    assert '<script>' not in html and '<link rel="icon" href="data:,">' in html
    assert not re.search(r'\son[a-z]+\s*=', html)


def test_http_la_raiz_del_token_es_la_pagina_de_inicio(http_server):
    assert request(http_server)[2] == request(http_server, 'index.html')[2]


@pytest.mark.parametrize('activo', ACTIVOS_ESTATICOS)
def test_http_sirve_los_activos_de_la_lista_blanca(http_server, activo):
    status, headers, body = request(http_server, activo)
    esperado = (ROOT / 'skills/plugin-panel' / ('' if activo.startswith('assets/') else 'assets') / activo).read_bytes()
    assert status == 200 and body == esperado
    assert headers['Content-Type'].split(';')[0] == ('text/css' if activo.endswith('.css') else 'text/javascript')
    assert headers['Cache-Control'] == 'no-store' and headers['X-Content-Type-Options'] == 'nosniff'


@pytest.mark.parametrize('suffix', ['assets/serve_panel.py', 'assets/../scripts/serve_panel.py', 'assets/', 'assets',
                                    'vendor/', 'vendor/chart.js/', 'vendor/chart.js/otro.js', 'assets/panel-review.js',
                                    'scripts/build_panel.py', 'catalogo', 'catalogo.html/', 'Catalogo.html',
                                    'plan-0123456789abcdef.html', 'plan-xyz.html', 'plan-0123456789abcdef0.html',
                                    'api/memory', 'api/activity/x'])
def test_http_activo_o_pagina_fuera_de_la_lista_blanca_es_404(http_server, suffix):
    assert request(http_server, suffix)[0] in (404, 405)


@pytest.mark.parametrize('suffix', ['catalogo.html?x=1', 'catalogo.html#a', 'assets%2Fpanel.css', 'assets\\panel.css',
                                    'assets/panel.css?v=1', 'assets/panel%2ecss'])
def test_http_sigue_rechazando_consulta_porcentaje_barra_inversa_y_ancla(http_server, suffix):
    assert request(http_server, target=http_server.access_prefix + suffix)[0] == 404


@pytest.mark.parametrize('headers', [{'Host': 'outside.invalid'}, {'Origin': 'null'}, {'Origin': 'https://outside.invalid'},
                                     {'Sec-Fetch-Site': 'cross-site'}])
@pytest.mark.parametrize('suffix', ['catalogo.html', 'assets/panel.css'])
def test_http_paginas_y_activos_exigen_host_y_origen_propios(http_server, suffix, headers):
    assert request(http_server, suffix, headers=headers)[0] == 403


def test_http_paginas_y_activos_sin_token_o_con_otro_token_dan_404_sin_contenido(http_server):
    for objetivo in ('/catalogo.html', '/assets/panel.css', '/' + 'A' * 43 + '/catalogo.html'):
        status, _, body = request(http_server, target=objetivo)
        assert status == 404 and b'Piezas por tipo' not in body and b'.card' not in body


def test_http_head_de_una_pagina_y_de_un_activo(http_server):
    for suffix in ('catalogo.html', 'assets/panel.css'):
        status, headers, body = request(http_server, suffix, method='HEAD')
        assert status == 200 and body == b'' and int(headers['Content-Length']) > 0


def test_http_no_lee_disco_por_peticion(http_server, monkeypatch):
    import builtins
    real_open = builtins.open
    monkeypatch.setattr(builtins, 'open', lambda *a, **k: pytest.fail('lectura de disco al servir'))
    monkeypatch.setattr(Path, 'read_bytes', lambda *a, **k: pytest.fail('lectura de disco al servir'))
    monkeypatch.setattr(Path, 'read_text', lambda *a, **k: pytest.fail('lectura de disco al servir'))
    for suffix in ('catalogo.html', 'assets/panel-core.js', 'vendor/chart.js/chart.umd.min.js'):
        assert request(http_server, suffix)[0] == 200
    monkeypatch.setattr(builtins, 'open', real_open)


def test_http_plan_por_iniciativa_solo_se_sirve_si_esta_registrado(http_server):
    identificador = 'plan-0123456789abcdef.html'
    assert request(http_server, identificador)[0] == 404
    http_server.plan_pages[identificador] = b'<p>plan registrado</p>'
    status, headers, body = request(http_server, identificador)
    assert status == 200 and body == b'<p>plan registrado</p>' and headers['Content-Type'].startswith('text/html')
    assert request(http_server, 'plan-aaaaaaaaaaaaaaaa.html')[0] == 404


def test_http_cada_pagina_carga_solo_sus_scripts_vivos(http_server):
    def scripts(pagina):
        return re.findall(r'<script nonce="[^"]+" src="([^"]+)"', request(http_server, pagina)[2].decode('utf8'))
    assert 'assets/panel-live.js' in scripts('index.html') and 'assets/panel-live.js' in scripts('plan.html')
    assert 'assets/panel-activity.js' in scripts('agentes.html') and 'assets/panel-memory.js' in scripts('memoria.html')
    assert 'assets/panel-review.js' not in scripts('plan.html')  # sin revisión seleccionada
    assert 'assets/page-catalogo.js' in scripts('catalogo.html') and 'assets/page-diagnostico.js' in scripts('diagnostico.html')
    assert not any('panel-live' in s or 'panel-memory' in s for s in scripts('catalogo.html'))


def _copia_de_assets(tmp_path):
    destino = tmp_path / 'assets-copia'
    shutil.copytree(ROOT / 'skills/plugin-panel/assets', destino)
    return destino


def _servidor_con_assets(service, tmp_path, monkeypatch, assets, **kwargs):
    builder = service._load_builder()
    monkeypatch.setattr(builder._load_pages(), 'ASSETS_DIR', assets)
    monkeypatch.setattr(service, '_load_builder', lambda: builder)  # el servidor usa el builder ya parcheado
    inventory = builder.build_inventory(tmp_path, project=None)
    return service.create_server(tmp_path, inventory, **kwargs)


def test_http_chart_con_huella_distinta_se_sirve_sin_chart_y_con_aviso(service, tmp_path, monkeypatch):
    assets = _copia_de_assets(tmp_path)
    with open(assets / 'vendor/chart.js/chart.umd.min.js', 'ab') as chart:
        chart.write(b'\n/* alterado */')
    server = _servidor_con_assets(service, tmp_path, monkeypatch, assets)
    try:
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        pagina = request(server, 'catalogo.html')[2].decode('utf8')
        datos = json.loads(re.search(r'id="panel-data">(.*?)</script>', pagina, re.S).group(1))
        assert 'chart.umd.min.js' not in pagina and datos['chartjs_disponible'] is False
        assert request(server, 'vendor/chart.js/chart.umd.min.js')[0] == 404
        assert server.warnings and 'Chart.js' in server.warnings[0]
        assert request(server, 'assets/panel-charts.js')[0] == 200
    finally:
        server.shutdown(); server.server_close()


def test_http_sin_chart_el_arranque_no_falla(service, tmp_path, monkeypatch):
    assets = _copia_de_assets(tmp_path)
    shutil.rmtree(assets / 'vendor')
    server = _servidor_con_assets(service, tmp_path, monkeypatch, assets)
    try:
        assert 'chart.umd.min.js' not in server.pages['catalogo.html'].decode('utf8') and server.warnings
    finally:
        server.server_close()


@pytest.mark.parametrize('faltante', ['panel-live.js', 'panel-memory.js'])
def test_asset_vivo_obligatorio_ausente_es_un_error_opaco_y_no_deja_el_puerto_abierto(service, tmp_path, monkeypatch, faltante):
    assets = _copia_de_assets(tmp_path)
    (assets / faltante).unlink()
    with pytest.raises(ValueError, match='bundled live panel asset unavailable'):
        _servidor_con_assets(service, tmp_path, monkeypatch, assets)


def test_actividad_ausente_degrada_solo_esa_pagina(service, tmp_path, monkeypatch):
    assets = _copia_de_assets(tmp_path)
    (assets / 'panel-activity.js').unlink()
    server = _servidor_con_assets(service, tmp_path, monkeypatch, assets)
    try:
        agentes = server.pages['agentes.html'].decode('utf8')
        assert 'falta el recurso local de esta vista' in agentes and 'panel-activity.js' not in agentes
        assert 'assets/panel-activity.js' not in server.assets and 'panel-live.js' in server.pages['index.html'].decode('utf8')
    finally:
        server.server_close()


def test_la_pagina_de_plan_lleva_la_revision_cuando_hay_seleccion(service, tmp_path, monkeypatch):
    assets = _copia_de_assets(tmp_path)
    (assets / 'panel-review.js').unlink()
    builder = service._load_builder()
    monkeypatch.setattr(builder._load_pages(), 'ASSETS_DIR', assets)
    monkeypatch.setattr(service, '_load_builder', lambda: builder)
    seleccion = {'initiative': 'docs/roadmap/x', 'state_root': str(tmp_path / 'estado')}
    with pytest.raises(ValueError, match='bundled review panel asset unavailable'):
        service.create_server(tmp_path, builder.build_inventory(tmp_path, project=None), review_selection=seleccion)


# --- T-17: api/cartera ------------------------------------------------------------------------------------

def test_http_api_cartera_proyecta_el_ledger_con_las_cifras_de_progress_report(http_server):
    status, headers, raw = request(http_server, 'api/cartera')
    assert status == 200 and headers['Content-Type'] == 'application/json; charset=utf-8'
    assert headers['Cache-Control'] == 'no-store' and len(raw) <= 65536
    datos = json.loads(raw)
    fila, = datos['iniciativas']
    assert fila['tareas'] == {'total': 2, 'completadas': 1, 'pct': 50} and fila['ledger'] == 'ok'
    assert fila['categoria'] == 'sin_spec' and fila['horas']['real'] is None and fila['coste']['real_eur'] is None
    assert datos['totales']['tareas'] == {'completadas': 1, 'total': 2, 'pct': 50, 'ledgers': 1}
    assert http_server.access_prefix.encode() not in raw and b'tasks.md' not in raw


@pytest.mark.parametrize('suffix', ['api/cartera?x=1', 'api/cartera/', 'api/Cartera', 'api/cartera.json'])
def test_http_api_cartera_solo_la_ruta_exacta_y_sin_consulta(http_server, suffix):
    assert request(http_server, suffix)[0] == 404


@pytest.mark.parametrize('method', ['POST', 'PUT', 'DELETE'])
def test_http_api_cartera_es_solo_lectura(http_server, method):
    assert request(http_server, 'api/cartera', method=method)[0] == 405


def test_http_api_cartera_cae_en_unavailable_sin_filtrar_la_causa(service, tmp_path, monkeypatch):
    ledger(tmp_path)
    monkeypatch.setattr(service, '_load_data', lambda: (_ for _ in ()).throw(ImportError('/ruta/privada')))
    server = service.create_server(tmp_path, service._load_builder().build_inventory(tmp_path, project=None))
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        status, _, raw = request(server, 'api/cartera')
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=5)
    datos = json.loads(raw)
    assert status == 200 and datos['status'] == 'unavailable' and datos['iniciativas'] == []
    assert b'/ruta/privada' not in raw


def test_http_api_cartera_pasa_por_el_saneador_unico_del_servidor(service, tmp_path):
    carpeta = tmp_path / 'docs/roadmap/2026-10-09-example'
    ledger(tmp_path)
    (carpeta / 'spec.md').write_text('---\nestado: aprobada\n---\n# Plan de jdoeuser en /home/jdoeuser/notas\n', encoding='utf8')
    redact = service._load_shared('redact.py')
    scrub = lambda t: redact.anonimizar(redact.redactar(t), None, '/home/jdoeuser', 'jdoeuser')
    server = service.create_server(tmp_path, service._load_builder().build_inventory(tmp_path, project=None), scrub=scrub)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        raw = request(server, 'api/cartera')[2]
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=5)
    assert b'jdoeuser' not in raw and b'/home/' not in raw and '<usuario>'.encode() in raw


# --- fix1 de la Fase 2: cachés por firma (F2-4, F2-13) ----------------------------------------------------------------

def _server_con_plan(service, tmp_path):
    carpeta = tmp_path / 'docs/roadmap/2026-10-09-example'
    ledger(tmp_path)
    (carpeta / 'spec.md').write_text('---\nestado: aprobada\n---\n# Spec\n', encoding='utf8')
    (carpeta / 'improvement-plan.md').write_text('# Plan\n', encoding='utf8')
    server = service.create_server(tmp_path, service._load_builder().build_inventory(tmp_path, project=None))
    ident = hashlib.sha256(b'2026-10-09-example').hexdigest()[:16]
    return server, carpeta, ident


def test_la_cartera_no_se_recalcula_si_nada_cambio_y_un_cambio_de_ledger_si_se_ve(service, tmp_path, monkeypatch):
    """F2-4: dos peticiones seguidas (pasado el TTL) sin cambios no recalculan; un cambio de ledger se ve."""
    server, carpeta, _ = _server_con_plan(service, tmp_path)
    try:
        data = service._load_data()
        llamadas = []
        real = data.cartera
        data.cartera = lambda project: (llamadas.append(1), real(project))[1]
        monkeypatch.setattr(service, '_load_data', lambda: data)
        primera = json.loads(server.cartera())
        assert len(llamadas) == 1 and primera['iniciativas'][0]['tareas']['total'] == 2
        server._cartera_at -= 30                                  # caducó el TTL corto, pero el roadmap es el mismo
        assert json.loads(server.cartera()) == primera and len(llamadas) == 1
        (carpeta / 'tasks.md').write_text((carpeta / 'tasks.md').read_text(encoding='utf8')
                                          + '### T-03 — Extra\n- **Estado**: borrador\n', encoding='utf8')
        server._cartera_at -= 30
        despues = json.loads(server.cartera())
        assert len(llamadas) == 2 and despues['iniciativas'][0]['tareas']['total'] == 3
    finally:
        server.server_close()


def test_la_firma_de_la_cartera_cambia_con_un_artefacto_y_con_una_carpeta_nueva(service, tmp_path):
    ledger(tmp_path)
    data = service._load_data()
    antes = data.cartera_firma(tmp_path)
    assert antes == data.cartera_firma(tmp_path)
    (tmp_path / 'docs/roadmap/2026-10-10-otra').mkdir()
    assert data.cartera_firma(tmp_path) != antes


def test_el_detalle_de_una_tarea_no_sirve_la_copia_anterior_tras_cambiar_el_ledger(service, tmp_path):
    """F2-13: el cambio de fila en el ledger se ve en la petición siguiente, dentro de la ventana de caché."""
    server, carpeta, ident = _server_con_plan(service, tmp_path)
    try:
        antes = json.loads(server.tarea(ident, 'T-02'))['tarea']
        assert antes['estado_tarea'] == 'en-progreso'
        texto = (carpeta / 'tasks.md').read_text(encoding='utf8').replace(
            'Build feature\n- **Estado**: en-progreso', 'Build feature\n- **Estado**: completado')
        (carpeta / 'tasks.md').write_text(texto, encoding='utf8')
        assert json.loads(server.tarea(ident, 'T-02'))['tarea']['estado_tarea'] == 'completado'
        assert [t['estado_tarea'] for t in json.loads(server.plan(ident))['tareas']] == ['completado', 'completado']
    finally:
        server.server_close()
