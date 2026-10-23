# Errores, evals, automatización de firma y proveedores externos — S095–S100

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Seis cuerpos completos y un recurso: **45.983 bytes/1.423 líneas** de cuerpos
más 4.651 bytes del checklist de S096. [errors-evals-providers-reading-evidence.json](errors-evals-providers-reading-evidence.json)
registra fuentes y contrapartes. Los scripts citados por S097
(`scripts/lib/eval-harness/`) y los servidores MCP de S099/S100 no se leyeron
ni se ejecutaron. Nombres originales en el mapa privado. Propuestas para T-08.

## S095 — Manejo de errores en TypeScript, Python y Go

`10.984 bytes/377 líneas`. Jerarquías tipadas, Result, manejadores globales,
Error Boundary, errores centinela en Go, reintento con backoff, mensajes al usuario.

**Comparación.** backend-practices fija códigos estables, separación de error
de validación e inesperado, correlación y retry solo cuando es seguro;
stack-practices/python exige encadenar la causa y no capturar `Exception` para
devolver éxito. El delta son los ejemplos por lenguaje.

| Ejemplo o afirmación | Adaptación |
|---|---|
| Envelope propio `{error:{code,message}}` como estándar | Problem Details (RFC 9457) o el contrato existente del cliente, ya fijado en backend-practices |
| `fetchUser` captura todo y devuelve `DB_ERROR` sin causa | Encadenar la causa (`cause`) y registrarla; si no, el diagnóstico se pierde |
| `ValidationError` con 422 y `UnauthorizedError` con 401 fijos | El estado depende del contrato existente; no cambiarlo en un endpoint ya consumido |
| Go: `ErrUnauthorized` responde 403 | 401 (sin autenticar) y 403 (sin permiso) son distintos; mezclar ambos confunde al cliente |
| Go: `err.Error()` en la respuesta 404 | Expone el texto interno envuelto (IDs, consultas); mensaje propio al cliente |
| `withRetry` con `retryIf = () => true` por defecto | Por defecto no reintentar; reintentar solo lo clasificado como transitorio e idempotente |
| `fetch().then(r => r.json())` como ejemplo de retry | `fetch` no lanza en 4xx/5xx: el `retryIf` nunca ve un `AppError` |
| «Envolver todos los componentes en ErrorBoundary» | Los boundaries no capturan errores de eventos ni async; colocarlos por zona funcional |
| `console.error` del error completo | Redactar datos sensibles antes de registrar |

**Destino.** Ejemplos por lenguaje en `stack-practices` (Python/React) y una
fila de reintentos por defecto desactivados en backend-practices.

## S096 — Colocación de campos en un compositor de firma electrónica

`10.333 bytes/199 líneas` + checklist (`4.651 bytes/82 líneas`). Procedimiento
escrito (no ejecutable) para automatizar un compositor web por navegador:
identidad de origen y marco, calibración de coordenadas, propiedad de campos
por destinatario, evidencia y puerta dura antes de enviar.

**Comparación.** El dominio (contratos y firma) no tiene rol en el plugin.
El método de **puerta de acción con efectos externos** es el más riguroso del
corpus leído hasta ahora: borrador por defecto, aprobación ligada a destinatarios,
digest del documento, acción y caducidad, revalidación inmediatamente antes de
actuar, y ningún texto de la página puede conceder autoridad. Coincide con la
dirección del plugin (aprobación de planes ligada a hashes, `version_changed`).

**Destino.** No adoptar la pieza. Registrar el patrón «aprobación ligada a
objeto, acción y caducidad; revalidar antes del efecto» como criterio de
delivery-practices para integraciones con efectos externos.

## S097 — Desarrollo guiado por evals

`8.738 bytes/305 líneas`. Evals de capacidad y regresión, calificadores de
código/modelo/humano, pass@k y pass^k, almacenamiento en `.claude/evals/` y
utilidades de cápsula, replay y recibo.

**Comparación.** `outcome-evals` ya separa activación de resolución, exige corpus
y checks antes de ejecutar y publica casos, repeticiones y fallos; `evals/` mide
activación de piezas; `tdd` cubre el criterio antes del código. El delta útil es
la **terminología pass@k / pass^k** para expresar fiabilidad con repeticiones.

| Afirmación | Adaptación |
|---|---|
| Objetivo «pass@3 > 90 %» | Umbral sin base; publicar k, casos y fallos, como exige outcome-evals |
| Calificador por modelo con puntuación 1-5 | Un juicio de modelo no sustituye un check disponible (tabla de outcome-evals) |
| `grep` de un nombre de función como eval | Comprueba presencia, no comportamiento |
| `.claude/evals/` como almacén de definiciones | El plugin versiona el corpus en `evals/` o en la carpeta de la iniciativa; no otro almacén |
| La propia pieza declara que la ejecución de candidatos está deshabilitada sin aislamiento | **Conservar** como límite: sin contención verificada no se ejecutan candidatos |

**Destino.** Definición de pass@k/pass^k en `outcome-evals/references/protocol.md`.

## S098 — Decimales de tokens EVM

`3.988 bytes/131 líneas`. Consultar `decimals()`, cachear por cadena y dirección,
aritmética exacta, normalizar a 18 decimales.

**Comparación.** Encaja en la especialidad opcional Solidity del bloque de
contratos (S073). Correcciones: el fallback silencioso a 18 decimales cuando
`decimals()` revierte produce importes erróneos en vez de fallar; la
normalización con división trunca sin declararlo; y un token con proxy puede
cambiar `decimals()` tras una actualización, así que la caché necesita
invalidación. **Destino:** referencia de la especialidad Solidity opcional.

## S099 — Búsqueda con Exa por MCP

`4.425 bytes/117 líneas`. Configuración del servidor MCP, herramientas y
parámetros, resultados como contenido no confiable.

**Comparación.** Igual que Context7 (S085): canal opcional de `research-first`.
Correcciones: la configuración de ejemplo pone la clave en `~/.claude.json`
(usar variables de entorno sin valor en el fichero) y ejecuta `npx -y` sin
versión fijada; buscar perfiles personales (`site:linkedin.com/in`) introduce
datos personales en la investigación. **Conservar** la sección de resultados no
confiables. **Destino:** fila de canal en research-first.

## S100 — Generación de imagen, vídeo y audio con fal.ai

`7.515 bytes/294 líneas`. Configuración MCP, modelos por tipo de medio,
parámetros, estimación de coste y descubrimiento.

**Comparación.** Fuera del ciclo de desarrollo del plugin; ningún rol genera
medios. La pieza se declara «propensa a quedarse obsoleta» (IDs de modelos,
precios). Mismas correcciones de configuración que S099; además, subir ficheros
locales a un servicio externo requiere autorización explícita del usuario.
**Fuera del bundle**; extensión de proyecto si un consumidor la necesita.

## Resumen

| ID | Decisión | Destino |
|---|---|---|
| S095 | Ejemplos útiles con 9 correcciones | stack-practices + backend-practices |
| S096 | Dominio ajeno; patrón de aprobación valioso | delivery-practices (criterio) |
| S097 | Solapa con outcome-evals | pass@k/pass^k en su protocolo |
| S098 | Dominio Solidity | especialidad opcional existente |
| S099 | Canal de búsqueda opcional | research-first |
| S100 | Fuera del ciclo | extensión de proyecto |

Contraste oficial pendiente para S095 (RFC 9457 ya citado en backend-practices)
y S097; ningún servidor MCP se configuró.
