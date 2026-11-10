#!/usr/bin/env python3
# panel-title: Cierre de subagente
# panel-description: Informa del estado de las iniciativas activas cuando termina un subagente, en un solo intérprete y sin repetir el último estado mostrado.
"""SubagentStop: progress of the active initiatives, in one interpreter and debounced.

H-30 (T-14): `subagent-progress.sh` chained about nine processes per SubagentStop (bash, cat,
two Python interpreters…) and repeated the same state after every subagent. This module keeps
its output byte for byte (`progress-report.py active` as `systemMessage`, only when an initiative
is active) and suppresses a state the user has just seen, with the same `.progress-last` debounce
as `ledger-post.py`, in its own `.claude/.progress-last-subagent`. Informative only: always exit 0, never `decision`/`continue`.
"""
import argparse
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
SHARED = HERE.parent / 'agent-kits/shared'
MAX_BYTES = 2 * 1024 * 1024
SIN_ACTIVAS = 'sin iniciativas en progreso'


def _load(name, path):
    spec = importlib.util.spec_from_file_location('subagent_progress_' + name, path)
    module = importlib.util.module_from_spec(spec)
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        spec.loader.exec_module(module)
    return module


def compose(root):
    """`{"systemMessage": …}` line, or '' when nothing is active or the state was just shown."""
    roadmap = os.path.join(root, 'docs', 'roadmap')
    if not os.path.isdir(roadmap):
        return ''
    progress = _load('report', SHARED / 'progress-report.py')
    output = io.StringIO()
    with contextlib.redirect_stdout(output), contextlib.redirect_stderr(io.StringIO()):
        try:
            progress.main(['active', '--root', roadmap])
        except SystemExit:
            pass
    text = output.getvalue().rstrip('\n')   # like the shell's $(...)
    if not text or text == SIN_ACTIVAS:
        return ''
    try:
        # Own last state (review attempt 1, B-note): a ledger line shown by PostToolUse inside a subagent
        # may never reach the user, so it must not silence the closing summary.
        if _load('ledger_post', HERE / 'ledger-post.py')._repeated(Path(os.path.abspath(root)), text,
                                                                  '.progress-last-subagent'):
            return ''
    except (OSError, ValueError, UnicodeError, AttributeError):
        pass   # as in ledger-post: a debounce failure may repeat a state, never lose it
    return json.dumps({'systemMessage': text}, ensure_ascii=False) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--root', default=os.environ.get('CLAUDE_PROJECT_DIR') or os.getcwd())
    try:
        args = parser.parse_args(argv)
        sys.stdin.buffer.read(MAX_BYTES + 1)   # the payload is not used: the state comes from the ledgers
        sys.stdout.write(compose(args.root))
    except Exception:
        pass  # Informative: SubagentStop never holds the subagent.
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
