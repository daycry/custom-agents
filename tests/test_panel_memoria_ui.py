"""T-30..T-35: página Memoria (tipo y estado, bandeja del curador, línea de tiempo, grafo de una entrada, backends y journal).

Tres capas: la proyección `panel_data.memoria()` contra las salidas REALES de `knowledge-find.py --json` y
`journal.py select --json`; el HTML del exportador/servidor (esqueleto, scripts, datos incrustados) y el JS de la
página en Node con un DOM falso. Datos de prueba genéricos (`tests/memoria_fixture.py`).
"""
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest

from memoria_fixture import SECRETO, crear_proyecto
from test_panel_inicio_ui import ASSETS, HARNESS, SCRIPTS, inventory, panel  # noqa: F401  (fixtures)

ROOT = Path(__file__).resolve().parents[1]
FIND = ROOT / 'agent-kits/shared/knowledge-find.py'
IDS = ('memoria-estado', 'grafico-memoria', 'memoria-area', 'memoria-tabla', 'memoria-bandeja', 'memoria-linea',
       'memoria-relaciones', 'memoria-relaciones-estado', 'memoria-grafo', 'memoria-lista-relaciones',
       'memoria-backends', 'memoria-journal', 'memoria-actualizar', 'memoria-area-nota')


def _panel_data():
    spec = importlib.util.spec_from_file_location('panel_data_memoria', SCRIPTS / 'panel_data.py')
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope='module')
def proyecto(tmp_path_factory):
    return crear_proyecto(tmp_path_factory.mktemp('memoria'))


@pytest.fixture(scope='module')
def memoria(proyecto):
    return _panel_data().memoria(proyecto, relaciones=True)


def _find(proyecto, *args):
    r = subprocess.run([sys.executable, str(FIND), *args, '--json', '--root', str(proyecto), '--no-index'],
                       capture_output=True, text=True, encoding='utf8', check=True)
    return json.loads(r.stdout)


# --- proyección de datos (T-30..T-32, T-35) ------------------------------------------------------------------------

def test_conteos_por_tipo_y_estado_son_los_de_knowledge_find_json(proyecto, memoria):
    aciertos = _find(proyecto, '', '--limit', '0')['aciertos']
    esperado = {}
    for a in aciertos:
        esperado.setdefault(a['tipo'], {}).setdefault(a['estado'], 0)
        esperado[a['tipo']][a['estado']] += 1
    assert memoria['conteos'] == esperado and memoria['total'] == len(aciertos) == len(memoria['entradas'])
    assert {e['id'] for e in memoria['entradas']} == {a['id'] for a in aciertos}
    assert memoria['source'] == 'memoria_panel' and memoria['status'] == 'ok' and memoria['recortado'] == 0


def test_vigente_es_la_entrada_sin_sucesor_y_no_obsoleta(memoria):
    por_id = {e['id']: e for e in memoria['entradas']}
    assert {i for i, e in por_id.items() if e['vigente']} == {'ADR-003', 'GOT-001', 'GOT-002', 'LES-001'}
    assert por_id['ADR-001']['sustituida_por'] == ['ADR-002'] and por_id['ADR-002']['sustituida_por'] == ['ADR-003']
    assert por_id['ADR-003']['sustituye_a'] == ['ADR-002']
    assert not por_id['ADR-004']['vigente'] and por_id['ADR-004']['sustituida_por'] == []   # obsoleta sin sucesor


@pytest.mark.parametrize('ident', ['ADR-002', 'ADR-003', 'GOT-001', 'LES-001'])
def test_las_relaciones_son_las_de_related_json(proyecto, memoria, ident):
    real = _find(proyecto, '--related', ident)['relaciones']
    mia = memoria['relaciones'][ident]
    assert [(s['relacion'], s['id']) for s in mia['sucesion']] == [(s['relacion'], s['id']) for s in real['sucesion']]
    assert mia['por_iniciativa'] == [a['id'] for a in real['iniciativa']['aciertos']]
    assert mia['por_area'] == [a['id'] for a in real['area']['aciertos']]


