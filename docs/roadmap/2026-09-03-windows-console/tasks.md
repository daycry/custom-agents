---
tasks: windows-console
descripcion: Salida UTF-8 segura en toda consola — bug REAL reportado por el usuario en Windows/PowerShell (`python scripts/release.py 1.16.0` → `lint_plugin.py` revienta con `UnicodeEncodeError: 'charmap' codec can't encode characters` al imprimir `⚠️`, y `release.py` disfraza el crash como `changelog-sync --check: PENDIENTE`). (1) Los **27 scripts Python versionados con caracteres no ASCII** reconfiguran `sys.stdout`/`sys.stderr` a UTF-8 con `errors="replace"` al arrancar, con el snippet replicado LITERAL (siguen siendo standalone: el paquete portable y los agentes los invocan sueltos), test de regresión `tests/test_console_encoding.py` que descubre la lista dinámicamente y aviso del linter para el script futuro que traiga símbolos sin el snippet; (2) `release.py` distingue «el check FALLA» (exit 1 legítimo) de «el check NO SE PUDO EJECUTAR» (traceback / exit ≠ 0,1 / `Traceback` en stderr) y esto último BLOQUEA con las 3 últimas líneas de stderr; (3) doc ES/EN (`CONVENTIONS` regla 8, `plugin-dev`, `INSTALL`), gotcha `GOT-005` y fila en el índice de knowledge. (4) **T-04** cierra las dos mitades que faltaban del MISMO bug, encontradas por la revisión de dos lentes: el snippet cubre también `sys.stdin` (sin él, el guardrail del implementer dejaba de denegar en silencio ante cualquier contenido con emoji) y todo `.py` que capture a un hijo lo decodifica con `encoding="utf-8", errors="replace"` (sin eso el PADRE revienta donde antes daba su veredicto); más linter estructural con `ast`, criterio único compartido con la suite, descubridor a prueba de rutas citadas y fila del roadmap dentro de su tabla. (5) **T-05** cierra los gaps del intento 2 de la revisión: el criterio pasa a mirar también al que LEE (`no-ASCII en el fuente O lee de sys.stdin`, con `ast`), entra la 28.ª pieza (`pick_asset.py`, ASCII pura y lectora de stdin, cuyo fallo se presentaba como «no hay binario para tu plataforma»), la doc dice EXACTAMENTE la regla que el guardarraíl vigila, tres tests dejan de mentir (la comparación de veredictos solo mira lo versionado; el test del `except` mide sobre un script real y tiene su mutante; la salida degradada a ASCII falla en vez de saltarse) y los `python3 -c` de `hooks/` y `statusline/` reconfiguran con `PYTHONIOENCODING=utf-8:replace`.
estado: completado        # borrador | en-progreso | completado | cancelado
creado: 2026-09-03
actualizado: 2026-09-03
via: rapida               # vía rápida de /dev-cycle: sin spec/evaluación/plan; conserva revisión de dos lentes + suites
verificacion: obligatoria # cada `### T-XX` lleva `- **Verificación**:`; ledger-lint lo exige (exit ≠ 0 si falta)
generacion:
  fuente: estimado        # usage-meter no disponible en este entorno (sandbox cloud)
---

# Checklist de Tareas — windows-console (vía rápida)

| | |
|---|---|
| **Estado** | completado |
| **Fecha** | 2026-09-03 |
| **Plan** | n/a — **vía rápida** (sin spec/evaluación/plan; ledger ligero + revisión de dos lentes + verificación) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del cambio. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador externo— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

> **Bug reportado por el usuario (2026-09-03, con traceback real).** Al ejecutar `python scripts/release.py 1.16.0` en PowerShell (Windows, locale con ANSI codepage `cp1252`), `lint_plugin.py` sale con exit 1 por `UnicodeEncodeError: 'charmap' codec can't encode characters in position 0-1` en `print(f"⚠️  {w}")`, y en cascada `release.py` marca `changelog-sync --check` como **PENDIENTE** (lee su exit code, que también es el del crash). Reproducido en Linux con `PYTHONIOENCODING=cp1252 python3 scripts/lint_plugin.py` → mismo traceback. **Dos defectos, no uno:** el script revienta al imprimir, y el orquestador del release presenta el crash como deuda de notas.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase única — consola Windows | 6 | 6 | 100% | 11,6 / 11,6h | 0,67 / 0,67h | 0,17 / 0,17h | 320k / 320k |
| **TOTAL** | **6** | **6** | **100%** | **11,6 / 11,6h** | **0,67 / 0,67h** | **0,17 / 0,17h** | **320k / 320k** |

---

## Fase única — consola Windows

**Estado**: completado · **Estimado**: 10,4h · **Real**: 10,4h (estimado) · **Coste est.**: ≈545 € · **Tokens est.**: 285k
(T-01 a T-03: 4,3h · ≈225 € · 115k. T-04, la primera ronda de corrección de la revisión de dos lentes: 3,5h · ≈185 € · 95k. T-05, el cierre de los gaps del intento 2: 2,6h · ≈135 € · 75k.)

### T-01 — Salida UTF-8 segura en toda consola (los 27 scripts + test de regresión + aviso del linter)

- **Descripción**: los **27 scripts Python versionados con caracteres no ASCII** (`for f in $(git ls-files '*.py' | grep -v test_); do LC_ALL=C grep -qP '[^\x00-\x7F]' "$f" && echo "$f"; done`, menos `evals/fixtures/project/src/app.py` — fixture de un proyecto AJENO que simula el código del consumidor, no una pieza del plugin) reconfiguran `sys.stdout`/`sys.stderr` a UTF-8 con `errors="replace"` **al arrancar**, a nivel de módulo justo tras el bloque de imports (no dentro de `main()`: hay scripts que imprimen desde funciones sueltas —`lint_plugin.lint_*`, `doctor._check`— o que se importan desde tests y desde otros scripts por ruta). El snippet se replica **LITERAL** en los 27 en vez de vivir en un módulo compartido: los scripts son **standalone** por contrato (el paquete portable `export-skills.py` los copia sueltos y los agentes los invocan con `python3 <ruta>` sin `PYTHONPATH`), así que un `import` compartido sería exactamente la dependencia que el paquete portable no puede satisfacer — replicar 4 líneas es el precio correcto, y el linter + el test lo vigilan para que no se olvide en el siguiente script. **Decisión: SIN modo ASCII** (`CUSTOM_AGENTS_ASCII` / `--ascii`) — justificada con medición en «Notas de cierre»: la premisa («los emojis saldrán como `?`») **no se cumple**, porque `reconfigure(encoding="utf-8")` sustituye al codec cp1252 y la salida sale en UTF-8 íntegro (`errors="replace"` queda de red de seguridad, nunca se dispara), así que un modo ASCII replicado en 7 scripts añadiría superficie sin arreglar nada medible. **Test de regresión** `tests/test_console_encoding.py`: descubre la lista con el MISMO grep (un script nuevo con emojis entra solo; **T-05 amplía ese criterio**: también entra el que lee de `sys.stdin`, aunque su fuente sea ASCII pura) y, por cada script, (a) exige el snippet por patrón y (b) lo ejecuta en su modo más barato que de verdad imprime no-ASCII, con `PYTHONIOENCODING=cp1252` y con `ascii`, afirmando exit code esperado y `UnicodeEncodeError` ausente de stderr. **`lint_plugin.py`**: aviso (no error) si un `.py` versionado tiene caracteres no ASCII y NO lleva el snippet.
- **Estado**: completado
- **Tiempo humano**: est. 2,5h · real 2,5h (estimado)
- **Tiempo IA (ejec.)**: est. 0,15h · real 0,15h (estimado)
- **Supervisión**: est. 0,04h · real 0,04h (estimado)
- **Archivos**: `tests/test_console_encoding.py` (nuevo), `scripts/lint_plugin.py`, `tests/test_lint_plugin.py`, y el snippet en los 27: `agent-kits/qa/coverage-check.py`, `agent-kits/qa/qa-gate.py`, `agent-kits/shared/doctor.py`, `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/journal.py`, `agent-kits/shared/ledger-lint.py`, `agent-kits/shared/model-tier.py`, `agent-kits/shared/progress-report.py`, `agent-kits/shared/scope-check.py`, `agent-kits/shared/skill-index.py`, `agent-kits/shared/task-brief.py`, `agent-kits/shared/usage-meter.py`, `evals/check.py`, `evals/run.py`, `scripts/export-skills.py`, `scripts/release.py`, `skills/adversarial-review/scripts/review-lens-select.py`, `skills/api-contract/scripts/openapi-lint.py`, `skills/changelog-sync/scripts/changelog-sync.py`, `skills/code-health/scripts/code-health.py`, `skills/confluence-publish/scripts/confluence-scope.py`, `skills/dependency-upgrade/scripts/deps-inventory.py`, `skills/jira-sync/scripts/jira-flow.py`, `skills/jira-sync/scripts/worklog.py`, `skills/roadmap-dashboard/scripts/build_dashboard.py`, `skills/unit-tests/scripts/coverage-gate.py`
- **Verificación** (ejecutada 2026-09-03): `PYTHONIOENCODING=cp1252 python3 scripts/lint_plugin.py` → **exit 0**, sin traceback, salida legible con los emojis intactos — literal: «⚠️  command `roadmap-status`: nombre genérico — sin instalar como plugin (namespace `custom-agents:`) puede chocar con otro `.claude/`. Ok si se usa como plugin.» — los tres avisos son de piezas DISTINTAS, no tres copias de esa línea: `retro`, `roadmap-status` y `setup`, cada uno en su propia línea con el mismo texto y su nombre de command [corregido en T-04] — y la última línea «lint_plugin: 9 agentes · 0 errores · 3 avisos» · `for f in $(git ls-files '*.py' | grep -v test_); do LC_ALL=C grep -qP '[^\x00-\x7F]' "$f" && ! grep -qF 'reconfigure(encoding="utf-8", errors="replace")' "$f" && echo "FALTA $f"; done` → una sola línea, `FALTA evals/fixtures/project/src/app.py` (el fixture excluido a propósito); los 27 restantes lo llevan · `python3 -m pytest -q tests/test_console_encoding.py` → **165 passed** — desglose comprobado contra el fichero de T-01 (`git show 25c7a7a:tests/test_console_encoding.py`): **2** tests parametrizados solo por script (snippet presente · snippet a nivel de módulo) = 2×27 = 54, **2** parametrizados por script Y codificación (arranca sin reventar · la salida sigue siendo UTF-8) = 2×27×2 = 108, y **3** sin parametrizar (descubridor · script nuevo cazado · `capsys`): 54 + 108 + 3 = **165**. [T-04 amplía el fichero a 229 y T-05 a 246 — ver sus verificaciones] · `python3 tests/test_lint_plugin.py` → `26/26 OK` (casos 25 y 26: `.py` con emoji sin snippet → aviso; con snippet → sin aviso) [T-04 lo lleva a `29/29 OK` y T-05 a `32/32 OK`]

