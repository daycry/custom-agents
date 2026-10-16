"""Fase 4, ronda fix1 (F4-1, F4-3..F4-10): Memoria del panel. Datos genericos (`ana.perez@empresa.example`).

Cada test se escribio y se ejecuto contra el codigo ANTERIOR a la correccion (RED en el ledger). Lo que Python emite se
pasa por `PanelMemoria.validar` en Node: una fila anomala nunca invalida la pagina entera.
"""
import importlib.util
import json
import threading
import time
import types

import pytest

from memoria_fixture import crear_proyecto
from test_panel_inicio_ui import SCRIPTS
from test_panel_memoria_ui import IDS, _correr, _exportado, _panel_data

CORREO = 'ana.perez@empresa.example'
_DATOS = {'counts': dict.fromkeys(('agents', 'skills', 'commands', 'tools', 'hooks'), 0), 'agents': [], 'skills': [],
          'commands': [], 'tools': [], 'hooks': [], 'runtimes': {}, 'memory': {}, 'warnings': [], 'workflow': {'roles': {}}}


def _servicio():
    spec = importlib.util.spec_from_file_location('fix1_serve', SCRIPTS / 'serve_panel.py')
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _constructor():
    spec = importlib.util.spec_from_file_location('fix1_build', SCRIPTS / 'build_panel.py')
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _scrub(servicio, usuario='ana'):
    redact = servicio._load_shared('redact.py')
    return lambda t: redact.anonimizar(redact.redactar(t), None, '/home/' + usuario, usuario)


def _md(ruta, **fm):
    ruta.parent.mkdir(parents=True, exist_ok=True)
    cabecera = ''.join(f'{k}: {v}\n' for k, v in fm.items())
    ruta.write_text('---\n' + cabecera + '---\n\n# ' + str(fm.get('titulo', '')) + '\n\nCuerpo.\n', encoding='utf8')


def _valida_en_node(tmp_path, memoria):
    _correr(tmp_path, 'assert.equal(window.PanelMemoria.validar(' + json.dumps(memoria) + '), true, "validar rechaza lo que Python emite");',
            datos=_exportado(memoria))


def _backend(p, **extra):
    ks = p / '.claude/knowledge-services'
    config = json.loads((ks / 'taxonomy.json').read_text(encoding='utf8'))
    config['backends']['kwipu']['config'].update(extra)
    (ks / 'taxonomy.json').write_text(json.dumps(config), encoding='utf8')


# --- F4-1: iniciativa, sucesor e id por el mismo saneador ------------------------------------------------------------

def _con_correos(tmp_path):
    p = crear_proyecto(tmp_path)
    _md(p / 'docs/knowledge/adr/ADR-020-x.md', id='ADR-020', titulo='Con correo', estado='aceptada', fecha='2026-04-01',
        area='Datos', iniciativa=CORREO, sucesor=CORREO)
    return p


@pytest.mark.parametrize('relaciones', [False, True])
def test_f4_1_el_correo_en_iniciativa_y_sucesor_no_sale_en_claro_y_los_ids_cerrados_quedan(tmp_path, relaciones):
    servicio = _servicio()
    datos = _panel_data().memoria(_con_correos(tmp_path), relaciones=relaciones)
    limpio = servicio._scrub_memoria(datos, _scrub(servicio))
    crudo = json.dumps(limpio, ensure_ascii=False)
    assert 'ana.perez' not in crudo and 'empresa.example' not in crudo
    por_id = {e['id']: e for e in limpio['entradas']}
    assert por_id['ADR-001']['sustituida_por'] == ['ADR-002'] and por_id['ADR-003']['sustituye_a'] == ['ADR-002']
    assert por_id['ADR-020']['iniciativa'] == '<correo>'
    if relaciones:
        assert {'relacion': 'sustituida por', 'id': '<correo>', 'ausente': True} in limpio['relaciones']['ADR-020']['sucesion']


def test_f4_1_la_copia_exportada_no_lleva_el_correo_en_ningun_campo(tmp_path):
    servicio, constructor = _servicio(), _constructor()
    p = _con_correos(tmp_path)
    exportada = constructor._memoria_exportada(types.SimpleNamespace(project=str(p)), _scrub(servicio))
    assert exportada is not None and 'ana.perez' not in json.dumps(exportada, ensure_ascii=False)


