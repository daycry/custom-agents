# Instalación y despliegue

Bundle de agentes custom para Claude Code: **nemesis** (auditoría SAST+DAST), **evaluator** (evalúa/presupuesta specs), **planner** (planes presupuestados), **qa** (E2E con Playwright), **pdfy** (conversión a PDF) y **documenter** (documentación técnica y de producto), más las skills compartidas **cybersecurity**, **to-pdf** y **confluence-publish**.

Contenido (todo cuelga de la raíz del bundle, que se despliega como `.claude/`):
- `agents/*.md` — definiciones de los agentes.
- `skills/<skill>/` — skills compartidas (`cybersecurity`, `to-pdf`, `confluence-publish`).
- `agent-kits/<agente>/` — toolkits/plantillas privadas de cada agente.
- `.claude-plugin/` — manifiesto de plugin y marketplace (para la vía 3).
- `docs/` — documentación (no se carga como código; el loader la ignora).

Las rutas de los kits se resuelven en tiempo de ejecución con un `find` sobre `$PWD/.claude` y `$HOME/.claude`, así que **los agentes funcionan igual en las tres vías** siguientes.

---

## Vía 1 — Probar en un proyecto (rápido)

Enlaza (o copia) el bundle como `.claude/` del proyecto a probar:

```bash
# symlink (recomendado para probar; refleja cambios del repo al instante)
ln -s "/ruta/al/repo/custom-agents" "/ruta/al/proyecto/.claude"

# o copia
cp -r "/ruta/al/repo/custom-agents/." "/ruta/al/proyecto/.claude/"
```

En Claude Code, dentro del proyecto: `/agents` para verlos e invócalos con `@nemesis`, `@evaluator`, `@planner`, `@pdfy` (o "usa el agente …").

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
/plugin marketplace add daycry/claude-agents
/plugin install custom-agents@daycry
```

**b) Claude Desktop / Cowork (interfaz).** Menú **Customize** (barra lateral) → pestaña **Plugins**. En Cowork, abre antes la pestaña **Cowork**. En **Personal plugins**, botón **"+"** → **Add marketplace** → **Add from a repository** → pega la URL del repo (`https://github.com/daycry/claude-agents.git`). Después **Install** en el plugin `custom-agents`.

Tras instalar, los agentes quedan disponibles en **todos los proyectos** de la máquina.

> **Dónde corre cada cosa.** Los **comandos `/plugin …` solo funcionan en una sesión de Claude Code** (terminal con `claude`), **no** en la caja de chat normal. Los **sub-agentes se ejecutan solo en Cowork** (en el chat normal aparecen en gris); las **skills** funcionan en chat web, Chat de Desktop y Cowork.

> **Caveat de rutas.** En Claude Code, `${CLAUDE_PLUGIN_ROOT}` no se expande dentro del markdown de agentes/skills. Por eso los agentes NO usan rutas fijas: resuelven su kit con `find` sobre `$PWD/.claude` y `$HOME/.claude` (el segundo cubre tanto `~/.claude/` como el caché de plugins `~/.claude/plugins/…`). Es la razón de que las tres vías funcionen sin tocar nada.

---

## Actualizar el plugin tras cambios en el repo

**Regla de oro:** Claude Code detecta actualizaciones **por número de versión**, no por commit. Si publicas cambios sin subir la versión, `update` no verá nada.

### Al publicar (autor del repo)
1. Haz los cambios.
2. **Sube la versión** en `.claude-plugin/plugin.json` **y** `.claude-plugin/marketplace.json` (p. ej. `1.2.0` → `1.2.1`). Ambos deben quedar con el **mismo** número; si no coinciden o no suben, el cliente no detecta la actualización.
3. Commit + push al repo (opcional: tag `vX.Y.Z`).

> Versión actual publicada-pendiente: **1.3.0** (ya reflejada en ambos manifiestos).

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

## Conector de Atlassian (Confluence) — para `confluence-publish`

La skill `confluence-publish` publica/espeja la documentación de `docs/` en Confluence, y los
agentes `planner`, `evaluator` y `qa` la invocan al escribir en `docs/` (paso "Sincronizar con
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
