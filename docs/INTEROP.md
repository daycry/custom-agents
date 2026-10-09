# Interoperabilidad — Claude Code, Codex y OpenCode

[English](en/INTEROP.md) · **Español**

Este plugin nació para Claude Code y hoy se instala también en **Codex** (OpenAI) y **OpenCode**
(SST). Este documento explica **cómo** (instalación), **qué se traduce** (y con qué formato) y
—lo más importante— **qué NO funciona igual** en cada runtime.

> **Una sola fuente de verdad.** `agents/`, `commands/`, `skills/` y `hooks/` siguen siendo las
> piezas reales. Lo que viaja a Codex y OpenCode son **traducciones generadas** por
> `scripts/export-interop.py`; nadie las edita a mano y `--check` falla si se quedan atrás.

---

## 1. Instalación

### La vía corta: el instalador

```bash
npx @daycry/custom-agents                     # menú: elige proveedores (marca los que detecta)
npx @daycry/custom-agents install -p codex    # solo Codex, en este proyecto
npx @daycry/custom-agents install --all --scope user
npx @daycry/custom-agents install -p opencode --dry-run   # imprime el plan, no escribe nada
npx @daycry/custom-agents status               # qué hay instalado y dónde
npx @daycry/custom-agents uninstall -p codex   # borra lo que instaló, y solo eso
```

| Opción | Para qué |
|---|---|
| `-p, --provider <ids>` | `claude-code`, `codex`, `opencode` (coma) o `all` |
| `--scope project\|user` | proyecto (por defecto) o instalación global del runtime |
| `--dir <ruta>` | proyecto destino (por defecto, el directorio actual) |
| `--mode plugin\|copy` | **solo Claude Code**: instalarlo como plugin (por defecto) o copiar el bundle a `.claude/` |
| `--source <ruta\|owner/repo>` | de dónde sale el marketplace de Claude Code (por defecto `daycry/custom-agents`); una ruta local sirve para desarrollar |
| `--force-marketplace` | **solo Codex**: si el marketplace `daycry` ya existe apuntando a otra fuente, rehacerlo (por defecto se avisa y no se toca) |
| `--dry-run` | plan completo sin escribir nada |
| `-y, --yes` | sin preguntas (CI) |

> `CLAUDE_CONFIG_DIR` se respeta en todo: si lo tienes apuntando a otro sitio, el instalador
> escribe ahí y no en `~/.claude`.

### Instalar no es copiar: qué hace el instalador en cada runtime

Cada runtime tiene un fichero que decide si el plugin **carga**. Copiar los ficheros no lo toca, y
sin él no hay hooks, ni statusline, ni namespace de comandos. El instalador escribe esos ficheros:

| Runtime | Qué se copia | Qué se **registra** (y dónde) |
|---|---|---|
| **Claude Code** | con `--mode plugin` no copia nada en tu proyecto: el paquete va al caché de plugins | `claude plugin marketplace add` + `claude plugin install` si tienes la CLI en el PATH; si no, el mismo registro a mano: `plugins/known_marketplaces.json`, `plugins/installed_plugins.json` y `enabledPlugins` de `settings.json` (scope user) o `.claude/settings.json` con `extraKnownMarketplaces` (scope project) |
| **Codex** | bundle bajo `.codex/plugins/custom-agents/` del scope, agentes `.toml` y prompts | caché mediante `codex plugin add` (CLI ≥ 0.161.0); registro `marketplaces.daycry`, `plugins."custom-agents@daycry".enabled` y `features.hooks` en el config del scope después del éxito |
| **OpenCode** | agentes, comandos, skills, kits y el adaptador de hooks en `plugins/` | `plugins: ["./.opencode/plugins/custom-agents"]` en `opencode.json` (ruta absoluta en scope user), añadido a lo que ya tuvieras |

**La vía preferida siempre es la CLI oficial del runtime.** El respaldo —escribir el registro
nosotros— existe porque `claude` no está en el PATH de todo el mundo (instalación de escritorio en
Windows, shims de npm que Node no sabe lanzar) y sin él el instalador no podía hacer nada útil. Es
formato interno de cada herramienta, así que el instalador **dice** cuándo lo usa y por qué.

