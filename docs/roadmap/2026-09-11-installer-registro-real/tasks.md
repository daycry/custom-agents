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
| Fase 1 — el instalador registra de verdad (Claude Code, Codex, OpenCode) | 1 | 4 | 25% | 6,0h / 7,0h | 2,55h / 0,90h | 0,20h / 0,25h | 21,7M medidos (sin el T-01 original ni el intento 2: JSON perdido / medidor degradado) / 420k |
| Fase 2 — diagnóstico veraz y documentación | 0 | 2 | 0% | — / 3,0h | — / 0,40h | — / 0,10h | — / 180k |
| **TOTAL** | **1** | **6** | **17%** | **6,0h / 10,0h** | **2,55h / 1,30h** | **0,20h / 0,35h** | **21,7M medidos (sin el T-01 original ni el intento 2) / 600k** |

---

## Fase 1 — el instalador registra de verdad (Claude Code, Codex, OpenCode)

**Estado**: en-progreso · **Estimado**: 7,0h · **Real**: 6,0h humanas (estimado) + 2,55h IA + 0,20h supervisión · **Coste est.**: ≈350 € · **Tokens est.**: 420k · **Tramo**: I1 (T-01…T-03) **completado**, revisión de dos lentes intento 1 cerrada (20/20) e intento 2 cerrada (15/15: 1 Critical, 7 Important, 7 Minor) · I2 (T-04)

### T-01 — Banner y multiselect con checkboxes, cero dependencias

- **Descripción**: `install/install.mjs`: (a) `banner()` estático — wordmark ASCII `custom-agents`, versión y lema en una caja, colores ANSI a mano; no se imprime con `--quiet`, `NO_COLOR`, `CI` o sin TTY, y `--help`/`--version`/`status`/`list` no lo muestran; (b) `preguntar()` pasa a un **multiselect raw** (`readline.emitKeypressEvents` + `setRawMode`): lista de proveedores con `[x]`/`[ ]`, etiqueta `detectado`/`no detectado` y el `blurb`; teclas ↑/↓/j/k, espacio, `a` (todos), `i` (invertir), Enter, Esc/`q`/Ctrl-C (cancela con exit 0 y mensaje); preselección = detectados ∪ {`claude-code`}; sin `setRawMode` (stdin no TTY o terminal sin soporte) cae al menú numérico actual. El reductor de teclas es una **función pura** exportada (`reducirTecla(estado, tecla) → estado`) para poder probarlo sin terminal. `-y`/`--yes` y `-p` siguen sin preguntar nada.
- **Changelog**: El instalador `npx` muestra un título al arrancar y permite elegir los runtimes con checkboxes (espacio marca, Enter confirma), con los detectados preseleccionados.
- **Estado**: completado
- **Tipo**: feature
- **Tiempo humano**: est. 1,5h · real 1,5h (estimado)
- **Tiempo IA (ejec.)**: est. 0,20h · real 0,58h (0,30h estimadas del tramo + **0,18h medidas** del intento 1 de revisión, reparto abajo — desviación 7: el marcador `installer-registro-real/T-01` se abrió a las 03:18:44Z y se cerró a las ~03:37Z, pero la salida del `close` se truncó y el JSON medido se perdió; el `close` sí dio `ratio_usado: 479326.0`, `ratio_origen: CALIBRATION.md (mediana de 6)`) + **0,10h estimadas** del intento 2 (marcador `I1-fix2`: el medidor degradó, ver el reparto al final)
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
  - **Re-ejecutada tras las correcciones del intento 1** (2026-09-11, después del último cambio, GOT-007):
    `node --test tests/installer.test.mjs` → `tests 59 · pass 59 · fail 0`, **exit 0** (`echo $?`);
    `node --test tests/*.test.mjs` → `tests 69 · pass 69 · fail 0`, **exit 0** (44 previos + 25 nuevos, uno o varios por gap);
    `python scripts/lint_plugin.py` → `9 agentes · 0 errores · 3 avisos`; `python scripts/export-interop.py --check` → `48 ficheros al día`;
    `python -m pytest -q tests/` → `26 failed, 862 passed` = **el MISMO conjunto** de rojos preexistentes de Windows que en `git stash` (diff de los dos `FAILED` ordenados: vacío).
    Gaps de T-01: `cortarAnsi` recorta a `columns - 1` (200 caracteres → 79 visibles, «…» y reset ANSI conservado);
    el listener del multiselect con `try/finally` + `process.once("exit")` — probado en un proceso hijo que hace reventar
    `stdout.write` a media tecla: `{"raw":false,"cursor":"ESC[?25h","oyentes":0}`; Enter sin marcar → `{vacio:true}` y
    mensaje propio con exit 0 (`resultadoSeleccion`).
  - **Re-ejecutada tras las correcciones del intento 2** (2026-09-11, después del último cambio, GOT-007):
    `node --test tests/*.test.mjs` → `ℹ tests 93 · ℹ pass 93 · ℹ fail 0`, **exit 0** (`echo $?`, sin `| tail`);
    69 previos + **24 nuevos**, y **0 nombres de test perdidos** (conjunto ordenado antes/después: `comm -23` vacío);
    `python scripts/lint_plugin.py` → `9 agentes · 0 errores · 3 avisos`; `python scripts/export-interop.py --check` →
    `48 ficheros al día`; `python -m pytest -q tests/` → `26 failed, 862 passed` (el conjunto conocido de rojos de
    Windows; esta tarea no toca Python). De T-01, lo que rozó el intento 2: los manejadores de señal conviven con el
    multiselect sin dejar la terminal en raw (el `process.once("exit", limpiar)` sigue siendo la red) y el test nuevo
    comprueba que durante la instalación hay manejador de `SIGINT` y que al terminar no queda ninguno.
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
- **Changelog**: En Claude Code el instalador registra el plugin de verdad (hooks, namespace y actualizaciones), con la CLI oficial o escribiendo su registro; copiar el bundle es ahora `--mode copy`.
- **Estado**: en-progreso
- **Tipo**: feature
- **Tiempo humano**: est. 3,0h · real 3,0h (estimado)
- **Tiempo IA (ejec.)**: est. 0,40h · real 1,25h (0,03h + **0,62h medidas** del intento 1 de revisión, reparto abajo; marcador del tramo `installer-registro-real/T-02`, ventana 03:37:17Z–03:40:43Z: `{"fuente": "medido", "tokens_reales": {"entrada": 18, "salida": 4486, "cache_creacion": 8447, "cache_lectura": 1665275, "respuestas": 9}, "eur": 0.92, "horas_ia": 0.03, "duracion": "2m"}`. La medida sale baja porque el grueso del diseño y del código de T-02 se escribió dentro de la ventana de T-01 — desviación 7) + **0,60h estimadas** del intento 2 (marcador `I1-fix2`, reparto al final)
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
  - **Re-ejecutada tras las correcciones del intento 1** (2026-09-11, después del último cambio, GOT-007):
    `node --test tests/installer.test.mjs` → `tests 59 · pass 59 · fail 0`, **exit 0** (`echo $?`);
    `node --test tests/*.test.mjs` → `tests 69 · pass 69 · fail 0`, **exit 0** (44 previos + 25 nuevos, uno o varios por gap);
    `python scripts/lint_plugin.py` → `9 agentes · 0 errores · 3 avisos`; `python scripts/export-interop.py --check` → `48 ficheros al día`;
    `python -m pytest -q tests/` → `26 failed, 862 passed` = **el MISMO conjunto** de rojos preexistentes de Windows que en `git stash` (diff de los dos `FAILED` ordenados: vacío).
    `--mode copy` sigue siendo **el plan de HEAD**: comparación programática de `buildPlan` de hoy contra el de `git archive HEAD`
    (`claude-code copy/project`, `copy/user`, `opencode/project`, `opencode/user`) → `IGUALES: true` en los cuatro (única
    diferencia, el `aviso` que añadió T-02, que es lo pedido).
    **Prueba real repetida** con `claude` en un `CLAUDE_CONFIG_DIR` temporal (sin tocar el `~/.claude` real),
    `install -p claude-code --scope user --source "<repo>" -y`:

    ```
    Claude Code — plugin nativo — agentes, comandos, skills, hooks y statusline
      → ejecutando $ claude plugin marketplace add C:/…/custom-agents --scope user…
      ✓ $ claude plugin marketplace add C:/…/custom-agents --scope user
      → ejecutando $ claude plugin install custom-agents@daycry --scope user --yes…
      ✓ $ claude plugin install custom-agents@daycry --scope user --yes
      ✓ 2 paso(s) aplicados en C:\…\Temp\ca-real2\cfg\plugins
    ```

    `claude plugin list` → `custom-agents@daycry · Version: 1.19.0 · Scope: user · Status: ✔ enabled`;
    `uninstall -p claude-code --scope user` → `Claude Code (v1.19.0, user, plugin)` y `claude plugin list` → `No plugins installed.`
    (la línea «ejecutando …» es del gap 8: se ve qué se está lanzando ANTES de lanzarlo).
  - **Re-ejecutada tras las correcciones del intento 2** (2026-09-11, después del último cambio, GOT-007):
    `node --test tests/*.test.mjs` → `ℹ tests 93 · ℹ pass 93 · ℹ fail 0`, **exit 0** (`echo $?`);
    `python scripts/lint_plugin.py` → `9 agentes · 0 errores · 3 avisos`; `python scripts/export-interop.py --check` →
    `48 ficheros al día`; `python -m pytest -q tests/` → `26 failed, 862 passed` (mismo conjunto conocido de Windows).
    `--mode copy` **sigue siendo el plan de HEAD**: comparación programática de `buildPlan` de hoy contra el de
    `git archive HEAD` en los cuatro casos → `claude-code/copy/project` y `claude-code/copy/user`
    **IGUALES (sin aviso): true** (única diferencia, el `aviso` que añadió T-02, que es lo pedido) y
    `opencode/plugin/project` y `opencode/plugin/user` **IGUALES: true, avisos iguales: true**.
    **Prueba real repetida** con `claude` en un `CLAUDE_CONFIG_DIR` temporal (`C:\…\Temp\ca-real3\cfg`, sin tocar el
    `~/.claude` real), `install -p claude-code --scope user --source "<repo>" -y`:

    ```
    Claude Code — plugin nativo — agentes, comandos, skills, hooks y statusline
      → ejecutando $ claude plugin marketplace add C:/…/custom-agents --scope user…
      ✓ $ claude plugin marketplace add C:/…/custom-agents --scope user
      → ejecutando $ claude plugin install custom-agents@daycry --scope user --yes…
      ✓ $ claude plugin install custom-agents@daycry --scope user --yes
      ✓ 2 paso(s) aplicados en C:\…\Temp\ca-real3\cfg\plugins
    ```

    `claude plugin list` → `custom-agents@daycry · Version: 1.19.0 · Scope: user · Status: ✔ enabled`;
    `uninstall -p claude-code --scope user` → exit 0 y `claude plugin list` → `No plugins installed.`
