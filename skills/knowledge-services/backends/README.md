# Contrato de adaptador (`backends/<type>.py`)

`knowledge-sync.py` (T-07) es el único núcleo: carga un adaptador por `type` (declarado en
`.claude/knowledge-services/taxonomy.json` → `backends.<id>.type`) y le pasa SOLO las entradas de
`docs/knowledge/approved/` que ya pasaron el filtro de `routing` (fail-closed, CA-09/CA-11). El
núcleo **nunca** menciona un backend concreto; añadir uno nuevo es un fichero nuevo en este
directorio (o en cualquier carpeta que el llamador añada a `--backends-dir`, ver CA-12), sin
tocar `knowledge-sync.py` ni `backends/__init__.py`.

## Nombre de fichero

`type` → `<type con "-" por "_">.py` (p. ej. `"markdown-export"` → `markdown_export.py`). Las
fixtures de test pueden usar además `backend_<type>.py` (p. ej. `backend_test.py` para
`type: "test"`), para no chocar de nombre con un futuro adaptador real del mismo `type` corto.

## Las 6 funciones obligatorias

| Función | Firma | Qué hace | Efectos permitidos |
|---|---|---|---|
| `health` | `(cfg) -> {"estado": "off"\|"sano"\|"degradado"\|"error", "detalle": str}` | Salud/desfase de red **sin publicar nada**; nunca lanza — cualquier fallo de red/parseo degrada a un `estado` del enum, nunca a una excepción. | Solo lectura (red permitida) |
| `plan` | `(entries, cfg) -> ops` | Calcula las operaciones IDEMPOTENTES a partir de `entries` (YA filtradas por `routing`; el adaptador nunca decide enrutado). Repetir `plan` con las mismas `entries` produce el mismo `ops`. | Ninguno (puro) |
| `apply` | `(ops, cfg) -> result` | Ejecuta `ops` publicando FICHERO A FICHERO desde un staging HERMANO al destino, con un diario (`manifest.pending.json` → publica → `manifest.json`) que hace segura la reanudación tras un fallo a mitad — nunca un intercambio del árbol entero (perdería ficheros ajenos al manifiesto propio). Si falla a medias, la publicación ANTERIOR debe seguir intacta y nunca se borra nada que `apply()` no controle; el `knowledge-sync.py` que lo invoca reencola con backoff (nunca dead-letter directo por un solo fallo) y drena la outbox propia ANTES de cada sync fresco — ver `references/kwipu-adapter.md` para el algoritmo de referencia. | Escritura atómica por fichero |
| `verify` | `(cfg) -> {"ok": bool, "desfase": [...]}` | Compara el manifiesto publicado contra la fuente/destino real. Si hay desfase, **nombra el remedio en `detalle`/`desfase` sin ejecutarlo** (CA-16: el reindexado, si aplica, es responsabilidad del stack externo). | Solo lectura (red permitida) |
| `rebuild` | `(entries, cfg) -> result` | Reconstruye la proyección ENTERA desde `entries` (todas las ya enrutadas, no una lista parcial) — mismo resultado que borrar la publicación y repetir `plan`+`apply` desde cero, pero sin pasar por el staging de `knowledge-sync.py` (el propio adaptador es responsable de que sea seguro). | Escritura completa |
| `revoke` | `(knowledge_id, cfg) -> result` | Invalida/tombstone una entrada que salió de `approved/`. Puede ser un no-op DECLARADO (una función que exista y no haga nada), pero tiene que existir. | Escritura puntual (o ninguno) |

Nota de diseño (T-07, desviación documentada de la tabla de `design.md`): `rebuild` recibe
`entries` como primer parámetro (no solo `cfg`) porque reconstruir exige saber QUÉ debería
existir; el enrutado sigue siendo responsabilidad exclusiva del núcleo — `rebuild` nunca decide
qué entra, solo cómo se materializa.

## Funciones OPCIONALES del contrato

Además de las 6 obligatorias, un adaptador puede exponer estas; el núcleo las pide con
`getattr(...)` y, si no están, sigue sin ellas (nunca son un requisito de carga).

