"""T-23 fix18 (gap 16): el escaner de la statusline es LINEAL en el numero de tokens por debajo del tope de 8 KB.

Antes: `s="${s:${#BASH_REMATCH[0]}}"` copia el resto de la entrada en CADA token; una entrada de 7,9 KB con 2.600 tokens (`nota: [0]*2600`) costaba 1,6-1,9 s con la cache caliente
(96/271/1.594 ms con 2/4/8 KB). Ahora el escaner cuenta sus pasos (`STATUSLINE_SCAN_STEPS`): pasado el tope «no puede decidir» y pinta Python con la entrada en la clave. El test cuenta PASOS
(iteraciones del bucle, trazadas con `bash -x`), no segundos: por razon de tamano 2/4/8 KB, los pasos no pasan del tope.
"""
import json
import re
import subprocess

import pytest
from test_hooks_shell import BASH, STATUSLINE, env_de, hook, proyecto

pytestmark = pytest.mark.skipif(BASH is None, reason='Git Bash/bash unavailable')
BASE = {'model': {'display_name': 'Opus'}, 'cost': {'total_cost_usd': 0.42}, 'context_window': {'used_percentage': 8}}


def tope():
    m = re.search(r'^STATUSLINE_SCAN_STEPS=(\d+)', open(STATUSLINE, encoding='utf-8').read(), re.M)
    assert m, 'el escaner no declara STATUSLINE_SCAN_STEPS'
    return int(m.group(1))


def pasos(payload, tmp_path, nombre):
    (tmp_path / nombre).mkdir()
    proj, _ = proyecto(tmp_path / nombre)
    env = env_de(proj, tmp_path / nombre)
    r = subprocess.run([BASH, '-x', STATUSLINE], input=json.dumps(payload), capture_output=True, text=True, encoding='utf-8', errors='replace',
                       env=env, cwd=env['CLAUDE_PROJECT_DIR'], timeout=120)
    assert r.returncode == 0 and r.stdout.startswith('[Opus] $0.42 ctx 8%'), (r.returncode, r.stdout, r.stderr[-300:])
    return sum(1 for linea in r.stderr.splitlines() if re.match(r'^\++ chunk=', linea))


@pytest.mark.parametrize('kb', [2, 4, 8])
def test_los_pasos_del_escaner_no_pasan_del_tope_por_razon_de_tamano(tmp_path, kb):
    n = (kb * 1024 - 300) // 3          # (ajuste tras el RED, k4) el caso de 8 KB tiene que caber en el tope de 8192 B para llegar al escaner
    entrada = dict(BASE, nota=[0] * n)
    assert len(json.dumps(entrada)) <= 8192
    assert pasos(entrada, tmp_path, 'k%d' % kb) <= 3 * tope(), 'con %d KB (%d tokens) el escaner pasa de su tope de pasos' % (kb, n)


def test_la_entrada_real_cabe_holgada_en_el_tope(tmp_path):
    real = dict(BASE, context_window={'used_percentage': 8, 'total_input_tokens': 15234, 'context_window_size': 200000,
        'current_usage': {'input_tokens': 8, 'output_tokens': 4, 'cache_creation_input_tokens': 5, 'cache_read_input_tokens': 14000}},
        cost={'total_cost_usd': 0.42, 'total_duration_ms': 45000, 'total_lines_added': 156, 'total_lines_removed': 23},
        workspace={'current_dir': 'C:/x', 'project_dir': 'C:/x'}, rate_limits={'five_hour': {'used_percentage': 3.5, 'resets_at': 1738425600}})
    assert 0 < pasos(real, tmp_path, 'real') <= tope() // 2, 'el tope de pasos no puede dejar fuera una entrada normal'
