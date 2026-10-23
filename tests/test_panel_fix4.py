"""Confirmacion del intento 3 de panel-redesign: C-1 (contrato del saneado servido) y C-3 (topes tras anonimizar).

Datos de prueba genericos (`jdoe@example.org`, `jdoeuser`); nada del equipo donde se ejecuta.
"""
import copy
import hashlib
import json
import shutil
import subprocess

import pytest

from test_panel_fix3 import (CORREO, RUTA, SCRIPTS, SEC, SENSIBLES, _cargar, _pedir, _producer, _propietario,
                             _revision, _scrub, _servir, _parar)
from test_panel_live_ui import HARNESS as HARNESS_MEMORIA
from test_panel_memory_ui import SETUP as SETUP_MEMORIA
from test_panel_review_ui import HARNESS as HARNESS_REVISION

PLANTADO = f'jdoeuser {RUTA}/x {CORREO}'


def _hojas(valor, ruta=()):
    """(ruta de claves, cadena) de cada cadena de un JSON."""
    if isinstance(valor, str):
        yield ruta, valor
    elif isinstance(valor, list):
        for fila in valor:
            yield from _hojas(fila, ruta)
    elif isinstance(valor, dict):
        for clave, fila in valor.items():
            yield from _hojas(fila, ruta + (clave,))


def _entrada(**extra):
    base = {'id': 'ADR-001', 'tipo': PLANTADO, 'estado': PLANTADO, 'estado_detalle': PLANTADO,
            'titular': PLANTADO, 'area': PLANTADO, 'version': 2, 'category': PLANTADO, 'evidencia': PLANTADO,
            'origen': 'approved', 'ruta': 'docs/knowledge/approved/' + CORREO + '.md',
            'source_sha256': 'f' * 64}
    base.update(extra)
    return base


def _memoria():
    return {'version': 1, 'source': 'canonical_knowledge', 'observed_at': '2026-10-09T10:00:00Z',
            'operation': 'related', 'status': 'ok', 'complete': True, 'issues': ['scan_budget'],
            'entries': [_entrada()], 'selected': _entrada(texto=PLANTADO),
            'related': {'sucesion': [{'relation': PLANTADO, 'id': 'ADR-002', 'entry': _entrada(id='ADR-002')}],
                        'iniciativa': [_entrada(id='ADR-003')], 'area': [_entrada(id='ADR-004')],
                        'enlaces': [_entrada(id='ADR-005')]},
            'budget': {'files': 1, 'bytes': 1, 'entries': 1}}


# Contrato de `api/memory`: lo que `panel-memory.js` muestra (se anonimiza) y lo que vuelve al servidor o valida
# por vocabulario/forma (queda intacto). Un campo nuevo sin clasificar rompe este test.
MEMORIA_MOSTRADO = {'tipo', 'estado', 'estado_detalle', 'titular', 'area', 'category', 'evidencia', 'ruta',
                    'texto', 'relation'}
MEMORIA_INTACTO = {'id', 'origen', 'source_sha256', 'observed_at', 'operation', 'source', 'status', 'issues'}


def test_contrato_memoria_cada_campo_mostrado_anonimizado_y_el_resto_intacto():
    servicio = _cargar()
    dato = _memoria()
    limpio = servicio._scrubbed(copy.deepcopy(dato), _scrub(servicio))
    sin_clasificar = {r[-1] for r, _ in _hojas(dato) if r[-1] not in MEMORIA_MOSTRADO | MEMORIA_INTACTO}
    assert not sin_clasificar, f'campo de texto sin clasificar en el contrato de api/memory: {sin_clasificar}'
    originales = dict(_hojas_con_indice(dato))
    for indice, (ruta, texto) in enumerate(_hojas(limpio)):
        clave = ruta[-1]
        if clave in MEMORIA_MOSTRADO:
            for sensible in SENSIBLES:
                assert sensible not in texto, (ruta, sensible)
        else:
            assert texto == originales[indice], ruta
    assert {r[-1] for r, _ in _hojas(dato)} >= MEMORIA_MOSTRADO       # el contrato cubre todos los campos