**Criterios de aceptación**
- [x] Los 27 scripts no-ASCII llevan el snippet IDÉNTICO a nivel de módulo, tras los imports (el fixture ajeno `evals/fixtures/project/src/app.py` queda fuera, con motivo escrito)
- [x] `PYTHONIOENCODING=cp1252` y `PYTHONIOENCODING=ascii` sobre CADA script en su modo real de impresión → exit esperado y `UnicodeEncodeError` ausente de stderr
- [x] El test descubre la lista con el mismo grep, así que un script nuevo con símbolos entra solo y falla si no lleva el snippet
- [x] `capsys` de pytest y la salida por pipe no rompen (el `except` cubre los streams sin `reconfigure`); la suite completa sigue verde
- [x] `lint_plugin.py` avisa (no error) del `.py` versionado con no-ASCII sin snippet, con test en los dos sentidos
- [x] La decisión sobre el modo ASCII está tomada y justificada con medición, no con opinión

### T-02 — Que el fallo no se disfrace en `release.py`

- **Descripción**: `release.py` presentaba `changelog-sync --check: PENDIENTE` cuando el script había **crasheado** (el exit 1 del `UnicodeEncodeError` es indistinguible del exit 1 de «hay entradas pendientes»). Ahora los tres checks previos (`lint_plugin.py`, `evals/check.py`, `changelog-sync.py --check`) pasan por un clasificador único `clasificar(r)` → `ok` | `falla` | `error`: **`error`** cuando el exit no es 0 ni 1, o cuando stderr contiene `Traceback` (con `Traceback` gana sobre cualquier exit code — un traceback nunca es un veredicto). En ese caso la línea dice `ERROR al ejecutar` con las **3 últimas líneas de stderr** indentadas y **bloquea el release**, incluido el de `changelog-sync`, que como veredicto es solo un AVISO: la deuda de notas se puede publicar a sabiendas, un entorno roto no. `_run()` además fija `encoding="utf-8", errors="replace"` al leer los pipes de los hijos: tras T-01 los hijos escriben UTF-8, y decodificar eso como cp1252 en Windows puede reventar la propia `release.py` (los bytes `0x81/0x8D/0x8F/0x90/0x9D` no existen en cp1252 y aparecen dentro de emojis comunes como 👍 = `F0 9F 91 8D`). Y el resumen de iniciativas pendientes deja de depender del glifo de la viñeta: se reconoce la FORMA de la línea (`SLUG_PENDIENTE`: «`<viñeta> <slug> (AAAA-MM-DD)`»), para que un hijo que NO escriba UTF-8 —un script legacy o de otro plugin— no pierda los slugs por un `·` degradado a `�` al decodificar.
- **Estado**: completado
- **Tiempo humano**: est. 1,0h · real 1,0h (estimado)
- **Tiempo IA (ejec.)**: est. 0,06h · real 0,06h (estimado)
- **Supervisión**: est. 0,01h · real 0,01h (estimado)
- **Archivos**: `scripts/release.py`, `tests/test_release.py`
- **Verificación** (ejecutada 2026-09-03): `PYTHONIOENCODING=cp1252 python3 scripts/release.py --check` → **exit 0**, sin traceback; salida literal (con su relleno de espacios real, corregido en T-04):
  ```
  plugin.json           : 1.15.0
  marketplace metadata  : 1.15.0
  marketplace plugins   : ['1.15.0']
  OK: todas coinciden en 1.15.0
  CHANGELOG.md    : sección [1.15.0] presente
  CHANGELOG.es.md : sección [1.15.0] presente
  ```
  · `PYTHONIOENCODING=cp1252 python3 skills/changelog-sync/scripts/changelog-sync.py --check --only roles-and-jira-flow` → `changelog-sync --check: sin entradas pendientes ✅` **exit 0** con el emoji íntegro (bytes del pipe: `342 234 205` = `E2 9C 85`); **sin `--only`** el mismo comando sale **1** con el veredicto legítimo «entradas PENDIENTES … · windows-console» — esta iniciativa está cerrada y sus notas quedan fuera de alcance por indicación explícita («NO toques CHANGELOG*.md»), así que ese 1 es la deuda REAL, no un crash (y T-02 lo distingue: sale `PENDIENTE`, no `ERROR al ejecutar`) · `python3 -m pytest -q tests/test_release.py` → **24 passed** (18 antes + 6 nuevos: crash de lint reportado como `ERROR al ejecutar` con las 3 últimas líneas · `changelog-sync` que crashea BLOQUEA en vez de decir PENDIENTE · su exit 1 legítimo sigue siendo aviso que NO bloquea · exit ≠ 0,1 clasificado como error · `clasificar()`/`cola_stderr()` en unitario · el slug pendiente se lee aunque la viñeta no sobreviva a la decodificación) · reproducción del bug ORIGINAL: con un `changelog-sync.py` que revienta con `UnicodeEncodeError`, ANTES → `changelog-sync --check: PENDIENTE` + exit 0 del release; AHORA → `changelog-sync --check: ERROR al ejecutar (exit 1)` + las 3 líneas de stderr + exit 1

**Criterios de aceptación**
- [x] Los tres checks previos distinguen `OK` · `FALLA (exit N)` · `ERROR al ejecutar` con el mismo criterio (`Traceback` en stderr, o exit ∉ {0,1})
- [x] «No se pudo ejecutar» imprime las 3 últimas líneas de stderr y **bloquea** el release (también en `changelog-sync`, cuyo veredicto normal solo avisa)
- [x] El exit 1 legítimo de `changelog-sync --check` sigue siendo AVISO y no bloquea (no se convierte la deuda de notas en un muro)
- [x] `_run()` lee los pipes como UTF-8 con `errors="replace"` (los hijos escriben UTF-8 tras T-01)
- [x] Tests en `tests/test_release.py` con un script que crashea de verdad, no con un mock del mensaje
- [x] El resumen de pendientes nombra la iniciativa aunque la viñeta no sobreviva a la decodificación (hijo sin el snippet de T-01, padre bajo `cp1252`)

### T-03 — Doc y memoria

