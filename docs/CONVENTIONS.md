# Convención de organización — agentes custom

[English](en/CONVENTIONS.md) · **Español**

Reglas para añadir agentes sin que se pisen entre sí, permitiendo que unos dependan de otros o de recursos compartidos. **Léela antes de crear o mover nada.**

## 1. Principio

Tres tipos de artefacto, tres ubicaciones fijas. Lo **compartido** vive en carpetas comunes por nombre único; lo **privado** de un agente vive en su propio namespace. La documentación va **siempre** en `docs/`, nunca junto al código.

```
custom-agents/               (raíz; se despliega como .claude/ del proyecto)
├── agents/<agente>.md       # definición del agente (uno por fichero, plano)
├── skills/<skill>/          # skills COMPARTIDAS (reutilizables por varios agentes)
├── agent-kits/<agente>/     # toolkit PRIVADO de un agente (scripts, plantillas)
└── docs/                    # TODA la documentación
    ├── README.md            # índice maestro (actualízalo al añadir un agente)
    ├── CONVENTIONS.md       # este documento
    ├── INSTALL.md           # despliegue del bundle
    └── agents/<agente>*.md  # documentación por agente
```

## 2. Nomenclatura (evita colisiones)

- **Un agente = un nombre en kebab-case** (`nemesis`, `code-reviewer`, `db-migrator`). Ese nombre es la clave única en todo el repo.
- El fichero del agente es `agents/<nombre>.md` y su `name:` en el frontmatter **debe** coincidir con `<nombre>`.
- El toolkit privado de un agente va en `agent-kits/<nombre>/` — mismo nombre. Así nunca chocan dos toolkits.
- Las skills se nombran por **función**, no por agente (`cybersecurity`, no `nemesis-sast`), porque están pensadas para reutilizarse.
- La documentación de un agente vive en `docs/agents/<nombre>.md` (+ ficheros auxiliares con prefijo `<nombre>-`, p. ej. `nemesis-presentacion.md`).

## 3. Compartido vs. privado — cómo decidir

| ¿Lo usará más de un agente? | Dónde va |
|-----------------------------|----------|
| Sí (o está pensado para reutilizar) | `skills/<skill>/` — compartido |
| No, es específico de un agente | `agent-kits/<agente>/` — privado |

Regla práctica: si dudas, empieza en el kit privado. Promociónalo a `skills/` el día que un segundo agente lo necesite (y actualiza las dependencias de ambos).

**Excepción — `agent-kits/shared/` (fragmentos de prompt compartidos):** cuando un **trozo de texto del prompt** (no un script ni una skill invocable) debe ser idéntico en varios agentes —la tabla de parámetros de estimación, el paso de opt-in de Confluence—, vive en `agent-kits/shared/` con **una sola fuente de verdad**, y los agentes lo referencian con la misma resolución `find` que sus kits. No es el kit de un agente concreto; es la excepción documentada a "un kit por agente". Un agente que no lo encuentre (instalación parcial) usa el fallback de una línea de su propio prompt. Ver `agent-kits/shared/README.md`. La tabla de transiciones de estado **no** se duplica: su única fuente es la §7.

**Model tiering (obligatorio, en dos capas):** todo agente declara `model` **y `effort`** en su frontmatter, proporcionales a la complejidad de su tarea. El linter (`scripts/lint_plugin.py`) exige ambos campos presentes y válidos (valores oficiales de sub-agents.md, verificados 2026-09-03: `model` ∈ `haiku|sonnet|opus|inherit`; `effort` ∈ `low|medium|high|xhigh|max`).

| Tier | `model` | `effort` | Agentes |
|---|---|---|---|
| Mecánico (convertir, formatear) | `haiku` | `medium` | *(ninguno hoy — `pdfy` se retiró, `ADR-011`)* |
| Desarrollo estándar (escribir, planificar, probar, documentar) | `sonnet` | `medium` | `analyst`, `planner`, `implementer`, `qa`, `documenter` |
| Razonamiento crítico (decidir, juzgar, auditar) | `opus` | `high` | `evaluator`, `architect`, `reviewer`, `nemesis` |

