---
tasks: token-efficiency
estado: completado
creado: 2026-11-04
verificacion: obligatoria
changelog: Changed
---

# Token efficiency

> **Este fichero es el ledger canónico de progreso.** Actualiza checkbox y Estado por tarea; el resumen de progreso se deriva de las tareas.

Alcance aprobado por el usuario; [spec](spec.md).

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 | 4 | 4 | 100.0% |
| **TOTAL** | **4** | **4** | **100.0%** |

## Fase 1

### T-01 - Verified source receipts

- **Estado**: completado
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/source-snapshot.py`, `agent-kits/shared/test_source_snapshot.py`.
- **Verificación**: `python -m pytest agent-kits/shared/test_source_snapshot.py -q`.
- **Changelog**: Fresh and stale source bytes distinguished without project writes.

Verificación ejecutada: `python -m pytest agent-kits/shared/test_source_snapshot.py -q --tb=short` → Windows 33 passed, 1 skipped (privilegio symlink). Regresiones Linux del código final y gate oficial: 49 passed entre ambos helpers, cobertura 92,68 %, mínimo 90. Revisión A/B intento 3 sin gaps pendientes.

**Criterios de aceptación**
- [x] Fresh and stale source bytes distinguished without project writes.


RED: `test_source_snapshot.py` falló con 11 fallos: recibos frescos y obsoletos indistinguibles; entradas inseguras no clasificadas · 2026-11-04.


RED: `test_nonportable_paths_are_rejected_before_io; test_receipt_version_and_byte_count_are_checked` falló con RED observado: 4 fallos; nombres reservados Windows aceptados y version booleana tratada como fresca · 2026-11-04.


RED: `test_snapshot_never_emits_a_complete_receipt_its_cli_cannot_read` falló con RED observado: 32 rutas Unicode producian recibo completo superior a 64 KiB que verify CLI rechazaba; Lente B intento 1 · 2026-11-04.


RED: `test_receipt_budget_reserves_windows_crlf_at_the_exact_boundary` falló con RED observado: recibo de 65536 bytes con LF salia como 65537 en Windows por CRLF; Lente B intento 2 · 2026-11-04.

### T-02 - Compact PM instructions and conditional procedures

- **Estado**: completado
- **Tipo**: backend
- **Archivos**: `agents/**`, `skills/**/SKILL.md`, `agent-kits/shared/read-discipline.md`, `agent-kits/shared/output-discipline.md`, `agent-kits/planner/**`, `agent-kits/evaluator/**`, `agent-kits/architect/**`, `commands/pm-cycle.md`, `commands/dev-cycle.md`.
- **Verificación**: `python scripts/export-interop.py --check`.
- **Changelog**: Role boundaries, approval gates, canonical formats and original moved procedures preserved.

Verificación ejecutada: `python scripts/export-interop.py --check` → exit 0, 92 ficheros al día. `python -m pytest tests/test_export_interop.py -q --tb=short` → 50 passed. Procedimientos originales y descriptions contrastados por A; ajuste de cuatro expectations de cuerpo documentado en testing/review-3.md sin alterar campos nativos, permisos ni asserts.

**Criterios de aceptación**
- [x] Role boundaries, approval gates, canonical formats and original moved procedures preserved.

### T-03 - Context source measurements

- **Estado**: completado
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/context-footprint.py`, `agent-kits/shared/test_context_footprint.py`.
- **Verificación**: `python -m pytest agent-kits/shared/test_context_footprint.py -q`.
- **Changelog**: Comparable source footprint reports distinguish eager content, references and estimated tokens.

Verificación ejecutada: `python -m pytest agent-kits/shared/test_context_footprint.py -q --tb=short` → Windows 15 passed. Baseline profundo con JSON explícito, comparación normalizada y mismas 60 rutas; informes en testing/. Consumo real desconocido, no se afirma ahorro facturado.

**Criterios de aceptación**
- [x] Comparable source footprint reports distinguish eager content, references and estimated tokens.


RED: `test_context_footprint.py` falló con 4 fallos: faltan tamanos, comparacion por rutas y separacion de referencias · 2026-11-04.


RED: `test_discovery_ignores_top_level_skill_files_but_reports_missing_skill; test_root_reference_and_invalid_utf8; test_untrusted_baselines_cannot_make_a_comparison; test_cli_rejects_null_or_duplicate_baseline` falló con RED observado: 4 fallos; README tratado como skill, referencias raiz mal clasificadas y baselines booleano o null aceptados · 2026-11-04.


RED: `test_cli_rejects_null_or_duplicate_baseline` falló con RED observado: baseline JSON con profundidad 5000 producia RecursionError y stdout vacio en vez de estado explicito; Lente B intento 1 · 2026-11-04.

### T-04 - Documentation distribution and validation

- **Estado**: completado
- **Tipo**: backend
- **Archivos**: `docs/**`, `agent-kits/shared/README.md`, `README.md`, `README.es.md`, `CLAUDE.md`, `interop/**`, `.codex-plugin/**`, `.agents/plugins/**`, `ci.yml.MANUAL-COPY`, `.github/workflows/ci.yml`, `tests/**`, `CHANGELOG.md`, `CHANGELOG.es.md`, `output/pdf/**`.
- **Verificación**: `python scripts/lint_plugin.py; python evals/check.py; python scripts/check-handbook.py`.
- **Changelog**: ES/EN docs, portable closure, console checks, review and regressions verified.

Verificación ejecutada: linter → 10 agentes, 0 errores, 7 avisos previos; evals/check → 60 piezas, 229 casos, 0 errores; check-handbook → exit 0. PDF actual renderizado e inspeccionado (133 páginas, 34 diagramas, 30 workflows). Revisión A/B final sin gaps pendientes. CI inicial: 10.367 passed, 39 skipped, único fallo por entrada ausente en índice, corregido y verificado con 65 tests del índice. El check requerido de la PR #28 valida el cierre completo; consumo real sigue desconocido.

**Criterios de aceptación**
- [x] ES/EN docs, portable closure, console checks, review and regressions verified.

TDD n/a: prose, instructions, configuration and documentation; executable helpers require observed RED before implementation.

## Revisión de dos lentes — intento 1: A conforme; B detecta dos Important: B-1 baseline JSON profundo (T-03), B-2 recibo Unicode mayor que stdin (T-01). Ambos reproducidos en RED y corregidos con regresiones; pendiente intento 2. (T-01, T-02, T-03, T-04)

| Tarea | Veredicto fusionado | Gaps |
|---|---|---|
| T-01 | ✗ | B-2 Important, recibo Unicode excesivo |
| T-02 | ✓ | Ninguno |
| T-03 | ✗ | B-1 Important, JSON profundo |
| T-04 | ✓ conformidad documental | QA global aparte |

[Tabla completa y reproducciones](testing/review-1.md). Sin rebates.

## Revisión de dos lentes — intento 2: A conforme; B-1 corregido; B-2 Important aun reproducible en limite exacto CRLF Windows. RED dedicado observado; reserva de dos bytes aplicada. Pendiente intento 3. (T-01, T-02, T-03, T-04)

| Tarea | Veredicto fusionado | Gaps |
|---|---|---|
| T-01 | ✗ | B-2 Important, byte CRLF Windows |
| T-02 | ✓ | Ninguno |
| T-03 | ✓ | B-1 corregido |
| T-04 | ✓ conformidad documental | QA global aparte |

[Tabla completa y corrección](testing/review-2.md). Sin rebates.

## Revisión de dos lentes — intento 3: A y B conformes sobre correccion final de CRLF; CLI Windows 65535/65536 bytes fresca y 65537 bytes receipt_budget. Sin gaps pendientes; QA global continua y queda ajuste de fixture de textos compactados aprobado en T-02. (T-01, T-02, T-03, T-04)

| Tarea | Veredicto fusionado | Gaps |
|---|---|---|
| T-01 | ✓ | B-2 corregido |
| T-02 | ✓ | Ninguno |
| T-03 | ✓ | B-1 corregido |
| T-04 | ✓ conformidad documental | QA global aparte |

[Tabla completa, CLI Windows y seguimiento QA](testing/review-3.md). Sin gaps Critical/Important pendientes. Sin rebates.
