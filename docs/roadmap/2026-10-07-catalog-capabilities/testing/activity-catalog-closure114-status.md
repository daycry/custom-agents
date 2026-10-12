# Activity catalog and local dependency closure

Source53 full QA reproduces six failures on both platforms. Four follow the
reviewed whole-owner pin predating the single native-start mapping change:
the fail-closed hook traversal rejects the owner and cannot traverse its three
declared local dependencies. Two follow the panel validating activity with the
terminal-only capture vocabulary: it rejects the real catalog and accepts an
activity catalog whose start was removed.

The scoped Windows reproduction preserves all six failures, with 220 passed and
two skips. The entire owner was read; its only difference from the previously
pinned body is the native-start mapping. Local imports, effects and dependencies
are unchanged. Renewing its pin restores traversal without a network exception.
Panel validation keeps the exact terminal vocabulary for capture and requires
execution start for activity. The existing positive inventory oracle now names
that native start. Invalid catalogs, mutated dependency network imports and
missing modules retain their rejection tests.

Windows: 226 passed, two skips. Linux: 227 passed, one Windows-only junction skip;
pytest exits zero. The Linux driver exits one because its expected count wrongly
required no skips. Its original failed receipt is preserved. JUnit identifies
the sole skip as the Windows junction contract; source/dependency preservation,
native modes, fixture execution and owned container/job cleanup are verified.
No rerun or product/test alteration was used to hide that driver mismatch.

[Structured evidence](activity-catalog-closure114-evidence.json). This correction
does not change native adapter transport or capture. Full current-source QA,
human UI and independent review remain separate pending gates.
