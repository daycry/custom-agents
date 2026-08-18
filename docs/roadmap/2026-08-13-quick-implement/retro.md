# Retro — quick-implement (vía rápida)

> Iniciativa de **vía rápida** cerrada (ledger `completado`). Cifras del bloque `generacion:` y
> del resumen del ledger; nada de memoria.

## Estimado vs real

| Concepto | Estimado | Real (medido) | Desviación |
|---|---|---|---|
| Horas IA de ejecución | 0,3 h | 0,07 h (re-derivada con el ratio calibrado) | **−77 %** |
| Tokens facturables | 100k | 34.062 | **−66 %** |
| Horas humanas | ver ledger | 0 h (ejecución por IA) | no comparable |
| Coste económico (proceso) | ver ledger | 2,15 € (medido) | verificado el 2026-08-18 con `rates-verify` |

**Ratio medido:** 1.048.061 tokens/hora — ver definición y límites en [`CALIBRATION.md`](../CALIBRATION.md).


> **Nota de re-derivación (2026-08-18).** Las horas-IA están re-derivadas con el ratio **calibrado** (479.326 tok/h de [`CALIBRATION.md`](../CALIBRATION.md)), no con el default de 300.000 con el que se registraron. Los **tokens** no cambian: son la medición; las horas son el derivado.

## Causa principal de la desviación

Alcance minúsculo y **definido de antemano**: la spec de backlog ya estaba escrita (con su riesgo principal y su contraargumento), así que la implementación no tuvo que decidir nada. La estimación de 1 h se hizo sin contar con que ese trabajo de definición ya estaba pagado.

## Aprendizaje

Escribir la spec antes —aunque sea para dejarla en backlog— **reduce de forma medible el coste de implementarla después**: el trabajo de pensar no se repite. También aquí la revisión fue decisiva: 10 hallazgos, uno de ellos un puntero de fases que habría hecho que la skill se saltara el `qa-gate`.

## Ajuste sugerido

Descontar de la estimación el trabajo ya hecho en la spec cuando una iniciativa nace de backlog; y mantener la revisión de dos lentes incluso en piezas de una hora.
