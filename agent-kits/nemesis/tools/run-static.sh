#!/usr/bin/env bash
# ============================================================================
# run-static.sh — escáneres ESTÁTICOS sobre el árbol del proyecto (sin target
# de red, por tanto SIN guardrail):
#   trivy fs   -> vulnerabilidades de dependencias (SCA)  -> area deps
#   hadolint   -> lint de Dockerfile                       -> area iac
# Sus salidas JSON se dejan en <out-dir>/raw/ para que el agente las funda en
# findings.json (mapeo en agents/nemesis.md §5).
#
# Usage:  run-static.sh <project-dir> <out-dir>
# ============================================================================
set -uo pipefail
PROJECT="${1:?usage: run-static.sh <project-dir> <out-dir>}"
OUTDIR="${2:?missing out-dir}"

ROOT="${SECURITY_TOOLS_DIR:-$HOME/.claude/security-tools}"
BIN="$ROOT/bin"; export PATH="$BIN:$PATH"
RAW="$OUTDIR/raw"; mkdir -p "$RAW"
EXE=""; case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) EXE=".exe";; esac
avail(){ [ -x "$BIN/$1$EXE" ] || [ -x "$BIN/$1" ] || command -v "$1" >/dev/null 2>&1; }

echo ">> static scanners on: $PROJECT"
echo ">> tool dir: $BIN"

# --- trivy fs: SCA de dependencias (area deps) ------------------------------
if avail trivy; then
  echo ">> trivy fs (SCA / vulnerabilidades -> area deps)"
  if ! trivy$EXE fs --quiet --scanners vuln --format json \
        --output "$RAW/trivy.json" "$PROJECT" 2>"$RAW/trivy.err"; then
    echo "  [!!] trivy falló (¿sin BD/red en el primer uso? ver raw/trivy.err)"
  fi
else echo "  [--] trivy no instalado"; fi

# --- hadolint: lint de Dockerfile (area iac) --------------------------------
if avail hadolint; then
  # recolecta Dockerfiles de forma portable (sin mapfile, compatible bash 3.2)
  dockerfiles=""
  while IFS= read -r f; do dockerfiles="$dockerfiles${dockerfiles:+$'\n'}$f"; done < <(
    find "$PROJECT" -type f \( -iname 'Dockerfile' -o -iname 'Dockerfile.*' -o -iname '*.dockerfile' \) \
      -not -path '*/node_modules/*' -not -path '*/vendor/*' 2>/dev/null)
  if [ -n "$dockerfiles" ]; then
    n="$(printf '%s\n' "$dockerfiles" | grep -c . )"
    echo ">> hadolint ($n Dockerfile(s) -> area iac)"
    # shellcheck disable=SC2086
    printf '%s\n' "$dockerfiles" | tr '\n' '\0' | xargs -0 hadolint$EXE --format json \
      > "$RAW/hadolint.json" 2>"$RAW/hadolint.err" || true
  else
    echo "  [--] hadolint: sin Dockerfile (N/A)"
  fi
else echo "  [--] hadolint no instalado"; fi

echo ">> raw outputs in: $RAW"
ls -1 "$RAW" 2>/dev/null | sed 's/^/   - /'
