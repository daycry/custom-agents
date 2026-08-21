---
generacion:
  inicio: 2026-08-11T12:45:00Z
  fin: 2026-08-11T13:40:00Z
  fuente: estimado          # retroactivo: el artefacto se generó ANTES de desplegar usage-meter
  tokens_reales: null       # estimación a juicio: ~75k facturables
  eur: null                 # precioTokens sin verificar (rates-verify)
  horas_ia: 0.25
  duracion: 15m
  ratio_usado: 300000       # default no calibrado
---

# 2026-08-11-coste-generacion

> Coste real de generación de artefactos (usage-meter) + calibración tokens→horas: evaluación de coste/esfuerzo para decidir si se aprueba medir con tokens reales lo que cuesta producir cada `.md` del ciclo y cada tarea, registrarlo en frontmatter/ledger, calibrar el ratio tokens→hora con `/retro` y presentar todas las duraciones en formato humano (`Xh Ym`).

| | |
|---|---|
| **Fecha** | 2026-08-11 |
| **Estado** | completado ✅ |
| **Prioridad global** | Media 🟡 |
| **Solicitante** | daycry |
| **Spec** | [`spec.md`](spec.md) |
| **Plan** | [`improvement-plan.md`](improvement-plan.md) + [`tasks.md`](tasks.md) (2026-08-11) — 4 fases · 10 tareas · 16,75 h base (20,1 h con margen) · ~1.044 € |
| **Características evaluadas** | 8 |

---

## Cuadro de mando

| Métrica | Total estimado | Confianza |
|--------|----------------|-----------|
| Esfuerzo humano | **19,2 h** (16,0 h base +20 %) | Media |
| Tiempo IA (ejecución) | **6,1 h** (+ 1,5 h supervisión) | Media |
| Coste | **~995 €** | Media |
| Tokens IA | **~1,69 M** (in 1,44 M / out 0,25 M) | Baja |
| Multiplicador productividad | **×2,5** | — |
| Características | **8** | — |

> ⚠️ **Incógnita que baja la confianza:** la fuente de tokens reales es la **transcripción JSONL de Claude Code**, un formato **interno, no API pública** (aunque estable y usado por herramientas como `ccusage`). Si el formato cambia o el entorno no expone `~/.claude/projects/`, el meter degrada a `fuente: estimado` sin bloquear — la degradación es parte del diseño, pero significa que el valor "medido" no está garantizado en todos los entornos. Verificación empírica temprana obligatoria (T de la Fase 1): leer una transcripción real del propio entorno antes de construir encima.

---

## Resumen ejecutivo

La spec (confirmada con el usuario el 2026-08-11) pide hacer visible el coste que hoy es invisible: **cuánto cuesta producir** la spec, la evaluación, el plan y el ledger — y cada tarea de implementación — con la máxima realidad posible. El corazón es un script determinista nuevo (**`usage-meter.py`**, C-01) que suma el `usage` real de la transcripción de la sesión entre un marcador de inicio y el cierre de cada artefacto; el resto es integración: bloque `generacion:` en el frontmatter (C-02), arranque/cierre del meter desde los agentes del ciclo (C-03), overhead de proceso en `/roadmap-metrics` (C-04), calibración del ratio tokens→hora en `/retro` (C-05), extrapolación a las tareas para que el worklog impute horas-IA **medidas** en vez de estimadas (C-06), defaults/documentación (C-07) y **formato humano de duraciones** en todo lo presentado (`XhYm` estilo Jira, C-08, añadido a petición del usuario). Decisión de fondo confirmada: **las fechas son contexto, los tokens son la medida, las horas se derivan de tokens × ratio calibrado** — nunca del reloj de pared. Se presupuestan **16,0 h base (19,2 h con margen), ~995 €** y ~1,69 M tokens. La evaluación soporta **aprobar con condición**: la dependencia del formato JSONL interno exige verificación empírica temprana y degradación obligatoria en todo el camino.

---

## Requerimientos recibidos

