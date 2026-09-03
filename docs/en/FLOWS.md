# Plugin flows — diagrams

**English** · [Español](../FLOWS.md)

Visual overview of how agents, commands and skills fit together. The diagrams are Mermaid
(they render on GitHub and in compatible editors).

**Legend:** **solid** arrow = main flow · **dotted** arrow = optional, return or feedback · diamond = decision/gate · green = forward path (*go*/green) · red = rejection or step back (*no-go*/red).

## 0 · General map — who uses what

```mermaid
flowchart TD
    PM(["👤 PM / product"]) --> S0["/setup"]
    PM --> P1["/pm-cycle<br/>defines and budgets"]
    PM --> P2["/pm-backlog<br/>prioritizes portfolio"]
    PM --> P3["/confluence-pull<br/>docs without git"]
    DEV(["👩‍💻 Dev / team"]) --> D1["/dev-cycle<br/>builds"]
    DEV --> D2["/retro<br/>learns"]
    DIR(["👔 Management"]) --> V1["/roadmap-brief<br/>one-pager PDF"]
    TODOS(["👀 Anyone"]) --> V0["/doctor<br/>is it installed correctly?"]
    TODOS --> V2["/roadmap-status<br/>dashboard"]
    TODOS --> V3["/roadmap-metrics<br/>actual vs estimated"]
    TODOS --> V4["/roadmap-live<br/>live Jira"]
    P1 -->|go| D1
    D1 --> V3
    D2 -.->|CALIBRATION.md| P1
```

## 1 · The complete chain of an initiative

**Product** phase: `analyst → evaluator` (+ optional `architect` after the go). **Development** phase: `planner → implementer → qa`. The adversarial review dispatches its lenses to the read-only `reviewer` agent.

```mermaid
flowchart LR
    idea(["💡 Idea / request"]) --> analyst["🗣️ analyst<br/>requirements gathering"]
    analyst -->|spec aprobada| evaluator["💶 evaluator<br/>budgets<br/>(+ code-health opt-in: measured risk)"]
    evaluator -->|go| planner["🗺️ planner<br/>plan + tasks"]
    evaluator -.->|"go + High complexity<br/>(opt-in)"| architect["🏗️ architect<br/>2-3 options → design.md<br/>2 passes: options → user choice → ADR"]
    architect -->|design approved| planner
    evaluator -.->|no-go| fin1(["✋ discarded"])
    planner --> implementer["⚙️ implementer<br/>code + ledger"]
    implementer --> scope{"scope-check.py<br/>diff ⊆ Archivos?"}
    scope -.->|out of scope| implementer
    scope -->|exit 0| review["🔍 skill adversarial-review<br/>lenses A+B → reviewer agent (read-only)<br/>in parallel, fresh context<br/>(+ security lens C when the diff warrants it)"]
    review -->|no gaps| qa["✅ qa<br/>E2E Playwright"]
    review -.->|correctness gaps| implementer
    qa -->|green| documenter["📚 documenter<br/>project docs"]
    qa -.->|red| implementer
    documenter --> retro["🔁 /retro<br/>calibration"]
    nemesis["🛡️ nemesis<br/>audit"] -.->|critical findings| analyst
    retro -.->|CALIBRATION.md| evaluator
    style fin1 fill:#fdecea,stroke:#ef9a9a
    style documenter fill:#e8f5e9,stroke:#81c784
```

Everything lives in **one folder per initiative**: `docs/roadmap/<fecha>-<slug>/`
(`spec.md → evaluation.md → [design.md] → improvement-plan.md + tasks.md → testing/ → retro.md`).

## 2 · `/pm-cycle` — product role (defines and budgets, closes at the gate)

```mermaid
flowchart TD
    A["/pm-cycle objective"] --> B{"objective<br/>well defined?"}
    B -->|no| C["@analyst<br/>interview → spec.md"]
    B -->|yes| D["evaluator<br/>spec + evaluation.md"]
    C --> D
    D --> E{"gate<br/>go / no-go"}
    E -->|no-go| F["evaluation → cancelado<br/>spec → obsoleta"]
    E -->|needs revision| C
    E -->|go| G["spec → aprobada<br/>evaluation → completado"]
    G -.->|"opt-in (recommended when<br/>complexity is High)"| AR["architect<br/>design.md: 2-3 options<br/>2 passes · user choice · ADR"]
    AR -.-> H
    G --> H["opt-in outputs:<br/>📄 brief PDF · 🎫 epic in Jira"]
    H --> I(["offers handoff to /dev-cycle<br/>without running it"])
    style F fill:#fdecea,stroke:#ef9a9a
    style G fill:#e8f5e9,stroke:#81c784
    style I fill:#e8f5e9,stroke:#81c784
```

