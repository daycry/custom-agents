---
retro: plugin-audit-remediation
fecha: 2026-11-10
---

# Retro — Corrección de la auditoría completa de v3.2.2

| Magnitud | Estimado | Real | Desviación |
|---|---|---|---|
| Horas humanas | Sin presupuesto (no hubo evaluación) | No registradas | No calculable |
| Horas IA | Sin estimación | 4,43 h medidas en 15 de 21 tareas; los ciclos de corrección no se midieron | No calculable; la medida se queda corta |
| Tokens y coste | Sin estimación | Sin medición completa | No calculable |
| Tokens/hora | — | Sin tokens medidos | No calibra |

Las cifras salen del ledger ([tasks.md](tasks.md)); la IA medida es la suma de los campos «real … (medido)».

## Hechos de la ejecución

- 21 tareas en 4 fases; las cuatro fases agotaron los tres intentos de la revisión adversarial y terminaron con un ciclo final acotado decidido por el orquestador: 12 secciones de revisión, todas con gaps Important (fase 4: 6, 5 y 3 por intento).
- La CI del PR #32 estuvo en rojo desde `544b50d` (T-14, fase 3) durante 12 ejecuciones sin que se detectara; se vio al empezar la fase 4 y se corrigió dentro de T-21 (`b3f899d`, `d47c787`).
- Riesgo residual aceptado por el orquestador: formas ofuscadas de shell sin el token literal `SHAREDKIT` siguen pudiendo asignar la variable; documentado en `docs/CONVENTIONS.md` y en la traza del intento 3 de la fase 4.

## Causas (respuestas del usuario, que aceptó los borradores del orquestador)

1. **Tres intentos y ciclo final en cada fase.** Las correcciones se hacían caso a caso en lugar de por diseño (por ejemplo, las formas de la línea del kit), y cada arreglo abría un caso nuevo. Mejoró cuando el orquestador fijó el diseño en el ciclo final.
2. **Incógnita cara.** La paridad entre los tres runtimes y las particularidades de Windows (el `bash` de WSL en las sondas, las rutas cortas 8.3).
3. **Qué se haría distinto.** Vigilar la CI en cada push y no solo al cerrar fase; estimar antes de empezar, aunque sea una auditoría; medir todas las tareas con `usage-meter`.

## Ajuste sugerido

En remediaciones de auditoría, presupuestar al menos tres intentos de revisión por fase y fijar el diseño de las correcciones de seguridad antes del primer fix, no después del tercero.

## Conocimiento y alcance

Esta retrospectiva registra observaciones; no aprueba doctrina ni crea propuestas de conocimiento. La lección sobre la CI («vigilar cada push») queda como candidata para la próxima curación si se repite. Siguiente iniciativa: [plugin-audit-2](../2026-11-10-plugin-audit-2/improvement-plan.md).
