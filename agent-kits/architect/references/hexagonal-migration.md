# Opción hexagonal y migración por rebanadas

> Léela solo en P3 cuando una de las opciones de `design.md` sea aislar el
> dominio de su infraestructura (puertos y adaptadores) o migrar un módulo
> existente hacia esa forma. Es **una opción más**, comparada con la misma
> tabla que las otras; no un estilo que se imponga.

El reparto controlador / servicio / repositorio y sus pruebas por capa ya
están en `skills/backend-practices/references/service-boundaries.md`; la
transacción frente a un servicio externo, en
`skills/backend-practices/references/contracts-data.md`. Aquí solo va lo que
añade la opción hexagonal.

## Cuándo merece ser una opción

| Señal en el repo | Por qué apunta a hexagonal |
|---|---|
| El mismo caso de uso se dispara desde HTTP, colas, CLI o tareas programadas | Un puerto de entrada evita repetir la regla en cada borde |
| Hay dos o más implementaciones reales de una dependencia (dos pasarelas de pago, dos almacenes) | El puerto de salida expresa esa variación |
| Los tests del dominio necesitan base de datos o red para correr | Los adaptadores en el borde permiten probar el dominio aislado |
| Se va a sustituir una infraestructura (motor, proveedor) sin parar el producto | Permite migrar por rebanadas detrás del puerto |

Sin variación real, un puerto es ceremonia: no se crea un puerto para el
logger o el reloj de un servicio pequeño. En Python, el criterio ya fijado es
`Protocol` solo cuando hay comportamiento que variar
(`skills/stack-practices/references/python.md`).

## Piezas que la opción debe nombrar en `design.md`

| Pieza | Qué escribe el architect en «Impacto» |
|---|---|
| Dominio | Ruta del núcleo y la regla: no importa nada de infraestructura |
| Puerto de entrada | Caso de uso con su contrato (entrada, salida, errores) |
| Puerto de salida | Lo que el dominio necesita del exterior, con la semántica exacta (crear frente a actualizar, no un `save` ambiguo) |
| Adaptadores | Ruta de cada uno: HTTP, base de datos, proveedor externo |
| Raíz de composición | Único sitio donde se conectan puertos y adaptadores |

Orden de efectos: si un caso de uso cobra y luego guarda, un fallo al guardar
deja un cobro sin pedido. El diseño fija el orden y la compensación (ver
`contracts-data.md`), no lo deja al implementer.

## Migración por rebanadas

La tabla de la opción valora la reversibilidad con este plan, no con una
reescritura de golpe.

1. **Rebanada vertical.** Elige un caso de uso completo (entrada, regla,
   persistencia), no una capa entera.
2. **Tests de caracterización antes de extraer.** Fijan el comportamiento
   actual, incluidos sus defectos conocidos, con entradas y salidas reales.
   Sin ellos no hay forma de saber si la extracción cambió algo.
3. **Estrangulador.** El código nuevo crece al lado del viejo y la entrada se
   desvía caso a caso; el viejo se retira cuando ya no recibe tráfico.
4. **Interruptor reversible por rebanada.** Una configuración elige el camino
   viejo o el nuevo; volver atrás es cambiar el valor, no desplegar código.
   El interruptor tiene fecha de retirada.
5. **Tests de contrato por puerto.** Una misma batería se ejecuta contra cada
   adaptador del puerto (el real y el doble de prueba); si el doble pasa y el
   real no, el doble miente.
6. **Retirada del camino viejo.** Cuando la rebanada lleva el tráfico, se
   borran el código viejo y el interruptor; cada retirada es una tarea del plan.

El código de transición (desvío, interruptor) es temporal y se declara como
tal en «Riesgos»: si no tiene fecha de retirada, se queda para siempre.

## Cómo se compara con las otras opciones

| Criterio | Qué mirar en esta opción |
|---|---|
| Complejidad | Nº de puertos y adaptadores nuevos; capas que hoy no existen |
| Riesgo | Rebanadas sin tests de caracterización; orden de efectos sin decidir |
| Coste relativo | Rebanadas hasta retirar el camino viejo, no solo la primera |
| Reversibilidad | Interruptor por rebanada: alta mientras convivan los dos caminos |

Si la alternativa más simple (un servicio bien acotado) cumple los criterios
de decisión, la recomendación es esa, y esta opción queda como descartada con
motivo.

## Fuentes

- Alistair Cockburn, «Hexagonal architecture» (intención del patrón): https://alistair.cockburn.us/hexagonal-architecture/ · consultada 2026-10-14.
- Martin Fowler, «Strangler Fig Application» (sustitución gradual y arquitectura de transición): https://martinfowler.com/bliki/StranglerFigApplication.html · consultada 2026-10-14.