| Función | Firma | Quién la usa | Qué significa que exista |
|---|---|---|---|
| `puede_leer` | `(cfg) -> {"puede": bool, "razon": str}` | el router de `knowledge-find.py --intent` | el backend decide si AUTORIZA una lectura ahora mismo (modo, salud, desfase). Sin `puede: true` exacto, el router no consulta |
| `consultar` | `(cfg, consulta) -> {"aciertos": [...], "descartados": int, "motivo": str}` | el router de `knowledge-find.py --intent` (T-07, CA-12) | **es lo que hace ENRUTABLE a un backend**: un adaptador sin `consultar` puede publicar pero nunca servir una consulta. `consulta` = `{"intent", "texto", "limit", "area", "tipo", "claves", "iniciativa"}`; devuelve `aciertos` (lista), `descartados` (int, lo que se descartó fail-closed) y `motivo` (str); cada acierto tiene que traer `id`, `estado`, `evidencia` y `ruta` canónica (el núcleo descarta, fail-closed, el que no las traiga) y `motivo` NO VACÍO con 0 aciertos significa «no pude servir» → el núcleo degrada a local con ese motivo a la vista (nunca lanza, igual que `health`) |
| `modo` | `(cfg) -> "off"\|"shadow"\|"read"` | `capabilities.py` (estado de la capacidad, sin red) | `modo(cfg)`: el adaptador es la fuente única del enum y del default de `mode`; quien lo necesite lo pregunta en vez de reimplementarlo |
| `proponer_config` | `(taxonomy, cfg) -> dict` | `knowledge-sync.py --propose-config` | el adaptador sabe proponer su propia configuración a partir de la taxonomía del proyecto |

## Carga y validación

`backends/__init__.py::cargar_adaptador(tipo, directorios=None)` busca el fichero, lo carga con
`importlib.util` y comprueba que las 6 funciones existen y son invocables. Un adaptador que no
cumple el contrato completo (fichero ausente, no carga, o falta una función) levanta
`AdaptadorNoDisponible` con un mensaje que nombra exactamente qué falta — `knowledge-sync.py` lo
convierte en `exit 2`, nunca en un traceback.

## Modo `resumen` (gap 83, fix1 2026-09-18)

Cada entrada que `knowledge-sync.py` pasa a `plan`/`rebuild` trae `modo: "completo"` o
`modo: "resumen"` (según `routing.<backend>` sea `true` o `"summary"` en `taxonomy.json`) — el
núcleo NUNCA decide qué es un resumen, solo marca la intención. Cada adaptador es responsable de
interpretarlo: el criterio de referencia (`markdown_export.py`, ver `references/kwipu-adapter.md`)
es "el campo `resumen` del frontmatter si existe, si no el primer párrafo del cuerpo". Un
adaptador nuevo puede definir otro criterio, pero tiene que documentarlo — nunca ignorar `modo` y
publicar siempre el cuerpo completo.

## Adaptador `graphiti` (ADR-018, T-04/T-05/T-06)

Segundo adaptador real del contrato: publica hacia un servidor Graphiti MCP (protocolo
streamable-HTTP, `POST <endpoint>/mcp`, JSON-RPC) resuelto en `backends/graphiti.py`, con las
funciones de proveedor (`none`/`ollama`/`openai`/`anthropic`) en `graphiti_providers.py` — añadir
un proveedor nuevo es una función nueva ahí, sin tocar `graphiti.py` (ver su docstring para la
decisión de que la extracción de entidades la hace el SERVIDOR, no el cliente).

- **Idempotencia**: manifiesto local propio (`graphiti-manifest.json` bajo
  `.claude/knowledge-services/`, patrón diario `.pending` → publicado, igual que
  `markdown_export.py`) con ids de episodio deterministas (`uuid5(group_id:knowledge_id:version)`)
  — repetir `apply()` con el mismo estado no crea duplicados.
