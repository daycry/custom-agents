---
design: session-end-durable-capture
estado: aprobado
opcion_elegida: O1
spec: spec.md
evaluation: evaluation.md
plan: improvement-plan.md
---

# Diseño - captura ligera + materialización recuperable

| Opción | Descripción | Decisión |
|---|---|---|
| O1 | `SessionEnd` solo escribe un envelope atómico en una **outbox** local; la materialización (git, prompts, IA opt-in) corre en `SessionStart` con presupuesto o a demanda (`journal.py replay`). El log de prompts por turno que ya existe hace de checkpoint. Cola en `agent-kits/shared/outbox.py`, compartida con los exportadores de memoria. | **Elegida.** |
| O2 | Subir el `timeout` y seguir haciendo el trabajo en el teardown. | Descartada: el presupuesto ya sube hasta 45 s y el fallo no es de tiempo sino de cancelación; una cancelación pierde todo. |
| O3 | Paquete externo CA-HOOK-001 tal cual: máquina de 8 estados, hooks `Stop`/`PreCompact` nuevos, `CLAUDE_PLUGIN_DATA`, 15 tareas. | Descartada: duplica lo que `journal.py` y `user-prompt-capture.sh` ya hacen; `CLAUDE_PLUGIN_DATA` no está verificado en Codex/OpenCode; 3× el coste para la misma garantía. |
| O4 | Hook `async: true`. | Descartada: la doc oficial no lo ofrece como garantía de persistencia en el teardown y se pierde la observabilidad. |

## Flujo

```text
UserPromptSubmit ─► user-prompt-capture.sh ─► .claude/session-prompts-<sid>.log   (checkpoint, YA EXISTE)

SessionEnd ─► session-journal.sh (exec form, timeout 5)
              └► journal.py capture-end  ─► .claude/journal/outbox/<event_id>.json   (tmp + rename, < 100 ms)

SessionStart ─► session-context.sh
              └► journal.py replay --budget-ms 300 --max 3
                    claim  outbox → processing (rename atómico, cerrojo)
                    materializar = camino actual (draft → render → write; git; prompts; IA opt-in)
                    verificar  → done/ (manifiesto con hash)  |  dead-letter/<event_id>.json {causa, intentos}
                    huérfanas: log de prompts sin envelope y sin sesión viva > ventana → recuperado_sin_cierre

A demanda ─► journal.py status | replay | recover <sid> | purge --confirm
/doctor   ─► sección «Journal»: outbox/processing/done/dead-letter, huérfanas, triage «Hook cancelled»
```

## Envelope (`schema_version: 1`)

`event_id = sha256(session_id · reason · schema_version · sha256(contenido del log de prompts, o "" si no
existe))[:16]` (revisión intento 2, gap 28: `sequence`, nº de líneas del log, NO es monótono cuando el log
rota — podía volver a un valor ya usado y colisionar con una entrada en `done/`; el HASH del contenido no).
Campos: `session_id`, `hook_event_name`, `reason`, `cwd`, `transcript_path` (referencia, se valida antes de
usar), `captured_at`, `plugin_version`, `sequence` (ahora puramente INFORMATIVO: líneas del log en el
momento del cierre). Sin texto de conversación. Se aceptan esquemas N y N-1 en el replay durante una versión.

**Validación completa en `replay` (gap 27/37/44 de la revisión intento 2).** `_validar_envelope` ya no mira
solo `session_id`/`schema_version`: exige `reason` ∈ `^[a-z_]{1,40}$`, `captured_at` ∈
`^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$`, `cwd`/`transcript_path` sin `\n` y ≤ `ENVELOPE_STR_MAX`, `sequence`
entero ≥ 0 y `hook_event_name == "SessionEnd"`; lo que no cumpla va a `dead-letter/` con causa — un
`captured_at` tipo `"../../../../tmp/PWN"` ya no llega a formar parte de un nombre de fichero ni un `reason`
con `\n` inyecta claves YAML en el frontmatter (todos los escalares de `render()` pasan por `_yaml_str`,
incluido `reason`). La fecha de la entrada se obtiene parseando `captured_at` (UTC) y convirtiéndolo a hora
LOCAL (`_fecha_local_de_captured_at`, gap 44 — coherente con `hoy()`). `write()` añade una defensa en
profundidad: si `os.path.realpath(destino)` cayera fuera de `os.path.realpath(journal_dir(root))`, lanza en
vez de escribir.

