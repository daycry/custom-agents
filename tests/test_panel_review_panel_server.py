"""Panel-wide review routes (`review_scope`): summary, current review and browser-side open (T-56)."""
import hashlib
import http.client
import importlib.util
import json
from pathlib import Path
import threading
import types

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/plugin-panel/scripts/serve_panel.py'
OWNER_SCRIPT = Path(__file__).resolve().parents[1] / 'agent-kits/shared/plan-review.py'
DATA = {'counts': dict.fromkeys(('agents', 'skills', 'commands', 'tools', 'hooks'), 0),
        'agents': [], 'skills': [], 'commands': [], 'tools': [], 'hooks': [],
        'runtimes': {}, 'memory': {}, 'warnings': [], 'workflow': {'roles': {}}}
FOLDER = '2026-10-09-alpha'
INITIATIVE = 'docs/roadmap/' + FOLDER
IDENT = hashlib.sha256(FOLDER.encode()).hexdigest()[:16]
OTHER = '2026-10-10-beta'
OTHER_ID = hashlib.sha256(OTHER.encode()).hexdigest()[:16]
RID = 'a' * 64


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


@pytest.fixture
def service():
    return load(SCRIPT, 'panel_scope_transport')


def make_project(tmp_path):
    for folder in (FOLDER, OTHER):
        plan = tmp_path / 'docs/roadmap' / folder / 'improvement-plan.md'
        plan.parent.mkdir(parents=True); plan.write_text('# Plan\n## Cambio\nValidar.\n', encoding='utf8')
        (plan.parent / 'spec.md').write_text('---\nestado: aprobada\n---\n# Spec\n', encoding='utf8')
    (tmp_path / 'docs/roadmap/2026-10-11-sinplan').mkdir()
    (tmp_path / 'docs/roadmap/README.md').write_text('indice', encoding='utf8')
    (tmp_path / '.claude').mkdir()
    return tmp_path


def fake_owner(calls, *, gate='requested-review', rid=RID, estado='pendiente'):
    def summarize(project, initiatives, **kwargs):
        calls.append(('summarize_reviews', tuple(initiatives), kwargs))
        rows = [{'initiative': i, 'estado': estado if i == INITIATIVE else 'sin_revision', 'version_ordinal': 1,
                 'gate_key': gate, 'review_state': 'pendiente', 'plan': 'ok', 'comments': 0,
                 'comments_with_result': 0, 'needs_clarification': 0, 'results_without_verification': 0,
                 'other_current_reviews': 0, 'review_id': rid if i == INITIATIVE else None} for i in initiatives]
        return {'schema_version': 1, 'status': 'ok', 'reason': None, 'complete': True, 'observed_at': 'x',
                'initiatives': rows, 'omitted': 0, 'approval_granted': False}
    def open_review(project, initiative, **kwargs):
        calls.append(('open_review', (initiative,), kwargs))
        return {'schema_version': 1, 'status': 'ok', 'reason': None,
                'review': {'review_id': hashlib.sha256(initiative.encode()).hexdigest(), 'revision': 0}}
    def other(name):
        def invoke(*args, **kwargs):
            calls.append((name, args, kwargs)); return {'schema_version': 1, 'status': 'ok', 'reason': None, 'review': {'review_id': args[1]}}
        return invoke
    return types.SimpleNamespace(summarize_reviews=summarize, open_review=open_review,
        **{n: other(n) for n in ('get_view', 'get_status', 'save_comments', 'submit_decision')})


def run_server(service, monkeypatch, tmp_path, owner, **extra):
    monkeypatch.setattr(service, '_load_review', lambda: owner, raising=False)
    server = service.create_server(make_project(tmp_path), DATA,
        review_scope={'state_root': tmp_path / '.claude/plan-review'}, **extra)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    return server, thread


@pytest.fixture
def scoped(service, tmp_path, monkeypatch):
    calls = []
    server, thread = run_server(service, monkeypatch, tmp_path, fake_owner(calls))
    server.calls = calls
    yield server
    server.shutdown(); server.server_close(); thread.join(5)
    assert not thread.is_alive() and server.socket.fileno() == -1


