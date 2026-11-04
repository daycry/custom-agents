#!/usr/bin/env python3
"""Reproduce this initiative's declared scenario; never measure native billing."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

OWN_ROOT = Path(__file__).resolve().parents[4]
FOLDER = Path('docs/roadmap/2026-11-04-token-efficiency/testing')
REVISION = '9c109c592e5a152a7ad311ad6c13080764fd00f1'
ROLES = ('analyst', 'evaluator', 'architect', 'planner')
POLICIES = ('agent-kits/shared/read-discipline.md', 'agent-kits/shared/output-discipline.md')
REFERENCES = ('agent-kits/planner/references/task-types.md',
    'agent-kits/planner/references/plan-maintenance.md',
    'agent-kits/evaluator/references/code-health.md',
    'agent-kits/shared/references/source-reuse.md')


def load(path):
    with path.open('rb') as stream:
        raw = stream.read(1024 * 1024 + 1)
    if len(raw) > 1024 * 1024:
        raise ValueError('input budget')
    data = json.loads(raw.decode('utf-8-sig'))
    if not isinstance(data, dict):
        raise ValueError('input object required')
    return data


def footprint():
    spec = importlib.util.spec_from_file_location('audit_footprint', OWN_ROOT / 'agent-kits/shared/context-footprint.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def bindings(record):
    value = record.get('role_policy_paths')
    if not isinstance(value, dict) or set(value) != set(ROLES):
        raise ValueError('invalid scenario bindings')
    for paths in value.values():
        if (not isinstance(paths, list) or not all(isinstance(p, str) and p in POLICIES for p in paths)
                or len(set(paths)) != len(paths)):
            raise ValueError('invalid policy binding')
    return value


def capture(root):
    api = footprint()
    maps = ['agents/' + role + '.md' for role in ROLES]
    current = api.report(root, maps + list(POLICIES) + list(REFERENCES))
    if not current['complete']:
        raise ValueError('incomplete sources')
    reader = api.helper().module('local-read.py')
    measured = {r['path']: r for r in current['files']}
    selected = {}
    for role, path in zip(ROLES, maps):
        source = reader.read_bytes(root, path, max_bytes=256 * 1024, include_digest=True)
        if source['status'] != 'ok' or source['sha256'] != measured[path]['sha256']:
            raise ValueError('source changed during calculation')
        text = source['data'].decode('utf-8-sig')
        selected[role] = [p for p in POLICIES if Path(p).name in text]
    return {'footprint': current, 'role_policy_paths': selected}


def calculate(root, current=False):
    root = Path(root)
    baseline = load(root / FOLDER / 'scenario-before.json')
    if baseline.get('source_revision') != REVISION:
        raise ValueError('invalid scenario baseline')
    before_bindings = bindings(baseline)
    snapshot = capture(root) if current else load(root / FOLDER / 'scenario-after.json')
    after_bindings = bindings(snapshot)
    api = footprint()
    maps = ['agents/' + role + '.md' for role in ROLES]
    after = snapshot['footprint']
    if (not api.comparison(after, after)['comparable']
            or {r['path'] for r in after['files']} != set(maps + list(POLICIES) + list(REFERENCES))):
        raise ValueError('invalid scenario sources')
    core = dict(after, files=[r for r in after['files'] if r['path'] not in REFERENCES])
    before = baseline.get('footprint')
    if not api.comparison(core, before)['comparable']:
        raise ValueError('incomplete or incomparable sources')
    old = {r['path']: r['characters'] for r in before['files']}
    new = {r['path']: r['characters'] for r in after['files']}
    rows = []
    for role, path in zip(ROLES, maps):
        old_policy = sum(old[p] for p in before_bindings[role])
        new_policy = sum(new[p] for p in after_bindings[role])
        rows.append({'role': role, 'map_before_characters': old[path], 'map_after_characters': new[path],
            'before_policy_characters': old_policy, 'after_policy_characters': new_policy,
            'estimated_input_tokens_saved': (old[path] + old_policy - new[path] - new_policy) / 4})
    return {'method': 'characters/4, not native tokenizer or billed usage', 'baseline': REVISION,
        'scenario': 'One fresh context per PM role. Entire role map plus each directly referenced shared read/output policy, once. No new conditional reference. Excludes unchanged native wrappers and other existing resources, project reads, tool results, outputs and retries.',
        'roles': rows, 'estimated_input_tokens_saved_total': sum(r['estimated_input_tokens_saved'] for r in rows),
        'conditional_reference_estimated_tokens': {p: new[p] / 4 for p in sorted(REFERENCES)},
        'native_usage': None, 'output_token_savings': None, 'quality_or_billing_guarantee': False}


def render(report):
    total = report['estimated_input_tokens_saved_total']
    costs = report['conditional_reference_estimated_tokens']
    lines = ['# Cuántos tokens se podrían ahorrar', '',
        'Escenario: una pasada de analyst, evaluator, architect y planner, cada uno',
        'con contexto separado. Cuenta el mapa completo y las políticas de lectura/salida',
        'directamente referidas, una vez. No carga referencias nuevas condicionales.', '',
        f'**Estimación: unos {round(total / 10) * 10} tokens de entrada menos por recorrido PM.**',
        'Método: caracteres UTF-8 normalizados a LF / 4. No es un tokenizer nativo,',
        'consumo real medido ni una garantía de facturación.', '',
        '| Rol | Tokens de entrada estimados que se eliminan |', '|---|---:|']
    lines.extend(f"| {r['role']} | {r['estimated_input_tokens_saved']:.2f} |" for r in report['roles'])
    lines.extend([f'| Total del escenario | {total:.2f} |', '',
        'Se excluyen envolturas nativas sin cambios, otros recursos previos, lecturas',
        'del proyecto, herramientas, respuestas y reintentos. La carga del cliente,',
        'el tokenizer y la caché pueden cambiar el resultado. No se estima dinero.', '',
        '## Costes condicionales', '',
        'Leer cada archivo completo una vez añade este presupuesto de entrada:', '',
        '| Referencia | Tokens estimados adicionales |', '|---|---:|'])
    lines.extend(f'| `{Path(path).name}` | {value:.2f} |' for path, value in costs.items())
    lines.extend([f'| Todas, una vez | {sum(costs.values()):.2f} |', '',
        f'Si se cargan todas, antes de contar lecturas evitadas, habría unos {round(sum(costs.values()) - total)}',
        'tokens adicionales. Una referencia puede necesitarse en varios contextos.',
        'No hay un ahorro universal garantizado.', '',
        'Evitar releer 20.000 caracteres equivale aproximadamente a 5.000 tokens por',
        'lectura evitada. Es un ejemplo de cálculo, no una observación. Hay que',
        'descontar recibos, interpretación y referencias necesarias.', '',
        'El consumo real total exige ejecuciones equivalentes con medidas nativas:',
        'mismo modelo, objetivo, calidad y condiciones. No se han lanzado sesiones',
        'de pago para este informe. Consumo observado y ahorro de salida: desconocidos.', '',
        '## Reproducir y comprobar', '',
        '`python docs/roadmap/2026-11-04-token-efficiency/testing/audit-token-estimates.py`',
        'reproduce los snapshots versionados y comprueba JSON y Markdown: exit 0',
        'vigentes, 1 cifras distintas, 2 entrada inválida o ausente. `--current` compara',
        'además con las fuentes actuales; no obliga a reescribir evidencia histórica.',
        '`--generate` emite JSON por stdout; `--generate --markdown` emite este texto.',
        '`--capture-current` emite el snapshot actual por stdout. No escribe archivos.', '',
        'Fuentes: scenario-before.json (commit original y políticas literales),',
        'scenario-after.json y token-estimates.json. No contienen datos privados.'])
    return '\n'.join(lines) + '\n'


def inventory(root, current=False):
    root = Path(root)
    calculate(root, current)  # Validate the scenario snapshots too.
    before = load(root / FOLDER / 'context-before.json')
    api = footprint()
    after = (api.report(root, [r['path'] for r in before['files']]) if current
             else load(root / FOLDER / 'context-after.json'))
    comparison = api.comparison(after, before)
    if not comparison['comparable'] or not api.comparison(after, after)['comparable']:
        raise ValueError('invalid inventory')
    old = {r['path']: r['characters'] for r in before['files']}
    new = {r['path']: r['characters'] for r in after['files']}
    baseline = load(root / FOLDER / 'scenario-before.json')['footprint']
    snapshot = capture(root)['footprint'] if current else load(root / FOLDER / 'scenario-after.json')['footprint']
    old_policy = sum(r['characters'] for r in baseline['files'] if r['path'] in POLICIES)
    new_policy = sum(r['characters'] for r in snapshot['files'] if r['path'] in POLICIES)
    references = sum(r['characters'] for r in snapshot['files'] if r['path'] in REFERENCES)
    return {'same_60_entry_maps': comparison,
        'pm_four_roles': {'before': sum(old['agents/' + r + '.md'] for r in ROLES),
                          'after': sum(new['agents/' + r + '.md'] for r in ROLES)},
        'added_conditional_reference_characters': references,
        'shared_policy_before': old_policy, 'shared_policy_after': new_policy,
        'all_references_and_shared_loaded_delta': comparison['delta_characters'] + references + new_policy - old_policy,
        'runtime_usage': None}


def inventory_table(summary):
    def number(value): return f'{value:,}'.replace(',', '.')
    def delta(value): return f'{value:+,}'.replace(',', '.')
    def reduction(before, after):
        return f"({(before - after) * 100 / before:.2f} %)".replace('.', ',') if before else '(sin base)'
    pm = summary['pm_four_roles']
    maps = summary['same_60_entry_maps']
    references = summary['added_conditional_reference_characters']
    before = maps['before_characters'] + summary['shared_policy_before']
    after = maps['after_characters'] + references + summary['shared_policy_after']
    lines = ['| Selección | Antes | Después | Diferencia |', '|---|---:|---:|---:|',
        f"| Cuatro roles PM: analyst, evaluator, architect y planner | {number(pm['before'])} | {number(pm['after'])} | {delta(pm['after'] - pm['before'])} {reduction(pm['before'], pm['after'])} |",
        f"| Los mismos 60 mapas | {number(maps['before_characters'])} | {number(maps['after_characters'])} | {delta(maps['delta_characters'])} {reduction(maps['before_characters'], maps['after_characters'])} |",
        f'| Referencias condicionales añadidas | 0 | {number(references)} | {delta(references)} |',
        f"| Políticas compartidas de lectura y salida | {number(summary['shared_policy_before'])} | {number(summary['shared_policy_after'])} | {delta(summary['shared_policy_after'] - summary['shared_policy_before'])} |",
        f'| Mapas + todas las referencias nuevas + políticas una vez | {number(before)} | {number(after)} | {delta(after - before)} |']
    return '\n'.join(lines) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=OWN_ROOT)
    parser.add_argument('--generate', action='store_true')
    parser.add_argument('--markdown', action='store_true')
    parser.add_argument('--current', action='store_true')
    parser.add_argument('--capture-current', action='store_true')
    parser.add_argument('--inventory', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.capture_current:
            print(json.dumps(capture(args.root), ensure_ascii=False, indent=2))
            return 0
        if args.inventory:
            expected_inventory = inventory(args.root, args.current)
            table = inventory_table(expected_inventory)
            if args.generate:
                print(table, end='') if args.markdown else print(json.dumps(expected_inventory, indent=2))
                return 0
            saved = load(args.root / FOLDER / 'measurement-summary.json')
            markdown = (args.root / FOLDER / 'measurements.md').read_text(encoding='utf-8')
            complete = saved == expected_inventory and table.strip() in markdown
            print(json.dumps({'status': 'ok' if complete else 'stale', 'runtime_usage': None}))
            return 0 if complete else 1
        expected = calculate(args.root, args.current)
        if args.generate:
            print(render(expected), end='') if args.markdown else print(json.dumps(expected, ensure_ascii=False, indent=2))
            return 0
        saved = load(args.root / FOLDER / 'token-estimates.json')
        markdown = (args.root / FOLDER / 'token-estimates.md').read_text(encoding='utf-8')
        complete = saved == expected and markdown == render(expected)
        print(json.dumps({'status': 'ok' if complete else 'stale',
            'estimated_input_tokens_saved': expected['estimated_input_tokens_saved_total'],
            'native_usage': None}))
        return 0 if complete else 1
    except (OSError, ValueError, TypeError, KeyError, ImportError, AttributeError, RecursionError):
        print(json.dumps({'status': 'unavailable'}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
