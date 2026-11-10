"""Fase 4, intento 2 (fix2), gap 2: la iniciativa se fija al capturar, no al materializar."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / 'agent-kits/shared'


def _ledger(project, slug, state='en-progreso', mtime=None):
    folder = project / 'docs' / 'roadmap' / slug
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / 'tasks.md'
    path.write_text(f"---\ntasks: {slug}\nestado: {state}\ncreado: 2026-01-01\n---\n\n# X\n\n## Fase 1\n\n"
                    "### T-01 — a\n- **Estado**: borrador\n\n**Criterios de aceptación**\n- [ ] a\n", encoding='utf-8')
    if mtime:
        os.utime(path, (mtime, mtime))


def _run(script, *args, stdin=None):
    env = {k: v for k, v in os.environ.items() if k != 'CLAUDE_PLUGIN_ROOT'}
    return subprocess.run([sys.executable, str(KIT / script), *args], input=stdin, capture_output=True, text=True,
                          encoding='utf-8', env=env, timeout=120)


def _capture_at(project, age_hours, *, strip_initiative=False):
    (project / '.claude').mkdir(exist_ok=True)
    (project / '.claude' / 'session-prompts-s1.log').write_text(
        json.dumps({'ts': '2026-01-01T00:00:00Z', 'text': 'Decidimos revisar el kit'}) + '\n', encoding='utf-8')
    payload = {'hook_event_name': 'SessionEnd', 'session_id': 's1', 'reason': 'other', 'cwd': str(project)}
    done = _run('journal.py', 'capture-end', '--root', str(project), stdin=json.dumps(payload))
    assert done.returncode == 0
    outbox = project / '.claude' / 'journal' / 'outbox'
    (path,) = list(outbox.glob('*.json'))
    envelope = json.loads(path.read_text(encoding='utf-8'))
    envelope['captured_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() - age_hours * 3600))
    if strip_initiative:
        envelope.pop('iniciativa', None)
    path.write_text(json.dumps(envelope), encoding='utf-8')
    return envelope


def _startup_block(project):
    return _run('progress-report.py', 'resume', '--root', str(project), '--history-only').stdout


def _scenario(tmp_path, age_hours, **kw):
    project = tmp_path / 'p'
    now = time.time()
    _ledger(project, '2026-11-01-alfa', mtime=now)
    envelope = _capture_at(project, age_hours, **kw)
    # Between the capture and the replay the work moves to another initiative.
    _ledger(project, '2026-11-02-beta', mtime=now + 10)
    (project / 'docs' / 'roadmap' / '2026-11-01-alfa' / 'tasks.md').write_text(
        (project / 'docs' / 'roadmap' / '2026-11-01-alfa' / 'tasks.md').read_text(encoding='utf-8').replace('en-progreso', 'completado'), encoding='utf-8')
    replay = _run('journal.py', 'replay', '--root', str(project), '--ia', 'no')
    assert replay.returncode == 0, replay.stderr
    return project, envelope


def test_f4fix2_2_the_envelope_records_the_initiative_active_at_capture(tmp_path):
    project = tmp_path / 'p'
    _ledger(project, '2026-11-01-alfa')
    assert _capture_at(project, 0)['iniciativa'] == 'alfa'


def test_f4fix2_2_replay_keeps_the_captured_initiative_at_0_2_and_14_hours(tmp_path):
    for hours in (0, 2, 14):
        sub = tmp_path / f'h{hours}'
        sub.mkdir()
        project, _ = _scenario(sub, hours)
        entries = [p for p in (project / 'docs/knowledge/journal').glob('*.md') if p.name != 'README.md']
        assert len(entries) == 1, hours
        text = entries[0].read_text(encoding='utf-8')
        assert 'iniciativa: "alfa"' in text and 'regla_iniciativa: "vigente"' in text, (hours, text)


def test_f4fix2_2_an_old_envelope_without_initiative_uses_the_longer_threshold(tmp_path):
    (tmp_path / 'a').mkdir()
    (tmp_path / 'b').mkdir()
    recent, _ = _scenario(tmp_path / 'a', 14, strip_initiative=True)
    old, _ = _scenario(tmp_path / 'b', 30, strip_initiative=True)
    mark = lambda p: 'regla_iniciativa' in next(q for q in (p / 'docs/knowledge/journal').glob('*.md') if q.name != 'README.md').read_text(encoding='utf-8')
    assert mark(recent) and not mark(old)


def test_f4fix2_2_the_startup_block_says_when_it_omits_history(tmp_path):
    project, _ = _scenario(tmp_path, 30, strip_initiative=True)
    # the unattributed entry belongs to the initiative named in its file, not to the current one: list by that slug
    entries = [p for p in (project / 'docs/knowledge/journal').glob('*.md') if p.name != 'README.md']
    assert entries and 'regla_iniciativa' not in entries[0].read_text(encoding='utf-8')
    block = _startup_block(project)
    assert 'omitida' in block, block
