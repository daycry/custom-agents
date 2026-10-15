"""Explicit loopback transport for local ledger and canonical memory reads."""
from datetime import datetime, timezone
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, HTTPServer
import importlib.util
import json
from pathlib import Path
import re
import secrets
import sys
import time

HERE = Path(__file__).resolve().parent
MAX_SCAN = 128
MAX_FILE_BYTES = 256 * 1024
MAX_READ_BYTES = 1024 * 1024
MAX_INITIATIVES = 64
MAX_RESPONSE_BYTES = 65536
MAX_REQUEST_BYTES = 4096
BODY_TIMEOUT = 3
MAX_REVIEW_REQUEST_BYTES = 16 * 1024
MAX_REVIEW_RESPONSE_BYTES = 512 * 1024
MAX_REVIEW_IDS = 128
REVIEW_OPEN_GATE = 'requested-review'  # the only gate the browser can open; `plan-ok` belongs to the orchestrator
TOO_MANY_REVIEWS = 'demasiadas revisiones abiertas en este proceso'
STATES = {'borrador', 'en-progreso', 'en-revision', 'completado', 'cancelado'}


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError('bundled helper unavailable')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_shared(filename):
    return _load('panel_service_' + filename.replace('-', '_'), HERE.parents[2] / 'agent-kits/shared' / filename)


def _load_builder():
    return _load('panel_service_builder', HERE / 'build_panel.py')


PLAN_PAGE = re.compile(r'plan-[a-f0-9]{16}\.html')
PLAN_API = re.compile(r'api/plan-([a-f0-9]{16})')
TAREA_API = re.compile(r'api/plan-([a-f0-9]{16})-(T-\d{1,4})')
REVIEW_OPEN_API = re.compile(r'api/review-open/([a-f0-9]{16})')
REVIEW_CURRENT_API = re.compile(r'api/review-current/([a-f0-9]{16})')
# Same shape as plan-review.py INITIATIVE (the owner validates it again before any write).
_INITIATIVE_FOLDER = re.compile(r'[0-9]{4}-[0-9]{2}-[0-9]{2}-[a-z0-9]+(?:-[a-z0-9]+)*')
ASSET_TYPES = {'.css': 'text/css; charset=utf-8', '.js': 'text/javascript; charset=utf-8',
               '.json': 'application/json; charset=utf-8', '.md': 'text/markdown; charset=utf-8'}


def _load_memory():
    return _load_shared('knowledge-view.py')


def _load_data():
    return _load('panel_service_data', HERE / 'panel_data.py')


def _load_review():
    return _load_shared('plan-review.py')


def _review_failure(reason='reader_unavailable'):
    return {'schema_version': 1, 'status': 'unavailable', 'reason': reason, 'review': None}


def _review_code(result):
    if result.get('status') in ('version_changed', 'conflict'):
        return 409
    reason = result.get('reason') or ''
    if reason in ('invalid_input', 'invalid_comments', 'comments_required', 'invalid_version'):
        return 400
    if reason.endswith('_budget'):
        return 413
    return 200 if result.get('status') in ('ok', 'waiting') else 503


def _review_payload_error(operation, payload, review_id):
    """Validate transport shapes; the owner checks section membership and CAS."""
    if type(payload) is not dict:
        return 400
    if operation == 'refresh':
        return None if set(payload) == {'review_id'} and payload['review_id'] == review_id else 400
    fields = {'version', 'comments', 'expected_revision'}
    if operation == 'submit':
        fields.add('choice')
        if payload.get('choice') not in ('approve', 'request_changes'):
            return 400
    if set(payload) != fields or type(payload['expected_revision']) is not int or payload['expected_revision'] < 0:
        return 400
    version = payload['version']
    if (type(version) is not dict or set(version) != {'raw_sha256', 'view_sha256', 'view_version'}
            or version['view_version'] != 'plan-text-v1'
            or any(type(version[key]) is not str or re.fullmatch('[a-f0-9]{64}', version[key]) is None
                   for key in ('raw_sha256', 'view_sha256'))):
        return 400
    comments = payload['comments']
    if type(comments) is not list:
        return 400
    if len(comments) > 20:
        return 413
    identities = set(); total = 0
    for row in comments:
        if type(row) is not dict or set(row) != {'comment_id', 'section_id', 'text'}:
            return 400
        if (type(row['comment_id']) is not str or re.fullmatch('[A-Za-z0-9_-]{1,64}', row['comment_id']) is None
                or row['comment_id'] in identities or type(row['section_id']) is not str
                or re.fullmatch('[a-f0-9]{64}', row['section_id']) is None
                or type(row['text']) is not str):
            return 400
        if len(row['text']) > 2000:
            return 413
        identities.add(row['comment_id'])
        try: total += len(row['text'].encode('utf8'))
        except UnicodeError: return 400
    return None if total <= 10 * 1024 else 413


def review_initiatives(project):
    """`{id16: 'docs/roadmap/<carpeta>'}` of the initiatives with a plan: the only paths the browser can name
    (by id, never by path). Folders that are not valid initiatives, have no `improvement-plan.md` (listed, never
    read) or collide in id16 (both leave) are out. Never loads the review owner."""
    try:
        reader = _load_shared('local-read.py')
        listing = reader.list_names(project, 'docs/roadmap', max_entries=MAX_SCAN)
        if listing['status'] not in ('ok', 'incomplete'):
            return {}
        found, collided = {}, set()
        for folder in listing['names']:
            if len(folder) > 160 or _INITIATIVE_FOLDER.fullmatch(folder) is None:
                continue
            inner = reader.list_names(project, 'docs/roadmap/' + folder, max_entries=MAX_SCAN)
            if inner['status'] not in ('ok', 'incomplete') or 'improvement-plan.md' not in inner['names']:
                continue
            ident = hashlib.sha256(folder.encode('utf8')).hexdigest()[:16]
            if ident in found:
                collided.add(ident)
            found[ident] = 'docs/roadmap/' + folder
        return {i: path for i, path in sorted(found.items()) if i not in collided}
    except Exception:
        return {}


