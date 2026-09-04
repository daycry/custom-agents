# Instalación y despliegue

[English](en/INSTALL.md) · **Español**

Bundle de agentes custom para Claude Code que cubren el ciclo de una iniciativa (requisitos → presupuesto → plan → implementación → pruebas → documentación) con contabilidad de tiempo/coste y trazabilidad opcional en Jira/Confluence. Agentes: **analyst** (toma de requerimientos), **evaluator** (evalúa/presupuesta), **planner** (planes), **implementer** (implementa), **qa** (E2E Playwright), **documenter** (documentación) y **nemesis** (auditoría SAST+DAST). Skills compartidas: **cybersecurity**, **to-pdf**, **confluence-publish**, **confluence-pull**, **roadmap-dashboard** y **jira-sync**. Comandos: **/setup**, **/pm-cycle**, **/dev-cycle**, **/pm-backlog**, **/roadmap-status**, **/roadmap-metrics**, **/roadmap-brief**, **/roadmap-live**, **/retro** y **/confluence-pull**.

Contenido (todo cuelga de la raíz del bundle, que se despliega como `.claude/`):
- `agents/*.md` — definiciones de los agentes.
- `skills/<skill>/` — skills compartidas (algunas con `scripts/` y `assets/`).
- `commands/*.md` — comandos orquestadores (`/…`).
- `agent-kits/<agente>/` — toolkits/plantillas privadas de cada agente.
- `.claude-plugin/` — manifiesto de plugin y marketplace (para la vía 3).
- `docs/` — documentación (no se carga como código; el loader la ignora). Ver [`README.md`](README.md) (índice), [`FLOWS.md`](FLOWS.md) (diagramas), [`CONVENTIONS.md`](CONVENTIONS.md) y [`atlassian-connector-notes.md`](atlassian-connector-notes.md).
- `.github/workflows/ci.yml` — CI (tests + sintaxis + coherencia de versión).

Las rutas de los kits se resuelven en tiempo de ejecución con un `find` sobre `$PWD/.claude` y `$HOME/.claude`, así que **los agentes funcionan igual en las tres vías** siguientes.

> ⚠️ **No clones el repositorio dentro de una carpeta sincronizada en la nube** (OneDrive, Dropbox, Google Drive, iCloud…). El sincronizador y git se pisan: bloquea los ficheros `.lock` y objetos de `.git` mientras sube, lo que provoca errores tipo `Unable to create '.git/HEAD.lock'`, "index file corrupt" o ficheros que se leen a medias. Clónalo en una ruta local **fuera** del área sincronizada (p. ej. `C:\dev\custom-agents` o `~/code/custom-agents`). Si ya lo tienes en una carpeta sincronizada y ves esos errores: pausa la sincronización, borra los `.git/*.lock`, ejecuta `git status` para reconstruir el índice, y considera mover el repo fuera.

> ℹ️ **Windows — símbolos en la consola.** Los scripts del plugin imprimen `✅ ⚠️ ❌`. Desde la
> versión que arregla `GOT-005` reconfiguran su salida a UTF-8 al arrancar, así que **no** revientan
> con `UnicodeEncodeError` aunque el locale sea `cp1252` (Windows español) o la salida vaya a un
> pipe — que es como `release.py` lanza sus checks. En una consola moderna (Windows Terminal,
> PowerShell 7) los símbolos se ven bien; en una **consola legacy** (`cmd.exe` con codepage antiguo o
> `PYTHONLEGACYWINDOWSSTDIO=1`) se ven como caracteres raros (`âœ…`), no como `?` (medido): es **esperado**
> y solo afecta a cómo se dibuja el símbolo — el veredicto, el texto y el exit code son correctos. Si
> te molesta, `chcp 65001` antes de ejecutar, o usa Windows Terminal.

---

## Vía 1 — Probar en un proyecto (rápido)

Enlaza (o copia) el bundle como `.claude/` del proyecto a probar:

