---
tasks: debt-cleanup
descripcion: Saldar TODAS las deudas anotadas por las tres iniciativas del 2026-09-02 (live-visibility, deterministic-guardrails, adversarial-review) — debounce atómico, título sin negrita, modo de hooks.json, rutas case-insensitive e índice del roadmap en el guardrail, stems con límite y `revision.excluir` en la lente C, paso 5-ter de /setup, copia manual de la CI vigilada, linter de nombres genéricos afinado, suite de SHELL de los hooks y lista de verificación manual.
estado: completado        # borrador | en-progreso | completado | cancelado
creado: 2026-09-02
actualizado: 2026-09-02
via: rapida               # vía rápida de /dev-cycle: sin spec/evaluación/plan; conserva revisión de dos lentes + suites
generacion:
  fuente: estimado        # usage-meter no disponible en este entorno (sandbox cloud)
---

# Checklist de Tareas — debt-cleanup (vía rápida)

| | |
|---|---|
| **Estado** | completado |
| **Fecha** | 2026-09-02 |
| **Plan** | n/a — **vía rápida** (sin spec/evaluación/plan; ledger ligero + revisión de dos lentes + verificación) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del cambio. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador externo— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

> **Decisión del usuario (2026-09-02).** Las tres iniciativas de hoy cerraron en verde pero dejaron deuda anotada en sus secciones «Aceptados como deuda» / «Dudas y decisiones» (`live-visibility`: debounce no atómico, negrita en el título, `hooks.json` 100755, sin suite de shell; `deterministic-guardrails`: rutas case-sensitive, `docs/roadmap/README.md` bloqueado, sin suite de shell; `adversarial-review`: falsos positivos `tokenizer`/`helmet`, `/setup` sin la lente, copia manual de la CI pendiente, aviso «nombre genérico» de `adversarial-review`). Se saldan TODAS en una iniciativa de vía rápida; cada deuda saldada queda marcada en su ledger de ORIGEN (`saldada en 2026-09-02-debt-cleanup (T-XX)`) sin borrar la línea (traza). `CHANGELOG*.md` lo toca el orquestador.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase única — saldar deudas | 6 | 6 | 100% | 5,2 / 5,5h | 0,26 / 0,28h | 0,06 / 0,06h | 105k / 115k |
| **TOTAL** | **6** | **6** | **100%** | **5,2 / 5,5h** | **0,26 / 0,28h** | **0,06 / 0,06h** | **105k / 115k** |

---

## Fase única — saldar deudas

**Estado**: completado · **Estimado**: 5,5h · **Real**: 5,2h (estimado) · **Coste est.**: ≈285 € · **Tokens est.**: 115k

### T-01 — live-visibility: debounce atómico, título sin negrita, modo de `hooks.json`

- **Descripción**: (a) `hooks/progress-line.sh`: el debounce escribe la línea en un temporal (`mktemp` en el MISMO directorio) y hace `mv -f` sobre `.progress-last` (rename atómico); si existe `flock`, la sección crítica (comparar + escribir) se serializa sobre `.claude/.progress-last.lock` (fd 9, se libera al salir); sin `flock` (macOS sin coreutils) solo el rename → como mucho duplicadas, nunca perdidas ni a medias. (b) `ledger-lint.py` `parse_ledger`: el título de `### T-XX — **Bold** resto` pierde los `**` interiores (`re.sub(r"\*\*(.+?)\*\*", r"\1", …)`). (c) `hooks/hooks.json` → modo `100644` (`chmod -x` + `git update-index --chmod=-x`); `lint_hooks()` avisa si un `.json` de `hooks/` es ejecutable.
- **Estado**: completado
- **Tiempo humano**: est. 1,0h · real 1,0h (estimado)
- **Tiempo IA (ejec.)**: est. 0,05h · real 0,05h (estimado)
- **Supervisión**: est. 0,01h · real 0,01h (estimado)
- **Archivos**: `hooks/progress-line.sh`, `hooks/hooks.json`, `.gitignore`, `agent-kits/shared/ledger-lint.py`, `agent-kits/shared/test_progress_report.py`, `scripts/lint_plugin.py`, `tests/test_lint_plugin.py`, `docs/roadmap/2026-09-02-live-visibility/tasks.md` (deudas marcadas como saldadas)

