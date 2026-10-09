"""Review transport delegates all receipt state to the common owner."""
import http.client
import importlib.util
import json
from pathlib import Path
import socket
import threading
import time
import types

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'skills/plugin-panel/scripts/serve_panel.py'
RID = 'a' * 64
VERSION = {'raw_sha256': 'b' * 64, 'view_sha256': 'c' * 64, 'view_version': 'plan-text-v1'}
DATA = {'counts': dict.fromkeys(('agents', 'skills', 'commands', 'tools', 'hooks'), 0),
        'agents': [], 'skills': [], 'commands': [], 'tools': [], 'hooks': [],
        'runtimes': {}, 'memory': {}, 'warnings': [], 'workflow': {'roles': {}}}

@pytest.fixture
def service():
    spec = importlib.util.spec_from_file_location('review_transport', SCRIPT)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module

@pytest.fixture
def review_server(service, tmp_path, monkeypatch):
    calls = []
    result = {'schema_version': 1, 'status': 'ok', 'reason': None,
              'review': {'review_id': RID, 'version': VERSION, 'revision': 0}}
    def operation(name):
        def invoke(*args, **kwargs):
            calls.append((name, args, kwargs)); return result
        return invoke
    owner = types.SimpleNamespace(**{name: operation(name) for name in
        ('open_review', 'get_view', 'get_status', 'save_comments', 'submit_decision')})
    monkeypatch.setattr(service, '_load_review', lambda: owner, raising=False)
    selection = {'initiative': 'docs/roadmap/2026-10-09-example',
                 'state_root': tmp_path / '.claude/plan-review', 'gate_key': 'plan-ok'}
    server = service.create_server(tmp_path, DATA, review_selection=selection)
    server.calls = calls; server.result = result; server.service = service; server.selection = selection
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    yield server
    server.shutdown(); server.server_close(); thread.join(5)
    assert not thread.is_alive()

def send(server, op='view', payload=None, *, method='GET', rid=RID, raw=None, headers=None):
    connection = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=5)
    body = raw if raw is not None else json.dumps(payload, ensure_ascii=False).encode('utf8') if method == 'POST' else None
    request_headers = {'Content-Type': 'application/json', **(headers or {})}
    # Early header rejections must not race unread TCP data on Windows.
    early = method == 'POST' and (op not in ('comments', 'submit', 'refresh') or len(body) > 16384
        or any(key in request_headers for key in ('Host', 'Origin', 'Sec-Fetch-Site'))
        or request_headers['Content-Type'] != 'application/json')
    if early: request_headers['Content-Length'] = str(len(body))
    connection.request(method, server.access_prefix + 'api/review/' + rid + '/' + op,
                       None if early else body, request_headers)
    response = connection.getresponse(); result = response.status, dict(response.getheaders()), response.read()
    connection.close(); return result

def test_review_open_and_get_delegate_without_browser_paths(review_server):
    server = review_server
    assert server.calls[0][0] == 'open_review'
    assert server.calls[0][1] == (server.project, server.selection['initiative'])
    assert send(server)[0] == 200
    assert server.calls[-1][0] == 'get_view'
    assert send(server, 'status')[0] == 200 and server.calls[-1][0] == 'get_status'
    headers = send(server)[1]
    assert headers['Cache-Control'] == 'no-store' and 'nonce-' in headers['Content-Security-Policy']

def test_comments_submit_and_refresh_delegate(review_server):
    server = review_server
    comment = {'comment_id': 'comment-1', 'section_id': 'd'*64, 'text': 'Revisar 🚀'}
    payload = {'version': VERSION, 'comments': [comment], 'expected_revision': 0}
    assert send(server, 'comments', payload, method='POST')[0] == 200
    name, args, kwargs = server.calls[-1]
    assert name == 'save_comments' and args[2:] == (VERSION, [comment]) and kwargs['expected_revision'] == 0
    assert kwargs['deadline'] > time.monotonic() and kwargs['state_root'] == server.selection['state_root']
    assert send(server, 'submit', {**payload, 'choice': 'request_changes'}, method='POST')[0] == 200
    assert server.calls[-1][0] == 'submit_decision'
    assert send(server, 'refresh', {'review_id': RID}, method='POST')[0] == 200
    assert server.calls[-1][0] == 'open_review' and len(server.calls) == 4

