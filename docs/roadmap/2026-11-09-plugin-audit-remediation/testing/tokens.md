# Consumo de tokens — medidas antes y después (Fase 4, CA-06)

[Ledger](../tasks.md) · [Auditoría](auditoria-2026-11-09.md)

## Método

- **Qué se mide:** TAMAÑO de lo que se carga, en caracteres UTF-8 con saltos LF (script de medida sobre el árbol de trabajo; el mismo criterio que `context-footprint.py`). Tokens estimados = caracteres / 4, sin tokenizer.
- **Qué NO se mide:** consumo observado ni facturado. Reducir caracteres no acredita ahorro de tokens hasta medirlo con `usage-meter.py` sobre el mismo objetivo y modelo; no se ha hecho en esta fase.
- **Antes:** árbol en 514409e~ (inicio de la fase, HEAD de la fase 3). **Después:** árbol de la fase 4 cerrada.
- Máquina: Windows 11, Python 3.13.

## Tamaño por pieza (caracteres)

| Pieza | Antes | Después | Delta | Tarea |
|---|---|---|---|---|
| `agents/analyst.md`, `documenter.md`, `planner.md`, `qa.md`, `implementer.md` (bruto T-17) | 11.635 / 18.032 / 21.420 / 19.271 / 29.396 | +296 cada uno | +296 | T-17 |
| `agents/architect.md`, `knowledge-curator.md`, `nemesis.md`, `reviewer.md` | 15.790 / 12.920 / 15.449 / 8.495 | +154 cada uno | +154 | T-17 |
| `agents/evaluator.md` (tope 15.513 bytes) | 14.921 | 15.060 (15.499 bytes) | +139 | T-17 |
| `agents/implementer.md` (neto, tras T-18) | 29.396 | 28.632 | −764 | T-17/T-18 |
| `agent-kits/shared/project-integrations.md` | 5.199 | 5.306 | +107 | T-17 |
| `commands/dev-cycle.md` | 28.708 | 28.784 | +76 | T-17/T-21 |
| `skills/quick-implement/SKILL.md` | 6.922 | 6.935 | +13 | T-21 |
| `phase2-planning.md` (carga por defecto del flujo completo) | 18.136 | 3.034 | −15.102 | T-18 |
| `phase2-plan-review.md` (solo si se pide la revisión visual) | 0 | 15.536 | +15.536 | T-18 |
| `commands/doctor.md` | 16.626 | 5.491 | −11.135 | T-18 |
| `docs/reference/doctor.md` (no se carga) | 0 | 12.042 | +12.042 | T-18 |
| `skills/adversarial-review/SKILL.md` | 18.972 | 18.104 | −868 | T-18 |
| Interop OpenCode, agente `implementer` | 29.702 | 28.344 | −1.358 | T-17/T-18 |

## Lo que cada tarea evita por despacho (tamaño leído que se omite)

| Tarea | Se omite | Caracteres | ≈ tokens |
|---|---|---|---|
| T-17 | `capability-check.md` si el brief/ledger ya trae la selección | 5.491 | 1.373 |
| T-17 | `project-integrations.md` con «sin integraciones» | 5.306 | 1.327 |
| T-18 | revisión visual del plan en cada flujo completo | 15.102 | 3.776 |
| T-18 | notas de `/doctor` en cada invocación | 11.135 | 2.784 |
| T-20 | bloque de delegación en 9 agentes × runtime | 6.264 (Codex), 5.526 (OpenCode) en total | ~690 por agente |
| T-19 | `find` de la regla 5 (tiempo, no texto: 7,7 s por bloque según la auditoría) | — | — |

Flujo completo de `/dev-cycle` por defecto (comando + fases 1, 2 sin revisión visual, 3-subagentes y 4): 56.363 → 41.337 caracteres (−15.026, ≈ −3.757 tokens).

## Puerta de la vía rápida (CA-06)

`quick_default_estimate` de la línea base − (`dev-cycle.md` + `quick-implement/SKILL.md`) / 4: **6.158 → 6.136** (mínimo 6.000). Los cambios de párrafo de `dev-cycle.md` y de la skill se registran con su motivo en `tests/fixtures/dev-cycle-modular-replacements.json`.

## Recomputación del contexto de OpenCode (T-20)

Recuento, no tiempo. Prueba `opencode-plugin.test.mjs`: antes, un prompt, un `bash` completado y el reloj a +31 s recomputaban el contexto; ahora, con los ficheros sin cambiar, ninguno lo hace.

## Consumo observado

No medido. Pendiente: repetir un ciclo de revisión de 12 despachos con `usage-meter.py` antes y después para convertir las cifras de tamaño en consumo.
