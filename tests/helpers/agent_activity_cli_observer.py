"""Test-only observer of the exact CLI's API envelope; no producer changes."""
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

root = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('activity_cli', root / 'agent-kits/shared/agent-activity-store.py')
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)
receipt = Path(sys.argv[1])
assert receipt.parent == Path(os.environ['ACTIVITY_EVIDENCE'])
original = api.capture
diagnostics = []
original_need = api._need
first_io_reason = None
original_read = getattr(api._reader, 'read_bytes', None)


def read(*args, **kwargs):
    global first_io_reason
    row = original_read(*args, **kwargs)
    if first_io_reason is None and row.get('status') != 'ok':
        first_io_reason = {'status': row.get('status'), 'reason': row.get('reason'),
            'relative': str(args[1]) if len(args) > 1 else None,
            'monotonic_ns': time.monotonic_ns()}
    return row


if original_read is not None:
    api._reader.read_bytes = read


def need(condition, reason):
    if not condition:
        frame = sys._getframe(1)
        diagnostics.append({'kind': 'need', 'reason': reason, 'file': Path(frame.f_code.co_filename).name,
            'function': frame.f_code.co_name, 'line': frame.f_lineno})
    return original_need(condition, reason)


def trace(frame, event, value):
    if event == 'exception' and Path(frame.f_code.co_filename).name in ('agent-activity-store.py', 'local-state.py', 'local-read.py'):
        exc = value[1]
        diagnostics.append({'kind': 'exception', 'type': type(exc).__name__, 'errno': getattr(exc, 'errno', None),
            'winerror': getattr(exc, 'winerror', None), 'file': Path(frame.f_code.co_filename).name,
            'function': frame.f_code.co_name, 'line': frame.f_lineno})
    return trace


api._need = need


def observe(*args, **kwargs):
    sys.settrace(trace)
    try:
        result = original(*args, **kwargs)
    finally:
        sys.settrace(None)
    with receipt.open('x', encoding='utf-8') as handle:
        json.dump({'pid': os.getpid(), 'result': result, 'diagnostics': diagnostics,
            'first_io_reason': first_io_reason}, handle)
    return result


api.capture = observe
raise SystemExit(api.main(sys.argv[2:]))
