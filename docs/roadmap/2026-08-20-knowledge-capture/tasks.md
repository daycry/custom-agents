---
generacion:
  inicio: 2026-08-20T10:32:18Z
  fin: 2026-08-20T10:37:05Z
  fuente: estimado        # ventana compartida con improvement-plan.md — degradación: sin carpeta de transcripciones en este sandbox
  tokens_reales: no-medido (sandbox)
  eur: null
  horas_ia: null
  duracion: no-medido (sandbox)
  ratio_usado: 479326
---

# Checklist de Tareas — Memoria técnica de los agentes (knowledge-capture)

| | |
|---|---|
| **Estado** | completado |
| **Fecha** | 2026-08-20 |
| **Plan** | [`improvement-plan.md`](./improvement-plan.md) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del plan. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador SDD externo— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

> **Disciplina de desarrollo (P1-bis).** `.claude/dev.json` no existe en este entorno → disciplina clásica (sin TDD obligatorio, sin worktree, sin subagentes por tarea). `usage-meter.py` no puede medir en este sandbox: los tiempos reales quedan `(estimado)`, nunca `(medido)`. `.claude/jira.json`/`.claude/confluence.json` no existen (sin opt-in): no hay volcado a Jira ni sincronización con Confluence durante esta implementación — constatado una vez, no se repite por tarea. Rama de trabajo: `feature/knowledge-capture`, creada desde `master` (que ya incluye `confluence-policy` mergeada).

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — ADR ligero + gotchas | 6 | 6 | 100% | 2,15 / 8,5h | 0,21 / 0,21h | 0,055 / 0,05h | n/d / 95k |
| Fase 2 — `/retro` con dos salidas | 1 | 1 | 100% | 0,4 / 1,5h | 0,04 / 0,04h | 0,01 / 0,01h | n/d / 20k |
| Fase 3 — Backfill semilla | 2 | 2 | 100% | 0,9 / 2,0h | 0,09 / 0,08h | 0,022 / 0,02h | n/d / 35k |
| Fase 4 — Bucle de lectura ⭐ | 4 | 4 | 100% | 2,0 / 5,0h | 0,14 / 0,14h | 0,036 / 0,04h | n/d / 60k |
| Fase 5 — Documentar la práctica | 3 | 3 | 100% | 1,4 / 3,0h | 0,095 / 0,09h | 0,024 / 0,02h | n/d / 45k |
| **TOTAL** | **16** | **16** | **100%** | **6,85 / 20,0h** | **0,575 / 0,56h** | **0,147 / 0,14h** | **n/d / 255k** |

> **Horas → Jira.** El worklog que imputa `jira-sync` al completar cada tarea es Tiempo IA (ejec.) + Supervisión (real; o estimación si no hay real), topado a la jornada configurada. Ver `skills/jira-sync/SKILL.md`. **Nota:** las horas IA/supervisión de esta tabla son solo el trabajo por característica (heredado de `evaluation.md`); las líneas transversales de revisión adversarial y coste de proceso viven en `improvement-plan.md` §Presupuesto económico. La suma de horas-IA por tarea (0,56h) difiere en centésimas del total de característica de la evaluación (0,52h) por redondeo al repartir tokens por tarea — declarado, no un error de cálculo.

---

## Fase 1 — ADR ligero + gotchas en el punto de nacimiento (C-01 + C-02)

**Estado**: completado · **Estimado**: 8,5h · **Real**: 2,15h humanas (estimado) · **Coste est.**: ≈425 € · **Tokens est.**: 95k

> **Verificación de fase (P5):** `python3 scripts/lint_plugin.py` → 0 errores (3 avisos preexistentes). `for t in tests/test_*.py; do python3 "$t" || exit 1; done` → todas las suites en verde (sin tocar tests en esta fase). Sincronización Confluence: no aplica (sin `.claude/confluence.json` en este repo).

### T-01 — Plantilla de ADR + fragmento de escritura `knowledge-write.md`

- **Descripción**: Crear `agent-kits/shared/templates/adr.md` (contexto · decisión · alternativas descartadas · consecuencias · estado, corta, cabe en una pantalla) y `agent-kits/shared/knowledge-write.md` (molde de `constitution-check.md`): define el **umbral** combinado de ADR y gotcha con ejemplos explícitos de qué **NO** merece entrada, la orientación de 0-2 entradas por iniciativa, y dónde escribe cada tipo (`docs/knowledge/adr/`, `docs/knowledge/gotchas.md`). Es la base que consumen T-02, T-03, T-05 y T-06.
- **Estado**: completado
- **Tiempo humano**: est. 1,5h · real 0,4h (estimado)
- **Tiempo IA (ejec.)**: est. 0,04h · real 0,04h (estimado — usage-meter.py no disponible)
- **Supervisión**: est. 0,01h (≈25 % IA) · real 0,01h (estimado)
- **Previsión IA**: 15k in / 2k out tok · 0,12 €
- **Dependencias**: ninguna
- **Tipo**: docs
- **Archivos**: `agent-kits/shared/templates/adr.md` (nuevo), `agent-kits/shared/knowledge-write.md` (nuevo)
- **Cubre (tests)**: — (no aplica, sin UI)

**Criterios de aceptación**
- [x] CA-01 — `agent-kits/shared/templates/adr.md` existe con los 5 campos (contexto · decisión · alternativas descartadas · consecuencias · estado) y cabe en una pantalla (≤ ~40 líneas).
- [x] CA-02 (parcial) — `knowledge-write.md` existe, declara la degradación ("si `docs/knowledge/` no existe, se crea en el primer registro; nunca bloquea") con el mismo formato que `constitution-check.md`.
- [x] CA-04 — El umbral está escrito con al menos 2 ejemplos concretos de qué **NO** merece ADR y 2 de qué **NO** merece gotcha, y la orientación de 0-2 entradas por iniciativa.

**Subtareas**
- [x] Redactar `templates/adr.md` con `ID: ADR-NNN`, campos y `estado: propuesta|aceptada|obsoleta`.
- [x] Redactar `knowledge-write.md`: umbral (copiado literal de `spec.md` §Decisiones de diseño, fila "Umbral de registro"), dónde escribe cada tipo, ejemplos de qué NO registrar.
- [x] Revisar que el molde (estructura de frases, tono) sea consistente con `constitution-check.md` (mismo patrón "si existe/no existe... nunca bloquea").

**Notas**: base compartida por C-01 y C-02 (evita escribir el fragmento dos veces); confirmado en la inspección previa que no hay ninguna pieza equivalente ya existente que deba reconciliarse.

<!-- ==================================================================== -->

### T-02 — `agents/planner.md` escribe ADR en la puerta de decisión

- **Descripción**: Añadir a `agents/planner.md` (tras P3/P4, en la sección de reglas junto al molde de `constitution-check.md`, línea 92) el paso: cuando una decisión de diseño del plan cruza el umbral (cierra alternativa y afecta a 2+ piezas o se tomó en puerta), escribe un ADR `estado: propuesta` en `docs/knowledge/adr/` usando la plantilla de T-01, y actualiza el índice `docs/knowledge/README.md` en el mismo cambio.
- **Estado**: completado
- **Tiempo humano**: est. 1h · real 0,2h (estimado)
- **Tiempo IA (ejec.)**: est. 0,03h · real 0,03h (estimado)
- **Supervisión**: est. 0,01h (≈25 % IA) · real 0,01h (estimado)
- **Previsión IA**: 10k in / 2k out tok · 0,09 €
- **Dependencias**: T-01
- **Tipo**: docs
- **Archivos**: `agents/planner.md` (§3 Reglas, cerca de línea 92)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] CA-05 (parcial: planner) — `agents/planner.md` declara el paso de escritura de ADR condicionado al umbral, citando `knowledge-write.md`.
- [x] El frontmatter `dependencies.kits` de `planner.md` ya incluye `agent-kits/shared` (verificado en la inspección previa: sin cambio necesario).

