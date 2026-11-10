"""Panel servido y consola sin bloqueos ni sondeos caros (auditoría 2026-11-09, T-15: H-32, H-33, H-34).

Servidores efímeros en el puerto 0 y dobles en proceso: nada sobrevive al test ni se lanza un CLI real.
Los topes de tiempo son holgados (el doble lento tarda 4 s; se exige < 2 s) y solo distinguen
«espera al cálculo» de «no espera»; lo que se comprueba de verdad son los recuentos.
"""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import threading
import time
from types import SimpleNamespace

import pytest

from test_panel_server import ledger, request

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/plugin-panel/scripts'


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def service():
    return _load(SCRIPTS / 'serve_panel.py', 'perf_panel_service')


def _servidor(service, project):
    inventory = service._load_builder().build_inventory(project, project=None)
    server = service.create_server(project, inventory)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread


def _parar(server, thread):
    server.shutdown(); server.server_close(); thread.join(timeout=5)


# ------------------------------------------------------------------ H-32: progreso del panel servido

def test_h32_el_progreso_sin_cambios_no_se_recalcula_en_cada_sondeo(service, tmp_path, monkeypatch):
    """H-32: el progreso (~0,5-0,7 s con el roadmap real) se recalculaba cada 2 s de sondeo aunque
    ningún ledger hubiera cambiado. Con la firma igual se sirve la misma versión."""
    ledger(tmp_path)
    server, thread = _servidor(service, tmp_path)
    try:
        primera = json.loads(server.snapshot())
        llamadas = []
        real = service.progress_snapshot
        monkeypatch.setattr(service, 'progress_snapshot', lambda *a, **k: (llamadas.append(1), real(*a, **k))[1])
        for _ in range(3):
            server._snapshot_at -= 30          # caduca el intervalo de sondeo
            assert json.loads(server.snapshot())['initiatives'] == primera['initiatives']
        assert llamadas == [], 'sin cambios en los ledgers no hay que recalcular'
    finally:
        _parar(server, thread)


def test_h32_un_progreso_lento_no_bloquea_el_resto_de_rutas(service, tmp_path, monkeypatch):
    """H-32: el servidor era de un solo hilo y el cálculo del progreso bloqueaba todas las rutas
    (también el envío de una revisión). El recálculo va en segundo plano y se sirve la última versión."""
    path, text = ledger(tmp_path)
    server, thread = _servidor(service, tmp_path)
    try:
        assert request(server, 'api/progress')[0] == 200
        real = service.progress_snapshot
        empezado = threading.Event()
        def lento(*a, **k):
            empezado.set(); time.sleep(4); return real(*a, **k)
        monkeypatch.setattr(service, 'progress_snapshot', lento)
        path.write_text(text.replace('### T-02 — Build feature\n- **Estado**: en-progreso',
                                     '### T-02 — Build feature\n- **Estado**: completado'), encoding='utf8', newline='\n')
        server._snapshot_at -= 30
        resultados = {}
        def pedir(nombre, ruta):
            inicio = time.monotonic(); estado = request(server, ruta)[0]
            resultados[nombre] = (estado, time.monotonic() - inicio)
        hilos = [threading.Thread(target=pedir, args=('progreso', 'api/progress'))]
        hilos[0].start()
        time.sleep(.2)
        hilos.append(threading.Thread(target=pedir, args=('inicio', '')))
        hilos[1].start()
        for hilo in hilos:
            hilo.join(timeout=10)
        assert resultados['progreso'][0] == 200 and resultados['progreso'][1] < 2, resultados
        assert resultados['inicio'][0] == 200 and resultados['inicio'][1] < 2, resultados
        assert empezado.wait(timeout=5), 'el cambio del ledger debe lanzar el recálculo'
    finally:
        _parar(server, thread)


# ------------------------------------------------------------------ H-33 / H-34: consola

@pytest.fixture
def consola(tmp_path):
    registry = _load(SCRIPTS / 'console_workspaces.py', 'perf_console_workspaces')
    module = _load(SCRIPTS / 'console_service.py', 'perf_console_service')
    workspace = registry.Workspace('one', 'One', tmp_path, ('codex', 'claude-code', 'opencode'))
    service = module.Service({'one': workspace}, sessions=SimpleNamespace(close=lambda: None, errors={}))
    yield module, service
    service.close()


