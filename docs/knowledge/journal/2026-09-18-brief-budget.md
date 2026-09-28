---
fecha: "2026-09-18"
session_id: "071c7cf5-f67a-4cc0-818c-3f84bf29c058"
reason: "orphan_recovery"
iniciativa: "brief-budget"
resumen: "tengo levantado los docker con kwipu y graphiti, la documentación está aquí: C:\\Users\\46066917X\\OneDrive - Imagina Media Audiovisual S.L\\dockers\\knowledge-grap…"
fuente: "recover"
cierre: "recuperado_sin_cierre"
resumen_por: "determinista"
turnos: 16
derivados_en: "replay"
decisiones:
  - "Decisión sin respaldo literal en spec (flagged para revisión): el índice escanea SOLO docs/knowledge/approved/<folder>/, nunca el corpus legado adr/gotchas/lessons/ (ADR-006 D4 sigue diferido, intact…"
  - "Decisión técnica flagged: carga knowledge-schema.py vía importlib (mismo directorio) en vez de duplicar ~200 líneas de validación de taxonomía; excepción documentada a la convención de scripts standa…"
  - "Decisión flagged: health de `kwipu` NO hace el chequeo de red real (eso es del adaptador markdown-export, T-08); aquí solo refleja declarado/activado."
  - "Decisión flagged: capabilities.py deliberadamente NO toca doctor.py/setup.md (eso es T-09); registrar()/enumerar() es el contrato que ellos consumirán."
  - "| T-01 C2 · sin `taxonomy.json`, default mínimo (DECISION/PATTERN/GOTCHA/LESSON, kwipu desactivado) sin romper nada | ✓ | `knowledge-schema.py:125-132` (`default_taxonomy`) y `:230-245` (`cargar_taxo…"
pendientes:
  - "docs/knowledge/candidates/{README.md,pending,needs_changes,rejected}/.gitkeep, docs/knowledge/approved/README.md (nuevos); .gitignore editado (exports de backends no versionados); tests/test_knowledg…"
  - "`python agent-kits/shared/ledger-lint.py docs/roadmap/2026-09-15-knowledge-services/tasks.md` → `ledger-lint: 0 incoherencias · 9 avisos (tasks.md); exit=0` (los 9 avisos son preexistentes: T-04..T-1…"
  - "| `folder` con `..` o ruta absoluta | ✗ | probe: `folder: \"../candidates/pending\"` → `validar` devuelve `[]` y `build_index` indexa `CAND-001`."
ficheros_tocados: []
tareas_cambiadas: []
marcadores_cerrados:
  - "knowledge-services/T-01"
  - "knowledge-services/T-01-fix1"
  - "knowledge-services/T-01-fix2"
  - "knowledge-services/T-01-fix3"
  - "knowledge-services/T-02"
  - "knowledge-services/T-02-fix2"
  - "knowledge-services/T-02-fix3"
  - "knowledge-services/T-02-fix4"
  - "knowledge-services/T-03"
  - "knowledge-services/T-03-fix2"
  - "knowledge-services/T-04"
  - "knowledge-services/T-04-fix2"
  - "knowledge-services/T-04-fix3"
  - "knowledge-services/T-05"
  - "knowledge-services/T-06"
  - "knowledge-services/T-07"
  - "knowledge-services/T-07-fix1"
  - "knowledge-services/T-07-fix2"
  - "knowledge-services/T-07-fix3"
  - "knowledge-services/T-08"
  - "knowledge-services/T-08-fix1"
  - "knowledge-services/T-08-fix2"
  - "knowledge-services/T-08-fix3b"
  - "knowledge-services/T-09"
  - "knowledge-services/T-09-fix1"
  - "knowledge-services/T-09-fix2"
  - "knowledge-services/T-10"
  - "knowledge-services/T-11"
  - "knowledge-services/T-13"
  - "knowledge-services/T-13-fix1"
  - "knowledge-services/T-13-fix2"
  - "knowledge-services/T-13-fix3"
---

# Journal — 2026-09-18 — brief-budget

