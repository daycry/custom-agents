# Interoperability — Claude Code, Codex and OpenCode

**English** · [Español](../INTEROP.md)

## Modular architecture and project integrations

Core works with local `tasks.md` and `docs/`. Functions are bound in project `.claude/integrations.json`; Jira and Confluence are optional adapters. Projects can add Redmine, a wiki or other providers without changing core. A declaration neither connects accounts nor authorizes external effects.

The versioned `agent-kits/shared/modules.json` catalog resolves profiles and dependencies. Portable export and profiled Claude copies filter files; native plugins remain complete bundles. Shared caches are not modified to simulate per-project installation.

The [complete handbook](CUSTOMIZATION.md) details workflows, agents, commands, skills, tools, settings, artifacts, gates, Atlassian/Redmine examples and recovery. Provider-specific sections below describe optional adapters rather than core requirements. This update includes contract changes for the next major version; see [migration and limits](guides/operations.md).

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


### Local models per agent (project opt-in)

Create a consumer JSON file, either `.claude/dev.json` or a separate file:

```json
{"modelos":{"implementer":{"model":"ollama/qwen3:32b"}}}
```

```bash
npx @daycry/custom-agents install -p codex --models-config .claude/dev.json
npx @daycry/custom-agents install -p opencode --models-config .claude/dev.json
```

`--models-config` requires Python 3 and a regular file inside the project (maximum
256 KiB, no links). The manifest remembers this path for subsequent installations;
model configuration is never discovered by default. Invalid input or a missing
remembered file stops that provider before writing. Set `"modelos": {}` and
reinstall to restore inherited models. The JSON file remains yours.

| Runtime | Effective projection |
|---|---|
| Codex | `model = "qwen3:32b"` in the owned agent and `agents.<id>.config_file` in project config. The provider is inherited from the parent session: launch Codex with Ollama configured for that session; the installer does not configure providers or authentication. |
| OpenCode | `model: "ollama/qwen3:32b"` in the owned agent. Configure its native provider separately. |
| Claude Code | Existing Claude aliases/ids and behavior remain; Ollama ids are not passed to the Agent tool. |

Owned ids, instructions and permissions are retained; canonical `interop/` files
and the plugin payload in the native cache are not personalized. Official
reinstallation may update its cached installation manifest. Foreign or edited agents and bindings
are preserved with a warning and incomplete status. A conflict may release the
preserved agent from the inventory: uninstall then leaves that copy alone. An
unchanged owned binding is undone during uninstall, preserving other fields and
consumer edits. Installation steps do not form a global transaction.

Claude effort is not mapped to local models. Codex omits
`model_reasoning_effort` unless explicitly overridden; check model support.
OpenCode warns when effort is declared and does not project it: configure its
native variant. Model names do not establish quality or context capacity.

To inspect without installing or modifying `interop/`:

```bash
python scripts/export-interop.py --model-config .claude/dev.json --runtime codex --projection-json
python agent-kits/shared/model-tier.py implementer --runtime codex --json
```

The exporter returns JSON containing content and hashes without writing files.
The resolver accepts `--project` to read another project and also supports
`--runtime opencode`; the default remains Claude. Canonical `--check` stays
independent of consumer configuration.


### Local model context in doctor

Run the located kit's `doctor.py --runtime codex` or `--runtime opencode`.
It reads project config and owned agents; invisible user settings and CLI
overrides are not inferred. Codex TOML needs Python 3.11; OpenCode supports strict
JSON (JSONC is reported as unverifiable). Default Claude behavior is preserved.

Output distinguishes `declarado` (declared), `observado` (observed), and
`desconocido` (unknown). Values below **65,536 tokens** or unknown trigger a warning
with a remedy; they do not establish model capacity or a session's effective
context. Codex inherits its provider from the parent. OpenCode aliases with an
explicit `modelID` are matched against that native id when probing.
Codex 0.166 does not apply `model_context_window` from a role TOML and may reset
the parent's window when starting a child: child context stays unknown until
separately observed, without assuming that inheritance.

| Advisory tier | Scope |
|---|---|
| 8–9B | Bounded reading/query tasks; autonomous editing and a universal minimum context are not certified. |
| 32B with context >=65,536 | Candidate for the quick path with lite; real model testing and every quality gate still apply. |

Configuration does not prove model size or quality: these tiers come from the
plan and remain subject to manual validation on the other machine.
To inspect models already loaded on the server, explicitly request:

