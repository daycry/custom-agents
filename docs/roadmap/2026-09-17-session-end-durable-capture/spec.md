---
spec: session-end-durable-capture
estado: implementada
creado: 2026-09-17
actualizado: 2026-09-18
evaluacion: evaluation.md
design: design.md
plan: improvement-plan.md
origen: paquete externo `docs/feature/` (CA-HOOK-001, 2026-09-16), acotado y adaptado al repo real
generacion: {fuente: estimado, tokens_reales: {entrada: 0, salida: 0, cache_creacion: 0, cache_lectura: 0}, eur: null, horas_ia: 0.0, duracion: 0m, ratio_usado: 0}
---

# Captura durable de `SessionEnd` y materialización recuperable del journal

> [Evaluación](evaluation.md) · [Diseño](design.md) · [Plan](improvement-plan.md)

## Problema

Al cerrar Claude Code aparece a veces `SessionEnd hook [bash ".../hooks/session-journal.sh"] failed: Hook cancelled`.
El hook actual hace **todo el trabajo en el teardown**: `git status/diff/show` (hasta 3 × 5 s), lectura del
transcript, lectura del log de prompts y, con `sesion.resumen: true`, una llamada `claude -p` de hasta 25 s;
por eso `hooks.json` declara `timeout: 45`. Si el runtime cancela el hook (Ctrl+C, cierre de terminal,
`SIGKILL`, teardown) **se pierde la entrada entera**, y el mensaje no distingue cancelación real de un falso
positivo con la entrada ya escrita.

Contrato oficial verificado el 2026-09-17 (`code.claude.com/docs/en/hooks`): los hooks de `SessionEnd`
comparten un presupuesto de 1,5 s que **sube hasta el `timeout` declarado, máximo 60 s**; un hook `command`
corre en exec form cuando declara `args`. Nada en la documentación oficial menciona una variable
`CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS` ni una excepción para hooks de plugin: **la solución no es más
timeout, es menos trabajo en el teardown.**

## Objetivo

Separar **captura** (en `SessionEnd`, ultraligera y atómica) de **materialización** (después, recuperable),
de modo que:

- una salida normal deje un *envelope* durable en < 100 ms, sin git, sin IA y sin red;
- una sesión cancelada antes del hook se recupere hasta el **último prompt capturado**, que ya existe: el hook
  `UserPromptSubmit` (`user-prompt-capture.sh`) acumula `.claude/session-prompts-<session_id>.log` por turno —
  **ese log es el checkpoint**; no se añaden hooks `Stop`/`PreCompact` sin medir antes que hacen falta;
- el journal final conserve ruta, formato e idempotencia por `session_id` actuales (`docs/knowledge/journal/`),
  distinguiendo `materializado`, `recuperado_sin_cierre` y `dead_letter` en su frontmatter;
- `/doctor` muestre el estado real (outbox, processing, dead-letter, sesiones huérfanas) y explique cuándo un
  `Hook cancelled` es un aviso del runtime con entrada ya escrita y cuándo es pérdida;
- el mecanismo de cola quede en un módulo compartido (`agent-kits/shared/outbox.py`) que reutilicen los
  exportadores de `knowledge-services` (Kwipu) y `graphiti-memory`: **misma idempotencia, mismo staging
  atómico, mismo dead-letter** en toda la cadena de memoria.

## Alcance

- C-01 **Capturador**: `journal.py capture-end` escribe un envelope JSON (≤ 64 KiB, `schema_version`, `event_id`
  determinista, `session_id`, `reason`, `cwd`, `transcript_path` como referencia no confiable, `captured_at`,
  `plugin_version`, `sequence`) con temporal + rename atómico en `<estado>/journal/outbox/`. No abre el
  transcript, no ejecuta git, no llama a IA, no usa red. `hooks.json` pasa el hook a **exec form** y
  `timeout: 5`.
- C-02 **Materializador**: `journal.py replay` reclama `outbox → processing` (rename atómico), materializa con el
  camino ya existente (`draft`/`render`/`write`, git, log de prompts, resumen IA opt-in), verifica y mueve a
  `done/` o `dead-letter/` (causa estructurada, contador, sin transcript). Idempotente y seguro con dos
  procesos concurrentes (reutiliza `_cerrojo`).
- C-03 **Reconciliación en `SessionStart`**: `session-context.sh` invoca `replay --budget-ms 300 --max 3` antes de
  inyectar contexto; un log de prompts sin envelope y sin sesión viva tras la ventana configurada
  (`sesion.journal.ventanaHuerfanaMin`, default 360) se materializa como `recuperado_sin_cierre`. Nunca bloquea
  el arranque; nunca inyecta una entrada no verificada.
- C-04 **Diagnóstico**: `journal.py status` y sección de `/doctor` (contadores por estado, huérfanas, último
  error de dead-letter, triage del `Hook cancelled`); `journal.py replay`/`recover` como remedio nombrado.
- C-05 **Módulos compartidos**: `agent-kits/shared/outbox.py` (escritura atómica, claim, done, dead-letter,
  manifiesto con hash) y `agent-kits/shared/redact.py` (extraído de `journal.py:redactar`, que pasa a
  importarlo). Ambos con tests y registrados en `copias.json` si viajan como copia.
