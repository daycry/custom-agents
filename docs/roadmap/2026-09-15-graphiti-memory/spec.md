---
spec: graphiti-memory
estado: implementada
creado: 2026-09-15
actualizado: 2026-09-23
evaluacion: evaluation.md
design: design.md
plan: improvement-plan.md
---

# Memoria relacional temporal con Graphiti

## Objetivo

Anadir Graphiti como proyeccion relacional y temporal opcional del conocimiento ya aprobado por `knowledge-services`. Markdown/Git permanece canonico; Graphiti solo recibe eventos derivados, conserva `knowledge_id` y permite relacionar evidencia, versiones, sucesiones y contradicciones.

## Dependencia de entrada

No comienza implementacion hasta que `knowledge-services` entregue esquema validado, `docs/knowledge/approved/`, Curator y exportacion Kwipu. Si esa puerta no esta completa, este plan permanece `borrador`.

## Alcance

- Configuracion opt-in de endpoint, grupo logico y telemetria desactivable.
- Adaptador determinista `approved/` -> episodios Graphiti, con idempotencia y procedencia, **filtrado por `routing.graphiti` de `.claude/knowledge-services/taxonomy.json`** (mismo fichero que define categorias y enrutado Kwipu en `knowledge-services`): solo sincroniza las categorias que el proyecto declare `true`.
- Modelo inicial: `Knowledge`, `Evidence`, `Case`, `Constraint`, `Failure`, `Correction` y relaciones `SUPPORTED_BY`, `SUPERSEDES`, `CONTRADICTS`, `MITIGATES`, `APPLIES_TO`.
- Router de lectura que selecciona Graphiti solo para consultas relacionales o temporales y conserva fallback Markdown/Kwipu.
- Salud, desfase, reindexacion explicita y pruebas con backend local.

## Fuera de alcance

- Capturar prompts, conversaciones, TODOs o logs; llamadas de red en hooks; Graphiti como fuente de verdad; escritura directa por agentes; multi-proyecto; sincronizacion cloud; entrenamiento Ollama.

## Criterios de aceptacion

- [ ] CA-01 - Solo entradas `approved` validas crean episodios Graphiti con `knowledge_id`, version y ruta fuente.
- [ ] CA-02 - Repetir sincronizacion no duplica nodos/relaciones ni elimina historial.
- [ ] CA-03 - Las consultas temporales y de relaciones incluyen procedencia y estado vigente/sustituido.
- [ ] CA-04 - Endpoint apagado, modelo local invalido o backend sin datos degradan sin bloquear el ciclo.
- [ ] CA-05 - Los agentes no pueden escribir directamente; solo Curator y sincronizador aprobado.
- [ ] CA-06 - Kwipu conserva preguntas documentales y Graphiti no se consulta por defecto.
- [ ] CA-07 - Una categoria sin `routing.graphiti: true` en `taxonomy.json` nunca genera episodios (fail-closed), y el sincronizador no asume un routing universal para todo `approved/`.
- [ ] CA-08 - Graphiti es un adaptador del contrato de `knowledge-services` (`backends/graphiti.py`): `knowledge-sync.py --backend graphiti` funciona sin que el nucleo mencione Graphiti; el adaptador `test` de knowledge-services y este pasan la misma suite de contrato.
- [ ] CA-09 - El proveedor de LLM/embeddings es configuracion (`backends.graphiti.provider`: `ollama` | `openai` | `anthropic` | `none`, con `model`, `embedder`, `base_url`); ningun modelo ni endpoint esta cableado; con `none` el adaptador solo acepta episodios pre-estructurados.
- [ ] CA-10 - `mode: off | shadow | read`: en `shadow` se sincroniza pero el router NUNCA lee de Graphiti; `read` exige `health` sano y un `verify` sin desfase; el default es `shadow`.
- [ ] CA-11 - `--rebuild` reconstruye el grupo entero desde `approved/` y produce el mismo manifiesto (hash) que la sincronizacion incremental; `revoke <knowledge_id>` deja tombstone/invalidacion sin borrar historial.
- [ ] CA-12 - Las reglas del router son configuracion (`backends.graphiti.router.intents`), el `intent` lo declara quien consulta (`--intent temporal|relacional|evidencia`) y un intent no declarado cae SIEMPRE al camino local/Kwipu; ningun LLM decide el enrutado.
- [ ] CA-13 - (reformulado en la enmienda 2026-09-18) La ontologia nace de `taxonomy.json`, pero los `entity_types` los define el **servidor** Graphiti MCP (`config.yaml`), no el cliente: el adaptador (a) lee los tipos del servidor y mapea cada categoria a uno declarado en `backends.graphiti.entity_map` (default: `Document`), llevando `knowledge_id`, categoria y version en el cuerpo del episodio, y (b) `knowledge-sync.py --backend graphiti --propose-config` genera el bloque `entity_types` sugerido (uno por categoria + `Knowledge`, `Evidence`) para que el usuario lo aplique en su servidor. Relaciones nucleo (`SUPPORTED_BY`, `SUPERSEDES`, `CONTRADICTS`) via `add_triplet`, ampliables en `backends.graphiti.relations`; ninguna lista de dominio vive en el plugin.
- [ ] CA-15 - El cliente es MCP **streamable HTTP** minimo con stdlib (JSON-RPC: `initialize` -> `notifications/initialized` -> `tools/call`), sin librerias: usa la URL exacta configurada (el servidor de referencia responde `307` a `/mcp/` y exige `/mcp`; el cliente sigue un 307 conservando el POST o falla con mensaje que cite la URL), reenvia `Mcp-Session-Id` en cada llamada y acepta `application/json` y `text/event-stream`. `health` = `GET /health` + `tools/call get_status`.
- [ ] CA-14 - Antes de permitir `apply` real con Ollama, un fixture de salida estructurada invalida debe degradar a `dead-letter` via `outbox.py` sin datos corruptos en el grafo.

