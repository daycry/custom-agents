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
| D4 | **OpenCode**: registrar el adaptador en `opencode.json` `plugin: ["./.opencode/plugins/custom-agents-hooks.js"]` en scope project (unión de arrays, como `instructions`) además de copiarlo. **Corregida el 2026-09-11** (desviación 21, confirmada por la Lente A contra `packages/opencode/src/config/plugin.ts`): el literal original de esta decisión, `./plugins/…`, era **incorrecto** — OpenCode resuelve los specs de ruta contra la carpeta del config, que en project es la raíz del proyecto, así que el adaptador no habría cargado | Confiar en la carga automática desde `plugins/`: no está confirmado en la doc y claude-mem lo registra explícitamente |
| D5 | **`/doctor` y `status` comprueban el registro real**: en Claude Code, `installed_plugins.json` / `enabledPlugins` del scope (o `.claude/settings.json`), y si la raíz del plugin es una copia en `.claude/` avisa ⚠️ «bundle copiado: hooks/statusline NO registrados; instala como plugin» con el comando; en Codex, `config.toml` `enabled`; en OpenCode, `opencode.json` `plugin`. El falso positivo de hoy desaparece | Mantener la comprobación de existencia: es lo que ocultó el fallo |
| D6 | **Desinstalación** sigue por manifiesto: en modo plugin el manifiesto apunta al registro escrito (claves y rutas), y `uninstall` deshace eso (o `claude plugin uninstall` si hay CLI) y nada más | — |

**Regla de honestidad:** lo que no se puede probar en esta máquina (Codex y OpenCode reales) no se marca como verificado; va a la checklist M-01 para el usuario y se dice en la Verificación de cada tarea.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — el instalador registra de verdad (Claude Code, Codex, OpenCode) | 3 | 4 | 75% | 7,2h / 7,0h | 3,17h / 0,90h | 0,30h / 0,25h | 30,9M medidos (sin el T-01 original ni el intento 2: JSON perdido / medidor degradado) / 420k |
| Fase 2 — diagnóstico veraz y documentación | 0 | 2 | 0% | 4,2h / 3,0h | 1,65h / 0,40h | 0,20h / 0,10h | 28,2M medidos / 180k |
| **TOTAL** | **3** | **6** | **50%** | **11,4h / 10,0h** | **4,82h / 1,30h** | **0,50h / 0,35h** | **59,1M medidos (sin el T-01 original ni el intento 2) / 600k** |

---

## Fase 1 — el instalador registra de verdad (Claude Code, Codex, OpenCode)

**Estado**: completado · **Estimado**: 7,0h · **Real**: 7,2h humanas (estimado) + 3,17h IA + 0,30h supervisión · **Coste est.**: ≈350 € · **Tokens est.**: 420k · **Tramo**: I1 (T-01…T-03) **completado** (3/4 tareas de la fase), revisión de dos lentes intento 1 cerrada (20/20), intento 2 cerrada (15/15) e intento 3 cerrado en una **4.ª pasada** (3/3: 1 Critical, 2 Minor) · I2 (T-04 **completado**; revisión de dos lentes del tramo I2 intento 1 cerrada, 15/15 corregidos)

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
- **Estado**: completado
- **Tipo**: feature
- **Tiempo humano**: est. 3,0h · real 3,0h (estimado)
- **Tiempo IA (ejec.)**: est. 0,40h · real 1,25h (0,03h + **0,62h medidas** del intento 1 de revisión, reparto abajo; marcador del tramo `installer-registro-real/T-02`, ventana 03:37:17Z–03:40:43Z: `{"fuente": "medido", "tokens_reales": {"entrada": 18, "salida": 4486, "cache_creacion": 8447, "cache_lectura": 1665275, "respuestas": 9}, "eur": 0.92, "horas_ia": 0.03, "duracion": "2m"}`. La medida sale baja porque el grueso del diseño y del código de T-02 se escribió dentro de la ventana de T-01 — desviación 7) + **0,60h estimadas** del intento 2 (marcador `I1-fix2`, reparto al final) + **0,08h medidas** de la 4.ª pasada (marcador `installer-registro-real/I1-fix3`, reparto al final) → **1,33h**
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
  - **Re-ejecutada tras la 4.ª pasada** (2026-09-11, después del último cambio: post-condición de `ponerToml`,
    reintento + caída con aviso y `chmodSync` en `escribirAtomico`):
    `node --test tests/*.test.mjs` → `ℹ tests 103 · ℹ pass 103 · ℹ fail 0`, **exit 0** (`echo $?`, sin `| tail`);
    conjunto de nombres antes/después comparado con `--test-reporter=tap`: **0 perdidos, 10 nuevos**.
    `python scripts/lint_plugin.py` → `9 agentes · 0 errores · 3 avisos`; `python scripts/export-interop.py --check`
    → `48 ficheros al día`. `--mode copy` **sigue siendo el plan de HEAD** (comparación programática de `buildPlan`
    contra `git archive HEAD`, desviación 19): `claude-code/copy/project` y `claude-code/copy/user` iguales sin el
    `aviso` que añadió T-02: **true**; `opencode/plugin/project` y `opencode/plugin/user` **IGUALES: true**.
  - **I3-2** (`escribirAtomico` con el destino abierto): con un handle abierto sobre el fichero, `renameSync` da
    `EPERM` en Windows (medido en un temporal: `rename falla: EPERM`). Con el arreglo, `escribirAtomico` reintenta
    3 veces (60/120 ms) y cae a escritura directa: el fichero queda con el contenido nuevo, no queda ningún `.tmp-`
    por el camino y el aviso dice «… otro proceso lo tiene abierto (EPERM); lo he escrito DIRECTAMENTE, sin
    atomicidad …». Test `gap I3-2: con el destino abierto por otro proceso se escribe igual, y se dice` (en POSIX
    exige lo contrario: rename correcto y **cero** avisos).
  - **I3-3** (permisos): `chmod 600` + `escribirAtomico` → el modo de antes y el de después coinciden
    (test `gap I3-3: el rename no puede cambiarle los permisos al fichero del usuario`). En Windows solo existe el
    bit de solo-lectura y `0600` se lee como `0666` (medido), así que ahí la aserción fuerte es la igualdad
    antes/después; el `0o600` exacto solo se exige en POSIX — **desviación 20**.
  - **Prueba real repetida** con `claude` en un `CLAUDE_CONFIG_DIR` temporal (`C:\…\Temp\ca-real4\cfg`, sin tocar
    el `~/.claude` real), `install -p claude-code --scope user --source "<repo>" -y`:

    ```
      ✓ 2 paso(s) aplicados en C:\Users\460669~1\AppData\Local\Temp\ca-real4\cfg\plugins
    ```

    `CLAUDE_CONFIG_DIR=<tmp> claude plugin list` → `custom-agents@daycry · Version: 1.19.0 · Scope: user ·
    Status: ✔ enabled`; `uninstall -p claude-code --scope user -y` → `Claude Code (v1.19.0, user, plugin)` y
    `claude plugin list` → `No plugins installed.`