**`transcript_path` (gap 38).** Además del `basename == <session_id>.jsonl` (gap 15, intento 1),
`_transcript_seguro` exige que no sea un symlink y que, tras `os.path.realpath`, caiga bajo
`$CLAUDE_CONFIG_DIR/projects` (o `~/.claude/projects` sin la variable): el basename por sí solo compara dos
campos del MISMO envelope no confiable y no bastaba.

## Estados (frontmatter del journal, clave `cierre:`)

`materializado` (envelope + verificación) · `recuperado_sin_cierre` (sin envelope; desde el log de prompts) ·
`dead_letter` (solo en la cola, con causa). No hay `FINAL_CAPTURED` visible al usuario: el envelope es un
detalle de la cola, no un estado del journal. Un envelope QUE SÍ LLEGÓ a `dead-letter/` no bloquea la
recuperación: el log de prompts sigue siendo la fuente para `recover` (gap 68 de la revisión tramo 2 —
antes `dead-letter/` contaba como «ya capturada» y esa sesión se perdía sin vía de recuperación).

**`recover` bajo el mismo cerrojo/presupuesto que `replay` (gaps 65/66/69 de la revisión tramo 2).**
Hasta esta corrección, `recover` corría suelto en `SessionStart` sin `--budget-ms`/`--max` propios y SIN
cerrojo: cientos de huérfanas podían tardar segundos en un arranque (gap 65, cada `draft` corre git con el
`GIT_TIMEOUT` de 5s por defecto, no el acotado bajo presupuesto) y dos `SessionStart` concurrentes podían
duplicar la misma entrada (gap 66, sin exclusión mutua). `journal.py replay --con-recover` materializa la
outbox y recupera huérfanas EN LA MISMA pasada, bajo el MISMO `_cerrojo_presupuestado` — `recover` recibe
lo que quede del presupuesto/tope tras drenar la outbox — en vez de un cerrojo propio duplicado; `recover`
a demanda (`journal.py recover`) toma el mismo fichero de cerrojo (`<dir>/.replay`) para serializarse
también con `replay`. La entrada recuperada usa el mtime del LOG de prompts (UTC, convertido a ISO) como
`captured_at` — no `hoy()` — para que la fecha del frontmatter sea la del último turno real, no la del
momento en que corrió `recover` (gap 67); sus campos derivados de `git` se marcan `derivados_en: replay`
(la pasada que los calculó), no `recover`.

**Ventana huérfana: 360 → 1440 min / 24h (gaps 65/69 de la revisión tramo 2) — limitación aceptada por
diseño.** Con 360 min, una sesión viva pero OCIOSA (portátil en suspensión, fin de semana, `SessionStart`
de otra sesión corriendo `--con-recover` sin conocer el `session_id` de la primera) podía recuperarse ANTES
de tiempo como `recuperado_sin_cierre`; solo la guarda de «sesión que arranca» (`current_session_id`)
protege a la sesión que está iniciándose, no a OTRAS sesiones vivas y ociosas del mismo proyecto. Esto NO
se resuelve del todo con una ventana más larga —solo se hace menos frecuente—: la limitación se acepta
porque **se autocorrige sola al cerrar de verdad** (`escribir_sesion`/`write` son idempotentes por
`session_id`: la entrada `materializado` de un cierre real SOBRESCRIBE la `recuperado_sin_cierre` anterior,
así que el peor caso es una entrada temporalmente optimista, nunca datos perdidos ni duplicados). Con
`current_session_id == ""` (el payload de `SessionStart` llegó sin `session_id`) `recover` NO corre en
absoluto (con aviso) en vez de recuperar sin esa guarda (gap 79); tampoco corre con `source: compact` (la
compactación no cambia el journal).

