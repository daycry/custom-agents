#!/usr/bin/env python3
"""Inventory local declarations; never execute user components or contact servers."""
import argparse
from datetime import date
import hashlib
import importlib.util
import itertools
import json
import os
from pathlib import Path
import re
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001

try:
    import tomllib
except ImportError:
    tomllib = None

MAX_BYTES = 512 * 1024
MAX_TOTAL_BYTES = 8 * 1024 * 1024
MAX_PIECES = 1000
MAX_DEPTH = 32
MAX_SELECTED = 20
RUNTIMES = ('claude-code', 'codex', 'opencode')
HERE = Path(__file__).resolve().parent


def _bundled(name):
    path = HERE / name
    spec = importlib.util.spec_from_file_location('pieces_' + path.stem.replace('-', '_'), path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


try:
    GUARD = _bundled("capability-route.py")
    REDACT = _bundled("redact.py").redactar
except (OSError, ImportError, AttributeError):
    GUARD, REDACT = None, None


def _absolute(path):
    return Path(os.path.abspath(path))


def _safe_path(path):
    if GUARD is None:
        raise ValueError('bundled guard unavailable')
    if any(GUARD._linked(p) for p in (path, *path.parents)):
        raise ValueError('linked path excluded')


def _object(value):
    if not isinstance(value, dict):
        raise ValueError('object required')
    return value


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError('duplicate JSON key')
        result[key] = value
    return result


def _jsonc(raw):
    """Remove comments/trailing commas outside strings; never evaluate expressions."""
    tokens, i, quoted = [], 0, False
    while i < len(raw):
        char = raw[i]
        if quoted:
            tokens.append(char)
            if char == '\\' and i + 1 < len(raw):
                i += 1
                tokens.append(raw[i])
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
            tokens.append(char)
        elif raw.startswith('//', i):
            end = raw.find('\n', i + 2)
            i = len(raw) if end < 0 else end
            tokens.append('\n')
            continue
        elif raw.startswith('/*', i):
            end = raw.find('*/', i + 2)
            if end < 0:
                raise ValueError('unclosed comment')
            tokens.append(' ')
            i = end + 2
            continue
        else:
            tokens.append(char)
        i += 1
    raw = ''.join(tokens)
    tokens, quoted, escaped = [], False, False
    for i, char in enumerate(raw):
        if not quoted and char == ',':
            following = i + 1
            while following < len(raw) and raw[following].isspace():
                following += 1
            if following < len(raw) and raw[following] in '}]':
                continue
        tokens.append(char)
        if char == '"' and not escaped:
            quoted = not quoted
        escaped = char == '\\' and not escaped if quoted else False
    return ''.join(tokens)


def _config(raw, suffix):
    if suffix == '.toml':
        if tomllib is None:
            raise ValueError('optional TOML parser unavailable')
        value = tomllib.loads(raw)
    else:
        value = json.loads(_jsonc(raw) if suffix == '.jsonc' else raw,
                           object_pairs_hook=_pairs)
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        if depth > MAX_DEPTH:
            raise ValueError('config nesting limit')
        children = item.values() if isinstance(item, dict) else item if isinstance(item, list) else ()
        pending.extend((child, depth + 1) for child in children)
    return _object(value)


def _scalar(value):
    value = value.strip()
    if value.startswith('"'):
        parsed = json.loads(value)
        if not isinstance(parsed, str):
            raise ValueError('string required')
        return parsed
    if value.startswith("'"):
        if not value.endswith("'"):
            raise ValueError('unclosed scalar')
        return value[1:-1].replace("''", "'")
    if value.startswith(('[', '{', '&', '*', '!')):
        raise ValueError('unsupported scalar')
    return re.split(r'\s+#', value, maxsplit=1)[0]


def _frontmatter(raw):
    lines = raw.splitlines()
    if not lines or lines[0] != '---':
        raise ValueError('frontmatter required')
    end = next((i for i, line in enumerate(lines[1:], 1) if line == '---'), None)
    if end is None:
        raise ValueError('unclosed frontmatter')
    return lines[1:end]


def _policy_child(policy, key, line, child):
    match = re.match(r'^([ \t]+)([^:]+):[ \t]*(.*)$', line)
    if not match:
        raise ValueError('invalid policy declaration')
    indentation, label, value = match.groups()
    if '\t' in indentation or len(indentation) > MAX_DEPTH:
        raise ValueError('unsupported policy indentation')
    label = _scalar(label)
    if child is None or len(indentation) == child[1]:
        if label in policy:
            raise ValueError('duplicate policy declaration')
        if key == 'tools':
            if value.strip().lower() not in ('true', 'false'):
                raise ValueError('boolean tool declaration required')
            policy[label] = value.strip().lower() == 'true'
        else:
            policy[label] = _scalar(value) if value.strip() else {}
        return label, len(indentation)
    if key != 'permission' or len(indentation) <= child[1] or not isinstance(policy[child[0]], dict):
        raise ValueError('invalid nested policy')
    if label in policy[child[0]]:
        raise ValueError('duplicate policy pattern')
    policy[child[0]][label] = _scalar(value)
    return child


def _metadata(raw, *, ignore_name=False):
    result, key, child = {}, None, None
    description_parts = []
    for line in _frontmatter(raw):
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        match = re.match(r'^(name|description|model|tools|permission):\s*(.*)$', line)
        if match:
            key, value = match.groups()
            if key == 'name' and ignore_name:
                key = None
                continue
            child = None
            if key in result:
                raise ValueError('duplicate metadata key')
            if key == 'tools':
                result[key] = [_scalar(x.strip()) for x in value.strip('[]').split(',') if x.strip()] if value.strip() else {}
            elif key == 'permission':
                result[key] = _scalar(value) if value.strip() else {}
            else:
                result[key] = '' if value in ('>', '|', '>-', '|-') else _scalar(value)
                if key == 'description':
                    description_parts = [result[key]]
        elif line.startswith((' ', '\t')) and key == 'description':
            description_parts.append(line.strip())
        elif key == 'tools' and line.lstrip().startswith('- '):
            if result[key] == {}:
                result[key] = []
            if not isinstance(result[key], list):
                raise ValueError('ambiguous tools declaration')
            result[key].append(_scalar(line.strip()[2:]))
        elif key in ('tools', 'permission') and line.startswith((' ', '\t')):
            child = _policy_child(_object(result[key]), key, line, child)
        else:
            key = None
    if description_parts:
        result['description'] = ' '.join(description_parts).strip()
    return result


def _agent_servers(raw):
    """Read only public MCP identity/transport from a Claude agent's YAML list."""
    servers, active, seen, current, property_indent = [], False, False, None, None
    entry_indent = None
    for line in _frontmatter(raw):
        if not line.strip() or line.lstrip().startswith('#'):
            continue
        if line.startswith('mcpServers:'):
            if seen:
                raise ValueError('duplicate agent server declaration')
            active, seen = True, True
            value = line.partition(':')[2].strip()
            if value:
                if not value.startswith('[') or not value.endswith(']'):
                    raise ValueError('server list required')
                for name in value[1:-1].split(','):
                    if name.strip():
                        servers.append((_scalar(name), {}, 'reference'))
            continue
        if not line.startswith((' ', '\t')):
            active, current = False, None
        if not active:
            continue
        entry = re.match(r'^([ ]*)-[ ]+(.+)$', line)
        if entry:
            indentation = len(entry[1])
            if entry_indent is None:
                entry_indent = indentation
            if indentation > entry_indent and current is not None:
                continue  # Nested args and other private lists are not MCP identities.
            if indentation != entry_indent or indentation > MAX_DEPTH:
                raise ValueError('unsupported server list indentation')
            value = entry[2].strip()
            if value.endswith(':'):
                current = {}
                servers.append((_scalar(value[:-1]), current, 'inline'))
            else:
                current = None
                servers.append((_scalar(value), {}, 'reference'))
            property_indent = None
        elif current is not None:
            prop = re.match(r'^([ ]+)([A-Za-z_]+):[ ]*(.*)$', line)
            if not prop:
                continue  # Nested private config is neither interpreted nor exported.
            indentation = len(prop[1])
            if property_indent is None:
                property_indent = indentation
            if indentation != property_indent:
                continue
            field, value = prop[2], prop[3]
            if field in ('command', 'url'):
                current[field] = 'declared'  # Only presence is public, never the value.
            elif field == 'type':
                current[field] = _scalar(value)
        else:
            raise ValueError('unsupported agent server list')
    if len(servers) > 128 or len({name for name, _, _ in servers}) != len(servers):
        raise ValueError('duplicate or excessive agent servers')
    return servers


def _redact(value):
    if isinstance(value, str):
        return _public_text(value)
    if isinstance(value, list):
        return [_redact(item) for item in value]
    if isinstance(value, dict):
        return {key: _redact(item) for key, item in value.items()}
    return value


def _public_text(value):
    return re.sub(r'[\x00-\x1f\x7f-\x9f]', lambda m: f'\\u{ord(m[0]):04x}', REDACT(value))


def _tool_names(value):
    if isinstance(value, dict):
        if any(type(flag) is not bool for flag in value.values()):
            raise ValueError('invalid tool policy')
        names = list(value)
    else:
        names = value
    if not isinstance(names, list) or len(names) > 128 or any(not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_*?().:-]{1,128}', name) for name in names):
        raise ValueError('invalid tool declarations')
    return list(dict.fromkeys(names))


def _permission_declarations(value):
    if isinstance(value, str):
        value = {'*': value}
    _object(value)
    _tool_names(list(value))
    result = {}
    for name, action in value.items():
        public_name = _public_text(name)
        if public_name in result:
            raise ValueError('ambiguous redacted permission names')
        if isinstance(action, dict):
            if len(action) > 128 or any(not isinstance(rule, str) or rule not in ('allow', 'ask', 'deny') for rule in action.values()):
                raise ValueError('invalid permission patterns')
            result[public_name] = 'pattern-rules'
        elif isinstance(action, str) and action in ('allow', 'ask', 'deny'):
            result[public_name] = action
        else:
            raise ValueError('invalid permission declaration')
    return result


def _registry_text(value, maximum=256):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        raise ValueError('invalid registry text')
    return value


def _server_metadata(server, runtime, declaration):
    enabled = None if runtime == 'claude-code' else server.get('enabled')
    if enabled is not None and type(enabled) is not bool:
        raise ValueError('invalid enabled declaration')
    transport = server.get('type')
    if runtime == 'claude-code':
        if declaration == 'reference':
            return {'transport': 'unknown', 'enabled': None}
        if transport == 'streamable-http':
            transport = 'http'
        if transport is None:
            transport = 'stdio'
        required = 'command' if transport == 'stdio' else 'url'
        endpoint = server.get(required)
        if transport not in ('stdio', 'http', 'sse', 'ws') or not isinstance(endpoint, str) or not endpoint.strip():
            return {'transport': 'unknown', 'enabled': None, 'definition_status': 'invalid'}
    else:
        if transport is None:
            transport = 'stdio' if isinstance(server.get('command'), str) else 'http' if isinstance(server.get('url'), str) else 'unknown'
        if transport not in ('stdio', 'http', 'sse', 'local', 'remote'):
            transport = 'unknown'
    return {'transport': transport, 'enabled': enabled}


def _registry_entries(data):
    """Validate the complete O1 aggregate before granting any ownership."""
    if set(data) != {'version', 'hash_version', 'piezas'} or type(data['version']) is not int or data['version'] != 1 or data['hash_version'] != 'sha256-lf-1':
        raise ValueError('invalid registry header')
    if not isinstance(data['piezas'], list) or len(data['piezas']) > MAX_PIECES:
        raise ValueError('registry limit')
    entries, names = {}, set()
    fields = {'nombre', 'forma', 'area', 'origen', 'creada', 'evidencia', 'confirmaciones', 'destinos'}
    for piece in data['piezas']:
        if set(_object(piece)) != fields:
            raise ValueError('invalid registry piece')
        name = _registry_text(piece['nombre'])
        if name in names:
            raise ValueError('duplicate piece name')
        names.add(name)
        if not isinstance(piece['forma'], str) or piece['forma'] not in ('persona', 'tool', 'skill', 'agente'):
            raise ValueError('invalid piece form')
        if not isinstance(piece['origen'], str) or piece['origen'] not in ('generada', 'adoptada'):
            raise ValueError('invalid piece origin')
        _registry_text(piece['area'])
        created = _registry_text(piece['creada'], 10)
        if date.fromisoformat(created).isoformat() != created:
            raise ValueError('invalid creation date')
        evidence = piece['evidencia']
        if not isinstance(evidence, list) or len(evidence) > 128:
            raise ValueError('invalid evidence')
        for item in evidence:
            _registry_text(item, 1024)
        confirmations = _object(piece['confirmaciones'])
        if set(confirmations) != {'tools', 'arbol_plugin', 'tope'}:
            raise ValueError('invalid confirmations')
        _tool_names(confirmations['tools'])
        for key in ('arbol_plugin', 'tope'):
            if confirmations[key] is not None:
                _registry_text(confirmations[key])
        destinations = piece['destinos']
        if not isinstance(destinations, list) or not destinations or len(destinations) > 16:
            raise ValueError('invalid destinations')
        canonical = 0
        for dest in destinations:
            if set(_object(dest)) != {'runtime', 'ruta', 'canonica', 'hash'} or type(dest['canonica']) is not bool:
                raise ValueError('invalid destination')
            canonical += dest['canonica']
            relative = _registry_text(dest['ruta'], 1024)
            runtime = _registry_text(dest['runtime'])
            signature = _registry_text(dest['hash'])
            if not re.fullmatch(r'sha256:[0-9a-f]{64}', signature):
                raise ValueError('invalid signature')
            parts = relative.replace('\\', '/').split('/')
            if parts[0] not in ('.claude', '.codex', '.opencode', '.agents') or len(parts) < 2 or any(part in ('', '..', '.') for part in parts) or ':' in relative:
                raise ValueError('unconfined destination')
            key = (runtime, '/'.join(parts))
            if key in entries or len(entries) >= MAX_PIECES:
                raise ValueError('duplicate destination or registry limit')
            entries[key] = (signature, piece['origen'])
        if canonical != 1:
            raise ValueError('exactly one canonical destination required')
    return entries


class Inventory:
    def __init__(self, project):
        self.project = project
        self.pieces, self.warnings, self.cache = [], [], {}
        self.read_budget_used = 0
        self.registry, self.registry_status = {}, 'absent'
        self.orphans = []
        self.claude_servers, self.claude_disabled = [], set()
        self.claude_disabled_source = None

    def warn(self, source):
        message = source + ': declaration unavailable, invalid, linked or exceeds limit'
        if message not in self.warnings:
            self.warnings.append(message)

    def read(self, path):
        if path not in self.cache:
            remaining = MAX_TOTAL_BYTES - self.read_budget_used
            if remaining <= 0:
                raise ValueError('total read limit')
            limit = min(MAX_BYTES, remaining - 1)
            self.read_budget_used += limit + 1
            # Failed reads keep their reservation: rejected inputs still cost I/O.
            data = GUARD._read(path, max_bytes=limit, as_bytes=True)
            self.read_budget_used -= limit + 1 - len(data)
            self.cache[path] = data
        return self.cache[path]

    def folder(self, path, source):
        try:
            _safe_path(path)
            if not path.exists():
                return []
            if not path.is_dir():
                raise ValueError('directory required')
            entries = list(itertools.islice(path.iterdir(), MAX_PIECES + 1))
            if len(entries) > MAX_PIECES:
                self.warn(source)
                return []  # Reject the directory, not a filesystem-order-dependent subset.
            return sorted(entries)
        except (OSError, ValueError):
            self.warn(source)
            return []

    def load_registry(self):
        path = self.project / '.claude/pieces.json'
        try:
            _safe_path(path)
            if not path.exists():
                return
            data = _config(self.read(path).decode('utf-8-sig'), '.json')
            entries = _registry_entries(data)
            self.registry, self.registry_status = entries, 'valid'
            for runtime, relative in entries:
                source = 'project/' + relative
                try:
                    destination = self.project / relative
                    _safe_path(destination)
                    if not destination.exists():
                        self.orphans.append({'runtime': runtime, 'source': source})
                        self.warn(source)
                    elif not destination.is_file():
                        self.warn(source)
                except (OSError, ValueError):
                    self.warn(source)
        except (OSError, ValueError, UnicodeError, RecursionError):
            self.registry_status = 'invalid'
            self.warn('project/.claude/pieces.json')

    def add(self, base, scope, path, runtime, kind, metadata, *, locator='', extra=None):
        if len(self.pieces) >= MAX_PIECES:
            self.warn('inventory limit')
            return
        relative = path.relative_to(base).as_posix()
        name = metadata.get('name')
        description = metadata.get('description', '')
        if not isinstance(name, str) or not name.strip() or len(name) > 256 or not isinstance(description, str):
            raise ValueError('invalid public metadata')
        root_id = 'project' if scope == 'project' else 'user-' + hashlib.sha256(os.path.normcase(str(base)).encode()).hexdigest()[:20]
        identity = json.dumps([runtime, scope, root_id, relative, kind, name, locator], ensure_ascii=True)
        ownership = 'unknown' if self.registry_status == 'invalid' else 'unmanaged'
        if scope == 'project' and (runtime, relative) in self.registry:
            signature, origin = self.registry[(runtime, relative)]
            actual = 'sha256:' + hashlib.sha256(self.read(path).replace(b'\r\n', b'\n')).hexdigest()
            ownership = 'managed' if signature == actual and origin == 'generada' else 'modified'
        piece = {'id': 'ext-' + hashlib.sha256(identity.encode()).hexdigest()[:20],
                 'name': _public_text(name), 'description': _public_text(description)[:480],
                 'runtime': runtime, 'kind': kind, 'scope': scope,
                 'root_id': root_id,
                 'source': scope + '/' + relative, 'locator': REDACT(locator),
                 'availability': 'unverified', 'ownership': ownership}
        if 'tools' in metadata:
            piece['declared_tools'] = _tool_names(metadata['tools'])
        if 'permission' in metadata:
            piece['declared_permissions'] = _permission_declarations(metadata['permission'])
        if extra:
            piece.update(extra)
        self.pieces.append(piece)
        return piece

    def files(self, base, scope, relative, runtime, kind, extension='.md'):
        directory = base / relative
        for candidate in self.folder(directory, scope + '/' + relative):
            path = candidate / 'SKILL.md' if kind == 'skill' else candidate
            if kind != 'skill' and path.suffix != extension:
                continue
            source = scope + '/' + path.relative_to(base).as_posix()
            try:
                raw = self.read(path).decode('utf-8-sig')
                extra = {}
                if kind in ('persona','tool-source'):
                    metadata = {'name': path.stem}
                elif extension == '.toml':
                    data = _config(raw, '.toml')
                    if not isinstance(data.get('developer_instructions'), str):
                        raise ValueError('agent instructions required')
                    metadata = {key:data[key] for key in ('name','description') if key in data}
                else:
                    optional = runtime == 'claude-code' and kind in ('skill', 'command')
                    file_named = kind == 'command' or runtime == 'opencode' and kind == 'agent'
                    metadata = {} if optional and raw.partition('\n')[0].rstrip('\r') != '---' else _metadata(raw, ignore_name=file_named)
                    if optional:
                        metadata.setdefault('name', path.parent.name if kind == 'skill' else path.stem)
                    if file_named:
                        metadata['name'] = path.stem
                    if runtime == 'claude-code' and kind == 'skill':
                        extra['invocation_names'] = list(dict.fromkeys(_public_text(name) for name in (metadata['name'], path.parent.name)))
                self.add(base, scope, path, runtime, kind, metadata, extra=extra)
                if extension == '.toml':
                    self.servers(base, scope, path, runtime, data.get('mcp_servers', {}), 'mcp_servers', owner_agent=metadata['name'])
                if runtime == 'claude-code' and kind == 'agent':
                    for name, server, declaration in _agent_servers(raw):
                        self.servers(base, scope, path, runtime, {name: server}, 'mcpServers',
                                     owner_agent=metadata['name'], declaration=declaration)
            except (OSError, ValueError, UnicodeError, RecursionError):
                self.warn(source)

    def servers(self, base, scope, path, runtime, servers, field, owner_agent=None, declaration=None):
        for name, server in _object(servers).items():
            _object(server)
            extra = _server_metadata(server, runtime, declaration)
            if owner_agent:
                extra['owner_agent'] = owner_agent
            if declaration:
                extra['declaration'] = declaration
            piece = self.add(base, scope, path, runtime, 'mcp', {'name': name}, locator=field + '.' + name, extra=extra)
            if extra.get('definition_status') == 'invalid':
                self.warn(scope + '/' + path.relative_to(base).as_posix() + '#' + field)
            if piece is not None and runtime == 'claude-code' and owner_agent is None:
                self.claude_servers.append((name, piece))

    def codex_roles(self, base, scope, path, roles):
        for name, role in _object(roles).items():
            if not isinstance(role, dict):
                continue  # Scalar keys in [agents] configure the runtime, not a role.
            extra = {}
            reference = role.get('config_file')
            if reference is not None:
                if not isinstance(reference, str) or Path(reference).is_absolute() or '..' in reference.replace('\\','/').split('/'):
                    raise ValueError('unconfined config reference')
                definition = _absolute(path.parent / reference)
                relative = definition.relative_to(base).as_posix()
                _config(self.read(definition).decode('utf-8-sig'), '.toml')
                extra['definition_source'] = scope + '/' + relative
            self.add(base, scope, path, 'codex', 'agent',
                     {'name':name,'description':role.get('description','')}, locator='agents.' + name, extra=extra)

    def config(self, base, scope, relative, runtime):
        path = base / relative
        source = scope + '/' + relative
        try:
            _safe_path(path)
            if not path.exists():
                return
            data = _config(self.read(path).decode('utf-8-sig'), path.suffix)
            field = 'mcp_servers' if runtime == 'codex' else 'mcp' if runtime == 'opencode' else 'mcpServers'
            self.servers(base, scope, path, runtime, data.get(field, {}), field)
            if runtime == 'codex':
                self.codex_roles(base, scope, path, data.get('agents', {}))
            if runtime == 'opencode':
                for field, kind in (('agent','agent'),('command','command')):
                    for name, definition in _object(data.get(field, {})).items():
                        _object(definition)
                        metadata = {'name':name,'description':definition.get('description','')}
                        if 'tools' in definition:
                            metadata['tools'] = definition['tools']
                        if 'permission' in definition:
                            metadata['permission'] = definition['permission']
                        self.add(base, scope, path, runtime, kind, metadata, locator=field + '.' + name)
            if runtime == 'claude-code' and scope == 'user':
                projects = _object(data.get('projects', {}))
                local = next((value for key,value in projects.items() if isinstance(key,str) and Path(key).is_absolute() and _absolute(key) == self.project), {})
                self.servers(base, 'local', path, runtime, _object(local).get('mcpServers',{}), 'projects.current.mcpServers')
                disabled = local.get('disabledMcpServers', [])
                if not isinstance(disabled, list) or len(disabled) > MAX_PIECES:
                    raise ValueError('invalid disabled server declarations')
                names = {_registry_text(name) for name in disabled}
                self.claude_disabled = names
                self.claude_disabled_source = source + '#projects.current.disabledMcpServers'
        except (OSError, ValueError, UnicodeError, RecursionError):
            self.warn(source)

    def scan(self, base, scope, runtime, config_root=None):
        prefix = '.claude' if runtime == 'claude-code' else '.codex' if runtime == 'codex' else '.opencode' if scope == 'project' else '.config/opencode'
        prefix = prefix if config_root is None else config_root
        stem = prefix + '/' if prefix else ''
        self.files(base, scope, stem + 'agents', runtime, 'agent', '.toml' if runtime == 'codex' else '.md')
        skills = ('.agents/skills',) if runtime == 'codex' else (stem + 'skills',) if runtime == 'claude-code' else (stem + 'skills','.claude/skills','.agents/skills')
        for folder in skills:
            self.files(base, scope, folder, runtime, 'skill')
        self.files(base, scope, '.claude/personas', runtime, 'persona')
        if runtime == 'opencode':
            self.files(base, scope, stem + 'commands', runtime, 'command')
            for suffix in ('.js','.ts'):
                self.files(base, scope, stem + 'tools', runtime, 'tool-source', suffix)
            for suffix in ('.json','.jsonc'):
                self.config(base, scope, ('opencode' if scope == 'project' else stem + 'opencode') + suffix, runtime)
        elif runtime == 'codex':
            self.config(base, scope, stem + 'config.toml', runtime)
        else:
            self.files(base, scope, stem + 'commands', runtime, 'command')
            self.config(base, scope, '.mcp.json' if scope == 'project' else '.claude.json', runtime)

    def result(self):
        for name, piece in self.claude_servers:
            if name in self.claude_disabled:
                piece['enabled'] = False
                piece['enabled_source'] = self.claude_disabled_source
        groups = {}
        for piece in self.pieces:
            kind = 'invocable' if piece['runtime'] == 'claude-code' and piece['kind'] in ('skill', 'command') else piece['kind']
            for name in piece.get('invocation_names', [piece['name']]):
                key = (piece['runtime'],kind,name)
                groups.setdefault(key, []).append(piece['id'])
        conflicts = [{'runtime':key[0],'kind':key[1],'name':key[2], 'ids': sorted(ids),
                      'resolution':'runtime-dependent; explicit selection required'}
                     for key,ids in sorted(groups.items()) if len(ids) > 1]
        bundled = self.bundled_names()
        for key, ids in sorted(groups.items()):
            kinds = ('skill', 'command') if key[1] == 'invocable' else (key[1],)
            for kind in kinds:
                if (kind, key[2]) in bundled:
                    conflicts.append({'runtime': key[0], 'kind': key[1], 'name': key[2],
                                      'ids': sorted(ids), 'bundled_source': bundled[(kind, key[2])],
                                      'resolution': 'qualified extension reference required; cycle roles unchanged'})
        return _redact({'version':1, 'evidence':'local declarations; session availability not measured',
                        'pieces': sorted(self.pieces, key=lambda x:(x['runtime'],x['kind'],x['name'],x['id'])),
                        'conflicts':conflicts, 'warnings':sorted(self.warnings),
                        'orphans': sorted(self.orphans, key=lambda x: (x['runtime'], x['source'])),
                        'partial': bool(self.warnings), 'registry_status':self.registry_status})

    def bundled_names(self):
        names = {}
        for kind, folder in (('agent', 'agents'), ('skill', 'skills'), ('command', 'commands')):
            for entry in self.folder(GUARD.BUNDLE / folder, 'bundle/' + folder):
                path = entry / 'SKILL.md' if kind == 'skill' else entry
                try:
                    _safe_path(path)
                    if path.is_file() and path.suffix == '.md':
                        name = entry.name if kind == 'skill' else entry.stem
                        names[(kind, name)] = path.relative_to(GUARD.BUNDLE).as_posix()
                except (OSError, ValueError):
                    self.warn('bundle/' + folder)
        return names


def select_pieces(inventory, identifiers, *, runtime='all'):
    """Resolve explicit IDs against a fresh discovery result; never invoke a piece."""
    if runtime not in (*RUNTIMES, 'all'):
        raise ValueError('unknown selection runtime')
    if not isinstance(identifiers, list) or len(identifiers) > MAX_SELECTED or any(not isinstance(value, str) or not re.fullmatch(r'ext-[0-9a-f]{20}', value) for value in identifiers):
        raise ValueError('invalid or excessive selected identities')
    index = {piece['id']: piece for piece in inventory['pieces']}
    selected, warnings = [], list(inventory['warnings'])
    for identity in sorted(set(identifiers)):
        piece = index.get(identity)
        if piece is None or runtime != 'all' and piece['runtime'] != runtime:
            warnings.append('selected extension not discovered for this runtime: ' + identity)
        else:
            selected.append(piece)
    chosen = {piece['id'] for piece in selected}
    conflicts = [item for item in inventory['conflicts'] if chosen.intersection(item['ids'])]
    if conflicts:
        warnings.append('selected extension name conflict; use qualified sources and verify session availability')
    return _redact({'version': 1, 'selection_only': True, 'selected': selected,
                    'conflicts': conflicts, 'warnings': sorted(set(warnings)),
                    'partial': bool(warnings), 'evidence': inventory['evidence']})


def discover(project, *, home=None, cwd=None, runtime='all', include_user=True, user_roots=None):
    if GUARD is None or REDACT is None:
        raise ValueError('bundled readers unavailable')
    project = _absolute(project)
    cwd = _absolute(cwd or project)
    home = _absolute(home or Path.home())
    _safe_path(project)
    _safe_path(cwd)
    if not project.is_dir() or not cwd.is_dir():
        raise ValueError('project directory unavailable')
    cwd.relative_to(project)
    runtimes = RUNTIMES if runtime == 'all' else (runtime,)
    if set(runtimes) - set(RUNTIMES):
        raise ValueError('unknown runtime')
    user_roots = {} if user_roots is None else _object(user_roots)
    if set(user_roots) - set(RUNTIMES):
        raise ValueError('unknown runtime user root')
    inventory = Inventory(project)
    inventory.load_registry()
    chain, current = [], cwd
    while True:
        chain.append(current)
        if current == project:
            break
        current = current.parent
    for runtime_id in runtimes:
        for directory in reversed(chain):
            # Sources are relative to project even for a nested runtime directory.
            relative = directory.relative_to(project).as_posix()
            prefix = (relative + '/' if relative != '.' else '') + ('.claude' if runtime_id == 'claude-code' else '.codex' if runtime_id == 'codex' else '.opencode')
            if directory == project:
                inventory.scan(project, 'project', runtime_id)
            else:
                folder = prefix + '/skills' if runtime_id == 'claude-code' else relative + '/.agents/skills'
                inventory.files(project, 'project', folder, runtime_id, 'skill')
                if runtime_id == 'opencode':
                    for folder in (prefix + '/skills',relative + '/.claude/skills'):
                        inventory.files(project, 'project', folder, runtime_id, 'skill')
        if include_user:
            if runtime_id in user_roots:
                inventory.scan(_absolute(user_roots[runtime_id]), 'user', runtime_id, config_root='')
                if runtime_id == 'codex':
                    inventory.files(home, 'user', '.agents/skills', runtime_id, 'skill')
            else:
                inventory.scan(home, 'user', runtime_id)
    return inventory.result()


def parse_user_roots(declarations):
    roots = {}
    for declaration in declarations:
        key, separator, value = declaration.partition('=')
        if not separator or key in roots or not value or key not in RUNTIMES:
            raise ValueError('invalid root declaration')
        roots[key] = value
    return roots


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', default='.')
    parser.add_argument('--cwd')
    parser.add_argument('--home')
    parser.add_argument('--runtime', choices=(*RUNTIMES,'all'), default='all')
    parser.add_argument('--project-only', action='store_true')
    parser.add_argument('--user-root', action='append', default=[], metavar='RUNTIME=PATH')
    parser.add_argument('--json', action='store_true')
    parser.add_argument('--select', action='append', default=None, metavar='ID')
    args = parser.parse_args(argv)
    try:
        roots = parse_user_roots(args.user_root)
        result = discover(args.project, home=args.home, cwd=args.cwd, runtime=args.runtime,
                          include_user=not args.project_only, user_roots=roots)
        if args.select is not None:
            result = select_pieces(result, args.select, runtime=args.runtime)
        if args.json:
            print(json.dumps(result, ensure_ascii=False))
        else:
            for piece in result.get('selected', result.get('pieces', [])):
                print(f"{piece['id']} {piece['runtime']} {piece['kind']} {piece['name']} [{piece['scope']}; {piece['availability']}] {piece['source']}")
            for warning in result['warnings']:
                print('warning: ' + warning)
        return 0
    except (OSError, ValueError, UnicodeError, RecursionError):
        print('project components unavailable: check selected roots and bundled readers', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
