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
| Fase 1 | 6 | 6 | 100.0% |
| Fase 2 | 6 | 6 | 100.0% |
| Fase 3 | 0 | 4 | 0.0% |
| Fase 4 | 0 | 5 | 0.0% |
| **TOTAL** | **12** | **21** | **57.1%** |

## Fase 1 — Seguridad y pérdida de datos

**Estado**: completado

### T-01 — worklog sin pérdida de datos

- **Estado**: completado
- **Descripción**: H-1 y H-2. Un estado ilegible o con BOM no se trata como vacío ni se sobrescribe; escritura atómica; fecha futura y horas negativas rechazadas.
- **Archivos**: `skills/jira-sync/scripts/worklog.py`, `tests/test_worklog.py`, `agent-kits/shared/usage-meter.py`, `agent-kits/shared/test_usage_meter.py` (añadidos en la revisión intento 1, gap 3: mismo defecto de estado ilegible tratado como vacío), `agent-kits/shared/doctor.py`, `agent-kits/shared/test_doctor.py`, `docs/agents/CONTRACTS.md` (revisión intento 2: ⚠️ de `/doctor` y contrato E7).
- **Verificación**: `python -m pytest -q tests/test_worklog.py` → todos pasan, con casos de BOM, JSON corrupto, fecha futura y horas negativas.
- **Changelog**: El worklog de Jira y la medición de uso ya no pierden su estado: con BOM se lee, ilegible detiene la escritura (usage-meter sale con exit 3) y se rechazan fechas y horas imposibles.
- **Cerrada**: 2026-11-09

**Criterios de aceptación**
- [x] `jira-state.json` con BOM se lee bien; corrupto → exit 2 sin escribir.
- [x] Escritura atómica (tmp + `os.replace`).
- [x] `--fecha` futura y horas negativas → exit 2.


RED: `tests/test_worklog.py (6 casos nuevos)` falló con 6 failed, 2 passed: BOM leido como vacio (bancoPendiente 0), corrupto/futura/negativas exit 0 con aplicado, raiz lista traceback exit 1, save_json sin os.replace · 2026-11-09.

GREEN: `python -m pytest -q tests/test_worklog.py` → `8 passed in 6.18s` (BOM, corrupto, raíz lista, ausente, os.replace, fecha futura/inválida, 6 flags negativos + 13 casos históricos); `test_jira_flow.py` → `74 passed` · 2026-11-09.


RED: `agent-kits/shared/test_usage_meter.py -k fix1 + tests/test_worklog.py -k fix1` falló con fix1: usage-meter 2 failed (BOM e ilegible tratados como vacio y sobrescritos); worklog 3 failed (nan/inf aceptados, tipos erroneos con traceback, PermissionError en os.replace sin reintento) · 2026-11-09.

GREEN fix1: `pytest tests/test_worklog.py` → `11 passed` (nan/inf, 7 formas de tipo equivocado sin traceback, reintento acotado de `os.replace` ante PermissionError); `pytest agent-kits/shared/test_usage_meter.py` → `80 passed` (BOM conserva marcadores; ilegible o raíz no objeto → start/close exit 3 sin escribir, status exit 0 con aviso; el test histórico de estado corrupto conserva el caso de marcador corrupto y los casos ilegibles pasan al test nuevo); `test_jira_flow.py` → `74 passed` · 2026-11-09.


RED: `tests/test_worklog.py -k fix2 + agent-kits/shared/test_doctor.py -k fix2` falló con fix2: 4 failed: tasks internos y numeros de config invalidos aceptados o con traceback, CONTRACTS.md promete exit 0 siempre, doctor ignora el aviso de usage-state ilegible · 2026-11-09.

GREEN fix2: `pytest tests/test_worklog.py` → `14 passed` (campos internos de `tasks` y números de `rates.json`/`jira.json` validados → exit 2; fila E7 de CONTRACTS con exit 3); `pytest agent-kits/shared/test_doctor.py` → `230 passed, 1 skipped` + el test nuevo en verde tras ajustar su aserción (`17 passed` con `-k "fix2 or marcador"`); `test_jira_flow.py` → `74 passed`. `doctor.py`/`usage-meter.py` sin huella `sha256_lf` · 2026-11-09.


RED: `test_doctor.py::test_fix3_doctor_distingue_estado_ilegible_de_marcador_corrupto + test_usage_meter.py::test_fix3_status_marca_solo_el_estado_ilegible_como_fatal` falló con fix3: 2 failed: un marcador corrupto descartado se presentaba como estado ilegible con arreglo de borrar y sin huerfanos; status no distingue el aviso fatal · 2026-11-09.

GREEN fix3: `pytest agent-kits/shared/test_doctor.py` → `232 passed, 1 skipped` (solo `estado_ilegible` es fatal; un marcador corrupto da ⚠️ «respáldalo y repara solo esa entrada», sin proponer borrar, y los huérfanos siguen saliendo); `pytest agent-kits/shared/test_usage_meter.py` → `81 passed` (`status` publica `estado_ilegible: true` solo con estado ilegible) · 2026-11-09.

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


RED: `tests/test_qa_gate.py::test_fix2_sin_ningun_passed_no_es_flaky_ni_se_justifica` falló con fix2: [failed, skipped] con expectedStatus skipped contado flaky y justificado -> VERDE sin haber pasado nunca · 2026-11-09.

GREEN fix2: `pytest tests/test_qa_gate.py` → `8 passed` (flaky exige al menos un `passed`); `python tests/test_qa_gate.py` → `13/13 OK` · 2026-11-09.


RED: `tests/test_qa_gate.py::test_fix3_flaky_es_el_resultado_esperado_tras_un_fallo` falló con fix3: [timedOut, failed] con expectedStatus failed contado unexpected (flaky exigia el literal passed) · 2026-11-09.

GREEN fix3: `pytest tests/test_qa_gate.py` → `9 passed` (flaky = resultado esperado tras un fallo; `[timedOut, failed]` con test.fail() es flaky justificable; `[failed, skipped]` sigue siendo fallo); `python tests/test_qa_gate.py` → `13/13 OK` · 2026-11-09.

### T-03 — Instalador robusto en Windows y con configuración ajena

- **Estado**: completado
- **Descripción**: H-4, H-9, H-10, H-11, H-13 y menores del instalador. Buscar las CLI sin el directorio actual; `merge` con lectura estricta; `uninstall` aislado por proveedor; enlaces solo prohibidos en lo que crea el instalador; aviso de rutas absolutas en configuración compartida; misma exclusión de tests desde un clon que en npm.
- **Archivos**: `install/install.mjs`, `install/providers.mjs`, `install/manifest-auth.mjs`, `tests/installer.test.mjs`, `tests/install-auth.test.mjs`, `docs/INSTALL.md`, `docs/en/INSTALL.md`, `agent-kits/shared/codex-plugin-state.mjs`, `tests/codex-plugin-state.test.mjs` (revisión intento 1, gap 10: resolvedor de `codex` de `install status`), `hooks/run-hook.mjs` (revisión intento 2, C8: `NoDefaultCurrentDirectoryInExePath`).
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


RED: `tests/installer.test.mjs --test-name-pattern=revision intento 1 + tests/codex-plugin-state.test.mjs relative PATH` falló con fix1: 3 fail: plugin no verificable bloquea la copy del mismo proveedor, correr exportado/sin error propio si la CLI falta, codex.cmd plantado resuelto via entrada relativa del PATH · 2026-11-09.

GREEN fix1: `node --test tests/installer.test.mjs` → `pass 184 · fail 0` (uninstall aislado por manifiesto; `correr` sin ruta real → ENOENT propio); `node --test tests/codex-plugin-state.test.mjs` → `pass 7 · fail 0` (entradas relativas del PATH ignoradas, el `codex.cmd` plantado no se ejecuta); `tests/install-auth.test.mjs` → `pass 7`; `tests/codex-native-install.test.mjs` → `pass 11`. `codex-plugin-state.mjs` sin huella `sha256_lf` · 2026-11-09.


RED: `installer.test.mjs C8 + codex-plugin-state.test.mjs NoDefaultCurrentDirectoryInExePath` falló con fix2: 3 fail: correr y runCodexQuery lanzan sin NoDefaultCurrentDirectoryInExePath (con el entorno limpio cmd.exe resolveria node.bat del proyecto); run-hook no lo fija · 2026-11-09.

GREEN fix2: `node --test tests/codex-plugin-state.test.mjs` → `pass 9 · fail 0` (con `node.bat` plantado en el cwd del proyecto y el shim llamando a `node` pelado, se ejecuta el node real); `node --test tests/installer.test.mjs` → `pass 184 · fail 1`: el que falla es «gap 8: una CLI colgada…» por tiempo (30906 ms frente al tope de 30000 ms con la máquina cargada); solo pasa en 15393 ms; el test C8 nuevo pasa. `node --test tests/hook-runtime.test.mjs` → `pass 25`; `export-interop.py` → sin cambios de contenido · 2026-11-09.


RED: `tests/codex-plugin-state.test.mjs: run-hook candidates ignore relative PATH entries` falló con fix3: 1 fail: candidates() de run-hook acepta entradas relativas del PATH (sin filtro de absolutas) · 2026-11-09.

