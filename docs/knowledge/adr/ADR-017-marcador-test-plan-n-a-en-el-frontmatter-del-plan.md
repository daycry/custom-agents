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
con la clave presente termina limpio (exit 0, una línea **ℹ️** en el informe: «sin UI por diseño»,
nunca un ✅ — no se ha comprobado cobertura, se ha aceptado una declaración); sin clave y sin
`test-plan.md`, `qa` avisa **una vez** con el comando que lo fija y termina — nunca en bucle.

**Qué exime exactamente el marcador** (precisión añadida el 2026-09-11 tras la revisión del tramo
R4a, que validó la desviación 18 de T-13):

- **Exime** la ausencia de `test-plan.md` y, con ella, los criterios **`[GWT]`** de la `spec.md`:
  sin UI no hay E2E que los cubra, así que dejan de forzar exit 1. Es una inversión de precedencia
  respecto a la regla vieja, que disparaba el error de `[GWT]` ANTES de mirar el marcador y
  confundía «formato Given/When/Then» con «necesita interfaz».
- **No exime** nada más: con `test-plan.md` presente, la puerta corre entera (referencias rotas y
  `[GWT]` sin cubrir siguen siendo exit 1), y SIN el marcador un `[GWT]` sin test-plan sigue siendo
  exit 1, con un error por criterio y sus IDs impresos. El marcador tampoco vale citado en la prosa
  del plan, anidado bajo otra clave, ni con texto detrás: es una clave de primer nivel del
  frontmatter, con el literal exacto (entrecomillarlo sí vale: es YAML equivalente).
- **Se lista siempre lo eximido**, para que la revisión pueda cazar un marcador puesto para
  esquivar la puerta: los criterios `[GWT]` si los hay; si no, los criterios `CA-XX` de la spec; si
  no, las tareas del ledger; y si no hay nada que listar, la salida lo dice con esas palabras. La
  evidencia de lo eximido es el campo `Verificación` de la tarea que lo cierra en `tasks.md`.
  Además, si el **diff** (misma base que `scope-check.py`) o el alcance declarado (`Archivos`) tocan
  rutas con pinta de interfaz, sale un ⚠️ que dice de cuál de las dos fuentes salió cada ruta; sin
  git, se degrada al alcance declarado diciéndolo (mirar solo `Archivos` dejaba ciego el caso del
  `.tsx` excluido por `alcance.excluir`, que está en el diff y no en el ledger). También lo dice
  cuando la base del diff no aporta ficheros —`HEAD` en la rama principal—: «no he mirado el diff»
  no es «he mirado y no hay interfaz».

`qa-gate.py` no cambia de contrato. La iniciativa `plugin-refactor` es la primera que lleva
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
(`coverage-check.py` exit 0 con la línea «declarado»). El precio de eximir a los `[GWT]` es que una
iniciativa CON interfaz que declare el marcador por error se salta la cobertura: se acepta porque la
declaración es explícita, queda en el frontmatter del plan (versionado), lo eximido se imprime
enumerado y el ⚠️ de rutas con pinta de interfaz lo señala; la alternativa —seguir fallando por
`[GWT]` con el marcador puesto— dejaba el hueco E1 abierto para cualquier spec que usara el formato
Given/When/Then, que es el formato recomendado. Se renuncia a que el ledger sea autocontenido
respecto al caso sin UI: quien lo lea debe mirar el frontmatter del plan (la tabla de cabecera del
ledger lo repite en una fila para que sea visible). Hasta que T-13 exista, la clave la lee una
persona; después la leen `dev-cycle` y `qa`.

## Estado

`propuesta` — la Lente A del **intento 1 del tramo R4a** (2026-09-11) validó la inversión de
precedencia con la evidencia reproducida y pidió que se escribiera aquí (gap R4a-6); esta corrección
lo escribe, pero **no promueve el ADR**: la promoción a `aceptada` la hace el orquestador al cerrar
el tramo sin gaps pendientes. Pasa a `obsoleta` si una decisión posterior la reemplaza (enlaza aquí
a la que la sustituye, nunca se borra el rastro).
