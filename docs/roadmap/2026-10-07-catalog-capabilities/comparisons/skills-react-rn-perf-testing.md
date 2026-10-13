# React: React Native, patrones, rendimiento y pruebas — S228–S231

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cuatro cuerpos completos: **54.570 bytes/1.667 líneas**, sin recursos locales.
[react-rn-perf-testing-reading-evidence.json](react-rn-perf-testing-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08.

## Decisión común

React (web) tiene dueño: `stack-practices/references/react.md` (estado
derivado, efectos, fronteras cliente/servidor, formularios, pruebas por rol) y
`frontend-quality` (interacción y rendimiento medido). Como con S108 en
[skills-frontend-direction-patterns-slides.md](skills-frontend-direction-patterns-slides.md),
no se abre otra pieza: se proponen líneas concretas en esos dueños y se anotan
correcciones. React Native es otra plataforma sin consumidor declarado.

## S229 — Patrones React 18/19

`11.466 bytes/342 líneas`. Render puro, árbol de decisión de estado, Server y
Client Components, Suspense y error boundaries, acciones de formulario,
matriz de obtención de datos y composición.

**Comparación.** `react.md` ya cubre lo esencial con escenarios de prueba.
Correcciones:

| Ejemplo | Adaptación |
|---|---|
| Acción con `"use server"` en línea dentro de un fichero `"use client"` | No se puede definir una acción de servidor dentro de un módulo de cliente; va en su propio fichero |
| La acción actualiza `where: { id: parsed.data.id }` tomado del formulario | Sin autorización: cualquiera edita a otro usuario cambiando el `id` (y el formulario ni envía `id`). `react.md` ya pide autorización en el servidor |
| `useOptimistic` con `id: "pending"` | Dos envíos seguidos repiten la `key` |
| Buscador con `<input>` sin etiqueta | Contradice su propia sección de accesibilidad |
| «React Native: skill aparte, aún no existe» | S228 sí existe en el mismo corpus |

## S230 — Rendimiento React y Next.js

`18.184 bytes/575 líneas`. Catálogo de reglas en ocho prioridades (cascadas,
bundle, servidor, datos en cliente, re-render, render, micro-optimización de JS,
avanzados), adaptado de un catálogo público con atribución.

**Comparación.** `frontend-quality` prohíbe prescribir memoización o
virtualización por regla sin medir; la lente D de `adversarial-review` revisa
el coste del diff. El catálogo por reglas choca con ese criterio y no se adopta.
Sí aportan dos ideas que no están en el plugin:

| Idea | Destino |
|---|---|
| Toda función `"use server"` es un endpoint público: autenticar y autorizar dentro | `review-lens-select.py`: añadir `"use server"` a los patrones de contenido de la lente C, con su test |
| El estado mutable de módulo en servidor (RSC/SSR) se comparte entre peticiones y usuarios | Fila nueva en `react.md` con el caso «dos usuarios concurrentes no ven datos del otro» |

Defectos: `useLatest` escribe una ref durante el render, lo que contradice el
render puro de S229; «paralelizar con `Promise.all` por elemento» es un N+1 en
paralelo y sin límite (caso para probar contra la heurística de la lente D);
«ahorra 200–800 ms de JS» mezcla tiempo y bytes y no tiene fuente; la
autenticación de acciones aparece bajo «rendimiento»; el estado del compilador
de React figura como «RFC, en canary», dato fechado que hay que contrastar con la
documentación oficial antes de citarlo; las micro-optimizaciones
(`const len = arr.length`) se prescriben sin medición.

## S231 — Pruebas de componentes React

`13.168 bytes/424 líneas`. Testing Library con prioridad de consultas,
`userEvent`, esperas asíncronas, MSW, wrapper de proveedores, hooks, axe,
snapshots, frontera con Playwright y objetivos de cobertura.

**Comparación.** `react.md` ya exige rol/nombre accesible, sin sleeps y sin
snapshot como única prueba; `tdd` es el método; `qa` hace E2E. Dos líneas útiles
para `react.md`: con MSW, **una petición no simulada hace fallar el test**
(`onUnhandledRequest: "error"`), y un cliente de caché nuevo por test, sin
reintentos. Defectos: dice «elige un solo runner salvo separación clara» y a
continuación prescribe tres carriles; `renderWithProviders` recibe `options` pero
fija los proveedores; los objetivos de cobertura por capa repiten lo descartado
en S081 (`tests.coberturaMinima` con herramienta oficial).

## S228 — React Native y Expo

`11.752 bytes/326 líneas`. Rutas con Expo Router y validación de parámetros,
separación de estado, TanStack Query con Zod, listas virtualizadas, estilos,
APIs nativas en hooks y almacenamiento seguro de tokens.

**Comparación.** `react.md` asume DOM. **No se abre especialidad React Native**
hasta que un consumidor la declare. Ideas ya cubiertas en otra forma: validar
parámetros de enlaces profundos como entrada no confiable, tokens en el almacén
seguro del sistema y nunca secretos en el bundle. Correcciones:

| Ejemplo | Adaptación |
|---|---|
| `router.replace('/not-found')` durante el render | Navegar es un efecto; hacerlo en un efecto o devolver una redirección declarativa |
| `useCurrentLocation` sin captura de errores | Si `getCurrentPositionAsync` rechaza, el estado queda en `loading` para siempre |

**Destino:** las dos ideas de S230 (lente C y `react.md`) y las dos líneas de
S231 en `react.md`; resto, correcciones anotadas.
