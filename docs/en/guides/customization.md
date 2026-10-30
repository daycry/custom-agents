# 5. Customize without changing core

## W-16. Choose the right extension

**Entry:** a new domain criterion, specialist, system or operation is needed.
**Commands:** work-context; optional plugin-catalog. **Owners:** domain lead and
technical team; planner records selected references in tasks. **Readers:** project-pieces
and capability-route, without executing project code.

| Need | Piece | Owner/location | Required check |
|---|---|---|---|
| Billing/legal/business criteria | Short persona | Project | Task type and brief limits |
| Specialist objective/tools | Agent | Project runtime | Actual ID, instructions and allowed tools |
| Reusable method | Skill | Project/user/bundle module | Triggers, references and positive/negative cases |
| User-started sequence | Command | Supported runtime | Inputs, decisions, outputs, handoffs |
| Permanent principle | Instructions/constitution | Project | Native scope/precedence |
| Programmatic operation | Tool/script | Project/runtime | Schema, exit codes, permission and tests |
| Service access | MCP/connector | Runtime/administrator | Trust, authentication and actual operations |
| Provider participation in core | Adapter plus binding | Project | Events, capabilities, destination and receipts |

Do not add an agent just to wrap a skill, or confuse an MCP declaration with a workflow.
Extensions complement existing lifecycle owners rather than replacing their gates.

## Domain personas and team members

A domain persona can live in `.claude/personas/billing.md`, a plugin convention,
with short rules for currency, taxes, rounding, billing period and audit examples.
Label the task with `Tipo: billing`. The brief prefers the project persona, then
the catalog; absent personas yield a warning and ordinary operation. The profile
does not create a native agent or impersonate a real person.

Human team members have real service/runtime accounts. Administrators invite them
using provider mechanisms. Agree who approves scope, who publishes and who owns
tasks. The plugin does not create those identities. Assignment can notify a person,
so preview and authorize it as an external effect.

## Project agents, skills, commands and rules

A Claude project agent can be a Markdown file under `.claude/agents/` with a unique
name such as project-billing-reviewer, description, minimal read tools and selected
model. Its body requires file/line/business-case evidence, forbids editing and
publication and leaves QA to its owner. Codex has TOML agents/role configuration;
OpenCode has its native Markdown/configuration surfaces. Do not copy fields across
runtimes as if their loaders were interchangeable.

A minimal standalone Codex declaration recognized by the inventory uses name,
description and developer_instructions. Inventory recognition does not certify the
runtime's effective loading or restrictions. A model choice grants no tools or permission.
[Exact locations and inventory contracts](../PROJECT-EXTENSIONS.md).

Copy the project-redmine reference skill from docs/examples/integrations into the
runtime's skill root, rather than the plugin cache. A professional skill has a
unique name, useful triggers, scope, inputs, steps, limits, errors and demand-loaded
references. Deterministic parsing/calculation/verdicts belong to tested scripts.
External dependencies and explicit degradation must be described.

Test missing configuration, read-only permission, wrong project, unavailable state,
partial batch and timeout-after-create. The supplied skill is a starting contract,
not a tested transport implementation.

Project commands coordinate existing owners and retain one publisher per effect.
Claude uses its commands directory, OpenCode its supported command surfaces.
The inventory does not invent a Codex project-command loader; use supported native
capabilities such as an invocable skill. Permanent rules belong to project native
instructions and an optional constitution, without pasting the entire handbook
into every prompt or relaxing mandatory authorization/review/QA.

## W-17. Add a tool or MCP server

**Owner:** project administrator/developer. **Inventory commands:** work-context,
doctor and runtime-native MCP management. **Skills:** delivery-practices plus the
business adapter. **Tools:** declared server, then the operations actually discovered.

| Step | Action | Evidence |
|---|---|---|
| 1 | Define the missing operation | Input, output, effect and bounded need |
| 2 | Assess official/maintained connectors | Ownership, license, maintenance, compatibility |
| 3 | Choose scope and authentication | Correct account/project; secure credentials |
| 4 | Declare server in the runtime | Valid configuration, not connection proof |
| 5 | Connect and authorize natively | Session's actual operation list |
| 6 | Pilot a bounded read | Expected destination and failure handling |
| 7 | Add adapter/binding for lifecycle use | Capabilities match what was verified |
| 8 | Preview/authorize one pilot write | Actual receipt and reconciliation |
| 9 | Revalidate after version/permission changes | No inference from stale inventory |

A local script does not become a native tool by existing in an arbitrary directory.
The inventory never imports scripts, executes exports or installs dependencies to
discover tools. OpenCode custom tool sources and Claude/Codex MCP tools follow their
own runtime contracts.

Examples use a nonfunctional `.invalid` endpoint and need an approved real destination:

```json
{"mcpServers":{"corporate-wiki":{"type":"http","url":"https://wiki.example.invalid/mcp"}}}
```

The JSON above is Claude project `.mcp.json`. A Codex configuration block is:

```toml
[mcp_servers.corporate_wiki]
url = "https://wiki.example.invalid/mcp"
```

An OpenCode server-per-key example is:

```json
{"mcp":{"corporate-wiki":{"type":"remote","url":"https://wiki.example.invalid/mcp","enabled":true}}}
```

Use the installed version's schema. The inventory also recognizes OpenCode V2
surfaces such as mcp.servers without claiming native precedence. Official sources:
[Claude MCP](https://code.claude.com/docs/en/mcp), [Codex MCP](https://learn.chatgpt.com/docs/extend/mcp?surface=cli),
[OpenCode MCP](https://opencode.ai/docs/mcp-servers/). Authentication/trust remain native.

Direct tool bindings use kind=tool, origin=session and an actual tool name. They
still require schema, purpose, destination, authorization and receipt checks.
For a multistep provider workflow, a skill adapter usually makes the contract clearer.

## Profiles and selective delivery

Read-only logical selection:

```powershell
python agent-kits/shared/module-selection.py --profile core --with jira
```

Portable skills export/check from the plugin checkout:

```powershell
python scripts/export-skills.py --profile core --with jira --out dist/team-skills --format all
python scripts/export-skills.py --check dist/team-skills
```

Claude copy plan:

```powershell
node install/install.mjs install -p claude-code --mode copy --profile core --with jira --dir <project> --dry-run
```

After review, run without dry-run. Copy mode does not register plugin hooks,
statusline or namespace. Existing foreign/modified targets are rejected before
copying. Profile changes retire only unchanged owned files; reinstall without
flags preserves the selection. Native plugins remain complete. Unsupported partial
native/OpenCode installer requests fail before registration/writes; choose the
complete bundle or portable skills as appropriate. Portable skills are not the full cycle.

## Conflicts and ownership

Use unique project names. Inventory preserves source IDs and duplicate warnings,
without universal runtime precedence. Planner records Extensiones and Procedencia
de extensiones; the brief revalidates references. A pieces.json inventory can compare
hash ownership/modification, but never adopts/executes/overwrites pieces.

Version project contracts, examples and tests. Keep secrets and runtime state out
of Git. Before retiring an extension, check task references and provide an explicit
alternative/warning. Previously cancelled adoption/generation work stays cancelled.
