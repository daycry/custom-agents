# agent-kits/shared — fragmentos compartidos entre agentes

Fragmentos de prompt que usan **varios** agentes y que deben tener **una única fuente de verdad** (DRY). No es el kit de un agente concreto: es la excepción documentada a la regla «un kit por agente» (ver `docs/CONVENTIONS.md`).

| Fragmento | Qué contiene | Lo usan |
|-----------|--------------|---------|
| `estimation-defaults.md` | Parámetros de estimación (tarifa, supervisión, margen, FTE…) + regla de `.claude/rates.json` | `evaluator`, `planner` |
| `confluence-optin.md` | Paso «Sincronizar con Confluence (opt-in)» | `evaluator`, `planner`, `qa`, `documenter` |
| `ledger-lint.py` | Validación mecánica del ledger `tasks.md` (exit code; `--warn-only` para el hook) | `implementer`, `qa`, `/dev-cycle`, hook `ledger-lint-warn.sh` |
| `read-discipline.md` | Disciplina de lectura del recon (grep antes de Read, límites, ignorar deps/generados) | `documenter`, `nemesis`, `evaluator`, `qa` |
| `output-discipline.md` | Disciplina de salida en handoffs (mensaje final ≤ ~12 líneas, datos no informe) | `evaluator`, `planner`, `implementer`, `qa`, `documenter` |
| `review-report.template.md` | Plantilla fija del comentario de revisión (veredicto por criterio ✓/✗ + gaps + nº intentos + tiempo) | `/dev-cycle` (Modo B) → `jira-sync` Paso 9 |
| `usage-meter.py` (+ tests) | Coste real de generación: tokens medidos de la transcripción por ventana (`start`/`close`/`status`), €, horas-IA por ratio calibrado y formato humano `fmt` (`XhYm`). Degrada a `estimado` sin bloquear | `analyst`, `evaluator`, `planner`, `/dev-cycle` (vía rápida + medición por tarea), `/retro` |

Resolución en runtime (igual que el resto de kits):

```bash
SHAREDKIT="$(find "$PWD/.claude" "$HOME/.claude" -type d -path '*agent-kits/shared' 2>/dev/null | head -1)"
```

Si un agente no encuentra el fragmento (instalación parcial), usa el fallback de una línea indicado en su propio prompt; no inventa valores nuevos.

La tabla de **transiciones de estado** de la cadena spec→evaluación→plan NO vive aquí: su única fuente es la **regla 7 de `docs/CONVENTIONS.md`** (los commands remiten a ella).
