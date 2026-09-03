---
tasks: activation-reliability
descripcion: Cerrar la brecha de FIABILIDAD DE ACTIVACIÓN (que la skill/comando/agente correcto se dispare siempre) y de robustez del prompt ante racionalizaciones del modelo — suite de evals de comportamiento (`evals/`), índice de piezas inyectado al arrancar la sesión (`skill-index.py` + `session-context.sh`), tablas de racionalización en los 3 puntos críticos (implementer DoD, adversarial-review, qa) y linter/doc/lección.
estado: completado        # borrador | en-progreso | completado | cancelado
creado: 2026-09-03
actualizado: 2026-09-03
via: rapida               # vía rápida de /dev-cycle: sin spec/evaluación/plan; conserva revisión de dos lentes + suites
generacion:
  fuente: estimado        # usage-meter no disponible en este entorno (sandbox cloud)
---

# Checklist de Tareas — activation-reliability (vía rápida)

| | |
|---|---|
| **Estado** | completado |
| **Fecha** | 2026-09-03 |
| **Plan** | n/a — **vía rápida** (sin spec/evaluación/plan; ledger ligero + revisión de dos lentes + verificación) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del cambio. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador externo— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

> **Decisión del usuario (2026-09-03).** Comparado con el plugin superpowers, este plugin gana en método pero pierde en fiabilidad de activación y en robustez del prompt ante racionalizaciones. Se cierran ambas en una iniciativa de vía rápida: evals (T-01), índice al arrancar (T-02), tablas de racionalización (T-03), linter+doc+lección (T-04). `CHANGELOG*.md` lo toca el orquestador.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase única — activación fiable | 4 | 4 | 100% | 7,4 / 7,5h | 0,39 / 0,40h | 0,08 / 0,08h | 155k / 160k |
| **TOTAL** | **4** | **4** | **100%** | **7,4 / 7,5h** | **0,39 / 0,40h** | **0,08 / 0,08h** | **155k / 160k** |

---

## Fase única — activación fiable

**Estado**: completado · **Estimado**: 7,5h · **Real**: 7,4h (estimado) · **Coste est.**: ≈390 € · **Tokens est.**: 160k

### T-01 — Suite de evals de comportamiento (`evals/`)

- **Descripción**: la `description` de cada pieza es una promesa de activación que hasta hoy no se probaba. Se crea `evals/` con **un fichero JSON por pieza** (`cases/<kind>-<nombre>.json`: 12 skills + 11 comandos + 8 agentes = 31 targets, 96 casos: 62 positivos —≥ 1 `trigger: literal` que contiene una frase de la description real y ≥ 1 `parafrasis`— y 34 negativos vecinos con `redirect` a la pieza que sí toca); `check.py` (estático, CI): esquema, nombre de fichero = target, cobertura de TODA pieza con ≥ 2 positivos + 1 negativo, ids únicos, el literal casa con la description REAL (cambiar la description rompe el caso), sin datos corporativos, `redirect` a pieza existente; `run.py` (local, cuesta tokens): `claude -p "<prompt>" --output-format stream-json --verbose --plugin-dir <plugin> --max-turns 8 --permission-mode acceptEdits` por caso sobre una copia de `fixtures/project/` (iniciativa `demo` inventada), detecta la activación por las tool uses `Skill`/`Agent` de la transcripción, evalúa `mentions`/`must_not`/`artifacts`, escribe `reports/<fecha>.json` (gitignored); `--dry-run`, `--target`, `--only`, exit 2 sin `claude`. Formato propio, documentado en `evals/README.md` (ES+EN) con la verificación de que no existe `claude plugin eval` y el mapeo 1:1 al formato de `skill-creator`. CI: paso `python evals/check.py` + `pytest … evals` en `ci.yml.MANUAL-COPY` y `.github/workflows/ci.yml` (idénticos).
- **Estado**: completado
- **Tiempo humano**: est. 3,0h · real 3,0h (estimado)
- **Tiempo IA (ejec.)**: est. 0,16h · real 0,16h (estimado)
- **Supervisión**: est. 0,03h · real 0,03h (estimado)
- **Archivos**: `evals/**`, `ci.yml.MANUAL-COPY`, `.github/workflows/ci.yml`, `.gitignore`

