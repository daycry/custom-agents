---
tasks: roles-and-jira-flow
descripcion: Un rol un dueño + ciclo Jira firmado por agente — (1) matriz de roles `docs/agents/ROLES.md` con los solapes resueltos (`pdfy` retirado, skill `discovery` absorbida por `analyst`, fronteras qa/unit-tests y reviewer/adversarial-review escritas) y guardarraíl heurístico de disparadores duplicados en el linter; (2) `jira-flow.py`: los 7 eventos del ciclo (arrancar · implementado · revision · gaps · aprobado · qa-verde · qa-rojo) como `ops` deterministas (etiqueta → transición → comentario → worklog) con el comentario ya renderizado desde `assets/comment-*.md` y FIRMADO por el agente (`ca-implementer`/`ca-reviewer`/`ca-qa`); (3) cableado en `implementer`, `adversarial-review` y `qa` + tabla única del ciclo en `/dev-cycle` Fase 3 + gaps al `implementer` por su brief (`task-brief.py`); (4) coste del ciclo medido y documentado en `docs/observability.md` (+EN); (5) integración, evals, ADR-011 y LES-014.
estado: completado        # borrador | en-progreso | completado | cancelado
creado: 2026-09-03
actualizado: 2026-09-03
via: rapida               # vía rápida de /dev-cycle: sin spec/evaluación/plan; conserva revisión de dos lentes + suites
verificacion: obligatoria # cada `### T-XX` lleva `- **Verificación**:`; ledger-lint lo exige (exit ≠ 0 si falta)
generacion:
  fuente: estimado        # usage-meter no disponible en este entorno (sandbox cloud)
---

# Checklist de Tareas — roles-and-jira-flow (vía rápida)

| | |
|---|---|
| **Estado** | completado |
| **Fecha** | 2026-09-03 |
| **Plan** | n/a — **vía rápida** (sin spec/evaluación/plan; ledger ligero + revisión de dos lentes + verificación) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del cambio. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador externo— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

> **Decisión del usuario (2026-09-03, literal).** «Organizar los agentes que existen, para que no haya roles duplicados, y asegurar que cuando Jira está configurado se vaya cambiando de estado, el implementer añada comentarios de lo que se hizo, el reviewer añada comentarios de la revisión, y si está bien pase a Done, o que el implementer sea notificado; imputación de horas; que la funcionalidad sea lo más eficiente posible en tokens. En los comentarios deberá ir indicado el agente que lo hizo, para saber quién comentó.» Dos consecuencias de diseño: (a) **un rol, un dueño** — los solapes se resuelven retirando o absorbiendo, no documentando la ambigüedad; (b) **lo determinista no lo redacta el modelo** — el ciclo Jira lo genera un script con plantillas fijas y firma por agente, y la secuencia se describe UNA vez (tabla de la Fase 3 de `/dev-cycle`), no en cada agente.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase única — roles y ciclo Jira | 5 | 5 | 100% | 9,0 / 9,0h | 0,52 / 0,52h | 0,13 / 0,13h | 210k / 210k |
| **TOTAL** | **5** | **5** | **100%** | **9,0 / 9,0h** | **0,52 / 0,52h** | **0,13 / 0,13h** | **210k / 210k** |

---

## Fase única — roles y ciclo Jira

**Estado**: completado · **Estimado**: 9,0h · **Real**: 9,0h (estimado) · **Coste est.**: ≈470 € · **Tokens est.**: 210k

### T-01 — Mapa de roles: una responsabilidad, un dueño