def test_f4_1_el_servidor_no_sirve_el_correo(tmp_path, monkeypatch):
    servicio = _servicio()
    p = _con_correos(tmp_path)
    server = servicio.create_server(p, _DATOS, scrub=_scrub(servicio))
    try:
        server.memoria_panel()
        hilo = getattr(server, '_memoria_hilo', None)
        if hilo is not None:
            hilo.join(20)
        assert b'ana.perez' not in server.memoria_panel()
    finally:
        server.server_close()


# --- F4-3: journal incompleto -----------------------------------------------------------------------------------------

def _sesion(ruta, fecha, ident):
    ruta.write_text(f'---\nfecha: "{fecha}"\nsession_id: "{ident}"\nreason: "other"\niniciativa: "alfa"\nresumen: "Sesion {ident}"\n'
                    'fuente: "hook"\ncierre: "materializado"\nresumen_por: "determinista"\nturnos: 3\n'
                    'materializado_en: "' + fecha + 'T10:00:00Z"\ndecisiones:\n  - "Usar la cola"\n---\n\n# J\n', encoding='utf8')


def test_f4_3_un_frontmatter_roto_no_borra_las_sesiones_legibles(tmp_path):
    p = crear_proyecto(tmp_path)
    (p / 'docs/knowledge/journal/2026-10-11-roto.md').write_text('esto no es frontmatter\n', encoding='utf8')
    j = _panel_data().memoria(p)['journal']
    assert j['status'] == 'incomplete' and [s['fecha'] for s in j['sesiones']] == ['2026-10-10']


def test_f4_3_mas_de_128_ficheros_siguen_mostrando_sesiones(tmp_path):
    p = crear_proyecto(tmp_path)
    for n in range(1, 131):
        _sesion(p / f'docs/knowledge/journal/2026-09-{(n % 28) + 1:02d}-s{n:03d}.md', f'2026-09-{(n % 28) + 1:02d}', f's-{n}')
    j = _panel_data().memoria(p)['journal']
    assert j['status'] == 'incomplete' and len(j['sesiones']) >= 1


def test_f4_3_la_pagina_avisa_de_lista_incompleta_y_nunca_dice_sin_sesiones(tmp_path, memoria_base):
    con = json.loads(json.dumps(memoria_base))
    con['journal'] = {'status': 'incomplete', 'sesiones': con['journal']['sesiones']}
    _correr(tmp_path, '''const t=ids['memoria-journal'].textContent;
assert.match(t,/incompleta/i);assert.ok(t.includes('Cerrar la fase'));assert.ok(!/Sin sesiones registradas/.test(t));''', datos=_exportado(con))
    vacia = json.loads(json.dumps(memoria_base))
    vacia['journal'] = {'status': 'incomplete', 'sesiones': []}
    _correr(tmp_path, '''const t=ids['memoria-journal'].textContent;
assert.match(t,/incompleta/i);assert.ok(!/Sin sesiones registradas/.test(t));''', datos=_exportado(vacia))


@pytest.fixture
def memoria_base(tmp_path):
    return _panel_data().memoria(crear_proyecto(tmp_path / 'base'), relaciones=True)


# --- F4-4 / F4-10: ui_url solo local y nunca invalida la pagina --------------------------------------------------------

@pytest.mark.parametrize('url,local', [
    ('http://localhost:9000/ui', True), ('http://127.0.0.1:9000/ui', True), ('http://[::1]:9000/ui', True),
    ('http://kwipu.test/ui', True), ('http://192.168.1.5/ui', True), ('http://10.1.2.3:8080/', True),
    ('http://172.20.0.2/x', True), ('https://kwipu.example.com/ui', False), ('http://127.0.0.1.evil.example/ui', False),
    ('http://8.8.8.8/ui', False), ('http://172.32.0.1/ui', False)])
def test_f4_4_la_url_de_interfaz_solo_se_ofrece_si_el_host_es_local(tmp_path, url, local):
    p = crear_proyecto(tmp_path)
    _backend(p, ui_url=url)
    fila = next(b for b in _panel_data().memoria(p)['backends'] if b['backend'] == 'kwipu')
    assert (fila['ui_url'] == url) is local and fila['ui_url_no_local'] is (not local)


