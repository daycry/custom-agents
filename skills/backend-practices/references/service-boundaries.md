# Límites de servicio en el backend

Léela solo cuando repartas un cambio backend entre transporte (controlador,
middleware), servicio y repositorio, o cuando revises código que cruza esas
capas. Los criterios de datos (N+1, transacción con servicio externo,
reintentos, límites de peticiones) están en [contratos y datos](contracts-data.md);
el diseño visible para el consumidor, en [diseño de contratos HTTP](http-contract-design.md).

## Qué decide cada capa

| Capa | Hace | No hace |
|---|---|---|
| Transporte (ruta, controlador, middleware) | Autentica, valida la forma de la entrada, traduce el resultado a estado HTTP | Reglas de negocio ni consultas directas |
| Servicio | Reglas de dominio, autorización sobre el recurso y el tenant, frontera transaccional | Conocer el formato HTTP o la sesión del framework |
| Repositorio | Consultas con columnas y orden explícitos; devuelve datos tipados | Decidir permisos o capturar errores para devolverlos como datos |

La autorización vive en el servicio aunque el controlador ya la compruebe: el
servicio también se invoca desde jobs, comandos o pruebas. Sigue el patrón de
inyección que ya use el proyecto; en CodeIgniter 4, ver
`skills/stack-practices/references/php-codeigniter.md`.

## Criterios y el caso que descubre el defecto

| Criterio | Decisión explícita | Caso que descubre el defecto |
|---|---|---|
| Interfaz completa | Todo método que el servicio llama está declarado en la interfaz o contrato del repositorio; un doble de prueba implementa esa interfaz entera | El servicio usa un método que la interfaz no declara: el doble no compila o la prueba pasa contra un método inexistente |
| Columnas explícitas | `SELECT` con la lista de columnas que el caso necesita; nunca `SELECT *` ni `select('*')` en código que alimenta una respuesta | Se añade una columna privada a la tabla y no aparece en la respuesta |
| Inserción explícita | `INSERT` con lista de columnas; nada de insertar un JSON o un array asociativo completo confiando en el orden de la tabla | Se reordena o añade una columna y la inserción falla o escribe en la columna equivocada |
| Orden declarado | Sentido (ascendente/descendente), desempate y tratamiento de valores ausentes escritos en el contrato del método | Dos elementos con la misma puntuación y uno sin puntuación salen en el mismo orden en cada llamada |
| Orden por un valor calculado | Precalcula un mapa clave→valor antes de ordenar en vez de buscar el valor dentro del comparador | Al duplicar los candidatos, el tiempo de ordenar crece mucho más del doble porque cada comparación recorre la lista |
| Resultado frente a transporte | El llamante comprueba el error del transporte **y** el resultado del dominio | Una función de base de datos que captura la excepción y devuelve `success: false` se trata como éxito porque la llamada no falló |
| Autenticación frente a negocio | El bloque que traduce errores a 401 envuelve solo la verificación de credenciales; el handler va fuera | Un fallo del handler (síncrono o una promesa rechazada) responde 500 o su error de dominio, nunca 401 |
| Token verificado | Algoritmos permitidos fijados por el servidor, `iss` y `aud` comprobados, claims validados en ejecución; un tipo estático sobre el payload no valida nada | Token firmado por otro emisor o para otra audiencia rechazado; claim con tipo inesperado rechazado |
| Errores con contexto | Logs estructurados con identificador de correlación; el contexto que añade el llamante no sobrescribe campos de control (nivel, correlación, marca de tiempo) | Un contexto con clave `level` o `request_id` no cambia esos campos; un email o una traza no se copian sin redactar |

## Funciones de base de datos

Una función o procedimiento con manejador de excepciones no es transparente:
en PostgreSQL, un bloque PL/pgSQL con `EXCEPTION` deshace los cambios de ese
bloque y continúa, así que el llamante ve una llamada correcta. Si la función
devuelve un indicador de fallo en vez de propagar el error, ese indicador forma
parte del contrato y se comprueba en cada llamante, con un caso que fuerce el
fallo. Además, un bloque con `EXCEPTION` es más caro de entrar y salir: úsalo
solo cuando haga falta.

## Pruebas por capa

| Capa | Prueba | Qué demuestra |
|---|---|---|
| Servicio | Doble del repositorio que implementa la interfaz completa; reloj, red y correo aislados | Reglas de dominio y autorización, con éxito y cada fallo |
| Repositorio | Motor real con estado restaurable | Columnas, orden, desempate y restricciones; SQLite no sustituye al motor de producción |
| Transporte | Petición completa por la ruta y sus filtros | JSON mal formado, 401 frente a error de negocio, promesa rechazada, forma del error |

Los ejemplos de un SDK concreto (cliente de base de datos, librería de tokens,
framework) se escriben contra la versión bloqueada en el proyecto; ninguno es
obligatorio.

## Fuentes

Consultadas el 2026-10-14:
[PostgreSQL 18 — Trapping Errors en PL/pgSQL](https://www.postgresql.org/docs/18/plpgsql-control-structures.html#PLPGSQL-ERROR-TRAPPING),
[RFC 8725 — JWT Best Current Practices](https://www.rfc-editor.org/rfc/rfc8725)
(§3.1 verificación del algoritmo, §3.8 emisor, §3.9 audiencia).
