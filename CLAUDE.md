# CLAUDE.md

Contexto para Claude Code al trabajar en este repositorio.

## Qué es esto

Repositorio de **agentes custom** para Claude Code (bundle reutilizable + **plugin** instalable vía marketplace: `.claude-plugin/plugin.json` + `marketplace.json`). Se despliega como `.claude/` de un proyecto (ver `docs/INSTALL.md`). No es una aplicación. Por ser plugin, los agentes **no** usan rutas fijas a sus kits: las resuelven en runtime con `find` sobre `$PWD/.claude` y `$HOME/.claude` (regla 5 de `docs/CONVENTIONS.md`).

```
custom-agents/               (se despliega como .claude/)
├── agents/<nombre>.md       # definición de cada agente (uno por fichero)
├── commands/<nombre>.md     # orquestadores (/pm-cycle, /dev-cycle, …)
├── skills/<skill>/          # skills COMPARTIDAS: SKILL.md corto (≤ 200 líneas, mapa) + references/<tema>.md bajo demanda
├── agent-kits/<agente>/     # toolkits PRIVADOS por agente (shared/ = fragmentos y scripts comunes)
├── hooks/                   # PostToolUse · SubagentStop · SessionStart · SessionEnd (journal de sesión) — informan (systemMessage/additionalContext) o escriben la bitácora, no deciden; siempre exit 0
├── statusline/              # roadmap-statusline.sh (opt-in en /setup): modelo · coste sesión · ctx · progreso roadmap
├── scripts/                 # lint_plugin.py · release.py (release mecánico COMPLETO: changelog + checks + bump + chmod + commit/tag) · export-skills.py (paquete portable «solo skills» → dist/, ignorado)
├── tests/                   # suites del repo (corren en CI)
├── evals/                   # evals de ACTIVACIÓN: cases/<kind>-<nombre>.json por pieza · check.py (estático, CI) · run.py (local, claude -p)
├── *.yml.MANUAL-COPY        # ci.yml · release.yml · headless.yml (opcional: evals reales + hooks en sesión real, secret ANTHROPIC_API_KEY) → copia manual a .github/workflows/
├── github-templates.MANUAL-COPY/  # issue forms (bug · mejora · pieza-nueva) + PULL_REQUEST_TEMPLATE → copia manual a .github/ (test_ci_manual_copy vigila ambos árboles)
├── CONTRIBUTING.md          # cómo proponer una pieza (plugin-dev), checklist pre-PR, commits T-XX:/feat:/chore:, copias .MANUAL-COPY
└── docs/                    # TODA la documentación (README índice, CONVENTIONS, FLOWS, INSTALL, agents/)
```

## Reglas al trabajar aquí

