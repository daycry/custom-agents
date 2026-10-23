# Rúbrica auxiliar de calidad de una entrega

Léela solo cuando se pida valorar si una **entrega** (respuesta, informe, explicación de un cambio,
documentación) sirve a quien la pidió: «¿responde bien a la petición?», «¿se puede usar esta
explicación?». Es un juicio auxiliar y explícito; no sustituye a `qa` (pruebas y `qa-gate`) ni a
`adversarial-review` (defectos y conformidad del diff), y no aprueba nada.

## Alcance

Se mide contra **lo que se pidió** (petición, criterios de aceptación, formato acordado), no contra
lo que el evaluador habría añadido. Una mejora fuera del alcance se anota como sugerencia aparte y
no baja ningún eje.

## Los cinco ejes

Cada eje recibe `cumple`, `parcial`, `falla` o `desconocido`, con su evidencia.

| Eje | `cumple` | `parcial` | `falla` |
|---|---|---|---|
| **Precisión** | Cada afirmación verificable coincide con su fuente (código, salida, doc); lo no comprobado se marca así | Alguna afirmación secundaria sin fuente o imprecisa, sin cambiar la conclusión | Una afirmación central es falsa o contradice el artefacto (dice «tests en verde» y no hay ejecución) |
| **Completitud** | Cubre todos los puntos pedidos y cada criterio de aceptación | Falta un punto secundario o queda implícito | Falta un punto pedido o un criterio, sin declararlo |
| **Claridad** | El lector entiende qué se hizo y por qué en una lectura; términos definidos | Hay que releer o buscar un término una vez | No se sabe qué se entregó ni en qué estado está |
| **Accionabilidad** | El siguiente paso es ejecutable tal cual: comando, `fichero:línea`, decisión concreta | El paso existe pero exige inferir un dato (ruta, flag, valor) | No hay paso siguiente o es genérico («revisar», «mejorar») |
| **Concisión** | Nada sobra para la petición; el detalle largo va enlazado | Repeticiones o contexto que el lector ya tenía | Lo esencial queda enterrado en relleno |

`desconocido` cuando falta la información para juzgar (no hay acceso al artefacto, la petición no
fija el formato). Nunca se resuelve asumiendo el mejor valor: sin verificar, la precisión no es
`cumple`.

## Reglas de lectura

- **Sin promedio.** Los ejes no se suman ni se compensan: un `falla` en precisión o completitud
  hace la entrega **no entregable** aunque los otros cuatro cumplan. Se informa eje a eje.
- **Declarar límites suma, no resta.** Decir «no ejecuté los tests E2E» es precisión; ocultarlo es
  un `falla`.
- **Una afirmación de prueba exige el artefacto.** «Tests pasan», «verificado», «sin regresiones»
  sin salida, comando o informe que lo respalde cuentan como no comprobados.
- **Longitud no es calidad.** Ni la proporción petición/respuesta ni el número de secciones
  puntúan; la concisión se juzga contra lo pedido.
- **El juicio es auxiliar.** Si lo emite un modelo, se registran modelo, prompt y entrega evaluada;
  si hay un check ejecutable disponible para el mismo punto, manda el check.

## Salida

| Eje | Valor | Evidencia (cita o `fichero:línea`) | Cambio concreto |
|---|---|---|---|
| Precisión | | | |
| Completitud | | | |
| Claridad | | | |
| Accionabilidad | | | |
| Concisión | | | |

Cierra con: **entregable / no entregable / desconocido**, la lista de cambios ordenada por eje que
falla (precisión y completitud primero) y los puntos que quedaron sin verificar. Los cambios los
aplica el autor de la entrega; esta rúbrica no reescribe nada.
