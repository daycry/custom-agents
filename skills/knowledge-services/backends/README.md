# Contrato de adaptador (`backends/<type>.py`)

`knowledge-sync.py` (T-07) es el núcleo de publicación: carga un adaptador por `type` (declarado en
`.claude/knowledge-services/taxonomy.json` → `backends.<id>.type`) y le pasa SOLO las entradas de
`docs/knowledge/approved/` que ya pasaron el filtro de `routing` (fail-closed, CA-09/CA-11). El
núcleo **nunca** menciona un backend concreto; añadir uno nuevo es un fichero nuevo en este
directorio (o en cualquier carpeta que el llamador añada a `--backends-dir`, ver CA-12), sin
tocar `knowledge-sync.py` ni `backends/__init__.py`.

## Alcance de los adaptadores incluidos

| Adaptador | Publicación y verificación | Consulta desde el plugin |
|---|---|---|
| `markdown-export` (Kwipu) | Exporta Markdown y manifiesto propios; consulta salud/snapshot del bridge para verificar. Nombra el reindexado externo sin ejecutarlo. | Expone `puede_leer` y `consultar` opcionales. `knowledge-find.py --intent` exige backend habilitado, `read.enabled: true`, intent autorizado y contexto canónico completo antes de red/inferencia. Un rechazo o fallo vuelve a local. |
| `graphiti` | Publica y verifica episodios mediante MCP. `off` evita conexiones y rechaza escrituras; `shadow` (default) permite sincronizar, sin autorizar consultas. | `read` permite solicitar lectura mediante `knowledge-find.py --intent`; exige backend habilitado, intent declarado como `true`, grupo propio efectivo, `health` sano y `verify` completo sin desfase. Un rechazo o fallo degrada a la búsqueda local con motivo. |

Instalar el plugin no activa estos servicios. La publicación sigue limitada a las entradas
aprobadas que el `routing` del proyecto autoriza. Los proveedores de `graphiti_providers.py`
orientan la extracción mediante instrucciones enviadas al servidor: no configuran ni ejecutan
un modelo o embedder desde el cliente. La configuración efectiva y el coste de esos servicios
dependen del servidor; `provider.llm: none` omite esas instrucciones, sin desactivar por sí solo
la extracción del servidor.

## Autoridad y recuperación local

El Markdown local es canónico. `knowledge-find.py` recupera ADR/GOT/LES legados y entradas
válidas de `approved/` con su ID completo, versión, estado, evidencia y ruta. Query y relaciones
JSON conservan `version` del conocimiento; `--show --json` conserva `version: 1` del envelope
y añade `knowledge_version`. Las relaciones aprobadas incluyen sus enlaces declarados.

La categoría determina el tipo de consulta, independientemente de la carpeta: DECISION →
`adr`, GOTCHA/PATTERN → `gotcha`, LESSON → `leccion`; una categoría propia usa su etiqueta
normalizada. `aprobado` comparte prioridad con `aceptada`, sin cambiar su estado almacenado.
La caché SQLite es reconstruible y conserva los mismos metadatos que el recorrido plano.

La lectura local usa reglas compartidas sin cargar adaptadores ni validar conexiones.
Una configuración de servicio inválida no elimina la memoria local; una taxonomía local o
corpus aprobado inválido excluye ese corpus con diagnóstico y conserva el legado válido.
Se rechazan IDs aprobados duplicados y rutas fuera de las carpetas declaradas. Una colisión
entre legado y aprobado hace fallar `--show`/`--related` en vez de elegir el primero.
`candidates/` no participa. Validar carpeta, forma y estado no acredita aprobación humana
o semántica; esta lectura no promueve entradas ni cambia la política del Curator.

El lector común conserva etiquetas de contenido derivado y UUID en JSON, con ID y ruta
exactos dentro de sus límites. La línea compacta antepone «derivado sin autoridad» para
que el recorte no elimine esa distinción en CLI o briefs. Contratos incompletos o
identidades inseguras se descartan; aprobado describe la fuente, no el texto derivado.

