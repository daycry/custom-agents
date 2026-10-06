# Plugin capability panel

**English** · [Español](../PLUGIN-PANEL.md)

The plugin-catalog command uses plugin-panel to explore agents, skills, commands,
declared tools and global hooks. Search and filters run in a standalone HTML
file. Initiative progress remains in roadmap-dashboard.

From a checkout:

```powershell
python skills/plugin-panel/scripts/build_panel.py --html panel.html
python skills/plugin-panel/scripts/build_panel.py --json
```

Installed bundles resolve the skill through their runtime roots. The generator
finds its own bundle; `--root <bundle>` inspects another catalog without importing
its code. Native Python supports Windows without WSL, Tkinter, extra Python
packages or a server.

Only public frontmatter and hooks/hooks.json are read. Bodies, hook commands,
environment variables and private memory contents are excluded. The central
redactor runs before export. Names, models and tools describe declarations,
not which tools are available in the current session.

Runtime and memory indicators show **source presence in the inspected bundle**.
They do not establish service health, access, consumer configuration or hook
execution. Agent guards remain in their definitions.

Malformed/unreadable inputs produce warnings. Missing bundled redactor or invalid
root produces exit 2 with no metadata export; the user's main task continues.
Reads and inventory are bounded and symlinks rejected. HTML writes are atomic
and replace only output bearing this generator's marker. Rebuild to refresh.

See the [ECC and Graphify comparison](../roadmap/2026-10-06-ecc-capabilities/comparison.md)
for adoption decisions. ECC 2.2.3 inspired the capability navigation; the stdlib
implementation is original.
