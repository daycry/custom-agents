---
retro: setup-statusline-polish
fecha: 2026-10-01
---

# Retro — setup-statusline-polish

> Iniciativa cerrada el 2026-10-01: 14/14 tareas, QA sin UI (18/19 CA con test ejecutado; CA-17 es un rojo de entorno de Windows que ya existía antes) y Knowledge Gate (PAT-002, GOT-015, LES-021). Es el **primer piloto de `sdd-proporcional`** (riesgo `medio`). Las cifras salen del ledger ([tasks.md](tasks.md)) y de la [evaluación](evaluation.md).

## Estimado frente a real

| Métrica | Estimado | Real | Desviación |
|---|---:|---:|---:|
| Horas IA | 14,13 h (×1,5 de revisión incluido) | **sin medir**: el meter degradó en todo el ciclo (`fuente: estimado`, sin transcripciones legibles desde los worktrees) | — |
| Reloj de las ventanas | — | ≈ 15 h 30 min sumadas (F1-F3 1 h 1 min · T-10/T-11 34 min · T-12/T-13 36 min · fix1 10 h 13 min, con un corte por límite de uso · fix2 59 min · T-14 56 min) | — |
| Horas humanas | 54,8 h | 0 h (ejecución íntegra por agentes) | −100 % |
| Revisión | 3 intentos (tope) | **3 intentos**: 18 + 6 + 3 gaps (0 Critical · 9 Important · 18 Minor), cerrada en el intento 3 sin Critical ni Important | dentro del tope |

## Causas

Las propone el orquestador; el usuario aún no las ha validado.
1. **Lo que funcionó.** Las reglas de `sdd-proporcional` hicieron su trabajo. El tope real de 3 intentos se respetó, los Minor no bloquearon el cierre (#17, CA-17 y #27 quedan en backlog o declarados) y el diseño O1 se aprobó ANTES de implementar T-12. Comparado con `training-data-services` (15 secciones y 206 gaps), la revisión convergió en 3.
2. **Lo que costó.** Casi todos los Important estaban en el único fichero que escribe en la configuración de otro (`kwipu-project-add.py`): la reversión que borraba bytes ajenos (#1, #7, #19), los nombres que YAML no lee como texto (#2) y los caracteres que no parsean (#20). El riesgo del conjunto era `medio`, pero ese fichero era de riesgo `alto`.
3. **Qué se haría distinto.** Declarar el riesgo **por tarea** cuando una tarea toca configuración ajena, aunque la iniciativa sea de riesgo medio. Y medir la cobertura sobre las líneas del diff desde el principio (LES-021).

## Aprendizajes

- Revertir un append: se trunca por el descriptor y solo con la identidad, el tamaño y los bytes propios confirmados. Ver `docs/knowledge/`, PAT-002 (local).
- La salida de un CLI se escapa en texto y en `--json` (`ensure_ascii`). Ver GOT-015 (local).
- La cobertura de riesgo medio se mide sobre las líneas del diff. Ver LES-021 (local).
- Precedente de TDD (#17): en T-12 el script se escribió antes que los tests. Las rondas de fix sí llevaron un RED de comportamiento.

## Ajuste sugerido

En iniciativas de riesgo medio, la tarea que escribe en configuración ajena se trata como riesgo alto (Lente C y mutantes) aunque el resto sea medio. El ×1,5 de revisión no se puede calibrar con esta iniciativa porque las horas no se midieron.

Estado: actualizado
