"""T-18: página Inicio (estados de spec, avance global, coste real frente al estimado).

Dos capas: el HTML que sale del exportador/servidor (esqueleto, scripts, datos incrustados) y el JS de la página
ejecutado en Node con un DOM falso, alimentado con la cartera REAL que produce `panel_data.cartera()` sobre la
fixture de T-01 y comparado con las salidas de `build_dashboard.py --json` y `progress-report.py`.
"""
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest

from panel_render import pagina
from test_panel_contract_golden import materializar
from test_panel_live_ui import inventory, panel  # noqa: F401  (fixtures)

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'skills/plugin-panel/assets'
SCRIPTS = ROOT / 'skills/plugin-panel/scripts'
DASHBOARD = ROOT / 'skills/roadmap-dashboard/scripts/build_dashboard.py'
PROGRESS = ROOT / 'agent-kits/shared/progress-report.py'
IDS_INICIO = ('cartera-estado', 'grafico-estados', 'avance-global', 'avance-fuera-de-tope', 'coste-cartera',
              'coste-procedencia')


def _panel_data():
    spec = importlib.util.spec_from_file_location('panel_data_inicio', SCRIPTS / 'panel_data.py')
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope='module')
def proyecto(tmp_path_factory):
    copia = materializar(tmp_path_factory.mktemp('inicio'))
    destino = copia / 'proyecto'
    (destino / 'docs').mkdir(parents=True)
    shutil.copytree(copia / 'roadmap', destino / 'docs/roadmap')
    return destino


@pytest.fixture(scope='module')
def cartera(proyecto):
    return _panel_data().cartera(proyecto)


@pytest.fixture(scope='module')
def esperado(proyecto):
    """Cifras de referencia obtenidas EJECUTANDO los scripts, no copiadas."""
    salida = subprocess.run([sys.executable, str(DASHBOARD), '--root', str(proyecto / 'docs/roadmap'), '--json'],
                            capture_output=True, text=True, encoding='utf8', check=True).stdout
    iniciativas = json.loads(salida)
    estados = {e: sum(1 for r in iniciativas if r['spec_estado'] == e)
               for e in ('borrador', 'aprobada', 'implementada', 'obsoleta')}
    n = m = 0
    for carpeta in sorted((proyecto / 'docs/roadmap').iterdir()):
        ledger = carpeta / 'tasks.md'
        if not ledger.is_file() or ledger.stat().st_size > 256 * 1024:
            continue
        r = json.loads(subprocess.run([sys.executable, str(PROGRESS), 'line', str(ledger), '--json'],
                                      capture_output=True, text=True, encoding='utf8', check=True).stdout)
        n += r['completadas']; m += r['total']
    return {'estados': estados, 'completadas': n, 'total': m, 'pct': round(100 * n / m),
            'medidos': sum(r['medidos'] for r in iniciativas), 'estimados': sum(r['estimados'] for r in iniciativas),
            'desconocidos': sum(r['generacion_otros'] for r in iniciativas), 'iniciativas': len(iniciativas)}


# --- HTML: esqueleto, scripts y datos incrustados -------------------------------------------------------------

def test_inicio_exportado_lleva_el_esqueleto_los_scripts_en_orden_y_la_cartera_incrustada(panel, inventory, cartera):
    pp = panel._load_pages()
    cuerpos = panel.cuerpos_paginas(inventory)
    html = pp.render_page('inicio', modo='exportado', generado='2026-10-15 10:00 UTC', cuerpo=cuerpos['inicio'],
                          datos=pp.datos_de_pagina('inicio', inventory, modo='exportado', cartera=cartera),
                          scripts_omitidos=('panel-review.js',))
    for ident in IDS_INICIO:
        assert f'id="{ident}"' in html, ident
    orden = [m.group(1) for m in re.finditer(r'<script[^>]*\ssrc="([^"]+)"', html)]
    assert orden == ['vendor/chart.js/chart.umd.min.js', 'assets/panel-core.js', 'assets/panel-charts.js',
                     'assets/page-cartera.js', 'assets/page-inicio.js']
    bruto = re.search(r'<script type="application/json" id="panel-data">(.*?)</script>', html, re.S).group(1)
    assert '<' not in bruto and '>' not in bruto and '&' not in bruto
    datos = json.loads(bruto)
    assert datos['modo'] == 'exportado' and datos['cartera'] == cartera
    assert 'operations' not in html and not re.search(r'<script(?![^>]*\ssrc=)(?![^>]*application/json)[^>]*>', html)


