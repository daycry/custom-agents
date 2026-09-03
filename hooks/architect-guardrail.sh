#!/usr/bin/env bash
# Hook PreToolUse DE GUARDIA del agente `architect` (Write|Edit|MultiEdit|NotebookEdit|Bash).
# Registrado SOLO en el frontmatter `hooks:` de agents/architect.md — NUNCA en hooks/hooks.json
# (ADR-007 + enmienda parity-core: mismo patrón que el implementer, alcance propio).
# Alcance (decide agent-kits/shared/guardrail-check.py --agent architect, con tests):
#   permitido  docs/roadmap/<inic>/design.md · docs/knowledge/adr/** · docs/knowledge/README.md ·
#              spec.md / improvement-plan.md SOLO con Edit y si el Edit contiene `design:`/`design.md`
#   deny       todo lo demás (código, tasks.md, evaluation.md, gotchas/lessons, security-scan) y git destructivo
# Degradación: sin python3 → NO bloquea (aviso una vez). Desactivable en .claude/dev.json → guardrails.
set -u
GUARDRAIL_AGENT=architect exec bash "$(dirname "${BASH_SOURCE[0]}")/implementer-guardrail.sh"
