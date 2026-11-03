---
tasks: second-brain-foundation
estado: completado
creado: 2026-11-03
verificacion: obligatoria
changelog: Added
---

# Categorías y plantillas de conocimiento del proyecto

**Ledger canónico**. Requisitos: [spec.md](spec.md), acordados en la conversación.
Implementación autorizada por el usuario después de aclarar autoría y aprobación.

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 — Contratos | 1 | 1 | 100.0% |
| Fase 2 — Herramientas | 1 | 1 | 100.0% |
| Fase 3 — Integración y validación | 1 | 1 | 100.0% |
| **TOTAL** | **3** | **3** | **100.0%** |

## Fase 1 — Contratos

### T-01 — Configuración, formato y origen de las propuestas

- **Estado**: completado
- **Tipo**: backend
- **Descripción**: Añadir contratos opcionales de categoría y aplicarlos mediante los dueños existentes de taxonomía, aprobación y persistencia.
- **Archivos**: `agent-kits/shared/knowledge-taxonomy-local.py`, `agent-kits/shared/knowledge-curation-rules.py`, `agent-kits/shared/knowledge-curation.py`, `agent-kits/shared/schemas/taxonomy.schema.json`, `agent-kits/shared/test_knowledge_category_contract.py`.
- **Verificación**: `python -m pytest agent-kits/shared/test_knowledge_category_contract.py agent-kits/shared/test_knowledge_curation.py agent-kits/knowledge-curator/test_curator_gate.py -q` → contratos y persistencia correctos.
- **Changelog**: Los proyectos pueden exigir formato y declarar quién aporta contenido a cada categoría de conocimiento.

**Criterios de aceptación**
- [x] Configuración opcional validada; rutas y valores incompatibles se rechazan.
- [x] Metadatos y secciones obligatorios se comprueban antes de aprobar.
- [x] Código Markdown citado no satisface una sección obligatoria real.
- [x] Procedencia declarada compatible con productores permitidos, preservada al aprobar.
- [x] Categorías antiguas sin contrato mantienen el comportamiento existente.


RED: `agent-kits/shared/test_knowledge_category_contract.py` falló con 33 failed: contratos y politicas nuevas se ignoran; aprobacion acepta formato incompleto · 2026-11-03.


RED: `test_proposal_rechecks_policy_under_existing_cooperative_lock` falló con propuesta creada aunque allowed_producers cambio antes de adquirir el lock · 2026-11-03.


RED: `test_large_heading_whitespace_has_bounded_processing_time` falló con TimeoutExpired tras 8 segundos con 64000 espacios internos en encabezado · 2026-11-03.

## Fase 2 — Herramientas

### T-02 — Plantillas externas y revisión de carpetas

- **Estado**: completado
- **Tipo**: backend
- **Descripción**: Crear vista previa/aplicación recuperable para categoría y plantilla; lectura acotada; revisión sin cambios y propuestas mediante el servicio existente.
- **Archivos**: `skills/knowledge-category-template/**`, `commands/knowledge-category-check.md`, `agent-kits/shared/knowledge-write.md`, `agents/knowledge-curator.md`, `agent-kits/knowledge-curator/README.md`.
- **Verificación**: `python -m pytest skills/knowledge-category-template/scripts -q` → previews, colisiones, concurrencia, rutas y propuestas sintéticas correctas.
- **Changelog**: Una skill guía la creación de categorías y plantillas del proyecto; un comando revisa sus carpetas de entrada y prepara candidatos con fuentes.

**Criterios de aceptación**
- [x] Plantilla fuera del plugin y ruta registrada sin alterar preferencias ajenas.
- [x] Vista previa ligada a SHA; cambio concurrente o archivo ajeno no se sobrescribe.
- [x] Revisión por defecto no escribe; archivos originales y conocimiento aprobado permanecen intactos.
- [x] Propuesta explícita usa `knowledge-curation.py`, registra origen y no aprueba ni publica.
- [x] Lecturas, cantidades y tamaños acotados; enlaces y escapes rechazados.


RED: `skills/knowledge-category-template/scripts/test_category_template.py::test_preview_is_read_only_and_configuration_preserves_other_preferences` falló con unavailable en vez de preview; faltan configuracion y revision de carpetas · 2026-11-03.


RED: `test_proposal_rejects_change_after_preview_validation` falló con 2 failed: fuente o politica cambiada despues del token crea candidato obsoleto · 2026-11-03.


RED: `test_configuration_rejects_serialized_taxonomy_over_read_budget` falló con preview acepta configuracion serializada que excede el limite de lectura posterior · 2026-11-03.


