# 2026-08-10-agent-best-practices

> Evaluación y presupuesto de la adopción de las mejores prácticas de las colecciones top de agentes (model tiering, tools mínimos, DoD verificable, revisión adversarial, descriptions de enrutado, DRY, linter en CI) — soporta la decisión go/no-go y el orden de ejecución.

| | |
|---|---|
| **Fecha** | 2026-08-10 |
| **Estado** | completado |
| **Prioridad global** | Media 🟡 |
| **Solicitante** | daycry |
| **Spec** | [`spec.md`](spec.md) |
| **Plan** | [`improvement-plan.md`](improvement-plan.md) (2026-08-10 · 20,7 h · ~1.069 €) |
| **Características evaluadas** | 8 |

---

## Cuadro de mando

| Métrica | Total estimado | Confianza |
|--------|----------------|-----------|
| Esfuerzo humano | **19,8 h** (16,5 h base +20 %) | Alta |
| Tiempo IA (ejecución) | **5,5 h** (+ 1,4 h supervisión) | Media |
| Coste | **~1.023 €** | Alta (h) / Media (tokens ⚠️) |
| Tokens IA | **~1,70 M** (in 1,53 M / out 167 k) | Media |
| Multiplicador productividad | **×2,9** | — |
| Características | **8** | — |

---

## Resumen ejecutivo

La spec (revisada y confirmada con el usuario el 2026-08-10) pide incorporar al plugin las seis estrategias contrastadas que faltan respecto al estado del arte (wshobson, VoltAgent, superpowers, best practices oficiales) más dos arreglos puntuales y un linter de CI. Son en su mayoría **ediciones de prompts y frontmatter** sobre los 8 agentes existentes, sin código de producto salvo el linter (C-08). Se presupuestan **16,5 h base (19,8 h con margen), ~1.023 €** y ~1,7 M tokens. La evaluación soporta la decisión de **aprobar la iniciativa completa** y ejecutarla en tres tandas: quick wins (C-01/C-02/C-03) → medias (C-04/C-05/C-06) → mayores (C-07/C-08).

---

## Requerimientos recibidos

Mapa del documento de origen a las características evaluadas.

| ID | Característica | Requisito origen (ref.) | ¿Claro? |
|----|---------------|-------------------------|---------|
| C-01 | Model tiering | spec §Características + §Configuración (tabla de modelos) | ✅ |
| C-02 | Arreglos puntuales (planner P7 doble, refs § de nemesis) | spec §Características + §Referencias (verificado 2026-08-10) | ✅ |
| C-03 | Descriptions de enrutado | spec §Características + §Decisiones de diseño | ✅ |
| C-04 | Tools mínimos | spec §Características | ✅ (criterio por agente, ver incógnitas) |
| C-05 | DoD verificable | spec §Características + §Decisiones de diseño | ✅ |
| C-06 | DRY / `agent-kits/shared` | spec §Características + §Decisiones de diseño | ✅ |
| C-07 | Revisión adversarial en `/dev-cycle` | spec §Características + §Manejo de errores | ✅ |
| C-08 | Linter de plugin en CI | spec §Características + §Pruebas | ✅ |

**Ambigüedades / información que falta:**

- C-01: la spec deja abierta la elección **opus vs. `inherit`** para evaluator y nemesis «si el coste preocupa»; se presupuesta igual (una línea por fichero), pero la decisión debe cerrarse en el plan.
- C-04: el «mínimo real» de tools por agente exige revisar el uso efectivo agente a agente; el esfuerzo puede variar si aparecen usos no documentados (confianza Media en esa característica).
- C-08: el alcance exacto del patrón de «frases-gatillo» a validar en descriptions no está formalizado; se asume una regex/heurística simple acordada en el plan.

---

## Datos necesarios para una evaluación completa

