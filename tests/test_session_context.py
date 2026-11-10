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
        # f4fix1 gap 17: an empty block still carries the kit line (and nothing else).
        out = module.compose({'session_id': 'same'}, root=str(tmp_path))
        assert json.loads(out)['hookSpecificOutput']['additionalContext'].startswith('Kit activo: SHAREDKIT=')
        assert chr(10) not in json.loads(out)['hookSpecificOutput']['additionalContext']
    assert (dict(os.environ), sys.argv, sys.stdout, sys.stderr) == before


def test_invalid_runtime_does_not_block_or_emit_context(tmp_path):
    result = subprocess.run([sys.executable, str(NATIVE), '--runtime=unknown'], input=b'{}', capture_output=True)
    assert (result.returncode, result.stdout, result.stderr) == (0, b'', b'')


EMPTY_BLOCK = b'{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ""}}' + bytes([10])


def test_partial_installation_omits_unavailable_services(tmp_path, monkeypatch):
    module = native_module()
    monkeypatch.setattr(module, '_load', lambda *_args: None)
    # f4fix1 gap 17: nothing else to say, but the kit line still goes out.
    context = json.loads(module.compose({}, root=str(tmp_path)))['hookSpecificOutput']['additionalContext']
    assert context.startswith('Kit activo: SHAREDKIT=') and chr(10) not in context


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
    # The retired shell oracle knows nothing of the kit line of H-45 (T-19), which the native
    # compositor puts first; every other byte must still match.
    import re
    kit_line = rb"Kit activo: SHAREDKIT='.*?' \(\xc3\xbasalo [^\n]*?\.(?:\\n\\n|(?=\x22}}))"   # single-quoted since f4fix1 gap 1
    native_stdout, removed = re.subn(kit_line, b'', after.stdout, count=1)
    assert removed == (1 if after.stdout.strip() else 0)
    if native_stdout.strip() == EMPTY_BLOCK.strip():      # f4fix1 gap 17: the kit line alone; the oracle printed nothing
        native_stdout = b''
    assert before.stdout == native_stdout
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


# ------------------------------------------------- H-14, H-27, H-48 (auditoría 2026-11-09)

def test_h48_memoria_consulta_primero_la_iniciativa_en_curso(tmp_path):
    module = native_module()
    consultas = []
    def progress(_args):
        print(json.dumps({'activas': [
            {'slug': 'cerrada', 'path': 'x/tasks.md', 'pct': 100},
            {'slug': 'vieja', 'path': 'y/tasks.md', 'pct': 10},
            {'slug': 'actual', 'path': 'z/tasks.md', 'pct': 30}],
            'iniciativa_en_curso': 'actual'}))
        return 0
    def knowledge(args):
        consultas.append(args[args.index('--iniciativa') + 1])
        print(json.dumps({'aciertos': [{'id': 'ADR-001', 'linea': 'acierto', 'puntuacion': 1}]}))
        return 0
    text = module._memory(SimpleNamespace(main=knowledge), SimpleNamespace(main=progress), str(tmp_path))
    assert consultas == ['actual', 'vieja']
    assert 'fuera: cerrada' in text


def test_h48_pie_de_memoria_sin_ruta_absoluta(tmp_path):
    module = native_module()
    def progress(_args):
        print(json.dumps({'activas': [{'slug': 'demo', 'path': 'missing/tasks.md'}]}))
        return 0
    def knowledge(_args):
        print(json.dumps({'aciertos': [{'id': f'ADR-{n:03d}', 'linea': 'x' * 150, 'puntuacion': 1}
                                       for n in range(20)]}))
        return 0
    text = module._memory(SimpleNamespace(main=knowledge), SimpleNamespace(main=progress), str(tmp_path))
    assert 'Detalle solo por ID (kit compartido, $SHAREDKIT): knowledge-find.py --show <ID>' in text
    assert 'más: knowledge-find.py --contexto' in text
    assert str(module.SHARED) not in text and str(module.SHARED).replace(chr(92), '/') not in text


def test_h27_session_start_de_claude_reinyecta_tras_clear():
    hooks = json.loads((ROOT / 'hooks/hooks.json').read_text(encoding='utf-8'))
    matchers = [entry['matcher'] for entry in hooks['hooks']['SessionStart']]
    assert any('clear' in matcher.split('|') for matcher in matchers), matchers


