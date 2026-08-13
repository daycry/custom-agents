# Organization conventions — custom agents

**English** · [Español](../CONVENTIONS.md)

Rules for adding agents without them stepping on each other, while allowing some to depend on others or on shared resources. **Read this before creating or moving anything.**

## 1. Principle

Three artifact types, three fixed locations. Anything **shared** lives in common folders keyed by unique name; anything **private** to an agent lives in its own namespace. Documentation goes **always** in `docs/`, never next to the code.

```
custom-agents/               (root; deployed as the project's .claude/)
├── agents/<agent>.md        # agent definition (one per file, flat)
├── skills/<skill>/          # SHARED skills (reusable by several agents)
├── agent-kits/<agent>/      # an agent's PRIVATE toolkit (scripts, templates)
└── docs/                    # ALL documentation
    ├── README.md            # master index (update it when adding an agent)
    ├── CONVENTIONS.md       # this document
    ├── INSTALL.md           # bundle deployment
    └── agents/<agent>*.md   # per-agent documentation
```

## 2. Naming (avoids collisions)

- **One agent = one kebab-case name** (`nemesis`, `code-reviewer`, `db-migrator`). That name is the unique key across the whole repo.
- The agent's file is `agents/<name>.md` and its frontmatter `name:` **must** match `<name>`.
- An agent's private toolkit goes in `agent-kits/<name>/` — same name. That way two toolkits can never collide.
- Skills are named by **function**, not by agent (`cybersecurity`, not `nemesis-sast`), because they are meant to be reused.
- An agent's documentation lives in `docs/agents/<name>.md` (+ auxiliary files prefixed with `<name>-`, e.g. `nemesis-presentacion.md`).

## 3. Shared vs. private — how to decide

| Will more than one agent use it? | Where it goes |
|----------------------------------|---------------|
| Yes (or it is meant for reuse) | `skills/<skill>/` — shared |
| No, it is specific to one agent | `agent-kits/<agent>/` — private |

