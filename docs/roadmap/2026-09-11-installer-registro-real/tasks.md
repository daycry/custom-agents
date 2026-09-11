---
tasks: installer-registro-real
descripcion: >
  El instalador `npx @daycry/custom-agents` no instala el plugin: en Claude Code copia el bundle a `.claude/`
  (los hooks de `hooks/hooks.json` no se registran, no hay namespace `/custom-agents:`, ni statusline, ni
  actualizaciones; `/doctor` da un falso positivo «hooks registrados ✅» porque solo mira que los ficheros
  existan), en Codex copia el plugin y el marketplace pero nunca lo HABILITA (`codex plugin marketplace add`
  + `enabled = true` en `config.toml`), y en OpenCode copia el adaptador de hooks sin registrarlo en
  `opencode.json` `plugin`. La experiencia tampoco es la esperada: sin título y con menú por números en vez
  de checkboxes. Referencia del usuario: el instalador de `thedotmack/claude-mem` (banner, `multiselect`,
  registro real en `known_marketplaces.json` + `installed_plugins.json` + `enabledPlugins`, `CodexCliInstaller`).
  Reproducido por el orquestador el 2026-09-11 en un HOME temporal y contrastado con la doc oficial de
  Claude Code (hooks de proyecto solo en `settings.json`; `claude plugin marketplace add` / `claude plugin
  install` no interactivos) y de Codex (plugins cargados desde `~/.codex/plugins/cache/` tras habilitarlos).
estado: en-progreso       # borrador | en-progreso | completado | cancelado
creado: 2026-09-11
actualizado: 2026-09-11
via: rapida               # vía rápida de /dev-cycle: sin spec/evaluación/plan; conserva verificación + revisión de dos lentes
changelog: Fixed
verificacion: obligatoria # cada `### T-XX` lleva `- **Verificación**:`; ledger-lint lo exige
test-plan: n/a (sin UI)   # ADR-017: instalador CLI + scripts; la verificación en runtimes reales es la checklist M-01
generacion:
  inicio: 2026-09-11T03:10:56Z
  fin: 2026-09-11T03:14:29Z
  fuente: medido
  tokens_reales: {"entrada": 97, "salida": 17657, "cache_creacion": 23795, "cache_lectura": 1068975, "respuestas": 3}
  eur: 1.04
  horas_ia: 0.09
  duracion_reloj: 4m
  ratio_usado: 479326.0
---

# Checklist de Tareas — installer-registro-real (vía rápida)

| | |
|---|---|
| **Estado** | en-progreso |
| **Fecha** | 2026-09-11 |
| **Plan** | n/a — **vía rápida** (sin spec/evaluación/plan; ledger ligero + verificación + revisión de dos lentes) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del cambio.

> **Origen.** El usuario probó `npx @daycry/custom-agents` y en Claude Code y Codex «no parece que se haya instalado
> correctamente»; comparó con `claude-mem` (título en consola, proveedores seleccionables con checkboxes). El
> orquestador reprodujo la instalación en un HOME temporal (`install -p claude-code,codex -y`): 221 ficheros copiados a
> `.claude/` y a `.codex/plugins/custom-agents/`, `/doctor` del plugin diciendo «hooks registrados ✅», y ningún registro
> en los ficheros que los runtimes leen de verdad. Diagnóstico y referencias: sección «Decisiones cerradas» abajo.
> **Fuera de alcance:** volver a exportar piezas (`export-interop.py` no cambia); soporte a runtimes nuevos; la
> verificación de punta a punta en Codex y OpenCode (en esta máquina no hay `codex` ni `opencode`: la hace el usuario
> con la checklist **M-01**).

---

## Decisiones cerradas (vía rápida: aquí en vez de en `design.md`)

| # | Decisión | Alternativa descartada y por qué |
|---|---|---|
| D1 | **Cero dependencias se mantiene.** Banner ASCII estático (`custom-agents` + versión + lema; apagado con `NO_COLOR`, `CI` o sin TTY) y **multiselect propio** en modo raw (↑/↓ mueve, espacio marca, `a` todos, `i` invierte, Enter confirma, Esc/Ctrl-C cancela), con los runtimes **detectados preseleccionados y Claude Code siempre marcado** (como claude-mem). Si `setRawMode` no está disponible, cae al menú numérico actual | `@clack/prompts` como única dependencia (lo que usa claude-mem): misma experiencia, pero rompe el principio «cero dependencias» que declaran `install.mjs`, `tests/installer.test.mjs` e `INTEROP.md`, obliga a `npm ci` en CI para `node --test` y añade una superficie de supply-chain a un instalador que escribe en `~/.claude`. Un multiselect raw son ~80 líneas con test de su reductor de teclas |
| D2 | **Claude Code por defecto = plugin registrado** (`--mode plugin`). Primera opción: la CLI oficial si `claude` está en PATH — `claude plugin marketplace add <fuente> --scope <s>` + `claude plugin install custom-agents@daycry --scope <s>`; fuente por defecto `daycry/custom-agents` (GitHub, como la vía nativa), `--source <ruta|owner/repo>` para desarrollo. Respaldo sin CLI: escritura directa del registro como claude-mem — copia del paquete a `<CLAUDE_CONFIG_DIR>/plugins/marketplaces/daycry/` y a `plugins/cache/daycry/custom-agents/<versión>/`, entrada en `known_marketplaces.json`, en `installed_plugins.json` y `enabledPlugins["custom-agents@daycry"] = true` en `settings.json` (scope user); en scope project, `.claude/settings.json` con `extraKnownMarketplaces` + `enabledPlugins` (Claude Code lo ofrece al confiar en la carpeta). La copia del bundle a `.claude/` queda como **`--mode copy`** explícito (vías 1/2 de `INSTALL.md`), con aviso de lo que se pierde | Seguir copiando el bundle: es exactamente el fallo reportado. Solo CLI: deja fuera a quien instala sin `claude` en PATH (Windows con instalación de escritorio). Solo registro directo: es formato interno de Claude Code; se usa como respaldo y se dice |
| D3 | **Codex**: además de las copias actuales, `codex plugin marketplace add <raíz del marketplace>` si `codex` está en PATH (versión mínima comprobada; si el marketplace ya existe con otra fuente, `remove` + `add`, como claude-mem) y `enabled = true` en `[plugins."custom-agents@daycry"]` del `config.toml` del scope (`~/.codex/config.toml` o `.codex/config.toml`) más `[features] hooks = true`; editor TOML mínimo propio (poner un booleano en una tabla, crear la tabla si falta, sin tocar nada más). Sin `codex` en PATH: se escribe `config.toml` igual y se imprime el comando pendiente | Dejar al usuario `/plugins` en la app: es lo que hoy no ocurre y por eso «no aparece nada» |
| D4 | **OpenCode**: registrar el adaptador en `opencode.json` `plugin: ["./plugins/custom-agents-hooks.js"]` (unión de arrays, como `instructions`) además de copiarlo | Confiar en la carga automática desde `plugins/`: no está confirmado en la doc y claude-mem lo registra explícitamente |
| D5 | **`/doctor` y `status` comprueban el registro real**: en Claude Code, `installed_plugins.json` / `enabledPlugins` del scope (o `.claude/settings.json`), y si la raíz del plugin es una copia en `.claude/` avisa ⚠️ «bundle copiado: hooks/statusline NO registrados; instala como plugin» con el comando; en Codex, `config.toml` `enabled`; en OpenCode, `opencode.json` `plugin`. El falso positivo de hoy desaparece | Mantener la comprobación de existencia: es lo que ocultó el fallo |
| D6 | **Desinstalación** sigue por manifiesto: en modo plugin el manifiesto apunta al registro escrito (claves y rutas), y `uninstall` deshace eso (o `claude plugin uninstall` si hay CLI) y nada más | — |

