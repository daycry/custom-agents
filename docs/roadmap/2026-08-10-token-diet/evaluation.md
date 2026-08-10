# 2026-08-10-token-diet

> Evaluación y presupuesto de la «dieta de tokens» del plugin (disciplina de lectura en recon, filtrado de payloads Atlassian, progressive disclosure de prompts largos, disciplina de salida en handoffs y mini-skill `rates-verify`) — soporta la decisión go/no-go y el orden de ejecución.

| | |
|---|---|
| **Fecha** | 2026-08-10 |
| **Estado** | completado ✅ |
| **Prioridad global** | Media 🟡 |
| **Solicitante** | jmano@mediapro.tv |
| **Spec** | [`spec.md`](spec.md) |
| **Plan** | [`improvement-plan.md`](improvement-plan.md) (+ [`tasks.md`](tasks.md)) |
| **Características evaluadas** | 5 |

---

## Cuadro de mando

| Métrica | Total estimado | Confianza |
|--------|----------------|-----------|
| Esfuerzo humano | **12,9 h** (10,75 h base +20 %) | Media |
| Tiempo IA (ejecución) | **3,6 h** (+ 0,9 h supervisión) | Media |
| Coste | **~669 €** | Alta (h) / Media (tokens ⚠️) |
| Tokens IA | **~1,24 M** (in 1,11 M / out 125 k) | Media |
| Multiplicador productividad | **×2,9** | — |
| Características | **5** | — |

---

## Resumen ejecutivo

La spec (confirmada con el usuario el 2026-08-10, en `borrador` a la espera de aprobar esta evaluación) ataca el **número de tokens** que consume el plugin —no el coste por token, que ya cubrió `agent-best-practices`— en los cuatro focos donde está el grueso real (recon de agentes, payloads de Atlassian, prompts largos siempre cargados y acumulación de resúmenes en el orquestador) más una mini-skill que resuelve el `⚠️ verificar` del precio de tokens. Son en su mayoría **ediciones de prompts y fragmentos compartidos** (C-01, C-04), una **regla en skills existentes** (C-02), una **reestructuración de dos prompts largos** (C-03) y una **mini-skill nueva con WebFetch** (C-05); no hay código de producto. Se presupuestan **10,75 h base (12,9 h con margen), ~669 €** y ~1,24 M tokens. El total queda **netamente por debajo** de las dos iniciativas comparables (`agent-best-practices` 16,5 h base, `qa-strict` 19 h base), coherente con que aquí no hay agente nuevo ni linter con tests. La evaluación soporta **aprobar la iniciativa completa** y ejecutarla en dos tandas: fragmentos y disciplina baratos primero (C-01 → C-04 → C-02), luego los medianos (C-03 → C-05).

---

## Requerimientos recibidos

Mapa del documento de origen a las características evaluadas.

| ID | Característica | Requisito origen (ref.) | ¿Claro? |
|----|---------------|-------------------------|---------|
| C-01 | Fragmento `read-discipline.md` + adopción | spec §Características C-01 + §Decisiones de diseño (fragmento compartido) | ✅ |
| C-02 | Filtrado de payloads Atlassian | spec §Características C-02 + §Decisiones de diseño (Payloads Atlassian) | ✅ |
| C-03 | Progressive disclosure de documenter y nemesis | spec §Características C-03 + §Decisiones de diseño (Prompts largos) | ✅ (riesgo de calidad, ver incógnitas) |
| C-04 | Fragmento `output-discipline.md` + adopción | spec §Características C-04 + §Decisiones de diseño (Disciplina de salida) | ✅ |
| C-05 | Mini-skill `rates-verify` | spec §Características C-05 + §Decisiones de diseño (Precio de tokens) + §Manejo de errores | ✅ |

**Ambigüedades / información que falta:**

