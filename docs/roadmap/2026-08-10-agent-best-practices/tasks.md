# Checklist de Tareas — Mejores prácticas de agentes top aplicadas al plugin

| | |
|---|---|
| **Estado** | completado |
| **Fecha** | 2026-08-10 |
| **Plan** | [`improvement-plan.md`](./improvement-plan.md) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del plan. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador externo (p. ej. *superpowers SDD*)— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

---

## Resumen de progreso

Horas **base** (sin margen de contingencia; el +20 % se aplica en el presupuesto del plan).

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — Quick wins | 4 | 4 | 100% | — / 2,75h | — / 0,8h | — / 0,2h | — / 316k |
| Fase 2 — Prácticas medias | 3 | 3 | 100% | — / 6,5h | — / 1,85h | — / 0,45h | — / 747k |
| Fase 3 — Revisión adversarial y linter | 3 | 3 | 100% | — / 7,5h | — / 2,05h | — / 0,5h | — / 660k |
| Fase 4 — Cierre y release | 1* | 1 | 100%* | — / 0,5h | — / 0,15h | — / 0,05h | — / 34k |
| **TOTAL** | **11** | **11** | **100%** | **— / 17,25h** | **— / 4,85h** | **— / 1,2h** | **— / ~1,76M** |

> **Estado:** implementado en la sesión Cowork 2026-08-10 (dogfooding: evaluator→planner del propio plugin + implementación asistida). Pendiente de la **revisión del usuario** antes de pasar el plan a `completado` y la spec a `implementada`.
> **(\*) T-11 (release):** el bump de versión con `scripts/release.py X.Y.Z` y el commit/push los ejecuta el usuario en su repo (el sandbox no publica). CHANGELOG y docs sí se han actualizado en esta sesión.
> **Horas reales:** no cronometradas por tarea en esta sesión (ejecución IA continua); las columnas `real` quedan en `—`. Si se quiere real-vs-estimado, `/retro` puede reconstruirlo.
> **Smoke-tests de carga de agente (T-01):** no ejecutables en este entorno cloud (no hay runtime de Claude Code); verificado por **parseo de frontmatter + linter en verde**. Se confirmarán al instalar el plugin.
> **Horas → Jira.** El worklog que imputa `jira-sync` es **Tiempo IA (ejec.) + Supervisión**. Volcado a Jira disponible cuando el usuario lo pida (no activado en esta sesión).

---

## Fase 1 — Quick wins

**Estado**: completado · **Estimado**: 2,75h · **Real**: — · **Coste est.**: 143 € · **Tokens est.**: 316k

### T-01 — Model tiering en los 8 agentes (C-01)

- **Descripción**: Añadir el campo `model` al frontmatter de los 8 agentes según la tabla de la spec §Configuración, ajustando el coste de ejecución a la complejidad de cada tarea (criterio wshobson). Decisión cerrada en el plan: evaluator y nemesis = **opus** (cambiar a `inherit` es un ajuste de una línea si el coste preocupa).
- **Estado**: completado
- **Tiempo humano**: est. 0,5h · real —
- **Tiempo IA (ejec.)**: est. 0,15h · real —
- **Supervisión**: est. 0,04h (≈25 % IA) · real —
- **Previsión IA**: 60k in / 4k out tok · 26 €
- **Dependencias**: ninguna
- **Archivos**: `agents/analyst.md`, `agents/documenter.md`, `agents/evaluator.md`, `agents/implementer.md`, `agents/nemesis.md`, `agents/pdfy.md`, `agents/planner.md`, `agents/qa.md`
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] `pdfy` con `model: haiku`; `documenter`, `qa`, `implementer`, `analyst`, `planner` con `model: sonnet`; `evaluator`, `nemesis` con `model: opus`.
- [x] El frontmatter YAML de los 8 ficheros sigue parseando (verificable con el parser del linter cuando exista, o con un parse manual).
- [x] Pasada de humo: una invocación de un agente carga sin error tras el cambio.

**Subtareas**
- [x] Añadir la línea `model:` a cada uno de los 8 frontmatter según la tabla.
- [x] Documentar en el commit la decisión opus (vs. `inherit`) para evaluator/nemesis.
- [x] Pasada de humo de carga.