## Decisiones confirmadas (usuario, 2026-09-15)

1. Graphiti viene despues de la gobernanza Markdown/Kwipu, no en paralelo.
2. Su funcion es memoria relacional/temporal, no captura indiscriminada de agentes.
3. Un proyecto consumidor es un unico limite de aislamiento; el grupo Graphiti evita mezclar instalaciones que compartan Docker.

## Enmienda 2026-09-17 (usuario) — segundo adaptador, proveedor configurable, shadow mode, rebuild y revocacion

Motivo: `ADR-018` fija que los backends se declaran en `taxonomy.json` → `backends` y se implementan como
adaptadores del contrato de `knowledge-services`. Graphiti pasa de «integracion propia» a **segundo adaptador**
(`type: graphiti`), lo que prueba que el contrato es extensible (CA-08). Del paquete externo `docs/feature/`
(CA-MEM-003/004/005) se adoptan solo las ideas con valor y sin servicio nuevo que operar:

1. **Proveedor configurable** de LLM/embeddings (CA-09): el modelo inicial `Knowledge/Evidence/Case/Constraint/
   Failure/Correction` deja de ser una lista fija: nucleo minimo + `entity_type` por categoria (CA-13).
2. **`mode: shadow`** como etapa de rollout por defecto (sincronizar sin leer) antes de `read` (CA-10).
3. **Rebuild reproducible y revocacion** (CA-11): un `approved/` retirado o rechazado se refleja como
   invalidacion en el grafo; el grupo se puede reconstruir entero y verificar por hash.
4. **Router por configuracion + intent declarado** (CA-12), nunca inferido por un modelo.
5. **Cola compartida**: el sincronizador usa `outbox.py` (idempotencia, dead-letter, manifiesto) — CA-14.
6. Descartado explicitamente (ver `ADR-018`): gateway Graphiti como servicio aparte, control plane
   multi-proyecto, router Kwipu+Graphiti como componente independiente.

Dependencias: `knowledge-services` **completado** (incluye T-07 contrato de adaptador y T-13 capabilities) y,
transitivamente, `session-end-durable-capture`. Efecto en coste: +6 h base -> **50 h** con contingencia (antes
44 h), 2,500 EUR, 545k tokens. Ver `evaluation.md` y `tasks.md`.
## Enmienda 2026-09-18 (usuario) — validacion en vivo contra el stack local `knowledge-graphs`

Motivo: se ejecuto el handshake MCP real contra el servidor de referencia (`dockers/knowledge-graphs`,
`graphiti-mcp 1.29.1`, protocolo `2025-03-26`, FalkorDB, `127.0.0.1:8001`). Lo comprobado obliga a precisar
T-02, T-04 y T-06 sin anadir componentes:

1. **Solo MCP.** Graphiti no expone API REST mas alla de `GET /health`; todo va por `/mcp` (streamable HTTP).
   El cliente de T-04 es un cliente MCP minimo con `urllib` (CA-15). Trampa verificada: `/mcp/` con barra
   devuelve `307` a `/mcp` y `urllib` no sigue redirecciones en POST, con lo que el handshake falla en
   silencio; el `initialize` devuelve `Mcp-Session-Id` que hay que reenviar.
2. **Tools disponibles y su uso en el plan**: `add_memory` (`name`, `episode_body`, `group_id`, `source`,
   `source_description`, `uuid`, `reference_time`, `previous_episode_uuids`) para episodios con procedencia
   (CA-01); `add_triplet` para las relaciones nucleo; `search_nodes`/`search_memory_facts` (con
   `valid_at_*`/`invalid_at_*`) para el router en `read` (CA-03, CA-12); `get_episodes` para `verify`;
   `get_status` para `health`. `delete_episode`/`clear_graph` **no** son la primitiva de `revoke`: la revocacion
   es un episodio de invalidacion que conserva historial (CA-11); `clear_graph` solo dentro de `--rebuild` y
   acotado al `group_id` propio.
3. **Los tipos de entidad los fija el servidor** (`config.yaml`: `Document`, `Project`, `Topic`,
   `Organization`, `Person`); `entity_types` en las tools es un filtro de busqueda, no una definicion. CA-13 se
   reformula: mapeo por configuracion + propuesta de bloque `entity_types` para el servidor.
4. **Proveedor del stack de referencia**: Ollama via API compatible OpenAI (`OPENAI_API_URL=…/v1`,
   `structured_output_mode: json_object`, `SEMAPHORE_LIMIT: 1`, ingestion lenta en CPU). Encaja con CA-09
   (`provider: ollama`) y refuerza CA-14 (dead-letter ante JSON invalido) y el default `mode: shadow` (CA-10).
   El `group_id` lo fija el servidor (`knowledge-graphs`) aunque las tools lo acepten por llamada: el
   adaptador pasa siempre el suyo y `verify` avisa si el servidor responde con otro.

Alcance opt-in confirmado: sin `backends.graphiti` en `taxonomy.json` (o con `mode: off`) nada de esto se
ejecuta ni se registra. Estado del servidor de referencia al validar: 0 episodios en `knowledge-graphs`,
coherente con que aun no existe adaptador. Sin efecto en horas: el 307 y el mapeo de tipos entran en T-04 y
T-02. Ver `tasks.md`.
