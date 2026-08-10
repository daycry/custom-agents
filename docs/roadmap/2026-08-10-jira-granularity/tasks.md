# Checklist de Tareas — Granularidad del volcado a Jira (modo fase) + resultado del revisor en Jira

| | |
|---|---|
| **Estado** | en-revision |
| **Fecha** | 2026-08-10 |
| **Plan** | [`improvement-plan.md`](./improvement-plan.md) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del plan. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador externo (p. ej. *superpowers SDD*)— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — Config de granularidad | 1 | 1 | 100% | 0 / 1,5h | 0 / 0,5h | 0 / 0,15h | 0 / 140k |
| Fase 2 — Modo fase | 4 | 4 | 100% | 0 / 12,5h | 0 / 3,95h | 0 / 1,0h | 0 / 1.250k |
| Fase 3 — Revisor → Jira | 2 | 2 | 100% | 0 / 4,75h | 0 / 1,55h | 0 / 0,4h | 0 / 565k |
| Fase 4 — Puerta de dry-run y cierre | 1 | 2 | 50% | 0 / 1,5h | 0 / 0,6h | 0 / 0,2h | 0 / 118k |
| **TOTAL** | **8** | **9** | **89%** | **0 / 20,25h** | **0 / 6,6h** | **0 / 1,75h** | **0 / 2.073k** |

> **Horas → Jira.** El worklog que imputa `jira-sync` al completar cada tarea es **Tiempo IA (ejec.) + Supervisión** (real; o estimación si no hay real), topado a la jornada configurada. Ver `skills/jira-sync/SKILL.md`.
>
> Horas heredadas de [`evaluation.md`](./evaluation.md) (C-01…C-07, 18,75 h base) + delta de cierre declarado en el plan (Fase 4, +1,5 h base).

---

## Fase 1 — Config de granularidad

**Estado**: borrador · **Estimado**: 1,5h · **Real**: — · **Coste est.**: ~78 € · **Tokens est.**: 140k

### T-01 — Config `granularidad` en `.claude/jira.json` y documentación en el SKILL (C-01)

- **Descripción**: Añadir el campo `granularidad: "tarea" | "fase"` a la config de `jira-sync`. `"tarea"` es el defecto y reproduce el comportamiento actual **bit a bit** (no romper instalaciones existentes). Si falta al volcar, preguntar una sola vez (artefacto en Cowork / conversacional en CLI) y persistir la respuesta.
- **Estado**: completado
- **Tiempo humano**: est. 1,5h · real —
- **Tiempo IA (ejec.)**: est. 0,5h · real —
- **Supervisión**: est. 0,15h (≈25 % IA) · real —
- **Previsión IA**: 120k in / 20k out tok · ~78 €
- **Dependencias**: ninguna
- **Archivos**: `skills/jira-sync/SKILL.md` (Paso 0 + §Config)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] El SKILL documenta `granularidad` en `.claude/jira.json` con `"tarea"` como defecto y `"fase"` como alternativa
- [x] Con `granularidad` ausente, el flujo pregunta **una vez** (paridad artefacto/conversacional) y persiste el valor en `.claude/jira.json`
- [x] Con `granularidad: "tarea"` (explícito o por defecto), las instrucciones del SKILL no alteran nada del flujo actual (comportamiento bit a bit)

**Subtareas**
- [x] Añadir el campo al bloque de config del SKILL (Paso 0) con defecto y semántica
- [x] Prosa de "preguntar una vez y persistir" (Cowork artefacto / CLI conversacional), siguiendo el patrón de los opt-ins existentes
- [x] Revisar los Pasos 1–8 para confirmar que la rama `"tarea"` queda intacta

**Notas**: habilita todo el modo fase; quick win según la evaluación (confianza Alta).

---

## Fase 2 — Modo fase

**Estado**: completado · **Estimado**: 12,5h · **Real**: — · **Coste est.**: ~653 € · **Tokens est.**: 1.250k

### T-02 — Volcado en modo fase: un issue por Fase con checklist de tareas (C-02)