def _discover_contado(module, monkeypatch, llamadas, filas=None):
    original = module.C.sibling
    def discover(workspace, **kwargs):
        llamadas.append(1)
        return {'status': 'ok', 'complete': True, 'sessions': list(filas or [{'id': 'x', 'title': 'Una'}])}
    monkeypatch.setattr(module.C, 'sibling', lambda name: SimpleNamespace(discover=discover)
                        if name in ('console_codex.py', 'console_claude.py', 'console_opencode.py') else original(name))


def _esperar(funcion):
    limite = time.monotonic() + 3
    while time.monotonic() < limite:
        valor = funcion()
        if valor['freshness']['state'] != 'refreshing' and valor['status'] != 'calculating':
            return valor
        time.sleep(.01)
    return valor


def test_h33_el_resumen_no_relanza_los_cli_de_sesiones_nativas(consola, monkeypatch):
    """H-33: Inicio pedía `native-sessions` cada 2 s y cada 15 s relanzaba hasta 3 CLIs (codex
    app-server, claude agents, opencode serve). Fuera de la vista Sesiones solo se lee lo ya observado."""
    module, service = consola
    llamadas = []
    _discover_contado(module, monkeypatch, llamadas)
    valor = service.native_sessions('one', discover=False)
    assert llamadas == [] and valor['sessions'] == [] and valor['complete'] is False
    _esperar(lambda: service.native_sessions('one'))
    assert len(llamadas) == 3                     # la vista Sesiones sí descubre (un CLI por runtime)
    assert service.native_sessions('one', discover=False)['sessions'][0]['title'] == 'Una'
    assert len(llamadas) == 3


def test_h33_sin_cambios_el_descubrimiento_espacia_los_relanzamientos(consola, monkeypatch):
    """H-33: con el mismo resultado, cada nuevo descubrimiento espera el doble (15 → 30 → 60 s, tope
    120 s); un cambio vuelve a 15 s."""
    module, service = consola
    llamadas = []
    _discover_contado(module, monkeypatch, llamadas)
    ahora = [1000.0]
    service.discovery_reads = module.SNAPSHOTS.Snapshots(clock=lambda: ahora[0])
    momentos = []
    for segundo in range(0, 200, 5):
        ahora[0] = 1000.0 + segundo
        antes = len(llamadas)
        _esperar(lambda: service.native_sessions('one'))
        if len(llamadas) > antes:
            momentos.append(segundo)
    assert momentos == [0, 15, 45, 105], momentos


def test_h34_runtimes_cacheado_y_modulos_hermanos_cargados_una_vez(consola, monkeypatch):
    """H-34: `runtimes` buscaba los ejecutables (~600 ms en vivo) en cada sondeo de 2 s y cargaba de
    nuevo `console_transport.py` en cada llamada."""
    module, service = consola
    assert module.C.sibling('console_transport.py') is module.C.sibling('console_transport.py')
    transport = module.C.sibling('console_transport.py')
    buscados = []
    monkeypatch.setattr(transport, 'executable', lambda runtime, root: buscados.append(runtime) or 'bin')
    primera = service.runtimes('one')
    segunda = service.runtimes('one')
    assert primera == segunda and len(buscados) == 3
    assert {r['id']: r['installed'] for r in segunda['runtimes']} == {'claude-code': True, 'codex': True, 'opencode': True}


def test_h34_el_catalogo_sigue_cargando_su_constructor_de_nuevo(consola):
    """El constructor del catálogo guarda su saneador en el módulo: cada catálogo necesita uno propio."""
    module, _ = consola
    assert module.C.sibling('build_panel.py') is not module.C.sibling('build_panel.py')


# ------------------------------------------------------------------ menores: plazo en leerResumen

