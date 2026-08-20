---
generacion:
  inicio: 2026-08-20T10:32:18Z
  fin: 2026-08-20T10:37:05Z
  fuente: estimado        # degradación declarada: usage-meter.py sin carpeta de transcripciones en este sandbox
  tokens_reales: no-medido (sandbox)
  eur: null
  horas_ia: null
  duracion: no-medido (sandbox)
  ratio_usado: 479326     # mediana de CALIBRATION.md (referencia; no se aplicó por falta de medición)
---

# 2026-08-20-knowledge-capture

> Memoria técnica de los agentes: ADR ligero, gotchas en el punto de nacimiento, bucle de lectura (`knowledge-check.md`), `/retro` con dos salidas y backfill semilla — para que el conocimiento se capture donde nace y los agentes lo lean después.

| | |
|---|---|
| **Fecha** | 2026-08-20 |
| **Estado** | completado |
| **Tipo** | Infra |
| **Prioridad** | Alta |
| **Solicitante** | Jordi (jmano@mediapro.tv) vía `/pm-cycle` |
| **Responsable** | implementer (vía `/dev-cycle`) |
| **Spec** | [`spec.md`](spec.md) |
| **Evaluación** | [`evaluation.md`](evaluation.md) |

---

## Inspección previa (obligatoria, hecha por el planner — no delegada al implementer)

La evaluación rebajó su confianza en C-01, C-02 y C-04 porque **cuatro piezas no estaban en la copia del repo** con la que se evaluó: `agents/nemesis.md`, `agents/planner.md`, `skills/debug-root-cause/SKILL.md` y `agent-kits/planner/templates/tasks.md`. Ahora SÍ están disponibles; las he inspeccionado antes de descomponer las tareas:

| Pieza | Qué confirma la inspección | ¿Cambia horas? |
|---|---|---|
| `agents/nemesis.md` (L60-78, "Protocolo de sesión (bookends)") | El patrón a generalizar es exactamente el descrito en la spec: apertura lee `STATE.md`+`MEMORY.md`, cierre actualiza + `Estado: [actualizado\|sin cambios]`. Sirve de molde literal para `knowledge-check.md`/`knowledge-write.md`. | **No** — confirma el supuesto de diseño, sin sorpresas |
| `agents/planner.md` (este mismo fichero) | Ya declara `agent-kits/shared` en `dependencies.kits` (línea 15) y ya tiene el molde idéntico de `constitution-check.md` en su §3 (línea 92) — el punto de inserción para `knowledge-check.md` es mecánico (una línea más, mismo molde). La puerta de decisión donde escribiría un ADR es P3 (Descomposición) / P4 (Estimación). | **No** — C-01 se mantiene en 4h; si acaso, más fácil de lo previsto |
| `skills/debug-root-cause/SKILL.md` (Fase 4, L37-42) | El cierre de F4 ya produce exactamente el material de un gotcha (síntoma implícito en la Fase 1, causa raíz probada en la Fase 3, fix + test de regresión en la Fase 4): solo falta el paso que lo **escribe**. No hay reestructuración de las 4 fases, solo un párrafo añadido al final de Fase 4. | **No** — pero sube la confianza de C-02 de Baja a Media (era el punto de mayor incertidumbre) |
| `agent-kits/planner/templates/tasks.md` (L157-159) | La sección "## Notas de implementación" a retirar (D2) es exactamente esas 3 líneas al final del fichero, sin nada más enganchado a ella (ni referencias cruzadas desde otras plantillas). Retirarla es una operación de una línea de `Edit`. | **No** — confirma que D2 es tan barato como decía la spec |

**Conclusión de la inspección:** ninguna de las cuatro piezas exige re-estimar. Se mantienen las horas/coste heredados de `evaluation.md` sin cambios; la única actualización es de **confianza** (C-02 sube de Baja a Media). Registrado también en el Changelog del plan.

**Verificado además (coordinación con `2026-08-20-confluence-policy`, ya implementada e integrada en `master`):** `skills/confluence-publish/assets/confluence.example.json` no excluye `docs/knowledge/**` en su `exclude` actual (solo `docs/en/**`, `docs/examples/**`, `docs/agents/**`, notas del conector, planes/`tasks.md`/`test-plan.md`, `**/testing/**` y el marcador de staging). Como la política es **opt-out** sobre `include: ["**/*.md"]`, `docs/knowledge/**` **ya entra en la selección curada sin tocar la config** — lo que falta es dejarlo **explícito** (documental) y con un caso de prueba que lo confirme, no una exclusión que quitar. Ver Fase 5 / T-16.

