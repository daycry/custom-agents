# Salud del código — `C:\Users\46066917X\OneDrive - Imagina Media Audiovisual S.L\claude-cowork\custom-agents` (2026-09-09)

**36 ficheros · 14259 líneas de código** · duplicado **7.6 %** (273 bloques) · funciones largas **105** (> 30 líneas) · anidamiento máx. **6** · TODO/FIXME/HACK **8** (el más viejo: 29 días) · hotspots 36 ficheros cambiados en 90 días

Parámetros: lenguajes `cs,go,java,js,jsx,kt,php,py,rb,rs,ts,tsx` · ventana 8 líneas · tests excluidos. Todas las medidas son **heurísticas** (regex y tokens, no un parser): sirven para ordenar y comparar, no para juzgar una línea concreta.

## 1. Duplicados — 7.6 % de 14150 líneas (273 bloques entre ficheros distintos)

| Líneas | Fichero A | Fichero B |
|---|---|---|
| 118 | `hooks/opencode-plugin.js:37` | `interop/opencode/plugins/custom-agents-hooks.js:37` |
| 93 | `agent-kits/shared/doctor.py:647` | `scripts/lint_plugin.py:549` |
| 25 | `agent-kits/shared/scope-check.py:51` | `skills/adversarial-review/scripts/review-lens-select.py:104` |
| 21 | `agent-kits/shared/ledger-lint.py:103` | `skills/changelog-sync/scripts/changelog-sync.py:123` |
| 19 | `agent-kits/shared/ledger-lint.py:142` | `skills/changelog-sync/scripts/changelog-sync.py:310` |
| 17 | `agent-kits/shared/doctor.py:647` | `agent-kits/shared/knowledge-find.py:247` |
| 17 | `agent-kits/shared/knowledge-find.py:247` | `scripts/lint_plugin.py:549` |
| 15 | `evals/check.py:110` | `scripts/lint_plugin.py:906` |
| 13 | `agent-kits/shared/scope-check.py:27` | `skills/adversarial-review/scripts/review-lens-select.py:62` |
| 13 | `agent-kits/shared/task-brief.py:581` | `skills/jira-sync/scripts/jira-flow.py:249` |
| 13 | `scripts/export-skills.py:36` | `skills/jira-sync/scripts/jira-flow.py:83` |
| 13 | `skills/code-health/scripts/code-health.py:27` | `skills/dependency-upgrade/scripts/deps-inventory.py:29` |
| 12 | `agent-kits/shared/doctor.py:56` | `agent-kits/shared/guardrail-check.py:49` |
| 12 | `agent-kits/shared/doctor.py:56` | `skills/roadmap-dashboard/scripts/build_dashboard.py:14` |
| 12 | `agent-kits/shared/doctor.py:57` | `evals/run.py:55` |

## 2. Tamaño y complejidad aproximada — 105 funciones > 30 líneas

| Líneas | Función | Dónde |
|---|---|---|
| 155 | `def main(argv=None):` | `agent-kits/shared/task-brief.py:640` |
| 122 | `def construir_plan(args):` | `skills/jira-sync/scripts/jira-flow.py:523` |
| 120 | `def parse_ledger(text):` | `agent-kits/shared/ledger-lint.py:209` |
| 114 | `def lint(root):` | `scripts/lint_plugin.py:397` |
| 113 | `const RAICES = (worktree, directory) => [` | `hooks/opencode-plugin.js:48` |
| 113 | `const RAICES = (worktree, directory) => [` | `interop/opencode/plugins/custom-agents-hooks.js:48` |
| 108 | `def declaradas(m, avisos):` | `skills/dependency-upgrade/scripts/deps-inventory.py:115` |
| 102 | `def do_release(root, new, args):` | `scripts/release.py:419` |
| 98 | `def check(root):` | `evals/check.py:148` |
| 93 | `def render_html(inits, root):` | `skills/roadmap-dashboard/scripts/build_dashboard.py:372` |
| 91 | `def main(argv=None):` | `skills/changelog-sync/scripts/changelog-sync.py:832` |
| 87 | `def main():` | `agent-kits/qa/coverage-check.py:70` |
| 87 | `def bloque_plugin(plugin_root, project, explicito=None):` | `agent-kits/shared/doctor.py:252` |
| 87 | `def main(argv=None):` | `agent-kits/shared/knowledge-find.py:932` |
| 85 | `def scan(root):` | `skills/roadmap-dashboard/scripts/build_dashboard.py:228` |

