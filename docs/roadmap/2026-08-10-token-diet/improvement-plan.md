# 2026-08-10-token-diet

> Dieta de tokens del plugin: disciplina de lectura en recon, filtrado de payloads Atlassian, progressive disclosure de prompts largos, disciplina de salida en handoffs y mini-skill `rates-verify` para cerrar el precio de tokens.

| | |
|---|---|
| **Fecha** | 2026-08-10 |
| **Estado** | borrador |
| **Tipo** | Refactor / Infra (optimización de consumo de tokens) |
| **Prioridad** | Media |
| **Solicitante** | daycry |
| **Responsable** | equipo de plugin (agente `implementer`) |
| **Spec** | [`spec.md`](spec.md) |
| **Evaluación** | [`evaluation.md`](evaluation.md) |

---

## Cuadro de mando

| Métrica | Estimado | Real | Confianza |
|--------|---------|------|-----------|
| Tiempo humano | **12,9 h** (10,75 h base +20 %) | 0 h | Media |
| Tiempo IA (ejecución) | **3,6 h** (+ 0,9 h supervisión) | 0 h | Media |
| Coste total | **~669 €** | 0 € | Alta (h) / Media (tokens ⚠️) |
| Tokens IA | **~1,24 M** (in 1,11 M / out 125 k) | 0 | Media |
| Multiplicador productividad | **×2,9** | — | — |
| Tareas | **8** | 0 hechas | — |

> Presupuesto **heredado de `evaluation.md`** por característica (C-01…C-05); el `planner` reparte esas horas/tokens en tareas, **no re-estima**. La Fase 3 (cierre) no añade horas base: se absorbe en el margen de contingencia (+20 %) — ver «Estimación por fase».

---

## Estimación por fase

Horas y tokens **base** (sin margen). El +20 % se aplica en el «Presupuesto económico».

| Fase | Estimado (h) | Tokens (in / out) | Coste € (base) |
|------|-------------|-------------------|---------|
| Fase 1 — Quick wins (C-01, C-04, C-02) | 4,75 | 510k / 50k | 248 |
| Fase 2 — Medianas (C-03, C-05) | 6,0 | 600k / 75k | 313 |
| Fase 3 — Cierre y verificación | 0 *(absorbido por margen)* | — | — |
| **Total** | **10,75 h** | **1,11 M / 125 k** | **561 €** |

> Fase 1 = C-01 (2,0 h) + C-04 (1,5 h) + C-02 (1,25 h). Fase 2 = C-03 (3,0 h, repartida documenter/nemesis) + C-05 (3,0 h, repartida core/integración). El total base **cuadra con la evaluación** (10,75 h / 561 € / ~1,24 M tokens). El coste base + margen (+20 %) da los **~669 €** del cuadro de mando.

---

## Presupuesto económico

**Coste = (horas × tarifa) + coste de tokens de IA.** Todos los importes en **EUR**.

### Supuestos (ajustables)

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | 50 €/h | Default del evaluator; no existe `.claude/rates.json` todavía |
| Modelo IA asumido | claude-opus-4-8 | Modelo previsto para la ejecución |
| Precio input | 13,80 € / 1M tokens | ⚠️ verificar — supuesto de trabajo (15 USD/M × 0,92); lo cierra C-05 |
| Precio output | 69,00 € / 1M tokens | ⚠️ verificar — supuesto de trabajo (75 USD/M × 0,92); lo cierra C-05 |
| Tipo de cambio | 1 USD = 0,92 € | Default |
| Ratio de supervisión | 25 % de las horas IA | Default |
| Margen de contingencia | 20 % | Sobre horas base (humanas e IA) |

### Desglose

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 10,75 h × 50 €/h | 537,50 € |
| Margen de contingencia | +20 % sobre desarrollo base | 107,50 € |
| Tokens IA (input) | 1,11 M tok × 13,80 €/M ⚠️ | 15,32 € |
| Tokens IA (output) | 125 k tok × 69,00 €/M ⚠️ | 8,63 € |
| **Total estimado (con margen)** | | **~668,95 € (~669 €)** |

> ⚠️ El coste de tokens (~24 €, ~4 % del total) usa precios **supuestos** pendientes de verificar; una desviación del ±50 % en la tarifa de tokens mueve el total menos de un 2 %. Cierre autorreferente: **C-05 (`rates-verify`)** es precisamente lo que elimina este `⚠️` en futuras evaluaciones y permitirá recalibrar el coste real de este mismo plan.

