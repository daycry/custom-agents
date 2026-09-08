---
tasks: memory-retrieval
estado: completado        # borrador | en-progreso | completado | cancelado — 21 tareas cerradas el 2026-09-08 (18 del plan + T-19/T-20/T-21, cierres de las tres revisiones de dos lentes); cierre declarado el 2026-09-08 tras pasar la puerta de retro (retro.md + fila en CALIBRATION.md)
creado: 2026-09-04
actualizado: 2026-09-08
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
| **Estado** | completado |
| **Fecha** | 2026-09-04 |
| **Plan** | [`improvement-plan.md`](./improvement-plan.md) |
| **Spec** | [`spec.md`](./spec.md) |
| **Evaluación** | [`evaluation.md`](./evaluation.md) |
| **Análisis de origen** | [`analysis.md`](./analysis.md) |
| **Diseño** | n/a |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del plan. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador SDD externo— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

> **Fases 1-3 completadas el 2026-09-07 (T-01…T-10, rama `feature/pendiente`)**, más **T-19** (cierre de
> los 12 gaps del intento 1 de la revisión de dos lentes sobre esas fases, mismo día). **Fase 4 completada
> el 2026-09-08 (T-11…T-14)**, con el contrato oficial de `UserPromptSubmit` verificado y fechado antes de
> arrancar; su revisión de dos lentes (intento 1: A+B+C, 16 gaps → 15 corregidos en **T-20** y 1 delegado
> a T-18 con alcance ampliado) se traza al final de este ledger. **Fases 5 y 6 implementadas el 2026-09-08**
> (T-15…T-18); su revisión de dos lentes (intento 1: A+B+D, 10 gaps → 10 corregidos en **T-21**, 0 rebatidos)
> se traza al final. **Ledger cerrado el 2026-09-08**: evaluación y plan `completado`; la spec pasó a
> `implementada` el 2026-09-08 al abrir la puerta de retro (`retro.md` + fila en `CALIBRATION.md` — la propia
> iniciativa fue la primera a la que se le exigió el paso 8 del ritual que ella misma introdujo). El campo `- **Changelog**:` lo escribe quien CIERRA cada tarea (`ADR-012`): las
> veintiuna lo llevan. Al entrar este ledger (y el de `sin-motor-externo`) en el corpus de cerrados, las **cifras
> vivas** de `changelog-sync` se re-midieron con `--medicion` (SKILL, `references/medicion-escalera.md`, ADR-012 e
> índice: 17 ledgers / 98 tareas, `changelog` 35, techo 539) — el mismo paso que dio `sin-motor-externo` T-05;
> por eso esos cuatro ficheros aparecen en el commit de cierre sin estar en ningún `Archivos` de este plan. Las horas IA «reales» van marcadas `(estimado)`: el
> `usage-meter` no puede leer la transcripción en este entorno.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — Recuperación | 4 | 4 | 100% | 0 / 9,0h | 0,60 (est.) / 0,51h | 0,16 (est.) / 0,13h | n/d / 245.000 |
| Fase 2 — Llegada | 3 | 3 | 100% | 0 / 4,0h | 0,46 (est.) / 0,31h | 0,12 (est.) / 0,08h | n/d / 150.000 |
| Fase 3 — Prueba de que se recorre | 4 | 4 | 100% | 0 / 4,0h | 0,76 (est.) / 0,27h | 0,20 (est.) / 0,07h | n/d / 128.000 |
| Fase 4 — Captura episódica | 5 | 5 | 100% | 0 / 7,0h | 1,20 (est.) / 0,43h | 0,30 (est.) / 0,11h | n/d / 205.000 |
| Fase 5 — Que la doctrina viaje | 2 | 2 | 100% | 0 / 3,0h | 0,35 (est.) / 0,24h | 0,09 (est.) / 0,06h | n/d / 115.000 |
| Fase 6 — Cerrar el bucle | 3 | 3 | 100% | 0 / 3,0h | 0,95 (est.) / 0,30h | 0,24 (est.) / 0,08h | n/d / 145.000 |
| Revisión de dos lentes (transversal, línea propia) | — | — | — | 0 / 4,0h | 0 / 0,54h | 0 / 0,13h | 0 / 260.000 |
| **TOTAL** | **21** | **21** | **100%** | **0 / 34,0h** | **4,32 (est.) / 2,60h** | **1,11 (est.) / 0,66h** | **n/d / 1.248.000** |

> **Horas → Jira.** El worklog que imputa `jira-sync` al completar cada tarea es **Tiempo IA (ejec.) + Supervisión** (real; o estimación si no hay real), topado a la jornada configurada (8 h). Ver `skills/jira-sync/SKILL.md`.
>
> **T-19** (cierre de gaps del intento 1 sobre F1-3), **T-20** (ídem sobre F4) y **T-21** (ídem sobre F5-6) no estaban en el plan:
> cuentan en la fase donde viven con estimación propia, y su coste es el de la **línea transversal de
> revisión** (0,54h IA presupuestadas), no de las fases — por eso el «Estimado» de las fases y el TOTAL de
> tareas estimadas no cambian. Con T-20 el real IA de la iniciativa (3,02h est.) supera el estimado (2,60h):
> la revisión de F4 encontró 16 gaps, 6 de ellos Important/Critical — la línea transversal estaba bien
> presupuestada en horas (0,90h para F4 frente a 0,45h gastadas), lo que se subestimó fue la implementación.
>
> Las horas IA salen de **tokens ÷ 479.326 tok/h** (mediana medida de 5 muestras, `CALIBRATION.md`), no del default no calibrado de 300.000. La supervisión es el **25 %** de las horas IA (`rates.json` `ratioSupervision`); el total exacto sería 0,65 h y la suma por tarea da **0,66 h** por redondeo — se usa 0,66 h para que plan y ledger digan lo mismo.

---

## Fase 1 — Recuperación

**Estado**: completado · **Estimado**: 9,0h · **Real**: 0h humanas · 0,60h IA (estimado) + 0,16h supervisión (estimado) · **Coste est.**: 452 € · **Tokens est.**: 245.000

> Cierra los huecos **2** («no hay búsqueda») y **5** («el índice no lo vigila nada») de
> `analysis.md` §1.4. No depende de nada, y es lo que más rinde: por eso va primera.

### T-01 — Capa 1 de `knowledge-find.py`: consulta → aciertos compactos

- **Descripción**: script nuevo `agent-kits/shared/knowledge-find.py` que sustituye «lee el índice y decide» por «pregunta y recibe». Devuelve **una línea por acierto** con el formato `ID · estado · área · titular · ruta` (~25 tokens), ordenada por relevancia y con el **`estado` DELANTE** para que el lector sepa si tiene doctrina (`aceptada`), indicio (`propuesta`) u obsoleta con sucesor. Admite `--area`, `--tipo`, `--limit`, `--json` y consulta libre posicional. El área se casa **normalizada** (minúsculas, sin acentos, por token), no por comparación exacta: medido hoy, la columna «Área» tiene **21 valores distintos para 31 entradas**, casi todos singleton.
- **Estado**: completado
- **Tiempo humano**: est. 3,0h · real 0h (sin intervención humana en la ejecución)
- **Tiempo IA (ejec.)**: est. 0,17h · real 0,20h (estimado: el usage-meter no lee la transcripción en este entorno)
- **Supervisión**: est. 0,04h (≈25 % IA) · real 0,05h (estimado)
- **Previsión IA**: 65k in / 20k out tok · 0,76 €
- **Dependencias**: ninguna
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/knowledge-find.py`, `tests/test_knowledge_find.py`, `tests/test_console_encoding.py` (añadido al cerrar: la suite exige declarar en su tabla MODOS el modo de arranque de cada script nuevo con símbolos, GOT-005)
- **Changelog**: Los agentes pueden consultar la memoria técnica del proyecto con una orden en vez de leer el índice entero: cada acierto es una línea compacta con el estado delante, y el área se casa sin acentos ni mayúsculas.
- **Verificación** (ejecutada 2026-09-07):
  - `RED: tests/test_knowledge_find.py falló con FileNotFoundError: [Errno 2] No such file or directory: '/work/ca/agent-kits/shared/knowledge-find.py' (1 error during collection) · 2026-09-07`; GREEN después → `15 passed in 1.21s`.
  - `python3 agent-kits/shared/knowledge-find.py --area estimacion --json` → `"indice": …`, `total: 9`, ids `LES-001…LES-009` (todas con `area: Estimación / calibración`), exit 0. `grep -c "Estimación / calibración" docs/knowledge/README.md` → 9. La salida humana equivalente (`--area estimacion`) → **9 líneas · 1.034 caracteres** (≤ 1.200), exit 0.
  - `python3 agent-kits/shared/knowledge-find.py "consola windows cp1252" --limit 5` → 4 líneas, la primera `GOT-005 · aceptada · Scripts / consola y codificación · imprimir `✅ ⚠️ ❌` sin reconfigurar… · gotchas/GOT-005-…`; las 4 ≤ 120 caracteres; exit 0. Bajo `PYTHONIOENCODING=cp1252` la misma orden imprime los símbolos íntegros y sale 0.
  - `python3 agent-kits/shared/knowledge-find.py --area no-existe-esta-area | wc -c` → `0`, exit 0.
  - `python3 agent-kits/shared/knowledge-find.py --limit 0` → 32 líneas (una por entrada del corpus de hoy: 12 ADR · 6 gotchas · 14 lecciones), todas ≤ 120 caracteres y con 4 separadores ` · `.
  - `python3 -m pytest -q tests/test_console_encoding.py` → `281 passed` (el script entra en `SCRIPTS` por sus símbolos y declara su modo en `MODOS`) · `python3 scripts/lint_plugin.py` → `lint_plugin: 9 agentes · 0 errores · 3 avisos`, exit 0 (los 3 avisos son los nombres genéricos preexistentes).
  - Nota medida: el corpus tiene hoy **32** entradas (la spec y este ledger decían 31: `GOT-006` se añadió el 2026-09-04, después del análisis). La ruta de la línea humana casi siempre se abrevia a `carpeta/ID-…` porque los nombres de fichero del corpus miden 41-100 caracteres y con la ruta completa el titular quedaría en 6-28 caracteres; el JSON trae siempre la ruta completa y el detalle se abre por ID (`--show`, T-03).

**Criterios de aceptación**
- [x] `--area estimacion --json` devuelve las **9** entradas de esa área en **≤ 300 tokens (≤ 1.200 caracteres)** con **exit 0** (spec CA-01). Nota medida: las **6** que menciona `analysis.md` §1.5 son las *no citadas*, no las del área — no se confunden.
- [x] Cada acierto es **≤ 30 tokens (≤ 120 caracteres)** y trae `ID · estado · área · titular · ruta` **en ese orden**, con el `estado` delante (spec CA-02).
- [x] Una consulta libre ordena por relevancia: `"consola windows cp1252"` pone `GOT-005` primero.
- [x] Sin `docs/knowledge/` o sin aciertos: **0 líneas y exit 0** — ni una línea de relleno para decir que no hay nada (no gastar contexto).
- [x] El área se casa normalizada: `--area estimacion` encuentra «Estimación / calibración».
- [x] Reconfiguración UTF-8 de `stdin`/`stdout`/`stderr` al arrancar (`GOT-005`), como los otros 28 scripts del repo.

**Subtareas**
- [x] Escribir primero el test que afirma el formato y el tope por acierto (RED), como manda la skill `tdd` si `dev.json` la trae activa.
- [x] Parsear el índice `docs/knowledge/README.md` (tabla de 31 filas) y el frontmatter de cada entrada.
- [x] Normalizar área/tipo y ordenar por relevancia.
- [x] Salida humana y `--json`; exit codes documentados en el docstring.

**Notas**: la salida `--json` es la que consumirán `task-brief.py` (T-05) y `session-context.sh` (T-06): su esquema es contrato, y cambiarlo después rompe dos consumidores.

### T-02 — Capa 2: `--related <ID>` con grafo curado

- **Descripción**: segunda capa de recuperación. `--related <ID>` devuelve el **grafo curado** de una entrada: ADR sucesor/sustituido, entradas de la **misma iniciativa** y entradas de la **misma área**. Sustituye deliberadamente la `timeline` de `claude-mem` («qué pasó cerca en el tiempo»): un grafo de sustitución y área es mejor información al mismo coste de tokens.
- **Estado**: completado
- **Tiempo humano**: est. 2,0h · real 0h (sin intervención humana en la ejecución)
- **Tiempo IA (ejec.)**: est. 0,11h · real 0,10h (estimado: el usage-meter no lee la transcripción en este entorno)
- **Supervisión**: est. 0,03h (≈25 % IA) · real 0,03h (estimado)
- **Previsión IA**: 40k in / 12k out tok · 0,46 €
- **Dependencias**: T-01
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/knowledge-find.py`, `tests/test_knowledge_find.py`
- **Changelog**: Desde cualquier entrada de la memoria técnica se puede pedir su grafo curado (qué la sustituyó o a qué sustituye, qué más salió de la misma iniciativa y qué comparte área), en vez de una lista cronológica.
- **Verificación** (ejecutada 2026-09-07):
  - `RED: tests/test_knowledge_find.py -k related falló con knowledge-find.py: error: unrecognized arguments: --related (6 failed, 1 passed) · 2026-09-07`; GREEN después → `python3 -m pytest -q tests/test_knowledge_find.py -k related` → `13 passed, 15 deselected`, y el fichero completo `28 passed`.
  - `python3 agent-kits/shared/knowledge-find.py --related ADR-010` → **≤ 1.600 caracteres** (483 al cerrar T-02; **452** re-medido el 2026-09-07 al cerrar T-19: el titular de una línea depende del corpus del día), exit 0, tres grupos etiquetados en este orden: `Sucesión:` → `(ninguna)` · `Misma iniciativa (memory-health):` → `(ninguna)` · `Misma área (Memoria técnica / hooks):` → `ADR-006 · aceptada · Memoria técnica / lectura-escritura · …` y `ADR-007 · aceptada · Hooks / implementer · …` (comparte «memoria técnica» con el uno y «hooks» con el otro). Ninguna línea empieza por fecha ni menciona cronología. `--related LES-001` (el área más poblada, 9 entradas) → ≤ 1.600 (1.281 al cerrar T-02; **1.184** re-medido al cerrar T-19).
  - `python3 agent-kits/shared/knowledge-find.py --related ID-INEXISTENTE` → stdout vacío, una línea en stderr (`knowledge-find: no hay ninguna entrada con ID `ID-INEXISTENTE` en …/docs/knowledge`), **exit 1**.
  - Sucesión probada con el corpus sintético de `tmp_path` (el real no tiene hoy ninguna entrada `obsoleta`): `ADR-002` obsoleta → `sustituida por → ADR-003 · aceptada · …`; `ADR-003` → `sustituye a → ADR-002 · obsoleta · …`; la relación se deduce también desde el otro extremo (si solo el sucesor declara `sustituye:`), y del ID citado en el `estado` de una obsoleta. Relaciones leídas del frontmatter (`sucesor`/`sustituye` y sinónimos; `iniciativa`) y de la columna «Fuente» del índice (`<fecha>-<slug>/tasks.md` → slug).
  - Tope: `RELATED_TOPE_CHARS = 1600` con test (40 lecciones de la misma área → 1.600 caracteres o menos y una línea `… y N más`).

**Criterios de aceptación**
- [x] `--related ADR-010` devuelve el grafo curado en **≤ 400 tokens (≤ 1.600 caracteres)** con **exit 0** (spec CA-03).
- [x] Las tres relaciones salen **etiquetadas y separadas** (sucesión · iniciativa · área), no como una lista plana.
- [x] Una entrada `obsoleta` muestra su **sucesor**; una `aceptada` que sustituyó a otra muestra a **quién sustituyó**.
- [x] **No hay salida cronológica**: ningún «qué pasó cerca en el tiempo». Es una decisión de diseño, no una omisión.
- [x] ID inexistente → **exit 1** con una línea en stderr (error de uso, no degradación).

**Subtareas**
- [x] Test RED con un corpus de `tmp_path` que tenga un ADR sustituido y un sucesor.
- [x] Extraer las relaciones del frontmatter y de la columna «Fuente» del índice.
- [x] Agrupar y topar la salida.

**Notas**: `ADR-010` es el caso de prueba natural porque esta misma iniciativa lo **revisa** (T-12), así que el grafo tiene que saber contarlo.

### T-03 — Capa 3 (`--show`) e índice SQLite FTS5 reconstruible

