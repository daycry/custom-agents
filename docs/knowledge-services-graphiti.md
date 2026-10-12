# Publicación y recuperación de Graphiti

[English](en/knowledge-services-graphiti.md) · **Español**

La memoria canónica vive en `docs/knowledge/approved/`. Graphiti es una proyección
opcional: una caída, una confirmación pendiente o una lectura rechazada conserva
la búsqueda local. El plugin no activa servicios ni migra grafos automáticamente.

## Creación y confirmación

Un episodio nuevo se envía sin UUID. El servidor asigna su identidad; la respuesta
de encolado no prueba que el episodio esté guardado. El adaptador confirma nombre,
grupo, contenido y UUID mediante `get_episodes` antes de publicarlo en el manifiesto.

El manifiesto guarda `binding: verified_readback` y `episode_body_sha256`. El hash
corresponde al cuerpo enviado, incluyendo procedencia e instrucciones del proveedor.
Los manifiestos antiguos conservan su comprobación limitada y no reciben este sello
mediante una migración automática.

Los recibos de envío viven en `.claude/knowledge-services/graphiti-submissions/`, con
marcador de propietario y bloqueo compartido. Sus fases son `submitting`, `submitted`
y `confirmed`. Una respuesta perdida conserva la incertidumbre: el reintento busca
la publicación existente y no vuelve a enviarla automáticamente.

El diario admite 128 operaciones en total, incluyendo episodios y relaciones, y
256 KiB de estado. El bloqueo serializa a los clientes que lo respetan; no autentica
al servidor ni garantiza entrega exactamente una vez. Una instalación parcial debe
incluir `agent-kits/shared/local-read.py` y `agent-kits/shared/local-state.py`.

## Sucesión y retirada

La sucesión confirma `<id>@<version>@superseded`; la retirada confirma
`<id>@<version>@withdrawn`. Cada marcador conserva la identidad remota de la versión
afectada. Retirar la versión 1 permite aprobar después la versión 2. Los marcadores
antiguos `<id>@tombstone` mantienen su significado histórico de invalidación completa.

Una operación encolada se vincula a su grupo. Una retirada incluye también versión,
UUID real y hash. Los reintentos de versiones superadas, retiradas o de otro grupo
se omiten y se cuentan como `omitidos_obsoletos`. Cambiar el contenido de una versión
ya publicada exige incrementarla; una retirada sin identidad vinculada se rechaza.
La identidad real retenida permite retirar una versión que dejó de aparecer en la
ventana de observación del manifiesto pendiente.

## Recuperación de envíos retirados

Si una entrada desaparece de `approved/` antes de confirmar su publicación, el plan
local incluye `retire_submission`, vinculado al nombre, grupo y hash del cuerpo enviado.
Planificar esta recuperación no abre red, crea archivos ni vuelve a enviar el episodio.
Una entrada que sigue aprobada conserva su operación ordinaria de publicación.

La ejecución busca el episodio del recibo propio y comprueba su contenido y UUID.
Si no puede confirmarlo, conserva el recibo pendiente y falla con diagnóstico; no
interpreta una ausencia en la ventana como prueba de que el envío nunca ocurrió.
Tras confirmarlo, registra su retirada por versión sin hacerlo vigente. El marcador
publicado conserva `retired_episode` con nombre, UUID y hash del cuerpo, y solo entonces
se puede retirar el recibo de envío. `retirados_pendientes` cuenta estas recuperaciones.

Un corte antes del commit conserva los recibos confirmados; la siguiente ejecución
reutiliza episodio y marcador. Una retirada antigua no elimina una generación nueva.
Los marcadores guardan su intención antes del envío: versión afectada, UUID de origen,
reemplazo cuando corresponda, referencias y representación. `recover_transition` adopta
ese evento solo después de confirmar el episodio y reconstruir exactamente su cuerpo.
Recupera primero el marcador; después puede retirar una versión abandonada o confirmar
la versión nueva que sigue aprobada. Las identidades históricas permanecen en el manifiesto.

