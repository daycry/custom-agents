# Plugin capability panel

Hooks appear in one card per **runtime and event**. `PostToolUse` retains three
handlers in each runtime. HTML counts groups; JSON retains one entry per handler,
`counts.hooks` counts actions and `hook_group_count` counts groups. `--runtime`
selects hook and extension sources; `all` compares the three runtimes. The HTML
runtime filter affects hooks while retaining other bundle capabilities.

Each action has a stable ID, source and locator, native channel, public purpose,
activation and behavior. Claude reads `hooks/hooks.json`; Codex reads
`interop/codex/hooks.json`. OpenCode reads bounded strict JSON between markers in
`hooks/opencode-plugin.js`: the catalog governs the adapter and is never imported
as JavaScript. `hook_sources` reports each source as declared, missing or invalid;
a failed source is never replaced with another runtime's hooks.

Claude/Codex timeouts use seconds with registration provenance. OpenCode shows
milliseconds of adapter supervision; its idle/execution stream capture is not a
native teardown hook. Declared, absent and invalid budgets remain distinct;
no default is invented. The guard obtains role identities from the central bundle
map; configuration, loading and execution are different evidence. `load_status`
and `execution_status` remain `unknown` in this static catalog.

Informational names and purposes come from recognized handlers' public
`panel-title` and `panel-description` headers. The panel excludes full commands
and never executes scripts, hooks or diagnostics. Action links restore filters
and focus; Sources stays reachable on mobile.

**English** · [Español](../PLUGIN-PANEL.md)

The plugin-catalog command uses plugin-panel to explore agents, skills, commands,
declared tools and global hooks. Search and filters run in a standalone HTML
file. Initiative progress remains in roadmap-dashboard.

From a checkout:

```powershell
python skills/plugin-panel/scripts/build_panel.py --html panel.html
python skills/plugin-panel/scripts/build_panel.py --json
python skills/plugin-panel/scripts/build_panel.py --project . --runtime codex --html panel.html
```

Installed bundles resolve the skill through their runtime roots. The generator
finds its own bundle; `--root <bundle>` inspects another catalog without importing
its code. Native Python supports Windows without WSL, Tkinter, extra Python
packages or a server.

Include your components with `--project <root>` and the actual session runtime
in `--runtime claude-code|codex|opencode`. `--cwd <package>` inspects its skill
ancestor chain. Personal sources are included by default; `--project-only`
excludes them and `--user-root <runtime>=<path>` selects another root. `all`
compares declarations without claiming that one session loaded every runtime.

“Tus extensiones” has independent search and kind/origin/runtime filters. Its
declarations do not change bundle counts. Cards retain ID, source, ownership and
conflicts. Disabled MCP entries describe configuration; connection and permissions
remain unverified. OpenCode tools are definition sources, without inferred exports.
Personas retain the brief's `Tipo` contract and remain distinct from agents.

The generator imports `project-pieces.py` from its own bundle, never inspected
`--root` data. Reader failure preserves the bundle catalog with an explicit
partial inventory. JSON adds `extensions` only when a project is requested,
keeping `schema_version: 1` and existing counts. Task selection follows the
[shared extension method](PROJECT-EXTENSIONS.md).

The inventory extracts public frontmatter, runtime hook registries and metadata from
the first eight lines of scripts recognized by the bundled launcher. Executable
bodies, full commands, environment values and private memory are excluded from
the output. The central
redactor runs before export. Names, models and tools describe declarations,
not which tools are available in the current session.

The bundled local template offers section navigation, inventory cards, filters
and expandable role and capability details. It adapts to mobile, supports keyboard
controls and respects reduced motion. It needs no server or third-party assets.
If the template is missing, HTML generation reports the issue while JSON remains
available.

Runtime and memory indicators show **source presence in the inspected bundle**.
They do not establish service health, access, consumer configuration or hook
execution. The extension section separately inventories local project/user
declarations; it does not measure health or invoke servers.

Malformed/unreadable inputs produce warnings. Missing bundled redactor or invalid
root produces exit 2 with no metadata export; the user's main task continues.
Reads and inventory are bounded and symlinks rejected. HTML writes are atomic
and replace only output bearing this generator's marker. Rebuild to refresh.

See the [architecture and memory decisions](../roadmap/2026-10-06-capability-foundation/comparison.md)
for the design rationale. The panel is an original stdlib implementation.

“Guides by role” reads the inspected bundle's capability registry. These rows
are separate from catalog cards and do not prove that guides were applied.
An absent/invalid registry leaves the catalog usable with an explicit limitation.
`/work-context` selects from the same registry by role/phase/stack/area using the
task's package manifests.
