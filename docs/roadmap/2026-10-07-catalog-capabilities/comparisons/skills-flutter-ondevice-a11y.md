# Revisión Flutter, modelos en el dispositivo y accesibilidad React — S104–S106

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Tres cuerpos completos: **44.310 bytes/1.122 líneas**, sin recursos locales.
[flutter-ondevice-a11y-reading-evidence.json](flutter-ondevice-a11y-reading-evidence.json)
registra fuentes y contrapartes. Nada se ejecutó ni se integró. Propuestas para T-08.

## S104 — Checklist de revisión Flutter/Dart

`23.194 bytes/436 líneas`. Quince bloques de revisión independientes de la
librería de estado: salud del proyecto, Dart, widgets, estado, rendimiento,
tests, accesibilidad, plataforma, seguridad, paquetes, navegación, errores,
l10n, inyección de dependencias y análisis estático, más tabla por librería.

**Comparación.** S067 (bloque de comercio, Flutter y dashboards) ya propuso la
especialidad opcional Flutter y señaló que `const`, selectores o extracción de
widgets deben justificarse midiendo frames, no por regla. S104 es el
complemento de revisión de esa misma especialidad.

| Afirmación | Adaptación |
|---|---|
| «Ningún `build()` de más de 80-100 líneas» y extraer siempre `_build*()` | Heurística; la extracción se justifica por límites de reconstrucción medidos (criterio ya fijado en S067) |
| «80 % de cobertura en lógica de negocio» | Umbral del proyecto vía `tests.coberturaMinima`, no universal |
| Puntos de pub.dev, likes y popularidad como señal | research-first: la popularidad no acredita adecuación; contrastar licencia, mantenimiento y plataforma |
| «Adjuntar el ID de usuario a los informes de error» | Dato personal en un tercero; requiere base legal y redacción según el proyecto |
| `pumpAndSettle` contra tests inestables | Puede colgarse con animaciones infinitas; `pump(Duration)` explícito |
| Fijado de certificados «a considerar» | Implica plan de rotación; sin él, una renovación deja la app sin red |
| Contraste ≥ 4,5:1 y objetivos de 48×48 | **Conservar**: coinciden con las guías de plataforma y con frontend-quality |
| `BuildContext` tras `await` sin `context.mounted` | **Conservar**: defecto real y frecuente |

**Destino.** `flutter-practices/references/review.md` en la especialidad opcional
de S067; la lente B de `adversarial-review` la lee solo con stack Flutter declarado.

## S105 — Modelo de lenguaje en el dispositivo con FoundationModels (iOS)

`8.255 bytes/243 líneas`. Disponibilidad, sesiones, generación guiada con
`@Generable`, herramientas y streaming de instantáneas.

**Comparación.** API de una plataforma concreta (iOS 26+) sin consumidor en el
plugin ni en los stacks declarados (PHP/CodeIgniter, Python, React). La pieza
cita un tope de contexto de 4.096 tokens y comportamientos de sesión que
dependen de la versión del SO; no se contrastaron. El criterio general (comprobar
disponibilidad del modelo antes de ofrecer la función y degradar con aviso)
ya es la regla «degradación, no bloqueo» del plugin. **Fuera del bundle**;
especialidad de proyecto si un consumidor desarrolla para iOS.

## S106 — Accesibilidad en React y Next.js

`12.861 bytes/443 líneas`. Etiquetas, errores enlazados, HTML semántico, ARIA,
teclado, foco en modales, imágenes, movimiento reducido y antipatrones.

**Comparación.** `frontend-quality/references/interaction-performance.md` fija los
criterios observables (controles nativos antes que ARIA, nombre accesible, foco
visible, modal con foco inicial y retorno, Escape) con los patrones WAI como
fuente. S106 aporta ejemplos de código, varios con defectos:

| Ejemplo | Adaptación |
|---|---|
| Combobox propio sobre un `div` con `role="combobox"` | Sin `aria-activedescendant` ni id de opciones, el lector no anuncia la opción activa; preferir `<select>` nativo o seguir el patrón WAI completo |
| Modal: foco al contenedor sin trampa de Tab, remitida a una librería | El fondo sigue siendo interactivo; `<dialog>` nativo con `showModal()` resuelve inercia y Escape |
| `role="alert"` en cada error de campo | Con varios errores se anuncian todos a la vez; resumen de errores o `aria-live` único |
| `required` y `aria-required="true"` a la vez | Redundante; `required` ya expone el estado |
| `alt=""` junto con `aria-hidden="true"` | Redundante; `alt=""` basta |
| `aria-live` asertivo para errores en un `role="status"` | `status` es implícitamente polite; mezclarlo confunde |
| `useReducedMotion` inicializado en `false` | Primer render con animación antes de leer la preferencia; preferir CSS `@media (prefers-reduced-motion)` |

**Destino.** Añadir dos casos a la tabla de frontend-quality (`<dialog>` nativo y
anuncio de errores agregado) y ejemplos React en `stack-practices/references/react.md`.
Contraste con los patrones WAI pendiente antes de integrar.