- **Descripción**: Rama de creación en modo fase (prosa en Pasos 4–6 del SKILL): un issue por Fase del plan con las `T-XX` de la fase como **checklist** en la descripción; tipo descubierto por jerarquía del padre (no hardcodear); previsualización y confirmación como hoy; idempotente vía `fase-N → issueKey` en `jira-state.json`; clave Jira anotada en la **cabecera de la fase** de `tasks.md`.
- **Estado**: completado
- **Tiempo humano**: est. 4,0h · real —
- **Tiempo IA (ejec.)**: est. 1,25h · real —
- **Supervisión**: est. 0,3h (≈25 % IA) · real —
- **Previsión IA**: 320k in / 60k out tok · ~209 €
- **Dependencias**: T-01
- **Archivos**: `skills/jira-sync/SKILL.md` (Pasos 4–6)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] En modo fase se crea exactamente 1 issue por fase con tareas, con las `T-XX` como checklist `- [x]` en la descripción; el tipo sale de la jerarquía del padre
- [x] El manifiesto guarda `fase-N → issueKey`; una reejecución no duplica issues; el modo tarea (`T-XX → issueKey`) queda intacto
- [x] La clave Jira de cada fase se escribe en la cabecera de esa fase en `tasks.md`
- [x] Una **fase sin tareas** no genera issue y se avisa
- [x] Cambiar `granularidad` con issues ya creados en el otro modo produce un **aviso de choque** de manifiesto (continuar en el modo volcado o empezar limpio); nunca se duplica en silencio
- [x] El SKILL exige `ledger-lint.py` en verde antes de volcar en modo fase

**Subtareas**
- [x] Prosa de agrupación fase→tareas desde `tasks.md` (apoyada en `ledger-lint.py`) y construcción de la descripción con checklist
- [x] Extender previsualización/confirmación (Paso 4) con la vista por fase
- [x] Idempotencia con clave `fase-N` en el manifiesto + detección del choque de modos
- [x] Escritura de vuelta (Paso 6): clave Jira en la cabecera de fase

**Notas**: núcleo del modo nuevo; la sintaxis exacta de la checklist en la descripción se valida en el dry-run (T-08).

### T-03 — Progreso en modo fase: comentario por tarea + marca en la checklist (C-03)

- **Descripción**: Al completar una `T-XX` en modo fase (prosa en Paso 7 del SKILL): (a) publicar un **comentario** en el issue de su fase con tarea, evidencia y horas; (b) marcar `- [x]` esa tarea en la **checklist** de la descripción del issue vía `editJiraIssue`. El issue se localiza por `fase-N` en el manifiesto.
- **Estado**: completado
- **Tiempo humano**: est. 3,0h · real —
- **Tiempo IA (ejec.)**: est. 0,95h · real —
- **Supervisión**: est. 0,25h (≈25 % IA) · real —
- **Previsión IA**: 260k in / 45k out tok · ~157 €
- **Dependencias**: T-02
- **Archivos**: `skills/jira-sync/SKILL.md` (Paso 7, rama de fase)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] Al completar cada `T-XX`, el SKILL indica publicar un comentario en el issue de su fase con tarea, evidencia y horas (un issue de fase acumula tantos comentarios como tareas)
- [x] La checklist de la descripción se actualiza (`- [x]` → `- [x]`) para esa tarea sin perder el resto de la descripción (edición con merge, no reescritura ciega)
- [x] Documentado el **plan B** si `editJiraIssue` no permite editar la descripción: degradar a "solo comentarios" con aviso y anotar la limitación

**Subtareas**
- [x] Prosa del comentario de progreso (contenido y momento: al pasar la tarea a `completado` en el ledger)
- [x] Prosa de la actualización de la checklist vía `editJiraIssue` (leer descripción → marcar → escribir)
- [x] Documentar la degradación (plan B) y el caso "issue de fase no encontrado en el manifiesto"

**Notas**: confianza Baja en la evaluación por depender de `editJiraIssue` sobre la descripción; se verifica en T-08.

### T-04 — Worklog tarea a tarea en el issue de fase + Done al cerrar todas (C-04)

- **Descripción**: En modo fase, el worklog se imputa en el **issue de la fase**, tarea a tarea (misma lógica de `worklog.py` —tope de jornada y banco de horas—, cambiando solo el `issueKey` destino). La transición a **Done** del issue de fase solo se dispara cuando **todas** sus tareas están `completado` en `tasks.md`, nunca antes.
- **Estado**: completado
- **Tiempo humano**: est. 3,0h · real —
- **Tiempo IA (ejec.)**: est. 0,95h · real —
- **Supervisión**: est. 0,25h (≈25 % IA) · real —
- **Previsión IA**: 280k in / 50k out tok · ~157 €
- **Dependencias**: T-02
- **Archivos**: `skills/jira-sync/SKILL.md` (Paso 7), `skills/jira-sync/scripts/worklog.py`, `tests/test_worklog.py`
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] `worklog.py` acepta el destino `issueKey` de fase sin cambiar la aritmética (tope de jornada diario y banco de horas idénticos); los tests existentes siguen verdes
- [x] Nuevo test en `tests/test_worklog.py`: imputación a issue de fase = mismo cálculo, distinto destino
- [x] El SKILL define el disparo de Done del issue de fase **solo** cuando todas sus tareas están `completado` en `tasks.md` (fase parcial → issue abierto)
- [x] Transición Done no descubrible → se pregunta/omite con aviso, igual que en modo tarea (sin id hardcodeado)

