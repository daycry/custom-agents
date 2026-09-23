---
verificacion: obligatoria
---

# Checklist de Tareas - Captura de casos y dataset

| **Estado** | en-progreso |
|---|---|
| **Plan** | [improvement-plan.md](improvement-plan.md) |
| **Diseno** | [design.md](design.md), O1 |

> **Ledger canonico de progreso.** Los casos y el dataset viven fuera de Git; el avance de ESTA iniciativa sigue en Git.

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervision (real/est) | Tokens (real/est) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fase 1 - Config, redaccion compartida y capacidad | 0 | 3 | 0% (reabiertas por la revisión intento 1: fix1 pendiente) | 0 / 6.5h | 0.41 / 2.0h | 0 / 0.5h | ~70k out+in? / 85k (T-01 0.22h · T-02 0.12h · T-03 0.07h; tokens por marcador: 37.8k · 17.3k · 14.4k de salida) |
| Fase 2 - Recorder y puerta humana | 0 | 3 | 0% | 0 / 8h | 0 / 2.4h | 0 / 0.6h | 0 / 120k |
| Fase 3 - Dedup, particion y ensamblador | 0 | 3 | 0% | 0 / 14h | 0 / 4.2h | 0 / 1.1h | 0 / 210k |
| Fase 4 - Setup, doctor y cierre | 0 | 2 | 0% | 0 / 11h | 0 / 3.3h | 0 / 0.8h | 0 / 160k |
| **TOTAL** | **0** | **11** | **0%** | **0 / 39.5h** | **0.41 / 11.9h** | **0 / 3.0h** | **medido / 575k** |

## Fase 1 - Config, redaccion compartida y capacidad

### T-01 - Esquema de `training.json` y del caso
- **Estado**: en-progreso
- **Tiempo humano**: est. 3h · real -
- **Tiempo IA**: real 0.22h (medido; usage-meter `training-data-services/T-01`, 13m, 37.8k out tok)
- **Prevision IA**: 35k in / 14k out tok
- **Dependencias**: ninguna
- **Tipo**: docs
- **Archivos**: `skills/training-data-services/SKILL.md`, `skills/training-data-services/scripts/case_schema.py`, `skills/training-data-services/scripts/test_case_schema.py`, `evals/cases/skill-training-data-services.json`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `docs/README.md`, `docs/en/README.md`, `CLAUDE.md`, `interop/**` (nota: el plan citaba agent-kits/shared/, que T-01 no toca; la skill nueva exige fila en docs/README.md, docs/en/README.md y CLAUDE.md (regla de plugin-dev) y entra en el indice generado `interop/opencode/custom-agents-index.md`)
- **Verificacion**: `python -m pytest -q skills/training-data-services/scripts/test_case_schema.py` -> valida `training.json` y esquema de caso, rechaza estados/outcome invalidos
  - Salida real (2026-09-23): `36 passed in 1.10s`
- **RED**: `test_case_schema.py` (todo el modulo) fallo en la coleccion con `FileNotFoundError: [Errno 2] No such file or directory: '.../skills/training-data-services/scripts/case_schema.py'` · 2026-09-23
- **Nota**: decisiones con margen — (1) nombre del validador `case_schema.py` (con guion bajo: lo importan recorder/ensamblador); (2) `root` dentro de `docs/knowledge/` se rechaza (coherente con ADR-019 de T-03); (3) clave desconocida en `training.json` es error (erratas visibles; `$comment` admitido); (4) `validation.approved_by_human: true` con status distinto de `approved` es error (coherencia); (5) ajuste del orquestador 2026-09-23: `OUTCOME_MAPEO["graphify"]` = `useful->success · dead_end->failure · corrected->corrected` + `mapear_outcome()`, sin ampliar el vocabulario cerrado; `context.refs` opcional `[{ref, kind}]`; (6) estructura de ids = la de `design.md` (`cases/<family>.<variant>/v<NNN>`).
- **Changelog**: New opt-in `training-data-services` skill: `training.json` config and a dependency-free case schema validator with closed status/outcome vocabularies and a declared mapping from `useful|dead_end|corrected`.
**Criterios de aceptación**
- [x] `training.json` declara root, `id_prefix`, y si el puente a `knowledge-curator` esta activo.
- [x] El esquema del caso exige `case_id`, `version`, `outcome`, y valida `validation.status` contra el vocabulario cerrado.

