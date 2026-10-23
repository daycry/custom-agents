# CLI budget and Windows acceptance publication

The CLI budget diagnostic now measures the complete emitted text, including its terminating newline. Criteria, memory and the persona floor remain intact. The exact 10,000-character boundary stays silent; 10,001 characters produces a warning with the measured output length.

The synthetic recovery protocol retries only Windows sharing/access errors 5 and 32 for 20, 40 and 80 milliseconds. Both audit replacement and restore publication use the same bounded helper. Restore rechecks that its destination is absent before each attempt. Persistent and unrelated errors still fail, preserving staging, the previous audit and the detailed failure receipt.

Actual Windows file and directory handles reproduce these failures without a product change. The handle owner responsible for the earlier global failure was not identified. The first corrected boundary fixture allowed an optional section to shrink and was corrected to isolate CLI output accounting; that failed run remains preserved.

The deterministic red run has 12 failures and 5 passes. All 118 affected Windows cases pass. Linux has 116 passes and two Windows-specific skips, with its owned container removed. Source hashes are preserved. See [machine-readable evidence](windows-boundary80-evidence.json).

The original Windows global run remains failed (7,126 passed, two failed and 99 skipped). Full current-source QA, native protected roles, human dashboard acceptance and independent review remain pending. These targeted results do not close those gates.
