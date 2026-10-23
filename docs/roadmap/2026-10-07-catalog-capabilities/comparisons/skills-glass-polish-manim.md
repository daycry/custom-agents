# Liquid Glass, pulido de interfaz y vídeos con Manim — S162, S168, S169

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Tres cuerpos completos: **16.820 bytes/521 líneas** y el recurso de S169
(`assets/network_graph_scene.py`, 2.897 bytes/52 líneas).
[glass-polish-manim-reading-evidence.json](glass-polish-manim-reading-evidence.json).
Nada se ejecutó, compiló ni renderizó. Propuestas para T-08.

## S162 — Liquid Glass (iOS 26)

`9.119 bytes/279 líneas`. Material de vidrio en SwiftUI (`glassEffect`,
contenedores, uniones, transiciones con `glassEffectID`), UIKit
(`UIGlassEffect`, efectos de borde de scroll) y WidgetKit (modo acentuado).

**Comparación.** API de una plataforma sin consumidor, como S105
(FoundationModels) y S139 (iconos iOS). **Fuera del bundle**; especialidad de
proyecto si alguien desarrolla para iOS. Las APIs no se contrastaron con la
documentación de Apple. Lo general ya está en `frontend-quality` («respeta
preferencias de movimiento y contraste»); la pieza pide contraste legible sobre
el vidrio pero no menciona las preferencias de accesibilidad del sistema
(transparencia y movimiento reducidos) ni cómo se prueban. «Usa siempre
`GlassEffectContainer`» es un absoluto que la propia tabla de decisiones
justifica solo por rendimiento y transiciones.

## S168 — Detalles que hacen que una interfaz se sienta mejor

`4.795 bytes/152 líneas`. Radios concéntricos, alineación óptica, sombras frente
a bordes, `text-wrap`, cifras tabulares, contorno de imágenes, movimiento
interrumpible, alcance de `transition`, áreas de pulsación y formato de revisión
antes/después.

**Comparación.** `frontend-quality` cubre teclado, foco, estados y rendimiento
medido, no acabado visual. S107 propuso una sección «dirección visual» en esa
skill junto a la de S075–S077; esta pieza aporta criterios verificables para
ella:

| Idea | Encaje |
|---|---|
| Cifras que cambian (contadores, precios, tablas) con `tabular-nums` para que no salte el layout | Sección «dirección visual» |
| `transition` con propiedades explícitas, nunca `all`; `will-change` solo para el primer fotograma | Misma sección y «Rendimiento que justifica un cambio» |
| Salida más corta que la entrada; transiciones interrumpibles para estados interactivos | Sección «dirección visual» |
| Revisión como tabla principio / antes / después con fichero y propiedad, omitiendo lo comprobado sin cambio | Formato de salida de esa sección, sin abrir otra revisión |

Correcciones:

| Ejemplo | Corrección |
|---|---|
| Área de pulsación mínima de 40×40 px, ideal 44×44 | La referencia citable es WCAG 2.2: 24×24 CSS px como mínimo (2.5.8, AA) y 44×44 (2.5.5, AAA). 40 no corresponde a ninguno; usar el umbral que fije el proyecto |
| `-webkit-font-smoothing: antialiased` global | Decisión de estilo solo efectiva en macOS, no criterio de calidad |
| `img { outline: … }` global | Afecta también a logos e iconos con transparencia; acotar a fotografías |
| `scale(0.96)` y desenfoque en entradas | Respetar `prefers-reduced-motion`; el desenfoque sobre áreas grandes tiene coste de render, que hay que medir |
| Procedencia: «rescatado de un PR comunitario abandonado» | Sin autor contrastable; adoptar solo lo verificable |

**Destino:** las cuatro filas de ideas en la sección «dirección visual»
propuesta para `frontend-quality` (S107), y una fila de área de pulsación con el
umbral WCAG en la tabla de `references/interaction-performance.md`.

## S169 — Vídeos explicativos con Manim

`2.906 bytes/90 líneas` más la escena de ejemplo. Tesis visual en una frase,
3–6 escenas que prueban una cosa cada una, render de humo en baja calidad y
traspaso a otras piezas de vídeo.

**Comparación.** Ningún rol del ciclo produce vídeo, como S100.
**Fuera del bundle.** Sus reglas de método («una escena demuestra una cosa»,
«primero la versión mínima que renderiza») son las generales de cualquier
entrega incremental. La escena de ejemplo tiene un defecto: el desplazamiento
final mueve el grupo de nodos pero no las flechas, que no están en ese `VGroup`,
y quedan desplazadas respecto a los nodos. El título de la escena es el de otra
pieza del corpus de contactos sociales, no un ejemplo neutro. **Sin destino.**
