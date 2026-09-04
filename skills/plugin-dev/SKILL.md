---
name: plugin-dev
description: Meta-skill para DESARROLLAR este plugin — crear o modificar agentes, skills, comandos, kits y hooks de custom-agents siguiendo sus convenciones, con checklist de validación y plantillas. Garantiza que cada pieza nueva nazca con frontmatter correcto, model tiering, dependencias declaradas, doc en docs/, determinismo en scripts (tests + exit codes) y degradación sin bloquear. Úsala cuando el usuario diga "crea un agente/skill/comando nuevo", "añade una skill al plugin", "modifica el agente X", "extiende el plugin", o cuando cualquier tarea toque agents/, skills/, commands/, agent-kits/ o hooks/ de este repo.
---

# plugin-dev — cómo se construye este plugin (fuente única del proceso)

Meta-skill de desarrollo del propio plugin: cubre **todas** sus piezas, no solo
skills, también agentes, comandos, kits y hooks. La regla que gobierna todo:

> **Las convenciones se LEEN antes de crear, no se recuerdan de memoria.** El primer paso de
> cualquier pieza nueva es abrir `docs/CONVENTIONS.md` (y `docs/FLOWS.md` si tocas un flujo).
> Esta skill es el mapa del proceso; CONVENTIONS es la ley.

Resolución de rutas (regla 5 de CONVENTIONS — nunca rutas fijas):

```bash
PLUGROOT="$(find "$PWD/.claude" "$HOME/.claude" -type d -path '*skills/plugin-dev' 2>/dev/null | head -1)"
# plantillas: "$PLUGROOT/templates/…" · convenciones: la CONVENTIONS.md del repo en que trabajas
```

## Paso 0 — ¿Qué tipo de pieza es? (árbol de decisión)

| Si lo que necesitas es… | Entonces es… | Va en… | Plantilla |
|---|---|---|---|
| Un rol autónomo con prompt propio que Claude invoca por nombre | **agente** | `agents/<nombre>.md` | `templates/agent.template.md` |
| Un orquestador que el usuario lanza (`/algo`) y coordina agentes/puertas | **comando** | `commands/<nombre>.md` | `templates/command.template.md` |
| Capacidad reutilizable por 2+ agentes (o pensada para reutilizar) | **skill compartida** | `skills/<nombre>/SKILL.md` | `templates/skill.template.md` |
| Script/plantilla de UN solo agente | **kit privado** | `agent-kits/<agente>/` | — |
| Trozo de PROMPT idéntico en varios agentes (no invocable) | **fragmento shared** | `agent-kits/shared/` | — |
| Reacción automática a eventos del ciclo de vida, para INFORMAR | **hook informativo** | `hooks/` + registro global en `hooks/hooks.json` (eventos usados: `PostToolUse`, `SubagentStop`, `SessionStart`). **Informan, no deciden**: `systemMessage`/`additionalContext`, SIEMPRE exit 0, silencio sin `python3`; el linter exige que cada `command` exista y sea ejecutable | `hooks/progress-line.sh` como referencia |
| Impedir que UN agente haga algo prohibido (deny) | **hook de guardia** | wrapper en `hooks/` registrado SOLO en el frontmatter `hooks:` de ese agente (`PreToolUse` → JSON `permissionDecision: deny`); la decisión en un script de `agent-kits/shared/` con tests; desactivable en `.claude/dev.json`; sin `python3` → aviso y exit 0. **Nunca en `hooks/hooks.json`** (regla 8 de CONVENTIONS, ADR-007) | `hooks/implementer-guardrail.sh` + `agent-kits/shared/guardrail-check.py` |

**Contratos oficiales de Claude Code (regla antes de cualquier WebFetch):** consulta
`references/claude-code-contracts.md` (hooks, frontmatter de agente y skill, CLI headless, `statusLine`,
`plugin.json`, cada uno con URL + fecha). Si el contrato está ahí con menos de 90 días, úsalo; **si dudas o
han pasado > 90 días, re-verifica** con su sección «cómo re-verificar» y actualiza la fecha de la fila en el
mismo cambio. Redacción de docs/agentes/skills: `agent-kits/shared/docs-style.md`.

Duda entre kit privado y skill → **empieza privado**; promociona a `skills/` el día que un
segundo agente lo necesite (regla 3). Duda entre agente y comando → si decide *puertas* y
*orquesta* a otros, es comando; si *hace* un trabajo con criterio propio, es agente.
Duda entre **skill y agente nuevo** → es agente SOLO si aporta un rol que **decide y escribe un
artefacto propio** que hoy nadie decide; una **capacidad** que 2+ agentes invocan es skill, aunque
suene a oficio («tester», «revisor de rendimiento»). Síntoma de haber elegido mal: repartir la misma
responsabilidad entre dos piezas («este escribe el test, aquel dice si vale») — `LES-013`, `ADR-011`.

## Paso 1 — Nombre y colisiones

- Kebab-case, único en TODO el repo (`agents/`, `agent-kits/`, `skills/`, `commands/` comparten
  espacio de nombres a efectos prácticos). El `name:` del frontmatter **coincide** con el fichero/carpeta.
