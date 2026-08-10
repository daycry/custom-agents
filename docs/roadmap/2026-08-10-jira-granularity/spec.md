---
spec: jira-granularity
descripcion: Añadir a jira-sync la opción de volcar el plan con granularidad por FASE (un issue por fase con sus tareas como checklist) además del modo por TAREA actual, con comentarios/worklog/Done coherentes con cada modo, y publicar en Jira el resultado del agente revisor (comentario por criterio + worklog de revisión) en ambos modos
estado: aprobada          # borrador | aprobada | implementada | obsoleta
creado: 2026-08-10
actualizado: 2026-08-10
evaluacion: evaluation.md
plan: improvement-plan.md
---

# Granularidad del volcado a Jira: por fase o por tarea

> **Evaluación:** [`evaluation.md`](evaluation.md) — 7 características · 18,75 h base (22,5 h con margen), ~1.168 €, ~1,96 M tokens; veredicto go CONDICIONADO a dry-run del conector (comentario + worklog de revisión incl.) y a `qa-strict` desplegado para C-06/C-07 (en-revision).
> **Plan de implementación:** [`improvement-plan.md`](improvement-plan.md) + [`tasks.md`](tasks.md) — 4 fases · 9 tareas · 20,25 h base (24,3 h con margen) · ~1.261 € · puerta de dry-run contra DM5985 antes del cierre (T-08)

> **Terminología:** «modo tarea» = un issue de Jira por cada `T-XX` (comportamiento actual). «modo fase» = un issue por cada Fase del plan, con sus tareas como checklist en la descripción. «ledger» = `tasks.md`, fuente única de progreso. «revisor» = el agente de revisión adversarial (dos lentes) que corre en `/dev-cycle` Modo B tras la implementación (iniciativa `qa-strict`, C-06). «worklog de revisión» = entrada de tiempo separada, marcada `[revisión]`, distinta de la de implementación.

## Contexto y objetivo

Hoy `jira-sync` crea **un issue por cada tarea `T-XX`** del plan. Para equipos que trabajan Jira a nivel de fase/entregable, eso genera demasiados issues. El objetivo es ofrecer **dos granularidades** elegibles: la actual (por tarea) y una nueva **por fase** — un issue por fase, con las tareas de esa fase como checklist en su descripción. El progreso (comentarios, worklog, transición a Done) se adapta a la granularidad elegida sin perder el desglose por tarea. El ledger `tasks.md` sigue siendo la fuente de verdad en ambos modos; Jira es el espejo para el equipo. Reutiliza toda la maquinaria existente (opt-in, previsualización, idempotencia por manifiesto, `worklog.py`, descubrimiento de tipos por jerarquía).

## Decisiones de diseño

