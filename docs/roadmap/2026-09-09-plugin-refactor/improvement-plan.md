---
design: design.md         # `aprobado` 2026-09-10 · opción O1 (ADR-016 `propuesta`) — el plan la respeta, no la rediseña
test-plan: n/a (sin UI)   # marcador de C-08 (E1): esta iniciativa NO tiene UI. Hoy lo lee una persona; tras T-13 lo leen `dev-cycle` (Fase 3) y `qa` (sale limpio sin pedir regenerar). Primera iniciativa que lo usa (ADR-017 `propuesta`)
generacion:
  inicio: 2026-09-10T11:55:46Z
  fin: 2026-09-10T12:00:57Z
  fuente: medido           # intento 3 (cierre y puertas sobre los borradores del intento 2). Tokens leídos de las transcripciones con el parser del repo + filtro `timestamp >= inicio − 60 s` (17 respuestas; 5.765 registros previos descartados). El marcador lo abrió el kit en caché del plugin (1.13.0, anterior a C-13 (i)): `transcriptDir: null`, `offsets: {}` → `close` oficial degradó a estimado; sin filtro habría sumado el histórico entero (el caso de T-04). `duracion` = tokens ÷ ratio; reloj de la ventana 5m11s. Los dos intentos anteriores (muertos por API) se descartaron y NO se acumulan: el 2.º midió 1,20 h IA / 7,76 € escribiendo los borradores
  tokens_reales: { entrada: 459, salida: 25431, cache_creacion: 216259, cache_lectura: 4637516, respuestas: 17 }
  eur: 3.96
  horas_ia: 0.51
  duracion: 31m
  ratio_usado: 479326            # CALIBRATION.md (mediana de 6)
---

# 2026-09-09-plugin-refactor

> Refactor medido del plugin en cinco fases y cuatro tramos de revisión: bloque (a) con cero cambio de comportamiento sobre los cinco hotspots (32 → ≤ 16 funciones largas) y un solo mecanismo de copias declaradas (O1); bloque (b) con los huecos de encadenamiento E1–E10 más el E11 descubierto hoy, presupuestado como propuesta.

| | |
|---|---|
| **Fecha** | 2026-09-10 |
| **Estado** | borrador |
| **Tipo** | Refactor (bloque a) + Bugfix de contratos entre piezas (bloque b) |
| **Prioridad** | Alta |
| **Solicitante** | usuario (petición del 2026-09-09 tras tres rondas de corrección sobre `task-brief.py`) |
| **Responsable** | `implementer` (ejecución) · `/dev-cycle` (orquestación, revisión por tramo) |
| **Spec** | [`spec.md`](spec.md) — `aprobada` (2026-09-10) |
| **Evaluación** | [`evaluation.md`](evaluation.md) — `completado`, go con cuatro condiciones |
| **Diseño** | [`design.md`](design.md) — `aprobado`, opción **O1** (registro `copias.json` + un test de identidad + comprobación del linter) · [`ADR-016`](../../knowledge/adr/ADR-016-copias-declaradas-con-test-de-identidad.md) `propuesta` |
| **Análisis** | [`analysis.md`](analysis.md) — fuente única del alcance (§1–§9, §8-bis) · línea base [`code-health-baseline.json`](code-health-baseline.json) |
| **Test-plan** | **n/a (sin UI)** — marcador de C-08 en el frontmatter de este fichero. Sin `test-plan.md` por diseño, no por olvido: `qa` no tiene E2E que ejecutar; la prueba del bloque (a) es la suite existente + `code-health --baseline`, la del bloque (b) son tests unitarios con mutante y `evals/check.py` |

---

## Cuadro de mando

| Métrica | Estimado | Real | Confianza |
|--------|---------|------|-----------|
| Tiempo humano | **88,8 h** (74,0 h base +20 %) | 0 h | Baja (el histórico nunca ha validado horas humanas — `CALIBRATION.md` aprendizaje 2) |
| Tiempo IA (ejecución) | **10,6 h** (8,83 h base +20 %; + 2,65 h supervisión) | 0 h | Media (`memory-retrieval`: IA real +66 %; aquí la corrección post-revisión ya es línea propia, T-21) |
| Coste total | **~4.479 €** (3.734 € base; 4.440 € horas + ~39 € tokens con margen) | 0 € | Media |
| Tokens IA | **5,08 M facturables** (in 3,71 M / out 0,56 M / caché creación 0,81 M; + ~9,6 M lectura de caché) | 0 | Baja |
| Multiplicador productividad | **×6,7** | — | — |
| Tareas | **22** (19 de producto + 3 de proceso) en 5 fases · 4 tramos de revisión | 0 hechas | — |

**Herencia de la evaluación (regla: no se re-estima).** La evaluación cerró **75,0 h base / 90,0 h con margen / ~4.540 €**. Este plan hereda cada característica tal cual y declara tres diferencias, todas fijadas por la ejecución de hoy: **P-1 (`architect`, 2,0 h) ya está hecha** (`design.md` `aprobado`, medido 0,71 h IA / 9,16 €) → fuera del plan; **C-13 (i) ya está hecha** en la vía rápida `2026-09-10-usage-meter-transcripts` (cerrada, con retro, en `master` `8fee28a`) → de C-13 quedan 3,0 h de las 4,0 h; **E11 entra como propuesta C-14** (+2,0 h, T-19; opt-out en la puerta del plan). Neto: 75,0 − 2,0 − 1,0 + 2,0 = **74,0 h base**. El resto de cifras por característica es idéntico a la evaluación.

---

## Estimación por fase

Horas **base** (sin colchón); entre paréntesis, con el margen del 20 %. Tokens facturables in / out (la creación de caché va aparte en la previsión). Coste base = horas × 50 € + tokens.

| Fase | Tramo de revisión | Estimado (h) | Tokens (in / out) | Coste € |
|------|---|-------------|-------------------|---------|
| Fase 1 — Línea base limpia y la cicatriz (C-04 · C-05 · C-01 · C-13 ii-a) | **R1** | 11,5 (13,8) | 452k / 68k | 580 |
| Fase 2 — Los otros cuatro hotspots (C-02, uno por tarea) | **R2** | 14,0 (16,8) | 560k / 84k | 706 |
| Fase 3 — Un solo mecanismo de copias declaradas (C-03 sobre O1) | **R3** | 4,0 (4,8) | 175k / 26k | 202 |
| Fase 4 — Encadenamiento E1–E11 (C-12 · C-11 · C-08 · C-06 · C-09 · C-07 · C-13 ii-b · C-10 · C-14) | **R4** | 30,5 (36,6) | 1.276k / 190k | 1.539 |
| Fase 5 — Proceso: revisión por tramo, corrección y cierre (P-2 · P-3 · P-4) | — | 14,0 (16,8) | 631k / 96k | 707 |
| **Total** | 4 tramos | **74,0 h (88,8 h)** | **3.094k / 464k** | **3.734 € (4.479 € con margen)** |