```bash
# symlink (recomendado para probar; refleja cambios del repo al instante)
ln -s "/ruta/al/repo/custom-agents" "/ruta/al/proyecto/.claude"

# o copia
cp -r "/ruta/al/repo/custom-agents/." "/ruta/al/proyecto/.claude/"
```

En Claude Code, dentro del proyecto: `/agents` para verlos e invócalos con `@analyst`, `@evaluator`, `@planner`, `@implementer`, `@qa`, `@nemesis` (o "usa el agente …"). Para el flujo completo, usa los comandos (`/setup`, `/pm-cycle`, `/dev-cycle`…).

---

## Vía 2 — Reuso personal en todos tus proyectos (`~/.claude/`)

Copia el contenido a tu carpeta de usuario; queda disponible en **todos tus proyectos** (precedencia: si un proyecto define un agente con el mismo nombre, gana el del proyecto):

```bash
cp -r "/ruta/al/repo/custom-agents/agents/."      "$HOME/.claude/agents/"
cp -r "/ruta/al/repo/custom-agents/skills/."      "$HOME/.claude/skills/"
cp -r "/ruta/al/repo/custom-agents/agent-kits/."  "$HOME/.claude/agent-kits/"
```

El resolvedor de ruta encuentra los kits en `~/.claude/agent-kits/…` automáticamente.

---

## Vía 3 — Plugin + marketplace (recomendado, escalable y para el equipo)

El bundle ya incluye `.claude-plugin/plugin.json` y `.claude-plugin/marketplace.json`. Publica el repo en git (GitHub) y añádelo como marketplace. Dos formas según dónde trabajes:

**a) CLI de Claude Code (terminal).** Abre una terminal, lanza `claude` y, dentro de la sesión:

```
/plugin marketplace add daycry/custom-agents
/plugin install custom-agents@daycry
```

**b) Claude Desktop / Cowork (interfaz).** Menú **Customize** (barra lateral) → pestaña **Plugins**. En Cowork, abre antes la pestaña **Cowork**. En **Personal plugins**, botón **"+"** → **Add marketplace** → **Add from a repository** → pega la URL del repo (`https://github.com/daycry/custom-agents.git`). Después **Install** en el plugin `custom-agents`.

Tras instalar, los agentes quedan disponibles en **todos los proyectos** de la máquina.

> **Namespacing (por qué la Vía 3 es la preferente).** Instalado como plugin, Claude Code **prefija** automáticamente todo con el nombre del plugin: los agentes y commands se invocan como `custom-agents:evaluator`, `/custom-agents:dev-cycle`, etc. — como cualquier plugin bien empaquetado. Así **nunca chocan** con agentes/commands de otro plugin, aunque compartan nombre. En cambio, en las **Vías 1 y 2** (copiar el bundle a un `.claude/`) los nombres van "pelados" (`evaluator`, `/dev-cycle`) y **pueden colisionar** con otro `.claude/` que use el mismo nombre. El linter avisa de los nombres más genéricos (`setup`, `retro`, …) precisamente por esto. Regla práctica: para uso real y en equipo, **instala como plugin** (Vía 3); reserva las Vías 1/2 para desarrollo del propio bundle.

> **Dónde corre cada cosa.** Los **comandos `/plugin …` solo funcionan en una sesión de Claude Code** (terminal con `claude`), **no** en la caja de chat normal. Los **sub-agentes se ejecutan solo en Cowork** (en el chat normal aparecen en gris); las **skills** funcionan en chat web, Chat de Desktop y Cowork.

> **Caveat de rutas.** En Claude Code, `${CLAUDE_PLUGIN_ROOT}` no se expande dentro del markdown de agentes/skills. Por eso los agentes NO usan rutas fijas: resuelven su kit con `find` sobre `$PWD/.claude` y `$HOME/.claude` (el segundo cubre tanto `~/.claude/` como el caché de plugins `~/.claude/plugins/…`). Es la razón de que las tres vías funcionen sin tocar nada.

