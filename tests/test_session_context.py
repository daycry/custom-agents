"""Compare the native compositor with the retained shell on disposable consumers."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace

import pytest

import test_hooks_shell as legacy

ROOT = Path(__file__).resolve().parents[1]
NATIVE = ROOT / 'hooks/session-context.py'


def test_native_compositor_exists():
    assert NATIVE.is_file(), 'single-process session context compositor is absent'


def native_module():
    spec = importlib.util.spec_from_file_location('test_native_session_context', NATIVE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_failed_memory_service_stdout_is_not_a_success(tmp_path):
    module = native_module()
    def progress(_args):
        print(json.dumps({'activas': [{'slug': 'demo', 'path': 'missing/tasks.md'}]}))
        return 0
    def knowledge(_args):
        print(json.dumps({'aciertos': [{'id': 'GOT-001', 'linea': 'FAILED QUERY DATA', 'puntuacion': 1}]}))
        return 1
    assert module._memory(SimpleNamespace(main=knowledge), SimpleNamespace(main=progress), str(tmp_path)) == ''


def test_composition_restores_process_state_and_never_spawns(tmp_path, monkeypatch):
    module = native_module()
    config = tmp_path / '.claude/dev.json'
    config.parent.mkdir()
    config.write_text('{"sesion":{"indice":false}}', encoding='utf-8')
    def forbidden(*_args, **_kwargs):
        pytest.fail('compositor spawned another process')
    monkeypatch.setattr(subprocess, 'Popen', forbidden)
    monkeypatch.setenv('CLAUDE_PROJECT_DIR', 'outer-project')
    before = dict(os.environ), sys.argv[:], sys.stdout, sys.stderr
    for _ in range(2):
        assert module.compose({'session_id': 'same'}, root=str(tmp_path)) == ''
    assert (dict(os.environ), sys.argv, sys.stdout, sys.stderr) == before


def test_invalid_runtime_does_not_block_or_emit_context(tmp_path):
    result = subprocess.run([sys.executable, str(NATIVE), '--runtime=unknown'], input=b'{}', capture_output=True)
    assert (result.returncode, result.stdout, result.stderr) == (0, b'', b'')


def test_partial_installation_omits_unavailable_services(tmp_path, monkeypatch):
    module = native_module()
    monkeypatch.setattr(module, '_load', lambda *_args: None)
    assert module.compose({}, root=str(tmp_path)) == ''


def test_progress_default_retains_legacy_marker_timeout(tmp_path, monkeypatch):
    module = native_module()._load('progress_contract', 'progress-report.py')
    calls = []
    def run(args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(stdout='{"marcadores":[{"artefacto":"open"}]}')
    monkeypatch.setattr(subprocess, 'run', run)
    assert module.marcadores_huerfanos(str(tmp_path)) == ['open']
    assert calls[0][1]['timeout'] == 10


@pytest.mark.parametrize('runtime', ['claude', 'codex', 'opencode'])
def test_in_process_composition_keeps_memory_history_and_reentry(tmp_path, monkeypatch, runtime):
    module = native_module()
    project, _ = legacy.proyecto(tmp_path)
    legacy._knowledge(project)
    legacy._owned_history(project, 'selected.md', 'demo', 'Selected history')
    legacy._owned_history(project, 'foreign.md', 'other', 'Foreign history')
    (project / '.claude/usage-state.json').write_text(json.dumps({
        'demo/open-marker': {'inicio': '2026-01-01T00:00:00Z'},
        'closed-marker': {'inicio': '2026-01-01T00:00:00Z', 'ultimoCierre': 'closed'},
    }), encoding='utf-8')
    monkeypatch.setenv('CLAUDE_PLUGIN_ROOT', str(ROOT))
    def forbidden(*_args, **_kwargs):
        pytest.fail('local context composition spawned another process')
    monkeypatch.setattr(subprocess, 'Popen', forbidden)
    payload = {'source': 'startup', 'session_id': 'local-composition'}
    first = module.compose(payload, runtime=runtime, root=str(project))
    assert module.compose(payload, runtime=runtime, root=str(project)) == first
    context = json.loads(first)['hookSpecificOutput']['additionalContext']
    assert 'Memoria técnica' in context and 'ADR-001' in context
    assert 'Selected history' in context and 'Foreign history' not in context
    assert 'usage-meter: marcadores abiertos → demo/open-marker' in context
    assert 'closed-marker' not in context
    assert context.index('Plugin custom-agents') < context.index('Ledger canónico') < context.index('Selected history') < context.index('Memoria técnica')


@pytest.mark.skipif(legacy.BASH is None, reason='capture fixture needs Bash')
def test_in_process_due_replay_never_spawns_another_python(tmp_path, monkeypatch):
    module = native_module()
    project, _ = legacy.proyecto(tmp_path)
    (project / '.claude/dev.json').write_text('{"sesion":{"journal":{"replay":{"budgetMs":5000}}}}', encoding='utf-8')
    legacy._log_prompts(project, 'closed-native')
    env = legacy.env_de(project, tmp_path)
    assert legacy.hook('session-journal.sh', legacy.session_end(project, sid='closed-native'), env)[0] == 0
    original = subprocess.Popen
    def observe(command, *args, **kwargs):
        executable = Path(command[0]).name.lower()
        assert not executable.startswith(('python', 'py.exe')), 'replay spawned another Python'
        return original(command, *args, **kwargs)
    monkeypatch.setattr(subprocess, 'Popen', observe)
    monkeypatch.setenv('CLAUDE_PLUGIN_ROOT', str(ROOT))
    output = module.compose({'source': 'startup', 'session_id': 'current-native'}, root=str(project))
    assert 'closed-native' in output
    assert legacy.outbox_pendientes(project) == []
    assert len(legacy.entradas_journal(project)) == 1


@pytest.mark.skipif(legacy.BASH is None, reason='shell oracle needs Bash')
@pytest.mark.parametrize('runtime', ['claude', 'codex', 'opencode'])
@pytest.mark.parametrize('case', ['startup', 'resume', 'compact', 'off', 'history', 'ambiguous', 'invalid-config', 'memory', 'replay', 'meter'])
def test_native_output_matches_shell_bytes(tmp_path, runtime, case):
    assert NATIVE.is_file(), 'single-process session context compositor is absent'
    project, _ = legacy.proyecto(tmp_path, activa=case != 'off')
    if case == 'off':
        (project / '.claude/dev.json').write_text('{"sesion":{"indice":false}}', encoding='utf-8')
    if case == 'invalid-config':
        (project / '.claude/dev.json').write_text('{"sesion":{"journal":{"replay":{"max":true,"budgetMs":600000}}}}', encoding='utf-8')
    if case == 'memory':
        legacy._knowledge(project)
    if case == 'meter':
        (project / '.claude/usage-state.json').write_text(json.dumps({
            'demo/open-marker': {'inicio': '2026-01-01T00:00:00Z'},
            'closed-marker': {'inicio': '2026-01-01T00:00:00Z', 'ultimoCierre': 'closed'},
        }), encoding='utf-8')
    if case == 'replay':
        # A generous declared budget isolates semantic recovery from scheduler
        # timing; default-budget performance is measured separately.
        (project / '.claude/dev.json').write_text('{"sesion":{"journal":{"replay":{"budgetMs":5000}}}}', encoding='utf-8')
    if case in ('history', 'ambiguous'):
        legacy._owned_history(project, 'selected.md', 'demo', 'Selected history')
        legacy._owned_history(project, 'foreign.md', 'other', 'Foreign history')
    if case == 'ambiguous':
        ledger = project / 'docs/roadmap/2026-01-01-demo/tasks.md'
        other = ledger.parent.parent / '2026-01-02-other/tasks.md'
        other.parent.mkdir()
        other.write_bytes(ledger.read_bytes())
    native_project = tmp_path / 'native-consumer'
    shutil.copytree(project, native_project)
    source = case if case in ('startup', 'resume', 'compact') else 'startup'
    payload = json.dumps({'hook_event_name': 'SessionStart', 'source': source,
                          'session_id': 'context-equivalence'}, ensure_ascii=False).encode('utf-8')
    old_env = legacy.env_de(project, tmp_path)
    new_env = legacy.env_de(native_project, tmp_path)
    if case == 'replay':
        for consumer, env in [(project, old_env), (native_project, new_env)]:
            legacy._log_prompts(consumer, 'closed-context')
            assert legacy.hook('session-journal.sh', legacy.session_end(consumer, sid='closed-context'), env)[0] == 0
            assert len(legacy.outbox_pendientes(consumer)) == 1
    before = subprocess.run([legacy.BASH, str(ROOT / 'hooks/session-context.sh'), '--runtime=' + runtime],
                            input=payload, env=old_env, cwd=project, capture_output=True, timeout=90)
    after = subprocess.run([sys.executable, '-I', '-S', str(NATIVE), '--runtime=' + runtime],
                           input=payload, env=new_env, cwd=native_project, capture_output=True, timeout=90)
    assert before.returncode == after.returncode == 0
    assert before.stderr == after.stderr == b''
    assert before.stdout == after.stdout
    # These fixtures have no due envelopes: both implementations retain the same
    # owned cache and journal artefact names, without borrowing another consumer.
    def artefacts(root):
        return {p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file()}
    if case == 'replay':
        for consumer in (project, native_project):
            assert legacy.outbox_pendientes(consumer) == []
            entries = legacy.entradas_journal(consumer)
            assert len(entries) == 1
            text = (consumer / 'docs/knowledge/journal' / entries[0]).read_text(encoding='utf-8')
            assert 'closed-context' in text and 'decidimos recuperar' in text
        assert b'closed-context' in before.stdout
    else:
        assert artefacts(project) == artefacts(native_project)
    if case == 'memory':
        assert 'Memoria técnica'.encode('utf-8') in before.stdout