| ID | Característica | Requisito origen (ref.) | ¿Claro? |
|----|---------------|-------------------------|---------|
| C-01 | `usage-meter.py` (medición) | spec §Características C-01 + §Decisiones (fuente, qué se suma, sidechains, mecanismo, degradación) | ⚠️ ambiguo (formato JSONL interno) |
| C-02 | Frontmatter `generacion:` | spec §Características C-02 + §Decisiones ("Dónde vive el dato") + Decisión confirmada 2 | ✅ |
| C-03 | Integración en el ciclo | spec §Características C-03 + §Decisiones ("Quién arranca/cierra") | ✅ |
| C-04 | Overhead en `/roadmap-metrics` | spec §Características C-04 | ✅ |
| C-05 | Calibración en `/retro` | spec §Características C-05 + §Decisiones ("Calibración") | ✅ |
| C-06 | Medición por tarea → worklog | spec §Características C-06 + Decisión confirmada 5 | ⚠️ ambiguo (encaje con `worklog.py plan` y el ledger) |
| C-07 | Default del ratio + docs | spec §Características C-07 | ✅ |
| C-08 | Formato humano de duraciones | spec §Características C-08 + Decisión confirmada 6 (formato `XhYm` fijado por el usuario) | ✅ |

**Ambigüedades / información que falta:**

- **Estabilidad y presencia del formato JSONL (C-01).** No es API pública. En Cowork la ruta existe (`/root/.claude/projects/`), en CLI también, pero el esquema exacto de `usage` (nombres de campos de caché) hay que verificarlo empíricamente contra una transcripción real antes de fijar el parser. La spec ya exige degradación sin bloqueo.
- **Detección de sidechains (C-01).** El criterio "ficheros `.jsonl` modificados dentro de la ventana" es una heurística de mtime; puede colar mensajes de otra conversación paralela del mismo proyecto. Aceptable como primera versión (se documenta), pero baja la confianza de la precisión fina.
- **Encaje de C-06 con `worklog.py plan`.** Hoy las horas-IA por tarea salen de la estimación del plan (real→est). Sustituirlas por horas medidas exige decidir el punto exacto: la opción barata es que `/dev-cycle` pase las horas medidas como "real" al flujo existente (que ya prefiere real sobre estimado), sin tocar `worklog.py`. Se presupuesta esa opción; si hiciera falta tocar el script, +0,5 h.
- **Solape de marcadores (C-03).** Dos artefactos abiertos a la vez reparten mal el coste (los mismos mensajes caen en ambas ventanas). La spec lo documenta como limitación y ordena cerrar antes de abrir; no se intenta atribución fina por mensaje.
- **Ratio tokens→hora default (C-07).** No existe histórico (CALIBRATION.md sin estrenar). El default inicial es una convención declarada "no calibrada"; el valor real llegará con las primeras `/retro`. No bloquea: el frontmatter marca `ratio_usado` y `fuente`.

---

## Datos necesarios para una evaluación completa

- [x] **Requerimientos** completos y sin ambigüedades — salvo las incógnitas de formato JSONL y encaje con worklog marcadas
- [x] **Alcance** acotado (dentro/fuera bien delimitado; OTEL, tiempo humano medido y desglose por modelo, fuera)
- [x] **Criterios de aceptación / éxito** por característica (spec §Pruebas)
- [x] **Restricciones** (no bloquear nunca el flujo, no hardcodear rutas, degradación explícita, wall-clock solo contexto)
- [ ] **Dependencias externas** — formato JSONL de Claude Code **no verificado empíricamente** en este repo (verificación = primera tarea del plan)
- [x] **Contexto técnico** (patrón de scripts deterministas con tests ya rodado: worklog, qa-gate, ledger-lint; rates.json + rates-verify; formato CALIBRATION de /retro)
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

