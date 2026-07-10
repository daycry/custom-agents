# Agente: implementer

Implementa un **plan aprobado** ejecutándolo **fase a fase**. Es el eslabón que faltaba entre
`planner` y `qa`: convierte `improvement-plan.md` + `tasks.md` en **código funcionando**.

## Qué hace

- Lee la iniciativa en `docs/roadmap/<fecha>-<slug>/` (`improvement-plan.md`, `tasks.md`, `test-plan.md` si hay UI).
- Trabaja sobre una **rama de trabajo** (`feature/<slug>`), no la principal.
- Implementa cada tarea `T-XX` cumpliendo sus criterios de aceptación, siguiendo las convenciones del proyecto.
- Mantiene **`tasks.md` como ledger canónico**: marca cada tarea (checkbox + estado) y actualiza el resumen de progreso a medida que avanza.
- Hace **handoff a `qa`** al terminar. La documentación (`documenter`) va después, solo si `qa` queda en verde.

## Qué NO hace

- No planifica ni evalúa (eso es `planner`/`evaluator`).
- No prueba el producto (E2E lo hace `qa`) ni escribe la documentación de referencia (`documenter`).
- No toca `docs/roadmap/` salvo `tasks.md` (progreso), ni `docs/security-scan/`.

## A diferencia del resto

Es el **único agente que modifica el código** del proyecto. Por eso trabaja sobre rama, respeta
los guardrails del repo (p. ej. el local-only de `nemesis`) y no marca completado nada con tests
fallando o criterios sin cumplir.

## Ledger canónico

`tasks.md` es la **fuente única de verdad** del progreso. Si conviven otras herramientas con su
propio registro (todo-list, orquestadores externos como *superpowers SDD*), esos registros son
espejo, no fuente. Ver regla 8 de [`CONVENTIONS.md`](../CONVENTIONS.md).

## Uso

```
@implementer implementa el plan docs/roadmap/2026-07-10-mi-feature/
@implementer ejecuta la fase 2
```

O, dentro del ciclo completo, mediante el command `/dev-cycle`. Nota: `implementer` es el motor de
implementación **nativo** — el `/dev-cycle` lo usa cuando **no** hay superpowers instalado; si lo
hay, el backbone se delega en superpowers y `tasks.md` sigue siendo el ledger canónico.

## Dependencias

- Agente `qa` (handoff de pruebas al terminar).
