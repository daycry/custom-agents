---
design: graphiti-memory
estado: aprobado
opcion_elegida: O1
---

# Diseno - proyeccion Graphiti derivada

**O1 elegida:** `approved/` es la fuente, un sincronizador genera episodios idempotentes SOLO para las categorias cuyo `routing.graphiti` (en `.claude/knowledge-services/taxonomy.json`, definido por `knowledge-services`) sea `true`, y un router consulta Graphiti solo ante relaciones, evidencia o tiempo. **O2 descartada:** guardar memoria de cada turno, por ruido, privacidad e inyeccion. **O3 descartada:** hacer que Graphiti sea el almacen primario. **O4 descartada:** sincronizar TODO `approved/` sin distincion por categoria — el plugin es base de proyectos con dominios distintos y no todos quieren relaciones temporales para todas sus categorias (p. ej. un `TOOL` documentado no necesita grafo).

Cada instalacion configura un `group_id` estable bajo `.claude/knowledge-services/`; nunca acepta uno libre desde el prompt. Las escrituras pasan por Curator/sincronizador. El adaptador conserva `knowledge_id`, `version`, `status`, `evidence_level`, `source_path` y hash. Un `SUPERSEDES` invalida la vigencia sin borrar la version previa.

No hay red desde hooks. El cliente usa timeout, allow-list de loopback por defecto y `GRAPHITI_TELEMETRY_ENABLED=false` cuando el usuario lo elija. La sincronizacion se lanza explicitamente al cerrar la curacion o a demanda, y por categoria: una categoria sin `routing.graphiti` declarado (o `false`) nunca genera episodios (fail-closed, mismo criterio que el exportador Kwipu).

## Enmienda 2026-09-17 — Graphiti como adaptador (`ADR-018`)

```json
"backends": {
  "graphiti": {
    "type": "graphiti", "enabled": true, "mode": "shadow",
    "endpoint": "http://127.0.0.1:8000", "group_id": "<slug-estable>", "allow_remote": false,
    "telemetry": false, "timeout_ms": 3000, "concurrency": 1,
    "provider": {"llm": "ollama", "model": "qwen2.5:7b", "base_url": "http://127.0.0.1:11434",
                 "embedder": "ollama", "embedder_model": "nomic-embed-text"},
    "router": {"intents": {"temporal": true, "relacional": true, "evidencia": true}, "default": "local"},
    "relations": ["MITIGATES", "APPLIES_TO"]
  }
}
```

