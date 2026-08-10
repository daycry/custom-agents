# 2026-08-10-qa-strict

> Evaluación y presupuesto del endurecimiento de qa y `/dev-cycle` con puertas deterministas (`qa-gate.py`, `ledger-lint.py`), Playwright estricto, puerta de cobertura criterios↔tests, hook de aviso sobre `tasks.md`, bucle acotado de corrección, revisión de dos lentes y bloques opt-in API/A11Y — soporta la decisión go/no-go y el orden de ejecución.

| | |
|---|---|
| **Fecha** | 2026-08-10 |
| **Estado** | completado |
| **Prioridad global** | Media 🟡 |
| **Solicitante** | jmano@mediapro.tv |
| **Spec** | [`spec.md`](spec.md) |
| **Plan** | [`improvement-plan.md`](improvement-plan.md) (2026-08-10) |
| **Características evaluadas** | 7 |

---

## Cuadro de mando

| Métrica | Total estimado | Confianza |
|--------|----------------|-----------|
| Esfuerzo humano | **22,8 h** (19,0 h base +20 %) | Alta |
| Tiempo IA (ejecución) | **6,7 h** (+ 1,7 h supervisión) | Media |
| Coste | **~1.174 €** | Alta (h) / Media (tokens ⚠️) |
| Tokens IA | **~1,69 M** (in 1,50 M / out 187 k) | Media |
| Multiplicador productividad | **×2,7** | — |
| Características | **7** | — |

---

## Resumen ejecutivo

La spec (redactada y confirmada con el usuario el 2026-08-10, segunda iteración sobre `2026-08-10-agent-best-practices`) pide convertir en **mecánicas** tres decisiones que hoy dependen de la prosa del LLM: el veredicto de qa (C-01/C-02/C-03), la coherencia del ledger `tasks.md` (C-04/C-05) y el bucle de corrección qa→implementer (C-06), más una ampliación opt-in de cobertura API/A11Y (C-07). El grueso son **dos scripts Python con tests** (análogos al linter de la iniciativa anterior, estimado allí en 5 h base) más cambios de config, workflow y plantillas. Se presupuestan **19,0 h base (22,8 h con margen), ~1.174 €** y ~1,69 M tokens. La evaluación soporta la decisión de **aprobar la iniciativa completa** y ejecutarla en cuatro tandas: deterministas (C-01/C-04) → cableado barato (C-02/C-05) → integración en qa y workflow (C-03/C-06) → opt-in (C-07).

---

## Requerimientos recibidos

Mapa del documento de origen a las características evaluadas.

| ID | Característica | Requisito origen (ref.) | ¿Claro? |
|----|---------------|-------------------------|---------|
| C-01 | `qa-gate.py` — veredicto determinista | spec §Características C-01 + §Configuración (umbral) + §Manejo de errores + §Pruebas | ✅ |
| C-02 | Playwright estricto | spec §Características C-02 + §Configuración (retries/trace/forbidOnly/timeout) | ✅ |
| C-03 | Puerta de cobertura criterios↔tests | spec §Características C-03 + §Manejo de errores (proyecto sin UI) | ✅ (ubicación qa-gate vs. auxiliar abierta, ver incógnitas) |
| C-04 | `ledger-lint.py` — validación del ledger | spec §Características C-04 + §Manejo de errores (formato legacy) + §Pruebas | ✅ |
| C-05 | Hook PostToolUse sobre `tasks.md` | spec §Características C-05 + §Configuración (modo aviso) + §Manejo de errores (sin python) | ✅ |
| C-06 | /dev-cycle: bucle acotado + doble lente | spec §Características C-06 + §Decisiones de diseño + §Manejo de errores (3.er rojo) | ✅ |
| C-07 | Bloques `API-xx` / `A11Y-xx` (opt-in) | spec §Características C-07 + §Decisiones de diseño + §Supuestos (axe-core) | ✅ |

**Ambigüedades / información que falta:**

