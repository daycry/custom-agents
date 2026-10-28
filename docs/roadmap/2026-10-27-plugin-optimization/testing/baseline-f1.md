# Línea base F1: Windows + OneDrive

Tres pasadas completas válidas tras reducir la inicialización del helper de limpieza: **36/36 casos por pasada, exit 0, 1.080 muestras medidas y 108 calentamientos descartados**.

El procedimiento es reproducible; **no se acredita estabilidad uniforme de los tiempos**. Las medianas y sus rangos se conservan para comparar futuros cambios. No se declara ahorro global de hooks.

## Entorno y procedimiento

Entorno de la auditoría inicial: «Windows + OneDrive, 2,8 GB libres, no extrapolable». Las pasadas actuales registran su RAM libre real, distinta de esa observación histórica.

Python 3.13.0; Node v23.8.0. Código en OneDrive; proyectos fixture en el temporal del sistema.

Comando por pasada: `python scripts/bench-hooks.py --runs 10 --warmup 1 --fail-fast --json`.
Un wrapper llama al mismo `main`, imprime el progreso fuera del cronómetro y repite tres veces secuencialmente. No se lanzaron otras pruebas de esta sesión durante la serie.

| Pasada | Fecha UTC | RAM libre GiB | Estado |
|---|---|---:|---|
| 1 | 2026-10-28T11:31:47.640895+00:00 | 12.70 | 36/36, exit 0 |
| 2 | 2026-10-28T11:42:34.790323+00:00 | 12.28 | 36/36, exit 0 |
| 3 | 2026-10-28T11:53:38.506580+00:00 | 13.10 | 36/36, exit 0 |

Se invoca directamente el launcher compartido con fixtures por selector de runtime; estos resultados no prueban entrega nativa de eventos en las aplicaciones.

Los payloads representan una sesión sin rol protegido y con actividad desactivada. Las capturas exigen el recibo persistido. No se activa IA ni red.

## Comparación de medianas

Milisegundos. Dispersión = `100 × (máximo / mínimo - 1)` entre las tres medianas; es descriptiva y no un umbral de CI.