def test_f4_4_la_pagina_dice_host_no_local_y_no_enlaza_un_host_externo(tmp_path, memoria_base):
    otro = json.loads(json.dumps(memoria_base))
    for b in otro['backends']:
        b['ui_url'], b['ui_url_no_local'] = None, True
    otro['backends'][0]['ui_url'] = 'https://kwipu.example.com/ui'      # defensa en profundidad: aunque el dato llegue
    _correr(tmp_path, '''const t=ids['memoria-backends'].textContent;
assert.match(t,/interfaz: no declarada \\(host no local\\)/);
assert.equal(walk(ids['memoria-backends'],n=>n.tagName==='a').length,0);''', datos=_exportado(otro))


def test_f4_10_una_url_que_anonimizar_alarga_se_descarta_y_la_pagina_sigue_valida(tmp_path):
    servicio = _servicio()
    p = crear_proyecto(tmp_path)
    _backend(p, ui_url='http://localhost:9000/' + 'ana/' * 40)
    limpio = servicio._scrub_memoria(_panel_data().memoria(p), _scrub(servicio))
    fila = next(b for b in limpio['backends'] if b['backend'] == 'kwipu')
    assert fila['ui_url'] is None
    _valida_en_node(tmp_path, limpio)


# --- F4-5: relaciones recortadas ---------------------------------------------------------------------------------------

def _con_muchas_relaciones(tmp_path):
    p = crear_proyecto(tmp_path)
    for n in range(30):
        _md(p / f'docs/knowledge/lessons/LES-{n + 100:03d}-x.md', id=f'LES-{n + 100:03d}', titulo='L', estado='aceptada',
            fecha='2026-05-01', area='Datos / almacenamiento', iniciativa='alfa')
    return p


def test_f4_5_ningun_grupo_se_queda_sin_cupo_y_el_recorte_se_declara(tmp_path):
    rel = _panel_data().memoria(_con_muchas_relaciones(tmp_path), relaciones=True)['relaciones']['ADR-002']
    assert rel['recortado'] is True and rel['total'] > 20
    assert len(rel['sucesion']) + len(rel['por_iniciativa']) + len(rel['por_area']) + len(rel['enlaces']) == 20
    assert rel['sucesion'] and rel['por_iniciativa'] and rel['por_area']          # todos los grupos con relaciones tienen cupo


def test_f4_5_la_pagina_dice_se_muestran_n_de_m_y_si_la_lectura_es_incompleta(tmp_path):
    memoria = _panel_data().memoria(_con_muchas_relaciones(tmp_path), relaciones=True)
    _valida_en_node(tmp_path, memoria)
    _correr(tmp_path, '''const boton=walk(ids['memoria-tabla'],n=>n.tagName==='button'&&n.attrs['aria-label']==='Ver relaciones de ADR-002')[0];
boton.events.click[0]({});
assert.match(ids['memoria-relaciones-estado'].textContent,/se muestran 20 de \\d+ relaciones/);''', datos=_exportado(memoria))
    _correr(tmp_path, '''
const rel={version:1,source:'canonical_knowledge',operation:'related',status:'partial',complete:false,observed_at:'2026-10-16T10:00:00Z',
  selected:null,entries:[],related:{sucesion:[],iniciativa:[],area:[],enlaces:[]},issues:[],budget:{files:1,bytes:1,entries:1}};
const boton=walk(ids['memoria-tabla'],n=>n.tagName==='button'&&n.attrs['aria-label']==='Ver relaciones de ADR-002')[0];
await respond(DATOS);
walk(ids['memoria-tabla'],n=>n.tagName==='button'&&n.attrs['aria-label']==='Ver relaciones de ADR-002')[0].events.click[0]({});
await respond(rel);
assert.match(ids['memoria-relaciones-estado'].textContent,/incompleta/i);
'''.replace('DATOS', json.dumps(memoria)), datos={'pagina': 'memoria', 'modo': 'servido', 'chartjs_disponible': True})


