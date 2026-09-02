---
id: GOT-004
tipo: gotcha
area: Jira / conector
estado: aceptada (validada: usuario, 2026-09-02)
fuente: docs/roadmap/2026-08-10-jira-granularity/tasks.md (T-08, dry-run PROJ-60) vía Notas de implementación
---

## Resolver la transición de cierre por nombre, o confiar en el "asignado por defecto" del proyecto, rompe en Jira real

- **Síntoma:** dry-run de la puerta manual T-08 (`2026-08-10-jira-granularity`) contra el proyecto
  de pruebas de Jira, issue desechable `PROJ-60` (subtarea bajo `PROJ-59`). Dos hallazgos al
  ejercitar el conector en vivo: (1) la transición a Done se buscaba por su **nombre**
  ("Done"), pero el estado destino real estaba **localizado** ("HECHO") y los ids de transición
  variaban por workflow — una búsqueda por nombre/id fijo habría fallado o transicionado al estado
  equivocado en otro proyecto; (2) el proyecto tenía "asignado por defecto" activo y, al crear el
  issue sin `assignee` explícito, `createJiraIssue` lo **auto-asignó a otra persona del equipo**
  (con notificación), no a quien ejecutaba el volcado.
- **Causa raíz:** ambos son casos de **confiar en un valor que Jira decide por su cuenta según la
  configuración del proyecto/workflow** en vez de resolverlo explícitamente cada vez: el nombre y
  el id de una transición no son estables entre proyectos (dependen del workflow y del idioma), y
  el campo `assignee` tiene un default de proyecto que no tiene por qué coincidir con quien opera
  el conector.
- **Qué hacer en su lugar:** (a) resolver la transición de cierre por
  `to.statusCategory.key == "done"` vía `getTransitionsForJiraIssue`, nunca por el nombre de la
  transición ni del estado destino ni por un id fijo; (b) fijar `assignee` de forma **explícita**
  en todo `createJiraIssue` — accountId propio (`atlassianUserInfo`) o sin asignar, a elección del
  usuario, preguntada una vez y persistida en `.claude/jira.json` (`assignee: "me" | "none"`,
  opt-in como el resto de la config de `jira-sync`).
- **Evidencia / fuente:** [`docs/roadmap/2026-08-10-jira-granularity/tasks.md`](../../roadmap/2026-08-10-jira-granularity/tasks.md)
  (T-08, dry-run PROJ-60 bajo PROJ-59, 2026-09-02); reglas incorporadas en
  [`docs/atlassian-connector-notes.md`](../../atlassian-connector-notes.md) y
  [`skills/jira-sync/SKILL.md`](../../../skills/jira-sync/SKILL.md) (Paso 0-ter, Paso 5, Paso 7).

`estado: aceptada (validada: usuario, 2026-09-02)`
