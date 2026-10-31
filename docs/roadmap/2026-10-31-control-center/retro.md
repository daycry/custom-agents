---
retro: control-center
fecha: 2026-10-31
---

# Retro — Consola única, proyectos aislados y límites nativos

| Magnitud | Estimado | Real | Desviación |
|---|---|---|---|
| Horas | Sin presupuesto solicitado | No medidas de forma completa | No calculable |
| Tokens y coste | Sin estimación independiente | Sin medición completa | No calculable |
| Tokens/hora | Sin estimación | Sin medición independiente | No calibra |

## Observaciones de la entrega

La revisión detectó carreras de confirmación/cierre, una previsualización recortada y avisos perdidos al volver a una vista. Cada caso quedó nombrado en un test dedicado. Separar copia bajo lock y proyección redujo bytes serializados sin mezclar latencias de cargas diferentes.

Las fuentes son el ledger y testing/report.md, la revisión independiente y las ejecuciones enlazadas. No se atribuyen al usuario entrevistas ni causas de desviación que no aportó; sin horas/tokens no se calcula una desviación o ratio.

## Ajuste sugerido

Incluir desde el primer fixture respuestas nativas anteriores al ack, Unicode y cambios de proyecto/vista durante lecturas.

## Conocimiento y alcance

Esta retrospectiva registra observaciones del trabajo; no aprueba doctrina ni publica memoria externa. No se crea una propuesta de conocimiento ni se modifica approved desde este cierre. Los detalles permanecen en sus pruebas e informes, disponibles para una curación explícita posterior.

Entrega: [v3.0.0](https://github.com/daycry/custom-agents/releases/tag/v3.0.0); [CI del commit de versión](https://github.com/daycry/custom-agents/actions/runs/41169576551). Ollama sigue aplazado.