**Criterios de aceptación**
- [x] `python3 evals/check.py` → exit 0 con la línea `evals/check: 31 ficheros · 96 casos (62 positivos, 34 negativos) · 31 piezas del repo · 0 errores`; borrar cualquier `cases/*.json` o cambiar una `description` sin tocar su caso `literal` → exit 1 (tests `test_check_cobertura_pieza_sin_fichero`, `test_check_cambiar_la_description_rompe_el_caso_literal`).
- [x] `python3 evals/run.py --dry-run` imprime los 96 comandos `claude -p …` sin ejecutar nada; sin `claude` en PATH → exit 2 con aviso (`test_run_exit_2_sin_claude`); con el subprocess mockeado, informe JSON en `reports/` y exit 0/1 según casos (`test_run_con_subprocess_mockeado_informe_y_exit_codes`, `test_run_timeout_y_exit_distinto_de_0_fallan_el_caso`).
- [x] `python3 -m pytest -q evals` → 21 passed (19 funciones, 2 parametrizadas) sin lanzar `claude`; cada negativo con `redirect` apunta a una pieza distinta del target (`test_casos_reales_cada_negativo_con_redirect_apunta_a_pieza_distinta`).
- [x] `ci.yml.MANUAL-COPY` == `.github/workflows/ci.yml` (`tests/test_ci_manual_copy.py` verde; linter sin aviso «difieren») con el paso `Evals — validación estática` y `pytest … evals`; `evals/reports/` en `.gitignore`.
- [x] Sin datos corporativos en `cases/` (regla 6 de `check.py`: correos, `*.atlassian.net`, URLs externas, claves Jira reales → 0 hallazgos).

### T-02 — Índice de skills al arrancar (patrón `using-superpowers`)

