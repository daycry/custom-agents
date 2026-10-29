"""T-05: preserve the status line while eliminating repeated Python startups."""
import json
import os
from pathlib import Path
import shlex
import sys

import pytest
from test_hooks_shell import BASH, env_de, hook, proyecto

pytestmark = pytest.mark.skipif(BASH is None, reason='Git Bash/bash unavailable')
PAYLOAD = {'model': {'display_name': 'Opus'}, 'cost': {'total_cost_usd': 0.42},
           'context_window': {'used_percentage': 8}}


def counted_env(proj, tmp_path):
    env = env_de(proj, tmp_path)
    bindir = tmp_path / 'counted-bin';bindir.mkdir()
    count = tmp_path / 'python-count'
    program = '#!/bin/bash\nprintf x >> ' + shlex.quote(str(count).replace(chr(92), '/')) + '\nexec ' + shlex.quote(sys.executable.replace(chr(92), '/')) + ' "$@"\n'
    shim = bindir / 'python3';shim.write_text(program, encoding='utf-8');shim.chmod(0o755)
    env['PATH'] = str(bindir) + os.pathsep + env['PATH']
    env['CUSTOM_AGENTS_PYTHON'] = str(shim).replace(chr(92), '/')
    return env, count


def launches(count):
    return len(count.read_bytes()) if count.exists() else 0


def test_statusline_cold_one_python_and_warm_zero(tmp_path):
    proj, _ = proyecto(tmp_path)
    env, count = counted_env(proj, tmp_path)
    rc, out, err = hook('statusline', PAYLOAD, env)
    assert (rc, err) == (0, '')
    assert out == '[Opus] $0.42 ctx 8% \u00b7 \U0001f4cb demo T-03/4 75%\n'
    assert launches(count) == 1, 'a cold render must launch Python only once'
    assert hook('statusline', PAYLOAD, env) == (0, out, '')
    assert launches(count) == 1, 'a valid cache must launch no Python'


def test_statusline_cache_invalidates_input_and_ledger_mtime(tmp_path):
    proj, ledger = proyecto(tmp_path)
    env, count = counted_env(proj, tmp_path)
    rc, original, _ = hook('statusline', PAYLOAD, env)
    assert rc == 0
    changed = {**PAYLOAD, 'cost': {'total_cost_usd': 0.004}}
    assert '<$0.01' in hook('statusline', changed, env)[1]
    assert launches(count) == 2
    ledger.write_text(ledger.read_text(encoding='utf-8').replace('estado: en-progreso', 'estado: completado', 1), encoding='utf-8')
    os.utime(ledger, (2000000000, 2000000000))
    assert hook('statusline', changed, env)[1] == '[Opus] <$0.01 ctx 8%\n'
    assert launches(count) == 3


def test_statusline_skips_windowsapps_interpreter(tmp_path):
    proj, _ = proyecto(tmp_path, activa=False)
    env, count = counted_env(proj, tmp_path)
    bad = tmp_path / 'Microsoft' / 'WindowsApps';bad.mkdir(parents=True)
    sentinel = tmp_path / 'alias-started'
    alias = bad / 'python3'
    alias.write_text('#!/bin/bash\nprintf bad > ' + shlex.quote(str(sentinel).replace(chr(92), '/')) + '\nexit 1\n', encoding='utf-8');alias.chmod(0o755)
    env['PATH'] = str(bad) + os.pathsep + env['PATH']
    env['CUSTOM_AGENTS_PYTHON'] = str(alias).replace(chr(92), '/')
    assert hook('statusline', PAYLOAD, env) == (0, '[Opus] $0.42 ctx 8%\n', '')
    assert not sentinel.exists() and launches(count) == 1


def test_statusline_no_python_keeps_model_and_exit_zero(tmp_path):
    proj, _ = proyecto(tmp_path, activa=False)
    env = env_de(proj, tmp_path, sin_python=True)
    env['CUSTOM_AGENTS_PYTHON'] = '/missing/python'
    assert hook('statusline', PAYLOAD, env) == (0, '[Opus]\n', '')


def test_statusline_cache_does_not_store_other_payload_fields(tmp_path):
    proj, _ = proyecto(tmp_path, activa=False)
    env, count = counted_env(proj, tmp_path)
    payload = {**PAYLOAD, 'private_unrelated': 'DO_NOT_CACHE_RAW_INPUT'}
    assert hook('statusline', payload, env)[0] == 0
    cache = proj / '.claude' / 'statusline-cache'
    assert cache.is_file() and 'DO_NOT_CACHE_RAW_INPUT' not in cache.read_text(encoding='utf-8')
    assert 'statusline-cache' in (proj / '.claude' / '.gitignore').read_text(encoding='utf-8')



