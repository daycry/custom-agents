---
generacion:
  inicio: 2026-08-20T08:57:27Z
  fin: 2026-08-20T08:59:24Z
  fuente: estimado        # ventana compartida con improvement-plan.md — degradación: sin carpeta de transcripciones en este sandbox
  tokens_reales: no-medido (sandbox)
  eur: null
  horas_ia: null
  duracion: no-medido (sandbox)
  ratio_usado: 479326
---

# Checklist de Tareas — Política de publicación en Confluence

| | |
|---|---|
| **Estado** | completado |
| **Fecha** | 2026-08-20 |
| **Plan** | [`improvement-plan.md`](./improvement-plan.md) |

> **Disciplina de desarrollo (P1-bis):** `.claude/dev.json` no existe en este entorno → disciplina clásica (sin TDD obligatorio, sin worktree, sin subagentes por tarea). El plan sí exige tests para el script nuevo (T-09): se escriben igualmente, por criterio de aceptación, no por config de TDD. `usage-meter.py` no puede medir en este sandbox: los tiempos reales quedan `(estimado)`, nunca `(medido)`. `.claude/jira.json`/`.claude/confluence.json` no existen (sin opt-in): no hay volcado a Jira ni sincronización con Confluence durante esta implementación — constatado una vez, no se repite por tarea.

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del plan. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador SDD externo— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — Alcance del mirror + evidencias de qa | 3 | 3 | 100% | 0,65 (estimado) / 4,5h | 0,10 (estimado) / 0,11h | 0,025 (estimado) / 0,05h | n/d (sandbox) / 55k |
| Fase 2 — Disparadores que faltan | 2 | 2 | 100% | 0,8 (estimado) / 3,0h | 0,08 (estimado) / 0,08h | 0,02 (estimado) / 0,02h | n/d (sandbox) / 35k |
| Fase 3 — Verificador + staging generado | 5 | 5 | 100% | 3,2 (estimado) / 7,5h | 0,26 (estimado) / 0,21h | 0,07 (estimado) / 0,06h | n/d (sandbox) / 100k |
| Fase 4 — Documentar la política | 3 | 3 | 100% | 1,6 (estimado) / 3,0h | 0,13 (estimado) / 0,09h | 0,03 (estimado) / 0,03h | n/d (sandbox) / 45k |
| **TOTAL** | **13** | **13** | **100%** | **6,25 / 18,0h** | **0,57 / 0,49h** | **0,145 / 0,16h** | **n/d / 235k** |

> **Horas → Jira.** El worklog que imputa `jira-sync` al completar cada tarea es Tiempo IA (ejec.) + Supervisión (real; o estimación si no hay real), topado a la jornada configurada. Ver `skills/jira-sync/SKILL.md`. **Nota:** las horas IA/supervisión de esta tabla son solo el trabajo por característica (heredado de `evaluation.md`); las líneas transversales de revisión adversarial y coste de proceso viven en `improvement-plan.md` §Presupuesto económico, no en tareas individuales.

---

## Fase 1 — Alcance del mirror + evidencias de qa (C-01 + C-03)

**Estado**: completado · **Estimado**: 4,5h · **Real**: 0,65h humanas (estimado) · **Coste est.**: ≈225 € · **Tokens est.**: 55k

> **Verificación de fase (P5):** `python3 scripts/lint_plugin.py` → 0 errores (3 avisos preexistentes de nombres genéricos, no relacionados). Sin suite propia todavía (llega en Fase 3, T-09); las suites existentes (`tests/test_*.py`) no se han tocado por esta fase. Sincronización Confluence: no aplica — sin `.claude/dev.json` no hay disparo por fase de `implementer` en este propio repo de desarrollo del plugin (constatado una vez, ver nota P1-bis arriba); en un proyecto consumidor con Confluence activo, aquí se dispararía el paso opt-in al cierre de esta fase (D3).

### T-01 — Definir el `exclude` por defecto de la política (D1) en la config de ejemplo

- **Descripción**: Sustituir el `exclude` actual (`["**/node_modules/**", "docs/security-scan/**"]`) de `skills/confluence-publish/assets/confluence.example.json` por el aprobado en la spec, con un comentario que explique cada exclusión. Es la lista que consumirán después el verificador (Fase 3) y la documentación (Fase 4).
- **Estado**: completado
- **Tiempo humano**: est. 3h · real 0,3h (estimado)
- **Tiempo IA (ejec.)**: est. 0,06h · real 0,05h (estimado — usage-meter.py no disponible en este sandbox)
- **Supervisión**: est. 0,02h (≈25 % IA) · real 0,01h (estimado)
- **Previsión IA**: 26k in / 4k out tok · 0,21 €
- **Dependencias**: ninguna
- **Tipo**: docs
- **Archivos**: `skills/confluence-publish/assets/confluence.example.json`, `skills/confluence-publish/SKILL.md` (§Config, tabla de `publish`)
- **Cubre (tests)**: — (no aplica, sin UI)

**Criterios de aceptación**
- [x] CA-01 — `confluence.example.json` tiene `exclude: ["**/node_modules/**", "docs/security-scan/**", "docs/en/**", "docs/examples/**", "docs/agents/**", "docs/**/atlassian-connector-notes.md", "docs/roadmap/**/improvement-plan.md", "docs/roadmap/**/tasks.md", "docs/roadmap/**/test-plan.md", "**/testing/**"]` y un `_comment_exclude` (o comentarios por línea) que explica cada patrón.
- [x] CA-06 (parcial) — `docs/security-scan/**` sigue en el `exclude` tras el cambio (verificable por `grep -n "security-scan" skills/confluence-publish/assets/confluence.example.json`).
- [x] `SKILL.md` §Config referencia la lista actualizada (no queda desincronizada con el JSON de ejemplo).

**Subtareas**
- [x] Editar `confluence.example.json`: nuevo array `exclude` + comentario justificativo.
- [x] Actualizar la tabla de `publish` en `SKILL.md` §Config para que cite los mismos valores.
- [x] `python3 -c "import json; json.load(open('skills/confluence-publish/assets/confluence.example.json'))"` para confirmar que el JSON sigue siendo válido (los `_comment*` son claves, no comentarios reales).

**Notas**: no toca aún `source`/`staging` (eso es D5, Fase 3/T-10) — solo el `exclude` de D1/D4.

<!-- ==================================================================== -->

### T-02 — Simetría del filtro en `confluence-pull`

- **Descripción**: Declarar en `skills/confluence-pull/SKILL.md` que el pull respeta el mismo `include`/`exclude` de `confluence.json` que `confluence-publish` (spec §Arquitectura, fila "Skill de bajada"): una página cuyo fichero local cae fuera del alcance no se trae ni se recrea.
- **Estado**: completado
- **Tiempo humano**: est. 1h · real 0,15h (estimado)
- **Tiempo IA (ejec.)**: est. 0,02h · real 0,02h (estimado)
- **Supervisión**: est. 0,01h (≈25 % IA) · real 0,005h (estimado)
- **Previsión IA**: 9k in / 1k out tok · 0,06 €
- **Dependencias**: T-01
- **Tipo**: docs
- **Archivos**: `skills/confluence-pull/SKILL.md` (§Paso 1 — construir el conjunto remoto)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] `confluence-pull/SKILL.md` declara explícitamente que aplica el mismo `include`/`exclude` que `confluence-publish` antes de mapear páginas a ficheros locales.
- [x] Queda anotado que una página remota fuera del alcance actual se trata como "no gestionada por el circuito" (no se recrea localmente sin más).

