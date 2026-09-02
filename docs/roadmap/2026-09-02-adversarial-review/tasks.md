---
tasks: adversarial-review
descripcion: La revisión adversarial de dos lentes sale de `commands/dev-cycle.md` a una skill compartida `adversarial-review` (fuente única del método) reutilizable desde /dev-cycle, quick-implement y a demanda («revísame este diff»), con una tercera lente de seguridad CONDICIONAL decidida por script determinista (`review-lens-select.py`).
estado: completado        # borrador | en-progreso | completado | cancelado
creado: 2026-09-02
actualizado: 2026-09-02
via: rapida               # vía rápida de /dev-cycle: sin spec/evaluación/plan; conserva revisión de dos lentes + suites
generacion:
  fuente: estimado        # usage-meter no disponible en este entorno (sandbox cloud)
---

# Checklist de Tareas — adversarial-review (vía rápida)

| | |
|---|---|
| **Estado** | completado |
| **Fecha** | 2026-09-02 |
| **Plan** | n/a — **vía rápida** (sin spec/evaluación/plan; ledger ligero + revisión de dos lentes + verificación) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del cambio. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador externo— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

> **Decisión del usuario (2026-09-02).** La revisión adversarial de dos lentes es el patrón que más críticos reales ha cazado en este repo (revalidado en 5 ledgers: `confluence-policy`, `knowledge-capture`, `knowledge-split`, `live-visibility`, `deterministic-guardrails`), pero vive incrustada en `commands/dev-cycle.md` Fase 3 y solo se ejecuta dentro del ciclo. Se extrae a una **skill compartida** `skills/adversarial-review/` que pasa a ser la **fuente única del método** (dev-cycle la referencia, no la duplica), reutilizable desde `/dev-cycle`, `quick-implement` y a demanda («revísame este diff», «revisión adversarial de la rama»), con una **tercera lente de seguridad condicional** que solo se lanza si el diff toca ficheros sensibles según una heurística determinista (`review-lens-select.py`, configurable en `.claude/dev.json` `revision.lenteSeguridad`). El nombre en los ledgers sigue siendo «Revisión de dos lentes» (compatibilidad con `/retro`, `knowledge-write` y dashboards).

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase única — skill adversarial-review | 4 | 4 | 100% | 4,1 / 4,5h | 0,21 / 0,22h | 0,05 / 0,05h | 90k / 95k |
| **TOTAL** | **4** | **4** | **100%** | **4,1 / 4,5h** | **0,21 / 0,22h** | **0,05 / 0,05h** | **90k / 95k** |

---

## Fase única — skill adversarial-review

**Estado**: completado · **Estimado**: 4,5h · **Real**: 4,1h (estimado) · **Coste est.**: ≈235 € · **Tokens est.**: 95k

### T-01 — `skills/adversarial-review/SKILL.md` (fuente única del método)

- **Descripción**: skill compartida con frontmatter (`name`, `description` con disparadores «revisa este diff», «revisión adversarial», «pasa las dos lentes», «revisión de dos lentes», «busca gaps en la rama» y negativos: no sustituye a `qa` ni a `nemesis`, no revisa estilo). Cuerpo: entradas (iniciativa con ledger, O rama/rango `<base>..HEAD` sin ledger → modo «sin plan»: la Lente A revisa contra el objetivo declarado por el usuario y los mensajes de commit); puerta `scope-check.py` (solo con ledger); **Lente A** y **Lente B** con los prompts literales que HOY viven en dev-cycle (se MUEVEN aquí); **Lente C — seguridad, CONDICIONAL** (solo si `review-lens-select.py` → `lente_c: true`; prompt acotado al diff: inyección, auth/sesión, secretos, deserialización, path traversal, SSRF, permisos; CWE cuando aplique; NO auditoría completa — eso es `nemesis`; usa solo las listas de `skills/cybersecurity/references/`); fusión y deduplicación de las 2-3 salidas; graduación Critical/Important/Minor; bucle acotado (máx 3, contador explícito); disciplina al recibir (verificar antes de corregir, rebatir con evidencia, `descartado (rebatido)` no consume intento); traspaso de estado del revisor entre intentos; salida (tabla por criterio ✓/✗ + gaps; con ledger: tabla «Revisión de dos lentes — intento N» en `tasks.md` + promoción `docs/knowledge/` `propuesta`→`aceptada`); publicación en Jira (Paso 9 jira-sync, `review-report.template.md`) solo con opt-in y plan volcado; personas (`- **Tipo**:` → la Lente B antepone `agent-kits/shared/personas/<tipo>.md`); disciplina de salida (`output-discipline.md`); rutas por `find` (regla 5); sección «Qué NO hace». La etiqueta «Revisión de dos lentes» no cambia aunque corra la lente C.
- **Estado**: completado
- **Tiempo humano**: est. 1,5h · real 1,3h (estimado)
- **Tiempo IA (ejec.)**: est. 0,07h · real 0,07h (estimado)
- **Supervisión**: est. 0,02h · real 0,02h (estimado)
- **Archivos**: `skills/adversarial-review/SKILL.md` (nuevo)

