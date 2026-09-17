---
generacion: {fuente: estimado, tokens_reales: {entrada: 0, salida: 0, cache_creacion: 0, cache_lectura: 0}, eur: null, horas_ia: 0.0, duracion: 0m, ratio_usado: 0}
verificacion: obligatoria
---

# Checklist de Tareas - Captura durable de SessionEnd

| **Estado** | en-progreso |
|---|---|
| **Plan** | [improvement-plan.md](improvement-plan.md) |
| **Diseño** | [design.md](design.md), O1 |

> **Ledger canónico de progreso.** Esta es la fuente única de avance; los servicios externos son espejo.

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervision (real/est) | Tokens (real/est) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fase 1 - Módulos compartidos | 1 | 2 | 50% | 0.2 / 2.5h | 0.15 / 0.8h | 0 / 0.2h | 0 / 45k |
| Fase 2 - Captura y materialización | 0 | 2 | 0% | 0 / 5.5h | 0 / 1.6h | 0 / 0.4h | 0 / 85k |
| Fase 3 - Reconciliación y diagnóstico | 0 | 2 | 0% | 0 / 4h | 0 / 1.2h | 0 / 0.3h | 0 / 60k |
| Fase 4 - Pruebas, medición y cierre | 0 | 2 | 0% | 0 / 2h | 0 / 0.6h | 0 / 0.2h | 0 / 40k |
| **TOTAL** | **1** | **8** | **13%** | **0.2 / 14h** | **0.15 / 4.2h** | **0 / 1.1h** | **0 / 230k** |

## Fase 1 - Módulos compartidos

### T-01 - `outbox.py`: cola atómica con claim, done y dead-letter
- **Estado**: completado
- **Tiempo humano**: est. 1.5h · real 0.2h (estimado)
- **Prevision IA**: 20k in / 8k out tok · real (estimado): usage-meter degradó a `fuente: estimado` (sin transcripciones en este entorno); horas_ia real (estimado): 0.15h
- **Dependencias**: ninguna
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/outbox.py`, `agent-kits/shared/test_outbox.py`, `agent-kits/shared/README.md`
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_outbox.py` -> escribir idempotente por clave, claim exclusivo con dos procesos, dead-letter con causa, corte antes/después del rename sin parcial · **ejecutado**: `13 passed in 0.05s`
- **RED**: `test_escribir_es_idempotente_por_clave` (y el resto del módulo) falló con `FileNotFoundError: [Errno 2] No such file or directory: '.../agent-kits/shared/outbox.py'` · 2026-09-17
**Criterios de aceptación**
- [x] Solo stdlib; sin red; contrato `escribir/reclamar/completar/dead_letter/estado/purgar` documentado en el docstring.
- [x] Dos `reclamar` concurrentes sobre el mismo item: uno gana, el otro recibe `None`.
- **Changelog**: Nueva cola atómica compartida `agent-kits/shared/outbox.py` (escribir/reclamar/completar/dead_letter/estado/purgar) para la captura durable de `SessionEnd` y futuros exportadores de memoria.

### T-02 - `redact.py` extraído de `journal.py` (una sola fuente)
- **Estado**: borrador
- **Tiempo humano**: est. 1h · real -
- **Prevision IA**: 12k in / 5k out tok
- **Dependencias**: ninguna
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/redact.py`, `agent-kits/shared/test_redact.py`, `agent-kits/shared/journal.py`, `agent-kits/shared/test_journal.py`, `agent-kits/shared/copias.json`
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_redact.py agent-kits/shared/test_journal.py` -> mismos casos de redacción que hoy; `journal.py` importa `redactar` con fallback a copia declarada si viaja suelto
**Criterios de aceptación**
- [ ] Ningún caso de `test_journal.py` cambia de resultado.
- [ ] Si `journal.py` necesita copia local para el paquete portable, está en `copias.json` y el test de identidad la cubre (ADR-016).

## Fase 2 - Captura y materialización

### T-03 - `journal.py capture-end` + exec form en `hooks.json`
- **Estado**: borrador
- **Tiempo humano**: est. 2.5h · real -
- **Prevision IA**: 30k in / 12k out tok
- **Dependencias**: T-01
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/journal.py`, `hooks/session-journal.sh`, `hooks/hooks.json`, `agent-kits/shared/test_journal.py`, `tests/test_hooks_shell.py`, `tests/test_hooks_config.py`, `.gitignore`
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_journal.py tests/test_hooks_shell.py tests/test_hooks_config.py` -> envelope válido en `outbox/`, ni `git` ni `claude` invocados (dobles en PATH), `hooks.json` con `command: bash` + `args` y `timeout: 5`, ruta con espacios y Unicode
**Criterios de aceptación**
- [ ] Envelope ≤ 64 KiB con `schema_version`, `event_id` determinista y sin texto de conversación.
- [ ] Opt-out `sesion.journal: false` sigue funcionando; el objeto `sesion.journal.{dir,...}` se acepta.
- [ ] `git` y `claude` falsos en `PATH` no se ejecutan durante la captura (CA-01).