**Criterios de aceptación**
- [x] (a) 6 invocaciones concurrentes de `progress-line.sh` con la misma línea → **exactamente 1** `systemMessage` con `flock` (medido: 5 rondas manuales y `test_progress_line_seis_concurrentes_debounce_atomico`, 3 ejecuciones de la suite). **Honestidad sobre la degradación sin `flock`:** medido con un PATH sin `flock` en 5 rondas de 6 → 2, 4, 2, 2 y 1 emitidas (el rename es atómico, pero dos lectores pueden ver el estado viejo a la vez) → la aserción del test en esa rama es «≥ 1, todas idénticas, `.progress-last` íntegro y sin temporales huérfanos», y el comentario de cabecera del hook lo dice tal cual. Sin `flock` no se crea `.progress-last.lock` (`test_progress_line_sin_flock_degrada_a_rename_atomico`). `.gitignore` cubre `.progress-last.lock` y los temporales `.progress-last.*`.
- [x] (b) `test_titulo_con_negrita_interior_sale_sin_asteriscos` (`### T-03 — **Bold** resto del título` → línea `en curso: T-03 Bold resto del título`, sin `**`; `resumir()` devuelve `titulo: "Bold resto del título"`). Salida de `ledger-lint.py` **byte-idéntica en los 18 ledgers previos (19 con este)** de `docs/roadmap/*/tasks.md` frente a `git show HEAD:agent-kits/shared/ledger-lint.py` (salida completa + exit code; ninguno usa negrita en el título → idéntica, como se esperaba).
- [x] (c) `git ls-files -s hooks/hooks.json` → `100644`. `lint_plugin` caso 16: `hooks.json` con `0o755` → aviso `hooks/hooks.json: un .json no debería ser ejecutable`; con `0o644` → sin aviso; sigue exit 0 (aviso, no error). `test_todos_los_hooks_son_bash_valido_y_ejecutables` (suite de shell) afirma además que los `.sh` son ejecutables y `bash -n` limpio y que ningún `.json` de `hooks/` lo es.

### T-02 — deterministic-guardrails: rutas case-insensitive e índice del roadmap permitido

- **Descripción**: (a) `guardrail-check.py`: `_ROADMAP_RE`/`_SECSCAN_RE` con `re.I`; comparación de `tasks.md`/`testing` en minúsculas (`Docs/Roadmap/x/Spec.md` deny, `DOCS/ROADMAP/x/TASKS.md` allow). (b) `es_ledger()`/`check_alcance`: el implementer puede tocar `docs/roadmap/README.md` (índice de iniciativas, que el cierre de cada iniciativa actualiza) — SOLO ese fichero en la raíz; `CALIBRATION.md`/`DRIFT.md`/`BACKLOG.md` siguen deny y quedan DOCUMENTADOS como diseño (los escriben `/retro`, `/spec-drift`, `/pm-backlog`, comandos que no pasan por el hook) en el docstring del script, en `docs/agents/implementer.md` y en `agents/implementer.md` (una frase); la razón del deny en la raíz lo dice también. (c) `docs/CONVENTIONS.md` + EN, sección de hooks: los hooks tienen suite de shell (`tests/test_hooks_shell.py`, T-06) y el alcance incluye el índice + case-insensitive.
- **Estado**: completado
- **Tiempo humano**: est. 0,8h · real 0,7h (estimado)
- **Tiempo IA (ejec.)**: est. 0,04h · real 0,04h (estimado)
- **Supervisión**: est. 0,01h · real 0,01h (estimado)
- **Archivos**: `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/test_guardrail_check.py`, `docs/agents/implementer.md`, `agents/implementer.md`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `docs/roadmap/2026-09-02-deterministic-guardrails/tasks.md` (deudas marcadas como saldadas)

**Criterios de aceptación**
- [x] (a) `test_cleanup_alcance_case_insensitive`: `Docs/Roadmap/2026-01-01-x/Spec.md` → deny «solo toca tasks.md»; `DOCS/ROADMAP/2026-01-01-x/TASKS.md` → allow; `Docs/Security-Scan/STATE.md` → deny; `docs/roadmap/x/Testing/tasks.md` → deny (qa). CLI: `Docs/Roadmap/x/Spec.md` → JSON oficial `deny`, exit 0.
- [x] (b) `test_cleanup_raiz_roadmap_readme_permitido_resto_deny`: `docs/roadmap/README.md` y `/proy/docs/roadmap/readme.md` → allow (también con HEAD en `main`: cuenta como ledger para `ramaPrincipal`); `CALIBRATION.md`/`DRIFT.md`/`BACKLOG.md` → deny con razón «raíz de docs/roadmap/: … los escriben /retro, /spec-drift y /pm-backlog»; el `README.md` de una INICIATIVA (`docs/roadmap/2026-01-01-x/README.md`) sigue deny. Docstring, `docs/agents/implementer.md` (fila `alcance` + «No toca…») y `agents/implementer.md` §0 lo documentan como diseño. `pytest agent-kits/shared/test_guardrail_check.py` → 24 passed (22 + 2).
- [x] (c) `docs/CONVENTIONS.md` y `docs/en/CONVENTIONS.md` regla 8: «Visibilidad en vivo» cita la suite de shell (`tests/test_hooks_shell.py`: qué lanza y qué afirma, skip sin `bash`); «Dos clases de hooks» dice «solo `tasks.md` —más el índice `docs/roadmap/README.md`—, rutas case-insensitive».

