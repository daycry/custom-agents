# knowledge-services — QA sin UI

Esta iniciativa (ADR-018) no tiene interfaz gráfica: es infraestructura del plugin (esquema de
taxonomía, índice, gate del curador, sincronización con backends, registro de capacidades para
`/setup`/`/doctor`). El plan declara `test-plan: n/a (sin UI)` (patrón ADR-017) — no hay Playwright
que ejecutar ni pantallas que capturar. La cobertura de los 17 criterios de aceptación (`CA-01`
… `CA-17` de `spec.md`) se hace con **suites de `pytest` deterministas**, sin red real: los casos
de red usan un servidor HTTP efímero en `127.0.0.1` (`http.server`) o el backend `type: "test"` de
`evals/fixtures/knowledge-services/backend_test.py`.

## Cómo se verifica el ciclo completo

```
python -m pytest -q tests/test_knowledge_services.py                                    # E2E
python -m pytest -q agent-kits/shared/test_knowledge_schema.py                           # CA-01/09/11/13
python -m pytest -q agent-kits/shared/test_knowledge_index_canonico.py tests/test_knowledge_index.py  # CA-01/02
python -m pytest -q agent-kits/knowledge-curator/test_curator_gate.py                    # CA-03/06/10
python -m pytest -q skills/knowledge-services/scripts/test_knowledge_sync.py             # CA-04/09/11/12/15
python -m pytest -q skills/knowledge-services/scripts/test_backend_markdown_export.py    # CA-16/17
python -m pytest -q skills/knowledge-services/scripts/test_backends_init.py              # CA-12
python -m pytest -q agent-kits/shared/test_capabilities.py agent-kits/shared/test_doctor.py -k knowledge  # CA-05/14
python scripts/lint_plugin.py && python evals/check.py && python scripts/export-interop.py --check       # CA-07
```

## Cobertura criterios ↔ tests (CA-01 … CA-17)

