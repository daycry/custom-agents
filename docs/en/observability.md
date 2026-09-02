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
  finishes) and `SessionStart` (resume context on startup/resume/compaction). They do not intercept
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
| On startup, resume or after context compaction | `SessionStart` hook → `session-context.sh` | Block ≤ 15 lines injected as context: active initiatives, in-progress tasks, open usage-meter markers and "resume from the in-progress task". Nothing active → nothing injected. |
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
2. **Session context.** resume the session (`claude --resume`, or wait for a compaction; `/clear` does NOT fire the hook: the matcher is `startup|resume|compact`) → the
   `progress-report.py session` block (active initiatives, task in progress, "resume from…") comes in as
   context; with nothing active, nothing comes in.
3. **Implementer guard hook.** As `implementer` (e.g. `@implementer …`), try to write
   `docs/roadmap/<slug>/spec.md` → the **deny** with its reason ("only touches tasks.md…") must arrive;
   writing `tasks.md` or `docs/roadmap/README.md` must go through.

If a step does not happen: `python3 scripts/lint_plugin.py` (the `hooks.json` commands exist and are
executable), `python3 -m pytest -q tests/test_hooks_shell.py` (hook logic) and, if both are green, the
failure is in how Claude Code registers the hook (version, `${CLAUDE_PLUGIN_ROOT}`), not in the plugin.

## Where to look for what (cheat sheet)

- Cost of an initiative (process + implementation): `/roadmap-metrics`.
- Roadmap status: `/roadmap-status` (local) · `/roadmap-live` (from Jira).
- Actual cost per artifact: the `generacion:` block in the frontmatter of spec/eval/plan/tasks.
- Tokens→hour calibration: `docs/roadmap/CALIBRATION.md` (fed by `/retro`).
- Progress of the initiative in flight: the hook's progress line, the session context and the opt-in status line (`progress-report.py line|active|session`).
- Live session activity, tools, subagents: the external monitor.