### T-03 — adversarial-review: heurística de la Lente C (stems con límite, `revision.excluir`, /setup 5-ter)

- **Descripción**: (a) `review-lens-select.py` `RUTA_RE`: stems con límite final donde son prefijo de palabras inocuas — `tokens?(?![a-z])`, `helm(?![a-z])`, `acl(?![a-z])`, `rbac(?![a-z])`, `cors(?![a-z])`, `auth(?!or)`; siguen amplios `sessions?`, `login`, `oauth`, `jwt`, `password`, `passwd`, `secrets?`, `crypt`, `permissions?`, `csrf`, `upload`, `payment`, `billing`, `docker`, `nginx`, `k8s` (más `.env*`, `Dockerfile*`, `.github/workflows/`). (b) `.claude/dev.json` → `"revision": {"lenteSeguridad": …, "excluir": ["glob", …]}`: globs `**`-aware (traductor `glob_to_regex` de `confluence-scope.py` por `importlib`, copia local si la skill no está — mismo patrón que `scope-check.py`) que se excluyen SOLO de la heurística de RUTA (el contenido añadido sigue contando); `leer_config()` devuelve (modo, excluir, avisos), `excluir` que no sea lista de cadenas → se ignora + aviso. Documentado en la skill §1 y en CONVENTIONS regla 9 (+EN) con el ejemplo `["hooks/**"]` para un repo cuyos hooks se llamen `session-*.sh`. (c) `commands/setup.md` paso **5-ter «Lente de seguridad de la revisión (opt-in)»**: pregunta «¿Añadir una tercera lente de SEGURIDAD … [auto (recomendado) / siempre / nunca]», persiste `revision.lenteSeguridad` mergeando `dev.json`, menciona `revision.excluir` como ajuste manual, idempotente; `description` del frontmatter y filas de `/setup` en `README.md`/`README.es.md`/`CLAUDE.md`/`docs/README.md`/`docs/en/README.md` actualizadas.
- **Estado**: completado
- **Tiempo humano**: est. 1,2h · real 1,1h (estimado)
- **Tiempo IA (ejec.)**: est. 0,06h · real 0,06h (estimado)
- **Supervisión**: est. 0,01h · real 0,01h (estimado)
- **Archivos**: `skills/adversarial-review/scripts/review-lens-select.py`, `skills/adversarial-review/scripts/test_review_lens_select.py`, `skills/adversarial-review/SKILL.md`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `commands/setup.md`, `README.md`, `README.es.md`, `CLAUDE.md`, `docs/README.md`, `docs/en/README.md`, `docs/roadmap/2026-09-02-adversarial-review/tasks.md` (deudas marcadas como saldadas)

**Criterios de aceptación**
- [x] (a) `test_cleanup_stems_con_limite_final`: `tokens.py`, `token_store.py`, `auth_middleware.py`, `sessions/x.py`, `hooks/session-context.sh`, `deploy/helm/values.yaml`, `acl.py`, `cors-config.js`, `auth/oauth2.py`, `secrets_loader.py` → true por ruta; `tokenizer.py`, `helmet.py`, `helmets.py`, `author.md`, `authors.py`, `aclimate.py`, `corsair.py` → false. `test_fix1_ruta_anclada…` actualizado (`tokenizer.py`/`helmet.py` pasan a negativos). El propio script sigue sin dispararse a sí mismo (`test_el_propio_script_no_se_dispara_a_si_mismo`: el docstring nuevo evitó el literal `eval(`).
- [x] (b) `test_cleanup_revision_excluir_aplica_a_ruta_no_a_contenido`: con `"excluir": ["hooks/**", "deploy/*.yaml"]`, `hooks/session-context.sh` y `deploy/helm.yaml` NO disparan por ruta pero `deploy/sub/helm.yaml` SÍ (`*` = un nivel); una línea con ejecución dinámica añadida en `hooks/session-context.sh` (excluido) → `lente_c: true` con motivo `contenido … eval linea 2`; `"excluir": "hooks/**"` (no lista) → aviso stderr y no excluye. Skill §1 y CONVENTIONS regla 9 ES/EN documentan `excluir` con el ejemplo `["hooks/**"]`. `pytest skills/adversarial-review/scripts` → 22 passed (20 + 2).
- [x] (c) `commands/setup.md` tiene el paso 5-ter entre 5-bis y 6 con la pregunta literal, el merge de `revision.lenteSeguridad` sin pisar otras claves, la mención de `revision.excluir` como ajuste manual y la idempotencia; `description` del frontmatter enumera la lente; las filas de `/setup` en `README.md`, `README.es.md`, `CLAUDE.md`, `docs/README.md` y `docs/en/README.md` mencionan «lente de seguridad de la revisión». `test_readme_badges` OK.

