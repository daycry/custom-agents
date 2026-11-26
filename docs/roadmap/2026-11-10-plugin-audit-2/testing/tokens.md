---
titulo: Medidas de tokens de la Fase 3 de plugin-audit-2
tasks: [tasks.md](../tasks.md)
---

# Fase 3 (Tokens) de plugin-audit-2 — medidas (tanda A: T-12, T-13, T-14, T-21, T-20)

Método: `agent-kits/shared/context-footprint.py --project . --file …` (caracteres UTF-8 normalizados a LF;
tokens = caracteres/4). Es una ESTIMACIÓN de tamaño, no consumo observado ni facturado. Línea base: HEAD
`ab7eeb2` (tras la fase 2). Medido el 2026-11-20.

| Tarea | Qué se mide | Antes | Después | Diferencia | Criterio |
|---|---|---|---|---|---|
| T-12 | `agents/implementer.md` | 29.280 | 29.268 | −12 | menos bytes ✓ |
| T-12 | Brief de T-12 con `--tdd` (copia del ledger; `task-brief.py … --sin-lint --tdd`) | 7.271 | 7.398 | +127 (sección «TDD» 680 → 807 bytes) | el brief gana ≤ 2 KB ✓ |
| T-12 | `skills/tdd/SKILL.md` (ya no se carga siempre; solo ante una duda) | 10.111 | 10.304 | +193 (1 párrafo) | — |
| T-12 | Agente + brief + skill con `tdd: true` | 29.280 + 7.271 + 10.111 = 46.662 | 29.268 + 7.398 = 36.666 | **−9.996** | baja ≥ 8 KB ✓ |
| T-12 | Brief sin `tdd` (T-12 y T-15, `tdd: false`) | 6.815 / 6.705 bytes | idénticos (`cmp`) | 0 | sin `tdd` no cambia ✓ |
| T-13 | Lo que lee el revisor: `skills/adversarial-review/SKILL.md` → `references/lentes.md` | 18.104 | 3.012 | **−15.092** por lectura | ≤ 5 KB y ≥ 13 KB menos ✓ |
| T-13 | `skills/adversarial-review/SKILL.md` | 18.104 | 16.471 (16.878 tras T-14) | −1.633 (−1.226 tras T-14) | menos bytes ✓ |
| T-13 | `agents/reviewer.md` | 8.649 | 8.833 | +184 | — |
| T-14 | Umbral de aviso de `ledger-lint.py` (bytes) | 183.500 | 60.000 (`--umbral-bytes N`) | −123.500 | ≤ 60.000 ✓ |
| T-14 | Entrada de la Lente A, ledger de prueba de 4 fases (`task-brief.py <carpeta> --fase 2`; bytes) | 100.414 | 25.253 | **−75 %** | baja ≥ 50 % ✓ |
| T-14 | Entrada de la Lente A, ledger real de plugin-audit-2 (copia, 189.819 bytes con CRLF) | 189.819 | fase 1: 57.123 · fase 2: 52.268 · fase 3: 21.232 | −70 % / −72 % / −89 % | — |
| T-14 | `commands/dev-cycle.md` | 29.173 | 29.131 | −42 | — |
| T-14 | Ahorro de la vía rápida (puerta ≥ 6.000) | 6.012 | 6.023 | +11 | ≥ 6.000 ✓ |
| T-21 | Comandos exportados de Codex (`references/command.md`) que pierden la cabecera | 15 con cabecera | 4 con cabecera (dev-cycle, pm-cycle, retro, knowledge-category-check) | 11 × −696 = **−7.656** | ≈ 7,2 KB ✓ |
| T-21 | Comandos exportados de OpenCode (`commands/*.md`) que pierden la cabecera | 15 con cabecera | 4 con cabecera | 11 × −658 = **−7.238** | ≈ 7,2 KB ✓ |
| T-20 | Índice del bloque de `SessionStart`, runtime `claude` | 3.378 (3.578 bytes) | 331 (335 bytes) | **−3.047** (≈ 762 tokens) | ≈ 3,4 KB (844 tokens) — ver nota |
| T-20 | Índice, runtime `codex` / `opencode` | 3.349 / 3.499 | 3.349 / 3.499 | 0 | sin cambio ✓ |

Puertas de tokens al final de la tanda: vía rápida 6.023 (≥ 6.000) · `agents/evaluator.md` 15.465 bytes en LF
(≤ 15.513) · `--diet-check` de `tdd` y `adversarial-review` → 0 párrafos perdidos.

