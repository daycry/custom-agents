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