### T-04 — CI y linter: copia manual vigilada y «nombre genérico» afinado

- **Descripción**: (a) `tests/test_ci_manual_copy.py`: si existe `.github/workflows/<x>.yml` debe ser byte-idéntico a `<x>.yml.MANUAL-COPY` (`ci.yml` y `release.yml`); si no existe → `skip` con «copia manual pendiente: cp ci.yml.MANUAL-COPY .github/workflows/ci.yml». Funciona como script (bucle `tests/test_*.py` de la CI) y bajo pytest. `scripts/lint_plugin.py` `lint_manual_copies()`: AVISO cuando ambos existen y difieren, con el `cp` a ejecutar. **Se hizo la copia** `cp ci.yml.MANUAL-COPY .github/workflows/ci.yml` (estaba atrasada: aún tenía la lista fija `test_usage_meter` + `test_task_brief`) en un commit propio, revertible si el orquestador prefiere no tocar la ruta protegida. (b) `lint_plugin.py` `nombre_generico()`: para SKILLS avisa solo si el nombre COMPLETO es un token genérico o tiene un solo token (`review`), no si es compuesto (`adversarial-review`); commands conservan la regla (`setup`, `roadmap-status` avisan).
- **Estado**: completado
- **Tiempo humano**: est. 0,8h · real 0,7h (estimado)
- **Tiempo IA (ejec.)**: est. 0,04h · real 0,04h (estimado)
- **Supervisión**: est. 0,01h · real 0,01h (estimado)
- **Archivos**: `tests/test_ci_manual_copy.py` (nuevo), `scripts/lint_plugin.py`, `tests/test_lint_plugin.py`, `.github/workflows/ci.yml`

**Criterios de aceptación**
- [x] (a) `python3 tests/test_ci_manual_copy.py` → `OK: .github/workflows/ci.yml idéntico a ci.yml.MANUAL-COPY (2068 bytes)` · `OK: … release.yml … (1700 bytes)` · `2/2 OK`, exit 0; con la copia atrasada (probado con `git stash` del fichero) → `FAIL … copia manual pendiente: cp ci.yml.MANUAL-COPY .github/workflows/ci.yml`, exit 1, y `lint_plugin` → 4 avisos (el nuevo, con el `cp`). Pytest: 3 passed (2 parametrizados + `test_lint_plugin_avisa_con_el_mismo_criterio`). `lint_plugin` caso 18: sin copia → sin aviso; iguales → sin aviso; distintas → aviso con `cp`. La CI ya recorre `tests/test_*.py` por bucle → la suite entra sola.
- [x] (b) `lint_plugin` caso 17: `skill adversarial-review` sin aviso, `skill review` con aviso, `command setup` y `command roadmap-status` con aviso (`3 avisos` en la fixture). Sobre el repo: `python3 scripts/lint_plugin.py` → `8 agentes · 0 errores · 3 avisos` (4 → 3). `test_lint_plugin: 18/18 OK`.

### T-05 — Verificación en sesión real: lo automatizable y la lista manual

