"""Correcciones de la revision de dos lentes (intento 3), gaps 3-1 y 3-2 de panel-redesign.

El saneado del modo servido es una LISTA BLANCA de texto libre que solo se muestra. Datos de prueba
genericos (`jdoe@example.org`, `jdoeuser`); nada del equipo donde se ejecuta.
"""
import copy
import http.client
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import threading
import types

import pytest

from test_panel_review_ui import HARNESS

RAIZ = Path(__file__).resolve().parents[1]
SCRIPTS = RAIZ / 'skills/plugin-panel/scripts'
DATOS = {'counts': dict.fromkeys(('agents', 'skills', 'commands', 'tools', 'hooks'), 0),
         'agents': [], 'skills': [], 'commands': [], 'tools': [], 'hooks': [],
         'runtimes': {}, 'memory': {}, 'warnings': [], 'workflow': {'roles': {}}}
RID = 'a' * 64
SEC = 'd' * 64
VERSION = {'raw_sha256': 'b' * 64, 'view_sha256': 'c' * 64, 'view_version': 'plan-text-v1'}
CORREO = 'jdoe@example.org'
RUTA = '/home/jdoeuser/notas'
SENSIBLES = ('jdoeuser', CORREO, '/home/')


def _cargar():
    spec = importlib.util.spec_from_file_location('fix3_serve', SCRIPTS / 'serve_panel.py')
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _scrub(servicio):
    redact = servicio._load_shared('redact.py')
    return lambda t: redact.anonimizar(redact.redactar(t), None, '/home/jdoeuser', 'jdoeuser')


def _producer():
    return {'caller_id': 'owned', 'runtime': 'codex', 'actor_id': None, 'identity_basis': 'declared'}


def _revision(texto_plan, texto_usuario, texto_agente):
    comentario = {'comment_id': 'one', 'section_id': SEC, 'text': texto_usuario}
    resultado = {'result_id': '1' * 64, 'comment_id': 'one', 'section_id': SEC,
                 'supersedes_result_id': None, 'disposition': 'addressed', 'response_text': texto_agente,
                 'text_flags': {'redacted': False, 'controls_sanitized': False}, 'producer': _producer(),
                 'recorded_at': '2026-10-09T10:00:03Z',
                 'artifact_observation': {'status': 'available', 'version': VERSION,
                                          'observed_at': '2026-10-09T10:00:03Z'}}
    return {'schema_version': 1, 'status': 'ok', 'reason': None, 'review': {
        'review_id': RID, 'initiative': 'docs/roadmap/2026-10-09-example', 'artifact': 'improvement-plan.md',
        'gate_key': 'plan-ok', 'version': VERSION, 'current_version': VERSION, 'revision': 1,
        'state': 'consumida', 'created_at': '2026-10-09T10:00:00Z', 'observed_at': '2026-10-09T10:00:01Z',
        'consumer_registration': {'caller_id': 'dev-cycle', 'runtime': 'codex',
                                  'registered_at': '2026-10-09T10:00:00Z'},
        'draft_comments': [], 'validity': 'current', 'complete': True, 'redacted': False,
        'controls_sanitized': False,
        'decision': {'decision_id': 'e' * 64, 'choice': 'request_changes', 'comments': [comentario],
                     'submitted_at': '2026-10-09T10:00:02Z'},
        'delivery': {'delivery_id': 'c' * 64, 'delivered_at': '2026-10-09T10:00:02Z'},
        'ack': {'decision_id': 'e' * 64, 'delivery_id': 'c' * 64, 'consumed_at': '2026-10-09T10:00:02Z'},
        'sections': [{'section_id': SEC, 'title': texto_plan, 'text': texto_plan, 'level': 1}],
        'feedback': {'schema_version': 1, 'results': [resultado], 'verifications': []}}}


def _servir(monkeypatch, tmp_path, propietario):
    servicio = _cargar()
    monkeypatch.setattr(servicio, '_load_review', lambda: propietario, raising=False)
    seleccion = {'initiative': 'docs/roadmap/2026-10-09-example', 'state_root': tmp_path / 's'}
    servidor = servicio.create_server(tmp_path, DATOS, review_selection=seleccion, scrub=_scrub(servicio))
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    return servidor, hilo


def _parar(servidor, hilo):
    servidor.shutdown(); servidor.server_close(); hilo.join(timeout=5)


