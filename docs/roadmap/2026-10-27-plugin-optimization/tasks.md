---
generacion:
  inicio: 2026-10-27T14:14:18Z
  fin: 2026-10-27T14:23:52Z
  fuente: medido
  fuente_id: src-d2ceb5c719af848b4c213bb2d521d0f003976923acb613d7512912ccbeb6a09e
  ventana_id: win-e20bc509ddb34b0d9d593d35104a422f
  revision_medicion: 1
  medicion_persistida: true
  tokens_reales: { entrada: 20, salida: 51792, cache_creacion: 66534, cache_lectura: 1007417 }
  eur: 1.44
  horas_ia: 0.22
  duracion: 13m
  ratio_usado: 531798.5
  avisos: ["CALIBRATION: filas marcadas (estimado) fuera de la mediana (informativo)"]
  # ventana compartida con improvement-plan.md
verificacion: obligatoria   # cada T-XX lleva `- **Verificación**:`; lo exige ledger-lint (exit 1 si falta)
changelog: Changed
---

# Checklist de Tareas — Optimización del plugin: hooks, tokens y modelos locales

| | |
|---|---|
| **Estado** | en-progreso |
| **Fecha** | 2026-10-27 |
| **Plan** | [`improvement-plan.md`](./improvement-plan.md) |
| **Diseño** | n/a (paso `architect` previsto en T-21, antes de F3) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del plan. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador SDD externo— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

> **Alcance autorizado 2026-10-29:** F1 publicada como **v2.1.0**; el usuario autoriza continuar **F2 y F3**. Se ejecutan secuencialmente: T-08 revalida F2 contra `master` publicado; F3 conserva su revalidación T-20 tras la release de F2 y la puerta de diseño T-21. Cada fase se publica en su propia release.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — Quick wins medibles (v2.1.0 publicada) | 7 | 7 | 100% | 0 / 38.4h | 0 / 14.8h | 0 / 3.7h | 0 / 6.0M in + 600k out |
| Fase 2 — Reestructuración (en ejecución) | 8 | 12 | 66.7% | 0 / 69.0h | 0 / 28.3h | 0 / 7.1h | 0 / 11.4M in + 1140k out |
| Fase 3 — Modelos locales (diferida) | 0 | 7 | 0% | 0 / 45.0h | 0 / 18.1h | 0 / 4.5h | 0 / 7.3M in + 730k out |
| **TOTAL** | **15** | **26** | **57.7%** | **0 / 152.4h** | **0 / 61.2h** | **0 / 15.3h** | **0 / 24.7M in + 2470k out** |

> **F2: 8 tareas completadas y revisión aprobada en 2 intentos; 3 condicionales canceladas (T-16/T-17/T-18, no implementadas); T-19 en progreso, QA/cobertura/CI verificadas y publicación pendiente de confirmar versión.** Las cancelaciones no se suman a las completadas.

> **Horas → Jira.** El worklog que imputa `jira-sync` al completar cada tarea es **Tiempo IA (ejec.) + Supervisión** (real; o estimación si no hay real), topado a la jornada configurada. Jira no está activado en este proyecto (no hay `jira.json`). Ver `skills/jira-sync/SKILL.md`.

> **Clasificación por tarea y primer oráculo (`dev.json`: `tdd: true`, `subagentes: false`, `coberturaMinima: 90`).** Capacidad nueva y defecto → test en ROJO primero (con evidencia `RED:`); cambio de comportamiento → test de comportamiento/caracterización en ROJO + suites existentes sin cambiar expectativas; refactor → test de caracterización de la salida actual; prosa/proceso → `lint`/`ledger-lint`/`scope-check` como oráculo y lectura declarada. Máquina justa de memoria: las `Verificación` son suites **dirigidas**; la suite completa corre en Linux/CI (T-07).

---
```curation-refs-v1
[
  {
    "candidate": "docs/knowledge/candidates/pending/2026-10-28-hook-cleanup-import-startup.md",
    "sha256": "30b3641663d65f42b560dedc6481e87b4b1cf06d96ef49c2d88242ff78255c4a"
  },
  {
    "candidate": "docs/knowledge/candidates/pending/2026-10-28-adr023-native-prefilter.md",
    "sha256": "f4633d214b5f07194d16270dd1752a7dbe1fe785baba515454432f9577bb5e46"
  },
  {
    "candidate": "docs/knowledge/candidates/pending/2026-10-29-redact-option-free-prose.md",
    "sha256": "d37ad0edf57bb634f4f4180a6b8ea1bd49fe280ca4deabdf8737b551711f8e8a"
  }
]
```

## Fase 1 — Quick wins medibles

**Estado**: completado · **Estimado**: 38.4h · **Real**: — · **Coste est.**: 1956 € · **Tokens est.**: 6.0M in / 600k out.

### T-01 — C-00 — Benchmark reproducible de hooks y tokens (línea base de esta máquina)

- **Descripción**: Resultado: un script versionado y con tests que mide la mediana (≥ 10 ejecuciones, con calentamiento descartado) de cada hook registrado en `hooks/hooks.json` con payloads fixture por runtime, y suma los tokens fijos por sesión (descriptions + índice de SessionStart) y bajo demanda (`commands/dev-cycle.md`, `agent-kits/shared/knowledge-check.md`); sale en JSON y Markdown para pegarlo en el ledger antes y después de cada cambio. Requisito: evaluation.md §C-00 y spec §Criterios («benchmark reproducible versionado… línea base registrada»); decisión 8 de la puerta: se versionan el procedimiento Y la línea base de esta máquina, marcada como tal (Windows + OneDrive, poca RAM).
- **Changelog**: Benchmark de hooks y tokens con fixtures, calentamiento y fallos estructurados; informa variabilidad. El helper de cierre difiere imports exclusivos de ejecución.
- **Estado**: completado
- **Cerrada**: 2026-10-29
- **Tiempo humano**: est. 7.2h · real —
- **Tiempo IA (ejec.)**: est. 2.23h · real —
- **Supervisión**: est. 0.56h (≈25 % IA) · real —
- **Previsión IA**: 0.9M in / 90k out tok · 5.38 €
- **Dependencias**: ninguna
- **Tipo**: test
- **Archivos**: `tests/test_console_encoding.py`, `docs/roadmap/2026-10-27-plugin-optimization/spec.md`, `docs/roadmap/2026-10-27-plugin-optimization/evaluation.md`, `scripts/bench-hooks.py`, `tests/test_bench_hooks.py`, `hooks/runtime-supervisor.py`, `tests/test_hook_supervisor.py`, `docs/knowledge/candidates/pending/2026-10-28-hook-cleanup-import-startup.md`, `tests/fixtures/bench-hooks/**`, `docs/observability.md`, `docs/en/observability.md`, `docs/roadmap/2026-10-27-plugin-optimization/testing/**`
- **Cubre (tests)**: `tests/test_bench_hooks.py` (28 casos); `tests/test_hook_supervisor.py`; `tests/test_hook_launcher_security.py`; `tests/hook-budget.test.mjs`; `tests/hook-runtime.test.mjs`; `tests/hook-guard-delivery.test.mjs`.
- **Verificación**:
  - `python3 -m pytest -q tests/test_bench_hooks.py` → todos pasan (parseo de payloads, mediana, calentamiento descartado, salida JSON, FALLO estructurado ante timeout)
  - `python3 scripts/bench-hooks.py --runs 10 --json` → exit 0 y JSON con `hooks[].mediana_ms`, `tokens_fijos`, `tokens_bajo_demanda` y `maquina` (SO, RAM libre)
  - `python3 scripts/bench-hooks.py --runs 10 --md` → tabla Markdown idéntica en estructura a la de `testing/baseline-f1.md`

**Criterios de aceptación**
- [x] El script mide ≥ 10 ejecuciones por hook (calentamiento descartado) con payloads fixture por runtime (`claude`, `codex`, `opencode`) y devuelve mediana, p95 y máximo.
- [x] Los tokens fijos por sesión (descriptions de agentes/skills/comandos + índice) y bajo demanda (`dev-cycle.md`, `knowledge-check.md`) salen en el mismo informe, con el método declarado (estimación, no tokenizador).
- [x] Un timeout o un hook caído produce un `FALLO` estructurado y exit 1, no un traceback; el hook medido nunca altera el estado del repo (usa un directorio temporal como `CLAUDE_PROJECT_DIR`).
- [x] `testing/baseline-f1.md` contiene la línea base de esta máquina, marcada explícitamente como «Windows + OneDrive, 2,8 GB libres, no extrapolable», con fecha, comando exacto y tabla.
- [x] El procedimiento (cómo ejecutar, cómo leer, por qué sin umbrales absolutos en CI) está en `docs/observability.md` y en su espejo EN.
- [x] Cobertura de `scripts/bench-hooks.py` ≥ 90 % (`dev.json` `tests.coberturaMinima`) o `coverage-gate.py` aplicado con `--changed-only`.

**Subtareas**
- [x] RED: escribir `tests/test_bench_hooks.py` y verlo fallar (el script no existe).
- [x] Crear fixtures por evento/runtime a partir de los payloads reales de `tests/hook-runtime.test.mjs` y `tests/hook_security_support.py`.
- [x] Implementar `scripts/bench-hooks.py` (medición in-process donde se pueda y e2e informativo, como `bench-session-end.py`).
- [x] Ejecutar tres pasadas completas correctas con ≥ 10 muestras por caso/runtime y calentamiento descartado; versionar muestras, procedencia, entorno y dispersión entre las tres medianas. Si no permite una comparación concluyente, declararlo y no atribuir ahorro global al código. Evaluar cada mejora temporal con control antes/después intercalado del mismo workload, fuentes identificadas, control de arranque y declaración de dispersión y fallos; ningún fallo se acepta como muestra de éxito (opción 2 autorizada por delegación del usuario, 2026-10-29).
- [x] Escribir `testing/baseline-f1.md` y el procedimiento en `docs/observability.md` + `docs/en/observability.md`.

**Notas**: Cierre 2026-10-29 tras revisión fresca A de F1 sobre `05ea2e0`: tres pasadas originales, 36 casos por pasada, 1.080 muestras, 108 calentamientos y ocho huellas históricas contrastadas; dispersión recalculada 102,06965 %. El benchmark actual coincide con el hash del recibo de cobertura (98 %), sin extrapolar ese dato al resto de F1. Se acepta solo la caracterización autorizada; no estabilidad uniforme ni la repetición parcial. Traza del intento 1 de revisión F1 y `testing/t01-characterized-baseline-verification-2026-10-29.json`. **Histórico previo al cierre:** Decisión independiente autorizada el 2026-10-29: el usuario delega la elección («lo que consideres mejor»); se elige y aplica la opción 2 de `testing/t01-stability-decision-proposal.md`. No se acredita estabilidad uniforme: se exige línea base caracterizada y comparación intercalada de cada mejora. La revisión de las tres pasadas y de la cobertura queda pendiente antes del cierre; `testing/t01-approved-adjustment-2026-10-29.json`. Diagnóstico 2026-10-29: reconstrucción de fuentes con las ocho huellas históricas coincidentes (LF/CRLF); repetición interrumpida tras cuatro casos, sin pasada completa ni muestras crudas recuperadas. Control separado: Node vacío 547,574–1.116,230 ms; fixture 7,449–50,438 ms. No se acredita estabilidad ni se atribuye una causa única a Windows. T-01 sigue abierta; `testing/t01-stability-diagnostic-2026-10-29.md`. **Histórico:** RED de integración Linux: se registra el modo de arranque real más barato en `test_console_encoding.py`; renderer usa el snippet UTF-8 canónico y configura LF aparte, sin relajar las aserciones cp1252/ascii. Estado revisado 2026-10-28: implementación y línea base registradas, tres pasadas válidas de 36/36, 1.080 muestras medidas y 108 calentamientos descartados. **T-01 sigue abierta por la subtarea original de estabilidad**: dispersión máxima 102,07 %. Scope-check detectó que se había reformulado su condición; se restaura literalmente y no se acepta esa dispersión como medianas estables. Las implementaciones independientes de F1 continúan con evidencia funcional, sin cerrar fase ni liberar mientras sigan abiertos estabilidad y rendimiento de T-02. JSON y Markdown canónico en `testing/baseline-f1.md`; comprobaciones en `testing/verification-2026-10-28.json`. **Histórico anterior al cierre (los estados siguientes corresponden a su momento):** GREEN 2026-10-28: 51 pruebas Python dirigidas; suite de entrega del guard repetida completa: 75/75. La primera ejecución real combinada tuvo 103/105: dos timeouts OpenCode; ambos pasan aislados con el supervisor antiguo y con el nuevo. Presupuestos y otros 30 casos de runtime pasaron en la combinada inicial. Inicialización del módulo: mediana 66,844 → 8,974 ms (20 muestras alternadas por variante, proceso nuevo, un calentamiento descartado); no incluye arranque de proceso ni cierre del job. Propuesta de gotcha pendiente de Curator vinculada en `curation-refs-v1`. Prerrequisito descubierto por el benchmark: reducir la inicialización innecesaria del helper de cierre, conservando el protocolo, los 500 ms del caller y los 250 ms de confirmación. RED: `test_windows_close_does_not_initialize_business_execution_modules` falló con `cleanup initialized business modules: [json, runpy, subprocess]` · 2026-10-28. La traza por pipe mide hasta 157,791 ms de inicialización previa a `close_job`; no demuestra por sí sola la causa única de los timeouts originales. Reanudación 2026-10-28: RED: `test_baseline_requires_discarded_warmup` falló (`linea_base: true` con `--warmup 0`); RED: `test_fail_fast_retains_first_failure_and_reports_incomplete_inventory` falló (`--fail-fast` no reconocido). La pasada completa anterior se conserva como diagnóstica y no usa estas opciones nuevas. Usage-meter cerrado: `fuente: estimado`, sin medida de tokens/horas/coste; duración de reloj 1h14m de ventana mixta (implementación y revisiones pedidas). No se imputa como horas IA de T-01 ni se usa para calibración.  Medición real: dos pasadas completas con 35/36 casos correctos cada una; ambas salieron 1 por `child cleanup confirmation timed out` en casos distintos. La serie de tres se detuvo; no hay línea base válida ni estabilidad demostrada. Evidencia en `testing/baseline-f1.md` y JSON crudos; T-01 conserva `en-progreso` y T-02 no se inicia. La investigación del patch OpenCode solicitada durante esta ventana se hizo solo en copias bajo `.pytest_cache`; no altera el patch ni los hooks de producción.  RED adicional: `test_silent_capture_without_persistence_is_failure` falló en las dos capturas (exit 0 sin recibo); ahora se exige un registro coincidente fuera del cronómetro, igual que `bench-session-end.py` (no se propone otra memoria para el mismo patrón ya documentado).  Alcance: la spec y la evaluación aprobadas ya estaban en disco sin seguimiento Git al retomar; se declaran para que scope-check reconozca esos artefactos heredados, sin alterar su contenido.  RED: `tests/test_bench_hooks.py::test_statistics_exclude_warmup` falló con `AssertionError: missing reproducible hook benchmark` (script ausente) · 2026-10-27. RED adicional: `test_reports_json_markdown_and_failure_exit_code` falló porque un informe fallido se marcaba como línea base; corregido. GREEN: 26 pruebas y cobertura medida del 98 % con `.venv/Scripts/python.exe -m coverage` (no se instaló ninguna dependencia). Smoke real de los 12 registros con `--runs 1 --runtime codex --json`: exit 0, sin fallos; no es línea base.  Clasificación: capacidad nueva → primer oráculo = test del propio script en ROJO (mediana, parseo de payloads, salida JSON) antes de escribirlo. Patrón a reflejar: `scripts/bench-session-end.py` (cabecera, `--runs/--warmup`, JSON estructurado, `FALLO` estructurado en timeout, exit 1) y su test `tests/test_bench_session_end.py`; los hooks salen de `hooks/hooks.json`. Hipótesis (a confirmar en la implementación): tokens = caracteres/4 como estimación declarada (no hay tokenizador en el repo; marcarlo `⚠️ estimación`); descriptions y frontmatter se leen igual que `scripts/lint_plugin.py`; el índice de SessionStart se mide ejecutando `agent-kits/shared/skill-index.py`. Fixtures en `tests/fixtures/bench-hooks/` (un JSON por evento y runtime). Ruido: comparar medianas relativas en la misma sesión; NO fijar umbrales absolutos en CI. Esta tarea ejecuta el benchmark en esta máquina y pega la tabla en `testing/baseline-f1.md`. No corras suites completas. Clasificación: capacidad nueva. Coste estimado de la tarea: 365 € (horas × 50 € + tokens).


### T-02 — C-02 — Prefiltro del guard nativo en node

- **Descripción**: Resultado: `hooks/run-hook.mjs` lee `agent-kits/shared/native-roles.json`, `agent-kits/shared/copias.json`, `agent-kits/shared/copias.json`, compara la identidad nativa EXACTA (`agent_type` en Claude/Codex, `agent` en OpenCode) con los roles protegidos del runtime y, si no coincide, termina sin lanzar Python; si el mapa falta o es inválido, lanza Python como hoy y emite su diagnóstico. La decisión de deny sigue en `native-guardrail.py`. Requisito: evaluation.md §C-02 (cero Python y ahorro local medido, sin extrapolación a minutos por sesión tras el ajuste aprobado 2026-10-29); spec §Criterios CA-01/CA-02/CA-03 y §Manejo de errores; ADR-023.
- **Changelog**: Prefiltro nativo de identidades exactas para evitar Python en sesiones sin rol protegido, con retorno al evaluador ante dudas.
- **Estado**: completado
- **Cerrada**: 2026-10-29
- **Tiempo humano**: est. 7.2h · real —
- **Tiempo IA (ejec.)**: est. 3.48h · real —
- **Supervisión**: est. 0.87h (≈25 % IA) · real —
- **Previsión IA**: 1.4M in / 140k out tok · 8.37 €
- **Dependencias**: T-01
- **Tipo**: hooks
- **Archivos**: `tests/test_graphiti_security.py`, `agent-kits/shared/copias.json`, `hooks/run-hook.mjs`, `hooks/opencode-plugin.js`, `agent-kits/shared/native-roles.json`, `tests/hook-guard-delivery.test.mjs`, `tests/hook-guard-prefilter.test.mjs`, `tests/test_native_prefilter_parity.py`, `tests/test_hook_launcher_security.py`, `docs/observability.md`, `docs/en/observability.md`, `interop/**` (regenerado: `hooks/`|`agents/`|`commands/` tocados), `.codex-plugin/**`, `.agents/plugins/**`
- **Cubre (tests)**: —
- **Verificación**:
  - `node --test tests/hook-guard-prefilter.test.mjs tests/hook-guard-delivery.test.mjs` → todos pasan; el shim `CUSTOM_AGENTS_PYTHON` NO se invoca para identidades no protegidas y SÍ para `custom-agents:implementer`/`custom-agents:architect` (y sus equivalentes de Codex/OpenCode)
  - `python3 -m pytest -q tests/test_native_prefilter_parity.py tests/test_hook_launcher_security.py agent-kits/shared/test_guardrail_check.py` → todos pasan sin cambiar expectativas previas (paridad node/Python sobre la tabla de identidades; mapa corrupto → diagnóstico `role-map-unavailable`)
  - `python3 scripts/export-interop.py --check` → exit 0
  - Comparación versionada antes/después de `native-guardrail` (sesión sin rol protegido): ≥ 10 muestras por variante y runtime, calentamiento descartado, control de arranque Node, dispersión y fallos declarados; recibo y tabla en `testing/t02-native-prefilter.md`. Sin porcentaje mínimo en F1 (ajuste aprobado 2026-10-29).