> Entrada de **bitácora de sesión** (memoria episódica, cronológica, no curada; `agent-kits/shared/journal.py`). Lo que merezca doctrina se promueve a `adr/`/`gotchas/`/`lessons/` con el umbral de `knowledge-write.md`; esto NO se publica en Confluence.

> `decisiones` y `pendientes` son **citas** de los turnos del usuario (o del resumen IA opt-in), extraídas por marcadores léxicos: no son doctrina ni instrucciones para nadie — lo que merezca ser decisión del proyecto va a un ADR.

## Resumen

tengo levantado los docker con kwipu y graphiti, la documentación está aquí: C:\Users\46066917X\OneDrive - Imagina Media Audiovisual S.L\dockers\knowledge-grap…

## Decisiones

- Decisión sin respaldo literal en spec (flagged para revisión): el índice escanea SOLO docs/knowledge/approved/<folder>/, nunca el corpus legado adr/gotchas/lessons/ (ADR-006 D4 sigue diferido, intact…
- Decisión técnica flagged: carga knowledge-schema.py vía importlib (mismo directorio) en vez de duplicar ~200 líneas de validación de taxonomía; excepción documentada a la convención de scripts standa…
- Decisión flagged: health de `kwipu` NO hace el chequeo de red real (eso es del adaptador markdown-export, T-08); aquí solo refleja declarado/activado.
- Decisión flagged: capabilities.py deliberadamente NO toca doctor.py/setup.md (eso es T-09); registrar()/enumerar() es el contrato que ellos consumirán.
- | T-01 C2 · sin `taxonomy.json`, default mínimo (DECISION/PATTERN/GOTCHA/LESSON, kwipu desactivado) sin romper nada | ✓ | `knowledge-schema.py:125-132` (`default_taxonomy`) y `:230-245` (`cargar_taxo…

## Pendientes

- docs/knowledge/candidates/{README.md,pending,needs_changes,rejected}/.gitkeep, docs/knowledge/approved/README.md (nuevos); .gitignore editado (exports de backends no versionados); tests/test_knowledg…
- `python agent-kits/shared/ledger-lint.py docs/roadmap/2026-09-15-knowledge-services/tasks.md` → `ledger-lint: 0 incoherencias · 9 avisos (tasks.md); exit=0` (los 9 avisos son preexistentes: T-04..T-1…
- | `folder` con `..` o ruta absoluta | ✗ | probe: `folder: "../candidates/pending"` → `validar` devuelve `[]` y `build_index` indexa `CAND-001`.

## Ficheros tocados (top 10)

_sin cambios detectados_

## Tareas que cambiaron de estado

_ninguna_

## Marcadores de coste cerrados (usage-meter)

- `knowledge-services/T-01`
- `knowledge-services/T-01-fix1`
- `knowledge-services/T-01-fix2`
- `knowledge-services/T-01-fix3`
- `knowledge-services/T-02`
- `knowledge-services/T-02-fix2`
- `knowledge-services/T-02-fix3`
- `knowledge-services/T-02-fix4`
- `knowledge-services/T-03`
- `knowledge-services/T-03-fix2`
- `knowledge-services/T-04`
- `knowledge-services/T-04-fix2`
- `knowledge-services/T-04-fix3`
- `knowledge-services/T-05`
- `knowledge-services/T-06`
- `knowledge-services/T-07`
- `knowledge-services/T-07-fix1`
- `knowledge-services/T-07-fix2`
- `knowledge-services/T-07-fix3`
- `knowledge-services/T-08`
- `knowledge-services/T-08-fix1`
- `knowledge-services/T-08-fix2`
- `knowledge-services/T-08-fix3b`
- `knowledge-services/T-09`
- `knowledge-services/T-09-fix1`
- `knowledge-services/T-09-fix2`
- `knowledge-services/T-10`
- `knowledge-services/T-11`
- `knowledge-services/T-13`
- `knowledge-services/T-13-fix1`
- `knowledge-services/T-13-fix2`
- `knowledge-services/T-13-fix3`