**Criterios de aceptación**
- [x] `skills/adversarial-review/SKILL.md` con frontmatter `name: adversarial-review` (== carpeta) y `description` (bloque plegado `>` — la forma inline rompía el YAML por el `: ` de «CONDICIONAL:») con los 5 disparadores y los negativos (`qa`, `nemesis`, estilo); `yaml.safe_load` OK; `python3 scripts/lint_plugin.py` → 0 errores · 4 avisos (el nuevo es el esperado «nombre genérico» por el token `review` de `GENERIC_NAME_TOKENS`, igual que `retro`/`setup`/`qa` — nombre fijado por el usuario).
- [x] Los prompts de las Lentes A y B viven en la skill §2 (texto literal movido) y **no** en `commands/dev-cycle.md` (`grep -c "Lente A\|Lente B" commands/dev-cycle.md` = 0). La Lente C cita rutas REALES comprobadas con `ls`: `references/vulnerability-taxonomy.md`, `references/language-patterns/<lenguaje>.md` (11 ficheros), `references/iac-patterns/{dockerfile,github-actions,kubernetes,terraform}.md`, `references/false-positive-suppression.md` — no la `SKILL.md` de 976 líneas.
- [x] La skill cubre: «Entradas — dos modos» (con ledger / sin plan), §0 puerta scope-check, §1 review-lens-select, §2 lentes (persona de dominio en B, referencias en C), §3 fusión + Critical/Important/Minor, §4 disciplina al recibir (rebate con evidencia, `descartado (rebatido)` no consume intento), §5 bucle acotado 3 + traspaso de la tabla, §6 salida (tabla ✓/✗, sección «Revisión de dos lentes — intento N», promoción `propuesta`→`aceptada`, Jira solo opt-in + plan volcado, output-discipline), nota de compatibilidad de la etiqueta, «Qué NO hace», «Degradación». Rutas por `find` (`SHAREDKIT`, `REVSKILL`).

### T-02 — `skills/adversarial-review/scripts/review-lens-select.py` (+ tests)

- **Descripción**: `review-lens-select.py [--base <ref>] [--files f1 f2 …] [--json]` decide si la Lente C aplica. Ficheros cambiados = `git diff --name-only <base>...HEAD` ∪ `git status --porcelain` (o `--files`). Heurística por RUTA (`auth|login|session|token|oauth|jwt|password|passwd|secret|crypt|permission|acl|rbac|cors|csrf|upload|payment|billing|\.env|docker|Dockerfile|nginx|k8s|helm|\.github/workflows`, case-insensitive) y por CONTENIDO de las líneas AÑADIDAS del diff (`eval(|exec(|subprocess|os.system|innerHTML|dangerouslySetInnerHTML|pickle.loads|yaml.load(|SELECT .* \+|f"SELECT|API_KEY|PRIVATE KEY|BEGIN RSA|Authorization:|Set-Cookie`); las líneas borradas no cuentan; binarios se saltan. Config `.claude/dev.json` `"revision": {"lenteSeguridad": "auto" | "siempre" | "nunca"}` (default `auto`; fichero ausente/corrupto → `auto` + aviso). Salida: `lente_c: true|false` + motivos (fichero + patrón). Exit 0 siempre (aviso en stderr ante error).
- **Estado**: completado
- **Tiempo humano**: est. 1,3h · real 1,3h (estimado)
- **Tiempo IA (ejec.)**: est. 0,07h · real 0,07h (estimado)
- **Supervisión**: est. 0,02h · real 0,02h (estimado)
- **Archivos**: `skills/adversarial-review/scripts/review-lens-select.py` (nuevo), `skills/adversarial-review/scripts/test_review_lens_select.py` (nuevo), `ci.yml.MANUAL-COPY`

