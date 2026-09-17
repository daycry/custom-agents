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

`event_id = sha256(session_id · reason · sequence · schema_version)[:16]`; campos: `session_id`, `hook_event_name`,
`reason`, `cwd`, `transcript_path` (referencia, se valida antes de usar), `captured_at`, `plugin_version`,
`sequence`. Sin texto de conversación. Se aceptan esquemas N y N-1 en el replay durante una versión.

## Estados (frontmatter del journal, clave `cierre:`)

`materializado` (envelope + verificación) · `recuperado_sin_cierre` (sin envelope; desde el log de prompts) ·
`dead_letter` (solo en la cola, con causa). No hay `FINAL_CAPTURED` visible al usuario: el envelope es un
detalle de la cola, no un estado del journal.

**Limitación aceptada por diseño (revisión intento 1, gap 8):** la entrada usa la FECHA DEL CIERRE
(`captured_at` del envelope, nombre de fichero y frontmatter), pero los campos derivados de `git`
(`ficheros_tocados`, `tareas_cambiadas`) se calculan EN EL MOMENTO DEL REPLAY, no en el del cierre —
CA-01 prohíbe ejecutar git en el teardown, así que no hay otra fuente. El frontmatter lo marca con
`derivados_en: replay` para que quede explícito que ese fragmento describe el estado del repo al
materializar, no al cerrar la sesión.

## `agent-kits/shared/outbox.py` (contrato)

`escribir(dir, clave, payload)` (tmp + fsync si viable + rename, idempotente por clave) · `reclamar(dir) -> item`
(rename a `processing/`, cerrojo) · `completar(item, manifiesto)` · `dead_letter(item, causa)` · `estado(dir) -> dict`
· `purgar(dir, confirmar=True)`. Sin dependencias; stdlib. Lo usan `journal.py` (esta iniciativa),
`kwipu-export.py` (knowledge-services T-07) y `graphiti-sync.py` (graphiti-memory T-05).

## Configuración (`.claude/dev.json` → `sesion.journal`)

Hoy `sesion.journal: false` desactiva. Pasa a admitir también objeto: `{"activo": true, "dir": ".claude/journal",
"ventanaHuerfanaMin": 360, "replay": {"budgetMs": 300, "max": 3}}`; el booleano sigue valiendo (compatibilidad).
`/setup` no añade paso: son valores por defecto sensatos; `/doctor` los muestra.

## Multi-runtime

El capturador es un script Python que lee stdin; el adaptador de Codex/OpenCode (`hooks/opencode-plugin.js`,
`interop/`) invoca `journal.py capture-end` con el mismo JSON. La ubicación es siempre `<proyecto>/.claude/journal/`
(en git-ignore), como el resto del estado no versionado del plugin.
