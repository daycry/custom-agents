# 2026-08-10-jira-granularity

> Granularidad del volcado a Jira (por fase o por tarea) **+ publicación del resultado del revisor** (comentario por criterio + worklog de revisión): evaluación de coste/esfuerzo para decidir si se aprueba extender la skill `jira-sync` y cablear la salida del revisor de `/dev-cycle`.

| | |
|---|---|
| **Fecha** | 2026-08-10 |
| **Estado** | completado ✅ |
| **Prioridad global** | Media 🟡 |
| **Solicitante** | jmano@mediapro.tv |
| **Spec** | [`spec.md`](spec.md) |
| **Plan** | [`improvement-plan.md`](improvement-plan.md) + [`tasks.md`](tasks.md) (2026-08-10) |
| **Características evaluadas** | 7 |

---

## Cuadro de mando

| Métrica | Total estimado | Confianza |
|--------|----------------|-----------|
| Esfuerzo humano | **22,5 h** (18,75 h base +20 %) | Media |
| Tiempo IA (ejecución) | **7,2 h** (+ 1,8 h supervisión) | Media |
| Coste | **~1.168 €** | Media |
| Tokens IA | **~1,96 M** (in 1,66 M / out 0,30 M) | Baja |
| Multiplicador productividad | **×2,5** | — |
| Características | **7** | — |

> ⚠️ **Incógnita que baja la confianza:** toda la iniciativa se apoya en capacidades del conector Atlassian **no ejercitadas end-to-end** en este proyecto: (a) editar la descripción de un issue para mantener la checklist `- [x]` (`editJiraIssue`), (b) acumular **varias entradas de worklog** en un mismo issue de fase, y —nuevo con C-06/C-07— (c) publicar **comentarios** (`addCommentToJiraIssue`) y **worklogs `[revisión]`** (`addWorklogToJiraIssue`) del resultado del revisor. La creación real de issues, comentarios y worklogs no está probada aún contra la instancia. Además **C-06/C-07 dependen de que `qa-strict` esté desplegado** (el revisor de dos lentes que emite la salida a publicar). Presupuestado bajo el supuesto de que todo lo anterior funciona; de ahí la puerta de dry-run.

---

## Resumen ejecutivo

La spec (confirmada y **ampliada** con el usuario el 2026-08-10, de 5 a 7 características) pide dos cosas: **(1)** extender `jira-sync` para ofrecer, junto al modo actual "un issue por tarea `T-XX`", un nuevo **modo fase** (un issue por Fase, tareas como checklist, comentarios / worklog / Done coherentes) — C-01…C-05; y **(2)** publicar en Jira el **resultado del agente revisor** de `/dev-cycle` Modo B: un **comentario estructurado por criterio** contra una plantilla fija y un **worklog de revisión `[revisión]`** separado, en ambos modos — C-06 y C-07. El grueso sigue siendo **prosa de instrucciones al agente** (SKILL.md y dev-cycle.md) más un cambio acotado en `worklog.py` + tests y una plantilla nueva. Se presupuestan **18,75 h base (22,5 h con margen), ~1.168 €** y ~1,96 M tokens. La evaluación soporta **aprobar la iniciativa con condición**: coherente y de coste contenido, pero con dependencias no verificadas del conector (ahora también comentario + worklog de revisión) y de `qa-strict`; se recomienda un dry-run empírico contra DM5985 antes de dar por cerrados C-03/C-04 y C-06/C-07.

---

## Requerimientos recibidos

Mapa de la spec a las características evaluadas.

