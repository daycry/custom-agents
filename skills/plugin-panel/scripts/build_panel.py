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


def _unsafe_link(path):
    try:
        info = path.lstat()
        return path.is_symlink() or bool(getattr(info, 'st_file_attributes', 0) & 0x400)
    except FileNotFoundError:
        return False


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


def _hooks(root, warnings):
    path = root / 'hooks/hooks.json'
    if not path.exists():
        return []
    try:
        events = json.loads(_read(root, path)).get('hooks', {})
        if not isinstance(events, dict):
            raise ValueError('invalid events')
        result = []
        for event in sorted(events):
            for group in events[event]:
                for hook in group.get('hooks', []):
                    timeout = hook.get('timeout')
                    result.append({'event': event, 'timeout': timeout if isinstance(timeout, (int, float)) else None, 'scope': 'global'})
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
    return _redact_values(data)


def _cards(data):
    cards = []
    for kind in ('agents', 'skills', 'commands'):
        for entry in data[kind]:
            esc = lambda value: html.escape(str(value), quote=True)
            detail = esc(entry['model'] or ', '.join(entry['tools']))
            cards.append(f'<article data-kind="{kind}" class="card"><small>{kind} · {detail}</small><h2>{esc(entry["name"])}</h2><p>{esc(entry["description"])}</p><code>{esc(entry["source"])}</code></article>')
    for tool in data['tools']:
        cards.append(f'<article data-kind="tools" class="card"><small>DECLARED TOOL</small><h2>{html.escape(tool)}</h2><p>Availability depends on the current runtime.</p></article>')
    for hook in data['hooks']:
        cards.append(f'<article data-kind="hooks" class="card"><small>GLOBAL HOOK</small><h2>{html.escape(hook["event"])}</h2><p>Timeout: {html.escape(str(hook["timeout"]))} s. Definition only; execution not measured.</p></article>')
    return '\n'.join(cards)


def render_html(data):
    stats = ''.join(f'<div class="stat"><strong>{count}</strong><span>{kind}</span></div>' for kind, count in data['counts'].items())
    notes = html.escape(json.dumps({'runtimes': data['runtimes'], 'memory': data['memory'], 'warnings': data['warnings']}, ensure_ascii=False, indent=2))
    return MARKER + '''
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'">
<title>Custom Agents · Control panel</title><style>
:root{color-scheme:dark;font-family:system-ui,sans-serif;background:#0b1120;color:#e7edf7}*{box-sizing:border-box}body{margin:0}main{max-width:1280px;margin:auto;padding:48px 28px}.tag{color:#62d4bf;font-size:12px;letter-spacing:.18em;text-transform:uppercase}h1{font-size:clamp(32px,5vw,50px);letter-spacing:-.04em;margin:12px 0}header p{max-width:760px;color:#94a3b8;line-height:1.6}.stats{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:28px 0}.stat,.card{background:#121c2e;border:1px solid #26344b;border-radius:14px}.stat{padding:18px}.stat strong{display:block;font-size:30px}.stat span,small{color:#8b9fb9;font-size:12px}.controls{display:flex;gap:12px;margin-bottom:24px}input,select{padding:14px 18px;border:1px solid #31435e;border-radius:10px;background:#121c2e;color:#e7edf7;font:inherit}input{flex:1;min-width:0}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}.card{padding:22px;overflow-wrap:anywhere}.card h2{font-size:19px;margin:14px 0}.card p{color:#aebdd0;line-height:1.55;font-size:14px}.card code{font-size:11px;color:#6ed7c6}details{margin-top:28px;padding:20px;border:1px solid #26344b;border-radius:12px}pre{white-space:pre-wrap;font-size:12px;color:#aebdd0}footer{font-size:12px;color:#8b9fb9;margin-top:32px}@media(max-width:640px){main{padding:28px 16px}.stats{grid-template-columns:repeat(3,1fr)}.controls{flex-direction:column}}
</style></head><body><main><header><div class="tag">Custom Agents / Local capabilities</div><h1>Your plugin, at a glance.</h1><p>Explore agents, skills, commands, declared tools and global hooks. This snapshot reads public definitions. It does not run hooks, change settings or establish service health.</p></header><section class="stats">''' + stats + '''</section>
<div class="controls"><input id="search" type="search" placeholder="Search capabilities…" aria-label="Search capabilities"><select id="kind" aria-label="Capability type"><option value="all">All capabilities</option><option>agents</option><option>skills</option><option>commands</option><option>tools</option><option>hooks</option></select></div><p id="results" aria-live="polite"></p><section class="grid">''' + _cards(data) + '''</section><details><summary>Runtime and memory source presence</summary><pre>''' + notes + '''</pre></details><footer>Static local snapshot · Rebuild to refresh · Agent guards live in agent definitions. Workflow orchestration lives in commands; initiative progress lives in the roadmap dashboard.</footer></main><script>
const search=document.getElementById('search'),kind=document.getElementById('kind'),cards=[...document.querySelectorAll('.card')];function filter(){let count=0;const query=search.value.toLocaleLowerCase();for(const card of cards){const visible=(kind.value==='all'||card.dataset.kind===kind.value)&&card.textContent.toLocaleLowerCase().includes(query);card.hidden=!visible;if(visible)count++;}document.getElementById('results').textContent=count+' capabilities shown';}search.addEventListener('input',filter);kind.addEventListener('change',filter);filter();
</script></body></html>'''


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
