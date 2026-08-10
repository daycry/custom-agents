---
spec: qa-strict
descripcion: Endurecer qa y el orquestador /dev-cycle con puertas deterministas (qa-gate, ledger-lint), Playwright estricto, cobertura criterios↔tests, bucle acotado de corrección y revisión de dos lentes
estado: aprobada          # borrador | aprobada | implementada | obsoleta
creado: 2026-08-10
actualizado: 2026-08-10
evaluacion: evaluation.md # ruta a la evaluación cuando exista
plan: improvement-plan.md # ruta al plan cuando exista
---

# qa estricto y orquestador endurecido (puertas deterministas)

> **Evaluación:** [`evaluation.md`](evaluation.md) (2026-08-10 · 22,8 h · ~1.174 € · veredicto: go)
> **Plan de implementación:** [`improvement-plan.md`](improvement-plan.md) + [`tasks.md`](tasks.md) (2026-08-10 · 23,4 h · ~1.205 € · 8 tareas)

> **Terminología:** «puerta determinista» = veredicto calculado por un script con exit code (patrón `lib-guardrail.sh`), no por juicio del LLM. «flaky» = test que falla y pasa al reintentar. «lente» = perspectiva de revisión de un subagente (conformidad con spec vs. calidad de código).

## Contexto y objetivo

Segunda iteración sobre la iniciativa `2026-08-10-agent-best-practices`: aquélla hizo la DoD **explícita** (el prompt de qa ya define «verde = 0 failed, 0 flaky sin justificar»); ésta la hace **mecánica**. Hoy el veredicto de qa, la coherencia del ledger `tasks.md` y el bucle de corrección qa→implementer dependen de que el LLM siga la prosa. El objetivo es mover esas tres decisiones a scripts con exit code y a reglas de workflow acotadas, siguiendo el patrón que el plugin ya usa con éxito (`lib-guardrail.sh`, `worklog.py`): lo innegociable se impone con código determinista; el LLM interpreta y comunica. Referencias: best practices oficiales (Stop-hook/gate determinista, «give Claude a check it can run»), superpowers (two-stage review, verification-before-completion).

## Decisiones de diseño

| Decisión | Elección | Motivo |
|---|---|---|
| Veredicto de qa | **Script `qa-gate.py` (kit qa) con exit code** | El verde/rojo deja de ser opinable; mismo patrón que guardrail/worklog |
| Flaky | **`retries: 2` en Playwright; flaky = pasa al reintento → NO verde salvo justificación en el informe** | Detecta inestabilidad sin falsos rojos; la justificación queda escrita |
| Validación del ledger | **Script `ledger-lint.py` en `agent-kits/shared/`** | Lo consumen implementer, qa y /dev-cycle; una sola implementación |
| Hook sobre tasks.md | **PostToolUse → ledger-lint en modo AVISO (no bloqueo)** | Validación que ocurre siempre; bloquear rompería flujos legítimos a medio editar |
| Bucle qa→implementer | **Acotado: máx. 3 intentos, luego parar y preguntar al usuario** | Evita bucle infinito y evita «lo doy por bueno»; el humano decide en el corte |
| Revisión adversarial | **Dos lentes en paralelo (conformidad con spec · calidad/robustez)** | Diversidad de perspectiva caza fallos que la redundancia no; patrón superpowers |
| Bloques API/A11Y | **Opt-in en test-plan (`API-xx` con curl, `A11Y-xx` con axe-core)** | Amplía cobertura sin imponer dependencias a quien no las quiera |

## Configuración / parámetros

| Parámetro | Clave / mecanismo | Default | Valor objetivo |
|---|---|---|---|
| Reintentos Playwright | `playwright.config.mjs` `retries` | 0 | **2** |
| Traza en fallo | `trace` | off | **retain-on-failure** |
| `test.only` accidental | `forbidOnly` | false | **true** |
| Timeout por test | `timeout` | 30 s | **30 s explícito** (configurable) |
| Máx. intentos bucle qa→implementer | regla de /dev-cycle | ∞ (implícito) | **3** |
| Umbral qa-gate | `qa-gate.py` | — | **exit 0 ⟺ 0 failed y 0 flaky-sin-justificar** |
| Modo del hook ledger-lint | `hooks.json` | — | **aviso** (exit 0 siempre; imprime problemas) |

