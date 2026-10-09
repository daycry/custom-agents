---
description: "Explora el catálogo del plugin en un control panel HTML local: agentes, skills, comandos, herramientas declaradas y hooks; incluye extensiones de proyecto y usuario, personas y MCP con fuentes y conflictos. Usa plugin-panel; no configura servicios ni ejecuta hooks."
argument-hint: "[ruta de salida HTML] [--diagnostics-report informe.json]"
---
<!-- GENERADO por scripts/export-interop.py desde commands/plugin-catalog.md — no lo edites a mano.
     Regenera con `python3 scripts/export-interop.py`; el porqué está en `docs/INTEROP.md`. -->

> **Adaptación a Codex** (fichero generado; la fuente es `commands/plugin-catalog.md`).
> Este comando ORQUESTA agentes. En Codex no hay herramienta Agent: usa `spawn_agent` con `agent_type` igual al ID nativo del rol, si está disponible; las definiciones se copian a `.codex/agents/`.
> En el cuerpo, los roles propios se resuelven con este mapa: analyst → `custom-agents-analyst`; architect → `custom-agents-architect`; documenter → `custom-agents-documenter`; evaluator → `custom-agents-evaluator`; implementer → `custom-agents-implementer`; knowledge-curator → `custom-agents-knowledge-curator`; nemesis → `custom-agents-nemesis`; planner → `custom-agents-planner`; qa → `custom-agents-qa`; reviewer → `custom-agents-reviewer`. Conserva nombres y rutas de agentes del consumidor.
> Las skills se invocan mencionándolas con `$nombre`. Todo lo demás (puertas, artefactos, ledger) no cambia.

# /plugin-catalog — control panel de capacidades

Usa la skill **plugin-panel**. La ruta de salida es **$ARGUMENTS** o una ruta
local acordada para el artefacto. El script no reemplaza archivos ajenos.
Si los argumentos incluyen `--diagnostics-report`, separa esa opción de la ruta
de salida y pásala al generador con la raíz explícita del mismo proyecto. Usa
una lista de argumentos, sin interpolar texto del usuario en shell ni eval.
No ejecutes doctor ni busques informes automáticamente para completar la vista.

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
ejecución real. Explica los grupos de hooks por runtime/evento, sus handlers,
fuentes y presupuestos; el timeout de registro y la supervisión del adapter
son contratos distintos. Una declaración no acredita carga ni ejecución. Para progreso de iniciativas usa roadmap-dashboard.
El diagnóstico importado es una instantánea histórica: explica fecha, alcance,
formato rechazado, antigüedad o recorte. No cambia los estados de los hooks.
Para el detalle y los arreglos conserva /doctor como dueño de la comprobación.