def _hojas_con_indice(valor):
    return list(enumerate(t for _, t in _hojas(valor)))


# Contrato de `api/review`: `title`/`text` solo dentro de `sections`; `initiative` (slug acotado por regex en
# plan-review.py, solo se muestra) queda intacto: el anonimizador no casa un usuario unido por guiones a otras
# palabras, asi que sanearlo seria un no-op y es la identidad publica de la iniciativa; lo escrito por el usuario (`draft_comments`, `decision.comments[].text`) vuelve en Guardar/Decidir.
REVISION_MOSTRADO = {'title', 'response_text', 'note'}
REVISION_INTACTO = {'review_id', 'artifact', 'gate_key', 'raw_sha256', 'view_sha256', 'view_version', 'state',
                    'created_at', 'observed_at', 'registered_at', 'caller_id', 'runtime', 'identity_basis',
                    'validity', 'decision_id', 'choice', 'submitted_at', 'delivery_id', 'delivered_at',
                    'consumed_at', 'status', 'reason', 'comment_id', 'section_id', 'result_id',
                    'supersedes_result_id', 'disposition', 'recorded_at', 'verification_id', 'assessment',
                    'basis', 'actor_id', 'initiative'}


def _revision_completa():
    base = _revision(PLANTADO, PLANTADO, PLANTADO)
    rev = base['review']
    rev['initiative'] = 'docs/roadmap/2026-10-09-jdoeuser'
    rev['sections'][0]['title'] = PLANTADO
    rev['draft_comments'] = [{'comment_id': 'two', 'section_id': SEC, 'text': PLANTADO}]
    rev['feedback']['verifications'] = [{
        'verification_id': '2' * 64, 'result_id': '1' * 64, 'comment_id': 'one', 'section_id': SEC,
        'assessment': 'confirmed', 'note': PLANTADO, 'text_flags': {'redacted': False, 'controls_sanitized': False},
        'basis': 'human_instruction', 'producer': _producer(), 'recorded_at': '2026-10-09T10:00:04Z'}]
    return base


def _clasifica_revision(ruta):
    clave = ruta[-1]
    if clave == 'text':
        return 'mostrado' if 'sections' in ruta else 'usuario'
    if clave in REVISION_MOSTRADO:
        return 'mostrado'
    return 'intacto' if clave in REVISION_INTACTO else None


def test_contrato_revision_cada_campo_mostrado_anonimizado_y_el_resto_intacto():
    servicio = _cargar()
    dato = _revision_completa()
    limpio = servicio._scrubbed(copy.deepcopy(dato), _scrub(servicio))
    antes = list(_hojas(dato)); despues = list(_hojas(limpio))
    sin_clasificar = {r[-1] for r, _ in antes if _clasifica_revision(r) is None}
    assert not sin_clasificar, f'campo de texto sin clasificar en el contrato de api/review: {sin_clasificar}'
    vistos = set()
    for (ruta, original), (_, nuevo) in zip(antes, despues):
        tipo = _clasifica_revision(ruta); vistos.add(ruta[-1])
        if tipo == 'mostrado':
            for sensible in SENSIBLES:
                assert sensible not in nuevo, (ruta, sensible)
        elif tipo in ('intacto', 'usuario'):
            assert nuevo == original, ruta
    assert REVISION_MOSTRADO <= vistos      # el contrato recorre todos los campos mostrados


# C-3: anonimizar alarga el texto; el recorte a los topes del validador del navegador va DESPUES, en el servidor.

def _corto(servicio):
    # usuario de 3 caracteres: `<usuario>` (9) es 3 veces mas largo
    redact = servicio._load_shared('redact.py')
    return lambda t: redact.anonimizar(redact.redactar(t), None, '/home/abc', 'abc')


def _node(tmp_path, fuente, escenario):
    node = shutil.which('node')
    if not node:
        pytest.skip('Node unavailable')
    f = tmp_path / 'v.cjs'
    f.write_text(fuente + '\n(async()=>{' + escenario
                 + '})().catch(error=>{console.error(error);process.exitCode=1;});', encoding='utf8')
    r = subprocess.run([node, str(f)], capture_output=True, text=True, encoding='utf8', errors='replace',
                       timeout=30)
    assert r.returncode == 0, r.stdout + r.stderr


