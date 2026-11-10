# Consumo de tokens — medidas antes y después (Fase 4, CA-06)

[Ledger](../tasks.md) · [Auditoría](auditoria-2026-11-09.md)

## Método

- **Qué se mide:** TAMAÑO de lo que se carga, en caracteres UTF-8 con saltos LF, con `agent-kits/shared/context-footprint.py --project <árbol> --file …` (la herramienta que nombra la Verificación de T-17 y T-18). Tokens estimados = caracteres / 4, sin tokenizer.
- **Qué NO se mide:** consumo observado ni facturado. Reducir caracteres no acredita ahorro de tokens hasta medirlo con `usage-meter.py` sobre el mismo objetivo y modelo; no se ha hecho en esta fase.
- **Antes:** `cb6fb40` (el último commit de la fase 3, padre de T-17), extraído con `git -c core.autocrlf=false archive`. **Después:** el HEAD de la fase 4 tras el fix2 (`b5829b9`), extraído igual. Los dos árboles en LF.
- Máquina: Windows 11, Python 3.13.

## Tamaño por pieza (caracteres, `context-footprint.py`)

| Pieza | Antes | Después | Delta | Tarea |
|---|---|---|---|---|
| `agents/analyst.md` | 11.635 | 12.071 | +436 | T-17/T-19 |
| `agents/architect.md` | 15.790 | 16.084 | +294 | T-17/T-19 |
| `agents/documenter.md` | 18.032 | 18.468 | +436 | T-17/T-19 |
| `agents/evaluator.md` (tope CA-22: 15.513 bytes LF; HEAD 15.429) | 14.921 | 15.130 | +209 | T-17/T-19 |
| `agents/implementer.md` | 29.396 | 28.842 | −554 | T-17/T-18/T-19 |
| `agents/knowledge-curator.md` | 12.920 | 13.214 | +294 | T-17/T-19 |
| `agents/nemesis.md` | 15.449 | 15.813 | +364 | T-17/T-19 |
| `agents/planner.md` | 21.420 | 21.856 | +436 | T-17/T-19 |
| `agents/qa.md` | 19.271 | 19.777 | +506 | T-17/T-19 |
| `agents/reviewer.md` | 8.495 | 8.649 | +154 | T-17 |
| `agent-kits/shared/project-integrations.md` | 5.199 | 5.306 | +107 | T-17 |
| `agent-kits/shared/capability-check.md` | 5.491 | 5.561 | +70 | T-19 fix1/fix2 |
| `commands/dev-cycle.md` | 28.708 | 29.019 | +311 | T-17/T-19 |
| `commands/pm-cycle.md` | 10.402 | 10.529 | +127 | T-19 fix1 |
| `skills/quick-implement/SKILL.md` | 6.922 | 7.038 | +116 | T-21/T-19 |
| `agent-kits/dev-cycle/references/phase2-planning.md` (carga por defecto del flujo completo) | 18.136 | 3.034 | −15.102 | T-18 |
| `agent-kits/dev-cycle/references/phase2-plan-review.md` (solo si se pide la revisión visual) | 0 | 15.536 | +15.536 | T-18 |
| `commands/doctor.md` | 16.626 | 5.700 | −10.926 | T-18 |
| `agent-kits/shared/doctor-reference.md` (no se carga; viaja con el kit) | 0 | 12.129 | +12.129 | T-18 fix1 |
| `skills/adversarial-review/SKILL.md` | 18.972 | 18.104 | −868 | T-18 |
| Interop OpenCode, agente `implementer` | 29.702 | 28.554 | −1.148 | T-17/T-18 |

Correcciones respecto a la versión anterior de este fichero: `commands/doctor.md` mide 5.700 (no 5.491; 5.491 es `capability-check.md` en `cb6fb40`); el `evaluator` se mide en LF (antes se midió en CRLF); la base es `cb6fb40` (antes se nombraba `514409e~`, que es el commit de T-20, no el inicio de la fase); las bases de planner y evaluator eran 7 caracteres menores.

## Lo que cada tarea evita por despacho (tamaño leído que se omite)

| Tarea | Se omite | Caracteres | ≈ tokens |
|---|---|---|---|
| T-17 | `capability-check.md` si el brief/ledger ya trae la selección | 5.561 | 1.390 |
| T-17 | `project-integrations.md` con «sin integraciones» | 5.306 | 1.327 |
| T-18 | revisión visual del plan en cada flujo completo | 15.102 | 3.776 |
| T-18 | notas de `/doctor` en cada invocación | 10.926 | 2.732 |
| T-20 | bloque de delegación en 9 agentes × runtime | 6.264 (Codex), 5.526 (OpenCode) en total | ~690 por agente |
| T-19 | `find` de la regla 5 (tiempo, no texto: 7,7 s por bloque según la auditoría) | — | — |

Flujo completo de `/dev-cycle` por defecto (comando + fases 1, 2 sin revisión visual, 3-subagentes y 4): 56.363 → 41.572 caracteres (−14.791, ≈ −3.697 tokens).

## Puerta de la vía rápida (CA-06)

`quick_default_estimate` de la línea base (15.066) − (`dev-cycle.md` + `quick-implement/SKILL.md`, ceil(caracteres/4)): **6.158 → 6.051** (mínimo 6.000; margen 51). El plan pedía ampliar el margen y baja 107: la desviación se debe al texto añadido en T-17 (marca «sin integraciones») y en el fix1 (pasar la línea del kit a cada despacho) y se registra en el ledger. Los cambios de párrafo de `dev-cycle.md` y de la skill se registran con su motivo en `tests/fixtures/dev-cycle-modular-replacements.json`.

## Recomputación del contexto de OpenCode (T-20)

Recuento, no tiempo. Prueba `opencode-plugin.test.mjs`: antes, un prompt, un `bash` completado y el reloj a +31 s recomputaban el contexto; ahora, con los ficheros sin cambiar, ninguno lo hace. Tras el fix1, tampoco lo recomputan los cierres de turno (`session.execution.started/succeeded`, `session.idle`) cuando lo que cita el bloque no cambia (`f4fix1 gap 3`), y una sesión delegada no desaloja la del padre (`gap 11`).

## Consumo observado

No medido. Pendiente: repetir un ciclo de revisión de 12 despachos con `usage-meter.py` antes y después para convertir las cifras de tamaño en consumo.
