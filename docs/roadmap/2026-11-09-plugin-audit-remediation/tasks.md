---
tasks: plugin-audit-remediation
estado: en-progreso
creado: 2026-11-09
verificacion: obligatoria
changelog: Fixed
---

# Corrección de la auditoría completa de v3.2.2

> Ledger canónico de progreso. Fuente única. Autorización: el usuario pidió corregir todo lo hallado en la auditoría del 2026-11-09 («adelante, con todo»). Hallazgos numerados según la auditoría local (H-1…H-49 y menores).

[Spec](spec.md) · [Plan](improvement-plan.md)

## Resumen de progreso

| Fase | Completadas | Total | Progreso |
|---|---|---|---|
| Fase 1 | 4 | 6 | 66.7% |
| Fase 2 | 0 | 6 | 0.0% |
| Fase 3 | 0 | 4 | 0.0% |
| Fase 4 | 0 | 5 | 0.0% |
| **TOTAL** | **4** | **21** | **19.0%** |

## Fase 1 — Seguridad y pérdida de datos

**Estado**: en-progreso

### T-01 — worklog sin pérdida de datos

- **Estado**: completado
- **Descripción**: H-1 y H-2. Un estado ilegible o con BOM no se trata como vacío ni se sobrescribe; escritura atómica; fecha futura y horas negativas rechazadas.
- **Archivos**: `skills/jira-sync/scripts/worklog.py`, `tests/test_worklog.py`, `agent-kits/shared/usage-meter.py`, `agent-kits/shared/test_usage_meter.py` (añadidos en la revisión intento 1, gap 3: mismo defecto de estado ilegible tratado como vacío).
- **Verificación**: `python -m pytest -q tests/test_worklog.py` → todos pasan, con casos de BOM, JSON corrupto, fecha futura y horas negativas.
- **Changelog**: El worklog de Jira ya no pierde el banco de horas: un estado con BOM se lee, uno ilegible detiene la imputación sin escribir, y se rechazan fechas futuras y horas negativas.
- **Cerrada**: 2026-11-09

**Criterios de aceptación**
- [x] `jira-state.json` con BOM se lee bien; corrupto → exit 2 sin escribir.
- [x] Escritura atómica (tmp + `os.replace`).
- [x] `--fecha` futura y horas negativas → exit 2.


RED: `tests/test_worklog.py (6 casos nuevos)` falló con 6 failed, 2 passed: BOM leido como vacio (bancoPendiente 0), corrupto/futura/negativas exit 0 con aplicado, raiz lista traceback exit 1, save_json sin os.replace · 2026-11-09.

GREEN: `python -m pytest -q tests/test_worklog.py` → `8 passed in 6.18s` (BOM, corrupto, raíz lista, ausente, os.replace, fecha futura/inválida, 6 flags negativos + 13 casos históricos); `test_jira_flow.py` → `74 passed` · 2026-11-09.


RED: `agent-kits/shared/test_usage_meter.py -k fix1 + tests/test_worklog.py -k fix1` falló con fix1: usage-meter 2 failed (BOM e ilegible tratados como vacio y sobrescritos); worklog 3 failed (nan/inf aceptados, tipos erroneos con traceback, PermissionError en os.replace sin reintento) · 2026-11-09.

GREEN fix1: `pytest tests/test_worklog.py` → `11 passed` (nan/inf, 7 formas de tipo equivocado sin traceback, reintento acotado de `os.replace` ante PermissionError); `pytest agent-kits/shared/test_usage_meter.py` → `80 passed` (BOM conserva marcadores; ilegible o raíz no objeto → start/close exit 3 sin escribir, status exit 0 con aviso; el test histórico de estado corrupto conserva el caso de marcador corrupto y los casos ilegibles pasan al test nuevo); `test_jira_flow.py` → `74 passed` · 2026-11-09.

### T-02 — qa-gate sin falso verde