def send(server, route, payload=None, *, method='GET', raw=None, headers=None, early=False, prefix=None):
    connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
    body = raw if raw is not None else json.dumps(payload).encode() if payload is not None else None
    hdrs = {'Content-Type': 'application/json', **(headers or {})}
    early = body is not None and (early or method != 'POST' or prefix is not None or route.endswith('0' * 16)
        or any(k in hdrs for k in ('Host', 'Origin', 'Sec-Fetch-Site')) or hdrs['Content-Type'] != 'application/json'
        or len(body) > 16384 or route == 'api/review-summary')
    if early and body is not None:
        hdrs['Content-Length'] = str(len(body)); body = None
    connection.request(method, (server.access_prefix if prefix is None else prefix) + route, body, hdrs)
    response = connection.getresponse(); result = response.status, dict(response.getheaders()), response.read()
    connection.close(); return result


def open_body(ident=IDENT):
    return {'initiative_id': ident}


def test_summary_is_keyed_by_id16_without_paths_or_review_ids(scoped):
    code, headers, raw = send(scoped, 'api/review-summary')
    body = json.loads(raw)
    assert code == 200 and body['status'] == 'ok' and body['approval_granted'] is False
    assert {row['initiative_id'] for row in body['initiatives']} == {IDENT, OTHER_ID}
    assert 'docs/roadmap' not in raw.decode() and RID not in raw.decode() and 'review_id' not in raw.decode()
    assert len(raw) <= 65536 and 'nonce-' in headers['Content-Security-Policy'] and 'Set-Cookie' not in headers
    # the folder without a plan and the index file are not initiatives
    assert scoped.calls[0][1] == (INITIATIVE, 'docs/roadmap/' + OTHER)


def test_current_registers_requested_review_with_write_and_plan_ok_read_only(service, tmp_path, monkeypatch):
    calls = []
    server, thread = run_server(service, monkeypatch, tmp_path, fake_owner(calls, gate='plan-ok'))
    try:
        body = json.loads(send(server, 'api/review-current/' + IDENT)[2])
        assert body['review_id'] == RID and body['estado'] == 'pendiente' and body['escritura'] is False
        assert server.review_registry[RID]['gate_key'] == 'plan-ok'
        # readable, but no write route: 405 and the owner is not called
        before = len(calls)
        assert send(server, 'api/review/' + RID + '/view')[0] == 200
        payload = {'review_id': RID}
        assert send(server, 'api/review/' + RID + '/refresh', payload, method='POST', early=True)[0] == 405
        assert len(calls) == before + 1 and calls[-1][0] == 'get_view'
    finally:
        server.shutdown(); server.server_close(); thread.join(5)


def test_current_write_for_requested_review_and_unknown_id_is_404(scoped):
    body = json.loads(send(scoped, 'api/review-current/' + IDENT)[2])
    assert body['escritura'] is True and body['review_id'] == RID and scoped.review_registry[RID]['initiative'] == INITIATIVE
    before = len(scoped.calls)
    assert send(scoped, 'api/review-current/' + '0' * 16)[0] == 404 and len(scoped.calls) == before


def test_open_uses_literal_gate_and_registers_owner_id(scoped):
    code, _, raw = send(scoped, 'api/review-open/' + IDENT, open_body(), method='POST')
    body = json.loads(raw)
    name, args, kwargs = scoped.calls[-1]
    assert code == 200 and name == 'open_review' and args == (INITIATIVE,)
    assert kwargs['gate_key'] == 'requested-review' and kwargs['consumer'] is None
    assert body['escritura'] is True and body['review_id'] in scoped.review_registry
    assert scoped.review_registry[body['review_id']]['gate_key'] == 'requested-review'
    # the registered id works with the existing write routes
    assert send(scoped, 'api/review/' + body['review_id'] + '/refresh', {'review_id': body['review_id']}, method='POST')[0] == 200
    assert scoped.calls[-1][0] == 'open_review' and scoped.calls[-1][2]['gate_key'] == 'requested-review'


def test_open_unknown_id16_is_404_without_loading_the_owner(service, tmp_path, monkeypatch):
    monkeypatch.setattr(service, '_load_review', lambda: pytest.fail('owner loaded'), raising=False)
    server = service.create_server(make_project(tmp_path), DATA, review_scope={'state_root': tmp_path / '.claude/plan-review'})
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        assert send(server, 'api/review-open/' + '0' * 16, open_body('0' * 16), method='POST')[0] == 404
        assert not (tmp_path / '.claude/plan-review').exists()
    finally:
        server.shutdown(); server.server_close(); thread.join(5)