**Subtareas**
- [x] Añadir el párrafo de escritura de ADR en §3 Reglas de `planner.md`.
- [x] Verificar que no se solapa con el paso de lectura que añadirá T-11 en el mismo fichero (mismo bloque de reglas, dos párrafos distintos).

**Notas**: la inspección previa confirmó que P3 (Descomposición)/P4 (Estimación) son los momentos naturales donde el planner toma decisiones de diseño del plan (p. ej. elegir una arquitectura entre alternativas).

<!-- ==================================================================== -->

### T-03 — `agents/implementer.md` escribe ADR en la puerta de decisión

- **Descripción**: Mismo paso que T-02, en `agents/implementer.md`: cuando el implementer resuelve una ambigüedad del plan eligiendo un default (regla ya existente: "si el plan es ambiguo, elige el default más seguro y documéntalo"), si esa elección cruza el umbral, escribe ADR en vez de solo anotarlo en `tasks.md`.
- **Estado**: completado
- **Tiempo humano**: est. 1h · real 0,3h (estimado)
- **Tiempo IA (ejec.)**: est. 0,03h · real 0,03h (estimado)
- **Supervisión**: est. 0,01h (≈25 % IA) · real 0,01h (estimado)
- **Previsión IA**: 10k in / 2k out tok · 0,09 €
- **Dependencias**: T-01
- **Tipo**: docs
- **Archivos**: `agents/implementer.md` (cerca de la regla "Ejecutas, no planificas ni evalúas"; frontmatter `dependencies.kits`)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] CA-05 (parcial: implementer) — `agents/implementer.md` declara el paso de escritura de ADR condicionado al umbral.
- [x] No se duplica con la anotación existente en `tasks.md` para defaults NO ambiguos que no cruzan el umbral (deja claro cuándo es solo nota y cuándo es ADR).

**Subtareas**
- [x] Añadir el párrafo en `agents/implementer.md`, junto a la regla de defaults.
- [x] Aclarar la frontera con la anotación en `tasks.md` (nota local vs. ADR transversal).

**Desviación declarada (corrige la inspección previa del plan):** la inspección de `improvement-plan.md` daba por hecho que los 5 agentes lectores "ya incluyen `agent-kits/shared`" en `dependencies.kits` (T-02/T-11 lo citan como "sin cambio necesario"). Verificado al tocar el fichero: `agents/implementer.md` tenía `kits: []` — inconsistente con que **ya** referenciaba `constitution-check.md` de ese kit sin declararlo. Corregido aquí (`kits: [agent-kits/shared]`), ya que esta tarea es la primera en tocar el frontmatter de `implementer.md` en este plan; `lint_plugin.py` sigue en verde (0 errores). Los otros 4 agentes (evaluator, planner, qa, documenter) sí lo declaraban ya, confirmado por inspección directa.

**Notas**: —

<!-- ==================================================================== -->

### T-04 — `agents/documenter.md` indexa `docs/knowledge/` en vez de derivar del código

- **Descripción**: Modificar `agents/documenter.md` L74 (categoría "arquitectura y decisiones" hoy derivada del código) y L96 ("README existente, ADRs… reutiliza lo que ya haya") para que, al cierre del ciclo, **indexe** las entradas de `docs/knowledge/adr/` y `docs/knowledge/gotchas.md` en su taxonomía, en vez de re-derivar decisiones leyendo el código.
- **Estado**: completado
- **Tiempo humano**: est. 0,5h · real 0,15h (estimado)
- **Tiempo IA (ejec.)**: est. 0,01h · real 0,01h (estimado)
- **Supervisión**: est. 0,01h (≈25 % IA) · real 0,005h (estimado)
- **Previsión IA**: 4k in / 1k out tok · 0,04 €
- **Dependencias**: T-01
- **Tipo**: docs
- **Archivos**: `agents/documenter.md` (L74, L96)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] `agents/documenter.md` L74 ya no dice que la categoría "arquitectura y decisiones" se deriva del código: dice que se indexan las entradas de `docs/knowledge/adr/`.
- [x] L96 pasa de "reutiliza lo que ya haya" a "indexa `docs/knowledge/` en la taxonomía correspondiente" (referencia explícita a la ruta).

**Subtareas**
- [x] Editar L74.
- [x] Editar L96.

**Notas**: cambio pequeño y localizado, confirmado en la inspección previa (ambas líneas existen tal como las cita `evaluation.md`).

---

### T-05 — `debug-root-cause`: el cierre de Fase 4 escribe el gotcha

- **Descripción**: Añadir al final de la **Fase 4 — Fix + test de regresión** de `skills/debug-root-cause/SKILL.md` un paso: si la causa raíz probada (Fase 3) costó ≥1 ciclo de depuración o rompió/casi rompió una garantía del producto (umbral de `knowledge-write.md`), escribe un gotcha en `docs/knowledge/gotchas.md` con síntoma (de la Fase 1) · causa raíz (de la Fase 3) · qué hacer en su lugar · enlace al test de regresión (de la Fase 4). Si no cruza el umbral, no escribe nada — decláralo también.
- **Estado**: completado
- **Tiempo humano**: est. 2,5h · real 0,6h (estimado)
- **Tiempo IA (ejec.)**: est. 0,06h · real 0,06h (estimado)
- **Supervisión**: est. 0,02h (≈25 % IA) · real 0,015h (estimado)
- **Previsión IA**: 24k in / 4k out tok · 0,20 €
- **Dependencias**: T-01
- **Tipo**: docs
- **Archivos**: `skills/debug-root-cause/SKILL.md` (Fase 4, y §Integración con /dev-cycle)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] CA-05 (parcial: debug-root-cause) — la Fase 4 de `debug-root-cause/SKILL.md` escribe el gotcha cuando cruza el umbral, con los 4 campos (síntoma, causa raíz, alternativa, enlace al test).
- [x] Queda explícito que, con diagnóstico **parcial** (gancho del 3.er rojo sin Fase 4 aplicada), no se escribe gotcha — solo con Fase 4 completa.
- [x] No se reestructuran las 4 fases existentes: el paso se añade al final, sin tocar su secuencia (confirmado viable en la inspección previa).

**Subtareas**
- [x] Añadir el paso al final de la Fase 4.
- [x] Verificar la interacción con la sección "Integración con /dev-cycle" (el gancho del 3.er rojo se detiene en Fase 3 salvo que el usuario decida seguir con el fix — el gotcha solo se escribe si se llega a Fase 4 de verdad).

**Notas**: era el punto de mayor incertidumbre de C-02 en la evaluación (confianza Baja); la inspección previa la sube a Media — el cambio es tan localizado como esperaba la spec.

<!-- ==================================================================== -->

### T-06 — `agents/qa.md`: flaky justificado que es patrón escribe gotcha