- **Estado**: completado
- **Descripción**: H-3 y menor C4. Un test con `expectedStatus: "skipped"` no cuenta como pasado; BOM y raíz no objeto dan veredicto, no traceback.
- **Archivos**: `agent-kits/qa/qa-gate.py`, `tests/test_qa_gate.py`.
- **Verificación**: `python -m pytest -q tests/test_qa_gate.py` → todos pasan, con los casos nuevos.
- **Changelog**: La puerta de QA ya no da verde con todo saltado: un test marcado como saltado cuenta como saltado, y un results.json con BOM o con forma inesperada da un veredicto claro.
- **Cerrada**: 2026-11-09

**Criterios de aceptación**
- [x] Sin bloque `stats`, un test saltado se cuenta como `skipped` y 0 ejecutados no es VERDE.
- [x] `results.json` con BOM se lee; raíz lista → ROJO con motivo.


RED: `tests/test_qa_gate.py (5 casos nuevos)` falló con 5 failed: skipped sin stats contado passed con VERDE, BOM da malformado, raiz lista y estructuras inesperadas dan Traceback · 2026-11-09.

GREEN: `python -m pytest -q tests/test_qa_gate.py` → `6 passed in 4.63s` (skipped sin stats, skipped+passed, BOM, raíz lista, 4 estructuras inesperadas sin traceback); `python tests/test_qa_gate.py` → `13/13 OK` · 2026-11-09.


RED: `tests/test_qa_gate.py::test_fallo_seguido_de_saltado_no_desaparece` falló con fix1: [failed, skipped] contado como skipped (counts.skipped 1), el fallo previo desaparecia · 2026-11-09.

GREEN fix1: `pytest tests/test_qa_gate.py` → `7 passed in 4.83s` (la rama skipped exige TODOS los resultados saltados) · 2026-11-09.

### T-03 — Instalador robusto en Windows y con configuración ajena

- **Estado**: en-progreso
- **Descripción**: H-4, H-9, H-10, H-11, H-13 y menores del instalador. Buscar las CLI sin el directorio actual; `merge` con lectura estricta; `uninstall` aislado por proveedor; enlaces solo prohibidos en lo que crea el instalador; aviso de rutas absolutas en configuración compartida; misma exclusión de tests desde un clon que en npm.
- **Archivos**: `install/install.mjs`, `install/providers.mjs`, `install/manifest-auth.mjs`, `tests/installer.test.mjs`, `tests/install-auth.test.mjs`, `docs/INSTALL.md`, `docs/en/INSTALL.md`.
- **Verificación**: `node --test tests/installer.test.mjs tests/install-auth.test.mjs` → 0 fail, con casos nuevos para `.cmd` plantado, JSON ilegible en `merge`, manifiesto no verificable en `uninstall` y HOME bajo un enlace.
- **Changelog**: El instalador ya no ejecuta lanzadores plantados en el directorio actual, no reescribe JSON ilegibles, desinstala cada proveedor por separado, acepta HOME o dotfiles enlazados y avisa de rutas absolutas en configuración compartida.
- **Cerrada**: 2026-11-09

**Criterios de aceptación**
- [x] Un `claude.cmd`/`codex.cmd` en el cwd no se ejecuta.
- [x] `merge` sobre JSON ilegible falla sin escribir.
- [x] Un manifiesto no verificable no impide desinstalar los demás proveedores.
- [x] Un ancestro enlazado (HOME, dotfiles) no bloquea la instalación.
- [x] Desde un clon no se copian tests ni `.pytest_cache`.


RED: `tests/installer.test.mjs --test-name-pattern=auditor (7 casos) + tests/install-auth.test.mjs (2 casos H-11)` falló con 7 fail: .cmd del cwd resuelto por where.exe, merge reescribe marketplace.json ilegible con exit 0, uninstall aborta OpenCode por manifiesto de Claude, HOME/dotfile enlazado da unverified manifest, enlace en proyecto sin error propio, ficherosDe copia test_*.py, sin aviso de ruta absoluta · 2026-11-09.

GREEN: `node --test tests/installer.test.mjs` → `tests 182 · pass 182 · fail 0` (7 casos nuevos de auditoría incl. `.cmd` plantado, merge sobre marketplace.json ilegible, uninstall aislado, HOME y dotfile enlazados, enlace en proyecto → `linked path`, exclusión de tests/cachés, aviso de ruta absoluta); `node --test tests/install-auth.test.mjs` → `pass 7 · fail 0`; `node --test tests/codex-native-install.test.mjs` → `pass 11 · fail 0`. Decisión: anclas de confianza (HOME, raíces de config de cada runtime, paquete y `--dir`); por debajo del ancla más profunda un enlace da `LINKED_PATH` · 2026-11-09.

