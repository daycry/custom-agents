---
id: custom-agents.LES-020
category: LESSON
version: 1
estado: aprobado
evidencia: validated_case
project: custom-agents
scope: project
source: agent
confidence: medium
fuentes:
  - docs/roadmap/2026-09-15-knowledge-services/tasks.md (Revisión de dos lentes Fase 3, intentos 2 y 3 — gaps #126, #127, #136)
  - docs/roadmap/2026-09-15-knowledge-services/tasks.md (nota T-08 fix3, 2026-09-19 — «diseño sustitutivo, decisión del orquestador»)
  - docs/roadmap/2026-09-15-knowledge-services/retro.md (causa 2 de la desviación)
  - commit 02b9c57 (T-08-fix2, publicación por intercambio de directorio — diseño roto)
  - commit 656bfd8 (T-08-fix3, publicación por fichero con diario — sustitutivo)
enlaces:
  - custom-agents.GOT-012
tags:
  - area:orquestacion
  - agente:dev-cycle
  - tipo:proceso
curador: knowledge-curator
fecha_aprobacion: 2026-09-23
---
# Un diseño nuevo en mitad del bucle de revisión pasa por revisión antes de implementarse

En la Fase 3 de `knowledge-services` (intento 2 de la revisión de dos lentes), el orquestador fijó un diseño de publicación por intercambio de directorio dentro de la columna «Corrección» del ledger, sin someterlo a lente alguna. La ronda que lo implementó cerró los gaps de atomicidad pero abrió dos Critical nuevos (#126 rollback que borra la publicación, #127 `apply` que vacía ficheros ajenos de `export_dir`) y una regresión O(N) (#136), que costaron una ronda completa más y un diseño sustitutivo (publicación por fichero con diario `manifest.pending.json`).

**Regla:** si una corrección exige cambiar el diseño (no solo el código), el cambio se escribe como propuesta con sus caminos de fallo y la Lente B lo prueba con probes ANTES de despacharlo al implementer; una prescripción en una celda de gap no sustituye esa revisión.

Evidencia: `tasks.md` secciones «Revisión de dos lentes — intento 2/3 (Fase 3)», commits `02b9c57` (diseño roto) y `656bfd8` (sustitutivo); `retro.md` causa 2.

---

*Curado el 2026-09-23 por `knowledge-curator` (`/dev-cycle` Fase 4-bis, cierre de `graphiti-memory`; candidato heredado de `knowledge-services`, propuesto tras su Knowledge Gate del 2026-09-19): la causa 2 de `retro.md` es literal («un cambio de diseño en pleno bucle necesita su propia revisión antes de implementarse, no una prescripción en la columna "Corrección"»), los gaps #126/#127/#136 y la nota T-08 fix3 constan en el ledger y ambos commits existen. Enlazada a `custom-agents.GOT-012`, que recoge el MISMO incidente desde el ángulo técnico (qué rompió el intercambio de directorio); esta lección recoge el ángulo de proceso (por qué llegó a implementarse sin revisión). No duplican.*