- C-02: la spec no lista los `fields` mínimos por tipo de llamada (búsqueda JQL vs. lectura de Confluence); se asume que se derivan del uso real de `jira-sync`/`roadmap-live` durante la implementación. El §Manejo de errores ya fija la política («si falta un campo, se añade a la lista explícita; nunca se vuelve a "todos"»), lo que acota el riesgo.
- C-03: «sin cambiar comportamiento, solo cuándo se carga el detalle» es el criterio de éxito, pero el reparto exacto de qué queda inline (flujo de alto nivel + punteros) y qué se mueve a ficheros del kit se decide al reestructurar cada prompt; afecta al esfuerzo y a la confianza.
- C-05: el formato de la doc de precios de la API que parsea el WebFetch no está fijado (la propia spec §Supuestos lo asume adaptable); el parseo puede requerir 1-2 iteraciones. La política ante fallo de red ya está definida (no inventa precio, mantiene `⚠️ verificar`).

---

## Datos necesarios para una evaluación completa

- [x] **Requerimientos** completos y sin ambigüedades (tabla C-01…C-05 con detalle por característica y decisiones de diseño justificadas)
- [x] **Alcance** de cada característica acotado (sección «Alcance» con fuera-de-alcance explícito: cachés propias, agentes "lite", telemetría, medición A/B)
- [x] **Criterios de aceptación / éxito** por característica (sección «Pruebas»: inspección de prompts, prueba real+red-caída de `rates-verify`, `lint_plugin.py` verde, contraste cualitativo con `/context`)
- [x] **Restricciones** (retrocompatibilidad vía fallback de una línea en «Manejo de errores»; sin deadline; no reinventar lo que trae Claude Code)
- [x] **Dependencias externas** — solo una: la doc de precios accesible por WebFetch para C-05 (con degradación controlada si falla)
- [x] **Contexto técnico** disponible (estructura del plugin, patrón `agent-kits/shared`, resolución por `find` de CONVENTIONS regla 5)
- [ ] **Tarifa/hora y supuestos de coste** confirmados — no existe `.claude/rates.json`; se usan los defaults del evaluator (declarados abajo). No bloquea; además C-05 existe precisamente para cerrar el precio de tokens.

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

**Calibración con el histórico del repo** (no existe `docs/roadmap/CALIBRATION.md`; se usan las evaluaciones cerradas como referencia): `2026-08-10-agent-best-practices` (ediciones de prompts + fragmentos compartidos `agent-kits/shared` + linter con tests) = **16,5 h base**; `2026-08-10-qa-strict` (scripts + tests + hook + workflow) = **19 h base**. Esta iniciativa es de la **misma familia** (edición de prompts y fragmentos compartidos) pero de menor volumen: cuatro de las cinco características no introducen código —solo C-05 añade una mini-skill con un WebFetch y un pequeño parseo— y no hay agente nuevo ni linter. Por eso el total base estimado (**10,75 h**) queda deliberadamente **por debajo** de ambas referencias. El coste unitario del par «crear fragmento compartido + adoptarlo en N agentes» se toma directamente de C-06 de `agent-best-practices` (2,25 h base por el fragmento DRY con 4 referencias), lo que da alta confianza a C-01 y C-04. Con solo dos filas de histórico, se trata como indicio de calibración, no como ley.

---

## Evaluación por característica

### C-01 — Fragmento `read-discipline.md` + adopción