### T-04 — Graphiti sin proxy

- **Estado**: completado
- **Descripción**: H-5. El tráfico a Graphiti (solo local o privado) no pasa por `HTTP(S)_PROXY` ni por el proxy del sistema.
- **Archivos**: `skills/knowledge-services/backends/graphiti.py`, `skills/knowledge-services/scripts/test_graphiti_backend.py`, `tests/test_graphiti_security.py`.
- **Verificación**: test que comprueba que los openers no llevan proxy con `HTTP_PROXY` definido → pasa.
- **Changelog**: Las conexiones a Graphiti, que solo van a hosts locales o privados, ya no pasan por el proxy del entorno ni por el del sistema.
- **Cerrada**: 2026-11-09

**Criterios de aceptación**
- [x] Los dos openers usan `ProxyHandler({})`.


RED: `tests/test_graphiti_security.py::test_openers_de_graphiti_ignoran_proxy_del_entorno` falló con URLError getaddrinfo failed: con HTTP_PROXY definido _post_json resolvio el host del proxy en vez de 127.0.0.1 · 2026-11-09.

GREEN: `pytest tests/test_graphiti_security.py -k ignoran_proxy` → `1 passed` (sin el fix: `1 failed`); fichero completo → `126 passed in 79.13s`; `skills/knowledge-services/scripts/test_backend_graphiti.py` → `209 passed`; `tests/test_copias_declaradas.py` → `30 passed`. Nota: `test_graphiti_backend.py` del campo Archivos no existe; el test va en `tests/test_graphiti_security.py` (declarado); `graphiti.py` no tiene huella `sha256_lf` · 2026-11-09.

### T-05 — Guardarraíles en perfil lite y en subagentes

- **Estado**: completado
- **Descripción**: H-6 y H-7. La implementación siempre se despacha a la identidad nativa `implementer` (también en `lite` y con subagentes), para que la guardia nativa aplique.
- **Archivos**: `commands/dev-cycle.md`, `agent-kits/dev-cycle/references/phase3-subagents.md`, `skills/quick-implement/SKILL.md`, `agent-kits/shared/task-brief.py`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `interop/**`, `tests/test_dev_cycle_split.py`, `tests/fixtures/dev-cycle-modular-replacements.json`, `tests/fixtures/dev-cycle-paragraphs.json`, `tests/test_native_guardrail_dispatch.py`, `docs/agents/CONTRACTS.md`, `docs/guides/quality-playbook.md`, `docs/guides/subscription-efficiency.md` (añadidos por el implementer: E3, también describían «lite en el hilo actual»), `docs/agents/implementer.md`, `agent-kits/shared/README.md` (revisión intento 1, gap 4).
- **Verificación**: test que exige el despacho a `implementer` en lite y subagentes → pasa; `export-interop.py --check` al día; ahorro de la vía rápida ≥ 6000.
- **Changelog**: La implementación se entrega siempre a la identidad nativa del implementer, también en el perfil lite y con subagentes, para que su guardia de rama, alcance y git aplique.
- **Cerrada**: 2026-11-09

**Criterios de aceptación**
- [x] `lite` implementa con `implementer` en secuencia, no en el hilo principal.
- [x] El modo subagentes despacha `implementer` con el brief.


RED: `tests/test_native_guardrail_dispatch.py` falló con 5 failed, 1 passed: lite dice implementa en el hilo actual, paso 2 sin subagent_type implementer, brief lite y docs con hilo actual/current thread, interop sin native-roles.json · 2026-11-09.

