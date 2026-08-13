# Installation and deployment

**English** · [Español](../INSTALL.md)

Bundle of custom agents for Claude Code covering the lifecycle of an initiative (requirements → budget → plan → implementation → tests → documentation) with time/cost accounting and optional traceability in Jira/Confluence. Agents: **analyst** (requirements gathering), **evaluator** (evaluates/budgets), **planner** (plans), **implementer** (implements), **qa** (Playwright E2E), **documenter** (documentation), **pdfy** (PDF) and **nemesis** (SAST+DAST audit). Shared skills: **cybersecurity**, **to-pdf**, **confluence-publish**, **confluence-pull**, **roadmap-dashboard**, **jira-sync** and **discovery**. Commands: **/setup**, **/pm-cycle**, **/dev-cycle**, **/pm-backlog**, **/roadmap-status**, **/roadmap-metrics**, **/roadmap-brief**, **/roadmap-live**, **/retro** and **/confluence-pull**.

Contents (everything hangs from the bundle root, which is deployed as `.claude/`):
- `agents/*.md` — agent definitions.
- `skills/<skill>/` — shared skills (some with `scripts/` and `assets/`).
- `commands/*.md` — orchestrator commands (`/…`).
- `agent-kits/<agent>/` — private per-agent toolkits/templates.
- `.claude-plugin/` — plugin and marketplace manifest (for option 3).
- `docs/` — documentation (not loaded as code; the loader ignores it). See [`README.md`](README.md) (index), [`FLOWS.md`](FLOWS.md) (diagrams), [`CONVENTIONS.md`](CONVENTIONS.md) and [`atlassian-connector-notes.md` (Spanish)](../atlassian-connector-notes.md).
- `.github/workflows/ci.yml` — CI (tests + syntax + version consistency).

Kit paths are resolved at runtime with a `find` over `$PWD/.claude` and `$HOME/.claude`, so **the agents work the same across the following three options**.

> ⚠️ **Do not clone the repository inside a cloud-synced folder** (OneDrive, Dropbox, Google Drive, iCloud…). The sync client and git step on each other: it locks `.lock` files and `.git` objects while uploading, causing errors like `Unable to create '.git/HEAD.lock'`, "index file corrupt" or half-read files. Clone it into a local path **outside** the synced area (e.g. `C:\dev\custom-agents` or `~/code/custom-agents`). If it is already in a synced folder and you see those errors: pause syncing, delete the `.git/*.lock` files, run `git status` to rebuild the index, and consider moving the repo out.

---

## Option 1 — Try it in a project (quick)

Link (or copy) the bundle as the target project's `.claude/`:

```bash
# symlink (recommended for trying it out; reflects repo changes instantly)
ln -s "/path/to/repo/custom-agents" "/path/to/project/.claude"

# or copy
cp -r "/path/to/repo/custom-agents/." "/path/to/project/.claude/"
```

In Claude Code, inside the project: `/agents` to see them, and invoke them with `@analyst`, `@evaluator`, `@planner`, `@implementer`, `@qa`, `@nemesis`, `@pdfy` (or "use the … agent"). For the full flow, use the commands (`/setup`, `/pm-cycle`, `/dev-cycle`…).

---

## Option 2 — Personal reuse across all your projects (`~/.claude/`)

Copy the contents to your user folder; it becomes available in **all your projects** (precedence: if a project defines an agent with the same name, the project's wins):

```bash
cp -r "/path/to/repo/custom-agents/agents/."      "$HOME/.claude/agents/"
cp -r "/path/to/repo/custom-agents/skills/."      "$HOME/.claude/skills/"
cp -r "/path/to/repo/custom-agents/agent-kits/."  "$HOME/.claude/agent-kits/"
```

The path resolver finds the kits in `~/.claude/agent-kits/…` automatically.

---

## Option 3 — Plugin + marketplace (recommended, scalable and for teams)

The bundle already includes `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`. Publish the repo to git (GitHub) and add it as a marketplace. Two ways depending on where you work:

**a) Claude Code CLI (terminal).** Open a terminal, launch `claude` and, inside the session:

