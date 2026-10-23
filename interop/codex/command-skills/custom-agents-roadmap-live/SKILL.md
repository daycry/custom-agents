---
name: custom-agents-roadmap-live
description: "Abre un dashboard VIVO del estado del roadmap leyendo Jira en tiempo real (issues + horas imputadas por label). En Cowork/escritorio como artefacto interactivo; en CLI/VS Code como resumen conversacional. Requiere el conector Atlassian y que el plan se haya volcado con jira-sync. Usa la skill roadmap-dashboard."
---
<!-- GENERADO por scripts/export-interop.py desde commands/roadmap-live.md — no lo edites a mano.
     Regenera con `python3 scripts/export-interop.py`; el porqué está en `docs/INTEROP.md`. -->

# Comando /roadmap-live

Invocación explícita: `$custom-agents:custom-agents-roadmap-live <argumentos>`.
Argumentos esperados: `(opcional) <slug> de una iniciativa; por defecto toda la cartera (label 'roadmap')`.

1. Lee íntegramente `references/command.md`, relativa a esta skill, antes de actuar.
   Si no puedes leerla completa, comunica la limitación y no improvises el workflow.
2. Sigue su adaptación Codex y el comando canónico con sus dueños, puertas y ledger.
3. En su prosa, `$ARGUMENTS` representa los argumentos del mensaje invocante.
   No hay sustitución del compositor de prompts; conserva literalmente los dólares
   de las recetas y resuelve sus variables sólo al ejecutar la shell correspondiente.

| Referencia | Cuándo leerla |
|---|---|
| [Comando completo](references/command.md) | Siempre, antes de ejecutar el comando |
