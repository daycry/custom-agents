# Checklist de Tareas — qa estricto y orquestador endurecido (puertas deterministas)

| | |
|---|---|
| **Estado** | completado |
| **Fecha** | 2026-08-10 |
| **Plan** | [`improvement-plan.md`](./improvement-plan.md) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del plan. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador externo (p. ej. *superpowers SDD*)— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

---

## Resumen de progreso

Horas y tokens estimados en **base** (sin margen); el +20 % se aplica en el presupuesto global del plan. Presupuesto de T-01…T-07 **heredado de `evaluation.md`**; T-08 es delta explícito del plan.

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — Puertas deterministas | 2 | 2 | 100% | 0 / 7,5 h | 0 / 2,2 h | 0 / 0,55 h | 0 / 735 k |
| Fase 2 — Cableado | 2 | 2 | 100% | 0 / 2,25 h | 0 / 0,7 h | 0 / 0,2 h | 0 / 175 k |
| Fase 3 — Integración | 3 | 3 | 100% | 0 / 9,25 h | 0 / 2,7 h | 0 / 0,7 h | 0 / 777 k |
| Fase 4 — Cierre | 1 | 1 | 100% | 0 / 0,5 h | 0 / 0,2 h | 0 / 0,05 h | 0 / 46 k |
| **TOTAL** | **8** | **8** | **100%** | **0 / 19,5 h** | **0 / 5,8 h** | **0 / 1,5 h** | **0 / ~1,73 M** |

> **Horas → Jira.** El worklog que imputa `jira-sync` al completar cada tarea es **Tiempo IA (ejec.) + Supervisión** (real; o estimación si no hay real), topado a la jornada configurada. Ver `skills/jira-sync/SKILL.md`. `jira-sync` disponible **a petición**.


> **Estado:** implementado en la sesión Cowork 2026-08-10 (dogfooding: evaluator→planner→implementación→revisión de dos lentes). Pendiente de revisión del usuario para plan → `completado` y spec → `implementada`. La parte de release de T-08 (bump con `scripts/release.py` + push) la ejecuta el usuario. Horas reales no cronometradas por tarea (ejecución IA continua) → columnas `real` en 0/—.

---

## Fase 1 — Puertas deterministas (C-01, C-04)

**Estado**: completado · **Estimado**: 7,5 h · **Real**: — · **Coste est.**: 390 € · **Tokens est.**: 735 k

### T-01 — `qa-gate.py`: veredicto determinista de qa (C-01)

- **Descripción**: Crear `agent-kits/qa/qa-gate.py`: parsea el `results.json` del reporter JSON de Playwright, cuenta passed/failed/flaky/skipped, aplica el umbral (exit 0 ⟺ 0 failed y 0 flaky sin justificar) con justificaciones vía fichero JSON (`--justify`, mapa test→texto **no vacío**) y emite resumen JSON por stdout. Integrar en la DoD de `agents/qa.md` (invocar el gate y pegar su salida como evidencia).
- **Estado**: completado
- **Tiempo humano**: est. 3,5 h · real —
- **Tiempo IA (ejec.)**: est. 1,0 h · real —
- **Supervisión**: est. 0,25 h (≈25 % IA) · real —
- **Previsión IA**: 300 k in / 45 k out tok · 7,2 €
- **Dependencias**: ninguna (fixtures propios); cerrar junto a T-03 para validar el esquema `flaky` real
- **Archivos**: `agent-kits/qa/qa-gate.py`, `tests/test_qa_gate.py` (+ fixtures), `agents/qa.md`
- **Cubre (tests)**: — (sin UI; pruebas = pytest)

**Criterios de aceptación**
- [x] `results.json` **ausente o malformado** ⟹ exit 1 con motivo «sin resultados» (la ausencia de evidencia es rojo, nunca verde).
- [x] Exit 0 ⟺ 0 failed y 0 flaky sin justificar; flaky con justificación de **texto no vacío** no rompe el verde; texto vacío o «es flaky» sin detalle por test ⟹ exit 1.
- [x] Emite resumen JSON por stdout (contadores + veredicto + motivos) apto para pegarse como evidencia en `report.md`.
- [x] `tests/test_qa_gate.py` cubre los 6 escenarios de spec §Pruebas (todo verde; con failed; flaky justificado; flaky no justificado; malformado; ausente) y pasa con `python tests/test_qa_gate.py`.
- [x] `agents/qa.md` invoca el gate en su DoD (resolución `find`, sin rutas fijas) y `scripts/lint_plugin.py` sigue en verde.

