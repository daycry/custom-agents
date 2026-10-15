"""T-19 y T-20: página Iniciativas (kanban de solo lectura, alertas en texto, navegación a Plan y gráficos).

Misma estructura que `test_panel_inicio_ui.py`: HTML del exportador/servidor y JS de la página en Node con un
DOM falso, alimentado con la cartera REAL de `panel_data.cartera()` sobre la fixture de T-01.
"""
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

import pytest

from test_panel_inicio_ui import (ASSETS, HARNESS, cartera, esperado, inventory, panel, proyecto)  # noqa: F401

IDS = ('cartera-estado', 'kanban-iniciativas', 'grafico-horas', 'grafico-coste')
ESTADOS = ('borrador', 'aprobada', 'implementada', 'obsoleta')


def _html(panel, inventory, cartera, modo='exportado'):
    pp = panel._load_pages()
    cuerpos = panel.cuerpos_paginas(inventory, live=modo == 'servido')
    return pp.render_page('iniciativas', modo=modo, generado='2026-10-15 10:00 UTC', cuerpo=cuerpos['iniciativas'],
                          datos=pp.datos_de_pagina('iniciativas', inventory, modo=modo, cartera=cartera),
                          nonce='n1' if modo == 'servido' else None, scripts_omitidos=('panel-review.js',))


def test_iniciativas_exportado_lleva_esqueleto_scripts_en_orden_y_cartera(panel, inventory, cartera):
    html = _html(panel, inventory, cartera)
    for ident in IDS:
        assert f'id="{ident}"' in html, ident
    orden = [m.group(1) for m in re.finditer(r'<script[^>]*\ssrc="([^"]+)"', html)]
    assert orden == ['vendor/chart.js/chart.umd.min.js', 'assets/panel-core.js', 'assets/panel-charts.js',
                     'assets/page-cartera.js', 'assets/page-iniciativas.js']
    bruto = re.search(r'<script type="application/json" id="panel-data">(.*?)</script>', html, re.S).group(1)
    assert json.loads(bruto)['cartera'] == cartera and '<' not in bruto
    principal = re.search(r'<main\b.*</main>', html, re.S).group(0)      # el menú de la cabecera sí lleva un botón
    assert 'draggable' not in html and not re.search(r'<(button|input|select|textarea|form)\b', principal)


def test_iniciativas_servido_no_incrusta_cartera_y_lleva_nonce(panel, inventory, cartera):
    html = _html(panel, inventory, cartera, 'servido')
    bruto = re.search(r'id="panel-data">(.*?)</script>', html, re.S).group(1)
    assert 'cartera' not in json.loads(bruto) and json.loads(bruto)['modo'] == 'servido'
    assert all('nonce="n1"' in e for e in re.findall(r'<script\b[^>]*>', html))
    assert 'assets/page-iniciativas.js' in html


def test_exportar_sitio_copia_page_iniciativas(panel, inventory, cartera, tmp_path):
    escritos, _ = panel._load_pages().exportar_sitio(tmp_path / 's', inventory, cartera=cartera,
                                                     cuerpos=panel.cuerpos_paginas(inventory))
    assert 'assets/page-iniciativas.js' in escritos


def _correr(tmp_path, cuerpo, *, datos):
    node = shutil.which('node')
    if not node:
        pytest.skip('Node no disponible para el arnés de page-iniciativas.js')
    fuentes = ''.join((ASSETS / n).read_text(encoding='utf8')
                      for n in ('panel-core.js', 'panel-charts.js', 'page-cartera.js', 'page-iniciativas.js'))
    programa = (HARNESS.replace('IDS', json.dumps(list(IDS))) + '\nponerDatos(' + json.dumps(datos) + ');\n' + fuentes
                + '\n(async()=>{' + cuerpo + '})().catch(e=>{console.error(e);process.exitCode=1;});')
    fuente = tmp_path / 'iniciativas.cjs'
    fuente.write_text(programa, encoding='utf8')
    r = subprocess.run([node, str(fuente)], capture_output=True, text=True, encoding='utf8', errors='replace', timeout=30)
    assert r.returncode == 0, r.stdout + r.stderr


