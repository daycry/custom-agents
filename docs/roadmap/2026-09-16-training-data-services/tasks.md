---
verificacion: obligatoria
---

# Checklist de Tareas - Captura de casos y dataset

| **Estado** | borrador |
|---|---|
| **Plan** | [improvement-plan.md](improvement-plan.md) |
| **Diseno** | [design.md](design.md), O1 |

> **Ledger canonico de progreso.** Los casos y el dataset viven fuera de Git; el avance de ESTA iniciativa sigue en Git.

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervision (real/est) | Tokens (real/est) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fase 1 - Config, redaccion compartida y capacidad | 0 | 3 | 0% | 0 / 6.5h | 0 / 2.0h | 0 / 0.5h | 0 / 85k |
| Fase 2 - Recorder y puerta humana | 0 | 3 | 0% | 0 / 8h | 0 / 2.4h | 0 / 0.6h | 0 / 120k |
| Fase 3 - Dedup, particion y ensamblador | 0 | 3 | 0% | 0 / 14h | 0 / 4.2h | 0 / 1.1h | 0 / 210k |
| Fase 4 - Setup, doctor y cierre | 0 | 2 | 0% | 0 / 11h | 0 / 3.3h | 0 / 0.8h | 0 / 160k |
| **TOTAL** | **0** | **11** | **0%** | **0 / 39.5h** | **0 / 11.9h** | **0 / 3.0h** | **0 / 575k** |

## Fase 1 - Config, redaccion compartida y capacidad

