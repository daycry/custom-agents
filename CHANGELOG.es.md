# Changelog

[English](CHANGELOG.md) · **Español**

Todos los cambios notables de este proyecto se documentan aquí.

El formato sigue [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y el versionado sigue [SemVer](https://semver.org/lang/es/).

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

- **Las 9 iniciativas del roadmap auditadas y coherentes**: ledger-lint en verde en todos los `tasks.md`; estados cerrados donde el trabajo estaba publicado (qa-agent y nemesis-sca-iac **reconciliados con nota explícita** — ledgers anteriores a la disciplina de ledger canónico; agent-best-practices, qa-strict y token-diet → `completado`/`implementada`); jira-granularity se mantiene en `en-revision` a propósito (T-08, dry-run contra DM5985, sigue pendiente).
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

[1.11.2]: https://github.com/daycry/custom-agents/releases/tag/v1.11.2
[1.11.1]: https://github.com/daycry/custom-agents/releases/tag/v1.11.1
[1.11.0]: https://github.com/daycry/custom-agents/releases/tag/v1.11.0
[1.8.0]: https://github.com/daycry/custom-agents/releases/tag/v1.8.0
[1.6.0]: https://github.com/daycry/custom-agents/releases/tag/v1.6.0
[1.5.1]: https://github.com/daycry/custom-agents/releases/tag/v1.5.1
[1.5.0]: https://github.com/daycry/custom-agents/releases/tag/v1.5.0
[1.3.1]: https://github.com/daycry/custom-agents/releases/tag/v1.3.1
[1.3.0]: https://github.com/daycry/custom-agents/releases/tag/v1.3.0
