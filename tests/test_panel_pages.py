"""T-05: plantilla común multi-página del panel (panel_pages.py + assets)."""
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess

import pytest

RAIZ = Path(__file__).resolve().parents[1]
SCRIPTS = RAIZ / 'skills/plugin-panel/scripts'
ASSETS = RAIZ / 'skills/plugin-panel/assets'
ORDEN = [('index.html', 'Inicio'), ('iniciativas.html', 'Iniciativas'), ('plan.html', 'Plan'),
         ('agentes.html', 'Agentes en vivo'), ('memoria.html', 'Memoria'),
         ('catalogo.html', 'Catálogo'), ('diagnostico.html', 'Diagnóstico')]


def _cargar(nombre):
    spec = importlib.util.spec_from_file_location(nombre, SCRIPTS / f'{nombre}.py')
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope='module')
def pp():
    return _cargar('panel_pages')


def _paginas(pp, modo='exportado'):
    return {archivo: pp.render_page(slug, modo=modo, generado='2026-10-15 10:00 UTC',
                                    datos={'pagina': slug})
            for slug, archivo, _ in pp.PAGES}


def _nav(html):
    encontrados = re.findall(r'<nav\b.*?</nav>', html, re.S)
    assert len(encontrados) == 1
    return encontrados[0]


def test_siete_paginas_en_orden_fijo(pp):
    assert [(archivo, titulo) for _, archivo, titulo in pp.PAGES] == ORDEN


def test_las_siete_paginas_comparten_el_mismo_nav_salvo_aria_current(pp):
    paginas = _paginas(pp)
    normalizados = {re.sub(r' aria-current="page"', '', _nav(html)) for html in paginas.values()}
    assert len(normalizados) == 1
    nav = normalizados.pop()
    assert [m for m in re.findall(r'<a [^>]*href="([^"]+)"', nav)] == [a for a, _ in ORDEN]
    assert re.findall(r'<a [^>]*>([^<]+)</a>', nav) == [t for _, t in ORDEN]


def test_aria_current_solo_en_la_pagina_actual(pp):
    for slug, archivo, _ in pp.PAGES:
        html = pp.render_page(slug, modo='exportado', generado='x', datos={})
        nav = _nav(html)
        assert nav.count('aria-current') == 1
        assert re.search(rf'<a [^>]*href="{re.escape(archivo)}"[^>]*aria-current="page"', nav)


def test_salto_al_contenido_y_main_destino(pp):
    for html in _paginas(pp).values():
        assert html.index('href="#main"') < html.index('<nav')
        assert 'Saltar al contenido' in html
        assert re.search(r'<main id="main" tabindex="-1">', html)


def test_marca_idioma_y_icono(pp):
    bp = _cargar('build_panel')
    assert pp.MARKER == bp.MARKER
    for html in _paginas(pp).values():
        assert html.startswith(pp.MARKER)
        assert '<html lang="es">' in html
        assert '<link rel="icon" href="data:,">' in html


def test_ningun_script_inline_ejecutable(pp):
    for html in _paginas(pp).values():
        etiquetas = re.findall(r'<script\b([^>]*)>(.*?)</script>', html, re.S)
        assert etiquetas
        for atributos, cuerpo in etiquetas:
            assert 'src="' in atributos or 'type="application/json"' in atributos
            if 'src="' in atributos:
                assert cuerpo == ''
        assert not re.search(r'\son[a-z]+\s*=', html)
        assert 'javascript:' not in html


def test_datos_en_json_con_escape_de_menor_mayor_y_ampersand(pp):
    datos = {'t': '</script><img src=x onerror=alert(1)> & más', 'u': 'a b'}
    html = pp.render_page('inicio', modo='exportado', generado='x', datos=datos)
    m = re.search(r'<script type="application/json" id="panel-data">(.*?)</script>', html, re.S)
    bruto = m.group(1)
    assert '<' not in bruto and '>' not in bruto and '&' not in bruto and ' ' not in bruto
    assert json.loads(bruto) == {**datos, 'chartjs_disponible': True}
    assert '<img src=x' not in html


def test_csp_solo_en_exportado_con_la_politica_decidida_en_t03(pp):
    exportado = pp.render_page('inicio', modo='exportado', generado='x', datos={})
    csp = re.search(r'<meta http-equiv="Content-Security-Policy" content="([^"]+)">', exportado).group(1)
    assert csp == "default-src 'none'; script-src 'self' file:; style-src 'self' 'unsafe-inline'; img-src data:"
    assert 'unsafe-eval' not in csp and "script-src 'self' file:" in csp and 'unsafe-inline' not in csp.split('style-src')[0]
    servido = pp.render_page('inicio', modo='servido', generado='x', datos={})
    assert 'Content-Security-Policy' not in servido


def test_cabecera_de_modo(pp):
    exportado = pp.render_page('inicio', modo='exportado', generado='2026-10-15 10:00 UTC', datos={})
    assert 'Instantánea' in exportado and '2026-10-15 10:00 UTC' in exportado
    servido = pp.render_page('inicio', modo='servido', generado='2026-10-15 10:00 UTC', datos={})
    assert 'Servido' in servido and 'Instantánea' not in servido
    with pytest.raises(ValueError):
        pp.render_page('inicio', modo='otro', generado='x', datos={})
    with pytest.raises(ValueError):
        pp.render_page('no-existe', modo='servido', generado='x', datos={})


def test_cuerpo_se_inserta_tal_cual_y_el_titulo_se_escapa(pp):
    html = pp.render_page('catalogo', modo='servido', generado='x', datos={}, cuerpo='<p id="mi-cuerpo">hola</p>')
    assert '<p id="mi-cuerpo">hola</p>' in html
    assert '<h1>Catálogo</h1>' in html


