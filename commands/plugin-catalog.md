---
description: >
  Explora el catálogo del plugin en un control panel HTML local: agentes, skills,
  comandos, herramientas declaradas y hooks. Usa plugin-panel; no configura
  servicios ni ejecuta hooks.
argument-hint: "(opcional) ruta de salida HTML"
---

# /plugin-catalog — control panel de capacidades

Usa la skill **plugin-panel**. La ruta de salida es **$ARGUMENTS** o una ruta
local acordada para el artefacto. El script no reemplaza archivos ajenos.

```bash
PANEL="$(find "$PWD/.claude" "$PWD/.codex" "$PWD/.opencode" "$HOME/.claude" "$HOME/.codex" "$HOME/.config/opencode" -type f -path '*skills/plugin-panel/scripts/build_panel.py' 2>/dev/null | head -1)"
# En el checkout, el script está también en skills/plugin-panel/scripts/.
python3 "$PANEL" --html "<salida.html>"
```

En Windows usa el Python nativo disponible. El script identifica el bundle
por su ubicación; `--root` sirve para inspeccionar otro bundle sin importar su
código. Si falta el script o su redactor, informa y sigue la tarea del usuario.
Entrega el fichero generado y distingue catálogo, presencia de fuente y
ejecución real. Para progreso de iniciativas usa roadmap-dashboard.
