# 2026-08-10-qa-strict

> Endurecer `qa` y `/dev-cycle` con puertas deterministas: `qa-gate.py` (veredicto por exit code), `ledger-lint.py` (coherencia mecánica de `tasks.md`), Playwright estricto con detección de flaky, puerta de cobertura criterios↔tests, hook de aviso sobre el ledger, bucle de corrección acotado a 3 intentos, revisión de dos lentes y bloques opt-in `API-xx`/`A11Y-xx`.

| | |
|---|---|
| **Fecha** | 2026-08-10 |
| **Estado** | borrador |
| **Tipo** | Infra (tooling del plugin: scripts, hooks, prompts y plantillas) |
| **Prioridad** | Media |
| **Solicitante** | daycry |
| **Responsable** | `implementer` (agente) · supervisión: daycry |
| **Spec** | [`spec.md`](spec.md) |
| **Evaluación** | [`evaluation.md`](evaluation.md) |

---

## Cuadro de mando

| Métrica | Estimado | Real | Confianza |
|--------|---------|------|-----------|
| Tiempo humano | **23,4 h** (19,5 h base +20 %) | 0 h | Alta |
| Tiempo IA (ejecución) | **7,0 h** (+ 1,7 h supervisión) | 0 h | Media |
| Coste total | **~1.205 €** | 0 € | Alta (h) / Media (tokens ⚠️) |
| Tokens IA | **~1,73 M** (in 1,54 M / out 193 k) | 0 | Media |
| Multiplicador productividad | **×2,7** | — | — |
| Tareas | **8** | 0 hechas | — |

> **Herencia de presupuesto.** Las horas de C-01…C-07 se **heredan de [`evaluation.md`](evaluation.md) sin re-estimar** (19,0 h base / 22,8 h con margen / ~1.174 € / ~1,69 M tokens). El plan añade **una tarea de cierre (T-08) como delta explícito: +0,5 h base (+0,6 h con margen), +46 k tokens, +~31 €**, que lleva el total a 19,5 h base / 23,4 h con margen / ~1.205 €.

---

## Estimación por fase

Horas y costes **base** (el margen de contingencia se aplica en el desglose global).

| Fase | Estimado (h) | Tokens (in / out) | Coste € |
|------|-------------|-------------------|---------|
| Fase 1 — Puertas deterministas (C-01, C-04) | 7,5 | 640 k / 95 k | 390 |
| Fase 2 — Cableado (C-02, C-05) | 2,25 | 160 k / 15 k | 116 |
| Fase 3 — Integración (C-03, C-06, C-07) | 9,25 | 700 k / 77 k | 478 |
| Fase 4 — Cierre (delta explícito) | 0,5 | 40 k / 6 k | 26 |
| **Total (base)** | **19,5 h** | **1,54 M / 193 k** | **1.010 €** |

---

## Presupuesto económico

**Coste = (horas × tarifa) + coste de tokens de IA.** Todos los importes en **EUR**.

### Supuestos (ajustables)

Heredados de la evaluación (no existe `.claude/rates.json`; defaults de `agent-kits/shared/estimation-defaults.md`).

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | 50 €/h | Default compartido |
| Modelo IA asumido | claude-opus-4-8 | Modelo previsto para la ejecución |
| Precio input | 13,80 € / 1M tokens | ⚠️ verificar — supuesto de trabajo: 15 USD/M × 0,92 |
| Precio output | 69,00 € / 1M tokens | ⚠️ verificar — supuesto de trabajo: 75 USD/M × 0,92 |
| Tipo de cambio | 1 USD = 0,92 € | Default |
| Margen de contingencia | 20 % | Sobre horas base (humanas e IA) |

### Desglose

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 19,5 h × 50 €/h | 975,00 € |
| Margen de contingencia | +20 % sobre desarrollo base | 195,00 € |
| Tokens IA (input) | 1,54 M tok × 13,80 €/M ⚠️ | 21,25 € |
| Tokens IA (output) | 193 k tok × 69,00 €/M ⚠️ | 13,32 € |
| **Total estimado (con margen)** | | **~1.205 €** |

> Herencia: ~1.174 € de la evaluación + ~31 € del delta de cierre (T-08). El coste de tokens (~35 €, un 3 % del total) usa precios **supuestos** pendientes de verificar; una desviación del ±50 % en la tarifa de tokens mueve el total menos de un 2 %.

---

## Previsión de tokens (por fase)

Base: claude-opus-4-8 · precios de la tabla de supuestos.

