---
description: "Explora el catálogo del plugin en un control panel HTML local: agentes, skills, comandos, herramientas declaradas y hooks; incluye extensiones de proyecto y usuario, personas y MCP con fuentes y conflictos. Usa plugin-panel; no configura servicios ni ejecuta hooks."
---
<!-- GENERADO por scripts/export-interop.py desde commands/plugin-catalog.md — no lo edites a mano.
     Regenera con `python3 scripts/export-interop.py`; el porqué está en `docs/INTEROP.md`. -->

> **Adaptación a OpenCode** (fichero generado; la fuente es `commands/plugin-catalog.md`).
> Este comando ORQUESTA agentes. En OpenCode no hay herramienta Agent: usa `subagent` con el campo `agent` igual al ID nativo, definido en `.opencode/agents/`.
> En el cuerpo, los roles propios se resuelven con este mapa: analyst → `custom-agents-analyst`; architect → `custom-agents-architect`; documenter → `custom-agents-documenter`; evaluator → `custom-agents-evaluator`; implementer → `custom-agents-implementer`; knowledge-curator → `custom-agents-knowledge-curator`; nemesis → `custom-agents-nemesis`; planner → `custom-agents-planner`; qa → `custom-agents-qa`; reviewer → `custom-agents-reviewer`. Conserva nombres y rutas de agentes del consumidor.
> Las skills se invocan con la herramienta `skill` (`skill({ name: "nombre" })`). Todo lo demás (puertas, artefactos, ledger) no cambia.

# /plugin-catalog — control panel de capacidades

Usa la skill **plugin-panel**. La ruta de salida es **$ARGUMENTS** o una ruta
local acordada para el artefacto. El script no reemplaza archivos ajenos.

```bash
PANEL="$(find "$PWD/.claude" "$PWD/.codex" "$PWD/.opencode" "$HOME/.claude" "$HOME/.codex" "$HOME/.config/opencode" -type f -path '*skills/plugin-panel/scripts/build_panel.py' 2>/dev/null | head -1)"
# En el checkout, el script está también en skills/plugin-panel/scripts/.
python3 "$PANEL" --project "<raíz-proyecto>" --runtime <claude-code|codex|opencode> --html "<salida.html>"
```

En Windows usa el Python nativo disponible. El script identifica el bundle
por su ubicación; `--root` sirve para inspeccionar otro bundle sin importar su
código. Si falta el script o su redactor, informa y sigue la tarea del usuario.
Para un paquete anidado pasa `--cwd`; para excluir piezas personales,
`--project-only`. Raíces personalizadas requieren `--user-root <runtime>=<ruta>`.
Elige el runtime real de la sesión; `all` sirve para comparar declaraciones
entre entornos. El panel separa el bundle y las extensiones. Un fallo del lector
de extensiones conserva el catálogo del bundle con aviso. No modifica, adopta
ni ejecuta las piezas encontradas; contrasta disponibilidad antes de invocarlas.
Entrega el fichero generado y distingue catálogo, presencia de fuente y
ejecución real. Para progreso de iniciativas usa roadmap-dashboard.
