---
name: custom-agents-work-resume
description: "Retoma una iniciativa o sesión con el estado actual del ledger y citas del journal local; selecciona identidades exactas y muestra ambigüedad, registros ilegibles e historial incompleto sin iniciar otro ciclo ni modificar el proyecto."
---
<!-- GENERADO por scripts/export-interop.py desde commands/work-resume.md — no lo edites a mano.
     Regenera con `python3 scripts/export-interop.py`; el porqué está en `docs/INTEROP.md`. -->

# Comando /work-resume

Invocación explícita: `$custom-agents:custom-agents-work-resume <argumentos>`.
Argumentos esperados: `[--initiative <carpeta-o-slug>] [--session-id <id>] [--runtime claude|codex|opencode] [--entry <fichero.md>] [--json]`.

1. Lee íntegramente `references/command.md`, relativa a esta skill, antes de actuar.
   Si no puedes leerla completa, comunica la limitación y no improvises el workflow.
2. Sigue su adaptación Codex y el comando canónico con sus dueños, puertas y ledger.
3. En su prosa, `$ARGUMENTS` representa los argumentos del mensaje invocante.
   No hay sustitución del compositor de prompts; conserva literalmente los dólares
   de las recetas y resuelve sus variables sólo al ejecutar la shell correspondiente.

| Referencia | Cuándo leerla |
|---|---|
| [Comando completo](references/command.md) | Siempre, antes de ejecutar el comando |