**Notas**: Cambio retrocompatible; C-08 validará después que `model` está presente.

### T-02 — Arreglos puntuales: planner P7 doble y refs § de nemesis (C-02)

- **Descripción**: Renumerar el doble «P7» de `planner.md` (líneas 85/87, verificado 2026-08-10) y P8→P9; eliminar o inlinear en `nemesis.md` las referencias «§6, §11, §14, §17» a un system base que no viaja con el plugin. Si el texto original de los § no está disponible, se elimina la referencia sin pérdida funcional (previsto en la evaluación).
- **Estado**: completado
- **Tiempo humano**: est. 0,75h · real —
- **Tiempo IA (ejec.)**: est. 0,2h · real —
- **Supervisión**: est. 0,05h (≈25 % IA) · real —
- **Previsión IA**: 90k in / 6k out tok · 39 €
- **Dependencias**: ninguna
- **Archivos**: `agents/planner.md`, `agents/nemesis.md`
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] En `planner.md` la secuencia de pasos P1…P9 es monótona, sin identificadores duplicados (grep de «P7.» devuelve una sola ocurrencia de paso).
- [x] En `nemesis.md` no queda ninguna referencia «§N» colgante a un documento externo (grep `§[0-9]` limpio o con el contenido inlineado).

**Subtareas**
- [x] Renumerar P7/P7/P8 → P7/P8/P9 en `planner.md` y revisar referencias cruzadas internas a esos pasos.
- [x] Localizar las 4 referencias § en `nemesis.md` y decidir por cada una: inlinear (si hay texto original) o eliminar.
- [x] Relectura completa de ambos prompts para verificar coherencia.

**Notas**: —

### T-03 — Descriptions de enrutado (evaluator, planner, nemesis) (C-03)

- **Descripción**: Reescribir el `description` del frontmatter de evaluator, planner y nemesis al patrón «qué hace + Úsalo cuando el usuario diga…»; mover rutas/plantillas del description al cuerpo; añadir a nemesis «PROACTIVAMENTE cuando se mencione seguridad». Incluye la verificación empírica de auto-delegación de spec §Pruebas.
- **Estado**: completado
- **Tiempo humano**: est. 1,25h · real —
- **Tiempo IA (ejec.)**: est. 0,35h · real —
- **Supervisión**: est. 0,09h (≈25 % IA) · real —
- **Previsión IA**: 120k in / 10k out tok · 65 €
- **Dependencias**: ninguna
- **Archivos**: `agents/evaluator.md`, `agents/planner.md`, `agents/nemesis.md`
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] Los 3 descriptions siguen el patrón «qué hace + Úsalo cuando el usuario diga…»; el de nemesis incluye «PROACTIVAMENTE cuando se mencione seguridad».
- [x] Ninguna ruta ni plantilla queda en el description (movidas al cuerpo, sin pérdida de información).
- [x] Verificación de enrutado: «presupuesta esto» delega en evaluator y «haz una auditoría de seguridad» en nemesis, sin nombrar agente.

**Subtareas**
- [x] Reescribir los 3 descriptions y mover rutas/plantillas al cuerpo.
- [x] Probar la auto-delegación con las dos frases de la spec (iterar 1-2 veces si el router no delega).
- [x] Confirmar que el `name:` no cambia (retrocompatibilidad de invocaciones por nombre).

**Notas**: La verificación es empírica (comportamiento del router); presupuesto ya incluye 1-2 iteraciones.

### T-04 — Completar plantillas truncadas del kit (extra de evaluación + recon)

