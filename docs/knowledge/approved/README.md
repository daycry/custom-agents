# `docs/knowledge/approved/` — conocimiento aprobado del flujo de `knowledge-services`

Fuente de verdad de las entradas que ya pasaron por `docs/knowledge/candidates/` y fueron
promovidas (ADR-018). **Ownership: únicamente el agente `knowledge-curator` escribe aquí**
(T-04) — es quien mueve un candidato desde `candidates/` tras aprobarlo; ningún otro agente
crea, edita ni borra ficheros bajo este árbol directamente.

Estructura: una carpeta por `categories[].folder` de `.claude/knowledge-services/taxonomy.json`
(o de la plantilla por defecto del plugin si el proyecto no configura nada — ver
`agent-kits/shared/templates/taxonomy.json`), con un fichero Markdown por entrada
(`id`/`version`/`enlaces` en el frontmatter). `agent-kits/shared/knowledge-index.py` (T-02)
construye el índice determinista SOLO sobre estas carpetas: falla con fichero+campo si hay un
`id` duplicado, falta `version` o un enlace roto.

Este árbol es **distinto** del legado `docs/knowledge/{adr,gotchas,lessons}/` (memoria técnica
del propio plugin, con su índice manual en `docs/knowledge/README.md`, ADR-006 D4): no lo
sustituye ni lo migra. Sirve al flujo de `knowledge-services` para proyectos que declaren su
propia taxonomía.

Cualquier exportación a un backend declarado (p. ej. Kwipu, `type: markdown-export`) se
**deriva** de este árbol y nunca se versiona (ver `.gitignore`:
`.claude/knowledge-services/*-export/`).
