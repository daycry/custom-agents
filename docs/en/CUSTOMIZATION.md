# custom-agents usage and customization handbook

**English** · [Español](../CUSTOMIZATION.md)

This handbook accompanies the modular architecture of the next version. It is
intended for department leads, product owners, technical teams and administrators.
It separates implemented product behavior from project adapters that still need
configuration and acceptance testing. An integration recipe is not a verified connection.

| Chapter | Purpose | Main audience |
|---|---|---|
| [Product and decisions](guides/product.md) | Core, modules and ownership | Department leads |
| [Core workflows](guides/core-workflows.md) | Steps, commands, agents, skills and gates | Product and delivery teams |
| [Atlassian](guides/atlassian.md) | Tasks/phases, comments, transitions and documents | Leads and administrators |
| [Redmine and wiki](guides/redmine.md) | Add a project provider without changing core | Technical teams |
| [Customization](guides/customization.md) | Personas, agents, skills, commands, tools, MCP and profiles | Technical teams |
| [Operations and adoption](guides/operations.md) | Permissions, failures, migration and rollout | Process owners |

The delivery PDF combines these chapters and configuration examples in Spanish,
the requested language for department leads. Markdown remains the maintainable source.
Commands run from the project root. `$SHAREDKIT` means the shared kit in the installed
bundle, located through the runtime's supported roots, rather than a fixed user path.

The product provides a traceable local lifecycle, project-selected integrations and
optional modules. It does not create organizational accounts, grant service permissions
or install tools merely because configuration mentions them. Administrators and the
runtime retain those responsibilities.

## Invocation by runtime

This handbook uses short command names. A native Claude plugin uses
`/custom-agents:setup`, `/custom-agents:dev-cycle`, etc. Codex uses generated
command adapter skills such as `$custom-agents:custom-agents-setup`, selected
explicitly or from `/skills`. OpenCode uses the short form `/setup`. A Claude
copy has no plugin namespace. Confirm the actual available command/skill before
following a workflow; agent IDs similarly follow the generated runtime map.
