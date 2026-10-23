# Familia Itô: cestas, cómputo, inferencia y entrenamiento — S141–S144

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cuatro cuerpos completos: **32.238 bytes/670 líneas** y tres recursos de S141–S142
(cliente `ito-baskets.js` y dos `agents/openai.yaml`).
[ito-family-reading-evidence.json](ito-family-reading-evidence.json).
Nada se ejecutó ni se integró; no se contactó ningún servicio. Propuestas para T-08.

## Decisión común

Las cuatro piezas envuelven productos de un proveedor concreto (mercados de
predicción y alquiler de GPU) y dos de ellas, S143–S144, son **andamios**: describen
un servicio que hoy no existe y se limitan a detenerse. **Fuera del bundle.** No
hay rol del ciclo que las necesite y su valor depende de credenciales y de una CLI
externa sin publicar.

Lo que sí merece la pena es el **método de seguridad**, que es de lo mejor del
corpus y refuerza propuestas ya hechas en bloques anteriores.

## S141 — Cestas y mercados (solo lectura)

`13.385 bytes/263 líneas` más el cliente (9.956 bytes/195 líneas). Cuatro modos
(índice, comparación, informe, hoja de planificación) sin ninguna vía de
ejecución, con un contrato de procedencia por dato.

| Idea | Pieza propia |
|---|---|
| Distinguir **fecha de la fuente** (`as_of`) de **fecha de recuperación**; si falta, `unknown`, nunca la hora actual | `research-first` (fuentes con fecha) |
| Comparación determinista: misma entrada y misma hora de comparación → misma salida; coincidencia por ID exacto, nunca por parecido | Patrón de los scripts deterministas del plugin |
| Vocabulario cerrado de errores con reintento único y sin bucles ante 429 | `backend-practices` (errores) |
| El contenido recuperado es dato no confiable y no amplía el acceso | Sección de contenido no confiable propuesta para `delivery-practices` (S115) |
| Usar el acceso **más débil** que baste (anónimo antes que con clave) | `delivery-practices` (límites de acceso MCP) |

Defectos del cliente: 401 y 403 salen ambos como `AUTH_REJECTED`, aunque la pieza
documenta `AUTH_FORBIDDEN` para el 403; el cuerpo se interpreta como JSON **antes**
de mirar el estado, de modo que un 429 o un 5xx con cuerpo HTML se informa como
`INVALID_RESPONSE` y se pierde el `Retry-After`.

## S142 — Cómputo GPU

`6.619 bytes/165 líneas`. Petición de precio (RFQ), estado, aceptación y
revocación a través de una CLI canónica que se compila desde su repositorio y
se apunta por ruta absoluta, **nunca por `PATH`**.

Ideas útiles: exigir **autoridad explícita del comprador** y todos los parámetros
antes de una operación con efecto (sin derivar topología); tras un fallo de
transporte ambiguo, **consultar el estado antes de repetir**. Ambas ya están en
`backend-practices` (idempotencia) y en el patrón de aprobación ligada de S096.

## S143–S144 — Inferencia y entrenamiento (andamios)

`6.147 + 6.087 bytes`. Hoy se detienen antes de autenticarse. Describen el
contrato futuro: manifiesto revisado cuyo **digest se calcula sobre el
descriptor ya abierto** (sin seguir enlaces simbólicos, con tamaño acotado) y
debe coincidir con el ligado a una confirmación de un solo uso; clave de
idempotencia reservada de forma atómica; «autenticación es identidad, no
autoridad sobre la carga de trabajo»; no declarar `ready` hasta pasar salud,
identidad del modelo y una prueba canaria.

Encaje: el digest sobre el descriptor abierto es la versión robusta del
`--expected-sha256` que ya usa `knowledge-curation.py apply`; anotarlo como
mejora posible si alguna vez la ruta pudiera cambiar entre la comprobación y el
uso. Sin destino inmediato.

**Contradicción entre piezas de la familia:** S142 expone `accept` y `logout`
(y la herramienta MCP `ito_accept`), S143 dice que el puente solo tiene `login`,
`auth`, `find`, `status` y `evals`, y que el MCP solo expone auth, find y status;
S144 añade `logout` pero no `accept`. Tres descripciones distintas de la misma
superficie.
