---
generacion: {fuente: estimado, tokens_reales: {entrada: 0, salida: 0, cache_creacion: 0, cache_lectura: 0}, eur: null, horas_ia: 0.0, duracion: 0m, ratio_usado: 0}
verificacion: obligatoria
---

# Checklist de Tareas - Captura durable de SessionEnd

| **Estado** | en-progreso |
|---|---|
| **Plan** | [improvement-plan.md](improvement-plan.md) |
| **Diseño** | [design.md](design.md), O1 |

> **Ledger canónico de progreso.** Esta es la fuente única de avance; los servicios externos son espejo.

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervision (real/est) | Tokens (real/est) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fase 1 - Módulos compartidos | 1 | 2 | 50% | 0.55 / 2.5h | 0.42 / 0.8h | 0 / 0.2h | 0 / 45k |
| Fase 2 - Captura y materialización | 0 | 2 | 0% | 2.1 / 5.5h | 1.8 / 1.6h | 0 / 0.4h | 0 / 85k |
| Fase 3 - Reconciliación y diagnóstico | 0 | 2 | 0% | 0 / 4h | 0 / 1.2h | 0 / 0.3h | 0 / 60k |
| Fase 4 - Pruebas, medición y cierre | 0 | 2 | 0% | 0 / 2h | 0 / 0.6h | 0 / 0.2h | 0 / 40k |
| **TOTAL** | **1** | **8** | **13%** | **2.65 / 14h** | **2.22 / 4.2h** | **0 / 1.1h** | **0 / 230k** |

## Fase 1 - Módulos compartidos

### T-01 - `outbox.py`: cola atómica con claim, done y dead-letter
- **Estado**: en-progreso
- **Tiempo humano**: est. 1.5h · real 0.2h (estimado) + fix1 0.15h (estimado)
- **Prevision IA**: 20k in / 8k out tok · real (estimado): usage-meter degradó a `fuente: estimado` (sin transcripciones en este entorno); horas_ia real (estimado): 0.15h + fix1 (estimado, `usage-meter` degradó otra vez): 0.12h
- **Dependencias**: ninguna
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/outbox.py`, `agent-kits/shared/test_outbox.py`, `agent-kits/shared/README.md`, `agent-kits/shared/copias.json` (bloque `hook_cmd_con_args`, compartido con T-03/gap 11), `tests/test_console_encoding.py` (añadido en la puerta scope-check del intento 1: los scripts nuevos sin `__main__` necesitan su entrada en `MODOS`/`SIN_SIMBOLOS_EN_LA_SALIDA`)
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_outbox.py` -> escribir idempotente por clave, claim exclusivo con dos procesos, dead-letter con causa, corte antes/después del rename sin parcial, huérfanos de `processing/` reencolados/dead-letter, clave inválida rechazada, retención de `done/`, permisos 0700/0600 · **ejecutado (fix1)**: `21 passed in 0.12s`
- **RED**: `test_escribir_es_idempotente_por_clave` (y el resto del módulo) falló con `FileNotFoundError: [Errno 2] No such file or directory: '.../agent-kits/shared/outbox.py'` · 2026-09-17
- **RED (fix1)**: `test_reclamar_reencola_processing_huerfano_por_ttl`, `test_reclamar_huerfano_agota_intentos_y_va_a_dead_letter`, `test_escribir_valida_clave_y_rechaza_escape`, `test_escribir_no_deja_tmp_a_medias_tras_fallo_a_mitad`, `test_limpiar_tmp_huerfanos_borra_planted_y_respeta_ttl`, `test_purgar_antiguos_borra_done_pero_no_dead_letter`, `test_directorios_y_ficheros_de_la_cola_son_privados`, `test_dead_letter_no_fuga_el_handle_de_causa_json` fallaron contra el `outbox.py` de T-01 (sin re-encolado de huérfanos, sin validación de `clave`, sin `purgar_antiguos`/`limpiar_tmp_huerfanos`, directorios/ficheros con permisos por defecto) · 2026-09-17
**Criterios de aceptación**
- [x] Solo stdlib; sin red; contrato `escribir/reclamar/completar/dead_letter/reencolar_o_dead_letter/estado/purgar_antiguos/limpiar_tmp_huerfanos/purgar` documentado en el docstring.
- [x] Dos `reclamar` concurrentes sobre el mismo item: uno gana, el otro recibe `None`.
- [x] (fix1) `reclamar` re-encola/dead-letter los huérfanos de `processing/` (gap 1); `escribir` valida `clave` (gap 23); directorios 0700 y ficheros 0600 (gap 9); `_escribir_atomico` no deja `.tmp-*` a medias ni sin limpiar (gap 3/21); `purgar_antiguos` acota `done/` sin tocar `dead-letter/` (gap 22); `dead_letter` cierra el handle de `causa.json` (gap 23).
- **Changelog**: Nueva cola atómica compartida `agent-kits/shared/outbox.py` (escribir/reclamar/completar/dead_letter/estado/purgar) para la captura durable de `SessionEnd` y futuros exportadores de memoria. **Corrección de revisión (T-fix1):** re-encolado de huérfanos en `processing/` con dead-letter al agotar intentos, validación de `clave`, permisos 0700/0600, retención de `done/`, limpieza de temporales huérfanos y cierre del handle de `causa.json`.

