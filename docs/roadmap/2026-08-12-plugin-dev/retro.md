# Retro — plugin-dev (vía rápida)

> Iniciativa de **vía rápida** cerrada (ledger `completado`). Cifras del bloque `generacion:` y
> del resumen del ledger; nada de memoria.

## Estimado vs real

| Concepto | Estimado | Real (medido) | Desviación |
|---|---|---|---|
| Horas IA de ejecución | 0,8 h | 0,10 h (re-derivada con el ratio calibrado) | **−88 %** |
| Tokens facturables | 250k | 49.175 | **−80 %** |
| Horas humanas | ver ledger | 0 h (ejecución por IA) | no comparable |
| Coste económico (proceso) | ver ledger | 1,52 € (medido) | verificado el 2026-08-18 con `rates-verify` |

**Ratio medido:** 300.050 tokens/hora — ver definición y límites en [`CALIBRATION.md`](../CALIBRATION.md).


> **Nota de re-derivación (2026-08-18).** Las horas-IA están re-derivadas con el ratio **calibrado** (479.326 tok/h de [`CALIBRATION.md`](../CALIBRATION.md)), no con el default de 300.000 con el que se registraron. Los **tokens** no cambian: son la medición; las horas son el derivado.

## Causa principal de la desviación

Igual que workflow-polish (prosa + plantillas), pero con un coste real concentrado en la **revisión**: dos hallazgos críticos —una invocación de pytest que no recogía las suites y unos comentarios inline que habrían hecho que el linter rechazara cualquier agente creado desde la plantilla— obligaron a rehacer partes ya "terminadas".

## Aprendizaje

Cuando la pieza que se escribe es una **plantilla que otros rellenarán**, hay que probarla rellenándola: el defecto no se ve leyendo. La revisión de dos lentes pagó su coste de sobra en esta iniciativa.

## Ajuste sugerido

Toda plantilla nueva lleva una verificación de uso real (rellenarla y pasarla por el validador que corresponda) como criterio de aceptación explícito.