**Calibración con el histórico del repo** (evaluaciones cerradas como referencia): `qa-strict` = 19,0 h base (dos scripts Python con tests + prosa + plantilla); `token-diet` = 10,75 h base (sobre todo prosa + un script pequeño). Esta iniciativa se parece a un híbrido: **un script Python de tamaño medio-alto con tests** (C-01, análogo a `qa-gate.py` + `ledger-lint.py` juntos en complejidad de parsing: 4,5 h) más **prosa de integración** repartida en 6 piezas pequeñas (C-02…C-07, 10,5 h). El histórico avala que el coste de tokens es marginal (~4 %). La incertidumbre está en el **formato de la fuente** (JSONL interno) y en el encaje fino con `worklog.py`, no en el volumen de trabajo.

---

## Evaluación por característica

### C-01 — `usage-meter.py` (medición)

- **Requisito origen**: spec §Características C-01; §Decisiones (fuente, qué se suma, sidechains, mecanismo, degradación, no hardcodear).
- **Descripción**: script en `agent-kits/shared/` con `start`/`close`/`status` por artefacto: marcador (timestamp + posición por transcripción) en `.claude/usage-state.json`; al cerrar, suma `usage` (input/output/caché) de los mensajes nuevos, sidechains incluidas; emite JSON con tokens/€/horas/fuente. `--transcript-dir` para tests. Degradación a `estimado` sin romper. Tests pytest con fixtures JSONL sintéticas.
- **Complejidad**: Alta (parsing incremental por offset, ventanas, sidechains, degradaciones, conversiones).
- **Esfuerzo**: 4,5 h · confianza **Media** (el patrón está rodado; la incógnita es el esquema exacto del JSONL → primera tarea: verificarlo empíricamente).
- **Previsión IA**: 380k in / 70k out tok · ~10 €
- **Coste**: (4,5 h × 50 €/h) + 10,07 € = **~235 €**
- **Impacto / áreas afectadas**: nuevo `agent-kits/shared/usage-meter.py` + `test_usage_meter.py`; `.claude/usage-state.json` (nuevo estado).
- **Dependencias y prerequisitos**: ninguna interna; lee `rates.json` (existente) y `CALIBRATION.md` (si existe).
- **Riesgos**: formato JSONL cambia o difiere entre entornos (CLI vs Cowork); heurística de sidechains por mtime puede sobrecontar con sesiones paralelas (documentado como limitación).
- **Incógnitas / preguntas abiertas**: nombres exactos de los campos de caché en `usage`; codificación de la carpeta de proyecto. Se resuelven leyendo una transcripción real (T-01 del plan).

### C-02 — Frontmatter `generacion:` en artefactos

- **Requisito origen**: spec §Características C-02; Decisión confirmada 2 (frontmatter YAML).
- **Descripción**: bloque `generacion:` (inicio, fin, tokens_reales desglosado, eur, horas_ia, ratio_usado, fuente) en las plantillas de spec/evaluation (evaluator) y plan/tasks (planner), y en el `tasks.md` ligero de vía rápida. Artefactos legacy sin bloque siguen siendo válidos.
- **Complejidad**: Baja
- **Esfuerzo**: 1,0 h · confianza **Alta**
- **Previsión IA**: 100k in / 15k out tok · ~2 €
- **Coste**: (1,0 h × 50 €/h) + 2,42 € = **~52 €**
- **Impacto / áreas afectadas**: `agent-kits/evaluator/templates/spec.md` y `evaluation.md`, plantillas de `agent-kits/planner/templates/`, sección de tasks ligero en `commands/dev-cycle.md`.
- **Dependencias y prerequisitos**: C-01 (define el JSON que se vuelca al bloque).
- **Riesgos**: mínimos; YAML mal formado se cubre con el ejemplo fijo de la plantilla.
- **Incógnitas / preguntas abiertas**: ninguna material.

### C-03 — Integración en el ciclo

