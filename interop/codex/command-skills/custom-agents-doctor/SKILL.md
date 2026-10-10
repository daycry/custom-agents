---
name: custom-agents-doctor
description: "Diagnóstico de la instalación del plugin en este proyecto — herramientas (python3, git, jq, node, Playwright), plugin y hooks registrados, statusline, configs de .claude (rates, dev, jira, confluence) y estado del trabajo (marcadores de medición huérfanos, iniciativas en progreso, memoria técnica —curadas, índice, FTS5, journal, calibración—, evals), con veredicto ✅/⚠️/❌ y el arreglo concreto de cada línea. Solo lee; no toca nada. Sin red salvo la comprobación en vivo de capacidades opcionales activadas en `taxonomy.json`, acotada a hosts locales/privados y a un tope total de tiempo (p. ej. `kwipu` o la memoria de grafo `graphiti`). Úsalo cuando el usuario diga \"¿está bien instalado?\", \"diagnostica el plugin\", \"por qué no funciona el hook\", \"comprueba mi configuración\", \"doctor\"."
---
<!-- GENERADO por scripts/export-interop.py desde commands/doctor.md — no lo edites a mano.
     Regenera con `python3 scripts/export-interop.py`; el porqué está en `docs/INTEROP.md`. -->

# Comando /doctor

Invocación explícita: `$custom-agents:custom-agents-doctor <argumentos>`.
Argumentos esperados: `(opcional) --json · --panel-json para el panel · --verbose para las capacidades opt-in sin configurar`.

1. Lee íntegramente `references/command.md`, relativa a esta skill, antes de actuar.
   Si no puedes leerla completa, comunica la limitación y no improvises el workflow.
2. Sigue su adaptación Codex y el comando canónico con sus dueños, puertas y ledger.
3. En su prosa, `$ARGUMENTS` representa los argumentos del mensaje invocante.
   No hay sustitución del compositor de prompts; conserva literalmente los dólares
   de las recetas y resuelve sus variables sólo al ejecutar la shell correspondiente.

| Referencia | Cuándo leerla |
|---|---|
| [Comando completo](references/command.md) | Siempre, antes de ejecutar el comando |