| Fase | Input (tok) | Output (tok) | Total (tok) | Coste € |
|------|------------|-------------|-------------|---------|
| Fase 1 — Puertas deterministas | 640 k | 95 k | 735 k | 15,39 |
| Fase 2 — Cableado | 160 k | 15 k | 175 k | 3,24 |
| Fase 3 — Integración | 700 k | 77 k | 777 k | 14,97 |
| Fase 4 — Cierre | 40 k | 6 k | 46 k | 0,97 |
| **Total** | **1,54 M** | **193 k** | **~1,73 M** | **34,57 €** |

**Método de estimación:** heredado de la evaluación por característica (lectura de los kits/prompts afectados × tamaño medio + generación de scripts, fixtures y tests; lo empírico —C-06— pondera iteraciones de prompt). El delta de la Fase 4 se estima igual (lectura de CHANGELOG/CONVENTIONS/FLOWS/ci.yml + ediciones cortas).

---

## Productividad IA (humano vs. IA)

| KPI | Valor |
|-----|-------|
| Horas humanas estimadas | 23,4 h *(19,5 h base)* |
| Horas IA (ejecución) | 7,0 h *(5,8 h base; supuesto)* |
| Supervisión humana | 1,7 h *(25 % de las horas IA)* |
| **Horas totales (IA + supervisión)** | **8,7 h** |
| Horas ahorradas | 14,7 h |
| **Ahorro** | **63 %** |
| **Multiplicador de productividad** | **×2,7** |
| FTE equivalentes *(opcional)* | ~0,09 |

> Horas mostradas **con el margen de contingencia (+20 %)** ya aplicado sobre las horas base (humanas e IA). El trabajo determinista (scripts + fixtures, T-01/T-02) es muy agente-friendly; la supervisión se concentra en lo empírico (T-06: comportamiento del bucle y las lentes; T-05: criterio de degradación legacy).

---

## Resumen ejecutivo

Hoy el veredicto de `qa`, la coherencia del ledger `tasks.md` y el bucle de corrección qa→implementer dependen de que el LLM siga la prosa. Este plan mueve esas tres decisiones a **código determinista con exit code** (patrón `lib-guardrail.sh`/`worklog.py`): dos scripts Python con tests (`qa-gate.py`, `ledger-lint.py`), configuración estricta de Playwright, un hook de aviso sobre `tasks.md`, un bucle de corrección acotado a 3 intentos con corte humano, revisión adversarial de dos lentes en `/dev-cycle` y bloques opt-in `API-xx`/`A11Y-xx` en el test-plan. Cuatro fases en el orden de la evaluación: deterministas → cableado → integración → cierre.

### Objetivos

- El verde/rojo de `qa` lo decide `qa-gate.py` (exit 0 ⟺ 0 failed y 0 flaky sin justificar), no la prosa: veredicto reproducible con evidencia pegable.
- Toda incoherencia dura de `tasks.md` (estado inválido, `completado` sin criterios `[x]`, resumen descuadrado, IDs duplicados) la detecta `ledger-lint.py` y la avisa un hook en cada edición.
- Ningún ciclo qa→implementer supera los 3 intentos sin decisión humana explícita.
- La cobertura criterios↔tests y la revisión de dos lentes quedan integradas en `qa` y `/dev-cycle`; API/A11Y disponibles como opt-in sin imponer dependencias.

---

## Datos necesarios para un informe completo

- [x] **Requisitos funcionales** confirmados por el solicitante (spec `aprobada`, decisiones confirmadas 2026-08-10)
- [x] **Alcance** cerrado (spec §Alcance con fuera-de-alcance explícito: TDD estricto, regresión visual, Lighthouse, Stop-hook duro, multi-navegador)
- [x] **Criterios de éxito / métricas** acordados (spec §Pruebas + criterios por tarea en `tasks.md`)
- [x] **Accesos y credenciales** — no aplican: todo es local al repo del plugin
- [x] **Entornos** disponibles — repo + python3 + runner Playwright del kit `qa` (opt-in ya existente)
- [x] **Stakeholders** identificados (solicitante = validador de las puertas manuales)
- [x] **Dependencias externas** mapeadas — solo `axe-core/playwright` (opt-in, con degradación a checklist manual prevista)
- [x] **Restricciones** conocidas (spec §Manejo de errores: ausencia de evidencia = rojo, hook nunca rompe la edición, legacy degradado a aviso)
- [ ] **Tarifa/hora y supuestos de coste** confirmados — no existe `.claude/rates.json`; se usan los defaults compartidos declarados arriba. No bloquea (la evaluación ya lo asume); `/setup` puede fijarlos cuando se quiera.