- [x] **Requerimientos** completos y sin ambigüedades (tabla C-01…C-08 con detalle por característica)
- [x] **Alcance** de cada característica acotado (sección «Alcance» con fuera-de-alcance explícito)
- [x] **Criterios de aceptación / éxito** por característica (sección «Pruebas»: autovalidación del linter, fixtures, prueba manual de `/dev-cycle`, verificación de auto-delegación)
- [x] **Restricciones** (retrocompatibilidad declarada en «Manejo de errores»; sin deadline)
- [x] **Dependencias externas** — ninguna: todo es interno al plugin (CI y `release.py` ya existen)
- [x] **Contexto técnico** disponible (estructura del plugin, CONVENTIONS regla 5, informe comparativo de origen)
- [ ] **Tarifa/hora y supuestos de coste** confirmados — no existe `.claude/rates.json`; se usan los defaults del evaluator (declarados abajo). No bloquea: la spec ya lo asume.

---

## Supuestos económicos (ajustables)

**Coste = (horas × tarifa) + coste de tokens de IA.** Importes en **EUR**.

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | 50 €/h | Default del evaluator (no hay `.claude/rates.json`) |
| Modelo IA asumido | claude-opus-4-8 | Base de la previsión de tokens |
| Precio input | 13,80 € / 1M tokens | ⚠️ verificar — supuesto de trabajo: 15 USD/M × 0,92 |
| Precio output | 69,00 € / 1M tokens | ⚠️ verificar — supuesto de trabajo: 75 USD/M × 0,92 |
| Tipo de cambio | 1 USD = 0,92 € | Default |
| Ratio de supervisión | 25 % de las horas IA | Default |
| Margen de contingencia | 20 % | Sobre horas base (humanas e IA) |

**Calibración con el histórico del repo** (no existe `docs/roadmap/CALIBRATION.md`; se usan las evaluaciones cerradas como referencia): `2026-07-09-qa-agent` (agente nuevo completo + runner Playwright) = 21,6 h / ~1.087 €; `2026-07-09-nemesis-sca-iac` (integración trivy+hadolint) = 12 h / ~605 €. Esta iniciativa tiene 8 características pero mayoritariamente **más pequeñas** que aquéllas (ediciones de prompt/frontmatter); solo C-08 introduce código nuevo con tests. El total con margen (19,8 h) queda coherente: por debajo de un agente nuevo completo pese a tocar los 8 agentes.

---

## Evaluación por característica

### C-01 — Model tiering

- **Requisito origen**: spec §Características C-01 + tabla §Configuración (pdfy=haiku; documenter/qa/implementer/analyst/planner=sonnet; evaluator/nemesis=opus o `inherit`)
- **Descripción**: añadir el campo `model` al frontmatter de los 8 agentes según la tabla de la spec. Ajusta el coste de ejecución de cada agente a la complejidad real de su tarea (criterio wshobson).
- **Complejidad**: Baja (trivial: una línea por fichero)
- **Esfuerzo**: 0,5 h · confianza Alta
- **Previsión IA**: 60 k in / 4 k out tok · ~1,1 €
- **Coste**: (0,5 h × 50 €) + tokens = **26 €**
- **Impacto / áreas afectadas**: `agents/*.md` (8 ficheros, solo frontmatter)
- **Dependencias y prerequisitos**: ninguna; C-08 luego lo valida (`model` presente)
- **Riesgos**: mínimos — cambio retrocompatible; el único punto de decisión es opus vs. `inherit` en evaluator/nemesis
- **Incógnitas / preguntas abiertas**: cerrar opus vs. `inherit` para evaluator/nemesis (decisión de coste, no de esfuerzo)

### C-02 — Arreglos puntuales

- **Requisito origen**: spec §Características C-02 + §Referencias (doble «P7» en planner.md líneas 85/87, verificado 2026-08-10)
- **Descripción**: renumerar el doble «P7» (y P8→P9) en `planner.md`; eliminar o inlinear en `nemesis.md` las referencias «§6, §11, §14, §17» a un system base que no viaja con el plugin.
- **Complejidad**: Baja
- **Esfuerzo**: 0,75 h · confianza Alta
- **Previsión IA**: 90 k in / 6 k out tok · ~1,7 €
- **Coste**: (0,75 h × 50 €) + tokens = **39 €**
- **Impacto / áreas afectadas**: `agents/planner.md`, `agents/nemesis.md`
- **Dependencias y prerequisitos**: ninguna
- **Riesgos**: al inlinear las referencias de nemesis hay que decidir qué contenido sustituye a cada §; si el contenido original no está disponible, se elimina la referencia sin pérdida funcional
- **Incógnitas / preguntas abiertas**: ¿existe el texto original de los § citados para inlinearlo, o se opta por eliminar?