- C-01: el **esquema exacto de `results.json`** del reporter JSON de Playwright (identificación del status `flaky` por reintentos) está verificado en doc según la spec, pero puede variar con la versión del runner; la propia spec prevé adaptarse al esquema real. Afecta poco al coste (fixtures propios), baja algo la confianza.
- C-03: la spec deja abierta la ubicación de la comprobación de cobertura («en `qa-gate.py` o script auxiliar del kit»); se presupuesta como módulo del mismo kit y la decisión se cierra en el plan.
- C-05: se asume la **variable de entorno estándar** de hooks de Claude Code para la ruta del fichero editado (declarado como supuesto en la spec); si el mecanismo real difiere, el filtro `*/tasks.md` se implementa distinto sin cambio material de coste.
- Recon: en esta copia de trabajo del repo no están presentes `agent-kits/qa/` ni `hooks/` (checkout parcial); las rutas de impacto se toman de la spec §Arquitectura y del histórico (`2026-07-09-qa-agent` creó ese kit). Verificar sobre el repo completo al planificar.

---

## Datos necesarios para una evaluación completa

- [x] **Requerimientos** completos y sin ambigüedades (tabla C-01…C-07 con detalle, parámetros con valores objetivo)
- [x] **Alcance** de cada característica acotado (sección «Alcance» con fuera-de-alcance explícito: TDD estricto, regresión visual, Lighthouse, Stop-hook duro, multi-navegador)
- [x] **Criterios de aceptación / éxito** por característica (sección «Pruebas»: fixtures de ambos scripts, CI, prueba manual del bucle y doble lente)
- [x] **Restricciones** (manejo de errores exhaustivo: ausencia de evidencia = rojo, hook nunca rompe la edición, legacy degradado a aviso)
- [x] **Dependencias externas** — solo `axe-core/playwright` (opt-in, con degradación a checklist manual prevista en la spec)
- [x] **Contexto técnico** disponible (patrón guardrail/worklog, kit shared y linter de la iniciativa anterior, resolución `find`, CI existente)
- [ ] **Tarifa/hora y supuestos de coste** confirmados — no existe `.claude/rates.json`; se usan los defaults de `agent-kits/shared/estimation-defaults.md` (declarados abajo). No bloquea: la spec ya lo asume.

---

## Supuestos económicos (ajustables)

**Coste = (horas × tarifa) + coste de tokens de IA.** Importes en **EUR**.

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | 50 €/h | Default compartido (no hay `.claude/rates.json`) |
| Modelo IA asumido | claude-opus-4-8 | Base de la previsión de tokens |
| Precio input | 13,80 € / 1M tokens | ⚠️ verificar — supuesto de trabajo: 15 USD/M × 0,92 |
| Precio output | 69,00 € / 1M tokens | ⚠️ verificar — supuesto de trabajo: 75 USD/M × 0,92 |
| Tipo de cambio | 1 USD = 0,92 € | Default |
| Ratio de supervisión | 25 % de las horas IA | Default |
| Margen de contingencia | 20 % | Sobre horas base (humanas e IA) |

**Calibración con el histórico del repo** (no existe `docs/roadmap/CALIBRATION.md`; se usan las evaluaciones cerradas como referencia): `2026-07-09-qa-agent` (agente qa completo + runner Playwright) = 21,6 h / ~1.087 €; `2026-07-09-nemesis-sca-iac` (integración trivy+hadolint) = 12 h / ~605 €; `2026-08-10-agent-best-practices` = 17,25 h base / 11 tareas, y dentro de ella el **linter con tests** — el análogo más cercano a C-01 y C-04 — se estimó en **5 h base**. Esta iniciativa contiene **dos** scripts de ese tipo (más acotados que el linter: sin grafo de dependencias) más config, hook, workflow y plantilla: el total base de 19,0 h queda entre la iniciativa de best-practices (mayoría prompts) y el agente qa completo, lo que es coherente con su mezcla de código nuevo con tests + ediciones de prompt/workflow.

---

## Evaluación por característica

### C-01 — `qa-gate.py` — veredicto determinista