### T-02 - Consumir `redact.py` compartido y registrar la capacidad `training`
- **Estado**: en-progreso
- **Tiempo humano**: est. 1.5h · real -
- **Tiempo IA**: real 0.12h (medido; usage-meter `training-data-services/T-02`, 7m, 17.3k out tok)
- **Prevision IA**: 18k in / 7k out tok
- **Dependencias**: `session-end-durable-capture` T-02 (`redact.py`), `knowledge-services` T-13 (`capabilities.py`) — ambas cerradas (`session-end-durable-capture` en `completado`; `redact.py` y `capabilities.py` presentes)
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/capabilities.py`, `agent-kits/shared/test_capabilities.py`, `skills/training-data-services/scripts/case-recorder.py`, `skills/training-data-services/scripts/test_case_recorder.py`, `skills/training-data-services/SKILL.md`, `tests/test_console_encoding.py`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md` (nota: `case-recorder.py` nace aqui minimo —solo la redaccion delegada— con el nombre que fija T-04; `test_console_encoding.py` exige declarar el modo de arranque de todo script con no-ASCII: cubre `case_schema.py` de T-01, que se habia quedado fuera, y `case-recorder.py`; el parrafo del registro de capacidades de CONVENTIONS ES/EN describe la entrada nueva, E3)
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_capabilities.py -k training agent-kits/shared/test_redact.py` -> la capacidad `training` expone enabled/health/doctor/setup_step; el recorder importa `redactar` de `redact.py` (una sola fuente)
  - Salida real (2026-09-23): `10 passed, 21 deselected in 0.29s` (el `-k training` filtra tambien `test_redact.py`); sin filtro: `python -m pytest -q skills/training-data-services/scripts agent-kits/shared/test_redact.py agent-kits/shared/test_capabilities.py` -> `72 passed in 1.22s`; `tests/test_console_encoding.py` -> `393 passed`; `agent-kits/shared/test_doctor.py` -> `131 passed, 1 skipped`
- **RED**: `test_training_*` de `test_capabilities.py` (9 de 10) fallaron con `StopIteration` (no hay capacidad `training` en `REGISTRO`); `test_case_recorder.py` fallo en la coleccion con `FileNotFoundError: ... skills/training-data-services/scripts/case-recorder.py` · 2026-09-23
- **Nota**: decisiones con margen — (1) `capabilities.py` valida `training.json` cargando `case_schema.py` de la skill (una sola fuente del esquema; skills/ y agent-kits/ son hermanos); sin la skill degrada a `declarado` sin validacion propia; (2) config invalida -> `health.estado: error` con fichero y campo (mismo trato que `knowledge-gate`: /doctor lo pinta en rojo pero el ciclo no se bloquea); (3) sin `redact.py` el recorder levanta `RedaccionNoDisponible` en vez de caer a una copia local (fail closed); (4) `doctor.py` sin tocar (`grep -c training` -> 0). Pendiente para T-11: registrar en `docs/agents/CONTRACTS.md` el acoplamiento nuevo `agent-kits/shared/capabilities.py` -> `skills/training-data-services/scripts/case_schema.py`.
- **Changelog**: `/doctor` and `/setup` now list the opt-in `training` capability (off without `training.json`, no network), and case redaction reuses the plugin's single shared secret-redaction module.
**Criterios de aceptación**
- [x] **Enmienda 2026-09-17**: la extraccion de `redact.py` desde `journal.py` la hace `session-end-durable-capture` (unica iniciativa que refactoriza `journal.py`); aqui solo se consume. Sin esa dependencia cerrada, esta tarea queda `bloqueada`.
- [x] `redact.py` sigue siendo la unica fuente de los patrones de secretos del plugin; el recorder no define ninguno propio.

### T-03 - Plantillas y estructura de directorios del case store
- **Estado**: en-progreso
- **Tiempo humano**: est. 2h · real -
- **Tiempo IA**: real 0.07h (medido; usage-meter `training-data-services/T-03`, 4m, 14.4k out tok)
- **Prevision IA**: 20k in / 8k out tok
- **Dependencias**: T-01
- **Tipo**: docs
- **Archivos**: `skills/training-data-services/assets/`, `skills/training-data-services/scripts/test_assets.py`, `skills/training-data-services/SKILL.md`, `docs/knowledge/adr/`, `docs/knowledge/README.md` (nota: `test_assets.py` convierte la verificacion «lectura» en una comprobacion ejecutable de que el ejemplo valida con `case_schema.py` y sigue `design.md`; `SKILL.md` gana la fila de `assets/`)
- **Verificacion**: lectura: la estructura documentada coincide con `design.md`
  - Salida real (2026-09-23): lectura hecha — `assets/README.md` reproduce el arbol de `design.md` (`<root>/cases_index.jsonl`, `cases/<family>.<variant>/v<NNN>/{metadata,request,context,constraints,metrics,validation}.json + trajectory.jsonl + final/`, `exports/<export_id>/{manifest.json,train.jsonl,benchmark.jsonl}`); ejecutable: `python -m pytest -q skills/training-data-services/scripts/test_assets.py` -> `7 passed in 0.04s`; skill completa `python -m pytest -q skills/training-data-services/scripts` -> 48 passed (con `test_knowledge_index.py`/`test_skill_size.py`: `86 passed`)
- **RED**: `test_assets.py` 6 de 7 fallaron con `FileNotFoundError` (sin `assets/training.example.json`, `assets/README.md` ni `assets/case-store-example/`) · 2026-09-23
- **Nota**: decisiones con margen — (1) las «plantillas comentadas» son un ejemplo completo y validable (`case-store-example/`, caso `geo-ramp.steep` con `v001` failure/rejected conservada y `v002` corrected/Gold humano) + `README.md` con la tabla de campos, porque JSON no admite comentarios y un `$comment` dentro de `metadata.json` ensuciaria los casos reales; `training.example.json` si lleva `$comment` (el esquema lo admite); (2) `design.md` dice `final/` = «solo referencias» sin nombrar fichero: se fija `final/artifacts.json` (lista `{path, hash, kind}`), a confirmar por T-04; (3) `request.json` = `{"request": ...}`; (4) ADR-019 `propuesta` (cruza el umbral: cierra alternativas y afecta a `case_schema.py`, recorder, capacidad `training` y puente a curator). Rojos preexistentes de Windows NO de esta tarea: `tests/test_knowledge_find.py` `test_show_imprime_la_entrada_completa_tal_cual`, `test_show_json_envuelve_el_contenido_con_su_ficha`, `test_ca04_show_adr012_...` (copia de trabajo `w/crlf` de ADR-003/ADR-012/LES con `core.autocrlf=true`; comparan byte a byte con LF).
- **Changelog**: Case store templates ship with the skill: an example store with a failure-then-correction pair, an index sample and a field-by-field guide; the store lives outside Git and `docs/knowledge/`.
**Criterios de aceptación**
- [x] Plantillas de `metadata.json`/`validation.json`/`cases_index.jsonl` documentadas con ejemplos.
- [x] ADR propuesta con la decision de mantener el case store fuera de `docs/knowledge/`.

## Fase 2 - Recorder y puerta humana

### T-04 - Recorder determinista (crear/actualizar caso)
- **Estado**: borrador
- **Tiempo humano**: est. 4h · real -
- **Prevision IA**: 45k in / 18k out tok
- **Dependencias**: T-01, T-02
- **Tipo**: backend
- **Archivos**: `skills/training-data-services/scripts/case-recorder.py`, `skills/training-data-services/scripts/test_case_recorder.py`
- **Verificacion**: `python -m pytest -q skills/training-data-services/scripts/test_case_recorder.py` -> ID estable, nunca sobrescribe version existente, redacta antes de escribir
**Criterios de aceptación**
- [ ] Un `case_id`+version existente nunca se sobrescribe; escribir de nuevo crea una version siguiente.
- [ ] La trayectoria y el contexto pasan por `redact.py` antes de tocar disco.
- [ ] Un caso rechazado se conserva; no hay borrado silencioso.

### T-05 - Puerta de aprobacion humana para Gold
- **Estado**: borrador
- **Tiempo humano**: est. 3h · real -
- **Prevision IA**: 35k in / 14k out tok
- **Dependencias**: T-04
- **Tipo**: backend
- **Archivos**: `skills/training-data-services/scripts/case-recorder.py`, `skills/training-data-services/scripts/test_case_recorder.py`
- **Verificacion**: `python -m pytest -q skills/training-data-services/scripts/test_case_recorder.py -k gold` -> transicion a approved rechazada sin `--approved-by-human`
**Criterios de aceptación**
- [ ] Sin el flag, marcar `approved` falla con mensaje explicito; `needs_changes`/`rejected` no lo requieren.
- [ ] Un caso `corrected` declara `supersedes_case` y se conserva junto al `failure` que corrige.

### T-06 - Indice `cases_index.jsonl` y consulta basica
- **Estado**: borrador
- **Tiempo humano**: est. 1h · real -
- **Prevision IA**: 10k in / 5k out tok
- **Dependencias**: T-04
- **Tipo**: backend
- **Archivos**: `skills/training-data-services/scripts/case-recorder.py`, `skills/training-data-services/scripts/test_case_recorder.py`
- **Verificacion**: `python -m pytest -q skills/training-data-services/scripts/test_case_recorder.py -k index` -> indice append-only coherente con `cases/`
**Criterios de aceptación**
- [ ] El indice se puede reconstruir desde `cases/` si se corrompe (caché, no fuente).

## Fase 3 - Dedup, particion y ensamblador

### T-07 - Deduplicacion por shingles (reutilizando `code-health.py`)
- **Estado**: borrador
- **Tiempo humano**: est. 5h · real -
- **Prevision IA**: 55k in / 22k out tok
- **Dependencias**: T-04
- **Tipo**: backend
- **Archivos**: `skills/training-data-services/scripts/dedup.py`, `skills/training-data-services/scripts/test_dedup.py`
- **Verificacion**: `python -m pytest -q skills/training-data-services/scripts/test_dedup.py` -> near-duplicates detectados sin embeddings, boilerplate fijo no da falsos positivos
**Criterios de aceptación**
- [ ] Dos casos casi identicos entre versiones se marcan como grupo de duplicados.
- [ ] Texto fijo compartido por todos los casos no dispara falsos positivos.

### T-08 - Particion anti-leakage por familia
- **Estado**: borrador
- **Tiempo humano**: est. 4h · real -
- **Prevision IA**: 45k in / 18k out tok
- **Dependencias**: T-07
- **Tipo**: backend
- **Archivos**: `skills/training-data-services/scripts/dataset-assembler.py`, `skills/training-data-services/scripts/test_dataset_assembler.py`
- **Verificacion**: `python -m pytest -q skills/training-data-services/scripts/test_dataset_assembler.py -k leakage` -> ninguna familia queda partida entre train y benchmark
**Criterios de aceptación**
- [ ] Sin al menos una familia reservada como benchmark, el ensamblador se niega a exportar y explica por que.

### T-09 - Ensamblador de dataset y puente a `knowledge-curator`
- **Estado**: borrador
- **Tiempo humano**: est. 5h · real -
- **Prevision IA**: 55k in / 22k out tok
- **Dependencias**: T-05, T-08
- **Tipo**: backend
- **Archivos**: `skills/training-data-services/scripts/dataset-assembler.py`, `skills/training-data-services/scripts/propose-from-case.py`, `skills/training-data-services/scripts/test_dataset_assembler.py`
- **Verificacion**: `python -m pytest -q skills/training-data-services/scripts/test_dataset_assembler.py` -> solo casos approved+humano entran; propuesta a Curator nunca auto-aprueba
**Criterios de aceptación**
- [ ] `train.jsonl`/`benchmark.jsonl` en formato chat (`messages`), manifiesto con hashes por caso.
- [ ] `propose-from-case.py` genera un candidato `pending` para `knowledge-curator`, nunca `approved`.

## Fase 4 - Setup, doctor y cierre

### T-10 - Opt-in en setup y doctor
- **Estado**: borrador
- **Tiempo humano**: est. 4h · real -
- **Prevision IA**: 45k in / 18k out tok
- **Dependencias**: T-09
- **Tipo**: devops
- **Archivos**: `commands/setup.md`, `commands/doctor.md`, `agent-kits/shared/doctor.py`, `agent-kits/shared/test_doctor.py`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `interop/**`
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_doctor.py` -> desactivado/activado, recuento por estado, dataset desactualizado; `python scripts/export-interop.py --check` -> 0
**Criterios de aceptación**
- [ ] Sin `training.json`, `/doctor` no reporta nada de esta capacidad; con el, informa sin bloquear.

### T-11 - Aislamiento, regresion, interop y cierre
- **Estado**: borrador
- **Tiempo humano**: est. 7h · real -
- **Prevision IA**: 65k in / 25k out tok
- **Dependencias**: T-01 a T-10
- **Tipo**: test
- **Archivos**: `tests/test_training_data_services.py`, `tests/test_hooks_shell.py`, `docs/agents/CONTRACTS.md`, `docs/README.md`, `CHANGELOG.md`, `CHANGELOG.es.md`, `interop/**`
- **Verificacion**: `python -m pytest -q tests/test_training_data_services.py tests/test_hooks_shell.py` -> ningun binario inline, ningun caso no-Gold exportado, hooks sin red; `python scripts/lint_plugin.py` -> 0 · `python evals/check.py` -> 0
**Criterios de aceptación**
- [ ] Suite completa en verde; revision de dos lentes sin gaps Critical/Important; QA sin UI verde; retro abre `retro-gate.py`.

## Revisión de dos lentes — intento 1: Fase 1 (T-01, T-02, T-03) — 14 gaps (0 Critical, 2 Important, 12 Minor), lentes A+B+D (D por `review-lens-select.py`: `regex-en-bucle` en `case_schema.py:129`, resultó falso positivo; C no aplica), rango `bab4fb5..ef4841f`

Puertas previas: `scope-check --base origin/master` → 1 fuera (`improvement-plan.md`, cambio de Estado del orquestador en `bab4fb5`: **arbitraje, no-gap**) · `ledger-lint` 0/8 (Changelog ausente en T-04…T-11, aún borrador) · `lint_plugin` 0 · `evals/check` 0 (148 casos) · `export-interop --check` al día · `grep -c training doctor.py` 0. Tres worktrees separados (`tds-lente-a-i1|b-i1|d-i1`); 3 falsos rojos por MAX_PATH de GOT-012 en las copias (verdes en el árbol principal; ver GOT candidato en `needs_changes`). Lente A: criterios de T-01/T-02/T-03 ✓ con evidencia reproducida cifra a cifra (36 · 10/21 · 7 · 79 · 393 passed), RED de T-02 reproducido cargando `capabilities.py@bab4fb5` (9/10 fallan), skill nueva conforme a `plugin-dev` (105 líneas, description 921 chars, eval 2+1), CONVENTIONS ES/EN equivalentes. Lente B: ~40 sondas sobre `validar_caso`/`validar_config`, 11 configs sobre `capabilities`, assets validan (`v001` rechazada conservada + `v002` corrected Gold coherentes); 28 mutantes, 23 muertos, **5 vivos** (M2, M15, M16, M17, M18) + M19 equivalente. Lente D: `validar_caso` ×10 000 = 0,46 s, `redactar_estructura` 5 MB en 0,39 s, capacidad O(1) sin listar el store, carga de `case_schema.py` ≈9 ms por `/doctor`: sin hallazgos. Fusión: B-1 → #1; B-2 + A-1 → #2; B-3 → #3; B-4 + C nota → #4; B-5 → #5; B-6 → #6; B-7 → #7; B-8 + A «fuera de lente» (import al cargar) → #8; A-2 → #9; A-3 → #10; A-4 → #11; A-5 → #12; A-6 → #13; mutantes vivos → #14.

| # | Grado | Gap | Tarea | Corrección | Evidencia | Lente |
|---|---|---|---|---|---|---|
| 1 | **Important** | `validar_caso` lanza `TypeError: unhashable type` con un `outcome` no hashable (`case_schema.py:350` `outcome in tabla`, ídem `:186` en `mapear_outcome`): `"outcome": ["success"]` → traceback por CLI con **exit 1**, el mismo código que «errores de validación»; el recorder de T-04 heredaría el crash. **Arbitraje:** todo valor de tipo inesperado devuelve `{campo, mensaje}` (comprobar `isinstance(str)` antes de mirar vocabularios); exit 2 reservado a uso/entrada ilegible, 1 a validación; tests con `list`/`dict`/`None` en `outcome`, `status`, `case_id` | T-01 | pendiente | B |
| 2 | **Important** | La regla «`root` nunca dentro de `docs/knowledge/`» (ADR-019 Decisión 2, fila de CONVENTIONS) solo cubre rutas relativas en minúsculas: `case_schema.py:114` exige `not os.path.isabs(root) and …`; `validar_config` no recibe la raíz del proyecto aunque `cargar_config(root)` la tiene. `"root": "C:/proj/docs/knowledge/cases"` → `[]` y capacidad `ok`; `"Docs/Knowledge/x"` → `[]` (en Windows/macOS es el mismo directorio). Mutante M19 (quitar `isabs`) sobrevive: no hay test del absoluto. **Arbitraje:** resolver `root` contra la raíz del proyecto (`realpath`/`normcase`) y rechazar si cae dentro de `<proyecto>/docs/knowledge/` sea relativo, absoluto o con otra capitalización; `validar_config(cfg, raiz_proyecto)`; tests con los tres casos | T-01/T-03 | pendiente | B + A |
| 3 | Minor | Una regex que compila pero revienta (`OverflowError`, p. ej. `family_pattern: "a{4294967296}"`) no la captura `except re.error` (`case_schema.py:131-136`): CLI con traceback; en `capabilities` degrada sin el campo. **Arbitraje:** capturar `(re.error, OverflowError, RecursionError)` y devolver el campo | T-01 | pendiente | B |
| 4 | Minor | Las anclas `$` aceptan `\n` final y los patrones del proyecto se evalúan con `re.match` (parcial) (`case_schema.py:69,70,300,354`): `family: "ramp\n"`, `id_prefix: "geo\n"`, `supersedes_case: "…@v1\n"` → `[]` (nombre de directorio inválido en Windows al grabar); con `family_pattern: "[a-z]"` sin anclas, `family: "r/../../x"` → `[]` y `directorio_version` devuelve `cases\r/../../x.steep\v001` (traversal, CWE-22). **Arbitraje:** `\Z` en vez de `$`, `re.fullmatch` para los patrones del proyecto, y rechazo explícito de separadores de ruta/`..`/controles en `family`/`variant`/`id_prefix`; tests | T-01 | pendiente | B |
| 5 | Minor | `supersedes_case` no se comprueba contra el propio caso ni contra el `case_id` (`case_schema.py:353-358`): un v1 `corrected` que se reemplaza a sí mismo, o que apunta a otro `case_id`, o `outcome: success` con `supersedes_case` → `[]`; el par fallo → corrección (CA-12 de design) queda sin garantizar. **Arbitraje:** `supersedes_case` obligatorio solo con `corrected`, mismo `case_id`, versión estrictamente menor; tests | T-01 | pendiente | B |
| 6 | Minor | El filtro anti chain-of-thought (`case_schema.py:196-198`) solo mira claves exactas, en minúscula y en el primer nivel del turno: `Thinking`, `reasoning_details`, `tool_calls[].arguments.reasoning` pasan. **Arbitraje:** comparación case-insensitive por prefijo (`thinking`, `reasoning`, `chain_of_thought`, `scratchpad`) y recursiva dentro del turno; tests | T-01 | pendiente | B |
| 7 | Minor | `root` con `~` ni se expande ni se rechaza (`capabilities.py:251-253`): `"~/store"` → `declarado` con la ruta literal `<proyecto>\~\store`. **Arbitraje:** rechazar `~` en el validador (el `root` es relativo al proyecto o absoluto explícito) y test | T-02 | pendiente | B |
| 8 | Minor | `redactar_estructura` (`case-recorder.py:63-69`) no redacta elementos de tuplas/sets ni claves de dict (latente hasta T-04); y `case-recorder.py:57` carga `redact.py` al importar el módulo, así que sin él falla cualquier import, no solo grabar. **Arbitraje:** recorrer tuplas/sets/claves; carga perezosa de `redact` en la función de grabar con `RedaccionNoDisponible` al grabar; tests | T-02 | pendiente | B + A |
| 9 | Minor | Registrar `training` en `REGISTRO` hace que `/doctor` pinte «training · desactivado» en todo proyecto sin `training.json` (`capabilities.py:303`, `doctor.py:1603-1604`), en contra del criterio de T-10 («sin `training.json`, `/doctor` no reporta nada») y del «cero impacto» de CA-01; `doctor.py` no puede filtrar sin código específico (prohibido). **Arbitraje del orquestador:** regla GENÉRICA en el contrato de capacidades: una capacidad opt-in cuyo `config_path` no existe se omite del bloque de `/doctor` salvo `--verbose`/`--all` (aplica a `kwipu`/`graphiti`/`training` por igual); documentar en CONVENTIONS y `commands/doctor.md`; test genérico en `test_doctor.py` sin nombrar capacidades; se hace en esta ronda para no arrastrarlo a T-10 | T-02 (→ T-10) | pendiente | A |
| 10 | Minor | Aristas nuevas sin fila en `docs/agents/CONTRACTS.md` («una arista nueva se declara el día que se crea», `:12,17`): kit → skill (`capabilities.py:216` → `skills/training-data-services/scripts/case_schema.py`) y skill → shared (`case-recorder.py` → `agent-kits/shared/redact.py`); la nota del ledger las difería a T-11 y omitía la segunda. **Arbitraje:** declararlas ahora con su Puerta (tests existentes) | T-02 | pendiente | A |
| 11 | Minor | ADR-019 no reconcilia su decisión con ADR-018 punto 1 («cualquier dataset es una proyección reconstruible desde el Markdown en git»): el case store es una segunda fuente fuera de git y ADR-019 solo dice «fuente de verdad **curada**» (`ADR-019:55` vs `ADR-018:24-26`). **Arbitraje:** párrafo explícito en ADR-019 («ADR-018 habla del conocimiento curado; el case store es evidencia bruta no curada, deliberadamente fuera de git y de `docs/knowledge/`») y enlace cruzado | T-03 | pendiente | A |
| 12 | Minor | La lista «Shared skills» de `README.md:241` / `README.es.md:241` no incluye la skill nueva y ninguna tarea lo prevé. **Arbitraje:** añadirla en ambos README raíz | T-01 | pendiente | A |
| 13 | Minor | Celda de tokens del Resumen dice `medido` sin cifra aunque los tres marcadores la dan (37.8k + 17.3k + 14.4k out). **Arbitraje:** orquestador al cerrar fix1 | Resumen | pendiente (orquestador, al cerrar fix1) | A |
| 14 | Minor | Mutantes vivos (agujeros de test): M2 (`version: true` aceptado al quitar `_es_int`, `:99`), M15 (`version_width <= 60`, `:139`), M16 (`tool_calls` fuera de `assistant`, `:206`), M17 (`refs[].kind` no texto, `:246`), M18 (claves desconocidas dentro de `ids`, `:127`). **Arbitraje:** un test por mutante | T-01 | pendiente | B |

**Decisión del orquestador (2026-09-23):** 2 Important ⇒ T-01/T-02/T-03 vuelven a `en-progreso`; ronda `fix1` (implementer `opus`, marcador `training-data-services/T-01-fix1`) sobre #1-#12 y #14 (#13 del orquestador) y **revisión intento 2 de 3**. Regla de higiene para lentes e implementer: worktrees con nombre único (`tds-lente-<x>-i<N>`), scripts en `_tools/` propios y borrado al cerrar; MAX_PATH: candidata a gotcha ya en `needs_changes`.
