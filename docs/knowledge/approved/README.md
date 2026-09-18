# `docs/knowledge/approved/` — conocimiento aprobado del flujo de `knowledge-services`

Fuente de verdad de las entradas que ya pasaron por `docs/knowledge/candidates/` y fueron
promovidas (ADR-018). **Ownership: únicamente el agente `knowledge-curator` escribe aquí**
(T-04) — es quien mueve un candidato desde `candidates/` tras aprobarlo; ningún otro agente
crea, edita ni borra ficheros bajo este árbol directamente.

Estructura: una carpeta por `categories[].folder` de `.claude/knowledge-services/taxonomy.json`
(o de la plantilla por defecto del plugin si el proyecto no configura nada — ver
`agent-kits/shared/templates/taxonomy.json`), con un fichero Markdown por entrada. Frontmatter:
`id` (con el `id_prefix` de la taxonomía, forma `[A-Za-z0-9._-]+`, sin `/` ni `\`), `category`
(**obligatoria**, clave de `categories[].key` — ver nota de migración más abajo), `version`
(entero, 1 si es nueva), `enlaces` (opcional, ids de otras entradas de este mismo árbol).
`agent-kits/shared/knowledge-index.py` (T-02) construye el índice determinista SOLO sobre estas
carpetas: falla con fichero+campo si hay un `id` duplicado o con forma inválida, falta
`version`/`category`, `category` no está declarada en la taxonomía, o un enlace roto.

**Vocabulario del campo opcional `estado` del frontmatter (gap 34, revisión de dos lentes):** si
se declara, su único valor válido bajo este árbol es el token en español `aprobado` (coherente
con el resto de tokens parseados en español del plugin, aunque las carpetas sean inglesas —
`docs/CONVENTIONS.md`). Lo exige `knowledge-index.py`; `knowledge-curator` (T-04) escribe ese
mismo token al mover un candidato aquí.

**Nota de migración (gap 113, revisión de dos lentes Fase 3 intento 2, 2026-09-18):** `category`
era opcional cuando este árbol nació y pasó a **obligatoria** en `T-02-fix6`/`T-04-fix4`
(`knowledge-index.py` la exige al indexar, `curator-gate.py` bloquea `approve` sin ella). Un
proyecto con entradas `approved/` escritas ANTES de ese cambio y sin `category` en su frontmatter
verá `knowledge-index.py` fallar con `falta \`category\`` para esas entradas: añade manualmente el
campo `category: <clave-de-taxonomy.json>` a cada una (la clave correcta es la de la carpeta que
las contiene, `categories[].folder`, si esa carpeta sirve a una sola categoría; si sirve a varias
— ver el aviso de más arriba sobre `folder` compartido —, decide cuál es la real caso a caso, como
haría `knowledge-curator` en P2 de su proceso).

Este árbol es **distinto** del legado `docs/knowledge/{adr,gotchas,lessons}/` (memoria técnica
del propio plugin, con su índice manual en `docs/knowledge/README.md`, ADR-006 D4): no lo
sustituye ni lo migra. Sirve al flujo de `knowledge-services` para proyectos que declaren su
propia taxonomía.

Cualquier exportación a un backend declarado (p. ej. Kwipu, `type: markdown-export`) se
**deriva** de este árbol y nunca se versiona (ver `.gitignore`:
`.claude/knowledge-services/*-export/`).
