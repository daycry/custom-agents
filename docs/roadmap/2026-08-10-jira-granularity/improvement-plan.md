# 2026-08-10-jira-granularity

> Granularidad del volcado a Jira por fase o por tarea (modo fase: un issue por Fase con sus tareas como checklist) + publicación del resultado del revisor de `/dev-cycle` Modo B (comentario estructurado por criterio + worklog `[revisión]`), extendiendo la skill `jira-sync`.

| | |
|---|---|
| **Fecha** | 2026-08-10 |
| **Estado** | borrador |
| **Tipo** | Nueva Funcionalidad |
| **Prioridad** | Media |
| **Solicitante** | daycry |
| **Responsable** | implementer (ejecución) · daycry (dry-run y aprobación) |
| **Spec** | [`spec.md`](spec.md) |
| **Evaluación** | [`evaluation.md`](evaluation.md) |

---

## Cuadro de mando

| Métrica | Estimado | Real | Confianza |
|--------|---------|------|-----------|
| Tiempo humano | **24,3 h** (20,25 h base +20 %) | 0 h | Media |
| Tiempo IA (ejecución) | **7,9 h** (+ 2,1 h supervisión) | 0 h | Media |
| Coste total | **~1.261 €** | 0 € | Media |
| Tokens IA | **~2,07 M** (in 1,76 M / out 0,31 M) | 0 | Baja |
| Multiplicador productividad | **×2,4** | — | — |
| Tareas | **9** | 0 hechas | — |

> **Herencia y delta.** Las horas por característica se **heredan de la evaluación sin re-estimar**: C-01 1,5 h · C-02 4,0 h · C-03 3,0 h · C-04 3,0 h · C-05 2,5 h · C-06 3,0 h · C-07 1,75 h = **18,75 h base (22,5 h con margen, ~1.168 €, ~1,96 M tokens)**. Este plan añade una **Fase 4 de cierre** no presupuestada en la evaluación: puerta de dry-run manual contra PROJ (T-08, 1,0 h) + cierre documental (T-09, 0,5 h) → **delta +1,5 h base (+1,8 h con margen, +~93 €, +118k tokens)**. Total del plan: **20,25 h base / 24,3 h con margen / ~1.261 € / ~2,07 M tokens**.

---

## Estimación por fase

| Fase | Estimado (h) | Tokens (in / out) | Coste € |
|------|-------------|-------------------|---------|
| Fase 1 — Config de granularidad (C-01) | 1,5 | 120k / 20k | ~78 € |
| Fase 2 — Modo fase (C-02…C-05) | 12,5 | 1.060k / 190k | ~653 € |
| Fase 3 — Revisor → Jira (C-06…C-07) | 4,75 | 480k / 85k | ~250 € |
| Fase 4 — Puerta de dry-run y cierre | 1,5 | 100k / 18k | ~78 € |
| **Total (base)** | **20,25 h** | **1,76 M / 0,31 M** | **~1.059 €** |

> Horas y costes de la tabla son **base** (sin colchón). El margen de contingencia (+20 % sobre las horas base) está en el presupuesto de abajo: total con margen **~1.261 €**.

---

## Presupuesto económico

**Coste = (horas × tarifa) + coste de tokens de IA.** Todos los importes en **EUR**.

### Supuestos (ajustables)

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | 50 €/h | Default compartido (no existe `.claude/rates.json`); heredado de la evaluación |
| Modelo IA asumido | claude-opus-4-8 | Modelo previsto para la ejecución |
| Precio input | 13,80 € / 1M tokens | ⚠️ verificar — supuesto de trabajo (15 USD/M × 0,92), heredado de la evaluación |
| Precio output | 69,00 € / 1M tokens | ⚠️ verificar — supuesto de trabajo (75 USD/M × 0,92) |
| Tipo de cambio | 1 USD = 0,92 € | Default |
| Ratio de supervisión | 25 % de las horas IA | Default |
| Margen de contingencia | 20 % | Sobre horas base (humanas e IA) |

