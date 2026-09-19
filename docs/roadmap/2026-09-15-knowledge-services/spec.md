---
spec: knowledge-services
estado: implementada
creado: 2026-09-15
actualizado: 2026-09-19
evaluacion: evaluation.md
design: design.md
plan: improvement-plan.md
generacion: {fuente: estimado, tokens_reales: {entrada: 0, salida: 0, cache_creacion: 0, cache_lectura: 0}, eur: null, horas_ia: 0.0, duracion: 0m, ratio_usado: 0}
---

# Servicios de conocimiento locales para Kwipu

> [Evaluacion](evaluation.md) · [Diseno](design.md) · [Plan](improvement-plan.md)

## Objetivo

Mantener `docs/knowledge/` como fuente de verdad versionada y anadir un Knowledge Gate local que exporte solo conocimiento aprobado a Kwipu. El plugin es la base de MUCHOS proyectos distintos (no solo de si mismo): la taxonomia de categorias y el enrutado de destino son **configuracion del proyecto consumidor**, nunca una lista fija del plugin. Kwipu sera un recuperador documental opcional; indices y exports son reconstruibles y nunca sustituyen Markdown/Git.

## Alcance

- Candidatos y aprobados bajo `docs/knowledge/`, con categorias **definidas por proyecto** en `.claude/knowledge-services/taxonomy.json` (clave, carpeta, evidencia minima requerida); sin ese fichero, el plugin usa un default minimo propio (`DECISION`, `PATTERN`, `GOTCHA`, `LESSON`, alineado con `adr/`/`gotchas/`/`lessons/` ya existentes) para no romper su propio dogfooding.
- Frontmatter validado: ID estable (prefijo configurable por proyecto), version, estado, evidencia, fuentes, relaciones y tags `clave:valor` normalizados.
- **Lista negra por defecto** (nunca memoria activa, ampliable por proyecto): chain-of-thought, conversacion cruda, TODOs, planes/progreso, logs completos, salidas enormes, codigo duplicado, errores triviales, intentos sin aprendizaje, hipotesis presentadas como hechos, opiniones, redundancias.
- **Escalera de evidencia por defecto** (`observation -> single_case -> validated_case -> multiple_validated_cases -> human_confirmed_rule`), aplicada por cualquier proyecto salvo que declare la suya.
- **Utility scoring opcional** (`taxonomy.json` -> `"utility_scoring": true`): si se activa, el candidato lleva un desglose 0-10 que SOLO ordena la cola de revision; nunca decide `approved`/`rejected` por si mismo. Apagado por defecto.
- **Destination Router configurable**: `.claude/knowledge-services/taxonomy.json` declara, por categoria, si exporta a Kwipu (`true`/`false`/`"summary"`) y si sincroniza a Graphiti (`true`/`false`) cuando esa iniciativa este activa. Sin declaracion explicita, una categoria nueva NO exporta a ningun sitio hasta que el proyecto lo decida (fail-closed).
- Agente `knowledge-curator`, unico dueno de candidatos/aprobados; `documenter` detecta y propone, nunca aprueba ni exporta.
- Exportador determinista a `.claude/knowledge-services/kwipu-export/`, con manifiesto y hashes.
- Opt-in Kwipu en `/setup`, salud/desfase en `/doctor`, y Fase 4-bis despues de QA verde y `documenter`.

## Fuera de alcance

- Graphiti, MCP registration, escritura de memoria conversacional, red desde hooks, migracion masiva y entrenamiento/Ollama.
- Convivencia con un dataset de entrenamiento propio de proyecto (tipo `training_data/`): se abordara en una iniciativa aparte.

## Criterios de aceptacion