**Subtareas**
- [x] Añadir el párrafo de simetría en §Paso 1.
- [x] Referenciar `confluence.example.json` como fuente del `exclude` vigente (evita duplicar la lista en dos ficheros).

**Notas**: prerequisito conceptual de T-10 (mapeo inverso staged→canónico), que amplía esta misma sección.

---

### T-03 — Evidencias binarias de qa: informe `testing/` solo-local (D4)

- **Descripción**: Ajustar `agents/qa.md` para que P7 declare explícitamente que el informe de `docs/roadmap/<slug>/testing/` es **solo-local** (queda fuera del espejo por la exclusión `**/testing/**` de T-01) y ya no ofrece sincronizarlo con Confluence. Actualizar también la dependencia declarada del frontmatter de `qa.md` sobre `confluence-publish`.
- **Estado**: completado
- **Tiempo humano**: est. 0,5h · real 0,2h (estimado)
- **Tiempo IA (ejec.)**: est. 0,03h · real 0,03h (estimado)
- **Supervisión**: est. 0,01h (≈25 % IA) · real 0,01h (estimado)
- **Previsión IA**: 13k in / 2k out tok · 0,11 €
- **Dependencias**: T-01
- **Tipo**: docs
- **Archivos**: `agents/qa.md` (frontmatter `dependencies`, P7 L~77, notas L26/L73)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] CA-04 (parcial: qa) — `agents/qa.md` declara en una frase que el informe de `testing/` (con `report.pdf`, `screenshots/`, `raw/`) es **solo-local** por decisión D4, y que P7 ya no dispara sincronización sobre esa carpeta.
- [x] El frontmatter de `agents/qa.md` deja de listar `confluence-publish` como dependencia si P7 deja de invocarla para `testing/` (o el comentario de esa dependencia se corrige para no prometer algo que ya no ocurre).
- [x] CA-06 no se rompe: ningún texto de `qa.md` sugiere excepcionar `**/testing/**` de la exclusión.

**Subtareas**
- [x] Reescribir P7 de `agents/qa.md`.
- [x] Revisar y ajustar el comentario de `dependencies.skills` en el frontmatter.
- [x] Grep de `docs/README.md` para detectar si su fila de `qa` ("Sincroniza el informe en Confluence") queda desactualizada — dejar nota para T-13 (no se corrige aquí, se corrige en Fase 4).

**Notas**: el `exclude` de `**/testing/**` en sí ya lo aporta T-01; esta tarea es solo la declaración en `qa.md`.

---

## Fase 2 — Disparadores que faltan (C-02)

**Estado**: completado · **Estimado**: 3,0h · **Real**: 0,8h humanas (estimado) · **Coste est.**: ≈150 € · **Tokens est.**: 35k

> **Verificación de fase (P5):** `python3 scripts/lint_plugin.py` → 0 errores (mismos 3 avisos preexistentes). Sin cambios en suites de `tests/`. Sincronización Confluence (P5-bis, D3): no aplica en este repo (sin `.claude/confluence.json`; es el propio repo del plugin, no un proyecto consumidor) — constatado, no bloquea.

### T-04 — Opt-in de Confluence en los comandos de fin de ciclo

- **Descripción**: Añadir el paso compartido `confluence-optin.md` al cierre de `commands/retro.md`, `commands/spec-drift.md` y `commands/roadmap-brief.md`, con el mismo texto de degradación que usan `evaluator`/`planner`/`qa`/`documenter`. Cierra el hueco por el que `retro.md`, `CALIBRATION.md`, `DRIFT.md` y `brief.md` nunca se sincronizaban (nadie publica después de ellos).
- **Estado**: completado
- **Tiempo humano**: est. 1,5h · real 0,4h (estimado)
- **Tiempo IA (ejec.)**: est. 0,04h · real 0,04h (estimado)
- **Supervisión**: est. 0,01h (≈25 % IA) · real 0,01h (estimado)
- **Previsión IA**: 16k in / 2k out tok · 0,12 €
- **Dependencias**: ninguna
- **Tipo**: docs
- **Archivos**: `commands/retro.md`, `commands/spec-drift.md`, `commands/roadmap-brief.md`
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] CA-03 — Los tres comandos aplican `confluence-optin.md` como último paso de su cierre, citando `SHAREDKIT="$(find "$PWD/.claude" "$HOME/.claude" -type d -path '*agent-kits/shared' 2>/dev/null | head -1)"` igual que el resto de la cadena.
- [x] El texto de degradación (nunca bloquea, respeta `enabled: false`) es literalmente el mismo en los tres comandos (copia del fragmento, no una paráfrasis distinta cada vez).

**Subtareas**
- [x] `commands/retro.md`: añadir el paso al final (tras escribir `retro.md` + `CALIBRATION.md`).
- [x] `commands/spec-drift.md`: añadir el paso al final (tras escribir `DRIFT.md`).
- [x] `commands/roadmap-brief.md`: añadir el paso al final (tras generar `brief.md`/`brief.pdf`).

**Notas**: `brief.pdf`/`report.pdf` no son `.md`: no entran en el espejo aunque el paso opt-in se dispare; no hace falta excluirlos aparte.

<!-- ==================================================================== -->

### T-05 — Ledger por fase en `implementer` (D3)

- **Descripción**: `agents/implementer.md` debe aplicar el paso opt-in de Confluence **al cerrar cada fase** (ni tarea a tarea, ni solo al final), en su P5 ("Verificación de fase") o inmediatamente después. Añadir también la nota de interacción D1↔D3: el disparo refresca lo que haya cambiado en el alcance, pero `tasks.md` en sí **no** sube (D1 lo deja fuera del espejo).
- **Estado**: completado
- **Tiempo humano**: est. 1,5h · real 0,4h (estimado)
- **Tiempo IA (ejec.)**: est. 0,04h · real 0,04h (estimado)
- **Supervisión**: est. 0,01h (≈25 % IA) · real 0,01h (estimado)
- **Previsión IA**: 15k in / 2k out tok · 0,12 €
- **Dependencias**: T-01 (para citar el alcance final con propiedad)
- **Tipo**: docs
- **Archivos**: `agents/implementer.md` (P5 "Verificación de fase", frontmatter `dependencies`)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] CA-04 (parcial: implementer) — `agents/implementer.md` declara literalmente que aplica `confluence-optin.md` **al cerrar cada fase**, no antes ni solo al final.
- [x] La misma sección incluye la advertencia: "el ledger `tasks.md` no está en el espejo por defecto (D1); este disparo refresca el resto de lo que haya cambiado bajo `docs/`".
- [x] El frontmatter `dependencies.skills` de `implementer.md` incluye `confluence-publish` (si no estaba ya) con un comentario que explique el disparo por fase.