GREEN: `pytest tests/test_native_guardrail_dispatch.py` → `6 passed`; `tests/test_dev_cycle_split.py` → `10 passed` (ahorro vía rápida 6012 → 6057: la frase de justificación de la vía rápida se condensa en su conclusión; filas de reemplazo registradas, incl. la encadenada `2ece9f09`→nuevo); `export-interop.py` → `92 ficheros escritos` y `--check` → `92 ficheros al día`; `tests/test_lite_profile.py` 30 passed; `test_token_estimates.py` 13 passed; `agent-kits/shared/test_context_footprint.py` 15 passed; `test_source_snapshot.py` 33 passed, 1 skipped; `test_task_brief.py` 92 passed. `skills/quick-implement/SKILL.md` no cambia (ya despachaba a `implementer`) · 2026-11-09.


RED: `tests/test_native_guardrail_dispatch.py (DOCS ampliada + respaldo copiado)` falló con fix1: 2 failed: docs/agents/implementer.md y shared README dicen hilo actual; sin respaldo implementer en instalacion copiada · 2026-11-09.

GREEN fix1: `pytest tests/test_native_guardrail_dispatch.py` → `7 passed` (DOCS incluye docs/agents/implementer.md y shared README; respaldo `implementer` con bundle copiado); `tests/test_dev_cycle_split.py` → `10 passed`, ahorro vía rápida 6055 (≥ 6000; la frase duplicada «La política efectiva prevalece…» se integra en «Consume sus flags efectivos»); `tests/test_lite_profile.py` → `30 passed`; `export-interop.py --check` → `92 ficheros al día` · 2026-11-09.

### T-06 — Puertas que fallan cerradas

- **Estado**: en-progreso
- **Descripción**: H-8 y H-12. `review-lens-select` en `auto` activa C y D ante error; `guardrail-check` deniega `reset --hard`, `clean -f*`, borrar ramas remotas y `stash drop|clear`.
- **Archivos**: `skills/adversarial-review/scripts/review-lens-select.py`, `skills/adversarial-review/scripts/test_review_lens_select.py`, `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/test_guardrail_check.py`, `skills/adversarial-review/SKILL.md`, `tests/test_graphiti_security.py`, `CHANGELOG.md`, `CHANGELOG.es.md` (añadidos por el implementer: entrada `### Fixed` de toda la Fase 1, commit aparte pedido por el orquestador).
- **Verificación**: tests de los dos scripts → pasan con los casos nuevos.
- **Changelog**: Las puertas fallan cerradas: si no se puede evaluar el diff se activan las lentes de seguridad y rendimiento, y el implementer ya no puede descartar cambios, borrar ramas remotas ni vaciar stashes.
- **Cerrada**: 2026-11-09

**Criterios de aceptación**
- [x] `--base` inexistente en `auto` → `lente_c` y `lente_d` true con aviso.
- [x] Las seis operaciones destructivas se deniegan para el implementer.


RED: `test_review_lens_select.py::test_error_en_auto_activa_c_y_d_con_aviso_exit_0 + test_guardrail_check.py::test_git_deny_operaciones_destructivas_auditoria` falló con --base inexistente en auto dio lente_c False; 17 failed: reset --hard, clean -f*, push :rama/--delete/-d y stash drop/clear permitidos · 2026-11-09.

GREEN: `pytest skills/adversarial-review/scripts/test_review_lens_select.py` → `61 passed in 126.89s`; `pytest agent-kits/shared/test_guardrail_check.py` → `158 passed in 7.43s` (18 destructivas deny + 16 no destructivas allow); `tests/test_copias_declaradas.py` → `30 passed`. Ninguno de los dos scripts tiene huella `sha256_lf` · 2026-11-09.


RED: `agent-kits/shared/test_guardrail_check.py -k fix1_formas` falló con fix1: 23 failed: --ha/--fo/--del/--mirror/--prune, clean.requireForce en linea y -c alias.* permitidos; clean --dr -f denegado · 2026-11-09.

## Fase 2 — Funciones documentadas que no funcionan

**Estado**: borrador

### T-07 — Retoma de sesión: journal y bloque útil