### T-02 - `redact.py` extraído de `journal.py` (una sola fuente)
- **Estado**: completado
- **Tiempo humano**: est. 1h · real 0.2h (estimado)
- **Prevision IA**: 12k in / 5k out tok · real (estimado): usage-meter degradó a `fuente: estimado` (sin transcripciones en este entorno); horas_ia real (estimado): 0.15h
- **Dependencias**: ninguna
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/redact.py`, `agent-kits/shared/test_redact.py`, `agent-kits/shared/journal.py`, `agent-kits/shared/test_journal.py`, `agent-kits/shared/copias.json`, `agent-kits/shared/README.md`, `scripts/lint_plugin.py`
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_redact.py agent-kits/shared/test_journal.py` -> mismos casos de redacción que hoy; `journal.py` importa `redactar` con fallback a copia declarada si viaja suelto · **ejecutado**: `50 passed in 4.29s`
- **RED**: `test_redacta_api_key_con_prefijo_conocido` (y el resto del módulo) falló con `FileNotFoundError: [Errno 2] No such file or directory: '.../agent-kits/shared/redact.py'` · 2026-09-17
**Criterios de aceptación**
- [x] Ningún caso de `test_journal.py` cambia de resultado.
- [x] Si `journal.py` necesita copia local para el paquete portable, está en `copias.json` y el test de identidad la cubre (ADR-016).
- **Nota (desviación menor)**: se actualizó también `scripts/lint_plugin.py` (quitar `outbox.py`/`redact.py` de `PIEZAS_PLANIFICADAS`, ahora que existen en el árbol); no estaba en el plan pero era necesario para que el linter no avise de una tolerancia caducada — fuera del alcance de T-01/T-02 en sentido estricto, añadido a `Archivos` de ambas.
- **Changelog**: `redact.py` extrae `redactar`/`REDACTADO`/`_SECRETOS_RE` de `journal.py` a un módulo compartido único (fuente única, CA-11), con respaldo local declarado en `copias.json` para el paquete portable.

## Fase 2 - Captura y materialización

