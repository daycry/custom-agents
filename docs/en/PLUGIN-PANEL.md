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

The OpenCode catalog retains six bindings and eight actions. `ActivityObserved`
identifies the informative `agent-activity` capture, with declared supervision of
2500 ms; the reader requires its exact terminal events and idle inputs. This row
is an adapter declaration, not evidence of opt-in, loading or actual execution.

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
file. Served mode adds local progress, memory queries and opt-in recent activity signals; portfolio details, evaluations and
budgets remain in roadmap-dashboard.

From a checkout:

```powershell
python skills/plugin-panel/scripts/build_panel.py --html panel.html
python skills/plugin-panel/scripts/build_panel.py --json
python skills/plugin-panel/scripts/build_panel.py --project . --runtime codex --html panel.html
```

Installed bundles resolve the skill through their runtime roots. The generator
finds its own bundle; `--root <bundle>` inspects another catalog without importing
its code. Native Python supports Windows without WSL, Tkinter, extra Python
packages. Standalone export needs no server.

## Local dashboard with refresh

```powershell
python skills/plugin-panel/scripts/build_panel.py --project . --runtime codex --serve
```

Open the access URL printed by the process; stop it with Ctrl+C or its launch
handle. The URL contains a private process capability: keep it out of Git,
documentation, memory and logs. Every launch creates a new one. Binding is
fixed to 127.0.0.1, with an ephemeral port or an explicit `--port 8765`.
The server never serves arbitrary project files.

Requires a project and excludes HTML/JSON export and personal roots. Project
declarations are read for the initial snapshot. Catalog and diagnostics stay
fixed at startup; Progress polls ledgers every five seconds, with manual refresh,
search and state filters. Responses share a two-second read cache. Hidden tabs
pause polling; requests expire after four seconds. Failure preserves the last
view and its original date, with an explicit freshness warning.

The canonical parser derives task counts and phase from `tasks.md`. Read date
and SHA-256 identify decoded UTF-8 text without BOM, including line endings;
they do not authenticate authors or prove agents are running. Progress polling
performs no journal, usage-meter, memory or backend queries, or state writes.
Memory is read only after an explicit action.

Reads reject redirected or changed paths. Limits: 128 entries, 256 KiB per ledger,
1 MiB cumulative, 64 initiatives, eight visible active tasks per initiative and
64 KiB JSON. Incomplete reads, unreadable ledgers, unknown states and truncation
remain partial. Text is redacted and bounded; bodies, free-form verification
and absolute paths are excluded.

Page/API require the capability and exact Host; any Origin must match the server.
Cross-site requests, queries and arbitrary paths are rejected. POST is accepted
for local memory queries and an explicitly selected plan review.
Review writes only its own local receipts and comments.
No cookies or access logs; nonce CSP, same-origin connections, no-store,
no-referrer and no framing. The capability does not isolate other processes
owned by the same user. Consuming a plan decision requires the common CLI and
an authorized workflow. Memory publication/rebuild retain their consumers and tests.

## Recent activity signals

In `--serve` mode, Activity is separate from Progress. Reading it neither starts
agents nor turns ledger states into process presence. The common owner,
`agent-kits/shared/agent-activity-store.py`, persists only closed metadata; the
reader calls its `snapshot(project)` and the pure `agent-activity.py` projection.

Capture requires the boolean opt-in `sesion.actividad: true` in the project's
`.claude/dev.json`. Missing or `false` disables it. To enable it manually, merge
this key into the existing configuration without replacing other settings:

```json
{"sesion": {"actividad": true}}
```

Opening the panel or running setup neither creates nor enables this setting.
The producer owns `.claude/agent-activity/` and first creates its `.gitignore`
with `*` followed by a newline, excluding new local-state files from Git. The
reader never initializes, locks, purges, migrates or recovers state. Unowned,
partial or invalid directories remain unavailable without adoption. Ignore rules
do not remove files that Git already tracks.

There are at most 64 observations. The JSON snapshot and HTTP response each have
a 64 KiB limit. `complete` means that snapshot validated; visible
`collection_complete: false` does not represent every session or agent. Cards
show declared runtime/role, source, state and time; pseudonymous keys stay
internal. This state retains no prompts, transcripts, tool arguments or raw
consumer paths.

