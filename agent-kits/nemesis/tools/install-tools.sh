#!/usr/bin/env bash
# Optional, explicitly invoked installer. Pins and validation live beside this file.
set -uo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
for candidate in python3 python; do
  if "$candidate" -I -B -c 'import sys; sys.exit(sys.version_info < (3, 10))' >/dev/null 2>&1; then
    exec "$candidate" -I -B "$SCRIPT_DIR/install-tools.py" "$@"
  fi
done
printf '%s\n' 'Nemesis tools: Python 3.10+ is required; nothing installed.' >&2
exit 1
