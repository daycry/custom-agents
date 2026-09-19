---
id: custom-agents.GOT-012
category: GOTCHA
version: 1
estado: aprobado
evidencia: validated_case
project: custom-agents
scope: project
source: agent
confidence: medium
fuentes:
  - docs/roadmap/2026-09-15-knowledge-services/tasks.md (gaps #126, #127; ronda fix3)
  - commit 02b9c57 (T-08-fix2, diseño de intercambio de directorio)
  - commit 656bfd8 (T-08-fix3, diseño sustitutivo por fichero)
  - skills/knowledge-services/scripts/test_backend_markdown_export.py (tests citados en Evidencia)
enlaces:
  - custom-agents.PAT-001
tags:
  - agente:knowledge-services
  - area:publicacion-atomica
  - riesgo:perdida-de-datos
curador: knowledge-curator
fecha_aprobacion: 2026-09-19
---

## Publicar una proyección con intercambio de directorio completo pierde datos ajenos y rompe el rollback

- **Síntoma:** `apply()` del adaptador `markdown-export` (`skills/knowledge-services/backends/markdown_export.py`)
  publicaba moviendo `export_dir` entero a `export_dir.prev` y el staging a `export_dir` con dos
  `os.replace`. La revisión adversarial (gaps #126/#127, `docs/roadmap/2026-09-15-knowledge-services/tasks.md`)
  encontró dos Critical: (1) una corrida SIN cambios movía los ficheros `sin_cambios` al staging y
  el rollback tras un fallo perdía esos datos; (2) la contención de `export_dir` era unidireccional
  (no podía estar dentro de `approved/`, pero sí contenerlo), así que `"export_dir": "docs"` pasaba
  la validación y un solo `knowledge-sync` borraba `docs/` entero (incluido `approved/` y `roadmap/`).
- **Causa raíz:** el diseño de intercambio de directorio (`T-08-fix2`, commit `02b9c57`) trata la
  publicación como una operación de UN solo objeto (el árbol completo), así que cualquier fichero
  ajeno al backend que viva dentro de `export_dir` (o cualquier ruta compartida que lo contenga)
  queda a merced del swap, sin distinción entre "propio del manifiesto" y "ajeno".
- **Qué hacer en su lugar:** publicar FICHERO A FICHERO con un diario (`manifest.pending.json` →
  publica cada `upsert` con un `os.replace` individual → renombra a `manifest.json`), nunca
  sustituyendo el árbol entero; los `revoke` solo pueden borrar ficheros que constan en el
  manifiesto PROPIO. La contención de `export_dir` debe ser BIDIRECCIONAL: ni el root, ni un
  ancestro del root, ni dentro de o conteniendo `docs/knowledge/`. Diseño aplicado en `T-08-fix3`
  (commit `656bfd8`).
- **Evidencia:** tests `test_apply_no_borra_ficheros_ni_subcarpetas_ajenas_en_export_dir`,
  `test_rebuild_no_toca_ficheros_ajenos_en_export_dir`,
  `test_export_dir_igual_a_docs_que_contiene_docs_knowledge_es_config_invalida`,
  `test_export_dir_ancestro_del_root_es_config_invalida`
  (`skills/knowledge-services/scripts/test_backend_markdown_export.py`),
  todos en verde tras `656bfd8`.

---

*Curado el 2026-09-19 por `knowledge-curator` (`/dev-cycle` Fase 4-bis, `knowledge-services`): gaps #126/#127, commits `02b9c57`/`656bfd8` y los cuatro tests verificados (existen y pasan); la cita del fichero de tests se corrigió a su ruta real (`skills/knowledge-services/scripts/test_backend_markdown_export.py`, no `tests/test_knowledge_services.py`). Afín a `LES-016` del corpus legado (estados intermedios con dueño): el diario `manifest.pending.json` es ese dueño.*
