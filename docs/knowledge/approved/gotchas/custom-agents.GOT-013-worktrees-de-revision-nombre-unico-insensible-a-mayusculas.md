---
id: custom-agents.GOT-013
category: GOTCHA
version: 1
estado: aprobado
evidencia: validated_case
project: custom-agents
scope: project
source: agent
confidence: medium
fuentes:
  - docs/roadmap/2026-09-15-graphiti-memory/tasks.md (gap #184, Minor proceso, revisión Fase 4 intento 2 — incidentes (a)-(d) y arbitraje)
  - docs/roadmap/2026-09-15-graphiti-memory/tasks.md (gap #167, revisión Fase 4 intento 1 — incidente de proceso de la Lente C, primera forma del patrón)
tags:
  - area:adversarial-review
  - agente:reviewer
  - tipo:proceso
curador: knowledge-curator
fecha_aprobacion: 2026-09-23
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

---

*Curado el 2026-09-23 por `knowledge-curator` (`/dev-cycle` Fase 4-bis, `graphiti-memory`): gaps #184 y #167 verificados en el ledger (la cita de #184 es literal; #167 consta como «incidente de proceso de C» en la fusión del intento 1). Sin solape con lo ya aprobado ni con `LES-010` del corpus legado (que trata la revisión adversarial como skill, no su higiene de entorno). El nivel `validated_case` se sostiene: el patrón apareció en dos intentos consecutivos y el arbitraje se aplicó (scratchpad limpiado, reglas en los briefs de las lentes en el intento 3, que corrió sin repetir el incidente).*