- **Requisito origen**: spec §Características C-03; §Decisiones ("Quién arranca/cierra el meter").
- **Descripción**: analyst/evaluator/planner ejecutan `start` al abrir su artefacto y `close` al cerrarlo (escribiendo el bloque en el frontmatter); `/dev-cycle` lo hace para el `tasks.md` de vía rápida. Re-cierre actualiza sin duplicar. Regla de "cerrar antes de abrir" documentada (solape reparte mal).
- **Complejidad**: Media (prosa en 3 agentes + 1 command, con el patrón `SHAREDKIT` existente).
- **Esfuerzo**: 2,0 h · confianza **Media**
- **Previsión IA**: 180k in / 30k out tok · ~5 €
- **Coste**: (2,0 h × 50 €/h) + 4,55 € = **~105 €**
- **Impacto / áreas afectadas**: `agents/analyst.md`, `agents/evaluator.md`, `agents/planner.md`, `commands/dev-cycle.md` (vía rápida).
- **Dependencias y prerequisitos**: C-01 (script) y C-02 (formato del bloque).
- **Riesgos**: los agentes olviden el `close` si la sesión se corta → cubierto por `status` (marcadores huérfanos) y por que el siguiente `close` del artefacto reutiliza el marcador.
- **Incógnitas / preguntas abiertas**: ninguna material.

### C-04 — Overhead de proceso en `/roadmap-metrics`

- **Requisito origen**: spec §Características C-04.
- **Descripción**: `roadmap-dashboard` lee `generacion:` de los artefactos de cada iniciativa y añade al informe de métricas la sección **coste de proceso** (tokens/€/horas de producir spec+eval+plan+tasks), separada del coste de implementación, con total de cartera. Sin bloque → "sin datos".
- **Complejidad**: Media
- **Esfuerzo**: 2,0 h · confianza **Media**
- **Previsión IA**: 180k in / 30k out tok · ~5 €
- **Coste**: (2,0 h × 50 €/h) + 4,55 € = **~105 €**
- **Impacto / áreas afectadas**: `skills/roadmap-dashboard/` (parser de frontmatter + salida `--metrics-md`), `commands/roadmap-metrics.md` (describir la sección nueva).
- **Dependencias y prerequisitos**: C-02 (formato del bloque). Independiente de C-03 en desarrollo (puede probarse con bloques escritos a mano).
- **Riesgos**: mezclar "sin datos" con 0 € distorsionaría el total → regla explícita de la spec (no inventar 0).
- **Incógnitas / preguntas abiertas**: presentación (columna vs sección); se decide en el plan, no cambia el coste.

### C-05 — Calibración en `/retro`

- **Requisito origen**: spec §Características C-05; §Decisiones ("Calibración", "Horas-IA").
- **Descripción**: `/retro` calcula el **ratio real tokens→hora** de la iniciativa cerrada (tokens medidos ÷ horas reales validadas) y lo escribe como columna en `CALIBRATION.md`; evaluator y `usage-meter.py` usan la mediana del histórico (precedencia CALIBRATION > default).
- **Complejidad**: Media
- **Esfuerzo**: 1,5 h · confianza **Media**
- **Previsión IA**: 140k in / 25k out tok · ~4 €
- **Coste**: (1,5 h × 50 €/h) + 3,66 € = **~79 €**
- **Impacto / áreas afectadas**: `commands/retro.md` (cálculo y columna nueva), formato de `docs/roadmap/CALIBRATION.md` (aún sin estrenar — esta iniciativa define su primera columna medida), prosa del evaluator (leer el ratio).
- **Dependencias y prerequisitos**: C-01/C-02 (necesita tokens medidos que comparar). `/retro` aún no se ha estrenado: no hay migración de histórico que hacer.
- **Riesgos**: pocas muestras al principio → mediana ruidosa; se marca nº de muestras junto al ratio.
- **Incógnitas / preguntas abiertas**: ninguna material.

### C-06 — Medición por tarea (extrapolación al worklog)