### C-03 — Descriptions de enrutado

- **Requisito origen**: spec §Características C-03 + §Decisiones de diseño
- **Descripción**: reescribir el `description` de evaluator, planner y nemesis al patrón «qué hace + Úsalo cuando el usuario diga…», mover rutas/plantillas al cuerpo, y añadir a nemesis «PROACTIVAMENTE cuando se mencione seguridad». Mejora la auto-delegación de Claude Code.
- **Complejidad**: Baja
- **Esfuerzo**: 1,25 h · confianza Alta (incluye la verificación manual de enrutado de §Pruebas)
- **Previsión IA**: 120 k in / 10 k out tok · ~2,4 €
- **Coste**: (1,25 h × 50 €) + tokens = **65 €**
- **Impacto / áreas afectadas**: `agents/evaluator.md`, `agents/planner.md`, `agents/nemesis.md` (frontmatter + primeras líneas del cuerpo)
- **Dependencias y prerequisitos**: ninguna; C-08 valida después el patrón de frases-gatillo
- **Riesgos**: la verificación de auto-delegación es empírica (comportamiento del router); una description puede necesitar 1-2 iteraciones
- **Incógnitas / preguntas abiertas**: ninguna relevante para el coste

### C-04 — Tools mínimos

- **Requisito origen**: spec §Características C-04
- **Descripción**: revisar agente a agente el conjunto `tools` y recortarlo al mínimo real: quitar `Edit` a evaluator y planner (escriben con Write), mantener Write donde generan artefactos. La restricción mecánica no se diluye con el contexto, a diferencia de la semántica.
- **Complejidad**: Media (el recorte es fácil; el criterio por agente requiere leer los 8 prompts y sus flujos completos)
- **Esfuerzo**: 1,75 h · confianza Media
- **Previsión IA**: 200 k in / 12 k out tok · ~3,6 €
- **Coste**: (1,75 h × 50 €) + tokens = **91 €**
- **Impacto / áreas afectadas**: `agents/*.md` (8 ficheros, frontmatter `tools`)
- **Dependencias y prerequisitos**: conviene hacerlo antes de C-05 (el DoD puede exigir comprobaciones que dependan de las tools disponibles)
- **Riesgos**: **el mayor riesgo funcional de la iniciativa**: recortar de más rompe un flujo real del agente (p. ej. un agente que edita su propio artefacto en iteraciones necesita `Edit`). Mitigación: revisar los flujos P1…Pn de cada prompt antes de recortar y validar con una pasada de humo por agente
- **Incógnitas / preguntas abiertas**: usos de tools no evidentes en el prompt (p. ej. ediciones incrementales de `tasks.md` por implementer) — a confirmar durante la revisión

### C-05 — DoD verificable

- **Requisito origen**: spec §Características C-05 + §Decisiones de diseño + §Configuración (umbral verde de qa)
- **Descripción**: añadir a los 8 agentes una sección final `## ANTES DE CERRAR (DoD)` con 3-5 comprobaciones ejecutables y obligación de mostrar evidencia; explicitar en qa el umbral verde (0 failed, 0 flaky sin justificar en `results.json`). Principio «evidence over claims».
- **Complejidad**: Media (8 DoD distintos, cada uno con comprobaciones *ejecutables* específicas de su dominio, no boilerplate)
- **Esfuerzo**: 2,5 h · confianza Media
- **Previsión IA**: 260 k in / 30 k out tok · ~5,7 €
- **Coste**: (2,5 h × 50 €) + tokens = **131 €**
- **Impacto / áreas afectadas**: `agents/*.md` (8 ficheros, sección nueva), énfasis en `agents/qa.md` (umbral)
- **Dependencias y prerequisitos**: mejor tras C-04 (las comprobaciones del DoD deben ser ejecutables con las tools que le queden a cada agente)
- **Riesgos**: DoD genéricos que no aportan (sobre-ingeniería); el valor está en que cada comprobación sea ejecutable y específica. Riesgo de alargar los prompts (coste de contexto por invocación)
- **Incógnitas / preguntas abiertas**: cuántas comprobaciones admite cada agente sin inflar el prompt (se decide en el plan, 3-5 por diseño)