| ID | Característica | Requisito origen (ref.) | ¿Claro? |
|----|---------------|-------------------------|---------|
| C-01 | Config de granularidad | spec §Características C-01 + §Decisiones de diseño ("Dónde se elige") | ✅ |
| C-02 | Volcado en modo fase | spec §Características C-02 + §Decisiones (estructura, tipo, checklist, idempotencia, escritura en `tasks.md`) | ✅ |
| C-03 | Progreso en modo fase (comentarios + checklist) | spec §Características C-03 + §Decisiones (comentarios, checklist de la descripción) | ⚠️ ambiguo (depende de `editJiraIssue`) |
| C-04 | Worklog y Done en modo fase | spec §Características C-04 + §Decisiones (worklog, transición a Done) + §Pruebas | ⚠️ ambiguo (varias entradas de worklog / Done al cerrar todas) |
| C-05 | Read-back y coherencia por modo | spec §Características C-05 (Paso 8) | ✅ |
| C-06 | Resultado del revisor → comentario en Jira (plantilla + salida estructurada) | spec §Características C-06 + §Decisiones ("Resultado del revisor → Jira", "Formato del comentario", "Cadencia") + §Decisiones confirmadas 3-4-6 | ⚠️ ambiguo (cambia el contrato del revisor; depende de `qa-strict` y de `addComment` no ejercitado) |
| C-07 | Worklog de revisión (entrada `[revisión]`, ambos modos) | spec §Características C-07 + §Decisiones ("Worklog de revisión") + §Decisiones confirmadas 5 + §Pruebas | ⚠️ ambiguo (`addWorklog` de revisión no ejercitado; depende de C-04 y C-06) |

**Ambigüedades / información que falta:**

- **Capacidad `editJiraIssue` para la checklist (C-03).** Si el conector no permite editar la descripción, la checklist se refleja solo en comentarios (plan B ya previsto). No verificado end-to-end → confianza Baja.
- **Varias entradas de worklog en un mismo issue (C-04 y C-07).** La spec asume que Jira lo permite; ahora las entradas `[revisión]` de C-07 conviven con las de implementación en el mismo issue → refuerza la necesidad de verificarlo.
- **Contrato de salida del revisor (C-06).** Es lo nuevo de la ampliación: el revisor de `qa-strict` hoy emite **prosa**; C-06 exige que emita **estructura por criterio** (`T-XX` → criterio → ✓/✗ + gaps) para renderizarla contra la plantilla fija. Estimar el cambio de contrato depende de cómo esté escrito hoy el paso de revisión en `dev-cycle.md`; se asume que es prosa guiada y que añadir un esquema de salida es acotado.
- **`addCommentToJiraIssue` / `addWorklogToJiraIssue` no ejercitados end-to-end (C-06/C-07).** La spec §Supuestos lo declara: disponibles pero sin probar contra la instancia → misma puerta de dry-run que el modo fase, confianza Baja-Media.
- **Dependencia de `qa-strict` desplegado (C-06/C-07).** Si el revisor de dos lentes no está en producción, C-06/C-07 no aplican (no hay salida que publicar). Se presupuesta asumiendo que sí lo está.
- **Detección de "cabecera de fase" en `tasks.md`** para anotar la clave Jira (C-02) y agregar el estado (C-04/C-05). Se apoya en `ledger-lint.py`; si el formato no es homogéneo, sube el coste de parseo.

---

## Datos necesarios para una evaluación completa

- [x] **Requerimientos** completos y sin ambigüedades — salvo las incógnitas de conector y contrato del revisor marcadas
- [x] **Alcance** de cada característica acotado (dentro/fuera bien delimitado en la spec, incl. Modo A fuera)
- [x] **Criterios de aceptación / éxito** por característica (spec §Pruebas)
- [x] **Restricciones** (opt-in, no romper modo tarea, no hardcodear tipos, solo Modo B)
- [ ] **Dependencias externas** — el conector Atlassian **no** está verificado para `editJiraIssue` sobre descripción, múltiples worklogs por issue, ni `addComment`/`addWorklog` de revisión; y **C-06/C-07 dependen de `qa-strict` desplegado**
- [x] **Contexto técnico** del proyecto (skill existente, `worklog.py` con tests, manifiesto, revisor de `qa-strict`)
- [x] **Tarifa/hora y supuestos de coste** confirmados (defaults; sin `.claude/rates.json`)

---

## Supuestos económicos (ajustables)

**Coste = (horas × tarifa) + coste de tokens de IA.** Importes en **EUR**.

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | 50 €/h | Default compartido (no existe `.claude/rates.json`) |
| Modelo IA asumido | claude-opus-4-8 | Base de la previsión de tokens |
| Precio input | 13,80 € / 1M tokens | ⚠️ verificar — supuesto de trabajo: 15 USD/M × 0,92 |
| Precio output | 69,00 € / 1M tokens | ⚠️ verificar — supuesto de trabajo: 75 USD/M × 0,92 |
| Tipo de cambio | 1 USD = 0,92 € | Default |
| Ratio de supervisión | 25 % de las horas IA | Default |
| Horas por FTE-mes | 160 h | Para FTE equivalentes |
| Margen de contingencia | 20 % | Sobre horas base (humanas e IA) |

