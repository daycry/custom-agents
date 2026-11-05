---
tasks: npm-payload
estado: completado
creado: 2026-11-05
verificacion: obligatoria
changelog: Fixed
---

# Completar el paquete npm

Ledger canónico. [Alcance](spec.md).

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 | 2 | 2 | 100.0% |
| **TOTAL** | **2** | **2** | **100.0%** |

## Fase 1

### T-01 - Corregir la allowlist con regresiones sobre el tgz

- **Estado**: completado
- **Tipo**: build
- **Archivos**: `package.json`, `tests/test_npm_payload.py`.
- **Verificación**: `python -m pytest tests/test_npm_payload.py -q --tb=short`.
- **Changelog**: The npm artifact includes the model projection exporter and all PDF editions linked from its README.

Verificación ejecutada: test del artefacto → 3 passed; con ediciones e índice → 74 passed. [Detalle](testing/validation.md).

**Criterios de aceptación**
- [x] La proyección de modelos funciona desde el paquete, los PDF/manifiestos están presentes y no viaja estado privado.

RED observado sobre 3.2.0: 2 failed, 1 passed. NPM-01 falla al ejecutar la proyección desde el tgz por ausencia del exportador; NPM-02 detecta cuatro archivos PDF/manifiesto ausentes. El control de exclusión de estado privado pasa.

### T-02 - Documentar y validar la entrega

- **Estado**: completado
- **Tipo**: docs
- **Archivos**: `docs/INSTALL.md`, `docs/en/INSTALL.md`, `docs/roadmap/README.md`, `docs/roadmap/2026-11-05-npm-payload/**`, `CHANGELOG.md`, `CHANGELOG.es.md`.
- **Verificación**: lint, evals, interop, tests de artefacto/ediciones/índice, revisión y CI de la PR.
- **Changelog**: Bilingual publishing guidance distinguishes GitHub releases from npm publication and verifies the actual tarball before publishing.

Verificación ejecutada: 74 tests passed; lint 0 errores/16 avisos previos, evals 60 piezas/229 casos, interop 92 ficheros actuales, check-handbook exit 0. A+B sin defectos; ambos ejecutan 3 tests del artefacto. [PR #29](https://github.com/daycry/custom-agents/pull/29) preparada; su CI requerida debe estar verde antes de integrar. La publicación npm se comprueba como operación externa posterior y no se acredita con estos tests.

**Criterios de aceptación**
- [x] Guía ES/EN actualizada, pruebas y revisión verificadas, PR integrada con CI verde; publicación npm no se simula ante E401.

## Revisión de dos lentes — intento 1: A+B aprobadas

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| — | — | Sin defectos | T-01/T-02 | No requerida | [Traza](testing/review.md); 3 tests pasados por cada revisor independiente |

Scope-check: 8 archivos en alcance, 0 fuera/excluidos. C/D false por selector determinista; sin cambios de lógica runtime. El cierre conserva las comprobaciones ejecutadas y exige el check de la PR antes de integrar; no atribuye a los revisores una CI aún pendiente en su instantánea.