### Desglose

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 20,25 h × 50 €/h | 1.012,50 € |
| Margen de contingencia | +20 % sobre desarrollo base | 202,50 € |
| Tokens IA (input) | 1,76 M tok × 13,80 €/M ⚠️ | 24,29 € |
| Tokens IA (output) | 0,313 M tok × 69,00 €/M ⚠️ | 21,60 € |
| **Total estimado (con margen)** | | **~1.261 €** |

> ⚠️ El coste de tokens (~46 €, un 3,6 % del total) usa precios **supuestos** pendientes de verificar (skill `rates-verify`); una desviación del ±50 % en la tarifa de tokens mueve el total menos del 2 %. El riesgo económico está en las horas (integración con el conector), no en los tokens.

---

## Previsión de tokens (por fase)

Estimación del consumo de tokens del modelo por fase. Base: claude-opus-4-8 · precios de la tabla de supuestos.

| Fase | Input (tok) | Output (tok) | Total (tok) | Coste € |
|------|------------|-------------|-------------|---------|
| Fase 1 — Config de granularidad | 120k | 20k | 140k | 3,04 € |
| Fase 2 — Modo fase | 1.060k | 190k | 1.250k | 27,74 € |
| Fase 3 — Revisor → Jira | 480k | 85k | 565k | 12,49 € |
| Fase 4 — Dry-run y cierre | 100k | 18k | 118k | 2,62 € |
| **Total** | **1.760k** | **313k** | **2.073k** | **~45,88 €** |

**Método de estimación:** heredado de la evaluación por característica (lectura repetida de `SKILL.md` ~218 líneas, `dev-cycle.md` ~108 líneas, `worklog.py` ~206 líneas + tests, por cada tarea que los toca, más generación de prosa/código/tests). Fase 4 estimada aparte: llamadas al conector en el dry-run + edición de CHANGELOG/docs.

---

## Productividad IA (humano vs. IA)

Compara el esfuerzo **humano** estimado con el tiempo que tardaría un **agente de IA** en ejecutarlo (más la supervisión humana necesaria). Cifras aproximadas; supuestos declarados.

| KPI | Valor |
|-----|-------|
| Horas humanas estimadas | 24,3 h *(20,25 h base)* |
| Horas IA (ejecución) | 7,9 h *(6,6 h base; supuesto)* |
| Supervisión humana | 2,1 h *(1,75 h base; ≈25 % de las horas IA)* |
| **Horas totales (IA + supervisión)** | **10,0 h** |
| Horas ahorradas | 14,3 h |
| **Ahorro** | **~59 %** |
| **Multiplicador de productividad** | **×2,4** |
| FTE equivalentes *(opcional)* | ~0,09 |

> Horas mostradas **con el margen de contingencia (+20 %)** ya aplicado sobre las horas base (humanas e IA). El trabajo es muy agente-friendly (sobre todo prosa en skill/command existentes + cambio acotado en `worklog.py`); la supervisión se concentra en lo empírico: el dry-run de la Fase 4 (checklist, N worklogs por issue, comentario y worklog de revisión) es trabajo humano y por eso el multiplicador baja ligeramente respecto a la evaluación (×2,5 → ×2,4).

---

## Resumen ejecutivo

Extender la skill `jira-sync` para ofrecer, junto al modo actual "un issue por tarea `T-XX`", un **modo fase**: un issue de Jira por cada Fase del plan, con sus tareas como checklist en la descripción, y progreso (comentarios por tarea, worklog tarea a tarea, Done al cerrar todas) coherente con esa granularidad. Además, publicar en Jira el **resultado del agente revisor** de `/dev-cycle` Modo B: comentario estructurado por criterio contra una plantilla fija (con bucle reviewer→implementer acotado a 3 intentos) y worklog separado `[revisión]` que acumula todas las pasadas, en ambos modos. El ledger `tasks.md` sigue siendo la fuente de verdad; Jira es el espejo. La iniciativa se cierra solo tras superar la **puerta de dry-run** contra el proyecto de pruebas PROJ (condición del veredicto go de la evaluación).

### Objetivos