def test_scripts_son_ficheros_en_orden_y_chart_solo_si_esta_disponible(pp):
    con = pp.render_page('inicio', modo='exportado', generado='x', datos={}, chart_ok=True)
    srcs = re.findall(r'<script src="([^"]+)"', con)
    assert srcs == ['vendor/chart.js/chart.umd.min.js', 'assets/panel-core.js', 'assets/panel-charts.js']
    sin = pp.render_page('inicio', modo='exportado', generado='x', datos={}, chart_ok=False)
    assert re.findall(r'<script src="([^"]+)"', sin) == ['assets/panel-core.js', 'assets/panel-charts.js']
    def dato(h):
        return json.loads(re.search(r'id="panel-data">(.*?)</script>', h, re.S).group(1))['chartjs_disponible']
    assert dato(con) is True and dato(sin) is False


def test_css_con_foco_visible_y_sin_elementos_fijos_que_lo_tapen():
    css = (ASSETS / 'panel.css').read_text(encoding='utf-8')
    assert ':focus-visible' in css
    sin_comentarios = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    assert not re.search(r'position\s*:\s*(fixed|sticky)', sin_comentarios)
    assert 'scroll-padding' in sin_comentarios
    assert 'http://' not in css and 'https://' not in css and '@import' not in css and 'url(' not in css


def test_assets_sin_innerhtml_ni_red():
    for nombre in ('panel-core.js',):
        js = (ASSETS / nombre).read_text(encoding='utf-8')
        assert 'innerHTML' not in js and 'insertAdjacentHTML' not in js and 'eval(' not in js
        assert 'fetch(' not in js and 'XMLHttpRequest' not in js and 'http://' not in js


def _node():
    node = shutil.which('node')
    if not node:
        pytest.skip('Node no disponible para el arnés de panel-core.js')
    return node


HARNESS_MENU = r'''
const assert = require('node:assert/strict');
class El {
  constructor(){this.attrs={};this.listeners={};this.hidden=false;this.focused=false;this.classList={_s:new Set(),add:(c)=>this.classList._s.add(c),remove:(c)=>this.classList._s.delete(c),contains:(c)=>this.classList._s.has(c)};}
  setAttribute(k,v){this.attrs[k]=String(v);}
  getAttribute(k){return this.attrs[k]===undefined?null:this.attrs[k];}
  addEventListener(t,f){this.listeners[t]=f;}
  focus(){this.focused=true;}
  contains(o){return o===this;}
}
const boton=new El(), nav=new El();
boton.hidden=true; nav.hidden=false;
const docListeners={};
let estrecho=true;
global.window=global;
global.matchMedia=()=>({matches:estrecho,addEventListener(){}});
global.document={getElementById(id){return id==='menu-toggle'?boton:id==='panel-nav'?nav:null;},
  querySelector(){return null;},querySelectorAll(){return [];},addEventListener(t,f){docListeners[t]=f;},activeElement:null,
  readyState:'complete'};
require(CORE);
global.PanelCore.iniciarMenu();
'''


def _correr(tmp_path, cuerpo):
    programa = HARNESS_MENU.replace('CORE', json.dumps(str(ASSETS / 'panel-core.js'))) + '\n' + cuerpo
    fuente = tmp_path / 'menu.cjs'
    fuente.write_text(programa, encoding='utf8')
    r = subprocess.run([_node(), str(fuente)], capture_output=True, text=True, encoding='utf8',
                       errors='replace', timeout=15)
    assert r.returncode == 0, r.stdout + r.stderr


def test_menu_estrecho_se_pliega_y_el_boton_lo_abre_y_cierra(tmp_path):
    _correr(tmp_path, '''
assert.equal(boton.hidden,false,'el botón aparece en pantallas estrechas');
assert.equal(nav.hidden,true,'el menú arranca plegado');
assert.equal(boton.getAttribute('aria-expanded'),'false');
boton.listeners.click();
assert.equal(nav.hidden,false);assert.equal(boton.getAttribute('aria-expanded'),'true');
boton.listeners.click();
assert.equal(nav.hidden,true);assert.equal(boton.getAttribute('aria-expanded'),'false');
''')


def test_escape_cierra_el_menu_y_devuelve_el_foco_al_boton(tmp_path):
    _correr(tmp_path, '''
boton.listeners.click();
assert.equal(nav.hidden,false);
boton.focused=false;
docListeners.keydown({key:'Escape',preventDefault(){}});
assert.equal(nav.hidden,true);assert.equal(boton.getAttribute('aria-expanded'),'false');
assert.equal(boton.focused,true,'el foco vuelve al botón');
''')


def test_escape_con_menu_cerrado_no_roba_el_foco(tmp_path):
    _correr(tmp_path, '''
docListeners.keydown({key:'Escape',preventDefault(){}});
assert.equal(boton.focused,false);
''')


def test_pantalla_ancha_deja_el_menu_visible_y_sin_boton(tmp_path):
    programa = HARNESS_MENU.replace('estrecho=true', 'estrecho=false').replace(
        'CORE', json.dumps(str(ASSETS / 'panel-core.js'))) + '''
assert.equal(boton.hidden,true);assert.equal(nav.hidden,false);
'''
    fuente = tmp_path / 'ancho.cjs'
    fuente.write_text(programa, encoding='utf8')
    r = subprocess.run([_node(), str(fuente)], capture_output=True, text=True, encoding='utf8', errors='replace', timeout=15)
    assert r.returncode == 0, r.stdout + r.stderr
