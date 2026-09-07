---
generacion:            # ventana compartida con spec.md · evaluation.md · improvement-plan.md (se cuenta UNA vez)
  inicio: 2026-09-04T09:00:00Z
  fin: 2026-09-04T09:40:00Z
  fuente: estimado     # el usage-meter no puede leer la transcripción en este entorno: no hay medición
  tokens_reales: { entrada: 180000, salida: 60000, cache_creacion: 40000, cache_lectura: 900000 }
  eur: 2.85
  horas_ia: 0.58
  duracion: 40m
  ratio_usado: 479326
verificacion: obligatoria   # cada T-XX lleva `- **Verificación**:`; lo exige ledger-lint (exit 1 si falta)
---

# Checklist de Tareas — Memoria técnica recuperable (tres capas, dos velocidades y un presupuesto por camino)

| | |
|---|---|
| **Estado** | borrador |
| **Fecha** | 2026-09-04 |
| **Plan** | [`improvement-plan.md`](./improvement-plan.md) |
| **Spec** | [`spec.md`](./spec.md) |
| **Evaluación** | [`evaluation.md`](./evaluation.md) |
| **Análisis de origen** | [`analysis.md`](./analysis.md) |
| **Diseño** | n/a |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del plan. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador SDD externo— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

> **Todas las tareas están sin empezar** (`borrador`). Ninguna se ha ejecutado: este ledger es la
> salida del `planner`, no de una implementación. El campo opcional `- **Changelog**:` se deja
> **fuera a propósito**: lo escribe quien CIERRA la tarea (`ADR-012`), y ponerlo ahora con el
> placeholder de la plantilla solo produciría avisos de `ledger-lint` y un bullet degradado.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — Recuperación | 0 | 4 | 0% | 0 / 9,0h | 0 / 0,51h | 0 / 0,13h | 0 / 245.000 |
| Fase 2 — Llegada | 0 | 3 | 0% | 0 / 4,0h | 0 / 0,31h | 0 / 0,08h | 0 / 150.000 |
| Fase 3 — Prueba de que se recorre | 0 | 3 | 0% | 0 / 4,0h | 0 / 0,27h | 0 / 0,07h | 0 / 128.000 |
| Fase 4 — Captura episódica | 0 | 4 | 0% | 0 / 7,0h | 0 / 0,43h | 0 / 0,11h | 0 / 205.000 |
| Fase 5 — Que la doctrina viaje | 0 | 2 | 0% | 0 / 3,0h | 0 / 0,24h | 0 / 0,06h | 0 / 115.000 |
| Fase 6 — Cerrar el bucle | 0 | 2 | 0% | 0 / 3,0h | 0 / 0,30h | 0 / 0,08h | 0 / 145.000 |
| Revisión de dos lentes (transversal, línea propia) | — | — | — | 0 / 4,0h | 0 / 0,54h | 0 / 0,13h | 0 / 260.000 |
| **TOTAL** | **0** | **18** | **0%** | **0 / 34,0h** | **0 / 2,60h** | **0 / 0,66h** | **0 / 1.248.000** |

> **Horas → Jira.** El worklog que imputa `jira-sync` al completar cada tarea es **Tiempo IA (ejec.) + Supervisión** (real; o estimación si no hay real), topado a la jornada configurada (8 h). Ver `skills/jira-sync/SKILL.md`.
>
> Las horas IA salen de **tokens ÷ 479.326 tok/h** (mediana medida de 5 muestras, `CALIBRATION.md`), no del default no calibrado de 300.000. La supervisión es el **25 %** de las horas IA (`rates.json` `ratioSupervision`); el total exacto sería 0,65 h y la suma por tarea da **0,66 h** por redondeo — se usa 0,66 h para que plan y ledger digan lo mismo.

---

## Fase 1 — Recuperación

**Estado**: borrador · **Estimado**: 9,0h · **Real**: — · **Coste est.**: 452 € · **Tokens est.**: 245.000

> Cierra los huecos **2** («no hay búsqueda») y **5** («el índice no lo vigila nada») de
> `analysis.md` §1.4. No depende de nada, y es lo que más rinde: por eso va primera.

### T-01 — Capa 1 de `knowledge-find.py`: consulta → aciertos compactos

- **Descripción**: script nuevo `agent-kits/shared/knowledge-find.py` que sustituye «lee el índice y decide» por «pregunta y recibe». Devuelve **una línea por acierto** con el formato `ID · estado · área · titular · ruta` (~25 tokens), ordenada por relevancia y con el **`estado` DELANTE** para que el lector sepa si tiene doctrina (`aceptada`), indicio (`propuesta`) u obsoleta con sucesor. Admite `--area`, `--tipo`, `--limit`, `--json` y consulta libre posicional. El área se casa **normalizada** (minúsculas, sin acentos, por token), no por comparación exacta: medido hoy, la columna «Área» tiene **21 valores distintos para 31 entradas**, casi todos singleton.
- **Estado**: borrador
- **Tiempo humano**: est. 3,0h · real —
- **Tiempo IA (ejec.)**: est. 0,17h · real —
- **Supervisión**: est. 0,04h (≈25 % IA) · real —
- **Previsión IA**: 65k in / 20k out tok · 0,76 €
- **Dependencias**: ninguna
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/knowledge-find.py`, `tests/test_knowledge_find.py`
- **Verificación**: `python3 agent-kits/shared/knowledge-find.py --area estimacion --json` → las **9** entradas de área «Estimación / calibración» (`grep -c "Estimación / calibración" docs/knowledge/README.md` → 9), salida completa ≤ 1.200 caracteres, exit 0 · `python3 agent-kits/shared/knowledge-find.py "consola windows cp1252" --limit 5` → `GOT-005` primero, ≤ 5 líneas, cada línea ≤ 120 caracteres, exit 0 · `python3 -m pytest -q tests/test_knowledge_find.py` → todos passed · `python3 agent-kits/shared/knowledge-find.py --area no-existe-esta-area` → sin líneas y exit 0

**Criterios de aceptación**
- [ ] `--area estimacion --json` devuelve las **9** entradas de esa área en **≤ 300 tokens (≤ 1.200 caracteres)** con **exit 0** (spec CA-01). Nota medida: las **6** que menciona `analysis.md` §1.5 son las *no citadas*, no las del área — no se confunden.
- [ ] Cada acierto es **≤ 30 tokens (≤ 120 caracteres)** y trae `ID · estado · área · titular · ruta` **en ese orden**, con el `estado` delante (spec CA-02).
- [ ] Una consulta libre ordena por relevancia: `"consola windows cp1252"` pone `GOT-005` primero.
- [ ] Sin `docs/knowledge/` o sin aciertos: **0 líneas y exit 0** — ni una línea de relleno para decir que no hay nada (no gastar contexto).
- [ ] El área se casa normalizada: `--area estimacion` encuentra «Estimación / calibración».
- [ ] Reconfiguración UTF-8 de `stdin`/`stdout`/`stderr` al arrancar (`GOT-005`), como los otros 28 scripts del repo.

**Subtareas**
- [ ] Escribir primero el test que afirma el formato y el tope por acierto (RED), como manda la skill `tdd` si `dev.json` la trae activa.
- [ ] Parsear el índice `docs/knowledge/README.md` (tabla de 31 filas) y el frontmatter de cada entrada.
- [ ] Normalizar área/tipo y ordenar por relevancia.
- [ ] Salida humana y `--json`; exit codes documentados en el docstring.

**Notas**: la salida `--json` es la que consumirán `task-brief.py` (T-05) y `session-context.sh` (T-06): su esquema es contrato, y cambiarlo después rompe dos consumidores.

### T-02 — Capa 2: `--related <ID>` con grafo curado

- **Descripción**: segunda capa de recuperación. `--related <ID>` devuelve el **grafo curado** de una entrada: ADR sucesor/sustituido, entradas de la **misma iniciativa** y entradas de la **misma área**. Sustituye deliberadamente la `timeline` de `claude-mem` («qué pasó cerca en el tiempo»): un grafo de sustitución y área es mejor información al mismo coste de tokens.
- **Estado**: borrador
- **Tiempo humano**: est. 2,0h · real —
- **Tiempo IA (ejec.)**: est. 0,11h · real —
- **Supervisión**: est. 0,03h (≈25 % IA) · real —
- **Previsión IA**: 40k in / 12k out tok · 0,46 €
- **Dependencias**: T-01
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/knowledge-find.py`, `tests/test_knowledge_find.py`
- **Verificación**: `python3 agent-kits/shared/knowledge-find.py --related ADR-010` → agrupa sucesor/sustituido, misma iniciativa y misma área, ≤ 1.600 caracteres, exit 0, **sin ninguna línea de cronología** · `python3 agent-kits/shared/knowledge-find.py --related ID-INEXISTENTE` → una línea en stderr y exit 1 · `python3 -m pytest -q tests/test_knowledge_find.py -k related` → todos passed

