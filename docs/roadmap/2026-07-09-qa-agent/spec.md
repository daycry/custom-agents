---
spec: qa-agent
descripcion: Nuevo agente qa que audita un plan ejecutando tests E2E con Playwright contra la app local, captura screenshots y genera un informe md+pdf (con checklist manual para el humano) en docs/roadmap/<slug>/testing/. Incluye extender planner para generar un test-plan.md por plan.
estado: aprobada
creado: 2026-07-09
actualizado: 2026-07-09
evaluacion: evaluation.md
plan: improvement-plan.md
---

# Agente `qa`: E2E con Playwright + informe de auditoría del plan

> Evaluación: [`evaluation.md`](evaluation.md)
> Plan de implementación: [`improvement-plan.md`](improvement-plan.md)

## Contexto y objetivo

Los planes que genera `planner` definen **qué** hay que construir y sus criterios de aceptación, pero no hay una pieza que **verifique la UI de punta a punta**. Se quiere un agente **`qa`** que, dado un plan, ejecute sus **tests E2E con Playwright** contra la app en local, capture **evidencias (screenshots)**, y entregue un **informe md + pdf** con el resultado y una **checklist manual** para lo que no se automatiza.

Es el equivalente funcional de `nemesis` pero para **QA/UI**: audita contra un plan y produce un informe con evidencias.

## Decisiones de diseño

| Decisión | Elección | Motivo |
|---|---|---|
| Motor E2E | **Playwright** (Node) | Estándar E2E, multinavegador, screenshots/trazas nativas. |
| Definición de tests | **`test-plan.md` por plan** + etiquetas de trazabilidad por tarea | Los E2E son flujos que cruzan varias tareas; definirlos por tarea duplica. Cada tarea UI referencia su escenario (p. ej. "cubierta por E2E-02"). |
| Quién define los tests | **`planner`** los redacta en `test-plan.md` al crear el plan | Conoce los criterios de aceptación y el alcance. |
| Quién los ejecuta | **`qa`** ejecuta los automáticos y guía los manuales | Separación clara: definir (planner) vs. ejecutar/auditar (qa). |
| Automáticos vs. manuales | Dos bloques en `test-plan.md`: **E2E-xx** (IA/Playwright) y **M-xx** (humano) | El humano recibe una lista exacta de lo que debe comprobar (visual/UX, email real, captcha, pagos, accesibilidad, multidispositivo). |
| PDF del informe | Reutiliza la skill compartida **`to-pdf`** | No se reinventa; mismo tema moderno. |
| Guardrail | E2E **solo contra hosts locales/privados** | Misma filosofía que `nemesis`; no se apunta a terceros. |
| Instalación | Playwright + navegadores en `~/.claude/tool-cache/qa/`, **opt-in** | Descarga pesada de navegadores; permiso previo, como `nemesis`/`pdfy`. |
| Salida | `docs/roadmap/<fecha>-<slug>/testing/` | Cuelga del plan que audita. |

## Arquitectura y componentes

- **Agente** `agents/qa.md` — orquestador: localiza el plan y su `test-plan.md`, confirma la URL local, ejecuta los E2E, recoge resultados y evidencias, genera el informe y deja la checklist manual.
- **Kit** `agent-kits/qa/`:
  - `runner/` — proyecto Playwright base (config, runner que lee los escenarios `E2E-xx` y produce resultados JSON + screenshots + trazas).
  - `templates/report.md` — plantilla del informe de QA.
  - `lib-guardrail` — gate local-only para la URL objetivo (reutiliza el patrón de `nemesis`).
- **Reutiliza** la skill `to-pdf` para `report.pdf`.
- **Extensión de `planner`**: nueva plantilla `agent-kits/planner/templates/test-plan.md` y paso en el flujo para generarla; etiqueta de trazabilidad por tarea en `tasks.md` (campo "Cubre: E2E-xx / M-xx").

### `test-plan.md` (por plan, generado por `planner`)
- **Automáticos (E2E-xx):** por escenario → nombre, precondiciones, pasos, aserciones, tareas cubiertas, capturas esperadas.
- **Manuales (M-xx):** por ítem → qué revisar, por qué no se automatiza, criterio de aceptación, tareas cubiertas.
- **Cobertura:** mapa tarea → escenarios que la cubren.

