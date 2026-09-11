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
| Fase 1 — el instalador registra de verdad (Claude Code, Codex, OpenCode) | 0 | 4 | 0% | — / 7,0h | — / 0,90h | — / 0,25h | — / 420k |
| Fase 2 — diagnóstico veraz y documentación | 0 | 2 | 0% | — / 3,0h | — / 0,40h | — / 0,10h | — / 180k |
| **TOTAL** | **0** | **6** | **0%** | **— / 10,0h** | **— / 1,30h** | **— / 0,35h** | **— / 600k** |

---

## Fase 1 — el instalador registra de verdad (Claude Code, Codex, OpenCode)

**Estado**: borrador · **Estimado**: 7,0h · **Real**: — · **Coste est.**: ≈350 € · **Tokens est.**: 420k · **Tramo**: I1 (T-01…T-03) · I2 (T-04)

### T-01 — Banner y multiselect con checkboxes, cero dependencias

- **Descripción**: `install/install.mjs`: (a) `banner()` estático — wordmark ASCII `custom-agents`, versión y lema en una caja, colores ANSI a mano; no se imprime con `--quiet`, `NO_COLOR`, `CI` o sin TTY, y `--help`/`--version`/`status`/`list` no lo muestran; (b) `preguntar()` pasa a un **multiselect raw** (`readline.emitKeypressEvents` + `setRawMode`): lista de proveedores con `[x]`/`[ ]`, etiqueta `detectado`/`no detectado` y el `blurb`; teclas ↑/↓/j/k, espacio, `a` (todos), `i` (invertir), Enter, Esc/`q`/Ctrl-C (cancela con exit 0 y mensaje); preselección = detectados ∪ {`claude-code`}; sin `setRawMode` (stdin no TTY o terminal sin soporte) cae al menú numérico actual. El reductor de teclas es una **función pura** exportada (`reducirTecla(estado, tecla) → estado`) para poder probarlo sin terminal. `-y`/`--yes` y `-p` siguen sin preguntar nada.
- **Changelog**: El instalador `npx` muestra un título al arrancar y permite elegir los runtimes con checkboxes (espacio marca, Enter confirma), con los detectados preseleccionados.
- **Estado**: borrador
- **Tipo**: feature
- **Tiempo humano**: est. 1,5h · real —
- **Tiempo IA (ejec.)**: est. 0,20h · real —
- **Supervisión**: est. 0,05h · real —
- **Previsión IA**: 70k in / 10k out tok
- **Dependencias**: —
- **Archivos**: `install/install.mjs`, `tests/installer.test.mjs`
- **Verificación**:
  - `node install/install.mjs --help | head -3` → sin banner (solo la ayuda); `CI=1 node install/install.mjs install --all --dry-run | head -2` → sin banner
  - `node --test tests/installer.test.mjs` → verde, con los tests nuevos del reductor: `↓`+espacio marca el segundo; `a` marca todos; `i` invierte; preselección con `claude-code` aunque no esté detectado; Enter devuelve solo los marcados
  - `echo "" | node install/install.mjs install --dry-run` (stdin no TTY, sin `-y`) → usa los detectados, no cuelga, exit 0 o 2 con el mensaje de «ningún proveedor»
  - Comprobación manual del orquestador en terminal real: banner + checkboxes visibles, espacio y Enter funcionan (salida pegada)

**Criterios de aceptación**
- [ ] Banner solo en TTY sin `NO_COLOR`/`CI`/`--quiet`, y nunca en `--help`, `--version`, `status`, `list`
- [ ] Multiselect con checkboxes, teclas documentadas en pantalla, preselección detectados ∪ claude-code, cancelación limpia (cursor visible, raw mode restaurado también en error)
- [ ] Reductor puro con tests; sin `setRawMode` cae al menú numérico; `-y`/`-p`/stdin no TTY no preguntan
- [ ] Cero dependencias nuevas en `package.json`

**Subtareas**
- [ ] `banner()` + condiciones de apagado
- [ ] `reducirTecla()` + `multiselect()` + fallback numérico
- [ ] Tests del reductor y de las condiciones de banner
  - commit `T-01: …` — lo hace el orquestador tras la revisión

### T-02 — Claude Code: modo plugin por defecto (CLI oficial → registro directo), `--mode copy` explícito

