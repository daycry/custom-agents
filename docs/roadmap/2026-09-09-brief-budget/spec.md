---
spec: brief-budget
descripcion: >
  Presupuesto por sección del brief del subagente (`task-brief.py`): el tope global `BRIEF_TOPE_CHARS = 10000`
  (CA-08 de `memory-retrieval`) se rompe por construcción en cuanto la iniciativa tiene `design.md`, porque solo
  una de las siete secciones (`## Memoria técnica`) tiene tope propio. Cinco opciones combinables del análisis
  (O1 topes por sección · O2 diseño bajo demanda · O3 gaps solo de la tarea · O4 verificación sin evidencia ·
  O5 guardarraíl sobre todos los ledgers), sin subir el tope, sin recortar la tarea ni el contrato, sin tocar la
  persona ni la memoria. Fuente única del alcance: `analysis.md` de esta carpeta.
estado: aprobada
creado: 2026-09-09
actualizado: 2026-09-09
evaluacion: evaluation.md
design: n/a
plan: pendiente
analisis: analysis.md
relacionado: docs/knowledge/gotchas/GOT-009-presupuesto-del-brief-se-rompe-con-design-md.md · docs/knowledge/gotchas/GOT-008-tope-ca08-del-brief-depende-de-ruta-y-corpus.md · docs/roadmap/2026-09-09-plugin-refactor/analysis.md (toca el mismo script; hay que ordenarlas)
generacion:            # la spec se escribió en la MISMA ventana que evaluation.md (una sola medición, no se duplica)
  inicio: 2026-09-09T17:56:55Z
  fin: 2026-09-09T18:07:07Z
  fuente: estimado     # `usage-meter.py close` degrada en esta máquina: «carpeta de transcripciones no disponible» (Windows). Parte estimada a juicio de la ventana compartida
  tokens_reales: { entrada: 30000, salida: 9000, cache_creacion: 12000, cache_lectura: 150000 }
  eur: 0.47
  horas_ia: 0.11
  duracion: 10m
  ratio_usado: 479326
---

# El presupuesto del brief, sección a sección

> **Análisis de origen:** [`analysis.md`](analysis.md) — única fuente del alcance; esta spec no lo amplía.
> **Evaluación:** [`evaluation.md`](evaluation.md)
> **Plan de implementación:** pendiente

> **Terminología:** **brief** = salida de `agent-kits/shared/task-brief.py <carpeta> T-XX` (el texto que recibe el subagente
> de una tarea). **Tope** = `BRIEF_TOPE_CHARS = 10000` caracteres (≈ 2.500 tokens; CA-08 de la spec de `memory-retrieval`).
> **Sección** = cada bloque `## …` del brief: siete hoy (cabecera+contexto+contrato · La tarea · Verificación · Memoria
> técnica · Diseño · Gaps pendientes · Persona). **Presupuesto propio** = constante `*_TOPE_CHARS` + recorte alineado
> (`_recorte_seguro`) + aviso por stderr, el patrón que hoy solo tiene la memoria (`task-brief.py:188-205`).

## Contexto y objetivo

Medido el 2026-09-09 sobre el ledger real de `docs/roadmap/2026-09-09-project-specialization/` (22 tareas, único
`design.md` aprobado del repo) con el código de F1 de esa iniciativa ya aplicado: **12 de 22 briefs por encima de 10.000**
con la persona íntegra en su suelo de 1.300 (el mayor, T-01 = 15.624) y **12 avisos por stderr**. Sin persona alguna eran
11/22 (Lente B, intento 2). La composición explica el resultado (`analysis.md` §1): `## Diseño` = **3.510 en las 22 tareas**
(la sección «opción elegida» de `design.md` entra entera vía `_design_elegida`, `task-brief.py:531`), fijo ≈ 1.025, tarea
mediana 2.632 / máx 3.845, verificación mediana 764 / máx 2.285 (T-02, evidencia pegada), memoria mediana 1.194 / máx 2.324
(tope 2.400), gaps hasta **4.396** (T-01, sin tope; `task-brief.py:722-738`). Antes de la primera línea de la tarea ya van
5.729 … 6.935 caracteres: **con `design.md` el presupuesto está roto por construcción**, no por una tarea gorda.

