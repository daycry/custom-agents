# Technical workflow context

**English** · [Español](../WORK-CONTEXT.md)

`/work-context` selects task guidance without starting another cycle. pm-cycle,
dev-cycle and manual roles use the same method. The trusted registry is
`agent-kits/shared/capability-catalog.json`; check its references with
`python agent-kits/shared/capability-route.py --check` in the repository. Resolve
the installed kit as described in capability-check.md.

The selector reads the task package's composer.json, package.json and
pyproject.toml: at most 128 KiB per manifest, depth 32, no linked paths and no
script execution. OneDrive CLOUD placeholders are supported; junctions, symlinks
and other reparse points remain excluded. Node/TypeScript alone do not imply React. `--stack` declares
task technology separately from detection. Areas are explicit filters; select
the affected package in a monorepo instead of loading every root-level stack.

On Python 3.9/3.10 without tomllib, the selector reports the TOML reading limit;
JSON manifests, explicit filters, the panel and task briefs remain available.

Planner stores comma-separated IDs in `- **Capacidades**:` and the reason in
`- **Procedencia de capacidades**:`. Briefs carry map pointers rather than full
manuals. Architect/implementer/reviewer/qa share criteria and scenarios, recording
changes driven by new facts in the ledger. Selection grants no tool access and
does not replace TDD, review, QA or Knowledge Gate. Missing optional components
warn and preserve the task contract.

Stack guidance is consolidated in stack-practices. Backend-practices,
frontend-quality and delivery-practices provide cross-cutting criteria.
Capability-audit evaluates utility/currency/overlaps; the panel inventories sources.
Outcome-evals prepares reproducible comparisons and summarizes existing JUnit;
activation checks do not demonstrate agent effectiveness or measured consumption.

## Optional structural context

`code-context.py` reads an existing Graphify-compatible artifact: nodes with
`_origin: ast`, `file_type: code`, relative paths and source_location `L<n>`;
AST EXTRACTED edges with valid endpoints and citations. It accepts links or edges.
Semantic nodes/reflections do not become approved knowledge.

Limits are 8 MiB, 20,000 nodes, 50,000 edges and depth 32; the result contains
1–50 nodes (default 6), one neighborhood and explicit truncation. It never reads
cited file contents or follows symlinks/junctions. Sources must exist inside the
package. Large/incompatible artifacts return exit 2 with rg/local knowledge as
fallback. Coverage and freshness remain unverified; check current code before
applying a relationship.

Graphify remains an optional external extractor: the reader adds no dependency,
hook, service or global installation. Use a fresh destination for code-only
extraction: rebuilding an existing graph can preserve its semantic layer. Do
not install mandatory hooks that replace this workflow. The [pilot report](../roadmap/2026-10-06-workflow-integration/testing/structural-pilot.md)
records the executed scope and limitations.

Journal preserves session continuity, approved stores governed knowledge and
knowledge-services publishes approved content. This query neither generates
project-specialization pieces nor creates another consumer piece registry.