---

## Análisis de impacto

Rutas verificadas en el repo (la duda de «checkout parcial» de la evaluación queda resuelta: `agent-kits/qa/` y `hooks/` existen).

- **`agent-kits/qa/`** — nuevo `qa-gate.py` (+ fixtures) y nuevo `coverage-check.py`; `runner/playwright.config.mjs` endurecido (`retries: 2`, `forbidOnly: true`, timeout explícito); `templates/report.md` gana la sección de criterios huérfanos.
- **`agent-kits/shared/`** — nuevo `ledger-lint.py` (+ fixtures), consumido por `implementer`, `qa`, `/dev-cycle` y el hook.
- **`agents/qa.md`** — la DoD pasa a invocar `qa-gate.py` y pegar su salida como evidencia; puerta de cobertura en P1; ejecución condicional de bloques `API-xx`/`A11Y-xx`.
- **`agents/implementer.md`** — la DoD invoca `ledger-lint.py` antes de dar una tarea por cerrada.
- **`agents/planner.md`** — cuándo proponer los bloques opt-in API/A11Y en el test-plan.
- **`commands/dev-cycle.md`** — bucle qa→implementer con contador (máx. 3) y revisión adversarial de dos lentes con fusión/dedupe (solo Modo B).
- **`hooks/hooks.json` + `hooks/lint-tasks-ledger.sh`** — nueva entrada PostToolUse sobre `*/tasks.md` en modo aviso, siguiendo el patrón de `mark-docs-pending.sh`.
- **`agent-kits/planner/templates/test-plan.md`** — secciones opcionales `API-xx`/`A11Y-xx`.
- **`tests/` + `.github/workflows/ci.yml`** — `test_qa_gate.py` y `test_ledger_lint.py` se suman a la batería existente.
- **`CHANGELOG.md`, `docs/CONVENTIONS.md`, `docs/FLOWS.md`** — registro del cambio y actualización de reglas/flujos.

---

## Cambios arquitectónicos

Decisiones que la spec/evaluación dejaban abiertas, **cerradas en este plan**:

- **Ubicación de la puerta de cobertura (C-03): script auxiliar `agent-kits/qa/coverage-check.py`**, no dentro de `qa-gate.py`. Separación de responsabilidades: el gate juzga **resultados de ejecución** (`results.json`, post-run); la cobertura es una **puerta estática previa** (tasks.md + test-plan.md, pre-run). Ambos comparten kit y convención de salida (exit code + resumen).
- **Canal de justificaciones de flaky (C-01): fichero JSON opcional** (`--justify <ruta>`, mapa `título del test → texto`), con la alternativa `--justify-inline` por argumento para casos puntuales. El gate exige **texto no vacío** por test justificado.
- **Vocabulario de estados embebido en `ledger-lint.py`** (los cinco de `docs/CONVENTIONS.md`), no leído en runtime: el script debe funcionar standalone (hook, CI) sin depender de rutas de docs.
- **Resultados API/A11Y fuera del umbral de `qa-gate.py` en v1 (C-07)**: un `API-xx`/`A11Y-xx` fallido se lista en `report.md` y **veta el verde** por la misma regla que los criterios huérfanos, sin complicar el contrato del gate. Se revisará cuando lleven rodaje.
- **Patrón guardrail-por-script** en todo lo nuevo: lo innegociable lo impone código con exit code; el LLM interpreta y comunica (mismo enfoque que `lib-guardrail.sh` y `worklog.py`).

---

## Archivos a crear/modificar