**Subtareas**
- [x] Añadir el paso opt-in al final de P5 en `agents/implementer.md`.
- [x] Redactar la nota D1↔D3 (una frase, sin ambigüedad).
- [x] Revisar el frontmatter `dependencies` del agente.

**Notas**: esta es la parte "no mecánica" de C-02 (a diferencia de T-04, que es la misma línea repetida tres veces) — requiere la frase de interacción D1↔D3 para no desconcertar a quien espere ver el ledger publicado.

---

## Fase 3 — Verificador + staging generado (C-05)

**Estado**: completado · **Estimado**: 7,5h · **Real**: 3,2h humanas (estimado) · **Coste est.**: ≈375 € · **Tokens est.**: 100k

> **Verificación de fase (P5):** `python3 scripts/lint_plugin.py` → 0 errores. `python3 tests/test_confluence_scope.py` → 16/16 OK (incluye T-09 + el caso del hook de T-10). Bucle completo `for t in tests/test_*.py` → todas las suites en verde (8 ficheros). Sincronización Confluence (P5-bis, D3): no aplica en este repo (sin `.claude/confluence.json`).
>
> **Ronda de corrección post-revisión adversarial (T-06/T-07/T-08/T-09 reabiertas → cerradas de nuevo).** La revisión de dos lentes (intento 1/3) reprodujo 8 huecos en `confluence-scope.py` y su suite: 3 críticos (C1 — el marcador de staging pisaba `docs/README.md`; C2 — `--stage` podía `rmtree` un `--out` ajeno sin comprobarlo; I1 — el fixture `tests/fixtures/confluence-scope/docs/security-scan/finding.md` no estaba trackeado por `.gitignore`), 3 importantes (I2 — la autoexclusión del staging estaba cableada al literal `docs/confluence/**` en vez de derivarse del `--out` real; I3 — `--config` explícito roto degradaba en silencio a defaults; I4 — `--map ""` salía 0 sin salida) y 2 menores (M1 — `ValueError` sin capturar en el mapeo inverso; M2 — la fecha en el marcador rompía la idempotencia byte a byte entre días). Las tareas T-06 a T-09 (comparten el mismo fichero y su suite) volvieron a `en-progreso` mientras se corregían los 8 puntos, cada uno con test de regresión, y vuelven a `completado` con la evidencia siguiente:
> ```
> $ python3 tests/test_confluence_scope.py
> test_confluence_scope: 23/23 OK
>
> $ for t in tests/test_*.py; do python3 "$t" || exit 1; done   # las 9 suites, sin excepción
> (verde, ver detalle en el cierre de Fase 4 más abajo)
>
> $ python3 scripts/lint_plugin.py
> lint_plugin: 8 agentes · 0 errores · 3 avisos (preexistentes, no relacionados)
>
> $ SHAREDKIT="$(find "$PWD/.claude" "$HOME/.claude" -type d -path '*agent-kits/shared' 2>/dev/null | head -1)"
> $ python3 agent-kits/shared/ledger-lint.py docs/roadmap/2026-08-20-confluence-policy/tasks.md
> ledger-lint: 0 incoherencias · 0 avisos (tasks.md)
> ```
> 8 commits `T-XX-fix: ...` (uno por hueco o grupo coherente), más este de cierre del ledger. `docs/roadmap/README.md` no se toca (lo refresca `/roadmap-status`, regla del propio `implementer`); la ausencia de `docs/confluence/` en este propio repo del plugin es correcta (no es un proyecto consumidor con `.claude/confluence.json` activo) y queda anotada aquí, no "corregida".

### T-06 — `confluence-scope.py --check` (invariantes)

- **Descripción**: Primera pieza del script nuevo `skills/confluence-publish/scripts/confluence-scope.py`: subcomando `--check` que lee `.claude/confluence.json` (o el `exclude` por defecto de `confluence.example.json` si no hay config de proyecto) y falla con exit ≠ 0 y un mensaje que **nombra la invariante violada** si `docs/security-scan/**` no está en `exclude`. Es la base sobre la que se apoyan `--status` y `--stage`.
- **Estado**: completado
- **Tiempo humano**: est. 1h · real 0,4h (estimado)
- **Tiempo IA (ejec.)**: est. 0,03h · real 0,15h (estimado — script completo escrito en una pasada junto con T-07/T-08)
- **Supervisión**: est. 0,01h (≈25 % IA) · real 0,04h (estimado)
- **Previsión IA**: 11k in / 2k out tok · 0,10 €
- **Dependencias**: T-01
- **Tipo**: backend
- **Archivos**: `skills/confluence-publish/scripts/confluence-scope.py` (nuevo)
- **Cubre (tests)**: — (ver T-09, CA-08)

**Criterios de aceptación**
- [x] [GWT] CA-08 — Con un `confluence.json` cuyo `exclude` omite `docs/security-scan/**`, `python3 confluence-scope.py --check` termina con exit code ≠ 0 y un mensaje que menciona literalmente `docs/security-scan`.
- [x] Con la política aprobada (T-01) intacta, `--check` termina en exit 0.
- [x] El script sigue el patrón del repo: rutas relativas (`dirname "$BASH_SOURCE"`-equivalente en Python: `Path(__file__).resolve().parent`), `def main()` + `sys.exit(code)`.

**Subtareas**
- [x] Esqueleto del script: parseo de argumentos (`--check`/`--status`/`--stage`/`--map`), resolución de config con `find`-equivalente en Python (`load_policy`, degrada a `assets/confluence.example.json` si no hay `.claude/confluence.json`).
- [x] Función `check_invariants(publish) -> list[str]` (lista de violaciones; vacía = ok) — usa un fichero-sonda `docs/security-scan/__confluence_scope_probe__.md` para no depender de que exista contenido real bajo esa carpeta.
- [x] CLI: exit 0 si no hay violaciones, exit 1 + mensajes si las hay. Verificado manualmente con config rota (exit 1, menciona `docs/security-scan`) y config por defecto (exit 0).

**Decisión sobre la marcha:** las tres funciones (`--check`, `--status`, `--stage` + `--map`) comparten la misma implementación de glob (`glob_to_regex`, semántica de `glob.glob(..., recursive=True)` para `**`) — se escribió el fichero completo en una sola pasada (T-06/T-07/T-08) en vez de tres incrementos separados, porque las tres reutilizan `load_policy`/`resolve_scope` y separarlas habría significado reescribir el mismo fichero tres veces. El reparto de horas por tarea es un prorrateo, no una medición por subcomando.

**Notas**: dejar la función de resolución de config/alcance reutilizable para T-07 y T-08 (no reimplementar el cruce de globs tres veces).

**Ronda de corrección (gap I3, revisión adversarial):** `--config` explícito a un fichero inexistente o con JSON corrupto degradaba en silencio a los defaults del paquete — `--check` podía reportar "OK" contra una política que nadie llegó a validar. Fix: `ConfigError` se levanta solo cuando `--config` se pasa explícito y es inválido; sin `--config`, la degradación a defaults se mantiene igual. Commit `8923257` — tests `test_check_explicit_missing_config_is_an_error`, `test_check_explicit_corrupt_config_is_an_error`.

<!-- ==================================================================== -->

### T-07 — `confluence-scope.py --status`

