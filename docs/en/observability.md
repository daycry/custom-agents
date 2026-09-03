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

## Hook coexistence (verified)

- **This plugin** registers **non-blocking** hooks (`hooks/hooks.json`) on three events:
  `PostToolUse` (marking `docs/` as pending for Confluence, the `ledger-lint` warning and the
  **progress line** on `tasks.md`), `SubagentStop` (state of the active initiatives when a subagent
  finishes), `SessionStart` (plugin piece index + resume context on startup/resume/compaction +
  latest journal entry on startup/resume) and `SessionEnd` (session log entry under
  `docs/knowledge/journal/`).
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
| When the session ends (exit, `/clear`, logout) | `SessionEnd` hook → `session-journal.sh` | Nothing on screen (by contract `SessionEnd` output is ignored): writes `docs/knowledge/journal/YYYY-MM-DD-<slug>.md` with `agent-kits/shared/journal.py write` — a **deterministic draft** (date, active initiative, files touched per git, ledger tasks whose state changed, closed meter markers, first prompt as summary), idempotent by `session_id`. On startup/resume (`startup\|resume`, not `compact`) `session-context.sh` appends (3) the latest entry compacted (≤ 25 lines, `journal.py latest`). Disable with `dev.json` `{"sesion": {"journal": false}}`. **No AI summary**: the official docs (hooks.md, 2026-09-03) only let `prompt`/`agent` hooks return an `ok/reason` decision, and on `SessionEnd` every output is ignored; `journal.py write --enrich` stays manual. Budget: `SessionEnd` hooks share 1.5 s → `hooks.json` declares `timeout: 20`. |
| Always, in the status bar (**opt-in** in `/setup`, step 5-bis) | `statusline/roadmap-statusline.sh` | `[Opus] $0.01 ctx 8% · 📋 <slug> T-04/12 33%` — model, session cost, context used and roadmap progress. Without `jq` it uses `python3`; with neither, model only. |

Reverting the status line: remove the `statusLine` key from `.claude/settings.json`.

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

**Design rule (the same one superpowers applies to its skills, taken to the integration layer):**
whatever can be deterministic is not written by the model. Superpowers has no project-tracker
integration, so there is nothing to copy here — but there is something not to repeat: its *one
subagent per task* pattern multiplies context; the Jira cycle spawns no subagent, they are calls
from the agent already at work.

## Where to look for what (cheat sheet)

- Cost of an initiative (process + implementation): `/roadmap-metrics`.
- Roadmap status: `/roadmap-status` (local) · `/roadmap-live` (from Jira).
- Actual cost per artifact: the `generacion:` block in the frontmatter of spec/eval/plan/tasks.
- Tokens→hour calibration: `docs/roadmap/CALIBRATION.md` (fed by `/retro`).
- Progress of the initiative in flight: the hook's progress line, the session context and the opt-in status line (`progress-report.py line|active|session`).
- Live session activity, tools, subagents: the external monitor.