def _exportado(cartera, **extra):
    return {'pagina': 'iniciativas', 'modo': 'exportado', 'chartjs_disponible': True, 'cartera': cartera, **extra}


SERVIDO = {'pagina': 'iniciativas', 'modo': 'servido', 'chartjs_disponible': True}

LIBRES = '''
const columnas=()=>walk(ids['kanban-iniciativas'],n=>n.className.split(' ').includes('columna'));
const tarjetas=(col)=>walk(col,n=>n.tagName==='article');
const porTitulo=()=>Object.fromEntries(columnas().map(c=>[tag(c,'h2')[0].textContent,tarjetas(c)]));
const tarjetaDe=(slug)=>walk(ids['kanban-iniciativas'],n=>n.tagName==='article'&&n.textContent.includes(slug))[0];
'''


def test_kanban_una_columna_por_estado_y_una_tarjeta_por_iniciativa(tmp_path, cartera, esperado):
    _correr(tmp_path, LIBRES + '''
const cols=porTitulo();
for(const [estado,n] of Object.entries(ESP)){assert.equal(cols[ETIQ[estado]+' ('+n+')'].length,n,estado);}
assert.equal(columnas().length,4+EXTRA,'las cuatro columnas de estado y solo las extra con tarjetas');
assert.equal(walk(ids['kanban-iniciativas'],n=>n.tagName==='article').length,TOTAL);
assert.ok(tarjetaDe('2026-01-13-delta').textContent.includes('Ilegible'),'la ilegible va en su propia columna');
assert.equal(columnas().filter(c=>tag(c,'h2')[0].textContent.startsWith('Ilegible')).length,1);
'''.replace('ESP', json.dumps(esperado['estados'])).replace('ETIQ', json.dumps(
        {'borrador': 'Borrador', 'aprobada': 'Aprobada', 'implementada': 'Implementada', 'obsoleta': 'Obsoleta'}))
            .replace('EXTRA', '2').replace('TOTAL', str(esperado['iniciativas'])), datos=_exportado(cartera))


def test_la_tarjeta_muestra_slug_fecha_tareas_horas_coste_y_procedencia(tmp_path, cartera):
    _correr(tmp_path, LIBRES + '''
const t=tarjetaDe('2026-01-10-alfa').textContent;
assert.match(t,/2026-01-10-alfa/);assert.match(t,/2026-01-10/);
assert.match(t,/1\\/2 tareas \\(50 %\\)/);
assert.match(t,/Horas.*real 1,90 h.*estimado 2,50 h/);
assert.match(t,/Coste: real sin datos · estimado 1\\.300 €/);
assert.match(t,/procedencia: 3 medidos · 0 estimados · 0 desconocidos/);
const zeta=tarjetaDe('2026-01-15-zeta').textContent;
assert.match(zeta,/Coste: real 0,40 € \\(parcial\\) · estimado 200 €/);
const beta=tarjetaDe('2026-01-11-beta').textContent;
assert.match(beta,/Tareas: sin datos/);assert.match(beta,/Horas.*real sin datos.*estimado sin datos/);
assert.ok(!/ 0 h|0 €/.test(beta),'lo ausente no se pinta como 0');
''', datos=_exportado(cartera))


def test_cada_alerta_aparece_con_su_texto(tmp_path, cartera):
    sucia = json.loads(json.dumps(cartera))
    fila = next(f for f in sucia['iniciativas'] if f['slug'] == '2026-01-12-gamma')
    fila['alertas'].append({'codigo': 'completado_sin_marcar', 'n': 2})
    _correr(tmp_path, LIBRES + '''
const alertas=(slug)=>walk(tarjetaDe(slug),n=>n.className==='alertas').flatMap(u=>tag(u,'li')).map(l=>l.textContent);
assert.ok(alertas('2026-01-10-alfa').includes('2 gaps de revisión abiertos'));
assert.ok(alertas('2026-01-14-epsilon').some(t=>/fuera del tope de lectura/.test(t)));
assert.ok(alertas('2026-01-11-beta').some(t=>/Sin estimación/.test(t)));
assert.ok(alertas('2026-01-12-gamma').includes('2 tareas completadas con criterios sin marcar'));
const sin=walk(tarjetaDe('2026-01-12-gamma'),n=>n.className==='alertas');
assert.ok(sin.length===1,'una lista de alertas por tarjeta con alertas');
''', datos=_exportado(sucia))