- **Desviaciones**:
  3. El apunte del manifiesto de un `exec` lleva, además del `{exec: "<cmd args>"}` informativo del contrato, un campo `deshacer` con el comando inverso cuando el paso lo declara. Sin él no se puede cumplir lo que pide la propia descripción de T-02 («`claude plugin uninstall …` si hay CLI») sin adivinar el comando a partir de una cadena.
  4. Para un `--source` que es una **ruta local**, la fuente se escribe como `{source: "directory", path}` y no como `{source: "github", repo}`: es lo que escribe la CLI oficial de Claude Code (comprobado en el `settings.json` que dejó `claude plugin marketplace add <ruta>` en la prueba real). Para `owner/repo` se mantiene `{source: "github", repo}` del contrato.
  5. El paso `json-set` admite dos campos no previstos en el contrato: `volatiles` (campos de marca de tiempo que no cuentan como cambio, para que reinstalar NO reescriba el registro) y `noQuitar` (claves que se ponen pero que `uninstall` no quita, como el `version: 2` de `installed_plugins.json`, que es del fichero y no nuestra).
  9. `destino()` acepta un tercer argumento `modo`, porque el destino del manifiesto de Claude Code depende de él (`<cfg>/plugins` en plugin, `.claude/` en copy); `status` y `uninstall` miran los dos.
  10. Corrección del **gap 19**: el test `Claude Code sin CLI: registro real, idempotente y desinstalable sin tocar lo del
      usuario` cambia una aserción. Antes comprobaba que tras `uninstall` quedaba `installed_plugins.json` con `version: 2`;
      ahora comprueba que ese fichero **ya no está**, porque lo había creado el instalador y se ha quedado sin nada nuestro
      dentro (el manifiesto lo anota con `creado`). El caso que SÍ conserva `version: 2` — fichero preexistente del usuario —
      pasa a un test nuevo (`gap 19: un fichero del registro que YA existía se conserva`). No se relaja ningún criterio:
      se parte en dos el escenario que la lente pedía distinguir. Para que sobreviva a un reinstall, el manifiesto arrastra
      `creado`/`padresCreados` del manifiesto anterior (si no, la segunda pasada daría el fichero por «del usuario»).
  12. El manifiesto se apunta (con `estado: "incompleto"`) **ANTES** de cada paso `copy`, no solo al final ni solo en el
      `catch`. Los manejadores de señal del gap B-4 no cubren un `taskkill /F` (Windows no ejecuta nada al terminar un
      proceso a lo bruto) y esa es justo la interrupción que deja 159 ficheros sin inventario. Cuesta un JSON pequeño
      por paso; el manifiesto final (`completo`) es idéntico al de antes.
  13. Para el gap B-12 no basta con `taskkill /T /F /PID`: al expirar, Node ya ha matado al hijo directo (el `cmd.exe`),
      así que el árbol ya no existe y el nieto —la CLI de verdad— sobrevive. Se añade un barrido de huérfanos por
      `ParentProcessId` con `wmic`, y los dos se invocan por **ruta absoluta** bajo `System32` (el PATH del usuario
      puede no traerlos). Sin `wmic` (Windows recientes lo retiran) degrada en silencio: nunca peor que antes.
  14. Al conservar los ficheros con cambios locales (gap B-8), el manifiesto del `--mode copy` se retira igual, así que
      esos ficheros quedan **fuera de todo inventario**. Es deliberado —el alternativo es borrarle al usuario lo que
      editó— y se dice en el aviso, que nombra la ruta donde se quedan.
  15. Los tests que validan el `config.toml` con **`tomllib`** llaman a `python3`/`python` solo **si está en la máquina**;
      si no, se quedan en las aserciones de texto. El contrato del instalador es cero dependencias y `node --test`: no
      se puede exigir Python para que la suite pase.
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
- **Tiempo IA (ejec.)**: est. 0,20h · real 0,72h (0,03h + **0,39h medidas** del intento 1 de revisión, reparto abajo; marcador del tramo `installer-registro-real/T-03`, ventana 03:40:44Z–03:43:16Z: `{"fuente": "medido", "tokens_reales": {"entrada": 12, "salida": 5229, "cache_creacion": 9184, "cache_lectura": 1149696, "respuestas": 6}, "eur": 0.7, "horas_ia": 0.03, "duracion": "2m"}`) + **0,30h estimadas** del intento 2 (marcador `I1-fix2`, reparto al final)
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
  - **Re-ejecutada tras las correcciones del intento 1** (2026-09-11, después del último cambio, GOT-007):
    `node --test tests/installer.test.mjs` → `tests 59 · pass 59 · fail 0`, **exit 0** (`echo $?`);
    `node --test tests/*.test.mjs` → `tests 69 · pass 69 · fail 0`, **exit 0** (44 previos + 25 nuevos, uno o varios por gap);
    `python scripts/lint_plugin.py` → `9 agentes · 0 errores · 3 avisos`; `python scripts/export-interop.py --check` → `48 ficheros al día`;
    `python -m pytest -q tests/` → `26 failed, 862 passed` = **el MISMO conjunto** de rojos preexistentes de Windows que en `git stash` (diff de los dos `FAILED` ordenados: vacío).
    Gaps de T-03 en el editor TOML: cabeceras normalizadas (`[plugins.'x']`, `[ plugins . "x" ]` y `[plugins."x"]` son la MISMA
    tabla, sin duplicar), `[[…]]` con ese nombre → error del paso, arrays y cadenas `"""` multilínea no se invaden, el
    `# comentario` de la línea se conserva al cambiar el valor y `uninstall` ya no RE-CREA la tabla que el usuario borró.
  - **Re-ejecutada tras las correcciones del intento 2** (2026-09-11, después del último cambio, GOT-007):
    `node --test tests/*.test.mjs` → `ℹ tests 93 · ℹ pass 93 · ℹ fail 0`, **exit 0** (`echo $?`);
    `python scripts/lint_plugin.py` → `9 agentes · 0 errores · 3 avisos`; `python scripts/export-interop.py --check` →
    `48 ficheros al día`; `python -m pytest -q tests/` → `26 failed, 862 passed` (mismo conjunto conocido de Windows).
    **Gap B-1 (Critical) reproducido y cerrado con `tomllib`** — instalación real en un HOME temporal partiendo de cada
    una de las dos formas que dejaba el usuario:

    ```
    FORMA A (clave con punto)                     FORMA B (tabla en línea)
    # mi config                                   [plugins]
    plugins."custom-agents@daycry".enabled = false   "custom-agents@daycry" = { enabled = false }
    [tui] / theme = "dark"
    ------ después (exit 0) ------                ------ después (exit 0) ------
    plugins."custom-agents@daycry".enabled = true    "custom-agents@daycry" = { enabled = true }
    [tui] / theme = "dark"                        [features] / hooks = true
    [features] / hooks = true
    ------ tomllib ------                         ------ tomllib ------
    PARSEA OK · enabled = True                    PARSEA OK · enabled = True
    ```

    (antes, con la forma B, el instalador apendizaba `[plugins."custom-agents@daycry"]`, salía con exit 0 y mensaje de
    éxito, y `tomllib` daba `Cannot declare ('plugins','custom-agents@daycry') twice`). Tercer caso, sin declaración
    previa: se crea la cabecera como siempre y también parsea. Cuarto: `plugins = { "custom-agents@daycry" = { … } }`
    → **error del paso**, `config.toml` byte a byte intacto y mensaje con el fichero y el cambio a mano.
    `uninstall` sigue poniendo `enabled = false` donde esté declarado (y no re-crea lo que el usuario borró).
  - **No verificable aquí** (igual que en el intento 1): que Codex cargue el plugin → checklist **M-01** (usuario).