- **Descripción**: Subcomando `--status`: recorre `docs/` aplicando `include`/`exclude`, cruza con `.claude/confluence-state.json` (si existe) y clasifica cada documento en **en alcance / sincronizado / desactualizado o pendiente / excluido**. Salida legible + exit 0 si el análisis se completó (el estado de los ficheros no afecta al exit code; para eso está `--check`).
- **Estado**: completado
- **Tiempo humano**: est. 2h · real 0,7h (estimado)
- **Tiempo IA (ejec.)**: est. 0,06h · real incluida en T-06 (misma pasada del script)
- **Supervisión**: est. 0,01h (≈25 % IA) · real incluida en T-06
- **Previsión IA**: 23k in / 4k out tok · 0,20 €
- **Dependencias**: T-06
- **Tipo**: backend
- **Archivos**: `skills/confluence-publish/scripts/confluence-scope.py`
- **Cubre (tests)**: — (ver T-09, CA-07)

**Criterios de aceptación**
- [x] [GWT] CA-07 — Sobre este repositorio con la política por defecto, `--status` clasifica cada documento en las 4 categorías, lista `docs/en/**`, `docs/examples/**`, `docs/agents/**`, `**/testing/**` y `docs/security-scan/**` entre los **excluidos**, no lista ningún fichero fuera de `docs/`, y termina con exit 0. Verificado manualmente: `--status` imprime la sección "Patrones de exclusión activos" (siempre lista los 5 patrones, aunque `security-scan`/`testing` no tengan ficheros reales en este repo hoy) y luego cada `.md` real de `docs/agents/`, `docs/en/`, `docs/examples/` bajo "Excluidos"; exit 0.
- [x] Un fichero sin entrada en `confluence-state.json` se clasifica como "pendiente" (nunca publicado); uno con hash distinto al manifiesto, como "desactualizado"; uno con hash igual, como "sincronizado".
- [x] Si `confluence-state.json` no existe, `--status` sigue funcionando (todo lo que esté en alcance sale como "pendiente"), sin fallar.

**Subtareas**
- [x] Función `resolve_scope(root, publish, docs_dirname) -> (en_alcance, excluidos)` (glob real vía `glob_to_regex`, no aproximado).
- [x] Función `classify_sync(en_alcance, root, manifest) -> dict[rel, categoria]`.
- [x] Formato de salida humano (listado por categoría) + resumen numérico al final.

**Notas**: reutiliza `resolve_scope` de T-06/T-08 — es la misma semántica de glob en las tres funciones (riesgo transversal señalado en `evaluation.md`).

**Ronda de corrección (gap I2, revisión adversarial):** la autoexclusión de la carpeta de salida estaba cableada al literal `docs/confluence/**`, ignorando `--out`/`--docs`: con un `--out` no default, la segunda ejecución de `--stage` intentaba recopiar ficheros que la primera acababa de borrar y crasheaba con `FileNotFoundError`. Fix: `resolve_out_dir()`/`always_exclude_for()` derivan la exclusión del `out_dir` efectivo, usadas en `resolve_scope` y `cmd_status`. Commit `3a778b8` — test `test_stage_custom_out_survives_repeated_runs`.

<!-- ==================================================================== -->

### T-08 — `confluence-scope.py --stage` + mapeo inverso

- **Descripción**: Subcomando `--stage`: regenera `docs/confluence/` desde cero (copia byte a byte de los ficheros en alcance) + un fichero de aviso de "no editar" con el comando que lo produjo (nombre reservado `_STAGING-LEEME.md` tras la ronda de corrección — ver abajo). Debe ser **idempotente** (dos ejecuciones seguidas sin cambios dan el mismo árbol) y exponer el mapeo inverso `staged → canónico` (p. ej. `--stage --map` o una función/JSON auxiliar) para que `confluence-pull` lo consuma en T-10.
- **Estado**: completado
- **Tiempo humano**: est. 2,5h · real 0,9h (estimado)
- **Tiempo IA (ejec.)**: est. 0,07h · real incluida en T-06 (misma pasada del script)
- **Supervisión**: est. 0,02h (≈25 % IA) · real incluida en T-06
- **Previsión IA**: 28k in / 5k out tok · 0,24 €
- **Dependencias**: T-06, T-07
- **Tipo**: backend
- **Archivos**: `skills/confluence-publish/scripts/confluence-scope.py`, `docs/confluence/` (carpeta de salida, generada — no crear a mano)
- **Cubre (tests)**: — (ver T-09, CA-10/CA-11)

**Criterios de aceptación**
- [x] [GWT] CA-10 — `--stage` sobre un repo sin `docs/confluence/` crea la carpeta con **exactamente** los ficheros en alcance (mismo contenido byte a byte que sus canónicos, incluido `docs/README.md`) + el marcador `_STAGING-LEEME.md` generado; ejecutado una segunda vez sin cambios, el resultado es **idéntico** (idempotente); ningún fichero excluido aparece dentro. Verificado con la suite (`test_stage_creates_exact_scope_and_marker`, `test_stage_copies_readme_byte_for_byte`, `test_stage_is_idempotent`).
- [x] El script borra por completo el contenido previo de `docs/confluence/` antes de regenerar (`shutil.rmtree` + recreación) — no deja residuos de una ejecución anterior con distinto alcance, y **solo si es reconocible como staging propio** (ver gap C2 abajo): un `--out` ajeno con contenido real se rehúsa sin tocarlo.
- [x] Expone el mapeo inverso `staged → canónico` de forma programática: función pura `staged_to_canonical(staged_path, root, docs_dirname, out_dir)` + subcomando `--map` — no requiere haber corrido `--stage` antes (aritmética de rutas, 1:1 salvo el prefijo). T-10 la consume sin reimplementar la lógica.
- [x] `docs/confluence/**` se excluye de sí misma en el `exclude` efectivo: `ALWAYS_EXCLUDE = ["docs/confluence/**"]` se añade SIEMPRE en `resolve_scope`, con independencia de la config del proyecto, y la autoexclusión EFECTIVA se deriva del `--out`/`--docs` reales (`always_exclude_for`, gap I2 abajo) — no depende de que el usuario no borre la línea de config ni de que use el `--out` por defecto.

**Subtareas**
- [x] Función `stage(root, scope, out_dir)` (implementada como `cmd_stage`): limpia `out_dir`, copia ficheros, preserva estructura de carpetas.
- [x] Generar el marcador de staging con plantilla de aviso (comando que lo produjo; sin fecha tras gap M2, ver abajo).
- [x] Función/flag que emite el mapeo inverso (`staged_to_canonical` + `--map`) como función importable.
- [x] Prueba manual de idempotencia (dos `--stage` seguidos, diff vacío) antes de pasar a T-09 — automatizada en `test_stage_is_idempotent`.

**Notas**: es la pieza de mayor riesgo del lote (evaluación: "generador de árbol" + "cambia el contrato de tres piezas existentes"). Si hay que recortar alcance por tiempo, se recorta variedad de casos de glob en T-09, nunca esta tarea ni CA-10/CA-11.

