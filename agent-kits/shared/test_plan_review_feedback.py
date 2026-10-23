"""Feedback belongs to the consumed comment/version; owned fixtures only."""
import json
import os
from pathlib import Path
import subprocess
import sys
import threading

import pytest

from test_plan_review import owned, ready, comment, submit, receive, ack, stored, load, SCRIPT

PRODUCER = {'caller_id': 'owned-feedback', 'runtime': 'codex', 'actor_id': None}


def consumed(o):
    r = ready(o)
    response = submit(o, r, 'request_changes', comment(r)); assert response['status'] == 'ok', response
    r = response['review']
    response = receive(o, r); assert response['status'] == 'ok', response
    r = response['review']
    response = ack(o, r); assert response['status'] == 'ok', response
    return response['review']


def result(o, r, **changes):
    payload = dict(gate_key=r['gate_key'], decision_id=r['decision']['decision_id'],
        delivery_id=r['delivery']['delivery_id'], comment_id='one', result_id='1111111111111111111111111111111111111111111111111111111111111111',
        expected_revision=r['revision'], disposition='addressed', response_text='Changed scope; review the new paragraph.',
        supersedes_result_id=None, producer=PRODUCER, state_root=o.state)
    payload.update(changes)
    return o.module.record_feedback_result(o.root, r['review_id'], r['version'], **payload)


def verify(o, r, **changes):
    payload = dict(gate_key=r['gate_key'], decision_id=r['decision']['decision_id'],
        delivery_id=r['delivery']['delivery_id'], comment_id='one', result_id='1111111111111111111111111111111111111111111111111111111111111111',
        verification_id='4444444444444444444444444444444444444444444444444444444444444444', expected_revision=r['revision'] + 1,
        assessment='confirmed', note='Checked by prior explicit human instruction.',
        producer=PRODUCER, state_root=o.state)
    payload.update(changes)
    return o.module.record_feedback_verification(o.root, r['review_id'], r['version'], **payload)


def test_feedback_response_is_immutable_declared_and_not_approval(owned):
    r = consumed(owned)
    receipt = result(owned, r)
    assert receipt['status'] == 'ok', receipt
    assert receipt['review'] is None and receipt['approval_granted'] is False
    assert receipt['feedback_receipt']['revision'] == r['revision'] + 1
    row = json.loads(stored(owned, r).read_bytes())
    assert row['schema_version'] == 2 and row['ack'] == r['ack']
    feedback = owned.module.get_status(owned.root, r['review_id'], state_root=owned.state)['review']['feedback']
    item = feedback['results'][0]
    assert item['response_text'] == 'Changed scope; review the new paragraph.'
    assert item['producer'] == {**PRODUCER, 'identity_basis': 'declared'}
    assert item['section_id'] == r['decision']['comments'][0]['section_id']
    assert item['artifact_observation']['status'] == 'available'
    assert feedback['verifications'] == []


def test_feedback_retry_after_restart_does_not_rewrite_or_reobserve(owned):
    r = consumed(owned); first = result(owned, r)
    path = stored(owned, r); before = path.read_bytes(); stamp = path.stat().st_mtime_ns
    owned.plan.write_bytes(b'# Different plan\n'); owned.module = load()
    retried = result(owned, r, expected_revision=0)
    assert retried == first
    assert path.read_bytes() == before and path.stat().st_mtime_ns == stamp
    assert result(owned, r, response_text='Different claim')['reason'] == 'operation_conflict'
    assert path.read_bytes() == before