- **Descripción**: `agent-kits/shared/skill-index.py` genera, DETERMINISTA desde los frontmatters (`commands/*.md` description+argument-hint, `skills/*/SKILL.md` name+description, `agents/*.md` name+description; nunca los cuerpos), un índice compacto: cabecera de 3 líneas con las reglas de enrutado («antes de cualquier tarea comprueba si aplica una pieza; si el usuario describe algo que casa con una skill, invócala en vez de improvisar; los comandos solo con `/`») + 3 bloques (Comandos / Skills / Agentes), **una línea por pieza ≤ 110 caracteres** (description recortada en la primera frase o en «Úsalo/Úsala cuando», con `…`), total **≤ 45 líneas / ≤ 3.500 caracteres** (constantes `LIMITE_LINEAS`/`LIMITE_CHARS`, afirmadas por test). Caché `${CLAUDE_PROJECT_DIR}/.claude/.skill-index.cache` (1.ª línea `# skill-index <sha256[:16] de los frontmatters>`): se regenera solo si el hash cambia o con `--no-cache`. Localización del plugin: `CLAUDE_PLUGIN_ROOT` → `dirname` del script → `find` (regla 5). `--json` opcional. **Exit 0 siempre**; sin piezas → sin salida; frontmatter roto → la pieza sale como `(sin description)` sin romper. `hooks/session-context.sh` añade el índice al `additionalContext` en SessionStart `startup|resume` **y también `compact`** (decisión: la doc oficial de hooks —verificada 2026-09-03— no dice que el `additionalContext` de un SessionStart previo sobreviva a la compactación; la línea de retoma del roadmap ya se reinyecta en `compact` por la misma razón; el coste es fijo y medido), respetando el tope de 10.000 caracteres del hook (índice ≤ 3.500 + bloque de sesión ≤ 15 líneas); desactivable con `.claude/dev.json` `"sesion": {"indice": false}`; sin `python3` → silencio. Doc ES+EN (`observability`, `FLOWS`, `CONVENTIONS` regla de hooks: el índice es informativo) + README/README.es (una frase) + `agent-kits/shared/README.md`.
- **Estado**: completado
- **Tiempo humano**: est. 2,0h · real 2,0h (estimado)
- **Tiempo IA (ejec.)**: est. 0,10h · real 0,10h (estimado)
- **Supervisión**: est. 0,02h · real 0,02h (estimado)
- **Archivos**: `skills/quick-implement/SKILL.md`, `agent-kits/shared/skill-index.py`, `agent-kits/shared/test_skill_index.py`, `hooks/session-context.sh`, `tests/test_hooks_shell.py`, `.gitignore`, `docs/observability.md`, `docs/en/observability.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `README.md`, `README.es.md`, `agent-kits/shared/README.md`

**Criterios de aceptación**
- [x] `python3 agent-kits/shared/skill-index.py` sobre el repo → 3 bloques (Comandos / Skills / Agentes) con 11 + 12 + 8 = 31 líneas de pieza, cada una ≤ 110 caracteres, total ≤ 45 líneas y ≤ 3.500 caracteres; dos ejecuciones → salida byte-idéntica (`test_determinista_y_estructura_sobre_el_repo_real`, `test_tope_de_tamano_sobre_el_repo_real`, `test_recorte_de_description_primera_frase_o_gatillo`). **Medido:** 37 líneas · 3.408 caracteres · ancho 110 · hash `0935371f41160814`.
- [x] Caché: 1.ª ejecución escribe `.claude/.skill-index.cache` con `# skill-index <hash>`; 2.ª con frontmatters iguales lee de caché (mismo texto); cambiar una `description` → hash distinto y regeneración; `--no-cache` ignora la caché (`test_cache_invalidada_por_cambio_de_frontmatter`).
- [x] Plugin sin piezas → exit 0 y stdout vacío; frontmatter roto (sin cierre `---`) → exit 0 y la pieza sale como `(sin description)`; `--json` → objeto con `lineas`, `texto`, `chars`, `n_lineas`, `hash`, `piezas` (`test_plugin_sin_piezas_exit_0_sin_salida`, `test_frontmatter_roto_no_rompe`, `test_json`); `.claude/dev.json` `{"sesion": {"indice": false}}` → sin salida (`test_dev_json_off_y_corrupto`). **11 tests** en `agent-kits/shared/test_skill_index.py` (11 passed).
- [x] `bash hooks/session-context.sh` con `{"source":"startup"}` → un único JSON `{"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "…"}}` que contiene el índice (`Comandos:`) y, si hay iniciativa activa, el bloque del roadmap; con `indice: false` → solo roadmap; sin roadmap activo y con índice → solo índice; `additionalContext` < 10.000 caracteres; exit 0 siempre (5 casos nuevos en `tests/test_hooks_shell.py`: `startup_indice_mas_roadmap_bajo_el_tope` —incluye `compact`—, `indice_false_solo_roadmap`, `sin_activas_solo_indice`, `sin_activas_e_indice_off_vacio`, `sin_python3_silencio`; suite 24 passed). **Medido sobre este repo:** `additionalContext` de 3.950 caracteres (índice 3.408 + roadmap).
- [x] Doc ES+EN actualizada (`docs/observability.md`, `docs/FLOWS.md`, `docs/CONVENTIONS.md` regla 8 + espejos `docs/en/`), una frase en `README.md`/`README.es.md`, fila `skill-index.py` en `agent-kits/shared/README.md`, `.claude/.skill-index.cache` en `.gitignore`; `dev.json` `sesion.indice` documentado en la regla 9 de CONVENTIONS.

### T-03 — Tablas de racionalización en los 3 puntos críticos (patrón «iron law»)