**Ronda de corrección (revisión adversarial, intento 1/3) — T-08 reabierta → cerrada de nuevo con evidencia:**
- **[C1] CRÍTICO** — `--stage` copiaba `docs/README.md` al staging y LUEGO lo pisaba con la plantilla de aviso (el README staged pasaba a ser boilerplate; `--map docs/confluence/README.md` devolvía `docs/README.md` con exit 0, así que un pull habría sobrescrito el canónico). Fix: aviso movido a un nombre reservado `_STAGING-LEEME.md` (excluido del alcance en cualquier carpeta), copia del README real garantizada byte a byte + `assert` defensivo en `cmd_stage`. Commit `b9c342a`.
- **[C2] CRÍTICO** — `shutil.rmtree(out_dir)` sin salvaguarda: un `--out` mal configurado (p. ej. `docs/` real) se borraba sin más. Fix: `assert_safe_stage_target()` rehúsa borrar salvo que el destino no exista, esté vacío o sea un staging reconocible (contenga el marcador). Commit `2e73522`.
- **[I2] IMPORTANTE** — ver nota en T-07 (misma función `resolve_scope`/`cmd_stage`). Commit `3a778b8`.
- **[I4] IMPORTANTE** — `--map ""` salía 0 sin salida (cadena vacía es falsy en Python, saltaba el dispatch de `main()`). Fix: dispatch `if args.map is not None`, más rechazo explícito dentro de `cmd_map`. Commit `9c0f6e0`.
- **[M1] MENOR** — `staged_to_canonical` podía dejar escapar un `ValueError` (p. ej. `--out` fuera de `--root`). Fix: ambas ramas bajo un único `try/except ValueError: return None` (huérfana, nunca traceback). Commit `9c0f6e0`.
- **[M2] MENOR** — la fecha en el marcador rompía la idempotencia byte a byte entre días. Fix: se retira `{fecha}` de la plantilla y el import muerto `from datetime import date`. Commit `084e60f`.
- Evidencia conjunta: `python3 tests/test_confluence_scope.py` → `23/23 OK`; ver cierre de Fase 3 arriba para lint/ledger-lint.

<!-- ==================================================================== -->

### T-09 — Suite de tests `tests/test_confluence_scope.py`

- **Descripción**: Tests unitarios con fixtures (árbol de `docs/` de ejemplo, `confluence-state.json` de muestra, configs válida/inválida) que cubren las tres funciones (`--status`, `--stage`, `--check`), la idempotencia del staging y el mapeo inverso. Sin red, sin conector — sigue el patrón del repo: fichero `tests/test_*.py` con `def main()` y `sys.exit(code)`, ejecutable con `python3 tests/test_confluence_scope.py`.
- **Estado**: completado
- **Tiempo humano**: est. 1,5h · real 0,6h (estimado)
- **Tiempo IA (ejec.)**: est. 0,04h · real 0,08h (estimado)
- **Supervisión**: est. 0,01h (≈25 % IA) · real 0,02h (estimado)
- **Previsión IA**: 17k in / 3k out tok · 0,15 €
- **Dependencias**: T-06, T-07, T-08
- **Tipo**: test
- **Archivos**: `tests/test_confluence_scope.py` (nuevo), `tests/fixtures/confluence-scope/` (nuevo, árbol de ejemplo + configs)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] [GWT] CA-07 — Test que ejecuta `--status` sobre el fixture y verifica las 4 categorías y la lista de excluidos (`test_status_categories_and_scope`, `test_status_sync_classification`, `test_status_without_manifest_all_pending`).
- [x] [GWT] CA-08 — Test que ejecuta `--check` sobre una config sin `docs/security-scan/**` en `exclude` y verifica exit ≠ 0 + mensaje (`test_check_fails_without_security_scan`).
- [x] [GWT] CA-10 — Test que ejecuta `--stage` dos veces seguidas sobre el fixture y compara los árboles resultantes por hash (deben ser idénticos); verifica que ningún excluido aparece (`test_stage_is_idempotent`, `test_stage_creates_exact_scope_and_marker`, `test_stage_copies_readme_byte_for_byte`, `test_stage_wipes_previous_contents`, `test_stage_refuses_unsafe_out_target`, `test_stage_custom_out_survives_repeated_runs`).
- [x] [GWT] CA-11 — Test que, con staging activo, resuelve el mapeo inverso de una ruta staged y comprueba que apunta al fichero canónico correcto (`test_map_inverse_resolves_canonical`, `test_map_inverse_without_prior_stage_is_pure_arithmetic`, `test_map_orphan_page_is_rejected`, `test_map_empty_argument_is_a_usage_error`, `test_map_out_outside_root_is_orphan_not_crash`).
- [x] La suite entera pasa con `python3 tests/test_confluence_scope.py` y termina con exit 0 — evidencia tras la ronda de corrección (ver abajo): `23/23 OK`.
- [x] CA-09 (parcial) — `python3 scripts/lint_plugin.py` sigue en verde tras añadir el script y la suite (0 errores).

**Subtareas**
- [x] Fixture: árbol mínimo bajo `tests/fixtures/confluence-scope/docs/` con al menos un fichero de cada categoría (en alcance, excluido por cada patrón, `security-scan`, `testing/`).
- [x] Fixture: `confluence-state.json` de ejemplo — **decisión sobre la marcha:** se genera en memoria dentro de cada test (`test_status_sync_classification`) con el hash real del fichero de la fixture calculado en el momento, en vez de un fichero estático versionado; evita que el fixture quede desincronizado si el contenido de `docs/README.md` cambia algún día (el hash estático se habría roto en silencio).
- [x] Fixture: config válida (con `security-scan` en `exclude`, `confluence.json`) y config inválida (sin él, `confluence-bad.json`) para CA-08.
- [x] Los 4 tests `[GWT]` + un test de "sintaxis del script no rompe con config ausente" (`test_check_degrades_to_defaults_without_project_config`).
- [x] Confirmado: el bucle `for t in tests/test_*.py` de `ci.yml.MANUAL-COPY` recoge `tests/test_confluence_scope.py` automáticamente (verificado ejecutando el mismo bucle localmente — ver evidencia de cierre de fase); no hizo falta tocar `ci.yml.MANUAL-COPY`.

**Notas**: no se fabricaron tests vacíos; cada `[GWT]` tiene test(s) que lo ejercen de verdad (incl. una regresión explícita de la semántica `**` con cero directorios en `test_glob_to_regex`, el caso que rompería una implementación ingenua basada en `fnmatch` puro).

**Ronda de corrección (gap I1, revisión adversarial):** `tests/fixtures/confluence-scope/docs/security-scan/finding.md` NO estaba trackeado — `.gitignore:4` (`**/security-scan/`) lo bloqueaba sin querer, así que un clon limpio hacía fallar la suite entera (reproducido por la revisión). Fix: excepción `!tests/fixtures/**` en `.gitignore` (el contenido del fixture es inventado, no un hallazgo real) + `git add` del fichero. Verificado con `git ls-files tests/fixtures/confluence-scope` (trackeado) y con el clon limpio de la evidencia final del plan. Commit `5f740cc`. La suite crece de 16 a **23 tests** con los 7 nuevos de esta ronda (C1 ×1, C2 ×1, I2 ×1, I3 ×2, I4 ×1, M1 ×1).

---

### T-10 — Integrar el staging: config, skills y hook