**`--mode copy`** es la instalación de siempre: el bundle copiado a `.claude/`. Sirve para leer las
piezas (agentes, skills, kits) y para trastear, pero Claude Code **no lee `hooks/hooks.json` fuera
de un plugin instalado**: sin hooks, sin statusline y sin `/custom-agents:`. El instalador lo avisa
al terminar y `/doctor` lo marca ⚠️ (§4).

### ¿Está registrado de verdad?

```bash
npx @daycry/custom-agents status   # por runtime y scope: manifiesto + «registrado: sí/no»
```

`status` no se fía del manifiesto: lee los mismos ficheros que lee el runtime (`installed_plugins.json`
/ `enabledPlugins`, `config.toml` de Codex, `plugins` de `opencode.json`). Por eso puede decir
«registrado: sí» sin manifiesto (lo instalaste con la CLI del runtime) y «no» con él (`--mode copy`).
De Claude Code lee `enabledPlugins` en los **cuatro** ficheros de ajustes de la pila documentada
(`settings-reference#enabledplugins`: «Scope: Any file») y resuelve en el orden de
`settings#settings-precedence` («Managed > command line > Project local > Shared project > User»):
`managed-settings.json` > `.claude/settings.local.json` > `.claude/settings.json` > el `settings.json`
de tu `CLAUDE_CONFIG_DIR`. Mirar solo los dos últimos daba «registrado: sí» con el plugin apagado con
`claude plugin disable --scope local`.
Dentro de Claude Code, lo mismo con más detalle: `/doctor`.

Codex distingue la declaración por scope del estado que devuelve la CLI en
el proyecto actual. `status` y `/doctor` comparten un lector que consulta
`codex plugin list --marketplace daycry --available --json`, con tiempo acotado
y sin volcar otras entradas, rutas de origen ni errores privados. Si falta la
CLI o su respuesta no se puede comprobar, el estado nativo es desconocido.
Una instalación habilitada no acredita confianza del hash de hooks ni su
ejecución; eso requiere revisar una sesión del runtime.

En scope project, `plugin add` trabaja con un `CODEX_HOME` temporal: copia
regular de la configuración de usuario y un enlace limitado al namespace de
caché `daycry`. Su setter cambia esa copia, y la activación se escribe en el
proyecto al completar la instalación. Dos proyectos conservan sus propios
orígenes y no cambian el marketplace ni la preferencia global del usuario.
La caché de versión continúa compartida y una actualización puede cambiar
el contenido usado por otros proyectos. Los conflictos de origen requieren
`--force-marketplace`; una configuración con rutas relativas que no puede
preservarse en la copia se rechaza, sin reintentar contra el home real.
No se usa `plugin remove` como rollback ni se fuerza `chmod` en el caché.

Al desinstalar, se restaura cada clave de origen solo si todavía conserva el
valor escrito por el instalador; las ediciones posteriores y otros campos
se mantienen. La activación del plugin queda deshabilitada, sin apagar
`features.hooks` ni eliminar la caché compartida. Si la instalación nativa
falla, el manifiesto conserva el paso pendiente y no se declara activación.
La validación de rutas de la copia distingue campos nativos y sus scopes;
un valor de entorno de un MCP llamado `config_file` no es una ruta del runtime.

Cinco garantías del instalador, con test cada una en `tests/installer.test.mjs`:

1. **Idempotente** — reinstalar deja el mismo árbol y no duplica entradas de configuración.
2. **No pisa tu configuración** — los JSON se **fusionan**: lo que ya existe manda. `permission`
   de OpenCode ni se toca (ver §4), solo se avisa.
3. **Desinstalable con precisión** — cada instalación deja un `.custom-agents-install.json` (o
   `.custom-agents-install.plugin.json` en modo plugin) con la lista exacta de ficheros escritos y
   los apuntes de registro; `uninstall` borra esa lista, deshace esos apuntes y nada más. Un fichero
   tuyo en una carpeta nuestra sobrevive; tu configuración fusionada, también (no se borra nunca).
