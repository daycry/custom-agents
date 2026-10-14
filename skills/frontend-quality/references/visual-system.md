# Dirección visual y sistema de tokens

Léela solo cuando la tarea extraiga, normalice o revise tokens, estilos o el
acabado visual de una interfaz. Foco, teclado, área de pulsación y animación
accesible están en [interacción y rendimiento](interaction-performance.md);
contraste y alternativas al color, en [criterios de accesibilidad](accessibility-criteria.md).

## Antes de crear nada

Fija propósito, audiencia, tono y restricciones de la pantalla antes de
programar. Usa los tokens, componentes e iconos que ya existen antes de crear
otros: un componente nuevo que copia uno existente con otro radio es deuda, no
estilo. Comprueba el estilo de los iconos presentes (trazo, relleno, tamaño)
antes de añadir uno. Una herramienta de uso diario se diseña densa y
escaneable; no añadas dependencias por adorno. El texto cabe en móvil y en
escritorio con contenido largo e idioma distinto.

Gradientes, transparencias, tipografías o colores no son defectos por sí
mismos: valora legibilidad, jerarquía, intención y la preferencia del producto.
No sustituyas la identidad del producto por un preset universal ni exijas modo
oscuro si no está en el alcance.

## Extraer, proponer y aprobar son tres estados

| Estado | Qué contiene | Quién lo fija |
|---|---|---|
| Extracción observada | Valores tal como aparecen, con procedencia: regla CSS, componente y tema donde se usan, variable ya resuelta y override que la pisa | Quien audita; es un inventario, no una decisión |
| Normalización propuesta | Agrupación de valores en tokens con su rationale (uso semántico, no frecuencia) | architect si hay alternativas de diseño; si no, implementer en su tarea |
| Estilo aprobado | Lo que el usuario o el producto acepta | El usuario; documenter recoge el rationale |

Una frecuencia no es una decisión: el mismo hex puede tener dos usos semánticos
(texto secundario y borde) y dos valores distintos pueden ser deliberados por
estado o tema. Conserva la procedencia en cada token propuesto para poder
deshacer la agrupación.

Los tokens, estilos y vista previa viven en las rutas que ya use el proyecto o
en un área de documentación acordada con el usuario; no crees ficheros vacíos
por si acaso. Este sistema visual no es el `design.md` de arquitectura.

## Tokens y CSS que se comprueban

- **Formato.** Un JSON con nombres de token no es por sí un formato
  interoperable. El formato del Design Tokens Community Group (2025.10) define
  tipos, valores y referencias, y trata una referencia circular como error; es
  un informe de grupo comunitario, no un estándar W3C. Adóptalo solo si el
  proyecto lo necesita para sus herramientas.
- **Custom properties.** Heredan por cascada desde el elemento donde se
  declaran; no son variables globales. `var()` solo sirve en valores de
  propiedades: no funciona en media queries ni container queries. Un `var()`
  inválido en el punto de uso no cae en la declaración anterior, sino en el
  valor heredado o inicial; el fallback solo cubre una variable ausente o
  inválida. Prueba estilos computados en cada tema, no el texto generado.
- **Negar un `clamp()`.** `-clamp(...)` no es un `clamp()` negado: se lee como
  una función desconocida y la declaración se descarta sin aviso. Usa
  `calc(-1 * clamp(...))`.
- **Cifras que cambian** (contadores, precios, columnas de tablas):
  `font-variant-numeric: tabular-nums` para que el ancho no salte al cambiar
  el valor.
- **`transition` con propiedades explícitas**, nunca `all`: `all` anima también
  propiedades de layout que cambian por otro motivo. `will-change` es un último
  recurso ante un problema medido, no una declaración permanente.
- **Movimiento.** La salida de un elemento dura menos que su entrada; un estado
  interactivo (hover, despliegue) admite interrumpir la transición a medias sin
  saltar. Escalados y desenfoques respetan `prefers-reduced-motion`; un
  desenfoque sobre un área grande tiene coste de render que hay que medir.
- **Reglas globales con alcance.** Un contorno o sombra para imágenes se acota a
  fotografías: aplicado a todo `img` alcanza logos e iconos transparentes. El
  suavizado de fuentes por prefijo de motor es una decisión de estilo con efecto
  solo en algunos sistemas, no un criterio de calidad.

## Vista previa del sistema

La vista previa usa la misma fuente y versión de tokens que la aplicación,
controles accesibles y estados reales (carga, error, deshabilitado, foco), no
solo un mosaico de tarjetas. Escapa nombres, valores y contenido antes de
insertarlos en HTML o CSS; no cargues recursos externos no pedidos. Casos que
la ponen a prueba: alias ausente o circular, valor CSS inválido con fallback,
mismo color con dos semánticas, tema alternativo, viewport estrecho, zoom,
teclado y movimiento reducido. Sin navegador disponible, entrega la propuesta
estática y di qué no se ha visto renderizado.

Una puntuación visual (p. ej. de 0 a 10) es una rúbrica editorial: ancla cada
nota a un ejemplo y marca `n/a` lo que no aplica. No mide el área de pulsación
de WCAG ni certifica conformidad.

## Formato de la revisión

Una fila por cambio propuesto; omite lo que comprobaste y no cambia.

| Principio | Antes (fichero y propiedad) | Después |
|---|---|---|
| Cifras estables | `Price.css` `.amount` sin `font-variant-numeric` | `font-variant-numeric: tabular-nums` |
| Transición acotada | `Card.css` `transition: all 200ms` | `transition: opacity 200ms, transform 200ms` |

Fuentes, consultadas el 2026-10-14:
[DTCG Format 2025.10](https://www.designtokens.org/tr/2025.10/format/),
[MDN custom properties](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Cascading_variables/Using_custom_properties),
[CSS Syntax 3, tokenización de funciones](https://www.w3.org/TR/css-syntax-3/),
[MDN `clamp()`](https://developer.mozilla.org/en-US/docs/Web/CSS/clamp),
[MDN `font-variant-numeric`](https://developer.mozilla.org/en-US/docs/Web/CSS/font-variant-numeric),
[MDN `will-change`](https://developer.mozilla.org/en-US/docs/Web/CSS/will-change).