- **Descripción**: fragmento compartido `agent-kits/shared/rationalization-table.md` que fija el formato (tabla `| Excusa que el modelo se da | Por qué no vale | Qué hacer en su lugar |`) y las reglas: máximo 8 filas, excusas en primera persona y entrecomilladas, cada fila cierra con la acción concreta, la tabla va JUSTO ANTES del bloque DoD/veredicto de la pieza, ≤ 25 líneas, y sustituye la prosa equivalente (no la duplica). Se añade una tabla concreta (6-8 filas) en `agents/implementer.md` (antes de «ANTES DE CERRAR (DoD)»: completado sin correr tests, «lo probaré al final», tocar fuera de alcance, aplicar gaps sin verificar, «el ledger lo actualizo luego», tests vacíos para el TDD…), `skills/adversarial-review/SKILL.md` (excusas del REVISOR, antes de «6. Salida y traza»: «parece correcto», aprobar sin ejecutar, estilo como gap, no leer el diff completo, reabrir rebatidos, suavizar un Critical…) y `agents/qa.md` (antes de su DoD: verde con flaky, bajar el umbral, «el manual lo cubre», saltar `qa-gate.py`, cerrar estados en rojo…). Test `tests/test_rationalization_tables.py` que afirma cabecera exacta, 6-8 filas, posición antes del DoD/veredicto y el fragmento inventariado en `agent-kits/shared/README.md`.
- **Estado**: completado
- **Tiempo humano**: est. 1,5h · real 1,4h (estimado)
- **Tiempo IA (ejec.)**: est. 0,08h · real 0,07h (estimado)
- **Supervisión**: est. 0,02h · real 0,02h (estimado)
- **Archivos**: `agent-kits/shared/rationalization-table.md`, `agents/implementer.md`, `skills/adversarial-review/SKILL.md`, `agents/qa.md`, `tests/test_rationalization_tables.py`, `agent-kits/shared/README.md`

**Criterios de aceptación**
- [x] `agent-kits/shared/rationalization-table.md` existe, explica el formato y las 5 reglas (≤ 8 filas, primera persona, acción concreta al cierre, posición antes del DoD/veredicto, ≤ 25 líneas y sin duplicar prosa) y tiene fila en `agent-kits/shared/README.md`.
- [x] Los 3 ficheros (`agents/implementer.md`, `skills/adversarial-review/SKILL.md`, `agents/qa.md`) contienen la tabla con la cabecera EXACTA `| Excusa que el modelo se da | Por qué no vale | Qué hacer en su lugar |`, entre 6 y 8 filas, cada excusa entrecomillada en primera persona, y la tabla aparece ANTES del heading del DoD (`## ANTES DE CERRAR (DoD)`) o del veredicto (`### 6. Salida y traza`); cada tabla ≤ 25 líneas (`tests/test_rationalization_tables.py`, 6 tests, 6 passed; también ejecutable como script para el bucle de la CI). **Medido:** 8 filas en cada una de las 3 piezas; implementer 14 líneas, adversarial-review 14, qa 14 (título→última fila).
- [x] Prosa equivalente sustituida, no duplicada: la regla «Honesto con el estado» del implementer y el «no lo decides tú: lo decide el script» de qa quedan una sola vez (en la tabla o en la prosa, no en ambas); `python3 scripts/lint_plugin.py` sigue en 0 errores.

### T-04 — Doc y linter

