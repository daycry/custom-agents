# Consumidores operativos de las skills: manifiestos, perfiles y generadores (T-06)

**Estado.** Lectura y comparación cerradas el 2026-10-13. No se ejecutó código de
la fuente ni se integró nada. Completa el pendiente de T-03/T-06: las fichas
`skills-*.md` buscaron consumidores solo en `agents/`, `commands/` y `skills/`;
aquí se revisan los manifiestos de instalación, los perfiles de contexto y los
generadores o adaptadores que instalan o traducen skills a otros runtimes.
Evidencia con hashes y referencias por skill:
[skills-operational-consumers-evidence.json](skills-operational-consumers-evidence.json).

## Alcance

- Fuente de solo lectura: `C:/tmp/command-catalog24-root-20261010-01/source/`.
  IDs `Snnn` = posición 1-based de `skills/` en orden alfabético (293).
- Manifiestos completos: `manifests/install-*.json`, `pi-core.json`,
  `context-packs/*.json`, `context-profiles/*.json` e `install-assets/*`.
- Generadores y adaptadores de `scripts/` que instalan o traducen skills, más
  los módulos de `scripts/lib/` que resuelven skills (localizados con grep antes
  de leerlos).
- Superficies operativas que esos ficheros señalan y consumen: copias Codex en
  `.agents/skills/`, `.cursor/skills/`, `instructions` de `.opencode/opencode.json`,
  `agent.yaml`, la validación de `scripts/ci/validate-skills.js` y
  `tests/ci/codex-skill-surface.test.js`.
- Contraste propio: `scripts/export-interop.py`, `scripts/lint_plugin.py`,
  `.codex-plugin/plugin.json`, `package.json` (`files`), `docs/INTEROP.md`,
  `install/providers.mjs` y las fichas `skills-*.md`.

Fuera de alcance: `scripts/lib/agent-tools.js`, que solo lo importa el adaptador
Gemini para agentes, y el resto de `scripts/lib/install/*` que no resuelve skills.
La skill solo-Codex `.agents/skills/ecc-conventions/`, que no está entre las 293,
queda anotada pero sin ficha.

## Ficheros leídos

48 ficheros de la fuente: 21 completos (151.985 bytes/4.409 líneas) y 27
parciales o por grep, con el rango anotado. Los hashes están en el JSON.

