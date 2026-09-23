---
category: GOTCHA
evidencia: validated_case
fuentes: [docs/roadmap/2026-09-15-graphiti-memory/tasks.md]
tags: [area:adversarial-review, agente:reviewer, tipo:proceso]
project: custom-agents
scope: project
source: agent
confidence: medium
---
# Worktrees de revisión con mutation testing necesitan nombre único e insensible a mayúsculas, y scripts en subdirectorio propio

En la revisión de dos lentes de la Fase 4 de `graphiti-memory` (intento 2, `fix1`), tres lentes
corrieron en paralelo sobre tres worktrees del mismo scratchpad compartido. Dos incidentes de
proceso aparecieron a la vez: el worktree `scratchpad/B` desapareció a mitad de revisión (la lente
tuvo que seguir sobre una copia byte a byte con el baseline reproducido a mano), y en Windows
`scratchpad/b` resolvió al mismo directorio que `scratchpad/B` (case-insensitive), así que una
lente llegó a ejecutar pytest sobre el worktree de otra. Además, 9 scripts y 6 `.bak` del
implementer quedaron sueltos en el scratchpad compartido tras cerrar la ronda.

**Regla:** nombres de worktree únicos e insensibles a mayúsculas (p. ej. `lente-a-<intento>`, nunca
`A`/`a` o `B`/`b` como único diferenciador), scripts de cada rol en su propio subdirectorio con
borrado explícito al cerrar la ronda, y una sola suite pesada corriendo a la vez por máquina para
evitar flakes bajo carga.

Evidencia: `tasks.md`, gap #184 (Minor, proceso): *"(a) el arbitraje «limpiar el scratchpad al
cerrar cada ronda» no se cumplió en fix1 …; (b) el worktree `scratchpad/B` desapareció a mitad de
la revisión …; (c) Windows resolvió `scratchpad/b` → `scratchpad/B` (case-insensitive) y una lente
corrió pytest en el worktree de otra … Arbitraje: nombres de worktree únicos e insensibles a
mayúsculas (`lente-a-<intento>`), scripts de cada rol en su propio subdirectorio y borrado al
cerrar"*; incidente de proceso citado también en #167 (intento 1) como primera forma del mismo
patrón.
