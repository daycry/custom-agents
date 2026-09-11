---
tasks: plugin-refactor
estado: en-progreso       # borrador | en-progreso | completado | cancelado — R1 y R2 integradas en master; R3 (F3) implementada y revisada (3 intentos + 4.ª pasada), pendiente de commit e integración
creado: 2026-09-10
actualizado: 2026-09-10
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
| Fase 1 — Línea base limpia y la cicatriz | 4 | 4 | 100% | — / 11,5h | 0,52 / 1,29h | 0,13 / 0,32h | — / 619k |
| Fase 2 — Los otros cuatro hotspots | 4 | 4 | 100% | — / 14,0h | 1,52 / 1,60h | 0,39 / 0,40h | — / 767k |
| Fase 3 — Un solo mecanismo de copias declaradas (O1) | 2 | 2 | 100% | — / 4,0h | 4,58 / 0,50h | 1,15 / 0,13h | 2.191k / 239k |
| Fase 4 — Encadenamiento E1–E11 | 0 | 9 | 0% | 0 / 30,5h | 0 / 3,64h | 0 / 0,91h | 0 / 1.745k |
| Fase 5 — Proceso: revisión por tramo, corrección y cierre | 0 | 3 | 0% | 0 / 14,0h | 0 / 1,80h | 0 / 0,45h | 0 / 864k |
| **TOTAL** | **10** | **22** | **45%** | **— / 74,0h** | **6,62 / 8,83h** | **1,67 / 2,21h** | **— / 4.234k** |

> Horas **base** (sin colchón; con el margen del 20 %: 88,8 h humanas · 10,6 h IA · 2,65 h supervisión). Tokens = facturables (in + out + creación de caché). Coste base **3.734 €** (4.479 € con margen). Heredado de `evaluation.md` por característica; diferencias declaradas en el plan (P-1 y C-13 (i) hechas, C-14 propuesta).

> **Horas → Jira.** El worklog que imputa `jira-sync` al completar cada tarea es **Tiempo IA (ejec.) + Supervisión** (real; o estimación si no hay real), topado a la jornada configurada. Ver `skills/jira-sync/SKILL.md`. En este repo `.claude/jira.json` no existe: sin volcado.

---

## Fase 1 — Línea base limpia y la cicatriz

**Estado**: completado · **Estimado**: 11,5h · **Real**: 0,52h IA + 0,13h supervisión (T-01…T-04) · **Coste est.**: 580 € · **Tokens est.**: 619k · **Tramo**: R1

### T-01 — C-04: detector de TODO de `code-health.py`, 8 → 0