4. **Degrada** — si un proveedor falla, los demás se instalan igual; si falta la CLI de un runtime,
   se hace lo que se puede y se imprime el comando que queda pendiente.
5. **No miente** — si un paso no se pudo dar, sale en los avisos: nunca un «listo» por haber
   copiado ficheros.

### Las vías nativas (sin instalador)

| Runtime | Cómo |
|---|---|
| **Claude Code** | `/plugin marketplace add daycry/custom-agents` + `/plugin install custom-agents` (es lo que hace `--mode plugin`). Copiar el bundle como `.claude/` del proyecto (`docs/INSTALL.md`) equivale a `--mode copy`: sin hooks, sin statusline y sin namespace. |
| **Codex** | `codex plugin marketplace add daycry/custom-agents` seguido de `codex plugin add custom-agents@daycry`. Esta vía nativa habilita el plugin en config de usuario. Para conservar esa preferencia al instalar por proyecto, usa el instalador. |
| **OpenCode** | Copiar `interop/opencode/` a `.opencode/` + `skills/`, `agent-kits/` y `hooks/` dentro. Si ya tienes el bundle de Claude Code en `.claude/`, OpenCode **reutiliza esas skills** sin copiar nada (compatibilidad nativa). |

---

## 2. Qué se instala en cada runtime

| Pieza del plugin | Claude Code | Codex | OpenCode |
|---|---|---|---|
| **Skills** (24) | `.claude/skills/` | `skills/` del plugin (el manifiesto apunta ahí) | `.opencode/skills/` — *o* `.claude/skills/`, que lee de forma nativa |
| **Agentes** (10) | `agents/*.md` | `.codex/agents/*.toml` (generado) | `.opencode/agents/*.md` (generado) |
| **Comandos** (13) | `commands/*.md` (`/nombre`) | `~/.codex/prompts/*.md` (`/prompt:nombre`, a veces `/prompts:nombre`) | `.opencode/commands/*.md` (`/nombre`) |
| **Hooks** | `hooks/hooks.json` | `interop/codex/hooks.json` (subconjunto) | `.opencode/plugins/custom-agents` (adaptador JS) |
| **Kits** (`agent-kits/`) | `.claude/agent-kits/` | dentro del plugin | `.opencode/agent-kits/` |
| **Manifiesto** (`plugin.json`, de donde sale la versión) | dentro del plugin instalado (`.claude-plugin/`) | `.codex-plugin/plugin.json` | `.claude-plugin/plugin.json` — lo que `/doctor` lee para decir la versión (con fallback al de Codex) |
| **Statusline** | opt-in en `/setup` | — | — |

El formato de cada destino está verificado contra la doc oficial de su herramienta (Codex:
`developers.openai.com/codex` y `learn.chatgpt.com/docs`; OpenCode: `opencode.ai/docs`,
consultadas el 2026-09-08). Las **skills no se traducen**: su frontmatter (`name` + `description`)
es exactamente lo que exigen los tres runtimes.

### Cómo se traduce un agente

| Concepto del plugin | Codex (`.toml`) | OpenCode (frontmatter) |
|---|---|---|
| `description` | `description` | `description` |
| `tools` con Write/Edit | — | `permission.edit: allow\|deny` |
| `tools` sin escritura (`reviewer`) | Responsabilidad en el prompt; permisos heredados del padre | `permission.edit: deny` para herramientas de edición |
| `effort` (`medium`/`high`) | `model_reasoning_effort` | — |
| `model` (`sonnet`/`opus`) | — *(hereda de la sesión)* | `temperature` (0.1 / 0.2) |
| cuerpo del prompt | `developer_instructions` | cuerpo del `.md` |

`model` **no se traduce a Codex** a propósito: `haiku`/`sonnet`/`opus` no tienen equivalente en los
identificadores de OpenAI, así que el agente hereda el modelo de la sesión y del tiering solo viaja
el esfuerzo de razonamiento (que sí es portable). El tiering completo sigue siendo de Claude Code
(`ADR-009`).

