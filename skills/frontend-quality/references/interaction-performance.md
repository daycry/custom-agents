# Interacción, accesibilidad y coste visible

## Contratos que se prueban con acciones del usuario

Usa controles HTML nativos antes de reproducirlos con ARIA. Comprueba nombre
accesible, etiqueta asociada, orden de tabulación y foco visible. Un icono con
tooltip visual necesita un nombre accesible independiente del hover. Un estado
deshabilitado debe explicar cuándo volverá a estar disponible.

| Cambio | Caso obligatorio pertinente |
|---|---|
| Modal/dialog | Abrir con teclado, foco inicial útil, Escape según contrato, foco vuelve al disparador y fondo no interactivo |
| Formulario | Envío con teclado, errores asociados al campo, resumen/navegación a errores y datos conservados tras fallo |
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
[React profiler](https://react.dev/reference/react/Profiler).
Consulta el patrón específico y las APIs de la versión usada.
