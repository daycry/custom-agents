---
evaluation: dev-cycle-dataset
estado: completado
spec: spec.md
plan: improvement-plan.md
creado: 2026-09-16
---

# Evaluacion - dev-cycle-dataset

| Metrica | Estimado con margen | Confianza |
|---|---:|---|
| Tiempo humano | 26h (22h base +20%) | Media |
| Tiempo IA (ejecucion) | 7.8h | Media |
| Supervision | 2h | Media |
| Coste humano a 50 EUR/h | 1,300 EUR | Media |
| Tokens IA | 260k in / 100k out | Baja |
| Complejidad | Media | Alta |

> **Spec:** [spec.md](spec.md) · **Plan:** [improvement-plan.md](improvement-plan.md)

## Resumen ejecutivo

Coste menor que `training-data-services` porque reutiliza integramente su mecanismo (esquema, recorder, dedup, ensamblador): esta iniciativa es solo el ADAPTADOR — de donde salen `request`/`context`/`constraints`/`trajectory` para una tarea del propio ciclo, y como se deriva `outcome`/`validation` sin juicio nuevo del LLM. La complejidad es alta pese al coste moderado porque toca un punto sensible (Fase 6 del ritual de cierre) y debe demostrar, con tests, que el modo por defecto nunca filtra codigo fuente.

## Caracteristicas evaluadas

| ID | Caracteristica | Complejidad | Horas base | Riesgo principal |
|---|---|---:|---:|---|
| C-01 | Opt-in `datasetCapture` en `dev.json` + mapeo tarea->caso (modo metadata) | Media | 7h | Que `metadata` filtre sin querer fragmentos de diff. |
| C-02 | Derivacion deterministica de outcome/validation | Alta | 7h | Que un caso quede `approved` sin que qa-gate/revision lo respalden de verdad. |
| C-03 | Hook en Fase 6 (Gold humano) + modo `full-diff` opt-in separado | Media | 5h | Que `full-diff` se active por error junto al opt-in basico. |
| C-04 | Regresion, interop, doc y cierre | Media | 3h | Cobertura insuficiente del caso "iniciativa entera reservada". |
| **Total base** |  |  | **22h** |  |

## Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigacion |
|---|---|---|---|
| El modo `metadata` filtra fragmentos de codigo por descuido (p. ej. en `- **Notas**:` libres) | Media | Alto | Lista blanca de campos permitidos (Descripcion/Criterios/Archivos/Verificacion/Changelog), nunca lista negra; todo lo no listado se descarta. |
| Un caso se marca `approved` sin qa-gate verde real | Baja | Alto | Test que fuerza `qa-gate` rojo y comprueba que el adaptador NUNCA propone `approved`. |
| `full-diff` se activa sin que el usuario entienda el riesgo | Media | Medio | Requiere dos claves separadas en `dev.json`; `/setup` explica el riesgo en una frase antes de ofrecerlo. |
| Familia mal cortada (tarea suelta en vez de iniciativa) filtra casi-duplicados entre train/benchmark | Baja | Alto | Test con una iniciativa de 3 tareas casi identicas: todas caen en el mismo lado de la particion. |

## Veredicto

**Go**, condicionado a que `training-data-services` este implementado primero (dependencia dura declarada en la spec). Es la iniciativa de menor riesgo estrategico de las cuatro: no inventa mecanismo nuevo, solo demuestra que el ya diseñado sirve para un dominio real sin tocar nada fuera de `/dev-cycle` Fase 6 y `.claude/dev.json`.
