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

- **This plugin** registers **non-blocking** `PostToolUse` hooks (`hooks/hooks.json`): marking
  `docs/` as pending for Confluence and the `ledger-lint` warning on `tasks.md`. They do not intercept
  or modify anything; they only observe and warn.
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

## Where to look for what (cheat sheet)

- Cost of an initiative (process + implementation): `/roadmap-metrics`.
- Roadmap status: `/roadmap-status` (local) · `/roadmap-live` (from Jira).
- Actual cost per artifact: the `generacion:` block in the frontmatter of spec/eval/plan/tasks.
- Tokens→hour calibration: `docs/roadmap/CALIBRATION.md` (fed by `/retro`).
- Live session activity, tools, subagents: the external monitor.
