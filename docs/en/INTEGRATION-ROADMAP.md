# Phased integration

**English** · [Español](../INTEGRATION-ROADMAP.md)

Sequence agreed with the user on 2026-10-06. Each phase ships with a defined
scope, comparison against existing functionality, tests, review, documentation
and a branch push. Future phases need their own plans; this page does not claim
they have been implemented.

| Phase | Delivery | Status |
|---|---|---|
| 1. Shared core | Multi-runtime hooks, guidance selection, workflow, briefs, optional structural context, outcome evaluation and panel | Completed and published; evidence in [workflow-integration](../roadmap/2026-10-06-workflow-integration/tasks.md) |
| 2. User extensions | Recognize user agents, skills, personas, tools and MCP in Claude, Codex and OpenCode; show origin, conflicts and unverified availability | In progress; reader, selection, briefs and panel implemented on branch, pending review and closure. [Plan and evidence](../roadmap/2026-10-06-project-extensions/tasks.md) |
| 3. Catalog capabilities | Thoroughly compare existing skills, tools, agents and commands from the reference catalog; integrate useful improvements and verify actual runtime guard scope | Pending; the earlier inventory does not replace functional analysis or dispatch testing |
| 4. Memory and evaluation | Measure retrieval, freshness and usefulness; compare improvements against existing Markdown, journal and backends before deciding changes | Pending; the current AST pilot does not prove retrieval effectiveness |

No new technical packages will be created to fill gaps in the reference catalog.
Any future technical capability must exist there and justify adoption against
what we already have. Selection will be optional and project-specific, without
imposing stack packages on all users. Existing plugin guidance remains subject
to its current contracts.

## What the extension branch recognizes

| User component | Current behavior | Limit |
|---|---|---|
| Agent | Reader and panel recognize Markdown, TOML and project/user configuration roles per runtime | A declaration does not prove loading; it complements cycle roles |
| Skill with frontmatter | Inventory of native and compatible sources, with explicit selection by ID | Content is consulted on demand; it is not automatically added to the bundled catalog |
| Domain persona | The brief prioritizes project `.claude/personas/<type>.md` | This is a brief persona, not an independent agent; types are extensible |
| Tool | Displays declared names and OpenCode JS/TS sources | Does not execute exports or establish permissions or availability |
| MCP server | Inventories project, user and agent declarations; flags invalid Claude definitions and declared disabling | Does not connect servers or export endpoints, commands, variables or credentials |

`feat/project-extensions` contains this integration, which is not published yet.
The shared reader feeds `/work-context`, ledger selection, brief references and
the panel's independent filters. It preserves duplicates and displays sources;
session capabilities must be checked before invocation. It reuses the
[specialization](SPECIALIZATION.md) O1 contract to validate ownership read-only;
generation and adoption retain their separate plan.

Executed results and pending gates are in the phase 2 ledger; partial tests do
not establish closure or publication. The published phase 1 catalog retains its
recorded delivery in its own ledger.

**Scope check pending in phase 3:** current Claude documentation says plugin
agents ignore `hooks`, `mcpServers` and `permissionMode` in their frontmatter.
The declared implementer guard needs installation-mode dispatch tests and an
implementation update before claiming plugin coverage. See the
[verified contracts](../../skills/plugin-dev/references/claude-code-contracts.md).
