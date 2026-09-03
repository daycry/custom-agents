---
id: ADR-010
titulo: Journal de sesión como memoria episódica DETERMINISTA (hook SessionEnd); resumen por IA diferido hasta que el contrato oficial lo permita
estado: aceptada (validada: revisión de dos lentes, 2026-09-03, intento 2)
fecha: 2026-09-03
iniciativa: memory-health
---

# ADR-010: Journal de sesión como memoria episódica determinista; resumen por IA diferido

## Contexto

El plugin tenía memoria **curada** (`docs/knowledge/`: ADR, gotchas, lecciones — con umbral y estado) y
un contexto de retoma del roadmap (`progress-report.py session`: *qué tarea* está abierta), pero ninguna
memoria **episódica**: al reanudar una sesión nadie sabía *qué pasó* en la anterior (qué ficheros se
tocaron, qué tareas cambiaron de estado, qué quedó a medias). Las alternativas del mercado resuelven esto
con servidores MCP de memoria (dependencia externa, estado fuera del repo) o con un resumen redactado por
el modelo al cerrar la sesión.

La doc oficial de hooks (`code.claude.com/docs/en/hooks.md` + `hooks-guide.md`, verificada 2026-09-03)
fija tres hechos: (1) `SessionEnd` recibe `session_id`, `transcript_path`, `cwd`, `reason`
(`clear|resume|logout|prompt_input_exit|other`) y **su salida se ignora** («Output and exit code are
ignored, except `terminalSequence`»); (2) todos los hooks de `SessionEnd` comparten un **presupuesto de
1,5 s**, ampliable hasta 60 s con `timeout` por hook; (3) los hooks `prompt`/`agent` devuelven **solo una
decisión** `{"ok", "reason"}` — no hay contrato para que devuelvan texto que se escriba a disco, y en
`SessionEnd` esa salida también se ignora.

## Decisión

El journal se implementa como **script determinista sin modelo** (`agent-kits/shared/journal.py`) que un
hook `command` de `SessionEnd` (`hooks/session-journal.sh`, `timeout: 20`) ejecuta para escribir
`docs/knowledge/journal/AAAA-MM-DD-<slug>.md`: fecha, iniciativa activa (`progress-report.py active`),
ficheros tocados por git (top 10), tareas del ledger cuyo estado cambió respecto a HEAD, marcadores del
usage-meter cerrados hoy y, como resumen best-effort, el primer prompt del usuario de la transcripción.
Es **idempotente por `session_id`** (la misma sesión actualiza su entrada) y `SessionStart`
(`startup|resume`, no `compact`) reinyecta la última entrada compactada (≤ 25 líneas). El journal es
memoria **no curada**: `evaluator`/`planner`/`architect` leen solo la última entrada de su iniciativa,
`/retro` la usa como fuente de causas de desviación, lo que merezca doctrina se **promueve** a
ADR/gotcha/lección, y `docs/knowledge/journal/**` queda **excluido de Confluence**. Opt-out por proyecto:
`dev.json` `sesion.journal: false`.

El **resumen por IA** (`resumen`/`decisiones`/`pendientes` redactados por un modelo a partir de la
transcripción) **no se implementa**: no hay contrato oficial que lo soporte en `SessionEnd`. Queda el
punto de enganche manual `journal.py write --enrich <json>` y esta ADR como marcador para re-evaluar si
la doc cambia (regla de los 90 días de `plugin-dev`).

## Alternativas descartadas

- **Servidor MCP de memoria** — dependencia externa y estado fuera del repo (no versionado, no
  revisable, no publicable por la política de Confluence); contradice el principio del plugin de que la
  memoria del proyecto vive en `docs/`.
- **Hook `prompt`/`agent` en `SessionEnd` que redacte el resumen** — la doc oficial solo permite devolver
  `ok/reason`, la salida en `SessionEnd` se ignora y los hooks `agent` son experimentales; implementarlo
  sería fingir una capacidad que el contrato no da (honestidad > feature).
- **Que el agente escriba el journal a mano al terminar** — depende de que el modelo se acuerde (lo mismo
  que se quería evitar) y no cubre las sesiones que terminan sin cierre explícito (`/clear`, logout).
- **Guardar el journal dentro de `docs/knowledge/README.md`** — mezclaría bitácora cronológica con memoria
  curada indexada; el índice de entrada perdería su función de lectura selectiva.

## Consecuencias

Se gana memoria episódica entre sesiones **sin dependencias**, con coste fijo (un hook local, ≤ 25 líneas
al arrancar) y trazable en git. Se renuncia, por ahora, a un resumen redactado: la entrada dice *qué se
tocó*, no *por qué* — ese «por qué» se anota a mano (`--enrich`) o se promueve a ADR cuando importa. Queda
condicionado a la doc oficial: si `SessionEnd` admitiera hooks con salida útil, o los hooks `prompt`
pudieran devolver texto persistible, se abriría una iniciativa de vía rápida para el resumen opt-in.

## Estado

`propuesta` — a validar por la revisión de dos lentes de la iniciativa `memory-health` o el usuario en la
puerta. Pasa a `aceptada` cuando se valide; a `obsoleta` si el contrato oficial cambia y una decisión
posterior la reemplaza (enlazar aquí a la que la sustituya).