- Ofrecer las dos granularidades elegibles vía `.claude/jira.json` (`granularidad: "tarea" | "fase"`), con `"tarea"` por defecto reproduciendo el comportamiento actual **bit a bit**.
- En modo fase: 1 issue por fase con checklist de tareas, comentario + marca `- [x]` al completar cada `T-XX`, worklog tarea a tarea en el issue de fase y Done solo con todas las tareas `completado`.
- Publicar el resultado FINAL del revisor (pasa/falla por criterio + "revisión superada en N intento(s)") como comentario en Jira y su tiempo como worklog `[revisión]`, en ambos modos, idempotente.
- Validar empíricamente contra PROJ las cuatro capacidades no ejercitadas del conector antes de dar la iniciativa por cerrada.

---

## Datos necesarios para un informe completo

- [x] **Requisitos funcionales** confirmados por el solicitante (spec `aprobada` + §Decisiones confirmadas 2026-08-10)
- [x] **Alcance** cerrado (spec §Alcance: dentro C-01…C-07; fuera modo mixto, subtareas, migración, Modo A, gaps intra-fase)
- [x] **Criterios de éxito / métricas** acordados (spec §Pruebas)
- [ ] **Accesos y credenciales** — conector Atlassian conectado al site del proyecto con permiso de escritura en PROJ (necesario para la Fase 4; verificar antes del dry-run)
- [x] **Entornos** disponibles (repo local; proyecto de pruebas PROJ para el dry-run)
- [x] **Stakeholders** identificados (daycry; ejecuta el dry-run de la Fase 4)
- [ ] **Dependencias externas** — `editJiraIssue` sobre descripción, N worklogs por issue, `addCommentToJiraIssue` y `addWorklogToJiraIssue` **no ejercitados end-to-end** (se resuelven en la Fase 4); **`qa-strict` desplegado** es prerequisito de la Fase 3
- [x] **Restricciones** conocidas (opt-in, no romper modo tarea, no hardcodear tipos, C-06/C-07 solo Modo B)
- [x] **Tarifa/hora y supuestos de coste** confirmados (defaults compartidos; sin `.claude/rates.json`)

---

## Análisis de impacto

- **`skills/jira-sync/SKILL.md`** — el grueso del plan (prosa): Paso 0/§Config gana `granularidad`; Pasos 4–6 ganan la rama de creación por fase (checklist, manifiesto `fase-N`, clave en cabecera de fase de `tasks.md`); Paso 7 gana progreso/worklog/Done por fase; Paso 8 gana read-back con agregado por fase; y un paso nuevo de **publicación del resultado del revisor** (comentario + worklog `[revisión]`, idempotente).
- **`skills/jira-sync/scripts/worklog.py`** — cambio acotado: el destino `issueKey` por modo (fase/tarea) y un tipo/etiqueta de entrada `[revisión]`; la aritmética de tope de jornada y banco **no cambia**.
- **`tests/test_worklog.py`** — dos casos nuevos (imputación a issue de fase; entrada `[revisión]` separada que cuadra con el total); los existentes siguen verdes.
- **`commands/dev-cycle.md`** — el revisor de Modo B emite salida **estructurada** por criterio; bucle reviewer→implementer acotado a 3 intentos coordinado por el orquestador; invocación del paso de publicación de `jira-sync` al cerrar tarea/fase.
- **`agent-kits/shared/review-report.template.md`** — **nuevo**: plantilla fija del comentario de revisión.
- **`.claude/jira.json` / `.claude/jira-state.json`** — esquema (documentado en el SKILL): campo `granularidad`; claves `fase-N → issueKey`, `reviewComentado`, desglose implementación/revisión para `/retro`.

---

## Cambios arquitectónicos

- **La granularidad es config persistente, no flag por invocación** (`.claude/jira.json`), coherente con los opt-ins existentes; si falta, se pregunta una vez y se persiste. `"tarea"` es el defecto y reproduce el comportamiento actual bit a bit (compatibilidad total).
- **Idempotencia por manifiesto con claves separadas por modo**: `T-XX → issueKey` (tarea) y `fase-N → issueKey` (fase) conviven en `jira-state.json`; cambiar de granularidad con issues ya creados **avisa del choque** y nunca duplica en silencio.
- **El ledger `tasks.md` sigue siendo la fuente única de verdad**; Jira es espejo. En modo fase la clave Jira se anota en la cabecera de la fase; el Done del issue de fase se deriva del agregado de sus tareas en el ledger.
- **El revisor pasa de prosa a contrato de salida estructurado** (`T-XX` → criterio → ✓/✗ + gaps) renderizado contra una plantilla fija compartida; el bucle reviewer→implementer lo coordina `/dev-cycle` (no el implementer), acotado a 3 intentos, y a Jira se publica solo el resultado FINAL. Solo Modo B (en Modo A revisa superpowers con otro formato).
- **El tiempo de revisión es una entrada de worklog separada `[revisión]`** que acumula todas las pasadas; el desglose implementación/revisión vive en `jira-state.json` para `/retro`, y el total del issue en Jira = implementación + revisión.

