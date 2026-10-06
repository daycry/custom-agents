#!/usr/bin/env python3
"""Read public plugin definitions and build a local capability panel."""
import argparse
import html
import importlib.util
import json
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
TEMPLATE = Path(__file__).resolve().parents[1] / 'references/panel.html'


def _load_redactor():
    # Only trusted bundled code; --root is data and cannot select imported code.
    path = Path(__file__).resolve().parents[3] / 'agent-kits/shared/redact.py'
    if not path.is_file():
        return None
    spec = importlib.util.spec_from_file_location('panel_redactor', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.redactar


REDACTOR = _load_redactor()


def _redact_values(value):
    if isinstance(value, str):
        return REDACTOR(value)
    if isinstance(value, list):
        return [_redact_values(item) for item in value]
    if isinstance(value, dict):
        return {key: _redact_values(item) for key, item in value.items()}
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


def _hook_metadata(root, hook, group, metadata):
    launcher = '${CLAUDE_PLUGIN_ROOT}/hooks/run-hook.mjs'
    script = None
    arguments = hook.get('args')
    if hook.get('command') == 'node' and isinstance(arguments, list) and len(arguments) == 2 and arguments[0] == launcher:
        script = arguments[1]
    elif isinstance(hook.get('command'), str):
        match = re.fullmatch(r'node "\$\{CLAUDE_PLUGIN_ROOT\}/hooks/run-hook\.mjs" ([a-z][a-z0-9-]{0,63}\.sh)', hook['command'])
        if match:
            script = match.group(1)
    if not isinstance(script, str) or not re.fullmatch(r'[a-z][a-z0-9-]{0,63}\.sh', script):
        return {}
    if script not in metadata:
        fields = {'title': script, 'description': 'Descripción pública no disponible en esta instantánea.'}
        try:
            for line in _read(root, root / 'hooks' / script).splitlines()[:8]:
                for key in ('title', 'description'):
                    prefix = '# panel-' + key + ': '
                    if line.startswith(prefix):
                        fields[key] = REDACTOR(line[len(prefix):])[:300]
        except (OSError, ValueError, UnicodeError):
            pass
        metadata[script] = fields
    matcher = group.get('matcher')
    return {'handler': script, **metadata[script],
            'matcher': REDACTOR(matcher)[:160] if isinstance(matcher, str) else ''}


def _hooks(root, warnings):
    path = root / 'hooks/hooks.json'
    if not path.exists():
        return []
    try:
        events = json.loads(_read(root, path)).get('hooks', {})
        if not isinstance(events, dict):
            raise ValueError('invalid events')
        result, metadata = [], {}
        for event in sorted(events):
            for group in events[event]:
                for hook in group.get('hooks', []):
                    timeout = hook.get('timeout')
                    result.append({'event': event, 'timeout': timeout if isinstance(timeout, (int, float)) else None, 'scope': 'global', **_hook_metadata(root, hook, group, metadata)})
        return result
    except (OSError, UnicodeError, ValueError, TypeError, AttributeError):
        warnings.append('hooks/hooks.json: inventory unavailable')
        return []


def _presence(root, relative):
    path = root / relative
    try:
        _guard_path(root, path)
        return 'present' if path.exists() else 'absent'
    except (OSError, ValueError):
        return 'unavailable'


def build_inventory(root):
    if REDACTOR is None:
        raise ValueError('bundled redactor unavailable')
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError('bundle root unavailable')
    data = {'schema_version': 1, 'evidence': 'file_inventory; runtime execution not measured', 'warnings': []}
    for kind in ('agents', 'skills', 'commands'):
        data[kind] = _catalog(root, kind, data['warnings'])
    data['tools'] = sorted({tool for entry in data['agents'] for tool in entry['tools']})
    data['hooks'] = _hooks(root, data['warnings'])
    data['counts'] = {kind: len(data[kind]) for kind in ('agents', 'skills', 'commands', 'tools', 'hooks')}
    data['runtimes'] = {runtime: _presence(root, relative) for runtime, relative in {'claude': 'hooks/hooks.json', 'codex': 'interop/codex/hooks.json', 'opencode': 'interop/opencode/plugins/custom-agents-hooks.js'}.items()}
    data['memory'] = {'approved_directory': _presence(root, 'docs/knowledge/approved'), 'graphify_artifact': _presence(root, 'graphify-out/graph.json')}
    data['workflow'] = _workflow(root, data['warnings'])
    return _redact_values(data)


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
        grouped.setdefault(hook['event'], []).append(hook)
    for event, hooks in grouped.items():
        handlers = ''.join(
            '<li><strong>' + html.escape(hook.get('title', f'Acción {index}')) + '</strong>'
            + ('<p>' + html.escape(hook['description']) + '</p><code>' + html.escape(hook['handler']) + '</code><span class="hook-meta">Activación: '
               + html.escape(hook['matcher'].replace('|', ' · ') or 'Cada ocurrencia del evento') + '</span>' if 'handler' in hook else '<p>Función pública no identificada en esta definición.</p>')
            + ('<span class="hook-meta"> · Timeout: ' + html.escape(str(hook['timeout'])) + ' s</span>' if hook['timeout'] is not None else '') + '</li>'
            for index, hook in enumerate(hooks, 1)
        )
        cards.append(f'<article data-kind="hooks" class="card"><small>EVENTO DE HOOK</small><h2>{html.escape(event)}</h2><p>{len(hooks)} acciones configuradas. Su ejecución no se mide en este panel.</p><ul class="hook-handlers">{handlers}</ul></article>')
    return '\n'.join(cards)


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


def render_html(data):
    counts = {**data['counts'], 'hooks': len({hook['event'] for hook in data['hooks']})}
    labels = {'agents': 'Agentes', 'skills': 'Skills', 'commands': 'Comandos', 'tools': 'Herramientas', 'hooks': 'Eventos de hook'}
    stats = ''.join(f'<div class="stat"><strong>{count}</strong><span>{labels[kind]}</span></div>' for kind, count in counts.items())
    notes = html.escape(json.dumps({'runtimes': data['runtimes'], 'memory': data['memory'], 'warnings': data['warnings']}, ensure_ascii=False, indent=2))
    try:
        template = _read(TEMPLATE.parent, TEMPLATE)
    except (OSError, UnicodeError, ValueError):
        raise ValueError('bundled panel template unavailable') from None
    values = {'STATS': stats, 'CARDS': _cards(data), 'WORKFLOW': _workflow_html(data), 'NOTES': notes, 'FLOW': _flow_html(data)}
    return MARKER + re.sub(r'@@(STATS|CARDS|WORKFLOW|NOTES|FLOW)@@', lambda match: values[match.group(1)], template)



def _write_html(path, text):
    path = Path(path)
    if _unsafe_link(path) or any(_unsafe_link(parent) for parent in path.absolute().parents):
        raise ValueError('output is a symbolic link')
    if path.exists():
        with path.open(encoding='utf8') as handle:
            if handle.read(len(MARKER)) != MARKER:
                raise ValueError('output was not created by plugin-panel')
    descriptor, temporary = tempfile.mkstemp(prefix='.plugin-panel-', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf8', newline='\n') as handle:
            handle.write(text)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default=str(Path(__file__).resolve().parents[3]))
    parser.add_argument('--html')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    try:
        data = build_inventory(args.root)
        if args.html:
            _write_html(args.html, render_html(data))
        if args.json or not args.html:
            print(json.dumps(data, ensure_ascii=False, indent=2))
        return 0
    except (OSError, UnicodeError, ValueError) as error:
        print(f'plugin-panel: {error}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
