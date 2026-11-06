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
| Fase 1 | 4 | 5 | 80.0% |
| **TOTAL** | **4** | **5** | **80.0%** |

## Fase 1
**Estado**: en-progreso

### T-01 — Vistas Atlassian seguras

- **Estado**: completado
- **Archivos**: `skills/jira-sync/assets/**`, `skills/roadmap-dashboard/assets/**`, `skills/confluence-publish/assets/**`, `agent-kits/shared/render-artifact.py`, `skills/jira-sync/references/destination-and-types.md`, `skills/confluence-publish/references/wizard.md`, `docs/atlassian-connector-notes.md`, `skills/roadmap-dashboard/**`, `tests/artifact-dom-security.test.mjs`, `tests/test_artifact_renderer.py`
- **Changelog**: Metadatos Atlassian como texto, configuración JSON segura y etiquetas JQL confinadas al literal; renderer y referencias coherentes.
- **Verificación**: tests dirigidos y regresiones del área; evidencia ejecutada en [testing/validation.md](testing/validation.md).

**Criterios de aceptación**
- [x] F-001: títulos, nombres y errores son texto literal; configuración no rompe HTML/JS; selección conserva identidad y valores.


RED: `tests/artifact-dom-security.test.mjs` falló con RED navegador Edge: tres vistas ejecutan onerror desde metadatos externos; 0 passed y 3 failed · 2026-11-06.

### T-02 — Conversión PDF segura

- **Estado**: completado
- **Archivos**: `skills/to-pdf/**`, `tests/to-pdf*.test.mjs`
- **Changelog**: PDF con sandbox activo y JS/red desactivados por defecto; excepciones explícitas y salida atómica preservada.
- **Verificación**: tests dirigidos y regresiones del área; evidencia ejecutada en [testing/validation.md](testing/validation.md).

**Criterios de aceptación**
- [x] O-003: sandbox predeterminado, JS/red desactivados, excepciones documentadas, título escapado y salida atómica conservada.


RED: `tests/to-pdf-security.test.mjs` falló con RED: sandbox desactivado por defecto y sin política JS/red; CLI real con navegador sustituido por fixture · 2026-11-06.

### T-03 — CI con permisos acotados

- **Estado**: completado
- **Archivos**: `ci.yml.MANUAL-COPY`, `release.yml.MANUAL-COPY`, `headless.yml.MANUAL-COPY`, `.github/workflows/**`, `tests/test_ci*.py`, `docs/**/guides/nemesis-remediation.md`
- **Changelog**: Acciones por SHA, secretos por paso, permisos mínimos y build de release separado del publicador.
- **Verificación**: tests dirigidos y regresiones del área; evidencia ejecutada en [testing/validation.md](testing/validation.md).

**Criterios de aceptación**
- [x] O-002: secretos sólo en pasos consumidores; acciones por SHA completo, CLI fijada, permisos mínimos y copias manuales idénticas.


RED: `tests/test_ci_security.py` falló con RED previo: 5 contratos fallan por tags mutables, clave en job y build con token write; config/prosa TDD n/a, contratos verificados · 2026-11-06.

### T-04 — Herramientas opcionales verificadas

- **Estado**: completado
- **Archivos**: `agent-kits/nemesis/tools/**`, `agent-kits/nemesis/README.md`, `agents/nemesis.md`, `docs/agents/nemesis.md`, `docs/agents/nemesis-toolkit.md`, `.gitattributes`, `tests/test_nemesis_tools*.py`, `docs/**/guides/nemesis-remediation.md`
- **Changelog**: Herramientas opcionales con pins y hashes, extracción segura y propiedad verificada; no sobrescribir instalaciones ajenas o modificadas.
- **Verificación**: tests dirigidos y regresiones del área; evidencia ejecutada en [testing/validation.md](testing/validation.md).

**Criterios de aceptación**
- [x] O-001: catálogo con versiones/revisiones/hashes fijados y procedencia verificable; rechazar integridad inválida, archivos inseguros e instalaciones desconocidas sin sobrescribirlas; no instalar herramientas reales durante tests.

RED: `tests/test_nemesis_tools.py::InstallerPolicy::test_no_mutable_install_sources_or_eval` falló por resolver `/releases/latest` al instalar · 2026-11-06.

GREEN dirigido T-04: 13 pruebas offline. RED adicional del quoting de argumentos observado y corregido.

### T-05 — Regresión, revisión y entrega