- **Descripción**: Cerrar el contrato cruzado: `confluence.example.json` pasa a `source: "docs/confluence"` + `staging: true`; `SKILL.md` de `confluence-publish` invoca `confluence-scope.py --stage` antes de comparar con el manifiesto (siguiendo el patrón de `roadmap-dashboard`); `SKILL.md` de `confluence-pull` consume el mapeo inverso de T-08 para escribir siempre en el fichero **canónico**; `hooks/mark-docs-pending.sh` ignora `docs/confluence/**`.
- **Estado**: completado
- **Tiempo humano**: est. 0,5h · real 0,3h (estimado)
- **Tiempo IA (ejec.)**: est. 0,01h · real 0,03h (estimado)
- **Supervisión**: est. 0,01h (≈25 % IA) · real 0,01h (estimado)
- **Previsión IA**: 6k in / 1k out tok · 0,05 €
- **Dependencias**: T-08, T-09
- **Tipo**: devops
- **Archivos**: `skills/confluence-publish/assets/confluence.example.json`, `skills/confluence-publish/SKILL.md` (§Publicar), `skills/confluence-pull/SKILL.md` (§Paso 2/3), `hooks/mark-docs-pending.sh`, `tests/test_confluence_scope.py` (caso del hook)
- **Cubre (tests)**: `test_hook_ignores_staged_confluence_folder`, `test_hook_still_marks_pending_for_regular_docs`, `test_hook_still_ignores_security_scan`

**Criterios de aceptación**
- [x] `confluence.example.json` tiene `"source": "docs/confluence"` y `"staging": true` bajo `publish`, con un comentario que explique que `--stage` los regenera.
- [x] `confluence-publish/SKILL.md` documenta que, antes de comparar con el manifiesto, ejecuta `confluence-scope.py --stage` (mismo patrón que la regeneración de `dashboard.md`; regenera dashboard primero, staging después, para que `dashboard.md` entre en la misma pasada).
- [x] [GWT] CA-11 — `confluence-pull/SKILL.md` documenta que, con staging activo, resuelve el destino de escritura con `confluence-scope.py --map` y **nunca** escribe bajo `docs/confluence/`.
- [x] CA-12 — `hooks/mark-docs-pending.sh` no deja marca `.confluence-pending` cuando el único cambio detectado cae bajo `docs/confluence/**`, verificado con 3 casos de prueba del hook (staged ignorado, docs/ normal sigue marcando, security-scan sigue ignorado — regresión).

**Subtareas**
- [x] Editar `confluence.example.json` (`source`, `staging`).
- [x] Añadir la invocación de `--stage` en `SKILL.md` de `confluence-publish` (bloque bash + explicación, igual que el bloque de `roadmap-dashboard`; sección "Staging (regenerar DESPUÉS del dashboard, ANTES de comparar — D5)").
- [x] Añadir el consumo del mapeo inverso en `SKILL.md` de `confluence-pull` (bloque bash con `--map`).
- [x] Modificar `hooks/mark-docs-pending.sh`: añadido el `case` `*docs/confluence/*) continue ;;` junto al de `security-scan`.
- [x] Caso de prueba del hook para CA-12: se añadió a `tests/test_confluence_scope.py` (no había suite de hooks previa) — 3 tests via `subprocess` invocando `bash hooks/mark-docs-pending.sh` con payloads JSON reales.

**Notas**: si el repo ya tiene una suite de tests para hooks, añadir el caso ahí en vez de crear un fichero nuevo; si no, un test corto dentro de `test_confluence_scope.py` es suficiente (invoca el hook con `subprocess` y un payload de ejemplo).

---

## Fase 4 — Documentar la política (C-04)

**Estado**: completado · **Estimado**: 3,0h · **Real**: 1,6h humanas (estimado) · **Coste est.**: ≈150 € · **Tokens est.**: 45k

> **Verificación de fase (P5) — CIERRE DEL PLAN:**
> ```
> $ python3 scripts/lint_plugin.py
> lint_plugin: 8 agentes · 0 errores · 3 avisos
>
> $ for t in tests/test_*.py; do echo "── $t"; python3 "$t" || exit 1; done
> ── tests/test_confluence_scope.py   -> test_confluence_scope: 16/16 OK
> ── tests/test_coverage_check.py     -> OK
> ── tests/test_dashboard.py          -> OK
> ── tests/test_ledger_lint.py        -> test_ledger_lint: 10/10 OK
> ── tests/test_lint_plugin.py        -> test_lint_plugin: 8/8 OK
> ── tests/test_mermaid_blocks.py     -> test_mermaid_blocks: 26 diagrama(s) OK
> ── tests/test_qa_gate.py            -> test_qa_gate: 13/13 OK
> ── tests/test_readme_badges.py      -> test_readme_badges: 6 badge(s) verificados OK
> ── tests/test_worklog.py            -> OK
> ```
> Sincronización Confluence (P5-bis, D3): no aplica en este repo (sin `.claude/confluence.json`).
> Las 13 tareas y las 4 fases quedan `completado`. `spec.md` permanece `aprobada` (no la toca
> `implementer`; la transición a `implementada` la coordina el orquestador tras el cierre de ciclo).
>
> **Verificación REFRESCADA tras la ronda de corrección post-revisión adversarial** (ver detalle en Fase 3 y en T-06/T-07/T-08/T-09 arriba — 8 huecos: 3 críticos, 3 importantes, 2 menores, todos con test de regresión, 8 commits `T-XX-fix:`):
> ```
> $ python3 tests/test_confluence_scope.py
> test_confluence_scope: 23/23 OK
>
> $ for t in tests/test_*.py; do echo "── $t"; python3 "$t" || exit 1; done
> ── tests/test_confluence_scope.py   -> test_confluence_scope: 23/23 OK
> ── tests/test_coverage_check.py     -> OK
> ── tests/test_dashboard.py          -> OK
> ── tests/test_ledger_lint.py        -> test_ledger_lint: 10/10 OK
> ── tests/test_lint_plugin.py        -> test_lint_plugin: 8/8 OK
> ── tests/test_mermaid_blocks.py     -> test_mermaid_blocks: 26 diagrama(s) OK
> ── tests/test_qa_gate.py            -> test_qa_gate: 13/13 OK
> ── tests/test_readme_badges.py      -> test_readme_badges: 6 badge(s) verificados OK
> ── tests/test_worklog.py            -> OK
>
> $ python3 scripts/lint_plugin.py
> lint_plugin: 8 agentes · 0 errores · 3 avisos (preexistentes, no relacionados)
> ```
> Verificación adicional de clon limpio (`git clone . /tmp/clone-check && git checkout feature/confluence-policy && python3 tests/test_confluence_scope.py`) — confirma que el fixture de gap I1 quedó realmente trackeado, no solo presente en este working tree.

### T-11 — Sección normativa "qué sube y qué no" en `SKILL.md`