Capa 1 = frontmatter (lo que Claude Code aplica siempre, y lo ÚNICO que aplica en una invocación manual `@agente`). Capa 2 = override por proyecto en `.claude/dev.json` → `"modelos": {"<agente>": {"model": "…", "effort": "…"}}` (parcial, por agente; regla 9), que resuelve el script determinista `agent-kits/shared/model-tier.py <agente> [--json|--all]` (frontmatter + dev.json; valor inválido → aviso y se ignora; sin `dev.json` → frontmatter) y que los **orquestadores** (`/dev-cycle`, `/pm-cycle`, `adversarial-review`, `quick-implement`) consultan antes de despachar un agente por nombre para pasar `model` en el **parámetro por invocación del Agent tool** (prioridad 1 desde v2.1.251, por encima del frontmatter). **Honestidad:** el Agent tool no documenta un parámetro `effort`, así que el `effort` de `dev.json` es **informativo** (el orquestador lo anuncia; el efectivo es el del frontmatter). Decisión: `docs/knowledge/adr/ADR-009`.

**Skills cortas (progressive disclosure, obligatorio):** un `skills/<skill>/SKILL.md` se inyecta **completo** en el contexto cada vez que la skill se invoca, así que lleva solo el **mapa** — frontmatter, propósito, disparadores, el flujo de pasos (título + 1-3 líneas cada uno), guardrails/invariantes, «qué NO hace» y una **tabla de referencias** — y el detalle (plantillas largas, ejemplos, casuística, tablas de campos, catálogos, prompts de subagentes) vive en `skills/<skill>/references/<tema>.md`, enlazado desde el paso que lo usa con la instrucción explícita «lee X **solo** cuando llegues al paso Y». Umbrales: `SKILL.md` ≤ **200 líneas** (aviso del linter `SKILL_WARN_LINES`) y **250** como umbral duro (`tests/test_skill_size.py` falla). Al adelgazar una skill existente, **cero pérdida de contenido**: cada bloque movido reaparece literal en una referencia (`python3 tests/test_skill_size.py --diet-check <skill> <git-ref>` → `0 párrafos perdidos`) y los nombres de paso que citan otras piezas (`Paso 7`, `Paso 9`…) conservan su numeración. Decisión: `docs/knowledge/adr/ADR-008`.

## 4. Dependencias — se declaran en el frontmatter del agente

Cada agente declara de qué depende en su propio `agents/<nombre>.md`. Fuente de verdad única, junto al agente.

```yaml
---
name: nemesis
description: ...
tools: Read, Grep, Glob, Bash, Write, Edit, WebFetch, Agent
dependencies:
  skills:            # skills de skills/ que necesita
    - cybersecurity
  kits:              # toolkits privados de agent-kits/ que usa
    - agent-kits/nemesis
  agents: []         # otros agentes de los que depende (por nombre)
---
```

Notas:

- Las claves `name`, `description`, `tools` (y `model`) son las que interpreta Claude Code. `dependencies` es **informativo**: Claude Code ignora claves extra, y nos sirve a nosotros (y a scripts) para ver el grafo de un vistazo.
- **Campos nativos `skills:` y `hooks:`** (doc oficial de sub-agents, verificada 2026-09-02). `skills:` es la lista de skills que Claude Code **precarga** en el contexto del agente al arrancar (inyecta el contenido completo); `dependencies.skills` sigue siendo la fuente del grafo y debe ser **superconjunto** de `skills:` (el linter lo exige: una skill precargada que no esté declarada como dependencia es error). **Regla token-diet:** `skills:` solo para skills que el agente necesite en **TODAS** sus ejecuciones; las **opt-in** (Jira, Confluence…) se cargan bajo demanda con la herramienta Skill — precargar `jira-sync` + `confluence-publish` costaría ≈15k tokens por arranque para funciones que quizá estén apagadas. El linter avisa si la precarga declarada supera 16 KB. `hooks:` registra hooks **con alcance solo de ese agente** (misma forma que `settings.json`: evento → `[{matcher, hooks: [{type: command, command}]}]`); es el único sitio permitido para un hook de guardia (regla 8). `${CLAUDE_PLUGIN_ROOT}` no está documentado para esos `command`: úsalo con fallback `find` en la propia línea, como hace `agents/implementer.md`.
- Un agente **puede** depender de otro (campo `agents`). Referéncialo por su nombre; el otro agente debe existir en `agents/`. Evita ciclos (A→B→A).
- Un kit privado (`agent-kits/<x>/`) es de su agente; si otro agente lo necesita, es señal de que ese código debería ser una skill compartida (ver §3).

