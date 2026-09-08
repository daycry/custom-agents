---
id: ADR-010
titulo: Journal de sesión como memoria episódica DETERMINISTA (hook SessionEnd); el hook ESCRIBE lo que no puede devolver — decisiones/pendientes del log crudo y resumen por IA opt-in (revisado 2026-09-08)
estado: aceptada (validada por revisión de dos lentes, 2026-09-03, intento 2; revisada 2026-09-08 — memory-retrieval T-12/T-13, ver §Revisión)
fecha: 2026-09-03
revisada: 2026-09-08
iniciativa: memory-health
---

# ADR-010: Journal de sesión como memoria episódica determinista; el hook escribe lo que no puede devolver

> **Revisada el 2026-09-08** (iniciativa `memory-retrieval`, T-12/T-13; spec CA-20). La restricción del
> Contexto sigue siendo **cierta** y se conserva tal cual; lo que cambia es la **conclusión** — ver
> §Revisión al final. Las secciones Decisión y Consecuencias se dejan como se escribieron el 2026-09-03
> (registro histórico) con un puntero donde la revisión las matiza.

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
la doc cambia (regla de los 90 días de `plugin-dev`). *(Revisado 2026-09-08: la premisa sigue en pie, la
conclusión no — ver §Revisión.)*

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
*(Revisado 2026-09-08: la iniciativa fue `memory-retrieval`, y la vía no fue esperar a que cambiara el
contrato sino leerlo mejor — §Revisión.)*

## Revisión (2026-09-08 — memory-retrieval T-12/T-13)

**Lo que sigue siendo cierto y se conserva.** La doc oficial (`hooks.md` + `hooks-guide.md`, releída el
2026-09-08) mantiene los tres hechos del Contexto: la **salida** de los hooks de `SessionEnd` se ignora,
los hooks `prompt`/`agent` devuelven solo `ok/reason`, y el presupuesto compartido de 1,5 s sube hasta el
`timeout` declarado (máx. 60 s). **Ninguna de las tres restricciones se borra de este ADR.** La
alternativa «hook `prompt`/`agent` en `SessionEnd` que redacte el resumen» sigue descartada por la misma
razón de entonces.

**Lo que se revisa: la conclusión era más fuerte que su premisa.** «No hay contrato para que un hook
*devuelva* texto persistible» es verdad — pero el hook `command` no necesita **devolver** nada: puede
**escribir**. El análisis de `memory-retrieval` midió el hueco que esa conclusión dejó: `decisiones: []` y
`pendientes: []` **siempre** en modo hook, con el `resumen` reducido al primer prompt de una transcripción
de formato no oficial. Con la premisa intacta, la conclusión pasa a ser:

1. **Captura del turno (T-11).** Un hook `UserPromptSubmit` (`hooks/user-prompt-capture.sh` →
   `journal.py capture`) acumula el turno del usuario en un log crudo **no versionado**
   (`.claude/session-prompts-<session_id>.log`, `*.log` en `.gitignore`) con opt-out por turno
   (`<private>`: el log no se toca) y por proyecto (`dev.json` `sesion.journal` o `sesion.captura` a
   `false`). Contrato verificado el 2026-09-08 (`hooks-guide.md`): «`UserPromptSubmit` hooks get the
   `prompt` text», con `session_id` entre los campos comunes a todo evento; el stdout de ese evento **se
   inyecta como contexto** y un exit 2 **borra el prompt**, por eso el hook no emite nada y sale siempre 0.
2. **El hook `SessionEnd` escribe él mismo `decisiones` y `pendientes` (T-12).** Extracción
   **determinista** del log (frases del usuario con un marcador léxico ES/EN: `decidimos`, `acordamos`,
   `optamos por`, `we decided`… / `pendiente`, `queda por`, `más tarde`, `TODO:`, `remind me`…; ≤ 8 por
   lista, deduplicadas). Sin log o sin marcadores → `[]` **honesto**, no inventado. Sigue idempotente por
   `session_id`.
3. **El resumen por IA que este ADR difería existe como opt-in (T-13).** `dev.json` `sesion.resumen: true`
   → tras dejar en disco la entrada determinista, el propio hook `command` lanza `claude -p --bare
   --output-format json` — el CLI headless que ya usaba `evals/run.py`, **no** un hook `prompt`/`agent` —
   y re-escribe la misma entrada (`resumen_por: ia`). `--bare` salta hooks, plugins y MCP (sin recursión;
   además una guardia por variable de entorno) y exige `ANTHROPIC_API_KEY`. Sin CLI, sin clave, timeout
   (25 s; `hooks.json` sube el `timeout` del hook a 45), exit ≠ 0 o JSON ilegible → queda la determinista
   con el motivo en `avisos`, exit 0. El cierre de sesión nunca se entera.

**Lo que no cambia.** El ADR **no** pasa a `obsoleta`: su parte cierta sigue siendo doctrina y ningún ADR
la sustituye. El journal sigue siendo memoria **no curada** y excluida de Confluence. La promoción a
doctrina gana un camino mecánico (T-14): `journal.py candidatas` propone como `propuesta` — nunca
`aceptada` — los patrones repetidos en ≥ 2 sesiones, por la puerta de `/retro`.

## Estado

`propuesta` — a validar por la revisión de dos lentes de la iniciativa `memory-health` o el usuario en la
puerta. Pasa a `aceptada` cuando se valide; a `obsoleta` si el contrato oficial cambia y una decisión
posterior la reemplaza (enlazar aquí a la que la sustituya). *(Ciclo de vida: validada `aceptada` el
2026-09-03; **revisada, no reemplazada**, el 2026-09-08 — el frontmatter es la fuente del estado vigente.)*