| State | Meaning |
|---|---|
| `recent_start` | Recent start signal |
| `recent_response_end` | Recent response boundary |
| `recent_execution_end` | Recent execution boundary |
| `recent_idle` | Recent session idle signal |
| `unknown` | Expired signal, future clock or unknown freshness |

A signal proves neither a live process nor agent destruction, authenticated
identity or complete collection. Freshness expires at 60 seconds. The UI combines
advertised age with monotonic time since reception; refreshing the same event
and revision does not renew its age. HTTP failure preserves the view and date,
but signals keep expiring. Future timestamps remain unknown.

`GET api/activity` uses the server's existing capability and Host/Origin guards.
It is read-only, bounded and accepts no arbitrary route. POST retains the
existing 405 rejection. There is one active request, a four-second timeout and
polling five seconds after settlement. Hiding the tab aborts and pauses requests;
resuming applies expiry before fetching. Static HTML explains that no service
supplies signals. Missing activity JS degrades only this section, preserving
other views.

Skills-only export requires explicit skill references to
`agent-kits/shared/agent-activity-store.py`, `agent-kits/shared/agent-activity.py`,
`agent-kits/shared/local-state.py` and `agent-kits/shared/local-read.py`.
The `capture` producer also reads the central mapping
`agent-kits/shared/native-roles.json`: declare it explicitly so the package
includes the JSON, even though the `snapshot` reader does not use it.
That package registers no native hooks; bundled helpers and mapping do not prove capture.
Projection/HTTP/DOM have focal tests. Real browser interaction, hook loading and
native acceptance require their own evidence.

Official references checked on **2026-10-10**:

- [Claude Code: SubagentStart/SubagentStop](https://code.claude.com/docs/en/hooks): subagent signals; a response boundary does not prove destruction.
- [Codex: hooks](https://developers.openai.com/codex/hooks/): native subagent events/payloads; documentation does not establish loading in this session.
- [OpenCode V2.0.12: execution settlement](https://github.com/anomalyco/opencode/blob/2670273ff17da96f85c5826ced57aa1b368754fa/packages/core/src/session/execution.ts#L118-L150): emits one `session.execution.succeeded/failed/interrupted` terminal; its [projector](https://github.com/anomalyco/opencode/blob/2670273ff17da96f85c5826ced57aa1b368754fa/packages/core/src/session/projector.ts#L403-L434) derives idle/outcome from that event.
  Capture preserves `execution_finished`, without turning it into an independent `session_idle` observation or teardown. `session.idle`/`session.status` remain compatibility inputs without claiming emission by this version.
  Native acceptance requires its own evidence and exact correlation; reading the contract does not establish complete capture.

## Review a plan at the existing gate

Visual review is optional. When explicitly requested, it replaces the pending
plan approval in `/dev-cycle`. Sufficient approval already given in conversation
lets the workflow continue without opening this channel or asking again.

The [`/dev-cycle`](../../commands/dev-cycle.md) caller includes Bash and
PowerShell recipes. Use a real Python executable and owner/validator/builder from the same
bundle; multiple complete copies without active source provenance are ambiguous.
Validate `open` before starting a separately held server, and validate ack before
rereading the current view. These recipes alone do not establish native command
loading or real browser interaction.

```powershell
python skills/plugin-panel/scripts/build_panel.py --serve --project . --review-initiative docs/roadmap/<date>-<slug> --review-state-root ./.claude/plan-review --review-gate-key plan-ok
```

Select the exact initiative path; only `improvement-plan.md` is reviewed.
`--review-initiative` and `--review-state-root` are paired. The builder defaults
to `requested-review`; `/dev-cycle` must select `plan-ok`. A general review decision
cannot authorize that gate. Served mode excludes `--html`, `--json`, `--home` and
`--user-root`. Standalone HTML neither opens review nor writes its state.

The workflow first runs `plan-review.py open` to obtain the review ID and version,
using `gate-key: plan-ok` and its current runtime. It then starts the server,
which recovers that same receipt. Keep the server handle and private URL while
the user reviews; a waiting consumer must never interpret `waiting` as approval.

The view displays all Markdown as text, split into sections and bound to original
byte and view hashes. Repeated headings have separate IDs. Redacted secrets and
sanitized controls are indicated. Approval covers the displayed view, excluding
hidden values. Text, links, images and HTML cannot execute instructions or load
external resources. Unreadable, empty, partial or oversized plans disable decisions;
no clipped prefix can be approved.

| Action | Result |
|---|---|
| Save comments | Saves the redacted section drafts before a decision |
| Approve the view | Seals `approve` for that version; comments are optional |
| Request changes | Seals `request_changes`; needs at least one nonempty comment |
| Load current version | Explicitly opens the current version without transferring comments |
| Close without deciding | Closes the UI and preserves drafts/receipts without a decision |
| Return to review | Reopens the UI without submitting another decision |

The workflow uses `plan-review.py consume` with project, state-root, initiative,
review_id, gate and the raw/view tuple. The owner validates selection/view before
delivery, confirms actual IDs and rereads the version before returning consumed
state. It launches no roles and proves no external effects. Waiting preserves an
absent decision; an obsolete version is not consumed. A failed ack preserves the
delivery for retry; a post-ack change returns version_changed with historical
consumption. One three-second deadline covers the whole operation. The final view
is not a transaction with subsequent work and does not guarantee ABA detection.

An obsolete review preserves its historical decision but does not approve the
current plan. `receive` returns `version_changed` and exit code 2 without consuming
it. A new review opens with `open` against the current version and needs its own
decision; the old receipt hashes are not updated. Valid consumption remains
`receive → validation → ack → validation → view`, before effects. Sufficient
conversational authorization retains its existing route.

The common owner `agent-kits/shared/plan-review.py` maintains machine states
`pendiente` → `entregada` → `consumida`. Submission leaves the decision pending;
`receive` delivers it and `ack` records durable consumption. The panel never starts
agents, changes plan/tasks or performs receive/ack over HTTP. Consumer registration
is historical: the UI reports no registration or unknown activity.

GET view/status and POST comments/submit/refresh accept only IDs registered by
this server instance. No free-form roots, paths, artifacts or commands are accepted.
Project state under `.claude/plan-review/` is shared by all three runtimes; it is
not Claude-only personal configuration. Exclude it from Git. The owner neither
adopts an unrelated directory nor evicts decisions to make room.

Limits: 256 KiB plans, 128 sections, 64 receipts, 16 KiB requests and 512 KiB JSON
responses. Up to 20 comments, 2,000 characters each and 10 KiB cumulative UTF-8
text; excess is rejected without clipping. Operations share a three-second deadline
and a lock budget of up to 100 ms. Status polling runs every five seconds with
one active request, pauses on hide/close and aborts after four seconds.
Memory and Progress retain their separate limits.

Changed bytes or transformer produce `version_changed`, retain the old receipt
and disable decisions until the current version is explicitly selected.
The workflow validates gate, version and choice, acknowledges, then rereads before
starting work. A current consumed receipt permits resume without another confirmation.
Delivery may repeat; receipt consumption is idempotent, external effects have no such guarantee.
On resume the workflow checks the current ledger/plan: ack does not prove work
finished before a crash. Resume pending work without restarting planner for changes
already addressed. A stale receipt remains historical and cannot replay its decision on another plan.
Hashes and the capability do not authenticate a person. Rereads and locks provide
no workflow transaction, ABA detection or universal power-loss durability.
Fallback uses existing conversational authorization without inventing approval.

The common bundle needs `plan-review.py`, `local-state.py`, `local-read.py` and `redact.py`.
Skills-only review requires the export to include all four dependencies declared
from plugin-panel. Package verification belongs to QA; any missing dependency
leaves this channel unavailable.
The [command](../../commands/dev-cycle.md) describes receive/ack and the authorized return to planner.

### See what happened to a comment

Consumption confirmed means ack, not that the comment was addressed. Results show
the consumer's declaration: `addressed`, `not_applied` with a reason, or
`needs_clarification`. `confirmed`/`not_confirmed` records a human observation
already communicated; it authenticates nobody and grants no approval, QA or new
permission. Missing responses or verifications stay explicitly missing. This is
not chat and adds no confirmation before continuing authorized work.

The consumer records responses through the CLI after that decision's ack. The
browser reads results/history; result/verify-result/receive/ack have no HTTP write
endpoint. Comments on approve can also receive responses; no comments means no
invented row. Notes are inert text. Editing the plan leaves a response bound to
its old consumed review; the new view inherits neither attention nor approval.
Response history distinguishes versions and superseded results. Polling preserves
drafts and focus; failure retains the previous date with a warning.

### Record a response from the workflow

Reuse the `/dev-cycle` caller variables and owner from the same bundle. Retain
review_id, version, gate_key, decision_id and delivery_id from the consumed decision;
CommentId comes from decision.comments. ReviewRevision is that record's integer
`review.revision`, reread before a new operation. A historical version_changed or
unavailable view may expose this record; it cannot authorize work on a new plan.
Choose ResultId once (64 lowercase hex characters) and retain it and the payload
if a response is lost. ReviewRuntime is the current runtime.

```powershell
$OutputEncoding = [Text.UTF8Encoding]::new($false)
$ResultRequest = @{
  version = @{raw_sha256=$RawSha256; view_sha256=$ViewSha256; view_version='plan-text-v1'}
  gate_key = 'plan-ok'; decision_id = $DecisionId; delivery_id = $DeliveryId
  comment_id = $CommentId; result_id = $ResultId; expected_revision = $ReviewRevision
  disposition = 'addressed'; response_text = 'Separated consumption from comment attention.'
  supersedes_result_id = $null
  producer = @{caller_id='dev-cycle'; runtime=$ReviewRuntime; actor_id=$null}
}
$ResultRequest | ConvertTo-Json -Depth 4 -Compress | & $ReviewPython @ReviewPythonArgs $PlanReview result @ReviewScope --review-id $ReviewId --json
```

In Bash select a UTF-8 JSON file with the same eleven keys; RESULT_REQUEST is its
chosen path. Pass the note as data, never as executable shell text.

```bash
"$REVIEW_PYTHON" "${REVIEW_PYTHON_ARGS[@]}" "$PLANREVIEW" result "${REVIEW_SCOPE[@]}" --review-id "$REVIEW_ID" --json < "$RESULT_REQUEST"
```

`producer` has exactly caller_id (1–128 ASCII letters/digits/_/-), runtime
(`claude-code|codex|opencode`) and actor_id (null or an opaque 64 lowercase-hex ID).
Do not send identity_basis, human names, dates, flags, section_id or artifact
observations: the owner derives those. Matching the first consumer is not required.

If a human observation was already explicitly received, retain those bindings and
choose VerificationId once. Reread ReviewRevision for the new operation. Never
infer a verification from edits or tests.

```powershell
$VerifyRequest = @{
  version=$ResultRequest.version; gate_key=$ResultRequest.gate_key
  decision_id=$DecisionId; delivery_id=$DeliveryId; comment_id=$CommentId
  result_id=$ResultId; verification_id=$VerificationId; expected_revision=$ReviewRevision
  assessment='confirmed'; note='Human observation already communicated about this response.'
  producer=@{caller_id='dev-cycle'; runtime=$ReviewRuntime; actor_id=$null}
}
$VerifyRequest | ConvertTo-Json -Depth 4 -Compress | & $ReviewPython @ReviewPythonArgs $PlanReview verify-result @ReviewScope --review-id $ReviewId --json
```

The eleven verify-result keys replace disposition/response_text/supersedes_result_id
with verification_id/assessment/note. Assessment also accepts not_confirmed and
note may be empty. Bash uses the same verify-result CLI with its JSON on stdin.
This annotation is optional, never another gate or delivery requirement.

Exit 0/status ok confirms feedback persistence: review null, approval_granted false
and a feedback_receipt binding the operation, IDs and version. Never pass it to
the open validator or use it as authorization. Exit 2 means conflict; exit3 means
unavailable. Retry with identical IDs/content retains the date and observation,
even when the record revision has advanced. revision_conflict needs reread and
reconciliation; operation_conflict never permits overwrite. A correction uses a
new result_id and supersedes_result_id of the latest result (at most two per
comment). Each result allows one verification; superseded rows stay historical.

`feedback_receipt.revision` is the current record revision when the owner replies.
A retry after another operation may return a higher number than the first receipt;
the IDs, `recorded_at` and persisted row remain unchanged.


Requests 16 KiB; nonempty responses up to 1000 characters/2048 UTF-8 bytes; notes
up to 500/1024. Oversized input and row/record budgets fail without clipping.
History contains up to 8 complete reviews/64 KiB from the same scope, initiative
and gate. Incomplete is not empty. Older bundles without the extension report
unavailable results; an invalid extension is not treated as missing. The new owner
reads record schemas 1/2 without migration on reads; the first valid feedback write
may upgrade legacy to 2. Use owner/server/UI from one bundle; concurrent writes by
old and new binaries are not promised. The envelope remains 1. These instructions
do not establish V01–V08 browser interaction or native acceptance.

## Local memory queries

Queries preserve each entry's authority: proposals and legacy entries do not
become approved knowledge. The [local recovery contract](../roadmap/2026-10-07-catalog-capabilities/comparisons/memory-local-recovery-contract.md)
separates session preservation and restoration from query evaluation.

Served mode adds Memory with Search, Show entry and Relations. Each explicit
action uses `knowledge-view.py`; loading the page or refreshing Progress does
not trigger memory searches. Cards retain full ID, type, state, knowledge version,
evidence and source path. Proposed and obsolete entries retain their state.
Bodies are returned only on Show; an ID collision never selects an entry.

Reads share parsers, ranking, relations and approved validation with
`knowledge-find.py`. Cumulative limits: 256 directory entries, 128 files, 256 KiB
per file, 2 MiB read and depth eight. Queries allow 1,000 characters, IDs 256,
20 results/relations, bodies 12,000 characters and JSON responses 64 KiB.
Truncation, invalid corpus and incomplete reads remain partial; missing,
ambiguous and unavailable are distinct. Redaction precedes clipping;
paths and hashes do not prove approval.

Versions above JavaScript's safe integer range use exact decimal strings, up
to 4,300 digits. Invalid versions remain unknown with a partial result. Alongside
directory entries, enumeration calls are limited to 256; `scans` accounts for
this work even when directories are empty. The reader's probe byte is reserved
within the cumulative read budget.

Only UTF-8 JSON on the fixed private `api/memory` route is accepted, with a
4 KiB request limit and a cumulative three-second body deadline. Duplicate keys,
unknown selectors and other methods are rejected. The UI omits cookies, sets a
six-second query deadline and prevents overlapping requests. Failure preserves
the previous view/date with a warning; results, bodies and relations retain their
own freshness. No adapters, candidates, journal, cache or indexes are loaded.
Standalone HTML retains its inventory without these queries.

CLI usage: `knowledge-find.py --root <project> --view <query>`,
`--view --show <ID>` or `--view --related <ID>`. Output uses version 1 and source
`canonical_knowledge`. Ordinary CLI queries also use the bounded snapshot and
declare `corpus_read`; partial corpora are never cached as complete indexes.

## Standalone extension export

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
## Imported diagnostics

The panel can consume an **explicitly selected** report. Request doctor
`--panel-json` for the project root and save its output to a chosen file, then
pass `--diagnostics-report <report.json>` and `--project <same-root>` to build_panel.
The panel never runs doctor, discovers reports or checks services. An explicitly
requested doctor run retains checks of active opt-in capabilities and may contact
their backends. Exit 1 can accompany a valid report containing findings; exit 2
means usage/projection failure. General doctor JSON contains private details and
is rejected by this input.

Doctor applies the shared redactor before exporting this projection. A missing
bundled contract or redactor yields an opaque warning and exit 2.

Version 1 declares doctor as producer and includes UTC time, a SHA-256 key of
the normalized absolute project path and rows by public block. This binds path
spelling according to the operating system; it does not prove physical identity,
anonymity or process provenance. A moved project needs another check. The visible
source hash covers decoded UTF-8 text without BOM, rather than original file bytes;
it identifies content without authenticating its producer.

The contract allows eight public blocks, at most **512 rows** and **64 KiB** of
input. Only severity, exact public labels and up to three priority references are
exported. Private or unknown labels fall back to row ordinals. Details, paths and
free-form remedies remain in doctor. Priority links point to checks and refer to
doctor's block/row for details and remedies; they never execute commands.

Every report is a historical snapshot. Reports older than 24 hours are labelled
old; future timestamps are rejected. Missing input, incompatible format, unbound
or mismatched scope, read failure and truncation are distinct. Partial reports
show partial counts and omit priorities. Missing evidence does not become zero,
readiness, execution rates or health.

Diagnostics provides severity filtering, search, fragments and keyboard focus.
Inventory filters remain independent. A successful check never upgrades hook
`load_status` or `execution_status`. Regenerate HTML to update it; this is not a
live service. The checkout's /panel.html is ignored as a local generated artifact;
the packaged template remains versioned.
