---
name: custom-agents-setup
description: "Onboarding del plugin en un proyecto — en UNA pasada guiada crea la config compartida de presupuesto (.claude/rates.json), decide los opt-ins de Confluence y Jira, ofrece la constitución del proyecto (docs/CONSTITUTION.md), las opciones de disciplina de desarrollo (.claude/dev.json: TDD, worktrees, subagentes), la statusline opt-in (progreso del roadmap + coste de sesión), las lentes condicionales de la revisión adversarial (dev.json revision.lenteSeguridad/lenteRendimiento: auto/siempre/nunca cada una), la cobertura mínima de tests opt-in (dev.json tests.coberturaMinima, skill unit-tests) y el modelo por agente (dev.json modelos, tabla efectiva con model-tier.py), en vez de que cada skill pregunte por su cuenta la primera vez. Idempotente; se puede relanzar para cambiar decisiones."
---
<!-- GENERADO por scripts/export-interop.py desde commands/setup.md — no lo edites a mano.
     Regenera con `python3 scripts/export-interop.py`; el porqué está en `docs/INTEROP.md`. -->

# Comando /setup

Invocación explícita: `$custom-agents:custom-agents-setup <argumentos>`.
Argumentos esperados: `(sin argumentos)`.

1. Lee íntegramente `references/command.md`, relativa a esta skill, antes de actuar.
   Si no puedes leerla completa, comunica la limitación y no improvises el workflow.
2. Sigue su adaptación Codex y el comando canónico con sus dueños, puertas y ledger.
3. En su prosa, `$ARGUMENTS` representa los argumentos del mensaje invocante.
   No hay sustitución del compositor de prompts; conserva literalmente los dólares
   de las recetas y resuelve sus variables sólo al ejecutar la shell correspondiente.

| Referencia | Cuándo leerla |
|---|---|
| [Comando completo](references/command.md) | Siempre, antes de ejecutar el comando |