@pytest.mark.parametrize('op', ['receive', 'ack', 'reset', 'view/extra', 'status?x=1'])
def test_unknown_routes_never_delegate(review_server, op):
    before = len(review_server.calls)
    assert send(review_server, op, {}, method='POST')[0] in (404, 405)
    assert len(review_server.calls) == before

@pytest.mark.parametrize('rid', ['f'*64, '../outside', 'A'*64, 'a'*63])
def test_unregistered_id_never_delegates(review_server, rid):
    before = len(review_server.calls)
    assert send(review_server, rid=rid)[0] == 404
    assert len(review_server.calls) == before

@pytest.mark.parametrize('payload', [None, [], {'project': '/outside'},
    {'version': VERSION, 'comments': [], 'expected_revision': True},
    {'version': VERSION, 'comments': [], 'expected_revision': -1},
    {'version': {**VERSION, 'extra': 1}, 'comments': [], 'expected_revision': 0},
    {'version': VERSION, 'comments': [{'comment_id':'c', 'section_id':'d'*64,'text':42}], 'expected_revision':0},
    {'version': None, 'comments': [], 'expected_revision': 0},
    {'version': {**VERSION,'raw_sha256':42}, 'comments': [], 'expected_revision': 0},
    {'version': VERSION,'comments':{},'expected_revision':0},
    {'version': VERSION,'comments':[{'comment_id':'../outside','section_id':'d'*64,'text':'x'}],'expected_revision':0},
    {'version': VERSION,'comments':[{'comment_id':'c','section_id':'../outside','text':'x'}],'expected_revision':0},
    {'version': VERSION,'comments':[{'comment_id':'c','section_id':'d'*64,'text':'x','path':'outside'}],'expected_revision':0},
    {'version': VERSION,'comments':[{'comment_id':'c','section_id':'d'*64,'text':'x'}]*2,'expected_revision':0}])
def test_invalid_comments_rejected_before_owner(review_server, payload):
    before = len(review_server.calls)
    assert send(review_server, 'comments', payload, method='POST')[0] == 400
    assert len(review_server.calls) == before

@pytest.mark.parametrize('raw', [b'{"version":1,"version":2}', b'{"version":NaN}', b'{"bad":"\xff"}', b'{}'+b' '*16383])
def test_framing_limits_duplicate_nonfinite_utf8(review_server, raw):
    before = len(review_server.calls)
    assert send(review_server, 'comments', method='POST', raw=raw)[0] in (400, 413)
    assert len(review_server.calls) == before

@pytest.mark.parametrize('headers', [{'Host':'evil.local'}, {'Origin':'https://evil.local'}, {'Sec-Fetch-Site':'cross-site'}, {'Content-Type':'text/plain'}])
def test_origin_and_content_checks_precede_owner(review_server, headers):
    before = len(review_server.calls)
    assert send(review_server, 'comments', {}, method='POST', headers=headers)[0] in (403, 415)
    assert len(review_server.calls) == before

@pytest.mark.parametrize('status,reason,expected', [('version_changed',None,409), ('conflict','revision_conflict',409),
    ('unavailable','invalid_comments',400), ('unavailable','response_budget',413), ('unavailable','read_failed',503), ('waiting',None,200)])
def test_owner_envelope_translation(review_server, status, reason, expected):
    review_server.result.update(status=status, reason=reason)
    assert send(review_server)[0] == expected

def test_response_budget_is_independent_from_progress_memory(review_server):
    review_server.result['review']['text'] = 'x' * (512 * 1024)
    code, _, body = send(review_server)
    assert code == 413 and b'xxx' not in body
    assert review_server.service.MAX_REQUEST_BYTES == 4096
    assert review_server.service.MAX_RESPONSE_BYTES == 65536

def test_response_budget_counts_json_escapes_not_text_length(review_server):
    review_server.result['review']['text'] = '\x00' * 90000
    code, _, raw = send(review_server)
    assert code == 413 and json.loads(raw)['reason'] == 'response_budget'