Nota T-20: la cifra del ledger (≈ 3,4 KB / 844 tokens) era el índice entero; la cabecera que queda (331)
hace que el ahorro neto sea 3.047 caracteres (3.243 bytes). El bloque completo de SessionStart depende
del roadmap y la memoria del proyecto; lo que cambia es solo el índice.

Volcado por el orquestador desde el informe del implementer (2026-11-20). La tanda B2 (T-18, T-19, T-22) se añadirá aquí.

## Tanda B1 (T-15, T-16, T-17)

Método: `agent-kits/shared/context-footprint.py` (caracteres UTF-8 normalizados a LF; tokens = caracteres/4, sin tokenizer). Tamaño, no consumo observado ni facturado. Medido el 2026-11-26 sobre la rama `feat/plugin-audit-2`.

| Tarea | Qué se mide | Antes | Después | Diferencia |
|---|---|---|---|---|
| T-15 | `context-footprint.py --project .` (entrada: agentes, comandos y `SKILL.md`) | 509.586 | 495.189 | −14.397 (−14.753 bytes) |
| T-15 | `commands/doctor.md` | 5.807 | 5.245 | −562 |
| T-15 | `agents/reviewer.md` | 9.121 | 8.200 | −921 |
| T-15 | `skills/adversarial-review/SKILL.md` | 17.691 | 16.949 | −742 |
| T-15 | `skills/quick-implement/SKILL.md` | 7.135 | 6.224 | −911 |
| T-16 | `commands/dev-cycle.md` | 28.499 (28.987 bytes LF) | 22.662 (23.024 bytes LF) | −5.837 |
| T-16 | `agent-kits/dev-cycle/references/phase6-close.md` (solo en la Fase 6) | — | 7.088 | +7.088 bajo demanda |
| T-17 | Agentes + comandos (`--project .`) | 489.352 | 483.869 | −5.483 (−6.390 de recetas repetidas; +907 por las recetas que faltaban en `reviewer` y `/retro`) |
| T-17 | `agents/implementer.md` | 29.077 | 28.268 | −809 |
| T-17 | `commands/setup.md` | 19.040 | 18.020 | −1.020 |

Puertas de tokens (tras cada tarea):

| Puerta | T-15 | T-16 | T-17 |
|---|---|---|---|
| Ahorro estimado de la vía rápida (≥ 6.000) | 6.385 | 7.844 | 7.860 |
| `agents/evaluator.md` en bytes LF (≤ 15.513) | 15.465 | 15.465 | 15.434 |
| `--diet-check` | 14 skills: 1 párrafo perdido cada una, el «Alcance y activación» borrado a propósito | n/a (paridad de `dev-cycle` por `test_dev_cycle_split.py`) | n/a (no toca skills) |

Recetas del kit (`grep -c "M=agent-kits/shared/ledger-lint.py" agents/*.md commands/*.md`): 33 en 18 piezas → 20, una por pieza (se añade la que faltaba en `agents/reviewer.md` y `commands/retro.md`).

### Fix1 de la revisión intento 1 (T-16, T-17)

Método: `agent-kits/shared/context-footprint.py --project .` (caracteres UTF-8 con LF; tokens = caracteres/4). Estimación de tamaño, no consumo facturado.

| Medida | Antes (HEAD `7422d4a`) | Después (fix1) | Nota |
|---|---|---|---|
| `commands/dev-cycle.md` caracteres | 22.599 | 22.639 (+40) | T-16 tras T-17; criterio ajustado ≤ 23 KB |
| `commands/dev-cycle.md` bytes LF | 22.959 | 22.999 | ≤ 23.000 |
| Ahorro de la vía rápida (tokens estimados) | 7.860 | 7.850 | ≥ 6.000 |
| `agents/evaluator.md` bytes LF | 15.434 | 15.461 | tope 15.513 |
| Informe completo de entrada (total) | 483.869 (cierre T-17) | 484.575 | inicio T-17: 489.352 |
| Ahorro neto de T-17 entre agentes y comandos | −5.483 | −4.817 | +666 por el aviso «las variables no sobreviven entre llamadas de Bash» en 11 piezas (gap 6); sin la parte de T-16 en `dev-cycle` (+40) |
| `phase6-close.md` caracteres | 7.088 | 7.139 (+51) | enlace a `../../../docs/COMMIT-SELECTION.md` (+6) y cabecera con una sola condición de lectura |

Nota de la revisión intento 2: el aviso del gap 6 mide +628 en las 11 piezas, no +666; el neto −4.817 cuadra con `context-footprint.py`. Volcado por el orquestador el 2026-11-26.

