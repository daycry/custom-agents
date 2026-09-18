---
verificacion: obligatoria
---

# Checklist de Tareas - Dogfooding del dev-cycle

| **Estado** | borrador |
|---|---|
| **Plan** | [improvement-plan.md](improvement-plan.md) |
| **Diseno** | [design.md](design.md), O1 |

> **Ledger canonico de progreso.** El dataset resultante vive fuera de Git; el avance de ESTA iniciativa sigue aqui.

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervision (real/est) | Tokens (real/est) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fase 1 - Opt-in y mapeo | 0 | 2 | 0% | 0 / 7h | 0 / 2.1h | 0 / 0.5h | 0 / 95k |
| Fase 2 - Derivacion deterministica | 0 | 2 | 0% | 0 / 7h | 0 / 2.1h | 0 / 0.5h | 0 / 95k |
| Fase 3 - Hook Fase 6 y full-diff | 0 | 2 | 0% | 0 / 5h | 0 / 1.5h | 0 / 0.4h | 0 / 80k |
| Fase 4 - Regresion y cierre | 0 | 2 | 0% | 0 / 3h | 0 / 0.9h | 0 / 0.2h | 0 / 30k |
| **TOTAL** | **0** | **8** | **0%** | **0 / 26h** | **0 / 7.8h** | **0 / 2h** | **0 / 360k** |

## Fase 1 - Opt-in y mapeo (modo metadata)

### T-01 - Opt-in `datasetCapture` en `.claude/dev.json`
- **Estado**: borrador
- **Tiempo humano**: est. 3h · real -
- **Prevision IA**: 30k in / 12k out tok
- **Dependencias**: `training-data-services` implementado
- **Tipo**: devops
- **Archivos**: `commands/setup.md`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `interop/**`
- **Verificacion**: `python -m pytest -q tests/test_hooks_shell.py -k dataset_capture` -> desactivado por defecto; `python scripts/export-interop.py --check` -> 0
**Criterios de aceptación**
- [ ] `enabled: false` por defecto; `mode` por defecto `metadata`.
- [ ] `/setup` explica el riesgo de `full-diff` en una frase antes de ofrecerlo.

### T-02 - Extraccion de campos con lista blanca (modo metadata)
- **Estado**: borrador
- **Tiempo humano**: est. 4h · real -
- **Prevision IA**: 40k in / 16k out tok
- **Dependencias**: T-01
- **Tipo**: backend
- **Archivos**: `skills/dev-cycle-dataset/scripts/case-from-task.py`, `skills/dev-cycle-dataset/scripts/test_case_from_task.py`
- **Verificacion**: `python -m pytest -q skills/dev-cycle-dataset/scripts/test_case_from_task.py` -> ningun campo fuera de la lista blanca aparece en el caso
**Criterios de aceptación**
- [ ] Un campo libre de `tasks.md` (p. ej. `- **Notas**:`) NUNCA entra en la trayectoria.
- [ ] Los textos capturados pasan por `redact.py` antes de escribirse.

## Fase 2 - Derivacion deterministica

### T-03 - Derivar `outcome`/`validation` de senales existentes
- **Estado**: borrador
- **Tiempo humano**: est. 4h · real -
- **Prevision IA**: 40k in / 16k out tok
- **Dependencias**: T-02
- **Tipo**: backend
- **Archivos**: `skills/dev-cycle-dataset/scripts/case-from-task.py`, `skills/dev-cycle-dataset/scripts/test_case_from_task.py`
- **Verificacion**: `python -m pytest -q skills/dev-cycle-dataset/scripts/test_case_from_task.py -k outcome` -> qa-gate rojo nunca produce `approved`; gaps pendientes nunca producen `success`
**Criterios de aceptación**
- [ ] `approved` exige `qa-gate` exit 0 Y revision sin gaps `Critical`/`Important`.
- [ ] `T-XX-fix<N>` en `usage-meter` produce `outcome: corrected` con `supersedes_case` al intento original.

### T-04 - Familia = iniciativa completa
- **Estado**: borrador
- **Tiempo humano**: est. 3h · real -
- **Prevision IA**: 30k in / 12k out tok
- **Dependencias**: T-03
- **Tipo**: backend
- **Archivos**: `skills/dev-cycle-dataset/scripts/case-from-task.py`, `skills/dev-cycle-dataset/scripts/test_case_from_task.py`
- **Verificacion**: `python -m pytest -q skills/dev-cycle-dataset/scripts/test_case_from_task.py -k familia` -> tareas de la misma iniciativa nunca quedan en lados distintos de la particion
**Criterios de aceptación**
- [ ] Una iniciativa con 3 tareas casi identicas cae entera en train o entera en benchmark.

## Fase 3 - Hook Fase 6 y full-diff

### T-05 - Punto de aprobacion humana en el ritual de cierre
- **Estado**: borrador
- **Tiempo humano**: est. 3h · real -
- **Prevision IA**: 30k in / 12k out tok
- **Dependencias**: T-03
- **Tipo**: docs
- **Archivos**: `commands/dev-cycle.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `docs/agents/CONTRACTS.md`, `interop/**`
- **Verificacion**: `python scripts/export-interop.py --check` -> 0; lectura: el paso 4 del ritual de cierre queda documentado como el punto de `--approved-by-human`
**Criterios de aceptación**
- [ ] El flag humano se pide en el mismo paso donde ya se decide integrar la rama, no en un paso nuevo.

### T-06 - Modo `full-diff` opt-in separado
- **Estado**: borrador
- **Tiempo humano**: est. 2h · real -
- **Prevision IA**: 20k in / 8k out tok
- **Dependencias**: T-01, T-02
- **Tipo**: backend
- **Archivos**: `skills/dev-cycle-dataset/scripts/case-from-task.py`, `skills/dev-cycle-dataset/scripts/test_case_from_task.py`
- **Verificacion**: `python -m pytest -q skills/dev-cycle-dataset/scripts/test_case_from_task.py -k full_diff` -> activar solo `enabled` nunca activa `full-diff`
**Criterios de aceptación**
- [ ] `full-diff` requiere las dos claves activas a la vez; una sola nunca basta.

## Fase 4 - Regresion y cierre

### T-07 - Regresion de aislamiento y seguridad
- **Estado**: borrador
- **Tiempo humano**: est. 2h · real -
- **Prevision IA**: 20k in / 8k out tok
- **Dependencias**: T-01 a T-06
- **Tipo**: test
- **Archivos**: `tests/test_dev_cycle_dataset.py`
- **Verificacion**: `python -m pytest -q tests/test_dev_cycle_dataset.py` -> ningun caso en modo metadata contiene fragmentos de diff
**Criterios de aceptación**
- [ ] Mutante que fuerza incluir el diff en modo metadata hace fallar el test.

### T-08 - Documentacion, interop y cierre
- **Estado**: borrador
- **Tiempo humano**: est. 1h · real -
- **Prevision IA**: 10k in / 4k out tok
- **Dependencias**: T-07
- **Tipo**: docs
- **Archivos**: `docs/README.md`, `CHANGELOG.md`, `CHANGELOG.es.md`, `interop/**`
- **Verificacion**: `python scripts/lint_plugin.py` -> 0 · `python evals/check.py` -> 0 · `python scripts/export-interop.py --check` -> 0
**Criterios de aceptación**
- [ ] Suite completa en verde; revision de dos lentes sin gaps pendientes; QA sin UI verde; retro abre `retro-gate.py`.
