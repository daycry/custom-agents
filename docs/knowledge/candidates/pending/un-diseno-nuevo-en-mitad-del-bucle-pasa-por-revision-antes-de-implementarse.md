---
category: LESSON
evidencia: validated_case
fuentes: [docs/roadmap/2026-09-15-knowledge-services/tasks.md, docs/roadmap/2026-09-15-knowledge-services/retro.md]
tags: [area:orquestacion, agente:dev-cycle, tipo:proceso]
project: custom-agents
scope: project
source: agent
confidence: medium
---
# Un diseño nuevo en mitad del bucle de revisión pasa por revisión antes de implementarse

En la Fase 3 de `knowledge-services` (intento 2 de la revisión de dos lentes), el orquestador fijó un diseño de publicación por intercambio de directorio dentro de la columna «Corrección» del ledger, sin someterlo a lente alguna. La ronda que lo implementó cerró los gaps de atomicidad pero abrió dos Critical nuevos (#126 rollback que borra la publicación, #127 `apply` que vacía ficheros ajenos de `export_dir`) y una regresión O(N) (#136), que costaron una ronda completa más y un diseño sustitutivo (publicación por fichero con diario `manifest.pending.json`).

**Regla:** si una corrección exige cambiar el diseño (no solo el código), el cambio se escribe como propuesta con sus caminos de fallo y la Lente B lo prueba con probes ANTES de despacharlo al implementer; una prescripción en una celda de gap no sustituye esa revisión.

Evidencia: `tasks.md` secciones «Revisión de dos lentes — intento 2/3 (Fase 3)», commits `02b9c57` (diseño roto) y `656bfd8` (sustitutivo); `retro.md` causa 2.
