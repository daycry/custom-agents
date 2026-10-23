# Flujos multimodelo con Codex y Antigravity — C049–C052

Revisión fijada: `ef648e01899ba3e8dc6371642deaaf64b4477775`.
Cuatro definiciones completas: **34.890 bytes/956 líneas**. [commands-c3-multi-model-reading-evidence.json](commands-c3-multi-model-reading-evidence.json).
Nada se ejecutó ni se integró. Propuestas para T-08/T-11.

Los cuatro dependen del runtime externo `ccg-workflow` (`~/.claude/bin/codeagent-wrapper`
y los prompts de rol `~/.claude/.ccg/prompts/*`), que no viaja con los comandos y no se leyó.
Ningún comando declara `allowed-tools`, `model` ni `argument-hint`: solo `description`.

## Decisión común

La secuencia investigar → idear → planificar → ejecutar → optimizar → revisar ya tiene
dueño: el flujo completo de `/dev-cycle` (`analyst`/`evaluator` → `architect` con 2-3
opciones que elige el usuario → `planner` → `implementer` → `adversarial-review` → `qa`).
Lo propio de estos comandos es **despachar a modelos externos** y repartir la autoridad
por modelo («backend sigue a Codex, frontend sigue a Antigravity»). Ese despacho ya
está **aparcado** en el backlog de skills: D-118 (crítica externa y `external-review.py`
hasta tener adaptador por runtime verificado) y D-119 (despacho externo de misiones con
identidad, SHA base y sin auto-merge). Además, las piezas del plugin no saben de runtimes;
la traducción es de `export-interop.py`.

Lo conservable, la **soberanía del código** (los modelos externos devuelven un diff y
no escriben), ya es el contrato propio: `reviewer` no tiene Write/Edit y el subagente
de `task-brief.py` tiene prohibido tocar el ledger (`commands/dev-cycle.md:405`).

| Defecto de la fuente | Cita |
|---|---|
| La ejecución exige que el usuario haya respondido «Y» al plan, pero el comando de plan prohíbe preguntar Y/N | C049 l.21 y l.128-129 frente a C051 l.228-229 y l.271: cada ejecución vuelve a pedir confirmación |
| Los cuerpos se llaman a sí mismos `/ccg:plan`, `/ccg:execute`, `/frontend` y `/workflow`, no `multi-*` | C049 l.309, C051 l.220, C050 l.14, C052 l.16: el comando que se imprime para el siguiente paso no existe con ese nombre |
| Planes en `.claude/plan/` (singular) | C051 l.209 y C050 l.127 frente a `.claude/plans/` de C061 y C059: el lienzo de C059 no encuentra estos planes |
| Plantilla `{{LITE_MODE_FLAG}}` sin resolver en todas las llamadas | C049 l.32, C050 l.41, C051 l.31, C052 l.45 |
| Numeración de fases rota | C049 salta de la Fase 1 a la 3 (l.170 «Proceed to Phase 3») |
| Bucle de auditoría sin tope | C049 l.270 «Repeat Phase 5.1 as needed (until risk is acceptable)»; el propio acota a 3 intentos (`skills/adversarial-review/SKILL.md:114-124`) |
| Autoridad por modelo, no por evidencia | C049 l.187 («su prototipo es la línea base visual final») y l.268; los veredictos propios son por criterio con `fichero:línea` |
| Nota de modelo como puerta | C050 l.101 y C052 l.130-132 («completeness score ≥ 7»): ya resuelto en «Puntuaciones del modelo como veredicto» de [skills-destinations.md](skills-destinations.md) |
| Salida de datos sin declarar | El plan y los ficheros objetivo viajan al backend externo (C049 l.35-36, C051 l.35) sin decir qué sale ni excluir secretos |

## C049 — multi-execute

`11.067 bytes/321 líneas` · frontmatter: solo `description`. Lee un plan (o una
descripción directa), pide a Codex o Antigravity un prototipo en diff unificado,
Claude lo refactoriza y aplica, y ambos modelos auditan el resultado.

- **Intención y disparador:** «ejecuta el plan con Codex y Antigravity».
- **Artefactos y dueño propio:** código del proyecto → `implementer` (único que lo toca);
  informe final en el chat. Lee `.claude/plan/<x>.md` → en el plugin, `tasks.md` de `planner`.
- **Despacho:** `codeagent-wrapper` por Bash en segundo plano; `ace-tool` MCP opcional; Explore como respaldo.
- **Escenario positivo:** «implementa el plan aprobado de `docs/roadmap/<…>`» → `/dev-cycle`
  Fase 3 → `implementer` y después `adversarial-review`.