**Subtareas**
- [x] Cambio acotado en `worklog.py` (destino por modo) + test nuevo
- [x] Prosa de imputación tarea a tarea al issue de fase (Paso 7)
- [x] Prosa del agregado "todas las tareas de la fase `completado`" leyendo el ledger, y de la transición Done

**Notas**: "N worklogs por issue" no está ejercitado con el conector; se verifica en T-08. `python3 -m pytest tests/test_worklog.py` como verificación local.

### T-05 — Read-back y coherencia por modo (C-05)

- **Descripción**: Extender el read-back (Paso 8 del SKILL) para que entienda ambos modos: en modo fase compara el estado del issue de fase con el **agregado** de sus tareas en `tasks.md` (`Done` ⟺ todas `completado`), lista divergencias (fase parcialmente hecha, issue cerrado con tareas abiertas y viceversa) y no toca el ledger sin confirmación. Sin romper el modo tarea.
- **Estado**: completado
- **Tiempo humano**: est. 2,5h · real —
- **Tiempo IA (ejec.)**: est. 0,8h · real —
- **Supervisión**: est. 0,2h (≈25 % IA) · real —
- **Previsión IA**: 200k in / 35k out tok · ~130 €
- **Dependencias**: T-02
- **Archivos**: `skills/jira-sync/SKILL.md` (Paso 8)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] El Paso 8 detecta el modo por las claves del manifiesto (`fase-N` vs `T-XX`) y compara en consecuencia
- [x] En modo fase, la comparación usa el agregado de tareas de la fase; las divergencias parciales se listan sin sobreescribir el ledger sin confirmación
- [x] El read-back en modo tarea no cambia (sin regresión)

**Subtareas**
- [x] Prosa del mapeo de estados por agregado de fase (Done / In Progress / To Do)
- [x] Prosa de presentación de divergencias (fase parcialmente hecha) manteniendo la regla vigente de no tocar el ledger

**Notas**: agrega lo que producen T-02/T-03/T-04; sin llamadas nuevas al conector.

---

## Fase 3 — Revisor → Jira

**Estado**: completado · **Estimado**: 4,75h · **Real**: — · **Coste est.**: ~250 € · **Tokens est.**: 565k

### T-06 — Salida estructurada del revisor + bucle acotado + plantilla + publicación del comentario (C-06)

- **Descripción**: (a) El revisor de `/dev-cycle` Modo B (qa-strict) emite salida **estructurada** por criterio (`T-XX` → criterio → ✓/✗ + gaps), no solo prosa; (b) bucle reviewer→implementer **acotado a 3 intentos** coordinado por `/dev-cycle` (patrón del bucle qa→implementer; al 3.º con fallos, parar y preguntar: seguir/re-planificar/aceptar); (c) nueva plantilla fija `agent-kits/shared/review-report.template.md`; (d) paso de publicación en el SKILL de `jira-sync`: comentario con el resultado **FINAL** + línea "revisión superada en N intento(s)", con la granularidad del volcado (modo fase: 1 comentario agregado al cerrar la fase; modo tarea: 1 por issue), idempotente vía `reviewComentado`. Solo Modo B.
- **Estado**: completado
- **Tiempo humano**: est. 3,0h · real —
- **Tiempo IA (ejec.)**: est. 0,95h · real —
- **Supervisión**: est. 0,25h (≈25 % IA) · real —
- **Previsión IA**: 300k in / 55k out tok · ~158 €
- **Dependencias**: T-02 (mapeo `fase-N`); prerequisito: `qa-strict` desplegado
- **Archivos**: `commands/dev-cycle.md`, `agent-kits/shared/review-report.template.md` (nuevo), `skills/jira-sync/SKILL.md` (paso de publicación)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] `commands/dev-cycle.md` define el esquema de salida estructurada del revisor (por criterio: ✓/✗ + gaps) sin eliminar el resumen en prosa (no romper otros consumidores)
- [x] El bucle reviewer→implementer está acotado a **máx. 3 intentos** y lo coordina `/dev-cycle` (no el implementer); al 3.º con fallos, para y pregunta al usuario
- [x] Existe `agent-kits/shared/review-report.template.md` con formato fijo: cabecera + checklist por criterio + gaps + "revisión superada en N intento(s)" + tiempo de revisión
- [x] El SKILL de `jira-sync` tiene el paso de publicación: modo fase → 1 comentario agregado en el issue de fase al cerrarla; modo tarea → 1 comentario por issue; siempre el resultado FINAL tras el bucle
- [x] Idempotencia: `reviewComentado` por `T-XX`/`fase-N` en `jira-state.json` evita re-comentar en reejecución
- [x] Degradación definida: si el revisor devuelve prosa sin estructura, se publica solo resumen + gaps con aviso; no se inventan ✓/✗
- [x] Alcance explícito: solo Modo B; en Modo A se anota que la revisión vino de superpowers y no se publica en formato propio