**Regla de honestidad:** lo que no se puede probar en esta máquina (Codex y OpenCode reales) no se marca como verificado; va a la checklist M-01 para el usuario y se dice en la Verificación de cada tarea.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — el instalador registra de verdad (Claude Code, Codex, OpenCode) | 0 | 4 | 0% | 6,0h / 7,0h | 0,36h / 0,90h | 0,20h / 0,25h | 2,84M / 420k |
| Fase 2 — diagnóstico veraz y documentación | 0 | 2 | 0% | — / 3,0h | — / 0,40h | — / 0,10h | — / 180k |
| **TOTAL** | **0** | **6** | **0%** | **6,0h / 10,0h** | **0,36h / 1,30h** | **0,20h / 0,35h** | **2,84M / 600k** |

---

## Fase 1 — el instalador registra de verdad (Claude Code, Codex, OpenCode)

**Estado**: en-progreso · **Estimado**: 7,0h · **Real**: 6,0h humanas (estimado) + 0,36h IA + 0,20h supervisión · **Coste est.**: ≈350 € · **Tokens est.**: 420k · **Tramo**: I1 (T-01…T-03) **completado** · I2 (T-04)

### T-01 — Banner y multiselect con checkboxes, cero dependencias

- **Descripción**: `install/install.mjs`: (a) `banner()` estático — wordmark ASCII `custom-agents`, versión y lema en una caja, colores ANSI a mano; no se imprime con `--quiet`, `NO_COLOR`, `CI` o sin TTY, y `--help`/`--version`/`status`/`list` no lo muestran; (b) `preguntar()` pasa a un **multiselect raw** (`readline.emitKeypressEvents` + `setRawMode`): lista de proveedores con `[x]`/`[ ]`, etiqueta `detectado`/`no detectado` y el `blurb`; teclas ↑/↓/j/k, espacio, `a` (todos), `i` (invertir), Enter, Esc/`q`/Ctrl-C (cancela con exit 0 y mensaje); preselección = detectados ∪ {`claude-code`}; sin `setRawMode` (stdin no TTY o terminal sin soporte) cae al menú numérico actual. El reductor de teclas es una **función pura** exportada (`reducirTecla(estado, tecla) → estado`) para poder probarlo sin terminal. `-y`/`--yes` y `-p` siguen sin preguntar nada.
- **Changelog**: El instalador `npx` muestra un título al arrancar y permite elegir los runtimes con checkboxes (espacio marca, Enter confirma), con los detectados preseleccionados.
- **Estado**: en-progreso
- **Tipo**: feature
- **Tiempo humano**: est. 1,5h · real 1,5h (estimado)
- **Tiempo IA (ejec.)**: est. 0,20h · real 0,30h (estimado — desviación 7: el marcador `installer-registro-real/T-01` se abrió a las 03:18:44Z y se cerró a las ~03:37Z, pero la salida del `close` se truncó y el JSON medido se perdió; el `close` sí dio `ratio_usado: 479326.0`, `ratio_origen: CALIBRATION.md (mediana de 6)`)
- **Supervisión**: est. 0,05h · real 0,05h (estimado)
- **Previsión IA**: 70k in / 10k out tok
- **Dependencias**: —
- **Archivos**: `install/install.mjs`, `tests/installer.test.mjs`
- **Verificación** (ejecutada el 2026-09-11 después del último cambio):
  - `node install/install.mjs --help | head -3` → `(en blanco)` / `custom-agents v1.19.0 — ciclo SDD presupuestado para agentes de código` / `(en blanco)`: **sin wordmark**. `CI=1 node install/install.mjs install --all --dry-run | head -2` → `(en blanco)` / `custom-agents v1.19.0 → claude-code, codex, opencode  [project: …]  (dry-run: no se escribe nada)`: **sin wordmark**
  - `node --test tests/installer.test.mjs` → `ℹ tests 34 · ℹ pass 34 · ℹ fail 0`, **exit 0** (comprobado con `echo $?`, sin `| tail`). 17 preexistentes + 17 nuevos; del reductor: mover/espacio, `a`, `i`, Enter devuelve solo lo marcado, Esc/`q`/Ctrl-C cancelan, tecla desconocida devuelve el MISMO estado, preselección con `claude-code` sin detectar, `nombreTecla`
  - `echo "" | node install/install.mjs install --dry-run` → **exit 0**, no cuelga: `custom-agents v1.19.0 → claude-code, codex  [project: …] (dry-run…)` y el plan de los dos detectados
  - Banner + multiselect **vistos** (arnés que finge `isTTY`, desviación 1 — en este entorno no hay pty):

    ```
       ___ _   _ ___ _____ ___  __  __
      / __| | | / __|_   _/ _ \|  \/  |  custom-agents v1.19.0
     | (__| |_| \__ \ | || (_) | |\/| |  ciclo SDD presupuestado para agentes de código
      \___|\___/|___/ |_| \___/|_|  |_|

    ¿En qué proveedores quieres instalar custom-agents?
      arriba/abajo (o j/k) mover · espacio marcar · a todos · i invertir · Enter confirmar · Esc cancelar

    > [x] Claude Code   detectado     plugin nativo — agentes, comandos, skills, hooks y statusline
      [x] Codex         detectado     plugin + agentes `.toml` + comandos como prompts
      [ ] OpenCode      no detectado  agentes + comandos + skills + adaptador de hooks en JS
    ```

    Tras `abajo`, `abajo`, `espacio`, `Enter` → `RESULTADO: {"sel":["claude-code","codex","opencode"]}` (el cursor `>` baja, el `[ ]` de OpenCode pasa a `[x]` y cada tecla repinta subiendo el cursor 3 líneas)