| Regla | Resumen |
|---|---|
| Convenciones primero | Antes de crear/mover nada: `docs/CONVENTIONS.md`. Flujos visuales: `docs/FLOWS.md` (actualízalo si cambias un flujo). |
| Documentación en `docs/` | Nunca junto al código. Agente nuevo → `docs/agents/<nombre>.md` + fila en `docs/README.md`. |
| Bilingüe EN/ES | Inglés es el principal: `README.md` + `README.es.md`, `CHANGELOG.md` (EN, `[Unreleased]`) + `CHANGELOG.es.md` (ES, `[Sin publicar]`); docs clave con espejo en `docs/en/` (README, INSTALL, CONVENTIONS, FLOWS, observability). **Al cambiar uno, actualiza su espejo** en el mismo cambio. Los docs de agentes y el roadmap son solo ES. Los tokens parseados por máquina (estados `borrador/aprobada/…`, `generacion:`, `- **Tipo**:`) quedan en español también en la doc EN. |
| Nombres | Un agente = un nombre kebab-case único, igual en `agents/`, `agent-kits/` y `docs/agents/`; el `name:` del frontmatter coincide. |
| Compartido vs privado | Lo usan 2+ agentes → `skills/`; de uno solo → `agent-kits/<agente>/`; fragmentos de prompt repetidos → `agent-kits/shared/` (fuente única). |
| Un rol, un dueño | Cada responsabilidad del ciclo tiene EXACTAMENTE una pieza que decide y escribe su artefacto; el resto, si la toca, solo la lee. Un solape real se resuelve por **fusión (absorción)** en la pieza con más forma de "rol" (agente) o se **documenta explícitamente** como relación método/ejecutor o E2E/unitarios — nunca se deja implícito. Matriz completa: `docs/agents/ROLES.md`; decisión y casos: `ADR-011`. Guardarraíl heurístico: `lint_plugin.py` avisa si dos piezas declaran el MISMO disparador literal entrecomillado en su `description`. |
| Model tiering (dos capas) | Todo agente declara `model` (`haiku`/`sonnet`/`opus`/`inherit`) **y `effort`** (`low|medium|high|xhigh|max`; `medium` por defecto, `high` en los `opus`). Lo valida el linter. Override por proyecto en `dev.json` `modelos.<agente>` → `agent-kits/shared/model-tier.py` lo resuelve y los orquestadores pasan `model` al Agent tool (`effort` de dev.json es informativo; `@agente` manual → frontmatter). ADR-009. |
| Skills cortas | `skills/<skill>/SKILL.md` es el **mapa** (≤ 200 líneas: propósito, disparadores, pasos en 1-3 líneas, guardrails, «qué NO hace», tabla de referencias); el detalle va a `skills/<skill>/references/<tema>.md` con «lee X solo al llegar al paso Y». Linter avisa > 200, `tests/test_skill_size.py` falla > 250; al adelgazar, `--diet-check` → 0 párrafos perdidos (ADR-008). |
| Linter + tests | `python scripts/lint_plugin.py` (frontmatter, grafo `dependencies` sin ciclos, colisiones, `hooks/hooks.json` con commands existentes y ejecutables; avisa si una pieza no tiene caso positivo en `evals/cases/` o su description pasa de 1.200 caracteres) + `python evals/check.py` (toda pieza con ≥ 2 positivos + 1 negativo y el literal casando con la description REAL) + suites de `tests/` antes de publicar. Opcional con secret: `headless.yml` (evals reales + hooks en sesión real). **Publicar = `python3 scripts/release.py X.Y.Z`** (nunca a mano): mueve `[Unreleased]`/`[Sin publicar]` a la sección de la versión en los dos CHANGELOG, corre lint + evals, exige copias `.MANUAL-COPY` al día, corrige `.sh` en `100644`, bump en 3 sitios, commit + tag; `--dry-run` antes, `--check` después (LES-012). |
| Dependencias | Bloque `dependencies:` en el frontmatter del agente (skills/kits/agents) — fuente de verdad del grafo. |
| Rutas en scripts | Relativas entre sí (`dirname "$BASH_SOURCE"`); nunca absolutas del repo. |
| Determinismo | Los cálculos y veredictos van en **scripts con tests y exit codes** (patrón `worklog`/`qa-gate`/`ledger-lint`/`usage-meter`/`task-brief`/`progress-report`/`guardrail-check`/`scope-check`/`review-lens-select`/`skill-index`), no en prosa del agente. Cada `T-XX` del ledger lleva **`Verificación`** (`comando → resultado esperado`; `verificacion: obligatoria` en el frontmatter → `ledger-lint` falla si falta; `task-brief.py` la inyecta; el implementer la ejecuta y pega la salida). Las excusas típicas antes de saltarse una puerta se desarman con una **tabla de racionalización** (`agent-kits/shared/rationalization-table.md`) justo antes del DoD/veredicto de `implementer`, `adversarial-review` y `qa`. Hooks: los globales (`hooks/hooks.json`) solo informan; un deny solo vive en el frontmatter `hooks:` de un agente (ADR-007). |
| Hooks | Informan, no deciden: `hooks/` emite `systemMessage`/`hookSpecificOutput.additionalContext` y SIEMPRE exit 0 (sin `python3` → silencio). Progreso en vivo = `agent-kits/shared/progress-report.py` sobre el ledger canónico; **índice de piezas** al arrancar/retomar/compactar = `agent-kits/shared/skill-index.py` (≤ 45 líneas, caché por hash, `dev.json` `sesion.indice`) — informativo, para que la skill/comando correcto se dispare (ver `docs/observability.md`). |
| Degradación, no bloqueo | Las piezas opcionales (medición, constitución, Jira, Confluence) degradan con aviso; NUNCA bloquean el ciclo. |
| Memoria técnica | `docs/knowledge/` (siempre activa, sin opt-in): `adr/ADR-NNN-<slug>.md`, `gotchas/GOT-NNN-<slug>.md`, `lessons/LES-NNN-<agente>-<slug>.md`, con `README.md` como única puerta de entrada (índice). Lectura selectiva por área (`agent-kits/shared/knowledge-check.md`: evaluator/planner/implementer/qa/documenter); escritura con umbral anti-burocracia (`agent-kits/shared/knowledge-write.md`: ADR solo si cierra alternativa y afecta 2+ piezas, gotcha solo si costó ≥1 ciclo de depuración). **Journal de sesión** (`docs/knowledge/journal/`, memoria EPISÓDICA no curada, ADR-010): el hook `SessionEnd` escribe una entrada determinista por sesión con `agent-kits/shared/journal.py` (idempotente por `session_id`; `dev.json` `sesion.journal: false` la apaga) y `SessionStart` (`startup\|resume`) reinyecta la última (≤ 25 líneas); excluido de Confluence; lo que merezca doctrina se promueve a ADR/gotcha/lección. Sin resumen por IA: la salida de los hooks en `SessionEnd` se ignora por contrato. |

