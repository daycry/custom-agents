"""T-17: proyección de cartera de `panel_data.cartera()`.

Las cifras se comparan contra la salida REAL de `build_dashboard.py --json` y de `progress-report.py`
(se ejecutan los scripts), nunca contra un oráculo copiado. Datos de prueba genéricos.
"""
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from test_panel_contract_golden import materializar

ROOT = Path(__file__).resolve().parents[1]
DASHBOARD = ROOT / 'skills/roadmap-dashboard/scripts/build_dashboard.py'
PROGRESS = ROOT / 'agent-kits/shared/progress-report.py'
DATA = ROOT / 'skills/plugin-panel/scripts/panel_data.py'
ESTADOS = ('borrador', 'aprobada', 'implementada', 'obsoleta')


def _cargar():
    spec = importlib.util.spec_from_file_location('panel_data_probe', DATA)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope='module')
def proyecto(tmp_path_factory):
    copia = materializar(tmp_path_factory.mktemp('cartera'))
    destino = copia / 'proyecto'
    (destino / 'docs').mkdir(parents=True)
    shutil.copytree(copia / 'roadmap', destino / 'docs/roadmap')
    return destino


@pytest.fixture(scope='module')
def cartera(proyecto):
    return _cargar().cartera(proyecto)


def _por_slug(resultado):
    return {fila['slug']: fila for fila in resultado['iniciativas']}


def _dashboard_json(proyecto):
    salida = subprocess.run([sys.executable, str(DASHBOARD), '--root', str(proyecto / 'docs/roadmap'), '--json'],
                            capture_output=True, text=True, encoding='utf8', check=True).stdout
    return {r['slug']: r for r in json.loads(salida)}


def _progress_json(ledger):
    r = subprocess.run([sys.executable, str(PROGRESS), 'line', str(ledger), '--json'],
                       capture_output=True, text=True, encoding='utf8')
    return json.loads(r.stdout) if r.returncode == 0 else None


def test_estados_de_spec_iguales_a_dashboard_json_y_la_ilegible_no_cuenta(proyecto, cartera):
    referencia = _dashboard_json(proyecto)
    esperado = {estado: sum(1 for r in referencia.values() if r['spec_estado'] == estado) for estado in ESTADOS}
    assert {estado: cartera['totales']['por_estado'][estado] for estado in ESTADOS} == esperado
    delta = _por_slug(cartera)['2026-01-13-delta']
    assert referencia['2026-01-13-delta']['spec_estado'] is None and delta['categoria'] == 'ilegible'
    assert delta['motivo'] == 'sin_estado'
    assert cartera['totales']['por_estado']['ilegible'] == 1
    contados = sum(cartera['totales']['por_estado'].values())
    assert contados == len(cartera['iniciativas']) == len(referencia)   # cada iniciativa en UNA sola categoria


def test_tareas_por_ledger_iguales_a_progress_report_y_el_tope_no_suma(proyecto, cartera):
    filas = _por_slug(cartera)
    n = m = ledgers = 0
    for carpeta in sorted((proyecto / 'docs/roadmap').iterdir()):
        ledger = carpeta / 'tasks.md'
        if not ledger.is_file() or ledger.stat().st_size > 256 * 1024:
            continue
        esperado = _progress_json(ledger)
        fila = filas[carpeta.name]
        assert fila['ledger'] == 'ok'
        assert fila['tareas'] == {'total': esperado['total'], 'completadas': esperado['completadas'], 'pct': esperado['pct']}
        n += esperado['completadas']; m += esperado['total']; ledgers += 1
    assert cartera['totales']['tareas'] == {'completadas': n, 'total': m, 'pct': round(100 * n / m), 'ledgers': ledgers}
    grande = filas['2026-01-14-epsilon']
    assert grande['ledger'] == 'fuera_de_tope' and grande['tareas'] is None
    assert [x['slug'] for x in cartera['totales']['fuera_de_tope']] == ['2026-01-14-epsilon']
    assert {'codigo': 'fuera_de_tope', 'n': 1} in grande['alertas']