- **Desviaciones**:
  6. `correr()` resuelve la ruta real del comando (`where.exe`/`which`) y, en Windows, ejecuta los lanzadores `.cmd`/`.bat` a través de `cmd.exe /d /s /c` con los argumentos entrecomillados a mano. Sin esto Node no puede ejecutar un `codex.cmd`/`claude.cmd` (el caso normal de una instalación por npm) y el paso `exec` degradaba a aviso siempre. `enPath()` pasa a ser `Boolean(rutaDe(cmd))`.
  11. `--force-marketplace` es una **opción nueva** que el contrato de T-03 no preveía: la pide el gap 7 como única vía
      para ejecutar el `remove` + `add` del marketplace del usuario. Por defecto NO se ejecuta: se avisa con el comando
      exacto. (Estaba archivada bajo T-02 por error; movida aquí por el gap A-3 del intento 2.)
  8. El `toml-set` de `[features] hooks` declara `deshacer: false` (no se apunta en el manifiesto): apagar una preferencia global del usuario al desinstalar sería pisarle la configuración. El de `[plugins."custom-agents@daycry"] enabled` sí se apunta y se pone a `false`.
- **Notas**: `codex plugin marketplace add` y `[plugins."<id>"] enabled` están en la doc oficial de Codex («Package plugin»); el flujo lo usa `claude-mem` (`CodexCliInstaller.ts`) con la misma versión mínima.

**Criterios de aceptación**
- [x] `config.toml` del scope con `[plugins."custom-agents@daycry"] enabled = true` y `[features] hooks = true`, sin alterar el resto del fichero
- [x] Con `codex` en PATH se ejecuta `marketplace add` (con recuperación si ya existía — **opt-in**: el `remove` + `add` solo con `--force-marketplace`, ver desviación 11); sin él, aviso con el comando exacto
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

## Revisión de dos lentes — intento 1 (tramo I1: T-01…T-03): 2 Critical, 9 Important, 9 Minor (lentes A+B) — **20/20 corregidos**