- **Descripción**: tercera capa (`--show <ID>` → la entrada completa) y el índice de búsqueda: **SQLite FTS5 en `.claude/`, no versionado y RECONSTRUIBLE desde los ficheros**. El índice guarda el hash del corpus; si falta, está corrupto o el hash no cuadra → se reconstruye; si no se puede reconstruir (`.claude/` de solo lectura, `sqlite3` sin FTS5) → **recorrido plano** de los ficheros con los mismos aciertos. **Nunca sale con código ≠ 0 por culpa del índice.** Aquí está la diferencia estructural con `claude-mem`: para ellos la base **ES** el almacén (base corrupta = memoria perdida y nada revisable); para nosotros es una **caché**. Cero dependencias: `sqlite3` es stdlib.
- **Estado**: completado
- **Tiempo humano**: est. 2,5h · real 0h (sin intervención humana en la ejecución)
- **Tiempo IA (ejec.)**: est. 0,15h · real 0,20h (estimado: el usage-meter no lee la transcripción en este entorno)
- **Supervisión**: est. 0,04h (≈25 % IA) · real 0,05h (estimado)
- **Previsión IA**: 55k in / 15k out tok · 0,60 €
- **Dependencias**: T-01
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/knowledge-find.py`, `tests/test_knowledge_find.py`, `.gitignore`
- **Changelog**: La memoria técnica se puede abrir entera por su ID, y las consultas van sobre un índice de texto completo en `.claude/` que se reconstruye solo cuando el corpus cambia; si el índice no se puede usar, la consulta responde igual leyendo los ficheros.
- **Verificación** (ejecutada 2026-09-07):
  - `RED: tests/test_knowledge_find.py falló con knowledge-find.py: error: unrecognized arguments: --show y AttributeError: module 'knowledge_find' has no attribute 'INDICE_NOMBRE' (26 failed, 29 passed) · 2026-09-07`; GREEN después → `python3 -m pytest -q tests/test_knowledge_find.py` → **`55 passed in 4.84s`**.
  - `python3 agent-kits/shared/knowledge-find.py --show ADR-012 | wc -c` → `10704` bytes = **10.512 caracteres** (≤ 10.800; el fichero creció desde los 10.449 de la spec), byte a byte el contenido del fichero, exit 0.
  - `python3 agent-kits/shared/knowledge-find.py --show NO-EXISTE` → stdout vacío, stderr `knowledge-find: no hay ninguna entrada con ID `NO-EXISTE` en /work/ca/docs/knowledge`, **exit 1**.
  - `rm -f .claude/knowledge-index.sqlite && python3 agent-kits/shared/knowledge-find.py --area estimacion --json` → `"indice": "construido"`, `total: 9`, exit 0 · la misma orden otra vez → `"indice": "cache"`, 9 · `printf 'basura' > .claude/knowledge-index.sqlite && …` → `"indice": "reconstruido"`, 9, exit 0 · `--no-index` → `"indice": "degradado"`, `"indice_motivo": "--no-index"`, 9.
  - `python3 -c "import sqlite3; sqlite3.connect(':memory:').execute('CREATE VIRTUAL TABLE t USING fts5(x)')"` → sin excepción (SQLite 3.45.1, Python 3.11).
  - `git check-ignore -v .claude/knowledge-index.sqlite` → `.gitignore:62:.claude/knowledge-index.sqlite	.claude/knowledge-index.sqlite` (una línea; también `.claude/knowledge-index.sqlite.*` para el temporal del `os.replace`).
  - Degradaciones probadas en `tmp_path`: `.claude` que es un FICHERO (falla también como root, no depende de `chmod`) → `"indice": "degradado"` con motivo, **mismos aciertos y mismas líneas** que con índice, exit 0 y stderr vacío · `fts5_disponible()` forzada a `False` → `degradado` con motivo `sqlite3 sin FTS5`, mismos aciertos, y no queda ningún índice a medias · sin `docs/knowledge/` → no se crea índice. Identidad índice ↔ plano afirmada con 7 consultas sobre el corpus sintético (ids Y puntuaciones) y 6 sobre el real (ids).
  - `python3 -m pytest -q tests/test_console_encoding.py tests/test_knowledge_find.py` → `336 passed` · `python3 scripts/lint_plugin.py` → `lint_plugin: 9 agentes · 0 errores · 3 avisos`, exit 0.
  - Diseño anotado en el docstring: el hash es del CONTENIDO (README + entradas, en bytes; tocar el mtime no invalida, con test), el índice guarda las entradas ya parseadas más la tabla FTS5 (`unicode61 remove_diacritics 2`, la misma segmentación que `tokens()`), FTS5 solo PRESELECCIONA candidatos (`MATCH "tok"*`) y la relevancia es la misma función en los dos caminos — así los aciertos son idénticos por construcción, no por casualidad.

**Criterios de aceptación**
- [x] `--show <ID>` devuelve la entrada completa en **≤ 2.700 tokens** (máximo real hoy: 10.449 caracteres ≈ 2.612 tokens, `ADR-012`) con **exit 0**; ID inexistente → **exit 1** (spec CA-04).
- [x] Índice ausente → se construye; `--json` trae `indice: "construido"`, mismos aciertos, **exit 0** (spec CA-05).
- [x] Índice corrupto **o** hash que no cuadra → se reconstruye; `indice: "reconstruido"`, **exit 0**.
- [x] `.claude/` no escribible **o** `sqlite3` sin FTS5 → **recorrido plano**, `indice: "degradado"`, **aciertos idénticos** a los del camino con índice, **exit 0** (spec CA-06).
- [x] El índice está en `.gitignore` y `git check-ignore` lo confirma: **el almacén son los ficheros, el índice es caché**.
- [x] **Cero dependencias nuevas**: el script se ejecuta con `python3` a secas, sin `pip install`.

**Subtareas**
- [x] Test RED de los tres estados del índice y de las dos degradaciones, con `tmp_path` y un `.claude/` de solo lectura.
- [x] Esquema FTS5 mínimo + hash del corpus guardado dentro del propio índice.
- [x] Camino plano como implementación de respaldo del **mismo** contrato de salida.
- [x] Añadir la regla al `.gitignore` (el log crudo de T-11 ya está cubierto por `*.log`, verificado).

**Notas**: la degradación es parte de la spec (§Manejo de errores), no un añadido: no se puede garantizar FTS5 en la máquina del consumidor.

### T-04 — Lint del índice: biyección `ficheros ↔ filas` y `area` obligatoria

- **Descripción**: test barato que vigila el índice de memoria igual que `tests/test_roadmap_index.py` vigila su hermano del roadmap — y por la misma razón: una entrada **sin fila es invisible** para el único camino de lectura y no hay grep de respaldo. Afirma la **biyección** (todo fichero de `adr/`/`gotchas/`/`lessons/` tiene fila, y toda fila apunta a un fichero que existe) y que **cada fila tiene columna «Área»** no vacía. Esto último no es cosmético: **para los 12 ADR el `area` SOLO vive en el índice**, así que perder la fila es perder el enrutado **sin poder reconstruirlo**.
- **Estado**: completado
- **Tiempo humano**: est. 1,5h · real 0h (sin intervención humana en la ejecución)
- **Tiempo IA (ejec.)**: est. 0,08h · real 0,10h (estimado: el usage-meter no lee la transcripción en este entorno)
- **Supervisión**: est. 0,02h (≈25 % IA) · real 0,03h (estimado)
- **Previsión IA**: 30k in / 8k out tok · 0,32 €
- **Dependencias**: ninguna (puede ir en paralelo a T-01…T-03)
- **Tipo**: test
- **Archivos**: `tests/test_knowledge_index.py`, `scripts/lint_plugin.py`, `tests/test_lint_plugin.py` (los dos últimos añadidos al cerrar: el criterio vive UNA vez en el linter como ERROR —regla 10— y el test lo importa por ruta y lo prueba con mutaciones; el orquestador lo pidió así al arrancar la fase)
- **Changelog**: El índice de la memoria técnica queda vigilado: una entrada sin fila, una fila sin área o un enlace roto hacen fallar el linter del plugin y la suite, nombrando el fichero o el ID.
- **Verificación** (ejecutada 2026-09-07):
  - `RED: tests/test_knowledge_index.py falló con AttributeError: module 'lint_plugin_knowledge' has no attribute 'lint_knowledge_index' (12 failed, 1 passed) · 2026-09-07`; GREEN después → `python3 -m pytest -q tests/test_knowledge_index.py` → **`13 passed`** sobre el corpus de hoy: **32 ficheros ↔ 32 filas** (la spec decía 31: `GOT-006` entró el 2026-09-04, después del análisis; el test exige `≥ 31` y la igualdad).
  - Con la fila de `ADR-007` borrada a mano del índice real → el test falla con `AssertionError: docs/knowledge/adr/ADR-007-deny-solo-con-alcance-de-agente.md: entrada sin fila en docs/knowledge/README.md — invisible para el único camino de lectura; añade su fila (con «Área») en la tabla del índice` y `python3 scripts/lint_plugin.py` → `❌ …ADR-007…: entrada sin fila…` · `lint_plugin: 9 agentes · 1 errores · 3 avisos`, **exit 1**.
  - Con la columna «Área» de `GOT-005` vaciada → el test falla con `AssertionError: docs/knowledge/README.md:57 (GOT-005): fila sin «Área» — para los ADR el área SOLO vive aquí; sin ella la entrada no se enruta (knowledge-find.py --area) ni se puede reconstruir` y el linter → `1 errores`, **exit 1**. Índice restaurado después (`git status --short docs/knowledge` → limpio; test → `13 passed`).
  - Las mismas mutaciones viven como tests permanentes sobre una COPIA del corpus real en `tmp_path` (`test_quitar_una_fila_del_indice_real_…`, `test_vaciar_el_area_de_una_fila_real_…`) y sobre un corpus sintético (fila hacia fichero inexistente, fila fuera de la tabla, ID/ruta repetidos, sin README con entradas, sin `docs/knowledge/`).
  - `python3 tests/test_lint_plugin.py` → `test_lint_plugin: 36/36 OK` (casos 33-36 nuevos: índice correcto → exit 0; entrada sin fila → exit 1 nombrando `gotchas/GOT-001-g.md`; fila sin «Área» → exit 1 nombrando `(ADR-001)`; enlace a fichero inexistente → exit 1; plugin sin `docs/knowledge/` → sin comprobación).
  - `python3 -m pytest -q` → **≥ 1.175 passed** (1.257 al cerrar T-04, línea base 1.181; **1.315** el 2026-09-07 al cerrar T-19: la cifra crece con cada tarea, el umbral es el criterio).

**Criterios de aceptación**
- [x] Verde sobre el corpus de hoy: **31 ficheros ↔ 31 filas** (spec CA-07). *Medido al cerrar (2026-09-07): son **32 ↔ 32** — `GOT-006` entró el 2026-09-04, después del análisis; la biyección se cumple y el test exige la igualdad exacta, no la cifra 31.*
- [x] Quitar una fila del índice pone el test **rojo nombrando el fichero**.
- [x] Una fila sin «Área» pone el test **rojo nombrando el ID**.
- [x] Una fila que apunta a un fichero inexistente pone el test **rojo** (la biyección va en los dos sentidos).
- [x] El test **no ejecuta nada** y solo lee dos cosas del disco, como su hermano: `tests/test_roadmap_index.py` es deliberadamente barato y este también.
- [x] El propio test trae su **caso sintético** de detección (que la regla se cumple sin depender del estado del repo), copiando el patrón de `test_el_detector_pilla_la_fila_suelta`.

**Subtareas**
- [x] Parsear la tabla del índice (bloque contiguo de líneas `|`, como hace `tabla_y_cola`).
- [x] Comparar con `glob` de las tres carpetas.
- [x] Caso sintético de la regla, independiente del repo.

**Notas**: `analysis.md` §1.4-5 llama a esto «la asimetría demostrable»: el índice hermano del roadmap tiene test y el de memoria no.

---

## Fase 2 — Llegada

**Estado**: completado · **Estimado**: 4,0h · **Real**: 0h humanas · 0,46h IA (estimado) + 0,12h supervisión (estimado) · **Coste est.**: 201 € · **Tokens est.**: 150.000

> Cierra el hueco **1** de `analysis.md` §1.4, el **más caro**: con `subagentes: true` el brief es el
> ÚNICO contexto (`commands/dev-cycle.md:110`) y hoy no lleva memoria, así que quien escribe el
> código **no puede alcanzar un gotcha ni queriendo**.

### T-05 — Memoria técnica en `task-brief.py`, presupuestada y enrutada por `Tipo`

- **Descripción**: sección nueva en el brief del subagente con los aciertos de `knowledge-find.py` para el área y el tipo de la tarea. El enrutado **ya existe**: el campo `- **Tipo**: frontend|backend|db|devops|test|docs` está en el ledger desde `subagent-personas`. Tope explícito de **600 tokens** frente a los **1.818** que mide el brief hoy, y **degradación silenciosa**: sin `docs/knowledge/` o sin aciertos, el brief sale idéntico al de hoy.
- **Estado**: completado
- **Tiempo humano**: est. 2,0h · real 0h (sin intervención humana en la ejecución)
- **Tiempo IA (ejec.)**: est. 0,17h · real 0,25h (estimado: el usage-meter no lee la transcripción en este entorno)
- **Supervisión**: est. 0,04h (≈25 % IA) · real 0,06h (estimado)
- **Previsión IA**: 65k in / 16k out tok · 0,67 €
- **Dependencias**: T-01
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/task-brief.py`, `agent-kits/shared/test_task_brief.py`, `agent-kits/shared/knowledge-find.py`, `tests/test_knowledge_find.py` (los dos últimos añadidos al cerrar: el ENRUTADO por área vive UNA vez, en la capa 1 del script —«--contexto/--tipo-tarea/--iniciativa», tabla «TIPO_TAREA_AREAS»— y lo consumen el brief (T-05) y el hook (T-06) con la misma orden; duplicarlo en cada consumidor habría sido dos criterios de «qué área toca esta tarea»)
- **Changelog**: El brief que recibe cada subagente trae ahora los aciertos de la memoria técnica que tocan su tarea (por tipo, título e iniciativa), con tope de 600 tokens y el estado de cada entrada delante; sin memoria en el proyecto el brief sale como antes.
- **Verificación** (ejecutada 2026-09-07):
  - `RED: tests/test_knowledge_find.py -k enrutado falló con knowledge-find.py: error: unrecognized arguments: --tipo-tarea (8 failed, 55 deselected) · 2026-09-07`; GREEN después → `63 passed`. `RED: agent-kits/shared/test_task_brief.py -k memoria falló con AssertionError: la tarea es devops y hay una entrada de área Hooks: la sección tiene que estar (assert '') (6 failed, 1 passed) · 2026-09-07`; GREEN después → **`43 passed`**.
  - `python3 agent-kits/shared/task-brief.py docs/roadmap/2026-09-04-memory-retrieval T-06 | grep -c "Memoria técnica"` → **3**, no 1: la sección existe UNA vez (`grep -c "^## Memoria técnica"` → **1**) y las otras dos son aciertos cuya ÁREA se llama literalmente «Memoria técnica / hooks» (`ADR-010`) y «Memoria técnica / lectura-escritura» (`ADR-006`) — el criterio contaba el encabezado, no las áreas del corpus real.
  - `… T-06 | wc -m` → **12.543** caracteres al cerrar T-05 (la cifra apuntada entonces, 7.212, no reproducía: CA-08 incumplido — revisión intento 1) → **9.398** tras T-19 (≤ 10.000; T-05 9.164 · T-10 8.834; test sobre las tareas del ledger real). `… | sed -n '/## Memoria técnica/,/^## /p' | wc -c` → **1.636** (≤ 2.400): 8 aciertos (`ADR-010`, `GOT-005`, `LES-012`, `ADR-006`, `ADR-007`, `ADR-012`, `GOT-006`, `LES-011`) con las claves `devops, hooks, ci, release, distribucion, consola, scripts, memoria`.
  - `python3 -m pytest -q agent-kits/shared/test_task_brief.py` → **43 passed** · `python3 -m pytest -q tests/test_console_encoding.py tests/test_knowledge_find.py agent-kits/shared/test_task_brief.py` → `387 passed` · `PYTHONIOENCODING=cp1252 python3 … task-brief.py … T-06 | grep -c "Memoria técnica"` → 3 (símbolos íntegros) · `python3 scripts/lint_plugin.py` → `9 agentes · 0 errores · 3 avisos`, exit 0.
  - Árbol sin `docs/knowledge/` (copia de la iniciativa en `mktemp -d`): `cmp` entre ese brief y el del repo real menos la sección (`_memoria_tecnica()` + su salto) → **IDÉNTICOS byte a byte**, exit 0, `grep -c "Memoria técnica"` → 0; ni una línea en stdout ni en stderr (test `test_memoria_sin_docs_knowledge_salida_identica_a_la_de_hoy`).
  - Fallo del script (exit 1 + salida no JSON) y script ausente → brief sin sección, exit 0, aviso solo por stderr (test `test_memoria_un_fallo_de_knowledge_find_no_rompe_el_brief`). Mutante del tope: `MEMORIA_TOPE_CHARS == 2400` afirmado por test, y con 41 entradas de la misma área la sección mide ≤ 2.400 y termina en «… y N acierto(s) más …» con la orden que los lista.

**Criterios de aceptación**
- [x] La sección de memoria es **≤ 600 tokens (≤ 2.400 caracteres)** y el brief completo **≤ 2.500 tokens** (spec CA-08). *Medido: 1.636 y 12.543 al cerrar T-05 (incumplido; la cifra «7.212» era falsa) → 9.398 ≈ 2.350 tokens desde T-19, con `BRIEF_TOPE_CHARS = 10000` y test sobre el ledger real.*
- [x] El enrutado usa el campo `- **Tipo**:` que **ya existe**; sin `Tipo`, cae al área de la iniciativa y no al corpus entero. *Sin `Tipo` entran las entradas nacidas en la iniciativa (`iniciativa == slug`) y las cuya área casa con el título de la tarea; nunca puntuación 0 (test `test_memoria_sin_tipo_cae_a_la_iniciativa_y_no_al_corpus_entero`).*
- [x] Sin `docs/knowledge/` o sin aciertos: salida **idéntica a la de hoy**, sin aviso en stdout ni sección vacía, exit 0 (spec CA-09).
- [x] El tope es una **constante con test**, no una intención: un mutante que la suba pone el test rojo. *T-19: el recorte también tiene test que muerde.*
- [x] Las **10 secciones actuales** del brief siguen intactas y en su orden (test `test_memoria_no_altera_las_secciones_existentes_ni_su_orden`: la memoria va tras la Verificación y antes de Diseño/Arquitectura/Constitución/TDD/Contrato).
- [x] Un fallo de `knowledge-find.py` (cualquiera) **no rompe el brief**: se omite la sección y el brief sale con exit 0.

**Subtareas**
- [x] Test RED del tope y de la degradación silenciosa.
- [x] Llamar a `knowledge-find.py --json` y renderizar la sección 11.
- [x] Recorte al tope con la línea que lo dice, nunca emitir por encima.

**Notas**: `analysis.md` §1.4-1, medido: hoy `grep` sobre `task-brief.py` da un solo acierto de `knowledge`, y es un comentario de encoding. **Decisión de ejecución (no cruza el umbral de ADR: una pieza, reversible):** el enrutado es **por ÁREA, nunca por texto libre** — probado sobre el corpus real, una consulta libre con el título de la tarea («tope», «sesión», «activa») puntúa medio corpus por coincidencias en el texto; con área, `T-06` (devops) recibe `ADR-010`/`ADR-007`/`GOT-005` y ninguna lección de estimación. El ruido residual es el prefijo (`activa` casa «activación de piezas», `LES-011`): aceptado y visible en la línea `claves:` de la sección.

### T-06 — Memoria del área activa al arrancar sesión, con tope propio