---

## Cuadro de mando

> Heredado íntegro de `evaluation.md` (GO, sin decisiones abiertas; C-06 diferido y NO planificado aquí). El planner reparte estas cifras en fases/tareas; no re-estima desde cero.

| Métrica | Estimado | Real | Confianza |
|--------|---------|------|-----------|
| Tiempo humano | **24 h** (20 h base +20 %) | 0 h | Baja |
| Tiempo IA (ejecución) | **0,95 h** (+ 0,24 h supervisión) | 0 h | Media |
| Coste total | **≈ 1.205 €** | 0 € | Baja |
| Tokens IA | **456k** con margen — 380k base (in 328k / out 52k) | 0 | Media |
| Multiplicador productividad | **×20** | — | — |
| Tareas | **16** | 0 hechas | — |

> **Por qué la confianza del coste es Baja:** el 99,6 % del importe son horas humanas y, según `CALIBRATION.md`, nunca se han validado en este proyecto (0 h reales en las 5 iniciativas medidas). Heredado literal de `evaluation.md`.

---

## Estimación por fase

Cifras **base** (sin margen); tokens/coste por fase = suma de tareas = desglose por característica de `evaluation.md`. Orden heredado de la puerta go: **C-01+C-02 → C-04 → C-07 → C-03 → C-05**. **C-06 (índice generado + `knowledge-lint.py`) queda DIFERIDO y fuera de este plan** — ver nota al final de esta sección.

| Fase | Característica(s) | Estimado (h) | Tokens (in / out) | Coste € |
|------|-------------------|-------------|-------------------|---------|
| Fase 1 — ADR ligero + gotchas en el punto de nacimiento | C-01 + C-02 | 8,5 | 82k / 13k | ≈ 425 € |
| Fase 2 — `/retro` con dos salidas | C-04 | 1,5 | 17k / 3k | ≈ 75 € |
| Fase 3 — Backfill semilla de la memoria | C-07 | 2,0 | 30k / 5k | ≈ 100 € |
| Fase 4 — Bucle de lectura + migración de lecciones ⭐ | C-03 | 5,0 | 52k / 8k | ≈ 250 € |
| Fase 5 — Documentar la práctica (ES + EN) | C-05 | 3,0 | 39k / 6k | ≈ 150 € |
| **Total (base)** | | **20,0 h** | **220k / 35k (255k)** | **≈ 1.000 €** |
| **Total (con margen +20 %)** | | **24,0 h** | **≈ 264k / 42k (306k)** | **≈ 1.200 €** |

> El total **con margen** de esta tabla (≈1.200 €) es solo el trabajo por característica escalado +20 %. El total del cuadro de mando (**≈1.205 €**) añade, como líneas transversales (no atribuibles a una tarea): tokens de **revisión adversarial** (70k — la línea más alta evaluada hasta hoy, porque se tocan 8-10 prompts de agentes) y del **coste de proceso** spec+evaluación+plan (55k), más **lectura de caché** (~3,5M tok). Ver "Presupuesto económico" — heredado literal, sin re-estimar.

> **Nota — C-06 diferido, no planificado.** Índice generado + `agent-kits/shared/knowledge-lint.py` con tests: presupuesto conservado **5 h / ≈ 250 € / 70k tokens** para retomarlo sin re-estimar. **Disparadores objetivos** (cualquiera de los dos): **>15 entradas** en `docs/knowledge/`, o la **primera colisión de IDs de ADR** en un lote paralelo (máx. 3 tareas). Hasta entonces, el índice `docs/knowledge/README.md` se mantiene **a mano** (CA-12): quien añade una entrada actualiza el índice en el mismo cambio. No se incluye ninguna tarea de este plan para C-06.

---

## Presupuesto económico

**Coste = (horas × tarifa) + coste de tokens de IA.** Todos los importes en **EUR**. Heredado de `evaluation.md` §Presupuesto total y §Supuestos económicos — sin diferencias.