Nadie lo vio (`analysis.md` §2) porque el test que guarda el CA-08
(`test_ca08_el_brief_completo_cabe_en_el_tope_sobre_el_ledger_real_de_memory_retrieval`,
`agent-kits/shared/test_task_brief.py:781`) recorre solo `memory-retrieval`, sin diseño; `GOT-008` diagnosticó el problema
anterior con un remedio que presupone que no hay diseño; y hasta F1 no había aviso en runtime.

**Objetivo:** que el brief cumpla el tope que promete — **0 de 22 briefs de `project-specialization` por encima de 10.000**,
`## Diseño` deja de ser una constante de 3.510, el test del CA-08 recorre todos los ledgers y está en verde, y ningún aviso
de tope en el despacho de F2 (`analysis.md` §6) — **sin** subir el tope, recortar el contrato, ni tocar la persona o la
memoria (`analysis.md` §3).

## Decisiones de diseño

Las decisiones de **qué opciones entran y en qué orden** no se toman aquí (`analysis.md` §4: «para que `evaluator`
presupueste y `planner` elija»). Las que sí fija el análisis, porque son restricciones y no elecciones:

| Decisión | Elección | Motivo |
|---|---|---|
| El tope global | **`BRIEF_TOPE_CHARS = 10000` no se toca** | Requisito CA-08 de `memory-retrieval` (≤ 2.500 tokens: un brief más largo degrada al subagente). Subirlo esconde el problema |
| Dónde vive el presupuesto | **En cada sección variable, no en la forma del comando** | `GOT-008` (descartado, medido: acortar la ruta no ahorra; «el camino es el tope de la sección») |
| Cómo se recorta | **Alineado a línea con `_recorte_seguro`** (`task-brief.py:271`), nunca por carácter a ciegas; `## Diseño`, si se recorta, **por subsecciones enteras** | Maquinaria ya escrita y con tests (no parte fences ni comentarios HTML); `analysis.md` §5 |
| Qué se dice al recortar | **Aviso por stderr con la causa medida**, calcando la memoria y el aviso de F1 (`task-brief.py:818-833`) | El tope no vuelve a afirmarse solo en tests (`analysis.md` §2.3) |
| Qué mide las constantes nuevas | **La máquina de trabajo, con margen**, no un número inventado | El presupuesto es de la máquina, no del repo (`GOT-008`: ruta + corpus mueven ~250 caracteres) |
| El guardarraíl | **Recorre todos los `docs/roadmap/*/tasks.md`**, con y sin `design.md`; hasta que O1-O4 bajen los briefs, `xfail` **con motivo y fecha** (nunca `skip` sin fecha) | Sin él, O1-O4 pueden volver a romperse en silencio; un `skip` sin fecha es «la pieza muerta de siempre» (`analysis.md` §5) |
| Portabilidad del script | **`task-brief.py` sigue siendo standalone** (sin módulo común importado) y conserva el snippet UTF-8 de `GOT-005` | Los scripts del kit viajan sueltos (paquete portable, interop); consola cp1252 en Windows |

## Configuración / parámetros

Verificado contra `agent-kits/shared/task-brief.py` (HEAD, 2026-09-09):

| Parámetro | Clave / mecanismo | Hoy | Valor objetivo |
|---|---|---|---|
| Tope global del brief | `BRIEF_TOPE_CHARS` (`:108`) | `10000` | **`10000` (invariante)** |
| Tope de la memoria | `MEMORIA_TOPE_CHARS` (`:105`) | `2400` | **`2400` (invariante; es el patrón a copiar)** |
| Persona (suelo / cap / mínimo útil) | `PERSONA_SUELO_CHARS` · `PERSONA_TOPE_CHARS` · `PERSONA_TOPE_MINIMO_UTIL` (`:120-133`) | `1300` · `4000` · `200` | **sin cambios** (F1 de `project-specialization`) |
| Tope de `## Diseño` | `DISENO_TOPE_CHARS` (O1) — o inyección bajo demanda (O2) | **no existe** | **medido en la máquina de trabajo, con margen**; a fijar por el planner con la medición del §1 del análisis |
| Tope de `## Gaps pendientes` | `GAPS_TOPE_CHARS` (O1) | **no existe** | ídem |
| Tope de `## Verificación` | `VERIFICACION_TOPE_CHARS` (O1) — o solo comandos, sin evidencia (O4) | **no existe** | ídem |
| Ledgers que recorre el test CA-08 | `test_task_brief.py:781` | `memory-retrieval` (1) | **todos los `docs/roadmap/*/tasks.md`** (32 hoy) |

