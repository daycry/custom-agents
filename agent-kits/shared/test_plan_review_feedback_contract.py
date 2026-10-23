"""Remaining F07/F21/F23 oracles; isolated OWN fixtures, no browser or service."""
import copy
import json
import subprocess
import sys
import threading

import pytest

from test_plan_review import owned, ready, comment, submit, receive, ack, stored, SCRIPT, open_
from test_plan_review_feedback import consumed, result, verify, PRODUCER


def payload(r, operation):
    body = dict(version=r['version'], gate_key=r['gate_key'],
        decision_id=r['decision']['decision_id'], delivery_id=r['delivery']['delivery_id'],
        comment_id='one', result_id='1'*64, expected_revision=r['revision'], producer=PRODUCER)
    if operation == 'result':
        body.update(disposition='addressed', response_text='Changed scope.', supersedes_result_id=None)
    else:
        body.update(verification_id='4'*64, expected_revision=r['revision']+1,
                    assessment='confirmed', note='Checked by explicit instruction.')
    return body


def cli(o, r, operation):
    return subprocess.Popen([sys.executable, '-I', '-X', 'utf8', '-B', str(SCRIPT), operation,
        '--project', str(o.root), '--state-root', str(o.state), '--review-id', r['review_id']],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def finish(child, body):
    try:
        raw = body if isinstance(body, bytes) else json.dumps(body, ensure_ascii=False).encode('utf8')
        stdout, stderr = child.communicate(raw, timeout=15)
        assert stderr == b'' and child.returncode in (0, 2, 3), (child.returncode, stderr)
        response = json.loads(stdout)
        assert child.returncode == (0 if response['status'] == 'ok' else 2 if response['status'] == 'conflict' else 3)
        return response
    finally: drain(child)


def drain(child):
    """Terminal and actual pipe drain, including communicate's timeout path."""
    try:
        if child.poll() is None: child.kill()
        if any(stream is not None and not stream.closed for stream in (child.stdin, child.stdout, child.stderr)):
            try: child.communicate(timeout=15)
            except subprocess.TimeoutExpired:
                child.kill(); child.communicate(timeout=15)
    finally:
        if child.poll() is None: child.kill(); child.wait(timeout=15)
        for stream in (child.stdin, child.stdout, child.stderr):
            if stream is not None: stream.close()


def readiness_line(child, timeout=15):
    """Bound the holder's setup read; fixture timeout is unrelated to product budgets."""
    done = threading.Event(); lines = []; errors = []
    def read():
        try: lines.append(child.stdout.readline())
        except BaseException as exc: errors.append(exc)
        finally: done.set()
    reader = threading.Thread(target=read); reader.start(); completed = False
    try:
        if not done.wait(timeout): raise subprocess.TimeoutExpired(child.args, timeout)
        if errors: raise errors[0]
        reader.join(timeout=15)
        if reader.is_alive(): raise subprocess.TimeoutExpired(child.args, 15)
        completed = True
        return lines[0]
    finally:
        if not completed:
            if child.poll() is None: child.kill()
            child.wait(timeout=15); reader.join(timeout=15)
            drain(child)


@pytest.mark.parametrize('operation', ['result', 'verify-result'])
@pytest.mark.parametrize('same_id', [False, True], ids=['cas', 'dedup'])
def test_f07_two_real_cli_processes_and_restart(owned, operation, same_id):
    r = consumed(owned)
    if operation == 'verify-result': assert result(owned, r)['status'] == 'ok'
    initial = json.loads(stored(owned, r).read_bytes())
    bodies = [payload(r, operation), payload(r, operation)]
    id_key = 'result_id' if operation == 'result' else 'verification_id'
    if not same_id: bodies[1][id_key] = '2'*64 if operation == 'result' else '5'*64
    children = []; threads = []
    barrier = threading.Barrier(3); responses = [None, None]; errors = []
    def run(index):
        try:
            barrier.wait(timeout=15)
            responses[index] = finish(children[index], bodies[index])
        except BaseException as exc: errors.append(exc)
    try:
        for _ in range(2): children.append(cli(owned, r, operation))
        assert children[0].pid != children[1].pid
        threads = [threading.Thread(target=run, args=(i,)) for i in range(2)]
        for thread in threads: thread.start()
        barrier.wait(timeout=15)
        for thread in threads: thread.join(timeout=20)
        assert not any(thread.is_alive() for thread in threads) and not errors, errors
        assert all(child.poll() is not None for child in children)
        successes = [response for response in responses if response['status'] == 'ok']
        assert successes, responses
        collection = 'results' if operation == 'result' else 'verifications'
        row = json.loads(stored(owned, r).read_bytes())
        assert row['revision'] == initial['revision']+1 and len(row['feedback'][collection]) == 1
        assert all(row[key] == initial[key] for key in ('decision', 'delivery', 'ack'))
        if same_id:
            assert all(response['status'] == 'ok' or response['reason'] == 'state_busy' for response in responses)
            frozen = successes[0]
            before = stored(owned, r).read_bytes(); stamp = stored(owned, r).stat().st_mtime_ns
            retry = finish(cli(owned, r, operation), bodies[0])
            assert retry == frozen and stored(owned, r).read_bytes() == before
            assert stored(owned, r).stat().st_mtime_ns == stamp
        else:
            assert len(successes) == 1
            loser = next(i for i, response in enumerate(responses) if response['status'] != 'ok')
            assert responses[loser]['reason'] in ('revision_conflict', 'state_busy')
            before = stored(owned, r).read_bytes()
            assert finish(cli(owned, r, operation), bodies[loser])['reason'] == 'revision_conflict'
            assert stored(owned, r).read_bytes() == before
    finally:
        barrier.abort()
        for child in children:
            if child.poll() is None: child.kill()
        for thread in threads:
            if thread.ident is not None: thread.join(timeout=20)
        cleanup_errors = []
        for child in children:
            try: drain(child)
            except BaseException as exc: cleanup_errors.append(exc)
        if cleanup_errors: raise cleanup_errors[0]


@pytest.mark.parametrize('operation', ['result', 'verify-result'])
@pytest.mark.parametrize('extra', [0, 1], ids=['exact', 'plus1'])
def test_f21_original_stdin_16384_bytes(owned, operation, extra):
    r = consumed(owned)
    if operation == 'verify-result': assert result(owned, r)['status'] == 'ok'
    raw = json.dumps(payload(r, operation)).encode('utf8')
    raw += b' ' * (16384+extra-len(raw))
    assert len(raw) == 16384+extra
    before = stored(owned, r).read_bytes()
    response = finish(cli(owned, r, operation), raw)
    if extra:
        assert response['reason'] == 'request_budget' and response['feedback_receipt'] is None
        assert stored(owned, r).read_bytes() == before
    else: assert response['status'] == 'ok', response


@pytest.mark.parametrize('verification,kind,limit', [
    (False, 'codepoints', 1000), (False, 'utf8', 2048),
    (True, 'codepoints', 500), (True, 'utf8', 1024)])
@pytest.mark.parametrize('extra', [0, 1], ids=['exact', 'plus1'])
def test_f21_text_actual_boundaries(owned, verification, kind, limit, extra):
    r = consumed(owned)
    if verification: assert result(owned, r)['status'] == 'ok'
    text = 'x'*(limit+extra) if kind == 'codepoints' else '\U0001f680'*(limit//4)+'x'*extra
    assert (len(text) if kind == 'codepoints' else len(text.encode('utf8'))) == limit+extra
    before = stored(owned, r).read_bytes()
    response = verify(owned, r, note=text) if verification else result(owned, r, response_text=text)
    if extra:
        assert response['reason'] == 'feedback_text_budget' and response['feedback_receipt'] is None
        assert stored(owned, r).read_bytes() == before
    else: assert response['status'] == 'ok', response


@pytest.mark.parametrize('verification', [False, True], ids=['response', 'note'])
@pytest.mark.parametrize('kind', ['codepoints', 'utf8'])
@pytest.mark.parametrize('extra', [0, 1], ids=['exact', 'plus1'])
def test_f21_real_redactor_expansion_rechecked(owned, verification, kind, extra):
    m = owned.module
    limit = (500 if verification else 1000) if kind == 'codepoints' else (1024 if verification else 2048)
    suffix = ' token=Abcd1234'; clean = m._helper('redact.py').redactar(suffix)
    assert len(clean) > len(suffix)
    gap = limit+extra-len(clean)
    prefix = 'x'*gap if kind == 'codepoints' else '\U0001f680'*(gap//4)+'x'*(gap%4)
    text = prefix+suffix
    measure = len if kind == 'codepoints' else lambda value: len(value.encode('utf8'))
    assert measure(text) < limit and measure(m._helper('redact.py').redactar(text)) == limit+extra
    if extra:
        with pytest.raises(m._Failure) as failure: m._feedback_text(text, verification)
        assert failure.value.reason == 'feedback_text_budget'
    else:
        sanitized, flags = m._feedback_text(text, verification)
        assert measure(sanitized) == limit and flags['redacted'] is True


@pytest.mark.parametrize('verification', [False, True], ids=['response', 'note'])
def test_f21_input_limit_precedes_control_removal(owned, verification):
    m = owned.module; limit = 500 if verification else 1000
    with pytest.raises(m._Failure) as failure: m._feedback_text('x'*limit+'\x00', verification)
    assert failure.value.reason == 'feedback_text_budget'


def typed_record(o):
    """20 sealed comments, 40 valid result rows, 40 distinct optional annotations."""
    r = ready(o)
    comments = [dict(comment(r)[0], comment_id='c'+str(i)) for i in range(20)]
    response = submit(o, r, 'request_changes', comments)
    if response['status'] != 'ok':
        raise AssertionError(('submit', response))
    r = response['review']
    response = receive(o, r)
    if response['status'] != 'ok':
        raise AssertionError(('receive', response))
    r = response['review']
    response = ack(o, r)
    if response['status'] != 'ok':
        raise AssertionError(('ack', response))
    r = response['review']
    assert result(o, r, comment_id='c0', response_text='x')['status'] == 'ok'
    assert verify(o, r, comment_id='c0', note='')['status'] == 'ok'
    record = json.loads(stored(o, r).read_bytes())
    template_result = record['feedback']['results'][0]; template_verify = record['feedback']['verifications'][0]
    feedback = record['feedback']; feedback['results'] = []; feedback['verifications'] = []
    for index in range(40):
        identifier = format(index+1, '064x'); previous = format(index, '064x') if index%2 else None
        row = copy.deepcopy(template_result)
        row.update(result_id=identifier, comment_id='c'+str(index//2), supersedes_result_id=previous)
        row['producer']['caller_id'] = 'x'
        feedback['results'].append(row)
        annotation = copy.deepcopy(template_verify)
        annotation.update(verification_id=format(index+101, '064x'), result_id=identifier,
                          comment_id=row['comment_id'])
        annotation['producer']['caller_id'] = 'x'; feedback['verifications'].append(annotation)
    o.module._validate_feedback(record)
    return record


@pytest.mark.parametrize('stage', ['submit', 'receive', 'ack'])
def test_fixture_retains_failed_setup_envelope(monkeypatch, stage):
    """A failed setup must retain its stage and envelope before using review."""
    review = {'fixture': 'review'}
    failed = {'schema_version': 1, 'status': 'unavailable',
              'reason': stage + '_fixture_failure', 'review': None}
    monkeypatch.setitem(globals(), 'ready', lambda _: review)
    monkeypatch.setitem(globals(), 'comment', lambda _: [{'comment_id': 'one'}])
    for name in ('submit', 'receive', 'ack'):
        envelope = failed if name == stage else {'status': 'ok', 'review': review}
        monkeypatch.setitem(globals(), name, lambda *args, envelope=envelope: envelope)
    with pytest.raises(AssertionError) as caught:
        typed_record(object())
    assert caught.value.args == ((stage, failed),)


@pytest.mark.parametrize('quota,limit', [('response_bytes', 16384), ('note_bytes', 4096),
    ('results', 40), ('verifications', 40), ('feedback_json', 49152)])
@pytest.mark.parametrize('extra', [0, 1], ids=['exact', 'plus1'])
def test_f21_feedback_aggregate_boundaries(owned, quota, limit, extra):
    m = owned.module; record = typed_record(owned); feedback = record['feedback']
    if quota == 'response_bytes':
        feedback['results'] = feedback['results'][:20]; feedback['verifications'] = []
        # Each retained pair still has its valid supersession chain; each text <=1000.
        remaining = limit
        for row in feedback['results']:
            size = min(820, remaining); row['response_text'] = 'x'*size; remaining -= size
        assert remaining == 0
        if extra: feedback['results'][-1]['response_text'] += 'x'
        actual = sum(len(row['response_text'].encode('utf8')) for row in feedback['results'])
    elif quota == 'note_bytes':
        feedback['results'] = feedback['results'][:10]; feedback['verifications'] = feedback['verifications'][:10]
        remaining = limit
        for row in feedback['verifications']:
            size = min(450, remaining); row['note'] = 'x'*size; remaining -= size
        assert remaining == 0
        if extra: feedback['verifications'][-1]['note'] += 'x'
        actual = sum(len(row['note'].encode('utf8')) for row in feedback['verifications'])
    elif quota in ('results', 'verifications'):
        if quota == 'results': feedback['verifications'] = []
        if extra: feedback[quota].append(copy.deepcopy(feedback[quota][-1]))
        actual = len(feedback[quota])
    else:
        gap = limit-len(m._json(feedback)); assert gap >= 0
        # Quotes count twice in JSON but once in the aggregate UTF-8 text quota.
        for row in feedback['results']:
            amount = min(999, gap//2); row['response_text'] += '"'*amount; gap -= amount*2
        assert gap <= 1
        feedback['results'][-1]['response_text'] += 'x'*(gap+extra)
        actual = len(m._json(feedback))
    assert actual == limit+extra
    if extra:
        with pytest.raises(m._Failure) as failure: m._feedback_limits(feedback)
        assert failure.value.reason == 'feedback_budget'
    else: m._validate_feedback(record)


@pytest.mark.parametrize('extra', [0, 1], ids=['exact', 'plus1'])
def test_f21_record_writer_actual_98304_bytes(owned, extra):
    """Serialization primitive, deliberately not an accepted semantic review record."""
    m = owned.module; ready(owned)
    value = {'fixture_padding': ''}; value['fixture_padding'] = 'x'*(98304+extra-len(m._json(value)))
    assert len(m._json(value)) == 98304+extra
    path = owned.state/'writer-boundary.json'
    previous = b'{"fixture_padding":"previous"}'; path.write_bytes(previous)
    stamp = path.stat().st_mtime_ns; reader = m._helper('local-read.py'); signature = m._file(path, reader)
    if extra:
        with pytest.raises(m._Failure) as failure:
            m._write(path, value, reader, m._deadline(None), expected=signature)
        assert failure.value.reason == 'state_budget' and path.read_bytes() == previous
        assert path.stat().st_mtime_ns == stamp
    else:
        m._write(path, value, reader, m._deadline(None), expected=signature)
        assert path.read_bytes() == m._json(value)


@pytest.mark.parametrize('extra', [0, 1], ids=['exact', 'plus1'])
def test_f21_envelope_actual_524288_bytes(owned, extra):
    """Envelope serializer layer; padding is not a semantic plan/authorization."""
    m = owned.module; review = {'fixture_padding': ''}
    review['fixture_padding'] = 'x'*(524288+extra-len(m._json(m._envelope(review=review))))
    if extra:
        with pytest.raises(m._Failure) as failure: m._envelope(review=review)
        assert failure.value.reason == 'response_budget'
    else: assert len(m._json(m._envelope(review=review))) == 524288


@pytest.mark.parametrize('drop_to_null', [False, True], ids=['whole-row', 'null'])
def test_f21_envelope_optional_history_trims_without_truncating_current(owned, drop_to_null):
    m = owned.module
    final_history = None if drop_to_null else {'schema_version': 1, 'complete': False, 'reviews': []}
    review = {'fixture_current_text': '', 'feedback_history': final_history}
    prefix = m._json(m._envelope(review=copy.deepcopy(review)))
    review['fixture_current_text'] = 'x'*(524288-len(prefix))
    current_text = review['fixture_current_text']
    review['feedback_history'] = {'schema_version': 1, 'complete': True, 'reviews': [{'fixture_row': 'full'}]}
    output = m._envelope(review=review)
    assert len(m._json(output)) == 524288 and output['review']['fixture_current_text'] == current_text
    assert output['review']['feedback_history'] == final_history


@pytest.mark.parametrize('extra', [0, 1], ids=['exact', 'plus1'])
def test_f21_history_actual_65536_bytes_whole_rows(owned, extra):
    m = owned.module; first = typed_record(owned)
    first['feedback']['results'] = first['feedback']['results'][:32]
    first['feedback']['verifications'] = first['feedback']['verifications'][:32]
    owned.plan.write_bytes(owned.plan.read_bytes()+b'Next historical version\n')
    second = typed_record(owned)
    second['feedback']['results'] = second['feedback']['results'][:10]
    second['feedback']['verifications'] = second['feedback']['verifications'][:10]
    current = dict(second, review_id='0'*64)
    def unbounded_candidate():
        rows = [m._feedback_history(current, [record])['reviews'][0] for record in (first, second)]
        return {'schema_version': 1, 'complete': True, 'reviews': rows}
    gap = 65536-len(m._json(unbounded_candidate())); assert gap >= 0
    for record in (first, second):
        for row in record['feedback']['results']:
            available = min(999, (49152-len(m._json(record['feedback'])))//2, gap//2)
            row['response_text'] += '"'*available; gap -= available*2
    assert gap <= 1
    second['feedback']['results'][-1]['response_text'] += 'x'*(gap+extra)
    for record in (first, second): m._validate_feedback(record)
    assert len(m._json(unbounded_candidate())) == 65536+extra
    history = m._feedback_history(current, [first, second])
    assert len(m._json(history)) <= 65536
    if extra:
        assert history['complete'] is False and len(history['reviews']) == 1
    else:
        assert history['complete'] is True and len(history['reviews']) == 2
        assert len(m._json(history)) == 65536
    expected = {record['review_id']: m._feedback_projection(record) for record in (first, second)}
    assert all(row['feedback'] == expected[row['review_id']] for row in history['reviews'])


def test_f21_inventory_accepts_64th_and_rejects_65th_without_purge(owned, monkeypatch):
    """Quota oracle: fixed unit clock isolates capacity from machine latency (reported separately)."""
    m = owned.module; r = ready(owned); base = json.loads(stored(owned, r).read_bytes())
    marker = json.loads((owned.state/'owner.json').read_bytes())
    for index in range(62):
        row = copy.deepcopy(base)
        row['version']['raw_sha256'] = format(index+1, '064x')
        row['review_id'] = m._review_id(marker, row['initiative'], row['version'], row['gate_key'])
        (owned.state/('r-'+row['review_id']+'.json')).write_bytes(m._json(row))
    assert len(list(owned.state.glob('r-*.json'))) == 63
    # The existing default remains 3 seconds (100 -> 103); no raised product deadline.
    monkeypatch.setattr(m.time, 'monotonic', lambda: 100.0)
    owned.plan.write_bytes(owned.plan.read_bytes()+b'64th version\n')
    accepted = open_(owned); assert accepted['status'] == 'ok', accepted
    prior = {path.name: path.read_bytes() for path in owned.state.glob('r-*.json')}
    assert len(prior) == 64
    owned.plan.write_bytes(owned.plan.read_bytes()+b'65th version\n')
    rejected = open_(owned); assert rejected['reason'] == 'state_budget', rejected
    assert {path.name: path.read_bytes() for path in owned.state.glob('r-*.json')} == prior
    assert all(json.loads(raw)['state'] == 'pendiente' and json.loads(raw)['ack'] is None for raw in prior.values())


@pytest.mark.parametrize('operation,stage', [('result', 'validation'), ('verify-result', 'validation'),
    ('result', 'observation'), ('result', 'pre_replace'), ('verify-result', 'pre_replace')])
def test_f23_deadline_before_commit_preserves_exact_bytes(owned, monkeypatch, operation, stage):
    m = owned.module; r = consumed(owned); fn = result if operation == 'result' else verify
    if operation == 'verify-result': assert result(owned, r)['status'] == 'ok'
    path = stored(owned, r); before = path.read_bytes(); stamp = path.stat().st_mtime_ns
    clock = [100.0]
    with monkeypatch.context() as patch:
        patch.setattr(m.time, 'monotonic', lambda: clock[0])
        if stage == 'validation':
            original = m._producer
            def expire(value, stored=False):
                validated = original(value, stored)
                if not stored: clock[0] = 102.0
                return validated
            patch.setattr(m, '_producer', expire)
        elif stage == 'observation':
            original = m._observe_artifact
            def expire(*args, **kwargs):
                observed = original(*args, **kwargs); clock[0] = 102.0
                return observed
            patch.setattr(m, '_observe_artifact', expire)
        else:
            original = m.os.fsync
            def expire(*args, **kwargs):
                original(*args, **kwargs); clock[0] = 102.0
            patch.setattr(m.os, 'fsync', expire)
        failed = fn(owned, r, deadline=101.0)
    assert failed['reason'] == 'deadline_expired' and failed['feedback_receipt'] is None, failed
    assert path.read_bytes() == before and path.stat().st_mtime_ns == stamp
    assert not list(owned.state.glob('.tmp-*'))
    assert fn(owned, r)['status'] == 'ok'


@pytest.mark.parametrize('operation', ['result', 'verify-result'])
def test_f23_real_cross_process_lock_busy_and_recovery(owned, operation):
    r = consumed(owned)
    if operation == 'verify-result': assert result(owned, r)['status'] == 'ok'
    holder_source = owned.root/'lock_holder.py'
    holder_source.write_text("import os,sys\nf=open(sys.argv[1],'r+b')\n"
        "if os.name=='nt':\n import msvcrt\n msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)\n"
        "else:\n import fcntl\n fcntl.lockf(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB,1,0,0)\n"
        "print('locked',flush=True)\nsys.stdin.readline()\nf.close()\n", encoding='utf8')
    holder = subprocess.Popen([sys.executable, '-I', '-X', 'utf8', '-B', str(holder_source), str(owned.state/'.lock')],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        assert readiness_line(holder).rstrip(b'\r\n') == b'locked'
        before = stored(owned, r).read_bytes()
        blocked = finish(cli(owned, r, operation), payload(r, operation))
        assert blocked['reason'] == 'state_busy' and blocked['feedback_receipt'] is None
        assert stored(owned, r).read_bytes() == before
    finally:
        try:
            if holder.poll() is None:
                stdout, stderr = holder.communicate(b'close\n', timeout=15)
                assert holder.returncode == 0 and stdout == b'' and stderr == b''
        finally: drain(holder)
    assert finish(cli(owned, r, operation), payload(r, operation))['status'] == 'ok'


@pytest.mark.parametrize('operation', ['result', 'verify-result'])
@pytest.mark.parametrize('stage', ['temp_write', 'temp_flush', 'temp_fsync', 'replace',
    'directory_flush', 'dedup_fsync', 'postcommit_deadline'])
def test_f23_io_failure_and_exact_retry_truth(owned, monkeypatch, operation, stage):
    m = owned.module; r = consumed(owned); fn = result if operation == 'result' else verify
    if operation == 'verify-result': assert result(owned, r)['status'] == 'ok'
    if stage == 'dedup_fsync': assert fn(owned, r)['status'] == 'ok'
    path = stored(owned, r); before = path.read_bytes(); stamp = path.stat().st_mtime_ns
    baseline = json.loads(before); clock = [100.0]
    def fail(*args, **kwargs): raise OSError('OWN injected persistence failure')
    with monkeypatch.context() as patch:
        kwargs = {}
        if stage in ('temp_write', 'temp_flush'):
            original = m.os.fdopen
            class BrokenTemporary:
                def __init__(self, handle): self.handle = handle
                def __enter__(self): self.handle.__enter__(); return self
                def __exit__(self, *args): return self.handle.__exit__(*args)
                def write(self, raw):
                    if stage == 'temp_write': self.handle.write(raw[:16]); fail()
                    return self.handle.write(raw)
                def flush(self):
                    if stage == 'temp_flush': fail()
                    return self.handle.flush()
                def fileno(self): return self.handle.fileno()
            def temporary_only(fd, mode, *args, **kwargs):
                handle = original(fd, mode, *args, **kwargs)
                return BrokenTemporary(handle) if mode == 'wb' else handle
            patch.setattr(m.os, 'fdopen', temporary_only)
        elif stage in ('temp_fsync', 'dedup_fsync'): patch.setattr(m.os, 'fsync', fail)
        elif stage == 'replace': patch.setattr(m.os, 'replace', fail)
        elif stage == 'directory_flush': patch.setattr(m, '_sync_dir', fail)
        else:
            original = m._write
            def commit_then_expire(*args, **kwargs):
                original(*args, **kwargs); clock[0] = 102.0
            patch.setattr(m.time, 'monotonic', lambda: clock[0])
            patch.setattr(m, '_write', commit_then_expire); kwargs['deadline'] = 101.0
        failed = fn(owned, r, **kwargs)
    assert failed['status'] == 'unavailable' and failed['feedback_receipt'] is None
    assert failed['approval_granted'] is False
    expected_reason = 'invalid_input' if stage in ('temp_write', 'temp_flush', 'replace') else 'deadline_expired' if stage == 'postcommit_deadline' else 'durability_degraded'
    assert failed['reason'] == expected_reason, failed
    collection = 'results' if operation == 'result' else 'verifications'
    after_failure = json.loads(path.read_bytes())
    committed = stage in ('directory_flush', 'postcommit_deadline')
    if not committed:
        assert path.read_bytes() == before and path.stat().st_mtime_ns == stamp
    else:
        assert after_failure['revision'] == baseline['revision']+1
        assert len(after_failure['feedback'][collection]) == len(baseline['feedback'][collection])+1
    assert all(after_failure[key] == baseline[key] for key in ('decision', 'delivery', 'ack'))
    assert not list(owned.state.glob('.tmp-*'))
    recovered = fn(owned, r)
    assert recovered['status'] == 'ok', recovered
    after_retry = path.read_bytes(); final = json.loads(after_retry)
    assert final['revision'] == baseline['revision']+(0 if stage == 'dedup_fsync' else 1)
    assert len(final['feedback'][collection]) == len(baseline['feedback'][collection])+(0 if stage == 'dedup_fsync' else 1)
    if committed: assert recovered['feedback_receipt']['recorded_at'] == after_failure['feedback'][collection][-1]['recorded_at']
    assert fn(owned, r) == recovered and path.read_bytes() == after_retry