- **Desviaciones**:
  1. El banner y el multiselect **no se han visto en una terminal real** desde este agente (no hay pty en el entorno): se han pintado con un arnés que pone `process.stdout.isTTY`/`process.stdin.isTTY` a `true` y emite `keypress`. Para poder hacerlo, `multiselect` se **exporta** desde `install.mjs` (antes no existía). La comprobación en terminal real sigue siendo del orquestador/usuario.
  2. El test preexistente «cada proveedor declara lo mínimo y produce un plan no vacío» se **adapta**: acepta los seis tipos de paso y solo exige `to` a los que escriben (un `exec` lleva `cmd`/`args`).

**Criterios de aceptación**
- [x] Banner solo en TTY sin `NO_COLOR`/`CI`/`--quiet`, y nunca en `--help`, `--version`, `status`, `list`
- [x] Multiselect con checkboxes, teclas documentadas en pantalla, preselección detectados ∪ claude-code, cancelación limpia (cursor visible, raw mode restaurado también en error)
- [x] Reductor puro con tests; sin `setRawMode` cae al menú numérico; `-y`/`-p`/stdin no TTY no preguntan
- [x] Cero dependencias nuevas en `package.json`

**Subtareas**
- [x] `banner()` + condiciones de apagado
- [x] `reducirTecla()` + `multiselect()` + fallback numérico
- [x] Tests del reductor y de las condiciones de banner
  - commit `T-01: …` — lo hace el orquestador tras la revisión

### T-02 — Claude Code: modo plugin por defecto (CLI oficial → registro directo), `--mode copy` explícito

- **Descripción**: `install/providers.mjs` + `install/install.mjs`: nuevo tipo de paso `{ type: "exec" }` (comando con args, `cwd`, `opcional`) y `{ type: "json-set" }` (poner claves en un JSON del usuario; distinto de `merge`: sobrescribe SOLO las claves que pone, anota en el manifiesto qué claves puso para poder quitarlas). Proveedor `claude-code`, `modo: "plugin"` por defecto: (1) si `claude` está en PATH → `exec claude plugin marketplace add <source> --scope <scope>` (si ya existe, seguir) + `exec claude plugin install custom-agents@daycry --scope <scope>`; (2) si no → respaldo directo: `copy` del paquete (`PAYLOAD_CLAUDE` + `.claude-plugin/`) a `<CLAUDE_CONFIG_DIR>/plugins/marketplaces/daycry/` y a `<CLAUDE_CONFIG_DIR>/plugins/cache/daycry/custom-agents/<version>/`, `json-set` en `plugins/known_marketplaces.json` (`daycry: {source:{source:"github",repo:"daycry/custom-agents"}, installLocation, lastUpdated, autoUpdate:true}`), en `plugins/installed_plugins.json` (`version: 2`, `plugins["custom-agents@daycry"] = [{scope, installPath, version, installedAt, lastUpdated}]`) y en `settings.json` del scope (`enabledPlugins["custom-agents@daycry"] = true`; scope project además `extraKnownMarketplaces.daycry`). `CLAUDE_CONFIG_DIR` respetado (default `~/.claude`). `--mode copy` = plan actual con aviso «bundle copiado: hooks y statusline NO se registran; namespace no disponible». `--source <ruta|owner/repo>` cambia la fuente del marketplace (desarrollo). `restart`/`hint` actualizados (ya no «vía recomendada: /plugin…», porque ESTO es la vía). `uninstall`: `claude plugin uninstall custom-agents@daycry --scope` si hay CLI; si no, quitar las claves que el manifiesto anotó y borrar las copias; nunca borrar `settings.json`.
- **Changelog**: En Claude Code el instalador registra `custom-agents` como plugin de verdad (hooks, namespace y actualizaciones), usando la CLI oficial si está y escribiendo el registro del plugin si no; copiar el bundle pasa a ser `--mode copy`.
- **Estado**: en-progreso
- **Tipo**: feature
- **Tiempo humano**: est. 3,0h · real 3,0h (estimado)
- **Tiempo IA (ejec.)**: est. 0,40h · real 0,03h (medido, marcador `installer-registro-real/T-02`, ventana 03:37:17Z–03:40:43Z: `{"fuente": "medido", "tokens_reales": {"entrada": 18, "salida": 4486, "cache_creacion": 8447, "cache_lectura": 1665275, "respuestas": 9}, "eur": 0.92, "horas_ia": 0.03, "duracion": "2m"}`. La medida sale baja porque el grueso del diseño y del código de T-02 se escribió dentro de la ventana de T-01 — desviación 7)
- **Supervisión**: est. 0,10h · real 0,10h (estimado)
- **Previsión IA**: 120k in / 18k out tok
- **Dependencias**: T-01 (los pasos nuevos se imprimen en `--dry-run` con el mismo formato)
- **Archivos**: `install/providers.mjs`, `install/install.mjs`, `tests/installer.test.mjs`
- **Verificación** (ejecutada el 2026-09-11 después del último cambio):
  - Plan con y sin CLI: cubierto por los tests `Claude Code con CLI: el plan son los dos comandos oficiales` (dos `exec`, args exactos, `deshacer`) y `Claude Code sin CLI: copias + las tres claves del registro, bajo CLAUDE_CONFIG_DIR` (3 `json-set` a `known_marketplaces.json`, `installed_plugins.json` y `settings.json`, más las copias a `plugins/marketplaces/daycry` y `plugins/cache/daycry/custom-agents/<versión>`)
  - Instalación real de respaldo en HOME temporal con `PATH` sin `claude` (test `Claude Code sin CLI: registro real, idempotente y desinstalable sin tocar lo del usuario`, verde): `known_marketplaces.json` con `source.repo = daycry/custom-agents` e `installLocation`; `installed_plugins.json` con `version: 2` y `plugins["custom-agents@daycry"][0].scope = user`; `settings.json` con `enabledPlugins["custom-agents@daycry"] = true` **conservando** `model: opus` y `enabledPlugins["otro@mkt"]`; reinstalar → los tres ficheros **byte a byte idénticos**; `uninstall` → quitadas solo esas claves (siguen `model`, `otro@mkt` y `version: 2`), copias borradas, ningún fichero del usuario borrado
  - `--mode copy` = plan de siempre: test `--mode copy reproduce el plan de siempre, con el aviso de lo que se pierde` (mismos `from` que `PAYLOAD_CLAUDE`, mismos destinos `<dir>/.claude/<p>`, aviso «hooks y statusline NO se registran»)
  - `node --test tests/installer.test.mjs` → `ℹ tests 34 · ℹ pass 34 · ℹ fail 0`, **exit 0**; `node --test tests/*.test.mjs` → `ℹ tests 44 · ℹ pass 44 · ℹ fail 0`, **exit 0**
  - **Prueba real en esta máquina** (tiene `claude`), en un `CLAUDE_CONFIG_DIR` temporal y sin tocar el `~/.claude` real —
    `CLAUDE_CONFIG_DIR=<tmp>/cfg node install/install.mjs install -p claude-code --scope user --source "<ruta del repo>" -y`:

    ```
    Claude Code — plugin nativo — agentes, comandos, skills, hooks y statusline
      ✓ $ claude plugin marketplace add C:/…/custom-agents --scope user
      ✓ $ claude plugin install custom-agents@daycry --scope user --yes
      ✓ 2 paso(s) aplicados en C:\…\Temp\ca-real\cfg\plugins
    ```

    `CLAUDE_CONFIG_DIR=<tmp>/cfg claude plugin list` →

    ```
    Installed plugins:
      ❯ custom-agents@daycry
        Version: 1.19.0
        Scope: user
        Status: ✔ enabled
    ```

    El manifiesto apunta los dos `exec` (el segundo con su `deshacer`), y `uninstall -p claude-code --scope user` deja `claude plugin list` → `No plugins installed.`