- **Requisito origen**: spec §Características C-01 + §Decisiones de diseño (dónde vive la disciplina de lectura / recon)
- **Descripción**: nuevo fragmento en `agent-kits/shared/` con las reglas de recon (grep/glob antes de `Read`; `Read` con `limit`; lista de rutas/globs a ignorar —`node_modules/`, `vendor/`, lockfiles, `dist/`, binarios, `.min.*`—; «lee fragmentos, no ficheros completos, salvo que el fichero sea el objeto de trabajo»). Lo referencian documenter (P2), nemesis (SAST), evaluator (P2) y qa (P1) vía `$SHAREDKIT` con fallback de una línea. Es donde la spec sitúa el **mayor ahorro** de tokens.
- **Complejidad**: Baja-Media (el fragmento es sencillo y objetivo; el coste está en adoptarlo con criterio en 4 agentes sin romper su flujo de recon)
- **Esfuerzo**: 2,0 h · confianza Alta (calibrado con C-06 de `agent-best-practices`)
- **Previsión IA**: 200 k in / 20 k out tok · ~4,1 €
- **Coste**: (2,0 h × 50 €) + tokens = **104 €**
- **Impacto / áreas afectadas**: `agent-kits/shared/read-discipline.md` (nuevo), `agents/documenter.md`, `agents/nemesis.md`, `agents/evaluator.md`, `agents/qa.md` (referencia + fallback), `agent-kits/shared/README.md`
- **Dependencias y prerequisitos**: ninguna dura; comparte patrón de adopción con C-04 (conviene hacerlos juntos, misma mecánica de `$SHAREDKIT` + fallback)
- **Riesgos**: reglas demasiado estrictas que impidan una lectura legítima (mitigado: el §Manejo de errores permite explícitamente leer el fichero entero cuando es el objeto de trabajo); indirection si el `find` de `$SHAREDKIT` falla en algún scope (mitigado con el fallback textual)
- **Incógnitas / preguntas abiertas**: ¿se valida la adopción en el `lint_plugin.py` (que cada agente de recon referencie el fragmento) o solo por inspección? A decidir en el plan

### C-02 — Filtrado de payloads Atlassian

- **Requisito origen**: spec §Características C-02 + §Decisiones de diseño (Payloads Atlassian) + §Manejo de errores
- **Descripción**: en `jira-sync` (búsquedas/creación) y en la skill `roadmap-dashboard` / comando `roadmap-live`, pedir siempre `fields` explícitos (solo los usados), `maxResults` acotado y `searchResultMode:"issues"`. Documentar el patrón como regla en el SKILL de `jira-sync`. Las respuestas por defecto del conector son enormes y solo se usa una fracción.
- **Complejidad**: Baja (regla acotada sobre integraciones existentes; sin lógica nueva)
- **Esfuerzo**: 1,25 h · confianza Alta
- **Previsión IA**: 130 k in / 12 k out tok · ~2,6 €
- **Coste**: (1,25 h × 50 €) + tokens = **65 €**
- **Impacto / áreas afectadas**: `skills/jira-sync/` (llamadas + regla documentada en el SKILL), `skills/roadmap-dashboard/`, `commands/roadmap-live.md`
- **Dependencias y prerequisitos**: ninguna; independiente del resto
- **Riesgos**: un `fields` demasiado justo deja fuera un campo realmente necesario (mitigado: la política del §Manejo de errores es añadirlo a la lista explícita, nunca volver a «todos los campos»); ahorro real dependiente del volumen de issues, no medible sin ejecución
- **Incógnitas / preguntas abiertas**: lista mínima de `fields` por tipo de llamada (búsqueda vs. lectura); se deriva del uso real durante la implementación

### C-03 — Progressive disclosure de documenter y nemesis

- **Requisito origen**: spec §Características C-03 + §Decisiones de diseño (Prompts largos) + §Supuestos
- **Descripción**: mover el detalle paso-a-paso de las fases largas de `documenter` (148 líneas) y `nemesis` (173) a ficheros de su kit (`agent-kits/documenter/`, `agent-kits/nemesis/`), que el agente lee **cuando entra en esa fase**, dejando en el `.md` el flujo de alto nivel + punteros. No cambia comportamiento, solo **cuándo** se carga el detalle.
- **Complejidad**: Media (reestructurar dos prompts largos sin alterar su comportamiento; decidir el corte entre lo que queda inline y lo que se carga on-demand)
- **Esfuerzo**: 3,0 h · confianza Media
- **Previsión IA**: 320 k in / 40 k out tok · ~7,2 €
- **Coste**: (3,0 h × 50 €) + tokens = **157 €**
- **Impacto / áreas afectadas**: `agents/documenter.md`, `agents/nemesis.md` (adelgazan a flujo + punteros), `agent-kits/documenter/` y `agent-kits/nemesis/` (ficheros de fase nuevos)
- **Dependencias y prerequisitos**: ninguna dura; es la característica con más lectura de contexto (dos prompts largos completos)
- **Riesgos**: **el mayor riesgo funcional de la iniciativa** — que sacar el detalle inline degrade la calidad del agente si no lo carga en el momento oportuno. Mitigación: la spec ya prevé revertir esta característica aislada sin afectar al resto y verificar en rodaje; el punto de decisión es el criterio de corte por fase
- **Incógnitas / preguntas abiertas**: ¿qué mínimo de contexto debe quedar siempre inline para que el agente sepa *cuándo* cargar cada fichero de fase? Se define al reestructurar cada prompt