- **`mode`** (fix1 revisión Fase 2, gap #35, CA-10): `off` corta ANTES de abrir red — `health`
  informa `{"estado": "off"}` sin conectar y `apply`/`rebuild`/`revoke` rechazan con
  `ConfigInvalida`; `shadow` (default) escribe pero nunca lee (`plan`/`apply` no dependen de una
  lectura previa); `read` exige `health` sano Y `verify` sin desfase antes de autorizar una
  lectura (`puede_leer(cfg)`, que el router de `knowledge-find.py --intent` consume antes
  de cada consulta enrutada, junto con `consultar(cfg, consulta)`).
- **`rebuild`** es el ÚNICO camino que llama a `clear_graph`, acotado al `group_id` propio, y
  reproduce el mismo manifiesto que la sincronización incremental (uuid5 determinista). **Deuda
  aceptada (gap #40/#60):** `rebuild` solo reconstruye el estado VIGENTE desde `entries` — la
  traza histórica de sucesión (tombstones y relaciones `SUPERSEDES` de versiones ya superadas)
  NO se reproduce tras un `--rebuild`; la invalidación de lo que sigue vigente en el momento del
  rebuild sí es correcta. Reproducir el historial completo requeriría que el manifiesto conservara
  las versiones superadas (`status: superseded`) y usar `graphiti_model.cadena_supersedes`, fuera
  del alcance acotado de esta iniciativa.
- **`provider.model`** es OBLIGATORIO cuando `provider.llm` no es `none` (gap #37): sin él,
  `graphiti_providers.py` no tiene ningún modelo cableado por defecto (CA-09), así que la config
  debe declararlo explícitamente. **`endpoint`/`health.url`** nunca pueden llevar userinfo
  (`usuario:token@host`, gap #43): usa `provider.api_key_env` para credenciales. **Literales
  IPv4-mapeados en IPv6** (`::ffff:169.254.169.254`, etc.) se normalizan SIEMPRE antes de
  clasificarlos como locales/privados/prohibidos (gap #53), tanto en el adaptador como en el
  esquema. **`episode_body_max_kb`** (opcional, entero > 0, default 512 KiB) acota el tamaño del
  `episode_body` enviado a `add_memory`; por encima del tope se trunca con un marcador y `apply()`
  añade un aviso en el resultado (gap #64).
- **`revoke`** nunca llama a `delete_episode`: escribe un episodio tombstone
  (`<id>@tombstone`) y, si hay una versión previa, una relación `SUPERSEDES` hacia su uuid
  (con los CUATRO campos que exige el contrato real de la tool: `source_node_name`/
  `target_node_name` son OBLIGATORIOS según el `required` del `tools/list` capturado, y los
  `*_uuid` viajan además como refuerzo — gap #69, el arbitraje anterior de #40/#56 «solo `*_uuid`»
  era incompleto y hacía fallar TODO camino de sucesión contra el servidor real); un
  cambio de `version` en `apply()` emite un tombstone+`SUPERSEDES` hacia la versión anterior
  (CA-11, sucesión observable) — con OTRO nombre de episodio: `<id>@<version>@superseded`, que
  invalida solo esa versión, frente al `<id>@tombstone` del revoke, que invalida la entrada
  entera. Compartir nombre hacía que toda entrada que hubiera subido de versión se sirviera como
  `invalidado`, también en su versión vigente (gap #96 de la revisión de la Fase 3).
- **Lectura enrutada** (`consultar`, T-07): la vigencia la decide el `status` del bloque de
  procedencia del episodio servido (sin `status` no hay acierto: no se rellena con `aprobado`)
  más los dos tombstones de arriba; la `ruta` servida tiene que ser relativa y caer bajo
  `docs/knowledge/` (fail-closed, gap #106) y TODO texto de origen servidor —`summary`/`fact`,
  que genera el LLM de Graphiti a partir de lo ingerido— sale saneado (sin control/ANSI/bidi,
  tope de 200 caracteres, gap #98). Los filtros `tipo`/`area` NO los aplica el adaptador (la
  `category` del grafo no es el tipo/área del corpus local): los post-filtra el núcleo.
- **Topes de recursos** (`max_respuesta_kb`, `max_episodes` — gap #70, lente D): cada respuesta
  MCP se lee POR TROZOS con un tope duro (`max_respuesta_kb`, entero > 0, default **8192 KiB =
  8 MiB**); pasarse es un `ErrorMCP` explícito, nunca un `MemoryError` (que además ya se captura
  en `health`/`verify`/`puede_leer`, funciones que por contrato no lanzan). La ventana de
  `get_episodes` que barre `verify()` se amplía como mucho hasta `max_episodes` (entero > 0,
  default 5000). **Escenario de carga de referencia:** con 500 entradas publicadas y ~15 000
  episodios en el grupo, `verify()` hacía hasta 4 barridos de 1000/4000/5000/5000 episodios
  (~31 MB transferidos, ~35 MB de pico) para devolver un booleano; con `max_episodes: 2000` ese
  peor caso baja a ~4 MB por barrido, y `puede_leer()` —que el router llama por
  consulta— reutiliza el resultado de `verify()` cacheado en proceso durante 5 s en vez de barrer
  el grafo en cada consulta. Ajusta `max_episodes` por encima del número de episodios que
  esperas en el grupo si `verify()` empieza a reportar desfases falsos.
- **Cambio de `group_id`** (gap #73): el manifiesto pertenece a UN grupo. Si `taxonomy.json` cambia
  `group_id`, la base de comparación pasa a estar VACÍA (todo `upsert` contra el grupo nuevo), se
  avisa en el resultado de `apply()` y el manifiesto anterior se conserva como
  `graphiti-manifest.archivado-<group_id-viejo-saneado>-<huella>.json` para poder revocar a mano
  lo que quedó en el grupo viejo (el adaptador NUNCA revoca en un grupo que ya no es el suyo). El
  prefijo `archivado-` y la huella del `group_id` crudo evitan que ese fichero choque con el
  marcador `graphiti-manifest.pending.json` o con el de otro grupo que sanee igual (gap #91); si
  ya existe, el nuevo se numera (`-2`, `-3`…) en vez de sobrescribirlo.
- **`.pending` heredado** (gaps #54/#67/#68/#79): un `.pending` de una corrida cortada se
  CONFIRMA contra el servidor (`get_episodes`) antes de promoverlo a publicado, **siempre** —
  también cuando la corrida actual trae operaciones nuevas. Lo que el servidor no reconoce se
  quita del manifiesto y `plan()` lo vuelve a proponer como `upsert` en la siguiente pasada
  (reintentar de más nunca pierde datos; promover de más, sí) — salvo que la entrada ya no esté en
  `approved/`: entonces su `revoke` se emite IGUALMENTE (tombstone + `SUPERSEDES`) con el nombre y
  el `uuid` reconstruidos del manifiesto heredado, y `revocados` solo cuenta lo que de verdad se
  envió al servidor (gap #89). El aviso del resultado distingue los tres casos (se republica /
  se revoca igualmente / sin operación en esta corrida). Si NO se puede preguntar al
  servidor (caído, timeout, respuesta ilegible), `apply()` no toca nada —ni el `.pending` ni el
  publicado— y devuelve `{"aplicados": 0, "pendiente_sin_confirmar": true, "avisos": [...]}`.
  La confirmación exige que el `uuid` coincida **cuando `get_episodes` lo devuelve**; si el
  servidor no devuelve `uuid`, la confirmación es solo por nombre (`<id>@<version>`): límite
  conocido, un servidor hostil podría afirmar tener un episodio que no tiene.
- **Guardarraíl de red** (fix1, gap #34): todo host con nombre se resuelve SIEMPRE (nunca hay
  atajo por sufijo/literal) y TODAS sus direcciones deben ser loopback/privadas; link-local
  (`169.254.0.0/16`, `fe80::/10`), direcciones no especificadas y los prefijos de TRANSICIÓN IPv6
  6to4 (`2002::/16`) y Teredo (`2001:0::/32`) —que CPython clasifica como privados y envuelven una
  IPv4 arbitraria, p. ej. `2002:a9fe:a9fe::1` = `169.254.169.254`— se rechazan SIEMPRE, incluso
  con `allow_remote: true`, en el adaptador Y en el validador estático (gaps #71/#75, copia
  declarada `direccion_prohibida_siempre` en `copias.json`); de una redirección solo se siguen
  307/308 (≤ 3 saltos, revalidando el host en CADA salto y sin reenviar `Mcp-Session-Id` si
  cambia el esquema, el host **o el puerto** respecto al salto anterior — gap #78) — 301/302/303
  son error. El presupuesto de `timeout_ms` es ÚNICO para toda la petición: se reparte entre las
  IPs candidatas y los saltos, nunca se multiplica por ellos (gap #83). La función
  `_sanear_detalle` (copia declarada de `markdown_export.py`, ADR-016) sanea cualquier texto crudo
  del servidor antes de exponerlo en un mensaje.
- **`telemetria`** (bool) se traduce a la variable de entorno `GRAPHITI_TELEMETRY_ENABLED` que lee
  el SDK/servidor antes de abrir la primera conexión de cada llamada pública (`health`/`apply`/
  `rebuild`; `revoke` la aplica transitivamente al llamar a `apply` internamente).
- **`concurrency`** (validado por el esquema) queda RESERVADO — el servidor de referencia impone
  `SEMAPHORE_LIMIT: 1`, así que `apply()` sigue secuencial a propósito; el coste de una conexión +
  resolución DNS por operación se mitiga con una caché de resolución de TTL corto, no con paralelismo.
- **`knowledge-sync.py --backend <id> --propose-config`**: el núcleo llama a la función
  **opcional** `proponer_config(taxonomy, cfg)` del adaptador (séptima función del contrato, la
  única no obligatoria) y, si existe, imprime su clave `texto` tal cual (o el JSON completo con
  `--json`); si el adaptador no la define, lo dice y sale con 2. El núcleo NO nombra ningún
  backend concreto (gap #77, invariante del plan y CA-12). En `graphiti.py` la propuesta es el
  bloque `entity_types` para el `config.yaml` del servidor + el `entity_map` para
  `taxonomy.json`, sin aplicar nada ni tocar la red.

## Adaptador de fixture (CA-12)

`evals/fixtures/knowledge-services/backend_test.py` implementa el contrato completo de forma
trivial (`type: "test"`) para que los tests de `knowledge-sync.py` demuestren que un backend nuevo
no toca el núcleo: se carga pasando su carpeta en `--backends-dir`, fuera del árbol real del
plugin.