- **Requisito origen**: spec §Características C-01 + §Configuración (exit 0 ⟺ 0 failed y 0 flaky-sin-justificar) + §Manejo de errores (results ausente/malformado = rojo; justificación no vacía)
- **Descripción**: script en `agent-kits/qa/` que parsea `results.json` de Playwright, cuenta passed/failed/flaky/skipped, aplica el umbral con justificaciones de flaky por argumento/fichero y devuelve exit 0/1 + resumen JSON. qa lo invoca en su DoD; `/dev-cycle` usa el exit code como puerta.
- **Complejidad**: Media
- **Esfuerzo**: 3,5 h · confianza Alta (análogo directo del linter de la iniciativa anterior, 5 h base, con alcance menor: sin grafo ni frontmatter; incluye los 6 fixtures de §Pruebas y `tests/test_qa_gate.py`)
- **Previsión IA**: 300 k in / 45 k out tok · ~7,2 €
- **Coste**: (3,5 h × 50 €) + tokens = **182 €**
- **Impacto / áreas afectadas**: `agent-kits/qa/` (script nuevo), `agents/qa.md` (DoD invoca el gate y pega la salida como evidencia), `tests/test_qa_gate.py`, `.github/workflows/ci.yml`
- **Dependencias y prerequisitos**: el desarrollo es independiente (fixtures propios), pero el status `flaky` en producción solo aparece con `retries: 2` (C-02); C-06 consume su exit code
- **Riesgos**: divergencia del esquema `results.json` entre versiones de Playwright (la spec ya prevé adaptarse); diseño del canal de justificaciones (argumento vs. fichero) puede iterarse una vez
- **Incógnitas / preguntas abiertas**: formato exacto del fichero de justificaciones de flaky (a cerrar en el plan); versión del reporter JSON que fija el runner del kit

### C-02 — Playwright estricto

- **Requisito origen**: spec §Características C-02 + §Configuración (retries 2, forbidOnly true, trace retain-on-failure, timeout 30 s explícito, reporter JSON garantizado)
- **Descripción**: endurecer `agent-kits/qa/runner/playwright.config.mjs` para que el flaky quede identificado en `results.json` (insumo de C-01), con traza en fallo y sin `test.only` accidental.
- **Complejidad**: Baja (cambio de configuración sobre fichero existente)
- **Esfuerzo**: 1,0 h · confianza Alta (incluye una ejecución de humo del runner para verificar el `results.json` resultante)
- **Previsión IA**: 60 k in / 5 k out tok · ~1,2 €
- **Coste**: (1,0 h × 50 €) + tokens = **51 €**
- **Impacto / áreas afectadas**: `agent-kits/qa/runner/playwright.config.mjs`
- **Dependencias y prerequisitos**: ninguna; conviene cerrarlo junto a C-01 para validar el esquema flaky real
- **Riesgos**: `retries: 2` alarga la ejecución en suites con fallos reales (cada fallo se reintenta 2 veces); asumido por diseño
- **Incógnitas / preguntas abiertas**: ninguna relevante para el coste

### C-03 — Puerta de cobertura criterios↔tests

- **Requisito origen**: spec §Características C-03 + §Manejo de errores (proyecto sin tareas de UI → no aplica y se declara)
- **Descripción**: qa valida antes de ejecutar que cada criterio de aceptación de las tareas de UI de `tasks.md` esté cubierto por un `E2E-xx`/`M-xx` (campo «Cubre (tests)» del planner); los criterios huérfanos se listan en `report.md` y vetan el verde. Comprobación en `qa-gate.py` o script auxiliar del kit.
- **Complejidad**: Media
- **Esfuerzo**: 2,75 h · confianza Media (parsing de `tasks.md`/test-plan + integración en el flujo P1 de qa; reutiliza infraestructura de C-01 y el parseo de ledger de C-04)
- **Previsión IA**: 220 k in / 25 k out tok · ~4,8 €
- **Coste**: (2,75 h × 50 €) + tokens = **142 €**
- **Impacto / áreas afectadas**: `agent-kits/qa/` (módulo de cobertura), `agents/qa.md` (puerta previa a la ejecución), plantilla de informe del kit
- **Dependencias y prerequisitos**: requiere C-01 (si se integra en el gate) y que los planes traigan el campo «Cubre (tests)» del planner; C-04 aporta el parseo de `tasks.md`
- **Riesgos**: planes legacy sin campo «Cubre (tests)» generarían huérfanos masivos — hay que degradar con criterio (mismo espíritu que el modo legacy de C-04); matching criterio↔test es textual y puede necesitar convención estricta de IDs
- **Incógnitas / preguntas abiertas**: ¿gate integrado o script auxiliar? (spec lo deja abierto); tratamiento exacto de planes anteriores al campo «Cubre (tests)»

### C-04 — `ledger-lint.py` — validación mecánica del ledger