### Supuestos (ajustables)

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | 50 €/h | `.claude/rates.json:tarifaHora` |
| Modelo IA asumido | claude-opus-4-8 | `rates.json:modeloIA` |
| Precio input | 5,00 USD / 1M → **4,60 € / 1M** | Verificado 2026-08-18 con `rates-verify` (< 90 días: fiable) |
| Precio output | 25,00 USD / 1M → **23,00 € / 1M** | Ídem |
| Precio escritura de caché | 6,25 USD / 1M | Ídem; entra en tokens facturables |
| Precio lectura de caché | 0,50 USD / 1M | No cuenta para horas, **sí** para € (aprendizaje nº 4 de `CALIBRATION.md`) |
| Tipo de cambio | 1 USD = 0,92 € | ⚠️ **verificar** — supuesto fijo en `rates.json`, no dato verificado |
| Ratio tokens→hora-IA | **479.326 tok/h** | Mediana medida de `CALIBRATION.md` (5 muestras) |
| Ratio de supervisión | 25 % de las horas IA | `rates.json:ratioSupervision` |
| Margen de contingencia | 20 % | `rates.json:margenContingencia`; sobre horas base (humanas e IA) y sobre tokens |
| Lectura de caché prevista | ~3,5M tokens | ⚠️ supuesto por analogía con el histórico (baja tras diferir C-06: sin script ni tests que iterar) |

### Desglose

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 20 h × 50 €/h | 1.000,00 € |
| Margen de contingencia | +20 % sobre desarrollo base | 200,00 € |
| Tokens IA — características | 255k (220k in / 35k out) | 1,89 € |
| Tokens IA — revisión adversarial (2 lentes) | 70k (60k in / 10k out) | 0,53 € |
| Tokens IA — coste de proceso (spec + evaluación + plan) | 55k (48k in / 7k out) | 0,40 € |
| Tokens IA — lectura de caché | ~3,5M × 0,50 USD/M ⚠️ supuesto | 1,61 € |
| Margen sobre tokens | +20 % | 0,89 € |
| **Total estimado (con margen)** | 24 h × 50 €/h + 5,32 € | **≈ 1.205 €** |
| *No comprometido — C-06 diferido* | *5 h × 50 €/h + 0,53 €* | *(≈ 250 €)* — no forma parte de este plan |

<!-- Nota de método: las horas de "Estimación por fase" y de las tareas de tasks.md son SOLO el trabajo por característica (1.000€ base); revisión adversarial y coste de proceso son transversales, igual que en evaluation.md. -->

---

## Previsión de tokens (por fase)

Solo trabajo por característica (sin revisión adversarial ni coste de proceso, transversales — ver arriba). Base: claude-opus-4-8 · precios de la tabla de supuestos.

| Fase | Input (tok) | Output (tok) | Total (tok) | Coste € |
|------|------------|-------------|-------------|---------|
| Fase 1 — ADR + gotchas | 82k | 13k | 95k | 0,68 € |
| Fase 2 — `/retro` dos salidas | 17k | 3k | 20k | 0,15 € |
| Fase 3 — Backfill semilla | 30k | 5k | 35k | 0,25 € |
| Fase 4 — Bucle de lectura ⭐ | 52k | 8k | 60k | 0,42 € |
| Fase 5 — Documentación ES+EN | 39k | 6k | 45k | 0,32 € |
| **Total** | **220k** | **35k** | **255k** | **1,82 €** |

> Pequeña diferencia (1,82 € vs 1,89 € de `evaluation.md`) por redondeo de céntimos al repartir tokens por tarea; no afecta al total del plan, que usa el valor heredado de la evaluación.

**Método de estimación:** nº de ficheros a leer/tocar por tarea (rutas verificadas en la inspección previa) × tamaño medio, calibrado a la baja con `CALIBRATION.md` (aprendizaje nº 5: prosa = minutos). Fase 4 (bucle de lectura) es la más cara en tokens por tocar **cinco** agentes con el mismo párrafo repetido cinco veces + la migración del bloque de lecciones.

---

## Productividad IA (humano vs. IA)

Heredado literal de `evaluation.md` §Productividad IA.

| KPI | Valor |
|-----|-------|
| Horas humanas estimadas | 24 h *(20 h base)* |
| Horas IA (ejecución) | 0,95 h *(0,79 h base)* |
| Supervisión humana | 0,24 h *(25 % de las horas IA)* |
| **Horas totales (IA + supervisión)** | **1,19 h** |
| Horas ahorradas | 22,81 h |
| **Ahorro** | **95,0 %** |
| **Multiplicador de productividad** | **×20** |
| FTE equivalentes *(opcional)* | 0,14 |