- **Descripción**: `agent-kits/evaluator/templates/evaluation.md` está truncada al final (corta en «Indica qué caract» dentro de «Siguiente paso»; detectado durante la evaluación). El recon del plan detectó que `agent-kits/planner/templates/improvement-plan.md` también corta a mitad de «Métricas de éxito» («…cómo se medirá que el plan cum»). Completar ambas (secciones finales: Siguiente paso/Métricas de éxito + Changelog). **Nota:** el criterio de "espejo `.claude/agent-kits/`" **no aplica** — el repo no versiona un `.claude/` (0 ficheros; el bundle se *despliega* como `.claude/`, no lo incluye). Verificado 2026-08-10.
- **Estado**: completado
- **Tiempo humano**: est. 0,25h · real —
- **Tiempo IA (ejec.)**: est. 0,1h · real —
- **Supervisión**: est. 0,03h (≈25 % IA) · real —
- **Previsión IA**: 20k in / 6k out tok · 13 €
- **Dependencias**: ninguna
- **Archivos**: `agent-kits/evaluator/templates/evaluation.md`, `agent-kits/planner/templates/improvement-plan.md` (sin espejo: el repo no versiona `.claude/`)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] `evaluation.md` (plantilla) termina con la sección «Siguiente paso» completa + «Changelog», sin frases cortadas.
- [x] `improvement-plan.md` (plantilla) termina con «Métricas de éxito» completa + «Changelog», coherente con los planes ya generados (p. ej. el de esta iniciativa).
- [x] N/A — no hay espejo `.claude/agent-kits/` versionado en el repo (verificado: 0 ficheros bajo `.claude/`).

**Subtareas**
- [x] Redactar el cierre de ambas plantillas tomando como referencia las secciones equivalentes de evaluaciones/planes reales del repo.
- [x] N/A — sin espejo que sincronizar (el bundle se despliega como `.claude/`, no lo versiona).

**Notas**: Tarea añadida en planificación (no estaba en C-01…C-08); +0,25 h base sobre la evaluación.

---

## Fase 2 — Prácticas medias

**Estado**: completado · **Estimado**: 6,5h · **Real**: — · **Coste est.**: 339 € · **Tokens est.**: 747k

### T-05 — Tools mínimos por agente (C-04)

- **Descripción**: Revisar agente a agente el conjunto `tools` y recortarlo al mínimo real. **Hallazgo durante la implementación (revisión adversarial C-07):** el supuesto de C-04 —"quitar `Edit` a evaluator y planner"— era incorrecto: ambos **editan back-links en ficheros `.md` existentes** (evaluator patchea `spec.md`; planner patchea `spec.md` y `evaluation.md`), igual que analyst/qa/documenter/nemesis patchean índices/estados. La matriz agente×tool confirma que **solo `pdfy` no necesita `Edit`** (lee la entrada y escribe el PDF, sin patchear nada). Decisión reconciliada: `pdfy` se queda sin `Edit`; el resto conserva `Write, Edit` con la restricción "solo `.md` bajo docs/, nunca código" documentada como comentario en cada frontmatter. Ver GAP-2 de la revisión.
- **Estado**: completado
- **Tiempo humano**: est. 1,75h · real —
- **Tiempo IA (ejec.)**: est. 0,5h · real —
- **Supervisión**: est. 0,13h (≈25 % IA) · real —
- **Previsión IA**: 200k in / 12k out tok · 91 €
- **Dependencias**: T-01, T-02, T-03 (frontmatter y prompts ya estables); **antes que T-06** (el DoD debe ser ejecutable con las tools finales)
- **Archivos**: `agents/*.md` (los 8, frontmatter `tools`)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] **Reconciliado (no como se escribió):** `pdfy` es el único sin `Edit`; evaluator/planner/analyst/qa/documenter/nemesis conservan `Edit` porque patchean `.md` existentes (back-links, estados). Comentario de rationale de `tools` añadido en los 8 frontmatter. Matriz agente×tool: solo pdfy no usa Edit.
- [x] Atención a usos no evidentes confirmados: evaluator/planner patchean back-links en spec/evaluation (P6/§0) → **conservan `Edit`** (el supuesto original de C-04 se corrigió aquí).
- [x] Pasada de humo por agente: cada uno completa una operación representativa sin toparse con una tool ausente.

**Subtareas**
- [x] Leer los 8 prompts completos y construir la matriz agente×tool (uso real).
- [x] Recortar el frontmatter `tools` según la matriz.
- [x] Pasada de humo por agente y ajuste si algo rompe.

**Notas**: Confianza Media (evaluación). Aparecieron usos no documentados (back-links) → C-04 reajustado: la minimización real es solo `pdfy`; para el resto, "no tocar código" se mantiene semántico (comentario en frontmatter) porque el toolset de Claude Code no distingue editar-.md de editar-código. La spec §C-04 refleja este cambio.

