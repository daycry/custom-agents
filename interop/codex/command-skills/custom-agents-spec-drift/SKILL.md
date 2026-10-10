---
name: custom-agents-spec-drift
description: "Detecta la DERIVA entre las specs implementadas y el código actual (el /speckit.analyze del plugin) — por cada spec `implementada`, subagentes de contexto fresco verifican cada criterio de aceptación contra el código de HOY y emiten veredicto vigente/derivado/no-verificable con evidencia. Escribe docs/roadmap/DRIFT.md y ofrece abrir iniciativa para lo derivado. Solo lectura del código."
---
<!-- GENERADO por scripts/export-interop.py desde commands/spec-drift.md — no lo edites a mano.
     Regenera con `python3 scripts/export-interop.py`; el porqué está en `docs/INTEROP.md`. -->

# Comando /spec-drift

Invocación explícita: `$custom-agents:custom-agents-spec-drift <argumentos>`.
Argumentos esperados: `(opcional) <slug> — sin argumento revisa TODAS las specs implementadas`.

1. Lee íntegramente `references/command.md`, relativa a esta skill, antes de actuar.
   Si no puedes leerla completa, comunica la limitación y no improvises el workflow.
2. Sigue su adaptación Codex y el comando canónico con sus dueños, puertas y ledger.
3. En su prosa, `$ARGUMENTS` representa los argumentos del mensaje invocante.
   No hay sustitución del compositor de prompts; conserva literalmente los dólares
   de las recetas y resuelve sus variables sólo al ejecutar la shell correspondiente.

| Referencia | Cuándo leerla |
|---|---|
| [Comando completo](references/command.md) | Siempre, antes de ejecutar el comando |