> Horas con el margen de contingencia (+20 %) ya aplicado sobre las horas base. Las horas IA salen de `456.000 tokens facturables ÷ 479.326 tok/h`, no de un juicio; las horas humanas sí son un juicio no validado en este proyecto (0 h reales en el histórico).

---

## Resumen ejecutivo

El plugin **produce** conocimiento técnico bueno y lo **pierde**: nadie escribe ADRs, la bitácora de `tasks.md` está muerta (4/12 la conservan), los aprendizajes de `/retro` quedan en silo (solo los números llegan a `CALIBRATION.md`), `debug-root-cause` no persiste su causa raíz y el flaky justificado de `qa` se evapora en `raw/`. La prueba más elocuente: las tres lecciones de la primera calibración están **hardcodeadas en el prompt del evaluator**. Este plan ejecuta las 6 decisiones cerradas en `evaluation.md` (GO): fija `docs/knowledge/` único con su plantilla de ADR y el registro de gotchas en sus 4 puntos de nacimiento (Fase 1), estrena la segunda salida de `/retro` (Fase 2), puebla la memoria con el backfill semilla — 5 `retro.md` + las 5 decisiones D1-D5 de `confluence-policy` (Fase 3) —, construye el bucle de lectura y migra las tres lecciones hardcodeadas fuera del prompt del evaluator (Fase 4, el eje de valor) y documenta la práctica en ES+EN (Fase 5). Se integra sobre `confluence-policy` ya implementada: `docs/knowledge/**` entra en su selección curada sin tocar el `exclude`. C-06 (índice generado + lint) queda diferido, con disparadores objetivos para retomarlo.

### Objetivos

- Que `docs/knowledge/` exista con `README.md`, `adr/`, `gotchas.md` y `LESSONS.md`, poblado con el backfill semilla desde el primer día (no una memoria vacía).
- Que los cinco agentes lectores (`evaluator`, `planner`, `implementer`, `qa`, `documenter`) apliquen `knowledge-check.md` en su flujo, con progressive disclosure (índice antes que cuerpo).
- Que las tres lecciones hardcodeadas del `evaluator` salgan del prompt y se sigan aplicando leídas de `LESSONS.md` (CA-07, criterio de éxito real de la iniciativa).
- Que `/retro` separe números (→`CALIBRATION.md`, sin regresión) de aprendizajes técnicos (→`docs/knowledge/`).
- Que el umbral de registro (0-2 entradas por iniciativa) quede operativo con ejemplos de qué NO merece entrada, para no repetir el anti-patrón de la bitácora muerta.

---

## Datos necesarios para un informe completo

- [x] **Requisitos funcionales** confirmados — umbral aprobado tal cual y D1-D5 cerradas en `spec.md` (`aprobada`)
- [x] **Alcance** cerrado (qué entra y qué NO) — spec §Alcance; evaluación C-01..C-05 + C-07 comprometidas, C-06 diferido
- [x] **Criterios de éxito / métricas** acordados — CA-01 a CA-12 (spec §Criterios de aceptación), CA-07 como criterio de éxito real
- [x] **Accesos y credenciales** — ninguno: todo el trabajo es prosa + ficheros locales, sin red ni conector
- [x] **Entornos** disponibles y datos de prueba — los 5 `retro.md` existentes y la `spec.md` de `confluence-policy` (fuente del backfill), disponibles en el repo
- [x] **Stakeholders** identificados — Jordi (jmano@mediapro.tv), puerta cruzada el 2026-08-20
- [x] **Dependencias externas/internas** — **resueltas por la inspección previa** de este plan (ver sección arriba): las 4 piezas que preocupaban a la evaluación ya están inspeccionadas y no cambian horas
- [x] **Restricciones** conocidas — degradación sin bloqueo (D3, siempre activa sin opt-in), bilingüe EN/ES, tokens máquina en español, umbral anti-burocracia, linter en verde
- [x] **Tarifa/hora y supuestos de coste** confirmados — `.claude/rates.json`, verificado 2026-08-18

---

## Análisis de impacto