- **Requisito origen**: spec §Características C-04 + §Manejo de errores (legacy degradado a aviso; exit 1 solo para incoherencias duras) + §Pruebas
- **Descripción**: script en `agent-kits/shared/` que valida `tasks.md`: vocabulario de estados, coherencia checkbox↔estado (completado ⟹ criterios `[x]`), tabla resumen coherente con contadores por fase, IDs `T-XX` únicos. Exit 0/1 + informe. Lo consumen implementer (DoD), qa (P1) y `/dev-cycle` (cada puerta).
- **Complejidad**: Media
- **Esfuerzo**: 4,0 h · confianza Alta (mismo análogo de 5 h del linter; más reglas que C-01 —cuatro familias de validación + modo legacy— y tres puntos de integración en prompts; incluye los 5 fixtures de §Pruebas y `tests/test_ledger_lint.py`)
- **Previsión IA**: 340 k in / 50 k out tok · ~8,1 €
- **Coste**: (4,0 h × 50 €) + tokens = **208 €**
- **Impacto / áreas afectadas**: `agent-kits/shared/ledger-lint.py`, `agents/implementer.md` (DoD), `agents/qa.md` (P1), `commands/dev-cycle.md` (puertas), `tests/test_ledger_lint.py`, `.github/workflows/ci.yml`
- **Dependencias y prerequisitos**: ninguna dura; C-05 y C-06 lo consumen, así que va primero
- **Riesgos**: el formato real de `tasks.md` en iniciativas pasadas tiene variantes (legacy) — calibrar qué es aviso y qué es error duro es la parte fina; falsos positivos harían que los agentes ignoren el lint
- **Incógnitas / preguntas abiertas**: inventario de variantes legacy de `tasks.md` en el repo real (esta copia es parcial); ¿el vocabulario de estados se lee de `docs/CONVENTIONS.md` o va embebido?

### C-05 — Hook PostToolUse sobre `tasks.md`

- **Requisito origen**: spec §Características C-05 + §Configuración (modo aviso, exit 0 siempre) + §Manejo de errores (sin python3 → silencio)
- **Descripción**: entrada en `hooks/hooks.json` (matcher Write|Edit sobre `*/tasks.md`) que ejecuta `ledger-lint.py` en modo aviso vía script envoltorio: imprime problemas sin bloquear, ocurre siempre sin depender del prompt.
- **Complejidad**: Baja
- **Esfuerzo**: 1,25 h · confianza Alta (patrón ya existente: el plugin trae un hook PostToolUse para Confluence; el envoltorio son ~20 líneas con guard de `command -v python3`)
- **Previsión IA**: 100 k in / 10 k out tok · ~2,1 €
- **Coste**: (1,25 h × 50 €) + tokens = **65 €**
- **Impacto / áreas afectadas**: `hooks/hooks.json`, script del hook (junto al existente), resolución `find` de `ledger-lint.py`
- **Dependencias y prerequisitos**: requiere C-04
- **Riesgos**: el supuesto de la variable de entorno con la ruta editada (declarado en la spec); si el hook corre en scope plugin, la resolución del script compartido debe funcionar vía `find` en `$HOME/.claude`
- **Incógnitas / preguntas abiertas**: mecanismo exacto de paso de la ruta al hook (verificar contra la doc de hooks vigente en el plan)

### C-06 — /dev-cycle: bucle acotado + doble lente

- **Requisito origen**: spec §Características C-06 + §Decisiones de diseño (máx. 3 intentos; dos lentes en paralelo) + §Manejo de errores (3.er rojo → parar y preguntar)
- **Descripción**: (a) bucle qa→implementer con contador explícito y corte al 3.er rojo con resumen de fallos persistentes y decisión del usuario; (b) la revisión adversarial pasa a dos subagentes en paralelo (conformidad con spec/plan · calidad/robustez), fusión de gaps con dedupe y misma puerta manual. Solo en Modo B (cadena nativa; superpowers trae las suyas).
- **Complejidad**: Media
- **Esfuerzo**: 3,0 h · confianza Media (análogo a la revisión adversarial de la iniciativa anterior, 2,5 h, más el bucle con contador; incluye la prueba manual de §Pruebas simulando 3 rojos sobre iniciativa de juguete)
- **Previsión IA**: 220 k in / 22 k out tok · ~4,6 €
- **Coste**: (3,0 h × 50 €) + tokens = **155 €**
- **Impacto / áreas afectadas**: `commands/dev-cycle.md` (máquina de estados del ciclo: contador, corte, doble lente, fusión), `docs/FLOWS.md`
- **Dependencias y prerequisitos**: consume el exit code de C-01 y el lint de C-04 en las puertas → después de ambos
- **Riesgos**: la validación es empírica (comportamiento del orquestador): el corte al 3.er intento y el dedupe de gaps pueden requerir 1-2 iteraciones de prompt; coordinar con la rama superpowers para no duplicar revisión
- **Incógnitas / preguntas abiertas**: criterio de dedupe de gaps entre lentes (¿por fichero+síntoma?); qué contexto mínimo recibe cada lente para no encarecer la invocación