- **Descripción**: Modificar `agents/qa.md` (entorno de `flaky-justify.json`, L66-68) para que, si un test flaky justificado se repite en **2 o más ciclos** (patrón, no accidente aislado), escriba un gotcha en `docs/knowledge/gotchas.md` ("este test es inestable por X, mitigación Y"), en vez de dejarlo solo como evidencia puntual en `testing/raw/`.
- **Estado**: completado
- **Tiempo humano**: est. 2h · real 0,5h (estimado)
- **Tiempo IA (ejec.)**: est. 0,04h · real 0,04h (estimado)
- **Supervisión**: est. 0,01h (≈25 % IA) · real 0,01h (estimado)
- **Previsión IA**: 19k in / 2k out tok · 0,13 €
- **Dependencias**: T-01
- **Tipo**: docs
- **Archivos**: `agents/qa.md` (L66-68, y su DoD de cierre)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] CA-05 (parcial: qa) — `agents/qa.md` declara que un flaky justificado escribe gotcha cuando hay una señal **verificable desde disco ahora mismo** (ya existe una entrada sobre el test/motivo en `docs/knowledge/gotchas.md`, o el `flaky-justify.json` de la **ejecución actual** trae, para otro test de la tanda, un motivo idéntico a uno ya registrado en `gotchas.md`); uno aislado sin esas señales no escribe gotcha. *(Enmendado en revisión, intento 2: el criterio original dependía de comparar con el `flaky-justify.json` de una ejecución **anterior**, que `raw/` reutiliza/sobrescribe y por tanto no conserva — no era verificable.)*
- [x] Queda explícito el criterio para distinguir "patrón" de "accidente" (no delegado al criterio libre del agente sin regla escrita).

**Subtareas**
- [x] Redactar el criterio de "patrón" (repetición ≥2 ciclos con el mismo motivo o síntoma).
- [x] Añadir el paso de escritura del gotcha junto al manejo actual de `flaky-justify.json`.

**Notas**: se propone en la spec como incógnita menor ("¿vive en `knowledge/` o basta con `flaky-justify.json`?"); esta tarea fija el criterio operativo: solo si se repite.

---

## Fase 2 — `/retro` con dos salidas (C-04)

**Estado**: completado · **Estimado**: 1,5h · **Real**: 0,4h humanas (estimado) · **Coste est.**: ≈75 € · **Tokens est.**: 20k

> **Verificación de fase (P5):** `python3 scripts/lint_plugin.py` → 0 errores. Todas las suites de `tests/` en verde (sin tocar tests en esta fase — `commands/retro.md` es prosa).

### T-07 — `commands/retro.md`: separar números de aprendizajes técnicos

- **Descripción**: Modificar `commands/retro.md` (L16-17) para que produzca **dos salidas** explícitas: la fila de `CALIBRATION.md` **exactamente como hoy** (números: desviación, tokens/hora) y, además, los aprendizajes **técnicos** cualitativos hacia `docs/knowledge/LESSONS.md` (agrupados por agente) o `docs/knowledge/gotchas.md` según corresponda, con la marca `Estado: [actualizado|sin cambios]` del patrón `nemesis`. Un aprendizaje puede alimentar las dos salidas (número + lección) con enlace cruzado, sin duplicar el texto.
- **Estado**: completado
- **Tiempo humano**: est. 1,5h · real 0,4h (estimado)
- **Tiempo IA (ejec.)**: est. 0,04h · real 0,04h (estimado)
- **Supervisión**: est. 0,01h (≈25 % IA) · real 0,01h (estimado)
- **Previsión IA**: 17k in / 3k out tok · 0,15 €
- **Dependencias**: T-01 (formato de `knowledge-write.md`)
- **Tipo**: docs
- **Archivos**: `commands/retro.md` (L4, L16-17)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] CA-06 — `commands/retro.md` tiene dos salidas explícitas (números → `CALIBRATION.md`; técnicos → `docs/knowledge/`) y la fila de `CALIBRATION.md` se sigue escribiendo **exactamente** como hoy (sin regresión: mismo formato de columnas, mismo cálculo de mediana).
- [x] La salida técnica aplica `Estado: [actualizado|sin cambios]` al cerrar.
- [x] Un aprendizaje que vaya a las dos salidas usa un enlace cruzado (p. ej. "ver `docs/knowledge/LESSONS.md#evaluator`"), sin copiar el texto dos veces.

**Subtareas**
- [x] Añadir el paso de la segunda salida tras el paso existente de `CALIBRATION.md`.
- [x] Definir el criterio de reparto: ¿va a `LESSONS.md` (proceso/agente) o a `gotchas.md` (trampa técnica concreta)? Documentarlo con un ejemplo de cada uno.
- [x] Ejecutar mentalmente sobre `retro.md` de `sdd-hardening` (ya citado en la spec: "el coste se fue en la revisión, no en escribir") para comprobar que el criterio de reparto no es ambiguo.

**Notas**: es la vía por la que se hace el backfill (Fase 3, T-08) — dejar el mecanismo bien definido aquí ahorra ambigüedad en esa tarea.

---

## Fase 3 — Backfill semilla de la memoria (C-07)

**Estado**: completado · **Estimado**: 2h · **Real**: 0,9h humanas (estimado) · **Coste est.**: ≈100 € · **Tokens est.**: 35k

> **Verificación de fase (P5):** `python3 scripts/lint_plugin.py` → 0 errores (3 avisos preexistentes, sin cambios). `for t in tests/test_*.py; do python3 "$t" || exit 1; done` → todas las suites en verde (backfill es solo `docs/`, sin tocar código ni scripts). `python3 agent-kits/shared/ledger-lint.py docs/roadmap/2026-08-20-knowledge-capture/tasks.md` → 0 incoherencias.

### T-08 — Backfill de `LESSONS.md`/`gotchas.md` desde los 5 `retro.md` existentes

- **Descripción**: Usando la segunda salida de `/retro` (T-07) como mecanismo (no a mano), transformar los aprendizajes técnicos de los 5 `retro.md` existentes (`sdd-hardening`, `workflow-polish`, `plugin-dev`, `subagent-personas`, `quick-implement`) en entradas de `docs/knowledge/LESSONS.md` (agrupadas por agente) y, si aplica, `docs/knowledge/gotchas.md`. Cada entrada enlaza a su `retro.md` fuente; ninguna añade conclusiones que no estuvieran en él.
- **Estado**: completado
- **Tiempo humano**: est. 1h · real 0,4h (estimado)
- **Tiempo IA (ejec.)**: est. 0,04h · real 0,04h (estimado)
- **Supervisión**: est. 0,01h (≈25 % IA) · real 0,01h (estimado)
- **Previsión IA**: 15k in / 2,5k out tok · 0,13 €
- **Dependencias**: T-07
- **Tipo**: docs
- **Archivos**: `docs/knowledge/LESSONS.md`, `docs/knowledge/gotchas.md`, `docs/knowledge/README.md`, los 5 `docs/roadmap/*/retro.md` (solo lectura)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] CA-09 (parcial: retros) — Los 5 `retro.md` están representados en `LESSONS.md`/`gotchas.md`, agrupados por agente, cada entrada con enlace a su fuente (`docs/roadmap/<slug>/retro.md`).
- [x] Ninguna entrada añade una conclusión que no esté literalmente en su `retro.md` de origen (trazabilidad verificable por inspección directa, criterio de CA-09).
- [x] Cada entrada nace con `estado: propuesta` (a validar por doble lente/usuario), salvo que el propio `retro.md` ya la presente como validada.

**Subtareas**
- [x] Releer los 5 `retro.md` y extraer el/los aprendizaje(s) técnico(s) de cada uno (no los números, ya están en `CALIBRATION.md`).
- [x] Redactar la entrada correspondiente en `LESSONS.md` (por agente) o `gotchas.md` (si es una trampa técnica concreta), con enlace a la fuente.
- [x] Actualizar `docs/knowledge/README.md` (índice) con las nuevas entradas.

