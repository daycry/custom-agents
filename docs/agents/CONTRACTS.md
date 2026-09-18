# Matriz de contratos — cómo se hablan las piezas

[`ROLES.md`](ROLES.md) dice **quién decide y quién escribe** cada responsabilidad. Esta matriz dice
**cómo se hablan**: por cada arista invocador → invocado, con qué entrada, qué devuelve, qué
ficheros y marcadores se cruzan, y —lo importante— **qué puerta ejecutable lo comprueba**. Nace del
§8-bis de `docs/roadmap/2026-09-09-plugin-refactor/analysis.md`, que verificó **diez huecos de
contrato** (E1–E10) en un solo día de uso real: ninguno era un fallo de una pieza, todos eran un
acuerdo entre piezas que nadie comprobaba. La matriz tiene **catorce** aristas porque a esos diez se
suman **E11**, que no es un hueco verificado sino la **propuesta C-14 aceptada** por el usuario en la
puerta del plan (2026-09-10), y **E12**, el acoplamiento entre kits que NACIÓ en esta iniciativa
(T-13 hizo que `agent-kits/qa` cargue `agent-kits/shared/scope-check.py`): una arista nueva se
declara aquí el día que se crea, no el día que se rompe. **E13** nace en `knowledge-services` T-05
(`documenter` propone candidatos de conocimiento) y **E14** en T-06 (el Knowledge Gate de
`/dev-cycle`), con el mismo criterio: se declaran el día que se implementan.

La regla que ordena el fichero: **una arista sin puerta ejecutable se rompe en silencio**. Por eso
la columna «Puerta» nunca va vacía; cuando la puerta aún no existe, la celda dice qué tarea la trae
o que la decisión fue no ponerla.

> Gemelo de esta matriz para el **código**: [`agent-kits/shared/copias.json`](../../agent-kits/shared/copias.json)
> (`ADR-016`) declara los bloques replicados a propósito entre piezas y los guarda con
> `tests/test_copias_declaradas.py` + `scripts/lint_plugin.py`. Esta matriz cubre los contratos de
> **protocolo** (quién llama a quién y con qué); `copias.json` cubre los de **texto idéntico**.
> Dominios distintos, misma idea: lo que no está declarado y vigilado, envejece.

---

## 1. Las catorce aristas E1–E14

Columnas fijas y parseables (`scripts/lint_plugin.py` las lee — ver §3): **Arista · Invocador · Invocado ·
Flags/entrada · Exit codes/salida · Ficheros · Marcadores · Puerta · Piezas que describen**.

