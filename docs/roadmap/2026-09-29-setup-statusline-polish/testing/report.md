# Informe de QA — setup-statusline-polish

- **Rama / HEAD:** `feature/setup-statusline-polish` @ `d255bff`
- **Modo:** sin UI por diseño (`test-plan: n/a (sin UI)`). No se ejecutó Playwright ni hay `raw/results.json`.
- **Guardrail:** no aplica (no hay E2E ni acceso a hosts).

## Estado global

**⚠️ Parcial.** La iniciativa no tiene UI, así que `qa-gate.py` no tiene nada que evaluar. Su salida (abajo) es una ausencia de resultados, no un rojo de producto. La evidencia sustituta es la ejecución de los tests nombrados por criterio. 16 de 19 criterios salen ✓ en Windows. **CA-06** y **CA-17** salen ✗ parcial por rojos de entorno (detalle en la tabla). **CA-18** queda parcial por los rojos conocidos y un intermitente. La réplica en Linux la documenta el ledger (T-14); esta pasada no la repitió.

## Puertas

- ℹ️ **Sin UI por diseño** (`test-plan: n/a (sin UI)`). La puerta de cobertura NO se ha ejecutado: se aceptó una declaración, no es «cobertura OK».
- `ledger-lint`: 0 incoherencias · 0 avisos.
- `coverage-check`: `applies: false`, `test_plan_na: true`, `marcador_no_canonico: null`, `rutas_ui: []`, `rutas_ui_degradado: null`. Eximidos (`eximidos_exigidos: true`): CA-01, 02, 03, 04, 05, 06, 07, 09, 10, 11, 12, 14. Su evidencia es el campo `Verificación` de la tarea que los cierra y los tests de abajo.
- `qa-gate.py` sobre `testing/raw/results.json`:
  ```json
  {"verdict":"NO-VERDE","reason":"sin resultados: results.json no existe (la ausencia de evidencia es rojo)"}
  ```
  Exit 1. No es un veredicto sobre el producto: no hay E2E. No se hace handoff automático a `documenter` por esta vía; la decisión de cierre es de quien orquesta, con la tabla de abajo.
- `lint_plugin.py`: 0 errores · 3 avisos (nombre genérico, conocidos). `evals/check.py`: 0 errores (151 casos). `export-interop.py --check`: 50 ficheros al día.
- Datos personales: el grep de datos personales sobre las líneas añadidas del diff (`5a08d45..HEAD`) da 1 línea: es el propio comando de verificación citado en el ledger (T-14), no un dato. Este informe tampoco los contiene.

## Criterios y tests ejecutados (Windows)

| CA | Test ejecutado | Resultado |
|---|---|---|
| CA-01 | `test_progress_report.py` + `test_hooks_shell.py -k "en_curso or statusline or ca01…"` | ✓ 26 passed |
| CA-02 | ídem | ✓ |
| CA-03 | ídem | ✓ |
| CA-04 | `test_hooks_shell.py -k jobs_temporal` (incluido en la serie anterior) | ✓ |
| CA-05 | `-k statusline_coste` (incluido en la serie anterior) | ✓ |
| CA-06 | `test_coverage_gate.py -k "lent or timeout or arranque or ausente or falta"`: 6 casos nuevos (timeout con módulo presente, timeout persistente = «no verificado», import fallido = ausente, exit 2 con módulo ausente) | ✓ 6 passed. El fichero completo da 5 failed / 25 passed: son los 5 rojos conocidos de Windows (runner con espacios), ajenos a CA-06 |
| CA-07 | `tests/test_dashboard.py` (`test_evaluaciones_con_las_dos_familias_de_etiquetas`: un caso con las variantes) | ✓ 1 passed |
| CA-08 | `test_backend_markdown_export.py -k 200_upserts` | ✓ 1 passed (una ejecución aquí; las 20 seguidas son del ledger T-01) |
| CA-09 a CA-13 | `test_kwipu_project_add.py` | ✓ 148 passed, 4 skipped (enlaces simbólicos sin privilegio en Windows) |
| CA-14 | `test_knowledge_schema.py`, `test_capabilities.py`, `test_backend_graphiti.py`, `test_graphiti_security.py` | ✓ 505 passed. 1 failed: `test_fix4_gap70_puede_leer_no_repite_verify_dentro_del_ttl`, intermitente por carga conocido y ajeno a CA-14 |
| CA-15 | `-k "ca15 or aviso or estado_grupo"` en `skills/knowledge-services/scripts` | ✓ 29 passed |
| CA-16 | `test_doctor.py -k tope_ms` | ✓ 3 passed |
| CA-17 | `test_knowledge_find.py` + `test_knowledge_index.py` | ✗ 94 passed, 2 failed en Windows: `test_show_imprime_la_entrada_completa_tal_cual` y `test_show_json_envuelve_el_contenido_con_su_ficha`. Causa: el fixture está en LF (`git ls-files --eol`: `i/lf w/lf`), pero la salida de `--show` llega con saltos traducidos por la consola de Windows (`\n\n` y `\r\n`). No son rojos conocidos. Los ~20 tests que dependían de `docs/knowledge/` sí pasan sin él |
| CA-18 | lint 0 errores, evals 0 errores, interop al día; suites: rojos = conocidos + los 2 de CA-17 + el intermitente | ⚠️ parcial. Linux: ver ledger T-14 (3926 passed, 3 failed de entorno), no repetido aquí |
| CA-19 | `git diff 5a08d45..HEAD --stat` incluye `docs/en/`, READMEs y CHANGELOG EN/ES; grep de datos personales sin hallazgos reales | ✓ (revisión de ficheros tocados; sin test automático) |

## Pirámide de pruebas (informativo)

- **E2E:** 0 % por diseño (sin UI, sin Playwright).
- **Unitaria / integración stdlib:** la base. Cobertura de **líneas del diff** según el ledger (no recalculada aquí): 94 % (intento 1), 89 % (fix1), 100 % (fix2).
- **Estáticas:** lint, evals por pieza y `export-interop --check`.

## Rojos conocidos, no tratados como regresión

`test_hooks_shell` (sin `python3` en Windows), 5 de `coverage_gate` (runner con espacios), `test_progress_report::test_session_con_activas…`; intermitentes por carga: `test_bench_session_end`, `test_fix4_gap70`.

## Checklist manual

Sin bloques `M-xx` (no hay test-plan). Sugerencia para una persona: ver la statusline real con 2+ iniciativas activas y revisar que el `▶` marca la esperada.

## Trazabilidad

T-01 → CA-08 · T-02 → CA-17 (✗ en Windows, ver arriba) · T-03 → CA-05 · T-04 → CA-06 · T-05 → CA-07 · T-06 → CA-04 · T-07 → CA-01/02/03 · T-08 → CA-16 · T-09 → ADR · T-10 → CA-14 · T-11 → CA-15 · T-12 → CA-09..13 · T-13 → CA-13 · T-14 → CA-18/19.

## Pendiente antes de cerrar

1. CA-17 en Windows: dos tests comparan la salida de `--show` byte a byte y fallan por los saltos de línea de la consola, no por el fixture. Decidir si se normaliza en el test o se acepta como rojo de entorno (en Linux pasan según el ledger).
2. Sin PDF: el flujo sin UI no lo exige.
