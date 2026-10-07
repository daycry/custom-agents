# Plugin capability panel

Hooks appear in one card per event. `PostToolUse` lists its three handlers within
that card; the HTML counter measures distinct events. The JSON keeps one entry
per handler and `counts.hooks` counts handlers. Full hook commands remain excluded.
Recognized actions show names, purposes and triggers; timeouts appear when
configured in the source. Names and purposes come from the registered script's
public `panel-title` and `panel-description` headers. Scripts are never executed.

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

The inventory extracts public frontmatter, hooks/hooks.json and metadata from
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