def test_solo_lectura_sin_draggable_ni_arrastre_ni_controles_ni_escritura(tmp_path, cartera):
    _correr(tmp_path, LIBRES + '''
const todos=walk(ids['kanban-iniciativas'],()=>true);
assert.ok(todos.length>20);
for(const n of todos){
  assert.equal(n.attrs.draggable,undefined,'sin draggable');assert.equal(n.draggable,undefined);
  for(const ev of Object.keys(n.events))assert.ok(!/^(drag|drop|mousedown|pointerdown|touchstart|keydown)/.test(ev),'sin listener '+ev);
  assert.ok(!['button','input','select','textarea','form'].includes(n.tagName),'sin controles: '+n.tagName);
}
assert.equal(requests.length,0,'exportado: ninguna petición');
''', datos=_exportado(cartera))


def test_la_tarjeta_con_plan_es_un_enlace_a_plan_id16_html_y_sin_plan_no_hay_enlace(tmp_path, cartera):
    esperado_id = hashlib.sha256('2026-01-10-alfa'.encode()).hexdigest()[:16]
    _correr(tmp_path, LIBRES + '''
const alfa=tarjetaDe('2026-01-10-alfa');
const a=tag(alfa,'a');
assert.equal(a.length,1,'un solo enlace por tarjeta (activable con Enter y con clic)');
assert.equal(a[0].attrs.href,'plan-'+ID+'.html');
assert.equal(a[0].textContent,'2026-01-10-alfa');
assert.equal(tag(tarjetaDe('2026-01-11-beta'),'a').length,0,'sin plan, sin enlace');
assert.match(tarjetaDe('2026-01-11-beta').textContent,/sin plan/i);
for(const l of walk(ids['kanban-iniciativas'],n=>n.tagName==='a'))assert.match(l.attrs.href,/^plan-[a-f0-9]{16}\\.html$/);
'''.replace('ID', json.dumps(esperado_id)), datos=_exportado(cartera))


def test_el_texto_del_repo_entra_por_textcontent_y_no_forma_el_enlace(tmp_path, cartera):
    hostil = json.loads(json.dumps(cartera))
    fila = next(f for f in hostil['iniciativas'] if f['slug'] == '2026-01-10-alfa')
    fila['titulo'] = '<img src=x onerror=alert(1)>'
    fila['slug'] = '"><script>alert(1)</script>'
    _correr(tmp_path, LIBRES + '''
assert.ok(ids['kanban-iniciativas'].textContent.includes('<img src=x onerror=alert(1)>'));
const enlace=walk(ids['kanban-iniciativas'],n=>n.tagName==='a'&&n.textContent.includes('<script>'))[0];
assert.match(enlace.attrs.href,/^plan-[a-f0-9]{16}\\.html$/,'el href sale del id, no del slug');
''', datos=_exportado(hostil))


def test_sin_cartera_o_no_disponible_dice_sin_datos_y_no_inventa_tarjetas(tmp_path, cartera):
    _correr(tmp_path, LIBRES + '''
assert.match(ids['cartera-estado'].textContent,/no incluye la cartera/);
assert.equal(columnas().length,0);assert.match(ids['kanban-iniciativas'].textContent,/Sin datos/);
''', datos={'pagina': 'iniciativas', 'modo': 'exportado', 'chartjs_disponible': True})
    _correr(tmp_path, LIBRES + '''
await respond({...DATOS,version:2});
assert.match(ids['cartera-estado'].textContent,/No se pudo leer la cartera/);
assert.equal(columnas().length,0);assert.match(ids['kanban-iniciativas'].textContent,/Sin datos/);
'''.replace('DATOS', json.dumps(cartera)), datos=SERVIDO)


