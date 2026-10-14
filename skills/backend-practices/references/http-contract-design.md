# Diseño de contratos HTTP

Léela solo cuando diseñes o cambies lo que ve un consumidor de una API HTTP:
métodos y estados, nombres, forma de la respuesta, paginación, filtros, cuotas,
versión o retirada. La estructura OpenAPI y su diff son de `api-contract`; los
límites de datos (idempotencia, cursor con desempate, allowlist de orden,
autorización por recurso) están en [contratos y datos](contracts-data.md) y aquí
no se repiten.

## Primero, el contrato que ya existe

Antes de proponer nada, lista qué convenciones consumen hoy los clientes:
nombres de rutas y campos, forma de los errores, paginación, formato de fechas
e identificadores. Un endpoint nuevo sigue esas convenciones aunque haya otra
«mejor»; cambiarlas es un cambio rompedor con su propio plan de migración. Las
alternativas de abajo sirven para decidir en un contrato nuevo o para justificar
una excepción, no para renombrar ni envolver respuestas por gusto.

## Métodos y estados

| Situación | Decisión | Caso que descubre el defecto |
|---|---|---|
| Lectura | `GET` sin efectos; los filtros van en la query | Un `GET` que cambia estado se repite al recargar o al reintentar un proxy |
| Reintento seguro | `PUT` y `DELETE` son idempotentes por definición; `POST` no lo es: si se reintenta, lleva clave de idempotencia (ver contratos y datos) | El cliente repite un `POST` tras un timeout y se crean dos recursos |
| Cuerpo ilegible | JSON mal formado se rechaza **antes** de validar el esquema, con su propio error (normalmente 400) | Un cuerpo truncado llega al validador y sale como error de campo o como 500 |
| Cuerpo legible pero inválido | 422 (sintaxis correcta, contenido no procesable) o 400, según la convención existente; un identificador de error estable por caso | El cliente distingue «JSON roto» de «campo inválido» sin leer el texto traducido |
| Conflicto con el estado actual | 409 con el motivo; para escrituras concurrentes, `If-Match` con ETag y 412 si no coincide | Dos clientes editan la misma versión: el segundo recibe 412, no pisa el cambio |
| Sin permiso o inexistente | 403/404 según el contrato de ocultación; la autorización se comprueba sobre el recurso | Cambiar el ID por el de otro tenant no devuelve el recurso ni confirma que existe |
| Límite superado | 429 con `Retry-After` cuando el servidor sabe el plazo | El cliente espera el plazo; no reintenta en bucle |
| Error inesperado | 500 sin detalle interno; identificador de correlación en la respuesta y detalle redactado en el log | La traza, la SQL o la ruta del servidor no aparecen en el cuerpo |

Si el proyecto no tiene formato de error, Problem Details (RFC 9457) es una
opción estándar; si ya tiene uno, se conserva.

## Forma de la respuesta y nombres

| Decisión | Opciones | Criterio |
|---|---|---|
| Envoltorio | Plano (el recurso es el cuerpo) o sobre (`data` + `meta`) | El sobre aporta sitio para metadatos de paginación o avisos; un `data` sin metadatos solo añade un nivel. Un contrato existente no se envuelve |
| Nombres de campos | `snake_case` o `camelCase` | El que ya use la API; mezclar ambos en un mismo contrato es un defecto |
| Rutas | Sustantivos en plural, anidación de un nivel cuando el hijo no existe sin el padre | Acciones que no son CRUD se nombran explícitas (`POST /pedidos/{id}/cancelar`) en vez de forzar un `PATCH` ambiguo |
| Campos dispersos | Parámetro de selección de campos con allowlist | Un campo no permitido se rechaza o se ignora según el contrato, nunca se proyecta a ciegas |
| Fechas e identificadores | Fecha con zona explícita; IDs grandes como cadena si un consumidor los lee como número de coma flotante | Un ID mayor que 2^53 llega intacto a un cliente JavaScript |

## Paginación y filtros

- **Offset** (`page`/`limit`): sencillo y permite saltar a una página; con
  inserciones concurrentes repite u omite filas y su coste crece con el
  desplazamiento.
