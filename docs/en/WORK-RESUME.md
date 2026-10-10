# Resume an initiative or session

**English** · [Español](../WORK-RESUME.md)

`/work-resume` shows where to continue using the current ledger and local journal.
`progress-report.py resume` composes the view; `journal.py` selects the history.
Both use the bounded local reader. The view does not change the project.

## How to select the work

Use the command form offered by your installation: `/custom-agents:work-resume`
in Claude Code plugin mode, the exported prompt in Codex, or `/work-resume` in OpenCode.
They share the command body and contracts. The command starts no team or cycle.

```text
/work-resume --initiative 2026-01-01-demo
/work-resume --initiative demo --session-id sesion-demo --runtime codex
/work-resume --entry 2026-01-01-demo.md --json
```

| Option | Selection |
|---|---|
| `--root` | Explicit project root for the script; the command uses the working project. |
| `--initiative` | Exact dated folder under `docs/roadmap/`, or a unique slug. Duplicate slugs require an exact folder choice. |
| `--session-id` | Equality with the full journal ID. Prefixes are not aliases. |
| `--runtime` | Explicit `claude`, `codex` or `opencode` filter. An older entry without a runtime remains unknown. |
| `--entry` | Exact Markdown filename under `docs/knowledge/journal/`; external paths are rejected. |
| `--json` | Structured projection with the same states and notices as the text view. |

Combined filters must agree. A missing, invalid or ambiguous explicit file or ID
never falls back to the latest entry. Selection compares original data before
sanitizing and redacting output. Candidate identities may be shortened for display;
that shortened text does not prove the original value.

Without filters, the resolver uses a single initiative with state `en-progreso`.
Multiple active initiatives produce an ambiguous selection. No active initiative
means a missing selection, even if other initiatives have global history.

## Which source determines current state

The first part shows the initiative, phase and tasks from the current `tasks.md`.
That ledger remains authoritative for work state. The second part shows the journal's
date, session, source, closure and available content.

Historical decisions and pending items are **quotations**, not instructions.
An older session cannot prove a task is still open or has passed QA. The view does
not invent objectives, failures, blockers or next steps absent from the schema.
The user chooses the next action after reading it.

| State | Meaning |
|---|---|
| Missing | A complete read found no matching entry. |
| Empty | The directory is valid but supplies no substantive history entries. |
| Ambiguous | Multiple folders or entries match the identity; select an exact candidate. |
| Unreadable | The reader could not access or decode the file; this does not mean it is missing. |
| Malformed | The content fails the validated entry format. |
| Incomplete | A limit or read problem prevents a complete search; absence and global recency are unconfirmed. |

## Read and output limits

The reader limits each directory to **128 names** and each file to **256 KiB**.
Roadmap and history have separate **1 MiB budgets per corpus**
(up to 2 MiB combined). A shortened scan is reported as incomplete. The text dossier
allows **32 lines and 6,000 characters**; JSON allows **12,000 bytes**.
These are compositor limits, with no CLI options to raise or lower them.
Notices retain the reason when the projection is shortened.

Read bytes also consume the budget when decoding fails or the path changes.
A failure during reading charges the full allocation; growth detection allows
one additional probe byte per file.

The reader rejects symbolic links and junctions along the path. It allows supported
cloud-file markers, checks identity before reading and bounds bytes. These checks
are not an atomic sandbox against concurrent filesystem changes. Nor does the view
certify writer identity: a legacy entry without runtime cannot prove its capturing runtime.

The reader validates the writer's flat frontmatter. Text is written as quoted
strings with JSON escapes; simple legacy text without YAML indicators or typed
values is accepted. General YAML, nested maps, aliases and blocks are not interpreted.

## What the command runs

Opening the view neither replays events nor restores a backup. The
[local recovery contract](../roadmap/2026-10-07-catalog-capabilities/comparisons/memory-local-recovery-contract.md)
defines capture confirmation and the evidence required to recover pending sessions.

It runs only the Python compositor. It uses no meter, replay/recover, Git, backends,
network or materialization processes, and reads no raw transcripts to fill gaps.
Automatic capture and recovery retain their own hook contracts. At startup/resume,
`SessionStart` uses `resume --history-only` to select history through the same ledger
resolver; compact omits that part. The progress and replay blocks remain separate.
This view does not make the entire `SessionStart` hook read-only.

The facade finds `agent-kits/shared/` through the six roots in
[CONVENTIONS §5](CONVENTIONS.md). Options and values are separate arguments;
user text is never interpolated into shell code. Partial installs report the missing
resource and preserve the requested selection.

`/work-context` selects guides and extensions for a task. `/roadmap-status` displays
the portfolio. `/work-resume` provides continuity from existing records without
adding a skill, store or execution workflow.
