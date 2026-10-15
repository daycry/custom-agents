"""summarize_reviews / `plan-review.py summary`: read-only state of many initiatives."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import time
import sys
from types import SimpleNamespace

import pytest

HERE = Path(__file__).parent
SCRIPT = HERE / 'plan-review.py'
PREFIX = 'docs/roadmap/2026-10-15-'
STATES = {'sin_revision', 'pendiente', 'cambios_pedidos', 'aprobada', 'obsoleta', 'no_disponible'}


def load():
    spec = importlib.util.spec_from_file_location('plan_review_summary_test', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def o(tmp_path):
    return SimpleNamespace(root=tmp_path, state=tmp_path / '.claude/plan-review', m=load())


def plan(o, slug, text='# Plan\n\n## Scope\nBody.\n'):
    path = o.root / (PREFIX + slug) / 'improvement-plan.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8', newline='')
    return PREFIX + slug


def review(o, slug, choice=None, text='# Plan\n\n## Scope\nBody.\n', gate='requested-review'):
    initiative = plan(o, slug, text)
    r = o.m.open_review(o.root, initiative, state_root=o.state, gate_key=gate)['review']
    if choice:
        comments = [{'comment_id': 'c1', 'section_id': r['sections'][-1]['section_id'], 'text': 'Fix'}]
        done = o.m.submit_decision(o.root, r['review_id'], r['version'], choice,
                                   comments if choice == 'request_changes' else [],
                                   expected_revision=r['revision'], state_root=o.state)
        assert done['status'] == 'ok', done
    return initiative


def summary(o, initiatives, **kw):
    return o.m.summarize_reviews(o.root, initiatives, state_root=o.state, **kw)


def tree(o):
    out = {}
    for p in sorted(o.root.rglob('*')):
        if p.is_file() and '.claude' in p.parts:
            out[str(p.relative_to(o.root))] = (p.stat().st_size, hashlib.sha256(p.read_bytes()).hexdigest())
    return out


def by(result):
    return {r['initiative']: r for r in result['initiatives']}


def test_six_states_vn_and_closed_vocabulary(o):
    a = review(o, 'pend')
    b = review(o, 'chg', 'request_changes')
    c = review(o, 'apr', 'approve')
    d = review(o, 'old', 'approve')
    plan(o, 'old', '# Plan\n\n## Scope\nChanged body.\n')
    e = plan(o, 'none')
    f = review(o, 'gone', 'approve')
    (o.root / f / 'improvement-plan.md').unlink()
    result = summary(o, [a, b, c, d, e, f])
    assert result['status'] == 'ok' and result['complete'] is True and result['approval_granted'] is False
    rows = by(result)
    assert {r['estado'] for r in rows.values()} == STATES
    assert rows[a]['estado'] == 'pendiente' and rows[b]['estado'] == 'cambios_pedidos'
    assert rows[c]['estado'] == 'aprobada' and rows[c]['version_ordinal'] == 1
    assert rows[d]['estado'] == 'obsoleta' and rows[e]['estado'] == 'sin_revision'
    assert rows[f]['estado'] == 'no_disponible' and rows[f]['plan'] == 'missing'
    assert rows[b]['comments'] == 1 and rows[a]['review_id'] and rows[a]['gate_key'] == 'requested-review'
    assert len(json.dumps(result)) < 64 * 1024


def test_version_ordinal_is_stable_across_versions(o):
    slug = 'multi'
    initiative = review(o, slug, 'approve')
    review(o, slug, 'approve', text='# Plan\n\n## Scope\nSecond.\n')
    result = by(summary(o, [initiative]))[initiative]
    assert result['estado'] == 'aprobada' and result['version_ordinal'] == 2


def test_obsolete_by_view_sha_when_raw_matches(o, monkeypatch):
    initiative = review(o, 'view', 'approve')
    real = o.m._view
    def other(*a, **k):
        v = real(*a, **k)
        v['version'] = dict(v['version'], view_sha256='f' * 64)
        return v
    monkeypatch.setattr(o.m, '_view', other)
    row = by(summary(o, [initiative]))[initiative]
    assert row['estado'] == 'obsoleta'


def test_missing_state_returns_sin_revision_and_creates_nothing(o):
    initiative = plan(o, 'fresh')
    result = summary(o, [initiative])
    assert result['status'] == 'ok' and by(result)[initiative]['estado'] == 'sin_revision'
    assert not (o.root / '.claude').exists()


def test_tree_identical_and_works_with_lock_held(o):
    a = review(o, 'one', 'approve')
    b = review(o, 'two')
    before = tree(o)
    assert (o.state / '.lock').exists()
    code = ("import os,sys\nf=open(sys.argv[1],'r+b')\nif os.name=='nt':\n import msvcrt;msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)\n"
            "else:\n import fcntl;fcntl.flock(f.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)\nprint('locked',flush=True);sys.stdin.readline()")
    child = subprocess.Popen([sys.executable, '-X', 'utf8', '-B', '-c', code, str(o.state / '.lock')],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                             encoding='utf-8')
    try:
        assert child.stdout.readline().strip() == 'locked'
        result = summary(o, [a, b])
        assert result['status'] == 'ok' and by(result)[a]['estado'] == 'aprobada'
    finally:
        child.stdin.write('\n'); child.stdin.flush(); child.wait(5)
    assert tree(o) == before


def test_deadline_expired_gives_partial_never_another_state(o, monkeypatch):
    a = review(o, 'one', 'approve')
    b = review(o, 'two', 'approve')
    real = o.m._view
    calls = []
    def slow(*args, **kw):
        calls.append(1)
        if len(calls) == 2: raise o.m._Failure('deadline_expired')
        return real(*args, **kw)
    monkeypatch.setattr(o.m, '_view', slow)
    result = summary(o, [a, b], deadline=time.monotonic() + 120)
    assert result['status'] == 'partial' and result['reason'] == 'deadline_expired' and result['complete'] is False
    assert sorted(r['estado'] for r in result['initiatives']) == ['aprobada', 'no_disponible']
    assert summary(o, [a], deadline=0)['status'] == 'unavailable'


def test_state_changed_during_read(o, monkeypatch):
    a = review(o, 'one', 'approve')
    other = plan(o, 'late')
    real = o.m._view
    def meddle(*args, **kw):
        out = real(*args, **kw)
        o.m.open_review(o.root, other, state_root=o.state)
        return out
    monkeypatch.setattr(o.m, '_view', meddle)
    result = summary(o, [a], deadline=time.monotonic() + 120)
    assert result['status'] == 'unavailable' and result['reason'] == 'state_changed'


def test_plan_changed_during_read(o, monkeypatch):
    a = review(o, 'one', 'approve')
    real = o.m._view
    def meddle(*args, **kw):
        out = real(*args, **kw)
        plan(o, 'one', '# Plan\n\nMeanwhile.\n')
        return out
    monkeypatch.setattr(o.m, '_view', meddle)
    assert summary(o, [a], deadline=time.monotonic() + 120)['reason'] == 'state_changed'


def test_sixty_four_records_fit_the_envelope(o):
    initiatives = [review(o, 'p%02d' % i, 'approve' if i % 2 else None) for i in range(64)]
    before = tree(o)
    result = summary(o, initiatives, deadline=time.monotonic() + 120)
    assert result['status'] == 'ok' and len(result['initiatives']) == 64
    assert len(json.dumps(result)) < 64 * 1024 and tree(o) == before
    assert summary(o, initiatives + [PREFIX + 'extra'])['status'] == 'unavailable'


@pytest.mark.parametrize('bad', ['docs/roadmap/x', '../x', 7])
def test_invalid_initiative_is_unavailable(o, bad):
    assert summary(o, [bad])['status'] == 'unavailable'


def test_state_root_must_be_the_project_scope(o):
    result = o.m.summarize_reviews(o.root, [], state_root=o.root / 'elsewhere')
    assert result['status'] == 'unavailable' and result['reason'] == 'state_scope'


def run_cli(o, payload, raw=None):
    data = raw if raw is not None else json.dumps(payload).encode()
    return subprocess.run([sys.executable, '-X', 'utf8', '-B', str(SCRIPT), 'summary', '--project', str(o.root),
                           '--state-root', str(o.state)], input=data, capture_output=True, timeout=30)


def test_cli_exit_codes_and_stdin_limit(o):
    a = review(o, 'one', 'approve')
    done = run_cli(o, [a])
    assert done.returncode == 0 and json.loads(done.stdout)['initiatives'][0]['estado'] == 'aprobada'
    bad = run_cli(o, None, raw=b'[' + b'"x",' * 5000 + b'"x"]')
    assert bad.returncode == 3 and json.loads(bad.stdout)['reason'] == 'request_budget'
    assert run_cli(o, {'not': 'list'}).returncode == 3