| Archivo | Acción | Propósito |
|---------|--------|-----------|
| `agent-kits/qa/qa-gate.py` | Crear | Veredicto determinista sobre `results.json` (exit 0/1 + resumen JSON) |
| `tests/test_qa_gate.py` (+ fixtures) | Crear | 6 escenarios de §Pruebas de la spec |
| `agent-kits/shared/ledger-lint.py` | Crear | Validación mecánica de `tasks.md` (exit 0/1 + informe; legacy → aviso) |
| `tests/test_ledger_lint.py` (+ fixtures) | Crear | 5 escenarios de §Pruebas de la spec |
| `agent-kits/qa/runner/playwright.config.mjs` | Modificar | `retries: 2`, `forbidOnly: true`, timeout explícito, trace/reporter garantizados |
| `hooks/lint-tasks-ledger.sh` | Crear | Envoltorio del hook: stdin JSON, jq con fallback grep, guard python3, exit 0 siempre |
| `hooks/hooks.json` | Modificar | Nueva entrada PostToolUse (Write\|Edit\|MultiEdit) sobre `*/tasks.md` |
| `agent-kits/qa/coverage-check.py` | Crear | Puerta de cobertura criterios↔tests (E2E-xx/M-xx vs. «Cubre (tests)») |
| `agent-kits/qa/templates/report.md` | Modificar | Sección de criterios huérfanos + evidencias API/A11Y |
| `agents/qa.md` | Modificar | DoD con qa-gate; puerta de cobertura en P1; bloques API/A11Y condicionales |
| `agents/implementer.md` | Modificar | DoD invoca ledger-lint antes de cerrar tarea |
| `agents/planner.md` | Modificar | Cuándo proponer bloques API/A11Y |
| `commands/dev-cycle.md` | Modificar | Bucle acotado (máx. 3) + doble lente + puertas con exit codes |
| `agent-kits/planner/templates/test-plan.md` | Modificar | Secciones opcionales `API-xx` / `A11Y-xx` |
| `.github/workflows/ci.yml` | Modificar | Añadir los dos tests nuevos a la batería |
| `CHANGELOG.md` | Modificar | Entrada de la iniciativa |
| `docs/CONVENTIONS.md` | Modificar | Reflejar las puertas deterministas en las reglas del ledger/DoD |
| `docs/FLOWS.md` | Modificar | Ciclo /dev-cycle con contador y doble lente |

---

## Dependencias y prerequisitos

- **T-02 (C-04, ledger-lint) antes que T-04 (C-05, hook) y T-06 (C-06, dev-cycle)** — ambos lo consumen.
- **T-01 (C-01, qa-gate) antes que T-05 (C-03, cobertura) y T-06 (C-06)** — comparten infraestructura/exit code.
- **T-03 (C-02, Playwright) conviene cerrarlo junto a T-01** para validar contra el esquema `flaky` real de `results.json`.
- **T-07 (C-07) es independiente** — por eso cierra la Fase 3; primera candidata a recorte si se ajusta presupuesto.
- **T-08 (cierre) depende de todas** las anteriores.
- Supuestos de plataforma a verificar al arrancar cada tarea (spike corto, ya previsto en la spec): esquema `flaky` del reporter JSON, payload stdin del hook PostToolUse, instalabilidad opt-in de `axe-core/playwright`.

---

## Criterios de aceptación (global)

- [ ] `python tests/test_qa_gate.py` y `python tests/test_ledger_lint.py` pasan en local y en CI, junto a la batería existente.
- [ ] `python scripts/lint_plugin.py` sigue en verde tras todos los cambios de frontmatter/hooks.
- [ ] `qa-gate.py` devuelve exit 1 con motivo «sin resultados» ante `results.json` ausente o malformado, y rechaza justificaciones de flaky con texto vacío.
- [ ] `ledger-lint.py` degrada el formato legacy a aviso (exit 0) y reserva exit 1 para incoherencias duras (estado inválido, `completado` sin criterios `[x]`).
- [ ] El hook sobre `tasks.md` termina **siempre** con exit 0 (modo aviso) y sale en silencio si no hay `python3`; ninguna edición se rompe.
- [ ] Prueba manual: `/dev-cycle` sobre iniciativa de juguete corta al 3.er rojo (resumen + decisión del usuario, sin cerrar estados) y la doble lente produce gaps fusionados sin duplicados.
- [ ] Cadena de artefactos coherente: spec `plan:` + callout, fila Plan de la evaluación y fila del índice del roadmap enlazando plan y tasks.

---

## Riesgos y mitigaciones

Heredados de la evaluación (§Riesgos transversales), con la mitigación aterrizada a tareas.

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Falsos positivos de los gates (esquema `results.json` distinto, ledgers legacy) → los agentes aprenden a ignorarlos | Media | Alto | Fixtures contra el esquema real de la versión fijada (T-01/T-03 juntos); modo legacy degradado a aviso (T-02); rodar el hook en aviso antes de plantear bloqueo |
| Endurecer el verde frena ciclos hoy «válidos» (flaky sin justificar, criterios huérfanos) | Media | Medio | Justificación escrita de flaky (T-01) y corte al 3.er intento con decisión humana (T-06): fricción visible, no bloqueo ciego |
| Supuestos de plataforma (payload del hook, esquema flaky, axe-core opt-in) no se cumplen tal cual | Media | Medio | Verificación como primera subtarea (spike) de T-01, T-04 y T-07; degradaciones ya previstas en la spec |
| Doble lente duplica coste de tokens por ciclo de revisión | Media | Bajo | Contexto mínimo por lente (diff + artefacto de referencia) y dedupe de gaps antes de la puerta manual (T-06) |
| Validación empírica de T-06 requiere iteraciones de prompt | Media | Bajo | Prueba manual guionizada (3 rojos simulados) incluida en la propia tarea |