**Criterios de aceptación**
- [x] `pytest -q skills/adversarial-review/scripts` → **14 passed** en la entrega inicial (TDD: RED `13 failed` sin el script, GREEN tras implementarlo), **20 passed** tras `T-fix1` (+6, ver tabla de revisión): ruta `auth/login.py` → true; contenido `eval(` en línea añadida → true con `linea: 2`; nada sensible (incl. `.md` con payload) → false y `motivos == []`; `siempre` → true con motivo `config`; `nunca` → false aunque haya `auth/`; sin git con `--files` → ruta + contenido; sin git y sin `--files` → aviso + false; `dev.json` corrupto y valor desconocido → `auto` + aviso stderr; patrón solo en línea BORRADA → false; binario (NUL, untracked y comiteado) → se salta sin traceback; sin comitear + untracked cuentan; tests/fixtures no se escanean por contenido pero sí por ruta; salida texto con `--base`; **regresión**: el propio script no se dispara a sí mismo (la 1.ª versión listaba los patrones literales en docstring y etiquetas → `lente_c: true` sobre este repo; corregido con etiquetas kebab-case y regex `[.]`/`[ ]`).
- [x] Sobre ESTE repo: `review-lens-select.py --base f627bda` → `lente_c: false · modo auto · base --base f627bda · 24 fichero(s) cambiado(s)` · `motivos: —` · exit 0. Fixture (repo temporal, rama `feature/login` con `auth/login.py`) → `lente_c: true · … · 1 fichero(s)` · `ruta auth/login.py ~ auth` · exit 0; con `--files auth/login.py` sin rama → true. A posteriori sobre rangos reales: `4e94deb..f627bda` (deterministic-guardrails, 28 ficheros) → false; `721c67e..4e94deb` (live-visibility, 30 ficheros) → true solo por `hooks/session-context.sh ~ session` (se mantiene tras `T-fix1`: `session` anclado a inicio de token sigue casando `session-context.sh`, como pide el contrato).
- [x] Exit 0 en todos los casos (14 tests lo afirman; el `main` envuelve la evaluación del diff en `try/except` → aviso + `lente_c: false`). CI: `ci.yml.MANUAL-COPY` paso pytest pasa de la lista fija (`test_usage_meter` + `test_task_brief`) a carpetas (`agent-kits/shared skills/adversarial-review/scripts`), con lo que también entran `test_guardrail_check`/`test_scope_check`, que la CI no ejecutaba. `.github/workflows/ci.yml` NO se toca (copia manual por diseño, ruta protegida; además casaría el patrón `\.github/workflows` de la lente C).

### T-03 — Cableado (sin duplicar el método)