def test_servido_pide_api_cartera_conserva_el_dom_si_no_cambia_y_la_ultima_vista_si_falla(tmp_path, cartera):
    _correr(tmp_path, LIBRES + '''
assert.equal(requests[0].url,'api/cartera');assert.equal(requests[0].options.credentials,'omit');
await respond(DATOS);
const primera=tarjetaDe('2026-01-10-alfa');assert.ok(primera);
fire(10000);await respond({...DATOS,observed_at:'2026-10-15T10:05:00Z'});
assert.equal(tarjetaDe('2026-01-10-alfa'),primera,'mismas iniciativas: se conserva el DOM (y el foco)');
assert.ok(ids['cartera-estado'].textContent.includes('10:05'));
fire(10000);requests[2].reject(Error('PRIVADO'));await settle();
assert.equal(tarjetaDe('2026-01-10-alfa'),primera);
assert.match(ids['cartera-estado'].textContent,/Se conserva la última vista/);
assert.ok(!ids['cartera-estado'].textContent.includes('PRIVADO'));
'''.replace('DATOS', json.dumps(cartera)), datos=SERVIDO)


def test_el_js_de_iniciativas_no_usa_innerhtml_arrastre_ni_red_ajena():
    fuente = (ASSETS / 'page-iniciativas.js').read_text(encoding='utf8')
    assert not re.search(r'innerHTML|outerHTML|insertAdjacentHTML|document\.write|eval\(|new Function|XMLHttpRequest|'
                         r'WebSocket|draggable|dragstart|dragover|drop|localStorage|sessionStorage|\.write\(', fuente)
    assert 'fetch(' not in fuente    # solo `page-cartera.js` habla con api/cartera


# --- T-20: gráficos de horas y coste por iniciativa -----------------------------------------------------------

GRAFICOS = '''
const figura=(id)=>tag(ids[id],'figure')[0];
const tablaDe=(id)=>filas(figura(id));
const serieDe=(i)=>creados.map(c=>c.config)[i];
'''


def test_dos_graficos_con_su_tabla_equivalente_y_las_iniciativas_sin_datos_solo_en_la_tabla(tmp_path, cartera):
    horas = {f['slug']: (f['horas']['real'], f['horas']['est']) for f in cartera['iniciativas']}
    _correr(tmp_path, GRAFICOS + '''
assert.equal(creados.length,2,'un gráfico de horas y uno de coste');
for(const id of ['grafico-horas','grafico-coste']){
  const fig=figura(id);assert.ok(fig,id);
  assert.equal(tag(fig,'canvas').length,1);assert.equal(tag(fig,'table').length,1);
  const region=walk(fig,n=>n.attrs.role==='region')[0];assert.equal(region.attrs.tabindex,'0');
}
const H=HORAS;
const tabla=tablaDe('grafico-horas');
assert.equal(tabla.length,Object.keys(H).length,'todas las iniciativas están en la tabla');
const cfg=serieDe(0);
const conDatos=Object.keys(H).filter(s=>H[s][0]!==null||H[s][1]!==null);
assert.deepEqual(cfg.data.labels,conDatos,'solo las iniciativas con algún dato entran en las barras');
for(const [slug,[real,est]] of Object.entries(H)){
  const fila=tabla.find(f=>f[0]===slug);assert.ok(fila,slug);
  const f=(v)=>v===null?'sin datos':v;
  assert.equal(fila[1]===('sin datos'),real===null,slug+' real');assert.equal(fila[2]==='sin datos',est===null,slug+' est');
  const i=cfg.data.labels.indexOf(slug);
  if(i>=0){assert.equal(cfg.data.datasets[0].data[i],real);assert.equal(cfg.data.datasets[1].data[i],est);}
}
for(const d of cfg.data.datasets)d.data.forEach((v,i)=>{if(v===0){const s=cfg.data.labels[i];assert.ok(H[s].includes(0),'un 0 solo si el ledger lo declara: '+s);}});
assert.deepEqual(cfg.data.datasets.map(d=>d.label),['Real (h)','Estimado (h)']);
'''.replace('HORAS', json.dumps(horas)), datos=_exportado(cartera))