- **Desviaciones**:
  17. `escribirAtomico` **puede dejar de ser atómico**: si el `rename` falla con `EPERM`/`EACCES`/`EBUSY` (Windows,
      destino abierto por otro proceso) reintenta 3 veces y, si persiste, escribe directamente encima y lo **avisa**
      nombrando el fichero y diciendo que esa escritura no fue atómica. Es una relajación consciente del arreglo de
      B-7: tumbar la instalación entera porque el editor del usuario tiene abierto el `settings.json` es peor.
      Los avisos salen por un buzón propio (`drenarAvisosEscritura()`, export nuevo) que `ejecutar`/`deshacer` vacían
      en su lista de avisos, para no cambiarle la firma a todas las llamadas de escritura.
  19. La comparación «`--mode copy` = plan de HEAD» **no se puede hacer por CLI**: `HEAD` no conoce la opción
      `--mode` (es de esta misma tarea) y responde `opción desconocida: --mode`. Se hace, como en el intento 2,
      programáticamente sobre `buildPlan`, importando el `providers.mjs` de hoy y el de `git archive HEAD`.
  20. El test de permisos (I3-3) solo puede exigir `0o600` exacto en POSIX: Windows no tiene bits de permiso de
      usuario/grupo/otros y `chmod 600` se lee de vuelta como `0666` (medido en esta máquina). En Windows la
      aserción que queda es la igualdad modo-antes = modo-después, que es justo lo que el `rename` rompía.
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
- **Estado**: completado
- **Tipo**: feature
- **Tiempo humano**: est. 1,5h · real 1,5h (estimado)
- **Tiempo IA (ejec.)**: est. 0,20h · real 0,72h (0,03h + **0,39h medidas** del intento 1 de revisión, reparto abajo; marcador del tramo `installer-registro-real/T-03`, ventana 03:40:44Z–03:43:16Z: `{"fuente": "medido", "tokens_reales": {"entrada": 12, "salida": 5229, "cache_creacion": 9184, "cache_lectura": 1149696, "respuestas": 6}, "eur": 0.7, "horas_ia": 0.03, "duracion": "2m"}`) + **0,30h estimadas** del intento 2 (marcador `I1-fix2`, reparto al final) + **0,22h medidas** de la 4.ª pasada (marcador `installer-registro-real/I1-fix3`, reparto al final) → **0,94h**
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
  - **Re-ejecutada tras la 4.ª pasada** (2026-09-11, después del último cambio). **Las cinco formas** en que un
    `config.toml` puede tener (o no) declarada la tabla, cada una con **dos pasadas seguidas** y `uninstall`, todas
    validadas con **`tomllib`** (oráculo independiente; la tabla de resultados esperados de los tests está escrita a
    mano, no sale del analizador que se prueba). Partiendo siempre de `model = "gpt-5"` + `[mcp_servers.atlassian]`:

    ```
    forma                   pase       parsea  enabled  model    mcp_servers  idempotente
    sin declarar            1.ª        OK      True     'gpt-5'  True         True
    sin declarar            2.ª        OK      True     'gpt-5'  True         True
    sin declarar            uninstall  OK      False    'gpt-5'  True         —
    cabecera                1.ª        OK      True     'gpt-5'  True         True
    cabecera                2.ª        OK      True     'gpt-5'  True         True
    cabecera                uninstall  OK      False    'gpt-5'  True         —
    clave con punto         1.ª        OK      True     'gpt-5'  True         True
    clave con punto         2.ª        OK      True     'gpt-5'  True         True
    clave con punto         uninstall  OK      False    'gpt-5'  True         —
    tabla en línea          1.ª        OK      True     'gpt-5'  True         True
    tabla en línea          2.ª        OK      True     'gpt-5'  True         True
    tabla en línea          uninstall  OK      False    'gpt-5'  True         —
    sub-tabla implícita     1.ª        OK      True     'gpt-5'  True         True
    sub-tabla implícita     2.ª        OK      True     'gpt-5'  True         True
    sub-tabla implícita     uninstall  OK      False    'gpt-5'  True         —
    [features.web] + hooks  1.ª/2.ª    OK      True (features.hooks; features.web.search intacto)   True
    ```

    (`enabled` es `plugins["custom-agents@daycry"]["enabled"]` leído por `tomllib`, que es donde lo busca Codex.)
    En la **sub-tabla implícita** el `MI_VAR = "1"` del usuario sigue en su sitio: `enabled` ya no cae dentro de
    `env`, la super-tabla se declara después (TOML lo permite) y la 2.ª pasada es byte a byte idéntica — antes daba
    `Cannot overwrite a value (line 9)` y se perdían `model` y `mcp_servers`.
  - **Instalación real** sobre la forma reproducida por el orquestador (test `gap I3-1: instalar de verdad sobre la
    sub-tabla implicita — dos pasadas y uninstall`, verde): `install -p codex --scope user -y` en un HOME temporal →
    `tomllib` ve `enabled = True`, `env.MI_VAR = "1"` y `model = "gpt-5"`; **segunda** pasada → igual (ya no se
    pierden `model` ni `mcp_servers`); `uninstall` → `enabled = False` y `model` intacto.
  - **Post-condición** (lo que cierra la familia de raíz, desviación 16): `ponerToml` re-analiza el texto que va a
    escribir y exige que `plugins."custom-agents@daycry".enabled` / `features.hooks` quede declarado **una sola vez**
    y con el valor pedido; si no, **no devuelve texto**: lanza, el fichero se queda como estaba y el mensaje nombra
    el fichero, la forma encontrada y el cambio a mano. Test `gap I3-1: la post-condicion NO escribe si la clave no
    habria quedado unica` (fichero con `enabled` declarado dos veces → error «… la clave habría quedado declarada
    2 veces (fichero ilegible) …», fichero intacto).
  - `node --test tests/*.test.mjs` → `ℹ tests 103 · ℹ pass 103 · ℹ fail 0`, **exit 0**; **0 nombres perdidos**, 10
    nuevos. `python scripts/lint_plugin.py` → `0 errores`; `python scripts/export-interop.py --check` → `48 ficheros
    al día`.
  - **No verificable aquí** (igual que en el intento 1): que Codex cargue el plugin → checklist **M-01** (usuario).
- **Desviaciones**:
  16. El Critical I3-1 **no** se cierra con una quinta rama en el editor TOML, sino con una **post-condición**:
      `ponerToml` valida lo que va a escribir y, si el camino exacto no queda declarado una sola vez con el valor
      pedido, **falla el paso sin tocar el fichero**. Efecto secundario declarado: ficheros que antes se escribían
      (mal) ahora pueden dar error del paso — por ejemplo un `config.toml` que ya traía la clave duplicada. Es
      deliberado: un error honesto con el cambio a mano vale más que un `config.toml` corrupto con exit 0. La rama
      `implicita` además solo aplica si la asignación vive en el **ámbito exacto** del objetivo.
  18. La matriz **5 formas × 2 pasadas × uninstall** se prueba sobre `ponerToml` (con `tomllib` validando cada texto
      producido) más **una** instalación real por CLI con la forma que reprodujo el orquestador, en vez de 15
      instalaciones reales: cada `install` por CLI cuesta ~4,5 s de suite y lo que se quiere fijar es el TEXTO del
      `config.toml`, que es justo lo que compara la tabla de arriba.
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

- **Descripción**: en el paso `merge` de `opencode.json` añadir `plugin: ["./.opencode/plugins/custom-agents-hooks.js"]` (scope project, **ver desviación 21**) o la ruta absoluta bajo `~/.config/opencode/plugins/` (scope user), como unión de arrays sin duplicar; `uninstall` la deja (es config del usuario) y ahora lo **avisa nombrando la entrada**, porque el fichero al que apunta sí se borra.
- **Changelog**: En OpenCode el instalador registra el adaptador de hooks en `opencode.json`, además de copiarlo.
- **Estado**: en-progreso
- **Tipo**: feature
- **Tiempo humano**: est. 1,0h · real 1,2h
- **Tiempo IA (ejec.)**: est. 0,10h · real 0,32h (medido: 0,16h de la implementación + 0,16h de la corrección de la revisión I2)
- **Supervisión**: est. 0,05h · real 0,10h
- **Previsión IA**: 40k in / 5k out tok · **real medido**: `{"eur":2.14,"horas_ia":0.16,"duracion_reloj":"7m","tokens_reales":{"entrada":64,"salida":14829,"cache_creacion":60016,"cache_lectura":3149739,"respuestas":32},"fuente":"medido"}` · **+ corrección de la revisión I2**: 0,16h IA y ≈2,4M tokens medidos (marcador `installer-registro-real/I2-fix1`; el JSON completo y el reparto, al pie de la sección de revisión)
- **Dependencias**: —
- **Archivos**: `install/providers.mjs`, `install/install.mjs`, `tests/installer.test.mjs`
- **Verificación**:
  - `node install/install.mjs install -p opencode -y --dir <tmp>` → `opencode.json` con `plugin` además de `instructions`/`permission`; reinstalar → igual; usuario con `plugin: ["otro"]` → `["otro", …]`
  - `node --test tests/*.test.mjs` → verde
  - **No verificable aquí**: que OpenCode cargue el adaptador → **M-01**
- **Desviaciones**:
  21. **La ruta literal de D4 (`./plugins/custom-agents-hooks.js`) es incorrecta en scope `project` y se cambia por `./.opencode/plugins/custom-agents-hooks.js`.** Evidencia en el código de OpenCode (`packages/opencode/src/config/plugin.ts`, `resolvePluginSpec`: «Path-like specs are resolved relative to the config file that declared them»): en scope `project` el config vive en la RAÍZ del proyecto y el adaptador en `.opencode/plugins/`, así que `./plugins/…` resolvería a `<proyecto>/plugins/…`, que no existe. `resolvePathPluginTarget` no comprueba que el fichero esté ahí —devuelve la ruta resuelta—, así que el fallo llega **al importarlo**: OpenCode publica un `Failed to load plugin` en la sesión del usuario (peor que no registrar nada). En scope `user` config y adaptador comparten carpeta, así que la ruta absoluta de D4 vale tal cual. El test no fija la cadena a mano: comprueba que `resolve(dirname(config), spec)` es **el fichero que el plan copia**.
  21-bis. **La premisa de D4 («la carga automática desde `plugins/` no está confirmada en la doc») era falsa**: la doc oficial (`opencode.ai/docs/plugins`, «Files in these directories are automatically loaded at startup») y el código (`ConfigPlugin.load`, glob `{plugin,plugins}/*.{ts,js}`) confirman el autodescubrimiento. **Se mantiene el registro explícito igualmente** por dos razones: no duplica la carga (`deduplicatePluginOrigins` desempata por URL de fichero, y ambas vías normalizan a la misma) y hace el registro **comprobable** por `/doctor` y `status` (T-05), que es el objetivo de la iniciativa. Queda dicho para que M-01 lo contraste en un OpenCode real.
  21-ter. **`uninstall` gana un aviso nuevo.** Dejar `plugin` sin decir nada no es neutral como con `instructions`: el fichero al que apunta sí se borra y un spec de ruta colgante hace que OpenCode se queje al arrancar. Se añade `notaDesinstalar` al proveedor (una línea `!` al desinstalar) en vez de tocar la config del usuario.

```console
$ node install/install.mjs install -p opencode -y --dir <tmp> -q   # exit 0
$ cat <tmp>/opencode.json
{
  "$schema": "https://opencode.ai/config.json",
  "instructions": [".opencode/custom-agents-index.md"],
  "plugin": ["./.opencode/plugins/custom-agents-hooks.js"],
  "permission": { "skill": { "*": "allow" } }
}
$ node install/install.mjs install -p opencode -y --dir <tmp> -q   # reinstalar
['./.opencode/plugins/custom-agents-hooks.js']                      # sin duplicar

$ echo '{"plugin":["otro"]}' > <tmp2>/opencode.json && node install/install.mjs install -p opencode -y --dir <tmp2> -q
['otro', './.opencode/plugins/custom-agents-hooks.js']
$ node install/install.mjs uninstall -p opencode --dir <tmp2>
OpenCode (v1.19.0, project, plugin)
  ✓ 220 fichero(s) borrado(s). La configuración fusionada (opencode.json, marketplace.json) NO se toca: es tuya.
  ! tu `opencode.json` conserva `instructions` y `plugin` (`./.opencode/plugins/custom-agents-hooks.js`): es tuyo y
    no lo toco, pero el adaptador ya no está — quita esa entrada de `plugin` o OpenCode se quejará al arrancar
['otro', './.opencode/plugins/custom-agents-hooks.js']              # uninstall no la toca

$ node --test tests/*.test.mjs
ℹ tests 105   ℹ pass 105   ℹ fail 0
```