## 5. Rutas dentro del código

- Los scripts de un kit se localizan entre sí con **rutas relativas** (`dirname "$BASH_SOURCE"`), nunca con rutas absolutas del repo. Así renombrar/mover el kit no rompe nada interno.
- **Cuando el agente (`.md`) invoca su toolkit o plantillas, NO uses rutas fijas** tipo `.claude/agent-kits/...`: solo funcionan a nivel proyecto y se rompen a nivel usuario o como plugin (además, `${CLAUDE_PLUGIN_ROOT}` no se expande en markdown de agentes/skills). Resuelve el kit en tiempo de ejecución con `find` sobre ambos scopes:

  ```bash
  MIKIT="$(find "$PWD/.claude" "$HOME/.claude" -type d -path '*agent-kits/<nombre>' 2>/dev/null | head -1)"
  # luego usa "$MIKIT/tools/..." , "$MIKIT/templates/..." , etc.
  ```

  `$PWD/.claude` cubre el scope proyecto; `$HOME/.claude` cubre tanto usuario (`~/.claude/`) como el caché de plugins (`~/.claude/plugins/…`). El proyecto va primero → gana si hay varias copias (misma precedencia que Claude Code).
- Skills compartidas: invócalas con la herramienta Skill (por nombre). Si necesitas leer un fichero suyo, resuélvelo igual: `find "$PWD/.claude" "$HOME/.claude" -type f -path '*skills/<skill>/...'`.

## 6. Checklist para añadir un agente nuevo

1. Elige un nombre único en kebab-case.
2. Crea `agents/<nombre>.md` con frontmatter (incluido el bloque `dependencies`).
3. Si necesita scripts propios → `agent-kits/<nombre>/`. Si es reutilizable → `skills/<skill>/`.
4. Escribe la doc en `docs/agents/<nombre>.md`.
5. Añade la fila correspondiente en `docs/README.md` (agentes y, si aplica, skills).
6. **Actualiza los diagramas de `docs/FLOWS.md`** si el agente/comando/skill cambia algún flujo.
7. Verifica que no haya rutas absolutas rotas ni nombres duplicados.

## 7. Cadena de artefactos: spec → evaluación → plan (carpeta única por iniciativa)

Los agentes `evaluator` y `planner` producen sus artefactos en **una sola carpeta por iniciativa**: `docs/roadmap/<fecha>-<slug>/`. Todo lo de una iniciativa vive junto.

```
docs/roadmap/<fecha>-<slug>/
├── spec.md              # QUÉ se quiere (especificación)
├── evaluation.md        # CUÁNTO cuesta / si conviene
├── design.md            # (opcional) CON QUÉ ARQUITECTURA — 2-3 opciones, la elegida validada (agente architect)
├── improvement-plan.md  # CÓMO se ejecuta
├── tasks.md             # checklist de tareas del plan
└── testing/             # (opcional) salida del agente qa
```

Una evaluación **no-go** deja solo `spec.md` + `evaluation.md` (sin ficheros de plan). Índice único: `docs/roadmap/README.md`.

Estados por artefacto (vocabularios distintos, a propósito):

- **spec:** `borrador` · `aprobada` · `implementada` · `obsoleta`.
- **evaluación / plan:** `borrador` · `en-progreso` · `en-revision` · `completado` · `cancelado`.
- **design (opcional):** `borrador` (opciones abiertas) · `aprobado` (opción validada por el usuario) · `obsoleto` (re-diseño o cancelación).

**Transiciones a lo largo del ciclo (no dejar en `borrador`).** Todo artefacto nace en `borrador`,
pero cada fase que se supera **debe** moverlo al estado que toca (lo garantiza `/dev-cycle`, y los
agentes al ejecutarse sueltos):

- Tras **evaluar**: evaluación → `en-revision`. En la puerta **go**: spec → `aprobada`, evaluación → `completado`. En **no-go**: evaluación → `cancelado` (spec → `obsoleta` si se descarta).
- Al **crear el plan**: plan/tasks → `borrador`. Al **arrancar la implementación** (OK del plan): plan y fase activa → `en-progreso`.
- Durante la **implementación**: cada tarea `en-progreso` → `completado`; la fase → `completado` al cerrar sus tareas.
- En el **cierre** (qa en verde + documentado): plan → `completado` y spec → `implementada`.
- **Cancelación** en cualquier punto: plan/evaluación → `cancelado` (spec → `obsoleta` si aplica).