def test_inicio_servido_no_incrusta_la_cartera_y_conserva_el_progreso_vivo(panel, inventory, cartera):
    pp = panel._load_pages()
    cuerpos = panel.cuerpos_paginas(inventory, live=True)
    datos = pp.datos_de_pagina('inicio', inventory, modo='servido', cartera=cartera)
    assert datos['modo'] == 'servido' and 'cartera' not in datos       # el servido la pide a api/cartera
    html = pp.render_page('inicio', modo='servido', generado='x', cuerpo=cuerpos['inicio'], datos=datos, nonce='n1')
    assert 'id="operations"' in html and 'assets/page-inicio.js' in html and 'assets/panel-live.js' in html
    assert all(f'nonce="n1"' in e for e in re.findall(r'<script\b[^>]*>', html))


@pytest.mark.parametrize('slug', ['catalogo', 'diagnostico', 'plan', 'agentes', 'memoria'])
def test_la_cartera_solo_viaja_a_inicio_e_iniciativas(panel, inventory, cartera, slug):
    pp = panel._load_pages()
    assert 'cartera' not in pp.datos_de_pagina(slug, inventory, modo='exportado', cartera=cartera)


def test_exportar_sitio_copia_los_js_de_cartera_e_inicio_y_los_declara_en_el_manifiesto(panel, inventory, cartera, tmp_path):
    pp = panel._load_pages()
    escritos, _ = pp.exportar_sitio(tmp_path / 'salida', inventory, cartera=cartera, cuerpos=panel.cuerpos_paginas(inventory))
    assert {'assets/page-cartera.js', 'assets/page-inicio.js'} <= set(escritos)
    html = (tmp_path / 'salida/index.html').read_text(encoding='utf8')
    assert json.loads(re.search(r'id="panel-data">(.*?)</script>', html, re.S).group(1))['cartera'] == cartera


def test_cli_export_con_project_incrusta_la_cartera_anonimizada_y_sin_project_no_la_incluye(panel, tmp_path):
    spec = importlib.util.spec_from_file_location('build_panel_inicio', SCRIPTS / 'build_panel.py')
    build = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(build)
    bundle = ROOT / 'tests/fixtures/panel-redesign/bundle'
    proyecto = tmp_path / 'mi-proyecto'
    carpeta = proyecto / 'docs/roadmap/2026-10-20-ruta'
    carpeta.mkdir(parents=True)
    (carpeta / 'spec.md').write_text('---\nestado: aprobada\n---\n# Plan en ' + str(proyecto) + '/docs\n', encoding='utf8')
    assert build.main(['--root', str(bundle), '--project', str(proyecto), '--export', str(tmp_path / 'con')]) == 0
    html = (tmp_path / 'con/index.html').read_text(encoding='utf8')
    datos = json.loads(re.search(r'id="panel-data">(.*?)</script>', html, re.S).group(1))
    assert datos['cartera']['status'] == 'ok' and len(datos['cartera']['iniciativas']) == 1
    titulo = datos['cartera']['iniciativas'][0]['titulo']
    assert titulo.startswith('Plan en ') and str(proyecto) not in html and str(proyecto).replace(chr(92), '/') not in html
    assert str(proyecto) not in titulo
    assert build.main(['--root', str(bundle), '--export', str(tmp_path / 'sin')]) == 0
    sin = (tmp_path / 'sin/index.html').read_text(encoding='utf8')
    assert 'cartera' not in json.loads(re.search(r'id="panel-data">(.*?)</script>', sin, re.S).group(1))


# --- JS de la página en Node ----------------------------------------------------------------------------------

