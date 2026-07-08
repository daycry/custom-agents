#!/usr/bin/env bash
# ============================================================================
# install-tools.sh — Cross-platform installer for the local-pentest toolkit
# used by the `nemesis` agent.
#
# Works on Linux, macOS and Windows (Git Bash / MSYS). No root required.
# Installs into $SECURITY_TOOLS_DIR (default: ~/.claude/security-tools),
# which is OUTSIDE any project repo and carries its own `.gitignore` so no
# binary ever reaches version control.
#
# Idempotent: re-running skips already-installed tools (pass --force to redo).
# Each tool degrades gracefully: a failure for one never aborts the rest.
#
# The "library" of installable tools is declared in the CATALOG section below.
# ============================================================================
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="${SECURITY_TOOLS_DIR:-$HOME/.claude/security-tools}"
BIN="$ROOT/bin"
VENDOR="$ROOT/vendor"
LOG="$ROOT/install.log"
MANIFEST="$ROOT/manifest.txt"
FORCE=0
[ "${1:-}" = "--force" ] && FORCE=1

mkdir -p "$BIN" "$VENDOR"
# Hard guard: never commit anything under the install root.
[ -f "$ROOT/.gitignore" ] || printf '*\n' > "$ROOT/.gitignore"
: > "$MANIFEST"

# ---- platform detection ----------------------------------------------------
case "$(uname -s)" in
  Linux*)                 OS=linux ;;
  Darwin*)                OS=darwin ;;
  MINGW*|MSYS*|CYGWIN*)   OS=windows ;;
  *)                      OS=linux ;;
esac
case "$(uname -m)" in
  x86_64|amd64)           ARCH=amd64 ;;
  aarch64|arm64)          ARCH=arm64 ;;
  *)                      ARCH=amd64 ;;
esac
EXE=""; [ "$OS" = windows ] && EXE=".exe"

# ---- pick a working python (this Windows box ships a broken python3 stub) --
PY=""
for c in python3 python; do
  if "$c" -c 'import sys' >/dev/null 2>&1; then PY="$c"; break; fi
done

have(){ command -v "$1" >/dev/null 2>&1; }
log(){ echo "[$(date +%H:%M:%S)] $*" >> "$LOG"; }
say(){ echo "$*"; }
record(){ echo "$1	$2	$3" >> "$MANIFEST"; }   # name  status  detail

say ">> Toolkit target: $ROOT   ($OS/$ARCH)"
[ -z "$PY" ] && say "   [warn] no working python found — python-based tools will be skipped"

# ---- installers ------------------------------------------------------------
gh_json(){ curl -fsSL -H "Accept: application/vnd.github+json" \
             "https://api.github.com/repos/$1/releases/latest" 2>/dev/null; }

install_go_bin(){  # $1 repo   $2 binary-name
  local repo="$1" name="$2"
  if [ "$FORCE" = 0 ] && [ -x "$BIN/$name$EXE" ]; then
    say "  [--] $name (already installed)"; record "$name" present "$BIN/$name$EXE"; return; fi
  [ -z "$PY" ] && { say "  [--] $name (needs python to resolve asset)"; record "$name" skipped no-python; return; }
  log "install $name from $repo"
  local url; url="$(gh_json "$repo" | "$PY" "$SCRIPT_DIR/pick_asset.py" "$OS" "$ARCH" 2>>"$LOG")"
  if [ -z "$url" ]; then say "  [!!] $name: no release asset for $OS/$ARCH"; record "$name" failed no-asset; return; fi
  local tmp file found; tmp="$(mktemp -d)"; file="$tmp/${url##*/}"
  if ! curl -fsSL -o "$file" "$url"; then say "  [!!] $name: download failed"; record "$name" failed download; rm -rf "$tmp"; return; fi
  case "$file" in
    *.zip)            unzip -oq "$file" -d "$tmp" 2>>"$LOG" ;;
    *.tar.gz|*.tgz)   tar -xzf "$file" -C "$tmp" 2>>"$LOG" ;;
  esac
  found="$(find "$tmp" -type f \( -iname "$name$EXE" -o -name "$name" \) 2>/dev/null | head -1)"
  if [ -z "$found" ]; then say "  [!!] $name: binary not found in archive"; record "$name" failed no-binary; rm -rf "$tmp"; return; fi
  cp "$found" "$BIN/$name$EXE" && chmod +x "$BIN/$name$EXE" 2>/dev/null
  rm -rf "$tmp"
  say "  [OK] $name -> bin/$name$EXE"; record "$name" installed "$BIN/$name$EXE"
}