- **Descripción**: lo automatizable lo cubre `tests/test_hooks_shell.py` (T-06). Además `docs/observability.md` + `docs/en/observability.md` ganan la sección corta «Cómo comprobar los hooks en una sesión real» (3 pasos: editar un `tasks.md` y ver la línea 📋 + debounce; `/clear` + reanudar y ver el contexto de sesión; como implementer intentar escribir `docs/roadmap/x/spec.md` y ver el deny) + qué revisar si un paso no ocurre. Es la lista que el usuario hará tras el release: **no se inventan resultados** (aquí no hay sesión real de Claude Code con el plugin cargado).
- **Estado**: completado
- **Tiempo humano**: est. 0,4h · real 0,4h (estimado)
- **Tiempo IA (ejec.)**: est. 0,03h · real 0,02h (estimado)
- **Supervisión**: est. 0,01h · real 0,01h (estimado)
- **Dependencias**: T-06
- **Archivos**: `docs/observability.md`, `docs/en/observability.md`, `docs/roadmap/README.md` (fila de la iniciativa)

**Criterios de aceptación**
- [x] Sección `### Cómo comprobar los hooks en una sesión real` en ES y EN, tras la tabla de visibilidad en vivo, con los 3 pasos y el resultado ESPERADO (no afirmado como observado) más la escalera de diagnóstico (`lint_plugin` → `test_hooks_shell` → registro del hook en Claude Code).
- [x] Ningún resultado de sesión real se da por verificado en este ledger: la evidencia automática es la suite de T-06; la manual queda **pendiente del usuario tras el release**.

### T-06 — `tests/test_hooks_shell.py`: suite de shell para los hooks y la statusline