def test_ausente_es_null_nunca_cero_y_la_procedencia_sale_de_vista_json(proyecto, cartera):
    referencia = _dashboard_json(proyecto)
    filas = _por_slug(cartera)
    beta = filas['2026-01-11-beta']
    assert beta['ledger'] == 'sin_ledger' and beta['tareas'] is None
    assert beta['horas'] == {'real': None, 'est': None, 'humanas': {'real': None, 'est': None}}
    assert beta['coste'] == {'real_eur': None, 'real_parcial': False, 'est_eur': None, 'est_texto': None}
    gamma = filas['2026-01-12-gamma']                                  # real «—» en el ledger, estimado sí
    assert gamma['horas']['real'] is None and gamma['horas']['est'] == pytest.approx(1.25)
    assert gamma['horas']['humanas'] == {'real': None, 'est': 4.0}
    alfa = filas['2026-01-10-alfa']
    assert alfa['horas'] == {'real': pytest.approx(1.9), 'est': pytest.approx(2.5), 'humanas': {'real': 3.0, 'est': 6.0}}
    assert alfa['coste']['est_eur'] == 1300.0 and alfa['coste']['est_texto'] == '1.300 EUR'
    for slug, fila in filas.items():
        r = referencia[slug]
        assert fila['procedencia'] == {'medidos': r['medidos'], 'estimados': r['estimados'],
                                       'desconocidos': r['generacion_otros']}
    total = {k: sum(f['procedencia'][k] for f in filas.values()) for k in ('medidos', 'estimados', 'desconocidos')}
    assert cartera['totales']['procedencia'] == total


def test_coste_real_suma_solo_lo_presente_y_dice_cuantas_iniciativas_tienen_dato(proyecto, cartera):
    referencia = _dashboard_json(proyecto)
    filas = _por_slug(cartera)
    esperado = {}
    for slug, r in referencia.items():
        valores = [v['eur'] for v in r['procedencia']['coste'].values() if v['eur'] is not None]
        esperado[slug] = round(sum(valores), 6) if valores else None
        assert (filas[slug]['coste']['real_eur'] is None) == (esperado[slug] is None)
        if esperado[slug] is not None:
            assert filas[slug]['coste']['real_eur'] == pytest.approx(esperado[slug])
    assert filas['2026-01-15-zeta']['coste']['real_parcial'] is True    # estimado_incompleto en el dashboard
    con_dato = [v for v in esperado.values() if v is not None]
    assert cartera['totales']['coste']['real_n'] == len(con_dato)
    assert cartera['totales']['coste']['real_eur'] == pytest.approx(sum(con_dato))
    con_est = [f['coste']['est_eur'] for f in filas.values() if f['coste']['est_eur'] is not None]
    assert cartera['totales']['coste']['est_n'] == len(con_est)
    assert cartera['totales']['coste']['est_eur'] == pytest.approx(sum(con_est))


def test_alertas_con_su_codigo_y_su_cuenta(proyecto, cartera):
    filas = _por_slug(cartera)
    assert {'codigo': 'gaps_abiertos', 'n': 2} in filas['2026-01-10-alfa']['alertas']
    assert {'codigo': 'sin_estimacion', 'n': 1} in filas['2026-01-11-beta']['alertas']
    assert all(a['codigo'] != 'sin_estimacion' for a in filas['2026-01-10-alfa']['alertas'])


