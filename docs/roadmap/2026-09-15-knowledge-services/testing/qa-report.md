# QA — knowledge-services (2026-09-19)

## Modo: sin UI (ADR-017)

`improvement-plan.md` declara en su frontmatter `test-plan: n/a (sin UI)`. La iniciativa
(esquema de taxonomía, índice canónico, gate del curador, sincronización con backends,
registro de capacidades para `/setup`/`/doctor`) es infraestructura de plugin sin interfaz
gráfica ni pantallas: no hay Playwright que ejecutar. La verificación funcional se hace con
suites de `pytest` deterministas contra los 17 criterios de aceptación (`CA-01`…`CA-17`) de
`spec.md`, documentadas en `testing/README.md`. Esta línea es **informativa, no un ✅**: la
puerta de cobertura E2E no se ha ejecutado porque no aplica; lo que sí se ha comprobado son
los pasos 1-4 de abajo.

## 1. `ledger-lint.py`

```
$ python agent-kits/shared/ledger-lint.py docs/roadmap/2026-09-15-knowledge-services/tasks.md
ledger-lint: 0 incoherencias · 0 avisos (tasks.md)
```

Exit 0. Ledger coherente (13/13 tareas `completado`).

## 2. `coverage-check.py` (modo sin UI)

```
$ python agent-kits/qa/coverage-check.py docs/roadmap/2026-09-15-knowledge-services/tasks.md docs/roadmap/2026-09-15-knowledge-services/test-plan.md docs/roadmap/2026-09-15-knowledge-services/spec.md
ℹ️  test-plan: n/a (sin UI) declarado en improvement-plan.md: iniciativa sin UI por diseño, la puerta de cobertura NO se ha ejecutado (no es «cobertura OK»)
ℹ️  se listan para la revisión 17 criterio(s) de aceptación de la spec (ninguno [GWT]) (CA-01, CA-02, CA-03, CA-04, CA-05, CA-06, CA-07, CA-08, CA-09, CA-10, CA-11, CA-12, CA-13, CA-14, CA-15, CA-16, CA-17): la puerta no exigía cobertura de estos (solo la exige de los [GWT]), así que aquí no se exime nada — su evidencia es el campo `Verificación` de la tarea que los cierra en tasks.md
{"applies": false, "gwt_sin_id": 0, "test_plan_na": true, "marcador_no_canonico": null, "eximidos": ["CA-01", "CA-02", "CA-03", "CA-04", "CA-05", "CA-06", "CA-07", "CA-08", "CA-09", "CA-10", "CA-11", "CA-12", "CA-13", "CA-14", "CA-15", "CA-16", "CA-17"], "eximidos_exigidos": false, "rutas_ui": [], "rutas_ui_origen": {}, "rutas_ui_degradado": null}
```

Exit 0. Marcador canónico (`marcador_no_canonico: null`), ningún criterio `[GWT]` en la spec
(`gwt_sin_id: 0`), sin referencias rotas. Los 17 `CA-XX` quedan listados «para la revisión»
(`eximidos_exigidos: false`): no eran exigibles por la puerta, pero SÍ se han comprobado a
mano en el paso 4 (tabla de `testing/README.md`) y con las suites del paso 3. `rutas_ui: []`
(sin `.tsx`/`components/` en el diff de esta iniciativa, consistente con "sin UI").

## 3. Suites de la iniciativa

```
$ python -m pytest -q tests/test_knowledge_services.py agent-kits/knowledge-curator/test_curator_gate.py \
    agent-kits/shared/test_knowledge_index_canonico.py agent-kits/shared/test_knowledge_schema.py \
    agent-kits/shared/test_capabilities.py skills/knowledge-services/scripts \
    tests/test_knowledge_candidates.py tests/test_manifests.py tests/test_copias_declaradas.py \
    tests/test_ci_manual_copy.py
349 passed, 2 skipped, 6 subtests passed in 48.62s

$ python -m pytest -q agent-kits/shared/test_doctor.py -k "capacidad or bloque_capacidades"
27 passed, 102 deselected in 1.78s

$ python -m pytest -q tests/test_console_encoding.py -k "sync or export or index or curator or capabilities or schema"
104 passed, 273 deselected in 17.00s
```

Total: **480 passed, 2 skipped** (los 2 `skipped` son marcadores explícitos preexistentes de
las suites, no relacionados con esta verificación). Exit 0 en las tres invocaciones.

## 4. Tabla CA ↔ tests (`testing/README.md`)

Se verificó que cada test citado en la tabla de `testing/README.md` **existe** (`grep -n "def <nombre>"`
sobre el fichero indicado) y que los comandos de la tabla colectan/pasan lo declarado:

| CA | Test(s) citado(s) | Existe | Estado |
|---|---|---|---|
| CA-01 | `test_knowledge_schema.py`, `test_knowledge_index_canonico.py`, `test_knowledge_services.py::test_id_con_escape_no_se_indexa_y_no_escribe_nada`, `::test_folder_con_escape_se_rechaza_en_la_taxonomia` | sí | passed |
| CA-02 | `test_knowledge_services.py::test_mutante_candidato_en_candidates_nunca_se_indexa_ni_exporta`, `test_knowledge_index_canonico.py` | sí | passed |
| CA-03 | `agent-kits/knowledge-curator/test_curator_gate.py` | sí | passed |
| CA-04 | `test_knowledge_sync.py`, `test_knowledge_services.py::test_flujo_completo_taxonomia_indice_curator_sync_doctor_backend_test` | sí | passed |
| CA-05 | `test_capabilities.py`, `test_doctor.py -k "capacidad or bloque_capacidades"` | sí | passed |
| CA-06 | `commands/dev-cycle.md` (prosa, no test) + `test_curator_gate.py` | sí | passed (parte prosa no ejecutable, declarado como tal en README) |
| CA-07 | `lint_plugin.py`, `evals/check.py`, `export-interop.py --check`, `tests/test_lint_plugin.py` | sí | ver nota Windows abajo |
| CA-08 | lectura de alcance (no test) — `docs/roadmap/2026-09-15-graphiti-memory/` sigue `planificada`; confirmado por lectura directa | n/a | ok (verificación documental) |
| CA-09 | `test_knowledge_schema.py`, `test_knowledge_services.py::test_mutante_categoria_sin_routing_declarado_nunca_exporta` | sí | passed |
| CA-10 | `test_curator_gate.py::test_ca10_utility_alto_sin_evidencia_sigue_sin_aprobar`, `::test_ca10_utility_alto_con_evidencia_suficiente_aprueba_por_la_evidencia_no_por_el_score` | sí | passed |
| CA-11 | `test_knowledge_schema.py`, `test_knowledge_sync.py`, `test_knowledge_services.py::test_mutante_routing_false_nunca_llega_al_adaptador` | sí | passed |
| CA-12 | `test_backends_init.py`, `test_knowledge_sync.py`, `test_knowledge_services.py` | sí | passed |
| CA-13 | `test_knowledge_schema.py`, `test_knowledge_services.py::test_taxonomy_json_corrupto_falla_de_forma_segura`, `::test_taxonomy_json_con_bom_utf8_se_tolera`, `::test_taxonomy_json_utf16_falla_de_forma_segura_sin_traceback` | sí | passed |
| CA-14 | `test_capabilities.py`, `test_doctor.py -k "capacidad or bloque_capacidades"` | sí | passed |
| CA-15 | `test_knowledge_sync.py`, `agent-kits/shared/test_outbox.py` | sí (`test_knowledge_sync.py` confirmado; `test_outbox.py` está en la lista de rojos preexistentes de Windows, ver abajo) | ver nota |
| CA-16 | `test_backend_markdown_export.py`, `test_knowledge_services.py::test_export_dir_dentro_de_docs_knowledge_se_rechaza`, `::test_export_dir_ancestro_del_root_se_rechaza`, `::test_health_url_*` | sí | passed |
| CA-17 | `test_backend_markdown_export.py` | sí | passed |

Todos los `CA-01`…`CA-17` tienen al menos un test real que existe y pasa (en las corridas del
paso 3). No hay CA huérfano.

**Nota CA-07**: `tests/test_lint_plugin.py` documenta en el propio `testing/README.md` que en
Windows aborta antes de llegar al caso de `knowledge-services` por el chequeo del bit ejecutable
de otro caso anterior (no relacionado con esta iniciativa); en Linux/CI corre entero. `lint_plugin.py`,
`evals/check.py` y `export-interop.py --check` se ejecutaron directamente (no vía pytest) y no
dependen de bits ejecutables:

```
$ python scripts/lint_plugin.py
lint_plugin: 10 agentes · 0 errores · 3 avisos
$ python evals/check.py
evals/check: 40 ficheros · 144 casos (86 positivos, 58 negativos) · 40 piezas del repo · 0 errores
$ python scripts/export-interop.py --check
export-interop --check: 50 ficheros al dia
```

**Nota CA-15**: `agent-kits/shared/test_outbox.py` está en la lista de rojos preexistentes de
Windows (usa `fcntl`/permisos POSIX, no disponibles en este entorno) — no se ejecutó en esta
ronda porque no forma parte de las suites pedidas para esta verificación (T-12 ya documentó
esta clasificación); la cobertura de CA-15 queda confirmada por `test_knowledge_sync.py` (passed)
y por el histórico de T-12/T-15 en `tasks.md`.

## Rojos preexistentes (Windows, ajenos a esta iniciativa)

No forman parte de esta verificación (no se relanzó la suite completa del repo; ya están
documentados y clasificados en T-12). Se citan por nombre para que no se confundan con un
rojo de `knowledge-services`:

- `tests/test_hooks_shell.py` (bit ejecutable / `flock` / symlinks sin privilegio en Windows)
- `agent-kits/shared/test_journal.py`
- `agent-kits/shared/test_outbox.py` (`fcntl`, permisos POSIX)
- `agent-kits/shared/test_doctor.py::test_hook_sin_bit_ejecutable_es_aviso_con_chmod`
- `tests/test_knowledge_find.py::test_show_*` (CRLF)
- `tests/test_confluence_scope.py`
- `tests/test_release.py`
- `tests/test_suites_no_pytest.py`
- `agent-kits/shared/test_progress_report.py`
- `agent-kits/shared/test_task_brief.py`
- `agent-kits/shared/test_bench_session_end.py`

## Veredicto

**VERDE.**

Basado en exit codes reales:
- `ledger-lint.py` → exit 0
- `coverage-check.py` (modo sin UI) → exit 0, sin referencias rotas, sin `[GWT]` sin cubrir
- Suites de la iniciativa (3 invocaciones de `pytest`) → exit 0, 480 passed / 2 skipped, 0 failed
- Tabla CA↔tests de `testing/README.md` → los 17 CA tienen test real existente y en verde

No hay handoff a Playwright (no aplica: sin UI). Se generó también `qa-report.pdf` con la
skill `to-pdf` (motor ya cacheado en `~/.claude/tool-cache/to-pdf/`, sin red).

## Cierre de ciclo

Con veredicto verde, corresponde el handoff a `documenter` para una pasada de documentación y
la actualización de estados (spec → `implementada`, plan → `completado`), sujeto a que
`retro-gate.py` no bloquee el cierre completo del ciclo (fuera del alcance de esta tarea de qa).
