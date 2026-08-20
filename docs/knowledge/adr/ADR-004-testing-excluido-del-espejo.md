---
id: ADR-004
titulo: "`**/testing/**` de qa queda excluido del espejo de Confluence"
estado: aceptada
fecha: 2026-08-20
iniciativa: confluence-policy
---

# ADR-004: `**/testing/**` de qa queda excluido del espejo de Confluence

## Contexto

El filtro `**/*.md` dejaba fuera `report.pdf`, `screenshots/` y `raw/` de la salida de `qa`, pero
sí publicaba `report.md`, que **embebe capturas**. Como el conector Rovo MCP no expone subida de
adjuntos (solo `createConfluencePage`/`updateConfluencePage`), la página de Confluence salía con
**imágenes rotas**. Había que decidir si transformar `report.md` para ese caso o excluir la
carpeta entera.

## Decisión

**`**/testing/**` no se publica.** Se descarta transformar el `report.md` publicado; el informe
completo (md + pdf + capturas) queda **solo-local**, disponible en el repo.

## Alternativas descartadas

- **Transformar `report.md` al publicarlo** (p. ej. quitar las referencias a capturas o
  linkearlas de otro modo) — descartado: añade una transformación de contenido al circuito
  (rompe la propiedad "publicado ≡ staged ≡ canónico") para un caso que la exclusión resuelve de
  raíz.

## Consecuencias

Elimina de raíz las imágenes rotas y el riesgo de divergencia local↔remoto que afectaba también a
`confluence-pull`. `agents/qa.md` declara el informe como solo-local; su paso opt-in deja de
apuntar a `testing/`. Quien espere ver el informe de QA en Confluence no lo encontrará: la
ausencia es una decisión documentada, no un fallo aparente (`docs/FLOWS.md` y la doc de la skill
lo dicen explícitamente).

## Estado

`aceptada (validada: revisión de dos lentes, 2026-08-20, intento 3)` — implementada y mergeada en
`feature/confluence-policy` → `master`. Fuente:
[`docs/roadmap/2026-08-20-confluence-policy/spec.md`](../../roadmap/2026-08-20-confluence-policy/spec.md#decisiones-de-diseño)
(fila "Evidencias de qa", D4, y "Decisiones confirmadas" punto 4).