**Calibración con el histórico del repo** (no existe `docs/roadmap/CALIBRATION.md`; se usan las evaluaciones cerradas como referencia, <3 filas → indicio, no ley): `2026-08-10-qa-strict` = **19,0 h base** (por comparar: dos scripts Python con tests + config + workflow + plantilla). Esta iniciativa es sobre todo **prosa** de un modo nuevo dentro de una skill existente (C-01…C-05, 14,0 h base) más la **ampliación** C-06/C-07: C-06 es cambio de contrato del revisor (prosa en `dev-cycle.md` + esquema de salida) + fontanería de publicación + plantilla nueva, análoga en tamaño a una pieza media de `qa-strict` → **3,0 h base**; C-07 es `worklog.py` + tests (tipo/etiqueta de entrada + destino por modo) + desglose en `jira-state.json`, análogo a las piezas de `worklog.py` ya calibradas → **1,75 h base**. El histórico avala que el coste de tokens es marginal (~4 % del total). La incertidumbre no está en el volumen de trabajo sino en la **integración con el conector** (ahora también comentario + worklog de revisión) y en la **dependencia de `qa-strict`**; por eso el margen se mantiene y la confianza baja en C-03/C-04 y C-06/C-07.

---

## Evaluación por característica

### C-01 — Config de granularidad

- **Requisito origen**: spec §Características C-01; §Decisiones ("Dónde se elige").
- **Descripción**: nuevo campo `granularidad` en `.claude/jira.json` (`"tarea"` por defecto para no romper instalaciones; `"fase"` nuevo). Si falta al volcar, preguntar una vez (artefacto en Cowork / conversacional en CLI) y persistir. Documentar en el SKILL.
- **Complejidad**: Baja
- **Esfuerzo**: 1,5 h · confianza **Alta**
- **Previsión IA**: 120k in / 20k out tok · ~3 €
- **Coste**: (1,5 h × 50 €/h) + 3,04 € = **~78 €**
- **Impacto / áreas afectadas**: `skills/jira-sync/SKILL.md` (Paso 0 + §Config), `.claude/jira.json` (esquema).
- **Dependencias y prerequisitos**: ninguna; reutiliza el patrón opt-in existente.
- **Riesgos**: mínimos. Único cuidado: no alterar el comportamiento por defecto (`"tarea"` reproduce bit a bit lo actual).
- **Incógnitas / preguntas abiertas**: ninguna material.

### C-02 — Volcado en modo fase

- **Requisito origen**: spec §Características C-02; §Decisiones (estructura, tipo por jerarquía, checklist, idempotencia por `fase-N`, escritura en `tasks.md`).
- **Descripción**: al crear, un issue por Fase del plan; descripción con las `T-XX` de la fase como **checklist**; tipo descubierto por jerarquía (igual que hoy, sin hardcodear); previsualización/confirmación como el modo tarea; idempotente vía `fase-N → issueKey` en el manifiesto; escribe la clave Jira en la cabecera de cada fase de `tasks.md`.
- **Complejidad**: Alta (es el núcleo del modo nuevo; agrupar tareas por fase, construir la checklist y ampliar la clave del manifiesto).
- **Esfuerzo**: 4,0 h · confianza **Media**
- **Previsión IA**: 320k in / 60k out tok · ~9 €
- **Coste**: (4,0 h × 50 €/h) + 8,56 € = **~209 €**
- **Impacto / áreas afectadas**: `skills/jira-sync/SKILL.md` (Pasos 4–6 con rama de fase), `.claude/jira-state.json` (clave `fase-N`), `tasks.md` (cabecera de fase).
- **Dependencias y prerequisitos**: C-01 (necesita la config para saber en qué modo volcar). Se apoya en `ledger-lint.py` para validar el ledger antes de volcar.
- **Riesgos**: parseo de "fase → tareas" en `tasks.md` si el formato de cabecera no es homogéneo; colisión de manifiesto si se cambia de granularidad con issues ya creados (la spec lo cubre con aviso).
- **Incógnitas / preguntas abiertas**: sintaxis exacta de la checklist en la descripción (lista markdown en el cuerpo vs. panel nativo). Un **dry-run** contra el proyecto de pruebas DM5985 resolvería esto y calibraría C-03/C-04.

