---
verificacion: obligatoria
---

# Checklist de Tareas - Memoria Graphiti

| **Estado** | en-progreso |
|---|---|
| **Plan** | [improvement-plan.md](improvement-plan.md) |

> **Ledger canonico de progreso.** Graphiti es una proyeccion; el avance y las fuentes siguen en Git.
>
> **Enmienda 2026-09-17** (`ADR-018`): Graphiti como segundo adaptador del contrato de knowledge-services, proveedor configurable, `mode: shadow`, rebuild/revoke y router por configuracion. Cambian T-01, T-02, T-04, T-05, T-06, T-07, T-08 (44h -> 50h).
>
> **Enmienda 2026-09-18** (handshake MCP real contra `dockers/knowledge-graphs`, CA-13 reformulado + CA-15): cliente MCP streamable HTTP minimo (`/mcp` sin barra, 307, `Mcp-Session-Id`), tipos de entidad del servidor con mapeo por configuracion, `revoke` sin `delete_episode`. Precisa T-02, T-04 y T-06 sin cambiar horas.

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervision (real/est) | Tokens (real/est) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fase 1 - Contrato y modelo | 3 | 3 | 100% | 0 / 13h | 0.65 / 3.9h | 0 / 1.0h | ~311k / 175k |
| Fase 2 - Sincronizacion | 0 | 3 | 0% | 0 / 16h | 0 / 4.8h | 0 / 1.2h | 0 / 200k |
| Fase 3 - Router y configuracion | 0 | 2 | 0% | 0 / 11h | 0 / 3.3h | 0 / 0.9h | 0 / 110k |
| Fase 4 - Regresion y cierre | 0 | 2 | 0% | 0 / 10h | 0 / 3h | 0 / 0.7h | 0 / 60k |
| **TOTAL** | **3** | **10** | **30%** | **0 / 50h** | **0.65 / 15h** | **0 / 3.8h** | **~311k / 545k** |

## Fase 1 - Contrato y modelo