- **Cursor**: estable bajo inserciones si el orden es total. El cursor es
  **opaco, no secreto**: codificarlo en base64 no impide leerlo ni manipularlo.
  Si su contenido no debe alterarse, se firma o se guarda en servidor; en
  cualquier caso, la autorización y los filtros se vuelven a aplicar con cada
  página, no se heredan del cursor.
- Un cursor creado con unos filtros u orden no se acepta con otros: error de
  validación, no resultados mezclados.
- Límite máximo por página declarado en el contrato; el valor lo fija el
  proyecto según su carga medida.
- Orden múltiple y filtros: allowlist de campos y operadores (contratos y datos,
  fila «Búsqueda/sort»).

## Cuotas y límites

El contrato declara **qué** se limita (identidad, recurso, operación), la
respuesta al superarlo (429, `Retry-After`) y si las escrituras rechazadas
tienen efectos. Las cifras (peticiones por minuto, ventanas) son política del
proyecto, no un valor universal; HTTP no define cómo identificar al cliente ni
cómo contar. El almacén compartido entre réplicas y la identidad real tras un
proxy están en contratos y datos, tabla «Caché, cerrojos y límites».

## Versionado y compatibilidad

| Cambio | Compatible con… | Nota |
|---|---|---|
| Campo de respuesta nuevo | Clientes tolerantes | No es compatible con un cliente que rechaza campos desconocidos (deserializador estricto, `additionalProperties: false` en su copia del esquema): pregunta a los consumidores |
| Campo de petición opcional nuevo | Todos | Su ausencia conserva el comportamiento anterior |
| Valor de `enum` nuevo en la respuesta | Clientes con rama por defecto | Rompe un `switch` exhaustivo del consumidor |
| Campo obligatorio nuevo, campo eliminado, tipo cambiado | Ninguno | Nueva versión o migración coordinada |

Versionar por ruta (prefijo `v2` en la URL), por cabecera o por tipo de medio son opciones
equivalentes en capacidad; se usa la que ya tenga la API. `--diff` de
`api-contract` señala los rompedores que detecta; no prueba que cada
consumidor siga funcionando.

## Retirada

1. Anuncia la retirada con `Deprecation` (RFC 9745): marca el recurso como
   obsoleto sin cambiar su comportamiento.
2. Si hay fecha prevista de baja, añade `Sunset` (RFC 8594), que no puede ser
   anterior a la de `Deprecation`, y un enlace `rel="sunset"` a la política o
   guía de migración.
3. `Sunset` es una indicación para el cliente: no obliga a responder 410 ni a
   apagar el recurso en esa fecha. Qué se responde después (410, redirección)
   es decisión del contrato y se documenta.
4. Mide el uso de la versión antigua antes de retirarla; el plazo (meses,
   número de versiones vivas) lo fija el proyecto.

## Checklist del contrato

- [ ] Errores: JSON mal formado, validación, conflicto, permiso y fallo
      inesperado distinguibles, sin detalles internos.
- [ ] Autorización probada sobre el recurso y el tenant, no solo el rol.
- [ ] Límite de tamaño del cuerpo y de página declarados.
- [ ] Paginación con orden total; cursor ligado a filtros y orden.
- [ ] Compatibilidad revisada con los consumidores reales, no solo con el diff.
- [ ] Retirada con `Deprecation`/`Sunset` y política enlazada, si aplica.
- [ ] Spec OpenAPI actualizada y validada con `api-contract` antes del código.

## Fuentes

Consultadas el 2026-10-14:
[RFC 9110 — HTTP Semantics](https://www.rfc-editor.org/rfc/rfc9110) (métodos
idempotentes §9.2.2, `If-Match` §13.1.1, 409 §15.5.10, 422 §15.5.21),
[RFC 6585 — 429 Too Many Requests](https://www.rfc-editor.org/rfc/rfc6585#section-4),
[RFC 9745 — Deprecation](https://www.rfc-editor.org/rfc/rfc9745),
[RFC 8594 — Sunset](https://www.rfc-editor.org/rfc/rfc8594),
[RFC 9457 — Problem Details](https://www.rfc-editor.org/rfc/rfc9457).
