# APIs, fallos y datos durante un cambio

## Antes de escribir el endpoint

Conserva las convenciones que ya consumen los clientes. Elige estados HTTP por
semántica de operación, con errores de validación distinguibles de fallos
inesperados; documenta ambos en OpenAPI. Si existe un identificador de error
estable, úsalo para que el cliente no dependa del texto traducido. Devuelve un
identificador de correlación y registra el detalle redactado en el servidor.
Un wrapper `data` no mejora por sí mismo un contrato existente.

Autoriza sobre el recurso y su tenant en la consulta/servicio, además de
autenticar al usuario. Prueba cambiar el ID por el de otro usuario, permisos
retirados y acceso a objetos recién eliminados. Evita filtrar existencia mediante
mensajes cuando el contrato requiere ocultarla. CSRF y CORS no son controles de
autorización del recurso.

| Límite | Decisión que debe quedar explícita | Caso que descubre el defecto |
|---|---|---|
| Reintento de escritura | Clave de idempotencia ligada a identidad y contenido; unicidad y resultado durable | Dos solicitudes simultáneas con la misma clave, y misma clave con otro contenido |
| Transacción + servicio externo | No asumir atomicidad distribuida; outbox o compensación si el dominio lo exige | Commit local correcto y envío fallido; reintento tras caída |
| Paginación | Orden total estable; cursor incluye desempate y filtros; límites máximos | Inserciones concurrentes, claves repetidas y cursor inválido |
| Búsqueda/sort | Allowlist de campos y operadores; valores parametrizados | Nombre de columna inesperado y entrada con caracteres SQL |
| Serialización | Campos permitidos explícitos; paginar relaciones; revisar N+1 | Crece el número de filas sin crecer linealmente las consultas ocultas |
| Fallo de dependencia | Timeout, clasificación de error y retry limitado solo cuando sea seguro | Timeout después de aceptar la operación remota, sin duplicar efectos |
| Política de reintentos | Desactivada por defecto; reintentar solo errores clasificados como transitorios en operaciones idempotentes; un error determinista no se repite; un 429 se reintenta una vez como máximo respetando `Retry-After`; clasificar por estado antes de interpretar el cuerpo | Respuesta 400 o 422: una sola llamada. 429 con cuerpo HTML y `Retry-After`: espera ese plazo y no entra en bucle |
| Cuota o presupuesto por usuario | Reservar de forma atómica al aceptar la petición; el worker consume la reserva y la ajusta o libera al terminar, en vez de comprobar en la entrada y descontar en el worker | Dos peticiones simultáneas con cuota para una sola: solo se acepta una |
| Evento causado por la propia app | Reconocer y descartar los cambios que origina la app (actor, marca, rama propia) antes de reaccionar a un webhook | Un cambio publicado por la app no vuelve a disparar su propio flujo |
| Trabajo con coste por llamada | Comprobar que el resultado se podrá persistir (registro creado, destino accesible) antes de gastar; guardar el resultado de forma durable e idempotente | El destino falla antes de la llamada: no se gasta; un reintento no paga dos veces |
| Lectura en réplica | Leer lo propio tras escribir, comprobar permisos, flujos de pago y claves de idempotencia contra el primario; aceptar retraso solo donde el contrato lo tolera | Con retraso de replicación, el usuario ve su cambio recién guardado y la clave de idempotencia se encuentra |
| Interbloqueo | Orden de bloqueo determinista y ninguna llamada externa dentro de la transacción; reintentar la transacción completa con presupuesto acotado, nunca la última sentencia | Dos transacciones bloquean las mismas filas en orden inverso: una se reintenta entera y el saldo final cuadra |
| Webhook entrante | Verificar la firma sobre el cuerpo sin procesar antes de interpretarlo, con ventana de tiempo si el proveedor firma la marca; idempotencia por ID de evento; no depender del orden de entrega | Firma inválida rechazada sin parsear; mismo evento dos veces aplica un efecto; evento repetido fuera de ventana rechazado; evento antiguo tras uno nuevo no revierte el estado |
| Subida de ficheros | Límite de tamaño antes de leer el cuerpo; nombre y ruta generados por el servidor; almacenamiento fuera de la raíz servida; descarga con `Content-Disposition` y tipo fijado por el servidor. El tipo declarado por el cliente y los bytes mágicos son señales, no prueba de inocuidad | Fichero mayor que el límite rechazado sin leerlo entero; nombre con `../` o doble extensión no decide la ruta; un HTML o SVG subido no se ejecuta en el origen de la app |

## Caché, cerrojos y límites

Valen para cualquier almacén compartido (caché en memoria distribuida, base de
datos, broker). Un contador o un mapa por proceso no es un límite global ni un
cerrojo entre réplicas.

| Límite | Decisión que debe quedar explícita | Caso que descubre el defecto |
|---|---|---|
| Caché tras escritura | Invalidar tras el commit en vez de escribir el dato en la caché; clave con identidad y tenant | Dos escrituras concurrentes y una lectura entre el commit y la invalidación |
| Expiración de una clave caliente | Coalescer la recarga (cerrojo con TTL o expiración anticipada) | Muchas peticiones simultáneas en el instante en que expira |
| Cerrojo distribuido | Arrendamiento con dueño y token de valla que el recurso protegido comprueba | El trabajo dura más que el TTL y entra un segundo proceso |
| Límite de peticiones | Por identidad autenticada o por la IP real que entrega un proxy de confianza, nunca leyendo `X-Forwarded-For` directamente; almacén compartido entre réplicas | Cabecera `X-Forwarded-For` falsificada; dos réplicas con el mismo cliente |
| Cola con entrega al menos una vez | Consumidor idempotente y reclamación de los pendientes de un consumidor caído | El worker cae tras procesar y antes de confirmar |

Una cola no comparte almacén con una caché que expulsa claves por memoria: la
expulsión borraría trabajo pendiente.

## Migrar con lectores y escritores coexistentes

Describe qué versiones antiguas y nuevas convivirán. Para un cambio rompedor:
expandir esquema compatible → desplegar lectores/escritores compatibles → backfill
reanudable y verificable → comprobar adopción → contraer en otro despliegue.
No elimines columna/índice que use la versión que todavía puede ejecutarse.

Ensaya la migración con volumen representativo y la base real: bloqueos, duración,
índices, restricciones, permisos y espacio de disco. Una migración vacía en SQLite
no demuestra comportamiento de PostgreSQL/MySQL. Un down() que elimina datos
no equivale a recuperación; documenta rollback de aplicación, forward fix y
restauración verificada cuando proceda. El backfill debe tolerar corte y reintento.

Fuentes para el contrato aplicado: [HTTP semantics](https://www.rfc-editor.org/rfc/rfc9110),
[Problem Details](https://www.rfc-editor.org/rfc/rfc9457),
[PostgreSQL explicit locking](https://www.postgresql.org/docs/current/explicit-locking.html).
Verifica comportamiento en la versión del motor del proyecto antes de usar DDL.
