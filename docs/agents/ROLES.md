# Mapa de roles — un rol, un dueño

Matriz **pieza × responsabilidad**: quién **DECIDE** (juicio propio sobre el resultado), quién
**ESCRIBE** (el artefacto que le pertenece) y quién solo **LEE** (lo consulta como insumo, sin
tocarlo). Nace de `ADR-011` (agentes retirados y responsabilidades fusionadas) — léelo para el
porqué de cada fusión. Cubre los **9 agentes** de `agents/` más los **3 orquestadores** del plugin:
`/pm-cycle` y `/dev-cycle` (comandos) y la skill `adversarial-review` (orquesta al agente `reviewer`
por lente — el mismo patrón método/ejecutor que un comando aplica a los agentes, a menor escala).

> **Por qué `adversarial-review` cuenta como orquestador y no como "otra skill más".** Un
> orquestador de este plugin es la pieza que **decide una secuencia** y **coordina piezas
> ejecutoras** sin ella misma implementar el resultado final. `/pm-cycle` secuencia `evaluator`
> (+ `architect` opcional); `/dev-cycle` secuencia `planner` → `implementer` → revisión → `qa` →
> `documenter`; `adversarial-review` secuencia 2-4 lentes ejecutadas por `reviewer` en paralelo,
> las funde y gradúa. Las demás skills compartidas (`jira-sync`, `confluence-publish`,
> `roadmap-dashboard`…) no coordinan otras piezas con criterio propio: ejecutan un procedimiento.

## Matriz