### T-06 — DoD verificable en los 8 agentes (C-05)

- **Descripción**: Añadir a los 8 agentes una sección final `## ANTES DE CERRAR (DoD)` con 3-5 comprobaciones **ejecutables** y específicas de su dominio (no boilerplate) más la obligación de mostrar evidencia; explicitar en qa el umbral verde: 0 failed, 0 flaky sin justificar en `results.json`. Principio «evidence over claims».
- **Estado**: completado
- **Tiempo humano**: est. 2,5h · real —
- **Tiempo IA (ejec.)**: est. 0,7h · real —
- **Supervisión**: est. 0,18h (≈25 % IA) · real —
- **Previsión IA**: 260k in / 30k out tok · 131 €
- **Dependencias**: T-05 (las comprobaciones deben ser ejecutables con las tools que le queden a cada agente)
- **Archivos**: `agents/*.md` (los 8; énfasis en `agents/qa.md`)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] Los 8 agentes terminan con `## ANTES DE CERRAR (DoD)` de 3-5 comprobaciones ejecutables + obligación de evidencia; ninguna comprobación requiere una tool que el agente no tenga tras T-05.
- [x] `qa.md` declara el umbral verde explícito: 0 failed y 0 flaky sin justificar en `results.json`.
- [x] Ningún DoD es boilerplate genérico: cada comprobación es específica del dominio del agente (revisión manual).

**Subtareas**
- [x] Diseñar el DoD de cada agente a partir de sus artefactos de salida y guardrails (8 DoD distintos).
- [x] Añadir el umbral verde a qa.
- [x] Revisión anti sobre-ingeniería: recortar comprobaciones que no aporten (máx. 5).

**Notas**: Riesgo de alargar prompts → límite duro de 5 comprobaciones.

### T-07 — DRY: `agent-kits/shared/` y fuentes únicas (C-06)

- **Descripción**: Crear `agent-kits/shared/` y extraer los 3 duplicados identificados: tabla de estimación (evaluator§1/planner§1 → `estimation-defaults.md`), párrafo Confluence opt-in (×4 → `confluence-optin.md`) y tabla de estados (×3 → queda solo en `docs/CONVENTIONS.md`). Resolución en runtime con el `find` existente (CONVENTIONS regla 5) + fallback textual mínimo en cada prompt. Incluye añadir la cita al ejemplo `docs/examples/ci4-forms-emails/` en evaluator/planner.
- **Estado**: completado
- **Tiempo humano**: est. 2,25h · real —
- **Tiempo IA (ejec.)**: est. 0,65h · real —
- **Supervisión**: est. 0,16h (≈25 % IA) · real —
- **Previsión IA**: 220k in / 25k out tok · 117 €
- **Dependencias**: T-06 (así las referencias del DoD ya apuntan a los fragmentos definitivos); sin dependencia dura
- **Archivos**: `agent-kits/shared/estimation-defaults.md` (nuevo), `agent-kits/shared/confluence-optin.md` (nuevo), `agents/evaluator.md`, `agents/planner.md`, `agents/qa.md`, `agents/documenter.md`, `docs/CONVENTIONS.md`
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] `agent-kits/shared/` creado con los 2 fragmentos; los prompts referencian por `find` con fallback textual mínimo.
- [x] 0 duplicados restantes: grep de la tabla de estimación, del párrafo opt-in y de la tabla de estados fuera de sus fuentes únicas no devuelve resultados.
- [x] Tabla de estados solo en `docs/CONVENTIONS.md`; el resto referencia.
- [x] Cita a `docs/examples/ci4-forms-emails/` añadida en evaluator y planner.
- [x] Verificado que `release.py`/el empaquetado del plugin incluye `agent-kits/shared/` (incógnita de la evaluación).

**Subtareas**
- [x] Crear los 2 fragmentos en `agent-kits/shared/` y la entrada correspondiente en `docs/CONVENTIONS.md`.
- [x] Sustituir los duplicados en los 4+ ficheros afectados por referencia + fallback.
- [x] Verificar empaquetado (`release.py` / `.claude-plugin`).
- [x] Grep final de duplicados.