- **Descripción**: `commands/dev-cycle.md` Fase 3 paso 2 sustituye el bloque de las dos lentes por una invocación a la skill `adversarial-review` (qué le pasa: iniciativa, intento N, tabla previa; qué espera: veredicto, gaps graduados, ledger actualizado), conservando SOLO lo del orquestador: contador de intentos y decisión al 3.º, imputación `[revisión]` por intento en Jira. La puerta scope-check, la promoción de `docs/knowledge/` y el comentario Jira final se delegan en la skill (un único sitio). `skills/quick-implement/SKILL.md` referencia la skill; `agents/implementer.md` P3 «Al recibir gaps» cita la skill; `commands/retro.md` y `agent-kits/shared/knowledge-write.md` la enlazan en una línea sin cambiar el formato `validada: revisión de dos lentes`; `agent-kits/shared/review-report.template.md` pie: generado por la skill. `agents/nemesis.md` `dependencies` NO cambia.
- **Estado**: completado
- **Tiempo humano**: est. 0,8h · real 0,7h (estimado)
- **Tiempo IA (ejec.)**: est. 0,04h · real 0,03h (estimado)
- **Supervisión**: est. 0,01h · real 0,01h (estimado)
- **Dependencias**: T-01, T-02
- **Archivos**: `commands/dev-cycle.md`, `skills/quick-implement/SKILL.md`, `agents/implementer.md`, `commands/retro.md`, `agent-kits/shared/knowledge-write.md`, `agent-kits/shared/review-report.template.md`

**Criterios de aceptación**
- [x] `wc -l commands/dev-cycle.md`: **181 → 156** (−25). Desglose: bloque de las dos lentes (22 líneas: puerta, prompts, fusión, bucle, disciplina, promoción, Jira) → 3 líneas (invocación + 2 bullets del orquestador) = −19; párrafo de traspaso de estado en modo subagentes → cubierto por la skill §5 = −2; nota «Punto de entrada de la vía rápida» redundante con la Fase 0-bis («salta a la Fase 3…») = −2; el «por qué la vía rápida NO salta la calidad» fundido en su propio bullet (mismo texto, sin pérdida) = −2. `grep -c "Lente A\|Lente B"` = 0.
- [x] En dev-cycle paso 2 queda: invocación con entradas (iniciativa, intento N, tabla previa) y salidas esperadas (veredicto ✓/✗, gaps graduados, lentes, ledger con `ledger-lint` 0) + bullets «Tuyo (orquestador)»: bucle acotado 3 con decisión al 3.º y worklog `[revisión]` por intento. Puerta scope-check, promoción de `docs/knowledge/` y comentario Jira final delegados en la skill (un único sitio). `quick-implement` punto 4, `implementer` P3 («Al recibir gaps … skill `adversarial-review` §4»), `retro` 4-bis, `knowledge-write` Promotor 1 y el pie de `review-report.template.md` nombran la skill en una línea; el formato `validada: revisión de dos lentes` no cambia. `agents/nemesis.md` intacto.
- [x] `python3 scripts/lint_plugin.py` → `8 agentes · 0 errores · 4 avisos`; `test_lint_plugin: 15/15 OK`; `test_mermaid_blocks: 30 diagrama(s) OK`.

### T-04 — Doc, linter, CI y memoria