**Limitación aceptada por diseño (revisión intento 1, gap 8):** la entrada usa la FECHA DEL CIERRE
(`captured_at` del envelope, nombre de fichero y frontmatter), pero los campos derivados de `git`
(`ficheros_tocados`, `tareas_cambiadas`) se calculan EN EL MOMENTO DEL REPLAY, no en el del cierre —
CA-01 prohíbe ejecutar git en el teardown, así que no hay otra fuente. El frontmatter lo marca con
`derivados_en: replay` para que quede explícito que ese fragmento describe el estado del repo al
materializar, no al cerrar la sesión.

## `agent-kits/shared/outbox.py` (contrato)

`escribir(dir, clave, payload)` (tmp + fsync si viable + rename, idempotente por clave) · `reclamar(dir) -> item`
(rename a `processing/`, cerrojo) · `completar(item, manifiesto)` · `dead_letter(item, causa, intentos=None)` ·
`reencolar_o_dead_letter(item, causa, backoff=True) -> "reencolado"|"dead_letter"|"error"` ·
`reintentar_dead_letter(dir) -> int` · `estado(dir) -> dict` · `purgar(dir, confirmar=True)`. Sin
dependencias; stdlib. Lo usan `journal.py` (esta iniciativa), `kwipu-export.py` (knowledge-services T-07) y
`graphiti-sync.py` (graphiti-memory T-05).

**TTL sobre la reclamación, no sobre la creación (gap 25 Critical, revisión intento 2; reclamación EN DOS
PASOS, gap 50 de la revisión intento 3).** `reclamar()` mueve `outbox/<clave>.json` a un nombre TEMPORAL
`processing/<clave>.json.claiming`, refresca su mtime con `os.utime`, y SOLO ENTONCES lo renombra al nombre
final `<clave>.json` — visible como reclamado nunca antes de que el mtime esté al día. El TTL de huérfanos se
mide desde ESE instante (sin esto, un envelope que esperó horas en `outbox/` ya superaba la TTL nada más
reclamarlo, y un segundo `reclamar()` lo entregaba también a otro trabajador). Si `os.utime` falla (SMB/FUSE,
FS sin soporte), el item vuelve a `outbox/` tal cual (nunca se reclama) y `estado()["reclamacion"]` pasa a
`"degradada"`; como respaldo adicional, la reclamación con éxito también escribe un sidecar
`<clave>.json.claimed_at` que `_reclamar_huerfanos` lee ANTES que el mtime.

**Backoff tras un fallo TRANSITORIO (gap 26 Critical; tope y `--reintentar-ahora`, gap 51 de la revisión
intento 3).** `reencolar_o_dead_letter(..., backoff=True)` escribe en el sidecar `.intentos` un JSON
`{"intentos", "no_antes_de"}` con `no_antes_de = min(ahora + BACKOFF_S(60) × intentos, ahora +
BACKOFF_MAX_S(3600))` (creciente pero topado); `reclamar()` salta los candidatos de `outbox/` con
`no_antes_de` válido en el futuro — un valor no finito o que supere el tope al LEER se trata como 0
(reclamable), para que un salto de reloj o un sidecar corrupto no deje un item inalcanzable para siempre. La
recuperación de huérfanos de `processing/` (`backoff=False`: un worker murió, no es un fallo del código)
sigue siendo inmediata. Un fallo permanente necesita entonces 3 PASADAS de `replay` separadas por el backoff
para llegar a `dead-letter/`, nunca una sola pasada instantánea. `journal.py replay
--reintentar-dead-letter` (remedio nombrado que `/doctor`, T-06, expondrá) devuelve todo `dead-letter/` a
`outbox/` con el contador a 0; `--reintentar-ahora` hace lo equivalente pero sobre `outbox/` (pone a 0 el
`no_antes_de` de todo lo que esté en backoff). `estado()`/`replay` exponen `en_backoff` (cuántos items
esperan) y un aviso con la fecha ISO del más próximo, en vez de un `restantes` mudo.