**Criterios de aceptación**
- [x] CA-01: sin rol protegido (sin `agent_type`/`agent`, o identidad no protegida), un Bash o Edit no arranca ningún proceso Python; comparación versionada antes/después con ≥ 10 muestras por variante y runtime, calentamiento descartado, control de arranque Node, dispersión y fallos declarados. F1 informa la mejora observada sin exigir un porcentaje mínimo (ajuste aprobado 2026-10-29).
- [x] CA-02: con identidad nativa exacta de `implementer` o `architect` el guard deniega las operaciones prohibidas igual que antes (suites de guard en verde SIN modificar expectativas).
- [x] CA-03: con `native-roles.json` corrupto, ausente o con esquema no soportado se lanza Python y se emite el diagnóstico actual; nunca se omite la comprobación.
- [x] Tabla de paridad node/Python cubre mayúsculas, prefijos, espacios, valores no string, identidad de Codex vs OpenCode vs Claude y runtime desconocido; falla si `PROTECTED` y la lista de node divergen.
- [x] El prefiltro no emite nunca `deny` ni `systemMessage` propio; solo decide si se lanza Python (hooks informan, exit 0).
- [x] La revisión incluyó la Lente C (seguridad) en todos los intentos y su traza está en el ledger; adenda a ADR-023 propuesta (ruta pending/SHA anotada en Notas).
- [x] Estado de `hooks/opencode-plugin.js` decidido y documentado (prefiltro aplicado o diferencia declarada).

**Subtareas**
- [x] RED: test de no-lanzamiento con shim de Python (identidad no protegida) y test de paridad; verlos fallar.
- [x] Implementar la lectura de `native-roles.json` y la comparación exacta en `run-hook.mjs` (rama `guard`), con caída a Python ante cualquier duda.
- [x] Decidir y aplicar el criterio del adaptador de OpenCode.
- [x] Medir antes/después con `bench-hooks.py` y pegar la tabla en el ledger.
- [x] Proponer la adenda de ADR-023 (`knowledge-curation.py propose`) y regenerar `interop/`.

**Notas**: Cierre 2026-10-29 tras cuatro lentes independientes de contexto fresco A/B/C/D sobre `bae4e46..78c2070`; cero gaps Critical/Important/Minor. B confirma 16 pruebas de paridad y 23 Node; A ejecuta interop (88 al día); C contrasta ADR-023 original y adenda pendiente; D confirma límites y medición sin excluir Node. Traza en «Revisión de dos lentes — intento 3» y `testing/t02-review-attempt-3-2026-10-29.json`. CA-01 ajustado cumplido, sin afirmar 80 % ni estabilidad general. La cobertura global del diff y la revisión de fase siguen pendientes en T-07; no se declara un porcentaje inexistente. **Histórico previo al cierre:** Scope-check detecta exactamente los dos criterios previstos (T-02 CA-01 y su referencia en T-07), cero ficheros fuera de alcance. Se rebate con la aprobación explícita del usuario, sin cambiar el detector: `testing/f1-approved-adjustment-2026-10-29.json`. Ajuste aprobado por el usuario el 2026-10-29 («adelante», «adelante con el plan»), aplicado en spec/plan/evaluación/ledger: `testing/f1-performance-adjustment-proposal.md`. CA-01 de F1 exige cero Python y comparación transparente, sin mínimo porcentual. CA-01 se marca con la evidencia funcional y el control versionado existente; T-02 sigue en-progreso por su revisión de seguridad pendiente. El 80 % no se declara alcanzado: queda como investigación posterior sin alcance ni coste nuevos aprobados. T-01 estabilidad y T-07 revisión/entrega permanecen abiertas. **Histórico de mediciones y diagnóstico previo al ajuste:** Medición intercalada válida 2026-10-29, sin otras suites propias en ejecución: 10 muestras + calentamiento por variante y runtime, sin fallos. Claude 933,702 → 576,892 ms (38,21 %); Codex 854,110 → 540,547 ms (36,71 %); OpenCode 893,032 → 554,176 ms (37,94 %). Control Node vacío: 513–534 ms. Es mejora local observada, **no cumple el 80 % aprobado** ni acredita entrega nativa de eventos; T-02 permanece abierta. Recibo `testing/t02-paired-control-2026-10-29.json`, ambas variantes comparten supervisor y mapa actuales. Integración Linux 2026-10-29: se declara `tests/test_graphiti_security.py` para actualizar la huella nominal del launcher tras revisar su diff completo; el prefiltro local y la captura aislada no añaden red ni nuevos ejecutables. No se amplía ninguna excepción ni se relaja el detector; se conservan sus controles mutantes. La revisión es secuencial propia, no revisores independientes. Evidencia `testing/t07-launcher-fingerprint-review-2026-10-29.json`. Estado actual: implementación funcional validada, rendimiento del 80 % pendiente. Tres pasadas filtradas completadas; frente a la base antigua no se acredita reducción. Control intercalado: Node vacío 1.208 ms y prefiltro 1.266 ms; el control anterior tuvo un fallo y se conserva como FALLO, sin ganancia aceptada. No se cierra T-02. Informe `testing/t02-native-prefilter.md`; adenda propuesta vinculada en `curation-refs-v1`. Se permite continuar la implementación independiente de F1 tras validar seguridad funcional, manteniendo abierta la aceptación cuantitativa y el cierre de fase. RED de revisión C 2026-10-28: `unclosed input has a deadline (backward clock: true)` agotó el watchdog externo; corregido usando reloj monotónico para el plazo compartido de lectura y evaluación. Refactor con caracterización previa en verde (153 Python + 110 Node): la validación del mapa se replica byte a byte mediante `copias.json`, con paridad de roles y límite de entrada respecto a Python. RED adicional 2026-10-28: `OpenCode uncertain map before-setup/after-setup` fallaron porque el callback omitía Python cuando el mapa no era válido. RED 2026-10-28: las tres pruebas `unprotected native identity skips Python even when unavailable` fallaron con `role guard could not start` al intentar Python para una sesión principal. Clasificación: cambio de comportamiento observable (qué procesos arrancan) sin cambiar el veredicto → primer oráculo = test de no-lanzamiento en ROJO (hoy node SIEMPRE lanza Python: `hooks/run-hook.mjs:194-203`) más suites de guard SIN cambiar expectativas. Patrón: `evaluate()` en `agent-kits/shared/native-guardrail.py:256-300` (identidad exacta, `PROTECTED = ("implementer", "architect")` en :20); el override `CUSTOM_AGENTS_PYTHON` de `run-hook.mjs` (función `python()`) permite un shim que cuenta lanzamientos sin tocar el intérprete real; tests existentes `tests/hook-guard-delivery.test.mjs` y `tests/test_hook_launcher_security.py`. Decisión por defecto a confirmar en la revisión: NO cambiar el esquema de `native-roles.json` (`schema_version` 1, que `native-guardrail.py:263` exige); node deriva la lista protegida de las claves `implementer`/`architect` y un test de paridad ata esa lista a `PROTECTED` leyéndolo de `native-guardrail.py`. Si la revisión exige fuente física única → `schema_version` 2 con lectura compatible. Fallar cerrado: cualquier duda (JSON ilegible, runtime desconocido, `agent_type` no string) → lanzar Python. El adaptador `hooks/opencode-plugin.js:138` (`run`) lanza su propio proceso: decidir en el primer paso si necesita el mismo prefiltro y, si no lo lleva, documentarlo en la adenda. Adenda a ADR-023: proponer vía `agent-kits/shared/knowledge-curation.py propose` (no editar el ADR a mano). **Lente C (seguridad) obligatoria en los 3 intentos de revisión** (forzar con `dev.json` `revision.lenteSeguridad`); lente D por el hot path. Hooks exit 0 e informativos: el prefiltro nunca emite `deny` por sí mismo. Clasificación: cambio de comportamiento (rendimiento) en zona de seguridad. Coste estimado de la tarea: 368 € (horas × 50 € + tokens).


### T-03 — C-04 — Timeout de SessionStart y captura de prompt con arranque aislado

- **Descripción**: Resultado: `hooks/hooks.json` declara `timeout: 30` en SessionStart (decisión 5 de la puerta; se baja a 10 s cuando C-06 deje el arranque en un solo Python) y `test_hooks_config.py` lo vigila; la captura de UserPromptSubmit arranca `journal.py capture` con `-I -S` si sus imports lo permiten. Requisito: evaluation.md §C-04 y spec §Criterios («`hooks/hooks.json` declara timeout en SessionStart»); la parte `-I -S` entra porque la evaluación la incluye («siempre que sus imports lo permitan»).
- **Changelog**: SessionStart declara 30 s y la captura de prompts usa Python aislado, conservando redacción y opt-outs.
- **Estado**: completado
- **Cerrada**: 2026-10-28
- **Tiempo humano**: est. 2.4h · real —
- **Tiempo IA (ejec.)**: est. 0.99h · real —
- **Supervisión**: est. 0.25h (≈25 % IA) · real —
- **Previsión IA**: 0.4M in / 40k out tok · 2.39 €
- **Dependencias**: T-02
- **Tipo**: hooks
- **Archivos**: `hooks/hooks.json`, `hooks/run-hook.mjs`, `tests/test_hooks_config.py`, `tests/hook-runtime.test.mjs`, `docs/observability.md`, `docs/en/observability.md`, `interop/**` (regenerado: `hooks/`|`agents/`|`commands/` tocados), `.codex-plugin/**`, `.agents/plugins/**`
- **Cubre (tests)**: —
- **Verificación**:
  - `python3 -m pytest -q tests/test_hooks_config.py` → todos pasan, incl. el test nuevo `SessionStart` con `timeout == 30`
  - `node --test tests/hook-runtime.test.mjs` → todos pasan (la captura sigue escribiendo el log del turno con `-I -S`, o el caso queda documentado como descartado)
  - `python3 scripts/export-interop.py --check` → exit 0
  - `python3 scripts/bench-hooks.py --runs 10 --md` → mediana de `user-prompt-capture.sh` registrada antes/después en el ledger

**Criterios de aceptación**
- [x] `hooks/hooks.json` declara `timeout: 30` en SessionStart y el test lo vigila; `interop/codex/hooks.json` regenerado coherente.
- [x] La captura de prompts mantiene su salida (log del turno, redacción de secretos, opt-out `<private>`) con el arranque aislado, o la subtarea de comprobación demuestra que no es viable y queda declarado.
- [x] El hook sigue saliendo siempre con exit 0 e informativo.
- [x] Notas anota el plan de bajada a 10 s cuando se haga C-06.

**Subtareas**
- [x] RED: test de `timeout == 30` en SessionStart; verlo fallar.
- [x] Añadir `"timeout": 30` al bloque SessionStart y regenerar interop.
- [x] Probar `journal.py capture` con `-I -S` contra la fixture de prompt; si pasa, aplicar el cambio en `run-hook.mjs` con su test.
- [x] Medir antes/después y pegar la tabla en el ledger.

**Notas**: Verificación final: runtime Node **19/19**, configuración y captura Python **33 pass / 3 skips de plataforma**, interop **88 al día**. El prototipo aislado conserva el prompt exacto, redacta el secreto sintético y mantiene el log intacto con `<private>` (`testing/t03-verification.json`). Plan: bajar a **10 s cuando C-06 unifique el arranque**; los límites internos de 20 s del launcher y del adaptador OpenCode son independientes. Mediana Codex UserPromptSubmit: base **1.006,568 ms** (mediana de tres pasadas) → **1.074,019 ms** (10 muestras + 1 calentamiento); no se acredita mejora de velocidad. Primera tentativa: FALLO en calentamiento por confirmación de limpieza; se retiene en `testing/t03-capture-attempt-1.json`, repetición válida en `testing/t03-capture.json`. En Windows el supervisor ya arrancaba aislado; los flags ahora también llegan al despacho directo. Ventana de trabajo 24 min de reloj, sin medición compatible de tokens/horas IA/coste. Autorrevisión secuencial de conformidad y corrección, sin revisores independientes (`subagentes:false`); QA de fase/Linux pendiente en T-07. RED 2026-10-28: `test_session_start_declares_thirty_second_timeout` falló con `None != 30`. Prueba real previa: `journal.py capture` con `-I -S` persistió el prompt fixture exacto (exit 0, sin stderr). El cambio de flags reutiliza esa configuración validada. Implementación adelantada con T-02 funcional validada; su criterio cuantitativo del 80 % sigue abierto y bloquea el cierre de F1. Clasificación: cambio de comportamiento → primer oráculo = test en ROJO que exige `timeout == 30` en SessionStart (hoy el bloque `SessionStart` de `hooks/hooks.json` no declara `timeout`). Patrón: `tests/test_hooks_config.py::test_session_end_usa_exec_form_con_timeout_5` (:26-31) para el estilo de la aserción; la rama de captura está en `hooks/run-hook.mjs` (último `else` de la construcción de `args`, `journal.py capture` sin `-I -S`, mientras que `session-journal.sh` ya usa `-I -S`). `journal.py` importa solo stdlib (`argparse`, `json`, `os`, `subprocess`, … `importlib.util`), lo que hace viable `-I -S`; comprobarlo ejecutando la captura con la fixture de prompt antes de cambiar la línea: si algún import hermano falla, se descarta la mitad `-I -S`, se documenta y la tarea cierra solo con el timeout. Riesgo: un timeout menor que la mediana actual (14-22 s) dejaría la retoma sin contexto; 30 s es deliberadamente alto. Opcional (no obligatorio): verificar que el adaptador de OpenCode tiene su propio límite. Clasificación: cambio de comportamiento (configuración de hook). Coste estimado de la tarea: 122 € (horas × 50 € + tokens).


### T-04 — C-05 — Temporales sqlite huérfanos de `knowledge-find.py`