def test_bandeja_cuenta_y_lista_candidatos_por_estado_y_lo_aprobado(proyecto, memoria):
    b = memoria['bandeja']
    assert {k: v['n'] for k, v in b['estados'].items()} == {'pending': 2, 'needs_changes': 1, 'rejected': 0}
    assert [i['candidato'] for i in b['estados']['pending']['items']] == ['2026-10-01-uno.md', '2026-10-02-dos.md']
    assert b['estados']['pending']['items'][0]['titular'] == 'Candidato 2026-10-01-uno'
    assert b['estados']['pending']['items'][0]['category'] == 'GOTCHA'
    assert b['aprobadas'] == {'n': 0, 'items': []}


def test_journal_trae_la_continuidad_y_redacta_un_secreto_en_la_cita(tmp_path):
    proyecto = crear_proyecto(tmp_path, secreto_en_journal=True)
    j = _panel_data().memoria(proyecto)['journal']
    s = j['sesiones'][0]
    assert j['status'] == 'ok' and s['fecha'] == '2026-10-10' and s['iniciativa'] == 'alfa'
    assert s['punto_actual'] == 'En la tarea 3' and s['siguientes_pasos'] == ['Cerrar la tarea']
    assert s['bloqueos'] == ['Falta el dato'] and s['descartados'] == ['Polling - caro']
    assert SECRETO not in json.dumps(j) and '[secreto redactado]' in s['objetivo']


def test_la_respuesta_cabe_en_64_kib_y_declara_lo_recortado(tmp_path):
    proyecto = crear_proyecto(tmp_path)
    for n in range(200):          # el corpus lee como mucho 128 ficheros: ids, titulos y areas largos para pasar de 64 KiB
        ruta = proyecto / f'docs/knowledge/lessons/LES-{n + 10:03d}-x.md'
        ruta.write_text(f'---\nid: LES-{n + 10:03d}-' + 'i' * 200 + '\ntitulo: ' + 'T' * 150
                        + f'\nestado: aceptada\nfecha: 2026-03-01\narea: Area {n} ' + 'a' * 140 + '\n---\n\n# x\n', encoding='utf8')
    m = _panel_data().memoria(proyecto)
    assert len(json.dumps(m, ensure_ascii=False).encode('utf8')) <= 65536
    assert m['recortado'] > 0 and m['status'] == 'partial' and not m['complete']
    assert sum(sum(v.values()) for v in m['conteos'].values()) == m['total'] >= len(m['entradas']) + m['recortado']


def test_el_secreto_se_redacta_antes_de_recortar(tmp_path):
    proyecto = crear_proyecto(tmp_path)
    titular = 'x' * 140 + ' token=' + SECRETO
    (proyecto / 'docs/knowledge/lessons/LES-050-s.md').write_text(
        f'---\nid: LES-050\ntitulo: {titular}\nestado: aceptada\nfecha: 2026-03-01\narea: a\n---\n\n# x\n', encoding='utf8')
    m = _panel_data().memoria(proyecto)
    fila = next(e for e in m['entradas'] if e['id'] == 'LES-050')
    assert SECRETO[:12] not in fila['titular'] and len(fila['titular']) <= 160


def test_sin_corpus_dice_no_encontrado_y_sin_datos(tmp_path):
    m = _panel_data().memoria(tmp_path)
    assert m['status'] in ('not_found', 'partial') and m['entradas'] == [] and m['total'] == 0
    assert [b['situacion'] for b in m['backends']] == ['no_configurado', 'no_configurado']
    assert m['journal']['sesiones'] == []


# --- HTML ------------------------------------------------------------------------------------------------------------

def _html(panel, inventory, memoria, modo='exportado'):
    pp = panel._load_pages()
    cuerpos = panel.cuerpos_paginas(inventory, live=modo == 'servido')
    return pp.render_page('memoria', modo=modo, generado='2026-10-16 10:00 UTC', cuerpo=cuerpos['memoria'],
                          datos=pp.datos_de_pagina('memoria', inventory, modo=modo, memoria=memoria),
                          nonce='n1' if modo == 'servido' else None, scripts_omitidos=('panel-review.js',))


def test_exportado_lleva_esqueleto_scripts_en_orden_y_memoria_incrustada(panel, inventory, memoria):
    html = _html(panel, inventory, memoria)
    for ident in IDS:
        assert f'id="{ident}"' in html, ident
    orden = [m.group(1) for m in re.finditer(r'<script[^>]*\ssrc="([^"]+)"', html)]
    assert orden == ['vendor/chart.js/chart.umd.min.js', 'assets/panel-core.js', 'assets/panel-charts.js',
                     'assets/panel-graph.js', 'assets/page-memoria.js']
    bruto = re.search(r'<script type="application/json" id="panel-data">(.*?)</script>', html, re.S).group(1)
    assert json.loads(bruto)['memoria'] == memoria and '<' not in bruto
    assert 'for="memoria-area"' in html and '<select id="memoria-area"' in html
    assert 'api/' not in html and 'id="memory-query"' not in html


