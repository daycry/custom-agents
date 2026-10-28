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

> **Alcance de ejecución hoy:** solo **F1** (T-01..T-07). F2 y F3 son fases **diferidas**: su primera tarea (T-08, T-20) revalida el plan contra `master` y las verificaciones marcadas «se concreta al revalidar» se fijan entonces. Cada fase se publica en su propia release.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — Quick wins medibles (ejecutable ahora) | 3 | 7 | 42.9% | 0 / 38.4h | 0 / 14.8h | 0 / 3.7h | 0 / 6.0M in + 600k out |
| Fase 2 — Reestructuración (diferida) | 0 | 12 | 0% | 0 / 69.0h | 0 / 28.3h | 0 / 7.1h | 0 / 11.4M in + 1140k out |
| Fase 3 — Modelos locales (diferida) | 0 | 7 | 0% | 0 / 45.0h | 0 / 18.1h | 0 / 4.5h | 0 / 7.3M in + 730k out |
| **TOTAL** | **3** | **26** | **11.5%** | **0 / 152.4h** | **0 / 61.2h** | **0 / 15.3h** | **0 / 24.7M in + 2470k out** |

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
  }
]
```

## Fase 1 — Quick wins medibles

**Estado**: en-progreso · **Estimado**: 38.4h · **Real**: — · **Coste est.**: 1956 € · **Tokens est.**: 6.0M in / 600k out.

### T-01 — C-00 — Benchmark reproducible de hooks y tokens (línea base de esta máquina)

- **Descripción**: Resultado: un script versionado y con tests que mide la mediana (≥ 10 ejecuciones, con calentamiento descartado) de cada hook registrado en `hooks/hooks.json` con payloads fixture por runtime, y suma los tokens fijos por sesión (descriptions + índice de SessionStart) y bajo demanda (`commands/dev-cycle.md`, `agent-kits/shared/knowledge-check.md`); sale en JSON y Markdown para pegarlo en el ledger antes y después de cada cambio. Requisito: evaluation.md §C-00 y spec §Criterios («benchmark reproducible versionado… línea base registrada»); decisión 8 de la puerta: se versionan el procedimiento Y la línea base de esta máquina, marcada como tal (Windows + OneDrive, poca RAM).
- **Changelog**: Benchmark reproducible de latencia de hooks y estimaciones de tokens, con fixtures versionadas y fallos estructurados. El helper de cierre difiere imports exclusivos de ejecución para reducir su inicialización.
- **Estado**: en-progreso
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
- [ ] Ejecutar el benchmark 3 veces y comprobar que las medianas relativas son estables; anotar la dispersión en la línea base
- [x] Escribir `testing/baseline-f1.md` y el procedimiento en `docs/observability.md` + `docs/en/observability.md`.

**Notas**: RED de integración Linux: se registra el modo de arranque real más barato en `test_console_encoding.py`; renderer usa el snippet UTF-8 canónico y configura LF aparte, sin relajar las aserciones cp1252/ascii. Estado revisado 2026-10-28: implementación y línea base registradas, tres pasadas válidas de 36/36, 1.080 muestras medidas y 108 calentamientos descartados. **T-01 sigue abierta por la subtarea original de estabilidad**: dispersión máxima 102,07 %. Scope-check detectó que se había reformulado su condición; se restaura literalmente y no se acepta esa dispersión como medianas estables. Las implementaciones independientes de F1 continúan con evidencia funcional, sin cerrar fase ni liberar mientras sigan abiertos estabilidad y rendimiento de T-02. JSON y Markdown canónico en `testing/baseline-f1.md`; comprobaciones en `testing/verification-2026-10-28.json`. **Histórico anterior al cierre (los estados siguientes corresponden a su momento):** GREEN 2026-10-28: 51 pruebas Python dirigidas; suite de entrega del guard repetida completa: 75/75. La primera ejecución real combinada tuvo 103/105: dos timeouts OpenCode; ambos pasan aislados con el supervisor antiguo y con el nuevo. Presupuestos y otros 30 casos de runtime pasaron en la combinada inicial. Inicialización del módulo: mediana 66,844 → 8,974 ms (20 muestras alternadas por variante, proceso nuevo, un calentamiento descartado); no incluye arranque de proceso ni cierre del job. Propuesta de gotcha pendiente de Curator vinculada en `curation-refs-v1`. Prerrequisito descubierto por el benchmark: reducir la inicialización innecesaria del helper de cierre, conservando el protocolo, los 500 ms del caller y los 250 ms de confirmación. RED: `test_windows_close_does_not_initialize_business_execution_modules` falló con `cleanup initialized business modules: [json, runpy, subprocess]` · 2026-10-28. La traza por pipe mide hasta 157,791 ms de inicialización previa a `close_job`; no demuestra por sí sola la causa única de los timeouts originales. Reanudación 2026-10-28: RED: `test_baseline_requires_discarded_warmup` falló (`linea_base: true` con `--warmup 0`); RED: `test_fail_fast_retains_first_failure_and_reports_incomplete_inventory` falló (`--fail-fast` no reconocido). La pasada completa anterior se conserva como diagnóstica y no usa estas opciones nuevas. Usage-meter cerrado: `fuente: estimado`, sin medida de tokens/horas/coste; duración de reloj 1h14m de ventana mixta (implementación y revisiones pedidas). No se imputa como horas IA de T-01 ni se usa para calibración.  Medición real: dos pasadas completas con 35/36 casos correctos cada una; ambas salieron 1 por `child cleanup confirmation timed out` en casos distintos. La serie de tres se detuvo; no hay línea base válida ni estabilidad demostrada. Evidencia en `testing/baseline-f1.md` y JSON crudos; T-01 conserva `en-progreso` y T-02 no se inicia. La investigación del patch OpenCode solicitada durante esta ventana se hizo solo en copias bajo `.pytest_cache`; no altera el patch ni los hooks de producción.  RED adicional: `test_silent_capture_without_persistence_is_failure` falló en las dos capturas (exit 0 sin recibo); ahora se exige un registro coincidente fuera del cronómetro, igual que `bench-session-end.py` (no se propone otra memoria para el mismo patrón ya documentado).  Alcance: la spec y la evaluación aprobadas ya estaban en disco sin seguimiento Git al retomar; se declaran para que scope-check reconozca esos artefactos heredados, sin alterar su contenido.  RED: `tests/test_bench_hooks.py::test_statistics_exclude_warmup` falló con `AssertionError: missing reproducible hook benchmark` (script ausente) · 2026-10-27. RED adicional: `test_reports_json_markdown_and_failure_exit_code` falló porque un informe fallido se marcaba como línea base; corregido. GREEN: 26 pruebas y cobertura medida del 98 % con `.venv/Scripts/python.exe -m coverage` (no se instaló ninguna dependencia). Smoke real de los 12 registros con `--runs 1 --runtime codex --json`: exit 0, sin fallos; no es línea base.  Clasificación: capacidad nueva → primer oráculo = test del propio script en ROJO (mediana, parseo de payloads, salida JSON) antes de escribirlo. Patrón a reflejar: `scripts/bench-session-end.py` (cabecera, `--runs/--warmup`, JSON estructurado, `FALLO` estructurado en timeout, exit 1) y su test `tests/test_bench_session_end.py`; los hooks salen de `hooks/hooks.json`. Hipótesis (a confirmar en la implementación): tokens = caracteres/4 como estimación declarada (no hay tokenizador en el repo; marcarlo `⚠️ estimación`); descriptions y frontmatter se leen igual que `scripts/lint_plugin.py`; el índice de SessionStart se mide ejecutando `agent-kits/shared/skill-index.py`. Fixtures en `tests/fixtures/bench-hooks/` (un JSON por evento y runtime). Ruido: comparar medianas relativas en la misma sesión; NO fijar umbrales absolutos en CI. Esta tarea ejecuta el benchmark en esta máquina y pega la tabla en `testing/baseline-f1.md`. No corras suites completas. Clasificación: capacidad nueva. Coste estimado de la tarea: 365 € (horas × 50 € + tokens).


### T-02 — C-02 — Prefiltro del guard nativo en node

- **Descripción**: Resultado: `hooks/run-hook.mjs` lee `agent-kits/shared/native-roles.json`, `agent-kits/shared/copias.json`, `agent-kits/shared/copias.json`, compara la identidad nativa EXACTA (`agent_type` en Claude/Codex, `agent` en OpenCode) con los roles protegidos del runtime y, si no coincide, termina sin lanzar Python; si el mapa falta o es inválido, lanza Python como hoy y emite su diagnóstico. La decisión de deny sigue en `native-guardrail.py`. Requisito: evaluation.md §C-02 (partida de mayor retorno, ≈ 2,3 s × ~150 llamadas ≈ 5,7 min/sesión aquí); spec §Criterios CA-01/CA-02/CA-03 y §Manejo de errores; ADR-023.
- **Changelog**: Prefiltro nativo de identidades exactas para evitar Python en sesiones sin rol protegido, con retorno al evaluador ante dudas.
- **Estado**: en-progreso
- **Tiempo humano**: est. 7.2h · real —
- **Tiempo IA (ejec.)**: est. 3.48h · real —
- **Supervisión**: est. 0.87h (≈25 % IA) · real —
- **Previsión IA**: 1.4M in / 140k out tok · 8.37 €
- **Dependencias**: T-01
- **Tipo**: hooks
- **Archivos**: `agent-kits/shared/copias.json`, `hooks/run-hook.mjs`, `hooks/opencode-plugin.js`, `agent-kits/shared/native-roles.json`, `tests/hook-guard-delivery.test.mjs`, `tests/hook-guard-prefilter.test.mjs`, `tests/test_native_prefilter_parity.py`, `tests/test_hook_launcher_security.py`, `docs/observability.md`, `docs/en/observability.md`, `interop/**` (regenerado: `hooks/`|`agents/`|`commands/` tocados), `.codex-plugin/**`, `.agents/plugins/**`
- **Cubre (tests)**: —
- **Verificación**:
  - `node --test tests/hook-guard-prefilter.test.mjs tests/hook-guard-delivery.test.mjs` → todos pasan; el shim `CUSTOM_AGENTS_PYTHON` NO se invoca para identidades no protegidas y SÍ para `custom-agents:implementer`/`custom-agents:architect` (y sus equivalentes de Codex/OpenCode)
  - `python3 -m pytest -q tests/test_native_prefilter_parity.py tests/test_hook_launcher_security.py agent-kits/shared/test_guardrail_check.py` → todos pasan sin cambiar expectativas previas (paridad node/Python sobre la tabla de identidades; mapa corrupto → diagnóstico `role-map-unavailable`)
  - `python3 scripts/export-interop.py --check` → exit 0
  - `python3 scripts/bench-hooks.py --runs 10 --md` → mediana de `native-guardrail` (sesión sin rol protegido) ≥ 80 % menor que la de `testing/baseline-f1.md`; tabla pegada en el ledger

**Criterios de aceptación**
- [ ] CA-01: sin rol protegido (sin `agent_type`/`agent`, o identidad no protegida), un Bash o Edit no arranca ningún proceso Python y la mediana del hook baja ≥ 80 % frente a la línea base.
- [x] CA-02: con identidad nativa exacta de `implementer` o `architect` el guard deniega las operaciones prohibidas igual que antes (suites de guard en verde SIN modificar expectativas).
- [x] CA-03: con `native-roles.json` corrupto, ausente o con esquema no soportado se lanza Python y se emite el diagnóstico actual; nunca se omite la comprobación.
- [x] Tabla de paridad node/Python cubre mayúsculas, prefijos, espacios, valores no string, identidad de Codex vs OpenCode vs Claude y runtime desconocido; falla si `PROTECTED` y la lista de node divergen.
- [x] El prefiltro no emite nunca `deny` ni `systemMessage` propio; solo decide si se lanza Python (hooks informan, exit 0).
- [ ] La revisión incluyó la Lente C (seguridad) en todos los intentos y su traza está en el ledger; adenda a ADR-023 propuesta (ruta pending/SHA anotada en Notas).
- [x] Estado de `hooks/opencode-plugin.js` decidido y documentado (prefiltro aplicado o diferencia declarada).

**Subtareas**
- [ ] RED: test de no-lanzamiento con shim de Python (identidad no protegida) y test de paridad; verlos fallar.
- [ ] Implementar la lectura de `native-roles.json` y la comparación exacta en `run-hook.mjs` (rama `guard`), con caída a Python ante cualquier duda.
- [ ] Decidir y aplicar el criterio del adaptador de OpenCode.
- [ ] Medir antes/después con `bench-hooks.py` y pegar la tabla en el ledger.
- [ ] Proponer la adenda de ADR-023 (`knowledge-curation.py propose`) y regenerar `interop/`.

**Notas**: Estado actual: implementación funcional validada, rendimiento del 80 % pendiente. Tres pasadas filtradas completadas; frente a la base antigua no se acredita reducción. Control intercalado: Node vacío 1.208 ms y prefiltro 1.266 ms; el control anterior tuvo un fallo y se conserva como FALLO, sin ganancia aceptada. No se cierra T-02. Informe `testing/t02-native-prefilter.md`; adenda propuesta vinculada en `curation-refs-v1`. Se permite continuar la implementación independiente de F1 tras validar seguridad funcional, manteniendo abierta la aceptación cuantitativa y el cierre de fase. RED de revisión C 2026-10-28: `unclosed input has a deadline (backward clock: true)` agotó el watchdog externo; corregido usando reloj monotónico para el plazo compartido de lectura y evaluación. Refactor con caracterización previa en verde (153 Python + 110 Node): la validación del mapa se replica byte a byte mediante `copias.json`, con paridad de roles y límite de entrada respecto a Python. RED adicional 2026-10-28: `OpenCode uncertain map before-setup/after-setup` fallaron porque el callback omitía Python cuando el mapa no era válido. RED 2026-10-28: las tres pruebas `unprotected native identity skips Python even when unavailable` fallaron con `role guard could not start` al intentar Python para una sesión principal. Clasificación: cambio de comportamiento observable (qué procesos arrancan) sin cambiar el veredicto → primer oráculo = test de no-lanzamiento en ROJO (hoy node SIEMPRE lanza Python: `hooks/run-hook.mjs:194-203`) más suites de guard SIN cambiar expectativas. Patrón: `evaluate()` en `agent-kits/shared/native-guardrail.py:256-300` (identidad exacta, `PROTECTED = ("implementer", "architect")` en :20); el override `CUSTOM_AGENTS_PYTHON` de `run-hook.mjs` (función `python()`) permite un shim que cuenta lanzamientos sin tocar el intérprete real; tests existentes `tests/hook-guard-delivery.test.mjs` y `tests/test_hook_launcher_security.py`. Decisión por defecto a confirmar en la revisión: NO cambiar el esquema de `native-roles.json` (`schema_version` 1, que `native-guardrail.py:263` exige); node deriva la lista protegida de las claves `implementer`/`architect` y un test de paridad ata esa lista a `PROTECTED` leyéndolo de `native-guardrail.py`. Si la revisión exige fuente física única → `schema_version` 2 con lectura compatible. Fallar cerrado: cualquier duda (JSON ilegible, runtime desconocido, `agent_type` no string) → lanzar Python. El adaptador `hooks/opencode-plugin.js:138` (`run`) lanza su propio proceso: decidir en el primer paso si necesita el mismo prefiltro y, si no lo lleva, documentarlo en la adenda. Adenda a ADR-023: proponer vía `agent-kits/shared/knowledge-curation.py propose` (no editar el ADR a mano). **Lente C (seguridad) obligatoria en los 3 intentos de revisión** (forzar con `dev.json` `revision.lenteSeguridad`); lente D por el hot path. Hooks exit 0 e informativos: el prefiltro nunca emite `deny` por sí mismo. Clasificación: cambio de comportamiento (rendimiento) en zona de seguridad. Coste estimado de la tarea: 368 € (horas × 50 € + tokens).


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
- **Estado**: en-progreso
- **Tiempo humano**: est. 9.6h · real —
- **Tiempo IA (ejec.)**: est. 3.97h · real —
- **Supervisión**: est. 0.99h (≈25 % IA) · real —
- **Previsión IA**: 1.6M in / 160k out tok · 9.57 €
- **Dependencias**: T-05
- **Tipo**: docs
- **Archivos**: `agent-kits/evaluator/README.md`, `agent-kits/evaluator/references/scope.md`, `tests/fixtures/opencode-v2-agent-contract.json`, `agents/*.md`, `skills/*/SKILL.md`, `commands/setup.md`, `commands/doctor.md`, `evals/cases/*.json`, `scripts/lint_plugin.py`, `tests/test_lint_plugin.py`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `docs/agents/*.md`, `interop/**` (regenerado: `hooks/`|`agents/`|`commands/` tocados), `.codex-plugin/**`, `.agents/plugins/**`
- **Cubre (tests)**: —
- **Verificación**:
  - `python3 scripts/lint_plugin.py` → 0 avisos `description de N caracteres (> 600)`; sin errores nuevos
  - `python3 evals/check.py` → exit 0 (toda pieza con ≥ 2 positivos + 1 negativo y el literal casando con la description REAL)
  - `python3 -m pytest -q tests/test_lint_plugin.py tests/test_skill_size.py tests/test_export_interop.py` → todos pasan
  - `python3 scripts/export-interop.py --check` → exit 0
  - `python3 scripts/bench-hooks.py --runs 3 --md` → tokens fijos ≥ ~2.000 menos que `testing/baseline-f1.md`; tabla pegada en el ledger

**Criterios de aceptación**
- [x] Ninguna description de agente, skill o comando supera 600 caracteres (comprobado por test de repositorio y por el linter).
- [x] `lint_plugin.py` avisa a 600 (`DESC_WARN_CHARS = 600`) y `docs/CONVENTIONS.md` (+ EN) lo documenta.
- [x] Todos los literales de `evals/cases/` siguen casando (`evals/check.py` exit 0); no se editan casos salvo ampliación justificada.
- [x] Los tokens fijos por sesión bajan ≥ ~2.000 frente a la línea base (tabla antes/después en el ledger).
- [ ] Medición manual en sesión real registrada en Notas: ¿vuelven las 13 skills al listado? Si no, queda abierta la decisión del segundo recorte (no se hace en F1).
- [x] Para cada pieza recortada, Notas indica qué se movió y a dónde (cuerpo/`references/`), para que la revisión (lente A) valide que no se perdió ningún disparador.

**Subtareas**
- [ ] RED: test que exige ≤ 600 en todas las piezas y el aviso del linter a 600; verlo fallar con las 25 actuales.
- [ ] Grupo 1 — agentes (architect, reviewer, analyst, documenter, knowledge-curator, evaluator): reescribir, `evals/check.py`, regenerar interop.
- [ ] Grupo 2 — 16 skills: reescribir, `evals/check.py`.
- [ ] Grupo 3 — `commands/setup.md` y `commands/doctor.md`: reescribir, regenerar interop.
- [x] Bajar `DESC_WARN_CHARS` a 600 y actualizar CONVENTIONS ES/EN.
- [x] Medir tokens fijos antes/después; hacer la prueba manual del listado de skills y anotarla.

**Notas**: RED Linux de integración: evaluator alcanzó **15.856 bytes > tope CA-22 15.513**. Su alcance completo se mueve a `agent-kits/evaluator/references/scope.md` bajo demanda, sin elevar el tope; el test de exportación verifica ahora esa referencia y su contenido. Se recoloca la sección de alcance bajo el título principal de cada pieza para conservar intacto el bloque previo de capacidades. Implementación verificada: **80/80** pruebas de linter/tamaño/interop y suite-script histórica `test_lint_plugin: OK`; evals **52 piezas / 192 casos / 0 errores**, sin modificar casos. Linter: 0 errores y 4 avisos (3 comandos genéricos previos y plugin-dev de 209 líneas, por debajo del límite duro 250); 0 avisos de descriptions >600. 24 piezas movieron su description completa a `## Alcance y activación` del mismo cuerpo; evaluator la conserva en la referencia indicada; mapa individual y hashes en `testing/t06-description-moves.json`, con todos los disparadores anteriores conservados y el literal de setup en su propósito. Evitar corte automático de palabras con guion al plegar YAML: insertar un espacio en `adversarial-review` alteraba su literal. Tokens fijos estimados (caracteres/4): Claude **8.752 → 5.519**, Codex **8.745 → 5.512**, OpenCode **8.783 → 5.508**; ahorro **3.233/3.233/3.275** tokens estimados, no consumo real. T-06 sigue abierta: **no se ha medido en una sesión nueva real la recuperación de las 13 skills**; la sesión actual cargó el plugin instalado anterior. No se aplica un segundo recorte ni se cambia la instalación global. La fixture de semántica propia OpenCode fijaba las descriptions antiguas: se actualiza solo ese campo y se conserva el anterior como `description_body`, cuya presencia en el cuerpo exportado exige ahora el test. Mode, permisos y campos nativos permanecen idénticos (comparación de datos verificada). Dos literales adicionales de evals (`campo de respuesta eliminado`, `incluye extensiones propias de proyecto y usuario`) se conservaron en las descriptions tras el rojo; no se modificó ningún caso de activación. RED 2026-10-28: el test de 601 caracteres no recibió aviso (umbral 1.200); el test de inventario detectó las 25 piezas por encima de 600. La fixture inicial de linter contenía un reemplazo con acentos alterado por la consola; se corrigió antes de confirmar el rojo con la descripción real de 601 caracteres. Clasificación: refactor de prosa con riesgo de activación → primer oráculo = test en ROJO en `tests/test_lint_plugin.py`: el linter avisa a 600 y un test de repositorio comprueba que ninguna pieza real supera 600 (hoy 25 fallan). Patrón: `scripts/lint_plugin.py:108` (`DESC_WARN_CHARS = 1200`) y :1381-1403 (el aviso); los literales de activación están en `evals/cases/<kind>-<nombre>.json` y `python3 evals/check.py` los compara con la description REAL; las skills viajan sin traducir pero su description no puede pasar de 1.024 (OpenCode) — 600 queda por debajo. Mayores excesos: architect 1.097, reviewer 1.084, analyst 1.067 caracteres, además de documenter, knowledge-curator, evaluator, 16 `skills/*/SKILL.md`, `commands/setup.md`, `commands/doctor.md`. Trabajar por GRUPOS revisables (agentes → skills → comandos) y regenerar interop al cerrar cada grupo. Riesgo principal: perder disparadores; `evals/check.py` solo comprueba literales y la activación real (`evals/run.py`/`headless.yml`) necesita `ANTHROPIC_API_KEY`, que no se asume — la mitigación es mover el detalle fuera de la description (al cuerpo de la pieza o a `references/`) y no tocar los literales; declarar en Notas qué se movió. Medición manual declarada (no automatizable): en una sesión real comprobar si las 13 skills sin descripción vuelven al listado nativo; si no basta, abrir decisión para un segundo recorte (fuera de presupuesto). Medir tokens fijos antes/después con `bench-hooks.py`. Descriptions de `docs/agents/<x>.md` no cambian salvo que repitan el literal. Clasificación: refactor (prosa) con riesgo de activación. Coste estimado de la tarea: 490 € (horas × 50 € + tokens).


### T-07 — P-F1 — Proceso de la fase 1: revisión final, medición, CHANGELOG doble, Linux y release

- **Descripción**: Resultado: F1 cerrada y publicable: revisión de dos lentes de la fase completa (3 intentos como máximo, con corrección), tabla final antes/después del benchmark, CHANGELOG ES/EN actualizados desde los ledgers cerrados, docs espejo coherentes, `export-interop.py --check` verde, réplica de `ci.yml` en Linux verde y release de la fase con `scripts/release.py`. Requisito: evaluation.md §Partidas de proceso (P-F1) y decisión 6 de la puerta (una release por fase).
- **Changelog**: Evidencias de QA Linux y mediciones de F1 registradas, conservando abiertas las aceptaciones no acreditadas.
- **Estado**: en-progreso
- **Tiempo humano**: est. 2.4h · real —
- **Tiempo IA (ejec.)**: est. 0.64h · real —
- **Supervisión**: est. 0.16h (≈25 % IA) · real —
- **Previsión IA**: 0.3M in / 30k out tok · 1.79 €
- **Dependencias**: T-01, T-02, T-03, T-04, T-05, T-06
- **Tipo**: devops
- **Archivos**: `CHANGELOG.md`, `CHANGELOG.es.md`, `docs/observability.md`, `docs/en/observability.md`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `docs/roadmap/README.md`, `docs/roadmap/2026-10-27-plugin-optimization/testing/**`, `interop/**` (regenerado: `hooks/`|`agents/`|`commands/` tocados), `.codex-plugin/**`, `.agents/plugins/**`
- **Cubre (tests)**: —
- **Verificación**:
  - `python3 agent-kits/shared/ledger-lint.py docs/roadmap/2026-10-27-plugin-optimization/tasks.md` → exit 0
  - `python3 agent-kits/shared/scope-check.py docs/roadmap/2026-10-27-plugin-optimization` → exit 0
  - `python3 scripts/export-interop.py --check` → exit 0
  - `python3 scripts/lint_plugin.py && python3 evals/check.py` → exit 0
  - `python3 scripts/release.py 2.1.0 --dry-run` → exit 0 y sin avisos de copias `.MANUAL-COPY` desactualizadas
  - lectura: réplica de `ci.yml` en Linux (`python:3.11-slim`) con la suite completa en verde; salida pegada en el ledger

**Criterios de aceptación**
- [ ] La revisión de dos lentes de la fase completa quedó cerrada en ≤ 3 intentos con su traza en el ledger (Minor no bloquean).
- [ ] `testing/baseline-f1.md` incluye la tabla «después» y el ahorro medido frente a la línea base (CA-01: ≥ 80 % en el guard; ≥ ~2.000 tokens fijos; statusline ≤ 1 Python).
- [ ] Los dos CHANGELOG (`[Unreleased]` EN y `[Sin publicar]` ES) recogen F1 con un bullet por tarea; docs espejo ES/EN actualizados en el mismo cambio.
- [ ] La réplica Linux de `ci.yml` pasa sin rojos aceptados «de siempre».
- [ ] El release de F1 se publica con `scripts/release.py` (nunca a mano) previa confirmación del usuario sobre la versión; `--check` posterior en verde.
- [ ] El índice `docs/roadmap/README.md` refleja el estado de F1.

**Subtareas**
- [ ] Revisión de dos lentes sobre el diff de F1 (bucle ≤ 3) y corrección.
- [ ] Ejecutar `bench-hooks.py` «después» y completar `testing/baseline-f1.md`.
- [ ] Sincronizar CHANGELOG ×2 con `changelog-sync` desde los ledgers cerrados y revisar docs espejo.
- [ ] Verificación en Linux (réplica de `ci.yml`).
- [ ] `release.py --dry-run`, confirmar versión con el usuario, publicar y `--check`.

**Notas**: **Pausa solicitada por el usuario 2026-10-28, tras commits y push.** Última QA Linux: linter, evals y todas las suites-script pasan; pytest se detiene con **280 pass / 1 fail / 1 skip**, `test_bench_mide_in_process_no_solo_subproceso`: **p50 29,15 ms frente a <20 ms**. La causa no está aislada y no se cambia el umbral. No se ejecutan las etapas posteriores de esa corrida; **no es una suite global verde**. Snapshot verificado por bytes y modos de 1.587 ficheros (0 diferencias), limitado a 2 GiB/2 CPU; recibo `testing/t07-linux-attempt-4.json`. Los fallos anteriores de consola se corrigieron y pasan 25 tests seleccionados más arranques reales de los dos scripts bajo cp1252/ascii. Continúan pendientes T-01 estabilidad, T-02 reducción del 80 %, T-06 sesión real y el resto del cierre de T-07; sin release ni cambio de versión. Se adelanta QA Linux de la implementación independiente con snapshot del árbol actual; T-01 (estabilidad), T-02 (80 %) y T-06 (sesión real) siguen abiertos. No se bumpea versión, publica release ni cierra F1 con esas condiciones pendientes. Clasificación: proceso. Primer oráculo = `ledger-lint` + `scope-check` en rojo/verde sobre la iniciativa (sin tareas abiertas de F1). Release: `scripts/release.py` mueve `[Unreleased]`/`[Sin publicar]` a la sección de la versión en los dos CHANGELOG, corre lint + evals, exige copias `.MANUAL-COPY` al día, corrige `.sh` en 100644, bumpea los 5 manifiestos y comprueba `export-interop.py --check`; hacer `--dry-run` primero y `--check` después (LES-012). Versión propuesta: **2.1.0** (capacidad nueva —benchmark— y umbral de description más estricto para los consumidores); confirmar con el usuario antes de publicar. Verificación en Linux: réplica de `ci.yml` en `python:3.11-slim` con `git -c core.autocrlf=false archive` (los rojos «de siempre» no se aceptan: se investigan). Cierre de iniciativa = PR a master + release (lo coordina `/dev-cycle`). La retro (`/retro`) es puerta del cierre: `retro-gate.py`. No correr la suite completa en local (poca RAM): la completa se corre en Linux/CI. Clasificación: proceso (sin código nuevo). Coste estimado de la tarea: 122 € (horas × 50 € + tokens).

---

## Fase 2 — Reestructuración

**Estado**: borrador · **Estimado**: 69.0h · **Real**: — · **Coste est.**: 3518 € · **Tokens est.**: 11.4M in / 1140k out. **Diferida**: esqueleto, se concreta al revalidar (primera tarea de la fase).

### T-08 — Revalidar el plan de F2 contra `master`

- **Descripción**: Resultado: el esqueleto de F2 (T-09..T-19) queda confirmado o reajustado contra el `master` posterior a la release de F1 (cambios en hooks, comandos y suites que cita el plan), con los datos de F1 (medición de descriptions y benchmark) para decidir C-17/C-18. Requisito: decisión 2 de la puerta (+0,5 h de revalidación por fase diferida); evaluation.md §Riesgos transversales «envejecimiento del plan».
- **Changelog**:
- **Estado**: borrador
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
- [ ] Cada tarea T-09..T-19 tiene `Verificación` y `Archivos` concretos y vigentes contra `master`.
- [ ] Decisión explícita sobre C-15 (spike), C-17 y C-18 registrada en el `Changelog del plan`.
- [ ] Las estimaciones diferidas se recalculan con el real de F1 (`CALIBRATION.md`); la diferencia queda anotada.

**Subtareas**
- [ ] Comparar `master` con la base del plan (hooks, `dev-cycle.md`, suites citadas).
- [ ] Concretar verificaciones y archivos de F2.
- [ ] Decidir C-15/C-17/C-18 y anotar en el changelog del plan.

**Notas**: Primera tarea de F2; no se arranca nada de F2 sin ella. Al revalidar: concretar los `Verificación` marcados «se concreta al revalidar», actualizar `Archivos`, decidir C-17 y C-18 con los datos de C-01 (¿volvieron las 13 skills al listado?) y de C-09, y registrar los cambios en el `Changelog del plan`. IDs estables: lo nuevo toma el siguiente número libre. Clasificación: proceso. Coste estimado de la tarea: 30 € (horas × 50 € + tokens).


### T-09 — C-08 — `mark-docs-pending` dentro de node

- **Descripción**: Resultado: el hook que solo crea un fichero vacío tras escribir en `docs/` (3,6-4,6 s por Write/Edit) pasa a `hooks/run-hook.mjs` con los mismos filtros de ruta y exclusiones. Requisito: evaluation.md §C-08, spec §Alcance F2.
- **Changelog**:
- **Estado**: borrador
- **Tiempo humano**: est. 3.6h · real —
- **Tiempo IA (ejec.)**: est. 1.24h · real —
- **Supervisión**: est. 0.31h (≈25 % IA) · real —
- **Previsión IA**: 0.5M in / 50k out tok · 2.99 €
- **Dependencias**: T-08
- **Tipo**: hooks
- **Archivos**: `hooks/mark-docs-pending.sh`, `hooks/run-hook.mjs`, `hooks/opencode-plugin.js`, `hooks/hooks.json`, `tests/hook-post-preflight.test.mjs`, `interop/**` (regenerado: `hooks/`|`agents/`|`commands/` tocados), `.codex-plugin/**`, `.agents/plugins/**`
- **Cubre (tests)**: —
- **Verificación**: lectura: se concreta al revalidar (T-08/T-20 del plan); no inventar comandos que aún no existen

**Criterios de aceptación**
- [ ] Criterio (esqueleto): mismo fichero marcador y mismas exclusiones que el hook actual, sin lanzar Python ni shell; mediana medida con el benchmark. Se concreta al revalidar.

**Subtareas**
- [ ] Se concreta al revalidar.

**Notas**: Esqueleto diferido. Clasificación: refactor; oráculo = test de equivalencia en ROJO antes del cambio. Patrón: filtros de ruta ya en node (`postApplies` en `run-hook.mjs`). Equivalencia con el adaptador de OpenCode (`hooks/opencode-plugin.js`). Se concreta al revalidar. Clasificación: refactor (comportamiento igual, sin Python). Coste estimado de la tarea: 183 € (horas × 50 € + tokens).


### T-10 — C-07 — Hook de ledger fusionado (`ledger-lint-warn` + `progress-line`)

- **Descripción**: Resultado: un solo Python en modo python del launcher parsea `tasks.md` una vez y emite los dos mensajes, conservando el debounce con lock (CA-07). Requisito: evaluation.md §C-07, spec §Criterios CA-07.
- **Changelog**:
- **Estado**: borrador
- **Tiempo humano**: est. 7.2h · real —
- **Tiempo IA (ejec.)**: est. 2.98h · real —
- **Supervisión**: est. 0.74h (≈25 % IA) · real —
- **Previsión IA**: 1.2M in / 120k out tok · 7.18 €
- **Dependencias**: T-08
- **Tipo**: hooks
- **Archivos**: `hooks/ledger-lint-warn.sh`, `hooks/progress-line.sh`, `hooks/hooks.json`, `hooks/run-hook.mjs`, `agent-kits/shared/ledger-lint.py`, `agent-kits/shared/progress-report.py`, `tests/hook-post-preflight.test.mjs`, `interop/**` (regenerado: `hooks/`|`agents/`|`commands/` tocados), `.codex-plugin/**`, `.agents/plugins/**`
- **Cubre (tests)**: —
- **Verificación**: lectura: se concreta al revalidar (T-08/T-20 del plan); no inventar comandos que aún no existen

**Criterios de aceptación**
- [ ] Criterio (esqueleto): CA-07 — un Edit sobre `tasks.md` parsea el ledger una vez y salen los mismos mensajes. Se concreta al revalidar.

**Subtareas**
- [ ] Se concreta al revalidar.

**Notas**: Esqueleto diferido. Oráculo = test en ROJO de equivalencia de mensajes con los dos hooks actuales. Patrón: `hooks/ledger-lint-warn.sh`, `hooks/progress-line.sh`. Cambia la lista de hooks de `hooks/hooks.json` en 3 runtimes y lo que `/doctor` espera. Lente D. Se concreta al revalidar. Clasificación: refactor con salida idéntica. Coste estimado de la tarea: 367 € (horas × 50 € + tokens).


### T-11 — C-10 — Memoria gobernada condicional en `knowledge-check.md`

- **Descripción**: Resultado: los ~7k caracteres de «Consulta de la memoria gobernada» pasan a una referencia que solo se lee si el proyecto tiene memoria gobernada activa (ahorro estimado 10-14k tokens por ciclo; lo leen 8 agentes). Requisito: evaluation.md §C-10.
- **Changelog**:
- **Estado**: borrador
- **Tiempo humano**: est. 4.8h · real —
- **Tiempo IA (ejec.)**: est. 1.99h · real —
- **Supervisión**: est. 0.50h (≈25 % IA) · real —
- **Previsión IA**: 0.8M in / 80k out tok · 4.78 €
- **Dependencias**: T-08
- **Tipo**: docs
- **Archivos**: `agent-kits/shared/knowledge-check.md`, `agent-kits/shared/knowledge-check-governed.md`, `tests/test_knowledge_router.py`, `tests/test_graphiti_security.py`
- **Cubre (tests)**: —
- **Verificación**: lectura: se concreta al revalidar (T-08/T-20 del plan); no inventar comandos que aún no existen

**Criterios de aceptación**
- [ ] Criterio (esqueleto): ahorro por ciclo medido y registrado; un consumidor con memoria gobernada activa sigue consultándola. Se concreta al revalidar.

**Subtareas**
- [ ] Se concreta al revalidar.

**Notas**: Esqueleto diferido. Incógnita abierta de la evaluación: condición exacta de activación (¿`docs/knowledge/approved/`? ¿capacidad `kwipu`/`graphiti`?) — decidirla al revalidar con una condición determinista comprobable en una línea. Suites acopladas: `tests/test_knowledge_router.py`, `tests/test_graphiti_security.py`. Se concreta al revalidar. Clasificación: cambio de comportamiento (lectura condicional). Coste estimado de la tarea: 245 € (horas × 50 € + tokens).


### T-12 — C-06 — `session-context` en un único Python

- **Descripción**: Resultado: `hooks/session-context.sh` (315 líneas, 12 invocaciones de `python3`, 14-22 s) pasa a un único `session-context.py` que importa en proceso `journal`, `skill-index`, `progress-report` y `knowledge-find`; la salida por runtime es idéntica byte a byte (CA-06); permite bajar el timeout de SessionStart a 10 s. Requisito: evaluation.md §C-06, spec §Criterios CA-06.
- **Changelog**:
- **Estado**: borrador
- **Tiempo humano**: est. 14.4h · real —
- **Tiempo IA (ejec.)**: est. 5.96h · real —
- **Supervisión**: est. 1.49h (≈25 % IA) · real —
- **Previsión IA**: 2.4M in / 240k out tok · 14.35 €
- **Dependencias**: T-08, T-11 (orden recomendado)
- **Tipo**: hooks
- **Archivos**: `hooks/session-context.sh`, `hooks/session-context.py`, `hooks/hooks.json`, `hooks/run-hook.mjs`, `agent-kits/shared/journal.py`, `agent-kits/shared/skill-index.py`, `agent-kits/shared/progress-report.py`, `agent-kits/shared/knowledge-find.py`, `tests/test_hooks_shell.py`, `tests/hook-runtime.test.mjs`, `interop/**` (regenerado: `hooks/`|`agents/`|`commands/` tocados), `.codex-plugin/**`, `.agents/plugins/**`
- **Cubre (tests)**: —
- **Verificación**: lectura: se concreta al revalidar (T-08/T-20 del plan); no inventar comandos que aún no existen

**Criterios de aceptación**
- [ ] Criterio (esqueleto): CA-06 — un único proceso Python (más el supervisor en Windows) y salida idéntica por runtime; timeout de SessionStart bajado a 10 s. Se concreta al revalidar.

**Subtareas**
- [ ] Se concreta al revalidar.

**Notas**: Esqueleto diferido. Oráculo = test de caracterización de salida por runtime en ROJO. Riesgo: estado global de los módulos importados contamina la salida; es la característica de F2 con más probabilidad de agotar los 3 intentos. Incógnita: ¿se conserva `session-context.sh` como envoltorio sin node? Lente D. Se concreta al revalidar. Clasificación: refactor de alto riesgo con salida idéntica. Coste estimado de la tarea: 734 € (horas × 50 € + tokens).


### T-13 — C-09 — `dev-cycle.md` núcleo + fases bajo demanda

- **Descripción**: Resultado: `commands/dev-cycle.md` (546 líneas, 55 KB, ~15,4k tokens) se separa en un núcleo y referencias por fase (Fase 2, ciclo Jira, subagentes/Knowledge Gate) con «lee X solo al llegar a Y»; `quick-implement` deja de leerlo entero; ahorro ≥ 6k tokens por vía rápida; 0 párrafos perdidos. Requisito: evaluation.md §C-09, ADR-008, spec §Criterios.
- **Changelog**:
- **Estado**: borrador
- **Tiempo humano**: est. 16.8h · real —
- **Tiempo IA (ejec.)**: est. 7.45h · real —
- **Supervisión**: est. 1.86h (≈25 % IA) · real —
- **Previsión IA**: 3.0M in / 300k out tok · 17.94 €
- **Dependencias**: T-08
- **Tipo**: docs
- **Archivos**: `commands/dev-cycle.md`, `skills/quick-implement/SKILL.md`, `scripts/export-interop.py`, `tests/test_skill_size.py`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `interop/**` (regenerado: `hooks/`|`agents/`|`commands/` tocados), `.codex-plugin/**`, `.agents/plugins/**`
- **Cubre (tests)**: —
- **Verificación**: lectura: se concreta al revalidar (T-08/T-20 del plan); no inventar comandos que aún no existen

**Criterios de aceptación**
- [ ] Criterio (esqueleto): vía rápida sin cargar fases que no usa (≥ 6k tokens medidos), `--diet-check` con 0 párrafos perdidos, `export-interop.py --check` en verde. Se concreta al revalidar.

**Subtareas**
- [ ] Se concreta al revalidar.

**Notas**: Esqueleto diferido. Incógnita abierta: dónde viven las referencias de un comando (los comandos no tienen `references/`) y cómo las resuelve la regla 5 en Codex/OpenCode — decidir al revalidar (candidato a nota de diseño). 6 suites acopladas (`test_lint_plugin.py`, `test_plan_review_caller.py`, `test_project_pieces.py`, `test_review_jira_owner.py`, `test_graphiti_security.py`, `installer.test.mjs`) y `tests/test_skill_size.py --diet-check`. Se concreta al revalidar. Clasificación: refactor de alto riesgo (comportamiento del orquestador). Coste estimado de la tarea: 858 € (horas × 50 € + tokens).


### T-14 — C-16 — `review-lens-select` con una lectura por fichero

- **Descripción**: Resultado: el script abre cada fichero una sola vez y aplica los dos análisis sobre el mismo contenido (38 s con 1.081 ficheros hoy). Decidido «sí» en la puerta. Requisito: evaluation.md §C-16.
- **Changelog**:
- **Estado**: borrador
- **Tiempo humano**: est. 2.4h · real —
- **Tiempo IA (ejec.)**: est. 0.99h · real —
- **Supervisión**: est. 0.25h (≈25 % IA) · real —
- **Previsión IA**: 0.4M in / 40k out tok · 2.39 €
- **Dependencias**: T-08
- **Tipo**: backend
- **Archivos**: `skills/adversarial-review/scripts/review-lens-select.py`, `skills/adversarial-review/scripts/test_review_lens_select.py`
- **Cubre (tests)**: —
- **Verificación**: lectura: se concreta al revalidar (T-08/T-20 del plan); no inventar comandos que aún no existen

**Criterios de aceptación**
- [ ] Criterio (esqueleto): mismo veredicto de lentes con una lectura por fichero; tiempo medido sobre un diff grande. Se concreta al revalidar.

**Subtareas**
- [ ] Se concreta al revalidar.

**Notas**: Esqueleto diferido. Oráculo = test de equivalencia de veredicto en ROJO. Patrón: `skills/adversarial-review/scripts/review-lens-select.py` y su test. Lente D. Se concreta al revalidar. Clasificación: refactor de rendimiento. Coste estimado de la tarea: 122 € (horas × 50 € + tokens).


### T-15 — C-15 (spike, 2 h) — ¿Cierre del Job Object sin segundo Python?

- **Descripción**: Resultado: decisión go/no-go documentada sobre si el supervisor puede cerrar el Job Object en salida limpia (o node soltar el handle) sin perder la limpieza de procesos nietos; hoy cada hook paga un Python extra en Windows (`hooks/run-hook.mjs:233-240`, `:316`). Requisito: evaluation.md §C-15 y decisión 2 de la puerta (solo entra si el spike sale bien).
- **Changelog**:
- **Estado**: borrador
- **Tiempo humano**: est. 2.4h · real —
- **Tiempo IA (ejec.)**: est. 0.80h · real —
- **Supervisión**: est. 0.20h (≈25 % IA) · real —
- **Previsión IA**: 0.3M in / 30k out tok · 1.79 €
- **Dependencias**: T-08
- **Tipo**: hooks
- **Archivos**: `docs/roadmap/2026-10-27-plugin-optimization/testing/spike-c15.md`
- **Cubre (tests)**: —
- **Verificación**: lectura: se concreta al revalidar (T-08/T-20 del plan); no inventar comandos que aún no existen; el entregable es `testing/spike-c15.md` con medidas y decisión go/no-go

**Criterios de aceptación**
- [ ] Criterio (esqueleto): nota con el experimento, las medidas en Windows y la decisión go/no-go argumentada. Se concreta al revalidar.

**Subtareas**
- [ ] Se concreta al revalidar.

**Notas**: Esqueleto diferido. Riesgo alto: el supervisor existe por los gotchas de hooks-runtime (huérfanos). El spike NO modifica código de producción: produce una nota con medidas y la decisión. Si es no-go, T-16 se cancela con el motivo citado en Notas (decisión autorizada por la puerta). Lente C y D en la implementación posterior. Clasificación: investigación (go/no-go). Coste estimado de la tarea: 122 € (horas × 50 € + tokens).


### T-16 — C-15 (implementación, condicional al spike) — Cierre del Job Object sin segundo Python

- **Descripción**: Resultado: si T-15 es go, el supervisor cierra el job en salida limpia sin lanzar un segundo Python por hook, sin dejar procesos vivos. Requisito: evaluation.md §C-15. Se cancela con motivo si T-15 es no-go.
- **Changelog**:
- **Estado**: borrador
- **Tiempo humano**: est. 7.2h · real —
- **Tiempo IA (ejec.)**: est. 3.17h · real —
- **Supervisión**: est. 0.79h (≈25 % IA) · real —
- **Previsión IA**: 1.3M in / 130k out tok · 7.77 €
- **Dependencias**: T-15 (go)
- **Tipo**: hooks
- **Archivos**: `hooks/run-hook.mjs`, `hooks/runtime-supervisor.py`, `tests/test_hook_supervisor.py`, `tests/hook-budget.test.mjs`, `interop/**` (regenerado: `hooks/`|`agents/`|`commands/` tocados), `.codex-plugin/**`, `.agents/plugins/**`
- **Cubre (tests)**: —
- **Verificación**: lectura: se concreta al revalidar (T-08/T-20 del plan); no inventar comandos que aún no existen

**Criterios de aceptación**
- [ ] Criterio (esqueleto): sin procesos huérfanos tras 100 ejecuciones y un arranque de Python menos por hook en Windows. Se concreta al revalidar.

**Subtareas**
- [ ] Se concreta al revalidar.

**Notas**: Esqueleto diferido y condicional. Suites: `tests/test_hook_supervisor.py`, `tests/hook-budget.test.mjs`. Lente C y D obligatorias. Se concreta al revalidar. Clasificación: refactor de alto riesgo, condicional. Coste estimado de la tarea: 368 € (horas × 50 € + tokens).


### T-17 — C-17 — Kit shared resuelto una vez por fichero (se decide al abrir F2)

- **Descripción**: Resultado: cada agente/comando resuelve `$SHAREDKIT` una sola vez al principio (el `find` de 6 raíces aparece ~80 veces, ~1.200 tokens por `/dev-cycle`). Requisito: evaluation.md §C-17. Se decide en T-08 con los datos de C-01 y C-09; mejor después de T-13.
- **Changelog**:
- **Estado**: borrador
- **Tiempo humano**: est. 4.8h · real —
- **Tiempo IA (ejec.)**: est. 1.99h · real —
- **Supervisión**: est. 0.50h (≈25 % IA) · real —
- **Previsión IA**: 0.8M in / 80k out tok · 4.78 €
- **Dependencias**: T-08, T-13
- **Archivos**: `agents/*.md`, `commands/*.md`, `agent-kits/shared/*.md`, `scripts/lint_plugin.py`, `interop/**` (regenerado: `hooks/`|`agents/`|`commands/` tocados), `.codex-plugin/**`, `.agents/plugins/**`
- **Cubre (tests)**: —
- **Verificación**: lectura: se concreta al revalidar (T-08/T-20 del plan); no inventar comandos que aún no existen

**Criterios de aceptación**
- [ ] Criterio (esqueleto): ahorro medido por `/dev-cycle` y regla 5 del linter intacta. Se concreta al revalidar.

**Subtareas**
- [ ] Se concreta al revalidar.

**Notas**: Esqueleto diferido. Incógnita: mecanismo (los shells no comparten estado entre llamadas Bash: variable por bloque o ruta escrita por el agente). Acoplado a la regla 5 de `lint_plugin.py`. Se concreta al revalidar. Clasificación: refactor de prosa, condicional. Coste estimado de la tarea: 245 € (horas × 50 € + tokens).


### T-18 — C-18 — `skill-index` solo con nombres en Claude Code (se decide al abrir F2)

- **Descripción**: Resultado: en Claude Code el índice de SessionStart se reduce a nombres (o nada) para ahorrar ~650 tokens por sesión; Codex/OpenCode quedan igual. Requisito: evaluation.md §C-18. Solo si, tras C-01, las skills ya aparecen en el listado nativo; si no, el índice compacto es la única forma de que el modelo las conozca.
- **Changelog**:
- **Estado**: borrador
- **Tiempo humano**: est. 2.4h · real —
- **Tiempo IA (ejec.)**: est. 0.99h · real —
- **Supervisión**: est. 0.25h (≈25 % IA) · real —
- **Previsión IA**: 0.4M in / 40k out tok · 2.39 €
- **Dependencias**: T-08, T-06
- **Tipo**: hooks
- **Archivos**: `agent-kits/shared/skill-index.py`, `hooks/session-context.sh`, `tests/test_skill_index.py`, `interop/**` (regenerado: `hooks/`|`agents/`|`commands/` tocados), `.codex-plugin/**`, `.agents/plugins/**`
- **Cubre (tests)**: —
- **Verificación**: lectura: se concreta al revalidar (T-08/T-20 del plan); no inventar comandos que aún no existen

**Criterios de aceptación**
- [ ] Criterio (esqueleto): −650 tokens/sesión en Claude Code sin degradar la activación. Se concreta al revalidar.

**Subtareas**
- [ ] Se concreta al revalidar.

**Notas**: Esqueleto diferido. Interactúa con T-06 y T-12. Se decide en T-08 con la medición de T-06. Se concreta al revalidar. Clasificación: cambio de comportamiento, condicional. Coste estimado de la tarea: 122 € (horas × 50 € + tokens).


### T-19 — P-F2 — Proceso de la fase 2: revisión, CHANGELOG doble, Linux y release

- **Descripción**: Resultado: F2 cerrada y publicada: revisión de la fase, tabla antes/después del benchmark, CHANGELOG ES/EN, docs espejo, interop, réplica Linux y `scripts/release.py`. Requisito: evaluation.md §P-F2 y decisión 6 de la puerta.
- **Changelog**:
- **Estado**: borrador
- **Tiempo humano**: est. 2.4h · real —
- **Tiempo IA (ejec.)**: est. 0.64h · real —
- **Supervisión**: est. 0.16h (≈25 % IA) · real —
- **Previsión IA**: 0.3M in / 30k out tok · 1.79 €
- **Dependencias**: T-09, T-10, T-11, T-12, T-13, T-14
- **Tipo**: devops
- **Archivos**: `CHANGELOG.md`, `CHANGELOG.es.md`, `docs/observability.md`, `docs/en/observability.md`, `docs/roadmap/README.md`, `interop/**` (regenerado: `hooks/`|`agents/`|`commands/` tocados), `.codex-plugin/**`, `.agents/plugins/**`
- **Cubre (tests)**: —
- **Verificación**: lectura: se concreta al revalidar (T-08/T-20 del plan); no inventar comandos que aún no existen

**Criterios de aceptación**
- [ ] Criterio (esqueleto): los mismos que T-07 aplicados a F2. Se concreta al revalidar.

**Subtareas**
- [ ] Se concreta al revalidar.

**Notas**: Esqueleto diferido; mismo procedimiento que T-07. Se concreta al revalidar. Clasificación: proceso. Coste estimado de la tarea: 122 € (horas × 50 € + tokens).

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