def test_titular_de_160_pasa_el_validador_de_memoria_tras_anonimizar(tmp_path):
    servicio = _cargar()
    scrub = _corto(servicio)
    titular = 'abc ' * 40                       # 160 caracteres
    assert len(titular) == 160 and len(scrub(titular)) > 160
    dato = _memoria()
    dato['operation'] = 'search'; dato['selected'] = None; dato['related'] = None
    dato['entries'] = [_entrada(titular=titular, area='abc' * 53, evidencia='abc ' * 250, tipo='abc ' * 40)]
    limpio = servicio._scrubbed(dato, scrub)
    fila = limpio['entries'][0]
    assert len(fila['titular']) <= 160 and len(fila['area']) <= 160 and len(fila['evidencia']) <= 1000
    assert not fila['titular'].endswith('<') and '<usuari' not in fila['titular'].replace('<usuario>', '')
    escenario = ("submit();await resolve(" + json.dumps(limpio, ensure_ascii=False) + ");"
                 "assert.equal(ids['memory-results'].children.length,1);")
    fuente = (SCRIPTS.parent / 'assets/panel-memory.js').read_text(encoding='utf8')
    _node(tmp_path, HARNESS_MEMORIA + '\n' + SETUP_MEMORIA + '\n' + fuente, escenario)


def test_response_text_de_mil_caracteres_pasa_el_validador_de_revision_tras_anonimizar(monkeypatch, tmp_path):
    servicio = _cargar()
    texto = 'abc ' * 250                           # 1.000 caracteres; anonimizado ~3.000
    respuesta = _revision('Plan', 'x', texto)
    respuesta['review']['feedback']['verifications'] = []
    cargado = servicio._scrubbed(copy.deepcopy(respuesta), _corto(servicio))
    cortado = cargado['review']['feedback']['results'][0]['response_text']
    assert len(cortado) <= 1000 and len(cortado.encode('utf8')) <= 2048
    assert cortado.endswith('>') or '<' not in cortado[-9:]     # no parte una marca
    escenario = ("await resolve(" + json.dumps(cargado, ensure_ascii=False) + ");"
                 "assert.match(ids['review-status'].textContent,/consumida/i);"
                 "assert.ok(ids['review-feedback'].textContent.includes('<usuario>'));")
    fuente = (SCRIPTS.parent / 'assets/panel-review.js').read_text(encoding='utf8')
    _node(tmp_path, HARNESS_REVISION + '\n' + fuente, escenario)


def test_recorte_no_parte_una_marca_ni_un_caracter():
    servicio = _cargar()
    texto = 'x' * 155 + '<usuario>' + 'y' * 20
    for tope in range(150, 175):
        corte = servicio._clip(texto, tope)
        assert len(corte) <= tope
        assert corte in (texto[:tope], texto[:155])
        assert '<usuario>' in corte or '<' not in corte
    assert servicio._clip('a\U0001F680' * 10, 5) == 'a\U0001F680a\U0001F680a'
    assert len(servicio._clip('é' * 600, 1000, 1024).encode('utf8')) <= 1024


def test_recorte_no_parte_la_marca_del_redactor():
    """M-F1-3 (revision de la fase 1): `[secreto redactado]` (`redact.REDACTADO`) tampoco se parte."""
    servicio = _cargar()
    marca = '[secreto redactado]'
    assert marca == servicio._load_shared('redact.py').REDACTADO
    texto = 'x' * 150 + marca + 'y' * 20
    for tope in range(140, 190):
        corte = servicio._clip(texto, tope)
        assert len(corte) <= tope
        assert marca in corte or '[' not in corte, (tope, corte[-25:])
        assert corte in (texto[:tope], texto[:150])


