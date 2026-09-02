# Changelog

**English** · [Español](CHANGELOG.es.md)

All notable changes to this project are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and versioning follows [SemVer](https://semver.org/).

## [Unreleased]

## [1.15.0] - 2026-09-02

### Added — `live-visibility` initiative (2026-09-02)

- **Live progress while tasks run.** New deterministic script `agent-kits/shared/progress-report.py` (`line` / `active` / `session`, `--json`) built on a `parse_ledger()` now exposed by `ledger-lint.py` (CLI output byte-identical on every existing ledger). Three new informative hooks in `hooks/hooks.json`: `progress-line.sh` (PostToolUse on any `docs/roadmap/*/tasks.md` edit → one-line `systemMessage` "📋 <slug> · T-04/12 (33%) · phase 2/4 · in progress: T-05 …", debounced), `subagent-progress.sh` (SubagentStop → active initiatives) and `session-context.sh` (SessionStart `startup|resume|compact` → `additionalContext` with active initiatives, open tasks and orphan usage-meter markers, so a resumed or compacted session picks up where the ledger says). Zero output when nothing is active.
- **Opt-in statusline** `statusline/roadmap-statusline.sh` (model · session cost · context % · roadmap progress), wired through `/setup` step 5-bis (default No; never overwrites an existing `statusLine`). `lint_plugin.py` gains `lint_hooks()` (valid JSON, existing commands; executable bit is a warning). Docs ES+EN (`CONVENTIONS`, `FLOWS` §6b, `observability`, READMEs).

### Added — `deterministic-guardrails` initiative (2026-09-02)

- **The implementer's hard guardrails move from prose to a PreToolUse hook with tests.** `agent-kits/shared/guardrail-check.py` (+ wrapper `hooks/implementer-guardrail.sh`) denies, with a one-sentence reason: writes under `docs/roadmap/**` other than `tasks.md` (incl. `testing/**`), writes under `docs/security-scan/**`, writes to code while on `main`/`master`, `git push --force|-f|--force-with-lease|+refspec`, `git branch -D`, leaving the feature branch via `checkout/switch main`, `rm -rf` on `/`, `~`, `.git` or `.` — also inside `sh -c "…"`/`bash -c`/`eval`, without false positives on commit messages, `grep` or `echo`. Registered **only** in the agent's frontmatter `hooks:` (never in the global `hooks/hooks.json`: planner/evaluator/analyst legitimately write to `docs/roadmap/`) — recorded as [`ADR-007`](docs/knowledge/adr/). Configurable in `.claude/dev.json` → `"guardrails": false | {"alcance","git","ramaPrincipal"}`; without python3 it never blocks (warns once).
- **`scope-check.py`** compares the branch diff (committed + uncommitted + untracked) against the ledger's `Archivos` fields (globs, `(nuevo)`, folders; `**/` = zero or more dirs) and gates the adversarial review: exit 1 sends out-of-scope files back to the implementer as an Important gap without spending reviewers. Replaces the manual "git diff --stat only in scope" check in the implementer's DoD and in `quick-implement`.
- `lint_plugin.py` validates the native agent frontmatter fields `skills:` (exists, ⊆ `dependencies.skills`, warns above 16 KB of preloaded content) and `hooks:` (commands exist). Conventions ES+EN: two hook classes — informative (global, always exit 0) and guard (PreToolUse deny, agent-scoped only, script+tests, opt-out). `ledger-lint.py` recognises «Fase única» summary rows (no more false legacy warning on fast-track ledgers).

### Added — `adversarial-review` skill (2026-09-02)

- **The two-lens adversarial review becomes a reusable skill** (`skills/adversarial-review/`) — the single source of the method that `/dev-cycle` Phase 3 and `quick-implement` now invoke, also usable on demand on a branch or range without a ledger ("review this diff"). Lens A (spec/plan/constitution conformity, per-criterion ✓/✗) and Lens B (correctness defects only) keep their literal prompts; a **conditional Lens C (security)** runs only when `scripts/review-lens-select.py` detects sensitive paths (auth/session/token/secret/crypt/permissions/upload/payment/.env/Dockerfile/workflows, token-anchored, prose and `docs/**` excluded) or added lines (`eval(`, `os.system`, `innerHTML`, `pickle.loads`, `yaml.load(`, SQL concatenation, keys/tokens…) — configurable via `.claude/dev.json` `"revision": {"lenteSeguridad": "auto|siempre|nunca"}`. Merge + Critical/Important/Minor grading, 3-attempt loop with state hand-over, rebuttal with evidence, ledger table «Revisión de dos lentes — intento N», `docs/knowledge/` promotion and Jira comment are all in the skill; `commands/dev-cycle.md` shrinks by 25 lines and keeps only the orchestrator's part (attempt counter, `[revisión]` worklog per attempt). Lesson [`LES-010`](docs/knowledge/lessons/) records why (real catch rate across 5 initiatives). CI (`ci.yml.MANUAL-COPY`) now runs pytest per folder, so the new suites are covered.

### Fixed — `debt-cleanup` (2026-09-02)

- Every debt the three initiatives above had accepted is now paid: `progress-line.sh` debounce is atomic (`flock` + rename; honest fallback without `flock`), task titles with inner bold render clean, `hooks/hooks.json` is `100644` and the linter warns on executable JSON; the implementer guardrail is case-insensitive (Windows) and allows the roadmap index `docs/roadmap/README.md` (`CALIBRATION`/`DRIFT`/`BACKLOG` stay denied by design — they belong to commands); Lens C stems are bounded (`tokenizer.py`/`helmet.py`/`author.md` no longer trigger) and `.claude/dev.json` `revision.excluir` globs exclude paths from the route heuristic (content still counts); `/setup` step 5-ter asks for `revision.lenteSeguridad` (auto/siempre/nunca); `lint_plugin.py` warns when `ci.yml.MANUAL-COPY` drifts from `.github/workflows/ci.yml` (+ `tests/test_ci_manual_copy.py`) and no longer flags compound skill names as generic. New **shell suite for hooks** `tests/test_hooks_shell.py` (20 cases: the 3 progress hooks, the guardrail wrapper incl. no-python3 degradation, the 2 legacy hooks and the statusline). `docs/observability.md` (+EN) gains a 3-step manual check of the hooks in a real Claude Code session.

### Changed

- **`jira-granularity` closed**: the manual dry-run gate (T-08) ran against a disposable issue on the test project and verified the four connector capabilities (markdown checklist in the description via `editJiraIssue`, several worklogs per issue, review comment with the fixed template, `[revisión]` worklog). Two findings, recorded as [`GOT-004`](docs/knowledge/gotchas/) and applied to `jira-sync`: the closing transition is resolved by `statusCategory.key == "done"` (never by name or fixed id — transition "Done" landed on a localised status), and issues are created with an **explicit `assignee`** (`me` | `none`, asked once and persisted in `.claude/jira.json`) so a project default assignee never notifies a teammate. `docs/atlassian-connector-notes.md` extended (markdown in description/comments/worklogs, `\|` escaping in cells).

## [1.14.1] - 2026-08-20

### Changed

- **Neutral placeholders across every example, so the public repo carries no environment-specific values.** The plugin metadata's author email now uses the maintainer's GitHub noreply identity, and every sample that named a concrete Atlassian site, Jira project key, Confluence space or in-house project was replaced with neutral stand-ins (`PROJ` / `PROJ-59`, `DOCS`, `miapp`, `<usuario que autoriza>`, generic source paths). Touches `skills/jira-sync/SKILL.md` and its picker template, `skills/confluence-publish`'s asset templates and `confluence.example.json`, `agents/nemesis.md` plus its report schema, `agents/documenter.md` with `agent-kits/documenter/taxonomy.md`, and the roadmap history. **No behaviour change** — prompts, scripts and tests are untouched in substance; only the illustrative values differ.

### Docs

- Closed the documentation gap for this release's two initiatives (curated Confluence policy, `docs/knowledge/` technical memory): root `README.md`/`README.es.md` "What you get" table, `CLAUDE.md`, both documentation indexes (`docs/README.md`, `docs/en/README.md`), `agent-kits/shared/README.md`'s fragment inventory, and a short "technical memory" note on each involved agent's page (`docs/agents/evaluator.md`, `planner.md`, `implementer.md`, `qa.md`, `documenter.md`).

## [1.14.0] - 2026-08-20

### Added — `knowledge-split` initiative (2026-08-20)

- **One file per entry for `docs/knowledge/gotchas` and `LESSONS`, matching `adr/`'s pattern.** Predictable growth, selective reading and parallel-write collisions motivated the split: `docs/knowledge/gotchas/<slug>.md` and `docs/knowledge/lessons/<agent>-<slug>.md` replace the two aggregate files, migrated verbatim (same text, same acceptance trace) — recorded as [`ADR-006`](docs/knowledge/adr/).
  - **`README.md` becomes the entry index**: every row now links straight to its own file instead of `gotchas.md`/`LESSONS.md#agent`.
  - **`agent-kits/shared/knowledge-check.md` goes SELECTIVE**: read the index, then open only the specific entry file that matches the task's area — never the whole folder.
  - **File collision disappears for gotchas/lessons** (like `adr/` already had it): only the ADR's `id:` collision risk remains (D4, still deferred).
  - **Old `gotchas.md`/`LESSONS.md` become ≤5-line redirect stubs** (remote writes cannot delete files on a user's disk); freshly installed projects never see a stub — the folders are born directly.
  - Updated every writer (`/retro`, `debug-root-cause`, `qa`) and reader (`evaluator`, `planner`, `implementer`, `qa`, `documenter`) that cited the old paths, plus `docs/CONVENTIONS.md` rule 10, `docs/FLOWS.md` and `docs/INSTALL.md` (+ English mirrors), and a new Confluence-scope test fixture under `docs/knowledge/gotchas/`.

### Added — `knowledge-ids` extension (2026-08-20)

- **ADR-style IDs for gotchas and lessons, agent kept in the slug.** Extends `knowledge-split`'s one-file-per-entry split with sequential IDs matching the `ADR-NNN` pattern: `docs/knowledge/gotchas/GOT-NNN-<slug>.md` and `docs/knowledge/lessons/LES-NNN-<agent>-<slug>.md`, with `id: GOT-NNN`/`id: LES-NNN` in the frontmatter — the 12 existing files were `git mv`'d (real renames, content untouched) and numbered chronologically (backfill first, then by index order). `README.md` shows the ID per row; `knowledge-check.md`'s selective-reading globs and every writer/reader that cited a path pattern were updated to match. The `id:` collision note in `knowledge-write.md` now applies to all three families (ADR/GOT/LES), same mitigation (renumber + declare in the retro) — recorded as an amendment to [`ADR-006`](docs/knowledge/adr/).

### Added — `knowledge-capture` initiative (2026-08-20)

- **Cross-cutting technical memory for the plugin's agents, `docs/knowledge/`.** Generalizes the bookend pattern from `agents/nemesis.md` (`docs/security-scan/STATE.md`+`MEMORY.md`) into a project-wide, always-active (no opt-in) memory of design decisions (ADR), proven traps (gotchas) and process lessons — "what should never have to be re-discovered".
  - **Where it lives:** `docs/knowledge/adr/ADR-NNN-<slug>.md` (template `agent-kits/shared/templates/adr.md`), `docs/knowledge/gotchas.md` and `docs/knowledge/LESSONS.md` (grouped by agent), with a manual index `README.md` (the generated index + linter stay deferred until there is evidence of need — >15 entries or an ADR ID collision).
  - **Anti-bureaucracy threshold:** an ADR only if a decision closes a real alternative AND (affects 2+ pieces or was taken at a decision gate); a gotcha only if it cost at least one debugging cycle or nearly broke a product guarantee. Target: 0-2 entries per initiative.
  - **Writers:** `planner`/`implementer` write an ADR when a design decision crosses the threshold; `debug-root-cause` writes a gotcha when it closes its Phase 4 (confirmed root cause); `qa` writes a gotcha when a justified flaky turns out to be a pattern (2+ cycles), not an accident; `/retro` now produces a **second output** of qualitative technical learnings, in addition to its numeric `CALIBRATION.md` row.
  - **Reading loop (`agent-kits/shared/knowledge-check.md`):** `evaluator`, `planner`, `implementer`, `qa` and `documenter` read the short index first and open only the entries in their area (progressive disclosure, protecting the `2026-08-10-token-diet` investment) — `evaluator` → `LESSONS.md`; `planner` → `adr/`+`LESSONS.md`; `implementer` → `adr/`+`gotchas.md`; `qa` → `gotchas.md`; `documenter` → everything.
  - **Proof of the mechanism:** the "three lessons from the first real calibration" that used to live hardcoded in `agents/evaluator.md` were migrated verbatim to `docs/knowledge/LESSONS.md#evaluator` — the prompt now reads them from the file. Verified with a disposable smoke-test evaluation: the three lessons are still cited and applied, sourced from the file, not the prompt.
  - **Seed backfill:** the 5 existing `retro.md` files' technical learnings, and `confluence-policy`'s 5 design decisions as the first 5 ADR.
  - Retires the "Notas de implementación" section from the planner's `tasks.md` template (the qualitative record now belongs in `docs/knowledge/`, not a catch-all drawer). `docs/knowledge/**` is explicitly documented as publishable by default in `confluence-publish`'s scope (with its own fixture/test). New rule 10 in `docs/CONVENTIONS.md` (+ English mirror) and an extension of `docs/FLOWS.md`'s trigger→artifact matrix (+ English mirror).

### Added — `confluence-policy` initiative (2026-08-20)

- **Explicit publication policy for Confluence, closing 5 gaps of the publish/pull circuit before the first real `enabled: true`.** The mirror had a policy-free default (`include: ["**/*.md"]` + two exclusions): it would have published the duplicated EN tree, the plugin's own internal docs (`docs/examples/`, `docs/agents/`) and all 11 roadmap initiatives in full. Now the default `exclude` is **curated** (opt-out, decision D1): out go `docs/en/**`, `docs/examples/**`, `docs/agents/**`, `docs/**/atlassian-connector-notes.md`, and each initiative's plan/ledger (`improvement-plan.md`, `tasks.md`, `test-plan.md`) — Confluence keeps the **decision** (`spec.md`), the **budget** (`evaluation.md`) and the **result** (`retro.md`), not the execution board.
  - **Missing triggers closed** (D3): `implementer` now syncs Confluence when **closing each phase** (not per task, not only at the end) — with an explicit note that `tasks.md` itself stays out of the mirror by policy even though the trigger fires. `/retro`, `/spec-drift` and `/roadmap-brief` now apply the shared opt-in step at their close, same as the rest of the chain.
  - **qa's binary evidence** (D4): `**/testing/**` is excluded by default — the qa report embeds screenshots the Atlassian connector cannot attach, which used to publish with broken images. The report stays local-only; `agents/qa.md` no longer declares `confluence-publish` as a dependency.
  - **New `confluence-scope.py`** (`skills/confluence-publish/scripts/`, +23 tests): the scope's single source of truth, with `--check` (fails with a named-invariant message if `docs/security-scan/**` is missing from `exclude`), `--status` (classifies every doc as in-scope/excluded and, in-scope, as synced/stale/pending against the manifest) and `--stage` (regenerates `docs/confluence/` from scratch, byte-for-byte, idempotently, refusing to touch a non-empty `--out` unless it is a recognizable prior staging, with a reserved marker file `_STAGING-LEEME.md` — never `README.md`, so it can never overwrite a real one — warning it is derived and must not be hand-edited). A custom `**`-aware glob-to-regex translator matches `glob.glob(..., recursive=True)` semantics (`**/x` also matches zero directories) rather than naive `fnmatch`. Hardened after an adversarial review round (3 critical, 3 important, 2 minor gaps, all with regression tests).
  - **Reverse mapping staged → canonical** exposed as a pure function (`staged_to_canonical`) plus a `--map` subcommand, consumed by `confluence-pull` so it always writes to the **canonical** file under `docs/`, never under the generated `docs/confluence/`.
  - `hooks/mark-docs-pending.sh` ignores `docs/confluence/**` so regenerating the staging does not mark itself "pending" in a loop.
  - Documentation: a normative "what ships and what doesn't" section in both Confluence skills, a trigger→artifact→publishes? matrix covering the 10 known triggers in `docs/FLOWS.md` (+ English mirror), and the bidirectional-sync paragraph in both READMEs rewritten to reflect the curated policy and the generated staging folder.

## [1.13.0] - 2026-08-18

### Added

- **Estimation loop closed with verified numbers.** Following the first `/retro`, the findings it surfaced are now fixed at the source rather than only noted:
  - **AI hours re-derived with the calibrated ratio** in the 9 measured `generacion:` blocks and in every ledger summary row (~40 % lower — they had been derived with the uncalibrated 300.000 default). Tokens are untouched: they are the measurement, hours are the derivative, and each block's `ratio_usado` now says which ratio produced it, so the arithmetic stays auditable. Retros and `CALIBRATION.md` restated to match.
  - **Real cost in €, at last.** `rates-verify` read the official pricing page and wrote Claude Opus 4.8's standard prices into `.claude/rates.json` ($5/M input · $25/M output · $6.25/M cache writes · $0.50/M cache reads): the process cost of the 5 measured initiatives is **12,35 €**, replacing nine `eur: null`. The same verified prices seed `rates.example.json` so a new project starts with real figures. `tipoCambioUsdEur` stays flagged as an **assumption**, not a verified datum.
  - **`evaluator` now carries the three lessons** from the calibration: separate human-equivalent hours (value) from AI hours (schedule) instead of mixing them; budget the **process cost** as its own line; and give the adversarial review its own line, sizing by type (prose = minutes · prose + tests = ×2 · product code = hours).
  - **Root cause of the double count fixed where it originates:** `planner` P0 and the `tasks.md` template now state that the plan window is written **identically** in both files and why (the dashboard deduplicates it), so nobody "fixes" it by making them differ.
  - `.gitignore`: local state (`usage-state.json`, `jira-state.json`, `confluence-state.json`) excluded — machine state, not project state; `rates.json` is versioned on purpose. Since `.claude/` is a protected path for remote tools, the file ships as **`rates.json.MANUAL-COPY`** at the repo root (valid JSON, copy it to `.claude/rates.json`) — same pattern as `ci.yml.MANUAL-COPY`.
  - Titles that surface in publishable dashboards (`spec.md` H1 and `descripcion:`) no longer name third-party products.
- **First `/retro` of the project — the estimation loop is now closed with real data.** New `docs/roadmap/CALIBRATION.md` with one row per measured initiative and a **calibrated ratio of 479.326 tokens/hour** (median of 5 samples), which `usage-meter.py` already picks up in place of the uncalibrated 300.000 default — AI hours reported (and therefore logged to Jira) drop ~40 % and line up with the clock. The file documents the **exact, non-circular definition** of the ratio: measured billable tokens ÷ wall-clock time of the measurement windows, never the meter's own derived hours, plus its known limits. `retro.md` written for the 5 initiatives with measured data (`sdd-hardening`, `workflow-polish`, `plugin-dev`, `subagent-personas`, `quick-implement`), each with estimated-vs-actual, cause and suggested adjustment, and 4 accumulated learnings.

### Fixed

- `roadmap-dashboard`: a measurement window declared by **two artifacts** (the `planner` measures `improvement-plan.md` and `tasks.md` together and writes the same block in both, by design) was counted **twice** in "process cost" — `sdd-hardening` showed 85.077 tokens instead of its real 58.914 (+44 %), and the portfolio total was inflated by the same amount. Now an identical real measurement is deduplicated (same window, same tokens, same hours) and the cell notes `ventana compartida`. Two regression tests: the shared window counts once, and `estimado` blocks that share reference dates but hold **different** per-artifact estimates are still summed (a defect in the first version of this very fix, which lost 0,8 h from `coste-generacion`).
- `docs/roadmap/*/spec.md`: the `descripcion:` field no longer names third-party products — it is the field that surfaces as the initiative title in dashboards and metrics that get published to Confluence. Bodies keep their historical wording.

## [1.12.0] - 2026-08-13

### Added

- **`quick-implement` skill** — a **natural-language** shortcut into the `/dev-cycle` fast track, for the case where the user does not type the slash: commands only fire with `/`, while skills auto-invoke from their description. It is a thin entry point, not a second method — it resolves `commands/dev-cycle.md` with `find` and follows its fast track (single source: if the method changes there, it changes here), and stops with a warning if it cannot find it. Ships with the hijacking risk mitigated by design: **negative triggers** in the description (do not use it with unknowns, multi-file work, when a budget is wanted, when the user already typed `/dev-cycle`, or for a one-line change) plus a **mandatory suitability filter** as step 1. The ledger, the two-lens review and `qa-gate` are all preserved.
- Two-lens review passed with 10 findings fixed: a wrong phase pointer in the skill (it said "Phase 4 (qa)", but `qa` lives INSIDE Phase 3 and Phase 4 is `documenter` — following it literally would have skipped the `qa-gate` and triggered documentation the fast track leaves opt-in), the `find` not covering "work on the plugin repo itself" (the installed copy won), the measurement protocol contradicting the no-overlap rule, the skills list missing from `plugin.json`/`marketplace.json` and from the READMEs' prose list while the badge already said 11, the missing `docs/FLOWS.md` update (both languages), and remaining method duplication in step 2.

### Fixed

- `roadmap-dashboard`: a fast track that comes from a **backlog spec** (so it does have `spec.md`) is now detected by the marker the ledger itself declares (`| **Plan** | n/a — vía rápida`) instead of by the absence of a spec — before, it was classified as "spec only" and raised a spurious "spec `implementada` but no improvement-plan.md" warning, which would go red in CI with `--strict`. Also fixes `subagent-personas`, which had the same shape. New regression test.

## [1.11.2] - 2026-08-13

### Fixed

- **Mermaid diagrams did not render on GitHub** ("Unable to render rich display · Cannot read properties of undefined (reading 'render')"): the labels used `\n` as a line break, which GitHub's renderer does not accept. All **26 diagrams** across the repo (both READMEs, `docs/FLOWS.md` ×9, `docs/en/FLOWS.md` ×9, the doc indexes and the implementer/qa agent docs) now use the portable `<br/>`, verified by rendering every one of them with mermaid-cli.
- New guard `tests/test_mermaid_blocks.py`: fails if any `mermaid` code block uses `\n` as a line break, has an unclosed fence, or does not declare a diagram type on its first line. Static and dependency-free, so it runs in CI.

## [1.11.1] - 2026-08-13

### Added — bilingual EN/ES documentation (2026-08-13)

- **English as the repo's primary language**: `README.md` rewritten in English (same showcase: badges, cover Mermaid diagram, comparison, quick start) plus `README.es.md` holding the Spanish original, with a language switcher in both. Key docs now have an English mirror under **`docs/en/`**: README (index), INSTALL, CONVENTIONS (same §1-§9 numbering — existing "rule N" citations still hold), FLOWS (all 9 Mermaid diagrams with translated labels) and observability; the originals carry the language switcher too. Per-agent docs and the roadmap remain Spanish-only (noted in the EN index). Tokens parsed by the scripts (states `borrador/aprobada/…` — draft/approved, `generacion:`, `- **Tipo**:`) stay in Spanish in the English docs as well, with a gloss on first use. Bilingual sync rule added to `CLAUDE.md`.
- README: live CI badge (GitHub Actions) plus a version badge (latest tag) and a "Quality and CI" section describing what every push validates.
- README (EN and ES): **badge panel in three blocks** — status (CI · version · license · Python 3.11+), community (stars · forks · open issues · last commit · commits/month) and project nature (Claude Code plugin · Spec-Driven · 8 agents · 11 commands). The downloads badge was dropped: GitHub only counts downloads of release **assets**, not marketplace installs or clones, so it does not reflect real plugin usage.
- New `release.yml` workflow (manual copy, like ci.yml): pushing a `v*` tag packages the plugin as a zip, creates the GitHub Release and attaches the zip, with the release notes extracted automatically from the CHANGELOG.
- README (EN and ES): **skills badge** (10) next to agents and commands. New `tests/test_readme_badges.py` guard: it compares each static counter badge against what is actually in `agents/`, `skills/` and `commands/`, in both languages, so the counts cannot silently drift. `ci.yml` now runs the repo suites in a **loop** (`for t in tests/test_*.py`) instead of a fixed list, so any new suite joins CI automatically.

### Changed — documentation focused on the plugin itself (2026-08-13)

- **Dropped the "vs other plugins" comparison** from the README (EN and ES): the section becomes **"What you get" / "Qué te llevas"**, a 12-capability table stated positively along with **how each one is guaranteed** (a specific script, gate or agent). The documentation no longer defines itself by contrast with third-party products.
- **References to external engines are now generic** across the documentation and in the agent/skill/kit prompts: "external SDD orchestrator", "external engine". `/dev-cycle` Mode A interoperability **remains intact** (the flag still works); only the way it is documented changes.

- **Bilingual CHANGELOG**: `CHANGELOG.md` is now the English one (and the source for the GitHub Release notes), with `CHANGELOG.es.md` mirroring it in Spanish — same version headings, same order, same footer links. `release.py` warns if either of the two is missing the entry for the version being published.

### Fixed

- `ci.yml.MANUAL-COPY`: the warning header was Markdown (it broke the workflow when copied as-is — invalid YAML on L1); it is now `#` comments and the file can be copied whole without editing.

## [1.11.0] - 2026-08-12

### Added — `sdd-hardening` initiative (2026-08-12)

- **Full self-sufficiency (no dependency on external engines)**: the **native chain is ALWAYS the default engine** for `/dev-cycle` (an external SDD engine only on explicit request). New **`.claude/dev.json`** config (opt-in, defaults off, created by `/setup`): `tdd` (RED-GREEN-REFACTOR with **evidence of the red** in the ledger), `worktree` (initiative in an isolated git worktree, with graceful degradation) and `subagentes` (**every task is implemented by a FRESH-context subagent**, with the 4 mechanics of the subagent cycle: deterministic brief produced by the new **`task-brief.py`** (+6 tests), brief-only, rich states `DONE/DONE_WITH_CONCERNS/NEEDS_CONTEXT/BLOCKED` and a persistent reviewer with `Critical/Important/Minor` severities).
- **Consumer project constitution** (`docs/CONSTITUTION.md`, opt-in via `/setup` with a template in the shared kit): permanent principles that the 6 writing agents read and cite (`constitution-check.md`), and that **lens A enforces** (violating an explicit principle = gap with a line citation). Verified end to end.
- **`/spec-drift`** (new read-only command): spec↔code drift for `implementada` (implemented) specs — fresh subagents check every criterion against today's code (`vigente ✓ / derivado ✗ / no verificable` — current / drifted / not verifiable, with evidence) → `docs/roadmap/DRIFT.md` plus an offer to run `/pm-cycle` on whatever drifted. Verified end to end.
- **Optional Given/When/Then criteria** (`- [ ] [GWT] CA-XX — Dado…, Cuando…, Entonces…`): spec template, analyst/discovery offer them for observable behaviour, qa translates them 1:1 into E2E tests, and **`coverage-check.py` requires them** in the test plan (new tests, including GWT without a test plan = red).
- **`debug-root-cause` skill**: systematic 4-phase debugging with mandatory evidence (minimal reproduction → isolation → tested hypothesis → fix + regression); `/dev-cycle` triggers it on qa's 3rd red BEFORE giving up — so the question that reaches the user comes with a diagnosis.
- **`docs/observability.md`**: positioning of cost (usage-meter) vs live activity (Agent-Monitor-style monitors), with hook coexistence verified.
- Backlog: `subagent-personas` draft spec (domain profiles for the fresh subagent).
- Two-lens adversarial review passed in 2 attempts: 21 findings from attempt 1 fixed and verified 21/21 (including a brief parser tolerant of code blocks, a robust GWT regex, per-assigned-task measurement in the classic flow, a persistent reviewer across handoffs, and a proposed — not applied — fix in the 3rd-red hook). Suites: 45 pytest tests plus 6 repo suites green.

### Added — `workflow-polish` fast track (2026-08-12)

- **The 3 missing workflow disciplines** (completing the native method repertoire): (1) **discipline when RECEIVING a review** — the implementer verifies each gap before fixing it and **rebuts incorrect findings with evidence** (`descartado (rebatido)` — dismissed (rebutted) — arbitrated by the orchestrator; rebutting does not consume an attempt); (2) **PARALLEL dispatch of independent tasks** (`subagentes: true`): batches of at most 3 in per-task temporary worktrees, reintegration validated on `feature/<slug>` before review, and **honest per-batch measurement** (`(medido, lote)` — measured, batch — with proportional distribution); (3) **6-step branch CLOSING ritual** (final verification, per-task commits, PR summary derived from the ledger, integration asking when unclear, worktree and marker cleanup, final states). First **measured** fast track of the plugin (3m of AI, 16k billable tokens).

### Added — `plugin-dev` fast track (2026-08-12)

- **`plugin-dev` skill** (meta-skill for developing the plugin itself, covering ALL of its pieces): canonical process for creating/modifying agents, skills, commands, kits and hooks — decision tree for the type of piece, naming and collision rules, mandatory frontmatter (model tiering, minimal tools, `dependencies`), determinism (scripts with tests + exit codes) and degradation without blocking, TDD-ish validation in strict order (test first → `lint_plugin.py` → suites with the same invocation as CI → adversarial self-review), documentation obligations per type of piece, and a catalogue of **anti-patterns seen in real reviews** of this repo. Includes fill-in templates for agents, skills and commands (`templates/`) — the agent one empirically verified against the linter's parser; the command one with `description`/`argument-hint` frontmatter and `$ARGUMENTS`, like the real commands.
- Two-lens review passed: 7 findings fixed and re-verified, 2 of them critical (the cited pytest invocation did not pick up the script suites in `tests/`; inline comments in the agent template made the linter reject any agent created from it). **Measured** fast track: 10m of AI, ~49k billable tokens.

### Added — `subagent-personas` fast track (2026-08-12)

- **Domain personas for the fresh subagent** (closes the backlog spec noted in sdd-hardening): a SHORT catalogue of 6 profiles in `agent-kits/shared/personas/` (`frontend` · `backend` · `db` · `devops` · `test` · `docs` — priorities, typical pitfalls, and the quality and evidence each domain demands, ~10 lines per persona so the catalogue stays maintainable), an **optional** `- **Tipo**:` (type) field per task in the planner template (assigned only when the domain is clear; no type → generic subagent, as before) and **deterministic injection into the brief** by `task-brief.py` (a "Persona de dominio" section ahead of the task). Degrades without blocking: a label with no persona in the catalogue → warning + generic. Strict TDD (+7 tests, including regressions: an example `Tipo` inside a code block does not inject a persona; types containing `/` or `..` cannot escape the catalogue).
- Two-lens review passed: 1 real defect (the `Tipo` inside fences, caught by lens B by execution) plus 4 documentation gaps, all fixed and re-verified.

### Roadmap-wide verification (2026-08-12)

- **All 9 roadmap initiatives audited and consistent**: ledger-lint green across every `tasks.md`; states closed where the work had shipped (qa-agent and nemesis-sca-iac **reconciled with an explicit note** — their ledgers predate the canonical ledger discipline; agent-best-practices, qa-strict and token-diet → `completado`/`implementada` — completed/implemented); jira-granularity deliberately stays at `en-revision` (in review) (T-08, dry-run against PROJ, still pending).
- `roadmap-dashboard`: **fast-track** initiatives (with only a `tasks.md`) now show up in the dashboard and the metrics ("fast track" phase, title taken from the ledger, aggregated measured cost); states carrying an emoji (`completado ✅`) no longer raise false inconsistency warnings. New tests.

### Fixed

- `ledger-lint.py`: "Fase 3" and "Fase 3-bis" no longer collide in summary validation (regression test 9/9).

## [1.10.0] - 2026-08-11

### Added — `coste-generacion` initiative

- **`agent-kits/shared/usage-meter.py`** (+ 35 tests): measures the **real generation cost** of every cycle artifact and every task by reading the tokens from the session transcript's `usage` over windows (`start`/`close`/`status` per artifact, dedupe by response, sidechains included). Converts to € (`rates.json`, reliability rule) and to **AI-hours via a calibrated ratio** (median `tokens/hora` from `CALIBRATION.md` > uncalibrated default from `estimation-defaults.md`). Model confirmed with the user: **dates = context · tokens = measurement · hours = tokens × ratio** — never wall clock. Degrades to `fuente: estimado` (source: estimated) and never blocks the flow.
- **`generacion:` block** in the frontmatter of spec/evaluation/plan/tasks (evaluator and planner templates plus the lightweight fast-track `tasks.md`); analyst/evaluator/planner and `/dev-cycle` start/close the meter (no-overlap rule in the orchestrators).
- **`/roadmap-metrics` — "Process cost" section**: what it cost to *produce* each initiative's artifacts (kept separate from implementation cost); an honest "no data" for artifacts without the block, never a made-up 0.
- **Per-task measurement (Mode B)**: a marker per `T-XX`; **measured** AI-hours land as "actual" in the ledger (`(medido)` — measured) and in the Jira worklog, without touching the working-day/hour-bank arithmetic in `worklog.py`.
- **`/retro` calibrates the tokens→hour ratio**: `tokens/hora` column plus a "Ratio vigente (mediana de N muestras)" summary line in `CALIBRATION.md`, consumed by the evaluator and the meter.
- **Human-readable `XhYm` durations** (Jira style, fixed by the user: `32m` · `1h 32m` · `18h`): single `usage-meter.py fmt` helper, applied in frontmatter, reports and the review template (the machine-parsed ledger columns stay decimal, an exception declared in the spec).
- Two-lens adversarial review passed in 2 attempts (22 findings from attempt 1 fixed and verified 19/19 on attempt 2, including the calibration parser with `300k` notation, corrupt state, transcript truncation and invented "0 tok").

## [1.9.1] - 2026-08-11

Adjustments on top of 1.9.0 after the design run-in with the user: per-attempt tracing in the review worklog and an entry gate in `/dev-cycle`.

### Added
- **Per-attempt tracing in the review worklog** (`worklog.py --attempt N`, only with `--kind revision`): each pass of the reviewer→implementer loop is logged as **its own worklog entry** (duration and date per attempt, comment `"[revisión] intento N de 3 — T-XX"`), and `jira-state.json` stores `reviewAttempts: [{intento, fecha, horas}]` so `/retro` can see what each round cost. The total is still the sum (implementation + all reviews); without `--attempt` the behaviour matches 1.9.0. Tests in `tests/test_worklog.py` (13/13). The Jira comment remains single and final ("review passed in N attempt(s)").
- **Entry gate in `/dev-cycle` (Phase 0-bis):** on start it asks **full flow** vs **fast track** — or the user **states it explicitly** ("fast track"/"quick"/`rapido`, "full flow"/`completo`) and no question is asked. The fast track skips spec/evaluation/plan (it creates a lightweight `tasks.md` and goes straight to `implementer`) but **keeps** the two-lens adversarial review and `qa-gate`; the lightweight ledger still tracks progress, hours and the Jira dump. Meant for small changes that can be described in a sentence or two.

### Fixed
- **CI** (`.github/workflows/ci.yml`): wires in the 1.9.0 tests that were still missing (`test_lint_plugin`, `test_qa_gate`, `test_ledger_lint`) plus the `lint_plugin.py` step. ⚠️ This file has to be copied **by hand** into the repo (path protected for the remote tooling); the one published in 1.9.0 was still running only dashboard+worklog.

## [1.9.0] - 2026-08-10

Adoption of best practices from the top agent collections (reference agent collections and the official Claude Code best practices), hardening of qa and of the orchestrator with deterministic gates, a token diet, and Jira granularity per phase/task with review publishing. See `docs/roadmap/2026-08-10-agent-best-practices/`, `docs/roadmap/2026-08-10-qa-strict/`, `docs/roadmap/2026-08-10-token-diet/` and `docs/roadmap/2026-08-10-jira-granularity/`.

### Added (jira-granularity — granularity + review in Jira)
- **Selectable dump granularity** in `jira-sync` (`.claude/jira.json` → `granularidad: "tarea" | "fase"`; default `"tarea"`, does not break existing installs). **Phase mode**: one issue per phase with its `T-XX` items as a checklist in the description; per-task comment and worklog on the phase issue; checklist ticked with `editJiraIssue`; the phase is Done only when all its tasks are `completado` (completed).
- **Reviewer result → Jira** (`jira-sync` Step 9, Mode B only): the `/dev-cycle` reviewer emits output **structured per criterion** (`T-XX` → criterion → ✓/✗); a comment is posted with the **final result + "review passed in N attempt(s)"** against the fixed `agent-kits/shared/review-report.template.md` template, honouring the dump granularity. Idempotent (`reviewComentado`).
- **reviewer→implementer loop capped at 3 attempts** in `/dev-cycle` (same pattern as the qa→implementer loop): reviewer→fix→re-review; on the 3rd with gaps it stops and asks.
- **Review worklog** in `worklog.py`: new `--kind implementacion|revision`; the `[revisión]` entry accumulates all passes of the loop and carries a `worklogImpl`/`worklogRevision` breakdown in `jira-state.json` (for `/retro`) without distorting the daily cap or the issue total. Tests in `tests/test_worklog.py` (12/12).

### Added (token-diet — reducing token consumption)
- **`agent-kits/shared/read-discipline.md`**: reading discipline for recon (grep/glob before `Read`, `Read` with `limit`, ignore `node_modules`/`vendor`/lockfiles/minified files, sample patterns). Adopted by documenter, nemesis and evaluator in their recon via `$SHAREDKIT`.
- **`agent-kits/shared/output-discipline.md`**: output discipline in handoffs (agent's final message ≤ ~12 lines, data rather than a report; the detail lives in the artifacts). Adopted by evaluator, planner, implementer, qa and documenter.
- **Atlassian payload filtering**: a rule in `jira-sync` to request explicit `fields` and bound `maxResults` on every connector call (roadmap-live already did this).
- **Progressive disclosure**: the per-phase detail for documenter (writing guide → `agent-kits/documenter/redaction-guide.md`) and for nemesis (tool interpretation → `agent-kits/nemesis/interpretation.md`) is read on demand when entering that phase, not always.
- **`rates-verify` skill**: queries the official pricing docs (WebFetch) and writes `precioTokens` + `verificadoEl` into `.claude/rates.json`; never invents a price if it cannot read the docs. Offered in `/setup`; evaluator/planner stop flagging `⚠️ verificar` when the price is reliable and recent.

### Added (qa-strict — deterministic gates)
- **`agent-kits/qa/qa-gate.py`**: qa's green/red verdict is decided by a script with an exit code over `results.json` (0 failed, 0 unjustified flaky; justifications with real text via `--justify`). Absence of evidence is red. Tests in `tests/test_qa_gate.py` (8/8).
- **`agent-kits/shared/ledger-lint.py`**: mechanical validation of the `tasks.md` ledger (state vocabulary, `completado` ⟹ criteria ticked, summary adds up, unique IDs; legacy degrades to a warning). Invoked by implementer (DoD), qa (P1) and /dev-cycle. Tests in `tests/test_ledger_lint.py` (8/8).
- **`agent-kits/qa/coverage-check.py`**: criteria↔tests coverage gate — broken references in the "Cubre (tests)" field are errors; tasks with no coverage and unreferenced tests are listed for triage.
- **`hooks/ledger-lint-warn.sh` hook** (PostToolUse on `docs/roadmap/*/tasks.md`): runs ledger-lint in warning mode on every ledger edit; never blocks, exits silently without python3.
- **Strict Playwright** in the qa runner: `retries: 2` (flaky identified for the gate), `forbidOnly: true`, timeout configurable via `QA_TIMEOUT_MS`, traces on failure.
- **/dev-cycle**: qa→implementer correction loop **capped at 3 attempts** with an explicit counter (on the 3rd red: stop and ask), and adversarial review with **two lenses in parallel** (spec conformance · quality/robustness) with gap merging and dedupe.
- **Optional `API-xx` and `A11Y-xx` blocks** in the `test-plan.md` template (endpoint smoke tests with curl; accessibility with axe-core under opt-in); qa runs and reports them outside the gate threshold in this iteration.

### Added
- **Model tiering** across the 8 agents: `model` field proportional to complexity (wshobson's criterion) — `pdfy` = haiku; `documenter`/`qa`/`implementer`/`analyst`/`planner` = sonnet; `evaluator`/`nemesis` = opus.
- **`## ANTES DE CERRAR (DoD)` section** in the 8 agents: a definition of done with executable checks and the obligation to **show evidence** ("evidence over claims"). `qa` defines the explicit "green" threshold (0 `failed`, 0 unjustified `flaky` in `results.json`).
- **Adversarial diff review** in `/dev-cycle` (Mode B): a fresh-context subagent reviews the diff against the plan and reports only correctness/requirement gaps, before `qa`.
- **`agent-kits/shared/`**: shared fragments with a single source — `estimation-defaults.md` (estimation parameters) and `confluence-optin.md` (sync step) — referenced by `evaluator`, `planner`, `qa` and `documenter` (DRY).
- **Plugin linter** `scripts/lint_plugin.py` + tests (`tests/test_lint_plugin.py`), wired into CI: validates frontmatter (`model`, `tools`, `description`), name uniqueness, the `dependencies` graph (skills/kits/agents exist, no cycles) and warns about generic names at risk of collision in direct-copy-to-`.claude/` mode.

### Changed
- **Routing descriptions** for `evaluator`, `planner` and `nemesis` rewritten with trigger phrases ("Use it when…", nemesis with "PROACTIVELY") to improve auto-delegation; the routing/template detail moved into the prompt body.
- `evaluator` and `planner` read the estimation parameters from the shared fragment instead of duplicating the table; `qa`/`documenter` use the Confluence opt-in fragment.
- The `tools` frontmatter is documented with the rationale for each tool across the 8 agents (the "do not touch code" restriction remains semantic; `pdfy` is the only one without `Edit`).

### Fixed
- `planner.md`: duplicated "P7" step renumbered (P7 Jira / P8 Confluence).
- `nemesis.md`: removed the "§6/§11/§14/§17" references to a base system that did not travel with the plugin.
- Truncated templates completed: `agent-kits/evaluator/templates/evaluation.md` ("Next step" section) and `agent-kits/planner/templates/improvement-plan.md` ("Success metrics", "Changelog" and "Next step" sections).

## [1.8.0] - 2026-07-17

### Added
- **`analyst` agent** (requirements gathering): converses with the human choosing the technique (interview, examples, user stories, counterexamples) and **always** produces `spec.md` in a fixed format; iterates until the user approves and hands off to `evaluator`.
- **Shared budget config `.claude/rates.json`** (rate, token price, exchange rate, supervision ratio, margin, working day); read by `evaluator`, `planner` and `jira-sync`. Template in `agent-kits/evaluator/templates/rates.example.json`.
- **Actual vs estimated metrics**: `/roadmap-metrics` plus the generator's `--metrics-md` output (AI+supervision production, human hours and tokens, with deviations and a portfolio total).
- **`/retro`** (retrospective of a closed initiative) → `docs/roadmap/CALIBRATION.md`; the `evaluator` reads that history to **calibrate** future estimates (learning loop).
- **`/setup`** (onboarding in a single pass: rates + Confluence/Jira opt-ins).
- **`/roadmap-brief`** (portfolio one-pager to PDF via `to-pdf`) and **`/roadmap-live`** (live status from Jira: issues + hours logged by label; artifact or conversational).
- **`worklog.py` script** (part of the `jira-sync` kit) with tests: deterministic worklog computation, **daily** working-day cap and a **per-issue hour bank** (with re-banking); takes the arithmetic out of the prose. First-class **dry-run** mode in `jira-sync`.
- **CI** (`.github/workflows/ci.yml`): runs the tests, validates Python and JSON syntax, and checks version consistency (`release.py --check`). `release.py` warns if the CHANGELOG entry is missing.
- **Single reference for the Atlassian connector** (`docs/atlassian-connector-notes.md`) and a **table of config/state files** (rule 9 of `CONVENTIONS.md`).

### Changed
- `nemesis`: optional handoff (F8) to turn High/Critical findings into roadmap initiatives (via `analyst`/`evaluator`), connecting it to the chain.
- `implementer`/`jira-sync`: hour logging uses the `worklog.py` script rather than manual arithmetic.

## [1.6.0] - 2026-07-15

### Added
- **`jira-sync` skill**: dumps a plan (`tasks.md`) to Jira via the Atlassian connector (Rovo MCP). Offered **when the plan is created** (opt-in in `.claude/jira.json`, like Confluence). Destination picker with **dual mode**: interactive artifact in Cowork/desktop (`assets/jira-picker.template.html` — search projects, resolve issue keys/URLs, find a parent by key/text/JQL) and **conversational** in CLI/VS Code. The **issue type is derived from the parent's hierarchy** (Epic/Initiative → Task/Story; Task/Story → Subtask; no parent → standalone Task), discovered via metadata rather than hardcoded. It can **create a new epic** for the initiative. Idempotent via `.claude/jira-state.json`.
- **Automatic hour logging + closing in Jira**: on completing each task, `implementer` invokes `jira-sync` to log **AI time (exec.) + Supervision** (actual→estimate) and transition the issue to *Done* (transition discovered, not fixed). Configurable **daily working-day cap** (`horasJornada`, 8h/7h) with a **per-issue hour bank**: when the day is filled it asks (stop / continue / bank) and the excess is logged on later days, always dated to the current day (never post-dated).
- **`planner`'s `tasks.md` template** extended with **AI time (exec.)** and **Supervision** per task (on top of human time), and equivalent columns in the progress summary.

### Changed
- `planner` (offers the dump when creating the plan) and `implementer` (reflects progress) declare the `jira-sync` skill; `/dev-cycle` integrates it; `/pm-cycle` no longer duplicates the conversational Jira handoff.

## [1.5.1] - 2026-07-15

### Added
- **`scripts/release.py`**: bumps the version **consistently** in all three places (`plugin.json` and the two fields in `marketplace.json`), validates that they match and creates a commit + tag. Prevents the failure of forgetting `marketplace.json` (which leaves the client unable to see the update).
- **Dashboard tests** (`tests/` with fixtures) and **warnings** in `roadmap-dashboard`: the generator emits on `stderr` when it cannot read an expected field (possible label change in the templates) or detects state inconsistencies, with `--strict` for CI.

### Changed
- `docs/INSTALL.md`: warning about **not placing the git repo in a cloud-synced folder** (OneDrive/Dropbox…) because of lock/index conflicts, plus use of the release script.

## [1.5.0] - 2026-07-15

### Added
- **PM (product) role separated from development**: the **`/pm-cycle`** command (spec → evaluation; closes at the go/no-go gate and offers a handoff to `/dev-cycle`; opt-in outputs: PDF brief and a Jira epic) and **`/pm-backlog`** (prioritizes the portfolio by reading every `evaluation.md` → `docs/roadmap/BACKLOG.md`).
- **`roadmap-dashboard` skill** + **`/roadmap-status`** command: scans `docs/roadmap/*/` and generates a dashboard in **HTML** (local view), **Markdown** (for Confluence) or **JSON** with status, priority and budget per initiative.
- **`confluence-pull` skill** + **`/confluence-pull`** command: the **reverse** direction of publishing (Confluence → local `docs/`) for PMs without git; preserves the local frontmatter, warns about conflicts and confirms before writing. Reuses the `.claude/confluence-state.json` map.
- **Roadmap dashboard publishable to Confluence**: `confluence-publish` regenerates `dashboard.md` before publishing whenever `docs/roadmap/` changes, so a PM can see the real status without git.

### Changed
- Documentation and indexes (`CLAUDE.md`, `docs/README.md`) updated with the new commands and skills; Confluence sync described as **bidirectional**.

## [1.3.1] - 2026-07-10

### Added
- **`documenter` agent**: generates and maintains the project's technical and product documentation under `docs/`, with a structure **derived from the project itself** (it does not impose folder names; it derives them from the repo's layout and vocabulary). Covers index, RAG-INDEX, architecture, stack, system units, guides and product; idempotent; proposes a structure and confirms before writing. It runs **when a plan's cycle closes** (implementation done + `qa`'s automated tests green), as a handoff from `qa`, **not task by task**. Includes the `agent-kits/documenter` kit (`taxonomy.md` + generic format templates). Syncs the docs to Confluence (opt-in).
- **`implementer` agent**: implements an approved plan phase by phase (writes the project's real code, on a branch), marking `docs/roadmap/<…>/tasks.md` as the **canonical ledger** of per-task progress; honours guardrails and hands off to `qa`. It is the only agent that modifies code.
- **`/dev-cycle <objetivo>` command** (`commands/dev-cycle.md`): orchestrator that drives the chain by invoking each agent by name (without relying on auto-selection), with control gates (go/no-go, plan OK, qa green). Your `evaluator` and `planner` **always** generate the artifacts under `docs/roadmap/` (spec, evaluation, plan, tasks); planning is never delegated. **Optional external engine**: if the user asks for it, it delegates only **execution** (implementation/TDD/review) working against your `tasks.md`; if not, it uses the native chain (`implementer` + `qa`). No hard dependency on external engines.
- **Canonical ledger rule** (rule 8 of `CONVENTIONS.md` + a banner in the `tasks.md` template): a plan's progress is recorded only in `tasks.md`; any implementer — including external SDD orchestrators — must update it; their own ledgers are mirrors, not the source.

### Changed
- **Per-phase state transitions**: artifacts no longer stay at `borrador` (draft). `/dev-cycle` (and the agents when run standalone) move spec/evaluation/plan/tasks to the state that applies at each gate (go → spec `aprobada`/eval `completado`; implementation start → plan `en-progreso`; green close → plan `completado`/spec `implementada`; no-go/cancellation → `cancelado`/`obsoleta`). Map in rule 7 of `CONVENTIONS.md`.
- Work chain extended to `evaluator → planner → implementer → qa → documenter`; `qa` hands off to `documenter` once the tests are green.
- Documentation and indexes updated (`README.md`, `docs/README.md`, `docs/CONVENTIONS.md`, `CLAUDE.md`) with the new agents, the command and the with/without external-engine modes.

## [1.3.0] - 2026-07-10

### Added
- **Shared `confluence-publish` skill**: publishes/mirrors `docs/` to Confluence using the official Atlassian connector (Rovo MCP), with no bespoke integration. Guided assistant for non-technical people: connect → pick a space (with search) → browse the tree → pick a destination (space root or under an existing page) → name the project page → upload. Idempotent (creates/updates, does not duplicate).
- **Opt-in sync** in `planner`, `evaluator` and `qa` (new step "P7. Sync with Confluence"): when writing under `docs/`, they invoke the skill to reflect the changes. The first time it asks whether to sync; the decision is stored in `.claude/confluence.json` (`enabled: true/false`) and is not asked again.
- **Interactive tree browser** (`skills/confluence-publish/assets/tree-browser.template.html`): in Cowork/desktop it expands pages live via the connector; when a destination is picked it asks whether to use that page or create a child (with a name).
- **Conversational fallback** for the tree step in the Claude Code CLI and the VS Code extension (no artifact host).
- **Change detection without git**: `.claude/confluence-state.json` state manifest (content hash + `pageId` per document); publishes only what changed (create/update/obsolete), idempotent and independent of commits/dates.
- **`PostToolUse` hook** (`hooks/hooks.json` + `hooks/mark-docs-pending.sh`): deterministic trigger that, on editing under `docs/`, leaves a `.claude/.confluence-pending` marker (it does not publish; it excludes `docs/security-scan/`). The actual publishing is done by the skill.
- Example config `skills/confluence-publish/assets/confluence.example.json`.

### Changed
- Documentation updated (`README.md`, `docs/README.md`, `docs/INSTALL.md`, `CLAUDE.md`): new skill, registering the Atlassian connector per environment (Cowork vs CLI/VS Code), opt-in behaviour and compatibility matrix.
- Declared dependencies of `planner`, `evaluator` and `qa`: added the `confluence-publish` skill.

### Security
- `docs/security-scan/**` (sensitive data from the `nemesis` agent) is explicitly **excluded** from the Confluence sync.

### Notes / Limitations
- Deleting a `.md` does not delete the page in Confluence: the Atlassian connector exposes no delete/archive operation, so the page is marked as obsolete and listed for manual deletion.
- Syncing requires registering the Atlassian connector once per environment (see `docs/INSTALL.md`).

## [1.2.0] - earlier

Versions predating the introduction of this changelog: a bundle with the `nemesis`, `evaluator`, `planner`, `pdfy` and `qa` agents, and the shared `cybersecurity` and `to-pdf` skills. Packaged as a plugin + marketplace.

[1.15.0]: https://github.com/daycry/custom-agents/releases/tag/v1.15.0
[1.14.1]: https://github.com/daycry/custom-agents/releases/tag/v1.14.1
[1.14.0]: https://github.com/daycry/custom-agents/releases/tag/v1.14.0
[1.13.0]: https://github.com/daycry/custom-agents/releases/tag/v1.13.0
[1.12.0]: https://github.com/daycry/custom-agents/releases/tag/v1.12.0
[1.11.2]: https://github.com/daycry/custom-agents/releases/tag/v1.11.2
[1.11.1]: https://github.com/daycry/custom-agents/releases/tag/v1.11.1
[1.11.0]: https://github.com/daycry/custom-agents/releases/tag/v1.11.0
[1.8.0]: https://github.com/daycry/custom-agents/releases/tag/v1.8.0
[1.6.0]: https://github.com/daycry/custom-agents/releases/tag/v1.6.0
[1.5.1]: https://github.com/daycry/custom-agents/releases/tag/v1.5.1
[1.5.0]: https://github.com/daycry/custom-agents/releases/tag/v1.5.0
[1.3.1]: https://github.com/daycry/custom-agents/releases/tag/v1.3.1
[1.3.0]: https://github.com/daycry/custom-agents/releases/tag/v1.3.0