- **Estado**: borrador
- **Descripción**: H-14, H-27 y H-48. Reinyectar la última entrada del journal sin depender de la selección global de ledgers; iniciativa en curso primero en memoria; líneas opacas fuera; iniciativas al 100 % compactadas; pie sin ruta absoluta; `clear` también en Claude.
- **Archivos**: `agent-kits/shared/progress-report.py`, `hooks/session-context.py`, `hooks/hooks.json`, `agent-kits/shared/test_progress_report.py`, `tests/test_session_context.py`, `tests/test_hooks_shell.py`, `interop/**`, `docs/observability.md`, `docs/en/observability.md`.
- **Verificación**: test con más de 1 MiB de ledgers y dos iniciativas activas → se reinyecta la entrada del journal; tests de sesión existentes pasan.

**Criterios de aceptación**
- [ ] El journal se reinyecta con ledgers grandes y varias iniciativas activas.
- [ ] Sin «Journal: incomplete» ni rutas absolutas en el bloque.

### T-08 — Vía rápida con qa-gate y TDD verificados

- **Estado**: borrador
- **Descripción**: H-15 y H-16. El implementer acepta el ledger ligero; qa acepta `test-plan: n/a (sin UI)` en `tasks.md`; la Lente A comprueba `RED:`/`TDD n/a` con `tdd: true`.
- **Archivos**: `agents/implementer.md`, `agents/qa.md`, `agent-kits/qa/coverage-check.py`, `tests/test_coverage_check.py`, `skills/adversarial-review/references/lens-prompts.md`, `skills/tdd/SKILL.md`, `commands/dev-cycle.md`, `skills/quick-implement/SKILL.md`, `interop/**`, `tests/test_dev_cycle_split.py`, `tests/fixtures/dev-cycle-modular-replacements.json`, `tests/fixtures/dev-cycle-paragraphs.json`.
- **Verificación**: `coverage-check` con el marcador en `tasks.md` → exit 0 explícito; tests de split y de interop pasan.

**Criterios de aceptación**
- [ ] La vía rápida tiene un camino de QA ejecutable.
- [ ] La Lente A comprueba la evidencia TDD.

### T-09 — Dashboards completos con roadmaps grandes

- **Estado**: borrador
- **Descripción**: H-17 a H-20. Cartera y progreso de la más nueva a la más antigua y con aviso honesto; progreso por cabecera, sin leer el ledger entero; planes con ledger > 256 KiB operables desde la consola; un plan nuevo no da 404; errores mapeados en la UI.
- **Archivos**: `skills/plugin-panel/scripts/panel_data.py`, `skills/plugin-panel/scripts/serve_panel.py`, `skills/plugin-panel/scripts/console_service.py`, `skills/plugin-panel/assets/control-center.js`, `skills/plugin-panel/assets/page-iniciativas.js`, `tests/test_panel_*.py`, `tests/test_console_*.py`.
- **Verificación**: tests del panel y de la consola con 70 iniciativas y ledgers > 256 KiB → pasan.

**Criterios de aceptación**
- [ ] Las iniciativas más nuevas nunca se recortan antes que las antiguas.
- [ ] Un ledger > 256 KiB se puede continuar y revisar desde la consola.

### T-10 — Índice de sesión por prioridad

- **Estado**: borrador
- **Descripción**: H-21 y menor de BOM. El índice ordena por prioridad de ciclo y lee `dev.json` con `utf-8-sig`.
- **Archivos**: `agent-kits/shared/skill-index.py`, `agent-kits/shared/test_skill_index.py`.
- **Verificación**: el índice de este repo muestra planner, qa, reviewer, tdd y `/setup` dentro del tope de 3.500 caracteres.

**Criterios de aceptación**
- [ ] Las piezas del ciclo aparecen antes que las opcionales.
- [ ] `dev.json` con BOM respeta `sesion.indice: false`.

### T-11 — Un solo troceo del ledger

- **Estado**: borrador
- **Descripción**: H-22, H-23, H-26 y menores de ledger-lint. `scope-check`, `coverage-check` y `jira-flow` usan el troceo de `ledger-lint` (bloques de código y secciones posteriores fuera); resumen dentro de bloques de código ignorado; vocabulario de `estado` validado a nivel ledger.
- **Archivos**: `agent-kits/shared/ledger-lint.py`, `agent-kits/shared/scope-check.py`, `agent-kits/qa/coverage-check.py`, `skills/jira-sync/scripts/jira-flow.py`, sus tests, `agent-kits/shared/copias.json`.
- **Verificación**: casos con bloques de código en `tasks.md` para los cuatro scripts → pasan; los 67 ledgers del repo siguen dando exit 0.