# Contrato de `api/cartera` (T-17): el test construye la respuesta REAL con `panel_data.cartera()` sobre un
# proyecto de prueba (no una fixture a mano), la pasa por el saneador unico del servidor y comprueba que cada
# cadena esta clasificada: texto del repo que se muestra (se anonimiza) o vocabulario/forma (queda intacto).
CARTERA_MOSTRADO = {'slug', 'titulo', 'literal', 'est_texto'}
CARTERA_INTACTO = {'source', 'observed_at', 'status', 'id', 'fecha', 'categoria', 'ledger', 'motivo', 'codigo'}


def _proyecto_cartera(tmp_path):
    raiz = tmp_path / 'docs/roadmap'
    a = raiz / '2026-10-01-uno'
    a.mkdir(parents=True)
    (a / 'spec.md').write_text(f'---\nestado: {PLANTADO}\ncreado: 2026-10-01\n---\n# {PLANTADO}\n', encoding='utf8')
    (a / 'evaluation.md').write_text(f'| **Coste** | {PLANTADO} 500 EUR |\n', encoding='utf8')
    (a / 'tasks.md').write_text('# Uno\n\n### T-01 — Uno\n- **Estado**: completado\n\n**Criterios de aceptación**\n- [ ] x\n\n'
                                '## Revisión de dos lentes — intento 1: 1 gap\n\n| # | Grado | Gap | Tarea | Corrección | Evidencia |\n'
                                '|---|---|---|---|---|---|\n| 1 | Minor | g | T-01 | pendiente | e |\n', encoding='utf8')
    b = raiz / '2026-10-02-dos'
    b.mkdir()
    (b / 'spec.md').write_text('---\ncreado: 2026-10-02\n---\n# Dos\n', encoding='utf8')
    c = raiz / '2026-10-03-tres'
    c.mkdir()
    (c / 'tasks.md').write_text('# Tres\n\n### T-01 — Uno\n- **Estado**: completado\n' + '\n' * 300000, encoding='utf8')
    return tmp_path


def _clasifica_cartera(ruta):
    clave = ruta[-1]
    if clave in CARTERA_MOSTRADO:
        return 'mostrado'
    return 'intacto' if clave in CARTERA_INTACTO else None


def test_contrato_cartera_cada_campo_mostrado_anonimizado_y_el_resto_intacto(tmp_path):
    servicio = _cargar()
    respuesta = servicio._load_data().cartera(_proyecto_cartera(tmp_path))
    assert respuesta['status'] == 'ok' and len(respuesta['iniciativas']) == 3
    limpio = servicio._scrubbed(copy.deepcopy(respuesta), _scrub(servicio))
    antes, despues = list(_hojas(respuesta)), list(_hojas(limpio))
    sin_clasificar = {r[-1] for r, _ in antes if _clasifica_cartera(r) is None}
    assert not sin_clasificar, f'campo de texto sin clasificar en el contrato de api/cartera: {sin_clasificar}'
    vistos = set()
    for (ruta, original), (_, nuevo) in zip(antes, despues):
        tipo = _clasifica_cartera(ruta); vistos.add(ruta[-1])
        if tipo == 'mostrado':
            for sensible in SENSIBLES:
                assert sensible not in nuevo, (ruta, sensible)
        else:
            assert nuevo == original, ruta
    assert CARTERA_MOSTRADO <= vistos           # la respuesta real ejerce todos los campos mostrados
    assert {'ilegible', 'ok', 'fuera_de_tope'} <= {f['categoria'] for f in respuesta['iniciativas']} | {f['ledger'] for f in respuesta['iniciativas']}


def test_cartera_de_160_pasa_el_validador_de_las_paginas_tras_anonimizar(tmp_path):
    servicio = _cargar()
    scrub = _corto(servicio)
    carpeta = tmp_path / 'docs/roadmap/2026-10-01-abc'
    carpeta.mkdir(parents=True)
    (carpeta / 'spec.md').write_text('---\nestado: ' + 'abc ' * 12 + '\n---\n# ' + 'abc ' * 40 + '\n', encoding='utf8')
    (carpeta / 'evaluation.md').write_text('| **Coste** | ' + 'abc ' * 30 + ' 5 EUR |\n', encoding='utf8')
    respuesta = servicio._load_data().cartera(tmp_path)
    limpio = servicio._scrubbed(respuesta, scrub)['iniciativas'][0]
    assert len(limpio['titulo']) <= 160 and len(limpio['slug']) <= 80
    assert len(limpio['coste']['est_texto']) <= 120 and len(limpio['literal']) <= 48
    assert '<usuari' not in limpio['titulo'].replace('<usuario>', '')