def test_h14_compose_con_ledgers_grandes_y_dos_activas_reinyecta_el_journal(tmp_path, monkeypatch):
    module = native_module()
    project, led = legacy.proyecto(tmp_path)
    (project / '.claude/dev.json').write_text('{"sesion":{"indice":false,"memoria":false}}', encoding='utf-8')
    for index in range(5):
        big = project / f'docs/roadmap/2025-01-0{index + 1}-big{index}/tasks.md'
        big.parent.mkdir(parents=True)
        big.write_text(led.read_text(encoding='utf-8').replace('estado: en-progreso', 'estado: completado', 1)
                       + ('relleno ' * 60 + '\n') * 500, encoding='utf-8')
    other = project / 'docs/roadmap/2026-01-02-other/tasks.md'
    other.parent.mkdir(parents=True)
    other.write_bytes(led.read_bytes())
    (project / '.claude/usage-state.json').write_text(
        json.dumps({'demo/T-01': {'inicio': '2026-01-03T00:00:00Z'}}), encoding='utf-8')
    legacy._owned_history(project, 'selected.md', 'demo', 'Selected history')
    legacy._owned_history(project, 'other.md', 'other', 'History of the other initiative')
    monkeypatch.setenv('CLAUDE_PLUGIN_ROOT', str(ROOT))
    output = module.compose({'source': 'startup', 'session_id': 'h14'}, root=str(project))
    context = json.loads(output)['hookSpecificOutput']['additionalContext']
    assert 'Selected history' in context and 'History of the other initiative' not in context
    assert 'Journal: incomplete' not in context and 'Journal: ambiguous' not in context
    assert 'Revisiones: selección de iniciativa' not in context



# ------------------------------------------------- revisión intento 1 (fase 2): B4, memoria, A5

def test_fix1_b4_memoria_agrupa_al_final_solo_las_completas_de_verdad(tmp_path):
    module = native_module()
    consultas = []
    def progress(_args):
        print(json.dumps({'activas': [
            {'slug': 'cerrada', 'path': 'z/tasks.md', 'pct': 100, 'completadas': 3, 'total': 3},
            {'slug': 'otra', 'path': 'y/tasks.md', 'pct': 10, 'completadas': 1, 'total': 10},
            {'slug': 'casi', 'path': 'x/tasks.md', 'pct': 100, 'completadas': 199, 'total': 200}],
            'iniciativa_en_curso': 'otra'}))
        return 0
    def knowledge(args):
        consultas.append(args[args.index('--iniciativa') + 1])
        print(json.dumps({'aciertos': [{'id': 'ADR-001', 'linea': 'acierto', 'puntuacion': 1}]}))
        return 0
    module._memory(SimpleNamespace(main=knowledge), SimpleNamespace(main=progress), str(tmp_path))
    assert consultas == ['otra', 'casi'], '199/200 no está al 100 %'


def test_fix1_memoria_no_desaparece_si_la_en_curso_no_tiene_aciertos(tmp_path):
    module = native_module()
    def progress(_args):
        print(json.dumps({'activas': [
            {'slug': 'actual', 'path': 'x/tasks.md', 'completadas': 1, 'total': 5},
            {'slug': 'segunda', 'path': 'y/tasks.md', 'completadas': 1, 'total': 5},
            {'slug': 'tercera', 'path': 'z/tasks.md', 'completadas': 1, 'total': 5}],
            'iniciativa_en_curso': 'actual'}))
        return 0
    def knowledge(args):
        slug = args[args.index('--iniciativa') + 1]
        print(json.dumps({'aciertos': [{'id': 'ADR-009', 'linea': 'ADR-009 · acierto', 'puntuacion': 1}]
                          if slug == 'tercera' else []}))
        return 0
    text = module._memory(SimpleNamespace(main=knowledge), SimpleNamespace(main=progress), str(tmp_path))
    assert 'ADR-009' in text


def test_fix1_a5_ningun_documento_cita_el_matcher_sin_clear():
    viejo = 'startup|resume|compact'
    for rel in ('docs/CONVENTIONS.md', 'docs/en/CONVENTIONS.md', 'agent-kits/shared/README.md',
                'agent-kits/shared/skill-index.py', 'skills/plugin-dev/references/claude-code-contracts.md',
                'docs/observability.md', 'docs/en/observability.md', 'hooks/session-context.sh'):
        assert viejo not in (ROOT / rel).read_text(encoding='utf-8'), rel


# ------------------------------------------------- H-28 (auditoría 2026-11-09, T-13): una pasada

