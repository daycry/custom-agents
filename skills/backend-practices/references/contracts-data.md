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