# Contrato de `api/plan-<id16>` (T-23): como el de `api/cartera`, la respuesta se construye con el productor REAL
# (`panel_data.plan` sobre `ledger-view.py`) y se pasa por el saneador unico y el recorte del servidor
# (`_plan_body`). Cada cadena esta clasificada: texto del ledger que se muestra (se anonimiza y se recorta al tope
# del validador de `page-plan.js`) o vocabulario/forma (queda intacto). Un campo nuevo sin clasificar rompe el test.
PLAN_MOSTRADO = {'slug', 'titulo', 'fase_nombre', 'literal'}
PLAN_INTACTO = {'source', 'observed_at', 'status', 'id', 'vocabulario', 'estado_tarea', 'fuente'}


def _proyecto_plan(tmp_path):
    carpeta = tmp_path / 'docs/roadmap/2026-10-01-plan'
    carpeta.mkdir(parents=True)
    (carpeta / 'improvement-plan.md').write_text('# plan\n', encoding='utf8')
    (carpeta / 'tasks.md').write_text(
        f'# L\n\n## Fase 1 — {PLANTADO}\n\n### T-01 — {PLANTADO}\n- **Estado**: completado\n'
        '- **Tiempo IA (ejec.)**: est. 0,5h · real 0,4h (medido)\n\n**Criterios de aceptación**\n- [x] a\n\n'
        f'### T-02 — {PLANTADO}\n- **Estado**: 🚧 bloqueada\n\n'
        '## Revisión de dos lentes — intento 1: 1 gap\n\n| # | Grado | Gap | Tarea | Corrección | Evidencia |\n'
        '|---|---|---|---|---|---|\n| 1 | Minor | g | T-01 | pendiente | e |\n', encoding='utf8')
    return tmp_path


def _clasifica_plan(ruta):
    clave = ruta[-1]
    if clave in PLAN_MOSTRADO:
        return 'mostrado'
    return 'intacto' if clave in PLAN_INTACTO else None


def test_contrato_plan_cada_campo_mostrado_anonimizado_y_el_resto_intacto(tmp_path):
    servicio = _cargar()
    ident = hashlib.sha256(b'2026-10-01-plan').hexdigest()[:16]
    respuesta = servicio._load_data().plan(_proyecto_plan(tmp_path), ident)
    assert respuesta['status'] == 'ok' and [t['estado_tarea'] for t in respuesta['tareas']] == ['completado', None]
    limpio = json.loads(servicio._plan_body(copy.deepcopy(respuesta), _scrub(servicio)))
    antes, despues = list(_hojas(respuesta)), list(_hojas(limpio))
    sin_clasificar = {r[-1] for r, _ in antes if _clasifica_plan(r) is None}
    assert not sin_clasificar, f'campo de texto sin clasificar en el contrato de api/plan-<id16>: {sin_clasificar}'
    vistos = set()
    for (ruta, original), (_, nuevo) in zip(antes, despues):
        tipo = _clasifica_plan(ruta); vistos.add(ruta[-1])
        if tipo == 'mostrado':
            for sensible in SENSIBLES:
                assert sensible not in nuevo, (ruta, sensible)
        else:
            assert nuevo == original, ruta
    assert PLAN_MOSTRADO - {'slug'} <= vistos        # la respuesta real ejerce todos los campos mostrados
    assert limpio['tareas'][0]['gaps'] == 1 and limpio['tareas'][1]['literal'] == 'bloqueada'