### C-07 — Bloques `API-xx` / `A11Y-xx` (opt-in)

- **Requisito origen**: spec §Características C-07 + §Decisiones de diseño (opt-in en test-plan) + §Supuestos (axe-core instalable con el flujo opt-in de Playwright; si no, checklist manual)
- **Descripción**: secciones opcionales en la plantilla `test-plan.md` del planner: `API-xx` (smoke de endpoints con curl: método, URL relativa, status esperado, aserción simple) y `A11Y-xx` (axe-core vía Playwright sobre páginas clave). qa los ejecuta solo si el test-plan los trae.
- **Complejidad**: Media-Alta (dos tipos de bloque nuevos con semántica de ejecución distinta —curl vs. axe/Playwright— más plantilla, instrucciones en dos agentes y flujo de instalación opt-in)
- **Esfuerzo**: 3,5 h · confianza Media
- **Previsión IA**: 260 k in / 30 k out tok · ~5,7 €
- **Coste**: (3,5 h × 50 €) + tokens = **181 €**
- **Impacto / áreas afectadas**: `agent-kits/planner/templates/test-plan.md` (secciones opcionales), `agents/qa.md` (ejecución condicional + evidencias), `agent-kits/qa/` (soporte axe-core en el runner), `agents/planner.md` (cuándo proponer los bloques)
- **Dependencias y prerequisitos**: independiente del resto (por eso puede ir la última); guardrail local de qa aplica también a los curl de `API-xx`
- **Riesgos**: `axe-core/playwright` puede no encajar en el flujo opt-in previsto (la spec ya degrada a checklist manual); los smoke API contra servicios locales requieren que el entorno esté levantado — definir el comportamiento cuando no lo está
- **Incógnitas / preguntas abiertas**: ¿los resultados API/A11Y entran en el umbral de `qa-gate.py` o solo en el informe? (a decidir en el plan); versión/compatibilidad de axe-core con el Playwright del runner

---

## Comparativa

Ordenada por la secuencia recomendada (deterministas primero).

| # | Característica | Complejidad | Horas | Coste € | Tokens | Prioridad | Confianza |
|---|---------------|-------------|-------|---------|--------|-----------|-----------|
| C-01 | qa-gate.py (veredicto determinista) | Media | 3,5 h | 182 € | 345 k | Alta | Alta |
| C-04 | ledger-lint.py (ledger mecánico) | Media | 4,0 h | 208 € | 390 k | Alta | Alta |
| C-02 | Playwright estricto | Baja | 1,0 h | 51 € | 65 k | Alta | Alta |
| C-05 | Hook PostToolUse tasks.md | Baja | 1,25 h | 65 € | 110 k | Media | Alta |
| C-03 | Puerta cobertura criterios↔tests | Media | 2,75 h | 142 € | 245 k | Media | Media |
| C-06 | Bucle acotado + doble lente | Media | 3,0 h | 155 € | 242 k | Media | Media |
| C-07 | Bloques API-xx / A11Y-xx (opt-in) | Media-Alta | 3,5 h | 181 € | 290 k | Baja | Media |
| | **Total (base, sin margen)** | | **19,0 h** | **984 €** | **~1,69 M** | | |

---

## Presupuesto total

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 19,0 h × 50 €/h | 950,00 € |
| Margen de contingencia | +20 % sobre desarrollo base | 190,00 € |
| Tokens IA (input) | 1,50 M tok × 13,80 €/M ⚠️ | 20,70 € |
| Tokens IA (output) | 187 k tok × 69,00 €/M ⚠️ | 12,90 € |
| **Total estimado (con margen)** | | **~1.174 €** |

> ⚠️ El coste de tokens (~34 €, un 3 % del total) usa precios **supuestos** pendientes de verificar; una desviación del ±50 % en la tarifa de tokens mueve el total menos de un 2 %.

---

## Productividad IA (humano vs. IA)

Compara el esfuerzo **humano** estimado con el tiempo que tardaría un **agente de IA** en implementarlo (más la supervisión humana).