**Subtareas**
- [x] Spike: verificar el esquema real de `results.json` (status `flaky` con `retries`) contra la versión de Playwright del runner.
- [x] Implementar parseo + contadores + umbral + canal de justificaciones (`--justify` fichero JSON; se descartó `--justify-inline` — el fichero deja mejor rastro de evidencia). Endurecido tras la revisión de dos lentes: errores top-level del runner → rojo; `interrupted`/tests sin ejecutar → rojo; flaky declarados en `stats` pero no localizables → cuentan como sin justificar; títulos duplicados exigen justificación por `fichero::título`; verde exige ≥1 test ejecutado.
- [x] Manejo de errores: ausente/malformado ⟹ exit 1 «sin resultados»; justificación vacía ⟹ inválida.
- [x] Fixtures (6) + `tests/test_qa_gate.py`.
- [x] Editar la DoD de `agents/qa.md` (invocación + evidencia pegada).

**Notas**: decisión de plan: justificaciones por fichero JSON (ver improvement-plan §Cambios arquitectónicos). `/dev-cycle` consumirá el exit code en T-06.

### T-02 — `ledger-lint.py`: validación mecánica del ledger (C-04)

- **Descripción**: Crear `agent-kits/shared/ledger-lint.py`: valida `tasks.md` — vocabulario de estados permitido (los 5 de CONVENTIONS, embebidos), coherencia checkbox↔estado (`completado` ⟹ criterios `[x]`), tabla resumen coherente con los contadores por fase, IDs `T-XX` únicos. Exit 0/1 + informe legible. Integrarlo en las DoD/puertas de `implementer`, `qa` (P1) y `/dev-cycle`.
- **Estado**: completado
- **Tiempo humano**: est. 4,0 h · real —
- **Tiempo IA (ejec.)**: est. 1,2 h · real —
- **Supervisión**: est. 0,3 h (≈25 % IA) · real —
- **Previsión IA**: 340 k in / 50 k out tok · 8,1 €
- **Dependencias**: ninguna dura; T-04 y T-06 lo consumen (esta tarea va antes)
- **Archivos**: `agent-kits/shared/ledger-lint.py`, `tests/test_ledger_lint.py` (+ fixtures), `agents/implementer.md`, `agents/qa.md`, `commands/dev-cycle.md`
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] Exit 1 **solo** para incoherencias duras: estado fuera del vocabulario, tarea `completado` con criterios sin marcar, resumen descuadrado, IDs `T-XX` duplicados.
- [x] Formato **legacy** (planes anteriores, p. ej. sin columnas nuevas) ⟹ **avisos** por stdout y exit 0.
- [x] Informe legible por stdout que localiza cada problema (fase/tarea/línea).
- [x] `tests/test_ledger_lint.py` cubre los 5 escenarios de spec §Pruebas (coherente; estado inválido; completado con criterios sin marcar; resumen descuadrado; IDs duplicados) y pasa en local.
- [x] `agents/implementer.md` (DoD), `agents/qa.md` (P1) y `commands/dev-cycle.md` (puertas) lo invocan vía resolución `find`; `scripts/lint_plugin.py` en verde.

**Subtareas**
- [x] Inventariar variantes legacy reales (`docs/roadmap/*/tasks.md` del repo) para calibrar aviso vs. error duro.
- [x] Implementar las 4 familias de validación + modo legacy.
- [x] Fixtures (5) + `tests/test_ledger_lint.py`.
- [x] Integrar la invocación en los tres prompts (implementer DoD, qa P1, dev-cycle puertas).

**Notas**: vocabulario embebido (no se lee `docs/CONVENTIONS.md` en runtime) para funcionar standalone desde hook y CI. Calibrar con criterio: falsos positivos harían que los agentes ignoren el lint.

---

## Fase 2 — Cableado (C-02, C-05)

**Estado**: completado · **Estimado**: 2,25 h · **Real**: — · **Coste est.**: 116 € · **Tokens est.**: 175 k

### T-03 — Playwright estricto (C-02)

- **Descripción**: Endurecer `agent-kits/qa/runner/playwright.config.mjs`: `retries: 2` (hoy 1), `forbidOnly: true`, `trace: 'retain-on-failure'` y `timeout: 30_000` explícitos, reporter JSON garantizado. Con ello el flaky queda identificado en `results.json`, insumo de T-01.
- **Estado**: completado
- **Tiempo humano**: est. 1,0 h · real —
- **Tiempo IA (ejec.)**: est. 0,3 h · real —
- **Supervisión**: est. 0,1 h (≈25 % IA) · real —
- **Previsión IA**: 60 k in / 5 k out tok · 1,2 €
- **Dependencias**: ninguna; conviene cerrarlo junto a T-01 (valida el esquema `flaky` real)
- **Archivos**: `agent-kits/qa/runner/playwright.config.mjs`
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] La config contiene `retries: 2`, `forbidOnly: true`, `trace: 'retain-on-failure'`, `timeout` explícito (30 s, configurable) y el reporter `json` con `outputFile` garantizado.
- [x] Ejecución de humo del runner: un test que falla al 1.er intento y pasa al reintento aparece como `flaky` en `results.json` y T-01 lo detecta.
- [x] Un `test.only` accidental hace fallar la suite (`forbidOnly`).

