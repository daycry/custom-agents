# Test plan — demo

## E2E-01 — Exportar con filtro de fechas
- Dado: 3 informes en la vista `/informes`.
- Cuando: filtro 2026-01-01..2026-01-15 y pulso «Exportar CSV».
- Entonces: se descarga un CSV con 2 filas + cabecera. Cubre CA-01.

## M-01 — Escapado manual
- Abrir el CSV en una hoja de cálculo y comprobar que `a,b` queda en una sola celda. Cubre CA-02.