> Coordenadas `fichero:linea` de la columna «Evidencia» de esta tabla: las del arbol **en el intento 1**. Las correcciones del intento 2 las desplazaron (p. ej. `leerJsonEstricto` esta hoy en `install.mjs:167` y `ponerRutaEstricta` en `:243`, no en `:146-148/:420`; `podarVacios` en `:950`, no en `:607`; `cortarAnsi` en `:1053`; `avanzarLexico` en `:313`; `resultadoSeleccion` en `:1180`). **Los nombres de funcion son la referencia estable**; se conservan las lineas como registro historico (gap A-2 del intento 2).

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
| 1 (A-1 = B-2) | **Critical** | `json-set` lee con `leerJson` (traga todo error) y aplica `\|\| {}`: un `settings.json`/`installed_plugins.json`/`known_marketplaces.json` que no parsea (BOM de Notepad, coma final, JSONC) se **sustituye entero, sin aviso, exit 0, sin copia**. Reproducido: se pierden `model`, `permissions`, `env` y los demas plugins | T-02 | **Corregido**: `leerJsonEstricto()` (BOM tolerado al leer y conservado al escribir; parseo fallido = error con fichero y motivo) + `ponerRutaEstricta()` (valor no-objeto donde se espera objeto = error). Tests `gap 1` ×3: BOM+coma final, coma final, JSONC y `enabledPlugins: true` → exit 1, mensaje con el fichero, y el fichero **byte a byte** intacto; BOM válido → se instala conservando el BOM | `install.mjs:146-148,420` |
| 2 (B-1) | **Critical** | `rutaDe()` devuelve el **primer** resultado de `where.exe`, que con `npm i -g` es el shim POSIX **sin extension**; `correr()` solo enruta por `cmd.exe` con `.cmd/.bat`, asi que `spawnSync … ENOENT`, exit 1, nada instalado, y el respaldo no entra porque `enPath` dijo si. Con `codex`: «version desconocida < 0.128.0» siendo 0.130.0 -> marketplace nunca registrado mientras se escribe `enabled = true` | T-02/T-03 | **Corregido**: `elegirEjecutable()` recorre TODOS los resultados de `where.exe` y elige por PATHEXT (`.cmd`/`.exe`/`.bat`); `estadoCli()` da `si` / `no` / `no-ejecutable`. Test con el layout npm (shim sin extensión + `claude.cmd`, en ese orden) → elige el `.cmd`; solo shim → respaldo con el aviso «`claude` encontrado pero no ejecutable desde Node … uso el registro directo» (test en win32), nunca ENOENT | `providers.mjs:66` · `install.mjs:290` |
| 3 (A-2) | **Important** | `fuenteRegistro()` clasifica `./ruta` y `../ruta` como repo GitHub (`.` esta en `[\w.-]`): el respaldo escribe `{"source":"github","repo":"./mi-clon"}`, irresoluble; es el ejemplo del `--help` | T-02 | **Corregido**: `clasificarFuente()` — `owner/repo` solo si no empieza por `.`/`~`/`/`/letra de unidad y no existe como directorio; el resto, `directory` con ruta **absoluta**. Test de los 5 casos (`daycry/custom-agents`, `./mi-clon`, `../otro/clon`, `C:
epos\…`, `a/b` existente) | `providers.mjs:79` · `install.mjs:104` |
| 4 (A-3 = B-3) | **Important** | En scope `project`, `destino()` da la MISMA ruta para `plugin` y `copy` (`<dir>/.claude`): el segundo `install` pisa el manifiesto del primero -> 222 ficheros huerfanos que `uninstall` ya no borra (es la via de actualizacion de todo usuario del instalador anterior). Desviacion 9 falsa | T-02 / D6 | **Corregido**: manifiesto **por modo** (`.custom-agents-install.json` copy · `.custom-agents-install.plugin.json` plugin), `sitiosManifiesto()` y `status`/`uninstall` leen los dos; `migrarDeCopy()` avisa y, con `-y`, desinstala el copy antes de instalar el plugin. Tests: copy → plugin → uninstall → **0 huérfanos**; sin `-y` avisa con el comando y no borra nada. Desviación 9 retirada | `providers.mjs:180-182` · `install.mjs:540-541` |
| 5 (B-4) | **Important** | Si un paso lanza, `ejecutar()` sale sin escribir el manifiesto: lo ya aplicado (p. ej. `marketplace add` OK + `plugin install` KO) queda sin registro y `uninstall` se niega. Igual con EPERM en `escribirJson` | T-02 | **Corregido**: el manifiesto se escribe también en el `catch` con `estado: "incompleto"`, los pasos aplicados y el `error`; `escribirJson` lanza con mensaje. Test: `settings.json` ilegible → exit 1, manifiesto `incompleto` con 200+ ficheros, `status` lo marca como «instalación incompleta» y `uninstall` lo acepta y limpia | `install.mjs:450-461,571-574` |
| 6 (B-5) | **Important** | `podarVacios(dest)` barre TODO `~/.claude/plugins` y borra directorios vacios ajenos (`marketplaces/otro-mkt`, `cache/otro-mkt/**`, `repos/`), contra el principio de `install.mjs:17-18` | T-02 | **Corregido**: `podarVacios(dest, man.files)` solo mira los directorios **padres de los ficheros del manifiesto**, de abajo arriba y parando en `dest`. Test: `plugins/marketplaces/otro-mkt`, `plugins/cache/otro-mkt/algo` y `plugins/repos` (vacíos, ajenos) sobreviven; `marketplaces/daycry` sí se va | `install.mjs:607-616` |
| 7 (B-6) | **Important** | `siYaExiste` **borra** el marketplace `daycry` del usuario (otra fuente) y lo re-crea con la nuestra sin preguntar, sin aviso en exito y sin `deshacer`; el comentario dice lo contrario | T-03 | **Corregido**: `siYaExiste.soloConForce`; por defecto no hay `remove`, se avisa con el comando exacto (`codex plugin marketplace remove daycry && …`); `--force-marketplace` lo ejecuta, lo dice y lo anota en el manifiesto (`forzado`). Comentario del código corregido. Test con CLI falsa con estado (el `add` solo funciona tras un `remove`) | `providers.mjs:233-237` · `install.mjs:402-406` |
| 8 (B-7) | **Important** | `correr()` sin `timeout` y con stdout/stderr capturados: una CLI colgada bloquea `npx` sin una linea en pantalla (31 s medidos) | T-02/T-03 | **Corregido**: `TIMEOUT_EXEC` = 120 s (`CUSTOM_AGENTS_EXEC_TIMEOUT_MS` para cambiarlo), línea `→ ejecutando $ <cmd>…` ANTES de cada `exec` y `volcar()` del stdout/stderr capturado cuando falla. Tests: CLI colgada con timeout de 2 s → el instalador termina (< 30 s) y sigue; el valor por defecto se lee en un proceso hijo | `install.mjs:288-295` |
| 9 (B-8) | **Important** | Filas del menu de 82-95 columnas: en 80 columnas cada fila ocupa 2 lineas fisicas y el repintado (`\u001b[NA` con N logicas) descuadra el menu con cada tecla | T-01 | **Corregido**: `cortarAnsi()`/`anchoVisible()` recortan cada fila a `columns - 1` (una fila = una línea física) y el repintado sube las líneas realmente impresas. Test: 200 caracteres → 79 visibles con «…», los códigos ANSI no cuentan y el reset se conserva | `install.mjs:701-716` |
| 10 (B-9) | **Important** | `pintar()` fuera del `try` de `onTecla`: si `stdout.write` lanza (EPIPE) `limpiar()` no corre -> terminal en raw mode y sin cursor | T-01 | **Corregido**: el listener va entero en `try`/`finally` y hay un `process.once("exit", limpiar)` idempotente. Test en proceso hijo que hace reventar `stdout.write` a media tecla → `{"raw":false,"cursor":"ESC[?25h","oyentes":0}` y la promesa rechaza con el error | `install.mjs:727-742` |
| 11 (B-10) | **Important** | `ponerToml` compara la cabecera con `===` literal: `[plugins.'custom-agents@daycry']`, `[ plugins."…" ]` o `[[…]]` -> **segunda tabla** duplicada -> `config.toml` ilegible para Codex | T-03 | **Corregido**: `normalizarTabla()` compara cabeceras sin espacios y con comillas unificadas; `analizarToml()` las localiza fuera de literales; un `[[tabla]]` con ese nombre es **error del paso**. Tests de las 3 variantes (`[plugins."x"]`, `[plugins.'x']`, `[ plugins . "x" ]` → la misma tabla, sin duplicar) y del `[[…]]` | `install.mjs:232-240` |
| 12 (A-4) | Minor | `Changelog` de T-02: 230 caracteres > 200 | T-02 | **Corregido**: 182 caracteres | `tasks.md` T-02 |
| 13 (A-5) | Minor | Fila de progreso: tokens `2,84M` son solo T-02 + T-03 (T-01 perdio el JSON) y no se dice | ledger | **Corregido**: la celda dice «(sin T-01: JSON perdido)» | `tasks.md:73,75` |
| 14 (B-11) | Minor | En la rama `cmd.exe` se expanden `%VAR%` dentro de los argumentos (`%MISECRETO%` -> valor) | T-02 | **Corregido**: `argCmd()` saca el `%` FUERA de las comillas y lo escapa con `^` (`%%` no vale en la línea de comandos, solo en un `.bat`: comprobado). Test de vuelta completa por `cmd.exe` con `MISECRETO` en el entorno → `["%MISECRETO%","C:\con espacios\x","a%b"]` literal | `install.mjs:291-293` |
| 15 (B-12) | Minor | Si un paso lanza se pierden los `avisos` acumulados | T-02 | **Corregido**: los `avisos` acumulados se imprimen en el `catch` de `ejecutar()` antes de relanzar. Test: con `settings.json` ilegible, el aviso «registro escrito en …» (el contexto del fallo) aparece en la salida | `install.mjs:462,520-523` |
| 16 (B-13) | Minor | `uninstall` **re-crea** la tabla del plugin en `config.toml` si el usuario la habia borrado | T-03 | **Corregido**: al deshacer, `ponerToml(..., { soloSiExiste: true })` — si la tabla no está, no se escribe nada. Test: el usuario borra la tabla a mano, `uninstall` deja el `config.toml` **idéntico** | `install.mjs:592-596` |
| 17 (B-14) | Minor | El barrido de fin de tabla (`^\s*\[`) casa lineas de un array multilinea o cadena `"""` y la clave cae dentro del literal | T-03 | **Corregido**: `avanzarLexico()` cuenta `[`/`]` y las cadenas `"""`/`'''` línea a línea, así que ni el barrido de fin de tabla ni la inserción caen dentro de un literal. Test con un array multilínea (con `"[dos]"` dentro) y una cadena `"""` que contiene `[esto no es una tabla]` | `install.mjs:243` |
| 18 (B-15) | Minor | Al reemplazar `enabled = false # comentario` se pierde el comentario, contra el docstring | T-03 | **Corregido**: `partirValor()` separa valor y `# comentario` respetando las cadenas; al reemplazar se conserva el sufijo y su separación. Test: `hooks = false  # lo apagué yo a propósito` → `hooks = true  # lo apagué yo a propósito`; un `#` dentro de una cadena no es comentario | `install.mjs:245-249` |
| 19 (B-16) | Minor | `uninstall` deja `known_marketplaces.json` = `{}`, `installed_plugins.json` = `{"version":2,"plugins":{}}` y `enabledPlugins: {}` que no existian antes | T-02 | **Corregido**: el manifiesto anota `creado` (fichero que no existía), `padresCreados` (objetos intermedios que creó el paso) y `noQuitar`; `uninstall` quita los objetos vacíos que creó y borra el fichero si solo quedaban claves `noQuitar`. Tests: los dos ficheros del registro creados por el instalador desaparecen; uno **preexistente** conserva `version: 2` y `otro@mkt` (desviación 10) | `install.mjs:431-434,590-591` |
| 20 (B-17) | Minor | Enter sin marcar nada se confunde con «no he detectado ningun proveedor» (exit 2) | T-01 | **Corregido**: `resultadoSeleccion()` distingue Enter-sin-marcar (`{vacio:true}`) de «no hay proveedores»: mensaje propio «no has marcado ninguno: no se ha escrito nada» y **exit 0**. Test de las tres salidas del multiselect | `install.mjs:679,494-498` |

