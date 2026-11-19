# Verificar una pieza nueva con el inventario del proyecto

Léela en el Paso 3, tras escribir la pieza. `project-pieces.py` lee las declaraciones locales del
proyecto (y, si no pasas `--project-only`, las del usuario) **sin ejecutar** nada ni contactar con
servidores. Es el mismo lector que usan `/work-context` y el panel del plugin.

## Localizar el script

Viene con el plugin, no con el proyecto: se resuelve en tiempo de ejecución sobre las seis raíces
habituales (proyecto y usuario, para `.claude`, `.codex` y `.opencode`), nunca con una ruta fija:

```bash
R="${CLAUDE_PLUGIN_ROOT}"; M=agent-kits/shared/ledger-lint.py; [ -f "$R/$M" ] || R="$(for r in "$PWD"/.{claude,codex,opencode} ~/.{claude,codex}/plugins/cache/daycry ~/.{claude,codex,config/opencode}; do find "$r" -maxdepth 5 -path "*/$M" ! -path "$r/jobs/*" ! -path "$r/worktrees/*" 2>/dev/null | sort -V | tail -1 | grep . && break; done)"; R="${R%/$M}"; PIECES="${R:+$R/agent-kits/shared/project-pieces.py}"
python3 "$PIECES" --project . --project-only --json
```

Sin el script (instalación parcial o paquete portable sin los kits compartidos): avisa y revisa a mano
que el fichero está en la carpeta de la tabla de `SKILL.md`, con su frontmatter y sin placeholders;
nunca bloquees la entrega por esto.

## Qué mirar en la salida

- `pieces`: una entrada por declaración, con `runtime` (`claude-code`, `codex` u `opencode`), `kind`
  (`agent`, `skill`, `command`, `mcp`, `tool-source`), `name` y `source`. La pieza nueva tiene que
  aparecer para cada runtime elegido.
- `warnings`: debe quedar **vacío**. Cada aviso trae su causa (frontmatter inválido, campo desconocido,
  enlace inseguro, conflicto de nombre).
- `conflicts`: dos piezas con el mismo nombre en un mismo runtime; no se inventa precedencia, elige un
  nombre distinto.
- `partial: true` indica inventario incompleto: no lo des por bueno.

Filtros útiles: `--runtime claude-code|codex|opencode`, `--select <id>` para una sola pieza y
`--user-root <runtime>=<ruta>` para una raíz personal que no sea la habitual.

## Lo que NO prueba

Que la sesión del runtime la haya cargado, conectado o autorizado: eso lo decide el runtime. Tras
crear o editar una pieza, reinicia la sesión (o recarga el runtime) y pruébala con una petición real
que debería activarla.