### C-06 — DRY / `agent-kits/shared`

- **Requisito origen**: spec §Características C-06 + §Decisiones de diseño
- **Descripción**: crear `agent-kits/shared/` y extraer los fragmentos duplicados: tabla de estimación (evaluator§1/planner§1 → `estimation-defaults.md`), párrafo de Confluence opt-in (×4 → `confluence-optin.md`) y tabla de estados (×3, queda solo en `docs/CONVENTIONS.md`). Resolución por `find` ya existente (CONVENTIONS regla 5). Incluye añadir la cita al ejemplo `docs/examples/ci4-forms-emails/` en evaluator/planner.
- **Complejidad**: Media
- **Esfuerzo**: 2,25 h · confianza Media
- **Previsión IA**: 220 k in / 25 k out tok · ~4,8 €
- **Coste**: (2,25 h × 50 €) + tokens = **117 €**
- **Impacto / áreas afectadas**: `agent-kits/shared/` (nuevo), `agents/evaluator.md`, `agents/planner.md`, `agents/qa.md`, `agents/documenter.md` (referencias Confluence), `docs/CONVENTIONS.md` (fuente única de estados)
- **Dependencias y prerequisitos**: ninguna dura; si se hace antes que C-05, el DoD ya puede referenciar los fragmentos compartidos
- **Riesgos**: indirection — el agente debe *resolver y leer* el fragmento en runtime; si el `find` falla en algún scope (proyecto/usuario/plugin), el agente pierde esa información. Mitigación: fallback textual mínimo en el prompt + validación en C-08
- **Incógnitas / preguntas abiertas**: si `agent-kits/shared/` requiere ajuste en `release.py`/empaquetado del plugin (a verificar en el plan)

### C-07 — Revisión adversarial en `/dev-cycle`

- **Requisito origen**: spec §Características C-07 + §Decisiones de diseño + §Manejo de errores
- **Descripción**: nuevo paso en `commands/dev-cycle.md` entre la implementación (Fase 3) y qa: un subagente genérico con contexto fresco revisa el diff contra `improvement-plan.md`/`tasks.md` y reporta **gaps de corrección o requisitos, no preferencias de estilo**. Se decidió paso de command, no agente nuevo (más barato, no engorda el plugin).
- **Complejidad**: Media (el coste está en el diseño del prompt del paso: qué contexto recibe, cómo se acota a gaps, qué hace el ciclo con el resultado)
- **Esfuerzo**: 2,5 h · confianza Media (incluye la prueba manual sobre iniciativa de juguete de §Pruebas)
- **Previsión IA**: 180 k in / 20 k out tok · ~3,9 €
- **Coste**: (2,5 h × 50 €) + tokens = **129 €**
- **Impacto / áreas afectadas**: `commands/dev-cycle.md` (nuevo paso + máquina de estados del ciclo), `docs/FLOWS.md` (actualizar flujo)
- **Dependencias y prerequisitos**: independiente de C-01…C-06; conviene definirlo antes de C-08 solo si el linter fuera a validar commands (no está en alcance)
- **Riesgos**: falsos positivos (gaps de estilo pese al prompt) que añaden fricción al ciclo; interacción con la rama superpowers de `/dev-cycle` (¿el paso aplica también cuando delega el backbone?). Mitigación: la spec ya instruye descartar estilo; decidir en el plan si el paso aplica solo a la cadena nativa
- **Incógnitas / preguntas abiertas**: comportamiento cuando la revisión reporta gaps — ¿vuelta a implementer automática o puerta manual? (a decidir en el plan)