**Subtareas**
- [x] Editar la config (retries/forbidOnly/timeout; conservar trace y reporter existentes).
- [x] Humo local con test flaky sintético y verificación del `results.json` resultante contra `qa-gate.py`.

**Notas**: `retries: 2` alarga suites con fallos reales (cada fallo se reintenta 2 veces); asumido por diseño en la spec.

### T-04 — Hook PostToolUse sobre `tasks.md` (C-05)

- **Descripción**: Crear `hooks/lint-tasks-ledger.sh` y registrar la entrada en `hooks/hooks.json` (matcher `Write|Edit|MultiEdit`): si la ruta editada casa con `*/tasks.md`, ejecuta `ledger-lint.py` en **modo aviso** (imprime problemas, nunca bloquea). Sigue el patrón de `hooks/mark-docs-pending.sh`: lee el JSON por stdin, extrae `file_path` con `jq` y fallback `grep`, y **jamás rompe la edición**.
- **Estado**: completado
- **Tiempo humano**: est. 1,25 h · real —
- **Tiempo IA (ejec.)**: est. 0,4 h · real —
- **Supervisión**: est. 0,1 h (≈25 % IA) · real —
- **Previsión IA**: 100 k in / 10 k out tok · 2,1 €
- **Dependencias**: T-02
- **Archivos**: `hooks/lint-tasks-ledger.sh`, `hooks/hooks.json`
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] El script termina **siempre** con exit 0 (también con ledger inválido: los problemas se imprimen como aviso).
- [x] Sin `python3` disponible (`command -v python3` falla) ⟹ sale 0 **en silencio**.
- [x] Extrae la(s) ruta(s) del payload stdin con `jq` y, si no hay `jq`, con el `grep` de respaldo (mismo patrón que `mark-docs-pending.sh`); ficheros que no son `*/tasks.md` ⟹ salida silenciosa.
- [x] Resuelve `ledger-lint.py` sin rutas fijas (relativa al hook vía `${CLAUDE_PLUGIN_ROOT}` con fallback `find` sobre `$PWD/.claude` y `$HOME/.claude`); si no lo encuentra, sale 0 en silencio.
- [x] `hooks/hooks.json` sigue siendo JSON válido (lo verifica el paso de CI existente) y editar un `tasks.md` real dispara el aviso.

**Subtareas**
- [x] Spike: confirmar el payload stdin del hook (`tool_input.file_path` / `edits[]`) contra la doc vigente de hooks.
- [x] Escribir el envoltorio (~20-30 líneas) con los guards (python3, jq/grep, resolución del script).
- [x] Añadir la entrada a `hooks/hooks.json` y probar en vivo (edición legítima + ledger roto).

**Notas**: modo aviso primero; el Stop-hook duro queda explícitamente fuera de alcance (spec §Alcance).

---

## Fase 3 — Integración (C-03, C-06, C-07)

**Estado**: completado · **Estimado**: 9,25 h · **Real**: — · **Coste est.**: 478 € · **Tokens est.**: 777 k

### T-05 — Puerta de cobertura criterios↔tests (C-03)

