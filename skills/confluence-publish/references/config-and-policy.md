# confluence-publish — config `.claude/confluence.json` y política de publicación («qué sube y qué no»)

> Referencia de la skill `confluence-publish` (y fuente normativa que cita `confluence-pull`). Léela **solo** cuando tengas que crear o explicar la config, o decidir si un fichero concreto entra en el espejo. La invariante `docs/security-scan/**` (nunca se publica) está también en el `SKILL.md`; aquí va la tabla completa de exclusiones y sus razones.

## Config `.claude/confluence.json` (gestión interna, no la pide el usuario)

La escribe/actualiza la skill; el usuario no la edita a mano. Formato en
`assets/confluence.example.json`. Campos: `cloudId`, `spaceKey`, `anchor` (`mode`
root/child + `parentPageId`/`parentTitle`), `home` (`title` + `pageId` de caché) y `publish`
(`source`, `layout`, `include`, `exclude`, `onConflict`). Si falta `cloudId`, resuélvelo con
`getAccessibleAtlassianResources` (uno solo → úsalo; varios → pregunta por nombre) y persístelo.

**`publish` — defaults aprobados de la política (ver sección normativa más abajo):**

| Campo | Default | Nota |
|---|---|---|
| `staging` | `true` | D5: con `staging=true`, `--stage` regenera `docs/confluence/` antes de cada publicación (ver más abajo) |
| `source` | `docs/confluence` con staging activo; `docs` si `staging=false` o el script degrada | Raíz que se recorre para construir el árbol de páginas |
| `layout` | `mirror-tree` | Carpetas → páginas, `.md` → páginas hijas |
| `include` | `["**/*.md"]` | Sin cambio: la política se expresa en `exclude` (opt-out) |
| `exclude` | ver `assets/confluence.example.json` (`_comment_exclude` explica cada patrón) | `docs/security-scan/**` es invariante no negociable; `docs/confluence/**` se autoexcluye siempre por código, no hace falta listarla |
| `onConflict` | `update` | Sin cambio |

`SKILL.md` y `confluence.example.json` deben ir siempre sincronizados: si cambia una lista,
cambia la otra en el mismo commit.

## Qué sube y qué no (política de publicación — normativa)

> Fuente completa de la decisión: `docs/roadmap/2026-08-20-confluence-policy/spec.md`. Esta
> sección resume la política **vigente** para quien configure o audite un espacio. Matriz
> disparador → artefacto → ¿se publica? (los 10 disparadores conocidos): `docs/FLOWS.md`
> sección "5 · Confluence".

La política es **opt-out**: `include: ["**/*.md"]` y una lista de `exclude` cierra lo que NO se
publica. Un documento nuevo bajo `docs/` se publica **por defecto**, salvo que caiga en una de
estas exclusiones:

| Exclusión | Por qué |
|---|---|
| `docs/security-scan/**` | **Invariante no negociable** — datos sensibles del agente `nemesis`. Verificable con `confluence-scope.py --check` (exit ≠ 0 si falta). |
| `docs/en/**` | Árbol EN duplicado: es la traducción para lectores de GitHub, no del espacio de Confluence. |
| `docs/examples/**` | Documentación interna del **plugin** (ejemplos de cómo se construyen los agentes), no del producto del proyecto consumidor. |
| `docs/agents/**` | Ídem: documentación de cómo está hecho cada agente, no de qué hace el proyecto. |
| `docs/**/atlassian-connector-notes.md` | Notas de trabajo sobre el propio conector Atlassian. |
| `docs/roadmap/**/improvement-plan.md`, `tasks.md`, `test-plan.md` | Tablero de **ejecución** (plan y ledger): su sitio es el repo y Jira, no Confluence (D1). Confluence guarda la **decisión** (`spec.md`), el **presupuesto** (`evaluation.md`), la **arquitectura** (`design.md`, agente `architect` — se publica, no está en el `exclude`) y el **resultado** (`retro.md`) de cada iniciativa — no el plan detallado ni el progreso tarea a tarea. |
| `docs/knowledge/journal/**` | **Bitácora de sesión** generada por el hook `SessionEnd` (`agent-kits/shared/journal.py`, iniciativa `memory-health`): cronológica y **no curada** — es lo que pasó en cada sesión, no una decisión. La memoria **curada** de `docs/knowledge/` (`adr/`, `gotchas/`, `lessons/`) sí se publica; lo del journal que merezca doctrina se promueve allí primero (regla 10 de CONVENTIONS). |
| `**/testing/**` | El informe de `qa` (`report.md`/`report.pdf`, `screenshots/`, `raw/`) embebe capturas que el conector no puede adjuntar (saldrían rotas). Queda **solo-local** (D4); sigue disponible completo en el repo. |
| `docs/confluence/**` | La propia carpeta **staged** generada por `--stage` (D5) — se autoexcluye SIEMPRE (por código, no por config) para que un `--stage` no se anide dentro del anterior. |
| `**/node_modules/**` | Dependencias, nunca documentación. |

