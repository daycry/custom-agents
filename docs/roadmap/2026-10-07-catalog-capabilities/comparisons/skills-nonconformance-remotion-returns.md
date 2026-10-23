# Calidad en fabricación, vídeo con Remotion y devoluciones — S221, S236 y S239

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Tres cuerpos completos: **58.571 bytes/529 líneas**, más los 31 recursos de S236
(28 reglas y 3 ejemplos `.tsx`, 74.417 bytes/3.079 líneas), leídos completos.
[nonconformance-remotion-returns-reading-evidence.json](nonconformance-remotion-returns-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08.

## Decisión común

Tres dominios ajenos al ciclo de desarrollo: fabricación regulada, logística
inversa de comercio y producción de vídeo. **Fuera del bundle**; «persona de
proyecto» si un consumidor los necesita. Solo una idea de S221 llega a una
pieza propia.

## S221 — Calidad y no conformidades en fabricación regulada

`30.261 bytes/253 líneas`. Ciclo de la no conformidad (identificar, contener,
documentar, disponer por comité), análisis de causa raíz (5 porqués, Ishikawa,
árbol de fallos, 8D), acciones correctivas y preventivas, control estadístico,
muestreo de aceptación, gestión de proveedores, escalados con plazos e
indicadores.

**Comparación.** El método de causa raíz coincide con `debug-root-cause`
(hipótesis falsable probada antes de arreglar). La pieza aporta dos matices:

| Idea | Encaje |
|---|---|
| Cada «porqué» se verifica con datos; «error humano» o «reentrenar» no son causa raíz | Ya cubierto: Fase 3 exige hipótesis probada. Sin cambio |
| Varias causas que interactúan: los 5 porqués fuerzan una cadena única y arreglar una sola reduce la frecuencia sin eliminar el fallo | `debug-root-cause` Fase 3 pide una sola frase «falla porque X hace Y cuando Z». Añadir una línea: si la evidencia muestra una conjunción de causas, cada una se prueba por separado y lleva su test de regresión |
| Verificar que la acción se implantó no es validar que el fallo no vuelve; si reaparece, se reabre en vez de abrir otro expediente | Ya cubierto: `knowledge-write.md` obliga a enlazar la entrada existente sin duplicar; `/retro` recoge causas. Sin cambio |

Defectos: las reglas de «Western Electric» que cita (nueve puntos a un lado,
seis en tendencia, catorce alternos) son las de Nelson; las de Western Electric
son 2 de 3 más allá de 2σ, 4 de 5 más allá de 1σ y 8 seguidos a un lado. Cifras
sin fuente presentadas como norma («cada dólar en prevención devuelve 10–100»,
reparto del coste de calidad, objetivos de indicadores).

**Destino:** la línea de causas conjuntas en `debug-root-cause` (Fase 3). El
resto, **Fuera del bundle**.

## S239 — Devoluciones y logística inversa

`24.668 bytes/233 líneas`. Autorización de devoluciones, graduación A–D,
disposición por economía de recuperación, fraude, reclamaciones al proveedor y
garantías, con escalados e indicadores.

**Comparación.** Sin rol del ciclo que lo use. Defectos que impedirían reutilizar
su modelo de fraude incluso como persona de proyecto:

- «Puntúa cada devolución de 0 a 100» con umbrales 65/80, pero las señales de la
  tabla suman 145 puntos y no hay acotación. Además es un score aditivo de
  señales fijas convertido en retención de reembolso: un score no es un
  veredicto (doctrina del plugin).
- La fórmula de recuperación (crédito esperado × probabilidad frente a coste)
  queda anulada por la regla «por encima de 500 $, reclamar siempre».
- La lógica de excepciones acepta a cualquier cliente del 10 % superior,
  mientras el caso límite 6 pide segmentar al cliente de alto valor que abusa.

**Fuera del bundle.**

## S236 — Vídeo con Remotion

`3.642 bytes/43 líneas` más 31 recursos. Índice de reglas: toda animación sale de
`useCurrentFrame()` (prohibidas transiciones CSS y clases de animación),
recursos con `<Img>` y `staticFile()`, composiciones, premontaje de secuencias,
subtítulos, transiciones y lectura de metadatos con Mediabunny.

**Comparación.** `to-pdf` es la única pieza de render del plugin y no comparte
dominio. Para quien lo adopte como persona de proyecto, defectos concretos:

| Recurso | Defecto |
|---|---|
| `SKILL.md` | La descripción anuncia 29 reglas; el índice y el directorio tienen 28 |
| `rules/charts.md` | Enlaza `assets/charts/bar-chart.tsx`; el fichero es `assets/charts-bar-chart.tsx` |
| `rules/calculate-metadata.md` | Importa `getMediaMetadata` de `../get-media-metadata` «de la skill mediabunny/metadata», que no existe en la pieza; multiplica por 30 en vez de usar el `fps` de la composición (también `gifs.md`) |
| `rules/timing.md` | `const spring = spring({...})` usa la variable antes de declararla; el ejemplo de retardo resta `ENTRANCE_DELAY` al frame y además pasa `delay: 20` |
| `rules/videos.md` | Dice que `trimBefore`/`trimAfter` van en segundos y el ejemplo multiplica por `fps`; `audio.md` dice frames |
| `rules/trimming.md` | `const fps = useVideoConfig()` asigna el objeto, no el número: `-0.5 * fps` da `NaN` |
| `rules/can-decode.md` | `canDecodeBlob` deja el cuerpo en un comentario y no devuelve nada |
| `rules/tailwind.md` | Ordena consultar la documentación remota en cada uso en lugar de fijar versión |

**Fuera del bundle.**
