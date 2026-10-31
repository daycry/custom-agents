> Advanced reference. Start with the [plain-language handbook](../CUSTOMIZATION.md). This chapter preserves implementation contracts and configuration details.

# 2. Detailed core workflows

Skills listed below are selected when relevant, not all preloaded. Agent invocation
uses the runtime's actual native IDs. Each workflow retains local artifact ownership.

## W-01. Set up a project

**Trigger:** a team starts using the product in a repository. **Commands:** `/setup`
and `/doctor`. **Actor:** the command's current thread; no extra onboarding agent.
**Skills:** `rates-verify` and `unit-tests` when selected. **Tools:** local file access,
plus official pricing reads when requested.

| Step | Actor/action | Input | Output/gate |
|---|---|---|---|
| 1 | Orchestrator identifies root, runtime and installation | Explicit project | Correct scope, without cross-project settings |
| 2 | Doctor reviews existing setup | Bundle and project config | Read-only diagnostic and fixes |
| 3 | User confirms financial parameters | Rate, working day, supervision | `rates.json`, with unverified prices labeled |
| 4 | User chooses external functions or none | Tracking/documentation/other | `integrations.json` bindings or empty list |
| 5 | Adapter defines preferences | Destination, granularity, permission, states | Provider settings; credentials outside Git |
| 6 | User chooses discipline and principles | TDD, worktrees, delegation, constitution | `dev.json` and optional constitution |
| 7 | Orchestrator presents observability/model options | Setup/runtime options | Only accepted changes |
| 8 | Router and doctor validate configuration | Written declarations | Valid config; connectivity remains separately unverified |

Example: “Configure local work, TDD and coverage; do not connect external services yet.”
This does not create accounts, issues, pages or MCP servers. Invalid existing settings
are reviewed, not discarded to restart onboarding.

## W-02. Turn an idea into a product decision

**Command:** `/pm-cycle <objective>`. **Agents:** optional analyst, evaluator, optional
architect after go. **Skills:** research-first for alternatives, code-health for debt
evidence, rates-verify as needed, stack/memory context on demand. **Tools:** repository
reads, estimation/meter scripts, document writes and official research when relevant.

| Step | Owner | Work/artifact | Decision/handoff |
|---|---|---|---|
| 1 | Orchestrator | Reuse/create initiative folder | Avoid duplicate initiatives |
| 2 | Analyst if ambiguous | Clarify users, permissions, scope, exclusions, acceptance | Verifiable spec reviewed with user |
| 3 | Evaluator | Inspect code and estimate effort, cost, tokens, complexity, risks | Evaluation in review, estimates labeled |
| 4 | User | Go, revise or no-go | Approved spec/completed evaluation, iteration or traced cancellation |
| 5 | Architect if requested | Compare options; user chooses | Approved design and linked decision |
| 6 | Orchestrator | Summarize and offer dev-cycle on the same folder | PM cycle ends without automatic implementation |

For request approval, clarify who may approve, repeat decisions, audit retention and
rejection validation. A vague “approval screen” is not sufficient acceptance.
An external container is optional and needs a compatible `plan.container` adapter;
this stage does not bulk-create development tasks. Documentation projection does
not replace go/no-go.

## W-03. Select capabilities and plan

**Commands:** `/work-context` and `/dev-cycle <initiative>`. **Agent:** planner, using
the chosen design. **Skills:** relevant stack-practices, backend-practices,
frontend-quality, delivery-practices, api-contract, dependency-upgrade, research-first;
roadmap-dashboard for portfolio data. **Tools:** manifests, inventory and ledger scripts.

| Step | Component | Work | Output/check |
|---|---|---|---|
| 1 | Shared context | Inspect manifests, versions and task area | Applicable capability IDs and provenance |
| 2 | Project-pieces | Inventory declared agents, skills, personas, tools, MCP | Extension references, not availability proof |
| 3 | Planner | Split acceptance into phases/tasks | Plan and canonical ledger in the initiative folder |
| 4 | Planner | Set description, type, files, criteria and verification | Concrete testable scope and labeled estimates |
| 5 | Planner | Record selected capability/extension IDs and scenarios | Shared contract for implementation, review and QA |
| 6 | Ledger scripts | Validate structure | Ledger-lint without errors |
| 7 | User/orchestrator | Review the execution plan | Approved scope/dependencies |
| 8 | Optional adapter | Handle plan.created/plan.export | Preview of remote task/phase objects before authorized creation |

The example can split foundation, experience and verification phases. Every task keeps
its acceptance even if the remote board has only one card per phase.

## W-04. Implement, review and verify a task

**Command:** dev-cycle. **Agents:** implementer, independent reviewers and QA.
**Skills:** selected stack methods, TDD when enabled, adversarial-review, unit-tests,
debug-root-cause when needed. **Tools:** editor, shell, official test runner, ledger,
meter/gate scripts and Playwright where UI E2E applies.

