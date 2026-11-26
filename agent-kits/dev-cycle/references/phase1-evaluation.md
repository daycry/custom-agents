## Fase 1 — Evaluar (siempre en flujo completo, agente `evaluator`)
Invoca **`evaluator`** con el objetivo y el encargo conservado en la Fase 0: crea/lee `spec.md` y produce `evaluation.md` (coste, esfuerzo, veredicto). Esto es valor propio: el presupuesto en €/tokens antes de construir.

**Puerta go/no-go:** muestra el veredicto y pregunta si continuar. La transición la aplica la herramienta, igual que en `/pm-cycle`: `python3 "$SHAREDKIT/roadmap-sync.py" gate docs/roadmap/<fecha>-<slug> --decision go` (spec `aprobada`, evaluación `completado` y fila del índice, todo o nada) o `--decision no-go [--descartar]` (evaluación `cancelado`; spec `obsoleta` si se descarta) y, en no-go, para. Exit 1 `decision_already_taken`: la puerta ya se decidió; no la reabras a mano.