### C-03 — Progreso en modo fase (comentarios + checklist)

- **Requisito origen**: spec §Características C-03; §Decisiones (comentarios por tarea; checklist de la descripción).
- **Descripción**: al completar una `T-XX`: (a) **comentario** en el issue de su fase con tarea, evidencia y horas; (b) marca `- [x]` esa tarea en la **checklist** de la descripción del issue (localizando el issue por `fase-N` en el manifiesto).
- **Complejidad**: Media-Alta
- **Esfuerzo**: 3,0 h · confianza **Baja**
- **Previsión IA**: 260k in / 45k out tok · ~7 €
- **Coste**: (3,0 h × 50 €/h) + 6,69 € = **~157 €**
- **Impacto / áreas afectadas**: `skills/jira-sync/SKILL.md` (Paso 7, rama de fase; addComment + editJiraIssue).
- **Dependencias y prerequisitos**: C-02 (issues de fase creados y mapeados).
- **Riesgos**: **el marcado de la checklist depende de `editJiraIssue` sobre la descripción**, no verificado end-to-end. Riesgo de re-escritura de descripción (perder contenido si el editor no hace merge). Editar la descripción en cada tarea completada multiplica llamadas de escritura.
- **Incógnitas / preguntas abiertas**: ¿el conector permite editar la descripción manteniendo el resto? Si no → degradar a "solo comentario" y anotar la limitación (plan B ya previsto en la spec, reduciría este coste ~1 h).

### C-04 — Worklog y Done en modo fase

- **Requisito origen**: spec §Características C-04; §Decisiones (worklog, Done); §Pruebas (caso de imputación a issue de fase).
- **Descripción**: worklog imputado en el issue de la fase **tarea a tarea** (misma lógica de `worklog.py` —tope de jornada y banco—, cambiando solo el `issueKey` destino, que **ya es parámetro** del script); transición a **Done** del issue de fase solo cuando todas sus tareas están `completado` en `tasks.md`.
- **Complejidad**: Media
- **Esfuerzo**: 3,0 h · confianza **Baja** (incluye ~1 h de código+test en `worklog.py`; el resto es prosa de agregación "todas las tareas de la fase Done").
- **Previsión IA**: 280k in / 50k out tok · ~7 €
- **Coste**: (3,0 h × 50 €/h) + 7,31 € = **~157 €**
- **Impacto / áreas afectadas**: `skills/jira-sync/SKILL.md` (Paso 7, imputación y transición por fase), `skills/jira-sync/scripts/worklog.py` (mínimo: destino del `issueKey`), `tests/test_worklog.py` (nuevo caso: mismo cálculo, distinto destino).
- **Dependencias y prerequisitos**: C-02 (issues de fase) y C-03 (progreso). Los tests existentes deben seguir verdes.
- **Riesgos**: **acumular varias entradas de worklog en un mismo issue de fase** no está ejercitado con el conector; el tope de jornada/banco por día ya lo resuelve el script (no cambia). El disparo de Done "solo al cerrar todas las tareas" exige leer el agregado de la fase en `tasks.md` de forma fiable.
- **Incógnitas / preguntas abiertas**: ¿Jira/conector admite N worklogs por issue sin efectos raros de reporting? El tope de jornada es **diario y global**, no por issue, así que el reparto tarea→fase no altera la aritmética; solo el destino. Nota: C-07 añade a este mismo issue las entradas `[revisión]`, reforzando la incógnita de "N worklogs por issue".

### C-05 — Read-back y coherencia por modo

