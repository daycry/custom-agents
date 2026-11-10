## Fase 2 — Planificar (solo en flujo completo: `architect` opcional → `planner`)

**Fase 2-a — Diseño (agente `architect`, opt-in).** Invoca **`architect`** ANTES de `planner` si (a) la
carpeta ya tiene `design.md` (lo creó `/pm-cycle` 2-bis) — si está `aprobado`, salta a 2-b; si está en
`borrador` (`opcion_elegida: pendiente`), retoma en el paso 2 de abajo — o (b) el usuario lo pide («explora
el diseño», «compara opciones antes de planificar»). Si no se da ninguna, **ofrécelo en una línea** cuando
la evaluación marque complejidad Alta o riesgo arquitectónico; si no, ve directo a 2-b. **Dos pasadas** (el
subagente devuelve UN mensaje; la validación por trozos es tuya, como la puerta go/no-go):
1. Invoca `architect` SIN `elegida:` → `design.md` en `borrador` + resumen estructurado (una línea por
   opción, recomendada, pregunta).
2. **Presenta al usuario por trozos**: AskUserQuestion en Cowork (una opción por entrada, recomendada
   marcada) / lista numerada + pregunta en CLI. Recoge la elección (o una variante).
3. Re-invoca `architect` con `elegida: O<n>` (o `variante: …` → repite 1-2). Fija la opción,
   enlaza `design:` en spec/plan y pasa `design.md` a `aprobado`. Si la decisión cruza el umbral,
   `architect` propone el candidato mediante `knowledge-curation.py propose`, según
   `agent-kits/shared/knowledge-write.md`; conserva ruta pending/SHA para Curator y `adr:` en
   `design.md`. Sin servicio, deja `adr: pendiente` y el motivo. Elegir diseño no aprueba memoria.
**Puerta:** `design.md` en `aprobado` (o el usuario decide seguir sin diseño).

**Fase 2-b — Plan (agente `planner`).** `planner` genera los artefactos del plan en `docs/roadmap/<…>/`:
`improvement-plan.md` + `tasks.md` (+ `test-plan.md` si hay UI), con las plantillas del kit — así
la estructura y el ledger canónico existen siempre. Si existe `design.md` aprobado, `planner` lo lee
y **respeta la opción elegida** (enlaza `design:` ↔ `plan:`). Puerta: OK del plan.

**Revisión visual del plan (opcional, en esta misma puerta).** Si ya existe una
autorización conversacional suficiente, continúa sin abrir revisión ni pedir otro
OK. Cuando el usuario pide revisar visualmente, selecciona la iniciativa exacta;
no busques la última. La revisión sustituye el OK pendiente de esta puerta.
La vía rápida sin `improvement-plan.md` conserva su autorización existente.

Solo si el usuario pide esa revisión, lee `"$DEVKIT/references/phase2-plan-review.md"`: abrirla,
consumirla por CLI y responder a sus comentarios (recetas Bash/PowerShell). Sin esa petición no la cargues.

> **Proyección externa opcional.** Tras aprobar el plan, planner resuelve `plan.created`/`plan.export` por `agent-kits/shared/project-integrations.md`. El adaptador del proyecto elige granularidad, jerarquía y destino, prepara la vista previa y exige autorización aplicable antes de crear. Durante la ejecución cada dueño emite sus eventos; solo el orquestador puede proyectar `task.done` con revisión sin gaps y QA verde. Sin integración se completa el ciclo local.