RED: `test_B2_proposals_work_when_valid_taxonomy_omits_id_prefix` falló con changed_policy sin cambios concurrentes al omitir el campo opcional id_prefix · 2026-11-03.


RED: `test_B2_policy_snapshot_supports_all_graphiti_defaults_without_config_writes` falló con 2 failed: Graphiti sin group_id provoca changed_policy aun deshabilitado · 2026-11-03.


RED: `test_D2_proposals_reuse_the_original_policy_bytes_snapshot` falló con SHA expandido difiere del SHA de los bytes originales, repetido por candidato · 2026-11-03.

## Fase 3 — Integración y validación

### T-03 — Ejemplos, documentación, catálogo y regresiones

- **Estado**: completado
- **Tipo**: documentation
- **Descripción**: Integrar skill/comando, ejemplos meetings/FAQ/mixto y workflows legibles; validar superficies generadas, revisión adversarial y regresiones.
- **Archivos**: `agent-kits/shared/modules.json`, `.claude-plugin/**`, `ci.yml.MANUAL-COPY`, `.github/workflows/ci.yml`, `evals/cases/skill-knowledge-category-template.json`, `evals/cases/command-knowledge-category-check.json`, `interop/**`, `.agents/plugins/marketplace.json`, `.codex-plugin/plugin.json`, `docs/**`, `README.md`, `README.es.md`, `CLAUDE.md`, `CHANGELOG.md`, `CHANGELOG.es.md`, `tests/test_rationalization_tables.py`, `tests/test_knowledge_category_documentation.py`, `scripts/check-handbook.py`, `output/pdf/custom-agents-manual-operativo*`.
- **Nota de alcance**: Los manifiestos son proyecciones del exportador. El manual incorpora W-28–W-30 y sus ejemplos; su verificador conserva las comprobaciones de fuentes, PDF y diagramas.
- **Descripción de piezas**: `CLAUDE.md` (archivo adicional de T-03) se actualiza como índice de la skill y del comando, conforme a plugin-dev.
- **Regresión de consumidores**: `tests/test_knowledge_category_documentation.py` (archivo adicional de T-03) verifica que los contratos nuevos lleguen a las instrucciones del curator y que los enlaces de los índices resuelvan a workflows reales.
- **Verificación**: `python scripts/lint_plugin.py`; `python evals/check.py`; `python scripts/export-interop.py --check`; tests de exportación y suites afectadas → sin errores nuevos.
- **Changelog**: Documentación y ejemplos explican categorías humanas, de agentes y mixtas, con plantillas propias y destinos configurables.

**Criterios de aceptación**
- [x] Ejemplos ejecutables sin datos privados ni servicios externos.
- [x] Documentación ES/EN y catálogo explican límites reales de autoría, aprobación y publicación.
- [x] Interop y paquetes portables contienen las piezas y dependencias necesarias.
- [x] Revisión y regresiones completadas con evidencia.

TDD n/a: spec, ledger, instrucciones y documentación.

## Revisión de dos lentes — intento 1: Contratos y captura; A en curso, B1 y D1 pendientes de revalidacion (T-01, T-02, T-03)

Lentes A+B+D; C no seleccionada. Revisión completa sobre copia aislada, sin configuración privada.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A1 | Important | Dos proyecciones del curator antiguas en la copia QA | T-03 | Descartado (rebatido) para el árbol fuente; corregir la construcción del snapshot QA | En raíz `export-interop.py --check`: exit 0, 92 al día. La lista inicial de copia omitió esos dos archivos recién regenerados; la segunda copia recalcula la lista completa. |
| A2 | Important | Descripción E3 y catálogo incompletos | T-03 | Corregido, pendiente de revalidación | Actualizados `docs/agents/knowledge-curator.md`, `agent-kits/knowledge-curator/README.md` y `CLAUDE.md`. |
| A3 | Minor | Enlaces W-27 y rango dashboard incorrectos | T-03 | Corregido, pendiente de revalidación | Enlaces nuevos a W-29; dashboard conserva W-23 a W-27, categorías W-28 a W-30. |
| B1 | Important | Fuente o política cambiadas tras validar el token | T-02 | Corregido, pendiente de revalidación | La API de propose recibe snapshots y comprueba fuente/política bajo su lock. Test RED de ambas carreras y GREEN posterior. |
| D1 | Important | Regex cuadráticas en encabezados con espacios | T-01 | Corregido, pendiente de revalidación | Parser sin regex de cierre con retroceso; test con 64000 espacios agotó 8 s antes del arreglo y pasa después. |

