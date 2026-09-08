---
id: GOT-008
tipo: gotcha
area: Memoria técnica / recuperación
estado: aceptada (validada por usuario, 2026-09-08)
fuente: docs/roadmap/2026-09-04-memory-retrieval/retro.md (T-20/T-21 — cuatro recortes del ledger; revisión F4 gap A3)
---

## El tope CA-08 del brief (`task-brief.py` ≤ 10.000) no es una constante: cambia con la ruta absoluta del repo y crece con `docs/knowledge/`

- **Síntoma:** `test_ca08_el_brief_completo_cabe_en_el_tope_sobre_el_ledger_real_de_memory_retrieval` pasaba en el
  sandbox Linux con T-19 en **9.931** y fallaba en Windows con el MISMO ledger en **10.186**; y al añadir dos entradas
  a `docs/knowledge/` (ADR-013, LES-015) **todos** los briefs crecieron ~240 caracteres a la vez, tirando T-19 y T-20
  por encima del tope sin haberlos tocado.
- **Causa:** el brief incrusta la **ruta absoluta** de `knowledge-find.py` (en esta máquina, bajo `OneDrive - Imagina
  Media Audiovisual S.L`, ~250 caracteres más larga que en el sandbox) y su sección de memoria **crece con el corpus**
  hasta saturar `MEMORIA_TOPE_CHARS = 2400`; el test mide sobre el ledger real, así que el margen que le queda a cada
  tarea depende de la máquina y del día.
- **Arreglo:** deja **margen** en los bloques de tarea del ledger (≤ ~9.500 caracteres medidos en la máquina de
  trabajo, no al borde de 10.000); las tareas de cierre de gaps son las que más se acercan porque acumulan
  Verificación. El segundo efecto está acotado: la sección de memoria crece hasta `MEMORIA_TOPE_CHARS = 2400` y
  ahí se detiene.
- **Descartado, medido (2026-09-08):** sustituir la ruta absoluta por `$KF` + la resolución `find` de la regla 5
  **no ahorra**: la línea del `find` (≈113 caracteres) cuesta lo mismo que la ruta que quita, y al acortarse la
  cabecera entra otro acierto en la sección — los briefs SUBIERON (T-18: 10.180 → 10.268). Si algún día hay que
  recuperar ese margen, el camino es el tope de la sección, no la forma del comando.