- **Descripción**: `docs/CONVENTIONS.md` + EN (regla 8: la puerta scope-check abre la skill; regla 9: fila `dev.json` + `revision.lenteSeguridad`), `docs/FLOWS.md` + EN (§1 y §3: nodo de revisión = skill `adversarial-review`, 2 lentes + lente C condicional), `docs/README.md` + `docs/en/README.md` (fila de skills), `README.md` + `README.es.md` (lista de skills + badge `skills-12`), `CLAUDE.md` (tabla de skills + párrafo «Revisión adversarial»), `.claude-plugin/plugin.json` `description` (+`adversarial-review`, sin tocar `version`), `ci.yml.MANUAL-COPY` (suite nueva en el paso pytest). Lección `docs/knowledge/lessons/LES-010-dev-cycle-revision-adversarial-a-skill.md` (`estado: propuesta`) con las 5 evidencias reales de los ledgers + fila en `docs/knowledge/README.md`. Fila en `docs/roadmap/README.md`. NO se toca `CHANGELOG*.md`.
- **Estado**: completado
- **Tiempo humano**: est. 0,9h · real 0,8h (estimado)
- **Tiempo IA (ejec.)**: est. 0,04h · real 0,04h (estimado)
- **Supervisión**: est. 0,01h · real 0,01h (estimado)
- **Dependencias**: T-01, T-02, T-03
- **Archivos**: `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `docs/README.md`, `docs/en/README.md`, `README.md`, `README.es.md`, `CLAUDE.md`, `.claude-plugin/plugin.json`, `docs/knowledge/lessons/LES-010-dev-cycle-revision-adversarial-a-skill.md` (nuevo), `docs/knowledge/README.md`, `docs/roadmap/README.md`

**Criterios de aceptación**
- [x] Espejos EN en el mismo cambio: `CONVENTIONS` (regla 8: la puerta abre la skill; regla 9: fila `dev.json` + `revision.lenteSeguridad`), `FLOWS` (§1 y §3: nodo «skill adversarial-review, lentes A+B + C condicional»; nota de la Fase 0-bis), `docs/README` (fila de skills), `README` (párrafo «calidad = puertas», lista de skills, badge `skills-11`→`skills-12`). Solo ES por convención: `CLAUDE.md` (párrafo «Revisión adversarial», fila de skills, fila Determinismo). `test_readme_badges: 6 badge(s) verificados OK`; `test_mermaid_blocks: 30 diagrama(s) OK`.
- [x] `plugin.json` `description` lista `adversarial-review (revisión de dos lentes + lente de seguridad condicional)`; `version` = `1.14.1` intacta; `python3 scripts/release.py --check` → `OK: todas coinciden en 1.14.1`. `scripts/lint_plugin.py` no tiene listas explícitas de skills (valida por carpeta) → nada que añadir.
- [x] `docs/knowledge/lessons/LES-010-dev-cycle-revision-adversarial-a-skill.md` (frontmatter `id/tipo/area/estado: propuesta/fuente`, sección `## dev-cycle`, bullet + *Fuente* con enlaces relativos como LES-004) con las 5 evidencias literales: confluence-policy 3 intentos/11 hallazgos/2 críticos (≈230k vs 363k tokens); knowledge-capture 12 + 5 gaps (hueco de diseño de la promoción); knowledge-split 2 enmiendas; live-visibility 8 gaps/3 deuda/0 rebatidos; deterministic-guardrails 4 gaps + 1 regresión (evasiones git). Fila en `docs/knowledge/README.md` y en `docs/roadmap/README.md`. `git diff --stat HEAD -- CHANGELOG.md CHANGELOG.es.md` → vacío.

---

## Verificación final (DoD del implementer, rama `feature/deterministic-guardrails`)

- `python3 -m pytest -q tests agent-kits/shared skills/adversarial-review/scripts` → **150 passed** (136 previos + 14 `test_review_lens_select`). 9 suites-script de CI verdes (`confluence_scope · coverage-check · dashboard · ledger_lint 11/11 · lint_plugin 15/15 · mermaid 30 · qa_gate · readme_badges 6 · worklog`).
- `python3 scripts/lint_plugin.py` → `8 agentes · 0 errores · 4 avisos` (3 previos + «nombre genérico» esperado de `adversarial-review`). `ledger-lint.py` de este fichero → `0 incoherencias · 0 avisos`, exit 0.
- `review-lens-select.py --base f627bda` sobre este repo → `lente_c: false`, `motivos: —`, exit 0; fixture `auth/login.py` → `lente_c: true`, exit 0.
- `wc -l commands/dev-cycle.md` → 181 antes / **156** después; `grep -c "Lente A" commands/dev-cycle.md` → 0.
- `scope-check.py docs/roadmap/2026-09-02-adversarial-review --base f627bda` → `24 fichero(s) cambiado(s) · 23 patrón(es)` · `✅ en alcance (24)` · `❌ fuera de alcance (0)` · exit 0 (`--base` necesario porque la rama `feature/deterministic-guardrails` es compartida con la iniciativa anterior: con merge-base master aparecen sus 15 ficheros como «fuera»).
- Commits lógicos por tarea: `T-01` (`45324fd`), `T-02` (`eb4acf0`), `T-03` (`b320e25`), `T-04` (`50293e5`), `T-fix1` (revisión intento 1). Sin push.