- **Desviaciones**:
  3. El apunte del manifiesto de un `exec` lleva, además del `{exec: "<cmd args>"}` informativo del contrato, un campo `deshacer` con el comando inverso cuando el paso lo declara. Sin él no se puede cumplir lo que pide la propia descripción de T-02 («`claude plugin uninstall …` si hay CLI») sin adivinar el comando a partir de una cadena.
  4. Para un `--source` que es una **ruta local**, la fuente se escribe como `{source: "directory", path}` y no como `{source: "github", repo}`: es lo que escribe la CLI oficial de Claude Code (comprobado en el `settings.json` que dejó `claude plugin marketplace add <ruta>` en la prueba real). Para `owner/repo` se mantiene `{source: "github", repo}` del contrato.
  5. El paso `json-set` admite dos campos no previstos en el contrato: `volatiles` (campos de marca de tiempo que no cuentan como cambio, para que reinstalar NO reescriba el registro) y `noQuitar` (claves que se ponen pero que `uninstall` no quita, como el `version: 2` de `installed_plugins.json`, que es del fichero y no nuestra).
  9. `destino()` acepta un tercer argumento `modo`, porque el destino del manifiesto de Claude Code depende de él (`<cfg>/plugins` en plugin, `.claude/` en copy); `status` y `uninstall` miran los dos.
- **Notas**: el formato de `known_marketplaces.json`/`installed_plugins.json` es interno de Claude Code (claude-mem lo escribe igual); se documenta en `INTEROP.md` como respaldo y el modo CLI es el preferido. Nada de este cambio toca las piezas (`agents/`, `commands/`, `skills/`, `hooks/`): `export-interop.py --check` no varía.

**Criterios de aceptación**
- [x] Por defecto, tras instalar en Claude Code el plugin figura en `installed_plugins.json` + `enabledPlugins` (vía CLI o respaldo) y el bundle NO se copia a `.claude/`
- [x] `--mode copy` reproduce el comportamiento anterior byte a byte en el plan, con aviso
- [x] Idempotente y desinstalable por manifiesto (claves anotadas); `settings.json` del usuario nunca se borra ni se pisa fuera de las claves puestas
- [x] `CLAUDE_CONFIG_DIR` respetado; `--source` documentado en `--help`

**Subtareas**
- [x] Pasos `exec` y `json-set` en `ejecutar()` (dry-run, manifiesto, errores)
- [x] Proveedor `claude-code` con `modo` y detección de `claude` en PATH
- [x] `uninstall` para modo plugin
- [x] Tests
  - commit `T-02: …` — lo hace el orquestador tras la revisión

### T-03 — Codex: `marketplace add` + `enabled = true` (y `hooks`) en `config.toml`

