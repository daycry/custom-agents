"""H-17 a H-20 (auditoría 2026-11-09): dashboards y consola con roadmaps grandes.

- H-17: la cartera recorta las iniciativas más ANTIGUAS, nunca las más nuevas, y lo dice.
- H-18: el progreso no da `too_large` falso al agotar el presupuesto: lee la cabecera y el resumen.
- H-19: un plan con ledger > 256 KiB (o sin `improvement-plan.md`) se puede continuar y revisar.
- H-20: un plan creado después de arrancar el panel no enlaza a una página 404.
"""
import hashlib
import importlib.util
from pathlib import Path
import re

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'skills/plugin-panel/scripts'


def load(name):
    spec = importlib.util.spec_from_file_location('large_roadmaps_' + name.replace('.', '_'), SCRIPTS / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ledger_text(slug, *, done=1, total=2, padding=0):
    tasks = ''.join(f'### T-{n:02} — Tarea {n}\n\n- **Estado**: {"completado" if n <= done else "en-progreso"}\n\n'
                    f'**Criterios de aceptación**\n- [{"x" if n <= done else " "}] c\n\n' for n in range(1, total + 1))
    pct = round(100 * done / total, 1)
    return (f'---\ntasks: {slug}\nestado: en-progreso\n---\n# {slug}\n\n## Resumen de progreso\n\n'
            '| Fase | Completadas | Total | Progreso |\n|---|---|---|---|\n'
            f'| Fase 1 | {done} | {total} | {pct}% |\n| **TOTAL** | **{done}** | **{total}** | **{pct}%** |\n\n'
            '## Fase 1 — Trabajo\n\n' + tasks + ('relleno ' * 60 + '\n') * padding)


def initiative(root, folder, **kwargs):
    path = root / 'docs/roadmap' / folder / 'tasks.md'
    path.parent.mkdir(parents=True, exist_ok=True)
    slug = re.sub(r'^\d{4}-\d{2}-\d{2}-', '', folder)
    path.write_text(ledger_text(slug, **kwargs), encoding='utf-8')
    (path.parent / 'spec.md').write_text('---\nestado: aprobada\n---\n# ' + slug + '\n', encoding='utf-8')
    return path


def dated(n):
    return f'2026-{1 + n // 28:02}-{1 + n % 28:02}-iniciativa-{n:03}'


def test_h17_cartera_recorta_las_mas_antiguas_y_lo_dice(tmp_path):
    for n in range(70):
        initiative(tmp_path, dated(n))
    result = load('panel_data.py').cartera(tmp_path)
    slugs = {row['slug'] for row in result['iniciativas']}
    assert {dated(n) for n in range(64, 70)} <= slugs, 'las 6 más nuevas no pueden faltar'
    assert not {dated(n) for n in range(6)} & slugs, 'se recortan las más antiguas'
    assert result['recorte'] == {'mostradas': len(result['iniciativas']), 'omitidas': 70 - len(result['iniciativas']),
                                 'criterio': 'mas_nuevas_primero'}


def test_h17_la_pagina_de_iniciativas_dice_cuantas_antiguas_quedan_fuera():
    source = (ROOT / 'skills/plugin-panel/assets/page-iniciativas.js').read_text(encoding='utf-8')
    assert 'd.recorte' in source and 'más antiguas' in source


def test_h18_progreso_sin_too_large_falso_y_de_la_mas_nueva_a_la_mas_antigua(tmp_path):
    for n in range(12):
        initiative(tmp_path, dated(n), padding=420)        # ~200 KiB cada uno: 12 superan 1 MiB
    result = load('serve_panel.py').progress_snapshot(tmp_path)
    assert {'status': 'too_large'} not in result['issues'], result['issues']
    titles = [row['title'] for row in result['initiatives']]
    assert titles == [f'iniciativa-{n:03}' for n in reversed(range(12))]
    by_title = {row['title']: row for row in result['initiatives']}
    oldest = by_title['iniciativa-000']
    assert (oldest['completadas'], oldest['total'], oldest['pct']) == (1, 2, 50)
    assert oldest['fuente'] == 'resumen' and by_title['iniciativa-011']['fuente'] == 'ledger'


def _console(tmp_path):
    registry = load('console_workspaces.py')
    service_module = load('console_service.py')
    project = registry.Workspace('one', 'One', tmp_path, ('codex',))
    return service_module, service_module.Service({'one': project}, sessions=type('S', (), {'close': lambda self: None})())


@pytest.mark.parametrize('padding', [0, 700])          # 700 líneas de relleno → ~330 KiB
def test_h19_continuar_y_revisar_un_plan_grande_o_de_via_rapida(tmp_path, padding):
    folder = '2026-11-01-grande'
    initiative(tmp_path, folder, padding=padding)        # sin improvement-plan.md: vía rápida
    module, service = _console(tmp_path)
    plan = hashlib.sha256(folder.encode()).hexdigest()[:16]
    for action in ('continue', 'review'):
        preview = service.prepare('one', plan, action, None)
        assert 'docs/roadmap/' + folder in preview['prompt']
        assert preview['sources']['docs/roadmap/' + folder + '/tasks.md']


def test_h19_la_consola_explica_los_errores_del_plan():
    source = (ROOT / 'skills/plugin-panel/assets/control-center.js').read_text(encoding='utf-8')
    for code in ('plan_unavailable', 'plan_source_unavailable', 'plan_not_found'):
        assert re.search(r'\b' + code + r":'", source), code


def test_h20_un_plan_creado_tras_arrancar_tiene_pagina(tmp_path):
    server = load('serve_panel.py')
    source = (SCRIPTS / 'serve_panel.py').read_text(encoding='utf-8')
    assert hasattr(server, 'plan_page_path'), 'falta la resolución común de la página de un plan'
    folder = '2026-11-02-nueva'
    initiative(tmp_path, folder).with_name('improvement-plan.md').write_text('# Plan\n', encoding='utf-8')
    initiative(tmp_path, '2026-11-03-sin-plan')
    ident = hashlib.sha256(folder.encode()).hexdigest()[:16]
    assert server.plan_page_path(tmp_path, ident) is not None
    assert server.plan_page_path(tmp_path, '0' * 16) is None
    sin_plan = hashlib.sha256(b'2026-11-03-sin-plan').hexdigest()[:16]
    assert server.plan_page_path(tmp_path, sin_plan) is None, 'como `tiene_plan`: sin improvement-plan.md no hay página'
    assert server.plan_page_path(tmp_path, '../../etc/passwd') is None
    assert 'plan_page_path' in source


def test_h20_http_un_plan_creado_tras_arrancar_se_sirve_y_su_api_responde(tmp_path):
    import http.client
    import threading
    server_module = load('serve_panel.py')
    initiative(tmp_path, '2026-11-01-previa').with_name('improvement-plan.md').write_text('# Plan\n', encoding='utf-8')
    builder = server_module._load_builder()
    server = server_module.create_server(tmp_path, builder.build_inventory(tmp_path, project=None), port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        folder = '2026-11-02-nueva'
        initiative(tmp_path, folder).with_name('improvement-plan.md').write_text('# Plan\n', encoding='utf-8')
        ident = hashlib.sha256(folder.encode()).hexdigest()[:16]

        def get(suffix):
            conn = http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=10)
            conn.request('GET', server.access_prefix + suffix, headers={'Host': f'127.0.0.1:{server.server_port}'})
            response = conn.getresponse()
            body = response.read()
            conn.close()
            return response.status, body
        status, body = get(f'plan-{ident}.html')
        assert status == 200 and b'<html' in body.lower()
        assert get(f'api/plan-{ident}')[0] == 200
        assert get('plan-' + '0' * 16 + '.html')[0] == 404
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)