| Arista | Invocador | Invocado | Flags/entrada | Exit codes/salida | Ficheros | Marcadores | Puerta | Piezas que describen |
|---|---|---|---|---|---|---|---|---|
| E1 · caso sin UI (§8-bis E1; **CERRADO en T-13**) | `commands/dev-cycle.md` Fase 3 | `agents/qa.md` | frontmatter de `improvement-plan.md`; `agent-kits/qa/coverage-check.py <tasks.md> <test-plan.md> [spec.md]` | `0` sin UI declarada o cobertura correcta · `1` referencia rota o `[GWT]` sin cubrir **sin** marcador; JSON final con **11 claves** en la rama con test-plan (`applies`, `defined`, `referenced`, `broken_refs`, `tasks_sin_cobertura`, `tests_sin_referencia`, `gwt_cubiertos`, `gwt_sin_cubrir`, `gwt_sin_id`, `test_plan_na`, `marcador_no_canonico`) y **9** en la rama «sin UI» (`applies`, `gwt_sin_id`, `test_plan_na`, `marcador_no_canonico`, `eximidos`, `eximidos_exigidos`, `rutas_ui`, `rutas_ui_origen`, `rutas_ui_degradado`); `test_plan_na` y `marcador_no_canonico` salen en las **cuatro** ramas | `improvement-plan.md`, `tasks.md`, `test-plan.md` (ausente por diseño) | **`test-plan: n/a (sin UI)`** (literal exacto en las 5 piezas) | `python3 agent-kits/qa/coverage-check.py …` exit 0 + `python3 tests/test_coverage_check.py` — **cubre solo `coverage-check.py`**: comprueba que el literal exime ahí, no que las otras **cuatro** piezas lo escriban igual (cambiarlo en una sola rompe la cadena sin que nada lo vea). **La comprobación del literal en las 5 piezas la trae T-16** (lint de esta matriz) | `docs/agents/planner.md`, `docs/agents/qa.md`, `docs/FLOWS.md` (+`docs/en/FLOWS.md`), `agent-kits/planner/templates/improvement-plan.md`, `ADR-017` |
| E2 · regenerar `interop/` (§8-bis E2; **CERRADO en T-15**) | `agents/planner.md` (mete `interop/**` en `Archivos`) → `agents/implementer.md` (regenera) | `skills/adversarial-review` Lente A | `python3 scripts/export-interop.py` · `--check` · `--list` · `--root` | `0` al día · `1` desincronizado (`export-interop --check: N ficheros al día`) | `agents/**`, `commands/**`, `hooks/**` → `interop/**`, `.codex-plugin/`, `.agents/plugins/` | `interop/**` en el campo `- **Archivos**:` de la tarea | `python3 scripts/export-interop.py --check` exit 0 (puerta de CI y de `scripts/release.py`) | `CLAUDE.md` (regla Interop), `docs/INTEROP.md`, `docs/CONVENTIONS.md` regla 5 |
| E3 · quien DESCRIBE una pieza (§8-bis E3; **CERRADO en T-15 y T-16**) | cualquier pieza tocada | las piezas que la documentan (`docs/agents/<x>.md`, `docs/FLOWS.md`, plantillas, `references/`) | lista de dependientes tomada de esta matriz (columna «Piezas que describen») | n/a (es una regla de alcance, no un script con exit code propio) | `agents/**`, `commands/**`, `skills/**` → `docs/**`, `agent-kits/*/templates/**` | las piezas dependientes enumeradas en `- **Archivos**:` de la tarea | `python3 agent-kits/shared/scope-check.py <iniciativa>` exit 0 + Lente A con esta matriz (T-16 la hace lintable) | `CLAUDE.md` (regla «Documentación en `docs/`»), `docs/CONVENTIONS.md` regla 3, `skills/adversarial-review/references/lens-prompts.md` |
| E4 · disparo de la Lente C (§8-bis E4; **CERRADO en T-18**) | `skills/adversarial-review/SKILL.md` | `skills/adversarial-review/scripts/review-lens-select.py` | `--base <ref>` · `--files` · `--json` · `--root` | `0` siempre; JSON con `lente_c`, `lente_d`, `motivos`, `avisos` | el diff; `.claude/dev.json` | `revision.lenteSeguridad` · `revision.lenteRendimiento` (`auto` · `siempre` · `nunca`) · `revision.excluir` | `python3 -m pytest -q skills/adversarial-review/scripts/test_review_lens_select.py` (fixture del caso F1 → `lente_c: true`) | `skills/adversarial-review/references/lens-c-heuristics.md`, `docs/CONVENTIONS.md` regla 9, `docs/README.md` |
| E5 · nombre real del comando (§8-bis E5; **CERRADO en T-12**) | doc viva (`README*.md`, `docs/INSTALL.md`, `docs/README.md`, sus espejos `docs/en/`, `CLAUDE.md`) | el picker de comandos de Claude Code | `python3 agent-kits/shared/doctor.py [--root] [--plugin-root] [--json]` | `0` sin ❌ · `1` con ❌; fila ℹ️ «nombre de los comandos» + ⚠️ «doc viva sin el espacio de nombres» | los 7 ficheros de doc viva; `commands/*.md` | **`/custom-agents:<cmd>`** (namespace del plugin) vs `/<cmd>` (bundle copiado) | `python3 agent-kits/shared/doctor.py` sin ⚠️ de doc viva + `pytest -q agent-kits/shared/test_doctor.py` | `commands/doctor.md`, `docs/INSTALL.md` (+EN), `docs/README.md` (+EN) |
| E6 · ruido del orquestador en el alcance (§8-bis E6; **CERRADO en T-11**) | `commands/dev-cycle.md` Fase 3 / `agents/implementer.md` DoD | `agent-kits/shared/scope-check.py` | `<docs/roadmap/<fecha>-<slug>>` · `--base <ref>` · `--warn-only` · `--json` | `0` nada fuera · `1` hay ficheros fuera · `2` error de uso; JSON con **15 claves**: `slug`, `base`, `base_desc`, `cambiados`, `en_alcance`, `fuera_de_alcance`, `declarados_sin_tocar`, `patrones`, `excluidos`, `excluir_vigente`, `excluir_usuario`, `excluidos_patron`, `excluidos_usuario`, `avisos`, `info` | `tasks.md` (campos `Archivos`), el diff, `.claude/dev.json` | `EXCLUIR_DEFAULT` (`CONTINUE-HERE*.md`, `.claude/**`, `docs/knowledge/journal/**`) + `alcance.excluir` | `python3 agent-kits/shared/scope-check.py <iniciativa>` exit 0 + `pytest -q agent-kits/shared/test_scope_check.py` | `docs/CONVENTIONS.md` regla 9 (+EN), `agents/implementer.md`, `skills/adversarial-review/SKILL.md` |
| E7 · cadena de calibración (§8-bis E7; **CERRADO en T-17**) | `agent-kits/shared/usage-meter.py` → `generacion:` → `/retro` → `CALIBRATION.md` | `agents/evaluator.md` | `agent-kits/shared/usage-meter.py start` · `close` · `--artefacto <clave>` · `--state` · `--rates` · `--calibration` · `--ratio` · `--transcript-dir` | `0` siempre (degrada, nunca bloquea); JSON con `fuente`, `horas_ia`, `eur`, `ratio_usado` | `.claude/usage-state.json`, `docs/roadmap/CALIBRATION.md`, frontmatter `generacion:` de cada artefacto | **`fuente: medido`** vs **`fuente: estimado`** | `python3 agent-kits/shared/retro-gate.py <iniciativa>` exit 0 (retro + fila en `CALIBRATION.md`) — el agregado visible lo añade T-17 | `docs/observability.md` (+EN), `commands/retro.md`, `commands/roadmap-metrics.md` |
| E8 · tope del brief con `## Diseño` (§8-bis E8; **cubierta por `brief-budget` C-05**, fuera de esta iniciativa) | `commands/dev-cycle.md` (modo `subagentes`) | `agent-kits/shared/task-brief.py` | `<iniciativa> <T-XX>` · `--json` · `--root` · `--tdd` · `--constitucion` · `--knowledge-find` · `--sin-lint` | `0` brief emitido; tope `BRIEF_TOPE_CHARS = 10000` | `tasks.md`, `improvement-plan.md`, `design.md`, `docs/CONSTITUTION.md`, `docs/knowledge/` | `design:` en el frontmatter del plan (añade la sección `## Diseño` al brief) | `pytest -q agent-kits/shared/test_task_brief.py` sobre una iniciativa CON `design.md` (`GOT-009`) | `commands/dev-cycle.md`, `agents/implementer.md`, `agent-kits/shared/README.md` |
| E9 · regex de cabecera de revisión replicada (§8-bis E9; **CERRADO en T-09/T-10**) | `agent-kits/shared/ledger-lint.py` (canónico) | `agent-kits/shared/task-brief.py` y `skills/jira-sync/scripts/jira-flow.py` (respaldos) | n/a (constante en código, no CLI) | n/a (el guardarraíl es el test, no un exit code de la arista) | `agent-kits/shared/ledger-lint.py:179`, `agent-kits/shared/task-brief.py`, `skills/jira-sync/scripts/jira-flow.py`, `agent-kits/shared/copias.json` | `REVISION_HDR_PATTERN` · `_REVISION_HDR_FALLBACK` · centinelas `# --8<-- <bloque>` | `pytest -q tests/test_copias_declaradas.py` + `python3 scripts/lint_plugin.py` (error si un bloque `--8<--` o `_*_FALLBACK` no está registrado) | `ADR-016`, `agent-kits/shared/copias.json` (campos `que_es`/`comparacion`/`delimitacion`), `docs/CONVENTIONS.md` |
| E10 · el detector de TODO se detecta a sí mismo (§8-bis E10; **CERRADO en T-01/T-02**) | `skills/code-health/SKILL.md` | `skills/code-health/scripts/code-health.py` | `<ruta>` · `--exclude-tests` · `--exclude-path <ruta>` (repetible) · `--json` · `--baseline` · `--top` · `--min-lines` · `--langs` · `--since` · `--window` | `0` informe emitido; JSON con `marcadores`, `todos`, `funciones_largas` | el árbol analizado; `docs/roadmap/<…>/code-health-baseline*.json` | `--exclude-path interop` (rutas generadas fuera del informe) | `pytest -q skills/code-health/scripts/test_code_health.py` (el detector no se cuenta a sí mismo; `todos` = 1) | `skills/code-health/SKILL.md`, `docs/README.md` |
| E11 · cifras medidas en documentos vivos vs históricos (§8-bis, propuesta C-14; **CERRADO en T-19**, aceptada por el usuario el 2026-09-10 en la puerta del plan) | `tests/test_cifras_medidas.py` | los documentos con cifras (`README*.md`, `docs/**`, ledgers cerrados) | `pytest -q tests/test_cifras_medidas.py` | `0` cifras vivas al día · `1` una cifra viva desfasada | `tests/test_cifras_medidas.py`, `skills/changelog-sync/references/medicion-escalera.md`, ledgers históricos | **`<!--m:clave=valor-->`** (viva, se compara con la medición de hoy) vs **`<!--m@AAAA-MM-DD:clave=valor-->`** (fechada: conserva clave y cifra, no se compara) | `python3 -m pytest -q tests/test_cifras_medidas.py` exit 0 — **CERRADA en T-19**: el test compara contra `changelog-sync.py --medicion` **solo** las marcas `<!--m:clave=valor-->` de los documentos VIVOS; las de los históricos —y las que cuentan el corpus COMPLETO, que se mueven al abrir o cerrar cualquier iniciativa— van fechadas como `<!--m@AAAA-MM-DD:clave=valor-->` (misma clave, misma cifra, más el día en que se midió; en un documento VIVO la fecha se escribe además en la prosa). `test_no_hay_marcas_vivas_en_documentos_historicos` guarda la regla por UBICACIÓN (aviso en `docs/roadmap/**` y `docs/knowledge/**`, fallo duro sobre el corpus propio de `FICHEROS`; un ledger sin `estado:` NO se exime), `test_una_cifra_del_corpus_no_puede_marcarse_como_viva` por la CLAVE y `test_cada_fichero_vivo_conserva_sus_comprobaciones` el mínimo de comprobaciones vivas POR FICHERO. La válvula `<!--m?:motivo-->` está retirada: no tenía guarda de ubicación y perdía la clave | `ADR-012`, `skills/changelog-sync/references/medicion-escalera.md`, `docs/knowledge/README.md` |
| E12 · acoplamiento entre kits: `coverage-check` usa los helpers de git de `scope-check` (arista **nacida en T-13**, declarada en T-14) | `agent-kits/qa/coverage-check.py` (`_scope_check_mod()`) | `agent-kits/shared/scope-check.py` | carga por ruta relativa (`../shared/scope-check.py`, `importlib`) y uso de **siete firmas**: `repo_root(path)`, `resolver_base(root, base) → (ref, desc)`, `ficheros_cambiados(root, base) → [rutas]`, `git(root, *args)`, `git_disponible()`, `motivo_sin_repo(path) → str` y `hay_git_dir(path) → bool` (las dos últimas, del gap B4-2: se leen con `getattr` y, si no están, `coverage-check` cae al mensaje de dos causas) | sin exit code propio: si la carga falla o una firma cambia, `coverage-check` **degrada** —`rutas_ui_degradado` con el motivo, exit 0— y NUNCA tumba la puerta de `qa`; el precio de la degradación es que el diff no se mira | `agent-kits/qa/coverage-check.py`, `agent-kits/shared/scope-check.py` | ninguno: el contrato son las siete firmas y que la **base del diff sea la misma** que la de la puerta de alcance (duplicar esa escalera sería una copia más que mantener) | `python3 tests/test_coverage_check.py` — `escenario_r4a34_r4a35_r4a40()` comprueba que las cinco primeras firmas existen y son invocables, y `escenario_b42()` las dos del gap B4-2; `escenario_r4a19()` ejecuta la carga real contra un repo git. Sin esa puerta, un renombrado deja la puerta de cobertura verde y **ciega al diff** | `agent-kits/shared/README.md` (fila de `scope-check.py`), `agents/qa.md`, `docs/agents/qa.md` |
| E13 · `documenter` propone candidatos de conocimiento (arista **nacida en `knowledge-services` T-05**) | `agents/documenter.md` (P5-bis, buzón opcional) | `docs/knowledge/candidates/pending/` (consumido después por `agents/knowledge-curator.md`) | ninguno (creación directa de un fichero markdown nuevo; no hay CLI) | n/a: no hay comando que devuelva exit code en esta arista; el candidato es un fichero con frontmatter `category`/`evidencia`/`fuentes`/`tags` | `docs/knowledge/candidates/pending/<AAAA-MM-DD>-<slug>.md` (solo creación, nunca edición de un candidato existente) | **ausencia del campo `estado`** en el candidato propuesto (lo distingue de una entrada `approved/`, gap 34 delegado a T-04) | sin puerta mecánica (decisión, 2026-09-18): el contrato completo (evidencia mínima EXACTA, `fuentes`, `tags`, lista negra) lo exige `curator-gate.py` solo al **aprobar** (T-04) — proponer es deliberadamente más laxo; lo vigila la Lente A contra `docs/agents/ROLES.md` (documenter no aprueba ni escribe `estado`) | `agents/documenter.md`, `docs/agents/documenter.md`, `agents/knowledge-curator.md`, `docs/agents/ROLES.md` |
| E14 · Knowledge Gate de `/dev-cycle` (arista **nacida en `knowledge-services` T-06**) | `commands/dev-cycle.md` Fase 4-bis (tras QA verde y `documenter`) | `agents/knowledge-curator.md` | candidatos de la iniciativa bajo `docs/knowledge/candidates/**`; sin candidatos, la Fase se omite | por candidato, el de `agent-kits/knowledge-curator/curator-gate.py`: `0` decisión permitida · `1` con errores bloqueantes (`approve`) · `2` uso/taxonomía/candidato inválido; **omisión honesta** (una línea, sin fallo) si no hay candidatos que procesar | `docs/knowledge/candidates/**`, `docs/knowledge/approved/**` | ninguno propio: reutiliza el contrato de `curator-gate.py` de T-04 (E13 lo alimenta, esta arista lo dispara desde el ciclo) | `python3 agent-kits/knowledge-curator/curator-gate.py <candidato> --decision … --json` por candidato (T-04); la omisión sin candidatos la vigila la Lente A contra `commands/dev-cycle.md` | `commands/dev-cycle.md`, `docs/FLOWS.md` (+EN), `docs/agents/ROLES.md`, `docs/agents/knowledge-curator.md` |

