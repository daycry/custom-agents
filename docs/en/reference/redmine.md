> Advanced reference. Start with the [plain-language handbook](../CUSTOMIZATION.md). This chapter preserves implementation contracts and configuration details.

# 4. Redmine, wiki and project providers

Redmine is a project adapter, without adding its brand to core. The supplied
project skill is a reference contract to adapt and test, not an installed transport
or certified connection. Administrators choose a trusted connector for their instance.

Consult the official [issues API](https://www.redmine.org/projects/redmine/wiki/Rest_Issues)
and [wiki API](https://www.redmine.org/projects/redmine/wiki/Rest_WikiPages).
Instance version, roles and configuration determine the effective capabilities.
Core supplies ledger/events; the adapter translates fields, tracker, identities,
states and wiki format. A phase is not automatically a Redmine version/project.

## W-13. Add a Redmine adapter

**People:** process lead and technical/administrative team. **Commands:** setup,
work-context. **Project skill:** project-redmine. **Tools:** those verified in the
selected session connector. No core changes or mandatory redmine command.

| Step | Owner | Action | Output/check |
|---|---|---|---|
| 1 | Lead | Decide task/phase granularity and assignments | Collaboration policy |
| 2 | Administrator | Choose transport, account and pilot target | Minimum required access |
| 3 | Team | Add skill contract | Unique name and adapter tests |
| 4 | Team | Map operations/states | Declare only supported tools/capabilities |
| 5 | Setup | Adapt examples/integrations/project.json | Project-local bindings |
| 6 | Team | Add nonsecret preferences | Integration-settings/redmine.json |
| 7 | Router/inventory | Validate declarations and discover sources | Availability still checked in session |
| 8 | Team/user | Pilot reads and an authorized write | Actual receipts and failure handling |

Project preferences can include schema version, project identifier, granularity,
discovered tracker, assignment policy, logical started/reopen/closed targets and a
private map path. The router does not interpret that adapter-owned schema. Logical
targets must be resolved to real allowed states, never copied into status_id.

## Minimum adapter contract

| Capability | Core input | Adapter translation | Required evidence |
|---|---|---|---|
| plan.export | Approved ledger/task or phase/destination | Valid issue fields/project/tracker | Confirmed ID and local mapping |
| task.read | Issue reference and minimal fields | Bounded project read | ID, fields and query time |
| task.progress | Event, task, actor and evidence | Note/comment and allowed transition | Note receipt and observed state |
| worklog.write | Measurement with explicit unit | Instance-specific time entry | Actual entry and duplicate prevention |
| docs.publish | Approved document/revision | Separate wiki binding | Real page title/ID/version |

Do not declare aspirational capabilities. A read-only connector cannot subscribe
to write events. If an API combines a note and state change, document partial effects
and reconciliation instead of assuming errors roll back both.

## W-14. Run an initiative with Redmine

Local analyst/evaluator, optional architect, planner, implementer, review and QA
retain W-02–W-05 ownership. The project skill handles their optional projections.

| Moment | Emitter | Adapter effect | Evidence/control |
|---|---|---|---|
| Approved plan | Planner / plan.created | Preview task/phase issues | Account, project, tracker, assignment and authorization |
| Creation | Project-redmine | Check map/correlation; create missing | Per-object actual ID; no atomic-batch claim |
| Start | Implementer / task.started | Resolve allowed work state | Denial leaves projection pending, ledger unchanged |
| Implemented | Implementer / task.implemented | Note changes and verification | Role/event/task; no closure |
| Review | Review skill / completed or gaps | One attempt comment, reopen if applicable | Single publisher and actual evidence |
| QA | QA / passed or failed | Note gate result and evidence location | Comment does not execute QA |
| Accepted | Orchestrator / task.done | Final transition with both verdicts | Allowed state/receipt; all phase tasks required in phase mode |
| Phase closure | Implementer / phase.completed | Documentation handoff | No automatic raw evidence publication |

An implementation note includes role, event/task, change, actual verification and
approved evidence reference; it explicitly leaves review/QA pending. The adapter
adds its correlation key and instance format. Never attach conversations or secrets.

Correlation includes initiative, task/phase, event and attempt. Store remote IDs
and confirmed receipts, not credentials. Before replay, query the correlated object.
A timeout after send is uncertain. Losing the map is not permission to recreate all issues.

## W-15. Publish to a project wiki

**Binding:** documentation, project-wiki or another selected adapter.
**Event:** phase.completed; optional explicit docs.pull if implemented.
**Tools:** page/revision reads, writes, separately authorized attachments if needed.

Define Markdown conversion, hierarchy, stable document key and conflict policy.
Read the current remote revision, preview, obtain applicable authorization, write
and retain actual page version/local hash after verification. If conditional writes
are unavailable, disclose that limitation and revalidate; do not promise atomicity.

Deletion, attachments and concurrent edits are distinct cases. Local retirement
does not silently delete a remote page. Pull must compare both sides, preserve
frontmatter and resolve conflicts before writing.

GitHub/GitLab issues, Linear, Notion or a corporate wiki can implement these ports,
but their mention does not install adapters. Messaging requires a separate purpose,
contract and authorization; docs.publish is not an indirect permission to message people.