- **Descripción**: Resultado: `construir_indice` borra también el `-journal` de su temporal y, al reconstruir el índice, barre los temporales `knowledge-index.sqlite.<pid>.tmp` (+ `-journal`) de procesos muertos o con antigüedad suficiente, de modo que no se acumulen tras una muerte forzada. Requisito: evaluation.md §C-05 y spec §Criterios CA-05; hoy hay 20 parejas huérfanas en `.claude/`.
- **Changelog**: La reconstrucción del índice elimina temporales y journals antiguos de procesos confirmados muertos y limpia los propios incluso al fallar.
- **Estado**: completado
- **Cerrada**: 2026-10-28
- **Tiempo humano**: est. 3.6h · real —
- **Tiempo IA (ejec.)**: est. 1.24h · real —
- **Supervisión**: est. 0.31h (≈25 % IA) · real —
- **Previsión IA**: 0.5M in / 50k out tok · 2.99 €
- **Dependencias**: T-03
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/knowledge-find.py`, `tests/test_knowledge_find.py`, `agent-kits/shared/test_knowledge_index_canonico.py`
- **Cubre (tests)**: —
- **Verificación**:
  - `python3 -m pytest -q tests/test_knowledge_find.py agent-kits/shared/test_knowledge_index_canonico.py` → todos pasan, incl. los tests nuevos de barrido y `-journal`
  - `python3 -m pytest -q tests/test_knowledge_find.py -k "tmp or huerfano"` → los tests nuevos pasan; sin ellos (revertido el fix) fallan (RED registrado)

**Criterios de aceptación**
- [x] CA-05: dados `*.tmp` y `*.tmp-journal` de PIDs muertos, al reconstruir el índice se eliminan.
- [x] Un temporal de un PID vivo o más joven que el umbral NO se borra (test con proceso vivo simulado).
- [x] Tras una construcción normal (éxito o excepción) no queda ni `.tmp` ni `.tmp-journal` propios.
- [x] El barrido nunca sale del directorio del índice ni sigue enlaces simbólicos, y un fallo de E/S no rompe la reconstrucción (degrada con aviso, sin bloquear).

**Subtareas**
- [x] RED: test que crea el par huérfano y comprueba que sobrevive (fallo actual).
- [x] Borrar `tmp + '-journal'` en el `finally` de `construir_indice`.
- [x] Añadir el barrido con comprobación de PID vivo + antigüedad, acotado a los patrones del propio índice.
- [x] Ejecutar una reconstrucción real en el repo y comprobar que desaparecen las parejas viejas de `.claude/`.

**Notas**: GREEN: suites dirigidas **151 pass / 3 skips**; cuatro casos de carrera/estado desconocido añadidos después, conjunto dirigido de limpieza **24 pass / 2 skips**. Cobertura de líneas nuevas **95 %** (100 sentencias); la cobertura global in-process anterior fue 44 % porque los tests CLI lanzan procesos sin cobertura, no se presenta como 95 % del módulo. Linux verificará enlaces en T-07 (Windows no permite crear symlinks en estas fixtures). Reconstrucción real: **40 → 2** temporales, 38 eliminados, 70 entradas y caché legible; se preserva la pareja del PID 6 por estado dudoso (`testing/t04-real-rebuild.json`). Umbral conservador: **PID confirmado muerto Y todos los miembros con edad ≥ 1 h**. Autorrevisión A/B/C secuencial (sin agentes independientes): patrón literal del índice, PID acotado, lstat sin seguir enlaces, rechazo de reparse/junction y resolución del padre, comprobación de identidad antes del borrado, ninguna operación recursiva; fallos de E/S no propagan rutas o errores privados. No se afirma atomicidad contra un atacante que pueda sustituir directorios entre comprobaciones y syscalls; la limpieza usa el directorio local de caché bajo el mismo dueño. Scope-check con base `bae4e46` (los commits anteriores de OpenCode pertenecen a otro ledger) da 0 ficheros fuera de alcance y 0 criterios alterados. Se añadió `copias.json` a T-02 para declarar el registro de la validación compartida. RED 2026-10-28: `test_indice_barre_tmp_huerfano_y_journal_antiguos` falló porque ambos ficheros de PID muerto seguían existiendo tras reconstruir un índice SQLite válido (1 failed / 93 deselected). Clasificación: defecto → primer oráculo = test de regresión en ROJO que reproduce el fallo (temporal `.tmp` + `-journal` de un PID muerto sobrevive a una reconstrucción). Causa raíz ya localizada: `construir_indice` borra solo `tmp` en el `finally` (`agent-kits/shared/knowledge-find.py:825-830`) y un proceso matado por el Job Object no llega al `finally`; el journal de sqlite se llama `<tmp>-journal`. Patrón de tests: `tests/test_knowledge_find.py` y `agent-kits/shared/test_knowledge_index_canonico.py`. Riesgo: borrar el temporal de un proceso concurrente vivo → comprobar que el PID no está vivo (best-effort multiplataforma, sin dependencias nuevas) Y aplicar umbral de antigüedad; ante duda no se borra. El aviso en `/doctor` que menciona la evaluación es opcional y queda fuera salvo que sobre holgura. Las 20 parejas existentes en `.claude/` desaparecerán en la siguiente reconstrucción real (el directorio no está versionado; no se commitea nada de ahí). **Lente C obligatoria** (borrado de ficheros por patrón: path traversal/PID spoofing). Clasificación: defecto. Coste estimado de la tarea: 183 € (horas × 50 € + tokens).


### T-05 — C-03 — Statusline con una sola llamada Python y caché por mtime

- **Descripción**: Resultado: el statusline pasa de 3 llamadas a `python3` a UNA como máximo (script Python único que parsea la entrada y calcula el segmento de roadmap), usa el intérprete que ya resuelve el launcher —sin el alias `python3` de WindowsApps— y guarda caché por mtime de los ledgers activos; con caché vigente no lanza Python. Requisito: evaluation.md §C-03 y spec §Criterios CA-04.
- **Changelog**: El statusline conserva su formato con un solo Python aislado, sirve caché sin Python y evita alias de WindowsApps.
- **Estado**: completado
- **Cerrada**: 2026-10-28
- **Tiempo humano**: est. 6.0h · real —
- **Tiempo IA (ejec.)**: est. 2.23h · real —
- **Supervisión**: est. 0.56h (≈25 % IA) · real —
- **Previsión IA**: 0.9M in / 90k out tok · 5.38 €
- **Dependencias**: T-04
- **Tipo**: hooks
- **Archivos**: `tests/test_console_encoding.py`, `statusline/roadmap-statusline.sh`, `agent-kits/shared/statusline-render.py`, `agent-kits/shared/progress-report.py`, `tests/test_statusline_cache.py`, `commands/setup.md`, `docs/observability.md`, `docs/en/observability.md`, `interop/**` (regenerado: `hooks/`|`agents/`|`commands/` tocados), `.codex-plugin/**`, `.agents/plugins/**`
- **Cubre (tests)**: —
- **Verificación**:
  - `python3 -m pytest -q tests/test_statusline_cache.py` → todos pasan (salida idéntica a la de referencia; ≤ 1 lanzamiento de Python; 0 con caché vigente; alias de WindowsApps ignorado; sin Python → solo modelo)
  - `python3 -m pytest -q agent-kits/shared/test_progress_report.py` → sin regresiones
  - `python3 scripts/export-interop.py --check` → exit 0
  - `python3 docs/roadmap/2026-10-27-plugin-optimization/testing/t05-benchmark.py` → mediana del statusline antes/después pegada en el ledger

**Criterios de aceptación**
- [x] CA-04: con el statusline activado y el ledger sin cambios, un refresco lanza como máximo un proceso Python, sirve desde caché y no usa el alias de WindowsApps.
- [x] La salida (modelo · coste de sesión · ctx · progreso del roadmap) es idéntica a la actual para las entradas fixture, con y sin `jq`.
- [x] La caché se invalida cuando cambia el mtime de un ledger activo y no se versiona.
- [x] Sin intérprete válido o con error del script degrada en silencio mostrando al menos el modelo (nunca rompe la barra, siempre exit 0).

**Subtareas**
- [x] RED: test de caracterización + conteo de lanzamientos con shim; verlos fallar.
- [x] Crear `statusline-render.py` (entrada → modelo/coste/ctx + segmento de roadmap + caché por mtime).
- [x] Reescribir `roadmap-statusline.sh` para resolver el intérprete y hacer una sola llamada.
- [x] Actualizar `commands/setup.md` solo si cambia el comando instalado; documentar la caché en `docs/observability.md` (+ EN).
- [x] Medir antes/después y pegar la tabla en el ledger.

**Notas**: RED de integración Linux: se registra el modo de arranque real más barato en `test_console_encoding.py`; renderer usa el snippet UTF-8 canónico y configura LF aparte, sin relajar las aserciones cp1252/ascii. GREEN: **17/17** pruebas nuevas, **14/14** de compatibilidad de statusline y **39/39** de progreso. Cobertura del renderer **96 %** (97 sentencias, 4 sin cubrir). Medianas intercaladas (10 muestras + 1 calentamiento): antes **1.763,356 ms**, después frío **1.208,365 ms**, con caché **1.110,182 ms** (≈37 % menos frente al control de esta pasada; no se extrapola). El primer candidato, más lento por procesos auxiliares, se conserva como `testing/t05-benchmark-candidate-1.json`; se sustituyeron `grep`, `wc`, `tail`, `cut`, `cat` y `dirname` por operaciones internas cuando era posible. La normalización de rutas Windows se verificó tras un rojo de 6 casos que había ocultado el roadmap. Autorrevisión secuencial A/B/D: salida y redondeo caracterizados, argumentos sin eval, campos cacheados públicos, invalidación por entrada/mtime/usage/código, siempre exit 0; QA Linux de fase pendiente en T-07. El benchmark C-00 mide hooks registrados y no incluye el statusline opt-in; para esta tarea se versiona `testing/t05-benchmark.py`, que usa la misma fixture sintética y compara antes/después intercalados con 10 muestras y calentamiento. Se conserva Bash `printf` para mantener exactamente el redondeo visible; el renderer emite cuatro campos de línea, no código evaluable. La caché de campos públicos `.claude/statusline-cache` se invalida por entrada, mtime de ledgers, usage-state y scripts; no guarda el JSON crudo. RED adicional 2026-10-28: una caché truncada LF devolvía stdout vacío; se exige el número de líneas del protocolo antes de servirla. La primera implementación mezclaba CRLF con Bash en Windows y perdió coste/contexto; corregida con stdout LF explícito. RED 2026-10-28: `test_statusline_cold_one_python_and_warm_zero` conserva la salida exacta pero falla porque arranca **3** Python en vez de uno. Clasificación: refactor de rendimiento con salida idéntica → primer oráculo = test de caracterización en ROJO: la salida del statusline para unas entradas fixture (con jq y sin jq) debe ser idéntica antes y después, y un shim de `python3` en el PATH cuenta lanzamientos (hoy 3: `statusline/roadmap-statusline.sh:34,72,79`). Patrón: `agent-kits/shared/progress-report.py active --root … --json` ya calcula el segmento y `agent-kits/shared/skill-index.py` es el patrón de caché por hash. Hipótesis (a confirmar): script nuevo `agent-kits/shared/statusline-render.py` que importa `progress-report.py` por `importlib` (nombre con guion) y escribe la caché en `.claude/statusline-cache.json` (no versionado; sembrar `.claude/.gitignore` como hace `journal.py capture`); resolución del intérprete en bash: honrar `CUSTOM_AGENTS_PYTHON`, recorrer `command -v -a python3 python` y descartar rutas `*/WindowsApps/*` (mismo criterio que `candidates()` en `hooks/run-hook.mjs`); sin intérprete → imprime solo el modelo (degradación silenciosa existente, línea 17). El statusline es solo de Claude Code y sin node. Si cambia el comando que `/setup` 5-bis instala en `settings`, actualizar `commands/setup.md`. Lente D (rendimiento) por el refresco continuo. Clasificación: refactor (comportamiento observable igual; menos procesos). Coste estimado de la tarea: 305 € (horas × 50 € + tokens).


### T-06 — C-01 — Descriptions ≤ 600 caracteres conservando los literales de evals

- **Descripción**: Resultado: ninguna description de agente, skill o comando pasa de 600 caracteres (hoy 25 de 52 la superan, exceso 7.584 caracteres ≈ −2.100 tokens fijos/sesión), conservando los literales que exige `evals/check.py`; `DESC_WARN_CHARS` baja de 1.200 a 600 en `scripts/lint_plugin.py`, se regenera interop y se actualiza `docs/CONVENTIONS.md` (+ EN). Requisito: evaluation.md §C-01 y spec §Criterios («ninguna description… pasa de 600; los tokens fijos bajan al menos ~2.000»).
- **Changelog**: Descriptions de agentes, skills y comandos por debajo de 600 caracteres con alcance completo conservado en sus cuerpos y disparadores validados.
- **Estado**: completado
- **Cerrada**: 2026-10-29
- **Tiempo humano**: est. 9.6h · real —
- **Tiempo IA (ejec.)**: est. 3.97h · real —
- **Supervisión**: est. 0.99h (≈25 % IA) · real —
- **Previsión IA**: 1.6M in / 160k out tok · 9.57 €
- **Dependencias**: T-05
- **Tipo**: docs
- **Archivos**: `agent-kits/evaluator/README.md`, `agent-kits/evaluator/references/scope.md`, `tests/fixtures/opencode-v2-agent-contract.json`, `agents/*.md`, `skills/*/SKILL.md`, `skills/plugin-dev/references/piece-boundaries.md`, `commands/setup.md`, `commands/doctor.md`, `evals/cases/*.json`, `scripts/lint_plugin.py`, `tests/test_lint_plugin.py`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `docs/agents/*.md`, `interop/**` (regenerado: `hooks/`|`agents/`|`commands/` tocados), `.codex-plugin/**`, `.agents/plugins/**`
- **Cubre (tests)**: —
- **Verificación**:
  - `python3 scripts/lint_plugin.py` → 0 avisos `description de N caracteres (> 600)`; sin errores nuevos
  - `python3 evals/check.py` → exit 0 (toda pieza con ≥ 2 positivos + 1 negativo y el literal casando con la description REAL)
  - `python3 -m pytest -q tests/test_lint_plugin.py tests/test_skill_size.py tests/test_export_interop.py` → todos pasan
  - `python3 scripts/export-interop.py --check` → exit 0
  - `python3 scripts/bench-hooks.py --tokens-only --json` → tokens fijos ≥ ~2.000 menos que `testing/baseline-f1.md`; tabla pegada en el ledger

**Criterios de aceptación**
- [x] Ninguna description de agente, skill o comando supera 600 caracteres (comprobado por test de repositorio y por el linter).
- [x] `lint_plugin.py` avisa a 600 (`DESC_WARN_CHARS = 600`) y `docs/CONVENTIONS.md` (+ EN) lo documenta.
- [x] Todos los literales de `evals/cases/` siguen casando (`evals/check.py` exit 0); no se editan casos salvo ampliación justificada.
- [x] Los tokens fijos por sesión bajan ≥ ~2.000 frente a la línea base (tabla antes/después en el ledger).
- [x] Medición manual en sesión real registrada en Notas: ¿vuelven las 13 skills al listado? Si no, queda abierta la decisión del segundo recorte (no se hace en F1).
- [x] Para cada pieza recortada, Notas indica qué se movió y a dónde (cuerpo/`references/`), para que la revisión (lente A) valide que no se perdió ningún disparador.

**Subtareas**
- [x] RED: test que exige ≤ 600 en todas las piezas y el aviso del linter a 600; verlo fallar con las 25 actuales.
- [x] Grupo 1 — agentes (architect, reviewer, analyst, documenter, knowledge-curator, evaluator): reescribir, `evals/check.py`, regenerar interop.
- [x] Grupo 2 — 16 skills: reescribir, `evals/check.py`.
- [x] Grupo 3 — `commands/setup.md` y `commands/doctor.md`: reescribir, regenerar interop.
- [x] Bajar `DESC_WARN_CHARS` a 600 y actualizar CONVENTIONS ES/EN.
- [x] Medir tokens fijos antes/después; hacer la prueba manual del listado de skills y anotarla.

- [x] Revisar las correcciones A1/A2 del intento 1 de revisión final de F1 con su evidencia, sin reabrir veredictos aceptados salvo evidencia nueva.

**Notas**: Cierre tras intento 2 de revisión F1 sobre `8f83ecc`: A confirma A1/A2 resueltos (199 líneas, 0 párrafos perdidos y recibo tokens-only exacto); B sin defectos, C/D previos conservados sobre código idéntico. Cero gaps pendientes. `testing/t07-f1-review-attempt-2-2026-10-29.json`. **Histórico de la reapertura y corrección:** Reabierta durante la revisión final de F1, intento 1: dos Important. (1) `plugin-dev/SKILL.md` supera 200 líneas, incumpliendo CONSTITUTION:28; se traslada el detalle de clasificación a `references/piece-boundaries.md`, sin perder párrafos. (2) La Verificación declaraba `--runs 3 --md`, pero el recibo existente solo acredita inventario de tokens. Se corrige la declaración al comando pertinente `--tokens-only --json` y se ejecutará de nuevo para dejar su recibo exacto; no se inventa una corrida histórica de hooks. TDD n/a: prosa y trazabilidad; el primer oráculo es diet-check/lint/evals y el inventario real. **Histórico:** Cierre 2026-10-29 tras autenticar la CLI por el usuario: sesión nueva real con la rama local y presupuesto/modelo por defecto registra descripción para las 27 skills; 26 coinciden con el texto fuente tras normalizar espacios y entidades HTML, y `confluence-pull` usa el comando homónimo que la invoca. Sin herramientas ejecutadas ni cambios de instalación global. Recibo `testing/t06-native-visibility-authenticated-2026-10-29.json`; limitación: prueba con settings de proyecto y plugin local, sin reconstruir la configuración histórica ni acreditar causalidad o calidad de activación. No se aplica segundo recorte. **Histórico previo al cierre:** Reanudación 2026-10-29: dos arranques nativos reales con Claude Code 2.1.311 y la rama local registran los 27 nombres de skills, sin errores de plugin. La CLI no tiene autenticación (`loggedIn: false`); no se obtuvo respuesta del modelo ni recibo del listado renderizado con sus descripciones. T-06 sigue abierta, sin afirmar que falten o vuelvan las 13 descripciones históricas. Recibos `testing/t06-native-visibility-2026-10-29.json` y `testing/t06-native-visibility-debug-2026-10-29.json`. Se corrige la subtarea mixta que estaba marcada pese a faltar la comprobación manual; los grupos implementados quedan marcados conforme a las evidencias ya registradas. RED Linux de integración: evaluator alcanzó **15.856 bytes > tope CA-22 15.513**. Su alcance completo se mueve a `agent-kits/evaluator/references/scope.md` bajo demanda, sin elevar el tope; el test de exportación verifica ahora esa referencia y su contenido. Se recoloca la sección de alcance bajo el título principal de cada pieza para conservar intacto el bloque previo de capacidades. Implementación verificada: **80/80** pruebas de linter/tamaño/interop y suite-script histórica `test_lint_plugin: OK`; evals **52 piezas / 192 casos / 0 errores**, sin modificar casos. Linter: 0 errores y 4 avisos (3 comandos genéricos previos y plugin-dev de 209 líneas, por debajo del límite duro 250); 0 avisos de descriptions >600. 24 piezas movieron su description completa a `## Alcance y activación` del mismo cuerpo; evaluator la conserva en la referencia indicada; mapa individual y hashes en `testing/t06-description-moves.json`, con todos los disparadores anteriores conservados y el literal de setup en su propósito. Evitar corte automático de palabras con guion al plegar YAML: insertar un espacio en `adversarial-review` alteraba su literal. Tokens fijos estimados (caracteres/4): Claude **8.752 → 5.519**, Codex **8.745 → 5.512**, OpenCode **8.783 → 5.508**; ahorro **3.233/3.233/3.275** tokens estimados, no consumo real. T-06 sigue abierta: **no se ha medido en una sesión nueva real la recuperación de las 13 skills**; la sesión actual cargó el plugin instalado anterior. No se aplica un segundo recorte ni se cambia la instalación global. La fixture de semántica propia OpenCode fijaba las descriptions antiguas: se actualiza solo ese campo y se conserva el anterior como `description_body`, cuya presencia en el cuerpo exportado exige ahora el test. Mode, permisos y campos nativos permanecen idénticos (comparación de datos verificada). Dos literales adicionales de evals (`campo de respuesta eliminado`, `incluye extensiones propias de proyecto y usuario`) se conservaron en las descriptions tras el rojo; no se modificó ningún caso de activación. RED 2026-10-28: el test de 601 caracteres no recibió aviso (umbral 1.200); el test de inventario detectó las 25 piezas por encima de 600. La fixture inicial de linter contenía un reemplazo con acentos alterado por la consola; se corrigió antes de confirmar el rojo con la descripción real de 601 caracteres. Clasificación: refactor de prosa con riesgo de activación → primer oráculo = test en ROJO en `tests/test_lint_plugin.py`: el linter avisa a 600 y un test de repositorio comprueba que ninguna pieza real supera 600 (hoy 25 fallan). Patrón: `scripts/lint_plugin.py:108` (`DESC_WARN_CHARS = 1200`) y :1381-1403 (el aviso); los literales de activación están en `evals/cases/<kind>-<nombre>.json` y `python3 evals/check.py` los compara con la description REAL; las skills viajan sin traducir pero su description no puede pasar de 1.024 (OpenCode) — 600 queda por debajo. Mayores excesos: architect 1.097, reviewer 1.084, analyst 1.067 caracteres, además de documenter, knowledge-curator, evaluator, 16 `skills/*/SKILL.md`, `commands/setup.md`, `commands/doctor.md`. Trabajar por GRUPOS revisables (agentes → skills → comandos) y regenerar interop al cerrar cada grupo. Riesgo principal: perder disparadores; `evals/check.py` solo comprueba literales y la activación real (`evals/run.py`/`headless.yml`) necesita `ANTHROPIC_API_KEY`, que no se asume — la mitigación es mover el detalle fuera de la description (al cuerpo de la pieza o a `references/`) y no tocar los literales; declarar en Notas qué se movió. Medición manual declarada (no automatizable): en una sesión real comprobar si las 13 skills sin descripción vuelven al listado nativo; si no basta, abrir decisión para un segundo recorte (fuera de presupuesto). Medir tokens fijos antes/después con `bench-hooks.py`. Descriptions de `docs/agents/<x>.md` no cambian salvo que repitan el literal. Clasificación: refactor (prosa) con riesgo de activación. Coste estimado de la tarea: 490 € (horas × 50 € + tokens).


### T-07 — P-F1 — Proceso de la fase 1: revisión final, medición, CHANGELOG doble, Linux y release

- **Descripción**: Resultado: F1 cerrada y publicable: revisión de dos lentes de la fase completa (3 intentos como máximo, con corrección), tabla final antes/después del benchmark, CHANGELOG ES/EN actualizados desde los ledgers cerrados, docs espejo coherentes, `export-interop.py --check` verde, réplica de `ci.yml` en Linux verde y release de la fase con `scripts/release.py`. Requisito: evaluation.md §Partidas de proceso (P-F1) y decisión 6 de la puerta (una release por fase).
- **Changelog**: Refuerza las pruebas de prioridad y terminación, evita análisis de redacción innecesarios y actualiza inventarios y evidencias de QA manteniendo los plazos.
- **Estado**: completado
- **Cerrada**: 2026-10-29
- **Tiempo humano**: est. 2.4h · real —
- **Tiempo IA (ejec.)**: est. 0.64h · real —
- **Supervisión**: est. 0.16h (≈25 % IA) · real —
- **Previsión IA**: 0.3M in / 30k out tok · 1.79 €
- **Dependencias**: T-01, T-02, T-03, T-04, T-05, T-06
- **Tipo**: devops
- **Archivos**: `tests/codex-plugin-state.test.mjs`, `tests/test_agent_activity_store.py`, `tests/test_local_state_fix3.py`, `agent-kits/shared/redact.py`, `agent-kits/shared/journal.py`, `tests/test_redact_fix3.py`, `CHANGELOG.md`, `CHANGELOG.es.md`, `docs/observability.md`, `docs/en/observability.md`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `docs/roadmap/README.md`, `docs/roadmap/2026-10-27-plugin-optimization/testing/**`, `interop/**` (regenerado: `hooks/`|`agents/`|`commands/` tocados), `.codex-plugin/**`, `.agents/plugins/**`
- **Cubre (tests)**: —
- **Verificación**:
  - `python3 agent-kits/shared/ledger-lint.py docs/roadmap/2026-10-27-plugin-optimization/tasks.md` → exit 0
  - `python3 agent-kits/shared/scope-check.py docs/roadmap/2026-10-27-plugin-optimization` → exit 0
  - `python3 scripts/export-interop.py --check` → exit 0
  - `python3 scripts/lint_plugin.py && python3 evals/check.py` → exit 0
  - `python3 scripts/release.py 2.1.0 --dry-run` → exit 0 y sin avisos de copias `.MANUAL-COPY` desactualizadas
  - lectura: réplica de `ci.yml` en Linux (`python:3.11-slim`) con la suite completa en verde; salida pegada en el ledger

**Criterios de aceptación**
- [x] La revisión de dos lentes de la fase completa quedó cerrada en ≤ 3 intentos con su traza en el ledger (Minor no bloquean).
- [x] `testing/baseline-f1.md` incluye la tabla «después» y el ahorro medido frente a la línea base (CA-01: cero Python y comparación versionada con ≥ 10 muestras por variante/runtime, calentamiento descartado, control Node, dispersión y fallos; sin porcentaje mínimo del guard en F1, ajuste aprobado 2026-10-29; ≥ ~2.000 tokens fijos; statusline ≤ 1 Python).
- [x] Los dos CHANGELOG (`[Unreleased]` EN y `[Sin publicar]` ES) recogen F1 con un bullet por tarea; docs espejo ES/EN actualizados en el mismo cambio.
- [x] La réplica Linux de `ci.yml` pasa sin rojos aceptados «de siempre».
- [x] El release de F1 se publica con `scripts/release.py` (nunca a mano) previa confirmación del usuario sobre la versión; `--check` posterior en verde.
- [x] El índice `docs/roadmap/README.md` refleja el estado de F1.

**Subtareas**
- [x] Revisión de dos lentes sobre el diff de F1 (bucle ≤ 3) y corrección.
- [x] Ejecutar `bench-hooks.py` «después» y completar `testing/baseline-f1.md`.
- [x] Sincronizar CHANGELOG ×2 con `changelog-sync` desde los ledgers cerrados y revisar docs espejo.
- [x] Verificación en Linux (réplica de `ci.yml`).
- [x] `release.py --dry-run`, confirmar versión con el usuario, publicar y `--check`.

**Notas**: Publicada v2.1.0 tras la confirmación explícita del usuario («Sí, publicar F1 y continuar»). PR #19 fusionada; script de release, --check, interop y workflow 40891518461 correctos; dos ZIP publicados. Recibo `testing/t07-published-2.1.0-2026-10-29.json`. F1 completada; la iniciativa sigue en progreso. **Histórico:** CI completa de referencia VERDE sobre `5ede2a6`: https://github.com/daycry/custom-agents/actions/runs/40884197169; 9.653 Python / 38 skip / 82 subtests y Node 364 pass / 0 fail / 16 skip. Captura p95 8,18 ms / p99 8,61 ms, límites intactos. Recibo `testing/t07-reference-ci-5ede2a6-success-2026-10-29.json`; resumen `testing/t07-qa-summary-2026-10-29.md`. Preview portable: 254 ficheros / 25 skills / 0 problemas; `plugin-dev` y `quick-implement` excluidas por diseño existente, con la referencia nueva presente en el plugin completo. Memoria de la causa probada del oráculo: propose rechazado con `incomplete_inventory` (exit 2); borrador externo conservado y persistencia pendiente, sin candidato ni aprobación (`testing/t07-liveness-memory-handoff-2026-10-29.json`). **T-07 sigue abierta solo para confirmar la versión y entregar la release**; F2/F3 diferidas. **Histórico:** Revisión de implementación cerrada en intento 3 sobre `07e78b6`, A/B sin gaps; C/D previos conservados para producción idéntica. Preview local aislada 2.1.0: dry-run, aplicación sin git, `release --check` e interop 88 al día pasan. El patch solo toca cinco manifiestos y ambos changelogs; HEAD/tag de la preview y manifiestos de la rama no se publican ni cambian. Fuente `testing/t07-release-2.1.0-preview-2026-10-29.json`; sigue pendiente CI completa del fix y confirmación del usuario para fusionar/publicar. **Histórico:** Tabla final antes/después consolidada: guard con control intercalado aislado, tokens estimados y garantías funcionales, más los 36 registros de la observación posterior bajo carga declarada (sin atribuir ahorro global). Las notas ES/EN tienen un bullet por T-01..T-06 cerrado y uno por los cambios de validación/redacción realmente implementados en T-07; OpenCode V2 se conserva. `changelog-sync --check --json`: exit0 sin pendientes. Como el ledger completo26tareas sigue en progreso, se usa su renderer sin modificar sobre registros F1 completados y se traducen/editan ambos textos; no se finge una iniciativa cerrada. Proyección `testing/f1-changelog-projection-2026-10-29.json`. **Histórico:** Cobertura oficial completa recogida en Linux sobre `8f83ecc`: gate changed-only Python 90,74 % de media en siete ficheros medidos, mínimo 90; helper de medición documental sin datos excluido explícitamente por el gate. Perfil instrumentado: 9.635 pass / 1 fail temporal / 55 skip, 82 subtests; no se declara corrida global verde. Fallo del redactor: 500.012 caracteres sudo, 1,818 s frente al límite intacto 1,5 s. Exportación recuperada con la misma semántica ignore_errors de pytest-cov para cinco nombres compile virtuales; 285 resúmenes idénticos, sin cambiar datos ni exclusiones de fuente. `testing/t07-phase-python-coverage-2026-10-29.json`. Pasada después completa: 36/36, 360 muestras +36 calentamientos, exit 0 y fuentes estables; carga concurrente declarada, sin ahorro global atribuido (`testing/f1-after-hooks-2026-10-29.json`). **Histórico:** CI `40872615290` sobre `8f83ecc` falla en el oráculo de limpieza nativa Codex (PID visible); no se acepta como verde. Cinco repeticiones originales no reproducen el fallo; cinco con un subreaper propio que retiene estados terminales muestran `kill(pid,0)` visible y `/proc` estado Z, sin cambiar el helper ni su deadline. Esto prueba un defecto del oráculo, no el estado exacto del PID histórico CI. RED: `Codex state liveness oracle recognizes an exited child before it is reaped` falla con true != false y estado Z confirmado · 2026-10-29. Fix solo de test: reconoce Z/X terminales en Linux; R/S/T y errores inciertos no se aceptan como terminación. No cambia producción ni plazos. GREEN Linux: 7 tests; mutantes sin matar el grupo y con oráculo siempre false fallan por el motivo previsto. Revisión final se reabre para el intento 3 y nueva CI completa; se declaran fuente de test y evidencia como prerrequisito QA. **Histórico:** CI de referencia completa VERDE sobre `d29868d8c574bd9845b5d99b5c7abffc59cc9035`: https://github.com/daycry/custom-agents/actions/runs/40862893418; 9.653 pass / 38 skip / 82 subtests, Node 362 pass / 0 fail / 16 skip; captura p95 0,69 ms / p99 0,72 ms con límites intactos. Recibo `testing/t07-reference-ci-attempt-2.json`. El ajuste aprobado de CA-01 elimina solo el mínimo porcentual de F1; no cierra T-01, T-02 ni T-07. Los checks Linux de esta implementación se acreditan con ese SHA, sin afirmar validación de futuros cambios. **Histórico de QA previo al ajuste:** GREEN de la fixture de prioridad: 262 pruebas de actividad/modelo/IO pasan en Linux, 1 skip; tras reforzar la limpieza de hijos propios, la prueba real de contención vuelve a pasar en Windows. Ambos mutantes relevantes siguen rechazados. Evidencias `testing/t07-reference-ci-attempt-1.json` y `testing/t07-activity-contention-diagnostic-2026-10-29.json`. La siguiente CI de referencia validará la rama completa; no se marca aún QA global como verde. CI de referencia `40858130024` sobre `7e002a0`: 9.651 pass / 1 fail / 38 skip; las pruebas temporales del redactor pasan. Falla una de ocho señales con `state_busy` bajo contención. Diagnóstico sin cambiar producción: tres repeticiones originales y tres instrumentadas pasan; se observa una retención de 130,17 ms frente a la espera contractual de 100 ms. No se reconstruye la causa exacta del fallo CI; la fixture no garantizaba que el escritor previo liberase dentro del plazo. Se controla la prioridad antes de la ráfaga, manteniendo 8/8 señales, ocho escritores activos y cero eventos de herramienta admitidos bajo la prioridad; se conserva el test de `state_busy` observable con cerrojo ocupado. Un nuevo modelo comprueba el anuncio antes de la preparación. Mutantes sin anuncio temprano y sin cesión de herramientas fallan; positivos dirigidos 3 pass, modelo/IO 22 pass / 1 skip. TDD n/a: corrección de fixture y caracterización de contrato existente, sin cambios en el almacén ni sus presupuestos. Validación de referencia prevista mediante el workflow CI original en un PR en borrador de `feat/plugin-optimization`; los recibos locales conservan sus fallos y no se declaran verdes. Comprobaciones complementarias sobre el mismo código normalizado pasan: captura p95 19,39 ms / p99 21,70 ms, interop 88, Node 362 pass / 0 fail / 16 skip, sintaxis/JSON y `release --check`; no constituyen suite completa verde (`testing/t07-supplementary-linux-2026-10-29.json`). Intento Linux 8 detenido tras un fallo conocido: 5.554 pass / 1 fail / 36 skip, salida pytest 2 por SIGINT propio, no suite completa (`testing/t07-linux-attempt-8.json`). El primer caso de apóstrofos pasa; otro de 30.000 comandos curl repetidos mide 1,619 s. Caché acotada explorada solo en memoria: 1.470 comparaciones de salida coinciden; se descarta su incorporación al observar fallos temporales en rutas que no modifica. Control Windows posterior: 9,09–9,65 s reales frente a 0,72–0,89 s de CPU. La variación no demuestra la causa exacta del fallo Linux; se conserva el límite original y se busca validación en runner de referencia (`testing/t07-local-timing-variability-2026-10-29.json`). GREEN 2026-10-29: 809 pruebas dirigidas de redacción pasan con el límite original; otras 85 de índice y copias pasan. Cobertura oficial del módulo canónico: 99,23 %, 2/2 sentencias añadidas ejecutadas; no es cobertura del módulo journal ni gate global de F1 (`testing/t07-redact-coverage-2026-10-29.json`). QA completa intento 7: 9.631 pass / 3 fail / 55 skip, 82 subtests; recibo `testing/t07-linux-attempt-7.json`. Dos fallos comparten la fila de OpenCode fuera de la tabla Markdown: se elimina solo la línea vacía que cerraba la tabla. El redactor supera el límite intacto de 1,5 s en prosa patológica. Perfil: 50.002 análisis de comandos; hipótesis temporal probada evita analizar subtextos sin prefijo de opción `-`, reduce los análisis a 2 y la mediana 722,01 a 455,34 ms, conservando salida e idempotencia. Se declaran canónico, respaldo y test como prerrequisito de QA sin relajar umbrales. RED: `tests/test_redact_fix3.py::test_quoted_prose_without_options_avoids_nested_command_scans` falló con 200 análisis innecesarios en el ejemplo pequeño · 2026-10-29. RED de integración 2026-10-29: `test_todo_python_en_linea_del_repo_lleva_la_variable_incluido_el_que_no_la_necesitaba` esperaba 8 fragmentos shell y encontró 6. Causa: T-05 trasladó dos fragmentos de statusline al renderer standalone; el inventario del test no se había actualizado. Se ajusta solo el recuento a 6 y su explicación; la exigencia de UTF-8 para todos los fragmentos permanece. GREEN: 2 pruebas dirigidas pasan. Intento Linux 5: 1.684 pass / 1 fail / 2 skip, conservado en `testing/t07-linux-attempt-5.json`; intento 6 en curso con la corrección y snapshot verificado de 1.592 archivos, sin diferencias de contenido ni modos. **Reanudada por el usuario el 2026-10-29.** Diagnostico sin cambios de codigo: el test de captura con limite original <20 ms pasa tres veces aislado. En tres series de 30 muestras sobre disco la mediana queda entre 14,82 y 15,15 ms; el perfil atribuye el 92,6 % del tiempo de `capture_end` a `fsync`. El control en RAM solo sirve para aislamiento; no sustituye la QA sobre disco ni demuestra la causa exacta del rojo anterior. Evidencia: `testing/t07-resume-diagnostic-2026-10-29.json`. Nueva replica Linux completa en curso sobre el commit entregado `4de24ea`, 2 GiB/2 CPU, mismos umbrales. TDD n/a: diagnostico y proceso, sin cambios de codigo. **Historico: pausa solicitada por el usuario 2026-10-28, tras commits y push.** Última QA Linux: linter, evals y todas las suites-script pasan; pytest se detiene con **280 pass / 1 fail / 1 skip**, `test_bench_mide_in_process_no_solo_subproceso`: **p50 29,15 ms frente a <20 ms**. La causa no está aislada y no se cambia el umbral. No se ejecutan las etapas posteriores de esa corrida; **no es una suite global verde**. Snapshot verificado por bytes y modos de 1.587 ficheros (0 diferencias), limitado a 2 GiB/2 CPU; recibo `testing/t07-linux-attempt-4.json`. Los fallos anteriores de consola se corrigieron y pasan 25 tests seleccionados más arranques reales de los dos scripts bajo cp1252/ascii. Continúan pendientes T-01 estabilidad, T-02 reducción del 80 %, T-06 sesión real y el resto del cierre de T-07; sin release ni cambio de versión. Se adelanta QA Linux de la implementación independiente con snapshot del árbol actual; T-01 (estabilidad), T-02 (80 %) y T-06 (sesión real) siguen abiertos. No se bumpea versión, publica release ni cierra F1 con esas condiciones pendientes. Clasificación: proceso. Primer oráculo = `ledger-lint` + `scope-check` en rojo/verde sobre la iniciativa (sin tareas abiertas de F1). Release: `scripts/release.py` mueve `[Unreleased]`/`[Sin publicar]` a la sección de la versión en los dos CHANGELOG, corre lint + evals, exige copias `.MANUAL-COPY` al día, corrige `.sh` en 100644, bumpea los 5 manifiestos y comprueba `export-interop.py --check`; hacer `--dry-run` primero y `--check` después (LES-012). Versión propuesta: **2.1.0** (capacidad nueva —benchmark— y umbral de description más estricto para los consumidores); confirmar con el usuario antes de publicar. Verificación en Linux: réplica de `ci.yml` en `python:3.11-slim` con `git -c core.autocrlf=false archive` (los rojos «de siempre» no se aceptan: se investigan). Cierre de iniciativa = PR a master + release (lo coordina `/dev-cycle`). La retro (`/retro`) es puerta del cierre: `retro-gate.py`. No correr la suite completa en local (poca RAM): la completa se corre en Linux/CI. Clasificación: proceso (sin código nuevo). Coste estimado de la tarea: 122 € (horas × 50 € + tokens).

---

## Fase 2 — Reestructuración

**Estado**: en-progreso · **Estimado**: 69.0h · **Real**: — · **Coste est.**: 3518 € · **Tokens est.**: 11.4M in / 1140k out. **Autorizada el 2026-10-29**: revalidación T-08 contra v2.1.0; las verificaciones concretas siguen debajo.

### T-08 — Revalidar el plan de F2 contra `master`

- **Descripción**: Resultado: el esqueleto de F2 (T-09..T-19) queda confirmado o reajustado contra el `master` posterior a la release de F1 (cambios en hooks, comandos y suites que cita el plan), con los datos de F1 (medición de descriptions y benchmark) para decidir C-17/C-18. Requisito: decisión 2 de la puerta (+0,5 h de revalidación por fase diferida); evaluation.md §Riesgos transversales «envejecimiento del plan».
- **Changelog**: Revalida las rutas, pruebas y opciones de F2 contra v2.1.0; mantiene el presupuesto como provisional sin inventar costes reales.
- **Estado**: completado
- **Cerrada**: 2026-10-29
- **Tiempo humano**: est. 0.6h · real —
- **Tiempo IA (ejec.)**: est. 0.10h · real —
- **Supervisión**: est. 0.03h (≈25 % IA) · real —
- **Previsión IA**: 0.0M in / 0k out tok · 0.00 €
- **Dependencias**: T-07 (release de F1 publicada)
- **Tipo**: docs
- **Archivos**: `docs/roadmap/2026-10-27-plugin-optimization/improvement-plan.md`, `docs/roadmap/2026-10-27-plugin-optimization/tasks.md`
- **Cubre (tests)**: —
- **Verificación**: `python3 agent-kits/shared/ledger-lint.py docs/roadmap/2026-10-27-plugin-optimization/tasks.md` → exit 0 tras el reajuste

**Criterios de aceptación**
- [x] Cada tarea T-09..T-19 tiene `Verificación` y `Archivos` concretos y vigentes contra `master`.
- [x] Decisión explícita sobre C-15 (spike), C-17 y C-18 registrada en el `Changelog del plan`.
- [x] Las estimaciones diferidas se recalculan con el real de F1 (`CALIBRATION.md`); la diferencia queda anotada.

**Subtareas**
- [x] Comparar `master` con la base del plan (hooks, `dev-cycle.md`, suites citadas).
- [x] Concretar verificaciones y archivos de F2.
- [x] Decidir C-15/C-17/C-18 y anotar en el changelog del plan.

**Notas**: TDD n/a: proceso y prosa. Revalidación cerrada con `testing/t08-revalidation-2026-10-29.md`; 69,0 h F2 / 45,0 h F3 conservadas (delta 0 h) porque el real de implementación F1 no es medible en esta sesión. Se documenta ese límite y no se inventa desviación ni se modifica CALIBRATION. Verificación ledger: exit 0, avisos de tareas futuras. En revalidación contra `a157679`, release v2.1.0 verificada. Pruebas/rutas actualizadas; decisiones iniciales C-15 spike go, C-17 go condicionado a ahorro seguro tras T-13, C-18 no-go productivo por falta de evidencia de activación. Falta cerrar el informe y el contraste de estimaciones; no se inventan horas reales de F1. **Histórico:** Primera tarea de F2; no se arranca nada de F2 sin ella. Al revalidar: concretar los `Verificación` marcados «se concreta al revalidar», actualizar `Archivos`, decidir C-17 y C-18 con los datos de C-01 (¿volvieron las 13 skills al listado?) y de C-09, y registrar los cambios en el `Changelog del plan`. IDs estables: lo nuevo toma el siguiente número libre. Clasificación: proceso. Coste estimado de la tarea: 30 € (horas × 50 € + tokens).


### T-09 — C-08 — `mark-docs-pending` dentro de node

- **Descripción**: Resultado: el hook que solo crea un fichero vacío tras escribir en `docs/` (3,6-4,6 s por Write/Edit) pasa a `hooks/run-hook.mjs` con los mismos filtros de ruta y exclusiones. Requisito: evaluation.md §C-08, spec §Alcance F2.
- **Changelog**: Crea el marcador de documentación pendiente en Node sin Python ni shell, conservando exclusiones y avisando ante entradas o destinos inseguros.
- **Estado**: completado
- **Cerrada**: 2026-10-30
- **Tiempo humano**: est. 3.6h · real —
- **Tiempo IA (ejec.)**: est. 1.24h · real —
- **Supervisión**: est. 0.31h (≈25 % IA) · real —
- **Previsión IA**: 0.5M in / 50k out tok · 2.99 €
- **Dependencias**: T-08
- **Tipo**: hooks
- **Archivos**: `hooks/mark-docs-pending.sh`, `hooks/run-hook.mjs`, `hooks/opencode-plugin.js`, `tests/hook-post-preflight.test.mjs`, `tests/hook-docs-marker.test.mjs`, `interop/**` (regenerado), `.codex-plugin/**`, `.agents/plugins/**`
- **Cubre (tests)**: —
- **Verificación**: `node --test tests/hook-post-preflight.test.mjs tests/hook-docs-marker.test.mjs` → exit 0; tests nuevos se crean primero en RED antes del código correspondiente

**Criterios de aceptación**
- [x] Mismo marcador vacío y filtros docs/, security-scan y confluence; Write/Edit/MultiEdit y apply_patch en tres runtimes; ruta aplicable sin Python ni shell. Entradas inválidas y IO denegada degradan con exit 0. Rechazar enlaces observados en .claude y en el marcador antes de escribir. Mediana con 10 muestras, calentamiento y control intercalado.

**Subtareas**
- [x] Caracterizar comportamiento y observar primer oráculo declarado.
- [x] Implementar el alcance concreto y ejecutar las verificaciones dirigidas.
- [x] Medir, registrar evidencia y entregar a revisión/QA de F2.

**Notas**: Corrección de intento1 confirmada por revisión independiente2 sin gaps: `testing/f2-review-attempt2-2026-10-30.json`; RED previo, GREEN y fronteras en `testing/f2-review-fix1-2026-10-30.json`. Reabierta tras intento1 F2, gap F2-B01; RED dedicado observado antes del arreglo (2026-10-30), ver `testing/f2-review-attempt1-2026-10-30.json`. Estado al detectar el gap: corrección en curso; la nueva revisión independiente sigue pendiente. GREEN: 88 pass / 1 skip (enlace de fichero Windows sin privilegio), más 45 tests de runtime/adaptador; 0 fallos. Lint 0 errores/3 avisos genéricos, evals 192 e interop 88 vigentes. Control intercalado en la misma ruta temporal: Claude 1.616,995 a 577,301 ms (64,298 %), Codex 1.775,389 a 596,821 ms (66,384 %), OpenCode 2.123,034 a 644,218 ms (69,656 %); diez muestras por variante/runtime y calentamiento descartado, cero errores. No extrapolar a entrega nativa ni al path OneDrive. Recibos `testing/t09-functional-2026-10-29.json` y `testing/t09-paired-control-2026-10-29.json`. Revisión y CI Linux de la fase pendientes en T-19. RED: `node --test --test-name-pattern="claude: documentation marker works without Python or shell" tests/hook-docs-marker.test.mjs` falla: stderr `Git Bash unavailable; hook skipped` en lugar de crear el marcador sin intérpretes · 2026-10-29. Revalidada contra `a157679` (v2.1.0), 2026-10-29. Los ficheros de tests nuevos se declaran como entregables, no como pruebas ya ejecutadas. Oráculo y contratos concretos arriba. **Esqueleto histórico:** Esqueleto diferido. Clasificación: refactor; oráculo = test de equivalencia en ROJO antes del cambio. Patrón: filtros de ruta ya en node (`postApplies` en `run-hook.mjs`). Equivalencia con el adaptador de OpenCode (`hooks/opencode-plugin.js`). Se concreta al revalidar. Clasificación: refactor (comportamiento igual, sin Python). Coste estimado de la tarea: 183 € (horas × 50 € + tokens).


### T-10 — C-07 — Hook de ledger fusionado (`ledger-lint-warn` + `progress-line`)

- **Descripción**: Resultado: un solo Python en modo python del launcher parsea `tasks.md` una vez y emite los dos mensajes, conservando el debounce con lock (CA-07). Requisito: evaluation.md §C-07, spec §Criterios CA-07.
- **Changelog**: Unifica lint y progreso del ledger con un solo Python y análisis, debounce atómico y mensajes redactados; conserva los wrappers anteriores.
- **Estado**: completado
- **Cerrada**: 2026-10-30
- **Tiempo humano**: est. 7.2h · real —
- **Tiempo IA (ejec.)**: est. 2.98h · real —
- **Supervisión**: est. 0.74h (≈25 % IA) · real —
- **Previsión IA**: 1.2M in / 120k out tok · 7.18 €
- **Dependencias**: T-08
- **Tipo**: hooks
- **Archivos**: `hooks/ledger-post.py`, `hooks/ledger-lint-warn.sh`, `hooks/progress-line.sh`, `hooks/hooks.json`, `hooks/run-hook.mjs`, `hooks/opencode-plugin.js`, `agent-kits/shared/ledger-lint.py`, `agent-kits/shared/progress-report.py`, `tests/test_ledger_post.py`, `tests/test_console_encoding.py`, `tests/test_plugin_panel.py`, `skills/plugin-panel/scripts/build_panel.py`, `tests/hook-post-preflight.test.mjs`, `tests/hook-runtime.test.mjs`, `tests/opencode-plugin.test.mjs`, `tests/test_export_interop.py`, `tests/test_graphiti_security.py`, `scripts/export-interop.py`, `agent-kits/shared/doctor.py`, `agent-kits/shared/test_doctor.py`, `interop/**` (regenerado), `.codex-plugin/**`, `.agents/plugins/**`
- **Cubre (tests)**: —
- **Verificación**: `python -m pytest -q tests/test_ledger_post.py tests/test_ledger_lint.py agent-kits/shared/test_progress_report.py` → exit 0; tests nuevos se crean primero en RED antes del código correspondiente

**Criterios de aceptación**
- [x] CA-07: un Edit de tasks.md analiza el ledger una vez y conserva mensajes lint y progreso; un solo Python de negocio, sin shell, más supervisor Windows. Debounce con cerrojo y escritura atómica, una emisión para llamadas concurrentes idénticas. Mantener compatibilidad de las entradas antiguas y regenerar registros de tres runtimes.

**Subtareas**
- [x] Caracterizar comportamiento y observar primer oráculo declarado.
- [x] Implementar el alcance concreto y ejecutar las verificaciones dirigidas.
- [x] Medir, registrar evidencia y entregar a revisión/QA de F2.

**Seguimiento CI (2026-10-29)**: run `40905120413` sobre `0ed4a85` falla con 6 casos, 9.672 pass y 38 skip. RED local: mismos seis fallos; falta modo real de consola del hook nuevo y el panel rechaza su contrato OpenCode. Regresión adicional: catálogo nuevo rojo y legacy verde. Se registra payload de consola con consumidor temporal y se admiten solo los contratos completos legacy/combinado, comprobando handlers exactos. GREEN dirigido: 58 casos. Recibo `testing/t10-ci-0ed4a85-failed-2026-10-29.json`; suite completa de consola/panel: 766 pass, 2 skip, 182,84 s; linter 0 errores/3 avisos previos. CI `40908579625` sobre `97f5151`: verde; 9.684 pass / 38 skip / 82 subtests Python, 411 pass / 0 fail Node. Recibo `testing/t10-ci-97f5151-green-2026-10-29.json`.

**Notas**: Nuevo control final limpio, diez muestras y calentamiento por variante/runtime: Claude 9.004,689 a 2.693,599 ms (70,087 %), Codex 8.780,880 a 2.456,704 ms (72,022 %), OpenCode 8.045,168 a 2.098,828 ms (73,912 %); cero diagnósticos, sin ampliar 500 ms. Recibo `testing/t10-final-paired-control-2026-10-30.json`, fuente corregida y dependencias identificadas. El control anterior conserva siete avisos y sigue inconcluyente, no se reinterpreta como verde. Corrección de intento1 confirmada por revisión independiente2 sin gaps: `testing/f2-review-attempt2-2026-10-30.json`; RED previo, GREEN y fronteras en `testing/f2-review-fix1-2026-10-30.json`. Reabierta tras intento1 F2, gap F2-B01/F2-B02; RED dedicado observado antes del arreglo (2026-10-30), ver `testing/f2-review-attempt1-2026-10-30.json`. Estado al detectar el gap: corrección en curso; la nueva revisión independiente sigue pendiente. Cierre funcional: API compartida, seis llamadas concurrentes, tres runtimes sin Bash, egress/UTF-8/exportadores y smoke real OneDrive en verde. Comparación intercalada completa conserva **7 diagnósticos de confirmación de cierre**, en antes y después; **no acredita ahorro de latencia** y sus muestras fallidas no cuentan como éxitos. No se amplía el límite de 500 ms. `testing/t10-functional-2026-10-29.json`, `testing/t10-paired-control-2026-10-29.json`, recibo de autoverificación egress y diagnóstico del oráculo. La medición y el margen de cierre Windows se contrastan otra vez en el proceso T-19/spike T-15; la revisión independiente y CI completa siguen pendientes. Integración Windows inicial: 99 pass / 3 fail (dos fixtures seguían contando tres handlers y un oráculo temporal no aislaba spawn). Grupo posterior 8 pass / 1 fail, 1.380 ms frente a 1.000; tres aislados pasan. Control con 700 ms inyectados por spawn reproduce 2.301 ms, explicados por 1.119/1.174 ms síncronos. La prueba ahora retiene las consultas de actividad hasta que retorna el evento, mantiene el segundo y comprueba argv/payload de hijos reales tras liberar. Mutante que espera actividad falla por la dependencia retenida; mismo control lento pasa. Grupo corregido 9/9, seguridad egress 11/11, consola/exportadores 696/696. Diagnóstico `testing/t10-activity-oracle-diagnostic-2026-10-29.json`; no se reconstruye de forma única la causa del episodio histórico ni se cambia el runtime de actividad. RED de redacción: un token sintético del título aparece en mensaje/estado; se aplica el redactor canónico antes de emitir o guardar. GREEN: 14 tests nuevos / 1 skip. CI inicial de T-09 a0f3c50 conserva 2 fallos de huella no revisada, 9.651 pass; recibo histórico preservado. Revisión propia de frontera de red y cierre local explícito, con nuevos mutantes: 5 tests de seguridad pasan; no se presenta como revisión independiente T-19. RED adicional: `resumir(..., parsed=...)` falla por keyword no admitida; hook combinado ausente; registro nativo no contiene el handler nuevo (0 != 1). RED de interop: Codex conserva 3 handlers frente a 2 y OpenCode conserva dos handlers legacy frente al combinado · 2026-10-29. GREEN inicial: 61 tests Python / 1 skip y ejecución real en tres runtimes sin Bash; linter 0 errores/3 avisos. RED: `tests/test_ledger_post.py::test_lint_accepts_a_shared_parse_without_reopening_or_reparsing` falla con `TypeError: lint() got an unexpected keyword argument text` · 2026-10-29. El contrato nuevo permite reutilizar el mismo parse sin reabrir el ledger; antes del código. El debounce exigido es el del mensaje de progreso; lint conserva su informe en cada llamada, como antes. Revalidada contra `a157679` (v2.1.0), 2026-10-29. Los ficheros de tests nuevos se declaran como entregables, no como pruebas ya ejecutadas. Oráculo y contratos concretos arriba. **Esqueleto histórico:** Esqueleto diferido. Oráculo = test en ROJO de equivalencia de mensajes con los dos hooks actuales. Patrón: `hooks/ledger-lint-warn.sh`, `hooks/progress-line.sh`. Cambia la lista de hooks de `hooks/hooks.json` en 3 runtimes y lo que `/doctor` espera. Lente D. Se concreta al revalidar. Clasificación: refactor con salida idéntica. Coste estimado de la tarea: 367 € (horas × 50 € + tokens).


### T-11 — C-10 — Memoria gobernada condicional en `knowledge-check.md`

- **Descripción**: Resultado: los ~7k caracteres de «Consulta de la memoria gobernada» pasan a una referencia que solo se lee si el proyecto tiene memoria gobernada activa (ahorro estimado 10-14k tokens por ciclo; lo leen 8 agentes). Requisito: evaluation.md §C-10.
- **Changelog**: Difiere el detalle de memoria gobernada hasta que exista docs/knowledge en el consumidor; conserva consultas, doctrina del plugin, journal y contexto de código.
- **Estado**: completado
- **Cerrada**: 2026-10-29
- **Tiempo humano**: est. 4.8h · real —
- **Tiempo IA (ejec.)**: est. 1.99h · real —
- **Supervisión**: est. 0.50h (≈25 % IA) · real —
- **Previsión IA**: 0.8M in / 80k out tok · 4.78 €
- **Dependencias**: T-08
- **Tipo**: docs
- **Archivos**: `agent-kits/shared/knowledge-check.md`, `agent-kits/shared/knowledge-check-governed.md`, `tests/test_knowledge_prompt_split.py`, `tests/fixtures/knowledge-check-paragraphs.json`, `tests/test_knowledge_router.py`, `tests/test_graphiti_security.py`
- **Cubre (tests)**: —
- **Verificación**: `python -m pytest -q tests/test_knowledge_prompt_split.py tests/test_knowledge_router.py tests/test_graphiti_security.py` → exit 0; tests nuevos se crean primero en RED antes del código correspondiente

**Criterios de aceptación**
- [x] Condición determinista: existencia de docs/knowledge/ en el consumidor, conservando memoria legacy y approved, sin condicionar lectura local a backend remoto. Detalle gobernado cargado solo entonces; 0 párrafos perdidos, consultas y contratos de seguridad intactos. Registrar ahorro estimado por lectura/ciclo sin equipararlo a consumo API.

**Subtareas**
- [x] Caracterizar comportamiento y observar primer oráculo declarado.
- [x] Implementar el alcance concreto y ejecutar las verificaciones dirigidas.
- [x] Medir, registrar evidencia y entregar a revisión/QA de F2.

**Notas**: GREEN: 5 contratos estáticos y 171 tests de consultas/seguridad; cero párrafos perdidos por el helper oficial y hashes de todos los párrafos originales. Estimación chars/4: antes 2.284; núcleo 961; con memoria activa 2.531 (247 más, sin ahorro atribuido). Sin memoria: 1.323 tokens estimados menos por lectura; escenario ilustrativo de ocho lecturas 10.584. No son uso API ni calidad de activación medidos. Exportación portable 254 ficheros/0 problemas: el catálogo skills no selecciona este lector de agentes; si se selecciona el núcleo, su cierre incluye la referencia nueva. `testing/t11-conditional-memory-2026-10-29.json`. RED: `tests/test_knowledge_prompt_split.py::test_memory_detail_has_a_conditional_same_kit_reference` falla porque no existe el detalle gobernado extraído · 2026-10-29. La tabla incluye doctrina del plugin para evaluator aun sin memoria del consumidor: se conserva esa orden fuera de la condición. Journal y grafo de código permanecen en el núcleo. Revalidada contra `a157679` (v2.1.0), 2026-10-29. Los ficheros de tests nuevos se declaran como entregables, no como pruebas ya ejecutadas. Oráculo y contratos concretos arriba. **Esqueleto histórico:** Esqueleto diferido. Incógnita abierta de la evaluación: condición exacta de activación (¿`docs/knowledge/approved/`? ¿capacidad `kwipu`/`graphiti`?) — decidirla al revalidar con una condición determinista comprobable en una línea. Suites acopladas: `tests/test_knowledge_router.py`, `tests/test_graphiti_security.py`. Se concreta al revalidar. Clasificación: cambio de comportamiento (lectura condicional). Coste estimado de la tarea: 245 € (horas × 50 € + tokens).


### T-12 — C-06 — `session-context` en un único Python

- **Descripción**: Resultado: `hooks/session-context.sh` (315 líneas, 12 invocaciones de `python3`, 14-22 s) pasa a un único `session-context.py` que importa en proceso `journal`, `skill-index`, `progress-report` y `knowledge-find`; la salida por runtime es idéntica byte a byte (CA-06); permite bajar el timeout de SessionStart a 10 s. Requisito: evaluation.md §C-06, spec §Criterios CA-06.
- **Changelog**: Compone SessionStart en un Python de negocio, incluida la consulta del medidor en proceso; conserva salida por runtime y entrada shell directa.
- **Estado**: completado
- **Cerrada**: 2026-10-29
- **Tiempo humano**: est. 14.4h · real —
- **Tiempo IA (ejec.)**: est. 5.96h · real —
- **Supervisión**: est. 1.49h (≈25 % IA) · real —
- **Previsión IA**: 2.4M in / 240k out tok · 14.35 €
- **Dependencias**: T-08, T-11 (orden recomendado)
- **Tipo**: hooks
- **Archivos**: `hooks/session-context.sh`, `hooks/session-context.py`, `hooks/hooks.json`, `hooks/run-hook.mjs`, `agent-kits/shared/journal.py`, `agent-kits/shared/skill-index.py`, `agent-kits/shared/progress-report.py`, `agent-kits/shared/knowledge-find.py`, `agent-kits/shared/usage-meter.py`, `agent-kits/shared/test_progress_report.py`, `agent-kits/shared/test_usage_meter.py`, `tests/test_console_encoding.py`, `tests/test_graphiti_security.py`, `agent-kits/shared/test_review_resume.py`, `tests/test_session_context.py`, `tests/test_hooks_shell.py`, `tests/hook-runtime.test.mjs`, `tests/hook-budget.test.mjs`, `interop/**` (regenerado), `.codex-plugin/**`, `.agents/plugins/**`
- **Cubre (tests)**: —
- **Verificación**: `python -m pytest -q tests/test_session_context.py tests/test_hooks_shell.py; node --test tests/hook-runtime.test.mjs tests/hook-budget.test.mjs` → exit 0; tests nuevos se crean primero en RED antes del código correspondiente

**Criterios de aceptación**
- [x] CA-06: misma salida byte a byte y efectos propios sobre fixtures por runtime (startup/resume/compact, sin proyecto, índice off, replay, iniciativa ambigua, memoria y errores). Un solo Python de negocio, más supervisor Windows; sin subprocesos Python internos ni contaminación de globals. Mantener wrapper shell para invocación directa. Bajar timeout SessionStart a 10 s solo con prueba medida que satisface el criterio, sin ocultar fallos.

**Subtareas**
- [x] Caracterizar comportamiento y observar primer oráculo declarado.
- [x] Implementar el alcance concreto y ejecutar las verificaciones dirigidas.
- [x] Medir, registrar evidencia y entregar a revisión/QA de F2.

**Notas**: Seguimiento CI: run 40914558770 sobre 4bde93b conserva tres fallos de dobles con firma antigua, 9.731 pass / 38 skip / 82 subtests. Reproducción local 3 RED; commit 2823ac2 cambia sólo esos dobles a la firma keyword in_process, sin tocar aserciones ni producción; 18/18 casos de retoma pasan. Recibo testing/t12-ci-4bde93b-failed-2026-10-29.json, CI posterior pendiente. GREEN final: 156 casos de compositor/progreso/medidor, 26 de replay sin Python adicional y consola afectada, cuatro del lanzador nativo y cuatro de frontera egress. Comparación byte a byte: 30 combinaciones de fixture/runtime; recuperación real y marcadores abiertos/cerrados. La prueba de entorno poblado detectó un Python transitivo del medidor (3 RED): se incorpora API canónica status y keyword in_process, manteniendo CLI independiente con su timeout de 10 s. Las suites previas de 821 Python, 79 shell y 36 Node se conservan con su alcance, sin contarlas como validación final de ese delta. Medición intercalada: Claude 4.501,542 a 1.479,646 ms (67,130 %), Codex 4.548,668 a 1.387,995 ms (69,486 %), OpenCode 4.267,977 a 1.398,520 ms (67,232 %); diez muestras por variante/runtime, calentamiento descartado y cero errores. Se mantiene timeout 30 s: fixture temporal con índice/roadmap, sin corpus poblado ni outbox pendiente; no acredita bajar el límite global. CA-06 conserva un Python de negocio y salida equivalente. Recibos testing/t12-functional-2026-10-29.json, t12-paired-control-2026-10-29.json y t12-egress-boundary-review-2026-10-29.json; revisión independiente y CI de fase en T-19. RED: test_native_compositor_exists falla porque no existe el compositor de proceso único; launcher sin Bash falla con `Git Bash unavailable; hook skipped` · 2026-10-29. Regresión RED adicional: una consulta de memoria que retorna 1 filtra su stdout como éxito; ahora se respeta su código. GREEN inicial: cuatro ejecuciones CLI nativas, tres runtimes sin Bash y SessionStart normal. Comparación byte a byte y efectos sobre consumidores temporales en curso. No se ha bajado el timeout. Revalidada contra `a157679` (v2.1.0), 2026-10-29. Los ficheros de tests nuevos se declaran como entregables, no como pruebas ya ejecutadas. Oráculo y contratos concretos arriba. **Esqueleto histórico:** Esqueleto diferido. Oráculo = test de caracterización de salida por runtime en ROJO. Riesgo: estado global de los módulos importados contamina la salida; es la característica de F2 con más probabilidad de agotar los 3 intentos. Incógnita: ¿se conserva `session-context.sh` como envoltorio sin node? Lente D. Se concreta al revalidar. Clasificación: refactor de alto riesgo con salida idéntica. Coste estimado de la tarea: 734 € (horas × 50 € + tokens).


### T-13 — C-09 — `dev-cycle.md` núcleo + fases bajo demanda

- **Descripción**: Resultado: `commands/dev-cycle.md` (546 líneas, 55 KB, ~15,4k tokens) se separa en un núcleo y referencias por fase (Fase 2, ciclo Jira, subagentes/Knowledge Gate) con «lee X solo al llegar a Y»; `quick-implement` deja de leerlo entero; ahorro ≥ 6k tokens por vía rápida; 0 párrafos perdidos. Requisito: evaluation.md §C-09, ADR-008, spec §Criterios.
- **Changelog**: Difiere detalles de fases de dev-cycle a referencias privadas, conservando puertas, recetas y dueños; reduce lectura estimada de la vía rápida por defecto.
- **Estado**: completado
- **Cerrada**: 2026-10-29
- **Tiempo humano**: est. 16.8h · real —
- **Tiempo IA (ejec.)**: est. 7.45h · real —
- **Supervisión**: est. 1.86h (≈25 % IA) · real —
- **Previsión IA**: 3.0M in / 300k out tok · 17.94 €
- **Dependencias**: T-08
- **Tipo**: docs
- **Archivos**: `commands/dev-cycle.md`, `agent-kits/dev-cycle/references/*.md`, `skills/quick-implement/SKILL.md`, `scripts/export-interop.py`, `tests/test_dev_cycle_split.py`, `tests/fixtures/dev-cycle-paragraphs.json`, `tests/test_plan_review_caller.py`, `tests/test_review_jira_owner.py`, `tests/installer.test.mjs`, `tests/test_skill_size.py`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `interop/**` (regenerado), `.codex-plugin/**`, `.agents/plugins/**`
- **Cubre (tests)**: —
- **Verificación**: `python -m pytest -q tests/test_dev_cycle_split.py tests/test_skill_size.py tests/test_plan_review_caller.py tests/test_project_pieces.py tests/test_review_jira_owner.py tests/test_graphiti_security.py; python scripts/export-interop.py --check` → exit 0; tests nuevos se crean primero en RED antes del código correspondiente

**Criterios de aceptación**
- [x] Núcleo y fases resueltas por regla 5 en agent-kits/dev-cycle/references; vía rápida sin cargar fases ajenas con ahorro estimado >= 6.000 tokens. Cero párrafos perdidos; preservar puertas, identidad de dueños Jira/Knowledge Gate y contratos Bash/PowerShell; exportaciones e instalador transportan todas las referencias.

**Subtareas**
- [x] Caracterizar comportamiento y observar primer oráculo declarado.
- [x] Implementar el alcance concreto y ejecutar las verificaciones dirigidas.
- [x] Medir, registrar evidencia y entregar a revisión/QA de F2.

**Notas**: Autorrevisión del núcleo: RED exige la ruta canónica completa de candidatos; se añade y se precisa que una revisión de plan pendiente puede requerir el detalle de Fase 2 al retomar. GREEN: 407 pass / 1 skip en suites ampliadas; 43 casos de recetas reales Bash/PowerShell y dueños Jira; cuatro resoluciones del kit en shells reales y una instalación Codex con bytes de las cinco referencias iguales al origen. 0 párrafos perdidos (81 del comando y todos los originales de quick-implement), ocho recetas LF idénticas y puertas comunes conservadas en el núcleo. Estimación chars/4 del readset rápido por defecto: 15.066 a 8.739 (6.327 menos); comandos nativos directos Codex 6.361 y OpenCode 6.363 menos. Jira/subagentes/candidatos activos cargan su detalle y el ahorro puede bajar de 6.000; no se afirma un ahorro universal ni consumo API o calidad de activación medidos. Recibo testing/t13-prompt-split-2026-10-29.json. Linter 0 errores/3 avisos previos; evals 192/0 errores e interop 88 vigentes. Revisión independiente y CI completa pendientes en T-19. RED: test_phase_details_have_a_private_owner_and_lazy_routes falla por referencia privada ausente, antes del cambio; adaptador nativo sin etiqueta de núcleo también rojo · 2026-10-29. GREEN inicial: cinco contratos, 43 casos reales de recetas Bash/PowerShell y dueños Jira. La suite previa conservó 15 fail / 10 pass / 13 skip: 13 recetas sólo buscaban el fichero raíz, faltaba la tabla movida y un escáner local recorría clones históricos dentro de .pytest_cache. Se cambia la fuente exacta de recetas, se inspecciona el cierre canónico de cinco referencias y se excluye sólo esa caché de pruebas del escaneo vivo. Las aserciones de dueños/firmas se conservan. Revalidada contra `a157679` (v2.1.0), 2026-10-29. Los ficheros de tests nuevos se declaran como entregables, no como pruebas ya ejecutadas. Oráculo y contratos concretos arriba. **Esqueleto histórico:** Esqueleto diferido. Incógnita abierta: dónde viven las referencias de un comando (los comandos no tienen `references/`) y cómo las resuelve la regla 5 en Codex/OpenCode — decidir al revalidar (candidato a nota de diseño). 6 suites acopladas (`test_lint_plugin.py`, `test_plan_review_caller.py`, `test_project_pieces.py`, `test_review_jira_owner.py`, `test_graphiti_security.py`, `installer.test.mjs`) y `tests/test_skill_size.py --diet-check`. Se concreta al revalidar. Clasificación: refactor de alto riesgo (comportamiento del orquestador). Coste estimado de la tarea: 858 € (horas × 50 € + tokens).


### T-14 — C-16 — `review-lens-select` con una lectura por fichero

- **Descripción**: Resultado: el script abre cada fichero una sola vez y aplica los dos análisis sobre el mismo contenido (38 s con 1.081 ficheros hoy). Decidido «sí» en la puerta. Requisito: evaluation.md §C-16.
- **Changelog**: Comparte una lectura por fichero en el selector C/D, conservando motivos, exclusiones y detección de binarios.
- **Estado**: completado
- **Cerrada**: 2026-10-30
- **Tiempo humano**: est. 2.4h · real —
- **Tiempo IA (ejec.)**: est. 0.99h · real —
- **Supervisión**: est. 0.25h (≈25 % IA) · real —
- **Previsión IA**: 0.4M in / 40k out tok · 2.39 €
- **Dependencias**: T-08
- **Tipo**: backend
- **Archivos**: `skills/adversarial-review/scripts/review-lens-select.py`, `skills/adversarial-review/scripts/test_review_lens_select.py`
- **Cubre (tests)**: 58 casos del selector, incluidos 13 nuevos de IO/lectura; 30 de copias declaradas y 8 de consola.
- **Verificación**: `python -m pytest -q skills/adversarial-review/scripts/test_review_lens_select.py` → exit 0; tests nuevos se crean primero en RED antes del código correspondiente

**Criterios de aceptación**
- [x] Mismo veredicto C/D y motivos, con una apertura de contenido por fichero en --files y fallback untracked. Detectar binarios antes de analizar y mantener lecturas acotadas, errores y exclusiones. Verificar conteo de IO con test dedicado y comparación medida de diff grande con control intercalado.

**Subtareas**
- [x] Caracterizar comportamiento y observar primer oráculo declarado.
- [x] Implementar el alcance concreto y ejecutar las verificaciones dirigidas.
- [x] Medir, registrar evidencia y entregar a revisión/QA de F2.

**Notas**: Control final tras F2-D01: files 3.831,304 a 1.823,797 ms (52,397 %), untracked 5.614,099 a 3.554,042 ms (36,694 %), tracked 7.785,971 a 5.746,383 ms (26,196 %). Diez muestras/variante/modo, calentamiento, 33 pares JSON/stderr iguales y cero fallos; `testing/t14-paired-control-final-2026-10-30.json`. La medición inicial anterior se conserva con su fuente, sin atribuirla a los bytes nuevos. Regresión dedicada cuenta trabajo lineal para un bundle minificado de 4 MiB, sin deadline de host. Corrección de intento1 confirmada por revisión independiente2 sin gaps: `testing/f2-review-attempt2-2026-10-30.json`; RED previo, GREEN y fronteras en `testing/f2-review-fix1-2026-10-30.json`. Reabierta tras intento1 F2, gap F2-D01; RED dedicado observado antes del arreglo (2026-10-30), ver `testing/f2-review-attempt1-2026-10-30.json`. Estado al detectar el gap: corrección en curso; la nueva revisión independiente sigue pendiente. RED: `test_una_apertura_comparte_lineas_y_cabecera` conserva los motivos C/D esperados pero cuenta 4 aperturas en `--files` y fallback untracked, y 2 en tracked frente a 1 · 2026-10-30. La instrumentación usa rutas reales para reconocer tanto el alias Windows 8.3 temporal como el nombre largo de Git. GREEN dirigido: 3 casos de una apertura y 10 casos adicionales de lectura/aislamiento pasan. Cabecera de 8.192 caracteres y sondeo binario de 8.192 bytes; lectura UTF-8 incremental acotada, sin releer bytes ni cachear entre ejecuciones. GREEN: 88 casos selector/copias en 166,36 s y 8 de consola en 2,02 s. Control intercalado con 1.081 ficheros: files 5.947,799 a 1.872,201 ms (68,523 %); untracked 6.741,646 a 2.507,304 ms (62,809 %); tracked 4.538,717 a 2.804,780 ms (38,203 %). Diez muestras por variante/modo y calentamiento descartado; 33 pares con JSON/stderr idénticos y cero errores. Fixture temporal fuera de OneDrive; no reproduce la cifra histórica de 38 s ni mide entrega nativa. Lint 0 errores/3 avisos previos, evals 192/0 errores, interop 88 vigentes. Recibos `testing/t14-functional-2026-10-30.json` y `testing/t14-paired-control-2026-10-30.json`. Revisión independiente, cobertura y CI de fase siguen en T-19; la CI de T-13 8e8bcb4 terminó verde (40920644178), sin extrapolar al nuevo cambio. Revalidada contra `a157679` (v2.1.0), 2026-10-29. Los ficheros de tests nuevos se declaran como entregables, no como pruebas ya ejecutadas. Oráculo y contratos concretos arriba. **Esqueleto histórico:** Esqueleto diferido. Oráculo = test de equivalencia de veredicto en ROJO. Patrón: `skills/adversarial-review/scripts/review-lens-select.py` y su test. Lente D. Se concreta al revalidar. Clasificación: refactor de rendimiento. Coste estimado de la tarea: 122 € (horas × 50 € + tokens).


### T-15 — C-15 (spike, 2 h) — ¿Cierre del Job Object sin segundo Python?

- **Descripción**: Resultado: decisión go/no-go documentada sobre si el supervisor puede cerrar el Job Object en salida limpia (o node soltar el handle) sin perder la limpieza de procesos nietos; hoy cada hook paga un Python extra en Windows (`hooks/run-hook.mjs:233-240`, `:316`). Requisito: evaluation.md §C-15 y decisión 2 de la puerta (solo entra si el spike sale bien).
- **Changelog**: Conserva la limpieza confirmada de procesos Windows tras descartar alternativas sin garantía equivalente.
- **Cerrada**: 2026-10-30
- **Estado**: completado
- **Tiempo humano**: est. 2.4h · real —
- **Tiempo IA (ejec.)**: est. 0.80h · real —
- **Supervisión**: est. 0.20h (≈25 % IA) · real —
- **Previsión IA**: 0.3M in / 30k out tok · 1.79 €
- **Dependencias**: T-08
- **Tipo**: hooks
- **Archivos**: `docs/roadmap/2026-10-27-plugin-optimization/testing/spike-c15.md`, `docs/roadmap/2026-10-27-plugin-optimization/testing/t15-windows-experiment.json`
- **Cubre (tests)**: —
- **Verificación**: `lectura: testing/spike-c15.md y testing/t15-windows-experiment.json, con comandos reales, estados terminales y decisión go/no-go, sin cambio de producción` → exit 0; tests nuevos se crean primero en RED antes del código correspondiente

**Criterios de aceptación**
- [x] Spike Windows acotado a 2 h: medir propiedad/cierre de Job Object y terminación de hijos/nietos propios tanto en salida limpia como timeout y cancelación. Go solo con garantía equivalente y una invocación Python menos; si exige dependencia nativa o rediseño no presupuestado, no-go motivado y T-16 cancelada.

**Subtareas**
- [x] Caracterizar comportamiento y observar primer oráculo declarado.
- [x] Implementar el alcance concreto y ejecutar las verificaciones dirigidas.
- [x] Medir, registrar evidencia y entregar a revisión/QA de F2.

**Notas**: TDD n/a: investigación, sin código productivo nuevo. **NO-GO** con evidencia en `testing/spike-c15.md` y `testing/t15-windows-experiment.json`: 21 muestras finales con barrera y handles observados; las tres generaciones terminan en todas. En 6/9 salidas del propietario queda algún proceso propio vivo al primer sondeo posterior; cierre desde dentro no retorna para confirmar (3/3), fs.closeSync devuelve EBADF (3/3). Cierre actual confirma 6/6 dentro de 500 ms. Se conserva el primer arnes sin barrera como diagnóstico, no aceptación. Hashes de lanzador/supervisor idénticos antes/después; 15 tests de supervisor pasan en 0,60 s. Investigación dentro de 2 h; sin dependencia ni rediseño nativo. No acredita 100 ejecuciones ni subsana el benchmark T-10. T-16 se cancela por la condición aprobada. Revalidada contra `a157679` (v2.1.0), 2026-10-29. Los ficheros de tests nuevos se declaran como entregables, no como pruebas ya ejecutadas. Oráculo y contratos concretos arriba. **Esqueleto histórico:** Esqueleto diferido. Riesgo alto: el supervisor existe por los gotchas de hooks-runtime (huérfanos). El spike NO modifica código de producción: produce una nota con medidas y la decisión. Si es no-go, T-16 se cancela con el motivo citado en Notas (decisión autorizada por la puerta). Lente C y D en la implementación posterior. Clasificación: investigación (go/no-go). Coste estimado de la tarea: 122 € (horas × 50 € + tokens).


### T-16 — C-15 (implementación, condicional al spike) — Cierre del Job Object sin segundo Python

- **Descripción**: Resultado: si T-15 es go, el supervisor cierra el job en salida limpia sin lanzar un segundo Python por hook, sin dejar procesos vivos. Requisito: evaluation.md §C-15. Se cancela con motivo si T-15 es no-go.
- **Changelog**: Sin implementación: el spike no acredita un cierre sin helper con garantía equivalente.
- **Cerrada**: 2026-10-30
- **Estado**: cancelado
- **Tiempo humano**: est. 7.2h · real —
- **Tiempo IA (ejec.)**: est. 3.17h · real —
- **Supervisión**: est. 0.79h (≈25 % IA) · real —
- **Previsión IA**: 1.3M in / 130k out tok · 7.77 €
- **Dependencias**: T-15 (go)
- **Tipo**: hooks
- **Archivos**: `hooks/run-hook.mjs`, `hooks/runtime-supervisor.py`, `tests/test_hook_supervisor.py`, `tests/hook-budget.test.mjs`, `tests/hook-runtime.test.mjs`, `interop/**` (regenerado), `.codex-plugin/**`, `.agents/plugins/**`
- **Cubre (tests)**: —
- **Verificación**: `python -m pytest -q tests/test_hook_supervisor.py; node --test tests/hook-budget.test.mjs tests/hook-runtime.test.mjs` → exit 0; tests nuevos se crean primero en RED antes del código correspondiente

**Criterios de aceptación**
- [ ] Solo si T-15 es go. Cero procesos propios vivos tras 100 ejecuciones, incluidas salida limpia, timeout y cancelación; una invocación Python menos en Windows. C/D obligatorias y mutante de limpieza rechazado. Sin go, cancelar con enlace al experimento.

**Subtareas**
- [ ] Caracterizar comportamiento y observar primer oráculo declarado.
- [ ] Implementar el alcance concreto y ejecutar las verificaciones dirigidas.
- [ ] Medir, registrar evidencia y entregar a revisión/QA de F2.

**Notas**: **Cancelada, no implementada.** T-15 concluye no-go dentro del alcance aprobado: `testing/spike-c15.md` y recibo `testing/t15-windows-experiment.json`. La condición de entrada no se cumple; no se ejecutan las 100 pasadas de aceptación de una implementación inexistente ni se cuentan como superadas las revisiones C/D. Supervisor y presupuestos conservados. TDD n/a: cancelación condicional sin cambio productivo. Revalidada contra `a157679` (v2.1.0), 2026-10-29. Los ficheros de tests nuevos se declaran como entregables, no como pruebas ya ejecutadas. Oráculo y contratos concretos arriba. **Esqueleto histórico:** Esqueleto diferido y condicional. Suites: `tests/test_hook_supervisor.py`, `tests/hook-budget.test.mjs`. Lente C y D obligatorias. Se concreta al revalidar. Clasificación: refactor de alto riesgo, condicional. Coste estimado de la tarea: 368 € (horas × 50 € + tokens).


### T-17 — C-17 — Kit shared resuelto una vez por fichero (se decide al abrir F2)

- **Descripción**: Resultado: cada agente/comando resuelve `$SHAREDKIT` una sola vez al principio (el `find` de 6 raíces aparece ~80 veces, ~1.200 tokens por `/dev-cycle`). Requisito: evaluation.md §C-17. Se decide en T-08 con los datos de C-01 y C-09; mejor después de T-13.
- **Changelog**: No se modifica la resolución shared: el candidato conservador no acredita ahorro positivo.
- **Cerrada**: 2026-10-30
- **Estado**: cancelado
- **Tiempo humano**: est. 4.8h · real —
- **Tiempo IA (ejec.)**: est. 1.99h · real —
- **Supervisión**: est. 0.50h (≈25 % IA) · real —
- **Previsión IA**: 0.8M in / 80k out tok · 4.78 €
- **Dependencias**: T-08, T-13
- **Archivos**: `agents/*.md`, `commands/*.md`, `agent-kits/shared/*.md`, `agent-kits/dev-cycle/references/*.md`, `scripts/lint_plugin.py`, `tests/test_shared_resolution.py`, `interop/**` (regenerado), `.codex-plugin/**`, `.agents/plugins/**`
- **Cubre (tests)**: —
- **Verificación**: `python -m pytest -q tests/test_shared_resolution.py tests/test_lint_plugin.py; python scripts/export-interop.py --check` → exit 0; tests nuevos se crean primero en RED antes del código correspondiente

**Criterios de aceptación**
- [ ] Go condicionado a T-13: resolver bundle una vez por pieza y reutilizar la ruta observada, reasignándola en cada bloque shell nuevo; nunca asumir entorno persistente. Mantener seis raíces y precedencia proyecto/usuario, degradación parcial y regla 5. Ahorro por dev-cycle medido; si no es positivo o no es seguro, registrar no-go en vez de debilitar resolución.

**Subtareas**
- [ ] Caracterizar comportamiento y observar primer oráculo declarado.
- [ ] Implementar el alcance concreto y ejecutar las verificaciones dirigidas.
- [ ] Medir, registrar evidencia y entregar a revisión/QA de F2.

**Notas**: **Cancelada, no implementada** por no-go medido en `testing/t17-resolution-decision.md` y `.json`. Se observan 24 asignaciones en 20 piezas, solo tres con duplicados locales. Candidato conserva seis raíces, procedencia/fallbacks y reasignación en cada shell nuevo: delta estimado +270 vía rápida, +420 flujo completo y +77 incluso en las tres piezas duplicadas (chars/4, no API). No se afirma imposibilidad de otro diseño futuro; no cumple la condición de ahorro y se conserva el mecanismo actual. Cuatro pruebas existentes del kit privado pasan en 7,97 s; no se atribuyen a una resolución shared nueva. TDD n/a: cancelación condicional sin cambio de prompts/linter; no nace `tests/test_shared_resolution.py`. Revalidada contra `a157679` (v2.1.0), 2026-10-29. Los ficheros de tests nuevos se declaran como entregables, no como pruebas ya ejecutadas. Oráculo y contratos concretos arriba. **Esqueleto histórico:** Esqueleto diferido. Incógnita: mecanismo (los shells no comparten estado entre llamadas Bash: variable por bloque o ruta escrita por el agente). Acoplado a la regla 5 de `lint_plugin.py`. Se concreta al revalidar. Clasificación: refactor de prosa, condicional. Coste estimado de la tarea: 245 € (horas × 50 € + tokens).


### T-18 — C-18 — `skill-index` solo con nombres en Claude Code (se decide al abrir F2)

- **Descripción**: Resultado: en Claude Code el índice de SessionStart se reduce a nombres (o nada) para ahorrar ~650 tokens por sesión; Codex/OpenCode quedan igual. Requisito: evaluation.md §C-18. Solo si, tras C-01, las skills ya aparecen en el listado nativo; si no, el índice compacto es la única forma de que el modelo las conozca.
- **Changelog**: Se conserva el índice completo: la visibilidad nativa no prueba activación sin degradación.
- **Cerrada**: 2026-10-30
- **Estado**: cancelado
- **Tiempo humano**: est. 2.4h · real —
- **Tiempo IA (ejec.)**: est. 0.99h · real —
- **Supervisión**: est. 0.25h (≈25 % IA) · real —
- **Previsión IA**: 0.4M in / 40k out tok · 2.39 €
- **Dependencias**: T-08, T-06
- **Tipo**: hooks
- **Archivos**: `agent-kits/shared/skill-index.py`, `hooks/session-context.sh`, `agent-kits/shared/test_skill_index.py`, `docs/roadmap/2026-10-27-plugin-optimization/testing/t18-activation-decision.md`, `interop/**` (regenerado), `.codex-plugin/**`, `.agents/plugins/**`
- **Cubre (tests)**: —
- **Verificación**: `lectura: testing/t18-activation-decision.md; python -m pytest -q agent-kits/shared/test_skill_index.py` → exit 0; tests nuevos se crean primero en RED antes del código correspondiente

**Criterios de aceptación**
- [ ] Decisión inicial no-go para recorte productivo: la sesión nativa F1 acredita visibilidad, pero no no-degradación de activación. Conservar índice completo en Claude y otros runtimes. Si se obtiene comparación de activación válida antes de T-19, reconsiderar explícitamente; no sustituirla por evals literales. La tarea condicional se cancela con el motivo registrado.

**Subtareas**
- [ ] Caracterizar comportamiento y observar primer oráculo declarado.
- [ ] Implementar el alcance concreto y ejecutar las verificaciones dirigidas.
- [ ] Medir, registrar evidencia y entregar a revisión/QA de F2.

**Notas**: **Cancelada, no implementada** por la condición aprobada en T-08: `testing/t18-activation-decision.md` y recibo `.json`. La sesión nativa F1 ve 27 skills/descripciones pero no usa Skill ni compara activación con/sin índice. Sin evidencia nueva equivalente no se recorta Claude ni otros runtimes, ni se afirma el ahorro de 650. Suite existente `agent-kits/shared/test_skill_index.py`: 23 pass en 34,75 s. TDD n/a: cancelación condicional, sin código productivo nuevo. Evals y pruebas de índice no sustituyen la calidad de activación. Revalidada contra `a157679` (v2.1.0), 2026-10-29. Los ficheros de tests nuevos se declaran como entregables, no como pruebas ya ejecutadas. Oráculo y contratos concretos arriba. **Esqueleto histórico:** Esqueleto diferido. Interactúa con T-06 y T-12. Se decide en T-08 con la medición de T-06. Se concreta al revalidar. Clasificación: cambio de comportamiento, condicional. Coste estimado de la tarea: 122 € (horas × 50 € + tokens).


### T-19 — P-F2 — Proceso de la fase 2: revisión, CHANGELOG doble, Linux y release

- **Descripción**: Resultado: F2 cerrada y publicada: revisión de la fase, tabla antes/después del benchmark, CHANGELOG ES/EN, docs espejo, interop, réplica Linux y `scripts/release.py`. Requisito: evaluation.md §P-F2 y decisión 6 de la puerta.
- **Changelog**:
- **Estado**: en-progreso
- **Tiempo humano**: est. 2.4h · real —
- **Tiempo IA (ejec.)**: est. 0.64h · real —
- **Supervisión**: est. 0.16h (≈25 % IA) · real —
- **Previsión IA**: 0.3M in / 30k out tok · 1.79 €
- **Dependencias**: T-09, T-10, T-11, T-12, T-13, T-14
- **Tipo**: devops
- **Archivos**: `CHANGELOG.md`, `CHANGELOG.es.md`, `docs/observability.md`, `docs/en/observability.md`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `docs/roadmap/README.md`, `docs/roadmap/2026-10-27-plugin-optimization/testing/**`
- **Cubre (tests)**: —
- **Verificación**: `python agent-kits/shared/ledger-lint.py docs/roadmap/2026-10-27-plugin-optimization/tasks.md; python scripts/export-interop.py --check; lectura: CI Linux completa y scripts/release.py con versión confirmada` → exit 0; tests nuevos se crean primero en RED antes del código correspondiente

**Criterios de aceptación**
- [ ] F2 revisada en <= 3 intentos; CA funcionales, tablas antes/después con controles, cobertura cambiada >= 90 según gate oficial, lint/evals/interop verdes; CI completa Linux sin rojos aceptados, notas ES/EN y docs espejo. Publicar por release.py tras confirmar versión. Las tareas condicionales canceladas conservan su motivo y no se cuentan como implementadas.

**Subtareas**
- [ ] Caracterizar comportamiento y observar primer oráculo declarado.
- [ ] Implementar el alcance concreto y ejecutar las verificaciones dirigidas.
- [ ] Medir, registrar evidencia y entregar a revisión/QA de F2.

**Notas**: Revalidada contra `a157679` (v2.1.0), 2026-10-29. Los ficheros de tests nuevos se declaran como entregables, no como pruebas ya ejecutadas. Oráculo y contratos concretos arriba. **Esqueleto histórico:** Esqueleto diferido; mismo procedimiento que T-07. Se concreta al revalidar. Clasificación: proceso. Coste estimado de la tarea: 122 € (horas × 50 € + tokens).

---

## Fase 3 — Modelos locales

**Estado**: borrador · **Estimado**: 45.0h · **Real**: — · **Coste est.**: 2294 € · **Tokens est.**: 7.3M in / 730k out. **Diferida**: esqueleto, se concreta al revalidar (primera tarea de la fase).

### T-20 — Revalidar el plan de F3 contra `master`

- **Descripción**: Resultado: el esqueleto de F3 (T-21..T-26) queda confirmado o reajustado contra el `master` posterior a la release de F2. Requisito: decisión 2 de la puerta (+0,5 h por fase diferida).
- **Changelog**:
- **Estado**: borrador
- **Tiempo humano**: est. 0.6h · real —
- **Tiempo IA (ejec.)**: est. 0.10h · real —
- **Supervisión**: est. 0.03h (≈25 % IA) · real —
- **Previsión IA**: 0.0M in / 0k out tok · 0.00 €
- **Dependencias**: T-19 (release de F2 publicada)
- **Tipo**: docs
- **Archivos**: `docs/roadmap/2026-10-27-plugin-optimization/improvement-plan.md`, `docs/roadmap/2026-10-27-plugin-optimization/tasks.md`
- **Cubre (tests)**: —
- **Verificación**: `python3 agent-kits/shared/ledger-lint.py docs/roadmap/2026-10-27-plugin-optimization/tasks.md` → exit 0 tras el reajuste

**Criterios de aceptación**
- [ ] Cada tarea T-21..T-26 tiene `Verificación` y `Archivos` concretos y vigentes contra `master`.
- [ ] Las estimaciones de F3 se recalculan con el real de F1/F2; la diferencia queda anotada.

**Subtareas**
- [ ] Comparar `master` con la base del plan.
- [ ] Concretar verificaciones y archivos de F3.

**Notas**: Primera tarea de F3. Concretar `Verificación`/`Archivos` marcados «se concreta al revalidar». Recordar la validación de F3: estática + prueba manual del usuario en otro equipo con Ollama (decisión 7 de la puerta). Clasificación: proceso. Coste estimado de la tarea: 30 € (horas × 50 € + tokens).


### T-21 — Paso `architect` — diseño de C-11 (formato de ids y dónde vive el mapeo) y C-13 (qué recorta `lite`)

- **Descripción**: Resultado: `design.md` aprobado por el usuario con la opción elegida para (a) el formato de ids en OpenCode (`ollama/qwen3:32b`) frente a Codex (`model` + `model_provider`) y dónde vive el mapeo del consumidor (instalador o `dev.json` leído en runtime, sin romper el determinismo de interop), y (b) el alcance del perfil `lite`: solo recorta paralelismo y contexto, NO toca la revisión de dos lentes ni el `qa-gate` (decisión 3 de la puerta). Requisito: decisión 4 de la puerta; evaluation.md §C-11, §C-13.
- **Changelog**:
- **Estado**: borrador
- **Tiempo humano**: est. 0.0h · real —
- **Tiempo IA (ejec.)**: est. 0.00h · real —
- **Supervisión**: est. 0.00h (≈25 % IA) · real —
- **Previsión IA**: 0.0M in / 0k out tok · 0.00 €
- **Dependencias**: T-20
- **Tipo**: docs
- **Archivos**: `docs/roadmap/2026-10-27-plugin-optimization/design.md`, `docs/roadmap/2026-10-27-plugin-optimization/improvement-plan.md`
- **Cubre (tests)**: —
- **Verificación**: lectura: `design.md` con `estado: aprobado` y opción elegida O<n>; `python3 agent-kits/shared/ledger-lint.py docs/roadmap/2026-10-27-plugin-optimization/tasks.md` → exit 0

**Criterios de aceptación**
- [ ] `design.md` aprobado cubre formato de ids por runtime, ubicación del mapeo y alcance de `lite`.
- [ ] T-22..T-26 reajustadas al diseño, con la diferencia anotada en el `Changelog del plan`.

**Subtareas**
- [ ] Invocar `architect` sobre C-11 y C-13.
- [ ] Validar con el usuario por trozos.
- [ ] Reajustar tareas.

**Notas**: El coste del paso `architect` NO está presupuestado en la evaluación (0 h aquí); se mide con su propio `usage-meter` en `design.md`. Tras aprobarlo: `design: design.md` en el frontmatter de este plan y `plan: improvement-plan.md` en el del diseño; reajustar T-22..T-26 si cambia el alcance. ADR `propuesta` vía `knowledge-curation.py propose`. Clasificación: proceso (decisión de diseño). Coste estimado de la tarea: 0 € (horas × 50 € + tokens).


### T-22 — C-11 — Ids no Claude en `dev.json` y `model` en interop

- **Descripción**: Resultado: `model-tier.py` admite ids de proveedor local y `export-interop.py` emite `model` en `interop/opencode/agents` y `interop/codex/agents/*.toml` cuando haya mapeo, sin romper el determinismo (`--check`); ADR-009 revisado (CA-08). Requisito: evaluation.md §C-11, spec §Criterios CA-08.
- **Changelog**:
- **Estado**: borrador
- **Tiempo humano**: est. 12.0h · real —
- **Tiempo IA (ejec.)**: est. 4.96h · real —
- **Supervisión**: est. 1.24h (≈25 % IA) · real —
- **Previsión IA**: 2.0M in / 200k out tok · 11.96 €
- **Dependencias**: T-21
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/model-tier.py`, `scripts/export-interop.py`, `install/install.mjs`, `tests/test_export_interop.py`, `docs/INTEROP.md`, `docs/en/INTEROP.md`, `interop/**` (regenerado: `hooks/`|`agents/`|`commands/` tocados), `.codex-plugin/**`, `.agents/plugins/**`
- **Cubre (tests)**: —
- **Verificación**: lectura: se concreta al revalidar (T-08/T-20 del plan); no inventar comandos que aún no existen

**Criterios de aceptación**
- [ ] Criterio (esqueleto): CA-08 — `model-tier.py` acepta ids locales y los agentes de Codex/OpenCode llevan su `model`. Se concreta al revalidar.

**Subtareas**
- [ ] Se concreta al revalidar.

**Notas**: Esqueleto diferido; depende del diseño de T-21. Hoy `MODELOS_ALIAS` + `^claude-` (`agent-kits/shared/model-tier.py:43-49`) y solo `model_reasoning_effort` en `scripts/export-interop.py:464`. Se concreta al revalidar. Clasificación: capacidad nueva / cambio de comportamiento. Coste estimado de la tarea: 612 € (horas × 50 € + tokens).


### T-23 — C-12 — `ledger-write.py`

- **Descripción**: Resultado: script determinista con subcomandos para marcar estado de tarea, añadir evidencia `RED:` y abrir la cabecera `## Revisión de dos lentes — intento N:`, con lock y reescritura eficiente; `ledger-lint` lo valida (CA-09). Requisito: evaluation.md §C-12, spec §Criterios CA-09.
- **Changelog**:
- **Estado**: borrador
- **Tiempo humano**: est. 14.4h · real —
- **Tiempo IA (ejec.)**: est. 5.96h · real —
- **Supervisión**: est. 1.49h (≈25 % IA) · real —
- **Previsión IA**: 2.4M in / 240k out tok · 14.35 €
- **Dependencias**: T-21, T-13
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/ledger-write.py`, `agent-kits/shared/ledger-lint.py`, `agents/implementer.md`, `skills/adversarial-review/SKILL.md`, `skills/tdd/SKILL.md`, `commands/dev-cycle.md`, `agent-kits/shared/task-brief.py`, `interop/**` (regenerado: `hooks/`|`agents/`|`commands/` tocados), `.codex-plugin/**`, `.agents/plugins/**`
- **Cubre (tests)**: —
- **Verificación**: lectura: se concreta al revalidar (T-08/T-20 del plan); no inventar comandos que aún no existen

**Criterios de aceptación**
- [ ] Criterio (esqueleto): CA-09 — marcar con `ledger-write.py` deja el ledger sin avisos de `ledger-lint` y en formato canónico. Se concreta al revalidar.

**Subtareas**
- [ ] Se concreta al revalidar.

**Notas**: Esqueleto diferido. Dueño único del formato: `ledger-lint` valida y `ledger-write` escribe. Riesgos: concurrencia (lock) y ledgers de 260-520 KB. Incógnita: ¿obligatorio también para Claude o solo en `lite`? (lo resuelve T-21). Depende de C-09 para no editar `dev-cycle.md` monolítico. Se concreta al revalidar. Clasificación: capacidad nueva. Coste estimado de la tarea: 734 € (horas × 50 € + tokens).


### T-24 — C-14 — Aviso de contexto corto en `/doctor` y mínimos por tramo

- **Descripción**: Resultado: `/doctor` lee la configuración local de OpenCode/Codex (y Ollama solo si es host local y la capacidad está activa) y avisa ⚠️ si el contexto es menor que el mínimo del tramo; `docs/INTEROP.md` (+ EN) documenta los tramos orientativos (8-9B solo lectura; 32B con ≥ 64k para la vía rápida). Requisito: evaluation.md §C-14, spec §Criterios CA-10.
- **Changelog**:
- **Estado**: borrador
- **Tiempo humano**: est. 6.0h · real —
- **Tiempo IA (ejec.)**: est. 2.48h · real —
- **Supervisión**: est. 0.62h (≈25 % IA) · real —
- **Previsión IA**: 1.0M in / 100k out tok · 5.98 €
- **Dependencias**: T-22
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/doctor.py`, `agent-kits/shared/test_doctor.py`, `commands/doctor.md`, `docs/INTEROP.md`, `docs/en/INTEROP.md`, `interop/**` (regenerado: `hooks/`|`agents/`|`commands/` tocados), `.codex-plugin/**`, `.agents/plugins/**`
- **Cubre (tests)**: —
- **Verificación**: lectura: se concreta al revalidar (T-08/T-20 del plan); no inventar comandos que aún no existen

**Criterios de aceptación**
- [ ] Criterio (esqueleto): CA-10 — ⚠️ con el arreglo cuando el contexto es menor que el mínimo, sin red salvo hosts locales y sin bloquear. Se concreta al revalidar.

**Subtareas**
- [ ] Se concreta al revalidar.

**Notas**: Esqueleto diferido. Los mínimos salen de la auditoría, no de una prueba real: documentarlos como orientativos. Sin red salvo hosts locales (invariante). Depende de T-22. Se concreta al revalidar. Clasificación: capacidad nueva. Coste estimado de la tarea: 306 € (horas × 50 € + tokens).


### T-25 — C-13 — Perfil `lite`

- **Descripción**: Resultado: `dev.json` `perfil: lite` desactiva paralelismo y subagentes, reduce el tope del brief, obliga a `ledger-write.py` y carga solo el núcleo de `dev-cycle`; NO recorta la revisión de dos lentes ni el `qa-gate` (decisión 3 de la puerta); lo soportan `/setup` y `/doctor`. Requisito: evaluation.md §C-13.
- **Changelog**:
- **Estado**: borrador
- **Tiempo humano**: est. 9.6h · real —
- **Tiempo IA (ejec.)**: est. 3.97h · real —
- **Supervisión**: est. 0.99h (≈25 % IA) · real —
- **Previsión IA**: 1.6M in / 160k out tok · 9.57 €
- **Dependencias**: T-21, T-13, T-23
- **Tipo**: docs
- **Archivos**: `commands/setup.md`, `commands/dev-cycle.md`, `agent-kits/shared/task-brief.py`, `agent-kits/shared/doctor.py`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `interop/**` (regenerado: `hooks/`|`agents/`|`commands/` tocados), `.codex-plugin/**`, `.agents/plugins/**`
- **Cubre (tests)**: —
- **Verificación**: lectura: se concreta al revalidar (T-08/T-20 del plan); no inventar comandos que aún no existen

**Criterios de aceptación**
- [ ] Criterio (esqueleto): con `perfil: lite` no hay paralelismo, la revisión y el qa-gate siguen activos y el brief respeta el tope reducido. Se concreta al revalidar.

**Subtareas**
- [ ] Se concreta al revalidar.

**Notas**: Esqueleto diferido; depende de T-13, T-23 y del diseño de T-21. Choque potencial con las puertas no negociables: si el usuario quisiera recortarlas cambia el alcance y la constitución. Se concreta al revalidar. Clasificación: capacidad nueva. Coste estimado de la tarea: 490 € (horas × 50 € + tokens).


### T-26 — P-F3 — Proceso de la fase 3: revisión, CHANGELOG doble, Linux, prueba manual y release

- **Descripción**: Resultado: F3 cerrada y publicada: validación estática (contratos, interop, doctor) + prueba manual del usuario en otro equipo con Ollama (fuera de presupuesto; mínimos por tramo orientativos), CHANGELOG ES/EN, docs espejo, interop, réplica Linux y `scripts/release.py`. Requisito: evaluation.md §P-F3, decisiones 6 y 7 de la puerta.
- **Changelog**:
- **Estado**: borrador
- **Tiempo humano**: est. 2.4h · real —
- **Tiempo IA (ejec.)**: est. 0.64h · real —
- **Supervisión**: est. 0.16h (≈25 % IA) · real —
- **Previsión IA**: 0.3M in / 30k out tok · 1.79 €
- **Dependencias**: T-22, T-23, T-24, T-25
- **Tipo**: devops
- **Archivos**: `CHANGELOG.md`, `CHANGELOG.es.md`, `docs/INTEROP.md`, `docs/en/INTEROP.md`, `docs/roadmap/README.md`, `interop/**` (regenerado: `hooks/`|`agents/`|`commands/` tocados), `.codex-plugin/**`, `.agents/plugins/**`
- **Cubre (tests)**: —
- **Verificación**: lectura: se concreta al revalidar (T-08/T-20 del plan); no inventar comandos que aún no existen

**Criterios de aceptación**
- [ ] Criterio (esqueleto): los mismos que T-07 aplicados a F3, más resultado de la prueba manual del usuario anotado. Se concreta al revalidar.

**Subtareas**
- [ ] Se concreta al revalidar.

**Notas**: Esqueleto diferido; mismo procedimiento que T-07. Se concreta al revalidar. Clasificación: proceso. Coste estimado de la tarea: 122 € (horas × 50 € + tokens).

---

## Revisión de dos lentes — intento 3: Fase 1 (T-02) — prefiltro y CA-01 ajustado

Fecha: 2026-10-29. Rango inmutable: `bae4e46..78c20709fd0894d2a5be1a9e25aedc7a2f3b920b`.
Método: cuatro revisores genéricos de contexto fresco, uno por lente (fallback del agente
`reviewer`, no expuesto por nombre en este runtime); solo lectura. Los intentos 1/2 de
`testing/t02-review.json` fueron autorrevisión secuencial, no independientes; ambos incluyeron C.
Lentes: **A+B+C+D**; C forzada por el contrato de T-02, D por el hot path. Esta revisión se limita
a T-02; no acredita la revisión final de F1.

| Lente | Resultado y evidencia |
|---|---|
| A — conformidad | Criterios funcionales y CA-01 ajustado conformes; tabla por criterio y líneas en `testing/t02-review-attempt-3-2026-10-29.json`. Adenda pending y SHA comprobados. Interop ejecutado: exit 0, 88 ficheros al día. La traza correctamente pendiente en el SHA revisado se completa aquí. |
| B — corrección | Sin defectos. Identidad, mapas, UTF-8/BOM, entrada incompleta, fallback y copia OpenCode revisados; 16 pruebas de paridad y 23 específicas Node pasan. |
| C — seguridad | Sin hallazgos introducidos/reabiertos. Contraste con ADR-023 original, constitución y adenda tratada como propuesta; paridad dirigida 16 pass. |
| D — rendimiento | Sin hallazgos. Lecturas acotadas, selección constante y plazo monotónico; Node permanece en la latencia y el control histórico fallido no acredita ahorro. Sin nuevos benchmarks. |

Fusión: **0 Critical / 0 Important / 0 Minor**. La condición pendiente de traza se resuelve al
incorporar las cuatro salidas finales; no requiere modificar código. **T-02 completada**.
Scope-check frente al plan aprobado `78c2070`: exit 0, cero fuera de alcance y cero criterios
alterados; frente a `bae4e46`, los dos cambios de criterio son exclusivamente los aprobados por
el usuario (`testing/f1-approved-adjustment-2026-10-29.json`), sin cambiar el detector.
CI del SHA revisado completa verde: `40866395200`, 9.653 Python, 362 Node, cero fallos.

Limitaciones conservadas: no hay porcentaje medido de cobertura del diff T-02; no se acredita
entrega nativa ni estabilidad general. **T-01 y T-07 permanecen abiertas**, sin release ni
aprobación de memoria. Evidencia detallada: `testing/t02-review-attempt-3-2026-10-29.json`.
Jira comprobado con `jira-flow.py plan --event revision --actor reviewer --task T-02
--intento 3 --json`: desactivado, `ops: []`; no se publican mensajes externos.

## Revisión de dos lentes — intento 1: Fase 1 (T-01, T-02, T-03, T-04, T-05, T-06, T-07) — dos gaps de T-06

Fecha: 2026-10-29. SHA inmutable `05ea2e09e394aebe05fd849e58687fb1c1efe7f4`.
Diff de F1 = unión de `80d5836..8825414` (benchmark inicial) y `bae4e46..05ea2e0`
(resto F1); el commit intermedio OpenCode V2 pertenece a otra iniciativa.
Método: cuatro revisores genéricos de contexto fresco, solo lectura; lentes **A+B+C+D**.
Scope-check contra el plan aprobado `05ea2e0`: exit 0, cero fuera/cambios de criterio;
las modificaciones históricas autorizadas se conservan con sus recibos separados.

| ID/lente | Grado y escenario | Disposición |
|---|---|---|
| A1 — conformidad | **Important**: `plugin-dev/SKILL.md` crece de 200 a 209 líneas; viola CONSTITUTION:28. El umbral técnico 250 no sustituye el principio 200. | Aceptado. T-06 reabierta; detalle de clasificación trasladado a referencia, mapa de 199 líneas. Diet-check contra `05ea2e0`: 0 párrafos perdidos. |
| A2 — conformidad | **Important**: Verificación T-06 declara `--runs 3 --md`, pero solo hay recibo tokens-only; no consta ese workload. | Aceptado. Declaración corregida al inventario pertinente `--tokens-only --json`, ejecutado de nuevo con recibo exacto, sin inventar una ejecución histórica de hooks. |
| B — corrección | Sin defectos. | Revisa todo el diff funcional, incluida la fixture que conserva 8/8 señales y el contrato `state_busy`. |
| C — seguridad | Sin hallazgos nuevos. | Limpieza, caché/rutas, redactor, captura, helper y benchmark; limitación conocida de ancestros conservada. T-02 no se reabre sin evidencia nueva. |
| D — rendimiento | Sin hallazgos. | Lecturas/barridos acotados, caché y atajos; no usa el 80 % como objetivo actual ni excluye Node de las medidas. |

Fusión: **0 Critical / 2 Important / 0 Minor**. No se aprueba todavía la revisión de fase.
A verifica las tres pasadas, fuentes y cobertura del benchmark: **T-01 completada** con
el criterio autorizado de caracterización, sin declarar estabilidad uniforme. T-06 vuelve
a `en-progreso` por los dos gaps; T-07 sigue abierta. Corrección de prosa: TDD n/a.
Verificación de los fixes: diet-check 199 líneas/0 párrafos perdidos; linter 0 errores/3 avisos;
evals 192 casos/0 errores; interop 88 al día; 80 tests de linter/tamaño/export pasan.
Inventario real: 5.519/5.512/5.508 tokens fijos estimados, cero hooks ejecutados.
Evidencia completa `testing/t07-f1-review-attempt-1-2026-10-29.json`,
`testing/t07-f1-review-fix-verification-2026-10-29.json` y
`testing/t06-tokens-verification-2026-10-29.json`. Pendiente intento 2 sobre los fixes,
con traslado íntegro de los veredictos previos. Jira comprobado con
`jira-flow.py plan --event gaps --actor reviewer --task T-06 --intento 1 --json`:
desactivado, `ops: []`, sin mensajes externos.

## Revisión de dos lentes — intento 2: Fase 1 (T-01, T-02, T-03, T-04, T-05, T-06, T-07) — A1/A2 resueltos

Fecha: 2026-10-29. Corrección inmutable `05ea2e0..8f83eccd46b640cbec38c8d77907d223880ca665`.
Dos revisores frescos A/B comprueban solo lo corregido, con la tabla completa del intento 1;
C/D conservan sus veredictos sobre código runtime/tests/generados idéntico, sin evidencia
nueva que justifique reabrirlo. No hay otra modificación de criterios.

| ID/lente | Veredicto con evidencia |
|---|---|
| A1 | Resuelto: mapa 199 líneas; los 13 renglones originales están literalmente en `references/piece-boundaries.md`; frontmatter y description intactos. Diet-check ejecutado: exit 0, 0 párrafos perdidos. |
| A2 | Resuelto: declaración `--tokens-only --json` y ejecución real con exit 0, 5.519/5.512/5.508 tokens estimados y cero hooks. Cuatro hashes LF contrastados con los blobs. No se inventa la ejecución anterior. |
| B | Sin defectos: enlaces válidos, procedimiento conservado y datos coherentes; no cambian código ni expectativas funcionales. |
| C/D anteriores | Sin hallazgos nuevos; se conserva el juicio del intento 1 sobre fuentes de ejecución idénticas. |

A ejecuta interop (exit 0, 88 al día) y scope-check (exit 0, cero fuera/cambios de criterio).
Fusión: **0 Critical / 0 Important / 0 Minor**. **Revisión de implementación F1 cerrada en
2 intentos; T-06 completada**. Se conserva T-01 completada con caracterización autorizada,
no con una afirmación de estabilidad uniforme. T-07 sigue abierta por medición final,
QA/cobertura y entrega; este juicio no autoriza release ni promueve memoria.
Evidencia `testing/t07-f1-review-attempt-2-2026-10-29.json`.
Jira comprobado con `jira-flow.py plan --event revision --actor reviewer --task T-06
--intento 2 --json`: desactivado, `ops: []`, sin mensajes externos.

## Revisión de dos lentes — intento 3: Fase 1 (T-01, T-02, T-03, T-04, T-05, T-06, T-07) — oráculo terminal validado

Fecha: 2026-10-29. Corrección inmutable `8f83ecc..07e78b6434085f5f75663cce64674eda66b1467c`.
Dos revisores frescos A/B reciben todos los veredictos/gaps anteriores. C/D se conservan
sobre producción idéntica y sin un canal nuevo; selector incremental C=false/D=false.
No se reabren A1/A2 ni T-01..T-06 sin evidencia nueva.

| Lente | Veredicto y evidencia |
|---|---|
| A — conformidad | Aprobada. Estados Z/X terminales o PID ausente; vivos/detenidos/errores inciertos no se aceptan. RED, 7 tests Linux, 6 Windows y dos mutantes sustentan el cambio de oráculo, sin cambiar producción ni límites 3.000/9.500 ms. |
| A — mediciones/cobertura | Recalcula 36 medianas/p95/máximos y contrasta ocho hashes sin diferencias; carga concurrente explícita. Media oficial Python 90,74 % en siete archivos medidos, aviso documental y limitaciones preservados. No falsea QA verde. |
| B — corrección | Sin defectos. La regresión retiene un hijo terminal propio mientras bloquea el reap del propietario; cleanup con SIGKILL. Solo PID ausente o estados terminales pasan; errores inesperados hacen fallar. |
| C/D anteriores | Sin evidencia nueva para reabrir el juicio sobre código de producción idéntico. |

A ejecuta interop: exit 0, 88 al día; Windows dirigido: 6 pass/0 fail/1 skip Linux.
Ledger-lint exit 0, 19 avisos de los esqueletos diferidos. Scope-check: exit 0,
cero fuera/cambios de criterio/avisos. Fusión: **0 Critical / 0 Important / 0 Minor**.
**Revisión de implementación F1 cerrada en 3 intentos**; T-07 permanece abierta hasta
CI completa y entrega. No se autoriza release ni se convierte el perfil instrumentado
con un fallo temporal en una corrida verde. Recibo
`testing/t07-f1-review-attempt-3-2026-10-29.json`.
Jira comprobado con `jira-flow.py plan --event revision --actor reviewer --task T-07 --intento 3 --json`: desactivado, `ops: []`, sin mensajes externos.


## Revisión de dos lentes — intento 1: Fase 2 — tres gaps confirmados

A/C sin gaps; B dos Important y D un Important. Fusión: **0 Critical / 3 Important / 0 Minor**, sin rebates. F2-B01: rutas MultiEdit estándar perdidas por ledger y marcador; F2-B02: primer ledger repetido oculta segundo progreso; F2-D01: reescaneo cuadrático de línea larga. Tabla A completa, evidencias B/D, límites C y triaje en `testing/f2-review-attempt1-2026-10-30.json`. Fuentes revisadas `a157679..71968b0`; scope sobre revalidación aprobada `31cd57d`: exit0, sin fuera de alcance, criterios alterados ni avisos. Cuatro revisores genéricos frescos, respaldo del tipo nativo reviewer no disponible; no delegación de implementación.

RED del autor: dos tests B fallan por salidas omitidas; regresión del marcador en tres runtimes falla con aviso/skip; test D cuenta 1.080.033.289 caracteres de split frente a cota 2×entrada de 4.194.310 bytes. Todos observados antes del cambio productivo. T-09/T-10/T-14 vuelven a en-progreso. La primera cobertura instrumentada parcial se detuvo por esta candidata obsoleta y queda `ABORTED_INCOMPLETE_NO_COVERAGE_VERDICT`, sin porcentaje ni verde. T-19 no cerrada. Próxima revisión: intento2 de máximo3, con tabla y gaps de este intento, sin reiniciar contador.


### Corrección de intento1 F2 — lista para revisión2, no cierre de revisión

F2-B01/F2-B02/F2-D01 corregidos por el autor con regresiones dedicadas: 234 pass/1 skip Python y 103 pass/1 skip Node de marcador/preflight; tres runtimes del ledger con MultiEdit estándar sin Bash en verde. Verificación declarada T-10: 68 pass/1 skip; consola del hook: 8 pass. Son ejecuciones parcialmente solapadas, no totales de tests únicos. Lint0errores/3avisos previos, evals192/0errores, interop88vigentes. Pins nominales de owners actualizados sin cambiar cierres/dependencias ni excepciones egress; C fresca requerida. Nuevos controles finales T-10/T-14 limpios y con sus fuentes; históricos preservados. T-09/T-10/T-14 vuelven a completado funcional; los tres gaps requieren confirmación independiente en intento2. T-19 conserva cobertura90/CI final/publicación pendientes.


## Revisión F2, intento 2 y QA final

Cuatro revisores frescos de solo lectura, con tabla completa P/R y los tres gaps previos. Fuente inmutable `e8a59ee8f2f57ed77ed23480b730802bd43fd240`; scope contra `31cd57d` sin fuera de alcance ni criterios alterados. F2-B01, F2-B02 y F2-D01 resueltos de forma independiente. Fusión **0 Critical / 0 Important / 0 Minor**: revisión de implementación aprobada en **2 de 3 intentos**, sin reiniciar contador. A conserva 28 criterios P/R; C valida los pins y la frontera transitiva sin nuevas excepciones. Evidencia `testing/f2-review-attempt2-2026-10-30.json`.

B conserva dos ejecuciones exploratorias del marcador con timeouts Windows de arranque (3 y 1 fallos). Una comprobación posterior aislada del caso restante pasa, sin cambiar el límite de cinco segundos. No reconstruye de forma única la causa ni convierte las corridas fallidas en verdes. Los controles finales T-10/T-14 pasan sin diagnósticos y no sustituyen sus históricos.

Gate oficial Python: **92,25 %** de media en **los ocho** ficheros productivos cambiados, mínimo 90; todos presentes y con hashes idénticos a Git. Primera medición dirigida: 1.125 pass / 16 skip y media roja 87,49 %. Ampliación con suites existentes omitidas: 426 pass; datos reales anexados con `--cov-append`, sin cambiar fuentes/tests, excluir producción ni rebajar el umbral. La reexportación oficial ignora un nombre virtual sintético no resoluble de tests: los 101 resúmenes previos permanecen idénticos. No es cobertura de líneas nuevas, global ponderada ni JavaScript. Recibo `testing/f2-coverage-2026-10-30.json`.

CI normal Linux sobre el SHA exacto: [41032658988](https://github.com/daycry/custom-agents/actions/runs/41032658988), **9.764 Python pass / 38 skip / 82 subtests**, **423 Node pass / 0 fail / 16 skip**. Lint, evals e interop verdes; exención canónica `test-plan: n/a (sin UI)` comprobada sin rutas UI, sin afirmar Playwright ejecutado. Recibos `testing/f2-ci-e8a59ee8-green-2026-10-30.json` y `testing/f2-qa-checks-2026-10-30.json`.

**T-19 sigue abierta exclusivamente por la entrega**: preparar preview 2.2.0, confirmar versión y publicar por `release.py`. Sus CA compuestos conservan checkbox pendiente hasta publicar. Las decisiones no-go T-16/T-17/T-18 no cuentan como implementadas. F3 requiere la release F2, T-20 y aprobación de diseño T-21.

Preview aislada **2.2.0** verificada: dry-run, preparación sin Git, coherencia, interop y paquete portable en verde; cinco manifiestos y dos changelogs. Sin tag/release ni cambio de versión en la rama. Evidencia `testing/f2-release-preview-2.2.0-2026-10-30.json`; falta confirmación de versión exigida por T-19.
