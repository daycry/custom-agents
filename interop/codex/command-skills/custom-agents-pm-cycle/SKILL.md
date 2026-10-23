---
name: custom-agents-pm-cycle
description: "Orquesta el ciclo de PRODUCTO de una iniciativa (spec → evaluación) y CIERRA ahí. Separa el rol PM (definir y presupuestar) del rol de desarrollo. Invoca al evaluator por nombre, aplica la puerta go/no-go y, si es go, ofrece el handoff a /dev-cycle sobre la misma carpeta (sin ejecutarlo)."
---
<!-- GENERADO por scripts/export-interop.py desde commands/pm-cycle.md — no lo edites a mano.
     Regenera con `python3 scripts/export-interop.py`; el porqué está en `docs/INTEROP.md`. -->

# Comando /pm-cycle

Invocación explícita: `$custom-agents:custom-agents-pm-cycle <argumentos>`.
Argumentos esperados: `<objetivo o idea de la iniciativa>`.

1. Lee íntegramente `references/command.md`, relativa a esta skill, antes de actuar.
   Si no puedes leerla completa, comunica la limitación y no improvises el workflow.
2. Sigue su adaptación Codex y el comando canónico con sus dueños, puertas y ledger.
3. En su prosa, `$ARGUMENTS` representa los argumentos del mensaje invocante.
   No hay sustitución del compositor de prompts; conserva literalmente los dólares
   de las recetas y resuelve sus variables sólo al ejecutar la shell correspondiente.

| Referencia | Cuándo leerla |
|---|---|
| [Comando completo](references/command.md) | Siempre, antes de ejecutar el comando |
