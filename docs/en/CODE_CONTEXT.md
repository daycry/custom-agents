# How to query AST context with declared sources

**English** · [Español](../CODE_CONTEXT.md)

`agent-kits/shared/code-context.py` reads an existing local graph. It returns AST
nodes and edges with their file and location, separately from approved memory.
Markdown retrieval keeps working without Graphify, Docker or a service.

`agent-kits/shared/code-context-build.py` is an optional manual producer.
Queries never import it or start extraction. The panel and hooks retain their
local readers; opening them neither builds graphs nor queries external backends.

## What each query selects

The CLI requires one of these forms; the API retains positional `symbol`.

| Selector | Match | Collision result |
|---|---|---|
| `--symbol` | Casefolded substring of the displayed label, following the legacy contract. | May return several nodes; does not promise exact identity. |
| `--node-id` | Exact, case-sensitive ID. | A duplicate ID excludes every occurrence and its edges. |
| `--source-file` with `--label` | Exact original file and label, before redaction or shortening. | Several eligible IDs produce `ambiguous`, without nodes or edges, even with `--limit 1`. |

IDs accept ASCII letters, digits, `_`, `.`, `:`, `-`, up to 128 characters.
The pair uses the artifact's relative POSIX file path. It does not normalize
aliases to guess identity. Output labels retain redaction and a 240-character cap.

`--limit` accepts 1–50 and defaults to 6. Reaching a limit preserves `matches`,
`truncated: true`, `completeness: partial` and `reason: result_budget`.
`no-match-in-artifact` means absence in the artifact; it does not prove absence in code.

## How to build a graph and its receipt