**Notas**: Riesgo de indirection mitigado con fallback textual; C-08 valida coherencia después.

---

## Fase 3 — Revisión adversarial y linter

**Estado**: completado · **Estimado**: 7,5h · **Real**: — · **Coste est.**: 389 € · **Tokens est.**: 660k

### T-08 — Paso de revisión adversarial en `/dev-cycle` (C-07)

- **Descripción**: Añadir a `commands/dev-cycle.md` un paso nuevo entre la implementación (Fase 3 del ciclo) y qa: un subagente genérico con **contexto fresco** revisa el diff contra `improvement-plan.md`/`tasks.md` y reporta **gaps de corrección o requisitos, no preferencias de estilo**. Decisiones del plan: gaps → **puerta manual** (el usuario decide si vuelve a implementer); el paso aplica **solo a la cadena nativa** (superpowers ya trae revisión propia). Incluye la prueba manual sobre iniciativa de juguete (spec §Pruebas) y la actualización de `docs/FLOWS.md`.
- **Estado**: completado
- **Tiempo humano**: est. 2,5h · real —
- **Tiempo IA (ejec.)**: est. 0,7h · real —
- **Supervisión**: est. 0,18h (≈25 % IA) · real —
- **Previsión IA**: 180k in / 20k out tok · 129 €
- **Dependencias**: independiente de C-01…C-06 (se secuencia aquí por orden recomendado); antes de T-09/T-10
- **Archivos**: `commands/dev-cycle.md`, `docs/FLOWS.md`
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] El paso existe entre implementación y qa, con prompt que define: contexto que recibe (diff + plan + tasks), acotación a gaps de corrección/requisitos y descarte explícito de estilo.
- [x] Los gaps reportados desembocan en puerta manual (documentado en el command); el paso no se ejecuta en la rama superpowers.
- [x] Prueba manual sobre iniciativa de juguete: el paso se ejecuta y reporta contra el plan.
- [x] `docs/FLOWS.md` refleja el flujo nuevo de `/dev-cycle`.

**Subtareas**
- [x] Diseñar el prompt del paso (contexto, acotación, formato del reporte).
- [x] Insertarlo en la máquina de estados del ciclo con la puerta manual.
- [x] Ejecutar la prueba de juguete y ajustar el prompt si reporta estilo.
- [x] Actualizar `docs/FLOWS.md`.

**Notas**: Se decidió paso de command, no agente nuevo (spec §Decisiones de diseño).

### T-09 — Linter de plugin: script de validación (C-08a)

- **Descripción**: Script Python (`scripts/lint_plugin.py`, nombre orientativo, junto a los scripts existentes) que valida sobre `agents/*.md`: `model` presente y con valor admitido, `tools` declarados válidos, `description` con frases-gatillo (heurística **laxa** acordada: presencia de «Úsalo cuando» / «PROACTIVAMENTE» o patrón equivalente), bloque `dependencies` apuntando a agentes/skills/kits existentes y grafo sin ciclos. Mensaje de fallo con campo y patrón esperado; exit code ≠ 0 al fallar.
- **Estado**: completado
- **Tiempo humano**: est. 3,0h · real —
- **Tiempo IA (ejec.)**: est. 0,85h · real —
- **Supervisión**: est. 0,21h (≈25 % IA) · real —
- **Previsión IA**: 250k in / 40k out tok · 156 €
- **Dependencias**: T-01…T-07 recomendadas antes (autovalidación); formalizar la heurística de triggers al inicio de la tarea
- **Archivos**: `scripts/lint_plugin.py` (nuevo)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] El script valida las 5 reglas: `model` presente/válido, `tools` válidos, triggers en description, `dependencies` existentes, sin ciclos.
- [x] Cada fallo indica fichero, campo y patrón esperado (spec §Manejo de errores) y termina con exit code ≠ 0.
- [x] Heurística de triggers laxa y documentada en el propio script (docstring/README), para no generar falsos positivos en contribuciones externas.
- [x] Ejecutado sobre el propio repo tras las fases 1-2: **verde** (autovalidación de C-01…C-06).

