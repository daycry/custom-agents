---
name: custom-agents-knowledge-category-check
description: "Revisa documentos de una categoría del proyecto contra sus campos, secciones y origen permitido. No modifica originales; con petición explícita prepara candidatos para curación. Úsalo cuando el usuario diga \"revisa la categoría meetings\", \"comprueba el formato de las FAQ\" o \"check de categoría\"."
---
<!-- GENERADO por scripts/export-interop.py desde commands/knowledge-category-check.md — no lo edites a mano.
     Regenera con `python3 scripts/export-interop.py`; el porqué está en `docs/INTEROP.md`. -->

# Comando /knowledge-category-check

Invocación explícita: `$custom-agents:custom-agents-knowledge-category-check <argumentos>`.
Argumentos esperados: `<categoría> [--origin human|agent] [--propose]`.

1. Lee íntegramente `references/command.md`, relativa a esta skill, antes de actuar.
   Si no puedes leerla completa, comunica la limitación y no improvises el workflow.
2. Sigue su adaptación Codex y el comando canónico con sus dueños, puertas y ledger.
3. En su prosa, `$ARGUMENTS` representa los argumentos del mensaje invocante.
   No hay sustitución del compositor de prompts; conserva literalmente los dólares
   de las recetas y resuelve sus variables sólo al ejecutar la shell correspondiente.

| Referencia | Cuándo leerla |
|---|---|
| [Comando completo](references/command.md) | Siempre, antes de ejecutar el comando |
