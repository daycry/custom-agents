# Ejecución por unidades, registro de decisiones y doble revisión — S227, S233 y S244

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Tres cuerpos completos: **17.631 bytes/456 líneas**, sin recursos locales.
[rfc-dag-ledger-santa-reading-evidence.json](rfc-dag-ledger-santa-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08.

## S227 — De RFC a un grafo de unidades con cola de integración

`1.837 bytes/68 líneas`. Descomponer un RFC en unidades con dependencias,
pruebas de aceptación, nivel de riesgo y plan de vuelta atrás; cada unidad pasa
por investigación, plan, implementación, pruebas y revisión; se integran por una
cola con rebase y pruebas tras cada integración.

**Comparación.** El plugin ya hace esto con dueños: `planner` corta en tareas con
`Dependencias`, `Archivos` y `Verificación` obligatoria; `/dev-cycle` con
`subagentes: true` despacha lotes paralelos de hasta 3 tareas en worktrees
temporales, valida cada retorno y reintegra en la rama de la iniciativa; ADR-022
fija el rigor por nivel de riesgo. Lo que aporta de verdad:

| Idea | Encaje |
|---|---|
| Repetir las pruebas de integración **después de cada** integración de la cola | `/dev-cycle`, paso 6 del despacho paralelo: valida cada retorno contra sus criterios, pero no dice que se repita la `Verificación` de lo ya integrado. Añadir: tras reintegrar cada tarea del lote, volver a ejecutar la `Verificación` de las tareas del lote ya integradas; rojo o conflicto → esa tarea pasa a secuencial |
| Plan de vuelta atrás por unidad | No como campo nuevo (coste en cada tarea); la reversibilidad ya la compara `architect` y el rigor lo fija ADR-022 |

Defectos: «reintentar con restricciones actualizadas» no tiene tope (el plugin
acota a 3); «tarjetas de unidad» y los tres niveles no tienen criterio
verificable.

**Destino:** la línea en `/dev-cycle` (paso 6 del despacho paralelo).

## S233 — Registro de decisiones en rondas repetidas

`2.803 bytes/81 líneas`. Rondas repetidas con un registro en solo-añadir
(JSONL): ganador previo, información nueva, candidatos, marcas, coherencia con
la ronda anterior y una puerta de promoción. «La confianza recursiva no es
aprobación»: modo papel o ensayo salvo aprobación explícita.

**Comparación.** La doctrina coincide con la del plugin (un juicio del modelo no
es veredicto; las puertas son scripts y la aprobación es humana) y
`outcome-evals` ya compara resultados con corpus y condiciones declaradas. Aporta
una idea menor ya implícita en `outcome-evals`: comparar contra el ganador
previo **aceptado** con la misma métrica antes de promover.

Defectos: «recuento efectivo de ensayos» y la «marca de coherencia» no se
definen; el resumen de ejemplo («la ventaja se deterioró un 17 %») es una cifra
ilustrativa sin cálculo; sus disparadores («búsqueda en alta dimensión»,
«optimización estocástica») son tan amplios que colisionarían.

**Sin destino.**

## S244 — Doble revisión independiente con bucle de corrección

`12.991 bytes/307 líneas`. Generador, dos revisores con la misma rúbrica y sin
contexto compartido, puerta «ambos aprueban», bucle de corrección con tope de
3 y escalado humano; muestreo para lotes y métricas.

**Comparación.** `adversarial-review` es el dueño y va más lejos:

| Esta pieza | `adversarial-review` |
|---|---|
| Dos revisores con la misma rúbrica | Lentes distintas a propósito (A conformidad, B corrección, C y D condicionales); misma rúbrica y mismo modelo comparten sesgos, como admite la propia pieza en «sesgo de acuerdo» |
| «Si solo uno lo señala, es real» | Los revisores también se equivocan: rebate con evidencia y arbitraje (§4) |
| Revisores nuevos sin memoria en cada ronda | Traspaso de la tabla del intento anterior para no reabrir lo aprobado ni lo rebatido (§5) |
| Rúbrica de contenido (marca, SEO, avisos legales) | Fuera del ciclo; la prosa del plugin la revisa la lente A con `docs-style` |

Defectos en el código: `santa_verdict` devuelve la cadena `"NICE"` en el caso
bueno y una tupla en el malo, y el bucle desempaqueta tres valores: falla
justo cuando se aprueba. Tras la tercera corrección se relanzan los revisores y
el resultado no se evalúa: escala aunque la última revisión apruebe.
`santa_batch` se llama a sí misma sin tope y `random.sample` falla con menos de
cinco elementos. «Cuesta un 15–20 % y caza más del 90 %» no tiene fuente.

**Sin destino.**