@pytest.mark.parametrize('changes,reason', [
    ({'expected_revision': 0}, 'revision_conflict'),
    ({'expected_revision': True}, 'invalid_feedback'),
    ({'expected_revision': 9007199254740992}, 'invalid_feedback'),
    ({'comment_id': 'absent'}, 'comment_not_found'),
    ({'gate_key': 'requested-review'}, 'gate_conflict'),
    ({'decision_id': 'f' * 64}, 'ack_conflict'),
    ({'delivery_id': 'f' * 64}, 'ack_conflict'),
    ({'disposition': 'verified'}, 'invalid_feedback'),
    ({'response_text': ''}, 'invalid_feedback'),
    ({'response_text': '🚀' * 513}, 'feedback_text_budget'),
    ({'response_text': 'a' * 1001}, 'feedback_text_budget'),
    ({'producer': {**PRODUCER, 'native_observed': True}}, 'invalid_feedback'),
    ({'producer': {**PRODUCER, 'actor_id': 'human-name'}}, 'invalid_feedback'),
    ({'supersedes_result_id': 'ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff'}, 'result_conflict'),
])
def test_feedback_rejected_mutations_keep_exact_bytes(owned, changes, reason):
    r = consumed(owned); before = stored(owned, r).read_bytes()
    response = result(owned, r, **changes)
    assert response['reason'] == reason, response
    assert response['approval_granted'] is False and response['feedback_receipt'] is None
    assert stored(owned, r).read_bytes() == before


def test_ack_is_required_but_not_attention(owned):
    r = ready(owned); r = submit(owned, r, 'request_changes', comment(r))['review']; r = receive(owned, r)['review']
    before = stored(owned, r).read_bytes()
    assert result(owned, r)['reason'] == 'decision_not_consumed'
    assert stored(owned, r).read_bytes() == before
    r = ack(owned, r)['review']
    assert r['feedback']['results'] == []
    assert result(owned, r)['status'] == 'ok'


def test_optional_verification_is_an_annotation_with_no_gate(owned):
    r = consumed(owned); assert result(owned, r)['status'] == 'ok'
    receipt = verify(owned, r)
    assert receipt['status'] == 'ok' and receipt['approval_granted'] is False
    row = json.loads(stored(owned, r).read_bytes())
    annotation = row['feedback']['verifications'][0]
    assert annotation['basis'] == 'human_instruction_declared'
    assert annotation['producer']['identity_basis'] == 'declared'
    assert row['state'] == 'consumida' and row['ack'] == r['ack']
    before = stored(owned, r).read_bytes()
    assert verify(owned, r, expected_revision=0) == receipt
    assert verify(owned, r, note='Different annotation')['reason'] == 'operation_conflict'
    assert stored(owned, r).read_bytes() == before


def test_supersession_is_bounded_and_keeps_old_verification_history(owned):
    r = consumed(owned); result(owned, r); verify(owned, r)
    assert result(owned, r, result_id='2222222222222222222222222222222222222222222222222222222222222222', expected_revision=r['revision']+2,
        supersedes_result_id='1111111111111111111111111111111111111111111111111111111111111111', disposition='not_applied', response_text='Reverted after feedback.')['status'] == 'ok'
    assert verify(owned, r, verification_id='5555555555555555555555555555555555555555555555555555555555555555', expected_revision=r['revision']+3)['reason'] == 'result_superseded'
    assert verify(owned, r, expected_revision=0)['status'] == 'ok'  # Same frozen annotation retry.
    assert result(owned, r, result_id='3333333333333333333333333333333333333333333333333333333333333333', expected_revision=r['revision']+3,
        supersedes_result_id='2222222222222222222222222222222222222222222222222222222222222222')['reason'] == 'feedback_budget'
    row = json.loads(stored(owned, r).read_bytes())
    assert len(row['feedback']['results']) == 2 and len(row['feedback']['verifications']) == 1


