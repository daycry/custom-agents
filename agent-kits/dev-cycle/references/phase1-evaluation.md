## Fase 1 — Evaluar (siempre en flujo completo, agente `evaluator`)
Invoca **`evaluator`** con el objetivo y el encargo conservado en la Fase 0: crea/lee `spec.md` y produce `evaluation.md` (coste, esfuerzo, veredicto). Esto es valor propio: el presupuesto en €/tokens antes de construir.

**Puerta go/no-go:** muestra el veredicto y pregunta si continuar. Si no-go, para.