| Fichero | Bytes | Líneas | Alcance |
|---|---:|---:|---|
| `manifests/install-modules.json` | 31.763 | 1199 | completo |
| `manifests/install-components.json` | 19.841 | 690 | completo |
| `manifests/install-profiles.json` | 2.990 | 106 | completo |
| `manifests/pi-core.json` | 22.743 | 482 | completo |
| `manifests/context-packs/skill-registry@1.json` | 169 | 9 | completo |
| `manifests/context-packs/skill-triggers@1.json` | 5.512 | 1 | completo |
| `manifests/context-profiles/full@1.json` | 475 | 12 | completo |
| `manifests/context-profiles/lean@1.json` | 488 | 12 | completo |
| `manifests/install-assets/claude-project-scripts-package.json` | 25 | 3 | completo |
| `scripts/build-opencode.js` | 733 | 26 | completo |
| `scripts/build-pi-core.js` | 16.476 | 390 | completo |
| `scripts/gemini-adapt-agents.js` | 4.026 | 178 | completo |
| `scripts/install-plan.js` | 9.067 | 277 | completo |
| `scripts/install-apply.js` | 9.795 | 243 | completo |
| `scripts/catalog.js` | 4.827 | 186 | completo |
| `scripts/harness-adapter-compliance.js` | 3.401 | 149 | completo |
| `scripts/lib/context-pack-registry.js` | 7.585 | 160 | completo |
| `scripts/lib/context-profiles.js` | 7.213 | 133 | completo |
| `tests/ci/codex-skill-surface.test.js` | 4.231 | 125 | completo |
| `scripts/lib/install-manifests.js` | 23.390 | 759 | parcial: 1-260 completas (targets, compatibilidad legacy, exclusiones por target, componentes sintéticos skill:<dir>); 261-759 por índice de funciones |
| `scripts/lib/install/request.js` | 5.913 | 169 | parcial: líneas que normalizan --skill/--skills |
| `scripts/lib/install-targets/helpers.js` | 13.679 | 441 | parcial: 20-40 (exclusión de .agents en instalaciones de home) |
| `scripts/lib/install-targets/claude-home.js` | 2.875 | 100 | parcial: mapeo de skills/ a skills/ plano (grep) |
| `scripts/lib/install-targets/claude-project.js` | 3.304 | 114 | parcial: mapeo de skills/ a skills/ plano (grep) |
| `scripts/lib/install-targets/antigravity-project.js` | 3.847 | 121 | parcial: prefijos soportados y destino de skills (grep) |
| `scripts/lib/install-targets/kimi-project.js` | 3.603 | 109 | parcial: 80-95 (copia .agents/skills) |
| `scripts/lib/install/claude-skill-migration.js` | 13.271 | 417 | parcial: 85-130 y 215-232 (skills/ecc/<n> a skills/<n>, propiedad por install-state) |
| `scripts/lib/install/link-rewrite.js` | 6.043 | 167 | parcial: 1-30 (reescritura de enlaces inline) |
| `scripts/lib/context-profile-support.js` | 9.874 | 214 | parcial: TARGETS, normalizeMetadataText, isExcludedResource, validateRelativePath, validateTarget |
| `scripts/lib/context-selection.js` | 16.376 | 273 | parcial: 1-35 y uso de triggers |
| `scripts/lib/context-retrieval.js` | 8.762 | 186 | parcial: pesos de campo y uso de triggers (grep) |
| `scripts/lib/harness-adapter-compliance.js` | 16.337 | 487 | parcial: 30-160 (registros claude-code, codex, opencode, pi) |
| `scripts/codex/check-codex-global-state.sh` | 7.165 | 244 | parcial: 130-180 (16 skills requeridas) y grep de skill |
| `scripts/codex/check-plugin-cache.js` | 7.394 | 264 | grep: sin referencias a skills |
| `scripts/codex/install-global-git-hooks.sh` | 2.591 | 75 | grep: sin referencias a skills |
| `scripts/codex/legacy-sync-state.js` | 2.084 | 66 | grep: sin referencias a skills |
| `scripts/codex/merge-codex-config.js` | 9.526 | 317 | grep: sin referencias a skills |
| `scripts/codex/merge-mcp-config.js` | 13.013 | 352 | grep: sin referencias a skills |
| `scripts/sync-ecc-to-codex.sh` | 19.715 | 608 | parcial: 330-360 y grep de skill (no sincroniza skills) |
| `scripts/ci/validate-skills.js` | 13.122 | 387 | parcial: 1-35 y 200-387 (reglas de frontmatter) |
| `.agents/skills/tdd-workflow/agents/openai.yaml` | 268 | 7 | completo |
| `.agents/skills/tdd-workflow/SKILL.md` | 13.202 | 467 | parcial: frontmatter y comparación de cuerpo con skills/tdd-workflow |
| `.agents/plugins/marketplace.json` | 357 | 21 | completo |
| `.opencode/opencode.json` | 14.946 | 451 | parcial: 1-30 y referencias skills/*/SKILL.md |
| `agent.yaml` | 5.357 | 269 | parcial: lista skills: |
| `CONTRIBUTING.md` | 15.629 | 541 | parcial: 410-480 (subconjuntos por arnés) |
| `.codex/AGENTS.md` | 5.904 | 105 | parcial: grep de .agents/skills y openai.yaml |
| `docs/CODEX-NAVIGATION-GUIDE.md` | 7.490 | 167 | parcial: grep de .agents/skills y openai.yaml |

## Cómo resuelve la fuente las skills

- **Un dueño por skill.** Las 293 skills están en exactamente un módulo de
  `install-modules.json`; el registro de contexto lo exige
  (`scripts/lib/context-pack-registry.js:85`). Además, cada carpeta recibe un
  componente sintético `skill:<dir>` para instalarla sola con `--skills`
  (`scripts/lib/install-manifests.js:194-230`).
- **Base por defecto.** `workflow-quality` (47 skills, `defaultInstall: true`)
  depende de `skill-unified-memory` (`install-modules.json:314-383`). Por eso los
  siete perfiles, incluidos `minimal` y `opencode`, instalan esas 48 skills
  (`install-profiles.json:4-19`). `full` instala las 293.
- **Superficies secundarias.** Son copias o listas mantenidas a mano, sin
  generador:
  - 39 copias Codex en `.agents/skills/`, cada una con `agents/openai.yaml`.
    Las 38 que coinciden con una skill canónica difieren de ella
    (`CONTRIBUTING.md:415-426`: «Keeping these subsets in sync is manual»).
  - 11 copias en `.cursor/skills/`.
  - 11 `SKILL.md` cargados siempre como `instructions` de OpenCode
    (`.opencode/opencode.json:4-19`).
  - 16 skills que `scripts/codex/check-codex-global-state.sh:139-156` exige en
    `~/.agents/skills`.
  - 155 en `agent.yaml`.
  - `scripts/sync-ecc-to-codex.sh:341-343` no sincroniza skills.
- **Contexto.** `skill-triggers@1` aporta disparadores curados a mano a 32 skills.
  Un router BM25F local los pondera con 2,5 (`context-retrieval.js:23`). `lean@1`
  fija un núcleo de tres skills (`configure-ecc`, `context-budget`, `ecc-guide`);
  el resto queda enrutado, con un tope bloqueante de 8.000 tokens estimados para
  los metadatos de descubrimiento (`context-profiles.js:73-128`).
- **pi-core.** De las 293 skills, 123 están en `include`. Las 170 de `exclude`
  llevan cada una su motivo: red o SaaS, mecánica exclusiva de Claude Code, nicho
  o seguridad ofensiva. Hay un renombrado (`council` → `ecc-council`). El
  generador falla si una skill no está clasificada (`build-pi-core.js:56-77`).
- **Generadores.** `build-opencode.js` solo compila TypeScript.
  `gemini-adapt-agents.js` solo toca agentes: mapea herramientas y quita `color`.
  `install-plan.js`/`install-apply.js`/`catalog.js` resuelven módulos y no
  transforman el contenido. Los instaladores Claude aplanan `skills/<n>` y
  migran el formato antiguo `skills/ecc/<n>`. Una carpeta plana que no está
  registrada en install-state se considera del usuario y se omite con aviso
  (`claude-skill-migration.js:219-231`). El único generador que transforma
  skills es `build-pi-core.js`.

## Resumen por perfil

| Perfil | Módulos (con dependencias) | Skills | En pi-core `include` |
|---|---:|---:|---:|
| `minimal` | 6 | 48 | 18 |
| `opencode` | 4 | 48 | 18 |
| `core` | 7 | 48 | 18 |
| `security` | 8 | 67 | 24 |
| `research` | 10 | 74 | 19 |
| `developer` | 10 | 126 | 88 |
| `full` | 27 | 293 | 123 |

### Skills de la base por defecto (todos los perfiles)

Leyenda: «Codex» = copia en `.agents/skills/` con `openai.yaml`; «Codex req.» =
exigida por `check-codex-global-state.sh`; «OpenCode instr.» = cargada siempre;
«componente» = componente con nombre en `install-components.json`; «lean@1» =
núcleo eager.

| ID | Skill | pi-core | Otras superficies | Ficha | Decisión |
|---|---|---|---|---|---|
| S005 | `agent-introspection-debugging` | include | Codex | [foundations](skills-foundations.md) | se mantiene |
| S007 | `agent-self-evaluation` | include | — | [workflows](skills-workflows.md) | se mantiene |
| S008 | `agent-sort` | exclude | Codex | [workflows](skills-workflows.md) | se mantiene |
| S012 | `ai-regression-testing` | exclude | — | [workflows](skills-workflows.md) | se mantiene |
| S017 | `architecture-decision-records` | include | — | [architecture-operations](skills-architecture-operations.md) | se mantiene |
| S030 | `browser-qa` | exclude | disparadores 6 | [brand-browser-runtime](skills-brand-browser-runtime.md) | se mantiene |
| S035 | `ck` | exclude | — | [operations-session-context](skills-operations-session-context.md) | se mantiene |
| S037 | `click-path-audit` | include | — | [navigation-quality-data](skills-navigation-quality-data.md) | se mantiene |
| S039 | `code-tour` | include | disparadores 5 | [navigation-quality-data](skills-navigation-quality-data.md) | se mantiene |
| S040 | `codebase-onboarding` | include | — | [navigation-quality-data](skills-navigation-quality-data.md) | se mantiene |
| S041 | `codehealth-mcp` | exclude | — | [navigation-quality-data](skills-navigation-quality-data.md) | se mantiene |
| S046 | `config-gc` | exclude | — | [strategy-configuration-context](skills-strategy-configuration-context.md) | se mantiene |
| S047 | `configure-ecc` | exclude | lean@1 | [strategy-configuration-context](skills-strategy-configuration-context.md) | se mantiene |
| S051 | `context-budget` | exclude | lean@1 | [strategy-configuration-context](skills-strategy-configuration-context.md) | se mantiene |
| S053 | `continuous-learning` | exclude | componente | [session-learning-memory](skills-session-learning-memory.md) | se mantiene |
| S054 | `continuous-learning-v2` | exclude | — | [session-learning-memory](skills-session-learning-memory.md) | se mantiene |
| S058 | `council` | include | pi: ecc-council | [contracts-costs-decisions](skills-contracts-costs-decisions.md) | se mantiene |
| S059 | `council-multi-model` | exclude | — | [contracts-costs-decisions](skills-contracts-costs-decisions.md) | se mantiene |
| S074 | `delivery-gate` | exclude | — | [contract-security-delivery](skills-contract-security-delivery.md) | se mantiene |
| S077 | `dev-team` | include | — | [deployment-design-collaboration](skills-deployment-design-collaboration.md) | se mantiene |
| S088 | `e2e-testing` | include | Codex, Codex req., OpenCode instr. | [dotnet-harness-e2e](skills-dotnet-harness-e2e.md) | se mantiene |
| S089 | `ecc-guide` | exclude | lean@1 | [catalog-self-ops-domains](skills-catalog-self-ops-domains.md) | se mantiene |
| S090 | `ecc-recipes` | exclude | — | [catalog-self-ops-domains](skills-catalog-self-ops-domains.md) | se mantiene |
| S095 | `error-handling` | include | disparadores 11 | [errors-evals-providers](skills-errors-evals-providers.md) | se mantiene |
| S097 | `eval-harness` | exclude | Codex, Codex req., OpenCode instr., componente | [errors-evals-providers](skills-errors-evals-providers.md) | se mantiene |
| S114 | `git-workflow` | include | disparadores 7 | [git-github-workspace](skills-git-github-workspace.md) | **revisar** |
| S119 | `growth-log` | exclude | — | [growthlog-healthcare-imports](skills-growthlog-healthcare-imports.md) | se mantiene |
| S132 | `hookify-rules` | exclude | — | [vpn-hookify-i18n-legacy](skills-vpn-hookify-i18n-legacy.md) | se mantiene |
| S134 | `inherit-legacy-style` | include | — | [vpn-hookify-i18n-legacy](skills-vpn-hookify-i18n-legacy.md) | se mantiene |
| S135 | `intent-driven-development` | include | — | [intent-inventory](skills-intent-inventory.md) | se mantiene |
| S140 | `iterative-retrieval` | exclude | — | [investor-icons-retrieval](skills-investor-icons-retrieval.md) | se mantiene |
| S163 | `living-docs-governance` | include | — | [living-docs-loops-trading](skills-living-docs-loops-trading.md) | **revisar** |
| S166 | `loop-design-check` | exclude | — | [living-docs-loops-trading](skills-living-docs-loops-trading.md) | se mantiene |
| S205 | `plan-canvas` | exclude | Codex, componente | [product-canvas-flow-prompts](skills-product-canvas-flow-prompts.md) | se mantiene |
| S207 | `plankton-code-quality` | exclude | — | [plankton-postgres-prisma-audit](skills-plankton-postgres-prisma-audit.md) | se mantiene |
| S213 | `product-lens` | include | — | [product-canvas-flow-prompts](skills-product-canvas-flow-prompts.md) | se mantiene |
| S214 | `production-audit` | include | — | [plankton-postgres-prisma-audit](skills-plankton-postgres-prisma-audit.md) | se mantiene |
| S237 | `repo-scan` | exclude | — | [reposcan-research-rules-safety](skills-reposcan-research-rules-safety.md) | se mantiene |
| S240 | `rules-distill` | exclude | — | [reposcan-research-rules-safety](skills-reposcan-research-rules-safety.md) | se mantiene |
| S244 | `santa-method` | exclude | — | [rfc-dag-ledger-santa](skills-rfc-dag-ledger-santa.md) | se mantiene |
| S255 | `skill-comply` | exclude | — | [search-compliance-stocktake-compact](skills-search-compliance-stocktake-compact.md) | se mantiene |
| S256 | `skill-scout` | exclude | — | [search-compliance-stocktake-compact](skills-search-compliance-stocktake-compact.md) | se mantiene |
| S257 | `skill-stocktake` | exclude | — | [search-compliance-stocktake-compact](skills-search-compliance-stocktake-compact.md) | se mantiene |
| S264 | `strategic-compact` | exclude | Codex, Codex req., OpenCode instr., componente | [search-compliance-stocktake-compact](skills-search-compliance-stocktake-compact.md) | se mantiene |
| S273 | `tdd-workflow` | include | Codex, Codex req., OpenCode instr., disparadores 6, componente | [tdd-verification-ops](skills-tdd-verification-ops.md) | se mantiene |
| S283 | `unified-memory` | exclude | Codex, Cursor, componente | [team-memory-surface](skills-team-memory-surface.md) | se mantiene |
| S285 | `verification-loop` | include | Codex, Codex req., OpenCode instr., disparadores 5, componente | [tdd-verification-ops](skills-tdd-verification-ops.md) | se mantiene |
| S291 | `windows-desktop-e2e` | exclude | componente | [ui-demo-desktop-e2e](skills-ui-demo-desktop-e2e.md) | se mantiene |

### Otras skills con superficie operativa fuera de la base

Se incluyen las skills que no están en la base pero tienen copia Codex o Cursor,
`instructions` de OpenCode, disparadores o componente con nombre. El mapa
completo de las 293 skills está en `skill_refs` del JSON.

| ID | Skill | Módulo | pi-core | Superficies | Ficha |
|---|---|---|---|---|---|
| S015 | `api-connector-builder` | operator-workflows | include | disparadores 3 | [architecture-operations](skills-architecture-operations.md) |
| S016 | `api-design` | framework-language | include | Codex, Codex req., OpenCode instr., disparadores 11 | [architecture-operations](skills-architecture-operations.md) |
| S018 | `article-writing` | business-content | exclude | Codex, Codex req., Cursor | [architecture-operations](skills-architecture-operations.md) |
| S022 | `backend-patterns` | framework-language | include | Codex, Codex req., OpenCode instr., disparadores 8, componente | [iteration-backend-benchmarks](skills-iteration-backend-benchmarks.md) |
| S024 | `benchmark-methodology` | optimization-workflows | exclude | Codex | [iteration-backend-benchmarks](skills-iteration-backend-benchmarks.md) |
| S028 | `brand-discovery` | business-content | exclude | Codex | [brand-browser-runtime](skills-brand-browser-runtime.md) |
| S029 | `brand-voice` | business-content | exclude | Codex | [brand-browser-runtime](skills-brand-browser-runtime.md) |
| S031 | `bun-runtime` | framework-language | include | Codex, Cursor | [brand-browser-runtime](skills-brand-browser-runtime.md) |
| S032 | `canary-watch` | devops-infra | exclude | disparadores 6 | [brand-browser-runtime](skills-brand-browser-runtime.md) |
| S042 | `coding-standards` | framework-language | include | Codex, Codex req., OpenCode instr., disparadores 7, componente | [navigation-quality-data](skills-navigation-quality-data.md) |
| S043 | `competitive-platform-analysis` | business-content | exclude | Codex | [strategy-configuration-context](skills-strategy-configuration-context.md) |
| S044 | `competitive-report-structure` | business-content | exclude | Codex | [strategy-configuration-context](skills-strategy-configuration-context.md) |
| S049 | `content-engine` | business-content | exclude | Codex, Codex req., Cursor | [strategy-configuration-context](skills-strategy-configuration-context.md) |
| S050 | `content-hash-cache-pattern` | agentic-patterns | include | disparadores 3 | [strategy-configuration-context](skills-strategy-configuration-context.md) |
| S063 | `crosspost` | social-distribution | exclude | Codex | [cpp-dotnet-distribution-billing](skills-cpp-dotnet-distribution-billing.md) |
| S071 | `database-migrations` | database | include | disparadores 9 | [data-pipelines-research](skills-data-pipelines-research.md) |
| S072 | `deep-research` | research-apis | exclude | Codex, componente | [data-pipelines-research](skills-data-pipelines-research.md) |
| S075 | `deployment-patterns` | devops-infra | include | disparadores 7 | [deployment-design-collaboration](skills-deployment-design-collaboration.md) |
| S076 | `design-system` | framework-language | include | disparadores 5 | [deployment-design-collaboration](skills-deployment-design-collaboration.md) |
| S079 | `django-patterns` | framework-language | include | disparadores 6 | [django-queues-architecture](skills-django-queues-architecture.md) |
| S080 | `django-security` | security | include | disparadores 8 | [django-security-testing-verification](skills-django-security-testing-verification.md) |
| S083 | `dmux-workflows` | orchestration | exclude | Codex | [parallel-containers-docs](skills-parallel-containers-docs.md) |
| S084 | `docker-patterns` | devops-infra | include | disparadores 4 | [parallel-containers-docs](skills-parallel-containers-docs.md) |
| S085 | `documentation-lookup` | research-apis | exclude | Codex, Cursor | [parallel-containers-docs](skills-parallel-containers-docs.md) |
| S098 | `evm-token-decimals` | security | exclude | disparadores 4 | [errors-evals-providers](skills-errors-evals-providers.md) |
| S099 | `exa-search` | research-apis | exclude | Codex | [errors-evals-providers](skills-errors-evals-providers.md) |
| S100 | `fal-ai-media` | media-generation | exclude | Codex | [errors-evals-providers](skills-errors-evals-providers.md) |
| S106 | `frontend-a11y` | framework-language | include | disparadores 7 | [flutter-ondevice-a11y](skills-flutter-ondevice-a11y.md) |
| S108 | `frontend-patterns` | framework-language | include | Codex, Codex req., OpenCode instr., componente | [frontend-direction-patterns-slides](skills-frontend-direction-patterns-slides.md) |
| S109 | `frontend-slides` | framework-language | exclude | Codex, Codex req., OpenCode instr., Cursor | [frontend-direction-patterns-slides](skills-frontend-direction-patterns-slides.md) |
| S125 | `hexagonal-architecture` | framework-language | include | disparadores 3 | [hexagonal-hipaa-homelab](skills-hexagonal-hipaa-homelab.md) |
| S137 | `investor-materials` | business-content | exclude | Codex, Codex req., Cursor | [investor-icons-retrieval](skills-investor-icons-retrieval.md) |
| S138 | `investor-outreach` | business-content | exclude | Codex, Codex req., Cursor | [investor-icons-retrieval](skills-investor-icons-retrieval.md) |
| S154 | `kubernetes-patterns` | devops-infra | include | disparadores 6 | [k8s-latency-mailtrap](skills-k8s-latency-mailtrap.md) |
| S170 | `market-research` | business-content | exclude | Codex, Codex req., Cursor | [leads-logistics-research-agreements](skills-leads-logistics-research-agreements.md) |
| S173 | `mcp-server-patterns` | framework-language | include | Codex, Cursor | [mysql-nestjs-mcp-keccak](skills-mysql-nestjs-mcp-keccak.md) |
| S176 | `mle-workflow` | machine-learning | include | Codex, componente | [ml-adoption-mle](skills-ml-adoption-mle.md) |
| S188 | `nextjs-turbopack` | framework-language | include | Codex, Cursor | [motion-next-nuxt](skills-motion-next-nuxt.md) |
| S198 | `orch-fix-defect` | agentic-patterns | exclude | disparadores 5 | [orch-parallel-plan](skills-orch-parallel-plan.md) |
| S208 | `postgres-patterns` | database | include | disparadores 11 | [plankton-postgres-prisma-audit](skills-plankton-postgres-prisma-audit.md) |
| S212 | `product-capability` | business-content | include | Codex | [product-canvas-flow-prompts](skills-product-canvas-flow-prompts.md) |
| S218 | `python-patterns` | framework-language | include | disparadores 5 | [python-pytorch](skills-python-pytorch.md) |
| S219 | `python-testing` | framework-language | include | disparadores 5 | [python-pytorch](skills-python-pytorch.md) |
| S234 | `redis-patterns` | database | include | disparadores 4 | [rails-redis-rust](skills-rails-redis-rust.md) |
| S235 | `regex-vs-llm-structured-text` | agentic-patterns | include | disparadores 10 | [recsys-regex-llm](skills-recsys-regex-llm.md) |
| S241 | `rust-patterns` | framework-language | include | disparadores 6 | [rails-redis-rust](skills-rails-redis-rust.md) |
| S250 | `search-first` | agentic-patterns | exclude | disparadores 5 | [search-compliance-stocktake-compact](skills-search-compliance-stocktake-compact.md) |
| S252 | `security-review` | security | include | Codex, Codex req., OpenCode instr., disparadores 12, componente | [security-bounty-review-agentshield](skills-security-bounty-review-agentshield.md) |
| S253 | `security-scan` | security | exclude | disparadores 6 | [security-bounty-review-agentshield](skills-security-bounty-review-agentshield.md) |
| S286 | `video-editing` | media-generation | exclude | Codex | [taste-video](skills-taste-video.md) |
| S290 | `vue-patterns` | framework-language | include | componente | [vue-vite-tinystruct](skills-vue-vite-tinystruct.md) |
| S293 | `x-api` | social-distribution | exclude | Codex | [terminal-uncloud-x-visa](skills-terminal-uncloud-x-visa.md) |

## Decisiones a revisar (2)

Solo se señalan las decisiones cuya premisa contradice un consumidor operativo.
En las dos, la cobertura que alega la ficha está en ficheros del repo del plugin
que no llegan al proyecto consumidor (`package.json:37-58`). La fuente, en
cambio, instala ambas skills en el consumidor en todos sus perfiles.

### S114 — `git-workflow`

- **Decisión actual** ([skills-git-github-workspace.md](skills-git-github-workspace.md),
  líneas 31-32): sin skill nueva; `CONTRIBUTING.md` y los guardrails cubren
  conflictos y merge frente a rebase.
- **Consumidor operativo:**
  - Pertenece a `workflow-quality`, por defecto en los siete perfiles
    (`install-modules.json:314-364`, `install-profiles.json:4-19`).
  - Tiene siete disparadores curados, como «resolve merge conflict» y «merge vs
    rebase» (`skill-triggers@1.json:1`).
  - Está en pi-core `include` como guía portable (`pi-core.json:88`).
- **Por qué revisar:**
  - `CONTRIBUTING.md` no se distribuye.
  - El guardrail de git solo limita al implementer.
  - Ninguna pieza distribuida (`agents/`, `commands/`, `skills/`,
    `agent-kits/`) trata la resolución de conflictos ni merge frente a rebase;
    se comprobó con grep.
- **Revisión propuesta:**
  - Decidir un dueño para la parte útil en el consumidor: implementer o
    quick-implement, o una referencia de `delivery-practices`.
  - Conservar las correcciones de la ficha: no `git add .`, nada de config
    global ni `reset --hard`, y `--force-with-lease` solo en rama propia.
  - Si se mantiene «sin destino», el motivo no puede depender de ficheros que no
    se distribuyen.

### S163 — `living-docs-governance`

- **Decisión actual** ([skills-living-docs-loops-trading.md](skills-living-docs-loops-trading.md),
  líneas 16-43): solo cambia el texto del aviso `_tolerancias_caducadas` de
  `scripts/lint_plugin.py`; sin skill nueva.
- **Consumidor operativo:**
  - Pertenece a `workflow-quality`, por defecto en todos los perfiles
    (`install-modules.json:358`).
  - Está en pi-core `include` (`pi-core.json:108`).
  - Es una guía para el repositorio del usuario.
- **Por qué revisar:**
  - La comparación contrasta los cuatro papeles con el repo del plugin
    (`CLAUDE.md`, `docs/README.md`, `RUTAS_RETIRADAS`).
  - Su único destino es un script que no se distribuye.
  - No comprueba si `documenter` inventaría antes de crear ni si mantiene una
    «zona de borrado» en el consumidor; no se encontró en `agents/documenter.md`.
- **Revisión propuesta:**
  - Mantener el cambio del aviso.
  - Añadir la comprobación en el consumidor. Si `documenter` ya lo cubre,
    anotarlo. Si no, el registro de lo retirado (motivo, sustituto y condición
    de revisión) va a `documenter`.

## Revisadas sin cambio

- **S283 `unified-memory`.** Es dependencia obligatoria de la base
  (`install-modules.json:383`) y requiere un CLI externo (`:285`). La ficha
  sigue valiendo: sus criterios ya están en `/work-resume`. Además, hacer
  depender la base de un runtime externo choca con «degradación, no bloqueo».
- **S047, S051 y S089 (núcleo `lean@1`).** Describen el catálogo de la fuente.
  Sus dueños propios (`/setup`, `/doctor`, `skill-index.py`) se mantienen; el
  presupuesto pasa a contratos (n.º 5).
- **Skills siempre cargadas o exigidas en Codex** (S016, S022, S042, S088, S097,
  S108, S252, S264, S273, S285). Cargarlas siempre es una decisión de la
  fuente; ninguna superficie añade un consumidor que cambie el dueño fijado.
- **S053.** La propia fuente marca la v1 como legado
  (`install-components.json:506`), igual que «eliminar la segunda vía».
- **S058.** pi-core la renombra `ecc-council` por colisión genérica
  (`pi-core.json:159-161`); el destino `decision-review` no colisiona.
- **S205.** pi-core la excluye por ser exclusiva de Claude Code, pero se publica
  para Codex con `openai.yaml`. La contradicción es de la fuente; el destino
  sin hook ni CDN se mantiene.
- **Skills de negocio con copia Codex o Cursor y exigidas en Codex** (S018,
  S049, S137–S138, S170, S109). Se distribuyen así por la orientación de la
  fuente y no añaden un consumidor del ciclo.
- **S176.** Un test de la fuente exige su copia Codex
  (`codex-skill-surface.test.js:81`). Es un requisito interno de la fuente.

## Contratos de generador frente a `export-interop.py`

| # | Contrato de la fuente | Evidencia | Estado propio | Aplicabilidad |
|---|---|---|---|---|
| 1 | Frontmatter de skill en Codex solo con `name`, `description`, `metadata`, `license` y `allowed-tools` | `CONTRIBUTING.md:478`; `tests/ci/codex-skill-surface.test.js:12-18` | `export-interop.py:291-294` publica `./skills/` tal cual; `docs/INTEROP.md:145-146` solo exige `name`+`description`. Hay `user-invokable` en confluence-publish:14, confluence-pull:13, cybersecurity:16, jira-sync:14 y to-pdf:9, y `argument-hint` en cybersecurity:25 | **Verificar** con la doc oficial de Codex o con una prueba aislada que cargue esas cinco skills: la fuente lo afirma, pero no está contrastado aquí, y no consta que la prueba de Codex 0.161.0 las cubriera. Si se confirma, añadir a `test_export_interop.py` la regla «claves ⊆ lista» o mover las claves extra |
| 2 | `agents/openai.yaml` por skill: `display_name`, `short_description` de 25–64 caracteres, `default_prompt` con `$<skill>`, `policy.allow_implicit_invocation` | `codex-skill-surface.test.js:95-115`; `.agents/skills/tdd-workflow/agents/openai.yaml:1-7` | Solo los adaptadores de comandos lo generan (`export-interop.py:478-482`): 34 caracteres, sin `default_prompt` | Opcional. Si se generan para las skills canónicas, derivarlos con el generador, nunca a mano, y comprobar el rango |
| 3 | `name` igual a la carpeta, nombres únicos y `description` no vacía | `build-pi-core.js:134-137`; `codex-skill-surface.test.js:90` | `export-interop.py:486-500` comprueba unicidad y que no esté vacío, pero no la igualdad con la carpeta (hoy coinciden las 27) | Aplicable: una comprobación más |
| 4 | Prohibido el escalar literal `\|` en `description` | `validate-skills.js:275-277` | `campo()` pliega `>` y `\|` (`export-interop.py:158-180`); hoy hay 24 con `>` y ninguno con `\|` | Aviso de linter barato; protege a quien lee el frontmatter crudo |
| 5 | Presupuesto agregado de metadatos: pi-core falla por encima de 42.000 caracteres de `description`; `lean@1` bloquea por encima de 8.000 tokens (bytes UTF-8/4 de `{harness,type,name,description}`) | `build-pi-core.js:343-349`; `context-profiles.js:73-87,120-128`; `lean@1.json:11` | Solo avisos por pieza (`lint_plugin.py:108,112`). Medido hoy: 27 skills, 17.917 caracteres, unos 5.144 tokens con el método de la fuente; las 52 piezas suman 31.061 caracteres | Aplicable como total informativo del linter (token-diet), sin bloquear |
| 6 | Partición completa: toda skill clasificada `include`/`exclude` con motivo y un único dueño | `build-pi-core.js:56-77`; `context-pack-registry.js:85` | Se exportan todas; no hay subconjuntos | Solo si `export-skills.py` o un perfil reducido selecciona un subconjunto: exigir clasificación con motivo |
| 7 | Renombrado al exportar por colisión genérica | `pi-core.json:159-161`; `build-pi-core.js:142-147` | Prefijo `custom-agents-` y control de colisiones (`export-interop.py:452-500`) | Equivalente |
| 8 | Escaneo del árbol exportado: hosts fuera de la lista, `curl\|sh`, `npx -y`, secretos, rutas absolutas de home y symlinks | `build-pi-core.js:280-340` | No se escanea el árbol generado | Aplicable en parte: rutas absolutas de home y symlinks en `--check`, de acuerdo con la regla de datos personales; el resto, opcional |
| 9 | Copias manuales por runtime | `CONTRIBUTING.md:415-426`; las 38 copias Codex difieren y algunas conservan contenido ya retirado del canónico (limitador en memoria en backend-patterns, CSP con `'unsafe-inline'`/`'unsafe-eval'` en security-review, ruta de hook antigua en strategic-compact) | No se copian skills (`export-interop.py:21-22`) y existe `--check` | Confirma el diseño propio |
| 10 | Skills cargadas siempre en el contexto | `.opencode/opencode.json:4-19`; la misma fuente avisa en contra (`lib/harness-adapter-compliance.js:65`) | No se hace | Mantener |
| 11 | Disparadores curados en un manifiesto aparte, en minúsculas y sin duplicados, con peso 2,5 | `skill-triggers@1.json`; `context-pack-registry.js:128-143`; `context-retrieval.js:23` | Disparadores en `description`, `evals/cases/` y aviso de literales duplicados | No crear otro manifiesto; usarlos como semillas de casos positivos en las evals de los destinos (tdd, backend-practices, delivery-practices…) |
| 12 | Instalación: `.agents` nunca en home; carpeta de skill no registrada = del usuario | `install-targets/helpers.js:27-33`; `claude-skill-migration.js:219-231` | Manifiesto de propiedad; el payload no incluye `.agents` (`providers.mjs:31-35`) | Equivalente; la instalación de una sola skill no se necesita |
| 13 | Adaptador Gemini: mapa de herramientas y quitar `color` | `gemini-adapt-agents.js:8-17,87-130` | Sin destino Gemini | No aplica a skills |

**Observación lateral (a verificar).** Las cinco skills del contrato 1 usan
`user-invokable`. Si la clave documentada por Claude Code es `user-invocable`,
Claude Code también la ignora. Hay que comprobarlo con la documentación oficial
antes de tocar nada.

## Límites

- Lectura estática: no se instaló, ejecutó ni consultó ningún servicio. Las
  reglas del validador Codex y de Pi son afirmaciones de la fuente, no
  contrastadas con la documentación oficial.
- Las copias de `.agents/skills/` se compararon por líneas de cuerpo; solo se
  leyó completo el `SKILL.md` de tdd-workflow.
- El mapeo skill→ficha sale de los encabezados de las fichas. Las decisiones de
  las dos revisiones se releyeron en su ficha.
