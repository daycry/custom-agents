# PRD, plan y lienzo de revisión — C059–C061, C069, C071

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cinco definiciones completas: **42.966 bytes/1.362 líneas**. [commands-c3-prd-plan-reading-evidence.json](commands-c3-prd-plan-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

## Decisión común

La fuente mantiene **dos cadenas paralelas** para lo mismo: la actual
(`/plan-prd` → `.claude/prds/`, `/plan` → `.claude/plans/`) y la «legacy» PRP
(`/prp-prd` → `.claude/PRPs/prds/`, `/prp-plan` → `.claude/PRPs/plans/`), con
formatos distintos de PRD (tabla `Delivery Milestones` frente a `Implementation Phases`)
y lectura cruzada sin migrar (C061 l.49). En el plugin la cadena es una:
`analyst` → `spec.md`, `evaluator` → `evaluation.md`, `architect` → `design.md`
opcional, `planner` → `improvement-plan.md` + `tasks.md`, en una carpeta por iniciativa
enlazada (regla 7). Ninguno de los cinco justifica una pieza; dos ideas faltan en sus
dueños y ya estaban pendientes en [commands-workflow-comparison.md](commands-workflow-comparison.md):

| Fila pendiente | Qué aportan estos cuerpos | Línea propuesta |
|---|---|---|
| «Requisitos verificables» → `agents/analyst.md` | Evidencia de que el problema existe, o «supuesto — se validaría con {método}» (C060 l.50-54, C071 l.203-207) | `agents/analyst.md:68`, dimensión 1: «Pide la **evidencia** de que el problema existe (cita, ticket, métrica, alternativa que falla); si no la hay, anótalo en Supuestos como "supuesto — se validaría con <método>", nunca como hecho.» |
| «Plan por patrones reales» → `agents/planner.md` | Patrón existente a reflejar por categoría con `ruta:línea`, o ausencia declarada (C061 l.51-63, C069 l.97-135) | `agents/planner.md:86`, P2: «Por cada tarea que crea o cambia código, cita en su descripción el `fichero:línea` del patrón existente que debe reflejar (nombres, errores, acceso a datos, tests); si el repo no tiene equivalente, dilo así y no inventes uno. Solo la ruta, sin copiar el fragmento al plan (el brief no engorda, GOT-009).» |

`/dev-cycle` ya pide esos patrones en la Fase 0 (`commands/dev-cycle.md:30`), pero
la plantilla de `tasks.md` no tiene dónde dejarlos y `task-brief.py` no los recibe.

## C059 — plan-canvas

`1.810 bytes/45 líneas` · frontmatter: `description` y `argument-hint`. Entrada fina a
la skill `plan-canvas` (S205): abre el plan en el navegador, espera anotaciones o
veredicto, aplica cambios y repite hasta aprobar.

- **Artefactos y dueño propio:** edición del plan → `planner` (contenido); recibo de
  la decisión → `agent-kits/shared/plan-review.py` (estado en `.claude/plan-review`).
- **Despacho:** CLI `ecc-plan-canvas open|await|end`.
- **Escenario positivo:** «quiero revisar el plan en el navegador» → `/dev-cycle`
  Fase 2-b, revisión visual (`commands/dev-cycle.md:98-101`).
- **Escenario negativo:** «sigue con el plan» con el OK ya dado en la conversación →
  no se abre revisión ni se pide otro OK (`commands/dev-cycle.md:98-100`).

**Comparación.** Ya contrastada en [skills-product-canvas-flow-prompts.md](skills-product-canvas-flow-prompts.md)
(S205) y [panel-plan-review.md](panel-plan-review.md). Dos diferencias propias del
comando: sin argumento toma «el `.plan.md` modificado más recientemente» (l.17-18),
mientras el plugin exige la iniciativa exacta y prohíbe buscar la última
(`commands/dev-cycle.md:100-101`); y «approve» significa «empieza a implementar»
(l.26-27), cuando el recibo propio solo sustituye un OK que la puerta ya pedía.

**Destino:** **Sin destino**: ya integrado en `commands/dev-cycle.md` Fase 2-b.

## C060 — plan-prd

`5.380 bytes/162 líneas` · frontmatter: `description` y `argument-hint`. PRD breve en
cuatro puertas (encuadre, evidencia, hipótesis y alcance, generación) que se para
antes del «cómo»; escribe `.claude/prds/{nombre}.prd.md` y entrega a `/plan`.

- **Artefactos y dueño propio:** PRD → `analyst` (`spec.md` con la plantilla
  `agent-kits/evaluator/templates/spec.md`); tabla de hitos → cada hito es una
  iniciativa propia priorizada por `/pm-backlog`.
- **Despacho:** ninguno (en línea).
- **Escenario positivo:** «ayúdame a definir esto antes de presupuestar» → `analyst`
  (ofrecido por `/pm-cycle`, `commands/pm-cycle.md:29`).
- **Escenario negativo:** «divide esto en tareas» → `planner`, no `analyst`.

**Comparación.** Las ocho dimensiones de `analyst` (`agents/analyst.md:68-75`) cubren
problema, usuarios, alcance dentro/fuera, criterios, restricciones y supuestos; la
plantilla separa hechos del repo y restricciones por confirmar (`spec.md:112-122`,
D-099). Falta la evidencia del problema; la hipótesis «creemos que… lo sabremos
cuando…» es la dimensión 5 con cifra o incógnita. **Destino:** la línea de `analyst`.

## C061 — plan

`7.766 bytes/206 líneas` · frontmatter: `description` y `argument-hint`. Plan en línea
(sin subagente por defecto) con reformulación, riesgos, fases y espera de
confirmación; con un `.prd.md` escribe `.claude/plans/{nombre}.plan.md` y marca el hito
`in-progress` en el PRD.

- **Artefactos y dueño propio:** plan → `planner`; estado del hito → transiciones de
  `/dev-cycle` (`commands/dev-cycle.md:505-537`) y enlace `plan:` de la cadena.
- **Despacho:** en línea; agente `planner` solo si el usuario lo pide y existe (l.199-203).
- **Escenario positivo:** «haz un plan para esto» → `planner` (`/dev-cycle` Fase 2-b o `@planner`).
- **Escenario negativo:** «implementa esto ya, sin plan» → vía rápida o `quick-implement`.

**Comparación.** Mismo contrato que `planner` + puerta «OK del plan»
(`commands/dev-cycle.md:96`). El ejemplo estima «Backend 4-6 hours… Total 9-13 hours»
(l.168-172) sin método; `planner` P4 declara método y calibra. **Destino:** la línea de `planner`.

## C069 — prp-plan

`13.917 bytes/502 líneas` · frontmatter: `description` y `argument-hint`. Plan
«autocontenido»: ocho categorías de búsqueda, cinco trazas, investigación externa,
UX antes/después, alternativas, lectura obligatoria, fragmentos reales a imitar y
tareas con ACTION/IMPLEMENT/MIRROR/IMPORTS/GOTCHA/VALIDATE; escribe
`.claude/PRPs/plans/` y pasa la fase del PRD a `in-progress`.

- **Artefactos y dueño propio:** plan y tareas → `planner`; alternativas → `architect`
  (`design.md`); investigación externa → `research-first`; UX y E2E → `test-plan.md`.
- **Despacho:** ninguno (en línea, con búsqueda web en la fase 3).
- **Escenario positivo:** «planifica esta fase con todo lo necesario para implementarla de una pasada» → `planner`.
- **Escenario negativo:** «compara enfoques antes de planificar» → `architect`, no `planner`.

**Comparación.** `VALIDATE` + `EXPECT` es la `Verificación` obligatoria
(`comando → resultado esperado`) de `planner` P3; «Mandatory Reading» lo cubre
`task-brief.py` con los ficheros que referencia la tarea; `GOTCHA` lo cubre la lectura de
`docs/knowledge/gotchas/` por el implementer. Defectos:

| Defecto | Cita |
|---|---|
| Valla de código rota: la plantilla abre con cuatro comillas y cierra con tres | l.217 y l.420; «Output», «Verification» y «Next Steps» (l.424-501) quedan dentro del bloque de la plantilla hasta l.502 |
| Copiar fragmentos de código al plan «para no buscar después» | l.14 y l.269-295: copia que envejece y brief que engorda (GOT-009) |
| Las alternativas las decide el propio planificador | l.199-202; en el plugin la opción la fija el usuario en la doble pasada de `architect` |
| «Confidence Score 1-10» sin método | l.452 |

**Destino:** la línea de `planner` (compartida con C061); lo demás, **sin destino**.

## C071 — prp-prd

`14.093 bytes/447 líneas` · frontmatter: `description` y `argument-hint`. PRD
interactivo: tres rondas de preguntas, investigación de mercado y de viabilidad técnica
con `fichero:línea`, MoSCoW, enfoque técnico, fases de implementación con columnas de
paralelismo y dependencia, y registro de decisiones; escribe `.claude/PRPs/prds/`.

- **Artefactos y dueño propio:** problema, usuarios y alcance → `analyst`; viabilidad,
  complejidad y riesgos → `evaluator`; enfoque técnico → `architect`; fases y
  dependencias → `planner` (campo `Dependencias` del ledger).
- **Despacho:** ninguno declarado; «investigaciones en paralelo» sin agente nombrado.
- **Escenario positivo:** «no sé bien lo que necesito, ayúdame a definirlo» → `analyst`
  (con `research-first` a demanda, `agents/analyst.md:130-135`).
- **Escenario negativo:** «¿cuánto costaría y es viable?» → `evaluator`, no `analyst`.

**Comparación.** El PRD invade tres fases con dueño (enfoque técnico l.275-287, fases
l.291-324), justo lo que C060 retiró después con «NO_IMPLEMENTATION_DETAIL» (C060
l.160). La investigación de mercado «busca en la web» (l.77-84) sin canales ni
límites; `research-first` los declara. «Feasibility HIGH/MEDIUM/LOW» sin método.
**Destino:** la línea de `analyst` (compartida con C060); lo demás, **sin destino**.