def test_servido_no_incrusta_la_memoria_lleva_nonce_y_conserva_la_consulta(panel, inventory, memoria):
    html = _html(panel, inventory, memoria, 'servido')
    datos = json.loads(re.search(r'id="panel-data">(.*?)</script>', html, re.S).group(1))
    assert 'memoria' not in datos and datos['modo'] == 'servido'
    assert all('nonce="n1"' in e for e in re.findall(r'<script\b[^>]*>', html))
    orden = [m.group(1) for m in re.finditer(r'<script[^>]*\ssrc="([^"]+)"', html)]
    assert orden[-3:] == ['assets/panel-graph.js', 'assets/page-memoria.js', 'assets/panel-memory.js']
    assert 'id="memory-query"' in html

@pytest.mark.parametrize('modo', ['exportado', 'servido'])
def test_aria_label_solo_en_elementos_con_rol_fix_qa_a11y01(panel, inventory, memoria, modo):
    """A11Y-01 (axe aria-prohibited-attr): un div/span/p sin role no admite aria-label."""
    html = _html(panel, inventory, memoria, modo)
    malos = [t for t in re.findall(r'<(?:div|span|p)\b[^>]*>', html) if 'aria-label=' in t and ' role="' not in t]
    assert malos == []
    if modo == 'servido':
        for ident in ('memory-selected', 'memory-related'):
            assert re.search(rf'<div id="{ident}"[^>]*role="region"', html), ident


def test_exportar_sitio_copia_los_js_de_memoria(panel, inventory, memoria, tmp_path):
    escritos, _ = panel._load_pages().exportar_sitio(tmp_path / 's', inventory, memoria=memoria,
                                                     cuerpos=panel.cuerpos_paginas(inventory))
    assert {'assets/page-memoria.js', 'assets/panel-graph.js'} <= set(escritos)
    html = (tmp_path / 's/memoria.html').read_text(encoding='utf8')
    assert json.loads(re.search(r'id="panel-data">(.*?)</script>', html, re.S).group(1))['memoria'] == memoria


def test_la_memoria_solo_viaja_a_su_pagina(panel, inventory, memoria):
    pp = panel._load_pages()
    for slug in ('inicio', 'plan', 'catalogo', 'diagnostico', 'iniciativas', 'agentes'):
        assert 'memoria' not in pp.datos_de_pagina(slug, inventory, modo='exportado', memoria=memoria)


# --- JS en Node -------------------------------------------------------------------------------------------------------

def _correr(tmp_path, cuerpo, *, datos):
    node = shutil.which('node')
    if not node:
        pytest.skip('Node no disponible para el arnés de page-memoria.js')
    fuentes = ''.join((ASSETS / n).read_text(encoding='utf8')
                      for n in ('panel-core.js', 'panel-charts.js', 'panel-graph.js', 'page-memoria.js'))
    programa = (HARNESS.replace('IDS', json.dumps(list(IDS))) + '\ndocument.createElementNS=(ns,t)=>new El(t);\n'
                + 'ponerDatos(' + json.dumps(datos) + ');\n' + fuentes
                + '\n(async()=>{' + cuerpo + '})().catch(e=>{console.error(e);process.exitCode=1;});')
    fuente = tmp_path / 'memoria.cjs'
    fuente.write_text(programa, encoding='utf8')
    r = subprocess.run([node, str(fuente)], capture_output=True, text=True, encoding='utf8', errors='replace', timeout=30)
    assert r.returncode == 0, r.stdout + r.stderr


def _exportado(memoria, **extra):
    return {'pagina': 'memoria', 'modo': 'exportado', 'chartjs_disponible': True, 'memoria': memoria, **extra}


SERVIDO = {'pagina': 'memoria', 'modo': 'servido', 'chartjs_disponible': True}

LIBRES = '''
const filasTabla=()=>tag(ids['memoria-tabla'],'tbody').length?tag(tag(ids['memoria-tabla'],'tbody')[0],'tr'):[];
const idsTabla=()=>filasTabla().map(f=>f.children[0].textContent);
const botones=(n)=>walk(n,x=>x.tagName==='button');
'''


