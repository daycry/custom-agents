# Mínimo común de código y TypeScript

Léela solo cuando la tarea revise o fije convenciones de código (nombres,
cohesión, comentarios) o tipos TypeScript, y el proyecto no tenga ya una guía
propia que lo cubra. Las convenciones del proyecto (constitución, linter,
formateador, guía de estilo) prevalecen siempre sobre esta referencia.

## Mínimo agnóstico

| Tema | Criterio | Señal de que falla |
|---|---|---|
| Nombres | Dicen qué representa el valor o qué hace la función, en el vocabulario del dominio que ya usa el repo | Un mismo concepto con dos nombres (`user`/`account`), o un nombre que miente tras un cambio |
| Cohesión | Una función hace una cosa a un nivel de abstracción; un módulo agrupa lo que cambia junto | Para entender un cambio hay que tocar cinco ficheros sin relación aparente |
| Simplicidad | La abstracción nace con la segunda variación real, no por si acaso | Una interfaz con una sola implementación y sin tests que la sustituyan |
| Duplicación | Se unifica lo que cambia por el mismo motivo; dos fragmentos iguales por coincidencia pueden quedarse separados | Corregir un bug obliga a buscar sus copias |
| Comentarios | Explican el porqué (restricción, decisión, enlace a la incidencia), no repiten el qué | Un comentario que ya no coincide con el código |
| Documentación pública | La API exportada documenta contrato, errores y unidades | Un parámetro `timeout` sin unidad |

Longitud de funciones y profundidad de anidamiento son indicadores
contextuales: `code-health` los mide, pero no son defectos de corrección por sí
solos ni justifican un refactor fuera del alcance de la tarea.

## Quién es dueño de cada grupo

Esta referencia no repite métodos que ya tienen dueño:

| Contenido | Dónde vive |
|---|---|
| Nombres, cohesión, simplicidad, comentarios | Esta referencia; las convenciones del proyecto prevalecen |
| Tipos, `null`/`unknown`, inmutabilidad y alias | Sección TypeScript de esta referencia |
| Errores, contexto, reintentos y concurrencia en el servidor | `backend-practices`; en Python, la [referencia Python](python.md) |
| Componentes, estado, efectos y debounce | [Referencia React](react.md) |
| Foco, teclado, accesibilidad y rendimiento medido | `frontend-quality` |
| API, validación en el borde y acceso a datos | `backend-practices` y `api-contract` |
| Estructura AAA, nombres y casos de test | `tdd` y `unit-tests` |
| Memoización, carga diferida y consultas costosas | Referencias React y backend, con medición |
| Organización de carpetas | La del proyecto; ninguna estructura es obligatoria |

## TypeScript (si el manifiesto lo declara)

Comprueba la versión de TypeScript y el `tsconfig` del proyecto antes de
proponer una opción o una sintaxis.

| Situación | Decisión | Escenario de prueba |
|---|---|---|
| Dato externo (JSON, `localStorage`, mensaje) | Tiparlo `unknown` y estrecharlo con una validación en el borde; un `as Tipo` no valida nada | Una respuesta con un campo ausente produce un error controlado, no un `undefined` que viaja |
| Variable de `catch` | Tratarla como `unknown` y comprobar `instanceof Error` antes de leer `message`; con `strict` (desde TS 4.4) ya es `unknown` | Un `throw "texto"` no rompe el manejador |
| Acceso por índice o clave dinámica | `noUncheckedIndexedAccess` añade `undefined` a ese acceso; no lo activa `strict` | El primer elemento de un array vacío se trata antes de usarlo |
| Copia con spread | El spread es superficial: los objetos anidados siguen compartidos con el original | Cambiar `copia.direccion.ciudad` cambia el original |
| `readonly` y `Readonly<T>` | Superficiales y solo en compilación; un alias escribible del mismo objeto lo sigue mutando | Una función que recibe un `Readonly<Pedido>` ve cambiar `pedido.lineas` desde otro alias |
| Mutar o copiar | Estado compartido de UI o de otro dueño se copia; un buffer local propio puede mutarse. Decide por dueño del estado, no por regla general | Un render no ve cambios hechos fuera del flujo de actualización |
| Re-lanzar un error | `new Error("contexto", { cause: err })` conserva la causa; registra el contexto redactado, sin el objeto completo con credenciales | El registro muestra la causa original y no el token de la URL |
| Varias promesas | `Promise.all` solo si son independientes y el primer fallo invalida el conjunto (las demás siguen en curso: si hay que pararlas, `AbortController`); `Promise.allSettled` si cada resultado cuenta; con muchas, límite de concurrencia | Una de diez falla: el resultado declara qué pasó con las otras nueve |
| Respuesta con estados | Unión discriminada (`{ estado: "cargando" } \| { estado: "ok", datos } \| { estado: "error", error }`) en vez de tres campos independientes | No existe un estado con `datos` y `error` a la vez |

No impongas envoltorios de respuesta, librerías de validación ni frameworks
que el proyecto no use; si introduces una forma de respuesta, sigue el contrato
de sus consumidores reales. Un test vacío es una ilustración, no cobertura.

Fuentes, consultadas el 2026-10-14:
[TSConfig `useUnknownInCatchVariables` y `noUncheckedIndexedAccess`](https://www.typescriptlang.org/tsconfig/),
[TypeScript, `readonly` y alias](https://www.typescriptlang.org/docs/handbook/2/objects.html),
[MDN `Error.cause`](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/Error/cause).