- **Requisito origen**: spec §Características C-05 (Paso 8).
- **Descripción**: el read-back y la comprobación de coherencia entienden ambos modos; en modo fase compara el estado del issue de fase con el **agregado** de sus tareas (`completado` ⟺ todas las tareas de la fase cerradas). Sin romper el modo tarea.
- **Complejidad**: Media
- **Esfuerzo**: 2,5 h · confianza **Media**
- **Previsión IA**: 200k in / 35k out tok · ~5 €
- **Coste**: (2,5 h × 50 €/h) + 5,18 € = **~130 €**
- **Impacto / áreas afectadas**: `skills/jira-sync/SKILL.md` (Paso 8, mapeo de estado con agregación por fase).
- **Dependencias y prerequisitos**: C-02 (manifiesto con `fase-N`).
- **Riesgos**: mapeo de categorías de estado (Done/In Progress/To Do) frente al agregado; divergencias parciales (unas tareas cerradas y otras no) que hay que mostrar sin sobreescribir el ledger canónico.
- **Incógnitas / preguntas abiertas**: cómo representar en la salida una fase "parcialmente hecha" (issue Done en Jira pero no todas las tareas en `tasks.md`). Se resuelve listando la divergencia, sin tocar el ledger sin confirmación (regla vigente del Paso 8).

### C-06 — Resultado del revisor → comentario en Jira (plantilla + salida estructurada)

- **Requisito origen**: spec §Características C-06; §Decisiones ("Resultado del revisor → Jira", "Formato del comentario de revisión", "Cadencia de la revisión (modo fase)"); §Decisiones confirmadas 3-4-6.
- **Descripción**: (a) extender el paso de revisión de `/dev-cycle` (revisor `qa-strict` de dos lentes) para que **emita salida ESTRUCTURADA** por criterio de aceptación (`T-XX` → criterio → ✓/✗ + gaps), en vez de prosa; (b) nueva **plantilla fija** `agent-kits/shared/review-report.template.md` (cabecera + checklist por criterio + gaps + tiempo de revisión); (c) publicar el comentario con la granularidad del volcado: **modo fase** → 1 comentario en el issue de la fase al cerrarla, agregando el pasa/falla de todas sus tareas; **modo tarea** → 1 comentario por issue de tarea; (d) cablear quién publica: el orquestador `/dev-cycle` invoca el paso de comentario de `jira-sync` con la salida del revisor. Idempotente vía `reviewComentado` en `jira-state.json`. Solo Modo B.
- **Complejidad**: Media-Alta (cambia el **contrato de salida** del revisor + fontanería de publicación + idempotencia; toca dos artefactos + plantilla nueva).
- **Esfuerzo**: 3,0 h · confianza **Baja-Media**
- **Previsión IA**: 300k in / 55k out tok · ~8 €
- **Coste**: (3,0 h × 50 €/h) + 7,94 € = **~158 €**
- **Impacto / áreas afectadas**: `commands/dev-cycle.md` (revisor de Modo B emite salida estructurada por criterio; el orquestador invoca el paso de comentario al cerrar fase/tarea), `skills/jira-sync/SKILL.md` (nuevo paso: publicar el comentario de revisión con granularidad fase/tarea + idempotencia `reviewComentado`), **nuevo** `agent-kits/shared/review-report.template.md`, `.claude/jira-state.json` (`reviewComentado` por `T-XX`/`fase-N`).
- **Dependencias y prerequisitos**: **`qa-strict` desplegado** (el revisor de dos lentes cuya salida se extiende y publica); C-02 (mapeo `fase-N` para saber a qué issue comentar en modo fase). En modo tarea puede publicarse sobre el issue de tarea existente.
- **Riesgos**: cambiar el contrato del revisor puede afectar a otros consumidores de su salida en `/dev-cycle`; `addCommentToJiraIssue` **no ejercitado end-to-end**; si el revisor devuelve prosa (no estructura), el paso no debe publicar un comentario mal formado (la spec exige degradar a "resumen + gaps" con aviso, sin inventar ✓/✗).
- **Incógnitas / preguntas abiertas**: ¿cómo está escrito hoy el paso de revisión en `dev-cycle.md` (cuánto cuesta imponerle un esquema de salida)? ¿el conector renderiza bien la checklist del comentario (ADF)? Un dry-run contra DM5985 con un `tasks.md` de juguete lo resuelve.

### C-07 — Worklog de revisión (entrada `[revisión]`, ambos modos)