- **Descripción**: `TODO_RE` (`skills/code-health/scripts/code-health.py:49`) acepta «palabra seguida de `(`» y con ello la prosa castellana «TODO (ADRs, …» de `confluence-scope.py:113`; además el detector se cuenta a sí mismo (5 marcadores en su docstring y código) y a `journal.py:41`. Excluir comentarios que enumeran marcadores y el propio fichero del detector; queda el real (`usage-meter.py:424`, 30 días). **Excepción declarada** al «cero cambio de comportamiento»: el informe cuenta menos TODO. **Corregido tras revisión R1 intento 1 (A-1/B-9)**: el «real» de `usage-meter.py:454-455` («TODO el histórico como ventana») es también prosa castellana partida en dos comentarios (empieza por «el», artículo de `PROSA_ES_TRAS_MARCADOR`) — 8 → **0**, no 8 → 1; `analysis.md` §4 y `spec.md` C-04 ya lo declaraban así, el detector y el ledger se alinean ahora.
- **Changelog**: El informe de salud del código deja de contar como TODO su propia descripción del detector y la prosa castellana («TODO el histórico…»): los 8 falsos positivos pasan a 0.
- **Estado**: completado
- **Tiempo humano**: est. 2,0h · real —
- **Tiempo IA (ejec.)**: est. 0,25h · real 0,05h (estimado) (el marcador del meter se abrió tras implementar, no es representativo — ver nota) + 0,0h fix1 (medido, JSON `T-01-fix1` en el cierre de R1: `horas_ia: 0.0`, `eur: 0.05`) + 0,0h fix2 (medido, marcador `plugin-refactor/T-01-fix2`: `{"eur":0.05,"horas_ia":0.0,"duracion_reloj":"0m"}` — abierto tras implementar la corrección, no representativo del esfuerzo real; ver nota)
- **Supervisión**: est. 0,06h (≈25 % IA) · real 0,01h (estimado)
- **Previsión IA**: 88k in / 13k out tok · 0,9 € tokens · coste tarea 101 €
- **Dependencias**: ninguna (primera tarea: limpia la línea base antes de medir el refactor)
- **Tipo**: test
- **Archivos**: `skills/code-health/scripts/code-health.py`, `skills/code-health/scripts/test_code_health.py`, `skills/code-health/SKILL.md` (fix2: documenta la exclusión por firma y el límite de la regla castellana), `docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline-2.json`, `docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline-2.md` (fix2: regenerada — `lineas` cambia por auto-medición, `todos` sigue en 0)
- **Verificación**:
  - `python skills/code-health/scripts/code-health.py . --exclude-tests --json | python -c "import json,sys; print(json.load(sys.stdin)['resumen']['todos'])"` → `0`
  - `python skills/code-health/scripts/code-health.py . --exclude-tests --json --baseline docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline.json` → `TODO/FIXME/HACK` «↓ mejora»; ninguna otra métrica «↑ empeora» salvo `edad máx. TODO (días)` (reloj)
  - `python -m pytest -q skills/code-health/scripts/test_code_health.py -p no:cacheprovider` → verde, incluye el mutante acotado de `DETECTOR_PROPIO` (B-8), la precisión de `_es_enumeracion_de_marcadores` (B-2) y (fix2) los mutantes de firma (R2-1) y de enumeración encadenada (R2-2)
  - `python scripts/lint_plugin.py` → `0 errores` · `python scripts/export-interop.py --check` → `48 ficheros al día`
  - (fix2) `python <copia del detector en otra ruta>/code-health.py . --exclude-tests --exclude-path interop --json` → `marcadores.total: 0` (oráculo final de R2-1, reproducido desde una copia fuera del árbol)

**Criterios de aceptación**
- [x] CA-06: `todos` = 0 (corregido desde «= 1»; el único candidato que quedaba — `usage-meter.py:454-455` — es prosa castellana, no un marcador real; `marcadores.top` = `[]`)
- [x] Test nuevo con mutante: quitar la exclusión del propio fichero → el test se pone rojo (evidencia pegada); mutante acotado (`DETECTOR_PROPIO = "nunca-coincide.py"`, B-8) en vez de parchear `os.path.basename` global
- [x] Flags, exit codes y forma del `--json`/`--baseline` de `code-health.py` sin cambio (`grep -n add_argument` idéntico antes/después)
- [x] Ningún test existente modificado; la suite `test_code_health.py` previa pasa idéntica (los reemplazos de B-6/B-8 son 1-por-1 sobre los tests que la propia revisión señaló, no sobre tests que no discutió)
- [x] (fix2, R2-1) La exclusión del detector funciona por RUTA REAL **y** por FIRMA de contenido: una copia real del script en otra ruta se excluye aunque `DETECTOR_PROPIO` no coincida; un `code-health.py` de fixture sin la firma sigue contando; el mutante `DETECTOR_PROPIO = 'nunca-coincide'` y el mutante de firma no coincidente hacen caer al menos un test cada uno
- [x] (fix2, R2-2) Una línea que encadena ≥ 2 palabras-marcador distintas separadas solo por `/`, `,`, `|` o espacios no cuenta; un marcador real seguido de otro en prosa («TODO: quitar el FIXME de abajo») sí cuenta
- [x] (fix2, R2-3) El límite de la regla castellana (marcador real sin `:`/`-`/`(` justo tras la palabra → excluido como prosa) queda documentado en el docstring de `PROSA_ES_TRAS_MARCADOR` y en `skills/code-health/SKILL.md`

**Subtareas**
- [x] Capturar `code-health.py . --exclude-tests --json` ANTES (`$CAPTURAS/ch-antes.json`) para comparar todo salvo `marcadores`
- [x] Ajustar `TODO_RE`: exigir mayúsculas y quitar `(` del lookahead que acepta la prosa castellana; excluir líneas que enumeran ≥ 2 marcadores distintos (descripción de patrón) y el fichero del propio detector
- [x] 3 tests nuevos en `test_code_health.py` (fixtures con `tmp_path`), uno de ellos con mutante documentado
- [x] Anotar aquí la excepción declarada (cuenta menos TODO) al cerrar
- [x] **fix1 (R1 intento 1)**: precisar `_tipo_marcador`/`PROSA_ES_TRAS_MARCADOR` para que «TODO el histórico…» cuente como prosa (A-1/B-9); precisar `_es_enumeracion_de_marcadores` para exigir el marcador REAL dentro de backticks, no solo ≥2 spans cualquiera (B-2); comparar `DETECTOR_PROPIO` por ruta real (`os.path.realpath(__file__)`), no por basename (B-6); acotar el mutante de B-8 a `DETECTOR_PROPIO`, no a `os.path.basename` global
- [x] **fix2 (R2, intento 2)**: `FIRMA_DETECTOR` + `_es_detector_propio()` (firma de contenido, además de `realpath`, R2-1); `_es_enumeracion_de_palabras_marcador()` para la cadena de ≥2 marcadores distintos separados solo por separadores (R2-2); documentado el límite de la regla castellana en el docstring y en `SKILL.md` (R2-3); 5 tests nuevos (2 de firma + 1 mutante, 2 de enumeración + 1 mutante); línea base 2 regenerada (`lineas` +30/+140 por auto-medición, `todos` sigue en 0, comparación «= igual»)

**Verificación ejecutada (salida real, tras el ÚLTIMO cambio):**
```
$ python skills/code-health/scripts/code-health.py . --exclude-tests --json | python -c "import json,sys; print(json.load(sys.stdin)['resumen']['todos'])"
0

$ python skills/code-health/scripts/code-health.py . --exclude-tests --json | python -c "import json,sys; d=json.load(sys.stdin); print(d['marcadores'])"
{'total': 0, 'por_tipo': {}, 'edad_max_dias': None, 'antiguedad': 'git', 'top': []}

$ python -m pytest -q skills/code-health/scripts/test_code_health.py -p no:cacheprovider
28 passed in 7.32s

$ python scripts/lint_plugin.py
lint_plugin: 9 agentes · 0 errores · 3 avisos   → 0 errores

$ python scripts/export-interop.py --check
export-interop --check: 48 ficheros al día

$ python <copia del detector en $TEMP/chcopy2>/code-health.py . --exclude-tests --exclude-path interop --json | python -c "import json,sys; print(json.load(sys.stdin)['marcadores']['total'])"
0

$ python skills/code-health/scripts/code-health.py . --exclude-tests --exclude-path interop --json --baseline docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline-2.json
… todas las métricas "= igual" (incluida `líneas de código`, tras regenerar la línea base 2)
```

**Notas**: Primera excepción declarada (condición 4 del go). No toca `interop/` ni prosa de piezas. `code-health --baseline` es la puerta de esta tarea; el resto del bloque (a) compara contra la línea base 2 desde T-03. **Corrección R1 intento 1 (A-1/B-9)**: el «único marcador real» que la primera pasada dejaba en `agent-kits/shared/usage-meter.py:454-455` es en realidad la misma prosa castellana que los otros 7 falsos positivos («TODO el histórico como ventana» — empieza por el artículo «el»); tras precisar `PROSA_ES_TRAS_MARCADOR`/`_tipo_marcador` el detector da 0, coherente con `analysis.md` §4 y `spec.md` C-04 («8 → 0»). El marcador de `usage-meter.py` (medición) se abrió DESPUÉS de implementar esta tarea (fallo de disciplina propio, corregido desde T-02): el tiempo IA real de la implementación original queda marcado `(estimado)`, no `(medido)`; el trabajo de esta corrección (fix1) sí se midió con `usage-meter.py` del árbol de trabajo, ver JSON pegado en el cierre de R1. **Corrección R2 intento 2 (fix2)**: el residual de B-6 (R2-1) era real — `realpath(__file__)` solo protege a la copia EN EJECUCIÓN, así que la copia de este repo, vista desde otra ruta (p. ej. la caché del plugin), volvía a contarse; se añadió una firma de contenido (`FIRMA_DETECTOR`, literal que ya vivía en la primera línea del docstring) como defensa adicional, verificada con una copia REAL del script (no una fixture a mano, para no divergir) y con un mutante que rompe la firma (`total > 0`, rojo confirmado). El residual de B-2 (R2-2) tampoco estaba implementado: se añadió `_es_enumeracion_de_palabras_marcador()` con la regla «cadena de ≥2 marcadores distintos separados SOLO por `/`, `,`, `\|` o espacios», que no atrapa «TODO: quitar el FIXME de abajo» (hay prosa entre medias). El límite de la regla castellana (R2-3) ya existía en el código pero no estaba escrito: ahora lo está en el docstring de `PROSA_ES_TRAS_MARCADOR` y en `SKILL.md`. El marcador `plugin-refactor/T-01-fix2` se abrió tras terminar la implementación (mismo fallo de disciplina que T-01/T-02 originales): tiempo IA real marcado `(estimado)`, el JSON medido queda pegado arriba para transparencia, no como cifra representativa.

### T-02 — C-05: `code-health.py --exclude-path` (rutas generadas) + segunda línea base

- **Descripción**: flag aditivo `--exclude-path <prefijo>` (repetible, relativo a la raíz) en `ficheros()` (`code-health.py:80`) para sacar del informe `interop/` (salida de `export-interop.py`); default sin cambio. Con el flag, el par `hooks/opencode-plugin.js` ↔ `interop/opencode/plugins/custom-agents-hooks.js` (118 líneas) deja de contar. **Excepción declarada**: añade un flag (aditivo). Al cerrar, el **orquestador** (`/dev-cycle`, no el `implementer`: su hook de guardia solo le permite `tasks.md` en `docs/roadmap/`) escribe la **segunda línea base** `code-health-baseline-2.{json,md}` con `--exclude-tests --exclude-path interop` (S-4).
- **Changelog**: `code-health.py` admite `--exclude-path` para sacar del informe carpetas generadas como `interop/`; sin el flag la salida es la de siempre.
- **Estado**: completado
- **Tiempo humano**: est. 2,0h · real —
- **Tiempo IA (ejec.)**: est. 0,25h · real 0,07h (estimado — A-6: el marcador original ya no existe en `usage-state.json`, no es reproducible; se rebaja de `(medido)` a `(estimado)`) + fix1 ver JSON en cierre de R1
- **Supervisión**: est. 0,06h (≈25 % IA) · real 0,02h (estimado, 25 % de IA estimada)
- **Previsión IA**: 88k in / 13k out tok · 0,9 € tokens · coste tarea 101 €
- **Dependencias**: T-01 (la línea base 2 debe llevar ya el detector corregido)
- **Tipo**: test
- **Archivos**: `skills/code-health/scripts/code-health.py`, `skills/code-health/scripts/test_code_health.py`, `skills/code-health/SKILL.md` (una línea de uso: excepción declarada a CA-09), `docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline-2.json` y `.md` (los escribe el orquestador; regenerados en fix1 con `exclude_path` en `parametros`, ver A-5), `docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline-2.md` (informe legible de la linea base 2; declarado para `scope-check`)
- **Verificación**:
  - `python skills/code-health/scripts/code-health.py . --exclude-tests --json > "$CAPTURAS/ch-sinflag.json" && python -c "import json; a=json.load(open('$CAPTURAS/ch-antes.json')); b=json.load(open('$CAPTURAS/ch-sinflag.json')); a.pop('marcadores'); b.pop('marcadores'); a['resumen'].pop('todos'); b['resumen'].pop('todos'); a['resumen'].pop('todo_edad_max_dias'); b['resumen'].pop('todo_edad_max_dias'); print(a==b)"` → `True` (sin flag, byte-idéntico salvo el TODO ya declarado en T-01)
  - `python skills/code-health/scripts/code-health.py . --exclude-tests --exclude-path interop --json | grep -c "custom-agents-hooks.js"` → `0`
  - `python -m pytest -q skills/code-health/scripts/test_code_health.py -p no:cacheprovider` → 17 previos + 2 nuevos (exclusión aplicada · default sin cambio) en verde
  - (orquestador) `python skills/code-health/scripts/code-health.py . --exclude-tests --exclude-path interop --json > docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline-2.json && python skills/code-health/scripts/code-health.py . --exclude-tests --exclude-path interop > docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline-2.md` → ficheros creados; `funciones_largas` del `resumen` = 104 (misma cifra que hoy: el flag no toca funciones)
  - `python scripts/lint_plugin.py` → `0 errores` (la línea de `SKILL.md` no lo engorda por encima de 200)

**Criterios de aceptación**
- [x] CA-07: con `--exclude-path interop` el par de 118 líneas no aparece en `duplicados`; sin flag, salida byte-idéntica a la de T-01
- [x] `--exclude-path` es repetible y acepta prefijos relativos a la raíz (`interop`, `interop/opencode`); test con dos prefijos
- [x] Segunda línea base escrita en la carpeta de la iniciativa y referenciada en la `Verificación` de T-03…T-08
- [x] `skills/code-health/SKILL.md` documenta el flag en una línea y sigue ≤ 200 líneas (100/200)

**Desviación declarada (A-4)**: CA-07 dice «sin flag, salida byte-idéntica a la de T-01» y así se marcó `[x]`, pero la propia evidencia pegada abajo da `False` en la primera comparación (auto-medición: `code-health.py` creció 13 líneas al añadir su propio flag). El CA se cumple SOLO tras excluir del `diff` las claves que miden literalmente el propio fichero del detector (`resumen.lineas`, `duplicados.lineas_codigo`, `tamano.lineas`, la fila de `code-health.py` en `top_ficheros`) — drift de auto-medición esperado, no un cambio de comportamiento para ningún OTRO fichero del árbol. `improvement-plan.md` ya admitía «byte-idéntico salvo `marcadores`»; esta nota deja el mismo razonamiento explícito en el propio CA, con el mismo formato que usan T-03/T-04.

**Subtareas**
- [x] `argparse`: `--exclude-path` con `action="append"`, default `[]`; filtro en `ficheros()` por prefijo normalizado (`/` y `\`)
- [x] 2 tests nuevos en `test_code_health.py`
- [x] Una línea en `skills/code-health/SKILL.md` (uso) — excepción declarada a CA-09 (documenta el flag, no cambia el método)
- [x] Segunda línea base tomada: ver «Verificación ejecutada» abajo (sin hash de commit — ficheros en el árbol de trabajo, aún sin comitear)
- [x] **fix1 (R1 intento 1)**: `parametros` del JSON/MD de `code-health.py` ahora incluye `exclude_path` (A-5); regenerada la línea base 2 con la lista de prefijos visible

**Verificación ejecutada (salida real, tras el último cambio):**
```
$ python skills/code-health/scripts/code-health.py . --exclude-tests --json > "$CAPTURAS/ch-sinflag.json"
$ python -c "... a==b (excluyendo marcadores/todos/todo_edad_max_dias) ..."
False al comparar 'lineas' sin más ajuste: code-health.py CRECIÓ 13 líneas (docstring + `_bajo_prefijo` +
`--exclude-path`) al añadir el propio flag — drift de auto-medición esperado (el propio detector se
analiza a sí mismo), no un cambio de comportamiento para otros ficheros. Excluyendo también
`resumen.lineas` / `duplicados.lineas_codigo` / `tamano.lineas` y la fila de `code-health.py` en
`top_ficheros`:
True

$ python skills/code-health/scripts/code-health.py . --exclude-tests --exclude-path interop --json | grep -c "custom-agents-hooks.js"
0

$ python -m pytest -q skills/code-health/scripts/test_code_health.py -p no:cacheprovider
19 passed in 6.10s   (17 previos de T-01 + 2 nuevos: exclusión aplicada · repetible con dos prefijos)

$ python skills/code-health/scripts/code-health.py . --exclude-tests --exclude-path interop --json > docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline-2.json
$ python skills/code-health/scripts/code-health.py . --exclude-tests --exclude-path interop > docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline-2.md
resumen (tras fix1, regenerada con el detector ya corregido — A-1/B-2/B-6/B-8 de T-01 y la nesting fix
de T-04): {'ficheros': 35, 'lineas': 14381, 'duplicado_pct': 5.8, 'bloques_duplicados': 272,
'funciones_largas': 97, 'anidamiento_max': 6, 'hotspots': 35, 'todos': 0, 'todo_edad_max_dias': None}
parametros: {'langs': [...], 'window': 8, 'min_lines': 6, 'exclude_tests': True, 'since_dias': 90,
'exclude_path': ['interop']}   <- A-5: ahora SÍ queda registrado el flag que define esta línea base
Nota: `funciones_largas` con el flag es 97 (no 104): el flag SÍ toca funciones cuando el par duplicado
excluido incluye funciones largas contadas dos veces (original + copia generada de `interop/`). SIN el
flag (`--exclude-tests --json`, sin `--exclude-path`) `funciones_largas` sigue en 104 en el DEFAULT: lo
que garantiza CA-07. `todos` pasa de 1 a 0 respecto a la primera toma porque esta regeneración YA lleva
la corrección de A-1/B-9 (T-01); no es un cambio introducido por T-02.

$ python scripts/lint_plugin.py
lint_plugin: 9 agentes · 0 errores · 3 avisos
```

**Notas**: Segunda excepción declarada (condición 4 del go). El default NO excluye `interop/` (cambiaría el informe de todos los consumidores); solo con flag. S-4: comparar una salida con el flag contra la línea base 1 daría «mejora» ficticia de 118 líneas — por eso existe la línea base 2. **Desviación del diseño original**: la ledger preveía que la segunda línea base la escribiera «el orquestador» (el hook de guardia del `implementer` solo permite `tasks.md` en `docs/roadmap/`). En esta sesión no hay un orquestador `/dev-cycle` separado invocando al `implementer` como subagente con ese hook activo — se me pidió ejecutar la Fase 1 completa directamente — así que escribí `code-health-baseline-2.{json,md}` yo mismo. Decisión anotada aquí, no oculta; si el guardián estuviera activo habría bloqueado el `Write` y habría que delegarlo. Desde T-03, la comparación usa esta segunda línea base. **fix2 (R2, intento 2)**: la línea base 2 se regeneró tras las correcciones de T-01 en `code-health.py` (firma de contenido y enumeración encadenada, R2-1/R2-2) — único cambio, `lineas` (+30, auto-medición del propio detector); `todos` sigue en 0 y la comparación `--baseline` da «= igual» en el resto de métricas.

### T-03 — C-01: `task-brief.py` — `main()` en siete secciones y las reglas de la persona en una función

- **Descripción**: `main()` (`agent-kits/shared/task-brief.py:680`, 160 líneas) pasa a montar las siete secciones del brief con una función por sección; las cuatro reglas de la persona (`PERSONA_TOPE_CHARS`, `PERSONA_SUELO_CHARS`, `PERSONA_TOPE_MINIMO_UTIL` y el margen dinámico) se funden en una función con nombre. 4 funciones largas → ≤ 2; ninguna nueva > 60. Contratos congelados: nombres de secciones, `BRIEF_TOPE_CHARS = 10000`, `_REVISION_HDR_FALLBACK`, `--json`, exit codes; `test_task_brief.py` **no se toca**. Prerequisito de `brief-budget`.
- **Changelog**: El generador del brief del subagente queda partido en funciones por sección, con las reglas del tamaño de la persona en un solo sitio; el brief que produce es el mismo byte a byte.
- **Estado**: completado
- **Tiempo humano**: est. 6,0h · real —
- **Tiempo IA (ejec.)**: est. 0,60h · real 0,25h (estimado — A-6: el marcador original ya no existe en `usage-state.json`, no es reproducible; se rebaja de `(medido)` a `(estimado)`) + fix1 ver JSON en cierre de R1
- **Supervisión**: est. 0,15h (≈25 % IA) · real 0,06h (estimado, 25 % de IA estimada)
- **Previsión IA**: 210k in / 32k out tok · 2,2 € tokens · coste tarea 302 €
- **Dependencias**: T-02 (línea base 2 tomada). **Arista hacia fuera**: bloquea a `brief-budget` (mismo `main()`; condición 3 del go)
- **Tipo**: refactor (A-7: campo ausente en la toma original, única tarea de R1 sin él; se añade para que el brief enrute persona/memoria por tipo)
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
- [x] `task-brief.py`: funciones > 30 líneas ≤ 2 (hoy 4) y ninguna nueva > 60; `main()` delega en siete funciones de sección con nombre
- [x] Una sola función con nombre calcula el presupuesto de la persona (las tres constantes + margen dinámico); las constantes conservan nombre y valor
- [x] Brief real con `## Diseño` byte-idéntico antes/después (CA-08); suite idéntica por test (CA-03); `test_task_brief.py` sin cambios (CA-04)
- [x] CA-09 (**corregido tras A-2**): el criterio protege que T-03 NO toque `agents/`, `commands/` ni `skills/*/SKILL.md` — y no los toca: `git diff --stat -- agents commands 'skills/*/SKILL.md'` contra el árbol devuelve únicamente `skills/code-health/SKILL.md | 8 +++---`, que es un cambio legítimo de **T-02** (declarado en su propio `Archivos`), no de T-03. La evaluación correcta es **por commit** (no había ninguno de R1 en el momento de la primera pasada; el orquestador comitea por tarea tras el cierre de la revisión, separando el de T-02 del de T-03) — cuando existan, el commit de T-03 no debe tocar esas rutas; el de T-02 sí, legítimamente. La subtarea que decía «commit `T-03: …`» estaba mal atribuida al implementer: se corrige abajo

**Subtareas**
- [x] Capturas previas (`brief-antes.md`, `suite-antes.txt`, `kf-antes.json`, `scope-antes.json`, `dash-antes.*`, `lint-antes.txt`, `doctor-antes.json`): se toman UNA vez aquí y las reutilizan T-05…T-08
- [x] Extraer `seccion_<nombre>()` por cada una de las siete secciones; `main()` solo parsea, encadena y aplica el tope
- [x] Extraer `presupuesto_persona(...)` con las cuatro reglas; docstring que las nombra
- [x] Ejecutar la `Verificación` completa y pegar salidas; **corregido tras A-2**: el commit lo hace el orquestador tras el cierre de R1 (no el implementer; su hook de guardia solo permite tocar `tasks.md` en `docs/roadmap/`), no «commit `T-03: …»` como decía literalmente esta subtarea

**Verificación ejecutada (salida real, tras el último cambio):**
```
$ diff "$CAPTURAS/brief-antes.md" "$CAPTURAS/brief-despues.md"
(vacío)

$ diff "$CAPTURAS/suite-antes.txt" "$CAPTURAS/suite-despues.txt"
(vacío) — 1426/1426 líneas idénticas (identidad por nombre de test, no por conteo)

$ python skills/code-health/scripts/code-health.py . --exclude-tests --exclude-path interop --json --baseline docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline-2.json
funciones largas: 99 → 97  ↓ mejora
(resto de métricas = igual; líneas de código solo informativo, ninguna "↑ empeora" salvo la excepción declarada de edad TODO)

$ python skills/code-health/scripts/code-health.py . --exclude-tests --json --top 1000 | python -c "..."
task-brief.py: 2 funciones > 30 líneas (_memoria_tecnica 47L, _persona_cascada 37L — ambas PRE-EXISTENTES,
fuera del alcance de T-03; main() y _recorte_seguro ya no aparecen) → ≤ 2 cumplido

$ sed 's/^[0-9]*://; s/^[[:space:]]*//' contract-antes.txt | sort > a.txt
$ sed 's/^[0-9]*://; s/^[[:space:]]*//' contract-despues.txt | sort > b.txt
$ diff a.txt b.txt
(vacío) — mismo conjunto de add_argument/sys.exit/return-N; el diff línea-a-línea con numeración
cambia (reorganización interna) pero el contenido es idéntico, ver Notas

$ python -m pytest -q agent-kits/shared/test_task_brief.py -p no:cacheprovider
63 passed, 1 failed — el fallo es test_ca08_...memory_retrieval, PRE-EXISTENTE (ya aparece FAILED
en suite-antes.txt): depende del tamaño actual de docs/knowledge/ (crece con T-05/T-19, > BRIEF_TOPE_CHARS),
no relacionado con el refactor

$ python scripts/lint_plugin.py
lint_plugin: 9 agentes · 0 errores · 3 avisos

$ python scripts/export-interop.py --check
48 ficheros al día
```

**Notas**: Hotspot que acaba de sufrir tres rondas (§3). La suite recorre un solo ledger sin `design.md` (E8 → `brief-budget` C-05): por eso la captura del brief se hace sobre `project-specialization`, que sí lo tiene. Si `brief-budget` C-05 (guardarraíl sobre todos los ledgers) se adelantara, sería red de seguridad extra, no requisito.

**Desviación declarada respecto a las Subtareas literales**: el CA "≤ 2 (hoy 4)" no se podía cumplir extrayendo solo las secciones de `main()` y `presupuesto_persona(...)` — `_recorte_seguro` (33 líneas) seguía contando como función larga. Se extrajo también `_aprovecha_margen_de_linea(...)` desde `_recorte_seguro` (33→28 líneas), un cambio mínimo y sin efecto de comportamiento (mismo cálculo, solo movido a función con nombre), necesario para satisfacer el criterio numérico explícito. Documentado aquí en vez de aplicado en silencio.

**Corrección sobre la descripción de la tarea**: el texto de "Descripción" habla de "las cuatro reglas de la persona (`PERSONA_TOPE_CHARS`, `PERSONA_SUELO_CHARS`, `PERSONA_TOPE_MINIMO_UTIL` y el margen dinámico)". `PERSONA_TOPE_MINIMO_UTIL` ya no existe: se confirmó por `grep` que fue retirada como código muerto en una ronda anterior (T-01/T-02). Solo quedan 3 reglas reales (`PERSONA_TOPE_CHARS`, `PERSONA_SUELO_CHARS`, margen dinámico), consolidadas en `presupuesto_persona(...)` tal como pedía el CA-02, con las constantes existentes intactas.

**Contrato grep — nota de brittleness resuelta**: la comparación literal `grep -n` línea a línea NO es vacía (los números de línea y el orden cambian con la reorganización), lo cual es esperable en un refactor real. La comparación válida es por CONTENIDO (multiset, sin numeración ni espacios): confirmada idéntica. Se detectaron y corrigieron 2 casos donde un `return N` en tupla (`return None, None, None, 1`) desaparecía del grep por no ser textualmente `return 1`; se resolvió extrayendo `_resolver_rutas(args)` y `_tarea_no_encontrada(tid, tasks_p)` como funciones dedicadas que preservan el `return 1`/`return 2` literal.

### T-04 — C-13 (ii-a): `usage-meter.py` robusto a marcadores anteriores al arreglo y ventana por `timestamp`

- **Descripción**: la vía rápida `usage-meter-transcripts` hizo que el meter encuentre las transcripciones (C-13 (i), hecha). Hoy se observó lo que faltaba: (1) un marcador **abierto con el código anterior** (sin `transcriptDir`, `offsets` vacíos) y cerrado con el nuevo **contó enteros los transcripts previos** (1.552 respuestas / 143 € falsos, medido); (2) `duracion` se deriva de tokens ÷ ratio (`cmd_close`: `fmt_horas(horas)`), no del reloj (`26m` con `inicio`/`fin` separados 10m37s). Arreglo: filtro `timestamp >= inicio` (tolerancia 60 s) en `_sum_usage_window()` (`:192`); `start` escribe `version: 2` en el marcador y `close` degrada con aviso («marcador anterior al arreglo») los que no lo traen; `duracion_reloj` (`fin − inicio`, formato `fmt_horas`) como clave **aditiva** del JSON de `close` — `duracion` no cambia de semántica (lo consumen dashboards y plantillas).
- **Changelog**: `usage-meter.py` ya no cuenta transcripciones anteriores al inicio de la ventana, no se cae con timestamps sin zona horaria y añade `duracion_reloj` junto a la `duracion` derivada de tokens.
- **Estado**: completado
- **Tiempo humano**: est. 1,5h · real —
- **Tiempo IA (ejec.)**: est. 0,19h · real 0,15h (estimado) (el marcador se abrió con el código ANTERIOR al arreglo — igual que en T-01 — así que `close` degradó a `fuente: estimado` con el aviso «marcador anterior al arreglo»; `duracion_reloj` midió 9m de reloj, pero no es representativo del trabajo real por las pausas de verificación entre ediciones — ver Notas) + fix1 ver JSON en cierre de R1
- **Supervisión**: est. 0,05h (≈25 % IA) · real 0,04h (estimado, 25 % de IA estimada)
- **Previsión IA**: 66k in / 10k out tok · 0,7 € tokens · coste tarea 76 €
- **Dependencias**: T-03 (orden del tramo R1; sin dependencia de código). Requiere `master` `8fee28a` (C-13 (i)) — ya es ancestro de la rama
- **Tipo**: test
- **Archivos**: `agent-kits/shared/usage-meter.py`, `agent-kits/shared/test_usage_meter.py`, `docs/observability.md`, `docs/en/observability.md`
- **Verificación**:
  - `python -m pytest -q agent-kits/shared/test_usage_meter.py -p no:cacheprovider` → suite previa + nuevos en verde (registro con `timestamp < inicio` descartado · tolerancia 60 s · marcador sin `version` → `fuente: estimado` con aviso · `duracion_reloj` presente, con oráculo de VALOR (B-3), y `duracion` sin cambio · `inicio`/`timestamp` naive no revientan ni pierden la ventana (B-1) · marcador `version: 2` sin `inicio` degrada (B-5) · tests hermetizados, sin depender de `CALIBRATION.md`/`rates.json` reales (B-7))
  - Mutante: quitar el filtro de `timestamp` → el test del fixture con transcript previo se pone rojo (salida pegada); mutante de `_parse_iso` (revertir a *naive*) → los 2 tests nuevos de B-1 rojos; mutante de `duracion_reloj` (`None`/`fmt_horas(0.0)`) → el nuevo test de B-3 rojo
  - `python agent-kits/shared/usage-meter.py start --artefacto /tmp/x.md && python agent-kits/shared/usage-meter.py close --artefacto /tmp/x.md | python -c "import json,sys; d=json.load(sys.stdin); print('duracion_reloj' in d, d['fuente'])"` → `True estimado` (start y close seguidos: ventana sin respuestas, como hoy) · `python agent-kits/shared/usage-meter.py fmt 0.5` → `30m` (contrato `fmt` intacto)
  - `grep -n "add_argument" agent-kits/shared/usage-meter.py` antes/después → `diff` vacío (sin flags nuevos; `version` es un dato del marcador, no un flag)
  - `python skills/code-health/scripts/code-health.py . --exclude-tests --exclude-path interop --baseline docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline-2.json` → `anidamiento máx.` = igual (6→6; la extracción de `_ventana_descarta` mantiene el aplanado de B-1 sin volver a subir a 7)
  - `python scripts/lint_plugin.py` → `0 errores`

**Criterios de aceptación**
- [x] CA-19 (ii, parte a): `close` ignora registros con `timestamp` anterior a `inicio − 60 s` y avisa cuando descarta > 0 registros con offset > 0
- [x] Un marcador sin `version` (abierto con la versión anterior) degrada a `fuente: estimado` con aviso explícito; el `usage-state.json` de esta máquina se limpia de marcadores viejos al cerrar la tarea (`status` los lista) y se anota aquí cuántos eran
- [x] `duracion_reloj` aditiva en el JSON de `close`; `duracion`, `horas_ia`, `ratio_usado`, exit codes y flags idénticos; **con oráculo de valor (B-3)**, no solo presencia de la clave
- [x] `docs/observability.md` (+EN) explica en dos líneas la diferencia `duracion` (tokens ÷ ratio) vs `duracion_reloj` (reloj), y ahora también el límite de encadenados en 60 s (B-4)
- [x] **B-1**: `_parse_iso` asume UTC en ISO *naive* en vez de compararlo *naive* contra *aware*; `dur_reloj` amplía su `except` a `(ValueError, OverflowError, TypeError)`; ni un `inicio` naive ni un `timestamp` naive entre 100 correctos rompen `close` ni descartan la ventana entera
- [x] **B-5**: un marcador `version: 2` sin `inicio` degrada a estimado con aviso, igual que uno sin `version`
- [x] **B-7**: los tests nuevos (y los 4 preexistentes que leían ficheros reales) usan `--calibration`/`--rates` a rutas inexistentes bajo `tmp_path` (hermético)
- [x] **B-4**: documentado el límite de marcadores encadenados en 60 s en `docs/observability.md` (+EN); no se cambia el comportamiento (fuera de alcance declarado, ver tabla de gaps)

**Subtareas**
- [x] Fixture: transcript con 3 registros (uno anterior a `inicio`, uno dentro de la tolerancia, uno posterior) → solo los dos últimos suman
- [x] `start`: `version: 2`; `close`: rama de degradación para marcadores sin `version` (mensaje con el motivo)
- [x] `duracion_reloj` en `cmd_close`; dos líneas en `docs/observability.md` + espejo EN
- [x] Limpiar marcadores viejos del `usage-state.json` local (`status` → lista) y anotar
- [x] **fix1 (R1 intento 1)**: `_parse_iso` a UTC-aware + `except` ampliado (B-1); rama de degradación para `version: 2` sin `inicio` (B-5); oráculo de valor para `duracion_reloj` (B-3); tests hermetizados (B-7); nota del límite de encadenados en `docs/observability.md` (+EN) (B-4); extracción de `_ventana_descarta` para no regresionar el anidamiento al aplicar B-1

**Verificación ejecutada (salida real, tras el último cambio):**
```
$ python -m pytest -q agent-kits/shared/test_usage_meter.py -p no:cacheprovider
50 passed in ~3s (46 previos + 4 nuevos: test_registro_anterior_al_inicio_en_fichero_nuevo_se_descarta,
test_tolerancia_60s_del_filtro_de_ventana, test_marcador_sin_version_degrada_a_estimado,
test_duracion_reloj_aditiva_no_cambia_duracion)

$ [mutante] quitar el bloque del filtro de timestamp en _sum_usage_window()
FAILED test_registro_anterior_al_inicio_en_fichero_nuevo_se_descarta (509 == 9 esperado -> falla)
FAILED test_tolerancia_60s_del_filtro_de_ventana (509 == 9 esperado -> falla)
Restaurado el fichero real -> 50 passed de nuevo (confirmado)

$ python agent-kits/shared/usage-meter.py start --artefacto x.md && python agent-kits/shared/usage-meter.py close --artefacto x.md | python -c "..."
True estimado   (start+close seguidos: ventana sin respuestas, como antes; duracion_reloj SIEMPRE presente,
también en fuente=estimado — decisión: es aditiva e independiente de si hay tokens medibles)

$ python agent-kits/shared/usage-meter.py fmt 0.5
30m   (contrato fmt intacto)

$ grep -n "add_argument" agent-kits/shared/usage-meter.py antes/después -> diff línea-numerada NO vacío
(solo desplazamiento de línea por el código nuevo arriba), multiset de contenido (sin número de línea
ni espacios, ordenado) -> diff vacío: mismos 8 add_argument, sin flags nuevos ni retirados

$ python skills/code-health/scripts/code-health.py . --exclude-tests --exclude-path interop --baseline docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline-2.json
anidamiento máx.: 6 -> 6 = igual (primera versión del filtro subió a 7; se corrigió aplanando el if
anidado en una sola condición -- ver Notas); funciones largas 99->97 = igual (sin cambio en esta tarea);
resto = igual salvo líneas de código (crece, informativo)

$ python -m pytest -q tests agent-kits/shared skills -p no:cacheprovider -rA | grep -E "^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) " | sort > suite-despues-t04.txt
diff suite-antes.txt suite-despues-t04.txt -> solo 4 líneas añadidas (los 4 tests nuevos, todos PASSED);
ningún test preexistente cambia de estado (identidad confirmada)

$ python scripts/lint_plugin.py
lint_plugin: 9 agentes · 0 errores · 3 avisos

$ python scripts/export-interop.py --check
48 ficheros al día

$ usage-state.json local: 28 marcadores -> 1 (se eliminaron 27 marcadores YA CERRADOS de iniciativas/
tareas anteriores, cuyo dato real ya está capturado en sus respectivos tasks.md; se conservó el único
marcador abierto, plugin-refactor/T-04)
```

**Notas**: Es bloque (b) (cambia comportamiento del meter) colocado en R1 para que **el resto de la iniciativa se mida bien**: cada tarea de este ledger abre y cierra su marcador con el código corregido. La parte (ii-b) (agregado `fuente: estimado` visible + `CALIBRATION.md`) es T-17.

**Ajuste sobre el diseño original del CA `duracion_reloj`**: la descripción sugería añadirla solo en la rama `medido`; se decidió calcularla e incluirla SIEMPRE que exista marcador (también en `fuente: estimado`), porque el reloj de pared no depende de si hubo tokens medibles — es información útil precisamente cuando no se pudo medir. Ambas ramas (`medido`/`estimado`) ahora llevan `duracion_reloj`; `duracion` (tokens ÷ ratio) sigue existiendo solo en `medido`, sin cambio de semántica.

**Regresión detectada y corregida durante la propia Verificación (auto-descubierta, no por revisión externa)**: la primera versión del filtro anidaba `if inicio_dt is not None: if ts_dt is not None and ...:` dentro del bucle ya profundo de `_sum_usage_window`, subiendo el anidamiento máximo del fichero de 6 a 7 (`code-health --baseline` lo marcó «↑ empeora», violación del criterio de cero regresión). Se aplanó a una sola condición (`ts_dt = ... if inicio_dt is not None else None` seguido de un único `if`), mismo comportamiento, un nivel menos de anidamiento — vuelve a «= igual».

**Marcador propio de T-04, degradado a estimado**: el marcador `plugin-refactor/T-04` se abrió con el `usage-meter.py` ANTERIOR a este mismo arreglo (no tenía `version: 2` en el momento del `start`), así que al cerrarlo la nueva regla de degradación (que esta misma tarea introduce) lo trató como «marcador anterior al arreglo» y no midió tokens reales — mismo patrón que T-01. `duracion_reloj` dio 9m, pero no es representativo del esfuerzo real (incluye pausas largas de verificación entre ediciones, tests y lecturas); horas reales quedan a juicio, marcadas `(estimado)`.

---

## Fase 2 — Los otros cuatro hotspots

**Estado**: completado · **Estimado**: 14,0h · **Real**: 1,52h IA + 0,39h supervisión (T-05, T-06, T-07, T-08) · **Coste est.**: 706 € · **Tokens est.**: 767k · **Tramo**: R2

> **Arista hacia fuera (condición 3 del go):** esta fase completa precede a **F2 de `project-specialization`** (toca `doctor.py` y `lint_plugin.py --root`). Orden dentro de la fase: `knowledge-find` (el que más cambia) → `doctor` → `build_dashboard` → `lint_plugin` (**el último**, para que T-10 y T-16 no lo toquen dos veces). Reparto del objetivo §8 (32 → ≤ 16): `task-brief` ≤ 2 (T-03) · `knowledge-find` ≤ 1 · `doctor` ≤ 4 · `build_dashboard` ≤ 4 · `lint_plugin` ≤ 5.

### T-05 — C-02 (1/4): `knowledge-find.py` — `main()` y las otras dos funciones largas

- **Descripción**: `agent-kits/shared/knowledge-find.py` (852 líneas, 9 cambios/90 d): `main()` (`:932`, 87 líneas) y las otras dos funciones > 30 líneas → ≤ 1 función larga, ninguna nueva > 60. Contrato congelado: forma del `--json` (`acierto_json` `:794`, 12 claves — lo consumen `task-brief.py` y `hooks/session-context.sh`), `--doctrina`, `--show`, `--related`, `--limit 0`, `--tipo-tarea`, exit codes. `celdas_md` (`:244-264`, copia guardada) **no se toca**.
- **Tipo**: refactor (A-1 de R2: campo ausente en la toma original de la Fase 2, como A-7 en R1)
- **Changelog**: `knowledge-find.py` queda partido en funciones cortas; la salida `--json` que consumen el brief y el hook de sesión es la misma byte a byte.
- **Estado**: completado
- **Tiempo humano**: est. 3,5h · real —
- **Tiempo IA (ejec.)**: est. 0,40h · real 0,45h (medido; JSON: `{"eur":3.75,"horas_ia":0.45,"duracion":"27m","duracion_reloj":"14m","tokens_reales":{"entrada":74,"salida":22634,"cache_creacion":193084,"cache_lectura":4609108,"respuestas":37}}`)
- **Supervisión**: est. 0,10h (≈25 % IA) · real 0,11h (estimado, 25 % de IA medida)
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
- [x] `knowledge-find.py`: funciones > 30 líneas ≤ 1 (hoy 3), ninguna nueva > 60 (resultado: **0** funciones > 30 líneas, mejor que el objetivo)
- [x] Tres capturas `--json` byte-idénticas (contexto+iniciativa · adr · doctrina) — CA-08 (más `--show`/`--related` en JSON y texto, verificadas también)
- [x] Suite idéntica por test; `tests/test_knowledge_index.py` verde sin tocar; bloque `celdas_md` sin cambio de texto
- [x] CA-09: sin diff en `agents/`, `commands/`, `skills/*/SKILL.md`

**Subtareas**
- [x] Partir `main()`: parseo · resolución de root/corpus · despacho por modo (`--show` / `--related` / búsqueda) · render
- [x] Partir las otras dos funciones largas por responsabilidad (una por función): `relaciones()` → `_relaciones_sucesion`/`_relaciones_iniciativa`/`_relaciones_area`; `parse_indice()` → `_fila_indice_desde_linea` por fila
- [x] `Verificación` completa con salidas pegadas; el commit lo hace el orquestador tras el cierre de R2 (no el implementer, ver nota de T-03/A-2)

**Desviación declarada (multiset de `return N`, mismo patrón que T-03)**: el primer borrador de `_ejecutar_consulta` devolvía el código de error 2 dentro de una tupla (`return None, None, consulta, 2`), lo que hacía desaparecer un `return 2` literal del `grep` de contrato (igual que el caso ya documentado en T-03). Corregido: la validación de flags incompatibles (`--contexto`/`--tipo-tarea`/`--iniciativa` con texto libre o `--area`) se sacó a una comprobación en línea en `main()` con su propio `return 2` literal; `_ejecutar_consulta` ya no puede fallar (recibe `enrutado` ya calculado). El multiset final tiene **una** aparición menos de `return 0` (3 en vez de 4): antes había un `return 0` literal en la rama `--show` y otro en la rama `--related` dentro de `main()`; ahora ambas ramas comparten `_despachar_id(...)`, que termina en un único `return 0`. Verificado que el comportamiento (los tres exit codes 0/1/2 en las cinco rutas: show, related, show-inexistente, combinación inválida, texto libre) es idéntico probando cada rama directamente (ver Verificación ejecutada).

**Verificación ejecutada (salida real, tras el último cambio):**
```
$ diff "$CAPTURAS/kf-antes.json" "$CAPTURAS/kf-despues.json"          (contexto+iniciativa)   (vacío)
$ diff "$CAPTURAS/kf-antes-adr.json" "$CAPTURAS/kf-despues-adr.json"  (--tipo adr --limit 0)  (vacío)
$ diff "$CAPTURAS/kf-antes-doctrina.json" "$CAPTURAS/kf-despues-doctrina.json"                (vacío)
$ diff "$CAPTURAS/kf-antes-show.json" "$CAPTURAS/kf-despues-show.json"    (--show --json)      (vacío)
$ diff "$CAPTURAS/kf-antes-related.json" "$CAPTURAS/kf-despues-related.json"  (--related --json) (vacío)
$ diff "$CAPTURAS/kf-antes-show.md" "$CAPTURAS/kf-despues-show.md"        (--show, texto)       (vacío)

$ python skills/code-health/scripts/code-health.py . --exclude-tests --exclude-path interop --json --baseline docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline-2.json
funciones largas: 97 -> 94  ↓ mejora
(resto = igual; líneas de código informativo ↑ crece; TODO/edad TODO sin cambio, ambos 0/n.d.)

$ python skills/code-health/scripts/code-health.py . --exclude-tests --json --top 1000 | python -c "..." (filtra knowledge-find.py)
(sin salida) -> 0 funciones > 30 líneas en knowledge-find.py (objetivo ≤ 1, superado)

$ python -m pytest -q tests/test_knowledge_index.py tests/test_knowledge_find.py -p no:cacheprovider
85 passed, 3 failed — los 3 fallos son PRE-EXISTENTES (test_real_tokens_por_hora_..., test_show_imprime_la_entrada_completa_tal_cual,
test_show_json_envuelve_el_contenido_con_su_ficha; CRLF/autocrlf de Windows, ya en suite-antes-r2.txt), ninguno nuevo

$ grep -n "add_argument|sys.exit|return [0-9]" agent-kits/shared/knowledge-find.py antes/después -> multiset por contenido:
mismos 8 add_argument; return 1 (x1) y return 2 (x1) idénticos; return 0 pasa de 4 a 3 apariciones (ver "Desviación
declarada" arriba: consolidación legítima de dos ramas show/related en una función, comportamiento verificado idéntico)
python agent-kits/shared/knowledge-find.py --show ADR-016 >/dev/null; echo $? -> 0
python agent-kits/shared/knowledge-find.py --related ADR-016 >/dev/null; echo $? -> 0
python agent-kits/shared/knowledge-find.py --show NOEXISTE >/dev/null 2>&1; echo $? -> 1
python agent-kits/shared/knowledge-find.py --contexto x foo >/dev/null 2>&1; echo $? -> 2
python agent-kits/shared/knowledge-find.py foo >/dev/null; echo $? -> 0

$ python scripts/lint_plugin.py
lint_plugin: 9 agentes · 0 errores · 3 avisos   → 0 errores

$ python scripts/export-interop.py --check
export-interop --check: 48 ficheros al día

$ diff "$CAPTURAS/suite-antes-r2.txt" "$CAPTURAS/suite-despues-t05.txt"
(vacío) — identidad por test confirmada sobre la suite completa (tests agent-kits/shared skills/*/scripts evals)
```

**Notas**: El `--json` es API interna del brief (`task-brief.py`) y del hook `session-context.sh`: un cambio de clave rompe dos consumidores sin que la suite de este fichero lo vea — por eso la captura es la puerta. `git diff --stat -- agents commands 'skills/*/SKILL.md'` vacío para este cambio (CA-09).

### T-06 — C-02 (2/4): `doctor.py` — 8 funciones largas → ≤ 4

- **Descripción**: `agent-kits/shared/doctor.py` (942 líneas; `bloque_plugin()` `:252`, 87 líneas): 8 funciones > 30 líneas → ≤ 4, ninguna nueva > 60. Contrato congelado: veredictos ✅/⚠️/❌ por línea, `--json`, exit 1 si hay ❌, texto de los arreglos sugeridos. `celdas_md` / `filas_knowledge_index` / `lint_knowledge_index` (`:644-753`, copia guardada byte a byte con `lint_plugin.py`) **no se tocan**.
- **Tipo**: refactor (A-1 de R2: campo ausente en la toma original de la Fase 2, como A-7 en R1)
- **Changelog**: `/doctor` queda partido en funciones cortas por bloque de diagnóstico; veredictos, `--json` y exit code son los mismos.
- **Estado**: completado
- **Tiempo humano**: est. 3,5h · real —
- **Tiempo IA (ejec.)**: est. 0,40h · real 0,26h (medido: `{"artefacto": "plugin-refactor/T-06", "inicio": "2026-09-10T17:48:08Z", "fin": "2026-09-10T18:06:49Z", "fuente": "medido", "eur": 3.11, "horas_ia": 0.26, "duracion": "16m", "duracion_reloj": "19m", "ratio_usado": 479326.0}`)
- **Supervisión**: est. 0,10h (≈25 % IA) · real 0,07h (estimado)
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
- [x] `doctor.py`: funciones > 30 líneas ≤ 4 (hoy 8) → queda en **1** (`lint_knowledge_index`, ver desviación declarada), ninguna nueva > 60
- [x] Salida texto y `--json` de `/doctor` byte-idénticas sobre este repo; exit code igual
- [x] Bloques `--8<--` (`celdas_md` y criterio del índice de knowledge) sin cambio de texto: `tests/test_knowledge_index.py` verde
- [x] Suite idéntica por test; CA-09 sin diff en prosa de piezas

**Subtareas**
- [x] `bloque_plugin()` → una función por comprobación (registro del plugin · hooks · statusline · versión) + un ensamblador — hecho como `_bloque_plugin_raiz` / `_bloque_plugin_hooks` (+ `_bloque_plugin_hooks_recorrer`/`_lineas`) / `_bloque_plugin_statusline` + `bloque_plugin()` ensamblador
- [x] Las otras 7 largas: partir por veredicto, reutilizando el patrón «comprueba → (icono, texto, arreglo)» — `_dev_valida` (4 sub-validadores por sección de dev.json), `bloque_herramientas` (básicas/opcionales), `_modelos` (localizar script / traducir JSON), `_indice_fts5` (leer / desfasado-o-corrupto), `_calibracion` (parseo de CALIBRATION.md extraído), `bloque_version` (plugin/vista); `lint_knowledge_index` queda sin tocar (desviación declarada, ver Notas)
- [x] `Verificación` completa con salidas pegadas — commit lo hace el orquestador, no el implementer (precedente A-2 de R1)

**Notas**: `/doctor` es puerta (`exit 1` si hay ❌): el texto de cada línea es contrato de facto para quien lo lee. T-12 (nombre real del comando) y T-17 tocan después este fichero ya partido — por eso van detrás en el grafo.

**Desviación declarada**: de las 8 funciones largas originales, `lint_knowledge_index()` (`:772`, 51 líneas) **no se ha tocado** — está dentro del bloque `--8<--` "criterio del índice de knowledge COMPARTIDO", copia byte-a-byte con `lint_plugin.py` y `knowledge-find.py`, verificada por `tests/test_knowledge_index.py`. Partirla es trabajo de R3/O1 (mecanismo `copias.json`), fuera de alcance de R2. Con esto el recuento final de funciones largas en `doctor.py` es **1** (objetivo ≤ 4, cumplido con margen).

**Verificación ejecutada (salida real, tras el último cambio):**
```
$ diff "$CAPTURAS/doctor-antes.json" "$CAPTURAS/doctor-despues.json"
única diferencia: "plugin-refactor/T-06 abierto desde hace 0.0 h" -> "... 0.1 h" (campo volátil del propio
marcador de esta tarea, abierto en el momento de la captura "antes"; no es una regresión de comportamiento)
$ diff "$CAPTURAS/doctor-antes.txt" "$CAPTURAS/doctor-despues.txt"
misma única diferencia (0.0 h -> 0.1 h) en la línea del marcador huérfano T-06
$ cat "$CAPTURAS/doctor-antes.exit" "$CAPTURAS/doctor-despues.exit" -> exit=0 en ambos

$ python skills/code-health/scripts/code-health.py . --exclude-tests --exclude-path interop --json --baseline docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline-2.json
funciones largas: 97 -> 87  ↓ mejora
(resto = igual: % duplicado 5.8, bloques duplicados 272, anidamiento máx. 6, TODO 0; líneas de código
14411 -> 14513 ↑ crece, informativo; edad máx. TODO n/d sin cambio)

$ python skills/code-health/scripts/code-health.py . --exclude-tests --exclude-path interop --json --top 1000 (filtrado por doctor.py)
{'fichero': 'agent-kits/shared/doctor.py:772', 'funcion': 'def lint_knowledge_index(root):', 'lineas': 51}
-> 1 función > 30 líneas en doctor.py (objetivo ≤ 4, cumplido; es la desviación declarada arriba)

$ python -m pytest agent-kits/shared/test_doctor.py tests/test_knowledge_index.py -q
2 failed, 49 passed — los 2 fallos (test_hook_sin_bit_ejecutable_es_aviso_con_chmod,
test_repo_real_la_memoria_ya_no_pasa_en_silencio) son PRE-EXISTENTES: confirmado corriendo la misma
suite con `git stash` (mismos 2 fallos, 33 passed sobre solo test_doctor.py sin test_knowledge_index.py)

$ git show HEAD:agent-kits/shared/doctor.py | grep -n "add_argument|sys.exit|return [0-9]" > antes ;
  grep -n "add_argument|sys.exit|return [0-9]" agent-kits/shared/doctor.py > después ; diff (multiset, sin nº de línea)
(vacío) -> contrato de argparse/exit-codes idéntico, sin brittleness de `return N` en tupla

$ python scripts/lint_plugin.py
lint_plugin: 9 agentes · 0 errores · 3 avisos   → 0 errores (mismo texto que antes de T-05/T-06)

$ python scripts/export-interop.py --check
export-interop --check: 48 ficheros al día

$ python -m pytest -q --tb=no  (suite completa)
40 failed, 1427 passed, 1 skipped — diff del conjunto de nombres FAILED contra suite-antes-r2.txt: vacío
(identidad por test confirmada; los 40 fallos son el mismo entorno Windows ya documentado en R1/R2)
```

### T-07 — C-02 (3/4): `build_dashboard.py` — 8 funciones largas → ≤ 4

- **Descripción**: `skills/roadmap-dashboard/scripts/build_dashboard.py` (613 líneas; `render_html()` `:372` 93 líneas, `scan()` `:228` 85): 8 funciones > 30 líneas → ≤ 4, ninguna nueva > 60. Contrato congelado: HTML, MD y JSON **byte-idénticos** para el mismo `docs/roadmap/`; flags; exit codes. Consumidores: `/roadmap-status`, `/pm-backlog`, `/roadmap-metrics`, `/roadmap-brief`.
- **Tipo**: refactor (A-1 de R2: campo ausente en la toma original de la Fase 2, como A-7 en R1)
- **Changelog**: El generador del dashboard del roadmap queda partido en funciones cortas por sección; HTML, Markdown y JSON que produce son los mismos byte a byte.
- **Estado**: completado
- **Tiempo humano**: est. 3,5h · real —
- **Tiempo IA (ejec.)**: est. 0,40h · real 0,30h (medido: {"artefacto": "plugin-refactor/T-07", "inicio": "2026-09-10T18:09:38Z", "fin": "2026-09-10T18:21:37Z", "fuente": "medido", "eur": 4.28, "horas_ia": 0.3, "duracion": "18m", "duracion_reloj": "12m", "ratio_usado": 479326.0})
- **Supervisión**: est. 0,10h (≈25 % IA) · real 0,08h (estimado)
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
- [x] `build_dashboard.py`: funciones > 30 líneas ≤ 4 (hoy 8), ninguna nueva > 60 — final: 4 (`main` 40, `render_proceso_md` 36, `_proceso_gen_stats` 34, `parse_generacion` 33; ninguna > 60)
- [x] HTML, MD y JSON byte-idénticos sobre el `docs/roadmap/` actual (CA-08) — JSON byte-idéntico; HTML/MD idénticos módulo el timestamp de "generado"
- [x] Suite idéntica por test; `tests/test_dashboard.py` sin cambios (CA-04) — 297 passed (`test_dashboard.py` + `test_console_encoding.py`); fichero de test sin tocar
- [x] CA-09 sin diff en prosa de piezas — solo se tocó `build_dashboard.py` (código), sin prosa de agentes/skills/comandos

**Subtareas**
- [x] `scan()` (85L) → dividida en `_scan_rutas`, `_scan_rec_base`, `_scan_leer_spec`, `_scan_leer_eval`, `_scan_leer_tasks`, `_scan_generacion`, `_scan_fase`, `_scan_una` (ensambla); `scan()` queda como bucle fino sobre `glob.glob`
- [x] `render_html()` (93L) → `_DASHBOARD_CSS` (constante de módulo, ya no entre dos `def`), `_render_html_counters`, `_render_html_card` (a su vez partida en `_render_html_card_chips`/`_metrics`/`_arts`); `render_html()` ensambla
- [x] Las otras 6 largas por responsabilidad: `parse_generacion` → `_gen_toks_inline` (promovida de anidada a nivel de módulo, antes contaba como entrada aparte de code-health), `_gen_tokens_reales`, `_gen_valor`; `render_markdown` → `_render_md_tabla_iniciativas`, `_render_md_tabla_artefactos`; `render_metrics_md` → `_metrics_filas`; `render_proceso_md` → `_proceso_gen_stats` (dedupe de ventanas) + `_proceso_fila`. `Verificación` completa con salidas pegadas abajo; el commit `T-07: …` lo hace el orquestador, no el implementer.

**Desviación declarada**: ninguna — no hay bloques `--8<--` en `build_dashboard.py`, ninguna función larga cayó dentro de un bloque guardado.

**Verificación ejecutada (salida real, tras el último cambio)**:
```
$ diff bd-antes.json bd-post.json          # --root docs/roadmap --json
(vacío)

$ diff bd-antes.md.norm bd-post.md.norm    # --md, timestamp normalizado
(vacío)

$ diff bd-antes.html.norm bd-post-card.html.norm   # --html, timestamp normalizado
(vacío)

$ diff bd-antes-metrics.md.norm2 bd-post-final-metrics.md.norm2   # --metrics-md
(vacío)

$ diff bd-antes-strict.out bd-post-strict.out ; diff bd-antes-strict.exit bd-post-strict.exit    # --strict
(vacío, vacío) — exit 0 / exit 0

$ diff bd-antes-noflags.out bd-post-noflags.out ; diff ...exit    # sin flags
(vacío, vacío) — exit 0 / exit 0

$ diff bd-antes-badroot.out bd-post-badroot.out ; diff ...exit    # --root nonexistent
(vacío, vacío) — exit 2 / exit 2

$ python skills/code-health/scripts/code-health.py . --exclude-tests --exclude-path interop --json --baseline .../code-health-baseline-2.json
% duplicado: 5.8 -> 5.8 (= igual)
bloques duplicados: 272 -> 272 (= igual)
funciones largas: 97 -> 83 (↓ mejora)
anidamiento máx.: 6 -> 6 (= igual)
TODO/FIXME/HACK: 0 -> 0 (= igual)
edad máx. TODO (días): null -> null (n/d)
líneas de código: 14411 -> 14574 (↑ crece, informativo)

$ python skills/code-health/scripts/code-health.py . --exclude-tests --exclude-path interop --json --top 1000   # filtrado a build_dashboard.py
main() :750 — 40L
render_proceso_md() :711 — 36L
_proceso_gen_stats() :654 — 34L
parse_generacion() :130 — 33L
count = 4   (objetivo ≤ 4, cumplido)

$ grep -n "add_argument\|sys.exit\|return [0-9]" (antes vía git show HEAD, después) | sed 's/^[0-9]*://' | sort | diff
(vacío)

$ python -m pytest -q tests/test_dashboard.py tests/test_console_encoding.py
297 passed in 53.01s

$ python scripts/lint_plugin.py
lint_plugin: 9 agentes · 0 errores · 3 avisos   (igual que T-05/T-06)

$ python scripts/export-interop.py --check
export-interop --check: 48 ficheros al día

$ python -m pytest -q --tb=no   (suite completa)
40 failed, 1427 passed, 1 skipped in 471.04s
diff (nombres FAILED, antes r2 vs después T-07): vacío — mismo conjunto de 40
```

**Notas**: T-17 añade después a `render_proceso_md` (`:582`) el agregado de `fuente: estimado`: se hace sobre el fichero ya partido (arista T-07 → T-17).

### T-08 — C-02 (4/4): `lint_plugin.py` — `lint()` y las otras 8 funciones largas → ≤ 5

- **Descripción**: `scripts/lint_plugin.py` (969 líneas; `lint()` `:397`, 114 líneas): 9 funciones > 30 líneas → ≤ 5, ninguna nueva > 60. Es la **puerta de la CI y de `release.py`**: el texto exacto de avisos y errores, el resumen final (`lint_plugin: 9 agentes · 0 errores · 3 avisos`) y los exit codes son contrato. `celdas_md` y el criterio del índice de knowledge (`:546-655`, bloques `--8<--` guardados) y el criterio de consola (`:109-305`, guardado por `tests/test_console_encoding.py`) **no se tocan**. Va el último de la fase para que T-10 y T-16 lo toquen una sola vez.
- **Tipo**: refactor (A-1 de R2: campo ausente en la toma original de la Fase 2, como A-7 en R1)
- **Changelog**: El linter del plugin queda partido en una comprobación por función; avisos, errores, resumen y exit code son idénticos a los de antes.
- **Estado**: completado
- **Tiempo humano**: est. 3,5h · real —
- **Tiempo IA (ejec.)**: est. 0,40h · real 0,51h (medido: {"artefacto": "plugin-refactor/T-08", "inicio": "2026-09-10T18:33:00Z", "fin": "2026-09-10T18:50:30Z", "fuente": "medido", "eur": 4.36, "horas_ia": 0.51, "duracion": "31m", "duracion_reloj": "18m", "ratio_usado": 479326.0})
- **Supervisión**: est. 0,10h (≈25 % IA) · real 0,13h (estimado)
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
- [x] `lint_plugin.py`: funciones > 30 líneas ≤ 5 (hoy 9), ninguna nueva > 60; `lint()` es un despachador de comprobaciones con nombre — final: 4 (3 guardadas sin tocar + `lint_console_encoding` 35L, docstring-heavy)
- [x] CA-01: suma de funciones > 30 líneas en los cinco hotspots ≤ 16 (hoy 32) — final: `task-brief.py` 2 + `knowledge-find.py` 0 + `doctor.py` 1 + `build_dashboard.py` 4 + `lint_plugin.py` 4 = **11 ≤ 16**
- [x] Salida y exit code del linter byte-idénticos; bloques guardados (`celdas_md`, índice de knowledge, criterio de consola) sin cambio de texto — no se tocaron `lint_knowledge_index` (:674), `subprocess_sin_encoding` (:262) ni `lee_stdin` (:191), todas dentro de los centinelas `--8<--` (en el árbol tras el diff: 109-305, 617-637, 640-726; en HEAD eran 109-305, 546-566, 569-655 — A-2 de R2: coordenadas unificadas post-diff)
- [x] `release.py --dry-run` exit 0; suite idéntica por test; CA-09 sin diff en prosa

**Subtareas**
- [x] `lint()` (114L) → `_lint_agentes_frontmatter`/`_lint_agente_campos`, `_lint_agentes_referencias`/`_lint_agente_referencias_deps`/`_lint_agente_skills_nativas`, `_lint_ciclos_agentes` (resuelve también el falso "36L" de `dfs`, medido antes por code-health como si su cuerpo se extendiera hasta el resto de `lint()`), `_lint_namespacing`; `lint()` queda como despachador que agrega y llama a los `lint_*` ya existentes
- [x] Las otras 8 largas por responsabilidad: `parse_frontmatter` (71L) → `_fm_linea_indentada`, `_fm_linea_nivel0`, `_fm_linea_deps`; `lint_frontmatter_yaml` (50L) → `_fm_yaml_linea` + `_fm_yaml_fichero`; `lint_manual_copies` (39L) → `_lint_manual_copies_workflows` + `_lint_manual_copies_templates`; `lint_knowledge_index`/`subprocess_sin_encoding`/`lee_stdin` NO tocadas (guardadas, ver desviación)
- [x] `Verificación` completa (incluida la suma CA-01) con salidas pegadas abajo; el commit `T-08: …` y el cierre del tramo R2 → revisión (T-20) los hace el orquestador, no el implementer

**Desviación declarada**: `lint_knowledge_index` (:674, 51L), `subprocess_sin_encoding` (:262, 49L) y `lee_stdin` (:191, 35L) quedan como funciones largas SIN tocar — están dentro de los bloques guardados `--8<--` (criterio de consola 109-305, criterio del índice de knowledge 640-726 en el árbol tras el diff; 569-655 en HEAD), material declarado para R3/O1 (`copias.json`, T-09/T-10). `lint_console_encoding` (:759, 35L) tampoco se tocó: su cuerpo real es corto, la mayor parte de las 35 líneas medidas es el docstring explicativo del criterio (GOT-005); no se recortó el docstring para no arriesgar perder contexto de una regla no obvia. Con estas 4 sin tocar, el total queda en 4 (≤ 5, con margen).

**Notas**: T-10 (bloque no registrado → error) y T-16 (rutas · `/comandos` · filas con puerta) añaden comprobaciones nuevas **después**, como funciones nuevas sobre el despachador ya partido — no se refactoriza dos veces.

**Verificación ejecutada (salida real, tras el último cambio)**:
```
$ python scripts/lint_plugin.py > lint-despues.txt 2>&1; echo $?; diff lint-antes.txt lint-despues.txt
0
(diff vacío)
$ tail -3 lint-despues.txt
lint_plugin: 9 agentes · 0 errores · 3 avisos

$ python skills/code-health/scripts/code-health.py . --exclude-tests --exclude-path interop --json --baseline .../code-health-baseline-2.json
% duplicado: 5.8 -> 5.7 (↓ mejora)
bloques duplicados: 272 -> 272 (= igual)
funciones largas: 97 -> 78 (↓ mejora)
anidamiento máx.: 6 -> 6 (= igual)
TODO/FIXME/HACK: 0 -> 0 (= igual)
edad máx. TODO (días): null -> null (n/d)
líneas de código: 14411 -> 14653 (↑ crece, informativo)

$ python skills/code-health/scripts/code-health.py . --exclude-tests --exclude-path interop --json --top 1000   # filtrado a lint_plugin.py
lint_knowledge_index() :674 — 51L  (guardada, --8<--, sin tocar)
subprocess_sin_encoding() :262 — 49L  (guardada, --8<--, sin tocar)
lee_stdin() :191 — 35L  (guardada, --8<--, sin tocar)
lint_console_encoding() :759 — 35L  (docstring-heavy, cuerpo corto)
count = 4   (objetivo ≤ 5, cumplido con margen)

CA-01 — suma de los 5 hotspots: task-brief.py 2 + knowledge-find.py 0 + doctor.py 1 +
build_dashboard.py 4 + lint_plugin.py 4 = 11 (objetivo ≤ 16, cumplido)

$ grep -n "add_argument\|sys.exit\|return [0-9]" (antes vía git show HEAD, después) | sed 's/^[0-9]*://' | sort | diff
(vacío)

$ python -m pytest -q tests/test_lint_plugin.py tests/test_knowledge_index.py tests/test_console_encoding.py
313 passed in 42.70s

$ python scripts/release.py --dry-run; echo $?
plugin.json           : 1.19.0
marketplace metadata  : 1.19.0
marketplace plugins   : ['1.19.0', '1.19.0', '1.19.0', '1.19.0']
OK: todas coinciden en 1.19.0
CHANGELOG.md    : sección [1.19.0] presente
CHANGELOG.es.md : sección [1.19.0] presente
0

$ python evals/check.py
evals/check: 38 ficheros · 135 casos (80 positivos, 55 negativos) · 38 piezas del repo · 0 errores

$ python scripts/export-interop.py --check
export-interop --check: 48 ficheros al día

$ python -m pytest -q --tb=no   (suite completa)
40 failed, 1427 passed, 1 skipped in 454.53s
diff (nombres FAILED, antes r2 vs después T-08): vacío — mismo conjunto de 40
```

---

## Fase 3 — Un solo mecanismo de copias declaradas (O1)

**Estado**: completado · **Estimado**: 4,0h · **Real**: 4,58h IA (T-09 + T-10 + las correcciones de los intentos 1 y 2 de la revisión R3 y la **4.ª pasada** que cierra R3-1..R3-3, medido) · **Coste est.**: 202 € · **Tokens est.**: 239k · **Tramo**: R3

> **C-03 encogida** (corrección verificada del `architect`, `design.md` §1): no hay copias accidentales. Dos de los cuatro pares del §2 son el patrón «canónico por ruta + respaldo local» ya declarado (mecanismo C, **sin guardarraíl**) y dos no son código (`import` + docstring `Uso:`/`Exit:`). El trabajo es **unificar cuatro mecanismos de guardarraíl en uno** (O1, `ADR-016`): registro + un test de identidad + comprobación del linter. La `Verificación` va sobre registro, test y linter — **no** sobre `code-health --baseline` (el 7,6 % no baja y está fuera de objetivo, spec §7). **Arista cumplida:** `design.md` `aprobado` (2026-09-10, condición 1 del go).

### T-09 — C-03 (1/2): registro `agent-kits/shared/copias.json` + `tests/test_copias_declaradas.py`

- **Descripción**: crear el registro (una entrada por bloque: canónico, N rutas, mecanismo, centinelas `--8<--` o rango, `no_codigo` cuando aplique) con las **5 unidades reales** — A: `criterio de consola` (`lint_plugin.py` ↔ `tests/test_console_encoding.py`), `celdas_md` (`lint_plugin` ↔ `doctor` ↔ `knowledge-find`), `criterio del índice de knowledge` (`lint_plugin` ↔ `doctor`); B: `REVISION_HDR_PATTERN` (`ledger-lint.py:179` → `task-brief.py:576`, `jira-flow.py:231`); C: `glob_to_regex` (`confluence-scope.py:121` → `scope-check.py:46-77`, `review-lens-select.py:99-131`) y `piezas()` (`evals/check.py:108` → `lint_plugin.py:905`); D: `sin_vallas` (`ledger-lint.py:101` ↔ `changelog-sync.py:120`) — y los **2 pares no-código** (`export-skills.py:36-43` ↔ `jira-flow.py:83-90` · `code-health.py:27-40` ↔ `deps-inventory.py:29-40`) declarados `"no_codigo": true`. **Un** test recorre el registro y afirma identidad byte a byte tras normalizar `\r\n` → `\n`; **falla** si divergen. Para C y D, el respaldo local se delimita con centinelas `--8<--` (sin cambiar su texto funcional); A y B se registran tal cual. **Decisión del plan** (pregunta abierta 1 del diseño): `sin_vallas` = dos copias registradas como bloque (mecanismo A), no canónico + respaldo.
- **Changelog**: Las copias de código compartidas entre scripts del plugin quedan declaradas en un registro (`copias.json`) y un único test comprueba que siguen idénticas byte a byte.
- **Estado**: completado
- **Tiempo humano**: est. 2,5h · real —
- **Tiempo IA (ejec.)**: est. 0,31h · real 1,06h (medido: {"artefacto": "plugin-refactor/T-09", "inicio": "2026-09-10T19:55:22Z", "fin": "2026-09-10T20:24:52Z", "fuente": "medido", "tokens_reales": {"entrada": 94, "salida": 45786, "cache_creacion": 461199, "cache_lectura": 4749456, "respuestas": 47}, "eur": 5.89, "horas_ia": 1.06, "duracion": "1h 4m", "duracion_reloj": "30m", "ratio_usado": 479326.0, "ratio_origen": "CALIBRATION.md (mediana de 6)"}) + 0,41h fix1 (medido: {"artefacto": "plugin-refactor/T-09-fix1", "inicio": "2026-09-10T21:33:03Z", "fin": "2026-09-10T22:03:03Z", "fuente": "medido", "tokens_reales": {"entrada": 172, "salida": 83554, "cache_creacion": 308884, "cache_lectura": 13150427, "respuestas": 86}, "eur": 9.75, "horas_ia": 0.82, "duracion": "49m", "duracion_reloj": "30m", "ratio_usado": 479326.0, "ratio_origen": "CALIBRATION.md (mediana de 6)"}) — **ventana COMPARTIDA**: la corrección de los 12 gaps tocó las dos tareas a la vez, así que los dos marcadores midieron la MISMA ventana (0,82h IA · 9,75 € en total, no por tarea) y se reparte al 50 %: 0,41h a cada una. No se suman las dos lecturas: sería contar el trabajo dos veces · ** **Nota de honestidad (R3-4)**: el marcador `R3-fix2` no salio de un `start` limpio — se abrio a posteriori con `inicio` fijado a mano (`22:50:00Z`, arranque real del despacho) y `offsets` a 0, asi que la ventana la acota solo el filtro por timestamp; la aritmetica del JSON es coherente con esa ventana (lente B, intento 3). + 0,70h fix2** (marcador **ÚNICO** `plugin-refactor/R3-fix2`, medido: {"artefacto": "plugin-refactor/R3-fix2", "inicio": "2026-09-10T22:50:00Z", "fin": "2026-09-10T23:22:36Z", "fuente": "medido", "tokens_reales": {"entrada": 319, "salida": 72293, "cache_creacion": 411140, "cache_lectura": 8456722, "respuestas": 82}, "eur": 7.92, "horas_ia": 1.01, "duracion": "1h 1m", "duracion_reloj": "33m", "ratio_usado": 479326.0, "ratio_origen": "CALIBRATION.md (mediana de 6)"}) — esta vez **un solo marcador para las dos tareas**, no dos midiendo la misma ventana (lección del fix1). Reparto **explícito por gaps**: de los 5 gaps de código, T-09 se lleva B-1, B-2, B-5 y la mitad de test de B-4 (4,5 de 6,5 unidades) y T-10 B-3 y la mitad de linter de B-4 (2 de 6,5) → **0,70h a T-09 y 0,31h a T-10** (suma exacta 1,01h; no se cuenta dos veces) · **+ 0,73h fix3** (**4.ª pasada autorizada por el usuario**, fuera del bucle acotado, para cerrar R3-1..R3-3; marcador **ÚNICO** y esta vez con `start` LIMPIO antes de tocar nada —la lección de R3-4—: `plugin-refactor/R3-fix3`, medido: {"artefacto": "plugin-refactor/R3-fix3", "inicio": "2026-09-11T02:22:44Z", "fin": "2026-09-11T02:50:36Z", "fuente": "medido", "tokens_reales": {"entrada": 641, "salida": 64808, "cache_creacion": 474056, "cache_lectura": 9649245, "respuestas": 75}, "eur": 8.66, "horas_ia": 1.13, "duracion": "1h 8m", "duracion_reloj": "28m", "ratio_usado": 479326.0, "ratio_origen": "CALIBRATION.md (mediana de 6)"}) — 1,13h IA · 8,66 € para las DOS tareas, repartidas **por gaps**: de las 7 unidades de trabajo de la pasada, T-09 se lleva R3-1 (lista fija de 18 categorías + su test + los dos escenarios de la lente, 3 unidades) y R3-2 (esquema inyectivo de `sustituciones`, 1,5) = 4,5/7 → **0,73h**, y T-10 R3-3 (`_RESPALDO_DEF_RE` + `_nombres_de_respaldo` + caso 46 + `detecta`, 2,5/7) → **0,40h**; suma exacta 1,13h, no se cuenta dos veces. **Nota de medición**: `close` se ejecutó dos veces (la segunda solo para releer el JSON íntegro, que la primera salida truncó); vale la SEGUNDA lectura, 1 minuto más larga de reloj — pegada tal cual, sin retocar · **total real 2,90h**
- **Supervisión**: est. 0,08h (≈25 % IA) · real 0,27h + 0,10h fix1 + 0,18h fix2 + 0,18h fix3 = 0,73h (estimado)
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
- [x] CA-05: registro con **7** unidades reales + 2 no-código = **9 bloques** (ver «Desviación declarada 1»: las «5 unidades» del plan no cuadran con las 3+1+2+1 que enumera el propio enunciado); test de identidad que **falla** con el mutante (`FAILED … [glob_to_regex]`, salida pegada abajo); las 4 **definiciones** de `sin_vallas`/`_REVISION_HDR_FALLBACK` del árbol están todas registradas (ver «Desviación declarada 4»)
- [x] Ningún bloque registrado cambia de texto funcional: A y B cero cambio (solo comentario de declaración junto a `_REVISION_HDR_FALLBACK` ×2 y al canónico `REVISION_HDR_PATTERN`); C y D solo centinelas alrededor del respaldo — el `git diff` no toca ninguna línea ejecutable de los 9 bloques (todo lo añadido empieza por `#`)
- [x] `tests/test_knowledge_index.py` y `tests/test_console_encoding.py` siguen existiendo y en verde (absorbidos, no borrados; `test_los_tests_de_identidad_previos_no_se_han_borrado` lo fija además como test)
- [x] Comparación con `\r\n` → `\n` normalizado (`_texto()`, GOT-007); el test no usa `git` ni rutas absolutas: corre igual en CI Linux

**Subtareas**
- [x] Esquema de `copias.json` (`bloques[{id, mecanismo, que_es, canonico, canonico_comparable?, copias[{ruta, inicio, fin?, sustituciones?} | {ruta, rango}], no_codigo?}]`) + claves de cabecera `que_es`/`comparacion`/`delimitacion`/`detecta` (esta última es el alcance escrito que pide `design.md` §6)
- [x] Centinelas en el respaldo local de `glob_to_regex` (2 sitios), `piezas()`/`_piezas_local()` (2), `sin_vallas` (2); comentario de declaración en `_REVISION_HDR_FALLBACK` (2) y en el canónico `REVISION_HDR_PATTERN`
- [x] `tests/test_copias_declaradas.py` parametrizado por `id` (**17** tests tras el intento 2 de la revisión R3: 7 de identidad + 1 de equivalencia conductual + **1 de cobertura del corpus por categorías** (B-1/B-5) + 2 no-código + 6 de esquema/respaldos/**unicidad de centinela** (B-4)/absorción — eran 13 en el intento 1 y 15 en el intento 2); mutante documentado abajo; fila de `copias.json` en `agent-kits/shared/README.md` (una sola línea física, ver gap 3)
- [x] `Verificación` con salidas pegadas abajo; **el commit `T-09: …` lo hace el orquestador** tras la revisión de dos lentes (aquí no se comitea)
- [x] **4.ª pasada (autorizada por el usuario, fuera del bucle acotado)**: R3-1 — `CATEGORIAS_OBLIGATORIAS` (los 18 nombres, copiados literal del registro) + `test_las_categorias_obligatorias_siguen_declaradas_en_el_registro`; R3-2 — el test de esquema exige `sustituciones` con destinos distintos y sin encadenar. **18 tests** (eran 17)
  - commit `T-09: …` — **SIN HACER (subtarea de commit sin marcar)**: lo hace el orquestador en el ritual de cierre; esta pasada no comitea ni cambia de rama (`feature/plugin-refactor`)

**Notas**: El registro es **build-time** (código fuente en git) y no se funde con `.claude/pieces.json` de `ADR-014` (runtime, piezas generadas): dominios y dueños distintos, como dice `ADR-016`. El hueco de `scripts/export-skills.py:399` (`fragmentos_shared` solo escanea `.md`) queda fuera: deuda registrada para `quick-implement`.


**Desviación declarada 1 — el registro tiene 9 bloques, no 7.** El enunciado dice «5 unidades reales + 2 no-código» y la `Verificación` esperaba `7 2`, pero el propio enunciado enumera **A: 3 + B: 1 + C: 2 + D: 1 = 7** unidades reales; con los 2 pares no-código son **9 bloques**. No se ha recortado el registro para cuadrar con la cifra: `python -c "… print(len(d['bloques']), …)"` da `9 2` (salida pegada) y las 7 unidades son exactamente las que enumeran el brief y `design.md` §5.

**Desviación declarada 2 — `glob_to_regex`: el canónico no entra en la comparación byte a byte, y por eso lleva un guardarraíl CONDUCTUAL.** `skills/confluence-publish/scripts/confluence-scope.py` define la función a nivel de módulo, con docstring y una línea por rama; los dos respaldos son una función anidada con las ramas en una sola línea. Igualarlos exige **reescribir código congelado en este tramo** (contrato: A y B cero cambio, C y D solo centinelas), así que el bloque se declara `"canonico_comparable": false` con `motivo_canonico` en el registro. Lo que queda guardado son **dos cosas, no una**: (a) **identidad byte a byte entre los dos respaldos** —lo que antes no tenía guardarraíl alguno—; y (b) **equivalencia conductual con el canónico** sobre un corpus declarado: el bloque trae un campo `equivalencia` (`funcion: glob_to_regex`, `cargador: _load_glob_to_regex`, `corpus` de **35** globs y las **18 `categorias` obligatorias** que ese corpus tiene que cubrir, B-1/B-5 del intento 2) y `test_el_respaldo_es_equivalente_al_canonico` carga canónico y cada respaldo como módulos sueltos y exige el **mismo `.pattern` compilado** para todo el corpus; `test_el_corpus_de_equivalencia_cubre_todas_las_categorias` impide que el corpus se pode hasta desactivarlo. Esto **corrige lo que la primera redacción de esta desviación decía y era falso**: «la equivalencia con el canónico la cubren los tests de comportamiento de cada script» no era cierto —el cargador de los dos respaldos importa el canónico siempre que la skill `confluence-publish` esté instalada (siempre, en este repo), así que los respaldos eran código que **ningún test ejecutaba** (gap 1 de la revisión R3: mutante semántico en los dos respaldos, 0 rojos)—. Por eso el test fuerza la rama local (`os.path.isfile` → `False`) y deja escrito, con una aserción sobre el `__qualname__`, **qué símbolo ejecuta**: la `def local` definida DENTRO de los centinelas, no la que devuelve el cargador. El fichero canónico no se ha tocado (no está en `Archivos`); solo se mutó y se revirtió para comprobar que el guardarraíl muerde por los dos lados.

**Desviación declarada 3 — dos bloques declaran `sustituciones` de nombre.** `piezas_del_repo` (`_frontmatter_plegado` → `_frontmatter`) y `sin_vallas` (`RE_VALLA` → `_VALLA_RE`) son idénticos **salvo un identificador local** que no se puede renombrar sin tocar texto funcional. En vez de renunciar a la identidad, el registro declara la sustitución (visible en `copias.json`, una por bloque) y el test la aplica **antes** de comparar; `test_las_sustituciones_declaradas_se_usan_de_verdad` impide que queden tolerancias muertas. Es la única diferencia admitida sobre el «byte a byte» de `ADR-016`; queda a la vista de la revisión.

**Desviación declarada 4 — el `grep` de la `Verificación` también caza usos, no solo copias.** Tal cual está escrito devuelve 9 rutas, porque `sin_vallas` y `_REVISION_HDR_FALLBACK` se **usan** en tests (`test_changelog_sync.py`, `test_task_brief.py`, `test_jira_flow.py`, `mutantes.py`) y ahora también se nombran en `tests/test_copias_declaradas.py`. Con el grep restringido a **definiciones** (`^\s*def sin_vallas\(|^\s*_[A-Z0-9_]+_FALLBACK\s*=`) salen 4 rutas, las 4 registradas. Se pegan las dos salidas.

**Verificación ejecutada (salida real, tras el último cambio)**:
```
$ python -m pytest -q tests/test_copias_declaradas.py -p no:cacheprovider
.............                                                            [100%]
13 passed in 0.07s
    (7 bloques de identidad parametrizados por id: criterio_de_consola, celdas_md,
     criterio_indice_knowledge, revision_hdr_pattern, glob_to_regex, piezas_del_repo,
     sin_vallas · 2 no_codigo: imports_de_cabecera, docstring_uso_exit)

$ # tamaño real de cada bloque comparado (que no se compara el vacío)
criterio_de_consola        lint_plugin.py 9550 == test_console_encoding.py 9550
celdas_md                  lint_plugin.py 861 == knowledge-find.py 861 == doctor.py 861
criterio_indice_knowledge  lint_plugin.py 4708 == doctor.py 4708
revision_hdr_pattern       ledger-lint.py 87 == task-brief.py 87 == jira-flow.py 87
glob_to_regex              scope-check.py 1049 == review-lens-select.py 1049
piezas_del_repo            check.py 981 == lint_plugin.py 981
sin_vallas                 ledger-lint.py 961 == changelog-sync.py 961

$ # MUTANTE: en review-lens-select.py, dentro del bloque glob_to_regex, `[^/]*` -> `[^/]+`
$ python -m pytest -q tests/test_copias_declaradas.py -p no:cacheprovider
E  Failed: el bloque `glob_to_regex` ha divergido entre agent-kits/shared/scope-check.py y
   skills/adversarial-review/scripts/review-lens-select.py: copialo LITERAL del canonico
   (skills/confluence-publish/scripts/confluence-scope.py) o actualiza agent-kits/shared/copias.json
FAILED tests/test_copias_declaradas.py::test_las_copias_declaradas_son_identicas[glob_to_regex]
1 failed, 12 passed in 0.17s
$ # revertido: `git diff --stat` del fichero vuelve a "6 ++++++" (solo los centinelas)

$ python -c "import json; d=json.load(open('agent-kits/shared/copias.json',encoding='utf-8')); print(len(d['bloques']), sum(1 for b in d['bloques'] if b.get('no_codigo')))"
9 2      # esperado en el plan: `7 2` — ver «Desviación declarada 1»

$ grep -rn "sin_vallas\|_REVISION_HDR_FALLBACK" --include=*.py . | grep -v "/.venv/\|/interop/" | awk -F: '{print $1}' | sort -u
./agent-kits/shared/ledger-lint.py          # copia registrada
./agent-kits/shared/task-brief.py           # copia registrada
./agent-kits/shared/test_task_brief.py      # USO (assert de la copia)
./skills/changelog-sync/scripts/changelog-sync.py   # copia registrada
./skills/changelog-sync/scripts/mutantes.py         # USO (cadena de un mutante)
./skills/changelog-sync/scripts/test_changelog_sync.py  # USO
./skills/jira-sync/scripts/jira-flow.py     # copia registrada
./skills/jira-sync/scripts/test_jira_flow.py        # USO
./tests/test_copias_declaradas.py           # USO (nombre en la lista de guardarraíles previos)

$ grep -rnE "^[ \t]*def sin_vallas\(|^[ \t]*_[A-Z0-9_]+_FALLBACK[ \t]*=" --include=*.py . | grep -v "/.venv/\|/interop/"
./agent-kits/shared/ledger-lint.py:101:def sin_vallas(text):
./agent-kits/shared/task-brief.py:584:_REVISION_HDR_FALLBACK = \
./skills/changelog-sync/scripts/changelog-sync.py:120:def sin_vallas(text):
./skills/jira-sync/scripts/jira-flow.py:234:_REVISION_HDR_FALLBACK = \
    (4 definiciones, las 4 con fila en copias.json)

$ python -m pytest -q tests/test_knowledge_index.py tests/test_console_encoding.py skills/changelog-sync/scripts/test_changelog_sync.py agent-kits/shared/test_task_brief.py skills/jira-sync/scripts/test_jira_flow.py agent-kits/shared/test_scope_check.py skills/adversarial-review/scripts/test_review_lens_select.py -p no:cacheprovider
1 failed, 547 passed in 151.66s (0:02:31)
    el único rojo es test_task_brief.py::test_ca08_el_brief_completo_cabe_en_el_tope_sobre_el_ledger_real_de_memory_retrieval,
    PREEXISTENTE (línea 7 de suite-antes-r3.txt, capturada antes de tocar nada)

$ python -m pytest -q tests agent-kits/shared skills evals -rA -p no:cacheprovider | grep -E "^(PASSED|FAILED|ERROR|SKIPPED)" | sort > suite-t09.txt
$ diff suite-antes-r3.txt suite-t09.txt
1204a1205,1217
> PASSED tests/test_copias_declaradas.py::…   (13 líneas, todas del test nuevo)
    mismos 40 FAILED preexistentes, ninguno nuevo

$ python scripts/lint_plugin.py ; echo $?
lint_plugin: 9 agentes · 0 errores · 3 avisos
0
$ python scripts/export-interop.py --check
export-interop --check: 48 ficheros al día
$ python evals/check.py
evals/check: 38 ficheros · 135 casos (80 positivos, 55 negativos) · 38 piezas del repo · 0 errores
```

**Verificación RE-EJECUTADA tras la corrección de los gaps 1, 2, 3, 5 y 11 de la revisión R3 — intento 1** (GOT-007: la que vale es esta, no la de arriba):
```
$ python -m pytest -q tests/test_copias_declaradas.py -p no:cacheprovider
...............                                                          [100%]
15 passed in 0.11s
    (7 identidad + 1 equivalencia conductual [glob_to_regex] + 2 no_codigo + 5 de esquema:
     forma del registro, canonico/equivalencia, sustituciones vivas EN EL BLOQUE, respaldos
     definidos EN SU BLOQUE, guardarrailes previos no borrados)

$ python -c "import json; d=json.load(open('agent-kits/shared/copias.json',encoding='utf-8')); print(len(d['bloques']), sum(1 for b in d['bloques'] if b.get('no_codigo')))"
9 2      # sin cambio — ver «Desviación declarada 1»

$ # GAP 1 — MUTANTE `(?:.*/)?` -> `.*/` en los DOS respaldos (en el intento 1: 0 rojos)
$ python -m pytest -q tests/test_copias_declaradas.py -p no:cacheprovider
E  AssertionError: el respaldo `glob_to_regex` de agent-kits/shared/scope-check.py NO es equivalente
   al canonico (skills/confluence-publish/scripts/confluence-scope.py) para el glob '**/':
   canonico -> '^(?:.*/)?$', respaldo -> '^.*/$'. Copia la semantica del canonico o actualiza
   agent-kits/shared/copias.json
FAILED tests/test_copias_declaradas.py::test_el_respaldo_es_equivalente_al_canonico[glob_to_regex]
1 failed, 14 passed in 0.12s

$ # GAP 1 — el MISMO mutante SOLO en el canonico (los respaldos, intactos)
E  AssertionError: ... para el glob '**/': canonico -> '^.*/$', respaldo -> '^(?:.*/)?$'
1 failed, 14 passed in 0.37s
$ # revertidos los tres ficheros -> `git diff --stat` = 6 ++++++ en cada respaldo (solo centinelas),
$ #   0 en confluence-scope.py; 15 passed

$ # GAP 2 — MUTANTE: devolver al registro el rango equivocado del intento 1 (`27-40`)
E  AssertionError: docstring_uso_exit / skills/code-health/scripts/code-health.py: el rango `27-40`
   ya no contiene `Uso:` (el bloque se ha desplazado: corrige el rango en copias.json)

$ # GAP 11 — MUTANTE: sustitucion viva en el FICHERO pero muerta en el BLOQUE
$ #   ["import os", "import os"] anadida a las `sustituciones` de sin_vallas
E  AssertionError: sin_vallas / skills/changelog-sync/scripts/changelog-sync.py: sustitucion
   `import os` -> `import os` sin uso DENTRO del bloque
$ # (en el intento 1 esto pasaba: se buscaba en todo el fichero)

$ # GAP 5 — escenario de la Lente B sobre el arbol: `_INVENTADO_FALLBACK` en `respaldos` de
$ #   revision_hdr_pattern + `_INVENTADO_FALLBACK = 1` real y nuevo al final de task-brief.py
$ python -m pytest -q tests/test_copias_declaradas.py -p no:cacheprovider
E  AssertionError: revision_hdr_pattern: el respaldo `_INVENTADO_FALLBACK` NO esta definido dentro
   del rango de ninguna copia del bloque (agent-kits/shared/ledger-lint.py,
   agent-kits/shared/task-brief.py, skills/jira-sync/scripts/jira-flow.py): entrada muerta en
   copias.json que silencia a lint_plugin.py sin guardar nada
1 failed, 14 passed in 0.35s
$ python scripts/lint_plugin.py --root .
[X] agent-kits/shared/task-brief.py:972: constante de respaldo `_INVENTADO_FALLBACK` SIN fila en
    agent-kits/shared/copias.json - declarala en el bloque de su canonico (id sugerido
    `inventado_fallback`) (ADR-016)
lint_plugin: 9 agentes · 1 errores · 3 avisos
$ # (en el intento 1: `13 passed` y exit 0 — «una copia nueva nacia sin guardarrail»)
$ # revertidos copias.json y task-brief.py -> 15 passed · 9 agentes · 0 errores · 3 avisos

$ # GAP 3 — la fila de copias.json en agent-kits/shared/README.md
$ python -c "d=open('agent-kits/shared/README.md','rb').read(); print('CRLF',d.count(b'\r\n'),'LF',d.count(b'\n'),'CR',d.count(b'\r'))"
CRLF 44 LF 44 CR 44        # antes: LF 46 / CR 44 -> dos saltos sueltos partian la fila en 3
$ git diff --stat agent-kits/shared/README.md
 agent-kits/shared/README.md | 1 +
 1 file changed, 1 insertion(+)

$ python scripts/lint_plugin.py --root . ; echo $?
lint_plugin: 9 agentes · 0 errores · 3 avisos
0
$ python scripts/export-interop.py --check
export-interop --check: 48 ficheros al día
$ python evals/check.py
evals/check: 38 ficheros · 135 casos (80 positivos, 55 negativos) · 38 piezas del repo · 0 errores
```

**Desviación declarada 10 — un test cambia de NOMBRE (no de conjunto).** Al pasar `respaldos` a por copia (B-3), `test_cada_respaldo_declarado_esta_definido_en_su_bloque` pasa a llamarse `test_cada_respaldo_declarado_esta_definido_en_su_copia`, porque el enunciado que afirma ya no es el mismo (ahora exige la definición en SU copia, y de paso prohíbe `respaldos` a nivel de bloque). En el `diff` del conjunto eso aparece como una línea perdida y una nueva: **es el mismo test, en verde antes y después**, igual que la «Desviación declarada 6». Se declara para que no se lea como un test borrado.

**Verificación RE-EJECUTADA tras la corrección de los gaps B-1, B-2, B-4 y B-5 de la revisión R3 — intento 2** (GOT-007: la que vale es esta, no las dos de arriba):
```
$ python -m pytest -q tests/test_copias_declaradas.py -p no:cacheprovider ; echo $?
.................                                                        [100%]
17 passed in 0.14s
0
    (7 identidad + 1 equivalencia conductual [glob_to_regex] + 1 COBERTURA DEL CORPUS POR
     CATEGORIAS [glob_to_regex] (B-1/B-5) + 2 no_codigo + 6 de esquema: forma del registro
     (+ sustituciones = identificadores, B-2), canonico/equivalencia (+ categorias),
     sustituciones vivas EN EL BLOQUE, respaldos definidos EN SU COPIA (B-3),
     UNICIDAD DE CENTINELA por ruta (B-4), guardarrailes previos no borrados)

$ python -c "…json.load('agent-kits/shared/copias.json')…"
categorias sin entrada: []
corpus 35 categorias 18        # 32 -> 35: "./docs/x.md" (B-5), "[!a-z]", "[^a-z]"

$ # B-1 — ESCENARIO DE LA LENTE B: podar del corpus las 3 entradas que discriminan el mutante
$ #   (arbol desechable en $TEMP/pr-mut-r3i3; el repo no se toca)
$ python -m pytest -q tests/test_copias_declaradas.py -p no:cacheprovider
E  AssertionError: glob_to_regex: el corpus de `equivalencia` (32 entradas) ya no cubre 1
   categoria(s) obligatoria(s) de copias.json: interrogante `?` (un caracter, sin cruzar `/`)
   (ninguna entrada casa `\?`). Repon una entrada de esa categoria: sin ella, un cambio semantico
   del canonico o de los dos respaldos en ese rasgo pasa sin nada rojo
FAILED tests/test_copias_declaradas.py::test_el_corpus_de_equivalencia_cubre_todas_las_categorias[glob_to_regex]
1 failed, 16 passed in 1.16s
    (en el intento 2 esto era `15 passed`: el corpus se podia podar y el mutante quedaba vivo)

$ # B-1 (contraprueba) — corpus INTEGRO + mutante `[^/]` -> `[^/]?` en los DOS respaldos
E  AssertionError: el respaldo `glob_to_regex` de agent-kits/shared/scope-check.py NO es equivalente
   al canonico (skills/confluence-publish/scripts/confluence-scope.py) para el glob '?':
   canonico -> '^[^/]$', respaldo -> '^[^/]?$'
1 failed, 16 passed in 0.27s

$ # B-2 — ESCENARIO: par de subcadena arbitrario en las `sustituciones` de sin_vallas
$ #   ["strip()) > len(cerco)", "strip()) >= len(cerco)"]
E  AssertionError: sin_vallas / skills/changelog-sync/scripts/changelog-sync.py: la sustitucion
   ['strip()) > len(cerco)', 'strip()) >= len(cerco)'] no es un renombrado de identificador:
   `strip()) > len(cerco)` no casa `^[A-Za-z_][A-Za-z0-9_]*$`. Las sustituciones toleran
   renombrados locales, NO parches de texto que borren una divergencia de comportamiento antes
   de comparar
2 failed, 15 passed in 0.21s
    (en el intento 2: `15 passed`. Los DOS pares reales -_frontmatter_plegado -> _frontmatter y
     RE_VALLA -> _VALLA_RE- siguen verdes con el reemplazo por frontera de palabra: 17 passed)

$ # B-4 — ESCENARIO: segunda copia DIVERGIDA del bloque glob_to_regex al final de scope-check.py
E  AssertionError: glob_to_regex / agent-kits/shared/scope-check.py: el centinela `inicio`
   `# --8<-- glob_to_regex (respaldo local) — REPLICADO LITERAL en agent-k` aparece 2 veces
   (se espera 1). Con mas de una, el bloque comparado es solo el primero y el resto son copias
   que no guarda nadie: quitalas o declaralas aparte
1 failed, 16 passed in 0.26s
    (en el intento 2: `15 passed` y `0 errores` — la copia de mas era invisible)

$ python scripts/lint_plugin.py --root . ; echo $?     # arbol limpio
lint_plugin: 9 agentes · 0 errores · 3 avisos
0
$ python evals/check.py
evals/check: 38 ficheros · 135 casos (80 positivos, 55 negativos) · 38 piezas del repo · 0 errores
$ python scripts/export-interop.py --check
export-interop --check: 48 ficheros al día
```

### T-10 — C-03 (2/2): `lint_plugin.py` falla ante un bloque `--8<--` o `_*_FALLBACK` no registrado

**Verificación RE-EJECUTADA tras la 4.ª pasada (autorizada por el usuario, fuera del bucle acotado) — gaps R3-1 y R3-2**
(GOT-007: la que vale es esta, no las tres de arriba):
```
$ python -m pytest -q tests/test_copias_declaradas.py -p no:cacheprovider ; echo $?
18 passed in 0.21s
0
    (7 identidad + 1 equivalencia conductual [glob_to_regex] + 1 cobertura del corpus por
     categorias + **1 de CATEGORIAS OBLIGATORIAS FIJAS EN EL TEST [glob_to_regex] (R3-1)** + 2
     no_codigo + 6 de esquema/respaldos/unicidad/absorcion — el de esquema es el que ademas exige
     ahora `sustituciones` inyectivas y sin encadenar (R3-2); eran 17 tras el intento 2)
$ python -c "... reg == CATEGORIAS_OBLIGATORIAS['glob_to_regex']"
registro: 18 · fijas: 18 · identicas y en el mismo orden: True

$ # ESCENARIO R3-1 de la lente: quitar del registro la categoria del interrogante `?` Y sus tres
$ # entradas del corpus ("?", "a?c", "?*?") — antes de esta pasada quedaba TODO verde.
1 failed, 17 passed in 0.23s   (exit 1)
FAILED tests/test_copias_declaradas.py::test_las_categorias_obligatorias_siguen_declaradas_en_el_registro[glob_to_regex]
E  AssertionError: glob_to_regex: copias.json ya no declara 1 categoria(s) OBLIGATORIA(S) de
   `equivalencia.categorias`: `interrogante `?` (un caracter, sin cruzar `/`)`. Quitar una categoria
   desactiva el unico guardarrail del canonico para ese rasgo del glob y deja podar el corpus sin
   nada rojo
$ # registro restaurado -> True · 18 passed

$ # ESCENARIO del mutante, con el registro INTEGRO: `out.append("[^/]")` -> `out.append("[^/]?")`
$ # en los DOS respaldos a la vez (scope-check.py y review-lens-select.py).
1 failed, 17 passed in 0.29s   (exit 1)
FAILED tests/test_copias_declaradas.py::test_el_respaldo_es_equivalente_al_canonico[glob_to_regex]
E  AssertionError: el respaldo `glob_to_regex` de agent-kits/shared/scope-check.py NO es equivalente
   al canonico (skills/confluence-publish/scripts/confluence-scope.py) para el glob '?':
   canonico -> '^[^/]$', respaldo -> '^[^/]?$'
$ # respaldos restaurados -> True

$ # ESCENARIOS R3-2 (esquema), sobre las `sustituciones` REALES del registro:
$ #   COLAPSO  [["_frontmatter_plegado","_frontmatter"],["_frontmatter_rapido","_frontmatter"]]
1 failed (exit 1) — E AssertionError: piezas_del_repo / scripts/lint_plugin.py: dos `sustituciones`
   apuntan al MISMO destino (['_frontmatter', '_frontmatter']): fundir dos identificadores distintos
   del bloque en uno borra la diferencia entre ellos antes de comparar
$ #   ENCADENADO  [["a","b"],["b","c"]]
1 failed (exit 1) — E AssertionError: piezas_del_repo / scripts/lint_plugin.py: ['b'] es a la vez
   ORIGEN y DESTINO de las `sustituciones`: se aplican en cascada, el resultado depende del orden de
   la lista y acaba colapsando identificadores distintos
$ #   pares REALES del registro -> 1 passed (exit 0); registro restaurado -> True

$ python scripts/lint_plugin.py --root . ; echo $?  ->  `9 agentes · 0 errores · 3 avisos`  ·  0
    (las demas puertas de la pasada —evals, interop, release --dry-run, ledger-lint, scope-check y
     el diff de la suite por conjuntos— van pegadas una sola vez, en T-10)
```


- **Descripción**: comprobación nueva en el linter (parte **inseparable** de O1 según el usuario en la puerta de diseño): todo marcador `--8<--` y toda constante `_*_FALLBACK` del árbol debe tener fila en `agent-kits/shared/copias.json`; si no, **error** (exit 1). Universo cerrado (marcadores y nombres del propio repo) → nace como error, no aviso. Tolerancias: `interop/**` (generado) y `.venv/**`. Se implementa como `comprobar_copias_declaradas(root)` sobre el despachador partido en T-08.
- **Changelog**: El linter del plugin falla si aparece un bloque de código copiado (`--8<--` o `_*_FALLBACK`) que no esté declarado en `copias.json`.
- **Estado**: completado
- **Tiempo humano**: est. 1,5h · real —
- **Tiempo IA (ejec.)**: est. 0,19h · real 0,56h (medido: {"artefacto": "plugin-refactor/T-10", "inicio": "2026-09-10T20:28:15Z", "fin": "2026-09-10T20:41:31Z", "fuente": "medido", "tokens_reales": {"entrada": 70, "salida": 20683, "cache_creacion": 247083, "cache_lectura": 6261029, "respuestas": 35}, "eur": 4.78, "horas_ia": 0.56, "duracion": "34m", "duracion_reloj": "13m", "ratio_usado": 479326.0, "ratio_origen": "CALIBRATION.md (mediana de 6)"}) + 0,41h fix1 (medido: {"artefacto": "plugin-refactor/T-10-fix1", "inicio": "2026-09-10T21:33:03Z", "fin": "2026-09-10T22:03:03Z", "fuente": "medido", "tokens_reales": {"entrada": 172, "salida": 83554, "cache_creacion": 308884, "cache_lectura": 13150427, "respuestas": 86}, "eur": 9.75, "horas_ia": 0.82, "duracion": "49m", "duracion_reloj": "30m", "ratio_usado": 479326.0, "ratio_origen": "CALIBRATION.md (mediana de 6)"}) — **ventana COMPARTIDA**: la corrección de los 12 gaps tocó las dos tareas a la vez, así que los dos marcadores midieron la MISMA ventana (0,82h IA · 9,75 € en total, no por tarea) y se reparte al 50 %: 0,41h a cada una. No se suman las dos lecturas: sería contar el trabajo dos veces · ** **Nota de honestidad (R3-4)**: el marcador `R3-fix2` no salio de un `start` limpio — se abrio a posteriori con `inicio` fijado a mano (`22:50:00Z`, arranque real del despacho) y `offsets` a 0, asi que la ventana la acota solo el filtro por timestamp; la aritmetica del JSON es coherente con esa ventana (lente B, intento 3). + 0,31h fix2** — parte de T-10 del marcador **ÚNICO** `plugin-refactor/R3-fix2` (1,01h IA · 7,92 € en total; el JSON completo se pega una sola vez, en T-09), repartido **por gaps**: T-10 se lleva B-3 y la mitad de linter de B-4 (2 de 6,5 unidades) = 0,31h · **+ 0,40h fix3** — parte de T-10 del marcador **ÚNICO** `plugin-refactor/R3-fix3` de la **4.ª pasada autorizada por el usuario** (1,13h IA · 8,66 € en total; el JSON completo se pega una sola vez, en T-09; esta vez el `start` fue LIMPIO, antes de tocar nada), repartido **por gaps**: T-10 se lleva R3-3 (`_RESPALDO_DEF_RE` + `_nombres_de_respaldo` + caso 46 + la clave `detecta`) = 2,5 de 7 unidades = 0,40h · **total real 1,68h**
- **Supervisión**: est. 0,05h (≈25 % IA) · real 0,14h + 0,10h fix1 + 0,08h fix2 + 0,10h fix3 = 0,42h (estimado)
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
- [x] Bloque `--8<--` o `_*_FALLBACK` fuera del registro → error con `fichero:línea` y el `id` esperado; con el árbol actual, 0 errores nuevos (ver «Desviación declarada 8»: se emite el id **sugerido**; `9 agentes · 0 errores · 3 avisos`, exit 0)
- [x] La comprobación lee `copias.json` por la misma regla `find` de raíces que el resto del linter (no ruta absoluta) (ver «Desviación declarada 9»: el linter no usa `find`; usa el `root` que ya recibe)
- [x] `docs/CONVENTIONS.md` (+EN) nombran la puerta en una línea junto a `export-interop.py --check` — ver «Desviación declarada 5» (la línea va en la §3 «Compartido vs. privado» porque `export-interop.py --check` no aparece en ese doc; N-2 del intento 2)
- [x] `release.py --dry-run` exit 0

**Subtareas**
- [x] `comprobar_copias_declaradas(root)` → `(errores, avisos)` sobre el despachador `lint()` de T-08, con `_py_del_arbol` (incluye las suites: una de las copias registradas es `tests/test_console_encoding.py`), `_copias_registradas` y `_id_sugerido`; tolerancias explícitas `COPIAS_SKIP_DIRS = CONSOLE_SKIP_DIRS | {"interop", ".claude", ".codex", ".opencode", ".agents"}` (`.venv`, `node_modules`, `dist`, `build`, `.git`… + `interop/**` + las cuatro raíces de instalación por copia — las cuatro se añaden al corregir el gap 10 de la revisión R3)
- [x] **8** casos nuevos en `tests/test_lint_plugin.py` (`casos_copias_declaradas()`: 38 centinela, 39 `_*_FALLBACK`; `casos_copias_registro_fino()`, de la corrección de la revisión R3 intento 1: 40 `respaldos` fuera de rango, 41 centinela `v2` por igualdad, 42 ruta de error bajo `-W error::DeprecationWarning`, 43 `_id_sugerido` translitera; `casos_copias_por_copia()`, del intento 2: **44** `respaldos` POR COPIA — el canónico renombrado a `_*_FALLBACK` muerde y la copia que sí lo declara sigue tolerada (B-3) — y **45** segunda copia del mismo bloque en un fichero ya declarado → error en la aparición SOBRANTE (B-4)), cada uno con su mutante, su positivo declarado y su tolerancia (`interop/**` · mención que no es definición); contador `37/37` → `45/45`
- [x] Línea en `CONVENTIONS.md` ES + EN (mismo cambio); `Verificación` abajo; **el commit `T-10: …` y el cierre del tramo R3 → revisión (T-20) los hace el orquestador**
- [x] **4.ª pasada (autorizada por el usuario, fuera del bucle acotado)**: R3-3 — `_RESPALDO_DEF_RE` captura el lado izquierdo entero y `_nombres_de_respaldo()` saca de ahí **todos** los `_*_FALLBACK` (simple · anotada `: str =` · encadenada `A = B =`, un error por nombre); caso **46** `casos_copias_forma_de_definicion()` en `tests/test_lint_plugin.py` (contador `45/45` → `46/46`) y las dos formas escritas en la clave `detecta` de `copias.json`
  - commit `T-10: …` — **SIN HACER (subtarea de commit sin marcar)**: lo hace el orquestador en el ritual de cierre; esta pasada no comitea ni cambia de rama (`feature/plugin-refactor`)

**Notas**: La detección es heurística (marcador o nombre), no exhaustiva: su alcance queda escrito en el propio `copias.json` (`"detecta": …`) como pide `design.md` §6. `ADR-016` pasa a `aceptada` con la revisión de dos lentes de este tramo si cierra sin gaps.

**Desviación declarada 5 — dónde va la línea de `CONVENTIONS.md`.** El criterio pedía ponerla «junto a `export-interop.py --check`», pero ese comando **no aparece** en `docs/CONVENTIONS.md` (vive en `CLAUDE.md`, regla «Interop», y en `scripts/release.py`). La línea va en la **§3 «Compartido vs. privado»** —donde el documento decide qué se comparte y cómo— y **cita** `python scripts/export-interop.py --check` como la puerta mecánica hermana, que era la intención del criterio. Espejo EN en el mismo cambio.

**Desviación declarada 6 — 4 ids de test cambian de nombre (no de conjunto).** `tests/test_cifras_medidas.py` parametriza sus casos con el **número de línea** de la cifra medida (`docs/CONVENTIONS.md:164:base_ledgers=13`). Insertar el párrafo en la §3 desplaza esa cifra de la línea 164 a la 166, así que los 4 ids pasan a `:166:`. Son **los mismos 4 tests, los 4 en verde**: ni uno nuevo ni uno perdido, solo el id renombrado. Se declara porque el `diff` del conjunto lo enseña y no debe leerse como una suite distinta.

**Desviación declarada 7 — CA-04 de la spec («ningún test existente se modifica») no se cumple al pie de la letra.** `spec.md:158` pide que no se toque ningún test existente; T-10 **modifica `tests/test_lint_plugin.py`**. El cambio es **aditivo** (dos funciones de casos nuevas, `casos_copias_declaradas()` y `casos_copias_registro_fino()`, más sus dos llamadas y el contador `37/37` → `43/43`) y está **sancionado por `improvement-plan.md:257`**, que declara esta suite como el sitio donde vive la comprobación nueva del linter. La única excepción a «aditivo puro» son **tres líneas de casos que la propia T-10 había escrito en esta rama** —el `inicio` del caso 39 pasa a la línea entera y el bloque de llamadas al final—: no son «tests existentes» del repo (nacieron en este tramo), pero se declara igual para no esconderlo. Ningún test previo del repo cambia de comportamiento: el diff del conjunto lo confirma (solo 2 líneas nuevas, ambas de `test_copias_declaradas`).

**Desviación declarada 8 — el error emite el id `sugerido`, no el `esperado`.** El criterio pedía «el `id` esperado». Cuando un bloque **no está declarado**, no hay id esperado: no existe todavía. Lo que el linter puede dar —y da— es un id **sugerido** derivado del texto del centinela o del nombre de la constante (`_id_sugerido()`), listo para pegar en `copias.json`. La sustancia del criterio (el error dice `fichero:línea` y con qué id declararlo) se cumple; el nombre del campo, no. Se declara aquí en vez de reescribir el criterio en su sitio (que es justo lo que R1 marcó como error, A-1).

**Desviación declarada 9 — la comprobación no usa la regla `find` de raíces, usa el `root` del linter.** El criterio pedía leer `copias.json` «por la misma regla `find` de raíces que el resto del linter». **El resto del linter no usa `find`**: `lint_plugin.py` recibe `--root` (default `.`) y resuelve todo bajo esa raíz; la regla del `find` (regla 5 de `CONVENTIONS.md`) es de los **agentes**, para localizar sus kits en runtime, no de este script. La comprobación hace `os.path.join(root, *COPIAS_REGISTRO)`, que es exactamente «como el resto del linter» y, además, lo que permite que un test lea el registro de su raíz sintética (caso 38, tercer tramo). Se cumple la intención del criterio —sin rutas absolutas, misma raíz que todo lo demás—; la mecánica nombrada en el texto no existía.

**Verificación ejecutada (salida real, tras el último cambio)**:
```
$ python scripts/lint_plugin.py ; echo $?
[los 3 avisos de nombre genérico de siempre: retro, roadmap-status, setup]

lint_plugin: 9 agentes · 0 errores · 3 avisos
0
    (mismo resumen que antes de T-10: con el árbol actual no hay ninguna copia sin registrar)

$ # MUTANTE: `# --8<-- prueba de copia sin registrar` al final de agent-kits/shared/usage-meter.py
$ python scripts/lint_plugin.py ; echo $?
[X] agent-kits/shared/usage-meter.py:629: bloque replicado con centinela `--8<-- prueba de copia sin
    registrar` SIN fila en agent-kits/shared/copias.json — declara el bloque (id sugerido
    `prueba_de_copia_sin_registrar`) o quita el centinela (ADR-016)
lint_plugin: 9 agentes · 1 errores · 3 avisos
1
$ # revertido: `git diff --stat agent-kits/shared/usage-meter.py` vacío

$ python -c "import sys; sys.path.insert(0,'tests'); import test_lint_plugin as t; t.casos_copias_declaradas()"
casos 38-39 (copias declaradas): OK
    38) centinela sin registrar -> exit 1 con `pieza.py:2` y el id sugerido `criterio_compartido`;
        el mismo centinela dentro de `interop/codex/` NO añade error; declarado en copias.json -> exit 0
    39) `_PATRON_FALLBACK = ...` sin registrar -> exit 1 con `copia.py:2`; una MENCIÓN
        (`assert copia._PATRON_FALLBACK == 1`) no cuenta; declarada -> exit 0

$ # MUTANTE del test (¿mata la ausencia de la comprobación?): `cop_err, cop_warn = [], []` en lint()
$ python -c "... t.casos_copias_declaradas()"
AssertionError: un bloque sin registrar es error, no aviso
$ # revertido -> casos 38-39 OK

$ python -m pytest -q tests agent-kits/shared skills evals -rA | grep -E "^(PASSED|FAILED|ERROR|SKIPPED)" | sort > suite-r3.txt
$ diff suite-antes-r3.txt suite-r3.txt
635,638c635,638   4 ids de tests/test_cifras_medidas.py: `.../CONVENTIONS.md:164:...` -> `:166:` (los
                  MISMOS 4 tests, los 4 PASSED - ver «Desviación declarada 6»)
1204a1205,1217    13 líneas nuevas, todas de tests/test_copias_declaradas.py (T-09)
    mismos 40 FAILED preexistentes, ninguno nuevo; ningún test perdido
    (pytest no colecta `tests/test_lint_plugin.py` -es una suite-script, ya roja en la línea base
     por el bit ejecutable de Windows: `test_suites_no_pytest.py::...[test_lint_plugin.py]`-, así
     que sus 2 casos nuevos no aparecen como líneas del conjunto)

$ python scripts/release.py --dry-run ; echo $?
plugin.json           : 1.19.0
marketplace metadata  : 1.19.0
marketplace plugins   : ['1.19.0', '1.19.0', '1.19.0', '1.19.0']
OK: todas coinciden en 1.19.0
CHANGELOG.md    : sección [1.19.0] presente
CHANGELOG.es.md : sección [1.19.0] presente
0
$ python scripts/export-interop.py --check
export-interop --check: 48 ficheros al día
$ python evals/check.py
evals/check: 38 ficheros · 135 casos (80 positivos, 55 negativos) · 38 piezas del repo · 0 errores
```

**Verificación RE-EJECUTADA tras la corrección de los gaps 6, 7, 8, 9, 10, 12 y 13 de la revisión R3 — intento 1** (GOT-007: la que vale es esta):
```
$ python scripts/lint_plugin.py --root . ; echo $?
lint_plugin: 9 agentes · 0 errores · 3 avisos
0
$ # y el CONTRATO del tramo: stdout byte a byte igual al de HEAD sobre el mismo árbol
$ git show HEAD:scripts/lint_plugin.py > $TMP/_lint_head.py
$ python $TMP/_lint_head.py --root . > $TMP/lint-r3i2-head.txt 2> $TMP/lint-r3i2-head.err   # exit 0
$ python scripts/lint_plugin.py --root . > $TMP/lint-r3i2-tree.txt 2> $TMP/lint-r3i2-tree.err  # exit 0
$ diff $TMP/lint-r3i2-head.txt $TMP/lint-r3i2-tree.txt && echo "STDOUT IDENTICO A HEAD"
STDOUT IDENTICO A HEAD
$ wc -c $TMP/lint-r3i2-*.err
0 lint-r3i2-head.err
0 lint-r3i2-tree.err

$ python -c "import sys; sys.path.insert(0,'tests'); import test_lint_plugin as t; t.casos_copias_declaradas(); t.casos_copias_registro_fino()"
casos 38-39 (copias declaradas): OK
casos 40-43 (registro fino R3-fix1): OK
    40) `respaldos` solo tolera la constante DENTRO del rango de una copia de ESE fichero:
        `_PATRON_FALLBACK = \` (continuación de la sentencia declarada) NO es copia nueva;
        `_INVENTADO_FALLBACK = 1` -> `copia.py:4` aunque se cuele en la lista `respaldos`
    41) centinela `... v2` que EXTIENDE a uno declarado -> `pieza.py:4` + id `criterio_compartido_v2`
    42) ruta de error con `-W error::DeprecationWarning`: stderr vacío, exit 1, mensaje completo
        (`pieza.py:2` + ``id sugerido `prueba``) y la línea de resumen (`1 errores`)
    43) `_id_sugerido("--8<-- criterio del índice de knowledge COMPARTIDO")`
        -> `criterio_del_indice_de_knowledge_compartido`
    (`python tests/test_lint_plugin.py` entero sigue rojo EN WINDOWS por el caso preexistente del
     bit ejecutable de `hooks/hooks.json`, línea base; por eso se invocan las funciones de casos)

$ # GAP 6 — la ruta de error ANTES (re.split con maxsplit posicional) y DESPUÉS, con
$ #   `# --8<-- prueba` añadido a agent-kits/shared/usage-meter.py
$ python -W error::DeprecationWarning $TMP/lint_pre_g6.py --root .
  exit=1   stdout=0 bytes   stderr=1349 bytes
  ...
  DeprecationWarning: 'maxsplit' is passed as positional argument
$ python -W error::DeprecationWarning scripts/lint_plugin.py --root .
  exit=1   stderr=0 bytes
[X] agent-kits/shared/usage-meter.py:629: bloque replicado con centinela `--8<-- prueba` SIN fila en
    agent-kits/shared/copias.json - declara el bloque (id sugerido `prueba`) o quita el centinela
    (ADR-016)
lint_plugin: 9 agentes · 1 errores · 3 avisos
$ # revertido: `git diff --stat agent-kits/shared/usage-meter.py` vacío

$ # GAP 7 — prefijo vs. línea entera, sobre la MISMA fixture (caso 41)
ANTES (startswith) -> exit 0 | lint_plugin: 1 agentes · 0 errores · 0 avisos
DESPUES (igualdad) -> exit 1 | pieza.py:4: bloque replicado con centinela
    `--8<-- criterio compartido v2 (bloque NUEVO sin registrar)` SIN fila en ... (id sugerido
    `criterio_compartido_v2`) | lint_plugin: 1 agentes · 1 errores · 0 avisos
$ # y sobre el ÁRBOL, el mismo `v2` al final de tests/test_console_encoding.py:
[X] tests/test_console_encoding.py:1130: bloque replicado con centinela `--8<-- criterio de consola
    COMPARTIDO v2 (bloque NUEVO sin registrar)` SIN fila en agent-kits/shared/copias.json ...
lint_plugin: 9 agentes · 1 errores · 3 avisos
$ # revertido -> 0 errores

$ # GAP 10 — instalación por copia: lint_plugin.py + task-brief.py + ledger-lint.py bajo .claude/
ANTES  (COPIAS_SKIP_DIRS sin las 4 raíces): lint_plugin: 9 agentes · 11 errores · 3 avisos
DESPUÉS (con .claude/.codex/.opencode/.agents): lint_plugin: 9 agentes · 0 errores · 3 avisos
$ # borradas las copias de .claude/

$ python scripts/release.py --dry-run ; echo $?
OK: todas coinciden en 1.19.0
CHANGELOG.md    : sección [1.19.0] presente
CHANGELOG.es.md : sección [1.19.0] presente
0
$ python scripts/export-interop.py --check
export-interop --check: 48 ficheros al día
$ python evals/check.py
evals/check: 38 ficheros · 135 casos (80 positivos, 55 negativos) · 38 piezas del repo · 0 errores
$ python agent-kits/shared/ledger-lint.py docs/roadmap/2026-09-09-plugin-refactor/tasks.md
ledger-lint: 0 incoherencias · 0 avisos (tasks.md)

$ # SUITE POR CONJUNTO (antes de tocar nada en esta pasada vs. al final, árbol limpio)
$ diff $CAP/suite-antes-r3i2.txt $CAP/suite-despues-r3i2.txt
1204a1205
> PASSED tests/test_copias_declaradas.py::test_cada_respaldo_declarado_esta_definido_en_su_bloque
1206a1208
> PASSED tests/test_copias_declaradas.py::test_el_respaldo_es_equivalente_al_canonico[glob_to_regex]
    1.481 -> 1.483 líneas · SOLO las 2 nuevas de test_copias_declaradas · ninguna perdida
$ diff <(grep ^FAILED antes) <(grep ^FAILED despues)   # vacío: los MISMOS 40 rojos preexistentes
```

**Verificación RE-EJECUTADA tras la corrección de los gaps B-3 y B-4 de la revisión R3 — intento 2** (GOT-007: la que vale es esta):
```
$ python scripts/lint_plugin.py --root . ; echo $?
lint_plugin: 9 agentes · 0 errores · 3 avisos
0
$ # CONTRATO del tramo: stdout byte a byte igual al de HEAD sobre el mismo arbol.
$ # La copia de HEAD vive FUERA del repo ($TEMP/pr-head-r3i3, `git archive HEAD | tar -x`) y se
$ # ejecuta desde ahi con `--root .`. Hay que `git init` + `git add -A` en la copia: sin indice,
$ # `_es_ejecutable` cae al modo del sistema de ficheros y en Windows/OneDrive TODO sale
$ # ejecutable -> un aviso fantasma de `hooks/hooks.json` (4 avisos en vez de 3). Con indice, 3.
$ diff $CAP/lint-head-r3i3.out $CAP/lint-despues-r3i3.out && echo "STDOUT IDENTICO A HEAD"
STDOUT IDENTICO A HEAD
$ wc -c $CAP/lint-head-r3i3.err $CAP/lint-despues-r3i3.err
0 lint-head-r3i3.err
0 lint-despues-r3i3.err

$ # B-3 — ESCENARIO DE LA LENTE B sobre el arbol desechable: el canonico `REVISION_HDR_PATTERN`
$ #   renombrado a `_REVISION_HDR_FALLBACK` en ledger-lint.py:186, DENTRO del rango de su copia
$ python scripts/lint_plugin.py --root .
❌ agent-kits/shared/ledger-lint.py:186: constante de respaldo `_REVISION_HDR_FALLBACK` SIN fila en
   agent-kits/shared/copias.json — declárala en el bloque de su canónico (id sugerido
   `revision_hdr_fallback`) (ADR-016)
lint_plugin: 9 agentes · 1 errores · 4 avisos
    (el 4.º aviso es el fantasma de hooks.json del arbol sin indice, no una regresion)
    (en el intento 2 esto PASABA: `respaldos` era de bloque y la tolerancia se repartia a las 3
     rutas; ahora vive en copias[i].respaldos, solo en task-brief.py y jira-flow.py)

$ # B-4 — ESCENARIO: segunda copia del bloque glob_to_regex al final de scope-check.py
$ python scripts/lint_plugin.py --root .
❌ agent-kits/shared/scope-check.py:264: el centinela `--8<-- glob_to_regex (respaldo local) —
   REPLICADO LITERAL en agent-kit` aparece 2 veces en este fichero y agent-kits/shared/copias.json
   declara 1 — una copia de más del mismo bloque en un fichero YA declarado no la compara nadie:
   quítala o declárala como copia aparte (ADR-016)
❌ agent-kits/shared/scope-check.py:284: el centinela `--8<-- fin glob_to_regex (respaldo local)`
   aparece 2 veces en este fichero y agent-kits/shared/copias.json declara 1 — …
lint_plugin: 9 agentes · 2 errores · 4 avisos
    (en el intento 2: `0 errores` — el linter solo comprobaba pertenencia, no cuantas)

$ # `python tests/test_lint_plugin.py` entero sigue ABORTANDO EN WINDOWS en el caso preexistente
$ # del bit ejecutable de `hooks/hooks.json` (identico en HEAD, linea base): los casos de copias
$ # se verifican invocando las funciones `casos_*` directamente, como en el intento 1.
$ python -c "…importlib…; casos_copias_declaradas(); casos_copias_registro_fino(); casos_copias_por_copia()"
OK casos_copias_declaradas
OK casos_copias_registro_fino
OK casos_copias_por_copia          # casos 44 (B-3) y 45 (B-4), nuevos
    44) `respaldos` POR COPIA: con la constante declarada en SU copia -> `0 errores`; renombrado el
        CANONICO a `_PATRON_FALLBACK` (dentro del rango de su copia) -> exit 1 con `canon.py:2`, y
        `copia.py` (la que si lo declara) NO aparece en el error
    45) una sola aparicion del centinela -> `0 errores`; pegada una SEGUNDA copia del bloque ->
        exit 1 con `pieza.py:4` (inicio sobrante) y `pieza.py:6` (fin sobrante), «aparece 2 veces»
    (los casos 39, 40 se actualizan a la forma por copia: `copias[i].respaldos`. Contador 45/45)

$ python scripts/release.py --dry-run 1.20.0 ; echo $?
OK: todas coinciden en 1.19.0
CHANGELOG.md    : sección [1.19.0] presente
CHANGELOG.es.md : sección [1.19.0] presente
--dry-run: no se ha tocado nada.
0
    (con `--dry-run 0.0.0` la puerta responde «la versión 0.0.0 no es mayor que la actual 1.19.0»,
     que es su comportamiento correcto: el dry-run necesita una versión hacia delante)
$ python scripts/export-interop.py --check
export-interop --check: 48 ficheros al día
$ python evals/check.py
evals/check: 38 ficheros · 135 casos (80 positivos, 55 negativos) · 38 piezas del repo · 0 errores
$ python agent-kits/shared/ledger-lint.py docs/roadmap/2026-09-09-plugin-refactor/tasks.md
ledger-lint: 0 incoherencias · 0 avisos (tasks.md)

$ # SUITE POR CONJUNTO (antes de tocar nada en esta pasada vs. al final, arbol limpio)
$ diff $CAP/suite-antes-r3i3.txt $CAP/suite-despues-r3i3.txt
1182c1182,1183
< PASSED tests/test_copias_declaradas.py::test_cada_respaldo_declarado_esta_definido_en_su_bloque
---
> PASSED tests/test_copias_declaradas.py::test_cada_centinela_declarado_aparece_exactamente_una_vez_en_su_ruta
> PASSED tests/test_copias_declaradas.py::test_cada_respaldo_declarado_esta_definido_en_su_copia
1183a1185
> PASSED tests/test_copias_declaradas.py::test_el_corpus_de_equivalencia_cubre_todas_las_categorias[glob_to_regex]
    PASSED 1.421 -> 1.423 · FAILED 38 -> 38 (el MISMO conjunto, diff vacio) · ERROR 0 · SKIPPED 1
    Las 2 lineas nuevas son de test_copias_declaradas; la «perdida» es el RENOMBRADO
    `..._en_su_bloque` -> `..._en_su_copia` (Desviacion declarada 10), no un test borrado.
    El conjunto de esta pasada es `tests agent-kits/shared skills` (sin `evals`): por eso el
    contador de rojos preexistentes es 38 y no los 40 de las pasadas que si incluian `evals`.
    Lo que se compara es el CONJUNTO antes/despues de esta misma pasada, no el numero.
```

---

## Fase 4 — Encadenamiento E1–E11

**Desviación declarada 11 — `scope-check.py` sigue en exit 1, y no por esta pasada.** El DoD pide `scope-check` en verde. Sale **exit 1** con 7 ficheros fuera de alcance: `.claude/.confluence-pending`, `.claude/.gitignore`, `.claude/.headroom_wrap_marker.json` (estado local de herramientas), `CONTINUE-HERE.md` y `CONTINUE-HERE.local.md` (bitácora de sesión, raíz del repo), `feature-pendiente.bundle` y `docs/roadmap/2026-09-09-plugin-refactor/design.md`. **Ninguno lo toca esta 4.ª pasada** —cuyos 5 ficheros salen los 5 en ✅ «en alcance»— y el encargo excluía explícitamente `design.md`. Es ruido de árbol y artefactos de pasadas anteriores que arrastra el tramo: se declara aquí en vez de tocarlos para cuadrar un exit code, que es justo lo que la tabla de racionalización del implementer prohíbe. Lo resuelve el ritual de cierre de rama (commits ordenados), no una corrección de código.


**Verificación RE-EJECUTADA tras la 4.ª pasada (autorizada por el usuario, fuera del bucle acotado) — gap R3-3**
(GOT-007: la que vale es esta, no las anteriores):
```
$ # R3-3: el caso 46 nuevo. `python tests/test_lint_plugin.py` ABORTA antes en Windows (caso `chmod`,
$ # rojo preexistente), asi que el caso se verifica llamando a la funcion directamente.
$ python -c "import sys; sys.path.insert(0,'tests'); import test_lint_plugin as t; t.casos_copias_forma_de_definicion()"
    (sin salida = OK). Lo que afirma el caso, con `copia.py` =
        import re
        _NUEVO_FALLBACK: str = r"^x$"                  <- ANOTADA
        _OTRO_FALLBACK = _TERCERO_FALLBACK = r"^y$"    <- ENCADENADA (dos nombres)
        usa = _NUEVO_FALLBACK                          <- USO en el valor, no definicion
    -> exit 1 y **3 errores** (`out.count("constante de respaldo") == 3`):
       `copia.py:2` con `_NUEVO_FALLBACK`; `copia.py:3` con `_OTRO_FALLBACK` **y** `_TERCERO_FALLBACK`;
       `copia.py:4` NO aparece. Declaradas las dos lineas en copias.json -> exit 0 y `0 errores`.
$ # y los tres grupos previos de casos de copias siguen verdes:
$ python -c "... t.casos_copias_declaradas(); t.casos_copias_registro_fino(); t.casos_copias_por_copia()"
casos_copias_* previos: OK

$ # CONTRATO del tramo: stdout byte a byte igual al de HEAD sobre el mismo arbol.
$ # Copia de HEAD FUERA del repo ($TEMP/pr-head-r3i4, `git archive HEAD | tar -x` + `git init` +
$ # `git add -A`, para que `_es_ejecutable` lea el indice y no el modo de OneDrive), con `--root .`.
$ python scripts/lint_plugin.py --root . ; echo $?
lint_plugin: 9 agentes · 0 errores · 3 avisos
0
$ diff $CAP/lint-head-r3i4.txt $CAP/lint-ahora-r3i4.txt && echo IDENTICO
IDENTICO
$ wc -c $CAP/lint-head-r3i4.err $CAP/lint-ahora-r3i4.err
0 lint-head-r3i4.err
0 lint-ahora-r3i4.err

$ python evals/check.py ; echo $?                     -> 0
$ python scripts/export-interop.py --check            -> export-interop --check: 48 ficheros al día
$ python scripts/release.py --dry-run ; echo $?
OK: todas coinciden en 1.19.0 · CHANGELOG.md y CHANGELOG.es.md: sección [1.19.0] presente
0
$ python agent-kits/shared/ledger-lint.py docs/roadmap/2026-09-09-plugin-refactor/tasks.md ; echo $?
ledger-lint: 0 incoherencias · 0 avisos (tasks.md)
0
$ python agent-kits/shared/scope-check.py docs/roadmap/2026-09-09-plugin-refactor ; echo $?
scope-check: 2026-09-09-plugin-refactor · base merge-base master…HEAD (400b3fd0) · 25 fichero(s)
  cambiado(s) · 153 patrón(es) declarados en Archivos
✅ en alcance (18)  — TODO lo que toca esta 4.ª pasada: scripts/lint_plugin.py,
   tests/test_lint_plugin.py, tests/test_copias_declaradas.py, agent-kits/shared/copias.json y
   docs/roadmap/2026-09-09-plugin-refactor/tasks.md
❌ fuera de alcance (7): .claude/.confluence-pending · .claude/.gitignore ·
   .claude/.headroom_wrap_marker.json · CONTINUE-HERE.local.md · CONTINUE-HERE.md ·
   docs/roadmap/2026-09-09-plugin-refactor/design.md · feature-pendiente.bundle
1     <- exit 1 PREEXISTENTE (ver «Desviación declarada 11»): los 7 son ruido de arbol y
          artefactos de pasadas anteriores; esta pasada NO toca ninguno.

$ # Suite por CONJUNTO, con la recoleccion COMPLETA (leccion de R3-5: `evals/test_evals.py`, 21
$ # tests, SI se recoge; la linea base vuelve a ser 40 rojos, no 38).
$ python -m pytest -q tests agent-kits/shared skills evals -rA -p no:cacheprovider | grep -E "^(PASSED|FAILED|ERROR|SKIPPED)" | sort > $CAP/suite-despues-r3i4.txt
$ diff $CAP/suite-antes-r3i4.txt $CAP/suite-despues-r3i4.txt
1210a1211
> PASSED tests/test_copias_declaradas.py::test_las_categorias_obligatorias_siguen_declaradas_en_el_registro[glob_to_regex]
    1.485 -> 1.486 lineas · PASSED 1.444 -> 1.445 · SKIPPED 1 · la UNICA linea nueva es la del test
    de R3-1; ninguna perdida. El caso 46 de `test_lint_plugin.py` no aparece porque pytest no
    colecta esa suite-script (rojo preexistente por el bit ejecutable de Windows).
$ diff (solo FAILED/ERROR, antes vs despues)   # vacio
    FAILED 40 -> 40, el MISMO conjunto; `evals/test_evals.py` recogido: 21 tests.

$ # Cero cambio en bloques registrados: el delta de la pasada toca el DETECTOR y los tests, no los
$ # bloques `--8<--` ni sus copias (los 7 tests de identidad siguen verdes).
$ python -m pytest -q tests/test_copias_declaradas.py -p no:cacheprovider
18 passed in 0.21s
```


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

## Revision de dos lentes - intento 1 (tramo R1: T-01..T-04): 5 Important, 10 Minor (lentes A+B)

Lentes A (conformidad con ledger/plan/spec, criterio de prosa) y B (persona `test`) al agente `reviewer`,
en paralelo, contexto fresco. `review-lens-select.py --base HEAD`: `lente_c`/`lente_d: false`. Puerta previa
`scope-check.py --base HEAD`: 14 ficheros en alcance (tras declarar `code-health-baseline-2.md` en T-02);
los 5 fuera son el ruido previo fichado. **Coste de la revision, MEDIDO desde la sesion principal**
(marcador `plugin-refactor/revision-R1-intento1`, 13:22:28Z -> 13:59:50Z): 62 respuestas, **9,30 EUR**,
1,28 h IA, `duracion_reloj` 37m (coincide con la ventana real: la clave nueva de T-04 funciona en vivo).

**Lo que las lentes confirmaron como solido (no rehacer):** el brief de `task-brief.py` es **byte a byte
identico** antes y despues de partir `main()` — 520 invocaciones (todo `T-XX` de todo ledger, con y sin
`--tdd`, stdout + stderr + exit code) con 0 diferencias; `_recorte_seguro` y `presupuesto_persona` sin
divergencias en 40.000 casos de fuzz y 156 combinaciones end-to-end que ejercitan las tres ramas del
`max(SUELO, min(CAP, margen))`; suite identica por test (1426/1426, +4 PASSED aditivos); contratos
congelados intactos (multiset de `add_argument`/`sys.exit` identico salvo `--exclude-path`, la excepcion
declarada); linea base 2 reproducida exactamente (funciones largas 99 -> 97, resto igual); mutantes del
filtro `timestamp`, del detector de TODO y de `--exclude-path` mueren; `docs/observability.md` (+EN) fiel.

| # | Grado | Gap | Tarea | Correccion | Evidencia |
|---|---|---|---|---|---|
| A-1 / B-9 | **Important** | El «unico TODO real» que sobrevive a C-04 es **prosa castellana** partida en dos comentarios («medir seria contar / `# TODO el historico como ventana`»), igual que los otros siete. CA-06 se cumple al pie de la letra porque nombra esa linea, pero el objetivo de C-04 no: quedan 1 de 8 falsos positivos y **0 marcadores reales**. El error nace en `analysis.md` §4 y se propago a `spec.md`, al ledger y al `Changelog` de T-01, que publicaria «1 marcador real» siendo falso; `code-health-baseline-2.md` publica «TODO 1» como deuda | T-01 | **Corregido**: `PROSA_ES_TRAS_MARCADOR`/`_tipo_marcador` ahora reconocen la prosa castellana también cuando el marcador abre línea sin separador (`TODO el histórico…`, empieza por artículo/preposición de la lista). `todos` = 0 confirmado en repo (`marcadores.top: []`); CA-06, Verificación, Changelog y `analysis.md`/`spec.md` alineados a «8 → 0» | `code-health.py:55-96` (`PROSA_ES_TRAS_MARCADOR`, `_tipo_marcador`); verificado con `python skills/code-health/scripts/code-health.py . --exclude-tests --json` → `resumen.todos == 0` |
| B-1 | **Important** | `_parse_iso` devuelve *naive* si el ISO no lleva `Z` ni offset y solo captura `ValueError`: (i) en `close` el `TypeError` no esta capturado -> **el proceso muere** (rc=1, stdout vacio, marcador sin actualizar); (ii) en `_sum_usage_window` lo captura el `except Exception` de `cmd_close` y se pierde la medicion de **toda** la ventana por un solo registro. Contradice el docstring («registros sin timestamp parseable NUNCA se descartan») y «degradacion total: nunca bloquear». Antes de T-04 ambos casos median | T-04 | **Corregido**: `_parse_iso` asume UTC cuando el ISO llega *naive* (`dt.replace(tzinfo=timezone.utc)` en vez de dejarlo *naive*), eliminando la comparación mixta que producía el `TypeError`; además se amplió el `except` de `dur_reloj` a `(ValueError, OverflowError, TypeError)` como cinturón adicional. Ambos casos (marcador `inicio` naive, registro `timestamp` naive entre 100 correctos) miden ahora en vez de morir o descartar la ventana entera | `usage-meter.py:_parse_iso` (normaliza a aware) y broadened `except`. Tests nuevos: `test_marcador_con_inicio_naive_close_no_revienta_y_mide`, `test_registro_con_timestamp_naive_entre_correctos_se_cuenta` (asserta `tokens_reales.respuestas == 101`, no 0/crash). Mutante (revertir `_parse_iso`) → ambos tests rojos |
| B-2 | **Important** | `ENUMERACION_RE` se evalua antes que `TODO_RE` y excluye cualquier linea con **dos spans entre backticks separados por coma**, sea cual sea su contenido: suprime anotaciones reales inequivocas (`TODO:`). La regla del ledger dice «lineas que enumeran >= 2 **marcadores** distintos»; la implementada es «>= 2 backticks de cualquier cosa». En un repo con backticks como estilo de casa, falso negativo sistematico y silencioso | T-01 | **Corregido con una regla más precisa que la propuesta literal** (ver nota de rebate abajo): `_es_enumeracion_de_marcadores` exige que el marcador (`TODO`/`FIXME`/…) esté él mismo DENTRO de un span entre backticks (`` `TODO: …` ``, cita literal) **y** que haya ≥ 2 spans en la línea — no basta con «≥ 2 backticks de cualquier cosa». El fixture del gap (`# TODO: unificar \`a.py\`, \`b.py\`` y `# FIXME: el parser rompe con \`foo\`, \`bar\``) ahora cuenta **2** (no 0): los dos marcadores reales sobreviven | `code-health.py:101-110` (`_MARCADOR_ENTRE_BACKTICKS_RE`, `_es_enumeracion_de_marcadores`). Test `test_todo_seguido_de_referencias_entre_backticks_si_cuenta` reproduce el fixture del gap y asserta `todos == 2` |
| B-3 | **Important** | `duracion_reloj`, la unica salida nueva de T-04, **no tiene oraculo de valor**: el test solo comprueba que la clave existe. Mutante `dur_reloj = None` -> 50 passed; `= fmt_horas(0.0)` -> 50 passed. Un calculo de reloj roto pasaria la puerta (los otros cinco mutantes de T-04 si mueren) | T-04 | **Corregido**: nuevo test `test_duracion_reloj_valor_exacto_37_minutos` con oráculo de VALOR (`inicio`/`fin` separados exactamente 37 min reales vía `_now_marker(delta=...)` → `assert res["duracion_reloj"] == "37m"`), no solo presencia de la clave | `test_usage_meter.py::test_duracion_reloj_valor_exacto_37_minutos`. Mutante `dur_reloj = None` / `= fmt_horas(0.0)` → este test se pone rojo (verificado manualmente, restaurado después) |
| A-2 | **Important** | CA-09 de T-03 («`git diff --stat -- agents commands 'skills/*/SKILL.md'` vacio para este commit») marcado `[x]` y la subtarea «commit `T-03: …`» marcada hecha: **no existe ningun commit** de R1 (el orquestador comitea por tarea tras la revision, y asi se le dijo al implementer). Contra el arbol el comando devuelve `skills/code-health/SKILL.md \| 8 +++---` (cambio legitimo de T-02, que ira en SU commit) | T-03 | **Corregido en el ledger**: la subtarea ya no dice «commit `T-03: …`», dice que el commit lo hace el orquestador tras el cierre de R1 (fuera del alcance del implementer, cuyo hook de guardia solo permite `tasks.md`). CA-09 queda reformulado: se evalúa por commit cuando existan (separando el de T-02, que sí toca `SKILL.md`, del de T-03); mientras tanto se confirma que **T-03 en sí** no toca ninguna ruta protegida | `tasks.md` T-03 CA-09 y subtarea de commit, ambas reescritas; `git log master..HEAD` sigue sin commits de R1 (correcto, sin commits en esta sesión por instrucción explícita) |
| A-4 | Minor | CA-07 («sin flag, salida **byte-identica** a la de T-01») marcado `[x]` cuando la propia evidencia pegada da `False` (auto-medicion: `code-health.py` crecio 13 lineas); la desviacion esta explicada dentro de la salida, sin bloque «Desviacion declarada» como en T-03/T-04 | T-02 | **Corregido**: añadido bloque explícito «Desviación declarada (A-4)» en T-02, con el mismo formato que T-03/T-04, explicando que el `False` inicial es auto-medición esperada (el detector se analiza a sí mismo) y que el CA se cumple tras excluir esas claves | `tasks.md` T-02, bloque «Desviación declarada (A-4)» entre Subtareas y Verificación ejecutada |
| A-5 | Minor | La segunda linea base **no registra el flag que la define**: ni `parametros` del JSON ni la linea «Parametros» del MD mencionan `--exclude-path interop`. Quien compare las dos lineas base (7,5 % / 104 vs 5,9 % / 99) sin leer el ledger atribuye la diferencia al refactor: la «mejora ficticia» que S-4 existe para evitar | T-02 | **Corregido**: `analizar()` añade `exclude_path` (prefijos normalizados) a `parametros`; `md()` lo imprime en la línea «Parámetros» cuando la lista no está vacía. Línea base 2 regenerada: `parametros.exclude_path == ['interop']` visible en JSON y MD | `code-health.py` (`analizar()`/`md()`, clave `exclude_path`); `docs/roadmap/2026-09-09-plugin-refactor/code-health-baseline-2.json` regenerado — `parametros: {..., 'exclude_path': ['interop']}` |
| A-6 | Minor | `(medido)` en T-02 y T-03 sin el JSON del `close` pegado: no reproducible (sus marcadores ya no existen en `usage-state.json`). T-01 y T-04 si explican su `(estimado)` | T-02, T-03 | **Corregido**: ambos rebajados de `(medido)` a `(estimado)` con la misma nota que T-01/T-04 (marcador original no reproducible en `usage-state.json`); el trabajo de esta corrección (fix1) sí se midió con el `usage-meter.py` del árbol de trabajo, JSON pegado en el cierre de R1 | `tasks.md` T-02/T-03, campo «Tiempo IA (ejec.)» |
| A-3 | Minor | `improvement-plan.md` modificado en R1 (frontmatter `plan/estado/creado/actualizado`) sin figurar en el `Archivos` de ninguna tarea de F1; `scope-check` lo da en alcance por T-22. **Lo edito el orquestador** (transiciones de la puerta y la plantilla del planner sin `estado:`), no el implementer | — | orquestador: declarado aqui | `improvement-plan.md:2-5`. Hueco de encadenamiento para la matriz de contratos (T-14): la plantilla del `planner` no trae `estado:`/`tasks:`/`plan:` y `changelog-sync` los exige |
| A-7 | Minor | T-03 es la unica tarea de R1 sin `- **Tipo**:`; sin el, el brief no enruta persona ni memoria por tipo | T-03 | **Corregido**: añadido `- **Tipo**: refactor` a T-03, con nota de por qué faltaba | `tasks.md` T-03, campo `Tipo` |
| A-8 | Minor | El `Archivos` de T-02 arrastra un patron basura `.md` (texto «… `.json` y `.md`»); `scope-check --json` lo lista en `declarados_sin_tocar` | T-02 | **Corregido**: retirado el fragmento duplicado/basura del campo `Archivos` de T-02 (quedaba una entrada residual «`.md` (informe legible…)» repetida tras describir ya el JSON+MD) | `tasks.md` T-02, campo `Archivos` |
| B-4 | Minor | Dentro de la tolerancia de 60 s, un registro ya medido por el marcador anterior se vuelve a contar si reaparece en un fichero no visto en el `start` del siguiente (marcadores encadenados en el mismo minuto): A mide 100, B mide **105** en vez de 5, sin aviso. No es regresion (antes se contaba el fichero entero), pero es la grieta del parametro y no hay test de encadenados | T-04 | **Documentado, NO corregido (fuera de alcance declarado)**: es un límite conocido del parámetro de tolerancia (60 s), no una regresión — antes de T-04 se contaba el fichero entero, ahora en el peor caso se duplican unos pocos registros de la ventana de solape. Corregir el dedupe real (por `id` de registro entre marcadores encadenados) es un cambio de mayor alcance que excede esta corrección de gaps; se documenta el límite en `docs/observability.md` (+EN). **Corrección de test añadida en esta sesión:** `test_b4_marcadores_encadenados_dentro_de_60s_duplican_solape` reutilizaba un fichero YA EXISTENTE al `start` de B, así que su offset lo baselineaba correctamente y el test no reproducía el hueco real (pasaba por una razón distinta a la documentada). Corregido para que el fichero con los registros «reaparecidos» se cree DESPUÉS del `start` de B (como un subagente que escribe su propio transcript) — ahora sí ejercita la ruta de offset-0 + ventana de 60 s descrita en la fila; sigue en verde con el mismo valor esperado (105) | `docs/observability.md` y `docs/en/observability.md`, sección nueva sobre el límite de encadenados en 60 s; `agent-kits/shared/test_usage_meter.py::test_b4_marcadores_encadenados_dentro_de_60s_duplican_solape` (corregido) y `::test_b4_con_90s_de_separacion_no_hay_solape` (contraste) — `python -m pytest -q agent-kits/shared/test_usage_meter.py` → **56 passed** |
| B-5 | Minor | Un marcador `version: 2` **sin `inicio`** desactiva el filtro en silencio y vuelve al bug exacto que T-04 arregla, reportando `fuente: medido`. `offsets` si tiene defensa (`:453`); `inicio` no | T-04 | **Corregido**: nueva rama en `cmd_close` — un marcador con `version: 2` pero sin `inicio` (¿corrupto o editado a mano?) degrada a estimado con aviso explícito, igual que un marcador sin `version` | `usage-meter.py:cmd_close`, rama `elif not marcador.get("inicio")`. Test `test_marcador_version2_sin_inicio_degrada_con_aviso` |
| B-6 | Minor | `DETECTOR_PROPIO` compara por **basename**: cualquier `code-health.py` de un consumidor pierde todos sus marcadores | T-01 | **Corregido**: `DETECTOR_PROPIO = os.path.realpath(__file__)`; la comparación en el bucle de `marcadores()` usa la ruta real normalizada del fichero analizado (`os.path.realpath(os.path.join(root, ...))`), no el `basename` | `code-health.py:119` (`DETECTOR_PROPIO`), `:396` (comparación por ruta real). Test `test_el_propio_fichero_del_detector_se_excluye_por_ruta_real` (reemplaza el test por basename) |
| B-7 | Minor | 3 de los 4 tests nuevos de T-04 leen `docs/roadmap/CALIBRATION.md` real y los 4 `.claude/rates.json` real (la fixture no hace `chdir`). Patron **preexistente** del fichero heredado por los nuevos; hoy no cambia veredictos | T-04 | **Corregido**: helper `_hermetico(tmp_path)` (`--calibration`/`--rates` apuntando a ficheros inexistentes bajo `tmp_path`) aplicado a los 4 tests señalados y reutilizado en los 2 tests nuevos de B-1; ninguno depende ya de `CALIBRATION.md`/`rates.json` reales del repo | `test_usage_meter.py:_hermetico` y sus 6 usos (`test_registro_anterior_al_inicio…`, `test_tolerancia_60s…`, `test_marcador_sin_version…`, `test_duracion_reloj_aditiva…`, más los 2 nuevos de B-1) |
| B-8 | Minor | El mutante del test de T-01 parchea `os.path.basename` **global** del interprete (afecta a todo el proceso, incluido el `subprocess` de `git log`); `ch.DETECTOR_PROPIO = "nunca-coincide.py"` seria el mutante equivalente y acotado | T-01 | **Corregido**: `test_mutante_detector_propio_nunca_coincide_sube_el_recuento` sustituye el parche global de `os.path.basename` por `monkeypatch.setattr(ch, "DETECTOR_PROPIO", "nunca-coincide.py")`, acotado al módulo bajo test | `test_code_health.py::test_mutante_detector_propio_nunca_coincide_sube_el_recuento` |

**Fuera de las lentes, para el refactor (no gap de R1):** `TODO_RE` ya no reconoce `TODO(nombre):` (Go/Java/C++)
salvo al abrir el comentario — efecto colateral no declarado en `spec.md:116`; y `duracion_reloj` es un
campo nuevo del JSON de `close` que `roadmap-dashboard`/plantillas no consumen aun (informativo).

## Corrección de los 15 gaps (R1, intento 1) — cierre

**Verificado cada gap contra el código antes de corregir (disciplina «no aplicar feedback a ciegas»).**
14 de los 15 confirmados correctos y corregidos; ninguno rebatido como incorrecto. Dos merecen nota porque
la corrección aplicada **no es literalmente** la redacción propuesta en la columna «Gap», sino una regla
más precisa que consigue el mismo objetivo (mismo oráculo/fixture) sin romper comportamiento ya verificado
por tests existentes que la redacción literal SÍ habría roto:

- **B-2** — la redacción del gap («excluir líneas que enumeran ≥ 2 marcadores distintos») tomada al pie de
  la letra (¿2 palabras TODO/FIXME distintas en la misma línea?) habría reintroducido el falso positivo que
  A-1 acababa de eliminar en el estilo real de `journal.py:41` (una sola palabra marcador, varias referencias
  entre backticks) y habría dejado pasar líneas de puro estilo-con-backticks sin marcador real. Se implementó
  la regla que realmente separa ambos casos con evidencia (`code-health.py:101-110`): el marcador debe estar
  él mismo dentro de un span entre backticks para contar como «enumeración»; en caso contrario (marcador
  fuera de backticks + ≥ 2 spans de referencias) es un marcador real. Verificado con el fixture exacto del
  gap (2, no 0) Y con el test preexistente de `journal.py`-style (sigue en 0) — ambos pasan a la vez, algo
  que la redacción literal no permitía.
- **A-1/B-9** — el gap señala el «único marcador real» como bug de spec/ledger, no pide un cambio de regex
  explícito; la corrección técnica (ampliar `PROSA_ES_TRAS_MARCADOR`/`_tipo_marcador` para que ese comentario
  cuente como prosa igual que los otros 7) es la que hace que CA-06 y C-04 («8 → 0») sean ciertos a la vez;
  documentada en el código como referencia a «revisión R1, A-1».

**Medición de la corrección (usage-meter.py del árbol de trabajo, no el del caché del plugin), un marcador
por tarea, cerrado antes de abrir el siguiente:**

```
plugin-refactor/T-01-fix1: {"eur": 0.05, "horas_ia": 0.0, "duracion": "0m", "duracion_reloj": "0m",
  "fuente": "medido", "tokens_reales": {"entrada": 2, "salida": 202, "cache_creacion": 798,
  "cache_lectura": 86107, "respuestas": 1}}
plugin-refactor/T-02-fix1: {"fuente": "estimado", "duracion_reloj": "0m",
  "avisos": ["ventana sin respuestas del modelo (¿start y close seguidos?)"]}
plugin-refactor/T-03-fix1: {"fuente": "estimado", "duracion_reloj": "0m",
  "avisos": ["ventana sin respuestas del modelo (¿start y close seguidos?)"]}
plugin-refactor/T-04-fix1: (ver JSON más abajo, cerrado tras el resto del trabajo de T-04)
```

**Nota de honestidad sobre la medición**: el grueso del trabajo de corrección de los 15 gaps se hizo en una
sesión previa que se interrumpió por compactación de contexto; los marcadores `*-fix1` se abrieron y
cerraron en ESTA sesión de cierre (verificación final, regeneración de línea base, redacción del ledger),
así que miden esa cola final, no el esfuerzo completo de corrección — de ahí que T-02/T-03 degraden a
`estimado` (ventana sin respuestas) y T-01 mida solo 1 respuesta. Las horas reales de implementación de los
15 gaps quedan a juicio, marcadas `(estimado)` en cada tarea, siguiendo la misma disciplina que T-01/T-04 ya
aplicaban para sus propios marcadores no representativos.

## Revision de dos lentes - intento 2 (tramo R1): 1 Important, 2 Minor — verificacion determinista del orquestador (lente caida)

La Lente B del intento 2 murio por el limite de sesion antes de reproducir nada (tercera caida de agente del
dia). En vez de relanzarla, el orquestador ejecuto **los oraculos deterministas** que le habia pedido, sobre
copias en ruta corta (`C:/Users/460669~1/AppData/Local/Temp/mutr1`) y sin tocar el repo. Coste de la ventana de
revision (marcador `plugin-refactor/revision-R1-intento2`): medido: 12 respuestas, 8,63 EUR, duracion_reloj 1h 55m (incluye la ventana de la lente caida y la verificacion del orquestador).

| Comprobacion | Resultado |
|---|---|
| Mutante B-1: `_parse_iso` devuelve naive (sin `tzinfo=timezone.utc`) | **1 failed**, 55 passed — el test muerde |
| Mutante B-3: `dur_reloj = None` | **2 failed**, 54 passed — oraculo `"37m"` muerde |
| Mutante B-5: sin la defensa de marcador sin `inicio` | **1 failed**, 55 passed |
| Mutante A-1: sin la lista castellana tras el marcador | **1 failed**, 22 passed |
| **Mutante B-6: `DETECTOR_PROPIO = 'nunca-coincide'`** | **23 passed — SOBREVIVE** (ver gap 1) |
| B-7 hermeticidad (`--ratio`/`--rates`/`chdir` en los tests nuevos) | 11 usos; ninguno lee `CALIBRATION.md`/`rates.json` reales |
| B-8 mutante acotado (`monkeypatch` sobre `DETECTOR_PROPIO`, sin `os.path.basename` global) | 6 usos / 0 |
| B-4 limite de 60 s documentado en `docs/observability.md` y espejo EN; tests de encadenados | si / si; 2 tests (`105` y `5` con 90 s) |
| `_parse_iso`: naive -> UTC, `Z` -> UTC, `+02:00` -> conservado, basura -> `None` | correcto |
| TODO en el repo (ejecutando el detector DESDE el repo) | **0**; `exclude_path: ['interop']` registrado en la linea base 2 regenerada |
| Limites de la regla castellana (fixture de 11 lineas) | `TODO:`/`TODO(juan):`/ingles -> contados; «TODO el historico» -> excluido (bien); **«TODO en produccion esto falla», «TODO de verdad: arreglar», «FIXME la cache» -> excluidos** (marcadores reales en castellano sin `:` justo tras la palabra: limite a documentar, ver gap 3) |

| # | Grado | Gap | Tarea | Correccion | Evidencia |
|---|---|---|---|---|---|
| R2-1 (B-6 residual) | **Important** | `DETECTOR_PROPIO = os.path.realpath(__file__)` solo excluye a la copia que se esta ejecutando. Los agentes ejecutan el kit desde la **cache del plugin** (`~/.claude/plugins/cache/...`), asi que sobre ESTE repo el `code-health.py` del arbol vuelve a contar: **9 falsos positivos** (docstring y codigo del propio detector), frente a 0 ejecutado desde el repo. La linea base 2 dice 0 y un agente mediria 9: dos verdades segun quien mida. Y el test de B-6 **no mata al mutante** (`'nunca-coincide'` -> 23 passed): prueba un fichero de fixture, no la exclusion real | T-01 | corregido: `FIRMA_DETECTOR` + `_es_detector_propio()` (firma de contenido, ademas de `realpath`); 2 tests nuevos (copia real -> excluida; mutante de firma -> `total > 0`) | `python <copia>/code-health.py <repo> --exclude-tests --exclude-path interop --json` -> `total: 9`, todos en `skills/code-health/scripts/code-health.py` (`:18`, `:461`, `:486`, `:526`, `:113`, `:53`...). Correccion: excluir por **firma de contenido** (el fichero se declara detector: su docstring contiene un literal fijo, p. ej. el titulo «code-health.py — informe DETERMINISTA»), ademas de `realpath(__file__)`; test con (a) una copia real del detector bajo otra ruta -> excluida y (b) un `code-health.py` de fixture que NO es el detector -> contado; el mutante debe caer |
| R2-2 (B-2 residual) | Minor | La exclusion «>= 2 palabras-marcador en la misma linea» pedida en la correccion de B-2 **no esta implementada**: se quito la regla ancha (backticks) y no se puso la buena. En este repo el total es 0 porque el unico fichero que enumera marcadores es el propio detector; en un consumidor, un comentario que enumere marcadores cuenta como marcador | T-01 | corregido: `_es_enumeracion_de_palabras_marcador()` (cadena de >=2 marcadores distintos separados solo por `/`, `,`, `\|` o espacios); 2 tests nuevos + 1 mutante | Fixture: `# Busca marcadores TODO/FIXME/HACK en el codigo` -> CONTADO (tipo FIXME) antes de la correccion, EXCLUIDO despues. Deben contarse `# TODO: quitar el FIXME de abajo` (uno real) y `# TODO: unificar \`a.py\`, \`b.py\`` (si se cuentan hoy) |
| R2-3 | Minor | Limite de la regla castellana **sin documentar**: un marcador real en castellano que NO lleve `:`/`(`/`-` justo tras la palabra («`# TODO en produccion esto falla`») queda excluido como prosa. Es un compromiso razonable (el estilo `TODO:` es la convencion), pero tiene que estar escrito en el docstring del detector y en `skills/code-health/SKILL.md` («escribe `TODO:` con dos puntos si quieres que cuente») | T-01 | corregido: documentado en el docstring de `PROSA_ES_TRAS_MARCADOR` (`code-health.py`) y en `skills/code-health/SKILL.md` («escribe `TODO:` con dos puntos») | fixture de 11 lineas del orquestador; `code-health.py` `PROSA_ES_TRAS_MARCADOR` |
| R2-4 (A-8 residual) | Minor | Al limpiar el patron basura de `Archivos` (A-8) desaparecio la declaracion de `code-health-baseline-2.md`; `scope-check` lo vuelve a dar «fuera de alcance». Lo redeclara el orquestador en este mismo cambio | T-02 | orquestador: corregido aqui | `scope-check.py --base HEAD` -> `fuera` incluia `code-health-baseline-2.md` |

**Sin segunda opinion de contexto fresco** (dicho, no escondido): la calidad de la prosa de los tests nuevos y la
redaccion de `docs/observability.md`. El orquestador las leyo por encima; no es una lente.

## Revision de dos lentes - intento 3 (tramo R1): 0 gaps — verificacion determinista del orquestador; TRAMO R1 CERRADO

Tercer y ultimo intento del bucle acotado. Sin lentes (las dos ultimas cayeron por la API); el orquestador ejecuto
los oraculos que la tabla del intento 2 fijaba, sobre copias en ruta corta y sin tocar el repo:

| Oraculo | Resultado |
|---|---|
| R2-1: detector ejecutado **desde una copia** (como la cache del plugin) sobre el repo, `--exclude-tests --exclude-path interop` | **`total: 0`** (antes de la correccion: 9) — exclusion por `FIRMA_DETECTOR` en las 10 primeras lineas de cualquier `code-health.py`, ademas de `realpath(__file__)` |
| R2-1: mutante A (firma anulada Y `realpath` anulado) | **1 failed, 27 passed** — el test muerde (en el intento 2 sobrevivia) |
| R2-2: mutante B (`_es_enumeracion_de_palabras_marcador` siempre `False`) | **1 failed, 27 passed** |
| R2-2/R2-3: fixture de 11 lineas | **6 contadas / 5 excluidas**: contadas `TODO: el parser`, `TODO(juan):`, `FIXME the cache`, `TODO fix the parser`, `TODO: unificar a.py, b.py`, `TODO: quitar el FIXME de abajo`; excluidas `TODO en produccion…`, `TODO de verdad: arreglar`, `FIXME la cache`, `TODO el historico…`, `Busca marcadores TODO/FIXME/HACK`. **Correccion del oraculo del orquestador**: la tabla del intento 2 decia «7 / 4»; el septimo («TODO de verdad: arreglar») empieza por «de» y cae dentro del limite castellano documentado en R2-3 — el resultado es el correcto segun la regla escrita, el oraculo estaba mal contado |
| Suites tocadas | `test_code_health` 28 · `test_usage_meter` 56 · `test_task_brief` 63 + 1 rojo preexistente (`test_ca08…memory_retrieval`, `GOT-008`) — 147 passed |
| Puertas | `lint_plugin` 0 errores · `evals/check` 0 · `export-interop --check` 48 al dia · `ledger-lint` 0 · `scope-check --base HEAD` 14 en alcance, fuera solo el ruido fichado · `SKILL.md` 100 lineas |
| Linea base 2 (regenerada tras la correccion) vs arbol | todo «= igual» (5,8 % duplicado · 272 bloques · 97 funciones largas · anidamiento 6 · TODO 0). La mejora del tramo (funciones largas 99 -> 97, TODO 8 -> 0, duplicado 7,6 % -> 5,8 % al excluir `interop/`) queda registrada en las trazas de los intentos 1 y 2 y en la diferencia entre `code-health-baseline.json` y `code-health-baseline-2.json` |

**Balance del tramo R1**: 3 intentos · 15 + 4 gaps (6 Important reales, todos corregidos, ninguno rebatido) · revision
medida desde la sesion principal: intento 1 **9,30 EUR** (62 respuestas, 37m de reloj), intento 2 **8,63 EUR** (12
respuestas, 1h 55m de reloj incluyendo la lente caida), intento 3 sin coste de lentes. Lo que las lentes aportaron y
la verificacion determinista no habria visto: el octavo TODO como prosa castellana, `ENUMERACION_RE` suprimiendo
marcadores reales, `_parse_iso` naive matando el `close`, `duracion_reloj` sin oraculo, `DETECTOR_PROPIO` roto desde
la cache. **Sin segunda opinion de contexto fresco** en los intentos 2 y 3 (dicho, no escondido).

**Commits del tramo** (los hace el orquestador, uno por tarea; CA-09 de T-03 se cumple por commit — el de T-03 no toca
`agents/`, `commands/` ni ningun `SKILL.md`): ver `git log` de `feature/plugin-refactor` tras esta seccion.

## Revision de dos lentes - intento 1 (tramo R2: T-05..T-08): 0 Critical, 0 Important, 3 Minor (lentes A+B) — TRAMO R2 CERRADO

Dos lentes de contexto fresco (agente `reviewer`, opus) en paralelo sobre `git diff HEAD` (4 scripts + ledger), con
marcador medido desde la sesion principal (`plugin-refactor/revision-R2-intento1`):
`{"eur":12.16,"horas_ia":1.27,"duracion":"1h 16m","duracion_reloj":"27m","tokens_reales":{"entrada":5926,"salida":146633,"cache_creacion":454333,"cache_lectura":13373376,"respuestas":119},"fuente":"medido"}`.

**Lente A (conformidad)** — todos los criterios de T-05..T-08 en ✓ con evidencia re-ejecutada, no leida:
salidas byte-identicas HEAD/arbol **en bruto** para `knowledge-find --json` (5 consultas + 10 rutas de exit con los
mismos codigos), `doctor` texto y `--json` (copia de HEAD ejecutada desde `agent-kits/shared/`), `lint_plugin`
(exit 0, `9 agentes · 0 errores · 3 avisos`), `build_dashboard` (`--json`/`--md`/`--html`/`--metrics-md`, `--strict`,
`--root` invalido); multiset `add_argument|sys.exit|return N` identico (la unica baja, `return 0` 4 -> 3 en
`knowledge-find`, es la desviacion declarada en T-05) y multiset de literales de texto por AST identico en
`knowledge-find` (426) y `lint_plugin` (342); suite identica **por nombre de test** (1468 lineas `-rA` contra la
captura pre-R2: mismos 1427 passed / 40 failed / 1 skipped); linea base 2: funciones largas 97 -> 78, duplicado
5,8 -> 5,7, resto igual; copias `--8<--` con el **mismo sha256** en HEAD, arbol y entre ficheros, sin ningun hunk
del diff dentro de sus rangos; `release.py --dry-run` exit 0; CA-01 = 2+0+1+4+4 = **11 <= 16**.

**Lente B (correccion, persona «especialista en tests»)** — **sin defectos** en ~27.000 ejecuciones diferenciales
HEAD vs arbol: `knowledge-find` 61 casos CLI x 2 (indice FTS5 frio y caliente, `--show`/`--related`/`--doctrina`,
acentos, solo-stopwords, consulta vacia, `--limit -1`/`abc`, combinaciones prohibidas) + `parse_indice`/`relaciones`
sobre las 42 entradas reales y 25 sinteticas; `doctor` 29 casos (5 raices: repo, sin `docs/knowledge/` ni `.claude/`,
`dev.json` corrupto, marcador huerfano, indice FTS5 corrupto y desfasado; 4 raices de plugin rotas) + `_dev_valida`
con 3.000 estructuras aleatorias + `_calibracion` 33 variantes + `OSError` inyectado en `_calibracion_leer`;
`build_dashboard` 6 corridas x 3 raices (ledger `legacy` sin frontmatter, `cancelado`, carpeta sin `tasks.md`,
titulos con HTML y pipes) + `parse_generacion` 22 entradas adversarias + CSS extraido identico (1842 B, 0 `{{`);
`lint_plugin` 16 raices (repo + 15 fixtures con frontmatter roto, `model`/`effort`/`tools` invalidos, dependencia
inexistente, ciclo A->B->A, hook sin fichero, indice de memoria roto, description > 1.200, agente sin `name`,
`.MANUAL-COPY` desincronizada) con stdout byte a byte y **mismo orden**; `parse_frontmatter` con 25.014 frontmatters
(20.000 aleatorios + 2.809 pares + 2.197 tripletas + bordes CRLF/BOM/sin cerrar) -> 0 diffs. Anidamiento por fichero
nunca sube (6->6, 6->5, 6->4, 6->5); 65 funciones nuevas, la mayor 36 lineas; ningun simbolo publico desaparece
(`_toks_inline` era anidada; hoy `_gen_toks_inline`, sin referencias externas).

| # | Grado | Gap | Tarea | Correccion | Evidencia |
|---|---|---|---|---|---|
| A-1 | Minor | Las cuatro tareas de Fase 2 sin `- **Tipo**:` — repeticion del A-7 de R1; sin el, `task-brief.py` no enruta persona ni memoria por tipo | T-05..T-08 | **Corregido** (orquestador): `- **Tipo**: refactor` en las cuatro | `task-brief.py <carpeta> T-06` -> «tarea con Tipo `refactor`» (enruta; sin persona de dominio para `refactor`, como en T-03) |
| A-2 | Minor | El CA de T-08 y su «Desviacion declarada» mezclaban coordenadas post-diff (`:674`) con rangos pre-diff de los centinelas (569-655): «674 dentro de 569-655» es falso tal como estaba escrito; T-09 arrancaria del rango equivocado | T-08 | **Corregido** (orquestador): rangos del arbol (109-305, 617-637, 640-726) con los de HEAD entre parentesis | `grep -n -- '--8<--' scripts/lint_plugin.py` -> 109/305, 617/637, 640/726 |
| A-3 | Minor | Comentario de `estado:` del frontmatter parado en «R1 implementada, en revision» con la Fase 2 ya `completado` | ledger | **Corregido** (orquestador) | `tasks.md:3` |

**Observaciones de la Lente B que NO son gaps de comportamiento** (se anotan para T-19/T-22 y la retro):
- 7 de los 65 helpers nuevos son **desplazamiento cosmetico** (una sola llamada y cero ramificacion): `knowledge-find.py`
  `_construir_parser`, `_relaciones_iniciativa`, `_entradas_enrutado`; `build_dashboard.py` `_scan_rec_base`,
  `_render_html_card`, `_scan_rutas`, `_scan_leer_eval`. Cumplen la cifra sin bajar complejidad; coherente con que
  `knowledge-find.py` sea el unico cuyo anidamiento maximo no baja (6 -> 6). Los otros 23 helpers con anidamiento 1 si
  aplanan guardas reales (p. ej. `_fm_yaml_linea` quita 7 niveles al triple bucle de `lint_frontmatter_yaml`).
- 1 de las 19 «reducciones» de `lint_plugin.py` es **artefacto de medicion**: `dfs` figuraba con 36 lineas y su cuerpo es
  byte a byte el mismo (10 lineas por AST); `code-health.py` mide «hasta el siguiente `def`». La cifra real del tramo
  es 28 -> 9 con 18 reducciones genuinas.
- `doctor.py` `_calibracion_leer` devuelve el string `"error"` en el hueco de una `datetime.date` (centinela en banda);
  seguro hoy (`date.__eq__(str)` es `False`), fragil manana. Candidato a T-19.

**Restos de R1 vistos de reojo por la Lente A y corregidos aqui por el orquestador**: T-01 llevaba el placeholder
`0,XXh fix1` sin rellenar (el JSON de `T-01-fix1` mas abajo dice `horas_ia: 0.0`); y en T-01 y T-04 el `(estimado; …)`
con texto dentro del parentesis no casa con el patron `\(estimado\)` de `ledger-lint`, asi que `progress-report`
los sumaba como **medidos** (publicaba «IA real 1h 43m» frente a las 2,04h de la tabla). Reescritos como `(estimado)`
seguido del motivo entre parentesis aparte.

**Balance del tramo R2**: 1 intento · 3 Minor, ninguno de codigo, todos corregidos · **primera revision del refactor
con dos lentes vivas** (en R1 cayeron por la API en los intentos 2 y 3). Lo que las lentes aportaron y la
verificacion del orquestador no habria visto: los 7 helpers cosmeticos, el falso positivo de `dfs` en la cifra de
mejora, el centinela en banda de `_calibracion_leer`, la repeticion del A-7 y los restos de medicion de R1.

**Commits del tramo** (los hace el orquestador, uno por tarea; CA-09 se cumple por commit: ninguno toca `agents/`,
`commands/` ni ningun `SKILL.md`): ver `git log` de `feature/plugin-refactor` tras esta seccion.

## Revision de dos lentes - intento 1 (tramo R3: T-09..T-10): 6 Important, 7 Minor (lentes A+B)

> Coordenadas `fichero:linea` de esta tabla: las del arbol **en el momento del intento 1** (antes de la correccion). Tras el intento 2 varias se desplazaron (`_respaldo_declarado` a `lint_plugin.py:850-865`, `maxsplit=1` a `:873`, igualdad de centinela a `:908`, NFKD a `:875`; `copias.json` tiene 124 lineas y el bloque `docstring_uso_exit` esta en `:110-121`). Se conservan como registro historico (N-1 del intento 2).

Dos lentes de contexto fresco (agente `reviewer`, opus) en paralelo sobre `git diff HEAD` (14 modificados + 2 nuevos),
marcador medido desde la sesion principal (`plugin-refactor/revision-R3-intento1`):
`{"eur":7.55,"horas_ia":1.01,"duracion":"1h 1m","duracion_reloj":"18m","tokens_reales":{"entrada":275,"salida":108834,"cache_creacion":374375,"cache_lectura":6296784,"respuestas":74},"fuente":"medido"}`.

**Lo que esta bien y queda verificado** (no se repite en el intento 2): 0 lineas ejecutables tocadas en los 7 scripts con
bloques (todo lo anadido empieza por `#`); `lint_plugin.py --root .` stdout identico a HEAD, stderr 0 bytes, exit 0;
el test de identidad muerde en los 7 bloques comparables (14 mutantes de un byte, siempre el `[id]` correcto) y el
canonico de `REVISION_HDR_PATTERN` y de `piezas()` esta entre las copias; el registro no puede mentir en 11 mutaciones
(inicio inexistente, fin antes de inicio, ruta inexistente, copia unica, sustitucion muerta, id repetido: todas rojas);
normalizacion CRLF total / LF total / mixto / BOM: verde, espacio final: rojo (correcto); menciones de `--8<--` dentro
de cadenas no disparan (la regex ancla `^[ \t]*#`); tolerancias `interop/ .venv/ node_modules/ dist/ .git/ __pycache__/`;
orden de errores determinista por ruta; registro ausente = falla en alto (28 errores), correcto; suite por conjunto: +13
de `test_copias_declaradas`, 4 ids de `test_cifras_medidas` renombrados por linea (T-19), 40 rojos preexistentes iguales;
`release.py --dry-run` exit 0; finales de linea mixtos sin consecuencia (unico par mixto comparado, `evals/check.py` LF
frente a `lint_plugin.py` CRLF, normalizado). Desviaciones declaradas 1, 4, 5 y 6: **legitimas** (verificadas por la
Lente A); la 2, legitima en el mecanismo y **falsa en su justificacion** (gap 1); la 3, legitima pero fuera de la
doctrina escrita (gap 4).

| # | Grado | Gap | Tarea | Correccion | Evidencia |
|---|---|---|---|---|---|
| 1 (A-1 = B-2) | **Important** | `glob_to_regex` queda **sin guardarrail sobre el canonico** y el registro afirma lo contrario: `motivo_canonico` dice que «la equivalencia con el canonico la cubren los tests de comportamiento de cada script», pero `scope-check.py` y `review-lens-select.py` cargan **siempre** el canonico por `importlib` cuando `confluence-publish` existe (siempre en el repo), asi que los respaldos son codigo que ningun test ejecuta. Mutante semantico identico en los DOS respaldos (`(?:.*/)?` a `.*/`): **0 rojos nuevos**; el mismo en el canonico: 3 rojos. `ADR-016` promete «C pasa a tener guardarrail» | T-09 | **Corregido** - el bloque sigue `canonico_comparable: false`, pero anade `equivalencia` (funcion `glob_to_regex`, cargador `_load_glob_to_regex`, corpus de 32 globs con `**/`, `**/x`, `a/**`, `?`, `[a-z]`, `*.md`, `docs/**/*.py`, vacio, con espacios, con barra invertida, con `.`/`+`/`(`, `**` a secas y `/` inicial y final) y `test_el_respaldo_es_equivalente_al_canonico` la ejecuta: carga canonico y CADA respaldo como modulos sueltos (`spec_from_file_location`), fuerza la rama local (`os.path.isfile` -> False) y afirma el `__qualname__` para dejar por escrito que ejecuta la `def local` DEL BLOQUE, no la que devuelve el cargador; compara el `.pattern` compilado. `motivo_canonico` reescrito (identidad entre respaldos + equivalencia conductual con el canonico sobre el corpus declarado) y «Desviacion declarada 2» reescrita | `agent-kits/shared/copias.json:60-61` · `scope-check.py:50-58` · sondas de la Lente B · mutante `(?:.*/)?` -> `.*/` en los DOS respaldos: `FAILED ...[glob_to_regex]`, «para el glob `'**/'`: canonico -> `'^(?:.*/)?$'`, respaldo -> `'^.*/$'`» (antes: 0 rojos); el mismo mutante SOLO en el canonico: rojo tambien, al reves; revertidos -> `15 passed` |
| 2 (A-2) | **Important** | Entrada `docstring_uso_exit` con **lineas equivocadas** y `que_es` que no describe lo que hay: `code-health.py:27-40` es hoy la cola del docstring (`Exit:` + parrafo `--exclude-path` que anadio T-02 en esta rama) + 8 imports; el bloque se desplazo a 32-45. Ningun test lo detecta: el de `no_codigo` solo comprueba `0 < desde <= hasta <= n` | T-09 | **Corregido** - rangos reales del arbol (`code-health.py` **23-27** = de `Uso:` a `Exit:`; `deps-inventory.py` **27-28**) y `que_es` fiel (dice que el texto NO coincide y que los tamanos son distintos: en `code-health.py` el `Uso:` ocupa cuatro lineas y en `deps-inventory.py` una). Los DOS bloques `no_codigo` declaran `contiene` (`Uso:`+`Exit:` · comillas triples+`import os`+`import sys`) y `test_los_bloques_no_codigo_estan_declarados_pero_no_se_comparan` lo afirma dentro del rango de cada copia | `copias.json:126-131` · `code-health.py:27-40` vs `deps-inventory.py:29-40` · con el rango viejo (`27-40`): `AssertionError: docstring_uso_exit / code-health.py: el rango 27-40 ya no contiene 'Uso:' (el bloque se ha desplazado: corrige el rango en copias.json)`; con el corregido, verde |
| 3 (A-3) | **Important** | Fila de `copias.json` en `agent-kits/shared/README.md` escrita con los bytes CR y LF **literales** en vez del texto `\r\n`: la fila queda partida en 3 lineas fisicas y **corta la tabla** Markdown (las 3 filas siguientes se renderizan como texto). Subtarea marcada `[x]` | T-09 | **Corregido** - la fila es UNA linea fisica; los saltos van escapados como TEXTO (barra+r, barra+n) y el terminador es CRLF como el resto del fichero | `agent-kits/shared/README.md:29-31` · `README.md`: 44 CRLF · 44 LF · 44 CR (cero saltos sueltos; antes 46 LF frente a 44 CR) · `git diff --stat` = **1 insercion** (una fila = una linea): la tabla vuelve a cerrar |
| 4 (A-4) | **Important** | `ADR-016` no recoge las dos tolerancias que introduce la implementacion: `sustituciones` (renombrado de identificador antes de comparar, 2 de 7 bloques) y `canonico_comparable: false` (1 de 7); el ADR dice «byte a byte… no texto equivalente» y «C pasa a tener guardarrail». Promoverlo a `aceptada` tal cual deja doctrina contradictoria con el registro | T-09/T-10 | **Corregido** (orquestador): `ADR-016` enmendado con la seccion «Tolerancias explicitas del comparador» (`sustituciones` + test de uso, `canonico_comparable: false` + `equivalencia` conductual, `respaldos` con test de entrada muerta, centinelas como linea entera, limite del `str.replace`); sigue `propuesta` hasta cerrar el tramo | `docs/knowledge/adr/ADR-016-…md:39,43-45` vs `copias.json:4,60` |
| 5 (B-1) | **Important** | `respaldos` es una lista blanca **sin test de entrada muerta** y silencia al linter para TODAS las rutas del bloque, no solo la que define la constante. Escenario: `"_INVENTADO_FALLBACK"` anadido a `respaldos` de `revision_hdr_pattern` y luego un `_INVENTADO_FALLBACK = 1` real y nuevo en `task-brief.py`: `13 passed`, linter exit 0 — «una copia nueva nace sin guardarrail», lo que T-10 dice cerrar | T-09/T-10 | **Corregido** - dos mitades. Test: `test_cada_respaldo_declarado_esta_definido_en_su_bloque` exige `^NOMBRE =` dentro del rango de alguna copia del bloque, con el rango extendido hacia atras sobre las continuaciones de sentencia (barra invertida al final de la linea anterior), que es donde vive `_REVISION_HDR_FALLBACK =`. Linter: `_respaldo_declarado` tolera la constante solo si una copia **de ese fichero** la lista en `respaldos` **y** la definicion cae dentro del rango de ESA copia - no en todas las rutas del bloque | `copias.json:47` · `lint_plugin.py:817,860` · `tests/test_copias_declaradas.py:94-99` · escenario de la lente B sobre el arbol (`_INVENTADO_FALLBACK` en `respaldos` + `_INVENTADO_FALLBACK = 1` en `task-brief.py`): `1 failed, 14 passed` («NO esta definido dentro del rango de ninguna copia») **y** `task-brief.py:972: constante de respaldo _INVENTADO_FALLBACK SIN fila` · `9 agentes · 1 errores`; revertido -> `15 passed` y `0 errores`. Caso sintetico 40 en `test_lint_plugin.py` |
| 6 (A-5 = B-3) | **Important** | `re.split(..., 1)` con `maxsplit` posicional en la **ruta de error** del guardarrail nuevo (`_id_sugerido`): `DeprecationWarning` en 3.13 y, con `-W error::DeprecationWarning` (lo que hara el interprete al retirarlo), traceback sin la linea que dice QUE copia falta ni resumen. Ningun test ejercita la ruta con warnings activos; arbol limpio: stderr 0 bytes | T-10 | **Corregido** - `maxsplit=1` + caso 42 en `tests/test_lint_plugin.py`, que corre la ruta de error con `python -W error::DeprecationWarning` y afirma stderr vacio, exit 1, el mensaje con `fichero:linea` e `id sugerido` y la linea de resumen | `scripts/lint_plugin.py:823` · antes (posicional), bajo `-W error::DeprecationWarning`: **stdout 0 bytes, stderr 1.349 bytes** (traceback `DeprecationWarning: 'maxsplit' is passed as positional argument`), sin mensaje ni resumen. Despues: **stderr 0 bytes**, exit 1, `usage-meter.py:629: ... (id sugerido prueba)` + `9 agentes · 1 errores · 3 avisos` |
| 7 (B-4) | Minor | Casado del centinela por **prefijo** sin frontera (`marca.startswith(d)`): un bloque nuevo cuyo centinela extienda a uno declarado del mismo fichero es invisible (`criterio de consola COMPARTIDO v2 (bloque NUEVO)` en `test_console_encoding.py`: exit 0). Los 16 `inicio` del registro son prefijos, ninguno linea entera | T-10 | **Corregido** - los 16 `inicio` y los 13 `fin` del registro pasan a ser la LINEA ENTERA del centinela (tras `strip`); el linter casa por igualdad (`marca not in declarados`) y `_limites`/`_bloque` del test localizan la copia por igualdad de linea `strip`eada. El texto comparado no cambia (el bloque sigue empezando en el `#`), asi que los 7 bloques de identidad siguen verdes | `scripts/lint_plugin.py:853` · fixture del caso 41 con el linter anterior (`startswith`): **exit 0 · 0 errores**; con el actual: **exit 1**, `pieza.py:4 ... (id sugerido criterio_compartido_v2)`. Sobre el arbol, el mismo `v2` en `test_console_encoding.py`: `9 agentes · 1 errores`; revertido -> `0 errores` |
| 8 (B-5) | Minor | `_id_sugerido` borra las letras no ASCII en vez de transliterarlas: `criterio del índice` sugiere `criterio_del_ndice_de_knowledge` | T-10 | **Corregido** - `unicodedata.normalize("NFKD", ...)` y fuera los combinantes antes del `re.sub`; el caso 43 lo fija | `scripts/lint_plugin.py:825` · `_id_sugerido('--8<-- criterio del índice de knowledge COMPARTIDO')` -> `criterio_del_indice_de_knowledge_compartido` (antes `criterio_del_ndice_...`) |
| 9 (B-6) | Minor | El docstring de `comprobar_copias_declaradas` dice que una mencion «dentro de una cadena o de un docstring no cuenta»; para un docstring con `# --8<--` en columna 0 **si dispara**. `detecta` de `copias.json` es exacto (solo habla del regex) | T-10 | **Corregido** - el docstring dice ahora lo que hace el codigo: solo las menciones dentro de una CADENA quedan fuera (`ini = src.index(...)` no dispara); una linea que empieza por `#` cuenta este donde este, docstrings incluidos, porque el ancla es la forma de la linea y no su contexto sintactico | `scripts/lint_plugin.py:831-832` vs `:775` · `scripts/lint_plugin.py:882-885` |
| 10 (B-7) | Minor | `COPIAS_SKIP_DIRS` no excluye `.claude/`, `.codex/`, `.opencode/`, `.agents/` (instalacion por copia directa, `docs/INSTALL.md`): con el plugin copiado en `.claude/`, `9 agentes · 4 errores` | T-10 | **Corregido** - `COPIAS_SKIP_DIRS` suma `.claude`, `.codex`, `.opencode`, `.agents` (instalacion por copia directa, `docs/INSTALL.md`), con el motivo escrito al lado; `detecta` de `copias.json` las nombra | `scripts/lint_plugin.py:774` · con `scripts/lint_plugin.py`, `task-brief.py` y `ledger-lint.py` copiados bajo `.claude/`: antes **`9 agentes · 11 errores`**, despues **`9 agentes · 0 errores · 3 avisos`** |
| 11 (B-8) | Minor | `test_las_sustituciones_declaradas_se_usan_de_verdad` busca el `de` en TODO el fichero, no en el bloque: `["import os","import os"]` en `sin_vallas` pasa | T-09 | **Corregido** - busca en `_bloque(..., sustituir=False)` (el rango declarado), no en todo el fichero | `tests/test_copias_declaradas.py:99` · con `["import os", "import os"]` anadida a las `sustituciones` de `sin_vallas`: `AssertionError: sin_vallas / changelog-sync.py: sustitucion import os -> import os sin uso DENTRO del bloque` (antes pasaba) |
| 12 (A-6) | Minor | Spec CA-04 («ningun test existente se modifica») se incumple: T-10 modifica `tests/test_lint_plugin.py` (+57, puramente aditivo, sancionado por `improvement-plan.md:257`) y el ledger no lo declara entre las 6 desviaciones | T-10 | **Corregido** - bloque «Desviacion declarada 7» en T-10 | `tests/test_lint_plugin.py:46-99,679-681` · `spec.md:158` · ver T-10, «Desviacion declarada 7» |
| 13 (A-7) | Minor | Dos criterios de T-10 **reescritos en su sitio** sin bloque de desviacion: «id esperado» a «id sugerido» y «regla `find` de raices» a `os.path.join(root, …)`. La sustancia se cumple; la forma es la que R1 marco como error (A-1) | T-10 | **Corregido** - restaurado el texto literal de los dos criterios de T-10 desde `git show HEAD:.../tasks.md` («el `id` esperado» y «por la misma regla `find` de raices que el resto del linter (no ruta absoluta)») y anadidas debajo las desviaciones numeradas 8 y 9 | `tasks.md` criterios de T-10 vs `git show HEAD:…/tasks.md` · ver T-10, criterios 1 y 2 + «Desviacion declarada 8» y «9» |

**Sin segunda opinion de contexto fresco** (dicho, no escondido): ninguna — las dos lentes vivieron. **Fuera de lente,
para el orquestador**: `Changelog` de T-01 (207) y T-04 (350) pasan de 200 (tramo R1), se acortan al cerrar R3;
`agent-kits/shared/__pycache__/_doctor_head.cpython-313.pyc` huerfano, no versionado. **Restriccion del comparador**
(Lente A): `sustituciones` es un `str.replace` global sobre el bloque; si un identificador declarado fuera subcadena de
otro enmascararia divergencia — hoy no ocurre; se escribe en `ADR-016` como limite conocido.

## Revision de dos lentes - intento 2 (tramo R3): 1 Important, 9 Minor — los 13 gaps del intento 1 cerrados

Lentes A+B vivas, marcador `plugin-refactor/revision-R3-intento2`:
`{"eur":12.05,"horas_ia":1.63,"duracion_reloj":"44m","tokens_reales":{"entrada":303,"salida":129150,"cache_creacion":653081,"cache_lectura":11573108,"respuestas":119},"fuente":"medido"}`.

**Cerrado y re-verificado con mutantes** (Lente A los 13, Lente B ~35 mutantes en arboles desechables): la equivalencia
ejecuta la `def` del bloque del respaldo (aserta `__qualname__`), no la del cargador; mutante en los dos respaldos,
solo en el canonico y en un solo respaldo: rojos con el `[id]`; rangos `no_codigo` con `contiene` (6 mutaciones rojas);
`respaldos` con test de entrada muerta y linter que muerde la constante nueva; `maxsplit=1` y ruta de error limpia bajo
`-W error::DeprecationWarning` + cp1252 (dos ejecuciones byte-identicas); centinelas como linea entera (16 `inicio` +
13 `fin` casan por igualdad; `v2` extendido da error); NFKD en `_id_sugerido`; `.claude/.codex/.opencode/.agents`
tolerados; sustituciones acotadas al bloque; 16/16 mutantes de un byte rojos; `lint_plugin --root .` stdout identico a
HEAD, stderr 0 B; suite: 0 regresiones, 0 desaparecidos, +15. `ADR-016` enmendado (gap 4) sin contradiccion interna.
Limites declarados y verificados (no gaps): comparacion por `.pattern` yerra por el lado seguro; `contiene` es ancla
minima (rango ensanchado sigue verde); el linter solo recorre `.py`.

| # | Grado | Gap | Tarea | Correccion | Evidencia |
|---|---|---|---|---|---|
| B-1 | **Important** | El `corpus` de `equivalencia` **no esta fijado**: el esquema solo exige `>= 25` y hay 32; borrar las 3 entradas que discriminan un mutante (`"?"`, `"a?c"`, `"?*?"` para `[^/]` a `[^/]?`) deja 29 y el mutante vivo con `15 passed`. Es el unico guardarrail del canonico: podarlo lo desactiva sin nada rojo (misma clase que el gap 5 del intento 1) | T-09 | **Corregido** (intento 3): el `>= 25` desaparece del esquema; `equivalencia.categorias` declara **18 categorias obligatorias** `{nombre, regex}` y `test_el_corpus_de_equivalencia_cubre_todas_las_categorias` exige >= 1 entrada por categoria (`re.search`). Corpus 32 -> 35 (`"./docs/x.md"` de B-5, `"[!a-z]"`, `"[^a-z]"`) | Escenario de la Lente B (arbol desechable): borrar `"?"`, `"a?c"`, `"?*?"` -> `1 failed`: «el corpus (32 entradas) ya no cubre 1 categoria(s)… interrogante `?` (ninguna entrada casa `\?`)». Con el corpus integro, el mutante `[^/]` -> `[^/]?` en los DOS respaldos sigue rojo (`para el glob '?': canonico -> '^[^/]$', respaldo -> '^[^/]?$'`). Salidas abajo, T-09 |
| B-2 | Minor | `sustituciones` acepta **pares de subcadena arbitrarios**: `["strip()) > len(cerco)", "strip()) >= len(cerco)"]` revierte una divergencia real de comportamiento antes de comparar (`15 passed`). El registro y `ADR-016` hablan de «renombrados de identificador» | T-09 | **Corregido** (intento 3): el esquema exige que cada `sustitucion` sea un par y que **ambos lados** casen `^[A-Za-z_][A-Za-z0-9_]*$`; `_bloque` aplica `re.sub(r"\b" + re.escape(de) + r"\b", a, txt)` en vez de `str.replace`. `copias.json` `comparacion` lo dice igual | Inyectado el par `["strip()) > len(cerco)", "strip()) >= len(cerco)"]` en `sin_vallas` -> `2 failed`: «la sustitucion […] no es un renombrado de identificador: `strip()) > len(cerco)` no casa `^[A-Za-z_][A-Za-z0-9_]*$`». Los dos pares reales (`_frontmatter_plegado`, `RE_VALLA`) siguen verdes: `17 passed` en el arbol limpio |
| B-3 | Minor | La tolerancia de `respaldos` **no esta acotada a la ruta que define la constante** como afirman docstring, `copias.json:6` y `ADR-016`: es de bloque y se replica a las 3 rutas, acotada solo por rango. Renombrar el canonico `REVISION_HDR_PATTERN` a `_REVISION_HDR_FALLBACK` en `ledger-lint.py` (dentro del rango de esa copia) pasa | T-10 | **Corregido** (intento 3): `respaldos` es **por copia** (`copias[i].respaldos`); `_copias_registradas` lo lee de la copia, no del bloque; en `copias.json` el nombre `_REVISION_HDR_FALLBACK` vive ahora en las copias de `task-brief.py` y `jira-flow.py`, NO en la de `ledger-lint.py` (canonico). Docstrings de `_copias_registradas`/`_respaldo_declarado` y `copias.json` `detecta` reescritos; el test pasa a `test_cada_respaldo_declarado_esta_definido_en_su_copia` y ademas prohibe `respaldos` a nivel de bloque (seria entrada muerta) | Escenario: `REVISION_HDR_PATTERN` -> `_REVISION_HDR_FALLBACK` en `ledger-lint.py:186` (dentro del rango de SU copia) -> `❌ agent-kits/shared/ledger-lint.py:186: constante de respaldo `_REVISION_HDR_FALLBACK` SIN fila…` · `1 errores`. Caso 44 de `tests/test_lint_plugin.py` lo fija con fixture sintetica |
| B-4 | Minor | Una **segunda copia del mismo bloque en un fichero ya declarado** es invisible: el test toma la primera linea igual al `inicio` y el linter solo comprueba pertenencia, no cuenta ocurrencias. Copia divergida pegada al final de `scope-check.py`: `15 passed`, `0 errores` | T-09/T-10 | **Corregido** (intento 3): `test_cada_centinela_declarado_aparece_exactamente_una_vez_en_su_ruta` cuenta las lineas iguales (tras `strip`) a cada `inicio`/`fin` y exige **1**; el linter acumula los centinelas CON repeticion y da error cuando las apariciones superan las declaradas para esa ruta, con el `fichero:linea` de la SOBRANTE | Escenario: segunda copia divergida del bloque `glob_to_regex` pegada al final de `scope-check.py` -> test `1 failed` («el centinela `inicio` … aparece 2 veces (se espera 1)») y linter `❌ …scope-check.py:264` + `❌ …:284` · `2 errores`. Caso 45 de `tests/test_lint_plugin.py` |
| B-5 | Minor | Hueco de corpus: `./` inicial no lo discrimina ninguna entrada (normalizar `./` en una implementacion y no en la otra pasa) | T-09 | **Corregido** (intento 3): `"./docs/x.md"` en el corpus y categoria obligatoria «`./` inicial (ruta relativa sin normalizar)» (`^\./`) en `equivalencia.categorias`, para que la entrada no se pueda podar | `python -c "…"` sobre `copias.json`: `categorias sin entrada: []` · `corpus 35 categorias 18`; la categoria `^\./` la cubre solo esa entrada |
| N-1 | Minor | La columna «Evidencia» de la tabla del intento 1 cita coordenadas del arbol **de antes de la correccion** (8 de 13 filas ya no resuelven; `copias.json:126-131` apunta fuera de un fichero de 124 lineas) sin decirlo | traza | **Corregido** (orquestador): nota bajo el titulo de la seccion del intento 1 | `tasks.md`, seccion intento 1 |
| N-2 | Minor | El tercer criterio de T-10 seguia reescrito en su sitio (el gap 13 restauro solo dos) | T-10 | **Corregido** (orquestador): literal de HEAD + puntero a la desviacion 5 | `tasks.md` CA3 de T-10 |
| N-3 | Minor | Fila Fase 3 de la tabla de progreso: supervision 0,62 frente a 0,37 + 0,24 = 0,61; TOTAL 1,14 frente a 1,13 | ledger | **Corregido** (orquestador) | `tasks.md` tabla de progreso |
| N-4 | Minor | `progress-report.py active` publica «IA real 3h 8m» frente a 4,48h del ledger: `_parse_horas` de `ledger-lint.py:371` se queda con el **primer** `real <n>h` y no ve los tramos `+ 0,41h fix1`. Limitacion **preexistente** (T-01..T-04 ya la tenian), fuera de R3 | T-17/T-19 | anotado, no se corrige aqui: el parser de horas debe sumar los tramos `+ N,NNh` del mismo campo; candidata a T-17 (metricas) o T-19 | `agent-kits/shared/ledger-lint.py:371` |
| N-5 | Minor | La enmienda de tolerancias llego a `ADR-016` pero `design.md:218` sigue descartando «texto equivalente» sin remitir a ella | T-09 | **Corregido** (orquestador): nota de enmienda en la fila «Como se compara» de `design.md` §4 apuntando a `ADR-016` «Tolerancias explicitas del comparador» (fichero del `architect`; se toca solo la remision, no la decision) | `design.md:218` |

**Fuera de lente, anotado para T-19**: `lint_plugin.py:911` trunca el centinela a 70 caracteres en el mensaje (dos
centinelas largos que difieran despues del 70 son indistinguibles); `_id_sugerido` puede sugerir un `id` que ya existe.
**Entorno**: `python tests/test_lint_plugin.py` aborta en Windows en el caso preexistente de `chmod` (identico en HEAD);
los casos nuevos se verificaron llamando a `casos_copias_declaradas()` y `casos_copias_registro_fino()` directamente.
**Sin segunda opinion de contexto fresco**: ninguna, las dos lentes vivieron. Bucle: intento 3 = ultimo.

## Revision de dos lentes - intento 3 (tramo R3, ULTIMO del bucle): B-1..B-5 cerrados; residual 1 Important + 4 Minor

Verificacion determinista del orquestador (arbol desechable, 5 escenarios de la Lente B del intento 2: poda del corpus
-> rojo nombrando la categoria; par arbitrario en `sustituciones` -> 2 rojos del esquema; renombrado del canonico en
`ledger-lint.py` -> error del linter; segunda copia de `glob_to_regex` en `scope-check.py` -> test rojo + 2 errores
senalando la sobrante; `./docs/x.md` y categoria `^\./` presentes; `respaldos` solo por copia; `lint_plugin --root .`
stdout identico a HEAD con indice git en la copia, stderr 0 B) + **una lente fresca (B) sobre el delta del intento 3**,
marcador `plugin-refactor/revision-R3-intento3`:
`{"eur":5.83,"horas_ia":0.66,"duracion_reloj":"34m","tokens_reales":{"entrada":259,"salida":68245,"cache_creacion":249692,"cache_lectura":6143678,"respuestas":53},"fuente":"medido"}`.
Lente A no despachada en este intento (la conformidad ledger/docs se reviso en los intentos 1 y 2 y el delta es solo
codigo de guardarrail): **sin segunda opinion de conformidad sobre el delta**, dicho.

**Cerrado y verificado por la lente**: 18/18 mutantes de poda por categoria rojos y nombrando la categoria; el corpus
minimo que las categorias admiten (13 entradas) sigue matando 7 mutantes semanticos; `\b` en sustituciones respeta
`RE_VALLA_X`; `respaldos` por copia rechaza nivel de bloque, copia que no define y definicion fuera de rango (linter +
test); centinela duplicado senala la sobrante; mensajes nuevos bajo cp1252 + `-W error`: exit 1, stderr 0 B, md5
estable en 3 pasadas; suite en el repo real `PASSED=1444 FAILED=40 SKIPPED=1`, conjunto FAILED identico al del
intento 2, ningun test perdido; aritmetica del JSON de `R3-fix2` coherente con su ventana.

| # | Grado | Gap | Tarea | Correccion | Evidencia |
|---|---|---|---|---|---|
| R3-1 | **Important** | El candado de B-1 se movio del `corpus` a `equivalencia.categorias`, pero **la lista de categorias no la fija nadie**: el test itera la propia lista del registro. Quitar una categoria del registro y sus entradas del corpus (17 categorias / 32 entradas) deja verde el test de cobertura y el mutante `[^/]` -> `[^/]?` en los dos respaldos **sobrevive** (`62 passed`, linter `0 errores`). Mismo agujero de B-1 un nivel mas arriba | T-09 | **Corregido (4.ª pasada autorizada por el usuario)**: `CATEGORIAS_OBLIGATORIAS` en `tests/test_copias_declaradas.py` fija los **18 nombres** copiados literal del registro y `test_las_categorias_obligatorias_siguen_declaradas_en_el_registro` exige que cada uno siga declarado; anadir categorias al registro es libre, quitar una es rojo NOMBRANDOLA | Escenario de la lente (quitar del registro la categoria del `?` **y** las 3 entradas `"?"`, `"a?c"`, `"?*?"` del corpus): **exit 1**, `AssertionError: glob_to_regex: copias.json ya no declara 1 categoria(s) OBLIGATORIA(S) ...: `interrogante `?` (un caracter, sin cruzar `/`)``, `1 failed, 17 passed`; restaurado -> `18 passed`. Con el registro INTEGRO, el mutante `out.append("[^/]")` -> `out.append("[^/]?")` en los DOS respaldos sigue rojo: `FAILED ...::test_el_respaldo_es_equivalente_al_canonico[glob_to_regex]`, «para el glob `'?'`: canonico -> `'^[^/]$'`, respaldo -> `'^[^/]?$'`» · `tests/test_copias_declaradas.py:116-146,262-284` |
| R3-2 | Minor | Residual de B-2: las `sustituciones` no se validan como **inyectivas** ni sin encadenar: dos pares con el mismo destino (`_frontmatter_plegado`/`_frontmatter_rapido` -> `_frontmatter`) o `a->b`,`b->c` colapsan identificadores distintos y borran una divergencia real (`17 passed`, linter 0) | T-09 | **Corregido (4.ª pasada autorizada por el usuario)**: `test_el_registro_tiene_la_forma_que_dice_su_esquema` exige, **por copia**, destinos distintos entre si (sin COLAPSO) y ningun destino que sea tambien origen (sin ENCADENADO, que ademas haria depender el resultado del ORDEN de la lista) | `[["_frontmatter_plegado","_frontmatter"],["_frontmatter_rapido","_frontmatter"]]` -> **exit 1**, «dos `sustituciones` apuntan al MISMO destino (['_frontmatter', '_frontmatter'])»; `[["a","b"],["b","c"]]` -> **exit 1**, «['b'] es a la vez ORIGEN y DESTINO»; con los pares REALES del registro, `1 passed` · `tests/test_copias_declaradas.py:198-221` |
| R3-3 | Minor | La heuristica por nombre `_*_FALLBACK` no ve la definicion **anotada** (`_X_FALLBACK: str = …`) ni la **encadenada** (`_A_FALLBACK = _B_FALLBACK = …`, solo el primer nombre) | T-10 | **Corregido (4.ª pasada autorizada por el usuario)**: `_RESPALDO_DEF_RE` captura el LADO IZQUIERDO entero de la asignacion y `_nombres_de_respaldo()` extrae de ahi **todos** los `_*_FALLBACK` — simple, anotada y encadenada, un error por nombre —; una mencion en el VALOR (`x = _PATRON_FALLBACK`) sigue sin contar. Las dos formas quedan escritas en `detecta` de `copias.json` | Caso **46** nuevo (`casos_copias_forma_de_definicion()` en `tests/test_lint_plugin.py`): con `_NUEVO_FALLBACK: str = r"^x$"` y `_OTRO_FALLBACK = _TERCERO_FALLBACK = r"^y$"` en un `.py` de fixture -> **exit 1** y **3 errores**, `copia.py:2` con `_NUEVO_FALLBACK` y `copia.py:3` con `_OTRO_FALLBACK` y `_TERCERO_FALLBACK`; `copia.py:4` (el uso) NO aparece; declaradas en el registro -> exit 0. Verde llamando a `casos_copias_forma_de_definicion()` directamente (el runner completo aborta antes, en el caso `chmod`, en Windows) · `scripts/lint_plugin.py:780-800,952-958` · `copias.json` clave `detecta` |
| R3-4 | Minor | El marcador `R3-fix2` se abrio **a posteriori** (`inicio` puesto a mano a `22:50:00Z`, `offsets` a 0; la ventana la acota solo el filtro por timestamp de T-04) y el ledger no lo decia, aunque este mismo ledger declara esa clase de cosa (T-01-fix2) | T-09/T-10 | **Corregido** (orquestador): nota en `Tiempo IA` de T-09 y T-10 | `tasks.md` T-09/T-10 · `.claude/usage-state.json` |
| R3-5 | Minor | La evidencia «suite por conjunto» del intento 3 se midio sobre una recoleccion **23 tests mas corta** (`evals/test_evals.py` no recogido: 21 tests, 2 rojos preexistentes; FAILED 40 -> 38 sin anotarlo); es la unica suite que ejercita `evals/check.py`, que el delta toca | traza | **Corregido** (orquestador): anotado aqui; la lente rehizo la medicion completa en el repo real (`FAILED=40`, conjunto identico al intento 2, `evals/check.py` verde: 12 `test_check_*` + exit 0) | capturas `suite-*-r3i3.txt` |

**Balance del tramo R3**: 3 intentos · 6+1+1 Important y 7+9+4 Minor · revision medida 7,55 + 12,05 + 5,83 = **25,43 EUR**
(+ 3 pasadas de implementer). Lo que las lentes aportaron y la verificacion determinista no habria visto: el guardarrail
del canonico que no existia (gap 1 del intento 1), la lista blanca `respaldos`, el corpus podable y, un nivel arriba, la
lista de categorias podable; el `DeprecationWarning` en la ruta de error; la fila del README rota. **Estado tras la 4.ª pasada (autorizada por el usuario, fuera del bucle acotado)**: R3-1, R3-2 y R3-3 quedan **corregidos y verificados** con los escenarios que la propia lente describió (ver la columna «Evidencia» y los dos bloques «Verificación RE-EJECUTADA tras la 4.ª pasada» de T-09 y T-10); el tramo R3 ya no arrastra gaps de código abiertos, así que `ADR-016` puede pasar a `aceptada` cuando el orquestador cierre el tramo. R3-4 y R3-5 eran de traza y ya estaban corregidos. **Estado al tope del
bucle**: T-09/T-10 quedan `completado` con 1 Important + 2 Minor de codigo **declarados** y sin corregir (R3-1..R3-3); la
decision de una cuarta pasada o de aceptarlos como limite conocido en `ADR-016` es del usuario. `ADR-016` sigue
`propuesta` hasta esa decision. `copias.json` y `tests/test_copias_declaradas.py` siguen **sin trackear**: los anade el
commit de T-09.

## Revision de dos lentes - 4.a pasada (tramo R3, fuera del bucle acotado, autorizada por el usuario el 2026-09-11): R3-1..R3-3 cerrados — TRAMO R3 CERRADO

El bucle acotado (3 intentos) termino con 1 Important + 2 Minor de codigo declarados. El orquestador presento las dos
opciones (cuarta pasada corta o aceptar el residual como limite en `ADR-016`); el usuario eligio la cuarta pasada.
Implementer con marcador **unico y con `start` limpio** `plugin-refactor/R3-fix3` (1,13h IA · 8,66 EUR · 28m de reloj;
`close` ejecutado dos veces para releer el JSON truncado, vale la segunda lectura, anotado en T-09).

**Verificacion determinista del orquestador** (arbol desechable, `git archive HEAD` + diff + los 2 ficheros nuevos):
- R3-1: quitar del registro la categoria `?` y sus 3 entradas -> `FAILED test_las_categorias_obligatorias_siguen_declaradas_en_el_registro[glob_to_regex]` (1 failed, 17 passed); la lista fija de 18 nombres vive en `tests/test_copias_declaradas.py` (`CATEGORIAS_OBLIGATORIAS`).
- R3-2: `[["_frontmatter_plegado","_frontmatter"],["_frontmatter_rapido","_frontmatter"]]` -> 2 failed (esquema + uso); `[["a","b"],["b","c"]]` -> 2 failed (esquema + identidad).
- R3-3: `_NUEVO_FALLBACK: str = …` y `_OTRO_FALLBACK = _TERCERO_FALLBACK = …` -> linter exit 1 con **3 errores**, uno por nombre, y el uso en el valor no cuenta.
- Contrato: `lint_plugin --root .` stdout identico a HEAD (copia con indice git), stderr 0 B, exit 0, `9 agentes · 0 errores · 3 avisos`; base `18 passed`.
- Suite por conjunto con recoleccion **completa** (`evals/test_evals.py` recogido): PASSED 1.444 -> 1.445, FAILED 40 -> 40 mismo conjunto, +1 linea (`test_las_categorias_obligatorias…`); el caso 46 del linter no colecta como linea (suite-script, rojo preexistente de `chmod` en Windows).

**Sin lente de contexto fresco en esta pasada** (dicho, no escondido): el delta son ~140 lineas de tests + una regex; la
verificacion es la reproduccion de los 3 escenarios que la Lente B del intento 3 dejo escritos.

**Balance final del tramo R3**: 3 intentos + 1 pasada autorizada · 8 Important y 20 Minor en total, **todos cerrados**
· revision medida 7,55 + 12,05 + 5,83 = **25,43 EUR** · implementacion + correcciones medidas en T-09/T-10 (4,58h IA, Fase 3).
`ADR-016` pasa a **`aceptada`** con esta traza (T-10, Notas). **Desviacion declarada 11** (scope-check exit 1 por
ficheros ajenos al tramo: `.claude/*`, `CONTINUE-HERE*.md`, `feature-pendiente.bundle`, `design.md` del orquestador):
`design.md` se commitea con el ADR en el cierre; el resto es ruido no versionado ya fichado en R1.

**Commits del tramo** (orquestador, uno por tarea): ver `git log` de `feature/plugin-refactor` tras esta seccion. El de
T-09 incluye `git add` de `agent-kits/shared/copias.json` y `tests/test_copias_declaradas.py`.
