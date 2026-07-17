---
description: Retrospectiva de una iniciativa CERRADA — compara estimado vs real (horas, tokens, coste), captura causas de desviación y aprendizajes, y alimenta el histórico de calibración que el evaluator usa para estimar mejor las siguientes. Escribe retro.md en la carpeta de la iniciativa y una fila en docs/roadmap/CALIBRATION.md.
argument-hint: "<slug o carpeta de la iniciativa cerrada>"
---

# /retro — cerrar el bucle de aprendizaje

Cuando una iniciativa termina (plan `completado`, spec `implementada`), esto convierte su
experiencia en **datos de calibración** para estimar mejor las próximas. Iniciativa: **$ARGUMENTS**.

## Pasos
1. **Localiza y valida** la carpeta `docs/roadmap/<fecha>-<slug>/`. Si el plan no está `completado`, dilo y para (la retro es de iniciativas cerradas).
2. **Extrae los números** con la skill `roadmap-dashboard` (`--json`, campo `progreso` de esa iniciativa): horas humanas/IA/supervisión y tokens **real vs est**, y el coste de `evaluation.md`. Calcula desviaciones.
3. **Pregunta al usuario las causas** (breve, 2-3 preguntas): ¿qué explicó la desviación principal? ¿qué incógnita de la spec resultó cara? ¿qué se haría distinto? Registra respuestas literales, sin adornar.
4. **Escribe `retro.md`** en la carpeta de la iniciativa: tabla est vs real con desviaciones, causas, aprendizajes, y una línea de "ajuste sugerido" (p. ej. "las tareas de integración salieron +40 %: estimarlas con margen extra").
5. **Añade una fila** a `docs/roadmap/CALIBRATION.md` (créalo si falta; una tabla: fecha · slug · desv. producción % · desv. tokens % · causa principal · ajuste sugerido). Este fichero es el **histórico que lee `evaluator`** al estimar.
6. Cierra con el titular: desviación global y el aprendizaje nº1.

## Reglas
- **Sin culpa, con datos.** Causas y aprendizajes, no reproches; cifras del ledger, no de memoria.
- Solo lectura del roadmap salvo `retro.md` y `CALIBRATION.md`.
- Si no hay horas reales registradas, dilo: sin datos no hay retro útil (y recuerda que `jira-sync`/`implementer` las registran al completar tareas).