A cada cuerpo traducido se le antepone un **preámbulo** de cuatro líneas que traduce lo único que
cambia de runtime: cómo se invoca una skill, cómo se delega en otro agente, qué guardrail no está
impuesto y dónde se resuelven los kits. El cuerpo original no se toca.

---

## 3. Resolución de rutas (regla 5 de CONVENTIONS)

Los agentes y skills localizan sus kits en tiempo de ejecución con un `find` sobre **seis raíces**,
dos por runtime, proyecto antes que usuario:

```bash
find "$PWD/.claude" "$PWD/.codex" "$PWD/.opencode" \
     "$HOME/.claude" "$HOME/.codex" "$HOME/.config/opencode" \
     -type d -path '*agent-kits/shared' 2>/dev/null | head -1
```

Ni Codex ni OpenCode buscan kits bajo `.claude/`, así que sin sus raíces un plugin instalado en
ellos encontraría sus skills pero **no** su toolkit. El directorio global de OpenCode es
`~/.config/opencode`, **no** `~/.opencode`. Si añades un runtime, la raíz se añade en **todas** las
piezas (hoy 88 ocurrencias en 56 ficheros) — el `find` no es un detalle de estilo.

---

## 4. Degradación: qué NO funciona igual

La tabla es la parte honesta del documento. Nada de esto rompe el ciclo; todo se pierde o se
sustituye, y aquí está dicho.

| Capacidad | Claude Code | Codex | OpenCode |
|---|---|---|---|
| **Registro del plugin** (qué lo hace cargar) | ✅ `installed_plugins.json` + `enabledPlugins`, por CLI o escrito por el instalador — ⚠️ con `--mode copy` no hay registro: el bundle está en `.claude/` y el runtime no se entera (`/doctor` lo marca) | CLI nativa ≥0.161.0: caché validada antes de declarar marketplace y activación. En modo proyecto, registro preparado en un `CODEX_HOME` privado y configuración local; `status` y `/doctor` separan declaración, listado nativo y ejecución | Paquete local V2 en `plugins` de `opencode.json`; `status` y `/doctor` comprueban la declaración, no la ejecución |
| Skills bajo demanda | ✅ herramienta Skill | ✅ `$nombre` o activación por `description` | ✅ herramienta `skill` |
| Comandos | ✅ `/nombre` | ⚠️ `/prompt:nombre` (**o** `/prompts:nombre`), **solo en `~/.codex/`** (Codex no tiene prompts por proyecto) y marcados como *deprecated* por OpenAI en favor de skills | ✅ `/nombre` |
| Delegar en un agente por nombre | Agent con `subagent_type: custom-agents:<rol>` | `spawn_agent` con `agent_type: custom-agents-<rol>`; el modelo decide cuándo delegar | V2 `subagent` con `agent: custom-agents-<rol>` |
| Aviso de progreso al editar el ledger | ✅ `PostToolUse` | ✅ `PostToolUse` para `apply_patch`, con rutas extraídas del parche | ✅ `tool.execute.after` |
| Contexto al arrancar la sesión | ✅ `SessionStart` (índice + roadmap + journal + memoria) | ✅ `SessionStart` (`startup\|resume\|clear\|compact`) | Hook nativo `session.context`: índice actual, roadmap, journal y memoria en el contexto de salida |
| Journal de sesión | `SessionEnd`: captura canónica aislada; evidencia headless sin ampliar el presupuesto nativo, con límites de arranque documentados | `SessionEnd`: export con 3 s y captura canónica; verificado al archivar el hilo activo en el mismo app-server | `session.execution.succeeded/failed/interrupted`; captura canónica y replay acotado en el siguiente contexto |
| Captura del turno del usuario | ✅ `UserPromptSubmit` | ✅ `UserPromptSubmit` | `session.prompt`, antes de admisión: petición provisional, con exclusión `<private>` |
| Fin de subagente | ✅ `SubagentStop` | ✅ `SubagentStop` | ❌ sin evento equivalente |
| **Guardia por agente** (`implementer`, `architect`) | Dispatcher global `PreToolUse` por ID propio; `hooks:` del agente de plugin se ignora | Dispatcher `PreToolUse` por ID propio | V2 `tool.execute.before` por ID propio; validación final de los tres runtimes en el roadmap |
| `reviewer` de solo lectura | Sin Write/Edit; Bash sigue sujeto a permisos y responsabilidad del rol | El TOML no impone sandbox independiente; hereda permisos del padre | `permission.edit: deny`; no equivale a prohibir toda escritura desde shell |
| Statusline del roadmap | ✅ opt-in | ❌ | ❌ |
| **Memoria de grafo** (capacidad `graphiti`, opt-in) | ✅ `/doctor` la comprueba en vivo por su adaptador | ✅ igual: el adaptador habla HTTP con el endpoint declarado, no con el MCP del runtime | Mismo adaptador opt-in; no se activa ningún backend al instalar |
| Permisos de OpenCode | — | — | El instalador conserva `permission`/`permissions` y no añade grants globales. |

