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
    # H-39 (T-16): cost and context change every turn; Bash paints them and the roadmap stays cached
    assert launches(count) == 1, 'a new cost must not launch Python'
    ledger.write_text(ledger.read_text(encoding='utf-8').replace('estado: en-progreso', 'estado: completado', 1), encoding='utf-8')
    os.utime(ledger, (2000000000, 2000000000))
    assert hook('statusline', changed, env)[1] == '[Opus] <$0.01 ctx 8%\n'
    assert launches(count) == 2


@pytest.mark.parametrize('payload,rapido', [
    ({'model': {'display_name': 'Opus 4.1'}, 'cost': {'total_cost_usd': 1.239}, 'context_window': {'used_percentage': 41.5}}, True),
    ({'cost': {'total_cost_usd': 0.0}, 'context_window': {'used_percentage': 100}}, True),
    ({'cost': {'total_cost_usd': 0.4 + 0.03}, 'context_window': {'used_percentage': 12.300000000000001}}, True),
    ({}, True),
    ({'model': {'display_name': 'Ópus 🐛'}, 'cost': {'total_cost_usd': 0.5}}, False),
    ({'model': {'display_name': 'Quote " in name'}, 'cost': {'total_cost_usd': 2}}, False),
    ({'cost': {'total_cost_usd': 0.00001}, 'context_window': {'used_percentage': 0.00002}}, False),
    ({'cost': {'total_cost_usd': 1e-7}, 'model': {'display_name': None}}, False),
    ({'model': {'display_name': 'A', 'other': {'display_name': 'B'}}}, True),   # fix2: la anidada no cuenta
    ({'cost': {'total_cost_usd': '0.42'}}, False),
])
def test_h39_bash_pinta_lo_mismo_que_python_y_reutiliza_la_cache(tmp_path, payload, rapido):
    """H-39: la clave de la caché incluía el input entero y casi nunca acertaba. Ahora cubre solo el
    roadmap y Bash pinta modelo, coste y contexto; cuando un campo no tiene la forma simple que Python
    imprimiría igual, se usa Python como antes. La salida es la misma por los dos caminos."""
    proj, _ = proyecto(tmp_path)
    env, count = counted_env(proj, tmp_path)
    fria = hook('statusline', payload, env)          # sin caché: Python
    assert fria[0] == 0 and fria[2] == '' and launches(count) == 1
    caliente = hook('statusline', payload, env)      # con caché: Bash si el input es simple
    assert caliente == fria
    assert launches(count) == 1   # identical input hits the cache by either path (fix1, D1)
    otro = hook('statusline', {**payload, 'session_id': 'otro-turno'}, env)
    assert otro == fria and launches(count) == (1 if rapido else 2)


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


# ------------------------------------------------- revisión intento 1 (fase 3): D1 + B2 (T-16)

@pytest.mark.parametrize('payload,rapido', [
    ({'model': {'display_name': 'Opus'}, 'cost': {'total_cost_usd': 0.42},
      'context_window': {'used_percentage': 8},
      'rate_limits': {'five_hour': {'used_percentage': 77}, 'seven_day': {'used_percentage': 12}}}, True),
    ({'model': {'display_name': 'Opus'}, 'rate_limits': {'five_hour': {'used_percentage': 77}}}, True),
    ({'model': {'display_name': 'Opus'}, 'context_window': {'used_percentage': None}}, True),
    ({'model': {'display_name': 'Opus'}, 'agent': {'model': {'display_name': 'Otro'}}}, True),   # fix2: solo el primer nivel
    ({'context_window': {'used_percentage': 8, 'current_usage': {'input_tokens': 3}}}, True),   # fix2: grupos anidados
])
def test_fix1_d1_b2_cada_campo_se_lee_en_su_grupo_y_la_entrada_identica_acierta(tmp_path, payload, rapido):
    """D1: una clave repetida (`rate_limits.*.used_percentage`) o `null` lanzaba Python en cada
    refresco, también con la entrada idéntica. B2: la clave en otro objeto pintaba `ctx 77%`. Bash lee
    cada campo dentro de su grupo y, si no puede, Python con la entrada en la clave (como en b2621b0)."""
    proj, _ = proyecto(tmp_path)
    env, count = counted_env(proj, tmp_path)
    renderer = _renderer()
    campos = renderer.render(payload, proj, None).split('\n')[:3]
    fria = hook('statusline', payload, env)
    assert fria[0] == 0 and fria[2] == '' and launches(count) == 1
    assert ('ctx 77%' in fria[1]) is False
    if campos[0]:
        assert fria[1].startswith('[' + campos[0] + ']')
    assert hook('statusline', payload, env) == fria and launches(count) == 1, 'identical input must hit the cache'
    otro = hook('statusline', {**payload, 'session_id': 'otro-turno'}, env)
    assert otro == fria and launches(count) == (1 if rapido else 2)