- **Descripción**: `install/providers.mjs` + `install/install.mjs`: nuevo tipo de paso `{ type: "exec" }` (comando con args, `cwd`, `opcional`) y `{ type: "json-set" }` (poner claves en un JSON del usuario; distinto de `merge`: sobrescribe SOLO las claves que pone, anota en el manifiesto qué claves puso para poder quitarlas). Proveedor `claude-code`, `modo: "plugin"` por defecto: (1) si `claude` está en PATH → `exec claude plugin marketplace add <source> --scope <scope>` (si ya existe, seguir) + `exec claude plugin install custom-agents@daycry --scope <scope>`; (2) si no → respaldo directo: `copy` del paquete (`PAYLOAD_CLAUDE` + `.claude-plugin/`) a `<CLAUDE_CONFIG_DIR>/plugins/marketplaces/daycry/` y a `<CLAUDE_CONFIG_DIR>/plugins/cache/daycry/custom-agents/<version>/`, `json-set` en `plugins/known_marketplaces.json` (`daycry: {source:{source:"github",repo:"daycry/custom-agents"}, installLocation, lastUpdated, autoUpdate:true}`), en `plugins/installed_plugins.json` (`version: 2`, `plugins["custom-agents@daycry"] = [{scope, installPath, version, installedAt, lastUpdated}]`) y en `settings.json` del scope (`enabledPlugins["custom-agents@daycry"] = true`; scope project además `extraKnownMarketplaces.daycry`). `CLAUDE_CONFIG_DIR` respetado (default `~/.claude`). `--mode copy` = plan actual con aviso «bundle copiado: hooks y statusline NO se registran; namespace no disponible». `--source <ruta|owner/repo>` cambia la fuente del marketplace (desarrollo). `restart`/`hint` actualizados (ya no «vía recomendada: /plugin…», porque ESTO es la vía). `uninstall`: `claude plugin uninstall custom-agents@daycry --scope` si hay CLI; si no, quitar las claves que el manifiesto anotó y borrar las copias; nunca borrar `settings.json`.
- **Changelog**: En Claude Code el instalador registra `custom-agents` como plugin de verdad (hooks, namespace y actualizaciones), usando la CLI oficial si está y escribiendo el registro del plugin si no; copiar el bundle pasa a ser `--mode copy`.
- **Estado**: borrador
- **Tipo**: feature
- **Tiempo humano**: est. 3,0h · real —
- **Tiempo IA (ejec.)**: est. 0,40h · real —
- **Supervisión**: est. 0,10h · real —
- **Previsión IA**: 120k in / 18k out tok
- **Dependencias**: T-01 (los pasos nuevos se imprimen en `--dry-run` con el mismo formato)
- **Archivos**: `install/providers.mjs`, `install/install.mjs`, `tests/installer.test.mjs`
- **Verificación**:
  - `CLAUDE_CONFIG_DIR=<tmp>/claude HOME=<tmp>/home node install/install.mjs install -p claude-code --scope user -y --dry-run` → el plan imprime `exec claude plugin marketplace add …` + `exec claude plugin install …` si `claude` en PATH; con `PATH` sin `claude` imprime las 2 copias + 3 `json-set`
  - Instalación real de respaldo en HOME temporal (PATH sin `claude`): `known_marketplaces.json`, `installed_plugins.json` y `settings.json` con las claves esperadas (JSON pegado); reinstalar → idénticos (idempotente); `uninstall` → claves quitadas, copias borradas, `settings.json` conserva lo demás
  - `node install/install.mjs install -p claude-code --mode copy -y --dir <tmp>` → plan actual + aviso de lo que se pierde
  - `node --test tests/installer.test.mjs` → verde (tests nuevos: plan plugin con/sin CLI simulado por `PATH`, `json-set` no pisa otras claves, manifiesto anota claves, uninstall las quita, `--mode copy` = plan anterior)
  - **Prueba real del orquestador en esta máquina** (tiene `claude`): `install -p claude-code --scope user --source <ruta del repo> -y` en un `CLAUDE_CONFIG_DIR` temporal → `claude plugin list` (con ese `CLAUDE_CONFIG_DIR`) lista `custom-agents@daycry`; salida pegada. Sin tocar el `~/.claude` real
- **Notas**: el formato de `known_marketplaces.json`/`installed_plugins.json` es interno de Claude Code (claude-mem lo escribe igual); se documenta en `INTEROP.md` como respaldo y el modo CLI es el preferido. Nada de este cambio toca las piezas (`agents/`, `commands/`, `skills/`, `hooks/`): `export-interop.py --check` no varía.