- Skills se nombran por **función** (`cybersecurity`), nunca por agente (`nemesis-sast`).
- Evita nombres genéricos (`setup`, `test`, `docs`, `plan`, `status`…): el linter avisa
  (`GENERIC_NAME_TOKENS` en `scripts/lint_plugin.py`) porque colisionan al copiar el bundle a
  otros proyectos. Aunque tu nombre no esté en esa lista, aplica el mismo juicio.

## Paso 2 — Escribir la pieza (frontmatter obligatorio)

**Agente** — claves que interpreta Claude Code + las nuestras:

- `name` (== fichero) · `description` (párrafo con disparadores: termina con "Úsalo cuando el usuario diga …") · `tools` (**mínimos**: solo los que usa de verdad; pedir `Bash` sin usarlo es deuda) · `model` + `effort` (**obligatorios**, tabla de tiering de CONVENTIONS: `haiku`/`sonnet` → `effort: medium` · `opus` razonamiento crítico → `effort: high`; el override por proyecto vive en `dev.json` `modelos` y lo resuelve `agent-kits/shared/model-tier.py`, no el agente) · `dependencies` (skills/kits/agents que EXISTEN; sin ciclos A→B→A).
- Opcionales nativos: `skills:` (precarga el contenido COMPLETO de esas skills al arrancar — solo las que el agente necesita en TODAS sus ejecuciones; las opt-in se invocan bajo demanda con la herramienta Skill; cada una debe estar también en `dependencies.skills` y el linter avisa si la precarga supera 16 KB — regla token-diet) · `hooks:` (hooks con alcance del agente; único sitio para un hook de guardia — `command` con `${CLAUDE_PLUGIN_ROOT}` + fallback `find` en la misma línea, el linter comprueba que el fichero exista). No uses `isolation: worktree` nativo: choca con el opt-in `worktree` de `dev.json`.

**Skill** — `name` + `description` (misma regla de disparadores). El cuerpo es el **mapa**, no el manual:
≤ 200 líneas (aviso del linter; 250 = umbral duro en `tests/test_skill_size.py`) con propósito, disparadores,
pasos en 1-3 líneas, guardrails, «qué NO hace» y una **tabla de referencias**; el detalle va a
`skills/<nombre>/references/<tema>.md` enlazado con «lee X solo cuando llegues al paso Y» (regla «skills
cortas» de CONVENTIONS, ADR-008). Si adelgazas una existente: `tests/test_skill_size.py --diet-check <skill>
<ref>` → `0 párrafos perdidos`, y no renumeres pasos que otras piezas citan.

**Comando** — frontmatter YAML con `description` y `argument-hint` (lo interpreta Claude Code
para el picker de `/`), cuerpo con `$ARGUMENTS`, y fases con puertas explícitas (qué pregunta,
qué decide solo).

Reglas de cuerpo (las que más se incumplen):

1. **Determinismo**: cálculos, veredictos y parsing van en **scripts con tests y exit codes**
   (patrón `worklog`/`qa-gate`/`ledger-lint`/`usage-meter`/`task-brief`), NUNCA en prosa del
   agente. La prosa decide *cuándo* llamar al script; el script decide *el resultado*.
2. **Degradación, no bloqueo**: toda pieza opcional (medición, Jira, Confluence, constitución)
   degrada con un aviso claro y el ciclo SIGUE. Un `exit != 0` de una pieza opcional jamás
   detiene el trabajo del usuario.
3. **Rutas**: dentro de un kit, relativas (`dirname "$BASH_SOURCE"`); desde un `.md`, resolución
   `find` sobre `$PWD/.claude` y `$HOME/.claude` (regla 5). Nada de rutas absolutas del repo ni
   `${CLAUDE_PLUGIN_ROOT}` en markdown (no se expande).
4. **DRY de prompts**: si el mismo texto debe vivir en 2+ agentes, va a `agent-kits/shared/`
   con fallback de una línea en cada agente (instalaciones parciales).
5. **No reinventar**: antes de escribir un script nuevo, mira lo que ya existe con
   `ls agent-kits/*/ skills/*/scripts/ 2>/dev/null` — `usage-meter`, `task-brief` y `ledger-lint`
   viven en `agent-kits/shared/`; `qa-gate` y `coverage-check` en `agent-kits/qa/`; `worklog` en
   `skills/jira-sync/scripts/`.
6. **Codificación segura en cualquier consola, en las dos direcciones**: si el script imprime
   símbolos **o lee de `sys.stdin`**, copia tras los imports el snippet de 4 líneas que reconfigura
   `stdin`/`stdout`/`stderr` a UTF-8 con `errors="replace"` (LITERAL, a nivel de módulo, los scripts
   son standalone — CONVENTIONS regla 8, `GOT-005`); si no, revienta con `UnicodeEncodeError` al
   imprimir un símbolo o `UnicodeDecodeError` al leer un payload con emoji, en consola `cp1252` o con
   la salida a un pipe en Windows. **Que tu fuente sea ASCII pura no te libra**: quien lee depende
   del payload, no del fuente. Y si el script LANZA a otro y lee su salida, pásale
   `encoding="utf-8", errors="replace"`: los scripts del plugin escriben UTF-8 siempre, así que
   decodificarlos con el codec del locale revienta al padre. Las dos mitades las avisa
   `lint_plugin.py` y las prueba `tests/test_console_encoding.py`. En un `.sh`, el `python3 -c` en
   línea que lea `stdin` o imprima símbolos lleva delante `PYTHONIOENCODING=utf-8:replace`.

