# Comandos de sesión, catálogo, coste y aprendizaje — C001, C002, C004, C006, C010, C018

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Seis definiciones completas: **21.276 bytes/622 líneas**. [commands-c1-session-tools-reading-evidence.json](commands-c1-session-tools-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

Contraste oficial: referencia de comandos de Claude Code
(<https://code.claude.com/docs/en/commands>, consultada el 2026-10-14): `/btw`
(pregunta lateral sin añadirla a la conversación), `/rewind` (alias `/checkpoint`
y `/undo`), `/usage` (alias `/cost` y `/stats`) y `/plugin`.

**Decisiones previas que se respetan.** C001, C004 y C006 ya tienen fila en
[operational-panel-commands.md](operational-panel-commands.md) (líneas 59-61);
C004 además en [commands-session-continuity.md](commands-session-continuity.md)
(líneas 28 y 117). C006 está analizado a fondo con S057 en
[skills-contracts-costs-decisions.md](skills-contracts-costs-decisions.md)
(líneas 129-204) y su destino D-086 está integrado. C010 repite S089
([skills-catalog-self-ops-domains.md](skills-catalog-self-ops-domains.md), 13-23).
C018 es el caller de S054 ([skills-session-learning-memory.md](skills-session-learning-memory.md),
218-227); esa ficha pedía ficha propia en T-05 (línea 323): esta lo cierra.
Aquí solo se añade lo propio de cada comando: despacho, artefactos, dueño,
disparador y escenarios.

## C001 — aside

`5.946 bytes/164 líneas` · tools: no declara (hereda las de la sesión) · model: no declara.
Responde una pregunta lateral sin tocar ficheros, con un formato fijo
(`ASIDE:` … `— Back to task:`), y reanuda la tarea.

- **Artefactos:** ninguno (líneas 37, 160). **Despacho:** ninguno.
- **Disparador:** «/aside ¿esto es thread-safe?» en mitad de una tarea.
- **Escenario +:** pregunta lateral durante `/dev-cycle` → `/btw` nativo; no se activa ninguna pieza propia.
- **Escenario −:** «/aside mejor usamos Redis» → no es lateral; es cambio de
  alcance y vuelve a la puerta del orquestador en curso (`commands/dev-cycle.md:57-58`,
  «una contradicción nueva se comunica y resuelve antes del trabajo afectado»).

**Comparación.** El runtime ya lo resuelve con `/btw`, que además no añade la
respuesta a la conversación; C001 sí la añade y solo promete en prosa que no
escribe (37, 160), sin `allowed-tools` que lo imponga. Sus casos límite útiles
(cambio de dirección con opciones a/b, 85-93; «anota el arreglo, no lo hagas»,
117-123) ya los cubre la regla de `/dev-cycle` citada y la regla de alcance de
`scope-check.py`.

**Destino:** **Fuera del bundle** (nativo `/btw`). Coherente con «ningún comando
persistente nuevo» (operational-panel-commands.md:59).

## C002 — auto-update

`1.935 bytes/28 líneas` · `disable-model-invocation: true` · model: no declara.
Hace pull del repositorio de origen y reinstala los destinos gestionados a partir
del estado de instalación registrado.

- **Artefactos:** los ficheros instalados en las raíces del usuario/proyecto.
  **Dueño propio:** el gestor de plugins del runtime (`/plugin marketplace update`
  + `/plugin update`, `docs/INSTALL.md:141-167`) y el instalador idempotente,
  donde reinstalar es actualizar (`install/install.mjs:12-15`).
- **Despacho:** `node auto-update.js` (401 líneas, listado y no leído) tras
  resolver la raíz con un `node -e` de una línea (14).
- **Disparador:** «actualiza el plugin».
- **Escenario +:** «actualiza custom-agents» → `docs/INSTALL.md` (comandos `/plugin`) o reinstalar con el instalador.
- **Escenario −:** «actualiza las dependencias del proyecto» → `dependency-upgrade`; no se toca el plugin.

**Comparación.** Lo bueno es `disable-model-invocation: true`: solo el usuario
lo dispara. Defectos: la resolución de la raíz (14) toma la primera copia que
encuentra bajo `plugins/cache/<nombre>/<versión>` en el orden de `readdirSync`,
no la versión activa ni la más reciente; y el modo por defecto ejecuta código
recién descargado sin fijar versión ni revisarlo, con `--dry-run` solo como
sugerencia (28). Para el plugin, la versión la fija la release (`release.py`) y
el runtime detecta actualizaciones por número de versión (`docs/INSTALL.md:143`).

**Destino:** **Fuera del bundle.** Sin destino.

## C004 — checkpoint

`1.622 bytes/78 líneas` · tools/model: no declara. `create|verify|list|clear`
de puntos de control con stash o commit y un log propio.

- **Artefactos:** commit o stash, `.claude/checkpoints.log`. **Dueño propio:**
  los commits son del ritual de cierre (un commit por tarea con
  `commit-selection.py`, `commands/dev-cycle.md:494`); las bases verificables
  son la `Verificación` del ledger y la evidencia de `qa` (decisión de
  operational-panel-commands.md:60).
- **Despacho:** `/verify quick` (17), que **no existe** como comando en la
  fuente; es la «dependencia de verificación pendiente» que ya anotó
  commands-session-continuity.md:28, ahora confirmada como rota.
- **Disparador:** «guarda un checkpoint antes de refactorizar».
- **Escenario +:** «deshaz lo que acabas de editar» → `/rewind` nativo; «compara tests y cobertura con el inicio de la rama» → `qa` + `coverage-gate.py --changed-only`.
- **Escenario −:** «haz stash de mis cambios como checkpoint» → ninguna pieza propia hace stash ni commit fuera del ritual.

**Comparación.** Además de lo ya anotado: `git stash` como checkpoint (18) saca
los cambios del árbol de trabajo hasta un `pop` que el comando no hace;
`clear` borra «viejos» sin definir cuáles (78); el estado «behind/ahead» (54)
no se calcula en ningún paso. El nombre choca con el alias nativo `/checkpoint`
de `/rewind`, que sí restaura código y conversación.

**Destino:** **Sin destino nuevo** (decisión previa vigente).

## C006 — cost-report

`4.086 bytes/81 líneas` · `argument-hint: [csv]` · model: no declara. Resume el
log global `~/.claude/metrics/costs.jsonl` por día, modelo y sesión, o lo
exporta a CSV.

- **Artefactos:** ninguno (stdout). **Dueño propio del dato:** `usage-meter.py`
  por artefacto, con procedencia y cobertura (`agent-kits/shared/usage-meter.py:47-52`,
  D-086 integrado); el informe es `/roadmap-metrics`; el coste de sesión, la
  statusline opt-in y `/usage` nativo.
- **Despacho:** un `node -e` en línea; depende de un hook Stop de su repositorio.
- **Disparador:** «¿cuánto llevo gastado?».
- **Escenario +:** «¿cuánto ha costado la iniciativa X?» → `/roadmap-metrics`; «¿y esta sesión?» → `/usage` o la statusline.
- **Escenario −:** «presupuesta esta spec» → `evaluator`; un informe de gasto no estima.

**Comparación.** Todo lo de fondo está en S057. Un defecto propio del comando
que S057 solo nombra («falta zona horaria»): «today/yesterday» salen de
`toISOString()` (45-46), es decir, en UTC; en España un gasto de las 00:30
cae en el día anterior.

**Destino:** **ya integrado** en `usage-meter.py` (D-086). Sin destino nuevo.

## C010 — ecc-guide

`3.166 bytes/93 líneas` · tools/model: no declara. Mapa conversacional del
catálogo leído en vivo, con búsqueda `find:` y consulta por pieza.

- **Artefactos:** ninguno. **Dueño propio:** `/plugin-catalog` (panel con fuentes
  y conflictos), `skill-index.py` (índice al arrancar), `/doctor` (instalación) y
  `/work-context` (selección por tarea).
- **Despacho:** lectura de ficheros y `rg`; `scripts/ci/catalog.js` solo dentro del repositorio de origen (42).
- **Disparador:** «¿qué comando uso para X?», «¿qué incluye el plugin?».
- **Escenario +:** «enséñame qué skills y agentes hay» → `/plugin-catalog`; «qué guías aplican a esta tarea» → `/work-context`.
- **Escenario −:** «¿por qué no salta el hook?» → `/doctor`, no el mapa.

**Comparación.** Repite S089. Su regla 5 (28, no inventar piezas) la hace
cumplir en el plugin el linter de citas. Los cinco comandos que cita como
relacionados (89-93) existen en la fuente.

**Destino:** **Sin destino nuevo** (S089).

## C018 — evolve

`4.521 bytes/178 líneas` · frontmatter con `name` y `command: true` (claves
ajenas al formato de comandos) · model: no declara. Agrupa «instintos» y propone
o genera skills, comandos y agentes.

- **Artefactos:** con `--generate`, ficheros bajo `~/.claude/homunculus/.../evolved/{skills,commands,agents}` (87-89).
  **Dueño propio:** proponer patrones repetidos es de `journal.py candidatas`
  (categorías de D-084 integradas, `agent-kits/shared/journal.py:128-142`) en el
  paso 2-quater de `/retro`; aprobar memoria es de `knowledge-curator`; decidir
  qué pieza nace es la escalera «nada → persona → tool → skill → agente»
  (`docs/SPECIALIZATION.md:90-96`), cuyo comando `/specialize` aún no está
  entregado (`docs/agents/ROLES.md:9-10`); las piezas del propio plugin, `plugin-dev`.
- **Despacho:** `python3 .../continuous-learning-v2/scripts/instinct-cli.py evolve` (14-21).
- **Disparador:** «¿qué patrones se repiten en mis sesiones?», «convierte esto en una skill».
- **Escenario +:** «¿qué lecciones se repiten?» → `journal.py candidatas` en `/retro`, propuestas a `knowledge-curator`.
- **Escenario −:** «genérame un agente debugger con estos pasos» → no; `debug-root-cause` ya es dueño (ADR-011) y una pieza nueva del plugin pasa por `plugin-dev`.

**Comparación.** S054 ya mostró que el agrupado es heurístico y que el agente
generado no lleva las acciones. Lo propio del comando contradice la escalera:
tres instintos con confianza alta bastan para proponer un **agente** (63-75,
85), y su ejemplo genera precisamente un `debugger` que duplicaría una fase con
dueño. La plantilla de agente generado (163-178) no declara `tools`, así que
hereda todas; el plugin exige tools mínimas por agente.

**Destino:** **ya integrado** (D-084 en `journal.py`). Sin destino nuevo.

## Resumen

| ID | Dueño propio | Destino |
|---|---|---|
| C001 | Ninguno; `/btw` nativo | Fuera del bundle |
| C002 | `/plugin update` + instalador | Fuera del bundle |
| C004 | Ritual de commit, ledger, `qa` | Sin destino nuevo (decisión previa) |
| C006 | `usage-meter` + `/roadmap-metrics` | Ya integrado (D-086) |
| C010 | `/plugin-catalog`, `skill-index`, `/doctor`, `/work-context` | Sin destino nuevo (S089) |
| C018 | `journal.py candidatas`, `knowledge-curator`, escalera | Ya integrado (D-084) |