- **Descripción**: `docs/CONVENTIONS.md` regla 8 (+ espejo EN) — la regla vive donde ya está la de determinismo/degradación de los scripts, sin sección nueva: «todo script del plugin que imprima símbolos no ASCII reconfigura `stdout`/`stderr` a UTF-8 con `errors="replace"` al arrancar; el linter lo vigila y `tests/test_console_encoding.py` lo prueba bajo `cp1252`», con el porqué de replicar el snippet (standalone) y el porqué de no añadir modo ASCII. `skills/plugin-dev/SKILL.md`: una línea en las reglas de cuerpo de pieza nueva (regla 6, junto a Determinismo y Degradación). Gotcha `docs/knowledge/gotchas/GOT-005-consola-windows-cp1252.md` (siguiente NNN libre comprobado: existían GOT-001..004) con `estado: aceptada (validada: usuario, 2026-09-03)` porque lo reportó el usuario con traceback real, y su fila en `docs/knowledge/README.md`. Fila de la iniciativa en `docs/roadmap/README.md`. `docs/INSTALL.md` (+EN): nota junto al callout de Windows ya existente diciendo qué se ve en Windows y por qué. **No se toca `CHANGELOG*.md`** (fuera de alcance por indicación explícita).
- **Estado**: completado
- **Tiempo humano**: est. 0,8h · real 0,8h (estimado)
- **Tiempo IA (ejec.)**: est. 0,04h · real 0,04h (estimado)
- **Supervisión**: est. 0,01h · real 0,01h (estimado)
- **Archivos**: `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `skills/plugin-dev/SKILL.md`, `docs/knowledge/gotchas/GOT-005-consola-windows-cp1252.md` (nuevo), `docs/knowledge/README.md`, `docs/roadmap/README.md`, `docs/INSTALL.md`, `docs/en/INSTALL.md`, `docs/roadmap/2026-09-03-windows-console/tasks.md`
- **Verificación** (ejecutada 2026-09-03): `grep -c "reconfigur" docs/CONVENTIONS.md docs/en/CONVENTIONS.md skills/plugin-dev/SKILL.md` → 1 · 1 · 1 (regla, espejo EN y checklist) · `ls docs/knowledge/gotchas/` → `GOT-005-consola-windows-cp1252.md` es el siguiente ID libre y `grep -c "GOT-005" docs/knowledge/README.md` → 1 · `grep -c "windows-console" docs/roadmap/README.md` → 1 · `grep -c "cp1252" docs/INSTALL.md docs/en/INSTALL.md` → 1 · 1 · `git status --porcelain CHANGELOG.md CHANGELOG.es.md` → vacío (no se tocan) · `python3 agent-kits/shared/ledger-lint.py docs/roadmap/2026-09-03-windows-console/tasks.md` → exit 0

**Criterios de aceptación**
- [x] La regla está en `docs/CONVENTIONS.md` regla 8 y en su espejo EN, encajada donde ya vive la disciplina de scripts (sin sección nueva)
- [x] `skills/plugin-dev/SKILL.md` la cita en una línea dentro de las reglas de pieza nueva
- [x] `GOT-005` existe con el formato exacto de las existentes y `estado: aceptada (validada: usuario, 2026-09-03)`, con su fila en `docs/knowledge/README.md`
- [x] `docs/roadmap/README.md` tiene la fila de la iniciativa
- [x] `docs/INSTALL.md` (+EN) explica qué esperar en la consola de Windows
- [x] Ningún `CHANGELOG*.md` modificado

### T-04 — El lado padre y el lado stdin del mismo bug

- **Descripción**: la revisión de dos lentes encontró que T-01 arregló **solo el lado que escribe**. Faltaban las dos mitades simétricas, y las dos estaban rotas en producción. **(1) `stdin`** — `guardrail-check.py` leía el payload del hook con `sys.stdin.read()`, que usa el codec del locale; bajo `cp1252` un payload con un emoji (o un `—`) lanzaba `UnicodeDecodeError` y el `except Exception` que existe para «un guardrail roto nunca bloquea» lo convertía en un **allow silencioso**: en el Windows español del bug original bastaba con que el contenido llevara un emoji para que los guardrails de alcance y de rama dejaran de denegar. El snippet pasa a cubrir los **tres** streams, replicado LITERAL en los 27 scripts; medido que `reconfigure` sobre `stdin` a nivel de módulo (antes de leer) funciona y que el `except` cubre los tres casos que no lo admiten: stream ya leído (`UnsupportedOperation`), `None` (`pythonw`) y sin el método (`capsys`). **(2) El lado PADRE** — desde T-01 los hijos escriben UTF-8 SIEMPRE, así que un padre que los capture con `text=True` sin `encoding=` revienta donde antes funcionaba; es una **regresión introducida por el propio arreglo**, y estaba en el camino caliente de `/dev-cycle` (`task-brief.py` → `ledger-lint.py`). **Barrido AST propio** (no la lista recibida): 14 sitios en scripts y 42 en las suites, todos con `encoding="utf-8", errors="replace"` — el mismo remedio que T-02 dio a `release.py::_run` y que se quedó sin generalizar. **(3) Blindaje durable** — el aviso del linter era un `grep` de subcadena (`CONSOLE_MARK.encode() in data`) con dos falsos negativos reproducidos; pasa a ser **estructural con `ast`** (la llamada a `reconfigure` debe estar en una sentencia de nivel de módulo y antes de cualquier otra que no sea docstring o import), y el **lado padre entra en el mismo par linter+test**. **(4) Un solo criterio** — `es_pieza` · `snippet_al_arrancar` · `subprocess_sin_encoding` viven en un bloque replicado LITERAL en `lint_plugin.py` y en `test_console_encoding.py`, con tres tests que lo vigilan (identidad byte a byte y mismo veredicto sobre el árbol real y sobre uno con infractores de cada clase); se borra la ruta hardcodeada `EXCLUIDOS` porque el segmento `fixtures` ya la cubre, y ahora cubre también cualquier otro `…/fixtures/`. La doc deja de afirmar identidad donde no la hay: el linter mira el **disco** (tiene que funcionar sobre un plugin desempaquetado, sin git) y el test mira **`git ls-files`**. **(5) Descubridor** — `git ls-files` cita las rutas no ASCII y no escapa los espacios, así que `sorted(salida.split())` perdía ficheros en silencio; se usa `-c core.quotepath=false` + `-z` partido por `\0`, el remedio que ya usaba `review-lens-select.py`. **(6) Roadmap** — la fila de la iniciativa estaba tras el párrafo `**Calibración:**` y una línea en blanco, o sea FUERA de la tabla; se mueve a su sitio cronológico y `tests/test_roadmap_index.py` vigila la POSICIÓN (lo que el `grep -c` declarado en T-03 no podía ver). **(7) Rendimiento** — `_ejecutar` se memoiza por `(rel, args, stdin, encoding)`. **(8) Doc** — `GOT-005` gana los dos síntomas nuevos y el aprendizaje central; `CONVENTIONS` regla 8 (+EN) y `plugin-dev` cubren las dos direcciones con frases cortas; `INSTALL` ES/EN dejan de contradecir a `GOT-005` sobre la consola legacy; el mensaje de `release.py` deja de afirmar que un exit ∉ {0,1} es siempre del entorno.
- **Estado**: completado
- **Tiempo humano**: est. 3,5h · real 3,5h (**estimado**: `usage-meter.py` no disponible en este entorno — sandbox cloud sin transcripción)
- **Tiempo IA (ejec.)**: est. 0,20h · real 0,20h (estimado, mismo motivo)
- **Supervisión**: est. 0,05h · real 0,05h (estimado, mismo motivo)
- **Archivos**: `agent-kits/qa/coverage-check.py`, `agent-kits/qa/qa-gate.py`, `agent-kits/shared/doctor.py`, `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/journal.py`, `agent-kits/shared/ledger-lint.py`, `agent-kits/shared/model-tier.py`, `agent-kits/shared/progress-report.py`, `agent-kits/shared/scope-check.py`, `agent-kits/shared/skill-index.py`, `agent-kits/shared/task-brief.py`, `agent-kits/shared/test_doctor.py`, `agent-kits/shared/test_guardrail_check.py`, `agent-kits/shared/test_journal.py`, `agent-kits/shared/test_model_tier.py`, `agent-kits/shared/test_progress_report.py`, `agent-kits/shared/test_scope_check.py`, `agent-kits/shared/test_skill_index.py`, `agent-kits/shared/test_task_brief.py`, `agent-kits/shared/usage-meter.py`, `docs/CONVENTIONS.md`, `docs/INSTALL.md`, `docs/en/CONVENTIONS.md`, `docs/en/INSTALL.md`, `docs/knowledge/gotchas/GOT-005-consola-windows-cp1252.md`, `docs/roadmap/README.md`, `evals/check.py`, `evals/run.py`, `evals/test_evals.py`, `scripts/export-skills.py`, `scripts/lint_plugin.py`, `scripts/release.py`, `skills/adversarial-review/scripts/review-lens-select.py`, `skills/adversarial-review/scripts/test_review_lens_select.py`, `skills/api-contract/scripts/openapi-lint.py`, `skills/api-contract/scripts/test_openapi_lint.py`, `skills/changelog-sync/scripts/changelog-sync.py`, `skills/changelog-sync/scripts/test_changelog_sync.py`, `skills/code-health/scripts/code-health.py`, `skills/code-health/scripts/test_code_health.py`, `skills/confluence-publish/scripts/confluence-scope.py`, `skills/dependency-upgrade/scripts/deps-inventory.py`, `skills/dependency-upgrade/scripts/test_deps_inventory.py`, `skills/jira-sync/scripts/jira-flow.py`, `skills/jira-sync/scripts/test_jira_flow.py`, `skills/jira-sync/scripts/worklog.py`, `skills/plugin-dev/SKILL.md`, `skills/roadmap-dashboard/scripts/build_dashboard.py`, `skills/unit-tests/scripts/coverage-gate.py`, `skills/unit-tests/scripts/test_coverage_gate.py`, `tests/test_confluence_scope.py`, `tests/test_console_encoding.py`, `tests/test_coverage_check.py`, `tests/test_export_skills.py`, `tests/test_hooks_shell.py`, `tests/test_ledger_lint.py`, `tests/test_lint_plugin.py`, `tests/test_qa_gate.py`, `tests/test_release.py`, `tests/test_roadmap_index.py`, `tests/test_worklog.py`, `docs/roadmap/2026-09-03-windows-console/tasks.md`
- **Verificación** (ejecutada 2026-09-03, salidas literales):
  - **CRITICAL 1, antes/después.** Payload `{"tool_name":"Write","tool_input":{"file_path":"docs/roadmap/2026-09-03-x/spec.md","content":"👍 ok"}}` a `guardrail-check.py pre-tool --project-dir .` con `PYTHONIOENCODING=cp1252`. ANTES (`git show c0ce71f:agent-kits/shared/guardrail-check.py`) → stdout **vacío**, **exit 0**, y en stderr:
    ```
    guardrail-check: error interno (UnicodeDecodeError('charmap', b'{"tool_name":"Write","tool_input":{"file_path":"docs/roadmap/2026-09-03-x/spec.md","content":"\xf0\x9f\x91\x8d ok"}}', 97, 98, 'character maps to <undefined>')) — se permite
    ```
    DESPUÉS → **exit 0** y **deniega**:
    ```
    {"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "«docs/roadmap/2026-09-03-x/spec.md» está en docs/roadmap/: el implementer solo toca tasks.md (ledger); el plan/spec/evaluación los cambia planner — anota la duda en tasks.md y sigue."}}
    ```
  - **CRITICAL 2, antes/después.** `task-brief.py <inic> T-01` sobre un ledger con un estado fuera del vocabulario, con el locale bajado por debajo de UTF-8 (`LC_ALL=C PYTHONCOERCECLOCALE=0 PYTHONUTF8=0`, que deja `locale.getpreferredencoding(False)` en `ANSI_X3.4-1968`: es lo que hace un Windows español con `cp1252`, y NO lo reproduce `PYTHONIOENCODING`, que solo toca los streams propios). ANTES (`git show c0ce71f:agent-kits/shared/task-brief.py`) → **exit 1** con traceback crudo:
    ```
      File "/usr/lib/python3.11/subprocess.py", line 1086, in _translate_newlines
        data = data.decode(encoding, errors)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    UnicodeDecodeError: 'ascii' codec can't decode byte 0xe2 in position 0: ordinal not in range(128)
    ```
    DESPUÉS → **exit 2** con su veredicto de siempre:
    ```
    ❌ ledger inválido — arregla tasks.md antes de despachar (ledger-lint exit 1):
    ❌ T-01: estado inválido «inventado» (vocabulario: borrador · cancelado · completado · en-progreso · en-revision)
    ```
  - **Barrido del lado padre.** Script AST propio sobre los `.py` versionados (reconoce `subprocess.X`, alias de import, `from subprocess import …` y el invocador indirecto por llevar `capture_output=`): antes **14 sitios en scripts y 42 en suites**; después `-- scripts: 0 · tests: 0 · total: 0`.
  - **Suite completa.** `python3 -m pytest -q` → `797 passed in 38.85s` · `PYTHONIOENCODING=cp1252 python3 -m pytest -q` → `797 passed in 38.79s` (701 antes de T-04). [T-05 la lleva a **814** — ver su verificación.]
  - **Linter bajo cp1252.** `PYTHONIOENCODING=cp1252 python3 scripts/lint_plugin.py` → **exit 0**, `lint_plugin: 9 agentes · 0 errores · 3 avisos` (los mismos 3 de siempre: `retro`, `roadmap-status`, `setup`; ningún aviso nuevo de consola ni de subproceso).
  - **Falsos negativos del linter, antes/después** (con `--root` sobre un plugin de prueba). (a) snippet dentro de `main()` con un `print("⚠️ …")` de módulo antes: ANTES `lint_plugin: 1 agentes · 0 errores · 0 avisos` y el script **reventaba** bajo `cp1252` (`UnicodeEncodeError: 'charmap' codec can't encode characters in position 0-1`, exit 1); DESPUÉS, aviso: «⚠️  `scripts/malo.py`: imprime caracteres no ASCII y no reconfigura los streams AL ARRANCAR …» y `lint_plugin: 1 agentes · 0 errores · 1 avisos`. (b) marca solo en un docstring: idéntico antes/después.
  - **Tests del linter.** `python3 tests/test_lint_plugin.py` → `test_lint_plugin: 29/29 OK` (26 antes + 3: snippet en `main()` → aviso · marca solo en docstring → aviso · subproceso en modo texto sin `encoding=` → aviso, y sin aviso al añadirlo o al usar solo `capture_output`).
  - **Descubridor con rutas citadas.** Repo de prueba con `scripts/año.py`, `scripts/mi script.py` y `scripts/normal.py`. ANTES, `sorted(r.stdout.split())` → `['"scripts/a\\303\\261o.py"', 'script.py', 'scripts/mi', 'scripts/normal.py']` (ninguna de las dos primeras existe en disco: se caían en silencio). DESPUÉS, `git -c core.quotepath=false ls-files -z` partido por `\0` → `['scripts/año.py', 'scripts/mi script.py', 'scripts/normal.py']`.
  - **`test_console_encoding.py`.** `229 passed` [T-05 lo lleva a **246**] — desglose contra el fichero: **3** tests × 27 scripts = 81 (snippet presente · snippet que protege el arranque · snippet con su forma literal), **2** × 27 × 2 codificaciones = 108 (arranca sin reventar · la salida sigue siendo UTF-8), **1** × 2 codificaciones = 2 (el payload con emoji por stdin no apaga el guardrail), **1** × 28 piezas versionadas = 28 (ninguna captura un subproceso sin `encoding=`) y **10** sin parametrizar: 81 + 108 + 2 + 28 + 10 = **229**.
  - **Memoización (lente D), medido.** [**Cifras corregidas en T-05**: las que se pegaron aquí —«114 subprocesos, 58 claves, 56 repeticiones» y «el mismo fichero de 228 tests»— no cuadran con el fichero entregado. Remedido sobre él, estable en 3 pasadas: **117 llamadas · 58 claves · 59 repeticiones**, y el fichero tiene **229** tests. Lo demás se mantiene.] Comprobado antes de cachear que repetir no aporta señal: las claves devuelven lo mismo byte a byte salvo `usage-meter.py close` (una por codificación), que solo cambia en el campo `"fin"` — una marca de tiempo que ningún assert mira. A/B: `8,47 / 8,58 / 8,34 s` sin memoizar → `4,93 / 5,08 / 4,92 s` con memoización. Suite completa: `38,36 s` (701 tests, antes de T-04) → `38,85 s` (797 tests).
  - **Coste del linter, medido y aceptado.** La comprobación estructural cuesta lo que cuesta parsear: `python3 scripts/lint_plugin.py` pasa de `0,054 / 0,053 / 0,069 s` (antes de T-04) a `0,339 / 0,325 / 0,319 / 0,334 / 0,312 s`. Perfilado: el `ast.parse` de las 28 piezas son `0,227 s` de ese total; el `os.walk` `0,002 s`. Se acepta —es un linter que corre una vez en CI y en `release.py`, y la alternativa es el `grep` de subcadena que dejaba pasar los dos falsos negativos—. **Se probó cachear los árboles y salió PEOR**, así que no se quedó: con caché `0,421 / 0,417 / 0,450 / 0,416 / 0,423 s` en el linter y `5,50 / 5,59 / 5,23 s` en la suite de consola, frente a `5,21 / 5,06 / 5,20 s` sin ella (mantener 28 ASTs vivos sale más caro que volver a parsear).
  - **Roadmap.** `python3 -m pytest -q tests/test_roadmap_index.py` → `30 passed`. Devolviendo la fila al final del fichero, el test se pone rojo con `test_ninguna_fila_se_queda_fuera_de_la_tabla` y `test_cada_iniciativa_con_ledger_tiene_su_fila_dentro_de_la_tabla[2026-09-03-windows-console]`. El test cazó además un hueco preexistente: `2026-08-20-knowledge-split` estaba cerrada y no aparecía en el índice; se añadió su fila.
  - **Puertas del repo.** `python3 agent-kits/shared/ledger-lint.py docs/roadmap/2026-09-03-windows-console/tasks.md` → `ledger-lint: 0 incoherencias · 0 avisos (tasks.md)` **exit 0** · `python3 agent-kits/shared/scope-check.py docs/roadmap/2026-09-03-windows-console --base 51da438` → **exit 0** · `python3 evals/check.py` → `evals/check: 38 ficheros · 133 casos (78 positivos, 55 negativos) · 38 piezas del repo · 0 errores` **exit 0**.
  - **Paquete portable.** `python3 scripts/export-skills.py --out <tmp>` → `hash: a5c14e24001fe36cf1973b9430f05060cf5dd5715f720d6e867e2040f87b02d6` **exit 0**; `--check` sobre esa salida → `export-skills --check: 104 ficheros · 0 problema(s)` **exit 0**.
  - **No medido, dicho:** no hay Windows real en este entorno. Todo se reproduce en Linux con `PYTHONIOENCODING` (streams propios) y con `LC_ALL=C PYTHONCOERCECLOCALE=0 PYTHONUTF8=0` (`locale.getpreferredencoding` → ASCII, que es el equivalente al `cp1252` de un Windows español para el lado padre). El coste (horas y tokens) es **estimado**: `usage-meter.py` no puede leer la transcripción en este sandbox.

**Criterios de aceptación**
- [x] El snippet cubre `sys.stdin` en los 27 scripts, LITERAL e idéntico, y el `except` cubre stream ya leído · `None` · sin el método (los tres, medidos)
- [x] El payload con emoji bajo `cp1252` DENIEGA (antes: allow silencioso con exit 0 y stdout vacío), con test de regresión que se pone rojo al quitar `stdin` del snippet
- [x] `task-brief.py` vuelve a dar su exit 2 con «❌ ledger inválido — arregla tasks.md antes de despachar» con el locale por debajo de UTF-8, con test de regresión
- [x] Barrido AST propio: **0** llamadas a `subprocess` en modo texto sin `encoding=` en todo el repo (14 scripts + 42 suites arregladas)
- [x] El linter caza los dos falsos negativos medidos (snippet en `main()` · marca solo en docstring) con comprobación estructural por `ast`, y avisa del lado padre
- [x] Linter y suite comparten el MISMO TEXTO del criterio, con tests que comparan el bloque byte a byte y el veredicto sobre árbol limpio y sobre árbol con infractores
- [x] `EXCLUIDOS` borrado: `fixtures` como segmento cubre el caso y además cualquier otro `…/fixtures/`
- [x] El descubridor no pierde rutas con espacios ni no ASCII (`-c core.quotepath=false` + `-z`), con test que lo prueba en un repo de verdad
- [x] La fila del roadmap está DENTRO de la tabla, en su sitio cronológico, con test de regresión que mira la posición y no la cadena
- [x] `INSTALL` ES/EN dicen lo mismo que `GOT-005` sobre la consola legacy (la versión medida)
- [x] `GOT-005` recoge el lado padre y el lado stdin como el aprendizaje central de la ronda
- [x] La viñeta de `CONVENTIONS` regla 8 (+EN) no tiene frases de 58 palabras (máx. 36 ES / 38 EN) y conserva el porqué de replicar el snippet
- [x] El mensaje de `release.py` sobre el exit ∉ {0,1} es cierto (sin cambiar clasificación ni exit codes)
- [x] `_ejecutar` memoizado, con el antes/después medido y el determinismo de las repeticiones comprobado
- [x] `scope-check.py … --base 51da438` sigue en **exit 0**: todos los ficheros tocados están en un campo `Archivos`

### T-05 — Cierre de los gaps del intento 2 de la revisión de dos lentes

- **Descripción**: la segunda pasada de las dos lentes encontró que T-04 dejó el criterio a medias y tres tests que no medían lo que decían. **(1) El criterio solo miraba al que ESCRIBE.** El aviso del linter y el descubridor de la suite filtraban por «el fuente tiene bytes no ASCII», que es el criterio del lado que imprime; el lado que LEE no depende del fuente sino del **payload**. De las **28** piezas versionadas, 27 llevaban el snippet y la que faltaba era justo un lector: `agent-kits/nemesis/tools/pick_asset.py`, ASCII pura, con un `json.load(sys.stdin)` sobre el JSON de una release de GitHub — cuyo `body` trae las notas con emojis (🐛 = `F0 9F 90 9B`, byte `0x90`; 👍 lleva `0x8D`; ninguno existe en cp1252). Y el síntoma vuelve a ser **el crash disfrazado de veredicto** del bug original: `install-tools.sh` manda ese stderr al log, ve la URL vacía y anuncia `[!!] <tool>: no release asset for <os>/<arch>`. El criterio compartido pasa a ser **`exige_snippet` = no-ASCII en el fuente O `lee_stdin`**, con `ast` (una mención a `sys.stdin` en un comentario o dentro de una cadena no cuenta, y la sentencia del propio snippet queda fuera para que el criterio no sea circular — **corregido en T-06 (2026-09-03)**: excluir la sentencia entera excluía de más); el aviso del linter nombra el motivo real, y el snippet entra en la 28.ª pieza. **(2) La regla escrita dejaba de ser cierta.** `CONVENTIONS` regla 8 (+EN), `plugin-dev` regla 6 y `GOT-005` decían «**todo** script del plugin»; el guardarraíl vigilaba menos. **Decidido y escrito: la regla verdadera es «el que escribe símbolos o el que lee `stdin`»**, no «todo script» — el aviso también le sale a un plugin CONSUMIDOR, que puede tener `.py` que ni imprimen ni leen, y avisarle sería ruido sin síntoma. Las tres frases se corrigen para decir exactamente lo que se vigila. **(3) El test de coincidencia se ponía rojo por un fichero que ni estaba en el commit.** `test_linter_y_suite_dan_el_mismo_veredicto_sobre_el_arbol_actual` comparaba el veredicto del linter (que mira el DISCO) con el de la suite (que mira `git ls-files`): cualquier `.py` sin `git add` rompía la igualdad, en local y solo en local (CI hace checkout limpio), con un mensaje que mandaba a buscar una divergencia de criterio inexistente. Ahora se compara **solo sobre lo versionado**, lo no versionado se nombra aparte en el mensaje, y un test con repo git de verdad prueba las dos mitades: el borrador sin versionar ya no pone rojo, y una divergencia REAL sí. **(4) Evidencia tautológica.** `test_reconfigure_sobre_stdin_tolera_stream_leido_none_o_sin_metodo` era la evidencia declarada de «el `except` cubre los tres casos, medidos» y **no tenía una sola aserción**: `try: stream.reconfigure(...) except: pass` sobre tres dobles, sin tocar ningún script. Se sustituye por dos tests parametrizados que arrancan un script REAL (`ledger-lint.py`) con `sys.stdin` en cada estado imposible —lectura parcial, `None`, objeto sin el método— y exigen exit 0 sin traceback; y por su **mutación**, que copia el script a `tmp_path`, le quita el `except` y exige que los tres caigan. **(5) El skip que tapaba justo el caso a detectar.** `test_la_salida_sigue_siendo_utf8_no_interrogantes` decía cazar la degradación a `?` pero se **saltaba** el caso «la salida no trae no-ASCII», que es esa degradación. Medido: las 54 combinaciones (27 scripts × 2 codificaciones) emiten no-ASCII, así que el skip nunca se disparaba y solo podía tapar. Pasa a FALLO, con la única exención NOMBRADA y comprobada por su propio test (`pick_asset.py`: su veredicto es una URL ASCII, y entra en la lista por leer `stdin`, no por escribir símbolos). **(6) La misma clase de bug en los `.sh`.** `hooks/` y `statusline/` extraen el payload y componen su JSON con `python3 -c` en línea, sin reconfigurar: bajo cp1252 revientan con `UnicodeDecodeError` en cuanto el texto trae un byte que ese codec no define —`❌` (`0x9D`), `⚠️` (selector de variación, `0x8F`), `👍` (`0x8D`)— y el `2>/dev/null || true` con el que el hook degrada se lo traga. Son **7 sitios**, no 2; el octavo (`session-journal.sh:54`) lee un FICHERO con su `encoding=` e imprime `0`/`1`, y queda fuera con un test que lo dice — **corregido en T-06 (2026-09-03)**: la regla pasa a ser uniforme y ese sitio también la lleva. Se resuelve con `PYTHONIOENCODING=utf-8:replace` delante del comando (no hay fichero donde pegar el snippet) y lo vigila la **suite**, no el linter: un parser de shell en `lint_plugin.py` le haría opinar sobre los hooks de cualquier consumidor. **(7) Cifras del ledger.** Se remiden y se corrigen las que este cambio invalida, incluidas las de T-04.
- **Estado**: completado
- **Tiempo humano**: est. 2,6h · real 2,6h (**estimado**: `usage-meter.py` no disponible en este entorno — sandbox cloud sin transcripción)
- **Tiempo IA (ejec.)**: est. 0,15h · real 0,15h (estimado, mismo motivo)
- **Supervisión**: est. 0,04h · real 0,04h (estimado, mismo motivo)
- **Archivos**: `agent-kits/nemesis/tools/pick_asset.py`, `scripts/lint_plugin.py`, `tests/test_console_encoding.py`, `tests/test_lint_plugin.py`, `hooks/progress-line.sh`, `hooks/subagent-progress.sh`, `hooks/session-context.sh`, `hooks/session-journal.sh`, `statusline/roadmap-statusline.sh`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `skills/plugin-dev/SKILL.md`, `docs/knowledge/gotchas/GOT-005-consola-windows-cp1252.md`, `docs/roadmap/README.md`, `docs/roadmap/2026-09-03-windows-console/tasks.md`
- **Verificación** (ejecutada 2026-09-03, salidas literales):
  - **IMPORTANT 1, antes/después.** `PYTHONIOENCODING=cp1252 python3 agent-kits/nemesis/tools/pick_asset.py linux amd64 <<< '{"tag_name":"v1 👁", "assets":[{"name":"tool_linux_amd64.tar.gz","browser_download_url":"https://x/y"}]}'`. ANTES → **exit 1** y en stderr:
    ```
    bad json: 'charmap' codec can't decode byte 0x81 in position 19: character maps to <undefined>
    ```
    DESPUÉS → **exit 0** y su veredicto:
    ```
    https://x/y
    ```
    (la posición es **19**, no 20: los 16 caracteres de `{"tag_name":"v1 ` más los tres primeros bytes de 👁 = `F0 9F 91 81`. Es la única corrección a la reproducción recibida.)
  - **La 28.ª pieza, contada.** `git -c core.quotepath=false ls-files -z '*.py' | tr '\0' '\n' | grep -v '/test_\|^test_' | grep -v 'fixtures/' | wc -l` → **28**; con el criterio de T-04 el descubridor daba 27 y el linter 0 avisos sobre `pick_asset.py`. Con el de T-05, `descubrir()` da **28** y `test_el_descubridor_encuentra_los_scripts_conocidos` exige que esté.
  - **IMPORTANT 2, antes/después.** `echo 'print("⚠️ borrador")' > scripts/borrador_local.py` (sin `git add`) + `python3 -m pytest -q tests/test_console_encoding.py`. ANTES:
    ```
    E       AssertionError: linter: ['scripts/borrador_local.py'] · suite: []
    1 failed, 228 passed in 5.02s
    ```
    DESPUÉS, con el mismo fichero sin versionar en el árbol: **`246 passed`**, y el nuevo `test_el_veredicto_compartido_ignora_lo_no_versionado_pero_no_una_divergencia` monta un repo git de verdad para probar que el borrador NO rompe la igualdad y que el mismo fichero, una vez **versionado**, sí la rompe.
  - **IMPORTANT 3, la mutación.** Sobre `ledger-lint.py` con `sys.stdin` en los tres estados imposibles (`PYTHONIOENCODING=cp1252`, datos reales en el pipe). REAL → `ledger-lint: 0 incoherencias · 0 avisos (tasks.md)`, **exit 0** en los tres. Copia MUTADA en `/tmp` con el snippet sin su `except` → **exit 1** en los tres, con:
    ```
    io.UnsupportedOperation: It is not possible to set the encoding or newline of stream after the first read
    AttributeError: 'NoneType' object has no attribute 'reconfigure'
    AttributeError: 'SinReconfigure' object has no attribute 'reconfigure'
    ```
    Medido de paso un matiz que el test recoge: `reconfigure` tras un `read()` COMPLETO no lanza (el wrapper se resetea al llegar a EOF); el caso real es la lectura **parcial** (`readline()`), y así lo reproduce el envoltorio.
  - **MINOR 7, la medición que justifica el fallo.** Las **54** combinaciones de `SCRIPTS_CON_SIMBOLOS` (27 scripts × `cp1252`/`ascii`) emiten no-ASCII: `SIN no-ASCII en la salida: 0`. O sea que el `pytest.skip` no se disparaba nunca y solo podía tapar la degradación. La única exención es `pick_asset.py`, y no se salta: `test_los_exentos_de_simbolos_lo_estan_por_medicion` **ejecuta** su modo y exige que efectivamente no imprima símbolos, así que se pondrá rojo el día que empiece a hacerlo.
  - **MINOR 8, antes/después.** `hooks/progress-line.sh` sobre un ledger cuya fase se llama «consola ❌ rota», con `PYTHONIOENCODING=cp1252` y el debounce limpio. ANTES (`git show b21de3d:hooks/progress-line.sh`) → **exit 0** y stdout **vacío**: la línea desaparece en silencio. DESPUÉS → **exit 0** y:
    ```
    {"systemMessage": "📋 x · T-04/4 completadas (100%) · fase 1/1 «consola ❌ rota» · IA real 12m"}
    ```
    **Rebatido a medias lo recibido:** el «llega mojibake al `systemMessage`» **no** se reproduce. cp1252 hace ida y vuelta byte a byte con los códigos que sí define, así que `📋` (`F0 9F 93 8B`) y `·` (`C2 B7`) salen intactos; lo que falla es el **crash silencioso** con los bytes indefinidos (`0x81`, `0x8D`, `0x8F`, `0x90`, `0x9D`), y ahí sí se pierde la línea entera. Medido uno a uno: `📋 ok` → JSON correcto; `❌ …` → `can't decode byte 0x9d`; `⚠️  …` → `0x8f`; `👍 ok` → `0x8d`.
  - **El guardarraíl del shell puede fallar.** Quitando el prefijo a `hooks/progress-line.sh:87`, `python3 -m pytest -q tests/test_console_encoding.py -k python_en_linea` → `1 failed, 1 passed` con `AssertionError: python3 -c que lee stdin o imprime símbolos SIN PYTHONIOENCODING=utf-8:replace delante: hooks/progress-line.sh:87`.
  - **Suite completa.** `python3 -m pytest -q` → `814 passed in 37.81s` · `PYTHONIOENCODING=cp1252 python3 -m pytest -q` → `814 passed in 37.60s` (797 antes de T-05).
  - **Linter bajo cp1252.** `PYTHONIOENCODING=cp1252 python3 scripts/lint_plugin.py` → **exit 0**, `lint_plugin: 9 agentes · 0 errores · 3 avisos` (los mismos 3 de siempre: `retro`, `roadmap-status`, `setup`; ningún aviso nuevo). **Coste sin cambio medible**: `0,317 / 0,332 / 0,335 / 0,335 / 0,339 s` frente a los `0,312–0,339 s` de T-04 — el `or` de `exige_snippet` corta a la izquierda, así que solo se parsea de más el único fichero ASCII de las 28.
  - **Tests del linter.** `python3 tests/test_lint_plugin.py` → `test_lint_plugin: 32/32 OK` (29 antes + 3: lector de stdin ASCII puro → aviso que nombra `lee de sys.stdin` y no menciona símbolos, y sin aviso al añadirle el snippet · `sys.stdin` citado en comentario o cadena → sin aviso · los dos motivos a la vez → el aviso los nombra los dos).
  - **`test_console_encoding.py`.** `246 passed` — desglose comprobado con `pytest --collect-only` y no a ojo: **3** × 28 piezas = 84 (snippet presente · protege el arranque · forma literal), **1** × 28 × 2 codificaciones = 56 (arranca sin reventar), **1** × 27 × 2 = 54 (la salida sigue siendo UTF-8 — 27, no 28: `pick_asset.py` está exento y su exención se mide aparte), **1** × 28 = 28 (ninguna pieza captura un subproceso sin `encoding=`), **3** × 2 codificaciones = 6 (guardrail con emoji · JSON de release con emoji · el exento, medido), **2** × 3 estados de `stdin` = 6 (el `except` real y su mutante) y **12** sin parametrizar: 84 + 56 + 54 + 28 + 6 + 6 + 12 = **246**. Eran 229 antes de T-05.
  - **Memoización, remedida.** Con `_ejecutar` instrumentado, **estable en 3 pasadas**: `123 llamadas · 60 claves · 63 repeticiones`. A/B sobre el fichero de **246** tests: `9,36 / 9,34 / 9,44 s` sin memoizar → `5,55 / 5,74 / 5,94 s` con memoización.
  - **Puertas del repo.** `python3 agent-kits/shared/ledger-lint.py docs/roadmap/2026-09-03-windows-console/tasks.md` → `ledger-lint: 0 incoherencias · 0 avisos (tasks.md)` **exit 0** · `python3 agent-kits/shared/scope-check.py docs/roadmap/2026-09-03-windows-console --base 51da438` → **exit 0** · `python3 evals/check.py` → `evals/check: 38 ficheros · 133 casos (78 positivos, 55 negativos) · 38 piezas del repo · 0 errores` **exit 0**.
  - **Paquete portable.** `python3 scripts/export-skills.py --out <tmp>` → `hash: a5c14e24001fe36cf1973b9430f05060cf5dd5715f720d6e867e2040f87b02d6` **exit 0** — el **mismo** hash que en T-04, porque nada de lo que toca T-05 viaja en el paquete (`lint_plugin.py`, `pick_asset.py`, los hooks y la statusline se quedan fuera); `--check` sobre esa salida → `export-skills --check: 104 ficheros · 0 problema(s)` **exit 0**.
  - **No medido, dicho:** sigue sin haber Windows real en este entorno (todo se reproduce con `PYTHONIOENCODING` y con el locale por debajo de UTF-8), y el coste en horas y tokens sigue siendo **estimado** por la misma razón que en T-04.

**Criterios de aceptación**
- [x] El criterio de linter y suite es «no-ASCII en el fuente **O** lee de `sys.stdin`», detectado con `ast` (no `grep`), replicado LITERAL en los dos y comparado byte a byte
- [x] `pick_asset.py` lleva el snippet y su caso de release con emoji está en la suite, con el antes/después pegado
- [x] La regla escrita en `CONVENTIONS` (+EN), `plugin-dev` y `GOT-005` es **exactamente** la que vigila el guardarraíl — decidida y justificada, no ampliada de boquilla
- [x] El aviso del linter nombra el motivo real (símbolos, `stdin`, o los dos), con test de los tres mensajes
- [x] La comparación de veredictos solo mira lo versionado, y hay test que prueba que un `.py` sin versionar ya no la rompe y que una divergencia real sí
- [x] El test del `except` mide sobre un script REAL en los tres estados y se pone rojo con la mutación (demostrada sobre una copia en `tmp_path`, nunca sobre el repo)
- [x] La salida degradada a ASCII FALLA en vez de saltarse; la única exención está nombrada y la comprueba su propio test ejecutando el modo
- [x] Los `python3 -c` de `hooks/` y `statusline/` que leen `stdin` o imprimen símbolos llevan `PYTHONIOENCODING=utf-8:replace`, con test que se pone rojo si se quita
- [x] El byte de `GOT-005` es el medido (`0xe2`), y todas las cifras del ledger que este cambio invalida están remedidas (las de T-04 incluidas)
- [x] `scope-check.py … --base 51da438` sigue en **exit 0**


### T-06 — Cierre de los gaps del intento 3 (los dos agujeros del criterio nuevo)

- **Descripción**: la tercera pasada de la Lente B midió que el criterio que T-05 estrenó tenía **dos agujeros por los que se colaba justo el caso que existe para cazar**. **(1) `lee_stdin` se apagaba sola.** La exclusión del `sys.stdin` que el propio snippet nombra estaba escrita como «excluye la sentencia que contiene el `reconfigure`», y `ast.walk` recorre también los **ancestros**: un `FunctionDef`, un `If` o un `Try` es un `ast.stmt`, así que si el snippet vivía dentro de `main()`, **el cuerpo entero de `main()` quedaba fuera de la detección**. Medido: una pieza ASCII pura que hace `json.load(sys.stdin)` con el snippet mal colocado dentro de `main()` daba `lee_stdin` **False**, `exige_snippet` **False**, `lint_plugin --root .` **ningún aviso** y la suite **verde**, mientras la ejecución real reventaba (`UnicodeDecodeError: 'charmap' … byte 0x90`, exit 1). Es decir: el anti-patrón que T-04 documentó como el error típico —snippet dentro de `main()`— *apagaba* al guardarraíl que debía cazarlo. Ahora se excluye **solo el `iter` del `for` del snippet**, que es exactamente donde el snippet nombra `sys.stdin`, y nada más; y `lee_stdin` reconoce además `input()` y `fileinput.input()`, que leen del mismo stdin con el mismo codec. **(2) El guardarraíl de los `.sh` solo reconocía una forma de citar.** La expresión regular era `python3 -c '<programa>'` con comillas simples, así que **cuatro formas triviales pasaban verdes y sin señal**: comillas dobles, heredoc (`python3 <<'EOF'`), `python` sin el `3`, e invocación por variable (`"$PY" -c …`, que es como `install-tools.sh` elige intérprete). Un hook nuevo escrito de cualquiera de esas formas simplemente no se vigilaba. El criterio deja de parsear el programa —decidir «lee stdin o imprime símbolos» exige leer el programa, y el programa es justo lo que se escapa por la forma de citar— y pasa a ser **uniforme: todo python en línea de un `.sh` versionado lleva `PYTHONIOENCODING=utf-8:replace` delante**, se detecte la forma que se detecte. Con eso desaparece la exención de `session-journal.sh:54` (la variable ahí no arregla nada, pero cuesta cero y no hay que decidir nada por cada `python3 -c` nuevo).
- **Estado**: completado
- **Tiempo humano**: est. 1,2h · real 1,2h (estimado)
- **Tiempo IA (ejec.)**: est. 0,07h · real 0,07h (estimado)
- **Supervisión**: est. 0,02h · real 0,02h (estimado)
- **Archivos**: `scripts/lint_plugin.py`, `tests/test_console_encoding.py`, `hooks/session-journal.sh`, `docs/roadmap/2026-09-03-windows-console/tasks.md`
- **Verificación** (ejecutada 2026-09-03): el caso del agujero (1), sobre una pieza con el snippet dentro de `main()` y `json.load(sys.stdin)` en la misma función → `lee_stdin` **True** (antes False), y la no-circularidad se conserva: un fichero con SOLO el snippet sigue dando **False** · los 10 casos de `CASOS_LEE_STDIN` (snippet solo · snippet mal colocado + lectura · snippet bien + lectura · `import sys as s` · `from sys import stdin` · `input()` · `fileinput.input()` · mención en docstring · mención en comentario · no lo usa) pasan con el veredicto esperado · las 9 formas de invocación de `FORMAS_DE_PYTHON_EN_LINEA`: las 6 de python en línea se detectan (incluidas comillas dobles, heredoc, `python` sin `3` y `"$PY"`) y las 3 que no lo son (`command -v python3`, `for c in python3 python`, `python3 "$SHARED/progress-report.py"`) no · barrido de los `.sh` versionados → **8 sitios, los 8 con la variable** · bloque compartido `--8<--` **byte a byte idéntico** entre `scripts/lint_plugin.py` y `tests/test_console_encoding.py` (9.550 caracteres) · `bash -n hooks/session-journal.sh` → sin error · `python3 -m pytest -q tests/test_console_encoding.py` → **265 passed** · `python3 -m pytest -q` → **833 passed in 35,49s** y **833 passed** también con `PYTHONIOENCODING=cp1252` · `PYTHONIOENCODING=cp1252 python3 scripts/lint_plugin.py` → **exit 0**, `lint_plugin: 9 agentes · 0 errores · 3 avisos` · `python3 tests/test_lint_plugin.py` → `test_lint_plugin: 32/32 OK` · `python3 evals/check.py` → `evals/check: 38 ficheros · 133 casos (78 positivos, 55 negativos) · 38 piezas del repo · 0 errores` · `python3 agent-kits/shared/scope-check.py docs/roadmap/2026-09-03-windows-console --base 51da438` → **exit 0**, `❌ fuera de alcance (0): —`

**Criterios de aceptación**
- [x] `lee_stdin` excluye SOLO el `iter` del `for` del snippet, no la sentencia ancestra, y el caso «snippet dentro de `main()` + lee stdin» se detecta (con test que se pone rojo si se vuelve a excluir de más)
- [x] La no-circularidad se conserva: un fichero con solo el snippet sigue sin «leer» stdin
- [x] `input()` y `fileinput.input()` cuentan como lectura de stdin
- [x] El guardarraíl de los `.sh` detecta las cuatro formas que se le escapaban, y su regla es uniforme: todo python en línea lleva la variable
- [x] Los 8 sitios de python en línea del repo la llevan, `session-journal.sh` incluido; `bash -n` limpio
- [x] El bloque compartido sigue siendo byte a byte idéntico en las dos copias
---

## Notas de cierre

### Causa raíz: el crash fue por el PIPE, no por la consola

`release.py` lanza los checks con `subprocess.run(..., capture_output=True)`. Con stdout **redirigido a
un pipe**, Python no usa la API de consola de Windows: cae al `locale.getpreferredencoding()`, que en
un Windows español es **cp1252** — de ahí `File "…\Lib\encodings\cp1252.py"` en el traceback del usuario.
Encaja con lo que él vio: `release.py` imprimió sus propias líneas con `⚠️` sin problema (esas SÍ iban a
la consola real, que en Python ≥ 3.6 usa `WriteConsoleW`), y el que reventó fue el hijo. Por eso el
arreglo tiene que estar **en cada script**, no en el terminal ni en una variable de entorno del usuario:
cualquiera de los 27 puede ser el hijo de un pipe (los agentes los invocan así, y las skills también).

### Decisión: SIN modo ASCII (`CUSTOM_AGENTS_ASCII` / `--ascii`) — medido, no opinado

La premisa del modo ASCII era «con `errors="replace"` los emojis saldrán como `?` en una consola cp1252».
**Se midió y no se cumple**: `reconfigure(encoding="utf-8", …)` cambia el codec del stream en caliente y
**gana a `PYTHONIOENCODING`**, así que la salida sale en UTF-8 íntegro y `errors="replace"` no llega a
dispararse nunca (queda de red de seguridad para un stream que aceptase `errors` pero no `encoding`).

| Escenario | Antes | Después (medido) |
|---|---|---|
| `PYTHONIOENCODING=cp1252 python3 scripts/lint_plugin.py` | `UnicodeEncodeError`, exit 1 | exit 0, `⚠️`/`❌` intactos (`sys.stdout.encoding` → `utf-8`) |
| `PYTHONIOENCODING=ascii …` | `UnicodeEncodeError`, exit 1 | exit 0, símbolos intactos |
| Bytes en el pipe (`… \| od -c`) | — | `342 234 205` = `E2 9C 85` = `✅` en UTF-8 (no `?` = `077`) |
| Consola real de PowerShell (Python ≥ 3.6) | ya funcionaba (`WriteConsoleW`) | igual — el `reconfigure` es un no-op ahí |

Con eso, un modo ASCII solo cubriría la consola Windows **legacy** (`PYTHONLEGACYWINDOWSSTDIO=1`, o
`cmd.exe` con `chcp` antiguo), donde UTF-8 se ve como mojibake (`âœ…`) en vez de como `?`. A cambio
costaría replicar un mapa de sustitución + su bandera + sus tests en 7 scripts (`lint_plugin`, `doctor`,
`evals/check`, `ledger-lint`, `qa-gate`, `changelog-sync`, `scope-check`), y cambiaría en silencio la
salida que hoy afirman tests y `grep` del repo (`test_qa_gate`, `test_ledger_lint`, `doctor`). **No sale a
cuenta**: se documenta el escenario legacy en `GOT-005` y, si algún día aparece de verdad, la forma
correcta es **una línea más en el mismo snippet** (que ya viaja a los 27 sitios), no una bandera por script.

### Consecuencia deliberada: `changelog-sync --check` queda en rojo

El alcance excluía `CHANGELOG*.md` por indicación explícita del usuario. Como este ledger se cierra
`completado`, `changelog-sync --check` lo detecta y sale **1** con
`· windows-console (2026-09-03) — Fixed, 5 tarea(s) → falta en CHANGELOG.md, CHANGELOG.es.md`
(el número lo pone el propio comando y sube con cada tarea: eran 3 cuando se escribió esta nota, 4 tras
T-04 y 5 tras T-05 — remedido cada vez, no arrastrado).
Es el veredicto correcto de la herramienta —deuda de notas real, no un fallo— y con T-02 el release lo
presenta como `PENDIENTE` (aviso que no bloquea), no como `ERROR al ejecutar`. Las notas se generan con
la skill `changelog-sync` cuando el usuario quiera, y entonces vuelve a 0. La comprobación de que el
emoji del veredicto positivo imprime bien bajo `cp1252` se hizo con `--only roles-and-jira-flow`.

### La otra mitad de la causa raíz (T-04): el que LEE también revienta

La nota de arriba se quedó a medias. `release.py` lanza los checks con un pipe y **el hijo** revienta al
escribir: eso es T-01. Pero la tubería tiene dos extremos, y el otro estaba igual de roto en los dos
sentidos. **Quien lee un payload por `stdin`** usa el codec del locale igual que quien imprime: por eso
el guardrail del implementer se apagaba en silencio con cualquier contenido que llevara un emoji, y por
eso el snippet pasa a cubrir los tres streams. **Y quien captura a un hijo** lo decodifica con el codec
del locale salvo que se le diga otra cosa: como T-01 hizo que los hijos escriban UTF-8 SIEMPRE, arreglar
el lado que escribe **movió** el fallo al padre en vez de eliminarlo (`task-brief.py` → `ledger-lint.py`,
en el despacho de tarea de `/dev-cycle`). El aprendizaje, ya en `GOT-005`: **arreglar solo el lado que
escribe deja el bug intacto en el lado que lee, y encima lo mueve al padre.**

### La tercera mitad (T-05): el criterio no se puede sacar del fuente

T-04 arregló el lado que lee y el lado padre, pero dejó el **criterio** con la forma del lado que
escribe: «este fichero tiene bytes no ASCII». Eso funciona para quien imprime —sus símbolos están en
el código— y **no funciona para quien lee**, porque su riesgo lo trae el payload, no el fuente. El
resultado fue una pieza de 28 sin snippet, invisible para el linter y para la suite, y encima
precisamente un lector de `stdin`. El aprendizaje, ya en `GOT-005`: **cuando una regla tiene dos
lados, el criterio que decide a quién se le aplica también tiene dos lados**; si se hereda el del
primero, el segundo se queda sin vigilancia y la doc empieza a prometer lo que nadie comprueba.

Y su corolario, que es lo que pasó con las tres frases de `CONVENTIONS`/`plugin-dev`/`GOT-005`:
**ampliar la frase sin ampliar el guardarraíl es peor que no ampliarla**, porque el siguiente lector
se fía. La regla escrita tiene que ser la regla vigilada, ni más ni menos — y si se quiere más, se
amplía el criterio primero.

### Deuda anotada (no en esta iniciativa)

- ~~Los `.sh` de `hooks/` y `statusline/` …~~ **Cerrada en T-05, y la premisa era falsa.** Bash no
  codifica, cierto, pero esos `.sh` no imprimen su JSON con `printf`: lo componen con un `python3 -c`
  en línea, y ese sí codifica. Bajo cp1252 revienta con los bytes que ese codec no define (`❌`,
  `⚠️`, `👍`) y el `2>/dev/null || true` del hook se lo traga: la línea desaparece sin rastro.
  Arreglados los 7 sitios con `PYTHONIOENCODING=utf-8:replace`, con test que lo vigila.
- **El criterio del shell vive solo en la suite**, no en `lint_plugin.py` (decisión de T-05): el
  bloque compartido juzga `.py`, y meter un parser de shell en el linter le haría opinar sobre los
  hooks de cualquier plugin consumidor, que ni son nuestros ni tienen síntoma medido. Consecuencia
  asumida: un consumidor que escriba sus propios hooks no hereda esa vigilancia — igual que ya pasa
  con la regla del lado padre sobre SUS tests.
- ~~`evals/run.py` …~~ **Cerrada en T-04.** Estaba mal localizada: la llamada con `text=True` sin
  `encoding` no es el `subprocess.run` de la línea 124 —ese usa solo `capture_output=True`, devuelve
  bytes y descarta el resultado— sino la **indirecta** `runner(cmd, cwd=cwd, capture_output=True,
  text=True, …)` de la línea 268, cuyo `runner` por defecto es `subprocess.run` (línea 328). Arreglada
  con `encoding="utf-8", errors="replace"`, y el `runner` falso de `evals/test_evals.py` afirma ahora
  que los recibe, así que no hace falta fixture nueva ni `ANTHROPIC_API_KEY`.
- **Las suites (`test_*.py`) quedan fuera del criterio compartido**, por diseño: no imprimen a la
  consola de nadie, así que la regla del snippet no les aplica y el linter no las mira. La del lado
  padre sí les afecta (un desarrollador en Windows ejecutando la suite se comía el mismo
  `UnicodeDecodeError`), así que las 42 llamadas están arregladas y las vigila
  `test_las_suites_tambien_decodifican_a_sus_hijos_como_utf8`, que vive solo en el repo y no viaja en
  el paquete portable. Un plugin consumidor no hereda esa vigilancia sobre SUS tests.

---

## Revisión de dos lentes — intento 1: 1 Critical, 6 Important, 5 Minor → todos corregidos (T-04)

Lentes **A** (conformidad) y **B** (corrección) sobre `51da438..c0ce71f`, más **D** (rendimiento), que activó `review-lens-select.py` por RUTA (`progress-report.py ~ repo`, `export-skills.py ~ export`). Lente **C** no aplicó. Puerta de alcance previa: `scope-check.py --base 51da438` → exit 0, 39 ficheros, 0 fuera. Las tres corrieron por **subagente genérico**: el agente `reviewer` no está instalado en esta sesión (degradación con aviso, §2.3 de la skill).

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Critical | `guardrail-check.py:397` leía el payload del hook con el codec del locale y el `except` convertía el `UnicodeDecodeError` en **allow**: bajo cp1252, un emoji en el contenido apagaba el guardarraíl de alcance y de rama | T-04 | El snippet cubre también `sys.stdin` | Antes: stdout vacío, exit 0, `error interno (UnicodeDecodeError…) — se permite`. Después: `permissionDecision: deny` |
| 2 | Critical | `task-brief.py:375` decodificaba a `ledger-lint.py` sin `encoding=`: **regresión** de T-01, porque desde T-01 los hijos emiten UTF-8 siempre | T-04 | `encoding="utf-8", errors="replace"` | Antes: `UnicodeDecodeError: 'ascii' … 0xe2`, exit 1. Después: exit 2 con `❌ ledger inválido…` |
| 3 | Important | El mismo fallo del lado padre en el resto del repo | T-04 | Barrido AST: **14 scripts + 42 suites = 56** llamadas | Después: `scripts: 0 · tests: 0` |
| 4 | Important | El aviso del linter era `in data` (subcadena): falso negativo con el snippet dentro de `main()` o citado en un docstring | T-04 | Comprobación estructural con `ast` | Los 2 falsos negativos reproducidos: linter viejo 0 avisos, nuevo 2 |
| 5 | Important | El descubridor del test partía `git ls-files` por espacios: perdía rutas con espacio o no-ASCII **en silencio** | T-04 | `git -c core.quotepath=false ls-files -z` | Con `scripts/año.py` y `scripts/mi script.py`: antes `descubiertos: []` |
| 6 | Important | Linter y suite excluían cosas distintas mientras la doc decía «el mismo criterio» | T-04 | Bloque `--8<--` replicado byte a byte + test que compara veredictos | 9.550 caracteres idénticos en las dos copias |
| 7 | Important | La fila de la iniciativa en `docs/roadmap/README.md` quedó **fuera** de la tabla; el `grep -c` de la verificación no podía verlo | T-04 | Fila movida dentro + `tests/test_roadmap_index.py` | Mutación: al sacarla, 2 tests rojos. Cazó de paso una fila que faltaba desde el 20/08 |
| 8 | Minor | `INSTALL.md` (+EN) contradecía a `GOT-005` sobre qué se ve en consola legacy | T-04 | Se deja la versión medida | `âœ…`, no `?` |
| 9 | Minor | El desglose de `165 passed` no cuadraba (27×4+3 = 111) y «(×3 avisos históricos)» era falso | T-04 | Desglose real 54+108+3 y los tres avisos nombrados | Verificado contra `git show 25c7a7a` |
| 10 | Minor | Frase de 58 palabras en `CONVENTIONS` regla 8 (+EN) | T-04 | Partida | Máx. 36 palabras (ES) / 38 (EN) |
| 11 | Minor | `release.py` afirmaba que un exit ∉ {0,1} «es un fallo del ENTORNO, no del repo»: falso para el `return 2` de `changelog-sync` | T-04 | Redacción corregida | `changelog-sync --check` sin `CHANGELOG.md` sale 2 |
| 12 | Minor | 54 de los 113 subprocesos de la suite nueva eran relanzamientos idénticos | T-04 | `_ejecutar` memoizado | 8,47 s → 4,93 s; A/B sin caché: mismos 228 verdes |

**Tres afirmaciones mías rebatidas por el implementador, con evidencia, y arbitradas a su favor** (rebatir no consume intento): (a) 7 de los 20 sitios de `subprocess` que le pasé usan `capture_output=True` **sin** `text=True`, devuelven bytes y solo leen `.returncode` — no decodifican, y añadirles `encoding=` los pasaría a modo texto sin motivo; (b) la deuda de `evals/run.py` no estaba en `:124` sino en `:268`, una llamada **indirecta** (`runner(...)`, asignado a `subprocess.run` en `:328`) que ningún barrido por callee ve — cerrada, y sin necesidad de `ANTHROPIC_API_KEY`; (c) `PYTHONIOENCODING=cp1252` **no** reproduce el Critical 2, porque solo toca los streams propios y `subprocess(text=True)` usa `locale.getpreferredencoding()`: la receta correcta es `LC_ALL=C PYTHONCOERCECLOCALE=0 PYTHONUTF8=0`, y así consta en el ledger y en el test.

## Revisión de dos lentes — intento 2: 5 Important, 2 Minor → todos corregidos (T-05)

Lentes **A** y **B** sobre `c0ce71f..b21de3d` (62 ficheros), con la tabla del intento 1 traspasada («esto ya lo juzgaste así; re-evalúa solo lo corregido»). La Lente A verificó una por una las 12 correcciones del intento 1 —reproduciendo el antes/después, no creyéndose el ledger— y las dio **todas ✓**. Lente **D** no se relanzó: sus dos motivos son los mismos falsos positivos de RUTA ya descartados con medición, y los dos costes que este intento sí introducía (linter con `ast`, memoización) se midieron A/B y están en el ledger.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 13 | Important | El criterio solo miraba al que **escribe**: filtraba por «no-ASCII en el fuente», y el lado que **lee** no depende del fuente sino del payload. La 28.ª pieza, `pick_asset.py`, era ASCII pura, hacía `json.load(sys.stdin)` y quedaba invisible — y su crash se disfrazaba de `no release asset for <os>/<arch>` | T-05 | `exige_snippet` = no-ASCII **o** `lee_stdin` | Antes: `bad json: 'charmap' … byte 0x81 in position 19`, exit 1. Después: `https://x/y`, exit 0 |
| 14 | Important | La doc decía «**todo** script del plugin» y el guardarraíl vigilaba menos | T-05 | Decidida y escrita la regla real: «escribe símbolos **o** lee `stdin`» | `CONVENTIONS` ES/EN, `plugin-dev` regla 6, `GOT-005` |
| 15 | Important | El test de coincidencia se ponía **rojo por un `.py` sin `git add`**, con un mensaje que mandaba a buscar una divergencia inexistente | T-05 | Se compara solo lo versionado; lo no versionado se nombra aparte | Con el borrador en el árbol: antes `1 failed`, después `246 passed` |
| 16 | Important | Evidencia **tautológica**: el test que respaldaba «el `except` cubre los tres casos, medidos» no tenía ninguna aserción ni tocaba ningún script | T-05 | Dos tests sobre `ledger-lint.py` real + mutante sin `except` | Mutante: los 3 casos caen con su excepción concreta |
| 17 | Important | Cifras del ledger desactualizadas (`3 tarea(s)` → 4; `114·58·56` y `228` tests) | T-05 | Remedidas, con la corrección fechada en vez de reescrita en silencio | `117 · 58 · 59` y `229` sobre `b21de3d` |
| 18 | Minor | `GOT-005` citaba el byte `0xc2`; el real es `0xe2` (lead byte de `❌`) | T-05 | Corregido | Remedido con el `task-brief.py` de `c0ce71f` |
| 19 | Minor | `test_la_salida_sigue_siendo_utf8_no_interrogantes` **se saltaba** justo el caso que su nombre dice detectar | T-05 | El skip pasa a fallo, con una única exención nombrada y comprobada | Medido: las 54 combinaciones emiten no-ASCII; el skip no se disparaba nunca |

**Rebatido con evidencia y arbitrado a favor del implementador:** la mitad de un Minor mío («llega mojibake al `systemMessage`») no se reproduce — cp1252 hace ida y vuelta byte a byte con los códigos que sí define, así que `📋` y `·` salen intactos; lo real es el **crash silencioso** con los bytes indefinidos. Y el alcance era mayor del que yo dije: **7 sitios**, no 2. La deuda heredada «los `.sh` no revientan (bash no codifica)» resultó **falsa** y queda cerrada: no imprimen con `printf`, componen con `python3 -c`.

## Revisión de dos lentes — intento 3 (último del bucle): 1 Important, 1 Minor → corregidos (T-06)

Lente **B** sobre `b21de3d..HEAD`, dirigida a lo que T-05 tocó (criterio compartido, guardarraíl de los `.sh`, tests nuevos), que es donde un error costaba más. La lente verificó además **todas** las cifras del ledger de T-05 y las dio por reproducidas literalmente, incluido que nada de T-05 viaja en el paquete portable (`nemesis/` no se exporta: hash `a5c14e24…` idéntico al de T-04).

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 20 | Important | `lee_stdin` **se apagaba a sí misma**: excluía la sentencia que contiene el `reconfigure`, y `ast.walk` recorre los ancestros, así que el snippet dentro de `main()` sacaba de la detección el cuerpo entero de `main()` — el anti-patrón que el linter existe para cazar apagaba al linter | T-06 | Se excluye solo el `iter` del `for` del snippet; y `input()`/`fileinput.input()` cuentan | Antes: `lee_stdin` False, 0 avisos, suite verde, ejecución real `UnicodeDecodeError … 0x90`. Después: True, con los 10 casos de `CASOS_LEE_STDIN` en su veredicto |
| 21 | Minor | El guardarraíl de los `.sh` solo reconocía `python3 -c '…'`: comillas dobles, heredoc, `python` sin el `3` y `"$PY" -c` pasaban verdes y sin señal | T-06 | La regla deja de parsear el programa y pasa a ser uniforme: todo python en línea lleva la variable | Las 9 formas de `FORMAS_DE_PYTHON_EN_LINEA` con su veredicto; 8 sitios en el repo, los 8 con la variable |

**Cierre del bucle.** Tres intentos, el máximo que fija la skill. Los dos gaps del intento 3 se corrigieron directamente en la orquestación —son mecánicos, con `fichero:línea` y escenario reproducido, y cada uno lleva su test de regresión y su mutación— y **no se lanzó un cuarto intento**, que la skill no contempla. Queda dicho para quien lea esto: la última corrección no ha pasado por una lente de contexto fresco; lo que la respalda son los 265 tests de `tests/test_console_encoding.py`, la suite completa en verde en las dos codificaciones, y las mutaciones que demuestran que cada test nuevo puede ponerse rojo.
