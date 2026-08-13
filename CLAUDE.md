# CLAUDE.md

Contexto para Claude Code al trabajar en este repositorio.

## Qué es esto

Repositorio de **agentes custom** para Claude Code (bundle reutilizable + **plugin** instalable vía marketplace: `.claude-plugin/plugin.json` + `marketplace.json`). Se despliega como `.claude/` de un proyecto (ver `docs/INSTALL.md`). No es una aplicación. Por ser plugin, los agentes **no** usan rutas fijas a sus kits: las resuelven en runtime con `find` sobre `$PWD/.claude` y `$HOME/.claude` (regla 5 de `docs/CONVENTIONS.md`).

```
custom-agents/               (se despliega como .claude/)
├── agents/<nombre>.md       # definición de cada agente (uno por fichero)
├── commands/<nombre>.md     # orquestadores (/pm-cycle, /dev-cycle, …)
├── skills/<skill>/          # skills COMPARTIDAS
├── agent-kits/<agente>/     # toolkits PRIVADOS por agente (shared/ = fragmentos y scripts comunes)
├── hooks/                   # PostToolUse no bloqueantes
├── scripts/                 # lint_plugin.py, release.py
├── tests/                   # suites del repo (corren en CI)
└── docs/                    # TODA la documentación (README índice, CONVENTIONS, FLOWS, INSTALL, agents/)
```

## Reglas al trabajar aquí

| Regla | Resumen |
|---|---|
| Convenciones primero | Antes de crear/mover nada: `docs/CONVENTIONS.md`. Flujos visuales: `docs/FLOWS.md` (actualízalo si cambias un flujo). |
| Documentación en `docs/` | Nunca junto al código. Agente nuevo → `docs/agents/<nombre>.md` + fila en `docs/README.md`. |
| Bilingüe EN/ES | Inglés es el principal: `README.md` (EN) + `README.es.md` (ES); docs clave con espejo en `docs/en/` (README, INSTALL, CONVENTIONS, FLOWS, observability). **Al cambiar uno, actualiza su espejo** en el mismo cambio. Los docs de agentes y el roadmap son solo ES. Los tokens parseados por máquina (estados `borrador/aprobada/…`, `generacion:`, `- **Tipo**:`) quedan en español también en la doc EN. |
| Nombres | Un agente = un nombre kebab-case único, igual en `agents/`, `agent-kits/` y `docs/agents/`; el `name:` del frontmatter coincide. |
| Compartido vs privado | Lo usan 2+ agentes → `skills/`; de uno solo → `agent-kits/<agente>/`; fragmentos de prompt repetidos → `agent-kits/shared/` (fuente única). |
| Model tiering | Todo agente declara `model` (`haiku`/`sonnet`/`opus`/`inherit`). Lo valida el linter. |
| Linter + tests | `python scripts/lint_plugin.py` (frontmatter, grafo `dependencies` sin ciclos, colisiones) + suites de `tests/` antes de publicar. |
| Dependencias | Bloque `dependencies:` en el frontmatter del agente (skills/kits/agents) — fuente de verdad del grafo. |
| Rutas en scripts | Relativas entre sí (`dirname "$BASH_SOURCE"`); nunca absolutas del repo. |
| Determinismo | Los cálculos y veredictos van en **scripts con tests y exit codes** (patrón `worklog`/`qa-gate`/`ledger-lint`/`usage-meter`/`task-brief`), no en prosa del agente. |
| Degradación, no bloqueo | Las piezas opcionales (medición, constitución, Jira, Confluence) degradan con aviso; NUNCA bloquean el ciclo. |

## Agentes

| Agente | Rol (doc en `docs/agents/<nombre>.md`) |
|---|---|
| **analyst** | Toma de requerimientos → `spec.md` aprobada (formato fijo, plantilla del evaluator). No estima ni planifica. |
| **evaluator** | Presupuesta la spec (h/€/tokens, riesgos, veredicto), calibrando con `CALIBRATION.md`. Handoff a planner. |
| **planner** | Plan ejecutable: `improvement-plan.md` + `tasks.md` (fases, T-XX, criterios, presupuesto por fase). |
| **implementer** | Único que toca código. Fase a fase sobre rama/worktree; `tasks.md` = ledger canónico; mide cada tarea con usage-meter; TDD/worktree según `.claude/dev.json`. Handoff a qa. |
| **qa** | E2E Playwright solo local; veredicto por `qa-gate.py`; cobertura criterios↔tests por `coverage-check.py` (incl. `[GWT]`); informe md+pdf. |
| **documenter** | Documentación técnica/producto del proyecto bajo `docs/`, derivada del repo. Una vez al cierre del ciclo. No toca `docs/roadmap/` ni `docs/security-scan/`. |
| **nemesis** | Auditoría de seguridad: SAST (skill `cybersecurity`) + DAST **solo hosts locales/privados** (guardrail `lib-guardrail.sh`, no negociable). |
| **pdfy** | Markdown/HTML/Word → PDF moderno (skill `to-pdf`). |

**Cadena de artefactos (carpeta única por iniciativa):** `docs/roadmap/<fecha>-<slug>/` con `spec.md → evaluation.md → improvement-plan.md + tasks.md (+ testing/ + retro.md)`, enlazados bidireccionalmente (regla 7 de CONVENTIONS). `tasks.md` es el **ledger canónico** (regla 8): cualquier implementador lo marca; otros registros son espejo. Cada artefacto lleva su **coste de generación medido** en el frontmatter (`generacion:`, script `usage-meter.py`; fechas = contexto, tokens = medida, horas = tokens × ratio calibrado).