| Decisión | Elección | Motivo |
|---|---|---|
| Dónde se elige | **`.claude/jira.json` → `granularidad: "tarea" \| "fase"`; si falta, preguntar la primera vez** | Coherente con los opt-ins existentes; persistente y de un clic la próxima vez |
| Modo fase — estructura | **Un issue por Fase; las `T-XX` de la fase van como checklist (lista de tareas) en la descripción del issue** | Un entregable por fase, con su desglose visible dentro |
| Tipo de issue (modo fase) | **Descubierto por jerarquía del padre, igual que hoy** (Épica→Tarea, Tarea→Subtarea); NO hardcodear | Regla vigente del SKILL; el modo fase no la cambia |
| Comentarios (modo fase) | **Al completar cada `T-XX`, un comentario en el issue de SU fase** (con tarea, evidencia, horas). Un issue de fase acumula tantos comentarios de progreso como tareas tenga | Traza el avance tarea a tarea aunque el issue sea de fase |
| Worklog (modo fase) | **Se imputa en el issue de la fase, tarea a tarea** (cada `T-XX` imputa su IA+supervisión al issue de su fase al completarse) | No se pierde el desglose temporal; respeta el tope de jornada diario y el banco de horas existentes |
| Checklist de la descripción (modo fase) | **Se actualiza al completar cada tarea** (marca `- [x]` la tarea en la descripción del issue), además del comentario | La descripción refleja el estado sin abrir los comentarios |
| Transición a Done (modo fase) | **El issue de fase pasa a Done cuando TODAS sus tareas están `completado` en `tasks.md`**, no antes | Un entregable está hecho cuando lo están todas sus partes |
| Idempotencia | **Manifiesto `jira-state.json` con clave por fase en modo fase (`fase-N → issueKey`), por tarea en modo tarea (actual)** | Evita duplicados en reejecución en ambos modos |
| Escritura en `tasks.md` | **Modo fase: la clave Jira de la fase se anota en la cabecera de la fase; modo tarea: por tarea (actual)** | El ledger sabe a qué issue pertenece cada cosa |
| Resultado del revisor → Jira | **Comentario con la salida del revisor, con la granularidad del volcado** (modo fase: 1 comentario al cerrar la fase; modo tarea: 1 por tarea) | Que el pasa/falla por criterio quede registrado en Jira, no solo en el chat |
| Formato del comentario de revisión | **Plantilla FIJA en el kit** (`agent-kits/shared/review-report.template.md`); el revisor emite salida ESTRUCTURADA por criterio (`T-XX` → criterio → ✓/✗) que se renderiza contra ella | Comentario idéntico en formato siempre; exige que el revisor devuelva estructura, no prosa |
| Cadencia de la revisión (modo fase) | **Una sola pasada al cerrar la fase**, sobre el diff de todas sus tareas; comentario agregado con el pasa/falla por criterio de cada tarea | Más barato en tokens; coherente con «una vez acabe la fase» |
| Worklog de revisión | **Entrada separada `[revisión]` imputada en AMBOS modos** (issue de fase en modo fase; issue de tarea en modo tarea). Suma al total del issue como cualquier worklog; la separación implementación/revisión es interna (`jira-state.json`) para `/retro` | El tiempo total del issue es implementación+revisión; el desglose no se pierde y no distorsiona la calibración |
| Alcance del modo | **Solo Modo B (cadena nativa)** | En Modo A superpowers hace su propia revisión con otro formato; no hay salida estructurada nuestra que publicar |
| Bucle reviewer→implementer | **Acotado a máx. 3 intentos** (reutiliza el patrón del bucle qa→implementer de qa-strict): reviewer→corrige→re-review; al 3.º con fallos de corrección, parar y preguntar al usuario (seguir/re-planificar/aceptar). Lo coordina `/dev-cycle`, no el implementer | Evita bucles infinitos y da consistencia con el bucle de qa; el implementer no "sabe" solo — el orquestador cierra el ciclo |
| Qué se comenta tras el bucle | **El resultado FINAL** (pasa/falla por criterio ya definitivo) **+ una línea "revisión superada en N intento(s)"** | Jira legible (un comentario, no uno por intento) sin perder la señal de que hubo correcciones |
| Tiempo acumulado | **El worklog `[revisión]` acumula TODAS las pasadas del reviewer** (intento 1 + reintentos); las correcciones del implementer suman a su entrada `[implementación]`. Ambas al total del issue | Es tiempo real; el desglose separa implementación vs revisión, pero nada se descuenta |

## Arquitectura y componentes

Se toca: `skills/jira-sync/SKILL.md` (modo fase: creación, comentarios, worklog, Done, read-back; y el nuevo paso de publicar el resultado del revisor), `skills/jira-sync/scripts/worklog.py` + sus tests (destino por fase; entrada `[revisión]` separada), `.claude/jira.json` (config `granularidad`), `.claude/jira-state.json` (claves `fase-N`, `reviewComentado`, desglose implementación/revisión), `commands/dev-cycle.md` (el revisor de Modo B emite salida estructurada y, al cerrar fase/tarea, invoca el paso de comentario+worklog de jira-sync), y **nuevo** `agent-kits/shared/review-report.template.md` (plantilla fija del comentario de revisión). Se reutiliza: opt-in, previsualización, descubrimiento de tipos por jerarquía, tope de jornada/banco de `worklog.py`, e idempotencia por manifiesto. Depende de la revisión de dos lentes ya implementada en `qa-strict`.

## Características (alcance detallado)

