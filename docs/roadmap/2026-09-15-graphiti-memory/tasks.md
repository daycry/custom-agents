---
verificacion: obligatoria
---

# Checklist de Tareas - Memoria Graphiti

| **Estado** | borrador |
|---|---|
| **Plan** | [improvement-plan.md](improvement-plan.md) |

> **Ledger canonico de progreso.** Graphiti es una proyeccion; el avance y las fuentes siguen en Git.

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervision (real/est) | Tokens (real/est) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fase 1 - Contrato y modelo | 0 | 3 | 0% | 0 / 12h | 0 / 3.6h | 0 / 0.9h | 0 / 160k |
| Fase 2 - Sincronizacion | 0 | 3 | 0% | 0 / 12h | 0 / 3.6h | 0 / 0.9h | 0 / 150k |
| Fase 3 - Router y configuracion | 0 | 2 | 0% | 0 / 10h | 0 / 3h | 0 / 0.8h | 0 / 100k |
| Fase 4 - Regresion y cierre | 0 | 2 | 0% | 0 / 10h | 0 / 3h | 0 / 0.7h | 0 / 60k |
| **TOTAL** | **0** | **10** | **0%** | **0 / 44h** | **0 / 13.2h** | **0 / 3.3h** | **0 / 470k** |

## Fase 1 - Contrato y modelo

### T-01 - Puerta de dependencia y esquema de proyeccion
- **Estado**: borrador
- **Dependencias**: `knowledge-services` completado
- **Archivos**: `agent-kits/shared/knowledge-schema.py`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_knowledge_schema.py` -> rechaza cualquier entrada no aprobada
**Criterios de aceptación**
- [ ] El modelo exige ID, version, hash, evidencia y ruta fuente.

### T-02 - Ontologia y relaciones temporales
- **Estado**: borrador
- **Dependencias**: T-01
- **Archivos**: `skills/knowledge-services/`, `tests/test_graphiti_model.py`
- **Verificacion**: `python -m pytest -q tests/test_graphiti_model.py` -> relaciones y sucesion validas
**Criterios de aceptación**
- [ ] `SUPERSEDES` conserva historia y marca vigencia.

### T-03 - Politica de escritura y autoridad
- **Estado**: borrador
- **Dependencias**: T-01
- **Archivos**: `agents/knowledge-curator.md`, `docs/agents/ROLES.md`, `docs/agents/CONTRACTS.md`, `interop/**`
- **Verificacion**: `python scripts/lint_plugin.py` -> ownership y rutas validos
**Criterios de aceptación**
- [ ] Ningun agente normal escribe Graphiti.

## Fase 2 - Sincronizacion

### T-04 - Cliente Graphiti local y salud
- **Estado**: borrador
- **Dependencias**: T-01, T-02
- **Archivos**: `skills/knowledge-services/scripts/graphiti-health.py`, `skills/knowledge-services/scripts/test_graphiti_health.py`
- **Verificacion**: `python -m pytest -q skills/knowledge-services/scripts/test_graphiti_health.py` -> timeout y degradacion
**Criterios de aceptación**
- [ ] URL local permitida y telemetria configurable.

### T-05 - Sincronizador idempotente
- **Estado**: borrador
- **Dependencias**: T-04
- **Archivos**: `skills/knowledge-services/scripts/graphiti-sync.py`, `skills/knowledge-services/scripts/test_graphiti_sync.py`
- **Verificacion**: `python -m pytest -q skills/knowledge-services/scripts/test_graphiti_sync.py` -> sin duplicados ni borrado
**Criterios de aceptación**
- [ ] Solo sincroniza approved y conserva procedencia.

### T-06 - Reindexacion, manifiesto y recuperacion
- **Estado**: borrador
- **Dependencias**: T-05
- **Archivos**: `skills/knowledge-services/scripts/graphiti-sync.py`, `tests/test_graphiti_sync.py`
- **Verificacion**: `python -m pytest -q tests/test_graphiti_sync.py` -> desfase detectable y reconstruccion explicita
**Criterios de aceptación**
- [ ] Error parcial no invalida fuentes ni estado previo.

## Fase 3 - Router y configuracion

### T-07 - Router de consultas y fallback
- **Estado**: borrador
- **Dependencias**: T-05
- **Archivos**: `skills/knowledge-services/`, `tests/test_knowledge_router.py`
- **Verificacion**: `python -m pytest -q tests/test_knowledge_router.py` -> documental a Kwipu/local, temporal a Graphiti
**Criterios de aceptación**
- [ ] Resultados traen evidencia, estado y ruta canonica.

### T-08 - Setup, doctor y documentacion runtime
- **Estado**: borrador
- **Dependencias**: T-04, T-07
- **Archivos**: `commands/setup.md`, `commands/doctor.md`, `agent-kits/shared/doctor.py`, `docs/INTEROP.md`, `docs/en/INTEROP.md`, `interop/**`
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_doctor.py` -> off/sano/degradado
**Criterios de aceptación**
- [ ] Config no registra MCP ni toca configuracion global.

## Fase 4 - Regresion y cierre

### T-09 - Aislamiento, modelos locales y seguridad
- **Estado**: borrador
- **Dependencias**: T-01 a T-08
- **Archivos**: `tests/test_graphiti_security.py`, `tests/test_hooks_shell.py`
- **Verificacion**: `python -m pytest -q tests/test_graphiti_security.py tests/test_hooks_shell.py` -> sin datos excluidos ni red desde hooks
**Criterios de aceptación**
- [ ] Ollama JSON invalido degrada sin datos corruptos.

### T-10 - Interop, QA y retro
- **Estado**: borrador
- **Dependencias**: T-09
- **Archivos**: `docs/roadmap/2026-09-15-graphiti-memory/testing/`, `interop/**`
- **Verificacion**: `python scripts/lint_plugin.py` -> 0 · `python evals/check.py` -> 0 · `python scripts/export-interop.py --check` -> 0
**Criterios de aceptación**
- [ ] QA sin UI y revision no dejan gaps pendientes.