- **Descripción**: `docs/agents/ROLES.md` — matriz **pieza × responsabilidad** (DECIDE / ESCRIBE / LEE / no hace) de los 9 agentes más los 3 orquestadores (`/pm-cycle`, `/dev-cycle` y la skill `adversarial-review`, que orquesta al `reviewer` por lente), con los cuatro solapes resueltos y justificados en `ADR-011`: **(1)** `pdfy` **retirado** — era un envoltorio sin valor añadido de la skill `to-pdf`, que ya se auto-invoca por su `description` (borrados `agents/pdfy.md`, `docs/agents/pdfy.md` y `evals/cases/agent-pdfy.json`; referencias actualizadas en `roadmap-brief`, manifiestos, tabla de tiering y badges → 9 agentes); **(2)** skill `discovery` **absorbida** por `agents/analyst.md` — ambas prometían «convertir una idea vaga en spec» y la skill cerraba una promesa de activación que `/pm-cycle` no cumplía (borrada `skills/discovery/SKILL.md` y su eval; los disparadores pasan a la `description` del `analyst`); **(3)** frontera `qa` (E2E) ↔ skill `unit-tests` (unitarios/integración) escrita para que no nazca duplicada; **(4)** frontera `adversarial-review` (el MÉTODO) ↔ `reviewer` (el EJECUTOR de una lente) explicitada. Además, guardarraíl heurístico `lint_duplicate_triggers` en `scripts/lint_plugin.py`: avisa si dos piezas declaran el mismo disparador literal entrecomillado en su `description`.
- **Estado**: completado
- **Tiempo humano**: est. 3,0h · real 3,0h (estimado)
- **Tiempo IA (ejec.)**: est. 0,18h · real 0,18h (estimado)
- **Supervisión**: est. 0,05h · real 0,05h (estimado)
- **Archivos**: `docs/agents/ROLES.md` (nuevo), `docs/knowledge/adr/ADR-011-un-rol-un-dueno-agentes-retirados-y-responsabilidades-fusionadas.md` (nuevo), `agents/pdfy.md` (borrado), `docs/agents/pdfy.md` (borrado), `evals/cases/agent-pdfy.json` (borrado), `skills/discovery/SKILL.md` (borrado), `evals/cases/skill-discovery.json` (borrado), `agents/analyst.md`, `docs/agents/analyst.md`, `evals/cases/agent-analyst.json`, `commands/roadmap-brief.md`, `commands/pm-cycle.md`, `scripts/lint_plugin.py`, `tests/test_lint_plugin.py`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `docs/knowledge/README.md`, `docs/agents/qa.md` (retirada la mención a `pdfy` en el patrón opt-in de instalación)
- **Verificación** (ejecutada 2026-09-03): `grep -rn "pdfy" --include=*.md --include=*.json . | grep -v docs/roadmap/20 | grep -v CHANGELOG` → solo menciones históricas que explican la retirada (ROLES.md, CONVENTIONS ES/EN, índice de knowledge), 0 referencias vivas · `python3 scripts/lint_plugin.py` → `9 agentes · 0 errores` · `python3 tests/test_lint_plugin.py` → `24/24 OK` (el caso de disparadores duplicados, afinado en T-fix1: acentos plegados y solo la cola de «Úsalo cuando…») · `python3 evals/check.py` → 38 piezas · 0 errores (sin huérfanos tras borrar los dos evals)

**Criterios de aceptación**
- [x] `docs/agents/ROLES.md` lista las 12 piezas (9 agentes + 3 orquestadores) con las cuatro columnas y una fila «no hace» por pieza
- [x] Los cuatro solapes quedan resueltos en el fichero y justificados en `ADR-011` (no solo descritos)
- [x] `pdfy` retirado sin referencias vivas; badges y manifiestos a 9 agentes (`test_manifests`, `test_readme_badges` verdes)
- [x] `discovery` absorbida: sus disparadores están en la `description` del `analyst` y su eval negativo contradictorio retirado
- [x] `lint_duplicate_triggers` avisa con dos piezas que comparten disparador literal, y no avisa en el repo actual (test)

### T-02 — `jira-flow.py`: el ciclo Jira como script determinista y firmado

- **Descripción**: `skills/jira-sync/scripts/jira-flow.py plan --task T-XX --ledger <tasks.md> --event <arrancar|implementado|revision|gaps|aprobado|qa-verde|qa-rojo> --actor <implementer|reviewer|qa> [--batch] [--intento N] [--issue KEY] [--resumen …] [--evidencia …] [--json]`: **no llama al conector** (eso es del agente con las tools MCP) — devuelve el array `ops` en orden fijo (**etiqueta → transición → comentario → worklog**) con todo el trabajo hecho: la transición como destino LÓGICO (`en-curso`/`done`/`reabrir`) más la instrucción de resolverla por `to.statusCategory.key` (GOT-004: nunca por nombre ni id fijo), el **comentario ya renderizado** desde `assets/comment-<evento>.md` con la **firma del agente en la primera línea** (`> 🤖 **[custom-agents · implementer]** · implementador · <fecha>`) y la etiqueta por agente (`ca-implementer`/`ca-reviewer`/`ca-qa`) para filtrar en Jira quién comentó, y el worklog **delegado a `worklog.py`** (comando listo, con las horas del ledger; el tope de jornada y el banco siguen siendo suyos). Idempotencia por clave en `jira-state.json`; agrupación por tarea y, con granularidad `fase`, por fase (`--batch`). **Seis** plantillas fijas: implementado, revisión aprobada, revisión con gaps, **aprobado (cierre)**, qa verde, qa rojo.
- **Estado**: completado
- **Tiempo humano**: est. 3,0h · real 3,0h (estimado)
- **Tiempo IA (ejec.)**: est. 0,18h · real 0,18h (estimado)
- **Supervisión**: est. 0,04h · real 0,04h (estimado)
- **Archivos**: `skills/jira-sync/scripts/jira-flow.py` (nuevo), `skills/jira-sync/scripts/test_jira_flow.py` (nuevo), `skills/jira-sync/assets/comment-implementado.md` (nuevo), `skills/jira-sync/assets/comment-revision-aprobada.md` (nuevo), `skills/jira-sync/assets/comment-revision-gaps.md` (nuevo), `skills/jira-sync/assets/comment-qa-verde.md` (nuevo), `skills/jira-sync/assets/comment-qa-rojo.md` (nuevo), `skills/jira-sync/assets/comment-aprobado.md` (nuevo), `skills/jira-sync/SKILL.md`, `skills/jira-sync/references/config.md`, `skills/jira-sync/references/progress-sync.md`, `skills/jira-sync/references/review-publish.md`
- **Verificación** (ejecutada 2026-09-03; cifras actualizadas en T-fix1): `python3 -m pytest -q skills/jira-sync/scripts` → **42 passed** · `python3 skills/jira-sync/scripts/jira-flow.py plan --task T-01 --ledger docs/roadmap/2026-09-03-superiority/tasks.md --event implementado --actor implementer --json` → `ops` = `etiqueta`(`ca-implementer`) + `comentario` + `worklog`, comentario con primera línea `> 🤖 **[custom-agents · implementer]** · implementador · 2026-09-03` y el comando de `worklog.py` ya compuesto · el mismo con `--event gaps --actor reviewer --intento 1` sobre un ledger sin sección de revisión → `{"error": ["no hay sección `## Revisión de dos lentes — intento 1` en el ledger"]}` (no inventa gaps) · `wc -c skills/jira-sync/assets/comment-*.md` → `1000 total` (**bytes**; 6 plantillas con la de `aprobado`) · los 7 eventos y los 4 caminos de rechazo, con su salida real, en la tabla de la revisión de dos lentes al final de este ledger