## Agentes

| Agente | Rol (doc en `docs/agents/<nombre>.md`) |
|---|---|
| **analyst** | Toma de requerimientos y descubrimiento → `spec.md` aprobada (formato fijo, plantilla del evaluator). Puerta de entrada única al descubrimiento (`ADR-011`: absorbe la skill `discovery`, retirada). No estima ni planifica. |
| **evaluator** | Presupuesta la spec (h/€/tokens, riesgos, veredicto), calibrando con `CALIBRATION.md`. Handoff a planner. |
| **architect** | Opt-in tras el go: 2-3 opciones de diseño con trade-offs → `design.md` (`borrador · aprobado · obsoleto`), validadas con el usuario por trozos; ADR `propuesta`; enlaza spec ↔ design ↔ plan. Escribe SOLO `design.md`, `design:` en spec/plan y `docs/knowledge/adr/`. No estima ni planifica. |
| **planner** | Plan ejecutable: `improvement-plan.md` + `tasks.md` (fases, T-XX, criterios, presupuesto por fase). |
| **reviewer** | Una lente de `adversarial-review` (A/B/C) en contexto fresco, **solo lectura por construcción** (`tools: Read, Grep, Glob, Bash`); salida estructurada que la skill fusiona. La skill lo despacha por nombre con `model-tier.py`; fallback a subagente genérico. |
| **implementer** | Único que toca código. Fase a fase sobre rama/worktree; `tasks.md` = ledger canónico; mide cada tarea con usage-meter; TDD/worktree según `.claude/dev.json`. Guardrails **impuestos por hook de guardia** propio (`guardrail-check.py`: solo `tasks.md` en `docs/roadmap/`, rama de trabajo, git no destructivo; `dev.json` `guardrails`) y alcance del diff por `scope-check.py` (DoD). Handoff a qa. |
| **qa** | E2E Playwright solo local; veredicto por `qa-gate.py`; cobertura criterios↔tests por `coverage-check.py` (incl. `[GWT]`); informe md+pdf. |
| **documenter** | Documentación técnica/producto del proyecto bajo `docs/`, derivada del repo. Una vez al cierre del ciclo. No toca `docs/roadmap/` ni `docs/security-scan/`. |
| **nemesis** | Auditoría de seguridad: SAST (skill `cybersecurity`) + DAST **solo hosts locales/privados** (guardrail `lib-guardrail.sh`, no negociable). |

**Cadena de artefactos (carpeta única por iniciativa):** `docs/roadmap/<fecha>-<slug>/` con `spec.md → evaluation.md → [design.md] → improvement-plan.md + tasks.md (+ testing/ + retro.md)`, enlazados bidireccionalmente (regla 7 de CONVENTIONS). `tasks.md` es el **ledger canónico** (regla 8): cualquier implementador lo marca; otros registros son espejo. Cada artefacto lleva su **coste de generación medido** en el frontmatter (`generacion:`, script `usage-meter.py`; fechas = contexto, tokens = medida, horas = tokens × ratio calibrado).

## Comandos (orquestación)

Invocan a los agentes **por nombre** y con puertas de control sobre la carpeta de la iniciativa.