---

## Presupuesto económico

**Coste = (horas × tarifa) + coste de tokens de IA.** Todos los importes en **EUR**.

### Supuestos (ajustables)

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | 50 €/h | `.claude/rates.json` `tarifaHora` |
| Modelo IA asumido | claude-opus-4-8 | `rates.json` `modeloIA` |
| Precio input | 5 USD / 1M (4,60 €) | verificado 2026-08-18 con `rates-verify` (23 días; fiable hasta 90) |
| Precio output | 25 USD / 1M (23,00 €) | ídem |
| Caché creación / lectura | 6,25 / 0,50 USD por 1M | ídem; la lectura de caché no cuenta para horas pero sí para € (`CALIBRATION.md` aprendizaje 4) |
| Tipo de cambio | 1 USD = 0,92 € | **supuesto** fijo de `rates.json` — ⚠️ verificar antes de facturar |
| Margen de contingencia | 20 % | sobre horas base humanas e IA |
| Ratio de supervisión | 25 % de las horas IA | `rates.json` `ratioSupervision` |
| Ratio tokens → hora IA | 479.326 tok/h | mediana de `docs/roadmap/CALIBRATION.md` (precedencia sobre el default 300.000) — heredado de la evaluación |
| Coste de tokens por hora IA | ≈ 3,68 €/h | heredado de la evaluación (reparto 73 % in · 11 % out · 16 % caché creación; lectura de caché ≈ 1,9× facturables) |
| Horas humanas | estimación «si lo hiciera un desarrollador sin IA» | **nunca validadas** en este repo (0 h humanas reales en las 9 filas de `CALIBRATION.md`) → confianza Baja |
| `duracion` de `usage-meter close` | derivada de tokens ÷ ratio, **no de reloj** (`cmd_close`: `fmt_horas(horas)`) | observado por el `architect` (`26m` con `inicio`/`fin` separados 10m37s). T-04 añade `duracion_reloj` aditivo; `duracion` no cambia de semántica (lo consumen dashboards) |

### Desglose

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 74,0 h × 50 €/h | 3.700,00 € |
| Margen de contingencia | +20 % sobre desarrollo base (14,8 h) | 740,00 € |
| Tokens IA (input) | 3,71 M tok × 5 USD/M × 0,92 | 17,07 € |
| Tokens IA (output) | 0,56 M tok × 25 USD/M × 0,92 | 12,88 € |
| Tokens IA (creación de caché) | 0,81 M tok × 6,25 USD/M × 0,92 | 4,66 € |
| Tokens IA (lectura de caché) | ~9,6 M tok × 0,50 USD/M × 0,92 | 4,42 € |
| **Total estimado (con margen)** | | **≈ 4.479 €** |

> Base sin margen: 3.700 € + 32,4 € de tokens = **3.734 €**. Diferencia con la evaluación (4.540 €): −122 € por P-1 hecha, −61 € por C-13 (i) hecha, +121 € por C-14 (E11, propuesta). Si el usuario descarta C-14 en la puerta del plan: **86,4 h · ~4.358 €**.

---

## Previsión de tokens (por fase)

Estimación del consumo de tokens del modelo por fase. Base: claude-opus-4-8 · precios de la tabla de supuestos. Cifras **base**; con margen, ×1,2.

| Fase | Input (tok) | Output (tok) | Caché creación (tok) | Total facturable (tok) | Coste € |
|------|------------|-------------|---|-------------|---------|
| Fase 1 | 452k | 68k | 99k | 619k | 4,7 |
| Fase 2 | 560k | 84k | 123k | 767k | 5,9 |
| Fase 3 | 175k | 26k | 38k | 239k | 1,8 |
| Fase 4 | 1.276k | 190k | 279k | 1.745k | 13,4 |
| Fase 5 | 631k | 96k | 137k | 864k | 6,6 |
| **Total base** | **3.094k** | **464k** | **676k** | **4.234k** | **32,4 €** |
| **Total con margen (+20 %)** | **3.713k** | **557k** | **811k** | **5.081k** | **38,9 €** |

**Método de estimación:** heredado de la evaluación por característica (tokens = horas IA × 479.326, repartidos 73/11/16). Las horas IA de cada característica salen de su esfuerzo humano ÷ ~10 (ratio observado en las evaluaciones medidas de este repo) y se reparten entre tareas en proporción a las horas humanas de cada una. Las tareas de refactor de código (Fases 1-3) llevan más lectura (cada hotspot 600-970 líneas + su suite) que escritura; las de prosa (C-06, C-08, C-09, C-11) más lectura de piezas descritas que generación. La lectura de caché no entra en horas.

---

## Productividad IA (humano vs. IA)

Compara el esfuerzo **humano** estimado con el tiempo que tardaría un **agente de IA** en ejecutarlo (más la supervisión humana necesaria). Cifras aproximadas; los supuestos están en la tabla de arriba.

| KPI | Valor |
|-----|-------|
| Horas humanas estimadas | 88,8 h (74,0 h base) |
| Horas IA (ejecución) | 10,6 h (8,83 h base) |
| Supervisión humana | 2,65 h (25 % de las horas IA) |
| **Horas totales (IA + supervisión)** | **13,25 h** |
| Horas ahorradas | 75,55 h |
| **Ahorro** | **85 %** |
| **Multiplicador de productividad** | **×6,7** |
| FTE equivalentes *(opcional)* | 0,47 |

> Horas mostradas **con el margen de contingencia (+20 %)** ya aplicado sobre las horas base (humanas e IA). Las horas IA son un supuesto derivado (tokens ÷ 479.326); la única muestra comparable (`memory-retrieval`: código + tests + hooks) salió **+66 %** sobre lo estimado, y las líneas T-20/T-21 absorben esa desviación si la revisión encuentra lo que suele. Con C-13 (i) ya en `master`, esta será la **primera iniciativa medida de verdad en Windows** (`fuente: medido` en cada tarea): la retro comparará estas cifras con reloj y tokens reales.

---

## Resumen ejecutivo

El análisis midió antes de pedir: 104 funciones > 30 líneas, **32 de ellas en los cinco hotspots** que cambian cada semana (`lint_plugin.py` 9 · `build_dashboard.py` 8 · `doctor.py` 8 · `task-brief.py` 4 · `knowledge-find.py` 3, re-medido hoy con `--top 1000`), un `main()` de 160 líneas en `task-brief.py` y un 7,6 % de duplicación que **es diseño, no deuda** (scripts que viajan sueltos). El `architect` cerró la única decisión abierta con **O1**: un registro `agent-kits/shared/copias.json`, un test de identidad byte a byte y una comprobación del linter — y con ello **C-03 se encoge**: no hay copias accidentales, hay cuatro mecanismos de guardarraíl que se unifican en uno.