def test_ca22_grafico_y_tabla_por_tipo_y_estado_con_filtro_de_area_por_teclado(tmp_path, memoria):
    _correr(tmp_path, LIBRES + '''
assert.equal(creados.length,1);
const cfg=creados[0].config;
assert.deepEqual(cfg.data.labels,['ADR','Gotcha','Lección']);
const por=Object.fromEntries(cfg.data.datasets.map(d=>[d.label,d.data]));
assert.deepEqual(por['aceptada'],[2,1,1]);assert.deepEqual(por['propuesta'],[0,1,0]);assert.deepEqual(por['obsoleta'],[2,0,0]);
assert.equal(idsTabla().length,7);
const sel=ids['memoria-area'];
const opciones=sel.children.map(o=>o.textContent);
assert.equal(opciones[0],'Todas las áreas');assert.ok(opciones.some(t=>t.startsWith('Seguridad / sesiones (2)')));
sel.value='Seguridad / sesiones';sel.events.change[0]({});
assert.deepEqual(idsTabla().sort(),['GOT-001','GOT-002']);
const ultimo=creados[creados.length-1].config;
assert.equal(ultimo.data.datasets.reduce((a,d)=>a+d.data.reduce((x,y)=>x+y,0),0),2);
sel.value='';sel.events.change[0]({});assert.equal(idsTabla().length,7);
''', datos=_exportado(memoria))


def test_ca22_sin_memoria_incrustada_o_invalida_lo_dice(tmp_path, memoria):
    _correr(tmp_path, '''
assert.match(ids['memoria-estado'].textContent,/no incluye la memoria/);assert.equal(creados.length,0);
''', datos={'pagina': 'memoria', 'modo': 'exportado', 'chartjs_disponible': True})
    _correr(tmp_path, '''
assert.match(ids['memoria-estado'].textContent,/No se pudo leer la memoria/);assert.equal(creados.length,0);
''', datos=_exportado({**memoria, 'version': 2}))


def test_servido_pide_api_memoria_sin_credenciales_y_conserva_la_ultima_vista_si_falla(tmp_path, memoria):
    _correr(tmp_path, LIBRES + '''
assert.equal(requests[0].url,'api/memoria');assert.equal(requests[0].options.credentials,'omit');
assert.equal(requests[0].options.cache,'no-store');assert.ok(requests[0].options.signal);
await respond(DATOS);
assert.equal(idsTabla().length,7);
ids['memoria-actualizar'].events.click[0]({});
requests[1].reject(Error('PRIVADO'));await settle();
assert.equal(idsTabla().length,7);
assert.match(ids['memoria-estado'].textContent,/Se conserva la última vista/);
assert.ok(!ids['memoria-estado'].textContent.includes('PRIVADO'));
'''.replace('DATOS', json.dumps(memoria)), datos=SERVIDO)


def test_ca23_bandeja_en_solo_lectura_sin_botones_ni_formularios(tmp_path, memoria):
    _correr(tmp_path, LIBRES + '''
const b=ids['memoria-bandeja'];const t=b.textContent;
assert.match(t,/Pendientes \\(2\\)/);assert.match(t,/Cambios pedidos \\(1\\)/);assert.match(t,/Rechazados \\(0\\)/);
assert.ok(t.includes('2026-10-01-uno.md')&&t.includes('Candidato 2026-10-02-dos'));assert.match(t,/Aprobadas \\(0\\)/);
assert.match(t,/knowledge-curator/);
const todos=walk(b,()=>true);assert.ok(todos.length>10);
for(const n of todos){
  assert.ok(!['button','input','select','textarea','form','a'].includes(n.tagName),'sin controles: '+n.tagName);
  assert.equal(Object.keys(n.events).length,0,'sin listeners');
}
''', datos=_exportado(memoria))