---

## Previsión de tokens (por fase)

Estimación del consumo de tokens del modelo por fase. Base: claude-opus-4-8 · precios de la tabla de supuestos.

| Fase | Input (tok) | Output (tok) | Total (tok) | Coste € |
|------|------------|-------------|-------------|---------|
| Fase 1 — Quick wins | 510k | 50k | 560k | 10,49 |
| Fase 2 — Medianas | 600k | 75k | 675k | 13,46 |
| Fase 3 — Cierre | — | — | — | 0 *(margen)* |
| **Total** | **1,11 M** | **125 k** | **~1,24 M** | **~23,95 €** |

**Método de estimación:** heredado de `evaluation.md` (no se re-estima). Base: nº de prompts/ficheros a leer (documenter 148 líneas + nemesis 173 en C-03; prompts de cadena en C-01/C-04; SKILL de `jira-sync` en C-02) × tamaño medio + generación de fragmentos, reestructuración de prompts y skill nueva con su test (C-05). Los tokens de la Fase 3 (lint, CHANGELOG, consolidación de README) son menores y quedan cubiertos por el margen de contingencia.

---

## Productividad IA (humano vs. IA)

Compara el esfuerzo **humano** estimado con el tiempo que tardaría un **agente de IA** en ejecutarlo (más la supervisión humana necesaria).

| KPI | Valor |
|-----|-------|
| Horas humanas estimadas | 12,9 h *(10,75 h base +20 %)* |
| Horas IA (ejecución) | 3,6 h *(3,0 h base; supuesto)* |
| Supervisión humana | 0,9 h *(25 % de las horas IA)* |
| **Horas totales (IA + supervisión)** | **4,5 h** |
| Horas ahorradas | 8,4 h |
| **Ahorro** | **65 %** |
| **Multiplicador de productividad** | **×2,9** |
| FTE equivalentes *(opcional)* | ~0,05 |

> Horas mostradas **con el margen de contingencia (+20 %)** ya aplicado sobre las horas base (humanas e IA). Multiplicador moderado a propósito: C-03 (criterio de corte por fase) y C-05 (validación empírica del parseo y del comportamiento ante red caída) exigen supervisión humana que no se comprime como una edición mecánica. Las tres primeras (C-01, C-04, C-02) sí son casi puro trabajo de IA.

---

## Resumen ejecutivo

Esta iniciativa recorta el **número de tokens** que consume el plugin —no el coste por token, ya cubierto por `agent-best-practices`— en los cuatro focos donde está el grueso real: el **recon** de los agentes (leer de más), los **payloads de Atlassian** (respuestas enormes por defecto), los **prompts largos** siempre cargados (documenter/nemesis) y la **acumulación de resúmenes** en el orquestador; más una mini-skill (`rates-verify`) que cierra el `⚠️ verificar` del precio de tokens. Son en su mayoría ediciones de prompts y fragmentos compartidos (`agent-kits/shared/`), una regla en skills existentes, una reestructuración de dos prompts largos y una skill nueva con WebFetch. No hay código de producto. Se ejecuta en dos tandas —quick wins baratos primero (C-01 → C-04 → C-02), luego los medianos (C-03 → C-05)— y una fase de cierre.

### Objetivos

- Reducir los tokens de recon aplicando `read-discipline.md` (grep/glob antes de `Read`, `Read` con límite, rutas ignoradas) en documenter, nemesis, evaluator y qa, sin perder cobertura de análisis.
- Reducir los tokens de handoff con `output-discipline.md` (mensaje final ≤ ~12 líneas de datos) en los agentes de cadena, y los payloads de Atlassian con `fields`/`maxResults`/`searchResultMode` explícitos.
- Cargar el detalle procedimental de documenter y nemesis **on-demand** (progressive disclosure) sin cambiar comportamiento y de forma **reversible por agente**.
- Cerrar el precio de tokens con `rates-verify`, que escribe `.claude/rates.json` (precios + `verificadoEl`) y **no inventa precio** si falla la red.

---

## Datos necesarios para un informe completo