---

## Actualizar el plugin tras cambios en el repo

**Regla de oro:** Claude Code detecta actualizaciones **por número de versión**, no por commit. Si publicas cambios sin subir la versión, `update` no verá nada.

### Al publicar (autor del repo)
1. Escribe las notas del release en `CHANGELOG.md` (`## [Unreleased]`) y `CHANGELOG.es.md` (`## [Sin publicar]`) — **el script no inventa notas**: si están vacías, aborta.
2. Lanza el **release mecánico completo** (recomendado). En un solo paso, y sin tocar nada si algo falla antes de escribir:

   ```bash
   python scripts/release.py 1.5.1 --dry-run   # muestra el plan completo sin tocar nada
   python scripts/release.py 1.5.1             # release: changelog + checks + bump + chmod + commit + tag v1.5.1
   python scripts/release.py --check           # versiones coherentes Y sección [X.Y.Z] en ambos CHANGELOG
   ```

   Qué hace: (a) mueve el contenido de `[Unreleased]`/`[Sin publicar]` a `## [1.5.1] - <hoy>` en los **dos** CHANGELOG y añade el enlace `[1.5.1]: …/releases/tag/v1.5.1` (aborta si están vacíos, salvo `--allow-empty-notes`); (b) corre `scripts/lint_plugin.py` y `evals/check.py` y comprueba que cada `*.MANUAL-COPY` coincide con su copia en `.github/` (aborta si fallan; `--skip-checks` los salta); (c) sube la versión en los **tres** sitios donde vive (`plugin.json`, y en `marketplace.json` tanto `metadata.version` como la entrada del plugin); (d) corrige con `git update-index --chmod=+x` los `.sh` versionados que hayan llegado en modo `100644` (trampa habitual desde Windows) avisando; (e) `commit` `chore: release v1.5.1` + `tag v1.5.1`. `--no-git` deja solo los ficheros. Tests: `tests/test_release.py` (repo git temporal).

   Si prefieres a mano: edita esos **tres** campos al **mismo** número y mueve las notas en los dos CHANGELOG. Si las versiones no coinciden o no suben, el cliente no detecta la actualización (es el fallo más común).
3. `git push origin HEAD && git push origin vX.Y.Z`. El workflow `release.yml` crea la GitHub Release con las notas de esa sección del CHANGELOG y adjunta el zip del plugin y el zip portable de skills.

> Confirma antes de publicar con `python scripts/release.py --check` (versiones coherentes en ambos manifiestos y sección de la versión en ambos CHANGELOG).

### Al actualizar — CLI de Claude Code
En una sesión `claude`:

```
/plugin marketplace update daycry
/plugin update custom-agents@daycry
/reload-plugins
```

### Al actualizar — Claude Desktop / Cowork (interfaz)
**Customize → Plugins**, localiza el marketplace `daycry` y abre su menú (**⋯**).

- Si el botón **Update / Actualizar** está activo, úsalo.
- **Si el botón de actualizar aparece deshabilitado** (caso conocido): **quita el marketplace y vuelve a añadirlo** — menú **⋯ → Remove**, luego **"+" → Add marketplace → Add from a repository** con la URL del repo. Eso re-sincroniza la última versión. Reinstala el plugin si hiciera falta.

### Si sigue mostrando la versión antigua (caché)
El caché vive en `~/.claude/plugins/cache/` (una carpeta por versión). Reinstala:

```
/plugin uninstall custom-agents@daycry
/plugin install custom-agents@daycry
```

o, opción nuclear, borra el caché y reinstala:

```
rm -rf ~/.claude/plugins/cache/
```

---

## Usar las skills fuera de Claude Code (paquete portable)

