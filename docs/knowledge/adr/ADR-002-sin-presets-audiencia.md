---
id: ADR-002
titulo: Sin presets de audiencia en confluence-publish
estado: aceptada
fecha: 2026-08-20
iniciativa: confluence-policy
---

# ADR-002: Sin presets de audiencia en confluence-publish

## Contexto

Al definir la política de publicación (ADR-001) surgió la pregunta de si ofrecer distintos
presets de alcance según la audiencia del espacio de Confluence (p. ej. "interno", "cliente",
"completo"), además del default curado.

## Decisión

**Se descartan los presets de audiencia.** Hay un único default sensato (el de ADR-001); la copia
1:1 del repo sigue siendo posible editando `include`/`exclude` a mano, pero no es una opción de
primera clase (no hay un flag `preset: cliente` ni equivalente).

## Alternativas descartadas

- **Presets por audiencia (interno / cliente / completo)** — descartado: sin una audiencia
  confirmada para el espacio, un preset sería especulación cara de mantener (más superficie de
  config y de documentación para un caso no validado).

## Consecuencias

Menos superficie de configuración y de documentación que mantener. Como supuesto declarado: la
audiencia del espacio es mixta (PM + equipo), por lo que la forma general sigue siendo opt-out
(`exclude`) en vez de presets cerrados. Si en el futuro aparece una audiencia real que lo
justifique, esta decisión se reabre (pasaría a `obsoleta` con un ADR sucesor).

## Estado

`aceptada (validada: revisión de dos lentes, 2026-08-20, intento 3)` — implementada y mergeada en
`feature/confluence-policy` → `master`. Fuente:
[`docs/roadmap/2026-08-20-confluence-policy/spec.md`](../../roadmap/2026-08-20-confluence-policy/spec.md#decisiones-de-diseño)
(fila "Presets por audiencia", D2, y "Decisiones confirmadas" punto 2).