| KPI | Valor |
|-----|-------|
| Horas humanas estimadas | 22,8 h *(19,0 h base)* |
| Horas IA (ejecución) | 6,7 h *(5,6 h base; supuesto)* |
| Supervisión humana | 1,7 h *(25 % de las horas IA)* |
| **Horas totales (IA + supervisión)** | **8,4 h** |
| Horas ahorradas | 14,4 h |
| **Ahorro** | **63 %** |
| **Multiplicador de productividad** | **×2,7** |
| FTE equivalentes *(opcional)* | ~0,09 |

> Horas mostradas **con el margen de contingencia (+20 %)** ya aplicado sobre las horas base (humanas e IA). El trabajo determinista (scripts + fixtures, C-01/C-04) es muy agente-friendly; la supervisión se concentra en lo empírico (C-06: comportamiento del bucle y las lentes; C-03: criterio de degradación legacy).

---

## Recomendación

- **Veredicto**: **go** — coste contenido (~1.174 €), riesgo bajo (patrón guardrail-por-script ya probado en el plugin, manejo de errores exhaustivo en la spec) y ataca la causa raíz: los tres puntos donde hoy el ciclo depende de que el LLM siga la prosa.
- **Quick wins** (bajo coste, alto valor): **C-02 y C-05** — 2,25 h base / 116 € en total; C-02 además habilita la detección de flaky que da sentido al umbral de C-01.
- **Costosas / a valorar**: **C-04** (4 h, la mayor: calibrar aviso vs. error duro sobre ledgers legacy) y **C-07** (3,5 h y prioridad Baja: es opt-in y no bloquea el objetivo central; sería la primera candidata a recortar si se quiere ajustar presupuesto).
- **Orden sugerido**: **C-01 → C-04** (las dos puertas deterministas, corazón de la iniciativa y sin dependencias) → **C-02 → C-05** (cableado barato que las alimenta: flaky en `results.json`, lint en cada edición) → **C-03 → C-06** (integración en qa y en el workflow: consumen los gates ya construidos) → **C-07** al final, por ser opt-in e independiente.
- **Fuera de alcance recomendado**: mantener lo que la spec ya excluye (TDD estricto en implementer, regresión visual, Lighthouse, Stop-hook en modo bloqueo, navegadores más allá de Chromium).

---

## Riesgos transversales

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Falsos positivos de los gates (esquema `results.json` distinto, ledgers legacy) → los agentes aprenden a ignorarlos | Media | Alto | Fixtures contra el esquema real de la versión fijada; modo legacy degradado a aviso (ya en spec §Manejo de errores); rodar C-05 en aviso antes de plantear bloqueo |
| Endurecer el verde frena ciclos hoy «válidos» (flaky sin justificar, criterios huérfanos) y añade fricción | Media | Medio | La justificación escrita de flaky y el corte al 3.er intento con decisión humana están diseñados exactamente para eso: fricción visible, no bloqueo ciego |
| Supuestos de plataforma (env var del hook, esquema flaky del reporter, axe-core opt-in) no se cumplen tal cual | Media | Medio | Los tres están declarados en spec §Supuestos con degradación prevista; verificarlos en la primera tarea del plan (spike corto) |
| Doble lente duplica coste de tokens por ciclo de revisión | Media | Bajo | Contexto mínimo por lente (diff + artefacto de referencia); dedupe de gaps antes de la puerta manual |
| Recon parcial: `agent-kits/qa/` y `hooks/` no visibles en esta copia de trabajo | Baja | Bajo | Existen según el histórico (`2026-07-09-qa-agent`) y la spec; el planner los verifica sobre el repo completo |

---

## Siguiente paso

Para **ejecutar** lo aprobado, genera el plan detallado con el agente **`planner`** (creará `improvement-plan.md` + `tasks.md` en esta misma carpeta `docs/roadmap/2026-08-10-qa-strict/`, y rellenará el campo **Plan** de esta evaluación y el `plan:` de la spec). Indica qué características se aprueban para planificar; la recomendación es **las 7, en el orden sugerido** (C-01→C-04 → C-02→C-05 → C-03→C-06 → C-07). Requisitos de secuencia para el plan: C-04 antes que C-05 y C-06 (lo consumen); C-01 antes que C-03 y C-06; C-07 en último lugar por ser opt-in e independiente. La aprobación de esta evaluación (go) implica pasar la spec a `aprobada` y esta evaluación a `completado`.

---

## Changelog

| Fecha | Cambio |
|-------|--------|
| 2026-08-10 | Evaluación inicial de C-01…C-07 sobre spec confirmada con el usuario; estado `en-revision` a la espera de go/no-go |
