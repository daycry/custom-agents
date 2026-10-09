"""Explicit loopback transport for the panel; no runtime or memory execution."""
from datetime import datetime, timezone
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, HTTPServer
import importlib.util
import json
from pathlib import Path
import re
import secrets
import time

HERE = Path(__file__).resolve().parent
MAX_SCAN = 128
MAX_FILE_BYTES = 256 * 1024
MAX_READ_BYTES = 1024 * 1024
MAX_INITIATIVES = 64
MAX_RESPONSE_BYTES = 65536
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


def _encoded(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False).encode('utf8')


def progress_snapshot(project):
    """Bounded public ledger projection, independent of network and live-agent state."""
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
        value = redactor.redactar(str(value))
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
                self._snapshot = _encoded(progress_snapshot(self.project))
            except (OSError, ValueError, TypeError, KeyError, RecursionError):
                self._snapshot = _encoded({'version': 1, 'source': 'canonical_ledger',
                    'observed_at': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                    'status': 'unavailable', 'complete': False, 'initiatives': [],
                    'issues': [{'status': 'read_failed'}]})
            self._snapshot_at = now
        return self._snapshot


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

    def _allowed(self):
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
        if lengths is not None and lengths != ['0']:
            self._reply(400); return False
        return True

    def do_GET(self):
        if not self._allowed():return
        if not self.path.startswith('/') or any(c in self.path for c in ('?', '%', '\\', '#')):
            self._reply(404); return
        parts = self.path.split('/')
        if (len(parts) < 3 or re.fullmatch(r'[A-Za-z0-9_-]{43}', parts[1]) is None
                or not hmac.compare_digest(parts[1], self.server.capability)):
            self._reply(404); return
        route = '/'.join(parts[2:])
        if route == '':
            self._reply(200, self.server.page, 'text/html; charset=utf-8')
        elif route == 'api/progress':
            self._reply(200, self.server.snapshot(), 'application/json; charset=utf-8')
        else:
            self._reply(404)

    do_HEAD = do_GET

    def do_POST(self):
        self._reply(405)

    do_PUT = do_POST
    do_DELETE = do_POST
    do_PATCH = do_POST
    do_OPTIONS = do_POST


def create_server(project, inventory, *, port=0):
    """Return an owned stoppable HTTPServer; start only at the caller's request."""
    if type(port) is not int or not 0 <= port <= 65535:
        raise ValueError('invalid panel port')
    builder = _load_builder()
    page = builder.render_html(inventory, live=True)
    nonce = secrets.token_urlsafe(24)
    page = page.replace('<script>', '<script nonce="' + nonce + '">')
    server = PanelServer(('127.0.0.1', port), PanelHandler)
    server.project = project
    server.capability = secrets.token_urlsafe(32)
    server.access_prefix = '/' + server.capability + '/'
    server.page = page.encode('utf8')
    server._snapshot = None; server._snapshot_at = 0
    server.csp = ("default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-" + nonce
                  + "'; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'")
    return server


def run(project, inventory, *, port=0):
    server = create_server(project, inventory, port=port)
    try:
        print(json.dumps({'status': 'serving', 'url': f'http://127.0.0.1:{server.server_port}' + server.access_prefix,
                          'catalog': 'startup_snapshot', 'progress': 'canonical_ledger'}), flush=True)
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0