Los backends siguen siendo proyecciones opcionales. Una lectura externa autorizada conserva
versiones válidas; errores o respuestas incompatibles degradan a la recuperación local con
motivo. El versionado del Markdown en Git depende de la política del proyecto consumidor.

La lectura documental de Kwipu distingue aciertos canónicos de `respuesta_generada`.
Esta última declara `verificacion: no_verificada`, `autoridad: ninguna` y
`citas_por_afirmacion: false`. Sus `source_nodes` son fuentes recuperadas vinculadas;
no acreditan cada afirmación ni convierten el texto generado en conocimiento aprobado.

## Errores MCP y confirmación de publicación

El cliente Graphiti decodifica `ErrorResponse` aunque el transporte devuelva
`isError: false`. Un campo `error` en la salida tipada provoca `ErrorMCP` con
diagnóstico saneado; una respuesta de éxito se conserva. Esta comprobación
cubre el envelope `structuredContent.result` y el JSON de contenido textual.

Aceptar una solicitud en cola no confirma que el episodio exista. La prueba real
de creación encontró un rechazo posterior al enviar el UUID calculado para una
entrada nueva: Graphiti 0.30.1 intenta recuperar un episodio existente cuando se
le pasa UUID. La creación actual omite ese campo y exige lectura de UUID/contenido.
La reconstrucción aún requiere aceptación real. Health sano y la suite sintética no
cierran esa aceptación. [Evidencia](../../../docs/roadmap/2026-10-07-catalog-capabilities/testing/graphiti-error44-evidence.json).

## Nombre de fichero

`type` → `<type con "-" por "_">.py` (p. ej. `"markdown-export"` → `markdown_export.py`). Las
fixtures de test pueden usar además `backend_<type>.py` (p. ej. `backend_test.py` para
`type: "test"`), para no chocar de nombre con un futuro adaptador real del mismo `type` corto.

## Las 6 funciones obligatorias

| Función | Firma | Qué hace | Efectos permitidos |
|---|---|---|---|
| `health` | `(cfg) -> {"estado": "off"\|"sano"\|"degradado"\|"error", "detalle": str}` | Salud/desfase de red **sin publicar nada**; nunca lanza — cualquier fallo de red/parseo degrada a un `estado` del enum, nunca a una excepción. | Solo lectura (red permitida) |
| `plan` | `(entries, cfg) -> ops` | Calcula las operaciones IDEMPOTENTES a partir de `entries` (YA filtradas por `routing`; el adaptador nunca decide enrutado). Repetir `plan` con las mismas `entries` produce el mismo `ops`. | Ninguno (puro) |
| `apply` | `(ops, cfg) -> result` | Ejecuta `ops` publicando FICHERO A FICHERO desde un staging HERMANO al destino, con un diario (`manifest.pending.json` → publica → `manifest.json`) que hace segura la reanudación tras un fallo a mitad — nunca un intercambio del árbol entero (perdería ficheros ajenos al manifiesto propio). Si falla a medias, pueden quedar archivos ya actualizados o revocados: el diario permite completar el objetivo pendiente, sin rollback global. Nunca se borra nada que `apply()` no controle; el `knowledge-sync.py` que lo invoca reencola con backoff (nunca dead-letter directo por un solo fallo) y drena la outbox propia ANTES de cada sync fresco — ver `references/kwipu-adapter.md` para el algoritmo de referencia. | Escritura atómica por fichero |
| `verify` | `(cfg) -> {"ok": bool, "desfase": [...]}` | Compara el manifiesto publicado contra la fuente/destino real. Si hay desfase, **nombra el remedio en `detalle`/`desfase` sin ejecutarlo** (CA-16: el reindexado, si aplica, es responsabilidad del stack externo). | Solo lectura (red permitida) |
| `rebuild` | `(entries, cfg) -> result` | Reconstruye la proyección ENTERA desde `entries` (todas las ya enrutadas, no una lista parcial) — mismo resultado que borrar la publicación y repetir `plan`+`apply` desde cero, pero sin pasar por el staging de `knowledge-sync.py` (el propio adaptador es responsable de que sea seguro). | Escritura completa |
| `revoke` | `(knowledge_id, cfg) -> result` | Invalida/tombstone una entrada que salió de `approved/`. Puede ser un no-op DECLARADO (una función que exista y no haga nada), pero tiene que existir. | Escritura puntual (o ninguno) |

