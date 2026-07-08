# Documentación del agente `evaluator`

Agente que **evalúa y presupuesta** el coste de implementar una **especificación (spec)**. Responde a "¿cuánto costaría esto y conviene hacerlo?" — para decidir, no para ejecutar. Es el eslabón central de la cadena **spec → evaluación → plan**: primero se especifica, luego se evalúa/decide con `evaluator`, y por último se planifica el detalle con `planner`.

---

## 1. Entrada y salida

- **Entrada:** una spec en `docs/specs/<slug>.md`. Si la especificación llega **por el prompt** (o solo llegan requisitos sueltos), el agente **crea primero la spec** en `docs/specs/<slug>.md` (con la plantilla `spec.md`, estado inicial `borrador`) y luego la evalúa.
- **Salida:** `docs/evaluations/<YYYY-MM-DD>-<slug>/evaluation.md` (mismo `<slug>` que la spec), generado desde las plantillas de `agent-kits/evaluator/templates/` (`spec.md` y `evaluation.md`). Índices en `docs/evaluations/README.md` y `docs/specs/README.md`.
- **Enlazado bidireccional:** la evaluación apunta a su spec y, al crearse, actualiza la spec para que apunte a la evaluación. El enlace al plan lo completa `planner` en el handoff.

---

## 2. Qué contiene la evaluación

El documento reúne, en formato fijo: cuadro de mando con los totales (esfuerzo, coste €, tokens, confianza), resumen ejecutivo, un mapa de los **requerimientos recibidos** (con ambigüedades marcadas), el checklist de **datos necesarios para una evaluación completa**, los **supuestos económicos**, un **bloque de evaluación por característica** (`C-01`, `C-02`…), y — cuando hay varias — una **tabla comparativa** y una **recomendación** de orden. Cierra con el **presupuesto total**, los riesgos transversales y el **handoff a `planner`**.

Cada característica se evalúa con: requisito origen, descripción, complejidad, esfuerzo (h) y confianza, previsión de tokens (in/out) y coste €, impacto/áreas afectadas, dependencias, riesgos e incógnitas.

---

## 3. Estimaciones

Igual que `planner`, presupuesta en tres ejes: **tiempo** (horas), **coste económico en EUR** (`horas × tarifa + tokens de IA`) y **tokens de IA** (input/output). Los supuestos (tarifa/hora, modelo, precio de tokens, tipo de cambio) quedan escritos y son ajustables, de modo que el presupuesto es recalculable. Si el precio de tokens vigente no se conoce con certeza, se marca `⚠️ verificar` en lugar de inventar una cifra. Cuando el documento de requerimientos es ambiguo o incompleto, el agente lo declara, presupuesta bajo supuestos explícitos y baja la confianza.

---

## 4. Relación con `planner`

`evaluator` no genera el plan de ejecución: al final indica qué características se aprueban para planificar y remite al agente **`planner`**, que creará `docs/plans/<fecha>-<slug>/` con `improvement-plan.md` + `TASKS.md`. La dependencia queda declarada en el frontmatter (`agents: [planner]`).

| | `evaluator` | `planner` |
|---|-------------|-----------|
| Pregunta que responde | ¿Cuánto cuesta y conviene? | ¿Cómo se ejecuta, paso a paso? |
| Entrada | spec (`docs/specs/`) | evaluación/spec aprobada |
| Salida | `docs/evaluations/…/evaluation.md` | `docs/plans/…/improvement-plan.md` + `TASKS.md` |

Al crear el plan, `planner` rellena hacia atrás el `plan:` de la spec y la fila **Plan** de la evaluación, cerrando la cadena.

---

## 5. Cómo se invoca

Dentro del proyecto, en Claude Code:

- `usa el agente evaluator con docs/specs/login-magic-code.md`
- `evaluator, presupuesta esta especificación: …` (si la pegas, crea primero la spec y luego evalúa)
- `evalúa el coste de estas tres características: …`

La primera vez confirma los parámetros de estimación (tarifa/hora, modelo, precios de tokens).

---

## 6. Estados y prioridades

Vocabulario **único** del repo (una evaluación nace en `borrador`):

Estados: `borrador` 📝 · `en-progreso` 🚧 · `en-revision` 🔍 · `completado` ✅ · `cancelado` ❌

Prioridades (default `Media`): `Baja` 🟢 · `Media` 🟡 · `Alta` 🟠 · `Crítica` 🔴
