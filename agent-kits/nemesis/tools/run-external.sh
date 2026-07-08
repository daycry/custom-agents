#!/usr/bin/env bash
# ============================================================================
# run-external.sh — orchestrate the installed external tools against a LOCAL
# target, guardrailed. Raw outputs are dropped in <out-dir>/raw/ for the agent
# to read and fold into findings.json.
#
# Usage:  run-external.sh <target-url> <out-dir> [--sqli "<url-with-param>"]
#
# Runs by default (safe, non-exploitative): httpx, wafw00f, testssl, nuclei,
# nikto. sqlmap runs ONLY when --sqli is passed with an explicit parameterised
# URL (active exploitation — opt-in).
# ============================================================================
set -uo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
. "$HERE/lib-guardrail.sh"

TARGET="${1:?usage: run-external.sh <target-url> <out-dir> [--sqli <url>]}"
OUTDIR="${2:?missing out-dir}"
SQLI=""
[ "${3:-}" = "--sqli" ] && SQLI="${4:-}"

guardrail_assert "$TARGET"
[ -n "$SQLI" ] && guardrail_assert "$SQLI"

ROOT="${SECURITY_TOOLS_DIR:-$HOME/.claude/security-tools}"
BIN="$ROOT/bin"
export PATH="$BIN:$PATH"
RAW="$OUTDIR/raw"; mkdir -p "$RAW"
host="$(guardrail_host_of "$TARGET")"
EXE=""; case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) EXE=".exe";; esac
avail(){ [ -x "$BIN/$1$EXE" ] || [ -x "$BIN/$1" ] || command -v "$1" >/dev/null 2>&1; }
run(){ echo ">> $1"; shift; "$@"; }

echo ">> external tools target: $TARGET  (host: $host)"
echo ">> tool dir: $BIN"

if avail httpx; then
  run "httpx (fingerprint)" bash -c "printf '%s\n' '$TARGET' | httpx$EXE -silent -title -tech-detect -status-code -server -json > '$RAW/httpx.json' 2>/dev/null" || true
else echo "  [--] httpx not installed"; fi

if avail wafw00f; then
  run "wafw00f (WAF detect)" bash -c "wafw00f '$TARGET' > '$RAW/wafw00f.txt' 2>&1" || true
else echo "  [--] wafw00f not installed"; fi

if avail testssl && [ "${TARGET#https://}" != "$TARGET" ]; then
  run "testssl (TLS)" bash -c "testssl --quiet --color 0 --jsonfile '$RAW/testssl.json' '$host' >/dev/null 2>&1" || true
else echo "  [--] testssl skipped (not installed or http target)"; fi

if avail nuclei; then
  # safe template set: misconfig/exposures/tech; no intrusive/dos templates
  run "nuclei (templated checks)" bash -c "nuclei$EXE -silent -u '$TARGET' -severity low,medium,high,critical -tags misconfig,exposure,tech,default-login -jsonl -o '$RAW/nuclei.jsonl' >/dev/null 2>&1" || true
else echo "  [--] nuclei not installed"; fi

if avail nikto; then
  run "nikto (web server scan)" bash -c "nikto -host '$TARGET' -maxtime 120s -nointeractive -output '$RAW/nikto.txt' >/dev/null 2>&1" || true
else echo "  [--] nikto not installed"; fi

if [ -n "$SQLI" ]; then
  if avail sqlmap; then
    echo ">> sqlmap (ACTIVE SQLi — opt-in) on: $SQLI"
    run "sqlmap" bash -c "sqlmap -u '$SQLI' --batch --level 1 --risk 1 --crawl 0 --output-dir '$RAW/sqlmap' >'$RAW/sqlmap.txt' 2>&1" || true
  else echo "  [--] sqlmap not installed"; fi
fi

echo ">> raw outputs in: $RAW"
ls -1 "$RAW" 2>/dev/null | sed 's/^/   - /'