**Verificación re-ejecutada tras la corrección de la revisión I2** (gaps B-5 y A-9):

```console
$ node install/install.mjs install -p opencode -y --dir <tmp1> -q     # exit 0
$ cat <tmp1>/opencode.json
  "plugin": [ "./.opencode/plugins/custom-agents-hooks.js" ]          # igual que antes

$ echo '{"plugin":"mi-plugin.js"}' > <tmp2>/opencode.json             # el escalar del usuario (gap B-5)
$ node install/install.mjs install -p opencode -y --dir <tmp2>
  ! <tmp2>\opencode.json: plugin: tu valor "mi-plugin.js" no era una lista; lo conservo como primer elemento
['mi-plugin.js', './.opencode/plugins/custom-agents-hooks.js']        # ya no desaparece, y va delante

$ node --test tests/*.test.mjs
ℹ tests 114   ℹ pass 114   ℹ fail 0                                   # 108 → 114, ningún nombre perdido
```

**Criterios de aceptación**
- [x] `plugin` registrado en ambos scopes con la ruta correcta; unión sin duplicar; el `plugin` previo del usuario se conserva

**Subtareas**
- [x] `merge` con `plugin` + test (`rutaPluginOpencode()`, 2 tests nuevos: forma por scope y unión/idempotencia/uninstall)
  - commit `T-04: …` — lo hace el orquestador tras la revisión

---

## Fase 2 — diagnóstico veraz y documentación

**Estado**: completado · **Estimado**: 3,0h · **Real**: 4,2h humanas (estimado) + 1,65h IA + 0,20h supervisión · **Coste est.**: ≈150 € · **Tokens est.**: 180k · **Tokens reales**: 28,2M medidos (T-05 + T-06, incluidos los ≈12,1M de la corrección de la revisión I2) · **Tramo**: I2 (T-04…T-06) **completado**, revisión de dos lentes intento 1 cerrada (8 Important + 7 Minor, 15/15 corregidos)

### T-05 — `/doctor` y `status` comprueban el registro real, no la existencia de ficheros

- **Descripción**: `agent-kits/shared/doctor.py`, bloque «Plugin»: (1) determinar cómo está instalado — `plugin` (raíz bajo `<CLAUDE_CONFIG_DIR>/plugins/cache/…` o `custom-agents@…` en `installed_plugins.json`/`enabledPlugins` del scope) o `copia` (raíz en `<proyecto>/.claude` o `~/.claude` sin entrada en el registro); (2) fila «hooks registrados»: ✅ solo en modo plugin (y con `hooks/hooks.json` válido); en modo copia ⚠️ «bundle copiado a `.claude/`: Claude Code NO lee `hooks/hooks.json` fuera de un plugin — hooks, statusline y namespace no disponibles» con arreglo `npx @daycry/custom-agents install -p claude-code` (o `/plugin marketplace add daycry/custom-agents` + `/plugin install custom-agents`); (3) fila nueva «registro del plugin»: dónde está registrado (fichero y scope) o ❌ si `enabledPlugins` lo tiene en `false`. `install.mjs status`: por proveedor, además del manifiesto, «registrado: sí/no» leyendo lo mismo (Claude: `installed_plugins.json`/`enabledPlugins`; Codex: `config.toml` `enabled`; OpenCode: `opencode.json` `plugin`). Tests en `agent-kits/shared/test_doctor.py` con fixtures de los dos modos; `--json` gana las claves nuevas sin quitar ninguna.
- **Changelog**: `/doctor` y `status` dicen si el plugin está registrado de verdad en cada runtime; una copia del bundle en `.claude/` ya no pasa por «hooks registrados».
- **Estado**: en-progreso
- **Tipo**: fix
- **Tiempo humano**: est. 2,0h · real 2,5h
- **Tiempo IA (ejec.)**: est. 0,25h · real 0,86h (medido: 0,24h de la implementación + 0,62h de la corrección de la revisión I2)
- **Supervisión**: est. 0,05h · real 0,10h
- **Previsión IA**: 90k in / 12k out tok · **real medido**: `{"eur":4.97,"horas_ia":0.24,"duracion_reloj":"11m","tokens_reales":{"entrada":100,"salida":36337,"cache_creacion":79716,"cache_lectura":7999811,"respuestas":50},"fuente":"medido"}` · **+ corrección de la revisión I2**: 0,62h IA y ≈9,4M tokens medidos (marcador `installer-registro-real/I2-fix1`; el JSON completo y el reparto, al pie de la sección de revisión)
- **Dependencias**: T-02 (formato del registro escrito)
- **Archivos**: `agent-kits/shared/doctor.py`, `agent-kits/shared/test_doctor.py`, `install/install.mjs`, `install/providers.mjs`, `tests/installer.test.mjs`, `commands/doctor.md`, `interop/codex/prompts/doctor.md`, `interop/opencode/commands/doctor.md`
- **Verificación**:
  - Reproducción del falso positivo: HOME temporal + `install -p claude-code --mode copy -y --dir <tmp>` + `python <tmp>/.claude/agent-kits/shared/doctor.py` → fila hooks ⚠️ con el arreglo (antes ✅); pegado
  - Este repo real (plugin instalado desde el marketplace `daycry`): `python agent-kits/shared/doctor.py --json` → `registro: plugin`, hooks ✅; el resto del JSON idéntico salvo las claves nuevas (diff con HEAD pegado)
  - `python -m pytest -q agent-kits/shared/test_doctor.py -p no:cacheprovider` → verde (conjunto idéntico + nuevos; los 2 rojos de Windows preexistentes iguales)
  - `node install/install.mjs status` en el HOME temporal → «registrado: sí» tras T-02 y «no» tras `--mode copy`
- **Notas**: la doc del comando es `commands/doctor.md` (**desviación 22**: `docs/agents/doctor.md` no existe — `/doctor` es un comando, no un agente); al tocarla hay que regenerar la interop. Copias `--8<--` de `doctor.py` (registradas en `copias.json`) sin tocar: `pytest tests/test_copias_declaradas.py` verde.
- **Desviaciones**:
  22. La doc que pedía la tarea (`docs/agents/doctor.md`) **no existe**: `/doctor` es un comando. Se actualiza `commands/doctor.md` (nota nueva con los dos modos y las dos filas) y, por la regla de interop del repo, se regenera `interop/{codex/prompts,opencode/commands}/doctor.md` — dos ficheros generados que entran en `Archivos`.
  23. `registro(scope, dir)` de Claude Code es **por scope** (project mira `<dir>/.claude/settings.json`; user, los dos ficheros de `<CLAUDE_CONFIG_DIR>`). La primera versión miraba los tres en ambos scopes y el `status` decía «project: registrado: sí» por una entrada de USER — cierto pero engañoso. `/doctor`, en cambio, sigue mirando los tres (y dice el scope de cada uno): ahí la pregunta es «¿lo carga esta máquina?», no «¿en qué scope está?».
  24. Los tests nuevos fijan `CLAUDE_CONFIG_DIR` a un temporal (`monkeypatch`). Sin eso, en una máquina con el plugin instalado de verdad —esta— el modo salía `plugin` por el `~/.claude` real y el test verde no probaba nada; en CI salía `desconocido`. Ninguno tocaba nada, pero el veredicto dependía de la máquina.

**El falso positivo, reproducido y corregido** (HOME, USERPROFILE y `CLAUDE_CONFIG_DIR` temporales; el mismo proyecto copiado, el mismo fixture, solo cambia la versión de `doctor.py`):

```console
$ node install/install.mjs install -p claude-code --mode copy -y --dir <tmp>/proj -q     # 221 ficheros
$ cd <tmp>/proj && python .claude/agent-kits/shared/doctor.py     # ANTES (doctor.py de HEAD)
| ✅ | hooks registrados | PostToolUse (3) · SubagentStop (1) · SessionStart (1) · SessionEnd (1) ·
       UserPromptSubmit (1) — todos existen y son ejecutables | — |      ← falso positivo

$ python .claude/agent-kits/shared/doctor.py                      # DESPUÉS
| ✅ | raíz del plugin | …\proj\.claude · 9 agentes · 17 skills · 12 comandos · instalación: copia | — |
| ⚠️ | registro del plugin | sin entrada de `custom-agents@…` en <tmp>/home/.claude — el bundle está
       copiado, no instalado | npx @daycry/custom-agents install -p claude-code (o `/plugin marketplace
       add daycry/custom-agents` + `/plugin install custom-agents`) |
| ⚠️ | hooks registrados | PostToolUse (3) · … declarados en `hooks/hooks.json`, pero el bundle está
       copiado a `.claude/`: Claude Code NO lee `hooks/hooks.json` fuera de un plugin — hooks,
       statusline y namespace no disponibles | npx @daycry/custom-agents install -p claude-code … |
exit=0   (degrada, no bloquea)
```

**Este repo** (plugin instalado desde el marketplace `daycry`), `doctor.py --json --plugin-root .` contra HEAD — **solo suma**:

```diff
-          "detalle": "…/custom-agents · 9 agentes · 17 skills · 12 comandos",
+          "detalle": "…/custom-agents · 9 agentes · 17 skills · 12 comandos · instalación: plugin",
+        },
+        {
+          "estado": "ok",
+          "que": "registro del plugin",
+          "detalle": "custom-agents@daycry en C:\\Users\\…\\.claude\\plugins\\installed_plugins.json
+                      (installed_plugins.json, scope user) · custom-agents@daycry en
+                      C:\\Users\\…\\.claude\\settings.json (enabledPlugins, scope user)",
+      "modo": "plugin",
+      "registro": [ {…"habilitado": null}, {…"habilitado": true} ]
-    "ok": 12,
+    "ok": 13,
```

