# Plugin flows — diagrams

**English** · [Español](../FLOWS.md)

Visual overview of how agents, commands and skills fit together. The diagrams are Mermaid
(they render on GitHub and in compatible editors).

**Legend:** **solid** arrow = main flow · **dotted** arrow = optional, return or feedback · diamond = decision/gate · green = forward path (*go*/green) · red = rejection or step back (*no-go*/red).

## 0 · General map — who uses what

```mermaid
flowchart TD
    PM(["👤 PM / product"]) --> S0["/setup"]
    PM --> P1["/pm-cycle\ndefines and budgets"]
    PM --> P2["/pm-backlog\nprioritizes portfolio"]
    PM --> P3["/confluence-pull\ndocs without git"]
    DEV(["👩‍💻 Dev / team"]) --> D1["/dev-cycle\nbuilds"]
    DEV --> D2["/retro\nlearns"]
    DIR(["👔 Management"]) --> V1["/roadmap-brief\none-pager PDF"]
    TODOS(["👀 Anyone"]) --> V2["/roadmap-status\ndashboard"]
    TODOS --> V3["/roadmap-metrics\nactual vs estimated"]
    TODOS --> V4["/roadmap-live\nlive Jira"]
    P1 -->|go| D1
    D1 --> V3
    D2 -.->|CALIBRATION.md| P1
```

## 1 · The complete chain of an initiative

**Product** phase: `analyst → evaluator`. **Development** phase: `planner → implementer → qa`.

```mermaid
flowchart LR
    idea(["💡 Idea / request"]) --> analyst["🗣️ analyst\nrequirements gathering"]
    analyst -->|spec aprobada| evaluator["💶 evaluator\nbudgets"]
    evaluator -->|go| planner["🗺️ planner\nplan + tasks"]
    evaluator -.->|no-go| fin1(["✋ discarded"])
    planner --> implementer["⚙️ implementer\ncode + ledger"]
    implementer --> review["🔍 adversarial review\n(2 lenses in parallel,\nfresh context) diff vs plan"]
    review -->|no gaps| qa["✅ qa\nE2E Playwright"]
    review -.->|correctness gaps| implementer
    qa -->|green| documenter["📚 documenter\nproject docs"]
    qa -.->|red| implementer
    documenter --> retro["🔁 /retro\ncalibration"]
    nemesis["🛡️ nemesis\naudit"] -.->|critical findings| analyst
    retro -.->|CALIBRATION.md| evaluator
    style fin1 fill:#fdecea,stroke:#ef9a9a
    style documenter fill:#e8f5e9,stroke:#81c784
```

Everything lives in **one folder per initiative**: `docs/roadmap/<fecha>-<slug>/`
(`spec.md → evaluation.md → improvement-plan.md + tasks.md → testing/ → retro.md`).

## 2 · `/pm-cycle` — product role (defines and budgets, closes at the gate)

```mermaid
flowchart TD
    A["/pm-cycle objective"] --> B{"objective\nwell defined?"}
    B -->|no| C["discovery skill / @analyst\ninterview → spec.md"]
    B -->|yes| D["evaluator\nspec + evaluation.md"]
    C --> D
    D --> E{"gate\ngo / no-go"}
    E -->|no-go| F["evaluation → cancelado\nspec → obsoleta"]
    E -->|needs revision| C
    E -->|go| G["spec → aprobada\nevaluation → completado"]
    G --> H["opt-in outputs:\n📄 brief PDF · 🎫 epic in Jira"]
    H --> I(["offers handoff to /dev-cycle\nwithout running it"])
    style F fill:#fdecea,stroke:#ef9a9a
    style G fill:#e8f5e9,stroke:#81c784
    style I fill:#e8f5e9,stroke:#81c784
```

## 3 · `/dev-cycle` — development cycle (with gates)

> **Entry gate (Phase 0-bis):** `/dev-cycle` first asks **full flow** vs **fast track**. The fast track skips evaluator+planner (creates a lightweight `tasks.md`) and goes straight into implementation, but keeps the two-lens review + qa.

```mermaid
flowchart TD
    A["/dev-cycle objective"] --> Z{"full flow\nor fast track?"}
    Z -->|fast track| Q["lightweight tasks.md\n(no spec/eval/plan)"]
    Q --> H
    Z -->|full| B{"folder with\nspec+evaluation\nfrom /pm-cycle?"}
    B -->|yes| D
    B -->|no| C["evaluator → go/no-go gate"]
    C -->|go| D["planner\nimprovement-plan + tasks.md"]
    C -->|no-go| X(["stop"])
    D --> E["opt-in: push plan to Jira\njira-sync: 1 issue per task"]
    E --> F{"did the user ask for\nsuperpowers\nexplicitly?"}
    F -->|"yes (--superpowers)"| G["superpowers executes\nagainst YOUR tasks.md\n(its own review)"]
    F -->|"no (default):\nNATIVE chain"| H["implementer\ntask by task\n(dev.json opt-in: TDD ·\nworktree · fresh subagents)"]
    H --> R["🔍 adversarial review\nTWO lenses in parallel:\nspec conformance · quality\n(merge + dedupe)"]
    R -.->|gaps| H
    G --> I["qa · local E2E\nverdict: qa-gate.py"]
    R --> I
    I -->|"red (max 3 attempts,\nthen ask)"| H
    I -->|green| J["documenter\nonce at the end"]
    J --> K["optional: nemesis\naudit"]
    K --> L(["closeout: plan completado\nspec implementada"])
    style X fill:#fdecea,stroke:#ef9a9a
    style L fill:#e8f5e9,stroke:#81c784
```

