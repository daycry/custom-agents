---
id: ADR-001
titulo: Alcance de publicación en Confluence = selección curada (opt-out)
estado: aceptada
fecha: 2026-08-20
iniciativa: confluence-policy
---

# ADR-001: Alcance de publicación en Confluence = selección curada (opt-out)

## Contexto

El circuito `docs/ ↔ Confluence` (skills `confluence-publish`/`confluence-pull`) existía en
mecánica pero sin política explícita de qué documentación es apta para un espacio compartido. Con
el `include: ["**/*.md"]` por defecto y solo dos exclusiones (`node_modules`, `docs/security-scan/**`),
un espejo real subiría `docs/en/` (árbol EN duplicado), `docs/examples/`, `docs/agents/`
(documentación interna del plugin), `atlassian-connector-notes.md` y las iniciativas completas del
roadmap (`improvement-plan.md`/`tasks.md`/`test-plan.md` incluidos), sin que nadie lo hubiera
decidido.

## Decisión

El alcance por defecto es una **lista de `exclude` sobre `include: ["**/*.md"]`** (opt-out, no
allow-list). Por iniciativa suben `spec.md`, `evaluation.md` y `retro.md`; **no** suben
`improvement-plan.md`, `tasks.md` ni `test-plan.md`. Los ficheros de cartera (`dashboard.md`,
`BACKLOG.md`, `brief.md`, `DRIFT.md`, `CALIBRATION.md`) sí suben. Se añaden a `exclude`:
`docs/en/**`, `docs/examples/**`, `docs/agents/**`, `docs/**/atlassian-connector-notes.md`,
`docs/roadmap/**/improvement-plan.md`, `docs/roadmap/**/tasks.md`, `docs/roadmap/**/test-plan.md`.

## Alternativas descartadas

- **Allow-list (`include` explícito por carpeta)** — más frágil: cada carpeta nueva de `docs/`
  quedaría fuera del espejo hasta que alguien recordara añadirla.
- **Presets de audiencia (interno/externo/completo)** — ver ADR-002: descartado por separado.
- **Publicar `improvement-plan.md`/`tasks.md`** — es tablero de **ejecución**, no de decisión ni
  resultado; su sitio es el repo y Jira, no Confluence.

## Consecuencias

Confluence queda como la vista de **decisión y resultado** (spec, evaluación, retro, cartera), no
como el tablero de ejecución. Un proyecto que quiera ver el ledger en Confluence debe añadir
`tasks.md` al `include` a mano (no es opción de primera clase, ver ADR-002). Ver la nota de
interacción D1↔D3 en la spec fuente: el disparo por fase de `implementer` (ADR-003) refresca el
resto del alcance, pero `tasks.md` en sí no sube con la política por defecto.

## Estado

`aceptada (validada: revisión de dos lentes, 2026-08-20, intento 3)` — implementada y mergeada en
`feature/confluence-policy` → `master`. Fuente:
[`docs/roadmap/2026-08-20-confluence-policy/spec.md`](../../roadmap/2026-08-20-confluence-policy/spec.md#decisiones-de-diseño)
(fila "Qué entra del roadmap", D1, y "Decisiones confirmadas" punto 1).