Find the kit across the six installation roots, as described in
[CONVENTIONS](CONVENTIONS.md#5-paths-inside-the-code).
The library root below is a path the operator already knows and trusts.
The producer does not install, download or discover Graphify from project configuration.

```bash
SHAREDKIT="$(find "$PWD/.claude" "$PWD/.codex" "$PWD/.opencode" "$HOME/.claude" "$HOME/.codex" "$HOME/.config/opencode" -type d -path '*agent-kits/shared' 2>/dev/null | head -1)"
python3 "$SHAREDKIT/code-context-build.py" \
  --project . --graph graphify-out/graph.json \
  --input agent-kits/shared/code-context.py \
  --input agent-kits/shared/local-read.py \
  --graphify-root <trusted-library-root>
```

Repeat `--input` for each declared file that affects extraction or resolution.
The example declares two plugin files; it does not cover the whole project.
`--graph` and inputs use canonical paths relative to the project. The producer
rejects outputs that are inputs or physical aliases of inputs.

`--graphify-root` must point to a library outside the project with a compatible API.
That root executes Python code the operator explicitly trusts. Observed socket
and process controls do not sandbox arbitrary libraries or native extensions.

The producer captures every declared byte before and after extraction, and before
publication. It extracts AST without parallelism or automatic Git, using its own staging.
An observed input change rejects publication with `inputs_changed`.

A missing or incompatible library produces `unavailable`. The native API may
report failed sources because of a missing grammar, parser or empty content.
`ast_inputs_unavailable` alone does not identify the cause. A type without an extractor
returns `unsupported_input`. None of these results installs anything or queries a model.

Both the artifact and receipt require new destinations. If either already exists,
the producer returns `output_exists` before importing the extractor or extracting.
It creates the artifact first and the receipt last with exclusive `os.link` calls.
If linking fails or a destination appears concurrently, it never falls back to overwriting.

The pair is not atomic. Receipt publication failure returns `publish_failed` and may
leave the final artifact without a receipt. Failure cleanup never deletes or replaces
final destinations; it removes only private staging. The next build needs a new destination.
The producer also refuses to fabricate a current-file receipt for an unrelated historical graph.

## What the receipt contains

The automatic sidecar is `<graph>.sources.json`. Its schema allows only these fields:

| Field | Exact shape |
|---|---|
| `schema_version` | Integer 1; excludes bool. |
| `artifact_sha256` | Lowercase hex64 SHA-256 of the graph's original bytes. |
| `scope` | `declared-inputs`. |
| `inputs` | List of objects containing only `path`, `bytes`, `sha256`. |
| `path` | Unique canonical relative POSIX file path. |
| `bytes` | Nonnegative integer; excludes bool. |
| `sha256` | Lowercase hex64 SHA-256 of every original input byte. |

BOM and CRLF count toward hashes. Queries do not cache digests across calls or
normalize text. The reader rejects repeated JSON keys, extra fields, duplicate
paths and case collisions on every platform. Portable identity also rejects
artifact and receipt aliases; the whole schema is validated before any declared
input is read.

Every `source_file` in AST/code nodes and AST/EXTRACTED edges must be declared.
So must a non-null `definition_file`. This check precedes exclusion for duplicate
IDs or missing sources; exclusion cannot hide a receipt omission.

The reader rejects remote paths, absolute input paths, traversal, ADS, devices
and Windows filename aliases. It rejects links/junctions in files or ancestors,
nonregular files and physical aliases among inputs, graph and receipt.
Stable reading uses `local-read.py`. Its checks do not guarantee an atomic
snapshot against concurrent changes or ABA.

## How to read the result and its freshness

```bash
python3 "$SHAREDKIT/code-context.py" \
  --project . --graph graphify-out/graph.json \
  --source-file agent-kits/shared/code-context.py --label 'query_graph()'
```

You can replace the pair with `--node-id <exact-id>` or `--symbol query_graph`.
`--sources-manifest <relative-receipt>` selects an explicit receipt. If it is missing,
the query returns `verification-unavailable`; it does not fall back to legacy mode.

With a valid receipt, each query reads every declared input, including unselected
inputs. It shares digests only within that call.

| Condition | State and context |
|---|---|
| Automatic sidecar absent | Legacy query with `freshness: unverified`, `verification.state: legacy-unverified` and a warning. |
| Every input matches the receipt bound to the artifact | Selector result, `freshness: verified-declared-inputs`. |
| Declared input absent or bytes differ | `artifact-stale`, `freshness: stale`, empty nodes/edges. |
| Malformed receipt, invalid binding or coverage | `verification-invalid`, empty context. |
| Permissions, budget or unstable reading | `verification-unavailable`, empty context and partial diagnostics. |

A proven mismatch persists even if another input fails later. Ambiguity retains
freshness diagnostics without inventing context. An initial graph read failure keeps
`artifact_sha256: null`; it does not assign a digest to unread bytes.
The CLI returns 2 for unavailable, invalid or stale; it returns 0 for selector results.

`verified-declared-inputs` proves an observed match against the declared set bound
to that artifact. It retains `coverage: unknown`, `knowledge_status: unapproved-context`
and an unauthenticated producer. It does not discover new files, cover the whole
project or verify semantics, extraction, line locations or authority.

## What limits the bundle retains

| Resource | Cap |
|---|---|
| Graph | 8 MiB; 20,000 nodes and 50,000 edges. |
| Receipt | 512 KiB. |
| Declared inputs | 128 files. |
| Each input | 1 MiB. |
| Total inputs per query | 8 MiB. |

The reader and producer reserve the helper's excess-detection byte.
The accepted maximum can therefore be one byte below the cap. An incomplete
budget does not become verification or no-match.

The AST tools ship with the full plugin. The skills-only export does not include them.
For a separate manual installation, keep `agent-kits/shared/code-context.py`,
`agent-kits/shared/code-context-build.py`, `agent-kits/shared/local-read.py`,
`agent-kits/shared/capability-route.py` and `agent-kits/shared/redact.py` together.
The reader does not depend on the producer to query. Partial installation reports
unavailable and retains local memory.
Documentary reads have a separate contract:
[Kwipu adapter](../../skills/knowledge-services/references/kwipu-adapter.md#cómo-habilitar-la-lectura-documental).

Observed partial acceptance covers a Python AST with 8 nodes/7 edges and rereading
4/4 declared inputs, including an owned edit becoming stale and exact restoration becoming verified.
It does not establish other grammars, real corpora or final integration or release QA.