Las **skills** son markdown + Python y no dependen del runtime de Claude Code; los agentes, comandos, hooks y la statusline sí. Por eso el repo exporta un **paquete portable «solo skills»** (patrón multi-entorno de superpowers) que puedes usar en **Codex, GitHub Copilot, Cursor, Jules** o cualquier herramienta que lea [`AGENTS.md`](https://agents.md) o reglas de Cursor:

```bash
python3 scripts/export-skills.py --out dist/portable --format all   # claude | agents-md | cursor | all
python3 scripts/export-skills.py --check dist/portable              # valida el paquete (referencias, hash, sin `find` colgando)
```

Cada Release de GitHub adjunta el mismo paquete como `custom-agents-skills-portable-<versión>.zip` (junto al zip del plugin), así que no necesitas clonar el repo.

| Formato | Qué genera | Cómo se usa |
|---|---|---|
| `claude` | `skills/` + `agent-kits/shared/` (solo los fragmentos citados) + `README.md` | copia `skills/*` a `.claude/skills/` y `agent-kits/shared/` a `.claude/agent-kits/shared/` de un proyecto sin el plugin |
| `agents-md` | + `AGENTS.md` raíz con el índice compacto de skills («lee `skills/<n>/SKILL.md` cuando aplique») | Codex, Copilot, Jules… leen `AGENTS.md` de la raíz del repo (markdown plano, sin frontmatter) |
| `cursor` | + `.cursor/rules/custom-agents-skills.mdc` (frontmatter `description` + `alwaysApply: false` → regla *Agent-Selected*) | Cursor la adjunta cuando la petición casa con la descripción |

**Qué viaja y qué no** lo documenta el `README.md` del paquete (ES+EN, tabla «qué viaja / qué no / por qué», hash sha256 del contenido). No viajan: `agents/`, `commands/`, `hooks/`, `statusline/`, los kits privados y las skills que son punteros a piezas que no viajan (`quick-implement`, `plugin-dev`). **Rutas:** en la copia, el `find` sobre `$PWD/.claude` y `$HOME/.claude` se reescribe a `find "${PORTABLE_ROOT:-.}"` — ejecuta desde la carpeta que contiene `skills/` y `agent-kits/shared/` o exporta `PORTABLE_ROOT`; una skill que cite algo que no viajó degrada con aviso, nunca bloquea. El paquete es determinista (misma entrada → mismo árbol y mismo hash) y `tests/test_export_skills.py` lo cubre.

---

## Conector de Atlassian (Jira & Confluence) — para `confluence-publish`, `confluence-pull` y `jira-sync`

El mismo **conector oficial de Atlassian (Rovo MCP)** da servicio a tres integraciones, **todas
opt-in** e independientes: **Confluence** (`confluence-publish` sube `docs/`; `confluence-pull` los
baja) y **Jira** (`jira-sync` vuelca el plan a issues, imputa horas y marca *Done*; `/roadmap-live`
lee el estado en vivo). Un alta única del conector cubre las tres. Comportamientos verificados del
conector en [`atlassian-connector-notes.md`](atlassian-connector-notes.md).

La skill `confluence-publish` publica/espeja la documentación de `docs/` en Confluence, y los
agentes `planner`, `evaluator`, `qa` y `documenter` la invocan al escribir en `docs/` (paso "Sincronizar con
Confluence"). Es **opcional (opt-in)**: la primera vez la skill pregunta si quieres sincronizar
con Confluence; si dices que **no**, lo recuerda (`"enabled": false` en `.claude/confluence.json`)
y no vuelve a preguntar ni sincroniza. Si dices que **sí**, se conecta y se ejecuta el asistente.
Todo va por el **conector oficial de Atlassian (Rovo MCP)** — no hay integración propia. Si vas a
usar la sincronización, da de alta el conector **una vez** por entorno:

- **Claude Desktop / Cowork (UI):** menú **Customize → Connectors** (o **Conectores**) → añade
  **Atlassian (Jira & Confluence)** y completa el login OAuth. Es lo que se usa en la app.
- **Claude Code CLI (terminal):** registra el MCP remoto y autentícate:
  ```bash
  claude mcp add --transport http atlassian https://mcp.atlassian.com/v1/mcp
  # luego, dentro de una sesión `claude`, sigue el flujo OAuth que aparezca
  ```
- **Extensión de VS Code:** usa la misma configuración MCP de Claude Code (el `claude mcp add`
  anterior sirve; la extensión comparte los servidores MCP del CLI).

Comportamiento por entorno:

- **Cowork / escritorio:** el paso de "elegir dónde publicar" abre un **navegador de árbol
  interactivo** (artefacto) que expande páginas en vivo.
- **CLI / VS Code:** no hay host de artefactos, así que ese paso es **conversacional**
  (la skill lista espacios y páginas por texto y eliges por número). El resto —crear/actualizar
  páginas y la sincronización de los agentes— es **idéntico** en los tres entornos.

Notas:

- La primera vez, la skill te guía para elegir espacio y anclaje (raíz o bajo una página) y
  guarda la decisión en `.claude/confluence.json` del proyecto; después es automático.
- **Detección de cambios sin git:** la skill mantiene un manifiesto `.claude/confluence-state.json`
  (hash de contenido + `pageId` por documento) y publica solo lo que cambió (crear/actualizar/
  marcar obsoleto). Es idempotente e independiente de commits o fechas.
- **Hook opcional (disparador):** el plugin incluye un hook `PostToolUse` (`hooks/hooks.json`) que,
  al editar ficheros bajo `docs/`, deja una marca `.claude/.confluence-pending`; no publica nada.
  La sincronización real la hace la skill (respetando el opt-in). Los hooks de un plugin se activan
  al instalarlo; tras cambios en `hooks/` hace falta `/reload-plugins`.
- **Nunca** se sincroniza `docs/security-scan/**` (datos sensibles de `nemesis`).
- El conector Atlassian **no** permite borrar páginas: al eliminar un `.md`, la página se marca
  como obsoleta y se lista para borrado manual.

---

## Notas específicas de `nemesis`

- El pentest activo SOLO opera contra hosts locales/privados (guardrail `lib-guardrail.sh`). No apunta a terceros.
- La primera vez comprueba su toolkit y PIDE PERMISO antes de instalar lo que falte (binarios en `~/.claude/security-tools/`, fuera del repo).
- Informes en `docs/security-scan/<fecha>/index.html` del proyecto auditado. Esa subruta va en el `.gitignore` del proyecto (los hallazgos son sensibles); el resto de `docs/` sí se versiona.
- Requisitos por máquina: git, curl y python o php. El instalador resuelve el resto.

---

## Memoria técnica del proyecto (`docs/knowledge/`)

En un proyecto recién instalado, `docs/knowledge/` **todavía no existe** — nace vacía y se puebla
con el tiempo, a medida que `planner`/`implementer` cruzan el umbral de una decisión de diseño,
`debug-root-cause`/`qa` registran una trampa comprobada, y `/retro` cierra iniciativas con
aprendizajes técnicos. No hay que crearla a mano ni esperar contenido desde el primer día: ver
regla 10 de [`CONVENTIONS.md`](CONVENTIONS.md). Las carpetas `gotchas/` y `lessons/` (una entrada
por fichero, igual que `adr/`) nacen **directas** en el primer registro — sin los ficheros stub
`gotchas.md`/`LESSONS.md` que sí existen en este repo (arrastrados desde antes del split
`docs/knowledge/adr/ADR-006-*`, porque la escritura remota no puede borrarlos del disco de quien
ya los tenía).

---

## Observabilidad y monitores de sesión

El plugin mide el **coste** (tokens/€/horas por artefacto y tarea — `usage-meter`); para ver la
**actividad de sesión en vivo** (herramientas, subagentes, kanban) puedes instalar al lado un
monitor externo como Claude-Code-Agent-Monitor: los hooks de ambos conviven sin interferirse.
Detalle y chuleta de "dónde mirar cada cosa": [`observability.md`](observability.md).