### T-01 - Esquema de `training.json` y del caso
- **Estado**: borrador
- **Tiempo humano**: est. 3h · real -
- **Prevision IA**: 35k in / 14k out tok
- **Dependencias**: ninguna
- **Tipo**: docs
- **Archivos**: `agent-kits/shared/`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`
- **Verificacion**: `python -m pytest -q skills/training-data-services/scripts/test_case_schema.py` -> valida `training.json` y esquema de caso, rechaza estados/outcome invalidos
**Criterios de aceptación**
- [ ] `training.json` declara root, `id_prefix`, y si el puente a `knowledge-curator` esta activo.
- [ ] El esquema del caso exige `case_id`, `version`, `outcome`, y valida `validation.status` contra el vocabulario cerrado.

### T-02 - Consumir `redact.py` compartido y registrar la capacidad `training`
- **Estado**: borrador
- **Tiempo humano**: est. 1.5h · real -
- **Prevision IA**: 18k in / 7k out tok
- **Dependencias**: `session-end-durable-capture` T-02 (`redact.py`), `knowledge-services` T-13 (`capabilities.py`)
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/capabilities.py`, `agent-kits/shared/test_capabilities.py`, `skills/training-data-services/scripts/test_case_recorder.py`
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_capabilities.py -k training agent-kits/shared/test_redact.py` -> la capacidad `training` expone enabled/health/doctor/setup_step; el recorder importa `redactar` de `redact.py` (una sola fuente)
**Criterios de aceptación**
- [ ] **Enmienda 2026-09-17**: la extraccion de `redact.py` desde `journal.py` la hace `session-end-durable-capture` (unica iniciativa que refactoriza `journal.py`); aqui solo se consume. Sin esa dependencia cerrada, esta tarea queda `bloqueada`.
- [ ] `redact.py` sigue siendo la unica fuente de los patrones de secretos del plugin; el recorder no define ninguno propio.

### T-03 - Plantillas y estructura de directorios del case store
- **Estado**: borrador
- **Tiempo humano**: est. 2h · real -
- **Prevision IA**: 20k in / 8k out tok
- **Dependencias**: T-01
- **Tipo**: docs
- **Archivos**: `skills/training-data-services/assets/`, `docs/knowledge/adr/`
- **Verificacion**: lectura: la estructura documentada coincide con `design.md`
**Criterios de aceptación**
- [ ] Plantillas de `metadata.json`/`validation.json`/`cases_index.jsonl` documentadas con ejemplos.
- [ ] ADR propuesta con la decision de mantener el case store fuera de `docs/knowledge/`.

## Fase 2 - Recorder y puerta humana

### T-04 - Recorder determinista (crear/actualizar caso)
- **Estado**: borrador
- **Tiempo humano**: est. 4h · real -
- **Prevision IA**: 45k in / 18k out tok
- **Dependencias**: T-01, T-02
- **Tipo**: backend
- **Archivos**: `skills/training-data-services/scripts/case-recorder.py`, `skills/training-data-services/scripts/test_case_recorder.py`
- **Verificacion**: `python -m pytest -q skills/training-data-services/scripts/test_case_recorder.py` -> ID estable, nunca sobrescribe version existente, redacta antes de escribir
**Criterios de aceptación**
- [ ] Un `case_id`+version existente nunca se sobrescribe; escribir de nuevo crea una version siguiente.
- [ ] La trayectoria y el contexto pasan por `redact.py` antes de tocar disco.
- [ ] Un caso rechazado se conserva; no hay borrado silencioso.

### T-05 - Puerta de aprobacion humana para Gold
- **Estado**: borrador
- **Tiempo humano**: est. 3h · real -
- **Prevision IA**: 35k in / 14k out tok
- **Dependencias**: T-04
- **Tipo**: backend
- **Archivos**: `skills/training-data-services/scripts/case-recorder.py`, `skills/training-data-services/scripts/test_case_recorder.py`
- **Verificacion**: `python -m pytest -q skills/training-data-services/scripts/test_case_recorder.py -k gold` -> transicion a approved rechazada sin `--approved-by-human`
**Criterios de aceptación**
- [ ] Sin el flag, marcar `approved` falla con mensaje explicito; `needs_changes`/`rejected` no lo requieren.
- [ ] Un caso `corrected` declara `supersedes_case` y se conserva junto al `failure` que corrige.

### T-06 - Indice `cases_index.jsonl` y consulta basica
- **Estado**: borrador
- **Tiempo humano**: est. 1h · real -
- **Prevision IA**: 10k in / 5k out tok
- **Dependencias**: T-04
- **Tipo**: backend
- **Archivos**: `skills/training-data-services/scripts/case-recorder.py`, `skills/training-data-services/scripts/test_case_recorder.py`
- **Verificacion**: `python -m pytest -q skills/training-data-services/scripts/test_case_recorder.py -k index` -> indice append-only coherente con `cases/`
**Criterios de aceptación**
- [ ] El indice se puede reconstruir desde `cases/` si se corrompe (caché, no fuente).

## Fase 3 - Dedup, particion y ensamblador

### T-07 - Deduplicacion por shingles (reutilizando `code-health.py`)
- **Estado**: borrador
- **Tiempo humano**: est. 5h · real -
- **Prevision IA**: 55k in / 22k out tok
- **Dependencias**: T-04
- **Tipo**: backend
- **Archivos**: `skills/training-data-services/scripts/dedup.py`, `skills/training-data-services/scripts/test_dedup.py`
- **Verificacion**: `python -m pytest -q skills/training-data-services/scripts/test_dedup.py` -> near-duplicates detectados sin embeddings, boilerplate fijo no da falsos positivos
**Criterios de aceptación**
- [ ] Dos casos casi identicos entre versiones se marcan como grupo de duplicados.
- [ ] Texto fijo compartido por todos los casos no dispara falsos positivos.

### T-08 - Particion anti-leakage por familia
- **Estado**: borrador
- **Tiempo humano**: est. 4h · real -
- **Prevision IA**: 45k in / 18k out tok
- **Dependencias**: T-07
- **Tipo**: backend
- **Archivos**: `skills/training-data-services/scripts/dataset-assembler.py`, `skills/training-data-services/scripts/test_dataset_assembler.py`
- **Verificacion**: `python -m pytest -q skills/training-data-services/scripts/test_dataset_assembler.py -k leakage` -> ninguna familia queda partida entre train y benchmark
**Criterios de aceptación**
- [ ] Sin al menos una familia reservada como benchmark, el ensamblador se niega a exportar y explica por que.

### T-09 - Ensamblador de dataset y puente a `knowledge-curator`
- **Estado**: borrador
- **Tiempo humano**: est. 5h · real -
- **Prevision IA**: 55k in / 22k out tok
- **Dependencias**: T-05, T-08
- **Tipo**: backend
- **Archivos**: `skills/training-data-services/scripts/dataset-assembler.py`, `skills/training-data-services/scripts/propose-from-case.py`, `skills/training-data-services/scripts/test_dataset_assembler.py`
- **Verificacion**: `python -m pytest -q skills/training-data-services/scripts/test_dataset_assembler.py` -> solo casos approved+humano entran; propuesta a Curator nunca auto-aprueba
**Criterios de aceptación**
- [ ] `train.jsonl`/`benchmark.jsonl` en formato chat (`messages`), manifiesto con hashes por caso.
- [ ] `propose-from-case.py` genera un candidato `pending` para `knowledge-curator`, nunca `approved`.

## Fase 4 - Setup, doctor y cierre

### T-10 - Opt-in en setup y doctor
- **Estado**: borrador
- **Tiempo humano**: est. 4h · real -
- **Prevision IA**: 45k in / 18k out tok
- **Dependencias**: T-09
- **Tipo**: devops
- **Archivos**: `commands/setup.md`, `commands/doctor.md`, `agent-kits/shared/doctor.py`, `agent-kits/shared/test_doctor.py`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `interop/**`
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_doctor.py` -> desactivado/activado, recuento por estado, dataset desactualizado; `python scripts/export-interop.py --check` -> 0
**Criterios de aceptación**
- [ ] Sin `training.json`, `/doctor` no reporta nada de esta capacidad; con el, informa sin bloquear.

### T-11 - Aislamiento, regresion, interop y cierre
- **Estado**: borrador
- **Tiempo humano**: est. 7h · real -
- **Prevision IA**: 65k in / 25k out tok
- **Dependencias**: T-01 a T-10
- **Tipo**: test
- **Archivos**: `tests/test_training_data_services.py`, `tests/test_hooks_shell.py`, `docs/agents/CONTRACTS.md`, `docs/README.md`, `CHANGELOG.md`, `CHANGELOG.es.md`, `interop/**`
- **Verificacion**: `python -m pytest -q tests/test_training_data_services.py tests/test_hooks_shell.py` -> ningun binario inline, ningun caso no-Gold exportado, hooks sin red; `python scripts/lint_plugin.py` -> 0 · `python evals/check.py` -> 0
**Criterios de aceptación**
- [ ] Suite completa en verde; revision de dos lentes sin gaps Critical/Important; QA sin UI verde; retro abre `retro-gate.py`.