- **Requisito origen**: spec §Características C-06; Decisión confirmada 5 ("extrapolar a las tareas").
- **Descripción**: en Modo B, `/dev-cycle` abre marcador por `T-XX` al arrancar la tarea y lo cierra al completarla; las horas-IA **medidas** (tokens × ratio) entran como "real" en `tasks.md` y en el flujo `worklog.py plan` existente (que ya prefiere real sobre estimado). La supervisión sigue por `ratioSupervision`. `fuente: medido` viaja al ledger.
- **Complejidad**: Media-Alta (encaje con el flujo de imputación sin tocar la aritmética de jornada/banco).
- **Esfuerzo**: 3,0 h · confianza **Media** (opción presupuestada: pasar horas medidas como "real" sin tocar `worklog.py`; si hubiera que tocarlo, +0,5 h absorbibles por el margen).
- **Previsión IA**: 280k in / 50k out tok · ~7 €
- **Coste**: (3,0 h × 50 €/h) + 7,31 € = **~157 €**
- **Impacto / áreas afectadas**: `commands/dev-cycle.md` (marcador por tarea en Modo B), formato de columna real/fuente en `tasks.md` (plantilla del planner), prosa de imputación de `skills/jira-sync/SKILL.md` (de dónde sale la hora real).
- **Dependencias y prerequisitos**: C-01 (meter) y C-05 (ratio con el que derivar horas). Solo Modo B (en Modo A superpowers ejecuta y no hay marcador nuestro por tarea).
- **Riesgos**: doble contabilidad si la tarea se reabre (re-cierre debe sustituir, no sumar); tareas con revisión de dos lentes intercalada — decidir si los tokens del revisor van a la tarea o al bloque `[revisión]` (propuesta: revisor → `[revisión]`, coherente con jira-granularity).
- **Incógnitas / preguntas abiertas**: atribución de tokens del bucle reviewer→implementer entre intentos; primera versión: todo el intento N a la tarea, revisión aparte (ya trazada por `--attempt`).

### C-07 — Default del ratio + documentación

- **Requisito origen**: spec §Características C-07.
- **Descripción**: `estimation-defaults.md` gana el parámetro **ratio tokens→hora** (default declarado no-calibrado + precedencia CALIBRATION > default); docs: regla en CONVENTIONS, bucle medir→calibrar en FLOWS (diagrama 6), README del kit shared.
- **Complejidad**: Baja
- **Esfuerzo**: 1,0 h · confianza **Alta**
- **Previsión IA**: 90k in / 15k out tok · ~2 €
- **Coste**: (1,0 h × 50 €/h) + 2,28 € = **~52 €**
- **Impacto / áreas afectadas**: `agent-kits/shared/estimation-defaults.md`, `agent-kits/shared/README.md`, `docs/CONVENTIONS.md`, `docs/FLOWS.md`.
- **Dependencias y prerequisitos**: C-01…C-06 definidos (documenta lo construido).
- **Riesgos**: mínimos.
- **Incógnitas / preguntas abiertas**: valor del default inicial (convención; propuesta en el plan, marcada "calibrar cuanto antes").

### C-08 — Formato humano de duraciones

- **Requisito origen**: spec §Características C-08; Decisión confirmada 6 (formato exacto fijado por el usuario: "1h 32m, 34m, 1h").
- **Descripción**: helper único (`usage-meter.py fmt <horas>` o función compartida) que convierte horas decimales al estilo Jira compacto `XhYm` (`0,53` → `32m`; `1,53` → `1h 32m`; `18,0` → `18h`; omite la parte a cero; redondeo al minuto). Se aplica en todo lo presentado: bloque `generacion:` (campo legible junto al decimal), columnas de tiempo de `tasks.md`, informes de `/roadmap-metrics` y `/roadmap-status`, comentarios de Jira (plantilla de revisión incluida). La aritmética interna (worklog, jornada, banco) sigue en decimal, sin cambios.
- **Complejidad**: Baja
- **Esfuerzo**: 1,0 h · confianza **Alta** (helper trivial con tests; el grueso es aplicar el formato en los puntos de presentación existentes).
- **Previsión IA**: 90k in / 15k out tok · ~2 €
- **Coste**: (1,0 h × 50 €/h) + 2,28 € = **~52 €**
- **Impacto / áreas afectadas**: `agent-kits/shared/usage-meter.py` (+tests), plantillas del planner (columnas de tiempo), `skills/roadmap-dashboard/`, `agent-kits/shared/review-report.template.md`, prosa de presentación de `skills/jira-sync/SKILL.md`.
- **Dependencias y prerequisitos**: C-01 (vive en el mismo script). Aplicable de forma incremental: los puntos de presentación pueden adoptar el formato según se tocan.
- **Riesgos**: mínimos; único cuidado: no formatear los valores que Jira exige numéricos (el `timeSpent` del worklog ya va en formato nativo Jira, no cambia).
- **Incógnitas / preguntas abiertas**: ninguna material.

