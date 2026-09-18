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
>
> **Enmienda 2026-09-17** (`ADR-018`): backends declarados + contrato de adaptador + esquema versionado + registro de capacidades + cola compartida. Cambian T-01, T-07, T-08, T-09; nace T-13. Las cifras anteriores (48h · 12 tareas) quedan en el historial de git.

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervision (real/est) | Tokens (real/est) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fase 1 - Contrato y validacion | 0 | 3 | 0% | 0 / 13h | 0 / 3.9h | 0 / 1.0h | 0 / 200k |
| Fase 2 - Curacion y workflow | 0 | 3 | 0% | 0 / 14h | 0 / 4.2h | 0 / 1.1h | 0 / 210k |
| Fase 3 - Backends y Kwipu | 0 | 4 | 0% | 0 / 19h | 0 / 5.7h | 0 / 1.4h | 0 / 275k |
| Fase 4 - Regresion y cierre | 0 | 3 | 0% | 0 / 10h | 0 / 3.0h | 0 / 0.7h | 0 / 130k |
| **TOTAL** | **0** | **13** | **0%** | **0 / 56h** | **0 / 16.8h** | **0 / 4.2h** | **0 / 815k** |

## Fase 1 - Contrato y validacion

### T-01 - Esquema versionado `taxonomy.schema.json`, `backends` y plantillas
- **Estado**: borrador
- **Tiempo humano**: est. 5h · real -
- **Prevision IA**: 55k in / 22k out tok
- **Dependencias**: ninguna
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/schemas/taxonomy.schema.json`, `agent-kits/shared/knowledge-schema.py`, `agent-kits/shared/test_knowledge_schema.py`, `agent-kits/shared/templates/taxonomy.json`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `docs/knowledge/adr/ADR-018-arquitectura-de-memoria-markdown-canonico-backends-declarados.md`
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_knowledge_schema.py` -> valida `taxonomy.json` (version, categorias, evidencia, `backends`, `routing`, `evidence_levels`, `denylist`) con validador stdlib; rechaza estado/tag invalidos y un `routing` que cite un backend no declarado (CA-11, CA-13)
**Criterios de aceptación**
- [ ] `taxonomy.json` define categorias, carpeta, evidencia minima, `backends` (id, type, config) y `routing` por categoria hacia ids declarados.
- [ ] Sin `taxonomy.json`, el plugin usa su default minimo propio (DECISION/PATTERN/GOTCHA/LESSON, backend `kwipu` desactivado) sin romper nada.
- [ ] Una categoria sin `routing`, o con un id no declarado, no exporta a ningun backend (fail-closed); el error nombra fichero y campo; `ADR-018` pasa a `aceptada` al cerrar.

### T-02 - Indice canonico y validador determinista sobre la taxonomia configurada
- **Estado**: borrador
- **Tiempo humano**: est. 5h · real -
- **Prevision IA**: 55k in / 22k out tok
- **Dependencias**: T-01
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/knowledge-schema.py`, `agent-kits/shared/knowledge-index.py`, `agent-kits/shared/test_knowledge_schema.py`, `agent-kits/shared/test_knowledge_index.py`, `docs/knowledge/README.md`
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_knowledge_schema.py agent-kits/shared/test_knowledge_index.py` -> indice estable y errores con ruta/campo, dos fixtures de `taxonomy.json` distintas dan carpetas/routing distintos
**Criterios de aceptación**
- [ ] ID duplicado, version y enlaces rotos fallan; candidatos no aparecen.
- [ ] `knowledge-find.py` no se rompe.
- [ ] Dos proyectos con `taxonomy.json` distintos (p. ej. el default del plugin vs. uno con categorias de dominio propio) producen carpetas y enrutado distintos sin tocar codigo.

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