| Comando | Qué hace |
|---|---|
| `/pm-cycle <objetivo>` | Rol producto: spec → evaluación → **puerta go/no-go** y cierra. En go, ofrece `architect` (diseño opt-in) y el handoff a /dev-cycle. Salidas opt-in: brief PDF, épica en Jira. |
| `/dev-cycle <objetivo> [rapido\|completo] [--superpowers]` | Ciclo de desarrollo. **Cadena nativa SIEMPRE por defecto** (motor SDD externo solo bajo petición explícita con el flag; ver `commands/dev-cycle.md` Modo A). Puerta de entrada: flujo completo vs vía rápida (la rápida salta el papeleo PM pero conserva la revisión de dos lentes y qa). Disciplina opt-in en `.claude/dev.json`: `tdd` (skill `tdd`, fuente única de RED-GREEN-REFACTOR con evidencia del rojo), `worktree`, `subagentes` (una tarea = un subagente fresco con brief de `task-brief.py`, estados DONE/DONE_WITH_CONCERNS/NEEDS_CONTEXT/BLOCKED, revisor con severidades). Bucles acotados a 3; al 3.er rojo de qa, skill `debug-root-cause` antes de preguntar. |
| `/setup` | Onboarding en una pasada: `rates.json`, opt-ins Confluence/Jira, constitución (`docs/CONSTITUTION.md`), `dev.json` (disciplina, statusline 5-bis, lente de seguridad de la revisión 5-ter). Idempotente. |
| `/doctor` | Diagnóstico de la INSTALACIÓN (solo lectura, sin red): herramientas, plugin + hooks registrados, statusline, configs de `.claude/` y estado del trabajo. Veredicto ✅/⚠️/❌ por línea con el comando que lo arregla; `--json`. `agent-kits/shared/doctor.py`, exit 1 si hay ❌. Primera parada cuando algo «no salta». |
| `/pm-backlog` · `/roadmap-status` · `/roadmap-metrics` · `/roadmap-live` · `/roadmap-brief` | Cartera y visibilidad (solo lectura): backlog priorizado · dashboard · real vs estimado + coste de proceso medido · Jira en vivo · one-pager PDF. |
| `/spec-drift [slug]` | Gobernanza: deriva spec↔código de las specs `implementada` (vigente/derivado/no-verificable con evidencia) → `docs/roadmap/DRIFT.md`. Solo lectura; la corrección va por /pm-cycle. |
| `/retro <slug>` | Cierre de aprendizaje: real vs estimado + causas + **ratio tokens/hora medido** → `docs/roadmap/CALIBRATION.md` (lo leen evaluator y usage-meter). |
| `/confluence-pull` | Confluence → `docs/` local (PM sin git). |

**Revisión adversarial (skill `adversarial-review`, fuente única del método; la invocan /dev-cycle Fase 3 y quick-implement, y se usa a demanda):** lentes en paralelo con contexto fresco despachadas al agente `reviewer` (solo lectura; fallback a subagente genérico) — A: conformidad con spec/plan/constitución (salida estructurada por criterio ✓/✗, gaps con cita); B: solo defectos de corrección; C: seguridad del diff, **condicional** (`review-lens-select.py`: rutas/líneas sensibles; `dev.json` `revision.lenteSeguridad`); **D: rendimiento del diff, también condicional** (mismo script por heurística de rutas + patrones N+1, `await`/regex en bucle, `sleep` bloqueante; `dev.json` `revision.lenteRendimiento`). Bucle reviewer→implementer acotado a 3 (el contador y el worklog `[revisión]` por intento son del orquestador); traza «Revisión de dos lentes — intento N» en el ledger; comentario en Jira opt-in.

## Skills compartidas

