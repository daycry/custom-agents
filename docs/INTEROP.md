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
| `--dry-run` | plan completo sin escribir nada |
| `-y, --yes` | sin preguntas (CI) |

Cuatro garantías del instalador, con test cada una en `tests/installer.test.mjs`:

1. **Idempotente** — reinstalar deja el mismo árbol y no duplica entradas de configuración.
2. **No pisa tu configuración** — los JSON se **fusionan**: lo que ya existe manda. `permission`
   de OpenCode ni se toca (ver §4), solo se avisa.
3. **Desinstalable con precisión** — cada instalación deja un `.custom-agents-install.json` con la
   lista exacta de ficheros escritos; `uninstall` borra esa lista y nada más. Un fichero tuyo en
   una carpeta nuestra sobrevive; tu configuración fusionada, también (no se borra nunca).
4. **Degrada** — si un proveedor falla, los demás se instalan igual.

### Las vías nativas (sin instalador)

| Runtime | Cómo |
|---|---|
| **Claude Code** | `/plugin marketplace add daycry/custom-agents` + `/plugin install custom-agents`. O copiar el bundle como `.claude/` del proyecto (`docs/INSTALL.md`). |
| **Codex** | `codex plugin marketplace add daycry/custom-agents` (lee `.codex-plugin/plugin.json` y `.agents/plugins/marketplace.json` del repo). Los agentes `.toml` y los prompts se copian a mano desde `interop/codex/` (o los pone el instalador). |
| **OpenCode** | Copiar `interop/opencode/` a `.opencode/` + `skills/`, `agent-kits/` y `hooks/` dentro. Si ya tienes el bundle de Claude Code en `.claude/`, OpenCode **reutiliza esas skills** sin copiar nada (compatibilidad nativa). |

---

## 2. Qué se instala en cada runtime

| Pieza del plugin | Claude Code | Codex | OpenCode |
|---|---|---|---|
| **Skills** (17) | `.claude/skills/` | `skills/` del plugin (el manifiesto apunta ahí) | `.opencode/skills/` — *o* `.claude/skills/`, que lee de forma nativa |
| **Agentes** (9) | `agents/*.md` | `.codex/agents/*.toml` (generado) | `.opencode/agents/*.md` (generado) |
| **Comandos** (12) | `commands/*.md` (`/nombre`) | `~/.codex/prompts/*.md` (`/prompts:nombre`) | `.opencode/commands/*.md` (`/nombre`) |
| **Hooks** | `hooks/hooks.json` | `interop/codex/hooks.json` (subconjunto) | `.opencode/plugins/custom-agents-hooks.js` (adaptador JS) |
| **Kits** (`agent-kits/`) | `.claude/agent-kits/` | dentro del plugin | `.opencode/agent-kits/` |
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
| `tools` sin escritura (`reviewer`) | `sandbox_mode = "read-only"` | `permission.edit: deny` |
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
| Skills bajo demanda | ✅ herramienta Skill | ✅ `$nombre` o activación por `description` | ✅ herramienta `skill` |
| Comandos | ✅ `/nombre` | ⚠️ `/prompts:nombre`, **solo en `~/.codex/`** (Codex no tiene prompts por proyecto) y marcados como *deprecated* por OpenAI en favor de skills | ✅ `/nombre` |
| Delegar en un agente por nombre | ✅ herramienta Agent, con `model` por invocación | ⚠️ en lenguaje natural; Codex **no auto-invoca** agentes custom, hay que pedirlo | ✅ herramienta `task` |
| Aviso de progreso al editar el ledger | ✅ `PostToolUse` | ❌ Codex solo dispara Pre/PostToolUse para `Bash`; los tres hooks miran `Write\|Edit` → **no viajan** | ✅ `tool.execute.after` |
| Contexto al arrancar la sesión | ✅ `SessionStart` (índice + roadmap + journal + memoria) | ✅ `SessionStart` (`startup\|resume\|clear`) | ⚠️ sin hook que inyecte contexto → se sustituye por `custom-agents-index.md` en `instructions`: **el índice de piezas sí, lo dinámico no** |
| Journal de sesión | ✅ `SessionEnd` | ✅ `SessionEnd` | ⚠️ se dispara en `session.idle`; `journal.py` es idempotente por `session_id`, así que **actualiza** la entrada en vez de duplicarla |
| Captura del turno del usuario | ✅ `UserPromptSubmit` | ✅ `UserPromptSubmit` | ❌ sin evento documentado → el journal se queda con su parte determinista (git + ledger) |
| Fin de subagente | ✅ `SubagentStop` | ✅ `SubagentStop` | ❌ sin evento equivalente |
| **Guardrail de guardia por agente** (`implementer`, `architect`) | ✅ `deny` real vía `hooks:` del frontmatter (`ADR-007`) | ❌ no existe hook por agente → el agente lo **auto-comprueba** con `guardrail-check.py` (el preámbulo se lo dice y le da el comando) | ❌ igual que Codex; `permission` acota herramientas, no rutas |
| `reviewer` de solo lectura | ✅ sin Write/Edit en `tools` | ✅ `sandbox_mode = "read-only"` | ✅ `permission.edit: deny` |
| Statusline del roadmap | ✅ opt-in | ❌ | ❌ |
| `permission` de OpenCode | — | — | ⚠️ el instalador **no lo toca** si ya existe: OpenCode aplica «la última regla que casa», así que añadir `skill: {"*": "allow"}` detrás de un `deny` tuyo te lo abriría. Si tienes política propia, comprueba que las skills `custom-agents` no caigan en un `deny`. |

Los dos huecos que más importan:

- **El guardrail del `implementer` no está impuesto fuera de Claude Code.** Es un `deny` de
  `PreToolUse` con alcance de un solo agente, y eso solo existe aquí. En Codex y OpenCode el agente
  recibe la instrucción de comprobarlo él (`guardrail-check.py pre-tool --agent implementer`) antes
  de un git destructivo o de escribir en `docs/roadmap/` fuera de `tasks.md`. Es una regla de
  prompt, no una barrera: en esos runtimes, revisa el diff.
- **Los avisos de progreso no llegan a Codex.** No es un fallo de configuración: Codex solo emite
  Pre/PostToolUse para `Bash`. Registrarlos sería prometer un aviso que nunca se dispara, así que
  `interop/codex/hooks.json` los omite a propósito (lo afirma `tests/test_export_interop.py`).

---

## 5. Mantenerlo al día

```bash
python3 scripts/export-interop.py            # regenera los 48 ficheros de interop
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