# ------------------------------------------------- revisión intento 2 (fase 3): D y B3 (T-16)

def _payload_real(coste, current_usage=True):
    """La forma real de Claude Code: `context_window.current_usage` es un objeto anidado (o null)."""
    return {'session_id': 's1', 'transcript_path': '/tmp/s1.jsonl', 'cwd': '/tmp/proyecto',
            'model': {'id': 'claude-opus-4-1', 'display_name': 'Opus'},
            'workspace': {'current_dir': '/tmp/proyecto', 'project_dir': '/tmp/proyecto'},
            'version': '2.0.0', 'output_style': {'name': 'default'},
            'cost': {'total_cost_usd': coste, 'total_duration_ms': 45000, 'total_api_duration_ms': 2300,
                     'total_lines_added': 156, 'total_lines_removed': 23},
            'context_window': {'total_input_tokens': 1000, 'total_output_tokens': 200, 'context_window_size': 200000,
                               'current_usage': ({'input_tokens': 8500, 'output_tokens': 1200,
                                                  'cache_creation_input_tokens': 5000, 'cache_read_input_tokens': 2000}
                                                 if current_usage else None),
                               'used_percentage': 8, 'remaining_percentage': 92},
            'exceeds_200k_tokens': False}


@pytest.mark.parametrize('current_usage', [True, False])
def test_fix2_d_el_payload_real_con_current_usage_usa_el_atajo(tmp_path, current_usage):
    """D (intento 2): la regex de grupo plano exigía un grupo plano y el payload real trae
    `context_window.current_usage` anidado: tras la primera respuesta, 7 refrescos con el coste
    cambiando lanzaban 7 Pythons. El escáner admite objetos anidados: 1 Python."""
    proj, _ = proyecto(tmp_path)
    env, count = counted_env(proj, tmp_path)
    renderer = _renderer()
    for n in range(7):
        payload = _payload_real(0.4 + n / 100, current_usage)
        model, cost, ctx = renderer.render(payload, proj, None).split('\n')[:3]
        salida = hook('statusline', payload, env)
        assert salida[0] == 0 and salida[1].startswith(f'[{model}] ') and f'ctx {ctx}%' in salida[1]
    assert launches(count) == 1


@pytest.mark.parametrize('crudo', [
    '{"model":{"id":"a}","display_name":"X"}}',
    '{"cwd":"C:/a}b","agent":{"model":{"display_name":"Otro"}}}',
    '{"cwd":"C:/a{b","model":{"display_name":"Y"},"cost":{"note":"}{","total_cost_usd":0.5}}',
    '{"model":{"display_name":"Z","x":"\\"}"},"context_window":{"used_percentage":9}}',
])
def test_fix2_b3_llaves_dentro_de_cadenas_dan_lo_mismo_que_python(tmp_path, crudo):
    """B3 (intento 2): una llave dentro de una cadena JSON descuadraba el recuento y Bash pintaba algo
    distinto de Python. El escáner salta las cadenas, con sus escapes."""
    proj, _ = proyecto(tmp_path)
    env, count = counted_env(proj, tmp_path)
    fria = hook('statusline', crudo, env)
    (proj / '.claude' / 'statusline-cache').unlink()
    python = hook('statusline', crudo, env)          # sin caché: Python pinta todo
    caliente = hook('statusline', crudo, env)        # con caché: Bash si decide
    assert fria == python == caliente


