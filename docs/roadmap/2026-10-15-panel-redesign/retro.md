---
retro: panel-redesign
fecha: 2026-10-21
---

# Retro — panel-redesign

> Iniciativa cerrada el 2026-10-21: 58/58 tareas en cuatro fases, cada una cerrada con su revisión de dos lentes y la revisión visual del usuario (M-01..M-04). qa: VERDE, 32/32 bloques automáticos y 53 criterios `[GWT]` cubiertos ([testing/report.md](testing/report.md)). Las cifras salen del ledger ([tasks.md](tasks.md)) y de la [evaluación](evaluation.md). Las causas las propuso el orquestador y el usuario las confirmó el 2026-10-21.

## Estimado frente a real

| Métrica | Estimado | Real | Desviación |
|---|---:|---:|---:|
| Horas IA (ejecución) | 60,2 h | 14,83 h (derivadas de los tokens medidos con el ratio vigente) | −75 % |
| Horas humanas | 159,2 h | 0 h (ejecución íntegra por agentes) | −100 % |
| Supervisión | 19,6 h | 0,24 h registradas; no incluyen M-01..M-04 ni las decisiones del usuario | no comparable |
| Tokens | 32,01 M | registrados por tarea solo en la Fase 1 (0,70 M); el resto, en los `generacion:` de cada ventana | no comparable |
| Coste de ejecución con agentes | ≈ 1.188 € | sin agregado fiable (mismo motivo que los tokens) | — |
| Revisión | 3 intentos por fase (tope) | Fase 1: 3 + 2 confirmaciones · Fase 2: 3 · Fase 4: 2 · Fase 3: 3 + confirmación + fix4 | Fase 3 por encima del tope, con decisión del usuario |
| qa | 1 ejecución | 4 ejecuciones: 1 defecto real (A11Y-01), 3 errores del plan de pruebas y 2 ejecuciones perdidas por el montaje o un error de API | — |
| Duración | — | del 2026-10-15 al 2026-10-21 | — |

## Causas

Confirmadas por el usuario el 2026-10-21.

1. **La desviación principal.** La estimación suponía horas humanas de implementación y presupuestó la IA en proporción. Los agentes implementaron mucho más rápido, y casi todo el coste real se fue en revisión y corrección, no en implementar.
2. **La incógnita cara.** La captura en vivo con varios runtimes. Por un lado, el cerrojo frente a ráfagas de herramientas: una señal de ciclo de vida perdía el cerrojo, y mezclar `flock` y `lockf` bloquea al propio proceso en macOS/BSD y NFS. Por otro, el redactor de credenciales basado en heurísticas: cuatro rondas, y cada una abrió fugas nuevas (comillas, apóstrofos de prosa, programa dentro del valor de una opción).
3. **Qué se haría distinto.** Probar una heurística de seguridad contra un corpus de fugas y de casos limpios ANTES de implementarla. Presupuestar más rondas de revisión en las fases que tocan seguridad. Dejar el montaje de qa en un script reproducible desde la primera ejecución.

## Aprendizajes

- Una ráfaga de eventos de herramienta deja sin cerrojo a la señal de ciclo de vida; un solo tipo de cerrojo por fichero. Propuesto como gotcha en `docs/knowledge/candidates/pending/` (local; lo aprueba `knowledge-curator`).
- Una heurística de seguridad se valida contra un corpus (fugas + limpios + fuzz diferencial) antes de implementarla, no ronda a ronda. Propuesto como lección en `docs/knowledge/candidates/pending/` (local).
- El plan de pruebas describió mal el «comportamiento actual» dos veces (403 frente a 404, texto del exportado). Al citar comportamiento previo en una spec, se cita el código de la base, no la memoria.

## Pendiente fuera de esta iniciativa

- **UI más amigable** del panel, sobre todo de Agentes en vivo. Lo pidió el usuario al aprobar M-04 («de momento nos sirve»). Va a una iniciativa futura.
- Backlog de la revisión: A-5, B3, D4 y 3-3 (`tasks.md`).

## Ajuste sugerido

En iniciativas ejecutadas por agentes, estimar la IA desde las rondas de revisión esperadas y no como fracción de las horas humanas: aquí la implementación fue la parte barata. En fases con heurísticas de seguridad, contar con 4 rondas o con un corpus previo. La fila de [CALIBRATION.md](../CALIBRATION.md) no aporta muestra de tokens/hora: las horas salen del ratio vigente.

Estado: actualizado