Este plan ejecuta los dos bloques de la spec en **cinco fases y cuatro tramos de revisión**. Las Fases 1-3 son el bloque (a): cero cambio de comportamiento, aceptado por `code-health.py --baseline` («↓ mejora» en funciones largas, nunca «↑ empeora» salvo el reloj del TODO) y por **identidad de la suite test a test** (no «todo verde»: en Windows hay ~39 fallos de entorno preexistentes que no son regresión). La Fase 4 es el bloque (b): los diez huecos de encadenamiento E1–E10 menos lo ya pagado (E8 es C-05 de `brief-budget`; C-13 (i) se cerró hoy en la vía rápida `usage-meter-transcripts`), más **E11** —`tests/test_cifras_medidas.py` ancla cifras vivas del corpus en documentos históricos y se rompe al abrir o cerrar cualquier iniciativa (29 fallos hoy)— que se presenta como **propuesta C-14 con su coste**, no se cuela. La Fase 5 son las tres líneas de proceso que la evaluación prohíbe recortar (condición 2 del go).

Las cuatro condiciones del go son **aristas del grafo**, no notas: T-09 (C-03) depende de `design.md` `aprobado` (cumplida); las líneas de proceso son tareas con horas propias; C-01 (T-03) precede a `brief-budget` y toda la Fase 2 precede a F2 de `project-specialization`; las dos excepciones al «cero cambio de comportamiento» (T-01 cuenta menos TODO, T-02 añade `--exclude-path`) están declaradas en el ledger y T-02 toma la **segunda línea base** con el flag nuevo.

### Objetivos

- Funciones > 30 líneas en los cinco hotspots: **32 → ≤ 16**, ninguna nueva > 60 (`task-brief` 4 → ≤ 2 · `knowledge-find` 3 → ≤ 1 · `doctor` 8 → ≤ 4 · `build_dashboard` 8 → ≤ 4 · `lint_plugin` 9 → ≤ 5).
- Marcadores TODO detectados: **8 → 1** (`agent-kits/shared/usage-meter.py`), con test del detector; `interop/` excluible del informe con default sin cambio.
- **Un solo mecanismo** de copias compartidas: las 5 unidades reales (A: 3 bloques `--8<--` · B: `REVISION_HDR_PATTERN` · C: `glob_to_regex`, `piezas()` · D: `sin_vallas`) en `copias.json`, guardadas por `tests/test_copias_declaradas.py`, y el linter falla ante un bloque idéntico sin registrar.
- Suite, linter, evals, `export-interop.py --check` y `release.py --dry-run` **idénticos** antes y después del bloque (a) (identidad por test, capturas byte a byte de los `--json` y del HTML del dashboard).
- Bloque (b): matriz de contratos `docs/agents/CONTRACTS.md` con las 11 aristas E1–E11 y su puerta; linter con rutas y `/comandos` citados existentes; `test-plan: n/a (sin UI)` leído por `dev-cycle` y `qa`; `interop/**` en `Archivos` y `--check` en la Lente A; `scope-check` sin ruido del orquestador; `/doctor` con el nombre real `/custom-agents:<cmd>`; Lente C que ve texto del consumidor hacia un prompt; `usage-meter` robusto a marcadores viejos y agregado `fuente: estimado` visible.

---

## Datos necesarios para un informe completo

- [x] **Requisitos funcionales** confirmados por el solicitante — spec `aprobada` (C-01…C-13) + tres ajustes del orquestador de hoy (C-13 (i) hecha, C-03 encogida, E11 nuevo)
- [x] **Alcance** cerrado — `analysis.md` §7 y spec «Fuera»: prosa de piezas en (a), features en (a), `brief-budget`, el 7,6 %, E8, O3, funciones largas fuera de los cinco hotspots, los ~104 ficheros que citan `/dev-cycle`
- [x] **Criterios de éxito / métricas** acordados — CA-01…CA-20 con comando; señales del §8
- [x] **Accesos y credenciales** — repo local; sin servicios externos (`.claude/jira.json` no existe: sin volcado a Jira)
- [x] **Entornos** — Windows 11 (`PATH` con `.venv/Scripts`, consola cp1252 `GOT-005`, `core.autocrlf=true`); CI Linux como árbitro de la suite
- [x] **Stakeholders** — usuario (puerta del plan, decisión sobre C-14); `/dev-cycle` orquesta
- [x] **Dependencias externas** — `design.md` `aprobado` (era la única; cumplida); `brief-budget` y F2 de `project-specialization` esperan (aristas hacia fuera)
- [x] **Restricciones** — contratos congelados (sección «Contratos congelados»); rama `feature/plugin-refactor` = `master` `8fee28a` + commits de hoy; el `implementer` no escribe en `docs/roadmap/` salvo `tasks.md` (hook de guardia `guardrail-check.py`)
- [x] **Tarifa/hora y supuestos de coste** — `.claude/rates.json` (50 €/h · Opus 4.8 verificado 2026-08-18 · FX 0,92 supuesto)

---

## Análisis de impacto

**Bloque (a) — código Python de los cinco hotspots y de `code-health.py`; ninguna pieza de prosa.**

- **`agent-kits/shared/task-brief.py`** (685 líneas, `main()` 160 en `:680`) — `main()` en las siete secciones que ya monta; las cuatro reglas de la persona (`PERSONA_TOPE_CHARS`, `PERSONA_SUELO_CHARS`, `PERSONA_TOPE_MINIMO_UTIL`, margen dinámico) en una función con nombre. Consumidores sin cambio: `/dev-cycle` modo `subagentes`; `agent-kits/shared/test_task_brief.py` no se toca.
- **`agent-kits/shared/knowledge-find.py`** (852 líneas, `main()` 87 en `:932`) — partir `main()` y las otras dos largas. Su `--json` (`acierto_json` `:794`: `id, tipo, estado, estado_detalle, area, titular, ruta, linea, puntuacion, iniciativa, fecha, origen`) lo consumen `task-brief.py` y `hooks/session-context.sh`: **congelado**.
- **`agent-kits/shared/doctor.py`** (942 líneas, `bloque_plugin()` 87 en `:252`) — 8 funciones largas → ≤ 4; veredictos ✅/⚠️/❌, `--json` y exit 1 idénticos; `celdas_md`/`filas_knowledge_index`/`lint_knowledge_index` (`:644-753`, copia guardada) **no se tocan**.
- **`scripts/lint_plugin.py`** (969 líneas, `lint()` 114 en `:397`) — 9 → ≤ 5; es la **puerta de la CI** y de `release.py`: avisos y errores byte-idénticos. Va el **último** de la Fase 2 para que C-07 (T-16) no lo toque dos veces.
- **`skills/roadmap-dashboard/scripts/build_dashboard.py`** (613 líneas, `render_html()` 93 en `:372`, `scan()` 85 en `:228`) — 8 → ≤ 4; HTML/MD/JSON byte-idénticos para el mismo roadmap (captura previa).
- **`skills/code-health/scripts/code-health.py`** — `TODO_RE` (`:49`) y exclusión del propio detector (T-01); `--exclude-path` repetible en `ficheros()` (`:80`) (T-02). Sus 14 tests + los nuevos SOLO para el detector y la exclusión.
- **`agent-kits/shared/usage-meter.py`** (T-04, bloque b) — filtro `timestamp >= inicio` en `_sum_usage_window()` (`:192`), descarte de marcadores anteriores al arreglo, `duracion_reloj` aditivo en `cmd_close()` (`:412`).

