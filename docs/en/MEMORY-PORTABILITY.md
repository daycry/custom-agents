# Transfer knowledge between projects

**English** · [Español](../MEMORY-PORTABILITY.md)

Local memory remains the source of truth. Transfer approved notes to another
project through `knowledge-curation.py export` and `import`. The destination
receives pending proposals: importing does not approve, publish or synchronize
external services. Humans and agents use the same persistence service.

## Export a selection

Resolve `$SHAREDKIT` through the runtime's installation roots, as the cycle does.
Run `python3 "$SHAREDKIT/knowledge-curation.py" export --root <source>
--source-id <source-label> --id <exact-id> --out <relative-file>`.
Repeat `--id` per note; the entire corpus is never selected implicitly. Optional
`--scope-category` and `--scope-area` filter local metadata with AND.

Keep the JSON response, path and whole-package SHA. Output must be new and outside
`.git`, configuration, knowledge and the ledger. Export does not modify original
notes. Project and producer labels are declarations, not authentication or backend
permissions.

The closed v1 package preserves original Markdown bytes, BOM/CRLF and SHA through
base64. It exports valid approved entries only; notes that would change during
redaction are rejected. Limits: 32 notes, 1 MiB package, 256 KiB per note/proposal,
4096 inventory entries and 8 MiB combined reading. Notes are not truncated and
batches are not silently split.

## Check and import

1. Explicitly copy the package to the destination project without changing bytes.
2. Run `python3 "$SHAREDKIT/knowledge-curation.py" import --root <destination>
   --destination-id <destination-label> --package <relative-file>
   --expected-sha256 <package-sha> --check`.
   Preflight checks the whole batch without creating candidates, intents, receipts
   or a lock; it may acquire an existing cooperative lock to read stable state.
3. If you choose to persist the valid batch, run the same operation without
   `--check`. The service revalidates package, policy, project and reservations
   under the lock before publishing. Keep the JSON even when exit is nonzero.
4. Review each `candidate_path` and `candidate_sha256`. Curator uses the existing
   Gate and `apply` for an explicit decision bound to the pending SHA. Only that
   decision assigns a destination ID and initial version 1 on approval.

Import retains the body and representable metadata but removes approved ID,
version and state; it sets `proposed_by: import` and immediate `import_*` provenance.
It does not promise to strip every historical approval field. Legacy, journal,
configuration and external routing remain outside this operation.

## Retries and partial effects

Repeating the same request recognizes only its own intents/receipts and files
verified by identity and SHA. It does not adopt unrelated equal bytes or bypass
reservations by changing policy or label. A completed receipt records a proposal:
if Curator moved the note, retry reports `missing_or_moved` without recreating it
or inferring approval.

Import state lives under `docs/knowledge/candidates/.curation/import-v1/`, with
records separate from `apply` and an `import_operation_id` field. There is no second
memory store or additional approval gate.

A batch is not a multi-file transaction. Failed persistence can leave earlier
entries pending and later ones unstarted. The response distinguishes `not_started`,
`persistence_pending` and `orphan_unrecoverable`. Staging without proven owned intent
is neither adopted by hash nor purged automatically.

`written` reports observed proposal effects, not success or power-loss durability:
`false` before attempting creation, `null` after an OS creation failure without a
proven outcome, `true` after observed creation or persisted ownership. Lock
infrastructure is outside that indicator. For export, also inspect `output_current`;
a failed response can still have published bytes.

| Exit | Result |
|---|---|
| 0 | Complete export, complete preflight or verified import receipts |
| 1 | Validation or conflict |
| 2 | Usage, dependency, I/O or unverifiable state |

Local reading remains available without external services. Transfer does not enable
Kwipu, Graphiti, Graphify or models; those capabilities retain their own contracts
and opt-ins.