| ID | Característica | Detalle |
|----|---------------|---------|
| C-01 | Config de granularidad | Campo `granularidad` en `.claude/jira.json` (`"tarea"` por defecto para no romper instalaciones; `"fase"` nuevo). Si no existe al volcar, preguntar una vez (artefacto en Cowork / conversacional en CLI) y persistir. Documentado en el SKILL |
| C-02 | Volcado en modo fase | Al crear: un issue por Fase del plan; descripción con las `T-XX` de la fase como **checklist**; tipo descubierto por jerarquía; previsualización y confirmación como hoy; idempotente vía `fase-N → issueKey` en el manifiesto. Escribe la clave Jira en la cabecera de cada fase de `tasks.md` |
| C-03 | Progreso en modo fase (comentarios + checklist) | Al completar una `T-XX`: (a) **comentario** en el issue de su fase con tarea, evidencia y horas; (b) marca `- [x]` esa tarea en la **checklist** de la descripción del issue. Localiza el issue por `fase-N` en el manifiesto |
| C-04 | Worklog y Done en modo fase | Worklog imputado en el issue de la fase, **tarea a tarea** (misma lógica de `worklog.py`, tope de jornada y banco, sin cambios en el script salvo el destino del issueKey). Transición a **Done** del issue de fase solo cuando todas sus tareas están `completado` en `tasks.md` |
| C-05 | Read-back y coherencia por modo | El read-back (Paso 8) y la comprobación de coherencia entienden ambos modos: en modo fase compara el estado del issue de fase con el agregado de sus tareas. Sin romper el modo tarea |
| C-06 | Resultado del revisor → comentario en Jira (plantilla + salida estructurada + bucle acotado) | (a) Extender el paso de revisión de `/dev-cycle` (qa-strict C-06) para que **emita salida estructurada** por criterio de aceptación (`T-XX` → criterio → ✓/✗ + gaps), no solo prosa. (b) **Bucle reviewer→implementer acotado a 3 intentos** (patrón del bucle qa→implementer): si hay fallos de corrección, la tarea vuelve a `implementer` con los gaps y el reviewer re-ejecuta; al 3.º con fallos, parar y preguntar. Lo coordina `/dev-cycle`. (c) Nueva **plantilla fija** `agent-kits/shared/review-report.template.md` (cabecera + checklist por criterio + gaps + "revisión superada en N intento(s)" + tiempo de revisión). (d) Publicar el comentario con el **resultado FINAL** (tras el bucle) y la granularidad del volcado: **modo fase** → un comentario en el issue de la fase al cerrarla, agregando el pasa/falla por criterio de todas sus tareas; **modo tarea** → un comentario por issue de tarea. (e) Lo publica el orquestador `/dev-cycle` (o `implementer` al cerrar) invocando el paso de comentario de `jira-sync`. Idempotente vía `jira-state.json` (`reviewComentado`; no re-comentar). Solo Modo B |
| C-07 | Worklog de revisión (entrada `[revisión]`, ambos modos, acumula todas las pasadas) | Imputar el tiempo del revisor como **entrada de worklog separada** marcada `[revisión]`, distinta de la de implementación, en **ambos modos** (issue de fase / issue de tarea según granularidad). **Acumula todas las pasadas del bucle** (intento 1 + reintentos); las correcciones del implementer suman a la entrada `[implementación]`. `worklog.py` gana un tipo/etiqueta de entrada; `jira-state.json` guarda el desglose implementación vs revisión. El total del issue en Jira = implementación + revisión; respeta el tope de jornada y el banco igual que las demás entradas |

## Alcance

- **Dentro (esta iteración):** C-01 … C-07 — granularidad por fase/tarea + publicación del resultado del revisor (comentario + worklog) en ambos modos.
- **Fuera (siguientes specs):**
  - Modo **mixto** (algunas fases por tarea, otras por fase) — innecesario de momento; añade complejidad de manifiesto.
  - Crear subtareas de Jira por cada `T-XX` *bajo* el issue de fase (jerarquía de dos niveles) — es una tercera granularidad; se valora si alguien la pide.
  - Migrar un volcado ya hecho de un modo a otro — el cambio de granularidad aplica a volcados nuevos; cambiar con issues ya creados se documenta como "empieza carpeta nueva o borra el manifiesto".
  - Publicar el resultado del revisor en **Modo A** (superpowers): su revisión tiene otro formato; quedaría para una spec de integración SDD.
  - Comentar en Jira los gaps de la revisión **tarea a tarea en modo fase** (revisión fina intra-fase): se descartó por coste; en modo fase la revisión es una pasada al cerrar la fase.

## Manejo de errores