- **Descripción**: `session-context.sh` gana un cuarto bloque: **no el corpus** (27.100 tokens no caben en el `TOPE_CHARS = 9500` del hook) sino los N mejores aciertos del **área de la iniciativa activa**, con tope explícito de **300 tokens**. Hoy el hook inyecta 872 tokens y **ninguno** es memoria curada.
- **Estado**: completado
- **Tiempo humano**: est. 1,5h · real 0h (sin intervención humana en la ejecución)
- **Tiempo IA (ejec.)**: est. 0,10h · real 0,15h (estimado: el usage-meter no lee la transcripción en este entorno)
- **Supervisión**: est. 0,03h (≈25 % IA) · real 0,04h (estimado)
- **Previsión IA**: 40k in / 10k out tok · 0,41 €
- **Dependencias**: T-01
- **Tipo**: devops
- **Archivos**: `hooks/session-context.sh`, `tests/test_hooks_shell.py`, `agent-kits/shared/doctor.py`, `agent-kits/shared/test_doctor.py` (los dos últimos añadidos al cerrar: «sesion.memoria» entra en el vocabulario de «dev.json» que valida «/doctor» — sin eso el opt-out nuevo saldría como «clave desconocida»)
- **Changelog**: Al arrancar o retomar una sesión (también tras compactar), el contexto trae los aciertos de la memoria técnica del área de la iniciativa activa, topados a 300 tokens y sin desplazar el índice de piezas ni el roadmap; se apaga con `sesion.memoria: false`.
- **Verificación** (ejecutada 2026-09-07):
  - `RED: tests/test_hooks_shell.py -k "memoria or bloque" falló con AssertionError: [startup] falta el bloque de memoria del área activa (assert '') (2 failed, 3 passed) · 2026-09-07`; GREEN después → `python3 -m pytest -q tests/test_hooks_shell.py` → **`34 passed`** (4 tests nuevos: bloque bajo el tope en `startup|resume|compact` y detrás del roadmap · sin `docs/knowledge/`, sin aciertos o sin activa → mismo contexto que hoy · `sesion.memoria: false` lo apaga · 41 entradas del área → bloque ≤ 1.200 con «… y N más» y el índice/roadmap enteros, sin recorte global).
  - `echo '{"hook_event_name":"SessionStart","source":"startup"}' | bash hooks/session-context.sh | python3 -c "…print(len(t))"` → **≤ 9.500** (4.263 al cerrar T-06; 4.276 al cerrar T-19: el índice de piezas cambia con cada pieza; sin memoria: 3.730 ≈ 872 tokens) con `CLAUDE_PLUGIN_ROOT=$PWD`. *Medido al cerrar T-06:* sin la variable el `find` sobre `~/.claude` daba con una copia INSTALADA anterior (`~/.claude/plugins/synced/…`) y salía sin bloque; **corregido en T-19 (gap 9)**: `<proyecto>/agent-kits/shared` va antes que el `find`.
  - Porción de memoria de ese `additionalContext` → **533 caracteres** (≤ 1.200 = `MEMORIA_TOPE_CHARS`, spec CA-10), con 4 aciertos del área activa y el `estado` delante; el índice de piezas y el bloque de roadmap salen íntegros y el total queda < 10.000.
  - `echo '{"hook_event_name":"SessionStart","source":"compact"}' | bash hooks/session-context.sh` → JSON válido (`hookSpecificOutput.hookEventName/additionalContext`), **exit 0**.
  - Árbol sin `docs/knowledge/`, corpus sin aciertos del área o sin iniciativa activa → el hook no emite el bloque y el `additionalContext` es **igual** al de hoy (test `test_session_context_sin_knowledge_sin_aciertos_o_sin_activa_no_emite_el_bloque`, igualdad de cadenas).
  - **Tiempo del hook** (`time bash hooks/session-context.sh`, 3 medidas): sin memoria 0,42 s → con memoria 0,55 s (+0,13 s, una llamada local a `knowledge-find.py` con el índice ya construido).
  - `pytest -q tests/test_console_encoding.py` → `281 passed` (el `python3 -c` nuevo del hook lleva `PYTHONIOENCODING=utf-8:replace`, `GOT-005`).

**Criterios de aceptación**
- [x] El bloque de memoria es **≤ 300 tokens (≤ 1.200 caracteres)** y el `additionalContext` total sigue **≤ 9.500 caracteres** (spec CA-10). Línea base: 872 tokens, **0** de memoria. *Medido: 533 y 4.263 al cerrar T-06; 533 y 4.276 al cerrar T-19.*
- [x] El tope propio se aplica **antes** del recorte global a `TOPE_CHARS`, para que la memoria no se coma el índice de piezas ni el roadmap (`MEMORIA_TOPE_CHARS = 1200` dentro del bloque (4); test con 41 entradas).
- [x] Sin iniciativa activa, sin `docs/knowledge/` o sin aciertos: **no se emite el bloque**; el resto de la salida es la de hoy.
- [x] El hook sigue **siempre exit 0** y nunca emite JSON inválido, pase lo que pase con la memoria (todo el bloque va en un `$(… || true)` con stderr a `/dev/null`; el JSON final lo compone el mismo python de siempre).
- [x] Desactivable por `.claude/dev.json` → `sesion.memoria: false`, como ya se puede con `sesion.indice` y `sesion.journal`.

**Subtareas**
- [x] Test RED en `tests/test_hooks_shell.py` con un fixture de iniciativa activa.
- [x] Derivar el área de la iniciativa activa (`progress-report.py active` ya la sabe). *Matiz medido: `active --json` da `slug` y `path`, no un área; el área se deriva del título H1 del ledger + el slug, enrutados por `knowledge-find.py --contexto/--iniciativa`.*
- [x] Insertar el bloque (4) y respetar el orden actual de los tres que hay.

**Notas**: `TOPE_CHARS = 9500` está en `hooks/session-context.sh:88` y viene del tope de 10.000 caracteres del contrato oficial del hook. **Decisión de ejecución:** el bloque va también en `compact`, por la misma razón que el índice de piezas (la compactación resume la conversación y puede perder lo inyectado al arrancar; cuesta ≤ 300 tokens). Deuda declarada para T-18: `docs/CONVENTIONS.md` regla 9 y `/setup` aún no mencionan `sesion.memoria` (doc ES/EN es de la Fase 6).

### T-07 — El reparto por agente de `knowledge-check.md` deja de ser solo prosa

- **Descripción**: la tabla «qué lee cada agente» del fragmento compartido pasa de decir *qué debería abrir* a **nombrar el comando** de `knowledge-find.py` que le corresponde (`evaluator` → `--area estimacion`, `implementer` → área de la tarea, `qa` → `--tipo gotcha`, etc.). El fragmento sigue siendo la **fuente única**: no se duplica en ningún prompt.
- **Estado**: completado
- **Tiempo humano**: est. 0,5h · real 0h (sin intervención humana en la ejecución)
- **Tiempo IA (ejec.)**: est. 0,04h · real 0,06h (estimado: el usage-meter no lee la transcripción en este entorno)
- **Supervisión**: est. 0,01h (≈25 % IA) · real 0,02h (estimado)
- **Previsión IA**: 15k in / 4k out tok · 0,16 €
- **Dependencias**: T-01
- **Tipo**: docs
- **Archivos**: `agent-kits/shared/knowledge-check.md`, `agents/evaluator.md`, `agents/planner.md`, `agents/implementer.md`, `agents/qa.md`, `agents/documenter.md`, `agents/architect.md`, `agents/reviewer.md` (los agentes añadidos al cerrar, por encargo del orquestador: la línea de §REGLAS de cada agente que cita el fragmento nombra su orden exacta —UNA línea, sin duplicar la tabla—, y «reviewer», que no leía memoria nunca, gana la suya)
- **Changelog**: Cada agente sabe ya qué orden exacta de la memoria técnica le toca ejecutar (por área, tipo de entrada o tarea) en vez de leer el índice entero y decidir; el revisor adversarial también consulta los ADR del área del diff.
- **Verificación** (ejecutada 2026-09-07):
  - `TDD n/a: prosa` (fragmento compartido y líneas de prompt; se verifica por lectura y por grep, como declara la tarea).
  - `grep -c "knowledge-find.py" agent-kits/shared/knowledge-check.md` → **12** (≥ 5: las 7 filas de la tabla —`evaluator`, `planner`, `architect`, `implementer`, `reviewer`, `qa`, `documenter`— más el bloque de ejemplo de las tres capas).
  - `python3 scripts/lint_plugin.py` → `lint_plugin: 9 agentes · 0 errores · 3 avisos`, **exit 0** · `python3 tests/test_lint_plugin.py` → `36/36 OK`.
  - Lectura: cada fila de «Reparto de qué lee cada agente» nombra su orden y **ninguna** pide «lee el índice y decide» (`grep -c "lee su .README.md. y abre" knowledge-check.md` → 0); el párrafo de la distinción por `estado` (aceptada / propuesta / obsoleta con sucesor) es **substring literal** del de `HEAD` (comprobado con Python: `True`); la 1.ª capa no obliga a abrir nada («con 0 aciertos, sigue sin abrir nada»).
  - `grep -rl "Reparto de qué lee cada agente" agents/` → **sin resultados** (el fragmento no está copiado en ningún prompt); `grep -n "knowledge-find.py" agents/*.md` → exactamente UNA línea por agente (7 agentes).
  - Bytes de los prompts (`wc -c`, antes → después): `evaluator.md` **15.513 → 15.513 (+0; CA-22 intacto)** · `documenter.md` 12.836 → 12.871 (+35) · `planner.md` 17.945 → 17.987 (+42) · `qa.md` 15.742 → 15.800 (+58) · `architect.md` 13.697 → 13.770 (+73) · `implementer.md` 20.605 → 20.695 (+90) · `reviewer.md` 6.398 → 6.777 (+379, la línea nueva de un agente que no tenía ninguna). La orden literal es más larga que la prosa que sustituye; el resto de cada línea se acortó para compensar.

**Criterios de aceptación**
- [x] Las **5** filas de la tabla nombran su comando concreto de `knowledge-find.py` (spec CA-11). *Son 7 filas: las 5 de antes más `architect` (ya citaba el fragmento) y `reviewer` (nuevo lector, por encargo del orquestador).*
- [x] La regla de **progressive disclosure** se conserva: la 1.ª capa no obliga a abrir nada.
- [x] La distinción por `estado` (doctrina / indicio / obsoleta con sucesor) se conserva **literal**: es el criterio 1 de superioridad y no se toca al reescribir.
- [x] El fragmento sigue siendo **fuente única**: no aparece copiado en ningún `agents/*.md` (cada agente lleva una línea con SU orden y remite al fragmento).
- [x] `lint_plugin.py` sigue en **exit 0** (hoy: 9 agentes · 0 errores · 3 avisos).

**Subtareas**
- [x] Reescribir la tabla del reparto.
- [x] Añadir el ejemplo de invocación con localización del kit (regla 5 de `CONVENTIONS`).

**Notas**: es la única tarea de esta fase que se verifica **por lectura** en su mayor parte, y así se declara — es prosa, y fingir un test sería peor. El fragmento sigue diciendo cómo degradar sin el script (instalación parcial): leer `README.md` y abrir solo las filas del área.

---

## Fase 3 — Prueba de que se recorre

**Estado**: completado · **Estimado**: 4,0h · **Real**: 0h humanas · 0,76h IA (estimado) + 0,20h supervisión (estimado; incluye T-19) · **Coste est.**: 201 € · **Tokens est.**: 128.000

> **Esto no lo tiene nadie —ni nosotros ni `claude-mem`— y es la diferencia entre una intención y una
> garantía.** El gate es determinista y no gasta tokens; la eval de activación es la comprobación de
> comportamiento y vive donde ya viven las caras.

### T-08 — `tests/test_memory_path.py`: el camino se recorre, con su mutante

- **Descripción**: test determinista que afirma que un agente con una tarea de **área X** recibe la entrada de **área X**: sobre un corpus de `tmp_path`, el brief de una tarea de área X contiene el ID de la entrada de área X y **no** los de otras áreas. Y —la parte que lo hace valer— se prueba **con su mutante**: quitando la inyección de `task-brief.py`, el test se pone **rojo**. Un test que pasa con y sin la inyección no prueba nada.
- **Estado**: completado
- **Tiempo humano**: est. 1,5h · real 0h (sin intervención humana en la ejecución)
- **Tiempo IA (ejec.)**: est. 0,10h · real 0,10h (estimado: el usage-meter no lee la transcripción en este entorno)
- **Supervisión**: est. 0,03h (≈25 % IA) · real 0,03h (estimado)
- **Previsión IA**: 38k in / 10k out tok · 0,40 €
- **Dependencias**: T-05, T-06
- **Tipo**: test
- **Archivos**: `tests/test_memory_path.py`
- **Changelog**: La suite comprueba, sin gastar tokens, que la memoria técnica del área de una tarea llega de verdad al brief del subagente y al arranque de sesión, y que las de otras áreas no: si alguien quita la inyección, la suite se pone roja.
- **Verificación** (ejecutada 2026-09-07):
  - `python3 -m pytest -q tests/test_memory_path.py` → **`7 passed`** (verde sobre el código de T-05/T-06; el RED de esta tarea es el mutante, no un test escrito antes del código: el gate se escribe DESPUÉS de los dos caminos, y lo que prueba que muerde es que se ponga rojo al neutralizarlos).
  - **Mutante 1** (copia del repo en `/tmp` con `git archive HEAD`; `_memoria_tecnica()` devuelve `None` en su primera línea) → **`3 failed, 4 passed`**: `AssertionError: brief de T-01 (tipo devops, área Hooks / implementer): no llegó ADR-001 — el camino brief no se recorre` · `brief de T-02 (tipo test, área Tests / fixtures): no llegó GOT-001` · el tope (`assert 0 < 0`). El mensaje nombra el **área y el ID** que no llegaron.
  - **Mutante 2** (`session-context.sh` sin el bloque (4)) → **`2 failed, 5 passed`**: `[startup] additionalContext (área Hooks / implementer): no llegó ADR-001 — el camino del hook no se recorre` y `el tope del hook es una constante con test (spec CA-10)`.
  - **Mutante 3** (`MEMORIA_TOPE_CHARS = 2401` en `task-brief.py`) → `1 failed`: `assert 2401 == 2400`. Los tres mutantes están documentados en el docstring del test, con el mensaje esperado.
  - `env -i PATH=/usr/bin:/bin HOME=/tmp python3 -m pytest -q tests/test_memory_path.py` (sin `claude` en PATH —aquí vive en `/opt/node22/bin`—, sin variables, sin red) → `7 passed` · `test_los_dos_caminos_no_usan_red_ni_claude` afirma que ni `task-brief.py`, ni `session-context.sh`, ni `knowledge-find.py` importan `urllib`/`requests`/`socket` ni invocan `claude -p`.
  - `python3 -m pytest -q tests/test_suites_no_pytest.py` → `10 passed` (el fichero tiene `def test_*`: pytest lo recoge; no entra en el bucle de scripts).

**Criterios de aceptación**
- [x] Verde hoy y **rojo con el mutante** (spec CA-12): se documenta en el propio test qué se neutraliza para verlo rojo.
- [x] Cubre **los dos** caminos de llegada: el brief (T-05) y el arranque de sesión (T-06), este último en `startup|resume|compact`.
- [x] Afirma también el **tope** de cada camino (600 / 300 tokens), no solo la presencia: la constante (`MEMORIA_TOPE_CHARS` de cada pieza) y la medida de la sección/bloque.
- [x] **No usa red, ni `claude`, ni clave de API**, y corre sobre `tmp_path`, no sobre el corpus real (el corpus de mentira tiene tres áreas: la de la tarea devops, la de la tarea test y una ajena que nadie pide).
- [x] Un aserto **negativo**: una tarea de área Y **no** recibe la entrada de área X (si recibe todo, no hay enrutado) — en los dos sentidos y con la entrada ajena.

**Subtareas**
- [x] Fixture con un corpus mínimo de dos áreas y una iniciativa de mentira.
- [x] Asertos de presencia, de ausencia y de tope.
- [x] Documentar el mutante en el docstring.

**Notas**: este test es el **gate**; la eval de T-09 es la comprobación de comportamiento. No se confunden los papeles. El ledger de la iniciativa de mentira es VÁLIDO para `ledger-lint` a propósito: el brief se pide sin `--sin-lint`, por el mismo camino que usa `/dev-cycle`.

### T-09 — Casos en `evals/` para el camino de memoria

- **Descripción**: casos nuevos en `evals/cases/agent-implementer.json` y `agent-evaluator.json` que afirmen que el agente **usa** la memoria de su área (menciona el ID que le corresponde) en vez de ignorarla. Formato ya fijado por `evals/check.py` (38 ficheros y 133 casos de precedente); el fixture de `evals/fixtures/project/` gana las entradas de memoria necesarias.
- **Estado**: completado
- **Tiempo humano**: est. 1,0h · real 0h (sin intervención humana en la ejecución)
- **Tiempo IA (ejec.)**: est. 0,07h · real 0,06h (estimado: el usage-meter no lee la transcripción en este entorno)
- **Supervisión**: est. 0,02h (≈25 % IA) · real 0,02h (estimado)
- **Previsión IA**: 25k in / 7k out tok · 0,28 €
- **Dependencias**: T-08
- **Tipo**: test
- **Archivos**: `evals/cases/agent-implementer.json`, `evals/cases/agent-evaluator.json`, `evals/fixtures/project/`, `.gitignore` (añadido al cerrar: al pedir el brief de una tarea del fixture, «knowledge-find.py» crea su índice en «evals/fixtures/project/.claude/»; la regla pasa a «**/.claude/knowledge-index.sqlite» para cubrir también proyectos anidados)
- **Changelog**: La suite de evals comprueba que el implementador cita el gotcha de su área y el evaluador la lección de estimación que le toca, y no al revés, sobre un proyecto de prueba con memoria técnica inventada.
- **Verificación** (ejecutada 2026-09-07):
  - `TDD n/a: casos de eval (JSON) y fixture inventado; el gate mecánico es evals/check.py` — RED equivalente: antes de añadir los casos, `check.py` daba 133 casos; el fixture no tenía `docs/knowledge/`.
  - `python3 evals/check.py` → **`evals/check: 38 ficheros · 135 casos (80 positivos, 55 negativos) · 38 piezas del repo · 0 errores`**, exit 0 (línea base: 38 · 133 · 0; +2 casos: `implementer-memoria-gotcha-del-area` y `evaluator-memoria-leccion-de-estimacion`, ids únicos en toda la suite).
  - `python3 -m pytest -q evals` → `23 passed`.
  - `PATH=/usr/bin:/bin python3 evals/run.py --target agent:implementer` → `evals/run: \`claude\` no está en PATH — … Nada ejecutado.`, **exit 2** (degrada, no falla: la eval no es un gate que dependa de una clave).
  - Lectura: los prompts nuevos hablan de `docs/roadmap/2026-01-01-demo` y `docs/knowledge` del fixture inventado (`demo-app`); ningún correo, host, URL ni clave Jira (`check.py` regla 6, 0 errores). El fixture gana `docs/knowledge/README.md` + `gotchas/GOT-001-csv-comillas-dobles-rfc4180.md` (área «Backend / exportación CSV») + `lessons/LES-001-evaluator-csv-parece-trivial.md` (área «Estimación / calibración»), todo inventado.
  - Comprobado que el camino determinista enruta el fixture como esperan los casos: `knowledge-find.py --root evals/fixtures/project --tipo-tarea backend --contexto "Escapado de comas y comillas" --iniciativa demo` → solo `GOT-001`; `--area estimacion --tipo lesson` → solo `LES-001`; el brief de `T-02` del fixture trae la sección de memoria con `GOT-001`.
  - `git check-ignore -v evals/fixtures/project/.claude/knowledge-index.sqlite` → `.gitignore:63:**/.claude/knowledge-index.sqlite`; `tests/test_knowledge_find.py -k gitignore` → passed.

**Criterios de aceptación**
- [x] `evals/check.py` sigue en **exit 0** con los casos nuevos (spec CA-13).
- [x] Los casos nuevos tienen `expect.mentions` con el **ID de la entrada** de su área, no una frase vaga (`GOT-001` para el implementer, `LES-001` para el evaluator), y `must_not` con el ID del área vecina.
- [x] Se mantiene la cobertura que `check.py` exige (≥ 2 positivos + ≥ 1 negativo por pieza) y los **ids únicos** en toda la suite.
- [x] **Ni un dato corporativo** en los prompts nuevos (repo público).
- [x] `run.py` sigue degradando a **exit 2** sin `claude` en PATH: la eval **no** se convierte en un gate que dependa de una clave.