GREEN fix3: `node --test tests/codex-plugin-state.test.mjs` → `pass 10 · fail 0` (`candidates()` de `hooks/run-hook.mjs` ignora entradas vacías o relativas del PATH); `node --test tests/hook-runtime.test.mjs` → `pass 25 · fail 0`. Nota de evidencia (A2): `tests/installer.test.mjs:1909` «gap 8: una CLI colgada…» tiene tope 30000 ms y depende de la carga de la máquina (30906 ms en la pasada completa con la máquina cargada); aislado pasa en 17336 ms (`node --test --test-name-pattern="gap 8: una CLI colgada" tests/installer.test.mjs` → `✔`). El tope no se ha relajado; el resto de `installer.test.mjs` (184) pasó en la pasada de fix2 · 2026-11-09.

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
- **Archivos**: `commands/dev-cycle.md`, `agent-kits/dev-cycle/references/phase3-subagents.md`, `skills/quick-implement/SKILL.md`, `agent-kits/shared/task-brief.py`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `interop/**`, `tests/test_dev_cycle_split.py`, `tests/fixtures/dev-cycle-modular-replacements.json`, `tests/fixtures/dev-cycle-paragraphs.json`, `tests/test_native_guardrail_dispatch.py`, `docs/agents/CONTRACTS.md`, `docs/guides/quality-playbook.md`, `docs/guides/subscription-efficiency.md` (añadidos por el implementer: E3, también describían «lite en el hilo actual»), `docs/agents/implementer.md`, `agent-kits/shared/README.md` (revisión intento 1, gap 4), `commands/setup.md` (revisión intento 2, A1).
- **Verificación**: test que exige el despacho a `implementer` en lite y subagentes → pasa; `export-interop.py --check` al día; ahorro de la vía rápida ≥ 6000.
- **Changelog**: La implementación se entrega siempre a la identidad nativa del implementer, también en el perfil lite y con subagentes, para que su guardia de rama, alcance y git aplique.
- **Notas**: Deuda (orquestador, 2026-11-09): los manuales `docs/guides/subscription-efficiency.md` y `docs/guides/quality-playbook.md` (edición 2026-11-04) siguen diciendo que lite implementa en el hilo actual; requiere una nueva edición PDF (sus PDF de `output/pdf/` están atados a esa edición). Seguimiento en T-21.
- **Cerrada**: 2026-11-09

**Criterios de aceptación**
- [x] `lite` implementa con `implementer` en secuencia, no en el hilo principal.
- [x] El modo subagentes despacha `implementer` con el brief.


RED: `tests/test_native_guardrail_dispatch.py` falló con 5 failed, 1 passed: lite dice implementa en el hilo actual, paso 2 sin subagent_type implementer, brief lite y docs con hilo actual/current thread, interop sin native-roles.json · 2026-11-09.

GREEN: `pytest tests/test_native_guardrail_dispatch.py` → `6 passed`; `tests/test_dev_cycle_split.py` → `10 passed` (ahorro vía rápida 6012 → 6057: la frase de justificación de la vía rápida se condensa en su conclusión; filas de reemplazo registradas, incl. la encadenada `2ece9f09`→nuevo); `export-interop.py` → `92 ficheros escritos` y `--check` → `92 ficheros al día`; `tests/test_lite_profile.py` 30 passed; `test_token_estimates.py` 13 passed; `agent-kits/shared/test_context_footprint.py` 15 passed; `test_source_snapshot.py` 33 passed, 1 skipped; `test_task_brief.py` 92 passed. `skills/quick-implement/SKILL.md` no cambia (ya despachaba a `implementer`) · 2026-11-09.


RED: `tests/test_native_guardrail_dispatch.py (DOCS ampliada + respaldo copiado)` falló con fix1: 2 failed: docs/agents/implementer.md y shared README dicen hilo actual; sin respaldo implementer en instalacion copiada · 2026-11-09.

GREEN fix1: `pytest tests/test_native_guardrail_dispatch.py` → `7 passed` (DOCS incluye docs/agents/implementer.md y shared README; respaldo `implementer` con bundle copiado); `tests/test_dev_cycle_split.py` → `10 passed`, ahorro vía rápida 6055 (≥ 6000; la frase duplicada «La política efectiva prevalece…» se integra en «Consume sus flags efectivos»); `tests/test_lite_profile.py` → `30 passed`; `export-interop.py --check` → `92 ficheros al día` · 2026-11-09.


RED: `tests/test_native_guardrail_dispatch.py::test_docs_describen_lite_con_implementer_nativo (DOCS + commands/setup.md)` falló con fix2: 1 failed: commands/setup.md dice que lite ejecuta implementacion en el hilo actual · 2026-11-09.

GREEN fix2: `pytest tests/test_native_guardrail_dispatch.py` → `10 passed` (`commands/setup.md` en `DOCS`; tests dedicados de los gaps 5, 6 y 12 del intento 1); interop regenerado (`setup` en Codex y OpenCode) · 2026-11-09.

### T-06 — Puertas que fallan cerradas

