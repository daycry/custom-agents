# 2026-08-10-agent-best-practices

> Adoptar en el plugin las seis estrategias contrastadas de las colecciones top de agentes (model tiering, tools mínimos, DoD verificable, revisión adversarial, descriptions de enrutado, DRY) más dos arreglos puntuales y un linter de plugin en CI.

| | |
|---|---|
| **Fecha** | 2026-08-10 |
| **Estado** | borrador |
| **Tipo** | Refactor (mejora del propio plugin) |
| **Prioridad** | Media |
| **Solicitante** | jmano@mediapro.tv |
| **Responsable** | pendiente de asignar (previsto: agente `implementer`) |
| **Spec** | [`spec.md`](spec.md) |
| **Evaluación** | [`evaluation.md`](evaluation.md) |

---

## Cuadro de mando

| Métrica | Estimado | Real | Confianza |
|--------|---------|------|-----------|
| Tiempo humano | **20,7 h** (17,25 h base +20 %) | 0 h | Alta |
| Tiempo IA (ejecución) | **5,8 h** (+ 1,45 h supervisión) | 0 h | Media |
| Coste total | **~1.069 €** | 0 € | Alta (h) / Media (tokens ⚠️) |
| Tokens IA | **~1,76 M** (in 1,58 M / out 177 k) | 0 | Media |
| Multiplicador productividad | **×2,9** | — | — |
| Tareas | **11** | 0 hechas | — |

> Las cifras heredan la evaluación aprobada (16,5 h base / 19,8 h con margen / ~1.023 €) **más 0,75 h base** de dos tareas añadidas en planificación: completar las plantillas truncadas del kit (T-04, 0,25 h, detectada durante la evaluación) y el cierre de release (T-11, 0,5 h). No se re-estima ninguna característica: las horas por C-0X son las de la evaluación.

---

## Estimación por fase

| Fase | Estimado (h, base) | Tokens (in / out) | Coste € (base) |
|------|-------------|-------------------|---------|
| Fase 1 — Quick wins (C-01, C-02, C-03 + plantillas) | 2,75 | 290 k / 26 k | 143 |
| Fase 2 — Prácticas medias (C-04, C-05, C-06) | 6,5 | 680 k / 67 k | 339 |
| Fase 3 — Revisión adversarial y linter (C-07, C-08) | 7,5 | 580 k / 80 k | 389 |
| Fase 4 — Cierre y release | 0,5 | 30 k / 4 k | 26 |
| **Total** | **17,25 h** (20,7 h con margen) | **1,58 M / 177 k** | **897 €** (~1.069 € con margen) |

---

## Presupuesto económico

**Coste = (horas × tarifa) + coste de tokens de IA.** Todos los importes en **EUR**.

### Supuestos (ajustables)

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | 50 €/h | Default del planner — no existe `.claude/rates.json` (mismos supuestos que la evaluación) |
| Modelo IA asumido | claude-opus-4-8 | Modelo previsto para la ejecución |
| Precio input | 13,80 € / 1M tokens | ⚠️ verificar — supuesto de trabajo: 15 USD/M × 0,92 |
| Precio output | 69,00 € / 1M tokens | ⚠️ verificar — supuesto de trabajo: 75 USD/M × 0,92 |
| Tipo de cambio | 1 USD = 0,92 € | Default |
| Margen de contingencia | 20 % | Colchón por imprevistos; sobre horas base (humanas e IA) |

### Desglose

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 17,25 h × 50 €/h | 862,50 € |
| Margen de contingencia | +20 % sobre desarrollo base | 172,50 € |
| Tokens IA (input) | 1,58 M tok × 13,80 €/M ⚠️ | 21,80 € |
| Tokens IA (output) | 177 k tok × 69,00 €/M ⚠️ | 12,21 € |
| **Total estimado (con margen)** | | **~1.069 €** |

> ⚠️ El coste de tokens (~34 €, un 3 % del total) usa precios **supuestos** pendientes de verificar; una desviación del ±50 % en la tarifa de tokens mueve el total menos de un 2 %.

