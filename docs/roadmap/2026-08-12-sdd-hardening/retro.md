# Retro — sdd-hardening (2026-08-12)

> Primera retro del proyecto. Iniciativa cerrada: plan `completado`, spec `implementada`.
> Datos del ledger y de los bloques `generacion:`, no de memoria.

## Estimado vs real

| Concepto | Estimado | Real | Desviación |
|---|---|---|---|
| Horas humanas | 19,25 h | 0 h (no hubo trabajo humano de ejecución) | — no comparable |
| Horas IA de ejecución (tareas) | 6,2 h | 0,26 h (medido) | **−96 %** |
| Supervisión | 1,55 h | 0 h imputadas | — |
| Tokens de ejecución (tareas) | 1.835k | 123k (medido) | **−93 %** |
| Coste de proceso (spec+eval+plan) | — (no se presupuestó aparte) | 58.914 tok facturables · 3 ventanas | — |
| Coste económico (proceso) | ~1.195 € | 2,43 € (medido, Opus 4.8 con caché) | verificado el 2026-08-18 con `rates-verify` |

**Ratio medido:** 58.914 tok facturables ÷ 0,101 h de reloj = **584.271 tokens/hora**

> **Nota de re-derivación (2026-08-18).** Las horas-IA de este retro y del ledger están
> re-derivadas con el ratio **calibrado** (479.326 tok/h de `CALIBRATION.md`), no con el default
> de 300.000 con el que se registraron en su momento: por eso el «real» bajó de 0,40 h a 0,26 h.
> Los **tokens** no cambian — son la medición; las horas son el derivado.
(definición y límites en [`CALIBRATION.md`](../CALIBRATION.md)).

## Causas de la desviación

1. **La estimación se hizo con defaults genéricos, no con datos del proyecto.** El `evaluator`
   partió del ratio por defecto (300.000 tok/hora) y de horas-IA "a juicio", porque
   `CALIBRATION.md` no existía todavía. Esta retro es literalmente el fichero que faltaba.
2. **El presupuesto mezcló dos cosas distintas**: horas humanas equivalentes (lo que costaría a
   una persona, ~19 h) y horas-IA de ejecución (~6 h). La primera cifra es útil para justificar
   valor; la segunda pretendía predecir el ciclo y se pasó 15×.
3. **No se presupuestó el coste de proceso.** Producir spec + evaluación + plan costó 58.914
   tokens medidos que no aparecían en ninguna previsión: el papeleo también consume.

## Aprendizajes

- **El coste real se fue en la revisión, no en escribir.** La revisión adversarial de dos lentes
  encontró 21 hallazgos en el primer intento; corregirlos y re-verificarlos fue el trabajo grueso.
  Escribir las 13 tareas fue comparativamente barato.
- **Medir cambió el diagnóstico, no solo el número.** Sin `usage-meter` habríamos seguido creyendo
  que el ciclo cuesta horas de IA. Con medición, el cuello de botella visible es otro: la
  validación humana de lo producido.
- **Calibrar cambió las cifras ya publicadas, y eso es sano.** Al derivar el ratio real, las horas
  registradas con el default se revelaron ~60 % altas y hubo que re-derivarlas. Consecuencia
  práctica: lo que `jira-sync` habría imputado como worklog estaba inflado.
- Las **horas humanas** siguen sin validarse: nadie ha cronometrado supervisión real. Mientras eso
  no se registre, la columna "producción" mide IA y no debe usarse para comprometer plazos.

## Ajuste sugerido para las próximas estimaciones

1. Estimar el **coste de proceso** con el ratio calibrado de `CALIBRATION.md` (mediana vigente),
   como línea presupuestaria propia junto al de implementación.
2. Separar en la evaluación **horas humanas equivalentes** (valor) de **horas-IA previstas**
   (plazo): son magnitudes distintas y hoy se presentan juntas.
3. Añadir una línea explícita de **revisión y corrección** (dos lentes + bucle acotado): es donde
   se concentra el esfuerzo real en este tipo de iniciativa.
