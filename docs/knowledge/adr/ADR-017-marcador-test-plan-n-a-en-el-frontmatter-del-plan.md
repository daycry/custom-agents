---
id: ADR-017
titulo: "El caso «sin UI» se declara con `test-plan: n/a (sin UI)` en el frontmatter de `improvement-plan.md`"
estado: propuesta          # propuesta | aceptada | obsoleta
fecha: 2026-09-10
iniciativa: plugin-refactor
---

# ADR-017: El caso «sin UI» se declara con `test-plan: n/a (sin UI)` en el frontmatter de `improvement-plan.md`

## Contexto

Tres piezas se contradicen en el caso sin interfaz (hueco **E1** del `analysis.md` §8-bis de
`2026-09-09-plugin-refactor`): `planner` genera `test-plan.md` «si hay UI», `qa` sin `test-plan.md`
avisa «hay que (re)generarlo con `planner`» (`agents/qa.md:94`) y `/dev-cycle` Fase 3 invoca `qa`
**siempre**. Seguido al pie de la letra es un bucle sin salida que hoy resuelve el criterio del
orquestador en prosa — justo lo que el plugin prohíbe (regla de determinismo de `CLAUDE.md`). En el
ciclo real de `project-specialization` F1 el orquestador se saltó `qa` por juicio propio y lo dejó
escrito en el ledger. Hacía falta **un dato** que las tres piezas lean igual, y decidir dónde vive.

## Decisión

El `planner`, cuando la iniciativa no tiene UI, escribe la clave `test-plan: n/a (sin UI)` en el
**frontmatter YAML de `improvement-plan.md`** (junto a `design:`), con espejo legible en la tabla de
cabecera del plan. `/dev-cycle` Fase 3 la lee antes de despachar `qa`; `qa` (y `coverage-check.py`)
con la clave presente termina limpio (exit 0, una línea en el informe: «sin UI por diseño»); sin
clave y sin `test-plan.md`, `qa` avisa **una vez** con el comando que lo fija y termina — nunca en
bucle. `qa-gate.py` no cambia de contrato. La iniciativa `plugin-refactor` es la primera que lleva
la clave (plan del 2026-09-10); la implementación en las tres piezas es su tarea **T-13** (C-08).

## Alternativas descartadas

- **La clave en el frontmatter de `tasks.md` (el ledger).** El ledger lo escribe y reescribe el
  `implementer` en cada tarea y lo parsea `ledger-lint`; meter ahí una decisión del `planner` mezcla
  dueños (ADR-011: un rol, un dueño) y arriesga que una edición del ledger la pierda. El plan es el
  artefacto que el `planner` posee y que `dev-cycle` ya lee para arrancar la Fase 3.
- **Un `test-plan.md` vacío o con «n/a» dentro.** Crea un fichero para decir que no hace falta;
  `coverage-check.py` y `qa` tendrían que distinguir «vacío» de «mal generado», y el índice del
  roadmap lo enlazaría como si existiera un plan de pruebas.
- **Dejarlo al criterio del orquestador (statu quo).** Es exactamente el hueco E1: una decisión de
  contrato entre piezas resuelta en prosa, sin dato que una puerta pueda leer.

## Consecuencias

Las tres piezas leen el mismo literal (`test-plan: n/a (sin UI)`) desde el mismo sitio, y la arista
E1 de la matriz de contratos (`docs/agents/CONTRACTS.md`, C-06) tiene un marcador y una puerta
(`coverage-check.py` exit 0 con la línea «declarado»). Se renuncia a que el ledger sea autocontenido
respecto al caso sin UI: quien lo lea debe mirar el frontmatter del plan (la tabla de cabecera del
ledger lo repite en una fila para que sea visible). Hasta que T-13 exista, la clave la lee una
persona; después la leen `dev-cycle` y `qa`.

## Estado

`propuesta` — a validar por la revisión de dos lentes del tramo R4 de `plugin-refactor` o por el
usuario en la puerta del plan. Pasa a `aceptada` cuando se valida; a `obsoleta` si una decisión
posterior la reemplaza (enlaza aquí a la que la sustituye, nunca se borra el rastro).
