---
spec: knowledge-services
estado: aprobada
creado: 2026-09-15
actualizado: 2026-09-15
evaluacion: evaluation.md
design: design.md
plan: improvement-plan.md
generacion: {fuente: estimado, tokens_reales: {entrada: 0, salida: 0, cache_creacion: 0, cache_lectura: 0}, eur: null, horas_ia: 0.0, duracion: 0m, ratio_usado: 0}
---

# Servicios de conocimiento locales para Kwipu

> [Evaluacion](evaluation.md) · [Diseno](design.md) · [Plan](improvement-plan.md)

## Objetivo

Mantener `docs/knowledge/` como fuente de verdad versionada y anadir un Knowledge Gate local que exporte solo conocimiento aprobado a Kwipu. Kwipu sera un recuperador documental opcional; indices y exports son reconstruibles y nunca sustituyen Markdown/Git.

## Alcance

- Candidatos y aprobados bajo `docs/knowledge/`, con categorias `DECISION`, `PATTERN`, `CONSTRAINT`, `HEURISTIC`, `FAILURE`, `CORRECTION`, `SKILL`, `TOOL` y `CASE`.
- Frontmatter validado: ID estable, version, estado, evidencia, fuentes, relaciones y tags `clave:valor` normalizados.
- Agente `knowledge-curator`, unico dueno de candidatos/aprobados; `documenter` detecta y propone, nunca aprueba ni exporta.
- Exportador determinista a `.claude/knowledge-services/kwipu-export/`, con manifiesto y hashes.
- Opt-in Kwipu en `/setup`, salud/desfase en `/doctor`, y Fase 4-bis despues de QA verde y `documenter`.

## Fuera de alcance

- Graphiti, MCP registration, escritura de memoria conversacional, red desde hooks, migracion masiva y entrenamiento/Ollama.

## Criterios de aceptacion

- [ ] CA-01 - El esquema rechaza categorias, estados, IDs, tags y referencias invalidas.
- [ ] CA-02 - Candidatos, rechazados, journal, logs y derivados nunca se exportan a Kwipu.
- [ ] CA-03 - Solo el Curator puede aprobar, rechazar, pedir cambios o sustituir conocimiento.
- [ ] CA-04 - El export es idempotente, atomico y reconstruible desde `approved/`.
- [ ] CA-05 - Setup y doctor gestionan Kwipu como capacidad opcional y degradable.
- [ ] CA-06 - La curacion sucede solo despues de QA/documentacion y no altera cierres sin candidatos.
- [ ] CA-07 - Interop, contratos y documentacion ES/EN permanecen sincronizados.
- [ ] CA-08 - Esta entrega no implementa Graphiti.

## Decisiones confirmadas (usuario, 2026-09-15)

1. El proyecto consumidor ya es el limite de aislamiento: no hay `projects/<project_id>/`.
2. Kwipu consulta conocimiento aprobado; Graphiti queda para una iniciativa posterior.
3. El Curator es un agente especializado posterior a QA y `documenter`.