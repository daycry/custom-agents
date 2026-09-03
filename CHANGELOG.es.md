# Changelog

[English](CHANGELOG.md) · **Español**

Todos los cambios notables de este proyecto se documentan aquí.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el versionado sigue [SemVer](https://semver.org/lang/es/).

## [Sin publicar]

### Added — iniciativa `parity-core` (2026-09-03)

- **Tiering de modelos configurable en dos capas** ([`ADR-009`](docs/knowledge/adr/)): cada agente declara `model` **y `effort`** (valores oficiales `low|medium|high|xhigh|max`, exigidos por el linter), y `.claude/dev.json` `"modelos": {"<agente>": {...}}` lo sobrescribe por agente. `agent-kits/shared/model-tier.py` resuelve el tier efectivo (frontmatter + config, con `fuente` por campo) y los cuatro orquestadores pasan `model` al Agent tool. Límite declarado con honestidad: el Agent tool no documenta `effort` por invocación, así que esa clave es informativa — solo el del frontmatter es efectivo. `/setup` paso 5-quater lo edita.
- **Agente `architect` + `design.md`**: desde una spec aprobada explora el repo y produce 2-3 opciones con trade-offs, criterios y recomendación; el **orquestador** las presenta por trozos (AskUserQuestion en Cowork, lista numerada en CLI), recoge la elección y re-invoca al agente para fijar `opcion_elegida`, escribir el ADR y pasar `design.md` a `aprobado`. Opt-in desde `/pm-cycle` (tras el go) y `/dev-cycle` Fase 2-a; `planner` lo lee y respeta la opción elegida. Con su propio hook de guardia `PreToolUse` (solo escribe `design.md`, el frontmatter `design:` y `docs/knowledge/adr/`).
- **Skill `tdd`** — fuente única de RED-GREEN-REFACTOR: la ley dura (el código escrito antes de su test se borra y se reescribe tras el rojo), evidencia obligatoria del rojo en el ledger, qué NO es TDD, excepciones declaradas, tabla de racionalización de 8 filas, `references/anti-patterns.md` y `references/by-stack.md` (cómo correr UN solo test rojo en pytest/jest/vitest/phpunit/go). `implementer` y `task-brief.py` la referencian en vez de repetir el método.
- **Agente `reviewer` (solo lectura)** ejecuta cada lente para `adversarial-review` (sin `Write`/`Edit` en `tools`, por construcción), con contrato de salida fijo y degradación a subagente genérico. Más las referencias compartidas `docs-style` (reglas de redacción técnica ES/EN que cargan documenter/analyst/planner/architect) y `plugin-dev/references/claude-code-contracts.md` (cada contrato oficial usado, con URL y fecha de verificación, para que las piezas dejen de re-consultar la doc).

### Added — iniciativa `memory-health` (2026-09-03)

- **`session-journal`** ([`ADR-010`](docs/knowledge/adr/)): un hook `SessionEnd` más `agent-kits/shared/journal.py` escriben una entrada determinista por sesión en `docs/knowledge/journal/` (iniciativa activa, ficheros tocados, tareas que cambiaron de estado, marcadores cerrados del meter), idempotente por `session_id` y reinyectada al arrancar/retomar (≤ 25 líneas). Solo escribe en proyectos que usan el plugin; excluida del espejo de Confluence; las entradas se versionan (opt-out documentado). **Sin resumen por IA**: el contrato oficial de `SessionEnd` ignora la salida de los hooks, y eso queda registrado en vez de fingido.
- **Skill `code-health`** (`code-health.py`): informe agnóstico de lenguaje con cuatro medidas — duplicación por shingles de tokens normalizados con pares `fichero:línea`, tamaño/anidamiento/funciones largas, hotspots (churn de git × tamaño) y TODO/FIXME envejecidos — con MD, `--json` y `--baseline`; el `evaluator` lo usa para pesar el riesgo y el `planner` para abrir tareas de deuda.
- **Skill `dependency-upgrade`** (`deps-inventory.py`): 7 formatos de manifiesto más lockfiles, `outdated` oficial cuando la herramienta está presente (nunca inventa un «latest»), clasificación del salto semver y una spec de actualización redactada para que `evaluator` la presupueste. Delimitada frente a `nemesis` (vulnerabilidades).

### Added — iniciativa `superiority` (2026-09-03)

- **`/doctor`**: diagnóstico determinista y sin efectos de la instalación — herramientas, resolución del plugin, hooks registrados, statusline, configs de `.claude/`, estado del trabajo (marcadores huérfanos, iniciativas activas, última entrada del journal) y versión del plugin sin red — con veredicto ✅/⚠️/❌ y **arreglo sugerido por línea**; MD y `--json`, exit 0/1. `/setup` lo ofrece cuando encuentra config previa.
- **Skill `changelog-sync`**: entradas `[Unreleased]`/`[Sin publicar]` en ambos CHANGELOG derivadas de los ledgers cerrados (un bullet por tarea, categoría por heurística con override `changelog:`), idempotente por slug, `--dry-run`/`--only`/`--check`; `release.py` ejecuta `--check` como aviso en sus precondiciones.
- **Skill `unit-tests`** ([`LES-013`](docs/knowledge/lessons/)): la pirámide de pruebas y `coverage-gate.py` (pytest/jest/vitest/phpunit/go, `--changed-only` mide solo los ficheros del diff, exit 2 antes que inventar un porcentaje). Deliberadamente una **skill compartida que usan `implementer` y `qa`, no un agente nuevo** — la primera aplicación de la regla «un rol, un dueño».
- **Lente D de rendimiento** en `adversarial-review`, condicional como la de seguridad: `review-lens-select.py` detecta patrones N+1, I/O en bucles, `await` dentro de `for` y rutas de repositorio/consulta/caché; configurable con `revision.lenteRendimiento`.
- **Skill `api-contract`**: `openapi-lint.py` valida la estructura de OpenAPI 3.x sin dependencias externas y `--diff` informa de cambios rompedores entre dos versiones; flujo contract-first cableado en `planner` y en la Lente A.

### Changed — iniciativa `roles-and-jira-flow` (2026-09-03)

- **Un rol, un dueño** ([`ADR-011`](docs/knowledge/adr/), matriz en [`docs/agents/ROLES.md`](docs/agents/ROLES.md)): el plugin **retira** piezas por primera vez en lugar de solo añadirlas. `pdfy` se retira (envolvía la skill `to-pdf`, que ya se auto-invoca) y la skill `discovery` se absorbe en `analyst` (ambas prometían «convertir una idea vaga en spec»); las fronteras `qa` ↔ `unit-tests` y `adversarial-review` ↔ `reviewer` quedan escritas. El linter gana un guardarraíl heurístico contra dos piezas que declaren el mismo disparador literal. **9 agentes, 17 skills, 12 comandos.**
- **Ciclo Jira completo, determinista y firmado por agente** ([`LES-014`](docs/knowledge/lessons/)): `jira-flow.py` convierte el ciclo en siete eventos — `arrancar` (→ *En curso*), `implementado` (qué se hizo, evidencia, ficheros, horas medidas), `revision`/`gaps` por intento de revisión, `qa-verde`/`qa-rojo` y `aprobado` (→ *Done*) — devolviendo `ops` ordenadas (etiqueta → transición → comentario → worklog). **Cada comentario lleva el agente que lo escribió** en su primera línea (`> 🤖 [custom-agents · implementer]`) y una etiqueta por agente (`ca-implementer`, `ca-reviewer`, `ca-qa`, `ca-orquestador`) para poder filtrar en Jira por autor. El modelo no redacta comentarios ni compone llamadas: las plantillas son fijas (5 ficheros, 742 bytes; solo se carga la del evento) y la secuencia se describe **una vez**, en la Fase 3 de `/dev-cycle`.
  - **El Done se gana, no se anuncia**: `aprobado` es solo del orquestador y se rechaza (exit 2) sin una sección de revisión sin gaps en el ledger **y** `--qa-verde` (el exit 0 de `qa-gate.py`); `gaps` reabre el issue.
  - **Al implementer se le avisa por su brief**, no por Jira: `task-brief.py` le inyecta los gaps del último intento desde el ledger. Jira es el espejo para el equipo; el ledger sigue siendo la fuente.
  - Idempotente por evento en `jira-state.json` (`--force` para repetir), agrupado por tarea (`--batch` por fase), la imputación de horas sigue delegada en `worklog.py` (tope de jornada y banco intactos), y con Jira desactivado el ciclo entero devuelve `ops: []` en silencio. Coste del ciclo medido y documentado en `docs/observability.md`.

### Added — iniciativa `activation-reliability` (2026-09-03)

- **Evals de comportamiento para cada pieza del plugin (`evals/`).** Una `description` es una promesa de activación; ahora se prueba: 31 ficheros de casos (12 skills · 11 comandos · 8 agentes) con 96 casos — 62 positivos (disparador literal o paráfrasis, artefactos/menciones esperadas) y 34 negativos *vecinos* (mismo vocabulario, otra intención, con la redirección esperada). `evals/check.py` corre en CI de forma estática (esquema, cobertura ≥ 2 positivos + 1 negativo por pieza, ids únicos, disparadores literales presentes de verdad en la description, sin datos corporativos); `evals/run.py` los ejecuta en local en sesiones headless (`claude -p --plugin-dir … --output-format stream-json`, flags verificados contra la referencia oficial de la CLI) sobre una copia de `evals/fixtures/project/`, detecta la activación por las llamadas a las tools `Skill`/`Agent`, clasifica los fallos (`no activó` · `activó sin deber` · `permiso denegado` · `expectativa` · `timeout`) y escribe `evals/reports/<fecha>.json`. Registrado como lección [`LES-011`](docs/knowledge/lessons/).
- **Índice de piezas inyectado al arrancar la sesión** (`agent-kits/shared/skill-index.py` + `hooks/session-context.sh`, el patrón `using-superpowers`): índice determinista y cacheado de ≤ 45 líneas / ≤ 3.500 caracteres con comandos, skills y agentes generado desde los frontmatters, con la regla «antes de cualquier tarea comprueba si aplica una pieza», reinyectado tras la compactación (`startup|resume|compact`). Desactivable con `.claude/dev.json` `"sesion": {"indice": false}`. Los comandos se invocan por `/` **o por descripción**, como las skills — el índice, `CONVENTIONS` y `quick-implement` dejan de afirmar lo contrario.
- **Tablas de racionalización** (fragmento compartido `agent-kits/shared/rationalization-table.md`, patrón «iron law»): 8 filas de *excusa que el modelo se da → por qué no vale → qué hacer en su lugar*, justo antes del DoD/veredicto de `implementer`, `adversarial-review` y `qa`, sustituyendo la prosa equivalente. `lint_plugin.py` avisa cuando una pieza no tiene caso positivo en los evals o su description supera 1.200 caracteres.

### Added — iniciativa `plan-and-diet` (2026-09-03)

- **Dieta de tokens de las tres skills grandes** (progressive disclosure, [`ADR-008`](docs/knowledge/adr/)): `jira-sync` 289 → 149 líneas, `confluence-publish` 432 → 196, `cybersecurity` 976 → 167, moviendo el detalle literal a `skills/<skill>/references/*.md` (12 ficheros nuevos) con una tabla «lee X solo cuando llegues al paso Y» en cada SKILL.md. Cero pérdida verificada párrafo a párrafo (`tests/test_skill_size.py --diet-check <skill> <ref>`); todos los anclajes que citan otras piezas (`Paso 0-ter/7/8/9`, «Qué sube y qué no»…) se conservan. Tope duro de 250 líneas (test) y aviso del linter desde 200.
- **Campo `Verificación` obligatorio por tarea**: la plantilla del planner (y el ledger ligero de la vía rápida) declaran `verificacion: obligatoria` y cada `T-XX` lleva `- **Verificación**: \`<comando>\` → <resultado esperado>` (en línea con `·` o como sub-lista; `lectura: …` para prosa). `ledger-lint.py` convierte el campo ausente o vacío en incoherencia dura solo cuando el ledger lo declara (los 20 ledgers existentes validan byte-idénticos); `task-brief.py` lo inyecta en el brief del subagente (también cuando el campo ya registra una ejecución previa: pide re-ejecutarla); `implementer`/`planner`/Lente A exigen la evidencia.
- **CI headless opcional** (`headless.yml`, `workflow_dispatch` + semanal): con `ANTHROPIC_API_KEY` como `env` del job (los secrets no pueden usarse en `if:`), instala Claude Code, ejecuta un subconjunto barato de evals (`run.py --bare --target …`) y una comprobación de hooks reales sobre el fixture cuya evidencia es el fichero-testigo `.claude/.progress-last` que escribe `progress-line.sh` más el plugin listado en `system/init.plugins`; sin el secret todos los pasos se saltan y un paso guardia falla si alguno corrió. Cierra la verificación «hooks en sesión real» que era manual.

### Added — iniciativa `distribution` (2026-09-03)

- **Exportación portable «solo skills»** (`scripts/export-skills.py --format claude|agents-md|cursor|all`): paquete agnóstico de Claude Code con las 10 skills portables, sus `references/` y scripts Python puros, los 13 fragmentos compartidos que citan, un índice `AGENTS.md` (Codex, Copilot…) y una regla `.cursor/rules/*.mdc`, con las búsquedas `find "$PWD/.claude"` reescritas a `${PORTABLE_ROOT:-.}`, README (ES+EN) con la tabla «qué viaja / qué no / por qué» y un sha256, fichero-marcador dedicado antes de cualquier sobrescritura y `--check`. Determinista (`diff -r` vacío entre ejecuciones); el workflow de Release adjunta `custom-agents-skills-portable-<ver>.zip` reproducible (`SOURCE_DATE_EPOCH`).
- **`release.py` hace ahora TODO el release** (lección [`LES-012`](docs/knowledge/lessons/) — las dos trampas del release v1.15.0): mueve `[Unreleased]`/`[Sin publicar]` a `## [X.Y.Z] - fecha` en ambos CHANGELOG y añade el enlace de la release (aborta con notas vacías salvo `--allow-empty-notes`), rechaza una versión ≤ la actual, un árbol sucio o un tag existente, ejecuta `lint_plugin.py` + `evals/check.py` y comprueba las copias `*.MANUAL-COPY` antes de escribir nada, restaura el bit ejecutable de los `.sh` versionados (`git update-index --chmod=+x`, la trampa de Windows), conserva CRLF y ofrece `--dry-run`/`--check`. El comportamiento por defecto (bump + commit + tag) no cambia.
- Pulido de distribución: `displayName` y 18 keywords en `plugin.json`, `marketplace.json` sincronizado (`tests/test_manifests.py` comprueba que skills/comandos listados == reales, en ambos sentidos); README ES/EN con quickstart de 5 pasos copiables, «¿Qué verás?» y una sección honesta «Comparado con superpowers»; `CONTRIBUTING.md`; issue forms de GitHub + plantilla de PR (`github-templates.MANUAL-COPY/` espejado en `.github/`, vigilado por `tests/test_ci_manual_copy.py`). Los 7 `.sh` legacy de `agent-kits/nemesis` y `agent-kits/qa` recuperan el bit ejecutable.

## [1.15.0] - 2026-09-02

### Added — iniciativa `live-visibility` (2026-09-02)

- **Progreso en vivo mientras corren las tareas.** Nuevo script determinista `agent-kits/shared/progress-report.py` (`line` / `active` / `session`, `--json`) sobre un `parse_ledger()` que ahora expone `ledger-lint.py` (salida de la CLI idéntica byte a byte en todos los ledgers existentes). Tres hooks informativos nuevos en `hooks/hooks.json`: `progress-line.sh` (PostToolUse al editar cualquier `docs/roadmap/*/tasks.md` → `systemMessage` de una línea «📋 <slug> · T-04/12 (33%) · fase 2/4 · en curso: T-05 …», con debounce), `subagent-progress.sh` (SubagentStop → iniciativas activas) y `session-context.sh` (SessionStart `startup|resume|compact` → `additionalContext` con iniciativas activas, tareas abiertas y marcadores huérfanos de usage-meter, para que una sesión retomada o compactada arranque donde dice el ledger). Sin salida cuando no hay nada activo.
- **Statusline opt-in** `statusline/roadmap-statusline.sh` (modelo · coste de sesión · % de contexto · progreso del roadmap), activable desde `/setup` paso 5-bis (default No; nunca pisa una `statusLine` existente). `lint_plugin.py` gana `lint_hooks()` (JSON válido, commands existentes; el bit ejecutable es aviso). Doc ES+EN (`CONVENTIONS`, `FLOWS` §6b, `observability`, READMEs).

### Added — iniciativa `deterministic-guardrails` (2026-09-02)

- **Los guardrails duros del implementer pasan de prosa a un hook PreToolUse con tests.** `agent-kits/shared/guardrail-check.py` (+ wrapper `hooks/implementer-guardrail.sh`) deniega, con una razón de una frase: escrituras bajo `docs/roadmap/**` que no sean `tasks.md` (incl. `testing/**`), bajo `docs/security-scan/**`, escrituras de código estando en `main`/`master`, `git push --force|-f|--force-with-lease|+refspec`, `git branch -D`, salir de la rama de trabajo con `checkout/switch main`, `rm -rf` sobre `/`, `~`, `.git` o `.` — también dentro de `sh -c "…"`/`bash -c`/`eval`, sin falsos positivos en mensajes de commit, `grep` o `echo`. Registrado **solo** en el frontmatter `hooks:` del agente (nunca en `hooks/hooks.json` global: planner/evaluator/analyst escriben en `docs/roadmap/` legítimamente) — registrado como [`ADR-007`](docs/knowledge/adr/). Configurable en `.claude/dev.json` → `"guardrails": false | {"alcance","git","ramaPrincipal"}`; sin python3 nunca bloquea (avisa una vez).
- **`scope-check.py`** compara el diff de la rama (comiteado + sin comitear + sin seguimiento) con los campos `Archivos` del ledger (globs, `(nuevo)`, carpetas; `**/` = cero o más directorios) y hace de puerta de la revisión adversarial: exit 1 devuelve los ficheros fuera de alcance al implementer como gap Important sin gastar revisores. Sustituye el check manual «git diff --stat solo dentro del alcance» del DoD del implementer y de `quick-implement`.
- `lint_plugin.py` valida los campos nativos del frontmatter de agente `skills:` (existe, ⊆ `dependencies.skills`, avisa por encima de 16 KB precargados) y `hooks:` (commands existentes). Convenciones ES+EN: dos clases de hooks — informativos (globales, siempre exit 0) y de guardia (PreToolUse deny, solo con alcance de agente, script+tests, desactivables). `ledger-lint.py` reconoce las filas «Fase única» del resumen (adiós al aviso legacy falso en los ledgers de vía rápida).

### Added — skill `adversarial-review` (2026-09-02)

- **La revisión adversarial de dos lentes pasa a skill reutilizable** (`skills/adversarial-review/`) — fuente única del método que ahora invocan `/dev-cycle` Fase 3 y `quick-implement`, y utilizable a demanda sobre una rama o rango sin ledger («revisa este diff»). Lente A (conformidad con spec/plan/constitución, ✓/✗ por criterio) y Lente B (solo defectos de corrección) conservan sus prompts literales; una **Lente C condicional (seguridad)** corre solo cuando `scripts/review-lens-select.py` detecta rutas sensibles (auth/session/token/secret/crypt/permisos/upload/payment/.env/Dockerfile/workflows, ancladas a token, prosa y `docs/**` excluidos) o líneas añadidas (`eval(`, `os.system`, `innerHTML`, `pickle.loads`, `yaml.load(`, SQL concatenado, claves/tokens…) — configurable en `.claude/dev.json` `"revision": {"lenteSeguridad": "auto|siempre|nunca"}`. Fusión + graduación Critical/Important/Minor, bucle de 3 intentos con traspaso de estado, rebate con evidencia, tabla «Revisión de dos lentes — intento N» en el ledger, promoción de `docs/knowledge/` y comentario en Jira viven en la skill; `commands/dev-cycle.md` pierde 25 líneas y conserva solo lo del orquestador (contador de intentos, worklog `[revisión]` por intento). La lección [`LES-010`](docs/knowledge/lessons/) recoge el porqué (tasa de captura real en 5 iniciativas). La CI (`ci.yml.MANUAL-COPY`) pasa a ejecutar pytest por carpetas, así que las suites nuevas quedan cubiertas.

### Fixed — `debt-cleanup` (2026-09-02)

- Saldadas todas las deudas que habían aceptado las tres iniciativas anteriores: el debounce de `progress-line.sh` es atómico (`flock` + rename; fallback honesto sin `flock`), los títulos de tarea con negrita interior salen limpios, `hooks/hooks.json` pasa a `100644` y el linter avisa de JSON ejecutables; el guardrail del implementer es case-insensitive (Windows) y permite el índice `docs/roadmap/README.md` (`CALIBRATION`/`DRIFT`/`BACKLOG` siguen denegados por diseño — son de comandos); los stems de la Lente C llevan límite (`tokenizer.py`/`helmet.py`/`author.md` ya no disparan) y `.claude/dev.json` `revision.excluir` admite globs que se excluyen de la heurística por ruta (el contenido sigue contando); `/setup` paso 5-ter pregunta `revision.lenteSeguridad` (auto/siempre/nunca); `lint_plugin.py` avisa cuando `ci.yml.MANUAL-COPY` difiere de `.github/workflows/ci.yml` (+ `tests/test_ci_manual_copy.py`) y deja de marcar como genéricos los nombres compuestos de skills. Nueva **suite de shell para hooks** `tests/test_hooks_shell.py` (20 casos: los 3 hooks de progreso, el wrapper de guardia incl. degradación sin python3, los 2 hooks previos y la statusline). `docs/observability.md` (+EN) gana una comprobación manual en 3 pasos de los hooks en una sesión real de Claude Code.

### Changed

- **`jira-granularity` cerrada**: la puerta manual de dry-run (T-08) se ejecutó contra un issue desechable del proyecto de pruebas y verificó las cuatro capacidades del conector (checklist markdown en la descripción vía `editJiraIssue`, varios worklogs por issue, comentario de revisión con la plantilla fija, worklog `[revisión]`). Dos hallazgos, registrados como [`GOT-004`](docs/knowledge/gotchas/) y aplicados a `jira-sync`: la transición de cierre se resuelve por `statusCategory.key == "done"` (nunca por nombre ni id fijo — la transición «Done» aterrizó en un estado localizado), y los issues se crean con **`assignee` explícito** (`me` | `none`, se pregunta una vez y se persiste en `.claude/jira.json`) para que el asignado por defecto del proyecto nunca notifique a un compañero. `docs/atlassian-connector-notes.md` ampliado (markdown en descripción/comentarios/worklogs, escape `\|` en celdas).

## [1.14.1] - 2026-08-20

### Changed

- **Placeholders neutros en todos los ejemplos, para que el repo público no arrastre valores de ningún entorno concreto.** El email de autor de los metadatos del plugin pasa a la identidad noreply de GitHub del mantenedor, y todo ejemplo que nombraba un site de Atlassian, una clave de proyecto Jira, un espacio de Confluence o un proyecto propio se sustituye por marcadores neutros (`PROJ` / `PROJ-59`, `DOCS`, `miapp`, `<usuario que autoriza>`, rutas de código genéricas). Afecta a `skills/jira-sync/SKILL.md` y su plantilla de selector, las plantillas de assets de `skills/confluence-publish` y `confluence.example.json`, `agents/nemesis.md` y su esquema de informe, `agents/documenter.md` con `agent-kits/documenter/taxonomy.md`, y el histórico del roadmap. **Sin cambio de comportamiento**: prompts, scripts y tests quedan intactos en sustancia; solo cambian los valores de ejemplo.

### Docs

- Cerrado el hueco documental de las dos iniciativas de esta versión (política curada de Confluence, memoria técnica `docs/knowledge/`): tabla "Qué te llevas" de `README.md`/`README.es.md` raíz, `CLAUDE.md`, ambos índices de documentación (`docs/README.md`, `docs/en/README.md`), el inventario de fragmentos de `agent-kits/shared/README.md`, y una nota breve de "memoria técnica" en la página de cada agente implicado (`docs/agents/evaluator.md`, `planner.md`, `implementer.md`, `qa.md`, `documenter.md`).

## [1.14.0] - 2026-08-20

### Añadido — iniciativa `knowledge-split` (2026-08-20)

- **Un fichero por entrada para `docs/knowledge/gotchas` y `LESSONS`, igualando el patrón de `adr/`.** Crecimiento previsible, lectura selectiva y colisiones de escritura en paralelo motivan el split: `docs/knowledge/gotchas/<slug>.md` y `docs/knowledge/lessons/<agente>-<slug>.md` sustituyen a los dos ficheros agregados, migrados sin retocar texto ni traza de validación — registrado como [`ADR-006`](docs/knowledge/adr/).
  - **`README.md` pasa a ser el índice de entrada**: cada fila enlaza directo a su fichero en vez de a `gotchas.md`/`LESSONS.md#agente`.
  - **`agent-kits/shared/knowledge-check.md` pasa a lectura SELECTIVA**: leer el índice y abrir solo el fichero de la entrada concreta que toque el área de la tarea — nunca la carpeta entera.
  - **La colisión de FICHERO desaparece para gotchas/lecciones** (como ya le pasaba a `adr/`): solo queda el riesgo de colisión de `id:` del ADR (D4, sigue diferido).
  - **`gotchas.md`/`LESSONS.md` quedan como stub de redirección de ≤5 líneas** (la escritura remota no puede borrar ficheros del disco del usuario); un proyecto recién instalado nunca ve un stub — las carpetas nacen directas.
  - Actualizados todos los escritores (`/retro`, `debug-root-cause`, `qa`) y lectores (`evaluator`, `planner`, `implementer`, `qa`, `documenter`) que citaban las rutas antiguas, además de la regla 10 de `docs/CONVENTIONS.md`, `docs/FLOWS.md` y `docs/INSTALL.md` (+ espejos EN), y un fixture nuevo de test de alcance de Confluence bajo `docs/knowledge/gotchas/`.

### Añadido — extensión `knowledge-ids` (2026-08-20)

- **IDs con nomenclatura ADR para gotchas y lecciones, conservando el agente en el slug.** Extiende el split de un fichero por entrada de `knowledge-split` con numeración secuencial igual al patrón `ADR-NNN`: `docs/knowledge/gotchas/GOT-NNN-<slug>.md` y `docs/knowledge/lessons/LES-NNN-<agente>-<slug>.md`, con `id: GOT-NNN`/`id: LES-NNN` en el frontmatter — los 12 ficheros existentes se movieron con `git mv` (renombrado real, contenido intacto) y se numeraron por orden cronológico (backfill primero, luego por orden del índice). `README.md` muestra el ID en cada fila; los globs de lectura selectiva de `knowledge-check.md` y todo escritor/lector que citaba un patrón de ruta se actualizaron. La nota de colisión de `id:` de `knowledge-write.md` pasa a aplicar a las tres familias (ADR/GOT/LES), misma mitigación (renumerar + declararlo en la retro) — registrado como enmienda a [`ADR-006`](docs/knowledge/adr/).

### Añadido — iniciativa `knowledge-capture` (2026-08-20)

- **Memoria técnica transversal para los agentes del plugin, `docs/knowledge/`.** Generaliza el patrón de bookends de `agents/nemesis.md` (`docs/security-scan/STATE.md`+`MEMORY.md`) en una memoria de proyecto siempre activa (sin opt-in) de decisiones de diseño (ADR), trampas comprobadas (gotchas) y lecciones de proceso — "lo que ya no hay que volver a descubrir".
  - **Dónde vive:** `docs/knowledge/adr/ADR-NNN-<slug>.md` (plantilla `agent-kits/shared/templates/adr.md`), `docs/knowledge/gotchas.md` y `docs/knowledge/LESSONS.md` (agrupado por agente), con un índice manual `README.md` (el índice generado + el linter quedan diferidos hasta que haya evidencia de que hacen falta — más de 15 entradas o una colisión de ID de ADR).
  - **Umbral anti-burocracia:** un ADR solo si la decisión cierra una alternativa real Y (afecta a 2+ piezas o se tomó en una puerta de decisión); un gotcha solo si costó al menos un ciclo de depuración o casi rompió una garantía del producto. Objetivo: 0-2 entradas por iniciativa.
  - **Quién escribe:** `planner`/`implementer` escriben un ADR cuando una decisión de diseño cruza el umbral; `debug-root-cause` escribe un gotcha al cerrar su Fase 4 (causa raíz confirmada); `qa` escribe un gotcha cuando un flaky justificado resulta ser un patrón (2+ ciclos), no un accidente; `/retro` produce ahora una **segunda salida** de aprendizajes técnicos cualitativos, además de su fila numérica en `CALIBRATION.md`.
  - **Bucle de lectura (`agent-kits/shared/knowledge-check.md`):** `evaluator`, `planner`, `implementer`, `qa` y `documenter` leen primero el índice corto y abren solo las entradas de su área (progressive disclosure, protegiendo la inversión de `2026-08-10-token-diet`) — `evaluator` → `LESSONS.md`; `planner` → `adr/`+`LESSONS.md`; `implementer` → `adr/`+`gotchas.md`; `qa` → `gotchas.md`; `documenter` → todo.
  - **Prueba del mecanismo:** las "tres lecciones de la primera calibración real" que vivían hardcodeadas en `agents/evaluator.md` se migraron literalmente a `docs/knowledge/LESSONS.md#evaluator` — el prompt ahora las lee del fichero. Verificado con una evaluación de humo desechable: las tres lecciones se siguen citando y aplicando, leídas del fichero, no del prompt.
  - **Backfill semilla:** los aprendizajes técnicos de los 5 `retro.md` existentes, y las 5 decisiones de diseño de `confluence-policy` como los primeros 5 ADR.
  - Retira la sección "Notas de implementación" de la plantilla `tasks.md` del planner (el registro cualitativo vive ahora en `docs/knowledge/`, no en un cajón de sastre). `docs/knowledge/**` queda explícitamente documentado como publicable por defecto en el alcance de `confluence-publish` (con su propio fixture/test). Nueva regla 10 en `docs/CONVENTIONS.md` (+ espejo EN) y extensión de la matriz disparador→artefacto de `docs/FLOWS.md` (+ espejo EN).

### Añadido — iniciativa `confluence-policy` (2026-08-20)

- **Política explícita de publicación en Confluence, cerrando 5 huecos del circuito publish/pull antes del primer `enabled: true` real.** El espejo tenía un `include: ["**/*.md"]` sin política (solo dos exclusiones): habría publicado el árbol EN duplicado, la doc interna del propio plugin (`docs/examples/`, `docs/agents/`) y las 11 iniciativas completas del roadmap. Ahora el `exclude` por defecto es **curado** (opt-out, decisión D1): fuera `docs/en/**`, `docs/examples/**`, `docs/agents/**`, `docs/**/atlassian-connector-notes.md` y, por iniciativa, el plan y el ledger (`improvement-plan.md`, `tasks.md`, `test-plan.md`) — Confluence guarda la **decisión** (`spec.md`), el **presupuesto** (`evaluation.md`) y el **resultado** (`retro.md`), no el tablero de ejecución.
  - **Disparadores que faltaban, cerrados** (D3): `implementer` ahora sincroniza Confluence **al cerrar cada fase** (ni por tarea ni solo al final) — con una nota explícita de que `tasks.md` en sí queda fuera del espejo por política aunque el disparo ocurra. `/retro`, `/spec-drift` y `/roadmap-brief` aplican ahora el paso opt-in compartido en su cierre, igual que el resto de la cadena.
  - **Evidencias binarias de qa** (D4): `**/testing/**` queda excluido por defecto — el informe de qa embebe capturas que el conector Atlassian no puede adjuntar, y antes se publicaba con las imágenes rotas. El informe queda solo-local; `agents/qa.md` ya no declara `confluence-publish` como dependencia.
  - **Nuevo `confluence-scope.py`** (`skills/confluence-publish/scripts/`, +23 tests): fuente de verdad del alcance, con `--check` (falla con un mensaje que nombra la invariante si falta `docs/security-scan/**` en `exclude`), `--status` (clasifica cada doc en en-alcance/excluido y, dentro de en-alcance, en sincronizado/desactualizado/pendiente contra el manifiesto) y `--stage` (regenera `docs/confluence/` desde cero, byte a byte, de forma idempotente, rehusando tocar un `--out` no vacío salvo que sea un staging propio reconocible, con un fichero de aviso reservado `_STAGING-LEEME.md` — nunca `README.md`, para no poder pisar uno real — que avisa de que es derivada y no se edita a mano). Un traductor de glob a regex propio con soporte de `**` reproduce la semántica de `glob.glob(..., recursive=True)` (`**/x` también matchea cero directorios), en vez de un `fnmatch` ingenuo. Endurecido tras una revisión adversarial (3 huecos críticos, 3 importantes y 2 menores, todos con test de regresión).
  - **Mapeo inverso staged → canónico** expuesto como función pura (`staged_to_canonical`) más un subcomando `--map`, que consume `confluence-pull` para escribir siempre en el fichero **canónico** de `docs/`, nunca en la carpeta generada `docs/confluence/`.
  - `hooks/mark-docs-pending.sh` ignora `docs/confluence/**` para que regenerar el staging no se marque a sí mismo como "pendiente" en bucle.
  - Documentación: sección normativa "qué sube y qué no" en las dos skills de Confluence, matriz disparador→artefacto→¿se publica? cubriendo los 10 disparadores conocidos en `docs/FLOWS.md` (+ espejo EN), y el párrafo de sincronización bidireccional de ambos README reescrito para reflejar la política curada y la carpeta de staging generada.

## [1.13.0] - 2026-08-18

### Añadido

- **Bucle de estimación cerrado con cifras verificadas.** Tras el primer `/retro`, sus hallazgos quedan arreglados en el origen y no solo anotados:
  - **Horas-IA re-derivadas con el ratio calibrado** en los 9 bloques `generacion:` medidos y en todas las filas de resumen de los ledgers (~40 % más bajas — se habían derivado con el default sin calibrar de 300.000). Los tokens no se tocan: son la medición, las horas son el derivado, y el `ratio_usado` de cada bloque dice ahora con qué ratio se calculó, así que la cuenta sigue siendo auditable. Retros y `CALIBRATION.md` reexpresados en consecuencia.
  - **Coste real en €, por fin.** `rates-verify` leyó la página oficial de precios y escribió las tarifas estándar de Claude Opus 4.8 en `.claude/rates.json` ($5/M entrada · $25/M salida · $6,25/M escritura de caché · $0,50/M lecturas): el coste de proceso de las 5 iniciativas medidas es **12,35 €**, en lugar de nueve `eur: null`. Los mismos precios verificados quedan en `rates.example.json` para que un proyecto nuevo arranque con cifras reales. `tipoCambioUsdEur` sigue marcado como **supuesto**, no como dato verificado.
  - **El `evaluator` incorpora las tres lecciones** de la calibración: separar horas humanas equivalentes (valor) de horas-IA (plazo) en vez de mezclarlas; presupuestar el **coste de proceso** como línea propia; y dar su propia línea a la revisión adversarial, dimensionándola por tipo (prosa = minutos · prosa + tests = ×2 · código de producto = horas).
  - **Causa raíz del doble conteo arreglada donde nace:** P0 del `planner` y la plantilla de `tasks.md` explican ahora que la ventana del plan se escribe **idéntica** en los dos ficheros y por qué (el dashboard la deduplica), para que nadie lo "arregle" haciéndolos diferir.
  - `.gitignore`: el estado local (`usage-state.json`, `jira-state.json`, `confluence-state.json`) queda excluido — es estado de máquina, no del proyecto; `rates.json` sí se versiona a propósito. Como `.claude/` es ruta protegida para las herramientas remotas, el fichero se entrega como **`rates.json.MANUAL-COPY`** en la raíz (JSON válido; cópialo a `.claude/rates.json`) — mismo patrón que `ci.yml.MANUAL-COPY`.
  - Los títulos que salen en dashboards publicables (H1 de `spec.md` y `descripcion:`) ya no nombran productos de terceros.
- **Primer `/retro` del proyecto — el bucle de estimación queda cerrado con datos reales.** Nuevo `docs/roadmap/CALIBRATION.md` con una fila por iniciativa medida y un **ratio calibrado de 479.326 tokens/hora** (mediana de 5 muestras), que `usage-meter.py` ya toma en lugar del default sin calibrar de 300.000 — las horas-IA reportadas (y por tanto las que se imputan a Jira) bajan ~40 % y se ajustan al reloj. El fichero documenta la **definición exacta y no circular** del ratio: tokens facturables medidos ÷ tiempo de reloj de las ventanas de medición, nunca las horas que deriva el propio meter, más sus límites conocidos. `retro.md` escrito para las 5 iniciativas con datos medidos (`sdd-hardening`, `workflow-polish`, `plugin-dev`, `subagent-personas`, `quick-implement`), cada uno con estimado vs real, causa y ajuste sugerido, y 4 aprendizajes acumulados.

### Corregido

- `roadmap-dashboard`: una ventana de medición declarada por **dos artefactos** (el `planner` mide `improvement-plan.md` y `tasks.md` juntos y escribe el mismo bloque en ambos, por diseño) se contaba **dos veces** en el «coste de proceso» — `sdd-hardening` mostraba 85.077 tokens en vez de sus 58.914 reales (+44 %), y el total de cartera se inflaba lo mismo. Ahora una medición real idéntica se deduplica (misma ventana, mismos tokens, mismas horas) y la celda lo indica con `ventana compartida`. Dos tests de regresión: la ventana compartida cuenta una vez, y los bloques `estimado` que comparten fechas de referencia pero llevan estimaciones **distintas** por artefacto siguen sumándose (defecto de la primera versión de este mismo fix, que perdía 0,8 h de `coste-generacion`).
- `docs/roadmap/*/spec.md`: el campo `descripcion:` ya no nombra productos de terceros — es el que aparece como título de la iniciativa en dashboards y métricas publicables en Confluence. Los cuerpos conservan su redacción histórica.

## [1.12.0] - 2026-08-13

### Añadido

- **Skill `quick-implement`** — atajo en **lenguaje natural** a la vía rápida de `/dev-cycle`, para cuando el usuario no escribe la barra: los commands solo se disparan con `/`, las skills se auto-invocan por su descripción. Es una puerta de entrada delgada, no un segundo método: resuelve `commands/dev-cycle.md` con `find` y sigue su vía rápida (fuente única: si el método cambia allí, cambia aquí), y para con aviso si no lo encuentra. Nace con el riesgo de secuestro mitigado por diseño: **disparadores negativos** en la descripción (no usarla con incógnitas, multi-fichero, cuando se quiere presupuesto, si el usuario ya escribió `/dev-cycle`, o para un cambio de una línea) más un **filtro de idoneidad obligatorio** como paso 1. Se conservan el ledger, la revisión de dos lentes y `qa-gate`.
- Revisión de dos lentes superada con 10 hallazgos corregidos: un puntero de fases erróneo en la skill (decía «Fase 4 (qa)», pero `qa` va DENTRO de la Fase 3 y la Fase 4 es `documenter` — seguirlo al pie de la letra se habría saltado el `qa-gate` y habría disparado la documentación que la vía rápida deja opt-in), el `find` sin cubrir el caso «trabajar sobre el propio repo del plugin» (ganaba la copia instalada), el protocolo de medición contradiciendo la regla de no-solape, la lista de skills sin actualizar en `plugin.json`/`marketplace.json` ni en la lista en prosa de los README mientras el badge ya decía 11, la falta de actualización de `docs/FLOWS.md` (en los dos idiomas), y duplicación de método aún presente en el paso 2.

### Corregido

- `roadmap-dashboard`: una vía rápida que nace de una **spec de backlog** (y por tanto sí tiene `spec.md`) ahora se detecta por el marcador que declara el propio ledger (`| **Plan** | n/a — vía rápida`) en vez de por la ausencia de spec — antes se clasificaba como «solo spec» y emitía un aviso espurio de «spec `implementada` pero sin improvement-plan.md», que con `--strict` saldría rojo en CI. Corrige también `subagent-personas`, que tenía la misma forma. Test de regresión nuevo.

## [1.11.2] - 2026-08-13

### Corregido

- **Los diagramas Mermaid no renderizaban en GitHub** («Unable to render rich display · Cannot read properties of undefined (reading 'render')»): las etiquetas usaban `\n` como salto de línea, que el renderizador de GitHub no acepta. Los **26 diagramas** del repo (los dos README, `docs/FLOWS.md` ×9, `docs/en/FLOWS.md` ×9, los índices de doc y las docs de los agentes implementer/qa) pasan al `<br/>` portable, verificado renderizándolos todos con mermaid-cli.
- Nueva guarda `tests/test_mermaid_blocks.py`: falla si algún bloque `mermaid` usa `\n` como salto, tiene la fence sin cerrar o no declara tipo de diagrama en su primera línea. Estática y sin dependencias, así que corre en CI.

## [1.11.1] - 2026-08-13

### Añadido — documentación bilingüe EN/ES (2026-08-13)

- **Inglés como idioma principal del repo**: `README.md` reescrito en inglés (mismo escaparate: badges, mermaid de portada, comparativa, quick start) + `README.es.md` con el original en español, con selector de idioma en ambos. Docs clave con espejo inglés en **`docs/en/`**: README (índice), INSTALL, CONVENTIONS (misma numeración §1-§9 — las citas «regla N» siguen valiendo), FLOWS (los 9 diagramas Mermaid con etiquetas traducidas) y observability; selector de idioma también en los originales. Los docs por agente y el roadmap siguen solo en español (anotado en el índice EN). Los tokens que parsean los scripts (estados `borrador/aprobada/…`, `generacion:`, `- **Tipo**:`) se conservan en español también en la doc EN, con glosa la primera vez. Regla de sincronización bilingüe añadida a `CLAUDE.md`.
- README: badge vivo de CI (GitHub Actions) + badge de versión (último tag) y sección «Calidad y CI» con lo que valida cada push.
- README (EN y ES): **panel de badges en tres bloques** — estado (CI · versión · licencia · Python 3.11+), comunidad (estrellas · forks · issues abiertas · último commit · commits/mes) y naturaleza del proyecto (plugin de Claude Code · Spec-Driven · 8 agentes · 11 comandos). Descartado el badge de descargas: GitHub solo cuenta descargas de **assets** de release, no instalaciones por marketplace ni clones, así que no refleja el uso real del plugin.
- Nuevo workflow `release.yml` (copia manual, como ci.yml): al empujar un tag `v*` empaqueta el plugin como zip, crea la GitHub Release y adjunta el zip, con las notas de la versión extraídas automáticamente del CHANGELOG.
- README (EN y ES): **badge de skills** (10) junto a agentes y comandos. Nueva guarda `tests/test_readme_badges.py`: compara cada badge-contador estático con lo que hay de verdad en `agents/`, `skills/` y `commands/`, en los dos idiomas, para que los números no se queden obsoletos en silencio. `ci.yml` pasa a ejecutar las suites del repo en **bucle** (`for t in tests/test_*.py`) en vez de una lista fija, así cualquier suite nueva entra sola en la CI.

### Cambiado — documentación centrada en el propio plugin (2026-08-13)

- **Fuera la comparativa «vs otros plugins»** del README (EN y ES): la sección pasa a ser **«Qué te llevas» / «What you get»**, una tabla de 12 capacidades en positivo con **cómo se garantiza cada una** (script, puerta o agente concreto). La documentación ya no se define por contraste con productos de terceros.
- **Referencias a motores externos, en genérico** en toda la documentación y en los prompts de agentes/skills/kits: «orquestador SDD externo», «motor externo». La interoperabilidad del Modo A de `/dev-cycle` **se mantiene intacta** (el flag sigue funcionando); solo cambia cómo se documenta.

- **CHANGELOG bilingüe**: `CHANGELOG.md` pasa a ser el inglés (y la fuente de las notas de release en GitHub), con `CHANGELOG.es.md` como espejo en español — mismos encabezados de versión, mismo orden, mismos enlaces del pie. `release.py` avisa si a cualquiera de los dos le falta la entrada de la versión que se publica.

### Corregido

- `ci.yml.MANUAL-COPY`: la cabecera de aviso era Markdown (rompía el workflow al copiarla tal cual — YAML inválido en L1); ahora son comentarios `#` y el fichero se copia entero sin editar.

## [1.11.0] - 2026-08-12

### Añadido — iniciativa `sdd-hardening` (2026-08-12)

- **Autosuficiencia total (sin depender de motores externos)**: la **cadena nativa es SIEMPRE el motor por defecto** de `/dev-cycle` (un motor SDD externo solo bajo petición explícita). Nueva config **`.claude/dev.json`** (opt-in, defaults off, la crea `/setup`): `tdd` (RED-GREEN-REFACTOR con **evidencia del rojo** en el ledger), `worktree` (iniciativa en worktree de git aislado, con degradación) y `subagentes` (**cada tarea la implementa un subagente de contexto FRESCO**, con las 4 mecánicas del ciclo de subagentes: brief determinista por el nuevo **`task-brief.py`** (+6 tests), brief-only, estados ricos `DONE/DONE_WITH_CONCERNS/NEEDS_CONTEXT/BLOCKED` y revisor persistente con severidades `Critical/Important/Minor`).
- **Constitución del proyecto consumidor** (`docs/CONSTITUTION.md`, opt-in vía `/setup` con plantilla en el kit shared): principios permanentes que los 6 agentes que escriben leen y citan (`constitution-check.md`), y que la **lente A hace cumplir** (violación de principio explícito = gap con cita de línea). E2E verificado.
- **`/spec-drift`** (nuevo command, solo lectura): deriva spec↔código de las specs `implementada` — subagentes frescos verifican cada criterio contra el código de hoy (`vigente ✓ / derivado ✗ / no verificable` con evidencia) → `docs/roadmap/DRIFT.md` + oferta de `/pm-cycle` para lo derivado. E2E verificado.
- **Criterios Given/When/Then opcionales** (`- [ ] [GWT] CA-XX — Dado…, Cuando…, Entonces…`): plantilla de spec, analyst/discovery los ofrecen para comportamiento observable, qa los traduce 1:1 a E2E, y **`coverage-check.py` los exige** en el test-plan (nuevos tests, incl. GWT sin test-plan = rojo).
- **Skill `debug-root-cause`**: depuración sistemática en 4 fases con evidencia obligatoria (reproducción mínima → aislamiento → hipótesis probada → fix + regresión); `/dev-cycle` la dispara al 3.er rojo de qa ANTES de rendirse — la pregunta al usuario llega con diagnóstico.
- **`docs/observability.md`**: posicionamiento coste (usage-meter) vs actividad en vivo (monitores tipo Agent-Monitor) y coexistencia de hooks verificada.
- Backlog: spec borrador `subagent-personas` (perfiles de dominio para el subagente fresco).
- Revisión adversarial de dos lentes superada en 2 intentos: 21 hallazgos del intento 1 corregidos y verificados 21/21 (incl. parser de briefs tolerante a bloques de código, regex GWT robusto, medición por tarea asignada en el flujo clásico, revisor persistente por traspaso y fix propuesto —no aplicado— en el gancho del 3.er rojo). Suites: 45 tests pytest + 6 suites de repo en verde.

### Añadido — vía rápida `workflow-polish` (2026-08-12)

- **Las 3 disciplinas de flujo que faltaban** (con esto, el repertorio de método queda completo y nativo): (1) **disciplina al RECIBIR la revisión** — el implementador verifica cada gap antes de corregirlo y **rebate con evidencia** los señalamientos erróneos (`descartado (rebatido)` con arbitraje del orquestador; rebatir no consume intento); (2) **despacho PARALELO de tareas independientes** (`subagentes: true`): lotes de máx. 3 en worktrees temporales por tarea, reintegración validada en `feature/<slug>` antes de la revisión, y **medición honesta por lote** (`(medido, lote)`, reparto proporcional); (3) **ritual de CIERRE de rama** en 6 pasos (verificación final, commits por tarea, resumen de PR derivado del ledger, integración preguntando si no está claro, limpieza de worktrees y marcadores, estados finales). Primera vía rápida **medida** del plugin (3m de IA, 16k tokens facturables).

### Añadido — vía rápida `plugin-dev` (2026-08-12)

- **Skill `plugin-dev`** (meta-skill de desarrollo del propio plugin, para TODAS sus piezas): proceso canónico para crear/modificar agentes, skills, comandos, kits y hooks — árbol de decisión de tipo de pieza, reglas de nombre y colisiones, frontmatter obligatorio (model tiering, tools mínimos, `dependencies`), determinismo (scripts con tests + exit codes) y degradación sin bloquear, validación TDD-ish en orden estricto (test primero → `lint_plugin.py` → suites con la misma invocación que la CI → auto-revisión adversarial), obligaciones de documentación por tipo de pieza y catálogo de **anti-patrones vistos en revisiones reales** del repo. Incluye plantillas rellenables de agente, skill y comando (`templates/`) — la de agente verificada empíricamente contra el parser del linter; la de comando con frontmatter `description`/`argument-hint` y `$ARGUMENTS`, como los comandos reales.
- Revisión de dos lentes superada: 7 hallazgos corregidos y re-verificados, 2 de ellos críticos (la invocación de pytest citada no recogía las suites-script de `tests/`; los comentarios inline del template de agente hacían que el linter rechazara cualquier agente creado desde la plantilla). Vía rápida **medida**: 10m de IA, ~49k tokens facturables.

### Añadido — vía rápida `subagent-personas` (2026-08-12)

- **Personas de dominio para el subagente fresco** (cierra la spec de backlog anotada en sdd-hardening): catálogo CORTO de 6 perfiles en `agent-kits/shared/personas/` (`frontend` · `backend` · `db` · `devops` · `test` · `docs` — prioridades, trampas típicas, calidad y evidencia exigibles de cada dominio, ~10 líneas por persona para que el catálogo se mantenga), campo **opcional** `- **Tipo**:` por tarea en la plantilla del planner (se asigna solo con dominio claro; sin tipo → subagente genérico, como hasta ahora) y **inyección determinista en el brief** por `task-brief.py` (sección "Persona de dominio" antes de la tarea). Degradación sin bloquear: etiqueta sin persona en el catálogo → aviso + genérico. TDD estricto (+7 tests, incl. regresión: un `Tipo` de ejemplo dentro de un bloque de código no inyecta persona; tipos con `/` o `..` no escapan del catálogo).
- Revisión de dos lentes superada: 1 defecto real (el `Tipo` dentro de fences, cazado por la lente B ejecutando) + 4 gaps de documentación, todos corregidos y re-verificados.

### Verificación global del roadmap (2026-08-12)

- **Las 9 iniciativas del roadmap auditadas y coherentes**: ledger-lint en verde en todos los `tasks.md`; estados cerrados donde el trabajo estaba publicado (qa-agent y nemesis-sca-iac **reconciliados con nota explícita** — ledgers anteriores a la disciplina de ledger canónico; agent-best-practices, qa-strict y token-diet → `completado`/`implementada`); jira-granularity se mantiene en `en-revision` a propósito (T-08, dry-run contra PROJ, sigue pendiente).
- `roadmap-dashboard`: las iniciativas de **vía rápida** (solo `tasks.md`) ahora aparecen en dashboard y métricas (fase "vía rápida", título desde el ledger, coste medido agregado); los estados con emoji (`completado ✅`) ya no generan falsos avisos de incoherencia. Tests nuevos.

### Corregido

- `ledger-lint.py`: «Fase 3» y «Fase 3-bis» ya no colisionan en la validación del resumen (test de regresión 9/9).

## [1.10.0] - 2026-08-11

### Añadido — iniciativa `coste-generacion`

- **`agent-kits/shared/usage-meter.py`** (+ 35 tests): mide el **coste real de generación** de cada artefacto del ciclo y de cada tarea leyendo los tokens del `usage` de la transcripción de la sesión por ventanas (`start`/`close`/`status` por artefacto, dedupe por respuesta, sidechains incluidas). Convierte a € (`rates.json`, regla de fiabilidad) y a **horas-IA por ratio calibrado** (mediana `tokens/hora` de `CALIBRATION.md` > default no calibrado de `estimation-defaults.md`). Modelo confirmado con el usuario: **fechas = contexto · tokens = medida · horas = tokens × ratio** — nunca reloj de pared. Degrada a `fuente: estimado` sin bloquear jamás el flujo.
- **Bloque `generacion:`** en el frontmatter de spec/evaluation/plan/tasks (plantillas de evaluator y planner + `tasks.md` ligero de la vía rápida); analyst/evaluator/planner y `/dev-cycle` arrancan/cierran el meter (regla de no-solape en los orquestadores).
- **`/roadmap-metrics` — sección "Coste de proceso"**: lo que costó *producir* los artefactos de cada iniciativa (separado del coste de implementación); "sin datos" honesto para artefactos sin bloque, nunca 0 inventado.
- **Medición por tarea (Modo B)**: marcador por `T-XX`; las horas-IA **medidas** entran como "real" en el ledger (`(medido)`) y en el worklog de Jira, sin tocar la aritmética de jornada/banco de `worklog.py`.
- **`/retro` calibra el ratio tokens→hora**: columna `tokens/hora` + línea-resumen "Ratio vigente (mediana de N muestras)" en `CALIBRATION.md`, que consumen evaluator y el meter.
- **Formato humano de duraciones `XhYm`** (estilo Jira, fijado por el usuario: `32m` · `1h 32m` · `18h`): helper único `usage-meter.py fmt`, aplicado en frontmatter, informes y plantilla de revisión (las columnas parseadas por máquina del ledger permanecen en decimal, excepción declarada en la spec).
- Revisión adversarial de dos lentes superada en 2 intentos (22 hallazgos del intento 1 corregidos y verificados 19/19 en el intento 2, incl. parser de calibración con notación `300k`, state corrupto, truncado de transcripciones y "0 tok" inventado).

## [1.9.1] - 2026-08-11

Ajustes sobre la 1.9.0 tras el rodaje de diseño con el usuario: traza por intento en el worklog de revisión y puerta de entrada en `/dev-cycle`.

### Añadido
- **Traza por intento en el worklog de revisión** (`worklog.py --attempt N`, solo con `--kind revision`): cada pasada del bucle reviewer→implementer se imputa como **su propia entrada de worklog** (duración + fecha por intento, comentario `"[revisión] intento N de 3 — T-XX"`), y `jira-state.json` guarda `reviewAttempts: [{intento, fecha, horas}]` para que `/retro` vea cuánto costó cada vuelta. El total sigue siendo la suma (implementación + todas las revisiones); sin `--attempt` el comportamiento es el de 1.9.0. Tests en `tests/test_worklog.py` (13/13). El comentario de Jira sigue siendo único y final ("revisión superada en N intento(s)").
- **Puerta de entrada en `/dev-cycle` (Fase 0-bis):** al arrancar pregunta **flujo completo** vs **vía rápida** — o el usuario lo **indica explícitamente** ("vía rápida"/"rápido"/`rapido`, "flujo completo"/`completo`) y no se pregunta. La vía rápida salta spec/evaluación/plan (crea un `tasks.md` ligero y va directo a `implementer`) pero **conserva** la revisión adversarial de dos lentes y `qa-gate`; el ledger ligero mantiene progreso, horas y volcado a Jira. Para cambios pequeños que se describen en una o dos frases.

### Arreglado
- **CI** (`.github/workflows/ci.yml`): incorpora los tests de 1.9.0 que faltaban por cablear (`test_lint_plugin`, `test_qa_gate`, `test_ledger_lint`) y el paso `lint_plugin.py`. ⚠️ Este fichero hay que copiarlo **a mano** al repo (ruta protegida para las herramientas remotas); el publicado en 1.9.0 seguía corriendo solo dashboard+worklog.

## [1.9.0] - 2026-08-10

Adopción de las mejores prácticas de las colecciones top de agentes (colecciones de referencia y las best practices oficiales de Claude Code), endurecimiento de qa y del orquestador con puertas deterministas, dieta de tokens y granularidad de Jira por fase/tarea con publicación de la revisión. Ver `docs/roadmap/2026-08-10-agent-best-practices/`, `docs/roadmap/2026-08-10-qa-strict/`, `docs/roadmap/2026-08-10-token-diet/` y `docs/roadmap/2026-08-10-jira-granularity/`.

### Añadido (jira-granularity — granularidad + revisión en Jira)
- **Granularidad de volcado elegible** en `jira-sync` (`.claude/jira.json` → `granularidad: "tarea" | "fase"`; defecto `"tarea"`, no rompe instalaciones). **Modo fase**: un issue por Fase con sus `T-XX` como checklist en la descripción; comentario y worklog por tarea sobre el issue de la fase; checklist marcada con `editJiraIssue`; Done de la fase solo cuando todas sus tareas están `completado`.
- **Resultado del revisor → Jira** (`jira-sync` Paso 9, solo Modo B): el revisor de `/dev-cycle` emite salida **estructurada por criterio** (`T-XX` → criterio → ✓/✗); se publica un comentario con el **resultado final + "revisión superada en N intento(s)"** contra la plantilla fija `agent-kits/shared/review-report.template.md`, con la granularidad del volcado. Idempotente (`reviewComentado`).
- **Bucle reviewer→implementer acotado a 3 intentos** en `/dev-cycle` (patrón del bucle qa→implementer): reviewer→corrige→re-review; al 3.º con gaps, para y pregunta.
- **Worklog de revisión** en `worklog.py`: nuevo `--kind implementacion|revision`; la entrada `[revisión]` acumula todas las pasadas del bucle y lleva desglose `worklogImpl`/`worklogRevision` en `jira-state.json` (para `/retro`) sin distorsionar el tope de jornada ni el total del issue. Tests en `tests/test_worklog.py` (12/12).

### Añadido (token-diet — reducción de consumo de tokens)
- **`agent-kits/shared/read-discipline.md`**: disciplina de lectura del recon (grep/glob antes de `Read`, `Read` con `limit`, ignorar `node_modules`/`vendor`/lockfiles/minificados, muestrear patrones). La adoptan documenter, nemesis y evaluator en su recon vía `$SHAREDKIT`.
- **`agent-kits/shared/output-discipline.md`**: disciplina de salida en los handoffs (mensaje final del agente ≤ ~12 líneas, datos y no informe; el detalle vive en los artefactos). La adoptan evaluator, planner, implementer, qa y documenter.
- **Filtrado de payloads Atlassian**: regla en `jira-sync` de pedir `fields` explícitos y acotar `maxResults` en toda llamada al conector (roadmap-live ya lo hacía).
- **Progressive disclosure**: el detalle por-fase de documenter (guía de redacción → `agent-kits/documenter/redaction-guide.md`) y de nemesis (interpretación de tools → `agent-kits/nemesis/interpretation.md`) se lee on-demand al entrar en esa fase, no siempre.
- **Skill `rates-verify`**: consulta la doc oficial de precios (WebFetch) y escribe `precioTokens` + `verificadoEl` en `.claude/rates.json`; nunca inventa precio si no puede leer la doc. Se ofrece en `/setup`; evaluator/planner dejan de marcar `⚠️ verificar` cuando el precio es fiable y reciente.

### Añadido (qa-strict — puertas deterministas)
- **`agent-kits/qa/qa-gate.py`**: el veredicto verde/rojo de qa lo decide un script con exit code sobre `results.json` (0 failed, 0 flaky sin justificar; justificaciones con texto real vía `--justify`). La ausencia de evidencia es rojo. Tests en `tests/test_qa_gate.py` (8/8).
- **`agent-kits/shared/ledger-lint.py`**: validación mecánica del ledger `tasks.md` (vocabulario de estados, `completado` ⟹ criterios marcados, resumen cuadrado, IDs únicos; legacy degrada a aviso). Lo invocan implementer (DoD), qa (P1) y /dev-cycle. Tests en `tests/test_ledger_lint.py` (8/8).
- **`agent-kits/qa/coverage-check.py`**: puerta de cobertura criterios↔tests — referencias rotas del campo «Cubre (tests)» son error; tareas sin cobertura y tests sin referenciar se listan para triage.
- **Hook `hooks/ledger-lint-warn.sh`** (PostToolUse sobre `docs/roadmap/*/tasks.md`): ejecuta ledger-lint en modo aviso en cada edición del ledger; nunca bloquea, sale en silencio sin python3.
- **Playwright estricto** en el runner de qa: `retries: 2` (flaky identificado para el gate), `forbidOnly: true`, timeout configurable por `QA_TIMEOUT_MS`, trazas en fallo.
- **/dev-cycle**: bucle de corrección qa→implementer **acotado a 3 intentos** con contador explícito (al 3.º rojo: parar y preguntar), y revisión adversarial de **dos lentes en paralelo** (conformidad con spec · calidad/robustez) con fusión y dedupe de gaps.
- **Bloques opcionales `API-xx` y `A11Y-xx`** en la plantilla `test-plan.md` (smoke de endpoints con curl; accesibilidad con axe-core bajo opt-in); qa los ejecuta y reporta fuera del umbral del gate en esta iteración.

### Añadido
- **Model tiering** en los 8 agentes: campo `model` proporcional a la complejidad (criterio wshobson) — `pdfy` = haiku; `documenter`/`qa`/`implementer`/`analyst`/`planner` = sonnet; `evaluator`/`nemesis` = opus.
- **Sección `## ANTES DE CERRAR (DoD)`** en los 8 agentes: definition-of-done con comprobaciones ejecutables y obligación de **mostrar evidencia** ("evidence over claims"). `qa` define el umbral «verde» explícito (0 `failed`, 0 `flaky` sin justificar en `results.json`).
- **Revisión adversarial del diff** en `/dev-cycle` (Modo B): un subagente con contexto fresco revisa el diff contra el plan y reporta solo gaps de corrección/requisitos, antes de `qa`.
- **`agent-kits/shared/`**: fragmentos compartidos con fuente única — `estimation-defaults.md` (parámetros de estimación) y `confluence-optin.md` (paso de sincronización) — referenciados por `evaluator`, `planner`, `qa` y `documenter` (DRY).
- **Linter del plugin** `scripts/lint_plugin.py` + tests (`tests/test_lint_plugin.py`), integrado en CI: valida frontmatter (`model`, `tools`, `description`), unicidad de nombres, grafo `dependencies` (skills/kits/agents existen, sin ciclos) y avisa de nombres genéricos con riesgo de colisión en modo copia-directa a `.claude/`.

### Cambiado
- **Descriptions de enrutado** de `evaluator`, `planner` y `nemesis` reescritas con frases-gatillo ("Úsalo cuando…", nemesis con "PROACTIVAMENTE") para mejorar la auto-delegación; el detalle de rutas/plantillas se movió al cuerpo del prompt.
- `evaluator` y `planner` leen los parámetros de estimación del fragmento compartido en vez de duplicar la tabla; `qa`/`documenter` usan el fragmento de opt-in de Confluence.
- Frontmatter de `tools` documentado con el porqué de cada herramienta en los 8 agentes (la restricción de "no tocar código" se mantiene semántica; `pdfy` es el único sin `Edit`).

### Arreglado
- `planner.md`: doble paso «P7» renumerado (P7 Jira / P8 Confluence).
- `nemesis.md`: eliminadas las referencias «§6/§11/§14/§17» a un system base que no viajaba con el plugin.
- Plantillas truncadas completadas: `agent-kits/evaluator/templates/evaluation.md` (sección «Siguiente paso») y `agent-kits/planner/templates/improvement-plan.md` (secciones «Métricas de éxito», «Changelog» y «Siguiente paso»).

## [1.8.0] - 2026-07-17

### Añadido
- **Agente `analyst`** (toma de requerimientos): conversa con el humano eligiendo la técnica (entrevista, ejemplos, user stories, contraejemplos) y produce **siempre** la `spec.md` en formato fijo; itera hasta la aprobación del usuario y hace handoff a `evaluator`.
- **Config compartida de presupuesto `.claude/rates.json`** (tarifa, precio de tokens, tipo de cambio, ratio de supervisión, margen, jornada); la leen `evaluator`, `planner` y `jira-sync`. Plantilla en `agent-kits/evaluator/templates/rates.example.json`.
- **Métricas real vs estimado**: `/roadmap-metrics` + salida `--metrics-md` del generador (producción IA+supervisión, horas humanas y tokens, con desviaciones y total de cartera).
- **`/retro`** (retrospectiva de iniciativa cerrada) → `docs/roadmap/CALIBRATION.md`; el `evaluator` lee ese histórico para **calibrar** futuras estimaciones (bucle de aprendizaje).
- **`/setup`** (onboarding en una pasada: rates + opt-ins de Confluence/Jira).
- **`/roadmap-brief`** (one-pager de cartera a PDF vía `to-pdf`) y **`/roadmap-live`** (estado en vivo desde Jira: issues + horas imputadas por label; artefacto o conversacional).
- **Script `worklog.py`** (kit de `jira-sync`) con tests: cálculo determinista del worklog, tope de jornada **diario** y **banco de horas por issue** (con re-banco); saca la aritmética de la prosa. Modo **dry-run** de primera clase en `jira-sync`.
- **CI** (`.github/workflows/ci.yml`): corre los tests, valida sintaxis Python y JSON, y comprueba coherencia de versión (`release.py --check`). `release.py` avisa si falta la entrada de CHANGELOG.
- **Referencia única del conector Atlassian** (`docs/atlassian-connector-notes.md`) y **tabla de ficheros de config/estado** (regla 9 de `CONVENTIONS.md`).

### Cambiado
- `nemesis`: handoff opcional (F8) para convertir hallazgos High/Critical en iniciativas del roadmap (vía `analyst`/`evaluator`), conectándolo con la cadena.
- `implementer`/`jira-sync`: la imputación de horas usa el script `worklog.py`, no cálculo a mano.

## [1.6.0] - 2026-07-15

### Añadido
- **Skill `jira-sync`**: vuelca un plan (`tasks.md`) a Jira vía el conector Atlassian (Rovo MCP). Se ofrece **al crear el plan** (opt-in en `.claude/jira.json`, como Confluence). Selector de destino **con doble modo**: artefacto interactivo en Cowork/escritorio (`assets/jira-picker.template.html` — busca proyecto, resuelve claves/URLs de issue, busca padre por clave/texto/JQL) y **conversacional** en CLI/VS Code. El **tipo de issue se deriva de la jerarquía del padre** (Épica/Iniciativa → Tarea/Historia; Tarea/Historia → Subtarea; sin padre → Tarea suelta), descubierto vía metadatos, no hardcodeado. Permite **crear una épica nueva** para la iniciativa. Idempotente vía `.claude/jira-state.json`.
- **Imputación automática de horas + cierre en Jira**: al completar cada tarea, `implementer` invoca `jira-sync` para imputar **Tiempo IA (ejec.) + Supervisión** (real→estimación) y transicionar el issue a *Done* (transición descubierta, no fija). **Tope de jornada diario** configurable (`horasJornada`, 8h/7h) con **banco de horas por issue**: al cubrir la jornada pregunta (parar / seguir / banco) y el excedente se imputa en jornadas posteriores, siempre con fecha del día en curso (nunca post-datado).
- **Plantilla `tasks.md` del `planner`** ampliada con **Tiempo IA (ejec.)** y **Supervisión** por tarea (además del tiempo humano), y columnas equivalentes en el resumen de progreso.

### Cambiado
- `planner` (ofrece el volcado al crear el plan) e `implementer` (refleja el progreso) declaran la skill `jira-sync`; `/dev-cycle` lo integra; `/pm-cycle` deja de duplicar el handoff conversacional a Jira.

## [1.5.1] - 2026-07-15

### Añadido
- **`scripts/release.py`**: sube la versión de forma **coherente** en los tres sitios (`plugin.json` y los dos campos de `marketplace.json`), valida que coinciden y crea commit + tag. Evita el fallo de olvidar `marketplace.json` (que deja al cliente sin ver la actualización).
- **Tests del dashboard** (`tests/` con fixtures) y **avisos** en `roadmap-dashboard`: el generador emite por `stderr` cuando no puede leer un campo esperado (posible cambio de etiquetas en las plantillas) o detecta incoherencias de estado, con `--strict` para CI.

### Cambiado
- `docs/INSTALL.md`: aviso de **no ubicar el repo git en carpeta sincronizada en la nube** (OneDrive/Dropbox…) por conflictos de locks/índice, y uso del script de release.

## [1.5.0] - 2026-07-15

### Añadido
- **Rol PM (producto) separado del desarrollo**: command **`/pm-cycle`** (spec → evaluación; cierra en la puerta go/no-go y ofrece handoff a `/dev-cycle`; salidas opt-in: brief PDF y épica en Jira) y **`/pm-backlog`** (prioriza la cartera leyendo todas las `evaluation.md` → `docs/roadmap/BACKLOG.md`).
- **Skill `roadmap-dashboard`** + command **`/roadmap-status`**: escanea `docs/roadmap/*/` y genera un dashboard **HTML** (vista local), **Markdown** (para Confluence) o **JSON** con estado, prioridad y presupuesto por iniciativa.
- **Skill `confluence-pull`** + command **`/confluence-pull`**: sentido **inverso** de la publicación (Confluence → `docs/` local) para PMs sin git; preserva el frontmatter local, avisa de conflictos y confirma antes de escribir. Reutiliza el mapa `.claude/confluence-state.json`.
- **Dashboard del roadmap publicable en Confluence**: `confluence-publish` regenera `dashboard.md` antes de publicar cuando cambia `docs/roadmap/`, para que un PM vea el estado real sin git.

### Cambiado
- Documentación e índices (`CLAUDE.md`, `docs/README.md`) con los nuevos comandos y skills; sincronización con Confluence descrita como **bidireccional**.

## [1.3.1] - 2026-07-10

### Añadido
- **Agente `documenter`**: genera y mantiene la documentación técnica y de producto del proyecto bajo `docs/`, con estructura **derivada del propio proyecto** (no impone nombres de carpeta; deriva del reparto y vocabulario del repo). Cubre índice, RAG-INDEX, arquitectura, stack, unidades del sistema, guías y producto; idempotente; propone estructura y confirma antes de redactar. Se ejecuta **al cerrar el ciclo de un plan** (implementación hecha + pruebas automáticas de `qa` en verde), como handoff de `qa`, **no tarea a tarea**. Incluye kit `agent-kits/documenter` (`taxonomy.md` + plantillas de formato genéricas). Sincroniza los docs en Confluence (opt-in).
- **Agente `implementer`**: implementa un plan aprobado fase a fase (escribe código real del proyecto, sobre rama), marcando `docs/roadmap/<…>/tasks.md` como **ledger canónico** de progreso por tarea; respeta guardrails y hace handoff a `qa`. Es el único agente que modifica código.
- **Command `/dev-cycle <objetivo>`** (`commands/dev-cycle.md`): orquestador que dirige la cadena invocando cada agente por nombre (sin depender de la auto-selección), con puertas de control (go/no-go, OK de plan, verde de qa). Tu `evaluator` y `planner` **siempre** generan los artefactos en `docs/roadmap/` (spec, evaluación, plan, tasks); no se delega la planificación. **Motor externo opcional**: si el usuario lo pide, delega solo la **ejecución** (implementación/TDD/review) trabajando contra tu `tasks.md`; si no, usa la cadena nativa (`implementer` + `qa`). Sin dependencia dura de motores externos.
- **Regla de ledger canónico** (regla 8 de `CONVENTIONS.md` + banner en la plantilla `tasks.md`): el progreso de un plan se registra solo en `tasks.md`; cualquier implementador —incluidos orquestadores SDD externos— debe actualizarlo; los ledgers propios son espejo, no fuente.

### Cambiado
- **Transiciones de estado por fase**: los artefactos ya no se quedan en `borrador`. `/dev-cycle` (y los agentes al ejecutarse sueltos) mueven spec/evaluación/plan/tareas al estado que toca en cada puerta (go → spec `aprobada`/eval `completado`; arranque impl. → plan `en-progreso`; cierre en verde → plan `completado`/spec `implementada`; no-go/cancelación → `cancelado`/`obsoleta`). Mapa en regla 7 de `CONVENTIONS.md`.
- Cadena de trabajo ampliada a `evaluator → planner → implementer → qa → documenter`; `qa` hace handoff a `documenter` con las pruebas en verde.
- Documentación e índices actualizados (`README.md`, `docs/README.md`, `docs/CONVENTIONS.md`, `CLAUDE.md`) con los nuevos agentes, el command y los modos con/sin motor externo.

## [1.3.0] - 2026-07-10

### Añadido
- **Skill compartida `confluence-publish`**: publica/espeja `docs/` en Confluence usando el conector oficial de Atlassian (Rovo MCP), sin integración propia. Asistente guiado para personas no técnicas: conexión → elegir espacio (con búsqueda) → navegar el árbol → elegir destino (raíz del espacio o bajo una página existente) → nombrar la página del proyecto → subir. Idempotente (crea/actualiza, no duplica).
- **Sincronización opt-in** en `planner`, `evaluator` y `qa` (nuevo paso "P7. Sincronizar con Confluence"): al escribir en `docs/`, invocan la skill para reflejar los cambios. La primera vez se pregunta si se quiere sincronizar; la decisión se guarda en `.claude/confluence.json` (`enabled: true/false`) y no se vuelve a preguntar.
- **Navegador de árbol interactivo** (`skills/confluence-publish/assets/tree-browser.template.html`): en Cowork/escritorio expande páginas en vivo vía el conector; al elegir un destino pregunta si usar esa página o crear una hija (con nombre).
- **Fallback conversacional** del paso del árbol para Claude Code CLI y la extensión de VS Code (sin host de artefactos).
- **Detección de cambios sin git**: manifiesto de estado `.claude/confluence-state.json` (hash de contenido + `pageId` por documento); publica solo lo cambiado (crear/actualizar/obsoleto), idempotente e independiente de commits/fechas.
- **Hook `PostToolUse`** (`hooks/hooks.json` + `hooks/mark-docs-pending.sh`): disparador determinista que, al editar bajo `docs/`, deja una marca `.claude/.confluence-pending` (no publica; excluye `docs/security-scan/`). La publicación real la hace la skill.
- Config de ejemplo `skills/confluence-publish/assets/confluence.example.json`.

### Cambiado
- Documentación actualizada (`README.md`, `docs/README.md`, `docs/INSTALL.md`, `CLAUDE.md`): nueva skill, alta del conector Atlassian por entorno (Cowork vs CLI/VS Code), comportamiento opt-in y matriz de compatibilidad.
- Dependencias declaradas de `planner`, `evaluator` y `qa`: añadida la skill `confluence-publish`.

### Seguridad
- `docs/security-scan/**` (datos sensibles del agente `nemesis`) queda **excluido** de la sincronización con Confluence de forma explícita.

### Notas / Limitaciones
- El borrado de un `.md` no elimina la página en Confluence: el conector Atlassian no expone borrado/archivado, así que la página se marca como obsoleta y se lista para borrado manual.
- La sincronización requiere dar de alta el conector de Atlassian una vez por entorno (ver `docs/INSTALL.md`).

## [1.2.0] - anterior

Versiones anteriores a la introducción de este changelog: bundle con los agentes `nemesis`, `evaluator`, `planner`, `pdfy` y `qa`, y las skills compartidas `cybersecurity` y `to-pdf`. Empaquetado como plugin + marketplace.

[1.15.0]: https://github.com/daycry/custom-agents/releases/tag/v1.15.0
[1.14.1]: https://github.com/daycry/custom-agents/releases/tag/v1.14.1
[1.14.0]: https://github.com/daycry/custom-agents/releases/tag/v1.14.0
[1.13.0]: https://github.com/daycry/custom-agents/releases/tag/v1.13.0
[1.12.0]: https://github.com/daycry/custom-agents/releases/tag/v1.12.0
[1.11.2]: https://github.com/daycry/custom-agents/releases/tag/v1.11.2
[1.11.1]: https://github.com/daycry/custom-agents/releases/tag/v1.11.1
[1.11.0]: https://github.com/daycry/custom-agents/releases/tag/v1.11.0
[1.8.0]: https://github.com/daycry/custom-agents/releases/tag/v1.8.0
[1.6.0]: https://github.com/daycry/custom-agents/releases/tag/v1.6.0
[1.5.1]: https://github.com/daycry/custom-agents/releases/tag/v1.5.1
[1.5.0]: https://github.com/daycry/custom-agents/releases/tag/v1.5.0
[1.3.1]: https://github.com/daycry/custom-agents/releases/tag/v1.3.1
[1.3.0]: https://github.com/daycry/custom-agents/releases/tag/v1.3.0
