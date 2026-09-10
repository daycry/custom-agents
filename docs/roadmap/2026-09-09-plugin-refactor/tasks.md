---
generacion:              # ventana compartida con improvement-plan.md
  inicio: 2026-09-10T11:55:46Z
  fin: 2026-09-10T12:00:57Z
  fuente: medido           # intento 3 (cierre y puertas sobre los borradores del intento 2). Tokens leídos de las transcripciones con el parser del repo + filtro `timestamp >= inicio − 60 s` (17 respuestas; 5.765 registros previos descartados). El marcador lo abrió el kit en caché del plugin (1.13.0, anterior a C-13 (i)): `transcriptDir: null`, `offsets: {}` → `close` oficial degradó a estimado; sin filtro habría sumado el histórico entero (el caso de T-04). `duracion` = tokens ÷ ratio; reloj de la ventana 5m11s. Los dos intentos anteriores (muertos por API) se descartaron y NO se acumulan: el 2.º midió 1,20 h IA / 7,76 € escribiendo los borradores
  tokens_reales: { entrada: 459, salida: 25431, cache_creacion: 216259, cache_lectura: 4637516, respuestas: 17 }
  eur: 3.96
  horas_ia: 0.51
  duracion: 31m
  ratio_usado: 479326            # CALIBRATION.md (mediana de 6)
verificacion: obligatoria   # cada T-XX lleva `- **Verificación**:`; lo exige ledger-lint (exit 1 si falta)
---

# Checklist de Tareas — Refactor del plugin: deuda medida en hotspots, copias declaradas (O1) y contratos entre piezas

| | |
|---|---|
| **Estado** | en-progreso |
| **Fecha** | 2026-09-10 |
| **Plan** | [`improvement-plan.md`](./improvement-plan.md) |
| **Diseño** | [`design.md`](./design.md) — opción O1 (`ADR-016` `propuesta`) |
| **Test-plan** | n/a (sin UI) — marcador en el frontmatter de `improvement-plan.md` (C-08 / T-13) |
| **Tramos de revisión** | **R1** = Fase 1 (T-01…T-04) · **R2** = Fase 2 (T-05…T-08) · **R3** = Fase 3 (T-09, T-10) · **R4** = Fase 4 (T-11…T-19). Revisión de dos lentes **por tramo** (§6.6 del análisis), no por tarea; la traza «Revisión de dos lentes — intento N» se anota en T-20 |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del plan. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador SDD externo— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

> **Excepciones declaradas al «cero cambio de comportamiento» del bloque (a)** (condición 4 del go): **T-01** hace que `code-health.py` cuente menos TODO (8 → 1) y **T-02** añade el flag aditivo `--exclude-path` (default sin cambio). Ninguna otra tarea de las Fases 1-3 cambia una salida, un flag o un exit code. Tras T-02 se toma la **segunda línea base** (`code-health-baseline-2.json`) y desde T-03 toda comparación usa esa línea base **con los mismos flags** (`--exclude-tests --exclude-path interop`).

> **Entorno (Windows).** `export PATH="$PWD/.venv/Scripts:$PATH"` antes de cualquier puerta; consola cp1252 (`GOT-005`); `core.autocrlf=true`. Capturas de contratos fuera del repo: `CAPTURAS="${CAPTURAS:-$TEMP/plugin-refactor-capturas}"`. «Suite idéntica» = **identidad por test** (`-rA` + `sort` + `diff`), nunca «todo verde»: hay ~39 fallos de entorno preexistentes en esta máquina.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — Línea base limpia y la cicatriz | 0 | 4 | 0% | 0 / 11,5h | 0 / 1,29h | 0 / 0,32h | 0 / 619k |
| Fase 2 — Los otros cuatro hotspots | 0 | 4 | 0% | 0 / 14,0h | 0 / 1,60h | 0 / 0,40h | 0 / 767k |
| Fase 3 — Un solo mecanismo de copias declaradas (O1) | 0 | 2 | 0% | 0 / 4,0h | 0 / 0,50h | 0 / 0,13h | 0 / 239k |
| Fase 4 — Encadenamiento E1–E11 | 0 | 9 | 0% | 0 / 30,5h | 0 / 3,64h | 0 / 0,91h | 0 / 1.745k |
| Fase 5 — Proceso: revisión por tramo, corrección y cierre | 0 | 3 | 0% | 0 / 14,0h | 0 / 1,80h | 0 / 0,45h | 0 / 864k |
| **TOTAL** | **0** | **22** | **0%** | **0 / 74,0h** | **0 / 8,83h** | **0 / 2,21h** | **0 / 4.234k** |

> Horas **base** (sin colchón; con el margen del 20 %: 88,8 h humanas · 10,6 h IA · 2,65 h supervisión). Tokens = facturables (in + out + creación de caché). Coste base **3.734 €** (4.479 € con margen). Heredado de `evaluation.md` por característica; diferencias declaradas en el plan (P-1 y C-13 (i) hechas, C-14 propuesta).

> **Horas → Jira.** El worklog que imputa `jira-sync` al completar cada tarea es **Tiempo IA (ejec.) + Supervisión** (real; o estimación si no hay real), topado a la jornada configurada. Ver `skills/jira-sync/SKILL.md`. En este repo `.claude/jira.json` no existe: sin volcado.

---

## Fase 1 — Línea base limpia y la cicatriz

**Estado**: en-progreso · **Estimado**: 11,5h · **Real**: — · **Coste est.**: 580 € · **Tokens est.**: 619k · **Tramo**: R1

### T-01 — C-04: detector de TODO de `code-health.py`, 8 → 1

