"""T-23 y T-24: página Plan por iniciativa (`plan-<id16>.html`), `api/plan-<id16>` y `api/plan-<id16>-<T-XX>`.

Tres capas, igual que `test_panel_inicio_ui.py`: la proyección (`panel_data.plan`/`tarea`, sobre la fixture de T-01 y
`ledger-view.py`), el servidor y el exportador reales, y el JS de la página en Node con un DOM falso alimentado con
la respuesta REAL de la proyección.
"""
import hashlib
import http.client
import importlib.util
import json
from pathlib import Path
import re
import shutil
import subprocess
import threading

import pytest

from test_panel_fix3 import SENSIBLES, _scrub
from test_panel_inicio_ui import ASSETS, HARNESS, ROOT, SCRIPTS, proyecto  # noqa: F401
from test_panel_live_ui import inventory, panel  # noqa: F401
from test_panel_server import request

BUNDLE = ROOT / 'tests/fixtures/panel-redesign/bundle'
VOCABULARIO = ['borrador', 'en-progreso', 'en-revision', 'completado', 'cancelado']


def id16(carpeta):
    return hashlib.sha256(carpeta.encode('utf8')).hexdigest()[:16]


ALFA, GAMMA, BETA, EPSILON, IOTA = (id16(c) for c in (
    '2026-01-10-alfa', '2026-01-12-gamma', '2026-01-11-beta', '2026-01-14-epsilon', '2026-01-16-iota'))


def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope='module')
def datos():
    return _cargar('panel_data_plan', SCRIPTS / 'panel_data.py')


@pytest.fixture(scope='module')
def servicio():
    return _cargar('serve_panel_plan', SCRIPTS / 'serve_panel.py')


@pytest.fixture(scope='module')
def proyecto_plan(proyecto, tmp_path_factory):
    """La fixture de T-01 más dos iniciativas con plan que cubren los casos del ledger: uno fuera del tope de lectura
    (epsilon, > 256 KiB) y uno ilegible (iota: bytes que no son UTF-8)."""
    destino = tmp_path_factory.mktemp('plan') / 'proyecto'
    shutil.copytree(proyecto, destino)
    raiz = destino / 'docs/roadmap'
    (raiz / '2026-01-14-epsilon/improvement-plan.md').write_text('# Plan de epsilon\n', encoding='utf8')
    iota = raiz / '2026-01-16-iota'
    iota.mkdir()
    (iota / 'improvement-plan.md').write_text('# Plan de iota\n', encoding='utf8')
    (iota / 'tasks.md').write_bytes(b'# Iota \x80\x81\n\n### T-01 \xe9\n- **Estado**: borrador\n')
    return destino


@pytest.fixture(scope='module')
def servidor(servicio, proyecto_plan):
    inventario = servicio._load_builder().build_inventory(proyecto_plan, project=None)
    server = servicio.create_server(proyecto_plan, inventario, scrub=_scrub(servicio))
    hilo = threading.Thread(target=server.serve_forever, daemon=True)
    hilo.start()
    yield server
    server.shutdown(); server.server_close(); hilo.join(timeout=5)


# --- proyección: panel_data.plan --------------------------------------------------------------------------------

CLAVES_PLAN = {'version', 'source', 'status', 'complete', 'observed_at', 'id', 'slug', 'issues', 'vocabulario',
               'omitidas', 'tareas'}
CLAVES_FILA = {'id', 'titulo', 'fase_nombre', 'estado_tarea', 'literal', 'horas', 'gaps'}


def test_plan_proyecta_solo_lo_del_kanban_con_su_contrato(datos, proyecto_plan):
    r = datos.plan(proyecto_plan, ALFA)
    assert set(r) == CLAVES_PLAN and r['source'] == 'ledger_plan' and r['version'] == 1
    assert r['status'] == 'ok' and r['complete'] is True and r['id'] == ALFA and r['slug'] == '2026-01-10-alfa'
    assert r['vocabulario'] == VOCABULARIO and r['omitidas'] == 0
    assert [t['id'] for t in r['tareas']] == ['T-01', 'T-02']
    assert all(set(t) == CLAVES_FILA for t in r['tareas'])
    t1, t2 = r['tareas']
    assert (t1['estado_tarea'], t2['estado_tarea']) == ('completado', 'en-progreso')
    assert t1['gaps'] == 0 and t2['gaps'] == 2                     # el detalle va por api/plan-<id>-<T-XX> (T-24)
    assert t1['fase_nombre'] == 'Fase 1' and t1['horas'] == {'real': None, 'est': None, 'fuente': None}
    assert t1['literal'] is None


def test_un_estado_fuera_del_vocabulario_va_a_su_franja_con_el_literal(datos, tmp_path):
    carpeta = tmp_path / 'docs/roadmap/2026-02-01-zz'
    carpeta.mkdir(parents=True)
    (carpeta / 'improvement-plan.md').write_text('# p\n', encoding='utf8')
    (carpeta / 'tasks.md').write_text('# L\n\n## Fase 1\n\n### T-01 — a\n- **Estado**: 🚧 Bloqueada\n\n'
                                      '### T-02 — b\n- **Estado**: completado\n', encoding='utf8')
    r = datos.plan(tmp_path, id16('2026-02-01-zz'))
    t1, t2 = r['tareas']
    assert t1['estado_tarea'] is None and t1['literal'] == 'bloqueada' and t2['estado_tarea'] == 'completado'


def test_ledger_fuera_del_tope_ilegible_y_ausente_dicen_su_estado_sin_cifras(datos, proyecto_plan, tmp_path):
    for ident, estado in ((EPSILON, 'fuera_de_tope'), (IOTA, 'ilegible'), (BETA, 'sin_ledger')):
        r = datos.plan(proyecto_plan, ident)
        assert r['status'] == estado and r['tareas'] is None and r['complete'] is False, ident
        assert set(r) == CLAVES_PLAN


def test_un_id_desconocido_o_mal_formado_no_se_resuelve(datos, proyecto_plan):
    assert datos.plan(proyecto_plan, '0' * 16) is None
    for malo in ('', 'zz', 'A' * 16, '../' + 'a' * 13, 'a' * 17, None, 7):
        assert datos.plan(proyecto_plan, malo) is None


def test_la_proyeccion_no_lee_execution_history(datos, proyecto_plan):
    assert (proyecto_plan / 'docs/roadmap/2026-01-12-gamma/execution-history.md').is_file()
    assert 'execution-history' not in json.dumps(datos.plan(proyecto_plan, GAMMA))


# --- servidor: páginas por iniciativa y api/plan-<id16> ------------------------------------------------------------

def _json(servidor, sufijo):
    estado, cabeceras, cuerpo = request(servidor, sufijo)
    return estado, cabeceras, cuerpo, (json.loads(cuerpo) if cuerpo[:1] == b'{' else None)


def test_api_plan_sirve_el_kanban_de_una_iniciativa_con_plan(servidor):
    estado, cabeceras, cuerpo, r = _json(servidor, f'api/plan-{ALFA}')
    assert estado == 200 and cabeceras['Content-Type'] == 'application/json; charset=utf-8'
    assert len(cuerpo) < 64 * 1024 and r['id'] == ALFA and [t['id'] for t in r['tareas']] == ['T-01', 'T-02']
    assert cabeceras['Cache-Control'] == 'no-store'
    assert servidor.access_prefix.encode() not in cuerpo