def test_surrogate_comment_rejected_before_owner(review_server):
    payload = {'version':VERSION,'expected_revision':0,
               'comments':[{'comment_id':'c','section_id':'d'*64,'text':'\ud800'}]}
    before = len(review_server.calls)
    assert send(review_server,'comments',method='POST',raw=json.dumps(payload).encode())[0] == 400
    assert len(review_server.calls) == before

def test_ordinary_server_never_loads_review_owner(service, tmp_path, monkeypatch):
    monkeypatch.setattr(service, '_load_review', lambda: pytest.fail('ordinary server opened review'), raising=False)
    server = service.create_server(tmp_path, DATA)
    try:
        assert b'id="plan-review"' not in server.page
    finally: server.server_close()

@pytest.mark.parametrize('selection', [[], {}, {'initiative':'x'}, {'state_root':'x'},
    {'initiative':'x','state_root':'x','backend':'arbitrary'}])
def test_invalid_selection_does_not_open_owner(service, tmp_path, monkeypatch, selection):
    monkeypatch.setattr(service, '_load_review', lambda: pytest.fail('invalid selection opened owner'))
    with pytest.raises(ValueError, match='invalid review selection'):
        service.create_server(tmp_path, DATA, review_selection=selection)

def test_optional_owner_load_failure_keeps_panel_available(service, tmp_path, monkeypatch):
    def broken(): raise ImportError('SECRET outside/root')
    monkeypatch.setattr(service, '_load_review', broken)
    server = service.create_server(tmp_path,DATA,review_selection={'initiative':'docs/roadmap/2026-10-09-example',
        'state_root':tmp_path / '.claude/plan-review'})
    try:
        assert server.review_ids == set() and b'data-review-id=""' in server.page
        assert b'SECRET' not in server.page and b'id="plan-review"' in server.page
    finally: server.server_close()

def test_unicode_codepoints_and_aggregate_limits(review_server):
    def payload(rows): return {'version': VERSION, 'comments': rows, 'expected_revision': 0}
    comment = {'comment_id': 'c', 'section_id': 'd'*64, 'text': '🚀'*2000}
    assert send(review_server, 'comments', payload([comment]), method='POST')[0] == 200
    assert review_server.calls[-1][1][-1][0]['text'] == '🚀'*2000
    before = len(review_server.calls)
    rows = [{**comment, 'comment_id': str(i), 'text': '🚀'*1000} for i in range(3)]
    assert send(review_server, 'comments', payload(rows), method='POST')[0] == 413
    assert len(review_server.calls) == before

@pytest.mark.parametrize('rows', [[{'comment_id':'c','section_id':'d'*64,'text':'x'*2001}],
    [{'comment_id':str(i),'section_id':'d'*64,'text':'x'} for i in range(21)]])
def test_comment_budget_maps_to_413_without_owner(review_server, rows):
    before = len(review_server.calls)
    assert send(review_server, 'comments', {'version':VERSION,'comments':rows,'expected_revision':0}, method='POST')[0] == 413
    assert len(review_server.calls) == before

def test_body_and_owner_share_one_deadline(review_server):
    server = review_server
    raw = json.dumps({'version': VERSION, 'comments': [], 'expected_revision': 0}).encode()
    connection = socket.create_connection(('127.0.0.1', server.server_port), timeout=5)
    started = time.monotonic()
    target = server.access_prefix + 'api/review/' + RID + '/comments'
    header = f'POST {target} HTTP/1.1\r\nHost: 127.0.0.1:{server.server_port}\r\nContent-Type: application/json\r\nContent-Length: {len(raw)}\r\n\r\n'
    connection.sendall(header.encode()+raw[:1])
    time.sleep(0.15)
    connection.sendall(raw[1:])
    response = http.client.HTTPResponse(connection); response.begin(); response.read(); connection.close()
    assert response.status == 200
    deadline = server.calls[-1][2]['deadline']
    assert deadline - started < 3.1 and deadline - time.monotonic() < 2.95

def test_exhausted_operation_budget_cannot_be_renewed(review_server, monkeypatch):
    server = review_server
    original = server.review_owner.get_view
    def delayed(*args, **kwargs):
        time.sleep(0.03); return original(*args, **kwargs)
    server.review_owner.get_view = delayed
    monkeypatch.setattr(server.service, 'BODY_TIMEOUT', 0.02)
    code, _, raw = send(server)
    assert code == 503 and json.loads(raw)['review'] is None

