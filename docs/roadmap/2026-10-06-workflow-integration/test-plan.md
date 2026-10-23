---
test-plan: workflow-integration
estado: aprobado
creado: 2026-10-06
---

# Interacción del panel del workflow

- **P-01 [GWT]** Dado el catálogo real, cuando se abre el panel, entonces los
  totales, capacidades y responsables corresponden a las fuentes sin errores JS.
- **P-02 [GWT]** Dado el catálogo, cuando se busca o filtra, entonces los resultados
  corresponden a la consulta y limpiar restaura el total.
- **P-03 [GWT]** Dado el workflow, cuando se consulta un rol, entonces se distinguen
  sus guías, sus responsabilidades y las capacidades opcionales de memoria.
- **P-04 [GWT]** Dado un viewport móvil de 390 px, cuando se utilizan los controles,
  entonces siguen visibles y no hay desborde horizontal.

Los contratos de selector, retirada y límites de brief tienen pruebas de script
propias; no se sustituyen por capturas o este plan.

- **P-05 [GWT]** Dado un evento con varios handlers, cuando se filtra por teclado,
  entonces hay una sola tarjeta con funciones, activación y nombres reconocibles.
- **P-06 [GWT]** Dado el menú, cuando se navega por clic, teclado o historial,
  entonces cambia la opción seleccionada y solo una conserva aria-current.
- **P-07 [GWT]** Dadas las etapas del workflow, cuando se selecciona cada una,
  entonces cambia su contenido y sus enlaces abren el rol nativo correspondiente.
