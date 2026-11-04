#!/usr/bin/env python3
"""Source footprint estimates, not runtime usage or billed tokens."""
import argparse
import importlib.util
import json
from pathlib import Path
import stat
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
MAX_FILES = 256
MAX_TOTAL = 8 * 1024 * 1024
MAX_BASELINE = 512 * 1024


def helper():
    spec = importlib.util.spec_from_file_location('footprint_sources', HERE / 'source-snapshot.py')
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


def discover(project, api):
    reader = api.module('local-read.py')
    paths, issues = [], []
    for folder in ('agents', 'commands', 'skills'):
        listing = reader.list_names(project, folder, max_entries=MAX_FILES)
        if not listing['complete']:
            issues.append(folder + ':' + listing['status'])
        for name in listing.get('names', []):
            if name.startswith('.'):
                continue
            if folder == 'skills':
                entry = Path(project) / folder / name
                try:
                    info = entry.lstat()
                except OSError:
                    issues.append(folder + '/' + name + ':unavailable')
                    continue
                if reader._redirected(info):
                    issues.append(folder + '/' + name + ':redirected_path')
                    continue
                if not stat.S_ISDIR(info.st_mode):
                    continue
                paths.append(folder + '/' + name + '/SKILL.md')
            elif name.endswith('.md'):
                paths.append(folder + '/' + name)
    return paths, issues


def comparison(current, baseline):
    unavailable = {'comparable': False, 'reduction_percent': None, 'delta_characters': None}
    if (not isinstance(baseline, dict) or type(baseline.get('schema_version')) is not int or baseline.get('schema_version') != 1
            or baseline.get('kind') != 'source_footprint' or baseline.get('method') != 'characters/4'
            or baseline.get('normalization') != 'utf8-lf' or baseline.get('complete') is not True
            or not current['complete'] or not isinstance(baseline.get('files'), list)):
        return dict(unavailable, reason='incomplete_or_invalid_baseline')
    rows = baseline['files']
    if not 0 < len(rows) <= MAX_FILES:
        return dict(unavailable, reason='invalid_baseline')
    sources = helper()
    for row in rows:
        if (not isinstance(row, dict) or not sources.valid_path(row.get('path'))
                or type(row.get('characters')) is not int or not 0 <= row['characters'] <= sources.MAX_FILE):
            return dict(unavailable, reason='invalid_baseline')
    old = {r['path']: r for r in rows}
    new = {r['path']: r for r in current['files']}
    if len(old) != len(rows) or set(old) != set(new):
        return dict(unavailable, reason='different_path_set', added=sorted(set(new) - set(old)), removed=sorted(set(old) - set(new)))
    before = sum(r['characters'] for r in rows)
    after = sum(r['characters'] for r in current['files'])
    return {'comparable': True, 'before_characters': before, 'after_characters': after,
            'delta_characters': after - before,
            'reduction_percent': round((before - after) * 100 / before, 2) if before else None}


def report(project, paths=None, baseline=None):
    value = {'schema_version': 1, 'kind': 'source_footprint', 'method': 'characters/4',
             'normalization': 'utf8-lf', 'status': 'unavailable', 'complete': False,
             'native_observation': None, 'billed_tokens': None, 'files': [], 'issues': []}
    try:
        api = helper()
        if paths is None:
            paths, value['issues'] = discover(project, api)
        _, observed, issues = api.collect(project, paths, maximum=MAX_FILES, total=MAX_TOTAL)
        value['issues'].extend(issues)
        for row in observed:
            try:
                text = row['data'].decode('utf-8-sig').replace('\r\n', '\n').replace('\r', '\n')
            except UnicodeError:
                value['issues'].append({'path': row['path'], 'status': 'invalid_utf8'})
                continue
            size = len(text)
            value['files'].append({'path': row['path'], 'sha256': row['sha256'], 'bytes': row['bytes'],
                'characters': size, 'lines': len(text.splitlines()), 'estimated_tokens': size / 4,
                'scope': 'reference' if 'references' in row['path'].split('/')[:-1] else 'entry'})
        value['complete'] = not value['issues']
        value['status'] = 'ok' if value['complete'] else 'incomplete'
    except (OSError, ValueError, TypeError, ImportError, AttributeError, api.Invalid if 'api' in locals() else ValueError):
        value['issues'].append({'status': 'unavailable'})
    rows = value['files']
    value['totals'] = {'characters': sum(r['characters'] for r in rows), 'bytes': sum(r['bytes'] for r in rows),
        'entry_characters': sum(r['characters'] for r in rows if r['scope'] == 'entry'),
        'reference_characters': sum(r['characters'] for r in rows if r['scope'] == 'reference')}
    value['comparison'] = comparison(value, baseline) if baseline is not None else None
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', default='.')
    parser.add_argument('--file', action='append')
    parser.add_argument('--baseline', help='Project-relative source footprint JSON')
    args = parser.parse_args(argv)
    baseline = None
    try:
        api = helper()
        if args.baseline:
            if not api.valid_path(args.baseline):
                raise ValueError('unsafe baseline')
            row = api.module('local-read.py').read_bytes(args.project, args.baseline, max_bytes=MAX_BASELINE)
            if row['status'] != 'ok':
                raise ValueError('baseline unavailable')
            baseline = json.loads(row['data'].decode('utf-8-sig'), object_pairs_hook=api.unique)
            if not isinstance(baseline, dict):
                raise ValueError('invalid baseline')
        value = report(args.project, args.file, baseline)
        output = api.module('redact.py').redactar(json.dumps(value, ensure_ascii=False))
    except (OSError, ValueError, TypeError, ImportError, AttributeError, RecursionError):
        print(json.dumps({'status': 'unavailable', 'complete': False}))
        return 2
    print(output)
    return 0 if value['complete'] and (value['comparison'] is None or value['comparison']['comparable']) else 1


if __name__ == '__main__':
    raise SystemExit(main())