**Manifiesto ANTES de mover a `done/` (gap 59 de la revisión intento 3).** `completar()` escribe
`<clave>.json.manifest.json` en `processing/` (junto al envelope) y solo TRAS eso hace `os.replace` a
`done/`. Si escribir el manifiesto falla (ENOSPC, permisos), la excepción se propaga con el item TODAVÍA en
`processing/`: el llamador lo reencola/dead-letter con normalidad, y `replay` deja un aviso explícito
(«entrada escrita pero manifiesto pendiente…») cuando `escribir_sesion` ya materializó la entrada pero
`completar` falló después — nunca queda un envelope varado en `done/` sin `completado_en` que
`purgar_antiguos` no pueda purgar nunca.

**Marcador de la cola (gap 34; contenido cerrado, gap 62 de la revisión intento 3).** `_QUEUE_MARKER`
(`.custom-agents-journal`) se escribe al crear el directorio de la cola; `sesion.journal.dir` solo se acepta
si el candidato está CONTENIDO en la raíz tras `realpath` (rechaza symlinks de escape y rutas de unidad de
Windows vía `ntpath.splitdrive`) Y además está vacío, o lleva el marcador Y no tiene NINGÚN fichero fuera del
conjunto conocido de la cola (`outbox/`, `processing/`, `done/`, `dead-letter/`, `.gitignore`,
`.replay.lock`, los sentinelas de degradación y el propio marcador) — el marcador SOLO ya no basta: un
`docs/.custom-agents-journal` colado (versionado por error) ya no basta para que `docs/` entero —con su
`README.md` y el resto de documentación real— se trate como la cola. El `.gitignore` que se siembra dentro
lleva SOLO `*` (sin `!.gitignore`, gap 61 de la revisión intento 3): con la excepción, el propio `.gitignore`
de la cola quedaba sin ignorarse a sí mismo (visible en `git status -uall`).

## Configuración (`.claude/dev.json` → `sesion.journal`)

Hoy `sesion.journal: false` desactiva. Pasa a admitir también objeto: `{"activo": true, "dir": ".claude/journal",
"ventanaHuerfanaMin": 1440, "replay": {"budgetMs": 300, "max": 3}}`; el booleano sigue valiendo (compatibilidad).
`/setup` no añade paso: son valores por defecto sensatos; `/doctor` los muestra. `budgetMs`/`max` se acotan a
`[0, 5000]`/`[0, 50]` (gap 75 de la revisión tramo 2): fuera de rango, `session-context.sh` usa el default y
avisa en la línea de Journal — un `dev.json` clonado con un valor desmesurado ya no hace trabajar al hook
hasta el timeout del runtime que lo invoque.

## Multi-runtime

El capturador es un script Python que lee stdin; el adaptador de Codex/OpenCode (`hooks/opencode-plugin.js`,
`interop/`) invoca `journal.py capture-end` con el mismo JSON. La ubicación es siempre `<proyecto>/.claude/journal/`
(en git-ignore), como el resto del estado no versionado del plugin.

**Deuda aceptada por diseño (gap 47, revisión intento 2).** Sin `CLAUDE_PROJECT_DIR`, `session-journal.sh`
cae en la cascada `--root` > `CLAUDE_PROJECT_DIR` > `cwd` del payload > `.` de `cmd_capture_end` — simétrico
con `user-prompt-capture.sh`, que ya acepta el mismo riesgo. Un `cwd` de payload no controlado por el
usuario podría, en teoría, elegir dónde se crean directorios y se siembra `.gitignore`; está acotado por dos
guardas (`os.path.isdir(root)` antes de usarlo, `proyecto_con_plugin(root)` antes de escribir nada — rastro
real del plugin, no cualquier carpeta) y exigiría que el propio runtime mintiera sobre el `cwd` de la sesión:
fuera del modelo de amenaza («el proyecto consumidor es el límite de aislamiento», decisión confirmada
2026-09-15 en `spec.md`). No se corrige en código; se documenta aquí.