- **Estado**: completado
- **Descripción**: H-8 y H-12. `review-lens-select` en `auto` activa C y D ante error; `guardrail-check` deniega `reset --hard`, `clean -f*`, borrar ramas remotas y `stash drop|clear`.
- **Archivos**: `skills/adversarial-review/scripts/review-lens-select.py`, `skills/adversarial-review/scripts/test_review_lens_select.py`, `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/test_guardrail_check.py`, `skills/adversarial-review/SKILL.md`, `tests/test_graphiti_security.py`, `CHANGELOG.md`, `CHANGELOG.es.md` (añadidos por el implementer: entrada `### Fixed` de toda la Fase 1, commit aparte pedido por el orquestador), `skills/adversarial-review/references/lens-c-heuristics.md`, `agents/implementer.md`, `docs/agents/implementer.md`, `interop/**` (revisión intento 1, gaps 5 y 6), `agent-kits/shared/test_git_verification.py` (revisión intento 2: sus casos «permitidos» de `GIT_CONFIG_*` y de `--no-v` ambiguo pasan a denegados por el cierre por diseño)), `docs/FLOWS.md`, `docs/en/FLOWS.md`, `tests/test_native_guardrail_dispatch.py` (revisión intento 3: contrato final de la regla git y límite «no es un sandbox».
- **Verificación**: tests de los dos scripts → pasan con los casos nuevos.
- **Changelog**: Las puertas fallan cerradas: si no se puede evaluar el diff se activan las lentes de seguridad y rendimiento, y el implementer ya no puede descartar cambios, borrar ramas remotas ni vaciar stashes.
- **Cerrada**: 2026-11-09

**Criterios de aceptación**
- [x] `--base` inexistente en `auto` → `lente_c` y `lente_d` true con aviso.
- [x] Las seis operaciones destructivas se deniegan para el implementer.


RED: `test_review_lens_select.py::test_error_en_auto_activa_c_y_d_con_aviso_exit_0 + test_guardrail_check.py::test_git_deny_operaciones_destructivas_auditoria` falló con --base inexistente en auto dio lente_c False; 17 failed: reset --hard, clean -f*, push :rama/--delete/-d y stash drop/clear permitidos · 2026-11-09.

GREEN: `pytest skills/adversarial-review/scripts/test_review_lens_select.py` → `61 passed in 126.89s`; `pytest agent-kits/shared/test_guardrail_check.py` → `158 passed in 7.43s` (18 destructivas deny + 16 no destructivas allow); `tests/test_copias_declaradas.py` → `30 passed`. Ninguno de los dos scripts tiene huella `sha256_lf` · 2026-11-09.


RED: `agent-kits/shared/test_guardrail_check.py -k fix1_formas` falló con fix1: 23 failed: --ha/--fo/--del/--mirror/--prune, clean.requireForce en linea y -c alias.* permitidos; clean --dr -f denegado · 2026-11-09.

GREEN fix1: `pytest agent-kits/shared/test_guardrail_check.py` → `190 passed` (abreviaturas `--ha/--fo/--del/--mir/--pru`, `--mirror`/`--prune`, `clean.requireForce` por `-c`, `--config-env`, `GIT_CONFIG_*`, cualquier `-c alias.*`; siguen permitidos `reset --soft`, `stash list`, `push origin rama`, `push -u`, `clean -n`/`--dr -f`); `pytest skills/adversarial-review/scripts/test_review_lens_select.py` → `62 passed in 185.50s` (`.git` roto → C y D true con aviso); docstring y `lens-c-heuristics.md` alineados; lista de `agents/implementer.md`/`docs/agents/implementer.md` ampliada; `export-interop.py --check` → `92 ficheros al día` · 2026-11-09.


RED: `agent-kits/shared/test_guardrail_check.py -k fix2` falló con fix2: 42 failed: prefijos cortos (--h, --m, --force-w), clean -fn/-fen y --no-dry-run, --attr-source y globales desconocidas, include.*, GIT_CONFIG_* sin distinguir mayusculas y por export/set, git config de alias, branch -df/-d -f, requireForce=true denegado · 2026-11-09.

GREEN fix2: `pytest agent-kits/shared/test_guardrail_check.py` → `277 passed` (cualquier prefijo de opción destructiva, clean con `-n` exacto o `--dry-run` sin `--no-dry-run`, globales `--attr-source`/`--super-prefix`/`--list-cmds` y desconocidas, `-c`/`--config-env` con alias/include/includeif o requireForce falso, `GIT_CONFIG_*` sin distinguir mayúsculas en prefijo/env/export/set, `git config` que escribe esas claves, `branch -df/-d -f/--del --forc`; legítimas permitidas); `test_git_verification.py` → `357 passed`; `test_native_guardrail.py` → `227 passed` · 2026-11-09.

GREEN fix2 (changelog): `pytest tests/test_native_guardrail_dispatch.py` → `11 passed` (`test_fix2_changelog_de_fase_1_recoge_los_cambios_del_intento_2`; en HEAD las marcas `exit 3`/`NoDefaultCurrentDirectoryInExePath` daban 0 coincidencias) · 2026-11-09.


RED: `agent-kits/shared/test_guardrail_check.py -k fix3 (+ casos ajustados de fix2)` falló con fix3: 55 failed: -c fuera de lista blanca (core.editor, sshCommand, pager...) permitido, git config --comment/--rename-section/--file mal clasificado, GIT_EDITOR/GIT_SSH/HOME con git permitidos y export sin git denegado, clean -fn/-nf falso positivo y -e/-- sin analizar, push -4f, branch -f/-M/-C y update-ref -d permitidos · 2026-11-09.


RED: `agent-kits/shared/test_guardrail_check.py::test_fix3_gap8_docs_describen_lista_blanca_y_que_no_es_sandbox` falló con fix3: 1 failed: docs sin la lista blanca ni el limite de no ser un sandbox · 2026-11-09.

TDD n/a (intento 2, gaps 13 y 14): `test_fix2_gap5_*`, `test_fix2_gap6_*`, `test_fix2_gap12_*` y `test_fix2_changelog_de_fase_1_recoge_los_cambios_del_intento_2` se escribieron sobre texto ya corregido; son tests de regresión del texto, sin rojo observado en el momento (solo el contraste con HEAD del CHANGELOG) · 2026-11-09.

GREEN fix3: `pytest agent-kits/shared/test_guardrail_check.py` → `372 passed` (lista blanca de `-c`/`--config-env`/`git config`, clasificación lectura/escritura con `--comment`/`--file`/secciones, `GIT_*`/`HOME`/`XDG_CONFIG_HOME` solo con git, `clean` analizado de verdad con `-fn`/`-nf` como simulación y `-fen`/`-e -n -f`/`-f -- -n` denegados, `push -4f`, `branch -f|-M|-C`, `update-ref -d|--stdin`, globales legítimas permitidas, test de documentación gap 8); `test_git_verification.py` → `357 passed`; `test_native_guardrail.py` → `227 passed`; `tests/test_native_guardrail_dispatch.py` → `11 passed` (gap6 alineado con la lista blanca); `_env_hooks_override` eliminado (subsumido por la regla de entorno) · 2026-11-09.

GREEN fix3 (changelog): `pytest tests/test_native_guardrail_dispatch.py` → `12 passed` (`test_fix3_changelog_describe_la_lista_blanca_y_el_limite`; en HEAD la sección no nombraba `commit.gpgsign` ni `sandbox`: 0 coincidencias) · 2026-11-09.


RED: `agent-kits/shared/test_guardrail_check.py::test_fix3b_commit_gpgsign_solo_con_valor_verdadero` falló con fix3b: 11 failed: commit.gpgsign falso, vacio, sin valor o por --config-env (y git config que lo escribe a falso) permitido, desactiva la firma de commits · 2026-11-09.

GREEN fix3b: `.venv/Scripts/python -m pytest -q agent-kits/shared/test_guardrail_check.py` → `391 passed in 7.53s` (`commit.gpgsign` solo con valor verdadero; falso, vacío, sin valor, `--config-env` y escrituras de `git config` a falso → deny); `test_git_verification.py` → `357 passed` (su caso permitido pasa a `commit.gpgsign=true`); `tests/test_native_guardrail_dispatch.py` → `13 passed` (docs y CHANGELOG lo aclaran; en HEAD 0 coincidencias) · 2026-11-09.

## Fase 2 — Funciones documentadas que no funcionan

**Estado**: en-revision

### T-07 — Retoma de sesión: journal y bloque útil

- **Estado**: completado
- **Descripción**: H-14, H-27 y H-48. Reinyectar la última entrada del journal sin depender de la selección global de ledgers; iniciativa en curso primero en memoria; líneas opacas fuera; iniciativas al 100 % compactadas; pie sin ruta absoluta; `clear` también en Claude.
- **Archivos**: `agent-kits/shared/progress-report.py`, `hooks/session-context.py`, `hooks/hooks.json`, `agent-kits/shared/test_progress_report.py`, `tests/test_session_context.py`, `tests/test_hooks_shell.py`, `interop/**`, `docs/observability.md`, `docs/en/observability.md`, `hooks/session-context.sh` (oráculo de bytes del compositor nativo: mismo pie y mismo orden de memoria), `agent-kits/shared/test_work_resume.py` (casos H-14/H-48 del historial del arranque), `tests/test_graphiti_security.py` (huella `sha256_lf` de `hooks/session-context.py`), `docs/WORK-RESUME.md`, `docs/en/WORK-RESUME.md`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md` (E3: describían la selección del historial al arrancar) (añadidos por el implementer), `agent-kits/shared/journal.py` (revisión intento 1, B1: el escritor usa la misma regla que el lector), `agent-kits/shared/README.md`, `skills/plugin-dev/references/claude-code-contracts.md` (revisión intento 1, A5: matcher con `clear`).
- **Tiempo IA (ejec.)**: real 0,77h (medido)
- **Verificación**: test con más de 1 MiB de ledgers y dos iniciativas activas → se reinyecta la entrada del journal; tests de sesión existentes pasan.
- **Changelog**: Al arrancar o retomar se vuelve a citar la última entrada del journal aunque haya varias iniciativas activas o ledgers grandes, y el bloque de sesión agrupa las iniciativas al 100 % pendientes de `/retro`, sin líneas opacas ni rutas absolutas; `/clear` también reinyecta el contexto en Claude Code.
- **Cerrada**: 2026-11-09

**Criterios de aceptación**
- [x] El journal se reinyecta con ledgers grandes y varias iniciativas activas.
- [x] Sin «Journal: incomplete» ni rutas absolutas en el bloque.


RED: `test_work_resume.py -k 'h14 or h48' + test_progress_report.py -k h48 + tests/test_session_context.py -k 'h14 or h27 or h48'` falló con 12 failed: history-only imprime Journal: incomplete con mas de 1 MiB de ledgers y Journal: ambiguous con dos activas; sin compactar las de 100 %; Revisiones: seleccion de iniciativa incomplete; memoria consulta por orden de carpeta; pie con ruta absoluta; matcher SessionStart sin clear · 2026-11-09.

GREEN: `pytest agent-kits/shared/test_progress_report.py agent-kits/shared/test_work_resume.py` → `96 passed`; `pytest tests/test_session_context.py` → `44 passed in 283.90s` (incl. equivalencia de bytes nativo/shell); `pytest tests/test_hooks_shell.py -k "memoria or tope or activas or h14"` → `13 passed`; `pytest tests/test_graphiti_security.py` → `126 passed` (huella nueva; el pie ya no cita una ruta que el cierre no resuelve); `test_review_resume.py` 18 passed, `test_resume_curation.py` 25 passed, `test_source_snapshot.py` 33 passed 1 skipped, `test_context_footprint.py` 15 passed, `test_roadmap_index.py` 71 passed; `export-interop.py --check` → `92 ficheros al día`. En este repo el bloque ya trae el journal y compacta 3 iniciativas al 100 %. Decisiones: con varias activas o más de 1 MiB de ledgers el arranque cita la iniciativa en curso (marcador abierto o ledger más reciente) y nunca una no activa (cambia el contrato anterior «ambigua → nada»; `/work-resume` conserva la ambigüedad explícita); un fallo de selección no deja línea; el pie nombra `knowledge-find.py` y `$SHAREDKIT` sin ruta; `clear` reinyecta índice, progreso y memoria, no el journal · 2026-11-09.


RED: `test_work_resume.py + test_progress_report.py + tests/test_session_context.py -k fix1` falló con fix1: 9 failed: el escritor del journal etiqueta otra iniciativa que el lector (B1, sin iniciativa_vigente comun); seleccion por escaneo completo sin tope (C2) y usage-state releido (D1); Ledger canonico apunta a la de 100 % (B4) y memoria agrupa por pct redondeado; revisiones omitidas sin aviso con ledger grande (B5); memoria vacia si la en curso no tiene aciertos; matcher sin clear en 5 documentos (A5) · 2026-11-09.

GREEN fix1: `pytest agent-kits/shared/test_work_resume.py` → `59 passed` (B1: el escritor real `journal.py write` etiqueta `gamma`, la en curso pendiente, y el lector la cita; con marcador abierto ambos eligen `beta`; C2: `iniciativa_vigente` no llama a `activas()` y resuelve un ledger de ~330 KiB por su cabecera acotada; D1: `usage-state.json` se lee una vez por proceso si no cambia); `agent-kits/shared/test_progress_report.py` → `43 passed` (B4: «Ledger canónico» y la vigente son la pendiente aunque la de 100 % sea más reciente; B5: «Revisiones omitidas: ledger > 256 KiB; /work-resume --initiative …»); `tests/test_session_context.py` → `46 passed` + la equivalencia `replay-codex` falló una vez por tiempos y pasó al repetirla (`-k "matches_shell_bytes and replay"` → 3 passed); casos fix1: memoria por `completadas == total`, memoria que consulta más iniciativas si las primeras no traen aciertos, ningún documento con el matcher sin `clear`; `test_journal.py` 192 passed + 10 skipped, `test_review_resume.py` 18, `test_resume_curation.py` 25, `tests/test_graphiti_security.py` 126 passed (huella nueva de `session-context.py`). En este repo la vigente es `plugin-audit-remediation` y el bloque de memoria sale con 2 aciertos; el historial no sale porque las entradas existentes se etiquetaron con la regla vieja (primera alfabética), no por un fallo de selección · 2026-11-09.

### T-08 — Vía rápida con qa-gate y TDD verificados

- **Estado**: completado
- **Descripción**: H-15 y H-16. El implementer acepta el ledger ligero; qa acepta `test-plan: n/a (sin UI)` en `tasks.md`; la Lente A comprueba `RED:`/`TDD n/a` con `tdd: true`.
- **Archivos**: `agents/implementer.md`, `agents/qa.md`, `agent-kits/qa/coverage-check.py`, `tests/test_coverage_check.py`, `tests/test_quick_path_gates.py` (añadido por el implementer: contratos de prosa H-15/H-16 y resolución en Codex), `skills/adversarial-review/references/lens-prompts.md`, `skills/tdd/SKILL.md`, `commands/dev-cycle.md`, `skills/quick-implement/SKILL.md`, `interop/**`, `tests/test_dev_cycle_split.py`, `tests/fixtures/dev-cycle-modular-replacements.json`, `tests/fixtures/dev-cycle-paragraphs.json`, `tests/test_native_guardrail_dispatch.py` (añadido por el implementer: los dos manuales con edición PDF revertidos por el orquestador pasan a deuda vigilada T-05 → T-21), `docs/agents/CONTRACTS.md`, `docs/agents/qa.md` (revisión intento 1, A4: decían que el marcador solo vale en `improvement-plan.md`).
- **Tiempo IA (ejec.)**: real 0,07h (medido)
- **Verificación**: `coverage-check` con el marcador en `tasks.md` → exit 0 explícito; tests de split y de interop pasan.
- **Changelog**: La vía rápida de `/dev-cycle` ya puede cerrar QA: el ledger ligero declara «sin UI» y qa lo acepta, el implementer trabaja sin `improvement-plan.md`, la Lente A exige la evidencia del rojo con TDD activo y quick-implement encuentra el método también en Codex.
- **Cerrada**: 2026-11-09

**Criterios de aceptación**
- [x] La vía rápida tiene un camino de QA ejecutable.
- [x] La Lente A comprueba la evidencia TDD.


RED: `tests/test_coverage_check.py (escenario_h15) + tests/test_quick_path_gates.py` falló con coverage-check con el marcador en tasks.md sin improvement-plan.md sale exit 1; 6 failed: implementer exige el plan, qa y dev-cycle solo leen el marcador del plan, la Lente A no pide RED:, tdd cita una comprobacion inexistente, quick-implement en Codex resuelve commands/dev-cycle.md inexistente · 2026-11-09.

GREEN: `python tests/test_coverage_check.py` → `OK … todo pasa` (marcador en el frontmatter de `tasks.md` sin plan → exit 0 con «declarado en tasks.md»; en la prosa no exime; el del plan sigue mandando); `pytest tests/test_quick_path_gates.py` → `6 passed` (implementer, qa, dev-cycle, Lente A criterio (5b), tdd y la receta de quick-implement ejecutada en Bash con un plugin de Codex sin `commands/` → resuelve `interop/codex/command-skills/custom-agents-dev-cycle/references/command.md`); `tests/test_dev_cycle_split.py` → `10 passed`, ahorro de la vía rápida 6055 → 6080 (preámbulo histórico de quick-implement condensado; 4 filas de reemplazo registradas); `test_skill_size.py` 37, `test_context_footprint.py` 15, `test_source_snapshot.py` 33 + 1 skipped, `test_native_guardrail_dispatch.py` 14, `test_user_handbooks.py` 4, `test_npm_payload.py` 5 passed; `lint_plugin.py` 0 errores; `evals/check.py` 0 errores; `export-interop.py --check` → `92 ficheros al día`. Fuera de alcance: el aviso de ledger-lint para `RED:` que proponía la auditoría (ledger-lint no lee `dev.json`); la comprobación queda en la Lente A · 2026-11-09.


RED: `tests/test_quick_path_gates.py -k fix1` falló con fix1: 3 failed: la via rapida con UI no tiene camino de QA (A3); CONTRACTS E1, docs/agents/qa.md, qa P1 e implementer P1 solo hablan de improvement-plan.md (A4); sin deuda del aviso de ledger-lint sin RED (A2) · 2026-11-09.

GREEN fix1: `pytest tests/test_quick_path_gates.py` → `9 passed` (A3: un cambio con interfaz va al flujo completo, en el filtro de quick-implement y en la vía rápida de `/dev-cycle`; A4: CONTRACTS E1, `docs/agents/qa.md`, P1 de qa y del implementer nombran el `tasks.md` ligero; A2: el aviso de ledger-lint sin `RED:` queda como deuda en T-21); `tests/test_dev_cycle_split.py` → `10 passed`, ahorro de la vía rápida 6231 → 6189 (2 filas de reemplazo); `test_skill_size.py` 37, `test_context_footprint.py` 15, `test_source_snapshot.py` 33 + 1 skipped; `export-interop.py --check` → `92 ficheros al día` · 2026-11-09.

### T-09 — Dashboards completos con roadmaps grandes

- **Estado**: completado
- **Descripción**: H-17 a H-20. Cartera y progreso de la más nueva a la más antigua y con aviso honesto; progreso por cabecera, sin leer el ledger entero; planes con ledger > 256 KiB operables desde la consola; un plan nuevo no da 404; errores mapeados en la UI.
- **Archivos**: `skills/plugin-panel/scripts/panel_data.py`, `skills/plugin-panel/scripts/serve_panel.py`, `skills/plugin-panel/scripts/console_service.py`, `skills/plugin-panel/assets/control-center.js`, `skills/plugin-panel/assets/page-iniciativas.js`, `tests/test_panel_*.py`, `tests/test_console_*.py`, `agent-kits/shared/local-read.py` (lectura acotada de un prefijo para la cabecera de un ledger grande), `skills/plugin-panel/assets/panel-live.js` (valida y rotula `fuente: resumen`), `tests/test_control_center_http.py` (su contrato «sin improvement-plan.md → 503» pasa a la vía rápida operable) (añadidos por el implementer).
- **Tiempo IA (ejec.)**: real 0,28h (medido)
- **Verificación**: tests del panel y de la consola con 70 iniciativas y ledgers > 256 KiB → pasan.
- **Changelog**: Los paneles muestran primero las iniciativas más recientes y dicen cuántas antiguas quedan fuera; el progreso de ledgers grandes sale de su resumen en vez de marcarse como demasiado grande, la consola puede continuar o revisar planes grandes o de vía rápida, y un plan creado con el panel abierto ya tiene página.
- **Cerrada**: 2026-11-09

**Criterios de aceptación**
- [x] Las iniciativas más nuevas nunca se recortan antes que las antiguas.
- [x] Un ledger > 256 KiB se puede continuar y revisar desde la consola.


RED: `tests/test_panel_large_roadmaps.py` falló con 7 failed: con 70 iniciativas la cartera pierde las 6 mas nuevas y no dice el recorte; progreso con 12 ledgers de 200 KiB da too_large falso; prepare de un plan sin improvement-plan.md da plan_source_unavailable y con ledger de 330 KiB plan_unavailable; la UI no mapea esos errores; un plan creado tras arrancar no tiene pagina · 2026-11-09.

GREEN: `pytest tests/test_panel_large_roadmaps.py` → `8 passed` (70 iniciativas: se recortan las 6 más antiguas y `recorte` lo dice, con aviso en Iniciativas; 12 ledgers de ~200 KiB sin `too_large` falso, de la más nueva a la más antigua y los que no caben con `fuente: resumen` desde su cabecera; `prepare` continúa y revisa un plan de vía rápida sin `improvement-plan.md` y uno de ~330 KiB; errores `plan_*` mapeados en la consola; un plan creado tras arrancar se sirve por HTTP con su `api/plan-<id>`; el test HTTP de H-20 se añadió tras el arreglo, sin rojo propio: el rojo de H-20 es el de `plan_page_path`); `test_panel_server.py` → `137 passed, 2 skipped` (contrato de filas con `fuente`; presupuesto: 1 MiB de ledgers enteros + cabeceras de 16 KiB acotadas); `test_control_center_http.py` → `21 passed` (sin `improvement-plan.md` → 200, sin `tasks.md` → error); `test_panel_data.py` 17, `test_panel_contract_golden.py` 6, `test_panel_iniciativas_ui.py` 20, `test_panel_live_ui.py` 32, `test_panel_plan_ui.py` 124, `test_panel_pages.py` 32, `test_panel_export.py` 31+1s, `test_panel_fix1..4` 33+1s/18/8/14, `test_console_service.py` 5, `test_audit_console.py` 8, `test_code_receipts.py` 88, `test_console_encoding.py` 744 (serve_panel.py vuelve a ser ASCII), `test_local_read.py` 70+6s, `test_local_read_stability.py` 24, `test_source_snapshot.py` 33+1s passed. Decisión: la huella de la consola usa `read_bytes` con tope de 16 MiB, no un hash en streaming; queda como límite declarado · 2026-11-09.


RED: `tests/test_panel_large_roadmaps.py -k fix1` falló con fix1: con 140 carpetas list_names corta en orden de scandir y la cartera pierde las mas nuevas (B2); list_names sin newest_first; una linea de resumen con 20000 espacios bloquea progress_snapshot mas de 600 s y la ejecucion la corta el timeout (C1) · 2026-11-09.

GREEN fix1: `pytest tests/test_panel_large_roadmaps.py` → `11 passed` (B2: con 140 carpetas la cartera conserva las 10 más nuevas, `recorte.omitidas` = 140 − mostradas sin contar una carpeta con fecha que no es iniciativa, y el progreso empieza por la 139; `list_names(newest_first=True)` lee hasta 4.096 nombres, ordena y después corta; C1: una fila de resumen con 20.000 espacios se procesa en menos de 5 s —antes el `timeout` de 600 s cortó la ejecución— porque `_header_summary` delega en `progress-report.resumir_cabecera`, que separa celdas con `split`); `test_local_read.py` 70 + 6 skipped, `test_local_read_stability.py` 24, `tests/test_panel_server.py` 137 + 2 skipped, `test_panel_data.py` 17, `test_panel_contract_golden.py` 6, `test_control_center_http.py` 21, `test_console_service.py` 5, `test_panel_plan_ui.py` 124, `test_progress_report.py` 43, `test_work_resume.py` 59 passed · 2026-11-09.

### T-10 — Índice de sesión por prioridad

- **Estado**: completado
- **Descripción**: H-21 y menor de BOM. El índice ordena por prioridad de ciclo y lee `dev.json` con `utf-8-sig`.
- **Archivos**: `agent-kits/shared/skill-index.py`, `agent-kits/shared/test_skill_index.py`, `agent-kits/shared/README.md` (E3: describía el recorte; añadido por el implementer), `interop/**` (el índice de OpenCode se deriva de `skill-index.py`; faltó regenerarlo en el commit de T-10 y se corrigió en c078d2d), `tests/test_native_role_context.py` (CI de c078d2d: su muestra `architect` queda recortada con el nuevo orden; pasa a `planner`, siempre visible; el test sigue comprobando el prefijo nativo por runtime).
- **Tiempo IA (ejec.)**: real 0,01h (medido)
- **Verificación**: el índice de este repo muestra planner, qa, reviewer, tdd y `/setup` dentro del tope de 3.500 caracteres.
- **Changelog**: El índice de piezas que se inyecta al arrancar muestra primero las del ciclo (planner, qa, reviewer, tdd, `/setup`, `/work-resume`…) en vez de recortar por orden alfabético, y respeta `sesion.indice: false` aunque `dev.json` tenga BOM.
- **Cerrada**: 2026-11-09

**Criterios de aceptación**
- [x] Las piezas del ciclo aparecen antes que las opcionales.
- [x] `dev.json` con BOM respeta `sesion.indice: false`.


RED: `agent-kits/shared/test_skill_index.py -k h21` falló con 3 failed: el indice del repo oculta /setup (y planner, qa, reviewer, tdd) por orden alfabetico; sin orden de prioridad; dev.json con BOM ignora sesion.indice false e imprime el indice · 2026-11-09.

GREEN: `pytest agent-kits/shared/test_skill_index.py` → `30 passed` (casos H-21: en este repo `/setup`, `/work-resume`, tdd, unit-tests, planner, qa y reviewer visibles y llm-pipeline fuera; orden de prioridad y después alfabético; BOM con `indice: false` → sin salida); `skill-index.py --no-cache --json` sobre el repo → `3427` caracteres, `44` líneas (topes 3.500/45); `tests/test_hooks_shell.py -k "indice or index"` 4 passed, `tests/test_session_context.py -k "off or startup"` 6 passed, `test_context_footprint.py` + `test_source_snapshot.py` 48 passed + 1 skipped. `VERSION` del índice 3 → 4 para invalidar las cachés con el orden viejo · 2026-11-09.

GREEN (seguimiento CI): `pytest tests/test_native_role_context.py` → `3 passed` (muestra `planner` en vez de `architect`, recortado por el orden del ciclo); `export-interop.py --check` → `92 ficheros al día` tras c078d2d (la CI de 742a6b4 falló en `test_arbol_generado_al_dia` por el índice de OpenCode sin regenerar) · 2026-11-09.


RED: `agent-kits/shared/test_skill_index.py::test_fix1_a1_todos_los_agentes_y_los_comandos_del_ciclo_siempre_visibles` falló con fix1: 1 failed: solo 5 agentes visibles (faltan analyst, architect, documenter, knowledge-curator, nemesis) por la cuota fija por grupo · 2026-11-09.

GREEN fix1: `pytest agent-kits/shared/test_skill_index.py tests/test_native_role_context.py` → `34 passed` (A1: los 10 agentes y `/setup`, `/dev-cycle`, `/pm-cycle`, `/work-resume` siempre visibles; las skills opcionales se resumen; el test histórico del reparto proporcional pasa a exigir los 8 agentes visibles); índice del repo 3383 caracteres, 45 líneas; `export-interop.py` → índice de OpenCode regenerado, `--check` → `92 ficheros al día`. `skill-index.py` también corrige su docstring (matcher con `clear`, A5) · 2026-11-09.

### T-11 — Un solo troceo del ledger

- **Estado**: completado
- **Descripción**: H-22, H-23, H-26 y menores de ledger-lint. `scope-check`, `coverage-check` y `jira-flow` usan el troceo de `ledger-lint` (bloques de código y secciones posteriores fuera); resumen dentro de bloques de código ignorado; vocabulario de `estado` validado a nivel ledger.
- **Archivos**: `agent-kits/shared/ledger-lint.py`, `agent-kits/shared/scope-check.py`, `agent-kits/qa/coverage-check.py`, `skills/jira-sync/scripts/jira-flow.py`, sus tests, `agent-kits/shared/copias.json`, `tests/test_ledger_single_parser.py` (añadido por el implementer: casos H-22/H-23/H-26, resumen en bloque de código, vocabulario y los ledgers del repo).
- **Tiempo IA (ejec.)**: real 0,09h (medido)
- **Verificación**: casos con bloques de código en `tasks.md` para los cuatro scripts → pasan; los 67 ledgers del repo siguen dando exit 0.
- **Changelog**: La puerta de alcance, la cobertura de QA y el volcado a Jira trocean el ledger igual que ledger-lint: un ejemplo dentro de un bloque de código o una sección de notas ya no amplía el alcance ni crea tareas fantasma, y la Verificación en sub-lista llega entera a Jira; ledger-lint ignora un resumen citado y rechaza un estado de ledger fuera del vocabulario.
- **Cerrada**: 2026-11-09

**Criterios de aceptación**
- [x] Un `Archivos` o `### T-XX` dentro de un bloque de código no cuenta.
- [x] La Verificación en sub-lista llega entera a Jira.


RED: `tests/test_ledger_single_parser.py` falló con 5 failed: scope-check suma el Archivos de un bloque de codigo (**/*); coverage-check crea la tarea fantasma T-99 con referencia rota; jira-flow solo lleva el primer item de la Verificacion; ledger-lint cuenta un resumen citado en un bloque de codigo; estado del ledger fuera de vocabulario aceptado · 2026-11-09.

