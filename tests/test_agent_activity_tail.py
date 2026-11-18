"""plugin-audit-2, T-23 fix18 (gap 4, D2): los eventos de herramienta se anaden a una COLA (`events.tail`) con `O_APPEND` + `fsync` bajo el cerrojo, sin releer ni validar el anillo.

Causa medida (intento 18): abrir para LEER un fichero recien reemplazado cuesta 25-55 ms (escaneo sincrono de la maquina, igual con 1 KB que con 200 KB) y en una rafaga cada escritor
lee lo que publico el anterior. Con la cola, el camino caliente no lee el anillo: el pliegue al anillo lo hace el escritor que supera `TAIL_FOLD_BYTES` (o el ciclo de vida) y es a prueba de caidas
(el anillo se publica por CAS ANTES de truncar la cola; las lineas ya plegadas se reconocen por su `id` en `plegado` y no se duplican).
"""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

SHARED = Path(__file__).resolve().parents[1] / 'agent-kits' / 'shared'


@pytest.fixture(autouse=True)
def _plazos_inyectados(monkeypatch):
    monkeypatch.setenv('CUSTOM_AGENTS_ACTIVITY_DEADLINE_SCALE', '20')


def load():
    spec = importlib.util.spec_from_file_location('agent_activity_store', SHARED / 'agent-activity-store.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def api():
    return load()


@pytest.fixture
def project(tmp_path):
    root = tmp_path / 'project'
    (root / '.claude').mkdir(parents=True)
    (root / '.claude' / 'dev.json').write_text('{"sesion":{"actividad":true}}', encoding='utf-8')
    return root


def state(project):
    return project / '.claude' / 'agent-activity'


def native(root, event='SubagentStart'):
    return {'hook_event_name': event, 'session_id': 'session-secret-id', 'agent_id': 'agent-secret-id', 'agent_type': 'custom-agents:qa', 'cwd': str(root)}


def entry(**changes):
    row = dict(runtime='claude', scope='subagent', session='session-secret-id', agent='agent-secret-id', role='qa',
        tool='Bash', resumen='git status', duracion_ms=12, resultado='ok', window=None, nowait=False)
    row.update(changes)
    return row


def boot(api, project):
    assert api.capture(project, runtime='claude', payload=native(project))['status'] == 'ok'


def ring(project):
    return json.loads((state(project) / 'events.json').read_bytes())


def tail_lines(project):
    path = state(project) / 'events.tail'
    return path.read_bytes().splitlines() if path.exists() else []


def tools(history):
    return [e['tool'] for e in history['events']]


def test_un_evento_de_herramienta_va_a_la_cola_sin_tocar_el_anillo(api, project):
    boot(api, project)
    antes = (state(project) / 'events.json').read_bytes()
    assert api.record(project, entry(tool='T0')) == {'status': 'ok', 'reason': None}
    assert (state(project) / 'events.json').read_bytes() == antes, 'el camino caliente no reescribe el anillo'
    assert len(tail_lines(project)) == 1
    h = api.history(project)
    assert h['status'] == 'ok' and tools(h) == ['T0'], 'history ve anillo + cola'


def test_el_camino_caliente_no_lee_ni_valida_el_anillo(api, project, monkeypatch):
    boot(api, project)
    def prohibido(*a, **k):
        raise AssertionError('el camino caliente no debe leer el anillo')
    monkeypatch.setattr(api, '_load_events', prohibido)
    monkeypatch.setattr(api, '_preload', prohibido)
    for i in range(3):
        assert api.record(project, entry(tool='T%d' % i))['status'] == 'ok'
    assert len(tail_lines(project)) == 3


def test_la_cola_se_pliega_al_anillo_al_superar_el_umbral_y_se_trunca(api, project):
    boot(api, project)
    n = 0
    while n < 200:
        assert api.record(project, entry(tool='T%d' % n, resumen=('git status %d ' % n).ljust(120, 'x')))['status'] == 'ok'
        n += 1
        if not tail_lines(project):
            break
    assert 3 <= n < 200, 'el umbral de pliegue no se alcanzo'
    assert tail_lines(project) == [], 'tras el pliegue la cola queda vacia'
    value = ring(project)
    assert [e['tool'] for e in value['events']] == ['T%d' % i for i in range(n)]
    assert [e['revision'] for e in value['events']] == list(range(1, n + 1))
    assert tools(api.history(project)) == ['T%d' % i for i in range(n)]


def test_una_caida_entre_publicar_y_truncar_no_duplica_eventos(api, project, monkeypatch):
    boot(api, project)
    original = api._state_io.StateIO.truncate
    def cae(self, *a, **k):
        raise OSError('caida simulada tras publicar el anillo')
    monkeypatch.setattr(api._state_io.StateIO, 'truncate', cae)
    n = 0
    while len(tail_lines(project)) < 1 or (state(project) / 'events.tail').stat().st_size < api.TAIL_FOLD_BYTES:
        assert api.record(project, entry(tool='T%d' % n, resumen=('git status %d ' % n).ljust(120, 'x')))['status'] == 'ok', 'el evento ya es duradero: la caida del pliegue no lo pierde'
        n += 1
        assert n < 200
    assert ring(project)['events'], 'el anillo se publico antes de la caida'
    assert tail_lines(project), 'la cola NO se trunco'
    assert tools(api.history(project)) == ['T%d' % i for i in range(n)], 'anillo + cola sin duplicados'
    monkeypatch.setattr(api._state_io.StateIO, 'truncate', original)
    assert api.record(project, entry(tool='Tfin'))['status'] == 'ok'
    assert tools(api.history(project)) == ['T%d' % i for i in range(n)] + ['Tfin']
    assert [e['revision'] for e in ring(project)['events']] == sorted({e['revision'] for e in ring(project)['events']})


def test_una_senal_de_ciclo_de_vida_pliega_la_cola(api, project):
    boot(api, project)
    for i in range(3):
        assert api.record(project, entry(tool='T%d' % i))['status'] == 'ok'
    assert len(tail_lines(project)) == 3
    assert api.capture(project, runtime='claude', payload=native(project, 'SubagentStop'))['status'] == 'ok'
    assert tail_lines(project) == []
    assert [e['tool'] for e in ring(project)['events']] == ['T0', 'T1', 'T2']
    assert api.history(project)['runs'][0]['ended_at'] is not None


def test_count_oversize_ve_anillo_y_cola(api, project):
    boot(api, project)
    for i in range(2):
        assert api.record(project, entry(tool='T%d' % i))['status'] == 'ok'
    assert api.count_oversize(project)['status'] == 'ok'
    h = api.history(project)
    assert h['descartados_por_tamano'] == 1 and tools(h) == ['T0', 'T1']


def test_la_ventana_de_atribucion_se_aplica_en_orden_al_plegar(api, project):
    boot(api, project)
    assert api.record(project, entry(tool='Bash', window=('start', 'plan/T-01')))['status'] == 'ok'
    assert api.record(project, entry(tool='Edit'))['status'] == 'ok'
    h = api.history(project)
    assert len(h['events']) == 2 and h['ventanas'] and h['ventanas'][0]['tarea'] == 'plan/T-01' and h['ventanas'][0]['estado'] == 'abierta'


def test_la_cola_es_un_fichero_propio_y_un_enlace_se_rechaza(api, project, tmp_path):
    boot(api, project)
    fuera = tmp_path / 'fuera.txt'
    fuera.write_bytes(b'')
    try:
        os.symlink(fuera, state(project) / 'events.tail')
    except (OSError, NotImplementedError):
        pytest.skip('sin enlaces simbolicos')
    r = api.record(project, entry())
    assert r['status'] == 'unavailable' and r['reason'] == 'unsafe_state', r
    assert fuera.read_bytes() == b'', 'no se escribe fuera del estado'


def test_una_linea_final_cortada_se_ignora_y_una_corrupta_falla_cerrado(api, project):
    boot(api, project)
    assert api.record(project, entry(tool='T0'))['status'] == 'ok'
    with open(state(project) / 'events.tail', 'ab') as handle:
        handle.write(b'{"id":"')
    assert tools(api.history(project)) == ['T0'], 'una linea final sin salto de linea (caida a mitad de la escritura) no cuenta'
    with open(state(project) / 'events.tail', 'ab') as handle:
        handle.write(b'\nesto no es json\n')
    assert api.history(project)['status'] == 'unavailable'
    assert api.record(project, entry(tool='T1'))['status'] in ('ok', 'unavailable')


def test_la_cola_tiene_tope_y_el_inventario_la_admite(api, project):
    boot(api, project)
    assert api.record(project, entry())['status'] == 'ok'
    names = sorted(p.name for p in state(project).iterdir())
    assert names == ['.gitignore', '.lock', 'events.json', 'events.tail', 'owner.json', 'snapshot.json']
    assert api.TAIL_FOLD_BYTES < api.TAIL_MAX_BYTES <= 128 * 1024


def test_nowait_hace_un_solo_intento_tambien_con_la_cola(api, project):
    boot(api, project)
    assert api.record(project, entry(runtime='codex', nowait=True, tool='M0'))['status'] == 'ok'
    assert len(tail_lines(project)) == 1


_BURST = ('import importlib.util,json,sys,time;'
    's=importlib.util.spec_from_file_location("s",sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);'
    'assert m.DEADLINE_SCALE==1 and m.TOOL_LOCK_WAIT==1.0 and m.TOOL_DEADLINE==1.3;'
    'e=json.loads(sys.argv[3]);e["tool"]="T%s"%sys.argv[4];'
    'time.sleep(max(0,float(sys.argv[5])-time.time()));print(json.dumps(m.record(sys.argv[2],e)))')


@pytest.mark.serie
@pytest.mark.parametrize('count', [8, 16])
def test_d2_rafaga_sobre_el_anillo_lleno_con_la_espera_REAL_no_pierde_ninguno(api, project, count):
    """Plazos reales (sin escala: 1 s de espera y 1,3 s de plazo). 8 de 8 es el criterio; la sonda de 16 se anota (no es un umbral del diseno)."""
    boot(api, project)
    now = time.time()
    heavy = [{'schema_version': 1, 'runtime': 'claude', 'run_key': 'a' * 64, 'role': None, 'tool': 'Bash', 'resumen': ('git status %d ' % i).ljust(160, 'y'),
        'tarea': None, 'duracion_ms': None, 'resultado': None, 'observed_at': now - 5, 'revision': i} for i in range(1, 501)]
    value = json.loads((state(project) / 'events.json').read_bytes())
    value.update(revision=500, events=heavy)
    (state(project) / 'events.json').write_bytes(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())
    env = {k: v for k, v in os.environ.items() if k not in ('PYTEST_CURRENT_TEST', 'CUSTOM_AGENTS_ACTIVITY_DEADLINE_SCALE')}
    start = time.time() + 4
    children = [subprocess.Popen([sys.executable, '-I', '-X', 'utf8', '-B', '-c', _BURST, str(SHARED / 'agent-activity-store.py'), str(project),
        json.dumps(entry()), str(i), repr(start)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=project, env=env) for i in range(count)]
    resultados = []
    for p in children:
        out, err = p.communicate(timeout=90)
        assert p.returncode == 0, err
        resultados.append(json.loads(out))
    perdidos = [r for r in resultados if r['status'] != 'ok']
    print('D2 sonda: count=%d perdidos=%d motivos=%s' % (count, len(perdidos), sorted({r['reason'] for r in perdidos})))   # (anadido tras el RED, k10) la cifra que el ledger anota
    if count == 8:
        assert perdidos == [], perdidos
    visto = tools(api.history(project))
    assert sum(1 for t in visto if t.startswith('T') and t[1:].isdigit()) == count - len(perdidos)


def test_la_cola_no_guarda_la_sesion_ni_el_agente_en_claro(api, project):
    """(anadido tras el RED, k14) La serie del panel (`test_panel_privacy`) lo cazo: la primera version de la cola guardaba `session`/`agent` en claro; el anillo solo guarda sus seudonimos."""
    boot(api, project)
    assert api.record(project, entry(tool='T0'))['status'] == 'ok'
    raw = (state(project) / 'events.tail').read_bytes()
    assert raw.count(b'\n') == 1
    for secreto in (b'session-secret-id', b'agent-secret-id'):
        assert secreto not in raw
    assert tools(api.history(project)) == ['T0']