@pytest.mark.parametrize('sufijo', [f'api/plan-{BETA}', f'api/plan-{"0" * 16}', 'api/plan-', 'api/plan-xyz',
                                    f'api/plan-{ALFA}x', f'api/plan-{ALFA.upper()}', f'api/plan-{ALFA}/', 'api/plan',
                                    f'api/plan-{ALFA}?x=1', f'api/plan-{ALFA}-', f'api/plan-{ALFA}-T-', 'api/plan-' + 'a' * 17])
def test_api_plan_solo_responde_a_las_iniciativas_con_plan_del_inventario(servidor, sufijo):
    assert request(servidor, sufijo)[0] in (404, 405)


def test_api_plan_rechaza_metodos_que_escriben_y_origenes_ajenos(servidor):
    assert request(servidor, f'api/plan-{ALFA}', method='POST')[0] in (405, 400, 415)
    assert request(servidor, f'api/plan-{ALFA}', method='PUT')[0] == 405
    assert request(servidor, f'api/plan-{ALFA}', headers={'Origin': 'https://fuera.invalid'})[0] == 403
    assert request(servidor, f'api/plan-{ALFA}', headers={'Host': 'fuera.invalid'})[0] == 403


def test_api_plan_de_un_ledger_fuera_del_tope_o_ilegible_responde_su_estado(servidor):
    for ident, estado in ((EPSILON, 'fuera_de_tope'), (IOTA, 'ilegible')):
        s, _, _, r = _json(servidor, f'api/plan-{ident}')
        assert s == 200 and r['status'] == estado and r['tareas'] is None and r['complete'] is False


def test_las_paginas_plan_por_iniciativa_se_llenan_desde_el_inventario(servidor):
    esperadas = {f'plan-{i}.html' for i in (ALFA, GAMMA, EPSILON, IOTA)}
    assert set(servidor.plan_pages) == esperadas
    for nombre in esperadas:
        estado, cabeceras, cuerpo = request(servidor, nombre)
        assert estado == 200 and cabeceras['Content-Type'] == 'text/html; charset=utf-8'
        html = cuerpo.decode('utf8')
        assert 'id="kanban-plan"' in html and 'id="plan-estado"' in html
        nonce = re.search(r"script-src 'nonce-([A-Za-z0-9_-]+)'", cabeceras['Content-Security-Policy']).group(1)
        etiquetas = re.findall(r'<script\b[^>]*>', html)
        assert etiquetas and all(f'nonce="{nonce}"' in e for e in etiquetas)
        orden = re.findall(r'<script nonce="[^"]+" src="([^"]+)"', html)
        assert orden[-2:] == ['assets/page-cartera.js', 'assets/page-plan.js']
        assert not any('panel-live' in s or 'panel-review' in s for s in orden)
        bruto = re.search(r'id="panel-data">(.*?)</script>', html, re.S).group(1)
        d = json.loads(bruto)
        assert d['plan_id'] == nombre[5:21] and d['modo'] == 'servido' and 'plan' not in d and '<' not in bruto
    assert request(servidor, f'plan-{BETA}.html')[0] == 404              # beta no tiene plan


def test_el_indice_plan_enlaza_las_paginas_de_las_iniciativas_con_plan(servidor):
    html = request(servidor, 'plan.html')[2].decode('utf8')
    enlaces = re.findall(r'href="(plan-[a-f0-9]{16}\.html)"', html)
    assert sorted(enlaces) == sorted(f'plan-{i}.html' for i in (ALFA, GAMMA, EPSILON, IOTA))
    assert '2026-01-10-alfa' in html and f'plan-{BETA}.html' not in html
    assert 'aria-label="Planes por iniciativa"' in html


def test_el_enlace_de_la_tarjeta_de_iniciativas_ya_no_da_404(servidor):
    html = request(servidor, 'iniciativas.html')[2].decode('utf8')
    assert request(servidor, f'plan-{ALFA}.html')[0] == 200 and html            # el destino de T-19 existe


def test_las_paginas_plan_no_leen_disco_por_peticion(servidor, monkeypatch):
    import builtins
    monkeypatch.setattr(builtins, 'open', lambda *a, **k: pytest.fail('lectura de disco al servir'))
    monkeypatch.setattr(Path, 'read_bytes', lambda *a, **k: pytest.fail('lectura de disco al servir'))
    monkeypatch.setattr(Path, 'read_text', lambda *a, **k: pytest.fail('lectura de disco al servir'))
    assert request(servidor, f'plan-{ALFA}.html')[0] == 200 and request(servidor, 'plan.html')[0] == 200


def _servir_proyecto(servicio, proyecto, scrub=None):
    inventario = servicio._load_builder().build_inventory(proyecto, project=None)
    server = servicio.create_server(proyecto, inventario, scrub=scrub)
    hilo = threading.Thread(target=server.serve_forever, daemon=True)
    hilo.start()
    return server, hilo


def _parar(server, hilo):
    server.shutdown(); server.server_close(); hilo.join(timeout=5)


def _proyecto_con(tmp_path, carpeta, ledger):
    d = tmp_path / 'docs/roadmap' / carpeta
    d.mkdir(parents=True)
    (d / 'improvement-plan.md').write_text('# plan\n', encoding='utf8')
    (d / 'tasks.md').write_text(ledger, encoding='utf8')
    return tmp_path


def test_api_plan_anonimiza_el_texto_mostrado_con_el_saneador_unico(servicio, tmp_path):
    plantado = 'jdoeuser /home/jdoeuser/notas jdoe@example.org'
    proyecto = _proyecto_con(tmp_path, '2026-03-01-uno', f'# L\n\n## Fase 1 — {plantado}\n\n### T-01 — {plantado}\n- **Estado**: completado\n')
    server, hilo = _servir_proyecto(servicio, proyecto, _scrub(servicio))
    try:
        s, _, cuerpo, r = _json(server, 'api/plan-' + id16('2026-03-01-uno'))
    finally:
        _parar(server, hilo)
    texto = json.dumps(r, ensure_ascii=False)
    assert s == 200 and r['tareas'][0]['id'] == 'T-01'
    for sensible in SENSIBLES:
        assert sensible not in texto, sensible
    assert '<usuario>' in r['tareas'][0]['titulo'] and '<usuario>' in r['tareas'][0]['fase_nombre']
    assert len(r['tareas'][0]['titulo']) <= 160 and len(r['tareas'][0]['fase_nombre']) <= 160


def test_api_plan_de_un_ledger_enorme_recorta_con_indicador_y_pesa_menos_de_64_kib(servicio, tmp_path):
    filas = ''.join(f'### T-{n:03d} — ' + ('título largo ñ ' * 12)[:160] + '\n- **Estado**: borrador\n\n' for n in range(1, 700))
    proyecto = _proyecto_con(tmp_path, '2026-03-02-grande', '# L\n\n## Fase 1 — ' + 'F' * 150 + '\n\n' + filas)
    server, hilo = _servir_proyecto(servicio, proyecto, _scrub(servicio))
    try:
        s, _, cuerpo, r = _json(server, 'api/plan-' + id16('2026-03-02-grande'))
    finally:
        _parar(server, hilo)
    assert s == 200 and len(cuerpo) <= 65536
    assert r['status'] == 'partial' and r['complete'] is False and r['omitidas'] > 0
    assert len(r['tareas']) + r['omitidas'] == 699 and {'status': 'output_budget'} in r['issues']