def test_ca24_linea_de_tiempo_por_fecha_con_cadena_y_vigente_en_texto(tmp_path, memoria):
    _correr(tmp_path, LIBRES + '''
const items=tag(ids['memoria-linea'],'li').filter(l=>l.className.includes('entrada-tiempo'));
const ordenIds=items.map(l=>l.attrs['data-id']);
assert.deepEqual(ordenIds,['ADR-004','ADR-001','GOT-001','GOT-002','ADR-002','LES-001','ADR-003']);   // por fecha
const de=(id)=>items.find(l=>l.attrs['data-id']===id).textContent;
assert.match(de('ADR-003'),/vigente/i);assert.match(de('ADR-003'),/sustituye a ADR-002/);
for(const id of ['ADR-001','ADR-002','ADR-004'])assert.ok(!/vigente/i.test(de(id)),id);
assert.match(de('ADR-001'),/Cadena: ADR-001 → ADR-002 → ADR-003/);
assert.match(de('ADR-002'),/sustituida por ADR-003/);
assert.ok(!/Cadena/.test(de('ADR-004')));
''', datos=_exportado(memoria))


def _aristas(proyecto, ident):
    r = _find(proyecto, '--related', ident)['relaciones']
    return sorted([['sucesion', s['id']] for s in r['sucesion']] + [['iniciativa', a['id']] for a in r['iniciativa']['aciertos']]
                  + [['area', a['id']] for a in r['area']['aciertos']])


@pytest.mark.parametrize('ident', ['ADR-002', 'GOT-001'])
def test_ca25_exportado_el_grafo_tiene_las_aristas_de_related_json_y_ningun_nodo_a_dos_saltos(tmp_path, proyecto, memoria, ident):
    esperado = _aristas(proyecto, ident)
    _correr(tmp_path, LIBRES + '''
const fila=filasTabla().find(f=>f.children[0].textContent===IDENT);
botones(fila)[0].events.click[0]({});await settle();
const svg=walk(ids['memoria-grafo'],n=>n.tagName==='svg')[0];assert.ok(svg);
assert.equal(svg.attrs.role,'img');assert.match(svg.attrs['aria-label'],new RegExp(IDENT));
const lineas=walk(svg,n=>n.tagName==='line');
const aristas=lineas.map(l=>[l.attrs['data-grupo'],l.attrs['data-id']]).sort();
assert.deepEqual(aristas,ESP);
const nodos=walk(svg,n=>(n.attrs.class||'').split(' ').includes('nodo'));
const vecinos=new Set(ESP.map(a=>a[1]));
assert.equal(nodos.length,vecinos.size+1,'el centro y un salto, nada más');
assert.deepEqual(nodos.map(n=>n.attrs['data-id']).filter(i=>i!==IDENT).sort(),[...vecinos].sort());
const lista=tag(ids['memoria-lista-relaciones'],'li').map(l=>[l.attrs['data-grupo'],l.attrs['data-id']]).sort();
assert.deepEqual(lista,ESP,'la lista textual tiene las mismas aristas');
assert.equal(document.activeElement,ids['memoria-relaciones']);
assert.equal(requests.length,0,'exportado: sin red');
'''.replace('IDENT', json.dumps(ident)).replace('ESP', json.dumps(esperado)), datos=_exportado(memoria))


def test_ca25_servido_usa_la_operacion_related_de_api_memory(tmp_path, memoria):
    respuesta = {'version': 1, 'source': 'canonical_knowledge', 'observed_at': '2026-10-16T10:00:00Z', 'operation': 'related',
                 'status': 'ok', 'complete': True, 'issues': [], 'entries': [], 'selected': None,
                 'budget': {'files': 1, 'bytes': 1, 'entries': 1},
                 'related': {'sucesion': [{'relation': 'sustituida por', 'id': 'ADR-003', 'entry': None},
                                          {'relation': 'sustituye a', 'id': 'ADR-001', 'entry': None}],
                             'iniciativa': [], 'area': [], 'enlaces': []}}
    _correr(tmp_path, LIBRES + '''
await respond(DATOS);
botones(filasTabla().find(f=>f.children[0].textContent==='ADR-002'))[0].events.click[0]({});
const r=requests[1];assert.equal(r.url,'api/memory');assert.equal(r.options.method,'POST');
assert.deepEqual(JSON.parse(r.options.body),{operation:'related',id:'ADR-002'});assert.equal(r.options.credentials,'omit');
await respond(REL);
const lista=tag(ids['memoria-lista-relaciones'],'li').map(l=>[l.attrs['data-grupo'],l.attrs['data-id']]).sort();
assert.deepEqual(lista,[['sucesion','ADR-001'],['sucesion','ADR-003']]);
const lineas=walk(ids['memoria-grafo'],n=>n.tagName==='line');assert.equal(lineas.length,2);
botones(filasTabla().find(f=>f.children[0].textContent==='GOT-001'))[0].events.click[0]({});
await respond({...REL,operation:'show'});
assert.match(ids['memoria-relaciones-estado'].textContent,/No se pudieron leer las relaciones/);
'''.replace('DATOS', json.dumps(memoria)).replace('REL', json.dumps(respuesta)), datos=SERVIDO)