A ejecutó 67 tests nuevos y 164 de regresión; B 231 tests; D reprodujo 22,19 s con 16 documentos de 4 KiB. Los omitidos Windows por enlaces requieren validación Linux.
El PDF estaba pendiente de incorporar al snapshot del intento 1; ese resultado no acredita el cierre.

## Revisión de dos lentes — intento 2: Revalidacion de A2 A3 B1 D1 y snapshot completo (T-01, T-02, T-03)

Lentes A+B+D, snapshot completo. C sigue no seleccionada.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A1 | Important | Proyecciones antiguas solo en primer snapshot | T-03 | Descartado (rebatido), confirmado | A ejecutó interop: exit 0, 92 al día; PDF: exit 0. |
| A2/A3 | Important/Minor | Descripciones y enlaces | T-03 | Contenido corregido y revalidado | A verificó E3, catálogo, anchors W-29 y dashboard W-23 a W-27. |
| A4 | Important | Faltaba prueba dedicada para A2/A3 | T-03 | Corregido, pendiente de revalidación | Dos tests de consumidores documentales comprueban campos públicos del contrato, catálogo y enlaces a headings reales. |
| B1 | Important | Carrera fuente/política | T-02 | Corregido y revalidado | Tests de ambas carreras pasan y se comprueban snapshots bajo lock. |
| B2 | Important | Prefijo opcional normalizado distinto al calcular SHA | T-02 | Corregido, pendiente de revalidación | RED sin id_prefix; hash usa la normalización del dueño compartido sobre una copia, sin editar preferencias. |
| D1 | Important | Encabezados con coste cuadrático | T-01 | Corregido y revalidado | D: 64K espacios 0,000444 s; cierre ATX 0,000397 s; revisión de 16 documentos 0,052372 s. |

A ejecutó 97 tests con 1 skip Windows y validó lint/evals/interop/manual. B ejecutó 246 con 3 skips Windows. D midió 128 documentos/2.096.896 bytes: revisión 0,470565 s y propuestas 2,467623 s con persistencia simulada; esas cifras no miden disco real. No se reabre lo aprobado sin nueva evidencia.

## Revisión de dos lentes — intento 3: Cierre de B2 y regresiones documentales A4 (T-01, T-02, T-03)

Lentes A+B+D; tercera y última ronda adversarial. No se reinician los contadores.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| A4 | Important | Pruebas dedicadas de consumidores | T-03 | Corregido y revalidado por A | 2 tests de documentación pasan; interop 92 y manual coinciden, exit 0. |
| B2 | Important | Faltaba también group_id derivado, incluso con Graphiti deshabilitado | T-02 | Corregido tras decisión del orquestador; pendiente de QA final | El servicio compara SHA de bytes originales bajo lock; deja de comparar representaciones expandidas. Casos Graphiti por type con clave propia y prefijos implícitos pasan sin escribir configuración. |
| D2 | Important | Copia de taxonomía invariable por candidato | T-02 | Corregido tras decisión del orquestador; pendiente de QA final | Eliminadas deepcopy/normalización y serialización de la política del bucle. Test D2 exige usar el mismo SHA original en todas las propuestas. |

**Decisión del orquestador al recibir el tercer intento:** continuar exclusivamente
con B2/D2 y su validación, dentro de la implementación autorizada. La solución
acotada utiliza el snapshot de bytes que ya existe; no añade otro normalizador,
una cuarta ronda adversarial ni deuda aceptada. Los veredictos originales de B/D
se conservan: la corrección posterior se acredita por reproducción RED y QA,
sin atribuirles una revisión que no ejecutaron.

B ejecutó 41 tests con 1 skip y reprodujo el fallo Graphiti. D midió +57 % de CPU
con la copia por candidato a límites máximos; ese código se eliminó. Después de
la corrección, regresión Windows: 195 passed, 3 skipped. QA final: 769 passed / 3 skipped en Python; 452 passed / 16 skipped en Node; gate 90,93 % frente a m?nimo 90, exit 0. Resultado y limitaciones
finales en [testing/verification.md](testing/verification.md).

## Evidencia final de cierre

[Verificaci?n reproducible](testing/verification.md): contratos, persistencia, ejemplos, interop, portable, instalador, cobertura y manual verificados. Los skips y las limitaciones de simulaci?n permanecen expl?citos. No se publica ni reindexa conocimiento externo.

## Publication preparation for v3.1.0

The full CI script gate caught missing category entries in the canonical manifest descriptions. Existing manifest and README count tests also covered the catalog update: 34 skills and 16 commands. Both Claude manifests and their generated Codex projections now agree; README counters and prose are synchronized in ES/EN. CI now runs the category tool suite explicitly. Existing tests were retained, without threshold changes.