@pytest.mark.parametrize('payload', [{}, {'initiative_id': IDENT, 'gate_key': 'plan-ok'}, {'gate_key': 'plan-ok'},
    {'initiative_id': OTHER_ID}, {'initiative_id': 5}, [], None, {'initiative_id': IDENT, 'x': 1}])
def test_open_rejects_any_other_body_without_calling_the_owner(scoped, payload):
    before = len(scoped.calls)
    raw = json.dumps(payload).encode()
    assert send(scoped, 'api/review-open/' + IDENT, raw=raw, method='POST')[0] == 400
    assert len(scoped.calls) == before


def test_open_rejects_duplicate_fields_and_bad_transport(scoped):
    before = len(scoped.calls)
    raw = ('{"initiative_id":"%s","initiative_id":"%s"}' % (IDENT, IDENT)).encode()
    assert send(scoped, 'api/review-open/' + IDENT, raw=raw, method='POST')[0] == 400
    assert send(scoped, 'api/review-open/' + IDENT, open_body(), method='POST', headers={'Origin': 'http://evil.test'})[0] == 403
    assert send(scoped, 'api/review-open/' + IDENT, open_body(), method='POST', headers={'Sec-Fetch-Site': 'cross-site'})[0] == 403
    assert send(scoped, 'api/review-open/' + IDENT, open_body(), method='POST', headers={'Host': 'evil.test'})[0] == 403
    assert send(scoped, 'api/review-open/' + IDENT, open_body(), method='POST', headers={'Content-Type': 'text/plain'})[0] == 415
    assert send(scoped, 'api/review-open/' + IDENT, raw=b'{"initiative_id":"' + b'a' * 17000 + b'"}', method='POST')[0] == 413
    assert send(scoped, 'api/review-open/' + IDENT, open_body(), method='POST', prefix='/' + 'x' * 43 + '/')[0] == 404
    assert len(scoped.calls) == before


def test_new_routes_have_no_other_methods_and_summary_is_not_writable(scoped):
    before = len(scoped.calls)
    assert send(scoped, 'api/review-summary', {}, method='POST')[0] == 405
    assert send(scoped, 'api/review-open/' + IDENT)[0] == 404
    for method in ('PUT', 'DELETE', 'PATCH'):
        assert send(scoped, 'api/review-open/' + IDENT, open_body(), method=method)[0] == 405
    assert len(scoped.calls) == before


def test_registry_cap_is_explicit_and_only_owner_ids_enter(service, tmp_path, monkeypatch):
    calls = []
    server, thread = run_server(service, monkeypatch, tmp_path, fake_owner(calls))
    try:
        for n in range(service.MAX_REVIEW_IDS):
            server.review_registry[format(n, '064x')] = {'initiative': 'docs/roadmap/x', 'gate_key': 'plan-ok',
                                                        'consumer': None, 'escritura': False}
        code, _, raw = send(server, 'api/review-open/' + IDENT, open_body(), method='POST')
        body = json.loads(raw)
        assert code == 429 and 'demasiadas revisiones abiertas en este proceso' in body['message']
        assert len(server.review_registry) == service.MAX_REVIEW_IDS and not any(c[0] == 'open_review' for c in calls)
        assert json.loads(send(server, 'api/review-current/' + IDENT)[2])['reason'] == 'too_many_reviews'
        # a request body can never add an id
        assert send(server, 'api/review/' + 'e' * 64 + '/view')[0] == 404
    finally:
        server.shutdown(); server.server_close(); thread.join(5)