_H28_CONTADOR = r'''
import collections, importlib.util, json, os, sys
native, project = sys.argv[1], sys.argv[2]
opens = collections.Counter()
def hook(event, args):
    if event == 'open' and isinstance(args[0], str):
        name = os.path.basename(os.path.dirname(args[0])) + '/' + os.path.basename(args[0])
        if name.endswith(('/tasks.md', '/usage-state.json')):
            opens[name] += 1
sys.addaudithook(hook)
spec = importlib.util.spec_from_file_location('sc_h28', native)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
out = module.compose({'source': 'startup', 'session_id': 'h28'}, root=project)
print(json.dumps({'opens': opens, 'out': out}))
'''


def test_h28_compose_lee_cada_ledger_y_usage_state_una_sola_vez(tmp_path):
    """H-28: el arranque abre cada `tasks.md` y `usage-state.json` UNA vez (antes: el bloque de
    sesión, el historial y la memoria releían los ledgers y el estado del meter se cargaba dos
    veces, una por `_leer_usage_state` y otra por el `status` del meter)."""
    project, led = legacy.proyecto(tmp_path)
    legacy._knowledge(project)
    legacy._owned_history(project, 'selected.md', 'demo', 'Selected history')
    # la activa supera el prefijo de 16 KiB (antes: 16 KiB + 256 KiB = dos aperturas) y hay dos
    # inactivas, una grande y otra pequeña
    led.write_text(led.read_text(encoding='utf-8') + ('relleno ' * 60 + '\n') * 80, encoding='utf-8')
    for index, repeat in enumerate((400, 0)):
        other = project / f'docs/roadmap/2025-01-0{index + 1}-cerrada{index}/tasks.md'
        other.parent.mkdir(parents=True)
        other.write_text(led.read_text(encoding='utf-8').replace('estado: en-progreso', 'estado: completado', 1)
                         + ('relleno ' * 60 + '\n') * repeat, encoding='utf-8')
    (project / '.claude/usage-state.json').write_text(json.dumps({
        'demo/T-01': {'inicio': '2026-01-03T00:00:00Z'},
        'demo/T-00': {'inicio': '2026-01-01T00:00:00Z', 'ultimoCierre': '2026-01-02T00:00:00Z'},
    }), encoding='utf-8')
    env = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(ROOT))
    result = subprocess.run([sys.executable, '-c', _H28_CONTADOR, str(NATIVE), str(project)],
                            capture_output=True, text=True, encoding='utf-8', env=env, timeout=120)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout.strip().splitlines()[-1])
    context = json.loads(data['out'])['hookSpecificOutput']['additionalContext']
    assert 'Ledger canónico' in context and 'Selected history' in context and 'Memoria técnica' in context
    assert 'usage-meter: marcadores abiertos → demo/T-01' in context
    opens = data['opens']
    assert opens.get('.claude/usage-state.json') == 1, opens
    ledgers = {name: count for name, count in opens.items() if name.endswith('/tasks.md')}
    assert len(ledgers) == 3 and max(ledgers.values()) == 1, ledgers


def test_h28_compose_lee_el_corpus_de_la_memoria_una_sola_vez(tmp_path):
    """H-28: con dos iniciativas activas la memoria consulta dos veces knowledge-find; el corpus de
    `docs/knowledge/` se lee y se parsea una vez por arranque, no una vez por consulta."""
    project, led = legacy.proyecto(tmp_path)
    legacy._knowledge(project)
    other = project / 'docs/roadmap/2026-01-02-other/tasks.md'
    other.parent.mkdir(parents=True)
    other.write_bytes(led.read_bytes())
    script = _H28_CONTADOR.replace("name.endswith(('/tasks.md', '/usage-state.json'))",
                                   "name.endswith('/ADR-001-lentes-en-paralelo.md')")
    env = dict(os.environ, CLAUDE_PLUGIN_ROOT=str(ROOT))
    result = subprocess.run([sys.executable, '-c', script, str(NATIVE), str(project)],
                            capture_output=True, text=True, encoding='utf-8', env=env, timeout=120)
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout.strip().splitlines()[-1])
    context = json.loads(data['out'])['hookSpecificOutput']['additionalContext']
    assert 'Memoria técnica' in context and 'consultadas' not in context
    assert data['opens'] == {'adr/ADR-001-lentes-en-paralelo.md': 1}, data['opens']
