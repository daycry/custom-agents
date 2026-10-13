# Estado derivado y efectos

| Situación | Decisión | Escenario de prueba |
|---|---|---|
| Un valor depende solo de props/estado | Derivarlo al renderizar; memoizar solo si hay trabajo medible | Cambiar la entrada actualiza el valor sin un render de estado obsoleto |
| Acción causada por un evento del usuario | Mantenerla en el handler | Montar o repetir un efecto no reenvía una compra o mutación |
| Sincronización con sistema externo | Effect con cleanup y dependencias reales | Remontar no duplica suscripción; desmontar libera recursos |
| Búsqueda remota con respuestas fuera de orden | Usar mecanismo del framework/caché; si hay fetching manual, invalidar resultado obsoleto | La petición A llega después de B y no reemplaza el resultado de B |
| Reset de estado por identidad distinta | Expresar identidad con key cuando corresponda | Cambiar de usuario no reutiliza edición local del anterior |
| Cliente y servidor en framework híbrido | Datos y secretos respetan frontera del servidor; el primer render es determinista (sin `Date.now()`, aleatorios, almacenamiento del navegador ni fragmento de URL en el HTML del servidor); la convención de ficheros y rutas se comprueba en la versión instalada antes de proponer renombrar | El bundle del navegador no recibe secretos ni ejecuta APIs de servidor; la hidratación no avisa de diferencias entre servidor y cliente |
| Estado de módulo en servidor (RSC/SSR) | Ninguna variable de módulo guarda datos de una petición o usuario; el estado por petición viaja por argumentos, contexto de petición o caché con clave de identidad | Dos usuarios concurrentes renderizan a la vez y ninguno ve datos del otro |

Ejemplo de convención ligada a versión: en Next.js 16, `middleware.ts` está en
desuso y renombrado a `proxy.ts`, pero sigue siendo la vía del runtime edge, que
`proxy` no admite. No es un error que corregir sin mirar versión y runtime.

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

Si el manifiesto declara Vite: toda variable con el prefijo público (`VITE_` por
defecto) se incrusta en el bundle, y `loadEnv(mode, root, '')` carga todas las
variables sin filtrar, de modo que pasar una de ellas a `define` la publica.
`vite build` transpila sin comprobar tipos: en TypeScript, la verificación
incluye `tsc --noEmit` o el comando de tipos que ya use el proyecto.

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
Si el proyecto usa MSW, `onUnhandledRequest: "error"` hace fallar el test ante
una petición sin handler en vez de dejarla pasar con un aviso. Con una librería
de caché de datos, crea un cliente nuevo por test y sin reintentos, para que el
error se observe al primer intento y no se filtren datos entre tests.

Combina frontend-quality para foco/teclado y mediciones. No dupliques sus gates.
Memoización, splitting y virtualización requieren escenario/profiler medidos.

## Ejemplos corregidos

Carga manual cuando el proyecto no tiene librería de datos (si la tiene, su
caché ya resuelve cancelación y orden; no lo dupliques):

```jsx
const [res, setRes] = useState({ q: null, data: null, error: null });
useEffect(() => {
  const ctrl = new AbortController();
  fetch(`/api/items?q=${encodeURIComponent(q)}`, { signal: ctrl.signal })
    .then((r) => {
      if (!r.ok) throw new Error(`HTTP ${r.status}`); // un 500 no son datos
      return r.json();
    })
    .then((data) => { if (!ctrl.signal.aborted) setRes({ q, data, error: null }); })
    .catch((error) => { if (!ctrl.signal.aborted) setRes({ q, data: null, error }); });
  return () => ctrl.abort(); // ni setState tras desmontar ni respuesta obsoleta
}, [q]);
const loading = res.q !== q; // datos de otra consulta cuentan como carga
```

`fetch` no rechaza en 4xx/5xx: sin comprobar `r.ok`, un cuerpo de error se
pinta como resultado y un reintento que espera una excepción no lo ve.
Mostrar `res.data` cuando `res.q !== q` enseña datos de la consulta anterior.

Error boundaries: uno por zona funcional (ruta, panel) además del de la raíz,
no uno por componente. El fallback muestra un mensaje propio y el detalle va al
registro: `error.message` puede llevar rutas, consultas o IDs internos. No
capturan errores de handlers ni de código async; esos van al estado de la
operación.

| Patrón | Forma correcta (WAI-ARIA APG / HTML) | Error frecuente |
|---|---|---|
| Modal | `<dialog>` con `showModal()`: el resto del documento queda inerte y la petición de cierre llega como evento `cancel` | Foco al contenedor de un `div` con el fondo aún interactivo |
| Errores de formulario | Resumen de errores o una única región `aria-live`, cada error asociado a su campo | `role="alert"` en cada campo: con varios errores se anuncian todos a la vez |
| Mensaje de estado | `role="status"`, que ya es `polite` implícito | Añadirle `aria-live="assertive"` |
| Combobox propio | `<select>` nativo; si no basta, el patrón APG completo (`aria-activedescendant`, ids de opciones, `aria-expanded`) | `div` con `role="combobox"` cuya opción activa no se anuncia |
| Pestañas | `tablist`/`tab`/`tabpanel`, `aria-selected` y flechas entre pestañas | Botones sueltos sin roles ni navegación por flechas |
| Movimiento reducido | `@media (prefers-reduced-motion)` en CSS | Hook que arranca en `false` y anima el primer render |

Los casos que hay que probar los fija frontend-quality; esta tabla solo da la
forma React/HTML de llegar a ellos.

Fuentes: [state sharing](https://react.dev/learn/sharing-state-between-components),
[Suspense](https://react.dev/reference/react/Suspense),
[React Testing Library](https://testing-library.com/docs/react-testing-library/intro/),
[Testing Library queries](https://testing-library.com/docs/queries/about/),
[WAI-ARIA APG patterns](https://www.w3.org/WAI/ARIA/apg/patterns/),
[HTML dialog](https://html.spec.whatwg.org/multipage/interactive-elements.html#the-dialog-element),
[Vite env](https://vite.dev/guide/env-and-mode),
[Vite TypeScript](https://vite.dev/guide/features#typescript).
