---
evaluation: graphiti-memory
estado: completado
spec: spec.md
plan: improvement-plan.md
---

# Evaluacion - graphiti-memory

**Go condicionado a `knowledge-services` completado.** Estimacion (enmienda 2026-09-17): **50h humanas (42h base +20%)**, 15h IA, 3.8h supervision y 545k tokens previstos; coste humano de referencia: **2,500 EUR** a 50 EUR/h. Confianza media. (Antes: 44h / 36h base, 13.2h IA, 470k tokens, 2,200 EUR.)

| Area | Base | Riesgo |
|---|---:|---|
| Contrato, ontologia desde taxonomia y adaptador del contrato de knowledge-services | 11h | Duplicados y proyeccion no reversible; adaptador que se salte `routing`. |
| Sincronizacion (sobre `outbox.py`), proveedor configurable, shadow mode, rebuild y revocacion | 13h | Versiones, reintentos y schema de Graphiti; salida estructurada de Ollama. |
| Router por configuracion + intent declarado | 8h | Consultar Graphiti para preguntas que son documentales; un intent mal declarado. |
| Setup, doctor y seguridad | 4h | Endpoint remoto, telemetria y secretos. |
| Pruebas, interop y cierre | 6h | Dependencia Docker/modelo estructurado. |

Riesgo principal: Graphiti con Ollama necesita JSON estructurado fiable; se valida con fixtures antes de permitir sincronizacion real y se mantiene concurrencia baja.

## Enmienda 2026-09-17

+6 h base (proveedor configurable 2h · shadow/rebuild/revoke 3h · ontologia desde taxonomia 1h) a cambio de:
Graphiti como **segundo adaptador** del contrato (prueba de extensibilidad), ningun modelo/endpoint cableado,
rollout seguro por `mode` y reconstruccion verificable. Entra tambien como dependencia el `outbox.py` de
`session-end-durable-capture` (a traves de knowledge-services). El veredicto se mantiene.