def test_refresh_registers_new_owner_id_without_transferring_comments(review_server):
    server = review_server
    new_id = 'f'*64
    server.result['review']['review_id'] = new_id
    assert send(server, 'refresh', {'review_id': RID}, method='POST')[0] == 200
    assert send(server, rid=new_id)[0] == 200
    assert server.calls[-2][0] == 'open_review' and 'comments' not in server.calls[-2][2]

def test_helper_failures_are_opaque(review_server):
    def broken(*args, **kwargs): raise RuntimeError('SECRET_CAPABILITY outside/root')
    review_server.review_owner.get_view = broken
    code, _, raw = send(review_server)
    assert code == 503 and b'SECRET' not in raw and b'outside' not in raw

def test_review_route_never_reinterprets_capability(service, tmp_path, monkeypatch):
    monkeypatch.setattr(service, '_load_review', lambda: pytest.fail('disabled route loads owner'), raising=False)
    server = service.create_server(tmp_path, DATA)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try: assert send(server)[0] == 404
    finally:
        server.shutdown(); server.server_close(); thread.join(5)

@pytest.fixture
def real_review(service, tmp_path):
    initiative = 'docs/roadmap/2026-10-09-actual'
    plan = tmp_path / initiative / 'improvement-plan.md'
    plan.parent.mkdir(parents=True)
    (tmp_path / '.claude').mkdir()
    plan.write_bytes(b'\xef\xbb\xbf'+('# Plan\r\nTexto 🚀 <script>alert(1)</script>\r\n## Cambio\r\nValidar.\r\n').encode())
    selection = {'initiative':initiative, 'state_root':tmp_path / '.claude/plan-review', 'gate_key':'plan-ok',
                 'consumer':{'caller_id':'dev-cycle','runtime':'codex'}}
    servers = []
    def start():
        server = service.create_server(tmp_path, DATA, review_selection=selection)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        servers.append((server,thread))
        return server
    server = start()
    yield server,plan,start
    for server,thread in servers:
        server.shutdown(); server.server_close(); thread.join(5)
        assert not thread.is_alive()

def real_view(server):
    rid, = server.review_ids
    code, _, raw = send(server,rid=rid)
    assert code == 200, raw
    return rid,json.loads(raw)['review']


@pytest.mark.parametrize('control', ['\x00', '\u202e'], ids=['nul', 'bidi'])
@pytest.mark.parametrize('operation', ['comments', 'submit'])
def test_gap_b1_c1_http_comments_do_not_reveal_tokens_or_poison_state(real_review, control, operation):
    server, _, _ = real_review
    rid, view = real_view(server)
    token = 'sk-' + 'AbCd1234' * 6  # Synthetic credential-shaped fixture.
    rows = [{'comment_id': 'controlled', 'section_id': view['sections'][0]['section_id'],
             'text': 's' + control + token[1:]}]
    payload = {'version': view['version'], 'comments': rows, 'expected_revision': view['revision']}
    if operation == 'submit':
        payload['choice'] = 'request_changes'
    code, _, raw = send(server, operation, payload, method='POST', rid=rid)
    assert code == 200, raw
    assert token.encode('utf8') not in raw
    assert token not in (server.review_selection['state_root'] / ('r-' + rid + '.json')).read_text(encoding='utf8')
    code, _, raw = send(server, 'status', rid=rid)
    assert code == 200 and json.loads(raw)['status'] == 'ok'
    other = 'docs/roadmap/2026-10-09-other'
    other_plan = server.project / other / 'improvement-plan.md'
    other_plan.parent.mkdir(parents=True)
    other_plan.write_text('# Another plan\nUnrelated review.\n', encoding='utf8')
    result = server.review_owner.open_review(server.project, other,
        state_root=server.review_selection['state_root'], gate_key='plan-ok')
    assert result['status'] == 'ok', result