## Arquitectura y componentes

Se tocan: `agent-kits/qa/` (nuevo `qa-gate.py`; `runner/playwright.config.mjs` endurecido), `agent-kits/shared/` (nuevo `ledger-lint.py`), `agents/qa.md` (DoD pasa a invocar qa-gate; puerta de cobertura; bloques API/A11Y), `agents/implementer.md` (DoD invoca ledger-lint), `commands/dev-cycle.md` (bucle acotado + doble lente), `hooks/hooks.json` (+ script del hook), `agent-kits/planner/templates/test-plan.md` (bloques opcionales API-xx/A11Y-xx), `tests/` (tests de qa-gate y ledger-lint), `.github/workflows/ci.yml` (correr los tests nuevos). Se reutiliza: patrón guardrail-por-script, kit shared creado en la iniciativa anterior, resolución `find`, CI y linter existentes.

## Características (alcance detallado)

| ID | Característica | Detalle |
|----|---------------|---------|
| C-01 | `qa-gate.py` — veredicto determinista | Script en `agent-kits/qa/`: parsea `results.json` de Playwright, cuenta passed/failed/flaky/skipped, aplica el umbral (0 failed, 0 flaky sin justificar — las justificaciones se pasan por argumento/fichero) y devuelve exit 0/1 + resumen JSON por stdout. qa lo invoca en su DoD y pega la salida como evidencia; /dev-cycle usa su exit code como puerta |
| C-02 | Playwright estricto | `runner/playwright.config.mjs`: `retries: 2`, `forbidOnly: true`, `trace: 'retain-on-failure'`, timeout explícito, reporter JSON garantizado. Flaky queda identificado en `results.json` para que C-01 lo evalúe |
| C-03 | Puerta de cobertura criterios↔tests | qa valida antes de ejecutar: cada criterio de aceptación de las tareas de UI de `tasks.md` debe estar cubierto por un `E2E-xx` o `M-xx` (campo «Cubre (tests)» del planner). Criterios huérfanos → se listan en `report.md` y el estado global NO puede ser verde (van a manual como mínimo). Comprobación en `qa-gate.py` o script auxiliar del kit |
| C-04 | `ledger-lint.py` — validación mecánica del ledger | Script en `agent-kits/shared/`: valida `tasks.md` — vocabulario de estados permitido, coherencia checkbox↔estado (tarea `completado` ⟹ criterios `[x]`), tabla de resumen coherente con las tareas (contadores por fase), IDs `T-XX` únicos. Exit 0/1 + informe. Lo invocan implementer (DoD), qa (P1) y /dev-cycle (en cada puerta) |
| C-05 | Hook PostToolUse sobre `tasks.md` | Nueva entrada en `hooks/hooks.json` (matcher Write|Edit sobre `*/tasks.md`) que ejecuta `ledger-lint.py` en modo aviso: imprime los problemas sin bloquear. Determinista: ocurre siempre, sin depender del prompt |
| C-06 | /dev-cycle: bucle acotado + doble lente | (a) Bucle qa→implementer con contador explícito: máx. 3 intentos; al 3.º rojo, parar, resumir los fallos persistentes y preguntar al usuario. (b) La revisión adversarial pasa a **dos subagentes en paralelo** con lentes distintas: conformidad con spec/plan y calidad/robustez del código; se fusionan los gaps (dedupe) y se aplica la misma puerta manual. Ambas cosas solo en Modo B (superpowers trae las suyas) |
| C-07 | Bloques `API-xx` / `A11Y-xx` (opt-in) | Plantilla `test-plan.md` con secciones opcionales: `API-xx` (smoke de endpoints con curl: método, URL relativa, status esperado, aserción simple sobre el body) y `A11Y-xx` (axe-core vía Playwright sobre páginas clave). qa los ejecuta solo si el test-plan los trae; la instalación de axe-core sigue la regla de opt-in de Playwright |

