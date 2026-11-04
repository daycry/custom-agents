---
tasks: token-efficiency
estado: en-progreso
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
| Fase 1 | 0 | 4 | 0.0% |
| **TOTAL** | **0** | **4** | **0.0%** |

## Fase 1

### T-01 - Verified source receipts

- **Estado**: en-progreso
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/source-snapshot.py`, `agent-kits/shared/test_source_snapshot.py`.
- **Verificación**: `python -m pytest agent-kits/shared/test_source_snapshot.py -q`.
- **Changelog**: Fresh and stale source bytes distinguished without project writes.

**Criterios de aceptación**
- [ ] Fresh and stale source bytes distinguished without project writes.


RED: `test_source_snapshot.py` falló con 11 fallos: recibos frescos y obsoletos indistinguibles; entradas inseguras no clasificadas · 2026-11-04.


RED: `test_nonportable_paths_are_rejected_before_io; test_receipt_version_and_byte_count_are_checked` falló con RED observado: 4 fallos; nombres reservados Windows aceptados y version booleana tratada como fresca · 2026-11-04.


RED: `test_snapshot_never_emits_a_complete_receipt_its_cli_cannot_read` falló con RED observado: 32 rutas Unicode producian recibo completo superior a 64 KiB que verify CLI rechazaba; Lente B intento 1 · 2026-11-04.


RED: `test_receipt_budget_reserves_windows_crlf_at_the_exact_boundary` falló con RED observado: recibo de 65536 bytes con LF salia como 65537 en Windows por CRLF; Lente B intento 2 · 2026-11-04.

### T-02 - Compact PM instructions and conditional procedures

- **Estado**: en-progreso
- **Tipo**: backend
- **Archivos**: `agents/**`, `skills/**/SKILL.md`, `agent-kits/shared/read-discipline.md`, `agent-kits/shared/output-discipline.md`, `agent-kits/planner/**`, `agent-kits/evaluator/**`, `agent-kits/architect/**`, `commands/pm-cycle.md`, `commands/dev-cycle.md`.
- **Verificación**: `python scripts/export-interop.py --check`.
- **Changelog**: Role boundaries, approval gates, canonical formats and original moved procedures preserved.

**Criterios de aceptación**
- [ ] Role boundaries, approval gates, canonical formats and original moved procedures preserved.

### T-03 - Context source measurements

- **Estado**: en-progreso
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/context-footprint.py`, `agent-kits/shared/test_context_footprint.py`.
- **Verificación**: `python -m pytest agent-kits/shared/test_context_footprint.py -q`.
- **Changelog**: Comparable source footprint reports distinguish eager content, references and estimated tokens.

**Criterios de aceptación**
- [ ] Comparable source footprint reports distinguish eager content, references and estimated tokens.


RED: `test_context_footprint.py` falló con 4 fallos: faltan tamanos, comparacion por rutas y separacion de referencias · 2026-11-04.


RED: `test_discovery_ignores_top_level_skill_files_but_reports_missing_skill; test_root_reference_and_invalid_utf8; test_untrusted_baselines_cannot_make_a_comparison; test_cli_rejects_null_or_duplicate_baseline` falló con RED observado: 4 fallos; README tratado como skill, referencias raiz mal clasificadas y baselines booleano o null aceptados · 2026-11-04.


RED: `test_cli_rejects_null_or_duplicate_baseline` falló con RED observado: baseline JSON con profundidad 5000 producia RecursionError y stdout vacio en vez de estado explicito; Lente B intento 1 · 2026-11-04.

### T-04 - Documentation distribution and validation

- **Estado**: en-progreso
- **Tipo**: backend
- **Archivos**: `docs/**`, `agent-kits/shared/README.md`, `README.md`, `README.es.md`, `CLAUDE.md`, `interop/**`, `.codex-plugin/**`, `.agents/plugins/**`, `ci.yml.MANUAL-COPY`, `.github/workflows/ci.yml`, `tests/**`, `CHANGELOG.md`, `CHANGELOG.es.md`, `output/pdf/**`.
- **Verificación**: `python scripts/lint_plugin.py; python evals/check.py; python scripts/check-handbook.py`.
- **Changelog**: ES/EN docs, portable closure, console checks, review and regressions verified.

**Criterios de aceptación**
- [ ] ES/EN docs, portable closure, console checks, review and regressions verified.

TDD n/a: prose, instructions, configuration and documentation; executable helpers require observed RED before implementation.

## Revisión de dos lentes — intento 1: A conforme; B detecta dos Important: B-1 baseline JSON profundo (T-03), B-2 recibo Unicode mayor que stdin (T-01). Ambos reproducidos en RED y corregidos con regresiones; pendiente intento 2. (T-01, T-02, T-03, T-04)

Pendiente de revisión; sin veredicto.

## Revisión de dos lentes — intento 2: A conforme; B-1 corregido; B-2 Important aun reproducible en limite exacto CRLF Windows. RED dedicado observado; reserva de dos bytes aplicada. Pendiente intento 3. (T-01, T-02, T-03, T-04)

Pendiente de revisión; sin veredicto.

## Revisión de dos lentes — intento 3: A y B conformes sobre correccion final de CRLF; CLI Windows 65535/65536 bytes fresca y 65537 bytes receipt_budget. Sin gaps pendientes; QA global continua y queda ajuste de fixture de textos compactados aprobado en T-02. (T-01, T-02, T-03, T-04)

Pendiente de revisión; sin veredicto.
