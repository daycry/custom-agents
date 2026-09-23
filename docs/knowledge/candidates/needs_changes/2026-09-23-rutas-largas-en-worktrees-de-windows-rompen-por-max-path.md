---
category: GOTCHA
evidencia: single_case
fuentes: [docs/roadmap/2026-09-15-graphiti-memory/tasks.md]
tags: [area:tooling, agente:implementer, tipo:windows]
project: custom-agents
scope: project
source: agent
confidence: medium
---
# Nombres largos de entrada de conocimiento rompen worktrees profundos en Windows por MAX_PATH

En el cierre de la Fase 4 de `graphiti-memory` (fix2), un worktree del scratchpad falló tres tests
en falso (`test_mermaid_blocks`, la biyección de `lint_plugin`, y
`test_doctor::test_repo_real_la_memoria_curada…`) porque la ruta a
`docs/knowledge/approved/gotchas/custom-agents.GOT-012-…md` superaba MAX_PATH (263 > 260
caracteres) al vivir bajo la ruta más profunda del worktree. Los mismos tests pasaban en verde en
el árbol principal, donde la ruta absoluta es más corta.

**Regla:** con worktrees anidados en rutas ya largas (scratchpads, revisiones en paralelo), un
nombre de fichero de conocimiento largo (`GOT-NNN-<slug-largo>.md`, sobre todo con el prefijo del
proyecto delante) puede cruzar el límite de 260 caracteres de Windows sin que el contenido tenga
ningún problema; si aparecen fallos de tests de solo-lectura (biyección de índice, lint) que no
reproducen en el árbol principal, sospechar de MAX_PATH antes que de una regresión real —
comparando la longitud de la ruta absoluta, no solo el nombre del fichero.

Evidencia: `tasks.md`, sección de cierre de fix2: *"Artefacto de entorno, no gap: en los worktrees
del scratchpad la ruta a `docs/knowledge/approved/gotchas/custom-agents.GOT-012-…md` supera
MAX_PATH (263 > 260) y produce 3 falsos rojos …, todos verdes en el árbol principal (→ #195)."*

---

## Observaciones del curador (`knowledge-curator`, 2026-09-23 — `needs_changes`)

`curator-gate.py --decision approve --id custom-agents.GOT-014` → `errores: ["evidencia single_case
no alcanza min_evidence (validated_case) de la categoria GOTCHA"]`. La categoría `GOTCHA` es la
correcta (trampa de entorno, no regla de proceso: no se reclasifica a `LESSON` para bajar el
umbral), y la etiqueta `single_case` es honesta: el gap #195 del ledger registra el diagnóstico
(263 > 260, tres falsos rojos en los worktrees, verde en el árbol principal) pero el arbitraje
(«`core.longpaths` ya activo en el repo principal; nombres de gotcha ≤ 80 chars o worktrees en rutas
cortas») quedó **sin validar**: «sin cambio de código en esta iniciativa».

Qué falta para reintentar `approve`:

1. Validar el remedio y citarlo: p. ej. reproducir los 3 falsos rojos en un worktree de ruta
   profunda y comprobar que desaparecen con `git config core.longpaths true` en ese worktree, o con
   el worktree en una ruta corta (`pytest -q tests/test_mermaid_blocks.py agent-kits/shared/test_doctor.py`
   + `python scripts/lint_plugin.py`, salida real), y subir entonces `evidencia: validated_case`.
2. Añadir a `fuentes` la fila exacta (`tasks.md`, gap #195 y la nota «Artefacto de entorno, no gap»
   del intento 3) y, si se aplica, la regla de nombres (≤ 80 caracteres) donde quede fijada.
3. Relación a declarar en el cuerpo: `GOT-008` del corpus legado ya documenta que la ruta absoluta
   en Windows altera medidas del plugin (tope del brief); esta entrada es distinta (falsos rojos por
   MAX_PATH), pero debe citarla para no parecer duplicado.

`id` reservado al reintento: `custom-agents.GOT-014`.
