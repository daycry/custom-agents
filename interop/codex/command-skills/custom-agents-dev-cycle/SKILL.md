---
name: custom-agents-dev-cycle
description: "Orquesta el ciclo completo de una iniciativa (spec → evaluación → plan → implementación → pruebas → documentación) con la cadena nativa del plugin como único motor (autosuficiente: TDD, worktrees, subagentes frescos y debugging sistemático opt-in). Invoca los agentes por nombre y con puertas de control."
---
<!-- GENERADO por scripts/export-interop.py desde commands/dev-cycle.md — no lo edites a mano.
     Regenera con `python3 scripts/export-interop.py`; el porqué está en `docs/INTEROP.md`. -->

# Comando /dev-cycle

Invocación explícita: `$custom-agents:custom-agents-dev-cycle <argumentos>`.
Argumentos esperados: `<objetivo de la iniciativa> [rapido | completo]`.

1. Lee íntegramente `references/command.md`, relativa a esta skill, antes de actuar.
   Si no puedes leerla completa, comunica la limitación y no improvises el workflow.
2. Sigue su adaptación Codex y el comando canónico con sus dueños, puertas y ledger.
3. En su prosa, `$ARGUMENTS` representa los argumentos del mensaje invocante.
   No hay sustitución del compositor de prompts; conserva literalmente los dólares
   de las recetas y resuelve sus variables sólo al ejecutar la shell correspondiente.

| Referencia | Cuándo leerla |
|---|---|
| [Comando completo](references/command.md) | Siempre, antes de ejecutar el comando |