Ficheros más grandes (líneas · anidamiento máx.):

- `agent-kits/shared/journal.py` — 978 · 5
- `scripts/lint_plugin.py` — 971 · 6
- `agent-kits/shared/doctor.py` — 944 · 6
- `agent-kits/shared/knowledge-find.py` — 857 · 6
- `skills/changelog-sync/scripts/changelog-sync.py` — 710 · 5
- `agent-kits/shared/task-brief.py` — 686 · 6
- `skills/jira-sync/scripts/jira-flow.py` — 634 · 4
- `skills/roadmap-dashboard/scripts/build_dashboard.py` — 616 · 6
- `skills/api-contract/scripts/openapi-lint.py` — 570 · 5
- `scripts/release.py` — 455 · 4
- `skills/adversarial-review/scripts/review-lens-select.py` — 430 · 6
- `scripts/export-interop.py` — 419 · 4
- `skills/code-health/scripts/code-health.py` — 418 · 5
- `skills/confluence-publish/scripts/confluence-scope.py` — 416 · 4
- `scripts/export-skills.py` — 414 · 6

## 3. Hotspots (grandes Y que cambian mucho)

| Puntuación | Cambios (90 d) | Líneas | Fichero |
|---|---|---|---|
| 87.6 | 9 | 852 | `agent-kits/shared/knowledge-find.py` |
| 83.4 | 9 | 613 | `skills/roadmap-dashboard/scripts/build_dashboard.py` |
| 79.0 | 8 | 942 | `agent-kits/shared/doctor.py` |
| 69.5 | 7 | 969 | `scripts/lint_plugin.py` |
| 66.0 | 7 | 685 | `agent-kits/shared/task-brief.py` |
| 53.0 | 6 | 454 | `scripts/release.py` |
| 51.5 | 6 | 381 | `agent-kits/shared/ledger-lint.py` |
| 39.7 | 4 | 976 | `agent-kits/shared/journal.py` |
| 34.7 | 4 | 408 | `scripts/export-skills.py` |
| 30.5 | 4 | 196 | `skills/jira-sync/scripts/worklog.py` |
| 28.4 | 3 | 709 | `skills/changelog-sync/scripts/changelog-sync.py` |
| 26.2 | 3 | 427 | `skills/adversarial-review/scripts/review-lens-select.py` |
| 25.4 | 3 | 354 | `agent-kits/shared/guardrail-check.py` |
| 24.9 | 3 | 312 | `agent-kits/shared/skill-index.py` |
| 21.5 | 3 | 142 | `agent-kits/qa/coverage-check.py` |

## 4. TODO/FIXME/HACK/XXX — 8 (antigüedad: git)

| Edad (días) | Tipo | Dónde | Texto |
|---|---|---|---|
| 29 | TODO | `agent-kits/shared/usage-meter.py:380` | # TODO el histórico como ventana → degradar con aviso, no mentir |
| 20 | TODO | `skills/confluence-publish/scripts/confluence-scope.py:113` | del árbol. Los agentes siguen escribiendo TODO (ADRs, arquitectura, |
| 6 | FIXME | `skills/code-health/scripts/code-health.py:18` | 4. TODO/FIXME/HACK/XXX — marcadores con su antigüedad en días (`git blame -L` por línea; s |
| 6 | FIXME | `skills/code-health/scripts/code-health.py:375` | ("todos", "TODO/FIXME/HACK"), ("todo_edad_max_dias", "edad máx. TODO (días)"), |
| 6 | FIXME | `skills/code-health/scripts/code-health.py:400` | f"TODO/FIXME/HACK **{s['todos']}**" |
| 6 | FIXME | `skills/code-health/scripts/code-health.py:438` | L += ["", f"## 4. TODO/FIXME/HACK/XXX — {m['total']} (antigüedad: {m['antiguedad']})", ""] |
| 6 | TODO | `skills/code-health/scripts/code-health.py:47` | # Marcador = la palabra seguida de `:`/`(`/`-` o al COMIENZO del comentario («# TODO revis |
| 1 | TODO | `agent-kits/shared/journal.py:41` | `más tarde`, `TODO:`, `remind me`…), deduplicadas, ≤ MAX_ITEMS por lista y ≤ ITEM_MAX_CHAR |
