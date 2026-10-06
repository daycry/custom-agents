# Phased integration

**English** · [Español](../INTEGRATION-ROADMAP.md)

Sequence agreed with the user on 2026-10-06. Each phase ships with a defined
scope, comparison against existing functionality, tests, review, documentation
and a branch push. Future phases need their own plans; this page does not claim
they have been implemented.

| Phase | Delivery | Status |
|---|---|---|
| 1. Shared core | Multi-runtime hooks, guidance selection, workflow, briefs, optional structural context, outcome evaluation and panel | Completed and published; evidence in [workflow-integration](../roadmap/2026-10-06-workflow-integration/tasks.md) |
| 2. User extensions | Recognize user agents, skills, tools and MCP in Claude, Codex and OpenCode; show origin, conflicts and verified availability | Design and implementation pending |
| 3. Catalog capabilities | Thoroughly compare existing skills, tools, agents and commands from the reference catalog; integrate useful improvements without duplicating responsibilities | Pending; the earlier inventory does not replace functional analysis |
| 4. Memory and evaluation | Measure retrieval, freshness and usefulness; compare improvements against existing Markdown, journal and backends before deciding changes | Pending; the current AST pilot does not prove retrieval effectiveness |

No new technical packages will be created to fill gaps in the reference catalog.
Any future technical capability must exist there and justify adoption against
what we already have. Selection will be optional and project-specific, without
imposing stack packages on all users. Existing plugin guidance remains subject
to its current contracts.

## What the plugin recognizes today

| User component | Current behavior | Limit |
|---|---|---|
| Markdown agent with frontmatter | Panel and index read `agents/*.md` from the inspected root | They do not automatically merge all installations or formats across the three runtimes; they do not add workflow roles |
| Skill with frontmatter | Panel and index read `skills/*/SKILL.md` from that root | Workflow selection uses the bundled catalog; discovering a skill does not register it there |
| Domain persona | The brief prioritizes project `.claude/personas/<type>.md` | This is a brief persona, not an independent agent; types are extensible |
| Tool | The panel summarizes names declared in agent frontmatter | This is not a registry of user tools or evidence of execution or permissions |
| MCP server | The panel has no MCP server inventory | Its configuration, connection and exposed tools are not currently detected |

The inspection root is selected explicitly. Runtime discovery and plugin
inventory are different functions; listing a file does not prove the session
loaded it. Phase 2 must preserve user components, resolve collisions by origin
and distinguish **declared**, **detected** and **available in the session**.
Finding a component must not execute tools or connect servers. It will reuse the
[specialization contract](SPECIALIZATION.md): the persona cascade is implemented,
while registration and adoption remain pending work.
