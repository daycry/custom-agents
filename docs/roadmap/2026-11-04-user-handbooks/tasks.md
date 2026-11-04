---
tasks: user-handbooks
estado: completado
creado: 2026-11-04
verificacion: obligatoria
changelog: Added
---

# Manuales de uso

Ledger canónico. [Alcance autorizado](spec.md).

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 | 3 | 3 | 100.0% |
| **TOTAL** | **3** | **3** | **100.0%** |

## Fase 1

### T-01 - Redacción y fuentes verificadas

- **Estado**: completado
- **Tipo**: docs
- **Archivos**: `docs/guides/subscription-efficiency.md`, `docs/guides/quality-playbook.md`.
- **Verificación**: contraste con fuentes oficiales y comandos canónicos del plugin.
- **Changelog**: Detailed Spanish handbooks for subscription efficiency and evidence-based workflows.

Verificación ejecutada: fuentes oficiales y contratos canónicos contrastados en [sources.md](testing/sources.md); 24 enlaces locales válidos; regresiones DOC-B1/B2 con RED observado y GREEN (4 tests finales incluyendo integridad de ediciones).

**Criterios de aceptación**
- [x] Dos manuales detallados, comprensibles, con ejemplos, prompts y Mermaid, sin promesas de perfección o cuota fija.

### T-02 - PDF e integridad editorial

- **Estado**: completado
- **Tipo**: docs
- **Archivos**: `output/pdf/guia-uso-eficiente-claude-codex.pdf`, `output/pdf/guia-resultados-calidad-custom-agents.pdf`, `output/pdf/guia-*.manifest.json`.
- **Verificación**: extracción de texto, enlaces, hashes de fuentes, render de páginas y revisión visual.
- **Changelog**: Modern standalone PDF editions with rendered workflows and navigable contents.

Verificación ejecutada: PDF finales de 19 y 25 páginas; 3 y 5 diagramas, 18 y 19 marcadores, 66 y 53 enlaces. Extracción: 317 y 494 bloques de fuente presentes, sin desbordes detectados. Todas las páginas renderizadas, contact sheets y páginas clave inspeccionadas. [Informe](testing/pdf-validation.json).

**Criterios de aceptación**
- [x] Dos PDF íntegros, legibles, sin desbordes ni diagramas ausentes; evidencia de revisión visual.

### T-03 - Distribución y cierre

- **Estado**: completado
- **Tipo**: docs
- **Archivos**: `README.md`, `README.es.md`, `docs/README.md`, `docs/en/README.md`, `docs/roadmap/README.md`, `CHANGELOG.md`, `CHANGELOG.es.md`, `docs/roadmap/2026-11-04-user-handbooks/**`, `tests/test_user_handbooks.py`.
- **Verificación**: enlaces, lint, evals, checks documentales; commit y push a la PR existente.
- **Changelog**: Indexed and verified user handbooks alongside the token efficiency implementation.

Verificación ejecutada: 70 tests de manuales/índice passed; lint 0 errores/16 avisos documentados; evals 60 piezas/229 casos; interop 92 ficheros al día; manual operativo previo verificado. Commit `5730e0a` publicado en [PR #28](https://github.com/daycry/custom-agents/pull/28). Revisiones A+B aprobadas, sin gaps. Solo archivos propios en el cierre; preferencias privadas preservadas. Los checks requeridos de la PR deben estar verdes antes de integrar. [Detalle](testing/validation.md).

**Criterios de aceptación**
- [x] Índices ES/EN actualizados, comprobaciones pertinentes verificadas, cambios propios publicados sin configuración privada.

TDD n/a: documentación y maquetación; sin cambios de ejecución del plugin.

RED: DOC-B1 y DOC-B2 reproducidos con las afirmaciones originales → 2 failed; correcciones → 2 passed. Integridad de edición con fuente modificada como control → 1 failed, 3 passed; fuentes finales → 4 passed. Con el índice del roadmap: 70 passed.

## Revisión de dos lentes — intento 1: preparatorio incompleto

B detectó dos gaps; A todavía no ejecutada, sin pase de puerta. [Traza](testing/review.md).

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B1 | Important | Comando de esfuerzo atribuido a Codex CLI | T-01 | `/model` y `--reasoning=high` | Test dedicado B1, RED observado y GREEN |
| B2 | Important | Alcance excesivo atribuido a api-contract | T-01 | Validación/comparación de specs | Test dedicado B2, RED observado y GREEN |

## Revisión de dos lentes — intento 2: A+B aprobadas

A revisa conformidad completa; B conserva veredictos aprobados y reevalúa correcciones/tests. C/D no aplican por selector determinista. Ambos ejecutan 70 tests y whitespace check, sin fallos. Sin gaps pendientes, rebatidos o deuda. El cierre de T-03 conserva la evidencia de publicación y la comprobación requerida de la PR; no atribuye a los revisores la CI que todavía no había terminado en su instantánea.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| B1 | Important | Corregido | T-01 | Receta CLI documentada | `tests/test_user_handbooks.py`, fuente oficial, texto PDF |
| B2 | Important | Corregido | T-01 | Contrato real de skill | `tests/test_user_handbooks.py`, contrato canónico, texto PDF |
| — | — | Sin nuevos hallazgos | T-01/T-02/T-03 | — | [Revisión](testing/review.md), [validación](testing/validation.md) |
