# Migraciones de base de datos: bloqueos, estado y backfill

Léela solo cuando escribas o revises una migración de esquema o datos sobre
una base con tráfico. El orden expandir → compatibilidad → backfill → adopción
→ contraer, el ensayo con el motor real y la diferencia entre `down()` y
recuperación están en [contratos y datos](contracts-data.md), sección «Migrar
con lectores y escritores coexistentes», que sigue siendo el contrato común;
esto añade lo que cambia por motor y por runner. Todo dato de abajo es de la
versión indicada: comprueba la del proyecto antes de aplicar DDL.

## Bloqueos en PostgreSQL 18

| Operación | Bloqueo y efecto | Cómo hacerla con tráfico |
|---|---|---|
| `ALTER TABLE` (por defecto) | `ACCESS EXCLUSIVE` salvo que la subforma diga otra cosa: bloquea incluso los `SELECT`. Con varias subórdenes, se toma el más estricto | Una subforma por sentencia cuando sus bloqueos difieren; `SET LOCAL lock_timeout` en la transacción del DDL para que falle pronto en vez de esperar indefinidamente detrás de una transacción larga |
| `ADD COLUMN` nullable o con `DEFAULT` no volátil | No reescribe la tabla (el default se guarda en metadatos), pero **sigue tomando `ACCESS EXCLUSIVE`**: rápido no es «sin bloqueo» | Igual que arriba; un `DEFAULT` volátil (p. ej. `clock_timestamp()`) reescribe tabla e índices |
| `SET NOT NULL` | Recorre la tabla entera bajo el bloqueo, salvo que un `CHECK (col IS NOT NULL)` válido lo demuestre | `ADD CONSTRAINT … CHECK (…) NOT VALID` → `VALIDATE CONSTRAINT` (toma `SHARE UPDATE EXCLUSIVE`) → `SET NOT NULL` |
| Restricción o clave foránea nueva | La mayoría de `ADD CONSTRAINT` toman `ACCESS EXCLUSIVE`; `ADD FOREIGN KEY` toma `SHARE ROW EXCLUSIVE` en ambas tablas | `NOT VALID` al añadirla y `VALIDATE CONSTRAINT` en otra transacción |
| `CREATE INDEX` | `SHARE`: bloquea escrituras, no lecturas, hasta terminar | `CREATE INDEX CONCURRENTLY` (`SHARE UPDATE EXCLUSIVE`) |
| `CREATE INDEX CONCURRENTLY` | No puede ir dentro de un bloque de transacción; espera a las transacciones existentes; si falla deja un índice `INVALID` que no se usa pero sí cuesta en cada escritura (y, si es único, sigue imponiendo unicidad) | Fuera de la transacción del runner; tras un fallo, `DROP INDEX` y repetir, o `REINDEX INDEX CONCURRENTLY` |
| `… IF NOT EXISTS` | Solo compara el **nombre**: no garantiza que el índice existente se parezca al que se iba a crear | Tras una ejecución parcial, comprueba definición y validez del índice, no solo que exista |

`statement_timeout` y `lock_timeout` no se fijan en `postgresql.conf`: la
documentación lo desaconseja porque afectaría a todas las sesiones, incluidas
migraciones y backfills largos. Fíjalos por rol, sesión o transacción.

## Bloqueos en MySQL 8.4 y MariaDB

