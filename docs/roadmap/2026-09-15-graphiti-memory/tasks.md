---
verificacion: obligatoria
---

# Checklist de Tareas - Memoria Graphiti

| **Estado** | borrador |
|---|---|
| **Plan** | [improvement-plan.md](improvement-plan.md) |

> **Ledger canonico de progreso.** Graphiti es una proyeccion; el avance y las fuentes siguen en Git.
>
> **Enmienda 2026-09-17** (`ADR-018`): Graphiti como segundo adaptador del contrato de knowledge-services, proveedor configurable, `mode: shadow`, rebuild/revoke y router por configuracion. Cambian T-01, T-02, T-04, T-05, T-06, T-07, T-08 (44h -> 50h).

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervision (real/est) | Tokens (real/est) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fase 1 - Contrato y modelo | 0 | 3 | 0% | 0 / 13h | 0 / 3.9h | 0 / 1.0h | 0 / 175k |
| Fase 2 - Sincronizacion | 0 | 3 | 0% | 0 / 16h | 0 / 4.8h | 0 / 1.2h | 0 / 200k |
| Fase 3 - Router y configuracion | 0 | 2 | 0% | 0 / 11h | 0 / 3.3h | 0 / 0.9h | 0 / 110k |
| Fase 4 - Regresion y cierre | 0 | 2 | 0% | 0 / 10h | 0 / 3h | 0 / 0.7h | 0 / 60k |
| **TOTAL** | **0** | **10** | **0%** | **0 / 50h** | **0 / 15h** | **0 / 3.8h** | **0 / 545k** |

## Fase 1 - Contrato y modelo