def test_plan_de_160_pasa_el_validador_de_la_pagina_tras_anonimizar(tmp_path):
    servicio = _cargar()
    scrub = _corto(servicio)
    carpeta = tmp_path / 'docs/roadmap/2026-10-01-abc'
    carpeta.mkdir(parents=True)
    (carpeta / 'tasks.md').write_text('# L\n\n## Fase 1 — ' + 'abc ' * 40 + '\n\n### T-01 — ' + 'abc ' * 40 + '\n- **Estado**: completado\n', encoding='utf8')
    ident = hashlib.sha256(b'2026-10-01-abc').hexdigest()[:16]
    fila = json.loads(servicio._plan_body(servicio._load_data().plan(tmp_path, ident), scrub))['tareas'][0]
    assert len(fila['titulo']) <= 160 and len(fila['fase_nombre']) <= 160
    assert '<usuari' not in fila['titulo'].replace('<usuario>', '')


# Contrato de `api/plan-<id16>-<T-XX>` (T-24): igual que el de `api/plan-<id16>`, con el productor REAL
# (`panel_data.tarea`) y el saneado y recorte del servidor (`_tarea_body`). Todo texto del ledger que se muestra se
# anonimiza y se recorta al tope del validador de `page-plan.js`; vocabulario y forma quedan intactos.
TAREA_MOSTRADO = {'titulo', 'fase_nombre', 'literal', 'descripcion', 'criterio', 'verificacion', 'ejecutada', 'salida',
                  'cabecera', 'gap', 'correccion'}
TAREA_INTACTO = {'source', 'observed_at', 'status', 'id', 'tarea_id', 'estado_tarea', 'fuente', 'dependencias',
                 'enlace', 'cerrada', 'grado', 'num'}


def _proyecto_tarea(tmp_path):
    carpeta = tmp_path / 'docs/roadmap/2026-10-01-detalle'
    carpeta.mkdir(parents=True)
    (carpeta / 'improvement-plan.md').write_text('# plan\n', encoding='utf8')
    (carpeta / 'tasks.md').write_text(
        f'# L\n\n## Fase 1 — {PLANTADO}\n\n### T-01 — {PLANTADO}\n- **Descripción**: {PLANTADO}\n- **Estado**: completado\n'
        '- **Tiempo IA (ejec.)**: est. 0,5h · real 0,4h (medido)\n- **Dependencias**: T-02\n'
        f'- **Verificación** (ejecutada 2026-10-15 — salida: {PLANTADO}): {PLANTADO}. Detalle archivado: [execution-history.md](execution-history.md) · SHA-256 `abcdef123456`.\n'
        f'- **Verificación ejecutada** (2026-10-15): {PLANTADO}\n- **Cerrada**: 2026-10-15\n\n'
        f'**Criterios de aceptación**\n- [x] {PLANTADO}\n\n'
        f'## Revisión de dos lentes — intento 1: T-01 {PLANTADO}\n\n| # | Grado | Gap | Tarea | Corrección | Evidencia |\n'
        f'|---|---|---|---|---|---|\n| 1 | Important | {PLANTADO} | T-01 | pendiente | e |\n', encoding='utf8')
    return tmp_path


def _clasifica_tarea(ruta):
    clave = ruta[-1]
    if clave in TAREA_MOSTRADO:
        return 'mostrado'
    return 'intacto' if clave in TAREA_INTACTO else None


def test_contrato_tarea_cada_campo_mostrado_anonimizado_y_el_resto_intacto(tmp_path):
    servicio = _cargar()
    ident = hashlib.sha256(b'2026-10-01-detalle').hexdigest()[:16]
    respuesta = servicio._load_data().tarea(_proyecto_tarea(tmp_path), ident, 'T-01')
    assert respuesta['status'] == 'ok' and respuesta['tarea']['archivado'] == {'enlace': 'execution-history.md'}
    limpio = json.loads(servicio._tarea_body(copy.deepcopy(respuesta), _scrub(servicio)))
    antes, despues = list(_hojas(respuesta)), list(_hojas(limpio))
    sin_clasificar = {r[-1] for r, _ in antes if _clasifica_tarea(r) is None}
    assert not sin_clasificar, f'campo de texto sin clasificar en el contrato de api/plan-<id16>-<T-XX>: {sin_clasificar}'
    vistos = set()
    for (ruta, original), (_, nuevo) in zip(antes, despues):
        tipo = _clasifica_tarea(ruta); vistos.add(ruta[-1])
        if tipo == 'mostrado':
            for sensible in SENSIBLES:
                assert sensible not in nuevo, (ruta, sensible)
        else:
            assert nuevo == original, ruta
    assert TAREA_MOSTRADO - {'literal'} <= vistos          # la respuesta real ejerce todos los campos mostrados
    assert limpio['tarea']['gaps'][0]['grado'] == 'Important' and limpio['tarea']['dependencias'] == ['T-02']


