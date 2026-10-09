"""Pure portable doctor projection; bounded schema, scope and historical time."""
import datetime as dt
import hashlib
import os
import re
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

MAX_ROWS = 512
MAX_BYTES = 65536
BLOCK_IDS = ('herramientas', 'plugin', 'configs', 'estado', 'capacidades', 'memoria', 'journal', 'version')
STATES = ('ok', 'aviso', 'error', 'info')
PUBLIC_CHECK_TITLES = frozenset({
    'python3', 'git', 'bash', 'jq', 'node/npm', 'Playwright', 'raíz del plugin',
    'hook sin script', 'hook no ejecutable', 'hooks registrados', 'hooks/hooks.json',
    'registro del plugin', 'registro con valor inválido', 'registro con scope desconocido',
    'registro sin proyecto atribuible', 'registro en Codex', 'estado nativo en Codex',
    'registro en OpenCode', 'statusline', 'nombre de los comandos',
    'doc viva sin el espacio de nombres', 'rates.json', 'dev.json `guardrails`',
    'dev.json `revision`', 'dev.json `revision.excluir`', 'dev.json `sesion`',
    'dev.json `tests`', 'dev.json `tests.coberturaMinima`', 'dev.json `modelos`', 'dev.json',
    'marcadores de medición', 'marcador huérfano', 'iniciativas', 'iniciativa en progreso',
    'journal de sesión', 'informes de evals', 'capacidades opcionales',
    'índice de memoria (README)', 'índice de búsqueda (FTS5)', 'calibración (CALIBRATION.md)',
    'memoria técnica', 'memoria curada', 'plugin.json', 'versión del plugin',
    'versión vista en este proyecto', 'cola del journal', 'sesiones en dead-letter',
    'items en backoff', 'Hook cancelled (triage)',
})
TOP_KEYS = {'version', 'producer', 'checked_at', 'scope_key', 'complete', 'blocks', 'summary', 'priorities'}


def scope_key(root):
    """Bind normalized absolute spelling, not physical filesystem identity."""
    value = os.path.normcase(os.path.abspath(os.fspath(root)))
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def _counts(blocks):
    result = dict.fromkeys(STATES, 0)
    for block in blocks:
        for row in block['rows']:
            result[row['state']] += 1
    return result


def project(inf, *, checked_at=None):
    """Only enumerated public metadata leaves the original doctor result."""
    checked_at = checked_at or dt.datetime.now(dt.timezone.utc)
    if checked_at.tzinfo is None:
        raise ValueError('timezone required')
    blocks, seen, remaining, complete = [], set(), MAX_ROWS, True
    for block in inf['bloques']:
        key = block['clave']
        if key not in BLOCK_IDS or key in seen:
            raise ValueError('unsupported diagnostic block')
        seen.add(key)
        lines = block['lineas']
        complete = complete and len(lines) <= remaining
        rows = []
        for line in lines[:remaining]:
            if line['estado'] not in STATES:
                raise ValueError('unsupported diagnostic state')
            title = line.get('que')
            rows.append({'state': line['estado'], 'label': title if title in PUBLIC_CHECK_TITLES else ''})
        remaining -= len(rows)
        blocks.append({'id': key, 'rows': rows})
    priorities = []
    if complete:
        indexed = {block['id']: block['rows'] for block in blocks}
        for action in inf['acciones_prioritarias']['acciones'][:3]:
            key, ordinal = action['bloque'], action['linea']
            if (key not in indexed or type(ordinal) is not int or not 1 <= ordinal <= len(indexed[key])
                    or indexed[key][ordinal-1]['state'] not in ('error', 'aviso')):
                raise ValueError('unsupported priority reference')
            priorities.append({'block': key, 'row': ordinal})
    return {'version': 1, 'producer': 'doctor',
            'checked_at': checked_at.astimezone(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
            'scope_key': scope_key(inf['proyecto']), 'complete': complete,
            'blocks': blocks, 'summary': _counts(blocks), 'priorities': priorities}


def _validate(report):
    if (not isinstance(report, dict) or set(report) != TOP_KEYS or type(report['version']) is not int
            or report['version'] != 1 or report['producer'] != 'doctor' or type(report['complete']) is not bool
            or not isinstance(report['scope_key'], str) or not re.fullmatch('[a-f0-9]{64}', report['scope_key'])):
        raise ValueError('shape')
    stamp = report['checked_at']
    if not isinstance(stamp, str) or not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', stamp):
        raise ValueError('timestamp')
    measured = dt.datetime.strptime(stamp, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=dt.timezone.utc)
    blocks = report['blocks']
    if not isinstance(blocks, list) or len(blocks) > len(BLOCK_IDS):
        raise ValueError('blocks')
    seen, count, indexed = set(), 0, {}
    for block in blocks:
        if not isinstance(block, dict) or set(block) != {'id', 'rows'} or block['id'] not in BLOCK_IDS or block['id'] in seen:
            raise ValueError('block')
        key = block['id']; seen.add(key)
        if not isinstance(block['rows'], list):
            raise ValueError('rows')
        count += len(block['rows'])
        if count > MAX_ROWS:
            raise ValueError('row limit')
        for row in block['rows']:
            if (not isinstance(row, dict) or set(row) != {'state', 'label'} or row['state'] not in STATES
                    or not isinstance(row['label'], str) or row['label'] not in PUBLIC_CHECK_TITLES | {''}):
                raise ValueError('row')
        indexed[key] = block['rows']
    summary = report['summary']
    if (not isinstance(summary, dict) or set(summary) != set(STATES)
            or any(type(n) is not int or not 0 <= n <= MAX_ROWS for n in summary.values())
            or summary != _counts(blocks)):
        raise ValueError('summary')
    actions = report['priorities']
    if not isinstance(actions, list) or len(actions) > 3 or (not report['complete'] and actions):
        raise ValueError('priorities')
    references, previous = set(), -1
    for action in actions:
        if not isinstance(action, dict) or set(action) != {'block', 'row'}:
            raise ValueError('priority')
        key, ordinal = action['block'], action['row']
        if (not isinstance(key, str) or key not in indexed or type(ordinal) is not int
                or not 1 <= ordinal <= len(indexed[key]) or (key, ordinal) in references):
            raise ValueError('priority reference')
        state = indexed[key][ordinal-1]['state']
        if state not in ('error', 'aviso'):
            raise ValueError('priority state')
        rank = ('error', 'aviso').index(state)
        if rank < previous:
            raise ValueError('priority order')
        previous = rank; references.add((key, ordinal))
    return measured


def consume(report, *, project=None, now=None):
    """Validate data before scope/time interpretation; never run diagnostics."""
    try:
        measured = _validate(report)
    except (ValueError, TypeError, KeyError, OverflowError):
        return {'status': 'incompatible'}
    if project is None:
        return {'status': 'scope_unbound'}
    if scope_key(project) != report['scope_key']:
        return {'status': 'scope_mismatch'}
    now = now or dt.datetime.now(dt.timezone.utc)
    if measured > now:
        return {'status': 'future_timestamp'}
    age = (now-measured).total_seconds()
    return {'status': 'accepted' if report['complete'] else 'incomplete',
            'age_status': 'old_snapshot' if age > 86400 else 'recent_snapshot', 'report': report}
