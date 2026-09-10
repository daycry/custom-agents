# Salud del código — `C:\Users\46066917X\OneDrive - Imagina Media Audiovisual S.L\claude-cowork\custom-agents` (2026-09-10)

**35 ficheros · 14411 líneas de código** · duplicado **5.8 %** (272 bloques) · funciones largas **97** (> 30 líneas) · anidamiento máx. **6** · TODO/FIXME/HACK **0** · hotspots 35 ficheros cambiados en 90 días

Parámetros: lenguajes `cs,go,java,js,jsx,kt,php,py,rb,rs,ts,tsx` · ventana 8 líneas · tests excluidos · rutas excluidas `interop`. Todas las medidas son **heurísticas** (regex y tokens, no un parser): sirven para ordenar y comparar, no para juzgar una línea concreta.

## 1. Duplicados — 5.8 % de 14323 líneas (272 bloques entre ficheros distintos)

| Líneas | Fichero A | Fichero B |
|---|---|---|
| 93 | `agent-kits/shared/doctor.py:647` | `scripts/lint_plugin.py:549` |
| 25 | `agent-kits/shared/scope-check.py:51` | `skills/adversarial-review/scripts/review-lens-select.py:104` |
| 21 | `agent-kits/shared/ledger-lint.py:103` | `skills/changelog-sync/scripts/changelog-sync.py:123` |
| 19 | `agent-kits/shared/ledger-lint.py:142` | `skills/changelog-sync/scripts/changelog-sync.py:310` |
| 17 | `agent-kits/shared/doctor.py:647` | `agent-kits/shared/knowledge-find.py:247` |
| 17 | `agent-kits/shared/knowledge-find.py:247` | `scripts/lint_plugin.py:549` |
| 15 | `evals/check.py:110` | `scripts/lint_plugin.py:906` |
| 13 | `agent-kits/shared/scope-check.py:27` | `skills/adversarial-review/scripts/review-lens-select.py:62` |
| 13 | `agent-kits/shared/task-brief.py:603` | `skills/jira-sync/scripts/jira-flow.py:249` |
| 13 | `scripts/export-skills.py:36` | `skills/jira-sync/scripts/jira-flow.py:83` |

## 2. Tamaño y complejidad aproximada — 97 funciones > 30 líneas

| Líneas | Función | Dónde |
|---|---|---|
| 122 | `def construir_plan(args):` | `skills/jira-sync/scripts/jira-flow.py:523` |
| 120 | `def parse_ledger(text):` | `agent-kits/shared/ledger-lint.py:209` |
| 114 | `def lint(root):` | `scripts/lint_plugin.py:397` |
| 113 | `const RAICES = (worktree, directory) => [` | `hooks/opencode-plugin.js:48` |
| 108 | `def declaradas(m, avisos):` | `skills/dependency-upgrade/scripts/deps-inventory.py:115` |
| 102 | `def do_release(root, new, args):` | `scripts/release.py:419` |
| 98 | `def check(root):` | `evals/check.py:148` |
| 93 | `def render_html(inits, root):` | `skills/roadmap-dashboard/scripts/build_dashboard.py:372` |
| 91 | `def main(argv=None):` | `skills/changelog-sync/scripts/changelog-sync.py:832` |
| 87 | `def main():` | `agent-kits/qa/coverage-check.py:70` |

Ficheros más grandes (líneas · anidamiento máx.):

- `agent-kits/shared/journal.py` — 978 · 5
- `scripts/lint_plugin.py` — 971 · 6
- `agent-kits/shared/doctor.py` — 944 · 6
- `agent-kits/shared/knowledge-find.py` — 857 · 6
- `agent-kits/shared/task-brief.py` — 784 · 6
- `skills/changelog-sync/scripts/changelog-sync.py` — 710 · 5
- `skills/jira-sync/scripts/jira-flow.py` — 634 · 4
- `skills/roadmap-dashboard/scripts/build_dashboard.py` — 616 · 6
- `skills/api-contract/scripts/openapi-lint.py` — 570 · 5
- `agent-kits/shared/usage-meter.py` — 511 · 6

## 3. Hotspots (grandes Y que cambian mucho)

| Puntuación | Cambios (90 d) | Líneas | Fichero |
|---|---|---|---|
| 87.6 | 9 | 852 | `agent-kits/shared/knowledge-find.py` |
| 83.4 | 9 | 613 | `skills/roadmap-dashboard/scripts/build_dashboard.py` |
| 79.0 | 8 | 942 | `agent-kits/shared/doctor.py` |
| 76.9 | 8 | 783 | `agent-kits/shared/task-brief.py` |
| 69.5 | 7 | 969 | `scripts/lint_plugin.py` |
| 53.0 | 6 | 454 | `scripts/release.py` |
| 51.5 | 6 | 381 | `agent-kits/shared/ledger-lint.py` |
| 39.7 | 4 | 976 | `agent-kits/shared/journal.py` |
| 34.7 | 4 | 408 | `scripts/export-skills.py` |
| 30.5 | 4 | 196 | `skills/jira-sync/scripts/worklog.py` |

## 4. TODO/FIXME/HACK/XXX — 0 (antigüedad: git)

_Sin marcadores._