def test_selection_keeps_write_and_scope_does_not_change_it(service, tmp_path, monkeypatch):
    calls = []
    selection = {'initiative': INITIATIVE, 'state_root': tmp_path / '.claude/plan-review', 'gate_key': 'plan-ok',
                 'consumer': {'caller_id': 'dev-cycle', 'runtime': 'codex'}}
    owner = fake_owner(calls)
    monkeypatch.setattr(service, '_load_review', lambda: owner, raising=False)
    server = service.create_server(make_project(tmp_path), DATA, review_selection=selection,
                                   review_scope={'state_root': selection['state_root']})
    try:
        rid, = server.review_ids
        assert server.review_registry[rid] == {'initiative': INITIATIVE, 'gate_key': 'plan-ok',
            'consumer': selection['consumer'], 'escritura': True}
        with pytest.raises(ValueError, match='invalid review scope'):
            service.create_server(tmp_path, DATA, review_selection=selection, review_scope={'state_root': tmp_path / 'otra'})
    finally:
        server.server_close()


def test_scope_must_be_exactly_a_state_root(service, tmp_path, monkeypatch):
    monkeypatch.setattr(service, '_load_review', lambda: pytest.fail('invalid scope loaded owner'), raising=False)
    for scope in ([], {}, {'state_root': 'x', 'initiative': 'y'}):
        with pytest.raises(ValueError, match='invalid review scope'):
            service.create_server(tmp_path, DATA, review_scope=scope)


def test_no_scope_has_no_new_routes(service, tmp_path, monkeypatch):
    monkeypatch.setattr(service, '_load_review', lambda: pytest.fail('ordinary server opened review'), raising=False)
    server = service.create_server(make_project(tmp_path), DATA)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        assert send(server, 'api/review-summary')[0] == 404
        assert send(server, 'api/review-current/' + IDENT)[0] == 404
        assert send(server, 'api/review-open/' + IDENT, open_body(), method='POST')[0] == 405
    finally:
        server.shutdown(); server.server_close(); thread.join(5)


def test_owner_failure_degrades_without_stack_or_paths(service, tmp_path, monkeypatch):
    def broken(): raise ImportError('SECRET outside/root')
    monkeypatch.setattr(service, '_load_review', broken, raising=False)
    server = service.create_server(make_project(tmp_path), DATA, review_scope={'state_root': tmp_path / '.claude/plan-review'})
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        code, _, raw = send(server, 'api/review-summary')
        assert code == 200 and json.loads(raw)['status'] == 'unavailable' and b'SECRET' not in raw
        assert json.loads(send(server, 'api/review-current/' + IDENT)[2])['status'] == 'unavailable'
        assert send(server, 'api/review-open/' + IDENT, open_body(), method='POST')[0] == 503
    finally:
        server.shutdown(); server.server_close(); thread.join(5)


def test_real_owner_open_then_summary_and_current(service, tmp_path):
    project = make_project(tmp_path)
    server = service.create_server(project, DATA, review_scope={'state_root': project / '.claude/plan-review'})
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        code, _, raw = send(server, 'api/review-open/' + IDENT, open_body(), method='POST')
        opened = json.loads(raw)
        assert code == 200 and opened['status'] == 'ok' and len(opened['review_id']) == 64
        rows = {r['initiative_id']: r for r in json.loads(send(server, 'api/review-summary')[2])['initiatives']}
        assert rows[OTHER_ID]['estado'] == 'sin_revision'
        server._review_summary = None
        rows = {r['initiative_id']: r for r in json.loads(send(server, 'api/review-summary')[2])['initiatives']}
        assert rows[IDENT]['estado'] == 'pendiente' and rows[IDENT]['gate_key'] == 'requested-review'
        current = json.loads(send(server, 'api/review-current/' + IDENT)[2])
        assert current['review_id'] == opened['review_id'] and current['escritura'] is True
        view = json.loads(send(server, 'api/review/' + opened['review_id'] + '/view')[2])
        assert view['status'] == 'ok'
    finally:
        server.shutdown(); server.server_close(); thread.join(5)


def test_id16_collisions_and_invalid_folders_leave_the_map(service, tmp_path, monkeypatch):
    project = make_project(tmp_path)
    (project / 'docs/roadmap/Bad_Name').mkdir()
    (project / 'docs/roadmap/Bad_Name/improvement-plan.md').write_text('x', encoding='utf8')
    real = hashlib.sha256
    class Fake:
        def __init__(self, data): self.h = real(data); self.data = data
        def hexdigest(self): return 'c' * 64 if self.data.decode().startswith(('2026-10-09', '2026-10-10')) else self.h.hexdigest()
    monkeypatch.setattr(service, 'hashlib', types.SimpleNamespace(sha256=Fake))
    assert service.review_initiatives(project) == {}
    monkeypatch.undo()
    assert set(service.review_initiatives(project).values()) == {INITIATIVE, 'docs/roadmap/' + OTHER}