# --- exportado: una página por iniciativa con plan -----------------------------------------------------------------

@pytest.fixture(scope='module')
def exportado(proyecto_plan, tmp_path_factory):
    build = _cargar('build_panel_plan', SCRIPTS / 'build_panel.py')
    destino = tmp_path_factory.mktemp('salida-plan') / 'sitio'
    assert build.main(['--root', str(BUNDLE), '--project', str(proyecto_plan), '--export', str(destino)]) == 0
    return destino


def _datos_pagina(html):
    return json.loads(re.search(r'id="panel-data">(.*?)</script>', html, re.S).group(1))


def test_el_exportado_escribe_una_pagina_plan_por_iniciativa_con_plan_y_la_declara_en_el_manifiesto(exportado):
    esperadas = {f'plan-{i}.html' for i in (ALFA, GAMMA, EPSILON, IOTA)}
    assert esperadas <= {p.name for p in exportado.glob('plan-*.html')} and len(list(exportado.glob('plan-*.html'))) == 4
    manifiesto = json.loads((exportado / 'export-manifest.json').read_text(encoding='utf8'))
    assert esperadas <= {f['ruta'] for f in manifiesto['ficheros']} and 'assets/page-plan.js' in {f['ruta'] for f in manifiesto['ficheros']}
    html = (exportado / f'plan-{ALFA}.html').read_text(encoding='utf8')
    assert "script-src 'self' file:" in html and 'api/' not in html and 'id="kanban-plan"' in html
    d = _datos_pagina(html)
    assert d['modo'] == 'exportado' and d['plan_id'] == ALFA and d['plan']['id'] == ALFA
    assert [t['id'] for t in d['plan']['tareas']] == ['T-01', 'T-02'] and '<' not in re.search(r'id="panel-data">(.*?)</script>', html, re.S).group(1)
    assert _datos_pagina((exportado / f'plan-{EPSILON}.html').read_text(encoding='utf8'))['plan']['status'] == 'fuera_de_tope'
    assert _datos_pagina((exportado / f'plan-{IOTA}.html').read_text(encoding='utf8'))['plan']['status'] == 'ilegible'
    orden = re.findall(r'<script[^>]*\ssrc="([^"]+)"', html)
    assert orden[-2:] == ['assets/page-cartera.js', 'assets/page-plan.js'] and not any('panel-live' in s for s in orden)


def test_el_indice_plan_exportado_enlaza_cada_plan_y_la_copia_sin_project_lo_dice(exportado, tmp_path):
    html = (exportado / 'plan.html').read_text(encoding='utf8')
    assert sorted(re.findall(r'href="(plan-[a-f0-9]{16}\.html)"', html)) == sorted(f'plan-{i}.html' for i in (ALFA, GAMMA, EPSILON, IOTA))
    build = _cargar('build_panel_plan_sin', SCRIPTS / 'build_panel.py')
    assert build.main(['--root', str(BUNDLE), '--export', str(tmp_path / 'sin')]) == 0
    sin = (tmp_path / 'sin/plan.html').read_text(encoding='utf8')
    assert 'esta copia estática no incluye los planes' in sin.lower() and not list((tmp_path / 'sin').glob('plan-*.html'))
    assert not re.findall(r'href="plan-[a-f0-9]{16}\.html"', sin)


def test_un_segundo_exportado_no_deja_paginas_plan_obsoletas(proyecto_plan, tmp_path):
    build = _cargar('build_panel_plan_dos', SCRIPTS / 'build_panel.py')
    destino = tmp_path / 'sitio'
    proyecto = tmp_path / 'p'
    shutil.copytree(proyecto_plan, proyecto)
    assert build.main(['--root', str(BUNDLE), '--project', str(proyecto), '--export', str(destino)]) == 0
    assert (destino / f'plan-{IOTA}.html').is_file()
    shutil.rmtree(proyecto / 'docs/roadmap/2026-01-16-iota')
    assert build.main(['--root', str(BUNDLE), '--project', str(proyecto), '--export', str(destino)]) == 0
    assert not (destino / f'plan-{IOTA}.html').exists() and (destino / f'plan-{ALFA}.html').is_file()


# --- JS de la página en Node ----------------------------------------------------------------------------------------

LIBRES = '''
const columnas=()=>walk(ids['kanban-plan'],n=>n.className.split(' ').includes('columna'));
const tarjetas=(col)=>walk(col,n=>n.tagName==='article');
const porTitulo=()=>Object.fromEntries(columnas().map(c=>[tag(c,'h2')[0].textContent,tarjetas(c)]));
const tarjetaDe=(id)=>walk(ids['kanban-plan'],n=>n.tagName==='article'&&n.dataset.id===id)[0];
'''


def _correr(tmp_path, cuerpo, *, datos_pagina, extra=''):
    node = shutil.which('node')
    if not node:
        pytest.skip('Node no disponible para el arnés de page-plan.js')
    fuentes = ''.join((ASSETS / n).read_text(encoding='utf8') for n in ('panel-core.js', 'page-cartera.js', 'page-plan.js'))
    programa = (HARNESS.replace('IDS', json.dumps(list(IDS))) + extra + '\nponerDatos(' + json.dumps(datos_pagina) + ');\n' + fuentes
                + '\n(async()=>{' + cuerpo + '})().catch(e=>{console.error(e);process.exitCode=1;});')
    fuente = tmp_path / 'plan.cjs'
    fuente.write_text(programa, encoding='utf8')
    r = subprocess.run([node, str(fuente)], capture_output=True, text=True, encoding='utf8', errors='replace', timeout=30)
    assert r.returncode == 0, r.stdout + r.stderr


def _exportado_con(plan, **extra):
    return {'pagina': 'plan', 'modo': 'exportado', 'plan_id': plan['id'], 'chartjs_disponible': True, 'plan': plan, **extra}


def _servido(ident):
    return {'pagina': 'plan', 'modo': 'servido', 'plan_id': ident, 'chartjs_disponible': True}


@pytest.fixture(scope='module')
def plan_alfa(datos, proyecto_plan):
    return datos.plan(proyecto_plan, ALFA)


def _plan_con(plan, tareas, **cambios):
    nuevo = json.loads(json.dumps(plan))
    nuevo['tareas'] = tareas
    nuevo.update(cambios)
    return nuevo


def _fila(ident, estado, titulo='t', literal=None, real=None, est=None, fuente=None, gaps=0, fase='Fase 1'):
    return {'id': ident, 'titulo': titulo, 'fase_nombre': fase, 'estado_tarea': estado, 'literal': literal,
            'horas': {'real': real, 'est': est, 'fuente': fuente}, 'gaps': gaps}