- [ ] CA-01 - El esquema valida categorias/evidencia contra `taxonomy.json` del proyecto (o el default del plugin si no existe) y rechaza estados, IDs, tags y referencias invalidas.
- [ ] CA-02 - Candidatos, rechazados, journal, logs y derivados nunca se exportan a Kwipu.
- [ ] CA-03 - Solo el Curator puede aprobar, rechazar, pedir cambios o sustituir conocimiento.
- [ ] CA-04 - El export es idempotente, atomico y reconstruible desde `approved/`.
- [ ] CA-05 - Setup y doctor gestionan Kwipu como capacidad opcional y degradable.
- [ ] CA-06 - La curacion sucede solo despues de QA/documentacion y no altera cierres sin candidatos.
- [ ] CA-07 - Interop, contratos y documentacion ES/EN permanecen sincronizados.
- [ ] CA-08 - Esta entrega no implementa Graphiti.
- [ ] CA-09 - Una categoria sin enrutado declarado en `taxonomy.json` no exporta a ningun backend (fail-closed), y el plugin sigue funcionando con su taxonomia default si el proyecto no configura nada.
- [ ] CA-10 - Con `utility_scoring` activo, el score nunca decide un estado por si solo: un test mutante que fuerce `utility=10` sobre un candidato sin evidencia sigue en `pending`/`rejected`.
- [ ] CA-11 - `routing` solo puede citar ids declarados en `taxonomy.json` -> `backends`; un id no declarado es error de validacion y la categoria no exporta a ningun sitio (fail-closed).
- [ ] CA-12 - El contrato de adaptador es extensible sin tocar el nucleo: un adaptador de prueba (`type: "test"`) registrado solo en la fixture recibe exactamente las entradas que le enruta `taxonomy.json`, sin modificar validador, Curator ni `knowledge-sync.py`.
- [ ] CA-13 - `taxonomy.json` se valida contra `agent-kits/shared/schemas/taxonomy.schema.json` (version, categorias, backends, routing, evidence_levels, denylist) con validador stdlib; `/doctor` senala fichero, campo y arreglo.
- [ ] CA-14 - `/setup` y `/doctor` enumeran las capacidades opcionales desde `capabilities.py` (kwipu hoy; graphiti, training despues) sin codigo especifico por capacidad en `doctor.py`.
- [ ] CA-15 - El exportador usa `agent-kits/shared/outbox.py` (de `session-end-durable-capture`) para staging atomico, manifiesto y dead-letter; no reimplementa la cola.
- [ ] CA-16 - El adaptador `markdown-export` escribe en el directorio que declare `backends.kwipu.config.export_dir` (en el stack de referencia, `kwipu-data/generated/projects/<id>/`, la clase «Generated Knowledge» de `projects.yaml`); el **reindexado** de Kwipu (`build_view` + reinicio de `kwipu`/`kwipu-bridge`/`kwipu-mcp`) es del stack, no del plugin: `verify` detecta el desfase comparando el manifiesto del export con `GET /health` y `GET /graph/snapshot` y **nombra** el remedio sin ejecutarlo.
- [ ] CA-17 - El frontmatter de cada fichero exportado lleva los campos del Knowledge Gate del stack (`project`, `scope`, `category`, `source`, `confidence`) ademas de `knowledge_id`, `version` y `hash`, con valores derivados de la entrada aprobada y de `taxonomy.json`; ningun campo se inventa.

## Decisiones confirmadas (usuario, 2026-09-15/16)

1. El proyecto consumidor ya es el limite de aislamiento: no hay `projects/<project_id>/`.
2. Kwipu consulta conocimiento aprobado; Graphiti queda para una iniciativa posterior.
3. El Curator es un agente especializado posterior a QA y `documenter`.
4. Taxonomia y enrutado de destino son configuracion por proyecto (`.claude/knowledge-services/taxonomy.json`), no una lista fija del plugin — el plugin es base de multiples proyectos con dominios distintos.
5. El utility scoring es opt-in, apagado por defecto, y nunca decide un estado por si mismo.
6. La convivencia con un dataset de entrenamiento propio de proyecto se trata en otra iniciativa; no forma parte de esta entrega.

## Enmienda 2026-09-17 (usuario) — backends declarados, contrato de adaptador y registro de capacidades

Motivo: al revisar los planes de memoria junto al paquete externo `docs/feature/` se detecto que `routing`
cableaba dos nombres de backend (`kwipu`, `graphiti`) en el esquema. Para que el plugin sea **parametrizable y
extensible** (base de proyectos con dominios y backends distintos) se decide, y queda recogido en `ADR-018`:

1. **`backends` en `taxonomy.json`**: cada destino se declara con `id`, `type` y su configuracion; `routing` por
   categoria solo puede citar ids declarados (CA-11). Sin `backends`, el default del plugin declara solo
   `kwipu` (`type: markdown-export`) desactivado.
2. **Contrato de adaptador** en `skills/knowledge-services/backends/<type>.py`: `health(cfg)`, `plan(entries, cfg)`,
   `apply(ops, cfg)`, `verify(cfg)`, `rebuild(cfg)`, `revoke(knowledge_id, cfg)`. `knowledge-sync.py --backend <id>
   [--dry-run|--check|--rebuild]` es el unico punto de entrada; Kwipu es el primer adaptador (CA-12). El
   exportador `kwipu-export.py` previsto pasa a ser ese adaptador.