HARNESS = r'''
const assert = require('node:assert/strict');
class El {
  constructor(tag){this.tagName=String(tag).toLowerCase();this.children=[];this.attrs={};this.className='';this.dataset={};this._text='';this.hidden=false;this.events={};this.disabled=false;}
  set textContent(v){this._text=String(v);this.children=[];}
  get textContent(){return this._text+this.children.map(c=>c.textContent).join('');}
  set innerHTML(v){throw new Error('Asignación de HTML no confiable');}
  append(...ns){for(const n of ns)this.children.push(typeof n==='string'?Object.assign(new El('#text'),{_text:n}):n);}
  appendChild(n){this.append(n);return n;}
  replaceChildren(...ns){this.children=[];this._text='';this.append(...ns);}
  setAttribute(k,v){this.attrs[k]=String(v);}
  getAttribute(k){return this.attrs[k]===undefined?null:this.attrs[k];}
  addEventListener(t,f){(this.events[t]=this.events[t]||[]).push(f);}
  getContext(){return {};}
  focus(){global.document.activeElement=this;}
}
const walk=(el,f,out=[])=>{if(f(el))out.push(el);for(const c of el.children)walk(c,f,out);return out;};
const tag=(el,t)=>walk(el,n=>n.tagName===t);
const celdas=(fila)=>fila.children.map(c=>c.textContent);
const filas=(el)=>tag(tag(el,'tbody')[0],'tr').map(celdas);
global.window=global;
global.getComputedStyle=()=>({getPropertyValue:()=>''});
const ids={};
for(const id of IDS)ids[id]=new El('div');
ids['panel-data']=new El('script');
const docEvents={};
global.document={hidden:false,createElement:t=>new El(t),documentElement:new El('html'),getElementById:id=>ids[id]||null,
  addEventListener(t,f){docEvents[t]=f;},readyState:'complete',querySelector:()=>null,querySelectorAll:()=>[]};
let seq=0;const timers=new Map();
global.setTimeout=(f,d)=>{timers.set(++seq,{f,d});return seq;};
global.clearTimeout=id=>timers.delete(id);
class Abort{constructor(){this.signal={aborted:false};}abort(){this.signal.aborted=true;}}
global.AbortController=Abort;
const requests=[];
global.fetch=(url,options)=>new Promise((resolve,reject)=>requests.push({url,options,resolve,reject}));
const settle=async()=>{for(let i=0;i<12;i++)await Promise.resolve();};
const respond=async(data,i=requests.length-1)=>{requests[i].resolve({ok:true,json:async()=>data});await settle();};
const fire=(delay)=>{const f=[...timers].find(([,v])=>v.d===delay);assert.ok(f,'timer '+delay);timers.delete(f[0]);f[1].f();};
const pendientes=(delay)=>[...timers.values()].filter(t=>t.d===delay).length;
const creados=[];
class FakeChart{constructor(c,config){this.config=config;creados.push(this);}destroy(){}}
FakeChart.defaults={color:'',borderColor:'',font:{}};
global.Chart=FakeChart;
const ponerDatos=(d)=>{ids['panel-data'].textContent=JSON.stringify(d);};
'''


def _programa(cuerpo, *, datos, extra=''):
    fuentes = ''.join((ASSETS / n).read_text(encoding='utf8')
                      for n in ('panel-core.js', 'panel-charts.js', 'page-cartera.js', 'page-inicio.js'))
    return (HARNESS.replace('IDS', json.dumps(list(IDS_INICIO))) + extra + '\nponerDatos(' + json.dumps(datos) + ');\n'
            + fuentes + '\n(async()=>{' + cuerpo + '})().catch(e=>{console.error(e);process.exitCode=1;});')


def _correr(tmp_path, cuerpo, *, datos, extra=''):
    node = shutil.which('node')
    if not node:
        pytest.skip('Node no disponible para el arnés de page-inicio.js')
    fuente = tmp_path / 'inicio.cjs'
    fuente.write_text(_programa(cuerpo, datos=datos, extra=extra), encoding='utf8')
    r = subprocess.run([node, str(fuente)], capture_output=True, text=True, encoding='utf8', errors='replace', timeout=30)
    assert r.returncode == 0, r.stdout + r.stderr


def _exportado(cartera, **extra):
    return {'pagina': 'inicio', 'modo': 'exportado', 'chartjs_disponible': True, 'cartera': cartera, **extra}