### C-04 — Fragmento `output-discipline.md` + adopción

- **Requisito origen**: spec §Características C-04 + §Decisiones de diseño (Disciplina de salida)
- **Descripción**: nuevo fragmento en `agent-kits/shared/`: «tu mensaje final al orquestador es datos, no informe: ≤ ~12 líneas, rutas + cifras + estado, sin recap de pasos». Lo referencian los agentes de cadena (evaluator, planner, implementer, qa, documenter); el detalle para el usuario ya vive en los artefactos. Cada handoff se apila en el contexto del orquestador y se multiplica por ciclo, así que el ahorro es acumulativo.
- **Complejidad**: Baja (fragmento sencillo + una referencia por agente; misma mecánica que C-01)
- **Esfuerzo**: 1,5 h · confianza Alta
- **Previsión IA**: 180 k in / 18 k out tok · ~3,7 €
- **Coste**: (1,5 h × 50 €) + tokens = **79 €**
- **Impacto / áreas afectadas**: `agent-kits/shared/output-discipline.md` (nuevo), `agents/evaluator.md`, `agents/planner.md`, `agents/implementer.md`, `agents/qa.md`, `agents/documenter.md` (referencia + fallback), `agent-kits/shared/README.md`
- **Dependencias y prerequisitos**: ninguna; comparte mecánica con C-01 (hacerlos en la misma tanda)
- **Riesgos**: el límite de ~12 líneas puede recortar información que el orquestador necesita en algún handoff (mitigado: el detalle vive en los artefactos; el mensaje es puntero + cifras); ligera tensión con los DoD que piden «mostrar evidencia» (conciliar «evidencia» con «≤12 líneas» en el plan)
- **Incógnitas / preguntas abiertas**: ¿el límite es duro o una guía? ¿aplica igual a agentes que reportan a un humano directo y no a un orquestador? A precisar en el fragmento

### C-05 — Mini-skill `rates-verify`

- **Requisito origen**: spec §Características C-05 + §Decisiones de diseño (Precio de tokens) + §Manejo de errores + §Pruebas
- **Descripción**: skill que hace WebFetch a la doc de precios de la API de Claude, extrae input/output del modelo asumido y **escribe `.claude/rates.json`** (`precioTokensInput/Output`, `verificadoEl: YYYY-MM-DD`). evaluator/planner dejan de marcar `⚠️ verificar` si la fecha es reciente. Se ofrece en `/setup` y cuando una evaluación detecte el precio sin verificar. Elimina el supuesto que arrastra toda evaluación (incluida ésta).
- **Complejidad**: Media (única característica con lógica nueva: SKILL.md, WebFetch, parseo del precio, escritura idempotente de `rates.json`, manejo de red caída)
- **Esfuerzo**: 3,0 h · confianza Media
- **Previsión IA**: 280 k in / 35 k out tok · ~6,3 €
- **Coste**: (3,0 h × 50 €) + tokens = **156 €**
- **Impacto / áreas afectadas**: `skills/rates-verify/` (SKILL.md + assets), `.claude/rates.json` (salida), `commands/setup.md` (ofrecerla), referencia desde `agents/evaluator.md`/`agents/planner.md`; casa con la plantilla `agent-kits/evaluator/templates/rates.example.json` existente
- **Dependencias y prerequisitos**: dependencia externa blanda (doc de precios accesible por WebFetch); degradación controlada si falla
- **Riesgos**: el formato de la doc de precios cambia y rompe el parseo (mitigado: la spec asume adaptar el parseo al formato real; ante fallo no inventa precio, mantiene `⚠️ verificar` y avisa); riesgo de escribir un `rates.json` con un precio mal parseado — validar el rango antes de escribir
- **Incógnitas / preguntas abiertas**: ¿qué antigüedad de `verificadoEl` se considera «reciente» para no volver a marcar `⚠️`? ¿el WebFetch necesita autenticación o la doc es pública? A confirmar en el plan

