# Informe QA — training-data-services (modo sin UI)

Fecha: 2026-09-29 · Rama `feature/training-data-services` · HEAD `42046f1`

## Estado global

**ℹ️ Sin UI por diseño (`test-plan: n/a (sin UI)`).** No hay E2E ni `results.json`; los E2E no se ejecutan y no se presentan como verdes.
Veredicto de la evidencia alternativa (suites de la skill y del repo): **verde para la iniciativa**; los 16 rojos de `tests/test_hooks_shell.py` son entorno Windows preexistente (ver abajo).

- `qa-gate.py` sobre `testing/raw/results.json` (inexistente, no hay E2E), salida tal cual (exit 1):
  ```json
  {"verdict": "NO-VERDE", "reason": "sin resultados: results.json no existe (la ausencia de evidencia es rojo)"}
  ```
  Ese rojo es de ausencia de E2E, coherente con «sin UI»; no juzga la calidad. El veredicto efectivo sale de las suites de más abajo.
- `ledger-lint`: 0 incoherencias · 0 avisos.
- `coverage-check` (exit por «n/a»): `applies: false`, `test_plan_na: true`, `gwt_sin_id: 0`, `marcador_no_canonico: null`. ℹ️ La puerta de cobertura NO se ha ejecutado (se acepta la declaración). No hay criterios `[GWT]`; se listan los 12 CA (`eximidos_exigidos: false`): su evidencia es el campo `Verificación` de la tarea que los cierra.
- ⚠️ `rutas_ui` (origen `ledger`): `assets/` y `skills/training-data-services/assets/`. No son UI: son plantillas/ejemplos de datos del case store (JSON/README). El marcador «sin UI» es correcto; queda dicho aquí. `rutas_ui_degradado: null` (el diff sí se miró).
- Guardrail: no aplica (sin URL ni host).

## Criterios de aceptación → test (ejecutados)

Ejecución: `pytest -q skills/training-data-services/scripts agent-kits/shared/test_capabilities.py agent-kits/shared/test_doctor.py agent-kits/shared/test_redact.py tests/test_training_data_services.py tests/test_hooks_shell.py` → **948 passed, 12 skipped, 16 failed** (17 min). Los 16 failed son todos `test_hooks_shell.py`; **0 fallos** en skill, capabilities, doctor, redact y `test_training_data_services.py`. Los 12 skipped son symlinks de fichero sin privilegio en Windows.