**Marcador del intento 1 de revisión** `installer-registro-real/I1-fix1` (único para los 20 gaps, abierto ANTES de tocar
  nada y cerrado al final): `{"fuente":"medido","inicio":"2026-09-11T04:07:21Z","fin":"2026-09-11T05:04:12Z","tokens_reales":{"entrada":269,"salida":116208,"cache_creacion":455407,"cache_lectura":18306574,"respuestas":119},"eur":13.71,"horas_ia":1.19,"duracion":"1h 11m","duracion_reloj":"57m","ratio_usado":479326.0,"ratio_origen":"CALIBRATION.md (mediana de 6)"}`.
  **Reparto por gaps** (1,19h medidas, reparto **aproximado por bloques de trabajo**, no a prorrata exacta; el total coincide con lo medido): T-01 -> gaps 9, 10 y 20 = **0,18h**;
  T-02 → gaps 1, 3, 4, 5, 6, 12, 14, 15 y 19 más la mitad de los compartidos 2 y 8 = 10/20 → **0,62h** (incluye el gap 13,
  que es del ledger); T-03 → gaps 7, 11, 16, 17 y 18 más la otra mitad de 2 y 8 = 6/20 → **0,39h**.

**Fuera de lente, anotado**: `rutaDe` acepta el primer resultado de `where.exe` sin validar extension (secuestro por orden de PATH: lo cubre el gap 2); hasta 4 `where.exe` por paso `exec` (rendimiento, T-19-like); tres comentarios del codigo contradicen lo que hace (gaps 7, 10, 18); tras `uninstall` via CLI queda `daycry` en `known_marketplaces.json` (`marketplace add` sin `deshacer`: conforme a T-02, residuo declarado). La doc (`INTEROP.md`, `INSTALL.md`) sigue describiendo el instalador anterior: es T-06.

## Revision de dos lentes - intento 2 (tramo I1): 20/20 cerrados; nuevos 1 Critical, 7 Important, 8 Minor

Lentes A (conformidad) y B (instaladores CLI multiplataforma) sobre el delta, marcador
`installer-registro-real/revision-I1-intento2`:
`{"eur":20.13,"horas_ia":4.1,"duracion_reloj":"3h 24m","tokens_reales":{"entrada":212,"salida":142522,"cache_creacion":1824476,"cache_lectura":13821869,"respuestas":109},"fuente":"medido"}`.

