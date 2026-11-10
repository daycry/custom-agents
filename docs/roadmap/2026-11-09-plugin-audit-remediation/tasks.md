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
| Fase 3 | 4 | 4 | 100.0% |
| Fase 4 | 5 | 5 | 100.0% |
| **TOTAL** | **21** | **21** | **100.0%** |

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

**Estado**: completado

### T-07 — Retoma de sesión: journal y bloque útil

- **Estado**: completado
- **Descripción**: H-14, H-27 y H-48. Reinyectar la última entrada del journal sin depender de la selección global de ledgers; iniciativa en curso primero en memoria; líneas opacas fuera; iniciativas al 100 % compactadas; pie sin ruta absoluta; `clear` también en Claude.
- **Archivos**: `agent-kits/shared/progress-report.py`, `hooks/session-context.py`, `hooks/hooks.json`, `agent-kits/shared/test_progress_report.py`, `tests/test_session_context.py`, `tests/test_hooks_shell.py`, `interop/**`, `docs/observability.md`, `docs/en/observability.md`, `hooks/session-context.sh` (oráculo de bytes del compositor nativo: mismo pie y mismo orden de memoria), `agent-kits/shared/test_work_resume.py` (casos H-14/H-48 del historial del arranque), `tests/test_graphiti_security.py` (huella `sha256_lf` de `hooks/session-context.py`), `docs/WORK-RESUME.md`, `docs/en/WORK-RESUME.md`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md` (E3: describían la selección del historial al arrancar) (añadidos por el implementer), `agent-kits/shared/journal.py` (revisión intento 1, B1: el escritor usa la misma regla que el lector), `agent-kits/shared/README.md`, `skills/plugin-dev/references/claude-code-contracts.md` (revisión intento 1, A5: matcher con `clear`), `agent-kits/shared/test_local_read.py`, `agent-kits/shared/doctor.py`, `agent-kits/shared/test_doctor.py` (revisión intento 3: raíz del proyecto como ancla del lector acotado y avisos de la instantánea en `/doctor`).
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


RED: `agent-kits/shared/test_work_resume.py -k fix2` falló con fix2: 6 failed: estado solo en la tabla de cabecera ignorado y fuera del prefijo dado por inactivo (B-I1); la de 100 % con marcador abierto pierde frente a la pendiente (B-I2); session y active hacen lecturas completas con activas() (B-M3); entradas sin regla vigente reinyectadas y sin campo regla_iniciativa (B-M4); tope de 128 sin documentar · 2026-11-09.

GREEN fix2: `pytest agent-kits/shared/test_work_resume.py` → `66 passed` (B-I1: estado en la tabla de cabecera y fuera del prefijo de 16 KiB → relectura acotada de 256 KiB; B-I2: el marcador abierto manda aunque la iniciativa esté al 100 %, empate por nombre; B-M3: `session` y `active --json` usan `activas_acotadas`, la misma instantánea memoizada que el journal, y conservan las tareas en curso; B-M4: el escritor marca `regla_iniciativa: "vigente"` y `--history-only` solo cita esas entradas; tope de 128 carpetas documentado en WORK-RESUME ES/EN); `test_progress_report.py` 43, `test_journal.py` 192 + 10 skipped, `tests/test_session_context.py` 47, `test_review_resume.py` 18, `test_resume_curation.py` 25, `tests/test_hooks_shell.py -k "session_context or memoria or activas or h14"` 31, `tests/test_statusline_cache.py` 17 passed. Medida del arranque (`compose` en proceso, 3 pasadas, copias del roadmap; la 1.ª incluye cargas y replay): 68 carpetas 8,61 / 4,89 / 11,93 s antes → 8,70 / 1,95 / 1,80 s después; 345 carpetas 29,79 / 16,08 / 15,17 s → 8,14 / 2,24 / 3,31 s. Máquina cargada: cifras orientativas; el detalle de rendimiento es de T-13 · 2026-11-09.


RED: `agent-kits/shared/test_work_resume.py -k fix3` falló con fix3: 6 failed: session nombra la pendiente y no la vigente con marcador abierto (A); raiz bajo un enlace rechazada (B); activa de 320 KB sin tabla con total None (B3); recorte de 128 sin aviso (B4); invalid_encoding sin aviso (B5); la firma hace lstat dentro de una carpeta enlazada (C1) · 2026-11-09.

GREEN fix3: `pytest agent-kits/shared/test_work_resume.py agent-kits/shared/test_local_read.py` → `145 passed, 5 skipped` (A: «Ledger canónico» nombra la vigente con la misma regla —`alfa` al 100 % con marcador abierto— y la cola «al 100 %: /retro alfa» en vez de «retoma desde…»; B: con la raíz del proyecto bajo una junction el bloque y la vigente funcionan, y un enlace por debajo sigue rechazado; `local-read` resuelve la raíz una vez con `realpath` y comprueba solo los componentes por debajo; los casos `root` de los dos tests históricos de enlaces pasan al test nuevo del ancla; B3: una activa de ~330 KB sin tabla se lee entera (tope 16 MiB) con su tarea en curso; B4: «Roadmap recortado: 3 carpetas más antiguas sin revisar» en `session` y en `active --json`; B5: «…: tasks.md ilegible (invalid_encoding)» en el bloque y en `/doctor`; C1: la firma no hace `lstat` dentro de una carpeta enlazada; A3: `--initiative` y `--session` siguen citando entradas sin `regla_iniciativa`); `test_progress_report.py` 43, `test_doctor.py` 233 + 1 skipped, `tests/test_session_context.py` 47, `test_knowledge_view.py` 153 + 1 skipped, `test_source_snapshot.py` 33 + 1 skipped, `test_plan_review_feedback_contract.py` 69, `test_journal_selection.py` 68, `tests/test_graphiti_security.py` 126, `test_review_resume.py` 18 passed. TDD n/a (A4 y punto 12): los tests de texto `test_fix3_a4_*` y `test_fix3_deuda_de_recover_*` se escribieron sobre el texto ya corregido, igual que el de `/doctor` (`test_fix3_b5_doctor_*`), cuyo rojo es el de B5 en `session` · 2026-11-10.

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


RED: `tests/test_quick_path_gates.py::test_fix2_a_m2_modo_rapido_explicito_y_recomendacion_excluyen_la_interfaz` falló con fix2: 1 failed: el modo rapido explicito y la recomendacion por defecto no excluyen un cambio con interfaz · 2026-11-09.

GREEN fix2: `pytest tests/test_quick_path_gates.py tests/test_dev_cycle_split.py` → `20 passed` (A-M2: el modo rápido explícito avisa y usa el flujo completo si el cambio toca interfaz, y la recomendación por defecto propone vía rápida solo sin interfaz); ahorro de la vía rápida 6158 (2 filas de reemplazo); `export-interop.py --check` → `92 ficheros al día` · 2026-11-09.

### T-09 — Dashboards completos con roadmaps grandes

- **Estado**: completado
- **Descripción**: H-17 a H-20. Cartera y progreso de la más nueva a la más antigua y con aviso honesto; progreso por cabecera, sin leer el ledger entero; planes con ledger > 256 KiB operables desde la consola; un plan nuevo no da 404; errores mapeados en la UI.
- **Archivos**: `skills/plugin-panel/scripts/panel_data.py`, `skills/plugin-panel/scripts/serve_panel.py`, `skills/plugin-panel/scripts/console_service.py`, `skills/plugin-panel/assets/control-center.js`, `skills/plugin-panel/assets/page-iniciativas.js`, `tests/test_panel_*.py`, `tests/test_console_*.py`, `agent-kits/shared/local-read.py` (lectura acotada de un prefijo para la cabecera de un ledger grande), `skills/plugin-panel/assets/panel-live.js` (valida y rotula `fuente: resumen`), `tests/test_control_center_http.py` (su contrato «sin improvement-plan.md → 503» pasa a la vía rápida operable) (añadidos por el implementer), `docs/PLUGIN-PANEL.md`, `docs/en/PLUGIN-PANEL.md`, `docs/agents/CONTRACTS.md` (revisión intento 2: topes reales del listado y del recorrido).
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


RED: `tests/test_panel_large_roadmaps.py -k fix2` falló con fix2: 4 failed: review_initiatives pierde las 12 mas nuevas con 140 carpetas (A-I1); 600 carpetas sin ledger se recorren todas (D-1); el recuento de omitidas llama a exists (C-1); topes de 4096 nombres sin documentar · 2026-11-09.

GREEN fix2: `pytest tests/test_panel_large_roadmaps.py` → `15 passed` (A-I1: `review_initiatives` con 140 carpetas incluye las 12 más nuevas; D-1: con 600 carpetas sin ledger, cartera y progreso hacen como mucho `MAX_SCAN` + 1 listados; C-1: las omitidas se cuentan por nombre, sin `exists` sobre carpetas omitidas —en HEAD, 70 llamadas—; topes de 4.096 nombres y 128 carpetas documentados en PLUGIN-PANEL ES/EN, CONTRACTS E35 y `local-read.py`); `tests/test_panel_server.py` 137 + 2 skipped, `tests/test_panel_review_server.py` 67, `tests/test_panel_data.py` 17 passed · 2026-11-09.


RED: `tests/test_panel_large_roadmaps.py -k fix3` falló con fix3: 3 failed: un fichero fechado cuenta como omitida (77 frente a 76, B2); 600 carpetas nuevas sin ledger dejan el progreso vacio (B); la 65.a carpeta se lee antes del corte (A2) · 2026-11-09.

GREEN fix3: `pytest tests/test_panel_large_roadmaps.py` → `18 passed` (B2: 140 iniciativas + 5 carpetas «solo-notas» + un fichero fechado → 76 omitidas, contadas por nombre de carpeta de iniciativa sin extensión; B: con 600 carpetas más nuevas sin ledger el progreso muestra la iniciativa real (filtra por nombre y recorre hasta `MAX_WALK` = 1.024); A2: el corte de 64 filas va antes de leer la 65.ª y no se lee ninguna de las 76 omitidas); `tests/test_panel_server.py` 137 + 2 skipped (dos tests usaban carpetas sin nombre de iniciativa: pasan a nombres fechados), `test_panel_data.py` 17, `test_panel_contract_golden.py` 6, `test_control_center_http.py` 21, `tests/test_panel_review_server.py` 67 passed · 2026-11-10.

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


RED: `agent-kits/shared/test_skill_index.py -k fix2` falló con fix2: 2 failed: la rama proporcional oculta agentes del plugin y comandos clave; docstrings hablan de cesion proporcional · 2026-11-09.

GREEN fix2: `pytest agent-kits/shared/test_skill_index.py` → `33 passed` (A-M3: con 50 agentes el reparto proporcional conserva los 10 agentes de `PRIORIDAD` y `/dev-cycle`, `/pm-cycle`, `/setup`, `/work-resume` dentro de 45 líneas y 3.500 caracteres; A-M4: docstrings sin «cesión proporcional» de agentes y comandos del ciclo) · 2026-11-09.

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

**Estado**: completado

### T-13 — SessionStart en una pasada

- **Estado**: completado
- **Descripción**: H-28 y H-40. Una sola instantánea del roadmap por arranque; `usage-state.json` sin `offsets` en marcadores cerrados.
- **Archivos**: `hooks/session-context.py`, `agent-kits/shared/progress-report.py`, `agent-kits/shared/usage-meter.py`, sus tests (`agent-kits/shared/test_progress_report.py`, `agent-kits/shared/test_usage_meter.py`, `tests/test_session_context.py`), `agent-kits/shared/knowledge-find.py` (la memoria del arranque leía el corpus una vez por consulta), `agent-kits/shared/ledger-lint.py` (`estado_ledger`: el estado de un prefijo sin trocear las tareas, con la regla de `parse_ledger`), `tests/test_graphiti_security.py` (huella `sha256_lf` de `hooks/session-context.py`), `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md` (E3: qué guarda `usage-state.json`) (añadidos por el implementer), `docs/roadmap/2026-11-09-plugin-audit-remediation/testing/perf.md` (medidas de CA-05; la guardia del implementer no le deja escribir en `testing/`: borrador entregado al orquestador).
- **Tiempo IA (ejec.)**: real 1,28h (medido)
- **Verificación**: medida antes y después sobre este repo (`testing/perf.md`); misma salida.
- **Changelog**: El arranque de sesión abre cada ledger y el estado del medidor una sola vez y lee la memoria técnica una vez para todas sus consultas: la mitad de tiempo con la misma salida; `usage-state.json` deja de crecer con cada transcript (de 4 MB a ~100 KB) sin cambiar ninguna medida.
- **Cerrada**: 2026-11-10

**Criterios de aceptación**
- [x] Cada ledger se lee una vez por arranque.
- [x] Salida idéntica a la anterior salvo las mejoras de T-07.

RED: `tests/test_session_context.py -k h28 + agent-kits/shared/test_usage_meter.py -k h40` falló con 4 failed: el arranque abre el ledger activo 5 veces, cada inactivo 2 y usage-state.json 2; con dos activas el corpus de la memoria se lee 2 veces; close guarda los 40 offsets de transcripts sin cambios; la migración no poda los marcadores cerrados existentes · 2026-11-10.

GREEN: `pytest tests/test_session_context.py` → `49 passed` (H-28: una apertura por `tasks.md` y por `usage-state.json`, corpus una vez); `agent-kits/shared/test_usage_meter.py` → `83 passed` (H-40: close poda y re-close mide 105 = 100 + la línea nueva del transcript reanudado; la migración conserva `ultimoCierre`, `ventana_id`, `revision_medicion`, `fuente_id` y deja intacto el marcador abierto); `test_progress_report.py` 45 (incl. `estado_ledger` == `parse_ledger` en los 68 ledgers del repo y `_LectorUnaVez` == `local-read.read_text`; TDD n/a en estos dos: equivalencias escritas tras el código), `test_work_resume.py` 75, `test_review_resume.py` 18, `test_journal.py` 192 + 10 skipped, `tests/test_knowledge_find.py` 106 + 2 skipped, `tests/test_ledger_lint.py` 9, `test_ledger_single_parser.py` 10, `test_copias_declaradas.py` 31, `tests/test_graphiti_security.py` 126 passed (huella nueva, sin red). Medida (5 procesos nuevos, mediana, misma salida por SHA): `compose` p68 2,23 → 1,14 s y p345 2,66 → 1,31 s; aperturas de `tasks.md` 107 → 68 (máx. por ledger 3 → 1), `usage-state.json` 2 → 1, corpus 2 → 1; `usage-state.json` 4.007.683 → 134.997 B (`json.load` 36,9 → 2,0 ms), re-close igual en T-07 y T-12 reales; en el repo, 103.374 B tras el primer close. Decisiones: el historial del arranque va directo a la iniciativa vigente (el escaneo de 1 MiB llegaba a la misma con una sola activa); un ledger ≤ 1 MiB se lee entero en una apertura y se sirve de esos bytes; poda por offset solo si el último registro anterior al `start` cae fuera de la tolerancia de 60 s (la poda por mtime sola contaba 4 respuestas de más en T-12) · 2026-11-10.

RED fix1: `agent-kits/shared/test_usage_meter.py -k fix1` falló con 2 failed: B1 `_ts_previo` devuelve la fecha anidada de `snapshot.timestamp` de una línea `file-history-snapshot`; D2 la migración abre 6 transcripts a la vez · 2026-11-10.

GREEN fix1: `pytest agent-kits/shared/test_usage_meter.py` → `85 passed` (B1: una línea JSON válida sin `timestamp` en la raíz da None, se conserva el offset y re-cerrar cuenta 7 tokens, no 57; D2: la migración agrupa las colas por transcript, abre uno cada vez —máximo 1 abierto—, reutiliza el `stat` de cada fichero entre marcadores y, si una cola no se puede leer —EMFILE—, no poda ni marca el marcador, para reintentarlo). Sobre la copia del repo: los mismos 537 offsets, los mismos tokens al re-cerrar T-07 y T-12, migración 2,4 → 1,23 s. Tiempo de la corrección: 0,05h (medido, `plugin-audit-remediation/T-13-fix1`) · 2026-11-10.

RED fix2: `agent-kits/shared/test_usage_meter.py -k fix2` falló con 4 failed: con una línea `file-history-snapshot` de 7,5, 30 y 105 KiB `_ts_previo` devuelve el `snapshot.timestamp` anidado; un transcript que es un directorio hace repetir la poda en cada migración · 2026-11-10.

GREEN fix2: `pytest agent-kits/shared/test_usage_meter.py` → `90 passed` (B1: solo decide con la línea entera —cola de 4 KiB y, si no basta, de 64 KiB—, por el `timestamp` de la raíz; una línea mayor o que no es JSON da None y conserva el offset, sin regex; D: un transcript ilegible deja `poda_fallida` con su mtime y solo se reintenta cuando cambia). Copia del repo: los mismos 537 offsets y los mismos tokens al re-cerrar T-07 y T-12; migración 0,71 s (una cola de 1 MiB no cambiaba ningún offset y la subía a 15 s: descartada). Tiempo: 0,04h (medido, `plugin-audit-remediation/T-13-fix2`) · 2026-11-10.

RED fix3: `agent-kits/shared/test_usage_meter.py -k fix3` falló con 2 failed: un transcript que desaparece tras el error de lectura queda en `poda_fallida` con mtime None y no se poda; tres EMFILE seguidos en un transcript viejo dejan el marcador sin podar · 2026-11-10.

GREEN fix3: `pytest agent-kits/shared/test_usage_meter.py` → `92 passed` (5: un fichero que ya no existe se descarta, como en el camino normal; uno existente e ilegible se reintenta solo si cambia su mtime y como mucho `PODA_INTENTOS` = 3 veces; después se poda conservando su offset). Tiempo: 0,01h (medido, `plugin-audit-remediation/T-13-fix3`) · 2026-11-10.

### T-14 — Menos procesos por hook

- **Estado**: completado
- **Descripción**: H-29, H-30 y H-31. Sin el Python de limpieza cuando el job ya está vacío; SubagentStop en Python con debounce; captura de UserPromptSubmit con un módulo ligero.
- **Archivos**: `hooks/run-hook.mjs`, `hooks/runtime-supervisor.py`, `hooks/subagent-progress.sh`, `hooks/subagent-progress.py`, `hooks/hooks.json`, `agent-kits/shared/journal-capture.py`, `agent-kits/shared/journal.py`, `interop/**`, tests de hooks (`tests/test_hook_processes.py`, nuevo), `agent-kits/shared/journal-prompt.py` (módulo ligero de la captura: el plan nombraba `journal-capture.py`, que es el de SessionEnd; se separa para no cargar la política de la cola en cada turno), `tests/hook-guard-delivery.test.mjs` (el caso «la confirmación de limpieza expira» necesita ahora un descendiente vivo: con el job vacío ya no hay limpieza), `tests/test_graphiti_security.py` (huella `_LAUNCHER_NODE_HASH` revisada: sin red; citas por nombre de `journal-prompt.py` y de `subagent-progress.py`), `docs/observability.md`, `docs/en/observability.md`, `docs/INTEROP.md`, `docs/en/INTEROP.md`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md` (E3: qué ejecuta cada hook), `tests/test_console_encoding.py` (modos de arranque de `journal-prompt.py` y `subagent-progress.py`: la suite de consola los descubre y faltaban; corrección posterior al commit de la tarea), `hooks/ledger-post.py` (revisión fase 3 intento 1, B-nota: `_repeated` admite el nombre del fichero de último estado), `.gitignore` (revisión fase 3 intento 2, punto 5: `.claude/.progress-last-subagent`) (añadidos por el implementer). Sin cambios en `hooks/hooks.json` ni en `interop/**`: los nombres registrados siguen siendo los mismos y el launcher elige el script.
- **Tiempo IA (ejec.)**: real 0,44h (medido)
- **Verificación**: medidas antes y después en `testing/perf.md`; `tests/test_hooks_shell.py` y las suites de hooks pasan.
- **Changelog**: Los hooks lanzan menos procesos en Windows: al terminar un subagente el estado se calcula en un solo Python y no se repite si no ha cambiado, cada turno del usuario se captura sin cargar el journal entero y ningún hook arranca un segundo Python solo para cerrar un job vacío.
- **Cerrada**: 2026-11-10

**Criterios de aceptación**
- [x] SubagentStop baja de ~9 procesos a ≤ 3.
- [x] La captura no importa `journal.py`.

RED: `tests/test_hook_processes.py` (sobre el código de partida, copiado del commit faed5b5) falló con 4 failed: UserPromptSubmit carga journal.py; SubagentStop sin Bash dice Git Bash unavailable y no emite (x2); en Windows el supervisor se lanza como run y después close con el job ya vacío · 2026-11-10.

GREEN: `pytest tests/test_hook_processes.py` → `6 passed` (H-31: la captura escribe el turno, siembra `.gitignore` y respeta `<private>` y `captura: false` con `journal.py` sustituido por un marcador que no se ejecuta; H-30: SubagentStop sin Bash con la misma salida que `progress-report.py active`, la segunda vez en silencio y de nuevo al cambiar el ledger; H-29: el supervisor solo se lanza como `run` si el job queda vacío y como `run` + `close` con un descendiente vivo, que muere); `node --test tests/hook-runtime.test.mjs` 25/25, `hook-guard-delivery.test.mjs` 75/75, `hook-budget.test.mjs` 11/11, `opencode-plugin.test.mjs` 26/26; `test_hook_supervisor.py` 15, `test_journal.py` 192 + 10 skipped, `test_journal_selection.py` 68, `tests/test_hooks_shell.py -k "subagent or capture or prompt or journal or supervis"` 18, `test_native_guard_launcher.py` 5, `test_agent_activity_store.py` 239 + 1 skipped, `test_hooks_config.py` 4, `test_bench_hooks.py` 28, `tests/test_graphiti_security.py` 126 passed; `scripts/bench-session-end.py --assert-p95-ms 100 --assert-p99-ms 300` → p95 19,45 ms, p99 24,25 ms; `export-interop.py --check` → `92 ficheros al día`; `lint_plugin.py` 0 errores. Medida (Job Object, 5 eventos tras uno de calentamiento, mediana, `.venv` cuenta 2 procesos por Python): SubagentStop 26 → 4 procesos y 2,76 → 1,26 s con la misma primera salida; UserPromptSubmit 7 → 4 y 1,36 → 0,99 s; SessionEnd 7 → 4 y 1,08 → 0,91 s. Decisiones: la marca `JOB_EMPTY` (bit 24 del código de salida) solo la pone el supervisor tras comprobar que su job no tiene otro proceso; un código de negocio fuera de 0-255 pasa a 1 para que nadie la imite; el debounce de SubagentStop comparte `.progress-last` con la línea del ledger (no se repite lo que el usuario acaba de ver) · 2026-11-10.

RED fix1: `tests/test_hook_processes.py -k fix1` falló con 5 failed: B4 un prompt de 3 MiB se descarta y uno con un byte UTF-8 inválido también; B5 `with_empty_job(0xC0000005)` devuelve 1; B-nota SubagentStop se calla porque `.progress-last` ya tiene la línea del ledger; A6 FLOWS ES/EN sin `journal-prompt.py` ni `subagent-progress.py` · 2026-11-10.

GREEN fix1: `pytest tests/test_hook_processes.py tests/test_hook_supervisor.py` → `26 passed` (B4: la captura lee el payload entero con reemplazo y `capture` recorta el turno a 4.000 caracteres; B5: solo un código dentro del rango de la marca pasa a 1, el resto se conserva y la marca solo se añade a 0..255 tras comprobar el job; B-nota: SubagentStop guarda su último estado en `.claude/.progress-last-subagent`, la línea del ledger ya no lo calla; A6: FLOWS ES/EN nombran `journal-prompt.py` y `subagent-progress.py` con su debounce); A2: `pytest tests/test_hooks_shell.py` completo, solo y con `timeout 1800` → `79 passed in 307.34s`; `test_console_encoding.py` completo 763 passed y 4 failed por el comentario no ASCII que fix1 dejó en `runtime-supervisor.py`, ya en ASCII (e3ddfb2; `-k runtime-supervisor` pasa), `test_journal.py -k "capture or captura or rotar or private"` 44 + 3 skipped, `test_ledger_post.py` 20 + 1 skipped, `node --test tests/hook-guard-delivery.test.mjs` 75/75, `tests/test_graphiti_security.py` 126 (huella nueva de `hooks/ledger-post.py`, sin red). A3: el criterio «≤ 3 procesos» se cumple medido con un Python normal (`C:/laragon/bin/python/python-3.13/python.exe`, mismo arnés de Job Object): SubagentStop 22 → 3, UserPromptSubmit 5 → 3, SessionEnd 5 → 3; las cifras de 26 → 4 y 7 → 4 eran con el Python del `.venv`, que añade un proceso redirector por intérprete. Tiempo de la corrección: 0,05h (medido, `plugin-audit-remediation/T-14-fix1`) · 2026-11-10.

RED fix2: `tests/test_hook_processes.py -k fix2` falló con 3 failed: `git check-ignore .claude/.progress-last-subagent` sale 1; la captura redacta los 6.291.414 caracteres del turno entero; la fila de UserPromptSubmit de observability nombra `journal.py capture` · 2026-11-10.

GREEN fix2: `pytest tests/test_hook_processes.py` → `14 passed` (5: `.claude/.progress-last-subagent` en `.gitignore`, `git check-ignore` sale 0; 6: se redacta una ventana de 4.000 + 16 KiB caracteres —más que cualquier secreto de una pieza— y después se corta a 4.000, así que un secreto que cruza el corte se redacta entero; `<private>` se sigue mirando en el texto completo; lectura con tope de 32 MiB; con un turno de 6 MiB lleno de `password=` y `ghp_…` ningún secreto queda en el log; 9: observability ES/EN nombran `journal-prompt.py`); `test_console_encoding.py -k "fix or journal-prompt"` y `test_journal.py -k "capture or captura or rotar or private or recort"` 44 + 3 skipped pasan. No reproduje los 8,4 s de 2 MiB de la revisión con los patrones probados (`redactar` de 2 MiB tardó entre 0,5 y 1,4 s aquí), pero el coste era proporcional al turno entero y ahora no lo es. Tiempo: 0,03h (medido, `plugin-audit-remediation/T-14-fix2`) · 2026-11-10.

RED fix3: `tests/test_hook_processes.py -k fix3` falló con 3 failed: con cinco PEM, relleno y un sexto PEM que empieza en el carácter 18.885 se guardan `-----BEGIN PRIVATE KEY-----` y su base64; un `Bearer` y un `password=` cortados en el borde de la ventana quedan visibles · 2026-11-10.

GREEN fix3: `pytest tests/test_hook_processes.py` → `18 passed` (1, CWE-532: la ventana se amplía, duplicándose, hasta que lo redactado llegue a 4.000 + 16 KiB caracteres, se agote el texto o se alcance `REDACCION_TOPE` = 1 MiB; en ese último caso se descartan los últimos 16 KiB redactados; en los tres casos lo guardado es igual a redactar el turno entero y cortar a 4.000; 10: `test_fix2_6` mide ahora los caracteres que pasan por `redactar` en vez de un tope de tiempo; 7: `test_fix3_7_un_turno_de_31_mib_se_captura_recortado` fija el tope de 32 MiB —TDD n/a: test de guarda escrito sobre el comportamiento ya correcto—). Por encima del tope el turno se omite sin dejar rastro: el contrato de UserPromptSubmit prohíbe stdout y stderr (el stdout es contexto y el exit 2 borra el prompt), y sin leer el JSON no hay `session_id` ni log de la sesión donde escribir; queda justificado, no se añade la línea. `test_journal.py -k "capture or captura or rotar or private or recort"` 44 + 3 skipped. Tiempo: 0,03h (medido, `plugin-audit-remediation/T-14-fix3`) · 2026-11-10.

RED fix3 (verificación del orquestador): `tests/test_hook_processes.py::test_fix3_1_pem_largo_sin_end_en_la_ventana_no_deja_ver_el_begin` falló con 1 failed: con `"x " * 1500` y un PEM de ~40 KB de base64 el END queda fuera de la ventana, `redactar` no encoge el texto y lo guardado muestra `-----BEGIN PRIVATE KEY-----` y ~1.000 caracteres del cuerpo · 2026-11-10.

GREEN fix3 (verificación del orquestador): `pytest tests/test_hook_processes.py` → `19 passed`: un BEGIN sin su END en lo guardado se sustituye, desde ahí hasta el final, por el marcador de redacción (`_sin_pem_abierto`); `test_journal.py` completo pasa, con `test_standalone_fallback_capture_redacts_before_clip[unterminated-pem]` esperando ahora el marcador en vez de la cabecera visible (contrato nuevo, más estricto). El arnés `orq_fix3.py` reimplementa el bucle de la ventana y por eso sigue dando «BEGIN visible»; el código real lo cubre el test · 2026-11-10.

### T-15 — Panel y consola sin bloqueos

- **Estado**: completado
- **Descripción**: H-32, H-33, H-34 y menores. Panel servido con hilos acotados y progreso con caché por firma; `native-sessions` solo en Sesiones o a demanda; `runtimes` con caché; plazo en `leerResumen`.
- **Archivos**: `skills/plugin-panel/scripts/serve_panel.py`, `skills/plugin-panel/scripts/console_service.py`, `skills/plugin-panel/scripts/console_common.py`, `skills/plugin-panel/assets/*.js`, tests del panel y de la consola (`tests/test_panel_console_perf.py`, nuevo), `skills/plugin-panel/scripts/console_snapshots.py` (`peek`: la última lectura sin lanzar el cálculo), `skills/plugin-panel/scripts/control_center.py` (ruta `native-sessions/cached`), `tests/console_fixture_server.py`, `tests/e2e/control-center.mjs` (los dobles del fixture y del e2e aceptan la ruta nueva), `docs/PLUGIN-PANEL.md`, `docs/en/PLUGIN-PANEL.md`, `skills/plugin-panel/references/control-center.md` (E3: cómo se refrescan progreso, inventario externo y runtimes) (añadidos por el implementer).
- **Tiempo IA (ejec.)**: real 0,14h (medido)
- **Verificación**: sonda en vivo antes y después (`testing/perf.md`); tests del panel y de la consola pasan.
- **Changelog**: El panel servido ya no recalcula el progreso en cada sondeo ni deja esperando al resto de rutas mientras lo hace, y la consola solo arranca los CLI de sesiones nativas en la vista Sesiones, cada vez más espaciados si nada cambia, recuerda los runtimes instalados y da plazo a la lectura del resumen de revisiones.
- **Cerrada**: 2026-11-10

**Criterios de aceptación**
- [x] `runtimes` cacheado; `native-sessions` no relanza CLIs fuera de Sesiones.
- [x] Una petición lenta no bloquea las demás.

RED: `tests/test_panel_console_perf.py` falló con 6 failed: el progreso se recalcula en los 3 sondeos sin cambios; con un progreso de 4 s api/progress tarda 4,08 s y la portada 3,88 s; native_sessions no acepta discover; los descubrimientos van cada 15 s (0, 15, 30, 45…) sin espaciarse; sibling recarga console_transport.py en cada llamada; leerResumen sin signal ni plazo · 2026-11-10.

GREEN: `pytest tests/test_panel_console_perf.py` → `7 passed` (H-32: firma por `lstat` de cada `tasks.md` —sin mirar dentro de una carpeta enlazada—, recálculo en un hilo y `tiene_plan` aplicado al servir; H-33: `discover=False` sirve lo observado sin lanzar nada y los descubrimientos caen en 0, 15, 45 y 105 s con el mismo resultado; H-34: `runtimes` busca los ejecutables una vez cada 30 s y `sibling` carga cada hermano una vez, salvo `build_panel.py`, que sigue siendo nuevo en cada catálogo; menor: `leerResumen` aborta a los 4 s); las 44 suites `tests/test_panel_*`, `test_console_*` y `test_control_center_http.py` pasan (p. ej. `test_panel_server.py` 137 + 2 skipped, `test_panel_plan_ui.py` 124, `test_console_encoding.py` 760 tras registrar los dos scripts de T-14, `test_console_service.py` 5) salvo `test_console_transport.py::test_eof_closes_the_owned_process_instead_of_leaving_a_background_worker`, que falla igual sobre el código de partida (preexistente en Windows, fuera de alcance); `lint_plugin.py` 0 errores; `export-interop.py --check` → `92 ficheros al día`. Medida en proceso (servidor efímero en el puerto 0 sobre p68, reloj simulado para la consola): 10 sondeos sin cambios 10 → 0 recálculos y 0,638 → 0,018 s de mediana por sondeo; `api/progress` tras un cambio 0,639 → 0,022 s y la portada durante el recálculo 0,583 → 0,005 s; misma proyección (SHA `a4495396d688` sin `observed_at`); 10 sondeos de `runtimes` 1,24 → 0,21 s y 10 → 1 carga de `console_transport.py`; en 120 s de sondeo cada 2 s, CLIs lanzados desde Inicio 24 → 0 y desde Sesiones 24 → 12. Decisión: recálculo en segundo plano (como la cartera) en vez de `ThreadingHTTPServer`, para no abrir concurrencia en las rutas que escriben revisiones; e2e de la consola (Playwright) no ejecutado aquí · 2026-11-10.

RED fix1: `tests/test_panel_console_perf.py -k fix1` falló con 2 failed: B3 `console-dom.js` no tiene `sessionCountLabel` e Inicio da el recuento de gestionadas como total; A4 con un plan lento de 4 s la portada tarda 4,0 s · 2026-11-10.

GREEN fix1: `pytest tests/test_panel_console_perf.py` → `9 passed` (A4: `PanelServer` con hilos acotados —4 a la vez, el bucle de aceptación espera a un hueco—, los POST y las rutas de revisión siguen en serie bajo `escritura` y la primera versión del progreso se calcula al arrancar, como la cartera; B3: con el inventario externo sin consultar, Inicio muestra «≥ N»); las 44 suites `tests/test_panel_*`, `test_console_*` y `test_control_center_http.py` pasan con los hilos (p. ej. `test_panel_server.py` 137 + 2 skipped, `test_panel_review_server.py` 67, `test_panel_review_panel_server.py` 37, `test_panel_plan_ui.py` 124), salvo el preexistente `test_console_transport.py::test_eof_closes…`, que también falla en el código de partida. A5: `tests/e2e/control-center.mjs` no se puede ejecutar en esta máquina: necesita el módulo `puppeteer` (`CONSOLE_BROWSER_MODULE`, no instalado) y un servidor de fixture arrancado a mano (`CONSOLE_TEST_URL`), que las restricciones de la fase excluyen; `node --check` pasa y `node --test` sale con los 9 casos saltados. Queda como deuda en T-21. Tiempo de la corrección: 0,12h (medido, `plugin-audit-remediation/T-15-fix1`; la ventana incluye también la corrección de la barra de estado de T-16) · 2026-11-10.

RED fix2: `tests/test_panel_console_perf.py -k fix2` falló con 1 failed: con dos planes nuevos abiertos a la vez `plan_ids` pierde uno de los dos ids · 2026-11-10.

GREEN fix2: `pytest tests/test_panel_console_perf.py` → `11 passed` (7: `plan_page` actualiza la caché de páginas y `plan_ids` bajo `_planes_lock`; 4: `test_fix2_4_la_deuda_del_e2e_de_la_consola_queda_en_t21` vigila la deuda A5 como las otras de T-21); `test_panel_server.py` 137 + 2 skipped, `test_panel_fix2.py` 18, `test_panel_plan_ui.py` y `test_panel_review_panel_server.py` pasan. Tiempo: 0,03h (medido, `plugin-audit-remediation/T-15-fix2`) · 2026-11-10.

TDD n/a (revisión intento 3, punto 6): `test_fix2_4_la_deuda_del_e2e_de_la_consola_queda_en_t21` no tuvo rojo: vigila una deuda ya escrita en T-21 (pasaba en b0182bc), igual que los tests de deuda de la Fase 1. Los puntos 8 y 9 del intento 3 (deuda de la ruta 8.3 y decisión sobre la constitución) se registran en T-21; RED de `tests/test_statusline_cache.py::test_fix3_8_la_deuda_de_la_ruta_corta_8_3_queda_en_t21`: falló con `statusline-render.py` ausente del `Archivos` de T-21. Tiempo: 0,02h (medido, `plugin-audit-remediation/T-15-fix3`) · 2026-11-10.

### T-16 — Scripts de las puertas más rápidos

- **Estado**: completado
- **Descripción**: H-35 a H-39. `isdir` por patrón en scope-check; ledger-archive y ledger-lint sin bucles carácter a carácter; `sin_comentario` con atajo; lint en proceso en task-brief; clave de caché de la statusline.
- **Archivos**: `agent-kits/shared/scope-check.py`, `agent-kits/shared/ledger-archive.py`, `agent-kits/shared/ledger-lint.py`, `skills/code-health/scripts/code-health.py`, `agent-kits/shared/task-brief.py`, `statusline/roadmap-statusline.sh`, sus tests (`agent-kits/shared/test_scope_check.py`, `agent-kits/shared/test_ledger_archive.py`, `skills/code-health/scripts/test_code_health.py`, `agent-kits/shared/test_task_brief.py`, `tests/test_statusline_cache.py`), `skills/jira-sync/scripts/jira-flow.py` (copia declarada del bloque `secciones_revision` en `copias.json`: cambia a la vez que la de ledger-lint y la de task-brief), `docs/observability.md`, `docs/en/observability.md` (E3: qué cubre la caché de la barra de estado) (añadidos por el implementer).
- **Tiempo IA (ejec.)**: real 0,21h (medido)
- **Verificación**: tiempos antes y después en `testing/perf.md`; mismas salidas sobre los ledgers del repo.
- **Changelog**: Las puertas tardan menos con los mismos resultados: scope-check mira el disco una vez por patrón, el archivado de ledgers grandes y code-health ya no recorren cada carácter, el brief de una tarea valida el ledger sin lanzar otro Python y la barra de estado solo arranca Python cuando cambia el roadmap.
- **Cerrada**: 2026-11-10

**Criterios de aceptación**
- [x] Salidas idénticas; tiempos medidos más bajos.

RED: `test_scope_check.py -k h35 + test_ledger_archive.py -k h36 + test_code_health.py -k h37 + test_task_brief.py -k h38 + tests/test_statusline_cache.py` falló con 15 failed: 126 isdir para 4 patrones; bloques_revision enumera 126.502 caracteres; split_fila_md hace 1.981 llamadas nativas en una fila de ~2.000; sin_comentario indexa 232 veces una línea sin marcador; el brief lanza ledger-lint.py como subproceso; la statusline lanza Python al cambiar el coste y no reutiliza la caché en los 9 casos de forma · 2026-11-10.

GREEN: los cinco ficheros con sus tests nuevos pasan (`test_scope_check.py` 32, `test_ledger_archive.py` 25, `test_code_health.py` 33, `test_task_brief.py` 94, `tests/test_statusline_cache.py` 27; equivalencias: `split_fila_md` y `bloques_revision` iguales a la versión anterior en todas las filas de tabla y secciones de los 68 ledgers del repo, y `sin_comentario` igual en más de 1.000 líneas reales de cinco ficheros), más `test_copias_declaradas.py` 31 (las tres copias de `secciones_revision` siguen idénticas), `test_scope_check_commit_selection.py` 22 + 2 skipped + 27 subtests, `…_deep.py` 4, `tests/test_ledger_lint.py` 9, `test_ledger_single_parser.py` 10, `test_ledger_write.py` 33 + 2 skipped, `test_jira_flow.py` 74, `test_audit_jira.py` 4, `test_review_jira_owner.py` 12, `test_audit_briefs.py` 11, `test_progress_report.py` 45, `tests/test_hooks_shell.py -k statusline` 14 passed. Medida (cada ejecución un proceso nuevo, calentamiento + 3, mediana; mismo SHA de salida antes y después): scope-check de esta iniciativa 1,69 → 0,94 s; ledger-archive en seco del ledger de 519 KB 2,70 → 1,16 s; ledger-lint del mismo 0,21 → 0,21 s (sin cambio apreciable: lo caro era el archivado); code-health del árbol del repo 11,79 → 6,59 s; task-brief de T-16 3 → 2 procesos lanzados y 1,12 → 1,12 s (el que queda es knowledge-find); barra de estado en 7 turnos con el coste cambiando 7 → 1 Python y 1,49 → 0,62 s por refresco. Decisiones: la barra de estado solo pinta en Bash lo que Python imprimiría igual (nombre ASCII sin comillas ni barra invertida, una sola clave, número posicional ≥ 0,0001 con el texto más corto, como lo escriben `JSON.stringify` y `repr`); el resto vuelve a Python en ese refresco. La primera versión limitaba la parte decimal a 15 cifras y un coste sumado en coma flotante (0,43000000000000005) caía siempre a Python: lo destapó la medida · 2026-11-10.

RED fix1: `tests/test_statusline_cache.py -k "fix1 or h39"` falló con 11 failed: una entrada con `rate_limits.*.used_percentage`, `used_percentage: null` o la clave en otro objeto lanza Python en cada refresco, también idéntica; con solo `rate_limits.five_hour.used_percentage` Bash pinta `ctx 77%` · 2026-11-10.

GREEN fix1: `pytest tests/test_statusline_cache.py` → `32 passed` (D1+B2: cada campo se lee dentro de su grupo de primer nivel —`model.display_name`, `cost.total_cost_usd`, `context_window.used_percentage`—; `null` no pinta nada; si Bash no puede decidir, Python pinta esos campos con la entrada en la clave de caché, como en b2621b0, y la entrada idéntica vuelve a acertar); `tests/test_hooks_shell.py -k statusline` 14, `test_console_encoding.py -k statusline` 8. Barra de estado en 7 turnos con el coste cambiando: 7 → 1 Python, misma salida (`3dfebc8547c6`). A1: medido aislando el paso del lint (mediana de 5): subproceso `ledger-lint.py` 0,410 s → `lint()` en proceso 0,014 s, los −0,4 s por subagente que pedía H-38; el brief completo sigue en ~1,1 s porque lo domina la consulta de memoria (`knowledge-find.py`, subproceso, fuera de H-38). Con esa medida el criterio «tiempos medidos más bajos» se cumple para el paso que cambia la tarea · 2026-11-10.

RED fix2: `tests/test_statusline_cache.py -k "fix2 or fix1"` falló con 5 failed: el payload real (`context_window.current_usage` como objeto) lanza Python en cada refresco; `{"model":{"id":"a}","display_name":"X"}}` y `{"cwd":"C:/a}b","agent":{"model":{…}}}` pintan algo distinto de Python; la clave anidada en `agent.model` y `current_usage` dentro del grupo caen a Python · 2026-11-10.

GREEN fix2: `pytest tests/test_statusline_cache.py` → `38 passed` (un escáner de miembros JSON en Bash: recorre los miembros de un objeto, salta cadenas con sus escapes al contar llaves, admite objetos anidados dentro del grupo y, ante una clave repetida o con escapes, una cadena sin cerrar o algo que no sigue, deja que Python pinte esos campos con la entrada en la clave de caché; las cuatro entradas con llaves en cadenas dan la misma salida que Python; los dos casos del test de fix1 que daban la anidada y `current_usage` por lentos pasan al atajo); `tests/test_hooks_shell.py -k statusline` 14, `test_console_encoding.py -k statusline` 8. Barra de estado con el payload real (con `current_usage`) en 7 turnos con el coste cambiando: 7 Pythons y 1,22 s por refresco con fix1 → 1 Python y 0,59 s, misma salida (`3dfebc8547c6`). Tiempo: 0,27h (medido, `plugin-audit-remediation/T-16-fix2`) · 2026-11-10.

RED fix3: `tests/test_statusline_cache.py -k fix3` falló con 7 failed: una entrada de 24 KB de escapes no termina en menos de 1 s con la caché caliente; `0.50000000000000001`, `1.49999999999999999` y `0.12500000000000001` se redondean en Bash distinto que en Python; con coma final, texto tras el objeto o el escape `\x41`, Bash pinta campos y Python no · 2026-11-10.

GREEN fix3: `pytest tests/test_statusline_cache.py` → `45 passed` antes del test de deuda (2: por encima de 8 KB no se escanea y pinta Python con la entrada en la clave; una sola pasada lee los tres grupos y cada cadena es un solo token; 3: con más de 15 dígitos significativos y las cifras tras la posición de redondeo cerca de la mitad —5 o 49…—, o más de 17, pinta Python; 4: coma final, texto tras el objeto y escapes inválidos caen a Python; sin `declare -A`, compatible con Bash 3.2); `tests/test_hooks_shell.py -k statusline` 14, `test_console_encoding.py -k statusline` 8. Payload real en 7 turnos: 1 Python, misma salida (`3dfebc8547c6`). Tiempo: 0,07h (medido, `plugin-audit-remediation/T-16-fix3`) · 2026-11-10.

## Fase 4 — Consumo de tokens

**Estado**: completado

Medidas de tamaño antes y después (separadas del consumo observado, que no se midió): [`testing/tokens.md`](testing/tokens.md) (borrador del implementer en el scratchpad de la sesión; lo copió el orquestador).

### T-17 — Capacidades e integraciones una vez por ciclo

- **Estado**: completado
- **Descripción**: H-41 y H-42. Si el ledger, el brief o el prompt ya traen las capacidades o «sin integraciones», el rol no lo recalcula.
- **Archivos**: `agents/*.md`, `agent-kits/shared/capability-check.md`, `agent-kits/shared/project-integrations.md`, `commands/dev-cycle.md`, `interop/**`, `tests/fixtures/dev-cycle-modular-replacements.json`, `agent-kits/shared/task-brief.py` (el brief dice que no se relea el fragmento), `tests/test_once_per_cycle_context.py` (test nuevo) (añadidos por el implementer).
- **Tiempo IA (ejec.)**: real 0,06h (medido)
- **Verificación**: tamaño de carga por despacho antes y después (`context-footprint.py`); interop al día.
- **Changelog**: Los roles ya no releen la selección de capacidades ni las integraciones en cada despacho: el orquestador las resuelve una vez por ciclo y el brief lo indica.
- **Cerrada**: 2026-11-10

**Criterios de aceptación**
- [x] Un despacho con capacidades en el brief no lee `capability-check.md`.

RED: `tests/test_once_per_cycle_context.py` falló con 18 failed: ninguno de los 10 agentes dice que una selección ya presente impide leer `capability-check.md`/ejecutar `capability-route.py`, los 6 agentes con eventos externos no admiten «sin integraciones», `dev-cycle.md` no resuelve las dos cosas «una vez por ciclo» y el brief no lo dice · 2026-11-10.

GREEN: `tests/test_once_per_cycle_context.py` 18 passed; `test_dev_cycle_split.py` 10 passed (el párrafo de `dev-cycle.md` se registra con su motivo en `dev-cycle-modular-replacements.json`; ahorro de la vía rápida 6158 → 6146 ≥ 6000); `test_task_brief.py` 94, `test_knowledge_prompt_split.py` 5, `test_token_estimates.py` 13, `test_token_efficiency_distribution.py` 2, `test_source_snapshot.py` 33 + 1 skipped, `test_context_footprint.py` 15, `tests/test_export_interop.py` 50; `agents/evaluator.md` 15.499 bytes (≤ 15.513, CA-22: se compactaron dos frases de estilo del propio evaluator para compensar); `export-interop.py --check` 92 al día; lint 0 errores; evals 0 errores. Medida de tamaño (caracteres, no consumo observado; ver el borrador de `testing/tokens.md` en el scratchpad de la sesión): cada agente +139…+296 caracteres, `project-integrations.md` +107, `dev-cycle.md` +48; lo que se evita por despacho que ya trae la selección es `capability-check.md` (5.637 bytes ≈ 1.400 tokens) y su ejecución de `capability-route.py`, y con «sin integraciones» `project-integrations.md` (5.306 ≈ 1.300 tokens) y `integration-route.py`; en un bucle de revisión de 12 despachos ≈ 16.900 tokens de lectura evitados frente a ≈ 900 añadidos · 2026-11-10.

GREEN fix2 (`context-footprint.py --project <árbol> --file …`, `cb6fb40` → `b5829b9`, caracteres en LF): `agents/analyst.md` 11635 → 12071, `architect.md` 15790 → 16084, `documenter.md` 18032 → 18468, `evaluator.md` 14921 → 15130 (15429 bytes), `implementer.md` 29396 → 28842, `knowledge-curator.md` 12920 → 13214, `nemesis.md` 15449 → 15813, `planner.md` 21420 → 21856, `qa.md` 19271 → 19777, `reviewer.md` 8495 → 8649, `agent-kits/shared/project-integrations.md` 5199 → 5306, `capability-check.md` 5491 → 5561, `commands/dev-cycle.md` 28708 → 29019. Salida completa en `testing/tokens.md`.

### T-18 — Lo opcional fuera de la carga por defecto

- **Estado**: completado
- **Descripción**: H-43, H-44 y H-49. Revisión visual del plan en su propia referencia; notas de `/doctor` en `docs/`; scope-check imprime su propio remedio.
- **Archivos**: `agent-kits/dev-cycle/references/phase2-planning.md`, `agent-kits/dev-cycle/references/phase2-plan-review.md`, `commands/dev-cycle.md` (la ruta a la referencia de la fase 2), `commands/doctor.md`, `docs/reference/doctor.md`, `docs/en/reference/doctor.md` (espejo EN), `agents/implementer.md`, `skills/adversarial-review/SKILL.md`, `agent-kits/shared/scope-check.py`, `interop/**`, tests de split y de plan-review (`tests/test_dev_cycle_split.py`, `tests/test_plan_review_caller.py`, `tests/installer.test.mjs`, `tests/test_knowledge_services.py`, `agent-kits/shared/test_scope_check.py`, `tests/test_doctor_notes_in_docs.py` nuevo) (añadidos por el implementer).
- **Tiempo IA (ejec.)**: real 0,16h (medido)
- **Verificación**: `context-footprint.py` antes y después; tests de split y de recetas de plan-review pasan.
- **Changelog**: El flujo completo de `/dev-cycle` y `/doctor` cargan mucho menos texto por defecto: la revisión visual del plan y las notas internas de `/doctor` viven en su propia referencia y solo se leen si hacen falta, y scope-check imprime su remedio.
- **Cerrada**: 2026-11-10

**Criterios de aceptación**
- [x] El flujo completo y `/doctor` cargan menos texto por defecto con los mismos contratos.

RED: `tests/test_dev_cycle_split.py` + `tests/test_doctor_notes_in_docs.py` + `agent-kits/shared/test_scope_check.py -k h49` fallaron con 4 + 2 + 2 failed: `phase2-plan-review.md` no existe y `phase2-planning.md` carga 18.136 caracteres (tope 6.000) con las recetas de revisión visual dentro; `commands/doctor.md` mide 16.626 caracteres (tope 8.000) sin puntero a `docs/reference/doctor.md` ni espejo EN; los avisos ⚠️ de scope-check no traen remedio y el DoD del implementer y la §0 de la revisión repiten su explicación (> 700 caracteres) · 2026-11-10.

GREEN: `test_dev_cycle_split.py` 11 passed (las recetas Bash/PowerShell siguen byte a byte idénticas en su nueva referencia; la ruta a ella solo se nombra desde `phase2-planning.md`), `test_plan_review_caller.py` 13 + 13 skipped (sin `pwsh`: igual que antes), `test_review_jira_owner.py` 12, `test_plugin_root_resolution.py` 16, `test_doctor_notes_in_docs.py` 2, `test_knowledge_services.py -k gap112` 1 (lee ahora `docs/reference/doctor.md`), `test_scope_check.py` 34 (incluye los 2 de H-49); `export-interop.py --check` 92 al día; lint 0 errores (16 avisos, los mismos); evals 0 errores. Medida de tamaño (caracteres, no consumo observado; el borrador de `testing/tokens.md` está en el scratchpad de la sesión): `phase2-planning.md` 18.136 → 3.034 (−15.102 ≈ −3.775 tokens por flujo completo, la revisión visual pasa a 15.536 y se lee solo si se pide), `commands/doctor.md` 16.626 → 5.491 (−11.135 ≈ −2.784 tokens por `/doctor`), `agents/implementer.md` −1.060 (≈ −265) y `adversarial-review/SKILL.md` −916 (≈ −229) por la explicación duplicada de los avisos. Ahorro de la vía rápida 6.146 (≥ 6.000). No se registra reemplazo para el párrafo de la fase 2 de `dev-cycle.md` porque no estaba en la línea base de párrafos (la prueba exige que lo registrado esté en ella) · 2026-11-10.

GREEN fix2 (`context-footprint.py`, `cb6fb40` → `b5829b9`, caracteres en LF): `agent-kits/dev-cycle/references/phase2-planning.md` 18136 → 3034, `phase2-plan-review.md` 0 → 15536, `commands/doctor.md` 16626 → 5700, `agent-kits/shared/doctor-reference.md` 0 → 12129, `skills/adversarial-review/SKILL.md` 18972 → 18104, `agents/implementer.md` 29396 → 28842; flujo completo de `/dev-cycle` 56363 → 41572. Salida completa en `testing/tokens.md`.

### T-19 — Ruta del kit resuelta una vez

- **Estado**: completado
- **Descripción**: H-45. SessionStart y el brief inyectan la ruta absoluta del bundle activo; las piezas la usan antes de buscar.
- **Archivos**: `hooks/session-context.py`, `agent-kits/shared/task-brief.py`, `agents/*.md`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `interop/**`, tests (`tests/test_kit_path_injection.py` nuevo, `tests/test_session_context.py`, `tests/test_graphiti_security.py` huella de `session-context.py`, `agent-kits/shared/test_task_brief.py`) (añadidos por el implementer).
- **Tiempo IA (ejec.)**: real 0,13h (medido)
- **Verificación**: el bloque de sesión trae la ruta; test de resolución pasa.
- **Changelog**: El bloque de arranque de sesión y el brief de cada tarea traen la ruta del kit del bundle activo, así que un subagente sin `CLAUDE_PLUGIN_ROOT` ya no ejecuta el `find` de resolución.
- **Cerrada**: 2026-11-10

**Criterios de aceptación**
- [x] Un subagente sin `CLAUDE_PLUGIN_ROOT` no necesita `find`.

RED: `tests/test_kit_path_injection.py` falló con 3 failed: el bloque de `SessionStart` no trae ninguna línea `SHAREDKIT=`, el brief de `task-brief.py` tampoco (un bash sin `CLAUDE_PLUGIN_ROOT` y sin bundle en el directorio no tiene de dónde sacar el kit) y `docs/CONVENTIONS.md`/`docs/en/CONVENTIONS.md` no documentan la ruta inyectada · 2026-11-10.

GREEN: `tests/test_kit_path_injection.py` 3 passed (el bloque de sesión lleva UNA línea `Kit activo: SHAREDKIT="<ruta>"` la primera; el brief lleva `Kit: SHAREDKIT="<ruta>"` en su cabecera; un bash sin `CLAUDE_PLUGIN_ROOT`, en un directorio sin bundle, comprueba `[ -f "$SHAREDKIT/ledger-lint.py" ]` con solo esa ruta → `resolved`); `tests/test_session_context.py` 49 passed (el oráculo del shell retirado ya no conoce la línea: la prueba de paridad la quita de la salida nativa y compara el resto byte a byte); `test_task_brief.py` 94 (una prueba al borde del tope de 10.000 caracteres bajó su memoria simulada de 2.300 a 2.150 porque el brief ahora abre con ~100 caracteres que el presupuesto auxiliar no puede recortar); `tests/test_graphiti_security.py -k` de huellas 6 passed con la huella de `hooks/session-context.py` renovada (T-19, H-45: línea local, sin red); `export-interop.py --check` 92 al día, lint 0 errores, evals 0 errores. La ruta se calcula en ejecución (nunca queda en un fichero versionado) con barras `/` y entre comillas, porque una ruta con espacios (OneDrive) rompe el valor sin ellas. Medida: el coste de la línea es ≈ 150 caracteres por arranque de sesión y por brief, a cambio de evitar el `find` de la regla 5 de CONVENTIONS (7,7 s por bloque medido en la auditoría, una llamada de herramienta menos por bloque). Decisión: la instrucción de usar la ruta vive en la propia línea inyectada y en `CONVENTIONS.md`, no en los diez `agents/*.md`: `agents/evaluator.md` está a 14 bytes de su techo (CA-22) y cada agente ya recibe el brief o el contexto con la línea · 2026-11-10.

### T-20 — OpenCode e interop sin contexto repetido

- **Estado**: completado
- **Descripción**: H-46 y H-47. La caché de contexto de OpenCode se invalida por firma; la línea de delegación solo en agentes que delegan.
- **Archivos**: `hooks/opencode-plugin.js`, `scripts/export-interop.py`, `interop/**`, `tests/test_export_interop.py`, tests del adaptador de OpenCode (`tests/opencode-plugin.test.mjs`), `docs/INTEROP.md`, `docs/en/INTEROP.md` (E3: qué cubre la caché de contexto de OpenCode) (añadidos por el implementer)., `agent-kits/shared/outbox.py` (orden cronológico de la cola), `hooks/session-context.py` (modo `drain`), `tests/test_f4fix2_misc.py`, `tests/test_f4fix3_kit.py` (fix2/fix3)
- **Tiempo IA (ejec.)**: real 0,11h (medido)
- **Verificación**: tests del adaptador y de interop pasan; `--check` al día.
- **Changelog**: En OpenCode el contexto de sesión no se recompone mientras no cambie lo que cita, ni en los cierres de turno, y en Codex y OpenCode solo los agentes que pueden delegar reciben la instrucción de delegar.
- **Cerrada**: 2026-11-10

**Criterios de aceptación**
- [x] Sin reinyección mientras la firma no cambie.
- [x] Ningún agente sin `Agent` recibe la instrucción de delegar.

RED: `tests/opencode-plugin.test.mjs` (el test de la caché reescrito por firma) + `tests/test_export_interop.py -k delegation` fallaron con 1 + 1 failed: tras un `bash` completado que no toca los árboles canónicos el adaptador recomponía el contexto (`context 2` en vez de `context 1`) por la invalidación por evento y por el TTL de 30 s; y los 9 agentes sin `Agent` en `tools` (en OpenCode con `subagent: deny`) recibían el bloque «Delegar en otro agente» con el mapa de roles, en Codex y en OpenCode · 2026-11-10.

GREEN: `node --test tests/opencode-plugin.test.mjs` 26 pass (read, bash, prompt con su log de captura y +1 h de reloj dejan el contexto en `context 1`; un cambio en roadmap, memoria o `dev.json` lo recompone; un cambio durante el cálculo impide guardarlo), `hook-runtime.test.mjs` 25, `hook-guard-prefilter.test.mjs` 23, `native-guard-adapter.test.mjs` 3; `tests/test_export_interop.py` 51 passed (el test nuevo exige el bloque de delegación solo con `Agent` en `tools`: nemesis lo conserva), `test_console_opencode.py` 8, `test_native_prefilter_parity.py` 16, `test_codex_command_transport.py` 22 + 1 skipped; `export-interop.py --check` 92 al día, lint 0 errores, evals 0 errores. Medida de tamaño (caracteres): el bloque de delegación sale de 9 agentes por runtime, −6.264 bytes en los 10 `.toml` de Codex y −5.526 en los 10 `.md` de OpenCode (≈ 690 bytes ≈ 170 tokens por despacho de un agente sin `Agent`). Medida de recomputación (recuento, no tiempo): en la prueba antigua el prompt y el `bash` completado recomputaban el contexto (`context 2`, `context 3`) y el reloj a +31 s también (`context 8`); en la nueva, con los ficheros sin cambiar, los tres dejan `context 1`. Decisiones: la firma deja fuera `session-prompts-*.log` (volátil y nunca alimenta el contexto de sesión), se quita el TTL de 30 s porque la firma ya cubre todo lo que alimenta el contexto, y la invalidación por eventos solo queda en el flujo de cierres de ejecución, donde se escribe en la memoria · 2026-11-10.

### T-21 — Documentación alineada y menores

- **Estado**: completado
- **Descripción**: Menores de la auditoría: Lente D en `dev-cycle`, `quick-implement` y CLAUDE.md; hooks globales y ADR-023 en CLAUDE.md; consola frente a panel servido; rutas de memoria que no viajan; shells muertos; degradación sin node; `release.py` (5 manifiestos, `.MANUAL-COPY` pendiente); cookie por puerto; mapa de errores y `aria-live` de la consola. Deuda de T-15 (revisión fase 3 intento 1, A5): ejecutar `tests/e2e/control-center.mjs` con `puppeteer` y el servidor de fixture, que no se pudo correr en la máquina de la fase (`puppeteer` no instalado). Deuda anterior a la fase 3 (revisión intento 2): con la raíz del proyecto en una ruta corta 8.3 de Windows, `statusline-render.py` no escribe nunca la caché (`resolve()` expande la ruta y la compara con la corta). Decisión pendiente del usuario (revisión fase 3 intento 3, punto 9): las trazas de la Fase 3 usan el veredicto «evidenciado (medida)» para gaps de evidencia o de criterio sin test dedicado, una excepción que `docs/CONSTITUTION.md` (l. 13) no recoge; propuesta: o una línea en la constitución («un gap de evidencia o de criterio se cierra con la medida o la ejecución que lo prueba, citada en la traza») o un ADR que la registre. No se toca la constitución sin el usuario.
- **Notas**: Incluye la deuda de T-07 (revisión fase 2 intento 3, punto 12): `journal.py recover` redacta una sesión huérfana con la iniciativa vigente AL RECUPERAR y la marca `regla_iniciativa: vigente`, aunque la sesión fuera de otra iniciativa; decidir si las recuperadas tarde no llevan la marca. Incluye la deuda de T-08 (revisión fase 2 intento 1, A2): un aviso de ledger-lint para las tareas `completado` sin `RED:` ni `TDD n/a` cuando `dev.json` trae `tdd: true` (hoy solo lo comprueba la Lente A, criterio 5b). Incluye la deuda de T-05: nueva edición PDF de los manuales `docs/guides/subscription-efficiency.md` y `docs/guides/quality-playbook.md` para que digan que lite despacha al implementer nativo.
- **Archivos**: `CLAUDE.md`, `commands/*.md`, `skills/**/SKILL.md`, `docs/**`, `hooks/*.sh`, `scripts/release.py`, `skills/plugin-panel/**`, `interop/**`, tests afectados, `agent-kits/shared/statusline-render.py` (deuda de la ruta corta 8.3; revisión fase 3 intento 3, punto 8), `agent-kits/evaluator/README.md` (ruta de memoria que no viaja), `agent-kits/shared/journal.py`, `agent-kits/shared/ledger-lint.py`, `agent-kits/shared/doctor.py`, `skills/plugin-panel/**`, `docs/TOKEN-EFFICIENCY.md`, `docs/en/TOKEN-EFFICIENCY.md`, `CHANGELOG.md`, `CHANGELOG.es.md` y las pruebas de la regresión de CI (`agent-kits/shared/test_redact.py`, `tests/test_audit_journal.py`, `tests/test_memory_local_recovery.py`, `tests/test_kit_path_injection.py`, `commands/doctor.md`) (añadidos por el implementer)., `agent-kits/shared/journal-capture.py` (marcador abierto en el sobre), `agent-kits/shared/progress-report.py` (aviso de historial omitido), `docs/WORK-RESUME.md`, `docs/en/WORK-RESUME.md`, `tests/test_f4fix2_journal.py`, `tests/test_f4fix3_journal.py`, `tests/test_f4fix3_misc.py` (fix2/fix3)
- **Verificación**: lint 0 errores, evals 0 errores, interop al día, CI completa en Linux verde.
- **Tiempo IA (ejec.)**: real 0,61h (medido)
- **Changelog**: Arreglos menores de la auditoría: la documentación de revisión nombra la Lente D y la guardia global, la consola usa una cookie por puerto y avisa mejor de sus errores, release.py bloquea ante una copia manual pendiente, ledger-lint avisa de las tareas completadas sin RED y /doctor avisa si falta node.
- **Cerrada**: 2026-11-10

**Criterios de aceptación**
- [x] Los menores de la auditoría quedan corregidos o descartados con motivo en este ledger.

**Resolución de los menores y de la deuda (T-21)**

| Elemento | Resultado |
|---|---|
| Lente D en `dev-cycle`, `quick-implement` y CLAUDE.md | Corregido (`tests/test_docs_alignment_t21.py`; los párrafos cambiados se registran en `dev-cycle-modular-replacements.json`) |
| Hooks globales y ADR-023 en CLAUDE.md | Corregido (guardia global previa por identidad nativa) |
| Consola frente a panel servido | Corregido en CLAUDE.md (`/plugin-catalog --serve` abre `control_center.py`; `build_panel.py --serve` es el informativo) |
| Rutas de memoria que no viajan (LES-010, LES-012, ADR-012, ADR-019) | Corregido en `adversarial-review`, `changelog-sync`, `training-data-services` y el README del kit del evaluator: ya no citan rutas de `docs/knowledge/`. ADR-011 y ADR-017 solo aparecen como IDs sin ruta: sin cambio |
| Shells muertos (`session-context.sh`, `progress-line.sh`, `ledger-lint-warn.sh`) | **No retirados, deuda con motivo:** son el oráculo de paridad de unas 57 pruebas de `tests/test_hooks_shell.py` y de `test_session_context.py`, y sus nombres son identidades de hook en `run-hook.mjs`, `build_panel.py`, `export-interop.py` y los fixtures golden del panel; quitarlos exige reescribir esas pruebas sobre el Python nativo. Propuesta: iniciativa propia |
| Degradación sin node | Corregido: `/doctor` avisa (⚠️ con arreglo) y `docs/observability.md` + espejo EN lo documentan |
| `skill-index.py` ignora `sesion.indice: false` con BOM | Ya estaba corregido (`utf-8-sig`); comprobado: con BOM no emite nada |
| `release.py` (5 manifiestos, `.MANUAL-COPY` pendiente) | Corregido: docstring y bloqueo por copia pendiente (`tests/test_release.py`) |
| Cookie por puerto | Corregido (`ca_console_<puerto>`; `tests/test_control_center_http.py`) |
| Mapa de errores de la consola y `aria-live` | Corregido: 7 códigos con mensaje, chat `role="log"` `aria-live="polite"` (`tests/test_console_errors_and_live_region.py`) |
| Preguntas o permisos nativos pendientes solo dentro de Sesiones | **Descartado:** un indicador global es una función nueva y la spec excluye funciones nuevas; el `aria-live` de `chat-requests` los anuncia dentro de Sesiones |
| Deuda de T-15: `tests/e2e/control-center.mjs` con puppeteer | Ejecutado con `puppeteer-core` 23 (instalado en el scratchpad, fuera del repo) y Edge contra `tests/console_fixture_server.py`: 9 pasan, 0 fallan |
| Deuda: ruta corta 8.3 y `statusline-render.py` (revisión fase 3, intento 3, punto 8) | Corregido: la caché se escribe con una raíz en ruta corta 8.3; `.claude` redirigido sigue bloqueando (`tests/test_statusline_cache.py`; la prueba del enlace simbólico se omite sin privilegio en esta máquina) |
| Deuda de T-07: `journal.py recover` y `regla_iniciativa: vigente` | Decidido y corregido: las sesiones recuperadas tarde (`orphan_recovery`) no llevan la marca, así que no se citan como historial de la iniciativa vigente |
| Deuda de T-08: aviso de ledger-lint sin `RED:` ni `TDD n/a` con `tdd: true` | Corregido (aviso, nunca error; `tests/test_ledger_lint.py`) |
| Deuda de T-05: nueva edición PDF de los manuales | **No hecha, deuda con motivo:** exige la cadena de generación del PDF (diagramas y navegador) que no está disponible en esta máquina, y `check-handbook.py` ancla el PDF al markdown de `docs/guides/`; los manuales markdown ya dicen que lite despacha al implementer nativo. Queda para quien tenga esa cadena |
| Decisión pendiente del usuario: veredicto «evidenciado (medida)» frente a `docs/CONSTITUTION.md` | **Sin tocar, sigue pendiente de decisión del usuario** (línea en la constitución o ADR) |

RED: `tests/test_docs_alignment_t21.py` 4 failed, `tests/test_ledger_lint.py -k t21` 1 failed, `agent-kits/shared/test_journal.py -k t21` 2 failed, `tests/test_release.py -k t21` 2 failed, `tests/test_control_center_http.py -k t21` 1 failed, `tests/test_console_errors_and_live_region.py` 2 failed, `agent-kits/shared/test_doctor.py -k t21` 1 failed, `tests/test_statusline_cache.py -k t21` 1 failed: faltaban la Lente D, la guardia global y la distinción consola/panel en CLAUDE.md, 4 skills citaban rutas de `docs/knowledge/`, no había aviso de RED ausente con `tdd: true`, `recover` etiquetaba `vigente`, release no bloqueaba la copia pendiente ni hablaba de 5 manifiestos, la cookie era `ca_console` para todos los puertos, faltaban 7 códigos de error y el `aria-live` del chat estaba en `off`, sin node `/doctor` solo informaba y la caché de la barra de estado no se escribía con una ruta 8.3 · 2026-11-10.

GREEN: las mismas pruebas pasan (`test_docs_alignment_t21.py` 5, `test_ledger_lint.py` 12, `test_journal.py` 194 + 10 skipped, `test_journal_selection.py` 68, `test_release.py` 29, `test_control_center_http.py` 22, `test_console_errors_and_live_region.py` 3, `test_doctor.py -k t21` 3, `test_statusline_cache.py` 47 + 1 skipped, `test_dev_cycle_split.py` 11 con ahorro de la vía rápida 6.136, `test_roadmap_index.py` 71, `test_plugin_panel.py` 110 + 2 skipped); `export-interop.py --check` 92 al día, lint 0 errores (16 avisos de siempre), evals 0 errores. Medidas de tamaño y su separación del consumo observado: borrador de `testing/tokens.md` en el scratchpad de la sesión (para copiar) y `docs/TOKEN-EFFICIENCY.md` + espejo EN · 2026-11-10.

**Regresiones de CI de la fase 3 y de la fase 4** (PR 32 en rojo, 13 pruebas; reproducidas en Windows y en Linux `python:3.11-slim`)

RED: 13 nodeids fallaban en 514409e: `test_redact.py::test_journal_real_fallback_without_redact_module` (`ImportError` de `journal-prompt.py`) y `::test_t10fix2_178_transcript_seguro_ramas` (`None`), `test_audit_journal.py::test_first_prompts_survive_the_atomic_link_publication_window` (`journal_update_conflict`), `test_memory_local_recovery.py` N01, N03, N04 x3, N05, N08 y N09 (sin entrada del journal ni log de prompts, `TypeError: string indices`), `test_console_encoding.py::test_las_suites_tambien_decodifican_a_sus_hijos_como_utf8` y `test_dataset_assembler.py::test_t10fix2_m12_el_limite_de_sistemas_de_ficheros_locales_esta_declarado` · 2026-11-10.

Causas y arreglos: (1) commit de origen 544b50d (T-14, fase 3, H-31): `capture`, `_transcript_seguro` y `_asegurar_gitignore` pasaron a `journal-prompt.py`, que `journal.py` exige. Decisión: el bundle real SIEMPRE lo lleva (`run-hook.mjs` lo lanza solo y el instalador copia `agent-kits/` entero; el export de interop no enumera ficheros de kit y el paquete portable de skills no incluye el journal), así que NO se degrada `journal.py`: los bundles parciales de `test_redact.py` y de `test_memory_local_recovery.py` (lista de ficheros y bundle parcial de N08) copian también `journal-prompt.py`. (2) Los parches de las pruebas apuntaban a `journal` y no al módulo que ahora hace la comprobación: se redirigen a `journal._prompt_mod` y, para `JIO.IO`, a `journal._prompt_mod.JIO.IO` (journal-prompt carga su propia instancia de `journal-io`). (3) Fase 4, T-19: una prueba nueva lanzaba un subproceso en modo texto sin `encoding`; ahora `encoding='utf-8'`. (4) Fase 4, T-18: `commands/doctor.md` perdió la frase «sistemas de ficheros locales» (límite del tope de `/doctor`); se restaura en su sección Notas (+190 caracteres, sin tocar los presupuestos). Commits `b3f899d` y `d47c787`.

GREEN: en Windows los tres ficheros completos (`test_redact.py` 130, `test_audit_journal.py` 21, `test_memory_local_recovery.py` 14) y los dos nodeids de la fase 4; en Linux (`git -c core.autocrlf=false archive HEAD` en `python:3.11-slim`, `-m 1g`, un contenedor): los tres ficheros + los dos nodeids → `162 passed, 4 skipped, 1 failed` (el fallo era un artefacto del contenedor: árbol sin `git add`, sin ficheros versionados) y, repetido con `git add -A`, `test_las_suites_tambien_decodifican_a_sus_hijos_como_utf8` → `1 passed` · 2026-11-10.

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

## Revisión de dos lentes — intento 2: Fase 2 (T-07…T-12) — 3 Important y 9 Minor corregidos en fix2, ninguno descartado (T-07, T-08, T-09, T-10, T-11, T-12)

Lentes: A + B + C + D. Corrección en `fix2` por el implementer; cada gap con un test dedicado que lo nombra (`test_fix2_*`).

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | B-I1: `activas_acotadas` tomaba el estado solo del frontmatter de 16 KiB: un ledger de plantilla (estado en la tabla de cabecera) o con el estado fuera del prefijo dejaba de contar | T-07 | corregido | estado del frontmatter o de la tabla; si no aparece, relectura acotada de 256 KiB; `test_fix2_bi1_*` (e59bc28) |
| 2 | Important | B-I2: `vigente_entre` descartaba las de 100 % antes de mirar el marcador abierto | T-07 | corregido | orden: marcador abierto (aunque esté al 100 %), pendiente más reciente, más reciente; empate por nombre; `test_fix2_bi2_*` (e59bc28) |
| 3 | Important | A-I1: `review_initiatives` listaba sin `newest_first`: con 140 carpetas las 12 más nuevas no se podían revisar | T-09 | corregido | `list_names(newest_first=True)`; `test_fix2_ai1_*` (639c754) |
| 4 | Minor | B-M3/D-2: `session` y `active --json` usaban `activas()` con lecturas completas y otro orden | T-07 | corregido | todos usan `activas_acotadas` (instantánea memoizada); arranque 68 carpetas 4,89-11,93 s → 1,80-1,95 s y 345 carpetas 15-16 s → 2,2-3,3 s (pasadas 2.ª y 3.ª; detalle en T-07); `test_fix2_bm3_*` (e59bc28) |
| 5 | Minor | B-M4: las entradas viejas del journal se atribuían con la regla vieja | T-07 | corregido | campo `regla_iniciativa: "vigente"` en las nuevas; `--history-only` solo cita esas; `test_fix2_bm4_*` (e59bc28) |
| 6 | Minor | C+D: la regla solo mira las 128 carpetas más nuevas | T-07 | documentado | tope descrito en WORK-RESUME ES/EN y en el docstring; `test_fix2_cd_el_tope_de_la_regla_esta_documentado` (e59bc28) |
| 7 | Minor | D-1: con miles de carpetas sin ledger, cartera y progreso las recorrían todas | T-09 | corregido | como mucho `MAX_SCAN` carpetas tras ordenar; las demás se cuentan por nombre; `test_fix2_d1_*` (639c754) |
| 8 | Minor | C-1 (CWE-59): el recuento de omitidas usaba `os.path.exists`, que sigue enlaces | T-09 | corregido | recuento por nombre y comprobación de iniciativa por el listado acotado; en HEAD, 70 `exists` sobre carpetas omitidas; `test_fix2_c1_*` (639c754) |
| 9 | Minor | C+D: con ≥ 4.096 nombres se ordena el prefijo de `scandir` | T-09 | documentado | tope en `local-read.py`, PLUGIN-PANEL ES/EN y CONTRACTS E35; `test_fix2_cd_los_topes_reales_estan_documentados` (639c754) |
| 10 | Minor | A-M2: el modo rápido explícito y la recomendación por defecto no excluían la interfaz | T-08 | corregido | avisa y usa el flujo completo; `test_fix2_a_m2_*` (7216813) |
| 11 | Minor | A-M3: la rama proporcional de `_cupos` no tenía test | T-10 | corregido | mínimo garantizado de agentes y comandos de `PRIORIDAD` en el reparto proporcional; `test_fix2_a_m3_*` con 50 agentes (83fc520) |
| 12 | Minor | A-M4: docstrings de `skill-index.py`, PLUGIN-PANEL ES/EN y CONTRACTS E35 con topes viejos | T-10, T-09 | corregido | textos alineados; `test_fix2_a_m4_*` y `test_fix2_cd_los_topes_reales_*` (83fc520, 639c754) |

Ahorro de la vía rápida: 6158 (≥ 6000).

Nota: los comentarios de `serve_panel.py` de fix2 volvieron a ASCII (el linter y `tests/test_console_encoding.py` exigen ASCII en un script sin reconfiguración de streams); `lint_plugin.py` 0 errores.

## Revisión de dos lentes — intento 3: Fase 2 (T-07…T-12) — 2 Important y 10 Minor corregidos en un ciclo final acotado (T-07, T-08, T-09, T-10, T-11, T-12)

Lentes: A + B + C + D. Corrección en `fix3` por el implementer; cada gap con un test dedicado que lo nombra (`test_fix3_*`).

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | A: «Ledger canónico» del bloque `session` elegía la pendiente única, no `vigente_entre` | T-07 | corregido | misma regla que journal, memoria y statusline; cola según el estado («retoma…», «al 100 %: /retro …», «sin tarea en-progreso»); `test_fix3_a_*` (c36e488) |
| 2 | Important | B: `local-read` rechazaba enlaces en todos los ancestros hasta la raíz del disco: un proyecto bajo un enlace o una junction perdía el bloque de roadmap y `/doctor` | T-07 | corregido | la raíz se resuelve una vez con `realpath` (ancla) y solo se comprueban los componentes por debajo; panel y consola conservan el rechazo bajo la raíz; `test_fix3_b_*`, `test_fix3_root_behind_a_link_*` (c36e488) |
| 3 | Minor | B2: omitidas contadas solo por fecha (ficheros y carpetas no-iniciativa) | T-09 | corregido | nombre de carpeta de iniciativa sin extensión, sin disco; 76 exactas; `test_fix3_b2_*` (51e361f) |
| 4 | Minor | `progress_snapshot` cortaba en 128 carpetas sin mirar si tenían ledger | T-09 | corregido | filtro por nombre y recorrido hasta `MAX_WALK` = 1.024, parando a las 64 filas; `test_fix3_b_progreso_*` (51e361f) |
| 5 | Minor | B3: activa > 256 KiB sin tabla con `total: None` y, con tabla, sin tareas en curso | T-07 | corregido | las activas se leen enteras hasta 16 MiB; `test_fix3_b3_*` (c36e488) |
| 6 | Minor | B4: listado recortado a 128 sin aviso | T-07 | corregido | «Roadmap recortado: N carpetas más antiguas sin revisar» en `session`, `active --json` y `/doctor`; `test_fix3_b4_*` (c36e488) |
| 7 | Minor | B5: un ledger con `invalid_encoding` desaparecía sin aviso | T-07 | corregido | aviso en el bloque y en `/doctor`; `test_fix3_b5_*` (c36e488) |
| 8 | Minor | C1 (CWE-59): la firma de la memo hacía `lstat` dentro de una carpeta enlazada | T-07 | corregido | se comprueba la carpeta antes y una enlazada se avisa sin mirar dentro; `test_fix3_c1_*` (c36e488) |
| 9 | Minor | A2: el test de C-1 vigilaba 70 carpetas y la 65.ª se leía antes del corte | T-09 | corregido | corte antes de leer; el test cubre las 76; `test_fix3_a2_*` (51e361f) |
| 10 | Minor | A3: faltaba proteger que la retoma explícita cite entradas sin `regla_iniciativa` | T-07 | corregido | `test_fix3_a3_*` (c36e488) |
| 11 | Minor | A4: observability ES/EN y shared README sin la regla real ni el campo del journal | T-07 | corregido | textos actualizados; `test_fix3_a4_*` (TDD n/a: test de texto sobre el texto corregido) (c36e488) |
| 12 | Minor | `recover` marca `regla_iniciativa: vigente` con la iniciativa del momento de recuperar | T-07 | deuda | registrada en T-21; `test_fix3_deuda_de_recover_*` (c36e488) |

**Decisión del orquestador:** al 3.er intento con gaps, el orquestador decide un ciclo final acotado (autorización del usuario «con todo»); se verifica con tests dirigidos y CI, sin 4.º intento de lentes.

## Revisión de dos lentes — intento 1: Fase 3 (T-13..T-16) — 4 Important, 9 Minor

Lentes: A + B + C + D; C sin hallazgos. Corrección en `fix1` por el implementer; cada gap con un test dedicado que lo nombra (`test_fix1_*`) o con su medida.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | B1: `_ts_previo` usaba un `"timestamp"` anidado de una línea JSON válida sin fecha en la raíz y podaba un offset necesario (re-close 57 en vez de 7) | T-13 | corregido | regex solo si `json.loads` falla; `test_fix1_b1_*` (f468bb2) |
| 2 | Important | D1+B2: el atajo de Bash de la barra de estado leía la primera clave de cualquier objeto y, con claves repetidas o `null`, lanzaba Python en cada refresco aunque la entrada fuera idéntica | T-16 | corregido | campos dentro de su grupo; sin decidir, clave con la entrada; `test_fix1_d1_b2_*` (bfbe481) |
| 3 | Important | A1: criterio «tiempos medidos más bajos» con task-brief 1,12 → 1,12 s | T-16 | corregido | paso del lint aislado 0,410 → 0,014 s; nota en el GREEN fix1 de T-16 |
| 4 | Important | A2: la Verificación de T-14 nombra `tests/test_hooks_shell.py` y solo se ejecutó un subconjunto | T-14 | corregido | completo, solo y con timeout: `79 passed in 307.34s` |
| 5 | Minor | A3: criterio ≤ 3 procesos y medida 4 | T-14 | corregido | Python normal: 22 → 3, 5 → 3, 5 → 3; el `.venv` añade un redirector |
| 6 | Minor | A4: la primera instantánea y otras rutas lentas seguían en serie | T-15 | corregido | hilos acotados (4), escrituras en serie, progreso inicial al arrancar; `test_fix1_a4_*` (bda236c) |
| 7 | Minor | A5: `tests/e2e/control-center.mjs` modificado y sin ejecutar | T-15 | deuda aceptada | sin `puppeteer` ni servidor de fixture permitido en la máquina; `node --check` ok, 9 saltados; registrada en T-21 |
| 8 | Minor | A6: FLOWS ES/EN con `journal.py capture` y SubagentStop sin debounce | T-14 | corregido | `test_fix1_a6_*` (8579c3a) |
| 9 | Minor | D2: la migración dejaba todos los transcripts abiertos y con EMFILE marcaba como podado | T-13 | corregido | un fichero cada vez y reintento tras error; `test_fix1_d2_*` (f468bb2) |
| 10 | Minor | B3: Inicio daba las sesiones gestionadas como total sin consultar las externas | T-15 | corregido | «≥ N»; `test_fix1_b3_*` (bda236c) |
| 11 | Minor | B4: la captura descartaba prompts > 2 MiB y payloads con UTF-8 inválido | T-14 | corregido | lectura entera con reemplazo, recorte de `capture`; `test_fix1_b4_*` (8579c3a) |
| 12 | Minor | B5: `with_empty_job` convertía en 1 cualquier código fuera de 0..255 | T-14 | corregido | solo se normaliza el rango de la marca; `test_fix1_b5_*` (8579c3a, e3ddfb2) |
| 13 | Minor | B-nota: SubagentStop compartía `.progress-last` con ledger-post y podía callarse | T-14 | corregido | `.progress-last-subagent` propio; `test_fix1_bnota_*` (8579c3a) |

## Revisión de dos lentes — intento 2: Fase 3 (T-13..T-16) — 2 Important, 7 Minor

Lentes: A + B + D. Corrección en `fix2` por el implementer; cada gap de código con un test dedicado que lo nombra (`test_fix2_*`). La traza del intento 1 no se reescribe: queda como se escribió.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | B1 seguía abierto con líneas de más de 4 KiB: una cola con solo un trozo de línea iba a la regex y cogía el `snapshot.timestamp` anidado | T-13 | corregido | solo la línea entera decide; mayor de 64 KiB o no JSON → None; `test_fix2_b1_*` (d2c0a80) |
| 2 | Important | D: el atajo de la barra de estado exigía grupos planos y el payload real (`current_usage` anidado) caía siempre a Python; B3: llaves dentro de cadenas descuadraban el recuento | T-16 | corregido | escáner de miembros JSON con cadenas y anidamiento; 7 → 1 Python con el payload real; `test_fix2_d_*`, `test_fix2_b3_*` (d6f3e71) |
| 3 | Minor | A1, A2 y A3 del intento 1 constan como corregidos sin un test que los nombre | T-14, T-16 | evidenciado (medida) | no son gaps de código sino de evidencia o de criterio: A1 es la medida aislada del lint (0,410 → 0,014 s), A2 la ejecución completa de `tests/test_hooks_shell.py` (79 passed) y A3 el recuento con un Python normal (22 → 3); un test de texto no añadiría nada |
| 4 | Minor | La deuda A5 de T-21 (e2e de `control-center.mjs`) no tenía test que la vigilara | T-15 | corregido | `test_fix2_4_la_deuda_del_e2e_de_la_consola_queda_en_t21` (c8f1b26) |
| 5 | Minor | `.claude/.progress-last-subagent` no estaba en `.gitignore` | T-14 | corregido | línea propia en `.gitignore`; `git check-ignore` sale 0; `test_fix2_5_*` (823328d) |
| 6 | Minor | La captura redactaba el turno entero antes de recortarlo, sin tope de lectura | T-14 | corregido | ventana de 4.000 + 16 KiB, corte después de redactar, tope de 32 MiB; `test_fix2_6_*` (823328d) |
| 7 | Minor | `plan_page` actualizaba `plan_ids` sin cerrojo en varios hilos | T-15 | corregido | `_planes_lock`; `test_fix2_7_*` (c8f1b26) |
| 8 | Minor | Un transcript existente e ilegible hacía repetir la poda en cada start/close | T-13 | corregido | `poda_fallida` con su mtime, reintento solo si cambia; `test_fix2_d_*` (d2c0a80) |
| 9 | Minor | La fila de UserPromptSubmit de observability ES/EN nombraba `journal.py capture` | T-14 | corregido | `journal-prompt.py`; `test_fix2_9_*` (823328d) |

Anotado como deuda en T-21 (no es gap de esta fase): con la raíz del proyecto en una ruta corta 8.3, `statusline-render.py` no escribe la caché.

## Revisión de dos lentes — intento 3: Fase 3 (T-13..T-16) — 1 Important, 9 Minor

Lentes: A + B + D. Al tercer intento con gaps, el orquestador decide un ciclo final acotado (`fix3`), como en la Fase 1, siguiendo el «adelante, con todo» del usuario; sin intento 4 de lentes: lo verifica el orquestador con pruebas dirigidas. Cada gap de código con un test dedicado (`test_fix3_*`).

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | CWE-532: la ventana de redacción encoge al redactar y un secreto cortado en su borde (6.º PEM, `Bearer`, `password=`) acababa en los 4.000 guardados | T-14 | corregido | ventana que crece hasta 4.000 + 16 KiB redactados (tope 1 MiB); igual que redactar todo y cortar; `test_fix3_1_*` (e84f498). Verificación del orquestador: PEM de más de ~17 KB sin END → corregido (un BEGIN sin cerrar en lo guardado pasa a marcador; `test_fix3_1_pem_largo_sin_end_*`) |
| 2 | Minor | Escáner de la barra de estado cuadrático (25 KB → 13,5 s por refresco, también con caché caliente) | T-16 | corregido | tope de 8 KB, una pasada para los tres grupos, una cadena = un token; `test_fix3_2_*` (a89afdf) |
| 3 | Minor | `NUMBER` admitía 27 dígitos: `0.50000000000000001` daba `ctx 1%` en Bash y `ctx 0%` en Python | T-16 | corregido | cerca del redondeo con más de 15 dígitos, o más de 17, pinta Python; `test_fix3_3_*` (a89afdf) |
| 4 | Minor | Con JSON inválido Bash pintaba campos y Python no | T-16 | corregido | coma final, texto tras el objeto y escapes inválidos caen a Python; `test_fix3_4_*` (a89afdf) |
| 5 | Minor | `poda_fallida` con mtime None no se podaba nunca y un error pasajero bloqueaba la poda para siempre | T-13 | corregido | un fichero ausente se descarta; tope de 3 intentos; `test_fix3_5_*` (1a55539) |
| 6 | Minor | `test_fix2_4_…` no tuvo rojo y el ledger no lo decía | T-15 | corregido | `TDD n/a` en T-15 |
| 7 | Minor | El tope de 32 MiB de la captura no tenía test; por encima se omite el turno sin rastro | T-14 | corregido | `test_fix3_7_*` (TDD n/a: guarda); el rastro no se añade: el contrato prohíbe stdout/stderr y sin JSON no hay log de sesión (justificado en T-14) |
| 8 | Minor | `statusline-render.py` no figuraba en `Archivos` de T-21 ni había test de la deuda 8.3 | T-21 | corregido | `Archivos` de T-21; `test_fix3_8_*` |
| 9 | Minor | La excepción «evidenciado (medida)» no está en `docs/CONSTITUTION.md` | T-21 | deuda aceptada | decisión pendiente del usuario registrada en T-21 con dos propuestas (línea en la constitución o ADR); no se toca la constitución |
| 10 | Minor | `test_fix2_6` dependía de un tope de tiempo de 4,5 s | T-14 | corregido | mide los caracteres que pasan por `redactar` (e84f498) |

## Revisión de dos lentes — intento 1: Fase 4 (T-17..T-21) — 6 Important, 11 Minor, 1 descartado

Lentes: A + B + C + D (C por `hooks/session-context.py`; D por `scripts/export-interop.py` y la caché de la statusline). Se fusionan los gaps repetidos (C1+B3, A1+D2, D1 con la nota de B, A3+D5). Corrección en `fix1` por el implementer; cada gap corregido lleva un test dedicado que lo nombra (`test_f4fix1_*`) o su medida.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | C1+B3: `SHAREDKIT="<ruta>"` sin escapar entre comillas dobles; al pegarlo en Bash, `$(…)`, la comilla invertida y `$VAR` se ejecutan o se expanden (reproducido con un directorio `b$(touch PWNED)`; CWE-78) | T-19 | corregido | `'…'` POSIX con `'''` y sin línea si hay un carácter de control (`kit_line` en el hook y en `task-brief.py`); `test_f4fix1_1_*` ejecuta la línea con `bash -c` sobre `b$(touch X)`, `$1`, comilla invertida, `"` y `'`: no se crea nada y SHAREDKIT es exacto (2080b49) |
| 2 | Important | A1+D2: la ruta inyectada solo llega al hilo principal y a los despachos con brief; reviewer, qa, documenter, planner, evaluator y analyst siguen con el `find`, y las recetas de los agentes sobrescriben un `SHAREDKIT` que ya existe | T-19 | corregido | las 9 recetas con `R=` (+ `capability-check.md`) respetan un `SHAREDKIT` existente (`[ -f "$SHAREDKIT/${M##*/}" ] && R="${SHAREDKIT%/*/*}"`; la receta va inline en cada agente, no hay fuente compartida que cambiar); dev-cycle, pm-cycle, lens-prompts y quick-implement pasan la línea en cada despacho; evaluator 15.414 bytes LF ≤ 15.513; vía rápida 6.066 ≥ 6.000; `test_f4fix1_2_*` (2080b49) |
| 3 | Important | D1: en OpenCode, el bucle de eventos llama a `invalidate()` en cada evento de actividad o captura, y `session.idle` reescribe el journal, que está en la firma; la caché nunca sobrevive a un turno. El test no pasa por el flujo de eventos | T-20 | corregido | ningún evento invalida; la firma lee en paralelo (tope 1 s), resume las entradas del journal por las líneas que cita el bloque y deja fuera el índice y los sobres de la cola; `test_f4fix1 gap 3` pasa `session.execution.started/succeeded` y `session.status idle` y reutiliza el contexto entre turnos; `docs/INTEROP.md` y espejo EN corregidos (d644887) |
| 4 | Important | A2: el puntero de `/doctor` a sus notas (`docs/reference/doctor.md`) es relativo al proyecto; en un consumidor no existe y por `npx` no viaja `docs/` | T-18 | corregido | notas movidas a `agent-kits/shared/doctor-reference.md`; el comando las nombra con `$R/…`; `docs/reference/doctor.md` queda como puntero y `docs/en/reference/doctor.md` espeja la referencia; `test_f4fix1_4_*` comprueba payloads del instalador y las tres copias del comando (07f21b5) |
| 5 | Important | A3+D5: la Verificación de T-17/T-18 (CA-06) pide `context-footprint.py` y no hay salida suya; las cifras de `testing/tokens.md` y `TOKEN-EFFICIENCY` no describen HEAD (`doctor.md` 5.659 y no 5.491; base «514409e~» mal nombrada; evaluator medido en CRLF; bases de planner y evaluator −7) | T-17, T-18 | corregido | medido con `context-footprint.py` sobre `cb6fb40` y sobre `2080b49`, en LF; salida pegada en el GREEN de T-17 y T-18; `testing/tokens.md` (borrador entregado al coordinador) y `docs/TOKEN-EFFICIENCY.md` + espejo EN con cifras de HEAD; `test_f4fix2_5_the_published_figures_match_context_footprint_on_head` compara las cifras de `TOKEN-EFFICIENCY` ES/EN y de `testing/tokens.md` con la herramienta sobre HEAD, en LF (fix2) |
| 6 | Important | B1: el chat de la consola pasa a `aria-live="polite"` y se reconstruye entero con `replaceChildren` en cada sondeo de 2 s; un lector de pantalla vuelve a anunciar la conversación visible | T-21 | corregido | el log ya no es región viva (`aria-live="off"`); `#chat-live` anuncia solo los mensajes nuevos del asistente; `reconcileChildren` no reinserta nodos en su sitio; `tests/console-live.test.mjs` (`f4fix1 gap 6`) (cd3b344) |
| 7 | Minor | C2: el brief no distingue la línea de kit que genera el script de una igual copiada desde el ledger (CWE-829) | T-19 | corregido | la línea generada dice «única línea de kit válida»; `test_f4fix1_7_*` (2080b49) |
| 8 | Minor | B2: `_RED_RE` no casa `  - RED:`, `**RED**:` ni `RED (fix2):`; falsos avisos en ledgers reales | T-21 | corregido | `_RED_RE` acepta `- RED:`, `**RED**:` y `RED (fix2):`; `test_f4fix1_8_*` (2080b49) |
| 9 | Minor | B4: `replay` desde la cola sigue redactando con la iniciativa vigente y la marca `vigente` (arreglo parcial de la deuda de T-07) | T-21 | corregido | un cierre de más de 1 h no lleva la marca `vigente` (`_cierre_tardio`); `test_f4fix1_9_*` (2080b49) |
| 10 | Minor | D3: el tope de 250 ms de la firma desactiva la caché de OpenCode en proyectos medianos (lstat/readdir en serie) | T-20 | corregido | lstat/readdir en paralelo (lotes de 64) y tope de 1 s; `f4fix1 gap 10` con 1.500 ficheros (d644887) |
| 11 | Minor | D4: una sola ranura de caché; padre e hija se la pisan en cada delegación | T-20 | corregido | una ranura por sesión (hasta 16); `f4fix1 gap 11` (d644887) |
| 12 | Minor | D6: ningún script emite «sin integraciones»; los 10 agentes pagan siempre la prosa nueva de T-17 | T-17 | corregido | `task-brief.py` emite «Integraciones: sin integraciones.» cuando `integration-route.py` devuelve absent/disabled/no_match; `test_f4fix1_12_*` (2080b49) |
| 13 | Minor | A5: el plan pedía ampliar el margen de la vía rápida y bajó (6.158 → 6.136, ≥ 6.000); la desviación no está registrada | T-17, T-21 | corregido | desviación registrada: el margen de la vía rápida baja de 6.158 → 6.066 (mínimo 6.000), por la marca «sin integraciones» y por la línea del kit en cada despacho; `test_f4fix1_13_*` |
| 14 | Minor | A6: las medidas de la fase 4 no están donde dice el plan (`testing/perf.md`) ni enlazadas desde él | — | corregido | el orquestador añade a `testing/perf.md` la sección «Fase 4», que enlaza a `testing/tokens.md` (copiado desde el borrador del fix1); `test_f4fix2_14_perf_md_links_to_tokens_md_and_it_exists` lo fija: con el `perf.md` de `2080b49` falla (RED fix3, gap 7) |
| 15 | Minor | A7: frase de unas 65 palabras con comillas anidadas (regla 1 de `docs-style.md`) | T-21 | corregido | frases de ≤ 40 palabras y sin comillas anidadas en ES y EN; `test_f4fix1_15_*` |
| 16 | Minor | D-nota: el Changelog de T-20 atribuye la caché también a Codex, que no la tiene | T-20 | corregido | el error estaba en el campo `Changelog` de T-20 (decía «En OpenCode y Codex»), corregido; `CHANGELOG.md:44` y `CHANGELOG.es.md:44` ya solo nombraban a Codex en la cláusula de delegación (rebatido ahí) y se amplían; `test_f4fix1_16_*` |
| 17 | Minor | A-nota: `session-context.py` no emite la línea del kit si el resto del bloque está vacío | T-19 | corregido | la línea del kit sale aunque el bloque esté vacío; `test_f4fix1_17_*` (2080b49) |
| 18 | Important | A4: la Verificación de T-21 exige la CI completa en Linux | T-21 | descartado (rebatido) | la CI del PR #32 (`ci.yml`, ubuntu y Python 3.11) pasó completa en `774aebb`: run 42765058054, job 129659480354, `success` |

**fix1 — RED y GREEN**

RED fix1 (gaps 1, 2, 7, 12, 17): `tests/test_f4fix1_kit.py` sobre `b197d6c` falló con 42 failed, 2 passed: `kit_line` no existe, la línea usa comillas dobles (el directorio `b$(touch X)` ejecuta `touch`), las recetas de los agentes sobrescriben un `SHAREDKIT` existente, los orquestadores no pasan la línea y el brief no dice «sin integraciones» · 2026-11-10.
RED fix1 (gaps 8, 9): `tests/test_f4fix1_misc.py` sobre `b197d6c` falló con 2 failed: `  - RED:`, `**RED**:` y `RED (fix2):` no casan, y un replay de 3 días conserva `regla_iniciativa: vigente` · 2026-11-10.
RED fix1 (gaps 3, 10, 11): `tests/opencode-plugin.test.mjs -- f4fix1` sobre `b197d6c` falló con 3 failed: tras un turno completo el contexto pasa de `context 2` a `context 3`, padre e hija se pisan (`context 3` en vez de `context 1`) y un árbol de 1.500 ficheros no admite reutilización · 2026-11-10.
RED fix1 (gap 4): `test_f4fix1_4_*` falló: `agent-kits/shared/doctor-reference.md` no existe y las copias de interop citan `docs/reference/doctor.md` · 2026-11-10.
RED fix1 (gap 6): `tests/console-live.test.mjs` falló al importar: `reconcileChildren` y `newMessageAnnouncements` no existen; el log seguía con `aria-live="polite"` · 2026-11-10.
RED fix1 (gaps 13, 15, 16): `test_f4fix1_13/15/16_*` fallaron: frase de 41 palabras con comillas anidadas, Changelog de T-20 con «OpenCode y Codex», sin la desviación 6.158 → 6.066 · 2026-11-10.

GREEN fix1: `context-footprint.py` (salida completa en `testing/tokens.md`, borrador entregado), `cb6fb40` → `2080b49` en LF: `commands/doctor.md` 16.626 → 5.700, `phase2-planning.md` 18.136 → 3.034, flujo completo 56.363 → 41.510, `agents/evaluator.md` 14.921 → 15.115 caracteres (15.414 bytes LF ≤ 15.513), vía rápida 15.066 − 9.000 = 6.066 ≥ 6.000. Tests: `test_f4fix1_kit` 43, `test_f4fix1_misc` 6, `test_kit_path_injection` 3, `test_session_context`, `test_ledger_lint` 12, `test_doctor_notes_in_docs` 2, `test_graphiti_security` 126, `test_hooks_shell` 79, `test_knowledge_services` 53, `test_dev_cycle_split` 11, `opencode-plugin.test.mjs` 29, `console-live.test.mjs` 4; `test_task_brief` 94 tras reducir la memoria del escenario de borde de 2150 a 2050 caracteres (el encabezado crece ~70).

## Revisión de dos lentes — intento 2: Fase 4 (T-17..T-21) — 5 Important, 8 Minor

Lentes: A + B + C + D, re-evaluando solo el fix1 (`b197d6c..HEAD`) con la traza del intento 1 traspasada. Cerrados: gap 1 (CWE-78: probado con Unicode, bidi y `\`, además de la sonda del orquestador con 22 casos sobre los dos emisores), 3 (acierto de caché de 6-7 ms entre turnos con el flujo real de eventos), 4, 6 en su estructura, 8 en las formas pedidas, 11, 12, 13, 15 y 17. Se fusionan C-G1 con C-G2 y B-R6 (precedencia del `SHAREDKIT`), A-1 con D-c (roles sin la línea del kit) y A-4 con D-d (cifra del implementer). CI del PR #32 verde en `4b2cb7f` (run 42793107088), con la suite del instalador. Corrección en `fix2`, cada gap con su test `test_f4fix2_*`.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | C-G1+C-G2+B-R6: una línea `Kit: SHAREDKIT='…'` escrita en el ledger se copia literal al brief, no se distingue de la real, y las recetas anteponen `SHAREDKIT` a `CLAUDE_PLUGIN_ROOT`. Un script del repo consumidor sustituye a `scope-check`, `ledger-lint` o `lib-guardrail.sh` de qa/nemesis; también un `SHAREDKIT` heredado del entorno o de otra versión del plugin (CWE-829/CWE-426, reproducido: `FAKE scope-check OK`) | T-19 | corregido | precedencia `CLAUDE_PLUGIN_ROOT` > `SHAREDKIT` (solo sin raíz y con el marcador) > `find` en las 9 recetas y `capability-check.md`; `task-brief.py` (`sin_kit_falso`) y el hook (`neutralise_kit_text`) citan como dato todo `SHAREDKIT=` ajeno a su línea; la línea dice «única línea de kit válida: esta»; `test_f4fix2_1_*` reproduce la Lente C (ledger con línea falsa y `tools/agent-kits/shared/scope-check.py`): una sola asignación válida y la receta con `CLAUDE_PLUGIN_ROOT` resuelve al bundle real. Exigir que `SHAREDKIT` no esté bajo el árbol del proyecto se valoró y no se adoptó: cuesta ~110 bytes por receta (el evaluator no cabe en CA-22) y la precedencia más la neutralización cortan el vector (b5829b9) |
| 2 | Important | B-R1 (regresión del gap 9): con el umbral de 1 h, casi toda sesión de Claude Code se materializa en el SessionStart siguiente sin `regla_iniciativa`, y `--history-only` la quita del bloque de arranque sin avisar (reproducido: a 0 h la cita sale, a 2 h el bloque sale vacío) | T-21 | corregido | la iniciativa se fija al capturar (`_iniciativa_al_capturar`, campo `iniciativa` del envelope, sin texto de conversación) y `replay` la usa con `vigente`; los envelopes antiguos usan un umbral de 24 h; el arranque avisa de las entradas omitidas («N entrada(s) omitida(s)»); `test_f4fix2_2_*` replica a 0, 2 y 14 h (fd98bb4) |
| 3 | Important | B-R2 (resto del gap 6): `#chat-live` solo anuncia el primer fragmento de una respuesta en streaming, porque el id se marca como visto antes de mirar el texto; si el primer fragmento llega vacío, no se anuncia nunca | T-21 | corregido | `newMessageAnnouncements` lleva el texto ya anunciado por id y anuncia el texto nuevo; un primer fragmento vacío no marca el id; `tests/console-live.test.mjs` (`f4fix2 gap 3`) con deltas del mismo id (4b3584a) |
| 4 | Important | A-1+D-c (resto del gap 2): architect (pm-cycle Fase 2-bis y dev-cycle Fase 2), knowledge-curator (dev-cycle 4-bis) y el implementer clásico (sin brief, `subagentes: false`) no reciben la línea del kit; el test «names every dispatched role» solo comprueba 6 roles | T-19 | corregido | dev-cycle nombra analyst, evaluator, architect, planner, implementer sin brief, reviewer, qa, documenter, knowledge-curator y nemesis; pm-cycle añade architect; `test_f4fix2_4_*` deriva los roles de los despachos reales de cada comando; evaluator 15.429 bytes LF ≤ 15.513; vía rápida 6.051 ≥ 6.000 (b5829b9) |
| 5 | Important | A-2: los gaps 5 y 14 del intento 1 constan como `corregido` sin un test dedicado que los nombre (CONSTITUTION l.13) y sin `RED:`. El 14 lo cerró el orquestador | T-17, T-18 | corregido | `test_f4fix2_5_*` y `test_f4fix2_14_*` (los dos fallaron antes: `TOKEN-EFFICIENCY` decía 28.632 para el implementer y `testing/tokens.md` 5.546 de capability-check frente a lo medido); filas 5 y 14 del intento 1 corregidas para nombrarlos (b5829b9) |
| 6 | Minor | B-R3 + nota de D: con la caché acertando, la outbox de OpenCode no se drena; los sobres se acumulan, el bloque queda obsoleto y el replay posterior drena en orden de hash, no cronológico | T-20 | corregido | un acierto con la outbox no vacía la drena en segundo plano (una vez por estado de la cola) y `outbox.reclamar` ordena por mtime; `f4fix2 gap 6` y `test_f4fix2_6_*` (82bb2b6) |
| 7 | Minor | B-R5: se inyectan cosas que la firma no cubre (`marcadores_cerrados` decide si una entrada es placeholder; el aviso transitorio «replay bloqueado» se queda en caché) | T-20 | corregido | `marcadores_cerrados` firma como presente/ausente y el aviso transitorio no se cachea; `f4fix2 gap 7` (82bb2b6) |
| 8 | Minor | D-a (resto del gap 10): el tope `depth > 8` desactiva la caché en proyectos con fixtures bajo `docs/roadmap/*/testing/` (este repo incluido) | T-20 | corregido | profundidad 12 y `docs/roadmap/*/testing/` fuera de la firma; `f4fix2 gaps 8 and 9` (82bb2b6) |
| 9 | Minor | D-b: `.claude/.confluence-pending` se trunca en cada edición bajo `docs/` y está en la firma sin que el bloque lo cite; obliga a recalcular en cada turno | T-20 | corregido | `.confluence-pending` fuera de la firma, y los directorios firman solo por nombre (su mtime se mueve con cada fichero nuevo); `f4fix2 gaps 8 and 9` (82bb2b6) |
| 10 | Minor | B-R4 (resto del gap 8): `_RED_RE` no acepta `RED <palabra> (…)` ni varias palabras (`RED fix1 (gap 6):`, la forma del propio fix1) | T-21 | corregido | `_RED_RE` acepta hasta 6 palabras antes del paréntesis (`RED fix1 (gap 6):`); `test_f4fix2_10_*` (fd98bb4) |
| 11 | Minor | A-3: CONVENTIONS ES/EN siguen mostrando `SHAREDKIT="<ruta>"` con comillas dobles y no dicen «única línea de kit válida» ni cuál es la precedencia | T-19 | corregido | CONVENTIONS ES/EN con comillas simples, «única línea de kit válida» y la precedencia; `test_f4fix2_11_*` (b5829b9) |
| 12 | Minor | A-4+D-d: TOKEN-EFFICIENCY ES/EN da 28.632 para el implementer (b197d6c) y en HEAD mide 28.797; la evidencia del gap 5 cita un pegado en los GREEN de T-17/T-18 que no existe | T-17, T-18 | corregido | TOKEN-EFFICIENCY ES/EN con las cifras de HEAD (implementer 28.842, vía rápida 6.051) y el pegado de `context-footprint.py` en los GREEN de T-17 y T-18; `test_f4fix2_5_*` |
| 13 | Minor | A-5: el espejo EN dice que `commands/doctor.md` apunta «aquí», pero apunta a `agent-kits/shared/doctor-reference.md` | T-18 | corregido | el espejo EN dice que el comando apunta a `$R/agent-kits/shared/doctor-reference.md`; `test_f4fix2_13_*` (b5829b9) |

**fix2 — RED y GREEN**

RED fix2 (gaps 1, 4): `tests/test_f4fix2_kit.py` sobre `779213b` falló con 15 failed, 1 passed: las recetas anteponen `SHAREDKIT` a `CLAUDE_PLUGIN_ROOT`, el brief copia una línea de kit falsa del ledger y `neutralise_kit_text` no existe, dev-cycle no nombra a architect, knowledge-curator, nemesis ni al implementer sin brief y pm-cycle no nombra a architect · 2026-11-10.
RED fix2 (gap 2): `tests/test_f4fix2_journal.py` sobre `779213b` falló con 3 failed, 1 passed: el envelope no trae `iniciativa` y, a 2 h y a 14 h, la entrada se atribuye a la iniciativa vigente al materializar o pierde la marca · 2026-11-10.
RED fix2 (gap 3): `tests/console-live.test.mjs` falló con 3 failed: el id se marca como visto antes de mirar el texto (solo el primer fragmento) y un primer fragmento vacío no se anuncia nunca · 2026-11-10.
RED fix2 (gaps 6-9): `tests/opencode-plugin.test.mjs -- f4fix2` sobre `779213b` falló con 3 failed: la outbox no se drena con la caché acertando, el aviso transitorio se cachea y las marcas de coste no firman, un `testing/` profundo y `.confluence-pending` invalidan la caché; `test_f4fix2_6_*` falló con `aaaa` antes que `ffff` (orden por hash) · 2026-11-10.
RED fix2 (gaps 10, 11, 13): `test_f4fix2_10_*`, `test_f4fix2_11_*` y `test_f4fix2_13_*` fallaron: `RED fix1 (gap 6):` no casa, CONVENTIONS lleva comillas dobles y sin precedencia, el espejo EN dice «a pointer here» · 2026-11-10.
RED fix2 (gaps 5 y 14 del intento 1, 12): el rojo se observó contra el estado publicado: `test_f4fix2_5_*` falla con `testing/tokens.md` sin copiar (28.797 y 5.546 frente a lo medido, 28.842 y 5.561) y con `TOKEN-EFFICIENCY` en su versión de `779213b` (28.632); `test_f4fix2_14_*` pasa desde `4b2cb7f` (el enlace ya existía; el test lo fija) · 2026-11-10.

GREEN fix2: `test_f4fix2_kit` 16, `test_f4fix2_journal` 4, `test_f4fix2_misc` 6 (con `F4FIX2_TOKENS_MD` apuntando al borrador de `tokens.md` entregado al coordinador, que aún no está copiado), `console-live.test.mjs` 6, `opencode-plugin.test.mjs`, `test_outbox` 55; `context-footprint.py` `cb6fb40` → `b5829b9` en LF: `agents/evaluator.md` 14.921 → 15.130 caracteres (15.429 bytes LF ≤ 15.513), vía rápida 15.066 − 9.015 = 6.051 ≥ 6.000.

## Revisión de dos lentes — intento 3: Fase 4 (T-17..T-21) — 3 Important, 7 Minor

Lentes: A + B + C + D, re-evaluando solo el fix2 (`779213b..HEAD`) con las trazas de los intentos 1 y 2 traspasadas. Cerrados: los gaps 3, 4, 5, 8, 9, 11, 12 y 13 del intento 2, y la precedencia del 1. La caché de OpenCode acierta en 7-8 ms en el flujo real, y las cifras de tokens coinciden en las 21 filas. El orquestador comprobó que, con `CLAUDE_PLUGIN_ROOT` definido, un `SHAREDKIT` falso con marcador no gana.

Fusiones: C1 con B3 (neutralización por forma), y A1 con B1, B2, D1 y la nota de C (regla de iniciativa al capturar). Como es el 3.er intento con gaps, el orquestador decide un **ciclo final acotado (fix3)** con el diseño fijado (sin un 4.º intento de revisión). La verificación la hace el orquestador.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | C1+B3: la neutralización reconoce formas concretas (comillas simples o ruta absoluta, prefijos exactos) y deja pasar `SHAREDKIT=tools/…` sin comillas, comillas dobles relativas, `$'…'`, `~`, `export`, `declare`, `printf -v`, prefijos Markdown (`- Kit:`, `**Kit:**`, `> Kit:`), la K cirílica y el tabulador inicial (en el hook). Reproducido de punta a punta: la línea falsa sale intacta en el brief junto a la real (CWE-829/426) | T-19 | corregido | por token, no por forma: `sin_kit_falso` (brief) y `neutralise_kit_text` (hook) convierten cada `SHAREDKIT` (sin distinguir mayúsculas) fuera de la línea generada en `SHAREDKIT⟨cita⟩`, que no puede ser una asignación (única excepción: precedido de `$`, que es una expansión y no puede asignar; así el pie del bloque de memoria «kit compartido, $SHAREDKIT» y los comandos con `$SHAREDKIT` del ledger siguen copiables); se neutraliza antes del presupuesto del brief para que las longitudes avisadas sean las reales; fuera las heurísticas `Kit:`/`Kit activo:`. `test_f4fix3_1_*` prueba 16 variantes (sin comillas, comillas dobles relativas, `$'…'`, `~`, `export`, `declare`, `printf -v`, `: "${SHAREDKIT:=…}"`, `- Kit:`, `**Kit:**`, `> Kit:`, K cirílica, tabulador, minúsculas y mixtas) en el brief y en el bloque: una sola asignación ejecutable y, ejecutando en Git bash cada línea copiada, `SHAREDKIT` no se asigna. Coste aceptado y documentado en el docstring: un comando legítimo del ledger con `SHAREDKIT` llega citado y no se puede copiar; el brief ya trae el kit (f1397e6) |
| 2 | Important | A1+B1+B2+D1: `_iniciativa_al_capturar` es una segunda regla de «iniciativa en curso», distinta de la regla única (`docs/WORK-RESUME.md:137-142`, `progress-report.py:546`). No mira el estado en la tabla, se salta la preferencia por la pendiente, corta a 200 carpetas en el orden de `scandir` y aun así sella `vigente` (atribución errónea; diverge en 6 de 7 escenarios). La rama del marcador no valida el slug, así que una carpeta con tilde o con espacio manda la sesión a dead-letter. Además lee hasta 200 `tasks.md` en el teardown (p95 de 201 ms con 500 iniciativas) | T-21 | corregido | una sola regla: `capture-end` guarda solo el slug del marcador abierto (si casa con `_INICIATIVA_RE`; leyendo `usage-state.json`, sin recorrer el roadmap ni abrir ledgers) y `replay` lo usa con `vigente`; sin slug aplica `iniciativa_activa` (regla única) con el umbral de 24 h; un slug inválido de un envelope antiguo se descarta con aviso, sin dead-letter (`journal.py` `_slug_capturado`). `test_f4fix3_2_*` cubre estado en la tabla, comentario, pendiente más reciente al 100 %, carpeta con tilde y con espacio con marcador, replay a 0, 2 y 14 h, sin dead-letter. p95 de `capture-end` (subproceso, 30 iteraciones, dos pasadas): 0 iniciativas 253 y 286 ms; 500 iniciativas 247 y 279 ms (antes: 288 y 473 ms). `docs/WORK-RESUME.md` y su espejo EN actualizados (86a67c7) |
| 3 | Minor | B4: el drenaje se hace «una vez por estado de la cola», así que un envelope reencolado tras un fallo (o con el cerrojo tomado) no se reintenta mientras la caché acierte | T-20 | corregido | el drenaje se reintenta a los 30 s si la cola no se movió; `f4fix2 gap 6` avanza el reloj (7dec2f9) |
| 4 | Minor | B5: los avisos permanentes («Journal (estado operativo…», «cola dañada», «outbox.py no disponible») se tratan como transitorios, y la caché queda apagada para siempre | T-20 | corregido | solo `bloqueado (otro replay en curso)` es transitorio; un aviso permanente («outbox.py no disponible») se cachea; test en `f4fix2 gap 7` (7dec2f9) |
| 5 | Minor | D2: con un acierto de caché, el drenaje lanza el servicio de contexto completo en cada turno (≈ 1 s), cuando solo hace falta el replay | T-20 | corregido | el drenaje manda `source: 'drain'` y el hook ejecuta solo `journal replay`; `test_f4fix3_5_*` y la comprobación de `sources` en `f4fix2 gap 6` (7dec2f9) |
| 6 | Minor | B6: `_RED_RE` con `{0,6}` palabras da por evidencia la prosa que niega el RED («RED no observado…», «RED sin observar…») | T-21 | corregido | `_RED_RE` rechaza `RED no|sin|ni|nunca|aún|todavía …`; `test_f4fix3_6_*` (66112f0) |
| 7 | Minor | A2: la fila 14 del intento 1 no nombra `test_f4fix2_14_*`, y ese test no tiene RED aunque el rojo era demostrable con el `perf.md` de `2080b49` | T-17, T-18 | corregido | la fila 14 del intento 1 nombra `test_f4fix2_14_*`; rojo observado: ese test falla con el `perf.md` de `2080b49` (salida pegada en el RED fix3) |
| 8 | Minor | A3: TOKEN-EFFICIENCY ES/EN dice que la receta «respeta esa ruta si ya existe»; con `CLAUDE_PLUGIN_ROOT` definido, ya no | T-19 | corregido | TOKEN-EFFICIENCY ES/EN dicen que la receta usa la ruta solo sin `CLAUDE_PLUGIN_ROOT` y si es absoluta con el marcador; `test_f4fix3_8_*` |
| 9 | Minor | A4: el GREEN del fix2 dice que `tokens.md` «aún no está copiado» (lo está desde `b361040`), y `outbox.py`, `journal-capture.py` y `progress-report.py` no figuran en `Archivos` de T-20/T-21 | T-20, T-21 | corregido | GREEN de fix2 corregido (abajo, con la salida de `test_f4fix2_misc` sin la variable) y `outbox.py`, `journal-capture.py` y `progress-report.py` añadidos a `Archivos` de T-20/T-21; `test_f4fix3_9_*` |
| 10 | Minor | C-nota: sin `CLAUDE_PLUGIN_ROOT` (Codex, OpenCode o el bundle copiado), la receta acepta un `SHAREDKIT` relativo que contenga el marcador | T-19 | corregido | `case "$SHAREDKIT" in /*|?:*)` en las 9 recetas y en `capability-check.md`: un `SHAREDKIT` relativo con marcador no se acepta; cupo en CA-22 (evaluator 15.465 bytes LF ≤ 15.513, +34 bytes); `test_f4fix3_10_*` (f1397e6) |

**fix3 — RED y GREEN**

RED fix3 (gap 1): `tests/test_f4fix3_kit.py` sobre `3bfa6c5` falló con 33 failed: la neutralización reconocía formas (`SHAREDKIT=tools/…`, comillas dobles relativas, `$'…'`, `~`, `export`, `declare`, `printf -v`, `: "${SHAREDKIT:=…}"`, `- Kit:`, `**Kit:**`, `> Kit:`, K cirílica, tabulador y minúsculas salían intactos) · 2026-11-10.
RED fix3 (gap 2): `tests/test_f4fix3_journal.py` sobre `3bfa6c5` falló con 5 failed, 1 passed: `_iniciativa_al_capturar` seguía en el código, el envelope guardaba una iniciativa distinta de la regla única, una carpeta con tilde o con espacio mandaba la sesión a dead-letter y el coste de captura con 500 iniciativas subía (288 → 473 ms de p95 de subproceso) · 2026-11-10.
RED fix3 (gaps 3-5): `tests/opencode-plugin.test.mjs -- "f4fix2 gap"` sobre `3bfa6c5` falló con 2 failed: el drenaje no se reintenta con la cola quieta, ejecuta el contexto completo (`source: 'resume'`) y trata como transitorio cualquier aviso del journal · 2026-11-10.
RED fix3 (gap 6): `tests/test_f4fix3_misc.py` falló: `RED no observado:`, `RED sin observar:` y `RED aún no (gap 6):` casaban como evidencia · 2026-11-10.
RED fix3 (gap 7): `test_f4fix2_14_*` sobre `3bfa6c5` con el `perf.md` de `2080b49` (sin el enlace a `tokens.md`) falló con `AssertionError: assert '[`tokens.md`](tokens.md)' in '# Rendimiento de procesos — medidas antes y después (Fase 3, CA-05)…'` · 2026-11-10.
RED fix3 (gaps 8, 9, 10): `test_f4fix3_8_*` falló con la frase «respeta esa ruta si ya existe»; `test_f4fix3_9_*` con `Archivos` de T-20/T-21 sin los tres ficheros; `test_f4fix3_10_*` falló: un `SHAREDKIT=tools/agent-kits/shared` relativo con marcador se aceptaba · 2026-11-10.

GREEN fix3 (gap 9, sustituye al de fix2 sobre `tokens.md`): `tokens.md` está versionado desde `b361040`; `test_f4fix2_misc` sin `F4FIX2_TOKENS_MD` sobre `3bfa6c5` dio `1 failed, 5 passed` con el `perf.md` de `2080b49` (solo el `14`, el rojo del gap 7) y `6 passed` con el `perf.md` vigente. Tras el fix3 las cifras de agentes cambian (+34 bytes por receta): el borrador de `tokens.md` a `f1397e6` está entregado al coordinador y `test_f4fix2_5_*` pasa con `F4FIX2_TOKENS_MD` apuntando a él.
GREEN fix3: `context-footprint.py` `cb6fb40` → `f1397e6` en LF: `agents/evaluator.md` 14.921 → 15.166 caracteres (15.465 bytes LF ≤ 15.513), `agents/implementer.md` 29.396 → 28.950, `capability-check.md` 5.491 → 5.597, vía rápida 15.066 − 9.015 = 6.051 ≥ 6.000 (sin cambios en `dev-cycle.md`).