def test_tarea_con_textos_de_los_topes_pasa_el_validador_de_la_pagina_tras_anonimizar(tmp_path):
    servicio = _cargar()
    scrub = _corto(servicio)
    carpeta = tmp_path / 'docs/roadmap/2026-10-01-abc'
    carpeta.mkdir(parents=True)
    larga = 'abc ' * 100
    (carpeta / 'tasks.md').write_text(
        f'# L\n\n## Fase 1\n\n### T-01 — {larga[:160]}\n- **Descripción**: {larga * 3}\n- **Estado**: completado\n'
        f'- **Verificación**: {larga * 5}\n- **Verificación ejecutada** (2026-10-15): {larga * 3}\n\n'
        f'**Criterios de aceptación**\n- [x] {larga}\n\n## Revisión de dos lentes — intento 1: T-01\n\n'
        '| # | Grado | Gap | Tarea | Corrección | Evidencia |\n|---|---|---|---|---|---|\n'
        f'| 1 | Minor | {larga} | T-01 | pendiente | e |\n', encoding='utf8')
    ident = hashlib.sha256(b'2026-10-01-abc').hexdigest()[:16]
    t = json.loads(servicio._tarea_body(servicio._load_data().tarea(tmp_path, ident, 'T-01'), scrub))['tarea']
    assert len(t['titulo']) <= 160 and len(t['descripcion']) <= 1500 and len(t['verificacion']) <= 2000
    assert len(t['salida']) <= 1000 and len(t['criterios'][0]['criterio']) <= 400 and len(t['gaps'][0]['gap']) <= 400
    for campo in ('titulo', 'descripcion', 'verificacion', 'salida'):
        assert '<usuari' not in t[campo].replace('<usuario>', ''), campo



# Contrato de `api/memoria` (T-30..T-35, `panel_data.memoria`): lo que `page-memoria.js` muestra (se anonimiza) y lo que
# es identidad, fecha o vocabulario (queda intacto). Un campo nuevo sin clasificar rompe este test. `area` es clave de
# texto mostrado: por eso las relaciones incrustadas usan `por_area`/`por_iniciativa` (listas de ids, intactas).
MEMORIA_PANEL_MOSTRADO = {'tipo', 'estado', 'area', 'titular', 'candidato', 'category', 'ui_url', 'resumen', 'objetivo',
                          'punto_actual', 'siguientes_pasos', 'bloqueos', 'descartados', 'decisiones', 'pendientes'}
MEMORIA_PANEL_INTACTO = {'id', 'fecha', 'iniciativa', 'origen', 'sustituida_por', 'sustituye_a', 'relacion', 'status',
                         'source', 'observed_at', 'situacion', 'backend', 'ultima', 'sucesion', 'por_iniciativa',
                         'por_area', 'enlaces'}