def _pedir(servidor, op, metodo='GET', cuerpo=None):
    con = http.client.HTTPConnection('127.0.0.1', servidor.server_port, timeout=5)
    con.request(metodo, servidor.access_prefix + 'api/review/' + RID + '/' + op,
                json.dumps(cuerpo, ensure_ascii=False).encode('utf8') if cuerpo is not None else None,
                {'Content-Type': 'application/json'})
    r = con.getresponse(); datos = r.read().decode('utf8'); con.close()
    return r.status, json.loads(datos)


def _propietario(respuesta):
    return types.SimpleNamespace(open_review=lambda *a, **k: respuesta, get_view=lambda *a, **k: respuesta,
                                 get_status=lambda *a, **k: respuesta)


# (a) + (c): cuenta codex intacta, validador del navegador feliz, texto del plan y del agente anonimizados

def test_cuenta_codex_y_vocabulario_cerrado_intactos_y_texto_mostrado_anonimizado(monkeypatch, tmp_path):
    texto = f'Plan de jdoeuser en {RUTA}, avisar a {CORREO}'
    respuesta = _revision(texto, f'Comentario del usuario {CORREO} en {RUTA}', f'Hecho por jdoeuser ({CORREO})')
    servidor, hilo = _servir(monkeypatch, tmp_path, _propietario(respuesta))
    try:
        estado, datos = _pedir(servidor, 'view')
    finally:
        _parar(servidor, hilo)
    assert estado == 200
    rev = datos['review']
    assert rev['consumer_registration']['runtime'] == 'codex'
    assert rev['feedback']['results'][0]['producer'] == _producer()
    assert rev['state'] == 'consumida' and rev['decision']['choice'] == 'request_changes'
    # (c) lo que solo se muestra sale anonimizado
    visible = json.dumps([rev['sections'][0], rev['feedback']['results'][0]['response_text']],
                         ensure_ascii=False)
    for sensible in SENSIBLES:
        assert sensible not in visible, sensible
    # el comentario sellado por el usuario viaja tal cual
    assert rev['decision']['comments'][0]['text'] == f'Comentario del usuario {CORREO} en {RUTA}'
    # el validador del navegador acepta la respuesta del servidor
    node = shutil.which('node')
    if not node:
        pytest.skip('Node unavailable')
    escenario = ("await resolve(" + json.dumps(datos, ensure_ascii=False) + ");"
                 "assert.ok(ids['review-feedback'].textContent.includes('codex'));"
                 "assert.match(ids['review-status'].textContent,/consumida/i);"
                 "assert.ok(ids['review-feedback'].textContent.includes('Comentario del usuario'));")
    fuente = tmp_path / 'v.cjs'
    script = (SCRIPTS.parent / 'assets/panel-review.js').read_text(encoding='utf8')
    fuente.write_text(HARNESS + '\n' + script + '\n(async()=>{' + escenario
                      + '})().catch(error=>{console.error(error);process.exitCode=1;});', encoding='utf8')
    r = subprocess.run([node, str(fuente)], capture_output=True, text=True, encoding='utf8',
                       errors='replace', timeout=30)
    assert r.returncode == 0, r.stdout + r.stderr


# (b): ida y vuelta del comentario del usuario

def test_comentario_del_usuario_vuelve_intacto_y_se_entrega_intacto(monkeypatch, tmp_path):
    texto = f'Avisar a {CORREO}; revisar {RUTA} y a jdoeuser'
    guardado = []
    entregado = []

    def vista():
        base = _revision('Plan', 'x', 'y')
        rev = base['review']
        rev.update(state='pendiente', decision=None, delivery=None, ack=None,
                   draft_comments=copy.deepcopy(guardado))
        rev.pop('feedback')
        return base

    def guardar(proyecto, rid, version, comentarios, **k):
        guardado[:] = copy.deepcopy(comentarios)
        return vista()

    def decidir(proyecto, rid, version, eleccion, comentarios, **k):
        entregado[:] = copy.deepcopy(comentarios)
        return vista()

    propietario = types.SimpleNamespace(open_review=lambda *a, **k: vista(), get_view=lambda *a, **k: vista(),
                                        get_status=lambda *a, **k: vista(), save_comments=guardar,
                                        submit_decision=decidir)
    servidor, hilo = _servir(monkeypatch, tmp_path, propietario)
    try:
        comentario = {'comment_id': 'comment-0', 'section_id': SEC, 'text': texto}
        estado, datos = _pedir(servidor, 'comments', 'POST',
                               {'version': VERSION, 'comments': [comentario], 'expected_revision': 1})
        assert estado == 200
        devueltos = datos['review']['draft_comments']
        assert devueltos == [comentario]
        _pedir(servidor, 'submit', 'POST', {'version': VERSION, 'comments': devueltos,
                                            'expected_revision': 1, 'choice': 'request_changes'})
    finally:
        _parar(servidor, hilo)
    assert entregado == [comentario]