**Subtareas**
- [x] Añadir las entradas de memoria al fixture del proyecto de mentira.
- [x] Escribir los casos (positivo con el ID esperado, negativo de área vecina). *El «negativo de área vecina» va como `must_not` dentro del positivo: en el esquema de `check.py` un caso negativo es «el agente NO se activa», y aquí el agente sí debe activarse — lo que no debe hacer es citar la entrada del área ajena.*
- [x] Comprobar los ids únicos en toda la suite.

**Notas**: `LES-011`: «la description es una promesa de activación, y una promesa se prueba, no se asume». Aquí la promesa que se prueba es la de la memoria. Los casos cuestan tokens reales y viven donde ya viven las caras (`run.py` local / `headless.yml`); el gate barato es T-08.

### T-10 — `/doctor` puntúa la salud de la memoria

- **Descripción**: hoy `/doctor` da «Instalación sana» con **0** entradas de journal, **sin contar** las 31 curadas, **sin validar** el índice y **sin avisar** de que `CALIBRATION.md` lleva 15 días sin fila con 13 iniciativas cerradas detrás. Gana una sección de salud de memoria: entradas curadas por familia, estado del índice (válido / reconstruible / degradado), entradas de journal y antigüedad de la última fila de calibración.
- **Estado**: completado
- **Tiempo humano**: est. 1,5h · real 0h (sin intervención humana en la ejecución)
- **Tiempo IA (ejec.)**: est. 0,10h · real 0,15h (estimado: el usage-meter no lee la transcripción en este entorno)
- **Supervisión**: est. 0,02h (≈25 % IA) · real 0,04h (estimado)
- **Previsión IA**: 37k in / 11k out tok · 0,42 €
- **Dependencias**: T-03
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/doctor.py`, `agent-kits/shared/test_doctor.py`
- **Changelog**: `/doctor` deja de dar por sana una instalación con la memoria a medias: cuenta las entradas curadas por familia y estado, valida el índice de la memoria (❌ si una entrada no tiene fila), avisa si el journal sigue a 0 con memoria curada y si CALIBRATION.md lleva más de 14 días sin fila con iniciativas cerradas después, diciendo cuántas y cuáles.
- **Verificación** (ejecutada 2026-09-07):
  - `RED: agent-kits/shared/test_doctor.py falló con StopIteration (bloque "memoria" inexistente) y assert 0 == 1 (sin línea "memoria curada") (7 failed, 25 passed) · 2026-09-07`; GREEN después → **`33 passed`** (7 tests nuevos + `test_los_seis_bloques_estan_siempre`, antes «cinco»).
  - `python3 agent-kits/shared/doctor.py | grep -i "memoria"` → `✅ memoria curada · 32 entrada(s): 12 ADR · 6 gotcha(s) · 14 lección(es) · estados: 32 aceptada` · `✅ índice de memoria (README) · biyección ficheros ↔ filas y «Área» en las 32 entrada(s) (criterio de lint_plugin.py)` · `✅ índice de búsqueda (FTS5) · válido · al día con el corpus` · `⚠️ journal de sesión · 0 entradas con 32 entrada(s) curada(s): la memoria episódica no se está escribiendo` · `⚠️ calibración (CALIBRATION.md) · última fila 2026-08-20: 18 días sin fila y 15 iniciativa(s) cerrada(s) después sin retro: adversarial-review, debt-cleanup, deterministic-guardrails, live-visibility, activation-reliability, distribution …`. Resumen: **`12 ✅ · 2 ⚠️ · 0 ❌ · 9 ℹ️`** → «Nada roto: 2 aviso(s) …», **ya no dice «Instalación sana»** (antes: `9 ✅ · 0 ⚠️ · 0 ❌ · 10 ℹ️ · Instalación sana`). Las 31 de la spec son hoy **32** (`GOT-006`, medido en T-01); los 15 días / 13 cerradas del análisis son hoy **18 / 15** (han pasado tres días y se han cerrado `ci-sin-identidad-git` y `sin-motor-externo`).
  - Árbol con índice inválido (copia de `docs/knowledge` + `docs/roadmap` en `mktemp -d`, fila de `ADR-007` borrada): `❌ índice de memoria (README) · docs/knowledge/adr/ADR-007-…: entrada sin fila en docs/knowledge/README.md — invisible para el único camino de lectura …` · `Hay 1 problema(s) que rompen algo del plugin …`, **exit 1**, y **no** imprime «Instalación sana».
  - `python3 -m pytest -q agent-kits/shared/test_doctor.py` → `33 passed` · `tests/test_console_encoding.py -k doctor` → `8 passed` · `PYTHONIOENCODING=cp1252 python3 agent-kits/shared/doctor.py | grep -c memoria` → 5 (símbolos íntegros).
  - Árbol sin `docs/knowledge/` (`mktemp -d`): `ℹ️ memoria técnica · sin docs/knowledge/ — un proyecto recién instalado nace sin memoria, y es correcto` · `ℹ️ journal de sesión · sin docs/knowledge/journal/`, **exit 0**, `0 ❌`, sigue diciendo «Instalación sana».
  - Solo lectura afirmada: el índice FTS5 se lee en `mode=ro` y NUNCA se construye desde el doctor (`test_indice_fts5_ausente_informa_valido_ok_y_corrupto_avisa_sin_escribir` compara el snapshot del proyecto antes y después); la antigüedad de `CALIBRATION.md` es determinista en tests con `hoy=` (`diagnostico(project, plugin_root, hoy)` y `--hoy AAAA-MM-DD`).

**Criterios de aceptación**
- [x] Con 31 curadas, 0 de journal e índice inválido, **no** dice «Instalación sana»; nombra las tres cosas (spec CA-14). *Medido: 32 curadas; el índice inválido es ❌ (exit 1) nombrando el fichero sin fila; el journal a 0 con memoria curada es ⚠️.*
- [x] Avisa cuando `CALIBRATION.md` lleva **> 14 días** sin fila (hoy: 15) y dice **cuántas iniciativas** se han cerrado desde entonces (`CALIBRACION_DIAS_MAX = 14`; hoy 18 días y 15 cerradas, nombradas).
- [x] Cada línea trae su **arreglo concreto**, como el resto de `/doctor` (`test_toda_linea_de_aviso_o_error_trae_arreglo` sigue verde).
- [x] Sin `docs/knowledge/`: línea **informativa** y exit 0 — un proyecto recién instalado no está roto por nacer sin memoria.
- [x] Los avisos de memoria son **⚠️**, no ❌, salvo índice inválido: `/doctor` no se vuelve alarmista (si todo es rojo, la gente lo ignora). *El índice FTS5 corrupto o `sqlite3` sin FTS5 son ⚠️ (la búsqueda degrada a plano, no se rompe); ausente o desfasado, ℹ️.*
- [x] Sigue sin usar red y sigue siendo de **solo lectura**.

**Subtareas**
- [x] Test RED con árboles de `tmp_path` para los cuatro estados.
- [x] Función `_memoria(project)` al estilo del `_journal(project)` que ya existe. *Es `bloque_memoria(plugin_root, project, hoy)`: un bloque propio «Memoria técnica (docs/knowledge/)» —el sexto— que absorbe `_journal` (ahora con el aviso a 0 CON memoria curada) y añade `_curadas`, `_indice_readme` (delega en `lint_knowledge_index` de T-04), `_indice_fts5` y `_calibracion`.*
- [x] Enganchar en el veredicto y en la lista de secciones.

**Notas**: el `_journal(project)` actual ya informa de «carpeta sin entradas todavía» pero **no cambia el veredicto**; eso es exactamente lo que se corrige. **Deuda declarada para T-18:** `commands/doctor.md` (description y cuerpo), `docs/README.md` y `docs/FLOWS.md` describen cinco bloques sin la memoria — la description está atada al caso literal de `evals/cases/command-doctor.json` (`check.py` regla 4), así que se cambia con su eval, en la fase de doc.

### T-19 — Cierre de los gaps del intento 1 (Fases 1-3)

- **Descripción**: corrige los 12 gaps de la revisión de dos lentes (intento 1, `b5731c4..7ca3645`) sobre T-01…T-10, reproducidos antes de tocar nada: stopwords y orden de la consulta libre, recorte de la memoria del brief sin test, conteo del hook con ≥ 2 activas, CA-08 incumplido, enrutado vacío y `--limit` negativo, índice del doctor sin el criterio del linter, evals que no exigían «aplicar», resolución del kit en el hook, `test_memory_path` sin cubrir el `Tipo` y cifras sin re-medir. El detalle de cada uno está en su bullet de Verificación.
- **Estado**: completado
- **Tiempo humano**: est. 0h (fuera del plan: línea transversal de revisión) · real 0h
- **Tiempo IA (ejec.)**: est. 0,40h · real 0,45h (estimado: el usage-meter no lee la transcripción en este entorno)
- **Supervisión**: est. 0,10h (≈25 % IA) · real 0,11h (estimado)
- **Previsión IA**: 150k in / 45k out tok · 1,73 €
- **Dependencias**: T-01…T-10 (revisión de dos lentes, intento 1)
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/knowledge-find.py`, `tests/test_knowledge_find.py`, `agent-kits/shared/task-brief.py`, `agent-kits/shared/test_task_brief.py`, `hooks/session-context.sh`, `tests/test_hooks_shell.py`, `agent-kits/shared/doctor.py`, `agent-kits/shared/test_doctor.py`, `scripts/lint_plugin.py`, `tests/test_knowledge_index.py`, `evals/cases/agent-implementer.json`, `evals/cases/agent-evaluator.json`, `tests/test_memory_path.py`
- **Changelog**: La consulta libre de la memoria técnica ignora las palabras sin contenido y ordena por título, área e ID antes que por el cuerpo; el brief del subagente cabe en 2.500 tokens y lleva la verificación una vez; el arranque de sesión con varias iniciativas activas cuenta los aciertos una vez.
- **Verificación** (ejecutada 2026-09-07):
  - `python3 -m pytest -q` → **`1315 passed`** (antes 1.292); igual sin config global de git y con `PYTHONIOENCODING=cp1252`.
  - `lint_plugin.py` → `9 agentes · 0 errores · 3 avisos` · `tests/test_lint_plugin.py` → `36/36 OK` · `evals/check.py` → `135 casos · 0 errores` · `ledger-lint.py` → `0 incoherencias · 8 avisos` (Changelog de T-11…T-18) · `scope-check.py --base 7ca3645` → `fuera de alcance (0)` · `export-skills.py --out/--check` → `108 ficheros · 0 problema(s)`; todos exit 0.
  - Gap 1, antes → después: `knowledge-find.py "cual es el ratio de tokens por hora que uso para estimar" --json --limit 0` → `total 32` (las 9 lecciones de estimación en 15-32) → **`total 14`**, tokens `["ratio","token","hora","estim"]`, las 9 en **1-4 y 6-10** · `"de"` → 10 → **0** · `"quiero saber si el pato vuela hacia marte"` → 32 → **0** · `"consola windows cp1252"` → `GOT-005` primero (igual).
  - Gap 2, mutante «bucle de recorte → render único»: test viejo verde; `test_memoria_el_recorte_al_tope_muerde_de_verdad` → **`assert 3008 <= 2400`**.
  - Gap 3, hook: 2 activas de la misma área (3 entradas) → `3 acierto(s)`, 3 líneas, sin «más» · 3 activas → `… · 3 iniciativas activas, consultadas las 2 primeras; fuera: demo-c` · 41 entradas y 2 activas → `41 acierto(s)`, N = 41 − mostradas.
  - Gap 4, caracteres de los 10 briefs antes → después (2026-09-07, Linux): de 8.919-12.543 (7 de 10 por encima del tope) a 6.735-9.398, T-19 incluida (9.931); memoria de T-06 idéntica. *Re-medido 2026-09-08 en Windows (la medida incluye la ruta absoluta de `knowledge-find.py`, más larga aquí): T-01 7.888 · T-05 9.243 · T-06 9.477 · T-19 9.802.* Los valores por tarea del 09-07 están en el commit `7553131`.
  - Gaps 5 y 8: `--contexto "" --iniciativa "" --limit 0` → 32 → **0** · `--limit -1` → 32 líneas → **error de uso («es negativo; usa 0 para sin tope»), exit 2**.
  - Gap 6: fila hacia `adr/ADR-099-fantasma.md`: doctor de `e08fc05` → `✅ (comprobación local)`; HEAD → **`❌ … enlaza a `adr/ADR-099-fantasma.md`, que no existe`**, exit 1.
  - Gap 10: `def celdas_md` una vez por script (3); tests de identidad de los bloques `--8<--` verdes.
  - Gap 11, mutante sin `["--tipo-tarea", tipo]`: `test_memory_path.py` de `7ca3645` → `7 passed`; el de HEAD → **`3 failed, 4 passed`**.
  - Gap 12: cifras re-medidas y pegadas en T-02/T-04/T-05/T-06 (`--related`, `additionalContext`, `pytest` 1.315).

**Criterios de aceptación**
- [x] Una lista de stopwords ES/EN para consulta libre, enrutado y `--related`; consulta sin tokens con contenido que casen → **0, exit 0**; título/área/ID por encima del cuerpo; las tres consultas con test (real y sintético).
- [x] El recorte de la memoria del brief tiene un test que lo **fuerza**; el mutante «render único» lo pone rojo.
- [x] El hook deduplica **antes** de contar; «y N más» real; con > 2 activas la cabecera lo dice; tests con 2 y 3 activas, con y sin solape, y con el tope apretando.
- [x] CA-08 cumplido: `Verificación` una vez y sin `RED:`/`TDD n/a`; presupuesto y `Changelog` fuera del bloque; `BRIEF_TOPE_CHARS = 10000` con test sobre **todas** las tareas del ledger real (T-19 incluida) y sobre `tmp_path`; la Verificación de T-05 corregida.
- [x] Filtro de enrutado vacío = 0 aciertos; `--limit` negativo = exit 2; ambos en el docstring.
- [x] `/doctor` valida el índice con el criterio del linter **literal** (bloques `--8<--` + tests de identidad byte a byte, `celdas_md` incluida).
- [x] Evals: citar **y aplicar** (`GOT-001` + `RFC 4180`; `LES-001` + `escapado`), sin `must_not`.
- [x] Hook: `<proyecto>/agent-kits/shared` antes que el `find`, tras `CLAUDE_PLUGIN_ROOT`, con test.
- [x] `test_memory_path.py` cubre el enrutado por `Tipo` (títulos sin tokens de área; mutante → 3 failed).
- [x] Cifras re-medidas («≤ tope» donde dependen del corpus del día); `scope-check --base 7ca3645` exit 0; `CHANGELOG*.md` y `sin-motor-externo/` intactos.

**Subtareas**
- [x] Reproducir cada afirmación antes de corregir; mutantes y mediciones antes/después con copias de `HEAD~` en `/tmp`.
- [x] Gaps 1/5/8 en `knowledge-find.py`; 2/4 en `task-brief.py`; 3/9 en el hook; 6/10 en doctor/linter/knowledge-find; 7 en evals; 11 en `test_memory_path.py`; 12 aquí.

**Notas**: dos decisiones bajo el umbral de ADR. (1) **Poda del brief**: se quita lo duplicado, la evidencia de otra sesión, el presupuesto y el `Changelog` — determinista y sin pérdida. (2) **`raiz()`** (un sufijo si deja ≥ 4 caracteres), no un stemmer: casa por prefijo como la FTS5. Las tareas de cierre de gaps quedan cerca del tope CA-08: el test del ledger real avisa si crecen (`GOT-008`).

---

## Fase 4 — Captura episódica

**Estado**: completado (2026-09-08; revisión de dos lentes intento 1 cerrada con T-20 — ver «Revisión de dos lentes — intento 1 (Fase 4)» al final) · **Estimado**: 7,0h · **Real**: 0h humanas · 1,20h IA (est.) · 0,30h supervisión (est.) · **Coste est.**: 352 € · **Tokens est.**: 205.000

