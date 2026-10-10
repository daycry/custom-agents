---
name: custom-agents-plugin-catalog
description: "Explora el catálogo del plugin en un control panel HTML local: agentes, skills, comandos, herramientas declaradas y hooks; incluye extensiones de proyecto y usuario, personas y MCP con fuentes y conflictos. Usa plugin-panel; no configura servicios ni ejecuta hooks. El modo --serve abre un dashboard local con progreso actualizado desde el ledger y consulta local de memoria bajo demanda, sin dirigir agentes ni conectar backends."
---
<!-- GENERADO por scripts/export-interop.py desde commands/plugin-catalog.md — no lo edites a mano.
     Regenera con `python3 scripts/export-interop.py`; el porqué está en `docs/INTEROP.md`. -->

# Comando /plugin-catalog

Invocación explícita: `$custom-agents:custom-agents-plugin-catalog <argumentos>`.
Argumentos esperados: `[ruta de salida HTML] [--diagnostics-report informe.json] [--serve] [--port PUERTO]`.

1. Lee íntegramente `references/command.md`, relativa a esta skill, antes de actuar.
   Si no puedes leerla completa, comunica la limitación y no improvises el workflow.
2. Sigue su adaptación Codex y el comando canónico con sus dueños, puertas y ledger.
3. En su prosa, `$ARGUMENTS` representa los argumentos del mensaje invocante.
   No hay sustitución del compositor de prompts; conserva literalmente los dólares
   de las recetas y resuelve sus variables sólo al ejecutar la shell correspondiente.

| Referencia | Cuándo leerla |
|---|---|
| [Comando completo](references/command.md) | Siempre, antes de ejecutar el comando |