def test_actual_owner_receipt_comment_cas_submit_consume_restart(real_review):
    import hashlib
    server,plan,start = real_review
    rid,view = real_view(server)
    assert view['version']['raw_sha256'] == hashlib.sha256(plan.read_bytes()).hexdigest()
    assert b'data-review-id="'+rid.encode()+b'"' in server.page
    comments = [{'comment_id':'comment-1','section_id':view['sections'][0]['section_id'],'text':'Comprobar 🚀'}]
    payload = {'version':view['version'],'comments':comments,'expected_revision':view['revision']}
    code, _, raw = send(server,'comments',payload,method='POST',rid=rid)
    assert code == 200
    saved = json.loads(raw)['review']; assert saved['revision'] == 1
    assert send(server,'submit',{**payload,'choice':'approve'},method='POST',rid=rid)[0] == 409
    code, _, raw = send(server,'submit',{**payload,'expected_revision':1,'choice':'approve'},method='POST',rid=rid)
    assert code == 200
    submitted = json.loads(raw)['review']; assert submitted['state'] == 'pendiente'
    owner = server.review_owner
    args = {'state_root':server.review_selection['state_root'],'gate_key':'plan-ok'}
    received = owner.receive_decision(server.project,rid,view['version'],**args)
    assert received['status'] == 'ok' and received['review']['state'] == 'entregada'
    decision_id = received['review']['decision']['decision_id']; delivery_id = received['review']['delivery']['delivery_id']
    acked = owner.ack_decision(server.project,rid,view['version'],decision_id=decision_id,delivery_id=delivery_id,**args)
    assert acked['status'] == 'ok' and acked['review']['state'] == 'consumida'
    restarted = start()
    assert restarted.capability != server.capability
    same_id,same_view = real_view(restarted)
    assert same_id == rid and same_view['state'] == 'consumida'
    assert same_view['ack'] == acked['review']['ack']
    assert b'<script>alert(1)</script>' in plan.read_bytes()  # Canonical bytes untouched.
    plan.unlink()  # Synthetic OWN plan only; receipts retain their historical fact.
    code, _, raw = send(restarted,'status',rid=rid)
    unavailable = json.loads(raw)
    assert code == 503 and unavailable['review']['validity'] == 'unavailable'
    assert unavailable['review']['state'] == 'consumida' and unavailable['review']['decision']['decision_id'] == decision_id
    assert unavailable['review']['current_version'] is None

def test_actual_owner_changed_plan_explicit_refresh_does_not_transfer_draft(real_review):
    server,plan,_ = real_review
    rid,view = real_view(server)
    payload = {'version':view['version'],'comments':[{'comment_id':'c','section_id':view['sections'][0]['section_id'],'text':'Anterior'}],
               'expected_revision':0}
    assert send(server,'comments',payload,method='POST',rid=rid)[0] == 200
    plan.write_text('# Plan nuevo\nTexto cambiado 🚀',encoding='utf8')
    code, _, raw = send(server,'submit',{**payload,'expected_revision':1,'choice':'approve'},method='POST',rid=rid)
    stale = json.loads(raw)
    assert code == 409 and stale['status'] == 'version_changed' and stale['review']['decision'] is None
    code, _, raw = send(server,'refresh',{'review_id':rid},method='POST',rid=rid)
    fresh = json.loads(raw)['review']
    assert code == 200 and fresh['review_id'] != rid and fresh['draft_comments'] == [] and fresh['decision'] is None
    assert send(server,rid=fresh['review_id'])[0] == 200
    assert send(server,'status',rid=rid)[0] == 409

def test_actual_owner_contradictory_tabs_and_changes_delivery(real_review):
    server,_,_ = real_review
    rid,view = real_view(server)
    payload = {'version':view['version'],'comments':[{'comment_id':'c','section_id':view['sections'][0]['section_id'],'text':'Corregir'}],
               'expected_revision':0,'choice':'request_changes'}
    assert send(server,'submit',payload,method='POST',rid=rid)[0] == 200
    assert send(server,'submit',{**payload,'choice':'approve'},method='POST',rid=rid)[0] == 409
    assert send(server,'receive',{},method='POST',rid=rid)[0] == 405
    received = server.review_owner.receive_decision(server.project,rid,view['version'],
        gate_key='plan-ok',state_root=server.review_selection['state_root'])
    assert received['review']['decision']['choice'] == 'request_changes'
    code, _, raw = send(server,'status',rid=rid)
    assert code == 200 and json.loads(raw)['review']['state'] == 'entregada'