Si la confirmación o una relación quedan pendientes, se difieren las operaciones posteriores
de esa misma entrada; otras entradas conservan su progreso independiente. La recuperación
respeta la configuración actual: un recibo no puede habilitar aristas directas desactivadas.
Cambiar representación durante una operación pendiente requiere resolución explícita;
no se convierte ni se reenvía automáticamente. Los recibos antiguos sin intención registrada
mantienen el diagnóstico pendiente y no reciben una intención inventada.

Una sucesión confirmada no se deshace volviendo al mismo número de versión: utiliza una
versión nueva para una aprobación posterior.

## Representación de las relaciones

`transition_relations` admite dos valores:

| Valor | Comportamiento |
|---|---|
| `episode` (predeterminado) | Guarda `relation: SUPERSEDES`, referencias de origen y destino y UUID de procedencia dentro del marcador confirmado del grupo propio. No llama a `add_triplet`. |
| `triplet` | Añade una arista entre entidades de referencia y confirma grupo, nombres, hecho y UUID mediante búsquedas acotadas. Requiere que el operador haya comprobado el aislamiento de escritura del servidor. |

La representación `episode` conserva la relación documental y permite invalidación
determinista; no promete una arista tipada creada por el modelo. En `triplet`, los
UUID de episodios no se pasan como UUID de entidades. Una respuesta perdida de
`add_triplet` se recupera buscando la arista existente, sin reenvío automático.

La firma de una herramienta con `group_id` no demuestra aislamiento físico. En el
servidor inspeccionado con graphiti-core 0.30.1, `add_triplet` usa el cliente compartido
y el SDK escribe mediante su driver actual. La ingesta de episodios puede cambiar
ese driver a otro grupo. Esta ruta no debe habilitarse por defecto en FalkorDB.
No se modificaron contenedores ni datos para obtener esta evidencia de código.

## Extracción de los marcadores de control

Sucesión y retirada envían `previous_episode_uuids: []` y una instrucción que identifica
el episodio como registro de control, sin nuevas entidades de dominio. Los identificadores
son referencias opacas. Estos parámetros no se aplican a las entradas de conocimiento.

El marcador excluye siempre el tipo estándar `Entity`. Si el servidor declara tipos
personalizados, configura `transition_excluded_entity_types` con todos sus nombres.
La lista admite hasta 128 nombres imprimibles de 1 a 256 caracteres; se eliminan
duplicados y se conserva una ordenación estable. Por ejemplo, un servidor que declare
un tipo `Document` necesita incluir ese nombre. El plugin no inventa ni descubre tipos
personalizados mediante `get_status`, cuyo contrato no los expone.

La exclusión actúa antes de crear los nodos y validar sus atributos en el SDK comprobado.
Evita que un marcador de retirada intente completar, por ejemplo, atributos obligatorios
de una organización. El SDK sigue invocando el modelo para la extracción inicial: no es
una API de ingesta sin modelo ni una garantía de disponibilidad. Un tipo excluido que
el servidor no reconozca puede provocar un fallo asíncrono; comprueba los nombres antes
de habilitar la proyección y mantén la confirmación por lectura.

## Grupo lógico y generación publicada

El proyecto conserva su `group_id` lógico en la configuración. Un descriptor publicado
puede declarar `logical_group_id` y un grupo físico de generación. Solo se acepta una
generación cuyo nombre esté ligado al hash del grupo lógico y a un nonce hexadecimal
de 32 caracteres; un grupo de otro proyecto no se adopta. Un descriptor pendiente,
incompleto, ambiguo o con un componente de ruta inseguro no activa una generación.

