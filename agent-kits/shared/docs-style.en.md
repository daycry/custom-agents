<!--
  SHARED FRAGMENT: the plugin's technical-writing guide. Loaded (one line + fallback) by documenter,
  analyst, planner and architect when they write, and by lens A of adversarial-review ONLY when the
  initiative is prose. Spanish source: docs-style.md (same substance, not a literal translation —
  rule 8 applied to itself). If you change a rule here, change it there.
-->

# Technical writing — shared step (`docs-style`)

Eight rules. Each with the tell-tale sign and a before/after taken from this repo. They are a review
criterion only when **citable** (rule + line): anything that breaks no rule is taste, not a gap.

| # | Rule | Sign it is broken |
|---|---|---|
| 1 | **Short sentences.** One idea per sentence; ≤ ~25 words. If you need "which… that… and which", cut. | Sentences spanning 3+ lines; more than two subordinate clauses. |
| 2 | **Active voice.** Who does what: "`ledger-lint` validates the ledger", not "the ledger is validated". | "must be", "is validated by", "will be generated". |
| 3 | **One concept per paragraph.** Open with the claim, follow with the why. | Paragraphs that switch topic halfway; an "additionally" that opens a new subject. |
| 4 | **Tables to compare, prose to explain.** Options, fields, states → table. Why it was decided → prose. | A one-row table; a six-bullet list with identical structure (that is a table). |
| 5 | **Real examples from the code.** Paths, commands and outputs that exist (`agent-kits/shared/scope-check.py`, `exit 1`), not "the validation script". | "e.g. a module", "some test", invented or generic paths. |
| 6 | **No empty adjectives.** Replace "robust", "powerful", "simple", "complete" with the fact that proves it. | An adjective whose removal changes nothing. |
| 7 | **Headings that answer questions.** The reader asks "when does it publish?" → heading "What goes up and what doesn't". | "Introduction", "Considerations", "Miscellaneous", "Notes". |
| 8 | **Bilingual without literal translation.** The EN mirror says the same thing in native prose; machine tokens (`borrador`, `generacion:`, `- **Tipo**:`) stay in Spanish in both. | Calques ("realizar la publicación" ↔ "realize the publication"); a translated state token. |

## Before / after (from this repo)

| Rule | Before | After |
|---|---|---|
| 1, 2 | "Validation of the ledger must be performed by the script on every edit so that inconsistencies can be detected before the orchestrator reads them." | "`ledger-lint.py` validates the ledger on every edit. The orchestrator never reads an inconsistent one." |
| 3 | One paragraph covering the `scope-check` gate, then lens C, then the Jira worklog. | Three paragraphs: gate · lens · worklog. Each opens with its claim. |
| 4 | Six bullets "Lens A: … · Lens B: … · Lens C: …" with the same three attributes. | Table `Lens · What it checks · Against what · Output`. |
| 5 | "The agent runs the check script and, if it fails, returns it." | "`python3 "$SHAREDKIT/scope-check.py" docs/roadmap/<date>-<slug>` → exit 1 returns the out-of-scope files as an Important gap." |
| 6 | "A robust and complete system of informative hooks." | "Three hooks (`PostToolUse`, `SubagentStop`, `SessionStart`) that inform and always exit 0." |
| 7 | "## Considerations about Confluence" | "## What goes up and what doesn't" |
| 8 | ES "política curada" → EN "curated politics". | EN "curated publish scope". The states `borrador/aprobada` stay in Spanish in the EN text. |

## How to apply it

- **When writing** (`documenter`, `analyst`, `planner`, `architect`): check the text against the table
  before closing; prioritise 1, 2 and 5 — the costliest to fix later.
- **When reviewing** (lens A of `adversarial-review`, prose initiatives only): a writing gap cites
  **rule + line**; without a citation it is taste, not a gap. Grade `Minor` unless rule 5 or 8 breaks
  something verifiable (non-existent path, translated machine token) → `Important`.
- **Fallback** when this fragment is missing (partial install): short sentences, active voice, real
  examples, tables to compare. Never blocks.