Reglas de enlazado (**bidireccional**, y como todo está en la misma carpeta, los enlaces son **nombres simples**):

- La `spec` lleva en su frontmatter `evaluacion: evaluation.md` y `plan: improvement-plan.md` (o `pendiente`), más callouts al inicio. Si hubo diseño, también `design: design.md`; el `design.md` lleva `spec:`, `evaluacion:`, `plan:` (lo rellena `planner` al crear el plan) y `adr:`; el `improvement-plan.md` añade la fila **Diseño**.
- La `evaluation.md` lleva filas **Spec** (`spec.md`) y **Plan** (`improvement-plan.md`); el `improvement-plan.md` lleva filas **Spec** (`spec.md`) y **Evaluación** (`evaluation.md`).
- Al **crear la evaluación**: rellena su fila **Spec** y **actualiza la spec** (`evaluacion:` + callout) para que apunte a la evaluación.
- Al **crear el plan**: rellena sus filas **Spec/Evaluación** y **actualiza hacia atrás** el `plan:` de la spec y la fila **Plan** de la evaluación.

**Coste de generación (bloque `generacion:`).** Cada artefacto de la cadena lleva en su
frontmatter un bloque `generacion:` con lo que costó **producirlo**, medido por
`agent-kits/shared/usage-meter.py` (`start` al abrirlo, `close` al cerrarlo): fechas de
inicio/fin (solo **contexto**, nunca fuente de horas), `tokens_reales` (la **medida**, leída de la
transcripción de la sesión), `eur`, `horas_ia` (**derivadas**: tokens facturables × ratio
calibrado — mediana de `CALIBRATION.md` > default de `estimation-defaults.md`) y `fuente:
medido|estimado`. Reglas: el meter **nunca bloquea** (si no puede leer la transcripción, degrada
a `estimado` con aviso); re-cerrar **sustituye** el bloque (no acumula); cada agente **cierra su
marcador antes del handoff** (ventanas solapadas reparten mal el coste); los artefactos legacy
sin bloque son válidos. Las duraciones presentadas a personas van en formato humano `XhYm`
(`usage-meter.py fmt`: `32m` · `1h 32m` · `18h`). `/roadmap-metrics` agrega estos bloques como
**coste de proceso** (separado del de implementación) y `/retro` calibra con ellos el ratio.

## 8. Progreso de un plan: `tasks.md` es el ledger canónico

El avance de un plan se registra en **un único sitio**: `docs/roadmap/<fecha>-<slug>/tasks.md`
(checkbox + estado por tarea T-XX + tabla de resumen). Es la **fuente única de verdad**.

