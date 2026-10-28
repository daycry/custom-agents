#!/usr/bin/env bash
# Opt-in Claude Code statusline: model, session cost, context, canonical roadmap.
# /setup installs this absolute path; remove statusLine from settings to disable.
# One isolated Python on a miss; no Python for identical input and unchanged ledgers.
# Cache also tracks usage-state and renderer sources. Never evals input or cache.
set -u
INPUT=""
IFS= read -r -d '' INPUT || true
source_path="${BASH_SOURCE[0]//\\//}"
case "$source_path" in */*) directory="${source_path%/*}" ;; *) directory=. ;; esac
HERE="$(cd "$directory" 2>/dev/null && pwd)"
ROOT="${CLAUDE_PROJECT_DIR:-$PWD}"
REPORT="$HERE/../agent-kits/shared/progress-report.py"
RENDER="$HERE/../agent-kits/shared/statusline-render.py"
if [ ! -f "$REPORT" ]; then
  REPORT="$(find "$PWD/.claude" "$PWD/.codex" "$PWD/.opencode" "${HOME:-}/.claude" "${HOME:-}/.codex" "${HOME:-}/.config/opencode" -type f -path '*agent-kits/shared/progress-report.py' ! -path '*/.claude/jobs/*' 2>/dev/null | head -1)"
fi
if [ ! -f "$RENDER" ]; then
  RENDER="${CLAUDE_PLUGIN_ROOT:-}/agent-kits/shared/statusline-render.py"
  if [ ! -f "$RENDER" ]; then
    RENDER="$(find "$PWD/.claude" "$PWD/.codex" "$PWD/.opencode" "${HOME:-}/.claude" "${HOME:-}/.codex" "${HOME:-}/.config/opencode" -type f -path '*agent-kits/shared/statusline-render.py' ! -path '*/.claude/jobs/*' 2>/dev/null | head -1)"
  fi
fi
fallback() {
  local model
  model="$(printf '%s' "$INPUT" | grep -oE '"display_name"[[:space:]]*:[[:space:]]*"[^"]*"' 2>/dev/null | head -1 | sed -E 's/.*:[[:space:]]*"([^"]*)"/\1/' 2>/dev/null)"
  [ -n "$model" ] && printf '[%s]\n' "$model" 2>/dev/null
  return 0
}
[ -f "$RENDER" ] || { fallback; exit 0; }

# Hash the input and a single batch of file metadata. GNU stat is used by Git Bash/Linux;
# BSD stat keeps this optional optimization usable when available on another host.
files=()
for path in "$RENDER" "$REPORT" "${REPORT%/*}/ledger-lint.py" "${BASH_SOURCE[0]}" "$ROOT/.claude/usage-state.json" "$ROOT"/docs/roadmap/*/tasks.md; do
  [ -f "$path" ] && files+=("$path")
done
key=""
if command -v sha256sum >/dev/null 2>&1; then
  metadata="$(stat -c '%n:%s:%y:%i' -- "${files[@]}" 2>/dev/null || stat -f '%N:%m:%z:%i' "${files[@]}" 2>/dev/null)"
  if [ -n "$metadata" ]; then
    key="$(printf 'statusline-v1\000%s\000%s\000%s' "$INPUT" "$ROOT" "$metadata" | sha256sum)"
    key="${key%% *}"
  fi
fi
DATA="" cached=false
model="" cost="" ctx="" rm_seg=""
CACHE="$ROOT/.claude/statusline-cache"
if [ -n "$key" ] && [ -f "$CACHE" ] && [ ! -L "$CACHE" ]; then
  if {
    IFS= read -r saved_key &&
    IFS= read -r model &&
    IFS= read -r cost &&
    IFS= read -r ctx &&
    IFS= read -r rm_seg &&
    ! IFS= read -r extra
  } < "$CACHE"; then
    [ "$saved_key" = "$key" ] && cached=true
  fi
fi
if [ "$cached" = false ]; then
  PYTHON=""
  while IFS= read -r candidate; do
    [ -n "$candidate" ] || continue
    candidate_path="${candidate//\\//}"
    case "$candidate_path" in
      */[Ww][Ii][Nn][Dd][Oo][Ww][Ss][Aa][Pp][Pp][Ss]/*) continue ;;
    esac
    if [ -x "$candidate" ]; then PYTHON="$candidate"; break; fi
  done < <(printf '%s\n' "${CUSTOM_AGENTS_PYTHON:-}"; type -a -p python3 python 2>/dev/null)
  [ -n "$PYTHON" ] || { fallback; exit 0; }
  if ! DATA="$(printf '%s' "$INPUT" | "$PYTHON" -I -S "$RENDER" --root "$ROOT" --report "$REPORT" --cache-key "$key" 2>/dev/null)"; then
    fallback; exit 0
  fi
  model="" cost="" ctx="" rm_seg=""
  {
  IFS= read -r model || true
  IFS= read -r cost || true
  IFS= read -r ctx || true
  IFS= read -r rm_seg || true
  } <<< "$DATA"
fi
out=""
[ -n "$model" ] && out="[$model]"
if [[ "$cost" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
  LC_ALL=C printf -v cost_fmt '%.2f' "$cost" 2>/dev/null
  if [ "$cost_fmt" = "0.00" ] && [[ "$cost" =~ [1-9] ]]; then
    out="${out:+$out }<\$0.01"
  elif [ -n "$cost_fmt" ]; then
    out="${out:+$out }\$${cost_fmt}"
  fi
fi
if [[ "$ctx" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
  LC_ALL=C printf -v ctx_int '%.0f' "$ctx" 2>/dev/null
  [ -n "$ctx_int" ] && out="${out:+$out }ctx ${ctx_int}%"
fi
[ -n "$rm_seg" ] && out="${out:+$out · }$rm_seg"
[ -n "$out" ] && printf '%s\n' "$out" | LC_ALL=C tr -d '\000-\010\013\014\016-\037\177'
exit 0