- **Descripción**: proveedor `codex`: tras las copias actuales, (1) `exec codex plugin marketplace add <mktRoot>` si `codex` en PATH (versión mínima `0.128.0` leída de `codex --version`; si «already added from a different source» → `remove` + `add`; sin `codex` → aviso con el comando pendiente); (2) paso nuevo `{ type: "toml-set", to, tabla, clave, valor }`: editor mínimo propio que pone un booleano en `[plugins."custom-agents@daycry"]` (`enabled = true`) y en `[features]` (`hooks = true`) del `config.toml` del scope (`~/.codex/config.toml` o `<dir>/.codex/config.toml`), creando la tabla al final si no existe y **sin reescribir nada más** (conserva comentarios y orden); el manifiesto anota tabla+clave para `uninstall` (pone `enabled = false`, no borra la tabla). Nombre del marketplace = `name` de `.agents/plugins/marketplace.json` (`daycry`) → id `custom-agents@daycry`.
- **Changelog**: En Codex el instalador registra el marketplace con la CLI y habilita el plugin en `config.toml`, que es lo que faltaba para que skills y hooks aparezcan.
- **Estado**: en-progreso
- **Tipo**: feature
- **Tiempo humano**: est. 1,5h · real 1,5h (estimado)
- **Tiempo IA (ejec.)**: est. 0,20h · real 0,03h (medido, marcador `installer-registro-real/T-03`, ventana 03:40:44Z–03:43:16Z: `{"fuente": "medido", "tokens_reales": {"entrada": 12, "salida": 5229, "cache_creacion": 9184, "cache_lectura": 1149696, "respuestas": 6}, "eur": 0.7, "horas_ia": 0.03, "duracion": "2m"}`)
- **Supervisión**: est. 0,05h · real 0,05h (estimado)
- **Previsión IA**: 70k in / 10k out tok
- **Dependencias**: T-02 (paso `exec`)
- **Archivos**: `install/providers.mjs`, `install/install.mjs`, `tests/installer.test.mjs`
- **Verificación** (ejecutada el 2026-09-11 después del último cambio):
  - `node --test tests/installer.test.mjs` → `ℹ tests 34 · ℹ pass 34 · ℹ fail 0`, **exit 0**. Del `toml-set`: fichero vacío → `[features]\nhooks = true\n`; tabla existente con comentario y otras claves → solo cambia esa línea (`assert.equal(out, previo.replace("hooks = false", "hooks = true"))`); clave nueva → **al final de SU tabla**, no del fichero; CRLF y fichero sin salto final conservados; idempotente
  - `HOME=<tmp> node install/install.mjs install -p codex --scope user -y` con `codex` **fuera** del PATH → aviso `! \`codex\` no está en el PATH — ejecútalo tú: codex plugin marketplace add C:\…\home\.agents` y `✓ 223 paso(s) aplicados`. `config.toml` de partida (CRLF, con comentario) → resultado:

    ```toml
    # mi config
    [features]
    web_search = true
    hooks = true

    [tui]
    theme = "dark"

    [plugins."custom-agents@daycry"]
    enabled = true
    ```

    `file config.toml` → `ASCII text, with CRLF line terminators` (ni los saltos de línea se normalizan)
  - Con un `codex` **falso** en el PATH (responde `codex-cli 0.130.0` a `--version` y apunta lo que le piden), `--dry-run` imprime `→ $ codex plugin marketplace add C:\…\home\.agents` + los dos `toml-set`; y la instalación real lo **llama de verdad**: el log del falso recibe `plugin marketplace add C:\…\home\.agents`
  - `uninstall -p codex --scope user` → `enabled = false` en `[plugins."custom-agents@daycry"]`, `[features] hooks = true` **intacto** (es preferencia del usuario) y el resto del `config.toml` sin tocar; en el test, `assert.equal(toml2, toml.replace("enabled = true", "enabled = false"))`
  - **No verificable aquí**: que Codex cargue el plugin tras esto → checklist **M-01** (usuario); en esta máquina no hay `codex` real
- **Desviaciones**:
  6. `correr()` resuelve la ruta real del comando (`where.exe`/`which`) y, en Windows, ejecuta los lanzadores `.cmd`/`.bat` a través de `cmd.exe /d /s /c` con los argumentos entrecomillados a mano. Sin esto Node no puede ejecutar un `codex.cmd`/`claude.cmd` (el caso normal de una instalación por npm) y el paso `exec` degradaba a aviso siempre. `enPath()` pasa a ser `Boolean(rutaDe(cmd))`.
  8. El `toml-set` de `[features] hooks` declara `deshacer: false` (no se apunta en el manifiesto): apagar una preferencia global del usuario al desinstalar sería pisarle la configuración. El de `[plugins."custom-agents@daycry"] enabled` sí se apunta y se pone a `false`.
- **Notas**: `codex plugin marketplace add` y `[plugins."<id>"] enabled` están en la doc oficial de Codex («Package plugin»); el flujo lo usa `claude-mem` (`CodexCliInstaller.ts`) con la misma versión mínima.

**Criterios de aceptación**
- [x] `config.toml` del scope con `[plugins."custom-agents@daycry"] enabled = true` y `[features] hooks = true`, sin alterar el resto del fichero
- [x] Con `codex` en PATH se ejecuta `marketplace add` (con recuperación si ya existía); sin él, aviso con el comando exacto
- [x] `uninstall` pone `enabled = false` y no borra nada del `config.toml`

**Subtareas**
- [x] Paso `toml-set` + editor mínimo con tests
- [x] `exec codex …` con versión mínima y recuperación
- [x] `uninstall`
  - commit `T-03: …` — lo hace el orquestador tras la revisión

### T-04 — OpenCode: registrar el adaptador de hooks en `opencode.json`

- **Descripción**: en el paso `merge` de `opencode.json` añadir `plugin: ["./plugins/custom-agents-hooks.js"]` (scope project) o la ruta absoluta bajo `~/.config/opencode/plugins/` (scope user), como unión de arrays sin duplicar; `uninstall` la deja (es config del usuario, se avisa como hoy con `instructions`).
- **Changelog**: En OpenCode el instalador registra el adaptador de hooks en `opencode.json`, además de copiarlo.
- **Estado**: borrador
- **Tipo**: feature
- **Tiempo humano**: est. 1,0h · real —
- **Tiempo IA (ejec.)**: est. 0,10h · real —
- **Supervisión**: est. 0,05h · real —
- **Previsión IA**: 40k in / 5k out tok
- **Dependencias**: —
- **Archivos**: `install/providers.mjs`, `tests/installer.test.mjs`, `tests/opencode-plugin.test.mjs` (si afirma la ruta)
- **Verificación**:
  - `node install/install.mjs install -p opencode -y --dir <tmp>` → `opencode.json` con `plugin: ["./plugins/custom-agents-hooks.js"]` además de `instructions`/`permission` (pegado); reinstalar → igual; usuario con `plugin: ["otro"]` → `["otro", "./plugins/custom-agents-hooks.js"]`
  - `node --test tests/*.test.mjs` → verde
  - **No verificable aquí**: que OpenCode cargue el adaptador → **M-01**

**Criterios de aceptación**
- [ ] `plugin` registrado en ambos scopes con la ruta correcta; unión sin duplicar; el `plugin` previo del usuario se conserva

**Subtareas**
- [ ] `merge` con `plugin` + test
  - commit `T-04: …` — lo hace el orquestador tras la revisión

---

## Fase 2 — diagnóstico veraz y documentación

**Estado**: borrador · **Estimado**: 3,0h · **Real**: — · **Coste est.**: ≈150 € · **Tokens est.**: 180k · **Tramo**: I2