def test_ca25_el_texto_hostil_entra_por_textcontent(tmp_path, memoria):
    hostil = json.loads(json.dumps(memoria))
    for e in hostil['entradas']:
        if e['id'] == 'ADR-003':
            e['titular'] = '<img src=x onerror=alert(1)>'
    _correr(tmp_path, LIBRES + '''
botones(filasTabla().find(f=>f.children[0].textContent==='ADR-002'))[0].events.click[0]({});await settle();
assert.ok(ids['memoria-lista-relaciones'].textContent.includes('<img src=x onerror=alert(1)>'));
''', datos=_exportado(hostil))


def test_ca26_backends_con_fecha_de_la_fuente_sin_datos_y_sin_enlace_inventado(tmp_path, memoria):
    _correr(tmp_path, '''
const t=ids['memoria-backends'].textContent;
assert.match(t,/Kwipu/);assert.match(t,/3 entradas/);assert.match(t,/2026-10-02T11:30:00Z/);
assert.match(t,/Graphiti/);assert.match(t,/2 entradas/);assert.match(t,/publicación interrumpida/);
assert.match(t,/interfaz: no declarada/);
assert.ok(!/ 0 entradas/.test(t));
assert.equal(walk(ids['memoria-backends'],n=>n.tagName==='a').length,0,'sin ui_url no hay enlace');
''', datos=_exportado(memoria))


def test_ca26_backend_no_configurado_y_ui_url_declarada(tmp_path, memoria):
    otro = json.loads(json.dumps(memoria))
    otro['backends'] = [{'backend': 'kwipu', 'tipo': 'markdown-export', 'situacion': 'no_configurado', 'entradas': None,
                         'ultima': None, 'interrumpida': False, 'ui_url': None},
                        {'backend': 'graphiti', 'tipo': 'graphiti', 'situacion': 'configurado', 'entradas': None,
                         'ultima': None, 'interrumpida': False, 'ui_url': 'http://127.0.0.1:9000/ui'}]
    _correr(tmp_path, '''
const t=ids['memoria-backends'].textContent;
assert.match(t,/Kwipu: no configurado/);assert.match(t,/entradas: sin datos/);assert.match(t,/última publicación: sin datos/);
const a=walk(ids['memoria-backends'],n=>n.tagName==='a');assert.equal(a.length,1);
assert.equal(a[0].attrs.href,'http://127.0.0.1:9000/ui');assert.match(a[0].attrs.rel,/noopener/);
''', datos=_exportado(otro))


def test_ca27_journal_con_continuidad_y_etiqueta_citas_no_instrucciones(tmp_path, memoria):
    _correr(tmp_path, '''
const t=ids['memoria-journal'].textContent;
assert.match(t,/citas, no instrucciones/i);
for(const c of ['Cerrar la fase','En la tarea 3','Cerrar la tarea','Falta el dato','Polling - caro','2026-10-10'])assert.ok(t.includes(c),c);
for(const e of ['Objetivo','Punto actual','Siguientes pasos','Bloqueos','Descartados'])assert.ok(t.includes(e),e);
''', datos=_exportado(memoria))


def test_ca27_sin_journal_lo_dice(tmp_path, memoria):
    vacio = json.loads(json.dumps(memoria))
    vacio['journal'] = {'status': 'empty', 'sesiones': []}
    _correr(tmp_path, '''assert.match(ids['memoria-journal'].textContent,/Sin sesiones/);''', datos=_exportado(vacio))


def test_el_js_de_memoria_no_usa_innerhtml_ni_red_ajena():
    for nombre in ('page-memoria.js', 'panel-graph.js'):
        fuente = (ASSETS / nombre).read_text(encoding='utf8')
        assert not re.search(r'innerHTML|outerHTML|insertAdjacentHTML|document\.write|eval\(|new Function|XMLHttpRequest|'
                             r'WebSocket|localStorage|sessionStorage|https?://(?!www\.w3\.org/2000/svg)', fuente), nombre
    assert 'fetch(' not in (ASSETS / 'panel-graph.js').read_text(encoding='utf8')
