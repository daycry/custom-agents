# T-17: resolución shared una vez por pieza

Decisión **no-go para el cambio productivo** después de T-13, 2026-10-30.
T-17 se cancela conforme a su condición de ahorro positivo y resolución segura.
No se han cambiado prompts, búsquedas, linter ni adaptadores para esta propuesta.

El inventario concreto encuentra 24 asignaciones `SHAREDKIT=find` en 20 piezas
del alcance. Solo tres tienen duplicación local: implementer (3), documenter (2)
y setup (2). El núcleo de dev-cycle y su referencia de subagentes tienen una
cada uno. No se atribuyen automáticamente los ~80 casos o ~1.200 tokens del
esqueleto histórico al readset actual.

Se mide un candidato conservador: una búsqueda original completa por pieza,
instrucciones para guardar procedencia/ruta y degradar sin kit, y una asignación
explícita de esa ruta observada donde antes se repetía la búsqueda. Conserva las
seis raíces y la exclusión de jobs de setup; no presupone que una variable shell
sobreviva a otra herramienta. El recibo [JSON](t17-resolution-decision.json)
contiene política, construcción exacta, hashes y estimación por pieza.

| Readset ilustrativo | Delta estimado del candidato |
|---|---:|
| Vía rápida: núcleo, implementer, qa, documenter y capacidad común | +270 |
| Flujo completo: añade evaluator y planner | +420 |
| Solo las tres piezas con duplicados locales | +77 |

Son `ceil(caracteres/4)`, no tokens API ni consumo completo del ciclo. Los
fragmentos sin cambios se cancelan en la comparación. Ni siquiera el subconjunto
con duplicados ahorra con este candidato; por tanto no cumple la condición del
plan. Se conserva la resolución actual y no se debilita para forzar una cifra.

Esto no prueba que todo diseño futuro más corto sea imposible. Un fragmento
común podría repartir el coste, pero exigiría definir y validar su carga,
procedencia, instalaciones parciales y readsets reales antes de afirmar ahorro.
No se introduce ese contrato transversal solo para rescatar la estimación
histórica. Los fallbacks existentes y las ocho recetas visuales privadas de T-13
se conservan. Las cuatro pruebas de lookup del kit privado en Bash/PowerShell
pasan en 7,97 s; comprueban esa ruta existente, no una implementación shared nueva.
TDD n/a: decisión condicional sin cambio productivo; no nace la suite propuesta
para una implementación que se ha cancelado.