- **Cualquier implementador** debe actualizar `tasks.md` al completar cada tarea: el agente `implementer`, el chat principal, o un **orquestador externo** (cualquier motor SDD de terceros).
- Si una herramienta lleva su propio registro (todo-list interna, el fichero de progreso del motor externo, etc.), ese registro es **espejo**, no fuente: `tasks.md` manda. Ante discrepancia, gana `tasks.md`.
- El orquestador `/dev-cycle` y el agente `implementer` aplican esta regla de serie. Para que la respeten orquestadores externos, `/dev-cycle` ofrece añadir esta regla al `CLAUDE.md` del proyecto consumidor.
- **Estados con motor externo:** cuando la implementación se delega a un orquestador externo, ese motor **no** actualiza tus artefactos. Por tanto, `/dev-cycle` (o tú) aplica las **transiciones de estado** de la regla 7 y mantiene `tasks.md` al día en su nombre. Las transiciones valen igual haya o no motor externo.
- El cierre del ciclo (documentación con `documenter`) se hace **una vez** tras implementar y con `qa` en verde, no tarea a tarea.
- **Validación mecánica:** `agent-kits/shared/ledger-lint.py` comprueba el ledger con exit code (vocabulario de estados, `completado` ⟹ criterios marcados, resumen cuadrado, IDs únicos). Lo corren `implementer` (DoD), `qa` (P1) y `/dev-cycle` en sus puertas; además un hook PostToolUse (`hooks/ledger-lint-warn.sh`) lo ejecuta en **modo aviso** en cada edición de un `tasks.md`. El «verde» de qa también es mecánico: `agent-kits/qa/qa-gate.py` sobre `results.json`.
- **Dos clases de hooks.** (a) **Informativos** — globales, en `hooks/hooks.json`, `PostToolUse`/`SubagentStop`/`SessionStart`; informan (`systemMessage`/`additionalContext`) y **siempre exit 0**. (b) **De guardia** — `PreToolUse` con `permissionDecision: deny`, **SOLO en el frontmatter `hooks:` de un agente** (alcance del agente), con la decisión en un **script determinista con tests** (`agent-kits/shared/guardrail-check.py`), razón en una frase con cómo proceder, desactivables por regla en `.claude/dev.json` (`guardrails`), y que degradan sin bloquear (sin `python3` → aviso único, exit 0; error interno → allow). **Un deny global está prohibido**: `planner`/`evaluator`/`analyst` escriben en `docs/roadmap/` legítimamente y un hook en `hooks.json` los rompería (ADR-007). Hoy el único hook de guardia es el del `implementer` (`hooks/implementer-guardrail.sh`: alcance `docs/roadmap/` solo `tasks.md` —más el índice `docs/roadmap/README.md`— y nunca `docs/security-scan/`, rutas case-insensitive, rama de trabajo, git no destructivo). El alcance del **diff** completo lo comprueba aparte `agent-kits/shared/scope-check.py` (ficheros cambiados vs. campos `Archivos` del ledger) como puerta previa a la revisión de dos lentes (skill `adversarial-review`, fuente única del método; su `review-lens-select.py` decide si se añade la lente C de seguridad) y en el DoD del implementer.
- **Visibilidad en vivo (hooks informativos):** el plugin registra hooks en `PostToolUse` (aviso de lint + **línea de progreso** `progress-report.py line` al editar un `tasks.md`), `SubagentStop` (estado de las iniciativas `en-progreso` al terminar un subagente) y `SessionStart` (`startup|resume|compact`: **índice de piezas** con `agent-kits/shared/skill-index.py` —una línea por comando/skill/agente desde los frontmatters, ≤ 45 líneas / ≤ 3.500 caracteres, caché por hash en `.claude/.skill-index.cache`— más el contexto de retoma con `progress-report.py session` y, solo en `startup|resume`, la última entrada del **journal de sesión** — regla 10) y `SessionEnd` (`hooks/session-journal.sh`: escribe la entrada del journal; su salida se ignora por contrato y sus hooks comparten un presupuesto de 1,5 s que `hooks.json` sube con `timeout: 20` — hooks.md, verificado 2026-09-03) (el índice también en `compact` porque la compactación resume la conversación y puede perder el índice del arranque —guía oficial de hooks, verificada 2026-09-03—; total bajo el tope de 10.000 caracteres del hook). **El índice es informativo**: recuerda qué piezas existen y las reglas de enrutado (skill que casa → invocarla; los comandos se invocan por `/` o por descripción, como las skills —Claude Code los trata como skills salvo `disable-model-invocation`—, y los evals de `evals/cases/command-*.json` lo prueban con positivos en lenguaje natural), no fuerza ninguna invocación, y se apaga con `dev.json` `sesion.indice: false`. Principio: **los hooks informan (`systemMessage` / `hookSpecificOutput.additionalContext`), no deciden; siempre exit 0** — sin `python3` callan; un hook roto es una pieza muerta, no un guardrail (el linter comprueba que cada `command` de `hooks/hooks.json` exista y sea ejecutable). Los hooks tienen **suite de shell** (`tests/test_hooks_shell.py`: pytest lanza cada `hooks/*.sh` con `bash` sobre un proyecto temporal con un ledger de fixture y afirma el JSON de salida, el debounce —incluida su atomicidad con 6 invocaciones concurrentes—, la degradación sin `python3` y `exit 0` en todos los casos; se salta entera si no hay `bash`). La statusline (`statusline/roadmap-statusline.sh`) es **opt-in** en `/setup` y se escribe con ruta absoluta en `.claude/settings.json` (la doc oficial no expande `${CLAUDE_PLUGIN_ROOT}` en `statusLine.command`).

## 9. Ficheros de config/estado en `.claude/` del proyecto consumidor

