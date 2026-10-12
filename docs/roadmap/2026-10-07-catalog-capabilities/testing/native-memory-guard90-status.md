# Native producer memory scope

The current producer prompts require memory proposals through the shared curation service. The old architect guard still explicitly allowed legacy ADR/index writes, and implementer allowed direct knowledge writes. An actual OpenCode run created a synthetic legacy ADR against that contract. The red unit run has 48 failures and three controls passing.

Both producer guards now share one check for direct writes under `docs/knowledge/`. It directs new knowledge to `knowledge-curation.py`, retaining legacy bytes and the services that own journal/index persistence. The stale ADR/index allowlist is removed. The explicit scope opt-out and exact native owned-ID selection remain intact. This tool guard is not a filesystem sandbox, shell authorization or role authentication.

The shared and native dispatcher suites pass 316 cases on Windows and 316 on Linux. An installed OpenCode 2.0.12 plugin denies four producer memory writes and allows design plus a consumer agent's legacy-path write. Two actual child sessions retain their agent IDs and parent links; the owned implementer's spec write is blocked and the consumer child's write succeeds. Source hashes and zero active owned processes are verified after terminal exit. The provider is controlled loopback; no external inference or human semantic decision is credited. An earlier fixture launch failed because its source-path literal used unescaped Windows separators; that receipt is retained separately.

See [structured evidence](native-memory-guard90-evidence.json). Actual updated-guard acceptance in Claude/Codex, full current-source QA/coverage, human dashboard acceptance and independent review remain pending.
