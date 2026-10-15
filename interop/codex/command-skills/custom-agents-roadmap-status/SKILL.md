---
name: custom-agents-roadmap-status
description: "Muestra el estado de todas las iniciativas del roadmap (spec, evaluación, plan, tasks, testing), sus estados, prioridad y presupuesto. Escribe dashboard.md y exporta el panel multi-página a docs/roadmap/panel/. Solo lee docs/roadmap/; no modifica nada. Usa las skills roadmap-dashboard (datos) y plugin-panel (presentación)."
---
<!-- GENERADO por scripts/export-interop.py desde commands/roadmap-status.md — no lo edites a mano.
     Regenera con `python3 scripts/export-interop.py`; el porqué está en `docs/INTEROP.md`. -->

# Comando /roadmap-status

Invocación explícita: `$custom-agents:custom-agents-roadmap-status <argumentos>`.
Argumentos esperados: `(opcional) ruta al roadmap; por defecto docs/roadmap`.

1. Lee íntegramente `references/command.md`, relativa a esta skill, antes de actuar.
   Si no puedes leerla completa, comunica la limitación y no improvises el workflow.
2. Sigue su adaptación Codex y el comando canónico con sus dueños, puertas y ledger.
3. En su prosa, `$ARGUMENTS` representa los argumentos del mensaje invocante.
   No hay sustitución del compositor de prompts; conserva literalmente los dólares
   de las recetas y resuelve sus variables sólo al ejecutar la shell correspondiente.

| Referencia | Cuándo leerla |
|---|---|
| [Comando completo](references/command.md) | Siempre, antes de ejecutar el comando |