```
/plugin marketplace add daycry/custom-agents
/plugin install custom-agents@daycry
```

**b) Claude Desktop / Cowork (UI).** **Customize** menu (sidebar) → **Plugins** tab. In Cowork, open the **Cowork** tab first. Under **Personal plugins**, the **"+"** button → **Add marketplace** → **Add from a repository** → paste the repo URL (`https://github.com/daycry/custom-agents.git`). Then **Install** on the `custom-agents` plugin.

After installing, the agents become available in **all projects** on the machine.

> **Namespacing (why Option 3 is preferred).** Installed as a plugin, Claude Code automatically **prefixes** everything with the plugin name: agents and commands are invoked as `custom-agents:evaluator`, `/custom-agents:dev-cycle`, etc. — just like *superpowers* does. This way they **never collide** with agents/commands from another plugin, even if they share a name. In contrast, with **Options 1 and 2** (copying the bundle into a `.claude/`) the names are "bare" (`evaluator`, `/dev-cycle`) and **can collide** with another `.claude/` using the same name. The linter warns about the most generic names (`setup`, `retro`, …) precisely for this reason. Rule of thumb: for real and team use, **install as a plugin** (Option 3); reserve Options 1/2 for developing the bundle itself.

> **Where each thing runs.** The **`/plugin …` commands only work in a Claude Code session** (terminal with `claude`), **not** in the regular chat box. **Sub-agents run only in Cowork** (in the regular chat they appear grayed out); **skills** work in web chat, Desktop Chat and Cowork.

> **Path caveat.** In Claude Code, `${CLAUDE_PLUGIN_ROOT}` is not expanded inside agent/skill markdown. That is why the agents do NOT use fixed paths: they resolve their kit with `find` over `$PWD/.claude` and `$HOME/.claude` (the latter covers both `~/.claude/` and the plugin cache `~/.claude/plugins/…`). This is the reason all three options work without touching anything.

---

## Updating the plugin after repo changes

**Golden rule:** Claude Code detects updates **by version number**, not by commit. If you publish changes without bumping the version, `update` will see nothing.

### When publishing (repo author)
1. Make your changes.
2. **Bump the version** with the script (recommended), which keeps it consistent across the **three** places where it lives (`plugin.json`, and in `marketplace.json` both `metadata.version` and the plugin entry) and creates a commit + tag:

   ```bash
   python scripts/release.py 1.5.1        # consistent bump + commit + tag v1.5.1
   python scripts/release.py --check      # only verifies that the 3 versions match
   ```

   If you prefer doing it by hand: edit those **three** fields to the **same** number. If they do not match or do not increase, the client will not detect the update (this is the most common failure).
3. `git push origin HEAD && git push origin vX.Y.Z`.

> Current published version: **1.5.0** (consistent in both manifests). Use `python scripts/release.py --check` to confirm it before publishing.

### When updating — Claude Code CLI
In a `claude` session:

```
/plugin marketplace update daycry
/plugin update custom-agents@daycry
/reload-plugins
```

### When updating — Claude Desktop / Cowork (UI)
**Customize → Plugins**, locate the `daycry` marketplace and open its menu (**⋯**).

- If the **Update / Actualizar** button is enabled, use it.
- **If the update button appears disabled** (known case): **remove the marketplace and add it back** — menu **⋯ → Remove**, then **"+" → Add marketplace → Add from a repository** with the repo URL. That re-syncs the latest version. Reinstall the plugin if needed.

### If it still shows the old version (cache)
The cache lives in `~/.claude/plugins/cache/` (one folder per version). Reinstall:

```
/plugin uninstall custom-agents@daycry
/plugin install custom-agents@daycry
```

or, nuclear option, delete the cache and reinstall:

```
rm -rf ~/.claude/plugins/cache/
```

---

## Atlassian connector (Jira & Confluence) — for `confluence-publish`, `confluence-pull` and `jira-sync`

