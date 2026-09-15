---
generacion: {fuente: estimado, tokens_reales: {entrada: 0, salida: 0, cache_creacion: 0, cache_lectura: 0}, eur: null, horas_ia: 0.0, duracion: 0m, ratio_usado: 0}
verificacion: obligatoria
---

# Checklist de Tareas - Servicios de conocimiento locales

| **Estado** | borrador |
|---|---|
| **Plan** | [improvement-plan.md](improvement-plan.md) |
| **Diseno** | [design.md](design.md), O1 |

> **Ledger canonico de progreso.** Esta es la fuente unica de avance; los servicios externos son espejo.

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervision (real/est) | Tokens (real/est) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fase 1 - Contrato y validacion | 0 | 3 | 0% | 0 / 12h | 0 / 3.6h | 0 / 0.9h | 0 / 185k |
| Fase 2 - Curacion y workflow | 0 | 3 | 0% | 0 / 14h | 0 / 4.2h | 0 / 1.1h | 0 / 210k |
| Fase 3 - Kwipu | 0 | 3 | 0% | 0 / 12h | 0 / 3.6h | 0 / 0.9h | 0 / 190k |
| Fase 4 - Regresion y cierre | 0 | 3 | 0% | 0 / 10h | 0 / 3.0h | 0 / 0.7h | 0 / 130k |
| **TOTAL** | **0** | **12** | **0%** | **0 / 48h** | **0 / 14.4h** | **0 / 3.6h** | **0 / 715k** |

## Fase 1 - Contrato y validacion