@pytest.mark.parametrize('plan', [b'# New version\n', None, b'\xff', b''])
def test_historical_result_visible_only_on_old_review_history(owned, plan):
    r = consumed(owned)
    if plan is None: owned.plan.unlink()
    else: owned.plan.write_bytes(plan)
    receipt = result(owned, r)
    assert receipt['status'] == 'ok', receipt
    old = owned.module.get_status(owned.root, r['review_id'], state_root=owned.state)['review']
    assert old['feedback']['results'][0]['comment_id'] == 'one'
    assert old['validity'] != 'current'
    owned.plan.write_bytes(b'# Current plan with new content\n')
    current = ready(owned)
    assert current['feedback']['results'] == [] and current['feedback_history']['complete'] is True
    historical = current['feedback_history']['reviews'][0]
    assert historical['review_id'] == r['review_id'] and historical['version'] == r['version']
    assert historical['feedback']['results'][0]['response_text'].startswith('Changed scope')
    assert 'sections' not in historical and 'consumer_registration' not in historical


def test_legacy_reads_do_not_migrate_then_first_feedback_migrates_once(owned):
    r = consumed(owned); path = stored(owned, r); row = json.loads(path.read_bytes())
    row['schema_version'] = 1; row.pop('feedback', None); path.write_bytes(owned.module._json(row))
    before = path.read_bytes(); stamp = path.stat().st_mtime_ns
    for fn in [owned.module.get_view, owned.module.get_status]:
        projection = fn(owned.root, r['review_id'], state_root=owned.state)
        assert projection['review']['feedback'] == {'schema_version': 1, 'results': [], 'verifications': []}
    assert path.read_bytes() == before and path.stat().st_mtime_ns == stamp
    assert result(owned, r)['status'] == 'ok'
    updated = json.loads(path.read_bytes())
    assert updated['schema_version'] == 2 and updated['revision'] == r['revision'] + 1


def test_text_is_sanitized_and_redacted_without_capturing_raw_input(owned):
    r = consumed(owned); secret = 'sk-' + 'AbCd1234' * 6
    response = result(owned, r, response_text='Explicit note\r\n s\x00' + secret[1:] + ' \u202e')
    assert response['status'] == 'ok', response
    text = stored(owned, r).read_text(encoding='utf8')
    assert secret not in text and '\\u0000' not in text
    row = json.loads(text)['feedback']['results'][0]
    assert row['text_flags'] == {'redacted': True, 'controls_sanitized': True}
    assert '\r' not in row['response_text'] and '\x00' not in row['response_text']


def test_corrupt_feedback_is_rejected_without_reset_or_dedup_bypass(owned):
    r = consumed(owned); result(owned, r); path = stored(owned, r)
    row = json.loads(path.read_bytes()); row['feedback']['results'][0]['producer']['identity_basis'] = 'native_observed'
    path.write_bytes(owned.module._json(row)); before = path.read_bytes()
    assert owned.module.get_status(owned.root, r['review_id'], state_root=owned.state)['reason'] == 'invalid_state'
    assert result(owned, r)['reason'] == 'invalid_state'
    assert path.read_bytes() == before


def test_feedback_budget_and_output_budget_fail_before_commit(owned, monkeypatch):
    r = consumed(owned); before = stored(owned, r).read_bytes()
    monkeypatch.setattr(owned.module, 'MAX_RESPONSE_BYTES', 32)
    assert result(owned, r)['reason'] == 'response_budget'
    assert stored(owned, r).read_bytes() == before
    monkeypatch.setattr(owned.module, 'MAX_RESPONSE_BYTES', 512*1024)
    monkeypatch.setattr(owned.module, 'MAX_RECORD_BYTES', 32)
    assert result(owned, r)['reason'] == 'state_budget'
    assert stored(owned, r).read_bytes() == before


