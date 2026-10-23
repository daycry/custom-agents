"""T-07: adaptador de gráficos (panel-charts.js) y render de ausencias (panel-core.js), en Node con DOM falso."""
import json
from pathlib import Path
import re
import shutil
import subprocess

import pytest

ASSETS = Path(__file__).resolve().parents[1] / 'skills/plugin-panel/assets'

HARNESS = r'''
const assert = require('node:assert/strict');
class El {
  constructor(tag){this.tagName=String(tag).toLowerCase();this.children=[];this.attrs={};this.className='';this.dataset={};this._text='';this.hidden=false;}
  set textContent(v){this._text=String(v);this.children=[];}
  get textContent(){return this._text+this.children.map(c=>c.textContent).join('');}
  set innerHTML(v){throw new Error('Asignación de HTML no confiable');}
  append(...ns){for(const n of ns)this.children.push(typeof n==='string'?Object.assign(new El('#text'),{_text:n}):n);}
  appendChild(n){this.append(n);return n;}
  setAttribute(k,v){this.attrs[k]=String(v);}
  getAttribute(k){return this.attrs[k]===undefined?null:this.attrs[k];}
  addEventListener(){}
  getContext(){return {};}
}
const walk=(el,f,out=[])=>{if(f(el))out.push(el);for(const c of el.children)walk(c,f,out);return out;};
const tag=(el,t)=>walk(el,n=>n.tagName===t);
const celdas=(fila)=>fila.children.map(c=>c.textContent);
global.window=global;
const estilos={'--serie-1':'#aa0001','--serie-2':'#aa0002','--serie-3':'#aa0003','--serie-4':'#aa0004','--serie-5':'#aa0005','--serie-6':'#aa0006','--texto':'#ffffff','--borde':'#777777'};
global.getComputedStyle=()=>({getPropertyValue:(k)=>estilos[k]||''});
global.document={createElement:(t)=>new El(t),documentElement:new El('html'),getElementById:()=>null,addEventListener(){},readyState:'complete',querySelector:()=>null,querySelectorAll:()=>[]};
const creados=[];
class FakeChart{constructor(canvas,config){this.canvas=canvas;this.config=config;creados.push(this);}destroy(){}}
FakeChart.defaults={color:'',borderColor:'',font:{}};
require(CORE);const Core=global.PanelCore;
require(CHARTS);const Charts=global.PanelCharts;
const spec=(extra={})=>Object.assign({id:'g1',titulo:'Piezas por tipo',tipo:'bar',etiquetas:['Agentes','Skills','Comandos'],
  series:[{nombre:'Piezas',valores:[3,5,2]}],origen:'catálogo del plugin'},extra);
const nuevo=()=>new El('div');
'''


def _correr(tmp_path, cuerpo):
    node = shutil.which('node')
    if not node:
        pytest.skip('Node no disponible para el arnés de panel-charts.js')
    programa = (HARNESS.replace('CORE', json.dumps(str(ASSETS / 'panel-core.js')))
                .replace('CHARTS', json.dumps(str(ASSETS / 'panel-charts.js')))
                + '\n(async()=>{' + cuerpo + '})().catch(e=>{console.error(e);process.exitCode=1;});')
    fuente = tmp_path / 'charts.cjs'
    fuente.write_text(programa, encoding='utf8')
    r = subprocess.run([node, str(fuente)], capture_output=True, text=True, encoding='utf8', errors='replace', timeout=20)
    assert r.returncode == 0, r.stdout + r.stderr