## Arquitectura y componentes

Toca **un script, su suite y (solo en O2) la estructura del `design.md` del architect**:

- **`agent-kits/shared/task-brief.py`** (840 líneas; `main()` monta las siete secciones en línea, `:640-835`). Se **reutiliza**:
  `_recorte_seguro` (`:271`, recorte alineado que devuelve `(texto, se_recortó)`), `_seccion_plan` (`:621`, extrae `## …` por
  regex respetando fences), `_lineas_con_fence` (`:227`), `_design_elegida` (`:531`, devuelve la sección «opción elegida»),
  `_gaps_pendientes_de_tarea` (`:595`, último intento, filas con columna `Tarea == tid`), `_verificacion_de_tarea` (`:406`,
  ya separa `items` de `ejecutada`) y el patrón completo tope + recorte + aviso de `_memoria_tecnica` (`:158-205`). Lo
  **nuevo**: presupuestos por sección (O1), criterio «la tarea toca el diseño» (O2), acotado de gaps (O3), verificación solo
  con comandos (O4).
- **`agent-kits/shared/test_task_brief.py`** (1.234 líneas, 60 tests). Se reutiliza el fixture `inic`/`tmp_path` y
  `_tareas_del_ledger`. Lo nuevo: un test por tope/criterio y el CA-08 sobre todos los ledgers (O5).
- **`agent-kits/architect/templates/design.md`** §5 «Impacto en módulos y ficheros» (`:97`) — **solo si entra O2**, para que
  el criterio «la tarea referencia módulos del §5» sea parseable de forma determinista y no heurística.
- **No se toca:** `agents/`, `commands/`, hooks, `MEMORIA_TOPE_CHARS`, la cascada de personas, `ledger-lint.py`,
  ningún fichero de `docs/roadmap/2026-09-09-project-specialization/` (ledger con revisión en curso; solo se lee para medir).

## Flujo (paso a paso)

Cómo se compone el brief hoy y dónde entra cada opción:

1. `main()` lee `tasks.md`, extrae el bloque `### T-XX` (`_seccion_tarea`) y monta cabecera + `## Contexto de fase` +
   `## Contrato de retorno` (fijo ≈ 1.025). **Intocable.**
2. `## La tarea`: el bloque sin `Verificación` ni presupuesto (`_chunk_sin_verificacion`, `_chunk_sin_presupuesto`). **Intocable.**
3. `## Gaps pendientes de revisión`: filas del último intento para esta tarea (`:723-738`). → **O3** acota lo que entra;
   **O1** le pone `GAPS_TOPE_CHARS`.
4. `## Verificación`: los `items` del campo, más nota si ya se ejecutó (`:740-752`). → **O4** garantiza que solo entran los
   comandos, nunca la salida pegada; **O1** le pone `VERIFICACION_TOPE_CHARS`.
5. `## Memoria técnica`: `_memoria_tecnica` con `MEMORIA_TOPE_CHARS` y aviso. **Es el patrón; no se toca.**
6. `## Diseño`: `_design_elegida` inyecta la sección «opción elegida» entera si `design.md` está `aprobado`. → **O2** la
   inyecta solo si la tarea referencia módulos del §5 del diseño (si no, un puntero de una línea); **O1** le pone
   `DISENO_TOPE_CHARS` con recorte por subsecciones enteras.
7. `## Persona de dominio`: margen real tras montar el resto, con suelo 1.300 (F1). **No se toca.**
8. Aviso final si `len(texto) > BRIEF_TOPE_CHARS` con la causa por sección (`:818-833`). Se **amplía** con las nuevas
   secciones recortadas, no se sustituye.
9. **O5**: el test del CA-08 recorre todos los ledgers y afirma `≤ 10000` en cada brief; entra en `xfail` fechado hasta que
   O1-O4 bajen los briefs, y pasa a verde al final.

## Alcance