**Los 20 gaps del intento 1: cerrados los 20** (Lente A los reprodujo uno a uno; 0 residuales). Tambien verificado:
`--mode copy` y OpenCode identicos al plan de HEAD paso a paso; via CLI real (`claude plugin list` -> enabled ->
`uninstall` -> `No plugins installed.`); respaldo sin CLI idempotente byte a byte (md5 de los 3 JSON); `toml-set`
conserva CRLF, comentarios ajenos y el `# comentario` de la propia clave; 0 de los 27 nombres de test de HEAD perdidos,
+42 nuevos (25 con prefijo `gap N:`); `pytest` con el conjunto conocido de rojos de Windows; criterios no reescritos
(0 lineas de criterio tocadas en el diff del ledger); `podarVacios` respeta los directorios ajenos en scope user;
`--force-marketplace` **no** hace nada destructivo por defecto. **Desviaciones 10 y 11: legitimas** (la 11, mal
archivada: ver gap A-3).

**El multiselect con checkboxes y el banner quedan verificados en arnés, no en terminal real** (no hay pty en este
entorno): la comprobacion visual final es tuya, con la checklist M-01.

| # | Grado | Gap | Tarea | Correccion | Evidencia |
|---|---|---|---|---|---|
| B-1 | **Critical** | `ponerToml` solo reconoce la tabla si esta declarada como **cabecera**. Si el usuario la tiene como **clave con punto** (`plugins."custom-agents@daycry".enabled = false`) o como **tabla en linea** (`[plugins]` + `"custom-agents@daycry" = { enabled = false }`) —las dos formas validas que deja quien desactivo el plugin a mano— se apendiza una segunda declaracion y el `config.toml` **deja de parsear**, con exit 0 y mensaje de exito. **Reproducido por el orquestador**: `tomllib` -> `Cannot declare ('plugins','custom-agents@daycry') twice (line 10)`. Codex pierde toda su configuracion | T-03 | **Corregido**: `analizarToml` indexa ahora tambien las ASIGNACIONES con la ruta completa que declaran, y `ponerToml` atiende las tres formas: clave con punto (cambia ESA linea, con su `# comentario`), tabla en linea (`ponerEnTablaEnLinea`, dentro de las llaves; `{}` -> `{ enabled = true }`), declaracion implicita por otra clave del mismo prefijo (clave hermana) y, cuando no se puede hacer con seguridad (`plugins = { "x" = {...} }` anidado), **error del paso** nombrando fichero y forma sin tocar el fichero. 7 tests `gap B-1`; dos instalan de verdad y validan el resultado con **`tomllib`** (`PARSEA OK - enabled = True`) en las dos formas | `install.mjs` `analizarToml` / `ponerToml` / `ponerEnTablaEnLinea` / `partirAsignacion` |
| B-2 | **Important** | `migrarDeCopy` se llama **fuera** del `try/catch` por proveedor: un manifiesto de copy sin `files` (instalador viejo o parcial) lanza `TypeError: man.files is not iterable`, aborta el run entero con stack crudo y **OpenCode no se instala**. Contradice «DEGRADA, NO BLOQUEA» (`install.mjs:19-20`) | T-02 | **Corregido**: la llamada a `migrarDeCopy` va DENTRO del `try` del proveedor, y la propia funcion degrada (manifiesto ilegible o sin `files` -> aviso y seguir); `deshacerInstalacion` y `status` ya no suponen `man.files`. Test: manifiesto `{"plugin":"custom-agents","modo":"copy"}` sin `files` + `install -p claude-code,opencode -y` -> aviso, claude-code se instala, **OpenCode se instala**, exit 0 y ni un stack crudo | `install.mjs` `cmdInstall` / `migrarDeCopy` / `deshacerInstalacion` |
| B-3 | **Important** | Un **segundo** fallo sobrescribe el manifiesto parcial del primero y pierde su `registro`: `uninstall` borra los ficheros pero deja `plugins."custom-agents@daycry"` en `installed_plugins.json` apuntando a un `installPath` ya borrado -> **plugin fantasma** que Claude Code intenta cargar | T-02 | **Corregido**: `guardar()` FUSIONA con el manifiesto previo — union de `files` y `fusionarRegistro()` del registro (misma clave = un apunte; union de `claves`/`padresCreados`/`noQuitar`; `creado` se conserva). Tests: dos fallos seguidos (1.o en `settings.json`, 2.o antes, en `known_marketplaces.json`) -> el manifiesto final sigue apuntando el `installed_plugins.json` del primero y `uninstall` lo deshace (el fichero desaparece: cero plugin fantasma); mas test unitario de `fusionarRegistro` | `install.mjs` `guardar` / `fusionarRegistro` |
| B-4 | **Important** | El manifiesto `incompleto` solo cubre excepciones JS, no **señales**: Ctrl-C a mitad deja 159 ficheros y **cero** manifiesto; `uninstall` responde «no encuentro ningun manifiesto» y quedan huerfanos. Es la interrupcion mas probable de un `npx` de 444 ficheros | T-02 | **Corregido**: `process.on("SIGINT"/"SIGTERM"/"SIGBREAK")` -> `guardar("incompleto")` + salida con 128+senal, y los manejadores se sueltan en el `finally` (el multiselect ya restauraba cursor y raw mode con su `process.once("exit")`). Ademas —desviacion 12— el manifiesto se apunta ANTES de cada paso `copy`, porque un `taskkill /F` no ejecuta ningun manejador. Tests: matar el proceso a mitad de la copia -> hay manifiesto (`incompleto`) y `uninstall` deja 0 huerfanos en agents/skills/commands/hooks; y los manejadores se ponen al empezar (>= 1 durante) y se sueltan al acabar (0) | `install.mjs` `ejecutar` (senales + `guardar` previo al `copy`) |
| B-5 | **Important** | `estadoCli` devuelve `"si"` para extensiones que `correr()` no sabe lanzar (`.ps1`, `.vbs`, `.js`, `.wsf`… todas en el `PATHEXT` por defecto de W11): `claude.ps1` en el PATH -> `spawnSync … EFTYPE`, el paso aborta el proveedor y **el respaldo no se usa** | T-02/T-03 | **Corregido**: `ARRANCABLES` = solo lo que `correr()` lanza (`.EXE`, `.COM`, `.CMD`, `.BAT`); cualquier otra extension del PATHEXT (`.PS1`, `.VBS`, `.JS`, `.WSF`, `.MSC`, `.CPL`) -> `no-ejecutable` -> respaldo con aviso. Tests: unitario de las 6 extensiones (y `.ps1` + `.cmd` conviviendo -> se coge el `.cmd`), e integracion en win32 con `claude.ps1` en el PATH y `PATHEXT` que lo incluye -> «no ejecutable desde Node» y el registro directo escrito | `providers.mjs` `ARRANCABLES` / `preferencia` / `elegirEjecutable` |
| B-6 | **Important** | `elegirEjecutable` prefiere `.CMD` sobre `.EXE`, al reves que el interprete de comandos (que sigue el orden de `PATHEXT`: `.COM;.EXE;.BAT;.CMD`). Con `claude.exe` (instalador nativo) y los shims `.cmd` de npm conviviendo —**el caso de esta maquina**— el instalador ejecuta un lanzador distinto del que usa el usuario | T-02 | **Corregido**: `preferencia()` devuelve el orden de **PATHEXT** filtrado a lo arrancable (defecto de Windows `.COM;.EXE;.BAT;.CMD` si la variable falta o no trae ninguna); comentario del codigo corregido. Test: `claude.cmd` y `claude.exe` juntos -> gana el `.exe`; sin PATHEXT, igual; con `PATHEXT=.CMD;.EXE`, gana el `.cmd` (se le hace caso al usuario) | `providers.mjs` `preferencia` |
| B-7 | **Important** | Los JSON del registro se escriben con `writeFileSync` directo (sin tmp+rename): una interrupcion a mitad deja el `settings.json` del usuario en **0 bytes** (reproducido), y `leerJsonEstricto` trata el fichero vacio como `{}`, asi que la perdida queda **invisible** y la pasada siguiente lo reescribe con solo nuestras claves | T-02 | **Corregido**: `escribirAtomico()` (temporal en el MISMO directorio + `renameSync`) para todos los JSON del registro y tambien para el `toml-set`; y un fichero que YA existia y esta vacio (0 bytes o solo espacios) es **error del paso**, no `{}` (uno que no existe sigue siendo `{}`). Tests de las dos ramas: `settings.json` con solo espacios -> exit 1, mensaje «esta vacio», fichero intacto; sin `settings.json` -> se crea con `enabledPlugins` y no queda ni un `.tmp-` por el camino | `install.mjs` `escribirAtomico` / `escribirJson` / `leerJsonEstricto` |
| B-8 | **Important** | `migrarDeCopy -y` borra **todos** los ficheros del manifiesto de copy sin comprobar que sigan siendo los instalados: un `agents/implementer.md` editado por el usuario desaparece sin aviso y el modo plugin no lo repone. Y `-y` se anuncia en el `--help` «para CI» | T-02 | **Corregido**: `modificado()` compara cada fichero del manifiesto de copy con el del paquete (tamano y, si empata, sha1); los que difieren NO se borran y se listan en un aviso «tienes cambios locales en N fichero(s): los dejo en ...». Test: `agents/implementer.md` editado -> el aviso lo nombra, el fichero sobrevive con su edicion y `agents/reviewer.md` (intacto) si se limpia | `install.mjs` `migrarDeCopy` / `modificado` |
| A-1 = B-10 | Minor | En scope **project** + modo plugin, `uninstall` deja ~150 directorios vacios bajo `<cfg>/plugins`: `podarVacios` se ancla en `dest` (`<dir>/.claude`) mientras los ficheros se escribieron en `<cfg>/plugins`. Residuo, no perdida | T-02 | **Corregido**: `podarVacios` poda en DOS topes — `dest` y el **prefijo comun** de los ficheros que se escribieron fuera de el (`prefijoComun`, que nunca devuelve menos de 3 segmentos). Test scope project + plugin: tras `uninstall` no queda `<cfg>/plugins/cache` ni `marketplaces/daycry`, y el `marketplaces/otro-mkt` ajeno sigue ahi | `install.mjs` `podarVacios` / `podarBajo` / `prefijoComun` |
| B-9 | Minor | `argCmd` dobla las comillas pero no los backslashes que las preceden: `--source "C:\mi clon\"` se come el `--scope` siguiente | T-02 | **Corregido**: `citarCmd()` duplica las `\` que preceden a una `"` (regla MSVCRT), incluida la comilla de cierre. Test: `argCmd("C:\mi clon\")` -> `"C:\mi clon\\"`, y vuelta completa por `cmd.exe` con `--source "C:\mi clon\" --scope user` -> los cuatro argumentos llegan enteros | `install.mjs` `argCmd` / `citarCmd` |
| B-11 | Minor | `CUSTOM_AGENTS_EXEC_TIMEOUT_MS` negativo pasa el `Number(x) \|\| 120_000` y hace fallar todos los `exec` (`timeout out of range`), sin caer al respaldo; `0` se convierte en 120000 sin decirlo | T-02 | **Corregido**: `validarTimeout()` exige entero > 0; si no, aviso (impreso una vez, al primer `exec`) y defecto de 120 s. Test unitario de `-1`, `0`, `abc` y `1.5` (+ los casos validos) y proceso hijo: `TIMEOUT_EXEC` = 120000 con `-1` y con `0` | `install.mjs` `validarTimeout` / `correr` |
| B-12 | Minor | Al expirar el timeout muere `cmd.exe` pero **no su nieto** (queda vivo, comprobado con `tasklist`), y el mensaje dice `ETIMEDOUT` sin nombrar el timeout ni como subirlo | T-02/T-03 | **Corregido**: al expirar se llama a `taskkill /T /F /PID` y, como Node ya ha matado al hijo directo (desviacion 13), se barren ademas los HUERFANOS por `ParentProcessId` con `wmic` — los dos por ruta absoluta bajo `System32`, y si no hay `wmic` degrada en silencio; el mensaje dice «expiro a los N s; si tu maquina necesita mas, sube CUSTOM_AGENTS_EXEC_TIMEOUT_MS». Test en win32 con un nieto que escribe una marca a los 3 s: con timeout de 1 s, la marca NO aparece | `install.mjs` `matarArbol` / `correr` / `expiro` |
| B-13 | Minor | Un manifiesto de copy **ilegible** se ignora en silencio: ni migra ni avisa, y los ~222 ficheros del bundle quedan huerfanos | T-02 | **Corregido** (con B-2): un manifiesto de copy que existe pero no se puede usar se dice con su RUTA y el motivo («no es JSON valido» / «no tiene `files`») y con que el bundle que haya se queda y hay que limpiarlo a mano. Test propio con `{ esto no es json` | `install.mjs` `migrarDeCopy` |
| A-2 | Minor | Las 20 coordenadas `fichero:linea` de la columna «Evidencia» del intento 1 apuntan a codigo no relacionado tras las correcciones | traza | **Corregido** (orquestador): nota bajo el titulo del intento 1 con las coordenadas nuevas de las 5 funciones clave y la regla «los nombres de funcion son la referencia estable» | seccion del intento 1 |
| A-3 | Minor | La desviacion 11 (`--force-marketplace`) esta archivada bajo **T-02** cuando su sujeto es T-03, y el criterio 2 de T-03 sigue diciendo «con recuperacion si ya existia» sin la salvedad de que ahora es **opt-in** | T-03 | **Corregido**: la desviacion 11 (`--force-marketplace`) pasa de T-02 a **T-03**, y el criterio 2 de T-03 lleva el puntero: la recuperacion `remove` + `add` es **opt-in** | `tasks.md` T-02/T-03 |
| A-4 | Minor | El reparto «a prorrata de los 20 senalamientos» no reproduce las horas declaradas y las cuotas suman 19/20 (el total si cuadra con lo medido) | ledger | **Corregido** (orquestador): el reparto se declara **aproximado por bloques de trabajo**, no a prorrata exacta | `tasks.md` reparto de `I1-fix1` |