## 3 · `/dev-cycle` — development cycle (with gates)

> **Entry gate (Phase 0-bis):** `/dev-cycle` first asks **full flow** vs **fast track**. The fast track skips evaluator+architect+planner (creates a lightweight `tasks.md`) and goes straight into implementation, but keeps the two-lens review + qa. **The review is the `adversarial-review` skill** (single source of the method: `scope-check.py` gate, lenses A/B dispatched to the read-only **`reviewer`** agent — fallback to a generic subagent —, **conditional** lenses C (security) and **D (performance)** decided by `review-lens-select.py` (sensitive paths/lines · N+1, `await`/regex in a loop, blocking `sleep` patterns; `dev.json` `revision.lenteSeguridad`/`revision.lenteRendimiento`), loop bounded to 3); `/dev-cycle` only invokes it, keeps the attempt counter and logs the `[revisión]` worklog. It is also used on demand ("review this diff") without a ledger. **Phase 2-a (optional):** `architect` before `planner` when `design.md` exists or the user asks for it. **Model per agent:** before each dispatch, `model-tier.py <agent>` (frontmatter + `dev.json` `modelos`) → the Agent tool's `model` parameter.
>
> **Two entry points into the same gate:** the `/dev-cycle` command (explicit, with the slash) and the `quick-implement` skill, which auto-invokes from natural language ("implement X quickly") and enters through the fast-track branch after its suitability filter. The skill defines no method of its own: it delegates to this very Phase 0-bis.

```mermaid
flowchart TD
    NL(["natural-language request<br/>\"implement X quickly\""]) -.->|"quick-implement skill<br/>(suitability filter)"| Z
    A["/dev-cycle objective"] --> Z{"full flow<br/>or fast track?"}
    Z -->|fast track| Q["lightweight tasks.md<br/>(no spec/eval/plan)"]
    Q --> H
    Z -->|full| B{"folder with<br/>spec+evaluation<br/>from /pm-cycle?"}
    B -->|yes| AD
    B -->|no| C["evaluator → go/no-go gate"]
    C -->|go| AD{"design.md present or<br/>requested by the user?"}
    AD -->|yes| AR["architect<br/>options → approved design.md"]
    AR --> D
    AD -->|no| D["planner<br/>improvement-plan + tasks.md"]
    C -->|no-go| X(["stop"])
    D --> E["opt-in: push plan to Jira<br/>jira-sync: 1 issue per task"]
    E --> F{"did the user ask for<br/>an external engine<br/>explicitly?"}
    F -->|"yes (explicit opt-in)"| G["external engine executes<br/>against YOUR tasks.md<br/>(its own review)"]
    F -->|"no (default):<br/>NATIVE chain"| H["implementer<br/>task by task<br/>(dev.json opt-in: TDD ·<br/>worktree · fresh subagents)<br/>P5: coverage gate, unit-tests skill<br/>(coverage-gate.py --changed-only)"]
    H --> SC{"scope-check.py<br/>changed files ⊆<br/>ledger's Archivos?"}
    SC -.->|"exit 1: Important gap<br/>(no reviewers spent)"| H
    SC -->|exit 0| R["🔍 skill adversarial-review<br/>lenses A+B → reviewer agent<br/>(read-only, tier from model-tier.py)<br/>+ C security + D performance<br/>(conditional: review-lens-select.py)<br/>(merge + dedupe)"]
    R -.->|gaps| H
    G --> I["qa · local E2E<br/>verdict: qa-gate.py"]
    R --> I
    I -->|"red (max 3 attempts,<br/>then ask)"| H
    I -->|green| J["documenter<br/>once at the end"]
    J --> CS["changelog-sync skill<br/>[Unreleased] EN + [Sin publicar] ES<br/>from the closed ledger"]
    CS --> K["optional: nemesis<br/>audit"]
    K --> L(["closeout: plan completado<br/>spec implementada"])
    style X fill:#fdecea,stroke:#ef9a9a
    style L fill:#e8f5e9,stroke:#81c784
```