- **`agent-kits/shared/`** — `templates/adr.md` (nuevo), `knowledge-check.md` (nuevo, bucle de lectura), `knowledge-write.md` (nuevo, umbral + plantilla de gotcha + dónde escribir).
- **`docs/knowledge/`** — nueva raíz del proyecto: `README.md` (índice a mano), `adr/` (uno por decisión), `gotchas.md` (fichero único), `LESSONS.md` (por agente). Se estrena poblada por el backfill (Fase 3).
- **`agents/planner.md`, `agents/implementer.md`** — escriben ADR en la puerta de decisión cuando cruza el umbral; leen `knowledge-check.md`.
- **`agents/evaluator.md`** — pierde el bloque hardcodeado de las tres lecciones (bloque tras P2-bis); lee `LESSONS.md`.
- **`agents/qa.md`** — el flaky justificado que es patrón (no accidente) escribe gotcha; lee `knowledge-check.md`.
- **`agents/documenter.md`** — indexa `docs/knowledge/` en su taxonomía en vez de derivar decisiones del código (L74/L96); lee `knowledge-check.md`.
- **`skills/debug-root-cause/SKILL.md`** — el cierre de Fase 4 escribe el gotcha con causa raíz probada + enlace al test de regresión.
- **`commands/retro.md`** — dos salidas: números (como hoy) + aprendizajes técnicos.
- **`agent-kits/planner/templates/tasks.md`** — se retira "## Notas de implementación" (D2).
- **`docs/CONVENTIONS.md`, `docs/FLOWS.md`** (+ espejos `docs/en/`) — documentan dónde vive, el umbral, quién lee y quién escribe.
- **`skills/confluence-publish/SKILL.md`, `tests/test_confluence_scope.py`** — coordinación: `docs/knowledge/**` explícito como "sí se publica" + fixture/test que lo confirme.

---

## Cambios arquitectónicos

- **Generalizar el patrón de `nemesis`** (bookends: apertura lee, cierre actualiza, `Estado: [actualizado|sin cambios]`) como fragmento compartido en vez de reinventar un mecanismo de memoria nuevo.
- **Progressive disclosure**: el bucle de lectura abre primero el índice (una línea por entrada) y solo abre la entrada completa si su etiqueta de área toca la tarea — protege la inversión de `2026-08-10-token-diet`.
- **Umbral como defensa contra la burocracia**: ADR solo si cierra alternativa y (2+ piezas o puerta); gotcha solo si costó ≥1 ciclo de depuración o casi rompió una garantía. Se retira la sección "Notas de implementación" (D2) como señal de que el registro es por umbral, no por trámite.
- **Backfill por el mismo mecanismo que se está construyendo** (segunda salida de `/retro`, C-04), no a mano: el mecanismo se estrena con datos reales en vez de simularse.
- **Sin opt-in (D3)**: la memoria es parte del funcionamiento normal, con degradación silenciosa si `docs/knowledge/` no existe (se crea al primer registro).

---

## Archivos a crear/modificar

| Archivo | Acción | Propósito |
|---------|--------|-----------|
| `agent-kits/shared/templates/adr.md` | Crear | Plantilla corta: contexto · decisión · alternativas descartadas · consecuencias · estado |
| `agent-kits/shared/knowledge-write.md` | Crear | Umbral (ADR + gotcha) + plantilla + dónde escribir, molde de `constitution-check.md` |
| `agent-kits/shared/knowledge-check.md` | Crear | Paso "lee la memoria relevante", progressive disclosure, molde de `constitution-check.md` |
| `docs/knowledge/README.md` | Crear | Índice a mano (una línea por entrada, etiqueta de área + estado) |
| `docs/knowledge/adr/` | Crear | ADR por decisión (backfill: 5 de `confluence-policy`) |
| `docs/knowledge/gotchas.md` | Crear | Fichero único de gotchas (backfill: los que salgan de los 5 `retro.md`) |
| `docs/knowledge/LESSONS.md` | Crear | Lecciones por agente (backfill + migración de las 3 del evaluator) |
| `agents/planner.md` | Modificar | Lee `knowledge-check.md`; escribe ADR en la puerta de decisión |
| `agents/implementer.md` | Modificar | Ídem |
| `agents/evaluator.md` | Modificar | Lee `knowledge-check.md`; **retira** el bloque de las 3 lecciones (lee `LESSONS.md`) |
| `agents/qa.md` | Modificar | Lee `knowledge-check.md`; flaky-patrón escribe gotcha |
| `agents/documenter.md` | Modificar | Lee `knowledge-check.md`; indexa `docs/knowledge/` en vez de derivar del código |
| `skills/debug-root-cause/SKILL.md` | Modificar | Cierre de Fase 4 escribe el gotcha |
| `commands/retro.md` | Modificar | Dos salidas (números + técnicos) |
| `agent-kits/planner/templates/tasks.md` | Modificar | Retira "## Notas de implementación" (D2) |
| `docs/CONVENTIONS.md` / `docs/en/CONVENTIONS.md` | Modificar | Nueva regla: dónde vive, umbral, quién lee/escribe |
| `docs/FLOWS.md` / `docs/en/FLOWS.md` | Modificar | Extiende la matriz de `confluence-policy` con los puntos de escritura de conocimiento |
| `skills/confluence-publish/SKILL.md` | Modificar (menor) | Explicita que `docs/knowledge/**` se publica (ya entra por defecto) |
| `tests/test_confluence_scope.py` (+ fixture) | Modificar | Caso que confirma `docs/knowledge/**` en alcance |