def _review_summary_failure(reason='reader_unavailable'):
    return {'schema_version': 1, 'status': 'unavailable', 'reason': reason, 'complete': False,
            'observed_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'initiatives': [], 'omitted': 0, 'approval_granted': False}


def _unavailable_memory(operation):
    return {'version': 1, 'source': 'canonical_knowledge',
            'observed_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'operation': operation if operation in ('search', 'show', 'related') else '',
            'status': 'unavailable', 'complete': False,
            'issues': ['reader_unavailable'], 'entries': [], 'selected': None,
            'related': None, 'budget': {'files': 0, 'bytes': 0, 'entries': 0}}


def _unavailable_cartera():
    return {'version': 1, 'source': 'roadmap_cartera', 'status': 'unavailable', 'complete': False,
            'observed_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
            'issues': [{'status': 'reader_unavailable'}], 'iniciativas': [],
            'totales': {'iniciativas': 0, 'por_estado': {}, 'tareas': None, 'fuera_de_tope': [],
                        'coste': {'real_eur': None, 'real_n': 0, 'est_eur': None, 'est_n': 0},
                        'procedencia': {'medidos': 0, 'estimados': 0, 'desconocidos': 0}}}


def _encoded(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False).encode('utf8')


def _unavailable_plan(ident):
    """`api/plan-<id16>` cuando el ledger no se puede proyectar: la misma forma que la respuesta normal, sin cifras."""
    return {'version': 1, 'source': 'ledger_plan', 'status': 'unavailable', 'complete': False,
            'observed_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'), 'id': ident, 'slug': None,
            'issues': [{'status': 'reader_unavailable'}],
            'vocabulario': ['borrador', 'en-progreso', 'en-revision', 'completado', 'cancelado'],
            'omitidas': 0, 'tareas': None}


def _unavailable_tarea(ident, tarea_id):
    return {'version': 1, 'source': 'ledger_tarea', 'status': 'unavailable', 'complete': False,
            'observed_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'), 'id': ident,
            'tarea_id': tarea_id, 'issues': [{'status': 'reader_unavailable'}],
            'omitidos': {'criterios': 0, 'gaps': 0}, 'tarea': None}


def _tarea_body(data, scrub):
    """Cuerpo de `api/plan-<id16>-<T-XX>`: saneado y, si pasa de 64 KiB, recortado con indicador (primero los gaps y
    luego los criterios, del final) y contado en `omitidos`: nunca se inventa lo que falta."""
    limpio = _scrubbed(data, scrub)
    body = _encoded(limpio)
    tarea = limpio.get('tarea')
    if len(body) > MAX_RESPONSE_BYTES and tarea:
        limpio['status'] = 'partial'; limpio['complete'] = False
        if {'status': 'output_budget'} not in limpio['issues']:
            limpio['issues'].append({'status': 'output_budget'})
        for campo, contador in (('gaps', 'gaps'), ('criterios', 'criterios')):
            while len(body) > MAX_RESPONSE_BYTES and tarea[campo]:
                tarea[campo].pop()
                limpio['omitidos'][contador] += 1
                body = _encoded(limpio)
    if len(body) > MAX_RESPONSE_BYTES:
        raise ValueError('response budget')
    return body