| Aspecto | Comportamiento documentado | Consecuencia para la migración |
|---|---|---|
| Algoritmo | MySQL 8.4 usa `INSTANT` por defecto cuando la operación lo admite (añadir columna en cualquier posición, con límites: tamaño de fila, 64 versiones de fila por tabla, tablas `COMPRESSED` o con `FULLTEXT`) | Declara `ALGORITHM=INSTANT` o `INPLACE` explícito: si la operación no lo admite, la sentencia falla en vez de degradar a una copia lenta |
| `LOCK` | `NONE` permite lecturas y DML; `SHARED` solo lecturas; `EXCLUSIVE` nada. Pedir un nivel menos restrictivo del que la operación permite da error | Declara `LOCK=NONE` cuando el tráfico no admite bloqueo; el error es la señal para replanificar |
| Índice secundario | En sitio, con DML concurrente; termina cuando acaban las transacciones que acceden a la tabla | Medir duración con volumen real |
| `NULL`/`NOT NULL` | Reconstruye la tabla en sitio (caro); `NOT NULL` falla si hay nulos y exige modo SQL estricto | Backfill previo y verificación de nulos antes del cambio |
| Bloqueo de metadatos | El DDL en línea necesita un bloqueo exclusivo de metadatos al empezar y al confirmar; espera a transacciones abiertas sobre la tabla, y **mientras espera bloquea las transacciones posteriores** | Una transacción larga u olvidada detiene la tabla entera; ejecuta con un tiempo de espera de bloqueo corto y reintenta |
| Commit implícito | `ALTER TABLE`, `CREATE INDEX`, `CREATE/DROP TABLE` confirman la transacción en curso: una migración con varios DDL no es atómica | Un fallo a mitad deja el esquema medio aplicado (ver «Estado a medias») |
| MariaDB | Admite `ALGORITHM` (`INSTANT`, `NOCOPY`, `INPLACE`, `COPY`) y `LOCK` con error si no se pueden cumplir; el soporte por operación difiere de MySQL | No copies la tabla de MySQL: comprueba cada operación en el manual de la versión instalada |

## Defaults durante la convivencia

- Mientras conviven versiones, el escritor antiguo no envía la columna nueva:
  necesita `DEFAULT` en la base o columna nullable. Un default solo en la
  aplicación nueva deja nulos en las filas que escribe la vieja.
- Default del esquema y default de la aplicación deben coincidir; si
  divergen, el valor depende de qué versión escribió la fila.
- Un default volátil o calculado se rellena por backfill, no en el `ALTER`.

## Estado a medias («dirty»)

Un runner registra la versión aplicada **después** de ejecutar la migración.
Si falla a mitad:

- En PostgreSQL con la migración dentro de una transacción, el DDL se deshace
  (salvo `CONCURRENTLY` y lo ejecutado en bloques sin transacción).
- En MySQL/MariaDB, cada DDL ya confirmó: el esquema queda medio aplicado y
  la versión no registrada; reintentar falla con «ya existe».

Procedimiento: inspecciona el esquema real y los datos afectados, repara o
completa a mano lo pendiente con una migración correctiva revisada, y solo
entonces registra la versión. Marcar la versión como aplicada (un `force` o
editar la tabla de historial) cambia metadatos, no repara datos.

## Contrato del backfill

| Punto | Decisión | Caso que descubre el defecto |
|---|---|---|
| Lotes | Por rango de clave con tamaño acotado; checkpoint persistido tras el commit de cada lote | Caída tras el commit y antes del checkpoint: el lote se repite sin duplicar efectos |
| Escritores antiguos | La compatibilidad (doble escritura o trigger) se despliega **antes** del backfill; al terminar, reconciliar las filas escritas durante el proceso | Una fila creada por la versión vieja durante el backfill queda sin rellenar y se detecta antes de contraer |
| Filas que no progresan | Entradas que no se pueden transformar se marcan con motivo; el predicado de «pendiente» no las vuelve a elegir | El backfill termina con un recuento de no transformables, no en bucle infinito |
| `SKIP LOCKED` | Cero filas devueltas significa «nada disponible ahora», no «terminado»: puede haber filas bloqueadas. MySQL documenta que da una vista inconsistente, válida para tablas tipo cola | La terminación se decide con una consulta sin `SKIP LOCKED` sobre el predicado de pendientes |
| Commits dentro de SQL | En PostgreSQL, `COMMIT` dentro de `DO` o de un procedimiento solo funciona en una llamada de nivel superior y fuera de bloques con `EXCEPTION`; dentro de la transacción del runner no hay commit por lote | El lote se controla desde la aplicación o se verifica cómo invoca el runner |
| Carga | Pausa entre lotes y vigilancia del retraso de réplicas | El retraso de la réplica no supera lo que tolera el contrato de lectura |
| Verificación | Consulta de pendientes = 0 y reconciliación antes de contraer | Contraer con filas pendientes queda bloqueado por el plan |