---

## Comparativa

Ordenada por tanda recomendada (baratas de alto impacto primero, medianas después).

| # | Característica | Complejidad | Horas | Coste € | Tokens | Prioridad | Confianza |
|---|---------------|-------------|-------|---------|--------|-----------|-----------|
| C-01 | Fragmento `read-discipline.md` + adopción | Baja-Media | 2,0 h | 104 € | 220 k | Alta | Alta |
| C-04 | Fragmento `output-discipline.md` + adopción | Baja | 1,5 h | 79 € | 198 k | Alta | Alta |
| C-02 | Filtrado de payloads Atlassian | Baja | 1,25 h | 65 € | 142 k | Alta | Alta |
| C-03 | Progressive disclosure documenter/nemesis | Media | 3,0 h | 157 € | 360 k | Media | Media |
| C-05 | Mini-skill `rates-verify` | Media | 3,0 h | 156 € | 315 k | Media | Media |
| | **Total (base, sin margen)** | | **10,75 h** | **561 €** | **~1,24 M** | | |

---

## Presupuesto total

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 10,75 h × 50 €/h | 537,50 € |
| Margen de contingencia | +20 % sobre desarrollo base | 107,50 € |
| Tokens IA (input) | 1,11 M tok × 13,80 €/M ⚠️ | 15,32 € |
| Tokens IA (output) | 125 k tok × 69,00 €/M ⚠️ | 8,63 € |
| **Total estimado (con margen)** | | **~669 €** |

> ⚠️ El coste de tokens (~24 €, un 4 % del total) usa precios **supuestos** pendientes de verificar; una desviación del ±50 % en la tarifa de tokens mueve el total menos de un 2 %. Cierre autorreferente: C-05 (`rates-verify`) es precisamente lo que eliminaría este `⚠️` en futuras evaluaciones.

---

## Productividad IA (humano vs. IA)

Compara el esfuerzo **humano** estimado con el tiempo que tardaría un **agente de IA** en implementarlo (más la supervisión humana).

| KPI | Valor |
|-----|-------|
| Horas humanas estimadas | 12,9 h *(10,75 h base)* |
| Horas IA (ejecución) | 3,6 h *(3,0 h base; supuesto)* |
| Supervisión humana | 0,9 h *(25 % de las horas IA)* |
| **Horas totales (IA + supervisión)** | **4,5 h** |
| Horas ahorradas | 8,4 h |
| **Ahorro** | **65 %** |
| **Multiplicador de productividad** | **×2,9** |
| FTE equivalentes *(opcional)* | ~0,05 |

> Horas mostradas **con el margen de contingencia (+20 %)** ya aplicado sobre las horas base (humanas e IA). El multiplicador es moderado a propósito: C-03 (criterio de corte por fase) y C-05 (validación empírica del parseo y del comportamiento ante red caída) requieren supervisión humana que no se comprime como una edición mecánica. Las tres primeras (C-01, C-04, C-02) sí son casi puro trabajo de IA.

---

## Recomendación