def test_scope_serves_review_js_and_the_plan_button_without_the_legacy_section(scoped):
    page = send(scoped, 'plan-' + IDENT + '.html')[2].decode()
    assert 'id="plan-revisar"' in page and 'assets/panel-review.js' in page and 'data-revision="activa"' in page
    assert send(scoped, 'assets/panel-review.js')[0] == 200
    index = send(scoped, 'plan.html')[2].decode()
    assert 'id="plan-review"' not in index and 'id="plan-revisar"' not in index


def test_without_scope_the_plan_explains_activation_and_review_js_is_not_served(service, tmp_path, monkeypatch):
    monkeypatch.setattr(service, '_load_review', lambda: pytest.fail('ordinary server opened review'), raising=False)
    server = service.create_server(make_project(tmp_path), DATA)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        page = send(server, 'plan-' + IDENT + '.html')[2].decode()
        assert '--review-panel --review-state-root &lt;proyecto&gt;/.claude/plan-review' in page
        assert 'id="plan-revisar"' not in page and 'panel-review.js' not in page
        assert send(server, 'assets/panel-review.js')[0] == 404
    finally:
        server.shutdown(); server.server_close(); thread.join(5)


def test_new_responses_carry_only_closed_vocabulary_and_no_free_text(scoped):
    """Contract for `test_panel_fix4`: the three new APIs return ids, numbers and closed words, never user text or paths,
    so they bypass `_scrubbed` on purpose; an unlisted key fails here and must be classified there."""
    summary = json.loads(send(scoped, 'api/review-summary')[2])
    assert set(summary) == {'schema_version', 'status', 'reason', 'complete', 'observed_at', 'initiatives', 'omitted', 'approval_granted'}
    allowed = {'initiative_id', 'estado', 'version_ordinal', 'gate_key', 'review_state', 'plan', 'comments', 'comments_with_result',
               'needs_clarification', 'results_without_verification', 'other_current_reviews'}
    assert all(set(row) == allowed for row in summary['initiatives'])
    current = json.loads(send(scoped, 'api/review-current/' + IDENT)[2])
    assert set(current) == {'schema_version', 'status', 'reason', 'initiative_id', 'review_id', 'estado', 'version_ordinal', 'gate_key', 'escritura'}
    opened = json.loads(send(scoped, 'api/review-open/' + IDENT, open_body(), method='POST')[2])
    assert set(opened) == {'schema_version', 'status', 'reason', 'initiative_id', 'review_id', 'escritura'}


# --- fix1 de la Fase 2: caché por firma, lotes, registro lleno, carrera del mapa, páginas no revisables ------------------

def _escribe_registro(project, nombre='r-x.json', texto='{}'):
    carpeta = project / '.claude/plan-review'
    carpeta.mkdir(parents=True, exist_ok=True)
    (carpeta / nombre).write_text(texto, encoding='utf8')


def _envejece(server, segundos=8):
    server._review_summary_at -= segundos
    server._review_current_at = {k: v - segundos for k, v in server._review_current_at.items()}


def test_summary_y_current_no_vuelven_al_dueno_si_nada_cambio_y_un_cambio_se_ve(service, tmp_path, monkeypatch):
    """F2-10/F2-11: pasado el TTL corto, la misma firma del estado y de los planes reutiliza la respuesta."""
    calls = []
    server, thread = run_server(service, monkeypatch, tmp_path, fake_owner(calls))
    try:
        send(server, 'api/review-summary'); send(server, 'api/review-current/' + IDENT)
        base = len(calls)
        _envejece(server)
        send(server, 'api/review-summary'); send(server, 'api/review-current/' + IDENT)
        assert len(calls) == base                                  # nada cambió: ni summarize ni review-current al dueño
        _escribe_registro(tmp_path)                                # el estado de revisiones cambió
        _envejece(server)
        send(server, 'api/review-summary'); send(server, 'api/review-current/' + IDENT)
        assert len(calls) == base + 2
    finally:
        server.shutdown(); server.server_close(); thread.join(5)