def test_el_kanban_tiene_exactamente_las_cinco_columnas_del_vocabulario_y_una_tarjeta_por_tarea(tmp_path, plan_alfa):
    _correr(tmp_path, LIBRES + '''
const cols=porTitulo();
assert.deepEqual(Object.keys(cols),['Borrador (0)','En progreso (1)','En revisión (0)','Completado (1)','Cancelado (0)']);
assert.equal(walk(ids['kanban-plan'],n=>n.tagName==='article').length,2);
assert.equal(tarjetas(columnas()[3])[0].dataset.id,'T-01');assert.equal(tarjetas(columnas()[1])[0].dataset.id,'T-02');
const vacia=walk(columnas()[0],n=>n.className==='columna-vacia');assert.equal(vacia.length,1);assert.match(vacia[0].textContent,/Ninguna tarea/);
assert.equal(columnas().filter(c=>c.className.includes('desconocidos')).length,0,'sin franja si no hay desconocidos');
''', datos_pagina=_exportado_con(plan_alfa))


def test_la_tarjeta_muestra_id_titulo_fase_horas_con_procedencia_y_gaps(tmp_path, plan_alfa):
    plan = _plan_con(plan_alfa, [_fila('T-01', 'completado', 'Primera', real=1.03, est=0.5, fuente='medido'),
                                 _fila('T-02', 'en-progreso', 'Segunda', real=0.2, est=None, fuente='estimado', gaps=2),
                                 _fila('T-03', 'borrador', 'Tercera', fase=None)])
    _correr(tmp_path, LIBRES + '''
const a=tarjetaDe('T-01').textContent,b=tarjetaDe('T-02').textContent,c=tarjetaDe('T-03').textContent;
assert.match(a,/T-01/);assert.match(a,/Primera/);assert.match(a,/Fase: Fase 1/);
assert.match(a,/Horas IA: real 1,03 h \\(medido\\) · estimado 0,50 h/);assert.match(a,/Gaps de revisión abiertos: 0/);
assert.match(b,/real 0,20 h \\(estimado\\) · estimado sin datos/);assert.match(b,/Gaps de revisión abiertos: 2/);
assert.match(c,/Fase: sin datos/);assert.match(c,/real sin datos · estimado sin datos/);
assert.ok(!/ 0 h|0,00/.test(c),'lo ausente no se pinta como 0');
''', datos_pagina=_exportado_con(plan))


def test_un_estado_no_reconocido_va_a_su_franja_con_el_literal_y_no_a_las_cinco_columnas(tmp_path, plan_alfa):
    plan = _plan_con(plan_alfa, [_fila('T-01', None, 'Rara', literal='bloqueada-por-terceros'),
                                 _fila('T-02', None, 'Sin campo', literal=None), _fila('T-03', 'completado')])
    _correr(tmp_path, LIBRES + '''
const cols=porTitulo();
assert.deepEqual(Object.keys(cols),['Borrador (0)','En progreso (0)','En revisión (0)','Completado (1)','Cancelado (0)','Estado no reconocido (2)']);
const franja=columnas().find(c=>c.className.includes('desconocidos'));
assert.match(tarjetas(franja)[0].textContent,/Estado: «bloqueada-por-terceros»/);
assert.match(tarjetas(franja)[1].textContent,/Estado: sin estado/);
''', datos_pagina=_exportado_con(plan))


@pytest.mark.parametrize('estado,texto', [
    ('fuera_de_tope', 'Ledger fuera del tope de lectura (256 KiB)'), ('ilegible', 'Ledger no legible'),
    ('sin_ledger', 'no tiene ledger'), ('sin_tareas', 'no contiene tareas reconocibles'),
    ('sin_lectura', 'No se pudo leer el ledger')])
def test_un_ledger_que_no_se_puede_mostrar_dice_su_motivo_sin_cifras_ni_tarjetas(tmp_path, plan_alfa, estado, texto):
    plan = _plan_con(plan_alfa, None, status=estado, complete=False)
    _correr(tmp_path, f'''
assert.ok(ids['plan-estado'].textContent.includes({json.dumps(texto)}),ids['plan-estado'].textContent);
assert.equal(walk(ids['kanban-plan'],n=>n.tagName==='article').length,0);
assert.ok(!/[0-9]+ tareas/.test(ids['plan-estado'].textContent),'sin cifras');
assert.ok(ids['kanban-plan'].textContent.length>0,'el tablero dice que no hay datos');
''', datos_pagina=_exportado_con(plan))


def test_una_respuesta_recortada_por_el_presupuesto_lo_dice(tmp_path, plan_alfa):
    plan = _plan_con(plan_alfa, [_fila('T-01', 'borrador')], status='partial', complete=False, omitidas=41)
    _correr(tmp_path, '''
assert.match(ids['plan-estado'].textContent,/41 tareas omitidas/);assert.match(ids['plan-estado'].textContent,/no acredita ausencia/);
assert.equal(walk(ids['kanban-plan'],n=>n.tagName==='article').length,1);
''', datos_pagina=_exportado_con(plan))


@pytest.mark.parametrize('rompe', [
    lambda p: p.update(vocabulario=['borrador']), lambda p: p.update(source='otra'),
    lambda p: p['tareas'][0].update(estado_tarea='inventado'), lambda p: p['tareas'][0].update(titulo='x' * 161),
    lambda p: p['tareas'][0].update(horas={'real': -1, 'est': None, 'fuente': None}),
    lambda p: p['tareas'][0].update(id='T-1; drop'), lambda p: p['tareas'].append(dict(p['tareas'][0])),
    lambda p: p.update(id='zz'), lambda p: p['tareas'][0].pop('gaps')])
def test_una_respuesta_fuera_de_contrato_no_se_pinta(tmp_path, plan_alfa, rompe):
    plan = json.loads(json.dumps(plan_alfa))
    rompe(plan)
    _correr(tmp_path, '''
assert.equal(walk(ids['kanban-plan'],n=>n.tagName==='article').length,0);
assert.match(ids['plan-estado'].textContent,/No se pudo leer el plan/);
''', datos_pagina=_exportado_con(plan))


def test_exportado_sin_datos_incrustados_dice_que_no_hay_datos(tmp_path):
    _correr(tmp_path, '''
assert.match(ids['plan-estado'].textContent,/Sin datos/);assert.equal(walk(ids['kanban-plan'],n=>n.tagName==='article').length,0);
''', datos_pagina={'pagina': 'plan', 'modo': 'exportado', 'plan_id': ALFA, 'chartjs_disponible': True})


def test_servido_pide_api_plan_con_ruta_relativa_sin_credenciales_y_pinta(tmp_path, plan_alfa):
    _correr(tmp_path, '''
assert.equal(requests.length,1);assert.equal(requests[0].url,'api/plan-'+ID);
assert.equal(requests[0].options.credentials,'omit');assert.equal(requests[0].options.cache,'no-store');
await respond(PLAN);
assert.equal(walk(ids['kanban-plan'],n=>n.tagName==='article').length,2);
assert.match(ids['plan-estado'].textContent,/2026-01-10-alfa/);
'''.replace('ID', json.dumps(ALFA)).replace('PLAN', json.dumps(plan_alfa)), datos_pagina=_servido(ALFA))