| Runtime | Evento | Hook | Pasada 1 | Pasada 2 | Pasada 3 | Dispersión % |
|---|---|---|---:|---:|---:|---:|
| claude | PreToolUse | native-guardrail | 1030.024 | 897.494 | 808.876 | 27.34 |
| claude | PostToolUse | mark-docs-pending.sh | 2052.976 | 1514.635 | 1556.499 | 35.54 |
| claude | PostToolUse | ledger-lint-warn.sh | 2307.118 | 1716.508 | 2765.589 | 61.12 |
| claude | PostToolUse | progress-line.sh | 3124.794 | 2400.591 | 2838.419 | 30.17 |
| claude | PostToolUse | agent-activity | 588.949 | 454.827 | 635.168 | 39.65 |
| claude | PostToolUseFailure | agent-activity | 524.810 | 471.419 | 551.863 | 17.06 |
| claude | SubagentStart | agent-activity | 523.681 | 495.510 | 573.033 | 15.65 |
| claude | SubagentStop | agent-activity | 536.308 | 552.949 | 655.067 | 22.14 |
| claude | SubagentStop | subagent-progress.sh | 2277.409 | 2068.459 | 3799.055 | 83.67 |
| claude | SessionStart | session-context.sh | 5501.305 | 4507.676 | 4713.391 | 22.04 |
| claude | SessionEnd | session-journal.sh | 872.296 | 819.117 | 847.353 | 6.49 |
| claude | UserPromptSubmit | user-prompt-capture.sh | 976.927 | 861.167 | 1012.711 | 17.60 |
| codex | PreToolUse | native-guardrail | 865.589 | 801.314 | 1052.274 | 31.32 |
| codex | PostToolUse | mark-docs-pending.sh | 1767.576 | 1506.233 | 1606.231 | 17.35 |
| codex | PostToolUse | ledger-lint-warn.sh | 1995.103 | 2586.761 | 1895.513 | 36.47 |
| codex | PostToolUse | progress-line.sh | 2677.485 | 2639.124 | 3481.055 | 31.90 |
| codex | PostToolUse | agent-activity | 468.082 | 469.178 | 829.885 | 77.29 |
| codex | PostToolUseFailure | agent-activity | 466.264 | 581.485 | 783.177 | 67.97 |
| codex | SubagentStart | agent-activity | 481.239 | 484.193 | 572.894 | 19.05 |
| codex | SubagentStop | agent-activity | 499.869 | 478.645 | 635.145 | 32.70 |
| codex | SubagentStop | subagent-progress.sh | 2071.229 | 2016.248 | 2328.380 | 15.48 |
| codex | SessionStart | session-context.sh | 4022.319 | 8127.886 | 5367.863 | 102.07 |
| codex | SessionEnd | session-journal.sh | 927.571 | 1148.621 | 1180.281 | 27.24 |
| codex | UserPromptSubmit | user-prompt-capture.sh | 954.726 | 1006.568 | 1044.586 | 9.41 |
| opencode | PreToolUse | native-guardrail | 830.848 | 1022.659 | 1049.497 | 26.32 |
| opencode | PostToolUse | mark-docs-pending.sh | 1699.726 | 1794.053 | 1748.903 | 5.55 |
| opencode | PostToolUse | ledger-lint-warn.sh | 2247.182 | 2358.073 | 2041.285 | 15.52 |
| opencode | PostToolUse | progress-line.sh | 2707.508 | 2687.266 | 3014.818 | 12.19 |
| opencode | PostToolUse | agent-activity | 484.139 | 478.163 | 572.519 | 19.73 |
| opencode | PostToolUseFailure | agent-activity | 498.132 | 617.859 | 569.793 | 24.04 |
| opencode | SubagentStart | agent-activity | 482.678 | 550.478 | 630.193 | 30.56 |
| opencode | SubagentStop | agent-activity | 492.769 | 489.963 | 665.105 | 35.75 |
| opencode | SubagentStop | subagent-progress.sh | 2090.639 | 2081.083 | 2214.666 | 6.42 |
| opencode | SessionStart | session-context.sh | 4694.300 | 4489.142 | 4722.097 | 5.19 |
| opencode | SessionEnd | session-journal.sh | 844.313 | 1090.309 | 884.561 | 29.14 |
| opencode | UserPromptSubmit | user-prompt-capture.sh | 922.791 | 1024.926 | 913.231 | 12.23 |

Mayor dispersión observada: codex/SessionStart/session-context.sh, 102.07 % entre medianas.
La subtarea original de estabilidad de T-01 sigue abierta con ese resultado variable. Para evaluar una mejora se conservan todas las pasadas y se comprueba que su efecto exceda el rango observado; una fluctuación aislada no acredita ahorro.

## Cambios y diagnósticos conservados

- El helper `close` difiere imports exclusivos de ejecución. Sus presupuestos, validación de dueño y confirmación del job se conservan. La mediana de compilación e inicialización del módulo bajó de 66,844 a 8,974 ms en veinte muestras alternadas por variante; esta cifra excluye arranque del proceso y operaciones de job.
- Las pasadas fallidas del 27 de octubre y las dos anteriores al cambio del 28 de octubre se conservan. Ninguna se usa como pasada válida de esta serie.
- La traza por disco capturó un timeout antes de `close_job`; pudo introducir efecto observador. La traza por pipe completó 264 cierres. Las trazas instrumentadas no son línea base.
- Dos timeouts OpenCode en la primera suite real pasaron aislados con ambas versiones y en la repetición completa de 75 casos. El cambio reduce trabajo evitable; el diagnóstico causal de todos los fallos históricos sigue abierto.
- Los errores históricos de `legacy_notify` y las notificaciones de conversación desconocida siguen separados de estos resultados. No se ejecutaron WorkerRecovery ni integraciones del otro proyecto.

Evidencia: [comparación JSON](baseline-f1-comparison.json), [procedencia](baseline-f1-2026-10-28-post-cleanup-provenance.json), [inicialización antes/después](cleanup-module-initialization.json), [diagnóstico de fases](cleanup-diagnostic-2026-10-28.json), [informe previo archivado](baseline-f1-diagnostic-2026-10-27.md).

## Formato canónico de la última pasada

# Benchmark de hooks y tokens

Fecha UTC: 2026-10-28T11:53:38.506580+00:00

