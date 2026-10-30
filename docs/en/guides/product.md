# 1. Product, modules and ownership

custom-agents organizes AI-assisted work from an idea to a verified delivery. It
separates requirements, estimates, design, planning, implementation, review and QA.
Decisions and evidence stay in the project. Jira, Redmine or another collaboration
tool can mirror the work without becoming a prerequisite or a test authority.

The running example is **request approval**: a lead can approve or reject a request,
with an actor audit trail and a rejection reason. Product defines acceptance criteria;
the team chooses the design and splits permissions, API, UI and regression work.
Remote identifiers in examples are fictional.

## Components

| Component | Responsibility | Does not establish |
|---|---|---|
| Command | User entry point coordinating a workflow | Native loading or availability |
| Agent | Role with an objective, tools and artifact ownership | Permission to alter another owner's artifact |
| Skill | Reusable method activated when relevant | A requirement to preload every skill |
| Tool/MCP | Operation exposed in the current runtime session | Permission for every destination |
| Persona | Domain criteria applied to a task | A human identity or another agent |

Short agent names are used here. Native IDs may be prefixed, such as
`custom-agents-planner`; use the generated runtime map and actual available roles.

## Modules and delivery

`agent-kits/shared/modules.json` is the versioned catalog. Core contains lifecycle
and quality methods. Jira, Confluence, specialist security, PDF, training, catalog
tools and content/application capabilities have separate modules.

| Profile | Initial modules | Intended use |
|---|---|---|
| `core` | Core | Local product/development lifecycle |
| `developer` | Core, specialist security, application/data | Teams needing those specialties |
| `research` | Core, content and its voice dependency | Research/content work |
| `full` | Every bundled module | Complete library loaded as needed |

A profile is not a provider list. Core plus Jira is valid; core plus a project Redmine
adapter is also valid. The bundle catalog lists shipped modules, not every permitted
external service. Dependency closure is deterministic.

Portable export filters skills and their resources, and does not ship the full agent,
command and hook lifecycle. Claude copy mode supports file profiles with explicit
limitations. Native plugin packages remain complete; shared caches are not rewritten
to pretend each project has a partial plugin. Session availability is checked separately.

## Owners

| Role | Owns | Boundary |
|---|---|---|
| User/process owner | Objective, approved scope and authorizations | Does not replace test execution |
| Analyst | Discovery and verifiable specification | Does not implement or plan |
| Evaluator | Estimates, complexity and risks | Does not approve the business decision |
| Architect | Options and chosen technical design | Does not silently choose for the user when approval is required |
| Planner | Plan, phases, tasks and acceptance criteria | Does not execute or verify the implementation |
| Implementer | Code and implementation checks | Does not provide independent review or final QA |
| Reviewer | Evidence-backed findings | Does not edit the code being reviewed |
| QA | Applicable tests and gate verdict | Does not independently close a remote issue |
| Documenter | Maintainable product documentation | Does not publish without authorization |
| Knowledge-curator | Judgment of knowledge candidates | Does not allow producers to approve their own candidates |
| Nemesis | Requested specialist audit when installed | Does not replace normal review or functional QA |
| Orchestrator | Sequence, handoffs and closure with all verdicts | Does not absorb specialist ownership |

The `adversarial-review` skill coordinates lenses and publishes the attempt's optional
external projection. Reviewer agents produce findings. One owner publishes each comment.

## Authoritative records

An initiative lives at `docs/roadmap/<date>-<slug>/`. `spec.md` defines the result;
`evaluation.md` estimates it; `design.md` records the chosen design when needed;
`improvement-plan.md` explains execution; `tasks.md` is the canonical progress ledger;
`testing/` preserves results and evidence.

A remote Done status does not prove a test. QA green does not prove a remote comment
was delivered. A publication receipt does not approve a specification.

## Project ports and admission

`.claude/integrations.json` binds functions such as `task-tracking` or `documentation`
to a selected skill/tool and declared operations. `integration-route.py` only validates
and selects declarations. It neither connects accounts nor runs tools or authorizes writes.
The workflow and adapter check the actual session, destination, permission and receipt.

Optional failures leave external projection pending while local work continues. Mandatory
review/QA gates retain their requirements. A broken board never turns red QA into green.

Before adding a capability, identify its existing owner, demonstrated need, distinct value,
bounded contract, validation and maintenance owner. Organizational details normally belong
to project extensions. The remaining proposals were not bulk-added. This is modular
packaging with ports/adapters; it does not require claiming the entire product uses DDD.