Cada skill guarda su config (decisiones del usuario) y su estado (memoria de máquina) en
`.claude/` del proyecto. Mapa único — quién escribe qué y cómo se recupera si se pierde:

| Fichero | Qué es | Lo escribe | Si se corrompe/pierde |
|---|---|---|---|
| `rates.json` | Config compartida de presupuesto (tarifa, tokens, jornada, ratios) | `/setup` o a mano | Recrear desde `agent-kits/evaluator/templates/rates.example.json` |
| `confluence.json` | Opt-in + destino de publicación (espacio/anclaje) | skill `confluence-publish` | Relanzar el alta guiada (elige espacio de nuevo) |
| `confluence-state.json` | Manifiesto página↔fichero (hash + pageId) | `confluence-publish`/`pull` | Se reconstruye: publish busca por título bajo el anclaje antes de crear |
| `jira.json` | Opt-in + política de jornada (`alCubrirJornada`) | skill `jira-sync` o `/setup` | Recrear con `/setup`; defaults seguros |
| `jira-state.json` | Mapeo T-XX↔issue, imputado por día, banco de horas | `jira-sync` (vía `worklog.py`) | Mapeo: re-derivable de las claves anotadas en `tasks.md`; imputado/banco: revisar worklogs en Jira |
| `dev.json` | Disciplina de la cadena nativa de `/dev-cycle`: `tdd` (RED-GREEN-REFACTOR con evidencia del rojo), `worktree` (iniciativa en worktree aislado), `subagentes` (una tarea = un subagente fresco), `constitucion` (decisión del opt-in de `docs/CONSTITUTION.md` — distingue "declinado" de "nunca preguntado"), `guardrails` (hook de guardia del implementer: `true` por defecto; `false` o `{"alcance","ramaPrincipal","git"}` por regla), `revision.lenteSeguridad` (`auto` por defecto: la lente C de seguridad de `adversarial-review` solo si `review-lens-select.py` detecta rutas/líneas sensibles; `siempre` · `nunca`; lo pregunta `/setup` paso 5-ter), `revision.lenteRendimiento` (superiority T-04, mismo vocabulario y mismo default `auto`: la lente D de rendimiento del MISMO `review-lens-select.py` solo si detecta rutas de repositorio/consulta/cola o patrones costosos —N+1, `await` en bucle, `sleep` bloqueante—; lo pregunta el mismo paso 5-ter), `revision.excluir` (lista de globs `**`-aware que se sacan de la heurística de **ruta** de las lentes C y D —cada una con sus propios stems—, no de la de contenido — p. ej. `["hooks/**"]` en un repo cuyos hooks se llamen `session-*.sh`; ajuste manual), `tests.coberturaMinima` (superiority T-03, **ausente por defecto = sin gate**: umbral mínimo N de cobertura por diff que `implementer` P5 comprueba con la skill `unit-tests` —`coverage-gate.py --changed-only`— solo si la herramienta oficial del stack está instalada; sin ella, solo informa sin bloquear; lo pregunta `/setup` paso 5-quinquies), `sesion.indice` (`true` por defecto: el hook `SessionStart` inyecta el índice compacto de piezas de `skill-index.py`; `false` lo apaga y deja solo el contexto de retoma del roadmap), `sesion.journal` (`true` por defecto: el hook `SessionEnd` escribe la entrada de bitácora en `docs/knowledge/journal/` y `SessionStart` reinyecta la última; `false` lo apaga — regla 10), `modelos` (**tiering configurable, capa 2** — `{"<agente>": {"model": "haiku|sonnet|opus|inherit|claude-…", "effort": "low|medium|high|xhigh|max"}}`, parcial y por agente; lo resuelve `agent-kits/shared/model-tier.py` y lo pasan los orquestadores en el parámetro `model` del Agent tool; `effort` aquí es informativo — el Agent tool no lo admite por invocación —; la invocación manual `@agente` sigue el frontmatter; lo pregunta `/setup` paso 5-quater). Todo opt-in con defaults `false` salvo `guardrails` (activo), `revision.lenteSeguridad`/`revision.lenteRendimiento` (`auto` cada una), `sesion.indice` y `sesion.journal` (activos), `modelos` (ausente = frontmatter) y `tests.coberturaMinima` (ausente = sin gate) | `/setup` o a mano | Recrear con `/setup`; sin fichero o corrupto → defaults `false` + aviso (comportamiento clásico) |
| `usage-state.json` | Marcadores de medición de coste (`usage-meter.py`: offsets por transcripción y artefacto) | `usage-meter.py` | Borrarlo es inocuo: se pierden los marcadores abiertos; los siguientes `start` lo recrean |
| `.confluence-pending` | Marca efímera del hook (hay docs sin sincronizar) | hook `PostToolUse` | Borrarla es inocuo; la skill re-detecta por manifiesto |