**Criterios de aceptación**
- [ ] `--related ADR-010` devuelve el grafo curado en **≤ 400 tokens (≤ 1.600 caracteres)** con **exit 0** (spec CA-03).
- [ ] Las tres relaciones salen **etiquetadas y separadas** (sucesión · iniciativa · área), no como una lista plana.
- [ ] Una entrada `obsoleta` muestra su **sucesor**; una `aceptada` que sustituyó a otra muestra a **quién sustituyó**.
- [ ] **No hay salida cronológica**: ningún «qué pasó cerca en el tiempo». Es una decisión de diseño, no una omisión.
- [ ] ID inexistente → **exit 1** con una línea en stderr (error de uso, no degradación).

**Subtareas**
- [ ] Test RED con un corpus de `tmp_path` que tenga un ADR sustituido y un sucesor.
- [ ] Extraer las relaciones del frontmatter y de la columna «Fuente» del índice.
- [ ] Agrupar y topar la salida.

**Notas**: `ADR-010` es el caso de prueba natural porque esta misma iniciativa lo **revisa** (T-12), así que el grafo tiene que saber contarlo.

### T-03 — Capa 3 (`--show`) e índice SQLite FTS5 reconstruible

- **Descripción**: tercera capa (`--show <ID>` → la entrada completa) y el índice de búsqueda: **SQLite FTS5 en `.claude/`, no versionado y RECONSTRUIBLE desde los ficheros**. El índice guarda el hash del corpus; si falta, está corrupto o el hash no cuadra → se reconstruye; si no se puede reconstruir (`.claude/` de solo lectura, `sqlite3` sin FTS5) → **recorrido plano** de los ficheros con los mismos aciertos. **Nunca sale con código ≠ 0 por culpa del índice.** Aquí está la diferencia estructural con `claude-mem`: para ellos la base **ES** el almacén (base corrupta = memoria perdida y nada revisable); para nosotros es una **caché**. Cero dependencias: `sqlite3` es stdlib.
- **Estado**: borrador
- **Tiempo humano**: est. 2,5h · real —
- **Tiempo IA (ejec.)**: est. 0,15h · real —
- **Supervisión**: est. 0,04h (≈25 % IA) · real —
- **Previsión IA**: 55k in / 15k out tok · 0,60 €
- **Dependencias**: T-01
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/knowledge-find.py`, `tests/test_knowledge_find.py`, `.gitignore`
- **Verificación**:
  - `python3 agent-kits/shared/knowledge-find.py --show ADR-012` → la entrada completa, ≤ 10.800 caracteres (la mayor de hoy son 10.449), exit 0
  - `python3 agent-kits/shared/knowledge-find.py --show NO-EXISTE` → una línea en stderr, exit 1
  - `rm -f .claude/knowledge-index.sqlite && python3 agent-kits/shared/knowledge-find.py --area estimacion --json` → `"indice": "construido"`, 9 aciertos, exit 0
  - `printf 'basura' > .claude/knowledge-index.sqlite && python3 agent-kits/shared/knowledge-find.py --area estimacion --json` → `"indice": "reconstruido"`, 9 aciertos, exit 0
  - `python3 -c "import sqlite3; sqlite3.connect(':memory:').execute('CREATE VIRTUAL TABLE t USING fts5(x)')"` → sin excepción (FTS5 presente en este Python)
  - `git check-ignore -v .claude/knowledge-index.sqlite` → una línea con la regla que lo ignora
  - `python3 -m pytest -q tests/test_knowledge_find.py` → todos passed

**Criterios de aceptación**
- [ ] `--show <ID>` devuelve la entrada completa en **≤ 2.700 tokens** (máximo real hoy: 10.449 caracteres ≈ 2.612 tokens, `ADR-012`) con **exit 0**; ID inexistente → **exit 1** (spec CA-04).
- [ ] Índice ausente → se construye; `--json` trae `indice: "construido"`, mismos aciertos, **exit 0** (spec CA-05).
- [ ] Índice corrupto **o** hash que no cuadra → se reconstruye; `indice: "reconstruido"`, **exit 0**.
- [ ] `.claude/` no escribible **o** `sqlite3` sin FTS5 → **recorrido plano**, `indice: "degradado"`, **aciertos idénticos** a los del camino con índice, **exit 0** (spec CA-06).
- [ ] El índice está en `.gitignore` y `git check-ignore` lo confirma: **el almacén son los ficheros, el índice es caché**.
- [ ] **Cero dependencias nuevas**: el script se ejecuta con `python3` a secas, sin `pip install`.

**Subtareas**
- [ ] Test RED de los tres estados del índice y de las dos degradaciones, con `tmp_path` y un `.claude/` de solo lectura.
- [ ] Esquema FTS5 mínimo + hash del corpus guardado dentro del propio índice.
- [ ] Camino plano como implementación de respaldo del **mismo** contrato de salida.
- [ ] Añadir la regla al `.gitignore` (el log crudo de T-11 ya está cubierto por `*.log`, verificado).

**Notas**: la degradación es parte de la spec (§Manejo de errores), no un añadido: no se puede garantizar FTS5 en la máquina del consumidor.

### T-04 — Lint del índice: biyección `ficheros ↔ filas` y `area` obligatoria

- **Descripción**: test barato que vigila el índice de memoria igual que `tests/test_roadmap_index.py` vigila su hermano del roadmap — y por la misma razón: una entrada **sin fila es invisible** para el único camino de lectura y no hay grep de respaldo. Afirma la **biyección** (todo fichero de `adr/`/`gotchas/`/`lessons/` tiene fila, y toda fila apunta a un fichero que existe) y que **cada fila tiene columna «Área»** no vacía. Esto último no es cosmético: **para los 12 ADR el `area` SOLO vive en el índice**, así que perder la fila es perder el enrutado **sin poder reconstruirlo**.
- **Estado**: borrador
- **Tiempo humano**: est. 1,5h · real —
- **Tiempo IA (ejec.)**: est. 0,08h · real —
- **Supervisión**: est. 0,02h (≈25 % IA) · real —
- **Previsión IA**: 30k in / 8k out tok · 0,32 €
- **Dependencias**: ninguna (puede ir en paralelo a T-01…T-03)
- **Tipo**: test
- **Archivos**: `tests/test_knowledge_index.py`
- **Verificación**: `python3 -m pytest -q tests/test_knowledge_index.py` → todos passed sobre el corpus de hoy (31 entradas, 31 filas) · con una fila borrada a mano → **falla nombrando el fichero sin fila** · con la columna «Área» vaciada en una fila → **falla nombrando el ID** · `python3 -m pytest -q` → ≥ 1.175 passed

**Criterios de aceptación**
- [ ] Verde sobre el corpus de hoy: **31 ficheros ↔ 31 filas** (spec CA-07).
- [ ] Quitar una fila del índice pone el test **rojo nombrando el fichero**.
- [ ] Una fila sin «Área» pone el test **rojo nombrando el ID**.
- [ ] Una fila que apunta a un fichero inexistente pone el test **rojo** (la biyección va en los dos sentidos).
- [ ] El test **no ejecuta nada** y solo lee dos cosas del disco, como su hermano: `tests/test_roadmap_index.py` es deliberadamente barato y este también.
- [ ] El propio test trae su **caso sintético** de detección (que la regla se cumple sin depender del estado del repo), copiando el patrón de `test_el_detector_pilla_la_fila_suelta`.

**Subtareas**
- [ ] Parsear la tabla del índice (bloque contiguo de líneas `|`, como hace `tabla_y_cola`).
- [ ] Comparar con `glob` de las tres carpetas.
- [ ] Caso sintético de la regla, independiente del repo.

**Notas**: `analysis.md` §1.4-5 llama a esto «la asimetría demostrable»: el índice hermano del roadmap tiene test y el de memoria no.

---

## Fase 2 — Llegada

**Estado**: borrador · **Estimado**: 4,0h · **Real**: — · **Coste est.**: 201 € · **Tokens est.**: 150.000

> Cierra el hueco **1** de `analysis.md` §1.4, el **más caro**: con `subagentes: true` el brief es el
> ÚNICO contexto (`commands/dev-cycle.md:110`) y hoy no lleva memoria, así que quien escribe el
> código **no puede alcanzar un gotcha ni queriendo**.

### T-05 — Memoria técnica en `task-brief.py`, presupuestada y enrutada por `Tipo`

- **Descripción**: sección nueva en el brief del subagente con los aciertos de `knowledge-find.py` para el área y el tipo de la tarea. El enrutado **ya existe**: el campo `- **Tipo**: frontend|backend|db|devops|test|docs` está en el ledger desde `subagent-personas`. Tope explícito de **600 tokens** frente a los **1.818** que mide el brief hoy, y **degradación silenciosa**: sin `docs/knowledge/` o sin aciertos, el brief sale idéntico al de hoy.
- **Estado**: borrador
- **Tiempo humano**: est. 2,0h · real —
- **Tiempo IA (ejec.)**: est. 0,17h · real —
- **Supervisión**: est. 0,04h (≈25 % IA) · real —
- **Previsión IA**: 65k in / 16k out tok · 0,67 €
- **Dependencias**: T-01
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/task-brief.py`, `agent-kits/shared/test_task_brief.py`
- **Verificación**:
  - `python3 agent-kits/shared/task-brief.py docs/roadmap/2026-09-04-memory-retrieval T-06 | grep -c "Memoria técnica"` → 1 (T-06 lleva `- **Tipo**: devops`)
  - `python3 agent-kits/shared/task-brief.py docs/roadmap/2026-09-04-memory-retrieval T-06 | wc -c` → ≤ 10.000 caracteres (línea base de hoy re-medida: 7.452 en `changelog-brief` T-01)
  - `python3 agent-kits/shared/task-brief.py docs/roadmap/2026-09-04-memory-retrieval T-06 | sed -n '/## Memoria técnica/,/^## /p' | wc -c` → ≤ 2.400 caracteres
  - `python3 -m pytest -q agent-kits/shared/test_task_brief.py` → todos passed
  - en un árbol sin `docs/knowledge/`: la salida del brief es **byte a byte** la de hoy salvo la sección ausente, exit 0