Rule of thumb: when in doubt, start in the private kit. Promote it to `skills/` the day a second agent needs it (and update both agents' dependencies).

**Exception — `agent-kits/shared/` (shared prompt fragments):** when a **piece of prompt text** (not a script or an invocable skill) must be identical across several agents —the estimation parameters table, the Confluence opt-in step—, it lives in `agent-kits/shared/` with **a single source of truth**, and agents reference it with the same `find` resolution as their kits. It is not any specific agent's kit; it is the documented exception to "one kit per agent". An agent that cannot find it (partial installation) uses the one-line fallback in its own prompt. See `agent-kits/shared/README.md`. The state-transition table is **not** duplicated: its only source is §7.

**Model tiering (mandatory):** every agent declares `model` in its frontmatter, proportional to the complexity of its task (`haiku` mechanical · `sonnet` standard development · `opus` critical reasoning · `inherit` to inherit the session's model). The linter (`scripts/lint_plugin.py`) requires the field to be present and valid.

## 4. Dependencies — declared in the agent's frontmatter

Each agent declares what it depends on in its own `agents/<name>.md`. Single source of truth, right next to the agent.

```yaml
---
name: nemesis
description: ...
tools: Read, Grep, Glob, Bash, Write, Edit, WebFetch, Agent
dependencies:
  skills:            # skills from skills/ that it needs
    - cybersecurity
  kits:              # private toolkits from agent-kits/ that it uses
    - agent-kits/nemesis
  agents: []         # other agents it depends on (by name)
---
```

Notes:

- The keys `name`, `description`, `tools` (and `model`) are the ones Claude Code interprets. `dependencies` is **informative**: Claude Code ignores extra keys, and it serves us (and scripts) to see the graph at a glance.
- An agent **may** depend on another agent (the `agents` field). Reference it by name; the other agent must exist in `agents/`. Avoid cycles (A→B→A).
- A private kit (`agent-kits/<x>/`) belongs to its agent; if another agent needs it, that is a sign the code should be a shared skill (see §3).

## 5. Paths inside the code

- A kit's scripts locate each other with **relative paths** (`dirname "$BASH_SOURCE"`), never with absolute repo paths. That way renaming/moving the kit breaks nothing internal.
- **When the agent (`.md`) invokes its toolkit or templates, do NOT use fixed paths** like `.claude/agent-kits/...`: they only work at project scope and break at user scope or as a plugin (besides, `${CLAUDE_PLUGIN_ROOT}` is not expanded in agent/skill markdown). Resolve the kit at runtime with `find` over both scopes:

  ```bash
  MIKIT="$(find "$PWD/.claude" "$HOME/.claude" -type d -path '*agent-kits/<nombre>' 2>/dev/null | head -1)"
  # then use "$MIKIT/tools/..." , "$MIKIT/templates/..." , etc.
  ```

  `$PWD/.claude` covers project scope; `$HOME/.claude` covers both user scope (`~/.claude/`) and the plugin cache (`~/.claude/plugins/…`). The project comes first → it wins if there are multiple copies (same precedence as Claude Code).
- Shared skills: invoke them with the Skill tool (by name). If you need to read one of their files, resolve it the same way: `find "$PWD/.claude" "$HOME/.claude" -type f -path '*skills/<skill>/...'`.

## 6. Checklist for adding a new agent

1. Choose a unique kebab-case name.
2. Create `agents/<name>.md` with frontmatter (including the `dependencies` block).
3. If it needs its own scripts → `agent-kits/<name>/`. If it is reusable → `skills/<skill>/`.
4. Write the doc in `docs/agents/<name>.md`.
5. Add the corresponding row in `docs/README.md` (agents and, if applicable, skills).
6. **Update the diagrams in `docs/FLOWS.md`** if the agent/command/skill changes any flow.
7. Verify there are no broken absolute paths or duplicate names.

## 7. Artifact chain: spec → evaluation → plan (single folder per initiative)

The `evaluator` and `planner` agents produce their artifacts in **a single folder per initiative**: `docs/roadmap/<fecha>-<slug>/`. Everything belonging to an initiative lives together.

```
docs/roadmap/<fecha>-<slug>/
├── spec.md              # WHAT is wanted (specification)
├── evaluation.md        # HOW MUCH it costs / whether it is worth it
├── improvement-plan.md  # HOW it gets executed
├── tasks.md             # checklist of the plan's tasks
└── testing/             # (optional) output of the qa agent
```

A **no-go** evaluation leaves only `spec.md` + `evaluation.md` (no plan files). Single index: `docs/roadmap/README.md`.

States per artifact (distinct vocabularies, on purpose):

- **spec:** `borrador` (draft) · `aprobada` (approved) · `implementada` (implemented) · `obsoleta` (obsolete).
- **evaluation / plan:** `borrador` (draft) · `en-progreso` (in progress) · `en-revision` (in review) · `completado` (completed) · `cancelado` (cancelled).

**Transitions along the cycle (do not leave things in `borrador`).** Every artifact is born in `borrador`,
but each phase that is passed **must** move it to the appropriate state (`/dev-cycle` guarantees this, and the
agents do so when run standalone):

- After **evaluating**: evaluation → `en-revision`. At the **go** gate: spec → `aprobada`, evaluation → `completado`. On **no-go**: evaluation → `cancelado` (spec → `obsoleta` if it is discarded).
- When **creating the plan**: plan/tasks → `borrador`. When **starting the implementation** (plan approved): plan and active phase → `en-progreso`.
- During **implementation**: each `en-progreso` task → `completado`; the phase → `completado` when its tasks are closed.
- At **closeout** (qa green + documented): plan → `completado` and spec → `implementada`.
- **Cancellation** at any point: plan/evaluation → `cancelado` (spec → `obsoleta` if applicable).

Linking rules (**bidirectional**, and since everything is in the same folder, links are **plain filenames**):

- The `spec` carries `evaluacion: evaluation.md` and `plan: improvement-plan.md` (or `pendiente`) in its frontmatter, plus callouts at the top.
- `evaluation.md` carries **Spec** (`spec.md`) and **Plan** (`improvement-plan.md`) rows; `improvement-plan.md` carries **Spec** (`spec.md`) and **Evaluación** (`evaluation.md`) rows.
- When **creating the evaluation**: fill in its **Spec** row and **update the spec** (`evaluacion:` + callout) so it points to the evaluation.
- When **creating the plan**: fill in its **Spec/Evaluación** rows and **update backwards** the spec's `plan:` and the evaluation's **Plan** row.

**Generation cost (`generacion:` block).** Each artifact in the chain carries in its
frontmatter a `generacion:` block with what it cost to **produce it**, measured by
`agent-kits/shared/usage-meter.py` (`start` when opening it, `close` when closing it): start/end
dates (only **context**, never a source of hours), `tokens_reales` (the **measurement**, read from the
session transcript), `eur`, `horas_ia` (**derived**: billable tokens × calibrated ratio —
median from `CALIBRATION.md` > default from `estimation-defaults.md`) and `fuente:
medido|estimado`. Rules: the meter **never blocks** (if it cannot read the transcript, it degrades
to `estimado` with a warning); re-closing **replaces** the block (it does not accumulate); every agent **closes its
marker before the handoff** (overlapping windows misallocate the cost); legacy artifacts
without the block are valid. Durations presented to people use the human format `XhYm`
(`usage-meter.py fmt`: `32m` · `1h 32m` · `18h`). `/roadmap-metrics` aggregates these blocks as
**process cost** (separate from implementation cost) and `/retro` calibrates the ratio with them.

## 8. Progress of a plan: `tasks.md` is the canonical ledger

A plan's progress is recorded in **a single place**: `docs/roadmap/<fecha>-<slug>/tasks.md`
(checkbox + per-task T-XX state + summary table). It is the **single source of truth**.

- **Any implementer** must update `tasks.md` upon completing each task: the `implementer` agent, the main chat, or an **external orchestrator** (any third-party SDD engine).
- If a tool keeps its own record (internal todo-list, the external engine's own progress file, etc.), that record is a **mirror**, not a source: `tasks.md` rules. On discrepancy, `tasks.md` wins.
- The `/dev-cycle` orchestrator and the `implementer` agent apply this rule out of the box. So that external orchestrators respect it, `/dev-cycle` offers to add this rule to the consuming project's `CLAUDE.md`.
- **States with an external engine:** when implementation is delegated to an external orchestrator, that engine does **not** update your artifacts. Therefore `/dev-cycle` (or you) applies the **state transitions** of rule 7 and keeps `tasks.md` up to date on its behalf. The transitions apply equally with or without an external engine.
- The cycle closeout (documentation with `documenter`) happens **once**, after implementing and with `qa` green, not task by task.
- **Mechanical validation:** `agent-kits/shared/ledger-lint.py` checks the ledger with an exit code (state vocabulary, `completado` ⟹ criteria checked, summary adding up, unique IDs). It is run by `implementer` (DoD), `qa` (P1) and `/dev-cycle` at their gates; additionally, a PostToolUse hook (`hooks/ledger-lint-warn.sh`) runs it in **warning mode** on every edit of a `tasks.md`. The qa "green" is mechanical too: `agent-kits/qa/qa-gate.py` over `results.json`.

## 9. Config/state files in the consuming project's `.claude/`

Each skill stores its config (user decisions) and its state (machine memory) in the project's
`.claude/`. Single map — who writes what and how to recover it if lost:

| File | What it is | Written by | If corrupted/lost |
|---|---|---|---|
| `rates.json` | Shared budget config (rate, tokens, workday, ratios) | `/setup` or by hand | Recreate from `agent-kits/evaluator/templates/rates.example.json` |
| `confluence.json` | Opt-in + publishing destination (space/anchor) | `confluence-publish` skill | Re-run the guided onboarding (choose the space again) |
| `confluence-state.json` | Page↔file manifest (hash + pageId) | `confluence-publish`/`pull` | Rebuilds itself: publish searches by title under the anchor before creating |
| `jira.json` | Opt-in + workday policy (`alCubrirJornada`) | `jira-sync` skill or `/setup` | Recreate with `/setup`; safe defaults |
| `jira-state.json` | T-XX↔issue mapping, logged time per day, hours bank | `jira-sync` (via `worklog.py`) | Mapping: re-derivable from the keys annotated in `tasks.md`; logged time/bank: review worklogs in Jira |
| `dev.json` | Discipline of `/dev-cycle`'s native chain: `tdd` (RED-GREEN-REFACTOR with evidence of the red), `worktree` (initiative in an isolated worktree), `subagentes` (one task = one fresh subagent), `constitucion` (decision on the `docs/CONSTITUTION.md` opt-in — distinguishes "declined" from "never asked"). All opt-in, defaults `false` | `/setup` or by hand | Recreate with `/setup`; missing or corrupted file → defaults `false` + warning (classic behavior) |
| `usage-state.json` | Cost-measurement markers (`usage-meter.py`: offsets per transcript and artifact) | `usage-meter.py` | Deleting it is harmless: open markers are lost; subsequent `start` calls recreate it |
| `.confluence-pending` | Ephemeral hook flag (there are unsynced docs) | `PostToolUse` hook | Deleting it is harmless; the skill re-detects via manifest |

Rules: **config ≠ state** (config is decided by the user; state is maintained by the machine and
is never edited by hand); every new skill that needs memory follows this pattern (`<skill>.json` +
`<skill>-state.json`) and adds its row here.
