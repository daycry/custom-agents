# Procesos locales, incorporación e instintos — C062, C064–C066, C072

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cinco definiciones completas: **14.073 bytes/473 líneas**. [commands-c3-env-instincts-reading-evidence.json](commands-c3-env-instincts-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

Dos grupos sin relación entre sí: preparar el entorno del proyecto (C062, C064) y
operar los «instintos» de `continuous-learning-v2` (C065, C066, C072). Ninguno abre
destino nuevo.

## C062 — pm2

`6.804 bytes/276 líneas` · frontmatter: solo `description`. Detecta servicios (Vite,
Next, Nuxt, Express, FastAPI, Go), genera `ecosystem.config.cjs`, un envoltorio
Python, ocho comandos `.claude/commands/pm2-*.md`, dos scripts PowerShell y una
sección en el `CLAUDE.md` del proyecto.

- **Intención y disparador:** «configura PM2 para levantar mis servicios».
- **Artefactos y dueño propio:** ninguno; la configuración de procesos es del proyecto.
  En el plugin, `qa` solo necesita la `URL local` del `test-plan.md`
  (`agent-kits/planner/templates/test-plan.md:13`) y el `CLAUDE.md` del consumidor
  solo se toca para **ofrecer** la regla de ledger (`commands/dev-cycle.md:28`).
- **Despacho:** `npm`, `pm2`, Windows Terminal y `pwsh`.
- **Escenario positivo:** «arranca la app y pasa los E2E» → `qa` contra la URL local
  que declara el plan; arrancarla es del proyecto.
- **Escenario negativo:** «genérame los comandos de PM2» → ninguna pieza propia (fuera del bundle).

**Comparación.** [panel-plan-review.md](panel-plan-review.md) ya lo descartó como
panel («gestión de procesos, no de proyectos»). Defectos:

| Defecto | Cita |
|---|---|
| Instala PM2 globalmente sin preguntar | l.15 `npm install -g pm2`; `delivery-practices` no instala servicios globales (`skills/delivery-practices/SKILL.md:18`) |
| Servidor de desarrollo en todas las interfaces | l.103 `uvicorn … --host 0.0.0.0` |
| Rutas de Windows fijas en una detección genérica | l.75 `C:/Program Files/nodejs/node.exe`, l.117 `wt.exe` y `pwsh` |
| Escribe en `CLAUDE.md` (lo crea si falta) y genera comandos que se ejecutan «sin análisis» | l.211, l.218 y l.198 |

**Destino:** **Fuera del bundle.**

## C064 — project-init

`4.246 bytes/86 líneas` · frontmatter: solo `description`. Plan de incorporación del
catálogo en un proyecto: detecta el stack con evidencia, resuelve el plan con
`install-plan.js`, ejecuta un dry-run con `install-apply.js` y pide aprobación antes de
aplicar; el `CLAUDE.md` inicial va aparte y nunca se sustituye sin diff.

- **Artefactos y dueño propio:** instalación → `install/install.mjs` (`--dry-run`
  imprime el plan, l.7 y l.106 del script); configuración → `/setup` (idempotente);
  diagnóstico → `/doctor`; guía de incorporación bajo `docs/` → `documenter`
  (`agent-kits/documenter/templates/onboarding.template.md`, D-103).
- **Despacho:** scripts del repo de origen (`install-plan.js`, `install-apply.js`) y
  `config/project-stack-mappings.json`, que no viajan con el comando.
- **Escenario positivo:** «instala el plugin aquí, pero enséñame antes qué toca» →
  `npx @daycry/custom-agents install --dry-run` según `agent-kits/shared/installation-lifecycle.md`, luego `/setup`.
- **Escenario negativo:** «activa TDD y la statusline» → `/setup`, no el instalador.

**Comparación.** Sus cinco reglas (dry-run por defecto, conservar la guía existente,
instalar por manifiesto, permisos estrechos, informar antes de aplicar) ya están en
`installation-lifecycle.md` (D-088) y la selección por evidencia del repo en
`agent-kits/shared/capability-selection.md` (D-089, enlazada desde `/work-context`).
**Destino:** **Sin destino**: ya integrado (D-088, D-089, D-103).

## C065 — projects

`853 bytes/39 líneas` · frontmatter: `name`, `description` y `command: true`. Lista
el registro global de proyectos (`~/.claude/homunculus/projects.json`) con sus
recuentos de instintos y observaciones, vía `instinct-cli.py projects`.

- **Artefactos y dueño propio:** ninguno escrito. La memoria del plugin es por
  proyecto (`docs/knowledge/`) y su estado lo informa `/doctor`.
- **Despacho:** `instinct-cli.py` (recurso de S054, ya comparado).
- **Escenario positivo:** «¿cómo está la memoria de este proyecto?» → `/doctor`.
- **Escenario negativo:** «lista todos mis proyectos con sus instintos» → ninguna pieza; no hay registro global.

**Comparación.** El detector/registro y el CLI se contrastaron en
[skills-session-learning-memory.md](skills-session-learning-memory.md) (R-bfbbc1c8e8e9,
R-091ff88fa6e3: «no segundo CLI canónico de memoria»). El comando añade una segunda
vía para la misma respuesta: tras el CLI pide leer `projects.json` a mano (l.33).
**Destino:** **Sin destino.**

## C066 — promote

`1.263 bytes/41 líneas` · frontmatter: `name`, `description` y `command: true`.
Promueve instintos de proyecto a ámbito global: uno por ID o, sin argumento, los que
aparecen en al menos dos proyectos con confianza suficiente; `--force` promueve todos
sin preguntar.

- **Artefactos y dueño propio:** conocimiento aprobado → `knowledge-curator`, único
  que aprueba (ADR-018, `docs/agents/ROLES.md:35`); propuesta por repetición →
  `journal.py candidatas` (nace `propuesta`).
- **Despacho:** `instinct-cli.py promote`.
- **Escenario positivo:** «promociona esta lección a conocimiento aprobado» → `knowledge-curator`.
- **Escenario negativo:** «promueve todo lo que se repite en dos proyectos» → ninguna
  promoción automática: `journal.py candidatas` propone y el curador decide.

**Comparación.** Ya resuelto: «repetición no aprueba memoria»
(`docs/agents/ROLES.md:75`) y «Contradicciones resueltas» de
[skills-destinations.md](skills-destinations.md) (una sola vía journal → curador).
Defecto propio del comando: el bloque de ejecución lleva los marcadores literales
`[instinct-id] [--force] [--dry-run]` (l.16, l.22) y no usa `$ARGUMENTS`; que la
opción del usuario llegue depende de que el modelo la sustituya. **Destino:** **Sin destino.**

## C072 — prune

`907 bytes/31 líneas` · frontmatter: `name`, `description` y `command: true`. Borra los
instintos pendientes de más de 30 días que nunca se promovieron.

- **Artefactos y dueño propio:** candidatos pendientes (`docs/knowledge/candidates/pending/`)
  → `knowledge-curator`, que rechaza con motivo; un rechazo es terminal y no se reenvía.
- **Despacho:** `instinct-cli.py prune`.
- **Escenario positivo:** «limpia los candidatos de memoria que nadie revisó» →
  `knowledge-curator` los revisa y rechaza con motivo.
- **Escenario negativo:** «borra lo pendiente de más de 30 días» → ninguna pieza borra por edad.

**Comparación.** La edad no prueba falta de valor; el borrado del CLI actúa sobre todos
los proyectos y usa `mtime` si falta fecha
([skills-session-learning-memory.md](skills-session-learning-memory.md), «Retirada»).
Defecto propio del comando: el uso anuncia `--max-age 60` y `--dry-run` (l.29-30), pero
los dos bloques de ejecución llaman a `prune` sin argumentos ni `$ARGUMENTS` (l.16,
l.22): quien pida `/prune --dry-run` puede acabar ejecutando el borrado real.
**Destino:** **Sin destino.**