### T-03 - `journal.py capture-end` + exec form en `hooks.json`
- **Estado**: en-progreso
- **Tiempo humano**: est. 2.5h · real 0.6h (estimado) + fix1 0.35h (estimado)
- **Prevision IA**: 30k in / 12k out tok · real (estimado): usage-meter degradó a `fuente: estimado` (sin transcripciones en este entorno); horas_ia real (estimado): 0.5h + fix1 (estimado, `usage-meter` degradó otra vez): 0.3h
- **Dependencias**: T-01
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/journal.py`, `agent-kits/shared/test_journal.py`, `hooks/session-journal.sh`, `hooks/hooks.json`, `tests/test_hooks_shell.py`, `tests/test_hooks_config.py`, `.gitignore`, `scripts/lint_plugin.py`, `scripts/export-interop.py`, `tests/test_export_interop.py`, `agent-kits/shared/doctor.py`, `agent-kits/shared/test_doctor.py`, `agent-kits/shared/copias.json`, `skills/plugin-dev/references/claude-code-contracts.md`, `interop/codex/hooks.json`, `interop/opencode/**`
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_journal.py tests/test_hooks_shell.py tests/test_hooks_config.py` -> envelope válido en `outbox/`, ni `git` ni `claude` invocados (dobles en PATH), `hooks.json` con `command: bash` + `args` y `timeout: 5`, ruta con espacios y Unicode · **ejecutado (fix1)**: `agent-kits/shared/test_journal.py` 70 passed, `tests/test_hooks_shell.py` 50 passed, `tests/test_hooks_config.py` 3 passed (comando conjunto: `120 passed in 14.97s`)
- **RED**: `test_capture_end_escribe_envelope_valido_y_no_stdout` (y el resto de `capture_end`/CLI en `test_journal.py`, más `test_session_journal_no_invoca_git_ni_claude`/`test_session_journal_ruta_del_plugin_con_espacios_y_unicode`/`test_session_journal_repo_ajeno_sin_rastro_del_plugin_no_siembra_nada`/`test_session_journal_deja_envelope_en_outbox_y_replay_materializa_la_entrada` en `test_hooks_shell.py`, y `test_session_end_usa_exec_form_con_timeout_5`/`test_lint_plugin_da_error_si_el_script_de_args_no_existe` en `test_hooks_config.py`) fallaron contra el `journal.py`/`session-journal.sh`/`hooks.json`/`lint_plugin.py` previos a esta tarea (`AttributeError: module 'journal' has no attribute 'capture_end'`; outbox vacía; `'bash "${CLAUDE_PLUGIN_ROOT}/hooks/session-journal.sh"' != 'bash'`) · 2026-09-17
- **RED (fix1)**: `test_capture_end_session_id_gigante_no_rompe_el_tope_de_64kib`, `test_capture_end_incluye_hook_event_name`, `test_capture_end_dos_cierres_de_resume_generan_dos_envelopes`, `test_asegurar_gitignore_local_evita_que_la_cola_se_cuele_en_git`, `test_journal_activo_objeto_con_activo_false_es_opt_out`, `test_journal_queue_dir_rechaza_absoluto_y_dotdot` (`agent-kits/shared/test_journal.py`), `test_hook_exec_form_con_script_inexistente_en_args_es_error` (`agent-kits/shared/test_doctor.py`), `test_codex_session_end_va_en_shell_form_no_exec_form` (`tests/test_export_interop.py`) fallaron contra el código de T-03 (`session_id` sin tope, sin `hook_event_name`, `sequence` fijo a 0, sin `.gitignore` local de la cola, `_journal_activo` ciego al objeto `{"activo": false}`, `journal.dir` sin contención, `doctor.py`/`export-interop.py` ciegos al exec form) · 2026-09-17
**Criterios de aceptación**
- [x] Envelope ≤ 64 KiB con `schema_version`, `event_id` determinista y sin texto de conversación (fix1: `session_id` acotado a `SESSION_ID_MAX`, no solo `cwd`/`transcript_path`).
- [x] Opt-out `sesion.journal: false` sigue funcionando; el objeto `sesion.journal.{dir,...}` se acepta (fix1: incluido `{"activo": false}` dentro del objeto, y `dir` absoluto/`..` se rechaza con aviso).
- [x] `git` y `claude` falsos en `PATH` no se ejecutan durante la captura (CA-01).
- **Nota (desviación)**: `scripts/lint_plugin.py` (`lint_hooks`) solo escaneaba `command` en busca de rutas `${CLAUDE_PLUGIN_ROOT}/…`; con `command: bash` + `args` (exec form) el path vive en `args`, así que el linter no habría detectado un script inexistente ahí. Se amplió `lint_hooks` para escanear también `args` (dos tests nuevos en `test_hooks_config.py` prueban el antes/después). `interop/codex/hooks.json` se regeneró con `export-interop.py` para reflejar el exec form.
- **Nota (fix1)**: `doctor.py` tenía el MISMO hueco que `lint_plugin.py` antes de esta tarea (solo miraba `command`); se corrigió con el bloque compartido `hook_cmd_con_args` declarado en `copias.json` (ADR-016), no duplicado a mano dos veces. `export-interop.py --check` re-ejecutado tras regenerar: `48 ficheros al día` (evidencia pegada, gap 18).
- **Changelog**: `SessionEnd` pasa a captura ULTRALIGERA (`journal.py capture-end`, exec form en `hooks.json`, `timeout: 5`): un envelope atómico en la outbox local, sin git, sin IA y sin red (CA-01). **Corrección de revisión (T-fix1):** tope de `session_id`, `hook_event_name` en el envelope, `sequence` por líneas del log de prompts (distingue dos cierres de una misma sesión), `.gitignore` propio de la cola, opt-out por objeto, contención de `journal.dir`, `/doctor` y Codex ya no ciegos al exec form (Codex pasa a shell form, gap 16).

### T-04 - `journal.py replay`: claim, materialización, verificación, dead-letter
- **Estado**: en-progreso
- **Tiempo humano**: est. 3h · real 0.7h (estimado) + fix1 0.45h (estimado)
- **Prevision IA**: 35k in / 14k out tok · real (estimado): usage-meter degradó a `fuente: estimado` (sin transcripciones en este entorno); horas_ia real (estimado): 0.6h + fix1 (estimado, `usage-meter` degradó otra vez): 0.4h
- **Dependencias**: T-01, T-02, T-03
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/journal.py`, `agent-kits/shared/test_journal.py`, `docs/roadmap/2026-09-17-session-end-durable-capture/design.md` (fix1: nota del gap 8, `derivados_en: replay`)
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_journal.py -k replay` -> mismo evento ×5 = una entrada; envelope venenoso a `dead-letter/` y el resto continúa; transcript ausente usa el log de prompts o declara carencia; `cierre:` en el frontmatter · **ejecutado (fix1, re-ejecutado tras el gap 5)**: `11 passed in 0.74s` (el ledger del intento 1 decía «12 passed»; la cifra real, con el mismo comando, es 11 —confirmado también por el revisor con 7 antes de esta corrección, sobre el código de entonces—; el número correcto depende de cuántos tests de `replay`/`cmd_replay` existan en cada momento, así que se documenta el comando exacto en vez de fiarse de una cifra fija)
- **RED**: `test_replay_materializa_reutilizando_escribir_sesion` (y el resto de `replay`/`cmd_replay`) falló con `AttributeError: module 'journal' has no attribute 'capture_end'`/`replay` sobre el `journal.py` previo a T-03/T-04 · 2026-09-17
- **RED (fix1)**: `test_replay_dos_procesos_concurrentes_no_pierden_entradas`, `test_replay_usa_captured_at_como_fecha_y_marca_derivados_en_replay`, `test_replay_bajo_presupuesto_ajustado_no_llama_a_la_ia`, `test_replay_transcript_ajeno_o_relativo_se_ignora`, `test_schema_aceptados_admite_n_y_n_menos_1`, `test_draft_sin_turnos_ni_transcript_declara_la_carencia` fallaron contra el `replay()` de T-04 (sin `try/except` por item, sin cerrojo entre `replay` concurrentes, `draft` ignoraba `captured_at`, `transcript_path` sin validar, `SCHEMA_ACEPTADOS` sin la rama N-1 ejercitada, sin aviso de carencia) · 2026-09-17
**Criterios de aceptación**
- [x] Reutiliza `escribir_sesion` (git, prompts, IA opt-in) sin duplicar lógica.
- [x] Acepta `schema_version` N y N-1 (fix1: `_schema_aceptados` extraída a función pura y probada también con N=2, no solo con el N=1 vigente).
- [x] Nunca inventa contenido (CA-05; fix1: la rama «sin log ni transcript» ahora declara la carencia en `avisos`, no solo el genérico «Sesión sobre X»).
- [x] (fix1) Un item reclamado que no llega a completar/dead-letter no queda huérfano para siempre (gap 1, resuelto en `outbox.reclamar`); cada item corre en su propio `try/except` y `cmd_replay` siempre imprime JSON (gap 2); dos `replay` concurrentes no se pisan (`<dir>/.replay.lock`, gap 7); la entrada usa la fecha del cierre, no la de hoy (`captured_at`, gap 8); `transcript_path` se valida antes de abrirse (gap 15); `--budget-ms`/`--ia` acotan también la IA y el timeout de git bajo presupuesto (gap 14).
- **Nota (desviación menor)**: `docs/knowledge/journal/README.md` no se toca a mano — lo sigue regenerando `journal.py index` (invocado por `write`) como siempre; no hacía falta cambiarlo aparte, así que se retira del campo `Archivos` original.
- **Nota (desviación de proceso)**: T-03 y T-04 se implementaron y commitean JUNTOS (un solo commit `T-03/T-04: …`) en vez de uno por tarea: `capture_end`/`replay` se escribieron en la misma sesión de edición sobre `journal.py` y separar el diff a mano por hunks arriesgaba dejar un commit intermedio no coherente (T-04 depende de T-03 y ambos tocan el mismo fichero en las mismas franjas). El commit de T-04 también incluye el arreglo de `tests/test_console_encoding.py` para `outbox.py`/`redact.py` (MODOS + `SIN_SIMBOLOS_EN_LA_SALIDA`): un hueco de T-01/T-02 que no se detectó entonces porque solo se corrió la suite dirigida, no `python3 -m pytest -q` completo — se corrige aquí, al primer punto en que se ejecutó la suite entera.
- **Nota (simplificación documentada, corregida en fix1)**: la nota original decía que `sequence` quedaba fijo a 0 (MVP); la corrección del gap 6 lo sustituye por «líneas del log de prompts en el momento del cierre» — ver T-03 fix1. Esta nota se conserva para el historial de la decisión.
- **Changelog**: `journal.py replay` materializa la outbox reutilizando `escribir_sesion` (git, prompts, IA opt-in): claim exclusivo, verificación, `done/`/`dead-letter/` con causa, `cierre: materializado` en el frontmatter. **Corrección de revisión (T-fix1):** reintentos con dead-letter tras agotarlos, `try/except` por item sin abortar el drenaje, cerrojo de proceso entre `replay` concurrentes, fecha del cierre + `derivados_en: replay`, validación de `transcript_path`, `--ia auto|no` y timeout de git acotado bajo presupuesto, retención de `done/` y limpieza de temporales huérfanos.

## Fase 3 - Reconciliación y diagnóstico

### T-05 - Reconciliación presupuestada en `SessionStart` y huérfanas
- **Estado**: borrador
- **Tiempo humano**: est. 2h · real -
- **Prevision IA**: 25k in / 10k out tok
- **Dependencias**: T-04
- **Tipo**: backend
- **Archivos**: `hooks/session-context.sh`, `agent-kits/shared/journal.py`, `agent-kits/shared/test_journal.py`, `tests/test_hooks_shell.py`
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_journal.py -k "huerfana or budget" tests/test_hooks_shell.py -k session_context` -> 0/10/100 pendientes dentro del presupuesto; log de prompts sin envelope > ventana = `recuperado_sin_cierre`; sesión viva no se toca
**Criterios de aceptación**
- [ ] `--budget-ms` y `--max` leídos de `dev.json` con defaults 300/3.
- [ ] Solo entradas materializadas se inyectan en el contexto (CA-08).

### T-06 - `journal.py status` y sección «Journal» de `/doctor`
- **Estado**: borrador
- **Tiempo humano**: est. 2h · real -
- **Prevision IA**: 22k in / 9k out tok
- **Dependencias**: T-04
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/journal.py`, `agent-kits/shared/doctor.py`, `agent-kits/shared/test_doctor.py`, `commands/doctor.md`
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_doctor.py -k journal` -> estados sano / pendientes / huérfana / dead-letter con veredicto y remedio nombrado; triage del `Hook cancelled`
**Criterios de aceptación**
- [ ] `/doctor` lee `journal.py status --json`, no reimplementa la cola.
- [ ] Distingue «aviso del runtime con entrada escrita» de «pérdida» (CA-10).
- [ ] `purge --confirm` es el único borrado; uninstall no toca `.claude/journal/` (CA-12).

## Fase 4 - Pruebas, medición y cierre

### T-07 - Bench de captura y matriz de garantías
- **Estado**: borrador
- **Tiempo humano**: est. 1h · real -
- **Prevision IA**: 12k in / 5k out tok
- **Dependencias**: T-03, T-05
- **Tipo**: test
- **Archivos**: `scripts/bench-session-end.py`, `tests/test_bench_session_end.py`, `docs/observability.md`, `docs/en/observability.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `ci.yml.MANUAL-COPY`
- **Verificacion**: `python scripts/bench-session-end.py --iterations 30 --assert-p95-ms 100 --assert-p99-ms 300` -> exit 0; tabla de garantías por forma de salida en observability ES/EN
**Criterios de aceptación**
- [ ] p95 ≤ 100 ms / p99 ≤ 300 ms en CI de referencia (CA-02).
- [ ] La matriz documenta explícitamente lo que NO se garantiza (SIGKILL antes del hook).

### T-08 - GOT-011, changelog, interop y puertas
- **Estado**: borrador
- **Tiempo humano**: est. 1h · real -
- **Prevision IA**: 10k in / 4k out tok
- **Dependencias**: T-06, T-07
- **Tipo**: docs
- **Archivos**: `docs/knowledge/gotchas/GOT-011-hook-cancelled-en-session-end.md`, `docs/knowledge/README.md`, `CHANGELOG.md`, `CHANGELOG.es.md`, `interop/**`, `docs/roadmap/2026-09-17-session-end-durable-capture/tasks.md`
- **Verificacion**: `python scripts/lint_plugin.py` -> 0 · `python scripts/export-interop.py --check` -> 0 · `python -m pytest -q tests/test_knowledge_index.py` -> índice biyectivo
**Criterios de aceptación**
- [ ] GOT-011 recoge causa (trabajo en el teardown), diagnóstico y remedio.
- [ ] Ledger con evidencia; revisión de dos lentes sin gaps Critical/Important; retro abre `retro-gate.py`.

## Revisión de dos lentes — intento 1: 2 Critical + 12 Important + 10 Minor → 22 corregidos + 2 reasignados (lentes A+B+C; `T-fix1` cerrado)

Lentes: **A+B+C** (`review-lens-select.py`: C por `private-key` en `journal.py:188`/`redact.py:28` y stem `session` en `hooks/session-journal.sh`; D no aplica). Puerta `scope-check`: exit 0 tras declarar `tests/test_console_encoding.py` en T-01. Cada gap viene con reproducción del revisor; ninguno rebatido (todos se verificaron contra el código y eran reales). T-01/T-03/T-04 vuelven a `completado`; corrección medida con clave `session-end-durable-capture/T-0X-fix1`. Gap 13 se reasigna a T-05 (tramo 2, ya lo decía la revisión) y gap 20 a T-07 (FLOWS.md); ninguno de los dos se implementa en este ciclo.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Critical | Un envelope reclamado que no llega a `completar`/`dead_letter` (corte, excepción) queda en `processing/` para siempre: `reclamar` solo lista `outbox/`, nada re-encola, y `capture-end` lo da por idempotente porque `_localizar` lo ve en `processing/`. `replay` informa `restantes: 0` (éxito falso) (B1) | T-01/T-04 | `outbox.reclamar` barre `processing/` primero (`_reclamar_huerfanos`): items con más de `PROCESSING_TTL_S` (600s, parametrizable) se re-encolan a `outbox/` con contador de intentos, o van a `dead-letter/` con causa «reintentos agotados» tras `MAX_INTENTOS` (3) | `agent-kits/shared/outbox.py::_reclamar_huerfanos/reencolar_o_dead_letter`; `test_reclamar_reencola_processing_huerfano_por_ttl`, `test_reclamar_huerfano_agota_intentos_y_va_a_dead_letter` |
| 2 | Critical | Cualquier excepción materializando (disco lleno, permisos, `os.replace` con handle abierto en Windows) aborta el drenaje entero sin `try/except` por item; el item queda en `processing/`, el resto no se procesa, `cmd_replay` no imprime JSON y `main` devuelve 0 (B2) | T-04 | `replay()` envuelve cada item en `try/except`: `OSError` (transitorio) reencola o dead-letter vía `outbox.reencolar_o_dead_letter`, cualquier otra excepción va a dead-letter directo y el bucle sigue; `cmd_replay` envuelve `replay()` y SIEMPRE imprime JSON (con `errores` si algo se escapó) | `agent-kits/shared/journal.py::replay/cmd_replay`; `test_replay_dos_procesos_concurrentes_no_pierden_entradas` (indirecto), resumen ahora trae `reintentados`/`errores` verificado en todos los tests de `replay` |
| 3 | Important | La `Verificación` de T-01 da por ejecutado «corte antes/después del rename sin parcial» y ese test no existe; CA-04 sin cobertura; los `.tmp-<pid>` huérfanos no los limpia nadie (A1, B14) | T-01 | `_escribir_atomico` usa `tempfile.mkstemp` (nombre único, 0600) y limpia el tmp si `os.replace` falla; `outbox.limpiar_tmp_huerfanos` borra temporales con más de la TTL en `outbox/`/`processing/`, invocado por `replay` | `test_escribir_no_deja_tmp_a_medias_tras_fallo_a_mitad`, `test_limpiar_tmp_huerfanos_borra_planted_y_respeta_ttl` |
| 4 | Important | «Envelope ≤ 64 KiB» marcado pero no impuesto: `session_id` sin tope (200.000 chars → 196 KiB); el test no tiene dientes (A2, B12) | T-03 | `SESSION_ID_MAX = 200`; `capture_end` trunca `sid` antes de construir el envelope | `journal.py::capture_end` (`sid = sid[:SESSION_ID_MAX]`); `test_capture_end_session_id_gigante_no_rompe_el_tope_de_64kib` (con dientes: afirma que el `session_id` crudo SÍ superaría 64 KiB) |
| 5 | Important | Evidencia de `Verificación` de T-04 no reproducible: el ledger pega «12 passed», el comando da 7 (A3) | T-04 | Verificación re-ejecutada con el comando exacto tras el fix1 | `python -m pytest -q agent-kits/shared/test_journal.py -k replay` → `11 passed in 0.74s` (cifra pegada en T-04; el comando manda, no un número fijo) |
| 6 | Important | `sequence = 0` colapsa dos cierres legítimos de la misma sesión (`/resume` + nuevo turno + cierre): el segundo tramo nunca se journalea; regresión frente al hook anterior y el test que lo cubría se debilitó (A4, C-b) | T-03/T-04 | `sequence` = nº de líneas de `.claude/session-prompts-<sid>.log` en el momento del cierre (`_contar_lineas_log`); un turno nuevo entre dos cierres produce un `event_id` distinto, y `write()` actualiza la MISMA entrada por `session_id` | `journal.py::_contar_lineas_log/capture_end`; `test_capture_end_dos_cierres_de_resume_generan_dos_envelopes` |
| 7 | Important | Dos `replay` concurrentes pierden entradas: `write()` sin cerrojo elige el mismo nombre de fichero para dos sesiones y una pisa a la otra; spec C-02 exige `_cerrojo` (B3) | T-04 | `replay()` toma `_cerrojo(<dir>/.replay.lock)` alrededor de todo el drenaje: dos `replay` del mismo proyecto ya no corren `write()` en paralelo | `journal.py::replay` (bloque `with _cerrojo(...)`); `test_replay_dos_procesos_concurrentes_no_pierden_entradas` (4 hilos × 12 envelopes → 12 entradas) |
| 8 | Important | La entrada se materializa con datos del momento del replay (`fecha = hoy()`, iniciativa activa, ficheros tocados) en vez del cierre: `captured_at` no se usa (B4) | T-04 | `draft`/`escribir_sesion` aceptan `captured_at`; la fecha del frontmatter/nombre de fichero es la del cierre; los campos derivados de git se marcan `derivados_en: replay` (limitación aceptada por diseño, documentada en `design.md`) | `journal.py::draft/escribir_sesion/render`; `design.md` (nota bajo «Estados»); `test_replay_usa_captured_at_como_fecha_y_marca_derivados_en_replay` |
| 9 | Important | La cola se escribe world-readable (0644) y sin sembrar `.gitignore` en el proyecto consumidor: los envelopes salen en `git status`, se cuelan en `ficheros_tocados` y se pueden commitear (B5, C1 · CWE-538/732) | T-01/T-03 | Directorios de la cola 0700 (`_mkdir_privado`), ficheros 0600 (`tempfile.mkstemp` por defecto, preservado por `os.replace`); `capture_end` siembra un `.gitignore` propio DENTRO de la carpeta de la cola (`_asegurar_gitignore_local`, funciona aunque `journal.dir` se mueva) | `outbox.py::_mkdir_privado`; `journal.py::_asegurar_gitignore_local`; `test_directorios_y_ficheros_de_la_cola_son_privados`, `test_asegurar_gitignore_local_evita_que_la_cola_se_cuele_en_git` |
| 10 | Important | Regresión en la raíz: el hook perdió el fallback al `cwd` del payload (`CLAUDE_PROJECT_DIR > $PWD`) y siempre pasa `--root`, dejando muerta la cascada de `cmd_capture_end`; asimétrico con `user-prompt-capture.sh` → turnos capturados que ningún envelope materializa (A9, B6) | T-03 | `session-journal.sh` solo pasa `--root` si `CLAUDE_PROJECT_DIR` está definido; sin ella, `cmd_capture_end` cae en la cascada `--root > CLAUDE_PROJECT_DIR > cwd del payload > .` (ya existente en `journal.py`, ahora alcanzable) | `hooks/session-journal.sh` (`ROOT_ARGS`); simétrico con `user-prompt-capture.sh` — la suite de hooks (`tests/test_hooks_shell.py`, 50 passed) sigue en verde con `CLAUDE_PROJECT_DIR` definido, que es el caso que cubren sus fixtures; sin la variable, `cmd_capture_end` ya tenía cobertura directa en `agent-kits/shared/test_journal.py` (cascada `--root`) |
| 11 | Important | `/doctor` ciego al exec form: `doctor.py` duplica el escaneo de hooks mirando solo `command`; ya no comprueba que `session-journal.sh` exista (B7) | T-03 | `doctor.py` construye `cmds` igual que `lint_plugin.py` (command + args), con el bloque compartido `hook_cmd_con_args` declarado en `copias.json` (ADR-016) en vez de duplicarlo a mano sin guardarrail | `agent-kits/shared/doctor.py::_bloque_plugin_hooks_recorrer`; `agent-kits/shared/copias.json` (bloque `hook_cmd_con_args`); `test_hook_exec_form_con_script_inexistente_en_args_es_error` |
| 12 | Important | `sesion.journal.{activo: false}` (forma objeto documentada en `design.md`) no apaga la captura: `_journal_activo` solo mira `is not False` (B8) | T-03 | `_journal_activo` mira `v.get("activo") is not False` cuando `journal` es un objeto, además del booleano | `journal.py::_journal_activo`; `test_journal_activo_objeto_con_activo_false_es_opt_out` |
| 13 | Important | En este tramo nadie invoca `replay` (`session-context.sh` no drena hasta T-05): publicado así, ninguna instalación escribe bitácora (B9) | T-04 → T-05 | Reasignado, tal y como decidió el orquestador: **no** se implementa en T-fix1; lo cierra T-05 (reconciliación en `SessionStart`) | `grep -rn replay hooks/` (sigue sin invocarse fuera de `journal.py` mismo; a demanda funciona con `journal.py replay`) |
| 14 | Important | `--budget-ms` solo se mira antes de reclamar; un item puede costar 3×git + `claude -p` (25 s) → `SessionStart` bloqueado >30 s pese a `--budget-ms 300`; el test solo cubre `budget_ms=0` (B10) | T-04 | `replay` acepta `--ia auto\|no`; con `--ia no` o `budget_ms < BUDGET_MS_AJUSTADO` (5000 ms) fuerza `ia=off` y un `git_timeout` acotado (`BUDGET_GIT_TIMEOUT = 2s`) | `journal.py::replay` (`ia_efectiva`, `git_timeout`); `test_replay_bajo_presupuesto_ajustado_no_llama_a_la_ia` (con dientes: `resumen_ia` monkeypercheado para lanzar `AssertionError` si se llamara) |
| 15 | Important | `transcript_path` viaja en un envelope durable y `replay` lo abre sin validar: un envelope plantado lee un transcript de OTRO proyecto y lo vuelca en un fichero versionado (C2 · CWE-73/22/200) | T-04 | `_transcript_seguro`: solo se usa si es ruta absoluta, existe, termina en `.jsonl` y su `basename` es `<session_id>.jsonl`; si no, se ignora (cubre también CA-05: la entrada declara la carencia) | `journal.py::_transcript_seguro`, usado en `replay`; `test_replay_transcript_ajeno_o_relativo_se_ignora` |
| 16 | Important | Exec form sin red: si un runtime no honra `args`, `bash` lee el payload de stdin como shell y ejecuta `$(…)` embebido en `cwd`; `interop/codex/hooks.json` regenerado así sin verificar que Codex soporte `args` (B16, C5 · CWE-78) | T-03 | `export-interop.py` traduce `SessionEnd` a SHELL FORM (`bash "<ruta>"`) para Codex (sin `args` sueltos); exec form se mantiene solo para `hooks/hooks.json` (contrato de Claude Code verificado 2026-09-17). Comentario en `session-journal.sh` explicando por qué el script NO puede defenderse a sí mismo del escenario «bash sin fichero» (es técnicamente imposible: el script ni siquiera llega a ejecutarse en ese caso) | `scripts/export-interop.py::_hook_a_shell_form/codex_hooks_json`; `hooks/session-journal.sh` (nota de seguridad + `M-01`); `test_codex_session_end_va_en_shell_form_no_exec_form` |
| 17 | Minor | «Acepta `schema_version` N y N-1» es vacío con `SCHEMA_VERSION = 1` y sin test que guarde la rama; CA-05 solo prueba «usa el log de prompts», no «registra la carencia» (A5) | T-04 | `_schema_aceptados(version)` extraída a función pura y probada con N=1 y N=2; `draft` añade un aviso explícito cuando no hay ni log ni transcript legible («CA-05: no se inventa contenido») | `journal.py::_schema_aceptados/draft`; `test_schema_aceptados_admite_n_y_n_menos_1`, `test_draft_sin_turnos_ni_transcript_declara_la_carencia` |
| 18 | Minor | T-03 regeneró `interop/codex/hooks.json` sin pegar la evidencia de `export-interop.py --check` (el revisor lo ejecutó: `48 ficheros al día`, exit 0) (A6) | T-03 | Evidencia pegada en la nota fix1 de T-03 | `python3 scripts/export-interop.py --check` → `export-interop --check: 48 ficheros al día` (re-ejecutado tras regenerar por el gap 16) |
| 19 | Minor | `tests/test_console_encoding.py` viaja en el commit de T-03/T-04 pero su declaración en `Archivos` vive en el ledger sin comitear (A7) | T-01 | La declaración en `Archivos` de T-01 y el fichero viajan en el MISMO commit de esta corrección (`T-01-fix1`), cerrando el desfase | `docs/roadmap/2026-09-17-session-end-durable-capture/tasks.md` (campo `Archivos` de T-01) + `tests/test_console_encoding.py`, mismo commit |
| 20 | Minor | `docs/FLOWS.md` + `docs/en/FLOWS.md` siguen dibujando `session-journal.sh (timeout 45)` escribiendo en el teardown; ninguna tarea pendiente los declara (A8) | T-07 | Reasignado, tal y como decidió el orquestador: **no** se toca en T-fix1 — queda en `Archivos` de T-07 | `docs/FLOWS.md:298`, `docs/en/FLOWS.md:300` (sin cambios en este ciclo) |
| 21 | Minor | `_escribir_atomico` no hace `fsync` del directorio tras `os.replace`; la degradación del `fsync` es silenciosa (B11) | T-01 | `_fsync_dir` hace `fsync` del directorio tras `os.replace` (ignorado en Windows); si el fsync del fichero o del directorio degrada, se marca un sentinela (`_DEGRADADO_MARKER`) que `estado()` reporta como `durabilidad: degradada` | `outbox.py::_fsync_dir/_marcar_degradado/estado`; `test_estado_cuenta_por_carpeta` (`durabilidad == "ok"`) |
| 22 | Minor | `done/`/`dead-letter/` sin retención (crecen 2 ficheros por sesión para siempre) y una clave en dead-letter jamás puede recapturarse (B13) | T-01/T-04 | `outbox.purgar_antiguos(dir, "done", dias)` borra entradas de `done/` con más de `LOG_RETENCION_DIAS`; `dead-letter/` se conserva a propósito. Una clave en dead-letter SÍ puede recapturarse si el evento tiene `sequence` distinto (gap 6: `event_id` incluye `sequence`, así que difiere automáticamente) | `outbox.py::purgar_antiguos`, invocado desde `journal.py::replay`; `test_purgar_antiguos_borra_done_pero_no_dead_letter` |
| 23 | Minor | `dead_letter` abre `causa.json` sin cerrarlo (B15); `journal.dir` de `dev.json` sin contención (absoluta/`..` sacan la cola del proyecto y `purgar` hará `rmtree` ahí) (C3 · CWE-22); `outbox.escribir` no valida `clave` (`../../ESCAPE` crea fuera de la cola) (C4 · CWE-22) | T-01/T-03 | `dead_letter` usa `with open(...)` (cierra el handle); `_journal_queue_dir` rechaza `dir` absoluto o con `..` (aviso + default); `outbox.escribir` valida `clave` con `^[A-Za-z0-9._-]{1,64}$` (`ValueError` si no casa) | `outbox.py::dead_letter/escribir`; `journal.py::_journal_queue_dir`; `test_dead_letter_no_fuga_el_handle_de_causa_json`, `test_journal_queue_dir_rechaza_absoluto_y_dotdot`, `test_escribir_valida_clave_y_rechaza_escape` |
| 24 | Minor | Comentario obsoleto «`timeout: 45`» en `journal.py:162`; el envelope no guarda `hook_event_name` aunque `design.md` lo lista; `claude-code-contracts.md:26` cita `timeout: 20` (preexistente) (B, A) | T-03 | Comentario corregido a `timeout: 5`; `hook_event_name` añadido al envelope; `claude-code-contracts.md:26` actualizado a `timeout: 5`, verificado 2026-09-17 | `journal.py:163` (comentario), `journal.py::capture_end` (`hook_event_name`); `skills/plugin-dev/references/claude-code-contracts.md:26`; `test_capture_end_incluye_hook_event_name` |

**Verificado OK por la revisión (sin cambios):** claim exclusivo entre procesos (`os.replace`, ThreadPool); ventana `escribir`↔`reclamar` sin duplicados; `redact.py` idéntico byte a byte al `redactar` anterior (7 casos, mismos flags) y declarado en `copias.json`; CA-01 con dobles de `git`/`claude` en PATH (unitario + hook); payload roto (vacío, `[]`, `"hola"`, `{`) → rc 0 y outbox vacía; `session_id` con `../` o Unicode → clave hex, frontmatter escapado; envelope venenoso (JSON inválido) → dead-letter y el resto sigue; `hooks.json` exec form aceptado por `lint_plugin` con test negativo con dientes; `export-interop --check` 48 al día; sin `eval`/`shell=True`; `eval "$(…)"` del hook eliminado (mejora neta); `_load_module` resuelve desde el plugin, no desde el proyecto.

## Revisión de dos lentes — intento 2: 3 Critical + 11 Important + 11 Minor NUEVOS (lentes A+B+C; D por ruta, sin hallazgos) → corrección `T-fix2`

Lentes: **A+B+C** con traspaso de la tabla del intento 1. `review-lens-select` activó también **D** por la ruta `scripts/export-interop.py` (stem `export`); el único cambio ahí es `_hook_a_shell_form` (≤ 10 hooks, sin I/O en bucle): revisado por el orquestador, sin hallazgos de rendimiento. Re-evaluación de los 24 gaps del intento 1: **20 cerrados con guarda efectiva** (mutantes mínimos → rojo), 2 reasignados (13 → T-05, 20 → T-07), 2 no cerrados (2: sin test; 19: corrección declarada falsa) y 4 con guarda floja (7, 16, 21, 23). Los gaps de abajo son NUEVOS, introducidos por la corrección; todos reproducidos; ninguno rebatido. T-01/T-03/T-04 vuelven a `en-progreso`; corrección con clave `T-0X-fix2`. **Este es el 3.º y último intento del bucle.**

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 25 | Critical | El TTL de huérfanos de `processing/` se mide sobre el mtime del envelope (creación), no sobre la reclamación: un envelope que esperó > 600 s en `outbox/` (el caso normal: replay horas después) se entrega a dos trabajadores a la vez; el segundo `completar` revienta (B1) | T-01 | pendiente | `outbox.py:241` |
| 26 | Critical | Un fallo transitorio agota los 3 intentos dentro de la MISMA pasada de `replay` (reencola → el bucle lo reclama al instante, sin backoff) → dead-letter en milisegundos; `_localizar` incluye `dead-letter/` y no hay comando de reproceso → la sesión se pierde para siempre (B2) | T-04 | pendiente | `journal.py:483-489`, `outbox.py:214-226` |
| 27 | Critical | `captured_at` sin validar entra en el nombre de fichero y el frontmatter de la entrada: `"../../../../tmp/PWN"` → `<root>/.-sesion.md` fuera de `docs/knowledge/journal/`; `"../adr/xx"` → `docs/knowledge/adr/xx-sesion.md` (doctrina versionada); `\n` inyecta claves YAML (B3, K-2 · CWE-22/93) | T-04 | pendiente | `journal.py:893`, `404-414` |
| 28 | Important | `sequence` = líneas del log de prompts NO es monótono: el log rota (`_rotar`, `LOG_MAX_BYTES`) y el contador vuelve a un valor ya usado → `event_id` colisiona con `done/` → el cierre legítimo no se encola (A-N1) | T-03 | pendiente | `journal.py:327,358`, `:141,:589` |
| 29 | Important | El Critical 1 del intento 1 se cerró sin test: sustituir los `except` de `replay()` por `raise` y quitar el de `cmd_replay` deja la suite verde (A-N2) | T-04 | pendiente | `journal.py:482-489`, `1382-1390` |
| 30 | Important | `"${ROOT_ARGS[@]}"` sobre array vacío bajo `set -u` aborta en bash < 4.4 (macOS `/bin/bash` 3.2) → sin `CLAUDE_PROJECT_DIR` el hook muere antes del `printf` y no encola; la rama nueva no tiene test (A-N3) | T-03 | pendiente | `hooks/session-journal.sh:57,64` |
| 31 | Important | El barrido de `reclamar` llama a `dead_letter()` sin guarda y `ob.reclamar()` está FUERA del `try` por item en `replay`: cualquier excepción del barrido aborta el drenaje entero (B4) | T-01/T-04 | pendiente | `outbox.py:228-247`, `journal.py:458` |
| 32 | Important | El cerrojo de `replay` es `flock` BLOQUEANTE tomado antes de arrancar el reloj → `budget_ms=500` tarda 8 s si otro replay tiene el cerrojo; `SessionStart` (T-05) se colgaría (B5) | T-04 | pendiente | `journal.py:450-451,535` |
| 33 | Important | `purgar_antiguos` filtra por mtime del envelope (creación), no por fecha de completado: un envelope que esperó 40 días se materializa y se borra de `done/` en la misma pasada → sin manifiesto y sin barrera de idempotencia (B6) | T-01/T-04 | pendiente | `outbox.py:350-374`, `journal.py:496` |
| 34 | Important | `sesion.journal.dir` con contención LÉXICA: `"."` o `"docs"` pasan y `_asegurar_gitignore_local` planta `.gitignore` con `*` + `chmod 0700` en la raíz o en `docs/`; un symlink versionado (`esc -> /VICTIMA`) lo salta; `C:evil` (relativa a unidad, Windows) sale de la raíz (B7, K-3, C-2, C-3 · CWE-59/22/732) | T-03 | pendiente | `journal.py:286-287,376-389` |
| 35 | Important | `limpiar_tmp_huerfanos` decide por subcadena `".tmp-"`: una clave válida por contrato que la contenga se borra en silencio a los 600 s (B8) | T-01 | pendiente | `outbox.py:377-396` |
| 36 | Important | `_hook_a_shell_form` construye `'bash "%s"'` por interpolación sin escapar: `"`, `` ` ``, `$(` en `args[0]` inyectan; el test congela el formato inseguro; hooks con ≠ 1 arg o `command` ≠ bash se exportan tal cual sin aviso (C-1, B12 · CWE-78) | T-03 | pendiente | `scripts/export-interop.py:298-302`, `tests/test_export_interop.py:136-145` |
| 37 | Important | `_validar_envelope` solo valida `session_id`/`schema_version`: `reason` llega sin escapar al frontmatter YAML (`"other\nevil: si"` → claves inyectadas en un `.md` versionado) (C-4 · CWE-93) | T-04 | pendiente | `journal.py:404-414,952` |
| 38 | Important | `_transcript_seguro` NO cierra el gap 15: `isfile` sigue symlinks y `basename == <session_id>.jsonl` compara dos campos del MISMO envelope no confiable → transcript ajeno leído y volcado en un `.md` versionado (K-1 · CWE-59/73/200) | T-04 | pendiente | `journal.py:392-401` |
| 39 | Minor | La corrección declarada del gap 19 es falsa: `tests/test_console_encoding.py` entró en `3b08e4c`, la declaración en `Archivos` en `e2fbb68` (A-N4) | T-01 | pendiente | `tasks.md` fila 19 |
| 40 | Minor | `durabilidad: degradada` sin test de la rama degradada (mutante `"ok"` fijo → verde) (A-N5) | T-01 | pendiente | `outbox.py:112,346` |
| 41 | Minor | `dead_letter` con `with open` sin dientes (modo de fallo solo Windows); `replay` crea la carpeta y el cerrojo sin sembrar `.gitignore` de la cola → `.replay.lock.lock` asoma en `git status` (A-N6) | T-01/T-04 | pendiente | `outbox.py:325`, `journal.py:444-450` |
| 42 | Minor | El test del cerrojo de `replay` es intermitente: mutante sin cerrojo → rojo 11/20 (A-N7) | T-04 | pendiente | `test_journal.py:1140` |
| 43 | Minor | `causa.json` de dead-letter declara `intentos: 1` tras 3 intentos (el sidecar `.intentos` no se propaga) (B9) | T-01 | pendiente | `outbox.py:220-224,318-330` |
| 44 | Minor | Fecha de la entrada en UTC (`captured_at[:10]`) mientras el resto del módulo usa fecha local: `TZ=America/Santiago` 22:30 → entrada del día siguiente (B10) | T-04 | pendiente | `journal.py:893` vs `217-218` |
| 45 | Minor | `replay` cuenta `dead_letter += 1` cuando `reencolar_o_dead_letter` devuelve `False` también por «no se pudo mover» → JSON miente (B11) | T-04 | pendiente | `journal.py:485-488` |
| 46 | Minor | Permisos aplicados tras crear (`makedirs` con umask → `chmod`), fallo de `chmod` tragado sin señal; la raíz de la cola creada por `replay` nunca recibe 0700; `.gitignore`/sidecars a umask (C-5 · CWE-732/367) | T-01/T-04 | pendiente | `outbox.py:96-109`, `journal.py:445` |
| 47 | Minor | Sin `CLAUDE_PROJECT_DIR`, el `cwd` del payload elige la raíz donde el hook crea directorios y planta `.gitignore` (C-6 · CWE-73). Simétrico con `user-prompt-capture.sh` y acotado por `isdir` + `proyecto_con_plugin()` | T-03 | pendiente (decisión: deuda aceptada por diseño, documentar) | `hooks/session-journal.sh:53-62`, `journal.py:1374` |
| 48 | Minor | `_cerrojo(".replay.lock")` crea `.replay.lock.lock` (`_cerrojo` ya añade `.lock`); `docs/observability.md` y el README del journal no describen `derivados_en`/`materializado_en` (B, A) | T-04 → T-07 | pendiente | `journal.py:450,559` |

**Verificado OK por la revisión (sin cambios):** gaps 1(código), 3, 4, 5, 6(código), 8, 11 (doble guarda con `copias.json`), 12, 14, 15(código), 17, 18, 22, 24 del intento 1; permisos 0700/0600 en el caso normal; validación de `clave` (`../../ESCAPE`, `..\..\ESC`, `a/b`, 65 chars → `ValueError`); contador `.intentos` sobrevive al reencolado; `cmd_replay` imprime JSON cuando `replay()` lanza; `--ia no` corta la IA bajo presupuesto; `_schema_aceptados` con N=2; `export-interop --check` 48 al día; suite 1821 passed (1 rojo preexistente por `.claude/dev.json` del entorno).