- **Dentro (esta iteración)** — las cinco opciones del `analysis.md` §4, **combinables**; cuáles entran y en qué orden lo
  presupuesta `evaluation.md` y lo elige el planner tras la puerta:
  - **C-01 (O1)** Presupuesto por sección: `DISENO_TOPE_CHARS`, `GAPS_TOPE_CHARS`, `VERIFICACION_TOPE_CHARS`, cada uno con
    `_recorte_seguro` y aviso, calcando `MEMORIA_TOPE_CHARS`; constantes **medidas y justificadas** en comentario.
  - **C-02 (O2)** Diseño bajo demanda: `## Diseño` entra solo si la tarea referencia (campos `Archivos`/`Dependencias`)
    módulos del §5 «Impacto» de `design.md`; si no, un puntero de una línea.
  - **C-03 (O3)** Gaps solo de la tarea: la tabla de revisión entra acotada a lo de la propia tarea (y solo el último intento).
  - **C-04 (O4)** Verificación sin evidencia: el brief lleva los comandos de `Verificación`, nunca la salida pegada en el ledger.
  - **C-05 (O5)** El guardarraíl deja de ser ciego: el test del CA-08 recorre todos los `docs/roadmap/*/tasks.md`.
  - Ampliar el aviso de runtime con las secciones nuevas; actualizar los comentarios de cabecera de `task-brief.py` y el
    docstring del test; `GOT-009` pasa de `propuesta` a `aceptada` al cierre (lo escribe quien cierra, no esta spec).
- **Fuera (por el §3 del análisis — «lo que NO es el problema» — con su motivo):**
  - **Subir el tope de 10.000.** Es el requisito CA-08 de la spec de `memory-retrieval` (≤ 2.500 tokens): un brief más largo
    degrada al subagente. Subirlo esconde el problema.
  - **Recortar `## La tarea` o `## Contrato de retorno`.** Son el contrato del subagente; recortarlos es lo que este repo ya
    graduó **ALTA** en `test_task_brief.py:190-192` («el brief salía SIN criterios»).
  - **Tocar la persona.** F1 de `project-specialization` (T-01) la acota con suelo garantizado + margen real y la delimita.
    Está fuera de esta iniciativa.
  - **Tocar la memoria.** Es la única sección bien resuelta (tope propio, recorte alineado, aviso): **es el patrón a copiar**.
  - Medir si el subagente rinde mejor con briefs más cortos (lo asume la spec de `memory-retrieval`; aquí se respeta).
  - Partir `main()` de `task-brief.py` (155 líneas): es alcance de `2026-09-09-plugin-refactor`; aquí solo se **ordena**
    frente a ella (ver Supuestos).
  - Cualquier cambio en `agents/`, `commands/`, hooks, `ledger-lint.py` o en el ledger de `project-specialization`.

## Manejo de errores

| Caso | Comportamiento |
|---|---|
| Una sección supera su tope propio | Se recorta con `_recorte_seguro` (alineado a línea; `## Diseño` por subsecciones enteras), se añade una nota de recorte en la propia sección y se avisa por stderr con la cifra; `rc=0` (degradación, nunca bloqueo) |
| El brief completo sigue por encima de `BRIEF_TOPE_CHARS` tras los recortes | Aviso por stderr con la causa medida por sección (el de F1, ampliado); el subagente recibe el brief igual; `rc=0` |
| `design.md` existe pero la tarea no referencia módulos del §5 (O2) | Puntero de una línea a `design.md` en vez de la sección; sin aviso (es el caso normal) |
| `design.md` sin §5 parseable (O2) | Se degrada al comportamiento de hoy (inyección completa, sujeta a `DISENO_TOPE_CHARS` si O1 entra) y se avisa por stderr |
| `Verificación` con evidencia pegada `(ejecutada … — salida: …)` (O4) | Entran solo los comandos; la nota «re-ejecútala» se mantiene; la salida grabada nunca entra |
| Tabla de gaps con filas de otras tareas u otros intentos (O3) | Entran solo las filas de `tid` del último intento (comportamiento de `:614`, ahora afirmado por test) |
| Test CA-08 sobre un ledger que aún desborda (O5, fase intermedia) | `xfail(reason="brief-budget pendiente de C-0X", strict=True)` con **fecha** en el motivo; nunca `skip` sin fecha |
| Consola cp1252 (Windows) | El aviso usa el snippet UTF-8 de `GOT-005` ya presente; sin símbolos nuevos fuera de él |

