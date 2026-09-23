---
description: Diagnóstico de la instalación del plugin en este proyecto — herramientas (python3, git, jq, node, Playwright), plugin y hooks registrados, statusline, configs de .claude (rates, dev, jira, confluence) y estado del trabajo (marcadores de medición huérfanos, iniciativas en progreso, memoria técnica —curadas, índice, FTS5, journal, calibración—, evals), con veredicto ✅/⚠️/❌ y el arreglo concreto de cada línea. Solo lee; no toca nada. Sin red salvo la comprobación en vivo de capacidades opcionales activadas en `taxonomy.json` (p. ej. `kwipu`), acotada a hosts locales/privados y a un tope total de tiempo. Úsalo cuando el usuario diga "¿está bien instalado?", "diagnostica el plugin", "por qué no funciona el hook", "comprueba mi configuración", "doctor".
argument-hint: "(opcional) --json para la salida en JSON · --verbose para ver también las capacidades opt-in sin configurar"
---

# /doctor — ¿está todo en su sitio?

Primera parada cuando algo "no salta": el hook que no aparece, la statusline que no se ve, el
coste que sale a 0, la skill que no encuentra su script. Comprueba la instalación **sin tocar
nada**: cada línea lleva su veredicto y, si algo falla, **qué comando lo arregla**.

## Pasos
1. Localiza el script del kit compartido y ejecútalo:

   ```bash
   DOC="$(find "$PWD/.claude" "$PWD/.codex" "$PWD/.opencode" "$HOME/.claude" "$HOME/.codex" "$HOME/.config/opencode" -type f -path '*agent-kits/shared/doctor.py' 2>/dev/null | head -1)"
   python3 "$DOC"            # informe Markdown · exit 0 sin ❌, 1 con ❌
   python3 "$DOC" --json     # lo mismo para consumo por script
   python3 "$DOC" --verbose  # incluye las capacidades opt-in sin su fichero de config (alias --all)
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
- **Cómo se teclea el comando** (hueco E5): la fila «nombre de los comandos» dice la forma que
  funciona en ESTA instalación, con **tres** textos según el modo detectado y siempre en ℹ️ (no hay
  nada que arreglar: hay que saber qué se teclea). `plugin` → el nombre real lleva el espacio de
  nombres, `/custom-agents:<cmd>`, y la forma corta da «Unknown command». `copia` (bundle en
  `.claude/`) → forma corta `/<cmd>`, y se avisa de que `/custom-agents:<cmd>` solo existe
  instalado como plugin. `inactivo`/`desconocido` (dado de alta pero deshabilitado, o sin poder
  determinarlo) → las **dos** formas con su condición, para no afirmar la que no toca. Si el
  `plugin_root` no tiene carpeta `commands/` (instalación truncada), la fila lo dice y no nombra
  ningún comando en vez de inventar uno. El espacio de nombres es de **Claude Code**: en Codex el
  mismo comando es un prompt `/<cmd>` sin prefijo y en OpenCode un comando sin prefijo, y la fila
  lo menciona para no dar por hecho el runtime. La ⚠️ «doc viva sin el espacio de nombres» solo
  salta si la **primera** mención de un comando en un fichero de documentación **viva**
  (`README.md`, `README.es.md`, `docs/INSTALL.md`, `docs/README.md`, sus espejos en `docs/en/` y
  `CLAUDE.md`) va en forma corta: una nota al pie decenas de líneas más abajo no la satisface,
  porque quien teclea lo hace antes de llegar a ella. Los registros fechados (`docs/roadmap/`,
  `docs/knowledge/`, CHANGELOG) no se miran: quedan como se escribieron.
- **Ocho bloques**: herramientas · plugin y hooks · statusline · configs de `.claude/` · estado del trabajo · **capacidades opcionales** (`agent-kits/shared/capabilities.py`, T-09/T-13, CA-14: una fila por capacidad registrada —hoy el Knowledge Gate y, si el proyecto lo declara, un backend de `knowledge-services`— SIN código específico por capacidad; config inválida → ❌ con fichero+campo+arreglo, desactivada → ℹ️ —y **omitida** si su `config_path` no existe en el proyecto (regla genérica: un opt-in sin configurar no pinta nada; `--verbose`/`--all` la muestra)—, activa con backend declarado → comprobación de red EN VIVO vía SU adaptador —✅ sano sin desfase, ⚠️ export atrasado con el remedio que nombra `verify()` [nunca lo ejecuta], ⚠️/❌ degradado/error, ℹ️ sin conexión o timeout— y sin backend, el texto genérico de la propia capacidad) · **memoria técnica** (`docs/knowledge/`: entradas curadas por familia y estado, índice README —❌ si rompe la biyección—, índice FTS5, journal a 0 con memoria curada, `CALIBRATION.md` desfasada con iniciativas cerradas sin retro — la retro es puerta de cierre desde `memory-retrieval` T-17) · **Journal** (session-end-durable-capture T-06: lee `journal.py status --json` — contadores outbox/processing/done/dead-letter, huérfanas, backoff pendiente con el remedio nombrado, y triage del «Hook cancelled»: aviso del runtime sin pérdida vs. pérdida posible).
- **La versión del plugin es sin red por diseño**: `/doctor` no consulta el marketplace, así que
  no puede decir si hay una versión más nueva del plugin; solo informa de la versión instalada.
  (Esto NO es una afirmación general de "sin red": las capacidades opcionales activadas en
  `taxonomy.json`, ver «ocho bloques» arriba, sí hacen una comprobación en vivo acotada a hosts
  locales/privados y a un tope total de tiempo.)
- **No confundir con `/setup`**: `/doctor` diagnostica lo que ya hay (solo lectura); `/setup`
  configura y escribe (`rates.json`, `dev.json`, opt-ins de Jira/Confluence, statusline).