---

## Dependencias y prerequisitos

- Orden obligatorio heredado: **Fase 1 (C-01+C-02) → Fase 2 (C-04) → Fase 3 (C-07) → Fase 4 (C-03) → Fase 5 (C-05)**. C-03 no puede probarse de verdad (CA-07) sin memoria real: por eso el backfill (Fase 3) va **antes**. C-05 documenta al final para no rehacer el espejo EN dos veces.
- **Prerequisito ya resuelto**: la inspección de las 4 piezas (ver arriba) — no bloquea el arranque de la Fase 1.
- **Coordinación con `2026-08-20-confluence-policy`** (ya implementada en `master`): no requiere cambios de config (verificado); solo la documentación explícita de la Fase 5 (T-16).
- No depende de `2026-08-10-token-diet` para ejecutarse, pero su disciplina de lectura (índice antes de abrir) es la que evita deshacer esa inversión — aplicada en el diseño de `knowledge-check.md` (Fase 4).
- `python3 scripts/lint_plugin.py` + las 9 (más la nueva, si aplica) suites de `tests/` en verde son prerequisito de cierre de cada fase.

---

## Criterios de aceptación (global)

- [ ] CA-01 — Existe `agent-kits/shared/templates/adr.md` con contexto · decisión · alternativas descartadas · consecuencias · estado, y cabe en una pantalla.
- [ ] CA-02 — `agent-kits/shared/knowledge-check.md` y `knowledge-write.md` existen y declaran la degradación ("si no existe, continúa; nunca bloquea"), con el mismo formato que `constitution-check.md`.
- [ ] CA-03 — Los cinco agentes lectores (`evaluator`, `planner`, `implementer`, `qa`, `documenter`) referencian `knowledge-check.md` en su flujo y ya declaraban `agent-kits/shared` en `dependencies` (verificado en la inspección: sin cambio de frontmatter necesario).
- [ ] CA-04 — El umbral de registro está escrito en `knowledge-write.md` con ejemplos de qué **NO** merece entrada, y la orientación de 0-2 entradas por iniciativa.
- [ ] CA-05 — Los cuatro puntos de nacimiento escriben: `debug-root-cause` (cierre F4), `qa` (flaky justificado como patrón), `/retro` (aprendizaje técnico), `planner`/`implementer` (ADR en decisión de diseño).
- [ ] CA-06 — `commands/retro.md` tiene dos salidas explícitas y sigue escribiendo la fila de `CALIBRATION.md` exactamente como hoy (sin regresión en la calibración).
- [ ] [GWT] CA-07 — Con el prompt de `agents/evaluator.md` **sin** el bloque de las tres lecciones y `docs/knowledge/LESSONS.md` conteniéndolas, el evaluator cita las lecciones aplicables al estimar (separar horas humanas de horas-IA, presupuestar proceso y revisión aparte) — prueba **crítica**: si falla, el bucle no funciona.
- [ ] CA-08 — La plantilla de `tasks.md` ya no contiene "Notas de implementación" (D2) y `ledger-lint.py` sigue en verde.
- [ ] CA-09 — Backfill hecho: `docs/knowledge/` contiene los aprendizajes técnicos de los 5 `retro.md` (en `LESSONS.md`/`gotchas.md`, por agente) y las 5 decisiones D1-D5 de `confluence-policy` como ADR con contexto y alternativas descartadas; cada entrada enlaza a su fuente, sin conclusiones añadidas.
- [ ] CA-10 — `docs/CONVENTIONS.md` y `docs/FLOWS.md` documentan la práctica (dónde vive, umbral, quién lee, quién escribe), con espejos `docs/en/` actualizados en el mismo cambio.
- [ ] CA-11 — `python3 scripts/lint_plugin.py` y todas las suites de `tests/` en verde.
- [ ] CA-12 — El índice `docs/knowledge/README.md` lista **todas** las entradas existentes con su etiqueta de área y su estado.
- [ ] **Coordinación (no CA de la spec, criterio propio del plan)** — `docs/knowledge/**` queda explícito como publicable en `skills/confluence-publish/SKILL.md` y confirmado por un test de `tests/test_confluence_scope.py`.