**Cómo leer el estado de una fila.** «CERRADO en T-XX» = la puerta existe hoy y se puede ejecutar.
«lo cierra T-XX» = la arista está descrita y la puerta llega en esa tarea de
`docs/roadmap/2026-09-09-plugin-refactor/tasks.md`. E8 es la única cubierta **fuera** de esta
iniciativa (`brief-budget`, característica C-05). E11 era la única sin puerta y **ya la tiene**
(T-19); sigue siendo la única que no nace de un hueco verificado, sino de la propuesta C-14 aceptada
en la puerta del plan: diez huecos + una propuesta + un acoplamiento nuevo (E12), no doce huecos. **E12 es el caso
que prueba la regla 1 de §3**: la arista se creó al implementar T-13 y se declaró en el mismo tramo,
con su puerta, en vez de esperar a que un renombrado de firma la rompiera en silencio.

---

## 2. Reglas de `CLAUDE.md` con puerta ejecutable

Las reglas «al tocar X, regenera/actualiza Y» del `CLAUDE.md` de este repo son contratos igual que
las aristas de arriba: sin puerta, son prosa que se olvida. Una fila por regla, con su puerta real.

| Regla de `CLAUDE.md` | Al tocar… | …hay que actualizar | Puerta ejecutable | Qué pasa si se salta |
|---|---|---|---|---|
| **Interop** | `agents/**`, `commands/**`, `hooks/**` | `interop/**`, `.codex-plugin/`, `.agents/plugins/` (**generados**: `python3 scripts/export-interop.py`) | `python3 scripts/export-interop.py --check` (CI + `scripts/release.py`) | Codex y OpenCode cargan una versión vieja de la pieza (es el hueco E2) |
| **Convenciones primero (flujos)** | un flujo de la cadena (quién invoca a quién, en qué orden, con qué puerta) | `docs/FLOWS.md` **y su espejo** `docs/en/FLOWS.md` en el mismo cambio | **sin puerta mecánica** (decisión, 2026-09-11: no hay forma determinista de leer «el flujo cambió» desde un diff): la comprueba la Lente A con esta fila, y el campo `Archivos` de la tarea debe enumerar los dos ficheros (regla E3) | Los diagramas describen una cadena que ya no existe y el siguiente ciclo la sigue |
| **Bilingüe EN/ES** | `README.md`, `CHANGELOG.md`, `docs/{README,INSTALL,CONVENTIONS,FLOWS,observability}.md` | su espejo (`README.es.md`, `CHANGELOG.es.md`, `docs/en/**`) **en el mismo cambio** | **sin puerta mecánica** (decisión, 2026-09-11): hoy no existe suite de espejo bilingüe, así que lo comprueba la Lente A con esta fila; si algún día se escribe, esta celda la nombra | Una de las dos versiones miente; el usuario que lee la otra se lo cree |
| **Copias `.MANUAL-COPY`** | `ci.yml.MANUAL-COPY`, `release.yml.MANUAL-COPY`, `headless.yml.MANUAL-COPY`, `github-templates.MANUAL-COPY/` | su gemelo bajo `.github/` | `pytest -q tests/test_ci_manual_copy.py` (vigila los dos árboles) + `python3 scripts/release.py --dry-run` | CI corre una configuración distinta de la que el repo documenta |
| **Nombres (un agente, un nombre)** | `agents/<x>.md` | `agent-kits/<x>/`, `docs/agents/<x>.md`, fila de `docs/README.md`, `name:` del frontmatter | `python3 scripts/lint_plugin.py` (0 errores) | El agente no se resuelve por nombre, o hay dos piezas con el mismo disparador |
| **Linter + tests + evals** | cualquier pieza | casos en `evals/cases/<kind>-<nombre>.json` (≥ 2 positivos + 1 negativo, el literal casando con la `description` REAL) | `python3 scripts/lint_plugin.py` + `python3 evals/check.py` (ambos 0 errores) | Una pieza sin caso positivo no se dispara y nadie se entera |
| **Skills cortas** | `skills/<skill>/SKILL.md` | mover el detalle a `references/<tema>.md` | `pytest -q tests/test_skill_size.py` (falla > 250 líneas; el linter avisa > 200) | La skill deja de leerse entera y sus pasos dejan de aplicarse |
| **Determinismo (`Verificación` por tarea)** | `tasks.md` con `verificacion: obligatoria` | el campo `- **Verificación**:` de cada `T-XX` | `python3 agent-kits/shared/ledger-lint.py <tasks.md>` exit 0 | Una tarea se cierra sin comprobación reproducible |
| **Alcance del diff** | el código de una iniciativa | el campo `- **Archivos**:` de la tarea que lo toca | `python3 agent-kits/shared/scope-check.py <iniciativa>` exit 0 | Cambios sin declarar que la revisión devuelve como gap Important |
| **Publicar = `scripts/release.py`** | la versión | los 5 manifiestos + los 2 CHANGELOG + `chmod` de los hooks .sh | `python3 scripts/release.py X.Y.Z` (`--dry-run` antes, `--check` después) | Versiones descuadradas entre manifiestos (`LES-012`) |