**Bucle**: intento 3 = **ultimo del bucle acotado**. Lo que no cierre se declara y lo decide el usuario.

**Resultado del intento 3 (correcciones): 15/15 cerrados** — 1 Critical (B-1), 7 Important (B-2…B-8) y 7 Minor
(A-1/B-10, B-9, B-11, B-12, B-13, A-2 y A-4 los cerró el orquestador, A-3 aquí). Ninguno queda «no corregido».
Verificación única de los tres: `node --test tests/*.test.mjs` → `tests 93 · pass 93 · fail 0`, **exit 0** (69 antes,
**24 nuevos**, **0 nombres perdidos**); `lint_plugin` → `0 errores`; `export-interop --check` → `48 ficheros al día`;
`pytest` → el conjunto conocido de rojos de Windows; `--mode copy` y OpenCode = plan de HEAD; prueba real con `claude`
en `CLAUDE_CONFIG_DIR` temporal (instala → `✔ enabled` → `uninstall` → `No plugins installed.`). Las dos formas del
Critical, validadas con `tomllib` (`PARSEA OK · enabled = True`) — el detalle, en la Verificación de T-03.

**Marcador del intento 2 de revisión** `installer-registro-real/I1-fix2` (único para los 15 gaps, abierto ANTES de
tocar nada — `2026-09-11T08:38:42Z` — y cerrado al final — `2026-09-11T09:22:04Z`): el medidor **degradó**
(`"fuente": "estimado"`, aviso `carpeta de transcripciones no disponible`, GOT-010), así que **no hay medida**: las
horas van **estimadas y marcadas como tales**, no medidas. Estimación total **1,00h IA**, obtenida aplicando al reloj
de esta ventana (≈ 48 min de trabajo efectivo) el rendimiento MEDIDO del intento 1 (1,19h IA en 57 min de reloj).
**Reparto por bloques de trabajo observados** (método explícito, **no a prorrata** de los 15 señalamientos): el
analizador TOML del Critical y sus 7 tests → **T-03: 0,30h**; el grueso del instalador (B-2, B-3, B-4, B-7, B-8, B-9,
B-11, B-12, B-13, A-1/B-10 y la parte de `providers.mjs` de B-5/B-6) → **T-02: 0,60h**; solo la convivencia de las
señales con el menú/terminal → **T-01: 0,10h**.