def test_feedback_cli_exact_body_and_retry_do_not_accept_owner_fields(owned):
    r = consumed(owned)
    payload = dict(version=r['version'],gate_key=r['gate_key'],decision_id=r['decision']['decision_id'],
        delivery_id=r['delivery']['delivery_id'],comment_id='one',result_id='1'*64,
        expected_revision=r['revision'],disposition='addressed',response_text='Explicit CLI note 🚀',
        supersedes_result_id=None,producer=PRODUCER)
    argv = [sys.executable,str(SCRIPT),'result','--project',str(owned.root),'--state-root',str(owned.state),
            '--review-id',r['review_id'],'--json']
    def invoke(body):
        process = subprocess.run(argv,input=owned.module._json(body),capture_output=True,timeout=10)
        return process.returncode,json.loads(process.stdout)
    before = stored(owned,r).read_bytes()
    code,rejected = invoke({**payload,'recorded_at':'2026-10-10T00:00:00Z'})
    assert code == 3 and rejected['approval_granted'] is False
    assert stored(owned,r).read_bytes() == before
    code,receipt = invoke(payload)
    assert code == 0 and receipt['feedback_receipt']['operation'] == 'result'
    committed = stored(owned,r).read_bytes()
    assert invoke({**payload,'expected_revision':0}) == (0,receipt)
    assert stored(owned,r).read_bytes() == committed


def test_feedback_parallel_same_revision_has_one_committed_result(owned):
    r = consumed(owned); barrier = threading.Barrier(2); responses = []
    def attempt(identifier):
        barrier.wait(timeout=5)
        responses.append(result(owned,r,result_id=identifier))
    threads = [threading.Thread(target=attempt,args=(digit*64,)) for digit in ('1','2')]
    for thread in threads: thread.start()
    for thread in threads: thread.join(10)
    assert all(not thread.is_alive() for thread in threads) and len(responses) == 2
    assert sum(response['status'] == 'ok' for response in responses) == 1
    assert {response['reason'] for response in responses if response['status'] != 'ok'} <= {'revision_conflict','state_busy'}
    row = json.loads(stored(owned,r).read_bytes())
    assert row['revision'] == r['revision']+1 and len(row['feedback']['results']) == 1
    other = ('2' if row['feedback']['results'][0]['result_id'] == '1'*64 else '1')*64
    assert result(owned,r,result_id=other)['reason'] == 'revision_conflict'


@pytest.mark.parametrize('mutation', ['schema_bool','unknown_key','duplicate_id','noncanonical_text','wrong_comment','unknown_observation','unknown_flags'])
def test_feedback_nested_corruption_rejects_entire_inventory(owned,mutation):
    r = consumed(owned); result(owned,r); path = stored(owned,r); row=json.loads(path.read_bytes())
    feedback = row['feedback']; item = feedback['results'][0]
    if mutation == 'schema_bool': feedback['schema_version'] = True
    elif mutation == 'unknown_key': feedback['raw_arguments'] = {}
    elif mutation == 'duplicate_id': feedback['results'].append(dict(item))
    elif mutation == 'noncanonical_text': item['response_text'] += '\u202e'
    elif mutation == 'wrong_comment': item['comment_id'] = 'absent'
    elif mutation == 'unknown_observation': item['artifact_observation']['status'] = 'verified'
    elif mutation == 'unknown_flags': item['text_flags']['tool_capture'] = False
    path.write_bytes(owned.module._json(row)); before=path.read_bytes()
    owned.plan.write_bytes(b'# Another current version\n')
    assert owned.module.open_review(owned.root,r['initiative'],gate_key='plan-ok',state_root=owned.state)['reason'] == 'invalid_state'
    assert path.read_bytes() == before


def test_history_is_bounded_whole_rows_sorted_and_has_no_other_gate(owned):
    rows=[]
    for index in range(10):
        owned.plan.write_text('# Plan '+str(index)+'\n',encoding='utf8')
        r=consumed(owned); assert result(owned,r)['status'] == 'ok'; rows.append(r)
    owned.plan.write_bytes(b'# Current version\n')
    current=ready(owned); history=current['feedback_history']
    assert history['complete'] is False and len(history['reviews']) == 8
    assert [row['review_id'] for row in history['reviews']] == [row['review_id'] for row in reversed(rows[-8:])]
    assert len(owned.module._json(history)) <= 65536
    separate=owned.module.open_review(owned.root,current['initiative'],state_root=owned.state,gate_key='requested-review')['review']
    assert separate['feedback_history']['reviews'] == [] and separate['feedback_history']['complete'] is True