**Criterios de aceptación**
- [ ] Por defecto, tras instalar en Claude Code el plugin figura en `installed_plugins.json` + `enabledPlugins` (vía CLI o respaldo) y el bundle NO se copia a `.claude/`
- [ ] `--mode copy` reproduce el comportamiento anterior byte a byte en el plan, con aviso
- [ ] Idempotente y desinstalable por manifiesto (claves anotadas); `settings.json` del usuario nunca se borra ni se pisa fuera de las claves puestas
- [ ] `CLAUDE_CONFIG_DIR` respetado; `--source` documentado en `--help`

**Subtareas**
- [ ] Pasos `exec` y `json-set` en `ejecutar()` (dry-run, manifiesto, errores)
- [ ] Proveedor `claude-code` con `modo` y detección de `claude` en PATH
- [ ] `uninstall` para modo plugin
- [ ] Tests
  - commit `T-02: …` — lo hace el orquestador tras la revisión

### T-03 — Codex: `marketplace add` + `enabled = true` (y `hooks`) en `config.toml`

- **Descripción**: proveedor `codex`: tras las copias actuales, (1) `exec codex plugin marketplace add <mktRoot>` si `codex` en PATH (versión mínima `0.128.0` leída de `codex --version`; si «already added from a different source» → `remove` + `add`; sin `codex` → aviso con el comando pendiente); (2) paso nuevo `{ type: "toml-set", to, tabla, clave, valor }`: editor mínimo propio que pone un booleano en `[plugins."custom-agents@daycry"]` (`enabled = true`) y en `[features]` (`hooks = true`) del `config.toml` del scope (`~/.codex/config.toml` o `<dir>/.codex/config.toml`), creando la tabla al final si no existe y **sin reescribir nada más** (conserva comentarios y orden); el manifiesto anota tabla+clave para `uninstall` (pone `enabled = false`, no borra la tabla). Nombre del marketplace = `name` de `.agents/plugins/marketplace.json` (`daycry`) → id `custom-agents@daycry`.
- **Changelog**: En Codex el instalador registra el marketplace con la CLI y habilita el plugin en `config.toml`, que es lo que faltaba para que skills y hooks aparezcan.
- **Estado**: borrador
- **Tipo**: feature
- **Tiempo humano**: est. 1,5h · real —
- **Tiempo IA (ejec.)**: est. 0,20h · real —
- **Supervisión**: est. 0,05h · real —
- **Previsión IA**: 70k in / 10k out tok
- **Dependencias**: T-02 (paso `exec`)
- **Archivos**: `install/providers.mjs`, `install/install.mjs`, `tests/installer.test.mjs`
- **Verificación**:
  - `node --test tests/installer.test.mjs` → verde; tests del `toml-set`: fichero vacío → crea la tabla; tabla existente con otras claves y comentarios → solo cambia/añade `enabled`, el resto byte a byte igual; `enabled = false` → `true`; idempotente
  - `HOME=<tmp> node install/install.mjs install -p codex --scope user -y` (PATH sin `codex`) → `config.toml` con las dos tablas (pegado) + aviso «ejecuta `codex plugin marketplace add …`»; `--dry-run` imprime el `exec` cuando `codex` está en PATH (simulado con un `codex` falso en un dir temporal que responde a `--version` y a `plugin marketplace add`)
  - **No verificable aquí**: que Codex cargue el plugin tras esto → checklist **M-01** (usuario)
- **Notas**: `codex plugin marketplace add` y `[plugins."<id>"] enabled` están en la doc oficial de Codex («Package plugin»); el flujo lo usa `claude-mem` (`CodexCliInstaller.ts`) con la misma versión mínima.

**Criterios de aceptación**
- [ ] `config.toml` del scope con `[plugins."custom-agents@daycry"] enabled = true` y `[features] hooks = true`, sin alterar el resto del fichero
- [ ] Con `codex` en PATH se ejecuta `marketplace add` (con recuperación si ya existía); sin él, aviso con el comando exacto
- [ ] `uninstall` pone `enabled = false` y no borra nada del `config.toml`

**Subtareas**
- [ ] Paso `toml-set` + editor mínimo con tests
- [ ] `exec codex …` con versión mínima y recuperación
- [ ] `uninstall`
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
