---
id: ADR-007
titulo: Un hook de guardia (deny) solo vive en el frontmatter `hooks:` de un agente, nunca en `hooks/hooks.json`
estado: aceptada (validada: revisión de dos lentes, 2026-09-02, intento 2)
fecha: 2026-09-02
iniciativa: 2026-09-02-deterministic-guardrails
---

# ADR-007: Un hook de guardia (deny) solo vive en el frontmatter `hooks:` de un agente, nunca en `hooks/hooks.json`

## Contexto

Los guardrails duros del `implementer` («en `docs/roadmap/` solo `tasks.md`», «trabaja en rama», «sin `git push --force`») vivían en prosa y se cumplían si el modelo los recordaba. Al pasarlos a un hook `PreToolUse` determinista con `permissionDecision: deny` había que decidir DÓNDE registrarlo: el plugin ya tiene `hooks/hooks.json` global (informativos, siempre exit 0), pero las mismas rutas que el implementer no debe tocar (`docs/roadmap/**`) las escriben `planner`, `evaluator`, `analyst` y los comandos de forma legítima.

## Decisión

Un hook que **deniega** se registra **únicamente en el frontmatter `hooks:` del agente** al que restringe (alcance del subagente: Claude Code lo activa solo mientras corre ese agente), con la decisión en un **script determinista con tests** (`agent-kits/shared/guardrail-check.py`), razón en una frase con cómo proceder, desactivable en `.claude/dev.json` y con degradación sin bloqueo (sin `python3` → aviso único y exit 0; error interno → allow). `hooks/hooks.json` queda reservado a hooks **informativos** (`systemMessage`/`additionalContext`, exit 0); el linter no permite comprobarlo semánticamente, así que la regla vive en `docs/CONVENTIONS.md` regla 8 y en `skills/plugin-dev/SKILL.md` (Paso 0).

## Alternativas descartadas

- **Deny global en `hooks/hooks.json` filtrando por `agent_type` del stdin** — el hook global corre también en la sesión principal (sin `agent_type`) y en todos los demás agentes; una decisión por rol dentro de un script global es frágil (un `agent_type` nuevo o vacío bloquearía a planner/evaluator) y contradice el principio «los hooks globales informan, no deciden».
- **`isolation: worktree` nativo del subagente como sustituto de la regla de rama** — ramifica desde la rama por defecto (no desde `feature/<slug>`) y lo limpia Claude Code; choca con el opt-in `worktree` de `dev.json` (worktree único por iniciativa integrado por el ritual de la Fase 6) y no cubre alcance ni git destructivo.
- **Exit 2 con stderr** en vez de JSON `deny` — funciona, pero mezcla «bloqueo» con «error del script»: un fallo interno del guardrail se convertiría en bloqueo fantasma. Con JSON + exit 0, un error interno solo puede permitir.

## Consecuencias

Cada agente que necesite reglas duras las declara en su propio frontmatter y reutiliza el patrón (wrapper en `hooks/` + script en `agent-kits/shared/` con tests); el resto de agentes no cambian de comportamiento. El linter valida que cada skill de `skills:` esté en `dependencies.skills` y que los `command` de `hooks:` referencien ficheros existentes. Queda condicionado a la doc oficial: `${CLAUDE_PLUGIN_ROOT}` no está documentado para los `command` del frontmatter, por lo que la línea del hook lleva fallback `find`.

## Enmienda (2026-09-03, iniciativa `parity-core`, T-fix1)

El patrón se extiende a un **segundo agente** sin cambiar la decisión: `agents/architect.md` registra en su
frontmatter `hooks:` el wrapper `hooks/architect-guardrail.sh`, que reutiliza el MISMO script con
`guardrail-check.py --agent architect` (alcance propio: solo `docs/roadmap/<inic>/design.md`,
`docs/knowledge/adr/**` + `README.md`, y `spec.md`/`improvement-plan.md` únicamente con `Edit` que contenga
`design:`; git destructivo igual; sin regla de rama principal). El selector de reglas es explícito
(`--agent`, o `CLAUDE_AGENT_NAME` si el entorno lo define), nunca inferido del stdin global — la
alternativa descartada «deny global filtrando por `agent_type`» sigue descartada. Riesgo documentado: el
hook no puede diffear un `Edit`, así que un Edit de spec/plan que incluya `design:` junto a otros cambios
pasa; lo caza la Lente A. Tests: `agent-kits/shared/test_guardrail_check.py` (modo architect) y
`tests/test_hooks_shell.py` (`architect-guardrail.sh`).

## Estado

`propuesta` — a validar por la revisión de dos lentes o el usuario en la puerta. Pasa a `aceptada` cuando se valida; a `obsoleta` si una decisión posterior la reemplaza (enlaza aquí a la que la sustituye, nunca se borra el rastro).
