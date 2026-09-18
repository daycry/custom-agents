---
id: GOT-011
tipo: gotcha
area: journal de sesión / captura de SessionEnd
estado: propuesta (hallazgo del usuario, 2026-09-17; corregido en `session-end-durable-capture`)
fuente: docs/roadmap/2026-09-17-session-end-durable-capture/spec.md (Problema); tasks.md (T-01…T-08)
---

## «SessionEnd hook … failed: Hook cancelled» era el síntoma de hacer TODO el trabajo en el teardown, no de un timeout corto

- **Síntoma:** al cerrar Claude Code aparecía a veces `SessionEnd hook [bash ".../hooks/session-journal.sh"]
  failed: Hook cancelled`. El hook viejo hacía `git status/diff/show` (hasta 3 × 5 s), leía el transcript, leía
  el log de prompts y, con `sesion.resumen: true`, llamaba a `claude -p` (hasta 25 s) — todo ello DENTRO del
  teardown de la sesión, con `hooks.json` declarando `timeout: 45` para que le cupiera. Si el runtime cancelaba
  el hook (Ctrl+C, terminal cerrada, `SIGKILL`, teardown normal con prisa) se perdía la entrada ENTERA, y el
  mensaje no distinguía una cancelación real (sin escribir nada) de un falso positivo con la entrada ya escrita
  a tiempo.
- **Causa raíz:** el contrato oficial de `SessionEnd` (verificado 2026-09-17, `code.claude.com/docs/en/hooks`)
  reparte 1,5 s de presupuesto entre los hooks de ese evento, ampliable hasta el `timeout` declarado (máx. 60 s
  oficial) — pero **nada garantiza que el hook llegue a correr entero**: el teardown de la sesión (Claude Code
  cerrando worktrees y directorios de trabajo) puede ganarle la carrera al hook en cualquier punto de su
  ejecución, y cuanto más trabajo hace el hook (git × 3, IA de hasta 25 s), más tiempo pasa expuesto a esa
  carrera. Subir el `timeout` no arregla nada: **el fallo no es de tiempo, es de que hay demasiado que perder
  si te cancelan a mitad**. La hipótesis descartada explícitamente (`design.md`, opción O2): «subir el
  `timeout` y seguir haciendo el trabajo en el teardown» — no ataca la causa.
- **Qué hacer en su lugar:** separar CAPTURA (en `SessionEnd`, ultraligera y atómica) de MATERIALIZACIÓN
  (después, recuperable). `journal.py capture-end` escribe SOLO un *envelope* atómico (≤ 64 KiB, `event_id`
  determinista, sin git/IA/red — CA-01) en una **outbox** local (`agent-kits/shared/outbox.py`, tmp + rename),
  en < 100 ms (CA-02, medido con `scripts/bench-session-end.py`); `hooks.json` pasa a exec form con
  `timeout: 5`, no 45. La materialización real (`journal.py replay`: git, log de prompts, IA opt-in) corre
  DESPUÉS, en `SessionStart` con presupuesto (`--budget-ms 300 --max 3`, T-05) o a demanda — nunca en el
  teardown. Una sesión cancelada ANTES de que el hook llegue a correr se recupera igual, hasta el último
  turno capturado: el log de prompts que `UserPromptSubmit` ya acumulaba por turno (`.claude/session-prompts-
  <sid>.log`) es el checkpoint, y `journal.py recover` lo materializa como `cierre: recuperado_sin_cierre`
  pasada una ventana configurable sin sesión viva (CA-07).
- **Diagnóstico (triage del «Hook cancelled»):** `journal.py status [--json]` y la sección «Journal» de
  `/doctor` distinguen las dos lecturas del mismo mensaje (CA-10): si hay un envelope o una entrada de esa
  sesión (en `outbox/`, `processing/` o ya materializada), es el **aviso cosmético del runtime, SIN pérdida**
  — la materializa el próximo `SessionStart` o `journal.py replay`. Si NO hay ni envelope ni huérfana conocida,
  el diagnóstico sugiere `journal.py recover` para confirmar que no hay pérdida real antes de asumir lo peor.
  Un envelope corrupto o con un esquema no soportado va a `dead-letter/` con causa (`journal.py replay
  --reintentar-dead-letter` como remedio) y nunca bloquea al resto de la cola.
- **Evidencia:** `docs/roadmap/2026-09-17-session-end-durable-capture/spec.md` (§Problema, contrato oficial
  verificado 2026-09-17); `agent-kits/shared/journal.py::capture_end/replay/recover/status`;
  `agent-kits/shared/outbox.py` (cola atómica con claim/dead-letter/backoff); `hooks/session-journal.sh`
  (`timeout: 5`, exec form) y `hooks/session-context.sh` (reconciliación presupuestada en `SessionStart`);
  `agent-kits/shared/doctor.py::_bloque_journal_lineas` (triage); `scripts/bench-session-end.py` (CA-02:
  p95/p99 medidos, `ci.yml.MANUAL-COPY`); tabla de garantías por forma de salida en `docs/observability.md`
  (+EN).
