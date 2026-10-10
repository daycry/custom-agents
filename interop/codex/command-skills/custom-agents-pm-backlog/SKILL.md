---
name: custom-agents-pm-backlog
description: "Rol PM de cartera. Lee todas las evaluaciones del roadmap (docs/roadmap/*/evaluation.md) y produce un backlog PRIORIZADO cross-iniciativa (quick wins vs. costosas) en docs/roadmap/BACKLOG.md, para decidir el orden de ejecución. No planifica ni implementa; solo lee y prioriza."
---
<!-- GENERADO por scripts/export-interop.py desde commands/pm-backlog.md — no lo edites a mano.
     Regenera con `python3 scripts/export-interop.py`; el porqué está en `docs/INTEROP.md`. -->

# Comando /pm-backlog

Invocación explícita: `$custom-agents:custom-agents-pm-backlog <argumentos>`.
Argumentos esperados: `(opcional) criterio de priorización, p. ej. 'maximizar valor por € este trimestre'`.

1. Lee íntegramente `references/command.md`, relativa a esta skill, antes de actuar.
   Si no puedes leerla completa, comunica la limitación y no improvises el workflow.
2. Sigue su adaptación Codex y el comando canónico con sus dueños, puertas y ledger.
3. En su prosa, `$ARGUMENTS` representa los argumentos del mensaje invocante.
   No hay sustitución del compositor de prompts; conserva literalmente los dólares
   de las recetas y resuelve sus variables sólo al ejecutar la shell correspondiente.

| Referencia | Cuándo leerla |
|---|---|
| [Comando completo](references/command.md) | Siempre, antes de ejecutar el comando |
