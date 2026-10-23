# Graphiti publication and recovery

**English** · [Español](../knowledge-services-graphiti.md)

Canonical memory lives in `docs/knowledge/approved/`. Graphiti is an optional
projection: an outage, pending confirmation or rejected external read preserves local
search. The plugin does not activate services or migrate graphs automatically.

## Creation and confirmation

A new episode is sent without a UUID. The server assigns its identity; a queue
acknowledgment does not prove persistence. The adapter confirms name, group, content
and actual UUID through `get_episodes` before committing the publication manifest.

New entries store `binding: verified_readback` and `episode_body_sha256`, covering the
sent body including provenance and provider instructions. Legacy manifests retain
their limited checks without automatic promotion to this binding.

Submission receipts live in `.claude/knowledge-services/graphiti-submissions/`, with
an owner marker and cooperative lock. Episode phases are `submitting`, `submitted`
and `confirmed`. Lost acknowledgments retain uncertainty; retries observe the existing
submission instead of automatically sending it again.

The journal allows 128 operations in total, including episodes and relationships,
and 256 KiB of state. The lock serializes cooperating callers; it does not authenticate
the server or guarantee exactly-once delivery. Partial installations must include
`agent-kits/shared/local-read.py` and `agent-kits/shared/local-state.py`.

## Succession and withdrawal

Succession confirms `<id>@<version>@superseded`; withdrawal confirms
`<id>@<version>@withdrawn`. Each marker retains the affected version's actual remote
identity. Withdrawing version 1 permits a later approval of version 2. Legacy
`<id>@tombstone` markers keep their historical whole-entry invalidation meaning.

Queued operations bind their group. Withdrawals also bind version, actual UUID and
hash. Replayed superseded, withdrawn or different-group operations are skipped and
reported as `omitidos_obsoletos`. Changed content requires a new version. Unbound
withdrawals fail. A retained identity still permits withdrawal when an episode leaves
the pending manifest's observation window.

## Recovery of withdrawn submissions

When an entry leaves `approved/` before publication confirmation, the local plan adds
`retire_submission`, binding name, group and sent-body hash. Planning makes no network
call, creates no files and resends nothing. Still-approved entries keep their ordinary
publication operation.

Execution observes the owned receipt's episode and checks content and actual UUID.
If confirmation is unavailable, the receipt remains pending and a diagnostic error
is returned. Absence from the observation window is not proof that submission never
happened. Once confirmed, a version-scoped withdrawal is committed without making the
episode current. Its `retired_episode` binding retains name, UUID and body hash; only
then may its submission receipt be pruned. `retirados_pendientes` counts these recoveries.

An interruption before commit retains confirmed receipts. The next execution reuses
the episode and marker. An old withdrawal cannot remove a newer generation. Markers record their intent before submission: affected version, original UUID,
replacement UUID when applicable, references and representation. `recover_transition`
adopts the event only after confirming the episode and reconstructing its exact body.
It recovers the marker first, then withdraws an abandoned version or confirms the
still-approved replacement. Historical identities remain in the manifest.

If confirmation or a relationship remains pending, later operations for that entry
are deferred; other entries retain independent progress. Recovery respects current
configuration: a receipt cannot enable disabled direct edges. Changing representation
while an operation is pending requires explicit resolution, without automatic conversion
or resubmission. Legacy receipts without recorded intent remain diagnosed as pending;
no intent is invented for them.

A confirmed succession cannot be undone by returning to the same version number.
A later approval needs a new version.

## Relationship representation

`transition_relations` accepts two values:

| Value | Behavior |
|---|---|
| `episode` (default) | Stores `relation: SUPERSEDES`, source/target references and episode provenance in the confirmed own-group marker. Does not call `add_triplet`. |
| `triplet` | Adds a relationship between reference entities and confirms group, names, fact and UUID through scoped searches. Requires operator verification of server write isolation. |

Episode representation preserves the documentary relationship and deterministic
invalidation; it does not promise a typed edge extracted by the model. Triplet mode
never passes episode UUIDs as Entity identities. Lost relationship acknowledgments
are recovered by observing the existing edge, without automatic resubmission.

A `group_id` argument does not prove physical isolation. In the inspected server
using graphiti-core 0.30.1, `add_triplet` uses the shared client and the SDK writes
through its current driver. Episode ingestion can change that driver to another
group. This path must not be enabled by default with FalkorDB. Source inspection
did not change containers or database contents.

## Extraction for control markers

Succession and withdrawal send `previous_episode_uuids: []` and instructions identifying
the episode as a control record with no new domain entities. IDs are opaque references.
These parameters are not applied to ordinary knowledge entries.

Markers always exclude the standard `Entity` type. For a server with custom types,
declare all their names in `transition_excluded_entity_types`. The list allows up to
128 printable names of 1–256 characters; duplicates are removed and ordering is stable.
For example, a server declaring `Document` needs that name included. The plugin neither
invents custom types nor discovers them through `get_status`, which does not expose them.

The inspected SDK applies exclusion before node creation and custom attribute validation.
This prevents a withdrawal marker from attempting to fill mandatory organization fields.
The SDK still calls its model for initial extraction; this is not model-free ingestion
or a service-availability guarantee. Unknown excluded type names can fail asynchronously.
Verify the configured names and retain exact persistence readback.

## Logical scope and published generation

Project configuration retains its logical `group_id`. A published descriptor may declare
`logical_group_id` and a physical generation group. A generation name must bind the logical
scope hash and a 32-character hexadecimal nonce; another project's group is not adopted.
Pending, incomplete or ambiguous descriptors and unsafe path components never activate a generation.

Planning, publication, withdrawal, health, verification and queries resolve this selection
from the published manifest without changing caller configuration. Publication checks it
again after acquiring its lock; a concurrent change aborts before archiving or resurrecting
an obsolete generation. Code helpers are reused within the process; descriptor data is reread.