```bash
python "$DOC" --runtime codex --probe-ollama http://127.0.0.1:11434 --json
```

The probe only performs GET `/api/ps`; it does not load or download models.
It accepts HTTP on numeric loopback or `localhost` pinned to 127.0.0.1, without
external DNS, proxies, credentials, URL parameters or redirects. Headers and body
share a two-second deadline, with 16 KiB/256 KiB limits. Compressed or chunked,
ambiguous, corrupt or incomplete replies produce warnings. An observation is
about the server at that instant; it does not prove the client's context.
There are no new network calls by default or from hooks.

Sources checked 2026-10-30: [Ollama /api/ps](https://docs.ollama.com/api/ps),
[OpenCode V2 models](https://opencode.ai/v2/docs/models/). Codex's
`model_context_window` and [role field application](https://github.com/openai/codex/blob/6ff1e1ca3b30fc8b914720681fcf5fe62e95f856/codex-rs/core/src/agent/role.rs)
were checked in local CLI 0.166.0 source; Claude aliases do not establish a native
model mapping.

### Installing is not copying: what the installer does per runtime

Every runtime has one file that decides whether the plugin **loads**. Copying files does not touch
it, and without it there are no hooks, no statusline and no command namespace. The installer writes
those files:

| Runtime | What gets copied | What gets **registered** (and where) |
|---|---|---|
| **Claude Code** | with `--mode plugin` nothing is copied into your project: the package goes to the plugin cache | `claude plugin marketplace add` + `claude plugin install` if the CLI is on your PATH; otherwise the same registry written directly: `plugins/known_marketplaces.json`, `plugins/installed_plugins.json` and `enabledPlugins` in `settings.json` (user scope), or `.claude/settings.json` with `extraKnownMarketplaces` (project scope) |
| **Codex** | bundle under the scope's `.codex/plugins/custom-agents/`, `.toml` agents and command adapters | cache through `codex plugin add` (CLI ≥ 0.161.0); register `marketplaces.daycry`, `plugins."custom-agents@daycry".enabled` and `features.hooks` in the scope config after success |
| **OpenCode** | agents, commands, skills, kits and the hook adapter under `plugins/` | `plugins: ["./.opencode/plugins/custom-agents"]` in `opencode.json` (absolute path in user scope), appended to whatever you already had |

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
(`installed_plugins.json` / `enabledPlugins`, Codex's `config.toml`, `plugins` in `opencode.json`).
That is why it can say "registered: yes" with no manifest (you installed it with the runtime's CLI)
and "no" with one (`--mode copy`). For Claude Code it reads `enabledPlugins` in **all four** settings
files of the documented stack (`settings-reference#enabledplugins`: "Scope: Any file") and resolves
them in the order of `settings#settings-precedence` ("Managed > command line > Project local > Shared
project > User"): `managed-settings.json` > `.claude/settings.local.json` > `.claude/settings.json` >
the `settings.json` in your `CLAUDE_CONFIG_DIR`. Looking only at the last two reported "registered:
yes" for a plugin turned off with `claude plugin disable --scope local`. Inside Claude Code, the same with more detail: `/doctor`.

Codex separates declared scope configuration from the CLI's view in the
current project. `status` and `/doctor` share a bounded reader for
`codex plugin list --marketplace daycry --available --json`; it filters out
other entries, source paths and private errors. Missing CLI or an unsupported
response leaves native state unknown. An enabled installation establishes
neither hook-hash trust nor execution; inspect a native session for evidence.

For project scope, `plugin add` uses a temporary `CODEX_HOME` with a regular
copy of user configuration and a link limited to the `daycry` cache namespace.
Its setter changes that copy; project activation follows installation success.
Two projects retain their own sources without changing the user's marketplace
or global enabled preference. Version cache remains shared; updating it can
change content used by other projects. Source conflicts require
`--force-marketplace`. Relative paths that cannot be preserved in the snapshot
are rejected, with no retry against the real home. Neither `plugin remove`
rollback nor forced cache `chmod` is used.

Uninstall restores each source key only while it still holds the value
written by the installer; later edits and other fields remain intact.
Plugin activation becomes disabled without switching off `features.hooks`
or deleting shared cache. Native installation failure leaves a pending
manifest step and does not declare activation. Snapshot path validation
distinguishes native fields and scopes; an MCP environment variable called
`config_file` is not a runtime path.

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
| **Codex** | `codex plugin marketplace add daycry/custom-agents` followed by `codex plugin add custom-agents@daycry`. This native route enables the plugin in user config. Use the installer to preserve that preference for project installation. |
| **OpenCode** | Copy `interop/opencode/` to `.opencode/` plus `skills/`, `agent-kits/` and `hooks/` inside it. If you already have the Claude Code bundle in `.claude/`, OpenCode **reuses those skills** with nothing copied (native compatibility). |

---

## 2. What gets installed in each runtime

| Plugin piece | Claude Code | Codex | OpenCode |
|---|---|---|---|
| **Canonical skills** | `.claude/skills/` | the plugin's `skills/` (first manifest root) | `.opencode/skills/` — *or* `.claude/skills/`, which it reads natively |
| **Agents** (10) | `agents/*.md` | `.codex/agents/*.toml` (generated) | `.opencode/agents/*.md` (generated) |
| **Canonical commands** | `commands/*.md` (`/name`) | adapters in the plugin's `interop/codex/command-skills/` (`$custom-agents:custom-agents-<name>`) | `.opencode/commands/*.md` (`/name`) |
| **Hooks** | `hooks/hooks.json` | `interop/codex/hooks.json` (subset) | `.opencode/plugins/custom-agents` (JS adapter) |
| **Kits** (`agent-kits/`) | `.claude/agent-kits/` | inside the plugin | `.opencode/agent-kits/` |
| **Manifest** (`plugin.json`, where the version comes from) | inside the installed plugin (`.claude-plugin/`) | `.codex-plugin/plugin.json` | `.claude-plugin/plugin.json` — what `/doctor` reads to report the version (with a fallback to Codex's) |
| **Status line** | opt-in in `/setup` | — | — |

Every destination format was verified against each tool's official docs (Codex:
`developers.openai.com/codex` and `learn.chatgpt.com/docs`; OpenCode: `opencode.ai/docs`, both
consulted 2026-09-08). **Skills are not translated**: their frontmatter (`name` + `description`) is
exactly what all three runtimes require.

### Native command transport in Codex

The manifest declares two roots: `./skills/` for canonical capabilities and
`./interop/codex/command-skills/` for generated adapters. Invoke
`$custom-agents:custom-agents-dev-cycle <arguments>` or select the adapter in
`/skills`. The adapter prefix avoids collisions with capabilities such as
`confluence-pull`. Its map requires reading the complete `references/command.md`
before acting; canonical bodies and shell recipes remain literal. Arguments come
from the invoking user message, without prompt-composer substitution.

Metadata declares `allow_implicit_invocation: false`. An isolated Codex0.161.0
probe establishes discovery of both roots; body injection used a separate
fixture. Neither alone proves reference reading, workflow execution or policy
enforcement. Upgrades preserve old personal prompts and release their installer
manifest ownership; they do not delete them. Installation writes no new global prompts.

### How an agent is translated

| Plugin concept | Codex (`.toml`) | OpenCode (frontmatter) |
|---|---|---|
| `description` | `description` | `description` |
| `tools` with Write/Edit | — | Rule in `permissions`: `action: edit`, `resource: "*"`, `effect: allow` |
| `tools` without write access (`reviewer`) | Prompt responsibility; permissions inherited from parent | Rule in `permissions` with `action: edit` and `effect: deny` for edit tools |
| `effort` (`medium`/`high`) | `model_reasoning_effort` | — |
| `model` (`sonnet`/`opus`) | — *(inherits from the session)* | Inherits the native model and generation settings; Claude tiers are not mapped to temperatures |
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
| **Plugin registration** (what makes it load) | ✅ `installed_plugins.json` + `enabledPlugins`, via the CLI or written by the installer — ⚠️ with `--mode copy` there is no registration: the bundle sits in `.claude/` and the runtime never learns about it (`/doctor` flags it) | Native CLI ≥0.161.0: cache validated before declaring marketplace and activation. Project mode prepares registration in a private `CODEX_HOME` and writes local configuration; `status` and `/doctor` distinguish declaration, native listing and execution | V2 local package in `plugins` of `opencode.json`; `status` and `/doctor` check the declaration, not execution |
| On-demand skills | ✅ Skill tool | ✅ `$name` or activation by `description` | ✅ `skill` tool |
| Commands | ✅ `/name` | Explicit native adapter `$custom-agents:custom-agents-<name>`; arguments from the message, inside the scope's plugin | ✅ `/name` |
| Delegating to an agent by name | Agent with `subagent_type: custom-agents:<role>` | `spawn_agent` with `agent_type: custom-agents-<role>`; the model decides when to delegate | V2 `subagent` with `agent: custom-agents-<role>` |
| Progress notice when the ledger is edited | ✅ `PostToolUse` | ✅ `PostToolUse` for `apply_patch`, with paths extracted from the patch | ✅ `tool.execute.after` |
| Context at session start | ✅ `SessionStart` (index + roadmap + journal + memory) | ✅ `SessionStart` (`startup\|resume\|clear\|compact`) | Native `session.context` hook: current index, roadmap, journal and memory in outgoing context |
| Session journal | `SessionEnd`: isolated canonical capture; headless evidence without extending the native budget, with documented startup limits | `SessionEnd`: 3 s export and canonical capture; verified by archiving the active thread in the same app-server | `session.execution.succeeded/failed/interrupted`; canonical capture and bounded replay on the next context |
| Capturing the user's turn | ✅ `UserPromptSubmit` | ✅ `UserPromptSubmit` | `session.prompt`, before admission: provisional request with `<private>` exclusion |
| Subagent finished | ✅ `SubagentStop` | ✅ `SubagentStop` | ❌ no equivalent event |
| **Tool events** (Live agents, opt-in `sesion.actividad`) | `PostToolUse` + `PostToolUseFailure`, `async`: duration (`duration_ms`), `ok`/`error` result and identified subagent (`agent_id`/`agent_type`) | `PostToolUse` `async` (the activity group keeps its matcher; no `PostToolUseFailure`). **Does not identify the subagent** in tool events: they are grouped by session. No duration; result "sin datos" (no data). Hosted web searches emit no events; MCP tools run synchronously (a single attempt without waiting) | `tool-activity` binding on `tool.execute.after`, without waiting for the child: `status` → `ok`/`error`, `agent` and the session's `sessionID` (a child session for a subagent). No duration. **Not validated in a real OpenCode V2**: if V2 brings no `sessionID` the event is discarded (`invalid_identity`), and without `agent` the role stays empty. An older adapter without the binding emits no tool events |
| **Per-agent guard** (`implementer`, `architect`) | Global `PreToolUse` dispatcher selects owned IDs; plugin agent `hooks:` is ignored | `PreToolUse` dispatcher selects owned IDs | V2 `tool.execute.before` selects owned IDs; final validation for all three runtimes remains in the roadmap |
| Read-only `reviewer` | No Write/Edit; Bash remains subject to permissions and role responsibility | Role TOML does not impose an independent sandbox; inherits parent permissions | An `edit` rule with effect `deny` in `permissions`; does not prohibit every possible write through a shell |
| Roadmap status line | ✅ opt-in | ❌ | ❌ |
| **Graph memory** (`graphiti` capability, opt-in) | ✅ `/doctor` checks it live through its adapter | ✅ same: the adapter talks HTTP to the endpoint declared in `taxonomy.json`, not to the runtime's MCP | Same opt-in adapter; installing activates no backend |
| OpenCode permissions | — | — | The installer preserves `permission`/`permissions` and adds no global grants. |

### Agent identity and upgrades

Canonical agents remain `agents/<role>.md`. Native exports use
`.codex/agents/custom-agents-<role>.toml` and
`.opencode/agents/custom-agents-<role>.md`; generated commands and session context
use the same IDs from `agent-kits/shared/native-roles.json`. Consumer agents with
other IDs keep their normal permissions. An ID identifies a role to the runtime,
but does not prove prompt provenance: redefining an exact plugin ID may still
make its operations subject to role guards.

The installer checks known project/user agent directories and configurations.
It preserves foreign or modified files, links and ambiguous references, marking
conflicts as incomplete installation. An old unprefixed export is removed only
when owned by the prior manifest, matching the published hash and lacking bindings
within a regular Git repository boundary. Global old copies, worktrees using a
`.git` file and unverifiable references are preserved with diagnostics. It does
not scan other projects. Uninstall also preserves later edits to owned agents.
OpenCode file references are checked throughout the configuration, including
commands, instructions and keys. Unverifiable `~/` paths or environment
substitutions preserve agents with diagnostics; the installer does not read
secrets to resolve those references.
Markdown commands in known configuration layers also preserve old agents: the
installer does not interpret their frontmatter to authorize deletion. Its
diagnostic identifies the need to check those references before manual removal.

Guards evaluate all supported mutation targets, including move sources and
destinations. Claude supports Write/Edit/MultiEdit/NotebookEdit and Bash/PowerShell
command rules; Codex supports `apply_patch` and commands emitted as Bash; OpenCode
V2 supports write/edit/patch/shell (`path`, `oldString`/`newString`, `patchText`).
Unrecognized input or input above 64 KiB continues with diagnostics; arbitrary
indirect shell/MCP writes are not comprehensively inspected.

Branch lookup also recognizes symbolic HEAD before the first commit: main/master
remains protected and a feature retains branch-switch rules. The fallback uses
only the remaining budget; missing Git and errors retain existing diagnostics.

Native evaluation has a 4.5 s internal budget; Claude/Codex before-tool registrations
declare 10 s and OpenCode waits up to 10.5 s including startup and cleanup. The
first 5 s registration discarded a valid deny because of total Windows latency;
failed evidence is retained. Final matrix acceptance is in the
[ledger](../roadmap/2026-10-07-catalog-capabilities/tasks.md), with the decision in
[design](../roadmap/2026-10-07-catalog-capabilities/design.md).

### OpenCode V2 transport

The adapter ships as `.opencode/plugins/custom-agents/` with `index.js` and `package.json`,
using native `session`, `tool` and `event` domains. The context hook injects at most 10,000
characters without changing persisted history. It checks the actual session location
before reads or writes; events from other projects or workspaces are discarded.
Informational hooks warn on failure and continue.

Write notifications use normalized targets and original paths from the native
diff, so moving a document preserves its deletion notification. Read-only
continuations reuse context in an ephemeral cache for one session, for at most
30 seconds. Prompts, completed tools that may change state, and execution ends
invalidate it; reuse first compares configuration, logs/queue, roadmap and memory
metadata. Links, errors, oversized trees or a custom queue disable caching. The
shared service still composes context. Cleanup aborts the subscription, terminates
owned processes and waits for them to close.

The journal keeps its shared policy: capture only in projects with `docs/roadmap`,
`docs/knowledge` or `.claude/dev.json`, respecting session and turn opt-outs. V2 local
streams omit `location`; `session.get` verifies project and workspace before writing.
Events carrying a foreign location are discarded.

An update retires the old file only when it matches a known copy (including CRLF/LF
variations) and removes only its owned references. Modified copies are preserved with a
pending migration warning. Consumer instructions and permissions are preserved. The
static index remains consultable; V2 does not load it through `instructions`.

Contract: [V2 plugins](https://opencode.ai/v2/docs/build/plugins/) and
[V1 migration](https://opencode.ai/v2/docs/build/plugins/migrate-v1), verified on 2026-10-08.
Native guard validation across all three runtimes remains open in the roadmap.

### Reviewing Codex hooks after an update

`plugin contents changed; hook approval required` means Codex skipped the hook
because installed contents differ from the approved snapshot. Approval covers
the hook definition and plugin bundle; an update can require review even if
that command did not change. Installing or enabling a plugin does not trust its hooks.

In CLI 0.166.0, open `/hooks`, press Enter on the event and select a handler.
Review its source and command; `t` trusts the selected entry. Enter or Space
only toggle already reviewed hooks: they do not enable one awaiting review.
On the event list, `t` applies to all pending entries, including other plugins;
review that scope before using the action.

Codex uses `statusMessage` as the visible name. The exporter adds labels to owned
launchers and preserves explicit labels. An older installation can show
“Unnamed hook” until its bundle is updated and a new session starts. Changing
these labels also changes the definition requiring review. Labels do not grant
trust or change commands, permissions or timeouts.

Verified through native `hooks/list`: names, sources and trust status; this does
not establish Desktop UI behavior. If Desktop cannot review an entry, the CLI
provides the browser above for the same user and configuration. Do not rewrite
trusted hashes to silence the warning.
Contract checked on 2026-10-30: [hook review](https://learn.chatgpt.com/docs/hooks#review-and-trust-hooks).

### Portable hook startup

All three runtimes use `hooks/run-hook.mjs`, requiring Node 18+ (already required by the installer)
and Python 3. On Windows it finds native Python (`python3`, `python` or `py -3`) and Git Bash in PATH;
it excludes System32's WSL launcher. Set `CUSTOM_AGENTS_PYTHON` to select a specific interpreter.
Payloads travel through stdin and are never interpreted as shell code.

SessionEnd invokes canonical `journal-capture.py` with isolated Python (`-I -S`);
the before-tool guard also uses isolated Python without Bash. UserPromptSubmit
invokes `journal.py capture`, without Bash. Other hooks run through
Bash with a `python3` adapter for the selected interpreter. Missing tools produce a stderr warning
and exit 0. The implementer and architect guards remain scoped to their agents.

The three PostToolUse handlers check recognized paths before starting dependencies.
Code edits skip documentation business code; specs and designs skip tasks.md lint
and progress. Script patterns and exclusions remain unchanged. Incomplete or
unknown input and multiline paths keep the existing execution path. Handlers
remain independent.

Codex caps SessionEnd at 3 s; the exporter adjusts that timeout. Claude Code has
1.5 s by default even though this plugin declares 5 s. The internal child deadline
is 800 ms in Claude and 2,200 ms in Codex/OpenCode, selected by a literal adapter
argument. Timeout waits for child-tree closure. Final headless Claude 2.1.287 and
Codex 0.161.0 fixtures verify capture and closure; they establish no universal latency,
TUI exit or functional guard guarantee. OpenCode V2 captures on execution end and materializes
with bounded replay in the next `session.context`. Start a new session after updating a plugin; payload tests do not
replace checking event delivery within each application.
Contracts checked on 2026-10-08; evidence in [roadmap contracts](../roadmap/2026-10-07-catalog-capabilities/contracts.md): [Codex](https://learn.chatgpt.com/docs/hooks),
[Claude Code](https://code.claude.com/docs/en/hooks), [OpenCode](https://opencode.ai/docs/plugins/).

The three gaps that matter most:

- **Live agents does not see the same in every runtime.** Codex documents no subagent identifier in
  `PreToolUse`/`PostToolUse` (only in `SubagentStart`/`SubagentStop`; subagents use the parent's
  `session_id`) and no duration: its events are grouped by session and the page says so ("Codex no
  identifica el subagente en eventos de herramienta: se agrupan por sesión"). Source:
  [Codex hooks](https://learn.chatgpt.com/docs/hooks) (redirect from developers.openai.com/codex/hooks), checked on 2026-10-16.
  OpenCode V2 has not been validated in a real runtime for tool events.

- **Copying the bundle does not install the plugin.** It is the most noticeable gap and the easiest
  to miss: with `--mode copy` (or copying `.claude/` by hand) the whole bundle is there and none of
  the three things an installed plugin gives you are — hooks, statusline and the `/custom-agents:`
  namespace — because Claude Code only reads `hooks/hooks.json` inside a plugin. `/doctor` says so
  in the "hooks registrados" row (⚠️, not ✅) and `status` in "registered: no".

- **Guards depend on loading and scope.** The dispatcher selects owned IDs from native
  metadata and uses the central policy. Unknown tools, incomplete input and errors
  degrade; arbitrary shell/MCP requires runtime permissions. The final native matrix
  remains open in the roadmap; launcher tests do not replace it.
  The launcher collects a bounded structured result before delivering the decision.
  A missing or invalid evaluation emits `systemMessage` in Claude/Codex and a
  structured diagnostic in OpenCode, retaining normal permissions. A complete
  denial is retained even if evaluator termination or cleanup confirmation later
  fails. This does not establish a fix for startup under load.
- **Events differ across runtimes.** Codex supplies apply_patch changes in `tool_input.command`;
  the launcher converts them to `edits[].file_path` for the shell hooks. Linter notices are wrapped
  in `systemMessage`; OpenCode V2 stores them in `result.metadata.customAgentsMessages`,
  preserving tool content without promising a UI toast.

---

## 5. Keeping it in sync

```bash
python3 scripts/export-interop.py            # regenerate the interop files
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

Project and user extensions use the shared `project-pieces.py` reader with native
sources and references; it does not convert formats or infer loading, connection
or permissions. See the [extension guide](PROJECT-EXTENSIONS.md). Pass the current
runtime and inventory roots to the brief; extension references occupy at most
1,000 characters within its auxiliary budget. The plugin does not generate or
adopt project pieces (cancelled on 2026-10-27, see [specialization](SPECIALIZATION.md)).

The task brief caps design at 1,600 characters, review gaps at 1,600 and verification at 800. It includes the selected design only for matching task paths and links historical execution evidence to the ledger. Current requirements, decision notes and acceptance criteria remain complete. Optional sections share the remaining global budget before persona allocation. If the protected minimum exceeds 10,000 characters, the generator reports its exact size; split the task before delegation. Memory and persona limits and the return contract retain their existing rules.