**Consecuencia visible:** con esta política, el ledger `tasks.md` de una iniciativa **nunca**
aparece en Confluence, aunque `implementer` dispare la sincronización al cerrar cada fase (D3) —
ese disparo refresca lo demás que haya cambiado bajo `docs/` (típicamente `dashboard.md`), no el
ledger en sí. Un proyecto que quiera verlo publicado tiene que añadirlo a `include` a mano; no es
opción de primera clase (D2: sin presets de audiencia).

**`docs/knowledge/**` SÍ se publica** (memoria técnica del proyecto —
`2026-08-20-knowledge-capture`), **salvo `docs/knowledge/journal/**`** (bitácora de sesión, excluida arriba): el resto no está en el `exclude`, así que entra en el espejo como
cualquier otra documentación de **decisión/resultado** — igual que `spec.md`/`evaluation.md`/
`retro.md` por iniciativa. Contiene ADR (`adr/`), trampas comprobadas (`gotchas/`) y lecciones de
proceso (`lessons/`) — un fichero por entrada; a diferencia de `tasks.md`, no es tablero de ejecución, así que no cae en
la exclusión D1. Verificable con `confluence-scope.py --status`: un fichero de ejemplo bajo
`docs/knowledge/` aparece **en alcance**, no en la lista de excluidos.

**Stubs `gotchas.md`/`LESSONS.md` (`knowledge-split`): no requieren caso especial.** Solo existen
en este repo (que no publica — no hay `confluence.json` propio) y en proyectos que ya tenían el
árbol antiguo; un consumidor nuevo nace con `gotchas/`/`lessons/` directas, sin stub que publicar.
Si un proyecto heredara un stub y no quisiera publicarlo, lo añade a su propio `exclude`.

**`docs/confluence/` — la carpeta staged (D5):**

- **Derivada, no editable.** `confluence-scope.py --stage` la regenera POR COMPLETO en cada
  ejecución; cualquier edición manual se pierde en la siguiente. Lleva un fichero de aviso con el
  comando que la produjo llamado **`_STAGING-LEEME.md`** (nombre reservado, nunca `README.md`): así
  no pisa la copia real de un `docs/README.md` canónico ni colisiona con ningún otro README del
  árbol — queda excluido del alcance en cualquier carpeta.
- **Es la respuesta visual a "¿qué sube?"**: copia byte a byte de los `.md` en alcance, misma
  estructura de carpetas (sin el prefijo `docs/`). No hay que interpretar los `exclude`: lo que
  está ahí es exactamente lo que se publica.
- **`confluence-pull` nunca escribe aquí.** Un cambio bajado de Confluence se escribe siempre en
  el fichero **canónico** de `docs/`, resuelto con el mapeo inverso `confluence-scope.py --map`
  (ver `skills/confluence-pull/SKILL.md`).
- **Degradación:** si `confluence-scope.py` falla o no está disponible, la skill vuelve a
  `publish.source = "docs"` y resuelve `include`/`exclude` en línea (comportamiento anterior a
  D5), sin bloquear el ciclo del agente que llamó.
- **Invocación normal: siempre `--root "$PWD"`, nunca `--out`/`--docs` a mano** (ver bloques bash
  arriba). Si alguna vez invocas `confluence-scope.py` manualmente con `--out`/`--docs`, son
  relativos a `--root` (ubicaciones DENTRO del proyecto), no al directorio desde el que lanzas el
  comando — al revés que `--config`/`--state`, que sí son relativos al cwd (documentado en el
  `--help` del script tras la revisión adversarial: `--root demo --out demo/docs` anida en
  `demo/demo/docs` si se le pasa un `--out` ya prefijado con la ruta de `--root`).
  **Dónde están esos bloques bash:** en `references/publish-and-sync.md` («Publicar», paso 0, y «Staging»), no en este fichero.
