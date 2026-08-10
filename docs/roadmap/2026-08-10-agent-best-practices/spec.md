---
spec: agent-best-practices
descripcion: Adoptar en el plugin las estrategias contrastadas de las colecciones top de agentes (model tiering, tools mínimos, DoD verificable, revisión adversarial, descriptions de enrutado, DRY)
estado: aprobada          # borrador | aprobada | implementada | obsoleta
creado: 2026-08-10
actualizado: 2026-08-10
evaluacion: evaluation.md # ruta a la evaluación cuando exista
plan: improvement-plan.md # ruta al plan cuando exista
---

# Mejores prácticas de agentes top aplicadas al plugin

> **Evaluación:** [`evaluation.md`](evaluation.md) (2026-08-10 · 19,8 h · ~1.023 €)
> **Plan de implementación:** [`improvement-plan.md`](improvement-plan.md) (2026-08-10 · 20,7 h · ~1.069 € · 11 tareas) + [`tasks.md`](tasks.md)

> **Terminología:** «model tiering» = asignar a cada agente el modelo (haiku/sonnet/opus/inherit) proporcional a la complejidad de su tarea. «DoD» = definition of done, checklist de cierre. «Description de enrutado» = el campo `description` del frontmatter que Claude Code usa para auto-delegar.

## Contexto y objetivo

Análisis comparativo (2026-08-10) del plugin frente a las referencias del estado del arte: wshobson/agents (model tiering en 75 agentes), VoltAgent/awesome-claude-code-subagents (checklists de verificación), obra/superpowers (evidence over claims, revisión en dos etapas) y las best practices oficiales de Claude Code (verificación ejecutable, tools mínimos, revisor con contexto fresco). El plugin ya está al nivel top en orquestación (puertas go/no-go, máquina de estados, guardrails por script, plantillas externalizadas); esta iniciativa incorpora las seis estrategias que faltan y dos arreglos puntuales detectados durante el análisis. Fuente: informe [`analysis.md`](analysis.md) (sesión Cowork 2026-08-10).

## Decisiones de diseño

| Decisión | Elección | Motivo |
|---|---|---|
| Asignación de modelo | **Campo `model` en frontmatter de los 8 agentes** | Criterio wshobson: haiku=mecánico, sonnet=desarrollo estándar, opus=análisis crítico; una línea por fichero, sin riesgo funcional |
| Restricción de herramientas | **Recortar `tools` al mínimo real por agente** | La restricción mecánica (toolset) no se diluye con el contexto; la semántica ("no toques el código") sí |
| DoD | **Sección final `## ANTES DE CERRAR (DoD)` con 3-5 comprobaciones ejecutables + evidencia** | Principio "evidence over claims" (superpowers) y best practice oficial nº 1 |
| Revisión adversarial | **Paso en `/dev-cycle` (subagente genérico con contexto fresco), NO agente nuevo** | Más barato, no engorda el plugin; revisa diff contra plan/tasks (gaps, no estilo) |
| Duplicados | **Extraer a `agent-kits/shared/` con la resolución `find` ya existente** | Misma convención que el resto de kits (CONVENTIONS regla 5); una fuente de verdad |
| Linter de plugin | **Script en CI que valida frontmatter, grafo `dependencies` y patrón de triggers** | Ya existe CI y `release.py`; evita deriva doc↔realidad |

## Configuración / parámetros

| Parámetro | Clave / mecanismo | Default | Valor objetivo |
|---|---|---|---|
| Modelo pdfy | frontmatter `model` | (hereda) | **haiku** |
| Modelo documenter, qa, implementer, analyst, planner | frontmatter `model` | (hereda) | **sonnet** |
| Modelo evaluator, nemesis | frontmatter `model` | (hereda) | **opus** (o `inherit` si el coste preocupa) |
| Umbral «verde» de qa | `results.json` | implícito | **0 failed, 0 flaky sin justificar (explícito en prompt)** |

## Arquitectura y componentes

Se tocan: `agents/*.md` (8 ficheros: model, tools, descriptions, DoD), `commands/dev-cycle.md` (paso de revisión adversarial entre implementación y qa), `agent-kits/shared/` (nuevo: estimation-defaults.md, confluence-optin.md), `docs/CONVENTIONS.md` (única fuente de la tabla de estados), `.github/workflows` + `scripts/` (linter). Se reutiliza: resolución de rutas por `find`, CI existente, `release.py`, ejemplo `docs/examples/ci4-forms-emails/` como referencia de salida citada por evaluator/planner.

## Características (alcance detallado)