### C-08 — Linter de plugin en CI

- **Requisito origen**: spec §Características C-08 + §Pruebas + §Manejo de errores
- **Descripción**: script Python (junto a los tests existentes) que valida: `model` presente, tools declarados válidos, description con frases-gatillo, `dependencies` apuntando a agentes/skills/kits existentes y sin ciclos. Con tests unitarios sobre fixtures y cableado en el CI existente. Evita la deriva doc↔realidad.
- **Complejidad**: Alta (la mayor de la iniciativa: parser de frontmatter, grafo de dependencias con detección de ciclos, fixtures, integración CI y autovalidación sobre el propio repo)
- **Esfuerzo**: 5,0 h · confianza Media
- **Previsión IA**: 400 k in / 60 k out tok · ~9,7 €
- **Coste**: (5,0 h × 50 €) + tokens = **260 €**
- **Impacto / áreas afectadas**: `scripts/` (linter nuevo), `tests/` (fixtures + test unitario, junto a `test_dashboard.py`/`test_worklog.py`), `.github/workflows` (job/step nuevo)
- **Dependencias y prerequisitos**: **requiere C-01…C-06 aplicados** para la autovalidación en verde (o tolerancia temporal); el mensaje de fallo debe indicar campo y patrón esperado (spec §Manejo de errores)
- **Riesgos**: sobre-especificar el patrón de frases-gatillo y generar falsos positivos en contribuciones externas; deriva del linter si cambian las claves de frontmatter admitidas por Claude Code. Mitigación: heurística laxa y documentada, mensaje de error accionable
- **Incógnitas / preguntas abiertas**: formalizar el patrón exacto de triggers a validar; ¿el linter corre también en `release.py` además de CI?

---

## Comparativa

Ordenada por coste ascendente dentro de cada tanda recomendada.

| # | Característica | Complejidad | Horas | Coste € | Tokens | Prioridad | Confianza |
|---|---------------|-------------|-------|---------|--------|-----------|-----------|
| C-01 | Model tiering | Baja | 0,5 h | 26 € | 64 k | Alta | Alta |
| C-02 | Arreglos puntuales | Baja | 0,75 h | 39 € | 96 k | Alta | Alta |
| C-03 | Descriptions de enrutado | Baja | 1,25 h | 65 € | 130 k | Alta | Alta |
| C-04 | Tools mínimos | Media | 1,75 h | 91 € | 212 k | Media | Media |
| C-05 | DoD verificable | Media | 2,5 h | 131 € | 290 k | Media | Media |
| C-06 | DRY / agent-kits/shared | Media | 2,25 h | 117 € | 245 k | Media | Media |
| C-07 | Revisión adversarial /dev-cycle | Media | 2,5 h | 129 € | 200 k | Media | Media |
| C-08 | Linter de plugin en CI | Alta | 5,0 h | 260 € | 460 k | Media | Media |
| | **Total (base, sin margen)** | | **16,5 h** | **858 €** | **~1,70 M** | | |

---

## Presupuesto total

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 16,5 h × 50 €/h | 825,00 € |
| Margen de contingencia | +20 % sobre desarrollo base | 165,00 € |
| Tokens IA (input) | 1,53 M tok × 13,80 €/M ⚠️ | 21,11 € |
| Tokens IA (output) | 167 k tok × 69,00 €/M ⚠️ | 11,52 € |
| **Total estimado (con margen)** | | **~1.023 €** |

> ⚠️ El coste de tokens (~33 €, un 3 % del total) usa precios **supuestos** pendientes de verificar; una desviación del ±50 % en la tarifa de tokens mueve el total menos de un 2 %.

---

## Productividad IA (humano vs. IA)

Compara el esfuerzo **humano** estimado con el tiempo que tardaría un **agente de IA** en implementarlo (más la supervisión humana).