### T-01 - Esquema, taxonomia y plantillas
- **Estado**: borrador
- **Tiempo humano**: est. 4h · real -
- **Prevision IA**: 45k in / 18k out tok
- **Dependencias**: ninguna
- **Tipo**: docs
- **Archivos**: `agent-kits/shared/`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `docs/knowledge/adr/`
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_knowledge_schema.py` -> valida entradas y rechaza categoria/estado/tag invalidos
**Criterios de aceptación**
- [ ] Esquema con ID, version, fuentes, evidencia y sucesion.
- [ ] Taxonomia cerrada y ADR propuesta.

### T-02 - Indice canonico y validador determinista
- **Estado**: borrador
- **Tiempo humano**: est. 5h · real -
- **Prevision IA**: 55k in / 22k out tok
- **Dependencias**: T-01
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/knowledge-schema.py`, `agent-kits/shared/knowledge-index.py`, `agent-kits/shared/test_knowledge_schema.py`, `agent-kits/shared/test_knowledge_index.py`, `docs/knowledge/README.md`
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_knowledge_schema.py agent-kits/shared/test_knowledge_index.py` -> indice estable y errores con ruta/campo
**Criterios de aceptación**
- [ ] ID duplicado, version y enlaces rotos fallan; candidatos no aparecen.
- [ ] `knowledge-find.py` no se rompe.

### T-03 - Estructura e ignorados de derivados
- **Estado**: borrador
- **Tiempo humano**: est. 3h · real -
- **Prevision IA**: 35k in / 10k out tok
- **Dependencias**: T-01
- **Tipo**: docs
- **Archivos**: `.gitignore`, `docs/knowledge/candidates/`, `docs/knowledge/approved/`, `docs/knowledge/README.md`
- **Verificacion**: `python -m pytest -q tests/test_knowledge_index.py` -> fuentes e indice coherentes sin derivados
**Criterios de aceptación**
- [ ] Sin arbol projects; ownership documentado; export no versionado.

## Fase 2 - Curacion y workflow

### T-04 - Agente knowledge-curator, docs y evals
- **Estado**: borrador
- **Tiempo humano**: est. 5h · real -
- **Prevision IA**: 55k in / 24k out tok
- **Dependencias**: T-01, T-02
- **Tipo**: docs
- **Archivos**: `agents/knowledge-curator.md`, `agent-kits/knowledge-curator/`, `docs/agents/knowledge-curator.md`, `docs/agents/ROLES.md`, `docs/README.md`, `CLAUDE.md`, `evals/cases/agent-knowledge-curator.json`, `interop/**`
- **Verificacion**: `python scripts/lint_plugin.py` -> frontmatter/dependencias; `python evals/check.py` -> casos de activacion
**Criterios de aceptación**
- [ ] Unico escritor de candidatos/aprobados; contradicciones y alto impacto piden usuario.
- [ ] Interop regenerado.

### T-05 - Documenter propone, no promociona
- **Estado**: borrador
- **Tiempo humano**: est. 4h · real -
- **Prevision IA**: 45k in / 18k out tok
- **Dependencias**: T-04
- **Tipo**: docs
- **Archivos**: `agents/documenter.md`, `docs/agents/documenter.md`, `docs/agents/ROLES.md`, `docs/agents/CONTRACTS.md`, `evals/cases/agent-documenter.json`, `interop/**`
- **Verificacion**: `python scripts/lint_plugin.py` -> contratos/rutas; `python evals/check.py` -> activacion
**Criterios de aceptación**
- [ ] Propuesta incluye categoria, fuentes y evidencia; sin propuesta no hay fallo.
- [ ] No escribe estados ni exports.

### T-06 - Fase 4-bis Knowledge Gate
- **Estado**: borrador
- **Tiempo humano**: est. 5h · real -
- **Prevision IA**: 50k in / 20k out tok
- **Dependencias**: T-04, T-05
- **Tipo**: docs
- **Archivos**: `commands/dev-cycle.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `docs/agents/ROLES.md`, `docs/agents/CONTRACTS.md`, `evals/cases/command-dev-cycle.json`, `interop/**`
- **Verificacion**: `python scripts/export-interop.py --check` -> 0; `python evals/check.py` -> 0
**Criterios de aceptación**
- [ ] Solo tras QA/documenter; omision honesta sin candidatos.
- [ ] Kwipu no condiciona cierre.

## Fase 3 - Kwipu

### T-07 - Exportador atomico y manifiesto
- **Estado**: borrador
- **Tiempo humano**: est. 6h · real -
- **Prevision IA**: 65k in / 28k out tok
- **Dependencias**: T-02, T-03
- **Tipo**: backend
- **Archivos**: `skills/knowledge-services/scripts/kwipu-export.py`, `skills/knowledge-services/scripts/test_kwipu_export.py`, `.gitignore`
- **Verificacion**: `python -m pytest -q skills/knowledge-services/scripts/test_kwipu_export.py` -> hash estable, staging atomico, filtrado negativo
**Criterios de aceptación**
- [ ] Solo approved valido; reejecucion idempotente.
- [ ] Un error no borra export anterior.

### T-08 - Skill y salud de Kwipu
- **Estado**: borrador
- **Tiempo humano**: est. 3h · real -
- **Prevision IA**: 35k in / 12k out tok
- **Dependencias**: T-07
- **Tipo**: backend
- **Archivos**: `skills/knowledge-services/`, `evals/cases/skill-knowledge-services.json`, `docs/README.md`, `CLAUDE.md`
- **Verificacion**: `python -m pytest -q skills/knowledge-services/scripts/test_kwipu_health.py` -> URL local, timeout, sano y degradado
**Criterios de aceptación**
- [ ] Skill corta con referencias y sin secretos.
- [ ] No hooks/red ni Graphiti.

### T-09 - Opt-in setup y doctor
- **Estado**: borrador
- **Tiempo humano**: est. 3h · real -
- **Prevision IA**: 35k in / 15k out tok
- **Dependencias**: T-08
- **Tipo**: devops
- **Archivos**: `commands/setup.md`, `commands/doctor.md`, `agent-kits/shared/doctor.py`, `agent-kits/shared/test_doctor.py`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `docs/INTEROP.md`, `docs/en/INTEROP.md`, `interop/**`
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_doctor.py` -> desactivado, sano, timeout y export atrasado; `python scripts/export-interop.py --check` -> 0
**Criterios de aceptación**
- [ ] Config no sensible e idempotente; no MCP automatico.
- [ ] Fallo opcional no es error de ciclo.

## Fase 4 - Regresion y cierre

### T-10 - Aislamiento, seguridad y regresion
- **Estado**: borrador
- **Tiempo humano**: est. 4h · real -
- **Prevision IA**: 40k in / 16k out tok
- **Dependencias**: T-01 a T-09
- **Tipo**: test
- **Archivos**: `tests/test_knowledge_services.py`, `tests/test_hooks_shell.py`, `tests/test_lint_plugin.py`, `evals/fixtures/`, `docs/agents/CONTRACTS.md`
- **Verificacion**: `python -m pytest -q tests/test_knowledge_services.py tests/test_hooks_shell.py tests/test_lint_plugin.py` -> export aislado y hooks sin red
**Criterios de aceptación**
- [ ] Mutantes de filtrado mueren.
- [ ] YAML corrupto y rutas maliciosas fallan de forma segura.

### T-11 - Documentacion, espejos y changelog
- **Estado**: borrador
- **Tiempo humano**: est. 3h · real -
- **Prevision IA**: 30k in / 12k out tok
- **Dependencias**: T-04 a T-10
- **Tipo**: docs
- **Archivos**: `README.md`, `README.es.md`, `docs/README.md`, `docs/en/README.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `docs/INTEROP.md`, `docs/en/INTEROP.md`, `docs/agents/ROLES.md`, `docs/agents/CONTRACTS.md`, `CHANGELOG.md`, `CHANGELOG.es.md`
- **Verificacion**: `python scripts/lint_plugin.py` -> 0; lectura: ES/EN comparten alcance
**Criterios de aceptación**
- [ ] Kwipu opcional/derivado; Graphiti diferido; ownership sin solape.

### T-12 - Puertas completas, QA y retro
- **Estado**: borrador
- **Tiempo humano**: est. 3h · real -
- **Prevision IA**: 20k in / 12k out tok
- **Dependencias**: T-10, T-11
- **Tipo**: test
- **Archivos**: `docs/roadmap/2026-09-15-knowledge-services/tasks.md`, `docs/roadmap/2026-09-15-knowledge-services/testing/`, `interop/**`
- **Verificacion**: `python scripts/lint_plugin.py` -> 0 · `python evals/check.py` -> 0 · `python scripts/export-interop.py --check` -> 0
**Criterios de aceptación**
- [ ] Ledger con evidencia y revision sin gaps Critical/Important.
- [ ] QA reconoce sin UI y retro abre `retro-gate.py`.