La fila «hooks registrados» sigue ✅ (`criterio de lint_plugin.py`) y ninguna clave del JSON de HEAD desaparece: el diff completo son esas dos filas nuevas, el sufijo del detalle y el recuento.

**`status`** (mismo HOME temporal; `claude` sí estaba en el PATH, así que el modo plugin se instaló por la CLI oficial):

```console
$ node install/install.mjs status --dir <tmp>/proj        # solo el bundle copiado
  Claude Code   runtime no detectado
      ✓ project/copy: v1.19.0, 221 fichero(s) …\proj\.claude
      ! project: registrado: no — el runtime no lo carga; falta darlo de alta

$ node install/install.mjs install -p claude-code --scope user -y --dir <tmp>/proj -q
$ node install/install.mjs status --dir <tmp>/proj
  Claude Code   runtime detectado
      ✓ project/copy: v1.19.0, 221 fichero(s) …\proj\.claude
      ! project: registrado: no — el runtime no lo carga; falta darlo de alta
      ✓ user/plugin: v1.19.0, 0 fichero(s) …\home\.claude\plugins
      ✓ user: registrado: sí …\home\.claude\plugins\installed_plugins.json
```

```console
$ python -m pytest -q agent-kits/shared/test_doctor.py -p no:cacheprovider
2 failed, 39 passed in 30.22s
FAILED test_hook_sin_bit_ejecutable_es_aviso_con_chmod      ← los 2 rojos preexistentes de Windows
FAILED test_repo_real_la_memoria_ya_no_pasa_en_silencio        (mismo CONJUNTO que en la línea base)

$ python -m pytest -q tests/test_copias_declaradas.py -p no:cacheprovider
18 passed in 0.49s                                          ← copias `--8<--` intactas
```

**Verificación re-ejecutada tras la corrección de la revisión I2** (gaps B-1, B-2, A-3, A-4, B-3, B-6, B-7, A-2):

```console
$ python -m pytest -q agent-kits/shared/test_doctor.py -p no:cacheprovider
2 failed, 52 passed in 30.67s        # 41 → 54 tests; el CONJUNTO de rojos, los 2 preexistentes de Windows

# gap B-3, la máquina contaminada (`custom-agents@otro: false` en el CLAUDE_CONFIG_DIR):
$ CLAUDE_CONFIG_DIR=<tmp-otro> python -m pytest -q agent-kits/shared/test_doctor.py -p no:cacheprovider
2 failed, 52 passed in 28.21s        # ANTES de la corrección, con ese mismo cfg: 14 failed, 27 passed

# gaps A-3 y A-4: el MISMO estado (alta en installed_plugins + `enabledPlugins: false`)
$ CLAUDE_CONFIG_DIR=<tmp>/cfg node install/install.mjs status --dir <tmp>/proj
  ! user: registrado: no — está dado de alta pero APAGADO en <tmp>\cfg\settings.json: el runtime lo ignora
$ CLAUDE_CONFIG_DIR=<tmp>/cfg python agent-kits/shared/doctor.py --root <tmp>/proj --plugin-root .
| ❌ | registro del plugin | `custom-agents@daycry` … (scope user) como `false`: Claude Code lo ignora entero | …
| ⚠️ | hooks registrados  | … pero el plugin NO está activo en el registro (ver «registro del plugin») | …
exit=1                                # las dos herramientas, el mismo veredicto

$ python agent-kits/shared/doctor.py --plugin-root . --json     # este repo, plugin instalado de verdad
modo=plugin · registro=2 fuentes · ok 13 · aviso 1 · error 0 · exit 0
  ℹ️ | registro en Codex    | Codex está en esta máquina (…\.codex) y el plugin no está instalado ahí — opcional: …
  ℹ️ | registro en OpenCode | OpenCode no está en esta máquina: nada que comprobar
```

**Criterios de aceptación**
- [x] Modo copia → hooks ⚠️ con arreglo; modo plugin → ✅ y fila «registro» con fichero/scope; `enabledPlugins: false` → ❌
- [x] `status` informa «registrado» por runtime desde los ficheros reales
- [x] `--json` compatible hacia atrás; copias `--8<--` intactas

**Subtareas**
- [x] `modo_instalacion()` + `registro_plugin()` + filas en `doctor.py` con 6 tests nuevos
- [x] `status` en `install.mjs` (`leerRegistro()` + descriptores `registro()` por proveedor) con 3 tests nuevos
- [x] `commands/doctor.md` (+ interop regenerada)
  - commit `T-05: …` — lo hace el orquestador tras la revisión

### T-06 — Documentación, checklist M-01 y CHANGELOG

- **Descripción**: `docs/INTEROP.md` §1 (la vía corta: qué hace ahora en cada runtime, `--mode`, `--source`, `CLAUDE_CONFIG_DIR`, respaldo sin CLI y por qué) y §4 (tabla de degradación: fila «registro del plugin» por runtime); `docs/en/INTEROP.md` espejo; `docs/INSTALL.md` Vía 0 (y nota en Vías 1/2: «equivale a `--mode copy`, sin hooks») + `docs/en/INSTALL.md`; `README.md`/`README.es.md` sección de instalación; `install.mjs --help` al día. **Checklist M-01** (aquí, al final del ledger): pasos que el usuario ejecuta en su máquina con Codex y OpenCode reales y qué debe ver; se marca cuando él lo confirme, no antes. CHANGELOG EN/ES por `changelog-sync` al cerrar (`estado: completado`).
- **Changelog**: Documentación del instalador al día (modos, fuente, respaldo sin CLI) y checklist de verificación manual en Codex y OpenCode.
- **Estado**: en-progreso
- **Tipo**: docs
- **Tiempo humano**: est. 1,0h · real 1,7h
- **Tiempo IA (ejec.)**: est. 0,15h · real 0,79h (medido: 0,61h de la implementación + 0,18h de la corrección de la revisión I2)
- **Supervisión**: est. 0,05h · real 0,10h
- **Previsión IA**: 60k in / 8k out tok · **real medido**: `{"eur":5.54,"horas_ia":0.61,"duracion_reloj":"17m","tokens_reales":{"entrada":74,"salida":18896,"cache_creacion":275557,"cache_lectura":7652328,"respuestas":37},"fuente":"medido"}` · **+ corrección de la revisión I2**: 0,18h IA y ≈2,7M tokens medidos (marcador `installer-registro-real/I2-fix1`; el JSON completo y el reparto, al pie de la sección de revisión)
- **Dependencias**: T-01…T-05
- **Archivos**: `docs/INTEROP.md`, `docs/en/INTEROP.md`, `docs/INSTALL.md`, `docs/en/INSTALL.md`, `README.md`, `README.es.md`, `install/install.mjs` (texto de `--help`), `docs/roadmap/2026-09-11-installer-registro-real/tasks.md` (M-01)
- **Verificación**:
  - `python scripts/lint_plugin.py` → `0 errores`; `python evals/check.py` → 0; `python scripts/export-interop.py --check` → `48 ficheros al día`; `python -m pytest -q tests/test_ci_manual_copy.py tests/test_export_interop.py -p no:cacheprovider` → verde
  - `grep -n "mode copy\|--source\|CLAUDE_CONFIG_DIR" docs/INTEROP.md docs/en/INTEROP.md docs/INSTALL.md docs/en/INSTALL.md` → presente en los cuatro
  - Criterio de prosa (`docs-style.md`) revisado por la Lente A
  - `python skills/changelog-sync/scripts/changelog-sync.py --check --only 2026-09-11-installer-registro-real` (al cerrar; el script NO acepta ruta posicional — gap A-5) → entradas EN/ES generadas
- **Desviaciones**:
  25. **Los CHANGELOG no se tocan aquí.** El campo `- **Changelog**:` de cada T-01…T-06 ya está escrito (es lo que copia `changelog-sync`), pero las entradas se generan al cerrar la iniciativa (`estado: completado`), que no es de esta tarea. `CHANGELOG.md`/`CHANGELOG.es.md` salen de `Archivos`; el comando queda en la `Verificación`.
  27. **El criterio 3 de T-06 vuelve a su literal de HEAD, pero como viñeta.** A-1 pide tres cosas a la vez —literal de HEAD, sin marcar y T-06 `completado`— y `ledger-lint.py` tiene una incoherencia dura justo ahí (`completado` con `- [ ]` en el bloque de criterios, línea 407). Como el texto del criterio **no se puede tocar** (es lo que señala el gap) y el trabajo que describe no es de esta tarea (desviación 25), se restaura **literal y entrecomillado** como viñeta sin checkbox: queda visible que está abierto, no se marca lo que no está hecho y la puerta mecánica sigue en verde. Alternativas descartadas: marcarlo `[x]` (la mentira que el gap rechaza) y dejar T-06 `en-progreso` (bloquea el cierre del tramo sin ganar información).
  28. **`/doctor` respeta `CODEX_HOME` y, para no divergir, el instalador también.** Las filas nuevas de Codex leen `CODEX_HOME` antes de `~/.codex` (es lo que hace Codex), así que `install/providers.mjs` gana `codexHome()` con el mismo criterio: si las dos piezas leyeran sitios distintos volverían a poder contradecirse, que es justo el defecto A-3. Es un cambio de una línea en el proveedor, fuera de los 15 gaps y por eso declarado.
  29. **La regla de precedencia entre scopes se fija aquí**: manda el scope más específico que se pronuncia (`project` sobre `user`) y, dentro de él, un `false` explícito gana a cualquier alta; sin pronunciamiento, un alta de `installed_plugins.json` basta. **Rectificado el 2026-09-11 (revisión I2, intento 2)**: Claude Code **sí** documenta la precedencia — `settings-reference#enabledplugins` da `Scope: Any file` y `settings#settings-precedence` fija «Managed > command line > Project local > Shared project > User». El orden implementado coincide con el documentado, pero faltan dos niveles (`local` = `.claude/settings.local.json`, donde escribe `claude plugin disable --scope local`, y `managed`): es el gap **I2-1**. La regla queda escrita en el docstring de `estado_plugin()` y en `commands/doctor.md`, ahora con la cita de la doc.
  26. **`scope-check.py` sale con 1 por seis ficheros que no son del tramo I2.** Los 17 ficheros tocados en I2 están todos en alcance; los 6 que sobran (`.gitignore`, `.claude/.gitignore`, `CONTINUE-HERE.md`, `docs/roadmap/README.md`, `docs/roadmap/2026-09-04-changelog-brief/tasks.md`, `skills/changelog-sync/references/medicion-escalera.md`) vienen de **commits anteriores del orquestador** en esta rama (fila del índice, cifras re-medidas, estado de la sesión), no de ninguna tarea. No se añaden a `Archivos` de T-04…T-06 —no son suyos— ni se revierten. Lo resuelve el orquestador al cerrar la rama; queda dicho aquí para que la revisión no lo lea como alcance colado.

