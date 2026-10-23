---
name: custom-agents-roadmap-brief
description: "Genera un brief ejecutivo de la cartera (one-pager para dirección) combinando estado del roadmap, priorización y métricas real vs estimado, y lo exporta a PDF con aspecto moderno. Solo lee docs/roadmap/. Usa las skills roadmap-dashboard y to-pdf."
---
<!-- GENERADO por scripts/export-interop.py desde commands/roadmap-brief.md — no lo edites a mano.
     Regenera con `python3 scripts/export-interop.py`; el porqué está en `docs/INTEROP.md`. -->

# Comando /roadmap-brief

Invocación explícita: `$custom-agents:custom-agents-roadmap-brief <argumentos>`.
Argumentos esperados: `(opcional) nota o foco para el brief (p. ej. 'cierre de trimestre')`.

1. Lee íntegramente `references/command.md`, relativa a esta skill, antes de actuar.
   Si no puedes leerla completa, comunica la limitación y no improvises el workflow.
2. Sigue su adaptación Codex y el comando canónico con sus dueños, puertas y ledger.
3. En su prosa, `$ARGUMENTS` representa los argumentos del mensaje invocante.
   No hay sustitución del compositor de prompts; conserva literalmente los dólares
   de las recetas y resuelve sus variables sólo al ejecutar la shell correspondiente.

| Referencia | Cuándo leerla |
|---|---|
| [Comando completo](references/command.md) | Siempre, antes de ejecutar el comando |
