#!/usr/bin/env python3
# panel-title: Validación y progreso del ledger
# panel-description: Valida tasks.md y muestra su progreso con un solo análisis y debounce; informa sin bloquear.
"""Compose existing ledger lint/progress messages from one bounded read and parse."""
import argparse
import contextlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001

sys.dont_write_bytecode = True
SHARED = Path(__file__).resolve().parents[1] / 'agent-kits/shared'
MAX_BYTES = 2 * 1024 * 1024


def _load(name, filename):
    spec = importlib.util.spec_from_file_location('ledger_post_' + name, SHARED / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


try:
    lint_module = _load('lint', 'ledger-lint.py')
    progress_module = _load('progress', 'progress-report.py')
    reader = _load('reader', 'local-read.py')
    state_module = _load('state', 'local-state.py')
    redact_module = _load('redact', 'redact.py')
except Exception:  # A partial installation must not fail the user's edit.
    lint_module = progress_module = reader = state_module = redact_module = None


def _warn(message):
    print('custom-agents hooks: ' + message, file=sys.stderr)


def _need(condition, code):
    if not condition:
        raise ValueError(code)


def _guard(deadline):
    _need(time.monotonic() < deadline, 'deadline')


@contextlib.contextmanager
def _progress_lock(io, directory, deadline):
    """Use the legacy flock domain on POSIX; native byte locking on Windows."""
    lock = directory / '.progress-last.lock'
    fd = unlock = None
    try:
        try:
            fd = os.open(lock, os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, 'O_NOFOLLOW', 0), 0o600)
            os.write(fd, b'0')
        except FileExistsError:
            before = io.file(lock)
            fd = os.open(lock, os.O_RDWR | getattr(os, 'O_NOFOLLOW', 0))
            info = os.fstat(fd)
            _need((info.st_dev, info.st_ino) == before[:2], 'unsafe_state')
        io.dirs(directory)
        _need(io.file(lock)[:2] == (os.fstat(fd).st_dev, os.fstat(fd).st_ino), 'unsafe_state')
        while True:
            _guard(deadline)
            try:
                if os.name == 'nt':
                    unlock = state_module._byte_lock(fd, 0)
                else:
                    import fcntl
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    unlock = lambda: fcntl.flock(fd, fcntl.LOCK_UN)
                break
            except OSError:
                time.sleep(min(0.005, max(0, deadline - time.monotonic())))
        io.dirs(directory)
        yield
    finally:
        if unlock:
            with contextlib.suppress(OSError): unlock()
        if fd is not None:
            os.close(fd)


def _repeated(root, line):
    deadline = time.monotonic() + 5
    io = state_module.StateIO(reader, _need, _guard, maximum=MAX_BYTES)
    directory = root / '.claude'
    io.dirs(root)
    directory.mkdir(exist_ok=True)
    io.dirs(directory)
    with _progress_lock(io, directory, deadline):
        path = directory / '.progress-last'
        try:
            raw, before = io.read(path, MAX_BYTES)
        except FileNotFoundError:
            raw, before = b'', None
        if raw.decode('utf-8') == line:
            return True
        io.write(path, line.encode('utf-8'), deadline, expected=before)
        return False


def _paths(payload):
    value = payload.get('tool_input') if isinstance(payload, dict) else None
    if not isinstance(value, dict):
        return []
    paths = []
    if 'file_path' in value:
        paths.append(value['file_path'])
    if 'edits' in value:
        if not isinstance(value['edits'], list):
            return []
        for edit in value['edits']:
            paths.append(edit.get('file_path') if isinstance(edit, dict) else None)
    if any(not isinstance(p, str) or not p or any(c in p for c in '\r\n\0') for p in paths):
        return []
    return list(dict.fromkeys(p.replace('\\', '/') for p in paths))


def _lint_message(path, text, parsed):
    errors, warnings = lint_module.lint(str(path), text=text, parsed=parsed)
    lines = ['⚠️  ' + warning for warning in warnings]
    lines.extend('⚠️  ' + error for error in errors)
    lines.append(f'ledger-lint: {len(errors)} incoherencias · {len(warnings)} avisos ({path.name})')
    return '\n'.join(lines)


def process_payload(payload, root):
    if lint_module is None:
        _warn('ledger services unavailable; hook skipped')
        return ''
    root = Path(os.path.abspath(root))
    messages, progress = [], None
    for raw in _paths(payload):
        if 'docs/roadmap/' not in raw or not raw.endswith('tasks.md'):
            continue
        try:
            _need('..' not in raw.split('/'), 'invalid_path')
            path = Path(os.path.abspath(root / raw))
            relative = path.relative_to(root).as_posix()
            row = reader.read_text(root, relative, max_bytes=MAX_BYTES)
            _need(row['status'] == 'ok', 'ledger_unavailable')
            text = row['text'].removeprefix('\ufeff')
            parsed = lint_module.parse_ledger(text)
            messages.append(_lint_message(path, text, parsed))
            if progress is None:
                with contextlib.suppress(ValueError):
                    progress = redact_module.redactar(progress_module.linea(
                        progress_module.resumir(str(path), text=text, parsed=parsed)))
        except (OSError, ValueError, UnicodeError):
            _warn('ledger path unavailable; hook skipped')
    if progress:
        try:
            repeated = _repeated(root, progress)
        except (OSError, ValueError, UnicodeError):
            # As with the legacy fallback, a debounce failure may duplicate a line
            # but must not lose progress or replace an unverified existing file.
            _warn('progress debounce unavailable; progress emitted without saving')
            repeated = False
        if not repeated:
            messages.append(progress)
    return redact_module.redactar('\n'.join(messages))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', default=os.environ.get('CLAUDE_PROJECT_DIR') or os.getcwd())
    args = parser.parse_args(argv)
    try:
        raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ValueError('payload_budget')
        payload = json.loads(raw)
        message = process_payload(payload, args.root)
        if message:
            print(json.dumps({'systemMessage': message}, ensure_ascii=False))
    except Exception:
        _warn('ledger input unavailable; hook skipped')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
