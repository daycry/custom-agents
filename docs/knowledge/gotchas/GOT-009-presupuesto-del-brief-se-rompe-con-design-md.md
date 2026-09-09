---
id: GOT-009
tipo: gotcha
area: Brief del subagente / presupuesto CA-08
estado: propuesta (hallazgo de la revisión de dos lentes, project-specialization F1 intento 2, 2026-09-09)
fuente: docs/roadmap/2026-09-09-project-specialization/tasks.md (Revision de dos lentes - intento 2, gap B-3 y nota «Preexistente»); medición en docs/roadmap/2026-09-09-brief-budget/analysis.md §1
---

## El presupuesto del brief (`BRIEF_TOPE_CHARS = 10000`) se rompe en silencio en cuanto la iniciativa tiene `design.md`: `## Diseño` entra entero (3.510 caracteres, el 35 % del tope) y solo la memoria tiene tope propio

- **Síntoma:** al despachar las tareas de `2026-09-09-project-specialization` (la primera iniciativa del
  repo que llega a `/dev-cycle` con `design.md` aprobado), **8 de 22 briefs** salían por encima de 10.000
  caracteres con la persona reducida al mínimo (11 de 22 con la persona del catálogo entera), el mayor en
  **14.799** (T-01, +48 %), con `rc=0` y **sin un solo aviso**. La sección de persona —la única variable a
  la que se le pidió caber en el margen— quedaba en un muñón de 55 caracteres (T-06) para que el total
  diera exactamente 10.000. Todos los tests en verde.
- **Causa raíz:** de las siete secciones del brief, **solo `## Memoria técnica` tiene presupuesto propio**
  (`MEMORIA_TOPE_CHARS = 2400`, con recorte y aviso). `## Diseño` inyecta la sección «opción elegida» de
  `design.md` **entera y en las 22 tareas** (3.510 caracteres constantes, tengan o no que ver con el
  diseño), `## Gaps pendientes de revisión` inyecta la tabla completa de todos los intentos (4.396 en
  T-01) y `## Verificación` arrastra la evidencia pegada (2.285 en T-02). Antes de la primera línea de la
  tarea ya van **5.729 … 6.935** caracteres; la tarea mediana más su verificación (3.396) ya no cabe con
  la memoria al tope. Y **el test que guarda el CA-08 recorre un solo ledger, `memory-retrieval`, que no
  tiene `design.md`**: el guardarraíl nunca había visto un brief con `## Diseño`.
- **Qué hacer en su lugar:** (1) el tope global se **avisa en runtime** con la causa medida por sección,
  nunca solo en tests (lo añade F1 de `project-specialization`); (2) toda sección variable del brief lleva
  **su propio presupuesto con recorte alineado a línea** (`_recorte_seguro`) y aviso, calcando la memoria —
  o entra **bajo demanda** cuando la tarea la referencia (el caso de `## Diseño`); (3) el test del CA-08
  recorre **todos** los `docs/roadmap/*/tasks.md`, con y sin `design.md`, o seguirá ciego a la próxima
  sección nueva. **No** se arregla subiendo el tope (es requisito de la spec de `memory-retrieval`), ni
  recortando la tarea o el contrato de retorno (graduado ALTA en `test_task_brief.py:190-192`), ni
  sacrificando la única sección que sí tiene tope.
- **Relación con `GOT-008`:** sigue siendo cierto (la ruta absoluta y el corpus mueven ~250 caracteres),
  pero su remedio —«deja margen en los bloques de tarea, ≤ ~9.500»— **presupone que no hay diseño**. Con
  6.935 comprometidos antes de la tarea, ese margen no existe. Este gotcha no lo sustituye: le quita la
  premisa.
- **Evidencia / fuente:** medición por secciones en
  [`2026-09-09-brief-budget/analysis.md`](../../roadmap/2026-09-09-brief-budget/analysis.md) §1 (tabla
  de 22 tareas × 7 secciones, ejecutando `task-brief.py` sobre el ledger real); hallazgo original de la
  Lente B en [`2026-09-09-project-specialization/tasks.md`](../../roadmap/2026-09-09-project-specialization/tasks.md)
  (sección «Revision de dos lentes - intento 2», gap B-3: T-06 = 9.570 sin persona, 10.764 con la del
  catálogo, 13.950 con una de proyecto al tope; 21 de 21 tareas de `memory-retrieval` se pasarían con
  personas al tope de 4.000). Test ciego: `agent-kits/shared/test_task_brief.py:739`.