write_shim(){  # $1 shim-name   $2 command-line (absolute)
  local name="$1"; shift
  { echo '#!/usr/bin/env bash'; echo "exec $* \"\$@\""; } > "$BIN/$name"
  chmod +x "$BIN/$name" 2>/dev/null
}

install_git_tool(){  # $1 url  $2 dir  $3 shim-name  $4 runner-cmdline
  local url="$1" dir="$2" name="$3" runner="$4"
  if [ -d "$VENDOR/$dir/.git" ]; then
    if [ "$FORCE" = 1 ]; then (cd "$VENDOR/$dir" && git pull --ff-only -q) 2>>"$LOG"; fi
    say "  [--] $name (already present)"; write_shim "$name" "$runner"; record "$name" present "$VENDOR/$dir"; return; fi
  if git clone --depth 1 -q "$url" "$VENDOR/$dir" 2>>"$LOG"; then
    write_shim "$name" "$runner"
    say "  [OK] $name -> vendor/$dir (shim: bin/$name)"; record "$name" installed "$VENDOR/$dir"
  else
    say "  [!!] $name: git clone failed"; record "$name" failed clone
  fi
}

install_pip_tool(){  # $1 pip-package  $2 console-name
  local pkg="$1" name="$2"
  [ -z "$PY" ] && { say "  [--] $name (no python)"; record "$name" skipped no-python; return; }
  if "$PY" -m pip install --quiet --disable-pip-version-check --upgrade "$pkg" >>"$LOG" 2>&1; then
    say "  [OK] $name (pip: $pkg)"; record "$name" installed "pip:$pkg"
  else
    say "  [!!] $name: pip install failed (see install.log)"; record "$name" failed pip
  fi
}

# ============================================================================
# CATALOG — the library of everything this agent can install.
# Category A: prebuilt Go single-binaries (per-OS/arch release assets)
# Category B: git-cloned script tools (need a runtime already present)
# Category C: pip packages
# ============================================================================
say ""; say "== A. Prebuilt binaries (nuclei/httpx/ffuf/gitleaks) =="
install_go_bin projectdiscovery/nuclei nuclei
install_go_bin projectdiscovery/httpx  httpx
install_go_bin ffuf/ffuf               ffuf
install_go_bin gitleaks/gitleaks       gitleaks

say ""; say "== B. Script tools (testssl/sqlmap/nikto) =="
if have git && have openssl; then
  install_git_tool https://github.com/drwetter/testssl.sh.git testssl.sh testssl "bash '$VENDOR/testssl.sh/testssl.sh'"
else say "  [--] testssl (needs git + openssl)"; record testssl skipped deps; fi
if have git && [ -n "$PY" ]; then
  install_git_tool https://github.com/sqlmapproject/sqlmap.git sqlmap sqlmap "$PY '$VENDOR/sqlmap/sqlmap.py'"
else say "  [--] sqlmap (needs git + python)"; record sqlmap skipped deps; fi
if have git && have perl; then
  install_git_tool https://github.com/sullo/nikto.git nikto nikto "perl '$VENDOR/nikto/program/nikto.pl'"
else say "  [--] nikto (needs git + perl)"; record nikto skipped deps; fi

say ""; say "== C. Python packages (wafw00f) =="
install_pip_tool wafw00f wafw00f

# ---- verification ----------------------------------------------------------
say ""; say "== Verification =="
verify(){ local n="$1" c="$2"; if [ -x "$BIN/$n$EXE" ] || [ -x "$BIN/$n" ]; then
    local v; v="$(cd "$BIN" && eval "$c" 2>/dev/null | head -1)"; say "  $n: ${v:-installed}"; fi; }
export PATH="$BIN:$PATH"
verify nuclei   "./nuclei$EXE -version"
verify httpx    "./httpx$EXE -version"
verify ffuf     "./ffuf$EXE -V"
verify gitleaks "./gitleaks$EXE version"
verify testssl  "./testssl --version 2>&1 | grep -i testssl"
verify sqlmap   "./sqlmap --version"
verify nikto    "./nikto -Version 2>&1 | grep -i nikto"
[ -n "$PY" ] && { command -v wafw00f >/dev/null 2>&1 && say "  wafw00f: $(wafw00f --version 2>&1 | head -1)"; }

say ""; say ">> Done. Tools in: $BIN"
say ">> Add to PATH for manual use:  export PATH=\"$BIN:\$PATH\""
say ">> nuclei templates download on first run (nuclei -update-templates)."