def test_history_order_uses_timestamp_instant_and_stable_id_tie(owned):
    rows=[]
    for index in range(3):
        owned.plan.write_text('# Plan '+str(index)+'\n',encoding='utf8')
        r=consumed(owned); result(owned,r); rows.append(r)
    for index,r in enumerate(rows):
        path=stored(owned,r); row=json.loads(path.read_bytes())
        row['created_at']='2026-10-10T01:00:00Z' if index == 0 else '2026-10-10T01:00:00.100000Z'
        path.write_bytes(owned.module._json(row))
    owned.plan.write_bytes(b'# Latest\n'); current=ready(owned)
    expected=sorted([rows[1]['review_id'],rows[2]['review_id']])+[rows[0]['review_id']]
    assert [row['review_id'] for row in current['feedback_history']['reviews']] == expected


@pytest.mark.parametrize('operation',['result','verify-result'])
def test_gap_f24_deadline_retry_after_durable_expires_without_losing_receipt(owned,monkeypatch,operation):
    r=consumed(owned); committed=result(owned,r)
    if operation == 'verify-result': committed=verify(owned,r)
    path=stored(owned,r); before=path.read_bytes(); stamp=path.stat().st_mtime_ns
    clock=[100.0]; durable=owned.module._durable
    monkeypatch.setattr(owned.module.time,'monotonic',lambda:clock[0])
    def expires_after_real_flush(path):
        durable(path); clock[0]=102.0
    monkeypatch.setattr(owned.module,'_durable',expires_after_real_flush)
    fn=result if operation == 'result' else verify
    failed=fn(owned,r,expected_revision=0,deadline=101.0)
    assert failed['status']=='unavailable' and failed['reason']=='deadline_expired',failed
    assert failed['feedback_receipt'] is None and failed['approval_granted'] is False
    assert path.read_bytes()==before and path.stat().st_mtime_ns==stamp
    clock[0]=100.0; monkeypatch.setattr(owned.module,'_durable',durable)
    retried=fn(owned,r,expected_revision=0,deadline=101.0)
    assert retried['status']=='ok' and retried['feedback_receipt']==committed['feedback_receipt']
    assert path.read_bytes()==before and path.stat().st_mtime_ns==stamp


@pytest.mark.parametrize('field,bad', [('response_text',None),('response_text',7),('note',None),('note',7)])
def test_gap_f24_corruption_reason_nontext_is_invalid_state_before_limits(owned,field,bad):
    r=consumed(owned); result(owned,r); verify(owned,r)
    path=stored(owned,r); row=json.loads(path.read_bytes())
    row['feedback']['results' if field=='response_text' else 'verifications'][0][field]=bad
    path.write_bytes(owned.module._json(row)); before=path.read_bytes(); stamp=path.stat().st_mtime_ns
    for fn in (owned.module.get_status,owned.module.get_view):
        response=fn(owned.root,r['review_id'],state_root=owned.state)
        assert response['status']=='unavailable' and response['reason']=='invalid_state',response
    for fn in (result,verify):
        response=fn(owned,r,expected_revision=0)
        assert response['reason']=='invalid_state' and response['approval_granted'] is False
        assert response['feedback_receipt'] is None
    assert path.read_bytes()==before and path.stat().st_mtime_ns==stamp


def test_gap_f24_record_reason_uses_contracted_state_budget(owned,monkeypatch):
    r=consumed(owned); before=stored(owned,r).read_bytes()
    monkeypatch.setattr(owned.module,'MAX_RECORD_BYTES',32)
    response=result(owned,r)
    assert response['reason']=='state_budget' and response['status']=='unavailable',response
    assert response['feedback_receipt'] is None and response['approval_granted'] is False
    assert stored(owned,r).read_bytes()==before