- **Descripción**: Crear `agent-kits/qa/coverage-check.py` (decisión de plan: script auxiliar, no dentro del gate): antes de ejecutar, cruza los criterios de aceptación de las tareas de UI de `tasks.md` con los `E2E-xx`/`M-xx` del `test-plan.md` (campo «Cubre (tests)»). Criterios huérfanos ⟹ se listan en `report.md` y el estado global **no puede ser verde**. Integrar como puerta previa en el P1 de `agents/qa.md`.
- **Estado**: completado
- **Tiempo humano**: est. 2,75 h · real —
- **Tiempo IA (ejec.)**: est. 0,8 h · real —
- **Supervisión**: est. 0,2 h (≈25 % IA) · real —
- **Previsión IA**: 220 k in / 25 k out tok · 4,8 €
- **Dependencias**: T-01 (convención de salida del kit), T-02 (parseo de `tasks.md`)
- **Archivos**: `agent-kits/qa/coverage-check.py`, `agents/qa.md`, `agent-kits/qa/templates/report.md`
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] Cada criterio de una tarea de UI sin `E2E-xx`/`M-xx` que lo cubra queda listado como huérfano (salida del script) y veta el verde (van a manual como mínimo).
- [x] Proyecto/plan **sin tareas de UI** (sin `test-plan.md`) ⟹ la puerta no aplica: se declara y **no bloquea** (exit 0).
- [x] Planes **legacy** sin campo «Cubre (tests)» ⟹ degradación a aviso (mismo espíritu que el modo legacy de T-02), sin huérfanos masivos que invaliden el informe.
- [x] `agents/qa.md` ejecuta la puerta en P1 y `templates/report.md` tiene sección de criterios huérfanos.
- [x] Prueba con un `tasks.md`+`test-plan.md` de fixture: huérfano detectado; cobertura completa ⟹ exit 0.

**Subtareas**
- [x] Definir el matching por IDs (convención estricta `E2E-xx`/`M-xx` en «Cubre (tests)»).
- [x] Implementar el cruce reutilizando el parseo de ledger de T-02.
- [x] Integrar en P1 de `agents/qa.md` + sección en la plantilla de informe.
- [x] Fixture de verificación (huérfano vs. cubierto vs. sin UI vs. legacy).

**Notas**: decisión de plan cerrada: script auxiliar del kit (ver improvement-plan §Cambios arquitectónicos).

### T-06 — `/dev-cycle`: bucle acotado + doble lente (C-06)

- **Descripción**: En `commands/dev-cycle.md` (solo Modo B, cadena nativa): (a) bucle qa→implementer con contador explícito, máx. **3 intentos**; al 3.er rojo, **parar sin cerrar estados**, resumir los fallos persistentes y preguntar al usuario (continuar / re-planificar / cancelar); (b) revisión adversarial con **dos subagentes en paralelo** — lente conformidad con spec/plan y lente calidad/robustez — con fusión de gaps (dedupe) y la misma puerta manual. Las puertas del ciclo consumen los exit codes de `qa-gate.py` y `ledger-lint.py`.
- **Estado**: completado
- **Tiempo humano**: est. 3,0 h · real —
- **Tiempo IA (ejec.)**: est. 0,9 h · real —
- **Supervisión**: est. 0,25 h (≈25 % IA) · real —
- **Previsión IA**: 220 k in / 22 k out tok · 4,6 €
- **Dependencias**: T-01, T-02 (consume sus exit codes en las puertas)
- **Archivos**: `commands/dev-cycle.md`
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] El prompt del ciclo lleva contador explícito y regla de corte: 3.er rojo ⟹ NO cerrar estados, resumen de fallos persistentes y decisión del usuario (continuar / re-planificar / cancelar).
- [x] La revisión adversarial lanza dos lentes en paralelo con contexto mínimo (diff + artefacto de referencia), fusiona gaps con dedupe (fichero+síntoma) y mantiene la puerta manual única.
- [x] Las puertas del ciclo usan los **exit codes** de `qa-gate.py` y `ledger-lint.py`, no la prosa.
- [x] Todo lo anterior aplica **solo en Modo B**; con superpowers detectado no se duplica revisión ni bucle.
- [x] Prueba manual (spec §Pruebas): iniciativa de juguete con 3 rojos simulados ⟹ corte y pregunta; doble lente ⟹ gaps fusionados sin duplicados.

**Subtareas**
- [x] Redactar la máquina de estados del bucle (contador, corte, mensaje de decisión).
- [x] Redactar las dos lentes (encargo, contexto mínimo, formato de gap) y la fusión/dedupe.
- [x] Cablear los exit codes de los gates en las puertas del ciclo.
- [x] Prueba manual guionizada sobre iniciativa de juguete (3 rojos + doble lente).

**Notas**: validación empírica; presupuesto ya contempla 1-2 iteraciones de prompt. `docs/FLOWS.md` se actualiza en T-08.

### T-07 — Bloques `API-xx` / `A11Y-xx` opt-in en test-plan (C-07)