**Criterios de aceptación**
- [ ] La sección de memoria es **≤ 600 tokens (≤ 2.400 caracteres)** y el brief completo **≤ 2.500 tokens** (spec CA-08).
- [ ] El enrutado usa el campo `- **Tipo**:` que **ya existe**; sin `Tipo`, cae al área de la iniciativa y no al corpus entero.
- [ ] Sin `docs/knowledge/` o sin aciertos: salida **idéntica a la de hoy**, sin aviso en stdout ni sección vacía, exit 0 (spec CA-09).
- [ ] El tope es una **constante con test**, no una intención: un mutante que la suba pone el test rojo.
- [ ] Las **10 secciones actuales** del brief siguen intactas y en su orden.
- [ ] Un fallo de `knowledge-find.py` (cualquiera) **no rompe el brief**: se omite la sección y el brief sale con exit 0.

**Subtareas**
- [ ] Test RED del tope y de la degradación silenciosa.
- [ ] Llamar a `knowledge-find.py --json` y renderizar la sección 11.
- [ ] Recorte al tope con la línea que lo dice, nunca emitir por encima.

**Notas**: `analysis.md` §1.4-1, medido: hoy `grep` sobre `task-brief.py` da un solo acierto de `knowledge`, y es un comentario de encoding.

### T-06 — Memoria del área activa al arrancar sesión, con tope propio

- **Descripción**: `session-context.sh` gana un cuarto bloque: **no el corpus** (27.100 tokens no caben en el `TOPE_CHARS = 9500` del hook) sino los N mejores aciertos del **área de la iniciativa activa**, con tope explícito de **300 tokens**. Hoy el hook inyecta 872 tokens y **ninguno** es memoria curada.
- **Estado**: borrador
- **Tiempo humano**: est. 1,5h · real —
- **Tiempo IA (ejec.)**: est. 0,10h · real —
- **Supervisión**: est. 0,03h (≈25 % IA) · real —
- **Previsión IA**: 40k in / 10k out tok · 0,41 €
- **Dependencias**: T-01
- **Tipo**: devops
- **Archivos**: `hooks/session-context.sh`, `tests/test_hooks_shell.py`
- **Verificación**:
  - `echo '{"hook_event_name":"SessionStart","source":"startup"}' | bash hooks/session-context.sh | python3 -c "import json,sys; t=json.load(sys.stdin)['hookSpecificOutput']['additionalContext']; print(len(t))"` → ≤ 9.500
  - la porción de memoria de ese `additionalContext` → ≤ 1.200 caracteres
  - `echo '{"hook_event_name":"SessionStart","source":"compact"}' | bash hooks/session-context.sh` → JSON válido, exit 0
  - en un árbol sin `docs/knowledge/`: el hook **no emite el bloque** y el resto sale igual, exit 0
  - `python3 -m pytest -q tests/test_hooks_shell.py` → todos passed