---

## Previsión de tokens (por fase)

Estimación del consumo de tokens del modelo por fase. Base: claude-opus-4-8 · precios de la tabla de supuestos.

| Fase | Input (tok) | Output (tok) | Total (tok) | Coste € |
|------|------------|-------------|-------------|---------|
| Fase 1 — Quick wins | 290 k | 26 k | 316 k | 5,80 |
| Fase 2 — Prácticas medias | 680 k | 67 k | 747 k | 14,00 |
| Fase 3 — Revisión adversarial y linter | 580 k | 80 k | 660 k | 13,50 |
| Fase 4 — Cierre y release | 30 k | 4 k | 34 k | 0,70 |
| **Total** | **1,58 M** | **177 k** | **~1,76 M** | **34,00 €** |

**Método de estimación:** se hereda el reparto por característica de la evaluación (lecturas repetidas de los 8 `agents/*.md` ~6 k tok/pasada + plantillas/docs de contexto + generación de prompt/código), asignado a la tarea que implementa cada C-0X; C-08 se reparte entre T-09 (script, 250 k/40 k) y T-10 (tests+CI, 150 k/20 k). Las dos tareas nuevas añaden ~50 k in / 10 k out.

---

## Productividad IA (humano vs. IA)

Compara el esfuerzo **humano** estimado con el tiempo que tardaría un **agente de IA** en ejecutarlo (más la supervisión humana necesaria). Cifras aproximadas; supuestos declarados.

| KPI | Valor |
|-----|-------|
| Horas humanas estimadas | 20,7 h *(17,25 h base)* |
| Horas IA (ejecución) | 5,8 h *(4,85 h base; supuesto)* |
| Supervisión humana | 1,45 h *(25 % de las horas IA)* |
| **Horas totales (IA + supervisión)** | **7,25 h** |
| Horas ahorradas | 13,45 h |
| **Ahorro** | **65 %** |
| **Multiplicador de productividad** | **×2,9** |
| FTE equivalentes *(opcional)* | ~0,08 |

> Horas mostradas **con el margen de contingencia (+20 %)** ya aplicado sobre las horas base (humanas e IA). El multiplicador es moderado a propósito: gran parte del trabajo es criterio de revisión (C-04, C-05) y validación empírica (C-03, C-07), donde la supervisión no se comprime tanto como en tareas mecánicas.

---

## Resumen ejecutivo

Se incorporan al plugin las prácticas que el análisis comparativo (2026-08-10) identificó como faltantes frente a wshobson/agents, VoltAgent, superpowers y las best practices oficiales de Claude Code: `model` por agente, `tools` al mínimo real, DoD ejecutable en los 8 agentes, descriptions de enrutado, extracción de duplicados a `agent-kits/shared/`, un paso de revisión adversarial en `/dev-cycle` y un linter de plugin en CI que protege todo lo anterior de la deriva. Son mayoritariamente ediciones de prompts/frontmatter; solo el linter (C-08) introduce código nuevo con tests. Ejecución en tres tandas más un cierre de release, con C-08 al final para autovalidar en verde todo lo aplicado.

### Objetivos

- Los 8 agentes declaran `model` y `tools` mínimos, y cierran con un DoD de 3-5 comprobaciones ejecutables con evidencia.
- La auto-delegación funciona: «presupuesta esto» / «haz una auditoría de seguridad» enruta a `evaluator` / `nemesis` sin nombrarlos.
- Cero duplicación de la tabla de estimación, el párrafo Confluence opt-in y la tabla de estados (fuentes únicas en `agent-kits/shared/` y `docs/CONVENTIONS.md`).
- `/dev-cycle` incluye revisión adversarial (subagente fresco, gaps de corrección/requisitos) entre implementación y qa.
- El linter de plugin pasa en verde en CI sobre el propio repo (autovalidación de C-01…C-06).

---

## Datos necesarios para un informe completo

