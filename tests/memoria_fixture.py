"""Fixture de Memoria del panel (F4): un proyecto con corpus, candidatos, backends, outbox y journal. Datos genericos."""
import json
from pathlib import Path
import sys

SECRETO = 'sk-ant-api03-ABCDEFGHIJKLMNOPQRSTUV0123456789'


def _md(ruta, **fm):
    cuerpo = fm.pop('cuerpo', 'Cuerpo de la entrada.')
    cabecera = ''.join(f'{k}: {v}\n' for k, v in fm.items())
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text('---\n' + cabecera + '---\n\n# ' + str(fm.get('titulo', '')) + '\n\n' + cuerpo + '\n', encoding='utf8')


def crear_proyecto(raiz, *, secreto_en_journal=False):
    k = Path(raiz) / 'docs/knowledge'
    ds = 'Datos / almacenamiento'
    _md(k / 'adr/ADR-001-a.md', id='ADR-001', titulo='Almacen A', estado='obsoleta', fecha='2026-01-10', area=ds,
        iniciativa='alfa', sucesor='ADR-002')
    _md(k / 'adr/ADR-002-b.md', id='ADR-002', titulo='Almacen B', estado='aceptada', fecha='2026-02-10', area=ds,
        iniciativa='alfa', sucesor='ADR-003')
    _md(k / 'adr/ADR-003-c.md', id='ADR-003', titulo='Almacen C', estado='aceptada', fecha='2026-03-10', area=ds,
        iniciativa='alfa', sustituye='ADR-002')
    _md(k / 'adr/ADR-004-d.md', id='ADR-004', titulo='Obsoleta sin sucesor', estado='obsoleta', fecha='2026-01-05',
        area='Otra cosa distinta')
    _md(k / 'gotchas/GOT-001-e.md', id='GOT-001', titulo='Sesiones caducan', estado='aceptada', fecha='2026-02-01',
        area='Seguridad / sesiones')
    _md(k / 'gotchas/GOT-002-f.md', id='GOT-002', titulo='Propuesta de sesiones', estado='propuesta', fecha='2026-02-02',
        area='Seguridad / sesiones')
    _md(k / 'lessons/LES-001-g.md', id='LES-001', titulo='Medir antes', estado='aceptada', fecha='2026-02-20', area=ds,
        iniciativa='alfa')
    for estado, nombres in {'pending': ('2026-10-01-uno.md', '2026-10-02-dos.md'), 'needs_changes': ('2026-10-03-tres.md',),
                            'rejected': ()}.items():
        (k / 'candidates' / estado).mkdir(parents=True, exist_ok=True)
        for n in nombres:
            (k / 'candidates' / estado / n).write_text(
                '---\nproposed_by: documenter\ncategory: GOTCHA\n---\n# Candidato ' + n[:-3] + '\n\nTexto.\n', encoding='utf8')
    (k / 'candidates' / 'rejected' / '.gitkeep').write_text('', encoding='utf8')
    ks = Path(raiz) / '.claude/knowledge-services'
    ks.mkdir(parents=True, exist_ok=True)
    rutas = {'memoria-a': True, 'memoria-b': True}
    categorias = [{'key': 'DECISION', 'folder': 'adr', 'min_evidence': 'human_confirmed_rule', 'routing': dict(rutas)},
                  {'key': 'GOTCHA', 'folder': 'gotchas', 'min_evidence': 'validated_case', 'routing': dict(rutas)},
                  {'key': 'LESSON', 'folder': 'lessons', 'min_evidence': 'single_case', 'routing': dict(rutas)}]
    (ks / 'taxonomy.json').write_text(json.dumps({
        'version': 1, 'utility_scoring': False, 'categories': categorias,
        'backends': {
            'memoria-a': {'type': 'externo', 'enabled': True, 'config': {}},
            'memoria-b': {'type': 'externo', 'enabled': True, 'config': {}}},
        'evidence_levels': ['observation', 'single_case', 'validated_case', 'multiple_validated_cases', 'human_confirmed_rule'],
        'denylist': ['chain-of-thought']}), encoding='utf8')
    done = ks / '_sync-outbox/memoria-a/done'
    done.mkdir(parents=True)
    (done / 'sync-1.json.manifest.json').write_text(json.dumps({'completado_en': '2026-09-01T10:00:00Z'}), encoding='utf8')
    (done / 'sync-2.json.manifest.json').write_text(json.dumps({'completado_en': '2026-10-02T11:30:00Z'}), encoding='utf8')
    j = k / 'journal'
    j.mkdir(parents=True, exist_ok=True)
    objetivo = 'Cerrar la fase con token=' + SECRETO if secreto_en_journal else 'Cerrar la fase'
    (j / '2026-10-10-alfa.md').write_text(
        '---\nfecha: "2026-10-10"\nsession_id: "s-1"\nreason: "other"\niniciativa: "alfa"\nresumen: "Sesion de prueba"\n'
        'fuente: "hook"\ncierre: "materializado"\nresumen_por: "determinista"\nturnos: 3\n'
        'materializado_en: "2026-10-10T10:00:00Z"\ndecisiones:\n  - "Usar la cola"\npendientes:\n  - "Revisar el gap"\n'
        'objetivo: "' + objetivo + '"\npunto_actual: "En la tarea 3"\nsiguientes_pasos:\n  - "Cerrar la tarea"\n'
        'bloqueos:\n  - "Falta el dato"\ndescartados:\n  - "Polling - caro"\n---\n\n# Journal\n', encoding='utf8')
    return Path(raiz)
