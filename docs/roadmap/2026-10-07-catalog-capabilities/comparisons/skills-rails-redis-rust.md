# Rails, Redis y Rust — S226, S234, S241 y S242

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cuatro cuerpos completos: **53.789 bytes/1.880 líneas**, sin recursos locales.
[rails-redis-rust-reading-evidence.json](rails-redis-rust-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08.

## Decisión común

Ruby/Rails y Rust no tienen consumidor declarado: **no se abre especialidad**
en `stack-practices` (misma regla que Java, .NET y Go). Redis es distinto: no es
un stack sino infraestructura transversal, y su ciclo de vida de caché, cerrojos
y colas **no está** en `backend-practices`. Esta ficha cierra lo que dejó
pendiente [skills-django-queues-architecture.md](skills-django-queues-architecture.md)
(«S234 necesita su evaluación completa antes de cerrar solapes Redis») y el hueco
de caché que anotó [skills-iteration-backend-benchmarks.md](skills-iteration-backend-benchmarks.md).

## S234 — Patrones Redis

`11.977 bytes/404 líneas`. Estructuras, caché perezosa y de escritura,
invalidación por etiquetas, sesiones, límites de ventana fija y deslizante,
cerrojos `SET NX PX`, Pub/Sub y Streams, nombres de claves, TTL, pool,
Cluster, Sentinel y políticas de expulsión.

**Comparación.** `contracts-data.md` cubre idempotencia, outbox y fallo de
dependencia, pero no caché, cerrojos ni límites. **Destino:** una tabla
«Caché, cerrojos y límites» en `backend-practices/references/contracts-data.md`,
neutral de proveedor, con el mismo formato de sus filas:

| Límite | Decisión que debe quedar explícita | Caso que descubre el defecto |
|---|---|---|
| Caché tras escritura | Invalidar tras el commit en vez de escribir el dato; clave con identidad/tenant | Dos escrituras concurrentes y una lectura entre el commit y la invalidación |
| Expiración de una clave caliente | Coalescer la recarga (cerrojo con TTL o expiración anticipada) | Muchas peticiones simultáneas cuando expira |
| Cerrojo distribuido | Arrendamiento con dueño y token de valla que el recurso comprueba | El trabajo dura más que el TTL y entra un segundo proceso |
| Límite de peticiones | Identidad autenticada o IP real tras proxy de confianza (S223); almacén compartido entre réplicas | Cabecera `X-Forwarded-For` falsificada; dos réplicas |
| Cola con entrega al menos una vez | Consumidor idempotente y reclamación de pendientes tras caída | El worker cae tras procesar y antes de confirmar |

Defectos de la fuente:

| Ejemplo | Adaptación |
|---|---|
| Tabla «Bloom filter / HLL → HyperLogLog» | Un filtro de Bloom (pertenencia) no es HyperLogLog (cardinalidad) |
| Caché de escritura guarda el `data` del `UPDATE` y la tabla final la da por «consistencia fuerte» | Guarda el objeto parcial y, con dos escritores, el orden de los `setex` puede dejar el valor viejo |
| Script Lua de ventana deslizante con `key .. ':seq'` | Redis exige declarar en `KEYS` las claves que toca un script; además usa el reloj del cliente (desfase entre réplicas) en lugar del del servidor |
| `invalidate_category` borra varias claves en un solo `DELETE` | En Cluster falla si las claves caen en slots distintos |
| Cerrojo de 5 s para un pago, «TTL mayor que la duración esperada» | Sin token de valla, una pausa larga deja a dos procesos dentro |
| Consumidor de Streams que solo lee mensajes nuevos (`>`) | Los pendientes de un consumidor caído no se reclaman nunca; y `except Exception: pass` al crear el grupo oculta también errores de conexión |
| «Un solo Redis para todo → bases separadas» | Las bases numeradas comparten memoria y política de expulsión: cola con `noeviction` y caché con `allkeys-lru` necesitan instancias distintas |
| `_locks` por clave en memoria | Crece sin límite |

## S226 — Patrones Rails

`16.514 bytes/475 líneas`. Contrato de directorios, controladores delgados con
servicios que devuelven un resultado, objetos de formulario y de consulta,
jobs, ViewComponent, Hotwire y la pila Solid de Rails 8.

**Comparación.** Lo transversal ya está en `contracts-data.md` (idempotencia,
outbox, N+1); `dependency-upgrade` ya lee `Gemfile`. Correcciones para cuando
haya consumidor Ruby:

| Ejemplo | Adaptación |
|---|---|
| `Invoices::Overdue` con `where.not(id: Payment...pluck(:invoice_id))` | Carga todos los IDs pagados en memoria y genera un `NOT IN` enorme; con un `invoice_id` nulo, `NOT IN` no devuelve filas. Subconsulta o `NOT EXISTS` |
| Clave de idempotencia `invoice-export-<id>-<updated_at>` | Si la factura cambia entre reintentos, la clave cambia y la exportación se duplica, contra lo que afirma la propia pieza |
| Notificaciones tras el commit «registrando el fallo» | Si el proceso cae entre commit y encolado, se pierden: es el caso de la fila outbox |
| Umbrales «controlador > 80 líneas», «modelo > 200 líneas» | Sin medición; `code-health` informa tamaño sin imponer cifras |
| Remite a `rules/ruby/patterns.md` | Dependencia que no viaja con la pieza |

## S241 y S242 — Patrones y pruebas Rust

`13.500 bytes/500 líneas` y `11.798 bytes/501 líneas`. Propiedad y préstamo,
errores con `thiserror`/`anyhow`, enums exhaustivos, traits, concurrencia,
`unsafe`, módulos; pruebas unitarias, de integración, async, `rstest`,
`proptest`, `mockall`, doctests, Criterion y `cargo-llvm-cov`.

**Comparación.** `tdd/references/by-stack.md` ya tiene la fila `cargo`. Al
declararse un consumidor Rust habría que añadir `cargo-llvm-cov` a
`coverage-gate.py` y `Cargo.toml` a `deps-inventory.py`; hoy no lo leen.

| Ejemplo | Adaptación |
|---|---|
| `fetch_all` hace `panic!` si una tarea falla | Contradice «nunca `panic` en producción» de la misma pieza; y lanza una tarea por URL sin límite de concurrencia |
| `unsafe { slice.get_unchecked(index) }` «por el límite del bucle» | El bucle que justifica el invariante no aparece en el ejemplo |
| «Si compila, probablemente es correcto» | Contradice la razón de ser de S242 |
| `#[should_panic]` sobre `v[0]` y `sort_preserves_length` | Prueban la biblioteca estándar, no código propio (`tdd/references/anti-patterns.md`) |
| Mock de `mockall` con `User { id, name }` | El `User` definido antes en el mismo documento tiene `name` y `email`: no compila |
| Cobertura «lógica crítica 100 %, API pública 90 %» | Mismo criterio que S081: `tests.coberturaMinima` con herramienta oficial |

**Destino (S226, S241, S242):** anotación para una futura especialidad; **sin
especialidad ahora**.
