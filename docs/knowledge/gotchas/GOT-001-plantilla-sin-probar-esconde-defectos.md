---
id: GOT-001
tipo: gotcha
area: Plantillas / revisión
estado: aceptada (validada: revisión de dos lentes, 2026-08-20, intento 3)
fuente: docs/roadmap/2026-08-12-plugin-dev/retro.md
---

## Una plantilla nueva sin probar rellenándola esconde defectos que el lector no ve

- **Síntoma:** una plantilla de agente recién escrita ("lo que otros rellenarán") parecía correcta
  a simple lectura.
- **Causa raíz:** nadie la había **rellenado** de verdad antes de darla por terminada. La revisión
  de dos lentes encontró dos defectos que solo aparecen al usarla: una invocación de `pytest` que
  no recogía las suites, y unos comentarios inline que habrían hecho que el linter del plugin
  rechazara cualquier agente creado a partir de esa plantilla.
- **Qué hacer en su lugar:** toda plantilla nueva lleva una verificación de uso real (rellenarla y
  pasarla por el validador que corresponda, p. ej. `lint_plugin.py`) como criterio de aceptación
  explícito — no basta con leerla.
- **Evidencia / fuente:** [`docs/roadmap/2026-08-12-plugin-dev/retro.md`](../../roadmap/2026-08-12-plugin-dev/retro.md).

`estado: aceptada (validada: revisión de dos lentes, 2026-08-20, intento 3)` (backfill de retro ya
cerrada).
