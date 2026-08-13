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
    TODOS(["👀 Anyone"]) --> V2["/roadmap-status<br/>dashboard"]
    TODOS --> V3["/roadmap-metrics<br/>actual vs estimated"]
    TODOS --> V4["/roadmap-live<br/>live Jira"]
    P1 -->|go| D1
    D1 --> V3
    D2 -.->|CALIBRATION.md| P1
```

## 1 · The complete chain of an initiative

**Product** phase: `analyst → evaluator`. **Development** phase: `planner → implementer → qa`.

```mermaid
flowchart LR
    idea(["💡 Idea / request"]) --> analyst["🗣️ analyst<br/>requirements gathering"]
    analyst -->|spec aprobada| evaluator["💶 evaluator<br/>budgets"]
    evaluator -->|go| planner["🗺️ planner<br/>plan + tasks"]
    evaluator -.->|no-go| fin1(["✋ discarded"])
    planner --> implementer["⚙️ implementer<br/>code + ledger"]
    implementer --> review["🔍 adversarial review<br/>(2 lenses in parallel,<br/>fresh context) diff vs plan"]
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
(`spec.md → evaluation.md → improvement-plan.md + tasks.md → testing/ → retro.md`).

## 2 · `/pm-cycle` — product role (defines and budgets, closes at the gate)

```mermaid
flowchart TD
    A["/pm-cycle objective"] --> B{"objective<br/>well defined?"}
    B -->|no| C["discovery skill / @analyst<br/>interview → spec.md"]
    B -->|yes| D["evaluator<br/>spec + evaluation.md"]
    C --> D
    D --> E{"gate<br/>go / no-go"}
    E -->|no-go| F["evaluation → cancelado<br/>spec → obsoleta"]
    E -->|needs revision| C
    E -->|go| G["spec → aprobada<br/>evaluation → completado"]
    G --> H["opt-in outputs:<br/>📄 brief PDF · 🎫 epic in Jira"]
    H --> I(["offers handoff to /dev-cycle<br/>without running it"])
    style F fill:#fdecea,stroke:#ef9a9a
    style G fill:#e8f5e9,stroke:#81c784
    style I fill:#e8f5e9,stroke:#81c784
```

## 3 · `/dev-cycle` — development cycle (with gates)

> **Entry gate (Phase 0-bis):** `/dev-cycle` first asks **full flow** vs **fast track**. The fast track skips evaluator+planner (creates a lightweight `tasks.md`) and goes straight into implementation, but keeps the two-lens review + qa.
>
> **Two entry points into the same gate:** the `/dev-cycle` command (explicit, with the slash) and the `quick-implement` skill, which auto-invokes from natural language ("implement X quickly") and enters through the fast-track branch after its suitability filter. The skill defines no method of its own: it delegates to this very Phase 0-bis.

```mermaid
flowchart TD
    NL(["natural-language request<br/>\"implement X quickly\""]) -.->|"quick-implement skill<br/>(suitability filter)"| Z
    A["/dev-cycle objective"] --> Z{"full flow<br/>or fast track?"}
    Z -->|fast track| Q["lightweight tasks.md<br/>(no spec/eval/plan)"]
    Q --> H
    Z -->|full| B{"folder with<br/>spec+evaluation<br/>from /pm-cycle?"}
    B -->|yes| D
    B -->|no| C["evaluator → go/no-go gate"]
    C -->|go| D["planner<br/>improvement-plan + tasks.md"]
    C -->|no-go| X(["stop"])
    D --> E["opt-in: push plan to Jira<br/>jira-sync: 1 issue per task"]
    E --> F{"did the user ask for<br/>an external engine<br/>explicitly?"}
    F -->|"yes (explicit opt-in)"| G["external engine executes<br/>against YOUR tasks.md<br/>(its own review)"]
    F -->|"no (default):<br/>NATIVE chain"| H["implementer<br/>task by task<br/>(dev.json opt-in: TDD ·<br/>worktree · fresh subagents)"]
    H --> R["🔍 adversarial review<br/>TWO lenses in parallel:<br/>spec conformance · quality<br/>(merge + dedupe)"]
    R -.->|gaps| H
    G --> I["qa · local E2E<br/>verdict: qa-gate.py"]
    R --> I
    I -->|"red (max 3 attempts,<br/>then ask)"| H
    I -->|green| J["documenter<br/>once at the end"]
    J --> K["optional: nemesis<br/>audit"]
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

```mermaid
flowchart TD
    G["task completado<br/>in tasks.md"] --> H["worklog.py plan<br/>AI + supervision, actual→est"]
    H --> I{"does it fit in<br/>today's workday?"}
    I -->|yes| J["log worklog<br/>+ issue → Done"]
    I -->|no| K{"policy"}
    K -->|bank| L["log the rest of today<br/>excess → bank per issue<br/>paid off on following days"]
    K -->|stop| M["log the rest<br/>and HALT implementation"]
    K -->|continue| N["log everything<br/>even beyond the workday"]
    P["read-back<br/>Jira → tasks.md with confirmation"] -.-> G
```

## 5 · Confluence — bidirectional (opt-in)

```mermaid
flowchart LR
    A["local docs/: written by the agents<br/>evaluator · planner · qa · documenter"] -->|hook marks pending| C["confluence-publish<br/>hash+pageId manifest<br/>create/update without duplicating"]
    B["dashboard.md<br/>regenerated if the roadmap changes"] --> C
    C --> D[("🌐 Confluence<br/>page tree")]
    D -->|"confluence-pull · PM without git"| E["local docs/ up to date<br/>preserves frontmatter<br/>warns about conflicts"]
    D -.->|deletion not allowed| F["obsolete page<br/>→ manual deletion"]
```

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

## 7 · Configuration (one pass with `/setup`)

```mermaid
flowchart LR
    A["/setup"] --> B[".claude/rates.json<br/>rate · tokens · workday · ratios<br/>read by evaluator, planner and jira-sync"]
    A --> C[".claude/confluence.json<br/>opt-in + destination"]
    A --> D[".claude/jira.json<br/>opt-in + workday policy"]
    A --> G[".claude/dev.json<br/>tdd · worktree · subagents<br/>(+ constitution decision)"]
    A --> H["docs/CONSTITUTION.md<br/>permanent principles (opt-in)<br/>read by ALL agents;<br/>lens A enforces them"]
    C -.->|state| E[".claude/confluence-state.json"]
    D -.->|state| F[".claude/jira-state.json<br/>mapping · logged/day · bank"]
```

Details on each file: rule 9 of [`CONVENTIONS.md`](CONVENTIONS.md). Atlassian connector
behaviors: [`atlassian-connector-notes.md` (Spanish)](../atlassian-connector-notes.md).

> **Note (Confluence):** if this page is published to Confluence via `confluence-publish`, the
> Mermaid diagrams only render if the space has a Mermaid app/macro installed; otherwise
> the diagram's source code will be shown. On GitHub and in compatible editors they always render.

> **Maintenance:** when adding or changing an agent, command or skill, update the corresponding
> diagram in this document (see the checklist in `CONVENTIONS.md`).