**Desviación declarada:** los 4 aprendizajes de estimación de `sdd-hardening`, `workflow-polish`, `subagent-personas` y `quick-implement` se agrupan bajo la sección `## evaluator` de `LESSONS.md` (no bajo secciones por agente separadas) porque los cinco son, literalmente, lecciones de **estimación/calibración** — el mismo dominio que las tres lecciones hardcodeadas que T-12 migrará al mismo fichero. La lección de `plugin-dev` (plantilla sin probar) se clasificó como **gotcha**, no lección: es una trampa concreta y comprobada (2 defectos reales que casi rompen el linter), no un aprendizaje de proceso transversal — encaja mejor en el formato síntoma/causa/alternativa de `gotchas.md`. Todas nacen `estado: aceptada` (no `propuesta`): cada `retro.md` fuente ya pasó por su propio proceso de cierre con el usuario, así que se tratan como material ya validado (excepción prevista explícitamente en el criterio de aceptación de esta tarea).

**Notas**: es prerequisito de la prueba crítica de la Fase 4 (T-13): sin memoria real, CA-07 no demuestra nada.

<!-- ==================================================================== -->

### T-09 — Backfill de 5 ADR desde las decisiones D1-D5 de `confluence-policy`

- **Descripción**: Convertir las cinco decisiones D1-D5 de `docs/roadmap/2026-08-20-confluence-policy/spec.md` §Decisiones de diseño en **cinco ADR separados** (uno por decisión, cada una cierra su propia alternativa y se cita por ID) en `docs/knowledge/adr/`, con su contexto y sus alternativas descartadas tal como están en la spec fuente. Enlace obligatorio a `spec.md` §Decisiones de diseño.
- **Estado**: completado
- **Tiempo humano**: est. 1h · real 0,5h (estimado)
- **Tiempo IA (ejec.)**: est. 0,04h · real 0,05h (estimado)
- **Supervisión**: est. 0,01h (≈25 % IA) · real 0,012h (estimado)
- **Previsión IA**: 15k in / 2,5k out tok · 0,13 € · **real**: n/d (usage-meter no disponible) / est. 20k tok
- **Dependencias**: T-01 (plantilla)
- **Tipo**: docs
- **Archivos**: `docs/knowledge/adr/ADR-001-*.md` … `ADR-005-*.md`, `docs/roadmap/2026-08-20-confluence-policy/spec.md` (solo lectura)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] CA-09 (parcial: confluence-policy) — Existen 5 ADR (D1 alcance curado, D2 sin presets de audiencia, D3 ledger sincroniza al cerrar fase, D4 `**/testing/**` excluido, D5 verificador+staging), cada uno con contexto, decisión, alternativas descartadas (las que la spec descartó explícitamente) y consecuencias.
- [x] Cada ADR enlaza a `docs/roadmap/2026-08-20-confluence-policy/spec.md#decisiones-de-diseño` (o la fila concreta de la tabla) como fuente.
- [x] Numeración `ADR-NNN` secuencial sin colisiones con los ADR de T-08 si los hubiera (confirmado: T-08 no generó ningún ADR, solo lecciones/gotchas — ADR-001 a ADR-005 son los primeros del repo).

**Subtareas**
- [x] Releer la tabla de "Decisiones de diseño" y la sección "Decisiones confirmadas" de `spec.md` de `confluence-policy`.
- [x] Redactar los 5 ADR con la plantilla de T-01.
- [x] Actualizar `docs/knowledge/README.md` (índice) con las 5 nuevas entradas.

**Desviación declarada (corrige el paréntesis descriptivo del propio criterio de aceptación):** el glosado entre paréntesis de D2/D3 en el criterio de aceptación de esta tarea, tal como estaba redactado en el plan ("D2 retirar bitácora", "D3 opt-in siempre activo"), no corresponde a las decisiones D2/D3 reales de `confluence-policy/spec.md` — esas etiquetas describen, respectivamente, el D2 de **esta misma iniciativa** (retirar la sección "Notas de implementación" del planner) y una paráfrasis imprecisa de D3. Releída la spec fuente (única fuente admitida por CA-09, sin inventar conclusiones), las decisiones reales son: **D2 = sin presets de audiencia** y **D3 = el ledger sincroniza con Confluence al cerrar cada fase, no por tarea ni solo al final**. Los 5 ADR reflejan el contenido real de la spec fuente, no el paréntesis del criterio; la descripción de la tarea (que remite sin ambigüedad a "las cinco decisiones D1-D5 de `.../confluence-policy/spec.md`") y CA-09 (fidelidad a la fuente) priman sobre la glosa entre paréntesis.

**Notas**: se acota a estas 5 decisiones y a los 5 `retro.md` de T-08 — nada más (spec §Alcance: "backfill completo... fuera"). Cierra la Fase 3.

---

## Fase 4 — Bucle de lectura + migración de lecciones ⭐ (C-03)

**Estado**: completado · **Estimado**: 5h · **Real**: 2,0h humanas (estimado) · **Coste est.**: ≈250 € · **Tokens est.**: 60k

> **Verificación de fase (P5):** `python3 scripts/lint_plugin.py` → 0 errores (3 avisos preexistentes). `for t in tests/test_*.py; do python3 "$t" || exit 1; done` → todas las suites en verde. `grep -n "Tres lecciones" agents/evaluator.md` → vacío. **CA-07 (T-13, prueba crítica): PASA** — ver evidencia pegada en T-13.

### T-10 — Crear `agent-kits/shared/knowledge-check.md`

- **Descripción**: Crear el fragmento compartido `knowledge-check.md`, calcado del patrón de `constitution-check.md` y del protocolo de bookends de `agents/nemesis.md` (L60-78: apertura lee, cierre actualiza): "antes de trabajar, si `docs/knowledge/` existe, lee su `README.md` (índice corto) y abre **solo** las entradas cuya etiqueta de área toque tu tarea (progressive disclosure); si no existe, continúa sin quejarte — nunca bloquea".
- **Estado**: completado
- **Tiempo humano**: est. 1h · real 0,4h (estimado)
- **Tiempo IA (ejec.)**: est. 0,03h · real 0,03h (estimado)
- **Supervisión**: est. 0,01h (≈25 % IA) · real 0,008h (estimado)
- **Previsión IA**: 10k in / 2k out tok · 0,09 € · **real**: n/d (usage-meter no disponible) / est. 12k tok
- **Dependencias**: ninguna
- **Tipo**: docs
- **Archivos**: `agent-kits/shared/knowledge-check.md` (nuevo)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] CA-02 (parcial) — `knowledge-check.md` existe, con el mismo formato que `constitution-check.md` (comprobación → si existe/si no existe → nunca bloquea).
- [x] Declara explícitamente la progressive disclosure: lee el índice primero, abre la entrada completa solo si aplica a la tarea en curso.

**Subtareas**
- [x] Redactar el fragmento con la cabecera estándar (`<!-- FRAGMENTO COMPARTIDO... -->`) igual que `constitution-check.md`.
- [x] Citar el protocolo de `nemesis.md` como precedente en un comentario o nota (trazabilidad del patrón).

**Notas**: puede hacerse en paralelo a la Fase 1-3 (sin dependencias), pero se planifica aquí porque su prueba real (T-13) necesita memoria poblada (Fase 3 ya cerrada en el orden de ejecución).

<!-- ==================================================================== -->

### T-11 — Cablear el bucle de lectura en los cinco agentes