def test_leer_resumen_tiene_plazo_y_aborta_la_peticion():
    """`PanelReview.leerResumen` (tarjetas de Iniciativas) no tenía plazo: una petición colgada dejaba
    la tarjeta en «cargando» para siempre. Ahora aborta a los 4 s, como el resto de lecturas del panel."""
    node = shutil.which('node')
    if node is None:
        pytest.skip('node no disponible')
    script = r"""
const fs = require('fs'), vm = require('vm');
const code = fs.readFileSync(process.argv[1], 'utf8');
const timers = []; let signal = null, aborted = false;
class AC { constructor() { this.signal = {aborted: false}; } abort() { aborted = true; this.signal.aborted = true; } }
const ctx = { AbortController: AC, setTimeout: (f, ms) => { timers.push([f, ms]); return timers.length; }, clearTimeout: () => {},
  fetch: (url, init) => { signal = init && init.signal; return new Promise(() => {}); },
  document: { getElementById: () => null }, console };
ctx.globalThis = ctx; vm.createContext(ctx); vm.runInContext(code, ctx);
let result = 'pendiente';
ctx.PanelReview.leerResumen((rows, motivo) => { result = motivo; });
const plazo = timers.find(t => t[1] > 0 && t[1] <= 10000);
if (plazo) plazo[0]();
console.log(JSON.stringify({signal: !!signal, plazo: plazo ? plazo[1] : null, aborted}));
"""
    salida = subprocess.run([node, '-e', script, str(ROOT / 'skills/plugin-panel/assets/panel-review.js')],
                            capture_output=True, text=True, encoding='utf-8', timeout=30)
    assert salida.returncode == 0, salida.stderr
    datos = json.loads(salida.stdout.strip().splitlines()[-1])
    assert datos == {'signal': True, 'plazo': 4000, 'aborted': True}, datos


# ------------------------------------------------- revisión intento 1 (fase 3): T-15

def test_fix1_b3_sin_consultar_sesiones_el_recuento_de_inicio_es_parcial():
    """B3: Inicio lee `native-sessions/cached`; sin visitar Sesiones (`not_requested`) mostraba solo
    las sesiones gestionadas como si fueran el total «incluidas externas». Ahora dice «≥ N»."""
    node = shutil.which('node')
    if node is None:
        pytest.skip('node no disponible')
    modulo = (ROOT / 'skills/plugin-panel/assets/console-dom.js').as_uri()
    script = ("import {sessionCountLabel} from %r;\n"
              "const managed=[{runtime:'codex',native_id:'a'},{runtime:'codex',native_id:'b'}];\n"
              "console.log(JSON.stringify([\n"
              " sessionCountLabel({status:'not_requested',complete:false,sessions:[]},managed),\n"
              " sessionCountLabel({status:'ok',complete:true,sessions:[{runtime:'codex',id:'c'}],freshness:{state:'current'}},managed),\n"
              " sessionCountLabel({status:'partial',complete:false,sessions:[{runtime:'codex',id:'c'}]},managed),\n"
              " sessionCountLabel({status:'not_requested',complete:false,sessions:[]},[]),\n"
              " sessionCountLabel({status:'ok',complete:true,sessions:[],freshness:{state:'current'}},[])]))\n") % modulo
    salida = subprocess.run([node, '--input-type=module', '-e', script], capture_output=True, text=True,
                            encoding='utf-8', timeout=30)
    assert salida.returncode == 0, salida.stderr
    assert json.loads(salida.stdout) == ['≥ 2', 3, '≥ 3', None, 0]
    contexto = (ROOT / 'skills/plugin-panel/assets/console-context.js').read_text(encoding='utf-8')
    assert 'sessionCountLabel(' in contexto


def test_fix1_a4_una_ruta_lenta_no_bloquea_la_portada(service, tmp_path, monkeypatch):
    """A4: el servidor era de un solo hilo: además del progreso, un plan grande o la primera
    instantánea serializaban el resto. Ahora atiende con hilos acotados."""
    ledger(tmp_path)
    server, thread = _servidor(service, tmp_path)
    try:
        lento = threading.Event()
        def plan_lento(ident):
            lento.set(); time.sleep(4); return None
        server.plan_ids = {'a' * 16}
        monkeypatch.setattr(server, 'plan', plan_lento)
        resultado = {}
        hilo = threading.Thread(target=lambda: resultado.setdefault('plan', request(server, 'api/plan-' + 'a' * 16)[0]))
        hilo.start()
        assert lento.wait(timeout=5)
        inicio = time.monotonic(); estado = request(server, '')[0]
        assert estado == 200 and time.monotonic() - inicio < 2
        hilo.join(timeout=10)
        assert server.snapshot_inicial is True
    finally:
        _parar(server, thread)
