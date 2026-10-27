# Línea base de F1: pendiente de una pasada completa válida

Estado: **en-progreso**. No se acepta todavía una línea base ni se declara ahorro.

Entorno: **Windows + OneDrive, no extrapolable**. Los 2,8 GB libres citados en
el plan pertenecen a la auditoría inicial; las ejecuciones de hoy registran su
RAM libre real en cada JSON (más memoria disponible). El código está en
OneDrive y los proyectos de prueba están en el temporal del sistema.

Procedimiento: `python scripts/bench-hooks.py --runs 10 --warmup 1 --json`.
La ejecución se instrumentó desde un wrapper temporal que llama al mismo `main`
y muestra el progreso por caso, sin incluir esa impresión en el cronómetro.
La tabla Markdown procede de `markdown(report)` del mismo script. No son
pruebas de entrega nativa de eventos en Claude/Codex/OpenCode.

- `baseline-f1-diagnostic-initial.json`: primera pasada, antes de reforzar la
  verificación de recibos de captura. 35 casos correctos; guard Claude interrumpido
  en la sexta muestra por `child cleanup confirmation timed out` (cinco muestras
  conservadas, sin mediana de éxito). No se usa como línea base.
- `baseline-f1-run-1.json`: pasada del script definitivo, con recibos de captura
  comprobados. 35 casos correctos; SessionStart OpenCode falló al confirmar la
  limpieza. Informe `FALLO`, exit 1 y `linea_base: false`.
- El wrapper detuvo la serie tras ese fallo; no se han realizado tres pasadas
  correctas ni se ha evaluado estabilidad. Los errores se conservan, sin reintentos
  ocultos, exclusión de muestras fallidas ni cambios del plazo de limpieza.
- `baseline-f1-provenance.json`: hashes de las fuentes y fixtures del script
  definitivo, Node y Python observados.

Estos dos fallos medidos de limpieza no reproducen el error Windows 2 del
incidente original. Los registros históricos consultados solo acreditan los
fallos 206 de legacy_notify y avisos de notificación de Desktop. No se ha
modificado código de producción de los hooks para resolverlos.

Validación del benchmark: 26 pruebas en verde y cobertura del 98 % (Coverage.py
7.16.2, entorno `.venv`, salida registrada en el ledger). Los fallos reales
producen exit 1 estructurado: no se convierten en mediciones rápidas de éxito.

## Última pasada diagnóstica completa

# Benchmark de hooks y tokens

Fecha UTC: 2026-10-27T16:46:30.478766+00:00

Máquina: Windows; RAM libre: 9755930624 bytes.
Medición local end-to-end del launcher compartido (no aceptación nativa de los runtimes).
Muestras: 10; calentamiento descartado: 1; estado: FALLO.

| Runtime | Evento | Hook | Estado | Mediana ms | p95 ms | Máximo ms |
|---|---|---|---|---:|---:|---:|
| claude | PreToolUse | native-guardrail | OK | 938.581 | 987.362 | 990.287 |
| claude | PostToolUse | mark-docs-pending.sh | OK | 1751.104 | 1970.114 | 2005.941 |
| claude | PostToolUse | ledger-lint-warn.sh | OK | 1866.79 | 1993.418 | 2012.432 |
| claude | PostToolUse | progress-line.sh | OK | 2592.399 | 2816.981 | 2841.687 |
| claude | PostToolUse | agent-activity | OK | 548.017 | 624.015 | 640.112 |
| claude | PostToolUseFailure | agent-activity | OK | 542.475 | 656.118 | 661.426 |
| claude | SubagentStart | agent-activity | OK | 554.802 | 591.508 | 603.032 |
| claude | SubagentStop | agent-activity | OK | 532.966 | 616.0 | 639.622 |
| claude | SubagentStop | subagent-progress.sh | OK | 2105.927 | 2257.703 | 2268.026 |
| claude | SessionStart | session-context.sh | OK | 4765.234 | 7704.287 | 9283.692 |
| claude | SessionEnd | session-journal.sh | OK | 1118.133 | 1244.221 | 1278.555 |
| claude | UserPromptSubmit | user-prompt-capture.sh | OK | 1263.573 | 1593.344 | 1631.477 |
| codex | PreToolUse | native-guardrail | OK | 1071.352 | 1358.945 | 1441.362 |
| codex | PostToolUse | mark-docs-pending.sh | OK | 1959.047 | 2637.938 | 2670.968 |
| codex | PostToolUse | ledger-lint-warn.sh | OK | 1985.183 | 2215.188 | 2262.006 |
| codex | PostToolUse | progress-line.sh | OK | 2660.421 | 3140.014 | 3198.297 |
| codex | PostToolUse | agent-activity | OK | 525.624 | 583.239 | 595.15 |
| codex | PostToolUseFailure | agent-activity | OK | 494.206 | 664.709 | 696.081 |
| codex | SubagentStart | agent-activity | OK | 515.598 | 551.101 | 551.749 |
| codex | SubagentStop | agent-activity | OK | 512.377 | 575.198 | 607.924 |
| codex | SubagentStop | subagent-progress.sh | OK | 2229.378 | 2521.496 | 2543.816 |
| codex | SessionStart | session-context.sh | OK | 4111.827 | 4672.647 | 4698.347 |
| codex | SessionEnd | session-journal.sh | OK | 989.776 | 1151.301 | 1187.832 |
| codex | UserPromptSubmit | user-prompt-capture.sh | OK | 1058.718 | 1270.086 | 1292.804 |
| opencode | PreToolUse | native-guardrail | OK | 937.091 | 1163.968 | 1179.217 |
| opencode | PostToolUse | mark-docs-pending.sh | OK | 1774.566 | 2206.66 | 2251.167 |
| opencode | PostToolUse | ledger-lint-warn.sh | OK | 1826.606 | 2108.169 | 2116.337 |
| opencode | PostToolUse | progress-line.sh | OK | 2443.626 | 2868.618 | 2953.096 |
| opencode | PostToolUse | agent-activity | OK | 541.709 | 657.185 | 657.196 |
| opencode | PostToolUseFailure | agent-activity | OK | 734.587 | 1143.139 | 1192.22 |
| opencode | SubagentStart | agent-activity | OK | 533.158 | 639.07 | 657.151 |
| opencode | SubagentStop | agent-activity | OK | 592.002 | 644.672 | 646.786 |
| opencode | SubagentStop | subagent-progress.sh | OK | 2054.329 | 2232.376 | 2268.331 |
| opencode | SessionStart | session-context.sh | FALLO | None | None | None |

FALLO: launcher diagnostic: custom-agents hooks: child cleanup confirmation timed out

| opencode | SessionEnd | session-journal.sh | OK | 1499.662 | 2116.131 | 2178.015 |
| opencode | UserPromptSubmit | user-prompt-capture.sh | OK | 1583.323 | 2064.539 | 2150.957 |

estimación caracteres/4, redondeo superior; no es un tokenizador ni consumo real

| Runtime | Tokens fijos estimados |
|---|---:|
| claude | 8752 |
| codex | 8745 |
| opencode | 8783 |

| Bajo demanda | Caracteres | Tokens estimados |
|---|---:|---:|
| commands/dev-cycle.md | 53732 | 13433 |
| agent-kits/shared/knowledge-check.md | 9133 | 2284 |