- **Requisito origen**: spec §Características C-07; §Decisiones ("Worklog de revisión"); §Decisiones confirmadas 5; §Pruebas (caso de entrada `[revisión]` separada).
- **Descripción**: imputar el tiempo del revisor como **entrada de worklog separada** marcada `[revisión]`, distinta de la de implementación, en **ambos modos** (issue de fase / issue de tarea según granularidad). `worklog.py` gana un tipo/etiqueta de entrada; `jira-state.json` guarda el desglose implementación vs revisión (interno, para `/retro`). El total del issue en Jira = implementación + revisión; respeta el tope de jornada y el banco igual que las demás entradas.
- **Complejidad**: Media
- **Esfuerzo**: 1,75 h · confianza **Baja-Media** (incluye código+test en `worklog.py` para la entrada etiquetada + destino por modo; el resto es el desglose en el manifiesto).
- **Previsión IA**: 180k in / 30k out tok · ~5 €
- **Coste**: (1,75 h × 50 €/h) + 4,55 € = **~92 €**
- **Impacto / áreas afectadas**: `skills/jira-sync/scripts/worklog.py` (tipo/etiqueta `[revisión]` + destino issue por modo), `tests/test_worklog.py` (nuevo caso: el desglose implementación/revisión cuadra con el total del issue), `.claude/jira-state.json` (desglose implementación vs revisión).
- **Dependencias y prerequisitos**: **C-04** (worklog modo fase: destino del `issueKey` por fase) y **C-06** (de dónde sale el tiempo de revisión que se imputa). Indirectamente, `qa-strict` desplegado.
- **Riesgos**: acumular la entrada `[revisión]` **además** de las de implementación en el mismo issue refuerza la incógnita de "N worklogs por issue" (`addWorklogToJiraIssue` no ejercitado end-to-end); riesgo de doble imputación si la idempotencia (`reviewComentado`/desglose) no cubre la reejecución.
- **Incógnitas / preguntas abiertas**: ¿el conector separa/etiqueta worklogs de forma legible en Jira, o solo suma tiempo? La separación implementación/revisión se garantiza internamente en `jira-state.json` para `/retro` aunque Jira solo muestre el total.

---

## Comparativa

| # | Característica | Complejidad | Horas (base) | Coste € | Tokens (in/out) | Prioridad | Confianza |
|---|---------------|-------------|--------------|---------|-----------------|-----------|-----------|
| C-01 | Config de granularidad | Baja | 1,5 h | ~78 € | 140k (120/20) | Alta 🟠 | Alta |
| C-02 | Volcado en modo fase | Alta | 4,0 h | ~209 € | 380k (320/60) | Alta 🟠 | Media |
| C-03 | Progreso (comentarios + checklist) | Media-Alta | 3,0 h | ~157 € | 305k (260/45) | Media 🟡 | Baja |
| C-04 | Worklog y Done en modo fase | Media | 3,0 h | ~157 € | 330k (280/50) | Media 🟡 | Baja |
| C-05 | Read-back y coherencia | Media | 2,5 h | ~130 € | 235k (200/35) | Media 🟡 | Media |
| C-06 | Resultado del revisor → comentario en Jira | Media-Alta | 3,0 h | ~158 € | 355k (300/55) | Media 🟡 | Baja-Media |
| C-07 | Worklog de revisión (`[revisión]`) | Media | 1,75 h | ~92 € | 210k (180/30) | Media 🟡 | Baja-Media |
| | **Total** | | **18,75 h** | **~981 €** | **~1,96 M** | | |

> El **Total** de la tabla es coste **base** (18,75 h × 50 € + ~43 € de tokens). El presupuesto con margen está abajo.

---

## Presupuesto total

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 18,75 h × 50 €/h | 937,50 € |
| Margen de contingencia | +20 % sobre desarrollo base | 187,50 € |
| Tokens IA (input) | 1,66 M tok × 13,80 €/M ⚠️ | 22,91 € |
| Tokens IA (output) | 0,295 M tok × 69,00 €/M ⚠️ | 20,36 € |
| **Total estimado (con margen)** | | **~1.168 €** |

> ⚠️ El coste de tokens (~43 €, un 3,7 % del total) usa precios **supuestos** pendientes de verificar; una desviación del ±50 % en la tarifa de tokens mueve el total menos de un 2 %. El riesgo económico real está en las **horas** (integración con el conector y dependencia de `qa-strict`), no en los tokens.