---

## Métricas de éxito

- El veredicto de `qa` es **reproducible**: mismo `results.json` + mismas justificaciones ⟹ mismo exit code, y la salida del gate aparece pegada como evidencia en cada `report.md`.
- **0 cierres en verde** con failed > 0 o flaky sin justificación escrita tras el despliegue.
- Las incoherencias duras de `tasks.md` se detectan mecánicamente (hook/CI), no por lectura humana: incidencias de ledger descuadrado → 0 en las siguientes iniciativas.
- Ningún ciclo qa→implementer registrado con más de 3 intentos sin intervención del usuario.
- Desviación real vs. estimado del plan dentro del margen del 20 % (se medirá con `/roadmap-metrics` y `/retro`).

---

## Changelog del plan

| Fecha | Cambio | Autor |
|-------|--------|-------|
| 2026-08-10 | Creación del plan (presupuesto heredado de `evaluation.md` + delta T-08 de cierre) | planner |

---

## Siguiente paso

Con el **OK del plan** del usuario (puerta de control), el agente **`implementer`** lo ejecuta fase a fase sobre una rama, marcando [`tasks.md`](tasks.md) como **ledger canónico** (checkbox + estado por tarea). Al terminar, handoff a `qa` (sin `test-plan.md`: la validación es pytest + verificación manual de los criterios) y cierre con `documenter`. La **release** del plugin queda **a cargo del usuario** (T-08 la deja preparada, no la publica). Si se quiere volcar las tareas a Jira, la skill **`jira-sync`** está disponible **a petición**.

---

## Revisión adversarial de dos lentes (dogfooding de C-06 · 2026-08-10)

Se estrenó el propio mecanismo C-06b sobre esta implementación: **dos subagentes en paralelo con contexto fresco** (lente A: conformidad con spec/plan; lente B: calidad/robustez, ejecutando los scripts con inputs adversariales). Resultado tras fusión y dedupe — **todos corregidos y con test de regresión donde aplica**:

- **qa-gate.py (3 falsos verdes, severidad alta):** flaky declarados en `stats` pero no localizables en `suites` pasaban verdes → ahora cuentan como sin justificar; errores top-level del runner (`forbidOnly` violado, webserver caído) se ignoraban → ahora rojo; `interrupted`/tests sin ejecutar contaban como skipped → ahora rojo, y verde exige ≥1 test ejecutado. Además: títulos duplicados ya no se justifican con una sola entrada (clave `fichero::título`). Tests 9-13 añadidos (13/13).
- **ledger-lint.py (2 falsos negativos, 3 falsos rojos, 1 crash):** tabla de resumen con negritas no se validaba; checkbox `* [ ]` invisible; criterios como heading `####`; tarea tras sección no-fase atribuida a la fase anterior; estado con espacios («En Progreso») rechazado; no-UTF-8 rompía `--warn-only`. Todo corregido (8/8 + casos adversariales re-verificados).
- **coverage-check.py:** IDs definidos solo en tablas daban falso rojo; referencias en minúsculas degradaban error a aviso (falso verde); `tasks.md` sin tareas pasaba trivialmente → ahora error.
- **playwright.config.mjs:** `QA_TIMEOUT_MS` no numérico desactivaba el timeout (NaN) → saneado con fallback a 30 s.
- **Ledger y entregables:** sección de veredicto/cobertura/API-A11Y añadida a `templates/report.md`; nota de bloques opcionales en `planner.md`; plantilla `A11Y-example.spec.mjs` en el runner; dos afirmaciones infladas del ledger corregidas (`--justify-inline` descartado; axe-core on-demand).
- El hook `ledger-lint-warn.sh` salió **sin defectos** (probado con rutas con espacios, payloads MultiEdit, sin jq, sin match).

Cierre pendiente de **OK del usuario** → plan `completado`, spec `implementada`. Release (T-08) a cargo del usuario con `scripts/release.py`.