def test_summary_con_mas_de_64_planes_pide_al_dueno_en_lotes(service, tmp_path, monkeypatch):
    """F2-12: el dueño rechaza > 64 iniciativas por llamada; el servidor reparte en lotes y no da `invalid_input`."""
    calls = []
    inner = fake_owner(calls)

    def summarize(project, initiatives, **kwargs):
        if len(initiatives) > 64:
            return {'schema_version': 1, 'status': 'unavailable', 'reason': 'invalid_input', 'complete': False,
                    'observed_at': 'x', 'initiatives': [], 'omitted': 0, 'approval_granted': False}
        return inner.summarize_reviews(project, initiatives, **kwargs)
    owner = types.SimpleNamespace(**{**vars(inner), 'summarize_reviews': summarize})
    monkeypatch.setattr(service, '_load_review', lambda: owner, raising=False)
    project = make_project(tmp_path)
    for n in range(70):
        plan = project / 'docs/roadmap' / f'2026-11-{n % 28 + 1:02d}-extra{n}' / 'improvement-plan.md'
        plan.parent.mkdir(parents=True)
        plan.write_text('# p\n', encoding='utf8')
    server = service.create_server(project, DATA, review_scope={'state_root': project / '.claude/plan-review'})
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        body = json.loads(send(server, 'api/review-summary')[2])
        assert body['status'] == 'ok' and body['complete'] is True and body['reason'] is None
        assert len(body['initiatives']) == 72 and body['omitted'] == 0
        assert {len(c[1]) for c in calls if c[0] == 'summarize_reviews'} == {64, 8}
    finally:
        server.shutdown(); server.server_close(); thread.join(5)


def test_registro_lleno_con_la_iniciativa_ya_presente_reemplaza_su_id_viejo_sin_429(service, tmp_path, monkeypatch):
    """F2-18: al tope, una iniciativa ya presente cambia de id (nueva versión): se sustituye el suyo, no escribe y 429."""
    calls = []
    server, thread = run_server(service, monkeypatch, tmp_path, fake_owner(calls))
    try:
        viejo = 'b' * 64
        server.review_registry[viejo] = {'initiative': INITIATIVE, 'gate_key': 'requested-review', 'consumer': None,
                                         'escritura': True}
        for n in range(service.MAX_REVIEW_IDS - 1):
            server.review_registry[format(n, '064x')] = {'initiative': 'docs/roadmap/x', 'gate_key': 'plan-ok',
                                                        'consumer': None, 'escritura': False}
        code, _, raw = send(server, 'api/review-open/' + IDENT, open_body(), method='POST')
        body = json.loads(raw)
        assert code == 200 and body['review_id'] in server.review_registry and viejo not in server.review_registry
        assert len(server.review_registry) == service.MAX_REVIEW_IDS and body['escritura'] is True
    finally:
        server.shutdown(); server.server_close(); thread.join(5)


def test_la_carpeta_desaparece_en_el_refresco_del_mapa_da_json_y_no_cierra_la_conexion(service, tmp_path, monkeypatch):
    """F2-21: `review_open` no indexa el mapa fuera del `try`."""
    calls = []
    server, thread = run_server(service, monkeypatch, tmp_path, fake_owner(calls))
    try:
        real = server.review_paths
        veces = []

        def cambia():
            veces.append(1)
            return real() if len(veces) == 1 else {}
        monkeypatch.setattr(server, 'review_paths', cambia)
        code, _, raw = send(server, 'api/review-open/' + IDENT, open_body(), method='POST')
        assert code == 404 and json.loads(raw)['status'] == 'unavailable'
        assert not any(c[0] == 'open_review' for c in calls)
    finally:
        server.shutdown(); server.server_close(); thread.join(5)