## Revision de dos lentes - intento 3 (tramo I1, ULTIMO del bucle): 15/15 cerrados; nuevo 1 Critical, 2 Minor

Una lente fresca (B, instaladores CLI multiplataforma) sobre el **delta del intento 3** — la conformidad con los
criterios la cerro la Lente A en el intento 2 y el delta es codigo de robustez. Marcador
`installer-registro-real/revision-I1-intento3`:
`{"eur":10.51,"horas_ia":1.6,"duracion_reloj":"24m","tokens_reales":{"entrada":146,"salida":81780,"cache_creacion":685944,"cache_lectura":10177487,"respuestas":73},"fuente":"medido"}`.
**Sin segunda lente en este intento**, dicho.

**Los 15 gaps del intento 2: cerrados los 15.** Verificado ademas: manifiesto fusionado + senales (matar el proceso a
1200 ms deja manifiesto `incompleto` con 429 ficheros, reinstalar sube a 448, `uninstall` deja 0 y 0 huerfanos); dos
fallos encadenados conservan el `registro` del primero y `uninstall` borra el `installed_plugins.json` sin dejar plugin
fantasma; `modificado()` respeta los 3 ficheros con cambios locales (mismo tamano y contenido distinto, 0 bytes,
ilegible) y borra el intacto; `preferencia()` coincide con `cmd /c where` en 7 de 8 PATHEXT (la 8.a es la decision
declarada de B-5); `prefijoComun` devuelve `null` con unidades o raices distintas y nunca poda de mas; `--mode copy` y
OpenCode identicos al plan de HEAD; tres instalaciones seguidas con md5 identico en los 3 JSON y en `config.toml`, sin
temporales sobrantes. Los 11 casos validos de `ponerToml` que quedan parsean con `tomllib`.

| # | Grado | Gap | Tarea | Correccion | Evidencia |
|---|---|---|---|---|---|
| I3-1 | **Critical** | La rama `implicita` de `ponerToml` elige el sitio por la RUTA de la asignacion, sin comprobar si esa asignacion vive en una cabecera **mas profunda** que el objetivo. Si la tabla destino existe solo de forma implicita porque hay una **sub-tabla** suya declarada (`[plugins."custom-agents@daycry".env]`), el `enabled` se escribe DENTRO de la sub-tabla. **Reproducido por el orquestador**: pasada 1 -> exit 0, «223 pasos aplicados» y `plugins = {'custom-agents@daycry': {'env': {'MI_VAR': '1', 'enabled': True}}}` — **Codex no habilita el plugin y el instalador afirma que si**; pasada 2 -> `tomllib: Cannot overwrite a value (line 9)`, se pierden `model` y `mcp_servers`. Es la 4.a forma de la familia de B-1 | T-03 | pendiente (4.a pasada): cerrar la familia **de raiz** con una **post-condicion**: tras escribir, volver a analizar el TOML resultante y comprobar que el camino exacto (`plugins."custom-agents@daycry".enabled` / `features.hooks`) tiene el valor pedido **y que no hay clave duplicada**; si no se cumple, **restaurar el original** y error del paso con el cambio a hacer a mano. Ademas, la rama implicita solo aplica si la asignacion esta en el ambito exacto del objetivo | `install.mjs:594-601` |
| I3-2 | Minor | `escribirAtomico` (tmp + `renameSync`) falla con `EPERM` en Windows si otro proceso tiene el destino **abierto**, donde el `writeFileSync` anterior funcionaba. Forma de fallo nueva introducida por el arreglo de B-7, en la ruta mas caliente | T-02 | pendiente: reintento corto y, si persiste, caida a escritura directa con aviso (la atomicidad se pierde, se dice) | `install.mjs:209` |
| I3-3 | Minor | El `rename` sustituye el inodo: el fichero queda con los permisos del temporal. Un `settings.json` en `600` acaba en `644` (medido en WSL). El mismo codigo si conserva el BOM «para no cambiarle la codificacion al usuario» | T-02 | pendiente: `chmodSync` al modo del original (si existia) tras el `renameSync` | `install.mjs:204-214` |

**Fuera de lente, anotado para el cierre**: `matarArbol` cae al nombre pelado `taskkill`/`wmic` si no los encuentra bajo
System32 (plantado de binario en una ruta que solo se recorre con el entorno roto); el `hint` de Codex afirma que
`enabled = true` queda puesto sin comprobarlo — lo cierra la post-condicion de I3-1.

**Decision**: el bucle acotado estaba en 3/3, pero I3-1 es el fallo exacto que esta iniciativa existe para corregir
(corromper la configuracion del usuario y declarar exito sin verificarlo), asi que el orquestador ordena una **4.a
pasada** con la post-condicion como arreglo estructural, en vez de declararlo y publicarlo.