```console
$ python scripts/lint_plugin.py
lint_plugin: 9 agentes · 0 errores · 3 avisos        ← los 3 avisos son los de siempre (nombres genéricos)

$ python evals/check.py
evals/check: 38 ficheros · 135 casos (80 positivos, 55 negativos) · 38 piezas del repo · 0 errores

$ python scripts/export-interop.py --check
export-interop --check: 48 ficheros al día

$ python -m pytest -q tests/test_copias_declaradas.py tests/test_ci_manual_copy.py \
      tests/test_export_interop.py agent-kits/shared/test_doctor.py -p no:cacheprovider
2 failed, 84 passed in 21.63s                        ← los 2 rojos preexistentes de Windows

$ grep -c "mode copy\|--source\|CLAUDE_CONFIG_DIR" docs/INTEROP.md docs/en/INTEROP.md docs/INSTALL.md docs/en/INSTALL.md
docs/INTEROP.md:7   docs/en/INTEROP.md:7   docs/INSTALL.md:6   docs/en/INSTALL.md:6
```

**Verificación re-ejecutada tras la corrección de la revisión I2** (gaps A-1, A-5, A-6, A-7, A-8):

```console
$ python scripts/lint_plugin.py              → lint_plugin: 9 agentes · 0 errores · 3 avisos
$ python evals/check.py                      → evals/check: 38 ficheros · 135 casos · 38 piezas · 0 errores
$ python scripts/export-interop.py --check   → export-interop --check: 48 ficheros al día
$ python -m pytest -q tests/test_copias_declaradas.py tests/test_ci_manual_copy.py \
      tests/test_export_interop.py -p no:cacheprovider
45 passed in 0.74s                           # las copias `--8<--` de doctor.py, intactas
```

**Criterios de aceptación**
- [x] Docs ES/EN espejadas en el mismo cambio; `--help` coherente con la doc
- [x] M-01 escrita con pasos y resultado esperado por runtime; sin marcar hasta la confirmación del usuario
- **Sin marcar — literal de HEAD (`09f62bd`), restaurado**: «CHANGELOG EN/ES con un bullet por tarea (escalera de `changelog-sync`)». No lo cierra esta tarea: los bullets se generan al cerrar la iniciativa (`estado: completado`), **desviación 25**. El campo `- **Changelog**:` —que es lo que `changelog-sync` copia tal cual— sí está escrito en las seis tareas, y el comando está en la `Verificación`. Va como viñeta y no como `- [ ]` por la **desviación 27**

**Subtareas**
- [x] INTEROP + INSTALL + README (ES/EN): §1 con la tabla «qué se copia / qué se registra» por runtime, `--mode`/`--source`/`--force-marketplace`/`CLAUDE_CONFIG_DIR`, «¿está registrado de verdad?» y quinta garantía; §4 con la fila «registro del plugin» y el hueco «copiar el bundle no instala el plugin»; Vía 0 ampliada y aviso en Vías 1/2; README ES/EN
- [x] M-01 con pasos y resultado esperado por runtime (incluida la contraprueba del bug original)
  - `changelog-sync` al cerrar la iniciativa — fuera de esta tarea
  - commit `T-06: …` — lo hace el orquestador tras la revisión

---

## M-01 — Verificación manual en runtimes reales (la hace el usuario)

> **Por qué existe esta checklist.** En esta máquina no hay `codex` ni `opencode`, y lo que un
> runtime hace al arrancar con su registro no se puede afirmar desde aquí sin mentir (regla de
> honestidad). Los pasos de abajo son la verificación que falta; **nadie los marca salvo el usuario**,
> tras ejecutarlos en su equipo. Si alguno falla, se abre una tarea nueva con la salida pegada.
>
> **Antes de empezar** (vale para los tres): trabaja sobre una copia de tu configuración o ten a mano
> `npx @daycry/custom-agents uninstall -p <runtime>`, que deshace exactamente lo que el instalador
> escribió. Con `--dry-run` puedes ver el plan completo sin tocar nada.

### Claude Code

- [ ] **Instalar como plugin**: `npx @daycry/custom-agents install -p claude-code --scope user`
  - **Esperado**: entre los avisos, o bien las dos líneas `$ claude plugin marketplace add …` /
    `$ claude plugin install custom-agents@daycry` (CLI en el PATH), o bien el aviso «sin `claude` en
    el PATH: registro escrito en …» (respaldo). Ninguna de las dos es un fallo.
- [ ] `claude plugin list` → aparece **`custom-agents@daycry`** como habilitado.
- [ ] `npx @daycry/custom-agents status` → `user: registrado: sí` con el fichero que lo prueba.
- [ ] **Sesión nueva** de Claude Code: `/custom-agents:doctor` existe (namespace) y su bloque
      «Plugin» dice `instalación: plugin`, `registro del plugin` ✅ y `hooks registrados` ✅.
- [ ] Al arrancar esa sesión, el hook `SessionStart` inyecta el índice de piezas (y, si había, la
      última entrada del journal). Si no aparece, `/custom-agents:doctor` dice por qué.
- [ ] **Contraprueba del bug original**: `npx @daycry/custom-agents install -p claude-code --mode copy`
      en un proyecto de usar y tirar → `status` dice `registrado: no` y `/doctor` marca ⚠️ en
      «hooks registrados» con el comando del arreglo. **Antes de esta iniciativa decía ✅.**

### Codex

- [ ] `npx @daycry/custom-agents install -p codex --scope user`
- [ ] `codex plugin marketplace list` → incluye **`daycry`**. Si el instalador avisó de que `codex`
      no estaba en el PATH (o era < 0.128.0), ejecuta el comando que imprimió y repite.
- [ ] `~/.codex/config.toml` → `[plugins."custom-agents@daycry"] enabled = true` y
      `[features] hooks = true`, **con el resto del fichero intacto** (compara con tu copia previa:
      `model`, `mcp_servers` y lo que tuvieras deben seguir ahí, en su sitio y sin duplicar tablas).
- [ ] `npx @daycry/custom-agents status` → Codex `user: registrado: sí`.
- [ ] **Sesión nueva** de Codex: las skills de `custom-agents` se activan con `@` (p. ej. `@tdd`) y
      `/prompts:dev-cycle` existe.
- [ ] Un agente traducido responde: pídele explícitamente «usa el agente `evaluator`» (Codex no
      auto-invoca agentes custom: eso es degradación conocida, no un fallo de la instalación).
- [ ] `npx @daycry/custom-agents uninstall -p codex --scope user` → `enabled = false` y **ninguna
      línea más** del `config.toml` cambiada (`[features] hooks` se queda: es preferencia tuya).

### OpenCode

- [ ] `npx @daycry/custom-agents install -p opencode`
- [ ] `opencode.json` → `plugin` contiene `./.opencode/plugins/custom-agents-hooks.js` **añadido** a
      lo que ya tuvieras (y tu `permission`, si lo tenías, sin tocar).
- [ ] `npx @daycry/custom-agents status` → OpenCode `project: registrado: sí`.
- [ ] **Arrancar OpenCode en ese proyecto**: no aparece ningún `Failed to load plugin` ni error del
      adaptador. Es el punto que no se puede comprobar aquí y el que más importa: el adaptador se
      declara **y** OpenCode lo autodescubre desde `plugins/`, y no debe cargarse dos veces.
- [ ] Las skills se listan y `/dev-cycle` existe; editar un fichero dispara el aviso de progreso
      (`tool.execute.after`) si hay un ledger en curso.
- [ ] `npx @daycry/custom-agents uninstall -p opencode` → los ficheros se van, `opencode.json` se
      queda como estaba **y el instalador avisa** de que la entrada de `plugin` sigue ahí apuntando a
      un fichero que ya no existe (quítala a mano si no vas a reinstalar).

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