- [x] **Requisitos funcionales** confirmados por el solicitante (spec `aprobada`, decisiones confirmadas 2026-08-10)
- [x] **Alcance** cerrado (spec §Alcance con fuera-de-alcance explícito: TDD estricto, protocolo JSON, few-shots inline, agente reviewer)
- [x] **Criterios de éxito / métricas** acordados (spec §Pruebas: autovalidación linter, fixtures pytest, prueba manual de `/dev-cycle`, verificación de enrutado)
- [x] **Accesos y credenciales** — n/a: todo es interno al repo del plugin
- [x] **Entornos** disponibles (repo local + CI GitHub Actions existente + `scripts/release.py`)
- [x] **Stakeholders** identificados (jmano@mediapro.tv; puerta «OK del plan» antes de implementar)
- [x] **Dependencias externas** — ninguna
- [x] **Restricciones** conocidas (retrocompatibilidad declarada en spec §Manejo de errores; sin deadline)
- [x] **Tarifa/hora y supuestos de coste** — defaults declarados (no hay `.claude/rates.json`); mismos que la evaluación

---

## Análisis de impacto

- **`agents/*.md`** (8 ficheros: analyst, documenter, evaluator, implementer, nemesis, pdfy, planner, qa) — frontmatter `model` (C-01) y `tools` (C-04), `description` de enrutado en evaluator/planner/nemesis (C-03), sección `## ANTES DE CERRAR (DoD)` (C-05), sustitución de fragmentos duplicados por referencia a shared (C-06), renumeración P7/P9 en planner y limpieza de refs § en nemesis (C-02).
- **`commands/dev-cycle.md`** — nuevo paso de revisión adversarial entre la implementación y qa (C-07).
- **`agent-kits/shared/`** (nuevo) — `estimation-defaults.md` y `confluence-optin.md`, resueltos en runtime con el `find` de CONVENTIONS regla 5 (C-06).
- **`docs/CONVENTIONS.md`** — pasa a ser la fuente única de la tabla de estados (C-06); refleja `agent-kits/shared/` y el linter.
- **`docs/FLOWS.md`** — flujo de `/dev-cycle` actualizado con el paso adversarial (C-07).
- **`scripts/` + `tests/` + `.github/workflows/`** — linter de plugin nuevo con tests pytest sobre fixtures y step de CI (C-08), junto a `test_dashboard.py`/`test_worklog.py`.
- **`agent-kits/evaluator/templates/evaluation.md` y `agent-kits/planner/templates/improvement-plan.md`** — completar el final truncado de ambas plantillas (tarea extra detectada en evaluación + recon del plan); espejo en `.claude/agent-kits/`.
- **`CHANGELOG.md` + versión del plugin** — bump con `scripts/release.py` al cierre.

---

## Cambios arquitectónicos

- **Model tiering por frontmatter** (criterio wshobson): pdfy=haiku; documenter/qa/implementer/analyst/planner=sonnet; evaluator/nemesis=**opus** — se cierra aquí la incógnita de la evaluación: se elige opus (análisis crítico); cambiar a `inherit` queda como ajuste de una línea si el coste preocupa.
- **Restricción mecánica sobre semántica**: el recorte de `tools` se hace tras leer los flujos P1…Pn completos de cada prompt, porque el toolset no se diluye con el contexto y la instrucción «no toques el código» sí.
- **Revisión adversarial como paso de command, no agente nuevo**: subagente genérico con contexto fresco que revisa el diff contra `improvement-plan.md`/`tasks.md`. Decisiones de plan: los gaps reportados van a **puerta manual** (el usuario decide si vuelve a `implementer`), coherente con las puertas go/no-go del plugin; el paso aplica **solo a la cadena nativa** (la rama superpowers ya trae revisión en dos etapas propia).
- **DRY con indirection segura**: los fragmentos compartidos se resuelven por `find` (mismo mecanismo que los kits) con **fallback textual mínimo** en cada prompt para el caso de resolución fallida; C-08 valida la coherencia.
- **Linter como institución**: heurística **laxa y documentada** para las frases-gatillo (p. ej. presencia de «Úsalo cuando» / «PROACTIVAMENTE» o equivalente); corre en CI como check obligatorio y, opcionalmente, como paso previo en `release.py` (decisión menor a confirmar en T-10).