- **Descripción**: Añadir el párrafo de `knowledge-check.md` en la sección de reglas de los cinco agentes lectores, en el mismo punto donde ya tienen el molde idéntico de `constitution-check.md` (verificado en la inspección previa): `agents/evaluator.md` L95, `agents/planner.md` L92, `agents/implementer.md` L78, `agents/qa.md` L81, `agents/documenter.md` L142. Reparto de qué lee cada uno (propuesta de la evaluación): `evaluator` → `LESSONS.md`; `planner` → ADR + lecciones; `implementer` → ADR + gotchas; `qa` → gotchas; `documenter` → todo (para indexar, ver T-04).
- **Estado**: completado
- **Tiempo humano**: est. 1,5h · real 0,6h (estimado)
- **Tiempo IA (ejec.)**: est. 0,04h · real 0,04h (estimado)
- **Supervisión**: est. 0,01h (≈25 % IA) · real 0,01h (estimado)
- **Previsión IA**: 16k in / 2k out tok · 0,12 € · **real**: n/d (usage-meter no disponible) / est. 18k tok
- **Dependencias**: T-10
- **Tipo**: docs
- **Archivos**: `agents/evaluator.md`, `agents/planner.md`, `agents/implementer.md`, `agents/qa.md`, `agents/documenter.md`
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] CA-03 — Los cinco agentes referencian `knowledge-check.md` en su flujo, cada uno con el subconjunto de `docs/knowledge/` que le corresponde (según el reparto de la descripción).
- [x] El frontmatter `dependencies.kits` de los cinco ya incluye `agent-kits/shared` (confirmado: los 5 lo declaran; `implementer.md` ya lo tenía corregido desde T-03).
- [x] El párrafo nuevo no sustituye ni rompe el de `constitution-check.md` ya existente (van uno junto al otro, ambos completos; verificado con `grep -n "constitution-check\|knowledge-check"` en los 5 ficheros).

**Subtareas**
- [x] Añadir el párrafo en `agents/evaluator.md` (L96, junto al de constitución).
- [x] Añadir el párrafo en `agents/planner.md` (L94, tras el bullet de escritura de T-02).
- [x] Añadir el párrafo en `agents/implementer.md` (L82, tras el bullet de escritura de T-03).
- [x] Añadir el párrafo en `agents/qa.md` (L84, junto al de constitución).
- [x] Añadir el párrafo en `agents/documenter.md` (L145, junto al de constitución).

**Notas**: es la tarea de mayor superficie (5 ficheros) pero mecánica — mismo texto base, mismo punto de inserción (junto a `constitution-check.md`, o justo tras el bullet de escritura de `knowledge-write.md` en planner/implementer para mantener juntas lectura+escritura de memoria), confirmado en la inspección previa. `python3 scripts/lint_plugin.py` → 0 errores tras el cambio.

<!-- ==================================================================== -->

### T-12 — Migrar las tres lecciones hardcodeadas del evaluator a `LESSONS.md`

- **Descripción**: Retirar de `agents/evaluator.md` el bloque "Tres lecciones de la primera calibración real (2026-08-18)" (línea 71, tras P2-bis) y trasladarlo, sin reformular el contenido, a una entrada agrupada bajo "evaluator" en `docs/knowledge/LESSONS.md`. El prompt queda con una referencia a `knowledge-check.md` (ya añadida en T-11) en vez del bloque literal.
- **Estado**: completado
- **Tiempo humano**: est. 1h · real 0,4h (estimado)
- **Tiempo IA (ejec.)**: est. 0,03h · real 0,03h (estimado)
- **Supervisión**: est. 0,01h (≈25 % IA) · real 0,008h (estimado)
- **Previsión IA**: 10k in / 2k out tok · 0,09 € · **real**: n/d (usage-meter no disponible) / est. 12k tok
- **Dependencias**: T-08 (para no chocar con las entradas de `LESSONS.md` escritas por el backfill; esta tarea añade su propia sección "evaluator")
- **Tipo**: docs
- **Archivos**: `agents/evaluator.md` (L71-74), `docs/knowledge/LESSONS.md`, `docs/knowledge/README.md`
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] El bloque "Tres lecciones..." desaparece literalmente de `agents/evaluator.md` (verificado: `grep -n "Tres lecciones" agents/evaluator.md` → vacío, exit 1).
- [x] `docs/knowledge/LESSONS.md` contiene las tres lecciones, agrupadas bajo "evaluator" (subsección propia "### Tres lecciones de la primera calibración real (2026-08-18)"), con el mismo contenido (sin reformular ni perder matices — copia literal verbatim de las 3 numeradas).
- [x] El commit que retira el bloque queda en el historial de git (no se pierde: recuperable si T-13 revela una regresión).

**Subtareas**
- [x] Copiar el bloque literal a `LESSONS.md` bajo la sección "evaluator".
- [x] Retirar el bloque de `agents/evaluator.md`, sustituido por una referencia explícita a `docs/knowledge/LESSONS.md` §evaluator vía `knowledge-check.md` (ya cableado en T-11 en §3 REGLAS; el propio P2-bis ahora remite ahí).
- [x] Actualizar el índice `docs/knowledge/README.md`.

**Notas**: es la "prueba de fuego" del mecanismo — si T-13 falla, este commit es el primero en revisar (revertir es trivial: está en git).

<!-- ==================================================================== -->

### T-13 — Prueba de comportamiento del bucle (CA-07, prueba crítica)

- **Descripción**: Con el prompt de `agents/evaluator.md` ya adelgazado (T-12) y `docs/knowledge/LESSONS.md` poblado (T-08 + T-12), ejecutar el evaluator sobre una spec pequeña de prueba y verificar que **sigue aplicando** las tres lecciones (separar horas humanas de horas-IA, presupuestar el proceso aparte, presupuestar la revisión aparte) — leídas del fichero, no del prompt. Pegar la evidencia (fragmento de la evaluación generada citando las lecciones) en el ledger.
- **Estado**: completado
- **Tiempo humano**: est. 1,5h · real 0,6h (estimado)
- **Tiempo IA (ejec.)**: est. 0,04h · real 0,04h (estimado)
- **Supervisión**: est. 0,01h (≈25 % IA) · real 0,01h (estimado)
- **Previsión IA**: 16k in / 2k out tok · 0,12 € · **real**: n/d (usage-meter no disponible) / est. 14k tok
- **Dependencias**: T-11, T-12
- **Tipo**: test
- **Archivos**: `/tmp/knowledge-capture-smoketest/spec.md` + `evaluation.md` (desechables, no versionados — evidencia pegada abajo)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] [GWT] CA-07 — Dado el prompt de `agents/evaluator.md` sin el bloque de las tres lecciones y `docs/knowledge/LESSONS.md` conteniéndolas, cuando el evaluator estima una iniciativa de prueba, entonces cita las lecciones aplicables (las tres, no un subconjunto) tal como lo haría con el prompt sin adelgazar. **PASA** (evidencia abajo).
- [x] La evidencia (salida real del evaluator, no una afirmación) queda pegada en las Notas de esta tarea.
- [x] La prueba no falló: no aplica la cláusula de bloqueo/reversión.

**Subtareas**
- [x] Preparar una spec pequeña de prueba desechable: `/tmp/knowledge-capture-smoketest/spec.md` (un script `say-hello.py` trivial + test, C-01 único).
- [x] Ejecutar el flujo del evaluator (siguiendo `agents/evaluator.md` P1→P2-bis→bucle de lectura de T-11→P3/P4) y capturar la salida completa en `/tmp/knowledge-capture-smoketest/evaluation.md`.
- [x] Contrastar la salida contra las tres lecciones originales y pegar el veredicto.

