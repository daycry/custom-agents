# Interoperability — Claude Code, Codex and OpenCode

**English** · [Español](../INTEROP.md)

This plugin was born for Claude Code and today it also installs into **Codex** (OpenAI) and
**OpenCode** (SST). This document covers **how** (installation), **what gets translated** (and into
which format) and — most importantly — **what does NOT work the same** in each runtime.

> **A single source of truth.** `agents/`, `commands/`, `skills/` and `hooks/` remain the real
> pieces. What travels to Codex and OpenCode are **generated translations** produced by
> `scripts/export-interop.py`; nobody edits them by hand and `--check` fails when they fall behind.

---

## 1. Installation

### The short way: the installer

```bash
npx @daycry/custom-agents                     # menu: pick providers (detected ones are marked)
npx @daycry/custom-agents install -p codex    # Codex only, in this project
npx @daycry/custom-agents install --all --scope user
npx @daycry/custom-agents install -p opencode --dry-run   # print the plan, write nothing
npx @daycry/custom-agents status               # what is installed and where
npx @daycry/custom-agents uninstall -p codex   # remove what it installed, and only that
```

| Option | What for |
|---|---|
| `-p, --provider <ids>` | `claude-code`, `codex`, `opencode` (comma-separated) or `all` |
| `--scope project\|user` | project (default) or the runtime's global install |
| `--dir <path>` | target project (defaults to the current directory) |
| `--mode plugin\|copy` | **Claude Code only**: install it as a plugin (default) or copy the bundle into `.claude/` |
| `--source <path\|owner/repo>` | where the Claude Code marketplace comes from (default `daycry/custom-agents`); a local path is handy for development |
| `--force-marketplace` | **Codex only**: if the `daycry` marketplace already exists pointing elsewhere, redo it (by default it warns and touches nothing) |
| `--dry-run` | full plan without writing anything |
| `-y, --yes` | no prompts (CI) |

> `CLAUDE_CONFIG_DIR` is honoured everywhere: if you point it somewhere else, the installer writes
> there and not in `~/.claude`.

### Installing is not copying: what the installer does per runtime

Every runtime has one file that decides whether the plugin **loads**. Copying files does not touch
it, and without it there are no hooks, no statusline and no command namespace. The installer writes
those files:

| Runtime | What gets copied | What gets **registered** (and where) |
|---|---|---|
| **Claude Code** | with `--mode plugin` nothing is copied into your project: the package goes to the plugin cache | `claude plugin marketplace add` + `claude plugin install` if the CLI is on your PATH; otherwise the same registry written directly: `plugins/known_marketplaces.json`, `plugins/installed_plugins.json` and `enabledPlugins` in `settings.json` (user scope), or `.claude/settings.json` with `extraKnownMarketplaces` (project scope) |
| **Codex** | plugin in `~/.codex/plugins/custom-agents/`, `.toml` agents and prompts | `codex plugin marketplace add` if the CLI is on your PATH (and is ≥ 0.128.0), plus `[plugins."custom-agents@daycry"] enabled = true` and `[features] hooks = true` in the scope's `config.toml`, which is what Codex reads at startup |
| **OpenCode** | agents, commands, skills, kits and the hook adapter under `plugins/` | `plugin: ["./.opencode/plugins/custom-agents-hooks.js"]` in `opencode.json` (absolute path in user scope), appended to whatever you already had |

**The runtime's official CLI is always the preferred route.** The fallback — writing the registry
ourselves — exists because `claude` is not on everyone's PATH (desktop install on Windows, npm shims
Node cannot launch) and without it the installer could not do anything useful. It is each tool's
internal format, so the installer **says** when it uses it and why.

**`--mode copy`** is the old behaviour: the bundle copied into `.claude/`. It is enough to read the
pieces (agents, skills, kits) and to tinker, but Claude Code **does not read `hooks/hooks.json`
outside an installed plugin**: no hooks, no statusline, no `/custom-agents:`. The installer warns
about it when it finishes and `/doctor` flags it ⚠️ (§4).

### Is it actually registered?

```bash
npx @daycry/custom-agents status   # per runtime and scope: manifest + "registered: yes/no"
```