**Fase 3 — O1 (impacto por fichero heredado de `design.md` §5, sin cambio de texto en los bloques registrados).**

- **`agent-kits/shared/copias.json`** (nuevo) — 5 unidades compartidas + 2 pares declarados «no-código».
- **`tests/test_copias_declaradas.py`** (nuevo) — un test que recorre el registro; absorbe el criterio de `tests/test_knowledge_index.py:198-214` y `tests/test_console_encoding.py:801-804` sin borrarlos.
- **`scripts/lint_plugin.py`** — comprobación «marcador `--8<--` o `_*_FALLBACK` sin fila en el registro» → error (sobre el `lint()` ya partido en T-08).
- **`agent-kits/shared/scope-check.py:46-77` · `skills/adversarial-review/scripts/review-lens-select.py:99-131`** (`glob_to_regex`) · **`evals/check.py:108` · `scripts/lint_plugin.py:905`** (`piezas()`) — mecanismo C sin guardarraíl → el respaldo local pasa a bloque `--8<--` comparable.
- **`agent-kits/shared/ledger-lint.py:101` · `skills/changelog-sync/scripts/changelog-sync.py:120`** (`sin_vallas`) — de test conductual a identidad: **decisión del plan (pregunta abierta 1 del diseño): dos copias registradas como bloque `--8<--` (mecanismo A)**, no canónico + respaldo (B). Motivo: `changelog-sync.py` viaja solo en el paquete portable y el test de identidad ya lo cubre; B añadiría un `import` por ruta que hoy no tiene.
- **`agent-kits/shared/ledger-lint.py:179` · `agent-kits/shared/task-brief.py:576` · `skills/jira-sync/scripts/jira-flow.py:231`** — mecanismo B (E9): se registran; el texto no cambia.

**Bloque (b) — prosa de piezas + comprobaciones nuevas + doc viva. Todo cambio en `agents/`/`commands/`/`hooks/` regenera `interop/**` (`export-interop.py`) y toca las piezas que describen a la tocada (esto ES E2/E3; ver la sección «Archivos» de cada tarea).**

- **`docs/agents/CONTRACTS.md`** (nuevo, solo ES como el resto de `docs/agents/`) — matriz pieza → pieza; fila en `docs/README.md` + `docs/en/README.md`.
- **`scripts/lint_plugin.py`** + **`tests/test_lint_plugin.py`** — rutas citadas, `/comandos` citados, filas de la matriz con puerta (T-16).
- **`agents/planner.md` · `commands/dev-cycle.md` · `agents/qa.md` · `agent-kits/planner/templates/improvement-plan.md` · `agent-kits/qa/coverage-check.py`** — marcador `test-plan: n/a (sin UI)` (T-13). `qa-gate.py` no cambia de contrato (S-7).
- **`agents/planner.md` · `agent-kits/planner/templates/tasks.md` · `agents/implementer.md` · `skills/adversarial-review/references/lens-prompts.md`** — `interop/**` y piezas que describen en `Archivos`; regeneración; `--check` en la Lente A (T-15).
- **`skills/adversarial-review/scripts/review-lens-select.py`** (+ test) — heurística «texto del consumidor → prompt/brief» (T-18).
- **`agent-kits/shared/doctor.py`** (+ test) · README ES/EN · `docs/INSTALL.md` (+EN) · `docs/README.md` (+EN) · `CLAUDE.md` — nombre real `/custom-agents:<cmd>` (T-12).
- **`agent-kits/shared/scope-check.py`** (+ test) · `docs/CONVENTIONS.md` regla 9 (+EN) — exclusiones por defecto + `dev.json` `alcance.excluir` (T-11).
- **`skills/roadmap-dashboard/scripts/build_dashboard.py` (`render_proceso_md`, `:582`)** · `commands/retro.md` · `agent-kits/shared/usage-meter.py` (`_ratio_calibrado`) · `docs/roadmap/CALIBRATION.md` (formato de fila) · `docs/observability.md` (+EN) — agregado `fuente: estimado` visible (T-17).
- **`tests/test_cifras_medidas.py`** · `skills/changelog-sync/references/medicion-escalera.md` · `docs/knowledge/adr/ADR-012-*.md` · `docs/roadmap/2026-09-04-changelog-brief/tasks.md` · `docs/knowledge/README.md` — E11 (T-19, propuesta).

---

## Cambios arquitectónicos

La arquitectura la fija [`design.md`](design.md) (`aprobado`, O1). Este plan la **referencia**, no la rediseña:

- **O1 — registro + un test + linter** (`ADR-016`): `agent-kits/shared/copias.json` con una entrada por bloque (canónico, N rutas, mecanismo, centinelas o rango); `tests/test_copias_declaradas.py` compara byte a byte tras normalizar `\r\n` → `\n` y **falla** si divergen; `lint_plugin.py` falla ante un bloque `--8<--` o `_*_FALLBACK` no registrado (inseparable de O1). El 7,6 % de duplicado **no baja** y no es objetivo (spec §7): la `Verificación` de las tareas de C-03 va sobre registro + test + linter, **no** sobre `code-health --baseline`.
- **Decisiones de detalle que el diseño dejó al plan** (preguntas abiertas de `design.md` §7): (1) `sin_vallas` → dos copias registradas como bloque `--8<--` (mecanismo A), ver impacto; (2) el registro de copias vive en `agent-kits/shared/` (viaja con el kit) y la matriz de contratos en `docs/agents/` (la lee una persona y el linter): dominios distintos, se enlazan mutuamente en una línea; (3) el hueco de `scripts/export-skills.py:399` (`fragmentos_shared` solo escanea `.md`) **no entra**: con O1 es opcional y ajeno a la decisión → deuda registrada para `quick-implement`; (4) los dos pares no-código (`import` + docstring `Uso:`/`Exit:`) se declaran `"no_codigo": true` en `copias.json` y salen del recuento; el detector de `code-health.py` no aprende nada nuevo (C-04 es solo el TODO).
- **Segunda línea base tras C-05** (S-4): `docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline-2.json` + `.md`, tomada con `--exclude-tests --exclude-path interop`. **La escribe el orquestador** (`/dev-cycle`) al cerrar T-02, no el `implementer`: su hook de guardia (`guardrail-check.py`) solo le permite `tasks.md` dentro de `docs/roadmap/`. Desde T-03 en adelante, la comparación del bloque (a) usa la línea base 2 con los mismos flags.
- **Marcador `test-plan: n/a (sin UI)`** (C-08, S-7): vive en el **frontmatter de `improvement-plan.md`** (donde ya está `design:`), con espejo legible en la tabla de cabecera. Lo emite `planner`, lo lee `dev-cycle` Fase 3 antes de despachar `qa`, y `qa` termina limpio (exit 0, una línea en el informe). `qa-gate.py` no cambia. Decisión registrada en [`ADR-017`](../../knowledge/adr/ADR-017-marcador-test-plan-n-a-en-el-frontmatter-del-plan.md) (`propuesta`).
- **Exclusiones de `scope-check`** (C-12): default en el script (`CONTINUE-HERE*.md`, `.claude/**`, `docs/knowledge/journal/**` —lo escribe el hook, no la tarea—) y override **aditivo** en `dev.json` `alcance.excluir` (misma forma que `revision.excluir`: lista de globs `**`-aware).
- **Flag de `code-health`** (C-05): `--exclude-path <prefijo>` repetible, relativo a la raíz (`--exclude-path interop`); default sin cambio (salida byte-idéntica sin el flag, CA-07).
- **`usage-meter` tras el arreglo de hoy** (C-13 ii-a): `_sum_usage_window` filtra registros con `timestamp < inicio` (tolerancia 60 s), el marcador lleva `version: 2` desde `start` y `close` degrada con aviso un marcador sin `version` (abierto con el código anterior: contaría el histórico entero, medido: 1.552 respuestas / 143 € falsos); `duracion_reloj` (`fin − inicio`) se añade como clave aditiva sin cambiar `duracion`.
- **E11 (C-14, propuesta)**: de las dos vías del orquestador, el plan propone la segunda —**el test vigila solo el documento que quiere ser vivo**: `medicion-escalera.md` y `SKILL.md` de `changelog-sync` siguen con `<!--m:…-->`; los históricos (`ADR-012`, ledger de `changelog-brief`, índice de la memoria) pasan a `<!--m?:histórico medido el 2026-09-0X-->` con la cifra congelada y su fecha—. Es más barata que generar cifras con fecha y no cambia `changelog-sync.py`. El usuario decide en la puerta del plan.

---

## Contratos congelados (restricción del bloque a)

Nada de esto cambia en las Fases 1-3. Cada tarea del bloque (a) lo demuestra con capturas previas (CA-08) guardadas **fuera del repo** en `$CAPTURAS` (`CAPTURAS="${CAPTURAS:-$TEMP/plugin-refactor-capturas}"`; fuera del árbol para que `scope-check` no las cuente hasta que T-11 exista).

| Pieza | Contrato congelado | Cómo se demuestra |
|---|---|---|
| Todos los hotspots | Flags de `argparse` (`grep -n "add_argument"`), exit codes | `grep -n "add_argument\|return [0-9]\|sys.exit" <script>` antes/después → `diff` vacío |
| `knowledge-find.py` | Forma del `--json` (`acierto_json`: 12 claves), `--doctrina`, `--show`, `--related`, `--limit 0` | `python agent-kits/shared/knowledge-find.py --contexto "Refactor del plugin" --iniciativa plugin-refactor --json > "$CAPTURAS/kf-<antes\|despues>.json"` → `diff` vacío |
| `scope-check.py` | `--json`: `slug, base, base_desc, cambiados, en_alcance, fuera_de_alcance, declarados_sin_tocar, patrones`; exit 0/1/2 | `python agent-kits/shared/scope-check.py docs/roadmap/2026-09-09-plugin-refactor --json --base HEAD` → mismas claves |
| `ledger-lint.py` / `task-brief.py` / `jira-flow.py` | `REVISION_HDR_PATTERN` (`ledger-lint.py:179`) y sus dos `_REVISION_HDR_FALLBACK` | `agent-kits/shared/test_task_brief.py` (`:1102`) y `skills/jira-sync/scripts/test_jira_flow.py:361-364` en verde; tras T-09, `tests/test_copias_declaradas.py` |
| `task-brief.py` | Nombres de las 7 secciones del brief, `BRIEF_TOPE_CHARS = 10000`, `--json`, exit codes | brief real capturado sobre `docs/roadmap/2026-09-09-project-specialization` (tiene `design.md`, GOT-009) → `diff` vacío |
| `build_dashboard.py` | HTML / MD / JSON byte-idénticos para el mismo roadmap | `python skills/roadmap-dashboard/scripts/build_dashboard.py docs/roadmap --json > "$CAPTURAS/dash-<antes\|despues>.json"` (y `--md`, HTML) → `diff` vacío |
| `lint_plugin.py` | Texto exacto de avisos y errores; `lint_plugin: 9 agentes · 0 errores · 3 avisos` | salida completa capturada → `diff` vacío |
| `doctor.py` | Líneas ✅/⚠️/❌, `--json`, exit 1 si hay ❌ | `python agent-kits/shared/doctor.py --json > "$CAPTURAS/doctor-<antes\|despues>.json"` → `diff` vacío (salvo la marca de tiempo si la hay) |
| `code-health.py` | Flags existentes, forma del `--json` y de `--baseline`; **excepciones declaradas**: TODO 8 → 1 (T-01) y `--exclude-path` aditivo (T-02) | `code-health.py . --exclude-tests --json` sin flag nuevo → byte-idéntico salvo `marcadores` |
| Suite completa | **Identidad por test**, no por conteo | `python -m pytest -q tests agent-kits/shared skills -p no:cacheprovider -rA 2>/dev/null \| grep -E "^(PASSED\|FAILED\|ERROR\|SKIPPED\|XFAIL\|XPASS) " \| sort > "$CAPTURAS/suite-<antes\|despues>.txt"` → `diff` vacío |

