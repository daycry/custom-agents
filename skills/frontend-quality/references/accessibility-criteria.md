# Criterios web de accesibilidad (WCAG 2.2)

Léela solo cuando la tarea tenga que citar un criterio concreto: diseñar o
revisar contraste, color, nombres de controles, alternativas al arrastre,
errores de formulario o mensajes de estado. Los casos que se prueban con
acciones del usuario (modal, formulario, área de pulsación, animación, ruta)
están en [interacción y rendimiento](interaction-performance.md); aquí solo
el criterio y su umbral. La forma React/HTML de cada patrón está en
`stack-practices` (referencia React).

## Mapa de criterios

| Necesidad | Criterio (nivel) | Qué se comprueba |
|---|---|---|
| Contraste de texto | 1.4.3 Contraste mínimo (AA) | 4.5:1 en texto normal; 3:1 en texto grande (≥ 18 pt, o ≥ 14 pt en negrita). Logotipos y texto incidental, exentos |
| Contraste de controles y gráficos | 1.4.11 Contraste no textual (AA) | 3:1 contra los colores adyacentes para bordes de campos, iconos que actúan y cada estado (foco, seleccionado) |
| Alternativa al color | 1.4.1 Uso del color (A) | Error, estado o serie de un gráfico se distinguen también por texto, icono o patrón |
| Iconos y controles sin texto | 1.1.1 Contenido no textual (A) · 4.1.2 Nombre, rol, valor (A) | Cada botón de icono tiene nombre accesible; un icono decorativo queda oculto a la tecnología de apoyo |
| Etiqueta visible y nombre | 2.5.3 Etiqueta en el nombre (A) | El nombre accesible contiene el texto visible del control, para que el control por voz lo encuentre |
| Arrastrar | 2.5.7 Movimientos de arrastre (AA) | Lo que se hace arrastrando se puede hacer con un solo puntero sin arrastrar, salvo que el arrastre sea esencial o lo resuelva el navegador |
| Teclado y trampas | 2.1.1 Teclado (A) · 2.1.2 Sin trampa de teclado (A) | Todo se opera con teclado y el foco puede salir de cada componente |
| Orden y visibilidad del foco | 2.4.3 Orden del foco (A) · 2.4.7 Foco visible (AA) · 2.4.11 Foco no oculto, mínimo (AA) | Orden lógico; indicador visible; una cabecera o banner fijo no tapa entero el elemento enfocado. 2.4.13 Apariencia del foco es AAA: solo si el proyecto lo fija |
| Cierre de modal y retorno del foco | 2.4.3 (A) · 2.1.2 (A) | Ver la fila «Modal/dialog» de [interacción y rendimiento](interaction-performance.md) |
| Etiquetas e instrucciones | 3.3.2 Etiquetas o instrucciones (A) | Cada entrada tiene etiqueta y, si hay formato, se dice antes de escribir, no solo en el `placeholder` |
| Identificar el error | 3.3.1 Identificación de errores (A) | El campo erróneo se señala y el error se describe en texto |
| Ayuda para corregirlo | 3.3.3 Sugerencia ante errores (AA) | Si se conoce la corrección, se ofrece («usa el formato AAAA-MM-DD»), salvo que comprometa la seguridad o el propósito |
| No volver a pedir lo dado | 3.3.7 Entrada redundante (A) | Un dato ya introducido en el mismo proceso se rellena o se puede elegir, salvo que sea esencial, de seguridad o haya caducado |
| Acceso sin prueba cognitiva | 3.3.8 Autenticación accesible, mínima (AA) | El login no exige recordar ni transcribir sin ayuda: pegar y los gestores de contraseñas funcionan |
| Anuncios de estado | 4.1.3 Mensajes de estado (AA) | «Guardado», «3 resultados» o «subiendo» se anuncian sin mover el foco (`role="status"` o una región viva) |
| Ampliar y reajustar | 1.4.4 Cambio de tamaño del texto (AA) · 1.4.10 Reflujo (AA) · 1.4.12 Espaciado de texto (AA) | Texto al 200 % sin perder contenido; a 320 CSS px de ancho sin scroll horizontal, salvo contenido que necesita dos dimensiones (tablas, mapas); espaciado ampliado sin recortes |
| Contenido al pasar o enfocar | 1.4.13 Contenido con hover o foco (AA) | Un tooltip se puede cerrar sin mover el puntero, se puede recorrer con el puntero y no desaparece solo |
| Ayuda localizable | 3.2.6 Ayuda consistente (A) | Si hay ayuda en varias páginas, aparece en el mismo orden relativo |

4.1.1 Análisis sintáctico está obsoleto y retirado en WCAG 2.2; solo se informa
si una política del proyecto cita WCAG 2.0 o 2.1.

## Cómo usar el mapa

- Cita el criterio con su número y nivel en el escenario del test-plan; el
  nivel objetivo (A, AA) lo fija el proyecto, no esta guía.
- Un criterio con excepciones (2.5.7, 2.5.8, 1.4.10, 3.3.7) no se reduce a una
  regla absoluta: registra qué excepción aplicas y por qué.
- Un checker automático cubre parte de 1.4.3, 1.1.1 o 4.1.2; teclado, orden del
  foco, foco oculto, reflujo, anuncios y sugerencias de error necesitan prueba
  manual o E2E. qa reporta los bloques A11Y aparte del umbral de su gate: un
  informe sin incidencias no acredita conformidad.
- Las correspondencias con plataformas nativas (iOS, Android) no están en esta
  referencia: verifica la API de cada SDK antes de trasladar un criterio web.

Fuentes, consultadas el 2026-10-14:
[WCAG 2.2](https://www.w3.org/TR/WCAG22/),
[Understanding 2.5.8](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html),
[WAI-ARIA APG patterns](https://www.w3.org/WAI/ARIA/apg/patterns/).