**Subtareas**
- [x] Formalizar y documentar el patrón de frases-gatillo (incógnita abierta de la evaluación).
- [x] Parser de frontmatter + validadores de `model`/`tools`/description.
- [x] Grafo de `dependencies` con detección de ciclos y existencia de destinos.
- [x] Ejecución de autovalidación sobre el repo y corrección de lo que aflore.

**Notas**: C-08 repartida en T-09 (script, 3,0 h) + T-10 (tests+CI, 2,0 h) = 5,0 h base de la evaluación.

### T-10 — Linter de plugin: tests, fixtures e integración CI (C-08b)

- **Descripción**: Tests unitarios pytest del linter con fixtures inválidas (agente sin `model`, dependencia inexistente, description sin triggers), junto a `tests/test_dashboard.py` y `test_worklog.py`; cablear el linter como step del workflow CI existente. Decidir (menor) si `release.py` también lo invoca como paso previo al empaquetado.
- **Estado**: completado
- **Tiempo humano**: est. 2,0h · real —
- **Tiempo IA (ejec.)**: est. 0,5h · real —
- **Supervisión**: est. 0,13h (≈25 % IA) · real —
- **Previsión IA**: 150k in / 20k out tok · 103 €
- **Dependencias**: T-09; fases 1-2 aplicadas (autovalidación en verde)
- **Archivos**: `tests/test_lint_plugin.py` (nuevo), `tests/fixtures/` (nuevo), workflow en `.github/workflows/`
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] Tests con las 3 fixtures mínimas de spec §Pruebas (sin `model`, dependencia inexistente, description sin triggers) + caso válido, todos en verde.
- [x] Step del linter añadido al CI; el pipeline completo (tests existentes + nuevos + linter) pasa en verde sobre el repo.
- [x] El fallo del linter en CI no bloquea instalaciones de versiones ya publicadas (spec §Manejo de errores).
- [x] Decisión documentada sobre invocación desde `release.py` (sí/no y por qué).

**Subtareas**
- [x] Crear fixtures y tests pytest.
- [x] Añadir el step al workflow CI.
- [x] Ejecutar la suite completa y verificar verde.
- [x] Cerrar la decisión `release.py`.

**Notas**: —

---

## Fase 4 — Cierre y release

**Estado**: completado · **Estimado**: 0,5h · **Real**: — · **Coste est.**: 26 € · **Tokens est.**: 34k

### T-11 — Release: bump de versión, CHANGELOG y docs

- **Descripción**: Cerrar la iniciativa: bump de versión del plugin con `scripts/release.py`, entrada en `CHANGELOG.md`, y verificación final de que `docs/CONVENTIONS.md` (fuente única de estados, alta de `agent-kits/shared/`) y `docs/FLOWS.md` (flujo de `/dev-cycle` con revisión adversarial) quedaron coherentes con lo implementado.
- **Estado**: completado
- **Tiempo humano**: est. 0,5h · real —
- **Tiempo IA (ejec.)**: est. 0,15h · real —
- **Supervisión**: est. 0,04h (≈25 % IA) · real —
- **Previsión IA**: 30k in / 4k out tok · 26 €
- **Dependencias**: T-01…T-10 completadas y CI en verde
- **Archivos**: `CHANGELOG.md`, versión del plugin (vía `scripts/release.py`), `docs/CONVENTIONS.md`, `docs/FLOWS.md`
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] Versión bumpeada con `scripts/release.py` (y el linter en verde en ese punto).
- [x] `CHANGELOG.md` con entrada que enumera C-01…C-08 y los arreglos de plantillas.
- [x] `docs/CONVENTIONS.md` y `docs/FLOWS.md` coherentes con el estado final (revisión de cierre).
- [x] Este `tasks.md` con las 11 tareas marcadas y el resumen de progreso al 100 %.

**Subtareas**
- [x] Ejecutar `scripts/release.py` (bump).
- [x] Redactar la entrada del CHANGELOG.
- [x] Revisión final de CONVENTIONS/FLOWS.
- [x] Actualizar este ledger y el estado del plan a `completado`.

**Notas**: Tarea añadida en planificación (+0,5 h base sobre la evaluación).

---

## Notas de implementación

_A completar durante la ejecución. Registra decisiones, desvíos de la estimación y aprendizajes._