- C-06 **Pruebas y doc**: casos nuevos en `tests/test_hooks_shell.py` (Ctrl+C simulado = matar antes/después del
  rename, transcript ausente, ruta del plugin con espacios y Unicode, envelope repetido ×5, evento venenoso),
  `scripts/bench-session-end.py` con aserción p95/p99, matriz de garantías por forma de salida en
  `docs/observability.md` (+EN), `GOT-011` con el diagnóstico, CHANGELOG.

## Fuera de alcance

- Hooks `Stop`/`PreCompact` como checkpoint: solo si la medición de C-03 demuestra que el log de prompts no basta
  (se abre iniciativa aparte con la evidencia).
- `CLAUDE_PLUGIN_DATA` como ubicación: no está verificado en Codex/OpenCode; el estado no versionado del plugin
  ya vive en `.claude/` del proyecto (`knowledge-index.sqlite`, `session-prompts-*.log`, `usage-state.json`) y
  ahí sigue (`.claude/journal/`, ignorado por git).
- Ingestión en Kwipu/Graphiti, resumen semántico nuevo, migrar el journal fuera del repo, control plane
  multi-proyecto (`projects.yaml`, tenant, `project_id`): el proyecto consumidor **es** el límite de aislamiento
  (decisión confirmada 2026-09-15).
- Garantizar los últimos milisegundos ante `SIGKILL` antes de cualquier hook.

## Contrato de garantías

| Forma de salida | Garantía |
|---|---|
| `/exit`, `/clear`, `/resume`, Ctrl+D | envelope durable antes de terminar; journal materializado en la siguiente sesión o a demanda |
| Ctrl+C / terminal cerrada / proceso muerto antes del hook | recuperación hasta el último prompt capturado; entrada marcada `recuperado_sin_cierre` |
| Ctrl+C con envelope ya publicado | igual que salida normal; el aviso del runtime es cosmético y `/doctor` lo dice |
| Disco lleno / permisos | error verificable en `status`, nunca éxito falso; el resto de la cola sigue |
| Envelope corrupto | `dead-letter/` con causa; no bloquea a los demás |

## Criterios de aceptación

- [ ] CA-01 - `SessionEnd` no ejecuta git, IA ni red: el test inyecta un `git` falso en `PATH` y un `claude` falso y comprueba que ninguno se invoca durante la captura.
- [ ] CA-02 - Captura p95 ≤ 100 ms y p99 ≤ 300 ms en CI (`bench-session-end.py --assert-p95-ms 100 --assert-p99-ms 300`, 30 iteraciones).
- [ ] CA-03 - El mismo evento capturado cinco veces produce un único envelope lógico y una única entrada de journal.
- [ ] CA-04 - Matar el capturador antes o después del rename nunca deja un fichero parcialmente válido en `outbox/`.
- [ ] CA-05 - Con transcript inexistente, la materialización usa el log de prompts o registra la carencia; nunca inventa contenido.
- [ ] CA-06 - Un envelope venenoso acaba en `dead-letter/` con causa y los demás se procesan.
- [ ] CA-07 - Una sesión con log de prompts y sin envelope, pasada la ventana, se materializa como `recuperado_sin_cierre`; una sesión concurrente viva no se confunde con huérfana.
- [ ] CA-08 - `SessionStart` termina dentro del presupuesto con 0, 10 y 100 pendientes y nunca inyecta una entrada sin materializar.
- [ ] CA-09 - `hooks.json` usa exec form (`command: bash`, `args`) y la suite de shell pasa con `CLAUDE_PLUGIN_ROOT` con espacios y Unicode.
- [ ] CA-10 - `/doctor` distingue «aviso del runtime con entrada escrita» de «pérdida» y nombra el comando de remedio.
- [ ] CA-11 - `outbox.py` y `redact.py` tienen tests propios; `journal.py` importa `redactar` de `redact.py` (una sola fuente) y el mutante que la duplica es detectado por `copias.json`/linter.
- [ ] CA-12 - Uninstall/upgrade del plugin no borra `.claude/journal/`; solo `journal.py purge --confirm` lo hace.

## Decisiones confirmadas (usuario, 2026-09-17)

1. Se extrae del paquete externo `docs/feature/` (CA-HOOK-001) lo que aporta y se **acota** (15 tareas / 26-40 h → 8 tareas / ~14 h): el checkpoint por turno ya existe, la idempotencia por `session_id` ya existe, la escritura atómica y los cerrojos ya existen en `journal.py`.
2. El resto del paquete (CA-MEM-001…005: control plane, gateway Graphiti, router, interop) **no se adopta como iniciativas**; sus principios válidos entran en `ADR-018` y sus ideas útiles (shadow mode, rebuild, revocación, proveedor configurable) en la enmienda de `graphiti-memory`.
3. `outbox.py` nace aquí y lo consumen `knowledge-services` (exportador Kwipu) y `graphiti-memory` (sincronizador): esta iniciativa va **antes** de la Fase 3 de `knowledge-services`.
4. `redact.py` se extrae aquí (única iniciativa que ya refactoriza `journal.py`) y deja de ser tarea de `training-data-services`.