GREEN: `pytest tests/test_ledger_single_parser.py` → `7 passed` (scope-check sin el `Archivos` de un bloque de código ni el de `## Notas`; coverage-check sin la tarea fantasma, también copiado sin el kit compartido; jira-flow con la Verificación entera y `_campo` que no cruza líneas; resumen citado ignorado; `estado: terminado` → error; los 68 ledgers del repo sin errores); `agent-kits/shared/test_scope_check.py` 31, `tests/test_ledger_lint.py` 9, `skills/jira-sync/scripts/test_jira_flow.py` 74, `tests/test_copias_declaradas.py` 30, `tests/test_ledger_write.py` 29 + 2 skipped, `agent-kits/shared/test_task_brief.py` 92 passed; `python tests/test_coverage_check.py` → `OK`; `ledger-lint.py` sobre `docs/roadmap/*/tasks.md` → 68 ficheros, 0 con exit ≠ 0. Decisión: el troceo único es `bloques_de_tarea()` de `ledger-lint.py`; coverage-check conserva un respaldo local con el mismo criterio (no es una copia literal, así que no entra en `copias.json`) y jira-flow usa el del kit si está · 2026-11-09.


RED: `tests/test_ledger_single_parser.py -k fix1` falló con fix1: 3 failed: respaldos de coverage-check y jira-flow sin el criterio de bloques_de_tarea (valla de cuatro, corte en Fase); copias sin declarar; en batch parse_ledger y bloques por tarea · 2026-11-09.