### Identidad y actualización de agentes

Los agentes canónicos conservan `agents/<rol>.md`. Los exports nativos usan
`.codex/agents/custom-agents-<rol>.toml` y
`.opencode/agents/custom-agents-<rol>.md`; el contexto de sesión y los prompts
generados usan esos mismos IDs desde `agent-kits/shared/native-roles.json`.
Un agente personalizado con otro ID conserva sus permisos habituales. El ID
identifica el rol para el runtime, pero no acredita la procedencia del prompt:
redefinir exactamente un ID del plugin puede quedar sujeto a sus guardias.

El instalador comprueba colisiones en los directorios/configs conocidos del
proyecto y usuario. Conserva agentes ajenos, modificados, enlaces y referencias
ambiguas; señala conflictos como instalación incompleta. Solo retira un export
antiguo sin prefijo si pertenece al manifiesto anterior, coincide con el hash
publicado y no tiene bindings dentro del límite de un repositorio Git regular.
Las copias globales antiguas, worktrees con `.git` como archivo y referencias
que no puede verificar se conservan con diagnóstico. No recorre otros proyectos.
La desinstalación también conserva ediciones posteriores de los agentes propios.
En OpenCode se buscan referencias `{file:…}` en toda la configuración, incluidos
comandos, instrucciones y claves. Rutas `~/` o sustituciones de entorno que no
puede verificar conservan los agentes con diagnóstico; no lee secretos para
resolver esas referencias.
Si existen comandos Markdown en las capas conocidas, conserva también los
agentes antiguos: no interpreta su frontmatter para autorizar eliminaciones.
Emite un diagnóstico para revisar esas referencias antes de retirarlos a mano.

La guardia evalúa todas las rutas de mutación soportadas, incluyendo origen y
destino de movimientos. Claude admite Write/Edit/MultiEdit/NotebookEdit y las
reglas de comandos Bash/PowerShell; Codex admite `apply_patch` y comandos emitidos
como Bash; OpenCode V2 admite write/edit/patch/shell (`path`, `oldString`/`newString`,
`patchText`). Entrada no reconocida o mayor de 64 KiB continúa con diagnóstico;
no inspecciona toda escritura indirecta desde shell o MCP.

La evaluación nativa usa presupuesto interno de 4,5 s; registros previos Claude/
Codex declaran 10 s y OpenCode espera hasta 10,5 s incluyendo arranque y cleanup.
El primer registro de 5 s descartó un deny válido por tiempo total de Windows;
la evidencia fallida se conserva. La aceptación de la matriz final está en el
[ledger](roadmap/2026-10-07-catalog-capabilities/tasks.md) y el
[diseño](roadmap/2026-10-07-catalog-capabilities/design.md).

### Transporte OpenCode V2

El adaptador se distribuye como `.opencode/plugins/custom-agents/` con `index.js` y
`package.json`, y usa los dominios nativos `session`, `tool` y `event`. El hook de contexto
inyecta como máximo 10.000 caracteres sin modificar el historial persistido. Comprueba
la ubicación real de la sesión antes de leer o escribir; los eventos de otro proyecto o
workspace se descartan. Los hooks informativos degradan con aviso y continúan.