## Revision de dos lentes - intento 3 (tramo I1, ULTIMO del bucle): 15/15 cerrados; nuevo 1 Critical, 2 Minor -- **3/3 corregidos en la 4.a pasada**

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
| I3-1 | **Critical** | La rama `implicita` de `ponerToml` elige el sitio por la RUTA de la asignacion, sin comprobar si esa asignacion vive en una cabecera **mas profunda** que el objetivo. Si la tabla destino existe solo de forma implicita porque hay una **sub-tabla** suya declarada (`[plugins."custom-agents@daycry".env]`), el `enabled` se escribe DENTRO de la sub-tabla. **Reproducido por el orquestador**: pasada 1 -> exit 0, «223 pasos aplicados» y `plugins = {'custom-agents@daycry': {'env': {'MI_VAR': '1', 'enabled': True}}}` — **Codex no habilita el plugin y el instalador afirma que si**; pasada 2 -> `tomllib: Cannot overwrite a value (line 9)`, se pierden `model` y `mcp_servers`. Es la 4.a forma de la familia de B-1 | T-03 | **Corregido** (4.a pasada, **post-condicion**, sin quinta rama): `ponerToml` re-analiza con `rutasToml()` el texto que va a escribir y exige que el camino exacto quede declarado **una sola vez** y con el valor pedido (y que no choque con una cabecera del mismo nombre); si no, **lanza y no devuelve texto** -> el fichero se queda como estaba y el mensaje nombra fichero, forma encontrada y cambio a mano. Ademas la rama `implicita` solo aplica si la asignacion vive en el **ambito exacto** (`tabla actual + prefijo de la clave == objetivo`), no en una cabecera mas profunda. **Evidencia** (`tomllib`, oraculo independiente; tabla esperada escrita a mano): las **5 formas x 2 pasadas + uninstall** parsean siempre y el valor cae donde Codex lo busca -- sin declarar / cabecera / clave con punto / tabla en linea / **sub-tabla implicita** -> `enabled=True` en las dos pasadas (2.a byte a byte identica) y `False` tras `uninstall`, con `model`, `mcp_servers` y `env.MI_VAR` intactos; `[features.web] search = true` + `hooks` -> `features.hooks=True` sin tocar `features.web`. Instalacion real por CLI sobre la forma reproducida por el orquestador: 2 pasadas + `uninstall` verdes. Tabla completa en la `Verificacion` de T-03; desviaciones 16 y 18 | `install.mjs` `ponerToml`/`rutasToml`/`formaToml` + rama `implicita` · `tests/installer.test.mjs` (8 tests `gap I3-1`) |
| I3-2 | Minor | `escribirAtomico` (tmp + `renameSync`) falla con `EPERM` en Windows si otro proceso tiene el destino **abierto**, donde el `writeFileSync` anterior funcionaba. Forma de fallo nueva introducida por el arreglo de B-7, en la ruta mas caliente | T-02 | **Corregido**: 3 intentos con espera breve (60/120 ms) ante `EPERM`/`EACCES`/`EBUSY` y, si persiste, **escritura directa** con aviso que dice que se pierde la atomicidad y nombra el fichero (buzon `drenarAvisosEscritura()`, que `ejecutar`/`deshacer` vuelcan en sus avisos). Cualquier otro error sigue tumbando el paso, y el temporal se limpia siempre. Test `gap I3-2: con el destino abierto por otro proceso se escribe igual, y se dice` con un handle abierto sobre el destino: en win32 escribe + 1 aviso con `EPERM`, en POSIX rename normal y **cero** avisos; en ningun caso queda un `.tmp-` suelto. Desviacion 17 | `install.mjs` `escribirAtomico` · `tests/installer.test.mjs` |
| I3-3 | Minor | El `rename` sustituye el inodo: el fichero queda con los permisos del temporal. Un `settings.json` en `600` acaba en `644` (medido en WSL). El mismo codigo si conserva el BOM «para no cambiarle la codificacion al usuario» | T-02 | **Corregido**: se lee `statSync(p).mode & 0o7777` ANTES (solo si el fichero existia) y se aplica `chmodSync` tras el `renameSync` -- tambien en la caida a escritura directa de I3-2; si el FS no soporta permisos, se ignora en silencio. Test `gap I3-3: el rename no puede cambiarle los permisos al fichero del usuario`: `chmod 600` -> modo antes == modo despues; el `0o600` exacto solo se exige en POSIX porque Windows lee `600` como `666` (medido) -- desviacion 20 | `install.mjs` `escribirAtomico` · `tests/installer.test.mjs` |

**Fuera de lente, anotado para el cierre**: `matarArbol` cae al nombre pelado `taskkill`/`wmic` si no los encuentra bajo
System32 (plantado de binario en una ruta que solo se recorre con el entorno roto); el `hint` de Codex afirma que
`enabled = true` queda puesto sin comprobarlo — lo cierra la post-condicion de I3-1.

**Decision**: el bucle acotado estaba en 3/3, pero I3-1 es el fallo exacto que esta iniciativa existe para corregir
(corromper la configuracion del usuario y declarar exito sin verificarlo), asi que el orquestador ordena una **4.a
pasada** con la post-condicion como arreglo estructural, en vez de declararlo y publicarlo.

**Resultado de la 4.a pasada: 3/3 cerrados** (1 Critical + 2 Minor). Marcador `installer-registro-real/I1-fix3`
(`start` antes de tocar nada, `close` antes de esta revision):
`{"fuente":"medido","tokens_reales":{"entrada":90,"salida":38295,"cache_creacion":104801,"cache_lectura":3428622,"respuestas":45},"eur":3.06,"horas_ia":0.3,"duracion":"18m","duracion_reloj":"26m","ratio_usado":479326.0,"ratio_origen":"CALIBRATION.md (mediana de 6)"}`.
**Reparto por bloques de trabajo observados** (no a prorrata de los 3 senalamientos): el analizador TOML (post-condicion
`rutasToml`/`formaToml`, la rama `implicita` acotada al ambito exacto) y sus 8 tests con el oraculo `tomllib` ->
**T-03: 0,22h**; la capa de escritura (I3-2 + I3-3 en `escribirAtomico`, el buzon de avisos y sus 2 tests) ->
**T-02: 0,08h**. T-01 no se toco en esta pasada: 0h. Verificacion global re-ejecutada tras el ultimo cambio:
`node --test tests/*.test.mjs` -> `ℹ tests 103 · ℹ pass 103 · ℹ fail 0`, **exit 0**; conjunto de nombres sin perdidas
(93 -> 103); `lint_plugin` 0 errores; `export-interop --check` 48 ficheros al dia; `--mode copy` y OpenCode identicos
al plan de HEAD (desviacion 19); prueba real con `claude` en `CLAUDE_CONFIG_DIR` temporal, verde.

## Revision de dos lentes - intento 1 (tramo I2: T-04..T-06): 8 Important, 7 Minor (lentes A+B)

Lentes A (conformidad) y B (persona «diagnostico y deteccion de estado») en paralelo, marcador
`installer-registro-real/revision-I2-intento1`:
`{"eur":10.58,"horas_ia":1.07,"duracion_reloj":"27m","tokens_reales":{"entrada":2311,"salida":117312,"cache_creacion":391643,"cache_lectura":12222330,"respuestas":104},"fuente":"medido"}`.

**Verificado y correcto** (no se repite en el intento 2): T-04 registra `plugin` en los dos scopes con la ruta buena,
une sin duplicar, conserva el array previo del usuario y avisa al desinstalar; el **falso positivo de `/doctor` esta
corregido** (modo copia -> hooks en aviso con el arreglo; modo plugin -> OK con la fila de registro); `--json` sin
perder ninguna clave (`ok` 12 -> 13); copias `--8<--` de `doctor.py` con el **mismo sha256** que HEAD (solo se
desplazan); degradacion sin traceback en 5 entornos rotos, identica a HEAD; `leerRegistro` acierta las 5 formas de TOML
y nunca lanza; docs ES/EN espejadas con los mismos hechos; M-01 con 19 casillas ejecutables y **sin marcar**; 108 tests
de Node sin perder nombres; `lint_plugin` 0 errores, `evals/check` 0, `export-interop --check` 48, `ledger-lint` 0.

**Desviacion 21 CONFIRMADA** por la Lente A contra el codigo y la doc de OpenCode: `resolvePluginSpec` resuelve los
specs de ruta contra la carpeta del config (`packages/opencode/src/config/plugin.ts`) y `isPathPluginSpec` trata `./…`
como ruta, no como paquete npm (`packages/opencode/src/plugin/shared.ts`), asi que la ruta que fijo **D4 estaba mal** y
`./.opencode/plugins/custom-agents-hooks.js` es la correcta. 21-bis (el autodescubrimiento SI esta documentado, y el
dedupe por URL evita la carga doble) y 21-ter tambien confirmadas. **D4 queda corregida** en la tabla de decisiones.

