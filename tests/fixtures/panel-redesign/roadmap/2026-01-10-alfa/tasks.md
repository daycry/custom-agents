---
verificacion: obligatoria
---

# Checklist de Tareas — Alfa

| | |
|---|---|
| **Estado** | en-progreso |
| **Plan** | [`improvement-plan.md`](./improvement-plan.md) |

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 | 1 | 2 | 50% | 3 / 6h | 1,5 / 2h | 0,4 / 0,5h | 380k / 420k |
| **TOTAL** | **1** | **2** | **50%** | **3 / 6h** | **1,5 / 2h** | **0,4 / 0,5h** | **380k / 420k** |

## Fase 1

### T-01 — Primera tarea

- **Estado**: completado
- **Verificación**: `pytest -q` → `passed`

**Criterios de aceptación**
- [x] Hecho.

### T-02 — Segunda tarea

- **Estado**: en-progreso
- **Verificación**: `pytest -q` → `passed`

**Criterios de aceptación**
- [ ] Pendiente.

## Revisión de dos lentes — intento 1: 2 gaps abiertos (0 Critical, 1 Important, 1 Minor)

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | Falta validar la entrada vacía | T-02 | pendiente | `pytest -q` rojo |
| 2 | Minor | Mensaje de error poco claro | T-02 | pendiente | revisión manual |
