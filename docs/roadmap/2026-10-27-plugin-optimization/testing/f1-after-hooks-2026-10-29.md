# Benchmark de hooks y tokens

Fecha UTC: 2026-10-29T12:30:02.167558+00:00

Máquina: Windows; RAM libre: 6813888512 bytes.
Medición local end-to-end del launcher compartido (no aceptación nativa de los runtimes).
Muestras: 10; calentamiento descartado: 1; estado: OK.
Casos ejecutados: 36/36.

| Runtime | Evento | Hook | Estado | Mediana ms | p95 ms | Máximo ms |
|---|---|---|---|---:|---:|---:|
| claude | PreToolUse | native-guardrail | OK | 664.287 | 692.387 | 702.445 |
| claude | PostToolUse | mark-docs-pending.sh | OK | 1714.278 | 1984.071 | 2102.322 |
| claude | PostToolUse | ledger-lint-warn.sh | OK | 1903.845 | 2242.403 | 2379.949 |
| claude | PostToolUse | progress-line.sh | OK | 2707.512 | 3061.678 | 3114.005 |
| claude | PostToolUse | agent-activity | OK | 838.88 | 1201.797 | 1257.19 |
| claude | PostToolUseFailure | agent-activity | OK | 767.51 | 1277.177 | 1293.104 |
| claude | SubagentStart | agent-activity | OK | 710.654 | 1011.509 | 1160.727 |
| claude | SubagentStop | agent-activity | OK | 718.508 | 864.135 | 888.828 |
| claude | SubagentStop | subagent-progress.sh | OK | 2095.32 | 2527.449 | 2675.994 |
| claude | SessionStart | session-context.sh | OK | 4886.039 | 7879.781 | 8051.256 |
| claude | SessionEnd | session-journal.sh | OK | 1366.429 | 1935.886 | 2087.575 |
| claude | UserPromptSubmit | user-prompt-capture.sh | OK | 1435.057 | 2484.465 | 2489.984 |
| codex | PreToolUse | native-guardrail | OK | 881.863 | 1824.806 | 2429.452 |
| codex | PostToolUse | mark-docs-pending.sh | OK | 3043.328 | 7700.069 | 10657.99 |
| codex | PostToolUse | ledger-lint-warn.sh | OK | 4818.336 | 8238.975 | 9939.3 |
| codex | PostToolUse | progress-line.sh | OK | 7848.9 | 14254.783 | 15635.807 |
| codex | PostToolUse | agent-activity | OK | 1774.294 | 2731.256 | 2814.741 |
| codex | PostToolUseFailure | agent-activity | OK | 2047.976 | 3179.073 | 3297.716 |
| codex | SubagentStart | agent-activity | OK | 3021.108 | 4590.472 | 5108.278 |
| codex | SubagentStop | agent-activity | OK | 3258.282 | 4256.876 | 4318.511 |
| codex | SubagentStop | subagent-progress.sh | OK | 6700.341 | 7967.226 | 8210.982 |
| codex | SessionStart | session-context.sh | OK | 13855.747 | 16704.488 | 17187.305 |
| codex | SessionEnd | session-journal.sh | OK | 3208.703 | 5448.466 | 5911.123 |
| codex | UserPromptSubmit | user-prompt-capture.sh | OK | 2662.207 | 3163.69 | 3205.605 |
| opencode | PreToolUse | native-guardrail | OK | 1583.21 | 2820.145 | 2994.495 |
| opencode | PostToolUse | mark-docs-pending.sh | OK | 2948.35 | 3464.532 | 3484.626 |
| opencode | PostToolUse | ledger-lint-warn.sh | OK | 3005.167 | 3819.842 | 3909.315 |
| opencode | PostToolUse | progress-line.sh | OK | 3919.364 | 5165.576 | 5750.286 |
| opencode | PostToolUse | agent-activity | OK | 1004.666 | 1823.04 | 1957.626 |
| opencode | PostToolUseFailure | agent-activity | OK | 1282.284 | 2475.435 | 2993.688 |
| opencode | SubagentStart | agent-activity | OK | 883.702 | 1926.778 | 2410.601 |
| opencode | SubagentStop | agent-activity | OK | 992.11 | 1427.283 | 1437.878 |
| opencode | SubagentStop | subagent-progress.sh | OK | 2911.362 | 3296.997 | 3397.734 |
| opencode | SessionStart | session-context.sh | OK | 6722.064 | 10089.195 | 11785.363 |
| opencode | SessionEnd | session-journal.sh | OK | 2251.536 | 5033.681 | 6561.76 |
| opencode | UserPromptSubmit | user-prompt-capture.sh | OK | 1932.562 | 2865.395 | 2908.975 |

estimación caracteres/4, redondeo superior; no es un tokenizador ni consumo real

| Runtime | Tokens fijos estimados |
|---|---:|
| claude | 5519 |
| codex | 5512 |
| opencode | 5508 |

| Bajo demanda | Caracteres | Tokens estimados |
|---|---:|---:|
| commands/dev-cycle.md | 53732 | 13433 |
| agent-kits/shared/knowledge-check.md | 9133 | 2284 |