| Caso | Comportamiento |
|---|---|
| Se cambia `granularidad` con issues ya creados en el otro modo | Avisar del choque: el manifiesto tiene claves del modo anterior; ofrecer continuar en el modo ya volcado o empezar limpio (no duplicar en silencio) |
| Fase sin tareas | No se crea issue de fase vacío; se avisa |
| Una `T-XX` no mapea a ninguna fase (ledger mal formado) | `ledger-lint.py` ya lo detecta; jira-sync se apoya en él antes de volcar en modo fase |
| Tope de jornada / banco de horas en modo fase | Igual que hoy: `worklog.py` decide; solo cambia a qué issueKey (el de la fase) se imputa |
| Transición Done no descubrible en el issue de fase | Igual que en modo tarea: se pregunta/omite con aviso; no se fuerza un id fijo |
| El revisor devuelve prosa en vez de estructura | El paso de comentario no publica un comentario mal formado: si falta la estructura por criterio, se registra un aviso y se publica solo el resumen + gaps; no se inventan ✓/✗ |
| Re-ejecución tras publicar el comentario de revisión | Idempotente: `jira-state.json` marca `reviewComentado` por `T-XX`/`fase-N`; no se duplica el comentario ni se re-imputa el worklog `[revisión]` |
| Revisión en Modo A (superpowers) | La publicación no aplica; se anota que el resultado de revisión de este ciclo vino de superpowers y no se volcó en formato propio |

## Pruebas

- `worklog.py`: los tests existentes siguen verdes; añadir caso de imputación a issue de fase (mismo cálculo, distinto destino) y caso de **entrada `[revisión]` separada** (el desglose implementación/revisión cuadra con el total del issue).
- Prueba de manifiesto: modo fase escribe `fase-N → issueKey`; reejecución no duplica; modo tarea intacto; `reviewComentado` evita re-comentar/re-imputar la revisión.
- Dry-run/previsualización en ambos modos contra la instancia real (mediaprosuite, proyecto de pruebas DM5985) sin crear de verdad, o creando en un issue desechable — incluye publicar un comentario de revisión y un worklog `[revisión]` de prueba.
- Salida estructurada del revisor: con un tasks.md de juguete, el revisor devuelve `T-XX` → criterio → ✓/✗ y el comentario se renderiza contra la plantilla fija (mismo formato siempre).
- Coherencia: `ledger-lint.py` valida el ledger antes del volcado en modo fase.
- Verificación de que `granularidad` ausente → pregunta una vez y persiste; `"tarea"` reproduce el comportamiento actual bit a bit.

## Referencias

- `skills/jira-sync/SKILL.md` (Pasos 1–8, config, manifiesto) y `skills/jira-sync/scripts/worklog.py`.
- [[atlassian-mediaprosuite]] — cloudId, proyecto de pruebas DM5985 para dry-run.
- [[preferencias-jordi]] — no hardcodear tipos, opt-ins persistentes, paridad artefacto/conversacional.

## Decisiones confirmadas (revisión del usuario · 2026-08-10)

1. Ofrecer las **dos granularidades** (por tarea y por fase). **Confirmado.**
2. En modo fase, **un comentario por cada tarea completada** en el issue de la fase; worklog imputado en el issue de la fase tarea a tarea; Done al cerrar todas las tareas. **Confirmado** en conversación.
3. Publicar el **resultado del revisor** en Jira con la granularidad del volcado (modo fase: 1 comentario al cerrar la fase con pasa/falla por criterio; modo tarea: 1 por tarea). **Confirmado** (2026-08-10).
4. La revisión en **modo fase** es **una sola pasada al cerrar la fase** (revisando juntas todas sus tareas). **Confirmado.**
5. El **tiempo de revisión se imputa en AMBOS modos** como **entrada de worklog separada `[revisión]`**; el total del issue en Jira = implementación + revisión, con desglose interno para `/retro`. **Confirmado.**
6. El revisor usa una **plantilla fija** y emite salida estructurada por criterio. **Confirmado.**

## Supuestos

- El conector Atlassian permite editar la descripción de un issue para marcar la checklist (`editJiraIssue`); si no, la checklist se refleja solo en comentarios y se anota la limitación.
- Mantener `"tarea"` como defecto no rompe ninguna instalación existente.
- El desglose por tarea en el worklog del issue de fase es aceptable como varias entradas de worklog en el mismo issue (Jira lo permite) — igual que las entradas `[revisión]` conviven con las de implementación.
- C-06/C-07 dependen de la iniciativa `qa-strict` ya implementada (el paso de revisión de dos lentes en `/dev-cycle`): C-06 lo extiende para que emita salida estructurada. Si qa-strict no estuviera desplegado, C-06/C-07 no aplican (no hay revisor que publicar).
- `addCommentToJiraIssue` y `addWorklogToJiraIssue` del conector están disponibles pero **no ejercitados end-to-end** en este proyecto → misma puerta de dry-run que el resto del modo fase (baja la confianza de C-06/C-07).
