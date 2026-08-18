# Retro — subagent-personas (vía rápida)

> Iniciativa de **vía rápida** cerrada (ledger `completado`). Cifras del bloque `generacion:` y
> del resumen del ledger; nada de memoria.

## Estimado vs real

| Concepto | Estimado | Real (medido) | Desviación |
|---|---|---|---|
| Horas IA de ejecución | 0,8 h | 0,14 h (re-derivada con el ratio calibrado) | **−83 %** |
| Tokens facturables | 250k | 65.711 | **−74 %** |
| Horas humanas | ver ledger | 0 h (ejecución por IA) | no comparable |
| Coste económico (proceso) | ver ledger | 2,55 € (medido) | verificado el 2026-08-18 con `rates-verify` |

**Ratio medido:** 421.674 tokens/hora — ver definición y límites en [`CALIBRATION.md`](../CALIBRATION.md).


> **Nota de re-derivación (2026-08-18).** Las horas-IA están re-derivadas con el ratio **calibrado** (479.326 tok/h de [`CALIBRATION.md`](../CALIBRATION.md)), no con el default de 300.000 con el que se registraron. Los **tokens** no cambian: son la medición; las horas son el derivado.

## Causa principal de la desviación

La única vía rápida con **TDD real** (7 tests, rojo antes de verde): más tokens y más reloj que las de prosa pura — y aun así por debajo de lo estimado. La desviación es la menor de las cuatro vías rápidas, lo que sugiere que la estimación gruesa acierta más cuando hay código de verdad.

## Aprendizaje

El TDD **encarece la ejecución y abarata la revisión**: la lente B solo encontró un defecto (un `Tipo` de ejemplo dentro de un bloque de código que inyectaba la persona equivocada), frente a los 2-10 de las iniciativas sin tests.

## Ajuste sugerido

Cuando la tarea lleva tests, multiplicar por ~2 la estimación de una vía rápida de prosa — y descontar esfuerzo de revisión, porque los tests ya cubren parte.