**Criterios de aceptación**
- [x] Los 7 eventos devuelven `ops` en orden fijo (etiqueta → transición → comentario → worklog), solo las que aplican al evento
- [x] Todo comentario lleva la firma `[custom-agents · <agente>]` en la primera línea y su etiqueta `ca-<agente>`
- [x] El comentario se renderiza desde `assets/comment-<evento>.md`: el modelo rellena huecos, no redacta
- [x] La transición se expresa como destino lógico + cómo resolverla por `statusCategory` (nunca id fijo)
- [x] El worklog se delega a `worklog.py` (tope de jornada y banco intactos); `[revisión]` por intento
- [x] Idempotente por clave en `jira-state.json`; Jira apagado → `ops: []` y exit 0 sin ruido; ledger sin la tarea → exit 2
- [x] Agrupación: una llamada por evento y tarea; `--batch` agrupa la fase; ningún comentario por paso interno

### T-03 — Cableado del ciclo (agentes + orquestador) y gaps al implementer

- **Descripción**: `agents/implementer.md` dispara `arrancar` al abrir la tarea e `implementado` al cerrarla (qué hizo, evidencia de la verificación, ficheros, horas medidas); `skills/adversarial-review/SKILL.md` dispara `revision` (intento sin gaps) o `gaps` (con la tabla de gaps graduados) **por cada intento**, más el worklog `[revisión] --attempt N`; `agents/qa.md` dispara `qa-verde`/`qa-rojo` con el veredicto de `qa-gate.py`; el paso a **Done** es el evento `aprobado` y **lo dispara el orquestador** (`/dev-cycle`), nunca un agente por su cuenta, cuando coinciden revisión sin gaps y qa verde. La secuencia completa se describe **una sola vez** en la tabla «Ciclo Jira de la Fase 3» de `commands/dev-cycle.md` (evento · cuándo · quién · transición · comentario · worklog); en cada agente queda una línea. **Cómo se entera el `implementer` de los gaps:** `agent-kits/shared/task-brief.py` inyecta en su brief los gaps del ÚLTIMO intento leídos del ledger (grado, gap, corrección sugerida, evidencia) con la disciplina de «verificar antes de corregir, rebatir con evidencia»; el comentario de Jira es el espejo para el equipo, no el canal entre agentes.
- **Estado**: completado
- **Tiempo humano**: est. 1,8h · real 1,8h (estimado)
- **Tiempo IA (ejec.)**: est. 0,10h · real 0,10h (estimado)
- **Supervisión**: est. 0,02h · real 0,02h (estimado)
- **Archivos**: `agents/implementer.md`, `agents/qa.md`, `agents/reviewer.md`, `skills/adversarial-review/SKILL.md`, `commands/dev-cycle.md`, `agent-kits/shared/task-brief.py`, `agent-kits/shared/test_task_brief.py`, `agent-kits/shared/ledger-lint.py` (fuente única de la regex de la cabecera de revisión)
- **Verificación** (ejecutada 2026-09-03): `grep -c "jira-flow" agents/implementer.md agents/qa.md skills/adversarial-review/SKILL.md` → ≥ 1 en cada uno · `grep -n "Ciclo Jira de la Fase 3" commands/dev-cycle.md` → 1 (tabla con los 7 eventos y la columna «quién lo dispara») · `python3 -m pytest -q agent-kits/shared/test_task_brief.py` → **34 passed** (inyección de gaps del último intento; sin sección → nada; y, tras T-fix1, cabecera sin `:` leída igual que en `jira-flow.py` + la regex canónica compartida) · `python3 agent-kits/shared/ledger-lint.py docs/roadmap/2026-09-03-roles-and-jira-flow/tasks.md` → exit 0

