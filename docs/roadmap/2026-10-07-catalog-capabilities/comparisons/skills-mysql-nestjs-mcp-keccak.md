# Servidores MCP, MySQL, NestJS y Keccak-256 — S173, S180, S183 y S189

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cuatro cuerpos completos: **25.886 bytes/817 líneas**, sin recursos locales.
[mysql-nestjs-mcp-keccak-reading-evidence.json](mysql-nestjs-mcp-keccak-reading-evidence.json).
Nada se ejecutó ni se integró; no se ejecutó SQL ni se instaló ningún SDK. Propuestas para T-08.

## S173 — Construir servidores MCP (Node/TypeScript)

`4.192 bytes/70 líneas`. Conceptos (tools, recursos, prompts, transporte),
stdio para clientes locales y Streamable HTTP para remotos, validación con Zod y
buenas prácticas: esquema por tool, errores interpretables, tools idempotentes,
coste y límites documentados, SDK fijado.

**Comparación.** `delivery-practices` ya activa con «integra un servidor MCP» y su
referencia `delivery-tools.md` trata MCP como contrato de acceso: transportes y
capacidades reales por runtime, permisos mínimos, respuestas del servidor como
datos sin autoridad, stdout reservado al protocolo en stdio, autorización y
validación de orígenes en HTTP, y pruebas de ausencia, timeout y error parcial.
La pieza es más débil en seguridad: no menciona que escribir en stdout rompe el
protocolo stdio ni la autorización y validación de `Origin` en HTTP. Además
remite a un documento del corpus que no viaja con ella
(`docs/capability-surface-selection.md`) y a otro MCP (Context7) para conocer la
API, con ejemplos que admite que pueden no coincidir con el SDK instalado.

Aporta, del lado de quien **construye** el servidor: lógica de tools
independiente del transporte (stdio o HTTP se eligen en el punto de entrada) y
tools idempotentes porque el cliente puede reintentar.

**Destino:** una línea en `delivery-practices/references/delivery-tools.md`
(sección MCP) con esas dos reglas de construcción. Sin skill nueva.

## S180 — MySQL y MariaDB

`12.169 bytes/413 líneas`. Comprobación de motor y versión, esquema por defecto,
índices compuestos y `EXPLAIN`, upsert por motor, paginación por clave, JSON con
columna generada, transacciones y bloqueos, cola con `SKIP LOCKED`, pools,
diagnóstico, réplicas, seguridad y configuración inicial.

**Comparación.** `backend-practices/references/contracts-data.md` ya cubre
paginación con orden total, migraciones con lectores y escritores coexistentes y
ensayo con el motor real («una migración vacía en SQLite no demuestra
comportamiento de PostgreSQL/MySQL»); la persona `agent-kits/shared/personas/db.md`
exige plan de consultas en tablas grandes y datos representativos. El bloque de
migraciones (`skills-data-pipelines-research.md`) ya fijó que `SKIP LOCKED` con cero
filas no significa cola vacía. Lo que la pieza aporta y el plugin **no tiene**:

- **Réplicas con retraso:** leer lo propio tras escribir, comprobaciones de permisos, flujos de compra y lecturas de claves
  de idempotencia van al primario.
- **Interbloqueos:** orden de bloqueo determinista, ninguna llamada externa dentro
  de la transacción y reintento de la transacción **completa** con presupuesto acotado.
- **Motor antes que sintaxis:** MySQL y MariaDB divergen (alias de fila frente a
  `VALUES(col)` en `ON DUPLICATE KEY UPDATE`).

Defectos y contradicciones internas:

| Ejemplo | Adaptación |
|---|---|
| El pool de SQLAlchemy lleva `app:secret` en la URL | Contradice su propia regla de no poner credenciales en ejemplos; leer de entorno o gestor de secretos |
| Cola con `FOR UPDATE SKIP LOCKED` sin índice sobre `(status, created_at)` | La checklist de la misma pieza pide índices para lecturas con bloqueo; sin él cada reclamación recorre y bloquea más filas de las necesarias |
| `log_queries_not_using_indexes = ON` en la configuración «de partida» | La propia pieza lo limita a «entorno controlado» unas líneas antes; en producción puede inundar el log lento |
| Transferencia entre cuentas | No comprueba que existan las dos filas ni el saldo antes de los `UPDATE` |
| `CREATE USER 'app'@'%'` como ejemplo | `%` admite cualquier origen; restringir el host además de exigir TLS |

**Destino:** dos filas en la tabla de límites de `contracts-data.md` (réplica tras
escritura; interbloqueo y reintento completo). **No se abre guía de MySQL**: si un
consumidor PHP/CodeIgniter declara MySQL o MariaDB, esta pieza se lee junto a
`stack-practices/references/php-codeigniter.md` con las correcciones de arriba.

## S183 — NestJS

`6.533 bytes/231 líneas`. Estructura por módulos, `ValidationPipe` global, DTO
con `class-validator`, guards e interceptores, filtro de excepciones, config
validada al arrancar, transacciones en servicios y pruebas.

**Comparación.** TypeScript/Node en backend no es un stack declarado; **no se abre
especialidad** (misma regla que Java en S145 o Go en S116–S117). Lo transversal ya
está en `backend-practices`: autorización gruesa en guard y por recurso en el
servicio, un único formato de error, detalles internos fuera de la respuesta.
Correcciones para cuando haya consumidor:

| Ejemplo | Adaptación |
|---|---|
| `transformOptions: { enableImplicitConversion: true }` | La conversión implícita convierte la cadena `"false"` de una query en `true` para campos booleanos; transformar booleanos de forma explícita |
| El test monta `ValidationPipe` sin `forbidNonWhitelisted` ni la conversión, y sin el filtro global | Contradice «reutiliza en tests los mismos pipes y filtros que en producción» de la propia pieza |
| `HttpExceptionFilter` devuelve 500 sin registrar el error | La pieza pide «registrar y envolver centralmente» los fallos inesperados; registrar con identificador de correlación (backend-practices) |

**Sin destino** hasta que un consumidor declare NestJS.

## S189 — Keccak-256 en Node para Ethereum

`2.992 bytes/103 líneas`. `crypto.createHash('sha3-256')` es SHA3 del NIST, no el
Keccak-256 de Ethereum; usar los ayudantes de ethers, viem o web3.

**Comparación.** Dominio ajeno al ciclo (cadenas de bloques): **fuera del bundle**.
Defectos: el bloque «patrones comunes» usa `toUtf8Bytes` sin importarlo; y
`pubkeyToAddress` asume una clave pública sin comprimir de 65 bytes y quita el
primer byte sin comprobar la longitud, de modo que una clave comprimida produce
una dirección errónea sin error. Idea general reutilizable: cuando dos algoritmos
comparten nombre, un **test con vector de respuesta conocido** detecta la
confusión que el tipo no detecta. **Sin destino.**