Los avisos de escritura usan los targets normalizados del resultado nativo y
los orígenes de su diff, para conservar la eliminación del documento al moverlo.
El contexto se reutiliza durante continuaciones de lectura, en una caché efímera
de una sola sesión y máximo 30 segundos. Prompts, herramientas completadas que
pueden modificar estado y cierres invalidan la entrada; antes de reutilizar se
contrastan metadatos de configuración, logs/cola, roadmap y memoria. Enlaces,
errores, árboles fuera del límite o una cola personalizada desactivan la caché.
El servicio compartido sigue componiendo el contexto. Cleanup aborta la
suscripción, termina los procesos propios y espera su cierre.

El journal mantiene la política compartida: solo captura proyectos con `docs/roadmap`,
`docs/knowledge` o `.claude/dev.json`, respetando opt-outs de sesión y turno. El stream
local V2 omite `location`; `session.get` verifica proyecto y workspace antes de escribir.
Los eventos con ubicación ajena se descartan.

La actualización retira el archivo antiguo solo si coincide con una copia conocida
(incluyendo diferencias CRLF/LF) y elimina únicamente sus referencias propias. Si está
modificado, lo conserva y avisa de migración pendiente. Las instrucciones y permisos del
usuario se conservan. El índice estático queda consultable; V2 no lo carga por `instructions`.