- **Descripción**: `scripts/lint_plugin.py` gana dos avisos (nunca errores): (a) pieza (skill/comando/agente) sin ≥ 1 caso positivo en `evals/cases/` — reutiliza `piezas()`/`cargar_casos()` de `evals/check.py` importándolo por ruta (sin efectos secundarios); si el plugin no tiene `evals/cases/` (consumidor) no avisa; (b) `description` > 1.200 caracteres (token-diet del índice). `skills/plugin-dev/SKILL.md`: la checklist de pieza nueva incluye «≥ 1 caso positivo y 1 negativo en `evals/cases`» y «tabla de racionalización si la pieza tiene DoD o veredicto». Doc: fila `evals/` en `docs/README.md` + EN; `CLAUDE.md` (árbol con `evals/`, regla «Linter + tests» cita `evals/check.py`); lección `docs/knowledge/lessons/LES-011-plugin-dev-activacion-se-prueba-con-evals.md` (`estado: propuesta`, formato de LES-010) + fila en `docs/knowledge/README.md`; fila de la iniciativa en `docs/roadmap/README.md`.
- **Estado**: completado
- **Tiempo humano**: est. 1,0h · real 1,0h (estimado)
- **Tiempo IA (ejec.)**: est. 0,06h · real 0,06h (estimado)
- **Supervisión**: est. 0,01h · real 0,01h (estimado)
- **Archivos**: `scripts/lint_plugin.py`, `tests/test_lint_plugin.py`, `skills/plugin-dev/SKILL.md`, `docs/README.md`, `docs/en/README.md`, `CLAUDE.md`, `docs/knowledge/lessons/LES-011-plugin-dev-activacion-se-prueba-con-evals.md`, `docs/knowledge/README.md`, `docs/roadmap/README.md`

**Criterios de aceptación**
- [x] `tests/test_lint_plugin.py`: plugin sintético con `evals/cases/` donde una pieza no tiene caso positivo → aviso `sin caso positivo en evals/cases` y exit 0; con caso positivo → sin aviso; sin carpeta `evals/cases/` → sin aviso; `description` de 1.300 caracteres → aviso `description de 1300 caracteres (> 1200)`; de 500 → sin aviso (casos 19 y 20; `test_lint_plugin: 20/20 OK`). Sin `evals/check.py` el linter degrada a un lector local de frontmatters para (b) y omite (a).
- [x] `python3 scripts/lint_plugin.py` sobre el repo → 0 errores; avisos = los 3 previos (nombres genéricos `retro`/`roadmap-status`/`setup`) + los legítimos de description > 1.200 caracteres, listados en el cierre. **Medido:** `lint_plugin: 8 agentes · 0 errores · 3 avisos` — ninguna description supera 1.200 caracteres (la mayor: `skill:adversarial-review`, 919) y las 31 piezas tienen positivo en `evals/cases/` → 0 avisos nuevos.
- [x] `skills/plugin-dev/SKILL.md` contiene los dos ítems nuevos de la checklist (evals y tabla de racionalización); `docs/README.md` y `docs/en/README.md` tienen fila `evals/`; `CLAUDE.md` muestra `evals/` en el árbol y cita `evals/check.py` en «Linter + tests».
- [x] `LES-011-plugin-dev-activacion-se-prueba-con-evals.md` existe con el frontmatter de las lecciones (`id`, `tipo: leccion`, `area`, `estado: propuesta`, `fuente`), enlazada desde `docs/knowledge/README.md`; `docs/roadmap/README.md` tiene la fila de `2026-09-03 activation-reliability`.

---