Planificación, publicación, retirada, salud, verificación y consulta resuelven esa
selección desde el manifiesto publicado sin modificar la configuración del usuario.
La publicación vuelve a comprobarla después de adquirir su bloqueo: un cambio concurrente
aborta antes de archivar o volver a publicar una generación obsoleta. Los helpers de
código se reutilizan dentro del proceso; los datos del descriptor se leen de nuevo.

`rebuild` construye y verifica un grupo nuevo antes de cambiar el manifiesto publicado.
Conserva el grupo anterior y su historial; no vacía ningún grupo. Los UUID nuevos se
vinculan a las versiones y retiradas. Repetir una solicitud confirmada reutiliza la
generación; si pierde datos remotos, puede reconstruirlos desde copias propias vinculadas
por identidad y hash o, para documentos vigentes, desde la fuente canónica exacta.

El coordinador guarda contenido, intención y progreso en
`.claude/knowledge-services/graphiti-rebuild.json`; cada generación tiene estado propio
bajo `.claude/knowledge-services/graphiti-generations/<nonce>/`. Los recibos permiten
observar un envío interrumpido sin reenviarlo. Una publicación activa pendiente, un
episodio ajeno o una ventana incompleta impiden construir. No se inventa contenido histórico.

Si cambia el corpus, la extracción o la publicación activa entre intentos, archiva el
descriptor anterior y prepara otra generación. Conserva los grupos abandonados y sus
recibos inciertos; no cancela trabajos del servidor ni elimina datos automáticamente.
Cambiar endpoint o grupo lógico exige resolver o archivar la identidad anterior.

Cada descriptor tiene un límite de 8 MiB; la ventana remota conserva sus topes y las
escrituras comparten un presupuesto temporal. Agotar un límite conserva la publicación
anterior. La aceptación con el servicio real y los recorridos nativos sigue pendiente.

## Verificación del historial publicado

`verify` comprueba las entradas vigentes, los marcadores y las identidades retiradas
que conservan esos marcadores. Cada identidad histórica exige nombre único, grupo,
UUID y hash exacto del contenido. Un manifiesto sin entradas vigentes sigue verificando
su historial; no autoriza lectura por estar vacío. `historico_verificado` cuenta los
episodios históricos confirmados, incluyendo versiones retiradas.

Antes de abrir red, se valida la intención del marcador y se reconstruye su cuerpo
para comprobar el hash declarado. Una versión vigente no puede contradecir una
invalidación ya registrada. En representación `triplet`, se verifica además la arista
con sus UUID de origen y destino mediante búsquedas del grupo propio y presupuesto acotado.

Los nombres duplicados o las respuestas fuera del grupo solicitado mantienen cerrada
la lectura. Una ventana incompleta devuelve `incompleto`, no éxito; `total` incluye
todas las identidades que debía comprobar. La comprobación no crea archivos, recupera
envíos, reindexa ni publica datos. Un historial incompatible mantiene su diagnóstico;
no se le inventan intenciones o identidades.

## Lectura y mantenimiento

`off` evita conexiones y rechaza escrituras; `shadow` permite publicación y comprobación
sin autorizar consultas; `read` exige salud, permiso del intent y verificación completa.
Los recibos sin confirmar o confirmados sin commit bloquean la lectura externa antes
de aceptar resultados cacheados o un manifiesto vacío. La observación no crea estado,
abre bloqueos, recupera operaciones ni llama al servidor.

El manifiesto pendiente conserva progreso por operación. Si falla una publicación,
pueden existir episodios ya persistidos: no se promete rollback global. El sincronizador
drena su outbox antes de calcular el objetivo nuevo; un fallo no elimina la memoria local.

El manifiesto usa el escritor compartido de estado, con temporales exclusivos y
comprobación de identidad del destino. Reintenta solo los errores Windows 5, 32 y 33,
hasta cuatro intentos con esperas de 20/40/80 ms, mientras conserva esa identidad.
El límite de cada manifiesto es 8 MiB; el diario de recibos mantiene su límite de 256 KiB.
La escritura dentro de una publicación conserva su presupuesto temporal. Estas comprobaciones
cooperativas no equivalen a un intercambio condicionado atómico frente a cualquier escritor.