def test_servido_con_respuesta_invalida_o_caida_no_inventa_datos(tmp_path, plan_alfa):
    _correr(tmp_path, '''
await respond({version:1,source:'ledger_plan'});
assert.equal(walk(ids['kanban-plan'],n=>n.tagName==='article').length,0);
assert.match(ids['plan-estado'].textContent,/No se pudo leer el plan/);
''', datos_pagina=_servido(ALFA))


def test_page_plan_no_inserta_html_ni_usa_eval_ni_red_salvo_api_plan():
    js = (ASSETS / 'page-plan.js').read_text(encoding='utf8')
    assert 'innerHTML' not in js and 'insertAdjacentHTML' not in js and 'eval(' not in js and 'document.write' not in js
    assert 'draggable' not in js and 'dragstart' not in js
    assert js.count('.fetch(') == 2 and "'api/plan-'" in js           # el plan y el detalle de una tarea
    assert 'http://' not in js and 'https://' not in js


# =====================================================================================================================
# T-24: api/plan-<id16>-<T-XX> y detalle de tarea accesible
# =====================================================================================================================

CLAVES_ENV = {'version', 'source', 'status', 'complete', 'observed_at', 'id', 'tarea_id', 'issues', 'omitidos', 'tarea'}
CLAVES_TAREA = {'id', 'titulo', 'fase_nombre', 'estado_tarea', 'literal', 'descripcion', 'criterios', 'verificacion',
                'verificacion_recortada', 'ejecutada', 'salida', 'dependencias', 'archivado', 'cerrada', 'horas',
                'revision', 'gaps'}
MARCADOR_HISTORIAL = 'MARCADOR-SOLO-DEL-HISTORIAL-ARCHIVADO'


@pytest.fixture(scope='module', autouse=True)
def _historial_con_marcador(proyecto_plan):
    """El histórico de gamma lleva un marcador único: si alguna respuesta lo contiene, se mezcló con el ledger (CA-10)."""
    ruta = proyecto_plan / 'docs/roadmap/2026-01-12-gamma/execution-history.md'
    ruta.write_text(ruta.read_text(encoding='utf8') + '\n' + MARCADOR_HISTORIAL + ' T-01\n', encoding='utf8')


def test_tarea_proyecta_el_detalle_con_su_contrato(datos, proyecto_plan):
    r = datos.tarea(proyecto_plan, ALFA, 'T-02')
    assert set(r) == CLAVES_ENV and r['source'] == 'ledger_tarea' and r['status'] == 'ok' and r['complete'] is True
    assert r['id'] == ALFA and r['tarea_id'] == 'T-02' and r['omitidos'] == {'criterios': 0, 'gaps': 0}
    t = r['tarea']
    assert set(t) == CLAVES_TAREA and t['id'] == 'T-02' and t['titulo'] == 'Segunda tarea'
    assert t['estado_tarea'] == 'en-progreso' and t['literal'] is None and t['fase_nombre'] == 'Fase 1'
    assert t['criterios'] == [{'criterio': 'Pendiente.', 'marcado': False}]
    assert t['verificacion'] == '`pytest -q` → `passed`' and t['verificacion_recortada'] is False
    assert t['dependencias'] == [] and t['archivado'] is None and t['cerrada'] is None
    assert t['revision']['intento'] == 1 and t['revision']['abiertos'] == 2 and 'gaps abiertos' in t['revision']['cabecera']
    assert [(g['grado'], g['gap']) for g in t['gaps']] == [('Important', 'Falta validar la entrada vacía'),
                                                          ('Minor', 'Mensaje de error poco claro')]
    assert all(set(g) == {'intento', 'num', 'grado', 'gap', 'correccion'} for g in t['gaps'])
    assert set(t['horas']) == {'ia', 'supervision', 'humano'}
    t1 = datos.tarea(proyecto_plan, ALFA, 'T-01')['tarea']
    assert t1['criterios'] == [{'criterio': 'Hecho.', 'marcado': True}] and t1['revision'] is None and t1['gaps'] == []


def test_tarea_desconocida_o_mal_formada_o_de_otro_id_no_se_resuelve(datos, proyecto_plan):
    assert datos.tarea(proyecto_plan, ALFA, 'T-99') is None
    for malo in ('', 'T-', 't-01', 'T-01x', 'T-12345', '../T-01', None, 7):
        assert datos.tarea(proyecto_plan, ALFA, malo) is None, malo
    assert datos.tarea(proyecto_plan, '0' * 16, 'T-01') is None and datos.tarea(proyecto_plan, 'zz', 'T-01') is None


def test_tarea_de_un_ledger_que_no_se_puede_mostrar_dice_su_estado_sin_detalle(datos, proyecto_plan):
    for ident, estado in ((EPSILON, 'fuera_de_tope'), (IOTA, 'ilegible')):
        r = datos.tarea(proyecto_plan, ident, 'T-01')
        assert r['status'] == estado and r['tarea'] is None and r['complete'] is False and set(r) == CLAVES_ENV


def test_el_detalle_nunca_mezcla_el_historial_archivado(datos, proyecto_plan):
    for ident in (GAMMA, ALFA):
        assert MARCADOR_HISTORIAL not in json.dumps(datos.tarea(proyecto_plan, ident, 'T-01'), ensure_ascii=False)
        assert MARCADOR_HISTORIAL not in json.dumps(datos.plan(proyecto_plan, ident), ensure_ascii=False)


def test_una_tarea_con_historia_archivada_se_marca_archivado_y_solo_enlaza(datos, tmp_path):
    ledger = ('# L\n\n## Fase 1\n\n### T-01 — a\n- **Estado**: completado\n'
              '- **Verificación**: `x` → ok. Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `abcdef123456`.\n')
    proyecto = _proyecto_con(tmp_path, '2026-04-01-arch', ledger)
    (proyecto / 'docs/roadmap/2026-04-01-arch/execution-history.md').write_text('## x\n' + MARCADOR_HISTORIAL + '\n', encoding='utf8')
    t = datos.tarea(proyecto, id16('2026-04-01-arch'), 'T-01')['tarea']
    assert t['archivado'] == {'enlace': 'execution-history.md'} and MARCADOR_HISTORIAL not in json.dumps(t)


def test_la_verificacion_se_recorta_a_2000_caracteres_y_lo_dice_y_la_salida_a_1000(datos, tmp_path):
    ledger = ('# L\n\n## Fase 1\n\n### T-01 — a\n- **Estado**: completado\n- **Verificación**: `x` → ' + 'y' * 3000 + '\n'
              '- **Verificación ejecutada** (2026-10-15): ' + 'z' * 1500 + '\n')
    t = datos.tarea(_proyecto_con(tmp_path, '2026-04-02-larga', ledger), id16('2026-04-02-larga'), 'T-01')['tarea']
    assert len(t['verificacion']) == 2000 and t['verificacion_recortada'] is True and len(t['salida']) == 1000