**Criterios de aceptación**
- [ ] El bloque de memoria es **≤ 300 tokens (≤ 1.200 caracteres)** y el `additionalContext` total sigue **≤ 9.500 caracteres** (spec CA-10). Línea base: 872 tokens, **0** de memoria.
- [ ] El tope propio se aplica **antes** del recorte global a `TOPE_CHARS`, para que la memoria no se coma el índice de piezas ni el roadmap.
- [ ] Sin iniciativa activa, sin `docs/knowledge/` o sin aciertos: **no se emite el bloque**; el resto de la salida es la de hoy.
- [ ] El hook sigue **siempre exit 0** y nunca emite JSON inválido, pase lo que pase con la memoria.
- [ ] Desactivable por `.claude/dev.json` → `sesion.memoria: false`, como ya se puede con `sesion.indice` y `sesion.journal`.

**Subtareas**
- [ ] Test RED en `tests/test_hooks_shell.py` con un fixture de iniciativa activa.
- [ ] Derivar el área de la iniciativa activa (`progress-report.py active` ya la sabe).
- [ ] Insertar el bloque (4) y respetar el orden actual de los tres que hay.

**Notas**: `TOPE_CHARS = 9500` está en `hooks/session-context.sh:88` y viene del tope de 10.000 caracteres del contrato oficial del hook.

### T-07 — El reparto por agente de `knowledge-check.md` deja de ser solo prosa

- **Descripción**: la tabla «qué lee cada agente» del fragmento compartido pasa de decir *qué debería abrir* a **nombrar el comando** de `knowledge-find.py` que le corresponde (`evaluator` → `--area estimacion`, `implementer` → área de la tarea, `qa` → `--tipo gotcha`, etc.). El fragmento sigue siendo la **fuente única**: no se duplica en ningún prompt.
- **Estado**: borrador
- **Tiempo humano**: est. 0,5h · real —
- **Tiempo IA (ejec.)**: est. 0,04h · real —
- **Supervisión**: est. 0,01h (≈25 % IA) · real —
- **Previsión IA**: 15k in / 4k out tok · 0,16 €
- **Dependencias**: T-01
- **Tipo**: docs
- **Archivos**: `agent-kits/shared/knowledge-check.md`
- **Verificación**: `grep -c "knowledge-find.py" agent-kits/shared/knowledge-check.md` → ≥ 5 (una por agente de la tabla) · `python3 scripts/lint_plugin.py` → exit 0 · lectura: cada fila de la tabla «Reparto de qué lee cada agente» nombra su comando y **ninguna** sigue pidiendo «lee el índice y decide» · lectura: el fragmento no se ha copiado a ningún prompt (`grep -rl "Reparto de qué lee cada agente" agents/` → sin resultados)

**Criterios de aceptación**
- [ ] Las **5** filas de la tabla nombran su comando concreto de `knowledge-find.py` (spec CA-11).
- [ ] La regla de **progressive disclosure** se conserva: la 1.ª capa no obliga a abrir nada.
- [ ] La distinción por `estado` (doctrina / indicio / obsoleta con sucesor) se conserva **literal**: es el criterio 1 de superioridad y no se toca al reescribir.
- [ ] El fragmento sigue siendo **fuente única**: no aparece copiado en ningún `agents/*.md`.
- [ ] `lint_plugin.py` sigue en **exit 0** (hoy: 9 agentes · 0 errores · 3 avisos).

**Subtareas**
- [ ] Reescribir la tabla del reparto.
- [ ] Añadir el ejemplo de invocación con localización del kit (regla 5 de `CONVENTIONS`).

**Notas**: es la única tarea de esta fase que se verifica **por lectura** en su mayor parte, y así se declara — es prosa, y fingir un test sería peor.

---

## Fase 3 — Prueba de que se recorre

**Estado**: borrador · **Estimado**: 4,0h · **Real**: — · **Coste est.**: 201 € · **Tokens est.**: 128.000

> **Esto no lo tiene nadie —ni nosotros ni `claude-mem`— y es la diferencia entre una intención y una
> garantía.** El gate es determinista y no gasta tokens; la eval de activación es la comprobación de
> comportamiento y vive donde ya viven las caras.

### T-08 — `tests/test_memory_path.py`: el camino se recorre, con su mutante

- **Descripción**: test determinista que afirma que un agente con una tarea de **área X** recibe la entrada de **área X**: sobre un corpus de `tmp_path`, el brief de una tarea de área X contiene el ID de la entrada de área X y **no** los de otras áreas. Y —la parte que lo hace valer— se prueba **con su mutante**: quitando la inyección de `task-brief.py`, el test se pone **rojo**. Un test que pasa con y sin la inyección no prueba nada.
- **Estado**: borrador
- **Tiempo humano**: est. 1,5h · real —
- **Tiempo IA (ejec.)**: est. 0,10h · real —
- **Supervisión**: est. 0,03h (≈25 % IA) · real —
- **Previsión IA**: 38k in / 10k out tok · 0,40 €
- **Dependencias**: T-05, T-06
- **Tipo**: test
- **Archivos**: `tests/test_memory_path.py`
- **Verificación**: `python3 -m pytest -q tests/test_memory_path.py` → todos passed · con la llamada a `knowledge-find.py` neutralizada en `task-brief.py` → **falla**, y el mensaje nombra el área y el ID que no llegaron · `python3 -m pytest -q` → ≥ 1.175 passed · `python3 -m pytest -q tests/test_memory_path.py` sin red y sin `claude` en PATH → sigue passed

**Criterios de aceptación**
- [ ] Verde hoy y **rojo con el mutante** (spec CA-12): se documenta en el propio test qué se neutraliza para verlo rojo.
- [ ] Cubre **los dos** caminos de llegada: el brief (T-05) y el arranque de sesión (T-06).
- [ ] Afirma también el **tope** de cada camino (600 / 300 tokens), no solo la presencia.
- [ ] **No usa red, ni `claude`, ni clave de API**, y corre sobre `tmp_path`, no sobre el corpus real.
- [ ] Un aserto **negativo**: una tarea de área Y **no** recibe la entrada de área X (si recibe todo, no hay enrutado).

**Subtareas**
- [ ] Fixture con un corpus mínimo de dos áreas y una iniciativa de mentira.
- [ ] Asertos de presencia, de ausencia y de tope.
- [ ] Documentar el mutante en el docstring.

**Notas**: este test es el **gate**; la eval de T-09 es la comprobación de comportamiento. No se confunden los papeles.

### T-09 — Casos en `evals/` para el camino de memoria

- **Descripción**: casos nuevos en `evals/cases/agent-implementer.json` y `agent-evaluator.json` que afirmen que el agente **usa** la memoria de su área (menciona el ID que le corresponde) en vez de ignorarla. Formato ya fijado por `evals/check.py` (38 ficheros y 133 casos de precedente); el fixture de `evals/fixtures/project/` gana las entradas de memoria necesarias.
- **Estado**: borrador
- **Tiempo humano**: est. 1,0h · real —
- **Tiempo IA (ejec.)**: est. 0,07h · real —
- **Supervisión**: est. 0,02h (≈25 % IA) · real —
- **Previsión IA**: 25k in / 7k out tok · 0,28 €
- **Dependencias**: T-08
- **Tipo**: test
- **Archivos**: `evals/cases/agent-implementer.json`, `evals/cases/agent-evaluator.json`, `evals/fixtures/project/`
- **Verificación**: `python3 evals/check.py` → exit 0 (línea base de hoy: 38 ficheros · 133 casos · 0 errores; después: 133 + los nuevos) · `python3 -m pytest -q evals` → todos passed · `python3 evals/run.py --target agent:implementer` sin `claude` en PATH → **exit 2** con aviso (degrada, no falla) · lectura: ningún prompt nuevo trae datos corporativos (`check.py` lo vigila)