---

## Archivos a crear/modificar

| Archivo | Acción | Propósito |
|---------|--------|-----------|
| `agents/analyst.md` … `agents/qa.md` (×8) | Modificar | `model`, `tools`, DoD; y según agente: description, refs shared, arreglos puntuales |
| `commands/dev-cycle.md` | Modificar | Paso de revisión adversarial entre implementación y qa |
| `agent-kits/shared/estimation-defaults.md` | Crear | Fuente única de la tabla de estimación (antes duplicada evaluator§1/planner§1) |
| `agent-kits/shared/confluence-optin.md` | Crear | Fuente única del párrafo Confluence opt-in (antes ×4) |
| `docs/CONVENTIONS.md` | Modificar | Fuente única de la tabla de estados; alta de `agent-kits/shared/` |
| `docs/FLOWS.md` | Modificar | Flujo `/dev-cycle` con el paso adversarial |
| `scripts/lint_plugin.py` (nombre orientativo) | Crear | Linter de plugin: `model`, `tools`, triggers, grafo `dependencies` sin ciclos |
| `tests/test_lint_plugin.py` + `tests/fixtures/` | Crear | Tests unitarios del linter con fixtures inválidas |
| `.github/workflows/` (workflow CI existente) | Modificar | Step del linter |
| `agent-kits/evaluator/templates/evaluation.md` | Modificar | Completar final truncado («Indica qué caract…») |
| `agent-kits/planner/templates/improvement-plan.md` | Modificar | Completar final truncado (Métricas de éxito + Changelog) |
| `CHANGELOG.md` | Modificar | Entrada de la versión nueva |

---

## Dependencias y prerequisitos

- Orden de la evaluación (vinculante): **C-01→C-02→C-03** → **C-04→C-05→C-06** (C-04 antes que C-05 para que el DoD sea ejecutable con las tools finales) → **C-07→C-08** (C-08 el último: autovalida C-01…C-06 en verde).
- T-10 (tests+CI del linter) requiere T-09 (script) y las fases 1-2 aplicadas para la autovalidación.
- T-11 (release) requiere todas las anteriores completadas.
- Puerta de control: **OK del plan por el usuario** antes de arrancar la implementación (handoff a `implementer`).

---

## Criterios de aceptación (global)

- [ ] Los 8 agentes declaran `model` según la tabla de la spec y `tools` recortados al mínimo real, sin romper ningún flujo (pasada de humo por agente).
- [ ] Los 8 agentes cierran con `## ANTES DE CERRAR (DoD)` (3-5 comprobaciones ejecutables + evidencia); qa con umbral verde explícito (0 failed, 0 flaky sin justificar).
- [ ] Auto-delegación verificada: «presupuesta esto» → evaluator; «haz una auditoría de seguridad» → nemesis, sin nombrar agente.
- [ ] `agent-kits/shared/` creado y sin duplicados restantes (grep de tabla de estimación/estados/párrafo Confluence fuera de sus fuentes únicas = 0 resultados).
- [ ] `/dev-cycle` ejecuta el paso de revisión adversarial sobre una iniciativa de juguete y reporta contra el plan (gaps de corrección/requisitos, no estilo).
- [ ] Linter en verde en CI sobre el propio repo; tests pytest del linter (fixtures inválidas) en verde junto a los existentes.
- [ ] Plantillas del evaluator y del planner completas (sin truncados) en `agent-kits/` y `.claude/agent-kits/`.
- [ ] Versión bumpeada con `scripts/release.py`, `CHANGELOG.md`, `docs/CONVENTIONS.md` y `docs/FLOWS.md` actualizados.

---

## Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Recorte de `tools` o DoD rompe un flujo real de algún agente (C-04/C-05) | Media | Alto | Leer los flujos P1…Pn completos antes de recortar; pasada de humo por agente tras el cambio; C-08 valida la coherencia declarada |
| Prompts más largos (DoD ×8 + fragmentos shared) elevan el coste de contexto por invocación | Media | Medio | DoD limitado a 3-5 comprobaciones; fragmentos shared solo en los 3 casos con duplicación real |
| Indirection de `agent-kits/shared/`: el `find` no resuelve en algún scope o el empaquetado no lo incluye | Baja | Alto | Subtarea explícita en T-07: verificar `release.py`/empaquetado; fallback textual mínimo en los prompts |
| Linter demasiado estricto: falsos positivos en contribuciones externas | Media | Medio | Heurística laxa y documentada; mensaje de fallo con campo y patrón esperado (spec §Manejo de errores) |
| Falsos positivos de estilo en la revisión adversarial añaden fricción al ciclo | Media | Medio | Prompt acotado a gaps de corrección/requisitos; puerta manual descarta los de estilo; prueba con iniciativa de juguete (T-08) |
| Deriva frente a Claude Code (nuevos tiers de `model`, claves de frontmatter) | Baja | Medio | El linter centraliza el punto de actualización; supuesto documentado en la spec |

---

## Métricas de éxito

- Linter de plugin en verde en CI (0 violaciones) sobre el propio repo tras aplicar C-01…C-06 — autovalidación.
- Suite pytest completa en verde (tests existentes + tests nuevos del linter).
- 2/2 pruebas de auto-delegación enrutan al agente correcto sin nombrarlo.
- 1 ejecución de `/dev-cycle` de juguete con el paso adversarial ejecutado y reporte contra el plan.
- 0 duplicados de los 3 fragmentos extraídos fuera de sus fuentes únicas.
- Desviación real vs. estimado dentro del margen (+20 %): ≤ 20,7 h humanas y ≤ 7,25 h IA+supervisión (se cerrará con `/roadmap-metrics` y `/retro`).

---

## Siguiente paso

**Puerta de control:** este plan nace en `borrador` y requiere el **OK del usuario** antes de implementar. Con el OK, el handoff es al agente **`implementer`**, que ejecutará fase a fase sobre rama marcando [`tasks.md`](tasks.md) (ledger canónico). El volcado de tareas a **Jira** queda disponible vía la skill `jira-sync` cuando el usuario lo pida (no se ha activado en esta sesión).

---

## Changelog

| Fecha | Cambio |
|-------|--------|
| 2026-08-10 | Plan inicial (11 tareas, 4 fases) a partir de la evaluación `completado` con veredicto go; cerrada la incógnita opus vs. `inherit` (→ opus) y las decisiones de C-07 (puerta manual, solo cadena nativa) |

---

## Revisión adversarial (dogfooding de C-07 · 2026-08-10)

Antes de cerrar se ejecutó el propio mecanismo C-07: un subagente con **contexto fresco** revisó el diff contra este plan y `tasks.md`. Resultado: C-01…C-08 y T-01…T-11 **CUMPLEN**; dos gaps reales corregidos (no de estilo):

- **GAP-1 (alta) — descartado tras verificar:** el revisor señaló un espejo `.claude/agent-kits/` truncado. Verificado que el repo **no versiona** `.claude/` (0 ficheros; el bundle se *despliega* como `.claude/`). El criterio de "espejo" de T-04 se marcó **N/A**; era un artefacto del sandbox de la sesión.
- **GAP-2 (media) — corregido:** el plan (C-04) y el checkbox T-05 afirmaban "evaluator y planner sin `Edit`", pero ambos patchean back-links en `.md` existentes. Se reconcilió: **solo `pdfy` sin `Edit`**; el resto conserva `Edit` con la restricción "solo `.md`, nunca código" como comentario en el frontmatter. spec §C-04 y tasks T-05 actualizados para no mentir.

Cierre pendiente de **OK del usuario** → plan `completado`, spec `implementada`. Release (T-11) la ejecuta el usuario con `scripts/release.py`.