def test_una_carpeta_con_plan_no_revisable_no_ofrece_revision_y_review_current_da_json(service, tmp_path, monkeypatch):
    """F2-16: con plan pero fuera del mapa (nombre no válido): la página dice «inactiva» y `review-current` no es un 404 mudo."""
    calls = []
    monkeypatch.setattr(service, '_load_review', lambda: fake_owner(calls), raising=False)
    project = make_project(tmp_path)
    mala = project / 'docs/roadmap/Mala_Carpeta'
    mala.mkdir()
    (mala / 'improvement-plan.md').write_text('# p\n', encoding='utf8')
    (mala / 'spec.md').write_text('---\nestado: aprobada\n---\n# S\n', encoding='utf8')
    ident = hashlib.sha256(b'Mala_Carpeta').hexdigest()[:16]
    server = service.create_server(project, DATA, review_scope={'state_root': project / '.claude/plan-review'})
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        assert ident in server.plan_ids
        pagina = send(server, 'plan-' + ident + '.html')[2].decode()
        assert 'data-revision="activa"' not in pagina and 'id="plan-revisar"' not in pagina
        assert 'data-revision="activa"' in send(server, 'plan-' + IDENT + '.html')[2].decode()
        code, _, raw = send(server, 'api/review-current/' + ident)
        body = json.loads(raw)
        assert code == 200 and body['status'] == 'unavailable' and body['estado'] == 'no_disponible'
        assert body['escritura'] is False
        assert send(server, 'api/review-current/' + '0' * 16)[0] == 404
    finally:
        server.shutdown(); server.server_close(); thread.join(5)


# --- fix2 de la Fase 2: una operación que cambia estado invalida la caché de review-current/summary (I2-2) -------------

def test_con_el_dueno_real_refresh_y_submit_se_ven_al_instante_en_review_current(service, tmp_path):
    """I2-2: sin esperar al TTL de 5 s, `review-current` devuelve el `review_id` nuevo tras refresh y el estado tras submit."""
    project = make_project(tmp_path)
    server = service.create_server(project, DATA, review_scope={'state_root': project / '.claude/plan-review'})
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        opened = json.loads(send(server, 'api/review-open/' + IDENT, open_body(), method='POST')[2])
        viejo = opened['review_id']
        assert json.loads(send(server, 'api/review-current/' + IDENT)[2])['review_id'] == viejo   # llena la caché
        (project / INITIATIVE / 'improvement-plan.md').write_text('# Plan\n## Cambio\nOtra cosa.\n', encoding='utf8')
        code, _, raw = send(server, 'api/review/' + viejo + '/refresh', {'review_id': viejo}, method='POST')
        nuevo = json.loads(raw)['review']['review_id']
        assert code == 200 and nuevo != viejo
        assert json.loads(send(server, 'api/review-current/' + IDENT)[2])['review_id'] == nuevo   # inmediato, sin _envejece
        view = json.loads(send(server, 'api/review/' + nuevo + '/view')[2])
        version = {k: view['review']['version'][k] for k in ('raw_sha256', 'view_sha256', 'view_version')}
        status = json.loads(send(server, 'api/review/' + nuevo + '/status')[2])
        code, _, raw = send(server, 'api/review/' + nuevo + '/submit', {'version': version, 'comments': [], 'choice': 'approve',
                            'expected_revision': status['review']['revision']}, method='POST')
        assert code == 200, raw
        assert json.loads(send(server, 'api/review-current/' + IDENT)[2])['estado'] == 'aprobada'
        rows = {r['initiative_id']: r for r in json.loads(send(server, 'api/review-summary')[2])['initiatives']}
        assert rows[IDENT]['estado'] == 'aprobada'
    finally:
        server.shutdown(); server.server_close(); thread.join(5)


MAX_IDS = 128  # serve_panel.MAX_REVIEW_IDS (el test de F2-18 lo compara con la constante real)


def _llena_registro(server, **entrada):
    """Registro al tope: una entrada dada (`entrada`) y relleno de otras iniciativas hasta MAX_REVIEW_IDS."""
    server.review_registry['b' * 64] = {'initiative': INITIATIVE, 'consumer': None, **entrada}
    for n in range(MAX_IDS - 1):
        server.review_registry[format(n, '064x')] = {'initiative': 'docs/roadmap/x', 'gate_key': 'plan-ok',
                                                    'consumer': None, 'escritura': False}


