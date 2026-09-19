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
| Fase 1 - Contrato y modelo | 3 | 3 | 100% | 0 / 13h | 1.15 / 3.9h | 0 / 1.0h | ~13.6M / 175k (fix1: cache de contexto largo) |
| Fase 2 - Sincronizacion | 0 | 3 | 0% | 0 / 16h | 0 / 4.8h | 0 / 1.2h | 0 / 200k |
| Fase 3 - Router y configuracion | 0 | 2 | 0% | 0 / 11h | 0 / 3.3h | 0 / 0.9h | 0 / 110k |
| Fase 4 - Regresion y cierre | 0 | 2 | 0% | 0 / 10h | 0 / 3h | 0 / 0.7h | 0 / 60k |
| **TOTAL** | **3** | **10** | **30%** | **0 / 50h** | **1.15 / 15h** | **0 / 3.8h** | **~13.6M / 545k** |

## Fase 1 - Contrato y modelo

### T-01 - Puerta de dependencia, `backends.graphiti` en el esquema y suite de contrato
- **Estado**: completado
- **Dependencias**: `knowledge-services` completado (T-07 contrato de adaptador, T-13 capabilities)
- **Archivos**: `agent-kits/shared/schemas/taxonomy.schema.json`, `agent-kits/shared/knowledge-schema.py`, `agent-kits/shared/test_knowledge_schema.py`, `agent-kits/shared/templates/taxonomy.json`, `skills/knowledge-services/scripts/test_backends_init.py`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `skills/knowledge-services/backends/markdown_export.py` (fix1: sentinela de copia declarada, sin cambio de comportamiento), `agent-kits/shared/copias.json` (fix1: nuevo bloque `hosts_locales`, ADR-016, gap #15), `docs/roadmap/2026-09-15-graphiti-memory/design.md` (enmendado por el orquestador antes de fix1, gaps #1/#9, forma anidada + invariante local/privado)
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
  - **fix1 (revisión de dos lentes, intento 1, gaps #1/#3/#6/#7/#9/#10/#11/#13/#14/#15, 2026-09-19):** config anidada bajo `backends.graphiti.config` con claves desconocidas como error a 4 niveles (`backends.<id>`/`config`/`provider`/`router`/`health`), `group_id` sin default cableado (derivado del slug del proyecto, no vacío con `enabled: true`), `endpoint`/`provider.llm`/`mode` obligatorios con `enabled: true`, `health.url` bajo el mismo guardarraíl de red que `endpoint`, `health.timeout_ms > 0`, `allow_remote` booleano estricto, `relations` sin cadenas vacías, y el mismo criterio de hosts locales que `markdown_export.py` (`host.docker.internal`, `.test`/`.local`/`.internal`), declarado como copia en `copias.json` (gap #9: sin cambio de código, arbitraje mantiene el invariante local/privado del repo; `design.md` ya enmendado por el orquestador).
    - RED (fix1): `python -m pytest -q agent-kits/shared/test_knowledge_schema.py` con la implementación de `58b0ef6` (pre-fix, vía `git stash` de solo `knowledge-schema.py`/`templates/taxonomy.json`) -> `15 failed, 68 passed`
    - GREEN (fix1): `python -m pytest -q agent-kits/shared/test_knowledge_schema.py` -> `83 passed`
- **Changelog**: Los proyectos pueden declarar un backend Graphiti opcional (desactivado por defecto) en su configuración de conocimiento, con validación de endpoint local, proveedor de modelo y reglas de enrutado.
- **Tiempo humano**: est. - · real -
- **Tiempo IA**: real 0.50h (medido; usage-meter, T-01 0.14h + T-01-fix1 0.36h, artefactos `graphiti-memory/T-01` y `graphiti-memory/T-01-fix1`)
**Criterios de aceptación**
- [x] El modelo exige ID, version, evidencia y ruta fuente *(hereda del contrato ya validado por `knowledge-schema.py`/`curator-gate.py` para toda entrada `approved`; sin cambio en T-01)*. El **hash de procedencia** no es del modelo de entrada sino de cada episodio: criterio movido a T-05 (gap #8 de la revisión de la Fase 1, intento 1).
- [x] `provider.llm` acepta `ollama | openai | anthropic | none`; ningun modelo ni endpoint tiene default cableado salvo loopback (CA-09). Cubierto por `test_graphiti_provider_llm_invalido`, `test_graphiti_provider_none_no_exige_modelo`, `test_graphiti_endpoint_no_local_sin_allow_remote_falla`.

### T-02 - Ontologia derivada de `taxonomy.json` y relaciones temporales
- **Estado**: completado
- **Dependencias**: T-01
- **Archivos**: `skills/knowledge-services/backends/graphiti_model.py`, `tests/test_graphiti_model.py`, `tests/test_console_encoding.py`
- **Verificacion**: `python -m pytest -q tests/test_graphiti_model.py` -> cada categoria se mapea a un tipo EFECTIVO segun `backends.graphiti.entity_map`; `--propose-config` emite el bloque `entity_types` con UNA entrada POR CATEGORIA (nombre `entity_map[key]` si existe, si no `TitleCase(key)`, deduplicada por nombre — nunca un generico compartido como `Document`) + `Knowledge`/`Evidence`, en YAML valido y con `name:` siempre escapado; relaciones nucleo + `relations` declaradas; sucesion `SUPERSEDES` valida y con invariantes explicitos. Salida real de `--propose-config` contra `agent-kits/shared/templates/taxonomy.json`:
  ```
  entity_types:
    - name: "Decision"
      description: "Mapeado desde taxonomy.json: DECISION"
    - name: "Gotcha"
      description: "Mapeado desde taxonomy.json: GOTCHA"
    - name: "Lesson"
      description: "Mapeado desde taxonomy.json: LESSON"
    - name: "Pattern"
      description: "Mapeado desde taxonomy.json: PATTERN"
    - name: "Knowledge"
      description: "Nucleo del adaptador graphiti: conocimiento aprobado con procedencia"
    - name: "Evidence"
      description: "Nucleo del adaptador graphiti: evidencia que respalda un Knowledge"
  ```
  - RED: `tests/test_graphiti_model.py` fallaba con `FileNotFoundError` al cargar `skills/knowledge-services/backends/graphiti_model.py` (el modulo no existia) · 2026-09-19
  - GREEN: `python -m pytest -q tests/test_graphiti_model.py` -> `14 passed in 0.12s`
  - `python -m pytest -q tests/test_console_encoding.py` -> `385 passed in 91.10s` (snippet UTF-8 + entradas en `SIN_SIMBOLOS_EN_LA_SALIDA`/`_modos()` para el nuevo modulo, regla 8 de CONVENTIONS)
  - **fix1 (revisión de dos lentes, intento 1, gaps #2/#4/#5/#12, 2026-09-19):** `proponer_entity_types_yaml` reescrito a una entrada por categoría (dedupe por nombre, `TitleCase(key)` sin mapeo, sin lista de dominio) con `name:` escapado igual que `description`; `cadena_supersedes` valida la entrada (tipo, `knowledge_id` no vacío, ids repetidos -> `ValueError` explícito) y garantiza `vigentes ∩ invalidados = ∅` y `origen ≠ destino`; `tipo_entidad` tolera `config` no-dict con `RuntimeWarning` en vez de `AttributeError`; docstring documenta que la vigencia es posicional (orden por `version`, responsabilidad del llamante, T-05).
    - RED (fix1): `python -m pytest -q tests/test_graphiti_model.py` con la implementación de `58b0ef6` (11 tests nuevos contra el código pre-fix) -> `11 failed, 17 passed`
    - GREEN (fix1): `python -m pytest -q tests/test_graphiti_model.py` -> `28 passed`
- **Changelog**: Graphiti ya deriva sus tipos de entidad y relaciones desde la taxonomia del proyecto, sin listas de dominio fijas en el plugin.
- **Tiempo humano**: est. - · real -
- **Tiempo IA**: real 0.47h (medido; usage-meter, T-02 0.33h + T-02-fix1 0.14h, artefactos `graphiti-memory/T-02` y `graphiti-memory/T-02-fix1`)
**Criterios de aceptación**
- [x] `SUPERSEDES` conserva historia y marca vigencia — `cadena_supersedes()` devuelve `relaciones` (todas las `SUPERSEDES` consecutivas, ninguna version se pierde), `vigentes` (solo la ultima) e `invalidados` (las anteriores); `vigentes | invalidados` es siempre el conjunto completo de entrada (`test_cadena_supersedes_conserva_historia_y_marca_vigencia`).
- [x] Ninguna lista de tipos de dominio en el codigo del plugin; los tipos efectivos son los del servidor y el mapeo es configuracion (CA-13 reformulado, enmienda 2026-09-18) — `tipo_entidad`/`tipos_por_categoria` solo leen `config["entity_map"]` (config del proyecto) y, sin mapeo, caen a `Document` (el generico del servidor de referencia) sin declarar ningun tipo de dominio; probado contra dos `taxonomy.json` distintos (`test_tipos_por_categoria_dos_taxonomias_distintas`). **La propuesta de configuración es completa (gap #16, intento 2):** `entity_types` para el servidor + el `entity_map` que los hace efectivos; aplicar el `entity_map` propuesto ⇒ `tipos_por_categoria` == nombres propuestos.

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
- [ ] Cada episodio lleva `knowledge_id`, `version`, `status`, `evidence_level`, `source_path` y el **hash** del contenido aprobado (procedencia verificable; criterio heredado de T-01 por el gap #8 de la revisión de la Fase 1).
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

## Revisión de dos lentes — intento 1: Fase 1 (T-01, T-02, T-03) — 15 gaps (0 Critical, 7 Important, 8 Minor), lentes A+B (C y D no aplican: `review-lens-select.py` sin motivos), rango `58b0ef6..7d67a4c`

Puerta previa: `scope-check.py --base 58b0ef6` → exit 0, 18 ficheros, 0 fuera de alcance. Ambas lentes reprodujeron cifra a cifra las Verificaciones del ledger y los `RED` de T-01 (`11 failed, 4 passed` contra `58b0ef6`) y T-02 (`FileNotFoundError`). Lente B: 12 mutantes, 9 muertos; sobreviven M9 (host local por subcadena), M10 (cualquier IP literal) y M12 (`provider.llm` opcional). Fusión: el hallazgo de la Lente B sobre CA-13 «uno por categoría» coincide con A-2 y se cuenta una vez; B-4 y B-8 se anotan aquí aunque rocen la Lente C (no corrió) porque son defectos del validador, no del diff de red.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | Config anidada bajo `backends.graphiti.config` (decisión correcta: patrón `backends.<id> = {type, enabled, config}`) pero `design.md:17-29` sigue con el ejemplo PLANO y el validador ignora en silencio las claves desconocidas a nivel de `backends.<id>`: la forma del design pasa con `[]` aun con endpoint de tercero y secreto inline (`knowledge-schema.py:173-177,397`). Arbitraje del orquestador: se mantiene la forma anidada; el orquestador enmienda `design.md`; el implementer hace que cualquier clave no reconocida a nivel de `backends.<id>` sea ERROR | T-01 | corregido: `backends.<id>` con claves fuera de `{type, enabled, config}` es error de validacion | `test_graphiti_clave_desconocida_a_nivel_de_backend_falla` -> passed |
| 2 | Important | `proponer_entity_types_yaml` agrupa por tipo EFECTIVO: con la plantilla por defecto salen `Document/Knowledge/Evidence`, no «uno por categoría + Knowledge, Evidence» (CA-13); la Verificación de T-02 afirma «uno por categoria» y el código no lo hace (`graphiti_model.py:99-120`, `tasks.md:55`). Arbitraje: una entrada por categoría (nombre = `entity_map[key]` si existe, si no derivado de la `key` —TitleCase—, sin lista de dominio en código), dedupe por nombre, + `Knowledge` y `Evidence`; Verificación reescrita con la salida real | T-02 | corregido: una entrada por categoria (dedupe por nombre, TitleCase(key) sin mapeo); Verificacion de T-02 reescrita con la salida real | `test_proponer_entity_types_yaml_incluye_nucleo_y_categorias`, `test_proponer_entity_types_yaml_dedupe_por_nombre_explicito` -> passed |
| 3 | Important | `group_id` cableado `"knowledge-graphs"` (el grupo del stack de referencia) en `templates/taxonomy.json:41` y `knowledge-schema.py:132`, contra `design.md:11` y la decisión 3 de la spec: dos consumidores en la misma máquina mezclan conocimiento. Arbitraje: sin default cableado — si falta, se deriva del slug del directorio del proyecto (mismo criterio que `id_prefix`), y con `enabled: true` debe quedar como cadena no vacía | T-01 | corregido: `group_id` sin default cableado, derivado del slug del proyecto (mismo criterio que `id_prefix`); no vacio con `enabled: true` | `test_group_id_se_deriva_del_slug_del_proyecto` -> passed |
| 4 | Important | `proponer_entity_types_yaml` emite `name:` SIN comillas (`graphiti_model.py:115`) mientras `description` sí pasa por `_yaml_cadena`: `"Doc: interno"` → `ScannerError`; `"Doc\n  - name: Injected…"` inyecta una entrada; `"yes"` → booleano; `""` → `None` | T-02 | corregido: `name:` escapado con `_yaml_cadena`, igual que `description` | `test_proponer_entity_types_yaml_escapa_nombres_hostiles`, `test_proponer_entity_types_yaml_nombres_hostiles_son_yaml_valido` -> passed |
| 5 | Important | `cadena_supersedes` deriva la vigencia solo de la posición: `[A, B, A]` → `A` vigente E invalidada a la vez; `[A, A, B]` → relación `SUPERSEDES A→A` (auto-sucesión que T-04 convertiría en un `add_triplet` sobre sí mismo) (`graphiti_model.py:132-142`). Arbitraje: ids repetidos → error explícito; invariante `vigentes ∩ invalidados = ∅` y `origen ≠ destino`, con test | T-02 | corregido: `knowledge_id` repetido -> `ValueError` explicito; `vigentes ∩ invalidados = ∅` y `origen ≠ destino` garantizados por construccion | `test_cadena_supersedes_ids_repetidos_lanza_valueerror`, `test_cadena_supersedes_vigentes_e_invalidados_son_disjuntos`, `test_cadena_supersedes_ninguna_relacion_es_auto_sucesion` -> passed |
| 6 | Important | `_validar_backend_graphiti` solo valida claves PRESENTES: `{"type":"graphiti","enabled":true}` sin `config`, o `config` sin `endpoint`/`provider`/`mode` → `[]` en 5 casos; `knowledge-sync.py:312` entregaría `cfg = {}` al adaptador (`knowledge-schema.py:177-180`). Arbitraje: con `enabled: true`, `endpoint`, `provider.llm` y `mode` obligatorios | T-01 | corregido: con `enabled: true`, `endpoint`, `provider.llm` y `mode` obligatorios aunque `config` falte o sea invalido | `test_graphiti_habilitado_sin_config_falla_en_endpoint_provider_y_mode` -> passed |
| 7 | Important | `health.url` solo se valida como cadena (`knowledge-schema.py:263-269`): `http://evil.com/health` con `allow_remote: false` → aceptado; el precedente del repo (`markdown_export.py:960`) pasa la URL de health por `_host_permitido` | T-01 | corregido: `health.url` bajo el mismo guardarraíl de red que `endpoint` | `test_graphiti_health_url_remota_publica_sin_allow_remote_falla` -> passed |
| 8 | Minor | Criterio `[x]` de T-01 «el modelo exige … hash» no lo exige ni lo prueba nada (`grep hash knowledge-schema.py` → vacío; `curator-gate.py:303-309` exige `fuentes`). Arbitraje: el hash es del episodio (T-05): el orquestador reescribe el criterio de T-01 y añade «hash de procedencia por episodio» a los criterios de T-05 | T-01/T-05 | corregido por el orquestador en `2ffc69f`: criterio de T-01 reescrito y «hash de procedencia por episodio» añadido a T-05 | Lente A |
| 9 | Minor | `_endpoint_es_local` admite cualquier IP PRIVADA sin `allow_remote` (`knowledge-schema.py:60-77`); `design.md:13` y el criterio de T-01 dicen «loopback». Arbitraje: se mantiene el invariante del repo (local/privado, `lib-guardrail.sh`); el orquestador enmienda `design.md` y el criterio | T-01 | corregido: sin cambio de codigo (arbitraje mantiene el invariante local/privado del repo); `design.md` enmendado por el orquestador, doc de CONVENTIONS.md consistente | `test_graphiti_config_valida_no_da_error` (config con endpoint loopback por defecto) -> passed; sin test nuevo (gap doc-only, sin cambio de codigo) |
| 10 | Minor | Clave `telemetria` (design decía `telemetry`) ausente de la fila de `taxonomy.json` en `docs/CONVENTIONS.md`/`docs/en/CONVENTIONS.md` (tampoco `health`); `telemetry` se acepta en silencio dentro de `config`. Arbitraje: se mantiene `telemetria` (vocabulario ES de `dev.json`), se documenta en la fila EN/ES y las claves desconocidas de `config` pasan a error (ver #14) | T-01 | corregido: `telemetria` y `health` documentados en la fila de `taxonomy.json` de `docs/CONVENTIONS.md`/`docs/en/CONVENTIONS.md`; claves desconocidas de `config` -> error (ver #14) | Lectura manual de la fila actualizada + `test_graphiti_clave_desconocida_en_config_falla` -> passed |
| 11 | Minor | `health.timeout_ms` acepta `-5` y `0` (`knowledge-schema.py:270-274`): `socket.settimeout(-5)` lanza y `0` deja el socket no bloqueante. Exigir `> 0` | T-01 | corregido: `health.timeout_ms` debe ser `> 0` | `test_graphiti_health_timeout_ms_negativo_o_cero_falla` -> passed |
| 12 | Minor | `cadena_supersedes` no valida la entrada (`[{"id": "B"}]` → `KeyError`; `None` → `TypeError`; dict en vez de lista → `TypeError`) y `tipo_entidad("adr", ["entity_map"])` → `AttributeError`; el orden ascendente se confía al llamante (orden lexicográfico `v1 < v10 < v2` marca vigente la v2 en silencio). Arbitraje: entrada validada con error explícito; documentar en el docstring que la vigencia es posicional y que el llamante ordena por `version` (T-05 lo hará) | T-02 | corregido: `cadena_supersedes` valida tipo/forma con `TypeError`/`ValueError` explicitos; `tipo_entidad` tolera `config` no-dict con `RuntimeWarning`; docstring documenta vigencia posicional | `test_cadena_supersedes_elemento_sin_knowledge_id_lanza_valueerror`, `test_cadena_supersedes_no_lista_lanza_typeerror`, `test_tipo_entidad_config_no_dict_cae_al_default_con_warning` -> passed |
| 13 | Minor | La suite de T-01 no discrimina el guardarraíl de endpoint ni `provider` sin `llm` (`test_knowledge_schema.py:160-175`, solo `ejemplo-remoto.com`): sobreviven M9 (`"localhost" in host`), M10 (cualquier IP literal) y M12 (`provider.llm` opcional). Añadir `http://localhost.evil.com`, IP pública literal (`8.8.8.8`), `provider: {}` | T-01 | corregido: mutantes M9/M10/M12 muertos con casos nuevos (`localhost.evil.com`, IP publica literal, `provider: {}`) | `test_graphiti_endpoint_host_local_por_subcadena_falla_m9`, `test_graphiti_endpoint_ip_publica_literal_falla_m10`, `test_graphiti_provider_vacio_falla_m12` -> passed |
| 14 | Minor | Ninguna clave desconocida de `config`/`router` se rechaza y `allow_remote` se lee por truthiness (`knowledge-schema.py:177-276`): `api_key: "sk-…"` literal, `router.modelo: "gpt-4"` (CA-12), `relations: [""]`, `allow_remote: "no"` → aceptados. Arbitraje: claves no reconocidas en `backends.<id>`, `config`, `provider`, `router` y `health` → error; `allow_remote` solo booleano; `relations` sin cadenas vacías | T-01 | corregido: claves no reconocidas en `config`/`provider`/`router`/`health` -> error; `allow_remote` booleano estricto; `relations` sin cadenas vacias | `test_graphiti_allow_remote_string_no_autoriza_endpoint_remoto`, `test_graphiti_relations_con_cadena_vacia_falla`, `test_graphiti_clave_desconocida_en_config_falla`, `test_graphiti_clave_desconocida_en_provider_falla`, `test_graphiti_clave_desconocida_en_router_falla`, `test_graphiti_clave_desconocida_en_health_falla` -> passed |
| 15 | Minor | `_endpoint_es_local` solo admite `localhost` e IPs literales; `markdown_export.py:286` ya tiene `_HOSTS_LOCALES_LITERALES` + `_SUFIJOS_LOCALES` (`host.docker.internal`, `*.test`, …): el usuario dockerizado se ve empujado a `allow_remote: true`, que apaga el chequeo entero. Arbitraje: mismo criterio de hosts locales que el adaptador existente, con la copia DECLARADA en `agent-kits/shared/copias.json` (ADR-016) o importada de un helper compartido | T-01 | corregido: mismo criterio de hosts locales que `markdown_export.py` (`_HOSTS_LOCALES_LITERALES`/`_SUFIJOS_LOCALES`), copia DECLARADA en `agent-kits/shared/copias.json` (bloque `hosts_locales`, ADR-016) | `test_graphiti_host_local_con_sufijo_docker_es_valido` -> passed; `python -m pytest -q tests/test_copias_declaradas.py` -> passed |

Fuera de la ronda (anotado): la Lente C revisará, cuando exista `graphiti.py` (T-04), que el `_host_permitido` en runtime resuelva DNS y que `tipo_entidad` no propague un tipo inexistente en el servidor (typo `Documnet`) hasta la llamada MCP.

## Revisión de dos lentes — intento 2: Fase 1 (T-01, T-02, T-03) — 15/15 gaps del intento 1 cerrados (#11 y #12 parciales, reabsorbidos en #21 y #22); 11 gaps NUEVOS (0 Critical, 3 Important, 8 Minor), lentes A+B (C y D no aplican), rango `2ffc69f..3bb4bdb`

Puertas: `lint_plugin` 0 errores · `evals/check` 0 errores · `export-interop --check` al día · `test_copias_declaradas` 22 passed · `test_knowledge_schema` + `test_graphiti_model` 111 passed · `skills/knowledge-services/scripts/` 96 passed. Ambas lentes reprodujeron los 15 probes del intento 1 y el `RED (fix1)` de T-01 (`15 failed, 68 passed`); el de T-02 no reproduce (#25). `validar()` sobre la plantilla, el respaldo embebido y la copia del template → `[]` (la validación estricta no rompe `markdown-export`). Lente B: 18 mutantes, 14 muertos, 1 equivalente (M12), 3 huecos reales (M14, M15, M16 → #17 y #20). Fusión: A2-1 y B2-2 son el mismo defecto (#16); la contradicción entre el criterio y la Verificación de T-02 que anota la Lente B es su origen documental y se corrige dentro de #16.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 16 | Important | La PROPUESTA y el tipo EFECTIVO ya no coinciden: `proponer_entity_types_yaml` propone `Decision/Gotcha/Lesson/Pattern` (TitleCase de la `key`) mientras `tipo_entidad`/`tipos_por_categoria` etiquetan todo como `Document` si no hay `entity_map` (`graphiti_model.py:77` vs `:147`); el usuario crea 4 tipos en su `config.yaml` que ningún episodio usará; `design.md:44-45` sigue diciendo «default la clave» y el criterio `[x]` de T-02 («caen a `Document`») contradice la Verificación de la misma tarea («nunca un genérico como `Document`»). **Arbitraje:** el default efectivo sigue siendo `Document` (tipo genérico del servidor; sin lista de dominio en código) y la propuesta pasa a ser COMPLETA: `proponer_entity_types_yaml` (o una función hermana `proponer_config`) emite el bloque `entity_types` para el servidor **y** el bloque `entity_map` para `taxonomy.json` que los hace efectivos, con la nota «sin `entity_map`, todos los episodios viajan como `Document`»; test: aplicar el `entity_map` propuesto ⇒ `tipos_por_categoria` == nombres propuestos. El orquestador reescribe el criterio de T-02 y `design.md:44-45` | T-02 | pendiente | Lentes A y B, probe con `templates/taxonomy.json` |
| 17 | Important | `_con_group_id_por_defecto` busca el backend por la clave literal `"graphiti"` mientras la validación se dispara por `type == "graphiti"`, y `group_id` no es obligatorio con `enabled: true`: `backends["mi-grafo"] = {type: graphiti, enabled: true, config: {…}}` → `group_id = None` y `validar` = `[]`; T-04 caería al grupo por defecto del cliente (justo lo que #3 quería impedir) (`knowledge-schema.py:437` vs `:508`, `:344-360`). Derivar por `type`; con `enabled: true` exigir cadena no vacía tras la derivación; tests que maten M14 y M16 | T-01 | pendiente | Lente B, mutantes M14/M16 sobreviven |
| 18 | Important | `_titlecase_clave` parte por `[^0-9A-Za-z]+`: una taxonomía válida con `key: "decisión"` o `"日本"` produce `name: ""`/`"DecisiN"` y varias `keys` sin alfanuméricos ASCII colapsan en UNA entrada (`graphiti_model.py:119`). Normalización Unicode (`[^\W_]+` con `re.UNICODE`, NFKC) y, si el nombre derivado queda vacío o colisiona, error explícito «declara `entity_map` para <key>» en vez de una entrada vacía | T-02 | pendiente | Lente B, probe |
| 19 | Minor | La lista cerrada de claves de `config` deja fuera `timeout_ms` y `concurrency` del ejemplo de la enmienda 2026-09-17 y ahora son ERROR; `design.md:47` sigue diciendo «el cliente usa timeout» y T-04 (cliente MCP) no tiene clave para el timeout/concurrencia de las llamadas (solo `health.timeout_ms`). Añadir `timeout_ms` (entero finito > 0, default en la plantilla) y `concurrency` (entero ≥ 1, default 1, coherente con `SEMAPHORE_LIMIT: 1` del stack) al esquema, plantilla, respaldo embebido, fila EN/ES de CONVENTIONS y a la enmienda del design | T-01 | pendiente | Lente A, probe `config.timeout_ms: 3000` → error |
| 20 | Minor | `entity_map` acepta valores `""`/`"  "`/no-str (`knowledge-schema.py:279-283`): el YAML emite `name: ""` o OMITE la categoría en silencio y `tipo_entidad` devuelve `None`/`123` como tipo. Exigir cadenas no vacías (como `relations`); test que mate M15 | T-01/T-02 | pendiente | Lente B, mutante M15 sobrevive |
| 21 | Minor | `health.timeout_ms` acepta `NaN`, `Infinity` y `1e-09` (`knowledge-schema.py:345`): `socket.settimeout(nan)` lanza e `inf` bloquea. Exigir finito (`math.isfinite`) y > 0; aplicar lo mismo a `timeout_ms`/`concurrency` de #19 (cierra el parcial de #11) | T-01 | pendiente | Lente B, probe |
| 22 | Minor | El endurecimiento de entrada de #12 no llegó a `proponer_entity_types_yaml`: `config` lista → `AttributeError`; `key` int → `TypeError`; `key` lista → `unhashable` (`graphiti_model.py:137,147`); alcanzable porque `cargar_taxonomia` devuelve el config aunque tenga errores. Misma tolerancia que `tipo_entidad` (aviso + degradación o `ValueError` con mensaje) (cierra el parcial de #12) | T-02 | pendiente | Lente B, probe |
| 23 | Minor | `group_id` derivado cae al literal compartido `"ca"` cuando el directorio no aporta alfanuméricos ASCII (`/tmp/日本`, `/tmp/áéí`, `C:\`) (`knowledge-schema.py:444`): dos instalaciones con nombre no-ASCII comparten grupo. Slug Unicode (NFKC + `[^\W_]`) y, si sigue vacío, con `enabled: true` → error «declara `group_id`» en lugar de `"ca"` | T-01 | pendiente | Lente B, probe |
| 24 | Minor | La fila del gap #8 seguía `pendiente` aunque su arbitraje estaba hecho en `2ffc69f` | T-01/T-05 | corregido por el orquestador en esta sección (fila #8 actualizada) | Lente A |
| 25 | Minor | Dos evidencias de T-02 no reproducen: la Verificación cita `--propose-config` (no existe CLI en `graphiti_model.py`; llega en T-04/T-05) y el `RED (fix1)` dice `11 failed, 17 passed` cuando la reproducción da `13 failed, 15 passed` (`tasks.md:58,78`). Reescribir la Verificación con un comando ejecutable hoy (`python -c` sobre `proponer_entity_types_yaml`) y la cifra real del RED | T-02 | pendiente | Lente A, reproducción contra `2ffc69f` |
| 26 | Minor | El docstring de cabecera de `tests/test_graphiti_model.py:5-7` describe el contrato derogado («uno por tipo efectivo») | T-02 | pendiente | Lente A |

Fuera de la ronda (anotado para la Lente C de T-04): `_endpoint_es_local("http://169.254.169.254")` → `True` (link-local, endpoint de metadatos de nube; hereda el criterio de `markdown_export.py`) y la validación en frío no resuelve DNS (`graphiti.test` → IP pública valida `[]`): el `_host_permitido` en runtime de T-04 debe resolver y re-comprobar.

**Decisión del orquestador:** 3 Important sin Critical y un bucle convergente (15 → 11, sin regresiones en los cerrados) → ronda `fix2` sobre los 11 y **intento 3 (último)** con verificación dirigida de las lentes.