def test_completado_con_criterios_sin_marcar_es_una_alerta(tmp_path):
    carpeta = tmp_path / 'docs/roadmap/2026-02-01-sucia'
    carpeta.mkdir(parents=True)
    (carpeta / 'tasks.md').write_text('# Sucia\n\n## Fase 1\n\n### T-01 — Uno\n- **Estado**: completado\n\n'
                                      '**Criterios de aceptación**\n- [ ] A medias.\n- [x] Hecho.\n\n'
                                      '### T-02 — Dos\n- **Estado**: completado\n\n**Criterios de aceptación**\n- [x] Hecho.\n',
                      encoding='utf8')
    fila = _cargar().cartera(tmp_path)['iniciativas'][0]
    assert {'codigo': 'completado_sin_marcar', 'n': 1} in fila['alertas']


def test_estados_sin_spec_y_no_reconocido(tmp_path):
    raiz = tmp_path / 'docs/roadmap'
    (raiz / '2026-02-01-rapida').mkdir(parents=True)
    (raiz / '2026-02-01-rapida/tasks.md').write_text('# R\n\n### T-01 — Uno\n- **Estado**: completado\n', encoding='utf8')
    (raiz / '2026-02-02-rara').mkdir()
    (raiz / '2026-02-02-rara/spec.md').write_text('---\nestado: en revisión rara\ncreado: 2026-02-02\n---\n# Rara\n', encoding='utf8')
    filas = _por_slug(_cargar().cartera(tmp_path))
    assert filas['2026-02-01-rapida']['categoria'] == 'sin_spec'
    assert filas['2026-02-02-rara']['categoria'] == 'no_reconocido'
    assert filas['2026-02-02-rara']['literal'] == 'en revisión rara'
    assert filas['2026-02-02-rara']['fecha'] == '2026-02-02'


def test_el_panel_toma_las_cifras_de_vista_json_y_no_las_recalcula(proyecto, monkeypatch):
    modulo = _cargar()
    real = modulo._load_dashboard()
    original = real.vista_json

    def falsa(inits):
        resultado = original(inits)
        for r in resultado:
            r['estimados'], r['medidos'], r['generacion_otros'] = 70, 7, 700
        return resultado
    monkeypatch.setattr(real, 'vista_json', falsa)
    monkeypatch.setattr(modulo, '_load_dashboard', lambda: real)
    resultado = modulo.cartera(proyecto)
    assert all(f['procedencia'] == {'medidos': 7, 'estimados': 70, 'desconocidos': 700} for f in resultado['iniciativas'])


def _roadmap_grande(tmp_path, titulo):
    raiz = tmp_path / 'docs/roadmap'
    for n in range(70):
        carpeta = raiz / (f'2026-03-{(n % 28) + 1:02}-' + f'iniciativa-{n:03}-' + 'x' * 60)
        carpeta.mkdir(parents=True)
        (carpeta / 'spec.md').write_text('---\nestado: aprobada\ncreado: 2026-03-01\n---\n# ' + titulo + '\n', encoding='utf8')
        (carpeta / 'evaluation.md').write_text('| **Coste** | ' + '9' * 300 + ' EUR |\n', encoding='utf8')
        (carpeta / 'tasks.md').write_text('# T\n\n### T-01 — Uno\n- **Estado**: en-progreso\n', encoding='utf8')


def test_tope_de_64_iniciativas_y_de_64_kib_con_textos_al_limite(tmp_path):
    _roadmap_grande(tmp_path, 'T' * 160)
    resultado = _cargar().cartera(tmp_path)
    cuerpo = json.dumps(resultado, ensure_ascii=False).encode('utf8')
    assert len(resultado['iniciativas']) == 64 and len(cuerpo) <= 65536
    assert resultado['complete'] is False and {'status': 'row_budget'} in resultado['issues']
    assert resultado['status'] == 'partial'
    assert all(len(f['titulo']) <= 160 and len(f['slug']) <= 80 and len(f['coste']['est_texto']) <= 120
               for f in resultado['iniciativas'])