**Criterios de aceptación**
- [x] `implementer` dispara `arrancar` e `implementado`; `adversarial-review` `revision`/`gaps` por intento; `qa` `qa-verde`/`qa-rojo`
- [x] `aprobado` (→ Done) lo dispara SOLO el orquestador, con revisión sin gaps **y** qa verde; ningún agente lo hace por su cuenta
- [x] La secuencia está descrita una vez (tabla de la Fase 3), con una línea por agente (token-diet)
- [x] Los gaps llegan al `implementer` por su brief (`task-brief.py`), no por Jira; test de la inyección
- [x] Con Jira desactivado el ciclo es idéntico y no publica nada

### T-04 — Coste del ciclo: medido y documentado

- **Descripción**: sección «Coste del ciclo Jira (por qué lo genera un script)» en `docs/observability.md` (+ espejo EN): tabla ANTES (el modelo redactaba cada comentario releyendo el ledger, y el formato + reglas de transición + worklog vivían repetidos en `implementer`, `qa` y la skill de revisión) / AHORA (script + plantilla del evento; una línea por agente y la tabla única de la Fase 3; `ops` agrupadas). **Medición declarada, no estimada a ojo:** el tamaño de las plantillas está medido (727 caracteres las cinco, ≈ 180 tokens, y solo se carga la del evento) y el script (25 KB) **no entra en el contexto**: se ejecuta. Se declara explícitamente lo que NO se pudo medir aquí (el coste en tokens de una sesión real con Jira en vivo: este repo no tiene el conector en CI) y se da la receta para medirlo en el proyecto del usuario (`usage-meter.py start/close` alrededor del ciclo). Comparación honesta con superpowers: no tiene integración de gestión, así que no hay nada que copiar; lo que se evita es su patrón de *un subagente por tarea* — el ciclo Jira no lanza ningún subagente.
- **Estado**: completado
- **Tiempo humano**: est. 0,7h · real 0,7h (estimado)
- **Tiempo IA (ejec.)**: est. 0,03h · real 0,03h (estimado)
- **Supervisión**: est. 0,01h · real 0,01h (estimado)
- **Archivos**: `docs/observability.md`, `docs/en/observability.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `README.md`, `README.es.md`
- **Verificación** (ejecutada 2026-09-03): `grep -c "Coste del ciclo Jira" docs/observability.md` → 1 y `grep -c "Cost of the Jira cycle" docs/en/observability.md` → 1 (espejo) · `wc -c skills/jira-sync/assets/comment-*.md` → `1000 total` **bytes** (la cifra citada en la doc es la medida y la unidad es la del comando; en T-fix1 se corrigió el «727 chars» citando `wc -c`) · la doc dice explícitamente qué no se midió

**Criterios de aceptación**
- [x] La sección existe en ES y EN con la tabla antes/ahora
- [x] Toda cifra citada está medida con un comando reproducible que aparece en la propia sección
- [x] Se declara lo que no se pudo medir (sesión real con Jira) en vez de inventar una medición
- [x] La comparación con superpowers no atribuye a ese plugin capacidades que no tiene

### T-05 — Integración, evals, memoria y cierre

- **Descripción**: manifiestos (`plugin.json`, `marketplace.json`) y badges a 9 agentes / 17 skills tras las dos retiradas; `README.md`/`README.es.md`, `docs/README.md` (+EN), `docs/INSTALL.md` (+EN), `CLAUDE.md` (tabla de agentes, regla «un rol, un dueño», ciclo Jira), `docs/FLOWS.md` (+EN) con el ciclo de eventos; `scripts/export-skills.py` — el paquete portable arrastra también `assets/` y la cita de las plantillas en el SKILL.md se escribe para que `--check` la resuelva; evals ajustados (`agent-analyst` absorbe los disparadores de discovery y `agent-documenter` retoca su negativo vecino; `skill-jira-sync` **no** gana casos del ciclo a propósito —esta Descripción lo prometía y el diff no lo traía, corregido en T-fix1—: un caso que espere activación por «marca en Jira que terminé T-08» sería una promesa de activación que la `description` de la skill no hace, justo el anti-patrón que ADR-011 retiró con la skill `discovery`); memoria: **ADR-011** (un rol, un dueño) y **LES-014** (los comentarios los firma el agente y los redacta un script) con su fila en el índice; fila de la iniciativa en `docs/roadmap/README.md`.
- **Estado**: completado
- **Tiempo humano**: est. 0,5h · real 0,5h (estimado)
- **Tiempo IA (ejec.)**: est. 0,03h · real 0,03h (estimado)
- **Supervisión**: est. 0,01h · real 0,01h (estimado)
- **Archivos**: `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `README.md`, `README.es.md`, `docs/README.md`, `docs/en/README.md`, `docs/INSTALL.md`, `docs/en/INSTALL.md`, `CLAUDE.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `scripts/export-skills.py`, `evals/cases/agent-analyst.json`, `evals/cases/agent-documenter.json`, `docs/knowledge/lessons/LES-014-jira-sync-comentarios-firmados-por-script.md` (nuevo), `docs/knowledge/README.md`, `docs/roadmap/README.md`, `docs/roadmap/2026-09-03-roles-and-jira-flow/tasks.md`, `tests/test_readme_badges.py`
- **Verificación** (ejecutada 2026-09-03; cifras actualizadas en T-fix1): `python3 -m pytest -q tests agent-kits/shared skills/*/scripts evals` → **530 passed** · `python3 scripts/lint_plugin.py` → `9 agentes · 0 errores · 3 avisos` (los 3 históricos de nombre genérico) · `python3 evals/check.py` → 38 piezas · 129 casos · 0 errores · `python3 -m pytest -q tests/test_manifests.py tests/test_readme_badges.py tests/test_export_skills.py tests/test_skill_size.py` → passed · `python3 agent-kits/shared/skill-index.py --json` → dentro de los topes

**Criterios de aceptación**
- [x] Manifiestos, badges y doc ES/EN coherentes con 9 agentes y las skills reales (`test_manifests`, `test_readme_badges`)
- [x] El paquete portable pasa `--check` con las plantillas nuevas (`test_export_skills`)
- [x] `evals/check.py` en verde sin ficheros huérfanos ni piezas sin casos
- [x] ADR-011 y LES-014 escritos con su fila en `docs/knowledge/README.md`
- [x] Suites completas y linter sin errores

---

## Notas de cierre

- **Retiradas de la iniciativa:** `agents/pdfy.md` (la skill `to-pdf` ya cubría el caso) y `skills/discovery/SKILL.md` (absorbida por `analyst`). Son las dos primeras piezas que el plugin **quita** en vez de añadir: la regla «un rol, un dueño» de `ADR-011` da el criterio para la próxima vez.
- **Frontera con el ledger:** Jira no es nunca el canal de trabajo entre agentes. El `implementer` recibe los gaps por su brief; el comentario `gaps` es el espejo para el equipo humano.
- **Pendiente de ejercitar en vivo:** el ciclo completo contra un Jira real (crear issue → los 7 eventos → Done) no se ha ejecutado en esta sesión; el dry-run del 2026-09-02 ya validó las cuatro capacidades del conector que usa (`editJiraIssue`, comentario con plantilla, varios worklogs, transición por `statusCategory`), así que el riesgo vivo es de integración, no de contrato.

---

## Revisión de dos lentes — intento 1: 12 gaps corregidos (1 Critical, 7 Important, 4 Minor) + 1 hallazgo extra

Revisión adversarial de dos lentes sobre el commit `450b6da`, corregida en el commit `T-fix1`. El resumen recibido hablaba de «1 Critical, 6 Important y 4 Minor», pero la lista traía **12** puntos numerados (los Important eran 7): se verificaron y corrigieron **los 12**. **Ningún gap resultó incorrecto** — los 12 se reprodujeron antes de tocar nada, con el comando y su salida en la columna Evidencia, así que no hay nada `descartado (rebatido)`. Al verificar aparecieron **tres cosas más** de la misma familia («lo declarado no es lo que hay»), corregidas también: la **4.ª** copia de la prosa falsa de `aprobado` (`skills/jira-sync/SKILL.md:110`, va con la fila 1), el «15 skills» de la Descripción de T-05 con 17 reales (fila 8) y la promesa de casos de eval del ciclo que el diff no traía (fila 13, la única que se resuelve corrigiendo la Descripción en vez de añadiendo código).

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Critical | `aprobado` decía dispararlo `qa` en 3 sitios (contra `qa.md:84`, `dev-cycle.md:141` y el criterio T-03 ya marcado) y el script fijaba actor `qa` y emitía la transición a `done` SIEMPRE, sin comprobar nada | T-03 | Actor `orquestador` añadido y ÚNICO válido para `aprobado` (otro → exit 2 nombrando el actor esperado); el evento exige evidencia — última sección de revisión sin gaps pendientes para esas tareas **y** `--qa-verde` (declaración del exit 0 de `qa-gate.py`) — o exit 2 con la razón y `ops: []`; comentario de cierre firmado `[custom-agents · orquestador]` con etiqueta `ca-orquestador`. Prosa corregida en `progress-sync.md`, `review-publish.md`, `implementer.md` y (4.ª copia, hallada al verificar) `jira-sync/SKILL.md` | `test_aprobado_lo_dispara_el_orquestador_con_evidencia_y_cierra_firmando`, `…_con_actor_qa_es_rechazado_diciendo_que_actor_espera`, `…_sin_qa_verde_no_emite_nada`, `…_bloqueado_si_el_ultimo_intento_deja_gaps_pendientes`, `…_sin_seccion_de_revision_en_el_ledger_es_rechazado` · salidas reales abajo (E7, R1, R2) |
| 2 | Important | `gaps` no reabría el issue: `dev-cycle.md:139` y el criterio T-02 prometen transición → *En curso* y el plan no traía ninguna | T-02 | `gaps` emite `transicion` con destino lógico `reabrir` → `statusCategory` `indeterminate`, misma regla GOT-004; `revision` sigue sin transicionar | `test_gaps_reabre_el_issue_a_en_curso`, `test_revision_sin_gaps_no_transiciona` · salida real E4 |
| 3 | Important | Idempotencia inexistente aunque T-02 la marcaba `[x]` (`grep -c idempot jira-flow.py` → **0**): dos ejecuciones del mismo evento daban el mismo plan y publicarían dos comentarios | T-02 | Clave `flow["<issue>\|<evento>\|<tareas>\|<intento>"]` en `jira-state.json`, anotada al generar un plan con `ops`; repetición → `ops: []` + `yaRealizado: true` + exit 0; `--force` repite; estado corrupto o de solo lectura → aviso y sigue | `test_repetir_el_mismo_evento_no_publica_dos_veces`, `test_force_repite_el_evento_a_proposito`, `test_estado_corrupto_degrada_con_aviso_sin_bloquear`, `test_la_clave_de_idempotencia_distingue_intento_y_tareas` · salida real R3 |
| 4 | Important | Jira apagado seguía dando 3 ops: el script no leía `.claude/jira.json` (`grep -c jira.json jira-flow.py` → 0); reproducido con `{"enabled": false}` → `ops: 3` | T-02 | Lee `.claude/jira.json` con la resolución del kit (`--root`, o cwd hacia arriba, como `worklog.py`); `enabled` ≠ `true` → `ops: []`, `jira: "desactivado"`, exit 0 sin ruido. Falla cerrado: sin config tampoco publica | `test_jira_desactivado_no_devuelve_ninguna_op`, `test_sin_config_de_jira_tampoco_publica`, `test_root_resuelve_la_config_desde_otra_carpeta` · salida real R4 |
| 5 | Important | `--intento` caía a 1 en silencio en `revision`/`gaps`: publicaba los gaps del intento 1 con el pie «intento 2 de 3» mientras el brief inyectaba los del 2 | T-02 | Obligatorio en esos dos eventos (exit 2 con la razón); los eventos de `qa`, donde el intento es solo el rótulo, conservan el defecto 1. Se usa SIEMPRE la sección de ESE intento | `test_intento_obligatorio_en_revision_y_gaps`, `test_cada_intento_publica_su_propia_seccion` · salida real E4 y R5 |
| 6 | Important | La op de worklog componía `worklog.py … --issue "<issueKey>"` y `worklog.py` acepta ese literal (exit 0, JSON con `"issue": "<issueKey>"`), así que la op parecía lista para ejecutar | T-02 | Sin issue resuelto NO se emite comando: la op sale `{"tipo":"worklog","pendiente":"issueKey","requiereIssue":true,"instruccion":"…"}` con las horas y qué hacer (volcar el plan, Paso 5) | `test_worklog_sin_issue_no_emite_comando_ejecutable` (incluye `"<issueKey>" not in json.dumps(plan)`) · salida real E2 |
| 7 | Important | `scope-check --base dabdad5` exit 1: `docs/agents/qa.md` cambiado (retirada la mención a `pdfy`) y sin declarar en ningún campo `Archivos` | T-01 | Añadido a los `Archivos` de T-01 con el motivo | `python3 agent-kits/shared/scope-check.py docs/roadmap/2026-09-03-roles-and-jira-flow --base dabdad5` → `57 fichero(s)`, `fuera de alcance (0)`, **exit 0** |
| 8 | Important | Prosa de los README desincronizada: `README.md:25` «Ten agents» y `README.es.md:25` «Diez agentes» con 9 reales (el badge, dos líneas antes, ya decía 9) | T-05 | «Nine agents» / «Nueve agentes»; y `tests/test_readme_badges.py` valida ahora también la PROSA (palabra → número → conteo real, en los dos idiomas) con un mensaje que obliga a actualizar el patrón si se reescribe la frase. Extra hallado al verificar el conteo: la Descripción de T-05 decía «15 skills» con 17 reales → corregido | `python3 tests/test_readme_badges.py` → `10 conteo(s) verificados OK (badges + prosa)`; con «Ten agents» reinyectado a propósito → exit 1 con «la frase dice «Ten agents…» (Ten = 10) pero hay 9 en agents/» |
| 9 | Minor | `docs/observability.md` (+EN) citaba `wc -c` → 727, pero `wc -c` daba **742** bytes (727 eran caracteres) | T-04 | La cifra y el comando casan: `wc -c` → **1000 bytes** (6 plantillas, con la de `aprobado`) y ≈245 tokens; se explica que `wc -c` cuenta bytes, que `wc -m` daría 980 y que además depende del locale (en `POSIX` vuelve a contar bytes). Actualizado el tamaño del script (25 → 41 KB) | `wc -c skills/jira-sync/assets/comment-*.md` → `1000 total`; `LC_ALL=C.UTF-8 wc -m …` → `980`, `LC_ALL=POSIX wc -m …` → `1000` (de ahí que no se cite `wc -m` como cifra principal) |
| 10 | Minor | `jira-flow.py:187` exigía `:` tras el número de intento y `task-brief.py:241` no: una cabecera sin `:` daba brief CON gaps y Jira exit 2 sobre el MISMO ledger | T-03 | Regex extraída a `agent-kits/shared/ledger-lint.py` (`REVISION_HDR_PATTERN`, criterio laxo: `:` y resumen opcionales) y usada por los dos; cada consumidor guarda una copia LITERAL como fallback para el paquete portable, y hay test que compara las cadenas | `test_cabecera_de_intento_sin_dos_puntos_se_parsea_igual`, `test_la_regex_de_cabecera_es_la_canonica_del_kit` (en jira-flow y en task-brief), `test_gaps_cabecera_sin_dos_puntos_se_lee_igual_que_jira_flow` |
| 11 | Minor | `lint_duplicate_triggers` no plegaba acentos («revisión» ≠ «revision») y avisaba por cualquier frase entrecomillada de ≥ 4 caracteres, no solo por disparadores | T-01 | Normaliza acentos y mayúsculas (`unicodedata` NFD) y solo mira las frases de ≥ 3 palabras que van DESPUÉS de «Úsalo/Úsala cuando…» / «Use when…» | `python3 tests/test_lint_plugin.py` → `24/24 OK` (caso 24: par con acento distinto → avisa; cita corta repetida → no avisa; frase larga compartida fuera de la cola de disparadores → no avisa) · `python3 scripts/lint_plugin.py` → `9 agentes · 0 errores · 3 avisos` (sin falsos positivos en el repo) |
| 12 | Minor | T-05 declaraba «`docs/FLOWS.md` (+EN) con el ciclo de eventos» y el diff solo quitaba el nodo `discovery` | T-05 | Añadida la sección **4c** a `docs/FLOWS.md` y `docs/en/FLOWS.md`: tabla evento → quién lo dispara → transición → comentario (etiqueta), diagrama del ciclo completo y el callout de que Done es una puerta. Corregido además el nodo de 4b que aún decía «imputar worklog + issue → Done» (el bug que esta iniciativa arregló) | `grep -c "4c · Jira" docs/FLOWS.md docs/en/FLOWS.md` → 1 y 1; `grep -n "issue → Done" docs/FLOWS.md` → solo en 4c, como destino de `aprobado` |
| 13 | Minor (extra) | Hallado al verificar el 12: la Descripción de T-05 también prometía «`skill-jira-sync` gana casos del ciclo» y `evals/cases/skill-jira-sync.json` no está en el diff (sigue con sus 3 casos) | T-05 | Aquí **no** se añaden casos y se corrige la Descripción: un caso positivo del tipo «marca en Jira que terminé T-08» exigiría una promesa de activación que la `description` de `jira-sync` no hace — es el anti-patrón que ADR-011 retiró con la skill `discovery`. La cita a los evals de la Descripción queda ajustada a lo que el diff hace | `git diff dabdad5 HEAD --stat -- evals/` → solo `agent-analyst.json` y `agent-documenter.json`; `python3 evals/check.py` → `129 casos · 0 errores` (sin huérfanos) |

### Salida real de los 7 eventos y de los 4 caminos de rechazo (T-fix1)

Ejecutado con `--json` sobre ESTE ledger (`--root` a una carpeta con `.claude/jira.json` `{"enabled": true}` y `--state` con `T-01 → CA-101`; este repo no versiona `jira.json`). Resumido a lo que importa:

| id | Comando (abreviado, `plan --ledger tasks.md`) | Salida real (resumen) |
|---|---|---|
| E1 | `--event arrancar --actor implementer --task T-01` | exit 0 · `ops`: `etiqueta`(`ca-implementer`) → `transicion` `objetivo_logico: "en-curso"` / `statuscategory: "indeterminate"` |
| E2 | `--event implementado --actor implementer --task T-01` | exit 0 · `ops`: `etiqueta` → `comentario` (1.ª línea `> 🤖 **[custom-agents · implementer]** · implementador · 2026-09-03`) → `worklog` con `comando` = `worklog.py plan --task T-01 --issue CA-101 --kind implementacion --ia-real 0.18 --ia-est 0.18 --sup-real 0.05 --sup-est 0.05` (horas del ledger, sin `--apply`) |
| E2b | `--event implementado … --task T-03` (no está en el manifiesto de este `--state`) | exit 0 · la op de worklog sale `pendiente: "issueKey"`, `requiereIssue: true`, **sin** `comando`, con `instruccion` y las horas (gap 6) |
| E3 | `--event revision --actor reviewer --task T-01 --intento 2` (ledger fixture de `test_jira_flow.py`, el único con un intento sin gaps) | exit 0 · `ops`: `etiqueta` → `comentario` «intento 2: sin gaps», sin transición |
| E4 | `--event gaps --actor reviewer --task T-01 --intento 1 --ia-real 0.30` | exit 0 · `ops`: `etiqueta` → `transicion` `reabrir` → `comentario` (tabla de los gaps de T-01 del intento 1, pie «intento 2 de 3») → `worklog` `--kind revision --attempt 1` |
| E5 | `--event qa-verde --actor qa --task T-01 --resumen "…" ` | exit 0 · `ops`: `etiqueta`(`ca-qa`) → `comentario` con el resumen y la ruta de evidencias; sin transición ni worklog |
| E6 | `--event qa-rojo --actor qa --task T-01 --resumen "…"` | exit 0 · `ops`: `etiqueta` → `comentario`; sin transición ni worklog |
| E7 | `--event aprobado --actor orquestador --task T-01 --qa-verde` | exit 0 · `ops`: `etiqueta`(`ca-orquestador`) → `transicion` `objetivo_logico: "done"` → `comentario` de cierre: «Puerta de Done: revisión de dos lentes sin gaps pendientes (intento 1) — 12 gaps corregidos (…) — y `qa` en verde (`qa-gate.py` exit 0)» |
| R1 | E7 sin `--qa-verde` | **exit 2** · `{"error": ["`aprobado` sin `--qa-verde`: Done exige el verde de qa. Ejecuta `agent-kits/qa/qa-gate.py` y, SOLO si su exit es 0, repite con `--qa-verde`"], "ops": []}` |
| R2 | E7 con `--actor qa` | **exit 2** · `el evento `aprobado` lo dispara `orquestador`, no `qa` (actor esperado para `aprobado`: `orquestador`)`, `ops: []` |
| R3 | E1 repetido | exit 0 · `ops: []`, `yaRealizado: true`, aviso `evento ya publicado el 2026-09-03 (clave `CA-101\|arrancar\|T-01\|-`): no se repite — usa `--force`` |
| R4 | `--event implementado … --task T-03` con `--root` a una carpeta con `{"enabled": false}` | exit 0 · `ops: []`, `jira: "desactivado"`, aviso `Jira desactivado: `enabled` no es `true` en …/jira.json` |
| R5 | `--event gaps … --task T-01` sin `--intento` | **exit 2** · `el evento `gaps` exige `--intento N`: … no se adivina`, `ops: []` |

**Suites tras el arreglo:** `python3 -m pytest -q tests agent-kits/shared skills/*/scripts evals` (lista del DoD) → **530 passed** (510 antes + 20 tests nuevos: 18 en `test_jira_flow.py` —24 → 42— y 2 en `test_task_brief.py`; `test_lint_plugin.py` y `test_readme_badges.py` crecen dentro de su único test, de 23 a 24 casos y de 8 a 10 conteos) · `python3 scripts/lint_plugin.py` → `9 agentes · 0 errores · 3 avisos` · `python3 evals/check.py` → `38 ficheros · 129 casos · 0 errores` · `python3 agent-kits/shared/ledger-lint.py docs/roadmap/2026-09-03-roles-and-jira-flow/tasks.md` → exit 0 · `scope-check … --base dabdad5` → exit 0.

## Revisión de dos lentes — intento 2: sin gaps

Re-verificación del orquestador con Jira ACTIVADO en un proyecto temporal (`.claude/jira.json` `enabled: true`): `arrancar` → `[etiqueta, transicion]`; `implementado` → `[etiqueta, comentario, worklog]`; `gaps` → `[etiqueta, transicion(reabrir), comentario]`; repetir `arrancar` → `ops: []` con `yaRealizado: true`; `aprobado` sin `--qa-verde` → exit 2 («Done exige el verde de qa…»); `aprobado --actor qa` → exit 2 («lo dispara `orquestador`»). Con Jira desactivado (este repo), los 7 eventos → `ops: []` sin ruido. 530 tests · lint 0 errores · evals 0 errores · `scope-check --base dabdad5` exit 0. ADR-011, LES-013 y LES-014 promovidas a `aceptada (validada: revisión de dos lentes, 2026-09-03, intento 2)`.
