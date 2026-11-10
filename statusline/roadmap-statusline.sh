#!/usr/bin/env bash
# Opt-in Claude Code statusline: model, session cost, context, canonical roadmap.
# /setup installs this absolute path; remove statusLine from settings to disable.
# One isolated Python on a miss; no Python while the ledgers stay unchanged (H-39: model, cost
# and context change every turn, so Bash reads them from the input and the cache key covers only
# the roadmap). Cache also tracks usage-state and renderer sources. Never evals input or cache.
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

# H-39 (T-16): model, cost and context straight from the input, in Bash, when each field has the
# plain shape whose text Python would print unchanged. Each field is read INSIDE its top-level group,
# as Python does (`model.display_name`, `cost.total_cost_usd`, `context_window.used_percentage`): a small
# JSON scanner walks the members of one object, skips strings (with their escapes) when it counts braces
# and admits nested objects inside a group (review attempts 1 and 2: `rate_limits.*`, `current_usage`,
# braces inside strings). A duplicate or escaped key, an unterminated string or anything it cannot
# follow means "cannot decide": that refresh keeps Python, with the input in the cache key (D1).
json_member() {   # $1 JSON object text, $2 key: MEMBER = raw value; 0 found, 2 absent, 1 cannot decide
  local s="$1" want="\"$2\"" depth=1 state=key cur="" cap=0 val="" got=0 chunk sp seg LC_ALL=C
  local re_open='^[[:space:]]*\{' re_tok='^([^]"{},:[]*)(.?)' re_str='^([^"\]*)(\\.|")'
  MEMBER=""
  [[ "$s" =~ $re_open ]] || return 1
  s="${s:${#BASH_REMATCH[0]}}"
  while :; do
    [[ "$s" =~ $re_tok ]] || return 1
    chunk="${BASH_REMATCH[1]}"; sp="${BASH_REMATCH[2]}"
    s="${s:${#BASH_REMATCH[0]}}"
    [ "$cap" = 1 ] && val+="$chunk"
    case "$sp" in
      '') return 1 ;;
      '"')
        seg='"'
        while :; do
          [[ "$s" =~ $re_str ]] || return 1
          seg+="${BASH_REMATCH[0]}"
          s="${s:${#BASH_REMATCH[0]}}"
          [ "${BASH_REMATCH[2]}" = '"' ] && break
        done
        if [ "$depth" = 1 ] && [ "$state" = key ]; then
          case "$seg" in *\\*) return 1 ;; esac
          cur="$seg" state=colon
        elif [ "$cap" = 1 ]; then
          val+="$seg"
        fi ;;
      ':')
        if [ "$depth" = 1 ] && [ "$state" = colon ]; then
          state=value
          if [ "$cur" = "$want" ]; then
            [ "$got" = 1 ] && return 1
            got=1 cap=1 val=""
          fi
        elif [ "$cap" = 1 ]; then
          val+=':'
        fi ;;
      ',')
        if [ "$depth" = 1 ]; then cap=0 state=key; elif [ "$cap" = 1 ]; then val+=','; fi ;;
      '{'|'[')
        depth=$((depth + 1)); [ "$cap" = 1 ] && val+="$sp" ;;
      '}'|']')
        depth=$((depth - 1))
        if [ "$depth" = 0 ]; then break; fi
        [ "$cap" = 1 ] && val+="$sp" ;;
    esac
  done
  [ "$got" = 1 ] || return 2
  [[ "$val" =~ ^[[:space:]]*(.*[^[:space:]])[[:space:]]*$ ]] && val="${BASH_REMATCH[1]}"
  MEMBER="$val"
  return 0
}
input_field() {   # $1 group, $2 key, $3 value regex; sets FIELD; returns 1 when Bash cannot decide
  local group re LC_ALL=C
  FIELD=""
  json_member "$INPUT" "$1"
  case $? in 2) return 0 ;; 1) return 1 ;; esac             # no group: Python prints nothing either
  group="$MEMBER"
  case "$group" in '{'*) ;; *) return 0 ;; esac            # null or not an object: Python prints nothing
  json_member "$group" "$2"
  case $? in 2) return 0 ;; 1) return 1 ;; esac
  re="^(null|$3)\$"
  [[ "$MEMBER" =~ $re ]] || return 1
  FIELD="$MEMBER"
  [ "$FIELD" = null ] && FIELD=""
  [[ "$FIELD" =~ ^[\ -~]*$ ]] || return 1   # printable ASCII only: Python would print it unchanged
}
# Shortest round-trip text, as JSON.stringify and Python's repr write a double: up to 17
# significant digits, so the same text Python would print (a cost summed in floats is 0.43000000000000005).
NUMBER='(0|[1-9][0-9]{0,5})([.][0-9]{1,21})?'
fast=true model_in="" cost_in="" ctx_in=""
if input_field model display_name '"[^"\\]*"'; then model_in="${FIELD#\"}"; model_in="${model_in%\"}"; else fast=false; fi
if input_field cost total_cost_usd "$NUMBER"; then cost_in="$FIELD"; else fast=false; fi
if input_field context_window used_percentage "$NUMBER"; then ctx_in="$FIELD"; else fast=false; fi
case "$cost_in$ctx_in" in *0.0000*) fast=false ;; esac   # Python prints values < 1e-4 as 1e-05

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
    if [ "$fast" = true ]; then   # roadmap only: Bash paints the per-turn fields
      key="$(printf 'statusline-v2\000%s\000%s' "$ROOT" "$metadata" | sha256sum)"
    else                          # Python paints them: identical input still hits the cache
      key="$(printf 'statusline-v1\000%s\000%s\000%s' "$INPUT" "$ROOT" "$metadata" | sha256sum)"
    fi
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
if [ "$cached" = true ] && [ "$fast" = true ]; then model="$model_in" cost="$cost_in" ctx="$ctx_in"; fi
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
