# Guías del propio catálogo, operación de agentes y dominios ajenos — S089–S094

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Seis cuerpos completos: **54.512 bytes/906 líneas**, cero recursos en sus
directorios. [catalog-self-ops-domains-reading-evidence.json](catalog-self-ops-domains-reading-evidence.json)
registra fuentes y contrapartes propias. Los scripts, comandos y repositorios
hermanos que citan (catálogo, planificador de instalación, app de GitHub) no
se leyeron. Nombres originales en el mapa privado. Decisiones propuestas para T-08.

Ninguna pieza se ejecutó ni se integró. Tres de las seis describen el propio
catálogo de origen; su valor aquí es el **principio**, no el contenido.

## S089 — Guía del catálogo leída en vivo

`472d72a270cb…`, 5.713 bytes/190 líneas. Responder sobre qué incluye el
catálogo leyendo ficheros actuales, no memoria; respuesta corta con fichero
canónico, comando de verificación y siguiente paso.

**Comparación.** El plugin ya lo hace con dueños deterministas: `skill-index.py`
(índice al arrancar, por hash), `/plugin-catalog` (panel con fuentes y conflictos),
`/doctor` (instalación) y `/work-context` (selección por tarea). Conservar dos
reglas de presentación: no volcar el catálogo entero y no afirmar que una pieza
existe sin comprobarla — ya cubierta por el linter de citas. **Sin destino nuevo.**

## S090 — Recetas de secuencias de comandos

`0c3250fe8c8c…`, 6.451 bytes/150 líneas. Agrupar comandos por prefijo y dar orden
de ejecución y **condición de parada**, solo como consejo.

**Comparación.** El plugin tiene 17 comandos y los orquestadores ya fijan el
orden (`/pm-cycle` → `/dev-cycle`, vía rápida, `/retro`) en `docs/FLOWS.md`.
La clasificación por prefijo no aplica. El criterio útil es explícito en la pieza:
todo bucle autónomo declara condición de parada **y** tope de coste/iteraciones;
coincide con los bucles acotados a 3 de `/dev-cycle`. **Sin destino nuevo.**

## S091 — Auditoría de coste de una app de GitHub concreta

`efcc5b7c850d…`, 6.477 bytes/161 líneas. Flujo para un repositorio hermano
específico: webhooks, colas, reserva de cuota, enrutado a modelos premium.

**Comparación.** El repositorio y el producto no existen aquí; la pieza no se
adopta. Cuatro patrones son generales de backends con IA y faltan en
`backend-practices`: (1) comprobar cuota en la entrada y reservarla en el worker
permite carreras que superan el límite; (2) ramas o PR generados por la propia
app que vuelven a disparar el webhook producen recursión; (3) gastar tokens antes
de garantizar la persistencia del resultado quema coste sin entregar valor;
(4) reintentar errores deterministas multiplica el gasto. **Destino:** filas en la
tabla de límites de `backend-practices/references/contracts-data.md`.

## S092 — Operación de correo con verificación de envío

`188b226ec0df…`, 4.401 bytes/133 líneas. Triaje, borradores y envío con prueba
en «Enviados»; el correo entrante es dato no confiable.

**Comparación.** No hay superficie de correo en el plugin. El principio de
contenido externo no confiable ya rige en delivery-practices (respuestas MCP sin
autoridad) y en el journal (citas, no instrucciones). La regla «nunca afirmar
un envío sin prueba del destino» coincide con la de publicación comprobada de
T-16. **Sin destino**; candidata a extensión de proyecto si un consumidor opera correo.

## S093 — Compra de energía para industria y comercio

`4b4cb5d87f57…`, 29.934 bytes/221 líneas. Persona de responsable de compras de
energía: anatomía de la factura, estrategias de cobertura, cargos por demanda,
PPA, informes de alcance 2, escalados e indicadores.

**Comparación.** Conocimiento de dominio de negocio, no del ciclo de desarrollo;
ningún rol del plugin lo consume. Las cifras (precios, primas, rangos de pago)
dependen de fecha y mercado y no se verificaron. El cauce existente es una
**persona de proyecto** (`.claude/personas/`, reconocida por project-extensions),
que un consumidor del sector puede declarar con fuentes y fecha. **Fuera del bundle.**

## S094 — Operación de agentes de larga duración

`468a10e50752…`, 1.536 bytes/51 líneas. Ciclo de vida, observabilidad, control
de seguridad, cambios con rollback, métricas e incidentes, en forma de lista.

**Comparación.** Sin procedimiento verificable: enumera principios que
delivery-practices ya concreta (artefacto inmutable, credenciales mínimas,
readiness, rollback, condiciones de parada). Las métricas «coste por tarea
correcta» y «distribución de clases de fallo» solo son útiles con fuente
medida (`usage-meter`, `qa-gate`). **Sin destino nuevo.**

## Resumen

| ID | Decisión | Destino |
|---|---|---|
| S089 | Cubierta por dueños deterministas | — |
| S090 | Criterio ya presente (bucles acotados) | — |
| S091 | Pieza no aplicable; 4 patrones útiles | backend-practices, tabla de límites |
| S092 | Sin superficie propia | extensión de proyecto si se necesita |
| S093 | Dominio ajeno al ciclo | persona de proyecto |
| S094 | Lista sin procedimiento | — |

Validación pendiente: los cuatro patrones de S091 necesitan escenario de prueba
propio antes de entrar en backend-practices.