GREEN fix1: `pytest tests/test_ledger_single_parser.py` → `10 passed` (B6: los respaldos `_bloques_de_tarea_local` de coverage-check y jira-flow dan lo mismo que `bloques_de_tarea` con una valla de cuatro acentos y un `### Fase`; D2: en una pasada de 29 tareas `bloques_de_tarea` y `parse_ledger` corren una vez y ledger-lint se carga una vez); `tests/test_copias_declaradas.py` → `31 passed` (copias literales declaradas: `sin_vallas` gana coverage-check y el bloque nuevo `bloques_de_tarea` tiene tres sitios); `skills/jira-sync/scripts/test_jira_flow.py` → `74 passed`; `python tests/test_coverage_check.py` → `OK` · 2026-11-09.

### T-12 — Bucle de revisión y dueño del commit

- **Estado**: completado
- **Descripción**: H-24 y H-25. «Seguir» tras el 3.er intento abre un ciclo nuevo con OK del usuario; un solo dueño del commit.
- **Archivos**: `commands/dev-cycle.md`, `agents/implementer.md`, `skills/adversarial-review/SKILL.md`, `agent-kits/shared/ledger-write.py`, `agent-kits/shared/test_ledger_write.py`, `interop/**`, `tests/fixtures/dev-cycle-modular-replacements.json`, `tests/test_ledger_write.py` (la suite real del writer está en `tests/`, no en `agent-kits/shared/`; nota del implementer), `tests/test_review_cycle_owner.py`, `agent-kits/shared/ledger-write.md`, `docs/COMMIT-SELECTION.md`, `docs/en/COMMIT-SELECTION.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `docs/agents/implementer.md` (E3: describían el límite de intentos o el dueño del commit), `CHANGELOG.md`, `CHANGELOG.es.md` (entrada `### Fixed` de toda la Fase 2) (añadidos por el implementer).
- **Tiempo IA (ejec.)**: real 0,07h (medido)
- **Verificación**: test del writer con ciclo nuevo → pasa; interop al día.
- **Changelog**: «Seguir» tras el tercer intento de revisión abre un ciclo nuevo acotado con el OK del usuario citado en la cabecera (`ledger-write.py review --attempt 4 --new-cycle-ok`), y los commits de tarea tienen un único dueño y procedimiento, el del implementer.
- **Cerrada**: 2026-11-09