def test_una_tarea_con_muchos_criterios_y_gaps_recorta_con_indicador(datos, tmp_path):
    criterios = ''.join(f'- [ ] criterio {n}\n' for n in range(60))
    filas = ''.join(f'| {n} | Minor | gap {n} | T-01 | pendiente | e |\n' for n in range(1, 31))
    ledger = ('# L\n\n## Fase 1\n\n### T-01 — a\n- **Estado**: borrador\n\n**Criterios de aceptación**\n' + criterios
              + '\n## Revisión de dos lentes — intento 1: 30 gaps\n\n| # | Grado | Gap | Tarea | Corrección | Evidencia |\n'
              '|---|---|---|---|---|---|\n' + filas)
    r = datos.tarea(_proyecto_con(tmp_path, '2026-04-03-mucho', ledger), id16('2026-04-03-mucho'), 'T-01')
    assert len(r['tarea']['criterios']) == 40 and len(r['tarea']['gaps']) == 20
    assert r['omitidos'] == {'criterios': 20, 'gaps': 10} and r['status'] == 'partial' and r['complete'] is False
    assert r['tarea']['revision']['abiertos'] == 30             # el recuento real no se recorta


# --- servidor: api/plan-<id16>-<T-XX> ---------------------------------------------------------------------------------

def test_api_tarea_sirve_el_detalle_de_una_tarea_del_plan(servidor):
    estado, cabeceras, cuerpo, r = _json(servidor, f'api/plan-{ALFA}-T-02')
    assert estado == 200 and cabeceras['Content-Type'] == 'application/json; charset=utf-8' and len(cuerpo) < 64 * 1024
    assert r['tarea_id'] == 'T-02' and r['tarea']['gaps'][0]['grado'] == 'Important'
    assert cabeceras['Cache-Control'] == 'no-store' and servidor.access_prefix.encode() not in cuerpo


@pytest.mark.parametrize('sufijo', [f'api/plan-{ALFA}-T-99', f'api/plan-{BETA}-T-01', f'api/plan-{"0" * 16}-T-01',
                                    f'api/plan-{ALFA}-t-02', f'api/plan-{ALFA}-T-02/', f'api/plan-{ALFA}-T-02x',
                                    f'api/plan-{ALFA}-T-12345', f'api/plan-{ALFA}-T-02?x=1', f'api/plan-{ALFA}--T-02',
                                    f'api/plan-{ALFA}-T-02-T-01'])
def test_api_tarea_solo_responde_a_tareas_del_ledger_de_una_iniciativa_con_plan(servidor, sufijo):
    assert request(servidor, sufijo)[0] in (404, 405)


def test_api_tarea_rechaza_metodos_que_escriben_y_origenes_ajenos(servidor):
    assert request(servidor, f'api/plan-{ALFA}-T-02', method='PUT')[0] == 405
    assert request(servidor, f'api/plan-{ALFA}-T-02', method='POST')[0] in (405, 400, 415)
    assert request(servidor, f'api/plan-{ALFA}-T-02', headers={'Origin': 'https://fuera.invalid'})[0] == 403


def test_api_tarea_de_un_ledger_fuera_del_tope_responde_su_estado_sin_detalle(servidor):
    s, _, _, r = _json(servidor, f'api/plan-{EPSILON}-T-01')
    assert s == 200 and r['status'] == 'fuera_de_tope' and r['tarea'] is None and r['complete'] is False


def test_api_tarea_anonimiza_todo_el_texto_mostrado_y_respeta_los_topes(servicio, tmp_path):
    plantado = 'jdoeuser /home/jdoeuser/notas jdoe@example.org'
    ledger = (f'# L\n\n## Fase 1 — {plantado}\n\n### T-01 — {plantado}\n- **Descripción**: {plantado}\n'
              f'- **Estado**: completado\n- **Verificación**: {plantado}\n- **Verificación ejecutada** (2026-10-15): {plantado}\n\n'
              f'**Criterios de aceptación**\n- [x] {plantado}\n\n'
              '## Revisión de dos lentes — intento 1: T-01\n\n| # | Grado | Gap | Tarea | Corrección | Evidencia |\n'
              f'|---|---|---|---|---|---|\n| 1 | Important | {plantado} | T-01 | pendiente | e |\n')
    proyecto = _proyecto_con(tmp_path, '2026-04-04-anon', ledger)
    server, hilo = _servir_proyecto(servicio, proyecto, _scrub(servicio))
    try:
        s, _, _, r = _json(server, f'api/plan-{id16("2026-04-04-anon")}-T-01')
    finally:
        _parar(server, hilo)
    texto = json.dumps(r, ensure_ascii=False)
    assert s == 200 and r['tarea']['id'] == 'T-01'
    for sensible in SENSIBLES:
        assert sensible not in texto, sensible
    t = r['tarea']
    for campo in ('titulo', 'fase_nombre', 'descripcion', 'verificacion', 'salida'):
        assert '<usuario>' in t[campo], campo
    assert '<usuario>' in t['criterios'][0]['criterio'] and '<usuario>' in t['gaps'][0]['gap']


def test_api_tarea_enorme_recorta_con_indicador_y_pesa_menos_de_64_kib(servicio, tmp_path):
    criterios = ''.join('- [ ] ' + ('€' * 395) + f' {n:02d}\n' for n in range(40))      # 3 bytes por carácter
    filas = ''.join(f'| {n} | Minor | ' + ('€' * 395) + ' | T-01 | pendiente | e |\n' for n in range(1, 21))
    ledger = ('# L\n\n## Fase 1\n\n### T-01 — a\n- **Descripción**: ' + 'd' * 1400 + '\n- **Estado**: borrador\n'
              '- **Verificación**: ' + 'v' * 1900 + '\n\n**Criterios de aceptación**\n' + criterios
              + '\n## Revisión de dos lentes — intento 1: T-01\n\n| # | Grado | Gap | Tarea | Corrección | Evidencia |\n'
              '|---|---|---|---|---|---|\n' + filas)
    proyecto = _proyecto_con(tmp_path, '2026-04-05-enorme', ledger)
    server, hilo = _servir_proyecto(servicio, proyecto, _scrub(servicio))
    try:
        s, _, cuerpo, r = _json(server, f'api/plan-{id16("2026-04-05-enorme")}-T-01')
    finally:
        _parar(server, hilo)
    assert s == 200 and len(cuerpo) <= 65536 and r['status'] == 'partial' and r['complete'] is False
    assert r['omitidos']['gaps'] + r['omitidos']['criterios'] > 0 and {'status': 'output_budget'} in r['issues']
    assert len(r['tarea']['gaps']) + r['omitidos']['gaps'] == 20 and len(r['tarea']['criterios']) + r['omitidos']['criterios'] == 40


# --- exportado: el detalle va incrustado ----------------------------------------------------------------------------

def test_el_exportado_incrusta_el_detalle_de_cada_tarea_del_plan(exportado):
    html = (exportado / f'plan-{ALFA}.html').read_text(encoding='utf8')
    d = _datos_pagina(html)
    assert set(d['detalles']) == {'T-01', 'T-02'} and set(d['detalles']['T-02']) == CLAVES_ENV
    assert d['detalles']['T-02']['tarea']['gaps'][0]['grado'] == 'Important' and 'api/' not in html
    assert _datos_pagina((exportado / f'plan-{EPSILON}.html').read_text(encoding='utf8'))['detalles'] == {}
    assert MARCADOR_HISTORIAL not in (exportado / f'plan-{GAMMA}.html').read_text(encoding='utf8')


