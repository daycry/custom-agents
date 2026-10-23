#!/usr/bin/env python3
"""Select bundled guidance from bounded local manifests, without executing project code."""
import argparse
import importlib.util
import json
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

MAX_BYTES = 128 * 1024
MAX_DEPTH = 32
BUNDLE = Path(__file__).resolve().parents[2]
CATALOG = Path(__file__).with_name('capability-catalog.json')
ROLES = ('analyst', 'evaluator', 'architect', 'planner', 'implementer', 'reviewer', 'qa', 'documenter', 'knowledge-curator', 'nemesis')
STACKS = ('codeigniter4', 'php', 'python', 'react')
AREAS = ('research', 'api', 'data', 'frontend', 'accessibility', 'performance', 'delivery', 'mcp', 'security', 'testing', 'memory', 'catalog', 'evaluation', 'dependencies', 'documentation')
PHASE_ROLES = {'analysis': 'analyst', 'estimate': 'evaluator', 'design': 'architect', 'plan': 'planner', 'implement': 'implementer', 'review': 'reviewer', 'test': 'qa', 'document': 'documenter', 'curate': 'knowledge-curator', 'security': 'nemesis'}


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


def _read(path, max_bytes=MAX_BYTES, *, as_bytes=False):
    if any(_linked(parent) for parent in (path, *path.parents)):
        raise ValueError('linked path')
    with path.open('rb') as handle:
        data = handle.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise ValueError('manifest exceeds limit')
    return data if as_bytes else data.decode('utf-8-sig')


def _object(value):
    if not isinstance(value, dict):
        raise ValueError('expected object')
    return value


def _bounded(value):
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        if depth > MAX_DEPTH:
            raise ValueError('manifest exceeds nesting limit')
        children = item.values() if isinstance(item, dict) else item if isinstance(item, list) else ()
        pending.extend((child, depth + 1) for child in children)
    return value


def detect(project):
    project = Path(project).absolute()
    if not project.is_dir() or any(_linked(p) for p in (project, *project.parents)):
        raise ValueError('project directory unavailable or linked')
    stacks, sources, warnings = set(), [], []
    for filename in ('composer.json', 'package.json', 'pyproject.toml'):
        path = project / filename
        if not path.exists() and not _linked(path):
            continue
        try:
            raw = _read(path)
            if filename.endswith('.toml') and tomllib is None:
                raise ValueError('optional TOML parser unavailable')
            data = _object(_bounded(tomllib.loads(raw) if filename.endswith('.toml') else json.loads(raw)))
            dependencies = {}
            for field in ('require', 'require-dev') if filename == 'composer.json' else ('dependencies', 'devDependencies'):
                dependencies.update(_object(data.get(field, {})))
            if filename == 'composer.json':
                stacks.add('php')
                if 'codeigniter4/framework' in dependencies:
                    stacks.add('codeigniter4')
            elif filename == 'package.json':
                if 'react' in dependencies:
                    stacks.add('react')
            else:
                stacks.add('python')
            sources.append(filename)
        except (OSError, ValueError, UnicodeError, RecursionError):
            warnings.append(f'{filename}: manifest unavailable, invalid or exceeds limit')
    return {'stacks': sorted(stacks), 'sources': sources, 'warnings': warnings}


def load_catalog():
    return _bounded(json.loads(_read(CATALOG)))