---

## Productividad IA (humano vs. IA)

Compara el esfuerzo **humano** estimado con el tiempo que tardaría un **agente de IA** en implementarlo (más la supervisión humana). Cifras aproximadas; supuestos declarados.

| KPI | Valor |
|-----|-------|
| Horas humanas estimadas | 22,5 h *(18,75 h base)* |
| Horas IA (ejecución) | 7,2 h *(6,0 h base; supuesto)* |
| Supervisión humana | 1,8 h *(25 % de las horas IA)* |
| **Horas totales (IA + supervisión)** | **9,0 h** |
| Horas ahorradas | 13,5 h |
| **Ahorro** | **~60 %** |
| **Multiplicador de productividad** | **×2,5** |
| FTE equivalentes *(opcional)* | ~0,08 |

> Horas mostradas **con el margen de contingencia (+20 %)** ya aplicado sobre las horas base (humanas e IA). El trabajo es muy agente-friendly (sobre todo prosa dentro de una skill y un command que el agente ya conoce, más un cambio acotado en `worklog.py`), por eso el tiempo IA es bajo; la **supervisión se concentra en lo empírico**: validar contra el conector la checklist (C-03), los worklogs múltiples (C-04/C-07) y —nuevo— el comentario de revisión (C-06) y el worklog `[revisión]` (C-07), más comprobar que el nuevo contrato de salida del revisor no rompe otros consumidores en `/dev-cycle`. El multiplicador se mantiene ×2,5 porque parte del valor es criterio de diseño de prosa, que exige revisión humana.

---

## Recomendación

- **Veredicto**: **go CONDICIONADO** a un dry-run empírico contra el conector (proyecto de pruebas DM5985) que verifique las incógnitas de integración **antes** de dar por cerrados C-03/C-04 y —ahora también— C-06/C-07 (publicar un **comentario de revisión** y un **worklog `[revisión]`** de prueba, además de la checklist y el worklog de fase). Condición adicional para C-06/C-07: **`qa-strict` debe estar desplegado** (si no, esas dos quedan fuera de esta iteración). El coste sigue contenido (~1.168 €) y el trabajo, sobre todo prosa sobre skill/command existentes, es de bajo riesgo de ejecución; el riesgo vive en la integración y en el cambio de contrato del revisor.
- **Quick wins** (bajo coste, alto valor): **C-01** (config, 1,5 h, habilita todo el modo) y **C-02** (el volcado en sí, entrega el valor visible: menos issues por fase). **C-07** es barata (1,75 h) pero encadenada a C-04/C-06.
- **Costosas / a valorar**: **C-03**, **C-04**, **C-06** — no por horas, sino por dependencias no verificadas: `editJiraIssue` sobre descripción (C-03), múltiples worklogs por issue (C-04/C-07), `addComment`/`addWorklog` de revisión y cambio de contrato del revisor + dependencia de `qa-strict` (C-06/C-07). C-03 tiene plan B barato ("solo comentarios"); C-06 tiene degradación prevista ("resumen + gaps" si el revisor no da estructura).
- **Orden sugerido**: **C-01 → C-02 → C-03 → C-04 → C-05 → C-06 → C-07** — config primero (habilita el modo); luego el volcado (crea issues de fase y mapeo); el progreso (comentarios + checklist); el worklog/Done cuando ya hay issues a los que imputar; el read-back, que agrega lo que los anteriores producen; después **C-06** (necesita el mapeo `fase-N` y `qa-strict`, e introduce el comentario de revisión); y por último **C-07**, que depende de C-04 (destino del worklog por fase) y de C-06 (de dónde sale el tiempo de revisión). Tras C-02, hacer el dry-run antes de invertir en C-03/C-04; extenderlo a comentario + worklog de revisión antes de cerrar C-06/C-07.
- **Fuera de alcance recomendado**: se respeta el "Fuera" de la spec (modo mixto, subtareas por `T-XX` bajo la fase, migración de volcados existentes, **publicar la revisión en Modo A / superpowers**, y comentar gaps tarea a tarea intra-fase en modo fase). No añadir aquí; son specs futuras.

---