## Criterios de aceptación

Los criterios se verifican con comandos desde la raíz del repo, con `export PATH="$PWD/.venv/Scripts:$PATH"` en Windows y
sobre el ledger real de `project-specialization` **solo en lectura**. Los medidos en caracteres se toman en la máquina de
trabajo (`GOT-008`).

- [ ] [GWT] CA-01 — Dado el ledger real `docs/roadmap/2026-09-09-project-specialization/tasks.md` (22 tareas, `design.md`
  aprobado), Cuando se genera el brief de cada tarea, Entonces **0 de 22** miden más de 10.000 caracteres.
  `for t in $(grep -o '^### T-[0-9]*' docs/roadmap/2026-09-09-project-specialization/tasks.md | cut -c5-); do python3 agent-kits/shared/task-brief.py docs/roadmap/2026-09-09-project-specialization $t 2>/dev/null | wc -c; done | awk '$1>10000' | wc -l` → `0` (hoy: `12`).
- [ ] [GWT] CA-02 — Dado el mismo ledger, Cuando se generan los 22 briefs, Entonces stderr no contiene ningún aviso
  «por encima de BRIEF_TOPE_CHARS».
  `for t in $(grep -o '^### T-[0-9]*' docs/roadmap/2026-09-09-project-specialization/tasks.md | cut -c5-); do python3 agent-kits/shared/task-brief.py docs/roadmap/2026-09-09-project-specialization $t 2>&1 >/dev/null; done | grep -c "por encima de BRIEF_TOPE_CHARS"` → `0` (hoy: `12`).
- [ ] [GWT] CA-03 — Dado el mismo ledger, Cuando se mide la sección `## Diseño` de los 22 briefs, Entonces su tamaño **no es
  constante** (al menos dos valores distintos; con O2, las tareas sin referencia al §5 llevan solo el puntero).
  `for t in $(grep -o '^### T-[0-9]*' docs/roadmap/2026-09-09-project-specialization/tasks.md | cut -c5-); do python3 agent-kits/shared/task-brief.py docs/roadmap/2026-09-09-project-specialization $t 2>/dev/null | awk '/^## Diseño/{f=1;next} /^## /{f=0} f' | wc -c; done | sort -u | wc -l` → `>= 2` (hoy: `1`, valor 3.510).
- [ ] [GWT] CA-04 — Dado `test_task_brief.py`, Cuando se ejecuta el test del CA-08, Entonces recorre **todos** los
  `docs/roadmap/*/tasks.md` (con y sin `design.md`) y está en verde en la máquina de trabajo.
  `grep -c 'docs/roadmap/\*/tasks.md\|glob("docs/roadmap' agent-kits/shared/test_task_brief.py` → `>= 1` · `python3 -m pytest agent-kits/shared/test_task_brief.py -q -k ca08` → `passed`, `0 xfailed` al cierre.
- [ ] [GWT] CA-05 — Dada una tarea con `Verificación` que trae la salida pegada `(ejecutada <fecha> — salida: …)`, Cuando se
  genera su brief, Entonces la sección `## Verificación` contiene los comandos y **no** la salida grabada (O4).
  `python3 agent-kits/shared/task-brief.py docs/roadmap/2026-09-09-project-specialization T-02 2>/dev/null | awk '/^## Verificación/{f=1;next} /^## /{f=0} f' | wc -c` → `<= 800` (hoy: 2.285); test unitario en `tmp_path` que lo afirma.
- [ ] [GWT] CA-06 — Dado un ledger con dos intentos de revisión y filas de varias tareas, Cuando se genera el brief de una,
  Entonces `## Gaps pendientes` solo lleva las filas de **esa** tarea del **último** intento y su tamaño queda bajo su tope (O3/O1).
  `python3 -m pytest agent-kits/shared/test_task_brief.py -q -k gaps` → `passed` (test nuevo sobre `tmp_path`).
