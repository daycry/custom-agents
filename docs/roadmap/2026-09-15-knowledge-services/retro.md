---
retro: knowledge-services
fecha: 2026-09-19
autor: orquestador (/dev-cycle, modo autónomo por /goal del usuario)
validada_por_usuario: pendiente
---

# Retro — knowledge-services

Registrada por el orquestador al cierre del ciclo (2026-09-19). Las causas salen de la evidencia del ledger, no de una conversación con el usuario: **pendientes de validar por el usuario** (puede corregirlas en el PR).

## Estimado vs real

| Métrica | Estimado | Real | Desviación |
|---|---:|---:|---|
| Horas humanas | 56 h | 0 h | −100 % (toda la ejecución fue de agentes; el usuario solo fijó el objetivo y validó enmiendas) |
| Horas IA de implementación (ventanas `usage-meter` por tarea) | 16,8 h | 6,15 h | −63 % (mezcla de `(medido)` en ventanas compartidas repartidas y `(estimado)`) |
| Supervisión | 4,2 h | 0 h | sin supervisión humana en el ciclo |
| Tokens en ventanas de tarea | 815k | ~230k | −72 % (solo las ventanas del implementer; **no incluye** las 12 pasadas de lentes ni las 11 rondas de corrección coordinadas por el orquestador) |
| Tareas | 13 | 13 | 100 % |
| Gaps de la revisión de dos lentes | — | 185 (7 Critical, 73 Important, 105 Minor) | 4 fases × 3 intentos; 11 rondas de corrección (4 en la Fase 3) |
| Coste humano (50 EUR/h) | 2.800 EUR | 0 EUR | — |

Fuente: tabla «Resumen de progreso» de `tasks.md`, secciones «Revisión de dos lentes» y bloques de verificación final por ronda.

## Causas de la desviación (evidencia del ledger)

1. **El coste real no estuvo en implementar sino en revisar y corregir.** Las tareas cerraron en 6 h de IA, pero el bucle de dos lentes produjo 185 gaps y 11 rondas: la revisión adversarial con contexto fresco fue la que encontró los 7 Critical (colisión de basename que apagaba la colección de CI, lista negra por subcadena, `apply` no atómico, `--rebuild` no-op, rollback que perdía la publicación, `apply` que borraba ficheros ajenos, outbox atascada). El plan no presupuestaba esa parte.
2. **Un diseño fijado por el orquestador dentro de una tabla de gaps (publicación por intercambio de directorio, Fase 3 intento 2) generó 2 de los 3 Critical siguientes** (#126 pérdida de datos en el rollback, #127 borrado de ficheros ajenos). Se sustituyó por publicación por fichero con diario (`manifest.pending.json`), que además eliminó la regresión O(N) del camino estable. Lección: un cambio de diseño en pleno bucle necesita su propia revisión antes de implementarse, no una prescripción en la columna «Corrección».
3. **Ventanas de medición compartidas.** Los implementadores abrieron varios marcadores en la misma sesión (fixN de varias tareas) o los abrieron tarde: buena parte de las horas IA son repartos a partes iguales o `(estimado)`. El ratio tokens/hora de esta iniciativa no calibra.
4. **Contexto de subagentes que se compacta a mitad de ronda**: tres despachos perdieron el hilo (trabajo hecho sin comitear, informe parcial) y el orquestador tuvo que comitear y relanzar con brief acotado. Coste: tiempo de pared, no defectos.
5. **Lo que sí se validó en vivo**: el adaptador Kwipu contra el bridge real (`health` sano, export con frontmatter CA-17, `verify` con desfase y remedio, idempotencia, `summary`, `rebuild`); el cierre físico (reindexar el stack) quedó fuera del plugin por diseño (CA-16) y lo ejecuta el usuario.

## Aprendizajes

- Cualitativos (ya curados por el Knowledge Gate de esta misma iniciativa, Fase 4-bis): `docs/knowledge/approved/gotchas/custom-agents.GOT-012-…` (publicación por fichero con diario), `docs/knowledge/approved/lessons/custom-agents.LES-017-…` (lista negra por subcadena), `docs/knowledge/approved/gotchas/custom-agents.PAT-001-…` (adaptador externo opcional degrada y nunca ejecuta el stack).
- De proceso (nuevo, propuesto como candidato para el curador): `docs/knowledge/candidates/pending/un-diseno-nuevo-en-mitad-del-bucle-pasa-por-revision-antes-de-implementarse.md`.
- Numérico: ver fila en `docs/roadmap/CALIBRATION.md`.

## Ajuste sugerido

Presupuestar la **revisión de dos lentes y sus rondas de corrección** como partida propia (en esta iniciativa superó con mucho a la implementación: 11 rondas para 13 tareas) y exigir en `usage-meter` **un marcador por tarea sin solape** (o registrar la ventana compartida explícitamente) para que las horas IA calibren.

## Titular

Desviación global: −63 % en horas IA de implementación y 0 h humanas, pero con un coste de revisión no presupuestado (185 gaps, 11 rondas). Aprendizaje nº 1: la revisión adversarial con contexto fresco es donde aparecen los Critical; hay que presupuestarla y no fijar diseños nuevos dentro de una ronda de corrección sin revisarlos antes.
