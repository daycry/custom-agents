---
tasks: user-handbooks
estado: en-progreso
creado: 2026-11-04
verificacion: obligatoria
changelog: Added
---

# Manuales de uso

Ledger canónico. [Alcance autorizado](spec.md).

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 | 2 | 3 | 66.7% |
| **TOTAL** | **2** | **3** | **66.7%** |

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

- **Estado**: en-revision
- **Tipo**: docs
- **Archivos**: `README.md`, `README.es.md`, `docs/README.md`, `docs/en/README.md`, `docs/roadmap/README.md`, `CHANGELOG.md`, `CHANGELOG.es.md`, `docs/roadmap/2026-11-04-user-handbooks/**`, `tests/test_user_handbooks.py`.
- **Verificación**: enlaces, lint, evals, checks documentales; commit y push a la PR existente.
- **Changelog**: Indexed and verified user handbooks alongside the token efficiency implementation.

**Criterios de aceptación**
- [ ] Índices ES/EN actualizados, comprobaciones pertinentes verificadas, cambios propios publicados sin configuración privada.

TDD n/a: documentación y maquetación; sin cambios de ejecución del plugin.

RED: DOC-B1 y DOC-B2 reproducidos con las afirmaciones originales → 2 failed; correcciones → 2 passed. Integridad de edición con fuente modificada como control → 1 failed, 3 passed; fuentes finales → 4 passed. Con el índice del roadmap: 70 passed.