| Step | Owner | Action | Evidence/optional event |
|---|---|---|---|
| 1 | Orchestrator | Select task and bounded brief; apply normal/lite and delegation choices | Scope, persona, capabilities and extensions |
| 2 | Implementer | Set in-progress and start measurement | Ledger; task.started |
| 3 | Implementer/TDD | Observe a real failing test before code when applicable | Case, failure and date; fixture errors do not count |
| 4 | Implementer | Implement and run declared verification | Observed command/result, files and measurement; task.implemented |
| 5 | Review skill | Scope gate and lens selection | A conformance, B defects, conditional C security/D performance |
| 6 | Fresh reviewers | Inspect and report concrete evidence/scenarios | Graded findings; no edits to reviewed code |
| 7 | Review skill | Arbitrate findings/rebuttals and record attempt | Per-criterion verdict; review.completed or review.gaps |
| 8 | Implementer | Fix validated findings with dedicated regressions | New reviewable patch; no blind fixes/dismissals |
| 9 | QA | Execute applicable official checks | Testing artifacts, counts, applicable captures and qa-gate result |
| 10 | QA | Return actual verdict | task.qa-passed/failed; no independent remote Done |
| 11 | Orchestrator | Require review without gaps and green QA | Final closure permitted; task.done with evidence |

Implementation completion is not delivery acceptance. The orchestrator checks both
verdicts before projecting Done, without inventing ledger states to match board columns.

Correction is bounded. After three red QA attempts, run one root-cause pass with
reproduction, isolation, tested hypothesis and proposal, then decide whether to continue,
replan or cancel. Never lower coverage or falsify a gate to close.

External failure preserves local results and reports pending projection. Reconcile an
uncertain write before retrying. Board trouble does not change QA or require repeating
already valid checks without a reason.

## W-05. Close a phase and deliver

**Entry:** phase criteria and gates satisfied. **Command:** dev-cycle closure and retro.
**Agents:** implementer, documenter and knowledge-curator for actual candidates.
**Skills:** changelog-sync, roadmap-dashboard, opted-in knowledge-services and optional
to-pdf when requested/available. **Tools:** ledger checks, documentation and approved Git flow.

| Step | Owner | Work | Output/gate |
|---|---|---|---|
| 1 | Implementer/orchestrator | Verify phase and progress | Coherent ledger, no hidden unfinished task |
| 2 | Implementer | Emit phase.completed | Publishable documents once per revision |
| 3 | Documenter | Update owning documentation and indexes | Examples match the product |
| 4 | Changelog-sync | Generate user-facing notes from closed tasks | No invented release scope/version |
| 5 | Producers/curator | Propose/judge knowledge with evidence | Candidates remain distinct from approved |
| 6 | Orchestrator | Check branch, own diff and tests | Commits/PR under the approved repository flow |
| 7 | User/CI | Required delivery review/checks | Push is not CI green or deployment |
| 8 | Retro | Compare estimate/actual and lessons | Retro/calibration; absent measurements explicit |
| 9 | Orchestrator | Close only after the ritual | Completed plan/implemented spec under their contracts |

Release/deployment has its own authorization and workflow. A PDF request or task closure
does not authorize a release. Publishing docs does not implicitly attach every PDF.

## W-06. Make a small, defined change

**Entry:** quick-implement or dev-cycle quick path. **Agents:** implementer, review and
QA; documenter when needed. **Skills/tools:** the same implementation/quality checks as
W-04, retaining the selected TDD policy.

The orchestrator creates a lightweight ledger with one phase, minimal tasks, acceptance
and verification. It skips extensive PM paperwork, not review or QA. The same evidence
and optional events apply. Ambiguous or structurally complex work returns to the normal
cycle rather than using the quick path to avoid required tests.

## W-07. Portfolio, drift and resumption

| Command | Owner/skill | Inputs/output | Limit |
|---|---|---|---|
| pm-backlog | PM role, roadmap-dashboard | Evaluations and portfolio priority | Does not silently implement/cancel |
| roadmap-status | Roadmap-dashboard; optional plugin-panel | Local ledgers, summary/panel | Snapshot, not live process evidence |
| roadmap-brief | Roadmap-dashboard; optional PDF | Executive summary/budget | Source/date shown; no fabricated metrics |
| roadmap-metrics | Roadmap-dashboard | Estimate versus actual | Wall time is not measured AI effort |
| roadmap-live | Tracking adapter, task.read | Remote state at query time | No ledger mutation or constant polling claim |
| spec-drift | Comparison command | Spec, plan, code, evidence | Reports drift, does not silently rewrite approved scope |
| work-resume | Progress/history compositor | Current ledger, reviews, selected session | History does not override current state |
| plugin-catalog | Optional plugin-panel/catalog module | Bundle/extensions, conflicts/provenance | Declared is not loaded or connected |

Supply the initiative folder or slug when resuming. Recover the current ledger and
associated decisions, identify unfinished work and continue there. Historical “continue”
messages do not reactivate cancelled initiatives or create a duplicate plan.