**Puertas de cada tarea** (§6.5): `python scripts/lint_plugin.py` (0 errores) · `python evals/check.py` (0 errores) · `python scripts/export-interop.py --check` (`48 ficheros al día`) · `python -m pytest -q tests/test_knowledge_index.py tests/test_console_encoding.py` (copias guardadas; tras T-09 también `tests/test_copias_declaradas.py`). **Al cierre de cada tramo:** `python scripts/release.py --dry-run` → exit 0.

---

## Archivos a crear/modificar

| Archivo | Acción | Propósito |
|---------|--------|-----------|
| `skills/code-health/scripts/code-health.py` · `skills/code-health/scripts/test_code_health.py` · `skills/code-health/SKILL.md` | Modificar | T-01 detector de TODO · T-02 `--exclude-path` (una línea de uso en la skill: excepción declarada) |
| `docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline-2.{json,md}` | Crear (orquestador) | Segunda línea base tras T-02 |
| `agent-kits/shared/task-brief.py` | Modificar | T-03 `main()` en 7 secciones; reglas de persona en una función |
| `agent-kits/shared/usage-meter.py` · `agent-kits/shared/test_usage_meter.py` · `docs/observability.md` · `docs/en/observability.md` | Modificar | T-04 filtro `timestamp >= inicio`, descarte de marcadores viejos, `duracion_reloj` |
| `agent-kits/shared/knowledge-find.py` · `agent-kits/shared/doctor.py` · `skills/roadmap-dashboard/scripts/build_dashboard.py` · `scripts/lint_plugin.py` | Modificar | T-05…T-08 funciones largas 28 → ≤ 14 |
| `agent-kits/shared/copias.json` · `tests/test_copias_declaradas.py` | Crear | T-09 registro O1 + test de identidad |
| `agent-kits/shared/scope-check.py` · `skills/adversarial-review/scripts/review-lens-select.py` · `evals/check.py` · `scripts/lint_plugin.py` · `agent-kits/shared/ledger-lint.py` · `skills/changelog-sync/scripts/changelog-sync.py` · `agent-kits/shared/task-brief.py` · `skills/jira-sync/scripts/jira-flow.py` | Modificar (comentarios/centinelas) | T-09/T-10 mecanismos C y D → bloques `--8<--` registrados; A y B registrados sin cambiar texto |
| `scripts/lint_plugin.py` · `tests/test_lint_plugin.py` | Modificar | T-10 bloque idéntico no registrado → error · T-16 rutas/`/comandos`/filas con puerta |
| `agent-kits/shared/scope-check.py` · `agent-kits/shared/test_scope_check.py` · `docs/CONVENTIONS.md` · `docs/en/CONVENTIONS.md` | Modificar | T-11 exclusiones + `dev.json` `alcance.excluir` |
| `agent-kits/shared/doctor.py` · `agent-kits/shared/test_doctor.py` · `README.md` · `README.es.md` · `docs/INSTALL.md` · `docs/en/INSTALL.md` · `docs/README.md` · `docs/en/README.md` · `CLAUDE.md` | Modificar | T-12 nombre real `/custom-agents:<cmd>` |
| `agents/planner.md` · `commands/dev-cycle.md` · `agents/qa.md` · `agent-kits/planner/templates/improvement-plan.md` · `agent-kits/qa/coverage-check.py` · `docs/agents/planner.md` · `docs/agents/qa.md` · `docs/FLOWS.md` · `docs/en/FLOWS.md` · `evals/cases/agent-planner.json` · `evals/cases/agent-qa.json` · `evals/cases/command-dev-cycle.json` · `interop/**` | Modificar | T-13 `test-plan: n/a (sin UI)` en las tres piezas + quien las describe |
| `docs/agents/CONTRACTS.md` | Crear | T-14 matriz de contratos pieza → pieza (11 aristas) |
| `docs/README.md` · `docs/en/README.md` · `docs/agents/ROLES.md` | Modificar | T-14 fila y enlace cruzado a la matriz |
| `agents/planner.md` · `agent-kits/planner/templates/tasks.md` · `agents/implementer.md` · `skills/adversarial-review/references/lens-prompts.md` · `docs/agents/planner.md` · `docs/agents/implementer.md` · `agent-kits/planner/README.md` · `interop/**` | Modificar | T-15 `interop/**` + piezas que describen en `Archivos`; regeneración; `--check` en Lente A |
| `skills/roadmap-dashboard/scripts/build_dashboard.py` · `tests/test_dashboard.py` · `agent-kits/shared/usage-meter.py` · `agent-kits/shared/test_usage_meter.py` · `commands/retro.md` · `docs/roadmap/CALIBRATION.md` · `docs/observability.md` · `docs/en/observability.md` · `interop/**` | Modificar | T-17 agregado `fuente: estimado` visible; filas estimadas marcadas en `CALIBRATION.md` y fuera de la mediana |
| `skills/adversarial-review/scripts/review-lens-select.py` · `skills/adversarial-review/scripts/test_review_lens_select.py` · `skills/adversarial-review/references/lens-c-heuristics.md` | Modificar | T-18 Lente C: texto del consumidor → prompt |
| `tests/test_cifras_medidas.py` · `skills/changelog-sync/references/medicion-escalera.md` · `docs/knowledge/adr/ADR-012-resumen-del-changelog-lo-escribe-quien-cierra-la-tarea.md` · `docs/roadmap/2026-09-04-changelog-brief/tasks.md` · `docs/knowledge/README.md` | Modificar | T-19 (propuesta) E11: histórico congelado con fecha, vivo vigilado |
| `docs/roadmap/2026-09-09-plugin-refactor/tasks.md` | Modificar | Ledger canónico: trazas «Revisión de dos lentes — intento N» por tramo (T-20), correcciones (T-21) |
| `CHANGELOG.md` · `CHANGELOG.es.md` · `docs/roadmap/2026-09-09-plugin-refactor/retro.md` · `docs/roadmap/CALIBRATION.md` | Modificar / Crear | T-22 cierre (`changelog-sync`, `/retro`) |

---

## Dependencias y prerequisitos

