# Reglas de este repositorio (custom-agents)

Léela **solo al trabajar en este repositorio** (proponer o cambiar un agente, comando, skill, kit o
hook del propio plugin). En el proyecto de otra persona no aplica nada de esto: allí rige `SKILL.md`.

La regla que gobierna todo: **las convenciones se LEEN antes de crear, no se recuerdan de memoria.**
Abre `docs/CONVENTIONS.md` (y `docs/FLOWS.md` si tocas un flujo) y `CONTRIBUTING.md` antes de
cualquier pieza nueva; esta referencia es el mapa y CONVENTIONS es la ley.

Resolución de rutas (regla 5 de CONVENTIONS, nunca rutas fijas): los agentes no usan rutas fijas a sus
kits, las resuelven en tiempo de ejecución con `find` sobre `$PWD/.claude` y `$HOME/.claude` (y las
cuatro raíces de Codex y OpenCode).

## Árbol de decisión de piezas del plugin

| Si lo que necesitas es… | Entonces es… | Va en… |
|---|---|---|
| Un rol autónomo con prompt propio que se invoca por nombre | **agente** | `agents/<nombre>.md` |
| Un orquestador que el usuario lanza (`/algo`) y coordina agentes y puertas | **comando** | `commands/<nombre>.md` |
| Capacidad reutilizable por 2+ agentes | **skill compartida** | `skills/<nombre>/SKILL.md` |
| Script o plantilla de UN solo agente | **kit privado** | `agent-kits/<agente>/` |
| Trozo de prompt idéntico en varios agentes (no invocable) | **fragmento shared** | `agent-kits/shared/` |
| Reacción automática a eventos, para INFORMAR | **hook informativo** | `hooks/` + registro en `hooks/hooks.json`; informan, no deciden: `systemMessage`/`additionalContext`, SIEMPRE exit 0, silencio sin `python3` |
| Impedir que UN agente haga algo (deny) | **hook de guardia** | dispatcher previo por identidad nativa (`agent-kits/shared/native-guardrail.py` + `guardrail-check.py`), regla 8 de CONVENTIONS y ADR-023 |

**Busca dueño antes de crear:** `python3 agent-kits/shared/skill-index.py --no-cache`, `/plugin-catalog`
y la matriz `docs/agents/ROLES.md`. Si existe dueño, la propuesta es una línea en él (ADR-011). Si la idea
viene de una skill o plugin externo, compárala antes con `research-first`.

## Nombre, frontmatter y colisiones

- Kebab-case, único en TODO el repo (`agents/`, `agent-kits/`, `skills/`, `commands/`); el `name:` coincide con
  el fichero o carpeta. Las skills se nombran por función, nunca por agente. El linter avisa de nombres
  genéricos (`GENERIC_NAME_TOKENS` en `lint_plugin.py`).
- **Agente:** `name` · `description` con disparadores · `tools` mínimos · `model` + `effort` **obligatorios**
  (`haiku`/`sonnet` → `effort: medium`; `opus` → `effort: high`; override por proyecto en `dev.json` `modelos`,
  resuelto por `agent-kits/shared/model-tier.py`) · `dependencies` (skills, kits y agentes que EXISTEN, sin
  ciclos). Nativos opcionales: `skills:` (precarga completa, aviso si supera 16 KB) y `hooks:` (alcance de una
  copia local; los agentes de plugin lo ignoran). No uses `isolation: worktree`: choca con el opt-in `worktree`.
- **Skill:** SKILL.md ≤ 200 líneas (aviso del linter; 250 = umbral duro en `tests/test_skill_size.py`), detalle a
  `references/<tema>.md`. Al adelgazar una existente, `tests/test_skill_size.py --diet-check` → `0 párrafos
  perdidos`.
- **Comando:** frontmatter con `description` y `argument-hint`, cuerpo con `$ARGUMENTS` y fases con puertas.

## Reglas de cuerpo

1. **Determinismo:** cálculos, veredictos y parsing en scripts con tests y exit codes (`worklog`, `qa-gate`,
   `ledger-lint`, `usage-meter`, `task-brief`); la prosa decide cuándo llamar, el script el resultado.
2. **Degradación, no bloqueo:** toda pieza opcional (medición, Jira, Confluence, constitución) degrada con aviso.
3. **Rutas:** dentro de un kit, relativas (`dirname "$BASH_SOURCE"`); desde un `.md`, la resolución `find`;
   nada de rutas absolutas del repo ni `${CLAUDE_PLUGIN_ROOT}` en markdown.
4. **DRY de prompts:** el mismo texto en 2+ agentes va a `agent-kits/shared/` con fallback de una línea.
5. **No reinventar:** mira `agent-kits/*/` y `skills/*/scripts/` antes de escribir un script.
6. **Codificación segura:** si un script imprime símbolos o lee `sys.stdin`, copia el snippet de reconfiguración
   UTF-8 de CONVENTIONS regla 8 (`GOT-005`); avisa `lint_plugin.py` y prueba `tests/test_console_encoding.py`.

