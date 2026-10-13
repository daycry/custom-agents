# Interacción, accesibilidad y coste visible

## Contratos que se prueban con acciones del usuario

Usa controles HTML nativos antes de reproducirlos con ARIA. Comprueba nombre
accesible, etiqueta asociada, orden de tabulación y foco visible. Un icono con
tooltip visual necesita un nombre accesible independiente del hover. Un estado
deshabilitado debe explicar cuándo volverá a estar disponible.

| Cambio | Caso obligatorio pertinente |
|---|---|
| Modal/dialog | Abrir con teclado, foco inicial útil, Escape según contrato, foco vuelve al disparador y fondo no interactivo. Prefiere `<dialog>` nativo abierto con `showModal()`: deja inerte el resto del documento y convierte la petición de cierre (Escape en escritorio) en evento `cancel`. Un `div` con `role="dialog"` y `aria-modal` no bloquea el fondo por sí solo: exige el patrón WAI completo |
| Formulario | Envío con teclado, errores asociados al campo, resumen/navegación a errores y datos conservados tras fallo. Anuncio agregado: un resumen enlazado o una única región `aria-live`; `role="alert"` en cada campo anuncia todos los errores a la vez |
| Área de pulsación | Cada objetivo de puntero mide al menos 24×24 CSS px (WCAG 2.2, 2.5.8 AA, con sus excepciones de espaciado, equivalente, en línea, control del navegador y esencial) o 44×44 (2.5.5 AAA) si el proyecto lo fija; mide el área activa, no el icono |
| Animación | Cada animación declara su propósito (guiar la atención, comunicar estado, continuidad espacial) o se elimina; anima solo `transform`/`opacity`, no propiedades de layout. Movimiento reducido aplicado también a hover/tap y antes del primer render; las animaciones infinitas se pausan con la pestaña oculta; lo que se hace arrastrando tiene alternativa de un solo puntero y teclado (2.5.7); el contenido colapsado queda oculto (`hidden`/`inert`), no solo escalado, y no recibe foco |
| Ruta o contenido sustituido | Foco y título útiles tras navegación; historial atrás/adelante conserva lo esperado |
| Carga remota | Loading, vacío, error, reintento y éxito distinguibles; respuesta antigua no reemplaza la nueva |
| Mutación optimista | Fallo recupera el estado coherente y permite reintentar sin duplicar la operación |
| Buscador y filtros | Resultado y contador coherentes, reset completo y anuncio de cambios sin interrumpir cada tecla |
| Layout | Viewport estrecho y zoom; sin pérdida de acciones por overflow; contenido largo e idioma distinto |

Combina checker automatizado con teclado real y revisión visual. Un contador
de reglas aprobadas no mide cobertura de WCAG; registra reglas/herramienta y
pruebas manuales concretas. Respeta preferencias de movimiento y contraste.

## Rendimiento que justifica un cambio

Mide un escenario reproducible antes/después: dispositivo, caché, red, versión,
datos, interacciones y profiler. Localiza si el coste es red, payload, código
cliente, render o layout. Evita memoizar cada componente por intuición.

Reserva tamaños para medios; carga solo recursos necesarios para la vista;
no envíes secretos ni imports de servidor al navegador. Revisa waterfall,
duplicación de peticiones y bundles de rutas. Virtualizar requiere medir el
beneficio y comprobar foco, lectura y navegación: no lo prescribas por un número
fijo de filas. Declara presupuestos con el producto y el dispositivo objetivo;
una medición en desktop no demuestra mejora móvil.

Fuentes: [WAI patterns](https://www.w3.org/WAI/ARIA/apg/patterns/),
[WCAG 2.2](https://www.w3.org/TR/WCAG22/),
[HTML `dialog`](https://html.spec.whatwg.org/multipage/interactive-elements.html#the-dialog-element),
[React profiler](https://react.dev/reference/react/Profiler).
Consulta el patrón específico y las APIs de la versión usada.