## Riesgos transversales

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| El conector no permite editar la descripción para la checklist (`editJiraIssue`) | Media | Alto (C-03) | Dry-run temprano; plan B "solo comentarios" ya previsto en la spec; documentar la limitación |
| El conector no acumula bien varias entradas de worklog en un issue (fase + `[revisión]`) | Media | Medio (C-04/C-07) | Verificar en DM5985 con issue desechable; si falla, replantear a "worklog agregado" y desglose solo interno |
| `addComment`/`addWorklog` de revisión no ejercitados end-to-end | Media | Medio (C-06/C-07) | Ampliar el dry-run a publicar un comentario de revisión y un worklog `[revisión]` de prueba antes de cerrar C-06/C-07 |
| `qa-strict` no desplegado o su revisor cambia de forma | Media | Alto (C-06/C-07) | Condición de aprobación explícita: sin `qa-strict`, C-06/C-07 quedan fuera; acoplar C-06 al contrato de salida versionado del revisor |
| Cambiar el contrato del revisor rompe otros consumidores de su salida en `/dev-cycle` | Baja | Medio (C-06) | Añadir el esquema estructurado sin quitar el resumen; degradación prevista si falta estructura (aviso, no ✓/✗ inventados) |
| Regresión del modo tarea al introducir el modo fase | Media | Alto | Test que fija el comportamiento actual (`"tarea"` bit a bit); manifiesto con claves separadas por modo |
| `tasks.md` con cabeceras de fase heterogéneas → parseo frágil | Media | Medio | Apoyarse en `ledger-lint.py` antes del volcado (la spec ya lo exige) |
| Cambio de granularidad con issues ya creados en el otro modo | Baja | Medio | Aviso de choque de manifiesto: continuar en el modo volcado o empezar limpio (spec §Manejo de errores) |

---

## Siguiente paso

Para **ejecutar** lo aprobado, genera el plan detallado con el agente **`planner`** (rellenará `improvement-plan.md` + `tasks.md` en esta misma carpeta y actualizará la fila **Plan** de esta evaluación y el campo `plan:` de la spec). Recomendación de aprobación: **las 7 características**, en el orden C-01 → C-02 → C-03 → C-04 → C-05 → C-06 → C-07, con una **puerta de dry-run** tras C-02 (ampliada a comentario + worklog de revisión antes de C-06/C-07) para validar las incógnitas del conector, y con la condición de que **`qa-strict` esté desplegado** para C-06/C-07. Las horas y costes por característica de esta evaluación se heredan tal cual; `planner` no re-estima desde cero.

---

## Changelog

- **2026-08-10** — Evaluación inicial (borrador) de la spec `jira-granularity`. 5 características, 14,0 h base (16,8 h con margen), ~871 €, ~1,39 M tokens. Veredicto: go condicionado a dry-run del conector.
- **2026-08-10** — **Re-evaluación tras ampliar la spec de 5 a 7 características** (añadidas C-06 "resultado del revisor → comentario en Jira" y C-07 "worklog de revisión `[revisión]`"). C-06 = 3,0 h base, C-07 = 1,75 h base. Total **18,75 h base (22,5 h con margen), ~1.168 €, ~1,96 M tokens**. Estado → `en-revision`. Veredicto: **go condicionado** (dry-run del conector ahora también para comentario + worklog de revisión; y `qa-strict` desplegado para C-06/C-07). C-01…C-05 sin cambios de cifras.

---

## Nota de precisión (revisión de diseño con el usuario · 2026-08-10)

Tras cerrar C-06/C-07 con el usuario se fijaron dos detalles que **no alteran materialmente el presupuesto** (quedan absorbidos por el margen de contingencia, <0,25 h): (1) el **bucle reviewer→implementer se acota a 3 intentos**, reutilizando el patrón del bucle qa→implementer ya implementado en `qa-strict` (es prosa en `commands/dev-cycle.md`, no lógica nueva); (2) el comentario de Jira publica el **resultado final + "revisión superada en N intento(s)"** (un comentario, no uno por intento) y el worklog `[revisión]` **acumula todas las pasadas**. Las horas de C-06 (3,0 h) y C-07 (1,75 h) se mantienen. El veredicto sigue **go condicionado** al dry-run del conector y a `qa-strict` desplegado.