Nota de diseño (T-07, desviación documentada de la tabla de `design.md`): `rebuild` recibe
`entries` como primer parámetro (no solo `cfg`) porque reconstruir exige saber QUÉ debería
existir; el enrutado sigue siendo responsabilidad exclusiva del núcleo — `rebuild` nunca decide
qué entra, solo cómo se materializa.

## Funciones OPCIONALES del contrato

La lectura se invoca mediante `consultar(cfg, consulta)`: `cfg` contiene la
configuración del backend y `consulta` describe la petición ya autorizada por
el router. Esta función opcional devuelve resultados; no publica ni aprueba
conocimiento. La tabla siguiente define su forma y los controles del caller.

Además de las 6 obligatorias, un adaptador puede exponer estas; el núcleo las pide con
`getattr(...)` y, si no están, sigue sin ellas (nunca son un requisito de carga).

| Función | Firma | Quién la usa | Qué significa que exista |
|---|---|---|---|
| `puede_leer` | `(cfg) -> {"puede": bool, "razon": str}` | el router de `knowledge-find.py --intent` | el backend decide si AUTORIZA una lectura ahora mismo (modo, salud, desfase). Sin `puede: true` exacto, el router no consulta |
| `consultar` | `(cfg, consulta) -> {"aciertos": [...], "descartados": int, "motivo": str}` | el router de `knowledge-find.py --intent` (T-07, CA-12) | **es lo que hace ENRUTABLE a un backend**: un adaptador sin `consultar` puede publicar pero nunca servir una consulta. `consulta` = `{"intent", "texto", "limit", "area", "tipo", "claves", "iniciativa"}`; devuelve `aciertos` (lista), `descartados` (int, lo que se descartó fail-closed) y `motivo` (str); cada acierto tiene que traer `id`, `estado`, `evidencia` y `ruta` canónica (el núcleo descarta, fail-closed, el que no las traiga) y `motivo` NO VACÍO con 0 aciertos significa «no pude servir» → el núcleo degrada a local con ese motivo a la vista (nunca lanza, igual que `health`) |
| `modo` | `(cfg) -> "off"\|"shadow"\|"read"` | `capabilities.py` (estado de la capacidad, sin red) | `modo(cfg)`: el adaptador es la fuente única del enum y del default de `mode`; quien lo necesite lo pregunta en vez de reimplementarlo |
| `proponer_config` | `(taxonomy, cfg) -> dict` | `knowledge-sync.py --propose-config` | el adaptador sabe proponer su propia configuración a partir de la taxonomía del proyecto |
| `estado_grupo` | `(cfg, consultar_servidor=False) -> {"estado", "origen", "aviso"}` | `knowledge-sync.py --avisos-grupo [--consultar-servidor]` (`/setup`, CA-15) | avisa, ANTES de la primera sincronización, si el `group_id` ya trae episodios de otro origen: primero estado local (manifiesto), después servidor solo con opt-in y en loopback; sin respuesta, `no_verificado`. Nunca bloquea (exit 0) |

`consultar` puede añadir el campo genérico opcional `respuesta_generada`. El router
valida su forma y los bindings; no añade autoridad ni un contrato de citas por afirmación.
Los adaptadores que implementan solo las seis funciones siguen siendo compatibles.