---

## 3. Cómo se lee y cómo se mantiene

**Cómo se lee.** Busca la arista por su identificador (`E1`…`E12`) o por la pieza que vas a tocar en
la columna «Invocador»/«Invocado». La columna **«Piezas que describen»** es la lista que hay que
meter en el campo `- **Archivos**:` de la tarea que toque esa pieza: es exactamente lo que faltaba
en el hueco E3, y lo que `planner` copia de aquí al planificar.

**Cómo se mantiene.** Tres reglas:

1. **Una arista nueva nace con su puerta o con la razón de no tenerla.** La celda «Puerta» no puede
   quedar vacía: o un comando ejecutable, o «puerta pendiente: la trae T-XX», o «sin puerta
   (decisión del usuario, <fecha>)». Es lo que comprueba la lectura mecánica de abajo.
2. **Las columnas son fijas.** Nueve, en el orden del encabezado, y toda fila de arista empieza por
   `| E`. `scripts/lint_plugin.py` lee este fichero (`comprobar_matriz_contratos`, T-16) y avisa de
   tres cosas: una fila con la columna «Puerta» **vacía**, una Puerta que **nombra un script que no
   existe**, y una fila cuyo número de columnas no es nueve. Cambiar el orden o el número de columnas
   rompe esa lectura, y por eso lo avisa ella misma.
