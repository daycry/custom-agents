"""plugin-audit-2, T-23 fix24 (intento 19, gaps 1, 2, 3 y 12 del almacen de actividad): linea cortada + append, sello de configuracion en la cola, vista recortada y lectura cola->anillo."""
import importlib.util
import json
from pathlib import Path
import sys
import time

import pytest

SHARED = Path(__file__).resolve().parents[1] / 'agent-kits' / 'shared'


@pytest.fixture(autouse=True)
def _plazos_inyectados(monkeypatch):
    monkeypatch.setenv('CUSTOM_AGENTS_ACTIVITY_DEADLINE_SCALE', '20')


@pytest.fixture
def api():
    spec = importlib.util.spec_from_file_location('agent_activity_store', SHARED / 'agent-activity-store.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


def tools(history):
    return [e['tool'] for e in history['events']]


def test_gap1_un_append_tras_una_linea_cortada_no_corrompe_la_cola(api, project):
    boot(api, project)
    assert api.record(project, entry(tool='T0'))['status'] == 'ok'
    with open(state(project) / 'events.tail', 'ab') as handle:
        handle.write(b'{"id":"')                          # escritura cortada por una caida
    assert api.record(project, entry(tool='T1'))['status'] == 'ok'
    h = api.history(project)
    assert h['status'] == 'ok', h
    assert tools(h) == ['T0', 'T1']
    assert api.fold_tail(project)['status'] == 'ok'
    assert tools(api.history(project)) == ['T0', 'T1']


def test_gap1_una_linea_intermedia_que_no_es_una_cortada_reconocible_sigue_fallando_cerrado(api, project):
    boot(api, project)
    assert api.record(project, entry(tool='T0'))['status'] == 'ok'
    with open(state(project) / 'events.tail', 'ab') as handle:
        handle.write(b'esto no es json\n')
    assert api.record(project, entry(tool='T1'))['status'] in ('ok', 'unavailable')
    assert api.history(project)['status'] == 'unavailable'
    with open(state(project) / 'events.tail', 'ab') as handle:
        handle.write(b'{"id":"abcdef0123456789","at":1,"e":{}}\n')   # JSON valido de esquema incorrecto: tampoco se tolera
    assert api.history(project)['status'] == 'unavailable'


def test_gap2_editar_dev_json_caduca_una_ventana_cuyo_start_sigue_en_la_cola(api, project, monkeypatch):
    real = time.time
    off = [0.0]
    monkeypatch.setattr(api.time, 'time', lambda: real() + off[0])
    boot(api, project)
    off[0] = 10
    assert api.record(project, entry(tool='S', window=('start', 'plan/T-01')))['status'] == 'ok'
    off[0] = 20
    (project / '.claude' / 'dev.json').write_text('{"sesion":{"actividad":true},"x":1}', encoding='utf-8')
    off[0] = 30
    assert api.record(project, entry(tool='E2'))['status'] == 'ok'
    off[0] = 40
    assert api.fold_tail(project)['status'] == 'ok'
    off[0] = 50
    assert api.record(project, entry(tool='E3'))['status'] == 'ok'
    h = api.history(project)
    assert [(w['tarea'], w['estado']) for w in h['ventanas']] == [('plan/T-01', 'caducada')]
    assert [(e['tool'], e['tarea']) for e in h['events']] == [('S', None), ('E2', None), ('E3', None)]


def test_gap3_la_vista_recorta_a_500_como_el_pliegue(api, project):
    boot(api, project)
    now = time.time()
    heavy = [{'schema_version': 1, 'runtime': 'claude', 'run_key': 'a' * 64, 'role': None, 'tool': 'Bash', 'resumen': 'x',
        'tarea': None, 'duracion_ms': None, 'resultado': None, 'observed_at': now - 5, 'revision': i} for i in range(1, 501)]
    value = json.loads((state(project) / 'events.json').read_bytes())
    value.update(revision=500, events=heavy)
    (state(project) / 'events.json').write_bytes(json.dumps(value, sort_keys=True, separators=(',', ':')).encode())
    for i in range(5):
        assert api.record(project, entry(tool='N%d' % i))['status'] == 'ok'
    h = api.history(project)
    assert h['status'] == 'ok' and len(h['events']) == 500, len(h['events'])
    assert tools(h)[-5:] == ['N%d' % i for i in range(5)] and h['recortado'] == 5
    spec = importlib.util.spec_from_file_location('serve_panel_fix24', SHARED.parents[1] / 'skills' / 'plugin-panel' / 'scripts' / 'serve_panel.py')
    panel = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(panel)
    value, reason = panel.activity_history(project)
    assert reason is None and len(value['events']) == 500, reason


def test_gap12_un_pliegue_entre_las_dos_lecturas_no_hace_perder_eventos(api, project, monkeypatch):
    boot(api, project)
    for i in range(3):
        assert api.record(project, entry(tool='T%d' % i))['status'] == 'ok'
    done = []
    def una_vez(original):
        def wrapper(*a, **k):
            result = original(*a, **k)
            if not done:
                done.append(True)
                assert api.fold_tail(project)['status'] == 'ok'   # otro proceso pliega y trunca justo despues de la PRIMERA lectura
            return result
        return wrapper
    monkeypatch.setattr(api, '_load_events', una_vez(api._load_events))
    monkeypatch.setattr(api, '_read_tail', una_vez(api._read_tail))
    h = api.history(project)
    assert h['status'] == 'ok' and tools(h) == ['T0', 'T1', 'T2'], h
