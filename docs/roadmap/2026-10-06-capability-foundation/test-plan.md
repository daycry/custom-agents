---
test-plan: capability-foundation
estado: aprobado
creado: 2026-10-06
---

# Panel local — pruebas de interacción

- **P-01 [GWT]** Dado el catálogo real, cuando se abre el HTML, entonces muestra
  los cinco totales del JSON y tarjetas con metadatos sin errores de JavaScript.
- **P-02 [GWT]** Dado el panel abierto, cuando se busca plugin-panel, entonces
  quedan visibles las tarjetas pertinentes y el contador refleja el resultado.
- **P-03 [GWT]** Dado el panel abierto, cuando se selecciona skills, entonces
  todas las tarjetas visibles corresponden a skills; limpiar restablece el catálogo.
- **P-04 [GWT]** Dado un viewport móvil de 390 px, cuando se usan búsqueda y
  selector, entonces los controles siguen visibles y no hay scroll horizontal.

Las verificaciones de redacción, symlinks y ownership son tests del script,
no sustituyen estas interacciones. No hay servicio remoto ni login en el panel.