---

## Archivos a crear/modificar

| Archivo | Acción | Propósito |
|---------|--------|-----------|
| `skills/jira-sync/SKILL.md` | Modificar | Config `granularidad` (C-01); rama de creación modo fase (C-02); progreso comentarios+checklist (C-03); worklog/Done por fase (C-04); read-back por modo (C-05); paso de publicación del resultado del revisor (C-06) |
| `skills/jira-sync/scripts/worklog.py` | Modificar | Destino `issueKey` por modo (C-04) + tipo/etiqueta de entrada `[revisión]` (C-07) |
| `tests/test_worklog.py` | Modificar | Casos nuevos: imputación a issue de fase (C-04) y entrada `[revisión]` separada (C-07); los existentes siguen verdes |
| `commands/dev-cycle.md` | Modificar | Salida estructurada del revisor Modo B + bucle reviewer→implementer acotado a 3 + invocación de la publicación al cerrar fase/tarea (C-06) |
| `agent-kits/shared/review-report.template.md` | Crear | Plantilla fija del comentario de revisión (cabecera + checklist por criterio + gaps + "revisión superada en N intento(s)" + tiempo) |
| `CHANGELOG.md` | Modificar | Entrada en `[Unreleased]` con lo añadido (cierre, T-09) |
| `docs/FLOWS.md` | Modificar | Reflejar el bucle acotado reviewer→implementer y la publicación a Jira en el flujo de `/dev-cycle` (cierre, T-09) |

> `.claude/jira.json` y `.claude/jira-state.json` son ficheros **por proyecto** (no del repo); su esquema nuevo se documenta en el SKILL, no se versionan aquí.

---

## Dependencias y prerequisitos

- **`qa-strict` desplegado** (revisor de dos lentes en `/dev-cycle` Modo B) — prerequisito duro de la Fase 3 (C-06/C-07); ya implementado en este repo (`docs/roadmap/2026-08-10-qa-strict/`).
- **Orden interno**: C-01 antes que todo (la config habilita el modo); C-02 antes que C-03/C-04/C-05 (necesitan issues de fase y mapeo `fase-N`); C-06 antes que C-07 (el worklog `[revisión]` imputa el tiempo que sale del bucle de revisión).
- **La Fase 4 está bloqueada por todas las anteriores**: el dry-run ejercita creación en modo fase, checklist, comentario de revisión y worklog `[revisión]` — necesita todo implementado.
- **Conector Atlassian (Rovo MCP)** conectado al site del proyecto con acceso de escritura al proyecto de pruebas PROJ (Fase 4).
- `ledger-lint.py` (ya existente) valida el ledger antes del volcado en modo fase.

---

## Criterios de aceptación (global)

- [ ] Con `granularidad: "tarea"` (o ausente y respondida "tarea"), el comportamiento de `jira-sync` es **idéntico al actual** (sin regresión).
- [ ] Con `granularidad: "fase"`, el volcado crea 1 issue por fase con las `T-XX` como checklist, idempotente (`fase-N → issueKey`), sin issue para fases sin tareas, y el progreso (comentario + `- [x]` + worklog tarea a tarea + Done al cerrar todas) funciona end-to-end.
- [ ] El resultado FINAL del revisor se publica como comentario con la plantilla fija (+ "revisión superada en N intento(s)") y su tiempo como worklog `[revisión]` que acumula todas las pasadas, en ambos modos, sin duplicar en reejecución (`reviewComentado`).
- [ ] `python3 -m pytest tests/test_worklog.py` en verde (casos existentes + 2 nuevos).
- [ ] **Dry-run contra PROJ superado** (creación modo fase, `editJiraIssue` de checklist, `addComment` de revisión, `addWorklog [revisión]`) — puerta manual antes de dar la iniciativa por cerrada.

