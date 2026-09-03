---
id: LES-013
tipo: leccion
area: Proceso / desarrollo del plugin (roles y elección de pieza)
estado: aceptada (validada: revisión de dos lentes, 2026-09-03, intento 2)
fuente: 2026-09-03-superiority (T-03, T-06); doctrina de roles validada en 2026-09-03-roles-and-jira-flow (ADR-011, caso 3)
---

## plugin-dev

- **Los tests unitarios son una SKILL COMPARTIDA, no un agente: una capacidad que dos roles
  necesitan no justifica un rol nuevo.** Al abrir el hueco «no hay pirámide de pruebas ni gate de
  cobertura» la salida obvia era un agente `tester`. Habría sido un **rol duplicado**: `qa` ya
  decide el veredicto de pruebas (E2E con Playwright, `qa-gate.py`) y el `implementer` ya es el
  único que toca código y cierra fases. Un `tester` habría tenido que escribir código de test
  (frontera del implementer) y emitir veredicto de calidad (frontera de qa) — dos solapes, dos
  fuentes de verdad y una puerta más que negociar en cada fase.

  Se resolvió con la skill `unit-tests` (`scripts/coverage-gate.py`, 22 tests): **la capacidad se
  comparte, la decisión no se mueve.** El `implementer` la usa en P5 como gate opt-in
  (`.claude/dev.json` `tests.coberturaMinima`; exit 1 bajo el umbral es un gap de verificación
  como cualquier otro, exit 2 sin herramienta/stack degrada a aviso) y `qa` la usa **solo para
  informar** la capa unitaria junto a su % E2E, sin dar veredicto propio: el veredicto de esa fase
  sigue siendo de `qa-gate.py`. La frontera quedó escrita, no implícita: E2E → agente `qa`;
  unitarios/integración → skill compartida `unit-tests`, sin agente propio (fila en
  `docs/agents/ROLES.md`, caso 3 de `ADR-011`).

  Regla derivada para `plugin-dev`, antes de crear una pieza: si lo nuevo es un **cálculo o una
  técnica** que 2+ agentes invocan, es `skills/`; si es de uno solo, `agent-kits/<agente>/`; solo
  es **agente** cuando aporta un rol que **decide y escribe un artefacto propio** que hoy nadie
  decide. El síntoma de haber elegido mal es tener que repartir la misma responsabilidad entre dos
  piezas ("este escribe el test, aquel dice si vale"). Corolario medido en la misma iniciativa: las
  otras cuatro piezas de `superiority` salieron por el mismo árbol de decisión sin ningún agente
  nuevo — `/doctor` como **comando** (diagnóstico a demanda, sin artefacto), `changelog-sync` y
  `api-contract` como **skills**, y la Lente D de rendimiento como **lente más** de
  `adversarial-review` en vez de un revisor de rendimiento aparte. — *Fuente:*
  [`2026-09-03-superiority/tasks.md`](../../roadmap/2026-09-03-superiority/tasks.md) (T-03, T-06),
  [`skills/unit-tests/SKILL.md`](../../../skills/unit-tests/SKILL.md),
  [`adr/ADR-011`](../adr/ADR-011-un-rol-un-dueno-agentes-retirados-y-responsabilidades-fusionadas.md), [`docs/agents/ROLES.md`](../../agents/ROLES.md).