| # | Grado | Gap | Tarea | Correccion | Evidencia |
|---|---|---|---|---|---|
| B-1 | **Important** | `registro_plugin()` etiqueta `scope: "user"` toda entrada de `installed_plugins.json` e **ignora el `scope` y el `projectPath` que la propia entrada trae**: un alta hecha desde OTRO proyecto valida la raiz que se esta diagnosticando. Es el falso positivo que la iniciativa venia a matar, con otra cara | T-05 | **Corregido**: leer `scope`/`projectPath` de cada entrada y contar solo las que aplican a la raiz diagnosticada (las de `user` siempre; las de `project` solo si su `projectPath` es esta raiz); la fila dice el scope real — `_fuentes_instalados()` lee el `scope` y el `projectPath` de cada entrada y solo cuenta las que aplican a la raíz; la fila dice el scope real. Tests `test_gap_b1_un_alta_de_otro_proyecto_no_registra_esta_raiz` y `test_gap_b1_el_alta_de_ESTE_proyecto_si_cuenta_y_dice_su_scope_real` | `doctor.py:395,404,424` |
| B-2 | **Important** | Los descriptores `registro` de `claude-code` no cubren la via CLI: en scope project solo miran `<dir>/.claude/settings.json` (que escribe **solo** el respaldo sin CLI) y en user aceptan cualquier entrada sea cual sea su `scope`. Tras una instalacion correcta por CLI en scope project, `status` da **falso negativo y falso positivo a la vez** | T-05 | **Corregido**: los descriptores leen `installed_plugins.json` filtrando por `scope`/`projectPath`, con el mismo criterio que `doctor` — los descriptores de `claude-code` miran `installed_plugins.json` en los DOS scopes con `tipo: "json-instalados"` (filtra por `scope`/`projectPath`) y el respaldo sin CLI escribe `projectPath` en scope project. Test `gap B-2: instalado por la vía sin CLI en scope project…` | `providers.mjs:271-281` |
| A-3 | **Important** | `leerRegistro` devuelve en el **primer** descriptor que acierta, e `installed_plugins.json` va antes que `settings.json`: con `enabledPlugins = false`, `status` dice «registrado: si» mientras `/doctor` sobre el MISMO estado dice error. Dos herramientas de la misma iniciativa se contradicen, y M-01 usa `status` como prueba de que la instalacion fue bien | T-05 | **Corregido**: recorrer TODOS los descriptores y que un `false` explicito mande sobre cualquier alta — `leerRegistro` recorre TODOS los descriptores y un `false` manda (`valorRegistro`), igual que `estado_plugin()`. Tests `gap A-3: leerRegistro mira TODOS los descriptores…` (node) y `test_doctor_y_status_dan_el_MISMO_veredicto_sobre_el_MISMO_estado` (4 estados, python) | `install.mjs:1524-1547` |
| A-4 = B-4 | **Important** | `modo_instalacion()` declara `plugin` con que exista **un** hit no-`False` (las entradas de `installed_plugins.json` traen `habilitado: None`), asi que con el plugin **apagado** el informe dice `instalacion: plugin` y `hooks registrados` OK en la misma tabla en la que marca el registro en error | T-05 | **Corregido**: el modo lo decide el estado efectivo (un `false` en el scope que manda no es «plugin activo») y la fila de hooks no puede salir OK si el registro esta en error — `modo_instalacion()` decide por `estado_plugin()['habilitado']`; con el registro en error el modo es `inactivo` y la fila de hooks sale ⚠️ con arreglo. Test `test_gap_a4_con_el_registro_en_error_los_hooks_no_pueden_salir_en_verde` | `doctor.py:424` vs `:436` |
| B-3 | **Important** | `_bloque_plugin_registro()` mira `apagados` antes que `vivos` y **sin filtrar por clave**: cualquier `custom-agents@<otro>: false` pone la fila en error y `/doctor` en exit 1 aunque el plugin en uso este habilitado. De rebote, los tests nuevos **no aislan `CLAUDE_CONFIG_DIR`**: en una maquina con esa clave los rojos de `test_doctor.py` pasan de 2 a 14 | T-05 | **Corregido**: filtrar por la clave exacta del plugin diagnosticado y por scope; **todos** los tests de `test_doctor.py` que toquen el registro fijan `CLAUDE_CONFIG_DIR` a un temporal — solo la clave exacta (`clave_plugin()`) y fixture autouse `_registro_de_la_maquina_fuera` para TODA la suite. Comprobado simulando la máquina contaminada (`custom-agents@otro: false` en el `CLAUDE_CONFIG_DIR`): **14 rojos → 2** | `doctor.py:436-442` · `test_doctor.py` |
| B-5 | **Important** | `plugin` entra en el `merge` de `opencode.json` y `fusionar()` **sustituye un valor escalar del usuario** por nuestro array, sin aviso y sin apunte en el manifiesto: `"plugin": "mi-plugin.js"` desaparece y `uninstall` no lo devuelve. El agujero de `fusionar` es previo, pero este diff mete `plugin` en su radio | T-04 | **Corregido**: al fusionar un array sobre un escalar, conservarlo como primer elemento y avisar; si no es seguro, no tocar la clave y avisar — `fusionar()` conserva el escalar como primer elemento y avisa; un objeto no se toca y también avisa; el aviso se drena junto al fichero que lo provoca. Tests `gap B-5` (unitario + e2e: `"plugin": "mi-plugin.js"` sobrevive al install) | `providers.mjs:446` · `install.mjs:265` |
| A-1 | **Important** | El 3.er criterio de T-06 fue **reescrito** durante la implementacion y marcado `[x]`: HEAD pedia «CHANGELOG EN/ES con un bullet por tarea (escalera de `changelog-sync`)» y hoy dice «campo `- **Changelog**:` escrito en las seis tareas». La desviacion 25 explica bien por que no se tocan los CHANGELOG aqui; el camino conforme es dejar el criterio **sin marcar** apoyado en ella, no cambiar su texto | T-06 | **Corregido**: restaurar el literal de HEAD, dejarlo sin marcar y apuntar a la desviacion 25 — literal de HEAD (`09f62bd`) restaurado y sin marcar, apoyado en la desviación 25 (ver desviación 27 por la forma: viñeta, no `- [ ]`) | `tasks.md` CA3 de T-06 |
| A-2 | **Important** | D5 pedia que **`/doctor`** comprobara el registro tambien en Codex (`config.toml`) y OpenCode (`opencode.json`); solo lo hace `status`. `doctor.py` no menciona ninguno de los dos, y `/doctor` se exporta a esos runtimes | T-05 | **Corregido**: implementarlo en `doctor.py` (dos filas mas, leyendo lo mismo que `leerRegistro`) o **declararlo como desviacion numerada** con el motivo y anotarlo en D5. Preferible implementarlo: son dos lecturas de fichero — implementado: filas «registro en Codex» (`config.toml` con `tomllib`, las cinco formas) y «registro en OpenCode» (`plugin` de `opencode.json`), con el mismo criterio que `status`. Test `test_gap_a2_codex_y_opencode_tienen_su_fila_de_registro` | `doctor.py` (0 apariciones de `codex`/`opencode`) |
| B-6 | Minor | La forma del bloque `plugin` en `--json` no es estable: `modo`/`registro` solo existen en la rama larga; un consumidor que lea `bloque["modo"]` revienta con `KeyError` cuando la raiz no se localiza | T-05 | **Corregido**: emitir siempre las claves, con valor nulo o `desconocido` — `bloque_plugin` emite `modo` y `registro` también en la rama corta. Test `test_gap_b6_el_json_trae_modo_y_registro_tambien_sin_raiz` | `doctor.py:493` vs `:501` |
| B-7 | Minor | En `enabledPlugins`, cualquier valor falsy que no sea `False` (`0`, `null`, `""`, `"false"`) cuenta como alta | T-05 | **Corregido**: solo `True` cuenta como habilitado; cualquier otro valor, aviso de valor invalido — solo `True` habilita; cualquier otro valor es fila ⚠️ «registro con valor inválido» (y `invalidoEn` en `status`). Tests `test_gap_b7_en_enabled_plugins_solo_true_habilita` y `gap A-3` (node) | `doctor.py:405` |
| A-5 | Minor | El comando de la `Verificacion` de T-06 no es ejecutable: `changelog-sync.py` no acepta ruta posicional | T-06 | **Corregido**: `--check --only <slug>` — `--check --only 2026-09-11-installer-registro-real` | `tasks.md` Verificacion de T-06 |
| A-6 | Minor | «los 220 ficheros» en INTEROP (ES y EN): el bundle de Claude Code son 222 pasos; 220 es el de OpenCode | T-06 | **Corregido**: cifra real o sin cifra — sin cifra en los dos espejos («está el bundle entero» / «the whole bundle is there») | `INTEROP.md:178` + espejo |
| A-7 | Minor | INSTALL (ES y EN) sigue describiendo **un** manifiesto (`.custom-agents-install.json`) cuando en modo plugin es `.custom-agents-install.plugin.json` | T-06 | **Corregido**: nombrar los dos — INSTALL ES/EN nombran los dos: `.custom-agents-install.plugin.json` (modo plugin) y `.custom-agents-install.json` (`--mode copy`) | `INSTALL.md:46` + espejo |
| A-8 | Minor | INTEROP afirma como hecho que registrar el adaptador «no lo carga dos veces»; lo respalda el codigo upstream, no una ejecucion, y M-01 lo tiene como pendiente | T-06 | **Corregido**: matizar («segun el codigo de OpenCode…; pendiente de confirmar en M-01») — INTEROP ES/EN: «según su código (`deduplicatePluginOrigins` desempata por URL de fichero)… pendiente de confirmar en un OpenCode real (M-01)» | `INTEROP.md:161` + espejo |
| A-9 | Minor | Imprecision en la evidencia de la desviacion 21: un fichero inexistente no hace fallar a `resolvePathPluginTarget`; el error llega al importar | T-04 | **Corregido**: corregir la frase — la frase dice ahora que `resolvePathPluginTarget` devuelve la ruta sin comprobarla y que el fallo llega al importarla | `tasks.md` desviacion 21 |

**Higiene de revision** (no es gap del diff, pero tumba la puerta de CI): mientras una lente tuvo su copia
`agent-kits/shared/_doctor_head.py` en el arbol, `lint_plugin.py` salio con **4 errores** por centinelas `--8<--` sin
fila en `copias.json`. Comprobado por el orquestador al cerrar la revision: la copia ya no esta y el linter vuelve a
`0 errores`. Leccion: las copias de HEAD van al scratchpad; si tienen que vivir en el arbol, se borran antes de cerrar.

**Corrección — 15/15 cerrados** (8 Important + 7 Minor), marcador `installer-registro-real/I2-fix1`:
`{"fuente":"medido","tokens_reales":{"entrada":3454,"salida":111202,"cache_creacion":345174,"cache_lectura":14089856,"respuestas":101},"eur":11.04,"horas_ia":0.96,"duracion":"58m","duracion_reloj":"54m","ratio_usado":479326.0,"ratio_origen":"CALIBRATION.md (mediana de 6)"}`.
**Reparto por bloques de trabajo observados** (no a prorrata de los 15 señalamientos): el estado efectivo del
registro —`estado_plugin()` con sus reglas de scope/clave/precedencia, los descriptores `json-instalados`,
`leerRegistro` recorriendo todo, las filas de Codex y OpenCode, el aislamiento de la suite y 13 tests nuevos de
`test_doctor.py` + 4 de node— → **T-05: 0,62h**; la fusión que ya no borra la clave del usuario (`fusionar` + aviso
+ 2 tests) y la frase de la desviación 21 → **T-04: 0,16h**; docs ES/EN, `commands/doctor.md`, interop regenerada y
el criterio restaurado → **T-06: 0,18h**.