- **Descripción**: `TODO_RE` (`skills/code-health/scripts/code-health.py:49`) acepta «palabra seguida de `(`» y con ello la prosa castellana «TODO (ADRs, …» de `confluence-scope.py:113`; además el detector se cuenta a sí mismo (5 marcadores en su docstring y código) y a `journal.py:41`. Excluir comentarios que enumeran marcadores y el propio fichero del detector; queda el real (`usage-meter.py:380`, 29 días). **Excepción declarada** al «cero cambio de comportamiento»: el informe cuenta menos TODO.
- **Changelog**: El informe de salud del código deja de contar como TODO su propia descripción del detector y la palabra castellana «TODO (»: 8 falsos positivos pasan a 1 marcador real.
- **Estado**: borrador
- **Tiempo humano**: est. 2,0h · real —
- **Tiempo IA (ejec.)**: est. 0,25h · real —
- **Supervisión**: est. 0,06h (≈25 % IA) · real —
- **Previsión IA**: 88k in / 13k out tok · 0,9 € tokens · coste tarea 101 €
- **Dependencias**: ninguna (primera tarea: limpia la línea base antes de medir el refactor)
- **Tipo**: test
- **Archivos**: `skills/code-health/scripts/code-health.py`, `skills/code-health/scripts/test_code_health.py`
- **Verificación**:
  - `python skills/code-health/scripts/code-health.py . --exclude-tests --json | python -c "import json,sys; print(json.load(sys.stdin)['resumen']['todos'])"` → `1`
  - `python skills/code-health/scripts/code-health.py . --exclude-tests --json --baseline docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline.json` → `TODO/FIXME/HACK` «↓ mejora»; ninguna otra métrica «↑ empeora» salvo `edad máx. TODO (días)` (reloj)
  - `python -m pytest -q skills/code-health/scripts/test_code_health.py -p no:cacheprovider` → los 14 tests previos + 3 nuevos en verde (marcadores enumerados en comentario · prosa «TODO (» · el propio fichero del detector)
  - `python scripts/lint_plugin.py` → `0 errores` · `python scripts/export-interop.py --check` → `48 ficheros al día`

**Criterios de aceptación**
- [ ] CA-06: `todos` = 1 y el único marcador es `agent-kits/shared/usage-meter.py` (línea del «histórico como ventana»)
- [ ] Test nuevo con mutante: quitar la exclusión del propio fichero → el test se pone rojo (evidencia pegada)
- [ ] Flags, exit codes y forma del `--json`/`--baseline` de `code-health.py` sin cambio (`grep -n add_argument` idéntico antes/después)
- [ ] Ningún test existente modificado; la suite `test_code_health.py` previa pasa idéntica

**Subtareas**
- [ ] Capturar `code-health.py . --exclude-tests --json` ANTES (`$CAPTURAS/ch-antes.json`) para comparar todo salvo `marcadores`
- [ ] Ajustar `TODO_RE`: exigir mayúsculas y quitar `(` del lookahead que acepta la prosa castellana; excluir líneas que enumeran ≥ 2 marcadores distintos (descripción de patrón) y el fichero del propio detector
- [ ] 3 tests nuevos en `test_code_health.py` (fixtures con `tmp_path`), uno de ellos con mutante documentado
- [ ] Anotar aquí la excepción declarada (cuenta menos TODO) al cerrar

**Notas**: Primera excepción declarada (condición 4 del go). No toca `interop/` ni prosa de piezas. `code-health --baseline` es la puerta de esta tarea; el resto del bloque (a) compara contra la línea base 2 desde T-03.

### T-02 — C-05: `code-health.py --exclude-path` (rutas generadas) + segunda línea base

- **Descripción**: flag aditivo `--exclude-path <prefijo>` (repetible, relativo a la raíz) en `ficheros()` (`code-health.py:80`) para sacar del informe `interop/` (salida de `export-interop.py`); default sin cambio. Con el flag, el par `hooks/opencode-plugin.js` ↔ `interop/opencode/plugins/custom-agents-hooks.js` (118 líneas) deja de contar. **Excepción declarada**: añade un flag (aditivo). Al cerrar, el **orquestador** (`/dev-cycle`, no el `implementer`: su hook de guardia solo le permite `tasks.md` en `docs/roadmap/`) escribe la **segunda línea base** `code-health-baseline-2.{json,md}` con `--exclude-tests --exclude-path interop` (S-4).
- **Changelog**: `code-health.py` admite `--exclude-path` para sacar del informe carpetas generadas como `interop/`; sin el flag la salida es la de siempre.
- **Estado**: borrador
- **Tiempo humano**: est. 2,0h · real —
- **Tiempo IA (ejec.)**: est. 0,25h · real —
- **Supervisión**: est. 0,06h (≈25 % IA) · real —
- **Previsión IA**: 88k in / 13k out tok · 0,9 € tokens · coste tarea 101 €
- **Dependencias**: T-01 (la línea base 2 debe llevar ya el detector corregido)
- **Tipo**: test
- **Archivos**: `skills/code-health/scripts/code-health.py`, `skills/code-health/scripts/test_code_health.py`, `skills/code-health/SKILL.md` (una línea de uso: excepción declarada a CA-09), `docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline-2.json` y `.md` (los escribe el orquestador)
- **Verificación**:
  - `python skills/code-health/scripts/code-health.py . --exclude-tests --json > "$CAPTURAS/ch-sinflag.json" && python -c "import json; a=json.load(open('$CAPTURAS/ch-antes.json')); b=json.load(open('$CAPTURAS/ch-sinflag.json')); a.pop('marcadores'); b.pop('marcadores'); a['resumen'].pop('todos'); b['resumen'].pop('todos'); a['resumen'].pop('todo_edad_max_dias'); b['resumen'].pop('todo_edad_max_dias'); print(a==b)"` → `True` (sin flag, byte-idéntico salvo el TODO ya declarado en T-01)
  - `python skills/code-health/scripts/code-health.py . --exclude-tests --exclude-path interop --json | grep -c "custom-agents-hooks.js"` → `0`
  - `python -m pytest -q skills/code-health/scripts/test_code_health.py -p no:cacheprovider` → 17 previos + 2 nuevos (exclusión aplicada · default sin cambio) en verde
  - (orquestador) `python skills/code-health/scripts/code-health.py . --exclude-tests --exclude-path interop --json > docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline-2.json && python skills/code-health/scripts/code-health.py . --exclude-tests --exclude-path interop > docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline-2.md` → ficheros creados; `funciones_largas` del `resumen` = 104 (misma cifra que hoy: el flag no toca funciones)
  - `python scripts/lint_plugin.py` → `0 errores` (la línea de `SKILL.md` no lo engorda por encima de 200)

**Criterios de aceptación**
- [ ] CA-07: con `--exclude-path interop` el par de 118 líneas no aparece en `duplicados`; sin flag, salida byte-idéntica a la de T-01
- [ ] `--exclude-path` es repetible y acepta prefijos relativos a la raíz (`interop`, `interop/opencode`); test con dos prefijos
- [ ] Segunda línea base escrita por el orquestador en la carpeta de la iniciativa y referenciada en la `Verificación` de T-03…T-08
- [ ] `skills/code-health/SKILL.md` documenta el flag en una línea y sigue ≤ 200 líneas

**Subtareas**
- [ ] `argparse`: `--exclude-path` con `action="append"`, default `[]`; filtro en `ficheros()` por prefijo normalizado (`/` y `\`)
- [ ] 2 tests nuevos en `test_code_health.py`
- [ ] Una línea en `skills/code-health/SKILL.md` (uso) — excepción declarada a CA-09 (documenta el flag, no cambia el método)
- [ ] Handoff al orquestador: tomar la línea base 2 y anotar aquí su hash/fecha

**Notas**: Segunda excepción declarada (condición 4 del go). El default NO excluye `interop/` (cambiaría el informe de todos los consumidores); solo con flag. S-4: comparar una salida con el flag contra la línea base 1 daría «mejora» ficticia de 118 líneas — por eso existe la línea base 2.

### T-03 — C-01: `task-brief.py` — `main()` en siete secciones y las reglas de la persona en una función

- **Descripción**: `main()` (`agent-kits/shared/task-brief.py:680`, 160 líneas) pasa a montar las siete secciones del brief con una función por sección; las cuatro reglas de la persona (`PERSONA_TOPE_CHARS`, `PERSONA_SUELO_CHARS`, `PERSONA_TOPE_MINIMO_UTIL` y el margen dinámico) se funden en una función con nombre. 4 funciones largas → ≤ 2; ninguna nueva > 60. Contratos congelados: nombres de secciones, `BRIEF_TOPE_CHARS = 10000`, `_REVISION_HDR_FALLBACK`, `--json`, exit codes; `test_task_brief.py` **no se toca**. Prerequisito de `brief-budget`.
- **Changelog**: El generador del brief del subagente queda partido en funciones por sección, con las reglas del tamaño de la persona en un solo sitio; el brief que produce es el mismo byte a byte.
- **Estado**: borrador
- **Tiempo humano**: est. 6,0h · real —
- **Tiempo IA (ejec.)**: est. 0,60h · real —
- **Supervisión**: est. 0,15h (≈25 % IA) · real —
- **Previsión IA**: 210k in / 32k out tok · 2,2 € tokens · coste tarea 302 €
- **Dependencias**: T-02 (línea base 2 tomada). **Arista hacia fuera**: bloquea a `brief-budget` (mismo `main()`; condición 3 del go)
- **Archivos**: `agent-kits/shared/task-brief.py`
- **Verificación**:
  - Captura previa (antes de tocar): `python agent-kits/shared/task-brief.py docs/roadmap/2026-09-09-project-specialization/tasks.md T-05 > "$CAPTURAS/brief-antes.md"` (iniciativa CON `design.md`, GOT-009) y `python -m pytest -q tests agent-kits/shared skills -p no:cacheprovider -rA 2>/dev/null | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sort > "$CAPTURAS/suite-antes.txt"`
  - Tras el refactor: mismo comando del brief → `"$CAPTURAS/brief-despues.md"` · `diff "$CAPTURAS/brief-antes.md" "$CAPTURAS/brief-despues.md"` → vacío
  - Suite: mismo pipeline → `"$CAPTURAS/suite-despues.txt"` · `diff "$CAPTURAS/suite-antes.txt" "$CAPTURAS/suite-despues.txt"` → vacío (identidad por test)
  - `python skills/code-health/scripts/code-health.py . --exclude-tests --exclude-path interop --json --baseline docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline-2.json` → `funciones largas` «↓ mejora»; ninguna métrica «↑ empeora» salvo `edad máx. TODO (días)`
  - `python skills/code-health/scripts/code-health.py . --exclude-tests --json --top 1000 | python -c "import json,sys; d=json.load(sys.stdin); print(sum(1 for f in d['tamano']['largas'] if f['fichero'].endswith('task-brief.py')))"` → `≤ 2` (ajustar la clave a la forma real del JSON si difiere; la cifra es la que manda)
  - `grep -n "add_argument\|sys.exit\|return [0-9]" agent-kits/shared/task-brief.py` antes/después → `diff` vacío · `python -m pytest -q agent-kits/shared/test_task_brief.py -p no:cacheprovider` → verde sin tocar el fichero
  - `python scripts/lint_plugin.py` → `0 errores` · `python scripts/export-interop.py --check` → `48 ficheros al día`

**Criterios de aceptación**
- [ ] `task-brief.py`: funciones > 30 líneas ≤ 2 (hoy 4) y ninguna nueva > 60; `main()` delega en siete funciones de sección con nombre
- [ ] Una sola función con nombre calcula el presupuesto de la persona (las tres constantes + margen dinámico); las constantes conservan nombre y valor
- [ ] Brief real con `## Diseño` byte-idéntico antes/después (CA-08); suite idéntica por test (CA-03); `test_task_brief.py` sin cambios (CA-04)
- [ ] `git diff --stat -- agents commands 'skills/*/SKILL.md'` vacío para este commit (CA-09)

**Subtareas**
- [ ] Capturas previas (`brief-antes.md`, `suite-antes.txt`, `kf-antes.json`, `scope-antes.json`, `dash-antes.*`, `lint-antes.txt`, `doctor-antes.json`): se toman UNA vez aquí y las reutilizan T-05…T-08
- [ ] Extraer `seccion_<nombre>()` por cada una de las siete secciones; `main()` solo parsea, encadena y aplica el tope
- [ ] Extraer `presupuesto_persona(...)` con las cuatro reglas; docstring que las nombra
- [ ] Ejecutar la `Verificación` completa y pegar salidas; commit `T-03: …`

**Notas**: Hotspot que acaba de sufrir tres rondas (§3). La suite recorre un solo ledger sin `design.md` (E8 → `brief-budget` C-05): por eso la captura del brief se hace sobre `project-specialization`, que sí lo tiene. Si `brief-budget` C-05 (guardarraíl sobre todos los ledgers) se adelantara, sería red de seguridad extra, no requisito.

### T-04 — C-13 (ii-a): `usage-meter.py` robusto a marcadores anteriores al arreglo y ventana por `timestamp`

- **Descripción**: la vía rápida `usage-meter-transcripts` hizo que el meter encuentre las transcripciones (C-13 (i), hecha). Hoy se observó lo que faltaba: (1) un marcador **abierto con el código anterior** (sin `transcriptDir`, `offsets` vacíos) y cerrado con el nuevo **contó enteros los transcripts previos** (1.552 respuestas / 143 € falsos, medido); (2) `duracion` se deriva de tokens ÷ ratio (`cmd_close`: `fmt_horas(horas)`), no del reloj (`26m` con `inicio`/`fin` separados 10m37s). Arreglo: filtro `timestamp >= inicio` (tolerancia 60 s) en `_sum_usage_window()` (`:192`); `start` escribe `version: 2` en el marcador y `close` degrada con aviso («marcador anterior al arreglo») los que no lo traen; `duracion_reloj` (`fin − inicio`, formato `fmt_horas`) como clave **aditiva** del JSON de `close` — `duracion` no cambia de semántica (lo consumen dashboards y plantillas).
- **Changelog**: `usage-meter.py` ya no cuenta transcripciones anteriores al inicio de la ventana ni acepta marcadores de la versión antigua, y añade `duracion_reloj` junto a la `duracion` derivada de tokens.
- **Estado**: borrador
- **Tiempo humano**: est. 1,5h · real —
- **Tiempo IA (ejec.)**: est. 0,19h · real —
- **Supervisión**: est. 0,05h (≈25 % IA) · real —
- **Previsión IA**: 66k in / 10k out tok · 0,7 € tokens · coste tarea 76 €
- **Dependencias**: T-03 (orden del tramo R1; sin dependencia de código). Requiere `master` `8fee28a` (C-13 (i)) — ya es ancestro de la rama
- **Tipo**: test
- **Archivos**: `agent-kits/shared/usage-meter.py`, `agent-kits/shared/test_usage_meter.py`, `docs/observability.md`, `docs/en/observability.md`
- **Verificación**:
  - `python -m pytest -q agent-kits/shared/test_usage_meter.py -p no:cacheprovider` → suite previa + 4 nuevos en verde (registro con `timestamp < inicio` descartado · tolerancia 60 s · marcador sin `version` → `fuente: estimado` con aviso · `duracion_reloj` presente y `duracion` sin cambio)
  - Mutante: quitar el filtro de `timestamp` → el test del fixture con transcript previo se pone rojo (salida pegada)
  - `python agent-kits/shared/usage-meter.py start --artefacto /tmp/x.md && python agent-kits/shared/usage-meter.py close --artefacto /tmp/x.md | python -c "import json,sys; d=json.load(sys.stdin); print('duracion_reloj' in d, d['fuente'])"` → `True estimado` (start y close seguidos: ventana sin respuestas, como hoy) · `python agent-kits/shared/usage-meter.py fmt 0.5` → `30m` (contrato `fmt` intacto)
  - `grep -n "add_argument" agent-kits/shared/usage-meter.py` antes/después → `diff` vacío (sin flags nuevos; `version` es un dato del marcador, no un flag)
  - `python scripts/lint_plugin.py` → `0 errores`

**Criterios de aceptación**
- [ ] CA-19 (ii, parte a): `close` ignora registros con `timestamp` anterior a `inicio − 60 s` y avisa cuando descarta > 0 registros con offset > 0
- [ ] Un marcador sin `version` (abierto con la versión anterior) degrada a `fuente: estimado` con aviso explícito; el `usage-state.json` de esta máquina se limpia de marcadores viejos al cerrar la tarea (`status` los lista) y se anota aquí cuántos eran
- [ ] `duracion_reloj` aditiva en el JSON de `close`; `duracion`, `horas_ia`, `ratio_usado`, exit codes y flags idénticos
- [ ] `docs/observability.md` (+EN) explica en dos líneas la diferencia `duracion` (tokens ÷ ratio) vs `duracion_reloj` (reloj)

**Subtareas**
- [ ] Fixture: transcript con 3 registros (uno anterior a `inicio`, uno dentro de la tolerancia, uno posterior) → solo los dos últimos suman
- [ ] `start`: `version: 2`; `close`: rama de degradación para marcadores sin `version` (mensaje con el motivo)
- [ ] `duracion_reloj` en `cmd_close`; dos líneas en `docs/observability.md` + espejo EN
- [ ] Limpiar marcadores viejos del `usage-state.json` local (`status` → lista) y anotar

**Notas**: Es bloque (b) (cambia comportamiento del meter) colocado en R1 para que **el resto de la iniciativa se mida bien**: cada tarea de este ledger abre y cierra su marcador con el código corregido. La parte (ii-b) (agregado `fuente: estimado` visible + `CALIBRATION.md`) es T-17.

---

## Fase 2 — Los otros cuatro hotspots

**Estado**: borrador · **Estimado**: 14,0h · **Real**: — · **Coste est.**: 706 € · **Tokens est.**: 767k · **Tramo**: R2

> **Arista hacia fuera (condición 3 del go):** esta fase completa precede a **F2 de `project-specialization`** (toca `doctor.py` y `lint_plugin.py --root`). Orden dentro de la fase: `knowledge-find` (el que más cambia) → `doctor` → `build_dashboard` → `lint_plugin` (**el último**, para que T-10 y T-16 no lo toquen dos veces). Reparto del objetivo §8 (32 → ≤ 16): `task-brief` ≤ 2 (T-03) · `knowledge-find` ≤ 1 · `doctor` ≤ 4 · `build_dashboard` ≤ 4 · `lint_plugin` ≤ 5.

### T-05 — C-02 (1/4): `knowledge-find.py` — `main()` y las otras dos funciones largas

- **Descripción**: `agent-kits/shared/knowledge-find.py` (852 líneas, 9 cambios/90 d): `main()` (`:932`, 87 líneas) y las otras dos funciones > 30 líneas → ≤ 1 función larga, ninguna nueva > 60. Contrato congelado: forma del `--json` (`acierto_json` `:794`, 12 claves — lo consumen `task-brief.py` y `hooks/session-context.sh`), `--doctrina`, `--show`, `--related`, `--limit 0`, `--tipo-tarea`, exit codes. `celdas_md` (`:244-264`, copia guardada) **no se toca**.
- **Changelog**: `knowledge-find.py` queda partido en funciones cortas; la salida `--json` que consumen el brief y el hook de sesión es la misma byte a byte.
- **Estado**: borrador
- **Tiempo humano**: est. 3,5h · real —
- **Tiempo IA (ejec.)**: est. 0,40h · real —
- **Supervisión**: est. 0,10h (≈25 % IA) · real —
- **Previsión IA**: 140k in / 21k out tok · 1,5 € tokens · coste tarea 176 €
- **Dependencias**: T-04 (cierre del tramo R1 y su revisión)
- **Archivos**: `agent-kits/shared/knowledge-find.py`
- **Verificación**:
  - `python agent-kits/shared/knowledge-find.py --contexto "Refactor del plugin" --iniciativa plugin-refactor --json > "$CAPTURAS/kf-despues.json" && diff "$CAPTURAS/kf-antes.json" "$CAPTURAS/kf-despues.json"` → vacío · lo mismo con `--tipo adr --limit 0 --json` y con `--doctrina --area estimacion --limit 0 --json`
  - `python skills/code-health/scripts/code-health.py . --exclude-tests --exclude-path interop --json --baseline docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline-2.json` → `funciones largas` «↓ mejora»; nada «↑ empeora» salvo `edad máx. TODO (días)`
  - `python skills/code-health/scripts/code-health.py . --exclude-tests --json --top 1000` → funciones > 30 líneas en `knowledge-find.py` ≤ 1, ninguna > 60
  - Suite: pipeline `-rA | sort` → `diff "$CAPTURAS/suite-antes.txt" -` vacío · `python -m pytest -q tests/test_knowledge_index.py -p no:cacheprovider` → verde (copia guardada intacta)
  - `grep -n "add_argument\|sys.exit\|return [0-9]" agent-kits/shared/knowledge-find.py` antes/después → `diff` vacío · `python scripts/lint_plugin.py` → `0 errores` · `python scripts/export-interop.py --check` → `48 ficheros al día`

**Criterios de aceptación**
- [ ] `knowledge-find.py`: funciones > 30 líneas ≤ 1 (hoy 3), ninguna nueva > 60
- [ ] Tres capturas `--json` byte-idénticas (contexto+iniciativa · adr · doctrina) — CA-08
- [ ] Suite idéntica por test; `tests/test_knowledge_index.py` verde sin tocar; bloque `celdas_md` sin cambio de texto
- [ ] CA-09: sin diff en `agents/`, `commands/`, `skills/*/SKILL.md`

**Subtareas**
- [ ] Partir `main()`: parseo · resolución de root/corpus · despacho por modo (`--show` / `--related` / búsqueda) · render
- [ ] Partir las otras dos funciones largas por responsabilidad (una por función)
- [ ] `Verificación` completa con salidas pegadas; commit `T-05: …`

**Notas**: El `--json` es API interna del brief (`task-brief.py`) y del hook `session-context.sh`: un cambio de clave rompe dos consumidores sin que la suite de este fichero lo vea — por eso la captura es la puerta.

### T-06 — C-02 (2/4): `doctor.py` — 8 funciones largas → ≤ 4

- **Descripción**: `agent-kits/shared/doctor.py` (942 líneas; `bloque_plugin()` `:252`, 87 líneas): 8 funciones > 30 líneas → ≤ 4, ninguna nueva > 60. Contrato congelado: veredictos ✅/⚠️/❌ por línea, `--json`, exit 1 si hay ❌, texto de los arreglos sugeridos. `celdas_md` / `filas_knowledge_index` / `lint_knowledge_index` (`:644-753`, copia guardada byte a byte con `lint_plugin.py`) **no se tocan**.
- **Changelog**: `/doctor` queda partido en funciones cortas por bloque de diagnóstico; veredictos, `--json` y exit code son los mismos.
- **Estado**: borrador
- **Tiempo humano**: est. 3,5h · real —
- **Tiempo IA (ejec.)**: est. 0,40h · real —
- **Supervisión**: est. 0,10h (≈25 % IA) · real —
- **Previsión IA**: 140k in / 21k out tok · 1,5 € tokens · coste tarea 176 €
- **Dependencias**: T-05
- **Archivos**: `agent-kits/shared/doctor.py`
- **Verificación**:
  - `python agent-kits/shared/doctor.py --json > "$CAPTURAS/doctor-despues.json"; diff "$CAPTURAS/doctor-antes.json" "$CAPTURAS/doctor-despues.json"` → vacío (si el JSON lleva marca de tiempo, filtrarla con `python -c` en ambos lados y decirlo) · `python agent-kits/shared/doctor.py > "$CAPTURAS/doctor-despues.txt"; diff "$CAPTURAS/doctor-antes.txt" "$CAPTURAS/doctor-despues.txt"` → vacío
  - `python skills/code-health/scripts/code-health.py . --exclude-tests --exclude-path interop --json --baseline docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline-2.json` → `funciones largas` «↓ mejora»; nada «↑ empeora» salvo `edad máx. TODO (días)`
  - `python skills/code-health/scripts/code-health.py . --exclude-tests --json --top 1000` → funciones > 30 líneas en `doctor.py` ≤ 4, ninguna > 60
  - Suite idéntica (`diff suite-antes.txt`) · `python -m pytest -q agent-kits/shared/test_doctor.py tests/test_knowledge_index.py -p no:cacheprovider` → verde sin tocar
  - `grep -n "add_argument\|sys.exit\|return [0-9]" agent-kits/shared/doctor.py` antes/después → `diff` vacío · `python scripts/lint_plugin.py` → `0 errores`

**Criterios de aceptación**
- [ ] `doctor.py`: funciones > 30 líneas ≤ 4 (hoy 8), ninguna nueva > 60
- [ ] Salida texto y `--json` de `/doctor` byte-idénticas sobre este repo; exit code igual
- [ ] Bloques `--8<--` (`celdas_md` y criterio del índice de knowledge) sin cambio de texto: `tests/test_knowledge_index.py` verde
- [ ] Suite idéntica por test; CA-09 sin diff en prosa de piezas

**Subtareas**
- [ ] `bloque_plugin()` → una función por comprobación (registro del plugin · hooks · statusline · versión) + un ensamblador
- [ ] Las otras 7 largas: partir por veredicto, reutilizando el patrón «comprueba → (icono, texto, arreglo)»
- [ ] `Verificación` completa con salidas pegadas; commit `T-06: …`

**Notas**: `/doctor` es puerta (`exit 1` si hay ❌): el texto de cada línea es contrato de facto para quien lo lee. T-12 (nombre real del comando) y T-17 tocan después este fichero ya partido — por eso van detrás en el grafo.

### T-07 — C-02 (3/4): `build_dashboard.py` — 8 funciones largas → ≤ 4

- **Descripción**: `skills/roadmap-dashboard/scripts/build_dashboard.py` (613 líneas; `render_html()` `:372` 93 líneas, `scan()` `:228` 85): 8 funciones > 30 líneas → ≤ 4, ninguna nueva > 60. Contrato congelado: HTML, MD y JSON **byte-idénticos** para el mismo `docs/roadmap/`; flags; exit codes. Consumidores: `/roadmap-status`, `/pm-backlog`, `/roadmap-metrics`, `/roadmap-brief`.
- **Changelog**: El generador del dashboard del roadmap queda partido en funciones cortas por sección; HTML, Markdown y JSON que produce son los mismos byte a byte.
- **Estado**: borrador
- **Tiempo humano**: est. 3,5h · real —
- **Tiempo IA (ejec.)**: est. 0,40h · real —
- **Supervisión**: est. 0,10h (≈25 % IA) · real —
- **Previsión IA**: 140k in / 21k out tok · 1,5 € tokens · coste tarea 177 €
- **Dependencias**: T-06
- **Archivos**: `skills/roadmap-dashboard/scripts/build_dashboard.py`
- **Verificación**:
  - `python skills/roadmap-dashboard/scripts/build_dashboard.py docs/roadmap --json > "$CAPTURAS/dash-despues.json"; diff "$CAPTURAS/dash-antes.json" "$CAPTURAS/dash-despues.json"` → vacío · ídem con la salida MD y el HTML (`--out "$CAPTURAS/dash-despues.html"` o el flag real del script; `diff` vacío). Si el HTML/JSON lleva fecha de generación, comparar tras filtrarla y decirlo
  - `python skills/code-health/scripts/code-health.py . --exclude-tests --exclude-path interop --json --baseline docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline-2.json` → `funciones largas` «↓ mejora»; nada «↑ empeora» salvo `edad máx. TODO (días)`
  - `python skills/code-health/scripts/code-health.py . --exclude-tests --json --top 1000` → funciones > 30 líneas en `build_dashboard.py` ≤ 4, ninguna > 60
  - Suite idéntica (`diff suite-antes.txt`) · `python -m pytest -q tests/test_dashboard.py -p no:cacheprovider` → verde sin tocar
  - `grep -n "add_argument\|sys.exit\|return [0-9]" skills/roadmap-dashboard/scripts/build_dashboard.py` antes/después → `diff` vacío · `python scripts/lint_plugin.py` → `0 errores`

**Criterios de aceptación**
- [ ] `build_dashboard.py`: funciones > 30 líneas ≤ 4 (hoy 8), ninguna nueva > 60
- [ ] HTML, MD y JSON byte-idénticos sobre el `docs/roadmap/` actual (CA-08)
- [ ] Suite idéntica por test; `tests/test_dashboard.py` sin cambios (CA-04)
- [ ] CA-09 sin diff en prosa de piezas

**Subtareas**
- [ ] `scan()` → lectura de frontmatters · agregación por iniciativa · métricas de proceso (tres funciones)
- [ ] `render_html()` → cabecera/estilos · tabla de iniciativas · bloque de métricas (plantillas por sección)
- [ ] Las otras 6 largas por responsabilidad; `Verificación` completa con salidas pegadas; commit `T-07: …`

**Notas**: T-17 añade después a `render_proceso_md` (`:582`) el agregado de `fuente: estimado`: se hace sobre el fichero ya partido (arista T-07 → T-17).

### T-08 — C-02 (4/4): `lint_plugin.py` — `lint()` y las otras 8 funciones largas → ≤ 5

- **Descripción**: `scripts/lint_plugin.py` (969 líneas; `lint()` `:397`, 114 líneas): 9 funciones > 30 líneas → ≤ 5, ninguna nueva > 60. Es la **puerta de la CI y de `release.py`**: el texto exacto de avisos y errores, el resumen final (`lint_plugin: 9 agentes · 0 errores · 3 avisos`) y los exit codes son contrato. `celdas_md` y el criterio del índice de knowledge (`:546-655`, bloques `--8<--` guardados) y el criterio de consola (`:109-305`, guardado por `tests/test_console_encoding.py`) **no se tocan**. Va el último de la fase para que T-10 y T-16 lo toquen una sola vez.
- **Changelog**: El linter del plugin queda partido en una comprobación por función; avisos, errores, resumen y exit code son idénticos a los de antes.
- **Estado**: borrador
- **Tiempo humano**: est. 3,5h · real —
- **Tiempo IA (ejec.)**: est. 0,40h · real —
- **Supervisión**: est. 0,10h (≈25 % IA) · real —
- **Previsión IA**: 140k in / 21k out tok · 1,5 € tokens · coste tarea 177 €
- **Dependencias**: T-07
- **Archivos**: `scripts/lint_plugin.py`
- **Verificación**:
  - `python scripts/lint_plugin.py > "$CAPTURAS/lint-despues.txt" 2>&1; echo $? ; diff "$CAPTURAS/lint-antes.txt" "$CAPTURAS/lint-despues.txt"` → mismo exit code y `diff` vacío (incluido `lint_plugin: 9 agentes · 0 errores · 3 avisos`)
  - `python skills/code-health/scripts/code-health.py . --exclude-tests --exclude-path interop --json --baseline docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline-2.json` → `funciones largas` «↓ mejora»; nada «↑ empeora» salvo `edad máx. TODO (días)`
  - `python skills/code-health/scripts/code-health.py . --exclude-tests --json --top 1000` → funciones > 30 líneas en `lint_plugin.py` ≤ 5, ninguna > 60; **y suma de los cinco hotspots ≤ 16** (CA-01: cierre del objetivo §8)
  - Suite idéntica (`diff suite-antes.txt`) · `python -m pytest -q tests/test_lint_plugin.py tests/test_knowledge_index.py tests/test_console_encoding.py -p no:cacheprovider` → verde sin tocar
  - `grep -n "add_argument\|sys.exit\|return [0-9]" scripts/lint_plugin.py` antes/después → `diff` vacío · `python scripts/release.py --dry-run` → exit 0 (cierre del tramo R2)

**Criterios de aceptación**
- [ ] `lint_plugin.py`: funciones > 30 líneas ≤ 5 (hoy 9), ninguna nueva > 60; `lint()` es un despachador de comprobaciones con nombre
- [ ] CA-01: suma de funciones > 30 líneas en los cinco hotspots ≤ 16 (hoy 32) — se pega la cifra por fichero
- [ ] Salida y exit code del linter byte-idénticos; bloques guardados (`celdas_md`, índice de knowledge, criterio de consola) sin cambio de texto
- [ ] `release.py --dry-run` exit 0; suite idéntica por test; CA-09 sin diff en prosa

**Subtareas**
- [ ] `lint()` → `comprobar_<x>(root)` por familia de comprobación (frontmatter · grafo `dependencies` · colisiones · hooks · evals · descripciones · consola) devolviendo `(errores, avisos)`; `lint()` agrega e imprime
- [ ] Las otras 8 largas por responsabilidad
- [ ] `Verificación` completa (incluida la suma CA-01) con salidas pegadas; commit `T-08: …`; cierre del tramo R2 → revisión (T-20)

**Notas**: T-10 (bloque no registrado → error) y T-16 (rutas · `/comandos` · filas con puerta) añaden comprobaciones nuevas **después**, como funciones nuevas sobre el despachador ya partido — no se refactoriza dos veces.

---

## Fase 3 — Un solo mecanismo de copias declaradas (O1)

**Estado**: borrador · **Estimado**: 4,0h · **Real**: — · **Coste est.**: 202 € · **Tokens est.**: 239k · **Tramo**: R3

> **C-03 encogida** (corrección verificada del `architect`, `design.md` §1): no hay copias accidentales. Dos de los cuatro pares del §2 son el patrón «canónico por ruta + respaldo local» ya declarado (mecanismo C, **sin guardarraíl**) y dos no son código (`import` + docstring `Uso:`/`Exit:`). El trabajo es **unificar cuatro mecanismos de guardarraíl en uno** (O1, `ADR-016`): registro + un test de identidad + comprobación del linter. La `Verificación` va sobre registro, test y linter — **no** sobre `code-health --baseline` (el 7,6 % no baja y está fuera de objetivo, spec §7). **Arista cumplida:** `design.md` `aprobado` (2026-09-10, condición 1 del go).

### T-09 — C-03 (1/2): registro `agent-kits/shared/copias.json` + `tests/test_copias_declaradas.py`

- **Descripción**: crear el registro (una entrada por bloque: canónico, N rutas, mecanismo, centinelas `--8<--` o rango, `no_codigo` cuando aplique) con las **5 unidades reales** — A: `criterio de consola` (`lint_plugin.py` ↔ `tests/test_console_encoding.py`), `celdas_md` (`lint_plugin` ↔ `doctor` ↔ `knowledge-find`), `criterio del índice de knowledge` (`lint_plugin` ↔ `doctor`); B: `REVISION_HDR_PATTERN` (`ledger-lint.py:179` → `task-brief.py:576`, `jira-flow.py:231`); C: `glob_to_regex` (`confluence-scope.py:121` → `scope-check.py:46-77`, `review-lens-select.py:99-131`) y `piezas()` (`evals/check.py:108` → `lint_plugin.py:905`); D: `sin_vallas` (`ledger-lint.py:101` ↔ `changelog-sync.py:120`) — y los **2 pares no-código** (`export-skills.py:36-43` ↔ `jira-flow.py:83-90` · `code-health.py:27-40` ↔ `deps-inventory.py:29-40`) declarados `"no_codigo": true`. **Un** test recorre el registro y afirma identidad byte a byte tras normalizar `\r\n` → `\n`; **falla** si divergen. Para C y D, el respaldo local se delimita con centinelas `--8<--` (sin cambiar su texto funcional); A y B se registran tal cual. **Decisión del plan** (pregunta abierta 1 del diseño): `sin_vallas` = dos copias registradas como bloque (mecanismo A), no canónico + respaldo.
- **Changelog**: Las copias de código compartidas entre scripts del plugin quedan declaradas en un registro (`copias.json`) y un único test comprueba que siguen idénticas byte a byte.
- **Estado**: borrador
- **Tiempo humano**: est. 2,5h · real —
- **Tiempo IA (ejec.)**: est. 0,31h · real —
- **Supervisión**: est. 0,08h (≈25 % IA) · real —
- **Previsión IA**: 109k in / 16k out tok · 1,1 € tokens · coste tarea 126 €
- **Dependencias**: T-08 (las copias cambian de línea al partir funciones: registrar después) · `design.md` `aprobado` (cumplida)
- **Tipo**: test
- **Archivos**: `agent-kits/shared/copias.json` (nuevo), `tests/test_copias_declaradas.py` (nuevo), `agent-kits/shared/scope-check.py`, `skills/adversarial-review/scripts/review-lens-select.py`, `evals/check.py`, `scripts/lint_plugin.py`, `agent-kits/shared/ledger-lint.py`, `skills/changelog-sync/scripts/changelog-sync.py` (centinelas/comentario de declaración), `agent-kits/shared/task-brief.py`, `skills/jira-sync/scripts/jira-flow.py` (comentario de declaración), `agent-kits/shared/README.md` (una línea: qué es `copias.json`)
- **Verificación**:
  - `python -m pytest -q tests/test_copias_declaradas.py -p no:cacheprovider` → verde; nº de unidades comprobadas = 5 bloques + 2 `no_codigo` (el test lo imprime o lo parametriza)
  - Mutante: cambiar un byte en `skills/adversarial-review/scripts/review-lens-select.py` dentro del bloque `glob_to_regex` → `FAILED … glob_to_regex` (salida pegada); revertir
  - `python -c "import json; d=json.load(open('agent-kits/shared/copias.json')); print(len(d['bloques']), sum(1 for b in d['bloques'] if b.get('no_codigo')))"` → `7 2`
  - `grep -rn "sin_vallas\|_REVISION_HDR_FALLBACK" --include=*.py . | grep -v "/.venv/\|/interop/" | awk -F: '{print $1}' | sort -u` → solo rutas presentes en `copias.json`
  - Suite idéntica por test (`diff suite-antes.txt` — la única línea nueva permitida es el propio `test_copias_declaradas`) · `python -m pytest -q tests/test_knowledge_index.py tests/test_console_encoding.py skills/changelog-sync/scripts/test_changelog_sync.py agent-kits/shared/test_task_brief.py skills/jira-sync/scripts/test_jira_flow.py -p no:cacheprovider` → verde (los guardarraíles previos siguen; no se borran)
  - `python scripts/lint_plugin.py` → `0 errores` · `python scripts/export-interop.py --check` → `48 ficheros al día`

**Criterios de aceptación**
- [ ] CA-05: registro con 5 unidades + 2 no-código; un test de identidad que **falla** con mutante; `grep` de `sin_vallas`/`_REVISION_HDR_FALLBACK` solo devuelve rutas registradas
- [ ] Ningún bloque registrado cambia de texto funcional (A y B: cero cambio; C y D: solo centinelas/comentario alrededor del respaldo)
- [ ] `tests/test_knowledge_index.py` y `tests/test_console_encoding.py` siguen existiendo y en verde (absorbidos, no borrados)
- [ ] Comparación con `\r\n` → `\n` normalizado (Windows `core.autocrlf`, GOT-007); el test corre igual en CI Linux

**Subtareas**
- [ ] Esquema de `copias.json` (`bloques[{id, mecanismo, canonico, copias[{ruta, inicio, fin}], no_codigo?}]`) con los rangos delimitados por centinelas `--8<-- <id>` / `--8<-- fin <id>`
- [ ] Añadir centinelas al respaldo local de `glob_to_regex` (2 sitios), `piezas()`/`_piezas_local()` (2), `sin_vallas` (2); comentario de declaración en `_REVISION_HDR_FALLBACK` (2)
- [ ] `tests/test_copias_declaradas.py` parametrizado por `id`; mutante documentado; una línea en `agent-kits/shared/README.md`
- [ ] `Verificación` con salidas; commit `T-09: …`

**Notas**: El registro es **build-time** (código fuente en git) y no se funde con `.claude/pieces.json` de `ADR-014` (runtime, piezas generadas): dominios y dueños distintos, como dice `ADR-016`. El hueco de `scripts/export-skills.py:399` (`fragmentos_shared` solo escanea `.md`) queda fuera: deuda registrada para `quick-implement`.

### T-10 — C-03 (2/2): `lint_plugin.py` falla ante un bloque `--8<--` o `_*_FALLBACK` no registrado

- **Descripción**: comprobación nueva en el linter (parte **inseparable** de O1 según el usuario en la puerta de diseño): todo marcador `--8<--` y toda constante `_*_FALLBACK` del árbol debe tener fila en `agent-kits/shared/copias.json`; si no, **error** (exit 1). Universo cerrado (marcadores y nombres del propio repo) → nace como error, no aviso. Tolerancias: `interop/**` (generado) y `.venv/**`. Se implementa como `comprobar_copias_declaradas(root)` sobre el despachador partido en T-08.
- **Changelog**: El linter del plugin falla si aparece un bloque de código copiado (`--8<--` o `_*_FALLBACK`) que no esté declarado en `copias.json`.
- **Estado**: borrador
- **Tiempo humano**: est. 1,5h · real —
- **Tiempo IA (ejec.)**: est. 0,19h · real —
- **Supervisión**: est. 0,05h (≈25 % IA) · real —
- **Previsión IA**: 66k in / 10k out tok · 0,7 € tokens · coste tarea 76 €
- **Dependencias**: T-09 (el registro), T-08 (`lint()` partido)
- **Tipo**: test
- **Archivos**: `scripts/lint_plugin.py`, `tests/test_lint_plugin.py`, `docs/CONVENTIONS.md` (una línea en la regla de determinismo/linter: qué comprueba), `docs/en/CONVENTIONS.md`
- **Verificación**:
  - `python scripts/lint_plugin.py; echo $?` → `0 errores`, exit 0, y el resumen sigue `9 agentes · 0 errores · 3 avisos` (con el árbol actual no hay ninguna copia sin registrar)
  - Mutante: añadir `# --8<-- prueba` a un `.py` cualquiera fuera de `interop/` → `python scripts/lint_plugin.py` → `1 error` que nombra fichero y marcador, exit 1 (salida pegada); revertir
  - `python -m pytest -q tests/test_lint_plugin.py -p no:cacheprovider` → previos + 2 nuevos (marcador sin registrar → error · `_*_FALLBACK` sin registrar → error) en verde
  - `python scripts/release.py --dry-run` → exit 0 (cierre del tramo R3) · `python scripts/export-interop.py --check` → `48 ficheros al día`

**Criterios de aceptación**
- [ ] Bloque `--8<--` o `_*_FALLBACK` fuera del registro → error con `fichero:línea` y el `id` esperado; con el árbol actual, 0 errores nuevos
- [ ] La comprobación lee `copias.json` por la misma regla `find` de raíces que el resto del linter (no ruta absoluta)
- [ ] `docs/CONVENTIONS.md` (+EN) nombran la puerta en una línea junto a `export-interop.py --check`
- [ ] `release.py --dry-run` exit 0

**Subtareas**
- [ ] `comprobar_copias_declaradas(root)` → `(errores, avisos)`; tolerancias explícitas
- [ ] 2 tests con mutante en `tests/test_lint_plugin.py`
- [ ] Línea en `CONVENTIONS.md` ES + EN; `Verificación`; commit `T-10: …`; cierre del tramo R3 → revisión (T-20)

**Notas**: La detección es heurística (marcador o nombre), no exhaustiva: su alcance queda escrito en el propio `copias.json` (`"detecta": …`) como pide `design.md` §6. `ADR-016` pasa a `aceptada` con la revisión de dos lentes de este tramo si cierra sin gaps.

---

## Fase 4 — Encadenamiento E1–E11

**Estado**: borrador · **Estimado**: 30,5h · **Real**: — · **Coste est.**: 1.539 € · **Tokens est.**: 1.745k · **Tramo**: R4

> Bloque (b): **sí cambia comportamiento** y cada característica es propia. Orden: quick wins (C-12, C-11) → C-08 → **C-06 antes de C-09 y C-07** (S-6: la matriz es la entrada parseable de C-07 (c) y la lista de dependientes de C-09 — motivo escrito para adelantarla sobre el orden sugerido) → C-13 (ii-b) → C-10 → C-14 (propuesta). **Toda tarea que toque `agents/`, `commands/` o `hooks/` lleva `interop/**` (regenerado con `python scripts/export-interop.py`) y las piezas que describen a la pieza tocada en `Archivos`** — esto ES E2/E3 y esta iniciativa no puede caer en lo mismo. Si R4 supera 10 gaps Important en el intento 1, se parte en R4a (T-11…T-15) / R4b (T-16…T-19) dentro del presupuesto de T-20.

### T-11 — C-12 (E6): exclusiones por defecto en `scope-check.py` + `dev.json` `alcance.excluir`

- **Descripción**: `agent-kits/shared/scope-check.py` reporta «fuera de alcance» en **cada** ciclo los artefactos del orquestador (`CONTINUE-HERE*.md`) y el ruido de `.claude/**` (5-6 ficheros en las tres puertas del día). Lista de exclusión **por defecto en el script** (`CONTINUE-HERE*.md`, `.claude/**`, `docs/knowledge/journal/**` — lo escribe el hook, no la tarea) y override **aditivo** en `.claude/dev.json` `alcance.excluir` (lista de globs, misma forma y mismo `glob_to_regex` que `revision.excluir`). Contrato del `--json` (`slug, base, base_desc, cambiados, en_alcance, fuera_de_alcance, declarados_sin_tocar, patrones`) y exit codes 0/1/2 sin cambio; los excluidos se listan en una clave nueva aditiva `excluidos`.
- **Changelog**: `scope-check.py` deja de marcar como fuera de alcance los ficheros del orquestador (`CONTINUE-HERE*.md`, `.claude/**`, journal) y admite más exclusiones en `dev.json` `alcance.excluir`.
- **Estado**: borrador
- **Tiempo humano**: est. 2,0h · real —
- **Tiempo IA (ejec.)**: est. 0,25h · real —
- **Supervisión**: est. 0,06h (≈25 % IA) · real —
- **Previsión IA**: 88k in / 13k out tok · 0,9 € tokens · coste tarea 101 €
- **Dependencias**: T-10 (cierre de R3). Sin dependencia de código
- **Tipo**: test
- **Archivos**: `agent-kits/shared/scope-check.py`, `agent-kits/shared/test_scope_check.py`, `docs/CONVENTIONS.md` (regla 9: clave `alcance.excluir` de `dev.json`), `docs/en/CONVENTIONS.md`, `commands/setup.md` (si `/setup` ofrece la clave: una línea; si no, decirlo), `interop/**` (si se toca `commands/setup.md`)
- **Verificación**:
  - `touch CONTINUE-HERE.md .claude/prueba-scope.json && git add -N CONTINUE-HERE.md .claude/prueba-scope.json; python agent-kits/shared/scope-check.py docs/roadmap/2026-09-09-plugin-refactor --json --base HEAD | python -c "import json,sys; d=json.load(sys.stdin); print([f for f in d['fuera_de_alcance'] if 'CONTINUE-HERE' in f or '.claude/' in f])"` → `[]` (limpiar después los ficheros de prueba)
  - `python -m pytest -q agent-kits/shared/test_scope_check.py -p no:cacheprovider` → previos + 3 nuevos (default excluye · `dev.json` amplía · `alcance.excluir` mal formado → aviso y default) en verde; mutante: vaciar la lista default → el test del default se pone rojo (salida pegada)
  - `python agent-kits/shared/scope-check.py docs/roadmap/2026-09-09-plugin-refactor --json --base HEAD | python -c "import json,sys; print(sorted(json.load(sys.stdin).keys()))"` → las 8 claves de hoy + `excluidos`
  - `grep -n "add_argument" agent-kits/shared/scope-check.py` antes/después → `diff` vacío · `python scripts/lint_plugin.py` → `0 errores` · `python scripts/export-interop.py --check` → al día

**Criterios de aceptación**
- [ ] CA-18: `CONTINUE-HERE.md` y `.claude/usage-state.json` tocados no salen «fuera de alcance»; `dev.json` `alcance.excluir` amplía; test con mutante
- [ ] La lista default es mínima (tres patrones) y la ampliación es explícita y aditiva (nunca sustituye el default)
- [ ] `docs/CONVENTIONS.md` regla 9 (+EN) documenta `alcance.excluir` con su forma y default
- [ ] Exit codes y claves del `--json` previas idénticas; `excluidos` aditiva

**Subtareas**
- [ ] `EXCLUIR_DEFAULT` + lectura de `dev.json` `alcance.excluir` (misma función de carga tolerante que `review-lens-select.py`)
- [ ] 3 tests; fila en la regla 9 de `CONVENTIONS.md` ES/EN
- [ ] `Verificación`; commit `T-11: …`

**Notas**: Excluir de más convierte la puerta en decorativa: por eso el default no incluye `docs/**` ni nada del código. Los excluidos se siguen listando (clave `excluidos`) para que la revisión los vea.

### T-12 — C-11 (E5): nombre real del comando instalado como plugin (`/custom-agents:<cmd>`) en `/doctor` y en la doc viva

- **Descripción**: instalado desde el marketplace, el nombre del comando es `/custom-agents:dev-cycle`; `/dev-cycle` da «Unknown command» y ni `/doctor` lo comprueba ni la doc lo dice. `doctor.py` (ya partido en T-06) añade una línea: informa del prefijo real cuando detecta instalación como plugin y ⚠️ si la **doc viva** cita la forma corta sin mención al espacio de nombres; distingue «instalado como plugin» de «bundle local en `.claude/`» (donde la forma corta sí funciona) para no generar ruido. Doc viva que cita la forma que funciona: `README.md`, `README.es.md`, `docs/INSTALL.md`, `docs/en/INSTALL.md`, `docs/README.md`, `docs/en/README.md`, `CLAUDE.md`. **Los registros fechados (~104 ficheros con `/dev-cycle`) no se reescriben** (S-5, precedente `sin-motor-externo`).
- **Changelog**: `/doctor` informa del nombre real de los comandos cuando el plugin va instalado desde el marketplace (`/custom-agents:<cmd>`) y la documentación viva cita esa forma.
- **Estado**: borrador
- **Tiempo humano**: est. 3,0h · real —
- **Tiempo IA (ejec.)**: est. 0,35h · real —
- **Supervisión**: est. 0,09h (≈25 % IA) · real —
- **Previsión IA**: 123k in / 18k out tok · 1,3 € tokens · coste tarea 151 €
- **Dependencias**: T-06 (`doctor.py` partido), T-11 (orden del tramo). Coordinar con T-16 (b): el linter tolera ambas formas
- **Archivos**: `agent-kits/shared/doctor.py`, `agent-kits/shared/test_doctor.py`, `README.md`, `README.es.md`, `docs/INSTALL.md`, `docs/en/INSTALL.md`, `docs/README.md`, `docs/en/README.md`, `CLAUDE.md`, `docs/agents/doctor.md` o `commands/doctor.md` (la pieza que describe la línea nueva de `/doctor`: una línea), `evals/cases/command-doctor.json` (si cambia la description), `interop/**` (si se toca `commands/doctor.md`)
- **Verificación**:
  - `python -m pytest -q agent-kits/shared/test_doctor.py -p no:cacheprovider` → previos + 3 nuevos (plugin instalado → línea con `/custom-agents:` · bundle local → sin aviso · doc viva con forma corta → ⚠️ con fichero) en verde
  - `python agent-kits/shared/doctor.py | grep -c "custom-agents:"` → `≥ 1` en esta máquina (plugin instalado en `~/.claude/plugins/cache/daycry/custom-agents/`) y **sin** ⚠️ de doc viva tras editarla
  - `grep -n "custom-agents:dev-cycle\|custom-agents:<" README.md README.es.md docs/INSTALL.md docs/en/INSTALL.md docs/README.md docs/en/README.md CLAUDE.md | wc -l` → `≥ 7` (una mención por fichero como mínimo)
  - `git diff --stat HEAD~1 -- docs/roadmap docs/knowledge CHANGELOG.md CHANGELOG.es.md` → vacío (registros fechados intactos)
  - `python scripts/lint_plugin.py` → `0 errores` · `python evals/check.py` → `0 errores` · `python scripts/export-interop.py --check` → al día

**Criterios de aceptación**
- [ ] CA-17: `/doctor` informa `/custom-agents:<cmd>` cuando el plugin está instalado desde el marketplace y ⚠️ si la doc viva cita solo la forma corta; sin ruido en bundle local
- [ ] Los 7 ficheros de doc viva (ES+EN) citan la forma que funciona al menos en su primera mención de un comando
- [ ] Ningún fichero de `docs/roadmap/`, `docs/knowledge/` ni los CHANGELOG cambia
- [ ] Veredictos, `--json` y exit code previos de `/doctor` idénticos (la línea es aditiva)

**Subtareas**
- [ ] Detección: plugin instalado (ruta de caché del marketplace / `installed_plugins`) vs bundle local (`.claude/agents/` del proyecto)
- [ ] `comprobar_nombre_comandos(...)` con la lista de doc viva; 3 tests
- [ ] Editar los 7 ficheros (misma frase ES/EN: «instalado como plugin, el comando es `/custom-agents:<cmd>`; en bundle local, `/<cmd>`»)
- [ ] `Verificación`; commit `T-12: …`

**Notas**: Si el usuario quiere el barrido completo de los ~104 ficheros, es una característica aparte (~3 h humanas) — no se cuela aquí.

### T-13 — C-08 (E1): `test-plan: n/a (sin UI)` en `planner`, `dev-cycle` y `qa` a la vez

- **Descripción**: hoy `planner` genera `test-plan.md` «si hay UI», `qa` sin `test-plan.md` avisa «hay que (re)generarlo con `planner`» (`agents/qa.md:94`) y `dev-cycle` Fase 3 invoca `qa` siempre: bucle que resuelve la prosa del orquestador. Resolución en las tres piezas: `planner` emite `test-plan: n/a (sin UI)` en el **frontmatter de `improvement-plan.md`** (`ADR-017`, `propuesta`; **este plan ya lo lleva**); `dev-cycle` Fase 3 lo lee antes de despachar `qa`; `qa` con el marcador termina limpio (exit 0, una línea en el informe: «sin UI por diseño»), y sin marcador ni `test-plan.md` avisa **una vez** con el comando que lo fija y termina (no bucle). `coverage-check.py` reconoce el marcador (sigue exit 0 con aviso, ahora sin pedir regenerar). `qa-gate.py` no cambia de contrato (S-7).
- **Changelog**: Una iniciativa sin interfaz declara `test-plan: n/a (sin UI)` en su plan y `qa` termina limpio en vez de pedir un test-plan que no existe.
- **Estado**: borrador
- **Tiempo humano**: est. 3,0h · real —
- **Tiempo IA (ejec.)**: est. 0,35h · real —
- **Supervisión**: est. 0,09h (≈25 % IA) · real —
- **Previsión IA**: 123k in / 18k out tok · 1,3 € tokens · coste tarea 151 €
- **Dependencias**: T-12 (orden del tramo). Conviene tras T-14 en la matriz, pero se hace antes: es la muestra de que el método funciona (§8-bis punto 3)
- **Archivos**: `agents/planner.md`, `commands/dev-cycle.md`, `agents/qa.md`, `agent-kits/planner/templates/improvement-plan.md`, `agent-kits/qa/coverage-check.py`, `agent-kits/qa/test_coverage_check.py` (o el test existente del kit de qa), `docs/agents/planner.md`, `docs/agents/qa.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `evals/cases/agent-planner.json`, `evals/cases/agent-qa.json`, `evals/cases/command-dev-cycle.json`, `interop/**` (regenerado: `agents/` y `commands/` tocados), `docs/knowledge/adr/ADR-017-marcador-test-plan-n-a-en-el-frontmatter-del-plan.md` (pasa a `aceptada` con la revisión del tramo)
- **Verificación**:
  - `grep -n "test-plan: n/a" agents/planner.md commands/dev-cycle.md agents/qa.md agent-kits/planner/templates/improvement-plan.md agent-kits/qa/coverage-check.py` → 5 ficheros con el marcador (mismo literal en los cinco)
  - `python agent-kits/qa/coverage-check.py docs/roadmap/2026-09-09-plugin-refactor/tasks.md docs/roadmap/2026-09-09-plugin-refactor/test-plan.md docs/roadmap/2026-09-09-plugin-refactor/spec.md; echo $?` → exit 0 y una línea «test-plan: n/a (sin UI) declarado en improvement-plan.md» (no «regenéralo con planner»); test con fixture sin marcador → aviso con el comando que lo fija, exit 0
  - `grep -c "regenerarlo con \`planner\`\|(re)generarlo con" agents/qa.md` → `0` (la contradicción E1 desaparece del texto)
  - `python scripts/export-interop.py && python scripts/export-interop.py --check` → al día · `python evals/check.py` → `0 errores` (casos nuevos: «plan sin UI» en planner y qa) · `python scripts/lint_plugin.py` → `0 errores`, `commands/dev-cycle.md` y `agents/qa.md` sin aviso de tamaño
  - `wc -l commands/dev-cycle.md` → `≤ 200` (hoy 198: la lectura del marcador cabe en la Fase 3 sin engordar)

**Criterios de aceptación**
- [ ] CA-14: con `test-plan: n/a (sin UI)` en el plan, `dev-cycle` Fase 3 lo lee y `qa` termina limpio y lo deja en el informe; sin marcador ni `test-plan.md`, aviso único con el comando que lo fija y exit 0 — **se comprueba en vivo sobre esta iniciativa** al llegar a su Fase 3
- [ ] Mismo literal del marcador en las tres piezas, la plantilla del planner y `coverage-check.py` (fila E1 de la matriz de T-14 lo cita)
- [ ] `qa-gate.py` sin cambios; `interop/` regenerado; evals con caso positivo nuevo en `agent-planner.json` y `agent-qa.json`
- [ ] `docs/agents/planner.md`, `docs/agents/qa.md` y `docs/FLOWS.md` (+EN) describen el caso sin UI (E3: quien describe la pieza se actualiza en la misma tarea)

**Subtareas**
- [ ] `planner.md` §0 y plantilla: emitir el marcador cuando no hay UI (en vez de omitir el fichero en silencio)
- [ ] `dev-cycle.md` Fase 3: leer el frontmatter; con marcador, invocar `qa` en modo «sin UI» (o saltarlo dejando la línea en el ledger — decidir y escribirlo)
- [ ] `qa.md` P1 + `coverage-check.py`: salida limpia con marcador; aviso único sin él; test
- [ ] Regenerar `interop/`; evals; docs que describen; `Verificación`; commit `T-13: …`

**Notas**: Este plan es la **primera iniciativa** que lleva el marcador (frontmatter de `improvement-plan.md`, junto a `design:`); hasta que T-13 exista lo lee una persona. `ADR-017` recoge por qué el frontmatter del plan y no el ledger ni un `test-plan.md` vacío.

### T-14 — C-06: matriz de contratos pieza → pieza (`docs/agents/CONTRACTS.md`)

- **Descripción**: fichero nuevo junto a `ROLES.md` (`ROLES.md` dice quién decide; esta dice **cómo se hablan**): una fila por arista invocador → invocado con **columnas fijas** (Arista · Invocador · Invocado · Flags/entrada · Exit codes/salida · Ficheros · Marcadores · **Puerta** ejecutable · Piezas que describen). Cubre como mínimo las **11 aristas E1–E11** (E8 citada como cubierta por `brief-budget` C-05; E11 con puerta «propuesta T-19» o «sin puerta» según decida el usuario) y las reglas «al tocar X regenera/actualiza Y» de `CLAUDE.md` (regla Interop, Bilingüe, Nombres, Linter+tests) con su puerta nombrada (`export-interop.py --check`, `test_ci_manual_copy`, `lint_plugin.py`, …). La tabla es la **fuente parseable** de T-16 (c) y de la lista de dependientes de T-15: formato fijo desde el principio.
- **Changelog**: Nueva matriz `docs/agents/CONTRACTS.md` con los contratos entre piezas del plugin (quién invoca a quién, con qué flags, exit codes, ficheros, marcadores y puerta ejecutable).
- **Estado**: borrador
- **Tiempo humano**: est. 6,0h · real —
- **Tiempo IA (ejec.)**: est. 0,70h · real —
- **Supervisión**: est. 0,18h (≈25 % IA) · real —
- **Previsión IA**: 245k in / 37k out tok · 2,6 € tokens · coste tarea 303 €
- **Dependencias**: T-13 (orden del tramo). **Precede** a T-15 y T-16 (S-6)
- **Tipo**: docs
- **Archivos**: `docs/agents/CONTRACTS.md` (nuevo), `docs/README.md` (fila), `docs/en/README.md` (fila), `docs/agents/ROLES.md` (enlace cruzado en una línea), `agent-kits/shared/copias.json` (una línea de enlace mutuo: el registro de copias es el gemelo de la matriz para el código — pregunta abierta 2 del diseño), `docs/FLOWS.md` y `docs/en/FLOWS.md` (si alguna arista cambia un flujo dibujado)
- **Verificación**:
  - `python -c "import re; t=open('docs/agents/CONTRACTS.md',encoding='utf-8').read(); filas=[l for l in t.splitlines() if l.startswith('| E')]; print(len(filas), all(len(l.split('|'))>=11 for l in filas))"` → `≥ 11 True` (11 aristas, 9 columnas)
  - `grep -c "Puerta" docs/agents/CONTRACTS.md` → `≥ 1` y `python -c "t=open('docs/agents/CONTRACTS.md',encoding='utf-8').read(); import re; print([l[:40] for l in t.splitlines() if l.startswith('| E') and re.search(r'\|\s*\|\s*[^|]*\|\s*$', l)])"` → `[]` (ninguna fila con la columna Puerta vacía; E11 lleva «propuesta T-19» o «sin puerta (decisión del usuario)» escrito, no vacío)
  - Cada ruta de script citada en la matriz existe: `grep -o '\`[a-zA-Z0-9_./-]*\.\(py\|sh\|js\|mjs\)\`' docs/agents/CONTRACTS.md | tr -d '\`' | sort -u | while read f; do [ -e "$f" ] || echo "FALTA $f"; done` → sin salida
  - `grep -n "CONTRACTS.md" docs/README.md docs/en/README.md docs/agents/ROLES.md` → 3 ficheros · lectura: cada fila E1–E10 cita el hueco del §8-bis y la tarea de este ledger que lo cierra
  - `python scripts/lint_plugin.py` → `0 errores` · `python -m pytest -q tests/test_docs_links.py -p no:cacheprovider` si existe (o el test de enlaces que tenga el repo) → verde

**Criterios de aceptación**
- [ ] CA-10: matriz en `docs/agents/` junto a `ROLES.md` con una fila por arista (invocador, invocado, flags, exit codes, ficheros, marcadores, puerta) que cubre E1–E11
- [ ] CA-13 (parte de datos): cada regla «al tocar X regenera/actualiza Y» de `CLAUDE.md` está como fila con su puerta ejecutable nombrada
- [ ] Columnas fijas y parseables (la comprobación de T-16 (c) las lee); ninguna celda Puerta vacía
- [ ] Filas en `docs/README.md` ES+EN y enlace cruzado desde `ROLES.md` y desde `copias.json`

**Subtareas**
- [ ] Inventario de aristas: 9 agentes · 3 orquestadores · ~15 skills · ~20 scripts (leer `dependencies:` de cada agente y los `commands/`); verificar cada fila contra el código (flags reales con `grep add_argument`)
- [ ] Redactar la tabla con las 9 columnas; sección «Reglas de `CLAUDE.md` con puerta»; sección «Cómo se lee / cómo se mantiene» (T-16 la vigila)
- [ ] Filas de índice ES/EN; enlaces cruzados; `Verificación`; commit `T-14: …`

**Notas**: Una matriz que nadie vigila envejece como los 6 ficheros de E3: por eso T-16 (c) la hace lintable y T-15 la usa como fuente de `Archivos`. El coste está en **leer** (verificar cada fila contra el código), no en escribir.

### T-15 — C-09 (E2 + E3): piezas dependientes enumeradas en `Archivos`, regeneradas por `implementer` y comprobadas por la Lente A

- **Descripción**: `planner` (prompt + plantilla de `tasks.md`) exige `interop/**` y **las piezas que describen a la pieza tocada** (según la columna «Piezas que describen» de la matriz de T-14) en `Archivos` de toda tarea que toque `commands/`, `agents/` o `hooks/`; `implementer` regenera `interop/` con `python scripts/export-interop.py` antes de cerrar la tarea; la **Lente A** (`lens-prompts.md`) ejecuta `python scripts/export-interop.py --check` y lo cita ✓/✗ por criterio. `scope-check.py` ya acepta los ficheros generados si están en `Archivos` (patrón `interop/**`, no fichero a fichero, para no engordar el brief — GOT-009).
- **Changelog**: Las tareas que tocan un agente, comando o hook enumeran `interop/**` y las piezas que lo describen; `implementer` regenera `interop/` y la Lente A comprueba `export-interop.py --check`.
- **Estado**: borrador
- **Tiempo humano**: est. 3,0h · real —
- **Tiempo IA (ejec.)**: est. 0,35h · real —
- **Supervisión**: est. 0,09h (≈25 % IA) · real —
- **Previsión IA**: 123k in / 18k out tok · 1,3 € tokens · coste tarea 151 €
- **Dependencias**: T-14 (la lista de dependientes sale de la matriz)
- **Archivos**: `agents/planner.md`, `agent-kits/planner/templates/tasks.md`, `agents/implementer.md`, `skills/adversarial-review/references/lens-prompts.md`, `docs/agents/planner.md`, `docs/agents/implementer.md`, `agent-kits/planner/README.md`, `agent-kits/shared/README.md` (si describe el brief/`Archivos`), `evals/cases/agent-planner.json`, `evals/cases/agent-implementer.json` (si cambia la description), `interop/**` (regenerado: `agents/` tocados)
- **Verificación**:
  - `grep -n "interop/\*\*" agents/planner.md agent-kits/planner/templates/tasks.md agents/implementer.md skills/adversarial-review/references/lens-prompts.md` → 4 ficheros
  - `grep -n "export-interop.py --check" skills/adversarial-review/references/lens-prompts.md agents/implementer.md` → 2 ficheros (la Lente A lo ejecuta; el implementer lo corre en su DoD)
  - `python scripts/export-interop.py && python scripts/export-interop.py --check` → al día · `python evals/check.py` → `0 errores` · `python scripts/lint_plugin.py` → `0 errores` (sin aviso de tamaño en `agents/planner.md`, `agents/implementer.md`)
  - lectura: `docs/agents/planner.md` y `docs/agents/implementer.md` describen la regla nueva (E3: quien describe se actualiza en la misma tarea); la plantilla `tasks.md` del kit lleva el ejemplo `interop/**` en el campo `Archivos` con su comentario guía
  - `python agent-kits/shared/task-brief.py docs/roadmap/2026-09-09-plugin-refactor/tasks.md T-13 | wc -c` → `≤ 10000` (el patrón `interop/**` no dispara el tope del brief)

**Criterios de aceptación**
- [ ] CA-15: plantilla y `planner.md` exigen `interop/**` + piezas que describen cuando la tarea toca `commands/`/`agents/`/`hooks/`; `implementer.md` regenera; `lens-prompts.md` (Lente A) ejecuta `--check` y lo cita ✓/✗
- [ ] La lista de «piezas que describen» se toma de la matriz (T-14), no se improvisa por tarea
- [ ] `interop/` regenerado y `--check` verde; evals en verde; docs que describen actualizadas
- [ ] El brief de una tarea con `interop/**` en `Archivos` sigue bajo el tope de 10.000 caracteres

**Subtareas**
- [ ] `planner.md` (§0 o §2 P5) + plantilla `tasks.md`: regla y ejemplo
- [ ] `implementer.md` DoD: regenerar `interop/` y correr `--check` antes de cerrar la tarea
- [ ] `lens-prompts.md` Lente A: criterio «interop al día» con el comando y ✓/✗
- [ ] Docs que describen; evals; regenerar; `Verificación`; commit `T-15: …`

**Notas**: Decisión de detalle (incógnita de la evaluación): la Lente A **ejecuta** el `--check` ella misma (tiene Bash) y además exige la evidencia del implementer — doble puerta barata.

### T-16 — C-07: linter — rutas citadas existen · `/comandos` citados existen · filas de la matriz con puerta

- **Descripción**: tres comprobaciones nuevas en `scripts/lint_plugin.py` (sobre el despachador partido en T-08): (a) toda ruta de script citada entre acentos graves en `agents/`, `commands/`, `skills/` existe (65 rutas únicas hoy; placeholders `<x>.py`, `<ruta>` tolerados); (b) todo `/comando` citado en la doc existe como `commands/<x>.md` (18 distintos hoy; tolerar `/algo`, `/nombre`, nativos `/clear`, `/agents`, `/reload-plugins`, `/help`, `/config`, y la forma `/custom-agents:<cmd>` de T-12); (c) cada fila de `docs/agents/CONTRACTS.md` tiene la columna **Puerta** no vacía y, si nombra un script, existe. **Nacen como aviso** (corren en la CI y en `release.py`: un falso positivo bloquea releases) y suben a error tras una release limpia — se anota aquí la release en la que suben.
- **Changelog**: El linter avisa si un agente, comando o skill cita una ruta de script o un `/comando` que no existe, y si una fila de la matriz de contratos no tiene puerta ejecutable.
- **Estado**: borrador
- **Tiempo humano**: est. 6,0h · real —
- **Tiempo IA (ejec.)**: est. 0,70h · real —
- **Supervisión**: est. 0,18h (≈25 % IA) · real —
- **Previsión IA**: 245k in / 37k out tok · 2,6 € tokens · coste tarea 303 €
- **Dependencias**: T-08 (`lint()` partido), T-10 (mismo fichero), T-14 (la matriz es la entrada de (c)), T-15 (orden del tramo)
- **Tipo**: test
- **Archivos**: `scripts/lint_plugin.py`, `tests/test_lint_plugin.py`, `docs/CONVENTIONS.md` (regla Linter+tests: las tres comprobaciones), `docs/en/CONVENTIONS.md`, `CLAUDE.md` (fila «Linter + tests»: una frase), `docs/agents/CONTRACTS.md` (sección «cómo se mantiene» cita la puerta)
- **Verificación**:
  - `python scripts/lint_plugin.py; echo $?` → `0 errores`, exit 0, y **0 avisos nuevos** con el árbol actual (el resumen pasa de `3 avisos` solo si se corrige una cita rota real encontrada, que se anota aquí con fichero y ruta)
  - Mutante (a): añadir `` `agent-kits/shared/no-existe.py` `` a un `agents/x.md` → aviso con fichero y ruta; mutante (b): añadir `` `/no-existe` `` a un doc → aviso; mutante (c): vaciar la celda Puerta de una fila E-xx de `CONTRACTS.md` → aviso con la arista (tres salidas pegadas; revertir)
  - `python -m pytest -q tests/test_lint_plugin.py -p no:cacheprovider` → previos + 6 nuevos (positivo y tolerancia por cada comprobación) en verde
  - `python scripts/release.py --dry-run` → exit 0 · `python scripts/export-interop.py --check` → al día

**Criterios de aceptación**
- [ ] CA-11: ruta citada inexistente → aviso con fichero y ruta; con el árbol actual, 0 avisos nuevos (65 rutas existen o son placeholder tolerado)
- [ ] CA-12: `/comando` citado inexistente → aviso; `/algo`, `/nombre`, nativos y `/custom-agents:<cmd>` tolerados
- [ ] CA-13: fila de la matriz sin Puerta → aviso con la arista; script nombrado en Puerta inexistente → aviso
- [ ] Nacen como aviso; `CONVENTIONS.md` (+EN) y `CLAUDE.md` nombran las tres comprobaciones y la regla de subida a error

**Subtareas**
- [ ] `comprobar_rutas_citadas`, `comprobar_comandos_citados`, `comprobar_matriz_contratos` → `(errores=[], avisos)`; listas de tolerancia explícitas y comentadas
- [ ] 6 tests con mutante; línea en `CONVENTIONS.md` ES/EN y `CLAUDE.md`
- [ ] `Verificación`; commit `T-16: …`

**Notas**: (c) es deliberadamente «cada fila tiene Puerta no vacía y el script existe»: más débil de lo que suena, pero lintable hoy (S-6). Si aparece una cita rota real con el árbol actual, se corrige en esta misma tarea y se anota (es exactamente el hueco E3).

### T-17 — C-13 (ii-b): agregado `fuente: estimado` visible en `/roadmap-metrics` y `/retro`; filas estimadas marcadas en `CALIBRATION.md` y fuera de la mediana

- **Descripción**: la cadena de calibración se alimentaba de estimaciones sin que nadie lo viera agregado (E7). `build_dashboard.py` (`render_proceso_md`, `:582`, ya partido en T-07) añade la línea «N de M bloques `generacion:` con `fuente: estimado`» al informe de proceso que consume `/roadmap-metrics` (y una clave aditiva `estimados` en el JSON); `/retro` (`commands/retro.md`, paso 5) marca la fila de `CALIBRATION.md` como `(estimado)` en la celda `tokens/hora` cuando la iniciativa no tiene datos medidos (hoy dice «deja la celda vacía»: se hace explícito y parseable); `usage-meter._ratio_calibrado` **ignora** las filas marcadas `(estimado)` al calcular la mediana (test), y las 9 filas actuales se auditan una a una contra sus `generacion:` para marcar las que fueron estimadas (anotando aquí cuáles).
- **Changelog**: `/roadmap-metrics` muestra cuántos bloques de medición son estimados y no medidos; `/retro` marca las filas estimadas de `CALIBRATION.md` y el ratio calibrado deja de contarlas.
- **Estado**: borrador
- **Tiempo humano**: est. 1,5h · real —
- **Tiempo IA (ejec.)**: est. 0,19h · real —
- **Supervisión**: est. 0,05h (≈25 % IA) · real —
- **Previsión IA**: 66k in / 10k out tok · 0,7 € tokens · coste tarea 76 €
- **Dependencias**: T-07 (`build_dashboard.py` partido), T-04 (`usage-meter.py` ya tocado en R1), T-16 (orden del tramo)
- **Archivos**: `skills/roadmap-dashboard/scripts/build_dashboard.py`, `tests/test_dashboard.py`, `agent-kits/shared/usage-meter.py`, `agent-kits/shared/test_usage_meter.py`, `commands/retro.md`, `docs/roadmap/CALIBRATION.md` (marcas `(estimado)` en las filas que lo fueron), `docs/observability.md`, `docs/en/observability.md`, `commands/roadmap-metrics.md` (una línea, si describe la salida), `skills/roadmap-dashboard/SKILL.md` (una línea), `evals/cases/command-retro.json` (si cambia la description), `interop/**` (regenerado: `commands/` tocados)
- **Verificación**:
  - `python skills/roadmap-dashboard/scripts/build_dashboard.py docs/roadmap --json | python -c "import json,sys; d=json.load(sys.stdin); print(d['proceso']['estimados'] if 'proceso' in d else d.get('estimados'))"` → `{"estimados": N, "total": M}` con `N ≤ M` y ambos > 0 (ajustar la ruta de la clave a la forma real; la cifra se pega)
  - `python skills/roadmap-dashboard/scripts/build_dashboard.py docs/roadmap --md 2>/dev/null | grep -c "fuente: estimado"` → `≥ 1` (línea «N de M bloques…»)
  - `python -m pytest -q tests/test_dashboard.py agent-kits/shared/test_usage_meter.py -p no:cacheprovider` → previos + 3 nuevos (conteo estimados/total · fila `(estimado)` excluida de la mediana · fila sin marca incluida) en verde; mutante: quitar el filtro en `_ratio_calibrado` → rojo (salida pegada)
  - `python agent-kits/shared/usage-meter.py close --artefacto /tmp/y.md 2>/dev/null | python -c "import json,sys; d=json.load(sys.stdin); print(d['ratio_origen'])"` → `CALIBRATION.md (mediana de K)` con K = filas **no** marcadas (cifra pegada junto a la lista de filas marcadas)
  - `grep -c "(estimado)" docs/roadmap/CALIBRATION.md` → nº de filas auditadas como estimadas (anotado aquí con su motivo por fila) · `python scripts/export-interop.py && python scripts/export-interop.py --check` → al día · `python evals/check.py` → `0 errores`

**Criterios de aceptación**
- [ ] CA-19 (ii, parte b): `/roadmap-metrics` muestra «N de M bloques `generacion:` con `fuente: estimado`»; `/retro` marca `(estimado)` en `CALIBRATION.md` cuando no hay medida
- [ ] `_ratio_calibrado` ignora las filas `(estimado)` (test con mutante); el literal `tokens/hora` del encabezado y el parseo de enteros no cambian
- [ ] Las 9 filas actuales de `CALIBRATION.md` auditadas contra sus `generacion:`; las estimadas marcadas y el ratio vigente recalculado en la línea-resumen `> Ratio vigente: …`
- [ ] `docs/observability.md` (+EN) y `commands/retro.md` describen la marca; `interop/` regenerado

**Subtareas**
- [ ] `build_dashboard.py`: contar `fuente:` de todos los `generacion:` del roadmap; línea en `render_proceso_md` y clave aditiva en JSON; test
- [ ] `usage-meter.py` `_ratio_calibrado`: saltar celdas con `(estimado)`; test con mutante
- [ ] `commands/retro.md` paso 5: la marca; auditar las 9 filas y marcar; recalcular la línea-resumen
- [ ] Docs; regenerar `interop/`; `Verificación`; commit `T-17: …`

**Notas**: Cierra C-13 junto con T-04 (ii-a) y la vía rápida (i). La retro de **esta** iniciativa será la primera fila medida en Windows: por eso la marca importa ahora — separa lo medido de lo vendido (LES-007).

### T-18 — C-10 (E4): la Lente C se dispara ante texto controlado por el consumidor que acaba en un prompt o brief

- **Descripción**: `skills/adversarial-review/scripts/review-lens-select.py` mira patrones de código peligroso y stems de ruta; **no ve flujo de datos hacia un prompt** (dio `lente_c: false` tres veces en `project-specialization` F1 cuando el diff abría un canal de texto del consumidor — `.claude/personas/*.md`, `dev.json` — hacia el brief del subagente; la Lente B lo cazó las tres veces). Heurística nueva, **definición operativa**: el diff añade o modifica una lectura de `.claude/**`, `dev.json`, `personas/*.md`, `docs/knowledge/**` o `CONTINUE-HERE*.md` (texto del consumidor) en un fichero que **compone texto para un modelo** (nombre o docstring con `brief`, `prompt`, `persona`, `system`, o `subprocess` hacia `claude -p`) → `lente_c: true` con motivo `tipo: flujo`, fichero y línea. El **caso real de F1** se guarda como fixture y pasa a `true`; la tasa de disparo sobre los **últimos 5 ledgers** se mide antes/después y se anota (criterio: no sube más de un ledger). Válvula: `dev.json` `revision.excluir` (ya existe).
- **Changelog**: La selección de la lente de seguridad reconoce cuando un diff abre un canal de texto controlado por el consumidor hacia un prompt o brief, y lo dispara con el motivo.
- **Estado**: borrador
- **Tiempo humano**: est. 4,0h · real —
- **Tiempo IA (ejec.)**: est. 0,50h · real —
- **Supervisión**: est. 0,13h (≈25 % IA) · real —
- **Previsión IA**: 175k in / 26k out tok · 1,8 € tokens · coste tarea 202 €
- **Dependencias**: T-17 (orden del tramo). Sin dependencia de código. **Candidata a recortar** si el usuario quiere ajustar coste (evaluación): mínimo = detector del caso F1 + válvula
- **Tipo**: test
- **Archivos**: `skills/adversarial-review/scripts/review-lens-select.py`, `skills/adversarial-review/scripts/test_review_lens_select.py`, `skills/adversarial-review/references/lens-c-heuristics.md` (la heurística nueva, con lo que detecta y lo que no), `skills/adversarial-review/SKILL.md` (una línea; ≤ 200 líneas), `evals/cases/skill-adversarial-review.json` (si cambia la description)
- **Verificación**:
  - `python -m pytest -q skills/adversarial-review/scripts/test_review_lens_select.py -p no:cacheprovider` → previos + 4 nuevos (fixture F1 → `true` con `tipo: flujo` · lectura de `.claude/**` en fichero que no compone prompt → `false` · fichero de prompt sin texto del consumidor → `false` · `revision.excluir` apaga el disparo) en verde; mutante: quitar la heurística → el fixture F1 vuelve a `false` (salida pegada)
  - Tasa de disparo: `for s in $(ls -d docs/roadmap/2026-09-* | tail -5); do echo "$s $(python skills/adversarial-review/scripts/review-lens-select.py --files <ficheros del ledger> --json 2>/dev/null | python -c 'import json,sys; print(json.load(sys.stdin)[\"lente_c\"])')"; done` (o el flag `--base` real del script) antes/después → como máximo **un** ledger cambia de `false` a `true` (las dos listas pegadas)
  - `python skills/adversarial-review/scripts/review-lens-select.py --help | grep -c "\-\-"` antes/después → mismo número (sin flags nuevos; salida `lente_c`/`lente_d` + motivos con `tipo: flujo` aditivo)
  - `python scripts/lint_plugin.py` → `0 errores`, `skills/adversarial-review/SKILL.md` ≤ 200 líneas · `python evals/check.py` → `0 errores`

**Criterios de aceptación**
- [ ] CA-16: el fixture del caso real de F1 da `lente_c: true` con motivo `tipo: flujo`, fichero y línea
- [ ] La definición operativa está escrita en `lens-c-heuristics.md` (qué detecta · qué no · cómo se apaga) y el test cubre los tres casos negativos
- [ ] Tasa de disparo sobre los últimos 5 ledgers medida antes/después y anotada; sube como máximo un ledger
- [ ] Forma del `--json` y flags previos idénticos; `tipo: flujo` es un valor nuevo del campo `tipo` existente

**Subtareas**
- [ ] Fixture: diff real de F1 (`git show` del commit que abrió el canal de personas) recortado a lo relevante
- [ ] Heurística `flujo_texto_consumidor(diff)` con las dos listas (fuentes de texto · ficheros que componen prompt); 4 tests
- [ ] Medición antes/después; `lens-c-heuristics.md`; línea en `SKILL.md`; `Verificación`; commit `T-18: …`

**Notas**: Una heurística que «acierta» solo el caso F1 es un test de regresión disfrazado (riesgo de la evaluación): por eso los tres negativos y la tasa medida son criterios, no notas. Confianza **Baja** heredada.

### T-19 — C-14 (E11, propuesta ACEPTADA por el usuario el 2026-09-10 en la puerta del plan): `test_cifras_medidas.py` vigila solo los documentos vivos; los históricos congelan cifra y fecha

- **Descripción**: `tests/test_cifras_medidas.py` compara cada `<!--m:clave=valor-->` de la doc contra `changelog-sync.py --medicion` (corpus **vivo**), y algunas marcas viven en **documentos históricos** — `ADR-012`, el ledger cerrado de `changelog-brief`, `docs/knowledge/README.md` — que citan la medición del día en que se decidió. Resultado verificado hoy cuatro veces: **abrir o cerrar cualquier iniciativa rompe el test** (29 fallos al cerrar la vía rápida; un parche mecánico corrompió tres líneas) y obliga a reescribir prosa de documentos que no deberían moverse (este mismo plan movió `ledgers_totales` 33 → 34 al nacer). Propuesta del plan (la más barata de las dos vías del orquestador; **el usuario decide en la puerta**): los documentos **vivos** (`skills/changelog-sync/references/medicion-escalera.md`, `SKILL.md`, `CONVENTIONS.md`) siguen con `<!--m:…-->`; los **históricos** pasan a `<!--m?:histórico medido el AAAA-MM-DD-->` con la cifra congelada y su fecha (forma que el test ya acepta), y el test gana un caso: una marca `m:` en un fichero de `docs/roadmap/**` cerrado o `docs/knowledge/adr/**` es **aviso** («esto es histórico: congela con fecha»). `changelog-sync.py` no cambia. Alternativa (no elegida, +1,0 h): generar las cifras con fecha de medición en la prosa.
- **Changelog**: Las cifras medidas que viven en documentos históricos (ADR, ledgers cerrados) quedan congeladas con su fecha y ya no rompen la suite al abrir o cerrar una iniciativa; las vivas siguen vigiladas.
- **Estado**: borrador
- **Tiempo humano**: est. 2,0h · real —
- **Tiempo IA (ejec.)**: est. 0,25h · real —
- **Supervisión**: est. 0,06h (≈25 % IA) · real —
- **Previsión IA**: 88k in / 13k out tok · 0,9 € tokens · coste tarea 101 €
- **Dependencias**: T-18 (orden del tramo). **Decisión del usuario en la puerta del plan**: si se descarta, pasa a `cancelado` con motivo, E11 queda en la matriz de T-14 como «sin puerta» y en la retro; el presupuesto baja a 72,0 h base / 86,4 h con margen
- **Tipo**: test
- **Archivos**: `tests/test_cifras_medidas.py`, `docs/knowledge/adr/ADR-012-resumen-del-changelog-lo-escribe-quien-cierra-la-tarea.md`, `docs/roadmap/2026-09-04-changelog-brief/tasks.md`, `docs/knowledge/README.md` (fila de ADR-012), `docs/roadmap/2026-09-04-sin-motor-externo/tasks.md` (si tiene marcas vivas: comprobar con `grep '<!--m:'`), `skills/changelog-sync/references/medicion-escalera.md` (sección «qué es vivo y qué es histórico»: 3 líneas), `docs/agents/CONTRACTS.md` (fila E11: puerta = este test)
- **Verificación**:
  - `python -m pytest -q tests/test_cifras_medidas.py -p no:cacheprovider` → verde antes de cambiar nada (estado de partida pegado) y verde después
  - Prueba de la clase: crear un `docs/roadmap/2099-01-01-prueba/tasks.md` cerrado con dos tareas y campo `Changelog:` (mueve `ledgers_cerrados`, `tareas`, `camino_changelog`) → `python -m pytest -q tests/test_cifras_medidas.py` → **verde** (solo los vivos se comparan y no citan esas claves, o las citan con fecha); borrar la prueba. Hoy el mismo experimento da rojo: se pega el «antes» (nº de fallos) y el «después» (0)
  - `grep -rn "<!--m:" docs/knowledge/adr docs/roadmap/2026-09-04-changelog-brief/tasks.md docs/knowledge/README.md | wc -l` → `0` (todo histórico congelado como `m?:` con fecha) · `grep -rn "<!--m:" skills/changelog-sync docs/CONVENTIONS.md docs/en/CONVENTIONS.md | wc -l` → `≥ 10` (los vivos siguen vigilados)
  - Mutante: cambiar una cifra viva en `medicion-escalera.md` → rojo con `fichero:línea:clave=valor` (salida pegada); revertir
  - `python skills/changelog-sync/scripts/changelog-sync.py --medicion --json | python -c "import json,sys; print(len(json.load(sys.stdin)))"` antes/después → mismo número de claves (el script no cambia) · `python scripts/lint_plugin.py` → `0 errores`

**Criterios de aceptación**
- [ ] Abrir/cerrar una iniciativa de prueba no rompe `test_cifras_medidas.py` (experimento pegado: antes N fallos, después 0)
- [ ] Ninguna marca `m:` viva en ADR, ledgers cerrados ni índice de la memoria; las históricas llevan `m?:` con la fecha de medición y la cifra intacta (sin reescribir la prosa histórica más allá del marcador)
- [ ] Los documentos vivos siguen vigilados: mutante rojo con `fichero:línea`
- [ ] El test avisa ante una marca `m:` nueva en `docs/roadmap/**` cerrado o `docs/knowledge/adr/**`; `changelog-sync.py` sin cambios

**Subtareas**
- [ ] Inventario `grep -rn '<!--m:'` clasificado vivo/histórico (pegado aquí)
- [ ] Congelar históricos (`m?:histórico medido el …`, cifra intacta); caso nuevo del test (aviso por ubicación); 3 líneas en `medicion-escalera.md`
- [ ] Experimento de la clase (ledger de prueba) antes/después; fila E11 de la matriz; `Verificación`; commit `T-19: …`

**Notas**: Descubierto hoy (no está en `analysis.md` §8-bis): se propone **con su coste** y no se cuela. La doctrina previa del ledger de `changelog-brief` («la marca vigila la medición VIVA, por eso se actualiza el número») sigue en pie para los vivos; lo que cambia es reconocer que un ADR o un ledger cerrado no es un documento vivo. Si el usuario prefiere la otra vía (cifras generadas con fecha), esta tarea se re-estima (+1,0 h) antes de abrirse.

---

## Fase 5 — Proceso: revisión por tramo, corrección y cierre

**Estado**: borrador · **Estimado**: 14,0h · **Real**: — · **Coste est.**: 707 € · **Tokens est.**: 864k · **Tramo**: —

> Líneas de proceso P-2, P-3 y P-4 de la evaluación (**condición 2 del go: no se recortan**; 16 % del base). P-1 (`architect`) ya está hecha fuera del plan (`design.md` `aprobado`, 0,71 h IA / 9,16 € medidos).

### T-20 — P-2: revisión de dos lentes por tramo (R1 · R2 · R3 · R4)

- **Descripción**: al cerrar cada tramo, `/dev-cycle` invoca la skill `adversarial-review` (Lentes A y B en paralelo con contexto fresco; C y D condicionales por `review-lens-select.py` — T-18 cambia su criterio a partir de R4). En un refactor (R1-R3) la **Lente B** (regresiones) es la que trabaja, con las capturas de contratos (`$CAPTURAS/*-antes` vs `*-despues`) y `suite-antes.txt` como evidencia; en R4 la **Lente A** revisa contra esta spec, la matriz de T-14 y `ROLES.md`. Traza obligatoria en este ledger: «Revisión de dos lentes — intento N» por tramo, con gaps graduados Critical/Important/Minor. Bucle acotado a 3 por tramo. Con el tramo cerrado sin gaps pendientes, las entradas `propuesta` de la iniciativa se promueven (`ADR-016` en R3; `ADR-017` en R4).
- **Changelog**: Cada tramo del refactor pasa una revisión adversarial de dos lentes con las capturas de contratos como evidencia, y la traza queda en el ledger.
- **Estado**: borrador
- **Tiempo humano**: est. 6,0h · real —
- **Tiempo IA (ejec.)**: est. 0,75h · real —
- **Supervisión**: est. 0,19h (≈25 % IA) · real —
- **Previsión IA**: 263k in / 40k out tok · 2,8 € tokens · coste tarea 303 €
- **Dependencias**: R1 → tras T-04 · R2 → tras T-08 · R3 → tras T-10 · R4 → tras T-19 (o T-18 si C-14 se descarta). La tarea se marca `completado` cuando los cuatro tramos tienen su traza
- **Archivos**: `docs/roadmap/2026-09-09-plugin-refactor/tasks.md` (trazas), `docs/knowledge/adr/ADR-016-copias-declaradas-con-test-de-identidad.md` y `ADR-017-…` (`estado` → `aceptada (validada: revisión de dos lentes, AAAA-MM-DD, intento N)`), `docs/knowledge/README.md` (estado en las filas)
- **Verificación**:
  - `grep -c "Revisión de dos lentes — intento" docs/roadmap/2026-09-09-plugin-refactor/tasks.md` → `≥ 4` (una traza por tramo como mínimo)
  - `python agent-kits/shared/ledger-lint.py docs/roadmap/2026-09-09-plugin-refactor/tasks.md` → exit 0 tras cada traza
  - `python skills/adversarial-review/scripts/review-lens-select.py --base <inicio-del-tramo> --json` por tramo → `lente_c`/`lente_d` con motivo, pegado en la traza (R1-R3 se espera `false`/`false` salvo `usage-meter.py` en R1; R4 toca `scope-check`/`review-lens-select`: decisión pegada)
  - lectura: cada traza lista gaps por severidad, el rebate con evidencia o la corrección (T-21) y el nº de intento; al cerrar R3, `grep -n "^estado:" docs/knowledge/adr/ADR-016-*.md` → `aceptada (validada: revisión de dos lentes, …)`

**Criterios de aceptación**
- [ ] Cuatro tramos revisados con traza «Revisión de dos lentes — intento N» y gaps graduados; ninguno supera 3 intentos
- [ ] Lente B en R1-R3 recibe las capturas de contratos y `suite-antes.txt` como evidencia (citadas en la traza)
- [ ] Lente A en R4 revisa contra spec, `CONTRACTS.md` y `ROLES.md`; `export-interop.py --check` citado ✓/✗ (T-15 en vivo)
- [ ] `ADR-016` y `ADR-017` promovidos según el contrato de `knowledge-write.md` si el tramo cierra sin gaps pendientes

**Subtareas**
- [ ] R1 tras T-04 · R2 tras T-08 · R3 tras T-10 · R4 tras T-19 (o R4a/R4b si > 10 Important en el intento 1)
- [ ] Traza por tramo; promoción de ADR; `Verificación`

**Notas**: `memory-retrieval` midió +66 % de IA real por tres revisiones (38 gaps) no presupuestadas: esta línea y T-21 existen para absorberlo. El orquestador lleva el contador de intentos y el worklog `[revisión]`.

### T-21 — P-3: corrección post-revisión (igual a la revisión)

- **Descripción**: corregir los gaps Critical e Important de cada tramo (los Minor se aceptan como deuda con motivo o se corrigen si son de una línea), re-ejecutar la `Verificación` de las tareas afectadas y la puerta del tramo (`release.py --dry-run`), y actualizar la traza del intento. En el bloque (a) una corrección **nunca** toca un test existente ni un contrato congelado: si la revisión pide eso, es un cambio de comportamiento → fuera de (a), se anota y va por su cauce. Un gap rebatido con evidencia (comando + salida) cuenta como resuelto.
- **Changelog**: Los gaps de la revisión adversarial de cada tramo se corrigen o se rebaten con evidencia antes de cerrar el tramo, sin tocar tests existentes ni contratos congelados.
- **Estado**: borrador
- **Tiempo humano**: est. 6,0h · real —
- **Tiempo IA (ejec.)**: est. 0,75h · real —
- **Supervisión**: est. 0,19h (≈25 % IA) · real —
- **Previsión IA**: 263k in / 40k out tok · 2,8 € tokens · coste tarea 303 €
- **Dependencias**: T-20 (cada tramo, tras su intento 1). Se marca `completado` cuando los cuatro tramos han cerrado su bucle
- **Archivos**: los de las tareas afectadas en cada tramo (se listan en la traza), `docs/roadmap/2026-09-09-plugin-refactor/tasks.md` (traza actualizada), `interop/**` si la corrección toca `agents/`/`commands/`
- **Verificación**:
  - Por tramo: re-ejecutar la `Verificación` completa de cada tarea tocada por la corrección → mismas salidas esperadas (pegadas en la traza del intento N+1)
  - Bloque (a): `git diff --stat <inicio-del-tramo>..HEAD -- tests agent-kits/shared/test_*.py skills/*/scripts/test_*.py` → solo `test_code_health.py` (T-01/T-02) y `tests/test_copias_declaradas.py` (T-09) — ningún test existente tocado por una corrección
  - `python scripts/release.py --dry-run` → exit 0 al cerrar cada tramo · `python scripts/export-interop.py --check` → al día · `python agent-kits/shared/ledger-lint.py docs/roadmap/2026-09-09-plugin-refactor/tasks.md` → exit 0
  - lectura: la traza del intento final de cada tramo lista 0 gaps Critical/Important pendientes (o los aceptados como deuda por el usuario, con motivo)

**Criterios de aceptación**
- [ ] 0 gaps Critical/Important pendientes al cerrar cada tramo (corregidos o rebatidos con evidencia; deuda solo con OK del usuario)
- [ ] Ninguna corrección del bloque (a) modifica un test existente ni un contrato congelado (diff de tests limitado a los tres ficheros declarados)
- [ ] Puertas del tramo en verde tras la corrección: `release.py --dry-run`, `export-interop.py --check`, `ledger-lint`
- [ ] Si la corrección tocó `agents/`/`commands/`, `interop/` regenerado y las piezas que describen actualizadas (E2/E3 en vivo)

**Subtareas**
- [ ] Por tramo: corregir/rebatir · re-verificar tareas afectadas · puerta del tramo · traza intento N+1
- [ ] Anotar deuda aceptada (si la hay) con motivo y dueño

**Notas**: Igual a la revisión por diseño (LES-009, `memory-retrieval`). Si un tramo cierra en el intento 1 sin gaps, las horas no consumidas se declaran en la retro, no se reasignan.

### T-22 — P-4: cierre — `changelog-sync`, `release.py --dry-run`, `/retro` + `retro-gate`

- **Descripción**: cierre de `/dev-cycle` (Fase 6): este ledger a `estado: completado` con todas las tareas marcadas; `changelog-sync` genera las entradas `[Unreleased]` (EN) / `[Sin publicar]` (ES) con un bullet por `T-XX` (campo `Changelog` de cada tarea, ≤ 200 caracteres); `export-interop.py --check` y `release.py --dry-run` en verde; **re-medición E11** (`changelog-sync.py --medicion --json`: cerrar este ledger mueve `ledgers_cerrados`, `tareas`, `camino_changelog`… — si T-19 no se hizo, actualizar marcador y prosa adyacente en los ficheros que fallen, sin tocar citas históricas; si se hizo, solo los vivos); `/retro` con `retro.md` + fila en `CALIBRATION.md` (**primera fila medida en Windows**, con el ratio real tokens/hora de las 22 tareas) y `retro-gate.py` exit 0. Transiciones: spec → `implementada`, plan → `completado`, fila del índice del roadmap actualizada. Confluence: opt-in según `confluence-optin.md` (sin bloquear). Después arrancan `brief-budget` y F2 de `project-specialization`.
- **Changelog**: Cierre del refactor medido del plugin: 32 → ≤ 16 funciones largas en los cinco hotspots, copias declaradas con un test de identidad y once huecos de encadenamiento entre piezas resueltos.
- **Estado**: borrador
- **Tiempo humano**: est. 2,0h · real —
- **Tiempo IA (ejec.)**: est. 0,30h · real —
- **Supervisión**: est. 0,08h (≈25 % IA) · real —
- **Previsión IA**: 105k in / 16k out tok · 1,1 € tokens · coste tarea 101 €
- **Dependencias**: T-20 y T-21 completadas (los cuatro tramos cerrados)
- **Archivos**: `docs/roadmap/2026-09-09-plugin-refactor/tasks.md`, `docs/roadmap/2026-09-09-plugin-refactor/improvement-plan.md` (estado), `docs/roadmap/2026-09-09-plugin-refactor/spec.md` (`estado: implementada`), `docs/roadmap/2026-09-09-plugin-refactor/retro.md` (nuevo, lo escribe `/retro`), `docs/roadmap/CALIBRATION.md` (fila), `docs/roadmap/README.md` (fila), `CHANGELOG.md`, `CHANGELOG.es.md`, los ficheros con marcas `<!--m:…-->` vivas que muevan (`skills/changelog-sync/references/medicion-escalera.md`, `skills/changelog-sync/SKILL.md`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`; y los históricos solo si T-19 no se hizo)
- **Verificación**:
  - `python agent-kits/shared/ledger-lint.py docs/roadmap/2026-09-09-plugin-refactor/tasks.md` → exit 0 con `estado: completado` y 22/22 tareas marcadas
  - `python skills/changelog-sync/scripts/changelog-sync.py --check` → exit 0 y `plugin-refactor` con 22 bullets (0 tareas sin campo `Changelog`) · `grep -c "plugin-refactor" CHANGELOG.md CHANGELOG.es.md` → `≥ 1` cada uno
  - `python skills/changelog-sync/scripts/changelog-sync.py --medicion --json > /dev/null && python -m pytest -q tests/test_cifras_medidas.py tests/test_roadmap_index.py -p no:cacheprovider` → verde (tras re-medir y actualizar los vivos)
  - `python scripts/export-interop.py --check` → al día · `python scripts/release.py --dry-run` → exit 0 · `python scripts/lint_plugin.py` → `0 errores` · `python evals/check.py` → `0 errores`
  - `python agent-kits/shared/retro-gate.py docs/roadmap/2026-09-09-plugin-refactor` → exit 0 (`retro.md` + fila en `CALIBRATION.md`) · `grep -n "plugin-refactor" docs/roadmap/CALIBRATION.md` → fila con `tokens/hora` **medido** (sin `(estimado)`)
  - Cierre del objetivo §8: `python skills/code-health/scripts/code-health.py . --exclude-tests --exclude-path interop --json --baseline docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline-2.json` → `funciones largas` «↓ mejora» (cifra final pegada: hotspots ≤ 16, `todos` = 1)

**Criterios de aceptación**
- [ ] Ledger `completado` y lint exit 0; CHANGELOG ES/EN con un bullet por tarea desde el campo `Changelog`
- [ ] `release.py --dry-run`, `export-interop.py --check`, linter y evals en verde; `test_cifras_medidas` y `test_roadmap_index` en verde tras la re-medición
- [ ] `retro.md` + fila en `CALIBRATION.md` con ratio **medido** (`retro-gate.py` exit 0); spec `implementada`; índice del roadmap con estado y cifras reales
- [ ] Cifra final del §8 pegada: funciones largas en los cinco hotspots ≤ 16, TODO = 1, copias declaradas 7/7, `CONTRACTS.md` 11 aristas

**Subtareas**
- [ ] Marcar estados; `changelog-sync`; re-medición E11 y actualización de vivos
- [ ] Puertas: `--check`, `--dry-run`, lint, evals; `/retro` + `retro-gate`; transiciones spec/plan/índice
- [ ] Confluence opt-in (si procede); handoff: `brief-budget` (sobre `task-brief.py` partido) y F2 de `project-specialization`

**Notas**: La retro de esta iniciativa compara por primera vez horas IA **medidas en Windows** contra estas estimaciones (T-04 garantiza que las 22 ventanas se midan con el código corregido). Desviación objetivo ≤ +30 % en horas IA (la única muestra comparable dio +66 %).
