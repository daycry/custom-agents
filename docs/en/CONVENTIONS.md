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

**Model tiering (mandatory, two layers):** every agent declares `model` **and `effort`** in its frontmatter, proportional to the complexity of its task. The linter (`scripts/lint_plugin.py`) requires both fields to be present and valid (official values from sub-agents.md, verified 2026-09-03: `model` ∈ `haiku|sonnet|opus|inherit`; `effort` ∈ `low|medium|high|xhigh|max`).

| Tier | `model` | `effort` | Agents |
|---|---|---|---|
| Mechanical (convert, format) | `haiku` | `medium` | *(none today — `pdfy` was retired, `ADR-011`)* |
| Standard development (write, plan, test, document) | `sonnet` | `medium` | `analyst`, `planner`, `implementer`, `qa`, `documenter` |
| Critical reasoning (decide, judge, audit) | `opus` | `high` | `evaluator`, `architect`, `reviewer`, `nemesis` |

Layer 1 = the frontmatter (what Claude Code always applies, and the ONLY thing it applies on a manual `@agent` invocation). Layer 2 = the per-project override in `.claude/dev.json` → `"modelos": {"<agent>": {"model": "…", "effort": "…"}}` (partial, per agent; rule 9), resolved by the deterministic script `agent-kits/shared/model-tier.py <agent> [--json|--all]` (frontmatter + dev.json; invalid value → warning and ignored; no `dev.json` → frontmatter). The **orchestrators** (`/dev-cycle`, `/pm-cycle`, `adversarial-review`, `quick-implement`) consult it before dispatching an agent by name and pass `model` in the **per-invocation `model` parameter of the Agent tool** (priority 1 since v2.1.251, above the frontmatter). **Honesty:** the Agent tool documents no `effort` parameter, so the `effort` in `dev.json` is **informative** (the orchestrator announces it; the effective one is the frontmatter's). Decision: `docs/knowledge/adr/ADR-009`.

**Short skills (progressive disclosure, mandatory):** a `skills/<skill>/SKILL.md` is injected **in full** into the context every time the skill is invoked, so it carries only the **map** — frontmatter, purpose, triggers, the step flow (title + 1-3 lines each), guardrails/invariants, "what it does NOT do" and a **references table** — while the detail (long templates, examples, edge cases, field tables, catalogues, subagent prompts) lives in `skills/<skill>/references/<topic>.md`, linked from the step that uses it with the explicit instruction "read X **only** when you reach step Y". Thresholds: `SKILL.md` ≤ **200 lines** (linter warning, `SKILL_WARN_LINES`) and **250** as the hard limit (`tests/test_skill_size.py` fails). When slimming an existing skill, **zero content loss**: every moved block reappears verbatim in a reference (`python3 tests/test_skill_size.py --diet-check <skill> <git-ref>` → `0 párrafos perdidos`) and the step names other pieces cite (`Paso 7`, `Paso 9`…) keep their numbering. Decision: `docs/knowledge/adr/ADR-008`.

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
- **Native fields `skills:` and `hooks:`** (official sub-agents docs, verified 2026-09-02). `skills:` lists the skills Claude Code **preloads** into the agent's context at startup (the full content is injected); `dependencies.skills` remains the source of the graph and must be a **superset** of `skills:` (the linter enforces it: a preloaded skill not declared as a dependency is an error). **Token-diet rule:** `skills:` only for skills the agent needs in **EVERY** run; **opt-in** ones (Jira, Confluence…) are loaded on demand through the Skill tool — preloading `jira-sync` + `confluence-publish` would cost ≈15k tokens per startup for features that may be switched off. The linter warns when the declared preload exceeds 16 KB. `hooks:` registers hooks **scoped to that agent only** (same shape as `settings.json`: event → `[{matcher, hooks: [{type: command, command}]}]`); it is the only place a guard hook is allowed (rule 8). `${CLAUDE_PLUGIN_ROOT}` is not documented for those `command`s: use it with a `find` fallback on the same line, as `agents/implementer.md` does.
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
├── design.md            # (optional) WITH WHICH ARCHITECTURE — 2-3 options, the chosen one validated (architect agent)
├── improvement-plan.md  # HOW it gets executed
├── tasks.md             # checklist of the plan's tasks
└── testing/             # (optional) output of the qa agent
```

A **no-go** evaluation leaves only `spec.md` + `evaluation.md` (no plan files). Single index: `docs/roadmap/README.md`.

States per artifact (distinct vocabularies, on purpose):

- **spec:** `borrador` (draft) · `aprobada` (approved) · `implementada` (implemented) · `obsoleta` (obsolete).
- **evaluation / plan:** `borrador` (draft) · `en-progreso` (in progress) · `en-revision` (in review) · `completado` (completed) · `cancelado` (cancelled).
- **design (optional):** `borrador` (options open) · `aprobado` (option validated by the user) · `obsoleto` (redesign or cancellation).

**Transitions along the cycle (do not leave things in `borrador`).** Every artifact is born in `borrador`,
but each phase that is passed **must** move it to the appropriate state (`/dev-cycle` guarantees this, and the
agents do so when run standalone):

- After **evaluating**: evaluation → `en-revision`. At the **go** gate: spec → `aprobada`, evaluation → `completado`. On **no-go**: evaluation → `cancelado` (spec → `obsoleta` if it is discarded).
- When **creating the plan**: plan/tasks → `borrador`. When **starting the implementation** (plan approved): plan and active phase → `en-progreso`.
- During **implementation**: each `en-progreso` task → `completado`; the phase → `completado` when its tasks are closed.
- At **closeout** (qa green + documented): plan → `completado` and spec → `implementada`.
- **Cancellation** at any point: plan/evaluation → `cancelado` (spec → `obsoleta` if applicable).

Linking rules (**bidirectional**, and since everything is in the same folder, links are **plain filenames**):

- The `spec` carries `evaluacion: evaluation.md` and `plan: improvement-plan.md` (or `pendiente`) in its frontmatter, plus callouts at the top. If there was a design step, also `design: design.md`; `design.md` carries `spec:`, `evaluacion:`, `plan:` (filled by `planner` when the plan is created) and `adr:`; `improvement-plan.md` adds a **Diseño** row.
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
- **Two classes of hooks.** (a) **Informative** — global, in `hooks/hooks.json`, `PostToolUse`/`SubagentStop`/`SessionStart`; they inform (`systemMessage`/`additionalContext`) and **always exit 0**. (b) **Guard** — `PreToolUse` with `permissionDecision: deny`, **ONLY in an agent's frontmatter `hooks:`** (agent scope), with the decision in a **deterministic script with tests** (`agent-kits/shared/guardrail-check.py`), a one-sentence reason saying how to proceed, per-rule opt-out in `.claude/dev.json` (`guardrails`), and graceful degradation (no `python3` → single warning, exit 0; internal error → allow). **A global deny is forbidden**: `planner`/`evaluator`/`analyst` legitimately write to `docs/roadmap/` and a hook in `hooks.json` would break them (ADR-007). Today the only guard hook is the `implementer`'s (`hooks/implementer-guardrail.sh`: `docs/roadmap/` scope — only `tasks.md` plus the `docs/roadmap/README.md` index, never `docs/security-scan/`, case-insensitive paths —, working branch, non-destructive git). The scope of the whole **diff** is checked separately by `agent-kits/shared/scope-check.py` (changed files vs. the ledger's `Archivos` fields) as a gate before the two-lens review (`adversarial-review` skill, single source of the method; its `review-lens-select.py` decides whether the security lens C is added) and in the implementer's DoD.
- **Live visibility (informative hooks):** the plugin registers hooks on `PostToolUse` (lint warning + **progress line** `progress-report.py line` when a `tasks.md` is edited), `SubagentStop` (state of the `en-progreso` initiatives when a subagent finishes) and `SessionStart` (`startup|resume|compact`: **piece index** via `agent-kits/shared/skill-index.py` — one line per command/skill/agent from the frontmatters, ≤ 45 lines / ≤ 3,500 chars, hash-cached in `.claude/.skill-index.cache` — plus the resume context via `progress-report.py session` and, only on `startup|resume`, the latest **session journal** entry — rule 10) and `SessionEnd` (`hooks/session-journal.sh`: writes the journal entry; its output is ignored by contract and its hooks share a 1.5 s budget that `hooks.json` raises with `timeout: 20` — hooks.md, verified 2026-09-03) (the index also on `compact` because compaction summarises the conversation and may drop the startup index — official hooks guide, verified 2026-09-03 —; total under the hook's 10,000-char cap). **The index is informative**: it reminds which pieces exist and the routing rules (matching skill → invoke it; commands are invoked by `/` or by description, like skills — Claude Code treats them as skills unless `disable-model-invocation` — and the `evals/cases/command-*.json` evals prove it with natural-language positives), it forces no invocation, and it is switched off with `dev.json` `sesion.indice: false`. Principle: **hooks inform (`systemMessage` / `hookSpecificOutput.additionalContext`), they never decide; always exit 0** — without `python3` they stay silent; a broken hook is a dead piece, not a guardrail (the linter checks that every `command` in `hooks/hooks.json` exists and is executable). Hooks have a **shell test suite** (`tests/test_hooks_shell.py`: pytest runs every `hooks/*.sh` with `bash` against a temporary project holding a fixture ledger and asserts the output JSON, the debounce — including its atomicity under 6 concurrent invocations —, the degradation without `python3` and `exit 0` in every case; the whole suite is skipped when there is no `bash`). The status line (`statusline/roadmap-statusline.sh`) is **opt-in** in `/setup` and is written with an absolute path into `.claude/settings.json` (the official docs do not expand `${CLAUDE_PLUGIN_ROOT}` in `statusLine.command`).

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
| `dev.json` | Discipline of `/dev-cycle`'s native chain: `tdd` (RED-GREEN-REFACTOR with evidence of the red), `worktree` (initiative in an isolated worktree), `subagentes` (one task = one fresh subagent), `constitucion` (decision on the `docs/CONSTITUTION.md` opt-in — distinguishes "declined" from "never asked"), `guardrails` (the implementer's guard hook: `true` by default; `false` or `{"alcance","ramaPrincipal","git"}` per rule), `revision.lenteSeguridad` (`auto` by default: the security lens C of `adversarial-review` only when `review-lens-select.py` detects sensitive paths/lines; `siempre` · `nunca`; asked by `/setup` step 5-ter), `revision.lenteRendimiento` (superiority T-04, same vocabulary and same `auto` default: the performance lens D of the SAME `review-lens-select.py`, only when it detects repository/query/queue paths or costly patterns —N+1, `await` in a loop, blocking `sleep`—; asked by the same step 5-ter), `revision.excluir` (list of `**`-aware globs removed from lenses C's and D's **path** heuristic —each with its own stems—, not from the content one — e.g. `["hooks/**"]` for a repo whose hooks are named `session-*.sh`; manual setting), `tests.coberturaMinima` (superiority T-03, **absent by default = no gate**: minimum diff coverage threshold N that `implementer` step P5 checks with the `unit-tests` skill —`coverage-gate.py --changed-only`— only when the stack's official tool is installed; without it, informational only, never blocking; asked by `/setup` step 5-quinquies), `sesion.indice` (`true` by default: the `SessionStart` hook injects the compact piece index from `skill-index.py`; `false` turns it off and leaves only the roadmap resume context), `sesion.journal` (`true` by default: the `SessionEnd` hook writes the session log entry under `docs/knowledge/journal/` and `SessionStart` re-injects the latest one; `false` turns it off — rule 10), `modelos` (**configurable tiering, layer 2** — `{"<agent>": {"model": "haiku|sonnet|opus|inherit|claude-…", "effort": "low|medium|high|xhigh|max"}}`, partial and per agent; resolved by `agent-kits/shared/model-tier.py` and passed by the orchestrators in the Agent tool's `model` parameter; `effort` here is informative — the Agent tool has no per-invocation effort —; a manual `@agent` invocation follows the frontmatter; asked by `/setup` step 5-quater). All opt-in with defaults `false` except `guardrails` (on), `revision.lenteSeguridad`/`revision.lenteRendimiento` (`auto` each), `sesion.indice` and `sesion.journal` (on), `modelos` (absent = frontmatter) and `tests.coberturaMinima` (absent = no gate) | `/setup` or by hand | Recreate with `/setup`; missing or corrupted file → defaults `false` + warning (classic behavior) |
| `usage-state.json` | Cost-measurement markers (`usage-meter.py`: offsets per transcript and artifact) | `usage-meter.py` | Deleting it is harmless: open markers are lost; subsequent `start` calls recreate it |
| `.confluence-pending` | Ephemeral hook flag (there are unsynced docs) | `PostToolUse` hook | Deleting it is harmless; the skill re-detects via manifest |

Rules: **config ≠ state** (config is decided by the user; state is maintained by the machine and
is never edited by hand); every new skill that needs memory follows this pattern (`<skill>.json` +
`<skill>-state.json`) and adds its row here.

## 10. Project technical memory — `docs/knowledge/`

Besides the roadmap (rule 7, decision+outcome per initiative) and configuration (rule 9), the
plugin keeps a **cross-cutting technical memory** in the consuming project's `docs/knowledge/`:
design decisions (ADR), already-proven traps (gotchas) and process lessons — "what should never
have to be re-discovered", generalizing the bookend pattern from `agents/nemesis.md`
(`docs/security-scan/STATE.md`+`MEMORY.md`).

- **Where it lives.** `docs/knowledge/adr/ADR-NNN-<slug>.md` (one per decision, template
  `agent-kits/shared/templates/adr.md`), `docs/knowledge/gotchas/GOT-NNN-<slug>.md` (one per
  entry) and `docs/knowledge/lessons/LES-NNN-<agent>-<slug>.md` (one per entry, grouped by agent
  in the filename),
  with an **entry-point** index `README.md` (the generated index + `knowledge-lint.py` remain
  deferred until there is evidence they are needed: more than 15 entries, or the first ID
  collision in any of the three families, in a parallel batch). One file per entry across all
  three types removes the FILE collision risk in parallel writes; the `id:` collision risk
  remains possible across all three families (ADR/GOT/LES), with the same mitigation (renumber
  and declare it in the retro), see previous rule.
- **Always active, no opt-in.** If `docs/knowledge/` did not exist, no agent would complain: the
  folder is created on first write. Same silent-degradation philosophy as the rest of the plugin
  (constitution, Jira, Confluence), but without a switch — there is nothing to turn on.
- **Registration threshold (anti-bureaucracy).** An ADR only if the decision **closes a real
  alternative** AND (it affects 2+ pieces of the repo OR it was taken at a decision gate) — naming
  a variable, a freely reversible decision, or something already implicit in an existing rule does
  **not** deserve an ADR. A gotcha only if it cost **at least one real debugging cycle** or nearly
  broke a product guarantee — an unverified hunch or a typo fixed on the fly does **not** deserve a
  gotcha. The goal is 0-2 entries per initiative, not an exhaustive log.
- **Who writes.** `architect` writes the ADR of the chosen design option (the discarded ones as alternatives) when `design.md` is approved; `planner`/`implementer` write an ADR when a design decision (while decomposing
  the plan, or resolving an ambiguity during execution) crosses the threshold, with
  `estado: propuesta` to be validated by the two-lens review or the user. `debug-root-cause` writes
  a gotcha when it closes its Phase 4 (root cause confirmed, not a partial diagnosis). `qa` writes
  a gotcha when a justified flaky turns out to be a **pattern** (2+ cycles with the same cause), not
  an isolated accident. `/retro` produces, in addition to `CALIBRATION.md`'s numeric row, a
  **second output** with the qualitative technical learnings from the initiative's closeout. Shared
  fragment: `agent-kits/shared/knowledge-write.md`.
- **Who reads.** `evaluator`, `planner`, `implementer`, `qa` and `documenter` apply the shared step
  `agent-kits/shared/knowledge-check.md` before working: they read the entry index (`README.md`)
  and open **only the specific entry file** in their area (SELECTIVE reading, progressive
  disclosure — protects the `2026-08-10-token-diet` investment; never "all of `gotchas/`" or "all
  of `lessons/`"). Split: `evaluator` → `lessons/LES-*-evaluator-*`; `planner` → `adr/` + `lessons/`;
  `implementer` → `adr/` + `gotchas/`; `qa` → `gotchas/`; `documenter` → everything the index
  lists (it is the one that indexes it into product documentation).
- **Proof of the mechanism ("Prueba del mecanismo" row of `knowledge-capture`'s spec, not D3).**
  The "three lessons from the first real calibration" that used to live hardcoded in
  `agents/evaluator.md` were migrated to `docs/knowledge/LESSONS.md#evaluator` (now split across
  three files under `docs/knowledge/lessons/`, after `knowledge-split`): the prompt now
  reads them from there instead of carrying them inline. That is the test that the reading loop
  truly works — the lessons can leave the prompt and keep applying. **Note:** this only happens
  once the project's `docs/knowledge/` is populated with them (this repo, after the backfill); a
  freshly installed consuming project starts with an empty memory (D3: always active, no opt-in,
  but no content until the first write) and fills it via `/retro` and the decision gates.
- **Session journal — EPISODIC, uncurated memory (`docs/knowledge/journal/`, initiative
  `memory-health`).** Next to the **curated** memory (ADR/gotchas/lessons: with a threshold, a state and
  a gate that validates them) lives a **chronological per-session log**: `journal/YYYY-MM-DD-<slug>.md`,
  one entry per session, written by the `SessionEnd` hook (`hooks/session-journal.sh` →
  `agent-kits/shared/journal.py write`, idempotent by `session_id`) as a **deterministic draft** (date,
  active initiative, files touched per git, ledger tasks whose state changed, closed meter markers, first
  prompt as a best-effort summary) and re-injected compacted by `SessionStart` (`startup|resume`, not
  `compact`; ≤ 25 lines, `journal.py latest`). Rules: (1) nobody writes it by hand except to enrich the
  current session's entry (`--enrich`); (2) **whatever deserves doctrine gets promoted** to
  `adr/`/`gotchas/`/`lessons/` under the `knowledge-write.md` threshold — the journal is not where a
  decision stays; (3) `evaluator`/`planner`/`architect` read ONLY the latest entry and ONLY when it belongs
  to their initiative (`knowledge-check.md`); `/retro` uses the initiative's entries as a source of
  deviation causes; (4) **excluded from Confluence** (`docs/knowledge/journal/**`: a log, not a decision —
  policy D1) and with its own generated index (`journal/README.md`), outside the `docs/knowledge/README.md`
  table; (5) per-project opt-out `dev.json` `sesion.journal: false`; (6) the hook **only writes in
  projects that show a trace of the plugin** (`docs/roadmap/`, `docs/knowledge/` or `.claude/dev.json`)
  — in any other repo it exits silently; (7) **entries are versioned** (project memory, like ADRs and
  lessons) — whoever prefers not to adds `docs/knowledge/journal/*.md` (not the `README.md`) to their
  `.gitignore`; the file name is `YYYY-MM-DD-<active initiative | sesion>.md`. **No AI summary**: the official hooks
  docs (2026-09-03) only let `prompt`/`agent` hooks return an `ok/reason` decision, and on `SessionEnd`
  every output is ignored — documented as a limitation (ADR-010), not faked.
- **Note (D2):** the "Notas de implementación" section of the planner's
  `agent-kits/planner/templates/tasks.md` template was retired (`knowledge-capture` initiative,
  task T-14) — an initiative's qualitative record now lives in `docs/knowledge/`, not in a
  catch-all drawer at the end of the ledger.