Contrato: [plugins V2](https://opencode.ai/v2/docs/build/plugins/) y
[migración V1](https://opencode.ai/v2/docs/build/plugins/migrate-v1), verificados el 2026-10-08.
La validación de guardias nativas de los tres runtimes sigue abierta en el roadmap.

### Arranque portable de los hooks

Los tres runtimes usan `hooks/run-hook.mjs`: requiere Node 18+ (el mismo requisito del instalador)
y Python 3. En Windows busca Python nativo (`python3`, `python` o `py -3`) y Git Bash en PATH;
descarta el `bash.exe` de System32 que lanza WSL. `CUSTOM_AGENTS_PYTHON` permite indicar un
intérprete concreto. El payload viaja por stdin, nunca como código de shell.

SessionEnd llama al escritor canónico `journal-capture.py` con Python aislado (`-I -S`);
la guardia previa también usa Python aislado sin Bash. UserPromptSubmit llama
a `journal.py capture`, sin Bash. Los demás hooks
usan Bash con un adaptador `python3` al intérprete seleccionado. Si falta una herramienta,
se avisa por stderr y se continúa con exit 0. Las guardias de implementer y architect conservan su alcance por agente.

Codex limita SessionEnd a 3 s; el exportador ajusta ese timeout. Claude Code dispone
de 1,5 s por defecto, aunque nuestro plugin declare 5 s. El deadline interno del
hijo es 800 ms en Claude y 2.200 ms en Codex/OpenCode, por argumento literal del
adaptador. Se espera el cierre del árbol de procesos al agotar el tiempo. Las fixtures
headless finales Claude 2.1.287 y Codex 0.161.0 verifican captura y cierre; no acreditan
latencia universal, salida TUI ni guardias. OpenCode V2 captura al terminar la ejecución y materializa
con replay acotado en el siguiente contexto. Tras actualizar un plugin hay que iniciar una sesión nueva; las
pruebas con payloads no sustituyen la comprobación de eventos dentro de cada aplicación.
Contratos contrastados el 2026-10-08; evidencia en [contratos del roadmap](roadmap/2026-10-07-catalog-capabilities/contracts.md): [Codex](https://learn.chatgpt.com/docs/hooks),
[Claude Code](https://code.claude.com/docs/en/hooks), [OpenCode](https://opencode.ai/docs/plugins/).

Los tres huecos que más importan:

- **Copiar el bundle no instala el plugin.** Es el hueco que más se nota y el más fácil de no ver:
  con `--mode copy` (o copiando `.claude/` a mano) está el bundle entero y no está ninguna de las
  tres cosas que da un plugin instalado —hooks, statusline y namespace `/custom-agents:`—, porque
  Claude Code solo lee `hooks/hooks.json` dentro de un plugin. `/doctor` lo dice en la fila «hooks
  registrados» (⚠️, no ✅) y `status` en «registrado: no».

- **Las guardias dependen de su carga y alcance.** El dispatcher selecciona IDs propios
  desde metadata nativa y consulta la política central. Herramientas desconocidas, input
  incompleto y errores degradan; shell/MCP arbitrario necesita permisos del runtime.
  La matriz nativa final sigue abierta en el roadmap; un test del launcher no la sustituye.
  El launcher recoge un resultado estructurado acotado antes de entregar la decisión.
  Una evaluación ausente o inválida avisa mediante `systemMessage` en Claude/Codex
  y diagnóstico estructurado en OpenCode, conservando los permisos normales.
  Un bloqueo completo se conserva aunque falle después el cierre del evaluador o
  la confirmación de limpieza. Esto no acredita resolver el arranque bajo carga.
- **Los eventos difieren por runtime.** Codex entrega los cambios de apply_patch en
  `tool_input.command`; el launcher los convierte a `edits[].file_path` para los hooks de shell.
  OpenCode V2 conserva los avisos en `result.metadata.customAgentsMessages`, sin cambiar
  el contenido de la herramienta ni prometer un toast de UI.

---

## 5. Mantenerlo al día

```bash
python3 scripts/export-interop.py            # regenera los ficheros de interop
python3 scripts/export-interop.py --check    # ¿reflejan las piezas del repo? (CI y release.py)
python3 scripts/export-interop.py --list     # qué ficheros genera
python3 -m pytest -q tests/test_export_interop.py
node --test "tests/*.test.mjs"                # instalador + adaptador de hooks
```

> **¿Está bien instalado?** `/doctor` diagnostica la instalación de **Claude Code** (es un comando
> del plugin y se ejecuta dentro de él). Para Codex y OpenCode, el equivalente es
> `npx @daycry/custom-agents status`, que lee el manifiesto de cada instalación.

**Al tocar un agente, un comando o un hook, regenera.** `--check` es puerta de `release.py`, así
que una interop desincronizada no se publica. Lo generado lleva cabecera «GENERADO» y ruta de
origen; si te encuentras editando un fichero de `interop/`, estás editando la copia.

Al añadir una pieza nueva, lo único que hay que recordar: **la `description` de una skill no puede
pasar de 1.024 caracteres** (OpenCode la valida y, si se pasa, la skill no carga). Lo avisa el
linter y lo falla `tests/test_export_interop.py`.

| Fichero | Qué es |
|---|---|
| `scripts/export-interop.py` | el generador (solo stdlib, determinista, `--check`) |
| `install/install.mjs` · `install/providers.mjs` | el instalador (`npx`, cero dependencias) |
| `hooks/opencode-plugin.js` | **fuente** del adaptador de hooks de OpenCode (la copia viaja a `interop/`) |
| `.codex-plugin/plugin.json` · `.agents/plugins/marketplace.json` | manifiestos de Codex (generados) |
| `interop/codex/` · `interop/opencode/` | árboles traducidos (generados) |
| `tests/test_export_interop.py` · `tests/installer.test.mjs` · `tests/opencode-plugin.test.mjs` | las puertas |


## Presupuesto del brief

Agentes, skills, personas, fuentes de tools y MCP propios se reconocen mediante
el lector compartido para los tres runtimes. La selección conserva IDs, origen
y referencias nativas; no convierte formatos ni infiere carga, conexión o
permisos. [Guía de extensiones](PROJECT-EXTENSIONS.md). En el brief fija el runtime
y las mismas raíces del inventario; las referencias ocupan ≤1000 caracteres y
comparten el margen auxiliar. La generación/adopción mantiene el plan independiente
de project-specialization.

El brief acota diseño a 1.600 caracteres, gaps a 1.600 y verificación a 800. Incluye el diseño elegido para las rutas coincidentes de la tarea y enlaza las evidencias históricas al ledger. Conserva completos los requisitos, las notas de decisión y los criterios de aceptación. Las secciones auxiliares comparten el margen global antes de asignar la persona. Si el mínimo protegido supera 10.000 caracteres, informa de su tamaño exacto: hay que dividir la tarea antes de delegarla. Memoria, persona y contrato de retorno conservan sus reglas existentes.