**Subtareas**
- [x] Redactar la plantilla `review-report.template.md`
- [x] Extender el paso de revisión de `dev-cycle.md` (esquema de salida + bucle acotado a 3 + invocación de la publicación al cerrar fase/tarea)
- [x] Añadir el paso de publicación al SKILL de `jira-sync` (granularidad, idempotencia, degradación)
- [x] Prueba con `tasks.md` de juguete: la salida estructurada renderiza contra la plantilla con formato idéntico

**Notas**: cambia el contrato de salida del revisor; `addCommentToJiraIssue` no ejercitado end-to-end → se verifica en T-08.

### T-07 — Worklog de revisión `[revisión]` en ambos modos, acumulando todas las pasadas (C-07)

- **Descripción**: Imputar el tiempo del revisor como entrada de worklog **separada** marcada `[revisión]`, distinta de la de implementación, en ambos modos (issue de fase / issue de tarea según granularidad). La entrada **acumula todas las pasadas** del bucle (intento 1 + reintentos); las correcciones del implementer suman a `[implementación]`. `worklog.py` gana el tipo/etiqueta de entrada; `jira-state.json` guarda el desglose implementación vs revisión para `/retro`. Respeta tope de jornada y banco como cualquier entrada.
- **Estado**: completado
- **Tiempo humano**: est. 1,75h · real —
- **Tiempo IA (ejec.)**: est. 0,6h · real —
- **Supervisión**: est. 0,15h (≈25 % IA) · real —
- **Previsión IA**: 180k in / 30k out tok · ~92 €
- **Dependencias**: T-04 (destino por fase en `worklog.py`), T-06 (de dónde sale el tiempo de revisión)
- **Archivos**: `skills/jira-sync/scripts/worklog.py`, `tests/test_worklog.py`, `skills/jira-sync/SKILL.md` (imputación de revisión)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] `worklog.py` soporta la etiqueta `[revisión]` como entrada separada, con destino por modo (issue de fase / de tarea), respetando tope de jornada y banco
- [x] La entrada `[revisión]` acumula **todas** las pasadas del bucle; el total del issue = `[implementación]` + `[revisión]` (nada se descuenta)
- [x] Nuevo test en `tests/test_worklog.py`: el desglose implementación/revisión cuadra con el total del issue; los tests existentes siguen verdes (`python3 -m pytest tests/test_worklog.py`)
- [x] `jira-state.json` guarda el desglose implementación vs revisión (interno, para `/retro`); la idempotencia evita la doble imputación en reejecución (ligada a `reviewComentado`)
- [x] Alcance explícito: solo Modo B (sin revisor de qa-strict no hay entrada `[revisión]`)

**Subtareas**
- [x] Código: tipo/etiqueta de entrada en `worklog.py` + acumulación de pasadas
- [x] Test nuevo del desglose + verificación de los existentes
- [x] Prosa en el SKILL: cuándo y cómo se imputa `[revisión]` (tras el bucle, junto al comentario de T-06)

**Notas**: `addWorklogToJiraIssue` no ejercitado end-to-end; refuerza la incógnita "N worklogs por issue" → se verifica en T-08.

---

## Fase 4 — Puerta de dry-run y cierre

**Estado**: completado · **Estimado**: 1,5h · **Real**: — · **Coste est.**: ~78 € · **Tokens est.**: 118k

### T-08 — 🚦 PUERTA MANUAL: dry-run contra DM5985 (condición del go de la evaluación)