---

## Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| El conector no permite editar la descripción para la checklist (`editJiraIssue`) | Media | Alto (T-03) | Puerta de dry-run (T-08); plan B previsto en la spec: degradar a "solo comentarios" y documentar la limitación |
| El conector no acumula bien N worklogs por issue (fase + `[revisión]`) | Media | Medio (T-04/T-07) | Verificar en PROJ con issue desechable; si falla, worklog agregado y desglose solo interno en `jira-state.json` |
| `addComment`/`addWorklog` de revisión no ejercitados end-to-end | Media | Medio (T-06/T-07) | El dry-run (T-08) incluye publicar un comentario de revisión y un worklog `[revisión]` de prueba |
| Cambiar el contrato del revisor rompe otros consumidores en `/dev-cycle` | Baja | Medio (T-06) | Añadir el esquema estructurado sin quitar el resumen en prosa; degradación prevista (resumen + gaps con aviso, sin ✓/✗ inventados) |
| Regresión del modo tarea al introducir el modo fase | Media | Alto | Criterio explícito "bit a bit" en T-01/T-02; claves de manifiesto separadas por modo; revisar los Pasos 4–8 con la rama tarea intacta |
| Cabeceras de fase heterogéneas en `tasks.md` → parseo frágil | Media | Medio | Exigir `ledger-lint.py` en verde antes del volcado en modo fase (T-02) |
| Cambio de granularidad con issues ya creados en el otro modo | Baja | Medio | Aviso de choque de manifiesto: continuar en el modo volcado o empezar limpio; nunca duplicar en silencio (T-02) |

---

## Métricas de éxito

- **0 regresiones** en modo tarea: un volcado con `"tarea"` produce exactamente los mismos issues/comentarios/worklogs que antes del cambio.
- **Reducción de issues en modo fase**: un plan de N tareas en F fases genera F issues (no N), con el desglose íntegro (checklist + comentarios + worklogs por tarea).
- **Dry-run PROJ con las 4 capacidades verificadas** (o sus planes B documentados) — condición del go de la evaluación cumplida.
- **Trazabilidad de revisión en Jira**: cada tarea/fase cerrada en Modo B tiene su comentario de revisión (formato de plantilla fija) y su worklog `[revisión]`; `/retro` puede leer el desglose implementación/revisión del manifiesto.

---

## Changelog del plan

| Fecha | Cambio | Autor |
|-------|--------|-------|
| 2026-08-10 | Creación del plan (9 tareas en 4 fases; horas heredadas de la evaluación + delta de cierre +1,5 h) | planner |

---

## Siguiente paso

Con el **OK del plan** del usuario (puerta de control), el agente **`implementer`** lo ejecuta fase a fase sobre una rama, marcando `tasks.md` como **ledger canónico** (checkbox + estado por tarea). La **Fase 4 (T-08)** es una puerta manual: el dry-run contra PROJ lo ejecuta el usuario antes de dar la iniciativa por cerrada. Sin `test-plan.md` (no hay UI): las pruebas son pytest de `worklog.py` + el dry-run manual. Al terminar, cierre con `documenter`.

---

## Revisión adversarial de dos lentes (2026-08-10)

Dos subagentes con contexto fresco (conformidad + calidad/robustez), ejecutando los tests. Resultado: **worklog.py sin defectos de corrección** (total = impl+revisión en todos los caminos; el tope diario cuenta el total sin importar el kind; el banco conserva y re-imputa el kind; retrocompatibilidad de entradas legadas sin kind; 12/12 tests). Los dos apuntes de las lentes ya estaban cubiertos en el estado final del SKILL (invocación de `ledger-lint.py` antes de volcar en modo fase; clave `rev-fase-N` para el worklog de revisión agregada en modo fase) — y se arregló un **bloque de código a medio cerrar** en el Paso 9. C-01…C-07 conformes. **T-08 (dry-run del conector contra PROJ) queda como puerta manual pendiente**: es la condición del go y no es ejercitable en el sandbox.