- [ ] CA-07 — Cada constante nueva `*_TOPE_CHARS` lleva en comentario **la medición que la justifica** (mediana/máximo del §1
  del análisis o re-medida) y un test que la afirma, calcando `MEMORIA_TOPE_CHARS`.
  `grep -n "^[A-Z_]*_TOPE_CHARS = " agent-kits/shared/task-brief.py` → las de hoy (`MEMORIA`, `BRIEF`, `PERSONA`) más las nuevas, cada una con `#` de justificación en la misma línea o el bloque inmediatamente anterior.
- [ ] CA-08 — Los invariantes del §3 del análisis se mantienen: `BRIEF_TOPE_CHARS == 10000`, `MEMORIA_TOPE_CHARS == 2400`,
  `PERSONA_SUELO_CHARS == 1300`, y `## La tarea` / `## Contrato de retorno` salen **byte a byte iguales** que antes del cambio
  para las 22 tareas.
  `grep -c "^BRIEF_TOPE_CHARS = 10000\|^MEMORIA_TOPE_CHARS = 2400\|^PERSONA_SUELO_CHARS = 1300" agent-kits/shared/task-brief.py` → `3` · `python3 -m pytest agent-kits/shared/test_task_brief.py -q -k "fence_no_trunca or contrato or persona"` → `passed` · diff de esas dos secciones entre HEAD y la rama → vacío.
- [ ] CA-09 — Ningún `skip`/`xfail` sin motivo **y fecha** en la suite; al cierre, ningún `xfail` de esta iniciativa.
  `grep -n "xfail\|pytest.skip\|skipif" agent-kits/shared/test_task_brief.py | grep -v "20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]\|sin el ledger real"` → vacío.
- [ ] CA-10 — La suite completa del script está en verde y no baja el número de tests.
  `python3 -m pytest agent-kits/shared/test_task_brief.py -q` → `>= 60 passed` (hoy 60 definidos; el del CA-08 falla en Windows en HEAD por `GOT-008`, ruta absoluta — no es de esta iniciativa, pero la versión O5 del test **debe** pasar aquí).
- [ ] CA-11 — `task-brief.py` sigue siendo standalone (sin `import` de módulos del kit) y conserva el snippet UTF-8 de `GOT-005`.
  `grep -n "^from agent_kits\|^import agent_kits\|^from shared" agent-kits/shared/task-brief.py` → vacío · `python3 -m pytest tests/test_console_encoding.py -q` → `passed`.
- [ ] CA-12 — Las puertas del repo siguen en verde: `python3 scripts/lint_plugin.py` → `0 errores` · `python3 evals/check.py` → ok
  · `python3 scripts/export-interop.py --check` → sin cambios pendientes (el script no es pieza traducida, pero la puerta se corre igual).

## Pruebas

- **Unitarias sobre `tmp_path`** (patrón del fixture `inic`): un ledger sintético con `design.md` aprobado (con y sin §5
  parseable), dos intentos de revisión con filas de varias tareas, y una `Verificación` con evidencia pegada. Un test por tope
  (`DISENO`, `GAPS`, `VERIFICACION`), uno por criterio de O2 (referencia / sin referencia / §5 ausente), uno para O3 y uno para O4.
  Cada tope se afirma **con recorte que no parte fences** (reutiliza los casos de `_recorte_seguro`).
- **Integración sobre el corpus real** (solo lectura): CA-01…CA-03 y CA-05 sobre `project-specialization`; CA-04 sobre todos los
  ledgers. Medidas en la máquina de trabajo; el test deja margen (`GOT-008`).
- **Regresión**: los 60 tests de hoy siguen pasando (CA-10); las secciones intocables salen byte a byte iguales (CA-08).
- **Secuenciación de O5**: el test sobre todos los ledgers nace `xfail(strict=True)` fechado (RED evidenciable si `dev.json`
  activa `tdd`) y pasa a verde como **último** paso; su tiempo de ejecución se controla (ver Supuestos).
- Sin `test-plan.md` E2E: no hay UI. Los `[GWT]` son criterios de CLI que `qa`/`coverage-check.py` cubren con los comandos citados.

## Referencias

- [`analysis.md`](analysis.md) — §1 medición por secciones (22 × 7), §2 por qué nadie lo vio, §3 lo que NO es el problema,
  §4 opciones O1-O5, §5 riesgos, §6 señales de éxito.