`status` does not trust the manifest: it reads the very files the runtime reads
(`installed_plugins.json` / `enabledPlugins`, Codex's `config.toml`, `plugin` in `opencode.json`).
That is why it can say "registered: yes" with no manifest (you installed it with the runtime's CLI)
and "no" with one (`--mode copy`). For Claude Code it reads `enabledPlugins` in **all four** settings
files of the documented stack (`settings-reference#enabledplugins`: "Scope: Any file") and resolves
them in the order of `settings#settings-precedence` ("Managed > command line > Project local > Shared
project > User"): `managed-settings.json` > `.claude/settings.local.json` > `.claude/settings.json` >
the `settings.json` in your `CLAUDE_CONFIG_DIR`. Looking only at the last two reported "registered:
yes" for a plugin turned off with `claude plugin disable --scope local`. Inside Claude Code, the same with more detail: `/doctor`.

Five guarantees, each with a test in `tests/installer.test.mjs`:

1. **Idempotent** — reinstalling leaves the same tree and duplicates no config entries.
2. **It does not clobber your config** — JSON files are **merged**: whatever already exists wins.
   OpenCode's `permission` is not touched at all (see §4), only reported.
3. **Precisely uninstallable** — every install leaves a `.custom-agents-install.json` (or
   `.custom-agents-install.plugin.json` in plugin mode) with the exact list of files written and the
   registry entries it added; `uninstall` removes that list, undoes those entries and nothing else. A
   file of yours inside one of our folders survives; so does your merged configuration (never deleted).
4. **It degrades** — if one provider fails, the others still install; if a runtime's CLI is missing,
   it does what it can and prints the command left pending.
5. **It does not lie** — any step it could not take shows up in the warnings: never a "done" just
   because files were copied.

### The native routes (no installer)

| Runtime | How |
|---|---|
| **Claude Code** | `/plugin marketplace add daycry/custom-agents` + `/plugin install custom-agents` (that is what `--mode plugin` does). Copying the bundle as the project's `.claude/` (`docs/en/INSTALL.md`) is the equivalent of `--mode copy`: no hooks, no statusline, no namespace. |
| **Codex** | `codex plugin marketplace add daycry/custom-agents` (it reads the repo's `.codex-plugin/plugin.json` and `.agents/plugins/marketplace.json`). The `.toml` agents and the prompts are copied from `interop/codex/` (or the installer places them). |
| **OpenCode** | Copy `interop/opencode/` to `.opencode/` plus `skills/`, `agent-kits/` and `hooks/` inside it. If you already have the Claude Code bundle in `.claude/`, OpenCode **reuses those skills** with nothing copied (native compatibility). |

---

## 2. What gets installed in each runtime

| Plugin piece | Claude Code | Codex | OpenCode |
|---|---|---|---|
| **Skills** (24) | `.claude/skills/` | the plugin's `skills/` (the manifest points there) | `.opencode/skills/` — *or* `.claude/skills/`, which it reads natively |
| **Agents** (10) | `agents/*.md` | `.codex/agents/*.toml` (generated) | `.opencode/agents/*.md` (generated) |
| **Commands** (13) | `commands/*.md` (`/name`) | `~/.codex/prompts/*.md` (`/prompts:name`) | `.opencode/commands/*.md` (`/name`) |
| **Hooks** | `hooks/hooks.json` | `interop/codex/hooks.json` (subset) | `.opencode/plugins/custom-agents-hooks.js` (JS adapter) |
| **Kits** (`agent-kits/`) | `.claude/agent-kits/` | inside the plugin | `.opencode/agent-kits/` |
| **Manifest** (`plugin.json`, where the version comes from) | inside the installed plugin (`.claude-plugin/`) | `.codex-plugin/plugin.json` | `.claude-plugin/plugin.json` — what `/doctor` reads to report the version (with a fallback to Codex's) |
| **Status line** | opt-in in `/setup` | — | — |

Every destination format was verified against each tool's official docs (Codex:
`developers.openai.com/codex` and `learn.chatgpt.com/docs`; OpenCode: `opencode.ai/docs`, both
consulted 2026-09-08). **Skills are not translated**: their frontmatter (`name` + `description`) is
exactly what all three runtimes require.

### How an agent is translated

| Plugin concept | Codex (`.toml`) | OpenCode (frontmatter) |
|---|---|---|
| `description` | `description` | `description` |
| `tools` with Write/Edit | — | `permission.edit: allow\|deny` |
| `tools` without write access (`reviewer`) | `sandbox_mode = "read-only"` | `permission.edit: deny` |
| `effort` (`medium`/`high`) | `model_reasoning_effort` | — |
| `model` (`sonnet`/`opus`) | — *(inherits from the session)* | `temperature` (0.1 / 0.2) |
| prompt body | `developer_instructions` | the `.md` body |

`model` is deliberately **not translated to Codex**: `haiku`/`sonnet`/`opus` have no equivalent among
OpenAI's identifiers, so the agent inherits the session's model and only the reasoning effort — which
*is* portable — travels from the tiering. Full tiering remains a Claude Code feature (`ADR-009`).

Each translated body is prefixed with a four-line **preamble** that translates the only things that
change per runtime: how a skill is invoked, how another agent is delegated to, which guardrail is not
enforced, and where kits are resolved. The original body is untouched.

---

## 3. Path resolution (rule 5 of CONVENTIONS)

Agents and skills locate their kits at runtime with a `find` over **six roots**, two per runtime,
project before user:

```bash
find "$PWD/.claude" "$PWD/.codex" "$PWD/.opencode" \
     "$HOME/.claude" "$HOME/.codex" "$HOME/.config/opencode" \
     -type d -path '*agent-kits/shared' 2>/dev/null | head -1
```

Neither Codex nor OpenCode looks for kits under `.claude/`, so without their roots a plugin installed
in them would find its skills but **not** its toolkit. OpenCode's global directory is
`~/.config/opencode`, **not** `~/.opencode`. If you add a runtime, its root is added to **every**
piece (today 88 occurrences across 56 files) — the `find` is not a styling detail.

---

## 4. Degradation: what does NOT work the same

This table is the honest part of the document. None of it breaks the cycle; everything is either
lost or substituted, and it is stated here.

| Capability | Claude Code | Codex | OpenCode |
|---|---|---|---|
| **Plugin registration** (what makes it load) | ✅ `installed_plugins.json` + `enabledPlugins`, via the CLI or written by the installer — ⚠️ with `--mode copy` there is no registration: the bundle sits in `.claude/` and the runtime never learns about it (`/doctor` flags it) | ⚠️ `enabled = true` in `config.toml` is written by the installer, but the **marketplace** needs `codex plugin marketplace add`: without the CLI on your PATH the command is printed and it stays half-done until you run it | ✅ `plugin` in `opencode.json`; OpenCode also auto-discovers `plugins/*.js` and, per its own code (`deduplicatePluginOrigins` dedupes by file URL), registering it should not load it twice — **still to be confirmed on a real OpenCode** (the initiative's M-01 checklist) |
| On-demand skills | ✅ Skill tool | ✅ `$name` or activation by `description` | ✅ `skill` tool |
| Commands | ✅ `/name` | ⚠️ `/prompt:name` (**or** `/prompts:name`), **only under `~/.codex/`** (Codex has no per-project prompts) and marked *deprecated* by OpenAI in favour of skills | ✅ `/name` |
| Delegating to an agent by name | ✅ Agent tool, with per-invocation `model` | ⚠️ in natural language; Codex **does not auto-invoke** custom agents, you must ask | ✅ `task` tool |
| Progress notice when the ledger is edited | ✅ `PostToolUse` | ✅ `PostToolUse` for `apply_patch`, with paths extracted from the patch | ✅ `tool.execute.after` |
| Context at session start | ✅ `SessionStart` (index + roadmap + journal + memory) | ✅ `SessionStart` (`startup\|resume\|clear\|compact`) | ⚠️ static index in `instructions`; no dynamic session context |
| Session journal | ✅ `SessionEnd`, 5 s timeout | ✅ `SessionEnd`, 3 s timeout, shell-form Node launcher | ⚠️ captures on `session.idle`; materialized through `journal.py replay` |
| Capturing the user's turn | ✅ `UserPromptSubmit` | ✅ `UserPromptSubmit` | ❌ no documented event → the journal keeps its deterministic half (git + ledger) |
| Subagent finished | ✅ `SubagentStop` | ✅ `SubagentStop` | ❌ no equivalent event |
| **Per-agent guard hook** (`implementer`, `architect`) | ✅ real `deny` via the frontmatter's `hooks:` (`ADR-007`) | ❌ no per-agent hook exists → the agent **self-checks** with `guardrail-check.py` (the preamble tells it so and hands it the command) | ❌ same as Codex; `permission` bounds tools, not paths |
| Read-only `reviewer` | ✅ no Write/Edit in `tools` | ✅ `sandbox_mode = "read-only"` | ✅ `permission.edit: deny` |
| Roadmap status line | ✅ opt-in | ❌ | ❌ |
| **Graph memory** (`graphiti` capability, opt-in) | ✅ `/doctor` checks it live through its adapter | ✅ same: the adapter talks HTTP to the endpoint declared in `taxonomy.json`, not to the runtime's MCP | ✅ same; with no context hook, its state only shows up when you run `/doctor` |
| OpenCode's `permission` | — | — | ⚠️ the installer **leaves it alone** when it already exists: OpenCode applies "the last matching rule", so adding `skill: {"*": "allow"}` after a `deny` of yours would open it back up. If you have your own policy, check that the `custom-agents` skills do not fall into a `deny`. |

### Portable hook startup

All three runtimes use `hooks/run-hook.mjs`, requiring Node 18+ (already required by the installer)
and Python 3. On Windows it finds native Python (`python3`, `python` or `py -3`) and Git Bash in PATH;
it excludes System32's WSL launcher. Set `CUSTOM_AGENTS_PYTHON` to select a specific interpreter.
Payloads travel through stdin and are never interpreted as shell code.

SessionEnd and UserPromptSubmit call `journal.py` directly, without Bash. Other hooks run through
Bash with a `python3` adapter for the selected interpreter. Missing tools produce a stderr warning
and exit 0. The implementer and architect guards remain scoped to their agents.

Codex caps SessionEnd at 3 s; the exporter adjusts it while preserving Claude Code's 5 s.
The capture process has an internal 2.2 s limit. OpenCode captures on session.idle and needs manual
replay to materialize the journal. Start a new session after updating a plugin; payload tests do not
replace checking event delivery within each application.
Contracts checked on 2026-10-06: [Codex](https://learn.chatgpt.com/docs/hooks),
[Claude Code](https://code.claude.com/docs/en/hooks), [OpenCode](https://opencode.ai/docs/plugins/).

The three gaps that matter most:

- **Copying the bundle does not install the plugin.** It is the most noticeable gap and the easiest
  to miss: with `--mode copy` (or copying `.claude/` by hand) the whole bundle is there and none of
  the three things an installed plugin gives you are — hooks, statusline and the `/custom-agents:`
  namespace — because Claude Code only reads `hooks/hooks.json` inside a plugin. `/doctor` says so
  in the "hooks registrados" row (⚠️, not ✅) and `status` in "registered: no".

- **The `implementer` guardrail is not enforced outside Claude Code.** It is a `PreToolUse` `deny`
  scoped to a single agent, and that only exists here. In Codex and OpenCode the agent is instructed
  to check it itself (`guardrail-check.py pre-tool --agent implementer`) before a destructive git
  command or before writing into `docs/roadmap/` outside `tasks.md`. That is a prompt rule, not a
  barrier: in those runtimes, review the diff.
- **Events differ across runtimes.** Codex supplies apply_patch changes in `tool_input.command`;
  the launcher converts them to `edits[].file_path` for the shell hooks. Linter notices are wrapped
  in `systemMessage`, which OpenCode can also display.

---

## 5. Keeping it in sync

```bash
python3 scripts/export-interop.py            # regenerate the 48 interop files
python3 scripts/export-interop.py --check    # do they reflect the repo's pieces? (CI and release.py)
python3 scripts/export-interop.py --list     # which files it generates
python3 -m pytest -q tests/test_export_interop.py
node --test "tests/*.test.mjs"                # installer + hook adapter
```

> **Is it installed correctly?** `/doctor` diagnoses the **Claude Code** installation (it is a
> plugin command and runs inside it). For Codex and OpenCode the equivalent is
> `npx @daycry/custom-agents status`, which reads each install's manifest.

**When you touch an agent, a command or a hook, regenerate.** `--check` is a `release.py` gate, so an
out-of-sync interop never ships. Generated files carry a "GENERADO" header and their source path; if
you find yourself editing a file under `interop/`, you are editing the copy.

When adding a new piece, the one thing to remember: **a skill's `description` cannot exceed 1,024
characters** (OpenCode validates it and, past that, the skill does not load). The linter warns and
`tests/test_export_interop.py` fails.

| File | What it is |
|---|---|
| `scripts/export-interop.py` | the generator (stdlib only, deterministic, `--check`) |
| `install/install.mjs` · `install/providers.mjs` | the installer (`npx`, zero dependencies) |
| `hooks/opencode-plugin.js` | **source** of OpenCode's hook adapter (the copy travels to `interop/`) |
| `.codex-plugin/plugin.json` · `.agents/plugins/marketplace.json` | Codex manifests (generated) |
| `interop/codex/` · `interop/opencode/` | translated trees (generated) |
| `tests/test_export_interop.py` · `tests/installer.test.mjs` · `tests/opencode-plugin.test.mjs` | the gates |


## Brief budget

The task brief caps design at 1,600 characters, review gaps at 1,600 and verification at 800. It includes the selected design only for matching task paths and links historical execution evidence to the ledger. Current requirements, decision notes and acceptance criteria remain complete. Optional sections share the remaining global budget before persona allocation. If the protected minimum exceeds 10,000 characters, the generator reports its exact size; split the task before delegation. Memory and persona limits and the return contract retain their existing rules.
