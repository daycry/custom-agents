#!/usr/bin/env python3
"""Read public plugin definitions and build a local capability panel."""
import argparse
import html
import hashlib
import getpass
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001

MARKER = '<!doctype html><!-- custom-agents plugin-panel v1 -->'
MAX_BYTES = 512 * 1024
MAX_FILES = 1000


def _load_redactor():
    # Only trusted bundled code; --root is data and cannot select imported code.
    path = Path(__file__).resolve().parents[3] / 'agent-kits/shared/redact.py'
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location('panel_redactor', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    global ANONIMIZAR
    ANONIMIZAR = getattr(module, 'anonimizar', None)
    return module.redactar


ANONIMIZAR = None
REDACTOR = _load_redactor()


# Saneado activo durante `build_inventory(scrub=...)`: redactar -> anonimizar. Sin él, solo se redacta.
_SANEADOR = None

# Claves de VOCABULARIO CERRADO del inventario (ids, enums, rutas relativas del propio bundle, estados,
# conteos): nunca son texto libre del usuario, así que no se anonimizan (un usuario `user`, `project`,
# `agent` o `codex` rompería los filtros y la exportación). Una clave cerrada cubre todo su subárbol.
CLAVES_CERRADAS = frozenset((
    'schema_version', 'version', 'evidence', 'id', 'ids', 'role_ids', 'scope', 'kind', 'runtime', 'root_id',
    'source', 'locator', 'event', 'native_event', 'handler', 'behavior', 'availability', 'ownership',
    'resolution', 'registry_status', 'status', 'load_status', 'execution_status', 'identity_status',
    'timeout', 'timeout_status', 'timeout_unit', 'timeout_provenance', 'transport', 'enabled',
    'hook_sources', 'runtimes', 'memory', 'counts', 'workflow', 'hook_group_count',
    'definition_status', 'partial', 'selection_only'))


# Palabras del vocabulario cerrado que `project-pieces` pasa por su redactor junto al texto libre.
_VOCABULARIO_EXACTO = frozenset(('project', 'user', 'local', 'claude-code', 'codex', 'opencode', 'agent', 'skill',
                                 'command', 'persona', 'tool-source', 'mcp'))


def _sanear(texto):
    return (_SANEADOR or REDACTOR)(texto)


def _sanear_extension(texto):
    """Redactor que `project-pieces` aplica a TODO campo de texto, también a `scope`/`kind`/`runtime`: el
    vocabulario cerrado exacto solo se redacta; el resto, texto libre, se anonimiza antes de recortar."""
    return REDACTOR(texto) if texto in _VOCABULARIO_EXACTO else _sanear(texto)


def _redact_values(value, cerrado=False):
    """Texto libre -> `_sanear` (redactar y, si hay saneador, anonimizar); vocabulario cerrado -> solo redactar."""
    if isinstance(value, str):
        return REDACTOR(value) if cerrado else _sanear(value)
    if isinstance(value, list):
        return [_redact_values(item, cerrado) for item in value]
    if isinstance(value, dict):
        return {key: _redact_values(item, cerrado or key in CLAVES_CERRADAS) for key, item in value.items()}
    return value


# --8<-- cloud path guard SHARED
def _linked(path):
    try:
        info = path.lstat()
        if path.is_symlink():
            return True
        if not getattr(info, 'st_file_attributes', 0) & 0x400:
            return False
        # Windows CLOUD variants describe sync placeholders, not path redirects.
        # Unknown reparse tags stay excluded, including junctions and symlinks.
        tag = getattr(info, 'st_reparse_tag', 0)
        return (tag & 0xFFFF0FFF) != 0x9000001A
    except FileNotFoundError:
        return False
# --8<-- end cloud path guard SHARED

_unsafe_link = _linked


def _guard_path(root, path):
    current = root
    for part in path.relative_to(root).parts:
        current = current / part
        if _unsafe_link(current):
            raise ValueError('symbolic link')


def _read(root, path):
    _guard_path(root, path)
    with path.open('rb') as handle:
        data = handle.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError('file too large')
    return data.decode('utf-8-sig')


def _metadata(text):
    lines = text.splitlines()
    if not lines or lines[0] != '---':
        raise ValueError('missing frontmatter')
    end = next((i for i, line in enumerate(lines[1:], 1) if line == '---'), None)
    if end is None:
        raise ValueError('unclosed frontmatter')
    fields, key = {}, None
    for line in lines[1:end]:
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        match = re.match(r'^(name|description|model|tools):\s*(.*)$', line)
        if match:
            key, value = match.groups()
            fields[key] = '' if value in ('>', '|', '>-', '|-') else value.strip('"\'')
        elif line.startswith((' ', '\t')) and key == 'description':
            fields[key] = (fields[key] + ' ' + line.strip()).strip()
        elif line.lstrip().startswith('- ') and key == 'tools':
            fields[key] = (fields[key] + ' ' + line.strip()[2:]).strip()
        else:
            key = None
    return fields


def _paths(root, folder, warnings):
    directory = root / folder
    if _unsafe_link(directory):
        warnings.append(f'{folder}: linked directory excluded')
        return []
    if not directory.is_dir():
        return []
    if folder == 'skills':
        result = []
        for path in directory.iterdir():
            if _unsafe_link(path):
                warnings.append(f'skills/{path.name}: linked directory excluded')
            elif path.is_dir() and (path / 'SKILL.md').exists():
                result.append(path / 'SKILL.md')
        return sorted(result)
    return sorted(directory.glob('*.md'))


def _catalog(root, kind, warnings):
    entries, paths = [], _paths(root, kind, warnings)
    if len(paths) > MAX_FILES:
        warnings.append(f'{kind}: inventory limited to {MAX_FILES} files')
    for path in paths[:MAX_FILES]:
        relative = path.relative_to(root).as_posix()
        try:
            metadata = _redact_values(_metadata(_read(root, path)))
            tools = sorted(set(re.findall(r'\b[A-Z][A-Za-z]+\b', metadata.get('tools', ''))))
            entries.append({'name': metadata.get('name', path.parent.name if kind == 'skills' else path.stem), 'description': metadata.get('description', '')[:480], 'model': metadata.get('model', ''), 'tools': tools, 'source': relative})
        except (OSError, UnicodeError, ValueError):
            warnings.append(f'{relative}: metadata unavailable')
    return entries


HOOK_HANDLERS = frozenset(('native-guardrail', 'mark-docs-pending.sh', 'ledger-lint-warn.sh',
                         'progress-line.sh', 'subagent-progress.sh', 'session-context.sh',
                         'session-journal.sh', 'user-prompt-capture.sh', 'agent-activity'))
RUNTIME_NAMES = {'claude-code': 'claude', 'codex': 'codex', 'opencode': 'opencode'}
HOOK_SOURCES = {'claude-code': 'hooks/hooks.json', 'codex': 'interop/codex/hooks.json',
                'opencode': 'hooks/opencode-plugin.js'}
CATALOG_START = '// custom-agents hook-catalog:start'
CATALOG_END = '// custom-agents hook-catalog:end'


def _hook_metadata(root, hook, group, metadata, runtime):
    launcher = '${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.mjs'
    script = None
    arguments = hook.get('args')
    suffix = None
    if hook.get('command') == 'node' and isinstance(arguments, list) and len(arguments) in (2, 3) and arguments[0] == launcher:
        script = arguments[1]
        suffix = arguments[2] if len(arguments) == 3 else None
    elif isinstance(hook.get('command'), str):
        match = re.fullmatch(r'node "\$\{CLAUDE_PLUGIN_ROOT\}/hooks/run-hook\.mjs" (?:(?:"([a-z][a-z0-9.-]{0,63})")|([a-z][a-z0-9.-]{0,63}))(?: (--runtime=(?:claude|codex|opencode)))?', hook['command'])
        if match:
            script = match.group(1) or match.group(2)
            suffix = match.group(3)
    if script not in HOOK_HANDLERS or (suffix is not None and suffix != '--runtime=' + RUNTIME_NAMES[runtime]):
        return {}
    return _handler_metadata(root, script, group, metadata)


def _handler_metadata(root, script, group, metadata):
    if script not in metadata:
        fields = {'title': script, 'description': 'Descripción pública no disponible en esta instantánea.'}
        if script == 'native-guardrail':
            fields = {'title': 'Guardia de roles',
                      'description': 'Aplica las políticas centrales del implementer y architect cuando coincide su identidad nativa. El nombre no acredita procedencia del prompt ni un sandbox universal.'}
        elif script == 'agent-activity':
            fields = {'title': 'Señales recientes de actividad',
                      'description': 'Observaciones de sesión opt-in; no acreditan liveness ni teardown.'}
        else:
            try:
                for line in _read(root, root / 'hooks' / script).splitlines()[:8]:
                    for key in ('title', 'description'):
                        prefix = '# panel-' + key + ': '
                        if line.startswith(prefix):
                            fields[key] = _sanear(line[len(prefix):])[:300]
            except (OSError, ValueError, UnicodeError):
                pass
        metadata[script] = fields
    matcher = group.get('matcher')
    return {'handler': script, **metadata[script],
            'matcher': _sanear(matcher)[:160] if isinstance(matcher, str) else ''}


def _positive_number(value):
    try:
        return type(value) in (int, float) and math.isfinite(value) and value > 0
    except OverflowError:
        return False


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def _role_ids(root, runtime, warnings):
    source = 'agent-kits/shared/native-roles.json'
    try:
        text = _read(root, root / source)
        if len(text.encode('utf-8')) > 65536:
            raise ValueError('role map too large')
        mapping = json.loads(text, object_pairs_hook=_unique_object)
        roles = mapping['runtimes'][RUNTIME_NAMES[runtime]]
        prefix = 'custom-agents:' if runtime == 'claude-code' else 'custom-agents-'
        result = [roles[role] for role in ('implementer', 'architect')]
        if type(mapping.get('schema_version')) is not int or mapping['schema_version'] != 1 or result != [prefix + role for role in ('implementer', 'architect')]:
            raise ValueError('invalid native identities')
        return result
    except (OSError, ValueError, UnicodeError, TypeError, KeyError, RecursionError):
        warnings.append(f'{runtime}: native role identity metadata unavailable')
        return []


def _hook_record(runtime, event, native_event, source, locator, timeout, provenance, meta, roles, warnings):
    valid = _positive_number(timeout)
    status = 'declared' if valid else 'absent' if timeout is None else 'invalid'
    if status == 'invalid':
        warnings.append(f'{runtime}: invalid declared hook timeout')
    guard = meta.get('handler') == 'native-guardrail'
    return {'id': 'hook-' + hashlib.sha256(f'{runtime}:{source}:{locator}'.encode('utf-8')).hexdigest()[:16],
            'runtime': runtime, 'event': event, 'native_event': native_event, 'source': source,
            'locator': locator, 'scope': 'global', 'behavior': 'guard' if guard else 'informative' if 'handler' in meta else 'unknown',
            'timeout': timeout if valid else None, 'timeout_status': status,
            'timeout_unit': 'ms' if provenance == 'adapter-supervision' else 's',
            'timeout_provenance': provenance, 'load_status': 'unknown', 'execution_status': 'unknown',
            'role_ids': roles if guard else [], 'identity_status': 'declared' if guard and roles else 'unknown', **meta}


def _opencode_bindings(text):
    if text.count(CATALOG_START) != 1 or text.count(CATALOG_END) != 1:
        raise ValueError('missing or duplicate catalog markers')
    literal = text.split(CATALOG_START, 1)[1].split(CATALOG_END, 1)[0].strip()
    before, after = 'const hookCatalog = JSON.parse(`', '`);'
    if not literal.startswith(before) or not literal.endswith(after) or len(literal.encode('utf-8')) > 65536:
        raise ValueError('invalid catalog literal')
    payload = literal[len(before):-len(after)]
    # No JavaScript interpolation or extra statements can be interpreted as data.
    if '`' in payload or '${' in payload:
        raise ValueError('executable catalog interpolation')
    catalog = json.loads(payload, object_pairs_hook=_unique_object)
    if type(catalog.get('schema_version')) is not int or catalog['schema_version'] != 1:
        raise ValueError('invalid catalog version')
    bindings = catalog.get('bindings')
    expected = {'guard': ('tool', 'PreToolUse', 'guard'), 'prompt': ('session', 'UserPromptSubmit', 'informative'),
                'context': ('session', 'SessionStart', 'informative'), 'post': ('tool', 'PostToolUse', 'informative'),
                'capture': ('event', 'SessionEnd', 'informative'),
                'activity': ('event', 'ActivityObserved', 'informative')}
    allowed_handlers = {'guard': {'native-guardrail'}, 'prompt': {'user-prompt-capture.sh'},
                        'context': {'session-context.sh'}, 'capture': {'session-journal.sh'},
                        'activity': {'agent-activity'},
                        'post': {'mark-docs-pending.sh', 'ledger-lint-warn.sh', 'progress-line.sh'}}
    if not isinstance(bindings, list) or len(bindings) != len(expected):
        raise ValueError('invalid binding list')
    found = set()
    for binding in bindings:
        identifier = binding['id']
        if identifier in found or identifier not in expected:
            raise ValueError('invalid binding ID')
        found.add(identifier)
        if tuple(binding.get(key) for key in ('domain', 'event', 'behavior')) != expected[identifier]:
            raise ValueError('invalid callback binding')
        handlers = binding.get('handlers')
        if not isinstance(handlers, list) or not 1 <= len(handlers) <= 8 or any(type(item) is not str or item not in HOOK_HANDLERS for item in handlers) or len(set(handlers)) != len(handlers):
            raise ValueError('invalid binding handlers')
        if set(handlers) != allowed_handlers[identifier]:
            raise ValueError('invalid callback handler')
        if not _positive_number(binding.get('timeout_ms')):
            raise ValueError('invalid adapter budget')
        stream = identifier in ('capture', 'activity')
        names = binding.get('native_events') if stream else [binding.get('native_event')]
        if not isinstance(names, list) or not 1 <= len(names) <= 16 or any(type(name) is not str or not re.fullmatch(r'[a-z][a-z0-9.-]{0,99}', name) for name in names):
            raise ValueError('invalid native events')
        if type(binding.get('activation')) is not str or len(binding['activation']) > 300:
            raise ValueError('invalid activation')
        if stream:
            expected_events = ['session.execution.succeeded', 'session.execution.failed',
                               'session.execution.interrupted', 'session.idle']
            if identifier == 'activity':
                expected_events.insert(0, 'session.execution.started')
            if names != expected_events:
                raise ValueError('invalid execution/idle stream binding')
            if binding.get('idle_status_event') != 'session.status' or binding.get('idle_status') != 'idle':
                raise ValueError('invalid idle binding')
        if identifier == 'activity' and binding['timeout_ms'] != 2500:
            raise ValueError('invalid activity supervision budget')
        if identifier == 'post' and (not isinstance(binding.get('tools'), list) or not 1 <= len(binding['tools']) <= 32 or any(type(tool) is not str or not re.fullmatch(r'[a-z][a-z0-9_]{0,63}', tool) for tool in binding['tools'])):
            raise ValueError('invalid tool activation')
    return bindings


def _hooks(root, runtime, warnings):
    source = HOOK_SOURCES[runtime]
    path = root / source
    if not path.exists():
        warnings.append(f'{source}: declaration source missing; hooks unknown')
        return [], {'source': source, 'status': 'missing'}
    try:
        text = _read(root, path)
        result, metadata = [], {}
        roles = None
        if runtime == 'opencode':
            for binding in _opencode_bindings(text):
                native_event = (', '.join(binding['native_events']) + ', ' + binding['idle_status_event'] + ' (' + binding['idle_status'] + ')') if binding['domain'] == 'event' else binding['domain'] + '.' + binding['native_event']
                for index, handler in enumerate(binding['handlers']):
                    meta = _handler_metadata(root, handler, {'matcher': binding['activation']}, metadata)
                    if handler == 'native-guardrail' and roles is None:
                        roles = _role_ids(root, runtime, warnings)
                    result.append(_hook_record(runtime, binding['event'], native_event, source,
                                  'hook-catalog/bindings/' + binding['id'] + '/handlers/' + str(index),
                                  binding['timeout_ms'], 'adapter-supervision', meta, roles or [], warnings))
            return result, {'source': source, 'status': 'declared'}
        events = json.loads(text, object_pairs_hook=_unique_object).get('hooks', {})
        if not isinstance(events, dict):
            raise ValueError('invalid events')
        if len(events) > 64:
            raise ValueError('too many events')
        for event in sorted(events):
            groups = events[event]
            if not isinstance(event, str) or len(event) > 128 or not isinstance(groups, list) or len(groups) > 64:
                raise ValueError('invalid event groups')
            for group_index, group in enumerate(groups):
                if not isinstance(group, dict) or not isinstance(group.get('hooks'), list):
                    raise ValueError('invalid hook group')
                for index, hook in enumerate(group['hooks']):
                    if not isinstance(hook, dict) or len(result) >= MAX_FILES:
                        raise ValueError('invalid or oversized hook inventory')
                    meta = _hook_metadata(root, hook, group, metadata, runtime)
                    if meta.get('handler') == 'native-guardrail' and roles is None:
                        roles = _role_ids(root, runtime, warnings)
                    result.append(_hook_record(runtime, event, event, source,
                                  'hooks/' + event + '/' + str(group_index) + '/' + str(index),
                                  hook.get('timeout'), 'runtime-registration', meta, roles or [], warnings))
        return result, {'source': source, 'status': 'declared'}
    except (OSError, UnicodeError, ValueError, TypeError, AttributeError, KeyError, RecursionError):
        warnings.append(f'{source}: declaration inventory unavailable; hooks unknown')
        return [], {'source': source, 'status': 'invalid'}


def _presence(root, relative):
    path = root / relative
    try:
        _guard_path(root, path)
        return 'present' if path.exists() else 'absent'
    except (OSError, ValueError):
        return 'unavailable'


def _load_pieces():
    path = Path(__file__).resolve().parents[3] / 'agent-kits/shared/project-pieces.py'
    spec = importlib.util.spec_from_file_location('panel_project_pieces', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_shared(filename):
    path = Path(__file__).resolve().parents[3] / 'agent-kits/shared' / filename
    spec = importlib.util.spec_from_file_location('panel_' + filename.replace('-', '_'), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _diagnostics(path, project):
    if path is None:
        return {'status': 'not_provided'}
    try:
        contract = _load_shared('diagnostic-report.py')
        reader = _load_shared('local-read.py')
    except (OSError, ValueError, ImportError, AttributeError, SyntaxError):
        return {'status': 'reader_unavailable'}
    target = Path(os.path.abspath(path))
    result = reader.read_text(target.parent, target.name, max_bytes=contract.MAX_BYTES)
    if result['status'] != 'ok':
        return {'status': result['status']}
    try:
        report = json.loads(result['text'], object_pairs_hook=_unique_object,
                            parse_constant=lambda value: (_ for _ in ()).throw(ValueError('constant')))
        projection = contract.consume(report, project=project)
    except (ValueError, TypeError, RecursionError):
        return {'status': 'incompatible'}
    projection['source_sha256'] = hashlib.sha256(result['text'].encode('utf-8')).hexdigest()
    projection['digest_method'] = 'decoded-utf8-text'
    return projection


def _extensions(project, home, runtime, cwd, include_user, user_roots):
    redactor_previo = None
    try:
        module = _load_pieces()
        roots = module.parse_user_roots(user_roots or [])
        # Los textos de las extensiones se recortan dentro de `discover`: el saneador completo entra por el
        # mismo punto que su redactor, así que anonimiza antes de recortar.
        redactor_previo, module.REDACT = module.REDACT, _sanear_extension
        return module.discover(project, home=home, runtime=runtime, cwd=cwd,
                               include_user=include_user, user_roots=roots)
    except (OSError, ValueError, UnicodeError, RecursionError, ImportError, AttributeError, SyntaxError):
        return {'version': 1, 'pieces': [], 'conflicts': [], 'orphans': [],
                'registry_status': 'unknown', 'partial': True,
                'evidence': 'local declarations; session availability not measured',
                'warnings': ['Extension declarations unavailable; check project roots and bundled reader.']}
    finally:
        if redactor_previo is not None:
            module.REDACT = redactor_previo


def build_inventory(root, *, project=None, home=None, runtime='all', cwd=None,
                    include_user=True, user_roots=None, diagnostics_report=None, scrub=None):
    """Inventario redactado. Con `scrub` (redactar -> anonimizar, ver `_scrubber`) TODO el texto libre se
    anonimiza en origen, ANTES de recortar (orden de `redact.py`): exportado y servido comparten este punto."""
    global _SANEADOR
    anterior, _SANEADOR = _SANEADOR, scrub
    try:
        return _build_inventory(root, project=project, home=home, runtime=runtime, cwd=cwd,
                                include_user=include_user, user_roots=user_roots,
                                diagnostics_report=diagnostics_report)
    finally:
        _SANEADOR = anterior


def _build_inventory(root, *, project, home, runtime, cwd, include_user, user_roots, diagnostics_report):
    if REDACTOR is None:
        raise ValueError('bundled redactor unavailable')
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError('bundle root unavailable')
    data = {'schema_version': 1, 'evidence': 'file_inventory; runtime execution not measured', 'warnings': []}
    for kind in ('agents', 'skills', 'commands'):
        data[kind] = _catalog(root, kind, data['warnings'])
    data['tools'] = sorted({tool for entry in data['agents'] for tool in entry['tools']})
    selected = tuple(RUNTIME_NAMES) if runtime == 'all' else (runtime,)
    data['hooks'], data['hook_sources'] = [], {}
    for selected_runtime in selected:
        records, status = _hooks(root, selected_runtime, data['warnings'])
        data['hooks'].extend(records)
        data['hook_sources'][selected_runtime] = status
    data['hook_group_count'] = len({(hook['runtime'], hook['event']) for hook in data['hooks']})
    data['counts'] = {kind: len(data[kind]) for kind in ('agents', 'skills', 'commands', 'tools', 'hooks')}
    data['runtimes'] = {runtime: _presence(root, relative) for runtime, relative in {'claude': 'hooks/hooks.json', 'codex': 'interop/codex/hooks.json', 'opencode': 'interop/opencode/plugins/custom-agents/index.js'}.items()}
    data['memory'] = {'approved_directory': _presence(root, 'docs/knowledge/approved'), 'graphify_artifact': _presence(root, 'graphify-out/graph.json')}
    data['workflow'] = _workflow(root, data['warnings'])
    data['diagnostics'] = _diagnostics(diagnostics_report, project)
    if data['diagnostics']['status'] not in ('not_provided', 'accepted'):
        data['warnings'].append('Diagnostic snapshot: ' + data['diagnostics']['status'])
    if project is not None:
        data['extensions'] = _extensions(project, home, runtime, cwd, include_user, user_roots)
    return _redact_values(data)


DIAGNOSTIC_BLOCKS = {'herramientas': 'Herramientas', 'plugin': 'Plugin', 'configs': 'Configuración',
                     'estado': 'Estado del trabajo', 'capacidades': 'Capacidades opcionales',
                     'memoria': 'Memoria técnica', 'journal': 'Journal', 'version': 'Versión'}
DIAGNOSTIC_STATES = {'ok': 'Correcto en la comprobación', 'aviso': 'Advertencia',
                     'error': 'Error', 'info': 'Informativo'}


def _diagnostics_html(result):
    esc = html.escape
    intro = ('<section id="diagnostics"><div class="section-head"><div><h2>Instantánea de doctor</h2>'
             '<p>Instantánea importada de doctor; no acredita carga ni ejecución de hooks.</p></div>'
             '<span class="section-pill">Consulta explícita</span></div>')
    messages = {'not_provided': 'Sin diagnóstico importado. Obtén una proyección con doctor --panel-json y selecciónala al generar el panel.',
                'scope_unbound': 'Falta un proyecto explícito para ligar el diagnóstico.',
                'scope_mismatch': 'El diagnóstico pertenece a otra ruta de proyecto; no se adopta.',
                'future_timestamp': 'La fecha del diagnóstico está en el futuro; revisa el reloj y vuelve a comprobar.',
                'incompatible': 'El informe no cumple el contrato portable de doctor.',
                'reader_unavailable': 'Falta el lector o el contrato del informe.',
                'not_found': 'El fichero indicado no existe.',
                'too_large': 'El informe supera el límite de lectura de 64 KiB.',
                'invalid_encoding': 'El informe no tiene codificación UTF-8 válida.'}
    if 'report' not in result:
        return intro + '<p class="diagnostic-notice" role="status">' + esc(messages.get(result['status'], 'No se pudo leer el informe indicado.')) + '</p><p>Los datos del catálogo permanecen independientes. Consulta /doctor para obtener el detalle y el arreglo sugerido.</p></section>'
    report = result['report']
    old = result.get('age_status') == 'old_snapshot'
    notice = ('Instantánea anterior a 24 horas: vuelve a comprobar el estado.' if old else
              'Instantánea histórica: una fecha reciente tampoco prueba el estado actual.')
    if not report['complete']:
        notice += ' Informe recortado: recuentos parciales y prioridades omitidas.'
    body = '<p class="diagnostic-notice" role="status">' + esc(notice) + '</p>'
    body += '<p class="diagnostic-provenance">Productor declarado: doctor · Fecha UTC: <time>' + esc(report['checked_at']) + '</time> · Alcance: coincide con la ruta del proyecto indicado.</p>'
    body += '<details class="diagnostic-source"><summary>Identidad del contenido importado</summary><code>SHA-256 (texto UTF-8 decodificado): ' + esc(result['source_sha256']) + '</code><p>El hash identifica contenido; no autentica su productor ni certifica que siga vigente.</p></details>'
    if report['priorities']:
        body += '<h3>Acciones prioritarias</h3><ol class="diagnostic-priorities">'
        by_id = {block['id']: block for block in report['blocks']}
        for action in report['priorities']:
            key, ordinal = action['block'], action['row']
            row = by_id[key]['rows'][ordinal-1]
            label = row['label'] or 'Comprobación ' + str(ordinal)
            body += '<li><a href="#diagnostic-' + key + '-' + str(ordinal) + '">' + esc(DIAGNOSTIC_BLOCKS[key] + ' · ' + label) + '</a> · ' + esc(DIAGNOSTIC_STATES[row['state']]) + '. Consulta /doctor, bloque ' + esc(DIAGNOSTIC_BLOCKS[key]) + ', fila ' + str(ordinal) + ' para el detalle y arreglo sugerido.</li>'
        body += '</ol>'
    else:
        body += '<p>No hay prioridades exportadas. Esto no certifica salud, readiness ni ausencia de problemas no comprobados.</p>'
    body += '<div class="controls"><div class="search-wrap"><input id="diagnostic-search" type="search" aria-label="Buscar comprobaciones" placeholder="Buscar en el diagnóstico"></div><select id="diagnostic-state" aria-label="Severidad de diagnóstico"><option value="all">Todas las comprobaciones</option><option value="error">Errores</option><option value="aviso">Advertencias</option><option value="info">Informativas</option><option value="ok">Correctas en la comprobación</option></select></div><p id="diagnostic-results" role="status" aria-live="polite"></p>'
    for block in report['blocks']:
        key = block['id']
        body += '<details class="diagnostic-block"><summary>' + esc(DIAGNOSTIC_BLOCKS[key]) + ' · ' + str(len(block['rows'])) + ' comprobaciones</summary><ul>'
        for ordinal, row in enumerate(block['rows'], 1):
            label = row['label'] or 'Comprobación ' + str(ordinal)
            body += '<li class="diagnostic-row" id="diagnostic-' + key + '-' + str(ordinal) + '" data-state="' + row['state'] + '"><strong>' + esc(label) + '</strong><span class="diagnostic-badge">' + esc(DIAGNOSTIC_STATES[row['state']]) + '</span><small>' + esc(DIAGNOSTIC_BLOCKS[key]) + ' · fila ' + str(ordinal) + '</small></li>'
        body += '</ul></details>'
    return intro + body + '<p>Los detalles y arreglos libres permanecen en /doctor. El panel no los ejecuta, no comprueba backends y no recalifica las declaraciones del catálogo.</p></section>'


def _workflow(root, warnings):
    source = 'agent-kits/shared/capability-catalog.json'
    result = {'source': source, 'selection_only': True, 'roles': {}}
    if not (root / source).exists():
        return result
    try:
        # --root chooses inspected data only. Executable validation stays in this bundle.
        path = Path(__file__).resolve().parents[3] / 'agent-kits/shared/capability-route.py'
        spec = importlib.util.spec_from_file_location('panel_capability_route', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        catalog = json.loads(_read(root, root / source))
        if module.validate_catalog(catalog, bundle=root):
            raise ValueError('invalid catalog')
        result['roles'] = {role: sorted(entry['id'] for entry in catalog['capabilities'] if role in entry['roles']) for role in module.ROLES}
    except (OSError, ValueError, UnicodeError, RecursionError):
        warnings.append(f'{source}: routing metadata unavailable')
    return result


def _workflow_html(data):
    roles = data.get('workflow', {}).get('roles', {})
    responsibilities = {entry['name']: entry['description'] for entry in data.get('agents', [])}
    rows = ''.join(
        '<article class="workflow-role" id="role-' + html.escape(role) + '" data-role="' + html.escape(role) + '"><div class="role-heading"><span class="role-avatar" aria-hidden="true">' + html.escape(role[:2].upper()) + '</span><h3>' + html.escape(role) + '</h3></div>'
        + '<details><summary>Responsabilidades y guías</summary><p class="responsibility">Responsabilidad: ' + html.escape(responsibilities.get(role, 'Definición del rol no disponible en esta instantánea')) + '</p>'
        + '<p>Guías seleccionadas:</p><div>' + ''.join('<span class="guide-chip">' + html.escape(guide) + '</span>' for guide in guides) + '</div></details></article>'
        for role, guides in roles.items()
    )
    if not rows:
        rows = '<p>Registro de selección ausente o inválido. El catálogo de archivos sigue disponible.</p>'
    return '<section id="workflow"><div class="section-head"><div><h2>Tu workflow, rol a rol</h2><p>Responsabilidades propias y guías compartidas por el ciclo. Esta selección no acredita ejecución, acceso a herramientas ni permisos.</p></div><span class="section-pill">Una cadena compartida</span></div><div class="workflow-roles">' + rows + '</div></section>'


def _cards(data):
    cards = []
    for kind in ('agents', 'skills', 'commands'):
        for entry in data[kind]:
            esc = lambda value: html.escape(str(value), quote=True)
            detail = esc(entry['model'] or ', '.join(entry['tools']))
            labels = {'agents': 'AGENTE', 'skills': 'SKILL', 'commands': 'COMANDO'}
            teaser = entry['description'][:130].rsplit(' ', 1)[0] if len(entry['description']) > 130 else entry['description']
            cards.append(f'<article data-kind="{kind}" class="card"><small>{labels[kind]} · {detail}</small><h2>{esc(entry["name"])}</h2><p>{esc(teaser)}{"…" if len(teaser) < len(entry["description"]) else ""}</p><details><summary>Ver función y origen</summary><p>{esc(entry["description"])}</p><code>{esc(entry["source"])}</code></details></article>')
    for tool in data['tools']:
        cards.append(f'<article data-kind="tools" class="card"><small>HERRAMIENTA DECLARADA</small><h2>{html.escape(tool)}</h2><p>El acceso depende de las herramientas habilitadas en la sesión y del runtime actual.</p></article>')
    grouped = {}
    for hook in data['hooks']:
        grouped.setdefault((hook.get('runtime', 'unknown'), hook['event']), []).append(hook)
    for (runtime, event), hooks in grouped.items():
        handlers = ''.join(
            '<li id="' + html.escape(hook.get('id', 'hook-unknown-' + str(index))) + '"><strong>' + html.escape(hook.get('title', f'Acción {index}')) + '</strong>'
            + ('<p>' + html.escape(hook['description']) + '</p><code>' + html.escape(hook['handler']) + '</code><span class="hook-meta">Activación: '
               + html.escape(hook['matcher'].replace('|', ' · ') or 'Cada ocurrencia del evento') + '</span>' if 'handler' in hook else '<p>Función pública no identificada en esta definición.</p>')
            + _hook_details(hook) + ('<a class="hook-link" href="#' + html.escape(hook['id']) + '">Enlace a acción</a>' if 'id' in hook else '') + '</li>'
            for index, hook in enumerate(hooks, 1)
        )
        cards.append(f'<article data-kind="hooks" data-runtime="{html.escape(runtime)}" class="card"><small>EVENTO DE HOOK · {html.escape(runtime)}</small><h2>{html.escape(event)}</h2><p>{len(hooks)} acciones configuradas. Carga sin verificar · ejecución sin verificar.</p><ul class="hook-handlers">{handlers}</ul></article>')
    return '\n'.join(cards)


def _hook_details(hook):
    esc = lambda value: html.escape(str(value), quote=True)
    unit = hook.get('timeout_unit', 's')
    timeout = hook.get('timeout')
    label = 'Supervisión del adapter' if hook.get('timeout_provenance') == 'adapter-supervision' else 'Timeout'
    budget = f'{label}: {esc(timeout)} {esc(unit)}' if timeout is not None else 'Presupuesto inválido' if hook.get('timeout_status') == 'invalid' else 'Timeout: no declarado'
    source = hook.get('source', 'Fuente no identificada')
    provenance = 'Presupuesto del adapter; no equivale a un timeout de registro del runtime.' if hook.get('timeout_provenance') == 'adapter-supervision' else 'Presupuesto declarado en el registro del runtime; no acredita finalización dentro del límite.'
    identity = ''
    if hook.get('behavior') == 'guard':
        roles = hook.get('role_ids', [])
        identity = '<p>Identidad declarada: ' + (esc(', '.join(roles)) if roles else 'sin verificar') + '. Guardia global con alcance por identidad; configuración y ejecución son evidencias distintas.</p>'
    return ('<span class="hook-meta"> · ' + budget + '</span><details><summary>Fuente, contrato y límites</summary><p>Canal nativo: '
            + esc(hook.get('native_event', hook['event'])) + '</p><p>Comportamiento: '
            + {'guard': 'Guardia de roles', 'informative': 'Informativo'}.get(hook.get('behavior'), 'Sin identificar')
            + ' · ámbito global.</p>' + identity + '<p>' + provenance + '</p><code>'
            + esc(source) + '#' + esc(hook.get('locator', '')) + '</code></details>')


def _flow_html(data):
    stages = [
        ('discover', 'Descubrir', 'Definir requisitos y evaluar alcance, esfuerzo y riesgos.', ('analyst', 'evaluator')),
        ('design', 'Diseñar', 'Comparar opciones y definir la arquitectura de la iniciativa.', ('architect',)),
        ('plan', 'Planificar', 'Ordenar tareas, dependencias y criterios de aceptación.', ('planner',)),
        ('build', 'Construir', 'Implementar las tareas del plan y sus pruebas.', ('implementer',)),
        ('review', 'Revisar', 'Comprobar conformidad y defectos con revisión independiente.', ('reviewer',)),
        ('validate', 'Validar', 'Ejecutar QA y revisar seguridad cuando corresponda.', ('qa', 'nemesis')),
    ]
    available = {entry['name'] for entry in data['agents']} & set(data.get('workflow', {}).get('roles', {}))
    buttons, panels = [], []
    for index, (identifier, title, purpose, roles) in enumerate(stages):
        buttons.append(f'<button type="button" id="flow-button-{identifier}" aria-controls="flow-{identifier}" aria-pressed="{str(index == 0).lower()}">{title}</button>')
        links = ''.join(f'<a href="#role-{role}">{role} →</a>' for role in roles if role in available)
        panels.append(f'<div class="flow-detail" id="flow-{identifier}" aria-labelledby="flow-button-{identifier}" {"hidden" if index else ""}><strong>{title}</strong><p>{purpose}</p><div class="flow-role-links">{links or "Roles no disponibles en esta instantánea."}</div></div>')
    return '<div class="flow-steps" aria-label="Etapas del workflow">' + ''.join(buttons) + '</div>' + ''.join(panels)


def _extension_card(piece, conflicts):
    esc = lambda value: html.escape(str(value), quote=True)
    kinds = {'agent': 'AGENTE', 'skill': 'SKILL', 'command': 'COMANDO',
             'persona': 'PERSONA', 'tool-source': 'FUENTE DE TOOL', 'mcp': 'SERVIDOR MCP DECLARADO'}
    scopes = {'project': 'Proyecto', 'user': 'Usuario', 'local': 'Local del proyecto'}
    ownership = {'managed': 'Gestionada', 'modified': 'Modificada',
                 'unmanaged': 'Propia · sin registro', 'unknown': 'Propiedad sin verificar'}
    source = piece['source'] + ('#' + piece['locator'] if piece['locator'] else '')
    repeated = [item for item in conflicts if piece['id'] in item['ids']]
    conflict_html = ''.join('<p class="extension-conflict">Nombre repetido: <code>' + esc(item['name']) + '</code>; '
                          + ('coincide con <code>' + esc(item['bundled_source']) + '</code> del plugin.'
                             if 'bundled_source' in item else 'contrasta las fuentes con el runtime antes de invocar.') + '</p>'
                          for item in repeated)
    status = '<span class="extension-status">Disponibilidad sin verificar</span>'
    if piece.get('enabled') is False:
        status += '<span class="extension-status">Deshabilitado en la configuración</span>'
    if piece.get('definition_status') == 'invalid':
        status += '<span class="extension-status">Declaración MCP inválida</span>'
    details = '<p>Propiedad: ' + esc(ownership[piece['ownership']]) + '.</p><code>' + esc(source) + '</code>'
    details += '<p>Identificador para la tarea:</p><code class="extension-id">' + esc(piece['id']) + '</code>'
    if piece.get('root_id', 'project') != 'project':
        details += '<p>Raíz de usuario: <code>' + esc(piece['root_id']) + '</code></p>'
    if piece.get('owner_agent'):
        details += '<p>Declarado para el agente: ' + esc(piece['owner_agent']) + '.</p>'
    if piece.get('declared_tools'):
        details += '<p>Tools declaradas: ' + esc(', '.join(piece['declared_tools'])) + '.</p>'
    if piece.get('declared_permissions'):
        details += '<p>Reglas declaradas: ' + esc(json.dumps(piece['declared_permissions'], ensure_ascii=False)) + '. La sesión determina los permisos efectivos.</p>'
    return ('<article class="card extension-card" data-kind="' + esc(piece['kind'])
            + '" data-scope="' + esc(piece['scope']) + '" data-runtime="' + esc(piece['runtime']) + '">'
            + '<small>' + esc(kinds[piece['kind']]) + ' · ' + esc(scopes[piece['scope']]) + '</small>'
            + '<h2>' + esc(piece['name']) + '</h2><p>' + esc(piece['description']) + '</p>'
            + '<p class="extension-runtime">' + esc(piece['runtime']) + '</p>' + status + conflict_html
            + '<details><summary>Origen, propiedad e identificador</summary>' + details + '</details></article>')


def _extensions_html(data):
    inventory = data.get('extensions')
    if inventory is None:
        body = '<p class="extension-empty">Las extensiones de proyecto no se incluyeron en esta instantánea.</p>'
        total = 0
    else:
        total = len(inventory['pieces'])
        body = ''.join(_extension_card(piece, inventory['conflicts']) for piece in inventory['pieces'])
        if not body:
            body = '<p class="extension-empty">No se encontraron declaraciones en las fuentes inspeccionadas.</p>'
        body = '<div class="grid" id="extension-cards">' + body + '</div>'
        if inventory['warnings']:
            body += '<details class="extension-warnings"><summary>Inventario parcial · ' + str(len(inventory['warnings'])) + ' aviso(s)</summary><ul>'
            body += ''.join('<li>' + html.escape(warning) + '</li>' for warning in inventory['warnings']) + '</ul></details>'
    controls = '''<div class="controls extension-controls"><div class="search-wrap"><input id="extension-search" type="search" placeholder="Buscar extensiones propias" aria-label="Buscar extensiones"></div>
<select id="extension-kind" aria-label="Tipo de extensión"><option value="all">Todos los tipos</option><option value="agent">Agentes</option><option value="skill">Skills</option><option value="persona">Personas</option><option value="command">Comandos</option><option value="tool-source">Fuentes de tools</option><option value="mcp">MCP</option></select>
<select id="extension-scope" aria-label="Origen de extensión"><option value="all">Todos los orígenes</option><option value="project">Proyecto</option><option value="user">Usuario</option><option value="local">Local del proyecto</option></select>
<select id="extension-runtime" aria-label="Runtime de extensión"><option value="all">Todos los runtimes</option><option value="claude-code">Claude Code</option><option value="codex">Codex</option><option value="opencode">OpenCode</option></select></div>
<p id="extension-results" aria-live="polite"></p>'''
    return ('<section id="extensions"><div class="section-head"><div><h2>Tus extensiones</h2>'
            + '<p>Declaraciones de proyecto y usuario. La sesión determina carga, conexión y permisos; los roles del ciclo se mantienen.</p></div>'
            + '<span class="section-pill">' + str(total) + ' declaraciones</span></div>' + controls + body + '</section>')


def _stats_html(data):
    counts = {**data['counts'], 'hooks': len({(hook.get('runtime', 'unknown'), hook['event']) for hook in data['hooks']})}
    labels = {'agents': 'Agentes', 'skills': 'Skills', 'commands': 'Comandos', 'tools': 'Herramientas', 'hooks': 'Registros de hook'}
    return ''.join(f'<div class="stat"><strong>{count}</strong><span>{labels[kind]}</span></div>' for kind, count in counts.items()), counts


def _notes_text(data, counts):
    sources = {'runtimes': data['runtimes'], 'memory': data['memory'], 'warnings': data['warnings'],
               'hook_sources': data.get('hook_sources', {}), 'hook_handlers': data['counts']['hooks'],
               'hook_groups': counts['hooks'],
               'diagnostics': {key: value for key, value in data.get('diagnostics', {}).items() if key != 'report'}}
    if 'extensions' in data:
        sources['extensions'] = {key: data['extensions'][key] for key in ('registry_status', 'warnings', 'orphans')}
    return html.escape(json.dumps(sources, ensure_ascii=False, indent=2))


def _cuerpo_catalogo(data, live):
    stats, counts = _stats_html(data)
    refresh = ('Catálogo y diagnóstico fijados al arranque; progreso local con actualización periódica.' if live
               else 'Regenera la exportación para actualizarla.')
    progress = ('Los presupuestos y la cartera detallada se consultan en el dashboard del roadmap.' if live
                else 'El progreso de iniciativas se consulta en el dashboard del roadmap.')
    return (
        '<p id="navigation-status" class="navigation-status" role="status" aria-live="polite"></p>'
        '<section id="flujo"><div class="section-head"><div><h2>De la idea a la entrega</h2>'
        '<p>Roles con responsabilidades propias y una selección de guías compartida.</p></div></div>'
        + _flow_html(data) + '</section>'
        '<section id="inventario"><h2>Inventario de capacidades</h2><div class="stats">' + stats + '</div></section>'
        '<section id="piezas-por-tipo"><div class="section-head"><div><h2>Piezas por tipo</h2>'
        '<p>Cuántas piezas declara el bundle de cada tipo.</p></div></div><div id="grafico-piezas"></div>'
        '<noscript><p>Sin JavaScript no se dibuja el gráfico: las cifras están en el inventario de arriba.</p></noscript></section>'
        '<section id="catalog"><div class="section-head"><div><h2>Explora el catálogo</h2><p>Busca por nombre, función, herramienta o evento.</p></div>'
        '<span class="section-pill">Definiciones del bundle</span></div>'
        '<div class="controls"><div class="search-wrap"><input id="search" type="search" placeholder="¿Qué necesitas hacer?" aria-label="Buscar capacidades"></div>'
        '<select id="kind" aria-label="Tipo de capacidad"><option value="all">Todas las capacidades</option><option value="agents">Agentes</option>'
        '<option value="skills">Skills</option><option value="commands">Comandos</option><option value="tools">Herramientas</option><option value="hooks">Hooks</option></select>'
        '<select id="hook-runtime" aria-label="Runtime de hooks"><option value="all">Hooks de todos los runtimes</option>'
        '<option value="claude-code">Claude Code</option><option value="codex">Codex</option><option value="opencode">OpenCode</option></select></div>'
        '<p class="filter-note">El filtro de runtime afecta a los registros de hook; el resto del catálogo conserva sus declaraciones.</p>'
        '<p id="results" aria-live="polite"></p><div class="grid">' + _cards(data) + '</div></section>'
        + _extensions_html(data) + _workflow_html(data)
        + '<details id="source-notes"><summary>Fuentes de runtime y memoria · ver presencia y avisos</summary>'
        '<p>La presencia de un archivo no acredita ejecución, acceso ni salud del servicio.</p><pre>' + _notes_text(data, counts) + '</pre></details>'
        '<footer>Catálogo local · ' + refresh + ' Las guardias globales aplican políticas a identidades de rol concretas; su declaración no acredita ejecución. '
        'Los ciclos se definen en los comandos. ' + progress + '</footer>')


def _seccion_progreso():
    return '''<section id="operations"><div class="section-head"><div><h2>Progreso del proyecto</h2>
<p>Ledger recién leído: los estados de las tareas no demuestran agentes vivos. Catálogo y diagnóstico permanecen fijados al arranque.</p></div><span class="section-pill">Lectura local · cada 5 s</span></div>
<div class="controls"><div class="search-wrap"><input id="progress-search" type="search" placeholder="Buscar iniciativas o tareas" aria-label="Buscar progreso"></div>
<select id="progress-state" aria-label="Estado de iniciativa"><option value="all">Todos los estados</option><option value="borrador">Borrador</option><option value="en-progreso">En progreso</option><option value="en-revision">En revisión</option><option value="completado">Completado</option><option value="cancelado">Cancelado</option><option value="unknown">Sin estado reconocido</option></select>
<button id="progress-refresh" type="button">Actualizar ahora</button></div>
<p id="progress-status" role="status" aria-live="polite">Consultando el ledger seleccionado…</p><p id="progress-freshness">Sin lectura disponible todavía.</p>
<p id="progress-results" aria-live="polite"></p><div id="progress-cards" class="grid"></div></section>'''


def _seccion_actividad(live, disponible):
    if not live:
        return '<section id="activity"><h2>Señales de actividad</h2><p>Sin servicio: este archivo estático no consulta señales de actividad.</p></section>'
    if not disponible:
        return '<section id="activity"><h2>Señales de actividad</h2><p>Señales no disponibles: falta el recurso local de esta vista.</p></section>'
    return '''<section id="activity"><div class="section-head"><div><h2>Señales de actividad</h2>
<p>Señales nativas recientes, separadas del progreso declarado. Un fin de respuesta o ejecución no acredita presencia ni destrucción.</p></div><span class="section-pill">Lectura local · cada 5 s</span></div>
<button id="activity-refresh" type="button">Actualizar señales</button>
<p id="activity-status" role="status" aria-live="polite">Consultando señales…</p>
<p id="activity-freshness">Sin lectura disponible todavía.</p>
<p id="activity-coverage">collection_complete: false · Colección incompleta; no representa todos los agentes o sesiones.</p>
<div id="activity-cards" class="grid" aria-live="polite"></div></section>'''


def _seccion_memoria():
    return '''<section id="memory-query"><div class="section-head"><div><h2>Consulta tu conocimiento</h2>
<p>Busca en la memoria local del proyecto. El cuerpo y las relaciones se leen solo cuando los seleccionas.</p></div><span class="section-pill">Consulta explícita · local</span></div>
<form id="memory-form" class="controls"><div class="search-wrap"><input id="memory-text" type="search" placeholder="¿Qué necesitas recordar?" aria-label="Buscar conocimiento"></div>
<input id="memory-area" type="text" placeholder="Área opcional" aria-label="Área de conocimiento">
<input id="memory-type" type="text" list="memory-types" placeholder="Tipo opcional" aria-label="Tipo de conocimiento"><datalist id="memory-types"><option value="adr">Decisiones</option><option value="gotcha">Gotchas</option><option value="leccion">Lecciones</option></datalist>
<button id="memory-search" type="submit">Buscar</button></form>
<p id="memory-status" role="status" aria-live="polite">Sin consultas realizadas. Pulsa Buscar para leer la memoria local.</p>
<p id="memory-freshness">Sin lectura disponible todavía.</p><p id="memory-results-date"></p>
<div id="memory-results" class="grid"></div><div id="memory-selected" tabindex="-1" aria-label="Entrada seleccionada"></div>
<div id="memory-related" tabindex="-1" aria-label="Relaciones del conocimiento"></div>
<p class="filter-note">Estados y evidencia declarados conservan su procedencia. Una cita o un hash no prueban aprobación humana; los límites de lectura se muestran en cada consulta.</p></section>'''


def _seccion_revision(review_id):
    return '''<section id="plan-review" data-review-id="''' + html.escape(review_id) + '''"><div class="section-head"><div><h2>Revisa el plan seleccionado</h2>
<p>Lee la vista completa, comenta sus secciones y decide. El recibo se consume desde el workflow autorizado.</p></div><span class="section-pill">Revisión explícita · local</span></div>
<p id="review-status" role="status" aria-live="polite">Consultando la revisión seleccionada…</p>
<p id="review-metadata"></p><pre id="review-version"></pre><div id="review-sections"></div>
<div class="review-actions"><button id="review-save" type="button" disabled>Guardar comentarios</button>
<button id="review-approve" type="button" disabled>Aprobar la vista</button><button id="review-changes" type="button" disabled>Pedir cambios</button>
<button id="review-refresh" type="button" disabled>Cargar versión actual</button><button id="review-close" type="button">Cerrar sin decidir</button>
<button id="review-open" type="button" hidden>Volver a la revisión</button></div>
<section aria-labelledby="review-feedback-title"><h3 id="review-feedback-title">Respuestas a tus comentarios</h3>
<p>El ack confirma recepción. La atención declarada y la anotación humana opcional se muestran por separado.</p>
<div id="review-feedback" aria-live="polite"></div></section>
<section aria-labelledby="review-history-title"><h3 id="review-history-title">Respuestas de versiones anteriores</h3>
<div id="review-feedback-history" aria-live="polite"></div></section>
<p class="filter-note">Cerrar conserva el borrador y no crea una decisión. Este panel no inicia agentes ni acredita QA.</p></section>'''


def _cuerpo_inicio():
    """Esqueleto de Inicio: lo rellena `page-inicio.js` con la cartera (api/cartera o el JSON incrustado)."""
    return (
        '<p id="cartera-estado" class="filter-note" role="status" aria-live="polite">Leyendo la cartera…</p>'
        '<section id="cartera-estados"><div class="section-head"><div><h2>Iniciativas por estado de spec</h2>'
        '<p>Cuántas iniciativas hay en cada estado de su spec. Una spec ilegible no cuenta en ningún estado.</p></div></div>'
        '<div id="grafico-estados"></div>'
        '<noscript><p>Sin JavaScript no se leen las cifras de la cartera ni se dibuja el gráfico.</p></noscript></section>'
        '<section id="cartera-avance"><h2>Avance global</h2><p id="avance-global" role="status">Sin datos todavía.</p>'
        '<div id="avance-fuera-de-tope"></div></section>'
        '<section id="cartera-coste"><h2>Coste real frente al estimado</h2><div id="coste-cartera"></div>'
        '<p id="coste-procedencia"></p></section>')


def _cuerpo_iniciativas():
    """Esqueleto de Iniciativas: lo rellena `page-iniciativas.js` con la cartera (api/cartera o el JSON incrustado)."""
    return (
        '<p id="cartera-estado" class="filter-note" role="status" aria-live="polite">Leyendo la cartera…</p>'
        '<section id="iniciativas-kanban"><div class="section-head"><div><h2>Iniciativas por estado de spec</h2>'
        '<p>Solo lectura: una columna por estado y una tarjeta por iniciativa. La tarjeta con plan lleva a su Plan.</p></div></div>'
        '<div id="kanban-iniciativas" class="kanban"></div>'
        '<noscript><p>Sin JavaScript no se leen las iniciativas.</p></noscript></section>'
        '<section id="iniciativas-graficos"><div class="section-head"><div><h2>Horas y coste por iniciativa</h2>'
        '<p>Real frente a estimado. Una iniciativa sin datos aparece en la tabla como «sin datos» y no en las barras.</p></div></div>'
        '<div id="grafico-horas"></div><div id="grafico-coste"></div></section>')


def _cuerpo_plan_indice(planes):
    """Índice de `plan.html`: un enlace por iniciativa con plan, estático (sin JS y válido en servido y exportado).
    `planes` = `[{'id', 'slug', 'titulo'}]` ya saneados; `None` = copia estática sin `--project`."""
    if planes is None:
        return ('<section id="plan-indice"><h2>Planes por iniciativa</h2><p class="ausencia">Sin datos: esta copia '
                'estática no incluye los planes (se genera con --project).</p></section>')
    if not planes:
        return ('<section id="plan-indice"><h2>Planes por iniciativa</h2><p class="ausencia">Ninguna iniciativa del '
                'roadmap tiene plan (improvement-plan.md).</p></section>')
    items = ''.join(f'<li><a href="plan-{html.escape(p["id"])}.html">{html.escape(p["slug"])}</a>'
                    f' <span class="filter-note">{html.escape(p["titulo"])}</span></li>' for p in planes)
    return ('<section id="plan-indice"><h2>Planes por iniciativa</h2><p>Cada plan muestra el kanban de sus tareas, en solo '
            'lectura.</p><nav aria-label="Planes por iniciativa"><ul>' + items + '</ul></nav></section>')


REVISION_ACTIVAR = '--serve --project &lt;proyecto&gt; --review-panel --review-state-root &lt;proyecto&gt;/.claude/plan-review'


def _bloque_revision_plan(revision):
    """Bloque de revisión de `plan-<id16>.html` según el modo (CA-52, CA-53): `exportado` (copia estática, nunca
    controles ni lectura de `.claude/plan-review/`), `inactiva` (servido sin `--review-panel`: explica cómo activarla) o
    `activa` (servido con `--review-panel`: el estado y el botón «Revisar este plan», que `panel-review.js` muestra)."""
    if revision == 'activa':
        return ('<section id="plan-revision" data-revision="activa"><div class="section-head"><h2 id="plan-revision-titulo">'
                'Revisión del plan</h2></div><p id="plan-revision-estado" class="filter-note" role="status" '
                'aria-live="polite">Consultando el estado de revisión…</p>'
                '<button id="plan-revisar" type="button" hidden>Revisar este plan</button></section>')
    if revision == 'inactiva':
        return ('<p id="plan-revision" data-revision="inactiva" class="filter-note">La revisión del plan se activa al '
                'arrancar el panel con <code>' + REVISION_ACTIVAR + '</code>.</p>')
    if revision != 'exportado':
        raise ValueError('modo de revisión desconocido')
    return ('<p id="plan-revision" data-revision="exportado" class="filter-note">Revisión · estado de revisión: solo en '
            'modo servido.</p>')


def cuerpo_plan_iniciativa(revision='exportado'):
    """Esqueleto de `plan-<id16>.html`: lo rellena `page-plan.js` con `api/plan-<id16>` (servido) o con el plan
    incrustado en `panel-data` (exportado). `revision`: `exportado` (por defecto), `inactiva` o `activa`."""
    return (
        '<p><a href="plan.html">Todos los planes</a> · <a href="iniciativas.html">Iniciativas</a></p>'
        '<p id="plan-estado" class="filter-note" role="status" aria-live="polite">Leyendo el ledger…</p>'
        '<p><span id="plan-frescura" class="filter-note"></span> '
        '<button id="plan-refrescar" type="button" hidden>Actualizar ahora</button></p>'
        '<p id="plan-anuncio" class="solo-lectores" role="status" aria-live="polite"></p>'
        + _bloque_revision_plan(revision) +
        '<section id="plan-detalle" class="detalle" role="region" aria-labelledby="plan-detalle-titulo" tabindex="-1" hidden>'
        '<div class="section-head"><h2 id="plan-detalle-titulo">Detalle de la tarea</h2>'
        '<button id="plan-detalle-cerrar" type="button">Cerrar detalle</button></div>'
        '<div id="plan-detalle-contenido" aria-busy="false"></div></section>'
        '<section id="plan-kanban"><div class="section-head"><div><h2 id="plan-titulo">Tareas del plan</h2>'
        '<p>Solo lectura: una columna por estado del ledger y una tarjeta por tarea.</p></div></div>'
        '<div id="kanban-plan" class="kanban"></div>'
        '<noscript><p>Sin JavaScript no se leen las tareas del plan.</p></noscript></section>'
        '<section id="plan-graficos"><div class="section-head"><div><h2>Avance y horas del plan</h2>'
        '<p>Cada gráfico lleva su tabla equivalente; un dato ausente se dice «sin datos» y nunca se pinta como 0.</p></div></div>'
        '<div id="grafico-avance-fase"></div><div id="grafico-horas-fase"></div><div id="grafico-horas-tarea"></div>'
        '<div id="grafico-burndown"></div></section>')


def cuerpos_paginas(data, *, live=False, review_enabled=False, review_id='', actividad=True, planes=None):
    """Cuerpo HTML (ya escapado) de cada una de las 7 páginas, por slug.

    `planes` (`[{'id', 'slug', 'titulo'}]`, ya saneados; `None` sin `--project`) alimenta el índice de `plan.html`.

    Catálogo y Diagnóstico llevan hoy todo su contenido; el resto lleva, en modo servido, la sección viva
    que le toca (progreso → Inicio y Plan; revisión → Plan; actividad → Agentes; memoria → Memoria) y,
    en el exportado, su marcador provisional.
    """
    pages = _load_pages()
    cuerpos = {slug: pages.PLACEHOLDER for slug, _, _ in pages.PAGES}
    cuerpos['catalogo'] = _cuerpo_catalogo(data, live)
    cuerpos['diagnostico'] = _diagnostics_html(data.get('diagnostics', {'status': 'not_provided'}))
    cuerpos['agentes'] = _seccion_actividad(live, actividad)
    cuerpos['inicio'] = _cuerpo_inicio()
    cuerpos['iniciativas'] = _cuerpo_iniciativas()
    cuerpos['plan'] = _cuerpo_plan_indice(planes)
    if live:
        cuerpos['inicio'] += _seccion_progreso()
        cuerpos['plan'] += _seccion_progreso() + (_seccion_revision(review_id) if review_enabled else '')
        cuerpos['memoria'] = _seccion_memoria()
    return cuerpos


_PAGES_MODULE = None


def _load_pages():
    """Carga panel_pages.py del propio bundle (código de confianza; --root es dato)."""
    global _PAGES_MODULE
    if _PAGES_MODULE is None:
        path = Path(__file__).resolve().parent / 'panel_pages.py'
        spec = importlib.util.spec_from_file_location('panel_pages', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _PAGES_MODULE = module
    return _PAGES_MODULE


def _scrubber(args):
    """Saneado único del panel (CA-41), exportado y servido: redactar -> anonimizar (raíz -> `.`, home -> `~`,
    usuario -> `<usuario>`, correos -> `<correo>`). Los controles y el recorte los aplica cada campo después."""
    if ANONIMIZAR is None:
        raise ValueError('bundled redactor unavailable')
    roots = [str(Path(value).resolve()) for value in (args.project, args.root) if value]
    roots += [str(value) for value in (args.project, args.root) if value]
    homes = [str(Path.home())]
    if args.home:
        homes.append(str(args.home))
    try:
        user = getpass.getuser()
    except Exception:  # noqa: BLE001 - sin usuario resoluble no hay nada que sustituir
        user = ''
    return lambda text: ANONIMIZAR(REDACTOR(text), roots, homes, user)


def _cartera_exportada(args, scrub):
    """Cartera para la copia estática: la proyecta `panel_data` y la limpia el MISMO saneador que el servidor
    (`serve_panel._scrubbed`). Sin `--project` no hay roadmap que leer y la página lo dice."""
    if not args.project:
        return None
    try:
        servicio = _load_server()
        return servicio._scrubbed(servicio._load_data().cartera(Path(args.project)), scrub)
    except (OSError, ValueError, ImportError, AttributeError, SyntaxError):
        return None


def _planes_exportados(args, scrub, cartera):
    """Páginas Plan de la copia estática: una por iniciativa con plan de la cartera (ya anonimizada), con su plan
    proyectado y saneado por el MISMO saneador que el servidor. Sin `--project`, `None` (el índice lo dice)."""
    if cartera is None or not args.project:
        return None
    try:
        servicio = _load_server()
        data = servicio._load_data()
        planes = []
        for fila in cartera.get('iniciativas', []):
            if not fila.get('tiene_plan'):
                continue
            plan = data.plan(Path(args.project), fila['id'])
            if plan is None:
                continue
            limpio = servicio._scrubbed(plan, scrub)
            # Detalle de cada tarea del plan, incrustado: la copia estática no puede preguntar a `api/plan-<id16>-<T-XX>`.
            detalles = {}
            for fila_tarea in limpio.get('tareas') or []:
                detalle = data.tarea(Path(args.project), fila['id'], fila_tarea['id'])
                if detalle is not None:
                    detalles[fila_tarea['id']] = servicio._scrubbed(detalle, scrub)
            planes.append({'id': fila['id'], 'slug': fila['slug'], 'titulo': fila['titulo'],
                           'datos': {'plan': limpio, 'detalles': detalles}})
        return planes
    except (OSError, ValueError, ImportError, AttributeError, SyntaxError):
        return None


def _export(args, data, cartera=None, planes=None):
    pages = _load_pages()
    indice = None if planes is None else [{k: p[k] for k in ('id', 'slug', 'titulo')} for p in planes]
    paginas = None if planes is None else [{'id': p['id'], 'cuerpo': cuerpo_plan_iniciativa(), 'datos': p['datos']} for p in planes]
    written, warnings = pages.exportar_sitio(args.export, data, unsafe_link=_unsafe_link,
                                             cuerpos=cuerpos_paginas(data, planes=indice), cartera=cartera,
                                             planes=paginas)
    for warning in warnings:
        print(f'plugin-panel: aviso: {warning}', file=sys.stderr)
    return written


def _load_server():
    path = Path(__file__).resolve().parent / 'serve_panel.py'
    spec = importlib.util.spec_from_file_location('panel_local_server', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default=str(Path(__file__).resolve().parents[3]))
    parser.add_argument('--export', metavar='DIR', help='exporta el panel multi-página (7 páginas + assets + manifiesto) a una carpeta')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--serve', action='store_true', help='explicit loopback dashboard with canonical ledger refresh')
    parser.add_argument('--port', type=int, help='local server port; default ephemeral; only with --serve')
    parser.add_argument('--review-initiative', help='exact initiative relative path; explicit review only with --serve')
    parser.add_argument('--review-state-root', help='explicit owner state root; requires --review-initiative')
    parser.add_argument('--review-gate-key', choices=('requested-review', 'plan-ok'), help='review gate; default requested-review; requires explicit review selection')
    parser.add_argument('--review-panel', action='store_true', help='enable plan review from every Plan page; requires --serve, --project and --review-state-root; combinable with --review-initiative')
    parser.add_argument('--project', help='project root to inspect for local extensions')
    parser.add_argument('--cwd', help='task package within the project root')
    parser.add_argument('--home', help='user root to inspect')
    parser.add_argument('--runtime', choices=('claude-code', 'codex', 'opencode', 'all'), default='all')
    parser.add_argument('--project-only', action='store_true')
    parser.add_argument('--user-root', action='append', default=[], metavar='RUNTIME=PATH')
    parser.add_argument('--diagnostics-report', help='explicit portable doctor JSON snapshot; requires --project for scope')
    args = parser.parse_args(argv)
    if args.serve and (not args.project or args.export or args.json or args.home or args.user_root):
        parser.error('--serve requires --project and excludes --export, --json, --home and --user-root')
    if args.port is not None and (not args.serve or not 0 <= args.port <= 65535):
        parser.error('--port requires --serve and a value from 0 to 65535')
    if (args.review_initiative is not None or args.review_state_root is not None or args.review_gate_key is not None) and (
            not args.serve or not args.project or not args.review_state_root
            or not (args.review_initiative or args.review_panel)):
        parser.error('--review-initiative and --review-state-root require each other, --serve and explicit --project')
    if args.review_gate_key is not None and not args.review_initiative:
        parser.error('--review-gate-key requires --review-initiative')
    if args.review_panel and (not args.serve or not args.project or not args.review_state_root):
        parser.error('--review-panel requires --serve, explicit --project and --review-state-root')
    try:
        scrub = _scrubber(args) if (args.export or args.serve) else None  # un solo saneado: exportado y servido
        data = build_inventory(args.root, project=args.project, home=args.home,
                               runtime=args.runtime, cwd=args.cwd, include_user=not (args.project_only or args.serve),
                               user_roots=args.user_root, diagnostics_report=args.diagnostics_report, scrub=scrub)
        if args.serve:
            try:
                server = _load_server()
            except (OSError, ValueError, ImportError, AttributeError, SyntaxError):
                raise ValueError('bundled panel server unavailable') from None
            selection = {'initiative': args.review_initiative, 'state_root': args.review_state_root,
                         'gate_key': args.review_gate_key or 'requested-review'} if args.review_initiative else None
            scope = {'state_root': args.review_state_root} if args.review_panel else None
            return server.run(args.project, data, port=args.port or 0, review_selection=selection, review_scope=scope,
                              scrub=scrub)
        if args.export:
            cartera = _cartera_exportada(args, scrub)
            written = _export(args, data, cartera, _planes_exportados(args, scrub, cartera))
            print(f'plugin-panel: exportados {len(written)} ficheros (7 páginas, assets y vendor) con su export-manifest.json',
                  file=sys.stderr if args.json else sys.stdout)
        if args.json or not args.export:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    except (OSError, UnicodeError, ValueError) as error:
        print(f'plugin-panel: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
