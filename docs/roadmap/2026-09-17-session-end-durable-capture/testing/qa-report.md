# Informe de QA — session-end-durable-capture (2026-09-18)

**Modo: sin UI por diseño** (`test-plan: n/a (sin UI)` en el frontmatter de `improvement-plan.md`, ADR-017). ℹ️ La puerta de cobertura E2E **no se ha ejecutado**: se ha aceptado la declaración. No hay Playwright ni URL.

| Puerta | Comando | Resultado |
|---|---|---|
| Coherencia del ledger | `python3 agent-kits/shared/ledger-lint.py …/tasks.md` | `0 incoherencias · 0 avisos` |
| Cobertura (modo sin UI) | `python3 agent-kits/qa/coverage-check.py tasks.md test-plan.md spec.md` | exit 0 · `test_plan_na: true` · `rutas_ui: []` (diff mirado con base `4a149b0`) · 12 CA listados para revisión (ninguno `[GWT]`, cobertura no exigida; su evidencia es el campo `Verificación` de cada tarea) |
| Suite completa | `python3 -m pytest -q` | `1972 passed, 1 xfailed, 1 failed` — el rojo es `agent-kits/shared/test_task_brief.py::test_tdd_false_o_ausente_no_inyecta`, causado por el `.claude/dev.json` (`tdd: true`) del ENTORNO de trabajo; **sin ese fichero: `63 passed, 1 xfailed`** (verificado). Ajeno a la iniciativa |
| Linter del plugin | `python3 scripts/lint_plugin.py` | `9 agentes · 0 errores · 3 avisos` (nombres genéricos, preexistentes) |
| Interop | `python3 scripts/export-interop.py --check` | `48 ficheros al día` |
| Bench CA-02 | `scripts/bench-session-end.py --iterations 30 --assert-p95-ms 100 --assert-p99-ms 300` | p95 0,94 ms · p99 1,01 ms (in-process) · e2e p50 52 ms |
| CI ≡ copia manual | `python3 tests/test_ci_manual_copy.py` | `7/7 OK` |
| Ledger-lint (regresión) | `python3 tests/test_ledger_lint.py` | `23/23 OK` |
| Instalador (CA-12) | `node --test tests/installer.test.mjs` | `108 pass, 0 fail` |

## Criterios de la spec — evidencia por tarea

CA-01 (T-03, dobles de `git`/`claude` en PATH) · CA-02 (T-07, bench) · CA-03 (T-03/T-04, ×5 = 1 envelope + 1 entrada; verificado a mano en las revisiones) · CA-04 (T-01, tmp huérfano / corte) · CA-05 (T-04, carencia declarada) · CA-06 (T-04, dead-letter) · CA-07 (T-05, huérfanas / sesión viva) · CA-08 (T-05, 100 pendientes en presupuesto; cerrojo ocupado → `bloqueado` < 1 s) · CA-09 (T-03, exec form + rutas con espacios/Unicode) · CA-10 (T-06, triage en `/doctor`) · CA-11 (T-02, `redact.py` fuente única) · CA-12 (T-06, uninstall no toca la cola; `purge --confirm`).

## Verificación manual pendiente (del usuario)

- **M-01**: en Codex real, confirmar que el hook `SessionEnd` de `interop/codex/hooks.json` (shell form, comillas dobles) resuelve `${CLAUDE_PLUGIN_ROOT}` y encola el envelope.
- Copiar a mano `ci.yml.MANUAL-COPY` → `.github/workflows/ci.yml` (fichero protegido para el asistente).

**Veredicto: puertas deterministas en verde; sin UI por diseño (declaración aceptada, no cobertura E2E).**