`tasks.md` is the **canonical ledger** of progress in both modes.

## 4 · Jira (opt-in) — pushing the plan when it is created

> **Granularity** (`.claude/jira.json` → `granularidad`): **task** = one issue per `T-XX` (default); **phase** = one issue per Phase with its tasks as a checklist. In phase mode, comments/worklog/Done go to the phase's issue; the issue closes when all its tasks are `completado`. Additionally, the **reviewer's result** (Mode B) is published as a comment (per criterion ✓/✗ + number of attempts) and its time is logged as a separate `[revisión]` worklog — at the chosen granularity.

```mermaid
flowchart TD
    A["destination selector\n+ task/phase granularity\nartifact or conversational"] --> B{"parent?"}
    B -->|new epic| C["create Epic\n+ Tasks below it"]
    B -->|existing issue| D{"parent level\ndiscovered"}
    B -->|no parent| E["standalone Tasks\nin the project"]
    D -->|epic / initiative| C2["Tasks"]
    D -->|task / story| C3["Subtasks"]
    C --> F["dry-run + confirmation\n→ create issues\nkeys → tasks.md"]
    C2 --> F
    C3 --> F
    E --> F
    O["/roadmap-live\nlive status by label"] -.->|reads| F
```

## 4b · Jira (opt-in) — time logging when each task is completed

```mermaid
flowchart TD
    G["task completado\nin tasks.md"] --> H["worklog.py plan\nAI + supervision, actual→est"]
    H --> I{"does it fit in\ntoday's workday?"}
    I -->|yes| J["log worklog\n+ issue → Done"]
    I -->|no| K{"policy"}
    K -->|bank| L["log the rest of today\nexcess → bank per issue\npaid off on following days"]
    K -->|stop| M["log the rest\nand HALT implementation"]
    K -->|continue| N["log everything\neven beyond the workday"]
    P["read-back\nJira → tasks.md with confirmation"] -.-> G
```

## 5 · Confluence — bidirectional (opt-in)

```mermaid
flowchart LR
    A["local docs/: written by the agents\nevaluator · planner · qa · documenter"] -->|hook marks pending| C["confluence-publish\nhash+pageId manifest\ncreate/update without duplicating"]
    B["dashboard.md\nregenerated if the roadmap changes"] --> C
    C --> D[("🌐 Confluence\npage tree")]
    D -->|"confluence-pull · PM without git"| E["local docs/ up to date\npreserves frontmatter\nwarns about conflicts"]
    D -.->|deletion not allowed| F["obsolete page\n→ manual deletion"]
```

## 6 · Visibility and learning (all read-only)

> **Generation cost (usage-meter):** each artifact of the cycle (and each task in Mode B) is **measured** with real tokens from the transcript (`agent-kits/shared/usage-meter.py`); the `generacion:` block in its frontmatter feeds the **process cost** section of `/roadmap-metrics`, and `/retro` uses it to calibrate the **tokens→hour ratio** used by the evaluator and by the meter itself. Dates = context · tokens = measurement · hours = derived.

```mermaid
flowchart TD
    M["usage-meter.py\nstart/close per artifact and task\n(real tokens from the transcript)"] -->|generacion: block| R
    R[("docs/roadmap/*/\nspec · evaluation · plan · tasks")] --> S["/roadmap-status\nHTML + md dashboard"]
    R --> T["/pm-backlog\nprioritizes the portfolio\nBACKLOG.md"]
    R --> U["/roadmap-metrics\nactual vs estimated\n+ process cost\nmetrics.md"]
    S --> V["/roadmap-brief\none-pager PDF\nfor management"]
    T --> V
    U --> V
    J[("Jira\nissues + worklogs")] --> W["/roadmap-live\nreal-time status"]
    U --> X["/retro per initiative\ncauses of deviation\n+ measured tokens/hour ratio"]
    R --> DR["/spec-drift\nspec↔code drift\ncurrent ✓ · drifted ✗ · not verifiable\n→ DRIFT.md"]
    DR -.->|"drift → /pm-cycle"| R
    X --> Y[("CALIBRATION.md")]
    Y -->|calibrates estimates\nand tokens→hour ratio| Z["evaluator"]
    Y -.->|ratio| M
```

## 7 · Configuration (one pass with `/setup`)

```mermaid
flowchart LR
    A["/setup"] --> B[".claude/rates.json\nrate · tokens · workday · ratios\nread by evaluator, planner and jira-sync"]
    A --> C[".claude/confluence.json\nopt-in + destination"]
    A --> D[".claude/jira.json\nopt-in + workday policy"]
    A --> G[".claude/dev.json\ntdd · worktree · subagents\n(+ constitution decision)"]
    A --> H["docs/CONSTITUTION.md\npermanent principles (opt-in)\nread by ALL agents;\nlens A enforces them"]
    C -.->|state| E[".claude/confluence-state.json"]
    D -.->|state| F[".claude/jira-state.json\nmapping · logged/day · bank"]
```

Details on each file: rule 9 of [`CONVENTIONS.md`](CONVENTIONS.md). Atlassian connector
behaviors: [`atlassian-connector-notes.md` (Spanish)](../atlassian-connector-notes.md).

> **Note (Confluence):** if this page is published to Confluence via `confluence-publish`, the
> Mermaid diagrams only render if the space has a Mermaid app/macro installed; otherwise
> the diagram's source code will be shown. On GitHub and in compatible editors they always render.

> **Maintenance:** when adding or changing an agent, command or skill, update the corresponding
> diagram in this document (see the checklist in `CONVENTIONS.md`).