## Paso 3 — Validación (TDD-ish: la puerta se escribe ANTES de dar por hecha la pieza)

Orden estricto; no se avanza con un paso en rojo:

1. **Script nuevo → test nuevo primero.** Todo script determinista nace con su suite
   (`tests/test_<nombre>.py` para los del repo; junto al script si es de kit). Escribe el caso
   que HOY falla, míralo fallar, implementa, míralo pasar (evidencia estilo TDD:
   `RED: <test> falló con <error>`).
2. **Linter**: `python scripts/lint_plugin.py` — frontmatter completo, `model` válido, grafo
   `dependencies` sin ciclos ni referencias muertas, colisiones de nombres; avisa si la pieza no
   tiene caso positivo en `evals/cases/`, si su `description` pasa de 1.200 caracteres o si un
   `SKILL.md` pasa de 200 líneas (detalle a `references/`).
2-bis. **Evals de activación (checklist de pieza nueva):** `evals/cases/<kind>-<nombre>.json` con
   **≥ 1 caso positivo y 1 negativo** (en la práctica 2 positivos —uno `literal` con una frase de la
   description, otro `parafrasis`— y un negativo VECINO con `redirect`); `python3 evals/check.py`
   exit 0. La description es una promesa de activación: aquí se prueba (`evals/README.md`).
2-ter. **Tabla de racionalización si la pieza tiene DoD o veredicto:** justo antes de ese bloque,
   con el formato de `agent-kits/shared/rationalization-table.md` (6-8 filas en primera persona,
   acción concreta al cierre, ≤ 25 líneas). Añade la pieza a `tests/test_rationalization_tables.py`.
3. **Suites del repo** (misma invocación que la CI — las de `tests/` son suites-script, pytest
   NO las recoge):

   ```bash
   for t in tests/test_*.py; do python "$t" || exit 1; done   # suites del repo
   python -m pytest agent-kits/shared/ skills/*/scripts evals -q   # scripts shared + skills con suite propia + evals
   python3 evals/check.py                                     # cobertura y disparadores literales
   ```
4. **Auto-revisión adversarial** (piezas no triviales): lente de conformidad con CONVENTIONS
   (¿cumple cada regla citable?) + lente de defectos (¿qué input rompe el script? ¿qué pasa en
   instalación parcial?). Para iniciativas, esto lo hace `/dev-cycle`; para piezas sueltas,
   hazlo tú antes de entregar.

## Paso 4 — Documentación (sin esto la pieza NO está terminada)

| Pieza | Obligatorio |
|---|---|
| Agente nuevo | `docs/agents/<nombre>.md` + fila en tabla de agentes de `docs/README.md` + fila en `CLAUDE.md` |
| Skill nueva | fila en "Skills compartidas" de `docs/README.md` + fila en `CLAUDE.md` |
| Comando nuevo | fila en tabla de comandos de `docs/README.md` + fila en `CLAUDE.md` |
| Cualquiera que cambie un flujo | actualizar el diagrama en `docs/FLOWS.md` |
| Todo | entrada en **los dos** changelogs: `CHANGELOG.md` (EN, bajo `[Unreleased]`) y `CHANGELOG.es.md` (ES, bajo `[Sin publicar]`) — mismos encabezados de versión en ambos |

## Paso 5 — Cierre

- Si el trabajo es una iniciativa del roadmap: ledger en `docs/roadmap/<fecha>-<slug>/` con su
  bloque `generacion:` medido (usage-meter) y fila en `docs/roadmap/README.md`.
- Ritual de cierre de rama de `/dev-cycle` Fase 6 si hay rama (suites verdes → commits por
  tarea → resumen PR desde el ledger → integración → limpieza → estados finales).

## Anti-patrones (visto en revisiones reales de este repo)

- **Prosa que calcula**: "suma las horas y si supera X…" en un agente → script con test.
- **Ruta fija a un kit** (`.claude/agent-kits/...`) → se rompe como plugin; usa `find`.
- **Bloquear por una pieza opcional**: medición sin transcripción, Jira sin token → aviso + seguir.
- **Duplicar un fragmento de prompt** en dos agentes "porque es corto" → `agent-kits/shared/`.
- **`tools: *` o tools de más** en un agente → mínimos reales; el linter y la revisión lo cazan.
- **Skill sin disparadores** en la description → Claude no sabrá cuándo invocarla; termina
  siempre con "Úsala cuando el usuario diga …".
- **Hardcodear valores del proyecto consumidor** (tarifas, hosts, rutas) → config en `.claude/`
  del consumidor con default documentado.
