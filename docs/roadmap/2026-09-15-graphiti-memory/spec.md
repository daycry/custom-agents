---
spec: graphiti-memory
estado: aprobada
creado: 2026-09-15
actualizado: 2026-09-17
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
- [ ] CA-13 - La ontologia nace de `taxonomy.json`: nucleo fijo minimo (`Knowledge`, `Evidence`) + un tipo de entidad por categoria (`entity_type`, default = clave de la categoria) y relaciones nucleo (`SUPPORTED_BY`, `SUPERSEDES`, `CONTRADICTS`) ampliables en `backends.graphiti.relations`; ninguna lista de dominio vive en el plugin.
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