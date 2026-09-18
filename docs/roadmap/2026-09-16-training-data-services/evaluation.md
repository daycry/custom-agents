---
evaluation: training-data-services
estado: completado
spec: spec.md
plan: improvement-plan.md
creado: 2026-09-16
---

# Evaluacion - training-data-services

| Metrica | Estimado con margen | Confianza |
|---|---:|---|
| Tiempo humano | 39.5h (33h base +20%) — antes 41h | Media |
| Tiempo IA (ejecucion) | 12.3h | Media |
| Supervision | 3.1h | Media |
| Coste humano a 50 EUR/h | 1,975 EUR — antes 2,050 EUR | Media |
| Tokens IA | 415k in / 160k out — antes 430k / 170k | Baja |
| Complejidad | Alta | Media |

> **Spec:** [spec.md](spec.md)
> **Plan:** [improvement-plan.md](improvement-plan.md)

## Resumen ejecutivo

Reutiliza tres precedentes ya probados en este repo (redaccion de secretos de `journal.py`, deteccion de duplicados por shingles de `code-health.py`, aprobacion humana explicita con flag tipo `--qa-verde` de `jira-flow.py`), por lo que el riesgo tecnico es menor que el de `knowledge-services`: no hay agente nuevo, no hay dependencias nuevas, y el mecanismo de particion/anti-leakage es autocontenible. El riesgo real esta en el ALCANCE: mantenerlo estrictamente como mecanismo generico sin dejar que ninguna logica de dominio (metricas, herramientas) se cuele en el plugin.

## Caracteristicas evaluadas

| ID | Caracteristica | Complejidad | Horas humanas base | Riesgo principal |
|---|---|---:|---:|---|
| C-01 | Config, esquema de caso y redaccion compartida | Media | 8h | Duplicar la logica de secretos en vez de compartirla. |
| C-02 | Recorder determinista + puerta de aprobacion humana | Alta | 8h | Que un flujo automatizado marque Gold sin el flag humano. |
| C-03 | Deduplicacion por shingles y particion de benchmark anti-leakage | Alta | 8h | Fugar casi-duplicados entre train y benchmark. |
| C-04 | Ensamblador de dataset (formato chat) y puente a knowledge-curator | Media | 6h | Ensamblar cases no-Gold por error. |
| C-05 | Setup, doctor, regresion e interop | Media | 4h | Bloquear el ciclo si el proyecto no activa la capacidad. |
| **Total base** |  |  | **34h** |  |

## Supuestos economicos

- Tarifa de referencia: 50 EUR/h (misma que `knowledge-services`, no hay `rates.json` de consumidor que leer aqui).
- Margen +20% por ser una pieza nueva sin precedente exacto en el repo, aunque reutiliza tres mecanismos ya probados.
- Los tokens son previsión de elaboracion y revision; sin precio de tokens verificado, el coste de IA no se fija.

## Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigacion |
|---|---|---|---|
| Se cuela logica de dominio (metricas, herramientas) en el plugin | Media | Alto | El recorder solo valida FORMA (JSON valido, campos requeridos); nunca interpreta el contenido de `metrics.json`. |
| Un caso no-Gold entra en el dataset exportado | Baja | Alto | Filtro obligatorio por `validation.status == approved` + `approved_by_human == true`, con test que verifica que NINGUN otro estado pasa. |
| Leakage entre train y benchmark por versiones casi identicas | Media | Alto | Particion por familia completa, nunca por version suelta; test con familias sinteticas casi identicas. |
| Duplicar la redaccion de secretos en dos sitios (journal + recorder) | Media | Medio | Extraer a `agent-kits/shared/redact.py` ANTES de escribir el recorder; `journal.py` pasa a importarla. |
| El caso incluye binarios grandes (mallas, imagenes) inline | Media | Medio | El esquema solo acepta referencias (ruta + hash) para artefactos finales, nunca contenido binario inline. |

## Veredicto

**Go.** Encaja como tercera pieza del area de conocimiento sin depender de Graphiti, reutiliza mecanismos ya validados en el repo y mantiene una frontera de responsabilidad clara (mecanismo vs. dominio). Ejecutar despues de `knowledge-services` (necesita el puente al Curator) y en paralelo o despues de `graphiti-memory` indistintamente, porque no depende de ella.

## Enmienda 2026-09-17

La extraccion de `redact.py` (3 h) pasa a `session-end-durable-capture`, que ya refactoriza `journal.py`; aqui
entra en su lugar el registro de la capacidad `training` en `capabilities.py` (1.5 h, `ADR-018`). Neto **-1.5 h**
(41 h -> 39.5 h). Dependencias nuevas: `session-end-durable-capture` T-02 y `knowledge-services` T-13. El
veredicto se mantiene.