**Criterios de aceptación**
- [ ] Un `Archivos` o `### T-XX` dentro de un bloque de código no cuenta.
- [ ] La Verificación en sub-lista llega entera a Jira.

### T-12 — Bucle de revisión y dueño del commit

- **Estado**: borrador
- **Descripción**: H-24 y H-25. «Seguir» tras el 3.er intento abre un ciclo nuevo con OK del usuario; un solo dueño del commit.
- **Archivos**: `commands/dev-cycle.md`, `agents/implementer.md`, `skills/adversarial-review/SKILL.md`, `agent-kits/shared/ledger-write.py`, `agent-kits/shared/test_ledger_write.py`, `interop/**`, `tests/fixtures/dev-cycle-modular-replacements.json`.
- **Verificación**: test del writer con ciclo nuevo → pasa; interop al día.

**Criterios de aceptación**
- [ ] El camino de «seguir» es ejecutable con el writer.
- [ ] El commit tiene un único dueño y procedimiento.

## Fase 3 — Rendimiento de procesos

**Estado**: borrador

### T-13 — SessionStart en una pasada

- **Estado**: borrador
- **Descripción**: H-28 y H-40. Una sola instantánea del roadmap por arranque; `usage-state.json` sin `offsets` en marcadores cerrados.
- **Archivos**: `hooks/session-context.py`, `agent-kits/shared/progress-report.py`, `agent-kits/shared/usage-meter.py`, sus tests.
- **Verificación**: medida antes y después sobre este repo (`testing/perf.md`); misma salida.

**Criterios de aceptación**
- [ ] Cada ledger se lee una vez por arranque.
- [ ] Salida idéntica a la anterior salvo las mejoras de T-07.

### T-14 — Menos procesos por hook

- **Estado**: borrador
- **Descripción**: H-29, H-30 y H-31. Sin el Python de limpieza cuando el job ya está vacío; SubagentStop en Python con debounce; captura de UserPromptSubmit con un módulo ligero.
- **Archivos**: `hooks/run-hook.mjs`, `hooks/runtime-supervisor.py`, `hooks/subagent-progress.sh`, `hooks/subagent-progress.py`, `hooks/hooks.json`, `agent-kits/shared/journal-capture.py`, `agent-kits/shared/journal.py`, `interop/**`, tests de hooks.
- **Verificación**: medidas antes y después en `testing/perf.md`; `tests/test_hooks_shell.py` y las suites de hooks pasan.

**Criterios de aceptación**
- [ ] SubagentStop baja de ~9 procesos a ≤ 3.
- [ ] La captura no importa `journal.py`.

### T-15 — Panel y consola sin bloqueos

- **Estado**: borrador
- **Descripción**: H-32, H-33, H-34 y menores. Panel servido con hilos acotados y progreso con caché por firma; `native-sessions` solo en Sesiones o a demanda; `runtimes` con caché; plazo en `leerResumen`.
- **Archivos**: `skills/plugin-panel/scripts/serve_panel.py`, `skills/plugin-panel/scripts/console_service.py`, `skills/plugin-panel/scripts/console_common.py`, `skills/plugin-panel/assets/*.js`, tests del panel y de la consola.
- **Verificación**: sonda en vivo antes y después (`testing/perf.md`); tests del panel y de la consola pasan.

**Criterios de aceptación**
- [ ] `runtimes` cacheado; `native-sessions` no relanza CLIs fuera de Sesiones.
- [ ] Una petición lenta no bloquea las demás.

### T-16 — Scripts de las puertas más rápidos

- **Estado**: borrador
- **Descripción**: H-35 a H-39. `isdir` por patrón en scope-check; ledger-archive y ledger-lint sin bucles carácter a carácter; `sin_comentario` con atajo; lint en proceso en task-brief; clave de caché de la statusline.
- **Archivos**: `agent-kits/shared/scope-check.py`, `agent-kits/shared/ledger-archive.py`, `agent-kits/shared/ledger-lint.py`, `skills/code-health/scripts/code-health.py`, `agent-kits/shared/task-brief.py`, `statusline/roadmap-statusline.sh`, sus tests.
- **Verificación**: tiempos antes y después en `testing/perf.md`; mismas salidas sobre los ledgers del repo.

