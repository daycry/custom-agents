#!/usr/bin/env python3
"""Read-only CLI for reviewing and revalidating literal commit selections.

scope-check.py owns the projection. The caller performs the native Git commit;
this CLI never stages, commits, writes objects or adopts another staged change.
"""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001

MAX_SNAPSHOT_BYTES = 64 * 1024 * 1024


def _owner():
    path = Path(__file__).resolve().parent / 'scope-check.py'
    spec = importlib.util.spec_from_file_location('custom_agents_scope_check', path)
    if spec is None or spec.loader is None:
        raise ImportError('owner_unavailable')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pairs(items):
    obj = {}
    for key, value in items:
        if key in obj:
            raise ValueError('duplicate_key')
        obj[key] = value
    return obj


def _invalid():
    return {'valido': False, 'motivos': [{'code': 'invalid_snapshot'}]}


def _emit(value, code):
    raw = json.dumps(value, ensure_ascii=True, allow_nan=False,
        separators=(',', ':')).encode('utf8')
    if len(raw) + 1 > MAX_SNAPSHOT_BYTES:
        raw = b'{"status":"unavailable","reason":"response_budget"}'
        code = 3
    sys.stdout.buffer.write(raw + b'\n')
    return code


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    operations = parser.add_subparsers(dest='operation', required=True)
    preview = operations.add_parser('preview')
    preview.add_argument('--path', action='append', required=True,
        help='Exact project-relative path; repeat for each selected file')
    validate = operations.add_parser('validate')
    for command in (preview, validate):
        command.add_argument('--root', required=True)
    args = parser.parse_args(argv)
    if args.operation == 'validate':
        try:
            raw = sys.stdin.buffer.read(MAX_SNAPSHOT_BYTES + 1)
            if len(raw) > MAX_SNAPSHOT_BYTES:
                raise ValueError('input_budget')
            snapshot = json.loads(raw.decode('utf8'), object_pairs_hook=_pairs,
                parse_constant=lambda value: (_ for _ in ()).throw(ValueError('invalid_number')))
        except (ValueError, UnicodeError, RecursionError):
            return _emit(_invalid(), 1)
        try:
            result = _owner().validar_seleccion_commit(args.root, snapshot)
            return _emit(result, 0 if result['valido'] else 1)
        except (OSError, ValueError, TypeError, KeyError, ImportError, RecursionError, subprocess.SubprocessError):
            return _emit({'status': 'unavailable', 'reason': 'projection_unavailable'}, 3)
    try:
        result = _owner().proyectar_commit(args.root, args.path)
        return _emit(result, 1 if result['conflictos'] else 0)
    except ValueError:
        return _emit({'status': 'invalid_input', 'reason': 'invalid_selection'}, 2)
    except (OSError, TypeError, KeyError, ImportError, RuntimeError, RecursionError, subprocess.SubprocessError):
        return _emit({'status': 'unavailable', 'reason': 'projection_unavailable'}, 3)


if __name__ == '__main__':
    raise SystemExit(main())