def test_el_detalle_precede_al_kanban_en_el_orden_de_lectura_y_tiene_su_anuncio(exportado):
    html = (exportado / f'plan-{ALFA}.html').read_text(encoding='utf8')
    a, b = html.index('id="plan-detalle"'), html.index('id="kanban-plan"')
    assert a < b and 'role="region"' in html and 'aria-labelledby="plan-detalle-titulo"' in html
    assert re.search(r'id="plan-detalle"[^>]*\shidden', html) and re.search(r'id="plan-detalle"[^>]*tabindex="-1"', html)
    assert re.search(r'id="plan-anuncio"[^>]*role="status"[^>]*aria-live="polite"', html)
    assert re.search(r'<button[^>]*id="plan-detalle-cerrar"[^>]*type="button"|<button[^>]*type="button"[^>]*id="plan-detalle-cerrar"', html)


# --- JS: detalle accesible --------------------------------------------------------------------------------------

IDS = ('plan-estado', 'kanban-plan', 'plan-titulo', 'plan-detalle', 'plan-detalle-titulo', 'plan-detalle-contenido',
       'plan-detalle-cerrar', 'plan-anuncio')
EXTRA_DET = '''
ids['plan-detalle'].hidden=true;
const boton=(id)=>walk(ids['kanban-plan'],n=>n.tagName==='button'&&n.dataset.tarea===id)[0];
const abrir=async(id)=>{const b=boton(id);assert.ok(b,'botón de '+id);b.events.click[0]();await settle();return b;};
const esc=()=>{let evitado=false;docEvents.keydown({key:'Escape',preventDefault(){evitado=true;}});return evitado;};
const detalle=()=>ids['plan-detalle-contenido'].textContent;
'''


def _env(plan, tarea_id, **cambios):
    base = {'version': 1, 'source': 'ledger_tarea', 'status': 'ok', 'complete': True,
            'observed_at': '2026-10-15T10:00:00Z', 'id': plan['id'], 'tarea_id': tarea_id, 'issues': [],
            'omitidos': {'criterios': 0, 'gaps': 0}, 'tarea': None}
    base.update(cambios)
    return base


def _tarea_js(ident, **cambios):
    base = {'id': ident, 'titulo': 'Título de ' + ident, 'fase_nombre': 'Fase 1 — Base', 'estado_tarea': 'en-progreso',
            'literal': None, 'descripcion': 'Descripción larga de la tarea.',
            'criterios': [{'criterio': 'Primer criterio', 'marcado': True}, {'criterio': 'Segundo criterio', 'marcado': False}],
            'verificacion': '`pytest -q` → `passed`', 'verificacion_recortada': False, 'ejecutada': 'ejecutada 2026-10-15',
            'salida': '`pytest -q` → `3 passed`', 'dependencias': ['T-01', 'T-02'], 'archivado': None, 'cerrada': None,
            'horas': {'ia': {'real': 1.03, 'est': 0.5, 'fuente': 'medido'}, 'supervision': {'real': None, 'est': 0.1},
                      'humano': {'real': None, 'est': 4.2}},
            'revision': {'intento': 2, 'cabecera': 'Revisión de dos lentes — intento 2: 1 gap', 'abiertos': 1},
            'gaps': [{'intento': 2, 'num': '1', 'grado': 'Important', 'gap': 'Falta validar la entrada', 'correccion': 'pendiente'}]}
    base.update(cambios)
    return base


def _plan_dos(plan_alfa):
    return _plan_con(plan_alfa, [_fila('T-01', 'completado', 'Primera'), _fila('T-02', 'en-progreso', 'Segunda')])


def _detalles(plan):
    return {t: _env(plan, t, tarea=_tarea_js(t)) for t in ('T-01', 'T-02')}


def test_cada_tarjeta_lleva_un_boton_que_abre_su_detalle_y_nada_mas_escribe(tmp_path, plan_alfa):
    plan = _plan_dos(plan_alfa)
    _correr(tmp_path, EXTRA_DET + '''
const botones=walk(ids['kanban-plan'],n=>n.tagName==='button');
assert.deepEqual(botones.map(b=>b.dataset.tarea).sort(),['T-01','T-02']);
for(const b of botones){assert.equal(b.attrs.type,'button');}
assert.equal(walk(ids['kanban-plan'],n=>['input','textarea','select','form','a'].includes(n.tagName)).length,0);
assert.equal(walk(ids['kanban-plan'],n=>n.attrs.draggable!==undefined).length,0);
assert.match(boton('T-01').textContent,/T-01 · Primera/);
''', datos_pagina=_exportado_con(plan, detalles=_detalles(plan)))


def test_abrir_muestra_todos_los_campos_del_detalle_mueve_el_foco_y_lo_anuncia(tmp_path, plan_alfa):
    plan = _plan_dos(plan_alfa)
    detalles = _detalles(plan)
    detalles['T-02'] = _env(plan, 'T-02', tarea=_tarea_js('T-02', cerrada='2026-10-15', verificacion_recortada=True,
                                                          archivado={'enlace': 'execution-history.md'}))
    _correr(tmp_path, EXTRA_DET + '''
assert.equal(requests.length,0,'exportado: sin red');
const b=await abrir('T-02');
assert.equal(ids['plan-detalle'].hidden,false);
assert.equal(document.activeElement,ids['plan-detalle'],'el foco pasa al detalle');
assert.match(ids['plan-detalle-titulo'].textContent,/T-02 · Título de T-02/);
const t=detalle();
for(const r of [/Descripción larga de la tarea/,/Estado: en-progreso/,/Fase: Fase 1 — Base/,/Cerrada: 2026-10-15/,
  /IA: real 1,03 h \\(medido\\) · estimado 0,50 h/,/Supervisión: real sin datos · estimado 0,10 h/,/Humano: real sin datos · estimado 4,20 h/,
  /Dependencias: T-01, T-02/,/Hecho · Primer criterio/,/Pendiente · Segundo criterio/,/`pytest -q` → `passed`/,
  /recortada a 2\\.000 caracteres/,/Salida registrada/,/`pytest -q` → `3 passed`/,/Revisión de dos lentes — intento 2/,
  /1 gap abierto/,/Important/,/Falta validar la entrada/,/archivado/i,/execution-history\\.md/]) assert.match(t,r,String(r));
assert.match(ids['plan-anuncio'].textContent,/Detalle de T-02 abierto/);
assert.ok(!/ 0 h/.test(t),'lo ausente no se pinta como 0');
''', datos_pagina=_exportado_con(plan, detalles=detalles))