> Cierra el hueco **3** de `analysis.md` §1.4 y **revisa `ADR-010`**. Es la fase más cara, la de peor
> confianza y la única con un **contrato oficial sin verificar**: antes de arrancar hay que
> comprobar en la doc oficial si `UserPromptSubmit` trae `session_id` y **anotar la fecha**, como
> hizo `memory-health` con `SessionEnd`.
>
> ✅ **Contrato verificado el 2026-09-08** (`code.claude.com/docs/en/hooks-guide.md` §Hook input, leída
> completa; `hooks.md` llegó truncada antes de la sección del evento, pero sus tablas de exit codes y
> timeouts sí se leyeron): «Every event includes common fields like `session_id` […] `UserPromptSubmit`
> hooks get the `prompt` text». Además: **sin matcher** («always fires on every occurrence»), timeout por
> defecto **30 s** en este evento, el stdout en texto plano **se inyecta como contexto** de Claude, y un
> exit 2 «**Blocks prompt processing and erases the prompt**». De ahí las tres reglas del hook: nunca
> stdout, siempre exit 0, `timeout: 5` en `hooks.json`. El plan B del riesgo F4 (log por fecha + casar por
> mtime) **no hizo falta**. Anotado también en el docstring de `hooks/user-prompt-capture.sh`.
>
> **Entorno de ejecución de esta fase.** Windows 11 con Git Bash; el `python3` del PATH del sistema es el
> alias de la Microsoft Store, así que se creó un **venv** (`.venv/`, ignorado por git) con `python3.exe`
> real y `pytest`, y todas las puertas se corrieron con `PATH="$PWD/.venv/Scripts:$PATH"`. Con eso la
> suite de hooks pasó de 20 a 14 fallos preexistentes de Windows (`\` vs `/`, bit `+x`, `os.symlink` sin
> privilegio en el helper `sin_python3`, rutas con espacios); **ninguno introducido por esta fase** salvo el
> `sin_python3` nuevo de T-11, que cae en la misma familia. Las horas IA «reales» siguen marcadas
> `(estimado)`: el `usage-meter` no puede leer la transcripción en este entorno.

### T-11 — Hook `UserPromptSubmit`: log crudo no versionado con opt-out

- **Descripción**: hook nuevo que acumula el turno del usuario en `.claude/session-prompts-<session_id>.log`, **no versionado** (`*.log` ya está en `.gitignore`, verificado). Opt-out por etiqueta al estilo `<private>`: con la etiqueta puesta **el log no se toca** (ni mtime ni tamaño). Esto captura lo que hoy se pierde —las decisiones del usuario en la conversación— sin registrar cada `PostToolUse`, que es ruido y coste (decisión del usuario).
- **Estado**: completado
- **Tiempo humano**: est. 2,5h · real 0h (sin intervención humana en la ejecución)
- **Tiempo IA (ejec.)**: est. 0,15h · real 0,20h (estimado: el usage-meter no puede leer la transcripción en este entorno)
- **Supervisión**: est. 0,04h (≈25 % IA) · real 0,05h (estimado)
- **Previsión IA**: 55k in / 15k out tok · 0,60 €
- **Dependencias**: verificar el contrato oficial de `UserPromptSubmit` (¿llega `session_id`?) — **verificado y fechado el 2026-09-08** (cabecera de la fase)
- **Tipo**: devops
- **Archivos**: `hooks/user-prompt-capture.sh`, `hooks/hooks.json`, `tests/test_hooks_shell.py`, `agent-kits/shared/journal.py`, `agent-kits/shared/test_journal.py`
- **Changelog**: Cada turno del usuario queda en un log crudo no versionado (`.claude/session-prompts-*.log`) para la bitácora, con opt-out por turno `<private>` y por proyecto, y sin frenar nunca la sesión.
- **Verificación** (ejecutada 2026-09-08 en Windows con el venv; `CLAUDE_PLUGIN_ROOT`/`CLAUDE_PROJECT_DIR` = repo):
  - `RED: tests/test_hooks_shell.py -k "user_prompt_capture or hooks_json_registra" → rc 127 (hooks/user-prompt-capture.sh no existe) y KeyError 'UserPromptSubmit' en hooks.json; agent-kits/shared/test_journal.py -k "capture or capturas" → argparse «invalid choice: 'capture'» (exit 2) · 2026-09-08`; GREEN después.
  - `echo '{"hook_event_name":"UserPromptSubmit","session_id":"s1","prompt":"decidimos usar FTS5"}' | bash hooks/user-prompt-capture.sh; echo $?` → `exit=0`, sin stdout, y `.claude/session-prompts-s1.log` contiene `{"ts": "2026-09-08T08:37:52Z", "prompt": "decidimos usar FTS5"}`.
  - `git check-ignore -v .claude/session-prompts-s1.log` → `.gitignore:27:*.log	.claude/session-prompts-s1.log`.
  - Con `"prompt":"<private> mi clave es 1234"` → `exit=0`; `stat -c '%s %Y'` antes / después: `65 1788856672` / `65 1788856672` (**mismo tamaño y mismo mtime**); la clave no aparece en el log.
  - `echo 'no es json' | bash hooks/user-prompt-capture.sh; echo $?` → `exit=0`, sin stdout. `echo '{…}' | PATH= /usr/bin/bash hooks/user-prompt-capture.sh; echo $?` → `exit=0` (sin `python3` → silencio).
  - `pytest -q tests/test_hooks_shell.py -k "user_prompt_capture or hooks_json_registra"` → **4 passed, 1 failed** (`…sin_python3_silencio`: `os.symlink` sin privilegio en Windows, familia declarada; en CI corre). `pytest -q agent-kits/shared/test_journal.py -k "capture or capturas"` → **6 passed**.
  - `python3 scripts/lint_plugin.py` → `9 agentes · 0 errores · 3 avisos`, exit 0 (incluye el linter de `hooks.json`: el `command` referencia un fichero que existe). `git ls-files -s hooks/` → `100755 hooks/user-prompt-capture.sh` · `100644 hooks/hooks.json`.

**Criterios de aceptación**
- [x] El turno queda en el log, el fichero **no entra en git** y el hook sale **0** (spec CA-15).
- [x] Con `<private>`, el log **no se toca**: mismo tamaño y mismo mtime (spec CA-16). *Y si es el primer turno de la sesión, ni se crea.*
- [x] Payload roto, sin `session_id`, sin `python3` o sin `.claude/` escribible → **exit 0** sin emitir nada. **Nunca bloquea un turno del usuario.** *`cmd_capture` traga cualquier excepción; el hook redirige stdout/stderr a `/dev/null` y sale 0 pase lo que pase.*
- [x] El log es **rotativo o acotado**: un turno gigantesco no puede llenar el disco (tope por fichero, declarado en el hook). *`CAPTURA_MAX_CHARS = 4000` por turno, `LOG_MAX_BYTES = 256 KiB` por fichero (se conservan los últimos turnos cortando por línea) y `LOG_RETENCION_DIAS = 30` de purga de logs de otras sesiones — declarados en `journal.py` y citados en el docstring del hook.*
- [x] **No** se registra ningún `PostToolUse`: no se añade ese evento a `hooks.json`. *`test_hooks_json_registra_user_prompt_submit_y_ningun_post_tool_use_de_captura` lo afirma.*
- [x] `hooks.json` sigue en modo `100644` y el linter de hooks sigue verde (`LES-012`).

**Subtareas**
- [x] **Primero**: verificar el contrato oficial y anotar la fecha en el docstring del hook.
- [x] Test RED de los cuatro casos (feliz, opt-out, payload roto, sin escritura).
- [x] Escribir el hook y registrarlo en `hooks.json`.

**Notas**: privacidad en repo **público**: el log lleva texto del usuario → no versionado + opt-out + ningún dato real en tests. **Decisión de implementación:** el FORMATO del log y sus topes viven en `journal.py capture` —el mismo módulo que lo lee en T-12— y el hook es un envoltorio fino como `session-journal.sh`; por eso `journal.py`/`test_journal.py` entran en `Archivos`. Solo se captura en proyectos con rastro del plugin (T-fix1). Colateral en `hooks.json`: el `timeout` de `SessionEnd` sube de 20 a 45 s por T-13 (≤ 60 oficial). **Deuda declarada para T-18:** `docs/FLOWS.md`, `docs/observability.md`, `docs/CONVENTIONS.md` regla 9 y `commands/doctor.md`.

### T-12 — `SessionEnd` escribe él mismo `decisiones` y `pendientes`; `ADR-010` revisado

- **Descripción**: hoy `decisiones: []` y `pendientes: []` están vacías **siempre** en modo hook, y el `resumen` es el primer prompt del usuario recortado a 160 caracteres. El hook `SessionEnd` pasa a **escribir él mismo** la entrada del journal con `decisiones` y `pendientes` extraídas del log crudo de T-11. Esto **revisa `ADR-010`**: su restricción —«el contrato de `SessionEnd` ignora la salida de los hooks»— es **CIERTA y se conserva**; lo que cambia es la conclusión, que era demasiado fuerte: el hook no necesita *devolver* el resumen, **puede escribirlo**.
- **Estado**: completado
- **Tiempo humano**: est. 2,5h · real 0h (sin intervención humana en la ejecución)
- **Tiempo IA (ejec.)**: est. 0,16h · real 0,25h (estimado: el usage-meter no puede leer la transcripción en este entorno)
- **Supervisión**: est. 0,04h (≈25 % IA) · real 0,06h (estimado)
- **Previsión IA**: 60k in / 17k out tok · 0,67 €
- **Dependencias**: T-11
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/journal.py`, `hooks/session-journal.sh`, `agent-kits/shared/test_journal.py`, `docs/knowledge/adr/ADR-010-journal-memoria-de-sesion-determinista.md`, `docs/knowledge/README.md`, `tests/test_hooks_shell.py`
- **Changelog**: La entrada del journal trae `decisiones` y `pendientes` reales, extraídas sin modelo de los turnos del usuario; `ADR-010` queda revisado: el hook no devuelve, escribe.
- **Verificación** (ejecutada 2026-09-08; el demo en un proyecto temporal con `docs/roadmap/` como rastro):
  - `RED: agent-kits/shared/test_journal.py -k "extrae or marcadores or log_vacio or deduplica" → AttributeError: module 'journal' has no attribute 'decisiones_de' (4 failed) · 2026-09-08`; GREEN después.
  - Con 3 turnos capturados (`Revisa el ledger. Decidimos usar FTS5 para el índice, no embeddings.` · `Queda pendiente revisar la CI en Windows` · `implementa la T-03`): `python3 agent-kits/shared/journal.py write --root . --session-id s1 --reason other` → exit 0 y el frontmatter trae `resumen: "Revisa el ledger. Decidimos usar FTS5 para el índice, no embeddings."` · `resumen_por: determinista` · `turnos: 3` · `decisiones:` `- "Decidimos usar FTS5 para el índice, no embeddings."` · `pendientes:` `- "Queda pendiente revisar la CI en Windows"` (**no vacías**).
  - Repetir la misma orden → `ls docs/knowledge/journal/ | grep -v README | wc -l` = **1** (idempotente).
  - Otra sesión sin log (`--session-id s2`) → exit 0 y `turnos: 0` · `decisiones: []` (**honesto**, no inventado).
  - `python3 -m pytest -q agent-kits/shared/test_journal.py` → **30 passed, 3 failed** en Windows; los 3 fallos son los preexistentes `test_write_sin_rastro…`, `test_write_crea_entrada…`, `test_index_regenera…` (aserción `docs/knowledge/journal/...` con `/` contra `os.path.relpath` que en Windows da `\`), ya catalogados antes de esta fase. `tests/test_hooks_shell.py -k con_log_crudo` → **1 passed** (de punta a punta por los dos hooks: los turnos capturados acaban como `decisiones`/`pendientes` de la entrada que escribe `SessionEnd`, `turnos: 3`, idempotente, y otra sesión sin log sale con `decisiones: []`).
  - Lectura de `ADR-010`: frontmatter `estado: aceptada (…; revisada 2026-09-08 …)` + `revisada: 2026-09-08`; Contexto intacto; Decisión y Consecuencias con puntero; sección «Revisión» con «Lo que sigue siendo cierto» (las tres restricciones, literales), «Lo que se revisa» (T-11/T-12/T-13) y «Lo que no cambia» (no pasa a `obsoleta`). `knowledge-find.py --related ADR-010` → el estado sigue siendo `aceptada`.
  - `pytest -q tests/test_knowledge_index.py` → passed; `lint_plugin.py` → 0 errores (biyección en pie con la fila de `ADR-010` actualizada). `tests/test_knowledge_find.py` → 3 failed por CRLF del checkout de Windows, **iguales antes del cambio** (`git stash`).

**Criterios de aceptación**
- [x] Con log crudo poblado, `decisiones` y `pendientes` salen **no vacías**; idempotente por `session_id` (spec CA-17).
- [x] Con log crudo vacío, `decisiones: []` **sin inventar nada**: la degradación es honesta, no decorativa. *Y `turnos: 0` en el frontmatter dice por qué.*
- [x] El cierre de sesión **nunca se bloquea**: cualquier fallo cae a la entrada determinista de hoy con exit 0. *`capturas()` devuelve `[]` ante log ausente/ilegible y salta las líneas rotas; `main()` sigue tragando cualquier excepción con exit 0.*
- [x] `ADR-010` queda **revisado, no borrado**: la restricción del contrato sigue escrita como cierta y con su fecha; lo que se revisa es la conclusión (spec CA-20).
- [x] La fila de `ADR-010` en `docs/knowledge/README.md` refleja el cambio, y `tests/test_knowledge_index.py` (T-04) sigue verde.

**Subtareas**
- [x] Test RED de los tres casos (log poblado, log vacío, doble escritura).
- [x] Extracción determinista del log crudo (sin modelo): decisiones marcadas y pendientes. *Marcadores declarados en `DECISION_RE`/`PENDIENTE_RE` (ES/EN), a nivel de frase; deliberadamente estrechos («luego»/«later» a secas no son marcadores): mejor `[]` honesto que ruido.*
- [x] Reescribir la sección de `ADR-010` con la revisión y su fecha.

**Notas**: el ADR **no** se pone `obsoleta`: su parte cierta sigue siendo doctrina — el caso que la capa 2 (T-02) tiene que saber contar. **Colaterales justificados:** `docs/knowledge/README.md` (fila de ADR-010, la exige el último criterio) y `tests/test_hooks_shell.py` (test de punta a punta por los dos hooks) entran en `Archivos`; `session-journal.sh` gana la cadena de resolución de `session-context.sh` (gap 9 del intento 1) para no caer a la copia instalada. El `resumen` prefiere el primer turno del log (contrato oficial) al primer prompt de la transcripción (formato no oficial).

### T-13 — Resumen episódico por IA, opt-in y degradando siempre

- **Descripción**: extracción por IA de `decisiones`/`pendientes` **opt-in** vía `.claude/dev.json` → `sesion.resumen: true`, invocando el CLI en headless (`claude -p`) exactamente como ya hace `evals/run.py`. **Sin CLI, sin clave o con el opt-in apagado → degrada al journal determinista de hoy y nunca bloquea.**
- **Estado**: completado
- **Tiempo humano**: est. 1,0h · real 0h (sin intervención humana en la ejecución)
- **Tiempo IA (ejec.)**: est. 0,07h · real 0,15h (estimado: el usage-meter no puede leer la transcripción en este entorno)
- **Supervisión**: est. 0,02h (≈25 % IA) · real 0,04h (estimado)
- **Previsión IA**: 25k in / 7k out tok · 0,28 €
- **Dependencias**: T-12
- **Tipo**: devops
- **Archivos**: `hooks/session-journal.sh`, `agent-kits/shared/journal.py`, `agent-kits/shared/test_journal.py`, `hooks/hooks.json`, `agent-kits/shared/doctor.py`, `agent-kits/shared/test_doctor.py`
- **Changelog**: Resumen de sesión por IA opt-in (`sesion.resumen: true`, `claude -p --bare`) que siempre degrada a la entrada determinista si no hay CLI, clave o respuesta válida.
- **Verificación** (ejecutada 2026-09-08):
  - `python3 -m pytest -q agent-kits/shared/test_journal.py -k "resumen_ia or escribir_sesion or cli_write"` → **4 passed**, con `runner`/`which`/`environ` inyectados (aquí **nunca** se lanza `claude`, como en `evals/test_evals.py`): opt-in apagado · sin CLI · sin clave · sin turnos · guardia anti-recursión → `None` + motivo y **cero llamadas**; camino feliz → `cmd = [claude, -p, <prompt>, --bare, --output-format, json, --max-turns, 1]`, `timeout=IA_TIMEOUT`, `encoding="utf-8", errors="replace"`, `env[CUSTOM_AGENTS_JOURNAL_IA]="0"`; exit ≠ 0, stdout no JSON, `result` sin JSON, `is_error`, `TimeoutExpired`, `OSError` → degradan con su motivo; JSON envuelto en bloque de código se extrae; tipos raros se normalizan; listas acotadas a `MAX_ITEMS` y resumen a 160.
  - `RED: test_escribir_sesion_con_resumen_true… falló con 'ia' == 'manual' (resumen_por) · 2026-09-08` — el test cazó un **defecto real**: con `--enrich` manual el resumen no era de la IA pero se etiquetaba `resumen_por: ia`; corregido (solo se marca `ia` cuando el resumen lo puso la IA). GREEN después.
  - Demo (proyecto temporal, log con `Decidimos usar FTS5…`): sin `sesion.resumen` en `dev.json` → entrada determinista, exit 0, sin aviso. Con `{"sesion": {"resumen": true}}` y `env -u ANTHROPIC_API_KEY` → stderr `journal: resumen IA: sin ANTHROPIC_API_KEY (`claude -p --bare` la exige) — entrada determinista`, exit 0, `resumen_por: determinista` y las `decisiones` deterministas intactas (en esta máquina `claude` sí está en PATH: el camino «sin clave» es el que se recorre de verdad; el «sin CLI» lo cubre el test con `which` inyectado). Con `dev.json` = `{ roto` → exit 0, sin aviso (opt-in apagado por defecto).
  - `PATH= /usr/bin/bash hooks/session-journal.sh < payload.json; echo $?` → `exit=0` (sin `python3` → silencio).
  - `agent-kits/shared/test_doctor.py` → 32 passed + el fallo preexistente del bit `+x` en Windows; `/doctor` acepta `sesion.captura` y `sesion.resumen` como claves conocidas (sin ese cambio avisaría «clave desconocida»).

**Criterios de aceptación**
- [x] Los **tres** casos de degradación (opt-in apagado · sin CLI · sin clave) dan el journal determinista de hoy con **exit 0** y sin bloquear el cierre (spec CA-18). *Y dos más: sin turnos capturados no se llama al modelo, y una guardia por variable de entorno (`CUSTOM_AGENTS_JOURNAL_IA=0` en el hijo) impide la re-entrada aunque `--bare` ya salte los hooks.*
- [x] Con el opt-in activo y el CLI disponible, `decisiones`/`pendientes` salen del resumen; si el JSON de vuelta no parsea, **degrada** en vez de escribir basura.
- [x] Hay un **timeout** declarado en la llamada headless: una sesión no se queda colgada al cerrar. *`IA_TIMEOUT = 25` s; `hooks.json` sube el `timeout` del hook `SessionEnd` de 20 a 45 s (≤ 60, máximo oficial) para que quepa; y la entrada determinista se escribe ANTES de llamar, así que si Claude Code mata el hook, la bitácora ya está en disco.*
- [x] El test **no lanza `claude`**: subprocess mockeado, como `evals/test_evals.py`.
- [x] Ningún test nuevo necesita red ni clave de API. *El test de CLI real quita `ANTHROPIC_API_KEY` del entorno a propósito.*

**Subtareas**
- [x] Test RED de los tres caminos de degradación con el subprocess mockeado. *Honestidad: los tests de T-13 se escribieron en la misma pasada que el código (no hubo un rojo previo separado por camino); el rojo real que dejaron fue el defecto de `resumen_por` de arriba.*
- [x] Reutilizar el patrón de invocación de `evals/run.py` (no inventar otro). *`claude -p … --output-format json` + `runner` inyectable; aquí con `--bare` (salta hooks/plugins/MCP: sin recursión) y `--max-turns 1`.*
- [x] Timeout y captura de errores con `encoding="utf-8", errors="replace"` (`GOT-005`).

**Notas**: `ADR-010` decidió «sin resumen por IA»; esto no lo contradice: lo hace **opt-in** y lo escribe el hook, que es la parte que el ADR daba por imposible. **Por qué `--bare`:** un `claude -p` sin `--bare` cargaría el plugin y sus hooks, y el `SessionEnd` de la sesión hija volvería a entrar aquí; además `--bare` exige `ANTHROPIC_API_KEY`, que es exactamente el caso «sin clave» de CA-18. El aviso de degradación va a `stderr` **y** a `avisos` de la entrada, para que quien la lea sepa por qué es determinista. `hooks.json` y `doctor.py` entran en `Archivos` por el `timeout` y las claves nuevas de `sesion`.

### T-14 — Promoción journal → candidata a lección por la puerta de `/retro`

- **Descripción**: **la bisagra entre las dos velocidades, y lo que `claude-mem` no tiene.** Una entrada de journal cuyo patrón se repite entre sesiones se convierte en **candidata a lección** y entra por la puerta de `/retro` con `estado: propuesta` — no como lección aceptada: la curación sigue siendo la revisión de dos lentes o el usuario.
- **Estado**: completado
- **Tiempo humano**: est. 1,0h · real 0h (sin intervención humana en la ejecución)
- **Tiempo IA (ejec.)**: est. 0,05h · real 0,15h (estimado: el usage-meter no puede leer la transcripción en este entorno; incluye el rediseño de la clave de patrón)
- **Supervisión**: est. 0,01h (≈25 % IA) · real 0,04h (estimado)
- **Previsión IA**: 20k in / 6k out tok · 0,23 €
- **Dependencias**: T-12
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/journal.py`, `commands/retro.md`, `agent-kits/shared/test_journal.py`
- **Changelog**: `journal.py candidatas` propone como lección `propuesta` los patrones que se repiten en dos o más sesiones; `/retro` los muestra y solo el usuario los promueve.
- **Verificación** (ejecutada 2026-09-08; el fixture es el demo de T-12/T-13 con una tercera sesión):
  - `python3 agent-kits/shared/journal.py candidatas --root <demo>` con el patrón en **1** sola entrada (`Queda pendiente revisar la CI en Windows`) → **sin salida**, `exit=0`.
  - Tras capturar en otra sesión `vale, queda pendiente revisar la CI de Windows` y cerrarla → `Candidatas a lección desde el journal (patrón repetido en ≥ 2 entradas de sesiones distintas; nacen `propuesta` — la curación sigue siendo la revisión de dos lentes o el usuario, por /retro):` · `- [propuesta] «Queda pendiente revisar la CI en Windows» · pendientes · 2 entradas: 2026-09-08 2026-09-08-sesion.md · 2026-09-08 2026-09-08-sesion-3.md`, `exit=0` — **una** candidata, no una por entrada. `--json` → `"estado": "propuesta"`, `"entradas": 2`, evidencia con `session_id` `s1` y `s3`. `--min 3` → sin salida, exit 0.
  - `RED (diseño): la primera versión casaba el conjunto EXACTO de raíces y con esas dos frases devolvió NADA («vale» añade una raíz) · 2026-09-08` → la clave pasa a agrupación voraz por Jaccard ≥ `CANDIDATA_JACCARD = 0.6` sobre la primera formulación vista (cronológica, determinista), con test propio (`test_candidatas_agrupa_formulaciones_parecidas_por_jaccard_y_separa_las_distintas`). También hubo un rojo de datos de test: `Right contains one more item: ('decisiones', 2)` — «usar flock» no forma patrón porque `usar` es stopword del tokenizador (1 raíz < `CANDIDATA_MIN_RAICES`); el test pasó a «usar flock en el debounce» y quedó anotado.
  - `python3 -m pytest -q agent-kits/shared/test_journal.py -k candidatas` → **3 passed** (umbral 1 vs 2; misma entrada repite → cuenta una; `--min`; `--json`; orden por nº de entradas; patrón corto («ok», «sí», «tests») no cuenta; filtro `--iniciativa`; Jaccard agrupa parecidas y separa distintas; nunca `aceptada`).
  - Lectura: `commands/retro.md` paso **2-quater** describe la puerta (comando exacto, umbral ≥ 2 sesiones, evidencia, «una candidata nunca nace `aceptada`», solo se propone; si el usuario la da por buena entra en 4-bis con el mismo umbral y validación; sin python3 o sin el kit, sigue sin el paso); el antiguo segundo «2-bis» (journal) pasa a **2-ter** — nadie lo citaba por número.

**Criterios de aceptación**
- [x] Un patrón en **≥ 2** entradas de journal aparece como candidata con `estado: propuesta` (spec CA-19).
- [x] Un patrón en **1** entrada **no** se propone: el umbral está escrito y probado. *`CANDIDATA_MIN = 2`; `--min` lo sube, nunca por debajo de 1.*
- [x] Una candidata **nunca** nace `aceptada`: la puerta de curación no se puede saltar. *El script no escribe en `docs/knowledge/`: solo imprime; `/retro` la trata como propuesta del usuario.*
- [x] La candidata trae su **evidencia** (qué entradas de journal la sostienen), como cualquier entrada de `docs/knowledge/`. *fecha · fichero · `session_id` · iniciativa por entrada.*
- [x] Sin journal o con una sola entrada: **0 candidatas y exit 0**, sin ruido.

**Subtareas**
- [x] Test RED del umbral (1 vs 2 entradas) y de la deduplicación. *Honestidad: escritos en la misma pasada que el código; el rojo real fue el de diseño (clave exacta → Jaccard) descrito arriba.*
- [x] Subcomando `candidatas` en `journal.py`.
- [x] Enganchar en la salida de `/retro` como propuesta, no como escritura automática.

**Notas**: esta tarea es la razón por la que la captura sin filtro no hace falta: se captura poco y se **asciende** lo que se repite.

### T-20 — Cierre de los gaps del intento 1 (Fase 4)

- **Descripción**: corrige los 15 gaps corregibles de la revisión de dos lentes (intento 1, `36ff7f6..cf6330d`, lentes A+B+C) sobre T-11…T-14 — 1 Critical (`<private>` volvía como `resumen` por la transcripción), 5 Important (entrada truncada antes de renderizar, `--enrich` pisado por la IA, log no ignorado en consumidores y prosa sin depurar, inyección indirecta de prompt) y 9 Minor; el gap 6 (doc que contradice el código) se delega a T-18. Tabla completa en la traza «Revisión de dos lentes — intento 1 (Fase 4)».
- **Estado**: completado
- **Tiempo humano**: est. 0h (fuera del plan: línea transversal de revisión) · real 0h
- **Tiempo IA (ejec.)**: est. 0,45h · real 0,45h (estimado: el usage-meter no lee la transcripción en este entorno)
- **Supervisión**: est. 0,11h (≈25 % IA) · real 0,11h (estimado)
- **Previsión IA**: 120k in / 35k out tok · 1,36 €
- **Dependencias**: T-11…T-14 (revisión de dos lentes, intento 1)
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/journal.py`, `agent-kits/shared/test_journal.py`, `hooks/user-prompt-capture.sh`, `hooks/session-journal.sh`, `agent-kits/shared/doctor.py`, `agent-kits/shared/test_doctor.py`
- **Changelog**: Privacidad del journal de punta a punta: `<private>` ya no se filtra por la transcripción, los secretos evidentes se redactan, el log nace ignorado por git y 0600, y la entrada se escribe atómica.
- **Verificación** (ejecutada 2026-09-08, Windows + venv):
  - `RED` (reproducciones de los revisores, repetidas aquí antes de corregir): turno único `<private>` con secreto → aparecía en `resumen:`, cuerpo y `journal/README.md` · `write --draft` con `"turnos": "tres"` → entrada a **0 bytes**, exit 0 y `-2.md` en la siguiente · `--enrich` con listas manuales + IA → listas de la IA · repo consumidor: `git check-ignore` del log → exit 1 · 8 `capture` concurrentes ×3 → 8/8/**7** · `--min 0` → «≥ 0» · `--draft --ia on` → sin IA ni aviso · modo del log `0o666`.
  - Parches validados PRIMERO en una copia aislada del kit (sin tocar el árbol que las lentes leían) y después en el repo: `pytest test_journal.py` → **40 passed, 1 skipped** (+ 3 preexistentes de `\` vs `/`); **10 tests nuevos**, uno por gap con código (privado sin fuga por transcripción · redacción de secretos sin falsos positivos · `.gitignore` sembrado idempotente · log 0600 —POSIX, `skipped` en Windows— · procedencia «citas» · escritura atómica · `--enrich` manda sobre la IA · `--draft --ia` · `--min` · 24/24 turnos con 3 rondas × 8 procesos concurrentes) y `test_dev_json_sesion_captura_y_resumen…` en `test_doctor.py` (**2 passed**).
  - hooks E2E (`-k "user_prompt_capture or hooks_json_registra or session_journal"`) → **7 passed, 2 failed** (la pareja `sin_python3`) · CA-08 → **2 passed** · `lint_plugin.py` → 0 errores · `evals/check.py` → 0 errores · `test_console_encoding.py` → **281 passed** · `bash -n` OK · `session-journal.sh:22` dice `timeout: 45`.
  - Contrato re-verificado para el gap 11 (`headless.md`, 2026-09-08): «Non-interactive mode reads stdin, so you can pipe data in»; si stdin no es legible, sigue con el prompt de la línea de órdenes (degradación segura).
  - `pytest -q` completo (tests + kits + skills + evals, tras los parches) → **1310 passed, 38 failed, 1 skipped** en 9 m 16 s (puerta ≥ 1.175 ✓); 37 son las familias preexistentes de Windows (detalle en la traza) y el otro es `test_ca08` medido a mitad de la edición del ledger, verde tras el recorte (**2 passed**).

**Criterios de aceptación**
- [x] Un turno con `<private>` no aparece en la entrada del journal ni en su índice por ningún camino (log, transcripción, `--enrich`), con test de punta a punta.
- [x] La entrada previa nunca queda a 0 bytes ni a medias; la idempotencia por `session_id` sobrevive a un `render` roto o a un proceso matado a mitad (escritura atómica en `write` e `index`).
- [x] `--enrich` manda sobre la IA en `resumen`, `decisiones` y `pendientes`; la IA solo rellena lo que falta.
- [x] Los secretos evidentes se redactan antes de tocar el disco y en la entrada, con lista de falsos positivos que NO se tocan (`tokens por hora (479326)`, `password reset flow`, `clave: FTS5`).
- [x] El log no entra en git en un proyecto consumidor (`.claude/.gitignore` sembrado, idempotente, respetando lo que hubiera; `git check-ignore` en un repo temporal lo confirma) y nace `0600` en POSIX.
- [x] Dos hooks solapados de la misma sesión no pierden ningún turno (cerrojo `<log>.lock`, 24/24 en 3 rondas concurrentes).
- [x] La entrada, el bloque de `latest` que se reinyecta y el prompt de la IA declaran que los turnos son citas/datos, no instrucciones; los turnos van a `claude -p` por stdin.
- [x] `--min ≤ 0` se normaliza a 1 y la cabecera lo dice; `write --draft --ia on` recorre el camino de la IA (y degrada a la vista).
- [x] `/doctor` tiene test para `sesion.captura`/`sesion.resumen` y su pista de `sesion` mal formado nombra las claves nuevas.
- [x] T-18 tiene en `Archivos` y en un criterio propio los seis sitios de doc que hoy contradicen el código (gap 6, delegado con destino explícito).

**Subtareas**
- [x] Reproducir cada gap antes de corregir (los de B y C traían reproducción; se repitieron aquí).
- [x] Gaps 1/4/5/10/11 en `journal.py` (`redactar`, `_asegurar_gitignore`, `_abrir_log`, procedencia, stdin) — parche C; gaps 2/3/7/8/9 (`_escribir_atomico`, `manual`, `_cerrojo`, `--min`, `entrada=`) — parche B; 12/13/14/15/16 en hooks, ledger y `doctor.py`/`test_doctor.py`.

**Notas**: dos decisiones bajo el umbral de ADR. (1) **Redacción de secretos por patrón, no por entropía**: alta precisión antes que cobertura (un falso positivo borra una decisión legítima; el falso negativo lo cubren la retención corta, `<private>` y el `.gitignore` sembrado). (2) **El canal de decisiones sigue siendo el usuario** (spec CA-17): la inyección indirecta se mitiga con procedencia explícita y turnos como datos; `sesion.captura: false` la cierra del todo. Lo rebatido y el arbitraje de `scope-check` están en la traza.

---

## Fase 5 — Que la doctrina viaje

**Estado**: completado (2026-09-08; revisión de dos lentes intento 1 cerrada con T-21, junto con F6) · **Estimado**: 3,0h · **Real**: 0h humanas · 0,35h IA (est.) · 0,09h supervisión (est.) · **Coste est.**: 151 € · **Tokens est.**: 115.000

> Cierra el hueco **4** de `analysis.md` §1.4: «viaja el método y se queda el conocimiento».

### T-15 — Doctrina del plugin como assets, separada de la memoria del proyecto

- **Descripción**: separar dos cosas hoy mezcladas. **Memoria del proyecto** (`docs/knowledge/` del consumidor): sus decisiones, sus trampas, sus lecciones — **nace vacía, y eso es correcto**. **Doctrina del plugin**: las lecciones ciertas para cualquier proyecto que use estos agentes — las **9** de área «Estimación / calibración» (`LES-001…009`) son el caso obvio — que viajan como **assets del plugin** y son el fondo con el que el `evaluator` estima el primer día. Hay que **deshacer una pérdida real**: `LES-007/008/009` estaban garantizadas dentro del prompt del `evaluator` y se convirtieron en punteros a ficheros que el consumidor no tiene.
- **Estado**: completado
- **Tiempo humano**: est. 2,0h · real 0h (sin intervención humana en la ejecución)
- **Tiempo IA (ejec.)**: est. 0,16h · real 0,15h (estimado: el usage-meter no lee la transcripción en este entorno)
- **Supervisión**: est. 0,04h (≈25 % IA) · real 0,04h (estimado)
- **Previsión IA**: 60k in / 17k out tok · 0,67 €
- **Dependencias**: T-01
- **Tipo**: docs
- **Archivos**: `agent-kits/evaluator/assets/doctrina/`, `scripts/export-skills.py`, `tests/test_doctrina_viaja.py`, `agent-kits/evaluator/README.md`
- **Changelog**: Las 9 lecciones de estimación viajan con el plugin como doctrina del `evaluator` (copias byte a byte con test); la memoria del proyecto consumidor sigue naciendo vacía.
- **Verificación** (ejecutada 2026-09-08):
  - `RED: tests/test_doctrina_viaja.py → 8 failed (FileNotFoundError: agent-kits/evaluator/assets/doctrina/; sin criterio en el README; NO_VIAJA sin doctrina; --doctrina: unrecognized arguments) · 2026-09-08`; GREEN después → **8 passed**.
  - `ls agent-kits/evaluator/assets/doctrina/ | wc -l` → **9** (`LES-001…009`, todas `tipo: leccion`, `area: Estimación / calibración`, `estado: aceptada`); `diferencias(DOCTRINA, LESSONS)` → `[]` y el comprobador caza un mutante («difiere», «sin original»).
  - `python3 scripts/export-skills.py --out <tmp> && --check <tmp>` → `108 ficheros · 0 problema(s)`, exit 0; `NO_VIAJA` declara `agent-kits/evaluator/assets/doctrina/` como lo que **no** viaja en el paquete portable (ver Notas). `python3 scripts/lint_plugin.py` → `9 agentes · 0 errores · 3 avisos`.

**Criterios de aceptación**
- [x] Las **9** lecciones de estimación están disponibles como doctrina del plugin.
- [x] La memoria del proyecto **sigue naciendo vacía**: nada se copia al `docs/knowledge/` del consumidor al instalar. *`test_ca21_…` lo afirma: tras `--doctrina` el consumidor sigue con solo `src/`.*
- [x] El criterio de qué es doctrina está **escrito** («¿es cierta para cualquier proyecto que use estos agentes?») y aplicado entrada por entrada. *`agent-kits/evaluator/README.md` §Doctrina: tabla con las 9 que sí y las 5 (`LES-010…014`) + ADR/GOT que no, con su porqué; el test exige que las 14 estén nombradas.*
- [x] **Una sola copia**; si la copia es inevitable, un test la compara **byte a byte** (el patrón que el repo ya usa con las copias manuales). *La copia es inevitable: `docs/` no llega a una instalación «copiar como `.claude/`» y `agent-kits/` sí (las dos formas de instalar).*
- [x] El paquete portable (`export-skills.py`) declara qué viaja y qué no, y su `--check` sigue verde.

**Subtareas**
- [x] Decidir entrada por entrada cuáles de las 9 son doctrina universal.
- [x] Colocar los assets y atarlos con test.
- [x] Actualizar qué viaja en el paquete portable y su README ES/EN. *Fila nueva en `NO_VIAJA` (la tabla bilingüe del README del paquete se genera de ahí).*

**Notas**: `analysis.md` §1.4-4 lo llama «se cambió una garantía por una intención». Aquí se deshace **sin volver a meter prosa en los prompts** — eso lo ata T-16. **Desvío declarado respecto a la Verificación planificada** («la doctrina figura en lo que viaja»): el paquete portable es «solo skills» y no lleva al `evaluator`, así que la doctrina se declara en `NO_VIAJA` (viaja con el plugin y con el agente, no con ese paquete) — «declara qué viaja y qué no» se cumple diciendo que no. `agent-kits/evaluator/README.md` entra en `Archivos` porque el criterio escrito necesita un sitio y la carpeta de assets debe contener exactamente las 9.

### T-16 — El `evaluator` estima con ese fondo sin engordar su prompt

- **Descripción**: `knowledge-find.py --doctrina` lee los assets del plugin (y no la memoria del proyecto), y el `evaluator` la consulta el primer día. La restricción dura: **sin volver a meter prosa en los prompts**, atada a `wc -c agents/evaluator.md` ≤ **15.513 bytes** (el valor de hoy).
- **Estado**: completado
- **Tiempo humano**: est. 1,0h · real 0h (sin intervención humana en la ejecución)
- **Tiempo IA (ejec.)**: est. 0,08h · real 0,20h (estimado: el usage-meter no lee la transcripción en este entorno)
- **Supervisión**: est. 0,02h (≈25 % IA) · real 0,05h (estimado)
- **Previsión IA**: 30k in / 8k out tok · 0,32 €
- **Dependencias**: T-15
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/knowledge-find.py`, `agents/evaluator.md`, `tests/test_doctrina_viaja.py`, `agent-kits/shared/knowledge-check.md`, `tests/test_knowledge_find.py`
- **Changelog**: `knowledge-find.py --doctrina` lee la doctrina del plugin sin tocar la memoria del proyecto (cada acierto dice de dónde viene) y el prompt del `evaluator` adelgaza a 15.024 bytes.
- **Verificación** (ejecutada 2026-09-08):
  - En un árbol **sin** `docs/knowledge/` (solo `src/`): `knowledge-find.py --doctrina --area estimacion --limit 0 --root <árbol>` → **9 líneas** `LES-00N · aceptada · Estimación / calibración · <frase de la lección> · doctrina/LES-00N-…`, exit 0. Sin `--doctrina`: **0 líneas**, exit 0, y el árbol sigue con solo `src/` (nada sembrado).
  - `python3 -c "print(len(open('agents/evaluator.md','rb').read().replace(b'\r\n', b'\n')))"` → **15.024** ≤ 15.513 (spec CA-22). *Medida en LF: el checkout de Windows tiene CRLF y `wc -c` daba 15.642 ANTES de tocar nada — el fichero no había crecido, eran los CR; el test normaliza a LF.*
  - `python3 evals/check.py` → `135 casos · 0 errores` (la `description` del `evaluator` no se toca). `python3 scripts/lint_plugin.py` → 0 errores.
  - `python3 -m pytest -q tests/test_knowledge_find.py` → **69 passed, 3 failed** de 72 (los 3 son los preexistentes de CRLF en `--show`; la cifra «95 passed» que figuró aquí era la de una ejecución combinada de cuatro ficheros — gap A2 del intento 1, corregida en T-21); los dos tests de **contrato JSON** (`test_el_esquema_json_es_contrato`, `test_enrutado_respeta_limit_tipo_y_el_esquema…`) y los de `--show`/`--related` JSON se actualizaron **a propósito** con las claves nuevas `corpus` (todas las capas) y `origen` (por entrada), sin cambiar `version` (claves añadidas, ninguna renombrada; `task-brief.py`/`session-context.sh` las ignoran — `tests/test_memory_path.py` sigue verde). `tests/test_doctrina_viaja.py` → 8 passed (incluye la instalación parcial: kit sin `agent-kits/evaluator/` → 0 aciertos, aviso por stderr, exit 0; con `CLAUDE_PLUGIN_ROOT` la encuentra).
  - `pytest -q` completo antes de comitear F5-F6 → 1329 passed, 38 failed: la cifra tapaba 4 fallos nuevos de `tests/test_console_encoding.py` (esa suite solo descubre scripts **versionados**, y `retro-gate.py` aún no lo estaba — gaps A1/B2, corregidos en T-21). Cifra tras T-21: ver la traza de F5-F6.

**Criterios de aceptación**
- [x] `--doctrina --area estimacion` devuelve las **9** lecciones en un proyecto sin memoria propia, exit 0; y sin `--doctrina`, **0 aciertos** con exit 0 (spec CA-21).
- [x] `wc -c agents/evaluator.md` **no supera los 15.513 bytes de hoy** (spec CA-22): la garantía vuelve **sin** prosa nueva en el prompt. *15.024 en LF; el bloque de ~1.060 bytes que apuntaba a `LES-007/008/009` «migradas… léelas de ahí… cuando el proyecto tenga docs/knowledge» se sustituye por una invocación de ~600.*
- [x] La doctrina y la memoria del proyecto **no se mezclan** en la misma salida sin distinguirse: cada acierto dice de dónde viene. *`ruta_corta` `doctrina/…` vs `lessons/…`; JSON `corpus`/`origen`; `--doctrina` no lee la memoria del proyecto.*
- [x] El caso literal de `agent:evaluator` en `evals/` sigue atado a la `description` real (`check.py` regla 4).

**Subtareas**
- [x] Bandera `--doctrina` con localización del asset por `CLAUDE_PLUGIN_ROOT` + `find` (regla 5). *Relativa al kit (`agent-kits/shared/../evaluator/assets/doctrina`, rutas relativas entre sí) y `CLAUDE_PLUGIN_ROOT` como segundo candidato; sin `find`: `agent-kits/` viaja entero en las dos instalaciones.*
- [x] Sustituir el puntero del prompt por la invocación, sin añadir prosa.
- [x] Test del tope de bytes del prompt.

**Notas**: si el prompt tuviera que crecer, la tarea **falla** su criterio: es la restricción que hace que esto no sea volver atrás. Sin README que aporte titular, la doctrina toma como titular la **primera frase en negrita** de la lección (antes salía «evaluator», el encabezado). `agent-kits/shared/knowledge-check.md` (fila del `evaluator`: memoria del proyecto **y** doctrina) y `tests/test_knowledge_find.py` (contrato JSON) entran en `Archivos` por lo dicho en la Verificación.

---

## Fase 6 — Cerrar el bucle

**Estado**: completado (2026-09-08; T-18 cerrado con las transiciones de estado tras la revisión de dos lentes de F5-F6 — el cierre declarado de la iniciativa espera a la puerta de retro, paso 8) · **Estimado**: 3,0h · **Real**: 0h humanas · 0,95h IA (est.) · 0,24h supervisión (est.) · **Coste est.**: 151 € · **Tokens est.**: 145.000

> **Va al final por dependencias, pero el criterio de éxito de la spec NO se cumple sin ella**
> (CA-25). `analysis.md` la declara **condición previa**: «mientras la tubería que convierte
> experiencia en lección esté parada, reforzar la recuperación es afilar un grifo sin agua». Hoy:
> **15 días parado, 13 iniciativas cerradas** después de la última fila de `CALIBRATION.md`. Parar
> aquí es entrega **incompleta**, no «al 83 %».

### T-17 — `/retro` se dispara al cerrar una iniciativa

- **Descripción**: que `/retro` deje de ser «un comando que alguien recuerda». Al cerrar una iniciativa (plan `completado`), la puerta de cierre **exige** la retro y su fila en `CALIBRATION.md` — el mismo patrón que el repo ya usa con `qa-gate` y `ledger-lint`: una puerta, no un aviso ignorable (`LES-012`: «un aviso que se puede ignorar se ignorará»).
- **Estado**: completado
- **Tiempo humano**: est. 1,5h · real 0h (sin intervención humana en la ejecución)
- **Tiempo IA (ejec.)**: est. 0,15h · real 0,20h (estimado: el usage-meter no lee la transcripción en este entorno)
- **Supervisión**: est. 0,04h (≈25 % IA) · real 0,05h (estimado)
- **Previsión IA**: 55k in / 17k out tok · 0,64 €
- **Dependencias**: T-10, T-14
- **Tipo**: docs
- **Archivos**: `commands/retro.md`, `commands/dev-cycle.md`, `agent-kits/shared/doctor.py`, `agent-kits/shared/retro-gate.py`, `agent-kits/shared/test_retro_gate.py`
- **Changelog**: La retro es una puerta del cierre de `/dev-cycle` (`retro-gate.py`: `retro.md` + fila en `CALIBRATION.md`, exit 0 obligatorio), no un comando que alguien recuerda.
- **Verificación** (ejecutada 2026-09-08):
  - `RED: agent-kits/shared/test_retro_gate.py → error de recolección (retro-gate.py no existe) · tras escribir el script, 4 failed: la raíz se tomaba del cwd y no de la carpeta de la iniciativa (CALIBRATION.md del repo en vez del del proyecto temporal) · 2026-09-08`; corregido (`raiz_de(carpeta)`) → **11 passed** (un rojo más fue de datos de test: dos casos normalizaban al mismo directorio temporal).
  - Tras la revisión (T-21, gap B1 Critical): el contrato de `retro_ok` se rehízo desde las **7 retros reales** del repo (título `# Retro — …`, sin frontmatter — la primera versión exigía un frontmatter que `/retro` nunca escribe): `retro-gate.py docs/roadmap/2026-08-12-sdd-hardening` → `✅ retro.md con título y cuerpo` · `✅ fila del 2026-08-12 para \`sdd-hardening\`` · **exit 0**; las 7 dan exit 0 (`test_las_retros_reales_del_repo_cumplen_el_contrato`, parametrizado sobre `docs/roadmap/*/retro.md`).
  - `python3 agent-kits/shared/retro-gate.py docs/roadmap/2026-09-04-memory-retrieval` → `❌ retro.md no existe` · `❌ sin fila para \`memory-retrieval\` en docs/roadmap/CALIBRATION.md` · `ℹ️ el ledger está \`en-progreso\`…` · `❌ Puerta CERRADA — falta: retro.md, fila en CALIBRATION.md. Ejecuta \`/retro docs/roadmap/2026-09-04-memory-retrieval\`…`, **exit 1** (la propia iniciativa es el primer caso: no se declarará cerrada hasta pasar por aquí).
  - `python3 agent-kits/shared/doctor.py | grep -i calibrac` → `⚠️ calibración (CALIBRATION.md) · última fila 2026-08-20: 19 días sin fila y 15 iniciativa(s) cerrada(s) después sin retro: adversarial-review, debt-cleanup, deterministic-guardrails, live-visibility, activation-reliability, distribution …` (el análisis decía 15 días / 13; hoy 19 / 15) y el arreglo nombra la puerta.
  - Lectura: `commands/dev-cycle.md` Fase 6 paso 8 («Retro — PUERTA, no aviso»: comando exacto, exit 0 obligatorio, qué pasa con exit 1, degradación sin python3) y el cierre ya no «ofrece» la retro; `commands/retro.md` se declara puerta en su cabecera y muestra las candidatas (paso 2-quater, T-14). `python3 evals/check.py` → `135 casos · 0 errores` (la `description` de `/retro` no cambia); `lint_plugin.py` → 0 errores.

**Criterios de aceptación**
- [x] El cierre de iniciativa **exige** la retro y su fila en `CALIBRATION.md` (spec CA-23).
- [x] Es una **puerta**, no un aviso: el ritual de cierre no se puede declarar completo sin ella. *Script con exit code, como `qa-gate`/`ledger-lint`; la prosa decide cuándo llamarlo, el script el veredicto.*
- [x] `/doctor` cuenta cuántas iniciativas cerradas están sin fila y desde cuándo. *Lo hacía desde T-10; aquí su arreglo cita la puerta.*
- [x] La `description` de `/retro` y su caso literal en `evals/` siguen coherentes (`check.py` regla 4).
- [x] No se automatiza **escribir** la retro: se automatiza **exigirla**. Las causas de desviación las escribe quien las conoce. *`retro-gate.py` no escribe nada.*

**Subtareas**
- [x] Añadir la retro al ritual de cierre de `/dev-cycle`.
- [x] Contar en `/doctor` las cerradas sin fila.
- [x] Ajustar `commands/retro.md` para consumir las candidatas de T-14. *Hecho en T-14 (paso 2-quater); aquí se enlaza desde la cabecera.*

**Notas**: esta tarea es la que hace que las horas **humanas** de este presupuesto dejen de ser una estimación sin validar: sin retro, `CALIBRATION.md` no gana su primera fila con horas humanas reales. **Desvío declarado:** el plan no preveía script; una puerta sin exit code es un aviso ignorable (`LES-012`, regla de determinismo de CONVENTIONS), así que `retro-gate.py` + tests entran en `Archivos`. La puerta acepta carpeta con fecha, `<fecha>-<slug>` o slug (error de uso si es ambiguo) y deriva la raíz de la carpeta de la iniciativa, no del cwd.

### T-18 — Doc ES/EN y las entradas de `docs/knowledge/` que salen de aquí

- **Descripción**: cerrar la iniciativa con su documentación y su memoria: la regla nueva en `docs/CONVENTIONS.md` **y su espejo EN**, un ADR de las tres capas (fuente de verdad en git, índice como caché, grafo curado en vez de cronología), la lección que salga del ciclo, sus filas en el índice de `docs/knowledge/README.md`, y las transiciones de estado de los artefactos de esta carpeta.
- **Estado**: completado
- **Tiempo humano**: est. 1,5h · real 0h (sin intervención humana en la ejecución)
- **Tiempo IA (ejec.)**: est. 0,15h · real 0,35h (estimado: el usage-meter no lee la transcripción en este entorno; incluye la deuda de doc de F3-F4)
- **Supervisión**: est. 0,04h (≈25 % IA) · real 0,09h (estimado)
- **Previsión IA**: 55k in / 18k out tok · 0,67 €
- **Dependencias**: T-17
- **Tipo**: docs
- **Archivos**: `docs/CONVENTIONS.md` + espejo EN, `docs/knowledge/README.md`, `docs/knowledge/adr/` (ADR-013), `docs/knowledge/lessons/` (LES-015), los cuatro artefactos de `docs/roadmap/2026-09-04-memory-retrieval/`, `docs/roadmap/README.md`, `docs/observability.md` + EN, `docs/FLOWS.md` + EN, `docs/INSTALL.md` + EN, `docs/README.md` + EN, `CLAUDE.md`, `commands/doctor.md`, `commands/setup.md`, `agent-kits/shared/README.md`, `docs/agents/evaluator.md`
- **Changelog**: La doc ES/EN describe la captura del turno, el resumen IA opt-in, la doctrina y la retro como puerta; ADR-013 fija las tres capas de la memoria y LES-015 la lección de privacidad de F4.
- **Verificación** (doc ejecutada 2026-09-08; las transiciones de estado, al cerrar):
  - `pytest -q` de índice de knowledge, índice del roadmap, mermaid, badges, manifiestos y doctrina → **62 passed** (34 filas ↔ 34 ficheros con «Área»; `ADR-013`/`LES-015` nacen `propuesta`; 32 diagramas OK con los nodos nuevos en ES y EN). `knowledge-find.py --show ADR-013` y `--related LES-015` → exit 0.
  - `grep -c "^#" docs/CONVENTIONS.md` y `docs/en/CONVENTIONS.md` → **11 y 11** (misma estructura: lo nuevo son viñetas dentro de las reglas 9 y 10).
  - `grep -rn "Sin resumen por IA\|timeout: 20\|No AI summary" docs/ CLAUDE.md commands/ agent-kits/shared/README.md` (sin `docs/roadmap/`) → **solo `ADR-010:37`**, registro histórico de la decisión original (su §Revisión ya dice 45).
  - `lint_plugin.py` → 0 errores · `evals/check.py` → 0 errores (la `description` de `/doctor` gana «memoria técnica» sin tocar sus frases literales) · `ledger-lint.py` → 0 incoherencias · 0 avisos.
  - Cierre (2026-09-08, tras la revisión de F5-F6): `evaluation.md` e `improvement-plan.md` → `completado`; este ledger → `completado`; fila de `docs/roadmap/README.md` con el resultado real (`tests/test_roadmap_index.py` verde); `spec.md` → `implementada` el 2026-09-08 tras `retro-gate.py` → `✅ Puerta ABIERTA`, exit 0 (retro + fila; antes: `❌ retro.md no existe · ❌ sin fila`, exit 1).

**Criterios de aceptación**
- [x] La regla nueva está en `docs/CONVENTIONS.md` **y** en `docs/en/CONVENTIONS.md` (spec CA-24). *Alcance verificado:* `docs/en/` espeja solo los 5 documentos de producto — **no** el roadmap —, así que estos cuatro artefactos no llevan espejo EN, y eso no es una omisión. *Regla 10: viñeta «Doctrina del plugin» + reglas (8)-(11) del journal; regla 9: `sesion.captura`/`sesion.resumen`.*
- [x] Las entradas nuevas de `docs/knowledge/` tienen **su fila con «Área»** en el índice, en el mismo cambio (regla del índice) y con T-04 verde.
- [x] La fila de la iniciativa está **dentro** de la tabla de `docs/roadmap/README.md` y `tests/test_roadmap_index.py` lo confirma. *(El texto de la fila se actualiza con el resultado real al cerrar.)*
- [x] Los estados de `spec.md`, `evaluation.md`, `improvement-plan.md` y de este ledger se actualizan al cerrar, no antes. *Hecho el 2026-09-08 tras la revisión: evaluación, plan y ledger `completado`; la spec pasó a `implementada` al abrir la puerta de retro (paso 9, el que T-21 fijó).*
- [x] **`CHANGELOG*.md` no se toca a mano**: lo genera la skill `changelog-sync` desde este ledger cerrado.
- [x] El ADR nuevo dice **qué se descartó y por qué** (embeddings, capturar todo, retirar el journal), no solo lo elegido. *ADR-013: las tres + «un almacén propio como fuente».*
- [x] **Deuda de doc de las Fases 3 y 4 saldada** (revisión F4, Lente A gap 6): `observability`, `FLOWS` y `CONVENTIONS` (ES/EN), `CLAUDE.md`, `commands/doctor.md` + filas de `docs/README.md`/`docs/en/README.md`, `INSTALL` (ES/EN) + `commands/setup.md`, `agent-kits/shared/README.md`. Verificación: el `grep` de arriba → solo `ADR-010:37` (histórico).

**Subtareas**
- [x] ADR de las tres capas con las alternativas descartadas (`ADR-013`).
- [x] Lección del ciclo (con evidencia, no impresión): `LES-015`, del gap 1 de la revisión de F4.
- [x] Espejo ES/EN de la regla y filas del índice.
- [x] Transiciones de estado y fila del roadmap con el resultado real.

**Notas**: el `- **Changelog**:` lo escribe quien cierra (`ADR-012`). `docs/agents/evaluator.md` y las dos entradas nuevas entran en `Archivos`; el README del kit compartido gana las filas que faltaban de `knowledge-find.py` (deuda de T-01) y `retro-gate.py`.

### T-21 — Cierre de los gaps del intento 1 (Fases 5-6)

- **Descripción**: corrige los 10 gaps de la revisión de dos lentes (intento 1, `853ea8d..97afbe3`, lentes A+B+D) sobre T-15…T-18 — 2 Critical (`retro-gate.py` exigía un frontmatter que `/retro` nunca escribe, así que la puerta no habría abierto para ninguna retro real y su arreglo la volvía a cerrar; el script no estaba en `MODOS` de `tests/test_console_encoding.py` → 4 rojos en CI), 2 Important (titular de la doctrina desde cualquier negrita del fichero, frontmatter incluido; cifras de Verificación de T-16 no reproducibles) y 6 Minor (FLOWS ES/EN sin el paso 8; `sesion.memoria` fuera de la regla 9 y de `CLAUDE.md`; la puerta corría después de las transiciones que vigila; carpeta con `tasks.md` fuera de `docs/roadmap/` juzgada contra otro proyecto; `----` aceptado como cierre de frontmatter; aviso inútil con carpeta de doctrina vacía). Tabla completa en la traza «Revisión de dos lentes — intento 1 (Fases 5-6)».
- **Estado**: completado
- **Tiempo humano**: est. 0h (fuera del plan: línea transversal de revisión) · real 0h
- **Tiempo IA (ejec.)**: est. 0,40h · real 0,40h (estimado: el usage-meter no lee la transcripción en este entorno)
- **Supervisión**: est. 0,10h (≈25 % IA) · real 0,10h (estimado)
- **Previsión IA**: 110k in / 30k out tok · 1,23 €
- **Dependencias**: T-15…T-18 (revisión de dos lentes, intento 1)
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/retro-gate.py`, `agent-kits/shared/test_retro_gate.py`, `agent-kits/shared/knowledge-find.py`, `tests/test_doctrina_viaja.py`, `tests/test_console_encoding.py`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `CLAUDE.md`, `commands/dev-cycle.md`, `commands/retro.md`
- **Changelog**: La puerta de retro acepta el formato real de las retros y entra en la suite de codificación; el titular de la doctrina sale del cuerpo; la spec pasa a `implementada` solo con la puerta abierta.
- **Verificación** (ejecutada 2026-09-08):
  - `RED` (reproducciones de los revisores, repetidas aquí): `retro-gate.py docs/roadmap/2026-08-12-sdd-hardening` → `❌ retro.md sin frontmatter`, exit 1 (ídem las otras 6 retros reales) · `pytest tests/test_console_encoding.py -k retro` → 4 failed (`KeyError: 'agent-kits/shared/retro-gate.py'`) · doctrina sintética con `fuente: x (**medido**)` → `titular: "medido"`; con `300**k**` → `titular: "k"` · carpeta suelta con `tasks.md` + `--root` ajeno → exit 0 con `comando: /retro docs/roadmap/suelta` (inexistente) · `"---\nr: 1\n…\n----\n"` → aceptado como frontmatter cerrado.
  - GREEN: `pytest -q agent-kits/shared/test_retro_gate.py tests/test_doctrina_viaja.py tests/test_console_encoding.py tests/test_memory_path.py tests/test_mermaid_blocks.py` → **326 passed** (5 tests nuevos: formato real, las 7 retros reales parametrizadas, carpeta suelta = exit 2, `----`/solo títulos/sin título, titular por cuerpo, carpeta de doctrina vacía); `tests/test_knowledge_find.py` → 69 passed + 3 CRLF preexistentes; `lint_plugin.py` → 0 errores; `evals/check.py` → 0 errores; `python3 -W error knowledge-find.py --doctrina …` → sin avisos (un `DeprecationWarning` de `re.split` con `maxsplit` posicional, aflorado al probar, corregido).
  - Las 7 retros reales → `retro-gate.py` **exit 0**; `memory-retrieval` → exit 1 (sin retro: es la propia puerta de cierre de esta iniciativa); carpeta con `tasks.md` fuera de `docs/roadmap/` → exit 2 con el motivo.
  - Lectura: `commands/dev-cycle.md` pasos 6-9 en el orden nuevo; `docs/FLOWS.md`/`docs/en/FLOWS.md` con el nodo del paso 8 (`test_mermaid_blocks` → 32 diagramas OK); `grep -rn "sesion.memoria" docs/CONVENTIONS.md docs/en/CONVENTIONS.md CLAUDE.md` → 3 aciertos.
  - `pytest -q` completo (tests + kits + skills + evals, tras T-21) -> **1349 passed, 37 failed, 1 skipped** en 7 m 33 s (puerta >= 1.175 OK): los 37 son exactamente las familias preexistentes de Windows (ver la traza de F4); ninguno fuera de ellas.

**Criterios de aceptación**
- [x] La puerta abre con cualquiera de las 7 retros reales del repo y con el formato que `/retro` seguirá escribiendo (título; frontmatter opcional y cerrado); no abre con fichero vacío, solo títulos, sin título o con frontmatter sin cerrar.
- [x] La puerta solo juzga carpetas bajo `docs/roadmap/` de SU proyecto (exit 2 fuera) y está en `MODOS` de la suite de codificación.
- [x] El titular de la doctrina sale del bullet en negrita del cuerpo; nunca del frontmatter ni de una negrita inline; sin bullet, la primera frase del cuerpo.
- [x] El ritual de cierre pone el ledger en `completado` antes del changelog y de la retro, y la spec en `implementada` solo con la puerta abierta; FLOWS ES/EN lo dibujan.
- [x] `sesion.memoria` documentado en la regla 9 (ES/EN) y en el mapa de configs de `CLAUDE.md`.
- [x] Las cifras de Verificación de T-16 son reproducibles (69/3 de 72; la de la suite completa, re-medida tras T-21).

**Subtareas**
- [x] Reproducir cada gap antes de corregir (todos traían reproducción; se repitieron).
- [x] Gaps B1/B4/B5 en `retro-gate.py` + tests con el formato real y las retros reales; B2/A1 en `MODOS`; B3/B6 en `knowledge-find.py` + tests; A3/A4/A5 en FLOWS, CONVENTIONS, CLAUDE.md, dev-cycle y retro.

**Notas**: la lección de este intento es la misma que la de F4 y ya está escrita (`LES-015`): probé la puerta contra mi fixture y contra una iniciativa **sin** retro, nunca contra una retro real; la Lente B sí lo hizo. Por eso el test nuevo parametriza sobre `docs/roadmap/*/retro.md`: el contrato lo fijan los datos, no el fixture.

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

---

## Revisión de dos lentes — intento 1 (Fase 4): 16 gaps (1 Critical, 6 Important, 9 Minor) → 15 corregidos en T-20, 1 delegado a T-18; 0 rebatidos

Lentes: **A + B + C** (`review-lens-select.py --base 36ff7f6` → `lente_c: true` por ruta `hooks/session-journal.sh`, `lente_d: false`), tres agentes `reviewer` en paralelo (`opus`/`high`, frontmatter) sobre `git diff 36ff7f6...cf6330d`. `scope-check` → 12 en alcance (los 11 del plan + `test_doctor.py`, añadido a T-13 por el gap 16); «fuera»: los 3 sin seguimiento preexistentes ajenos a la iniciativa y `CONTINUE-HERE.md` (traspaso de sesión, fuera del roadmap por diseño) — arbitrado: ninguno forma parte del diff de la fase. Cada gap se reprodujo antes de corregir; las cifras Critical/Important se fusionaron cuando B y C señalaban lo mismo.

| # | Grado | Lente | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|---|
| 1 | **Critical** | B+C | `<private>` protegía el log pero `draft` caía a `primer_prompt(transcript)`: el turno privado volvía como `resumen` de una entrada versionada y al índice | T-11/T-12 | `primer_prompt` salta los mensajes con la etiqueta (en cualquier parte) y redacta el resto | `test_private_no_resucita_desde_la_transcripcion` |
| 2 | Important | B | `write` abría en `"w"` antes de renderizar: `render` roto → entrada a 0 bytes, exit 0, idempotencia rota (`-2.md`); disparador nuevo `int(turnos)` | T-13 | render antes de abrir + `_escribir_atomico` (temporal + `os.replace`) en `write` e `index`; `_entero` tolerante | `test_write_no_trunca_la_entrada_previa_si_el_render_falla_y_escribe_atomico` |
| 3 | Important | B | La IA pisaba `decisiones`/`pendientes` de `--enrich` (solo `resumen` estaba protegido) | T-13 | `draft` anota `manual: [...]`; `escribir_sesion` no toca lo manual | `test_enrich_manual_manda_sobre_la_ia_tambien_en_las_listas` |
| 4 | Important | B+C | Log crudo ignorado solo por el `.gitignore` de ESTE repo; prosa cruda del usuario (8×200 chars por lista) a un fichero versionado por diseño, sin depuración | T-11/T-12 | `redactar` (secretos evidentes) en `capture`, `primer_prompt`, `--enrich` y respuesta IA; `_asegurar_gitignore` siembra `.claude/.gitignore` con `session-prompts-*` | `test_redacta_secretos_evidentes…`, `test_capture_siembra_gitignore…` |
| 5 | Important | C | Inyección indirecta de prompt con persistencia: texto pegado con marcador → «decisión» → `additionalContext` de la sesión siguiente y prompt de la IA | T-12/T-13 | Procedencia explícita en la entrada y en `latest`; turnos como DATOS entre `<turnos>…</turnos>` por stdin. **Residual = diseño** (spec CA-17; opt-out `sesion.captura`) — anotado en T-20 | `test_la_entrada_y_el_contexto_reinyectado_declaran_que_son_citas` |
| 6 | Important | A | Seis sitios de doc contradicen el código («Sin resumen por IA», `timeout 20`, `dev.json` sin `sesion.captura/resumen`, tabla de hooks) y T-18 no los tenía en `Archivos` | T-18 | **Delegado con destino**: T-18 gana los ficheros en `Archivos` y un criterio con la lista y su `grep` de verificación | ledger T-18 |
| 7 | Minor | B | Append sin cerrojo + rotación leer-reescribir: 8 `capture` solapados → 7 líneas | T-11 | `_cerrojo` (`<log>.lock`, `fcntl`/`msvcrt` no bloqueante ≤ 3 s) alrededor de append+rotación; purga de `.lock` | `test_capture_concurrente_no_pierde_turnos` (24/24) |
| 8 | Minor | B | `candidatas --min 0/-5` anunciaba «≥ 0/−5» pero aplicaba `max(1,·)` | T-14 | Normalización única en `cmd_candidatas` | `test_candidatas_min_menor_que_uno…` |
| 9 | Minor | B | `write --draft --ia on` no-op silencioso | T-13 | La rama `--draft` pasa por `escribir_sesion(entrada=…)` | `test_write_draft_tambien_honra_ia` |
| 10 | Minor | C | Log `0644` (medido `0o666` antes de umask) | T-11 | `_abrir_log` con `os.open(…, 0o600)` | `test_capture_crea_el_log_solo_legible_por_el_usuario` (POSIX) |
| 11 | Minor | C | Turnos del usuario por argv a `claude -p` (visibles en `ps`) | T-13 | Instrucción en `-p`, turnos por stdin (`input=`); contrato `headless.md` verificado 2026-09-08 | `test_resumen_ia_tres_degradaciones…` (`kw["input"]`) |
| 12 | Minor | A | `session-journal.sh:22` decía `timeout: 20` y `:31` 45 | T-13 | Línea 22 → 45 | `grep -n "timeout: 45"` |
| 13 | Minor | A | Cifras de briefs de T-19 no reproducibles tras el recorte | T-19 | Línea re-medida (Windows) con la nota de que la medida incluye la ruta absoluta de `knowledge-find.py` | `task-brief.py` |
| 14 | Minor | A | La Fase 4 apuntaba a una traza inexistente | Fase 4 | Esta sección | — |
| 15 | Minor | A | Sin cifra de `pytest -q` completo en la fase | Fase 4 | Pegada en T-20 y aquí | `pytest -q` |
| 16 | Minor | A | Claves `sesion.captura/resumen` en `doctor.py` sin test; `test_doctor.py` fuera de `Archivos` de T-13 | T-13 | Test nuevo + pista de `sesion` con las claves + `Archivos` | `test_dev_json_sesion_captura_y_resumen_son_vocabulario_conocido` |

**Verificado OK por las lentes (sin cambios):** `session_id` hostil neutralizado dentro de `.claude/`; el hook nunca emite stdout ni sale ≠ 0; `subprocess.run` con lista y sin `shell=True`; `ANTHROPIC_API_KEY` no viaja a logs ni avisos; guardia anti-recursión y timeouts; `_yaml_str` entrecomilla todo lo del usuario; topes/rotación/purga; extracción determinista y `[]` honesto; degradaciones de CA-18; agrupación determinista de candidatas y «nunca `aceptada`»; ADR-010 revisado sin borrar; alcance limpio (11 ficheros del plan). La cadena de resolución `CLAUDE_PROJECT_DIR → find` es el patrón preexistente de `session-context.sh` (no introducido).

**Rebatido con evidencia (no cuenta como gap):** «una IA que devuelve `[]` no puede vaciar las listas deterministas» (A, fuera de lente) — intencional: las deterministas son citas del usuario con marcador; el silencio del modelo no prueba ausencia. «`_purgar_logs` hace un `listdir` por turno» (A) — un `listdir` de `.claude/` por prompt, sin efecto medible.

**Aceptado como diseño, no como deuda:** el journal versiona citas del usuario por defecto (ADR-010 + spec CA-17), con tres controles nuevos (redacción, `.gitignore` sembrado, procedencia) y dos opt-out (`<private>` por turno, `sesion.captura`/`sesion.journal` por proyecto). T-18 debe documentar qué se captura y cómo apagarlo (criterio nuevo).

Tras T-20: `test_journal.py` → **40 passed, 1 skipped** (+ 3 fallos preexistentes de `\` vs `/`) · hooks E2E **7 passed** (+ 2 `sin_python3`) · `test_doctor -k sesion` **2 passed** · CA-08 **2 passed** · `lint_plugin` 0 errores · `evals/check` 0 errores · `ledger-lint` 0 incoherencias · `pytest -q tests agent-kits/shared skills/*/scripts evals` (suite completa, Windows + venv, tras aplicar los parches) → **1310 passed, 38 failed, 1 skipped** en 9 m 16 s (puerta ≥ 1.175 ✓). De los 38: uno es `test_ca08_…` medido a mitad de la edición del ledger (la suite arrancó antes de los recortes de T-19/T-20; tras ellos → **2 passed**); los 37 restantes son las familias preexistentes de Windows ya catalogadas — `\` vs `/` (`test_confluence_scope` ×4, `test_journal` ×3, `test_progress_report` ×1), bit `+x` (`test_doctor`, `test_todos_los_hooks…`, `test_suites_no_pytest[test_lint_plugin]`), `sin_python3` ×5 y `progress_line` ×6 en `test_hooks_shell` más `mark_docs_pending`/`ledger_lint_warn` (reproducidos por la Lente B en un worktree de la base), CRLF en `test_knowledge_find` ×3, git en Windows en `test_release` ×3, rutas con espacios en `test_coverage_gate` ×5 y `WinError 5` en `evals/test_evals` ×2. En CI (Linux) estas familias no aplican. T-19 y T-20 quedan cerca del tope CA-08 (9,8-9,9k medidos aquí): el test del ledger real avisa si crecen.

---

## Revisión de dos lentes — intento 1 (Fases 5-6): 10 gaps (2 Critical, 2 Important, 6 Minor) → 10 corregidos en T-21; 0 rebatidos

Lentes: **A + B + D** (`review-lens-select.py --base 853ea8d` → `lente_c: false`, `lente_d: true` por dos motivos que la propia Lente D desmontó como falsos positivos de la heurística: la ventana de 6 líneas confundió los `re.compile` de nivel de módulo de `retro-gate.py:31-32` con el bucle de `reconfigure` de la :26, y `export-skills.py` saltó por su nombre de ruta con +2 líneas de tabla estática), tres agentes `reviewer` en paralelo (`opus`/`high`) sobre `git diff 853ea8d...97afbe3`. `scope-check` → 40 en alcance, «fuera» solo los 3 sin seguimiento preexistentes ajenos a la iniciativa. A1 y B2 señalaban lo mismo (fusionados).

| # | Grado | Lente | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|---|
| 1 | **Critical** | B | `retro_ok()` exigía frontmatter y `/retro` nunca lo escribe: las 7 retros reales daban exit 1 y el arreglo impreso (`/retro`) reproducía el mismo formato — bucle sin salida. La suite no lo cazaba porque el fixture inventaba el formato | T-17 | Contrato desde los datos: título `# …` + cuerpo (formato real) o frontmatter cerrado con `---` exacto + cuerpo; `/retro` paso 4 pide frontmatter mínimo hacia delante | `test_el_formato_real_de_retro_sin_frontmatter_abre_la_puerta`; `test_las_retros_reales_del_repo_cumplen_el_contrato` (7/7) |
| 2 | **Critical** | A+B | `retro-gate.py` imprime `✅❌ℹ️` (snippet GOT-005) y `tests/test_console_encoding.py` lo auto-descubre al estar versionado, pero exige entrada manual en `MODOS` → 4 rojos, sin dependencia de plataforma (CI roja) | T-17 | Entrada `retro-gate.py` → `[INI]`, exit `(0, 1)` | `pytest tests/test_console_encoding.py` → 281 passed (+4 casos) |
| 3 | Important | B | El titular de la doctrina se tomaba de la primera `**…**` de TODO el fichero: `fuente: x (**medido**)` del frontmatter → «medido»; `300**k**` inline → «k»; sin negrita → «evaluator» | T-16 | `_titular_leccion`: solo el cuerpo y solo la negrita que abre un bullet; sin ella, la primera frase del cuerpo | `test_el_titular_de_la_doctrina_sale_del_bullet_en_negrita_del_cuerpo` |
| 4 | Important | A | Cifras de Verificación de T-16 no reproducibles: «95 passed» para un fichero de 72 casos (era la suma de cuatro ficheros) y «38 failed» que tapaba los 4 rojos del gap 2 (la suite corrió antes de comitear el script) | T-16 | Cifras corregidas en el ledger y suite re-medida tras T-21 | ledger T-16 y esta traza |
| 5 | Minor | A | FLOWS ES/EN §`/dev-cycle` acababan en el nodo de cierre sin el paso 8 | T-18 | Nodo `RG` (`/retro` + `retro-gate.py`, exit 0 → cierre; exit 1 → «pendiente de retro, spec sigue aprobada») en ES y EN | `test_mermaid_blocks` 32 OK |
| 6 | Minor | A | `sesion.memoria` (opt-out real del bloque de memoria de `SessionStart`) ausente de la regla 9 ES/EN y de `CLAUDE.md:103`, justo donde `/setup` manda al lector | T-18 | Añadida en los tres sitios | `grep -rn "sesion.memoria"` → 3 |
| 7 | Minor | A (+B fuera de lente) | La puerta corría **después** de las transiciones que vigila: el paso 7 ya ponía la spec `implementada`; y el paso 6 (changelog) decía «con el ledger ya en `completado`» antes de que el 7 lo pusiera | T-17/T-18 | Ritual 6 estados del plan (ledger `completado`) → 7 changelog → 8 retro (puerta) → 9 spec `implementada` solo con exit 0; con exit 1 la spec se queda `aprobada` como señal visible | `commands/dev-cycle.md:156-159`, `retro.md`, FLOWS |
| 8 | Minor | B | Una carpeta con `tasks.md` fuera de `docs/roadmap/` abría la puerta contra el `CALIBRATION.md` de otro proyecto y devolvía rutas inexistentes | T-17 | `resolver_carpeta` exige `raiz_de(c)` (bajo `docs/roadmap/`); si no, exit 2 con el motivo | `test_una_carpeta_con_tasks_md_fuera_de_docs_roadmap_es_error_de_uso` |
| 9 | Minor | B | `retro_ok` aceptaba `----` (regla horizontal) como cierre de un frontmatter sin cerrar | T-17 | `_CIERRE_FM_RE = ^---\s*$` | `test_retro_vacia_solo_titulos_o_frontmatter_sin_cerrar_no_cuenta` |
| 10 | Minor | B | Carpeta de doctrina presente pero vacía → el aviso daba el motivo del éxito («assets del plugin, recorrido plano») | T-16 | Motivo propio: «carpeta de doctrina vacía (…): instalación incompleta» | `test_carpeta_de_doctrina_vacia_avisa_con_motivo_util` |

**Verificado OK por las lentes (sin cambios):** copias byte a byte idénticas también en el índice de git (`git rev-parse :<path>` iguales por pares); `--doctrina` no toca la memoria del proyecto ni siembra nada; `corpus`/`origen` compatibles con los 4 consumidores del JSON (`e.get("origen","proyecto")` para las entradas de la caché); `dir_doctrina` con precedencia kit co-ubicado → `CLAUDE_PLUGIN_ROOT` y degradación sin assets; CA-21/CA-22/CA-23/CA-24 reproducidos uno por uno; alcance 40/40 con las 4 ampliaciones justificadas; espejo bilingüe equivalente en los 5 pares; prosa sin violaciones citables de `docs-style.md`; rendimiento: doctrina en recorrido plano 10 ms (un índice costaría más), `retro-gate` y `--doctrina` por debajo del arranque del intérprete, tests nuevos 5,8 s (1,5 % de la suite).

**Rebatido:** nada. **Anotado sin cambio (fuera de lente):** `TOPE_EVALUATOR = 15513` es el valor de la spec (CA-22) y deja 489 bytes de holgura al prompt actual (15.024) — se mantiene el contrato de la spec; `--doctrina --related` muestra el slug de iniciativa de este repo (grupo vacío en un consumidor, cosmético); la heurística `regex-en-bucle` de `review-lens-select.py` (ventana de 6 líneas) da falsos positivos con `re.compile` de módulo cerca de un bucle — candidato a afinar en otra iniciativa, no aquí.

Tras T-21: `pytest -q agent-kits/shared/test_retro_gate.py tests/test_doctrina_viaja.py tests/test_console_encoding.py tests/test_memory_path.py tests/test_mermaid_blocks.py` → **326 passed** · `tests/test_knowledge_find.py` → 69 passed + 3 CRLF preexistentes · `lint_plugin` 0 errores · `evals/check` 0 errores · `ledger-lint` 0 incoherencias · `pytest -q` completo -> **1349 passed, 37 failed, 1 skipped** (7 m 33 s): los 37 son las familias preexistentes de Windows, ninguno fuera; los 4 rojos nuevos de `test_console_encoding.py` que tapaba la cifra anterior ya no estan.
