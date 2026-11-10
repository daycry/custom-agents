"""Fase 4, intento 3 (fix3), gap 2: una sola regla de «iniciativa en curso» (la de progress-report)."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / 'agent-kits/shared'
NOW = time.time()


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, KIT / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _ledger(project, folder, fm_estado=None, table_estado=None, done=False, mtime=None):
    d = project / 'docs' / 'roadmap' / folder
    d.mkdir(parents=True, exist_ok=True)
    fm = '---\ntasks: x\n' + (f'estado: {fm_estado}\n' if fm_estado else '') + '---\n\n# T\n\n'
    table = f'| | |\n|---|---|\n| **Estado** | {table_estado} |\n\n' if table_estado else ''
    st, ck = ('completado', 'x') if done else ('borrador', ' ')
    path = d / 'tasks.md'
    path.write_text(fm + table + f'## Fase 1\n\n### T-01 — a\n- **Estado**: {st}\n\n**Criterios de aceptación**\n- [{ck}] a\n', encoding='utf-8')
    if mtime:
        os.utime(path, (mtime, mtime))


def _marker(project, key):
    (project / '.claude').mkdir(exist_ok=True)
    (project / '.claude' / 'usage-state.json').write_text(json.dumps({key: {'inicio': '2026-01-01T00:00:00Z'}}), encoding='utf-8')


def _run(script, *args, stdin=None):
    env = {k: v for k, v in os.environ.items() if k != 'CLAUDE_PLUGIN_ROOT'}
    return subprocess.run([sys.executable, str(KIT / script), *args], input=stdin, capture_output=True, text=True,
                          encoding='utf-8', env=env, timeout=180)


def _roundtrip(project, age_hours, *, current_after=None):
    """capture-end now, age the envelope, optionally move the work, replay: the entry that results."""
    (project / '.claude').mkdir(exist_ok=True)
    (project / '.claude' / 'session-prompts-s1.log').write_text(json.dumps({'ts': 'x', 'text': 'Decidimos algo'}) + '\n', encoding='utf-8')
    payload = {'hook_event_name': 'SessionEnd', 'session_id': 's1', 'reason': 'other', 'cwd': str(project)}
    assert _run('journal.py', 'capture-end', '--root', str(project), stdin=json.dumps(payload)).returncode == 0
    (path,) = list((project / '.claude' / 'journal' / 'outbox').glob('*.json'))
    envelope = json.loads(path.read_text(encoding='utf-8'))
    envelope['captured_at'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(time.time() - age_hours * 3600))
    path.write_text(json.dumps(envelope), encoding='utf-8')
    if current_after:
        current_after()
    replay = _run('journal.py', 'replay', '--root', str(project), '--ia', 'no')
    assert replay.returncode == 0, replay.stderr
    dead = project / '.claude' / 'journal' / 'dead-letter'
    assert not (dead.exists() and any(dead.glob('*.json'))), 'the session went to dead-letter'
    (entry,) = [p for p in (project / 'docs/knowledge/journal').glob('*.md') if p.name != 'README.md']
    return envelope, entry.read_text(encoding='utf-8')


def _rule(project):
    pr = _load('f4fix3_pr', 'progress-report.py')
    return pr.iniciativa_vigente(str(project))


def test_f4fix3_2_capture_reads_no_ledger_and_scans_no_roadmap():
    source = (KIT / 'journal-capture.py').read_text(encoding='utf-8')
    assert '_iniciativa_al_capturar' not in source and 'scandir' not in source
    assert 'tasks.md' not in source


def test_f4fix3_2_without_a_marker_the_single_rule_decides_at_0_2_and_14_hours(tmp_path):
    scenarios = {
        'state in the table': lambda p: (_ledger(p, '2026-01-01-vieja', 'en-progreso', mtime=NOW - 100),
                                         _ledger(p, '2026-01-02-actual', table_estado='en-progreso', mtime=NOW)),
        'state with a comment': lambda p: (_ledger(p, '2026-01-01-a', 'en-progreso', mtime=NOW - 100),
                                           _ledger(p, '2026-01-02-b', 'en-progreso   # borrador | en-progreso', mtime=NOW)),
        'newest at 100 percent': lambda p: (_ledger(p, '2026-01-01-pend', 'en-progreso', mtime=NOW - 100),
                                            _ledger(p, '2026-01-02-hecha', 'en-progreso', done=True, mtime=NOW)),
    }
    for name, build in scenarios.items():
        for hours in (0, 2, 14):
            project = tmp_path / f'{abs(hash((name, hours)))}'
            project.mkdir()
            build(project)
            envelope, text = _roundtrip(project, hours)
            assert 'iniciativa' not in envelope, (name, envelope)
            assert f'iniciativa: "{_rule(project)}"' in text, (name, hours, text)
            assert 'regla_iniciativa: "vigente"' in text, (name, hours)


def test_f4fix3_2_an_open_marker_is_the_initiative_even_if_the_work_moves_before_the_replay(tmp_path):
    project = tmp_path / 'm'
    project.mkdir()
    _ledger(project, '2026-01-01-alfa', 'en-progreso', mtime=NOW)
    _ledger(project, '2026-01-02-beta', 'en-progreso', mtime=NOW - 100)
    _marker(project, 'docs/roadmap/2026-01-01-alfa/tasks.md')
    def moves():
        _marker(project, 'docs/roadmap/2026-01-02-beta/tasks.md')
    envelope, text = _roundtrip(project, 14, current_after=moves)
    assert envelope['iniciativa'] == 'alfa'
    assert 'iniciativa: "alfa"' in text and 'regla_iniciativa: "vigente"' in text


def test_f4fix3_2_a_folder_with_accent_or_space_goes_to_the_single_rule_not_to_dead_letter(tmp_path):
    for folder in ('2026-01-01-ñandú', '2026-01-01-mi plan'):
        project = tmp_path / ('p' + str(abs(hash(folder))))
        project.mkdir()
        _ledger(project, folder, 'en-progreso', mtime=NOW)
        _marker(project, f'docs/roadmap/{folder}/tasks.md')
        envelope, text = _roundtrip(project, 2)
        assert 'iniciativa' not in envelope, folder              # not storable: the rule decides at replay
        assert f'iniciativa: "{_rule(project)}"' in text, (folder, text)


def test_f4fix3_2_an_old_envelope_with_an_invalid_slug_is_not_dead_lettered(tmp_path):
    project = tmp_path / 'old'
    project.mkdir()
    _ledger(project, '2026-01-01-alfa', 'en-progreso', mtime=NOW)
    (project / '.claude').mkdir()
    (project / '.claude' / 'session-prompts-s1.log').write_text(json.dumps({'ts': 'x', 'text': 'Decidimos algo'}) + '\n', encoding='utf-8')
    payload = {'hook_event_name': 'SessionEnd', 'session_id': 's1', 'reason': 'other', 'cwd': str(project)}
    _run('journal.py', 'capture-end', '--root', str(project), stdin=json.dumps(payload))
    (path,) = list((project / '.claude' / 'journal' / 'outbox').glob('*.json'))
    envelope = json.loads(path.read_text(encoding='utf-8'))
    envelope['iniciativa'] = 'con espacio/y barra'
    path.write_text(json.dumps(envelope), encoding='utf-8')
    replay = json.loads(_run('journal.py', 'replay', '--root', str(project), '--ia', 'no').stdout)
    assert replay['materializados'] == 1 and replay['dead_letter'] == 0, replay
    assert any('iniciativa' in str(a) for a in replay['avisos']), replay


def test_f4fix3_2_capture_cost_is_flat_with_zero_and_five_hundred_initiatives(tmp_path):
    def p95(count):
        project = tmp_path / f'n{count}'
        project.mkdir()
        for i in range(count):
            _ledger(project, f'2026-01-01-i{i}', 'en-progreso', mtime=NOW - i)
        (project / '.claude').mkdir()
        payload = json.dumps({'hook_event_name': 'SessionEnd', 'session_id': 's', 'reason': 'other', 'cwd': str(project)})
        jc = _load(f'f4fix3_jc{count}', 'journal-capture.py')
        samples = []
        for i in range(25):
            for stale in (project / '.claude' / 'journal' / 'outbox').glob('*.json'):
                stale.unlink()
            start = time.perf_counter()
            jc.capture_end(str(project), json.loads(payload.replace('"s"', f'"s{i}"')))
            samples.append((time.perf_counter() - start) * 1000)
        samples.sort()
        return samples[int(len(samples) * 0.95) - 1]
    few, many = p95(0), p95(500)
    assert many < few + 25, (few, many)        # no per-initiative work at the teardown
