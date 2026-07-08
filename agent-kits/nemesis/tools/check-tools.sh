#!/usr/bin/env bash
# ============================================================================
# check-tools.sh — informa qué herramientas del toolkit están instaladas y
# cuáles faltan. NO instala nada. El agente lo usa para decidir si pedir
# permiso al usuario antes de llamar a install-tools.sh.
#
# Salida: resumen humano + líneas machine-readable (INSTALLED: / MISSING:).
# Exit code = número de herramientas que faltan (0 = todo instalado).
# ============================================================================
set -uo pipefail
ROOT="${SECURITY_TOOLS_DIR:-$HOME/.claude/security-tools}"
BIN="$ROOT/bin"
EXE=""; case "$(uname -s)" in MINGW*|MSYS*|CYGWIN*) EXE=".exe";; esac

# nombre|para qué sirve
TOOLS=(
  "nuclei|escáner por plantillas (misconfig, exposiciones, CVEs)"
  "httpx|fingerprint/probe HTTP"
  "ffuf|descubrimiento de contenido / fuzzing"
  "gitleaks|detección de secretos"
  "testssl|auditoría TLS/SSL"
  "sqlmap|SQLi (opt-in, activo)"
  "nikto|escáner de servidor web"
  "wafw00f|detección de WAF"
)

present(){ local t="$1"; [ -x "$BIN/$t$EXE" ] || [ -x "$BIN/$t" ] || command -v "$t" >/dev/null 2>&1; }

inst=(); miss=(); missdesc=()
for row in "${TOOLS[@]}"; do
  name="${row%%|*}"; desc="${row#*|}"
  if present "$name"; then inst+=("$name"); else miss+=("$name"); missdesc+=("$name — $desc"); fi
done

echo "Toolkit dir: $BIN"
echo "Instaladas (${#inst[@]}/${#TOOLS[@]}): ${inst[*]:-—}"
if [ "${#miss[@]}" -gt 0 ]; then
  echo "Faltan (${#miss[@]}):"
  for d in "${missdesc[@]}"; do echo "  - $d"; done
else
  echo "Faltan (0): —  (toolkit completo)"
fi
# machine-readable
echo "INSTALLED:${inst[*]:-}"
echo "MISSING:${miss[*]:-}"
exit "${#miss[@]}"