### T-05 — `/doctor` y `status` comprueban el registro real, no la existencia de ficheros

- **Descripción**: `agent-kits/shared/doctor.py`, bloque «Plugin»: (1) determinar cómo está instalado — `plugin` (raíz bajo `<CLAUDE_CONFIG_DIR>/plugins/cache/…` o `custom-agents@…` en `installed_plugins.json`/`enabledPlugins` del scope) o `copia` (raíz en `<proyecto>/.claude` o `~/.claude` sin entrada en el registro); (2) fila «hooks registrados»: ✅ solo en modo plugin (y con `hooks/hooks.json` válido); en modo copia ⚠️ «bundle copiado a `.claude/`: Claude Code NO lee `hooks/hooks.json` fuera de un plugin — hooks, statusline y namespace no disponibles» con arreglo `npx @daycry/custom-agents install -p claude-code` (o `/plugin marketplace add daycry/custom-agents` + `/plugin install custom-agents`); (3) fila nueva «registro del plugin»: dónde está registrado (fichero y scope) o ❌ si `enabledPlugins` lo tiene en `false`. `install.mjs status`: por proveedor, además del manifiesto, «registrado: sí/no» leyendo lo mismo (Claude: `installed_plugins.json`/`enabledPlugins`; Codex: `config.toml` `enabled`; OpenCode: `opencode.json` `plugin`). Tests en `agent-kits/shared/test_doctor.py` con fixtures de los dos modos; `--json` gana las claves nuevas sin quitar ninguna.
- **Changelog**: `/doctor` y `status` dicen si el plugin está registrado de verdad en cada runtime; una copia del bundle en `.claude/` ya no pasa por «hooks registrados».
- **Estado**: borrador
- **Tipo**: fix
- **Tiempo humano**: est. 2,0h · real —
- **Tiempo IA (ejec.)**: est. 0,25h · real —
- **Supervisión**: est. 0,05h · real —
- **Previsión IA**: 90k in / 12k out tok
- **Dependencias**: T-02 (formato del registro escrito)
- **Archivos**: `agent-kits/shared/doctor.py`, `agent-kits/shared/test_doctor.py`, `install/install.mjs`, `tests/installer.test.mjs`, `docs/agents/doctor.md`
- **Verificación**:
  - Reproducción del falso positivo: HOME temporal + `install -p claude-code --mode copy -y --dir <tmp>` + `python <tmp>/.claude/agent-kits/shared/doctor.py` → fila hooks ⚠️ con el arreglo (antes ✅); pegado
  - Este repo real (plugin instalado desde el marketplace `daycry`): `python agent-kits/shared/doctor.py --json` → `registro: plugin`, hooks ✅; el resto del JSON idéntico salvo las claves nuevas (diff con HEAD pegado)
  - `python -m pytest -q agent-kits/shared/test_doctor.py -p no:cacheprovider` → verde (conjunto idéntico + nuevos; los 2 rojos de Windows preexistentes iguales)
  - `node install/install.mjs status` en el HOME temporal → «registrado: sí» tras T-02 y «no» tras `--mode copy`
- **Notas**: `docs/agents/doctor.md` explica los dos modos y la fila nueva. Copias `--8<--` de `doctor.py` (registradas en `copias.json`) sin tocar: `pytest tests/test_copias_declaradas.py` verde.

**Criterios de aceptación**
- [ ] Modo copia → hooks ⚠️ con arreglo; modo plugin → ✅ y fila «registro» con fichero/scope; `enabledPlugins: false` → ❌
- [ ] `status` informa «registrado» por runtime desde los ficheros reales
- [ ] `--json` compatible hacia atrás; copias `--8<--` intactas

**Subtareas**
- [ ] `_modo_instalacion()` + filas en `doctor.py` con tests
- [ ] `status` en `install.mjs`
- [ ] `docs/agents/doctor.md`
  - commit `T-05: …` — lo hace el orquestador tras la revisión

### T-06 — Documentación, checklist M-01 y CHANGELOG

- **Descripción**: `docs/INTEROP.md` §1 (la vía corta: qué hace ahora en cada runtime, `--mode`, `--source`, `CLAUDE_CONFIG_DIR`, respaldo sin CLI y por qué) y §4 (tabla de degradación: fila «registro del plugin» por runtime); `docs/en/INTEROP.md` espejo; `docs/INSTALL.md` Vía 0 (y nota en Vías 1/2: «equivale a `--mode copy`, sin hooks») + `docs/en/INSTALL.md`; `README.md`/`README.es.md` sección de instalación; `install.mjs --help` al día. **Checklist M-01** (aquí, al final del ledger): pasos que el usuario ejecuta en su máquina con Codex y OpenCode reales y qué debe ver; se marca cuando él lo confirme, no antes. CHANGELOG EN/ES por `changelog-sync` al cerrar (`estado: completado`).
- **Changelog**: Documentación del instalador al día (modos, fuente, respaldo sin CLI) y checklist de verificación manual en Codex y OpenCode.
- **Estado**: borrador
- **Tipo**: docs
- **Tiempo humano**: est. 1,0h · real —
- **Tiempo IA (ejec.)**: est. 0,15h · real —
- **Supervisión**: est. 0,05h · real —
- **Previsión IA**: 60k in / 8k out tok
- **Dependencias**: T-01…T-05
- **Archivos**: `docs/INTEROP.md`, `docs/en/INTEROP.md`, `docs/INSTALL.md`, `docs/en/INSTALL.md`, `README.md`, `README.es.md`, `install/install.mjs` (texto de `--help`), `CHANGELOG.md`, `CHANGELOG.es.md`
- **Verificación**:
  - `python scripts/lint_plugin.py` → `0 errores`; `python evals/check.py` → 0; `python scripts/export-interop.py --check` → `48 ficheros al día`; `python -m pytest -q tests/test_ci_manual_copy.py tests/test_export_interop.py -p no:cacheprovider` → verde
  - `grep -n "mode copy\|--source\|CLAUDE_CONFIG_DIR" docs/INTEROP.md docs/en/INTEROP.md docs/INSTALL.md docs/en/INSTALL.md` → presente en los cuatro
  - Criterio de prosa (`docs-style.md`) revisado por la Lente A
  - `python skills/changelog-sync/scripts/changelog-sync.py --check docs/roadmap/2026-09-11-installer-registro-real` (al cerrar) → entradas EN/ES generadas

