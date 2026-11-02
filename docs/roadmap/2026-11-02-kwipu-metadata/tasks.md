---
tasks: kwipu-metadata
estado: en-progreso
creado: 2026-11-02
verificacion: obligatoria
changelog: Fixed
---

# Metadatos legibles en la exportación Kwipu

**Ledger canónico** de esta corrección solicitada por el usuario.

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 — CA-17 | 1 | 1 | 100.0% |
| **TOTAL** | **1** | **1** | **100.0%** |

## Fase 1 — CA-17

### T-01 — Conservar title y tags aprobados

- **Estado**: completado
- **Tipo**: backend
- **Descripción**: Propagar los metadatos opcionales desde el índice al adaptador, exportarlos con YAML seguro e incluirlos en la detección de cambios. Mantener coherente la comprobación de lectura documental.
- **Archivos**: `agent-kits/shared/knowledge-local.py`, `agent-kits/shared/knowledge-taxonomy-local.py`, `skills/knowledge-services/backends/markdown_export.py`, tests del adaptador y contrato CA-17.
- **Verificación**: pytest de metadatos, adaptador, sincronización y lectura documental; lint e interop; comprobación local --check. La reindexación externa se valida por separado de los tests sin red.

- RED adicional: sincronización con tags JSON inline perdió comas y escapes (`nota:` truncada); corregido el parsing limitado de metadatos, sin ampliar a YAML arbitrario · 2026-11-02.
- TDD n/a: contrato y changelogs, documentación.

**Criterios de aceptación**
- [x] title y tags llegan sin inventar valores; ausencias independientes no fallan.
- [x] YAML conserva dos puntos, comillas y Unicode.
- [x] Cambios de metadatos invalidan el hash; la migración y las pasadas siguientes son idempotentes.
- [x] Sincronización y puerta de lectura documental usan la misma proyección.
- [x] CA-17 y changelogs EN/ES explican los campos y la actualización.

## Verificación observada — 2026-11-02

- Linux aislado, imagen de QA ya disponible, sin red externa: 1.236 casos,
  0 fallos, 0 errores y 3 omitidos (1.233 pasados). `coverage-gate.py`
  sobre los tres ficheros de implementación cambiados: **91,61 %**, mínimo 90 %.
  La primera selección pasó 659 casos pero midió 85,89 %; se amplió a las
  regresiones existentes de recuperación, portabilidad y curación, sin bajar el umbral.
- Windows: 650 pasados, 2 omitidos y un fallo intermitente ajeno a este diff en
  `test_ca01_sin_training_json_o_desactivado_el_ciclo_es_identico`:
  dos consultas del doctor observaron distinto resultado de la CLI nativa Codex
  (timeout frente a versión reconocida). Repetido aisladamente: 1 pasado.
  No se presenta esa primera ejecución como totalmente verde.
- `lint_plugin.py`: 0 errores y 7 avisos existentes. Evals: 221 casos, 0 errores.
  `export-interop.py --check`: 88 ficheros al día. `git diff --check`: sin errores.
- Integración de prueba: sincronizar desde approved y ejecutar `--check` contra
  un servidor loopback con snapshot de los metadatos publicados devuelve verify.ok.
- Lector instalado de Kwipu: `parse_frontmatter()` y `enrich_documents()` aceptan
  dos fixtures sintéticas con comillas, acentos, emoji y etiquetas con comas.
  Sin inferencia ni persistencia. No equivale a regenerar el índice productivo.
- La inspección del stack confirma dos ajustes externos pendientes: las listas se
  aplanan a texto al enriquecer documentos y los chunks no asignan `name` desde title.
  Se explican al usuario con un prompt en el chat; no se crea fichero de handoff.
- Autorrevisión de conformidad y corrección: propagación por índice/routing,
  hash de publicación/lectura común, campos opcionales, escape YAML y posición
  temprana del hash para recuperación con listas largas comprobados.
- Los cambios no publican datos en Graphiti ni modifican approved. La actualización
  del índice de Kwipu con estos nuevos metadatos queda pendiente de la operación
  externa; no se declara completada ni se inicia una nueva inferencia cloud.

RED: `skills/knowledge-services/scripts/test_kwipu_metadata.py` falló con KeyError title en adaptador y sync; falta invalidacion del hash por metadatos · 2026-11-02.