**Criterios de aceptación**
- [ ] Salidas idénticas; tiempos medidos más bajos.

## Fase 4 — Consumo de tokens

**Estado**: borrador

### T-17 — Capacidades e integraciones una vez por ciclo

- **Estado**: borrador
- **Descripción**: H-41 y H-42. Si el ledger, el brief o el prompt ya traen las capacidades o «sin integraciones», el rol no lo recalcula.
- **Archivos**: `agents/*.md`, `agent-kits/shared/capability-check.md`, `agent-kits/shared/project-integrations.md`, `commands/dev-cycle.md`, `interop/**`, `tests/fixtures/dev-cycle-modular-replacements.json`.
- **Verificación**: tamaño de carga por despacho antes y después (`context-footprint.py`); interop al día.

**Criterios de aceptación**
- [ ] Un despacho con capacidades en el brief no lee `capability-check.md`.

### T-18 — Lo opcional fuera de la carga por defecto

- **Estado**: borrador
- **Descripción**: H-43, H-44 y H-49. Revisión visual del plan en su propia referencia; notas de `/doctor` en `docs/`; scope-check imprime su propio remedio.
- **Archivos**: `agent-kits/dev-cycle/references/phase2-planning.md`, `agent-kits/dev-cycle/references/phase2-plan-review.md`, `commands/doctor.md`, `docs/reference/doctor.md`, `agents/implementer.md`, `skills/adversarial-review/SKILL.md`, `agent-kits/shared/scope-check.py`, `interop/**`, tests de split y de plan-review.
- **Verificación**: `context-footprint.py` antes y después; tests de split y de recetas de plan-review pasan.

**Criterios de aceptación**
- [ ] El flujo completo y `/doctor` cargan menos texto por defecto con los mismos contratos.

### T-19 — Ruta del kit resuelta una vez

- **Estado**: borrador
- **Descripción**: H-45. SessionStart y el brief inyectan la ruta absoluta del bundle activo; las piezas la usan antes de buscar.
- **Archivos**: `hooks/session-context.py`, `agent-kits/shared/task-brief.py`, `agents/*.md`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `interop/**`, tests.
- **Verificación**: el bloque de sesión trae la ruta; test de resolución pasa.

**Criterios de aceptación**
- [ ] Un subagente sin `CLAUDE_PLUGIN_ROOT` no necesita `find`.

### T-20 — OpenCode e interop sin contexto repetido

- **Estado**: borrador
- **Descripción**: H-46 y H-47. La caché de contexto de OpenCode se invalida por firma; la línea de delegación solo en agentes que delegan.
- **Archivos**: `hooks/opencode-plugin.js`, `scripts/export-interop.py`, `interop/**`, `tests/test_export_interop.py`, tests del adaptador de OpenCode.
- **Verificación**: tests del adaptador y de interop pasan; `--check` al día.

**Criterios de aceptación**
- [ ] Sin reinyección mientras la firma no cambie.
- [ ] Ningún agente sin `Agent` recibe la instrucción de delegar.

### T-21 — Documentación alineada y menores

- **Estado**: borrador
- **Descripción**: Menores de la auditoría: Lente D en `dev-cycle`, `quick-implement` y CLAUDE.md; hooks globales y ADR-023 en CLAUDE.md; consola frente a panel servido; rutas de memoria que no viajan; shells muertos; degradación sin node; `release.py` (5 manifiestos, `.MANUAL-COPY` pendiente); cookie por puerto; mapa de errores y `aria-live` de la consola.
- **Archivos**: `CLAUDE.md`, `commands/*.md`, `skills/**/SKILL.md`, `docs/**`, `hooks/*.sh`, `scripts/release.py`, `skills/plugin-panel/**`, `interop/**`, tests afectados.
- **Verificación**: lint 0 errores, evals 0 errores, interop al día, CI completa en Linux verde.

**Criterios de aceptación**
- [ ] Los menores de la auditoría quedan corregidos o descartados con motivo en este ledger.