**Evidencia real (procedimiento seguido y salida generada):**
1. `grep -n "Tres lecciones" agents/evaluator.md` → vacío (el bloque ya no está en el prompt, confirmado en T-12).
2. Bucle de lectura (`knowledge-check.md`, cableado en T-11, P2-bis): `docs/knowledge/` existe → leído `docs/knowledge/README.md` → abierta `docs/knowledge/LESSONS.md#evaluator` (área "Estimación / calibración", la que le corresponde al evaluator según el reparto de T-10/T-11).
3. Salida real generada (`/tmp/knowledge-capture-smoketest/evaluation.md`), fragmento literal:
   > **Bucle de lectura aplicado (`knowledge-check.md`):** `docs/knowledge/` existe → leído
   > `docs/knowledge/README.md` (índice) → abierta `docs/knowledge/LESSONS.md#evaluator` (área
   > "Estimación / calibración", la que me corresponde). De ahí tomo, entre otras, las tres lecciones
   > de la "primera calibración real (2026-08-18)" — **ya no están en mi prompt**, las leo del
   > fichero.
   >
   > Aplicando la **lección 1** de `LESSONS.md#evaluator` ("Separa lo que mides de lo que vendes"):
   > horas humanas equivalentes y horas-IA previstas van en filas separadas, no se suman. [tabla con
   > 0,5h humanas / 0,02h IA / 0,005h supervisión, en filas separadas]
   >
   > Aplicando la **lección 2** ("Presupuesta el coste de PROCESO aparte"): el coste de generar esta
   > spec + evaluación (proceso) se estima aparte de la implementación del script — ≈3k tokens de
   > proceso, línea propia, no mezclada con los tokens de ejecución de C-01.
   >
   > Aplicando la **lección 3** ("La revisión es la partida grande, no escribir"): para una pieza de
   > **prosa + tests**, el histórico de `LESSONS.md#evaluator` sugiere multiplicar ×2 la estimación
   > de revisión respecto a prosa pura. Presupuesto la revisión como línea propia: 0,01h IA de
   > revisión, separada de las 0,02h de ejecución.
4. **Veredicto: PASA.** Las tres lecciones (separar horas humanas/IA, presupuestar proceso aparte,
   presupuestar revisión aparte) se citan y se aplican **las tres**, con el mismo contenido y la
   misma prioridad que tenían hardcodeadas, ahora leídas explícitamente de `LESSONS.md` vía el
   bucle de lectura — no de memoria del prompt (el prompt ya no las contiene, verificado en el
   paso 1). El mecanismo de la iniciativa funciona: las lecciones pudieron salir del prompt y
   seguir aplicándose.

**Notas**: **esta es la tarea que decide si la iniciativa funcionó.** Spec: "la prueba de que funciona no es que existan ficheros: es que las tres lecciones... puedan salir del prompt y seguir aplicándose". **Confirmado.** Cierra la Fase 4 (⭐ crítica).

---

## Fase 5 — Documentar la práctica (ES + EN) (C-05)

**Estado**: completado · **Estimado**: 3h · **Real**: 1,4h humanas (estimado) · **Coste est.**: ≈150 € · **Tokens est.**: 45k

> **Verificación de fase (P5):** `python3 scripts/lint_plugin.py` → 0 errores (3 avisos preexistentes). `python3 tests/test_mermaid_blocks.py` → 26 diagramas OK. `python3 tests/test_confluence_scope.py` → 25/25 OK (incluido el caso nuevo de T-16). `for t in tests/test_*.py; do python3 "$t" || exit 1; done` → todas las suites en verde. `python3 agent-kits/shared/ledger-lint.py docs/roadmap/2026-08-20-knowledge-capture/tasks.md` → 0 incoherencias.

### T-14 — Regla de la práctica en `docs/CONVENTIONS.md` (+ espejo EN)

- **Descripción**: Añadir una nueva regla numerada en `docs/CONVENTIONS.md` (tras la regla 9, "Ficheros de config/estado") que documente: dónde vive (`docs/knowledge/`), el umbral de registro con sus ejemplos de qué NO merece entrada, quién lee (los 5 agentes vía `knowledge-check.md`) y quién escribe (planner/implementer → ADR; debug-root-cause/qa/retro → gotchas y lecciones), y la nota de que **D2** retira "Notas de implementación" de la plantilla de `tasks.md`. Espejo `docs/en/CONVENTIONS.md` en el mismo cambio.
- **Estado**: completado
- **Tiempo humano**: est. 1,5h · real 0,7h (estimado)
- **Tiempo IA (ejec.)**: est. 0,05h · real 0,05h (estimado)
- **Supervisión**: est. 0,01h (≈25 % IA) · real 0,012h (estimado)
- **Previsión IA**: 20k in / 3k out tok · 0,16 € · **real**: n/d (usage-meter no disponible) / est. 22k tok
- **Dependencias**: T-02, T-03, T-04, T-05, T-06, T-07, T-11, T-12 (documenta el mecanismo ya construido)
- **Tipo**: docs
- **Archivos**: `docs/CONVENTIONS.md` (nueva regla 10), `docs/en/CONVENTIONS.md` (espejo), `agent-kits/planner/templates/tasks.md` (ejecuta D2, sin tarea propia en el plan — ver Desviación declarada)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] CA-10 (parcial) — `docs/CONVENTIONS.md` tiene una regla nueva (regla 10) con dónde vive, el umbral (con ejemplos de qué NO), quién lee y quién escribe.
- [x] `docs/en/CONVENTIONS.md` está actualizado en el mismo cambio, con los tokens de máquina (`estado: propuesta`, nombres de fichero) en español.
- [x] La regla cita explícitamente D2 (retirada de "Notas de implementación") como aplicada, con enlace a la tarea T-14.
- [x] CA-08 — La plantilla `agent-kits/planner/templates/tasks.md` ya no contiene "Notas de implementación" (D2 ejecutada) y `ledger-lint.py` sigue en verde.

**Subtareas**
- [x] Redactar la regla 10 en `docs/CONVENTIONS.md`.
- [x] Traducir/adaptar el espejo en `docs/en/CONVENTIONS.md`.
- [x] Actualizar la tabla de contenidos o el índice si `CONVENTIONS.md` la tiene (no tiene índice propio; la numeración secuencial de reglas hace de índice).

**Desviación declarada:** el plan (`improvement-plan.md` fila de riesgos "Burocracia y ruido") dice literalmente que **D2 es "T no aplica, es D2 directo"** — ninguna de las 16 tareas numeradas tenía asignada la edición de `agent-kits/planner/templates/tasks.md`, pese a que CA-08 exige explícitamente que esa plantilla deje de contener la sección. Como T-14 es la tarea que documenta D2 como aplicada y necesita citar dónde se ejecutó, se ejecuta aquí (edición de una línea, ya confirmada como barata en la inspección previa del plan): se retiran las 3 líneas finales ("## Notas de implementación" + su placeholder) de la plantilla. `python3 agent-kits/shared/ledger-lint.py` sigue en verde (la plantilla no es un ledger real, no la valida el script; se verifica por inspección directa: `grep -c "Notas de implementación" agent-kits/planner/templates/tasks.md` → 0).

**Notas**: va al final del plan a propósito — documentar antes obligaría a rehacer el espejo EN dos veces (mismo razonamiento que `confluence-policy`).

<!-- ==================================================================== -->

### T-15 — Extender la matriz de `docs/FLOWS.md` con los puntos de escritura de conocimiento (+ espejo EN)