**Criterios de aceptación**
- [ ] `evals/check.py` sigue en **exit 0** con los casos nuevos (spec CA-13).
- [ ] Los casos nuevos tienen `expect.mentions` con el **ID de la entrada** de su área, no una frase vaga.
- [ ] Se mantiene la cobertura que `check.py` exige (≥ 2 positivos + ≥ 1 negativo por pieza) y los **ids únicos** en toda la suite.
- [ ] **Ni un dato corporativo** en los prompts nuevos (repo público).
- [ ] `run.py` sigue degradando a **exit 2** sin `claude` en PATH: la eval **no** se convierte en un gate que dependa de una clave.

**Subtareas**
- [ ] Añadir las entradas de memoria al fixture del proyecto de mentira.
- [ ] Escribir los casos (positivo con el ID esperado, negativo de área vecina).
- [ ] Comprobar los ids únicos en toda la suite.

**Notas**: `LES-011`: «la description es una promesa de activación, y una promesa se prueba, no se asume». Aquí la promesa que se prueba es la de la memoria.

### T-10 — `/doctor` puntúa la salud de la memoria

- **Descripción**: hoy `/doctor` da «Instalación sana» con **0** entradas de journal, **sin contar** las 31 curadas, **sin validar** el índice y **sin avisar** de que `CALIBRATION.md` lleva 15 días sin fila con 13 iniciativas cerradas detrás. Gana una sección de salud de memoria: entradas curadas por familia, estado del índice (válido / reconstruible / degradado), entradas de journal y antigüedad de la última fila de calibración.
- **Estado**: borrador
- **Tiempo humano**: est. 1,5h · real —
- **Tiempo IA (ejec.)**: est. 0,10h · real —
- **Supervisión**: est. 0,02h (≈25 % IA) · real —
- **Previsión IA**: 37k in / 11k out tok · 0,42 €
- **Dependencias**: T-03
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/doctor.py`, `agent-kits/shared/test_doctor.py`
- **Verificación**: `python3 agent-kits/shared/doctor.py | grep -i "memoria"` → líneas con las 31 curadas, el estado del índice, las entradas de journal y la antigüedad de `CALIBRATION.md` · `python3 agent-kits/shared/doctor.py` sobre un árbol con índice inválido → **no** imprime «Instalación sana» · `python3 -m pytest -q agent-kits/shared/test_doctor.py` → todos passed · `python3 agent-kits/shared/doctor.py` en un árbol sin `docs/knowledge/` → línea informativa, exit 0, sin ❌

**Criterios de aceptación**
- [ ] Con 31 curadas, 0 de journal e índice inválido, **no** dice «Instalación sana»; nombra las tres cosas (spec CA-14).
- [ ] Avisa cuando `CALIBRATION.md` lleva **> 14 días** sin fila (hoy: 15) y dice **cuántas iniciativas** se han cerrado desde entonces.
- [ ] Cada línea trae su **arreglo concreto**, como el resto de `/doctor`.
- [ ] Sin `docs/knowledge/`: línea **informativa** y exit 0 — un proyecto recién instalado no está roto por nacer sin memoria.
- [ ] Los avisos de memoria son **⚠️**, no ❌, salvo índice inválido: `/doctor` no se vuelve alarmista (si todo es rojo, la gente lo ignora).
- [ ] Sigue sin usar red y sigue siendo de **solo lectura**.

**Subtareas**
- [ ] Test RED con árboles de `tmp_path` para los cuatro estados.
- [ ] Función `_memoria(project)` al estilo del `_journal(project)` que ya existe.
- [ ] Enganchar en el veredicto y en la lista de secciones.

**Notas**: el `_journal(project)` actual ya informa de «carpeta sin entradas todavía» pero **no cambia el veredicto**; eso es exactamente lo que se corrige.

---

## Fase 4 — Captura episódica

**Estado**: borrador · **Estimado**: 7,0h · **Real**: — · **Coste est.**: 352 € · **Tokens est.**: 205.000

> Cierra el hueco **3** de `analysis.md` §1.4 y **revisa `ADR-010`**. Es la fase más cara, la de peor
> confianza y la única con un **contrato oficial sin verificar**: antes de arrancar hay que
> comprobar en la doc oficial si `UserPromptSubmit` trae `session_id` y **anotar la fecha**, como
> hizo `memory-health` con `SessionEnd`.

### T-11 — Hook `UserPromptSubmit`: log crudo no versionado con opt-out

- **Descripción**: hook nuevo que acumula el turno del usuario en `.claude/session-prompts-<session_id>.log`, **no versionado** (`*.log` ya está en `.gitignore`, verificado). Opt-out por etiqueta al estilo `<private>`: con la etiqueta puesta **el log no se toca** (ni mtime ni tamaño). Esto captura lo que hoy se pierde —las decisiones del usuario en la conversación— sin registrar cada `PostToolUse`, que es ruido y coste (decisión del usuario).
- **Estado**: borrador
- **Tiempo humano**: est. 2,5h · real —
- **Tiempo IA (ejec.)**: est. 0,15h · real —
- **Supervisión**: est. 0,04h (≈25 % IA) · real —
- **Previsión IA**: 55k in / 15k out tok · 0,60 €
- **Dependencias**: verificar el contrato oficial de `UserPromptSubmit` (¿llega `session_id`?)
- **Tipo**: devops
- **Archivos**: `hooks/user-prompt-capture.sh`, `hooks/hooks.json`, `tests/test_hooks_shell.py`
- **Verificación**:
  - `echo '{"hook_event_name":"UserPromptSubmit","session_id":"s1","prompt":"decidimos usar FTS5"}' | bash hooks/user-prompt-capture.sh; echo $?` → 0, y el turno aparece en el log
  - `git check-ignore -v .claude/session-prompts-s1.log` → una línea con la regla `*.log`
  - con `"prompt":"<private> mi clave es …"` → el log **no cambia** (mismo tamaño y mismo mtime antes y después)
  - `echo 'no es json' | bash hooks/user-prompt-capture.sh; echo $?` → 0 (nunca bloquea el turno)
  - `python3 -m pytest -q tests/test_hooks_shell.py` → todos passed
  - `python3 scripts/lint_plugin.py` → exit 0 (incluye el linter de `hooks.json`)

**Criterios de aceptación**
- [ ] El turno queda en el log, el fichero **no entra en git** y el hook sale **0** (spec CA-15).
- [ ] Con `<private>`, el log **no se toca**: mismo tamaño y mismo mtime (spec CA-16).
- [ ] Payload roto, sin `session_id`, sin `python3` o sin `.claude/` escribible → **exit 0** sin emitir nada. **Nunca bloquea un turno del usuario.**
- [ ] El log es **rotativo o acotado**: un turno gigantesco no puede llenar el disco (tope por fichero, declarado en el hook).
- [ ] **No** se registra ningún `PostToolUse`: no se añade ese evento a `hooks.json`.
- [ ] `hooks.json` sigue en modo `100644` y el linter de hooks sigue verde (`LES-012`).

**Subtareas**
- [ ] **Primero**: verificar el contrato oficial y anotar la fecha en el docstring del hook.
- [ ] Test RED de los cuatro casos (feliz, opt-out, payload roto, sin escritura).
- [ ] Escribir el hook y registrarlo en `hooks.json`.

**Notas**: privacidad en repo **público**: el log lleva texto del usuario, así que no versionado + opt-out + nada en tests con datos reales.

### T-12 — `SessionEnd` escribe él mismo `decisiones` y `pendientes`; `ADR-010` revisado

- **Descripción**: hoy `decisiones: []` y `pendientes: []` están vacías **siempre** en modo hook, y el `resumen` es el primer prompt del usuario recortado a 160 caracteres. El hook `SessionEnd` pasa a **escribir él mismo** la entrada del journal con `decisiones` y `pendientes` extraídas del log crudo de T-11. Esto **revisa `ADR-010`**: su restricción —«el contrato de `SessionEnd` ignora la salida de los hooks»— es **CIERTA y se conserva**; lo que cambia es la conclusión, que era demasiado fuerte: el hook no necesita *devolver* el resumen, **puede escribirlo**.
- **Estado**: borrador
- **Tiempo humano**: est. 2,5h · real —
- **Tiempo IA (ejec.)**: est. 0,16h · real —
- **Supervisión**: est. 0,04h (≈25 % IA) · real —
- **Previsión IA**: 60k in / 17k out tok · 0,67 €
- **Dependencias**: T-11
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/journal.py`, `hooks/session-journal.sh`, `agent-kits/shared/test_journal.py`, `docs/knowledge/adr/ADR-010-journal-memoria-de-sesion-determinista.md`
- **Verificación**:
  - con un log crudo poblado: `python3 agent-kits/shared/journal.py write --session-id s1 …` → la entrada trae `decisiones` y `pendientes` **no vacías**
  - repetir la misma orden con `--session-id s1` → **una sola** entrada (idempotente), no dos
  - con el log crudo vacío → `decisiones: []` **honesto** (no inventado) y exit 0
  - `python3 -m pytest -q agent-kits/shared/test_journal.py` → todos passed
  - lectura: `ADR-010` conserva su restricción como cierta y añade la revisión con fecha, en lugar de borrarla

