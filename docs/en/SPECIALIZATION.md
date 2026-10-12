# Project specialization — the third loop

**English** · [Español](../SPECIALIZATION.md)

This document is the **single entry point** to the plugin's third loop, sibling to
[`INTEROP.md`](INTEROP.md) and [`observability.md`](observability.md): the plugin knows **how** to
work but not **where** it is working. The third loop closes that gap with the same grammar the cycle
(`tasks.md`) and memory (`docs/knowledge/README.md`) already have: a **canonical registry**, an
**entry gate** and a **closing gate**.

> **Scope of this iteration: F1 + F2.** See "The limit of this iteration" at the end. The full spec
> lives in `docs/roadmap/2026-09-09-project-specialization/spec.md` (`aprobada`).
>
> **What's shipped today in this tree is F1** (`tasks.md` T-01…T-03): the three-rung cascade in
> `task-brief.py` and this very entry document. **The canonical registry, `/specialize`,
> `pieces-registry.py`, `role-collision.py`, `project-scan.py`, `.claude/pieces.json` and the
> `/doctor` section** described below under "The canonical registry", "The decision ladder" and "The
> two gates" are the **F2 contract** (`design.md` `ADR-014`, `tasks.md` T-04…T-18): designed and
> planned, **not in the tree yet**. Same pattern as `docs/agents/ROLES.md` for `/specialize`.

The [user-extension reader](PROJECT-EXTENSIONS.md) recognizes existing pieces
and validates a project-supplied O1 registry in read-only mode. That derived
inventory does not deliver F2 generation, adoption, rebuilding or write gates;
their state remains in the separate specialization ledger.

## What the loop is

```
Memory ──reads──▶ Specialization ──feeds──▶ Cycle
Cycle ──/retro: service propose──▶ pending + SHA ──judgment──▶ Curator
Curator ──service apply bound to SHA──▶ Memory
```

`docs/knowledge/` (ADR, gotchas, lessons, journal) feeds `/specialize`, which produces **project
pieces** — personas, tools, skills or agents that live in the consumer's `.claude/` and know THEIR
domain. Those pieces enter the cycle (`task-brief.py` injects the persona into the brief of tasks
that carry `- **Tipo**: <type>` — the field is optional; without it, a generic subagent), and
`/retro` proposes evidence through `agent-kits/shared/knowledge-curation.py`; repetition does not
approve knowledge. Curator judges and the service persists with original SHA, reason and valid
metadata. Two distinct terms, so they don't get mixed up:

- **Plugin piece** — an agent, skill, command, kit or hook that lives in this repo and ships with the
  plugin. Domain-agnostic by design.
- **Project piece** — a persona, tool, skill or agent that lives in the consumer's `.claude/`, knows
  THEIR domain, and exists only there. This is what this loop lets a project have.

## The canonical registry

`.claude/pieces.json` holds one row per **generated** or **adopted** piece. Anything written by hand
and never adopted is still a first-class citizen: it shows up as `no gestionada`, which is a valid
state, not an error.

The schema is design option **O1** (`ADR-014`): the **piece is the root**, and its destinations — the
canonical Claude Code one plus each runtime's variant — go **nested inside**, never the other way
around.

```json
{
  "version": 1,
  "hash_version": "sha256-lf-1",
  "piezas": [
    {
      "nombre": "hooks",
      "forma": "persona",
      "area": "hooks",
      "origen": "generada",
      "creada": "2026-09-09",
      "evidencia": ["hooks/session-end.sh:12", "GOT-005"],
      "confirmaciones": { "tools": [], "arbol_plugin": null, "tope": null },
      "destinos": [
        { "runtime": "claude-code", "ruta": ".claude/personas/hooks.md", "canonica": true,  "hash": "sha256:ab12…" },
        { "runtime": "codex",       "ruta": ".codex/agents/hooks.toml",  "canonica": false, "hash": "sha256:cd34…" }
      ]
    }
  ]
}
```