- **Descripción**: Añadir a `skills/confluence-publish/SKILL.md` la sección normativa "qué sube y qué no": tabla de exclusiones con su motivo (igual contenido que spec §Configuración/parámetros, adaptado a doc de skill), la regla de evidencias binarias (`**/testing/**`, D4) y el contrato de `docs/confluence/` (derivada, no editable, se autoexcluye, mapeo inverso para el pull).
- **Estado**: completado
- **Tiempo humano**: est. 1h · real 0,5h (estimado)
- **Tiempo IA (ejec.)**: est. 0,03h · real 0,04h (estimado)
- **Supervisión**: est. 0,01h (≈25 % IA) · real 0,01h (estimado)
- **Previsión IA**: 13k in / 2k out tok · 0,11 €
- **Dependencias**: T-01, T-03, T-10
- **Tipo**: docs
- **Archivos**: `skills/confluence-publish/SKILL.md`, `skills/confluence-pull/SKILL.md` (resumen espejo, ver guía técnica del encargo: "en las DOS skills")
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] CA-02 — `SKILL.md` tiene una sección normativa "qué sube y qué no" con la tabla de exclusiones y su motivo, incluida `**/testing/**` y la de plan/ledger.
- [x] La sección documenta el contrato de `docs/confluence/` (generada, no editable, se autoexcluye) citando T-08/T-10.
- [x] CA-06 (documental) — la sección deja explícito que `docs/security-scan/**` es invariante no negociable.

**Subtareas**
- [x] Redactar la tabla de exclusiones + motivo (reutilizar la de `spec.md` §Configuración, adaptada al tono de la skill).
- [x] Redactar el párrafo del contrato de `docs/confluence/`.
- [x] Enlazar desde ahí a la matriz de `docs/FLOWS.md` (T-12) en vez de duplicarla.
- [x] **Añadido (no estaba en el plan original, sí en la guía técnica del encargo):** resumen equivalente en `confluence-pull/SKILL.md` — el pull nunca sube nada por su cuenta, así que su sección remite a la de `confluence-publish` como fuente y solo añade la regla propia (destino de escritura siempre canónico).

**Notas**: depende de que T-01/T-03/T-10 estén cerradas para no documentar algo que aún puede cambiar.

<!-- ==================================================================== -->

### T-12 — Matriz disparador→artefacto→¿se publica? en `docs/FLOWS.md`

- **Descripción**: Añadir a `docs/FLOWS.md` (sección "5 · Confluence") una matriz con los 10 disparadores conocidos (`analyst`, `evaluator`, `planner`, `qa`, `documenter`, `/pm-backlog`, `/retro`, `/spec-drift`, `/roadmap-brief`, `implementer`) → artefacto que producen → ¿se publica? (sí/no + motivo si es "no": plan, `tasks.md`, `testing/**`, `docs/en/`, `examples/`, `agents/`). Espejo en `docs/en/FLOWS.md` en el mismo cambio.
- **Estado**: completado
- **Tiempo humano**: est. 1h · real 0,5h (estimado)
- **Tiempo IA (ejec.)**: est. 0,03h · real 0,04h (estimado)
- **Supervisión**: est. 0,01h (≈25 % IA) · real 0,01h (estimado)
- **Previsión IA**: 13k in / 2k out tok · 0,11 €
- **Dependencias**: T-04, T-05, T-10
- **Tipo**: docs
- **Archivos**: `docs/FLOWS.md`, `docs/en/FLOWS.md`
- **Cubre (tests)**: `tests/test_mermaid_blocks.py` (regresión: no rompe ningún diagrama)

**Criterios de aceptación**
- [x] CA-05 — `docs/FLOWS.md` contiene la matriz disparador→artefacto→¿se publica? cubriendo los 10 disparadores, con los "no" explícitos (plan, `tasks.md`, `testing/**`, `docs/en/`, `examples/`, `agents/`).
- [x] `docs/en/FLOWS.md` tiene el espejo actualizado **en el mismo cambio** (regla bilingüe del repo).
- [x] Los tokens que parsea máquina (nombres de estado, rutas) se mantienen en español también en la versión EN, según CLAUDE.md (p. ej. "D1"/"D3"/"D4" y las rutas se dejan literales; los estados `en-progreso`/`completado` de otras secciones ya seguían esa regla).

**Subtareas**
- [x] Redactar la tabla en `docs/FLOWS.md` (sección 5, junto al diagrama Mermaid ya existente) + nota de la política y de los "no" estructurales.
- [x] Traducir/adaptar la tabla en `docs/en/FLOWS.md`.
- [x] Verificado con `tests/test_mermaid_blocks.py` → `26 diagrama(s) OK` (no se tocó ningún bloque Mermaid, solo se añadió texto/tabla junto al de la sección 5).

**Notas**: la nota de interacción D1↔D3 (T-05) debe quedar reflejada aquí también, no solo en `implementer.md`.

<!-- ==================================================================== -->

### T-13 — Actualizar `docs/README.md` + CHANGELOG + verificación transversal final

- **Descripción**: Actualizar el párrafo del circuito bidireccional en `docs/README.md` (L39) y su espejo `docs/en/README.md` para reflejar la política curada y el staging generado; corregir la fila de `qa` que hoy dice "Sincroniza el informe en Confluence" (ya no aplica tras T-03/D4). Añadir entradas a `CHANGELOG.md` (`[Unreleased]`) y `CHANGELOG.es.md` (`[Sin publicar]`). Cerrar con la verificación transversal: `python3 scripts/lint_plugin.py` + todas las suites de `tests/` en verde.
- **Estado**: completado
- **Tiempo humano**: est. 1h · real 0,6h (estimado)
- **Tiempo IA (ejec.)**: est. 0,03h · real 0,05h (estimado)
- **Supervisión**: est. 0,01h (≈25 % IA) · real 0,01h (estimado)
- **Previsión IA**: 13k in / 2k out tok · 0,11 €
- **Dependencias**: T-11, T-12
- **Tipo**: docs
- **Archivos**: `docs/README.md`, `docs/en/README.md`, `CHANGELOG.md`, `CHANGELOG.es.md`
- **Cubre (tests)**: suite completa `tests/test_*.py` (8 ficheros) + `scripts/lint_plugin.py`

**Criterios de aceptación**
- [x] `docs/README.md` L39 (párrafo del circuito bidireccional) refleja la política curada (D1), el staging (D5) y que `qa` ya no ofrece publicar `testing/` (D4); espejo `docs/en/README.md` actualizado en el mismo cambio. También se corrigieron la fila de `qa` (ya no cita `confluence-publish`) y la de `implementer`/la de la skill `confluence-publish` (usuarios actualizados: +`implementer`, +`documenter`, +los 3 comandos de fin de ciclo, -`qa`).
- [x] `CHANGELOG.md` (`[Unreleased]`) y `CHANGELOG.es.md` (`[Sin publicar]`) tienen una entrada describiendo la política nueva.
- [x] CA-09 — `python3 scripts/lint_plugin.py` termina en verde (0 errores, 3 avisos preexistentes no relacionados); **todas** las suites `tests/test_*.py` (8 ficheros, incluida `test_confluence_scope.py` 16/16) terminan en verde.
- [x] Ningún criterio CA-01 a CA-12 queda sin marcar tras esta tarea (ver checklist global "Criterios de aceptación (global)" más abajo, y `spec.md` §Criterios de aceptación).