`tasks.md` is the **canonical ledger** of progress in both modes.

## 4 · Jira (opt-in) — pushing the plan when it is created

> **Granularity** (`.claude/jira.json` → `granularidad`): **task** = one issue per `T-XX` (default); **phase** = one issue per Phase with its tasks as a checklist. In phase mode, comments/worklog/Done go to the phase's issue; the issue closes when all its tasks are `completado`. Additionally, the **reviewer's result** (Mode B) is published as a comment (per criterion ✓/✗ + number of attempts) and its time is logged as a separate `[revisión]` worklog — at the chosen granularity.

```mermaid
flowchart TD
    A["destination selector<br/>+ task/phase granularity<br/>artifact or conversational"] --> B{"parent?"}
    B -->|new epic| C["create Epic<br/>+ Tasks below it"]
    B -->|existing issue| D{"parent level<br/>discovered"}
    B -->|no parent| E["standalone Tasks<br/>in the project"]
    D -->|epic / initiative| C2["Tasks"]
    D -->|task / story| C3["Subtasks"]
    C --> F["dry-run + confirmation<br/>→ create issues<br/>keys → tasks.md"]
    C2 --> F
    C3 --> F
    E --> F
    O["/roadmap-live<br/>live status by label"] -.->|reads| F
```

## 4b · Jira (opt-in) — time logging when each task is completed

> **Careful: completing a task does NOT move it to Done.** The worklog is logged when the task
> closes; the issue only reaches *Done* through the `aprobado` event of the cycle below (4c), after
> review and `qa`.

```mermaid
flowchart TD
    G["task completado<br/>in tasks.md"] --> H["worklog.py plan<br/>AI + supervision, actual→est"]
    H --> I{"does it fit in<br/>today's workday?"}
    I -->|yes| J["log worklog<br/>(issue STAYS in progress)"]
    I -->|no| K{"policy"}
    K -->|bank| L["log the rest of today<br/>excess → bank per issue<br/>paid off on following days"]
    K -->|stop| M["log the rest<br/>and HALT implementation"]
    K -->|continue| N["log everything<br/>even beyond the workday"]
    P["read-back<br/>Jira → tasks.md with confirmation"] -.-> G
```

## 4c · Jira (opt-in) — the Phase 3 event cycle (who fires what)

The 7 events are generated by `skills/jira-sync/scripts/jira-flow.py` (deterministic `ops`: label →
transition → signed comment → worklog); the agent only **executes** them through the connector. Each
event has a fixed `--actor`: a mismatch is exit 2. Operational detail lives in the "Ciclo Jira de la
Fase 3" table of `commands/dev-cycle.md` (single source).

| Event | Who fires it | Issue transition | Comment (label) |
|---|---|---|---|
| `arrancar` | `implementer` | → *In Progress* (`en-curso`) | — |
| `implementado` | `implementer` | — (stays In Progress) | `ca-implementer` |
| `revision` (attempt with no gaps) | `reviewer` | — | `ca-reviewer` |
| `gaps` (attempt with gaps) | `reviewer` | → *In Progress* (`reabrir`) | `ca-reviewer` |
| `qa-verde` / `qa-rojo` | `qa` | — | `ca-qa` |
| `aprobado` | **the orchestrator** (`/dev-cycle`) | → *Done* (`done`) | `ca-orquestador` |

```mermaid
flowchart LR
    A["arrancar<br/>implementer"] --> B["implementado<br/>implementer"]
    B --> C{"two-lens<br/>review"}
    C -->|no gaps| D["revision<br/>reviewer"]
    C -->|gaps| E["gaps<br/>reviewer<br/>REOPENS the issue"]
    E -->|brief with gaps| B
    D --> F{"qa-gate.py"}
    F -->|red| G["qa-rojo<br/>qa"]
    G --> B
    F -->|green| H["qa-verde<br/>qa"]
    H --> I["aprobado<br/>ORCHESTRATOR<br/>needs evidence + --qa-verde"]
    I --> J[("issue → Done")]
```