- [x] **Requisitos funcionales** confirmados por el solicitante (spec `aprobada`, decisiones confirmadas el 2026-08-10)
- [x] **Alcance** cerrado (C-01…C-05 dentro; cachés propias, agentes «lite», telemetría y medición A/B fuera — spec §Alcance)
- [x] **Criterios de éxito / métricas** acordados (spec §Pruebas: inspección de prompts, prueba real+red-caída de `rates-verify`, lint verde)
- [x] **Accesos y credenciales** — solo dependencia externa blanda: doc de precios accesible por WebFetch para C-05 (degradación controlada si falla)
- [x] **Entornos** disponibles — trabajo sobre el propio repo del plugin; no requiere staging/prod
- [x] **Stakeholders** identificados (solicitante daycry; validación del usuario en la puerta del plan)
- [x] **Dependencias externas** mapeadas (doc de precios API para C-05; resto sin dependencias duras)
- [x] **Restricciones** conocidas (retrocompatibilidad vía fallback de una línea; sin deadline; no reinventar lo que trae Claude Code)
- [x] **Tarifa/hora y supuestos de coste** — defaults del evaluator (50 €/h) como base, no bloqueante; el precio de tokens queda `⚠️ verificar` y lo cierra C-05

---

## Análisis de impacto

- **`agent-kits/shared/read-discipline.md`** (nuevo) — reglas de recon compartidas; referenciado vía `$SHAREDKIT` con fallback de una línea.
- **`agent-kits/shared/output-discipline.md`** (nuevo) — regla de disciplina de salida en handoffs; misma mecánica de referencia + fallback.
- **`agents/documenter.md`, `agents/nemesis.md`, `agents/evaluator.md`, `agents/qa.md`** — adoptan `read-discipline.md` en su fase de recon; documenter/nemesis además adelgazan a flujo + punteros (C-03).
- **`agents/evaluator.md`, `agents/planner.md`, `agents/implementer.md`, `agents/qa.md`, `agents/documenter.md`** — adoptan `output-discipline.md` en su mensaje final.
- **`agent-kits/documenter/`, `agent-kits/nemesis/`** — ficheros de fase nuevos que cargan el detalle procedimental on-demand (C-03).
- **`skills/jira-sync/` (SKILL + scripts), `skills/roadmap-dashboard/`, `commands/roadmap-live.md`** — llamadas a Atlassian con `fields`/`maxResults`/`searchResultMode:"issues"` explícitos + regla documentada (C-02).
- **`skills/rates-verify/`** (nuevo: `SKILL.md` + script) — WebFetch a la doc de precios y escritura idempotente de **`.claude/rates.json`** (C-05).
- **`commands/setup.md`, `agents/evaluator.md`, `agents/planner.md`** — ofrecen/consumen `rates-verify` (dejan de marcar `⚠️ verificar` si `verificadoEl` es reciente).
- **`agent-kits/shared/README.md`, CHANGELOG, `docs/CONVENTIONS.md`/`docs/FLOWS.md` (si aplica)** — registro de los fragmentos nuevos y cierre documental (Fase 3).

---

## Cambios arquitectónicos

- **Fragmentos compartidos como fuente única (DRY).** `read-discipline.md` y `output-discipline.md` viven en `agent-kits/shared/` y se resuelven en runtime con `SHAREDKIT="$(find "$PWD/.claude" "$HOME/.claude" -type d -path '*agent-kits/shared' 2>/dev/null | head -1)"`, con **fallback de una línea** en cada agente si el fragmento no está (patrón ya usado por `estimation-defaults.md`/`confluence-optin.md`). No se rompe comportamiento en instalaciones parciales; solo se pierde la optimización.
- **Progressive disclosure reversible por agente (C-03).** El detalle paso-a-paso de las fases largas de documenter y nemesis se mueve a ficheros de su kit, dejando en el `.md` el flujo de alto nivel + punteros. El agente lee el detalle **cuando entra en la fase**. El corte se diseña para poder **revertir cada agente de forma aislada** sin tocar el otro ni el resto de la iniciativa.
- **`rates-verify` sin invención de datos.** La skill valida el rango del precio parseado **antes** de escribir; ante fallo de red/parseo mantiene el `⚠️ verificar` y avisa, sin escribir precios falsos. La escritura de `.claude/rates.json` es **idempotente** y respeta el esquema de `agent-kits/evaluator/templates/rates.example.json` (`precioTokens.input/output`) añadiendo `verificadoEl: YYYY-MM-DD`.
- **Filtrado Atlassian como política, no ajuste puntual.** Se documenta como regla en el SKILL de `jira-sync`: pedir siempre `fields` explícitos; si falta un campo, se añade a la lista, **nunca** se vuelve a «todos los campos».

