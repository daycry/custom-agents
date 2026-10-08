---
description: >
  Explora el catálogo del plugin en un control panel HTML local: agentes, skills,
  comandos, herramientas declaradas y hooks; incluye extensiones de proyecto y usuario,
  personas y MCP con fuentes y conflictos. Usa plugin-panel; no configura
  servicios ni ejecuta hooks.
argument-hint: "(opcional) ruta de salida HTML"
---

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
ejecución real. Explica los grupos de hooks por runtime/evento, sus handlers,
fuentes y presupuestos; el timeout de registro y la supervisión del adapter
son contratos distintos. Una declaración no acredita carga ni ejecución. Para progreso de iniciativas usa roadmap-dashboard.