### `testing/` (salida de `qa`)
```
docs/roadmap/<fecha>-<slug>/testing/
├── report.md              # informe de QA (resultado + evidencias + checklist manual)
├── report.pdf             # mismo informe vía to-pdf
├── screenshots/           # capturas por escenario/paso
└── raw/                   # resultados JSON + trazas de Playwright
```

## Flujo

1. **Recepción:** el usuario invoca `qa` sobre un plan (`docs/roadmap/<slug>/`). qa lee `improvement-plan.md`, `tasks.md` y `test-plan.md`. Confirma la **URL local** de la app en ejecución.
2. **Preparar Playwright:** localiza/instala el runner en `~/.claude/tool-cache/qa/` (opt-in; avisa de la descarga de navegadores). Verifica que la URL objetivo es local/privada (guardrail).
3. **Ejecutar automáticos (E2E-xx):** corre cada escenario, captura screenshots en los puntos clave y trazas; recoge pass/fail y errores.
4. **Informe:** genera `testing/report.md` con: resumen (X/Y pasan), resultado por escenario (pasos, aserciones, capturas embebidas, error si falla), **checklist manual (M-xx)** pendiente para el humano, y trazabilidad tarea→resultado. Genera `report.pdf` con `to-pdf`.
5. **Cierre:** resume al usuario (verde/rojo, nº de fallos, ruta del informe) y recuerda los tests manuales pendientes.

## Alcance

- **Dentro:**
  - Agente `qa` + kit con runner Playwright, guardrail local y capturas.
  - Ejecución de escenarios `E2E-xx` definidos en `test-plan.md`.
  - Informe `report.md` + `report.pdf` (vía `to-pdf`) con evidencias y checklist manual.
  - Plantilla `test-plan.md` y su generación por `planner` + etiquetas de trazabilidad por tarea.
  - Salida en `docs/roadmap/<slug>/testing/`.
- **Fuera (siguientes specs):**
  - Ejecución en CI/pipeline y matrices de navegadores/dispositivos.
  - Tests de rendimiento/carga y de accesibilidad automatizada (axe).
  - Datos de prueba/fixtures complejos y estado de BD.
  - Integración con gestores de test (TestRail, Xray).

## Manejo de errores

| Caso | Comportamiento |
|---|---|
| URL objetivo no local/privada | El guardrail la rechaza; no se ejecuta nada. |
| App no responde en la URL | Se aborta con mensaje claro (levanta la app primero). |
| Playwright/navegadores no instalados | Pide permiso e instala; si se declina, no ejecuta automáticos y lo declara. |
| Escenario E2E falla | Se marca fail, se guardan captura + traza + error; el resto sigue. |
| Plan sin `test-plan.md` | Avisa: hay que (re)generar el plan con `planner` para tener los escenarios. |

## Pruebas (de la propia feature)

- Sobre un plan de ejemplo con app local trivial: qa ejecuta un `E2E-01` que pasa y otro que falla; el `report.md` refleja ambos con sus capturas, y `report.pdf` se genera.
- URL no local → rechazada por el guardrail.
- Sin Playwright instalado y declinando la instalación → informe declara automáticos no ejecutados y mantiene la checklist manual.

## Referencias

- Playwright (test runner, `page.screenshot`, trazas).
- Skill `to-pdf` (`skills/to-pdf/`) para el PDF.
- `agents/nemesis.md` y `agent-kits/nemesis/tools/lib-guardrail.sh` (patrón de guardrail local e instalación opt-in).
- `agent-kits/planner/templates/` (donde vivirá `test-plan.md`).

## Decisiones confirmadas (revisión del usuario · 2026-07-09)

1. Definición de tests **por plan** (`test-plan.md`) con etiquetas de trazabilidad por tarea. **Confirmado.**
2. Separación **automáticos (IA) / manuales (humano)**. **Confirmado.**
3. Salida en `docs/roadmap/<slug>/testing/`. **Confirmado.**
4. Arranque **spec + evaluación primero** (dogfooding). **Confirmado.**

## Supuestos

- (a) La app a testear corre en **local** y el usuario facilita su URL.
- (b) Playwright descarga navegadores en el primer uso (red + espacio en disco), bajo permiso.
- (c) `to-pdf` está disponible (skill del bundle) para el PDF.
- (d) El plan auditado se generó con `planner` e incluye `test-plan.md`.