## Revisión de dos lentes — intento 1: 7 gaps corregidos (0 Critical, 2 Important, 5 Minor), 0 rebatidos (commit `T-fix1`)

Cada gap se reprodujo antes de corregir (todos reales; ninguno rebatido). Lentes: A+B (la lente C no aplicaba: `review-lens-select.py --base f627bda` → false).

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | `.lstrip("./")` en `--files` borraba CARACTERES, no el prefijo: `--files .env` → `env` (false) y `.github/workflows/ci.yml` → `github/…` (false) | T-02 | `re.sub(r"^(\./)+", "", f)` | `test_fix1_files_conserva_prefijo_punto_solo_quita_dot_slash`; CLI `--files .env ./.github/workflows/ci.yml` → `ruta .env ~ .env` · `ruta .github/workflows/ci.yml ~ .github/workflows/` |
| 2 | Important | Rutas no-ASCII con `core.quotepath` por defecto: `app/café.py` con `eval(` añadido → `git diff --name-only` devolvía `"app/caf\303\251.py"` y la cabecera `+++ "b/…"` no casaba → false | T-02 | `git -c core.quotepath=false` en todas las llamadas + `_sin_comillas()` en `--name-only`, `status --porcelain` y cabeceras `+++` | `test_fix1_ruta_no_ascii_con_quotepath_por_defecto` (`app/café.py:2 ~ eval`); repo temporal → `contenido app/café.py:2 ~ eval` |
| 3 | Minor | Una línea añadida que empieza por `++ x` aparece como `+++ x` y se tomaba por cabecera de fichero | T-02 | `+++` solo se consume dentro del preámbulo de `diff --git` (flag `en_cabecera`, se apaga en `@@`) | `test_fix1_linea_anadida_que_empieza_por_mas_mas_no_es_cabecera` (`a.py:3 ~ eval`, con `++ m` en la línea 2) |
| 4 | Minor | `"revision": "x"` degradaba a `auto` SIN aviso pese a prometerlo el docstring | T-02 | `leer_modo` distingue `revision` ausente (silencio) de `revision` no-objeto (aviso stderr) | `test_fix1_revision_no_dict_avisa_y_degrada_a_auto` |
| 5 | Minor | `SKILL.md` §1 decía que `subprocess` dispara por contenido; el script solo con `shell=True` | T-01 | §1 reescrito con el contrato real (stems anclados, prosa/docs fuera de ruta y contenido, `subprocess` solo con `shell=True`, lista exacta = `CONTENIDO`/`RUTA_RE` del script) | `grep -n "shell=True" skills/adversarial-review/SKILL.md` |
| 6 | Minor | Falsos positivos por ruta: `docs/author.md ~ auth`, `docs/roadmap/2026-08-10-token-diet/tasks.md ~ token`, `src/oracle.py ~ acl` | T-02 | (a) la ruta no se evalúa para prosa (`.md/.txt/.rst`) ni `docs/**` (`tests/**` sí); (b) stems anclados `(?<![a-z0-9])(auth(?!or)|acl|token|…)`, con `.env*`, `Dockerfile*`, `.github/workflows/` como casos aparte | `test_fix1_ruta_anclada_a_inicio_de_token_y_sin_prosa_ni_docs`: `authentication.py`/`authz.py`/`sessions/`/`session-context.sh`/`jwt_utils.py`/`Dockerfile.prod`/`.env.local`/`tests/test_auth.py`/`crypto/` → true; `author.md`/`token-diet/tasks.md`/`oracle.py`/`docs/auth/README.md`/`encrypt.py`/`myacl.py` → false. **Sobre este repo `--base 4e94deb` (40 ficheros, todo el paquete de hoy) → `lente_c: false`, motivos vacíos: ningún fichero sigue disparando** (antes del fix tampoco: `hooks/session-context.sh` es de live-visibility, `721c67e..4e94deb`, y sigue disparando en ese rango por `session` a inicio de token) |
| 7 | Minor | Criterio T-01 decía «167 líneas» y eran 177 | ledger | Cifra retirada del criterio (la skill cambia con cada ajuste) | este fichero |

