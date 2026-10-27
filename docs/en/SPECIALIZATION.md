# Project specialization

**English** · [Español](../SPECIALIZATION.md)

The plugin knows **how** to work but not **where** it is working. This document explains how a
project teaches the plugin its domain: through **project personas**, which are injected into each
subagent's brief, and through its **own pieces** (skills, agents, commands, tools, MCP), which the
plugin discovers in each runtime's native folders.

> **Status (2026-10-27).** The `docs/roadmap/2026-09-09-project-specialization/` initiative closed
> with **F1 delivered**: the persona cascade and this document. **F2 was cancelled**: the
> *specialize* command, registry writing, project scanning, the collision gate and the project mode
> of `export-interop.py` do not exist and are not planned. It was superseded by
> [project extensions](PROJECT-EXTENSIONS.md): `project-pieces.py` and `/work-context` already
> discover, select and pass to the brief the pieces a project writes by hand. Reason: the
> 2026-10-27 amendment in the initiative's spec.

## Project personas (the cascade)

A ledger task may carry `- **Tipo**: <type>` (optional field; without it, a generic subagent).
`agent-kits/shared/task-brief.py` resolves the persona for that type in three steps, from the most
specific to the most general:

1. **The project's `.claude/personas/<type>.md`.** It always wins: it is THIS project's domain.
2. **The plugin catalog** (`agent-kits/shared/personas/`, or whatever `--personas-dir` sets).
3. **None.** The brief comes out without a persona section, with a warning on stderr and exit 0.
   It never blocks.

There is no allow-list of types: any `<type>` with a file in either of the first two steps works
without touching code. A hand-written persona already pays off. A domain profile of about ten lines
in `.claude/personas/<type>.md` is enough.

Personas are a **brief** mechanism. Codex and OpenCode do not load `personas/` natively: it reaches
them inside the brief their subagents receive, not as an agent of their own
(see [`INTEROP.md`](INTEROP.md)).

## The project's own pieces

The project's skills, agents, commands, tool sources and MCP are written by hand, in each runtime's
native folder. The plugin recognises them without converting or executing them. How to create them,
where they go and how the cycle uses them: [`PROJECT-EXTENSIONS.md`](PROJECT-EXTENSIONS.md).

## The ownership registry (`.claude/pieces.json`, read-only)

A project **may** provide a registry that declares which pieces are its own and the hash they were
left with. The plugin **reads** and **validates** it but **does not write** it. Validation lives in
`_registry_entries()` in `agent-kits/shared/project-pieces.py`. The schema is option O1 (`ADR-014`):
the **piece is the root** and its destinations are nested inside it.

```json
{
  "version": 1,
  "hash_version": "sha256-lf-1",
  "piezas": [
    {
      "nombre": "hooks",
      "forma": "persona",
      "area": "hooks",
      "origen": "adoptada",
      "creada": "2026-09-09",
      "evidencia": ["hooks/session-end.sh:12"],
      "confirmaciones": { "tools": [], "arbol_plugin": null, "tope": null },
      "destinos": [
        { "runtime": "claude-code", "ruta": ".claude/personas/hooks.md", "canonica": true, "hash": "sha256:ab12…" }
      ]
    }
  ]
}
```

`runtime` is a **field** of each destination, not a schema key. The registry does not store each
piece's state: it is derived on every read, by comparing the on-disk hash (with line endings
normalised to LF) against the recorded one.

| State | When |
|---|---|
| managed | The on-disk hash matches the recorded one |
| modified | The on-disk hash differs from the recorded one |
| unmanaged | The piece has no entry. A valid state, not an error |

A project without a registry works the same: all its pieces show as unmanaged. A corrupt registry
produces a warning and never blocks. The panel (`/plugin-catalog`) shows each piece's ownership.

## Memory: the plugin reads, the curator decides

Specialization **reads** `docs/knowledge/` (ADRs, gotchas, lessons) as hints and never writes to it.
New knowledge is proposed through the shared service (`agent-kits/shared/knowledge-curation.py`),
and only `knowledge-curator` approves it (`docs/agents/ROLES.md`).

## What is out of scope

- **Generating or adopting pieces** (the former *specialize*): cancelled. If the idea of the plugin
  **proposing** pieces from repository evidence comes back, it will be a new initiative built on
  `project-pieces.py`, with its scripts in `agent-kits/shared/` so they ship with the plugin.
- **Semantic drift and retiring dead pieces** (the former F3): no plan.