| CA | Criterio (resumen) | Tests que lo cubren |
|---|---|---|
| CA-01 | El esquema valida categorías/evidencia contra `taxonomy.json` (o el default) y rechaza estados/IDs/tags/referencias inválidas | `agent-kits/shared/test_knowledge_schema.py` (validación de forma) · `agent-kits/shared/test_knowledge_index_canonico.py` + `tests/test_knowledge_index.py` (índice sobre `approved/`) · `tests/test_knowledge_services.py::test_id_con_escape_no_se_indexa_y_no_escribe_nada`, `::test_folder_con_escape_se_rechaza_en_la_taxonomia` |
| CA-02 | Candidatos, rechazados, journal, logs y derivados nunca se exportan a Kwipu | `tests/test_knowledge_services.py::test_mutante_candidato_en_candidates_nunca_se_indexa_ni_exporta` (índice NUNCA escanea `candidates/**`) · `agent-kits/shared/test_knowledge_index_canonico.py` (solo escanea `approved/<folder>`) |
| CA-03 | Solo el Curator puede aprobar/rechazar/pedir cambios o sustituir conocimiento | `agent-kits/knowledge-curator/test_curator_gate.py` (contrato `evaluar()`, único escritor de la decisión) |
| CA-04 | El export es idempotente, atómico y reconstruible desde `approved/` | `skills/knowledge-services/scripts/test_knowledge_sync.py` (manifiesto pendiente/aplicado, `--rebuild`) · `tests/test_knowledge_services.py::test_flujo_completo_...` (`--rebuild` sobre las entradas ya enrutadas) |
| CA-05 | Setup y doctor gestionan Kwipu como capacidad opcional y degradable | `agent-kits/shared/test_capabilities.py` · `agent-kits/shared/test_doctor.py -k knowledge` |
| CA-06 | La curación sucede solo después de QA/documentación y no altera cierres sin candidatos | `commands/dev-cycle.md` (Fase 4-bis, prosa del orquestador, T-06 — omisión honesta) · `agent-kits/knowledge-curator/test_curator_gate.py` (el gate no decide POR SÍ SOLO cuándo se invoca) |
| CA-07 | Interop, contratos y documentación ES/EN permanecen sincronizados | `python scripts/lint_plugin.py` (rutas citadas, matriz de `CONTRACTS.md`) · `python scripts/export-interop.py --check` · `tests/test_lint_plugin.py::caso_citas_rutas_skill_knowledge_services` |
| CA-08 | Esta entrega no implementa Graphiti | Lectura de alcance: `docs/roadmap/2026-09-15-graphiti-memory/` es una iniciativa SEPARADA y `en 2026-09-19` sigue `planificada`; ningún fichero de `knowledge-services` importa ni referencia un cliente Graphiti/MCP |
| CA-09 | Categoría sin enrutado declarado no exporta a ningún backend (fail-closed); el plugin sigue funcionando con la taxonomía default | `agent-kits/shared/test_knowledge_schema.py` · `tests/test_knowledge_services.py::test_mutante_categoria_sin_routing_declarado_nunca_exporta` |
| CA-10 | Con `utility_scoring` activo, el score nunca decide un estado por sí solo | `agent-kits/knowledge-curator/test_curator_gate.py` (mutante: `utility=10` sin evidencia sigue sin aprobar) |
| CA-11 | `routing` solo puede citar ids declarados en `backends`; un id no declarado es error de validación (fail-closed) | `agent-kits/shared/test_knowledge_schema.py` · `skills/knowledge-services/scripts/test_knowledge_sync.py` · `tests/test_knowledge_services.py::test_mutante_routing_false_nunca_llega_al_adaptador` |
| CA-12 | El contrato de adaptador es extensible sin tocar el núcleo (`type: "test"` recibe exactamente lo que le enruta la taxonomía) | `skills/knowledge-services/scripts/test_backends_init.py` (`cargar_adaptador`, `FUNCIONES_OBLIGATORIAS`) · `skills/knowledge-services/scripts/test_knowledge_sync.py` · `tests/test_knowledge_services.py` (backend `test` de fixture, flujo E2E completo) |
| CA-13 | `taxonomy.json` se valida contra `taxonomy.schema.json` con validador stdlib; `/doctor` señala fichero/campo/arreglo | `agent-kits/shared/test_knowledge_schema.py` · `tests/test_knowledge_services.py::test_taxonomy_json_corrupto_falla_de_forma_segura`, `::test_taxonomy_json_con_bom_utf8_se_tolera`, `::test_taxonomy_json_utf16_falla_de_forma_segura_sin_traceback` |
| CA-14 | `/setup`/`/doctor` enumeran capacidades desde `capabilities.py` sin código específico por capacidad en `doctor.py` | `agent-kits/shared/test_capabilities.py` · `agent-kits/shared/test_doctor.py::test_doctor_capacidad_sin_fila_es_error...` (CA-14 citado en el propio test) |
| CA-15 | El exportador usa `outbox.py` (staging atómico, manifiesto, dead-letter); no reimplementa la cola | `skills/knowledge-services/scripts/test_knowledge_sync.py` (citado CA-15 en el propio test: `apply()` roto no borra nada previo) · `agent-kits/shared/test_outbox.py` |
| CA-16 | El adaptador `markdown-export` escribe en `export_dir`; el reindexado es del stack, `verify` detecta el desfase y lo nombra sin ejecutarlo | `skills/knowledge-services/scripts/test_backend_markdown_export.py` · `tests/test_knowledge_services.py::test_export_dir_dentro_de_docs_knowledge_se_rechaza`, `::test_export_dir_ancestro_del_root_se_rechaza`, `::test_health_url_*` (SSRF/redirección) |
| CA-17 | El frontmatter exportado lleva `project/scope/category/source/confidence` + `knowledge_id/version/hash`, sin inventar campos | `skills/knowledge-services/scripts/test_backend_markdown_export.py` |

## Rojos preexistentes (fuera de alcance de esta iniciativa)

La ejecución completa de `python -m pytest tests agent-kits/shared agent-kits/knowledge-curator
skills/knowledge-services/scripts -q` (T-12, ronda 2026-09-19) mantiene un conjunto de fallos
**ajenos a `knowledge-services`**, todos artefactos de ejecutar en Windows en vez de Linux (CI real):
bit ejecutable (`os.stat().st_mode`) que Windows no preserva igual que POSIX, `flock` no disponible,
`WinError 1314` al crear symlinks sin privilegio elevado, y diferencias de rutas/`.gitignore` entre
sistemas. Ninguno toca código de esta iniciativa (`knowledge-schema.py`, `knowledge-index.py`,
`curator-gate.py`, `knowledge-sync.py`, `backends/`, `capabilities.py`) ni sus tests nuevos — el
detalle de la clasificación exacta de esta ronda vive en la nota de verificación de T-12 en
`../tasks.md`.

## Retro

`/retro` (fuera de esta tarea: la ejecuta el orquestador al cerrar el ciclo, no el `implementer`)
es la puerta de cierre — `agent-kits/shared/retro-gate.py docs/roadmap/2026-09-15-knowledge-services`
falla mientras no exista `retro.md` con su fila; eso es esperado en este punto (T-12 cierra la
Fase 4, pero el ciclo completo lo cierra `/dev-cycle`).