| Skill | Para qué (usuarios) |
|---|---|
| `jira-sync` | Plan → Jira (issue por tarea o por fase, tipo por jerarquía, idempotente); worklog al completar (IA+supervisión, tope jornada + banco, `worklog.py`); publica el resultado del revisor. Opt-in `.claude/jira.json`. (planner, implementer, /dev-cycle) |
| `confluence-publish` / `confluence-pull` | Espejo `docs/` ↔ Confluence, opt-in, idempotente por manifiesto; nunca `docs/security-scan/`. (evaluator, planner, qa, documenter / comando) |
| `roadmap-dashboard` | Escaneo de `docs/roadmap/` → HTML/md/JSON + métricas real-vs-estimado y coste de proceso (`build_dashboard.py`). (/roadmap-status, /pm-backlog, /roadmap-metrics) |
| `debug-root-cause` | Causa raíz en 4 fases con evidencia; prohibido arreglar a ciegas. (/dev-cycle al 3.er rojo; a demanda) |
| `adversarial-review` | Revisión adversarial del diff: lentes A (spec/plan) + B (corrección) + C seguridad condicional (`review-lens-select.py`, con tests); fusión, Critical/Important/Minor, bucle acotado, rebate con evidencia, traza en el ledger. Fuente única del método. (/dev-cycle Fase 3, quick-implement; a demanda «revísame este diff») |
| `rates-verify` | Actualiza `precioTokens` de `rates.json` desde la doc oficial, con fecha. (evaluator, /setup) |
| `plugin-dev` | Meta-skill para desarrollar ESTE plugin: árbol de decisión de piezas, frontmatter/tiering/tools mínimos, validación TDD-ish, doc obligatoria, anti-patrones; plantillas de agente/skill/comando. (crear/modificar piezas del plugin) |
| `quick-implement` | Atajo en lenguaje natural a la vía rápida de `/dev-cycle` (delegando en su fuente única): filtro de idoneidad + ledger + puertas. (peticiones «implementa X rápido» sin barra) |
| `tdd` | Fuente única de RED-GREEN-REFACTOR: ley dura, evidencia `RED:` en el ledger, qué NO es TDD, `TDD n/a`, tabla de racionalización; `references/by-stack.md` + `anti-patterns.md`. (implementer con `dev.json` `tdd: true`, subagentes vía `task-brief.py`; a demanda) |
| `code-health` | Informe DETERMINISTA de salud del código (`scripts/code-health.py`, 14 tests): duplicados por shingles (`fichero:línea`, %), tamaño/anidamiento/funciones largas, hotspots (`git log` × tamaño), TODO/FIXME con antigüedad; MD/`--json`/`--baseline`; sin git omite con aviso. No refactoriza ni busca vulnerabilidades. (evaluator P2 opt-in, planner deuda, /roadmap-brief; a demanda) |
| `dependency-upgrade` | Inventario de dependencias sin ejecutar nada (`scripts/deps-inventory.py`, 10 tests): 7 manifiestos + lockfiles, declarada/bloqueada/`latest` (solo del `outdated` oficial, nunca inventado), salto patch/minor/major; changelog upstream por major → `spec.md` «upgrade-…» con la plantilla del evaluator. Vulnerabilidades → nemesis. (a demanda; handoff evaluator → planner) |
| `changelog-sync` | Entradas `[Unreleased]` (EN) / `[Sin publicar]` (ES) de los DOS CHANGELOG derivadas de los ledgers **cerrados** (`estado: completado`): un bullet por `T-XX`, categoría `Added/Changed/Fixed` deducida o declarada (`changelog:`), idempotente por slug. No abre la sección de versión (eso es `release.py`) ni inventa alcance. (`/dev-cycle` Fase 6, `quick-implement`, precondición de `release.py`; a demanda) |
| `unit-tests` | Pirámide de pruebas + **gate de cobertura** determinista y agnóstico de stack (`coverage-gate.py`: pytest/jest/vitest/phpunit/go, herramienta OFICIAL solo si está en PATH, `--changed-only`; sin herramienta/stack → exit 2 y aviso, nunca un % inventado). Skill **compartida, no un agente nuevo** (LES-013). (implementer P5 con `dev.json` `tests.coberturaMinima`, qa informativo, Lente A; a demanda) |
| `api-contract` | Flujo **contract-first** para OpenAPI 3.x sin dependencias (`openapi-lint.py`): estructura mínima (`operationId` único, 2xx + 4xx/5xx, `$ref` internos, parámetros con `schema`/`content`) y `--diff <old> <new>` con los cambios **rompedores** separados de los compatibles. (planner, Lente A si el diff toca la spec; a demanda) |
| `cybersecurity` · `to-pdf` | SAST 8 dimensiones (nemesis) · conversión a PDF (qa, /roadmap-brief). |

**Configs en `.claude/` del proyecto consumidor** (mapa completo: regla 9 de CONVENTIONS): `rates.json` (presupuesto), `jira.json`/`jira-state.json`, `confluence.json`/`confluence-state.json`, `dev.json` (tdd/worktree/subagentes/constitución/`revision.lenteSeguridad`/`revision.lenteRendimiento`/`tests.coberturaMinima`/`sesion.indice`/`sesion.journal`/`modelos`), `usage-state.json` (marcadores del meter).

## Invariante de seguridad (no negociable)

`nemesis` hace pentest **activo** solo contra hosts **locales/privados** (`localhost`, `127.0.0.1`, `*.test`, redes privadas), impuesto por `agent-kits/nemesis/tools/lib-guardrail.sh`. Nunca puentees el guardrail ni apuntes a sistemas de terceros. La explotación activa (`sqlmap`) requiere opt-in explícito del usuario.

## Añadir un agente nuevo (resumen)

1. Nombre único kebab-case → `agents/<nombre>.md` con frontmatter (incl. `model` y `dependencies`).
2. Scripts propios → `agent-kits/<nombre>/`; reutilizables → `skills/`.
3. Doc en `docs/agents/<nombre>.md` + fila en `docs/README.md` (+ FLOWS si cambia un flujo).
4. `python scripts/lint_plugin.py` y suites en verde.

Detalle completo en `docs/CONVENTIONS.md`.