# ------------------------------------------------- revisión intento 3 (fase 3): T-16

def test_fix3_2_una_entrada_enorme_no_se_escanea_y_acierta_en_cache(tmp_path):
    """2: el escáner era cuadrático (25 KB de escapes → 13,5 s por refresco, también con la caché
    caliente). Por encima de 8 KB no se escanea: Python pinta, con la entrada en la clave."""
    import time
    proj, _ = proyecto(tmp_path)
    env, count = counted_env(proj, tmp_path)
    payload = {'model': {'display_name': 'Opus'}, 'cost': {'total_cost_usd': 0.42},
               'context_window': {'used_percentage': 8}, 'nota': '\\"' * 12000}
    fria = hook('statusline', payload, env)
    assert fria[0] == 0 and fria[1].startswith('[Opus] $0.42 ctx 8%') and launches(count) == 1
    inicio = time.monotonic()
    caliente = hook('statusline', payload, env)
    assert caliente == fria and launches(count) == 1
    assert time.monotonic() - inicio < 1, time.monotonic() - inicio


@pytest.mark.parametrize('crudo,esperado', [
    ('{"context_window":{"used_percentage":0.50000000000000001}}', 'ctx 0%'),
    ('{"context_window":{"used_percentage":1.49999999999999999}}', 'ctx 2%'),
    ('{"cost":{"total_cost_usd":0.12500000000000001}}', '$0.12'),
])
def test_fix3_3_un_numero_que_no_es_el_texto_mas_corto_redondea_como_python(tmp_path, crudo, esperado):
    """3: `NUMBER` admitía 27 dígitos significativos; `0.50000000000000001` daba `ctx 1%` en Bash y
    `ctx 0%` en Python. Cerca del redondeo, con más de 15 dígitos, pinta Python."""
    proj, _ = proyecto(tmp_path)
    env, count = counted_env(proj, tmp_path)
    fria = hook('statusline', crudo, env)
    caliente = hook('statusline', crudo, env)
    assert esperado in fria[1] and caliente == fria, (fria, caliente)


@pytest.mark.parametrize('crudo', [
    '{"model":{"display_name":"X",},"context_window":{"used_percentage":8}}',
    '{"model":{"display_name":"X"}} basura',
    r'{"model":{"display_name":"X","n":"\x41"}}',
])
def test_fix3_4_json_invalido_no_se_pinta_desde_bash(tmp_path, crudo):
    """4: con JSON inválido Python pinta vacío y Bash pintaba campos con la caché caliente. El escáner
    detecta la coma final, el texto tras el objeto y los escapes inválidos y deja que pinte Python."""
    proj, _ = proyecto(tmp_path)
    env, count = counted_env(proj, tmp_path)
    fria = hook('statusline', crudo, env)
    caliente = hook('statusline', crudo, env)
    assert fria == caliente and '[X]' not in caliente[1]


def test_fix3_8_la_deuda_de_la_ruta_corta_8_3_queda_en_t21():
    """8: la caché que `statusline-render.py` no escribe con una raíz en ruta corta 8.3 se vigila como
    las demás deudas de T-21, con el fichero en su campo `Archivos`."""
    ledger = (Path(__file__).parents[1] / 'docs/roadmap/2026-11-09-plugin-audit-remediation/tasks.md').read_text(encoding='utf-8')
    t21 = ledger[ledger.index('### T-21'):]
    t21 = t21[:t21.index('## Revisión de dos lentes')]
    archivos = next(l for l in t21.splitlines() if l.startswith('- **Archivos**:'))
    assert 'agent-kits/shared/statusline-render.py' in archivos
    assert 'ruta corta 8.3' in t21