`runtime` is a **data field** on each destination, never a schema key: a fourth provider is one more
row, not a migration. A row's state is **never persisted**: it is derived by comparing the on-disk
hash with the recorded one on every read.

The three states of a row (by hash, not by folder — `GOT-003`):

| State | When |
|---|---|
| `gestionada` (managed) | The on-disk hash matches the hash recorded on its row |
| `modificada` (modified) | The on-disk hash differs from the recorded one (hand-edited after generation, or adopted without a generation baseline). Never overwritten: the diff is shown and explicit confirmation is required |
| `no gestionada` (unmanaged) | No row exists. A valid state, not an error; can be **adopted** with `--adopt` |

## The decision ladder

From the cheapest rung to the most expensive. `/specialize` always starts at "nothing": duplicating a
piece that already exists is rejected, never generated.

```
nothing → persona → tool → skill → agent
```

- **nothing** — the candidate duplicates an installed or already-generated piece: rejected, naming
  the one that already covers it (`role-collision.py`).
- **persona** — a ~10-line domain profile; the default rung.
- **tool / skill / agent** — climbed only when the evidence justifies it; **agent** is the last
  resort, requiring an **explicit user override**.

## The two gates

`/specialize` never writes without human confirmation, and keeps **preview** separate from
**confirmation**:

1. **`--dry-run`/`--plan`** — previews the **full batch** of candidates (form, evidence, collision
   gate result) and **creates no file or row**.
2. **N confirmations for N candidates** — without `--dry-run`, an explicit confirmation is requested
   for each candidate, in the previewed order. Confirming one does not approve the rest; declining
   one only skips that one; if none is confirmed, nothing is written and the exit is clean (exit 0).

The **cap on generated pieces is 5, accumulated across the project's whole registry**, not per
invocation (reason: the measured budget of `skill-index.py`, `LIMITE_LINEAS = 45` /
`LIMITE_CHARS = 3500`, which is what fixes how much fits in the startup index). Exceeding it triggers
a warning and an extra confirmation, never a silent failure.

## The direction invariant

**`/specialize` reads `docs/knowledge/` and NEVER writes to it.** It consumes ADR, gotchas, lessons
and the journal's candidates as evidence; it produces pieces under the F2 contract. New knowledge
is proposed through the shared service; `knowledge-curator` decides and requests persistence via
`apply_decision`, not `/retro` or `adversarial-review`. Design/review/QA/Gold/repetition are evidence,
not approval. Retro after the Gate hands off or leaves route/ID and pending state visible.
Legacy preserves bytes/states/authority without automatic migration, reapproval or deletion;
conflicts/high impact require traced human resolution, not date/score. The third loop neither
writes nor approves memory (`docs/agents/ROLES.md`).

The curation service does not deliver F2 or prove authenticated actors or a universal sandbox.
Intent, publication and receipt are recoverable boundaries, not an atomic multi-file transaction;
native acceptance remains pending. [Curation contract](../roadmap/2026-10-07-catalog-capabilities/comparisons/memory-curation-contract.md).

## The limit of this iteration

The planned scope of this iteration covers **F1 (Substrate) and F2 (Birth)**: the persona cascade, the `/specialize`
command, the registry with its three states, the adoption mode, the non-functional requirements
(idempotency, concurrency, privacy) and `/doctor`'s own section that audits the registry — the ability
to generate is not shipped without the ability to check.

**F3 (semantic drift and retiring dead pieces) is deferred, not dropped.** The F2 contract requires
its own mechanical audit (`/doctor`); F2 remains unimplemented in this tree. F3 will resume as
its own initiative once success-criterion data exists. Full detail, reasoning and the named
checkpoint: `docs/roadmap/2026-09-09-project-specialization/spec.md`, section **"Alcance" →
"Fuera (esta iteración — diferido, no descartado)"**.