---

## Archivos a crear/modificar

| Archivo | Acción | Propósito |
|---------|--------|-----------|
| `agent-kits/shared/read-discipline.md` | Crear | Reglas de recon (grep/glob antes de `Read`; `Read` con `limit`; rutas/globs a ignorar; leer fragmentos no ficheros completos salvo objeto de trabajo) |
| `agent-kits/shared/output-discipline.md` | Crear | Regla de handoff: mensaje final ≤ ~12 líneas, rutas + cifras + estado, sin recap |
| `agents/documenter.md` | Modificar | Adoptar `read-discipline.md` (P2) y `output-discipline.md`; adelgazar fases a flujo + punteros (C-03) |
| `agents/nemesis.md` | Modificar | Adoptar `read-discipline.md` (SAST); adelgazar fases a flujo + punteros (C-03) |
| `agents/evaluator.md` | Modificar | Adoptar `read-discipline.md` (P2) y `output-discipline.md`; consumir `rates-verify` |
| `agents/qa.md` | Modificar | Adoptar `read-discipline.md` (P1) y `output-discipline.md` |
| `agents/planner.md` | Modificar | Adoptar `output-discipline.md`; consumir `rates-verify` |
| `agents/implementer.md` | Modificar | Adoptar `output-discipline.md` |
| `agent-kits/documenter/` | Crear | Ficheros de fase con el detalle procedimental on-demand (C-03) |
| `agent-kits/nemesis/` | Modificar/Crear | Ficheros de fase con el detalle procedimental on-demand (C-03) |
| `skills/jira-sync/SKILL.md` + `skills/jira-sync/scripts/` | Modificar | `fields`/`maxResults`/`searchResultMode:"issues"` explícitos + regla documentada (C-02) |
| `skills/roadmap-dashboard/` | Modificar | Filtrado de campos en las lecturas de Atlassian (C-02) |
| `commands/roadmap-live.md` | Modificar | Filtrado de campos en las búsquedas Jira (C-02) |
| `skills/rates-verify/SKILL.md` | Crear | Skill: WebFetch a la doc de precios, parseo, escritura idempotente de `.claude/rates.json` |
| `skills/rates-verify/scripts/` | Crear | Script de parseo/validación de rango + escritura de `rates.json` + manejo de red caída |
| `commands/setup.md` | Modificar | Ofrecer `rates-verify` en el onboarding |
| `agent-kits/shared/README.md` | Modificar | Registrar los dos fragmentos nuevos |
| `CHANGELOG` / `docs/CONVENTIONS.md` / `docs/FLOWS.md` | Modificar (si aplica) | Cierre documental (Fase 3) |

---

## Dependencias y prerequisitos

- **C-01 y C-04** son independientes entre sí y del resto; comparten mecánica de adopción (`$SHAREDKIT` + fallback) → conviene ejecutarlos en la misma tanda.
- **C-02** es independiente; regla acotada sobre integraciones existentes.
- **C-03** no tiene dependencias duras, pero es la de más contexto (dos prompts largos) y mayor riesgo funcional; se hace antes que C-05.
- **C-05** depende de una condición externa blanda: la doc de precios accesible por WebFetch (degradación controlada si falla).
- **Fase 3 (cierre)** depende de que Fase 1 y Fase 2 estén completadas (registro en README/CHANGELOG y lint final).

---

## Criterios de aceptación (global)

- [ ] `agent-kits/shared/read-discipline.md` y `output-discipline.md` existen, se referencian vía `$SHAREDKIT` con fallback de una línea y están registrados en `agent-kits/shared/README.md`.
- [ ] documenter, nemesis, evaluator y qa referencian `read-discipline.md` en su recon; evaluator, planner, implementer, qa y documenter referencian `output-discipline.md` en su mensaje final (inspección de prompts).
- [ ] Las llamadas a Atlassian de `jira-sync`, `roadmap-dashboard` y `roadmap-live` declaran `fields` explícitos, `maxResults` acotado y `searchResultMode:"issues"`; la regla queda documentada en el SKILL de `jira-sync`.
- [ ] documenter y nemesis quedan como flujo de alto nivel + punteros, con el detalle en ficheros de su kit cargados on-demand; el comportamiento no cambia y **cada agente es reversible de forma aislada**.
- [ ] `rates-verify` con doc real escribe `.claude/rates.json` con precios input/output y `verificadoEl: YYYY-MM-DD`; con red caída **mantiene `⚠️ verificar` sin inventar precio** y avisa. Existe un test que cubre ambos caminos.
- [ ] `python scripts/lint_plugin.py` verde y `python3 agent-kits/shared/ledger-lint.py` sobre `tasks.md` sin incoherencias.

