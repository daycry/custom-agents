---
tasks: demo
estado: borrador          # borrador | en-progreso | en-revision | completado | cancelado
creado: 2026-01-01
---

# Checklist de Tareas — demo

| | |
|---|---|
| **Estado** | borrador |
| **Fecha** | 2026-01-01 |
| **Plan** | [`improvement-plan.md`](./improvement-plan.md) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del plan. **Cualquier** implementador debe marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — Exportación CSV | 0 | 2 | 0% | 0 / 6h | 0 / 0,3h | 0 / 0,08h | 0 / 60k |
| **TOTAL** | **0** | **2** | **0%** | **0 / 6h** | **0 / 0,3h** | **0 / 0,08h** | **0 / 60k** |

---

## Fase 1 — Exportación CSV

**Estado**: borrador · **Estimado**: 6h · **Real**: — · **Coste est.**: 320 € · **Tokens est.**: 60k

### T-01 — Filtro por rango de fechas en `exportar_csv`

- **Descripción**: añadir parámetros `desde`/`hasta` (ISO-8601) y filtrar las filas antes de serializar.
- **Estado**: borrador
- **Tiempo humano**: est. 3h · real —
- **Tiempo IA (ejec.)**: est. 0,15h · real —
- **Supervisión**: est. 0,04h · real —
- **Tipo**: backend
- **Archivos**: `src/app.py`, `tests/test_app.py`
- **Cubre (tests)**: E2E-01

**Criterios de aceptación**
- [ ] CA-01: con 3 informes y un rango que cubre 2, el CSV tiene 2 filas + cabecera.
- [ ] Test unitario del filtro en `tests/test_app.py`.

### T-02 — Escapado de comas y comillas

- **Descripción**: un campo con coma o comillas se exporta entre comillas (RFC 4180).
- **Estado**: borrador
- **Tiempo humano**: est. 3h · real —
- **Tiempo IA (ejec.)**: est. 0,15h · real —
- **Supervisión**: est. 0,04h · real —
- **Tipo**: backend
- **Archivos**: `src/app.py`, `tests/test_app.py`
- **Cubre (tests)**: M-01

**Criterios de aceptación**
- [ ] CA-02: el campo `a,b` sale como `"a,b"`.
- [ ] Test unitario del escapado.
