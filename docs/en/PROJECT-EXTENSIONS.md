# Your agents, skills, personas, tools and MCP

**English** · [Español](../PROJECT-EXTENSIONS.md)

`agent-kits/shared/project-pieces.py` reads local project and user declarations.
The bundled reader is shared by work-context, task briefs and plugin-panel.
A declaration does not prove loading, connection or permission; the runtime
and the actual session determine those facts.

## Where to add them

Use your runtime's native folders and formats. Keep your components outside the
plugin cache, which updates replace.

| Component | Claude Code | Codex | OpenCode |
|---|---|---|---|
| Project agents | `.claude/agents/<name>.md` | `.codex/agents/<name>.toml`; also roles in `.codex/config.toml` | `.opencode/agents/<name>.md`; also `agent` in `opencode.json`/`.jsonc` |
| Project skills | `.claude/skills/<name>/SKILL.md` | `.agents/skills/<name>/SKILL.md` | `.opencode/skills`, `.claude/skills` or `.agents/skills`, containing `<name>/SKILL.md` |
| User commands | `.claude/commands/<name>.md` | The reader does not infer Codex commands from a project directory | `.opencode/commands/<name>.md`; also configured `command` entries |
| Tool sources | Agent-declared names; no generic plugin executor | Session-declared names; no inference of script exports | `.opencode/tools/*.{js,ts}`; sources are listed without running exports |
| Project MCP | `.mcp.json`, `mcpServers`; also agent-scoped declarations | `.codex/config.toml` and agent TOML, `mcp_servers` | `opencode.json`/`.jsonc`, `mcp` |

Markdown agents use native frontmatter. Standalone Codex agents declare `name`,
`description` and `developer_instructions`. Skills use `name`/`description`
frontmatter and an on-demand body. Extracting public metadata does not replace
native loader validation.

Normal user roots are `~/.claude`, `~/.codex`, `~/.agents/skills` and
`~/.config/opencode`. Claude stores personal and project-local MCP in
`~/.claude.json`; only the selected project's local declarations are considered.
Pass `--user-root <runtime>=<path>` explicitly for another root. The reader does
not infer custom roots or availability from private environment values.

Nested skills are inspected along the `--cwd` to `--project` ancestor chain,
not across the whole repository. The package must remain inside the project.

## How a task uses them

1. Work-context follows `capability-check.md` to select bundled guides and
   inspect relevant extension declarations for the current runtime.
2. Planner records the necessary IDs and their sources against the task contract:

   ```markdown
   - **Extensiones**: ext-<identifier returned by the reader>
   - **Procedencia de extensiones**: project billing specialist; consult its reference before use.
   ```

3. Implementer, reviewer and qa share that selection. The brief refreshes the
   declarations and adds bounded references, without preloading prompts or
   manuals. Removed components and IDs from another runtime are omitted with a warning.
4. Consult relevant content and check the session's actual capabilities before
   invoking an agent, tool or MCP. Extensions complement cycle roles and keep
   their responsibilities and quality gates intact.

IDs remain stable for a project-relative source. Personal roots have opaque
identities, without exporting absolute paths. Duplicate declarations are kept;
conflicts identify name, runtime and kind. No universal runtime precedence is assumed.

## Domain personas

This plugin contract is shared by all three environments. Add a short profile
at `.claude/personas/billing.md` and annotate the task:

```markdown
- **Tipo**: billing
```

The brief uses the project persona first, then the plugin catalog. If neither
exists it continues without a persona and warns. Types are extensible. The
profile enters the brief under its existing limits and remains distinct from
an agent. Detected personal personas can be referenced as material; they do
not add a fourth automatic step to the cascade.

## Panel and direct inventory

Plugin-catalog includes the current project. The panel separates bundle counts
from extension declarations and filters by kind, origin and runtime. Each entry
shows source, ID, conflicts, ownership and unverified availability.

```powershell
python skills/plugin-panel/scripts/build_panel.py --project . --runtime codex --html panel.html
python agent-kits/shared/project-pieces.py --project . --runtime codex --project-only --json
```

Repeat `--select <id>` to revalidate up to 20 selected identities. Task briefs
accept `--runtime`; carry the same custom roots/package using `--extensions-home`,
`--extensions-cwd` and `--extensions-user-root`. `--extensions-project-only`
excludes personal declarations. Extension references occupy at most 1000
characters and share the brief's auxiliary budget.

Claude MCP definitions with invalid transport or missing endpoint are flagged.
Disabling is read from the selected project's preferences in `~/.claude.json`;
other runtimes retain their declared enabled field. Neither proves connection.

## Ownership and limits

Claude skills may omit name and frontmatter; their name comes from the directory.
Legacy commands may omit frontmatter and use the filename. Missing declared
descriptions remain empty; private bodies are never used as public metadata.
Claude command and skill names share an invocation namespace, so cross-kind
collisions are visible, including those against the bundle.
Claude commands and OpenCode Markdown agents/commands use their filename even
if frontmatter declares another name. Claude skills preserve their frontmatter
name and directory alias to expose potential conflicts; the runtime determines
which invocation prevails.

Directories exceeding 1,000 entries are rejected as a whole with a warning;
other sources remain discoverable. This prevents filesystem enumeration order
from determining which pieces are silently dropped while keeping work bounded.

Registration is optional. If `.claude/pieces.json` exists, the reader validates
the [specialization O1 schema](SPECIALIZATION.md) and compares full LF-normalized
hashes. Ownership is managed, modified, unmanaged or unknown for an invalid
registry. Missing destinations are reported. Ownership grants no permissions
or overwrite rights.

Discovery does not create the registry, adopt, generate, rebuild or modify
components; these operations retain their separate specialization plan. It
does not run consumer scripts/CLIs, connect servers or resolve environment/file
placeholders. Private bodies, MCP commands, arguments, URLs, headers, environment
values and credentials stay excluded, with central redaction before export.

Limits are 512 KiB per file, 8 MiB total read budget, 1000 components and config
depth 32. Failed/rejected reads consume reservations. Complex YAML outside the
bounded extractor produces a warning. Links are excluded with the shared
OneDrive guard. Partial inventory is explicit and does not block the cycle.

[Verified native contracts](../roadmap/2026-10-06-project-extensions/contracts.md)
· [Panel](PLUGIN-PANEL.md) · [Shared flow](FLOWS.md).
