# Estado derivado y efectos

| Situación | Decisión | Escenario de prueba |
|---|---|---|
| Un valor depende solo de props/estado | Derivarlo al renderizar; memoizar solo si hay trabajo medible | Cambiar la entrada actualiza el valor sin un render de estado obsoleto |
| Acción causada por un evento del usuario | Mantenerla en el handler | Montar o repetir un efecto no reenvía una compra o mutación |
| Sincronización con sistema externo | Effect con cleanup y dependencias reales | Remontar no duplica suscripción; desmontar libera recursos |
| Búsqueda remota con respuestas fuera de orden | Usar mecanismo del framework/caché; si hay fetching manual, invalidar resultado obsoleto | La petición A llega después de B y no reemplaza el resultado de B |
| Reset de estado por identidad distinta | Expresar identidad con key cuando corresponda | Cambiar de usuario no reutiliza edición local del anterior |
| Cliente y servidor en framework híbrido | Datos y secretos respetan frontera del servidor | El bundle del navegador no recibe secretos ni ejecuta APIs de servidor |

No eliminar efectos necesarios para sistemas externos al reducir renders.
Abortar una petición no demuestra que el servidor haya deshecho una mutación;
la idempotencia pertenece también al contrato de la API.

Fuente oficial, 2026-10-06:
[You Might Not Need an Effect](https://react.dev/learn/you-might-not-need-an-effect).
Verifica APIs de framework y caché en la documentación de sus versiones reales.

## Composición, datos y pruebas React

Comprueba React, router, build y librería de tests reales. Mantén estado en el
dueño más próximo que lo necesita; separa datos remotos, identidad de formulario
y preferencias de UI. No conviertas todos ellos en un store global. Si un contexto
provoca renders costosos, mide consumidores y frecuencia antes de dividirlo.

Los límites cliente/servidor pertenecen al framework: no traslades ejemplos de
Actions/RSC a una SPA sin ese contrato. Props serializadas no llevan credenciales.
Suspense depende de fuentes compatibles; envolver fetch manual no lo hace
suspender. Error boundaries de render no sustituyen manejo de fallos de handlers.
Comprueba APIs de React 19 contra la versión mínima antes de proponerlas.

Formularios prueban pending, éxito, validación y error, con datos preservados y
autorización en el servidor. Optimismo requiere revertir/reconciliar y distinguir
un reintento del envío original. Cache keys incluyen identidad, filtros y tenant;
al mutar, invalida lo pertinente según la librería existente. No instales otra
librería de fetching únicamente por aplicar esta guía.

Tests de componentes actúan por rol/nombre accesible y eventos del usuario;
esperan estados observables, sin sleeps arbitrarios ni snapshot como única prueba.
Incluye cambio rápido de filtros, desmontaje durante carga y doble envío. Usa
fake timers solo para el reloj que se controla y restaura su estado; integra con
el contrato del runner. E2E verifica el flujo real y frontera API con qa.

Combina frontend-quality para foco/teclado y mediciones. No dupliques sus gates.
Memoización, splitting y virtualización requieren escenario/profiler medidos.

Fuentes: [state sharing](https://react.dev/learn/sharing-state-between-components),
[Suspense](https://react.dev/reference/react/Suspense),
[React Testing Library](https://testing-library.com/docs/react-testing-library/intro/),
[Testing Library queries](https://testing-library.com/docs/queries/about/).