**Criterios de aceptación**
- [ ] Con log crudo poblado, `decisiones` y `pendientes` salen **no vacías**; idempotente por `session_id` (spec CA-17).
- [ ] Con log crudo vacío, `decisiones: []` **sin inventar nada**: la degradación es honesta, no decorativa.
- [ ] El cierre de sesión **nunca se bloquea**: cualquier fallo cae a la entrada determinista de hoy con exit 0.
- [ ] `ADR-010` queda **revisado, no borrado**: la restricción del contrato sigue escrita como cierta y con su fecha; lo que se revisa es la conclusión (spec CA-20).
- [ ] La fila de `ADR-010` en `docs/knowledge/README.md` refleja el cambio, y `tests/test_knowledge_index.py` (T-04) sigue verde.

**Subtareas**
- [ ] Test RED de los tres casos (log poblado, log vacío, doble escritura).
- [ ] Extracción determinista del log crudo (sin modelo): decisiones marcadas y pendientes.
- [ ] Reescribir la sección de `ADR-010` con la revisión y su fecha.

**Notas**: el ADR **no** se pone `obsoleta`: sigue siendo doctrina en su parte cierta. Es exactamente el caso que la capa 2 (T-02) tiene que saber contar.

### T-13 — Resumen episódico por IA, opt-in y degradando siempre

- **Descripción**: extracción por IA de `decisiones`/`pendientes` **opt-in** vía `.claude/dev.json` → `sesion.resumen: true`, invocando el CLI en headless (`claude -p`) exactamente como ya hace `evals/run.py`. **Sin CLI, sin clave o con el opt-in apagado → degrada al journal determinista de hoy y nunca bloquea.**
- **Estado**: borrador
- **Tiempo humano**: est. 1,0h · real —
- **Tiempo IA (ejec.)**: est. 0,07h · real —
- **Supervisión**: est. 0,02h (≈25 % IA) · real —
- **Previsión IA**: 25k in / 7k out tok · 0,28 €
- **Dependencias**: T-12
- **Tipo**: devops
- **Archivos**: `hooks/session-journal.sh`, `agent-kits/shared/journal.py`, `agent-kits/shared/test_journal.py`
- **Verificación**:
  - `python3 -m pytest -q agent-kits/shared/test_journal.py -k resumen` → todos passed **con el subprocess mockeado** (aquí nunca se lanza `claude`)
  - sin `sesion.resumen` en `dev.json` → entrada determinista de hoy, exit 0
  - con `sesion.resumen: true` y `claude` **fuera** del PATH → entrada determinista de hoy, exit 0, aviso solo por stderr
  - con `dev.json` corrupto → entrada determinista de hoy, exit 0
  - `PATH= bash hooks/session-journal.sh < payload.json; echo $?` → 0

**Criterios de aceptación**
- [ ] Los **tres** casos de degradación (opt-in apagado · sin CLI · sin clave) dan el journal determinista de hoy con **exit 0** y sin bloquear el cierre (spec CA-18).
- [ ] Con el opt-in activo y el CLI disponible, `decisiones`/`pendientes` salen del resumen; si el JSON de vuelta no parsea, **degrada** en vez de escribir basura.
- [ ] Hay un **timeout** declarado en la llamada headless: una sesión no se queda colgada al cerrar.
- [ ] El test **no lanza `claude`**: subprocess mockeado, como `evals/test_evals.py`.
- [ ] Ningún test nuevo necesita red ni clave de API.

**Subtareas**
- [ ] Test RED de los tres caminos de degradación con el subprocess mockeado.
- [ ] Reutilizar el patrón de invocación de `evals/run.py` (no inventar otro).
- [ ] Timeout y captura de errores con `encoding="utf-8", errors="replace"` (`GOT-005`).

**Notas**: `ADR-010` decidió «sin resumen por IA»; esto no lo contradice: lo hace **opt-in** y lo escribe el hook, que es la parte que el ADR daba por imposible.

### T-14 — Promoción journal → candidata a lección por la puerta de `/retro`

