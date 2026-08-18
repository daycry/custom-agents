# Retro — workflow-polish (vía rápida)

> Iniciativa de **vía rápida** cerrada (ledger `completado`). Cifras del bloque `generacion:` y
> del resumen del ledger; nada de memoria.

## Estimado vs real

| Concepto | Estimado | Real (medido) | Desviación |
|---|---|---|---|
| Horas IA de ejecución | 1,1 h | 0,03 h (re-derivada con el ratio calibrado) | **−97 %** |
| Tokens facturables | 330k | 16.377 | **−95 %** |
| Horas humanas | ver ledger | 0 h (ejecución por IA) | no comparable |
| Coste económico (proceso) | ver ledger | 2,60 € (medido) | verificado el 2026-08-18 con `rates-verify` |

**Ratio medido:** 479.326 tokens/hora — ver definición y límites en [`CALIBRATION.md`](../CALIBRATION.md).


> **Nota de re-derivación (2026-08-18).** Las horas-IA están re-derivadas con el ratio **calibrado** (479.326 tok/h de [`CALIBRATION.md`](../CALIBRATION.md)), no con el default de 300.000 con el que se registraron. Los **tokens** no cambian: son la medición; las horas son el derivado.

## Causa principal de la desviación

Estimación por **analogía con iniciativas que llevaban código**, cuando en realidad las tres piezas eran disciplina de proceso en prosa (ni scripts ni tests nuevos). El trabajo de escribir fue de minutos; lo que consumió tiempo fue verificar que la prosa no se contradijera con el resto del ciclo.

## Aprendizaje

Una iniciativa de **solo prosa** se mide en minutos, no en horas. Fue además la primera vía rápida medida del plugin, y su valor no estuvo en el ahorro sino en descubrir que el instrumento de medición funcionaba end-to-end.

## Ajuste sugerido

Para vías rápidas sin scripts: estimar en minutos y presupuestar la revisión como la partida principal.