## Qué autoriza la lectura documental de Kwipu

`agent-kits/shared/knowledge-read-context.py` prepara el contexto desde la política
y el corpus actual. Exige `routing` y filtros sobre todo el conjunto publicado.
El protocolo nativo de consulta no restringe fuentes: un filtro que excluya alguna
entrada enrutada rechaza la lectura antes de consultar el servicio.

El adaptador compara canon, proyección y manifiesto propio. Después exige salud sana
y un snapshot completo con cinco metadatos por chunk: ID, versión, hash, proyecto y scope.
Todos los chunks deben corresponder al conjunto autorizado. Un filename nulo solo se
resuelve mediante ese binding; entidades, basenames o `fm.id` aislado no sustituyen el ID.

Cada consulta comparte un plazo monotónico para autorización, HTTP y revalidación.
Los límites acotan cuerpos, respuesta y fuentes. El lector refresca canon y snapshot;
un cambio, truncado o fuente irresoluble suprime la respuesta y conserva fallback local.
La coincidencia observada no garantiza atomicidad multiarchivo ni detecta cambios ABA.
Configuración y presupuesto exactos: [adaptador Kwipu](../references/kwipu-adapter.md#cómo-habilitar-la-lectura-documental).

Conserva en el bundle portable `agent-kits/shared/local-read.py`,
`agent-kits/shared/knowledge-read-context.py`, `agent-kits/shared/knowledge-taxonomy-local.py`
y los lectores locales existentes junto al router.
Instalaciones parciales degradan a local; el panel y los hooks no activan esta ruta.

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

## Adaptador `graphiti`

Cliente MCP streamable-HTTP de stdlib, con inicialización y sesión. La configuración
del servidor decide extracción, modelos y embeddings; `graphiti_providers.py` orienta
esa extracción sin llamar a modelos desde el plugin. Un proveedor conserva nombre,
grupo y procedencia; un episodio nuevo no declara UUID remoto.

Lee [publicación y recuperación](../../../docs/knowledge-services-graphiti.md) para
la confirmación asíncrona, recibos, versiones y elección de `transition_relations`.
El valor predeterminado `episode` confirma relaciones documentales en el grupo propio.
`triplet` requiere un servidor cuya escritura entre entidades esté aislada por grupo;
la firma MCP con `group_id` no demuestra ese aislamiento. Los UUID de episodios y
entidades tienen responsabilidades distintas.

- **Publicación**: el UUID real y el hash del cuerpo enviado se vinculan después de
  leer el episodio persistido. El manifiesto pendiente guarda progreso; una respuesta
  de encolado no autoriza commit. El recibo conserva incertidumbre tras perder una
  respuesta, sin reenvío automático. Los límites suman episodios y relaciones.
- **Marcadores de control**: sucesión y retirada no heredan episodios previos. Excluyen
  `Entity` y los tipos que el proyecto declare en `transition_excluded_entity_types`,
  con instrucciones de no extraer entidades de dominio. La configuración debe incluir
  todos los tipos personalizados del servidor; el SDK sigue usando el modelo para la
  extracción inicial. Las entradas de conocimiento conservan su extracción habitual.
- **Versiones**: sucesión y retirada usan marcadores por versión. La retirada vincula
  grupo, versión, UUID y hash; una operación antigua no retira una generación nueva.
  Las identidades retenidas sirven para retirar episodios fuera de la ventana de
  observación. Los marcadores legacy de invalidación completa conservan su significado.
- **Modos**: `off` evita conexiones y rechaza escrituras; `shadow` permite sincronizar,
  sin autorizar consultas; `read` exige salud, intent habilitado y verificación completa.
  Los recibos pendientes bloquean lectura externa antes de aceptar caché o un manifiesto
  vacío. La memoria local permanece disponible sin Docker.
- **Lectura enrutada**: `consultar` exige procedencia y estado del episodio, aplica
  invalidaciones y devuelve rutas relativas bajo `docs/knowledge/`. El texto remoto se
  sanea y limita. `tipo` sale de la carpeta de taxonomía; `area`, de los tags del corpus.
  Una categoría no se convierte en tipo mediante equivalencias cableadas. El legado
  puede derivar carpeta de `source_path`, sin inventar un área ausente.
- **Ventanas**: `get_episodes` carece de cursor. La consulta amplía la ventana hasta
  resolver procedencia o alcanzar sus límites; lo no resuelto se cuenta como
  `fuera_de_ventana`. `verify` distingue `ok`, `incompleto`, `desfase` y `no_verificable`.
  Solo una verificación completa y sin desfase autoriza lectura externa. La comprobación
  limitada de manifiestos legacy no se convierte automáticamente en `verified_readback`.
- **Recursos**: `max_respuesta_kb` limita cada respuesta por lectura en bloques
  (predeterminado 8192 KiB); `max_episodes` limita la observación (predeterminado 5000).
  La consulta tiene además un máximo de 2000 episodios; `/doctor` impone una ventana
  diagnóstica de 200. Una ventana que no cabe conserva lo ya observado y se declara
  incompleta. Aumentar episodios sin ajustar el límite de respuesta no resuelve ese caso.
  El presupuesto de red se reparte entre IP y redirecciones, sin multiplicarlo.
- **Tope duro de `/doctor`** (C-09a): `health()` y `verify()` respetan cada uno su
  `timeout_ms`, pero se ejecutan uno tras otro (medido con un blackhole TCP: 4,02 s con
  `tope_ms` = 2000). `/doctor` corre la sonda en un hilo `daemon` y deja de esperar a
  `tope_ms` + `CAPACIDAD_MARGEN_MS` (500 ms); si no termina, la fila es ⚠️ «no comprobado».
  Por eso ambas funciones deben ser de SOLO LECTURA: el hilo abandonado sigue hasta que el
  proceso acaba y no debe dejar escrituras a medias.
- **Red**: se resuelven todos los hosts con nombre y se comprueban todas sus IP.
  Se rechazan credenciales embebidas, link-local, direcciones no especificadas y
  encapsulados 6to4/Teredo, incluso con `allow_remote`. Los IPv4 mapeados se normalizan.
  Solo se siguen 307/308, hasta tres saltos, comprobando cada destino; la sesión MCP
  no se reenvía si cambia esquema, host o puerto. Los errores remotos se sanean.
- **Configuración**: `provider.model` es obligatorio si `llm` no es `none`; no hay
  modelo predeterminado del proyecto. `episode_body_max_kb` limita el cuerpo enviado
  y devuelve aviso de truncado. `concurrency` está reservado; la publicación es secuencial.
  `telemetria` ajusta el entorno de este proceso, sin reconfigurar un servidor remoto.
  `router.default` está reservado; un rechazo sigue hacia búsqueda local.
- **Generaciones publicadas**: `graphiti_scope.py` resuelve el grupo lógico y el grupo
  físico confirmado sin activar descriptores pendientes. El adaptador vuelve a comprobar
  la selección bajo bloqueo antes de publicar; una selección obsoleta no se archiva ni
  resucita. `graphiti_rebuild.py` guarda snapshots y progreso, construye y verifica otro
  grupo antes del cambio publicado y conserva grupos anteriores o abandonados. Los UUID
  nuevos se vinculan al historial y los reintentos no reenvían solicitudes inciertas.
  Puede reparar pérdidas remotas desde copias propias vinculadas por identidad y hash
  o fuentes canónicas exactas; nunca inventa contenido histórico.
- **Grupos**: cambiar el grupo archiva el manifiesto anterior con nombre y huella
  propios, sin sobrescribir archivos ni revocar datos de otro grupo. Los envíos pendientes
  conservan endpoint y grupo; cambiar endpoint no permite adoptar silenciosamente su identidad.
- **Propuesta**: `proponer_config` ofrece tipos del servidor y mapa de taxonomía,
  sin aplicar cambios ni abrir red. El sincronizador llama a este contrato opcional
  sin conocer el tipo concreto del backend.

El plan recupera envíos retirados antes de confirmarse mediante `retire_submission`,
con nombre, grupo y hash vinculados al recibo propio. Solo una lectura exacta permite
confirmar su UUID y registrar una retirada por versión; la identidad retirada se conserva
en el manifiesto antes de podar el recibo. La incertidumbre mantiene cerrada la lectura externa.

`recover_transition` confirma intenciones registradas antes de enviar marcadores y
reconstruye su cuerpo remoto. Reutiliza relaciones confirmadas, conserva identidades
superadas y difiere operaciones dependientes tras un fallo. Un recibo no amplía el modo
de representación permitido por la configuración actual. El escritor del manifiesto
reutiliza `local-state.py`, sus comprobaciones de identidad y reintentos Windows acotados;
la publicación mantiene su presupuesto y cada manifiesto tiene un límite de 8 MiB.

`verify` incluye marcadores e identidades retiradas aunque no queden entradas vigentes.
Exige nombre único, grupo, UUID y contenido exactos; comprueba intención/hash antes de
abrir red y verifica las aristas históricas mediante consultas acotadas. Las ventanas
incompletas y respuestas fuera del grupo no autorizan lectura. `historico_verificado`
cuenta identidades históricas; `total` incluye las identidades vigentes e históricas esperadas.

Reconstrucción, historial y vínculo semántico de fuentes se comprobaron con fixtures
reales en un servidor compatible temporal. Siguen pendientes despliegue, workflows
nativos, utilidad comparativa y aceptación global. Las pruebas focales no los cierran.

`graphiti_provenance.py` vincula UUID nativos con las fuentes vigentes publicadas.
Un nombre coincidente de Entity no sustituye la pertenencia verificada. Un resultado
que cita UUID y nombre exactos del episodio publicado conserva su vínculo directo.
Los hechos modernos requieren referencias explícitas; todo texto extraído declara
falta de autoridad. IDs y rutas de origen se validan completos, con topes de 512 y
4096 caracteres, antes de normalizarlos; nunca se recortan para hacerlos admisibles.
Los hechos declaran episodios de origen; las entidades requieren pertenencia obtenida
con `get_episode_entities` por episodio. El vínculo exige grupo, UUID, contenido,
versión e ID coherentes. Referencias desconocidas, ambiguas o solo retiradas se descartan.
Las ventanas por UUID y la consulta de pertenencia están acotadas. Una consulta
incompleta, un límite o una fuente vigente no observada impiden atribuir procedencia
inequívoca a una entidad; los hechos verificados por separado se conservan. El texto extraído
declara contenido derivado, sin autoridad ni verificación de cada afirmación; no se
convierte automáticamente en conocimiento aprobado.

## Recuperación local compartida

`knowledge-find.py` usa el snapshot acotado de `knowledge-view.py` para legado
y aprobado. Este valida textos ya leídos mediante `knowledge-local.index_snapshot`,
sin cargar adaptadores. La CLI ordinaria declara `corpus_read` y solo conserva
la caché cuando el corpus es completo; `--view` y la consulta explícita del
panel no usan caché. Un fallo o una identidad ambigua conserva su diagnóstico.
La lectura por `--intent` mantiene la autorización del router y el respaldo
local con su motivo; estos límites no activan consultas externas.

## Adaptador de fixture (CA-12)

`evals/fixtures/knowledge-services/backend_test.py` implementa el contrato completo de forma
trivial (`type: "test"`) para que los tests de `knowledge-sync.py` demuestren que un backend nuevo
no toca el núcleo: se carga pasando su carpeta en `--backends-dir`, fuera del árbol real del
plugin.