| ID | Característica | Detalle |
|----|---------------|---------|
| C-01 | Model tiering | Añadir `model` a los 8 agentes según tabla de parámetros |
| C-02 | Arreglos puntuales | planner.md: renumerar doble «P7» (líneas 85/87) y P8→P9; nemesis.md: eliminar/inlinear referencias «§6, §11, §14, §17» a un system base que no viaja con el plugin |
| C-03 | Descriptions de enrutado | Reescribir evaluator, planner y nemesis al patrón «qué hace + Úsalo cuando el usuario diga…»; mover rutas/plantillas al cuerpo; nemesis con «PROACTIVAMENTE cuando se mencione seguridad» |
| C-04 | Tools mínimos | Revisar agente a agente y recortar al mínimo real. **Reajustado en implementación:** el único que puede prescindir de `Edit` es `pdfy`; evaluator/planner/analyst/qa/documenter/nemesis patchean back-links y estados en `.md` existentes, así que conservan `Edit` con la restricción "solo `.md` bajo docs/, nunca código" documentada en cada frontmatter (el toolset no distingue editar-.md de editar-código; la garantía se queda semántica salvo pdfy) |
| C-05 | DoD verificable | Sección `## ANTES DE CERRAR (DoD)` en los 8 agentes con comprobaciones ejecutables y obligación de mostrar evidencia; umbral verde explícito en qa |
| C-06 | DRY / agent-kits/shared | Extraer tabla de estimación (duplicada evaluator§1/planner§1), párrafo Confluence opt-in (×4) y tabla de estados (×3, queda solo en CONVENTIONS) |
| C-07 | Revisión adversarial en /dev-cycle | Nuevo paso entre Fase 3 y qa: subagente fresco revisa diff contra improvement-plan.md/tasks.md; reporta gaps de corrección/requisitos, no preferencias |
| C-08 | Linter de plugin en CI | Script (python, junto a los tests existentes) que valida: `model` presente, tools declarados válidos, description con frases-gatillo, `dependencies` apuntando a agentes/skills/kits existentes, sin ciclos |

## Alcance

- **Dentro (esta iteración):**
  - C-01 … C-08 tal como se describen arriba.
- **Fuera (siguientes specs):**
  - TDD estricto RED-GREEN-REFACTOR (metodología del proyecto usuario, no del plugin; `/dev-cycle` ya delega en superpowers).
  - «Communication protocol» JSON estilo VoltAgent (cubierto por las secciones ENTRADA/SALIDA — INVARIANTE).
  - Few-shot largos inline (los suple `docs/examples/ci4-forms-emails/`; solo se añade la cita en evaluator/planner dentro de C-06).
  - Agente `reviewer` dedicado (se decidió paso de command, no agente).

## Manejo de errores

| Caso | Comportamiento |
|---|---|
| Instalación existente con agentes en uso | Cambios retrocompatibles: `model`/`tools` no rompen invocaciones; descriptions mantienen el nombre |
| Linter falla en CI sobre contribución externa | Falla el check con mensaje que indica campo y patrón esperado; no bloquea instalación de versiones ya publicadas |
| Revisión adversarial reporta gaps de estilo | El prompt del paso instruye «gaps de corrección o requisitos, no preferencias»; los de estilo se descartan (advertencia de sobre-ingeniería de la doc oficial) |

## Pruebas

- Linter (C-08) pasa en verde sobre el propio repo tras aplicar C-01…C-06 (autovalidación).
- Test unitario del linter con fixtures (agente sin `model`, dependencia inexistente, description sin triggers) — junto a `tests/test_dashboard.py` y `test_worklog.py`.
- Prueba manual de `/dev-cycle` sobre una iniciativa de juguete verificando que el paso de revisión adversarial se ejecuta y reporta contra el plan.
- Verificación de auto-delegación: con las nuevas descriptions, pedir «presupuesta esto» / «haz una auditoría de seguridad» sin nombrar agente y comprobar el enrutado.

## Referencias

- Informe comparativo [`analysis.md`](analysis.md) (2026-08-10) — origen de todos los requisitos.
- Best practices oficiales: https://code.claude.com/docs/en/best-practices (verificación, subagente revisor, tools mínimos).
- wshobson/agents — model tiering y orquestación: https://github.com/wshobson/agents
- VoltAgent cpp-pro — checklists de verificación: https://github.com/VoltAgent/awesome-claude-code-subagents/blob/main/categories/02-language-specialists/cpp-pro.md
- obra/superpowers — evidence over claims, revisión dos etapas: https://github.com/obra/superpowers
- planner.md líneas 85/87 (doble P7), verificado 2026-08-10.

## Decisiones confirmadas (revisión del usuario · 2026-08-10)

1. Materializar las mejoras como iniciativa del roadmap (spec + evaluación) en vez de implementarlas directamente. **Confirmado.**
2. Alcance = 6 estrategias + arreglos puntuales + linter, según el informe comparativo. **Confirmado.**

## Supuestos

- Los valores de `model` disponibles siguen siendo haiku/sonnet/opus/inherit; si el marketplace introduce tiers nuevos, la tabla de parámetros se revisa.
- No existe `.claude/rates.json` en el repo del plugin; la evaluación usará los defaults del evaluator (50 €/h, supervisión ~25 %, margen +20 %).
- El orden de ejecución recomendado (quick wins C-01/C-02/C-03 → C-04/C-05/C-06 → C-07/C-08) se decidirá formalmente en la evaluación/plan.
