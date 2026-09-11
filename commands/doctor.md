---
description: Diagnóstico de la instalación del plugin en este proyecto — herramientas (python3, git, jq, node, Playwright), plugin y hooks registrados, statusline, configs de .claude (rates, dev, jira, confluence) y estado del trabajo (marcadores de medición huérfanos, iniciativas en progreso, memoria técnica —curadas, índice, FTS5, journal, calibración—, evals), con veredicto ✅/⚠️/❌ y el arreglo concreto de cada línea. Solo lee; no toca nada y no usa red. Úsalo cuando el usuario diga "¿está bien instalado?", "diagnostica el plugin", "por qué no funciona el hook", "comprueba mi configuración", "doctor".
argument-hint: "(opcional) --json para la salida en JSON"
---

# /doctor — ¿está todo en su sitio?

Primera parada cuando algo "no salta": el hook que no aparece, la statusline que no se ve, el
coste que sale a 0, la skill que no encuentra su script. Comprueba la instalación **sin tocar
nada** y sin red: cada línea lleva su veredicto y, si algo falla, **qué comando lo arregla**.

## Pasos
1. Localiza el script del kit compartido y ejecútalo:

   ```bash
   DOC="$(find "$PWD/.claude" "$PWD/.codex" "$PWD/.opencode" "$HOME/.claude" "$HOME/.codex" "$HOME/.config/opencode" -type f -path '*agent-kits/shared/doctor.py' 2>/dev/null | head -1)"
   python3 "$DOC"            # informe Markdown · exit 0 sin ❌, 1 con ❌
   python3 "$DOC" --json     # lo mismo para consumo por script
   ```

2. Presenta el informe tal cual y **resume en 2-3 líneas**: cuántos ✅/⚠️/❌ y, si hay ❌, el
   primero con su arreglo. No repitas la tabla en prosa.
3. Si hay ❌ o ⚠️ que el usuario quiera resolver ahora, ofrece el arreglo que indica la propia
   línea (normalmente `/setup`, `rates-verify`, o un `chmod +x`); no lo apliques sin su OK.

## Notas
- **Qué es cada símbolo**: ✅ correcto · ⚠️ funciona pero a medias (opt-in a medio configurar,
  precio de tokens sin verificar, hook no ejecutable) · ❌ roto (config corrupta, valor fuera de
  vocabulario, script que falta) · ℹ️ informativo (opcional no instalado, opt-in apagado a
  propósito, estado del trabajo) — las ℹ️ **no** hay que arreglarlas.
- **Cómo está instalado**, no solo si los ficheros están: el bloque «Plugin» distingue **plugin**
  (registrado en `installed_plugins.json` / `enabledPlugins`, o con la raíz bajo
  `<CLAUDE_CONFIG_DIR>/plugins/cache/`) de **copia** (el bundle en `.claude/`, las vías 1 y 2 de
  `docs/INSTALL.md`). En modo copia, «hooks registrados» es ⚠️ por muy completo que esté
  `hooks/hooks.json`: **Claude Code no lo lee fuera de un plugin instalado**, así que no hay hooks,
  ni statusline, ni namespace `/custom-agents:`; el arreglo es `npx @daycry/custom-agents install
  -p claude-code`. La fila «registro del plugin» dice en qué fichero y scope está dado de alta, y
  es ❌ si `enabledPlugins` lo tiene en `false` (todo en su sitio y Claude Code ignorándolo). Lo
  mismo por runtime, desde fuera de una sesión: `npx @daycry/custom-agents status`.
- **Activo, no «apuntado en algún sitio»**: el veredicto sale del estado EFECTIVO para ESTA
  carpeta — solo la clave exacta del plugin (un `custom-agents@<otro>` no cuenta), las entradas de
  scope `project` o `local` solo si son de este proyecto, y un `false` explícito del nivel que
  manda gana a cualquier alta. `enabledPlugins` se lee en los **cuatro** ficheros de la pila
  documentada (`settings-reference#enabledplugins`: «Scope: Any file»), en el orden de
  `settings#settings-precedence` («Managed > command line > Project local > Shared project >
  User»): `managed-settings.json` de la plataforma > `.claude/settings.local.json` (donde escribe
  `claude plugin disable --scope local`) > `.claude/settings.json` > el `settings.json` de tu
  `CLAUDE_CONFIG_DIR`. La fila **nombra el fichero que manda**, que es donde hay que tocar. Si el
  plugin está instalado pero apagado, la instalación es `inactivo` y los
  hooks **no** pueden salir en ✅. `status` resuelve lo mismo con las mismas reglas: las dos
  herramientas no pueden contradecirse sobre el mismo estado.
- **Los tres runtimes**: además de Claude Code, hay fila para «registro en Codex» (`enabled = true`
  en el `config.toml` del scope) y «registro en OpenCode» (el adaptador de hooks en `plugin` de
  `opencode.json`). Si ese runtime no está en la máquina, la fila es ℹ️ y no pide nada.
- **Seis bloques**: herramientas · plugin y hooks · statusline · configs de `.claude/` · estado del trabajo · **memoria técnica** (`docs/knowledge/`: entradas curadas por familia y estado, índice README —❌ si rompe la biyección—, índice FTS5, journal a 0 con memoria curada, `CALIBRATION.md` desfasada con iniciativas cerradas sin retro — la retro es puerta de cierre desde `memory-retrieval` T-17).
- **Sin red por diseño**: `/doctor` no consulta el marketplace, así que no puede decir si hay una
  versión más nueva del plugin; solo informa de la versión instalada.
- **No confundir con `/setup`**: `/doctor` diagnostica lo que ya hay (solo lectura); `/setup`
  configura y escribe (`rates.json`, `dev.json`, opt-ins de Jira/Confluence, statusline).
