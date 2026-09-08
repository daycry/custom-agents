---
id: LES-001
tipo: leccion
area: Estimación / calibración
estado: aceptada (validada: usuario, 2026-01-01)
fecha: 2026-01-01
fuente: docs/roadmap/2025-12-01-informes-v1/retro.md#estimado-vs-real
---

## evaluator

- **«Exportar a CSV» nunca es trivial en este proyecto.** La primera versión se estimó en 2 h y costó
  9: el escapado (RFC 4180), las fechas ISO-8601 con zona horaria y la codificación (BOM para la hoja
  de cálculo) aparecieron después. Presupuesta el escapado y la codificación como tareas propias, no
  como «detalles» de la exportación.
