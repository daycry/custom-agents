# Plan decision consumption — implementation and validation

The common `plan-review.py` owner now exposes the CLI operation `consume`.
The caller supplies the exact project, state root, initiative, review ID, gate
and raw/view hashes. The owner checks the current view and selection before
delivery, calls its existing receive/ack primitives with their returned IDs,
and checks the view again before returning. All calls share one deadline.

This operation does not edit plans or tasks, run agents, or create another state
store. A failed acknowledgement preserves its delivery for retry. A version
change after durable acknowledgement retains historical consumption without
granting permission for the current plan.

## Evidence available

Tests were written and observed failing before implementing the operation:
the first CLI test rejected the absent `consume` choice; the expanded contract
then produced 16 failing consume cases. The implemented owner suite passed all
68 cases. Executable command recipes passed 34 tests without skips, including
eight cases against the real owner across Bash and PowerShell. Those cases cover
approval, requested changes, waiting, obsolete versions and idempotent replay.

After tightening command guidance for invalid inputs and receipt state, the
focused owner/caller/transport suite passed 150 cases with one skip for an
unavailable directory-symlink privilege. Export validation, lint, ledger and
static activation checks passed on the same snapshot.

Four actual native OpenCode 2.0.12 sessions invoked the installed command with
the existing configured model. Model outputs and tool calls were not forced.
Acceptance below compares completed tool calls, their returned JSON, the owner
record and unchanged synthetic plans/ledgers; command text alone is insufficient.

| Case | Actual consume result | Durable outcome |
|---|---|---|
| Current approval | exit 0, `ok` | Matching decision/delivery/ack, current consumed receipt |
| Requested changes | exit 0, `ok` | Sealed comments retained, matching consumed receipt |
| Waiting | exit 0, `waiting` | No decision, delivery or acknowledgement created |
| Obsolete version | exit 2, `version_changed` | Historical decision retained, no delivery or acknowledgement |

All four assistant responses retained the complete actual JSON payload.
Only approval and waiting returned raw JSON alone. Obsolete-version and
requested-changes responses added introductory text and a JSON code fence;
the original strict JSON-only cohort remains failed on those two presentation
requirements. The first observer also missed a completed call whose executable
path used a quoted `find` substitution; a separate returned-call trace verified
it without relabelling the original receipt.

The native cohort used 42 upstream HTTP 200 requests, with no gateway-budget
rejections or upstream authentication/quota block. Owned containers and network
were removed. These sessions used synthetic projects and owner-API decisions;
they do not establish a human browser approval or another client's native parity.

## Closure still pending

The first new full collection contained 7,320 cases: all 7,296 previous cases
and 24 consume cases. Linux passed 7,255 with 65 skips and no failures; official
parent-process coverage of the 33 changed Python sources was 91.2824%.
Windows passed 7,246 with 73 skips and one failure; coverage was 91.1718%.
Collection, direct dashboard checks, source preservation and owned cleanup
were verified on both platforms. The Windows result remains failed.

The failed Windows N06 fixture could not read its already published `ready.json`.
Publication is atomic; the original file holder was not identified. Two new
regressions reproduced the real sharing conflict with an exclusive Windows
handle and observed the actual PermissionError. The reader now retries at most
five times with 10 ms pauses under the existing deadline, then still validates
process identity, nonce, script hash and frontier. The wrong-nonce regression
confirms that a successful later read does not bypass identity checks.
Both new cases failed before the reader fix; all 14 local-recovery cases passed
after it. Production Python did not change for this fixture correction.

Full regression after the fixture correction passes on both platforms:
Windows has 7,249 passes and 73 skips; Linux has 7,255 passes and 67 skips.
Both preserve the same 7,322-case collection and all source hashes, pass the
direct dashboard checks, and confirm owned process/container cleanup. Official
parent-process coverage of the 33 changed Python sources is 91.1718% on Windows
and 91.2824% on Linux; child coverage is not attributed to those percentages.
The two new Linux skips require native Windows sharing handles.

[Final scoped QA evidence](plan-consume-final-qa-evidence.json) records these
receipts and the pending technical-memory proposal. Required independent review
and final branch consolidation remain pending. Earlier failed results retain
their exact snapshot scope and are not relabelled as a green suite. This QA does
not establish all-client native acceptance, human browser approval or catalog closure.

The installed-command snapshot for the four native cases has manifest SHA-256
`1d5a1276a2daee001c70f60b7ca0a0c8e4a60a0e4871c2efd5aecfeb59453047`.
This status report is a later documentation addition. It does not claim complete
catalog integration, all-client workflow acceptance, or publication.
