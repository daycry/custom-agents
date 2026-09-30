---
retro: training-data-services
fecha: 2026-09-29
---

# Retro — training-data-services

> Iniciativa cerrada el 2026-09-29: 11/11 tareas, QA sin UI y Knowledge Gate (GOT-014, LES-020 v2). Cifras del ledger canónico ([tasks.md](tasks.md)) y de la [evaluación](evaluation.md).

## Estimado frente a real

| Métrica | Estimado | Real | Desviación |
|---|---:|---:|---:|
| Horas IA (ejecución) | 12,3 h (evaluación) · 11,9 h (plan) | **105,86 h** (medidas por usage-meter, suma de ventanas; incluye fix5 de #197) | **+761 %** (×8,6) |
| Horas humanas | 39,5 h | 0 h (ejecución íntegra por agentes) | −100 % |
| Supervisión | 3,1 h | sin registrar | — |
| Coste de tokens | por verificar | **750,23 €** (medidos) | — |
| Tokens de salida | 575k | ~3,53 M | ×6,1 |
| Gaps de revisión | — | **206** en 15 secciones (1 Critical · 31 Important · 174 Minor) | — |

**Dónde fue el tiempo.** Implementar las 11 tareas costó ≈ 12 h de IA, en línea con lo estimado. El resto, ≈ 94 h, se lo llevó el bucle de revisión y corrección:
- **Fase 2** (recorder y puerta humana): 3 intentos más las rondas fix1 a fix6; 34,9 h.
- **Fase 3** (dedup, partición, ensamblador): intento 1, revisión previa de D-f3, fix1 y fix2; 27,1 h.
- **Fase 4** (setup, doctor, cierre): 3 intentos, fix1 a fix4 y fix5 para #197; 38,7 h.
- **Diseños rehechos DENTRO del bucle:** 6 (D-fix2, D-fix3, D-fix5, D-f3, D-f4, D-f5).

## Causas

Las propuso el orquestador y las dio por buenas el usuario el 2026-09-29, en su respuesta «todo go» a esta retro:
1. **Desviación ×8.** El objetivo «sin gaps ni errores» convirtió cada Minor en bloqueante. Además, las lentes adversariales defendían frente a escenarios sin límite: 10⁵-10⁶ ficheros, un `case_id` de 1 MB, secuencias ESC plantadas en ficheros que solo escribe el dueño del store. El tope de 3 intentos no funcionó como tope.
2. **Incógnita de la spec que salió cara.** La spec no declaraba modelo de amenaza ni escala. Por eso quedaron abiertos sin límite el uso concurrente, los enlaces (symlink, junction, hardlink), los stores enormes y el `/doctor` acotado en tiempo. Cada ronda de corrección abría gaps nuevos en el camino siguiente, y hubo regresiones de fixN (#165, #167, #181).
3. **Qué se haría distinto.** Lo que recoge [`sdd-proporcional`](../2026-09-29-sdd-proporcional/spec.md): nivel de riesgo declarado en la spec, que decide el rigor; tope real de intentos; Minor al backlog sin bloquear; diseño aprobado ANTES del bucle en riesgo alto; ledger fino.

## Aprendizajes

- **Revisión previa del diseño.** Un diseño nuevo en mitad del bucle tiene que revisarse antes de implementarlo. Las revisiones previas de D-f4 y D-f5 cazaron 9 defectos Important que habrían dado veredictos falsos. Ver `docs/knowledge/`, LES-020 v2 (memoria local).
- **Cobertura en un checkout limpio.** El `.claude/` local sin versionar inflaba `doctor.py` de 89,85 % a 91,32 %. Ver `docs/knowledge/`, GOT-014 (memoria local).
- **El coste no está en implementar, sino en cerrar el bucle.** Es la cuarta iniciativa seguida con este patrón: knowledge-services, graphiti-memory, session-end-durable-capture y esta.

## Ajuste sugerido

Presupuestar la revisión y la corrección como línea propia, aplicando el multiplicador por riesgo de `sdd-proporcional` (×2,2 en `alto`). Sin modelo de amenaza y escala declarados, no arrancar una iniciativa de riesgo alto.

Estado: actualizado