def test_statusline_truncated_cache_is_a_miss(tmp_path):
    proj, _ = proyecto(tmp_path, activa=False)
    env, count = counted_env(proj, tmp_path)
    assert hook('statusline', PAYLOAD, env)[1] == '[Opus] $0.42 ctx 8%\n'
    cache = proj / '.claude' / 'statusline-cache'
    cache.write_bytes(cache.read_bytes().splitlines()[0] + b'\n')
    assert hook('statusline', PAYLOAD, env)[1] == '[Opus] $0.42 ctx 8%\n'
    assert launches(count) == 2


def _renderer():
    import importlib.util
    spec = importlib.util.spec_from_file_location('statusline_renderer', Path(__file__).parents[1] / 'agent-kits/shared/statusline-render.py')
    module = importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('data,expected', [
    ({'activas': []}, ''),
    ({'activas': [{'slug': 'demo', 'completadas': 1, 'total': 2, 'pct': 50}]}, '\U0001f4cb demo T-01/2 50%'),
    ({'activas': [{'slug': 'a'}, {'slug': 'b'}]}, '\U0001f4cb 2 iniciativas activas'),
    ({'activas': [{'slug': 'a'}, {'slug': 'b', 'completadas': 1, 'total': 2, 'pct': 50}], 'iniciativa_en_curso': 'b'}, '\U0001f4cb 2 activas \u00b7 \u25b6 b T-01/2 50%')])
def test_statusline_renderer_reuses_report_cli_without_child(tmp_path, data, expected):
    renderer = _renderer()
    (tmp_path / 'docs/roadmap').mkdir(parents=True)
    report = tmp_path / 'report.py';report.write_text('print(' + repr(json.dumps(data)) + ')', encoding='utf-8')
    original = list(sys.argv)
    assert renderer.roadmap_segment(tmp_path, report) == expected
    assert sys.argv == original


@pytest.mark.parametrize('program', ['raise SystemExit(1)', 'print("not JSON")', 'raise OSError("broken")'])
def test_statusline_optional_report_error_is_silent(tmp_path, program):
    renderer = _renderer()
    (tmp_path / 'docs/roadmap').mkdir(parents=True)
    report = tmp_path / 'report.py';report.write_text(program, encoding='utf-8')
    assert renderer.roadmap_segment(tmp_path, report) == ''


def test_statusline_fields_are_one_line_and_invalid_cache_key_does_not_write(tmp_path):
    renderer = _renderer()
    assert renderer.render({'model': {'display_name': 'Opus\n\x1b'}}, tmp_path, None) == 'Opus  \n\n\n\n'
    assert renderer.render([], tmp_path, None) == '\n\n\n\n'
    renderer.write_cache(tmp_path, 'invalid', 'public')
    assert not (tmp_path / '.claude').exists()



@pytest.mark.parametrize('text,expected', [('invalid JSON', '\n\n\n\n'), (json.dumps(PAYLOAD), 'Opus\n0.42\n8\n\n')])
def test_statusline_renderer_main_writes_only_public_fields(tmp_path, monkeypatch, capsys, text, expected):
    import io
    renderer = _renderer()
    monkeypatch.setattr(sys, 'stdin', io.StringIO(text))
    assert renderer.main(['--root', str(tmp_path), '--cache-key', 'a' * 64]) == 0
    assert capsys.readouterr().out == expected
    assert (tmp_path / '.claude/statusline-cache').read_text(encoding='utf-8') == 'a' * 64 + '\n' + expected


def test_statusline_cache_io_failure_keeps_output_and_removes_own_temporary(tmp_path, monkeypatch, capsys):
    import io
    renderer = _renderer()
    monkeypatch.setattr(sys, 'stdin', io.StringIO(json.dumps(PAYLOAD)))
    def fail(*args):
        raise PermissionError('do not print private errors')
    monkeypatch.setattr(renderer.os, 'replace', fail)
    assert renderer.main(['--root', str(tmp_path), '--cache-key', 'a' * 64]) == 0
    assert capsys.readouterr().out == 'Opus\n0.42\n8\n\n'
    assert not list((tmp_path / '.claude').glob('statusline-cache*'))