## Alcance

- **Dentro (esta iteración):**
  - C-01 … C-07 tal como se describen arriba.
- **Fuera (siguientes specs):**
  - TDD estricto en implementer (RED-GREEN-REFACTOR obligatorio) — sigue siendo metodología del proyecto usuario; /dev-cycle ya delega en superpowers si está.
  - Regresión visual (diff de screenshots) — requiere baseline management; se valorará cuando C-02 lleve rodaje.
  - Lighthouse/performance budgets.
  - Hook en modo bloqueo (Stop-hook duro) — primero rodar el modo aviso.
  - Navegadores más allá de Chromium.

## Manejo de errores

| Caso | Comportamiento |
|---|---|
| `results.json` ausente o malformado | `qa-gate.py` exit 1 con motivo «sin resultados»: la ausencia de evidencia es rojo, no verde |
| Justificación de flaky sin detalle | El gate exige texto no vacío por test justificado; «es flaky» a secas no cuenta |
| `tasks.md` con formato legacy (planes anteriores) | `ledger-lint.py` degrada a avisos lo no crítico (formato) y reserva exit 1 para incoherencias duras (estado inválido, completado sin criterios marcados) |
| Hook sin python disponible | El script del hook comprueba `command -v python3` y sale 0 en silencio (el hook nunca rompe la edición) |
| 3.er intento rojo en el bucle | /dev-cycle NO cierra estados, resume los fallos persistentes y espera decisión del usuario (continuar, re-planificar o cancelar) |
| Proyecto sin tareas de UI | La puerta de cobertura no aplica (no hay test-plan); qa lo declara y no bloquea |

## Pruebas

- `tests/test_qa_gate.py`: fixtures de `results.json` (todo verde; con failed; con flaky justificado/no justificado; malformado; ausente) → exit code y resumen esperados.
- `tests/test_ledger_lint.py`: fixtures de `tasks.md` (coherente; estado inválido; completado con criterios sin marcar; resumen descuadrado; IDs duplicados) → exit y mensajes.
- CI ejecuta ambos junto a los tests existentes; `lint_plugin.py` sigue en verde tras los cambios de frontmatter/hooks.
- Prueba manual: /dev-cycle sobre iniciativa de juguete verificando bucle acotado (simular 3 rojos) y doble lente.

## Referencias

- Iniciativa previa: [`../2026-08-10-agent-best-practices/`](../2026-08-10-agent-best-practices/) (DoD explícita, revisión adversarial simple, agent-kits/shared, linter).
- Best practices oficiales — gates deterministas y verificación: https://code.claude.com/docs/en/best-practices
- obra/superpowers — two-stage review, verification-before-completion: https://github.com/obra/superpowers
- Patrón interno: `agent-kits/qa/lib-guardrail.sh`, `skills/jira-sync/scripts/worklog.py` (aritmética fuera de la prosa).

## Decisiones confirmadas (revisión del usuario · 2026-08-10)

1. Mejorar qa y orquestador vía **nueva iniciativa** del roadmap (spec + evaluación antes de implementar). **Confirmado.**
2. Alcance = puertas deterministas + workflow endurecido + bloques opt-in, según propuesta discutida en sesión. **Confirmado.**

## Supuestos

- El `results.json` del reporter JSON de Playwright identifica los reintentos (status `flaky`) — verificado en la doc de Playwright para el reporter `json`; si la versión del runner difiere, C-01 se adapta al esquema real.
- `axe-core/playwright` es instalable con el mismo flujo opt-in que Chromium; si no, `A11Y-xx` se degrada a checklist manual.
- El hook PostToolUse recibe la ruta del fichero editado (variable de entorno estándar de hooks de Claude Code) para filtrar `tasks.md`.
- No hay `.claude/rates.json` en el repo; la evaluación usa el fragmento compartido `agent-kits/shared/estimation-defaults.md` (creado en la iniciativa anterior).