**Criterios de aceptación**
- [x] El camino de «seguir» es ejecutable con el writer.
- [x] El commit tiene un único dueño y procedimiento.


RED: `tests/test_ledger_write.py -k h24 + tests/test_review_cycle_owner.py` falló con 4 failed: ledger-write review rechaza --attempt 4 (choices 1-3) aunque dev-cycle ofrece seguir; sin --new-cycle-ok en dev-cycle, adversarial-review ni ledger-write.md; implementer P4 y la Fase 6 describen dos procedimientos de commit · 2026-11-09.

GREEN: `pytest tests/test_ledger_write.py` → `32 passed, 2 skipped` (intento 4 sin `--new-cycle-ok` → `new_cycle_ok_required` sin escribir; con el OK → cabecera `intento 4: … — ciclo 2, abierto con OK del usuario: «…» (T-01, T-02)` que ledger-lint acepta; 5 y 6 sin repetir el OK, el 7 vuelve a pedirlo; OK fuera de lugar, vacío, multilínea o de más de 200 caracteres → rechazado; el test histórico «1, 2, 4 tras tres intentos → rechazado» sigue igual); `pytest tests/test_review_cycle_owner.py` → `2 passed` (dev-cycle, adversarial-review y ledger-write.md describen el ciclo nuevo; el procedimiento de commit vive en P4 del implementer y la Fase 6 solo lo verifica); `tests/test_dev_cycle_split.py` → `10 passed`, ahorro de la vía rápida 6080 → 6231 (el procedimiento de `commit-selection.py` pasa de la Fase 6 al implementer; 2 filas de reemplazo); `test_skill_size.py` 37, `test_context_footprint.py` 15, `test_source_snapshot.py` 33 + 1 skipped, `test_native_guardrail_dispatch.py` 14, `test_doctrina_viaja.py` 11, `test_lite_profile.py` 30, `test_commit_selection_cli.py` 10, `test_user_handbooks.py` 4, `test_npm_payload.py` 5, `test_roadmap_index.py` 71 passed; `lint_plugin.py` 0 errores; `evals/check.py` 0 errores; `export-interop.py --check` → `92 ficheros al día`. Decisión: cada ciclo de revisión tiene 3 intentos; «seguir» abre el siguiente (4-6, 7-9) solo con el OK citado y el writer no admite más de 9 · 2026-11-09.


RED: `tests/test_ledger_write.py::test_fix1_b3_un_t_nn_dentro_de_la_cita_no_atribuye_el_intento_a_otra_tarea` falló con fix1: 1 failed: el T-07 de la cita entra en menciones de la seccion de revision · 2026-11-09.

GREEN fix1: `pytest tests/test_ledger_write.py -k "fix1 or h24"` → `4 passed`; fichero completo `32 passed, 2 skipped` (B3: un `T-NN` en la cita del OK se escribe con guion U+2011, se lee igual y `menciones` solo ve T-01 y T-02) · 2026-11-09.

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
- **Notas**: Incluye la deuda de T-08 (revisión fase 2 intento 1, A2): un aviso de ledger-lint para las tareas `completado` sin `RED:` ni `TDD n/a` cuando `dev.json` trae `tdd: true` (hoy solo lo comprueba la Lente A, criterio 5b). Incluye la deuda de T-05: nueva edición PDF de los manuales `docs/guides/subscription-efficiency.md` y `docs/guides/quality-playbook.md` para que digan que lite despacha al implementer nativo.
- **Archivos**: `CLAUDE.md`, `commands/*.md`, `skills/**/SKILL.md`, `docs/**`, `hooks/*.sh`, `scripts/release.py`, `skills/plugin-panel/**`, `interop/**`, tests afectados.
- **Verificación**: lint 0 errores, evals 0 errores, interop al día, CI completa en Linux verde.

**Criterios de aceptación**
- [ ] Los menores de la auditoría quedan corregidos o descartados con motivo en este ledger.

## Revisión de dos lentes — intento 1: Fase 1 (T-01…T-06) — 12 gaps corregidos (5 Important, 7 Minor), 4 descartados por el orquestador (T-01, T-02, T-03, T-04, T-05, T-06)