### T-07 - `knowledge-sync.py`, contrato de adaptador y adaptador `test`
- **Estado**: borrador
- **Tiempo humano**: est. 7h · real -
- **Prevision IA**: 70k in / 30k out tok
- **Dependencias**: T-02, T-03, `session-end-durable-capture` T-01 (`outbox.py`)
- **Tipo**: backend
- **Archivos**: `skills/knowledge-services/scripts/knowledge-sync.py`, `skills/knowledge-services/backends/__init__.py`, `skills/knowledge-services/backends/README.md`, `skills/knowledge-services/scripts/test_knowledge_sync.py`, `evals/fixtures/knowledge-services/backend_test.py`, `.gitignore`
- **Verificacion**: `python -m pytest -q skills/knowledge-services/scripts/test_knowledge_sync.py` -> `routing` aplicado ANTES de `plan`; `--dry-run`/`--check`/`--rebuild`; staging y dead-letter via `outbox.py`; el adaptador `type: "test"` de la fixture recibe exactamente las entradas enrutadas sin tocar el nucleo (CA-12, CA-15)
**Criterios de aceptación**
- [ ] Solo approved valido; reejecucion idempotente; un error no borra la publicacion anterior.
- [ ] El contrato (`health · plan · apply · verify · rebuild · revoke`) esta documentado y un adaptador incompleto falla al cargar con mensaje claro.
- [ ] Una categoria con `routing.<id>: false` nunca llega al adaptador; `"summary"` entrega solo el resumen declarado.

### T-08 - Adaptador Kwipu (`markdown-export`) y skill
- **Estado**: borrador
- **Tiempo humano**: est. 5h · real -
- **Prevision IA**: 50k in / 20k out tok
- **Dependencias**: T-07
- **Tipo**: backend
- **Archivos**: `skills/knowledge-services/backends/markdown_export.py`, `skills/knowledge-services/scripts/test_backend_markdown_export.py`, `skills/knowledge-services/SKILL.md`, `skills/knowledge-services/references/`, `evals/cases/skill-knowledge-services.json`, `docs/README.md`, `CLAUDE.md`
- **Verificacion**: `python -m pytest -q skills/knowledge-services/scripts/test_backend_markdown_export.py` -> export con `manifest.json` y hashes estables, `health` con URL local/timeout/sano/degradado, `rebuild` reproduce el mismo manifiesto, `revoke` retira el fichero del export
**Criterios de aceptación**
- [ ] Kwipu es un adaptador mas del contrato de T-07; nada en `knowledge-sync.py` menciona Kwipu.
- [ ] Skill corta con referencias y sin secretos; no hooks/red ni Graphiti.

### T-09 - Opt-in en setup y doctor a traves del registro de capacidades
- **Estado**: borrador
- **Tiempo humano**: est. 4h · real -
- **Prevision IA**: 40k in / 16k out tok
- **Dependencias**: T-08, T-13
- **Tipo**: devops
- **Archivos**: `commands/setup.md`, `commands/doctor.md`, `agent-kits/shared/doctor.py`, `agent-kits/shared/test_doctor.py`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `docs/INTEROP.md`, `docs/en/INTEROP.md`, `interop/**`
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_doctor.py` -> desactivado, sano, timeout, export atrasado y `taxonomy.json` invalido con fichero+campo+arreglo; `doctor.py` no contiene la cadena `kwipu` (todo llega por `capabilities.py`); `python scripts/export-interop.py --check` -> 0
**Criterios de aceptación**
- [ ] Config no sensible e idempotente; no MCP automatico.
- [ ] Fallo opcional no es error de ciclo.
- [ ] `/setup` ofrece las capacidades registradas en un solo paso y escribe `taxonomy.json` desde la plantilla si no existe (CA-14).

### T-13 - Registro de capacidades `capabilities.py`
- **Estado**: borrador
- **Tiempo humano**: est. 3h · real -
- **Prevision IA**: 35k in / 14k out tok
- **Dependencias**: T-01
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/capabilities.py`, `agent-kits/shared/test_capabilities.py`, `agent-kits/shared/README.md`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_capabilities.py` -> registro con dos capacidades (`knowledge-gate`, `kwipu`) y una tercera de fixture; `enabled/health/doctor/setup_step` por capacidad; una capacidad rota degrada a `error` sin tumbar el resto
**Criterios de aceptación**
- [ ] Contrato `{id, config_path, enabled, health, doctor, setup_step}` documentado; sin dependencias.
- [ ] Anadir una capacidad es un registro nuevo, no una edicion de `doctor.py` (CA-14).

## Fase 4 - Regresion y cierre

### T-10 - Aislamiento, seguridad y regresion
- **Estado**: borrador
- **Tiempo humano**: est. 4h · real -
- **Prevision IA**: 40k in / 16k out tok
- **Dependencias**: T-01 a T-09, T-13
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
- [ ] Kwipu opcional/derivado; Graphiti diferido; ownership sin solape; doc del contrato de adaptador y de `backends` en ES/EN.

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