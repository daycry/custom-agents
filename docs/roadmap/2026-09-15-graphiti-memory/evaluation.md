---
evaluation: graphiti-memory
estado: completado
spec: spec.md
plan: improvement-plan.md
---

# Evaluacion - graphiti-memory

**Go condicionado a `knowledge-services` completado.** Estimacion: 44h humanas (36h base +20%), 13.2h IA, 3.3h supervision y 470k tokens previstos; coste humano de referencia: 2,200 EUR a 50 EUR/h. Confianza media.

| Area | Base | Riesgo |
|---|---:|---|
| Contrato, modelo y adaptador | 10h | Duplicados y proyeccion no reversible. |
| Sincronizacion y backend local | 9h | Versiones, reintentos y schema de Graphiti. |
| Router y recuperacion | 7h | Consultar Graphiti para preguntas que son documentales. |
| Setup, doctor y seguridad | 4h | Endpoint remoto, telemetria y secretos. |
| Pruebas, interop y cierre | 6h | Dependencia Docker/modelo estructurado. |

Riesgo principal: Graphiti con Ollama necesita JSON estructurado fiable; se valida con fixtures antes de permitir sincronizacion real y se mantiene concurrencia baja.