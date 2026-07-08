# Documentación del agente `evaluator`

Agente que **evalúa y presupuesta** el coste de implementar una o varias características a partir de un **documento de toma de requerimientos**. Responde a "¿cuánto costaría esto y conviene hacerlo?" — para decidir, no para ejecutar. Complementa a `planner`: primero se evalúa/decide con `evaluator`, luego se planifica el detalle con `planner`.

---

## 1. Entrada y salida

- **Entrada:** un documento de toma de requerimientos (ruta o contenido pegado), con una o varias características/requisitos.
- **Salida:** `docs/evaluations/<YYYY-MM-DD>-<slug>/evaluation.md`, generado desde la plantilla de `agent-kits/evaluator/templates/`. Índice en `docs/evaluations/README.md`.

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
| Entrada | Documento de requerimientos | Característica/objetivo aprobado |
| Salida | `docs/evaluations/…/evaluation.md` | `docs/plans/…/improvement-plan.md` + `TASKS.md` |

---

## 5. Cómo se invoca

Dentro del proyecto, en Claude Code:

- `usa el agente evaluator con docs/requerimientos/RFP-cliente.md`
- `evaluator, presupuesta lo que pide este documento de requerimientos`
- `evalúa el coste de estas tres características: …`

La primera vez confirma los parámetros de estimación (tarifa/hora, modelo, precios de tokens).

---

## 6. Estados y prioridades

Vocabulario **único** del repo (una evaluación nace en `borrador`):

Estados: `borrador` 📝 · `en-progreso` 🚧 · `en-revision` 🔍 · `completado` ✅ · `cancelado` ❌

Prioridades (default `Media`): `Baja` 🟢 · `Media` 🟡 · `Alta` 🟠 · `Crítica` 🔴