Lentes: A + B + C (C por `review-lens-select.py`: guardarraíles, instalador y red). Corrección en `fix1` por el implementer, con RED/GREEN en cada tarea.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | `guardrail-check.py`: abreviaturas (`--ha`, `--fo`, `--del`), `push --mirror/--prune`, `clean.requireForce` en línea y alias `-c alias.*` saltaban las denegaciones | T-06 | corregido | `_abrevia` + `_claves_config`; `test_guardrail_check.py` 190 passed (commit 4fe305c) |
| 2 | Important | `qa-gate.py`: `[failed, skipped]` sin `stats` contaba como saltado y ocultaba el fallo | T-02 | corregido | la rama skipped exige todos los resultados saltados; `test_qa_gate.py` 7 passed (3645f7b) |
| 3 | Important | `usage-meter.py`: estado con BOM o ilegible tratado como vacío y sobrescrito | T-01 | corregido | `utf-8-sig`; start/close exit 3 sin escribir, status avisa; `test_usage_meter.py` 80 passed (cc93811) |
| 4 | Important | `docs/agents/implementer.md` y `agent-kits/shared/README.md` aún decían «lite en el hilo actual» | T-05 | corregido | textos actualizados; `DOCS` del test ampliada; `test_native_guardrail_dispatch.py` 7 passed (27ae7d4) |
| 5 | Important | docstring de `review-lens-select.py` y `lens-c-heuristics.md` decían «error → false» | T-06 | corregido | alineados con «error → true en auto» (4fe305c) |
| 6 | Minor | `agents/implementer.md` y `docs/agents/implementer.md` no listaban las nuevas denegaciones | T-06 | corregido | listas ampliadas; interop regenerado, `--check` 92 al día (4fe305c, 27ae7d4) |
| 7 | Minor | `.git` roto trataba el caso como «fuera de repo» y apagaba C y D | T-06 | corregido | `_hay_git_arriba` → error → C y D true; fuera de git real sigue false y documentado; `test_review_lens_select.py` 62 passed (4fe305c) |
| 8 | Minor | `worklog.py`: `nan`/`inf`, campos de tipo equivocado con traceback, `os.replace` con PermissionError | T-01 | corregido | rechazo de no finitos, validación de forma → exit 2, reintento acotado; `test_worklog.py` 11 passed (cc93811) |
| 9 | Minor | `uninstall` aislaba por proveedor pero no por manifiesto | T-03 | corregido | bucle por `sitiosManifiesto` con try por manifiesto; `installer.test.mjs` 184 pass (0a7f98e) |
| 10 | Minor | `codex-plugin-state.mjs` aceptaba entradas relativas del PATH; `correr` lanzaba el nombre pelado | T-03 | corregido | filtro de absolutas; `correr` da ENOENT propio; `codex-plugin-state.test.mjs` 7 pass (0a7f98e) |
| 11 | Minor | sin respaldo del tipo `implementer` con el bundle copiado | T-05 | corregido | prosa en `dev-cycle.md` y `phase3-subagents.md`; ahorro vía rápida 6055 (27ae7d4) |
| 12 | Minor | cabecera del CHANGELOG sin el slug que usa `changelog-sync` | T-06 | corregido | cabeceras con `` `plugin-audit-remediation` `` (2a70dd0); al cerrar la iniciativa, las fases 2-4 se añaden a mano bajo esa sección porque `changelog-sync` la da por publicada |
| 13 | Minor | `git checkout -- .`/`git restore .`/`checkout -f` | T-06 | descartado (ampliación de H-12, no forma equivalente; propuesta para una iniciativa posterior) | decisión del orquestador |
| 14 | Minor | envoltorios `nice/timeout/sudo/xargs/find -exec/$G` saltan todas las reglas git | T-06 | descartado (limitación previa del parser, fuera del diff) | decisión del orquestador |
| 15 | Minor | `guardrail-check.py:709-711` deja pasar ante excepción interna | T-06 | descartado (diseño previo, ADR-007: un guardrail roto no bloquea) | decisión del orquestador |
| 16 | Minor | `setTrustAnchors` con `--dir` dentro de `~/.claude/plugins` en `--scope user` | T-03 | descartado (escenario no reproducido; queda como propuesta) | decisión del orquestador |

## Revisión de dos lentes — intento 2: Fase 1 (T-01…T-06) — 14 gaps corregidos (10 Important, 4 Minor), guardarraíl git cerrado por diseño (T-01, T-02, T-03, T-04, T-05, T-06)

Lentes: A + B + C (C por guardarraíles, instalador y lanzamiento de procesos). Corrección en `fix2` por el implementer; cada gap corregido tiene un test dedicado que lo nombra.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | Guardarraíl: prefijos cortos de opciones destructivas (`reset --h`, `push --m`, `--force-w`) | T-06 | corregido | `_prefijo` sin mínimos por opción; `test_fix2_guardarrail_cerrado_por_diseno_deniega` (bde0370) |
| 2 | Important | `clean -fn`, `-fen`, `-n --no-dry-run` contaban como simulación | T-06 | corregido | simulación solo con `-n` exacto o prefijo de `--dry-run` sin `--no-dry-run`; mismo test (bde0370) |
| 3 | Important | Opciones globales con valor (`--attr-source`, `--super-prefix`, `--list-cmds`) y desconocidas desincronizaban el subcomando | T-06 | corregido | lista completa de git 2.4x; una global desconocida se deniega; mismo test (bde0370) |
| 4 | Important | Inyección de configuración: `include.*`/`includeif.*`, `GIT_CONFIG_*` sin distinguir mayúsculas y por `export`/`set`/`env`, `git config` persistente; `requireForce=true` era falso positivo | T-06 | corregido | `_razon_config`; `_env_hooks_override` sin distinguir mayúsculas; `requireForce=true` permitido; `test_fix2_*` en `test_guardrail_check.py` y `test_git_verification.py` (los casos «permitidos» de `GIT_CONFIG_*` y `--no-v` pasan a denegados por diseño) (bde0370) |
| 5 | Important | `branch -df`, `-fd`, `-d -f`, `--del --forc` | T-06 | corregido | borrar + forzar en cualquier forma → deny; `-d` sigue permitido; mismo test (bde0370) |
| 6 | Important | Docstring y listas del implementer con el contrato final | T-06 | corregido | `guardrail-check.py`, `agents/implementer.md`, `docs/agents/implementer.md`; `test_fix2_gap6_implementer_lists_name_every_denied_family` (bde0370, b70a16e) |
| 7 | Minor | qa-gate: `[failed, skipped]` como flaky justificable → VERDE | T-02 | corregido | flaky exige al menos un `passed`; `test_fix2_sin_ningun_passed_no_es_flaky_ni_se_justifica` (16abc50) |
| 8 | Important | `CONTRACTS.md` E7 prometía exit 0 siempre en usage-meter | T-01 | corregido | fila con exit 3 y JSON real; `test_fix2_contracts_describe_exit_real_de_usage_meter` (f7025ca) |
| 9 | Minor | `/doctor` ignoraba los avisos de `usage-meter.py status` | T-01 | corregido | ⚠️ con respaldo `.bak` y borrado; `test_fix2_doctor_avisa_de_usage_state_ilegible_con_arreglo` (f7025ca) |
| 10 | Minor | worklog: campos internos de `tasks` y números de config sin validar | T-01 | corregido | exit 2 con JSON; `test_fix2_campos_internos_de_tasks_invalidos_exit2`, `test_fix2_numeros_de_config_invalidos_exit2` (f7025ca) |
| 11 | Important | `cmd.exe` resolvía `node` en el cwd del proyecto al lanzar shims `.cmd` | T-03 | corregido | `NoDefaultCurrentDirectoryInExePath=1` en `correr`, `runCodexQuery` y `hooks/run-hook.mjs`; tests C8 en `installer.test.mjs` y `codex-plugin-state.test.mjs` con `node.bat` plantado (ce2bf32) |
| 12 | Important | `commands/setup.md` decía «lite en el hilo actual» | T-05 | corregido | texto actualizado, interop regenerado, `commands/setup.md` en `DOCS` (b70a16e) |
| 13 | Important | Faltaban tests dedicados de los gaps 5, 6 y 12 del intento 1 | T-06 | corregido | `test_fix2_gap5_*`, `test_fix2_gap6_*`, `test_fix2_gap12_*` en `tests/test_native_guardrail_dispatch.py` (b70a16e) |
| 14 | Minor | CHANGELOG ES/EN y campo `Changelog` de T-01 sin los cambios nuevos | T-06 | corregido | entrada completada; `test_fix2_changelog_de_fase_1_recoge_los_cambios_del_intento_2` (RED: en HEAD faltaban las marcas) (aacea76) |

## Revisión de dos lentes — intento 3: Fase 1 (T-01…T-06) — 12 gaps corregidos (6 Important, 6 Minor) en un ciclo final acotado; guardarraíl por lista blanca (T-01, T-02, T-03, T-04, T-05, T-06)