def test_escape_cierra_el_detalle_devuelve_el_foco_a_la_tarjeta_y_lo_anuncia(tmp_path, plan_alfa):
    plan = _plan_dos(plan_alfa)
    _correr(tmp_path, EXTRA_DET + '''
assert.equal(esc(),false,'sin detalle abierto Escape no se intercepta');
const b=await abrir('T-01');
assert.equal(ids['plan-detalle'].hidden,false);
assert.equal(esc(),true);
assert.equal(ids['plan-detalle'].hidden,true);
assert.equal(document.activeElement,b,'el foco vuelve a la tarjeta que abrió el detalle');
assert.match(ids['plan-anuncio'].textContent,/Detalle de T-01 cerrado/);
const b2=await abrir('T-02');assert.equal(document.activeElement,ids['plan-detalle']);
ids['plan-detalle-cerrar'].events.click[0]();
assert.equal(ids['plan-detalle'].hidden,true);assert.equal(document.activeElement,b2);
''', datos_pagina=_exportado_con(plan, detalles=_detalles(plan)))


def test_abrir_otra_tarjeta_sustituye_el_detalle_y_devuelve_el_foco_a_la_ultima(tmp_path, plan_alfa):
    plan = _plan_dos(plan_alfa)
    _correr(tmp_path, EXTRA_DET + '''
await abrir('T-01');assert.match(ids['plan-detalle-titulo'].textContent,/T-01/);
const b2=await abrir('T-02');assert.match(ids['plan-detalle-titulo'].textContent,/T-02/);assert.ok(!/T-01 ·/.test(ids['plan-detalle-titulo'].textContent));
esc();assert.equal(document.activeElement,b2);
''', datos_pagina=_exportado_con(plan, detalles=_detalles(plan)))


def test_servido_pide_el_detalle_por_ruta_relativa_sin_credenciales_y_lo_pinta(tmp_path, plan_alfa):
    plan = _plan_dos(plan_alfa)
    _correr(tmp_path, EXTRA_DET + '''
await respond(PLAN);
assert.equal(requests.length,1);
await abrir('T-02');
assert.equal(requests.length,2);assert.equal(requests[1].url,'api/plan-'+ID+'-T-02');
assert.equal(requests[1].options.credentials,'omit');assert.equal(requests[1].options.cache,'no-store');
assert.match(detalle(),/Cargando/);assert.equal(ids['plan-detalle-contenido'].attrs['aria-busy'],'true');
await respond(DET);
assert.match(detalle(),/Descripción larga de la tarea/);assert.equal(ids['plan-detalle-contenido'].attrs['aria-busy'],'false');
assert.equal(document.activeElement,ids['plan-detalle']);
'''.replace('PLAN', json.dumps(plan)).replace('ID', json.dumps(ALFA)).replace('DET', json.dumps(_env(plan, 'T-02', tarea=_tarea_js('T-02')))),
            datos_pagina=_servido(ALFA))


def test_una_respuesta_vieja_no_pisa_el_detalle_de_la_tarea_que_se_abrio_despues(tmp_path, plan_alfa):
    plan = _plan_dos(plan_alfa)
    d1 = _env(plan, 'T-01', tarea=_tarea_js('T-01', descripcion='Descripción de la primera'))
    d2 = _env(plan, 'T-02', tarea=_tarea_js('T-02', descripcion='Descripción de la segunda'))
    _correr(tmp_path, EXTRA_DET + '''
await respond(PLAN);
await abrir('T-01');await abrir('T-02');
assert.equal(requests.length,3);
await respond(D2,2);
assert.match(ids['plan-detalle-titulo'].textContent,/T-02/);assert.match(detalle(),/Descripción de la segunda/);
await respond(D1,1);
assert.match(ids['plan-detalle-titulo'].textContent,/T-02/);assert.ok(!/Descripción de la primera/.test(detalle()));
'''.replace('PLAN', json.dumps(plan)).replace('D1', json.dumps(d1)).replace('D2', json.dumps(d2)), datos_pagina=_servido(ALFA))


@pytest.mark.parametrize('status,texto', [('fuera_de_tope', 'fuera del tope de lectura'), ('ilegible', 'no legible'),
                                          ('unavailable', 'no disponible')])
def test_un_detalle_que_no_se_puede_mostrar_lo_dice_sin_inventar_campos(tmp_path, plan_alfa, status, texto):
    plan = _plan_dos(plan_alfa)
    detalles = {'T-01': _env(plan, 'T-01', status=status, complete=False), 'T-02': _env(plan, 'T-02')}
    _correr(tmp_path, EXTRA_DET + f'''
await abrir('T-01');
assert.equal(ids['plan-detalle'].hidden,false);assert.match(detalle(),new RegExp({json.dumps(texto)},'i'));
assert.ok(!/Criterios|Verificación|Dependencias/.test(detalle()));
''', datos_pagina=_exportado_con(plan, detalles=detalles))


def _quita_revision(d):
    d['tarea'].pop('revision')


@pytest.mark.parametrize('rompe', [
    lambda d: d['tarea']['gaps'][0].update(grado='Grave'),
    lambda d: d['tarea']['criterios'][0].update(marcado='si'), lambda d: d['tarea'].update(verificacion='x' * 2001),
    lambda d: d['tarea'].update(descripcion='x' * 1501), lambda d: d['tarea'].update(dependencias=['T-1; x']),
    lambda d: d['tarea']['horas']['ia'].update(real=-1), lambda d: d.update(tarea_id='T-01'),
    lambda d: d['tarea'].update(archivado={'enlace': 'http://fuera.invalid/x'}), lambda d: d['tarea'].update(cerrada='ayer'),
    lambda d: d['tarea']['gaps'].extend([d['tarea']['gaps'][0]] * 21), _quita_revision,
    lambda d: d['tarea'].update(estado_tarea='inventado'), lambda d: d.update(extra=1)])
def test_un_detalle_fuera_de_contrato_no_se_pinta(tmp_path, plan_alfa, rompe):
    plan = _plan_dos(plan_alfa)
    detalles = _detalles(plan)
    rompe(detalles['T-02'])
    _correr(tmp_path, EXTRA_DET + '''
await abrir('T-02');
assert.match(detalle(),/No se pudo leer el detalle/);assert.ok(!/Descripción larga/.test(detalle()));
assert.equal(document.activeElement,ids['plan-detalle']);
''', datos_pagina=_exportado_con(plan, detalles=detalles))


def test_el_detalle_dice_cuando_se_recorto_por_presupuesto(tmp_path, plan_alfa):
    plan = _plan_dos(plan_alfa)
    detalles = _detalles(plan)
    detalles['T-02'] = _env(plan, 'T-02', status='partial', complete=False, omitidos={'criterios': 3, 'gaps': 2},
                            issues=[{'status': 'output_budget'}], tarea=_tarea_js('T-02'))
    _correr(tmp_path, EXTRA_DET + '''
await abrir('T-02');
assert.match(detalle(),/3 criterios omitidos/);assert.match(detalle(),/2 gaps omitidos/);assert.match(detalle(),/no acredita ausencia/);
''', datos_pagina=_exportado_con(plan, detalles=detalles))


def test_page_plan_usa_texto_plano_para_los_campos_del_ledger_y_dos_fetch_como_mucho():
    js = (ASSETS / 'page-plan.js').read_text(encoding='utf8')
    assert 'innerHTML' not in js and 'insertAdjacentHTML' not in js and 'eval(' not in js and 'http://' not in js
    assert js.count('.fetch(') == 2 and "'api/plan-' + " in js and "'Escape'" in js and 'plan-anuncio' in js