ESCENARIOS = {
    'con_chartjs_canvas_con_nombre_y_tabla_equivalente': '''
global.Chart=FakeChart;
const c=nuevo();
Charts.dibujar(c,spec());
const fig=tag(c,'figure')[0];assert.ok(fig,'hay un <figure>');
const canvas=tag(fig,'canvas')[0];assert.ok(canvas,'hay canvas');
assert.match(canvas.attrs['aria-label'],/Piezas por tipo/);
assert.equal(canvas.attrs.role,'img');
assert.equal(creados.length,1);assert.equal(creados[0].config.type,'bar');
const tabla=tag(fig,'table')[0];assert.ok(tabla,'tabla equivalente');
assert.equal(tag(tabla,'caption')[0].textContent,'Piezas por tipo');
const cab=celdas(tag(tabla,'thead')[0].children[0]);assert.deepEqual(cab,['Categoría','Piezas']);
const filas=tag(tag(tabla,'tbody')[0],'tr').map(celdas);
assert.deepEqual(filas,[['Agentes','3'],['Skills','5'],['Comandos','2']]);
const region=walk(fig,n=>n.attrs.role==='region')[0];assert.ok(region);
assert.equal(region.attrs.tabindex,'0');assert.match(region.attrs['aria-label'],/Tabla equivalente/);
assert.ok(tag(tabla,'th').every(t=>t.attrs.scope==='col'||t.attrs.scope==='row'),'th con scope');
''',
    'sin_chartjs_solo_tabla_con_aviso': '''
delete global.Chart;
const c=nuevo();
Charts.dibujar(c,spec());
const fig=tag(c,'figure')[0];
assert.equal(tag(fig,'canvas').length,0);assert.equal(creados.length,0);
assert.equal(tag(fig,'table').length,1);
const aviso=walk(fig,n=>n.attrs.role==='status')[0];
assert.match(aviso.textContent,/Chart\\.js/);assert.match(aviso.textContent,/solo la tabla/);
''',
    'chartjs_marcado_no_disponible_no_se_usa': '''
global.Chart=FakeChart;
const c=nuevo();
Charts.dibujar(c,spec(),{chartDisponible:false});
assert.equal(creados.length,0);assert.equal(tag(c,'canvas').length,0);assert.equal(tag(c,'table').length,1);
''',
    'chartjs_que_falla_degrada_a_tabla': '''
global.Chart=class{constructor(){throw new Error('boom');}};
const c=nuevo();
Charts.dibujar(c,spec());
assert.equal(tag(c,'table').length,1);
assert.match(walk(c,n=>n.attrs.role==='status')[0].textContent,/Chart\\.js/);
''',
    'valor_null_es_sin_datos_y_nunca_cero': '''
global.Chart=FakeChart;
const c=nuevo();
Charts.dibujar(c,spec({series:[{nombre:'Piezas',valores:[3,null,2]}]}));
const filas=tag(tag(c,'tbody')[0],'tr').map(celdas);
assert.deepEqual(filas[1],['Skills','sin datos']);
assert.deepEqual(creados[0].config.data.datasets[0].data,[3,null,2]);
assert.ok(!JSON.stringify(creados[0].config.data.datasets[0].data).includes('0'),'ningún 0 inventado');
assert.equal(creados[0].config.data.datasets[0].spanGaps,false);
const marca=walk(c,n=>n.className.includes('sin-datos'));assert.equal(marca.length,1);
''',
    'sin_datos_se_pinta_con_etiqueta_y_origen': '''
global.Chart=FakeChart;
const c=nuevo();
Charts.dibujar(c,spec({series:[{nombre:'A',valores:[null,null,null]}]}));
assert.equal(creados.length,0,'sin ningún valor no se dibuja el gráfico');
const aus=walk(c,n=>n.className.includes('ausencia'))[0];
assert.match(aus.textContent,/sin datos/i);assert.match(aus.textContent,/catálogo del plugin/);
''',
    'parcial_n_de_m_con_origen': '''
global.Chart=FakeChart;
const c=nuevo();
Charts.dibujar(c,spec({parcial:{presentes:2,total:3,origen:'ledger de la iniciativa'}}));
const aus=walk(c,n=>n.className.includes('ausencia'))[0];
assert.match(aus.textContent,/parcial: 2 de 3/i);assert.match(aus.textContent,/ledger de la iniciativa/);
''',
    'textos_por_textcontent_sin_innerhtml': '''
global.Chart=FakeChart;
const c=nuevo();
Charts.dibujar(c,spec({titulo:'<img src=x onerror=alert(1)>',etiquetas:['<b>x</b>','y','z']}));
assert.ok(c.textContent.includes('<img src=x onerror=alert(1)>'));
assert.ok(c.textContent.includes('<b>x</b>'));
''',
    'series_se_distinguen_por_forma_color_y_etiqueta': '''
global.Chart=FakeChart;
const c=nuevo();
const series=[1,2,3,4,5,6].map(i=>({nombre:'S'+i,valores:[i,i,i]}));
Charts.dibujar(c,spec({tipo:'line',series}));
const ds=creados[0].config.data.datasets;
assert.equal(new Set(ds.map(d=>d.pointStyle)).size,6,'6 formas distintas');
assert.equal(new Set(ds.map(d=>d.borderColor)).size,6,'6 colores distintos');
assert.deepEqual(ds.map(d=>d.label),['S1','S2','S3','S4','S5','S6']);
assert.equal(creados[0].config.options.plugins.legend.display,true);
assert.deepEqual(celdas(tag(tag(c,'table')[0],'thead')[0].children[0]),['Categoría','S1','S2','S3','S4','S5','S6']);
''',
    'sin_datos_filas_en_la_tabla_y_fuera_de_las_barras': '''
global.Chart=FakeChart;
const c=nuevo();
Charts.dibujar(c,spec({etiquetas:['A','B'],series:[{nombre:'Real',valores:[3,null]},{nombre:'Est',valores:[4,5]}],sinDatos:['C','D']}));
const fig=tag(c,'figure')[0];
const filas=tag(tag(fig,'table')[0],'tbody')[0].children.map(celdas);
assert.deepEqual(filas,[['A','3','4'],['B','sin datos','5'],['C','sin datos','sin datos'],['D','sin datos','sin datos']]);
assert.deepEqual(creados[0].config.data.labels,['A','B'],'las iniciativas sin datos no entran en las barras');
assert.deepEqual(creados[0].config.data.datasets.map(d=>d.data),[[3,null],[4,5]]);
assert.equal(walk(fig,n=>n.className.includes('sin-datos')).length,2+3,'una celda ausente por serie y fila sin datos');
''',
    'solo_filas_sin_datos_no_dibuja_el_grafico_pero_las_lista': '''
global.Chart=FakeChart;
const c=nuevo();
Charts.dibujar(c,spec({etiquetas:[],series:[{nombre:'Real',valores:[]}],sinDatos:['C']}));
assert.equal(creados.length,0);
const fig=tag(c,'figure')[0];
assert.match(walk(fig,n=>n.className.includes('ausencia'))[0].textContent,/sin datos/i);
assert.deepEqual(tag(tag(fig,'table')[0],'tbody')[0].children.map(celdas),[['C','sin datos']]);
''',
    'sin_animaciones_y_sin_red': '''
global.Chart=FakeChart;
const c=nuevo();Charts.dibujar(c,spec());
assert.equal(creados[0].config.options.animation,false);
''',
    'core_texto_de_ausencia': '''
assert.equal(Core.celda(null),'sin datos');assert.equal(Core.celda(undefined),'sin datos');
assert.equal(Core.celda(NaN),'sin datos');assert.equal(Core.celda(0),'0');assert.equal(Core.celda('a'),'a');
assert.equal(Core.textoAusencia({estado:'sin-datos',origen:'el ledger'}),'Sin datos (origen: el ledger)');
assert.equal(Core.textoAusencia({estado:'parcial',presentes:2,total:5,origen:'el ledger'}),'Parcial: 2 de 5 (origen: el ledger)');
assert.equal(Core.textoAusencia({estado:'sin-datos'}),'Sin datos');
const p=nuevo();const n=Core.renderAusencia(p,{estado:'parcial',presentes:1,total:4,origen:'x'});
assert.equal(n.tagName,'p');assert.equal(n.attrs.role,'status');assert.ok(n.className.includes('ausencia'));
assert.match(n.textContent,/parcial: 1 de 4/i);assert.equal(p.children.length,1);
''',
}


@pytest.mark.parametrize('nombre', ESCENARIOS)
def test_adaptador_de_graficos(nombre, tmp_path):
    _correr(tmp_path, ESCENARIOS[nombre])


def test_las_formas_cubren_todas_las_series_de_la_paleta():
    css = (ASSETS / 'panel.css').read_text(encoding='utf-8')
    series = set(re.findall(r'--serie-(\d+)\s*:', css))
    js = (ASSETS / 'panel-charts.js').read_text(encoding='utf-8')
    formas = re.search(r'FORMAS\s*=\s*\[(.*?)\]', js, re.S).group(1)
    assert len(re.findall(r"'[a-zA-Z]+'", formas)) >= len(series) == 6


def test_el_adaptador_no_usa_innerhtml_red_ni_eval():
    js = (ASSETS / 'panel-charts.js').read_text(encoding='utf-8') + (ASSETS / 'panel-core.js').read_text(encoding='utf-8')
    for prohibido in ('innerHTML', 'insertAdjacentHTML', 'outerHTML', 'eval(', 'new Function', 'fetch(', 'XMLHttpRequest', 'http://', 'https://'):
        assert prohibido not in js, prohibido