**Subtareas**
- [x] Reescribir el párrafo L39 de `docs/README.md` + fila de `qa`.
- [x] Espejo en `docs/en/README.md`.
- [x] Entradas de `CHANGELOG.md`/`CHANGELOG.es.md`.
- [x] `python3 scripts/lint_plugin.py` y `for t in tests/test_*.py; do python3 "$t" || exit 1; done` en local antes de cerrar la fase — evidencia pegada en la nota de cierre de Fase 4 más abajo.
- [x] Marcar el estado de fases/tareas como `completado` en este ledger tras la verificación en verde.

**Desviación declarada:** el plan listaba `docs/roadmap/README.md` (fila de esta iniciativa) entre los archivos de esta tarea. `implementer` tiene la regla explícita de NO tocar `docs/roadmap/` salvo `tasks.md` (regla del propio agente, ver `agents/implementer.md` §3 Reglas); esa fila del índice de cartera la mantiene `/roadmap-status`/`/pm-backlog` (dashboard derivado), no el implementer a mano. Se deja sin tocar; se refrescará sola con el próximo `/roadmap-status`.

**Notas**: es el cierre de todo el plan — si algo de CA-01..CA-12 falta, se resuelve aquí antes de dar la iniciativa por terminada, no después.

---

## Notas de implementación

- **Disciplina de esta ejecución (P1-bis).** `.claude/dev.json` no existe → flujo clásico (sin TDD obligatorio, sin worktree, sin subagentes por tarea); los tests de `confluence-scope.py` se escribieron igualmente por exigencia de la spec/plan (CA-07/CA-08/CA-10/CA-11), no por config de TDD. `usage-meter.py` no puede medir en este sandbox: todas las horas "real" quedan marcadas `(estimado)`, nunca `(medido)`. `.claude/jira.json`/`.claude/confluence.json` no existen: sin volcado a Jira ni sincronización real con Confluence durante esta implementación.
- **T-06/T-07/T-08 se implementaron en una sola pasada** (un único fichero `confluence-scope.py` que comparte `load_policy`/`resolve_scope`/`glob_to_regex` entre los tres subcomandos): separarlas en tres ediciones sucesivas del mismo fichero no aportaba valor y sí riesgo de inconsistencia. El reparto de horas por tarea en el ledger es un prorrateo declarado, no una medición independiente por subcomando.
- **`docs/confluence/**` se autoexcluye por código** (`ALWAYS_EXCLUDE` en el script), no listándola en `confluence.example.json` — más robusto que depender de que nadie borre la línea de la config, y evita que CA-01 (que fija el array `exclude` literal de T-01) tenga que anticipar una carpeta que aún no existía en esa tarea.
- **Fixture de `confluence-state.json` generada en memoria** (T-09) en vez de un fichero estático versionado: el hash de un contenido real se calcula en el propio test, así nunca se desincroniza en silencio si el fixture cambia.
- **Caso de prueba del hook (CA-12) añadido a `tests/test_confluence_scope.py`** en vez de crear un fichero de tests dedicado a hooks: el repo no tenía ese patrón previo (confirmado por búsqueda) y el plan lo dejaba como opción válida.
- **Desviación declarada (T-13):** no se tocó `docs/roadmap/README.md` (fila de esta iniciativa) pese a que el plan la listaba entre los archivos de T-13 — choca con la regla explícita de `implementer` de no tocar `docs/roadmap/` salvo `tasks.md`; esa fila la mantiene el dashboard (`/roadmap-status`/`/pm-backlog`).
- **Estados de cierre:** `improvement-plan.md` y `tasks.md` pasan a `completado` (implementación terminada, verificación en verde). `spec.md` se deja `aprobada`: su transición a `implementada` es del orquestador tras el cierre de ciclo (esta iniciativa no tiene `test-plan.md` ni handoff a `qa` — es infra sin UI; el propio plan lo señala en su "Siguiente paso").
- **Sin desviaciones de alcance:** las 13 tareas y las 5 características (C-01 a C-05) se completaron tal como las definió el plan; no hubo bloqueos ni recortes de criterios de aceptación.
- **Ronda de corrección post-revisión adversarial (intento 1/3, tras el cierre inicial).** La revisión de dos lentes reprodujo 8 huecos en `confluence-scope.py`/su suite, todos verificados/reproducidos por los revisores (no rebatidos): 3 críticos — **C1** el marcador de staging pisaba `docs/README.md` (fix: nombre reservado `_STAGING-LEEME.md`, commit `b9c342a`); **C2** `--stage` podía `rmtree` un `--out` ajeno (fix: `assert_safe_stage_target`, commit `2e73522`); **I1** el fixture de `security-scan` no estaba trackeado por `.gitignore` (fix: excepción `!tests/fixtures/**`, commit `5f740cc`) — 3 importantes — **I2** la autoexclusión del staging estaba cableada al literal por defecto en vez del `--out` real (fix: `resolve_out_dir`/`always_exclude_for`, commit `3a778b8`); **I3** `--config` explícito roto degradaba en silencio (fix: `ConfigError`, commit `8923257`); **I4** `--map ""` salía 0 sin salida (fix: dispatch `is not None`, commit `9c0f6e0`) — y 2 menores — **M1** `ValueError` sin capturar en el mapeo inverso (mismo commit `9c0f6e0`); **M2** la fecha en el marcador rompía la idempotencia entre días (fix: se retira, commit `084e60f`). T-06 a T-09 volvieron a `en-progreso` mientras se corregía y cerraron de nuevo con evidencia (ver notas de cada tarea arriba); la suite crece de 16 a 23 tests. **No se toca** `docs/roadmap/README.md` (lo mantiene `/roadmap-status`, fuera del alcance de `implementer`) ni se "corrige" la ausencia de `docs/confluence/` en este repo — es correcta: este repo es el propio plugin, no un proyecto consumidor con `.claude/confluence.json` activo, así que nadie ha ejecutado `--stage` aquí todavía.
- **Ronda de corrección intento 3/3 (revisión sobre las correcciones del intento 1).** Dos gaps nuevos detectados sobre el código ya corregido, ambos con test y sin tocar `spec.md` (la enmienda de CA-10 queda para el orquestador, cauce PM): **[Importante]** el marcador `_STAGING-LEEME.md` se habría publicado como página en Confluence — el paso 4 de `SKILL.md` recorre el árbol STAGED sin volver a invocar `confluence-scope.py`, así que la autoexclusión por código (que solo protege el escaneo del canónico al generar el staging) no cubre ese segundo recorrido; fix cinturón y tirantes: `**/_STAGING-LEEME.md` en el `exclude` de `assets/confluence.example.json` + frase explícita en el paso 4, test `test_default_policy_excludes_staging_marker_from_publish_walk` (commit `0cde278`). **[Menor]** `--out` relativo se resolvía contra `--root` mientras `--config`/`--state` contra el cwd, sin documentar (reproducido: `--root demo --out demo/docs` anida en `demo/demo/docs`); se mantiene la semántica (familias distintas: ubicación dentro del proyecto vs. puntero a fichero explícito) y se documenta en el docstring del módulo, el `--help` y `SKILL.md`, con test `test_out_relative_anchors_to_root_not_cwd` (commit `16ecd64`). Suite: 23 → 25 tests; suites completas + `lint_plugin.py` + `ledger-lint.py` en verde tras ambos commits.
