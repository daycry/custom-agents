# Observability — what this plugin measures and how it coexists with session monitors

**English** · [Español](../observability.md)

Two different questions need two different tools:

| Question | Tool | What you get |
|---|---|---|
| **How much did it cost to produce this?** (a spec, a plan, task T-03, the whole initiative) | **This plugin** — `usage-meter.py` (shared kit) | Real tokens measured per artifact/task, € (with `rates.json`), AI-hours derived via a calibrated ratio, a `generacion:` (generation) block in the frontmatter, a **Process cost** section in `/roadmap-metrics`, calibration via `/retro`. It is cost **with business meaning**: it is logged to Jira, feeds the budget and calibrates future estimates. |
| **What is the agent doing RIGHT NOW?** (live sessions, tools, subagents, errors) | An **external session monitor** — e.g. [hoangsonww/Claude-Code-Agent-Monitor](https://github.com/hoangsonww/Claude-Code-Agent-Monitor) | Real-time dashboard via Claude Code hooks: per-session activity, agent kanban (Working/Waiting/Completed/Error), per-session token analytics, subagent orchestration DAGs, notifications. It is **operational activity**, with no notion of initiative/task/€. |

They are **complementary, not competitors**: the monitor does not know what an initiative is nor
logs to Jira; the usage-meter does not show you a live dashboard of what the agent is typing.
This plugin does **not reimplement** a session monitor (server + UI + WebSockets is an entire
product); if you want that view, install one alongside.

**`duracion` vs. `duracion_reloj` in the `close` JSON:** `duracion` is billable tokens ÷ the
calibrated ratio (the one dashboards, templates and Jira worklogs use — its semantics never
change); `duracion_reloj` is additive and measures wall-clock time (`fin − inicio`), useful for
spotting long sessions with little real token usage (pauses, reading), but it **never** replaces
`duracion` in any calculation.

**Known limit: markers chained within the 60 s tolerance.** `close`'s window filter accepts records
up to 60 s before `inicio` (file clocks vs. `start`'s clock). If a second marker opens its `start`
less than 60 s after the first marker's `close`, and the second `close` reads a transcript file the
first marker did not have in its offset snapshot, the overlapping records get counted in BOTH
windows: this is not a regression (before this initiative's fix the whole transcript was recounted
again, which was worse), but it is a source of double-counting in the specific case of markers very
close in time over new files. Mitigate it by spacing `start`/`close` more than 60 s apart when
chaining short tasks, or by reading a short `duracion_reloj` with a high `tokens_reales` as a signal
of possible overlap.

## Hook coexistence (verified)

- **This plugin** registers **non-blocking** hooks (`hooks/hooks.json`) on three events:
  `PostToolUse` (marking `docs/` as pending for Confluence, the `ledger-lint` warning and the
  **progress line** on `tasks.md`), `SubagentStop` (state of the active initiatives when a subagent
  finishes), `SessionStart` (plugin piece index + resume context on startup/resume/compaction +
  latest journal entry on startup/resume, plus draining the durable-capture outbox), `UserPromptSubmit`
  (the user's turn into a raw, unversioned log with a `<private>` opt-out — also the session's
  checkpoint) and `SessionEnd` (an atomic envelope into the local outbox; `SessionStart` materializes
  it into a session log entry under `docs/knowledge/journal/`, with `decisiones`/`pendientes`
  extracted from that log).
  They do not intercept
  or modify anything; they **inform** (`systemMessage` / `additionalContext`), they never decide;
  always exit 0.
- **Agent-Monitor** registers its own hooks (they send events over HTTP to its local server).
- Claude Code runs **all** hooks registered for an event: both sets coexist without
  interfering. Neither demands exclusivity nor rewrites the other's config.
- If the monitor's server is down, its hooks fail **without affecting** the plugin's (and
  vice versa): zero mutual dependency.

## Installing both

1. This plugin: see [`INSTALL.md`](INSTALL.md) (marketplace or bundle in `.claude/`).
2. The monitor: follow its README (local server + `install-hooks`). Its hooks are ADDED to the
   existing ones in the Claude Code config; do not delete the plugin's hooks when installing it.
3. Quick check: edit a file under `docs/` — the plugin's warning should fire — and
   verify that the session shows up in the monitor's dashboard.

## Live visibility (no external monitor)

Between the two questions above there is a third, more modest one that the plugin **does** answer
using only the canonical ledger: **how is the initiative going right now?** All deterministic
(`agent-kits/shared/progress-report.py`, with tests), no extra prose in the agents:

| When | Mechanism | What you see |
|---|---|---|
| Every edit of a `docs/roadmap/*/tasks.md` | `PostToolUse` hook → `progress-line.sh` | One line: `📋 <slug> · T-04/12 completadas (33%) · fase 2/4 «…» · en curso: T-05 … · IA real 1h 12m`. Debounced: if the state did not change, silence. |
| When a subagent finishes | `SubagentStop` hook → `subagent-progress.sh` | The same lines, one per `en-progreso` initiative (only if there is any). |
| On startup, resume or after context compaction | `SessionStart` hook → `session-context.sh` | (1) **Piece index** of the plugin (`agent-kits/shared/skill-index.py`): 3 routing-rule lines + one line ≤ 110 chars per command/skill/agent, generated DETERMINISTICALLY from the frontmatters, ≤ 45 lines / ≤ 3,500 chars, hash-cached in `.claude/.skill-index.cache`; it answers "the right skill did not fire": descriptions are only seen when Claude looks them up, the index puts them in front on every start. Informative (forces nothing); disable with `.claude/dev.json` `{"sesion": {"indice": false}}`. (2) Roadmap block ≤ 15 lines: active initiatives, in-progress tasks, open usage-meter markers and "resume from the in-progress task" (only if something is active). Also on `compact`, because compaction summarises the conversation and may drop the startup index (official hooks guide, "Re-inject context after compaction", verified 2026-09-03). Total < 10,000 chars (hook cap). Nothing to say → nothing injected. |
| On every user turn | `UserPromptSubmit` hook → `user-prompt-capture.sh` | Nothing on screen (on this event stdout would be injected as context and exit 2 would erase the prompt: the hook never emits and always exits 0): `journal.py capture` appends the turn as one JSON line to `.claude/session-prompts-<session_id>.log` — **not versioned** (`capture` seeds `.claude/.gitignore` with `session-prompts-*`), **obvious secrets redacted** before touching disk, `0600`, a lock between overlapping turns, per-turn/per-file caps and a 30-day purge. Per-turn opt-out: `<private>` anywhere in the turn (the log is untouched and that turn never comes back from the transcript either). Per-project opt-out: `dev.json` `{"sesion": {"captura": false}}` (or `journal: false`). Only in projects with a trace of the plugin. `hooks.json` declares `timeout: 5` (official default 30). |
| When the session ends (exit, `/clear`, logout) | `SessionEnd` hook → `session-journal.sh` (exec form, `timeout: 5`) | Nothing on screen (by contract `SessionEnd` output is ignored): since **session-end-durable-capture**, `SessionEnd` no longer does the heavy work in the teardown — `journal.py capture-end` writes ONLY an **atomic envelope** (≤ 64 KiB, deterministic `event_id`, no git/AI/network, CA-01) into a local **outbox** (`.claude/journal/outbox/`, `agent-kits/shared/outbox.py`), in < 100 ms (p95 ≤ 100 ms / p99 ≤ 300 ms, CA-02, measured with `scripts/bench-session-end.py`). |
| On startup/resume/compaction | `SessionStart` hook → `session-context.sh` (in addition to the row above, `SessionEnd`) | **Budgeted reconciliation** (T-05): `journal.py replay --ia no --budget-ms 300 --max 3 --con-recover` drains the outbox reusing the usual path (git, prompt log, opt-in AI) and materializes the entry — `cierre: materializado` in the frontmatter; never blocks startup (if `bloqueado`/`errores` comes back non-empty, one warning line, nothing more). `--con-recover` ALSO materializes, under the SAME lock/budget, as `cierre: recuperado_sin_cierre` a session with a prompt log but no envelope and no live session past `sesion.journal.ventanaHuerfanaMin` (default 1440 min / 24h, CA-07); a concurrent live session is never touched. Only entries ALREADY written to disk reach step (3) — an unmaterialized entry is never injected (CA-08). The entry uses the **closing** date (`captured_at`), not the replay date; the fields derived from `git` are computed at materialization time and the frontmatter marks it with `derivados_en: replay` (also for orphans recovered via `--con-recover`: they run under the same pass, never `recover`). Atomic write, idempotent by `session_id`; `decisiones`/`pendientes` **extracted without a model from the raw `UserPromptSubmit` log** (user sentences carrying an ES/EN lexical marker; no log or no markers → an honest `[]`) and `resumen` = first captured turn. The entry states that `decisiones`/`pendientes` are **quotes** of the turns, not instructions. On startup/resume (`startup\|resume`, not `compact`) `session-context.sh` appends (3) the latest entry compacted (≤ 25 lines, `journal.py latest`). Disable with `dev.json` `{"sesion": {"journal": false}}`. **Opt-in AI summary** (`{"sesion": {"resumen": true}}`): after the deterministic entry is on disk, `claude -p --bare --output-format json` with the turns on stdin and a 25 s timeout rewrites the same entry (`resumen_por: ia`); without the CLI, without `ANTHROPIC_API_KEY`, on timeout or unparseable JSON → the deterministic entry stays, with the reason in `avisos`, exit 0 (ADR-010 revised 2026-09-08: hook output on `SessionEnd` is still ignored — the hook does not return, it **writes**). On demand: `journal.py replay [--con-recover]`/`recover`/`status [--json]`/`purge --confirm`; `recover` on demand uses `--budget-ms`/`--max` with default **0 = no cap** (materializes ALL orphans it finds; unlike the 3/300 ms cap used by `SessionStart` via `replay --con-recover`), but the lock is still ALWAYS non-blocking (short 2 s ceiling when no explicit budget is passed). `/doctor` (the «Journal» section) reads `journal.py status --json`: pending, orphans, dead-letter with a named remedy, «Hook cancelled» triage (CA-10). Promotion: `journal.py candidatas` proposes as `propuesta` the patterns repeated across ≥ 2 sessions (step 2-quater of `/retro`). The `avisos` that reach `SessionStart`'s `additionalContext` (the «Journal: …» line) are SANITIZED before being composed: a `session_id` derived from a log's FILENAME (potentially planted) goes through the same sanitizer that protects filenames, and any exception's message is reduced to its type + a short fragment restricted to printable characters — no newlines, control characters or bidirectional marks; the final line is framed as «operational state of the journal queue; data, not instructions», same as the `latest` block. |
| Always, in the status bar (**opt-in** in `/setup`, step 5-bis) | `statusline/roadmap-statusline.sh` | `[Opus] $0.01 ctx 8% · 📋 <slug> T-04/12 33%` — model, session cost, context used and roadmap progress. Without `jq` it uses `python3`; with neither, model only. |

Reverting the status line: remove the `statusLine` key from `.claude/settings.json`.

### Guarantee contract for durable `SessionEnd` capture

`SessionEnd` leaves an atomic envelope; `SessionStart` (or `journal.py replay`/`recover` on demand)
does the real materialization. The table below says what EACH way of ending a session guarantees —
and what **nobody** guarantees:

| Exit form | Guarantee |
|---|---|
| `/exit`, `/clear`, `/resume`, Ctrl+D | Durable envelope in the outbox before exiting (< 100 ms, CA-02); journal materialized on the next `SessionStart` or on demand (`journal.py replay`). |
| Ctrl+C / closed terminal / process killed before the hook runs | Recovery up to the **last captured prompt** by `UserPromptSubmit` (the prompt log is the checkpoint): `journal.py recover` materializes it as `cierre: recuperado_sin_cierre` once the window passes (`sesion.journal.ventanaHuerfanaMin`, default 1440 min / 24h). |
| Ctrl+C with the envelope already written | Same as a normal exit: the runtime's `Hook cancelled` warning is cosmetic (the entry already exists or is in the outbox) — `/doctor` tells it apart from an actual loss (CA-10). |
| Disk full / permissions while capturing or materializing | A verifiable error (`journal.py status`: `durabilidad`/`permisos` `degradada(os)`, or the item ends up in `dead-letter/` with a cause), never a false success; the rest of the queue keeps processing. |
| Corrupt envelope (poisoned JSON, unsupported schema, malformed fields) | `dead-letter/` with a structured cause; it does not block the others (`journal.py replay --reintentar-dead-letter` recovers it once the cause is fixed). |
| Concurrent live session (another terminal with the same `session_id`) | Never treated as an orphan, even if its prompt log has been idle longer than the configured window. |

**What this does NOT guarantee** (out of scope, `session-end-durable-capture` spec): the last
milliseconds before a `SIGKILL` that kills the process BEFORE any hook runs (nothing can be captured
if the hook never executes); two concurrent `replay`/`recover` on the SAME project running in
parallel (a non-blocking lock serializes them: the second one waits its turn within budget or
returns `bloqueado: true` and startup continues); nor does it replace `git` as the source of truth —
an envelope never runs git (CA-01): fields derived from `git` (`ficheros_tocados`, `tareas_cambiadas`)
are computed at MATERIALIZATION time (`replay`), never at closing time.

**New frontmatter fields of an entry** (`docs/knowledge/journal/YYYY-MM-DD-<slug>.md`):

| Field | Meaning |
|---|---|
| `cierre` | `materializado` (envelope + verification via `replay`) · `recuperado_sin_cierre` (no envelope; rebuilt from the prompt log via `recover`) · `dead_letter` (only visible in the queue, `journal.py status`: never becomes an entry). |
| `materializado_en` | ISO-8601 UTC instant when `escribir_sesion` wrote the entry — usually AFTER the session's actual close (`replay` may run sessions later). |
| `derivados_en` | `replay`: the fields that depend on `git` (`ficheros_tocados`, `tareas_cambiadas`) describe the repo's state AT MATERIALIZATION time, not at session close — CA-01 forbids running git in the teardown, so there is no other possible source. Orphans recovered via `--con-recover` also carry `derivados_en: replay` (they run under the same pass). |

Measurement (CA-02): `python3 scripts/bench-session-end.py --iterations 30 --assert-p95-ms 100
--assert-p99-ms 300` reports TWO numbers with different provenance (gap 71 of the tramo-2 review):

- `p50_ms`/`p95_ms`/`p99_ms`/`max_ms`/`mean_ms` — the ones that get ASSERTED — are IN-PROCESS:
  `journal.py` is imported once and `capture_end(...)` is timed directly (3 warm-up iterations
  discarded), without the fixed cost of interpreter startup. Each measured iteration also checks
  that it actually left an envelope (otherwise `FALLO: la captura no escribió nada`).
- `e2e_p50_ms` — informative ONLY, never asserted — is a handful of real `python3 journal.py
  capture-end` subprocesses (the true end-to-end path run by `hooks/session-journal.sh`, Python
  startup included). A `subprocess.TimeoutExpired` there produces a structured `FALLO` (exit 1),
  not a traceback.

`ci.yml.MANUAL-COPY` runs it with CA-02's thresholds on every build, against the in-process numbers.

### How to check the hooks in a real session

The hooks have an automated suite (`tests/test_hooks_shell.py`: every `hooks/*.sh` run with `bash`
against a temporary project, JSON contract, debounce, degradation without `python3`, exit 0). What the
suite **cannot** prove is that Claude Code registers and shows them; check that by hand after
installing or updating the plugin, in three steps (write down the actual result, not the expected one):

1. **Progress line.** With an `en-progreso` initiative, edit its `docs/roadmap/<slug>/tasks.md` (tick a
   criterion, say) → the `📋 <slug> · T-XX/N …` line must show up as a system message. Repeat the same
   edit without changing the state → silence (debounce).
2. **Session context.** resume the session (`claude --resume`, or wait for a compaction; `/clear` does NOT fire the hook: the matcher is `startup|resume|compact`) → the piece index
   (`Plugin custom-agents — índice de piezas…`, Comandos/Skills/Agentes blocks) and the `progress-report.py session` block
   (active initiatives, task in progress, "resume from…") come in as context; with nothing active only the index comes in,
   and with `dev.json` `sesion.indice: false` only the roadmap. Activation check: ask for something that matches a skill
   without naming it ("review this diff for me") and verify it gets invoked.
3. **Implementer guard hook.** As `implementer` (e.g. `@implementer …`), try to write
   `docs/roadmap/<slug>/spec.md` → the **deny** with its reason ("only touches tasks.md…") must arrive;
   writing `tasks.md` or `docs/roadmap/README.md` must go through.

If a step does not happen: `python3 scripts/lint_plugin.py` (the `hooks.json` commands exist and are
executable), `python3 -m pytest -q tests/test_hooks_shell.py` (hook logic) and, if both are green, the
failure is in how Claude Code registers the hook (version, `${CLAUDE_PLUGIN_ROOT}`), not in the plugin.

**In CI, automatically (optional):** step 1 is covered by the `headless.yml` workflow
(`headless.yml.MANUAL-COPY` → `.github/workflows/headless.yml`; `workflow_dispatch` + Mondays 06:00 UTC).
It only runs when the repo has the `ANTHROPIC_API_KEY` secret (secrets cannot be used directly in an
`if:`: the job exposes it as `env` and every step checks `env.ANTHROPIC_API_KEY != ''` — docs.github.com,
verified 2026-09-03); without the secret it ends green with a warning. It runs `claude -p --bare
--plugin-dir . --output-format stream-json` on a copy of `evals/fixtures/project/`, asking to edit the
`demo` ledger, and considers the hooks proven when (a) the stream's `system/init` lists the plugin under
`plugins` and (b) the **witness file** `.claude/.progress-last` written by `hooks/progress-line.sh`
exists — the evidence is the file, not a `systemMessage` in the output, because the stream-json docs only
document `hook_started/hook_progress/hook_response` events for `SessionStart`/`Setup` hooks and do not
guarantee that a `PostToolUse` `systemMessage` shows up. Since the docs also do not say whether `--bare`
runs the hooks of a plugin loaded with `--plugin-dir`, when the plugin loads under `--bare` but leaves no
witness the job retries WITHOUT `--bare` and records (`::warning::`) which mode produced the evidence.
Steps 2 and 3 remain manual (an interactive session). Job details: `evals/README.md`.

## Cost of the Jira cycle (why a script writes it)

With Jira enabled, each task fires up to 6 events (`arrancar`, `implementado`, `revision`/`gaps` per
attempt, `qa-verde`/`qa-rojo`, `aprobado`). The cost lives in **who writes the comment and composes
the call**:

| | Before (prose in the prompt) | Now (`jira-flow.py` + `assets/comment-*.md`) |
|---|---|---|
| Who writes the comment | the model, every time, reading the whole ledger | the script, filling a fixed template |
| Instructions in the agent's prompt | comment format + transition rules + worklog, repeated in `implementer`, `qa` and the review skill | one line per agent ("fire event X") plus the Phase 3 table in `/dev-cycle`, **once** |
| Connector calls per event | improvised (sometimes one per criterion) | `ops` in fixed order, grouped per task (or per phase with `--batch`) |
| Weight of the templates | — | **6 templates, 1000 bytes total (`wc -c`) ≈ 245 tokens**, and only the event's own template is loaded |

**Declared measurement, not a guess:** template and script sizes are measured (`wc -c
skills/jira-sync/assets/comment-*.md` → **1000 bytes**; `wc -c
skills/jira-sync/scripts/jira-flow.py` → **41 KB** of code that **never enters the model's
context**: it runs). **The unit is the command's:** `wc -c` counts **bytes**, which with accents and
emoji are not characters (`wc -m` would say 980 — and that itself depends on the locale: under
`POSIX` it counts bytes again). This paragraph used to claim "727 chars" while citing `wc -c`,
which returned 742: the figure was characters and the command was bytes (T-fix1).

What we could **NOT** measure here is the token cost of a real session with a live Jira (this repo has no connector enabled in CI): the table above is structural
(what enters the context and what does not), not a session measurement. To measure it in your
project: `usage-meter.py start --artefacto "<slug>/T-XX"` before the first event and `close` after
`aprobado`.

**Design rule (a rule of this repo — the «Determinismo» row of `CLAUDE.md` § «Reglas al trabajar
aquí» and body rule 1 of the `plugin-dev` skill: «computations and verdicts go in scripts with tests
and exit codes […], not in agent prose»; rule 8 of `CONVENTIONS.md` does not state it, it is where it
is APPLIED to the ledger with `ledger-lint`/`qa-gate` —, taken to the integration layer):** whatever
can be deterministic is not written by the model. And its corollary in context cost: the *one
subagent per task* pattern multiplies it, so the Jira cycle spawns no subagent — they are calls from
the agent already at work.

## Where to look for what (cheat sheet)

- Cost of an initiative (process + implementation): `/roadmap-metrics`.
- Roadmap status: `/roadmap-status` (local) · `/roadmap-live` (from Jira).
- Actual cost per artifact: the `generacion:` block in the frontmatter of spec/eval/plan/tasks.
- Tokens→hour calibration: `docs/roadmap/CALIBRATION.md` (fed by `/retro`).
- Progress of the initiative in flight: the hook's progress line, the session context and the opt-in status line (`progress-report.py line|active|session`).
- Live session activity, tools, subagents: the external monitor.

**How many of those numbers are actually a measurement (`fuente: estimado` in aggregate).** Every `generacion:` block declares `fuente: medido` or `fuente: estimado`, but on its own it goes unnoticed: an `estimado` is a judgement call **shaped like a measurement**, and in aggregate it can be most of the roadmap without anyone noticing (edge E7 of [`docs/agents/CONTRACTS.md`](../agents/CONTRACTS.md)). The process report produced by `build_dashboard.py --metrics-md` — the one `/roadmap-metrics` consumes — closes the table with the line **«N de M bloques `generacion:` con `fuente: estimado`»**, and `--json` carries the additive keys `estimados`, `medidos` and `generacion_total` per initiative (the aggregate is their sum; `--json` is still the same LIST of initiatives it always was). The chain continues in `docs/roadmap/CALIBRATION.md`: a row whose `tokens/hora` was not measured is marked **`(estimado)`** in the cell with its reason, and `usage-meter.py` **drops it from the median** — without that filter, a row that inherited the current ratio fed it straight back into the median and calibration ran on its own output.