- `agent-kits/shared/task-brief.py` — `:105-133` constantes · `:158-205` memoria (patrón) · `:271` `_recorte_seguro` ·
  `:406` `_verificacion_de_tarea` · `:531` `_design_elegida` · `:595` `_gaps_pendientes_de_tarea` · `:621` `_seccion_plan` ·
  `:640` `main()` · `:722-738` gaps · `:740-752` verificación · `:818-833` aviso de F1.
- `agent-kits/shared/test_task_brief.py` — `:190-192` (recorte del contrato, ALTA) · `:657-670` verificación · `:753` CA-08
  sobre `tmp_path` · `:781` CA-08 sobre `memory-retrieval`.
- `agent-kits/architect/templates/design.md:97` — §5 «Impacto en módulos y ficheros» (solo O2).
- `docs/roadmap/2026-09-04-memory-retrieval/spec.md:277` — CA-08 original (≤ 2.500 tokens).
- `docs/knowledge/gotchas/GOT-008-…` (`aceptada`; su remedio presupone que no hay diseño) · `GOT-009-…` (`propuesta`; este hallazgo).
- `docs/roadmap/2026-09-09-plugin-refactor/analysis.md:61,121-122` — propone partir `main()` de `task-brief.py` (155 líneas)
  **antes** de añadirle presupuestos por sección.

## Decisiones confirmadas (revisión del usuario · 2026-09-09)

1. Abrir iniciativa aparte en vez de absorber el hallazgo en F1 de `project-specialization` (opción B). **Confirmado** (`analysis.md`, Procedencia).
2. Las cinco opciones se presupuestan por separado; cuáles entran y en qué orden se decide en la puerta go/no-go de `/pm-cycle`. **Pendiente de la puerta.**

## Supuestos

- **Orden frente a `plugin-refactor`.** Su análisis propone partir `main()` de `task-brief.py` antes de que esta iniciativa
  le añada presupuestos (al revés se refactoriza dos veces). Se asume que **el usuario ordena las dos en la puerta**; esta spec
  no lo decide. Si `brief-budget` va primero, las funciones nuevas se escriben ya como funciones con nombre por sección para
  que el refactor las mueva sin reescribirlas.
- **La premisa de O3 hay que verificarla antes de planificar su tarea.** `_gaps_pendientes_de_tarea` (`task-brief.py:614`) ya
  filtra por `celdas[3] == tid` y por último intento; los 4.396 de T-01 pueden ser filas legítimas de la propia T-01. Si es
  así, O3 se reduce a **acotar** (tope + recorte) en vez de filtrar, y su esfuerzo baja. Lo verifica el planner con
  `python3 agent-kits/shared/task-brief.py docs/roadmap/2026-09-09-project-specialization T-01 2>/dev/null | awk '/^## Gaps/{f=1;next} /^## /{f=0} f' | grep -c '^- \*\*\['`.
- **Coste del test O5.** Un brief tarda ~3 s en esta máquina (medido: T-05, 2,9 s); 32 ledgers × ~10 tareas ≈ 300 briefs
  ≈ 15 min de suite. Se asume que el planner acota (p. ej. parametrizar por ledger con marca `slow`, o recorrer los ledgers
  con `design.md` más `memory-retrieval` y una muestra del resto) **sin** volver al guardarraíl de un solo ledger.
- **Las cifras son de esta máquina y de hoy.** La revisión en curso sobre el ledger de `project-specialization` mueve la tabla
  de gaps y la `Verificación` de sus tareas; CA-01…CA-03 se miden sobre el ledger tal como esté al cerrar, y los topes
  nuevos dejan margen (`GOT-008`: ~250 caracteres de ruta + corpus).
- **El corpus `docs/knowledge/` crece** (37 entradas hoy): la memoria satura en 2.400 y ahí se detiene; los topes nuevos
  deben presuponer la memoria **al tope**, no en su mediana (aritmética del §1: 6.935 comprometidos en el peor caso).
- **`design.md` de otras iniciativas futuras** tendrá el §5 con la estructura de la plantilla del architect; si el planner
  elige O2, la plantilla se ajusta en la misma iniciativa (alcance declarado por el análisis).