- **Descripción**: **la bisagra entre las dos velocidades, y lo que `claude-mem` no tiene.** Una entrada de journal cuyo patrón se repite entre sesiones se convierte en **candidata a lección** y entra por la puerta de `/retro` con `estado: propuesta` — no como lección aceptada: la curación sigue siendo la revisión de dos lentes o el usuario.
- **Estado**: borrador
- **Tiempo humano**: est. 1,0h · real —
- **Tiempo IA (ejec.)**: est. 0,05h · real —
- **Supervisión**: est. 0,01h (≈25 % IA) · real —
- **Previsión IA**: 20k in / 6k out tok · 0,23 €
- **Dependencias**: T-12
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/journal.py`, `commands/retro.md`, `agent-kits/shared/test_journal.py`
- **Verificación**: `python3 agent-kits/shared/journal.py candidatas --root <fixture>` → lista las candidatas con `estado: propuesta`, exit 0 · con un patrón presente en **1** sola entrada → **no** se propone (el umbral es ≥ 2) · con el patrón en **≥ 2** entradas → se propone una vez, no una por entrada · `python3 -m pytest -q agent-kits/shared/test_journal.py -k candidatas` → todos passed · lectura: `commands/retro.md` describe la puerta y dice que la candidata nace `propuesta`

**Criterios de aceptación**
- [ ] Un patrón en **≥ 2** entradas de journal aparece como candidata con `estado: propuesta` (spec CA-19).
- [ ] Un patrón en **1** entrada **no** se propone: el umbral está escrito y probado.
- [ ] Una candidata **nunca** nace `aceptada`: la puerta de curación no se puede saltar.
- [ ] La candidata trae su **evidencia** (qué entradas de journal la sostienen), como cualquier entrada de `docs/knowledge/`.
- [ ] Sin journal o con una sola entrada: **0 candidatas y exit 0**, sin ruido.

**Subtareas**
- [ ] Test RED del umbral (1 vs 2 entradas) y de la deduplicación.
- [ ] Subcomando `candidatas` en `journal.py`.
- [ ] Enganchar en la salida de `/retro` como propuesta, no como escritura automática.

**Notas**: esta tarea es la razón por la que la captura sin filtro no hace falta: se captura poco y se **asciende** lo que se repite.

---

## Fase 5 — Que la doctrina viaje

**Estado**: borrador · **Estimado**: 3,0h · **Real**: — · **Coste est.**: 151 € · **Tokens est.**: 115.000

> Cierra el hueco **4** de `analysis.md` §1.4: «viaja el método y se queda el conocimiento».

### T-15 — Doctrina del plugin como assets, separada de la memoria del proyecto

- **Descripción**: separar dos cosas hoy mezcladas. **Memoria del proyecto** (`docs/knowledge/` del consumidor): sus decisiones, sus trampas, sus lecciones — **nace vacía, y eso es correcto**. **Doctrina del plugin**: las lecciones ciertas para cualquier proyecto que use estos agentes — las **9** de área «Estimación / calibración» (`LES-001…009`) son el caso obvio — que viajan como **assets del plugin** y son el fondo con el que el `evaluator` estima el primer día. Hay que **deshacer una pérdida real**: `LES-007/008/009` estaban garantizadas dentro del prompt del `evaluator` y se convirtieron en punteros a ficheros que el consumidor no tiene.
- **Estado**: borrador
- **Tiempo humano**: est. 2,0h · real —
- **Tiempo IA (ejec.)**: est. 0,16h · real —
- **Supervisión**: est. 0,04h (≈25 % IA) · real —
- **Previsión IA**: 60k in / 17k out tok · 0,67 €
- **Dependencias**: T-01
- **Tipo**: docs
- **Archivos**: `agent-kits/evaluator/assets/doctrina/`, `scripts/export-skills.py`, `tests/test_doctrina_viaja.py`
- **Verificación**: `ls agent-kits/evaluator/assets/doctrina/ | wc -l` → 9 · `python3 -m pytest -q tests/test_doctrina_viaja.py` → todos passed (una copia, o dos copias comparadas byte a byte) · `python3 scripts/export-skills.py --check` → exit 0 y la doctrina figura en lo que viaja · `python3 scripts/lint_plugin.py` → exit 0

**Criterios de aceptación**
- [ ] Las **9** lecciones de estimación están disponibles como doctrina del plugin.
- [ ] La memoria del proyecto **sigue naciendo vacía**: nada se copia al `docs/knowledge/` del consumidor al instalar.
- [ ] El criterio de qué es doctrina está **escrito** («¿es cierta para cualquier proyecto que use estos agentes?») y aplicado entrada por entrada.
- [ ] **Una sola copia**; si la copia es inevitable, un test la compara **byte a byte** (el patrón que el repo ya usa con las copias manuales).
- [ ] El paquete portable (`export-skills.py`) declara qué viaja y qué no, y su `--check` sigue verde.

**Subtareas**
- [ ] Decidir entrada por entrada cuáles de las 9 son doctrina universal.
- [ ] Colocar los assets y atarlos con test.
- [ ] Actualizar qué viaja en el paquete portable y su README ES/EN.

**Notas**: `analysis.md` §1.4-4 lo llama «se cambió una garantía por una intención». Aquí se deshace **sin volver a meter prosa en los prompts** — eso lo ata T-16.

### T-16 — El `evaluator` estima con ese fondo sin engordar su prompt

- **Descripción**: `knowledge-find.py --doctrina` lee los assets del plugin (y no la memoria del proyecto), y el `evaluator` la consulta el primer día. La restricción dura: **sin volver a meter prosa en los prompts**, atada a `wc -c agents/evaluator.md` ≤ **15.513 bytes** (el valor de hoy).
- **Estado**: borrador
- **Tiempo humano**: est. 1,0h · real —
- **Tiempo IA (ejec.)**: est. 0,08h · real —
- **Supervisión**: est. 0,02h (≈25 % IA) · real —
- **Previsión IA**: 30k in / 8k out tok · 0,32 €
- **Dependencias**: T-15
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/knowledge-find.py`, `agents/evaluator.md`, `tests/test_doctrina_viaja.py`
- **Verificación**:
  - en un árbol **sin** `docs/knowledge/`: `python3 agent-kits/shared/knowledge-find.py --doctrina --area estimacion` → las **9** lecciones, exit 0
  - en el mismo árbol: `python3 agent-kits/shared/knowledge-find.py --area estimacion` → **0 aciertos**, exit 0
  - `wc -c agents/evaluator.md` → ≤ 15.513
  - `python3 evals/check.py` → exit 0 (el caso literal de `agent:evaluator` sigue atado a su `description` real)
  - `python3 -m pytest -q` → ≥ 1.175 passed

**Criterios de aceptación**
- [ ] `--doctrina --area estimacion` devuelve las **9** lecciones en un proyecto sin memoria propia, exit 0; y sin `--doctrina`, **0 aciertos** con exit 0 (spec CA-21).
- [ ] `wc -c agents/evaluator.md` **no supera los 15.513 bytes de hoy** (spec CA-22): la garantía vuelve **sin** prosa nueva en el prompt.
- [ ] La doctrina y la memoria del proyecto **no se mezclan** en la misma salida sin distinguirse: cada acierto dice de dónde viene.
- [ ] El caso literal de `agent:evaluator` en `evals/` sigue atado a la `description` real (`check.py` regla 4).

**Subtareas**
- [ ] Bandera `--doctrina` con localización del asset por `CLAUDE_PLUGIN_ROOT` + `find` (regla 5).
- [ ] Sustituir el puntero del prompt por la invocación, sin añadir prosa.
- [ ] Test del tope de bytes del prompt.

**Notas**: si el prompt tuviera que crecer, la tarea **falla** su criterio: es la restricción que hace que esto no sea volver atrás.

---

## Fase 6 — Cerrar el bucle

**Estado**: borrador · **Estimado**: 3,0h · **Real**: — · **Coste est.**: 151 € · **Tokens est.**: 145.000

> **Va al final por dependencias, pero el criterio de éxito de la spec NO se cumple sin ella**
> (CA-25). `analysis.md` la declara **condición previa**: «mientras la tubería que convierte
> experiencia en lección esté parada, reforzar la recuperación es afilar un grifo sin agua». Hoy:
> **15 días parado, 13 iniciativas cerradas** después de la última fila de `CALIBRATION.md`. Parar
> aquí es entrega **incompleta**, no «al 83 %».

### T-17 — `/retro` se dispara al cerrar una iniciativa

