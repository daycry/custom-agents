---
plan: plugin-audit-remediation
estado: aprobado
creado: 2026-11-09
spec: spec.md
tasks: tasks.md
---

# Plan: corrección de la auditoría de v3.2.2

[Spec](spec.md) · [Ledger](tasks.md)

## Fases

| Fase | Objetivo | Tareas | Criterios |
|---|---|---|---|
| 1 | Seguridad y pérdida de datos | T-01…T-06 | CA-01, CA-02 |
| 2 | Funciones documentadas que no funcionan | T-07…T-12 | CA-03, CA-04 |
| 3 | Rendimiento de procesos | T-13…T-16 | CA-05 |
| 4 | Consumo de tokens | T-17…T-21 | CA-06, CA-07 |

## Método

- Cada tarea sigue TDD: primero el test que reproduce el hallazgo y su rojo registrado en el ledger, después el arreglo.
- Al cerrar cada fase hay revisión de dos lentes (A+B, más C/D según `review-lens-select.py`), con el bucle acotado a 3.
- Las fases 3 y 4 registran sus medidas en `testing/perf.md`: tiempos con el mismo método antes y después, y tamaños con `context-footprint.py`.
- Antes del PR se replica la CI completa en Linux (`python:3.11-slim`).
- Publicación con `release.py`, previa confirmación de la versión.

## Riesgos

- **Tests de líneas base de párrafos:** los cambios de prosa en `dev-cycle` y `knowledge-check` deben registrarse como reemplazos con motivo.
- **Puerta de tokens de la vía rápida:** apenas tiene margen (6002 de un mínimo de 6000). La fase 4 debería ampliarlo; las fases 1 y 2 no pueden consumirlo.
- **Pocos recursos en la máquina:** los tests se ejecutan por ficheros y con un solo contenedor a la vez.