---

## Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| **Burocracia y ruido**: se pide papeleo y se rellena con relleno (ya ocurrió con la bitácora de `tasks.md`) | Alta | Alto | Umbral operativo con ejemplos de qué NO merece entrada (T-01); se retira "Notas de implementación" (T no aplica, es D2 directo); contar entradas en la primera retro |
| **Archivo muerto**: se escribe y nadie lee | Media | Alto | Fase 4 es el eje, no un extra; CA-07 (T-13) lo verifica con comportamiento observable |
| **Regresión silenciosa** al sacar las lecciones del prompt del evaluator | Media | Alto | Ejecutar el evaluator sobre una spec de prueba antes/después de T-12; el bloque queda en el historial de git para poder volver |
| **Coste de contexto**: leer memoria en 5 agentes deshace parte de `token-diet` | Media | Medio | Progressive disclosure (índice corto primero); medir tokens de una ejecución antes/después en la retro |
| **Doctrina obsoleta o errónea**: una entrada mal diagnosticada condiciona a los agentes que la leen | Media | Alto | `estado: propuesta` hasta validación por doble lente o usuario; constitución manda sobre la memoria |
| **Colisión de IDs de ADR** con lotes paralelos (máx. 3 tareas) | Media | Bajo | Numeración con sufijo por slug de iniciativa; sin lint (C-06 diferido) la detección es manual — la primera colisión es, de hecho, uno de los disparadores para retomar C-06 |
| **Índice a mano se desincroniza** (consecuencia asumida de diferir C-06) | Media | Medio | CA-12 + "quien añade entrada actualiza el índice en el mismo cambio" |
| **Distorsión en el backfill** (T-08/T-09): resumir un aprendizaje matizado como regla tajante | Media | Medio | Enlace obligatorio a la fuente y prohibición de añadir conclusiones (CA-09); `estado: propuesta` por defecto |
| Estimación de horas humanas no validada (0 h reales en el histórico) | Alta | Medio | Presentar el coste como comparativa, no compromiso; `/retro` al cerrar |

---

## Métricas de éxito

- El evaluator, ejecutado sobre una spec de prueba con el prompt adelgazado, cita las tres lecciones migradas leídas de `LESSONS.md` (CA-07 verificado con evidencia pegada, no afirmado).
- `docs/knowledge/` contiene, al cerrar, ≥5 ADR (backfill de confluence-policy) + al menos 1 entrada por agente con aprendizaje en `LESSONS.md`/`gotchas.md` (backfill de los 5 `retro.md`), cada una trazable a su fuente.
- Contando entradas nuevas al cierre de la **siguiente** iniciativa tras esta: ≤3 (umbral no burocrático, spec §Pruebas).
- `python3 scripts/lint_plugin.py` + todas las suites de `tests/` en verde tras el cambio completo (16/16 tareas).

---

## Changelog del plan

| Fecha | Cambio | Autor |
|-------|--------|-------|
| 2026-08-20 | Creación del plan a partir de `spec.md` (aprobada) y `evaluation.md` (completado, GO). Inspección previa de las 4 piezas que la evaluación no pudo verificar: sin cambio de horas, C-02 sube de confianza Baja a Media. 5 fases, 16 tareas (C-06 diferido, sin tareas). | planner |

---

## Siguiente paso

Con el **OK del plan** del usuario, el agente **`implementer`** lo ejecuta fase a fase (orden obligatorio 1→2→3→4→5) sobre una rama, marcando `tasks.md` como **ledger canónico**. La Fase 4 (T-13) es la prueba crítica: no se da la iniciativa por cerrada sin evidencia pegada de que el evaluator sigue aplicando las lecciones migradas. Cierre de cada fase con `python3 scripts/lint_plugin.py` + suites de `tests/`. Se recomienda ejecutar `/retro` al cerrar — que además alimentará el propio `docs/knowledge/` que esta iniciativa crea.