La reconstrucción, verificación histórica y vinculación semántica de fuentes pasaron
las fixtures acotadas del servidor compatible descritas abajo. Los workflows nativos,
la utilidad comparativa de recuperación y la QA global siguen pendientes.


La reconstrucción se comprobó contra una instancia aislada de la revisión oficial
0a3b1711b018e5590cf5c44a3ee3e67d6733ee13, con graphiti-core 0.30.2 y MCP 2.2.0.
El despliegue instalado 0.30.1 falla al leer varios grupos: los datos siguen guardados,
pero get_episodes consulta el último grafo usado. Se requiere enrutado por grupo compatible.
El adaptador enlaza los UUID de `episodes` de los hechos con identidades publicadas;
para entidades usa `get_episode_entities` por un único episodio vigente cada vez.
Exige grupo, UUID, hash del contenido, versión e ID coherentes con el manifiesto.
Las referencias desconocidas, ambiguas o solo retiradas se descartan. Una referencia
nativa inválida no permite usar el nombre de la entidad como alternativa.

La ventana de episodios se amplía también por UUID dentro de los topes configurados.
La pertenencia de entidades queda limitada a 20 episodios y 500 nodos por respuesta,
con presupuesto temporal. Un fallo de esa consulta conserva los hechos cuyo vínculo
se haya verificado independientemente y devuelve diagnóstico.

Los resúmenes y hechos extraídos son contenido derivado: `contenido_derivado: true`,
`autoridad: ninguna`, `verificacion: no_verificada` y `citas_por_afirmacion: false`.
El estado y la evidencia describen la fuente aprobada; no aprueban el texto generado
ni acreditan cada afirmación. Tras el cambio, un servidor temporal compatible recuperó
la versión vigente mediante consultas ordinarias, de hechos y de entidades. Respuestas
parciales de pertenencia, presupuesto agotado o fuentes vigentes no observadas no
establecen procedencia inequívoca de una entidad. El servicio original se conservó;
despliegue, workflows nativos, utilidad comparativa y aceptación global siguen abiertos.


El lector compartido conserva las etiquetas de contenido derivado y el UUID de origen
en JSON. La salida compacta empieza por «derivado sin autoridad», incluso al abreviar
identidades largas. ID y ruta dentro de sus límites permanecen exactos en JSON; una
identidad insegura o incoherente se descarta en vez de transformarse. El estado aprobado
describe la fuente, no el texto extraído. Los briefs compactos conservan esa distinción.


Si falla un envío inicial, el recibo propio conserva la clase del error y un
diagnóstico saneado y redactado de hasta 500 caracteres. El reintento conserva esa
causa al informar de confirmación pendiente; no autoriza otro envío. Los campos de
diagnóstico son opcionales en recibos anteriores y se validan antes de reutilizarlos.


El nombre de una Entity no establece procedencia en una publicación moderna. Se exige
UUID y nombre exactos del episodio confirmado o pertenencia de Entity verificada. Los
hechos modernos requieren referencias explícitas de episodios. Todo texto extraído
conserva etiquetas derivadas, incluso en formato legado. La planificación rechaza
versiones previas inválidas. ID hasta 512 caracteres y ruta hasta 4096 se validan
completos: los valores inseguros o excesivos se descartan antes de normalizarse y los
seguros no se recortan. No se ocultan traversal ni controles tras un tope de presentación.


El adaptador final se volvió a probar en el servidor compatible temporal tras corregir
identidades y nombres de Entity: consulta ordinaria, de hechos y de entidades recuperó
la versión 2, con tres creaciones y dos identidades históricas verificadas. Se retiraron
los grafos y la instancia propios. Utilidad comparativa, workflows de clientes nativos
y QA global siguen pendientes; el servicio existente no se actualizó.