### T-04 - `journal.py replay`: claim, materialización, verificación, dead-letter
- **Estado**: borrador
- **Tiempo humano**: est. 3h · real -
- **Prevision IA**: 35k in / 14k out tok
- **Dependencias**: T-01, T-02, T-03
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/journal.py`, `agent-kits/shared/test_journal.py`, `docs/knowledge/journal/README.md`
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_journal.py -k replay` -> mismo evento ×5 = una entrada; envelope venenoso a `dead-letter/` y el resto continúa; transcript ausente usa el log de prompts o declara carencia; `cierre:` en el frontmatter
**Criterios de aceptación**
- [ ] Reutiliza `escribir_sesion` (git, prompts, IA opt-in) sin duplicar lógica.
- [ ] Acepta `schema_version` N y N-1.
- [ ] Nunca inventa contenido (CA-05).

## Fase 3 - Reconciliación y diagnóstico

### T-05 - Reconciliación presupuestada en `SessionStart` y huérfanas
- **Estado**: borrador
- **Tiempo humano**: est. 2h · real -
- **Prevision IA**: 25k in / 10k out tok
- **Dependencias**: T-04
- **Tipo**: backend
- **Archivos**: `hooks/session-context.sh`, `agent-kits/shared/journal.py`, `agent-kits/shared/test_journal.py`, `tests/test_hooks_shell.py`
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_journal.py -k "huerfana or budget" tests/test_hooks_shell.py -k session_context` -> 0/10/100 pendientes dentro del presupuesto; log de prompts sin envelope > ventana = `recuperado_sin_cierre`; sesión viva no se toca
**Criterios de aceptación**
- [ ] `--budget-ms` y `--max` leídos de `dev.json` con defaults 300/3.
- [ ] Solo entradas materializadas se inyectan en el contexto (CA-08).

### T-06 - `journal.py status` y sección «Journal» de `/doctor`
- **Estado**: borrador
- **Tiempo humano**: est. 2h · real -
- **Prevision IA**: 22k in / 9k out tok
- **Dependencias**: T-04
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/journal.py`, `agent-kits/shared/doctor.py`, `agent-kits/shared/test_doctor.py`, `commands/doctor.md`
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_doctor.py -k journal` -> estados sano / pendientes / huérfana / dead-letter con veredicto y remedio nombrado; triage del `Hook cancelled`
**Criterios de aceptación**
- [ ] `/doctor` lee `journal.py status --json`, no reimplementa la cola.
- [ ] Distingue «aviso del runtime con entrada escrita» de «pérdida» (CA-10).
- [ ] `purge --confirm` es el único borrado; uninstall no toca `.claude/journal/` (CA-12).

## Fase 4 - Pruebas, medición y cierre

### T-07 - Bench de captura y matriz de garantías
- **Estado**: borrador
- **Tiempo humano**: est. 1h · real -
- **Prevision IA**: 12k in / 5k out tok
- **Dependencias**: T-03, T-05
- **Tipo**: test
- **Archivos**: `scripts/bench-session-end.py`, `tests/test_bench_session_end.py`, `docs/observability.md`, `docs/en/observability.md`, `ci.yml.MANUAL-COPY`
- **Verificacion**: `python scripts/bench-session-end.py --iterations 30 --assert-p95-ms 100 --assert-p99-ms 300` -> exit 0; tabla de garantías por forma de salida en observability ES/EN
**Criterios de aceptación**
- [ ] p95 ≤ 100 ms / p99 ≤ 300 ms en CI de referencia (CA-02).
- [ ] La matriz documenta explícitamente lo que NO se garantiza (SIGKILL antes del hook).

### T-08 - GOT-011, changelog, interop y puertas
- **Estado**: borrador
- **Tiempo humano**: est. 1h · real -
- **Prevision IA**: 10k in / 4k out tok
- **Dependencias**: T-06, T-07
- **Tipo**: docs
- **Archivos**: `docs/knowledge/gotchas/GOT-011-hook-cancelled-en-session-end.md`, `docs/knowledge/README.md`, `CHANGELOG.md`, `CHANGELOG.es.md`, `interop/**`, `docs/roadmap/2026-09-17-session-end-durable-capture/tasks.md`
- **Verificacion**: `python scripts/lint_plugin.py` -> 0 · `python scripts/export-interop.py --check` -> 0 · `python -m pytest -q tests/test_knowledge_index.py` -> índice biyectivo
**Criterios de aceptación**
- [ ] GOT-011 recoge causa (trabajo en el teardown), diagnóstico y remedio.
- [ ] Ledger con evidencia; revisión de dos lentes sin gaps Critical/Important; retro abre `retro-gate.py`.