- **Estado**: en-progreso
- **Archivos**: `docs/roadmap/2026-11-06-nemesis-remediation/**`, `docs/roadmap/README.md`, `docs/guides/nemesis-remediation.md`, `docs/en/guides/nemesis-remediation.md`, `CHANGELOG.md`, `CHANGELOG.es.md`, `tests/test_console_encoding.py`, `interop/**`, `docs/README.md`, `docs/en/README.md`
- **Changelog**: Regresiones, revisión independiente y documentación bilingüe de la remediación; sin publicación npm ni release.
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

## Revisión de dos lentes — intento 2: Fase 1 (T-01–T-05) — verde A+B+C

Head e351d2c, 43 archivos. A confirma A-01 y E2/E3; B confirma B1/B2; C no encuentra vulnerabilidades introducidas/reabiertas. Cada lente ejecutó 16 tests de herramientas; A/C verificaron interop (92 al día), A scope/ledger-lint sin incoherencias. D no aplica por selector. Sin gaps nuevos en esas lentes.

## Apoyo de Claude CLI — snapshot bb5ca20

Revisión sólo lectura con Claude Code 2.1.311 y Opus; sin Bash, red, MCP ni persistencia de sesión. Salida final recibida, no fue una ejecución cancelada. Confirma B1, B2 y A-01, e identifica:

| ID | Grado adjudicado | Evidencia | Acción |
|---|---|---|---|
| Claude-04 | Important | agents/nemesis.md invocaba catálogo completo tras aprobar sólo faltantes | Ya corregido en e351d2c con --only nombres autorizados; se añade contrato dedicado. |
| Claude-05 | Important | jira-live:70 concatena LABEL sin escapar y permite operadores fuera del literal | Confirmado mediante fixture JS; serializar un único literal JQL. |
| Claude-06 | Minor | Referencias usan CONFIG_JSON ambiguo aunque --config espera una ruta; nota central aún menciona marcadores antiguos | Explicitar fichero/ruta CONFIG_FILE y actualizar nota central; contrato dedicado. |

RED adicional: Claude-05, 1 passed/2 failed (comillas que amplían filtro y barra que cambia el valor); Claude-06, 1 failed por instrucciones de ruta ambiguas. Antes de las correcciones (2026-11-06). Claude-04/06: TDD n/a prosa; contrato dedicado. Los aspectos no confirmados por Claude (CSS con JS desactivado, compatibilidad de archivos upstream) están cubiertos por conversión real y lectura validada de los tres archivos fuente; no se ejecutaron herramientas externas.

Ampliación técnica T-01: docs/atlassian-connector-notes.md describe la parametrización que este cambio sustituye; se actualiza para evitar reintroducir sustitución insegura. Criterios funcionales sin cambios.

## Revisión de dos lentes — intento 3: Fase 1 (T-01–T-05) — sin Critical/Important

Head 2bbfbc9, 44 archivos, A+B+C; D no aplica. B/C aprueban el literal JQL y conservan cierres previos. A confirma criterios y detecta un Minor residual de Claude-06: live-artifact.md aún usaba CONFIG_JSON ambiguo. Se amplió el mismo test dedicado a las tres referencias, se observó RED (1 failed) y se corrigió la tercera referencia a CONFIG_FILE con ruta explícita. GREEN posterior: 10 tests renderer y 17 tools. Corrección sólo de prosa/test, sin cuarta ronda ni código funcional nuevo; Minor cerrado por evidencia. No quedan gaps de revisión aceptados pendientes.

Los revisores ejecutaron contratos dirigidos (27 Python, 3 JQL) y A comprobó scope/ledger-lint/interop sin incidencias. CI y entrega continúan en T-05.

## Regresión completa — integración de consola

CI 42194293340 (e351d2c) falló: 10504 passed, 41 skipped, 87 subtests, cuatro fallos por ausencia del modo render-artifact en el inventario general de consola y uno del test previo de benchmark adaptativo. El renderer ya tenía el snippet UTF-8, pero la suite exige registrar un modo que emita HTML Unicode real; se añade stdin JSON válido para jira-live, con los mismos asserts ASCII/cp1252. RED: cuatro fallos de la suite general observados en CI antes del registro. TDD n/a inventario de pruebas/configuración; no se modifica código ni se relajan puertas.

Ampliación técnica T-05: tests/test_console_encoding.py registra la nueva pieza bajo el contrato de consola existente. El test de benchmark y los umbrales de rendimiento permanecen sin cambios; su variación se valida de nuevo de forma dirigida y en CI.