def test_ca01_estados_iguales_a_dashboard_json_y_la_ilegible_aparte(tmp_path, cartera, esperado):
    _correr(tmp_path, '''
const fig=ids['grafico-estados'].children[0];
const f=filas(fig);
const etiquetas=f.map(r=>r[0]);
assert.deepEqual(etiquetas,['Borrador','Aprobada','Implementada','Obsoleta','Ilegible','Sin spec','Estado no reconocido']);
const por=Object.fromEntries(f.map(r=>[r[0],r[1]]));
assert.equal(por.Borrador,String(ESP.borrador));assert.equal(por.Aprobada,String(ESP.aprobada));
assert.equal(por.Implementada,String(ESP.implementada));assert.equal(por.Obsoleta,String(ESP.obsoleta));
assert.equal(por.Ilegible,'1','la iniciativa ilegible va en su propia fila');
assert.equal(f.reduce((a,r)=>a+Number(r[1]),0),TOTAL,'cada iniciativa cuenta en UNA sola fila');
assert.equal(creados.length,1);assert.deepEqual(creados[0].config.data.datasets[0].data,f.map(r=>Number(r[1])));
'''.replace('ESP', json.dumps(esperado['estados'])).replace('TOTAL', str(esperado['iniciativas'])), datos=_exportado(cartera))


def test_ca02_avance_global_igual_a_la_suma_de_progress_report_y_el_ledger_grande_va_aparte(tmp_path, cartera, esperado):
    _correr(tmp_path, '''
assert.equal(ids['avance-global'].textContent.startsWith(EXP),true,ids['avance-global'].textContent);
const aparte=ids['avance-fuera-de-tope'].textContent;
assert.match(aparte,/fuera del tope de lectura/);assert.ok(aparte.includes('2026-01-14-epsilon'));
assert.ok(!ids['avance-global'].textContent.includes('2026-01-14-epsilon'));
'''.replace('EXP', json.dumps(f"{esperado['completadas']} de {esperado['total']} tareas completadas ({esperado['pct']} %)")),
            datos=_exportado(cartera))


def test_ca03_sin_estimacion_no_suma_cero_y_la_procedencia_se_cuenta_por_tipo(tmp_path, cartera, esperado):
    _correr(tmp_path, '''
const coste=ids['coste-cartera'].textContent;
assert.match(coste,/Coste real/);assert.match(coste,/Coste estimado/);
assert.match(coste,/dato en \\d+ de 6 iniciativas/);
assert.ok(!/ 0 €/.test(coste),'un total ausente no se pinta como 0 €');
assert.match(coste,/no suma 0/);
assert.equal(ids['coste-procedencia'].textContent,'procedencia: '+MED+' medidos · '+EST+' estimados · '+DES+' desconocidos');
'''.replace('MED', str(esperado['medidos'])).replace('EST', str(esperado['estimados'])).replace('DES', str(esperado['desconocidos'])),
            datos=_exportado(cartera))


def test_sin_ninguna_estimacion_el_coste_estimado_dice_sin_datos(tmp_path, cartera):
    sin = json.loads(json.dumps(cartera))
    for fila in sin['iniciativas']:
        fila['coste'].update(est_eur=None, est_texto=None)
    sin['totales']['coste'].update(est_eur=None, est_n=0)
    _correr(tmp_path, '''
const dd=walk(ids['coste-cartera'],n=>n.tagName==='dd').map(n=>n.textContent);
assert.equal(dd[1],'sin datos');assert.notEqual(dd[0],'sin datos');
''', datos=_exportado(sin))


def test_estados_sin_datos_cuando_la_cartera_no_se_pudo_leer(tmp_path):
    _correr(tmp_path, '''
assert.match(ids['cartera-estado'].textContent,/Sin datos|no disponible/);
const fig=ids['grafico-estados'].children[0];
assert.equal(creados.length,0,'sin ningún valor no se dibuja el gráfico');
assert.ok(filas(fig).every(r=>r[1]==='sin datos'));
assert.match(ids['avance-global'].textContent,/Sin datos/);
assert.ok(!/\\b0\\b/.test(ids['avance-global'].textContent));
''', datos=_exportado({'version': 1, 'source': 'roadmap_cartera', 'status': 'unavailable', 'complete': False,
                       'observed_at': '2026-10-15T10:00:00Z', 'issues': [{'status': 'reader_unavailable'}],
                       'iniciativas': [], 'totales': {'iniciativas': 0, 'por_estado': {}, 'tareas': None,
                                                       'fuera_de_tope': [], 'coste': {'real_eur': None, 'real_n': 0, 'est_eur': None, 'est_n': 0},
                                                       'procedencia': {'medidos': 0, 'estimados': 0, 'desconocidos': 0}}}))