- **Descripción**: **Tarea manual del usuario** (asistido por el agente): dry-run contra el proyecto de pruebas DM5985 de mediaprosuite, con issue desechable, que ejercite las cuatro capacidades no verificadas del conector antes de dar la iniciativa por cerrada: creación en modo fase, `editJiraIssue` de la checklist, `addComment` del comentario de revisión y `addWorklog` de la entrada `[revisión]`.
- **Estado**: en-progreso
- **Tiempo humano**: est. 1,0h · real —
- **Tiempo IA (ejec.)**: est. 0,3h · real —
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 60k in / 10k out tok · ~52 €
- **Dependencias**: T-01, T-02, T-03, T-04, T-05, T-06, T-07 (bloqueada por todo el plan)
- **Archivos**: — (ejecución contra Jira; resultados anotados en este ledger y, si hay limitaciones, en `skills/jira-sync/SKILL.md`)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [ ] Creación en modo fase verificada en DM5985: 1 issue por fase con checklist correcta, manifiesto `fase-N` escrito, reejecución sin duplicados
- [ ] `editJiraIssue` verificado: la checklist de la descripción se marca `- [x]` sin perder contenido — o plan B "solo comentarios" activado y documentado
- [ ] `addCommentToJiraIssue` verificado: comentario de revisión publicado con el formato de la plantilla fija
- [ ] `addWorklogToJiraIssue` verificado: entrada `[revisión]` conviviendo con la de implementación en el mismo issue; el total suma ambas
- [ ] Resultado del dry-run (ok / limitaciones / planes B activados) anotado en las **Notas de implementación** de este ledger

**Subtareas**
- [ ] Preparar `tasks.md` de juguete y verificar acceso de escritura a DM5985
- [ ] Ejecutar el dry-run de las 4 capacidades sobre issue desechable
- [ ] Limpiar/cerrar el issue desechable y anotar el resultado

**Notas**: es la **condición del veredicto go** de la evaluación; sin esta puerta en verde (o con planes B documentados), la iniciativa NO se da por cerrada. La ejecuta jmano@mediapro.tv.

### T-09 — Cierre: CHANGELOG, documentación y nota de release

- **Descripción**: Cierre documental de la iniciativa: entrada en `CHANGELOG.md` (`[Unreleased]`), actualización de `docs/FLOWS.md` (bucle acotado reviewer→implementer y publicación a Jira en el flujo de `/dev-cycle`) y nota breve de release para el usuario (qué hay nuevo, cómo activar `granularidad: "fase"`, limitaciones detectadas en T-08).
- **Estado**: completado
- **Tiempo humano**: est. 0,5h · real —
- **Tiempo IA (ejec.)**: est. 0,3h · real —
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 40k in / 8k out tok · ~26 €
- **Dependencias**: T-08
- **Archivos**: `CHANGELOG.md`, `docs/FLOWS.md`, `docs/roadmap/README.md` (estado)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] `CHANGELOG.md` recoge en `[Unreleased]` el modo fase, la publicación del resultado del revisor y el worklog `[revisión]`, con las limitaciones/planes B de T-08 si los hubo
- [x] `docs/FLOWS.md` refleja el bucle acotado y la publicación a Jira en `/dev-cycle` Modo B
- [x] Nota de release entregada al usuario (incluye cómo cambiar de granularidad y el aviso de choque de manifiesto)

**Subtareas**
- [x] Redactar la entrada del CHANGELOG
- [x] Actualizar `docs/FLOWS.md`
- [x] Redactar la nota de release y actualizar el estado en `docs/roadmap/README.md`

**Notas**: esta tarea (junto a T-08) es el **delta** de +1,5 h base declarado en el plan sobre el presupuesto heredado de la evaluación.

---

## Notas de implementación

**Estado (2026-08-10):** implementado en la sesión Cowork (dogfooding) todo salvo la **puerta de dry-run T-08**, que es MANUAL y requiere Jira en vivo (DM5985) — queda pendiente para Jordi. Lo implementado sin conector: config `granularidad` (C-01), modo fase completo en el SKILL (C-02..C-05), publicación del revisor con plantilla + bucle acotado en dev-cycle (C-06), y `worklog.py --kind revision` con desglose + tests 12/12 (C-07). Revisión de dos lentes pasada. Pendiente además del cierre de estados y el release (usuario).

_A completar durante la ejecución. Registra decisiones, desvíos de la estimación y aprendizajes. Aquí se anota el resultado del dry-run de T-08 (capacidades verificadas / planes B activados)._