Reglas: **config ≠ estado** (la config la decide el usuario; el estado lo mantiene la máquina y
nunca se edita a mano); toda skill nueva que necesite memoria sigue este patrón (`<skill>.json` +
`<skill>-state.json`) y añade su fila aquí.

## 10. Memoria técnica del proyecto — `docs/knowledge/`

Además del roadmap (regla 7, decisión+resultado por iniciativa) y de la configuración (regla 9),
el plugin mantiene una **memoria técnica transversal** en `docs/knowledge/` del proyecto
consumidor: decisiones de diseño (ADR), trampas ya comprobadas (gotchas) y lecciones de proceso —
lo que "ya no hay que volver a descubrir" cada vez, generalizando el patrón de bookends de
`agents/nemesis.md` (`docs/security-scan/STATE.md`+`MEMORY.md`).

- **Dónde vive.** `docs/knowledge/adr/ADR-NNN-<slug>.md` (una por decisión, plantilla
  `agent-kits/shared/templates/adr.md`), `docs/knowledge/gotchas/GOT-NNN-<slug>.md` (una por
  entrada) y `docs/knowledge/lessons/LES-NNN-<agente>-<slug>.md` (una por entrada, agrupada por
  agente en el nombre),
  con un `README.md` **índice de entrada** (el índice generado + `knowledge-lint.py` quedan
  diferidos hasta que haya evidencia de que hacen falta: más de 15 entradas o la primera colisión
  de ID en cualquiera de las tres familias, en un lote paralelo). Un fichero por entrada en los
  tres tipos elimina la colisión de FICHERO en escritura paralela; la colisión de `id:` sigue
  siendo posible en las tres familias (ADR/GOT/LES), con la misma mitigación (renumerar y
  declararlo en la retro), ver regla anterior.
- **Siempre activa, sin opt-in.** Si `docs/knowledge/` no existiera, ningún agente se queja: la
  carpeta nace en el primer registro. Es la misma filosofía de degradación silenciosa que el resto
  del plugin (constitución, Jira, Confluence), pero sin interruptor — no hay nada que activar.
- **Umbral de registro (anti-burocracia).** Un ADR solo si la decisión **cierra una alternativa
  real** Y (afecta a 2+ piezas del repo O se tomó en una puerta de decisión) — **no** merece ADR
  elegir el nombre de una variable, ni una decisión reversible sin coste, ni algo que ya estaba
  implícito en una regla existente. Un gotcha solo si costó **al menos un ciclo de depuración real**
  o casi rompió una garantía del producto — **no** merece gotcha una intuición sin comprobar ni un
  typo corregido al vuelo. El objetivo es 0-2 entradas por iniciativa, no un registro exhaustivo.
- **Quién escribe.** `architect` escribe el ADR de la opción de diseño elegida (con las descartadas
  como alternativas) al aprobarse `design.md`; `planner`/`implementer` escriben un ADR cuando su decisión de diseño (al
  descomponer el plan o al resolver una ambigüedad en ejecución) cruza el umbral, con
  `estado: propuesta` a validar por la revisión de dos lentes o el usuario. `debug-root-cause`
  escribe un gotcha al cerrar su Fase 4 (causa raíz confirmada, no diagnóstico parcial). `qa`
  escribe un gotcha cuando un flaky justificado resulta ser un **patrón** (2+ ciclos con el mismo
  motivo), no un accidente aislado. `/retro` produce, además de la fila numérica de
  `CALIBRATION.md`, una **segunda salida** con los aprendizajes técnicos cualitativos del cierre de
  la iniciativa. Fragmento compartido: `agent-kits/shared/knowledge-write.md`.