def test_exportado_sin_cartera_o_con_una_invalida_lo_dice_y_no_inventa_cifras(tmp_path, cartera):
    for datos, mensaje in (({'pagina': 'inicio', 'modo': 'exportado', 'chartjs_disponible': True}, 'no incluye la cartera'),
                           (_exportado({**cartera, 'version': 2}), 'No se pudo leer la cartera')):
        _correr(tmp_path, '''
assert.ok(ids['cartera-estado'].textContent.includes(MENSAJE),ids['cartera-estado'].textContent);'''.replace('MENSAJE', json.dumps(mensaje)) + '''
assert.match(ids['avance-global'].textContent,/Sin datos/);
assert.equal(creados.length,0);
''', datos=datos)


def test_el_texto_del_repo_entra_por_textcontent(tmp_path, cartera):
    hostil = json.loads(json.dumps(cartera))
    hostil['totales']['fuera_de_tope'][0]['slug'] = '<img src=x onerror=alert(1)>'
    _correr(tmp_path, '''
assert.ok(ids['avance-fuera-de-tope'].textContent.includes('<img src=x onerror=alert(1)>'));
''', datos=_exportado(hostil))


def test_cartera_vacia_dice_que_el_roadmap_no_tiene_iniciativas(tmp_path):
    vacia = {'version': 1, 'source': 'roadmap_cartera', 'status': 'ok', 'complete': True,
             'observed_at': '2026-10-15T10:00:00Z', 'issues': [], 'iniciativas': [],
             'totales': {'iniciativas': 0, 'por_estado': {k: 0 for k in ('borrador', 'aprobada', 'implementada', 'obsoleta',
                                                                         'ilegible', 'sin_spec', 'no_reconocido')},
                         'tareas': None, 'fuera_de_tope': [],
                         'coste': {'real_eur': None, 'real_n': 0, 'est_eur': None, 'est_n': 0},
                         'procedencia': {'medidos': 0, 'estimados': 0, 'desconocidos': 0}}}
    _correr(tmp_path, '''
assert.match(ids['cartera-estado'].textContent,/no tiene iniciativas/);
assert.match(ids['avance-global'].textContent,/Sin datos: ningún ledger legible/);
''', datos=_exportado(vacia))


SERVIDO = {'pagina': 'inicio', 'modo': 'servido', 'chartjs_disponible': True}


def test_servido_pide_api_cartera_con_ruta_relativa_sin_credenciales_y_pinta_lo_recibido(tmp_path, cartera, esperado):
    _correr(tmp_path, '''
assert.equal(requests.length,1);assert.equal(requests[0].url,'api/cartera');
assert.equal(requests[0].options.credentials,'omit');assert.equal(requests[0].options.cache,'no-store');
assert.ok(requests[0].options.signal);
await respond(DATOS);
assert.ok(ids['avance-global'].textContent.startsWith(EXP));
assert.equal(pendientes(10000),1,'refresco programado cada 10 s');
'''.replace('DATOS', json.dumps(cartera)).replace('EXP', json.dumps(f"{esperado['completadas']} de {esperado['total']}")),
            datos=SERVIDO)


def test_servido_un_fallo_conserva_la_ultima_vista_y_su_fecha_y_no_solapa_peticiones(tmp_path, cartera):
    _correr(tmp_path, '''
await respond(DATOS);
const antes=ids['avance-global'].textContent;
fire(10000);assert.equal(requests.length,2);
fire(4000);assert.equal(requests[1].options.signal.aborted,true);
requests[1].reject(Error('PRIVADO'));await settle();
assert.equal(ids['avance-global'].textContent,antes);
assert.match(ids['cartera-estado'].textContent,/Se conserva la última vista/);
assert.ok(ids['cartera-estado'].textContent.includes(OBS));
assert.ok(!ids['cartera-estado'].textContent.includes('PRIVADO'));
assert.equal(pendientes(10000),1);
'''.replace('DATOS', json.dumps(cartera)).replace('OBS', json.dumps(cartera['observed_at'])), datos=SERVIDO)