def validate_catalog(data, bundle=None):
    errors = []
    if not isinstance(data, dict) or set(data) != {'version', 'capabilities'} or type(data.get('version')) is not int or data['version'] != 1:
        return ['catalog: invalid schema/version']
    entries = data['capabilities']
    if not isinstance(entries, list) or len(entries) > 100:
        return ['catalog: capabilities must be a bounded list']
    seen = set()
    for index, entry in enumerate(entries):
        prefix = f'capability {index + 1}'
        if not isinstance(entry, dict) or set(entry) != {'id', 'roles', 'stacks', 'areas'}:
            errors.append(f'{prefix}: invalid fields')
            continue
        name = entry['id']
        if not isinstance(name, str) or not re.fullmatch(r'[a-z][a-z0-9]*(?:-[a-z0-9]+)*', name):
            errors.append(f'{prefix}: invalid id')
            continue
        if name in seen:
            errors.append(f'{prefix}: duplicate id')
        seen.add(name)
        for field, allowed in (('roles', ROLES), ('stacks', STACKS), ('areas', AREAS)):
            values = entry[field]
            if not isinstance(values, list) or any(not isinstance(v, str) or v not in allowed for v in values) or len(set(values)) != len(values):
                errors.append(f'{prefix}: invalid {field}')
            elif field == 'roles' and not values:
                errors.append(f'{prefix}: empty roles')
        try:
            base = Path(bundle) if bundle is not None else BUNDLE
            _read(base / 'skills' / name / 'SKILL.md')
        except (OSError, ValueError, UnicodeError):
            errors.append(f'{prefix}: skill unavailable or linked')
    return errors


def select(catalog, role, stacks, areas):
    if role not in ROLES or set(stacks) - set(STACKS) or set(areas) - set(AREAS):
        raise ValueError('invalid selection filters')
    selected = []
    for entry in catalog['capabilities']:
        matching_stacks = sorted(set(entry['stacks']) & set(stacks))
        matching_areas = sorted(set(entry['areas']) & set(areas))
        if role in entry['roles'] and (matching_stacks or matching_areas):
            selected.append({'id': entry['id'], 'source': f"skills/{entry['id']}/SKILL.md", 'stacks': matching_stacks, 'areas': matching_areas})
    return sorted(selected, key=lambda entry: entry['id'])


def _redact(text):
    path = Path(__file__).with_name('redact.py')
    if not path.is_file() or _linked(path):
        raise ValueError('bundled redactor unavailable')
    spec = importlib.util.spec_from_file_location('capability_redactor', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.redactar(text)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', default='.')
    parser.add_argument('--role', choices=ROLES)
    parser.add_argument('--phase', choices=tuple(PHASE_ROLES))
    parser.add_argument('--stack', choices=STACKS, action='append', default=[])
    parser.add_argument('--area', choices=AREAS, action='append', default=[])
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    try:
        catalog = load_catalog()
        errors = validate_catalog(catalog)
        if errors:
            raise ValueError('; '.join(errors))
        if args.check:
            print(_redact(json.dumps({'valid': True, 'capabilities': len(catalog['capabilities'])}) if args.json else f"capabilities: {len(catalog['capabilities'])}; catalog valid"))
            return 0
        role = args.role or PHASE_ROLES.get(args.phase, 'implementer')
        if args.phase and PHASE_ROLES[args.phase] != role:
            raise ValueError('phase and role disagree')
        detected = detect(args.project)
        stacks = sorted(set(detected['stacks']) | set(args.stack))
        result = {'version': 1, 'role': role, 'phase': args.phase, 'stacks': stacks, 'explicit_stacks': sorted(set(args.stack)), 'areas': sorted(set(args.area)), 'sources': detected['sources'], 'warnings': detected['warnings'], 'selection_only': True, 'capabilities': select(catalog, role, stacks, args.area)}
        if args.json:
            rendered = json.dumps(result, ensure_ascii=False)
        else:
            lines = [f"role: {role}; stacks: {', '.join(stacks) or 'undetected'}; selection only"]
            lines += [f"- {entry['id']}: {entry['source']}" for entry in result['capabilities']]
            lines += [f'warning: {warning}' for warning in result['warnings']]
            rendered = '\n'.join(lines)
        print(_redact(rendered))
        return 0
    except (OSError, ValueError, UnicodeError, RecursionError):
        # Never echo untrusted manifest content or absolute paths through exceptions.
        print('capabilities unavailable: check the bundled catalog, redactor and local manifests', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