---

## Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Optimizar tokens degrada la calidad (recon insuficiente, handoff demasiado escueto, detalle C-03 no cargado a tiempo) | Media | Alto | Reglas que permiten leer/reportar de más cuando es legítimo; C-03 **reversible por agente**; contraste cualitativo con `/context` antes/después |
| Los fragmentos compartidos no se resuelven por `find` en algún scope | Baja | Medio | Fallback de una línea en cada agente; el comportamiento no se rompe, solo pierde la optimización |
| El formato de la doc de precios rompe el parseo de `rates-verify` | Media | Medio | Parseo adaptable + validación de rango antes de escribir; ante fallo no inventa, mantiene `⚠️ verificar` y avisa |
| Los `fields` de Atlassian se recortan de más y falta un campo usado | Media | Bajo | Política fija: añadir el campo a la lista explícita, nunca volver a «todos» |
| El ahorro real de tokens no es medible objetivamente en esta iteración | Alta | Bajo | Medición A/B fuera de alcance; el real por token entra en `CALIBRATION` vía `/retro`; se acepta evidencia cualitativa |

---

## Métricas de éxito

- Todos los agentes de recon referencian `read-discipline.md` y los de cadena `output-discipline.md` (verificable por inspección/grep).
- Menor consumo en una ejecución de documenter sobre un repo mediano, contrastable con `/context` antes/después (cualitativo).
- `.claude/rates.json` con `verificadoEl` reciente y sin `⚠️ verificar` en las evaluaciones posteriores a ejecutar C-05.
- `lint_plugin.py` y `ledger-lint.py` en verde; fragmentos nuevos listados en `agent-kits/shared/README.md`.

---

## Changelog del plan

| Fecha | Cambio | Autor |
|-------|--------|-------|
| 2026-08-10 | Creación del plan a partir de la evaluación `token-diet` (go). Presupuesto heredado por característica (C-01…C-05); 8 tareas en 3 fases; Fase 3 de cierre absorbida por el margen (delta 0 h). | planner |

---

## Siguiente paso

Con el **OK del plan** del usuario (puerta de control), el agente **`implementer`** lo ejecuta fase a fase sobre una rama, marcando `tasks.md` como **ledger canónico** (checkbox + estado por tarea). No hay `test-plan.md` (no hay UI): la validación es inspección de prompts + el test de `rates-verify` + `lint_plugin.py` verde, como criterios de aceptación. El **release queda a cargo del usuario**.

---

## Revisión adversarial de dos lentes (2026-08-10)

Dos subagentes con contexto fresco (conformidad con spec · calidad/robustez). Tres hallazgos reales, todos corregidos:

- **Ledger inflado (lente A):** T-06/T-07/T-08 marcaban un `scripts/` y un **test de `rates-verify` en CI** que no existen. Reconciliado: `rates-verify` es una **skill de prosa** que usa `WebFetch` (herramienta de agente, no invocable desde pytest), como confluence-publish/discovery/jira-sync; los criterios se corrigen a N/A con el motivo, sin fingir un test.
- **Sobre-declaración de C-01 (lente A):** el ledger/README decían que `qa` adoptaba `read-discipline.md` y no era cierto. Corregido **haciéndolo verdad**: qa referencia la disciplina de lectura en P1 para cuando explore código de la app.
- **Robustez de `rates-verify` (lente B, media):** faltaba la **validación de rango** del precio; un número plausible-pero-erróneo (tier de caché, plan mensual) habría pasado y se habría escrito como verificado. Añadido el paso 4 con cotas de cordura (input ~0,1-100 $/M, output ~0,5-500 $/M, output>input) → fuera de rango = "no verificable", no escribe.

Sin defectos en la resolución de variables `$SHAREDKIT/$DOCKIT/$NEMKIT`, en las excepciones de read/output-discipline, ni en los punteros de C-03. (Nota: `$DOCKIT/taxonomy.md` y `$NEMKIT/tools/*` son dependencias preexistentes del kit, fuera del alcance de esta iniciativa.)

Cierre pendiente de OK del usuario → plan `completado`, spec `implementada`. Release a cargo del usuario.