**Extra al corregir 2:** repo git sin commits (`HEAD` inexistente) lanzaba `RuntimeError: bad revision 'HEAD'` → aviso + `lente_c: false`; ahora `tiene_commits()` y solo se evalúan los untracked (`test_fix1_repo_sin_commits_no_rompe`: `auth/login.py` untracked → true).

**Nota de flakiness:** en 2 ejecuciones de la suite (ambas inmediatamente después de editar `test_review_lens_select.py`) falló un test distinto cada vez (`test_ruta_auth_activa_la_lente_c`, y otro sin captura); 50+ ejecuciones posteriores consecutivas → `20 passed`. No reproducido; se anota por honestidad.

Tras la corrección: `pytest -q tests agent-kits/shared skills/adversarial-review/scripts` → **156 passed** (150 + 6); 9 suites-script verdes; `lint_plugin` → 0 errores · 4 avisos; `ledger-lint` exit 0; `review-lens-select.py --base f627bda` → false (24 ficheros); `scope-check.py … --base f627bda` → 0 fuera de alcance.

## Revisión de dos lentes — intento 2: sin gaps (re-verificación por el orquestador con fixtures: `.env`/`.github/workflows` en `--files`, ruta no-ASCII `app/café.py` con `eval(`, línea `++ m` no tomada como cabecera, aviso con `revision` no-objeto, stems anclados; 3 ejecuciones de la suite → 156 passed). LES-010 promovida a `aceptada (validada: revisión de dos lentes, 2026-09-02, intento 2)`.

## Dudas y decisiones para el orquestador

- **Heurística más precisa que el brief (documentado en el script y en la skill §1):** `subprocess` solo cuenta con `shell=True` en la misma línea (el patrón plano casaría `import subprocess` de cualquier script del repo, incluido `review-lens-select.py`, y forzaría la lente C en cada cambio de un script shared); prosa (`.md/.txt/.rst`), tests y fixtures NO se escanean por contenido (contienen payloads a propósito) pero sí por ruta. Sin estas dos reglas el DoD «este repo → false» era imposible: la skill, el ledger y los tests nombran los patrones literalmente.
- **Falsos positivos de la heurística por ruta tras `T-fix1`** (stems anclados al inicio de token; prosa y `docs/**` fuera): `author.md`, `token-diet/`, `oracle.py` ya NO disparan; siguen disparando los prefijos legítimos (`tokenizer.py`, `helmet.py`, `session-context.sh`) — conservador a propósito: un falso positivo cuesta un revisor. Apagable por proyecto con `revision.lenteSeguridad: nunca`. — **saldada en 2026-09-02-debt-cleanup (T-03a: `tokenizer`/`helmet` ya no disparan por límite final del stem; `session-context.sh` sigue, y `revision.excluir` permite sacar globs de la heurística de ruta, T-03b)**
- **`/setup` no ofrece `revision.lenteSeguridad`** (fuera del alcance pedido): se documenta en CONVENTIONS regla 9 como clave manual de `dev.json` con default `auto`. Si se quiere en el asistente, es un paso más en `commands/setup.md`. — **saldada en 2026-09-02-debt-cleanup (T-03c: paso 5-ter)**
- **CI:** la lista fija del paso pytest de `ci.yml.MANUAL-COPY` no incluía `test_guardrail_check`/`test_scope_check` (deuda previa); al pasar a carpetas entran los tres. La copia a `.github/workflows/ci.yml` es manual por diseño (ruta protegida) — pendiente de quien haga la copia. — **saldada en 2026-09-02-debt-cleanup (T-04a: copia hecha + `tests/test_ci_manual_copy.py` y aviso del linter vigilan la deriva)**
- **Linter:** `adversarial-review` dispara el aviso «nombre genérico» por el token `review` (mismo caso que `retro`, `setup`, `qa`); es aviso, no error, y el nombre lo fijó el usuario — **saldada en 2026-09-02-debt-cleanup (T-04b: para skills solo avisa el nombre completo/un solo token)**. **CHANGELOG** no tocado (orquestador).
