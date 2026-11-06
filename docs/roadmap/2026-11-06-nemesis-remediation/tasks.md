---
tasks: nemesis-remediation
estado: en-progreso
creado: 2026-11-06
verificacion: obligatoria
changelog: Fixed
---
# Remediación de Nemesis
[Spec](spec.md) · [Plan](improvement-plan.md)

> Ledger canónico: este fichero conserva el estado y la evidencia de cada tarea.

## Resumen de progreso
| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 | 0 | 5 | 0.0% |
| **TOTAL** | **0** | **5** | **0.0%** |

## Fase 1
**Estado**: en-progreso

### T-01 — Vistas Atlassian seguras

- **Estado**: en-revision
- **Archivos**: `skills/jira-sync/assets/**`, `skills/roadmap-dashboard/assets/**`, `skills/confluence-publish/assets/**`, `agent-kits/shared/render-artifact.py`, `skills/jira-sync/references/destination-and-types.md`, `skills/confluence-publish/references/wizard.md`, `skills/roadmap-dashboard/**`, `tests/artifact-dom-security.test.mjs`, `tests/test_artifact_renderer.py`
- **Verificación**: tests dirigidos y regresiones del área; evidencia ejecutada en [testing/validation.md](testing/validation.md).

**Criterios de aceptación**
- [ ] F-001: títulos, nombres y errores son texto literal; configuración no rompe HTML/JS; selección conserva identidad y valores.


RED: `tests/artifact-dom-security.test.mjs` falló con RED navegador Edge: tres vistas ejecutan onerror desde metadatos externos; 0 passed y 3 failed · 2026-11-06.

### T-02 — Conversión PDF segura

- **Estado**: en-revision
- **Archivos**: `skills/to-pdf/**`, `tests/to-pdf*.test.mjs`
- **Verificación**: tests dirigidos y regresiones del área; evidencia ejecutada en [testing/validation.md](testing/validation.md).

**Criterios de aceptación**
- [ ] O-003: sandbox predeterminado, JS/red desactivados, excepciones documentadas, título escapado y salida atómica conservada.


RED: `tests/to-pdf-security.test.mjs` falló con RED: sandbox desactivado por defecto y sin política JS/red; CLI real con navegador sustituido por fixture · 2026-11-06.

### T-03 — CI con permisos acotados

- **Estado**: en-revision
- **Archivos**: `ci.yml.MANUAL-COPY`, `release.yml.MANUAL-COPY`, `headless.yml.MANUAL-COPY`, `.github/workflows/**`, `tests/test_ci*.py`, `docs/**/guides/nemesis-remediation.md`
- **Verificación**: tests dirigidos y regresiones del área; evidencia ejecutada en [testing/validation.md](testing/validation.md).

**Criterios de aceptación**
- [ ] O-002: secretos sólo en pasos consumidores; acciones por SHA completo, CLI fijada, permisos mínimos y copias manuales idénticas.


RED: `tests/test_ci_security.py` falló con RED previo: 5 contratos fallan por tags mutables, clave en job y build con token write; config/prosa TDD n/a, contratos verificados · 2026-11-06.

### T-04 — Herramientas opcionales verificadas

- **Estado**: en-revision
- **Archivos**: `agent-kits/nemesis/tools/**`, `agent-kits/nemesis/README.md`, `agents/nemesis.md`, `docs/agents/nemesis.md`, `docs/agents/nemesis-toolkit.md`, `.gitattributes`, `tests/test_nemesis_tools*.py`, `docs/**/guides/nemesis-remediation.md`
- **Verificación**: tests dirigidos y regresiones del área; evidencia ejecutada en [testing/validation.md](testing/validation.md).

**Criterios de aceptación**
- [ ] O-001: catálogo con versiones/revisiones/hashes fijados y procedencia verificable; rechazar integridad inválida, archivos inseguros e instalaciones desconocidas sin sobrescribirlas; no instalar herramientas reales durante tests.

RED: `tests/test_nemesis_tools.py::InstallerPolicy::test_no_mutable_install_sources_or_eval` falló por resolver `/releases/latest` al instalar · 2026-11-06.

GREEN dirigido T-04: 13 pruebas offline. RED adicional del quoting de argumentos observado y corregido.

### T-05 — Regresión, revisión y entrega

- **Estado**: en-progreso
- **Archivos**: `docs/roadmap/2026-11-06-nemesis-remediation/**`, `docs/roadmap/README.md`, `docs/guides/nemesis-remediation.md`, `docs/en/guides/nemesis-remediation.md`, `CHANGELOG.md`, `CHANGELOG.es.md`, `interop/**`, `docs/README.md`, `docs/en/README.md`
- **Verificación**: tests dirigidos y regresiones del área; evidencia ejecutada en [testing/validation.md](testing/validation.md).

**Criterios de aceptación**
- [ ] Verificaciones dirigidas, revisión A/B/C/D según selector, CI y documentación bilingüe; commits/push y PR actualizada, sin publicación npm/release.


Ampliación técnica T-05: los índices ES/EN enlazan la nueva guía para que sea descubrible; no cambia el alcance funcional.

## Revisión de dos lentes — intento 1: Fase 1 (T-01–T-05) — gaps

Lentes A+B+C sobre facad5f..bb5ca20; D no aplica según selector. Las tres lentes entregaron informes estructurados y ejecutaron pruebas dirigidas verdes. No equivalen a una auditoría SAST/DAST completa.

| ID | Lente | Grado | Tarea | Evidencia | Resolución |
|---|---|---|---|---|---|
| A-01 | A | Important | T-04 | catalog.md:37 seguía indicando editar CATALOG Bash; docs del agente describían git clone | Corregir catálogo y documentación operativa existente. |
| B1 | B | Important | T-04 | install-tools.py:273; SQLmap importa lib.utils antes de restaurar rutas, -I excluía el directorio | Lanzador aislado con búsqueda explícita en árbol verificado; fixture de módulos hermanos. |
| B2 | B | Important | T-04 | install-tools.py:282; requisitos sin atributo eol; LF/CRLF cambian digest | Fijar LF en .gitattributes y contrato dedicado. |
| C | C | — | todas | Sin hallazgos de seguridad introducidos/reabiertos confirmados | No hay gaps C pendientes. |

RED de correcciones: `test_B1_source_python_imports_its_verified_sibling_with_isolation`, `test_B2_requirements_checkout_is_explicitly_lf`, `test_A01_catalog_describes_current_pinned_installer`: 3 failed antes de modificar código/config/prosa (2026-11-06). B2/A-01: TDD n/a configuración/prosa; contratos de regresión dedicados.

Ampliación técnica T-04: .gitattributes protege el digest literal en Windows; docs/agents actualiza descripciones existentes; agents/nemesis.md limita el ejemplo de instalación a nombres expresamente autorizados. Interop se regenera desde esta fuente canónica (T-05). No se modifican criterios aprobados.