- **Escenario negativo:** «pide a Codex un segundo diff y fusiónalo» → ninguna pieza
  propia; no se activa `implementer` como despachador externo (D-119 aparcado).

**Comparación.** El reparto frontend/backend por palabras clave (l.133-137) es en el
plugin la persona por `- **Tipo**:` de la tarea (`commands/dev-cycle.md:394`). La
auditoría por dos modelos equivale a las lentes de `adversarial-review` ejecutadas por
`reviewer`, que añaden la Lente A (conformidad con spec y plan) que aquí no existe.

**Destino:** **Sin destino** (aparcado en D-118/D-119).

## C050 — multi-frontend

`5.712 bytes/164 líneas` · frontmatter: solo `description`. Flujo de UI dirigido por
Antigravity: investigación, al menos dos soluciones, plan, implementación,
optimización con la revisión de Antigravity y revisión final.

- **Intención y disparador:** «diseña y construye este componente/animación/layout».
- **Artefactos y dueño propio:** `.claude/plan/task-name.md` → `planner`
  (`improvement-plan.md` + `tasks.md`); código → `implementer`.
- **Despacho:** `codeagent-wrapper --backend antigravity` con prompts de análisis, arquitectura y revisión.
- **Escenario positivo:** «construye el panel de filtros con dos alternativas de diseño»
  → `/dev-cycle` flujo completo con `architect` (Fase 2-a) y `frontend-quality` en
  plan, implementación y revisión; `qa` para el E2E.
- **Escenario negativo:** «revisa la accesibilidad de este diff» → `adversarial-review`
  con los criterios de `frontend-quality`, no un flujo completo de UI.

**Comparación.** «Al menos dos soluciones y espera la elección del usuario» (l.115) es la
doble pasada de `architect` (`agents/architect.md:109-127`). La revisión final «verifica
responsividad y accesibilidad» (l.153-155) sin evidencia; en el plugin el verde lo da
`qa-gate.py`.

**Destino:** **Sin destino.**

## C051 — multi-plan

`10.048 bytes/274 líneas` · frontmatter: solo `description`. Solo planifica: mejora el
prompt, recupera contexto, pide análisis y borradores de plan a los dos modelos en
paralelo, sintetiza un plan, lo guarda con los `SESSION_ID` y termina sin ejecutar.

- **Intención y disparador:** «quiero un plan contrastado por Codex y Antigravity».
- **Artefactos y dueño propio:** `.claude/plan/<feature>.md` (y `-v2`, `-v3`) → `planner`.
- **Despacho:** `ace-tool` (`enhance_prompt`, `search_context`) o Glob/Grep/Read/Explore; dos modelos en paralelo.
- **Escenario positivo:** «planifica esta mejora» → `planner` (vía `/dev-cycle` Fase 2-b o `@planner`).
- **Escenario negativo:** «dame borradores de plan de dos modelos» → sin pieza propia (aparcado).

**Comparación.** «Planning only, never modify production code» es el «No hace» de
`planner` en `docs/agents/ROLES.md:30`. Repartir el requisito original «sin opiniones
previas» a dos analistas es la independencia que ya da el contexto fresco de las
lentes. Guardar los `SESSION_ID` de una herramienta externa en el plan mete estado
de transporte en el artefacto canónico.

**Destino:** **Sin destino.**

## C052 — multi-workflow

`8.063 bytes/197 líneas` · frontmatter: solo `description`. Flujo completo de seis
fases con los dos modelos, confirmación del usuario tras cada fase y parada si la
nota de completitud baja de 7. Remite a `node scripts/orchestrate-worktrees.js` para
trabajadores en paralelo (l.115), script que no viaja con el comando.

- **Intención y disparador:** «haz el ciclo completo de esta tarea con varios modelos».
- **Artefactos y dueño propio:** plan → `planner`; código → `implementer`.
- **Despacho:** `codeagent-wrapper` en las fases de idea, plan y optimización.
- **Escenario positivo:** «haz el ciclo completo de esta funcionalidad» → `/dev-cycle` flujo completo.
- **Escenario negativo:** «solo planifica» → `/dev-cycle` se detiene en la Fase 2
  (`commands/dev-cycle.md:544`) o `planner` a demanda; no el flujo entero.

**Comparación.** La secuencia es la de `/dev-cycle`. La diferencia es de puertas: la
fuente confirma tras cada fase; el plugin solo en go/no-go, OK del plan y verde de
pruebas (`commands/dev-cycle.md:543`). El reparto en worktrees paralelos ya tiene dueño
en el paso 6 del despacho por subagentes (máximo 3, worktree temporal por tarea,
`commands/dev-cycle.md:403`).

**Destino:** **Sin destino.**