- **Quién lee.** `evaluator`, `planner`, `implementer`, `qa` y `documenter` aplican el paso
  compartido `agent-kits/shared/knowledge-check.md` antes de trabajar: leen el índice de entrada
  (`README.md`) y abren **solo el fichero de la entrada concreta** de su área (lectura SELECTIVA,
  progressive disclosure — protege la inversión de `2026-08-10-token-diet`, nunca "todo
  `gotchas/`" ni "todo `lessons/`"). Reparto: `evaluator` → `lessons/LES-*-evaluator-*`; `planner` →
  `adr/` + `lessons/`; `implementer` → `adr/` + `gotchas/`; `qa` → `gotchas/`; `documenter` → todo
  lo que liste el índice (es quien la indexa en la documentación de producto).
- **Prueba del mecanismo (fila "Prueba del mecanismo" de la spec de `knowledge-capture`, no D3).**
  Las "tres lecciones de la primera calibración real" que vivían hardcodeadas en
  `agents/evaluator.md` se migraron a `docs/knowledge/LESSONS.md#evaluator` (hoy repartidas en
  tres ficheros bajo `docs/knowledge/lessons/`, tras `knowledge-split`): el prompt las lee de ahí,
  no las lleva incrustadas. Es el criterio de que el bucle de lectura funciona de verdad — las
  lecciones pueden salir del prompt sin dejar de aplicarse. **Ojo:** esto solo pasa cuando el
  proyecto tiene `docs/knowledge/` poblado con ellas (este repo, tras el backfill); un proyecto
  consumidor recién instalado arranca con memoria vacía (D3: siempre activa, sin opt-in, pero sin
  contenido hasta el primer registro) y las va poblando con `/retro` y las puertas de decisión.
- **Journal de sesión — memoria EPISÓDICA, no curada (`docs/knowledge/journal/`, iniciativa
  `memory-health`).** Junto a la memoria **curada** (ADR/gotchas/lecciones: con umbral, con estado, la
  valida una puerta) vive una **bitácora cronológica por sesión**: `journal/AAAA-MM-DD-<slug>.md`, una
  entrada por sesión, que escribe el hook `SessionEnd` (`hooks/session-journal.sh` →
  `agent-kits/shared/journal.py write`, idempotente por `session_id`) con un **borrador determinista**
  (fecha, iniciativa activa, ficheros tocados por git, tareas del ledger que cambiaron de estado,
  marcadores del meter cerrados, primer prompt como resumen best-effort) y que `SessionStart`
  (`startup|resume`, no `compact`) reinyecta compactada (≤ 25 líneas, `journal.py latest`). Reglas:
  (1) nadie la escribe a mano salvo para enriquecer la entrada de la sesión (`--enrich`); (2) **lo que
  merezca doctrina se promueve** a `adr/`/`gotchas/`/`lessons/` con el umbral de `knowledge-write.md`
  — el journal no es el sitio donde una decisión se queda; (3) `evaluator`/`planner`/`architect` leen
  SOLO la última entrada y SOLO si es de su iniciativa (`knowledge-check.md`); `/retro` usa las
  entradas de la iniciativa como fuente de causas de desviación; (4) **excluida de Confluence**
  (`docs/knowledge/journal/**`: bitácora, no decisión — política D1) y con índice propio generado
  (`journal/README.md`), fuera de la tabla de `docs/knowledge/README.md`; (5) opt-out por proyecto
  `dev.json` `sesion.journal: false`; (6) el hook **solo escribe en proyectos con rastro del plugin**
  (`docs/roadmap/`, `docs/knowledge/` o `.claude/dev.json`) — en cualquier otro repo sale en silencio;
  (7) **las entradas se versionan** (memoria del proyecto, como ADR y lecciones) — quien no quiera
  versionarlas añade `docs/knowledge/journal/*.md` (no el `README.md`) a su `.gitignore`; el nombre es
  `AAAA-MM-DD-<iniciativa activa | sesion>.md`. **Sin resumen por IA**: la doc oficial de hooks (2026-09-03) solo
  permite a los hooks `prompt`/`agent` devolver una decisión `ok/reason`, y en `SessionEnd` toda salida
  se ignora — se documenta como limitación (ADR-010), no se finge.
- **Nota (D2):** la sección "Notas de implementación" de la plantilla `agent-kits/planner/templates/tasks.md`
  se retiró (iniciativa `knowledge-capture`, tarea T-14) — el registro cualitativo de una
  iniciativa vive en `docs/knowledge/`, no en un cajón de sastre al final del ledger.