**Los cinco Important de `/doctor` y `status` se cerraron como UN concepto, no como cinco parches.** La pieza es
`estado_plugin(plugin_root, project, cfg)` en `agent-kits/shared/doctor.py`: recorre todas las fuentes, se queda
con las que aplican a la raíz (clave exacta; `user` siempre, `project` solo con su `projectPath`), y resuelve con
precedencia de scope y un `false` explícito mandando sobre cualquier alta. `modo_instalacion()` y las filas del
informe salen de ahí, y `leerRegistro()` de `install/install.mjs` repite las mismas reglas — con un test que monta
un estado y comprueba que `/doctor` y `status` **coinciden** en los cuatro casos que antes se contradecían
(`test_doctor_y_status_dan_el_MISMO_veredicto_sobre_el_MISMO_estado`). El modo nuevo `inactivo` es lo que impide
que la fila de hooks salga en ✅ con el registro en error.

**Puertas al cerrar**: `node --test tests/*.test.mjs` → 114/114, exit 0 (108 → 114, **ningún nombre perdido**);
suite de CI completa → **40 rojos, el mismo CONJUNTO que antes de tocar nada** (1452 → 1465 verdes);
`lint_plugin` 0 errores · `evals/check` 0 · `export-interop --check` 48 · `ledger-lint` 0. `scope-check` sigue
saliendo con 1 por los seis ficheros de la **desviación 26**, ajenos a estas tareas. Desviaciones nuevas: **27**
(la forma del criterio restaurado), **28** (`CODEX_HOME` en las dos piezas) y **29** (regla de precedencia entre
scopes). Ningún fichero de HEAD quedó copiado en el árbol (la lección de la «higiene de revisión»): las copias
vivieron en el scratchpad.

## Revision de dos lentes - intento 2 (tramo I2): 15/15 cerrados; nuevos 4 Important, 7 Minor

Una lente fresca (B, «diagnostico y deteccion de estado») sobre el **delta del intento 2**; la conformidad la cerro la
Lente A en el intento 1 y el delta es logica de deteccion. Marcador `installer-registro-real/revision-I2-intento2`:
`{"eur":9.06,"horas_ia":0.9,"duracion_reloj":"26m","tokens_reales":{"entrada":1510,"salida":75052,"cache_creacion":275805,"cache_lectura":12487147,"respuestas":84},"fuente":"medido"}`.
**Sin segunda lente en este intento**, dicho.

**Los 15 gaps del intento 1: cerrados los 15.** Verificado ademas, con mutantes y estados hostiles: la precedencia
elegida es la correcta en los 3 casos pedidos; `clave_plugin()` acierta el marketplace de un fork; `_misma_ruta` y su
gemelo `mismaRuta` coinciden en 11 comparaciones (mayusculas, barra final, separadores, ausente); las filas de Codex
aciertan las 5 formas y **ninguna lanza**; el import de `tomllib` esta guardado y degrada con aviso en Python < 3.11
(sin traceback, exit 0); el **test de coherencia mata los 4 mutantes** (ignorar el `false`, dejar que el alta gane,
`leerRegistro` siempre falso, quitar el filtro de `projectPath`); la fixture `autouse` cubre **toda** la suite (maquina
contaminada: siguen 2 rojos, no 14); planes de los 3 proveedores identicos a `d4294ae` salvo `projectPath` y el
`plugin` de OpenCode, `--mode copy` byte a byte; 114 tests de Node; copias `--8<--` con el mismo sha256 que HEAD.

| # | Grado | Gap | Tarea | Correccion | Evidencia |
|---|---|---|---|---|---|
| I2-1 | **Important** | `estado_plugin()` lee solo `<cfg>/settings.json` y `<proyecto>/.claude/settings.json`. **`.claude/settings.local.json` es un scope de plugin documentado (`local`), esta POR ENCIMA de `project` en la pila de precedencia y es donde escribe `claude plugin disable --scope local`**; `managed-settings.json` esta por encima de todo. Ninguno se lee, ni en `/doctor` ni en `status`: con el plugin apagado en `local`, el informe dice `modo: plugin`, `ok registro` y **`ok hooks registrados`**. Es el falso positivo de la iniciativa, reabierto en el fichero de mayor precedencia no gestionada | T-05 | pendiente: `estado_plugin` y `leerRegistro` leen tambien `<proyecto>/.claude/settings.local.json` (scope `local`, por encima de `project`) y, si existe, el `managed-settings.json` de la plataforma (por encima de todo, informativo); la fila nombra el fichero que manda | `doctor.py:490-492` · `providers.mjs:283-294` |
| I2-2 | **Important** | `_misma_ruta()` llama a `os.path.abspath()` sin comprobar el tipo: un `projectPath` que no sea cadena tumba `/doctor` **entero** con traceback y stdout vacio (exit 1). El gemelo de node no lanza, asi que los dos diagnosticos divergen justo en un fichero mal formado, que es cuando se usa `/doctor` | T-05 | pendiente: validar el tipo y descartar la entrada con aviso, como hace node | `doctor.py:417,442` |
| I2-3 | **Important** | La fila «registro en OpenCode» casa por **basename**: da OK a cualquier `custom-agents-hooks.js` de cualquier sitio, incluido uno que no resuelve al adaptador instalado, y acepta `plugin` como escalar. `status` (igualdad exacta) dice lo contrario sobre el MISMO estado. La invariante «las dos herramientas no se contradicen» solo esta impuesta para Claude Code y el test de coherencia no cubre OpenCode | T-05 | pendiente: comparar la **ruta resuelta** contra la que escribe el instalador (misma regla que `status`), y extender el test de coherencia a OpenCode y Codex | `doctor.py:684` vs `providers.mjs:471-475` |
| I2-4 | **Important** | El paso `exec` se lanza **sin `cwd`**, asi que `claude plugin install --scope project` graba `projectPath` = el cwd del proceso, no `--dir`. Con el filtro nuevo queda a la vista: el instalador dice «2 pasos aplicados» y acto seguido `status` dice «registrado: no» y `/doctor` «instalacion: inactivo». La causa es de T-02 (tramo I1, ya committeado); el filtro de I2 la **destapa**, no la crea | T-02/T-05 | pendiente: pasar `cwd: dir` en los pasos `exec` del proveedor `claude-code` (y comprobar el resto); test que instale por CLI en `--dir <X>` y afirme que `projectPath` es `<X>` y que `status` dice si | `providers.mjs:193-200,292` · `install.mjs:1152` |
| I2-5 | Minor | `bloque_plugin` pasa a la fila de Codex la clave deducida de la raiz de **Claude Code**, mientras el instalador escribe siempre `custom-agents@daycry`: con un fork, `/doctor` busca la clave equivocada en `config.toml` | T-05 | pendiente: para Codex, usar la clave que escribe el instalador (o mirar las dos y decirlo) | `doctor.py:742` vs `providers.mjs:37-39` |
| I2-6 | Minor | Un `scope` que no sea `user`/`project` cae a **`user`**, el lado permisivo: una entrada `scope: local` de otro proyecto vale para todos. Reabre el falso positivo por el valor por defecto | T-05 | pendiente: `local` se trata como scope de proyecto (exige `projectPath`); un scope desconocido no cuenta y se avisa | `doctor.py:440` · `install.mjs:1566` |
| I2-7 | Minor | Ni `_misma_ruta` ni `mismaRuta` resuelven enlaces: la misma carpeta por junction o `subst` no casa con el `projectPath` grabado (falso negativo, coherente en las dos) | T-05 | pendiente: `os.path.realpath` / `fs.realpathSync` en los dos lados, con caida al valor original si falla | `doctor.py:414-417` · `install.mjs:1538-1545` |
| I2-8 | Minor | Un `opencode.json` ilegible se traga en silencio y la fila propone «reinstala», que no arregla nada; el gemelo de Codex si distingue el fichero ilegible | T-05 | pendiente: distinguir ilegible de ausente, como en Codex | `doctor.py:680` vs `:615-617` |
| I2-9 | Minor | El test de coherencia hace `skip` del test **completo** sin `node`, con lo que se pierde tambien la mitad de python, que no necesita node | T-05 | pendiente: partir en dos, o afirmar la parte de python siempre | `test_doctor.py:857-861` |
| I2-10 | Minor | Con `CLAUDE_CONFIG_DIR` apuntando a `<proyecto>/.claude`, el mismo `settings.json` se lee dos veces y la fila lo lista con dos scopes | T-05 | pendiente: deduplicar por ruta real | `doctor.py:491-492` |
| I2-11 | Minor | La rama informativa de Codex afirma «Codex esta en esta maquina (`<CODEX_HOME>`)» mirando un directorio que puede no existir; lo detectado es `<proyecto>/.codex` | T-05 | pendiente: nombrar lo que se detecto | `doctor.py:663-666` |

**Correccion de la desviacion 29** (la hace el orquestador): decia que Claude Code «no documenta la precedencia entre
scopes». **Si la documenta**: `settings-reference#enabledplugins` da `Scope: Any file` y `settings#settings-precedence`
fija «Managed > command line > Project local > Shared project > User». El orden implementado coincide con el
documentado; lo que falta son **dos niveles** (`local` y `managed`), que es el gap I2-1.

**Higiene**: durante la prueba con la CLI real, `claude plugin install --scope project` (el `exec` sin `cwd` del gap
I2-4) creo un `.claude/settings.json` **en este repo**; la lente lo borro y el orquestador lo confirmo al cerrar
(`git status` en los 15 ficheros del tramo, `lint_plugin` 0 errores). Es una razon mas para pasar `cwd`.