- **Adaptador** `skills/knowledge-services/backends/graphiti.py` implementa `health · plan · apply · verify ·
  rebuild · revoke`. `plan` traduce entradas `approved` (ya filtradas por `routing`) a episodios idempotentes con
  `knowledge_id`, `version`, `status`, `evidence_level`, `source_path`, hash; `apply` corre sobre `outbox.py`
  (claim, reintento acotado, dead-letter); `verify` compara el manifiesto del grupo con `approved/`; `rebuild`
  vacia el grupo y reproduce el manifiesto; `revoke` escribe la invalidacion (`SUPERSEDES` hacia tombstone) sin
  borrar historial.
  **Deuda aceptada (gaps #40/#60 de la revisión de la Fase 2, 2026-09-21):** `rebuild` reconstruye únicamente el estado
  VIGENTE desde `entries`; la traza histórica de sucesión (tombstones y relaciones `SUPERSEDES` de versiones ya
  superadas antes del rebuild) no se reproduce tras un `--rebuild` — la invalidación de lo vigente en ese momento sí
  es correcta. Reproducir el historial completo exigiría que el manifiesto conservara las versiones superadas
  (`status: superseded`) y usar `graphiti_model.cadena_supersedes`; queda fuera del alcance acotado de esta iniciativa.
- **Proveedor**: `provider.llm` en `ollama | openai | anthropic | none`. Con `none` el adaptador no extrae
  entidades: solo acepta episodios con estructura ya calculada (util para CI y para proyectos sin modelo local).
  Cada proveedor es una funcion pequena con la misma firma; anadir uno no toca el adaptador.
- **Modo**: `off` (registrado, inactivo) → `shadow` (sincroniza, no lee; default) → `read` (el router puede
  leer, solo si `health` sano y `verify` sin desfase). El paso a `read` lo hace el usuario en la config.
- **Router**: `knowledge-find.py --intent <x>` consulta el adaptador solo si `intents.<x>` es `true` y `mode` es
  `read`; en cualquier otro caso responde el camino local/Kwipu. No hay clasificacion por modelo.
- **Ontologia**: nucleo `Knowledge`, `Evidence`; un `entity_type` por categoria de `taxonomy.json`
  (`categories[].entity_type`, default la clave); relaciones nucleo `SUPPORTED_BY`, `SUPERSEDES`, `CONTRADICTS`
  + `relations` declaradas. El plugin no conoce `Constraint`, `Failure` ni ningun tipo de dominio.
- **Seguridad**: `allow_remote: false` limita a loopback; `telemetry: false` fija `GRAPHITI_TELEMETRY_ENABLED`;
  ninguna credencial en `taxonomy.json` (variables de entorno referenciadas por nombre).
- Se registra en `capabilities.py` (`graphiti`) para `/setup` y `/doctor` sin tocar `doctor.py`.

## Enmienda 2026-09-19 — forma de la configuración y guardarraíl de red (revisión de la Fase 1, intento 1)

Registrada por el orquestador tras la revisión de dos lentes de la Fase 1 (gaps #1, #3, #9, #10). Prevalece sobre el
ejemplo de la enmienda 2026-09-17 donde difieran.

- **Forma anidada, no plana.** El bloque de Graphiti sigue el patrón genérico de `knowledge-services`
  (`backends.<id> = {type, enabled, config}`, igual que `markdown-export`): `mode`, `endpoint`, `group_id`,
  `allow_remote`, `provider`, `entity_map`, `relations`, `router`, `telemetria` y `health` viven **dentro de `config`**.
  Cualquier clave no reconocida a nivel de `backends.<id>` o dentro de `config`/`provider`/`router`/`health` es
  **error** de validación (así el ejemplo plano antiguo no pasa en silencio). Ejemplo vigente: el bloque `graphiti` de
  `agent-kits/shared/templates/taxonomy.json`.
- **`group_id` sin default cableado.** Si el proyecto no lo declara, se deriva del nombre del directorio del proyecto
  como slug **Unicode** (NFKC, `[^\W_]`), buscando el backend por `type: "graphiti"`; a diferencia de `id_prefix`, **no**
  cae a `"ca"`: si no se puede derivar, con `enabled: true` la validación falla pidiendo declararlo (revisión Fase 1,
  gaps #17, #23, #29). Dos instalaciones en la misma máquina no comparten grupo por omisión.
- **Guardarraíl de red = el del repo (local o privado), no solo loopback.** `endpoint` y `health.url` aceptan sin
  `allow_remote` los mismos hosts que el adaptador Kwipu (`localhost`, loopback, redes privadas, sufijos locales como
  `*.test`/`host.docker.internal`, `lib-guardrail.sh`); cualquier otro exige `allow_remote: true`. La frase «allow-list de
  loopback por defecto» de la sección inicial se lee así.
- **Vocabulario.** La clave es `telemetria` (vocabulario ES de `dev.json`), no `telemetry`; `health.timeout_ms` > 0.
- **Propuesta de tipos y tipo efectivo (revisión Fase 1, intento 2, gap #16).** Sin `entity_map` todos los episodios
  viajan con el tipo genérico del servidor (`Document`); `--propose-config` emite el bloque `entity_types` para el
  `config.yaml` del servidor **y** el `entity_map` para `taxonomy.json` que los hace efectivos (una entrada por categoría,
  nombre = `entity_map[key]` o TitleCase Unicode de la `key`; si no se puede derivar un nombre, error que pide declarar el
  mapeo). Donde la sección inicial dice «un `entity_type` por categoría … default la clave», se lee así.
- **Claves de cliente (gap #19).** `config.timeout_ms` (entero finito > 0; timeout de las llamadas MCP) y
  `config.concurrency` (entero ≥ 1; default 1, coherente con `SEMAPHORE_LIMIT: 1` del stack de referencia) forman parte
  de la lista cerrada de `config`. `group_id` se deriva por `type: "graphiti"` (no por la clave del backend) y, con
  `enabled: true`, debe quedar como cadena no vacía (slug Unicode; si no se puede derivar, error que pide declararlo).

## Enmiendas tras la verificación dirigida de la Fase 2 (fix4 + fix5, 2026-09-21)

- **`revoke` sobre una entrada podada del `.pending` heredado (gap #89):** un `revoke` cuya entrada la reconciliación no pudo confirmar se emite igual (tombstone + `SUPERSEDES`) con el nombre `<id>@<version>` y el uuid5 determinista reconstruidos del manifiesto heredado; sin datos suficientes va a `fallidos` con causa explícita, nunca a `revocados`. Un `apply()` llamado a mano con una op de `revoke` sin rastro alguno levanta error (antes se contaba como revocado).
- **Archivado del manifiesto al cambiar `group_id` (gaps #73/#91):** el fichero pasa a `graphiti-manifest.archivado-<group_id saneado>-<sha1(group_id)[:8]>.json`, con sufijo `-2`, `-3`… si ya existe; nunca colisiona con el marcador `.pending` ni entre grupos que saneen igual. sha1 es huella de nombre, no criptografía.
- **Caché de `verify` (gap #95):** se invalida por clave `(endpoint, group_id, _root)` al final de `apply()`, `rebuild()` y `revoke()`.
- **Tope de lectura configurable (`max_respuesta_kb`, gaps #70/#90):** lo respetan los cinco constructores del cliente MCP, `health()` incluido.

## Enmiendas tras la revisión de la Fase 3 (intento 1 → `fix1`, 2026-09-21)

- **Vigencia y tombstones (gap #96, Critical).** La vigencia de un acierto la decide el `status` del bloque de procedencia del episodio SERVIDO (sin `status`, no hay acierto: fail-closed), más dos tombstones con nombres DISTINTOS por camino: `<id>@tombstone` (revoke) invalida la entrada entera; `<id>@<version>@superseded` (sucesión de versión) invalida solo esa versión. Donde la sección inicial y la enmienda de 2026-09-18 hablan de «un tombstone» para los dos caminos, se lee así: compartir nombre hacía que toda entrada que hubiera subido de versión se sirviera como `invalidado`, también en su versión vigente.
- **Ruta canónica y saneado en la lectura (gaps #98/#106).** `consultar` solo sirve `source_path` RELATIVAS bajo `docs/knowledge/` (sin `..`, sin unidad ni raíz) y sanea todo texto de origen servidor (`summary`/`fact`/`evidence_level`/`valid_at`…: los genera el LLM del servidor a partir de lo ingerido) con el mismo criterio que los mensajes de error — tope de 200 caracteres, sin controles/ANSI/bidi/C1. El núcleo repite el saneado sobre el acierto y sobre la línea compacta: no se fía de que todo adaptador lo haga.
- **Config efectiva (gap #97, Critical).** El router pasa al adaptador la config EFECTIVA (la declarada más los defaults derivados, `group_id` incluido), nunca la cruda de `taxonomy.json`; la derivación es una copia declarada (`copias.json`, bloque `group_id_por_defecto`) entre el validador y el núcleo, sin un solo import de red. Sin `group_id` efectivo no se consulta: degradación a local con motivo.
- **Límite del guardarraíl estático de red en hooks (gap #101, arbitraje (c)).** El seguidor transitivo de `tests/test_knowledge_services.py::_ofensores_de_scripts_invocados` resuelve rutas de script CITADAS LITERALMENTE; no resuelve una ruta compuesta en runtime a partir de fragmentos (`BACKENDS_REL` + `cargar_adaptador` en `knowledge-find.py`/`capabilities.py`), así que **no** ve por sí solo el camino núcleo → adaptador con red. Límite declarado, no defecto: lo cubren dos puertas nuevas y explícitas — (a) ningún fichero de `hooks/` puede invocar `knowledge-find.py`/`capabilities.py` con `--intent` o `--backends-dir` (los únicos flags que cargan un adaptador), y (b) con el argv EXACTO del hook, `knowledge-find.py` no llama a `_cargar_modulo` (espía). Si algún día el hook necesitara enrutar, las dos puertas se ponen rojas antes que el invariante.
- **Episodio sin `group_id` (gap #105).** El `outputSchema` real de `get_episodes` declara los episodios como objetos ABIERTOS (`additionalProperties: true`): `group_id` no está garantizado. La sonda de SOLO LECTURA contra el servidor real (2026-09-21) no pudo confirmarlo porque el grafo está VACÍO (`get_episodes` sin filtro → `No episodes found`; `search_nodes` con varias consultas → `No relevant nodes found`), así que se adopta la regla conservadora del arbitraje: un episodio sin `group_id` se acepta SOLO porque la consulta se acotó a UN único `group_ids` —es el servidor quien filtró— y se rechaza si alguna vez se pidiera más de uno. Cuando haya datos reales, confirmar si el servidor lo devuelve siempre y pasar a fail-closed puro.
- **Límite conocido de la lectura enrutada: `_nombres_de_hit` (fuera de lente, informativo).** Los aciertos de `search_nodes`/`search_memory_facts` se casan con los episodios propios por NOMBRE (`<id>@<version>`), y los nodos que extrae el servidor llevan nombres de ENTIDAD, no de episodio: en un grafo poblado es probable que buena parte de los aciertos de `search_nodes` acabe en `descartados` (fail-closed: se prefiere descartar a servir procedencia inventada). No se pudo medir: el grafo real está vacío. Queda anotado como límite a verificar con datos —y, si se confirma, el camino es casar además por `uuid` de episodio o pedir al servidor los episodios fuente del nodo, no relajar el fail-closed.

## Enmiendas tras la revisión de la Fase 3 (intento 2 → `fix2`, 2026-09-21)

- **Vocabulario servido al post-filtro (gap #117, Important).** El adaptador sirve, además de `categoria` (la clave de taxonomía), el `tipo` y el `area` que el corpus LOCAL entiende: `tipo` es el `categories[].folder` DECLARADO en `taxonomy.json` (`adr`/`gotchas`/`lessons`) —que es exactamente lo que `knowledge-find.tipo_normalizado` traduce al tipo local— y `area` sale de los `tags` `area:<valor>` de la entrada. Los dos viajan en el bloque de procedencia del episodio (`local_folder`, `area`). **Ninguna equivalencia categoría→tipo se cablea en el núcleo** (seguiría siendo una lista de dominio en el plugin, contra CA-13): sale de la taxonomía del proyecto y del frontmatter de la entrada. Para grafos publicados antes de fix2, el `tipo` se deriva de la propia `source_path`; el `area` queda vacía hasta republicar. Y si el post-filtro se lleva TODOS los aciertos del grafo, la consulta cae al camino LOCAL diciendo cuántos tiró —antes devolvía `origen: backend`, `total: 0` y el corpus local no se consultaba nunca.
- **Versión vigente, no «el primer hit» (gap #118, Important; residual de #96).** Cuando la búsqueda devuelve v1 y v2 de la misma entrada (el caso normal: contenido casi idéntico casa la misma query), los aciertos se agrupan por `knowledge_id` y se sirve la VIGENTE —la no invalidada de mayor `version`—, nunca la primera que llegue. Las versiones no vigentes del mismo `knowledge_id` no son «descartes»: la entrada sí se sirve, por su versión buena.
- **Presupuesto de `/doctor` por BACKEND, no por capacidad (gap #119, Important).** El presupuesto del bloque de capacidades es un DEADLINE compartido que se re-evalúa dentro del bucle por backend (una capacidad con N backends multiplicaba por N el coste de red sin aviso: medido con blackhole TCP, 3,14 s con 1 backend → 9,24 s con 3); al agotarse, los backends que faltan salen como «no comprobado: presupuesto de red del bloque agotado». El tope de `/doctor` alcanza también al `timeout_ms` de NIVEL SUPERIOR (antes solo recortaba `health.timeout_ms`, así que la mitad cara del diagnóstico se le escapaba) y acota la ventana de lectura (`max_episodes`) a una ventana de diagnóstico: `/doctor` diagnostica, no verifica exhaustivamente. Todo por claves del vocabulario COMPARTIDO de config de backends — `doctor.py` sigue sin nombrar ninguna capacidad (CA-14, `grep -c graphiti` → 0).
- **Los dos topes de lectura tienen que ser coherentes (gap #120, Important).** Con los DEFAULTS, la ampliación de ventana de `verify()` llegaba a 4000 episodios ≈ 12,5 MiB, por encima de `max_respuesta_kb` (8 MiB): `ErrorMCP` ⇒ `verify` en falso ⇒ `puede_leer` false ⇒ toda consulta enrutada degradada a local con 0 aciertos, justo en el escenario de referencia documentado (500 entradas / 15 000 episodios). **Decisión:** como `get_episodes` NO tiene cursor de paginación en el contrato real, la «página» es la propia ventana — cuando una ampliación no cabe en el tope de lectura se conserva la última que sí cupo y la ventana se declara INCOMPLETA. Con la ventana incompleta, `verify()` no llama desfase a lo que no ha podido mirar (misma distinción del gap #67): `ok: true` + `no_verificado: N` + `aviso`; y `apply()` no promueve nada. La fórmula de coherencia queda documentada en `backends/README.md`: `max_respuesta_kb ≈ 3 × max_episodes` (KiB, con ~3 KiB por episodio).
- **Recall de la procedencia (gap #121, Important).** `search_*` busca en TODO el grafo pero la procedencia solo se lee con `get_episodes`, ventana de los más recientes. **El contrato real no ofrece ninguna herramienta que devuelva un episodio por `uuid`** (`tools/list` de 2026-09-18: `get_entity_edge` y `delete_episode` toman uuid, pero ninguna LEE un episodio por uuid; `get_episodes` solo acepta `group_ids` y `max_episodes`), así que la única «paginación» posible es ampliar la ventana: arranca pequeña y crece ×4 hasta resolver todos los aciertos, hasta que el servidor devuelva menos de lo pedido, o hasta el tope (`max_episodes`, como mucho 2000 por consulta). **Lo que siga fuera se CUENTA** (`fuera_de_ventana`, contador propio distinto de `descartados`) y sale en el `motivo`: nunca en silencio. Recall medido con 500 episodios (el corpus objetivo declarado) y los defaults: 100 %.
- **Migración de grafos publicados antes de fix1 (gap #126).** Hasta fix1, la sucesión de versión emitía `<id>@tombstone`, el mismo nombre que el revoke, así que el lector de hoy invalidaría la entrada entera. Un grafo publicado desde la rama antes de `59d9e35` (ningún release contiene esos commits: `git tag --contains` vacío) hay que republicarlo con `knowledge-sync.py --backend <id> --rebuild`. `verify()` lo DETECTA —tombstone de una entrada que el manifiesto da por vigente— y nombra el remedio en su `aviso`, sin ejecutarlo (CA-16).

## Enmienda tras la revisión de la Fase 4 (intento 2 → `fix2`, 2026-09-23)

- **Excepción NOMINAL a «No hay red desde hooks» (gap #173, Important).** La frase del párrafo de arriba (y «llamadas de red en hooks» de «Fuera de alcance» en `spec.md`) tiene **una** excepción real, anterior a esta iniciativa y opt-in: el resumen por IA del journal de sesión. `agent-kits/shared/journal.py` —alcanzable desde `hooks/session-journal.sh` y `hooks/session-context.sh`— lanza `claude -p <prompt> --bare` (`resumen_ia`) **solo** con `.claude/dev.json` → `sesion.resumen: true` (`ia_activa`, que exige `is True`) o con `--ia on` explícito, que ningún hook pasa (`session-context.sh` invoca `replay --ia no`). Decisión de ADR-010 revisado / ADR-013 (memory-retrieval F4-F6), no de graphiti-memory. La conciliación: la iniciativa NO añade ninguna llamada de red a los hooks, y la suite `tests/test_graphiti_security.py` declara la excepción como `_EGRESS_OPT_IN_DECLARADO` —**ese fichero y esos dos motivos** (`ejecutable claude`, `argv <variable> -p`), ninguno más— y solo la aplica mientras la guardia siga en el código (`_egress_del_journal_sin_condicion`: si `resumen_ia` deja de depender de `ia_activa(root)` o `ia_activa` deja de exigir `is True`, la puerta se pone roja). Cualquier otro script alcanzable que lance `claude`, o el mismo código con otro nombre, es FALLO.
- **La puerta mira el código, no solo las cadenas (gaps #173, #176, #177, #182, #183).** El escaneo de binarios de red por TOKEN se aplica también al AST de cada `.py` alcanzable (argv literales en lista/tupla, cadenas de shell pasadas a `subprocess.*`/`os.system`/`os.exec*`/`Popen`, el literal `claude`); `__import__`/`import_module` con literal cuentan como import y sin literal son FALLO; una cita a un ejecutable que la puerta no sabe escanear (`.js`/`.mjs`/`.ps1`/`.cmd`) es FALLO salvo lista blanca nominal (vacía); una cita se resuelve solo por su ruta literal (raíz, directorio del que cita, variable asignada en el propio `.sh`) o por la tabla nominal `_CITAS_POR_NOMBRE`, nunca por basename; y el comentario final de una línea de shell se quita antes de tokenizar.
- **CA-05 sin exención por prefijo (gaps #175, #179, #181).** Las piezas exentas de la puerta «ninguna pieza escribe en el grafo» se nombran una a una (`backends/README.md` para las primitivas; `SKILL.md`, `backends/README.md` y `references/kwipu-adapter.md` —solo para `--backend kwipu`— para el sincronizador); la invocación multilínea (continuaciones y bloque con valla como unidad) ya no la evade, y una variable en prosa no cuenta como invocación.