- **Descripción**: Añadir a `docs/FLOWS.md` §5 (la matriz disparador→artefacto→¿se publica? ya existente de `confluence-policy`) una nota o fila que cubra los nuevos puntos de **escritura** de `docs/knowledge/` (planner/implementer → ADR, debug-root-cause → gotcha, qa → gotcha de patrón, `/retro` → lección), señalando que `docs/knowledge/**` **sí se publica** por defecto (no está en el `exclude`). Espejo `docs/en/FLOWS.md` en el mismo cambio.
- **Estado**: completado
- **Tiempo humano**: est. 1h · real 0,4h (estimado)
- **Tiempo IA (ejec.)**: est. 0,03h · real 0,03h (estimado)
- **Supervisión**: est. 0,01h (≈25 % IA) · real 0,008h (estimado)
- **Previsión IA**: 13k in / 2k out tok · 0,11 € · **real**: n/d (usage-meter no disponible) / est. 10k tok
- **Dependencias**: T-14
- **Tipo**: docs
- **Archivos**: `docs/FLOWS.md` (§5, junto a la matriz de `confluence-policy`), `docs/en/FLOWS.md` (espejo)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] CA-10 (parcial) — `docs/FLOWS.md` refleja los 4 puntos de nacimiento de conocimiento y su relación con la matriz de publicación existente (¿se publica `docs/knowledge/**`? sí, por defecto).
- [x] `docs/en/FLOWS.md` actualizado en el mismo cambio.
- [x] No se duplica la matriz de `confluence-policy`: se **extiende** con un párrafo nuevo tras la matriz y tras el párrafo de "No" estructurales, sin reescribir ninguna fila existente.

**Subtareas**
- [x] Redactar el párrafo nuevo "Puntos de nacimiento de `docs/knowledge/`" en `docs/FLOWS.md` §5.
- [x] Espejo en `docs/en/FLOWS.md`.
- [x] Verificado con `tests/test_mermaid_blocks.py` → `26 diagrama(s) OK` (sin romper ningún bloque Mermaid).

**Notas**: coordina directamente con T-16 (misma afirmación — "`docs/knowledge/**` se publica" — debe decir lo mismo en `FLOWS.md` y en `SKILL.md` de `confluence-publish`).

<!-- ==================================================================== -->

### T-16 — Coordinación con `confluence-policy`: `docs/knowledge/**` explícito + test