# --- F4-6: lo que Python emite, JS lo acepta ---------------------------------------------------------------------------

def test_f4_6_un_id_duplicado_es_una_sola_fila_y_un_aviso(tmp_path):
    p = crear_proyecto(tmp_path)
    _md(p / 'docs/knowledge/adr/ADR-002-copia.md', id='ADR-002', titulo='Copia', estado='aceptada', fecha='2026-02-11', area='x')
    m = _panel_data().memoria(p, relaciones=True)
    assert [e['id'] for e in m['entradas']].count('ADR-002') == 1 and {'status': 'identidad_duplicada'} in m['issues']
    assert m['total'] == len(m['entradas']) == sum(sum(v.values()) for v in m['conteos'].values())
    _valida_en_node(tmp_path, m)


def test_f4_6_una_fecha_imposible_o_con_digitos_unicode_en_el_manifiesto_es_sin_datos(tmp_path):
    for malo in ('2026-13-45T10:00:00Z', '2026-02-30T10:00:00Z', '٢٠٢٦-١٠-٠٢T١١:٣٠:٠٠Z'):
        base = tmp_path / ('c' + str(abs(hash(malo))))
        p = crear_proyecto(base)
        for f in (p / '.claude/knowledge-services/_sync-outbox/kwipu/done').iterdir():
            f.unlink()
        (p / '.claude/knowledge-services/_sync-outbox/kwipu/done/sync-1.json.manifest.json').write_text(
            json.dumps({'completado_en': malo}), encoding='utf8')
        m = _panel_data().memoria(p)
        assert next(b for b in m['backends'] if b['backend'] == 'kwipu')['ultima'] is None, malo
        _valida_en_node(tmp_path, m)


def test_f4_6_una_fecha_de_entrada_con_digitos_unicode_o_imposible_es_sin_datos(tmp_path):
    p = crear_proyecto(tmp_path)
    _md(p / 'docs/knowledge/lessons/LES-060-u.md', id='LES-060', titulo='U', estado='aceptada', fecha='٢٠٢٦-٠١-٠١', area='x')
    _md(p / 'docs/knowledge/lessons/LES-061-i.md', id='LES-061', titulo='I', estado='aceptada', fecha='2026-13-45', area='x')
    m = _panel_data().memoria(p)
    por = {e['id']: e for e in m['entradas']}
    assert por['LES-060']['fecha'] is None and por['LES-061']['fecha'] is None
    _valida_en_node(tmp_path, m)


def test_f4_6_un_sucesor_largo_o_con_controles_se_sanea_y_se_recorta(tmp_path):
    p = crear_proyecto(tmp_path)
    _md(p / 'docs/knowledge/adr/ADR-030-l.md', id='ADR-030', titulo='L', estado='aceptada', fecha='2026-04-01', area='x',
        sucesor='S' * 400)
    _md(p / 'docs/knowledge/adr/ADR-031-c.md', id='ADR-031', titulo='C', estado='aceptada', fecha='2026-04-01', area='x',
        sucesor='ADR-9\x1f9')
    m = _panel_data().memoria(p, relaciones=True)
    por = {e['id']: e for e in m['entradas']}
    assert all(len(x) <= 256 for x in por['ADR-030']['sustituida_por']) and '\x1f' not in json.dumps(m)
    _valida_en_node(tmp_path, m)


def test_f4_6_los_separadores_unicode_son_controles():
    datos = _panel_data()
    assert datos._CONTROLES.search('a\u2028b') and datos._CONTROLES.search('a\u2029b')


def test_f4_6_un_sustituto_de_mas_de_16_etiquetas_no_invalida_la_pagina(tmp_path):
    p = crear_proyecto(tmp_path)
    for n in range(20):
        _md(p / f'docs/knowledge/adr/ADR-{200 + n}-s.md', id=f'ADR-{200 + n}', titulo='S', estado='aceptada',
            fecha='2026-04-01', area='x', sustituye=f'ADR-099')
    _md(p / 'docs/knowledge/adr/ADR-099-o.md', id='ADR-099', titulo='O', estado='obsoleta', fecha='2026-01-01', area='x')
    _valida_en_node(tmp_path, _panel_data().memoria(p, relaciones=True))


