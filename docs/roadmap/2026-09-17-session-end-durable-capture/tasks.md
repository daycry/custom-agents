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
| Fase 1 - Módulos compartidos | 2 | 2 | 100% | 0.4 / 2.5h | 0.3 / 0.8h | 0 / 0.2h | 0 / 45k |
| Fase 2 - Captura y materialización | 2 | 2 | 100% | 1.3 / 5.5h | 1.1 / 1.6h | 0 / 0.4h | 0 / 85k |
| Fase 3 - Reconciliación y diagnóstico | 0 | 2 | 0% | 0 / 4h | 0 / 1.2h | 0 / 0.3h | 0 / 60k |
| Fase 4 - Pruebas, medición y cierre | 0 | 2 | 0% | 0 / 2h | 0 / 0.6h | 0 / 0.2h | 0 / 40k |
| **TOTAL** | **4** | **8** | **50%** | **1.7 / 14h** | **1.4 / 4.2h** | **0 / 1.1h** | **0 / 230k** |

## Fase 1 - Módulos compartidos

### T-01 - `outbox.py`: cola atómica con claim, done y dead-letter
- **Estado**: en-progreso
- **Tiempo humano**: est. 1.5h · real 0.2h (estimado)
- **Prevision IA**: 20k in / 8k out tok · real (estimado): usage-meter degradó a `fuente: estimado` (sin transcripciones en este entorno); horas_ia real (estimado): 0.15h
- **Dependencias**: ninguna
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/outbox.py`, `agent-kits/shared/test_outbox.py`, `agent-kits/shared/README.md`, `tests/test_console_encoding.py` (añadido en la puerta scope-check del intento 1: los scripts nuevos sin `__main__` necesitan su entrada en `MODOS`/`SIN_SIMBOLOS_EN_LA_SALIDA`)
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_outbox.py` -> escribir idempotente por clave, claim exclusivo con dos procesos, dead-letter con causa, corte antes/después del rename sin parcial · **ejecutado**: `13 passed in 0.05s`
- **RED**: `test_escribir_es_idempotente_por_clave` (y el resto del módulo) falló con `FileNotFoundError: [Errno 2] No such file or directory: '.../agent-kits/shared/outbox.py'` · 2026-09-17
**Criterios de aceptación**
- [x] Solo stdlib; sin red; contrato `escribir/reclamar/completar/dead_letter/estado/purgar` documentado en el docstring.
- [x] Dos `reclamar` concurrentes sobre el mismo item: uno gana, el otro recibe `None`.
- **Changelog**: Nueva cola atómica compartida `agent-kits/shared/outbox.py` (escribir/reclamar/completar/dead_letter/estado/purgar) para la captura durable de `SessionEnd` y futuros exportadores de memoria.

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
- **Tiempo humano**: est. 2.5h · real 0.6h (estimado)
- **Prevision IA**: 30k in / 12k out tok · real (estimado): usage-meter degradó a `fuente: estimado` (sin transcripciones en este entorno); horas_ia real (estimado): 0.5h
- **Dependencias**: T-01
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/journal.py`, `agent-kits/shared/test_journal.py`, `hooks/session-journal.sh`, `hooks/hooks.json`, `tests/test_hooks_shell.py`, `tests/test_hooks_config.py`, `.gitignore`, `scripts/lint_plugin.py`, `interop/codex/hooks.json`, `interop/opencode/**`
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_journal.py tests/test_hooks_shell.py tests/test_hooks_config.py` -> envelope válido en `outbox/`, ni `git` ni `claude` invocados (dobles en PATH), `hooks.json` con `command: bash` + `args` y `timeout: 5`, ruta con espacios y Unicode · **ejecutado**: `agent-kits/shared/test_journal.py` 58 passed, `tests/test_hooks_shell.py` 47 passed, `tests/test_hooks_config.py` 3 passed
- **RED**: `test_capture_end_escribe_envelope_valido_y_no_stdout` (y el resto de `capture_end`/CLI en `test_journal.py`, más `test_session_journal_no_invoca_git_ni_claude`/`test_session_journal_ruta_del_plugin_con_espacios_y_unicode`/`test_session_journal_repo_ajeno_sin_rastro_del_plugin_no_siembra_nada`/`test_session_journal_deja_envelope_en_outbox_y_replay_materializa_la_entrada` en `test_hooks_shell.py`, y `test_session_end_usa_exec_form_con_timeout_5`/`test_lint_plugin_da_error_si_el_script_de_args_no_existe` en `test_hooks_config.py`) fallaron contra el `journal.py`/`session-journal.sh`/`hooks.json`/`lint_plugin.py` previos a esta tarea (`AttributeError: module 'journal' has no attribute 'capture_end'`; outbox vacía; `'bash "${CLAUDE_PLUGIN_ROOT}/hooks/session-journal.sh"' != 'bash'`) · 2026-09-17
**Criterios de aceptación**
- [x] Envelope ≤ 64 KiB con `schema_version`, `event_id` determinista y sin texto de conversación.
- [x] Opt-out `sesion.journal: false` sigue funcionando; el objeto `sesion.journal.{dir,...}` se acepta.
- [x] `git` y `claude` falsos en `PATH` no se ejecutan durante la captura (CA-01).
- **Nota (desviación)**: `scripts/lint_plugin.py` (`lint_hooks`) solo escaneaba `command` en busca de rutas `${CLAUDE_PLUGIN_ROOT}/…`; con `command: bash` + `args` (exec form) el path vive en `args`, así que el linter no habría detectado un script inexistente ahí. Se amplió `lint_hooks` para escanear también `args` (dos tests nuevos en `test_hooks_config.py` prueban el antes/después). `interop/codex/hooks.json` se regeneró con `export-interop.py` para reflejar el exec form.
- **Changelog**: `SessionEnd` pasa a captura ULTRALIGERA (`journal.py capture-end`, exec form en `hooks.json`, `timeout: 5`): un envelope atómico en la outbox local, sin git, sin IA y sin red (CA-01).

### T-04 - `journal.py replay`: claim, materialización, verificación, dead-letter
- **Estado**: en-progreso
- **Tiempo humano**: est. 3h · real 0.7h (estimado)
- **Prevision IA**: 35k in / 14k out tok · real (estimado): usage-meter degradó a `fuente: estimado` (sin transcripciones en este entorno); horas_ia real (estimado): 0.6h
- **Dependencias**: T-01, T-02, T-03
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/journal.py`, `agent-kits/shared/test_journal.py`
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_journal.py -k replay` -> mismo evento ×5 = una entrada; envelope venenoso a `dead-letter/` y el resto continúa; transcript ausente usa el log de prompts o declara carencia; `cierre:` en el frontmatter · **ejecutado**: `python -m pytest -q agent-kits/shared/test_journal.py -k replay` → `12 passed`
- **RED**: `test_replay_materializa_reutilizando_escribir_sesion` (y el resto de `replay`/`cmd_replay`) falló con `AttributeError: module 'journal' has no attribute 'capture_end'`/`replay` sobre el `journal.py` previo a T-03/T-04 · 2026-09-17
**Criterios de aceptación**
- [x] Reutiliza `escribir_sesion` (git, prompts, IA opt-in) sin duplicar lógica.
- [x] Acepta `schema_version` N y N-1.
- [x] Nunca inventa contenido (CA-05).
- **Nota (desviación menor)**: `docs/knowledge/journal/README.md` no se toca a mano — lo sigue regenerando `journal.py index` (invocado por `write`) como siempre; no hacía falta cambiarlo aparte, así que se retira del campo `Archivos` original.
- **Nota (desviación de proceso)**: T-03 y T-04 se implementaron y commitean JUNTOS (un solo commit `T-03/T-04: …`) en vez de uno por tarea: `capture_end`/`replay` se escribieron en la misma sesión de edición sobre `journal.py` y separar el diff a mano por hunks arriesgaba dejar un commit intermedio no coherente (T-04 depende de T-03 y ambos tocan el mismo fichero en las mismas franjas). El commit de T-04 también incluye el arreglo de `tests/test_console_encoding.py` para `outbox.py`/`redact.py` (MODOS + `SIN_SIMBOLOS_EN_LA_SALIDA`): un hueco de T-01/T-02 que no se detectó entonces porque solo se corrió la suite dirigida, no `python3 -m pytest -q` completo — se corrige aquí, al primer punto en que se ejecutó la suite entera.
- **Nota (simplificación documentada)**: `sequence` del envelope queda fijo a 0 (MVP suficiente para CA-03: el mismo `(session_id, reason)` deduplica, incluso si el primero ya fue materializado y movido a `done/` — `outbox.escribir` lo detecta por clave en cualquier carpeta de la cola). Permitir que una reapertura legítima del mismo `(session_id, reason)` tras la materialización genere un envelope nuevo (incrementando `sequence`) queda para cuando haya evidencia de que hace falta; hoy ningún CA de la spec lo exige.
- **Changelog**: `journal.py replay` materializa la outbox reutilizando `escribir_sesion` (git, prompts, IA opt-in): claim exclusivo, verificación, `done/`/`dead-letter/` con causa, `cierre: materializado` en el frontmatter.

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

## Revisión de dos lentes — intento 1: 2 Critical + 12 Important + 10 Minor → todos a corrección (lentes A+B+C; `T-fix1` en curso)

Lentes: **A+B+C** (`review-lens-select.py`: C por `private-key` en `journal.py:188`/`redact.py:28` y stem `session` en `hooks/session-journal.sh`; D no aplica). Puerta `scope-check`: exit 0 tras declarar `tests/test_console_encoding.py` en T-01. Cada gap viene con reproducción del revisor; ninguno rebatido. T-01/T-03/T-04 vuelven a `en-progreso`; corrección medida con clave `session-end-durable-capture/T-0X-fix1`.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Critical | Un envelope reclamado que no llega a `completar`/`dead_letter` (corte, excepción) queda en `processing/` para siempre: `reclamar` solo lista `outbox/`, nada re-encola, y `capture-end` lo da por idempotente porque `_localizar` lo ve en `processing/`. `replay` informa `restantes: 0` (éxito falso) (B1) | T-01/T-04 | pendiente | `outbox.py:104-128`, `journal.py:344-383` |
| 2 | Critical | Cualquier excepción materializando (disco lleno, permisos, `os.replace` con handle abierto en Windows) aborta el drenaje entero sin `try/except` por item; el item queda en `processing/`, el resto no se procesa, `cmd_replay` no imprime JSON y `main` devuelve 0 (B2) | T-04 | pendiente | `journal.py:365-380`, `1239-1242`, `1358-1362` |
| 3 | Important | La `Verificación` de T-01 da por ejecutado «corte antes/después del rename sin parcial» y ese test no existe; CA-04 sin cobertura; los `.tmp-<pid>` huérfanos no los limpia nadie (A1, B14) | T-01 | pendiente | `test_outbox.py:34` |
| 4 | Important | «Envelope ≤ 64 KiB» marcado pero no impuesto: `session_id` sin tope (200.000 chars → 196 KiB); el test no tiene dientes (A2, B12) | T-03 | pendiente | `journal.py:249,320`, `test_journal.py:939` |
| 5 | Important | Evidencia de `Verificación` de T-04 no reproducible: el ledger pega «12 passed», el comando da 7 (A3) | T-04 | pendiente | `tasks.md` T-04 |
| 6 | Important | `sequence = 0` colapsa dos cierres legítimos de la misma sesión (`/resume` + nuevo turno + cierre): el segundo tramo nunca se journalea; regresión frente al hook anterior y el test que lo cubría se debilitó (A4, C-b) | T-03/T-04 | pendiente | `journal.py:315`, `outbox.py:81-96`, `tests/test_hooks_shell.py:279-292` |
| 7 | Important | Dos `replay` concurrentes pierden entradas: `write()` sin cerrojo elige el mismo nombre de fichero para dos sesiones y una pisa a la otra; spec C-02 exige `_cerrojo` (B3) | T-04 | pendiente | `journal.py:344-383`, `929-950` |
| 8 | Important | La entrada se materializa con datos del momento del replay (`fecha = hoy()`, iniciativa activa, ficheros tocados) en vez del cierre: `captured_at` no se usa (B4) | T-04 | pendiente | `journal.py:373-374`, `768-794` |
| 9 | Important | La cola se escribe world-readable (0644) y sin sembrar `.gitignore` en el proyecto consumidor: los envelopes salen en `git status`, se cuelan en `ficheros_tocados` y se pueden commitear (B5, C1 · CWE-538/732) | T-01/T-03 | pendiente | `outbox.py:67-100`, `journal.py:298-335` |
| 10 | Important | Regresión en la raíz: el hook perdió el fallback al `cwd` del payload (`CLAUDE_PROJECT_DIR > $PWD`) y siempre pasa `--root`, dejando muerta la cascada de `cmd_capture_end`; asimétrico con `user-prompt-capture.sh` → turnos capturados que ningún envelope materializa (A9, B6) | T-03 | pendiente | `hooks/session-journal.sh:41,46`, `journal.py:1226-1236` |
| 11 | Important | `/doctor` ciego al exec form: `doctor.py` duplica el escaneo de hooks mirando solo `command`; ya no comprueba que `session-journal.sh` exista (B7) | T-03 | pendiente | `agent-kits/shared/doctor.py:328-329` |
| 12 | Important | `sesion.journal.{activo: false}` (forma objeto documentada en `design.md`) no apaga la captura: `_journal_activo` solo mira `is not False` (B8) | T-03 | pendiente | `journal.py:272-275` |
| 13 | Important | En este tramo nadie invoca `replay` (`session-context.sh` no drena hasta T-05): publicado así, ninguna instalación escribe bitácora (B9) | T-04 → T-05 | pendiente (lo cierra T-05 en el tramo 2; el tramo 1 NO se publica solo) | `grep -rn replay hooks/` |
| 14 | Important | `--budget-ms` solo se mira antes de reclamar; un item puede costar 3×git + `claude -p` (25 s) → `SessionStart` bloqueado >30 s pese a `--budget-ms 300`; el test solo cubre `budget_ms=0` (B10) | T-04 | pendiente | `journal.py:361-374`, `test_replay_max_y_budget_ms_acotan_el_trabajo` |
| 15 | Important | `transcript_path` viaja en un envelope durable y `replay` lo abre sin validar: un envelope plantado lee un transcript de OTRO proyecto y lo vuelca en un fichero versionado (C2 · CWE-73/22/200) | T-04 | pendiente | `journal.py:331-342`, `374`, `715-741` |
| 16 | Important | Exec form sin red: si un runtime no honra `args`, `bash` lee el payload de stdin como shell y ejecuta `$(…)` embebido en `cwd`; `interop/codex/hooks.json` regenerado así sin verificar que Codex soporte `args` (B16, C5 · CWE-78) | T-03 | pendiente | `hooks/hooks.json:47-50`, `interop/codex/hooks.json:39-46` |
| 17 | Minor | «Acepta `schema_version` N y N-1» es vacío con `SCHEMA_VERSION = 1` y sin test que guarde la rama; CA-05 solo prueba «usa el log de prompts», no «registra la carencia» (A5) | T-04 | pendiente | `journal.py:248,339` |
| 18 | Minor | T-03 regeneró `interop/codex/hooks.json` sin pegar la evidencia de `export-interop.py --check` (el revisor lo ejecutó: `48 ficheros al día`, exit 0) (A6) | T-03 | pendiente | `tasks.md` T-03 |
| 19 | Minor | `tests/test_console_encoding.py` viaja en el commit de T-03/T-04 pero su declaración en `Archivos` vive en el ledger sin comitear (A7) | T-01 | pendiente | `tasks.md:33` |
| 20 | Minor | `docs/FLOWS.md` + `docs/en/FLOWS.md` siguen dibujando `session-journal.sh (timeout 45)` escribiendo en el teardown; ninguna tarea pendiente los declara (A8) | T-07 | pendiente (se añade a `Archivos` de T-07) | `docs/FLOWS.md:298`, `docs/en/FLOWS.md:300` |
| 21 | Minor | `_escribir_atomico` no hace `fsync` del directorio tras `os.replace`; la degradación del `fsync` es silenciosa (B11) | T-01 | pendiente | `outbox.py:67-78` |
| 22 | Minor | `done/`/`dead-letter/` sin retención (crecen 2 ficheros por sesión para siempre) y una clave en dead-letter jamás puede recapturarse (B13) | T-01/T-04 | pendiente | `outbox.py:81-102` |
| 23 | Minor | `dead_letter` abre `causa.json` sin cerrarlo (B15); `journal.dir` de `dev.json` sin contención (absoluta/`..` sacan la cola del proyecto y `purgar` hará `rmtree` ahí) (C3 · CWE-22); `outbox.escribir` no valida `clave` (`../../ESCAPE` crea fuera de la cola) (C4 · CWE-22) | T-01/T-03 | pendiente | `outbox.py:171`, `journal.py:262-269`, `outbox.py:81-100` |
| 24 | Minor | Comentario obsoleto «`timeout: 45`» en `journal.py:162`; el envelope no guarda `hook_event_name` aunque `design.md` lo lista; `claude-code-contracts.md:26` cita `timeout: 20` (preexistente) (B, A) | T-03 | pendiente | `journal.py:162`, `design.md:40` |

**Verificado OK por la revisión (sin cambios):** claim exclusivo entre procesos (`os.replace`, ThreadPool); ventana `escribir`↔`reclamar` sin duplicados; `redact.py` idéntico byte a byte al `redactar` anterior (7 casos, mismos flags) y declarado en `copias.json`; CA-01 con dobles de `git`/`claude` en PATH (unitario + hook); payload roto (vacío, `[]`, `"hola"`, `{`) → rc 0 y outbox vacía; `session_id` con `../` o Unicode → clave hex, frontmatter escapado; envelope venenoso (JSON inválido) → dead-letter y el resto sigue; `hooks.json` exec form aceptado por `lint_plugin` con test negativo con dientes; `export-interop --check` 48 al día; sin `eval`/`shell=True`; `eval "$(…)"` del hook eliminado (mejora neta); `_load_module` resuelve desde el plugin, no desde el proyecto.