def test_registro_lleno_con_la_iniciativa_solo_como_plan_ok_no_llama_al_dueno_y_da_429(service, tmp_path, monkeypatch):
    """I2-4: la comprobación previa mira iniciativa Y puerta: sin hueco para `requested-review`, 429 sin escribir."""
    calls = []
    server, thread = run_server(service, monkeypatch, tmp_path, fake_owner(calls))
    try:
        _llena_registro(server, gate_key='plan-ok', escritura=False)
        code, _, raw = send(server, 'api/review-open/' + IDENT, open_body(), method='POST')
        assert code == 429 and json.loads(raw)['reason'] == 'too_many_reviews'
        assert not any(c[0] == 'open_review' for c in calls)
    finally:
        server.shutdown(); server.server_close(); thread.join(5)


def test_un_get_de_review_current_no_desplaza_la_entrada_de_arranque_con_escritura(service, tmp_path, monkeypatch):
    """I2-5: con el registro lleno, la entrada con `escritura: True` (la del orquestador) no la sustituye una sin escritura."""
    calls = []
    server, thread = run_server(service, monkeypatch, tmp_path, fake_owner(calls, gate='plan-ok'))
    try:
        _llena_registro(server, gate_key='plan-ok', escritura=True)
        body = json.loads(send(server, 'api/review-current/' + IDENT)[2])
        assert server.review_registry['b' * 64]['escritura'] is True
        assert RID not in server.review_registry and body['reason'] == 'too_many_reviews'
    finally:
        server.shutdown(); server.server_close(); thread.join(5)


def test_el_plazo_de_lectura_del_servidor_deja_margen_bajo_los_4_s_del_cliente(service, tmp_path, monkeypatch):
    """I2-6: plazo del servidor + margen del dueño (0,25 s) por debajo de los 4 s con que el cliente aborta (con holgura de cola)."""
    import time
    calls = []
    server, thread = run_server(service, monkeypatch, tmp_path, fake_owner(calls))
    try:
        ahora = time.monotonic()
        send(server, 'api/review-summary'); send(server, 'api/review-current/' + IDENT)
        plazos = [c[2]['deadline'] - ahora for c in calls if c[0] == 'summarize_reviews']
        assert len(plazos) == 2 and all(p + 0.25 < 3.0 for p in plazos), plazos
    finally:
        server.shutdown(); server.server_close(); thread.join(5)


# --- fix3 de la Fase 2: el dueño pudo escribir aunque la respuesta acabe mal (I3-6) -----------------------------------

@pytest.mark.parametrize('modo', ['timeout', 'demasiado_grande', 'excepcion'])
def test_una_operacion_que_pudo_escribir_olvida_la_cache_aunque_la_respuesta_acabe_en_error(service, tmp_path, monkeypatch, modo):
    import time
    calls = []
    inner = fake_owner(calls)

    def save_comments(project, review_id, version, comments, **kwargs):
        calls.append('save_comments')                              # el dueño YA escribió cuando devuelve (o falla)
        if modo == 'timeout':
            time.sleep(0.2)
        if modo == 'excepcion':
            raise RuntimeError('fallo del dueno tras escribir')
        review = {'review_id': RID, 'revision': 1, 'pad': 'x' * (600 * 1024) if modo == 'demasiado_grande' else ''}
        return {'schema_version': 1, 'status': 'ok', 'reason': None, 'review': review}
    owner = types.SimpleNamespace(**{**vars(inner), 'save_comments': save_comments})
    server, thread = run_server(service, monkeypatch, tmp_path, owner)
    try:
        server.review_registry[RID] = {'initiative': INITIATIVE, 'gate_key': 'requested-review', 'consumer': None, 'escritura': True}
        server._review_map = {IDENT: INITIATIVE}
        server._review_summary = b'copia vieja'
        server._review_current[IDENT] = ('firma', time.monotonic(), b'copia vieja')
        server._review_current_at[IDENT] = time.monotonic()
        payload = {'version': 1, 'comments': [], 'expected_revision': 0}
        deadline = time.monotonic() + (0.05 if modo == 'timeout' else 5)
        code, _body = server.review('comments', RID, payload, deadline)
        assert 'save_comments' in calls
        assert code == {'timeout': 503, 'demasiado_grande': 413, 'excepcion': 503}[modo]
        assert server._review_summary is None and IDENT not in server._review_current and IDENT not in server._review_current_at
    finally:
        server.shutdown(); server.server_close(); thread.join(5)
