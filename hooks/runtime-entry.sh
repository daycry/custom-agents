#!/usr/bin/env bash
# Private entry point: the Node launcher validates $1 against a fixed list.
set -u
HERE="$(cd "$(dirname "$BASH_SOURCE")" && pwd)"
export PATH="$HERE/runtime-bin:$PATH"
HOOK="$1"
shift
exec bash "$HERE/$HOOK" "$@"