- **Cumplida** — condición 1 del go: `design.md` `aprobado` con O1 (2026-09-10) → T-09/T-10 desbloqueadas desde el arranque.
- **Hecha fuera del plan** — C-13 (i) en `2026-09-10-usage-meter-transcripts` (`master` `8fee28a`): clave `[^A-Za-z0-9]`, búsqueda recursiva bajo `subagents/`, tests sin inyección, `GOT-010`. Este plan solo paga C-13 (ii): T-04 + T-17.
- **Hecha fuera del plan** — P-1 (`architect`): `design.md` + `ADR-016`, medido 0,71 h IA / 9,16 €.
- **Aristas internas** (campo `Dependencias` del ledger): T-01 → T-02 → T-03 → T-04 → T-05 → T-06 → T-07 → T-08 → T-09 → T-10 → Fase 4. Dentro de la Fase 4: T-14 (matriz) antes de T-15 y T-16 (S-6: sin matriz, C-07 (c) y la lista de dependientes de C-09 no existen — **motivo escrito** para adelantar C-06 sobre el orden sugerido por el orquestador); T-17 después de T-07 (mismo `build_dashboard.py`) y de T-04 (mismo `usage-meter.py`); T-12 después de T-06 (mismo `doctor.py`); T-16 después de T-08 y T-10 (mismo `lint_plugin.py`).
- **Aristas hacia fuera** (condición 3 del go): **T-03 antes de `brief-budget`** (mismo `main()` de `task-brief.py`); **Fase 2 completa antes de F2 de `project-specialization`** (toca `doctor.py` y `lint_plugin.py --root`).
- **Puertas de proceso** (condición 2): T-20 (4 tramos), T-21 y T-22 no se recortan.
- **Rama**: `feature/plugin-refactor` (= `master` `8fee28a` + los commits de hoy). Un commit por tarea con prefijo `T-XX:`.
- **Entorno**: `export PATH="$PWD/.venv/Scripts:$PATH"` antes de cualquier puerta (Windows); `$CAPTURAS` fuera del repo.

---

## Criterios de aceptación (global)

- [ ] CA-01 — Tras T-03…T-08: `code-health.py . --exclude-tests --json --top 1000` → funciones > 30 líneas en los cinco hotspots **≤ 16** y ninguna nueva > 60.
- [ ] CA-02 — Cada tarea del bloque (a) cerró con `--baseline` (línea base 1 hasta T-02; línea base 2 desde T-03) → `funciones largas` «↓ mejora» o «= igual», ninguna métrica «↑ empeora» salvo `edad máx. TODO` (reloj).
- [ ] CA-03 / CA-04 — Suite idéntica **por test** antes y después de cada tarea de (a); ningún test existente modificado ni borrado; tests nuevos solo en `test_code_health.py` (T-01, T-02) y `tests/test_copias_declaradas.py` (T-09).
- [ ] CA-05 — `copias.json` con las 5 unidades + 2 no-código; `tests/test_copias_declaradas.py` en verde y **rojo con mutante** (un byte cambiado en una copia); `grep -rn "sin_vallas\|_REVISION_HDR_FALLBACK"` solo devuelve rutas registradas.
- [ ] CA-06 / CA-07 — `todos` = 1; `--exclude-path interop` quita el par de 118 líneas; sin flag, salida byte-idéntica.
- [ ] CA-08 / CA-09 — Capturas de `--json`/HTML/brief/linter/doctor sin `diff`; `git diff --stat <base>..HEAD -- agents commands 'skills/*/SKILL.md'` vacío para los commits T-01…T-10 (excepción declarada: una línea en `skills/code-health/SKILL.md` documenta el flag de T-02).
- [ ] CA-10…CA-13 — `docs/agents/CONTRACTS.md` con 11 aristas (E1–E11) y columna **Puerta** no vacía; linter avisa por ruta/`/comando` inexistente y por fila sin puerta; con el árbol actual 0 avisos nuevos.
- [ ] CA-14 — `test-plan: n/a (sin UI)` en este plan: `dev-cycle` Fase 3 lo lee y `qa` termina limpio (exit 0, informe con la línea) — se comprueba **sobre esta misma iniciativa** al llegar a la Fase 3 tras T-13.
- [ ] CA-15 — Plantilla de tareas y `planner.md` exigen `interop/**` + piezas que describen; `implementer.md` regenera; Lente A ejecuta `export-interop.py --check` y lo cita ✓/✗.
- [ ] CA-16 — `review-lens-select.py` → `lente_c: true` con motivo para el caso real de `project-specialization` F1 (fixture del diff); tasa de disparo sobre los últimos 5 ledgers medida antes/después y anotada.
- [ ] CA-17 — `/doctor` informa `/custom-agents:<cmd>` cuando el plugin está instalado desde el marketplace y ⚠️ si la doc viva cita la forma corta; README/INSTALL/docs/README ES+EN y `CLAUDE.md` citan la forma que funciona.
- [ ] CA-18 — `scope-check.py` no reporta `CONTINUE-HERE.md` ni `.claude/usage-state.json`; `dev.json` `alcance.excluir` amplía; test con mutante.
- [ ] CA-19 (ii) — `usage-meter close` ignora registros con `timestamp < inicio` (test con fixture de transcript previo); marcadores sin `version` se degradan con aviso; `/roadmap-metrics` y `/retro` muestran «N de M bloques `generacion:` con `fuente: estimado`» y las filas estimadas de `CALIBRATION.md` van marcadas y fuera de la mediana.
- [ ] CA-20 — Todo cambio de prosa de (b): `export-interop.py --check` verde, `evals/check.py` 0 errores, espejo EN actualizado.
- [ ] Puertas de cierre — `python scripts/release.py --dry-run` exit 0 · `changelog-sync` con un bullet por tarea · `retro.md` + fila en `CALIBRATION.md` (`retro-gate.py` exit 0).

---

## Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| «Misma suite en verde» se lee como «todo verde» en Windows (~39 fallos de entorno preexistentes) | Alta | Medio (una regresión se confunde con un fallo conocido) | Identidad **por test** con `-rA` + `sort` + `diff` (sección «Contratos congelados»); CI Linux como árbitro; captura `suite-antes.txt` al abrir cada tramo |
| Contrato roto sin que la suite lo vea (`--json` de `knowledge-find`/`scope-check`, HTML del dashboard, brief con `## Diseño` — GOT-009) | Media | Alto | Capturas byte a byte en `$CAPTURAS` sobre datos reales del repo ANTES de T-03; la Lente B las recibe como evidencia |
| El `implementer` no puede escribir la segunda línea base (hook de guardia: solo `tasks.md` en `docs/roadmap/`) | Alta si no se prevé | Medio (T-03 compara contra la línea base equivocada → «mejora» ficticia de 118 líneas, S-4) | T-02 lo declara: la escribe el orquestador al cerrar la tarea; la `Verificación` de T-03…T-08 nombra `code-health-baseline-2.json` |
| La revisión encuentra más de lo presupuestado (`memory-retrieval`: +66 % IA, 38 gaps); la Fase 4 es un tramo de 9 tareas | Alta | Medio (coste) | T-20/T-21 como líneas propias (16 % del base); bucle acotado a 3 por tramo; si R4 supera 10 gaps Important en el intento 1, partir en R4a (T-11…T-15) / R4b (T-16…T-19) **dentro del presupuesto de T-20** y decirlo en la retro |
| `lint_plugin.py` refactorizado (T-08) o con comprobaciones nuevas (T-10, T-16) bloquea una release por falso positivo | Media | Alto | T-16 nace como **aviso** y sube a error tras una release limpia; T-10 (bloque no registrado) nace como error porque su universo es cerrado (marcadores `--8<--` y `_*_FALLBACK` del propio repo); `release.py --dry-run` al cierre de cada tramo |
| Conflicto de rama con F2 de `project-specialization` (mismo `doctor.py`, `lint_plugin.py`) o presión de `brief-budget` (mismo `task-brief.py`) | Media | Alto | Condición 3 del go como aristas hacia fuera; T-03 la primera tarea grande; Fase 2 completa antes de F2 |
| Sobredisparo de la Lente C tras T-18 encarece cada ciclo | Media | Medio | Medir tasa sobre los últimos 5 ledgers antes/después (criterio de T-18); válvula `dev.json` `revision.excluir`; recortar a «detector del caso F1 + válvula» si sube |
| El filtro `timestamp >= inicio` (T-04) descarta respuestas legítimas por reloj desfasado entre máquina y transcript | Baja | Medio (subconteo, publicado como medido) | Tolerancia de 60 s; test con fixture; aviso cuando el filtro descarta > 0 registros con offset > 0 |
| E11 (T-19) se descarta en la puerta y `test_cifras_medidas` sigue rompiéndose al abrir/cerrar iniciativas | Media | Bajo (coste recurrente de parcheo, ya medido: 29 fallos, un parche corrompió tres líneas) | El plan lo presenta con coste (2,0 h); si se descarta, queda en `docs/agents/CONTRACTS.md` como arista E11 sin puerta y en la retro |
| Prosa de (b) desincroniza a quien la describe (el propio E3) | Alta | Medio | Cada tarea de prosa lista en `Archivos` las piezas que describen a la tocada + `interop/**`; Lente A revisa con la matriz de T-14 desde que existe |
| Precio de tokens y FX | Baja | Bajo (tokens ≈ 1 % del coste) | `rates-verify` si pasan 90 días; `tipoCambioUsdEur` ⚠️ verificar antes de facturar |

---

## Métricas de éxito

- `code-health.py . --exclude-tests --json --top 1000` → funciones > 30 líneas en los cinco hotspots **≤ 16** (hoy 32), ninguna > 60; `todos` = 1 (hoy 8).
- `python -m pytest -q tests/test_copias_declaradas.py` en verde; mutante de un byte en cualquier copia → rojo; `lint_plugin.py` error ante un `--8<--` sin registrar (mutante).
- Cero `diff` en las capturas de contratos (`kf`, `scope-check`, `dash`, `brief`, `lint`, `doctor`, `suite`) al cerrar cada tarea del bloque (a).
- `docs/agents/CONTRACTS.md` con 11 filas y columna Puerta no vacía; `lint_plugin.py` con 0 avisos nuevos sobre el árbol actual y avisos con mutante (ruta/`/comando` inexistente, fila sin puerta).
- La Fase 3 de `/dev-cycle` de **esta iniciativa** pasa por `qa` sin pedir `test-plan.md` (CA-14 en vivo).
- `review-lens-select.py` → `lente_c: true` para el fixture del caso F1; tasa de disparo sobre los últimos 5 ledgers sin subir más de un ledger.
- `/roadmap-metrics` muestra «N de M bloques `generacion:` estimados»; la retro de esta iniciativa es la **primera fila de `CALIBRATION.md` medida en Windows** (`fuente: medido` en las 22 tareas).
- Desviación real vs. estimado en la retro ≤ +30 % en horas IA (la única muestra comparable dio +66 %; T-20/T-21 existen para absorberlo).

---

## Changelog del plan

| Fecha | Cambio | Autor |
|-------|--------|-------|
| 2026-09-10 | Creación del plan (Fase 2-b de `/dev-cycle`, flujo completo; relanzamiento tras un intento que murió por límite de sesión): 22 tareas en 5 fases y 4 tramos de revisión, horas y costes heredados por característica de `evaluation.md` (74,0 h base / 88,8 h con margen / ~4.479 €) con tres diferencias declaradas — P-1 y C-13 (i) ya hechas (−3,0 h), E11 como propuesta C-14 (+2,0 h). C-03 encogida según `design.md` (O1: registro + test + linter; `Verificación` sobre registro/test, no sobre `code-health`). Las cuatro condiciones del go convertidas en aristas del grafo; segunda línea base asignada al orquestador (hook de guardia del implementer); marcador `test-plan: n/a (sin UI)` estrenado en este frontmatter (`ADR-017` `propuesta`). C-06 adelantada sobre C-09/C-07 por dependencia (S-6). Sin Jira (`.claude/jira.json` no existe) | planner |
| 2026-09-10 | Tercer intento (los dos anteriores murieron por errores de API tras dejar los borradores): borradores verificados contra `spec.md`, `evaluation.md` y `design.md` §5/§7 (O1, C-03 encogida, C-13 (ii) en T-04/T-17, E11 en T-19, contratos congelados, `interop/**` en `Archivos`) sin cambios de fondo; `Changelog` de T-04 recortado a ≤ 200 caracteres; puertas ejecutadas: `ledger-lint` exit 0, `lint_plugin` 0 errores, `test_cifras_medidas` 252 verdes (cifras vivas ya re-medidas), `test_roadmap_index` + `test_knowledge_index` verdes. Bloque `generacion:` sustituido por la medición de este intento (los marcadores anteriores se descartaron; el segundo midió 1,20 h IA / 7,76 €, no acumulado) | planner |

---

## Siguiente paso

Con el **OK del plan** del usuario (puerta de control) —incluida la decisión sobre **C-14 (E11)**—, el agente **`implementer`** ejecuta la Fase 1 sobre `feature/plugin-refactor`, marcando `tasks.md` como **ledger canónico** (checkbox + estado por tarea, medición por tarea con `usage-meter.py`). Al cerrar cada tramo (R1…R4), `/dev-cycle` lanza la **revisión de dos lentes** (skill `adversarial-review`; la Lente B es la que trabaja en las Fases 1-3, la A en la Fase 4) y anota «Revisión de dos lentes — intento N» en el ledger. **Sin `test-plan.md`** (`test-plan: n/a (sin UI)`): `qa` corre `ledger-lint` y sale limpio. Cierre con `changelog-sync`, `release.py --dry-run`, `/retro` + `retro-gate.py` y `documenter` si el usuario lo pide. Después arrancan `brief-budget` (sobre el `task-brief.py` partido) y F2 de `project-specialization`.
