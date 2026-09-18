# `docs/knowledge/journal/` — bitácora de sesión (memoria episódica)

Una entrada por sesión, **generada** por `agent-kits/shared/journal.py` (hook `SessionEnd`; la
última se reinyecta al arrancar/retomar). Cronológica y **no curada**: lo que merezca doctrina
se promueve a `adr/`, `gotchas/` o `lessons/` con el umbral de `knowledge-write.md`. **Excluida de
Confluence** (`docs/knowledge/journal/**`). Nombre: `AAAA-MM-DD-<iniciativa activa | sesion>.md` (sufijo `-2`
si otra sesión del día ya lo usó). **Las entradas se versionan** (memoria del proyecto, como ADR y lecciones);
quien no quiera versionarlas añade `docs/knowledge/journal/*.md` (no este README) a su `.gitignore`.
Este índice lo regenera `journal.py index`; no lo edites (la tabla siguiente y el resto del
párrafo sí, hasta la próxima regeneración).

**Campos de frontmatter de cada entrada** (`agent-kits/shared/journal.py:render`, iniciativa
`session-end-durable-capture`):

| Campo | Valores | Qué significa |
|---|---|---|
| `cierre` | `materializado` · `recuperado_sin_cierre` · `dead_letter` (solo en la cola, nunca en una entrada del journal) | Con qué garantía se cerró la sesión: envelope verificado, recuperada del log de prompts sin cierre, o descartada antes de llegar aquí |
| `fuente` | `hook` · `recover` · `manual` | Quién generó la entrada: el hook `SessionEnd` vía `replay`, `journal.py recover` sobre una sesión huérfana, o un enriquecido a mano (`--enrich`) |
| `reason` | motivo declarado en el envelope de `SessionEnd`, o `orphan_recovery` | Motivo de cierre; `orphan_recovery` marca una entrada creada por `recover` porque nunca hubo envelope |
| `derivados_en` | `replay` · `recover` | En qué fase se calcularon con git `ficheros_tocados`/`tareas_cambiadas` (nunca en el teardown de `SessionEnd`, CA-01) |
| `materializado_en` | timestamp ISO UTC | Cuándo se escribió la entrada final en disco (no la fecha del cierre de sesión) |

| Fecha | Iniciativa | Resumen | Fuente |
|---|---|---|---|
| [2026-09-14](2026-09-14-plugin-refactor.md) | plugin-refactor | Sesión sobre plugin-refactor | hook |
| [2026-09-12](2026-09-12-plugin-refactor.md) | plugin-refactor | <task-notification> <task-id>aa201799db814ce28</task-id> <tool-use-id>toolu_01JKEBQeC2u77f6UwbYeDnn… | hook |
| [2026-09-08](2026-09-08-sesion.md) | n/a | continua con la implementación | hook |