**Criterios de aceptación**
- [ ] Docs ES/EN espejadas en el mismo cambio; `--help` coherente con la doc
- [ ] M-01 escrita con pasos y resultado esperado por runtime; sin marcar hasta la confirmación del usuario
- [ ] CHANGELOG EN/ES con un bullet por tarea (escalera de `changelog-sync`)

**Subtareas**
- [ ] INTEROP + INSTALL + README (ES/EN)
- [ ] M-01
- [ ] `changelog-sync` al cerrar
  - commit `T-06: …` — lo hace el orquestador tras la revisión

---

## M-01 — Verificación manual en runtimes reales (la hace el usuario)

> Se rellena en T-06 con los pasos exactos. Esqueleto:
>
> - [ ] **Claude Code** (máquina del usuario): `npx @daycry/custom-agents install -p claude-code --scope user` → `claude plugin list` muestra `custom-agents@daycry`; en una sesión nueva `/custom-agents:doctor` existe y el hook `SessionStart` inyecta el índice de piezas.
> - [ ] **Codex**: `npx @daycry/custom-agents install -p codex --scope user` → `codex plugin marketplace list` incluye `daycry`; `~/.codex/config.toml` tiene `enabled = true`; en sesión nueva las skills `custom-agents` aparecen con `@` y `/prompts:dev-cycle` existe.
> - [ ] **OpenCode**: `npx @daycry/custom-agents install -p opencode` → `opencode.json` con `plugin` y el adaptador carga (sin error al arrancar); las skills se listan.

## Revision de dos lentes - intento 1 (tramo I1: T-01..T-03): 2 Critical, 9 Important, 9 Minor (lentes A+B)

Lentes A (conformidad con D1-D6 y criterios) y B (persona «especialista en instaladores CLI multiplataforma») en
paralelo, contexto fresco, marcador `installer-registro-real/revision-I1-intento1`:
`{"eur":8.0,"horas_ia":0.88,"duracion_reloj":"17m","tokens_reales":{"entrada":221,"salida":99936,"cache_creacion":319450,"cache_lectura":8392528,"respuestas":78},"fuente":"medido"}`.

**Verificado y correcto** (no se repite en el intento 2): via CLI real con `claude` en `CLAUDE_CONFIG_DIR` temporal
instala (`claude plugin list` -> `custom-agents@daycry … enabled`) y desinstala (`No plugins installed.`); respaldo sin
CLI escribe las 3 claves de D2 y es idempotente byte a byte (`volatiles`); `uninstall` quita solo la clave propia y
conserva `model`, `otro@mkt`, `version: 2`; `--mode copy` = plan de HEAD (comparacion programatica, `IGUALES: true`) +
aviso; `toml-set` conserva CRLF y comentarios de otras lineas; recuperacion `already added…` ejercitada con CLI falsa;
`.cmd` por `cmd.exe` acotado a win32 y sin inyeccion por `"`/`&`/`^`; banner apagado en los 7 casos; reductor puro
(envuelve, `a`/`i`, tecla desconocida devuelve el mismo objeto); fallback numerico conserva la preseleccion; OpenCode
identico a HEAD; 44/44 tests, 17 nombres originales intactos; desviaciones 1, 2, 3, 5, 6, 7, 8 legitimas; la 4
legitima y confirmada leyendo lo que escribe la CLI real (`{"source":"directory","path"}`), la 9 falsa en scope project.