---

## Comparativa

| # | Característica | Complejidad | Horas (base) | Coste € | Tokens (in/out) | Prioridad | Confianza |
|---|---------------|-------------|--------------|---------|-----------------|-----------|-----------|
| C-01 | `usage-meter.py` (medición) | Alta | 4,5 h | ~235 € | 450k (380/70) | Alta 🟠 | Media |
| C-02 | Frontmatter `generacion:` | Baja | 1,0 h | ~52 € | 115k (100/15) | Alta 🟠 | Alta |
| C-03 | Integración en el ciclo | Media | 2,0 h | ~105 € | 210k (180/30) | Alta 🟠 | Media |
| C-04 | Overhead en `/roadmap-metrics` | Media | 2,0 h | ~105 € | 210k (180/30) | Media 🟡 | Media |
| C-05 | Calibración en `/retro` | Media | 1,5 h | ~79 € | 165k (140/25) | Media 🟡 | Media |
| C-06 | Medición por tarea → worklog | Media-Alta | 3,0 h | ~157 € | 330k (280/50) | Media 🟡 | Media |
| C-07 | Default del ratio + docs | Baja | 1,0 h | ~52 € | 105k (90/15) | Media 🟡 | Alta |
| C-08 | Formato humano de duraciones | Baja | 1,0 h | ~52 € | 105k (90/15) | Alta 🟠 | Alta |
| | **Total** | | **16,0 h** | **~837 €** | **~1,69 M** | | |

> El **Total** de la tabla es coste **base** (16,0 h × 50 € + ~37 € de tokens). El presupuesto con margen está abajo.

---

## Presupuesto total

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 16,0 h × 50 €/h | 800,00 € |
| Margen de contingencia | +20 % sobre desarrollo base | 160,00 € |
| Tokens IA (input) | 1,44 M tok × 13,80 €/M ⚠️ | 19,87 € |
| Tokens IA (output) | 0,250 M tok × 69,00 €/M ⚠️ | 17,25 € |
| **Total estimado (con margen)** | | **~995 €** |

> ⚠️ El coste de tokens (~35 €, un 3,7 % del total) usa precios **supuestos** pendientes de verificar (`rates-verify`); el riesgo económico está en las **horas** (parsing del JSONL y encaje con el worklog), no en los tokens.

---

## Productividad IA (humano vs. IA)

| KPI | Valor |
|-----|-------|
| Horas humanas estimadas | 19,2 h *(16,0 h base)* |
| Horas IA (ejecución) | 6,1 h *(5,1 h base; supuesto)* |
| Supervisión humana | 1,5 h *(25 % de las horas IA)* |
| **Horas totales (IA + supervisión)** | **7,6 h** |
| Horas ahorradas | 11,6 h |
| **Ahorro** | **~60 %** |
| **Multiplicador de productividad** | **×2,5** |
| FTE equivalentes *(opcional)* | ~0,05 |

> Horas mostradas **con el margen de contingencia (+20 %)** ya aplicado. El trabajo es agente-friendly (un script con tests siguiendo un patrón ya rodado + prosa de integración); la supervisión se concentra en lo empírico: validar el parser contra transcripciones reales de este entorno y comprobar que el bloque `generacion:` de una iniciativa de juguete cuadra con lo consumido.

---

## Recomendación