3. **Esquema versionado** `taxonomy.schema.json` + validador stdlib (sin dependencias, mismo criterio que
   ADR-013) usado por el validador del indice, `/doctor` y `/setup` (CA-13). `evidence_levels` y `denylist`
   pasan a ser claves opcionales del mismo fichero (ya eran configurables por diseno; ahora tienen esquema).
4. **Registro de capacidades** `agent-kits/shared/capabilities.py` (id, ruta de config, `enabled`, `health`,
   seccion de doctor, paso de setup) que recorren `/setup` y `/doctor`; esta iniciativa registra `kwipu` y el
   propio Knowledge Gate (CA-14). `graphiti-memory` y `training-data-services` se registran despues sin tocar
   `doctor.py`.
5. **Cola compartida**: el staging atomico, el manifiesto y el dead-letter del exportador salen de
   `agent-kits/shared/outbox.py`, que entrega `session-end-durable-capture` (CA-15). Dependencia nueva: la Fase 3
   de esta iniciativa arranca cuando esa iniciativa este `completado`.

Efecto en alcance/coste: +8 h base (esquema y validador +1, contrato de adaptador +1, Kwipu como adaptador +2,
capabilities +3, doctor/setup sobre capabilities +1); **48 h -> 56 h** con contingencia, 2.400 -> 2.800 EUR,
715k -> 815k tokens. Ver `evaluation.md` y `tasks.md` (T-13 nueva).

## Enmienda 2026-09-18 (usuario) — validacion en vivo contra el stack local `knowledge-graphs`

Motivo: se comprobo el contrato real de Kwipu contra el despliegue de referencia (`dockers/knowledge-graphs`,
bridge en `127.0.0.1:8765`, todos los contenedores `Up`). Las premisas del plan se sostienen (backend opt-in por
proyecto via `taxonomy.json`, fail-closed, sin red desde hooks) y se precisan tres puntos, sin nuevos componentes:

1. **Kwipu no tiene API de ingesta.** Indexa una vista de solo lectura que `source_manager/build_view.py`
   construye desde la allowlist `kwipu/config/projects.yaml`; hay que reiniciar `kwipu`, `kwipu-bridge` y
   `kwipu-mcp` para que la relean. El adaptador `markdown-export` (T-08) solo escribe el export; el destino es
   la clase «Generated Knowledge» del stack (`generated_knowledge.path`, hoy `enabled: false`, lo activa el
   usuario). El reindexado queda **fuera del plugin** y `verify` lo detecta como desfase (CA-16).
2. **Contrato de lectura verificado**: `GET /health` (`status: ok|degraded`, `llm_model`, `embed_model`,
   `property_graph.{present,valid,node_count,relation_count}`, `ollama.{reachable,models[]}`), `POST /query {q}`
   -> `answer`, `citations[{node_id,file_name,score}]`, `cited_files`, y `GET /graph/snapshot` (nodos con
   `file_path` y enlaces de procedencia `DEFINES`). `health` del adaptador lee ese JSON tal cual; el router de
   `knowledge-find.py` puede usar `/query`. El bridge responde 503 si cambia el embedder del indice: `health`
   debe reportar `embed_model` para que `/doctor` lo muestre.
3. **Frontmatter alineado con el Knowledge Gate del stack** (`docs/futuro/knowledge-gate.md`): `project`,
   `scope`, `category`, `source`, `confidence` (CA-17), para que el export del plugin y el gate del stack sean la
   misma cosa y no dos formatos.

Alcance opt-in confirmado: un proyecto sin `backends.kwipu.enabled: true` no ejecuta nada de esto; la
comprobacion en vivo cubre el caso «habilitado y sano», el caso «deshabilitado» lo cubren los tests de
`capabilities.py` (T-13). Sin efecto en horas: precisa T-08 y T-09 dentro de su estimacion. Ver `tasks.md`.

> **Nota 2026-09-18 (revisión de la Fase 2, gap 41).** El término de la lista negra por defecto `TODOs` pasa a ser el marcador `TODO:` (con dos puntos, como en `code-health`), y la lista negra se evalúa sobre el cuerpo del candidato con plegado de acentos (NFD), frontera de palabra asimétrica (no se exige tras un término que acaba en puntuación, p. ej. `TODO:`) y espacio≡guion en términos multi-palabra (gaps 41/64/65/66 de la Fase 2): la forma anterior bloqueaba cualquier texto con «todos»/«métodos». La lista sigue siendo configurable por proyecto (`denylist` de `taxonomy.json`).
