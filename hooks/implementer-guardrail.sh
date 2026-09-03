#!/usr/bin/env bash
# Hook PreToolUse DE GUARDIA del agente `implementer` (Write|Edit|MultiEdit|NotebookEdit|Bash).
# Registrado SOLO en el frontmatter `hooks:` de agents/implementer.md — NUNCA en hooks/hooks.json
# (planner/evaluator/analyst escriben en docs/roadmap/ legítimamente; ADR-007).
# Reutilizado por hooks/architect-guardrail.sh con GUARDRAIL_AGENT=architect (mismo script,
# reglas del architect: solo design.md + enlace design: en spec/plan + docs/knowledge/adr/).
#
# Delega la decisión en agent-kits/shared/guardrail-check.py (determinista, con tests):
#   deny  → JSON oficial {"hookSpecificOutput":{"permissionDecision":"deny",…}} · exit 0
#   allow → sin stdout · exit 0
# Degradación: sin python3 → NO bloquea (exit 0) y avisa por systemMessage UNA vez por
# proyecto (marca ${CLAUDE_PROJECT_DIR:-$PWD}/.claude/.guardrail-nopython). Desactivable en
# .claude/dev.json → "guardrails": false | {"alcance","git","ramaPrincipal"}.
set -u

AGENT="${GUARDRAIL_AGENT:-implementer}"
INPUT="$(cat 2>/dev/null || true)"
PROJ="${CLAUDE_PROJECT_DIR:-$PWD}"

if ! command -v python3 >/dev/null 2>&1; then
  MARK="$PROJ/.claude/.guardrail-nopython"
  if [ ! -e "$MARK" ]; then
    mkdir -p "$PROJ/.claude" 2>/dev/null && : > "$MARK" 2>/dev/null
    printf '{"systemMessage": "⚠️ guardrails del %s sin efecto: no hay python3 en PATH (alcance docs/roadmap/, rama y git NO se comprueban en esta sesión)."}\n' "$AGENT"
  fi
  exit 0
fi

# Localizar guardrail-check.py: junto al plugin, después por find (mismo patrón que el resto de hooks).
CHECK="${CLAUDE_PLUGIN_ROOT:-}/agent-kits/shared/guardrail-check.py"
if [ ! -f "$CHECK" ]; then
  CHECK="$(dirname "${BASH_SOURCE[0]}")/../agent-kits/shared/guardrail-check.py"
fi
if [ ! -f "$CHECK" ]; then
  CHECK="$(find "$PROJ/.claude" "${HOME:-}/.claude" -type f -path '*agent-kits/shared/guardrail-check.py' 2>/dev/null | head -1)"
fi
[ -n "$CHECK" ] && [ -f "$CHECK" ] || exit 0

printf '%s' "$INPUT" | CLAUDE_PROJECT_DIR="$PROJ" python3 "$CHECK" pre-tool --agent "$AGENT" 2>/dev/null || true
exit 0