- **Veredicto**: **go CONDICIONADO** a la **verificación empírica del formato JSONL** como primera tarea (leer una transcripción real del entorno, confirmar campos de `usage` y codificación de carpeta) **antes** de construir el parser encima, y a que la **degradación a `estimado` sin bloqueo** se pruebe explícitamente (test obligatorio). El coste es contenido (~995 €) y el valor es alto: hace visible el coste del ciclo de producto, sustituye estimaciones a ojo por medidas reales y cierra el bucle de calibración que el plugin tenía diseñado (CALIBRATION.md) pero sin datos.
- **Quick wins**: **C-02** (1,0 h, define el contrato del dato), **C-08** (1,0 h, mejora visible en todas partes desde el primer día) y **C-07** (1,0 h). **C-01** es el núcleo: cara pero habilita todo.
- **Costosas / a valorar**: **C-01** (parsing robusto multi-entorno) y **C-06** (encaje con worklog sin doble contabilidad). C-06 puede diferirse a una segunda tanda si se quiere valor antes (C-01…C-05 ya entregan el overhead de proceso completo).
- **Orden sugerido**: **C-01 → C-08 → C-02 → C-03 → C-04 → C-05 → C-06 → C-07** — script primero (con la verificación empírica al frente) y el helper de formato con él (viven juntos y C-02 ya lo usa), contrato del dato, integración del ciclo, métricas, calibración, extrapolación a tareas y documentación al final.
- **Fuera de alcance recomendado**: se respeta el "Fuera" de la spec (OTEL, tiempo humano medido, desglose por modelo, panel histórico de ratios). No añadir aquí.

---

## Riesgos transversales

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| El formato JSONL cambia o difiere entre entornos (CLI vs Cowork vs futuras versiones) | Media | Alto (C-01) | Verificación empírica primera tarea; parser tolerante (campos ausentes → 0 con aviso); degradación a `estimado` testeada |
| Entorno sin transcripciones accesibles (permisos, contenedores exóticos) | Baja-Media | Medio | `fuente: estimado` + aviso; el flujo nunca se bloquea (regla de la spec) |
| Sidechains por mtime sobrecontabilizan con sesiones paralelas | Media | Bajo-Medio | Documentar la limitación; ventana por offset minimiza; atribución fina queda fuera |
| Doble contabilidad al reabrir tarea/artefacto | Media | Medio (C-06) | Re-cierre sustituye (no suma); test de idempotencia obligatorio |
| Ratio default no calibrado da horas poco creíbles al principio | Alta | Bajo | `ratio_usado` + `fuente` visibles en el frontmatter; `/retro` lo corrige con datos; marcado "no calibrado" |
| Solape de marcadores reparte mal el coste entre artefactos | Baja | Bajo | Regla "cerrar antes de abrir" en la prosa de C-03; documentado |
| Precios de tokens a 0 / viejos → € no calculable | Media | Bajo | Regla existente: `⚠️ verificar` + sugerir `rates-verify`; tokens se registran igual |

---

## Siguiente paso

Para **ejecutar** lo aprobado, genera el plan detallado con el agente **`planner`** (rellenará `improvement-plan.md` + `tasks.md` en esta misma carpeta y actualizará la fila **Plan** de esta evaluación y el campo `plan:` de la spec). Recomendación de aprobación: **las 8 características**, en el orden C-01 → C-08 → C-02 → C-03 → C-04 → C-05 → C-06 → C-07, con la **verificación empírica del JSONL** como primera tarea y la **degradación testeada** como criterio de cierre de C-01. Las horas y costes por característica de esta evaluación se heredan tal cual; `planner` no re-estima desde cero.

---

## Changelog

- **2026-08-11** — Evaluación inicial de la spec `coste-generacion`. 7 características, 15,0 h base (18,0 h con margen), ~935 €, ~1,59 M tokens. Veredicto: **go condicionado** (verificación empírica del formato JSONL + degradación testeada).
- **2026-08-11** — **Re-evaluación tras ampliar la spec a 8 características** (añadida C-08 "formato humano de duraciones", estilo Jira `XhYm`, pedida y fijada por el usuario en conversación). C-08 = 1,0 h base. Total **16,0 h base (19,2 h con margen), ~995 €, ~1,69 M tokens**. Veredicto sin cambios: **go condicionado**.