Lentes: A + B + C. Corrección en `fix3` por el implementer; cada gap con test dedicado que lo nombra (`test_fix3_*`).

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | `-c`/`--config-env` por lista negra: `core.editor`, `core.sshCommand`, `core.pager`, `diff.external`, `remote.*`… pasaban | T-06 | corregido | LISTA BLANCA `_CONFIG_PERMITIDA`: user.name, user.email, core.quotepath, commit.gpgsign, init.defaultbranch, color.*, advice.* (justificadas en el código); `test_fix3_guardarrail_lista_blanca_y_analisis_real_deniega` (d29e940) |
| 2 | Important | `git config` mal clasificado (`--comment --get alias.x v`, `--rename-section`, `--file`, subcomandos nuevos) | T-06 | corregido | `_razon_git_config`: lectura/escritura reales, opciones que consumen valor, prefijos resueltos o denegados; escrituras solo de la lista blanca sin `--file`/`--blob` (d29e940) |
| 3 | Important | Entorno: `GIT_EDITOR`, `GIT_SSH*`, `GIT_DIR`, `HOME`, `XDG_CONFIG_HOME` con git permitidos; falso positivo `GIT_CONFIG_NOSYSTEM=1 pytest` | T-06 | corregido | `GIT_*`/`HOME`/`XDG_CONFIG_HOME` denegados solo cuando la orden ejecuta git (mismo segmento o exportados antes); `env -i git` permitido; `_env_hooks_override` eliminado por subsumido (d29e940) |
| 4 | Important | `clean`: `--`, `-e`/`--exclude` sin analizar; falso positivo `-fn`/`-nf` | T-06 | corregido | `_razon_clean`: `--` separa rutas, `e` consume valor, gana el último de `n`/`--dry-run` frente a `--no-dry-run`; `-fen`, `-e -n -f`, `-f -- -n .` → deny; `-fn`, `-fdn`, `-nf` → allow (d29e940) |
| 5 | Minor | `_cluster` sin dígitos (`push -4f`, `-6d`) | T-06 | corregido | `-[a-zA-Z0-9]+` (d29e940) |
| 6 | Important | `branch -f <rama>`, `-M`, `-C` y `update-ref -d` | T-06 | corregido | denegados (también `update-ref --stdin`); `-d`, `-m`, `--list` permitidos (d29e940) |
| 7 | Minor | Opciones globales legítimas | T-06 | corregido | `-C`, `-P`, `--no-pager`, `--no-optional-locks`, `--paginate`, `--literal-pathspecs`, `--bare` permitidas en `test_fix3_formas_legitimas_permitidas` (d29e940) |
| 8 | Minor | Docstring, prompt, doc del implementer y FLOWS ES/EN sin el contrato final ni el límite | T-06 | corregido | contrato de lista blanca y «no es un sandbox» (envoltorios, scripts propios y configs a mano fuera; ADR-023/ADR-007); `test_fix3_gap8_docs_describen_lista_blanca_y_que_no_es_sandbox` (d29e940) |
| 9 | Important | `/doctor` trataba cualquier aviso de `status` como estado ilegible y proponía borrar | T-01 | corregido | `status` publica `estado_ilegible`; marcador corrupto → respaldar y reparar, huérfanos siguen; `test_fix3_doctor_distingue_estado_ilegible_de_marcador_corrupto`, `test_fix3_status_marca_solo_el_estado_ilegible_como_fatal` (5505327) |
| 10 | Minor | qa-gate: flaky exigía el literal `passed`, no `expectedStatus` | T-02 | corregido | flaky = resultado esperado tras un fallo (un salto no cuenta); `test_fix3_flaky_es_el_resultado_esperado_tras_un_fallo` (1893cf5) |
| 11 | Minor | `candidates()` de `run-hook.mjs` aceptaba entradas relativas del PATH | T-03 | corregido | `absolutePathEntry`; `run-hook candidates ignore relative PATH entries` (5a683b1) |
| 12 | Minor | Evidencia de T-03 con 1 fallo y TDD de los gaps 13-14 del intento 2 | T-03, T-06 | corregido | nota en T-03: `installer.test.mjs:1909`, tope 30000 ms, dependiente de la carga, aislado ✔ 17336 ms (tope sin relajar); `TDD n/a` en T-06 para los tests escritos sobre texto ya corregido; CHANGELOG ES/EN con la lista blanca (c0264f3) |
| 13 | Important | `commit.gpgsign` en la lista blanca dejaba desactivar la firma (`-c commit.gpgsign=false`, `git config commit.gpgsign false`) — detectado en la verificación dirigida del orquestador | T-06 | corregido | solo con valor verdadero; falso, vacío, sin valor o `--config-env` → deny; `test_fix3b_commit_gpgsign_solo_con_valor_verdadero`, `test_fix3b_changelog_y_docs_dicen_que_commit_gpgsign_solo_vale_verdadero` (2357747) |

**Decisión del orquestador:** al 3.er intento con gaps, el orquestador decide seguir con un ciclo final acotado (autorización del usuario «con todo»); se verifica con tests dirigidos y CI, sin 4.º intento de lentes.

## Revisión de dos lentes — intento 1: Fase 2 (T-07…T-12) — 4 Important y 11 Minor corregidos en fix1, ninguno descartado (T-07, T-08, T-09, T-10, T-11, T-12)

Lentes: A + B + C + D. Corrección en `fix1` por el implementer; cada gap con un test dedicado que lo nombra (`test_fix1_*`).

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | B1: el escritor del journal etiquetaba con la primera activa alfabética y el lector elegía la en curso: con ≥ 2 activas no se reinyectaba nada | T-07 | corregido | `progress-report.iniciativa_vigente` es la regla única de escritor (`journal.iniciativa_activa`) y lector; excluye las de 100 % salvo que no haya otra; `test_fix1_b1_*` escribe con `journal.py write` y lee con `resume --history-only` (078abb3) |
| 2 | Important | B2: `list_names` cortaba en 128 en orden de `scandir` antes de ordenar; con > 128 carpetas se perdían las más nuevas y `recorte.omitidas` contaba carpetas con fecha que no son iniciativas | T-09 | corregido | `list_names(newest_first=True)` lee hasta 4.096 nombres, ordena y corta; cartera, progreso y `_carpeta` lo usan; omitidas solo cuenta iniciativas; `test_fix1_b2_*` con 140 carpetas (1c71a3f) |
| 3 | Important | C1: `_SUMMARY_ROW` con retroceso cúbico bloqueaba el servidor con una fila de miles de espacios | T-09 | corregido | `_header_summary` delega en `progress-report.resumir_cabecera` (celdas por `split`); `test_fix1_c1_*` con 20.000 espacios < 5 s, antes cortado por el `timeout` de 600 s (1c71a3f) |
| 4 | Important | A1: la cuota fija por grupo dejaba 5 agentes y ocultaba nemesis, analyst, architect, documenter y knowledge-curator | T-10 | corregido | cuotas fijas para los 10 agentes y los comandos de `PRIORIDAD`; las skills opcionales se resumen; índice de OpenCode regenerado; `test_fix1_a1_*` (b83eede) |
| 5 | Minor | C2/D1: `_history_initiative` usaba `activas()` sin tope que sigue enlaces, otro escaneo completo y otra lectura de `usage-state.json` | T-07 | corregido | `activas_acotadas` con `local-read` (cabecera acotada de los ledgers grandes) y memo de `usage-state.json` por firma; `test_fix1_c2_*`, `test_fix1_d1_*` (078abb3) |
| 6 | Minor | B3: un `T-NN` en la cita de `--new-cycle-ok` entraba en las menciones del intento | T-12 | corregido | el guion del `T-NN` citado pasa a U+2011; `test_fix1_b3_*` (6dd78a1) |
| 7 | Minor | B4: la en curso se elegía también entre las de 100 % y la memoria agrupaba por el % redondeado | T-07 | corregido | `vigente_entre` sobre las pendientes; memoria por `completadas == total`; `test_fix1_b4_*` (078abb3) |
| 8 | Minor | B5: con un ledger pendiente > 256 KiB las revisiones desaparecían sin aviso | T-07 | corregido | línea «Revisiones omitidas: ledger > 256 KiB; /work-resume --initiative <carpeta>»; `test_fix1_b5_*` (078abb3) |
| 9 | Minor | B6: los respaldos locales de coverage-check y jira-flow no seguían el criterio de `bloques_de_tarea` | T-11 | corregido | copias literales de `sin_vallas` y `bloques_de_tarea` declaradas en `copias.json` (paridad en `test_copias_declaradas.py`); `test_fix1_b6_*` (1faafb2) |
| 10 | Minor | D2: en `--batch`, jira-flow cargaba ledger-lint y troceaba/parseaba el ledger una vez por tarea | T-11 | corregido | carga memoizada y `_troceo` una vez por texto; `test_fix1_d2_*` (1faafb2) |
| 11 | Minor | A3: la vía rápida CON UI seguía sin QA ejecutable | T-08 | corregido | decisión: un cambio con interfaz va al flujo completo (filtro de quick-implement y vía rápida de `/dev-cycle`); `test_fix1_a3_*` (7bc6f6d) |
| 12 | Minor | A4: CONTRACTS E1, `docs/agents/qa.md`, P1 de qa y del implementer decían que el marcador solo vale en `improvement-plan.md` | T-08 | corregido | nombran el `tasks.md` ligero; `test_fix1_a4_*` (7bc6f6d) |
| 13 | Minor | A5: matcher `startup\|resume\|compact` desfasado en CONVENTIONS ES/EN, shared README, `skill-index.py` y `claude-code-contracts.md` | T-07 | corregido | todos con `clear`; `test_fix1_a5_*` (078abb3, b83eede) |
| 14 | Minor | A2: el aviso de ledger-lint para tareas cerradas sin `RED:`/`TDD n/a` se descartó sin deuda | T-08 | corregido como deuda | registrado en T-21 (ledger-lint no lee `dev.json`); `test_fix1_a2_*` lo vigila (7bc6f6d) |
| 15 | Minor | A6: `tests/test_native_guardrail_dispatch.py` (de T-05) se modificó dentro de T-08 sin traza | T-08 | anotado | se cambió en 828fdfa porque el orquestador devolvió los dos manuales a su edición PDF del 2026-11-04 (205f1ed) y su test exigía el texto nuevo: salen de `DOCS` y un test nuevo exige su deuda en T-21; el fichero está declarado en el `Archivos` de T-08 |

Notas: (a) en el arranque de este repo el historial no sale porque las entradas existentes se etiquetaron con la regla vieja; las nuevas usan la regla única. (b) la equivalencia de bytes `replay-codex` de `tests/test_session_context.py` falló una vez por tiempos y pasó al repetirla. (c) el ahorro de la vía rápida queda en 6189 (≥ 6000).

**fix1b (T-07):** la CI de Linux falló en los dos `test_fix1_b1_*`: leían `next(glob("*.md"))` del journal y en Linux el orden de `glob` devolvía el `README.md` del directorio. Ahora leen la única entrada que no es el README (`_entrada_journal`). Sin RED nuevo: el test dependía del orden del sistema de ficheros, no el código. Los demás `next(...glob(...))` de la fase casan un único fichero. `pytest agent-kits/shared/test_work_resume.py -k fix1_b1` → `2 passed`.
