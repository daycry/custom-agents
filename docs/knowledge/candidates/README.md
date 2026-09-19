# `docs/knowledge/candidates/` — conocimiento propuesto, sin aprobar

Fuente de verdad SOLO para conocimiento en tránsito hacia `approved/` (ADR-018,
`knowledge-services`). **Ownership: únicamente el agente `knowledge-curator` escribe aquí**
(T-04) — ningún otro agente crea, mueve ni borra ficheros bajo este árbol; `documenter`
**propone** candidatos, no los promociona (T-05, `docs/agents/ROLES.md`).

Subcarpetas (estado del candidato, no una categoría de la taxonomía):

- **`pending/`** — propuesto, aún sin revisar por el Curator.
- **`needs_changes/`** — revisado, con observaciones que resolver antes de reintentar.
- **`rejected/`** — revisado y descartado (se conserva por trazabilidad, no se re-propone).

Un candidato promovido se **mueve** a `docs/knowledge/approved/<folder>/` (el `folder` lo decide
la categoría de la entrada según `.claude/knowledge-services/taxonomy.json`, o la plantilla por
defecto del plugin si el proyecto no configura nada). `agent-kits/shared/knowledge-index.py`
(T-02) **nunca** escanea este árbol: un candidato no aprobado no puede aparecer en el índice ni
exportarse a ningún backend.

**Vocabulario (gap 34, revisión de dos lentes):** `pending`/`needs_changes`/`rejected` son
nombres de CARPETA (estado del candidato en este flujo), no un valor del campo `estado` del
frontmatter — ese campo solo tiene sentido, con el token `aprobado`, una vez la entrada vive bajo
`docs/knowledge/approved/<folder>/` (ver `docs/knowledge/approved/README.md`). No mezclar ambos
vocabularios al escribir o leer una entrada.