3. **Las rutas que se citan aquí existen.** Se comprueba mecánicamente, y el barrido mira **todas**
   las citas, no solo las que van solas entre acentos graves: una ruta con número de línea
   (`…/ledger-lint.py:179`) o pegada a un comando (`python3 agent-kits/…`) cuenta igual.

**La puerta de esta matriz es el propio linter.** Desde T-16, `python3 scripts/lint_plugin.py` hace
las tres comprobaciones de la regla 2 sobre este fichero, además de comprobar que las rutas y los
`/comandos` citados por `agents/`, `commands/` y `skills/` existen (reglas (a) y (b) de la fila
«Linter + tests» de `CLAUDE.md`, que es la puerta de la regla 3 de aquí abajo). Nacen como **aviso**
y suben a error tras una release limpia. Los dos comandos de abajo siguen valiendo como comprobación
manual rápida, sin depender del linter:

```bash
# ninguna fila de arista con la columna Puerta vacía
python3 -c "t=open('docs/agents/CONTRACTS.md',encoding='utf-8').read(); import re; print([l[:40] for l in t.splitlines() if l.startswith('| E') and re.search(r'\|\s*\|\s*[^|]*\|\s*$', l)])"
# toda ruta del repo citada aquí existe (con o sin `:línea`, esté o no sola entre acentos graves).
# Se filtran los globs (`*`, `<x>`) y `docs/CONSTITUTION.md`, que es artefacto del proyecto
# CONSUMIDOR (opt-in) y por diseño no existe en este repo.
grep -oE '(agents|commands|skills|agent-kits|scripts|tests|hooks|docs|evals|statusline|install|interop)/[-A-Za-z0-9_./*]+\.(py|sh|js|mjs|json|md|toml|yml)(:[0-9]+)?' docs/agents/CONTRACTS.md  \
  | sed 's/:[0-9]*$//' | grep -v '[*]' | grep -v '^docs/CONSTITUTION.md$' | sort -u \
  | while read f; do [ -e "$f" ] || echo "FALTA $f"; done    # salida vacía = al día
```

**Procedencia.** §8-bis de `docs/roadmap/2026-09-09-plugin-refactor/analysis.md` (diez huecos
verificados sobre un ciclo real, 2026-09-09, más la propuesta C-14 aceptada el 2026-09-10 = E11, más el acoplamiento entre kits nacido en T-13 = E12) · característica C-06 del plan, tarea **T-14** ·
decisión de dónde vive la matriz: pregunta abierta 2 de `design.md` §7 — `docs/agents/` porque la
lee una persona y el linter, mientras que el registro de copias vive en `agent-kits/shared/` porque
viaja con el kit.
