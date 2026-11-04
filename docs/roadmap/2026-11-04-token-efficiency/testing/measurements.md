# Tamaño de instrucciones: alcance y límites

Comparación del mismo conjunto de 60 mapas fuente (10 agentes, 16 comandos y
34 skills) contra la base `9c109c592e5a152a7ad311ad6c13080764fd00f1`.
Caracteres UTF-8 normalizados a LF; no tokens observados ni facturados.

| Selección | Antes | Después | Diferencia |
|---|---:|---:|---:|
| Cuatro roles PM: analyst, evaluator, architect y planner | 67.635 | 62.342 | -5.293 (7,83 %) |
| Los mismos 60 mapas | 521.490 | 514.256 | -7.234 (1,39 %) |
| Referencias condicionales añadidas | 0 | 8.336 | +8.336 |
| Políticas compartidas de lectura y salida | 3.108 | 2.034 | -1.074 |
| Mapas + todas las referencias nuevas + políticas una vez | 524.598 | 524.626 | +28 |

Los mapas contienen instrucciones generales y referencias que el cliente puede
cargar de distintas maneras. La clasificación por rutas no observa esa carga.
Las políticas compartidas se cuentan una vez en esta comparación de fuentes;
un agente con contexto fresco puede necesitarlas de nuevo. Otras referencias
preexistentes, el código del proyecto, respuestas, reintentos y resultados de
herramientas quedan fuera de este cuadro. No es un benchmark de una sesión.

La reducción de entrada más visible corresponde a planner: procedimientos de
tipos de tarea y mantenimiento se consultan al aplicar. Evaluator conserva el
procedimiento de salud en una referencia condicional. Las activaciones duplicadas
se quitan del cuerpo solo cuando ya están en la description; sus hashes y textos
retirados constan en `activation-deduplication.json`.

No se declara ahorro real ni una mejora de calidad medida. La reutilización de
navegación y las salidas concisas pretenden reducir trabajo repetido; habrá que
evaluarlas con el mismo objetivo, modelo, condiciones, criterios y consumo nativo
disponible. Una comparación estática no certifica cumplimiento semántico: por eso
se ejecutan revisión independiente y regresiones.

Fuentes: `context-before.json`, `context-after.json`,
`conditional-references.json` y `measurement-summary.json`. Las referencias
nuevas preservan los procedimientos originales; cargar todo puede aumentar el
contexto. Los helpers stdout-only no leen conversaciones ni realizan llamadas
a modelos o servicios externos.

La ampliación T-05 compacta las políticas compartidas y hace condicional su protocolo detallado. [Estimación por rol y escenarios](token-estimates.md). Las cifras de los informes de revisión anteriores describen sus snapshots históricos.