### T-01 - Puerta de dependencia, `backends.graphiti` en el esquema y suite de contrato
- **Estado**: completado
- **Dependencias**: `knowledge-services` completado (T-07 contrato de adaptador, T-13 capabilities)
- **Archivos**: `agent-kits/shared/schemas/taxonomy.schema.json`, `agent-kits/shared/knowledge-schema.py`, `agent-kits/shared/test_knowledge_schema.py`, `agent-kits/shared/templates/taxonomy.json`, `skills/knowledge-services/scripts/test_backends_init.py`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_knowledge_schema.py -k graphiti` -> valida `backends.graphiti` (`mode`, `provider`, `router`, `relations`, `allow_remote`) y rechaza cualquier entrada no aprobada; la suite de contrato de adaptadores de knowledge-services corre contra un `graphiti.py` vacio y falla con mensaje claro. Salida real:
  ```
  $ python -m pytest -q agent-kits/shared/test_knowledge_schema.py -k graphiti
  ...............                                                          [100%]
  15 passed, 47 deselected in 0.08s

  $ python -m pytest -q skills/knowledge-services/scripts/test_backends_init.py -k graphiti
  .                                                                        [100%]
  1 passed, 3 deselected in 0.22s
  ```
  RED previo (evidencia TDD, 2026-09-19): `agent-kits/shared/test_knowledge_schema.py -k graphiti` falló con `11 failed, 4 passed` antes de implementar `_validar_backend_graphiti`/el bloque `backends.graphiti` de la plantilla; el test del `graphiti.py` vacío (`test_adaptador_graphiti_vacio_falla_con_mensaje_claro`) pasó en verde desde el primer intento porque reutiliza el mecanismo genérico ya existente de `AdaptadorNoDisponible` (`backends/__init__.py`), sin necesitar código nuevo — TDD n/a para esa parte concreta.
- **Changelog**: Los proyectos pueden declarar un backend Graphiti opcional (desactivado por defecto) en su configuración de conocimiento, con validación de endpoint local, proveedor de modelo y reglas de enrutado.
- **Tiempo humano**: est. - · real -
- **Tiempo IA**: real 0.14h (medido; usage-meter, artefacto `graphiti-memory/T-01`, 4m reloj, 3.64 EUR)
**Criterios de aceptación**
- [x] El modelo exige ID, version, hash, evidencia y ruta fuente. *(hereda del contrato ya validado por `knowledge-schema.py` para toda entrada `approved`; sin cambio en T-01, que añade la config del backend, no el modelo de entrada — ver T-02 para el modelo de nodos/relaciones.)*
- [x] `provider.llm` acepta `ollama | openai | anthropic | none`; ningun modelo ni endpoint tiene default cableado salvo loopback (CA-09). Cubierto por `test_graphiti_provider_llm_invalido`, `test_graphiti_provider_none_no_exige_modelo`, `test_graphiti_endpoint_no_local_sin_allow_remote_falla`.

### T-02 - Ontologia derivada de `taxonomy.json` y relaciones temporales
- **Estado**: completado
- **Dependencias**: T-01
- **Archivos**: `skills/knowledge-services/backends/graphiti_model.py`, `tests/test_graphiti_model.py`, `tests/test_console_encoding.py`
- **Verificacion**: `python -m pytest -q tests/test_graphiti_model.py` -> cada categoria de dos `taxonomy.json` distintos se mapea a un tipo declarado por el servidor via `backends.graphiti.entity_map` (default `Document`), y una categoria sin mapeo cae al default sin fallar; `--propose-config` emite el bloque `entity_types` (uno por categoria + `Knowledge`, `Evidence`) en YAML valido; relaciones nucleo + `relations` declaradas; sucesion valida
  - RED: `tests/test_graphiti_model.py` fallaba con `FileNotFoundError` al cargar `skills/knowledge-services/backends/graphiti_model.py` (el modulo no existia) · 2026-09-19
  - GREEN: `python -m pytest -q tests/test_graphiti_model.py` -> `14 passed in 0.12s`
  - `python -m pytest -q tests/test_console_encoding.py` -> `385 passed in 91.10s` (snippet UTF-8 + entradas en `SIN_SIMBOLOS_EN_LA_SALIDA`/`_modos()` para el nuevo modulo, regla 8 de CONVENTIONS)
- **Changelog**: Graphiti ya deriva sus tipos de entidad y relaciones desde la taxonomia del proyecto, sin listas de dominio fijas en el plugin.
- **Tiempo humano**: est. - · real -
- **Tiempo IA**: real 0.33h (medido; usage-meter, artefacto graphiti-memory/T-02, 10m reloj, 3.50 EUR)
**Criterios de aceptación**
- [x] `SUPERSEDES` conserva historia y marca vigencia — `cadena_supersedes()` devuelve `relaciones` (todas las `SUPERSEDES` consecutivas, ninguna version se pierde), `vigentes` (solo la ultima) e `invalidados` (las anteriores); `vigentes | invalidados` es siempre el conjunto completo de entrada (`test_cadena_supersedes_conserva_historia_y_marca_vigencia`).
- [x] Ninguna lista de tipos de dominio en el codigo del plugin; los tipos efectivos son los del servidor y el mapeo es configuracion (CA-13 reformulado, enmienda 2026-09-18) — `tipo_entidad`/`tipos_por_categoria` solo leen `config["entity_map"]` (config del proyecto) y caen a `Document` (el generico del servidor de referencia) sin declarar ningun tipo de dominio; probado contra dos `taxonomy.json` distintos (`test_tipos_por_categoria_dos_taxonomias_distintas`).

### T-03 - Politica de escritura y autoridad
- **Estado**: completado
- **Dependencias**: T-01
- **Archivos**: `agents/knowledge-curator.md`, `docs/agents/knowledge-curator.md`, `docs/agents/ROLES.md`, `docs/agents/CONTRACTS.md`, `interop/**`
- **Verificacion**: `python scripts/lint_plugin.py` -> ownership y rutas validos
  - TDD n/a: cambio de documentacion/ownership (frontmatter, matrices y prosa), sin codigo testeable propio; la puerta mecanica es el propio linter y el `grep` declarado en la nueva arista E18
  - `python scripts/lint_plugin.py` -> `10 agentes · 0 errores · 4 avisos` (los 4 avisos son previos al cambio: 3 nombres de comando genericos + 1 cita a `skills/knowledge-services/backends/graphiti.py`, que llega en T-04 y aun no existe)
  - `python scripts/export-interop.py && python scripts/export-interop.py --check` -> `50 ficheros escritos` y `50 ficheros al dia`
  - `grep -rn -i graphiti agents/*.md | grep -v knowledge-curator` -> salida vacia (ningun otro agente cita Graphiti)
- **Changelog**: Documentada la unica via de escritura a Graphiti (knowledge-sync.py tras la aprobacion del curator); ningun agente normal escribe en el grafo directamente.
- **Tiempo humano**: est. - · real -
- **Tiempo IA**: real 0.18h (medido; usage-meter, artefacto graphiti-memory/T-03, 3m reloj, 2.17 EUR)
**Criterios de aceptación**
- [x] Ningun agente normal escribe Graphiti — `agents/knowledge-curator.md`/`docs/agents/knowledge-curator.md` declaran a `knowledge-sync.py` (disparado tras la aprobacion del Curator, filtrado por `routing.graphiti`) como unica via; `docs/agents/ROLES.md` y la nueva arista **E18** de `docs/agents/CONTRACTS.md` lo dejan escrito con puerta ejecutable (`grep` sobre `agents/*.md`); ningun otro fichero de `agents/` cita Graphiti (verificado arriba).

## Fase 2 - Sincronizacion

### T-04 - Adaptador `graphiti.py`: cliente, `health` y proveedores
- **Estado**: borrador
- **Dependencias**: T-01, T-02
- **Archivos**: `skills/knowledge-services/backends/graphiti.py`, `skills/knowledge-services/backends/graphiti_providers.py`, `skills/knowledge-services/scripts/test_backend_graphiti.py`
- **Verificacion**: `python -m pytest -q skills/knowledge-services/scripts/test_backend_graphiti.py -k "health or provider or mcp"` -> timeout y degradacion; `allow_remote: false` rechaza endpoint no loopback; los cuatro proveedores comparten firma y `none` no llama a ningun modelo; contra un servidor MCP falso de la suite: `initialize` -> `notifications/initialized` -> `tools/call get_status` con `Mcp-Session-Id` reenviado, un `307` en POST se sigue conservando el metodo (o falla citando la URL), y las respuestas llegan tanto en `application/json` como en `text/event-stream` (CA-15)
**Criterios de aceptación**
- [ ] URL local permitida y telemetria configurable; credenciales solo por nombre de variable de entorno.
- [ ] Anadir un proveedor es una funcion nueva en `graphiti_providers.py`, sin tocar `graphiti.py`.
- [ ] Cliente MCP streamable HTTP con stdlib, sin librerias; `health` = `GET /health` + `get_status`; la URL configurada se usa tal cual y el 307 de `/mcp/` -> `/mcp` no rompe el handshake en silencio (CA-15).

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
- **Verificacion**: `python -m pytest -q skills/knowledge-services/scripts/test_backend_graphiti.py -k "verify or rebuild or revoke"` -> desfase detectable via `get_episodes` del `group_id` propio (y aviso si el servidor responde con otro grupo); `--rebuild` reproduce el mismo hash de manifiesto que la sincronizacion incremental y es el UNICO camino que llama a `clear_graph`, acotado al grupo propio; `revoke` deja tombstone como episodio de invalidacion sin llamar a `delete_episode`
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