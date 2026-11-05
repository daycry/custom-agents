---
tasks: npm-payload
estado: en-progreso
creado: 2026-11-05
verificacion: obligatoria
changelog: Fixed
---

# Completar el paquete npm

Ledger canónico. [Alcance](spec.md).

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 | 1 | 2 | 50.0% |
| **TOTAL** | **1** | **2** | **50.0%** |

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

- **Estado**: en-revision
- **Tipo**: docs
- **Archivos**: `docs/INSTALL.md`, `docs/en/INSTALL.md`, `docs/roadmap/README.md`, `docs/roadmap/2026-11-05-npm-payload/**`, `CHANGELOG.md`, `CHANGELOG.es.md`.
- **Verificación**: lint, evals, interop, tests de artefacto/ediciones/índice, revisión y CI de la PR.
- **Changelog**: Bilingual publishing guidance distinguishes GitHub releases from npm publication and verifies the actual tarball before publishing.

**Criterios de aceptación**
- [ ] Guía ES/EN actualizada, pruebas y revisión verificadas, PR integrada con CI verde; publicación npm no se simula ante E401.