| Pieza | Tipo | DECIDE | ESCRIBE | LEE (solo) | No hace |
|---|---|---|---|---|---|
| **analyst** | Agente | Qué técnica de descubrimiento usar en cada conversación (entrevista dirigida / ejemplos / user stories / contraejemplos); cuándo la spec está lista para pedir aprobación. Absorbe el paso de descubrimiento (antes skill `discovery`, retirada — ADR-011 §2). | `spec.md` (crea o afina), fila de `docs/roadmap/README.md`. | El repo (recon ligero), `docs/CONSTITUTION.md` si existe. | No estima horas/coste (`evaluator`), no planifica tareas (`planner`), no implementa, no aprueba él mismo la spec — la aprueba el usuario. |
| **evaluator** | Agente | Coste, esfuerzo, tokens estimados por característica; complejidad y riesgos; orden recomendado si hay varias. El veredicto go/no-go lo **propone**; la puerta la cierra el usuario/orquestador. | `evaluation.md`; `spec.md` SOLO si no existía (la crea desde el prompt); backlink `evaluacion:` en la spec. | `CALIBRATION.md`, `docs/knowledge/lessons/LES-*-evaluator-*`, el repo. | No planifica tareas, no implementa, no diseña arquitectura (`architect`), no fuerza el go/no-go. |
| **architect** | Agente (opt-in) | Qué opciones de diseño son reales y comparables; cuál recomienda. **No fija la elegida** — la fija el usuario, en una segunda pasada. | `design.md`; ADR de la decisión (`propuesta`); SOLO el campo `design:` de `spec.md`/`improvement-plan.md` (vía Edit, alcance impuesto por hook de guardia). | `spec.md`, `evaluation.md`, `docs/knowledge/adr/`, el repo. | No estima horas (`evaluator`), no descompone en tareas (`planner`), no implementa, no reabre un ADR `aceptada` sin decirlo, no fija la opción sin validación del usuario. |
| **planner** | Agente | Descomposición en fases y tareas T-XX; criterios de aceptación verificables por tarea; presupuesto por fase. | `improvement-plan.md`, `tasks.md` (nace del ledger canónico); backlinks a spec/evaluación/design. | `spec.md`, `evaluation.md`, `design.md` (si existe, respeta la opción elegida), el repo. | No implementa, no re-decide el coste total (usa el de `evaluator` como referencia), no vuelca a Jira él mismo — solo **ofrece** la skill `jira-sync` tras crear el plan. |
| **implementer** | Agente | Cómo cumplir cada criterio de aceptación con código real; cuándo una tarea está `DONE`. | El **código del proyecto** (único agente que lo toca); `tasks.md` (ledger, estado por tarea); comentarios/worklog/transición Jira de SU evento (`arrancar`, `implementado`; opt-in — T-02/T-03 de esta iniciativa). | `improvement-plan.md`, `tasks.md`, `design.md` (opción elegida), `docs/knowledge/adr/` y `gotchas/`. | No escribe documentación de referencia (`documenter`), no escribe el informe de test (`qa`), no aprueba su propio trabajo — lo aprueban la revisión de dos lentes y `qa`. |
| **reviewer** | Agente | Veredicto ✓/✗ por criterio de **su lente** (A, B, C o D); graduación propuesta de cada gap que encuentra, con `fichero:línea` y escenario. La skill `adversarial-review` es el MÉTODO (qué lentes aplican, cómo se funden); `reviewer` es el EJECUTOR de una lente — solo lectura por construcción. | Nada en el repo: `tools: Read, Grep, Glob, Bash` (Bash solo para EJECUTAR evidencia, nunca para escribir); su salida vuelve a la skill/orquestador, que la traza en el ledger. | El diff, `improvement-plan.md`/`tasks.md`/`docs/CONSTITUTION.md` (o el objetivo declarado, modo sin ledger); la tabla de veredictos del intento anterior si N > 1. | No corrige nada, no propone refactors, no comenta estilo, no decide qué pasa al 3.er intento (lo devuelve al orquestador/usuario), no toca Jira — el comentario firmado lo compone `jira-flow.py` y lo publica el orquestador/implementer. |
| **qa** | Agente | Veredicto verde/rojo, mecánico vía `qa-gate.py` (nunca una impresión); qué queda como checklist manual para la persona. E2E es SU responsabilidad; unit/integración es la skill compartida `unit-tests` (usada por `implementer` P5 y citada aquí en el informe) — **sin agente "tester" nuevo** (ver nota abajo). | `docs/roadmap/<…>/testing/` (informe md+pdf, evidencias); comentario/label del veredicto en Jira (`qa-verde`/`qa-rojo`, opt-in). | `test-plan.md`, la app local en ejecución. | No implementa la app, no escribe unit tests, no documenta el proyecto (`documenter`). |
| **documenter** | Agente | Estructura de `docs/` derivada del propio proyecto; qué categoría de contenido se omite y por qué (declarado, no silencioso). | El árbol de `docs/` (excepto `docs/roadmap/**` y `docs/security-scan/**`, que solo enlaza). | Todo el repo; `docs/knowledge/**` completo (es quien lo indexa en la documentación de producto). | No implementa ni toca código, no escribe en `docs/roadmap/`, no decide el roadmap. |
| **nemesis** | Agente | Severidad de cada hallazgo de seguridad; si el pentest activo es seguro de lanzar (guardrail no negociable: solo hosts locales/privados). | `docs/security-scan/**` (informe visual + memoria persistente). | Todo el código auditado, CVEs (WebFetch). | No corrige hallazgos (los propone; la remediación es un ciclo de `implementer` vía `/dev-cycle`/`/pm-cycle`), no hace pentest activo fuera de local/privado, no sustituye a `unit-tests`/`api-contract` (esas piezas cubren cobertura y contrato, no vulnerabilidades). |
| **/pm-cycle** | Orquestador (comando) | Puerta go/no-go; si ofrece `architect` (diseño), el brief PDF o una épica en Jira al cierre. | Transiciones de estado de spec/evaluación (el CONTENIDO lo escriben `evaluator`/`architect`). | Toda la carpeta de la iniciativa. | No planifica, no implementa, no prueba, no documenta — cierra en la evaluación (regla explícita en su propio `description`). |
| **/dev-cycle** | Orquestador (comando) | Modo (vía rápida / completo), secuencia de agentes, cuándo relanzar revisión/qa, transiciones de estado del plan/`tasks.md`; en qué punto dispara cada evento de `jira-flow.py` (tabla única en `commands/dev-cycle.md`, T-03 de esta iniciativa). | Transiciones de estado (plan/tasks/spec); invoca los eventos Jira en los puntos que fija esta iniciativa. | Toda la carpeta de la iniciativa. | No escribe código ni documentación (delega en los agentes), no decide el veredicto de revisión/qa (lo dan sus scripts, `qa-gate.py`/la fusión de `adversarial-review`). |
| **adversarial-review** | Orquestador (skill) | Qué lentes aplican (A/B siempre; C seguridad y D rendimiento, condicionales vía `review-lens-select.py`); cómo se funden y gradúan (Critical/Important/Minor) las salidas de 2-4 `reviewer`. | La sección `## Revisión de dos lentes — intento N` en `tasks.md`; promueve entradas `docs/knowledge/` de `propuesta` → `aceptada` al cerrar sin gaps. | El diff, los artefactos de la iniciativa, la tabla del intento anterior. | No implementa ni corrige (eso es `implementer`), no da el verde de pruebas (`qa`), no imputa horas (es del orquestador `/dev-cycle`, vía `jira-flow.py`/`worklog.py`), no decide qué pasa al 3.er intento con gaps (lo devuelve). |

