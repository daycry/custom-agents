"""Confirmacion del intento 3 de panel-redesign: C-1 (contrato del saneado servido) y C-3 (topes tras anonimizar).

Datos de prueba genericos (`jdoe@example.org`, `jdoeuser`); nada del equipo donde se ejecuta.
"""
import copy
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
