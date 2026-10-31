> Advanced reference. Start with the [plain-language handbook](../CUSTOMIZATION.md). This chapter preserves implementation contracts and configuration details.

# 6. Operations, adoption and failure handling

Start with a small pilot, a process owner, connector administrator and technical
owner. Agree accounts, destinations, publication scope and write authorizations.
Run the local lifecycle first, then one tracking/documentation integration. Test
a controlled write, a rejection and reconciliation before broad rollout. An MCP
inventory is not business or technical acceptance.

## W-18. Validate and operate an integration

**Commands:** doctor, work-context, read-only router. **Actors:** user, administrator,
adapter owner. **Tools:** local checks and requested bounded remote reads.

| Step | Owner/action | Correct interpretation |
|---|---|---|
| 1 | User fixes project root/runtime | Another root's diagnostic proves nothing here |
| 2 | Router validates/filters declarations | Declared is not connected |
| 3 | Doctor checks installation/config | Does not certify past dispatch or remote permissions |
| 4 | Runtime/admin checks account/tools/access | Authentication differs from destination permission |
| 5 | Adapter pilots bounded read | Correct object/project; pagination accounted for |
| 6 | User reviews concrete write | Authorization for actual effects |
| 7 | Adapter executes/classifies | Confirmed, skipped, failed or uncertain |
| 8 | Owner records receipt/reconciles | No blind retry after uncertain writes |

```powershell
python agent-kits/shared/integration-route.py --project <project> --check
python agent-kits/shared/integration-route.py --project <project> --event task.started
python agent-kits/shared/project-pieces.py --project <project> --runtime codex --project-only --json
```

Locate scripts in the installed bundle; checkout paths above are examples.
Check returns 2 for invalid, partial or unavailable configuration. Ordinary optional
projection reports these conditions and continues the local lifecycle with gates intact.

## Router states

| Status | Meaning | Action |
|---|---|---|
| absent | No declarations/recognized opt-ins | Local work or explicit configuration |
| disabled | No active bindings | Respect choice; detecting MCP does not enable it |
| declared | Valid matching bindings | Verify session, contract, destination, permission |
| no_match | Active bindings do not match filter | Do not substitute another provider |
| partial | Valid matches plus rejected declarations | Report diagnostics, use independent valid entries only |
| invalid | Requested declaration cannot be used | Review schema/duplicates without resetting/fallback |
| unavailable | Safe read/dependency unavailable | Repair bundle/access; continue locally |

Router availability/permissions remain unverified and execution not_run. Actual
execution evidence belongs to the adapter, not this read-only component.

## Common incidents

| Symptom | Check | Response |
|---|---|---|
| Valid config, absent tool | Runtime, connection, version, actual catalog | Repair connector; never invent a tool name |
| Connected account, write denied | Account/destination/role/admin policy | Administrator reviews permission; no automatic escalation |
| Missing target status | Allowed transitions for this object | Pending projection and explicit mapping, no example ID |
| Timeout after send | Remote ID/correlation | Reconcile before replay |
| Both document sides changed | Base hash and revisions | Preview conflict and ask for resolution |
| Duplicate comments | Event owner/attempt key | One publisher, per-operation receipts |
| Phase closes early | Every task's gates | Reconcile/repair adapter under authorization |
| Partial extension inventory | Format, limits, links, conflicts | Repair declaration; omission grants no permission |
| Plugin contents changed approval error | Installed version and changed bundle | Review/approve through native UI, never bypass trust hashes |
| Unnamed hook/unverified execution | Installed labels and process result | Supported update; distinguish UI routing from process failure |

An unknown-conversation notification is not a failed-process receipt. An approved
hash does not prove hook execution. Keep diagnostics bounded and avoid dumping
conversations or full private configurations.

## Major-version migration

The user authorized breaking changes where appropriate. The explicit integration
contract is version-1 project integrations.json. Back up preferences/maps privately,
identify actual destinations and existing effects, then prepare/validate new bindings.
An explicit empty list disables selection. A present new config takes precedence
even if empty/invalid; it is not ignored to silently use an older account.

Only when the new file is absent are local Jira/Confluence enabled booleans recognized.
This transitional read neither migrates nor certifies connectivity. No other project
or HOME is used. Jira scripts now require the actual project root instead of inheriting
a parent opt-in.

Modified portable packages must be exported to a different destination and reconciled.
Profile copies do not adopt historical files by name. Choose a clean destination or
resolve ownership/modifications explicitly. Never delete remote maps to avoid migration
conflicts and accidentally recreate everything.

## Maintain documentation and PDF

Markdown chapters are the delivery source. Workflow changes update steps, owners,
commands, skills, tools, settings, events, gates and recovery in both languages.
Examples retain router/adapter checks. Regenerate and visually inspect the PDF
before distribution. Leads should be able to ask for a spec, a task preview, a
phase's documents or pending synchronization, and get results/evidence without
needing internal IDs or raw logs.

## Recover an interrupted copy installation

A profile update is not a transaction over the whole tree. Failure/cancellation
can leave some files applied. An incomplete manifest retains both previous and
planned owned hashes, recognizing unchanged old files without adopting consumer
edits. After reconciling the conflict, reinstall preserves selection and resumes;
uninstall can also remove owned files that still have their previous version.

Every file is revalidated before replacement. Persistent Windows locks fail rather
than falling back to truncating an in-use file. This detects observed changes;
it is neither a universal lock against external writers nor multi-file atomicity.
Retain error evidence and review the manifest before retrying or uninstalling.
