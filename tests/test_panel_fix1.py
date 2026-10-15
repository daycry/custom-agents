"""Correcciones de la revisión de dos lentes (intento 1) de la Fase 1 de panel-redesign.

Gaps 1, 2, 3, 4, 7, 8 y 10 de `docs/roadmap/2026-10-15-panel-redesign/tasks.md`. Datos de prueba
genéricos (`jdoe@example.org`); nada del equipo donde se ejecuta.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import types

import pytest

from test_panel_contract_golden import materializar
from test_panel_export import _escribir, _exportar, bundle, entorno, panel, CORREO, USUARIO  # noqa: F401

RAIZ = Path(__file__).resolve().parents[1]
SCRIPTS = RAIZ / 'skills/plugin-panel/scripts'
VOCABULARIO = {'scope': {'project', 'user', 'local'},
               'runtime': {'claude-code', 'codex', 'opencode'},
               'kind': {'agent', 'skill', 'command', 'persona', 'tool-source', 'mcp'}}


def _cargar(nombre):
    spec = importlib.util.spec_from_file_location('fix1_' + nombre, SCRIPTS / (nombre + '.py'))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture
def pp():
    return _cargar('panel_pages')


def _sha(contenido):
    return hashlib.sha256(contenido).hexdigest()


def _datos_pagina(html):
    bloque = re.search(r'<script[^>]*id="panel-data">(.*?)</script>', html, re.S).group(1)
    return json.loads(bloque)


# --- Gap 1: el manifiesto previo no puede sacar el borrado fuera del destino (CWE-22) ---------------

def _manifiesto(destino, entradas):
    destino.mkdir(exist_ok=True)
    (destino / 'export-manifest.json').write_text(
        json.dumps({'generador': 'custom-agents plugin-panel', 'version': 1, 'generado': 'x', 'ficheros': entradas}),
        encoding='utf8')


def _victima(tmp_path):
    victima = tmp_path / 'victima'
    victima.mkdir()
    fichero = victima / 'settings.json'
    fichero.write_bytes(b'{"mio": true}')
    return fichero


@pytest.mark.parametrize('ruta', ['../victima/settings.json', '/victima/settings.json', 'C:/victima/settings.json',
                                  'C:\\victima\\settings.json', 'a\\..\\..\\victima\\settings.json',
                                  './settings.json', 'a//settings.json', '', 'C:', 'a/./b.html', 'a/b/'])
def test_una_ruta_del_manifiesto_fuera_del_destino_no_borra_nada(pp, tmp_path, ruta):
    fichero = _victima(tmp_path)
    destino = tmp_path / 'salida'
    _manifiesto(destino, [{'ruta': ruta, 'sha256': _sha(fichero.read_bytes()), 'bytes': 13}])
    with pytest.raises(ValueError) as error:
        pp.exportar_sitio(destino, {'counts': {}})
    assert str(tmp_path) not in str(error.value)
    assert fichero.read_bytes() == b'{"mio": true}'
    assert not (destino / 'index.html').exists(), 'una entrada inválida aborta antes de escribir'


def test_la_ruta_absoluta_real_de_la_victima_tampoco_se_borra(pp, tmp_path):
    fichero = _victima(tmp_path)
    destino = tmp_path / 'salida'
    _manifiesto(destino, [{'ruta': str(fichero.resolve()), 'sha256': _sha(fichero.read_bytes()), 'bytes': 13}])
    with pytest.raises(ValueError):
        pp.exportar_sitio(destino, {'counts': {}})
    assert fichero.exists()


@pytest.mark.parametrize('entrada', [
    'texto', 7, {'ruta': 5, 'sha256': '0' * 64}, {'ruta': 'a.html', 'sha256': 'xyz'},
    {'ruta': 'a.html', 'sha256': 'A' * 63}, {'ruta': 'a.html'}, {'sha256': '0' * 64}])
def test_una_entrada_mal_formada_del_manifiesto_aborta(pp, tmp_path, entrada):
    destino = tmp_path / 'salida'
    _manifiesto(destino, [entrada])
    with pytest.raises(ValueError):
        pp.exportar_sitio(destino, {'counts': {}})
    assert not (destino / 'index.html').exists()


def test_un_padre_que_es_enlace_no_deja_borrar_a_traves_de_el(pp, tmp_path):
    fichero = _victima(tmp_path)
    destino = tmp_path / 'salida'
    destino.mkdir()
    try:
        (destino / 'sub').symlink_to(fichero.parent, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip('sin permiso para crear enlaces simbólicos')
    _manifiesto(destino, [{'ruta': 'sub/settings.json', 'sha256': _sha(fichero.read_bytes()), 'bytes': 13}])
    with pytest.raises(ValueError) as error:
        pp.exportar_sitio(destino, {'counts': {}})
    assert str(tmp_path) not in str(error.value)
    assert fichero.exists()


def test_una_entrada_valida_anidada_que_ya_no_se_genera_si_se_limpia(pp, tmp_path):
    destino = tmp_path / 'salida'
    viejo = destino / 'sub' / 'viejo.html'
    viejo.parent.mkdir(parents=True)
    viejo.write_bytes(b'generado antes')
    _manifiesto(destino, [{'ruta': 'sub/viejo.html', 'sha256': _sha(b'generado antes'), 'bytes': 14}])
    pp.exportar_sitio(destino, {'counts': {}})
    assert not viejo.exists()


# --- Gap 2: el vocabulario cerrado del inventario no se anonimiza ------------------------------------

@pytest.mark.parametrize('usuario', ['user', 'project', 'agent', 'codex'])
def test_un_usuario_con_nombre_de_vocabulario_no_rompe_la_exportacion_ni_los_filtros(
        tmp_path, monkeypatch, usuario):
    bp = _cargar('build_panel')
    copia = materializar(tmp_path / 'copia')
    for variable in ('USERNAME', 'USER', 'LOGNAME', 'LNAME'):
        monkeypatch.setenv(variable, usuario)
    destino = tmp_path / 'salida'
    assert bp.main(['--root', str(copia / 'bundle'), '--project', str(copia / 'project'),
                    '--home', str(copia / 'home'), '--export', str(destino)]) == 0
    html = (destino / 'catalogo.html').read_text(encoding='utf8')
    for atributo, permitidos in VOCABULARIO.items():
        patron = (r'extension-card" data-kind="([^"]*)"' if atributo == 'kind' else rf'data-{atributo}="([^"]*)"')
        valores = set(re.findall(patron, html))
        assert valores and valores <= permitidos, (atributo, valores)
    inventario = _datos_pagina(html)['inventario']
    assert {h['runtime'] for h in inventario['hooks']} <= VOCABULARIO['runtime'] and inventario['hooks']
    assert {p['scope'] for p in inventario['extensions']['pieces']} <= VOCABULARIO['scope']
    assert {p['kind'] for p in inventario['extensions']['pieces']} <= VOCABULARIO['kind']
    assert 'codex' in {h['runtime'] for h in inventario['hooks']}


# --- Gap 3: se anonimiza antes de recortar ------------------------------------------------------------

def _bundle_con_descripcion(tmp_path, descripcion):
    raiz = tmp_path / 'b'
    _escribir(raiz, 'agents/largo.md', '---\nname: largo\ndescription: ' + descripcion + '\nmodel: sonnet\n---\nx')
    return raiz


def test_un_correo_que_cruza_el_corte_de_480_no_se_filtra_a_medias(panel, tmp_path, entorno):
    raiz = _bundle_con_descripcion(tmp_path, 'a' * 472 + ' ana.lopez@example.org')
    assert _exportar(panel, raiz, tmp_path / 'salida') == 0
    html = (tmp_path / 'salida/catalogo.html').read_text(encoding='utf8')
    assert 'ana.lop' not in html


def test_una_ruta_del_home_que_cruza_el_corte_de_480_no_se_filtra_a_medias(panel, tmp_path, entorno):
    home = str(entorno).replace('\\', '/')
    # El corte de 480 cae dentro del último componente del home: sin anonimizar antes, queda la ruta partida.
    raiz = _bundle_con_descripcion(tmp_path, 'b' * (481 - len(home)) + ' ' + home)
    assert _exportar(panel, raiz, tmp_path / 'salida', '--home', str(entorno)) == 0
    html = (tmp_path / 'salida/catalogo.html').read_text(encoding='utf8')
    assert entorno.parent.name not in html


def test_los_textos_de_extensiones_tambien_se_anonimizan_antes_de_recortar(panel, tmp_path, entorno):
    proyecto = tmp_path / 'proyecto'
    _escribir(proyecto, '.claude/agents/ext.md',
              '---\nname: ext\ndescription: ' + 'c' * 472 + ' ana.lopez@example.org\nmodel: sonnet\n---\nx')
    raiz = tmp_path / 'b'
    _escribir(raiz, 'agents/demo.md', '---\nname: demo\ndescription: d\nmodel: sonnet\n---\nx')
    assert _exportar(panel, raiz, tmp_path / 'salida', '--project', str(proyecto)) == 0
    html = (tmp_path / 'salida/catalogo.html').read_text(encoding='utf8')
    assert 'ext' in html and 'ana.lop' not in html


# --- Gap 4: el modo servido aplica el mismo saneado que el exportado ------------------------------------

def _servir(panel, raiz, project):
    capturado = {}
    servicio = _cargar('serve_panel')

    def ejecutar(proyecto, datos, **kw):
        servidor = servicio.create_server(proyecto, datos, scrub=kw.get('scrub'))
        try:
            capturado['paginas'] = dict(servidor.pages)
        finally:
            servidor.server_close()
        return 0
    panel._load_server = lambda: types.SimpleNamespace(run=ejecutar)
    assert panel.main(['--serve', '--project', str(project), '--root', str(raiz)]) == 0
    return capturado['paginas']


def test_el_catalogo_servido_no_lleva_home_correo_ni_usuario(panel, bundle, tmp_path, entorno):
    paginas = _servir(panel, bundle, bundle)
    texto = paginas['catalogo.html'].decode('utf8')
    for sensible in (USUARIO, CORREO, str(entorno), str(entorno).replace('\\', '/')):
        assert sensible.lower() not in texto.lower(), sensible
    assert '&lt;correo&gt;' in texto or '\\u003ccorreo\\u003e' in texto


def test_progress_snapshot_anonimiza_los_titulos_con_el_mismo_saneado(tmp_path):
    servicio = _cargar('serve_panel')
    ruta = tmp_path / 'docs/roadmap/2026-10-09-demo/tasks.md'
    ruta.parent.mkdir(parents=True)
    ruta.write_text('---\nestado: en-progreso\n---\n# W\n## Fase 1 — Build\n'
                    '### T-01 — Avisar a jdoe@example.org\n- **Estado**: en-progreso\n', encoding='utf8', newline='\n')
    assert 'jdoe@example.org' in json.dumps(servicio.progress_snapshot(tmp_path))
    con = json.dumps(servicio.progress_snapshot(tmp_path, scrub=lambda t: t.replace('jdoe@example.org', '<correo>')))
    assert 'jdoe@example.org' not in con and '<correo>' in con


# --- Gaps 7 y 8: exportación sin crear carpetas ajenas y sin dejar nada a medias ------------------------

def test_no_se_crean_los_padres_del_destino(panel, bundle, tmp_path, capsys):
    destino = tmp_path / 'no-existe' / 'panel'
    assert _exportar(panel, bundle, destino) == 2
    assert not (tmp_path / 'no-existe').exists()
    assert str(tmp_path) not in capsys.readouterr().err


def test_un_fichero_donde_va_un_directorio_se_detecta_antes_de_escribir(panel, bundle, tmp_path, capsys):
    destino = tmp_path / 'salida'
    _escribir(destino, 'assets', 'soy un fichero')
    assert _exportar(panel, bundle, destino) == 2
    assert (destino / 'assets').read_text(encoding='utf8') == 'soy un fichero'
    assert not (destino / 'agentes.html').exists() and not (destino / 'index.html').exists()
    assert str(tmp_path) not in capsys.readouterr().err


def test_roadmap_status_no_exporta_sin_roadmap_ni_si_el_dashboard_falla():
    texto = (RAIZ / 'commands/roadmap-status.md').read_text(encoding='utf8')
    bloque = re.search(r'```bash\n(.*?)```', texto, re.S).group(1)
    assert '[ -d docs/roadmap ]' in bloque
    assert re.search(r'--md docs/roadmap/dashboard\.md\s*&&\s*\\?\s*python3 "\$PANEL"', bloque)


# --- Gap 10: la description dice lo que escribe ---------------------------------------------------------

def test_la_description_de_roadmap_status_declara_lo_que_escribe():
    texto = (RAIZ / 'commands/roadmap-status.md').read_text(encoding='utf8')
    descripcion = re.search(r'^description: (.*)$', texto, re.M).group(1)
    assert 'no modifica nada' not in descripcion.lower()
    assert 'dashboard.md' in descripcion and 'docs/roadmap/panel/' in descripcion