The same **official Atlassian connector (Rovo MCP)** serves three integrations, **all
opt-in** and independent: **Confluence** (`confluence-publish` uploads `docs/`; `confluence-pull`
downloads it) and **Jira** (`jira-sync` pushes the plan to issues, logs hours and marks them *Done*; `/roadmap-live`
reads live status). A single connector setup covers all three. Verified connector behaviors
in [`atlassian-connector-notes.md` (Spanish)](../atlassian-connector-notes.md).

The `confluence-publish` skill publishes/mirrors the documentation from `docs/` to Confluence, and the
`planner`, `evaluator`, `qa` and `documenter` agents invoke it when writing to `docs/` (the "Sync with
Confluence" step). It is **optional (opt-in)**: the first time, the skill asks whether you want to sync
with Confluence; if you say **no**, it remembers it (`"enabled": false` in `.claude/confluence.json`)
and never asks or syncs again. If you say **yes**, it connects and runs the assistant.
Everything goes through the **official Atlassian connector (Rovo MCP)** — there is no custom integration. If you are
going to use the sync, set up the connector **once** per environment:

- **Claude Desktop / Cowork (UI):** **Customize → Connectors** menu (or **Conectores**) → add
  **Atlassian (Jira & Confluence)** and complete the OAuth login. This is what the app uses.
- **Claude Code CLI (terminal):** register the remote MCP and authenticate:
  ```bash
  claude mcp add --transport http atlassian https://mcp.atlassian.com/v1/mcp
  # then, inside a `claude` session, follow the OAuth flow that appears
  ```
- **VS Code extension:** uses the same MCP configuration as Claude Code (the `claude mcp add`
  above works; the extension shares the CLI's MCP servers).

Behavior per environment:

- **Cowork / desktop:** the "choose where to publish" step opens an **interactive tree
  browser** (artifact) that expands pages live.
- **CLI / VS Code:** there is no artifact host, so that step is **conversational**
  (the skill lists spaces and pages as text and you pick by number). Everything else —creating/updating
  pages and the agents' sync— is **identical** across the three environments.

Notes:

- The first time, the skill guides you to choose a space and anchor (root or under a page) and
  saves the decision in the project's `.claude/confluence.json`; after that it is automatic.
- **Change detection without git:** the skill keeps a manifest `.claude/confluence-state.json`
  (content hash + `pageId` per document) and publishes only what changed (create/update/
  mark obsolete). It is idempotent and independent of commits or dates.
- **Optional hook (trigger):** the plugin includes a `PostToolUse` hook (`hooks/hooks.json`) that,
  when files under `docs/` are edited, leaves a `.claude/.confluence-pending` marker; it publishes nothing.
  The actual sync is done by the skill (honoring the opt-in). A plugin's hooks are activated
  when it is installed; after changes to `hooks/`, `/reload-plugins` is required.
- `docs/security-scan/**` is **never** synced (sensitive data from `nemesis`).
- The Atlassian connector does **not** allow deleting pages: when a `.md` is removed, the page is
  marked as obsolete and listed for manual deletion.

---

## `nemesis`-specific notes

- The active pentest ONLY operates against local/private hosts (`lib-guardrail.sh` guardrail). It never targets third parties.
- The first time, it checks its toolkit and ASKS FOR PERMISSION before installing what is missing (binaries in `~/.claude/security-tools/`, outside the repo).
- Reports in `docs/security-scan/<date>/index.html` of the audited project. That subpath goes in the project's `.gitignore` (findings are sensitive); the rest of `docs/` is versioned.
- Per-machine requirements: git, curl and python or php. The installer resolves the rest.

---

## Observability and session monitors

The plugin measures **cost** (tokens/€/hours per artifact and task — `usage-meter`); to see
**live session activity** (tools, subagents, kanban) you can install an external monitor
alongside it, such as Claude-Code-Agent-Monitor: both sets of hooks coexist without interfering.
Details and a cheat sheet of "where to look for what": [`observability.md`](observability.md).
