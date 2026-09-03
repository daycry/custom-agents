---
spec: demo
estado: aprobada          # borrador | aprobada | implementada | obsoleta
creado: 2026-01-01
evaluacion: evaluation.md
plan: improvement-plan.md
---

# Spec — demo: exportación CSV de informes con filtro por fecha

> Evaluación: [`evaluation.md`](evaluation.md) · Plan: [`improvement-plan.md`](improvement-plan.md)

## Objetivo
Permitir exportar a CSV el listado de informes, filtrado por rango de fechas, desde `src/app.py`.

## Alcance
- In: función `exportar_csv` con filtro `desde`/`hasta`; escapado de comas y comillas.
- Out: exportación a Excel; envío por correo.

## Criterios de aceptación
- [ ] [GWT] CA-01 — Dado un listado con 3 informes, Cuando exporto con rango que cubre 2, Entonces el CSV tiene 2 filas + cabecera.
- [ ] CA-02 — Un campo con coma se exporta entre comillas.

## Supuestos / incógnitas
- Las fechas llegan en ISO-8601.