def test_grafico_de_coste_usa_el_importe_estimado_y_el_real_y_deja_fuera_a_quien_no_tiene_ninguno(tmp_path, cartera):
    costes = {f['slug']: (f['coste']['real_eur'], f['coste']['est_eur']) for f in cartera['iniciativas']}
    _correr(tmp_path, GRAFICOS + '''
const C=COSTES;const cfg=serieDe(1);
const conDatos=Object.keys(C).filter(s=>C[s][0]!==null||C[s][1]!==null);
assert.deepEqual(cfg.data.labels,conDatos);
assert.deepEqual(cfg.data.datasets.map(d=>d.label),['Real (€)','Estimado (€)']);
const tabla=tablaDe('grafico-coste');
for(const [slug,[real,est]] of Object.entries(C)){
  const fila=tabla.find(f=>f[0]===slug);
  assert.equal(fila[1]==='sin datos',real===null,slug);assert.equal(fila[2]==='sin datos',est===null,slug);
  if(real!==null)assert.ok(fila[1].endsWith(' €'));
}
assert.ok(tabla.filter(f=>f[1]==='sin datos'&&f[2]==='sin datos').length>=1,'hay iniciativas sin ningún dato de coste');
'''.replace('COSTES', json.dumps(costes)), datos=_exportado(cartera))


def test_un_cero_real_es_un_dato_y_un_ausente_nunca_se_promedia(tmp_path, cartera):
    con_cero = json.loads(json.dumps(cartera))
    alfa = next(f for f in con_cero['iniciativas'] if f['slug'] == '2026-01-10-alfa')
    alfa['horas']['real'] = 0.0
    _correr(tmp_path, GRAFICOS + '''
const cfg=serieDe(0);const i=cfg.data.labels.indexOf('2026-01-10-alfa');
assert.equal(cfg.data.datasets[0].data[i],0,'un 0 declarado por el ledger es un dato');
const gamma=cfg.data.labels.indexOf('2026-01-12-gamma');
assert.equal(cfg.data.datasets[0].data[gamma],null,'«—» en el ledger sigue ausente');
const fila=tablaDe('grafico-horas').find(f=>f[0]==='2026-01-12-gamma');assert.equal(fila[1],'sin datos');
assert.ok(!JSON.stringify(cfg.data.datasets).includes('NaN'));
''', datos=_exportado(con_cero))


def test_sin_chartjs_los_dos_graficos_degradan_a_su_tabla(tmp_path, cartera):
    _correr(tmp_path, GRAFICOS + '''
assert.equal(creados.length,0);
for(const id of ['grafico-horas','grafico-coste']){assert.equal(tag(figura(id),'canvas').length,0);assert.equal(tag(figura(id),'table').length,1);}
assert.match(figura('grafico-horas').textContent,/Chart\.js no está disponible/);
''', datos=_exportado(cartera, chartjs_disponible=False))


def test_sin_datos_de_cartera_los_graficos_dicen_sin_datos_y_no_dibujan(tmp_path):
    _correr(tmp_path, GRAFICOS + '''
assert.equal(creados.length,0);
for(const id of ['grafico-horas','grafico-coste'])assert.match(figura(id).textContent,/Sin datos/);
''', datos={'pagina': 'iniciativas', 'modo': 'exportado', 'chartjs_disponible': True})


def test_los_graficos_no_se_redibujan_si_las_cifras_no_cambian_en_servido(tmp_path, cartera):
    _correr(tmp_path, GRAFICOS + '''
await respond(DATOS);const primero=figura('grafico-horas');assert.equal(creados.length,2);
fire(10000);await respond({...DATOS,observed_at:'2026-10-15T10:05:00Z'});
assert.equal(figura('grafico-horas'),primero);assert.equal(creados.length,2);
'''.replace('DATOS', json.dumps(cartera)), datos=SERVIDO)
