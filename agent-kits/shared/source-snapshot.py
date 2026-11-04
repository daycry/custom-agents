#!/usr/bin/env python3
"""Bounded source receipts for navigation reuse; never a quality verdict."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import stat
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
MAX_FILES = 32
MAX_FILE = 256 * 1024
MAX_TOTAL = 1024 * 1024
MAX_RECEIPT = 64 * 1024
_MODULES = {}
_SHA = re.compile('[a-f0-9]{64}')


class Invalid(Exception):
    pass


def module(name):
    if name not in _MODULES:
        spec = importlib.util.spec_from_file_location('source_receipt_' + name.replace('-', '_'), HERE / name)
        loaded = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(loaded)
        _MODULES[name] = loaded
    return _MODULES[name]


def result(status, complete=False, **fields):
    return dict(schema_version=1, status=status, complete=complete, **fields)


def valid_path(path):
    if (not isinstance(path, str) or not path or len(path) > 1024 or path != path.strip()
            or path.startswith('/') or '\\' in path or ':' in path
            or any(ord(c) < 32 or ord(c) == 127 for c in path)):
        return False
    parts = path.split('/')
    if any(p in ('', '.', '..') or p.casefold() == '.git' or p.endswith((' ', '.')) for p in parts):
        return False
    reserved = {'con', 'prn', 'aux', 'nul', *(f'com{i}' for i in range(1, 10)), *(f'lpt{i}' for i in range(1, 10))}
    if any(p.split('.')[0].casefold() in reserved for p in parts):
        return False
    folded = path.casefold()
    if folded in ('.claude/settings.json', '.claude/settings.local.json', '.codex/auth.json', '.codex/config.toml'):
        return False
    if any(p.casefold() in ('.env', '.npmrc', '.pypirc', 'credentials.json') or p.casefold().startswith('.env.') for p in parts):
        return False
    return not folded.endswith(('.pem', '.key'))


def collect(project, paths, *, maximum=MAX_FILES, total=MAX_TOTAL):
    if not isinstance(paths, list) or not paths or any(not valid_path(p) for p in paths):
        raise Invalid('invalid_paths')
    if len(paths) > maximum:
        raise Invalid('path_budget')
    if len(set(os.path.normcase(p) for p in paths)) != len(paths):
        raise Invalid('invalid_paths')
    redactor = module('redact.py')
    if any(redactor.redactar(p) != p for p in paths):
        raise Invalid('invalid_paths')
    root = Path(project).absolute()
    info = root.lstat()
    reader = module('local-read.py')
    if not stat.S_ISDIR(info.st_mode) or reader._redirected(info):
        raise Invalid('unsafe_project')
    identity = json.dumps([os.path.normcase(str(root)), info.st_dev, info.st_ino], separators=(',', ':'))
    project_id = hashlib.sha256(identity.encode('utf-8')).hexdigest()
    rows, issues, consumed = [], [], 0
    for path in sorted(paths):
        remaining = min(MAX_FILE, total - consumed)
        if remaining <= 0:
            issues.append({'path': path, 'status': 'byte_budget'})
            break
        row = reader.read_bytes(root, path, max_bytes=remaining, include_digest=True)
        consumed += row.get('bytes', 0)
        if row['status'] != 'ok':
            issues.append({'path': path, 'status': row['status']})
        else:
            rows.append({'path': path, 'sha256': row['sha256'], 'bytes': len(row['data']), 'data': row['data']})
    return project_id, rows, issues


def snapshot(project, paths):
    try:
        identity, rows, issues = collect(project, paths)
        receipt = result('incomplete' if issues else 'ok', not issues, project_id=identity,
                         sources=[{k: v for k, v in r.items() if k != 'data'} for r in rows], issues=issues)
        # Reserve CRLF too: TextIO stdout expands print's LF on Windows.
        if len((json.dumps(receipt, ensure_ascii=False) + '\r\n').encode('utf-8')) > MAX_RECEIPT:
            return result('receipt_budget')
        return receipt
    except Invalid as exc:
        return result(str(exc))
    except (OSError, ValueError, TypeError, ImportError, AttributeError):
        return result('unavailable')


def verify(project, receipt):
    try:
        keys = {'schema_version', 'status', 'complete', 'project_id', 'sources', 'issues'}
        if (not isinstance(receipt, dict) or set(receipt) != keys or type(receipt['schema_version']) is not int or receipt['schema_version'] != 1
                or receipt['status'] != 'ok' or receipt['complete'] is not True or receipt['issues'] != []
                or not isinstance(receipt['project_id'], str) or not _SHA.fullmatch(receipt['project_id'])
                or not isinstance(receipt['sources'], list) or not 0 < len(receipt['sources']) <= MAX_FILES):
            raise Invalid('invalid_receipt')
        for row in receipt['sources']:
            if (not isinstance(row, dict) or set(row) != {'path', 'sha256', 'bytes'}
                    or not valid_path(row['path']) or not isinstance(row['sha256'], str)
                    or not _SHA.fullmatch(row['sha256']) or type(row['bytes']) is not int
                    or not 0 <= row['bytes'] <= MAX_FILE):
                raise Invalid('invalid_receipt')
        paths = [r['path'] for r in receipt['sources']]
        identity, current, issues = collect(project, paths)
        if identity != receipt['project_id']:
            return result('different_project')
        original = {r['path']: (r['sha256'], r['bytes']) for r in receipt['sources']}
        changed = [r['path'] for r in current if (r['sha256'], r['bytes']) != original[r['path']]]
        return result('stale' if issues or changed else 'fresh', not (issues or changed), changed=changed, issues=issues)
    except Invalid as exc:
        return result(str(exc))
    except (OSError, ValueError, TypeError, ImportError, AttributeError, KeyError):
        return result('unavailable')


def unique(pairs):
    data = {}
    for key, value in pairs:
        if key in data:
            raise ValueError('duplicate key')
        data[key] = value
    return data


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('operation', choices=('snapshot', 'verify'))
    parser.add_argument('--project', default='.')
    parser.add_argument('--file', action='append', default=[])
    args = parser.parse_args(argv)
    if args.operation == 'snapshot':
        value = snapshot(args.project, args.file)
    else:
        try:
            raw = sys.stdin.buffer.read(MAX_RECEIPT + 1)
            if len(raw) > MAX_RECEIPT:
                raise ValueError('receipt budget')
            value = verify(args.project, json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique))
        except (ValueError, UnicodeError, RecursionError):
            value = result('invalid_receipt')
    try:
        output = module('redact.py').redactar(json.dumps(value, ensure_ascii=False))
    except (OSError, ImportError, AttributeError):
        print(json.dumps(result('unavailable')))
        return 2
    print(output)
    return 0 if value['complete'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
