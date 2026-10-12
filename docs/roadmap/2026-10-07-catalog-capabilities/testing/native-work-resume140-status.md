# Native JSON resume command validation

The native OpenCode 2.0.12 entry loaded and expanded the shipped command body,
then used a real configured model against an isolated synthetic project. Two
cases pass: an exact initiative and an unfiltered request with two active
initiatives. Both actually invoke the deterministic composer and return every
JSON field and value from its result. The ambiguous result retains its two
candidates without opening another interaction or selecting one automatically.
Neither changes the ledger bytes. Equality covers JSON semantics, not whitespace
or byte-for-byte preservation of the model response.

The earlier source55 run retained two semantic deviations despite its explicit
case reporting native success: missing top-level `status`, and manual ambiguity
selection without invoking the composer. Those original receipts remain failed
evidence. The correction sets the tool working directory to the authorized
project, requires the composer even without filters, and preserves the full JSON
response. It changes prompts and documentation, with regenerated native exports;
the composer, hooks, schemas and tests remain unchanged.

The focused Windows regression passes 118 tests with one platform-specific skip.
Export generation/checking, lint, ledger and static activation checks pass. The
native test makes 13 real upstream requests, all HTTP 200, without forced model
outputs or tool calls. Source and binary hashes remain intact. Its two owned
containers and internal network are removed; existing model services are unchanged.
No user project, profile or private corpus is mounted. Raw reasoning is not saved.

[Structured evidence](native-work-resume140-evidence.json) binds the results to
the exact tested source. The later snapshot adds only evidence and ledger notes
to that source, and requires its own structural/document checks. This validates
these two OpenCode JSON resume cases only. It does not accept other native clients,
approval/change requests, plan-version continuity, browser interaction, independent
review, the command catalog or the overall integration. Skills remain deferred.