## Solapes resueltos (detalle en ADR-011)

1. **`pdfy` (agente) vs skill `to-pdf`** — mismo disparador, mismo resultado, cero valor añadido en
   la capa "agente". **Retirado** `pdfy`; la skill se auto-invoca por su propia `description` para
   cualquier agente que necesite exportar a PDF (`qa`, `/roadmap-brief`).
2. **`analyst` (agente) vs `discovery` (skill)** — ambos producían la MISMA `spec.md` con la MISMA
   plantilla y el MISMO handoff; `discovery` no la usaba ningún otro agente (no cumplía "compartida
   por 2+", regla 3 de CONVENTIONS) y `/pm-cycle` la invocaba directamente, dejando sin cumplir la
   propia promesa de `analyst` ("cuando `/pm-cycle` reciba un objetivo poco definido"). **Fusión
   por absorción**: el checklist de `discovery` pasa a vivir dentro de `agents/analyst.md`; la
   `description` de `analyst` absorbe sus disparadores; `/pm-cycle` ahora ofrece `analyst`.
3. **`qa` vs una futura skill de tests unitarios** — ya resuelto en la práctica (skill `unit-tests`,
   iniciativa `superiority`, previa a esta): E2E es de `qa`; unit/integración es la skill
   compartida `unit-tests`, usada por `implementer` (P5, gate opcional por `dev.json`
   `tests.coberturaMinima`) y citada por `qa` en su informe (pirámide de pruebas). **Sin agente
   "tester" nuevo.** Esta fila deja el acuerdo por escrito para que nadie lo reabra.
4. **`reviewer` (agente) vs skill `adversarial-review`** — relación método (skill, decide qué
   lentes y cómo se funden) / ejecutor de una lente (agente, solo lectura por construcción). Ya
   funcionaba así; ahora está explícito en la matriz de arriba, no solo en el código.

## Guardarraíl mecánico (heurístico, no sustituye el criterio humano)

`scripts/lint_plugin.py` avisa si dos piezas (agente/skill/comando) declaran en su `description` el
**mismo disparador literal entrecomillado**, normalizado en minúsculas y espacios (`lint_duplicate_triggers`,
`tests/test_lint_plugin.py`). Es un aviso, no un error: cazamos la colisión más barata (copiar un
disparador de una pieza a otra) — los cuatro solapes de este documento usaban frases **distintas**
que un match literal no habría encontrado; esos los sigue cazando la revisión humana en la puerta de
"pieza nueva" de `skills/plugin-dev/SKILL.md`.