## Configuración del motor y colas

| Ejemplo frecuente | Corrección |
|---|---|
| `ALTER SYSTEM SET max_connections = …` seguido de `pg_reload_conf()` | `max_connections` solo cambia al reiniciar el servidor; recargar no basta |
| `statement_timeout` global | También corta migraciones y backfills; por rol, sesión o transacción |
| Cola con `UPDATE … SET status = 'processing' … FOR UPDATE SKIP LOCKED` | Un worker que cae deja el trabajo en `processing` para siempre: plazo de reclamación y proceso idempotente (contratos y datos, «Cola con entrega al menos una vez»); en MySQL, índice sobre las columnas del filtro para no bloquear más filas de las necesarias |

## Runners de los stacks del plugin

| Runner | Qué tener en cuenta |
|---|---|
| CodeIgniter 4 (`php spark migrate`, `migrate:status`, `migrate:rollback -b <lote>`) | El historial vive en la tabla `migrations` por lote; el runner registra cada migración al completarla y no la envuelve en una transacción: con MySQL, un fallo a mitad deja el estado a medias descrito arriba. La opción `lock` evita migraciones concurrentes entre procesos. `migrate:rollback` ejecuta los `down()`: no es una restauración de datos |
| Alembic (Python) | Envuelve las migraciones en una transacción si el dialecto admite DDL transaccional; `transaction_per_migration=True` da una por fichero. Para DDL que debe ir fuera de transacción (p. ej. `CREATE INDEX CONCURRENTLY`), `op.get_context().autocommit_block()`, que **confirma antes** todo lo anterior. `alembic upgrade <rev> --sql` genera el SQL para revisarlo sin tocar la base |

Otros runners (de otros lenguajes u ORM) se consultan en su documentación de la
versión instalada cuando un proyecto los declare.

## Fuentes

Consultadas el 2026-10-14:
PostgreSQL 18 — [ALTER TABLE](https://www.postgresql.org/docs/18/sql-altertable.html),
[CREATE INDEX](https://www.postgresql.org/docs/18/sql-createindex.html),
[bloqueo explícito](https://www.postgresql.org/docs/18/explicit-locking.html),
[timeouts de cliente](https://www.postgresql.org/docs/18/runtime-config-client.html),
[conexiones](https://www.postgresql.org/docs/18/runtime-config-connection.html),
[transacciones en PL/pgSQL](https://www.postgresql.org/docs/18/plpgsql-transactions.html);
MySQL 8.4 — [operaciones DDL en línea](https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-operations.html),
[rendimiento y concurrencia del DDL en línea](https://dev.mysql.com/doc/refman/8.4/en/innodb-online-ddl-performance.html),
[commit implícito](https://dev.mysql.com/doc/refman/8.4/en/implicit-commit.html),
[lecturas con bloqueo](https://dev.mysql.com/doc/refman/8.4/en/innodb-locking-reads.html);
MariaDB — [ALTER TABLE](https://mariadb.com/docs/server/reference/sql-statements/data-definition/alter/alter-table);
CodeIgniter 4.7.5 — [migraciones](https://codeigniter.com/user_guide/dbmgmt/migration.html)
y `system/Database/MigrationRunner.php` del repositorio oficial;
Alembic 1.20 — [runtime](https://alembic.sqlalchemy.org/en/latest/api/runtime.html),
[modo offline](https://alembic.sqlalchemy.org/en/latest/offline.html).