def test_f4_6_el_tipo_y_la_categoria_alargados_por_anonimizar_siguen_dentro_del_tope_de_la_pagina(tmp_path):
    servicio = _servicio()
    p = crear_proyecto(tmp_path)
    _backend(p)
    ks = p / '.claude/knowledge-services/taxonomy.json'
    config = json.loads(ks.read_text(encoding='utf8'))
    config['backends']['kwipu']['type'] = 'ana' * 13
    ks.write_text(json.dumps(config), encoding='utf8')
    (p / 'docs/knowledge/candidates/pending/2026-10-09-c.md').write_text('---\ncategory: ' + 'ana' * 13 + '\n---\n# C\n', encoding='utf8')
    limpio = servicio._scrub_memoria(_panel_data().memoria(p), _scrub(servicio))
    _valida_en_node(tmp_path, limpio)


# --- F4-7: ultima publicacion con listado truncado ---------------------------------------------------------------------

def test_f4_7_un_listado_truncado_marca_la_fecha_como_parcial(tmp_path):
    p = crear_proyecto(tmp_path)
    done = p / '.claude/knowledge-services/_sync-outbox/kwipu/done'
    for n in range(300):
        (done / f'sync-{n:04d}.json.manifest.json').write_text(json.dumps({'completado_en': '2026-01-01T00:00:00Z'}), encoding='utf8')
    kw = next(b for b in _panel_data().memoria(p)['backends'] if b['backend'] == 'kwipu')
    assert kw['ultima_parcial'] is True


def test_f4_7_un_listado_completo_no_es_parcial(tmp_path):
    kw = next(b for b in _panel_data().memoria(crear_proyecto(tmp_path))['backends'] if b['backend'] == 'kwipu')
    assert kw['ultima_parcial'] is False and kw['ultima'] == '2026-10-02T11:30:00Z'


def test_f4_7_la_pagina_dice_al_menos_si_es_parcial(tmp_path, memoria_base):
    otro = json.loads(json.dumps(memoria_base))
    otro['backends'][0]['ultima_parcial'] = True
    _correr(tmp_path, '''assert.match(ids['memoria-backends'].textContent,/al menos 2026-10-02T11:30:00Z/);''', datos=_exportado(otro))


# --- F4-8: filtro de area con el listado recortado ----------------------------------------------------------------------

def test_f4_8_con_recorte_el_filtro_de_area_dice_que_cuenta_solo_lo_mostrado(tmp_path, memoria_base):
    otro = json.loads(json.dumps(memoria_base))
    otro['recortado'], otro['total'], otro['status'], otro['complete'] = 2, len(otro['entradas']) + 2, 'partial', False
    _correr(tmp_path, '''assert.match(ids['memoria-area-nota'].textContent,/solo cuentan las \\d+ entradas mostradas de \\d+/);''',
            datos=_exportado(otro))
    _correr(tmp_path, '''assert.equal(ids['memoria-area-nota'].textContent,'');''', datos=_exportado(memoria_base))


# --- F4-9: api/memoria fuera del hilo de la peticion --------------------------------------------------------------------

@pytest.fixture
def servidor(tmp_path):
    servicio = _servicio()
    server = servicio.create_server(tmp_path, _DATOS)
    server.servicio = servicio
    yield server
    server.server_close()


def _memoria_con_puerta(servicio, monkeypatch, base):
    puerta, llamadas = threading.Event(), []

    def lenta(project, relaciones=False):
        llamadas.append(1)
        puerta.wait(5)
        return json.loads(json.dumps(base))
    monkeypatch.setattr(servicio, '_load_data', lambda: types.SimpleNamespace(memoria=lenta))
    return puerta, llamadas


def _esperar(server):
    hilo = getattr(server, '_memoria_hilo', None)
    if hilo is not None:
        hilo.join(10)
        assert not hilo.is_alive()