def test_servido_respuesta_invalida_o_no_disponible_sin_vista_previa_dice_sin_datos(tmp_path, cartera):
    _correr(tmp_path, '''
await respond({...DATOS,version:2});
assert.match(ids['cartera-estado'].textContent,/No se pudo leer la cartera/);
assert.match(ids['avance-global'].textContent,/Sin datos/);
assert.equal(creados.length,0);
'''.replace('DATOS', json.dumps(cartera)), datos=SERVIDO)


def test_servido_pausa_el_refresco_con_la_pestana_oculta_y_lo_reanuda(tmp_path, cartera):
    _correr(tmp_path, '''
await respond(DATOS);
document.hidden=true;docEvents.visibilitychange();
assert.equal(pendientes(10000),0);assert.equal(requests.length,1);
document.hidden=false;docEvents.visibilitychange();assert.equal(requests.length,2);
'''.replace('DATOS', json.dumps(cartera)), datos=SERVIDO)


def test_servido_una_pestana_que_vuelve_a_ser_visible_no_solapa_una_peticion_en_vuelo(tmp_path, cartera):
    _correr(tmp_path, '''
await respond(DATOS);
fire(10000);assert.equal(requests.length,2);
document.hidden=false;docEvents.visibilitychange();
assert.equal(requests.length,2,'con una lectura en vuelo no se abre otra');
'''.replace('DATOS', json.dumps(cartera)), datos=SERVIDO)


def test_servido_un_unavailable_con_vista_previa_no_la_pisa_y_avisa(tmp_path, cartera):
    caida = {'version': 1, 'source': 'roadmap_cartera', 'status': 'unavailable', 'complete': False,
             'observed_at': '2026-10-15T10:00:30Z', 'issues': [{'status': 'reader_unavailable'}], 'iniciativas': [],
             'totales': {'iniciativas': 0, 'por_estado': {}, 'tareas': None, 'fuera_de_tope': [],
                         'coste': {'real_eur': None, 'real_n': 0, 'est_eur': None, 'est_n': 0},
                         'procedencia': {'medidos': 0, 'estimados': 0, 'desconocidos': 0}}}
    _correr(tmp_path, '''
await respond(DATOS);
const antes=ids['avance-global'].textContent;assert.ok(!/Sin datos/.test(antes));
fire(10000);await respond(CAIDA);
assert.equal(ids['avance-global'].textContent,antes,'la vista previa no se pisa con una cartera caída');
assert.match(ids['cartera-estado'].textContent,/Se conserva la última vista/);
'''.replace('DATOS', json.dumps(cartera)).replace('CAIDA', json.dumps(caida)), datos=SERVIDO)


def test_el_grafico_no_se_redibuja_si_las_cifras_no_cambian(tmp_path, cartera):
    _correr(tmp_path, '''
await respond(DATOS);const primero=ids['grafico-estados'].children[0];
fire(10000);await respond({...DATOS,observed_at:'2026-10-15T10:05:00Z'});
assert.equal(ids['grafico-estados'].children[0],primero,'mismas cifras: se conserva el gráfico');
assert.equal(creados.length,1);
assert.ok(ids['cartera-estado'].textContent.includes('10:05'));
'''.replace('DATOS', json.dumps(cartera)), datos=SERVIDO)


def test_sin_chartjs_la_pagina_sigue_entera_con_la_tabla_y_el_aviso(tmp_path, cartera):
    _correr(tmp_path, '''
assert.equal(creados.length,0);
const fig=ids['grafico-estados'].children[0];
assert.equal(tag(fig,'table').length,1);assert.match(fig.textContent,/Chart\\.js no está disponible/);
assert.ok(ids['avance-global'].textContent.includes(' tareas completadas'));
''', datos=_exportado(cartera, chartjs_disponible=False))


def test_el_js_de_inicio_no_usa_innerhtml_ni_red_ajena_ni_eval():
    for nombre in ('page-cartera.js', 'page-inicio.js'):
        fuente = (ASSETS / nombre).read_text(encoding='utf8')
        assert not re.search(r'innerHTML|outerHTML|insertAdjacentHTML|document\.write|eval\(|new Function|XMLHttpRequest|WebSocket|importScripts|localStorage|sessionStorage', fuente), nombre
        assert re.findall(r"fetch\(\s*'([^']+)'", fuente) in ([], ['api/cartera'])
