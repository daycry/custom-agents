---
tasks: memory-integrations
estado: completado
creado: 2026-10-31
verificacion: obligatoria
changelog: Changed
---

# Memoria local y servicios opcionales

Ledger canónico. Alcance solicitado expresamente por el usuario durante la revisión
del manual: implementación robusta, UI moderna y útil, documentación detallada,
commits, push, PR y release v3.0.0. Se permiten cambios mayores sin retrocompatibilidad.
Las interfaces nativas se verifican; las limitaciones se presentan, no se simulan.

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 — Entrega | 3 | 3 | 100.0% |
| **TOTAL** | **3** | **3** | **100.0%** |

## Fase 1 — Entrega

### T-01 — Separar entrega y selección de servicios

- **Estado**: completado
- **Tipo**: backend
- **Descripción**: Extraer knowledge-services del perfil core a memory-integrations. Mantener curación y recuperación local sin adaptadores; comprobar copias y exportaciones selectivas.
- **Changelog**: Los servicios externos pasan a memory-integrations; la curación y recuperación locales siguen en core sin depender de un backend.
- **Archivos**: `skills/**`, `agent-kits/**`, `install/**`, `tests/**`, `docs/**`, `commands/**`, `agents/**`, `scripts/**`, `interop/**`, `output/pdf/**`, `README*`, `CHANGELOG*`, `package.json`
- **Verificación**: criterios del plan y evidencia en testing/report.md.

**Criterios de aceptación**
- [x] Comportamiento observado y límites contrastados; pruebas pertinentes y documentación coherentes. No confundir configuración, conexión, envío y confirmación.

### T-02 — Unificar el puerto de integraciones

- **Estado**: completado
- **Tipo**: backend
- **Descripción**: Añadir contratos/bindings de memoria con autorización, routing por categoría y recuperación existente; contexto de código separado. No duplicar curación, taxonomía ni outbox.
- **Changelog**: Los backends usan bindings del puerto común sin duplicar taxonomía, routing, curación ni outbox.
- **Archivos**: `skills/**`, `agent-kits/**`, `install/**`, `tests/**`, `docs/**`, `commands/**`, `agents/**`, `scripts/**`, `interop/**`, `output/pdf/**`, `README*`, `CHANGELOG*`, `package.json`
- **Verificación**: criterios del plan y evidencia en testing/report.md.

**Criterios de aceptación**
- [x] Comportamiento observado y límites contrastados; pruebas pertinentes y documentación coherentes. No confundir configuración, conexión, envío y confirmación.

### T-03 — Documentar y verificar cada recorrido

- **Estado**: completado
- **Tipo**: backend
- **Descripción**: Kwipu, Graphiti y Graphify con ejemplos validados, capacidades/límites actuales, separación publicar/leer y respaldo local. Sin prometer instalaciones o aceptación nativa no observadas.
- **Changelog**: Workflows ES/EN y PDF explican Kwipu, Graphify y Graphiti, con autorización, recuperación y límites de publicación y lectura.
- **Archivos**: `skills/**`, `agent-kits/**`, `install/**`, `tests/**`, `docs/**`, `commands/**`, `agents/**`, `scripts/**`, `interop/**`, `output/pdf/**`, `README*`, `CHANGELOG*`, `package.json`
- **Verificación**: criterios del plan y evidencia en testing/report.md.

**Criterios de aceptación**
- [x] Comportamiento observado y límites contrastados; pruebas pertinentes y documentación coherentes. No confundir configuración, conexión, envío y confirmación.


RED: tests/test_module_selection.py::test_memory_services_are_opt_in_without_removing_local_memory_roles falló: knowledge-services todavía estaba en core · 2026-10-31.