def _plan_body(data, scrub):
    """Cuerpo de `api/plan-<id16>`: saneado con el saneador unico y recortado (con indicador, nunca inventando datos)
    hasta que cabe en 64 KiB. El recorte quita tarjetas del final y lo dice en `omitidas`, `status` e `issues`."""
    limpio = _scrubbed(data, scrub)
    body = _encoded(limpio)
    if len(body) > MAX_RESPONSE_BYTES and limpio.get('tareas'):
        limpio['status'] = 'partial'; limpio['complete'] = False
        if {'status': 'output_budget'} not in limpio['issues']:
            limpio['issues'].append({'status': 'output_budget'})
        while len(body) > MAX_RESPONSE_BYTES and limpio['tareas']:
            media = max(1, len(body) // len(limpio['tareas']))
            quitar = min(len(limpio['tareas']), max(1, (len(body) - MAX_RESPONSE_BYTES) // media))
            del limpio['tareas'][-quitar:]
            limpio['omitidas'] += quitar
            body = _encoded(limpio)
    if len(body) > MAX_RESPONSE_BYTES:
        raise ValueError('response budget')
    return body


# `initiative` is deliberately NOT here: it is a regex-bounded slug (plan-review.py INITIATIVE) that the
# anonymizer cannot match anyway (a user joined by hyphens is not a whole word) and it identifies the plan.
# Allow-list of free-text fields that are only DISPLAYED and never travel back to the server.
# Everything else (ids, hashes, versions, runtime/state/disposition/caller_id vocabularies and, above all,
# the user's own comments and drafts: `draft_comments`, `decision.comments[].text`) is left verbatim:
# the user wrote them in this very session and they return in Save/Decide, so anonymizing them would
# corrupt what the panel delivers to the agent.
# `api/cartera` (panel_data.cartera): `slug`, `titulo`, `literal` (estado de spec no reconocido) y `est_texto`
# (coste estimado tal como lo escribe `evaluation.md`) son texto del repo que solo se muestra. Todo lo demas de
# esa respuesta (`id`, `categoria`, `ledger`, `motivo`, `codigo`, `fecha`, `status`, `issues`...) es vocabulario
# cerrado o numeros y queda intacto: un usuario llamado `ilegible` no puede romper los filtros de las paginas.
# `api/plan-<id16>` (panel_data.plan): ademas `fase_nombre` (nombre de la fase del ledger). El estado de la tarea
# va en `estado_tarea` (NO en `estado`, clave mostrada de la memoria): es vocabulario cerrado y queda intacto.
# `api/plan-<id16>-<T-XX>` (panel_data.tarea): ademas `descripcion`, `criterio`, `verificacion`, `ejecutada`, `salida`,
# `cabecera` (de la revision), `gap` y `correccion`. `grado` (Critical/Important/Minor/otro), `num`, `intento`,
# `dependencias`, `enlace` (execution-history.md) y las fechas son vocabulario o forma y quedan intactos.
_DISPLAY_KEYS = frozenset(('titular', 'texto', 'evidencia', 'estado_detalle', 'ruta',
                           'tipo', 'estado', 'area', 'category', 'relation',
                           'response_text', 'note', 'slug', 'titulo', 'literal', 'est_texto', 'fase_nombre',
                           'descripcion', 'criterio', 'verificacion', 'ejecutada', 'salida', 'cabecera', 'gap',
                           'correccion'))
_SECTION_KEYS = frozenset(('title', 'text'))
# Ceilings the browser validators enforce on each displayed field, as (code points, UTF-8 bytes or None):
# `panel-memory.js` (`string(...,160|1000|12000)`) and `panel-review.js` (`noteValid`: 1000/2048 for an
# agent answer, 500/1024 for a verification note). Anonymizing lengthens the text (`<usuario>` is longer than
# a short account name), so the cut happens HERE, after scrubbing, never before.
_CAPS = {'titular': (160, None), 'estado_detalle': (160, None), 'area': (160, None), 'tipo': (160, None),
         'estado': (160, None), 'category': (160, None), 'relation': (160, None),
         'evidencia': (1000, None), 'ruta': (1000, None), 'texto': (12000, None),
         'response_text': (1000, 2048), 'note': (500, 1024),
         'slug': (80, None), 'titulo': (160, None), 'literal': (48, None), 'est_texto': (120, None),
         'fase_nombre': (160, None), 'descripcion': (1500, None), 'criterio': (400, None),
         'verificacion': (2000, None), 'ejecutada': (1000, None), 'salida': (1000, None), 'cabecera': (160, None),
         'gap': (400, None), 'correccion': (400, None)}
# Marcas del anonimizador y del redactor (`redact.REDACTADO`) que un recorte no puede partir.
_MARKS = re.compile(r'<(?:usuario|correo)>|\[secreto redactado\]')


def _clip(text, chars, nbytes=None):
    """Cut `text` to `chars` code points (and `nbytes` UTF-8 bytes) without splitting an anonymizer mark."""
    cut = min(len(text), chars)
    while nbytes is not None and len(text[:cut].encode('utf8')) > nbytes:
        cut -= 1
    if cut >= len(text):
        return text
    for mark in _MARKS.finditer(text):
        if mark.start() < cut < mark.end():
            cut = mark.start()
            break
    return text[:cut]


def _scrubbed(value, scrub, key=None, in_section=False):
    """Apply the panel's single scrubber (redact -> anonymize) to the displayed free text of a JSON
    answer coming from another owner (memory notes; review plan sections and agent answers), then cut it
    to the ceiling of the browser validator."""
    if scrub is None:
        return value
    if isinstance(value, str):
        if key in _DISPLAY_KEYS or (in_section and key in _SECTION_KEYS):
            value = scrub(value)
            if key in _CAPS:
                value = _clip(value, *_CAPS[key])
        return value
    if isinstance(value, list):
        return [_scrubbed(item, scrub, key, in_section) for item in value]
    if isinstance(value, dict):
        return {k: _scrubbed(item, scrub, k, in_section or key == 'sections') for k, item in value.items()}
    return value


def progress_snapshot(project, scrub=None):
    """Bounded public ledger projection, independent of network and live-agent state.

    `scrub` (redact -> anonymize, the same one the builder applies to the inventory) replaces the bare
    redactor, so served titles lose paths, user and e-mails like the exported pages do."""
    result = {'version': 1, 'source': 'canonical_ledger',
              'observed_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
              'status': 'ok', 'complete': True, 'initiatives': [], 'issues': []}

    def issue(status):
        result['complete'] = False
        if len(result['issues']) < 16 and {'status': status} not in result['issues']:
            result['issues'].append({'status': status})

    try:
        reader = _load_shared('local-read.py')
        progress = _load_shared('progress-report.py')
        redactor = _load_shared('redact.py')
    except (OSError, ValueError, ImportError, AttributeError, SyntaxError):
        issue('reader_unavailable'); result['status'] = 'unavailable'
        return result

    def clean(value, limit=160):
        value = (scrub or redactor.redactar)(str(value))
        value = re.sub(r'[\x00-\x1f\x7f-\x9f\u202a-\u202e\u2066-\u2069]', '', value)
        if len(value) > limit:
            issue('text_budget')
        return value[:limit]

    listing = reader.list_names(project, 'docs/roadmap', max_entries=MAX_SCAN)
    if listing['status'] not in ('ok', 'incomplete'):
        issue(listing['status']); result['status'] = 'not_found' if listing['status'] == 'not_found' else 'unavailable'
        return result
    if not listing['complete']:
        issue('incomplete_scan')
    remaining = MAX_READ_BYTES
    for folder in listing['names']:
        if remaining <= 0:
            issue('scan_budget'); break
        directory = reader.list_names(project, 'docs/roadmap/' + folder, max_entries=1)
        if directory['status'] in ('not_found', 'not_regular'):
            continue  # Roadmap indexes are files, not initiative directories.
        if directory['status'] not in ('ok', 'incomplete'):
            issue(directory['status']); continue
        relative = 'docs/roadmap/' + folder + '/tasks.md'
        read = reader.read_text(project, relative, max_bytes=min(MAX_FILE_BYTES, remaining))
        remaining -= read['bytes']
        if read['status'] == 'not_found':
            continue
        if read['status'] != 'ok':
            issue(read['status']); continue
        try:
            summary = progress.resumir(relative, text=read['text'])
            parsed = progress.parse_ledger(read['text'])
        except (ValueError, TypeError, KeyError, OverflowError, RecursionError):
            issue('malformed'); continue
        if len(result['initiatives']) == MAX_INITIATIVES:
            issue('row_budget'); break
        state = summary['estado'] if summary['estado'] in STATES else 'unknown'
        if state == 'unknown':
            issue('unknown_state')
        if any(task.get('estado') not in STATES for task in parsed['tareas']):
            issue('unknown_task_state')
        active = summary['en_progreso']
        if len(active) > 8:
            issue('task_budget')
        phase = summary['fase']
        row = {'id': hashlib.sha256(folder.encode('utf8')).hexdigest()[:16],
               'title': clean(summary['slug']), 'estado': state,
               'total': summary['total'], 'completadas': summary['completadas'], 'pct': summary['pct'],
               'fase': {'indice': phase['indice'], 'total': phase['total'], 'nombre': clean(phase['nombre'])} if phase else None,
               'en_progreso': [{'id': clean(task['id'], 20), 'titulo': clean(task['titulo'])} for task in active[:8]],
               'source_sha256': hashlib.sha256(read['text'].encode('utf8')).hexdigest()}
        result['initiatives'].append(row)
    if not result['complete']:
        result['status'] = 'partial'
    # Retain only a bounded prefix and mark it; counts belong to individual ledgers.
    while len(_encoded(result)) > MAX_RESPONSE_BYTES and result['initiatives']:
        result['initiatives'].pop(); issue('output_budget'); result['status'] = 'partial'
    return result


ACTIVITY_REASONS = frozenset(('disabled', 'invalid_config', 'state_missing',
    'unowned_state', 'invalid_state', 'unsafe_state', 'state_busy',
    'deadline_exceeded', 'state_budget', 'durability_degraded', 'invalid_input',
    'input_budget', 'project_mismatch', 'unsupported_event', 'invalid_identity',
    'role_map_unavailable', 'quota_exceeded', 'revision_exhausted', 'invalid_clock'))


def _unavailable_activity(reason='reader_unavailable', status='unavailable'):
    return {'schema_version': 1, 'status': status, 'reason': reason,
        'complete': False, 'collection_complete': False, 'observations': []}


def activity_snapshot(project):
    """Read the opt-in owner's snapshot, without interpreting absence as coverage."""
    try:
        snapshot = _load_shared('agent-activity-store.py').snapshot(project)
        if (type(snapshot) is not dict or set(snapshot) !=
                {'status', 'reason', 'records', 'collection_complete'}
                or snapshot['collection_complete'] is not False):
            return _unavailable_activity('invalid_snapshot', 'invalid_snapshot')
        if snapshot['status'] == 'unavailable':
            reason = snapshot['reason']
            if type(reason) is not str or reason not in ACTIVITY_REASONS or snapshot['records'] != []:
                return _unavailable_activity('invalid_snapshot', 'invalid_snapshot')
            return _unavailable_activity(reason)
        if snapshot['status'] != 'ok' or snapshot['reason'] is not None:
            return _unavailable_activity('invalid_snapshot', 'invalid_snapshot')
        result = _load_shared('agent-activity.py').project_activity(snapshot['records'], now=time.time())
        return {**result, 'reason': None if result['status'] == 'ok' else 'invalid_snapshot',
            'collection_complete': False}
    except Exception:
        return _unavailable_activity()


class PanelServer(HTTPServer):
    """Serial handlers bound concurrency; a stalled socket expires in three seconds."""
    request_queue_size = 8

    def get_request(self):
        socket, address = super().get_request()
        socket.settimeout(3)
        return socket, address

    def handle_error(self, request, client_address):
        # No request targets, capability or project paths enter access/error logs.
        pass

    def snapshot(self):
        now = time.monotonic()
        if self._snapshot is None or now - self._snapshot_at >= 2:
            try:
                self._snapshot = _encoded(progress_snapshot(self.project, scrub=self.scrub))
            except (OSError, ValueError, TypeError, KeyError, RecursionError):
                self._snapshot = _encoded({'version': 1, 'source': 'canonical_ledger',
                    'observed_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                    'status': 'unavailable', 'complete': False, 'initiatives': [],
                    'issues': [{'status': 'read_failed'}]})
            self._snapshot_at = now
        return self._snapshot

    def cartera(self):
        """Roadmap portfolio for Inicio and Iniciativas: panel_data owns the projection, the single scrubber
        cleans the displayed text after it, and a short cache keeps several tabs from rescanning the roadmap."""
        now = time.monotonic()
        if self._cartera is None or now - self._cartera_at >= 2:
            try:
                body = _encoded(_scrubbed(_load_data().cartera(self.project), self.scrub))
                if len(body) > MAX_RESPONSE_BYTES:
                    raise ValueError('response budget')
            except Exception:
                body = _encoded(_unavailable_cartera())
            self._cartera, self._cartera_at = body, now
        return self._cartera

    def plan(self, ident):
        """`api/plan-<id16>`: kanban de una iniciativa DEL INVENTARIO de planes (no de cualquier id); `None` -> 404.
        `panel_data` proyecta con `ledger-view.py`, el saneador unico limpia el texto mostrado y una cache corta
        evita releer el ledger en cada pestana."""
        if ident not in self.plan_ids:
            return None
        now = time.monotonic()
        hit = self._plans.get(ident)
        if hit is not None and now - hit[0] < 2:
            return hit[1]
        try:
            data = _load_data().plan(self.project, ident)
            body = _plan_body(data, self.scrub) if data is not None else _encoded(_unavailable_plan(ident))
        except Exception:
            body = _encoded(_unavailable_plan(ident))
        if len(self._plans) >= MAX_INITIATIVES:
            self._plans.clear()
        self._plans[ident] = (now, body)
        return body

    def tarea(self, ident, tarea_id):
        """`api/plan-<id16>-<T-XX>`: detalle de una tarea de una iniciativa DEL INVENTARIO de planes; `None` -> 404
        (id fuera del inventario o tarea que el ledger no tiene)."""
        if ident not in self.plan_ids:
            return None
        now = time.monotonic()
        clave = (ident, tarea_id)
        hit = self._plans.get(clave)
        if hit is not None and now - hit[0] < 2:
            return hit[1]
        try:
            data = _load_data().tarea(self.project, ident, tarea_id)
            if data is None:
                return None
            body = _tarea_body(data, self.scrub)
        except Exception:
            body = _encoded(_unavailable_tarea(ident, tarea_id))
        if len(self._plans) >= MAX_INITIATIVES * 4:
            self._plans.clear()
        self._plans[clave] = (now, body)
        return body

    def activity(self):
        try:
            body = _encoded(activity_snapshot(self.project))
            if len(body) > MAX_RESPONSE_BYTES:
                return _encoded(_unavailable_activity('response_budget'))
            return body
        except Exception:
            return _encoded(_unavailable_activity())

    def memory(self, payload):
        try:
            helper = _load_memory()
            if not helper.valid_request(**payload):
                return 400, b'Panel request unavailable.'
            body = _encoded(_scrubbed(helper.query(self.project, **payload), self.scrub))
            if len(body) > MAX_RESPONSE_BYTES:
                raise ValueError('response budget')
            return 200, body
        except Exception:
            return 200, _encoded(_unavailable_memory(payload.get('operation', 'search')))

    @property
    def review_ids(self):
        """Registered review ids (a copy; the registry is the authority)."""
        return set(self.review_registry)

    def owner(self):
        if self.review_owner is None:
            self.review_owner = _load_review()
        return self.review_owner

    def review(self, operation, review_id, payload, deadline):
        """Only the common owner reads or changes durable review state."""
        try:
            if time.monotonic() >= deadline:
                raise TimeoutError
            entry = self.review_registry[review_id]
            helper = self.owner()
            args = {'state_root': self.review_state_root, 'deadline': deadline}
            if operation == 'refresh':
                result = helper.open_review(self.project, entry['initiative'],
                    gate_key=entry['gate_key'], consumer=entry['consumer'], **args)
            elif operation in ('view', 'status'):
                function = helper.get_view if operation == 'view' else helper.get_status
                result = function(self.project, review_id, **args)
            else:
                call_args = (self.project, review_id, payload['version'])
                if operation == 'comments':
                    result = helper.save_comments(*call_args, payload['comments'],
                        expected_revision=payload['expected_revision'], **args)
                else:
                    result = helper.submit_decision(*call_args, payload['choice'], payload['comments'],
                        expected_revision=payload['expected_revision'], **args)
            body = _encoded(_scrubbed(result, self.scrub))
            if time.monotonic() >= deadline:
                raise TimeoutError
            if len(body) > MAX_REVIEW_RESPONSE_BYTES:
                return 413, _encoded(_review_failure('response_budget'))
            if operation == 'refresh':
                self.register_review(result, entry['initiative'], entry['gate_key'], entry['consumer'], entry['escritura'])
            return _review_code(result), body
        except Exception:
            return 503, _encoded(_review_failure())

    def register_review(self, result, initiative, gate_key, consumer=None, escritura=None):
        """Register a review id taken from an OWNER response (never from a request body). An id that is already
        registered keeps its entry; at the cap new ids are left out instead of evicting."""
        review = result.get('review') if type(result) is dict else None
        if not (type(result) is dict and result.get('status') in ('ok', 'waiting') and type(review) is dict
                and type(review.get('review_id')) is str
                and re.fullmatch('[a-f0-9]{64}', review['review_id']) is not None):
            return ''
        rid = review['review_id']
        if rid not in self.review_registry:
            if len(self.review_registry) >= MAX_REVIEW_IDS:
                return ''
            self.review_registry[rid] = {'initiative': initiative, 'gate_key': gate_key, 'consumer': consumer,
                'escritura': gate_key == REVIEW_OPEN_GATE if escritura is None else escritura}
        return rid

    def review_paths(self):
        """`id16 -> initiative path`, refreshed every 5 s (the portfolio cache cadence)."""
        now = time.monotonic()
        if self._review_map is None or now - self._review_map_at >= 5:
            self._review_map, self._review_map_at = review_initiatives(self.project), now
        return self._review_map

    def review_summary(self):
        """`api/review-summary`: the owner's read-only summary keyed by id16 (no paths, no review ids), 5 s cache."""
        now = time.monotonic()
        if self._review_summary is not None and now - self._review_summary_at < 5:
            return self._review_summary
        try:
            paths = self.review_paths()
            ids = {path: ident for ident, path in paths.items()}
            deadline = time.monotonic() + BODY_TIMEOUT
            data = self.owner().summarize_reviews(self.project, list(paths.values()),
                state_root=self.review_state_root, deadline=deadline)
            rows = []
            for row in data.get('initiatives', []):
                ident = ids.get(row.get('initiative'))
                if ident is not None:
                    rows.append({'initiative_id': ident,
                                 **{k: v for k, v in row.items() if k not in ('initiative', 'review_id')}})
            data = {**data, 'initiatives': rows}
            body = _encoded(data)
            while len(body) > MAX_RESPONSE_BYTES and rows:
                rows.pop(); data['omitted'] = data.get('omitted', 0) + 1
                data['status'] = 'partial'; data['complete'] = False
                body = _encoded(data)
        except Exception:
            body = _encoded(_review_summary_failure())
        self._review_summary, self._review_summary_at = body, now
        return body

    def _current_failure(self, ident, reason, estado='no_disponible', **extra):
        return _encoded({'schema_version': 1, 'status': 'unavailable', 'reason': reason, 'initiative_id': ident,
                         'review_id': None, 'estado': estado, 'escritura': False, **extra})

    def review_current(self, ident):
        """`api/review-current/<id16>`: registers the main review id of ONE initiative for the browser. A
        `requested-review` review gets write access; any other gate (`plan-ok` of another process) is read-only."""
        initiative = self.review_paths().get(ident)
        if initiative is None:
            return None
        try:
            data = self.owner().summarize_reviews(self.project, [initiative], state_root=self.review_state_root,
                                                  deadline=time.monotonic() + BODY_TIMEOUT)
            row = (data.get('initiatives') or [None])[0]
            if row is None or data.get('status') not in ('ok', 'partial'):
                return self._current_failure(ident, data.get('reason') or 'reader_unavailable')
            rid, entry = row.get('review_id'), None
            if type(rid) is str:
                self.register_review({'status': 'ok', 'review': {'review_id': rid}}, initiative, row['gate_key'])
                entry = self.review_registry.get(rid)
                if entry is None:
                    return self._current_failure(ident, 'too_many_reviews', row['estado'], message=TOO_MANY_REVIEWS)
            return _encoded({'schema_version': 1, 'status': 'ok', 'reason': None, 'initiative_id': ident,
                'review_id': rid, 'estado': row['estado'], 'version_ordinal': row['version_ordinal'],
                'gate_key': row['gate_key'], 'escritura': bool(entry and entry['escritura'])})
        except Exception:
            return self._current_failure(ident, 'reader_unavailable')

    def review_open(self, ident, deadline):
        """`POST api/review-open/<id16>` (the id is already known to be in the map): opens with the literal gate."""
        initiative = self.review_paths()[ident]
        full = {'schema_version': 1, 'status': 'unavailable', 'reason': 'too_many_reviews',
                'message': TOO_MANY_REVIEWS, 'initiative_id': ident, 'review_id': None}
        if len(self.review_registry) >= MAX_REVIEW_IDS and all(e['initiative'] != initiative for e in self.review_registry.values()):
            return 429, _encoded(full)
        try:
            if time.monotonic() >= deadline:
                raise TimeoutError
            result = self.owner().open_review(self.project, initiative, state_root=self.review_state_root,
                gate_key=REVIEW_OPEN_GATE, consumer=None, deadline=deadline)
            if time.monotonic() >= deadline:
                raise TimeoutError
            rid = self.register_review(result, initiative, REVIEW_OPEN_GATE, None, True)
            self._review_summary = None
            if not rid and result.get('status') in ('ok', 'waiting'):
                return 429, _encoded(full)
            reason = result.get('reason')
            return _review_code(result), _encoded({'schema_version': 1, 'status': result.get('status'),
                'reason': reason if type(reason) is str else None, 'initiative_id': ident,
                'review_id': rid or None, 'escritura': bool(rid)})
        except Exception:
            return 503, _encoded(_review_failure())


class PanelHandler(BaseHTTPRequestHandler):
    server_version = 'CustomAgentsPanel'
    sys_version = ''

    def log_message(self, format, *args):
        pass

    def _reply(self, code, body=b'Panel request unavailable.', content_type='text/plain; charset=utf-8'):
        self.send_response(code)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Content-Security-Policy', self.server.csp)
        self.send_header('Connection', 'close')
        self.end_headers(); self.close_connection = True
        if self.command != 'HEAD':
            self.wfile.write(body)

    def send_error(self, code, message=None, explain=None):
        self._reply(code)

    def _allowed(self, *, body=False):
        origin = f'http://127.0.0.1:{self.server.server_port}'
        if self.headers.get_all('Host') != [origin.removeprefix('http://')]:
            self._reply(403); return False
        supplied = self.headers.get_all('Origin')
        if supplied is not None and supplied != [origin]:
            self._reply(403); return False
        sites = self.headers.get_all('Sec-Fetch-Site')
        if sites is not None and (len(sites) != 1 or sites[0] not in ('same-origin', 'none')):
            self._reply(403); return False
        if self.headers.get_all('Transfer-Encoding') is not None:
            self._reply(400); return False
        lengths = self.headers.get_all('Content-Length')
        if not body and lengths is not None and lengths != ['0']:
            self._reply(400); return False
        return True

    def _route(self):
        if not self.path.startswith('/') or any(c in self.path for c in ('?', '%', '\\', '#')):
            return None
        parts = self.path.split('/')
        if (len(parts) < 3 or re.fullmatch(r'[A-Za-z0-9_-]{43}', parts[1]) is None
                or not hmac.compare_digest(parts[1], self.server.capability)):
            return None
        return '/'.join(parts[2:])

    def _review_route(self, route, operations, *, write=False):
        if not route or not self.server.review_enabled:
            return None
        match = re.fullmatch(r'api/review/([a-f0-9]{64})/([a-z]+)', route)
        entry = self.server.review_registry.get(match[1]) if match else None
        if entry is not None and match[2] in operations and (entry['escritura'] or not write):
            return match[1], match[2]  # a read-only review (`plan-ok` of another process) has no write route
        return None

    def do_GET(self):
        deadline = time.monotonic() + BODY_TIMEOUT
        if not self._allowed():return
        route = self._route()
        if route == '':
            route = 'index.html'
        if route is None:
            self._reply(404)
        elif route in self.server.pages or (PLAN_PAGE.fullmatch(route) and route in self.server.plan_pages):
            self._reply(200, self.server.pages.get(route) or self.server.plan_pages[route], 'text/html; charset=utf-8')
        elif route in self.server.assets:
            self._reply(200, self.server.assets[route][0], self.server.assets[route][1])
        elif route == 'api/progress':
            self._reply(200, self.server.snapshot(), 'application/json; charset=utf-8')
        elif route == 'api/cartera':
            self._reply(200, self.server.cartera(), 'application/json; charset=utf-8')
        elif (plan := PLAN_API.fullmatch(route)) is not None or (tarea := TAREA_API.fullmatch(route)) is not None:
            body = self.server.plan(plan[1]) if plan is not None else self.server.tarea(tarea[1], tarea[2])
            if body is None:
                self._reply(404)
            else:
                self._reply(200, body, 'application/json; charset=utf-8')
        elif route == 'api/activity':
            self._reply(200, self.server.activity(), 'application/json; charset=utf-8')
        elif self.server.review_scope is not None and route == 'api/review-summary':
            self._reply(200, self.server.review_summary(), 'application/json; charset=utf-8')
        elif self.server.review_scope is not None and (current := REVIEW_CURRENT_API.fullmatch(route)) is not None:
            body = self.server.review_current(current[1])
            if body is None:
                self._reply(404)
            else:
                self._reply(200, body, 'application/json; charset=utf-8')
        elif (review := self._review_route(route, ('view', 'status'))) is not None:
            code, body = self.server.review(review[1], review[0], None, deadline)
            self._reply(code, body, 'application/json; charset=utf-8')
        else:
            self._reply(404)

    do_HEAD = do_GET

    def do_POST(self):
        deadline = time.monotonic() + BODY_TIMEOUT
        if not self._allowed(body=True): return
        route = self._route()
        if route is None:
            self._reply(404); return
        review = self._review_route(route, ('comments', 'submit', 'refresh'), write=True)
        opening = REVIEW_OPEN_API.fullmatch(route) if self.server.review_scope is not None else None
        if opening is not None and opening[1] not in self.server.review_paths():
            self._reply(404); return  # unknown initiative: before the body and before loading the owner
        if route != 'api/memory' and review is None and opening is None:
            self._reply(405); return
        lengths = self.headers.get_all('Content-Length')
        if lengths is None or len(lengths) != 1 or re.fullmatch(r'[0-9]{1,8}', lengths[0]) is None:
            self._reply(400); return
        size = int(lengths[0])
        if size > (MAX_REVIEW_REQUEST_BYTES if review or opening else MAX_REQUEST_BYTES):
            self._reply(413); return
        if size == 0:
            self._reply(400); return
        types = self.headers.get_all('Content-Type')
        if types is None or len(types) != 1 or re.fullmatch(r'application/json(?:\s*;\s*charset=utf-8)?', types[0], re.I) is None:
            self._reply(415); return
        chunks = []; remaining = size
        try:
            while remaining:
                timeout = deadline - time.monotonic()
                if timeout <= 0: raise TimeoutError
                self.connection.settimeout(timeout)
                chunk = self.rfile.read1(remaining)
                if not chunk: raise ValueError('incomplete body')
                chunks.append(chunk); remaining -= len(chunk)
            if time.monotonic() > deadline: raise TimeoutError
            def unique(pairs):
                value = {}
                for key, item in pairs:
                    if key in value: raise ValueError('duplicate field')
                    value[key] = item
                return value
            def constant(value): raise ValueError('nonfinite number')
            payload = json.loads(b''.join(chunks).decode('utf8'), object_pairs_hook=unique, parse_constant=constant)
        except (OSError, ValueError, RecursionError):
            self._reply(400); return
        if opening is not None:
            if type(payload) is not dict or set(payload) != {'initiative_id'} or payload['initiative_id'] != opening[1]:
                self._reply(400); return
            code, body = self.server.review_open(opening[1], deadline)
            self._reply(code, body, 'application/json; charset=utf-8'); return
        if review is not None:
            error = _review_payload_error(review[1], payload, review[0])
            if error is not None:
                self._reply(error); return
            code, body = self.server.review(review[1], review[0], payload, deadline)
            self._reply(code, body, 'application/json; charset=utf-8'); return
        if type(payload) is not dict or set(payload) - {'operation', 'text', 'id', 'area', 'tipo', 'limit'}:
            self._reply(400); return
        code, body = self.server.memory(payload)
        self._reply(code, body, 'application/json; charset=utf-8' if code == 200 else 'text/plain; charset=utf-8')

    def _reject_method(self):
        self._reply(405)

    do_PUT = _reject_method
    do_DELETE = _reject_method
    do_PATCH = _reject_method
    do_OPTIONS = _reject_method


def plan_inventory(project, scrub=None):
    """Iniciativas con plan, `[{'id', 'slug', 'titulo'}]` ya saneadas con el saneador unico: de ellas salen las
    paginas `plan-<id16>.html`, el indice de `plan.html` y los ids que acepta `api/plan-<id16>`. Sin roadmap
    legible, lista vacia (la pagina Plan lo dice; nunca se inventa un plan)."""
    try:
        cartera = _scrubbed(_load_data().cartera(project), scrub)
    except Exception:
        return []
    return [{'id': fila['id'], 'slug': fila['slug'], 'titulo': fila['titulo']}
            for fila in cartera.get('iniciativas', []) if fila.get('tiene_plan')]


def create_server(project, inventory, *, port=0, review_selection=None, review_scope=None, scrub=None):
    """Return an owned stoppable HTTPServer; start only at the caller's request."""
    if type(port) is not int or not 0 <= port <= 65535:
        raise ValueError('invalid panel port')
    if review_selection is not None and (type(review_selection) is not dict
            or set(review_selection) - {'initiative', 'state_root', 'gate_key', 'consumer'}
            or not {'initiative', 'state_root'} <= set(review_selection)):
        raise ValueError('invalid review selection')
    if review_scope is not None and (type(review_scope) is not dict or set(review_scope) != {'state_root'}
            or (review_selection is not None and str(review_selection['state_root']) != str(review_scope['state_root']))):
        raise ValueError('invalid review scope')
    builder = _load_builder()
    pages = builder._load_pages()
    # Allowlisted assets: read once here; the disk is never touched per request.
    files, chart_ok, warnings = pages.cargar_assets('servido', review=review_selection is not None or review_scope is not None)
    nonce = secrets.token_urlsafe(24)
    server = PanelServer(('127.0.0.1', port), PanelHandler)
    try:
        server.project = project
        server.scrub = scrub
        server.review_selection = dict(review_selection) if review_selection is not None else None
        server.review_scope = dict(review_scope) if review_scope is not None else None
        server.review_enabled = review_selection is not None or review_scope is not None
        server.review_state_root = (review_selection or review_scope or {}).get('state_root')
        server.review_registry = {}; server.review_owner = None
        server._review_map = None; server._review_map_at = 0
        server._review_summary = None; server._review_summary_at = 0
        review_id = ''
        if review_selection is not None:
            try:
                server.review_owner = _load_review()
                deadline = time.monotonic() + BODY_TIMEOUT
                opened = server.review_owner.open_review(project, review_selection['initiative'],
                    state_root=review_selection['state_root'], gate_key=review_selection.get('gate_key', 'requested-review'),
                    consumer=review_selection.get('consumer'), deadline=deadline)
                if time.monotonic() < deadline and len(_encoded(opened)) <= MAX_REVIEW_RESPONSE_BYTES:
                    review_id = server.register_review(opened, review_selection['initiative'],
                        review_selection.get('gate_key', REVIEW_OPEN_GATE), review_selection.get('consumer'), True)
            except Exception:
                pass  # Optional UI remains unavailable; no invented decision.
        server.capability = secrets.token_urlsafe(32)
        server.access_prefix = '/' + server.capability + '/'
        server._snapshot = None; server._snapshot_at = 0
        server._cartera = None; server._cartera_at = 0
        server._plans = {}
        server.csp = pages.CSP_SERVIDO.format(nonce=nonce)
        server.warnings = warnings
        planes = plan_inventory(project, scrub)
        server.plan_ids = {plan['id'] for plan in planes}
        bodies = builder.cuerpos_paginas(inventory, live=True, review_enabled=review_selection is not None,
                                         review_id=review_id, actividad='assets/panel-activity.js' in files,
                                         planes=planes)
        generated = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
        hidden = {name for name in pages.LIVE_ASSET_FILES if 'assets/' + name not in files}  # review not selected or asset missing
        server.pages = {archivo: pages.render_page(slug, modo='servido', generado=generated, chart_ok=chart_ok, nonce=nonce,
                                                   datos=pages.datos_de_pagina(slug, inventory, modo='servido'),
                                                   cuerpo=bodies[slug], scripts_omitidos=hidden).encode('utf8')
                        for slug, archivo, _ in pages.PAGES}
        # plan-<id16>.html: una pagina por iniciativa con plan, del inventario leido al arrancar (su contenido llega
        # por `api/plan-<id16>`, asi que servirlas no toca disco). Sin los JS vivos del indice (progreso, revision).
        server.plan_pages = {f"plan-{plan['id']}.html": pages.render_page(
            'plan', modo='servido', generado=generated, chart_ok=chart_ok, nonce=nonce, plan_id=plan['id'],
            datos=pages.datos_de_pagina('plan', inventory, modo='servido', plan_id=plan['id']),
            scripts_omitidos=hidden,
            cuerpo=builder.cuerpo_plan_iniciativa('activa' if review_scope is not None else 'inactiva')).encode('utf8')
            for plan in planes}
        server.assets = {rel: (content, ASSET_TYPES.get(Path(rel).suffix, 'application/octet-stream'))
                         for rel, content in files.items()}
    except BaseException:
        server.server_close()  # nada a medias: no deja el puerto abierto
        raise
    return server


def run(project, inventory, *, port=0, review_selection=None, review_scope=None, scrub=None):
    server = create_server(project, inventory, port=port, review_selection=review_selection,
                           review_scope=review_scope, scrub=scrub)
    try:
        for warning in server.warnings:
            print('plugin-panel: aviso: ' + warning, file=sys.stderr, flush=True)
        print(json.dumps({'status': 'serving', 'url': f'http://127.0.0.1:{server.server_port}' + server.access_prefix,
                          'catalog': 'startup_snapshot', 'progress': 'canonical_ledger'}), flush=True)
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0