Máquina: Windows; RAM libre: 14069755904 bytes.
Medición local end-to-end del launcher compartido (no aceptación nativa de los runtimes).
Muestras: 10; calentamiento descartado: 1; estado: OK.
Casos ejecutados: 36/36.

| Runtime | Evento | Hook | Estado | Mediana ms | p95 ms | Máximo ms |
|---|---|---|---|---:|---:|---:|
| claude | PreToolUse | native-guardrail | OK | 808.876 | 857.135 | 860.462 |
| claude | PostToolUse | mark-docs-pending.sh | OK | 1556.499 | 2120.289 | 2162.653 |
| claude | PostToolUse | ledger-lint-warn.sh | OK | 2765.589 | 3354.934 | 3363.931 |
| claude | PostToolUse | progress-line.sh | OK | 2838.419 | 4150.625 | 4492.904 |
| claude | PostToolUse | agent-activity | OK | 635.168 | 730.856 | 781.726 |
| claude | PostToolUseFailure | agent-activity | OK | 551.863 | 614.44 | 640.971 |
| claude | SubagentStart | agent-activity | OK | 573.033 | 669.055 | 694.776 |
| claude | SubagentStop | agent-activity | OK | 655.067 | 781.355 | 808.431 |
| claude | SubagentStop | subagent-progress.sh | OK | 3799.055 | 6011.606 | 6998.509 |
| claude | SessionStart | session-context.sh | OK | 4713.391 | 5590.105 | 5840.101 |
| claude | SessionEnd | session-journal.sh | OK | 847.353 | 1137.024 | 1158.917 |
| claude | UserPromptSubmit | user-prompt-capture.sh | OK | 1012.711 | 1356.493 | 1555.053 |
| codex | PreToolUse | native-guardrail | OK | 1052.274 | 1303.932 | 1381.37 |
| codex | PostToolUse | mark-docs-pending.sh | OK | 1606.231 | 1907.056 | 1917.569 |
| codex | PostToolUse | ledger-lint-warn.sh | OK | 1895.513 | 2973.811 | 3096.589 |
| codex | PostToolUse | progress-line.sh | OK | 3481.055 | 4001.609 | 4178.836 |
| codex | PostToolUse | agent-activity | OK | 829.885 | 1085.381 | 1193.385 |
| codex | PostToolUseFailure | agent-activity | OK | 783.177 | 1369.664 | 1398.343 |
| codex | SubagentStart | agent-activity | OK | 572.894 | 611.577 | 615.864 |
| codex | SubagentStop | agent-activity | OK | 635.145 | 676.568 | 698.796 |
| codex | SubagentStop | subagent-progress.sh | OK | 2328.38 | 2775.189 | 2879.451 |
| codex | SessionStart | session-context.sh | OK | 5367.863 | 7544.099 | 8346.55 |
| codex | SessionEnd | session-journal.sh | OK | 1180.281 | 1360.32 | 1364.91 |
| codex | UserPromptSubmit | user-prompt-capture.sh | OK | 1044.586 | 1168.858 | 1173.005 |
| opencode | PreToolUse | native-guardrail | OK | 1049.497 | 1150.79 | 1189.348 |
| opencode | PostToolUse | mark-docs-pending.sh | OK | 1748.903 | 2155.52 | 2178.994 |
| opencode | PostToolUse | ledger-lint-warn.sh | OK | 2041.285 | 2602.729 | 2686.439 |
| opencode | PostToolUse | progress-line.sh | OK | 3014.818 | 5045.589 | 6052.379 |
| opencode | PostToolUse | agent-activity | OK | 572.519 | 613.994 | 619.145 |
| opencode | PostToolUseFailure | agent-activity | OK | 569.793 | 653.976 | 704.326 |
| opencode | SubagentStart | agent-activity | OK | 630.193 | 666.801 | 669.621 |
| opencode | SubagentStop | agent-activity | OK | 665.105 | 757.197 | 794.255 |
| opencode | SubagentStop | subagent-progress.sh | OK | 2214.666 | 3429.161 | 3648.595 |
| opencode | SessionStart | session-context.sh | OK | 4722.097 | 5731.813 | 5888.246 |
| opencode | SessionEnd | session-journal.sh | OK | 884.561 | 947.548 | 968.881 |
| opencode | UserPromptSubmit | user-prompt-capture.sh | OK | 913.231 | 1017.047 | 1030.392 |

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