## Revisión de dos lentes — intento 1: 0 Critical · 2 Important · 3 Minor (lentes A+B; todos verificados y corregidos en `T-fix1`)

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | `skill-index.py` `leer_cache` solo capturaba `OSError`: caché con bytes no UTF-8 → `UnicodeDecodeError` al `except` de `main` → stdout vacío, exit 0 y la caché corrupta NO se sobreescribía → el índice desaparecía de todas las sesiones en silencio | T-02 | **Reproducido** (`printf 'garbage\x00\xff'` → 0 bytes de salida, caché intacta). `leer_cache` captura `(OSError, UnicodeDecodeError, ValueError)` → `(None, None)` → regenera y sobrescribe; cuerpo vacío con hash correcto también regenera | `test_cache_corrupta_no_utf8_se_regenera_y_sobrescribe` (13 tests en la suite) |
| 2 | Important | Contradicción: cabecera del índice y `docs/CONVENTIONS.md` regla 8 (+EN) decían «los comandos SOLO se disparan con `/`», pero los 11 `evals/cases/command-*.json` tienen 22 positivos en lenguaje natural (0 empiezan por `/`) y `run.py` los detecta vía tool `Skill` | T-02 | **Verificado** (22/22 positivos de comandos sin barra). Decisión: los comandos se invocan por `/` o por descripción, como las skills (Claude Code los trata como skills salvo `disable-model-invocation`). Cabecera reescrita (`VERSION` de la caché → 2), CONVENTIONS ES+EN, y la fila de `quick-implement` en `docs/README.md` + EN aclara que la razón «solo con la barra» es histórica. `check.py` no asume nada sobre `/` (solo frases de la description) | `evals/check.py` exit 0 · `test_determinista_y_estructura_sobre_el_repo_real` |
| 3 | Minor | `LIMITE_LINEAS = 45` no se aplicaba en `construir` (60 skills → 64 líneas) | T-02 | `_cupos()`: presupuesto = 45 − cabecera − títulos; cada grupo cede proporcionalmente (floor, determinista) y cierra con «… y N piezas más (ver `<carpeta>/`)» | `test_limite_de_lineas_recorta_grupos_proporcionalmente` (60+11+8 piezas → 43 líneas, visibles + «N más» = 60) |
| 4 | Minor | `agents/qa.md`: «el veredicto lo da qa-gate» repetido 3 veces en 15 líneas (intro de la tabla, fila, heading del DoD) | T-03 | Quitada la repetición de la intro; queda la fila de la tabla y el heading del DoD | `test_prosa_equivalente_no_duplicada` (afirma `NO lo decides tú` ausente y «el veredicto lo da qa-gate» ×1) |
| 5 | Minor | `evals/run.py`: `--permission-mode acceptEdits` sin `--allowedTools` → en `-p` nadie aprueba Bash; casos con `expect.artifacts` que dependan de scripts fallarían por permisos, no por activación | T-01 | `--allowed-tools` (default `Bash(python3:*),Bash(git:*),Bash(find:*)`, pasado tal cual a `--allowedTools`; `""` → no se pasa) documentado en `evals/README.md` ES+EN y docstring; `parsear_stream` recoge los `tool_result` `is_error` cuyo texto habla de permisos y cada fallo lleva `causa`: `no activó` · `activó sin deber` · `permiso denegado` · `expectativa` · `timeout` (consola + informe, con contador `permisos_denegados`) | `test_run_permiso_denegado_se_distingue_de_no_activo`, `test_run_dry_run_imprime_comandos_sin_ejecutar` (default, `""`, valor propio) |

**Rebatidos:** ninguno. **Deuda aceptada:** `skills/quick-implement/SKILL.md` línea 8 conserva la justificación histórica «los commands solo se disparan si el usuario escribe la barra» — fuera del alcance de esta iniciativa (no está en ningún `Archivos`); se propone aclararla en la próxima retoque de la skill, igual que se hizo en `docs/README.md`.

**Verificación tras `T-fix1`:** `pytest -q tests agent-kits/shared skills/adversarial-review/scripts evals` → 229 passed · suites-script de `tests/` OK · `lint_plugin` 0 errores · 3 avisos (los previos) · `evals/check.py` exit 0 · `scope-check --base 4991637` exit 0 (0 fuera de alcance) · índice 37 líneas / 3.411 chars.

**Deuda saldada por el orquestador (mismo cierre):** `skills/quick-implement/SKILL.md:8` reescrito — la razón de ser de la skill pasa de «los commands solo se disparan con la barra» (ya falso) a «razón histórica + filtro de idoneidad en lenguaje natural medido por sus evals». Añadido a `Archivos` de T-02 por extensión. 0 deudas pendientes.

## Revisión de dos lentes — intento 2: sin gaps (re-verificación del orquestador: caché corrupta regenerada y sobrescrita, cabecera del índice coherente con los evals, 229 tests). LES-011 promovida a `aceptada (validada: revisión de dos lentes, 2026-09-03, intento 2)`.
