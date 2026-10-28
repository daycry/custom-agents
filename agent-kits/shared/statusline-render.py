#!/usr/bin/env python3
"""Parse one statusline input and reuse the roadmap CLI in the same interpreter.

stdout contains four plain lines, formatted by Bash with its existing numeric rules.
The cache stores only those public fields, plus an opaque input/mtime digest.
"""
import argparse
import contextlib
import io
import json
import os
from pathlib import Path
import re
import runpy
import sys
import tempfile

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001

# The four-field protocol must remain LF when stdout is a Windows pipe.
try:
    sys.stdout.reconfigure(newline="\n")
except (AttributeError, ValueError):
    pass
sys.dont_write_bytecode = True


def one_line(value):
    if value is None:
        return ''
    return re.sub(r'[\x00-\x1f\x7f-\x9f\u202a-\u202e\u2066-\u2069]', ' ', str(value))


def roadmap_segment(root, report):
    if not report or not Path(root, 'docs', 'roadmap').is_dir():
        return ''
    output = io.StringIO()
    previous = sys.argv
    try:
        sys.argv = [str(report), 'active', '--root', str(Path(root, 'docs', 'roadmap')), '--json']
        with contextlib.redirect_stdout(output):
            try:
                runpy.run_path(str(report), run_name='__main__')
            except SystemExit as result:
                if result.code not in (0, None):
                    return ''
        data = json.loads(output.getvalue())
        active = data.get('activas', [])
        if len(active) == 1:
            row = active[0]
            return '\U0001f4cb %s T-%02d/%d %d%%' % (row['slug'], row['completadas'], row['total'], row['pct'])
        if len(active) > 1:
            row = next((r for r in active if r.get('slug') == data.get('iniciativa_en_curso')), None)
            if row:
                return '\U0001f4cb %d activas \u00b7 \u25b6 %s T-%02d/%d %d%%' % (
                    len(active), row['slug'], row['completadas'], row['total'], row['pct'])
            return '\U0001f4cb %d iniciativas activas' % len(active)
    except Exception:  # optional roadmap must never break the statusline
        return ''
    finally:
        sys.argv = previous
    return ''


def render(payload, root, report):
    def field(group, key):
        parent = payload.get(group) if isinstance(payload, dict) else None
        return one_line(parent.get(key)) if isinstance(parent, dict) else ''
    return '\n'.join((field('model', 'display_name'), field('cost', 'total_cost_usd'),
                      field('context_window', 'used_percentage'), one_line(roadmap_segment(root, report)))) + '\n'


def write_cache(root, key, data):
    if not re.fullmatch(r'[0-9a-f]{64}', key):
        return
    directory = Path(os.path.abspath(root)) / '.claude'
    temporary = None
    try:
        directory.mkdir(mode=0o700, exist_ok=True)
        if directory.is_symlink() or directory.resolve() != directory:
            return
        ignored = directory / '.gitignore'
        if ignored.is_symlink():
            return
        if not ignored.exists() or 'statusline-cache' not in ignored.read_text(encoding='utf-8').splitlines():
            flags = os.O_WRONLY | os.O_CREAT | os.O_APPEND | getattr(os, 'O_NOFOLLOW', 0)
            fd = os.open(ignored, flags, 0o600)
            try:
                os.write(fd, b'\n# local statusline cache\nstatusline-cache\nstatusline-cache.*.tmp\n')
            finally:
                os.close(fd)
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', newline='\n', dir=directory,
                                         prefix='statusline-cache.', suffix='.tmp', delete=False) as handle:
            temporary = handle.name
            handle.write(key + '\n' + data)
        os.replace(temporary, directory / 'statusline-cache')
    except (OSError, UnicodeError):
        pass
    finally:
        if temporary:
            try:
                os.unlink(temporary)
            except OSError:
                pass


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True)
    parser.add_argument('--report')
    parser.add_argument('--cache-key', default='')
    args = parser.parse_args(argv)
    try:
        payload = json.load(sys.stdin)
    except (ValueError, OSError):
        payload = {}
    data = render(payload, args.root, args.report)
    write_cache(args.root, args.cache_key, data)
    print(data, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
