---
id: ADR-018
titulo: "Arquitectura de la memoria del plugin: Markdown canónico, backends declarados por adaptador e ingestión durable por cola compartida"
estado: propuesta          # propuesta | aceptada | obsoleta
fecha: 2026-09-17
iniciativa: knowledge-services · graphiti-memory · session-end-durable-capture
---

# ADR-018: Arquitectura de la memoria — Markdown canónico, backends declarados por adaptador e ingestión durable

## Contexto

Cinco iniciativas tocan la misma área (`memory-retrieval` implementada; `knowledge-services`,
`graphiti-memory`, `training-data-services`, `dev-cycle-dataset` planificadas; `session-end-durable-capture`
nueva) y un paquete externo (`docs/feature/`, 2026-09-16) proponía además un «control plane» con
`projects.yaml`, `project_id`/`tenant`/`group_id`, un gateway de servicio para Graphiti y un router
Kwipu+Graphiti. Cada plan traía sus propios principios y nombres de backend **fijos** (`kwipu`,
`graphiti`) en el esquema. Hacía falta una decisión única que fijara qué es fuente de verdad, cómo se
añade un backend nuevo y cómo viaja el conocimiento entre piezas, para que el plugin sea la base de
proyectos con dominios distintos sin tocar código por cada uno.

## Decisión

1. **Fuente de verdad**: Markdown en git (`docs/knowledge/`, `tasks.md`, documentos aprobados). Kwipu,
   Graphiti, el índice FTS5 y cualquier dataset son **índices o proyecciones reconstruibles** desde la fuente;
   nunca autoridad.
2. **Límite de aislamiento = proyecto consumidor**. No hay `project_id`, tenant ni `projects.yaml`: el
   directorio del proyecto y su `.claude/` son la frontera. Un `group_id` estable por instalación evita mezclar
   instalaciones que compartan un mismo backend, y se fija en configuración, nunca desde el prompt.
3. **Backends declarados, no cableados**: `.claude/knowledge-services/taxonomy.json` declara en `backends` cada
   destino con `id`, `type` y su configuración; `routing` por categoría solo puede referirse a ids declarados.
   Un id desconocido o una categoría sin `routing` es **fail-closed**. Añadir un backend es añadir un adaptador
   que cumpla el contrato (`health · plan · apply · verify · rebuild · revoke`) y una entrada en `backends`;
   el validador, el Curator y el exportador **no cambian**. Kwipu (`type: markdown-export`) es el primer
   adaptador; Graphiti el segundo, y es la prueba de que el contrato es extensible.
4. **Ingestión durable por cola compartida**: `agent-kits/shared/outbox.py` es la única implementación de
   escritura atómica, claim, idempotencia por clave, manifiesto con hash y dead-letter. La usan el journal
   (`SessionEnd`), el exportador Kwipu y el sincronizador Graphiti. Cualquier trabajo durable tiene estados
   observables en `/doctor` y replay.
5. **Hooks sin trabajo pesado**: ningún hook ejecuta git costoso, IA, red ni backends de memoria; capturan y
   salen. La materialización ocurre después, con presupuesto, o a demanda.
6. **Escritura por política, no por inferencia**: solo `knowledge-curator` promociona conocimiento; ningún
   agente escribe directamente en un backend. Todo resultado recuperado conserva `knowledge_id`, versión,
   estado (vigente/sustituido), evidencia y ruta canónica.
7. **Degradación**: sin backend, sin modelo local o sin configuración, el ciclo completo funciona igual. Las
   capacidades opcionales se registran en un **registro de capacidades** (`agent-kits/shared/capabilities.py`:
   id, ruta de configuración, `enabled`, `health`, sección de doctor) que `/setup` y `/doctor` recorren, en vez
   de añadir una sección a mano por cada capacidad.
8. **Contratos versionados**: `taxonomy.json` (`version`), envelopes y manifiestos (`schema_version`) aceptan N
   y N-1 durante una versión del plugin; los cambios de contrato se registran como ADR.

## Alternativas descartadas

- **Control plane multi-proyecto** (`projects.yaml`, `project_id`, tenant, resolver de scope — CA-MEM-001 del
  paquete externo): resuelve un problema que el plugin no tiene (una instalación por proyecto) y añade una
  autoridad nueva que compite con `.claude/` y git.
- **Gateway Graphiti como servicio** (CA-MEM-003): un proceso más que operar, con credenciales y red, para
  aislar algo que ya aísla el `group_id` y el adaptador con allow-list de loopback. Se conserva la idea útil:
  **shadow mode** (sincronizar sin leer) como etapa de rollout dentro del adaptador.
- **Nombres de backend fijos en el esquema** (`routing: {kwipu, graphiti}`): cada backend nuevo obligaría a
  tocar validador, exportador y doc; contradice «el plugin es base de muchos proyectos».
- **Escritura directa desde agentes o captura de cada turno**: ruido, privacidad e inyección; ya descartado en
  `graphiti-memory` O2.

## Consecuencias

- `knowledge-services` incorpora `backends` + contrato de adaptador + registro de capacidades (enmienda
  2026-09-17); `graphiti-memory` se replantea como segundo adaptador con proveedor configurable, shadow mode,
  rebuild y revocación; `session-end-durable-capture` entrega `outbox.py` antes de la Fase 3 de
  `knowledge-services`.
- Los principios del paquete externo `README-memory-roadmap.md` quedan absorbidos aquí; el paquete no se
  incorpora al roadmap como iniciativas.
