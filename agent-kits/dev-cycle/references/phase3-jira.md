### Ciclo Jira de la Fase 3 (opt-in, `.claude/jira.json` `enabled: true`) — la secuencia, UNA sola vez

El estado del issue, los comentarios y las horas los produce **`jira-flow.py`** (skill `jira-sync`,
Paso 7): tú no redactas comentarios ni compones llamadas — el script devuelve `ops` (etiqueta →
transición → comentario → worklog) **ya firmadas por el agente** y en orden; ejecútalas seguidas con
las tools del conector y, **solo si todas respondieron bien**, ejecuta el comando `confirmar` que trae
el plan (con `--comentario-id` del comentario creado): sin confirmar, el evento sigue pendiente y el
siguiente plan avisa de buscar su referencia en el issue antes de publicar. Una llamada por evento y tarea (con granularidad `fase`, `--batch` agrupa las
tareas de la fase en un comentario). El **ledger sigue siendo la fuente**; Jira es espejo.

| Evento | Cuándo | Quién lo dispara | Transición | Comentario (firma) | Worklog |
|---|---|---|---|---|---|
| `arrancar` | al abrir `T-XX` | `implementer` | → *En curso* | — | — |
| `implementado` | criterios cumplidos | `implementer` | *(sigue En curso)* | `ca-implementer`: qué hizo, evidencia, ficheros | implementación (horas medidas) |
| `revision` | cierre de intento sin gaps | `adversarial-review` (su paso 6, por intento; **no** el orquestador ni `reviewer`) | — | `ca-reviewer`: veredicto por criterio | `[revisión] --attempt N` |
| `gaps` | cierre de intento con gaps | `adversarial-review` (su paso 6, por intento; **no** el orquestador ni `reviewer`) | → *En curso* (reabre) | `ca-reviewer`: gaps graduados | `[revisión] --attempt N` |
| `qa-verde` / `qa-rojo` | veredicto de `qa-gate.py` | `qa` | — | `ca-qa`: X/Y del gate + evidencias | — |
| `aprobado` | revisión sin gaps **y** qa verde | **el orquestador (tú)**, `--actor orquestador --qa-verde` | → *Done* | `ca-orquestador`: cierre con la evidencia | — |

**`aprobado` es TUYO y con evidencia (no a ciegas).** `jira-flow.py` lo rechaza (exit 2, `ops: []`,
con la razón) si el ledger no tiene una última sección `## Revisión de dos lentes — intento N` sin
gaps pendientes para esas tareas, o si no le pasas `--qa-verde` — flag que pasas **solo tras leer el
exit 0 de `agent-kits/qa/qa-gate.py`**, nunca por el resumen de `qa`. Es el único evento que ve los
dos veredictos, y por eso el único que puede cerrar el issue.

**Cómo se entera el `implementer` de los gaps:** por su **brief** (`task-brief.py` inyecta los gaps
del último intento desde el ledger), no por Jira — el comentario `gaps` es el espejo para el equipo.
Sin Jira activado, el ciclo es idéntico salvo que no se publica nada: el script lee
`.claude/jira.json` y con `enabled` ≠ `true` devuelve `ops: []` y `jira: "desactivado"` (exit 0, sin
ruido). Reejecutar una fase tampoco duplica: cada plan con `ops` queda anotado en `jira-state.json`
(`flow[...]`) y repetir el mismo evento da `ops: []` + `yaRealizado: true` (`--force` para repetirlo
a propósito). En `revision`/`gaps`, `--intento N` es obligatorio.