`rebuild` constructs and verifies a new group before switching the published manifest.
It retains the previous group and history; it clears no group. New UUIDs are bound to
versions and withdrawals. Repeating a confirmed request reuses the generation; remote
loss can be repaired from owned snapshots bound by identity and hash or, for current
documents, from exact canonical source.

The coordinator retains content, intent and progress in
`.claude/knowledge-services/graphiti-rebuild.json`; each generation has private state under
`.claude/knowledge-services/graphiti-generations/<nonce>/`. Receipts permit observation of
interrupted submissions without resending. Pending active publication, untracked episodes
or incomplete windows prevent construction. Historical content is never invented.

If the corpus, extraction configuration or active publication changes between attempts,
the previous descriptor is archived and another generation is prepared. Abandoned groups
and uncertain receipts are retained: server jobs are not cancelled and data is not deleted
automatically. Changing endpoint or logical scope requires resolving or archiving the old identity.

Each descriptor is limited to 8 MiB; remote windows retain their bounds and writes share
a time budget. Exhausting a limit preserves previous publication. Live-service and native
workflow acceptance remain pending.

## Published history verification

`verify` checks current entries, transition markers and retained withdrawn identities.
Each historical identity requires a unique name, exact group, UUID and content hash.
A manifest without current entries still verifies its history; emptiness does not
authorize reading. `historico_verificado` counts confirmed historical episodes,
including withdrawn versions.

Before network access, marker intent is validated and its body reconstructed to check
the declared hash. A current version cannot contradict a recorded invalidation. In
`triplet` representation, scoped searches also verify the edge and both endpoint UUIDs
within a bounded time budget.

Duplicate names and responses outside the requested group keep reading closed.
Incomplete windows report `incompleto`, not success; `total` counts every expected
identity. Verification creates no files, recovers no submissions, reindexes nothing
and publishes no data. Incompatible history remains diagnosed without invented
intent or identity.

## Reads and maintenance

`off` avoids connections and rejects writes; `shadow` permits publication and checks
without authorizing queries; `read` requires health, intent permission and complete
verification. Unconfirmed and confirmed-but-uncommitted receipts block external reads
before cached permission or empty manifests are accepted. Observation creates no state,
opens no lock, recovers nothing and makes no network call.

The pending manifest retains progress per operation. Partial failure can leave already
persisted episodes; no global rollback is promised. The synchronizer drains its outbox
before planning the fresh target. Local canonical memory remains available.

The manifest uses shared state I/O with exclusive temporary files and observed target
identity checks. Only Windows errors 5, 32 and 33 are retried: up to four attempts with
20/40/80 ms waits while identity remains unchanged. Each manifest is limited to 8 MiB;
the receipt journal keeps its 256 KiB limit. Writes inside a publication retain its time
budget. Cooperative checks are not a universal atomic compare-and-swap against other writers.

Generation rebuild, historical verification and semantic source linkage passed the
bounded compatible-server fixtures described below. Native workflows, comparative
retrieval utility and global QA still require acceptance.


Generation rebuild was verified against an isolated official server revision
0a3b1711b018e5590cf5c44a3ee3e67d6733ee13 with graphiti-core 0.30.2 and MCP 2.2.0.
The installed 0.30.1 deployment fails cross-group episode reads; physical data remains
but get_episodes queries the last-used graph. Compatible per-group routing is required.
The adapter links fact `episodes` UUIDs to published identities; for entities it calls
`get_episode_entities` for one current episode at a time. Scope, UUID, content hash,
version and knowledge ID must match the manifest. Unknown, ambiguous and retired-only
references are discarded. Invalid native references never fall back to an Entity name.

Episode windows also expand for UUID targets within configured bounds. Entity membership
is limited to 20 episodes and 500 nodes per response with a time budget. A failed
membership query preserves independently bound facts and reports a diagnostic.

Extracted summaries and facts are derivative text: `contenido_derivado: true`,
`autoridad: ninguna`, `verificacion: no_verificada` and `citas_por_afirmacion: false`.
Status and evidence describe approved source material; they neither approve generated
text nor verify individual claims. A compatible temporary server recovered the current
version through normal, fact-only and entity-only reads after this change. Partial
membership responses, exhausted budgets and unseen current sources cannot establish
unambiguous entity provenance. The original service was preserved; deployment, native
workflows, comparative utility and global acceptance remain open.


The shared reader preserves derivative labels and source UUIDs in JSON. Compact
output starts with “derivado sin autoridad”, including when shortening long identities.
Bounded IDs and paths remain exact in JSON; unsafe or inconsistent identities are
discarded instead of transformed. The approved status describes the source, not the
extracted text. This also preserves the distinction in compact agent briefs.


When an initial submission fails, the owned receipt preserves the error class and
a sanitized, redacted diagnostic of at most 500 characters. A retry retains that
cause while reporting pending confirmation; it never authorizes another send.
Diagnostic fields are optional for existing receipts and validated before reuse.


Modern Entity names cannot establish episode provenance. A result must identify an
exact confirmed episode UUID and name, or pass Entity membership lookup. Modern facts
require explicit episode references. All extracted graph text keeps derivative labels,
including legacy-format results. Planning rejects invalid prior versions. Source IDs
(up to 512 characters) and paths (up to 4096) are validated in full; unsafe or excessive
identities are discarded before normalization. Safe identities are never truncated.


The final adapter was retested against the compatible temporary server after the
identity and Entity-name corrections: normal, fact-only and Entity-only retrieval
returned current version 2, with three creation requests and two historical identities
verified. All owned graphs and the sidecar were removed. Comparative utility, native
client workflows and global QA remain pending; the existing service was not upgraded.