| # | Grado | Gap | Tarea | Correccion | Evidencia |
|---|---|---|---|---|---|
| 1 (A-1 = B-2) | **Critical** | `json-set` lee con `leerJson` (traga todo error) y aplica `\|\| {}`: un `settings.json`/`installed_plugins.json`/`known_marketplaces.json` que no parsea (BOM de Notepad, coma final, JSONC) se **sustituye entero, sin aviso, exit 0, sin copia**. Reproducido: se pierden `model`, `permissions`, `env` y los demas plugins | T-02 | pendiente: JSON invalido -> **error del paso** (no se escribe nada; el proveedor falla en alto con el fichero y el motivo; sin CLI, `settings.json` ilegible = no hay respaldo posible, se dice); BOM tolerado al leer y conservado al escribir; `enabledPlugins` no-objeto -> error, no pisar | `install.mjs:146-148,420` |
| 2 (B-1) | **Critical** | `rutaDe()` devuelve el **primer** resultado de `where.exe`, que con `npm i -g` es el shim POSIX **sin extension**; `correr()` solo enruta por `cmd.exe` con `.cmd/.bat`, asi que `spawnSync … ENOENT`, exit 1, nada instalado, y el respaldo no entra porque `enPath` dijo si. Con `codex`: «version desconocida < 0.128.0» siendo 0.130.0 -> marketplace nunca registrado mientras se escribe `enabled = true` | T-02/T-03 | pendiente: `rutaDe` prefiere en win32 el candidato con `.cmd`/`.exe`/`.bat` (recorrer TODOS los resultados de `where.exe`, elegir por `PATHEXT`); si solo hay shim sin extension, ejecutarlo via `cmd.exe`/`bash` segun cabecera o degradar al respaldo con aviso; test con layout npm (shim + `.cmd`) en el `PATH` falso | `providers.mjs:66` · `install.mjs:290` |
| 3 (A-2) | **Important** | `fuenteRegistro()` clasifica `./ruta` y `../ruta` como repo GitHub (`.` esta en `[\w.-]`): el respaldo escribe `{"source":"github","repo":"./mi-clon"}`, irresoluble; es el ejemplo del `--help` | T-02 | pendiente: `owner/repo` solo si casa `^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$` **y no empieza por `.`/`/`/letra de unidad** ni existe como directorio; lo demas `directory` con ruta absoluta resuelta; test de los 5 casos | `providers.mjs:79` · `install.mjs:104` |
| 4 (A-3 = B-3) | **Important** | En scope `project`, `destino()` da la MISMA ruta para `plugin` y `copy` (`<dir>/.claude`): el segundo `install` pisa el manifiesto del primero -> 222 ficheros huerfanos que `uninstall` ya no borra (es la via de actualizacion de todo usuario del instalador anterior). Desviacion 9 falsa | T-02 / D6 | pendiente: manifiesto **por modo** (`.custom-agents-install.json` para copy, `.custom-agents-install.plugin.json` para plugin, o clave `modo` en el nombre); `status`/`uninstall` leen ambos; al instalar en modo plugin sobre un `copy` previo, avisar y ofrecer/ejecutar el `uninstall` del copy primero (`--yes` lo hace) | `providers.mjs:180-182` · `install.mjs:540-541` |
| 5 (B-4) | **Important** | Si un paso lanza, `ejecutar()` sale sin escribir el manifiesto: lo ya aplicado (p. ej. `marketplace add` OK + `plugin install` KO) queda sin registro y `uninstall` se niega. Igual con EPERM en `escribirJson` | T-02 | pendiente: manifiesto **parcial** escrito en el `catch` (pasos aplicados + `estado: "incompleto"` + error), `uninstall` lo acepta; `escribirJson` con try y mensaje | `install.mjs:450-461,571-574` |
| 6 (B-5) | **Important** | `podarVacios(dest)` barre TODO `~/.claude/plugins` y borra directorios vacios ajenos (`marketplaces/otro-mkt`, `cache/otro-mkt/**`, `repos/`), contra el principio de `install.mjs:17-18` | T-02 | pendiente: podar solo los directorios **padres de los ficheros del manifiesto**, de abajo arriba, parando en `dest` | `install.mjs:607-616` |
| 7 (B-6) | **Important** | `siYaExiste` **borra** el marketplace `daycry` del usuario (otra fuente) y lo re-crea con la nuestra sin preguntar, sin aviso en exito y sin `deshacer`; el comentario dice lo contrario | T-03 | pendiente: NO hacer `remove` por defecto: aviso claro con el comando para que lo haga el usuario; `--force-marketplace` (o `--yes` + aviso) lo permite y queda en el manifiesto | `providers.mjs:233-237` · `install.mjs:402-406` |
| 8 (B-7) | **Important** | `correr()` sin `timeout` y con stdout/stderr capturados: una CLI colgada bloquea `npx` sin una linea en pantalla (31 s medidos) | T-02/T-03 | pendiente: `timeout` (p. ej. 120 s, configurable por env), linea «ejecutando `<cmd>`…» antes de cada `exec`, y en fallo volcar stderr capturado | `install.mjs:288-295` |
| 9 (B-8) | **Important** | Filas del menu de 82-95 columnas: en 80 columnas cada fila ocupa 2 lineas fisicas y el repintado (`\u001b[NA` con N logicas) descuadra el menu con cada tecla | T-01 | pendiente: recortar cada fila a `process.stdout.columns - 1` (blurb con `…`) y repintar por lineas fisicas; test del recorte | `install.mjs:701-716` |
| 10 (B-9) | **Important** | `pintar()` fuera del `try` de `onTecla`: si `stdout.write` lanza (EPIPE) `limpiar()` no corre -> terminal en raw mode y sin cursor | T-01 | pendiente: `try/finally` alrededor de todo el listener + `process.once("exit")` que restaura raw mode y cursor | `install.mjs:727-742` |
| 11 (B-10) | **Important** | `ponerToml` compara la cabecera con `===` literal: `[plugins.'custom-agents@daycry']`, `[ plugins."…" ]` o `[[…]]` -> **segunda tabla** duplicada -> `config.toml` ilegible para Codex | T-03 | pendiente: normalizar cabeceras (quitar espacios, unificar comillas) al comparar; `[[…]]` con el mismo nombre -> error del paso (no tocar); test de las 3 variantes | `install.mjs:232-240` |
| 12 (A-4) | Minor | `Changelog` de T-02: 230 caracteres > 200 | T-02 | pendiente: acortar | `tasks.md` T-02 |
| 13 (A-5) | Minor | Fila de progreso: tokens `2,84M` son solo T-02 + T-03 (T-01 perdio el JSON) y no se dice | ledger | pendiente: «(sin T-01: JSON perdido)» en la celda | `tasks.md:73,75` |
| 14 (B-11) | Minor | En la rama `cmd.exe` se expanden `%VAR%` dentro de los argumentos (`%MISECRETO%` -> valor) | T-02 | pendiente: escapar `%` como `%%` (o `^%`) en los argumentos que pasan por `cmd.exe` | `install.mjs:291-293` |
| 15 (B-12) | Minor | Si un paso lanza se pierden los `avisos` acumulados | T-02 | pendiente: imprimirlos en el `catch` | `install.mjs:462,520-523` |
| 16 (B-13) | Minor | `uninstall` **re-crea** la tabla del plugin en `config.toml` si el usuario la habia borrado | T-03 | pendiente: al deshacer, si la tabla no existe no escribir nada | `install.mjs:592-596` |
| 17 (B-14) | Minor | El barrido de fin de tabla (`^\s*\[`) casa lineas de un array multilinea o cadena `"""` y la clave cae dentro del literal | T-03 | pendiente: saltar arrays/cadenas multilinea abiertos (contar corchetes/comillas) o insertar justo tras la cabecera | `install.mjs:243` |
| 18 (B-15) | Minor | Al reemplazar `enabled = false # comentario` se pierde el comentario, contra el docstring | T-03 | pendiente: conservar el sufijo `# …` de la linea | `install.mjs:245-249` |
| 19 (B-16) | Minor | `uninstall` deja `known_marketplaces.json` = `{}`, `installed_plugins.json` = `{"version":2,"plugins":{}}` y `enabledPlugins: {}` que no existian antes | T-02 | pendiente: el manifiesto anota si el fichero lo **creo** el instalador; en ese caso, si queda vacio (solo `noQuitar`), borrarlo | `install.mjs:431-434,590-591` |
| 20 (B-17) | Minor | Enter sin marcar nada se confunde con «no he detectado ningun proveedor» (exit 2) | T-01 | pendiente: mensaje propio «no has marcado ninguno» exit 0 | `install.mjs:679,494-498` |

**Fuera de lente, anotado**: `rutaDe` acepta el primer resultado de `where.exe` sin validar extension (secuestro por orden de PATH: lo cubre el gap 2); hasta 4 `where.exe` por paso `exec` (rendimiento, T-19-like); tres comentarios del codigo contradicen lo que hace (gaps 7, 10, 18); tras `uninstall` via CLI queda `daycry` en `known_marketplaces.json` (`marketplace add` sin `deshacer`: conforme a T-02, residuo declarado). La doc (`INTEROP.md`, `INSTALL.md`) sigue describiendo el instalador anterior: es T-06.