def _memoria_panel():
    p = PLANTADO
    entrada = {'id': 'ADR-001', 'tipo': p, 'estado': p, 'area': p, 'titular': p, 'fecha': '2026-01-01',
               'iniciativa': 'alfa', 'origen': 'proyecto', 'vigente': True, 'sustituida_por': ['ADR-002'], 'sustituye_a': []}
    return {'version': 1, 'source': 'memoria_panel', 'observed_at': '2026-10-16T10:00:00Z', 'status': 'ok', 'complete': True,
            'issues': [{'status': 'output_budget'}], 'total': 1, 'recortado': 0, 'conteos': {'adr': {'aceptada': 1}},
            'entradas': [entrada],
            'relaciones': {'ADR-001': {'sucesion': [{'relacion': 'sustituida por', 'id': 'ADR-002', 'ausente': False}],
                                       'por_iniciativa': ['ADR-003'], 'por_area': ['ADR-004'], 'enlaces': ['ADR-005'],
                                       'recortado': False}},
            'bandeja': {'estados': {'pending': {'situacion': 'ok', 'n': 1, 'items': [
                {'candidato': p, 'titular': p, 'category': p}]}}, 'aprobadas': {'n': 1, 'items': [
                    {'id': 'ADR-001', 'titular': p, 'area': p}]}},
            'backends': [{'backend': 'kwipu', 'tipo': p, 'situacion': 'configurado', 'entradas': 1,
                          'ultima': '2026-10-02T11:30:00Z', 'interrumpida': False, 'ui_url': 'http://127.0.0.1:9/' + p}],
            'journal': {'status': 'ok', 'sesiones': [{
                'fecha': '2026-10-10', 'iniciativa': 'alfa', 'resumen': p, 'objetivo': p, 'punto_actual': p,
                'siguientes_pasos': [p], 'bloqueos': [p], 'descartados': [p], 'decisiones': [p], 'pendientes': [p]}]}}


def test_contrato_api_memoria_cada_campo_mostrado_anonimizado_y_el_resto_intacto():
    servicio = _cargar()
    dato = _memoria_panel()
    limpio = servicio._scrubbed(copy.deepcopy(dato), _scrub(servicio))
    sin_clasificar = {r[-1] for r, _ in _hojas(dato) if r[-1] not in MEMORIA_PANEL_MOSTRADO | MEMORIA_PANEL_INTACTO}
    assert not sin_clasificar, f'campo de texto sin clasificar en el contrato de api/memoria: {sin_clasificar}'
    originales = dict(_hojas_con_indice(dato))
    for indice, (ruta, texto) in enumerate(_hojas(limpio)):
        if ruta[-1] in MEMORIA_PANEL_MOSTRADO:
            for sensible in SENSIBLES:
                assert sensible not in texto, (ruta, sensible)
        else:
            assert texto == originales[indice], ruta
    assert {r[-1] for r, _ in _hojas(dato)} >= MEMORIA_PANEL_MOSTRADO
    # anonimizar alarga el texto: el recorte a los topes del validador del navegador va DESPUES
    largo = _memoria_panel()
    largo['entradas'][0]['titular'] = 'abc ' * 40
    largo['journal']['sesiones'][0]['objetivo'] = 'abc ' * 60
    recortado = servicio._scrubbed(largo, _corto(servicio))
    assert len(recortado['entradas'][0]['titular']) <= 160 and len(recortado['journal']['sesiones'][0]['objetivo']) <= 240


def test_contrato_api_memoria_la_identidad_no_cerrada_tambien_se_sanean_y_los_ids_cerrados_quedan():
    """F4-1: `iniciativa`, el id de un sucesor ausente y un id de forma libre pasan por el saneador unico (`_scrub_memoria`)."""
    servicio = _cargar()
    dato = _memoria_panel()
    dato['entradas'][0]['iniciativa'] = PLANTADO
    dato['entradas'][0]['sustituida_por'] = ['ADR-002', PLANTADO]
    dato['relaciones']['ADR-001']['sucesion'][0]['id'] = PLANTADO
    dato['journal']['sesiones'][0]['iniciativa'] = PLANTADO
    limpio = servicio._scrub_memoria(dato, _scrub(servicio))
    crudo = json.dumps(limpio, ensure_ascii=False)
    for sensible in SENSIBLES:
        assert sensible not in crudo, sensible
    assert limpio['entradas'][0]['id'] == 'ADR-001' and limpio['entradas'][0]['sustituida_por'][0] == 'ADR-002'
    assert limpio['bandeja']['aprobadas']['items'][0]['id'] == 'ADR-001' and 'ADR-001' in limpio['relaciones']