## Comandos (orquestación)

Invocan a los agentes **por nombre** y con puertas de control sobre la carpeta de la iniciativa.

| Comando | Qué hace |
|---|---|
| `/pm-cycle <objetivo>` | Rol producto: spec → evaluación → **puerta go/no-go** y cierra. En go, ofrece handoff a /dev-cycle. Salidas opt-in: brief PDF, épica en Jira. |
| `/dev-cycle <objetivo> [rapido\|completo] [--superpowers]` | Ciclo de desarrollo. **Cadena nativa SIEMPRE por defecto** (superpowers solo bajo petición explícita). Puerta de entrada: flujo completo vs vía rápida (la rápida salta el papeleo PM pero conserva la revisión de dos lentes y qa). Disciplina opt-in en `.claude/dev.json`: `tdd` (RED-GREEN-REFACTOR con evidencia del rojo), `worktree`, `subagentes` (una tarea = un subagente fresco con brief de `task-brief.py`, estados DONE/DONE_WITH_CONCERNS/NEEDS_CONTEXT/BLOCKED, revisor con severidades). Bucles acotados a 3; al 3.er rojo de qa, skill `debug-root-cause` antes de preguntar. |
| `/setup` | Onboarding en una pasada: `rates.json`, opt-ins Confluence/Jira, constitución (`docs/CONSTITUTION.md`), `dev.json`. Idempotente. |
| `/pm-backlog` · `/roadmap-status` · `/roadmap-metrics` · `/roadmap-live` · `/roadmap-brief` | Cartera y visibilidad (solo lectura): backlog priorizado · dashboard · real vs estimado + coste de proceso medido · Jira en vivo · one-pager PDF. |
| `/spec-drift [slug]` | Gobernanza: deriva spec↔código de las specs `implementada` (vigente/derivado/no-verificable con evidencia) → `docs/roadmap/DRIFT.md`. Solo lectura; la corrección va por /pm-cycle. |
| `/retro <slug>` | Cierre de aprendizaje: real vs estimado + causas + **ratio tokens/hora medido** → `docs/roadmap/CALIBRATION.md` (lo leen evaluator y usage-meter). |
| `/confluence-pull` | Confluence → `docs/` local (PM sin git). |

**Revisión adversarial (en /dev-cycle):** dos lentes en paralelo con contexto fresco — A: conformidad con spec/plan/constitución (salida estructurada por criterio ✓/✗, gaps con cita); B: solo defectos de corrección. Bucle reviewer→implementer acotado a 3; resultado publicable en Jira (comentario por criterio + worklog `[revisión]` por intento).

## Skills compartidas

| Skill | Para qué (usuarios) |
|---|---|
| `jira-sync` | Plan → Jira (issue por tarea o por fase, tipo por jerarquía, idempotente); worklog al completar (IA+supervisión, tope jornada + banco, `worklog.py`); publica el resultado del revisor. Opt-in `.claude/jira.json`. (planner, implementer, /dev-cycle) |
| `confluence-publish` / `confluence-pull` | Espejo `docs/` ↔ Confluence, opt-in, idempotente por manifiesto; nunca `docs/security-scan/`. (evaluator, planner, qa, documenter / comando) |
| `roadmap-dashboard` | Escaneo de `docs/roadmap/` → HTML/md/JSON + métricas real-vs-estimado y coste de proceso (`build_dashboard.py`). (/roadmap-status, /pm-backlog, /roadmap-metrics) |
| `discovery` | Entrevista guiada idea→spec sólida antes de evaluar. (analyst, /pm-cycle) |
| `debug-root-cause` | Causa raíz en 4 fases con evidencia; prohibido arreglar a ciegas. (/dev-cycle al 3.er rojo; a demanda) |
| `rates-verify` | Actualiza `precioTokens` de `rates.json` desde la doc oficial, con fecha. (evaluator, /setup) |
| `plugin-dev` | Meta-skill para desarrollar ESTE plugin: árbol de decisión de piezas, frontmatter/tiering/tools mínimos, validación TDD-ish, doc obligatoria, anti-patrones; plantillas de agente/skill/comando. (crear/modificar piezas del plugin) |
| `cybersecurity` · `to-pdf` | SAST 8 dimensiones (nemesis) · conversión a PDF (pdfy, qa). |

**Configs en `.claude/` del proyecto consumidor** (mapa completo: regla 9 de CONVENTIONS): `rates.json` (presupuesto), `jira.json`/`jira-state.json`, `confluence.json`/`confluence-state.json`, `dev.json` (tdd/worktree/subagentes/constitución), `usage-state.json` (marcadores del meter).

## Invariante de seguridad (no negociable)

`nemesis` hace pentest **activo** solo contra hosts **locales/privados** (`localhost`, `127.0.0.1`, `*.test`, redes privadas), impuesto por `agent-kits/nemesis/tools/lib-guardrail.sh`. Nunca puentees el guardrail ni apuntes a sistemas de terceros. La explotación activa (`sqlmap`) requiere opt-in explícito del usuario.

## Añadir un agente nuevo (resumen)

1. Nombre único kebab-case → `agents/<nombre>.md` con frontmatter (incl. `model` y `dependencies`).
2. Scripts propios → `agent-kits/<nombre>/`; reutilizables → `skills/`.
3. Doc en `docs/agents/<nombre>.md` + fila en `docs/README.md` (+ FLOWS si cambia un flujo).
4. `python scripts/lint_plugin.py` y suites en verde.

Detalle completo en `docs/CONVENTIONS.md`.