# (d): memoria sigue anonimizada, y los campos de vocabulario no se tocan

def test_memoria_anonimiza_texto_libre_y_conserva_vocabulario():
    servicio = _cargar()
    scrub = _scrub(servicio)
    nota = f'Ver {RUTA} con jdoeuser ({CORREO})'
    dato = {'status': 'ok', 'selected': {'id': 'ADR-001', 'titular': nota, 'texto': nota, 'evidencia': nota,
                                         'estado': 'aceptada', 'tipo': 'adr', 'source_sha256': 'f' * 64},
            'entries': [{'id': 'ADR-001', 'titular': nota, 'ruta': 'docs/knowledge/x.md'}]}
    limpio = servicio._scrubbed(copy.deepcopy(dato), scrub)
    visible = json.dumps(limpio, ensure_ascii=False)
    for sensible in SENSIBLES:
        assert sensible not in visible, sensible
    for clave in ('id', 'estado', 'tipo', 'source_sha256'):
        assert limpio['selected'][clave] == dato['selected'][clave]


def test_scrubbed_no_toca_text_fuera_de_sections():
    servicio = _cargar()
    scrub = lambda t: '<x>'
    valor = {'review': {'draft_comments': [{'text': 'mio'}], 'sections': [{'title': 'a', 'text': 'b'}],
                        'decision': {'comments': [{'text': 'mio'}]},
                        'feedback': {'results': [{'response_text': 'r'}], 'verifications': [{'note': 'n'}]}}}
    limpio = servicio._scrubbed(valor, scrub)['review']
    assert limpio['draft_comments'][0]['text'] == 'mio'
    assert limpio['decision']['comments'][0]['text'] == 'mio'
    assert limpio['sections'][0] == {'title': '<x>', 'text': '<x>'}
    assert limpio['feedback']['results'][0]['response_text'] == '<x>'
    assert limpio['feedback']['verifications'][0]['note'] == '<x>'


# --- Gap 3-3: alias 8.3 de Windows en la limpieza del manifiesto previo ---------------------------------

import hashlib
import sys

from test_panel_export import bundle, entorno, panel, _exportar  # noqa: E402,F401
from test_panel_fix2 import CHART, CHART_SHA, _manifiesto, _sha  # noqa: E402,F401


def _nombre_corto(ruta):
    """Alias 8.3 real del fichero (solo Windows con nombres cortos); None si no hay."""
    import ctypes
    buf = ctypes.create_unicode_buffer(1024)
    n = ctypes.windll.kernel32.GetShortPathNameW(str(ruta), buf, 1024)
    return buf.value if n else None


@pytest.mark.parametrize('rel', ['vendor/chart.js/CHARTU~1.JS', 'a~1/x.txt', 'vendor/CHART~12.js'])
def test_una_entrada_con_patron_de_nombre_corto_8_3_aborta_y_deja_chart(panel, bundle, tmp_path, rel, capsys):
    destino = tmp_path / 'salida'
    assert _exportar(panel, bundle, destino) == 0
    entradas = json.loads((destino / 'export-manifest.json').read_text(encoding='utf8'))['ficheros']
    _manifiesto(destino, entradas + [{'ruta': rel, 'sha256': CHART_SHA, 'bytes': 1}])
    assert _exportar(panel, bundle, destino) == 2
    assert (destino / CHART).is_file() and _sha((destino / CHART).read_bytes()) == CHART_SHA


def test_la_limpieza_no_borra_lo_recien_escrito_aunque_la_ruta_sea_un_alias_8_3(panel, bundle, tmp_path):
    if sys.platform != 'win32':
        pytest.skip('los alias 8.3 son de Windows')
    destino = tmp_path / 'salida'
    assert _exportar(panel, bundle, destino) == 0
    corto = _nombre_corto(destino / CHART)
    if not corto or '~' not in corto:
        pytest.skip('el volumen no genera nombres cortos 8.3')
    rel = Path(corto).relative_to(_nombre_corto(destino) or destino).as_posix()
    modulo = panel._load_pages()
    raiz = destino.resolve()
    escritos = {(destino / CHART).resolve()}
    assert modulo._borrar_si_es_nuestro(destino, raiz, rel, CHART_SHA, lambda p: p.is_symlink(), escritos) is False
    assert (destino / CHART).is_file() and _sha((destino / CHART).read_bytes()) == CHART_SHA
