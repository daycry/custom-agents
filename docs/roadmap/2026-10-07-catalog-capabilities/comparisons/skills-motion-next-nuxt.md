# Animación con Motion, Next.js con Turbopack y Nuxt 4 — S177–S179, S188 y S191

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cinco cuerpos completos: **49.917 bytes/1.491 líneas**, sin recursos locales.
[motion-next-nuxt-reading-evidence.json](motion-next-nuxt-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08.

## Decisión común

Las cinco piezas son de frontend. `stack-practices` cubre React (estado, efectos,
frontera cliente/servidor en frameworks híbridos) y `frontend-quality` cubre
interacción, accesibilidad y rendimiento medido, incluida la preferencia de
movimiento («Respeta preferencias de movimiento y contraste»). Ninguna de las dos
elige librerías («Las guías no eligen librerías»). Por eso no se abre una guía
de Motion ni de Nuxt; se extraen criterios generales para las dos piezas dueñas.

## S177–S179 — Sistema de animación con Motion (fundamentos, patrones, avanzado)

`18.800 bytes/597 líneas` (avanzado), `9.797 bytes/300 líneas` (fundamentos) y
`13.418 bytes/435 líneas` (patrones). Tres capas encadenadas sobre `motion/react`:
tokens de duración, curvas y muelles con reglas «no negociables» y un gate
`shouldAnimate()`; patrones de UI (botón, modal, toast, stagger, transición de
página, scroll, acordeón); arrastre, gestos, texto, SVG, `useAnimate` y loaders.

**Comparación.** Solapa con `frontend-quality` (preferencia de movimiento,
modal accesible, rendimiento) y con `stack-practices/references/react.md`
(efectos con cleanup). Lo que aporta de verdad son criterios independientes de la
librería: la animación debe servir para algo (guiar la atención, comunicar estado,
mantener continuidad espacial) o se elimina; animar `transform`/`opacity` en vez
de propiedades de layout; pausar animaciones infinitas con la pestaña oculta;
toda salida definida junto a la entrada. Coincide con lo ya fijado en S108
(respetar `prefers-reduced-motion`) y en el bloque Flutter/accesibilidad
(`useReducedMotion` inicializado en `false`: primer render animado antes de leer
la preferencia; el mismo hook es el que usa `useSafeMotion` aquí).

Defectos concretos y contradicciones internas:

| Ejemplo o regla | Problema | Adaptación |
|---|---|---|
| Regla 3 de S178: con movimiento reducido no hay transformaciones | `FadeInCard` mantiene `whileHover`/`whileTap` con `scale` y la transición `springs.gentle` sin límite de 0,2 s | Las interacciones también respetan la preferencia; la regla debe aplicarse a todo el componente |
| Ejemplo «CORRECTO» de SSR: `initial={{ opacity: mounted ? 0 : 1 }}` | `initial` solo se lee al montar: el primer render fija opacidad 1 y la animación no ocurre nunca | El riesgo real del SSR es contenido invisible hasta hidratar; decidir si el contenido debe verse sin JS |
| `FadeInCard` devuelve `<div>` hasta montar y luego `motion.div` | Cambiar el tipo de elemento remonta los hijos: se pierde su estado y hay salto visual | Mantener el mismo elemento y variar solo las props de animación |
| `isLowEnd` = `hardwareConcurrency <= 4` desactiva animaciones | Umbral sin medición; deja sin animación a muchos equipos normales | `frontend-quality` exige medir en el dispositivo objetivo, no reglas por número |
| Regla 6/8: «sin números en línea» | Los propios ejemplos usan `dragConstraints` 100, umbrales 120/500, `staggerChildren: 0.08`, `margin: "-80px"` | Regla incumplida por su autor; no exigirla como «no negociable» |
| Regla 3 de S177: no inferir intención solo por velocidad | El código de swipe y del panel descartable usa `offset > X \|\| velocity > Y`: basta la velocidad | Usar `&&` o documentar la excepción |
| `useLongPress` | Sin cleanup del temporizador al desmontar (contradice su regla 7), sin `pointercancel` y sin equivalente de teclado | Limpiar al desmontar y ofrecer la acción por teclado |
| Lista reordenable con `Reorder` y panel que se cierra arrastrando | Solo con arrastre | WCAG 2.2 (criterio 2.5.7, movimientos de arrastre) pide alternativa con un solo puntero; añadir también teclado |
| Acordeón con `scaleY: 0` y `opacity: 0` | `scaleY` no cambia la altura de layout (queda el hueco) y el contenido oculto sigue siendo enfocable | Ocultar de verdad (`hidden`/`inert`) al cerrar; el foco no debe llegar a contenido invisible |
| Modal que «incluye» trampa de foco, Escape y bloqueo de scroll | El código solo pone `role` y `aria-modal` | La tabla de `frontend-quality` ya fija el caso completo (foco inicial, Escape, retorno de foco, fondo inerte) |
| `-translate-x-1/2`/`-translate-y-1/2` de Tailwind junto a `x`/`y` de Motion (modal, seguidor del cursor) | Según la versión de Tailwind, el `transform` en línea de Motion anula el centrado | Comprobar en la versión real; centrar con layout o componer la traslación en Motion |

**Destino:** `frontend-quality/references/interaction-performance.md`, una fila
«Animación» en la tabla de casos (propósito, solo `transform`/`opacity`,
preferencia de movimiento aplicada también a hover/tap, pausa con pestaña
oculta, alternativa sin arrastre, contenido colapsado no enfocable). Sin guía
de Motion: la elección de librería es del proyecto.

## S188 — Next.js 16 y Turbopack

`3.141 bytes/58 líneas`. Turbopack por defecto en desarrollo, caché en disco,
analizador de bundles y el cambio de `middleware.ts` a `proxy.ts` en Next.js 16.

**Comparación.** Casi todo es descripción de producto con cifras sin fuente
(«5–14x») y remisiones a la documentación de cada versión; la propia pieza
duda del flag (`--webpack` o `--no-turbopack`). La aportación útil para el
plugin es una regla de **revisión**: no marcar como error una convención de
ficheros que depende de la versión del framework (`proxy.ts` en Next.js 16)
sin comprobar la versión en el manifiesto. Encaja con la selección por
manifiesto y versión mínima que ya hace `stack-practices`. La afirmación de
que renombrar a `middleware.ts` «romperá» el middleware no se contrastó en
esta lectura y la pieza no cita la nota de versión que la respalde.

**Destino:** una línea en `stack-practices/references/react.md`
(frameworks híbridos): verificar la convención de ficheros y rutas en la
versión real del framework antes de proponer renombrar.

## S191 — Nuxt 4

`4.761 bytes/101 líneas`. Hidratación segura, `useFetch`/`useAsyncData`,
`routeRules` por grupo de rutas, carga e hidratación perezosas.

**Comparación.** Vue/Nuxt no es un stack declarado; igual que con Java (S145) o
.NET (S086), **no se abre especialidad** hasta que un consumidor lo declare. Dos
ideas son generales y valen también para Next.js y React con SSR: el primer
render debe ser determinista (sin `Date.now()`, aleatorios, almacenamiento del
navegador ni fragmento de URL en el marcado del servidor), y la estrategia de
render y caché se elige por grupo de rutas, no globalmente. Correcciones para
cuando haya consumidor:

| Ejemplo | Adaptación |
|---|---|
| `'/api/**': { cache: { maxAge: 3600 } }` | Si la respuesta depende del usuario o del tenant, una caché compartida puede servir datos de uno a otro; cachear solo respuestas públicas o variar la clave por identidad |
| `'/admin/**': { ssr: false }` | Renderizar en cliente no protege nada; la autorización sigue en el servidor (backend-practices) |
| `useAsyncData` «sin efectos laterales» | Correcto y conviene conservarlo: puede ejecutarse en servidor e hidratación |

**Destino:** la línea de render inicial determinista en la fila «Cliente y
servidor en framework híbrido» de `stack-practices/references/react.md`. El
resto, **sin destino** hasta que un consumidor declare Vue/Nuxt.