| CA | Criterio | Test(s) nombrado(s) | Resultado |
|---|---|---|---|
| CA-01 | Cero impacto sin `training.json`/`enabled:false` | `tests/test_training_data_services.py::test_ca01_sin_training_json_o_desactivado_el_ciclo_es_identico`, `::test_ca01_ningun_script_del_ciclo_lee_training_json`; `test_capabilities.py` (training sin fichero); `test_doctor::test_t10_sin_training_json_doctor_no_reporta_nada_de_la_capacidad`; `test_case_recorder::test_t04_sin_config_desactivada_o_invalida_rechaza_sin_escribir` | ✓ |
| CA-02 | Nunca sobrescribe `case_id`+versión; rechazados se conservan | `test_case_recorder::test_t04_version_siguiente_libre_y_nunca_sobrescribe`, `::test_f2fix5_gap96_o_excl_nunca_sobrescribe_…`, docstring CA-02 (sin borrado) | ✓ |
| CA-03 | Solo Gold humano llega al dataset | `test_dataset_assembler::test_t09_solo_gold_entra_en_el_dataset`, `::test_t09_gold_exige_approved_by_human_true_en_el_fichero`; `tests/test_training_data_services.py::test_ningun_no_gold_ni_gold_sin_atar_llega_al_dataset` | ✓ |
| CA-04 | Sin métricas/lógica de dominio en el plugin | `tests/…::test_ca04_metrics_es_opaco_el_plugin_no_tiene_metricas_de_dominio`; `test_case_recorder::test_t04_sin_red_ni_dominio` | ✓ |
| CA-05 | Gold se propone, nunca se aprueba solo | `test_propose_from_case::test_t09_puente_nunca_aprueba_nada`, `::test_t09_puente_sin_bridge_to_curator_exit_1_sin_escribir` | ✓ |
| CA-06 | Benchmark reservado y near-duplicates señalados | `test_dataset_assembler::test_t08_leakage_near_duplicate_que_cruza_la_particion_sale_de_train`, `::test_t09_near_duplicates_en_el_manifiesto_y_cruce_excluido` | ✓ |
| CA-07 | `/doctor` informa sin bloquear | `test_doctor::test_t10_training_activo_informa_recuento_y_dataset_sin_bloquear`, `::test_t10_training_desactivado_con_fichero_es_informativo`, `::test_t10_training_config_invalida_es_error_con_fichero_y_campo` | ✓ |
| CA-08 | No entrena, no sirve, no corre benchmarks | `tests/…::test_ca08_la_skill_no_entrena_ni_sirve_ni_ejecuta_nada`; `test_dataset_assembler::test_t09_no_entrena_ni_sirve_ni_usa_red_ni_borra` | ✓ |
| CA-09 | Redacción antes de escribir, misma lógica que `journal.py` | `test_case_recorder::test_redactar_es_la_de_redact_py`, `::test_t04_redacta_request_context_constraints_y_trayectoria_antes_de_escribir`, `::test_f2fix1_gap44_todo_texto_libre_se_redacta`; `test_redact.py` | ✓ |
| CA-10 | Near-duplicates por shingles, sin embeddings ni red | `test_dedup.py::test_t07_dos_versiones_casi_identicas_forman_un_grupo`, `::test_t07_componentes_conexas_transitivas` | ✓ |
| CA-11 | Familia completa a un solo lado | `test_dataset_assembler::test_t08_leakage_toda_version_de_una_familia_va_al_mismo_lado`, `::test_t08_leakage_nunca_se_excluye_el_lado_de_benchmark_…` | ✓ |
| CA-12 | `failure` → `corrected` conserva `supersedes_case` en el dataset | `test_dataset_assembler` (#120: v1 failure + v2 corrected supersedes v1); `test_case_recorder::test_t04_corrected_exige_que_exista_la_version_que_corrige`, `::test_f2fix1_gap39_supersedes_exige_failure_o_corrected`; `test_case_schema::test_corrected_exige_supersedes_case_bien_formado` | ✓ |

12/12 ✓ (los tests nombrados están dentro de la ejecución anterior sin fallos).

## Pirámide de pruebas

| Capa | Suite | Resultado |
|---|---|---|
| Unit de la skill | `skills/training-data-services/scripts/test_*.py` (schema, recorder, dedup, assembler, propose, assets) | pasan todos |
| Integración / capacidad | `agent-kits/shared/test_capabilities.py`, `test_doctor.py`, `test_redact.py` | pasan todos |
| Suite de repo (iniciativa) | `tests/test_training_data_services.py` | pasa entera |
| Suite de repo (hooks) | `tests/test_hooks_shell.py` | 16 rojos, todos de entorno Windows (ver abajo) |
| E2E | — | no aplica (sin UI) |

Cobertura (citada del ledger, no recalculada): checkout limpio, fase **95,01 %** (`doctor.py` 92,18 %) e iniciativa **94,99 %**, todos los ficheros ≥ 90 % (#185; «Salida real fix4» de T-10). Ledger, fix4: `1322 passed, 12 skipped`, `lint_plugin` 0 errores, `evals/check` 0, `export-interop --check` al día, mutantes 17/17 muertos.

### Rojos de `test_hooks_shell.py` (16)
Familia de entorno Windows registrada en el ledger como igual en la base sin cambios de la iniciativa (`test_hooks_shell` ×16 tanto en HEAD como en el worktree limpio de la base): `progress_line_*` (6), `*sin_python3*`, bit de ejecución POSIX (`test_todos_los_hooks_son_bash_valido_y_ejecutables`), `mark_docs_pending`, `ledger_lint_warn`, captura de prompts. CI es Linux; la iniciativa pasó `tests/test_hooks_shell.py` en Linux (ledger, T-11). No se ha vuelto a verificar en Linux en esta ejecución. Honestidad: `test_user_prompt_capture_acumula_…` aparece en rojo aquí; el ledger ya documenta que depende de la ubicación del checkout, no del código.

## Checklist manual
Sin UI, no hay `M-xx`. Pendiente manual razonable: comprobar `/doctor` en un proyecto real con `training.json` activo y ver que la línea «training» aparece sin bloquear.

## Trazabilidad
T-01…T-11 → CA-01…CA-12 vía el campo `Verificación` de cada tarea en `tasks.md`; tabla arriba.

## Entregables
`report.pdf` no se ha generado (la skill `to-pdf` no se ha ejecutado en este flujo; degrada sin bloquear).
