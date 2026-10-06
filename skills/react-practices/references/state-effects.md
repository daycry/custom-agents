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
