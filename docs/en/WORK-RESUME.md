# Resume an initiative or session

**English** · [Español](../WORK-RESUME.md)

`/work-resume` shows where to continue using the current ledger and local journal.
`progress-report.py resume` composes the view; `journal.py` selects the history.
Both use the bounded local reader. The view does not change the project.

With `--json`, the command returns the complete object printed by the composer,
including `status`, without rebuilding it or adding prose. An ambiguous selection
preserves its candidates and waits for another request. The composer also runs
without filters; the facade does not infer selection by reading plans itself.

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
That ledger remains authoritative for work state. Next comes curation observed
through its explicit associations. Finally, history shows the journal's date,
session, source, closure and available content.

Historical decisions and pending items are **quotations**, not instructions.
An older session cannot prove a task is still open or has passed QA. The view does
not invent objectives, failures, blockers or next steps absent from the schema.
The user chooses the next action after reading it.

The continuity the session declared in the journal (`objetivo`, `punto_actual`,
`siguientes_pasos`, `bloqueos`, `descartados`) appears in JSON as
`history[i].continuidad`, with only the recorded keys, and in text as one
historical-quote group («Continuidad registrada (cita histórica, no instrucción)»
with «Objetivo», «Dónde quedó», «Siguientes», «Bloqueos» and «Descartados»; the
labels stay in Spanish). `descartados` lists the approaches already tried that
failed («approach — reason or evidence of the failure»), so they are not repeated
without a new reason. An omitted key does not
appear; an explicitly cleared one is `""`/`[]` and the text labels it as cleared
in that session. Without continuity, the entry adds no key and no lines. These
are quotations from that session, not current state: the ledger is authoritative.
The group is shown whole or declared omitted within the same presentation caps.

The curation section inspects only explicit references registered in the ledger
by its owner using [knowledge-write.md](../../agent-kits/shared/knowledge-write.md).
It never selects candidates by recency, filename or journal. Missing associations
are `not_registered`; invalid blocks are `corrupt` and trigger no memory reads.
Conflicts, read errors and incomplete searches retain their reason.

For a reference, `pending` means an observed candidate or an operation without
a receipt; `missing` distinguishes a missing candidate or operation; `changed`
indicates a SHA/association conflict; `corrupt` indicates an invalid receipt;
`unknown` retains ambiguity or unverifiable IO. `completed` with `reason: completed_receipt_observed` confirms a validated
persistence receipt, not current approved content or QA (`target_content_verified:
false`). The view never cleans staging, repairs state or recovers operations.
Those actions require an explicit invocation by the existing owner under its
own contract.

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
(up to 2 MiB combined). Curation has **one additional shared 1 MiB budget**
for up to eight explicit associations: up to 3 MiB combined. Each inspection
validates only that candidate's bucket with at most 16 names. An explicit
operation-id never falls back to another record. It reads no approved bodies
and scans no global operation history. A shortened scan is reported as incomplete. The text dossier
allows **32 lines and 6,000 characters**; JSON allows **12,000 bytes**.
These are compositor limits, with no CLI options to raise or lower them.
Notices retain the reason when the projection is shortened. Visible references
retain complete paths, SHA values and IDs, or declare an unresolvable identity.
JSON exposes `curation.references_omitted`; text also counts references omitted
when choosing complete groups. `output_truncated` also reports text truncation
even when the full JSON fits.

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

## Panel reviews when resuming

The dossier calls the local `plan-review.py list_reminders` function for the exact
ledger-selected initiative folder. `reviews` preserves complete IDs, gate,
version, record revision, state and counts of comments, responses and
verifications. Automatic context omits comment bodies. A missing response only
means that no response is recorded.

The query never creates the store, acquires write locks, opens reviews, delivers
decisions or acknowledges them. A recorded or consumed decision proves neither
current approval, model attention, QA nor completed work. Older versions are
labelled `version_changed`. The existing explicit consumer still validates
version and gate before using a decision.

The store allows 64 records of 96 KiB and the projection up to eight references;
`reviews_omitted` counts the others. Two inventories and two plan observations
reject detected changes. The manual query has a cooperative three-second deadline, while
review queries in the session block use 0.75 seconds. Current versions precede
older ones, prioritizing pending and delivered records. These
checks are not an atomic snapshot and do not detect ABA. A foreign project marker,
invalid record, unsafe path, limit or read failure yields an incomplete
observation, never a confirmed empty list. `not_registered` means that the store
was absent at the checked location.

`progress-report.py session` adds up to three observation lines within its
15-line block. The bounded reader selects one active initiative; several require
selection. References remain whole and omitted details are declared. History
through `--history-only` retains its selection and never queries reviews.

The roadmap, journal and curation budgets above exclude reviews. Two valid
inventories read up to 12 MiB of records, plus up to 1 MiB of plan/redactor
and 8 KiB of ownership markers. An incomplete inventory cannot establish absence.

## Stable local reads and queries without caches

On Windows, a ctime-only change during a read permits one reread of the same
descriptor. Identity, mode, link count, size, mtime, birth time and attributes must
remain unchanged. Payloads must match, the final generation must be stable, and
path and parent checks remain active. Both reads share the original byte limit;
`bytes` charges cumulative consumption. If both cannot fit, the result remains
`changed_path`. Access errors, payload changes and ctime changes on other platforms
are not retried. These checks do not guarantee multi-file atomicity or absence of ABA.

The `progress-report.py` and `plan-review.py` CLIs disable bytecode creation before
loading helpers: querying a project-local kit does not create `__pycache__`, even
without `-B`. Existing caches are retained. The tested guarantee covers these CLI
invocations and does not extend to arbitrary external loaders.

## Ledger size and execution history

The ledger read by resume must remain within 256 KiB. When it grows, execution
details can move to `execution-history.md` in the same initiative, preserving
their original bytes. Tasks, states, criteria and structured reviews governing
gaps and approval gates remain in `tasks.md`. Verify that briefs, review selection
and approval decisions produce the same results after separating details.
Execution history is consulted explicitly; resume does not load it automatically.

Headings used as markers by commands or tests also remain in the ledger,
in their original order. They may link to archived details. Structured review
checks alone are insufficient: verify marker consumers and the resume CLI
against the final source.