## Validación (la puerta se escribe ANTES de dar por hecha la pieza)

1. **Script nuevo → test nuevo primero** (`RED: <test> falló con <error>`).
2. `lint_plugin.py` (carpeta `scripts/` del repo): frontmatter, grafo `dependencies` sin ciclos, colisiones, `description` ≤ 1.200
   caracteres (1.024 en las skills, o OpenCode no las carga), citas de rutas y `/comandos` inexistentes.
3. **Evals de activación:** `evals/cases/<kind>-<nombre>.json` con ≥ 2 positivos (uno `literal` con una frase de
   la description, otro `parafrasis`) y 1 negativo vecino con `redirect`; `python evals/check.py` → exit 0.
4. **Tabla de racionalización** si la pieza tiene DoD o veredicto (`agent-kits/shared/rationalization-table.md`),
   y añadirla a `tests/test_rationalization_tables.py`.
5. **Saneado** si la pieza viene de otro entorno: sin rutas absolutas ni de usuario, sin tokens (`redactar()` de
   `agent-kits/shared/redact.py` no debe cambiar nada), sin nombres de persona, cliente o empresa, sin datos de salud
   o finanzas ni logs de sistemas privados.
6. **Suites del repo** (`for t in tests/test_*.py; do python "$t" || exit 1; done` y `python -m pytest agent-kits/shared/
   skills/*/scripts evals -q`) y, si tocaste `agents/`, `commands/` o `hooks/`, **regenera lo generado**:
   `export-interop.py` y luego `export-interop.py --check` (exit 0), ambos de la carpeta `scripts/`. Lo de `interop/`,
   `.codex-plugin/` y `.agents/plugins/` no se edita a mano.
7. **Auto-revisión adversarial** (piezas no triviales): conformidad con CONVENTIONS y defectos. Para iniciativas la
   hace `/dev-cycle`.

## Documentación (la pieza no está terminada sin esto)

| Pieza | Obligatorio |
|---|---|
| Agente nuevo | `docs/agents/<nombre>.md`, fila en la tabla de agentes de `docs/README.md` y en `CLAUDE.md` |
| Skill nueva | fila en «Skills compartidas» de `docs/README.md` y en `CLAUDE.md` |
| Comando nuevo | fila en la tabla de comandos de `docs/README.md` y en `CLAUDE.md` |
| Cualquiera que cambie un flujo | actualizar el diagrama en `docs/FLOWS.md` |
| Todo | `CHANGELOG.md` (EN, bajo `[Unreleased]`) y `CHANGELOG.es.md` (ES, bajo `[Sin publicar]`) |

Bilingüe EN/ES: al cambiar un documento con espejo en `docs/en/`, actualiza el espejo en el mismo cambio.
Publicar es `release.py X.Y.Z` de la carpeta `scripts/` (nunca a mano). Cómo proponer una pieza, el checklist pre-PR y los
commits (`T-XX:`/`feat:`/`chore:`): `CONTRIBUTING.md`.

## Cierre

Si el trabajo es una iniciativa del roadmap: ledger en `docs/roadmap/<fecha>-<slug>/` con su bloque
`generacion:` medido (`usage-meter`) y fila en `docs/roadmap/README.md`; ritual de cierre de rama de
`/dev-cycle` Fase 6 si hay rama.

## Capas de diagnóstico → piezas de este repo

Para `architecture-diagnostics.md`: dónde vive cada capa en este plugin.

| Capa | Dónde vive aquí |
|---|---|
| Ensamblado de instrucciones | prompt del agente, fragmentos de `agent-kits/shared/`, skills precargadas, `CLAUDE.md`, contexto de `SessionStart` |
| Memoria | `docs/knowledge/`, journal |
| Destilación | compactación, resumen del journal |
| Recuperación | `knowledge-find.py`, `skill-index.py`, `capability-route.py` |
| Selección de herramienta | descripciones de skills, agentes y comandos; casos de `evals/cases/` |
| Ejecución e interpretación | scripts de kits y skills (`doctor.py` como patrón de siguiente paso) |
| Formato | parsers de ledger, frontmatter y cabeceras |
| Transporte | stdout/stderr, JSON de hooks, codificación |
| Persistencia | ledger, `outbox.py`, ficheros de estado (`local-state.py`) |

## Anti-patrones vistos en revisiones de este repo

- **Ruta fija a un kit** (`.claude/agent-kits/...`) → se rompe como plugin; usa `find`.
- **Debilitar una guardia por coste o latencia** (un deny previo pasa a aviso posterior, se quita un patrón, se
  baja un umbral) → solo con ADR o aprobación; antes, mide y acelera el script.
- **Duplicar un fragmento de prompt** en dos agentes «porque es corto» → `agent-kits/shared/`.
- **Líneas que no cambian nada:** si al quitar una línea de un agente o skill hace lo mismo, se borra (ADR-008).
- **Hardcodear valores del proyecto consumidor** (tarifas, hosts, rutas) → config en `.claude/` con default
  documentado.
