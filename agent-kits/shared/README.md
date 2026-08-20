# agent-kits/shared — fragmentos compartidos entre agentes

Fragmentos de prompt que usan **varios** agentes y que deben tener **una única fuente de verdad** (DRY). No es el kit de un agente concreto: es la excepción documentada a la regla «un kit por agente» (ver `docs/CONVENTIONS.md`).

| Fragmento | Qué contiene | Lo usan |
|-----------|--------------|---------|
| `estimation-defaults.md` | Parámetros de estimación (tarifa, supervisión, margen, FTE…) + regla de `.claude/rates.json` | `evaluator`, `planner` |
| `confluence-optin.md` | Paso «Sincronizar con Confluence (opt-in)» | `evaluator`, `planner`, `qa`, `documenter` |
| `ledger-lint.py` | Validación mecánica del ledger `tasks.md` (exit code; `--warn-only` para el hook) | `implementer`, `qa`, `/dev-cycle`, hook `ledger-lint-warn.sh` |
| `read-discipline.md` | Disciplina de lectura del recon (grep antes de Read, límites, ignorar deps/generados) | `documenter`, `nemesis`, `evaluator`, `qa` |
| `output-discipline.md` | Disciplina de salida en handoffs (mensaje final ≤ ~12 líneas, datos no informe) | `evaluator`, `planner`, `implementer`, `qa`, `documenter` |
| `knowledge-check.md` | Paso «Memoria técnica del proyecto — lectura»: si existe `docs/knowledge/`, lee su `README.md` y abre SELECTIVAMENTE solo las entradas de `adr/`/`gotchas/`/`lessons/` del área de la tarea (nunca la carpeta entera); siempre activa, sin opt-in, degrada en silencio si no existe | `evaluator`, `planner`, `implementer`, `qa`, `documenter` |
| `knowledge-write.md` | Paso «Memoria técnica del proyecto — escritura»: umbral anti-burocracia (ADR solo si cierra alternativa y afecta 2+ piezas o se tomó en una puerta; gotcha solo si costó ≥1 ciclo de depuración) + nomenclatura `ADR-NNN`/`GOT-NNN`/`LES-NNN-<agente>`, un fichero por entrada | `planner`, `implementer` (ADR), `qa`, `debug-root-cause` (gotcha), `/retro` (lección) |
| `templates/adr.md` | Plantilla corta de entrada ADR (frontmatter `id`/`titulo`/`estado`/`fecha`/`iniciativa` + contexto · decisión · alternativas descartadas · consecuencias · estado) | `planner`, `implementer` |
| `review-report.template.md` | Plantilla fija del comentario de revisión (veredicto por criterio ✓/✗ + gaps + nº intentos + tiempo) | `/dev-cycle` (Modo B) → `jira-sync` Paso 9 |
| `usage-meter.py` (+ tests) | Coste real de generación: tokens medidos de la transcripción por ventana (`start`/`close`/`status`), €, horas-IA por ratio calibrado y formato humano `fmt` (`XhYm`). Degrada a `estimado` sin bloquear | `analyst`, `evaluator`, `planner`, `/dev-cycle` (vía rápida + medición por tarea), `/retro` |
| `constitution-check.md` | Paso «Constitución del proyecto»: leer/respetar/citar `docs/CONSTITUTION.md` si existe (opt-in, nunca bloquea); regla de enforcement para la lente A (violación explícita = gap con cita) | `analyst`, `evaluator`, `planner`, `implementer`, `qa`, `documenter`, revisión de `/dev-cycle` |
| `templates/CONSTITUTION.template.md` | Plantilla de la constitución del proyecto consumidor (principios permanentes, 1-2 páginas: código, arquitectura fijada/vetada, convenciones, seguridad) | `/setup` (la ofrece opt-in) |
| `task-brief.py` (+ tests) | Brief DETERMINISTA de una tarea para el subagente de contexto fresco (tarea + criterios + fase + persona de dominio + arquitectura + constitución + contrato de retorno DONE/…/BLOCKED); valida el ledger antes de extraer | `/dev-cycle` (despacho con `subagentes: true` en `.claude/dev.json`) |
| `personas/` (6 perfiles) | Catálogo CORTO de personas de dominio (`frontend` · `backend` · `db` · `devops` · `test` · `docs`): prioridades, trampas típicas, calidad y evidencia exigibles de cada dominio (~10 líneas cada una — corto por diseño, para que se mantenga). `task-brief.py` antepone la persona al brief cuando la tarea lleva `- **Tipo**: <tipo>`; sin etiqueta → genérico (sin aviso: el campo es opcional); etiqueta sin persona en el catálogo → genérico CON aviso (degradación) | `task-brief.py` (iniciativa subagent-personas) |

Resolución en runtime (igual que el resto de kits):

```bash
SHAREDKIT="$(find "$PWD/.claude" "$HOME/.claude" -type d -path '*agent-kits/shared' 2>/dev/null | head -1)"
```

Si un agente no encuentra el fragmento (instalación parcial), usa el fallback de una línea indicado en su propio prompt; no inventa valores nuevos.

La tabla de **transiciones de estado** de la cadena spec→evaluación→plan NO vive aquí: su única fuente es la **regla 7 de `docs/CONVENTIONS.md`** (los commands remiten a ella).