- **Descripción**: que `/retro` deje de ser «un comando que alguien recuerda». Al cerrar una iniciativa (plan `completado`), la puerta de cierre **exige** la retro y su fila en `CALIBRATION.md` — el mismo patrón que el repo ya usa con `qa-gate` y `ledger-lint`: una puerta, no un aviso ignorable (`LES-012`: «un aviso que se puede ignorar se ignorará»).
- **Estado**: borrador
- **Tiempo humano**: est. 1,5h · real —
- **Tiempo IA (ejec.)**: est. 0,15h · real —
- **Supervisión**: est. 0,04h (≈25 % IA) · real —
- **Previsión IA**: 55k in / 17k out tok · 0,64 €
- **Dependencias**: T-10, T-14
- **Tipo**: docs
- **Archivos**: `commands/retro.md`, `commands/dev-cycle.md`, `agent-kits/shared/doctor.py`
- **Verificación**: `python3 agent-kits/shared/doctor.py | grep -i "calibrac"` → avisa de las iniciativas cerradas sin fila (hoy: 13, 15 días) · lectura: `commands/dev-cycle.md` describe la retro como **puerta** del cierre de iniciativa, con el comando exacto · `python3 evals/check.py` → exit 0 (el caso literal de `command:retro` sigue atado a su `description`) · `python3 scripts/lint_plugin.py` → exit 0

**Criterios de aceptación**
- [ ] El cierre de iniciativa **exige** la retro y su fila en `CALIBRATION.md` (spec CA-23).
- [ ] Es una **puerta**, no un aviso: el ritual de cierre no se puede declarar completo sin ella.
- [ ] `/doctor` cuenta cuántas iniciativas cerradas están sin fila y desde cuándo.
- [ ] La `description` de `/retro` y su caso literal en `evals/` siguen coherentes (`check.py` regla 4).
- [ ] No se automatiza **escribir** la retro: se automatiza **exigirla**. Las causas de desviación las escribe quien las conoce.

**Subtareas**
- [ ] Añadir la retro al ritual de cierre de `/dev-cycle`.
- [ ] Contar en `/doctor` las cerradas sin fila.
- [ ] Ajustar `commands/retro.md` para consumir las candidatas de T-14.

**Notas**: esta tarea es la que hace que las horas **humanas** de este presupuesto dejen de ser una estimación sin validar: sin retro, `CALIBRATION.md` no gana su primera fila con horas humanas reales.

### T-18 — Doc ES/EN y las entradas de `docs/knowledge/` que salen de aquí

- **Descripción**: cerrar la iniciativa con su documentación y su memoria: la regla nueva en `docs/CONVENTIONS.md` **y su espejo EN**, un ADR de las tres capas (fuente de verdad en git, índice como caché, grafo curado en vez de cronología), la lección que salga del ciclo, sus filas en el índice de `docs/knowledge/README.md`, y las transiciones de estado de los artefactos de esta carpeta.
- **Estado**: borrador
- **Tiempo humano**: est. 1,5h · real —
- **Tiempo IA (ejec.)**: est. 0,15h · real —
- **Supervisión**: est. 0,04h (≈25 % IA) · real —
- **Previsión IA**: 55k in / 18k out tok · 0,67 €
- **Dependencias**: T-17
- **Tipo**: docs
- **Archivos**: `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `docs/knowledge/README.md`, `docs/knowledge/adr/`, `docs/knowledge/lessons/`, `docs/roadmap/2026-09-04-memory-retrieval/spec.md`, `docs/roadmap/2026-09-04-memory-retrieval/evaluation.md`, `docs/roadmap/2026-09-04-memory-retrieval/improvement-plan.md`, `docs/roadmap/README.md`
- **Verificación**:
  - `python3 -m pytest -q tests/test_knowledge_index.py` → todos passed (las entradas nuevas tienen fila y «Área»)
  - `python3 -m pytest -q tests/test_roadmap_index.py` → todos passed (la fila de la iniciativa sigue **dentro** de la tabla)
  - `diff <(grep -c "^#" docs/CONVENTIONS.md) <(grep -c "^#" docs/en/CONVENTIONS.md)` → misma estructura de secciones en los dos espejos
  - `python3 -m pytest -q` → ≥ 1.175 passed
  - `python3 agent-kits/shared/ledger-lint.py docs/roadmap/2026-09-04-memory-retrieval/tasks.md` → exit 0
  - lectura: `spec.md` pasa a `estado: implementada` y `evaluation.md`/`improvement-plan.md` a `completado` solo cuando todas las tareas están cerradas

**Criterios de aceptación**
- [ ] La regla nueva está en `docs/CONVENTIONS.md` **y** en `docs/en/CONVENTIONS.md` (spec CA-24). *Alcance verificado:* `docs/en/` espeja solo los 5 documentos de producto — **no** el roadmap —, así que estos cuatro artefactos no llevan espejo EN, y eso no es una omisión.
- [ ] Las entradas nuevas de `docs/knowledge/` tienen **su fila con «Área»** en el índice, en el mismo cambio (regla del índice) y con T-04 verde.
- [ ] La fila de la iniciativa está **dentro** de la tabla de `docs/roadmap/README.md` y `tests/test_roadmap_index.py` lo confirma.
- [ ] Los estados de `spec.md`, `evaluation.md`, `improvement-plan.md` y de este ledger se actualizan al cerrar, no antes.
- [ ] **`CHANGELOG*.md` no se toca a mano**: lo genera la skill `changelog-sync` desde este ledger cerrado.
- [ ] El ADR nuevo dice **qué se descartó y por qué** (embeddings, capturar todo, retirar el journal), no solo lo elegido.

**Subtareas**
- [ ] ADR de las tres capas con las alternativas descartadas.
- [ ] Lección del ciclo (con evidencia, no impresión).
- [ ] Espejo ES/EN de la regla y filas del índice.
- [ ] Transiciones de estado y fila del roadmap con el resultado real.

**Notas**: el campo `- **Changelog**:` de cada tarea lo escribe **quien la cierra** (`ADR-012`); este ledger nace sin él a propósito.

---

## Puerta de revisión de dos lentes (transversal, línea de presupuesto propia)

**Estado**: borrador · **Estimado**: 4,0h humanas · 0,54h IA · **Coste est.**: 202 € · **Tokens est.**: 260.000

No es una fase ni una tarea: es la **línea de presupuesto aparte** que `CALIBRATION.md` obliga a poner
(`LES-001`, `LES-009`: «el coste está en la revisión, no en escribir» — en las 4 vías rápidas medidas
encontró 1-10 hallazgos cada vez, y dos habrían roto una garantía del producto). Son el **12 %** del
presupuesto base y el **21 %** de los tokens, y por eso no se reparte por fases fingiendo que es gratis.

Al final de **cada** fase, en este orden:

1. `python3 agent-kits/shared/scope-check.py docs/roadmap/2026-09-04-memory-retrieval` → exit 0
   (ningún fichero fuera del alcance declarado en los campos `- **Archivos**:` de este ledger).
2. Revisión adversarial (skill `adversarial-review`): Lente A (conformidad con spec/plan/constitución,
   ✓/✗ por criterio) + Lente B (defectos de corrección), más las lentes C/D si
   `review-lens-select.py` las activa. **Bucle acotado a 3 intentos**, rebate con evidencia.
3. Traza en este ledger como `## Revisión de dos lentes — intento N`, con los gaps por tarea (así los
   recoge `task-brief.py` en el redespacho).
4. Puertas mecánicas: `ledger-lint.py` (exit 0) · `pytest -q` (**≥ 1.175 passed**) ·
   `lint_plugin.py` (exit 0) · `evals/check.py` (exit 0).

**Presupuesto por fase** (orientativo, suma 4,0 h): F1 1,2 h · F2 0,6 h · F3 0,5 h · F4 0,9 h ·
F5 0,4 h · F6 0,4 h. La Fase 1 y la Fase 4 se llevan la mitad porque son las que traen código nuevo
con degradaciones, que es donde las lentes han encontrado los críticos en este repo.
