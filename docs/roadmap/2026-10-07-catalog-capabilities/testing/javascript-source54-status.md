# Current JavaScript changed-line measurement

Official Node V8 samples cover all 205 evaluated changed nonblank/noncomment
lines across five distinct implementations (100%). The three runtime sources
are measured by their exact canonical file URLs and UTF-16 source lengths. The
activity/review assets are measured in 18/43 original DOM scenarios, bound to
captured program hashes and exact source spans. Their original assertions remain
unchanged. The renderer removes a UTF-8 BOM before embedding and Windows translates
newlines; the verified projection preserves source line ordinals. Leading whitespace
does not count as execution, and nested zero ranges override positive outer ranges.

This is a mapping of executed V8 ranges to changed lines, not statement or branch
coverage. A line can be covered while another branch on that line remains untested.
The generated OpenCode entry is byte-identical to the canonical hook, has no direct
V8 sample in this cohort, and is excluded from the percentage instead of counted
twice. Its native loading/execution proof remains the separate controlled-provider
probe, not a coverage claim.

[Per-source evidence](javascript-source54-evidence.json) records all six production
paths, their hashes, sample counts and the generated-entry distinction. The first
whitespace-span calculation, initial BOM binding failure and discarded newline
hypothesis remain private historical receipts. No product or test body was changed
to collect these samples. DOM exercise is not real-browser interaction, and a local
provider fixture does not prove unforced agent workflow continuity. Those gates and
independent review remain pending.