### T-01 - Puerta de dependencia, `backends.graphiti` en el esquema y suite de contrato
- **Estado**: borrador
- **Dependencias**: `knowledge-services` completado (T-07 contrato de adaptador, T-13 capabilities)
- **Archivos**: `agent-kits/shared/schemas/taxonomy.schema.json`, `agent-kits/shared/knowledge-schema.py`, `agent-kits/shared/test_knowledge_schema.py`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_knowledge_schema.py -k graphiti` -> valida `backends.graphiti` (`mode`, `provider`, `router`, `relations`, `allow_remote`) y rechaza cualquier entrada no aprobada; la suite de contrato de adaptadores de knowledge-services corre contra un `graphiti.py` vacio y falla con mensaje claro
**Criterios de aceptación**
- [ ] El modelo exige ID, version, hash, evidencia y ruta fuente.
- [ ] `provider.llm` acepta `ollama | openai | anthropic | none`; ningun modelo ni endpoint tiene default cableado salvo loopback (CA-09).

### T-02 - Ontologia derivada de `taxonomy.json` y relaciones temporales
- **Estado**: borrador
- **Dependencias**: T-01
- **Archivos**: `skills/knowledge-services/backends/graphiti_model.py`, `tests/test_graphiti_model.py`
- **Verificacion**: `python -m pytest -q tests/test_graphiti_model.py` -> nucleo `Knowledge`/`Evidence` + un `entity_type` por categoria de dos `taxonomy.json` distintos; relaciones nucleo + `relations` declaradas; sucesion valida
**Criterios de aceptación**
- [ ] `SUPERSEDES` conserva historia y marca vigencia.
- [ ] Ninguna lista de tipos de dominio en el codigo del plugin (CA-13).

### T-03 - Politica de escritura y autoridad
- **Estado**: borrador
- **Dependencias**: T-01
- **Archivos**: `agents/knowledge-curator.md`, `docs/agents/ROLES.md`, `docs/agents/CONTRACTS.md`, `interop/**`
- **Verificacion**: `python scripts/lint_plugin.py` -> ownership y rutas validos
**Criterios de aceptación**
- [ ] Ningun agente normal escribe Graphiti.

## Fase 2 - Sincronizacion

### T-04 - Adaptador `graphiti.py`: cliente, `health` y proveedores
- **Estado**: borrador
- **Dependencias**: T-01, T-02
- **Archivos**: `skills/knowledge-services/backends/graphiti.py`, `skills/knowledge-services/backends/graphiti_providers.py`, `skills/knowledge-services/scripts/test_backend_graphiti.py`
- **Verificacion**: `python -m pytest -q skills/knowledge-services/scripts/test_backend_graphiti.py -k "health or provider"` -> timeout y degradacion; `allow_remote: false` rechaza endpoint no loopback; los cuatro proveedores comparten firma y `none` no llama a ningun modelo
**Criterios de aceptación**
- [ ] URL local permitida y telemetria configurable; credenciales solo por nombre de variable de entorno.
- [ ] Anadir un proveedor es una funcion nueva en `graphiti_providers.py`, sin tocar `graphiti.py`.

### T-05 - `plan`/`apply` idempotentes sobre `outbox.py` y `mode: shadow`
- **Estado**: borrador
- **Dependencias**: T-04
- **Archivos**: `skills/knowledge-services/backends/graphiti.py`, `skills/knowledge-services/scripts/test_backend_graphiti.py`
- **Verificacion**: `python -m pytest -q skills/knowledge-services/scripts/test_backend_graphiti.py -k "plan or apply or shadow"` -> `knowledge-sync.py --backend graphiti` sin duplicados ni borrado; reintento acotado y dead-letter via `outbox.py`; fixture de salida estructurada invalida de Ollama -> dead-letter sin datos en el grafo (CA-14); en `shadow` ninguna lectura
**Criterios de aceptación**
- [ ] Solo sincroniza approved y conserva procedencia; el adaptador solo recibe entradas ya filtradas por `routing` (el nucleo lo garantiza, CA-07/CA-08).
- [ ] `mode` default `shadow`; `read` exige `health` sano y `verify` sin desfase (CA-10).

### T-06 - `verify`, `rebuild` reproducible y `revoke`
- **Estado**: borrador
- **Dependencias**: T-05
- **Archivos**: `skills/knowledge-services/backends/graphiti.py`, `skills/knowledge-services/scripts/test_backend_graphiti.py`
- **Verificacion**: `python -m pytest -q skills/knowledge-services/scripts/test_backend_graphiti.py -k "verify or rebuild or revoke"` -> desfase detectable; `--rebuild` reproduce el mismo hash de manifiesto que la sincronizacion incremental; `revoke` deja tombstone sin borrar historial
**Criterios de aceptación**
- [ ] Error parcial no invalida fuentes ni estado previo.
- [ ] Una entrada retirada de `approved/` aparece invalidada en el grafo tras la siguiente sincronizacion (CA-11).

## Fase 3 - Router y configuracion

### T-07 - Router por configuracion e intent declarado
- **Estado**: borrador
- **Dependencias**: T-05, T-06
- **Archivos**: `agent-kits/shared/knowledge-find.py`, `agent-kits/shared/test_knowledge_find.py`, `tests/test_knowledge_router.py`
- **Verificacion**: `python -m pytest -q tests/test_knowledge_router.py agent-kits/shared/test_knowledge_find.py -k intent` -> sin `--intent` o con intent no declarado -> local/Kwipu; `--intent temporal` con `mode: read` y `intents.temporal: true` -> Graphiti; con `mode: shadow` -> local aunque el intent este declarado
**Criterios de aceptación**
- [ ] Resultados traen evidencia, estado y ruta canonica.
- [ ] Ningun LLM decide el enrutado; las reglas viven en `backends.graphiti.router` (CA-12).

### T-08 - Capacidad `graphiti` registrada, setup/doctor y documentacion runtime
- **Estado**: borrador
- **Dependencias**: T-04, T-07
- **Archivos**: `agent-kits/shared/capabilities.py`, `agent-kits/shared/test_capabilities.py`, `commands/setup.md`, `commands/doctor.md`, `docs/INTEROP.md`, `docs/en/INTEROP.md`, `interop/**`
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_capabilities.py agent-kits/shared/test_doctor.py -k graphiti` -> off/shadow/read/degradado con veredicto y remedio; `doctor.py` no contiene la cadena `graphiti`
**Criterios de aceptación**
- [ ] Config no registra MCP ni toca configuracion global.
- [ ] La capacidad entra por `capabilities.py`, sin editar `doctor.py` (CA-14 de knowledge-services).

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