def test_con_textos_de_cuatro_bytes_la_respuesta_sigue_bajo_64_kib_y_lo_dice(tmp_path):
    _roadmap_grande(tmp_path, '🙂' * 160)
    resultado = _cargar().cartera(tmp_path)
    cuerpo = json.dumps(resultado, ensure_ascii=False).encode('utf8')
    assert len(cuerpo) <= 65536 and resultado['status'] == 'partial'
    assert {'status': 'output_budget'} in resultado['issues'] or len(resultado['iniciativas']) == 64
    assert resultado['totales']['iniciativas'] == len(resultado['iniciativas'])   # los totales no cuentan lo recortado


def test_sin_roadmap_no_es_ausencia_de_iniciativas_y_el_lector_ausente_falla_cerrado(tmp_path, monkeypatch):
    modulo = _cargar()
    assert modulo.cartera(tmp_path)['status'] == 'not_found'
    (tmp_path / 'docs/roadmap').mkdir(parents=True)
    vacio = modulo.cartera(tmp_path)
    assert vacio['status'] == 'ok' and vacio['iniciativas'] == [] and vacio['totales']['tareas'] is None
    monkeypatch.setattr(modulo, '_load_dashboard', lambda: (_ for _ in ()).throw(ImportError('/ruta/privada')))
    caido = modulo.cartera(tmp_path)
    assert caido['status'] == 'unavailable' and '/ruta/privada' not in json.dumps(caido)


def test_no_escribe_nada_en_el_proyecto(proyecto):
    antes = sorted((p, p.stat().st_mtime_ns) for p in proyecto.rglob('*') if p.is_file())
    _cargar().cartera(proyecto)
    assert sorted((p, p.stat().st_mtime_ns) for p in proyecto.rglob('*') if p.is_file()) == antes


# --- fix1 de la Fase 2 (F2-5, F2-6) -------------------------------------------------------------------------------------

def test_cada_ledger_se_parsea_una_sola_vez_por_calculo_de_cartera(proyecto):
    """F2-5: `progress.parse_ledger` una vez por ledger (antes `resumir` + `parse_ledger` = dos)."""
    datos = _cargar()
    cuentas = []
    cargar = datos._load_shared
    def contando(nombre):
        modulo = cargar(nombre)
        if nombre == 'progress-report.py':
            real = modulo.parse_ledger
            modulo.parse_ledger = lambda texto: (cuentas.append(1), real(texto))[1]
        return modulo
    datos._load_shared = contando
    resultado = datos.cartera(proyecto)
    con_ledger = [f for f in resultado['iniciativas'] if f['ledger'] == 'ok']
    assert con_ledger and len(cuentas) == len([f for f in resultado['iniciativas'] if f['ledger'] not in ('sin_ledger', 'fuera_de_tope', 'sin_lectura')])


def test_plan_y_detalles_lee_el_ledger_una_vez_y_da_lo_mismo_que_plan_y_tarea(proyecto, cartera):
    datos = _cargar()
    fila = next(f for f in cartera['iniciativas'] if f['tiene_plan'] and f['ledger'] == 'ok')
    lecturas = []
    vista = datos._load_ledger_view()
    real = vista.leer
    vista.leer = lambda ruta: (lecturas.append(1), real(ruta))[1]
    datos._load_ledger_view = lambda: vista
    plan, detalles = datos.plan_y_detalles(proyecto, fila['id'])
    assert len(lecturas) == 1
    datos2 = _cargar()
    observado = datos2.plan(proyecto, fila['id'])
    assert {k: v for k, v in plan.items() if k != 'observed_at'} == {k: v for k, v in observado.items() if k != 'observed_at'}
    assert set(detalles) == {t['id'] for t in plan['tareas']}
    for tarea_id, detalle in detalles.items():
        esperado = datos2.tarea(proyecto, fila['id'], tarea_id)
        assert {k: v for k, v in detalle.items() if k != 'observed_at'} == {k: v for k, v in esperado.items() if k != 'observed_at'}
    assert datos.plan_y_detalles(proyecto, '0' * 16) is None