> **Done is a gate, not a side effect.** `aprobado` is the ONLY event that moves the issue to *Done*,
> only the orchestrator fires it, and `jira-flow.py` rejects it (exit 2, `ops: []`) when the ledger
> has no latest review section free of pending gaps, or when `--qa-verde` (the exit 0 of
> `qa-gate.py`) is missing. With `.claude/jira.json` `enabled` ≠ `true` the whole cycle returns
> `ops: []` with no noise, and every published event is recorded (`flow` in `jira-state.json`) so it
> is not repeated.

## 5 · Confluence — bidirectional (opt-in)

```mermaid
flowchart LR
    A["local docs/: written by the agents<br/>evaluator · planner · qa · documenter"] -->|hook marks pending| C["confluence-publish<br/>hash+pageId manifest<br/>create/update without duplicating"]
    B["dashboard.md<br/>regenerated if the roadmap changes"] --> C
    C --> D[("🌐 Confluence<br/>page tree")]
    D -->|"confluence-pull · PM without git"| E["local docs/ up to date<br/>preserves frontmatter<br/>warns about conflicts"]
    D -.->|deletion not allowed| F["obsolete page<br/>→ manual deletion"]
```

> **Publication policy (2026-08-20-confluence-policy):** opt-out over `include: ["**/*.md"]` — a
> new document is published by default unless it falls under a known exclusion. Full normative
> detail and exclusion table: `skills/confluence-publish/SKILL.md`, "qué sube y qué no" (what
> ships and what doesn't) section.

**Trigger → artifact → does it publish? matrix** (the 11 known triggers that apply, or explicitly
declare they do not apply, the `agent-kits/shared/confluence-optin.md` step):

| Trigger | Artifact(s) it produces | Does it publish? |
|---|---|---|
| `analyst` | `spec.md` | ✅ Yes |
| `evaluator` | `evaluation.md` (+ `spec.md` if it creates it) | ✅ Yes |
| `architect` | `design.md` (+ ADR in `docs/knowledge/adr/`) | ✅ Yes — an architecture decision, like `spec.md` and the ADRs (not an execution board) |
| `planner` | `improvement-plan.md`, `tasks.md` | ❌ No — plan and ledger (D1): they live in the repo and in Jira, not in Confluence |
| `implementer` | updates `tasks.md` per task; triggers the sync **when closing each phase** (D3) | ⚠️ The trigger DOES fire, but `tasks.md` itself does **not** get published (D1) — it refreshes whatever else changed under `docs/` (typically `dashboard.md`) |
| `qa` | `testing/report.md` + `report.pdf`, `screenshots/`, `raw/` | ❌ No — `**/testing/**` (D4): the report embeds screenshots the connector cannot attach; stays local-only |
| `documenter` | reference documentation under `docs/` (architecture, stack, guides, product…) | ✅ Yes |
| `/pm-backlog` | `docs/roadmap/BACKLOG.md` | ✅ Yes |
| `/retro` | `retro.md` + `docs/roadmap/CALIBRATION.md` | ✅ Yes |
| `/spec-drift` | `docs/roadmap/DRIFT.md` | ✅ Yes |
| `/roadmap-brief` | `docs/roadmap/brief.md` + `brief.pdf` | ⚠️ The `.md` does; the `.pdf` is not part of the mirror (it is not `.md`) |

**Structural "no"s** (not tied to a specific trigger — policy exclusions that always apply,
whoever writes them): `docs/en/**` (duplicated EN tree, for GitHub readers), `docs/examples/**`
and `docs/agents/**` (the plugin's own internal documentation, not the consumer project's
product), `docs/**/atlassian-connector-notes.md` and, as always, `docs/security-scan/**`
(non-negotiable `nemesis` invariant). Verifiable with `confluence-scope.py --status` / `--check`
(`skills/confluence-publish/scripts/`).

**Where `docs/knowledge/` is born** (project technical memory, `2026-08-20-knowledge-capture`) —
**it IS in the mirror by default**, it is not in `exclude` (unlike the plan/ledger in the
`planner` row above): `planner`/`implementer` write an ADR under `docs/knowledge/adr/` when a
design decision crosses the threshold (see CONVENTIONS.md rule 10); `debug-root-cause` writes a
gotcha to a new file under `docs/knowledge/gotchas/GOT-NNN-<slug>.md` when it closes its Phase 4
(root cause confirmed); `qa` writes a gotcha when a justified flaky turns out to be a pattern, not
an accident; `/retro` produces a second output with process lessons in a new file under
`docs/knowledge/lessons/LES-NNN-<agent>-<slug>.md`, in addition to its
numeric row in `CALIBRATION.md`. The five reader agents (`evaluator`, `planner`, `implementer`,
`qa`, `documenter`) apply `agent-kits/shared/knowledge-check.md` before working (progressive
disclosure: only the index + their area). The **session journal** (`docs/knowledge/journal/`, a log
generated by the `SessionEnd` hook) is episodic, uncurated memory: `evaluator`/`planner`/`architect`
read only their initiative's latest entry, `/retro` uses it as a source of deviation causes, and
whatever deserves doctrine is promoted to an ADR/gotcha/lesson. Full detail: `CONVENTIONS.md` rule 10.

## 6 · Visibility and learning (all read-only)

> **Generation cost (usage-meter):** each artifact of the cycle (and each task in Mode B) is **measured** with real tokens from the transcript (`agent-kits/shared/usage-meter.py`); the `generacion:` block in its frontmatter feeds the **process cost** section of `/roadmap-metrics`, and `/retro` uses it to calibrate the **tokens→hour ratio** used by the evaluator and by the meter itself. Dates = context · tokens = measurement · hours = derived.

```mermaid
flowchart TD
    M["usage-meter.py<br/>start/close per artifact and task<br/>(real tokens from the transcript)"] -->|generacion: block| R
    R[("docs/roadmap/*/<br/>spec · evaluation · plan · tasks")] --> S["/roadmap-status<br/>HTML + md dashboard"]
    R --> T["/pm-backlog<br/>prioritizes the portfolio<br/>BACKLOG.md"]
    R --> U["/roadmap-metrics<br/>actual vs estimated<br/>+ process cost<br/>metrics.md"]
    S --> V["/roadmap-brief<br/>one-pager PDF<br/>for management"]
    T --> V
    U --> V
    J[("Jira<br/>issues + worklogs")] --> W["/roadmap-live<br/>real-time status"]
    U --> X["/retro per initiative<br/>causes of deviation<br/>+ measured tokens/hour ratio"]
    R --> DR["/spec-drift<br/>spec↔code drift<br/>current ✓ · drifted ✗ · not verifiable<br/>→ DRIFT.md"]
    DR -.->|"drift → /pm-cycle"| R
    X --> Y[("CALIBRATION.md")]
    Y -->|calibrates estimates<br/>and tokens→hour ratio| Z["evaluator"]
    Y -.->|ratio| M
```

## 6b · Live visibility (deterministic hooks + opt-in status line)

> While `implementer`/subagents work, the user sees progress without anyone writing it up:
> everything comes from `progress-report.py` over the **canonical ledger** (`tasks.md`). Hooks
> **inform, they never decide** (always exit 0). Details: [`observability.md`](observability.md).
> **Session journal** (memory-health): when the session ends, `SessionEnd` leaves a deterministic
> entry under `docs/knowledge/journal/` (active initiative, files touched, tasks whose state changed,
> meter markers); on startup/resume, `SessionStart` re-injects it compacted. No AI summary: hook output
> on `SessionEnd` is ignored by contract (ADR-010).

```mermaid
flowchart LR
    L[("docs/roadmap/*/tasks.md<br/>canonical ledger")] -->|Write/Edit| H1["PostToolUse hook<br/>progress-line.sh"]
    H1 -->|"systemMessage (debounced)"| U(["👀 user<br/>📋 slug · T-04/12 (33%) · fase 2/4 · en curso T-05"])
    SA["subagent finishes"] --> H2["SubagentStop hook<br/>subagent-progress.sh"]
    H2 -->|"systemMessage: active initiatives"| U
    SS["session: startup · resume · compact"] --> H3["SessionStart hook<br/>session-context.sh"]
    H3 -->|"additionalContext: piece index (≤ 45 lines, hash-cached)<br/>+ resume ≤ 15 lines (in-progress task)<br/>+ journal ≤ 25 lines (startup · resume only)"| C(["🧠 Claude's context"])
    SE["session ends: exit · /clear · logout"] --> H4["SessionEnd hook<br/>session-journal.sh (timeout 20)"]
    H4 -->|"journal.py write (idempotent by session_id)"| J[("docs/knowledge/journal/<br/>YYYY-MM-DD-slug.md")]
    J -->|"journal.py latest --n 2"| H3
    FM[("frontmatters<br/>commands · skills · agents")] --> SI["skill-index.py<br/>(dev.json sesion.indice)"]
    SI --> H3
    L --> P["progress-report.py<br/>line · active · session · --json"]
    P --> H1 & H2 & H3
    P -.->|"active --json"| SL["statusline/roadmap-statusline.sh<br/>(opt-in in /setup 5-bis)"]
    SL -.->|"[Opus] $0.01 ctx 8% · 📋 slug T-04/12 33%"| U
```

## 6c · Deterministic guardrails of the `implementer` (agent-scoped guard hook)

> The implementer's hard rules no longer depend on the model remembering them: a `PreToolUse`
> hook registered **only in its frontmatter** (`agents/implementer.md`) enforces them through
> `guardrail-check.py` (a script with tests). Other agents do not carry it: `planner`/`evaluator`
> legitimately write to `docs/roadmap/` (ADR-007). Can be switched off in `.claude/dev.json`.

```mermaid
flowchart LR
    T["implementer attempts<br/>Write · Edit · MultiEdit · NotebookEdit · Bash"] --> W["PreToolUse hook<br/>implementer-guardrail.sh"]
    W -->|"no python3"| M(["systemMessage (once)<br/>+ exit 0: never blocks"])
    W --> G["guardrail-check.py pre-tool<br/>(dev.json → guardrails)"]
    G -->|"docs/roadmap/** ≠ tasks.md<br/>docs/security-scan/**"| D(["❌ deny + reason:<br/>«only tasks.md; planner changes the plan»"])
    G -->|"HEAD on main/master<br/>+ write outside the ledger"| D2(["❌ deny: «work on feature/<slug>»"])
    G -->|"git push --force · branch -D<br/>checkout main from a feature<br/>rm -rf / ~ .git"| D3(["❌ deny + how to proceed"])
    G -->|"everything else"| A(["✅ no output, exit 0<br/>(normal permission flow)"])
    D & D2 & D3 -.->|"read the reason, switch file/branch"| T
```

## 7 · Configuration (one pass with `/setup`)

```mermaid
flowchart LR
    A["/setup"] --> B[".claude/rates.json<br/>rate · tokens · workday · ratios<br/>read by evaluator, planner and jira-sync"]
    A --> C[".claude/confluence.json<br/>opt-in + destination"]
    A --> D[".claude/jira.json<br/>opt-in + workday policy"]
    A --> G[".claude/dev.json<br/>tdd · worktree · subagents · statusline<br/>revision.lenteSeguridad/lenteRendimiento ·<br/>tests.coberturaMinima<br/>(+ constitution decision)"]
    A -.->|"opt-in 5-bis"| SL[".claude/settings.json<br/>statusLine → roadmap-statusline.sh<br/>(absolute path)"]
    A --> H["docs/CONSTITUTION.md<br/>permanent principles (opt-in)<br/>read by ALL agents;<br/>lens A enforces them"]
    C -.->|state| E[".claude/confluence-state.json"]
    D -.->|state| F[".claude/jira-state.json<br/>mapping · logged/day · bank"]
```

> **Checking the installation:** `/doctor` reads all of this (plus hooks, status line and work state) without
> writing anything and gives a ✅/⚠️/❌ verdict per line with the fix next to it. It is the first stop when a hook
> "does not fire" or a skill does not activate; `/setup` offers it when `.claude/` already has config.

Details on each file: rule 9 of [`CONVENTIONS.md`](CONVENTIONS.md). Atlassian connector
behaviors: [`atlassian-connector-notes.md` (Spanish)](../atlassian-connector-notes.md).

> **Note (Confluence):** if this page is published to Confluence via `confluence-publish`, the
> Mermaid diagrams only render if the space has a Mermaid app/macro installed; otherwise
> the diagram's source code will be shown. On GitHub and in compatible editors they always render.

> **Maintenance:** when adding or changing an agent, command or skill, update the corresponding
> diagram in this document (see the checklist in `CONVENTIONS.md`).
