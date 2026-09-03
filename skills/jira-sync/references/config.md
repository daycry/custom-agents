# jira-sync — config `.claude/jira.json` y estado `.claude/jira-state.json`

> Referencia de la skill `jira-sync`. Léela **solo** cuando tengas que crear, leer o explicar un campo de la config o del manifiesto de estado (Pasos 0, 0-bis, 0-ter, 5 y 7 los usan). Mapa general de configs: regla 9 de `docs/CONVENTIONS.md`.

## Config `.claude/jira.json` (gestión interna, editable)

La escribe/actualiza la skill; el usuario puede ajustarla. Campos:

- `enabled` (`true`/`false`) — opt-in del proyecto (como Confluence).
- `granularidad` (`"tarea"` por defecto · `"fase"`) — un issue por tarea, o uno por fase con sus tareas como checklist (Paso 0-bis). Si falta, se pregunta una vez y se persiste.
- `assignee` (`"me"` por defecto · `"none"`) — a quién se asignan los issues que crea la skill (Paso 0-ter): `"me"` fija el accountId propio, `"none"` los deja sin asignar. Evita depender del "asignado por defecto" del proyecto. Si falta, se pregunta una vez y se persiste.
- `cloudId` — site Atlassian (se resuelve solo si falta).
- `horasJornada` — **máximo de horas imputables por DÍA** (acumulado de todas las tareas), no por tarea; `8` por defecto, `7` en jornada intensiva. **Se lee de `.claude/rates.json`** (config compartida); `jira.json` solo lo sobreescribe si quieres un valor distinto para Jira.
- `alCubrirJornada` (por defecto `preguntar`) — qué hacer al llegar al tope diario: `preguntar` · `parar` · `seguir` · `banco`. Ver "Tope de jornada diario". (Específico de Jira → vive en `jira.json`.)
- `ratioSupervision` — para derivar la supervisión cuando no viene como `real`; también **de `.claude/rates.json`** (`0.25` por defecto).
- `defaults` (opcional) — `projectKey`, `parentKey`, `issueType`, `labels` para repetir de un clic.

Estado en `.claude/jira-state.json`: el **mapeo `T-XX → issueKey`** (modo tarea) o **`fase-N → issueKey`** (modo fase; el valor se anota en la cabecera de la fase de `tasks.md`, Paso 6), `imputadoPorDia` (horas imputadas por fecha), `bancoHoras` — lista de entradas por tarea/issue con su `kind` (`implementacion`/`revision`), p. ej. `[{ "task":"T-08", "issueKey":"PROJ-123", "horas":1, "origen":"2026-07-15", "kind":"implementacion" }]` — y, por tarea, el **desglose** `worklogImpl` / `worklogRevision` `flow` (**idempotencia de los eventos del Paso 7**: `flow["<issue>|<evento>|<tareas>|<intento>"] = {"fecha": …}`, escrito por `jira-flow.py` al generar un plan con `ops`; si la clave ya está, el mismo evento devuelve `ops: []` + `yaRealizado: true` y no vuelve a comentar — `--force` lo repite) y `reviewComentado` (**último intento de revisión ya publicado** en Jira — no un booleano: el ciclo de eventos del Paso 7 publica un comentario por intento, así que este campo evita repetir el comentario/worklog de un intento ya posteado si `/dev-cycle` se reejecuta; la misma idea vale para los comentarios de `qa`, con el nombre de campo que el orquestador prefiera — el esquema de este fichero no es rígido).

`scripts/jira-flow.py` (Paso 7) **reutiliza el mismo mapeo `T-XX → issueKey`** para resolver el
issue destino de cada evento sin que el llamador tenga que pasar `--issue` a mano (si no lo
encuentra, degrada con un aviso y sigue — nunca bloquea el plan). Cada evento añade además la
etiqueta **`ca-<agente>`** (`ca-implementer` · `ca-reviewer` · `ca-qa`) al issue — sirve para
filtrar en Jira quién comentó qué; es idempotente (añadir una etiqueta ya presente no hace nada).