def test_f4_9_la_primera_peticion_responde_calculando_sin_esperar_y_luego_sirve_los_datos(servidor, monkeypatch, memoria_base):
    puerta, llamadas = _memoria_con_puerta(servidor.servicio, monkeypatch, memoria_base)
    antes = time.monotonic()
    primera = json.loads(servidor.memoria_panel())
    assert time.monotonic() - antes < 1
    assert primera['status'] == 'unavailable' and {'status': 'calculando'} in primera['issues']
    puerta.set(); _esperar(servidor)
    assert json.loads(servidor.memoria_panel())['status'] == 'ok' and len(llamadas) == 1


def test_f4_9_vencida_la_cache_sirve_la_vieja_con_un_solo_calculo_a_la_vez(servidor, monkeypatch, memoria_base):
    puerta, llamadas = _memoria_con_puerta(servidor.servicio, monkeypatch, memoria_base)
    puerta.set(); servidor.memoria_panel(); _esperar(servidor)
    vieja = servidor.memoria_panel()
    puerta.clear()
    servidor._memoria_at -= 60
    durante = servidor.memoria_panel()
    servidor._memoria_at -= 60
    servidor.memoria_panel()                                                   # no abre un segundo calculo
    assert durante == vieja and len(llamadas) == 2
    puerta.set(); _esperar(servidor)


def test_f4_9_un_recalculo_fallido_conserva_la_ultima_buena(servidor, monkeypatch, memoria_base):
    puerta, _ = _memoria_con_puerta(servidor.servicio, monkeypatch, memoria_base)
    puerta.set(); servidor.memoria_panel(); _esperar(servidor)
    vieja = json.loads(servidor.memoria_panel())

    def roto(project, relaciones=False):
        raise RuntimeError('PRIVADO')
    monkeypatch.setattr(servidor.servicio, '_load_data', lambda: types.SimpleNamespace(memoria=roto))
    servidor._memoria_at -= 60
    servidor.memoria_panel(); _esperar(servidor)
    despues = servidor.memoria_panel()
    assert json.loads(despues)['entradas'] == vieja['entradas'] and b'PRIVADO' not in despues


def test_f4_9_la_pagina_reintenta_sola_si_el_servidor_aun_calcula(tmp_path, memoria_base):
    calculando = {**memoria_base, 'status': 'unavailable', 'complete': False, 'entradas': [], 'total': 0,
                  'issues': [{'status': 'calculando'}], 'relaciones': None}
    calculando.pop('relaciones')
    _correr(tmp_path, '''
await respond(CALC);
assert.match(ids['memoria-estado'].textContent,/Calculando/);
fire(3000);
await respond(DATOS);
assert.ok(!/Calculando/.test(ids['memoria-estado'].textContent));assert.ok(ids['memoria-tabla'].children.length>0);
'''.replace('CALC', json.dumps(calculando)).replace('DATOS', json.dumps({k: v for k, v in memoria_base.items() if k != 'relaciones'})),
            datos={'pagina': 'memoria', 'modo': 'servido', 'chartjs_disponible': True})


# --- F4-10: la bandeja se recorta, no tira la respuesta ------------------------------------------------------------------

def test_f4_10_una_bandeja_demasiado_larga_se_recorta_antes_de_dejar_la_respuesta_no_disponible(memoria_base):
    datos = _panel_data()
    m = json.loads(json.dumps(memoria_base))
    m['entradas'], m['total'] = [], 0
    item = {'candidato': '\U0001F600' * 160, 'titular': '\U0001F600' * 160, 'category': 'X'}
    for e in ('pending', 'needs_changes', 'rejected'):
        m['bandeja']['estados'][e] = {'situacion': 'ok', 'n': 20, 'items': [dict(item) for _ in range(20)]}
    m['bandeja']['aprobadas'] = {'n': 20, 'items': [{'id': 'ADR-%03d' % n, 'titular': '\U0001F600' * 160, 'area': '\U0001F600' * 160}
                                                    for n in range(20)]}
    assert len(json.dumps(m, ensure_ascii=False).encode('utf8')) > 65536
    r = datos.ajustar_memoria(m, 65536)
    assert len(json.dumps(r, ensure_ascii=False).encode('utf8')) <= 65536 and r['status'] == 'partial'
    assert {'status': 'output_budget'} in r['issues']
    assert all(e['n'] == 20 for e in r['bandeja']['estados'].values()) and r['bandeja']['aprobadas']['n'] == 20   # el total sigue siendo el real