- **Descripción**: pytest + `subprocess.run([bash, hook], input=json, env={CLAUDE_PLUGIN_ROOT, CLAUDE_PROJECT_DIR, HOME, PATH, LC_ALL})` sobre un proyecto temporal cuyo ledger es una copia REAL de `docs/roadmap/2026-09-02-adversarial-review/tasks.md` puesta en `en-progreso` (T-04 abierta → `T-03/4`). Casos (20 ≥ 14): progress-line ×7 (JSON con `systemMessage`; debounce 2.ª idéntica → vacío y re-emisión al cambiar el estado; ruta Windows `\`; `edits[]` de MultiEdit; stdin vacío y fichero ajeno → exit 0 vacío; 6 concurrentes → aserción honesta de T-01a; sin `flock` → degrada sin lock); subagent-progress ×2 (activa → `systemMessage`; sin activas → vacío); session-context ×2 (activa → SOLO `hookSpecificOutput.hookEventName: SessionStart` + `additionalContext`; sin activas → vacío); implementer-guardrail ×4 (deny `spec.md` → JSON oficial; allow `tasks.md` → vacío; deny `git push --force`; PATH sin `python3` → exit 0 + `systemMessage` una vez y marca `.guardrail-nopython`, 2.ª vez vacío); mark-docs-pending ×1 (`security-scan` no marca, `docs/` marca); ledger-lint-warn ×1 (ledger coherente e incoherente → exit 0); statusline ×2 (JSON oficial → UNA línea `[Opus] $0.01 ctx 8% · 📋 demo T-03/4 …`; stdin vacío → exit 0); `bash -n` + bits de ejecución ×1. `pytestmark = skipif(no bash)`; `main()` para el bucle de la CI (sin pytest → mensaje y exit 0).
- **Estado**: completado
- **Tiempo humano**: est. 1,3h · real 1,3h (estimado)
- **Tiempo IA (ejec.)**: est. 0,06h · real 0,05h (estimado)
- **Supervisión**: est. 0,01h · real 0,01h (estimado)
- **Archivos**: `tests/test_hooks_shell.py` (nuevo)

**Criterios de aceptación**
- [x] `python3 -m pytest -q tests/test_hooks_shell.py` → **20 passed** en 3 ejecuciones consecutivas (~1,7 s); `python3 tests/test_hooks_shell.py` (modo script de la CI) → 20 passed. Todos los casos afirman `exit 0`; los de «vacío» afirman `(rc, stdout, stderr) == (0, "", "")`.
- [x] Sin `python3` en PATH (bin temporal con solo bash/coreutils) el guardrail devuelve `{"systemMessage": …python3…}` sin `permissionDecision`, crea `.claude/.guardrail-nopython` y a la 2.ª calla. Sin `flock` en PATH progress-line emite la 1.ª, calla la 2.ª idéntica y no crea `.progress-last.lock`.
- [x] CI: `ci.yml.MANUAL-COPY` ya recorre `tests/test_*.py` por bucle (`python "$t"`) → `test_hooks_shell.py` y `test_ci_manual_copy.py` entran solos; `.github/workflows/ci.yml` copiado byte-idéntico (T-04a). No hace falta tocar la lista.

---

## Verificación final (DoD del implementer, rama `feature/deterministic-guardrails`)

- `python3 -m pytest -q tests agent-kits/shared skills/adversarial-review/scripts` → **184 passed** (156 previos + 28: 1 `test_progress_report` + 2 `test_guardrail_check` + 2 `test_review_lens_select` + 3 `test_ci_manual_copy` + 20 `test_hooks_shell`). Suites-script de la CI (`for t in tests/test_*.py`) todas exit 0, incl. `test_lint_plugin: 18/18 OK` y `test_ci_manual_copy: 2/2 OK`.
- `python3 scripts/lint_plugin.py` → `8 agentes · 0 errores · **3 avisos**` (`retro`, `roadmap-status`, `setup`; el de `adversarial-review` desaparece por T-04b). `bash -n hooks/*.sh statusline/*.sh` OK. `python3 scripts/release.py --check` → `OK: todas coinciden en 1.14.1`.
- `ledger-lint.py` de este fichero → `0 incoherencias · 0 avisos`, exit 0. Salida de `ledger-lint.py` byte-idéntica en los **18** ledgers de `docs/roadmap/*/tasks.md` frente a `HEAD` (el brief decía 20; en el repo hay 18 `tasks.md`).
- `review-lens-select.py --base b3d8c9d` sobre este paquete → `lente_c: true` por **un solo motivo**: `ruta .github/workflows/ci.yml ~ .github/workflows/` (la copia manual de T-04a). Es correcto que la lente C mire ese fichero; el diff es `cp` literal de `ci.yml.MANUAL-COPY`.
- `scope-check.py docs/roadmap/2026-09-02-debt-cleanup --base b3d8c9d` → `✅ en alcance` todos · `❌ fuera de alcance (0)` · exit 0 (`--base` = HEAD del orquestador «docs: CHANGELOG…», porque la rama es compartida con las tres iniciativas anteriores).
- Commits lógicos por tarea (`T-01` … `T-06`, más el de la copia de la CI aparte). Sin push. `CHANGELOG*.md` sin tocar.

## Dudas y decisiones para el orquestador

- **Copia de `.github/workflows/ci.yml` hecha aquí** (commit propio, `T-04a`): la ruta era «protegida para las herramientas remotas» y las iniciativas anteriores la dejaron para una copia manual. Con la copia atrasada, `test_ci_manual_copy` falla (por diseño) y `lint_plugin` da 4 avisos — el DoD «verde + 3 avisos» solo se cumple con la copia hecha. Si no se quiere tocar esa ruta desde aquí, `git revert` de ese commit y hacer el `cp` a mano antes del release; el test y el aviso lo recordarán.
- **Debounce sin `flock`:** la deuda pedía «exactamente 1» — se cumple con `flock` (Linux/CI). Sin `flock` el rename atómico garantiza integridad, no unicidad (medido 1–4 emisiones de 6); el test y el hook lo dicen con esa honestidad en vez de fingir la garantía.
- **`docs/roadmap/README.md` permitido al implementer** invierte la decisión de deterministic-guardrails («lo toca el orquestador»): es el único fichero de la raíz que el cierre de cada iniciativa edita y tenía que hacerse a mano fuera del hook. `CALIBRATION`/`DRIFT`/`BACKLOG` siguen bloqueados y ahora documentados como diseño.
- **Stems ampliados a plural** (`sessions?`, `tokens?`, `secrets?`, `permissions?`): el ancla de inicio de token ya los cubría como prefijo; con el límite final en `token` hacía falta el plural explícito para `tokens.py`. Sin cambio de comportamiento en el resto.
- **CHANGELOG** no tocado (orquestador). Verificación manual en sesión real: pendiente del usuario tras el release (lista en `docs/observability.md`).

## Revisión de dos lentes — intento 1: 0 gaps de corrección (0 Critical, 0 Important, 3 Minor: nota de `/clear` en observability ES/EN corregida; cifra «18 ledgers» precisada; `docs/roadmap/readme.md` en minúsculas permitido = decisión case-insensitive, aceptado como diseño). 184 tests · lint 0 errores · 3 avisos · 19/19 ledgers idénticos en ledger-lint.

**Post-volcado (verificación en el disco del usuario):** el aviso «hooks.json ejecutable» saltaba en falso porque el montaje OneDrive/WSL muestra TODO como ejecutable → `lint_plugin.py` pasa a leer el modo del ÍNDICE de git (`git ls-files -s`, 100755) y solo cae a `os.access` sin git (+ caso 16b en `tests/test_lint_plugin.py`). En el disco: 0 errores · 3 avisos.