| KPI | Valor |
|-----|-------|
| Horas humanas estimadas | 19,8 h *(16,5 h base)* |
| Horas IA (ejecución) | 5,5 h *(4,6 h base; supuesto)* |
| Supervisión humana | 1,4 h *(25 % de las horas IA)* |
| **Horas totales (IA + supervisión)** | **6,9 h** |
| Horas ahorradas | 12,9 h |
| **Ahorro** | **65 %** |
| **Multiplicador de productividad** | **×2,9** |
| FTE equivalentes *(opcional)* | ~0,08 |

> Horas mostradas **con el margen de contingencia (+20 %)** ya aplicado sobre las horas base (humanas e IA). El multiplicador es moderado a propósito: gran parte del trabajo es criterio de revisión (C-04, C-05) y validación empírica (C-03, C-07), donde la supervisión humana no se comprime tanto como en tareas mecánicas.

---

## Recomendación

- **Veredicto**: **go** — coste contenido (~1.023 €), riesgo bajo (cambios retrocompatibles por diseño), y C-08 institucionaliza la calidad hacia delante.
- **Quick wins** (bajo coste, alto valor): **C-01, C-02, C-03** — 2,5 h base / 130 € en total; C-01 y C-02 son triviales y C-03 mejora la auto-delegación de inmediato.
- **Costosas / a valorar**: **C-08** (5 h base, la única con código y tests) y **C-07** (valor alto pero requiere validación empírica del paso). Ambas se recomiendan igualmente: C-08 protege todo lo anterior de la deriva.
- **Orden sugerido**: **C-01 → C-02 → C-03** (quick wins) → **C-04 → C-05 → C-06** (medias; C-04 antes que C-05 para que el DoD sea ejecutable con las tools finales) → **C-07 → C-08** (mayores; C-08 al final para autovalidar en verde todo lo aplicado).
- **Fuera de alcance recomendado**: mantener lo que la spec ya excluye (TDD estricto, protocolo JSON, few-shots inline, agente `reviewer` dedicado).

---

## Riesgos transversales

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Recorte de `tools` o DoD rompe un flujo real de algún agente (C-04/C-05) | Media | Alto | Revisar los flujos completos de cada prompt antes de tocar; pasada de humo por agente tras el cambio; C-08 valida la coherencia declarada |
| Prompts más largos (DoD ×8 + fragmentos shared) elevan el coste de contexto por invocación | Media | Medio | Limitar el DoD a 3-5 comprobaciones; fragmentos shared solo donde hay duplicación real (3 casos identificados) |
| Indirection de `agent-kits/shared/`: el `find` no resuelve en algún scope o el empaquetado del plugin no lo incluye | Baja | Alto | Verificar `release.py`/empaquetado en el plan; fallback textual mínimo en los prompts |
| Linter demasiado estricto genera falsos positivos en contribuciones externas | Media | Medio | Heurísticas laxas y documentadas; mensaje de fallo con campo y patrón esperado (ya en spec §Manejo de errores) |
| Deriva frente a Claude Code (nuevos tiers de `model`, claves de frontmatter) | Baja | Medio | La spec ya lo prevé como supuesto; el linter centraliza el punto de actualización |

---

## Siguiente paso

Para **ejecutar** lo aprobado, genera el plan detallado con el agente **`planner`** (creará `improvement-plan.md` + `tasks.md` en esta misma carpeta `docs/roadmap/2026-08-10-agent-best-practices/`, y rellenará el campo **Plan** de esta evaluación y el `plan:` de la spec). Indica qué características se aprueban para planificar; la recomendación es **las 8, en el orden sugerido** (C-01→C-02→C-03 → C-04→C-05→C-06 → C-07→C-08). Requisito de secuencia para el plan: C-08 en último lugar para autovalidar C-01…C-06 en verde.

---

## Changelog

| Fecha | Cambio |
|-------|--------|
| 2026-08-10 | Evaluación inicial de C-01…C-08 sobre spec revisada con el usuario; estado `en-revision` a la espera de go/no-go |