- **Descripción**: Añadir a `agent-kits/planner/templates/test-plan.md` dos secciones **opcionales**: `API-xx` (smoke de endpoints con curl: método, URL relativa, status esperado, aserción simple sobre el body) y `A11Y-xx` (axe-core vía Playwright sobre páginas clave). `agents/qa.md` los ejecuta **solo si el test-plan los trae** (instalación de axe-core con el mismo flujo opt-in que Chromium; si no encaja, `A11Y-xx` se degrada a checklist manual). `agents/planner.md` documenta cuándo proponerlos.
- **Estado**: completado
- **Tiempo humano**: est. 3,5 h · real —
- **Tiempo IA (ejec.)**: est. 1,0 h · real —
- **Supervisión**: est. 0,25 h (≈25 % IA) · real —
- **Previsión IA**: 260 k in / 30 k out tok · 5,7 €
- **Dependencias**: independiente del resto (por eso cierra la fase); primera candidata a recorte
- **Archivos**: `agent-kits/planner/templates/test-plan.md`, `agents/qa.md`, `agents/planner.md`, `agent-kits/qa/runner/` (soporte axe-core)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] Las secciones `API-xx`/`A11Y-xx` de la plantilla son **opcionales**: un test-plan sin ellas se comporta exactamente como hoy.
- [x] `API-xx` define método, URL relativa, status esperado y aserción simple; qa los ejecuta con curl **bajo el guardrail local** existente (solo hosts locales/privados).
- [x] `A11Y-xx` corre axe-core vía Playwright solo con opt-in de instalación; si axe-core no es instalable, se degrada a checklist manual y se declara en el informe.
- [x] Un `API-xx`/`A11Y-xx` fallido se lista en `report.md` y **veta el verde** (misma regla que los criterios huérfanos; no toca el umbral del gate en v1).
- [x] Entorno no levantado para `API-xx` ⟹ se reporta como «no ejecutable» (no como verde), con instrucción al usuario.

**Subtareas**
- [x] Diseñar las dos secciones de la plantilla (campos + ejemplo).
- [x] Instrucciones de ejecución condicional + evidencias en `agents/qa.md`.
- [x] Soporte axe-core en el runner con flujo opt-in y degradación prevista (`runner/tests/A11Y-example.spec.mjs`, plantilla que qa adapta; la dependencia `@axe-core/playwright` se instala on-demand bajo permiso, no vive en `package.json`).
- [x] Nota en `agents/planner.md` (cuándo proponer los bloques).

**Notas**: decisión de plan: resultados API/A11Y fuera del umbral de `qa-gate.py` en v1 (ver improvement-plan §Cambios arquitectónicos).

---

## Fase 4 — Cierre (delta explícito del plan)

**Estado**: completado · **Estimado**: 0,5 h · **Real**: — · **Coste est.**: 26 € · **Tokens est.**: 46 k

### T-08 — Cierre: CHANGELOG, docs, CI y preparación de release

- **Descripción**: Cerrar la iniciativa: entrada en `CHANGELOG.md`; actualizar `docs/CONVENTIONS.md` (puertas deterministas en las reglas de ledger/DoD) y `docs/FLOWS.md` (ciclo con contador y doble lente); añadir `test_qa_gate.py` y `test_ledger_lint.py` a `.github/workflows/ci.yml`; dejar la release preparada (**la publicación queda a cargo del usuario**). **Delta explícito** sobre el presupuesto heredado: +0,5 h base.
- **Estado**: completado
- **Tiempo humano**: est. 0,5 h · real —
- **Tiempo IA (ejec.)**: est. 0,2 h · real —
- **Supervisión**: est. 0,05 h (≈25 % IA) · real —
- **Previsión IA**: 40 k in / 6 k out tok · 1,0 €
- **Dependencias**: T-01…T-07
- **Archivos**: `CHANGELOG.md`, `docs/CONVENTIONS.md`, `docs/FLOWS.md`, `.github/workflows/ci.yml`
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] `CHANGELOG.md` recoge la iniciativa (gates, hook, bucle, lentes, bloques opt-in).
- [x] `docs/CONVENTIONS.md` y `docs/FLOWS.md` reflejan las puertas deterministas y el ciclo endurecido.
- [x] `.github/workflows/ci.yml` ejecuta `tests/test_qa_gate.py` y `tests/test_ledger_lint.py` junto a la batería existente, y CI queda en verde (incluye `lint_plugin.py` y `release.py --check`).
- [x] Release **preparada y no publicada**: la publicación la decide y ejecuta el usuario.

**Subtareas**
- [x] Entrada de CHANGELOG.
- [x] Actualizar CONVENTIONS/FLOWS.
- [x] Cablear los dos tests en `ci.yml` y verificar CI en verde.
- [x] Nota de release para el usuario (qué versión y qué contiene).

**Notas**: no incluido en las 19,0 h heredadas de la evaluación; declarado como delta en el plan (cuadro de mando y presupuesto).

---

## Notas de implementación

_A completar durante la ejecución. Registra decisiones, desvíos de la estimación y aprendizajes._
