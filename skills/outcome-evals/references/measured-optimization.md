# Optimización por variantes medidas

Léela solo cuando se pida optimizar una operación concreta (un hotspot, una consulta, un build)
probando variantes contra un baseline, dentro de un límite. La medida se fija con
[baselines de rendimiento](performance-baselines.md); aquí, cómo buscar, rechazar, promover y parar.
La tabla resultante es **evidencia adjunta** de la tarea `T-XX` en el ledger, no otro gestor de
tareas.

## Contrato antes de la primera variante

| Campo | Regla |
|---|---|
| Operación | Una sola, con su entrada representativa y su forma (tamaño, tipos) fijadas |
| Gate de corrección | Tests o script que deben seguir verdes en cada variante; no se relajan para ganar tiempo |
| Métrica y dirección | Qué se optimiza y hacia dónde: minimizar tiempo, memoria o coste, o maximizar throughput; las demás restricciones se declaran como límites |
| Baseline | Medido con el mismo comando y condiciones que las variantes |
| Presupuesto | Máximo de variantes, tiempo y, si aplica, tokens o €; si el consumo no se puede medir, el tope no se declara aplicado |
| Empate | Diferencia mínima que cuenta como mejora, a partir del ruido medido en el baseline |

Sin métrica o gate ejecutable, completa el contrato y deja la búsqueda pendiente; no se optimiza
a ojo.

## Cada variante

- **Una hipótesis por variante** («el coste está en serializar dos veces»), en una rama o commit
  propio para poder volver atrás.
- Misma entrada, mismo comando, mismas condiciones que el baseline.
- Se **descarta** si rompe el gate, si es insegura (quita validaciones, comparte estado mutable sin
  control) o si su resultado no se reproduce al repetirla.

## Tabla de evidencia

| Variante | Hipótesis | Comando | Métrica (mediana, n) | Corrección | Notas |
|---|---|---|---|---|---|
| baseline | — | `<comando>` | 412 ms, n=30 | verde | ruido ±9 ms |
| v1 | Evita la doble serialización | `<comando>` | 301 ms, n=30 | verde | candidata |
| v2 | Caché en memoria del índice | `<comando>` | 120 ms, n=30 | **rojo** (test de invalidación) | descartada |

Toda variante probada entra en la tabla, también las descartadas: es lo que evita repetirlas.

## Promoción

1. La mejor variante **válida** se vuelve a medir contra el baseline, alternando el orden, con el
   mismo calentamiento y estado de caché.
2. Si el caso lo permite, se valida con datos distintos de los usados para elegirla: elegir entre
   muchas variantes favorece la que tuvo suerte con el ruido.
3. Solo se promueve si la mejora supera el umbral de empate en la repetición. Dentro del ruido, se
   queda el baseline (o la variante más simple).

## Parada

Se para la búsqueda cuando ocurre lo primero de esto: presupuesto agotado, el ruido es mayor que el
efecto buscado, varias variantes seguidas fallan el gate, o la mejora alcanza el objetivo declarado.
Terminar la búsqueda no prueba cumplido el objetivo de producto; eso lo dice su criterio.

## Cierre

Documenta en la evidencia de la tarea: variante ganadora y su hipótesis, tabla completa, comandos,
condiciones, límites («medido en laboratorio con n=30») y el **rollback** (commit o rama a revertir).
El resultado es la mejor variante válida encontrada dentro del presupuesto, nunca «el óptimo».
