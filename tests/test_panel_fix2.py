"""Correcciones de la revisión de dos lentes (intento 2) de la Fase 1 de panel-redesign.

Gaps 2-3 a 2-8 de `docs/roadmap/2026-10-15-panel-redesign/tasks.md`. Datos de prueba genéricos
(`jdoe@example.org`, `jdoeuser`); nada del equipo donde se ejecuta.
"""
import http.client
import importlib.util
import json
from pathlib import Path
import threading
import types

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SCRIPTS = RAIZ / 'skills/plugin-panel/scripts'
DATOS = {'counts': dict.fromkeys(('agents', 'skills', 'commands', 'tools', 'hooks'), 0),
         'agents': [], 'skills': [], 'commands': [], 'tools': [], 'hooks': [],
         'runtimes': {}, 'memory': {}, 'warnings': [], 'workflow': {'roles': {}}}


def _cargar(nombre):
    spec = importlib.util.spec_from_file_location('fix2_' + nombre, SCRIPTS / (nombre + '.py'))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


# --- Gap 2-3: api/memory y api/review pasan por el mismo saneador en modo servido -------------------

def _scrub(texto):
    redact = _cargar('serve_panel')._load_shared('redact.py')
    return redact.anonimizar(redact.redactar(texto), None, '/home/jdoeuser', 'jdoeuser')


def _servir(monkeypatch, tmp_path, query, **kw):
    servicio = _cargar('serve_panel')
    validador = servicio._load_shared('knowledge-view.py')
    monkeypatch.setattr(servicio, '_load_memory', lambda: types.SimpleNamespace(
        query=lambda root, **a: query(a), valid_request=validador.valid_request), raising=False)
    servidor = servicio.create_server(tmp_path, DATOS, scrub=_scrub, **kw)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    return servidor, hilo


def _parar(servidor, hilo):
    servidor.shutdown(); servidor.server_close(); hilo.join(timeout=5)


def test_api_memory_servida_no_lleva_home_correo_ni_usuario(monkeypatch, tmp_path):
    nota = 'Ver /home/jdoeuser/notas con jdoeuser (jdoe@example.org)'
    def consulta(args):
        entrada = {'id': 'ADR-001', 'titular': nota, 'evidencia': nota, 'ruta': 'docs/knowledge/x.md'}
        return {'version': 1, 'source': 'canonical_knowledge', 'operation': 'show', 'status': 'ok',
                'complete': True, 'issues': [], 'entries': [entrada],
                'selected': dict(entrada, texto=nota), 'related': None, 'budget': {'files': 1}}
    servidor, hilo = _servir(monkeypatch, tmp_path, consulta)
    try:
        con = http.client.HTTPConnection('127.0.0.1', servidor.server_port, timeout=5)
        con.request('POST', servidor.access_prefix + 'api/memory',
                    json.dumps({'operation': 'show', 'id': 'ADR-001'}),
                    {'Content-Type': 'application/json'})
        respuesta = con.getresponse(); cuerpo = respuesta.read().decode('utf8'); con.close()
    finally:
        _parar(servidor, hilo)
    assert respuesta.status == 200
    for sensible in ('jdoeuser', 'jdoe@example.org', '/home/'):
        assert sensible not in cuerpo, sensible
    datos = json.loads(cuerpo)
    assert datos['selected']['id'] == 'ADR-001' and '<usuario>' in datos['selected']['texto']


def test_api_review_servida_tampoco_lleva_datos_personales_y_conserva_los_ids(monkeypatch, tmp_path):
    rid = 'a' * 64
    texto = 'Plan de jdoeuser en /home/jdoeuser/p, avisar a jdoe@example.org'
    resultado = {'schema_version': 1, 'status': 'ok', 'reason': None,
                 'review': {'review_id': rid, 'revision': 0,
                            'sections': [{'section_id': 'b' * 64, 'title': texto, 'text': texto}]}}
    servicio = _cargar('serve_panel')
    propietario = types.SimpleNamespace(
        open_review=lambda *a, **k: resultado, get_view=lambda *a, **k: resultado,
        get_status=lambda *a, **k: resultado)
    monkeypatch.setattr(servicio, '_load_review', lambda: propietario, raising=False)
    seleccion = {'initiative': 'docs/roadmap/2026-10-09-x', 'state_root': tmp_path / 's'}
    servidor = servicio.create_server(tmp_path, DATOS, review_selection=seleccion, scrub=_scrub)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True); hilo.start()
    try:
        con = http.client.HTTPConnection('127.0.0.1', servidor.server_port, timeout=5)
        con.request('GET', servidor.access_prefix + 'api/review/' + rid + '/view')
        respuesta = con.getresponse(); cuerpo = respuesta.read().decode('utf8'); con.close()
    finally:
        _parar(servidor, hilo)
    assert respuesta.status == 200
    for sensible in ('jdoeuser', 'jdoe@example.org', '/home/'):
        assert sensible not in cuerpo, sensible
    assert rid in cuerpo and 'b' * 64 in cuerpo


# --- Gaps 2-4 y 2-7: la limpieza del manifiesto previo ----------------------------------------------------

import hashlib
import shutil
import sys

from test_panel_export import bundle, entorno, panel, _exportar  # noqa: E402,F401

CHART = 'vendor/chart.js/chart.umd.min.js'
CHART_SHA = '48444a82d4edcb5bec0f1965faacdde18d9c17db3063d042abada2f705c9f54a'


def _sha(contenido):
    return hashlib.sha256(contenido).hexdigest()


def _manifiesto(destino, entradas):
    destino.mkdir(exist_ok=True)
    (destino / 'export-manifest.json').write_text(json.dumps(
        {'generador': 'custom-agents plugin-panel', 'version': 1, 'generado': 'x', 'ficheros': entradas}),
        encoding='utf8')