- **Veredicto**: **go** — coste contenido (~669 €), por debajo de las dos iniciativas comparables de la misma familia, riesgo bajo en 4 de 5 características (fragmentos con fallback + regla acotada) y valor acumulativo (el ahorro de recon y de handoffs se multiplica por cada ciclo de `/dev-cycle`).
- **Quick wins** (bajo coste, alto valor): **C-01, C-04, C-02** — 4,75 h base / 248 € en total; los dos fragmentos comparten mecánica de adopción y C-02 es una regla acotada sobre integraciones existentes. Atacan el mayor ahorro (recon) y el más recurrente (handoffs) con riesgo mínimo.
- **Costosas / a valorar**: **C-03** (mayor riesgo funcional: no degradar la calidad de documenter/nemesis; reversible de forma aislada) y **C-05** (única con lógica nueva y dependencia externa). Ambas se recomiendan igualmente: C-05 cierra el `⚠️ verificar` que arrastra toda evaluación.
- **Orden sugerido**: **C-01 → C-04 → C-02** (tanda barata de alto impacto; los fragmentos primero por compartir mecánica) → **C-03 → C-05** (medianas; C-03 antes que C-05 por ser la de más contexto y mayor riesgo, se valida el comportamiento antes de rematar con la skill). C-05 al final permite verificar precios reales y recalibrar el coste de tokens del propio plan.
- **Fuera de alcance recomendado**: mantener lo que la spec ya excluye (cachés de prompt propias, agentes «lite», telemetría de tokens propia, medición A/B automatizada) — Claude Code ya cubre caché y `/cost`/`/context`, y el real por token entrará en `CALIBRATION` vía `/retro`.

---

## Riesgos transversales

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Los fragmentos compartidos no se resuelven por `find` en algún scope (proyecto/usuario/plugin) | Baja | Medio | Fallback de una línea en cada agente (spec §Manejo de errores); el comportamiento no se rompe, solo pierde la optimización |
| Optimizar por ahorrar tokens degrada la calidad (recon insuficiente, handoff demasiado escueto, detalle no cargado en C-03) | Media | Alto | Reglas que permiten leer/reportar de más cuando es legítimo; C-03 reversible aislada; contraste cualitativo con `/context` antes/después (spec §Pruebas) |
| El ahorro de tokens no es medible objetivamente en esta iteración (medición A/B queda fuera de alcance) | Alta | Bajo | La spec lo asume: el real por token entra en `CALIBRATION` vía `/retro`; se acepta evidencia cualitativa por ahora |
| Los `fields` de Atlassian se recortan de más y falta un campo usado | Media | Bajo | Política fija: añadir el campo a la lista explícita, nunca volver a «todos» (spec §Manejo de errores) |
| `lint_plugin.py` no cubre la adopción de los fragmentos y aparece deriva doc↔realidad | Media | Medio | Decidir en el plan si el linter valida las referencias a `read-discipline.md`/`output-discipline.md`; si no, inspección documentada |

---

## Siguiente paso

Para **ejecutar** lo aprobado, genera el plan detallado con el agente **`planner`** (rellenará `improvement-plan.md` + `tasks.md` en esta misma carpeta `docs/roadmap/2026-08-10-token-diet/`). Recomendación de aprobación: **las cinco características (C-01…C-05)**, en dos tandas —quick wins `C-01 → C-04 → C-02`, luego medianas `C-03 → C-05`—. Secuencia entre ellas: C-01 y C-04 comparten mecánica de fragmento compartido (hacerlos juntos); C-03 antes que C-05. El `planner` heredará las horas y costes de esta evaluación por característica —no re-estima desde cero— y actualizará la fila **Plan** de esta evaluación y el campo `plan:` de la spec al crear el plan.

---

## Changelog

- **2026-08-10** — Evaluación inicial de la spec `token-diet` (5 características). Estado `en-revision`; pendiente puerta go/no-go del usuario. Sin `.claude/rates.json`: defaults del evaluator; precio de tokens `⚠️ verificar`.