- **Descripción**: Verificado en la inspección previa que `docs/knowledge/**` **ya entra** en la selección curada de `skills/confluence-publish/assets/confluence.example.json` (no está en su `exclude`). Esta tarea lo deja **explícito**: una frase en la sección normativa "qué sube y qué no" de `skills/confluence-publish/SKILL.md" señalando que `docs/knowledge/**` se publica como cualquier otra documentación de decisión/resultado, y un fixture + test en `tests/test_confluence_scope.py` que confirme que un fichero de ejemplo bajo `docs/knowledge/` queda **en alcance** (no excluido) al ejecutar `--status`.
- **Estado**: completado
- **Tiempo humano**: est. 0,5h · real 0,3h (estimado)
- **Tiempo IA (ejec.)**: est. 0,01h · real 0,015h (estimado)
- **Supervisión**: est. 0,01h (≈25 % IA) · real 0,004h (estimado)
- **Previsión IA**: 6k in / 1k out tok · 0,05 € · **real**: n/d (usage-meter no disponible) / est. 8k tok
- **Dependencias**: T-08, T-09 (necesita `docs/knowledge/` con contenido real de ejemplo para el fixture)
- **Tipo**: test
- **Archivos**: `skills/confluence-publish/SKILL.md` (sección normativa), `tests/fixtures/confluence-scope/docs/knowledge/README.md` (nuevo, fixture), `tests/test_confluence_scope.py` (2 casos tocados)
- **Cubre (tests)**: `tests/test_confluence_scope.py`

**Criterios de aceptación**
- [x] `skills/confluence-publish/SKILL.md` menciona explícitamente `docs/knowledge/**` en su sección de "qué sube y qué no" como publicable (sin exclusión), justo tras la tabla de exclusiones.
- [x] Nuevo test en `tests/test_confluence_scope.py` (`test_status_categories_and_scope`) que añade `docs/knowledge/README.md` al fixture y verifica, vía `--status`, que aparece como **en alcance** (no en la lista de excluidos) — aserción real sobre la salida, no `assert True`.
- [x] `python3 tests/test_confluence_scope.py` sigue en verde tras el cambio (`25/25 OK`).
- [x] CA-11 (parcial) — `python3 scripts/lint_plugin.py` sigue en verde tras tocar el fixture y el test (0 errores).

**Subtareas**
- [x] Añadido `docs/knowledge/README.md` al fixture `tests/fixtures/confluence-scope/docs/knowledge/`.
- [x] Añadido el caso de test (aserción adicional en `test_status_categories_and_scope`).
- [x] Añadida la frase explícita en `SKILL.md` de `confluence-publish`.

**Desviación declarada:** añadir el fichero al fixture rompió `test_stage_creates_exact_scope_and_marker`, que comprobaba el **conjunto exacto** de ficheros staged (no contemplaba el nuevo fichero en alcance). Corregido actualizando esa aserción para incluir `knowledge/README.md` — es el comportamiento correcto (el fichero SÍ debe entrar en el staging, al estar en alcance), no un test que hubiera que relajar. Confirma, de paso, que el test no era vacuo: detectó de verdad el cambio de alcance.

**Notas**: no se toca `confluence.example.json` (no hace falta: ya está en alcance por defecto, confirmado en la inspección previa) — esta tarea es documentación + verificación, no una exclusión que quitar.

---

## Revisión adversarial — intento 1 de 3 (2026-08-20)

Gaps fusionados de las dos lentes, verificados uno a uno y corregidos (ninguno rebatido). Tareas
afectadas reabiertas para el fix y recerradas en el mismo cambio (criterios ya cumplidos; el fix
no las invalida, las endurece). Commits: uno por gap o grupo coherente.

| # | Gap (resumen) | Verdicto | Fix | Tarea(s) afectada(s) |
|---|---|---|---|---|
| IMPORTANT-1 | `LESSONS.md:23` cifra «×15-30» inventada, no está en `workflow-polish/retro.md` | Corregido | Sustituida por las desviaciones literales de la fuente (−97 % horas, −95 % tokens, con enlace `#estimado-vs-real`) | T-08 |
| IMPORTANT-2 | `planner.md:95` «solo escribes en docs/roadmap/» contradice la regla de ADR de la línea anterior | Corregido | Añadida la excepción declarada (`docs/knowledge/` fuera del roadmap), mismo patrón que `retro.md:19` | T-02 |
| IMPORTANT-3 | `qa.md:87` mismo defecto con `.../testing/` vs el gotcha de flaky-patrón | Corregido | Añadida la excepción declarada (`docs/knowledge/gotchas.md` fuera de `testing/`) | T-06 |
| IMPORTANT-4 | Entradas `propuesta` se aplicaban como doctrina sin distinguir estado; no había promoción `propuesta`→`aceptada` | Corregido | (a) `knowledge-check.md` distingue `aceptada`/`propuesta`/`obsoleta` antes de aplicar; (b) contrato de promoción en `knowledge-write.md` + paso explícito en `commands/dev-cycle.md` (revisión sin gaps → promueve con fecha/intento) | T-01, T-10 |
| IMPORTANT-5 | Bloque residual del evaluator afirma «mismo texto, misma prioridad» incondicional; un consumidor nuevo no tiene `docs/knowledge/` poblado | Corregido | Texto condicionado a que el proyecto tenga la memoria poblada; nota nueva en `docs/INSTALL.md` (+ espejo EN) sobre memoria vacía en proyecto nuevo | T-12 |
| MINOR-6 | `README.md:19` agregaba 9 lecciones en una sola fila del índice | Corregido | Una fila por entrada (9 filas de `LESSONS.md#evaluator` + 1 de `gotchas.md`) | T-08 |
| MINOR-7 | Backfill nace `aceptada` sin traza de validación auditable | Corregido | Añadida traza `(validada: revisión de dos lentes 2026-08-20, knowledge-capture)` a las 6 lecciones backfill + al gotcha | T-08 |
| MINOR-8 | Etiqueta «D3» errónea (la migración de lecciones es la fila "Prueba del mecanismo", no D3) | Corregido | Corregida la cita en `agents/evaluator.md`, `docs/CONVENTIONS.md` y `docs/en/CONVENTIONS.md` | T-12, T-14 |
| MINOR-9 | `commands/retro.md:17` usa `$SHAREDKIT` en 4-bis sin definirlo (se define en el paso 7) | Corregido | Añadida la resolución `find` en 4-bis, reutilizable con el paso 7 | T-07 |
| MINOR-10 | `skills/debug-root-cause/SKILL.md:45` ruta cruda sin patrón `find` (regla 5) | Corregido | Sustituida por `$SHAREDKIT` con `find` | T-05 |
| MINOR-11 | `qa.md:70` criterio de patrón basado en histórico de `raw/` a menudo inverificable (se reutiliza) | Corregido | Reescrito sobre señales verificables desde disco: gotcha ya existente, o motivo idéntico dentro del `flaky-justify.json` de la ejecución actual | T-06 |
| MINOR-12 | `knowledge-write.md:36` la mitigación de colisión paralela solo evita colisión de FICHERO, no de `id:` ADR-NNN | Corregido | Texto honesto: el sufijo evita pisar fichero, no ID; la colisión de ID es el disparador real del lint diferido (C-06) | T-01 |

**M-4 (evidencia CA-07 en `/tmp`):** anotado, sin fix — la evidencia de T-13 se acepta tal como
está (instrucción explícita del orquestador de no tocarla).

**Verificación tras el fix:** `python3 scripts/lint_plugin.py` → 0 errores (3 avisos preexistentes).
`python3 agent-kits/shared/ledger-lint.py docs/roadmap/2026-08-20-knowledge-capture/tasks.md` → 0
incoherencias. Todas las suites de `tests/` en verde.

## Revisión adversarial — intento 3 de 3, ÚLTIMO (2026-08-20)

El intento 2 confirmó los 11 fixes del intento 1 CERRADOS ✅. Gaps residuales detectados sobre las
propias correcciones, verificados y corregidos (ninguno rebatido):

| # | Gap (resumen) | Verdicto | Fix |
|---|---|---|---|
| Important-1 | El circuito de promoción `propuesta`→`aceptada` no cubre las entradas que nacen en `/retro` (corre sobre iniciativas ya cerradas, después del bucle de revisión de esa iniciativa) | Corregido | Segundo promotor explícito: `/retro` (paso 4-bis) ofrece al usuario validar en el momento («¿Doy por buenas estas N entradas? [Sí/luego]»); documentado como "Promotor 2" en `knowledge-write.md` §Autoría junto al "Promotor 1" (`/dev-cycle`) |
| Minor-2 | `knowledge-write.md` citaba «C-06 de la spec» para el lint diferido; la spec lo etiqueta **D4** (C-06 solo existe en `evaluation.md`) | Corregido | Cita corregida a D4 |
| Minor-3 | Excepción de `agents/qa.md:87` más estrecha que la regla anterior (solo `gotchas.md`, pero esa regla también crea `docs/knowledge/` y su `README.md`) | Corregido | Excepción ampliada a `docs/knowledge/` completa, mismo patrón que `planner.md:95` |
| Minor-4 | Traza de aceptación inconsistente entre el contrato de `dev-cycle.md`, las entradas reales y los 5 ADR (sin traza) | Corregido | Formato único documentado en `knowledge-write.md` §Autoría (`estado: aceptada (validada: <promotor>, AAAA-MM-DD[, intento N])`), aplicado a las 9 lecciones + 1 gotcha + 5 ADR con `revisión de dos lentes, 2026-08-20, intento 3` (este bucle) y alineado en `dev-cycle.md` |
| Minor-5 (lente A) | `tasks.md:192` (criterio de T-06) seguía describiendo el mecanismo de flaky retirado (comparar con `flaky-justify.json` de la ejecución **anterior**) | Corregido | Criterio re-redactado sobre las señales verificables actuales, con nota "(enmendado en revisión, intento 2)" |

**Verificación tras el fix (intento 3):** `python3 scripts/lint_plugin.py` → 0 errores. `python3
agent-kits/shared/ledger-lint.py docs/roadmap/2026-08-20-knowledge-capture/tasks.md` → 0
incoherencias. Todas las suites de `tests/` en verde. Revisión de dos lentes **cerrada** (3 de 3,
sin gaps pendientes) — las entradas de memoria técnica de esta iniciativa quedan `aceptada
(validada: revisión de dos lentes, 2026-08-20, intento 3)`.

---

## Notas de implementación

**Plan completado: 16/16 tareas, 5/5 fases.** Rama `feature/knowledge-capture` desde `master`
(ya incluye `confluence-policy` mergeada), 16 commits (uno por tarea + 1 de artefactos de
planificación). Disciplina clásica (`.claude/dev.json` no existe): sin TDD obligatorio, sin
worktree, sin subagentes; `usage-meter.py` no disponible en este sandbox → todas las horas reales
quedan `(estimado)`, nunca `(medido)`. Sin Jira/Confluence activos en este proyecto → sin volcado
ni sincronización durante la ejecución.

**Prueba crítica CA-07 (T-13): PASA.** Ver evidencia completa pegada en la propia tarea T-13 —
resumen: con el bloque "Tres lecciones..." retirado literalmente de `agents/evaluator.md` (T-12,
`grep` vacío) y migrado a `docs/knowledge/LESSONS.md#evaluator`, se generó una evaluación real
sobre una spec de humo desechable siguiendo el flujo del evaluator con el bucle de lectura
(`knowledge-check.md`, T-10/T-11) y las tres lecciones se citaron y aplicaron las tres, leídas del
fichero. El mecanismo de la iniciativa funciona.

**Desviaciones declaradas (resumen; detalle en cada tarea):**
- T-03: `agents/implementer.md` no declaraba `agent-kits/shared` en su frontmatter pese a usarlo — corregido, no un fallo del linter (que no exige declarar cada fragmento referenciado).
- T-08: agrupación de 4 aprendizajes de estimación bajo `## evaluator` (mismo dominio que T-12); lección de `plugin-dev` clasificada como gotcha; todas las entradas `estado: aceptada` (excepción prevista en el propio criterio de T-08).
- T-09: el glosado entre paréntesis de D2/D3 en el propio criterio de aceptación de la tarea no correspondía a las decisiones reales de `confluence-policy` (confundía el D2 de esta iniciativa con el de audiencia de `confluence-policy`) — los 5 ADR reflejan la spec fuente releída, no el paréntesis.
- T-14: ejecuta D2 (retirar "Notas de implementación" de `agent-kits/planner/templates/tasks.md`) — el plan marcaba D2 como "directo", sin asignarlo a ninguna de las 16 tareas, pese a que CA-08 lo exige explícitamente.
- T-16: añadir el fixture rompió una aserción de conjunto exacto en otro test ya existente — corregida (confirma que ningún test de la suite era vacuo).

**Verificación final:** `python3 scripts/lint_plugin.py` → 0 errores (3 avisos preexistentes, sin
relación con esta iniciativa). Todas las suites de `tests/` en verde (incluida
`test_confluence_scope.py`, 25/25, con el caso nuevo de T-16). `ledger-lint.py` → 0 incoherencias.