def _enlace_directorio(destino, objetivo):
    """Junction en Windows (sin privilegios), symlink en el resto; skip si la máquina no puede."""
    try:
        if sys.platform == 'win32':
            import _winapi
            _winapi.CreateJunction(str(objetivo), str(destino))
        else:
            destino.symlink_to(objetivo, target_is_directory=True)
    except (OSError, NotImplementedError, ImportError, AttributeError):
        pytest.skip('la máquina no crea enlaces ni junctions')


def test_un_padre_cambiado_por_un_enlace_durante_la_escritura_no_borra_fuera(panel, bundle, tmp_path):
    contenido = b'{"mio": true}'
    victima = tmp_path / 'victima'
    victima.mkdir()
    (victima / 'x.txt').write_bytes(contenido)
    destino = tmp_path / 'salida'
    _manifiesto(destino, [{'ruta': 'viejo/x.txt', 'sha256': _sha(contenido), 'bytes': len(contenido)}])
    (destino / 'viejo').mkdir()
    (destino / 'viejo' / 'x.txt').write_bytes(contenido)
    modulo = panel._load_pages()
    escribir = modulo._escribir_atomico
    hecho = []

    def escribir_y_sustituir(ruta, datos):
        escribir(ruta, datos)
        if not hecho:
            hecho.append(1)
            shutil.rmtree(destino / 'viejo')
            _enlace_directorio(destino / 'viejo', victima)

    modulo._escribir_atomico = escribir_y_sustituir
    try:
        _exportar(panel, bundle, destino)
    finally:
        modulo._escribir_atomico = escribir
    assert hecho and (victima / 'x.txt').read_bytes() == contenido


def test_entradas_que_el_sistema_de_ficheros_confunde_con_lo_escrito_no_borran_chart(panel, bundle, tmp_path):
    destino = tmp_path / 'salida'
    assert _exportar(panel, bundle, destino) == 0
    manifiesto = json.loads((destino / 'export-manifest.json').read_text(encoding='utf8'))
    entradas = manifiesto['ficheros']
    # Solo cambia mayúsculas: lo trata como el mismo fichero un sistema de ficheros que no las distingue.
    extra = {'ruta': CHART.upper().replace('VENDOR/CHART.JS/', 'vendor/chart.js/'), 'sha256': CHART_SHA, 'bytes': 1}
    _manifiesto(destino, entradas + [extra])
    assert _exportar(panel, bundle, destino) == 0
    assert (destino / CHART).is_file() and _sha((destino / CHART).read_bytes()) == CHART_SHA
    nuevo = json.loads((destino / 'export-manifest.json').read_text(encoding='utf8'))
    assert CHART in {f['ruta'] for f in nuevo['ficheros']}


@pytest.mark.parametrize('sufijo', ['.', ' ', '. .'])
def test_una_entrada_con_punto_o_espacio_final_aborta_y_deja_chart(panel, bundle, tmp_path, sufijo, capsys):
    destino = tmp_path / 'salida'
    assert _exportar(panel, bundle, destino) == 0
    entradas = json.loads((destino / 'export-manifest.json').read_text(encoding='utf8'))['ficheros']
    _manifiesto(destino, entradas + [{'ruta': CHART + sufijo, 'sha256': CHART_SHA, 'bytes': 1}])
    assert _exportar(panel, bundle, destino) == 2
    assert (destino / CHART).is_file() and _sha((destino / CHART).read_bytes()) == CHART_SHA
    assert str(tmp_path) not in capsys.readouterr().err


# --- Gap 2-5: model y tools son texto libre del frontmatter, no vocabulario cerrado ----------------------

def test_model_y_tools_no_estan_entre_las_claves_cerradas(panel):
    assert not {'model', 'tools'} & panel.CLAVES_CERRADAS


def test_un_model_con_home_y_correo_se_anonimiza_en_la_exportacion(panel, tmp_path, entorno):
    from test_panel_export import CORREO
    home = str(entorno).replace(chr(92), '/')
    raiz = tmp_path / 'b'
    (raiz / 'agents').mkdir(parents=True)
    (raiz / 'agents/demo.md').write_text(
        f'---\nname: demo\ndescription: d\nmodel: {home}/models {CORREO}\ntools: Read, {CORREO}\n---\nx',
        encoding='utf8', newline='\n')
    assert _exportar(panel, raiz, tmp_path / 'salida', '--home', str(entorno)) == 0
    html = (tmp_path / 'salida/catalogo.html').read_text(encoding='utf8')
    for sensible in (CORREO, home, str(entorno)):
        assert sensible.lower() not in html.lower(), sensible


# --- Gap 2-10: la defensa de `_route` (sin `? % \ #`) tiene test propio; antes era un mutante equivalente -----

CAPABILITY = 'A' * 43


@pytest.mark.parametrize('sufijo', [
    'index.html?x', 'index.html%2e', '%69ndex.html', 'index.html#x', 'index.html\\x',
    'assets\\panel.css', 'assets/panel.css?v=1', 'assets/%70anel.css', 'api/progress#x'])
def test_route_rechaza_cualquier_ruta_con_consulta_porcentaje_barra_invertida_o_fragmento(sufijo):
    servicio = _cargar('serve_panel')
    manejador = servicio.PanelHandler
    peticion = lambda ruta: types.SimpleNamespace(path=ruta, server=types.SimpleNamespace(capability=CAPABILITY))
    # Control: la misma ruta limpia SÍ se enruta, así que el rechazo viene del filtro y no de otra cosa.
    assert manejador._route(peticion('/' + CAPABILITY + '/index.html')) == 'index.html'
    assert manejador._route(peticion('/' + CAPABILITY + '/' + sufijo)) is None
