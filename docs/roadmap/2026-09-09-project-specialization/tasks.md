---
generacion:            # ventana compartida con improvement-plan.md
  inicio: 2026-09-09T10:53:07Z
  fin: 2026-09-09T11:13:04Z
  fuente: estimado     # `usage-meter.py close` degrado: «carpeta de transcripciones no disponible» (Windows). Tokens estimados a juicio a partir de lo leido/escrito
  tokens_reales: { entrada: 78000, salida: 34000, cache_creacion: 34000, cache_lectura: 420000 }
  eur: 1.53
  horas_ia: 0.30
  duracion: 20m
  ratio_usado: 479326
verificacion: obligatoria   # cada T-XX lleva `- **Verificación**:`; lo exige ledger-lint (exit 1 si falta)
---

# Checklist de Tareas — Especialización por proyecto (el tercer bucle)

| | |
|---|---|
| **Estado** | en-progreso |
| **Fecha** | 2026-09-09 |
| **Plan** | [`improvement-plan.md`](./improvement-plan.md) |
| **Diseño** | [`design.md`](./design.md) — opción **O1** (`ADR-014`) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del plan. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador SDD externo— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

> **Alcance:** F1 + F2 de [`spec.md`](spec.md) (`aprobada`). **F3 está diferida y no tiene tareas**: ni deriva semántica (C-08) ni campo «Cuándo aplica» en `knowledge-write.md` (C-09). Si aparecen en una tarea, es alcance colado.
> **Entorno:** las puertas se corren con `export PATH="$PWD/.venv/Scripts:$PATH"`. Consola cp1252 (`GOT-005`): ningún script nuevo emite emoji ni flechas Unicode.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — Sustrato | 3 | 3 | 100% | 0 / 6,0h | 1,30 (est.) / 0,46h | 0,33 (est.) / 0,11h | 220k (est.) / 220k |
| Fase 2 — Nacimiento | 0 | 16 | 0% | 0 / 31,0h | 0 / 2,41h | 0 / 0,60h | 0 / 1.153k |
| Fase 3 — Revisión, corrección y cierre | 0 | 3 | 0% | 0 / 10,0h | 0 / 1,10h | 0 / 0,27h | 0 / 525k |
| **TOTAL** | **3** | **22** | **14%** | **0 / 47,0h** | **1,30 (est.) / 3,96h** | **0,33 (est.) / 0,99h** | **220k (est.) / 1.898k** |

> **Horas → Jira.** No aplica en esta iniciativa: `.claude/jira.json` no está configurado, así que no hay volcado de tareas ni worklog. Si se configura más adelante, el worklog es **Tiempo IA (ejec.) + Supervisión** topado a la jornada (ver `skills/jira-sync/SKILL.md`).

---

## Fase 1 — Sustrato (C-01, C-02)

**Estado**: completado · **Estimado**: 6,0h · **Real**: 1,63h IA+supervisión (estimado, meter degradado — incluye la corrección intento 1, la corrección intento 2 y las dos rondas de la corrección intento 3 (opción A y la pasada acotada a los gaps B-4/B-5/B-6/B-7); las 3 tareas cierran completado con todos los gaps de las dos revisiones verificados) · **Coste est.**: 302,02 € · **Tokens est.**: 220k (real: estimado, igual al presupuesto — ver nota de degradación en cada tarea)

> Entrega el contrato de la carpeta de personas y la puerta de entrada documental del bucle. **Rinde sola**: al cerrarla, una persona de proyecto escrita a mano ya funciona sin generador.

### T-01 — Cascada de tres escalones en la resolución de personas de `task-brief.py`

- **Descripción**: `--personas-dir` deja de ser un solo directorio con default al catálogo del plugin (`agent-kits/shared/task-brief.py`, resolución en ~481-482 y ~526-528) y pasa a cascada: `.claude/personas/<tipo>.md` → `agent-kits/shared/personas/<tipo>.md` → sin sección de persona con aviso por `stderr` y exit 0. Los tipos quedan **extensibles**: no hay lista blanca de los 6.
- **Changelog**: Una persona de dominio escrita en `.claude/personas/<tipo>.md` del proyecto entra en el brief del subagente por delante del catálogo genérico del plugin, y cualquier tipo nuevo funciona sin tocar código.
- **Estado**: completado
- **Tiempo humano**: est. 2,5h · real —
- **Tiempo IA (ejec.)**: est. 0,19h · real 1,21h (estimado — 0,19h implementación + 0,15h corrección intento 1 + 0,34h corrección intento 2 (B-2 Critical + B-1 + B-3 en `task-brief.py`, 4 tests nuevos, 2 propagaciones más y el fix de `dev-cycle.md`) + 0,30h corrección intento 3 opción A (`PERSONA_SUELO_CHARS`, fórmula del tope, aviso con causa medida por sección, 2 tests reescritos/nuevos; clave `project-specialization/T-01-fix3`) + 0,23h corrección intento 3 pasada acotada, gaps B-4/B-5/B-6/B-7 (contenido no bloque en `_persona_delimitada`, aviso bifurcado por causa real, medición por secciones del brief montado, guardián de calibración y verificación de mutante; clave `project-specialization/T-01-fix4`); meter degradado en las cuatro rondas, sin marcador `start`: medido a juicio, no por `usage-meter.py`)
- **Supervisión**: est. 0,05h (≈25 % IA) · real 0,20h (estimado — +0,03h de la corrección intento 3 pasada acotada, ≈25 % de sus 0,23h de IA)
- **Previsión IA**: 70k in / 20k out tok · 0,78 €
- **Dependencias**: ninguna. Es la raíz del plan y la única característica de la que dependen todas las demás para servir de algo
- **Archivos**: `agent-kits/shared/task-brief.py`, `agent-kits/shared/test_task_brief.py`, `commands/dev-cycle.md` (nota: describía la inyección de persona como un solo catálogo — quedó falsa tras la cascada, gap 4 de la revisión intento 1; corrección intento 2, gap 17/18: matiza «gana siempre» al caso real —vacío u `OSError` caen al catálogo— y parte la frase en viñetas por longitud), `agents/planner.md` (nota: idem — la lista cerrada de 6 tipos ya no aplica), `agent-kits/shared/README.md` (nota: idem — dos filas, `task-brief.py` y `personas/`, describían el catálogo como único escalón), `agent-kits/planner/templates/tasks.md` (nota: corrección intento 2, gap 13 — el placeholder de `- **Tipo**:` seguía ofreciendo la lista cerrada de 6 tipos aunque `agents/planner.md` ya decía «libre»; el planner rellena de la plantilla, así que una tarea de tipo `hooks` salía sin `Tipo` y la persona nunca llegaba al brief), `docs/agents/planner.md` (nota: corrección intento 2, gap 14 — propagaba la misma lista cerrada de 6 tipos), `skills/adversarial-review/references/lens-prompts.md` (nota: corrección intento 2, gap 14 — la Lente B repetía la lista cerrada y afirmaba falsamente «misma mecánica que `task-brief.py`»), `interop/**` (GENERADO por `scripts/export-interop.py` al tocar `commands/dev-cycle.md` y `agents/planner.md`: regla de interop de `CLAUDE.md`, `--check` es puerta de CI y de `release.py`; 3 ficheros desincronizados detectados por el orquestador tras la revisión, no por las lentes)
- **Verificación**:
  - `python3 -m pytest -q agent-kits/shared/test_task_brief.py` → todos verdes, incluidos los casos nuevos de cascada, y **sin haber tocado los asserts previos**
  - `grep -nE "\"frontend\"|'frontend'" agent-kits/shared/task-brief.py` → ninguna lista cerrada de tipos (solo el nombre del fichero del catálogo, si aparece)
  - `python3 scripts/lint_plugin.py` → 0 errores
  - (ejecutada 2026-09-09 — salida: `pytest -q agent-kits/shared/test_task_brief.py` → `52 passed in 22.38s`; `grep -nE "\"frontend\"|'frontend'" agent-kits/shared/task-brief.py` → sin coincidencias; `lint_plugin.py` → `9 agentes · 0 errores · 3 avisos` (los 3 avisos son de nombres genéricos de comandos preexistentes, no de esta tarea))
  - (corrección intento 1 — ejecutada 2026-09-09: `pytest -q agent-kits/shared/test_task_brief.py` → `56 passed in 15.38s` (4 tests nuevos: OSError en escalón 1 cae al catálogo, persona por encima del tope se recorta, delimitado contra suplantación del contrato, aviso de vacío sin prometer un escalón inexistente); `lint_plugin.py` → `9 agentes · 0 errores · 3 avisos` (mismos 3 preexistentes))
  - (corrección intento 3, opción A (B-3, suelo de la persona) — re-ejecutada 2026-09-09 tras el ÚLTIMO cambio: `python3 -m pytest -q agent-kits/shared/test_task_brief.py` → `59 passed, 1 failed in 15.42s` (el failed es `test_ca08_el_brief_completo_cabe_en_el_tope_sobre_el_ledger_real_de_memory_retrieval`, la violación preexistente de CA-08 sin persona — ya fallaba igual antes de esta corrección, confirmado con `git stash`; iniciativa aparte `docs/roadmap/2026-09-09-brief-budget/`, fuera de alcance); `grep -nE "\"frontend\"|'frontend'" agent-kits/shared/task-brief.py` → sin coincidencias; `python3 scripts/lint_plugin.py` → `9 agentes · 0 errores · 3 avisos` (mismos 3 preexistentes, ninguno de esta tarea))
  - (corrección intento 3, pasada acotada a la opción A (B-4/B-5/B-6/B-7 de la segunda revisión) — **supersede la entrada anterior** (GOT-007: evidencia re-ejecutada tras el ÚLTIMO cambio, no reciclada) — ejecutada 2026-09-09: `python3 -m pytest -q agent-kits/shared/test_task_brief.py` → `63 passed, 1 failed in 13.63s` (el único failed sigue siendo `test_ca08_...memory_retrieval`, con `T-05: 10123` y `T-19: 10057` caracteres por encima de `BRIEF_TOPE_CHARS=10000`; confirmado que el bloque `## Persona de dominio` es **byte a byte idéntico** antes/después de esta corrección para ambas tareas — sus personas están muy por debajo del suelo, así que el suelo nunca las toca — y que el residuo se debe al crecimiento del corpus de `docs/knowledge/` entre sesiones (8→9 entradas), ajeno a este cambio y a `docs/roadmap/2026-09-09-brief-budget/`, fuera de alcance); `grep -nE "\"frontend\"|'frontend'" agent-kits/shared/task-brief.py` → sin coincidencias; `python3 scripts/lint_plugin.py` → `9 agentes · 0 errores · 3 avisos` (mismos 3 preexistentes, ninguno de esta tarea). Además, verificación personal del mutante `PERSONA_SUELO_CHARS = 400` (copia de trabajo, restaurada tras comprobar, `diff` limpio contra el fichero real): `pytest -k "test_persona_suelo_por_encima_del_catalogo or test_persona_suelo_entrega_contenido_util_no_bloque_relleno"` → **2 failed** (evidencia B-7 de que el guardián de calibración y la medición de contenido SÍ detectan la regresión))

**Criterios de aceptación**
- [x] CA-01 — con `.claude/personas/hooks.md` y una tarea `- **Tipo**: hooks`, el brief lleva el contenido del fichero del proyecto y **no** el del catálogo del plugin
- [x] CA-02 — sin `.claude/personas/backend.md`, el brief usa `agent-kits/shared/personas/backend.md`: **el comportamiento de hoy no cambia** y la suite previa sigue verde sin retocar sus asserts
- [x] CA-03 — con un `Tipo` que no existe en ninguno de los dos escalones, el brief sale sin sección de persona, con aviso por `stderr` y **exit 0** (degradación, no bloqueo)
- [x] CA-04 — un tipo nuevo (p. ej. `hooks`) funciona **sin tocar código**: no hay lista blanca de los 6 tipos

**Subtareas**
- [x] Leer la resolución actual y el punto exacto donde `--personas-dir` se colapsa a un directorio único
- [x] Convertirlo en cascada de tres escalones preservando la firma de `--personas-dir` (sigue valiendo para apuntar el segundo escalón)
- [x] Aviso de degradación a `stderr`, nunca a `stdout` (el script compone el brief; contaminar `stdout` lo rompe)
- [x] Casos nuevos en `test_task_brief.py`: proyecto gana al plugin, plugin como fallback, tipo inexistente con exit 0, tipo arbitrario

**Notas**: el hueco en el brief **ya existe** (`subagent-personas`), así que no hay sección nueva ni presupuesto de tokens nuevo: `MEMORIA_TOPE_CHARS = 2400` y `BRIEF_TOPE_CHARS = 10000` no se tocan. La incógnita que la evaluación anota (si el tope de facto de 9 líneas por persona debe hacerse constante explícita) **no la exige la spec**: si aparece en la revisión, es deuda declarada, no alcance.

<!-- ==================================================================== -->

### T-02 — `docs/SPECIALIZATION.md` + espejo EN, indexados en los dos `docs/README.md`

- **Descripción**: escribir la **única puerta de entrada** del tercer bucle, hermana de `INTEROP.md` y `observability.md`, con las seis cosas de las que CA-05 la hace fuente única: el registro, la escalera de decisión, las dos puertas, el invariante de dirección, **los tres estados por hash** y **el límite explícito de esta iteración a F1+F2**. Va en ES y en EN, con fila en `docs/README.md` y en `docs/en/README.md`.
- **Changelog**: La especialización por proyecto tiene un documento de entrada único, `docs/SPECIALIZATION.md` (con su espejo en inglés), que explica el registro de piezas, la escalera de decisión y las dos puertas.
- **Estado**: completado
- **Tiempo humano**: est. 2,0h · real —
- **Tiempo IA (ejec.)**: est. 0,16h · real 0,23h (estimado — 0,16h implementación + 0,05h corrección intento 1 + 0,02h corrección intento 2 (gap 16, línea de ledger); meter degradado, sin marcador `start` para esta ronda: medido a juicio, no por `usage-meter.py`)
- **Supervisión**: est. 0,04h (≈25 % IA) · real 0,06h (estimado)
- **Previsión IA**: 55k in / 20k out tok · 0,71 €
- **Dependencias**: T-01 (blanda — documenta la cascada **ya real**, no una promesa; no la bloquea)
- **Tipo**: docs
- **Archivos**: `docs/SPECIALIZATION.md`, `docs/en/SPECIALIZATION.md`, `docs/README.md`, `docs/en/README.md`
- **Verificación**:
  - `python3 scripts/lint_plugin.py` → 0 errores
  - `grep -nc "pieces.json" docs/SPECIALIZATION.md docs/en/SPECIALIZATION.md` → ≥ 1 en los dos ficheros
  - lectura: los seis contenidos de CA-05 presentes en ambos idiomas, y los tokens que parsea la máquina (`pieces.json`, `gestionada`/`modificada`/`no gestionada`) **en español también en la versión EN**
  - (ejecutada 2026-09-09 — salida: `lint_plugin.py` → `9 agentes · 0 errores · 3 avisos` (avisos preexistentes de nombres genéricos de comandos, no de esta tarea); `grep -nc "pieces.json" docs/SPECIALIZATION.md docs/en/SPECIALIZATION.md` → `docs/SPECIALIZATION.md:1` y `docs/en/SPECIALIZATION.md:1`; lectura confirmada: los seis contenidos —registro, escalera, dos puertas, invariante de dirección, tres estados por hash, límite F1+F2— están en ambos idiomas, con `gestionada`/`modificada`/`no gestionada` en español también en la versión EN)
  - (corrección intento 1 — ejecutada 2026-09-09: gap 3 — añadido bloque "entregado vs contrato de diseño" tras el callout de alcance en `docs/SPECIALIZATION.md:14-19` y su espejo en `docs/en/SPECIALIZATION.md:14-19`, citando `design.md`/`ADR-014`/T-04…T-18, mismo patrón que `docs/agents/ROLES.md:7-8`; gap 7 — `docs/en/SPECIALIZATION.md:6` corregido de `[INTEROP.md](../INTEROP.md)` a `[INTEROP.md](INTEROP.md)` (el espejo EN existe, el enlace ya no cruza al árbol ES); gap 10 — `docs/SPECIALIZATION.md:30` y `docs/en/SPECIALIZATION.md:30` matizados: la inyección de persona aplica a las tareas con `- **Tipo**: <tipo>` (campo opcional), no a "cada tarea". Verificación (re-ejecutada 2026-09-09 tras el bloque del gap 3, que añade una segunda mención): `grep -nc "pieces.json" docs/SPECIALIZATION.md docs/en/SPECIALIZATION.md` → `docs/SPECIALIZATION.md:2` y `docs/en/SPECIALIZATION.md:2` (el criterio de aceptación es ≥ 1 en los dos ficheros; sigue cumpliéndose, ahora en 2/2 en vez de 1/1); `lint_plugin.py` → `9 agentes · 0 errores · 3 avisos` (mismos 3 preexistentes); lectura confirmada de los tres textos corregidos en ambos idiomas)

**Criterios de aceptación**
- [x] CA-05 — `docs/SPECIALIZATION.md` existe, es la única puerta de entrada del bucle con los seis contenidos exigidos, tiene espejo en `docs/en/SPECIALIZATION.md`, y los dos `README.md` lo indexan; `lint_plugin.py` con 0 errores
- [x] El documento escribe el **invariante de dirección** en una frase: `/specialize` **lee** `docs/knowledge/` y **nunca escribe** en él (la promoción a doctrina sigue siendo de `/retro` y del contrato de promoción)
- [x] El documento declara el límite de esta iteración (F1+F2) y que F3 está **diferida, no descartada**, con puntero a `spec.md` §Fuera

**Subtareas**
- [x] Estructura del documento: qué es el bucle · registro canónico · escalera · puerta de colisión · puerta humana · los tres estados · el invariante de dirección · el límite de esta iteración
- [x] Redactar ES según `agent-kits/shared/docs-style.md` (frases cortas, rutas reales, tablas para comparar)
- [x] Espejo EN según `docs-style.en.md`, con los tokens de máquina intactos
- [x] Filas en `docs/README.md` y `docs/en/README.md`

**Notas**: el diagrama **no** va aquí (va en `FLOWS.md`, T-03). El esquema concreto del registro se documenta con la forma **O1** del diseño; si T-04/T-05 lo hicieran evolucionar, este documento se actualiza en el mismo cambio (regla bilingüe: los dos idiomas a la vez).

<!-- ==================================================================== -->

### T-03 — Sección del tercer bucle en `FLOWS.md` (+EN) y fila de `/specialize` en `ROLES.md`

- **Descripción**: añadir a `docs/FLOWS.md` y `docs/en/FLOWS.md` la sección del tercer bucle con el diagrama mermaid de `analysis.md` §2 (memoria → especialización → ciclo → memoria), y a `docs/agents/ROLES.md` la fila de `/specialize` con DECIDE / ESCRIBE / LEE / no hace, incluyendo escrito el invariante de dirección que impide el solape con el bucle de memoria (`ADR-011`).
- **Changelog**: Los diagramas de flujo y la matriz de roles incluyen el tercer bucle, con lo que `/specialize` decide, escribe y solo lee, para que no se solape con la memoria técnica.
- **Estado**: completado
- **Tiempo humano**: est. 1,5h · real —
- **Tiempo IA (ejec.)**: est. 0,11h · real 0,16h (estimado — 0,11h implementación + 0,05h corrección intento 1; meter degradado)
- **Supervisión**: est. 0,03h (≈25 % IA) · real 0,04h (estimado)
- **Previsión IA**: 40k in / 15k out tok · 0,53 €
- **Dependencias**: T-02 (la sección de FLOWS y la fila de ROLES apuntan al documento de entrada)
- **Tipo**: docs
- **Archivos**: `docs/FLOWS.md`, `docs/en/FLOWS.md`, `docs/agents/ROLES.md`
- **Verificación**:
  - `python3 -m pytest -q tests/test_mermaid_blocks.py` → verde (el diagrama no rompe el parseo)
  - `grep -n "specialize" docs/agents/ROLES.md` → la fila existe
  - `grep -c "mermaid" docs/FLOWS.md docs/en/FLOWS.md` → el mismo número en los dos ficheros
  - (ejecutada 2026-09-09 — salida: `tests/test_mermaid_blocks.py` se ejecuta como script, no como suite pytest — `python3 tests/test_mermaid_blocks.py` → `test_mermaid_blocks: 35 diagrama(s) OK`; `grep -n "specialize" docs/agents/ROLES.md` → 3 líneas, incluida la fila de la matriz; `grep -c "mermaid" docs/FLOWS.md docs/en/FLOWS.md` → `docs/FLOWS.md:13` y `docs/en/FLOWS.md:13`, mismo número)
  - (corrección intento 1 — ejecutada 2026-09-09: gap 3 — sección "6d · El tercer bucle" de `docs/FLOWS.md:335-336` y `docs/en/FLOWS.md:337` marca F1 como **entregado**/**shipped** y F2 como **contrato de diseño, aún no en el árbol**/**design contract, not in the tree yet**, cerrando el mismo hueco que gap 3 en T-02 pero en `FLOWS.md`; gap 5 — `docs/agents/ROLES.md:36`, columna "no hace" de la fila `/specialize`, ahora cita el flag `--project` y `ADR-015` (aún `propuesta`): sin el flag, `--root` sobre un árbol de consumidor sigue dando exit 1; gap 11 — la referencia colgante "esta carpeta" queda sustituida por el texto explícito de gap 3 (ya no hay antecedente ambiguo). Verificación: `python3 tests/test_mermaid_blocks.py` → `test_mermaid_blocks: 35 diagrama(s) OK` (sin regresión); `grep -c "mermaid" docs/FLOWS.md docs/en/FLOWS.md` sigue en 13/13; `grep -n "ADR-015" docs/agents/ROLES.md` → línea 36)

**Criterios de aceptación**
- [x] CA-06 — `docs/FLOWS.md` y `docs/en/FLOWS.md` tienen la sección del tercer bucle con el diagrama de `analysis.md` §2; `tests/test_mermaid_blocks.py` en verde
- [x] CA-07 — `docs/agents/ROLES.md` tiene la fila de `/specialize` con DECIDE / ESCRIBE / LEE / no hace, y escrito el invariante «lee `docs/knowledge/`, nunca escribe en él»
- [x] La fila de `ROLES.md` nombra explícitamente qué NO hace `/specialize`: no promueve doctrina (eso es `/retro`), no genera piezas del plugin (eso es `plugin-dev`) y no sabe de runtimes (eso es `export-interop.py`)

**Subtareas**
- [x] Copiar el diagrama de `analysis.md` §2 y comprobar que los nodos citan rutas reales
- [x] Sección ES + espejo EN de `FLOWS.md` (los dos en el mismo cambio)
- [x] Fila de `/specialize` en `ROLES.md` con las cuatro columnas
- [x] Repasar que ninguna fila existente quede contradicha (solape resuelto, no implícito)

**Notas**: `ROLES.md` es solo ES por convención (los docs de agentes y el roadmap no llevan espejo). `FLOWS.md` sí lleva espejo: al cambiar uno, el otro va en el mismo cambio.

---

## Fase 2 — Nacimiento (C-10, C-03, C-04, C-05, C-07, C-06, C-11)

**Estado**: borrador · **Estimado**: 31,0h · **Real**: — · **Coste est.**: 1.560,24 € · **Tokens est.**: 1.153k

> Orden de la evaluación, que es el del grafo: **C-10 → C-03 → C-04 → C-05 → C-07 → C-06 → C-11**. C-10 abre la fase porque es la **raíz sin dependencias** que fija el esquema con tests; C-05 y C-06 la consumen (condición (a) del go). La fase **no se entrega sin su propia auditoría mecánica** (`/doctor`, C-06): no se da la capacidad de generar sin la de comprobar.

### T-04 — `pieces-registry.py`: esquema O1, hash normalizado y los subcomandos de lectura

- **Descripción**: crear `agent-kits/shared/pieces-registry.py` con la forma **O1** del diseño (`piezas[]` con `destinos[{runtime, ruta, hash}]`, `version` y `hash_version` en cabecera), el hash `sha256` sobre los bytes del fichero completo con `\r\n`→`\n` normalizado, el índice invertido ruta→destino, y los subcomandos de **solo lectura**: `estado <ruta>…`, `dueno <ruta>`, `listar [--json]` y `tope`. El estado **no se persiste**: se deriva del hash en cada lectura.
- **Changelog**: El proyecto tiene un registro de piezas de especialización, `.claude/pieces.json`, con un script que dice de quién es cada fichero y si sigue igual que cuando se generó.
- **Estado**: borrador
- **Tiempo humano**: est. 2,0h · real —
- **Tiempo IA (ejec.)**: est. 0,17h · real —
- **Supervisión**: est. 0,04h (≈25 % IA) · real —
- **Previsión IA**: 60k in / 20k out tok · 0,74 €
- **Dependencias**: ninguna. **Raíz del subgrafo de F2** — C-05 (T-11) y C-06 (T-15) la consumen, y esa es la condición (a) del go
- **Archivos**: `agent-kits/shared/pieces-registry.py`, `agent-kits/shared/test_pieces_registry.py`, `tests/test_console_encoding.py`
- **Verificación**:
  - `python3 -m pytest -q agent-kits/shared/test_pieces_registry.py` → verde, con el caso del **mismo contenido en CRLF y en LF exigiendo el mismo hash**
  - `python3 agent-kits/shared/pieces-registry.py listar --json --project-dir <árbol temporal sin registro>` → `{"piezas": []}` y **exit 0** (degradación: sin `pieces.json`, registro vacío)
  - `python3 agent-kits/shared/pieces-registry.py dueno <ruta sin fila> --project-dir <árbol>` → **exit 3** y el motivo por `stdout`
  - `git add -N agent-kits/shared/pieces-registry.py && python3 -m pytest -q tests/test_console_encoding.py` → verde (`GOT-005` + `GOT-007`)

**Criterios de aceptación**
- [ ] Esquema **O1** literal del diseño §2: la pieza es la raíz, `destinos[]` dentro, `runtime` como **dato** y nunca clave; `version` y `hash_version` en cabecera con la regla «versión desconocida → solo lectura y aviso»
- [ ] Hash `sha256` sobre bytes con `\r\n`→`\n` normalizado, guardado como `"sha256:<hex>"`; test con el mismo contenido en los dos finales de línea (`GOT-007` caso 2)
- [ ] CA-17 (mitad de lectura) — `dueno(<ruta>)` es la **única** puerta de propiedad: sin fila con hash coincidente sale con **exit 3** y lo dice; nombres reservados (`pieces.json`, `pieces-state.json`, `pieces.json.lock`) no son adoptables ni destino
- [ ] La misma ruta en dos piezas es **rechazada** al cargar, con su test (es representable en O1, así que hay que cerrarla)
- [ ] `tope` lee `especializacion.topePiezas` de `.claude/dev.json` con **default 5** y cuenta `len(piezas)`; sin `dev.json` o con la clave ausente, 5
- [ ] Degradación: sin `pieces.json` → registro vacío, todo `no gestionada`, exit 0. Corrupto → se lee como vacío **con aviso** y exit 2 al intentar escribir, nombrando `--reconstruir`
- [ ] Snippet de consola UTF-8 replicado **literal** y el script en la tabla `MODOS` de `tests/test_console_encoding.py`; salida sin emoji ni flechas Unicode

**Subtareas**
- [ ] Esqueleto del script con el snippet de consola y `argparse` de los siete subcomandos (los de escritura quedan como stub para T-05)
- [ ] Carga, validación de esquema por `version`/`hash_version` e índice invertido ruta→destino
- [ ] `hash_fichero()` con normalización de finales de línea; `estado()` derivando los tres estados del hash
- [ ] `dueno()` con exit 3, nombres reservados y detección de marcadores `agent-kits/`/`.claude-plugin/` en la raíz del destino
- [ ] `listar [--json]` y `tope` (lector de `dev.json`)
- [ ] Suite: hash CRLF/LF, tres estados, ruta duplicada, nombres reservados, registro ausente y corrupto, tope con y sin clave

**Notas**: la lista de campos la cierra `ADR-014` decisión 6. Si la revisión pide un campo que no está ahí, el camino es **subir `version`**, no reinterpretar el esquema. `pieces-state.json` guarda **solo** la huella del último escaneo y **no se crea vacío** (un fichero vacío es una fila muerta en la regla 9).

<!-- ==================================================================== -->

### T-05 — Escritura del registro: `registrar`, `adopt`, `auditar` y `--reconstruir`, con cerrojo e idempotencia por bytes

- **Descripción**: completar `pieces-registry.py` con los caminos que escriben: `registrar`, `adopt`, `auditar` y `--reconstruir`. Dos promesas con **dos mecanismos** y **dos tests separados**: `temp + os.replace` para que el JSON nunca quede a medias (precedente `usage-meter.py:_save_state`) y `.lock` hermano para serializar el leer-modificar-escribir. Idempotencia **por bytes** con serialización canónica. La lectura no toma cerrojo.
- **Changelog**: Registrar o adoptar una pieza es seguro con varias personas trabajando: el registro nunca queda a medias, dos escrituras a la vez no se pisan, y volver a ejecutar sin cambios no toca el fichero.
- **Estado**: borrador
- **Tiempo humano**: est. 2,0h · real —
- **Tiempo IA (ejec.)**: est. 0,16h · real —
- **Supervisión**: est. 0,04h (≈25 % IA) · real —
- **Previsión IA**: 60k in / 18k out tok · 0,69 €
- **Dependencias**: T-04
- **Archivos**: `agent-kits/shared/pieces-registry.py`, `agent-kits/shared/test_pieces_registry.py`, `agent-kits/shared/journal.py`
- **Verificación**:
  - `python3 -m pytest -q agent-kits/shared/test_pieces_registry.py` → verde, con **dos tests separados**: corrupción (proceso muerto a mitad de escritura → JSON válido) y pérdida de fila (**dos procesos reales** con `subprocess`, no dos hilos)
  - `python3 agent-kits/shared/pieces-registry.py registrar … --project-dir <árbol>` dos veces seguidas → la segunda imprime «sin cambios» y **exit 0**, y `git diff --stat` del registro está vacío
  - `python3 agent-kits/shared/pieces-registry.py registrar … --project-dir <árbol con .lock tomado>` → **exit 4** tras la espera acotada, y el JSON sigue siendo válido

**Criterios de aceptación**
- [ ] CA-26 — el `.lock` hermano de `.claude/pieces.json` serializa la escritura; una segunda escritura concurrente **espera o falla con aviso** (exit 4) y el JSON **nunca** queda corrupto. Dos tests, uno por promesa
- [ ] CA-25 — idempotencia: sin cambios no se escribe, se informa «sin cambios» y sale con **exit 0**. Serialización canónica (piezas ordenadas por nombre, claves en orden fijo, `indent=2`, `ensure_ascii=False`) y **nada volátil** dentro del fichero
- [ ] CA-24 — `adopt <ruta>` añade fila con el hash **actual**, `origen: adoptada` y estado derivado `modificada`; **rehúsa (exit 3)** si la ruta ya tiene fila, si cae fuera de las raíces de destino, o si su raíz tiene marcadores de plugin desplegado sin `--confirmar-arbol-plugin` (que queda anotado en la fila con su fecha)
- [ ] CA-23 — una pieza cuyo hash en disco no coincide con el anotado se reporta `modificada` y **nunca se pisa**: se rehúsa la escritura hasta confirmación explícita
- [ ] CA-27 — `redactar()` se **importa** de `agent-kits/shared/journal.py:200` (nunca se reimplementa la heurística — `LES-013`) y se aplica a todo texto de evidencia antes de escribirlo; una ruta bajo `docs/security-scan/` **no se cita** (rechazo, no redacción)
- [ ] `auditar` distingue los tres estados de fichero del cuarto hallazgo, que es un defecto del registro: la **fila huérfana** (fila sin fichero). Exit 1 con hallazgos, 0 sin ellos
- [ ] `--reconstruir` aparta el registro corrupto a `pieces.json.corrupto-<ts>` y lo rehace desde el disco; **nunca** en silencio (lo invoca `/specialize` tras confirmación, T-11)
- [ ] Degradación de Windows **escrita**: sin `flock`, el camino es `msvcrt` en bucle acotado y, si no se consigue, **exit 4** — jamás escribir sin cerrojo

**Subtareas**
- [ ] `registrar` con `dueno()` como puerta previa, y escritura vía `temp + os.replace`
- [ ] Cerrojo: adquisición con espera acotada (~3 s, bucle de `journal.py`), liberación en `finally`, y camino Windows por `msvcrt`
- [ ] Serialización canónica + comparación de bytes antes de escribir
- [ ] `adopt` con sus tres rechazos y la anotación de `--confirmar-arbol-plugin`
- [ ] `auditar` con los tres estados + fila huérfana
- [ ] `--reconstruir` con el apartado a `pieces.json.corrupto-<ts>`
- [ ] Importar `redactar` de `journal.py` con `importlib.util`; si la revisión rechaza importar privados, promoverlos a nombre público **ahí** (una línea) — nunca duplicar el cerrojo ni la redacción
- [ ] Los dos tests de concurrencia por separado, con `subprocess` real

**Notas**: la evaluación marca el cerrojo como «la parte que más fácilmente queda verde en el test y roto en la práctica», con precedente propio (el debounce de la línea de progreso tuvo que rehacerse con `flock` + rename atómico en `debt-cleanup`). Un `assert True` aquí es un gap Critical, no un test.

<!-- ==================================================================== -->

### T-06 — Regla 9 de `CONVENTIONS.md` (+EN) con las dos filas del registro, nota de la regla 3 y `.gitignore`

- **Descripción**: documentar el registro donde el repo documenta la config: **dos filas** en la tabla de la regla 9 de `docs/CONVENTIONS.md` (`pieces.json` config comiteada / `pieces-state.json` estado ignorado), con su **espejo en `docs/en/CONVENTIONS.md`**; nota en la regla 3 distinguiendo pieza de plugin de pieza de proyecto; y `pieces-state.json` + `pieces.json.lock` fuera del control de versiones (`.gitignore` del repo y siembra de `.claude/.gitignore` en el consumidor, patrón `journal.py:209-219`).
- **Changelog**: Las convenciones del proyecto explican que `pieces.json` se comitea y se comparte con el equipo mientras `pieces-state.json` y el fichero de cerrojo quedan fuera de git.
- **Estado**: borrador
- **Tiempo humano**: est. 1,0h · real —
- **Tiempo IA (ejec.)**: est. 0,07h · real —
- **Supervisión**: est. 0,02h (≈25 % IA) · real —
- **Previsión IA**: 25k in / 7k out tok · 0,28 €
- **Dependencias**: T-04 (el esquema y la clave del tope ya fijados: se documenta lo que existe)
- **Tipo**: docs
- **Archivos**: `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `.gitignore`, `agent-kits/shared/pieces-registry.py`
- **Verificación**:
  - `grep -n "pieces.json" docs/CONVENTIONS.md docs/en/CONVENTIONS.md` → las dos filas en los dos ficheros
  - `grep -n "pieces-state.json\|pieces.json.lock" .gitignore` → las dos entradas
  - `git check-ignore -v .claude/pieces-state.json .claude/pieces.json.lock` → ignorados; y `git check-ignore .claude/pieces.json` → **no** ignorado (es config comiteada)
  - `python3 scripts/lint_plugin.py` → 0 errores

**Criterios de aceptación**
- [ ] CA-32 (parte de convenciones) — la regla 9 tiene **dos filas**: `pieces.json` (config, comiteada, entradas ordenadas por nombre, sin nada volátil dentro) y `pieces-state.json` (estado, ignorado, solo la huella del último escaneo, no se crea vacío), cada una con su columna «si se corrompe/pierde»
- [ ] Las **mismas dos filas** en `docs/en/CONVENTIONS.md`, con los tokens que parsea la máquina (`pieces.json`, `pieces-state.json`) **en español**
- [ ] La regla 3 gana la nota **pieza de plugin vs pieza de proyecto**, con el criterio de dónde vive cada una
- [ ] La fila de `dev.json` de la regla 9 (y su espejo) menciona `especializacion.topePiezas` con su default 5 y el motivo escrito (`skill-index.py` `LIMITE_LINEAS = 45` / `LIMITE_CHARS = 3500`)
- [ ] `pieces-state.json` y `pieces.json.lock` ignorados; `pieces.json` **no** ignorado

**Subtareas**
- [ ] Redactar las dos filas siguiendo el patrón `jira.json`/`jira-state.json` de la misma tabla
- [ ] Espejo EN en el mismo cambio
- [ ] Nota de la regla 3
- [ ] Ampliar la fila de `dev.json` con la clave del tope
- [ ] `.gitignore` del repo + siembra de `.claude/.gitignore` en el consumidor desde el script

**Notas**: cierra la **tercera** de las cosas que el `architect` dejó al plan (§Cambios arquitectónicos, decisión 3), y la fila de `dev.json` cierra la **primera** (el nombre de la clave). La pregunta en `/setup` va en T-13.

<!-- ==================================================================== -->

### T-07 — `project-scan.py`: composición de las cuatro fuentes y regla de evidencia en dos formas

- **Descripción**: crear `scripts/project-scan.py` como **compositor**, no como escáner: invoca `deps-inventory.py` (stack y manifiestos), `code-health.py` (hotspots), `coverage-gate.py` (stack de test) y `knowledge-find.py --json` (áreas de memoria), y emite candidatos donde cada uno cita evidencia válida en **cualquiera** de las dos formas: `fichero:línea` del escaneo **o** el ID de una entrada de memoria. Sin evidencia no se propone: regla dura, no aviso.
- **Changelog**: Un escaneo del proyecto propone piezas de especialización solo cuando puede citar la línea de código o la entrada de memoria en la que se apoya.
- **Estado**: borrador
- **Tiempo humano**: est. 3,5h · real —
- **Tiempo IA (ejec.)**: est. 0,27h · real —
- **Supervisión**: est. 0,07h (≈25 % IA) · real —
- **Previsión IA**: 100k in / 28k out tok · 1,10 €
- **Dependencias**: ninguna dura (el orden de la evaluación la pone tras C-10); **C-05 la necesita**
- **Archivos**: `scripts/project-scan.py`, `tests/test_project_scan.py`, `tests/test_console_encoding.py`
- **Verificación**:
  - `python3 -m pytest -q tests/test_project_scan.py` → verde, con un caso sobre **este repo** (mezcla las dos formas de evidencia) y otro sobre un árbol temporal sin `docs/knowledge/` (solo `fichero:línea`)
  - `grep -nE "deps-inventory|code-health|coverage-gate|knowledge-find" scripts/project-scan.py` → las **cuatro** invocaciones (CA-10)
  - `python3 scripts/project-scan.py --json` → JSON válido y **exit 0**, con todo candidato llevando `evidencia` no vacía
  - `git add -N scripts/project-scan.py && python3 -m pytest -q tests/test_console_encoding.py` → verde

**Criterios de aceptación**
- [ ] CA-08 — cada candidato lleva evidencia válida en **cualquiera** de las dos formas; ninguna es obligatoria por sí sola, pero al menos una lo es **siempre**. Dos casos de test: este repo y un árbol sin memoria
- [ ] CA-10 — **no** implementa escáner propio: el `grep` devuelve las cuatro invocaciones
- [ ] Un candidato sin `fichero:línea` **ni** ID de memoria **no se propone**. Regla dura con su test
- [ ] Cada `subprocess` a un sub-script fija `encoding="utf-8", errors="replace"` (la mitad PADRE de `GOT-005`)
- [ ] Snippet de consola replicado literal y el script en la tabla `MODOS`

**Subtareas**
- [ ] Resolver la ruta de los cuatro sub-scripts con el `find` de la regla 5 (seis raíces), no con rutas fijas
- [ ] Invocarlos capturando salida en modo texto con `encoding`/`errors` explícitos
- [ ] Normalizar sus cuatro salidas a una estructura de candidato común (`nombre`, `area`, `forma sugerida`, `evidencia[]`)
- [ ] Validador de la regla de evidencia con su test
- [ ] `--json` y salida legible; ambos deterministas y ordenados

**Notas**: la evaluación anota como riesgo «que los cuatro sub-scripts devuelvan formatos que no casan y aparezca un normalizador no presupuestado». Si el normalizador crece, es **deuda declarada** en el ledger, no horas silenciosas. Segunda incógnita anotada: cuánto tarda `code-health.py` en un repo grande — `--baseline` y caché resolverían, pero **no están presupuestados**.

<!-- ==================================================================== -->

### T-08 — Las cuatro degradaciones de `project-scan.py` y su privacidad, con el segundo árbol fixture

- **Descripción**: cerrar los cuatro caminos de degradación independientes (sin `git`, sin gestor de paquetes en PATH, sin stack de test, `docs/knowledge/` vacío o inexistente) —cada uno omite **su** dimensión con aviso, exit 0 y **sin inventar dato**— y la privacidad: todo lo citado pasa por `redactar()` y nunca se cita nada bajo `docs/security-scan/`. Estrena en la suite el patrón de **segundo árbol fixture** sin memoria.
- **Changelog**: El escaneo funciona en un proyecto sin git, sin gestor de paquetes o sin memoria técnica: omite esa parte, lo dice, y nunca cita un secreto ni un informe de seguridad.
- **Estado**: borrador
- **Tiempo humano**: est. 2,5h · real —
- **Tiempo IA (ejec.)**: est. 0,18h · real —
- **Supervisión**: est. 0,04h (≈25 % IA) · real —
- **Previsión IA**: 65k in / 20k out tok · 0,76 €
- **Dependencias**: T-07
- **Tipo**: test
- **Archivos**: `tests/test_project_scan.py`, `scripts/project-scan.py`
- **Verificación**:
  - `python3 -m pytest -q tests/test_project_scan.py` → verde, con un test por degradación (4) y los de privacidad
  - `python3 scripts/project-scan.py --project-dir <árbol temporal sin docs/knowledge/>` → **exit 0** y el aviso literal «las piezas propuestas se derivan solo del escaneo, sin memoria del proyecto» en la salida
  - `python3 scripts/project-scan.py --json --project-dir <fixture con secreto y con docs/security-scan/>` → ni el secreto ni ninguna ruta bajo `docs/security-scan/` aparecen en `evidencia`

**Criterios de aceptación**
- [ ] CA-09 — sin `git`, sin la herramienta de un sub-script, o con `docs/knowledge/` vacío/inexistente, omite **esa** dimensión con aviso y **exit 0**; si el recuento de aciertos de memoria es 0, el aviso lo dice **explícitamente** con ese texto
- [ ] CA-27 — el fixture con un secreto evidente y una entrada bajo `docs/security-scan/` demuestra que **ninguno de los dos** aparece citado: el secreto **redactado** por `redactar()`, la ruta de seguridad **rechazada**, no redactada
- [ ] Cuatro tests independientes, uno por degradación: ninguno pasa por casualidad porque otro ya fallara antes
- [ ] Ninguna degradación inventa dato (patrón de `code-health` y `deps-inventory`): omite y avisa

**Subtareas**
- [ ] Fixture de árbol temporal **sin** `docs/knowledge/` (patrón nuevo en esta suite)
- [ ] Fixture con secreto evidente + entrada bajo `docs/security-scan/`
- [ ] Test por degradación, simulando la ausencia de cada herramienta sin depender de la máquina
- [ ] Aviso explícito de 0 aciertos de memoria, afirmado por texto y por exit code

**Notas**: la evaluación sube C-03 en +1,0 h exactamente por esta tarea (la regla de evidencia en dos formas, el aviso explícito, el segundo fixture y CA-27). Es la mitad honesta de la característica: «en un consumidor sin memoria la salida es pobre — y hay que decirlo, no disimularlo».

<!-- ==================================================================== -->

### T-09 — `role-collision.py`: inventario descubierto y rechazo de los cuatro nombres canónicos

- **Descripción**: crear `scripts/role-collision.py`, la puerta que salva `ADR-011`. Generaliza la heurística que `lint_plugin.py` ya aplica al plugin (dos piezas con el mismo disparador literal entrecomillado → aviso) comparando el candidato contra las piezas **realmente instaladas** (hoy 9 agentes, 17 skills, 12 comandos, resueltas con el `find` de la regla 5) **y** contra las filas de `.claude/pieces.json`. Rechaza por nombre `test-writer`, `code-reviewer`, `security-auditor` y `doc-writer`.
- **Changelog**: Antes de crear una pieza nueva, el proyecto comprueba que no duplique una que ya existe y la rechaza nombrando la que ya cubre ese trabajo.
- **Estado**: borrador
- **Tiempo humano**: est. 2,0h · real —
- **Tiempo IA (ejec.)**: est. 0,16h · real —
- **Supervisión**: est. 0,04h (≈25 % IA) · real —
- **Previsión IA**: 60k in / 19k out tok · 0,71 €
- **Dependencias**: ninguna dura. **C-05 no debe entregarse sin ella** (condición (b) del go; el análisis: «sin ella, no vale construir esto»)
- **Archivos**: `scripts/role-collision.py`, `tests/test_role_collision.py`, `tests/test_console_encoding.py`
- **Verificación**:
  - `python3 -m pytest -q tests/test_role_collision.py` → verde, con los cuatro nombres canónicos rechazados nombrando su dueño
  - `python3 scripts/role-collision.py test-writer` → **exit 1** y una línea que nombra `unit-tests`/`tdd`
  - `python3 scripts/role-collision.py <nombre inventado sin colisión>` → **exit 0** y ninguna línea de colisión
  - `git add -N scripts/role-collision.py && python3 -m pytest -q tests/test_console_encoding.py` → verde

**Criterios de aceptación**
- [ ] CA-11 — rechaza **los cuatro** (`test-writer`, `code-reviewer`, `security-auditor`, `doc-writer`) nombrando la pieza instalada que ya los cubre: `unit-tests`/`tdd`, `reviewer`/`adversarial-review`, `nemesis`/`cybersecurity`, `documenter`
- [ ] CA-13 — el inventario son las piezas **realmente instaladas** más las filas de `.claude/pieces.json`, resuelto con el `find` de la regla 5 y **no** con una lista hardcodeada; test que añade una pieza al árbol temporal y la ve aparecer
- [ ] Es **aviso + veredicto** con la puerta humana detrás, **no** un deny: un falso positivo no bloquea nada por sí solo (`ADR-007`)
- [ ] Snippet de consola replicado literal y el script en la tabla `MODOS`

**Subtareas**
- [ ] Descubrimiento del inventario con el `find` de las seis raíces + lectura de los frontmatters
- [ ] Extracción de disparadores literales entrecomillados de cada `description` (misma heurística que el linter)
- [ ] Tabla de los cuatro nombres canónicos con su dueño, derivada del inventario y no escrita a mano
- [ ] Lectura de las filas del registro como parte del inventario
- [ ] Suite: los cuatro rechazos, el inventario descubierto, y un candidato limpio

**Notas**: riesgo anotado por la evaluación: falsos positivos que bloqueen piezas legítimas (el repo ya lo vivió — el linter de «nombre genérico» necesitó afinado en `debt-cleanup`) y falsos negativos por sinónimos que no comparten literal. La mitigación es que **hay una puerta humana detrás**, no un afinado infinito de la heurística.

<!-- ==================================================================== -->

### T-10 — Contrato de interfaz de `role-collision.py`: exit 0/1 y una línea por colisión

- **Descripción**: cerrar el contrato de salida para que `/specialize` lo consuma **sin parsear prosa**: exit 0 si no hay colisión, exit 1 si la hay, y por cada colisión **una línea** con el formato exacto `pieza instalada · disparador que choca · motivo`. El test **parsea la salida por el formato** y afirma **ambos** exit codes.
- **Changelog**: La puerta de colisión tiene un contrato fijo —cero si no hay choque, uno si lo hay, y una línea por colisión— para que otras piezas la usen sin interpretar texto.
- **Estado**: borrador
- **Tiempo humano**: est. 1,5h · real —
- **Tiempo IA (ejec.)**: est. 0,12h · real —
- **Supervisión**: est. 0,03h (≈25 % IA) · real —
- **Previsión IA**: 45k in / 14k out tok · 0,53 €
- **Dependencias**: T-09
- **Tipo**: test
- **Archivos**: `scripts/role-collision.py`, `tests/test_role_collision.py`
- **Verificación**:
  - `python3 -m pytest -q tests/test_role_collision.py` → verde, con el caso que **parsea el formato** de la línea y los dos casos de exit code
  - `python3 scripts/role-collision.py <candidato con disparador duplicado>; echo "exit=$?"` → `exit=1` y la línea con los **tres** campos separados por ` · `
  - `python3 scripts/role-collision.py <candidato limpio>; echo "exit=$?"` → `exit=0` y ninguna línea

**Criterios de aceptación**
- [ ] CA-12 — contrato cumplido: exit 0 sin colisión, exit 1 con ella, y una línea por colisión con el formato `pieza instalada · disparador que choca · motivo`; test que parsea la salida por el formato y comprueba **los dos** exit codes
- [ ] Un candidato cuyo disparador literal entrecomillado coincide con el de una pieza instalada **o ya generada** avisa con ese formato exacto (misma heurística que el linter aplica al plugin)
- [ ] El formato es estable y documentado en el propio `--help`: si cambia, el test se pone rojo
- [ ] El `·` del formato no rompe la consola cp1252 (el snippet ya reconfigura la salida a UTF-8 con `errors="replace"`); verificado por `tests/test_console_encoding.py`

**Subtareas**
- [ ] Fijar el formato de línea como constante única del script y citarla en `--help`
- [ ] Exit codes por camino, sin excepciones que se traguen el veredicto
- [ ] Test que parsea el formato campo a campo (no un `in` sobre la cadena entera)
- [ ] Test de disparador duplicado contra una pieza **generada** (fila del registro), no solo instalada

**Notas**: la evaluación **sube la confianza de C-04 de Media a Alta** precisamente por este contrato: cierra la incógnita que la pasada 1 dejaba abierta («¿exit ≠ 0 o campo JSON?»). Es el caso de manual en el que subir horas **baja** el riesgo.

<!-- ==================================================================== -->

### T-11 — `commands/specialize.md`: escalera de decisión y secuencia sobre los tres scripts

- **Descripción**: crear el comando. Secuencia —**no calcula**— el escaneo (`project-scan.py`), la escalera de decisión (nada → persona → tool → skill → agente) y la puerta de colisión (`role-collision.py`), y delega toda escritura en `pieces-registry.py`. Incluye el manejo de errores del registro: ante exit 2 (corrupto) dice el arreglo y **ofrece `--reconstruir` tras confirmación humana explícita**, nunca automático.
- **Changelog**: El comando `/specialize <área>` propone piezas de especialización para el proyecto, eligiendo siempre la forma más barata que resuelva el caso y rechazando lo que ya tiene dueño.
- **Estado**: borrador
- **Tiempo humano**: est. 2,5h · real —
- **Tiempo IA (ejec.)**: est. 0,19h · real —
- **Supervisión**: est. 0,05h (≈25 % IA) · real —
- **Previsión IA**: 70k in / 22k out tok · 0,83 €
- **Dependencias**: T-05 (API del registro), T-08 (evidencia), T-10 (contrato de la puerta de colisión). **Es la condición (a) del go hecha arista del grafo**
- **Archivos**: `commands/specialize.md`, `docs/README.md`, `docs/en/README.md`, `interop/`
- **Verificación**:
  - `python3 scripts/lint_plugin.py` → 0 errores (frontmatter, dependencias, disparadores duplicados)
  - `wc -l commands/specialize.md` → ≤ 200 líneas (`ADR-008`; el linter avisa por encima)
  - `python3 scripts/export-interop.py && python3 scripts/export-interop.py --check` → verde tras regenerar
  - lectura: ningún cálculo ni veredicto en la prosa del comando — cada paso nombra el script que decide y su exit code

**Criterios de aceptación**
- [ ] La escalera de decisión completa, con el escalón **«nada»** por abajo (duplica una pieza instalada → se rechaza nombrándola) y **agente** por arriba como último recurso con **override explícito del usuario**
- [ ] El comando **solo secuencia**: los tres veredictos (evidencia, colisión, propiedad) los dan los scripts con su exit code. Ninguna mecánica verificable vive en la prosa
- [ ] Manejo de errores del registro: exit 2 → nombra el arreglo y **ofrece `--reconstruir` tras confirmación explícita**; exit 3 → rehúsa y lo dice; exit 4 → «registro ocupado, reintenta»; exit 5 → aviso del tope con su motivo
- [ ] `/specialize` **no sabe de runtimes**: si hay otros instalados, **ofrece** `export-interop.py --root … --project`, nunca traduce por su cuenta ni automáticamente
- [ ] Frontmatter con `model` y `effort` declarados y `dependencies:` completo; fila en `docs/README.md` (+EN)
- [ ] `interop/` regenerado y `--check` en verde

**Subtareas**
- [ ] Frontmatter con `description` que no choque con `plugin-dev` (el negativo cruzado llega en T-14)
- [ ] Pasos del comando: escaneo → escalera → colisión → puerta humana (T-12) → nacimiento (registro) → validación → oferta de interop
- [ ] Tabla «qué NO hace» apuntando a `plugin-dev`, `/retro` y `export-interop.py`
- [ ] Camino de error por cada exit code del registro, con la oferta de `--reconstruir`
- [ ] Regenerar `interop/` y comprobar `--check`

**Notas**: cierra la **segunda** de las cosas que el `architect` dejó al plan (quién invoca `--reconstruir`): **`/specialize` lo ejecuta tras confirmación**, porque es la pieza que escribe; `/doctor` solo lo nombra (T-15), porque es solo lectura por contrato. `pieces.json` es un fichero **comiteado y compartido**: reconstruirlo en silencio pisaría el acuerdo de otra persona.

<!-- ==================================================================== -->

### T-12 — Las dos puertas: `--dry-run` del lote completo y N confirmaciones para N candidatos

- **Descripción**: implementar las dos puertas **separables** con su mecánica en el script, no en la prosa: `--dry-run`/`--plan` previsualiza el **lote completo** (forma, evidencia y resultado de la colisión de cada candidato) y **no escribe nada**; sin el flag se piden **exactamente N confirmaciones, una por candidato**, en el orden previsualizado. Incluye el tope de 5 **acumulado en el registro** y la confirmación **extra** cuando el destino es el árbol desplegado del propio plugin.
- **Changelog**: Antes de crear nada se ve el lote entero sin que se escriba un solo fichero, y luego se confirma pieza a pieza: rechazar una omite solo esa.
- **Estado**: borrador
- **Tiempo humano**: est. 2,5h · real —
- **Tiempo IA (ejec.)**: est. 0,19h · real —
- **Supervisión**: est. 0,05h (≈25 % IA) · real —
- **Previsión IA**: 70k in / 22k out tok · 0,83 €
- **Dependencias**: T-11
- **Archivos**: `commands/specialize.md`, `agent-kits/shared/pieces-registry.py`, `agent-kits/shared/test_pieces_registry.py`
- **Verificación**:
  - `python3 -m pytest -q agent-kits/shared/test_pieces_registry.py` → verde, con el test de `--dry-run` (árbol idéntico, diff vacío) y el de lote de 3 (confirma 2, rehúsa 1 → exactamente 2 piezas y 2 filas)
  - `<flujo --dry-run sobre un árbol temporal> && git -C <árbol> status --porcelain` → salida **vacía** y `.claude/pieces.json` sin cambios
  - `python3 agent-kits/shared/pieces-registry.py tope --project-dir <árbol con 5 filas>` → **exit 5** al intentar la sexta sin confirmación, con el motivo escrito

**Criterios de aceptación**
- [ ] CA-14 — `--dry-run` (o `--plan`) previsualiza el lote completo de N candidatos con su forma, evidencia y resultado de `role-collision.py`, y **no crea ningún fichero ni fila**. Test que afirma árbol idéntico y registro sin cambios
- [ ] CA-15 — sin `--dry-run` se piden **exactamente N confirmaciones, una por candidato**, en el orden previsualizado: confirmar una no aprueba las demás y rehusar una **solo omite esa pieza**. Test de lote 3 (2 sí, 1 no) → 2 piezas y 2 filas
- [ ] Si no se confirma **ninguna**, no se escribe nada y la salida es limpia con **exit 0** (no es un error)
- [ ] CA-18 — tope de **5 acumulado en el registro completo del proyecto**, no por invocación: la sexta fila que entraría, venga de esta invocación o de una posterior, produce aviso + confirmación extra, **nunca** un fallo silencioso. Test que genera 5 en **dos invocaciones distintas** y comprueba que la 6.ª dispara el aviso en cualquiera de las dos
- [ ] CA-17 (mitad de confirmación extra) — si la raíz del destino tiene marcadores `agent-kits/` o `.claude-plugin/` y el candidato es **skill o agente** (rutas indistinguibles de las del plugin), avisa y exige una confirmación humana **adicional**, anotada en la fila
- [ ] Motivo del tope **escrito** donde se avisa: `skill-index.py` `LIMITE_LINEAS = 45` / `LIMITE_CHARS = 3500`

**Subtareas**
- [ ] Modo previsualización del lote en el script, con salida determinista y ordenada
- [ ] Bucle de confirmación por candidato, con omisión individual
- [ ] Comprobación del tope sobre `len(piezas)` del registro, no sobre el lote
- [ ] Detección de marcadores de plugin desplegado + confirmación extra anotada
- [ ] Los tres tests: árbol idéntico, lote 3 (2/1), tope en dos invocaciones

**Notas**: la evaluación marca esto como su **Ambigüedad 1** y como riesgo transversal: «una puerta que vive en prosa no se puede testear». Si la mecánica del lote se quedase en el comando, CA-14 y CA-15 serían «verdes por afirmación» y la Lente A los marcaría como gap. Por eso baja al script.

<!-- ==================================================================== -->

### T-13 — `tools` mínimos, validación de lo generado con `--root`, eval del comando y paso de `/setup`

- **Descripción**: cerrar C-05 por sus cuatro extremos: `tools` mínimos por forma con la distinción **estático** (19a) / **comportamiento** (19b); validación de lo generado con las herramientas **existentes** (`lint_plugin.py --root`, `evals/check.py --root` — no se crea linter nuevo); el caso de eval del comando con ≥ 2 positivos y 1 negativo; y el paso nuevo de `/setup` que ofrece `/specialize` y pregunta `especializacion.topePiezas`.
- **Changelog**: Una pieza generada nace con los permisos mínimos, se valida con el linter y los evals que ya existen, y `/setup` pregunta cuántas piezas como máximo quieres en el proyecto.
- **Estado**: borrador
- **Tiempo humano**: est. 2,5h · real —
- **Tiempo IA (ejec.)**: est. 0,16h · real —
- **Supervisión**: est. 0,04h (≈25 % IA) · real —
- **Previsión IA**: 60k in / 18k out tok · 0,69 €
- **Dependencias**: T-12
- **Archivos**: `commands/specialize.md`, `commands/setup.md`, `evals/cases/command-specialize.json`, `agent-kits/shared/pieces-registry.py`, `agent-kits/shared/test_pieces_registry.py`, `interop/`
- **Verificación**:
  - `python3 evals/check.py` → verde, con ≥ 2 positivos y 1 negativo para `/specialize` y el literal casando con su `description` real
  - `python3 scripts/lint_plugin.py --root <árbol temporal con una pieza generada>` → **0 errores**; `python3 evals/check.py --root <ese árbol>` → verde
  - `python3 -m pytest -q agent-kits/shared/test_pieces_registry.py` → verde, con el test de 19b (candidato que pediría `Bash` sin confirmación registrada → frontmatter **sin** `Bash`)
  - `grep -n "specialize\|topePiezas" commands/setup.md` → el paso nuevo existe y nombra la clave

**Criterios de aceptación**
- [ ] CA-19a **(estático)** — una pieza generada declara `tools` **mínimos** para su forma: persona y tool sin `tools`; skill y agente sin `Bash`/`Write` salvo excepción registrada. Test sobre el frontmatter generado de **cada** forma
- [ ] CA-19b **(comportamiento)** — un candidato cuya escalera pediría `Bash` o `Write` **sin** que la fila de confirmación del registro lo registre explícitamente: el generador **rehúsa** emitir esos `tools` y degrada a los mínimos con aviso. Un hook de guardia (deny) **nunca** se genera sin opt-in explícito (`ADR-007`)
- [ ] CA-16 — lo generado pasa la validación con las herramientas **existentes**: `lint_plugin.py --root` con 0 errores y `evals/check.py --root` en verde. **No se crea linter nuevo**
- [ ] Caso `evals/cases/command-specialize.json` con ≥ 2 positivos (literal + paráfrasis) y 1 negativo; el cruzado con `plugin-dev` llega en T-14
- [ ] `/setup` ofrece `/specialize` al terminar y pregunta `especializacion.topePiezas` (default 5, con el motivo del presupuesto de arranque escrito); idempotente como el resto de sus pasos
- [ ] `interop/` regenerado y `--check` en verde

**Subtareas**
- [ ] Tabla `tools` mínimos por forma, en el script y no en la prosa
- [ ] Camino de rechazo de 19b con su aviso y su degradación
- [ ] Invocación de `lint_plugin.py --root` y `evals/check.py --root` tras cada nacimiento
- [ ] Generación del caso de eval de la pieza (≥ 2 positivos + 1 negativo)
- [ ] `evals/cases/command-specialize.json` del propio comando
- [ ] Paso de `/setup` con la pregunta del tope y la oferta de `/specialize`
- [ ] Regenerar `interop/` y comprobar `--check`

**Notas**: cierra la **primera** de las cosas que el `architect` dejó al plan por su lado de `/setup` (la clave la fija T-06/§Cambios arquitectónicos: `especializacion.topePiezas`). Incógnita anotada por la evaluación y **no resuelta aquí a propósito**: si las evals generadas entran en la CI del consumidor o solo se validan al generar — esta tarea implementa lo segundo, que es lo que la spec exige; lo primero es alcance de una iniciativa del consumidor, no de esta.

<!-- ==================================================================== -->

### T-14 — Desambiguación con `plugin-dev`: `description` «de ESTE plugin» y negativos cruzados

- **Descripción**: la `description` de `plugin-dev` promete hoy literalmente «crea un agente/skill/comando nuevo», que es **exactamente** el disparador de `/specialize`. Se reescribe para que sus disparadores digan **«de ESTE plugin»**, se añaden **negativos cruzados** en las evals de ambas piezas («crea un agente para el plugin» como negativo de `/specialize`, y el recíproco en `plugin-dev`), y las dos ganan fila «qué NO hace» apuntándose mutuamente.
- **Changelog**: Pedir «crea un agente» ya no es ambiguo: `plugin-dev` se ocupa de las piezas del plugin y `/specialize` de las piezas del proyecto, y cada una dice explícitamente qué no hace.
- **Estado**: borrador
- **Tiempo humano**: est. 1,5h · real —
- **Tiempo IA (ejec.)**: est. 0,11h · real —
- **Supervisión**: est. 0,03h (≈25 % IA) · real —
- **Previsión IA**: 40k in / 12k out tok · 0,46 €
- **Dependencias**: T-13 (el caso de eval de `/specialize` ya existe, así que el negativo cruzado tiene dónde ir). **Es la condición (b) del go: entra en el mismo tramo que C-05, no después**
- **Tipo**: docs
- **Archivos**: `skills/plugin-dev/SKILL.md`, `evals/cases/skill-plugin-dev.json`, `evals/cases/command-specialize.json`, `commands/specialize.md`, `interop/`
- **Verificación**:
  - `python3 evals/check.py` → verde, con los negativos cruzados en **ambos** sentidos y el literal casando con las descriptions reales
  - `grep -n "ESTE plugin" skills/plugin-dev/SKILL.md` → la `description` lo dice
  - `grep -n "plugin-dev" commands/specialize.md && grep -n "specialize" skills/plugin-dev/SKILL.md` → las dos filas «qué NO hace» se apuntan
  - `python3 scripts/lint_plugin.py` → 0 errores, **sin** aviso de disparador literal duplicado entre las dos piezas
  - `python3 scripts/export-interop.py --check` → verde tras regenerar (la `description` de una skill viaja sin traducir y no puede pasar de 1.024 caracteres)

**Criterios de aceptación**
- [ ] CA-22 — la `description` de `plugin-dev` dice «de ESTE plugin» en sus disparadores; «crea un agente para el plugin» es **negativo** del caso de `/specialize` y el recíproco es negativo del de `plugin-dev`; ambas piezas tienen fila «qué NO hace» apuntándose. `evals/check.py` en verde
- [ ] El linter deja de avisar de disparador literal duplicado entre las dos piezas (el guardarraíl heurístico que `lint_plugin.py` ya aplica)
- [ ] La `description` de `plugin-dev` sigue por debajo de **1.024 caracteres** (techo de OpenCode) y de los 1.200 del aviso del linter
- [ ] `interop/` regenerado y `--check` en verde

**Subtareas**
- [ ] Reescribir los disparadores de `plugin-dev` acotándolos a las piezas del plugin
- [ ] Negativo cruzado en `evals/cases/command-specialize.json` con su `redirect` a `plugin-dev`
- [ ] Negativo recíproco en `evals/cases/skill-plugin-dev.json` con su `redirect` a `/specialize`
- [ ] Filas «qué NO hace» en las dos piezas
- [ ] Regenerar `interop/` y comprobar longitud de `description` y `--check`

**Notas**: la evaluación la clasifica como complejidad **Baja** y **efecto alto**: sin ella quedan dos meta-generadores compitiendo por la misma frase y el modelo elige mal. Riesgo anotado: «que se despache como cosmética» — `evals/check.py` exige que el literal case con la `description` real, así que el linter no la deja a medias (`LES-011`).

<!-- ==================================================================== -->

### T-15 — Sección de especialización en `/doctor`: una línea por fila y los tres estados

- **Descripción**: `agent-kits/shared/doctor.py` (1.084 líneas, con `test_doctor.py` ya en pie) gana una sección que consume `pieces-registry.py listar --json` y `auditar` y emite **una línea por fila** del registro: ✅ `gestionada` / ⚠️ `modificada` con su arreglo («revisa el diff y confirma») / ❌ fila sin fichero. Las piezas escritas a mano sin fila salen como **«no gestionada»**, que es un estado **válido** y **no** cuenta como error: ofrece adopción. Ante un registro corrupto **nombra** `--reconstruir` y no lo ejecuta.
- **Changelog**: `/doctor` audita las piezas de especialización del proyecto con una línea por pieza, distinguiendo las que siguen igual, las editadas a mano y las escritas a mano sin registrar.
- **Estado**: borrador
- **Tiempo humano**: est. 2,0h · real —
- **Tiempo IA (ejec.)**: est. 0,17h · real —
- **Supervisión**: est. 0,04h (≈25 % IA) · real —
- **Previsión IA**: 65k in / 18k out tok · 0,71 €
- **Dependencias**: T-05 (no hay qué auditar sin filas). **Ya no depende de C-05 para el esquema: es la mejora del grafo que trae la condición (a) del go**
- **Archivos**: `agent-kits/shared/doctor.py`, `agent-kits/shared/test_doctor.py`, `commands/doctor.md`, `docs/agents/`
- **Verificación**:
  - `python3 -m pytest -q agent-kits/shared/test_doctor.py` → verde, con los casos de los tres estados y de «no gestionada»
  - `python3 agent-kits/shared/doctor.py --json --project-dir <árbol con 3 piezas en tres estados>` → una entrada por fila, con su veredicto y su arreglo
  - `python3 agent-kits/shared/doctor.py --project-dir <árbol con registro corrupto>` → ⚠️ con `--reconstruir` **nombrado** y **sin ejecutarlo** (el registro sigue igual: `git status --porcelain` vacío)
  - `python3 scripts/lint_plugin.py` → 0 errores

**Criterios de aceptación**
- [ ] CA-20 — hay sección de especialización con **una línea por fila** del registro: ✅ `gestionada` / ⚠️ `modificada` con su arreglo / ❌ fila sin fichero; y las piezas escritas a mano sin fila salen «no gestionada» ofreciendo adopción, **sin** contar como error
- [ ] `/doctor` sigue siendo **solo lectura**: nombra `--reconstruir` como arreglo y **jamás** lo ejecuta. Test que lo afirma comparando el registro antes y después
- [ ] Consume el contrato de `pieces-registry.py` (`listar --json`, `auditar`) y **no** recalcula hashes ni estados por su cuenta: un solo dueño del veredicto
- [ ] `--json` incluye la sección nueva sin romper el esquema existente; exit 1 solo si hay ❌
- [ ] La sección y sus tres estados documentados en `commands/doctor.md` y en el doc del comando

**Subtareas**
- [ ] Lector de `listar --json` / `auditar` con degradación si el script no está (aviso, nunca traceback)
- [ ] Render de una línea por fila con el arreglo por estado
- [ ] «No gestionada» como estado válido con oferta de adopción
- [ ] Camino de registro corrupto: nombra el arreglo, no lo ejecuta
- [ ] Casos en `test_doctor.py` + doc del comando

**Notas**: cierra la **segunda** de las cosas que el `architect` dejó al plan por su lado de diagnóstico (`/doctor` nombra `--reconstruir`; `/specialize` lo ejecuta, T-11). Riesgo anotado por la evaluación: que la sección salga ✅ con el registro vacío y dé **falsa seguridad** — es exactamente el defecto que `memory-retrieval` encontró en `/doctor` («Instalación sana» con 0 entradas de journal). Se cierra en T-16.

<!-- ==================================================================== -->

### T-16 — Biyección registro ↔ ficheros con mutante de hash, y «sin registro» ≠ «registro sano»

- **Descripción**: el test que sostiene la auditoría, con el patrón de `tests/test_knowledge_index.py`: fila sin fichero y fichero sin fila salen ⚠️; fichero con hash distinto del anotado sale **`modificada`**, nunca ⚠️ genérico. Con su **mutante de hash** además del mutante de fila. Y el criterio explícito que distingue «no hay registro» de «el registro está sano», para que la sección no dé falsa seguridad con cero filas.
- **Changelog**: La auditoría del registro no puede quedarse verde por accidente: un fichero editado a mano, una fila sin fichero o un registro vacío se distinguen y se reportan cada uno como lo que es.
- **Estado**: borrador
- **Tiempo humano**: est. 1,0h · real —
- **Tiempo IA (ejec.)**: est. 0,09h · real —
- **Supervisión**: est. 0,02h (≈25 % IA) · real —
- **Previsión IA**: 35k in / 10k out tok · 0,39 €
- **Dependencias**: T-15
- **Tipo**: test
- **Archivos**: `agent-kits/shared/test_doctor.py`, `agent-kits/shared/doctor.py`
- **Verificación**:
  - `python3 -m pytest -q agent-kits/shared/test_doctor.py` → verde, con el mutante de **fila** y el mutante de **hash**, y cada uno poniendo rojo su propia aserción
  - `python3 agent-kits/shared/doctor.py --json --project-dir <árbol sin pieces.json>` → veredicto de «sin registro», **distinto** del de «registro sano»
  - mutación manual del hash de una fila → la línea sale `modificada`, **no** ⚠️ genérico

**Criterios de aceptación**
- [ ] CA-21 — biyección **registro ↔ ficheros**: fila sin fichero y fichero sin fila salen ⚠️; fichero con hash distinto del anotado sale **`modificada`** y nunca ⚠️ genérico. Test determinista **con su mutante**, incluido el **mutante de hash**
- [ ] Los dos mutantes fallan por separado: si se rompe solo la comprobación de filas, el mutante de hash sigue verde y viceversa (ninguno cubre al otro por casualidad)
- [ ] Criterio explícito para «sin registro» **distinto** de «registro sano»: con cero filas el veredicto no es ✅ a secas
- [ ] Ningún test se parametriza con la constante que debería fijar (lección de `changelog-brief` T-06: 14 de 25 mutantes sobrevivían por eso)

**Subtareas**
- [ ] Fixture con las cuatro situaciones: gestionada, modificada, fila huérfana, fichero sin fila
- [ ] Mutante de fila (borrar el fichero de una fila) y mutante de hash (editar el fichero)
- [ ] Caso de árbol sin `pieces.json` con su veredicto propio
- [ ] Repasar que los asserts no lean las constantes del código bajo prueba

**Notas**: el patrón de biyección con mutante viene de `tests/test_knowledge_index.py`, que es el mismo mecanismo con el que el bucle de memoria demuestra que su registro canónico no se desincroniza. Es lo que convierte esto en un **bucle** y no en un conjunto de piezas (`analysis.md` §2).

<!-- ==================================================================== -->

### T-17 — Modo proyecto de `export-interop.py`: flag `--project` y plan de salida `.codex/`/`.opencode/`

- **Descripción**: `export-interop.py` (531 líneas) aprende el **modo proyecto** con un flag explícito `--project`: plan de salida `.codex/…` + `.opencode/…` en lugar de `interop/` + `.codex-plugin/`, y tolerancia a manifiestos y hooks ausentes (un `.claude/` de consumidor no tiene `.claude-plugin/plugin.json` ni `marketplace.json`). **Sin** el flag, `--root` sobre un árbol de proyecto sigue saliendo con **exit 1**: ese es el test que impide la regresión de la inferencia.
- **Changelog**: `export-interop.py --project` traduce las piezas de un proyecto a Codex y OpenCode con el mismo mecanismo con el que el plugin se traduce a sí mismo, sin que el comando de especialización sepa de runtimes.
- **Estado**: borrador
- **Tiempo humano**: est. 2,0h · real —
- **Tiempo IA (ejec.)**: est. 0,15h · real —
- **Supervisión**: est. 0,04h (≈25 % IA) · real —
- **Previsión IA**: 55k in / 17k out tok · 0,64 €
- **Dependencias**: ninguna dura. **El modo lo decide este plan** (§Cambios arquitectónicos, decisión 4 + `ADR-015`), que es la condición (d) del go: se decide **antes** de abrir la tarea, no dentro
- **Tipo**: devops
- **Archivos**: `scripts/export-interop.py`, `interop/`, `docs/knowledge/adr/ADR-015-modo-proyecto-explicito-en-export-interop.md`
- **Verificación**:
  - `python3 scripts/export-interop.py --root <árbol de consumidor>; echo "exit=$?"` → `exit=1` pidiendo `.claude-plugin/plugin.json` (**el comportamiento de hoy no cambia sin el flag**)
  - `python3 scripts/export-interop.py --root <árbol de consumidor> --project` → **exit 0**, y las variantes aparecen en `<árbol>/.codex/` y `<árbol>/.opencode/`, **no** en `interop/` ni `.codex-plugin/`
  - `python3 scripts/export-interop.py && python3 scripts/export-interop.py --check` → verde sobre el propio repo (el modo plugin intacto)
  - `python3 -m pytest -q tests/test_export_interop.py` → verde (la línea base de 17 tests sigue pasando)

**Criterios de aceptación**
- [ ] El modo se activa con **flag explícito `--project`**, nunca por inferencia de la ausencia de `.claude-plugin/`: sin el flag, un árbol de consumidor sigue dando **exit 1**
- [ ] Plan de salida del modo proyecto: `.codex/…` y `.opencode/…` en el árbol del proyecto; **cero escrituras** en `interop/` o `.codex-plugin/`
- [ ] Tolerancia a manifiestos y hooks ausentes, con aviso y sin inventar contenido
- [ ] El modo plugin **no cambia en nada**: `--check` sigue verde sobre este repo (es puerta de CI y de `release.py`)
- [ ] `--check --project` compara contra el plan de salida del modo proyecto, no contra el del plugin
- [ ] `ADR-015` escrito en `docs/knowledge/adr/` con estado `propuesta` y su fila en `docs/knowledge/README.md`

**Subtareas**
- [ ] `argparse`: `--project` y su propagación a `generar(root)` y a `--check`
- [ ] Separar el plan de salida en dos (plugin / proyecto) sin duplicar los traductores
- [ ] Tolerancia a manifiestos y hooks ausentes
- [ ] Comprobar que el modo plugin no se desvía: regenerar y `--check`

**Notas**: la premisa heredada de la spec («`--root` ya acepta cualquier árbol con forma de plugin (verificado)») es **falsa** y la evaluación la corrigió con comando y exit code (§Ambigüedad 2). Lección para toda esta fase: los «(verificado)» heredados **se re-ejecutan**, no se heredan. Añadir un runtime futuro sigue siendo una fila en `PROVIDERS` de `install/providers.mjs` (con `IDS` ya exportado) más su traductor — **nunca** un cambio en `/specialize`.

<!-- ==================================================================== -->

### T-18 — Casos de `tests/test_export_interop.py` sobre un árbol de proyecto (estrena `tmp_path` en esa suite)

- **Descripción**: `tests/test_export_interop.py` tiene hoy **245 líneas y 17 tests, todos sobre el árbol real del repo y ni un `tmp_path`**: un caso sobre árbol de proyecto **estrena el patrón de fixture** en esa suite. Se añaden los casos de `--project` (variantes generadas en `.codex/`/`.opencode/`), el de `--root` sin flag (exit 1) y el de `--check` **detectando la desincronización** de una variante.
- **Changelog**: La suite de interoperabilidad prueba el modo proyecto sobre un árbol temporal, incluida la detección de una variante que quedó desincronizada.
- **Estado**: borrador
- **Tiempo humano**: est. 1,5h · real —
- **Tiempo IA (ejec.)**: est. 0,12h · real —
- **Supervisión**: est. 0,03h (≈25 % IA) · real —
- **Previsión IA**: 45k in / 14k out tok · 0,53 €
- **Dependencias**: T-17
- **Tipo**: test
- **Archivos**: `tests/test_export_interop.py`
- **Verificación**:
  - `python3 -m pytest -q tests/test_export_interop.py` → verde, con los 17 tests previos **intactos** más los nuevos
  - `python3 -m pytest -q tests/test_export_interop.py -k project` → los casos nuevos pasan por sí solos
  - test de desincronización: tras generar, tocar una variante y correr `--check --project` → **exit ≠ 0** con el fichero desincronizado nombrado

**Criterios de aceptación**
- [ ] CA-29 — con piezas nacidas de `/specialize` en `.claude/` y Codex y/o OpenCode «instalados», `export-interop.py --root <proyecto> --project` genera las variantes en `.codex/` y `.opencode/` **exactamente igual** que para las piezas del plugin (mismo mecanismo), y `--check` detecta cuando una variante quedó desincronizada
- [ ] El caso de `--root` **sin** `--project` sobre el mismo árbol sigue dando **exit 1**: es la garantía de que no se colará la inferencia más adelante
- [ ] Fixture con `tmp_path` que construye un `.claude/` de consumidor mínimo (una persona, una skill, un agente) y **no** depende del árbol real del repo
- [ ] Los 17 tests previos siguen verdes sin retocar sus asserts

**Subtareas**
- [ ] Fixture `tmp_path` del árbol de consumidor mínimo, con las tres formas portables
- [ ] Test del plan de salida `.codex/`/`.opencode/`
- [ ] Test de `--root` sin flag → exit 1
- [ ] Test de `--check --project` con una variante tocada a mano

**Notas**: la evaluación reparte C-11 en ~2,0 h (modo proyecto) + ~1,5 h (esta suite) + ~0,5 h (filas por runtime) + ~0,5 h (fila de `INTEROP.md`), y avisa de que el fixture **estrena patrón** en esta suite: es la parte donde una estimación de 1,5 h se puede quedar corta si el árbol mínimo resulta no ser tan mínimo.

<!-- ==================================================================== -->

### T-19 — Destinos por runtime en el registro y fila de degradación en `docs/INTEROP.md` (+EN)

- **Descripción**: cerrar C-11 por sus dos extremos que faltan: que `export-interop.py` **registre** cada ruta que escribe con su `runtime` y su propio hash (una entrada `destinos[]` por variante, dentro de la pieza — forma O1), y la **fila nueva** en la tabla de degradación de `docs/INTEROP.md` §4 (+ espejo EN) con el **límite honesto** escrito.
- **Changelog**: El registro anota cada variante escrita para otro runtime con su propia ruta y hash, y la documentación de interoperabilidad dice con claridad qué se pierde fuera de Claude Code.
- **Estado**: borrador
- **Tiempo humano**: est. 1,0h · real —
- **Tiempo IA (ejec.)**: est. 0,08h · real —
- **Supervisión**: est. 0,02h (≈25 % IA) · real —
- **Previsión IA**: 30k in / 9k out tok · 0,35 €
- **Dependencias**: T-05 (API de escritura del registro), T-18 (el modo proyecto ya probado)
- **Archivos**: `scripts/export-interop.py`, `agent-kits/shared/pieces-registry.py`, `agent-kits/shared/test_pieces_registry.py`, `docs/INTEROP.md`, `docs/en/INTEROP.md`
- **Verificación**:
  - `python3 -m pytest -q agent-kits/shared/test_pieces_registry.py -k runtime` → verde: una pieza multi-runtime produce **N destinos**, cada uno con su ruta, su `runtime` y su hash
  - `grep -n "specialize" docs/INTEROP.md docs/en/INTEROP.md` → la fila nueva en los **dos** ficheros
  - `python3 agent-kits/shared/pieces-registry.py listar --json --project-dir <árbol tras --project>` → los destinos `.codex/`/`.opencode/` anotados con hash propio
  - `python3 scripts/export-interop.py --check` → verde tras regenerar

**Criterios de aceptación**
- [ ] CA-28 — el registro anota, por cada pieza traducida, la **ruta escrita y su hash por runtime** (p. ej. un destino `.claude/personas/hooks.md` y otro `.codex/agents/hooks.toml`, cada uno con el suyo), igual que el plugin ya hace consigo mismo en `interop/`. Test con una pieza multi-runtime que comprueba los N destinos
- [ ] CA-30 — `docs/INTEROP.md` (+ espejo `docs/en/INTEROP.md`) tiene una **fila nueva** en la tabla de degradación §4 con el límite honesto escrito: la puerta de confirmación humana de `/specialize` es un **comando** de Claude Code y, fuera de él, se traduce a un *prompt* — depende de que el runtime lo **respete**, no de una barrera técnica (misma clase de degradación que la fila del guardrail del `implementer`)
- [ ] `runtime` sigue siendo un **dato** del destino y nunca una clave del esquema: un cuarto runtime no toca el esquema ni `/specialize`
- [ ] La **portabilidad por escalón** queda escrita: persona y tool neutrales, skill viaja sin traducir (con el techo de 1.024 caracteres de `description` de OpenCode), agente **exige** traducción real

**Subtareas**
- [ ] `export-interop.py` llama a `registrar` con `--destino <ruta>:<runtime-id>` por cada variante escrita
- [ ] Test de pieza multi-runtime con N destinos y hashes distintos
- [ ] Fila de degradación en `docs/INTEROP.md` §4 y su espejo EN, en el mismo cambio
- [ ] Tabla de portabilidad por escalón en la doc (o puntero a `SPECIALIZATION.md` si ya la lleva)

**Notas**: el límite honesto **no es un defecto, es la naturaleza del medio**, y por eso va como riesgo escrito y no como promesa. El registro no valida el `runtime-id` contra una lista cerrada (diseño §2.0): enumerar los runtimes en el esquema convertiría cada proveedor nuevo en una migración.

---

## Fase 3 — Revisión, corrección y cierre

**Estado**: borrador · **Estimado**: 10,0h · **Real**: — · **Coste est.**: 504,35 € · **Tokens est.**: 525k

> Las dos **líneas de proceso** que `CALIBRATION.md` obliga a presupuestar aparte (`LES-008`) y que la **condición (c)** del go prohíbe recortar para financiar alcance: 21,3 % de las horas base. El precedente medido está fresco: `memory-retrieval` (2026-09-08) necesitó **3 rondas**, encontró **38 gaps (3 Critical)** y se desvió **+66 %** en horas IA. Aquí hay **35 CA** que la Lente A tiene que recorrer, no 28.

### T-20 — Revisión adversarial de dos lentes de la Fase 1 y de la Fase 2

- **Descripción**: pasar la revisión adversarial (skill `adversarial-review`, fuente única del método) sobre el diff de cada fase, en **contexto fresco**: Lente A (conformidad con spec, plan y diseño, ✓/✗ por criterio con cita) y Lente B (defectos de corrección), más las condicionales C (seguridad) y D (rendimiento) si `review-lens-select.py` las activa. Bucle acotado a **3 intentos** por tramo, con la traza «Revisión de dos lentes — intento N» en este ledger.
- **Changelog**: El trabajo de las dos fases pasa una revisión adversarial en contexto fresco antes de darse por bueno, con los hallazgos graduados y trazados en el ledger.
- **Estado**: borrador
- **Tiempo humano**: est. 5,0h · real —
- **Tiempo IA (ejec.)**: est. 0,59h · real —
- **Supervisión**: est. 0,15h (≈25 % IA) · real —
- **Previsión IA**: 225k in / 56k out tok · 2,32 €
- **Dependencias**: T-03 (cierra F1) y T-19 (cierra F2). Se ejecuta **por tramos**, uno por fase, no una vez al final
- **Archivos**: `docs/roadmap/2026-09-09-project-specialization/tasks.md`, `docs/knowledge/adr/ADR-014-registro-de-piezas-agregado-con-la-pieza-como-raiz.md`, `docs/knowledge/adr/ADR-015-modo-proyecto-explicito-en-export-interop.md`
- **Verificación**:
  - `python3 agent-kits/shared/scope-check.py docs/roadmap/2026-09-09-project-specialization/tasks.md` → **exit 0** (el diff ⊆ los campos `Archivos` del ledger) antes de despachar cada lente
  - `grep -n "Revisión de dos lentes — intento" docs/roadmap/2026-09-09-project-specialization/tasks.md` → una traza por intento y por tramo
  - `python3 agent-kits/shared/review-lens-select.py --diff <rango del tramo>` → deja por escrito si las lentes C y D entran, y por qué

**Criterios de aceptación**
- [ ] Lente A recorre **los 33 CA de F1, F2 y cierre** con ✓/✗ y cita `fichero:línea` por cada uno; CA-34 se marca explícitamente **abierto**, no aprobado
- [ ] Lente B emite solo defectos de corrección, graduados Critical / Important / Minor, cada uno con su escenario concreto
- [ ] Las lentes C y D se activan o se descartan por `review-lens-select.py`, con el motivo escrito (no por criterio del revisor)
- [ ] Traza «Revisión de dos lentes — intento N» en este ledger por cada intento de cada tramo; bucle **acotado a 3**
- [ ] Un rebate solo vale **con evidencia ejecutada**; «sin defectos» es una salida válida de una lente
- [ ] Si el bucle de un tramo cierra **sin gaps pendientes**, `ADR-014` y `ADR-015` pasan a `estado: aceptada (validada: revisión de dos lentes, AAAA-MM-DD, intento N)` en el **mismo cambio**; si no cierra limpio, se quedan en `propuesta`

**Subtareas**
- [ ] Puerta previa por tramo: `scope-check.py` en verde
- [ ] Despachar las lentes al agente `reviewer` (contexto fresco, solo lectura) en paralelo
- [ ] Fusionar, graduar y anotar la traza en el ledger
- [ ] Al 3.er rojo de un tramo, invocar la skill `debug-root-cause` **antes** de preguntar al usuario
- [ ] Promover o dejar en `propuesta` los dos ADR según cierre el bucle

**Notas**: la Lente A tiene un insumo extra en esta iniciativa: el **contrato de §2.0 del diseño** (subcomandos, exit codes 0/1/2/3/4/5, hash normalizado, dos promesas con dos tests, `dueno()` como única puerta). Un CA cuyo veredicto sea «se comporta bien» sin comando que lo demuestre es un gap, no un ✓. Antes del veredicto se aplica la **tabla de racionalización** de `agent-kits/shared/rationalization-table.md`.

<!-- ==================================================================== -->

### T-21 — Corrección de los gaps de la revisión

- **Descripción**: corregir los hallazgos de T-20 en el orden de su gravedad (Critical → Important → Minor), volviendo a la tarea que los originó y re-ejecutando su `Verificación`. Los candidatos de la evaluación a concentrar Critical son C-05 (`GOT-003`, complejidad Muy alta, confianza Baja), C-10 (el cerrojo) y C-11 (la premisa corregida).
- **Changelog**: Los defectos que encuentra la revisión se corrigen antes de cerrar, cada uno con la verificación de su tarea vuelta a ejecutar.
- **Estado**: borrador
- **Tiempo humano**: est. 4,5h · real —
- **Tiempo IA (ejec.)**: est. 0,46h · real —
- **Supervisión**: est. 0,11h (≈25 % IA) · real —
- **Previsión IA**: 175k in / 44k out tok · 1,82 €
- **Dependencias**: T-20
- **Archivos**: los de las tareas que originen gaps (se anotan aquí al conocerlos, para que `scope-check.py` no salte)
- **Verificación**:
  - por cada gap corregido, la `Verificación` de su tarea de origen vuelta a ejecutar y pegada en el ledger → mismo resultado esperado
  - `python3 -m pytest -q` → verde sobre la línea base de la suite
  - `python3 scripts/lint_plugin.py` → 0 errores
  - `grep -n "Critical" docs/roadmap/2026-09-09-project-specialization/tasks.md` → ningún Critical sin corregir ni rebatido con evidencia

**Criterios de aceptación**
- [ ] Cero gaps **Critical** abiertos: corregidos, o rebatidos **con evidencia ejecutada**, o aceptados por el usuario como deuda **escrita**
- [ ] Cada corrección re-ejecuta la `Verificación` de su tarea de origen y pega la salida; no se cierra un gap «por lectura»
- [ ] Un gap que revele un CA mal escrito se corrige en el **CA**, no en el veredicto, y se dice
- [ ] Los Minor que no se corrijan quedan como **deuda declarada** con su tarea y su motivo, nunca en silencio

**Subtareas**
- [ ] Ordenar los gaps por gravedad y agruparlos por tarea de origen
- [ ] Corregir, re-ejecutar la verificación y anotar la salida
- [ ] Actualizar `Archivos` de esta tarea con lo realmente tocado (puerta de `scope-check.py`)
- [ ] Declarar la deuda que quede, con tarea y motivo

**Notas**: `LES-009` y la fila de `CALIBRATION.md` del 2026-09-08 son inequívocos: **esta es la partida grande y no se recorta**. La línea de corrección conserva sus 5,0 h; 4,5 h están aquí y 0,5 h en T-22, y esa redistribución está declarada en el plan (§Estimación por fase).

<!-- ==================================================================== -->

### T-22 — Puerta de cierre: lint, suites, `--check`, changelog y retro

- **Descripción**: la puerta de cierre estándar del repo, que es trabajo y no adorno: `lint_plugin.py` con 0 errores, `pytest` en verde, `export-interop.py --check` en verde, entradas `[Unreleased]`/`[Sin publicar]` en los **dos** CHANGELOG vía `changelog-sync`, y la puerta de `/retro` (`retro.md` + fila en `CALIBRATION.md`), sin la cual `/dev-cycle` no cierra.
- **Changelog**: La iniciativa se cierra con las puertas del repo en verde y su retrospectiva escrita, que es la que alimenta la calibración de las estimaciones siguientes.
- **Estado**: borrador
- **Tiempo humano**: est. 0,5h · real —
- **Tiempo IA (ejec.)**: est. 0,05h · real —
- **Supervisión**: est. 0,01h (≈25 % IA) · real —
- **Previsión IA**: 20k in / 5k out tok · 0,21 €
- **Dependencias**: T-21
- **Tipo**: devops
- **Archivos**: `CHANGELOG.md`, `CHANGELOG.es.md`, `docs/roadmap/2026-09-09-project-specialization/retro.md`, `docs/roadmap/CALIBRATION.md`, `docs/roadmap/README.md`, `interop/`
- **Verificación**:
  - `export PATH="$PWD/.venv/Scripts:$PATH" && python3 scripts/lint_plugin.py` → **0 errores**
  - `python3 -m pytest -q` → verde sobre la línea base de la suite
  - `python3 scripts/export-interop.py --check` → verde
  - `python3 evals/check.py` → verde
  - `python3 agent-kits/shared/retro-gate.py` → verde (`retro.md` + fila en `CALIBRATION.md`)
  - `python3 agent-kits/shared/ledger-lint.py docs/roadmap/2026-09-09-project-specialization/tasks.md` → **exit 0**

**Criterios de aceptación**
- [ ] CA-31 — `lint_plugin.py` con 0 errores, `pytest -q` en verde, `export-interop.py --check` en verde, entradas en los **dos** CHANGELOG vía `changelog-sync`, y `/setup` ofreciendo `/specialize` al terminar
- [ ] CA-32 — cada pieza nueva con doc en `docs/`, fila en `docs/README.md`, fila en `docs/agents/ROLES.md` y las reglas **3 y 9** de `CONVENTIONS.md` actualizadas (+EN)
- [ ] CA-33 — `retro.md` en esta carpeta + fila en `docs/roadmap/CALIBRATION.md`; `retro-gate.py` en verde
- [ ] La fila de la iniciativa en `docs/roadmap/README.md` está **dentro de la tabla** y cita `plan` y `tasks` (lo vigila `tests/test_roadmap_index.py`)
- [ ] La spec pasa a `estado: implementada` y su callout apunta al plan y al ledger
- [ ] La retro anota el **ratio tokens/hora medido** de esta iniciativa y, si el dato existe, la **primera fila con horas humanas reales** del histórico (el mayor agujero del presupuesto según la evaluación)

**Subtareas**
- [ ] Correr las cinco puertas con `.venv/Scripts` en el `PATH`
- [ ] `changelog-sync` sobre este ledger cerrado (los campos `- **Changelog**:` de las 22 tareas ya están escritos)
- [ ] `/retro` sobre la iniciativa: real vs estimado, causas, ratio medido, candidatas a lección del journal
- [ ] Fila en `CALIBRATION.md` y actualización de la fila del índice del roadmap
- [ ] `spec.md` a `implementada`

**Notas**: `retro-gate.py` es **puerta**, no cortesía: sin `retro.md` y su fila, `/dev-cycle` no cierra (paso 8 de su Fase 6). Estas 0,5 h salen de la línea de corrección post-revisión, cuyas 5,0 h siguen íntegras dentro de esta fase; la redistribución está declarada en el plan y **no financia ninguna característica** (condición (c) del go).

## Revision de dos lentes - intento 1: 6 Important, 6 Minor (lentes A+B)

Lentes que corrieron: **A** (conformidad con plan/ledger, criterio de prosa `docs-style.md`) y **B**
(correccion, con persona de dominio `docs`). Las condicionales **no** aplicaron:
`review-lens-select.py --base HEAD` devolvio `lente_c: false` y `lente_d: false` (sin motivos: la
prosa y `docs/**` estan excluidas de ambas heuristicas y `task-brief.py` no casa ningun patron
sensible ni costoso). Ambas lentes al agente `reviewer` (solo lectura), contexto fresco, en paralelo.
Puerta previa `scope-check.py --base HEAD`: los 9 ficheros del diff **en alcance**; los 5 fuera son
ruido sin seguimiento previo a la sesion, ya fichado en `CONTINUE-HERE.md`.

| # | Grado | Gap | Tarea | Correccion | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | `open()` sin guarda en la cascada: cualquier `OSError` en el escalon 1 aborta el brief (exit 1 + traceback) en vez de caer al escalon 2, contra el contrato de su propio docstring | T-01 | corregido: `_persona()` envuelve `open()` en `try/except OSError` y cae al siguiente escalón con aviso (`task-brief.py:378-383`); test `test_cascada_oserror_en_escalon_1_no_aborta_cae_al_catalogo` | `task-brief.py:369`. Reproducido con `icacls /deny`: `PermissionError`, exit 1, brief no emitido; con el codigo de `HEAD` el mismo comando devolvia el brief. Disparador realista: fichero "solo en la nube" de OneDrive sin red |
| 2 | Important | La persona de proyecto se inyecta integra, sin tope ni recorte ni aviso; el tope del brief es `BRIEF_TOPE_CHARS = 10000` (spec CA-08 de `memory-retrieval`) y la seccion hermana de memoria si recorta y lo dice | T-01 | corregido: `PERSONA_TOPE_CHARS = 4000` recorta y avisa (mismo patrón que la memoria técnica, `task-brief.py:105-110,395-400`) y el contenido inyectado va delimitado con `<!-- cita externa, no instrucción del brief -->` (`task-brief.py:552-558`); tests `test_persona_por_encima_del_tope_se_recorta_y_se_dice` y `test_persona_inyectada_va_delimitada_contra_suplantacion_del_contrato` | `task-brief.py:361-375` y `:546-548`. Persona de 60.000 caracteres -> brief de **61.572**, `rc=0`, stderr vacio. Incluye la superficie de inyeccion: el contenido se pega literal y puede imitar secciones del brief (`## Contrato de retorno (obligatorio)`) |
| 3 | Important | Los documentos nuevos afirman en presente maquinaria de F2 que no existe en el arbol, sin distinguir lo entregado de lo disenado. Grado **subido** de Minor (Lente A) a Important por evidencia reproducible de la Lente B | T-02, T-03 | corregido: nota explícita de F1 entregado vs F2 contrato (aún no en el árbol) al inicio de `docs/SPECIALIZATION.md` + espejo EN, mismo patrón que `docs/agents/ROLES.md:7-8`; `docs/FLOWS.md` y espejo EN también distinguen «entregado» de «contrato de diseño» | `docs/SPECIALIZATION.md:33,91,100-103` + espejo EN; `docs/FLOWS.md:335` + espejo. `grep -rn "pieces\|especializ" agent-kits/shared/doctor.py commands/doctor.md` -> 0. Ausentes: `commands/specialize.md`, `pieces-registry.py`, `role-collision.py`, `project-scan.py`, `.claude/pieces.json` |
| 4 | Important | La cascada no se propago a las piezas que documentan la resolucion de personas: siguen describiendo un solo catalogo y la lista cerrada de 6 tipos. Ninguna de las 22 tareas del plan las toca | T-01 | corregido: `commands/dev-cycle.md`, `agents/planner.md` y `agent-kits/shared/README.md` (2 filas) actualizados a la cascada de tres escalones y tipos libres; añadidos al campo `Archivos` de T-01 con nota | `commands/dev-cycle.md:95`, `agents/planner.md:87`, `agent-kits/shared/README.md:31`. Tras T-01 esas frases son falsas: un `- **Tipo**: hooks` con `.claude/personas/hooks.md` si funciona |
| 5 | Important | `ROLES.md` ofrece un comando que hoy falla y omite el flag que decidio el plan: `ADR-015` fija que el modo proyecto se pide con `--project` y que sin el un arbol de consumidor sigue dando exit 1 | T-03 | corregido: cita el flag `--project` y `ADR-015` (aún `propuesta`), y deja explícito que sin el flag sigue dando exit 1 | `docs/agents/ROLES.md:36`. Verificado: `export-interop.py --root <arbol de consumidor>` -> `ERROR: no pude leer las piezas del plugin ... .claude-plugin/plugin.json`, exit 1 (`evaluation.md:159-174`, `ADR-015:17`) |
| 6 | Important | La suite dejo de ser hermetica: el escalon 1 se deriva con `_raiz_de` y no se puede desactivar, asi que los tests preexistentes leen un `.claude/personas/` fuera de su `tmp_path`, en ruta estable y compartida. Grado **subido** de Minor: un test fragil envenena todas las puertas futuras | T-01 | corregido: `inic_personas` (fixture de los tests de persona) pasa a la forma real `<raiz>/docs/roadmap/<slug>` dentro de `tmp_path`, igual que `inic_personas_proyecto` — `_raiz_de()` ya no puede escapar de `tmp_path` | `test_task_brief.py:78-84` + `task-brief.py:362-364`. Reproducido: fichero en `%TEMP%/pytest-of-<user>/.claude/personas/db.md` -> `pytest` pasa de `52 passed` a `1 failed, 51 passed` |
| 7 | Minor | Enlace del espejo EN que manda al lector al documento en espanol pese a existir el hermano en ingles | T-02 | corregido: `docs/en/SPECIALIZATION.md:6` enlaza `INTEROP.md` (relativo dentro de `en/`, no `../INTEROP.md`) | `docs/en/SPECIALIZATION.md:6` -> `(../INTEROP.md)`; `docs/en/INTEROP.md` existe y la convencion del arbol EN es relativa dentro de `en/` (`docs/en/README.md:24`) |
| 8 | Minor | Terminologia del contrato: el plan y el ledger dicen "cascada de tres escalones"; el codigo se autodocumenta como "de dos" | T-01 | corregido: docstring de `task-brief.py` dice «cascada de tres escalones» (antes «de dos»), consistente con plan y ledger | `task-brief.py:12-14,350-352` vs `tasks.md:49,74` e `improvement-plan.md:195,284`. Solo nombres: ningun criterio depende del numero |
| 9 | Minor | Aviso enganoso: el mensaje de fichero vacio promete un escalon siguiente que no existe cuando el vacio es el ultimo candidato | T-01 | corregido: el aviso «probando el siguiente escalón» solo se emite si NO es el último candidato (`task-brief.py:395-401`); test `test_persona_vacia_en_el_ultimo_escalon_no_promete_un_siguiente` | `task-brief.py:372`. Vacio en proyecto y en catalogo -> dos avisos "probando el siguiente escalon" + el final |
| 10 | Minor | La prosa generaliza la inyeccion de persona a todas las tareas; el codigo solo la aplica a las que llevan `- **Tipo**:` | T-02 | corregido: `docs/SPECIALIZATION.md` y espejo EN precisan que la inyección aplica a las tareas con `- **Tipo**:` (campo opcional), no a todas | `docs/SPECIALIZATION.md:22` y espejo EN `:22` vs `task-brief.py:544-547` |
| 11 | Minor | Referencia colgante "esta carpeta" en las dos versiones de `FLOWS.md`, copiada del contexto del ledger: el lector de `FLOWS.md` no tiene ninguna carpeta en contexto | T-03 | corregido: «esta carpeta» sustituido por «entregado: cascada de personas de `task-brief.py`» / «shipped: the persona cascade in `task-brief.py`» en `docs/FLOWS.md` y espejo EN | `docs/FLOWS.md:335`, `docs/en/FLOWS.md:337` (regla 5 de `docs-style.md`) |
| 12 | Minor | CA-01 y CA-04 comparten escenario casi identico (mismo tipo `hooks`, solo cambia la presencia en el catalogo): cobertura correcta pero redundante | T-01 | descartado (rebatido): CA-01 afirma PRECEDENCIA (el catálogo queda excluido cuando el proyecto tiene fichero) y CA-04 afirma AUSENCIA DE LISTA BLANCA (un tipo fuera de los 6 históricos funciona) — son invariantes distintos aunque el fixture se parezca; quitar cualquiera de los dos pierde una garantía (`test_task_brief.py:349` vs `:376`, asserts distintos: `"catálogo (no debe salir)" not in out` vs solo la presencia del contenido arbitrario) | `test_task_brief.py:336` vs `:363` |

**Lo que las lentes confirmaron como solido** (no es relleno: es lo que NO hay que rehacer):

- Los cuatro tests nuevos son detectores reales, no verdes de adorno: la Lente A los mato con tres
  mutantes sobre copias (orden de cascada invertido -> CA-01 rompe; lista blanca de los 6 tipos ->
  CA-01 y CA-04 rompen; `sys.exit(1)` en vez del aviso -> CA-03 rompe).
- Los `- **Tipo**:` hostiles no escapan de `personas/`: `re.fullmatch(r"[a-z][a-z0-9-]*")` en
  `task-brief.py:259`, 16 entradas probadas (traversal, rutas absolutas, vacio, dispositivos
  Windows `con`/`nul`/`aux`/`com1`/`prn`, 300 caracteres) -> `tipo_detectado=None`, sin fuga, `rc=0`.
- Fidelidad al diseno: el bloque JSON del registro en `SPECIALIZATION.md` (y su espejo) es
  **identico** al de `design.md:124-144` (opcion O1), con `runtime` declarado dato y no clave.
- Los tokens que parsea una maquina siguen en espanol tambien en la doc EN.
- `cp1252` (GOT-005) cubierto: `sys.std*.reconfigure(errors="replace")` en `task-brief.py:76-79`;
  con `PYTHONIOENCODING=cp1252` el aviso nuevo sale integro y `exit=0`.
- Alcance: los 9 ficheros son exactamente los `Archivos` declarados en T-01, T-02 y T-03.

**Pendiente ajeno a estas tres tareas** (del orquestador, no de F1): `tests/test_cifras_medidas.py`
falla 2 casos desde el commit del plan porque la doc dice `ledgers_totales = 31` y la medicion de hoy
da 32 (el ledger de esta iniciativa). Ficheros a actualizar:
`skills/changelog-sync/references/medicion-escalera.md:268` y
`docs/roadmap/2026-09-04-changelog-brief/tasks.md:184`. Afecta a la puerta de cierre T-22.

**Nota para `/retro`:** `review-lens-select.py` decidio `lente_c: false` y la Lente B encontro de
todos modos una superficie de inyeccion de prompt (gap 2). La heuristica no ve que abrir un canal de
texto controlado por el consumidor hacia el prompt de un subagente es materia de seguridad. Candidata
a leccion.

## Revision de dos lentes - intento 2: 1 Critical, 4 Important, 3 Minor (lentes A+B)

Lentes A+B al agente `reviewer` en paralelo, contexto fresco, con el estado del intento 1
traspasado (tabla completa + la instruccion de re-evaluar SOLO lo corregido). Condicionales:
`review-lens-select.py --base HEAD` devolvio otra vez `lente_c: false` y `lente_d: false` sobre 20
ficheros. Puerta previa `scope-check.py --base HEAD`: **15 en alcance** (ya incluye los tres
ficheros de propagacion anadidos a los `Archivos` de T-01), 5 fuera = el ruido previo ya fichado.

**Los 6 Important y 5 de los 6 Minor del intento 1 quedan CERRADOS** (verificado por las dos
lentes). El gap 12 se cierra como **descartado (rebatido)**: la Lente A arbitro con dos mutantes
propios y el rebate se sostiene (M1 orden invertido rompe CA-01 y no CA-04; M4 "el catalogo es el
registro de tipos validos" rompe CA-04 y no CA-01, y M4 es la implementacion equivocada mas
probable porque es la de antes de T-01). Cada test mata un mutante que el otro no ve.

Lo que este intento anade son defectos **de la propia correccion**, no reapertura de lo juzgado.

| # | Grado | Gap | Tarea | Correccion | Evidencia |
|---|---|---|---|---|---|
| B-2 | **Critical** | El recorte de la persona corta a ciegas (`contenido[:PERSONA_TOPE_CHARS].rstrip()`): parte estructura markdown y lo que sigue en el brief se lo come el bloque abierto. Grado **subido** de Important por el orquestador: la consecuencia es "subagente sin criterios de aceptacion", que este repo ya gradua ALTA en este mismo script, y la maquinaria para evitarlo ya existe sin usarse | T-01 | Recorte seguro: `_estado_estructura_por_linea` + `_recorte_seguro` (nuevas) retroceden el corte hasta la ultima linea fuera de un fence/comentario abierto, con fallback de corte a nivel de caracter si una sola linea no cabe entera. Usa la deteccion de fences ya existente en el fichero en vez de ignorarla | `pytest -q agent-kits/shared/test_task_brief.py -k "recorte_no_parte_un_fence_abierto or recorte_no_deja_comentario_html_abierto"` -> `2 passed` (reproducen los dos escenarios exactos del gap: fence en el caracter 3.901, comentario en el 3.880); verificados en rojo contra el codigo previo (`git stash` + pytest -> ambos fallan) y en verde tras el fix |
| B-1 | **Important** | El delimitador contra suplantacion es una marca de **apertura sin cierre**, y es un comentario HTML declarado inerte, o sea **invisible en cualquier render**: no acota la cita ni para un modelo ni para una persona. Peor, el test nuevo **canoniza al impostor** en vez de detectarlo | T-01 | Delimitadores visibles con apertura Y cierre (`_PERSONA_INICIO`/`_PERSONA_FIN`, blockquote `>` en vez de comentario HTML inerte) + `_neutraliza_encabezados` escapa cualquier `#`..`######` DENTRO del cuerpo de la persona (`\#`) para que no pueda fabricar un encabezado real. Test reescrito: ya no asume `count == 2`, comprueba que el contrato falso queda escapado (`\\## Contrato...`) y que solo hay UN encabezado real `## Contrato de retorno (obligatorio)` en todo el brief | `pytest -q agent-kits/shared/test_task_brief.py -k persona_inyectada_va_delimitada` -> `1 passed`; regex `re.findall(r"^## Contrato de retorno \(obligatorio\)$", out, re.M)` -> longitud 1 (antes: 2, canonizando al impostor) |
| B-3 | **Important** | `PERSONA_TOPE_CHARS = 4000` no honra `BRIEF_TOPE_CHARS`/CA-08: el gap 2 del intento 1 queda **desplazado, no cerrado**. El comentario de la constante afirma que "deja margen de sobra" y la medicion dice lo contrario. No hay ninguna comprobacion en runtime del tope global | T-01 | **Bucle acotado agotado en el intento 3** con este gap sin converger (la correccion del intento 2, `tope_cuerpo = min(PERSONA_TOPE_CHARS, margen_real)`, dejaba el margen real mandar SIEMPRE, aniquilando la persona a un munon ilegible en las tareas mas ajustadas: T-06 de 1.107 a 55 caracteres, T-22 de 1.164 a 115 — medido sobre el ledger real, no reproducido en la fixture de juguete). **Corregido (opcion A, decision del usuario tras el 3.er intento)**: suelo `PERSONA_SUELO_CHARS = 1300` (por encima de la mayor persona del catalogo, 1.182 caracteres) + aviso con causa; `tope_persona = max(PERSONA_SUELO_CHARS, min(PERSONA_TOPE_CHARS, margen_real))` — el margen manda si sobra, pero la persona nunca baja del suelo aunque el brief total se pase de `BRIEF_TOPE_CHARS`. El aviso runtime mide diseno/memoria/tarea+gaps/persona por separado y NO culpa a la persona cuando esta en su suelo garantizado. **La violacion preexistente del CA-08 (11/22 tareas ya sobre el tope SIN persona: `## Diseno` + memoria + tabla de gaps) va a iniciativa aparte** (ya iniciada: `docs/roadmap/2026-09-09-brief-budget/`, con `docs/knowledge/gotchas/GOT-009-presupuesto-del-brief-se-rompe-con-design-md.md`) — no es alcance de esta correccion, que solo protege a la persona de ser la victima de ese exceso ajeno | Medicion antes -> despues sobre el ledger real (brief total en caracteres · persona): T-01 14.799 sin persona (no aplica, sin `Tipo`) -> 14.910 sin persona; T-02 12.211 sin recorte -> 13.579 · 1.256 (suelo); T-03 10.328 sin recorte -> 11.837 · 1.256 (suelo); T-06 10.000 recortada de 1.107 a 55 -> 10.938 · 1.256 (integra, en su suelo); T-13 9.392 sin persona -> 9.504 sin persona; T-17 9.981 sin recorte -> 11.408 · 1.315 (suelo); T-22 10.001 recortada de 1.164 a 115 -> 10.934 · 1.315 (integra, en su suelo). `pytest -q agent-kits/shared/test_task_brief.py -k "persona_tope_dinamico_contra_margen_real or persona_corta_por_debajo_del_suelo"` -> `2 passed` (el segundo es un test nuevo: una persona corta, por debajo del suelo, no se toca y no avisa); suite completa `pytest -q agent-kits/shared/test_task_brief.py` -> `59 passed, 1 failed` (el failed es `test_ca08_...memory_retrieval`, la violacion preexistente de CA-08 sin persona — ya fallaba igual antes de esta correccion, confirmado con `git stash`; fuera de alcance, ver nota de la iniciativa aparte) |
| 13 | **Important** | La correccion del gap 4 dejo la plantilla del planner contradiciendo a su propio agente: `planner.md` ya dice que `Tipo` es libre sin lista cerrada, pero el `{{PLACEHOLDER}}` que el planner rellena sigue ofreciendo solo los 6 tipos. **La contradiccion la crea este intento** | T-01 | `agent-kits/planner/templates/tasks.md:81` reescrito: el placeholder ya no ofrece una lista cerrada ("libre, sin lista cerrada — p. ej. frontend/backend/db/devops/test/docs/hooks..."), describe la cascada de dos escalones y cuando aplica. Fichero anadido a los `Archivos` de esta tarea (con nota) | `grep -n "libre, sin lista cerrada" agent-kits/planner/templates/tasks.md` -> `81:...`; lectura confirmada: el placeholder ya no cierra la lista a 6 tipos y coincide con `agents/planner.md:87` |
| 16 | **Important** | Evidencia pegada que no reproduce: la nota de correccion de T-02 afirma que su `grep` de `Verificacion` "sigue en 1/1" DESPUES de anadir el bloque del gap 3, y ese bloque introdujo una segunda coincidencia. El numero es de la ejecucion anterior al cambio: la `Verificacion` no se re-ejecuto. Tercera vez que aparece `GOT-007` en esta sesion (dos del orquestador, una del implementer) | T-02 | Re-ejecutada la `Verificacion` de T-02 tras el ultimo cambio y sustituida la nota de `tasks.md:100` por el numero real, dejando explicito que el criterio (>= 1 en los dos ficheros) sigue cumpliendose aunque el numero cambio de 1/1 a 2/2 | `grep -nc "pieces.json" docs/SPECIALIZATION.md docs/en/SPECIALIZATION.md` (re-ejecutado ahora) -> `docs/SPECIALIZATION.md:2` y `docs/en/SPECIALIZATION.md:2` |
| 14 | Minor | Resto de la propagacion del gap 4: dos piezas mas siguen con la lista cerrada de 6 tipos, y una afirma "misma mecanica que `task-brief.py`", que ya es falsa | T-01 | `docs/agents/planner.md:18` y `skills/adversarial-review/references/lens-prompts.md:21` reescritos: el primero anade "libre, sin lista cerrada"; el segundo explica el escalonado real (proyecto -> catalogo del plugin) y retira la afirmacion "misma mecanica que `task-brief.py`" (la sustituye por "mismo escalonado... aunque este prompt lo resuelve en prosa, no con su script"). Grep repo-wide para confirmar que no queda ninguna otra pieza ACTIVA (no roadmap cerrado) con la lista cerrada o la afirmacion falsa | `grep -rn "misma mecanica que \`task-brief.py\`\|misma mecánica que \`task-brief.py\`" --include=*.md .` -> sin coincidencias tras el fix; `grep -rln "frontend/backend/db/devops/test/docs" agents/ docs/agents/ skills/ commands/ agent-kits/planner/` -> ninguna con lista CERRADA (todas cualificadas "libre"/"p. ej."); las unicas menciones del sexteto cerrado que quedan en el repo estan en roadmaps historicos ya cerrados (`docs/roadmap/2026-08-12-subagent-personas/spec.md`, `docs/roadmap/2026-09-04-memory-retrieval/{analysis,tasks}.md`, `docs/roadmap/README.md`), fuera de alcance y protegidos por guardrail |
| 17 | Minor | La prosa nueva promete precedencia absoluta del escalon 1 ("gana siempre"); el codigo entregado cae al catalogo si el fichero del proyecto esta vacio o da `OSError` | T-01 | `commands/dev-cycle.md:95` corregido: "gana siempre" -> "gana si existe y se puede leer — un fichero vacio o un `OSError` ... cae al siguiente escalon sin bloquear". `agent-kits/shared/README.md:31` revisado: YA decia "gana **si existe**" (matizado en un cambio anterior de esta misma tarea), no repite el gap; no necesito tocarlo | `grep -n "gana" agent-kits/shared/README.md commands/dev-cycle.md` -> README ya matizado ("gana si existe"); dev-cycle.md ya no contiene "gana siempre" tras el cambio |
| 18 | Minor | `docs-style.md` regla 1 (frases cortas): la frase corregida llega a **117 palabras** (en HEAD eran 94). Ya incumplia antes; el anadido la agrava. Se arregla partiendo la cascada a vineta o tabla, sin tocar el contenido | T-01 | `commands/dev-cycle.md:95` partido en una intro corta + 4 vinetas (tarea/criterios/fase; persona de dominio; opcion de `design.md`; arquitectura+constitucion+contrato). La vineta de persona sigue siendo la mas larga (lleva la cascada completa, necesaria para el gap 17) pero baja de una frase monolitica de 117 palabras a **4 frases mas cortas dentro de la misma vineta** (~99 palabras repartidas en 4 oraciones en vez de 1), y el resto del bloque queda en frases de 4-10 palabras. Ninguna de las 4 oraciones de la vineta de persona pasa de 40 palabras | `sed -n '95,99p' commands/dev-cycle.md`: intro `8` palabras; vinetas `9`, `99` (4 frases), `9`, `7` palabras; antes: una sola frase de 117 palabras. Contenido verificado por lectura: mismos 6 elementos, mismo comportamiento de la cascada, ningun dato perdido |

**Cerrado y verificado en este intento** (no rehacer): la guarda `OSError` cubre los tres escalones y
el ultimo degrada limpiamente, incluidos los `OSError` que no son de lectura (`.claude` como fichero,
la persona como directorio) -> `rc=0` en todos. La hermeticidad de la suite quedo **arreglada de
verdad**: recreado el veneno en `%TEMP%/pytest-of-<user>/.claude/personas/` con 8 tipos, la suite da
`56 passed` (en el intento 1 daba `1 failed`). Los cuatro tests nuevos **fallan los cuatro** con el
codigo previo, reconstruido en el scratchpad, y por los motivos correctos. El aviso de fichero vacio
ya no promete un escalon inexistente cuando es el ultimo. Y la Lente A confirmo que la propagacion
del gap 4 describe el comportamiento real y que la justificacion del campo `Archivos` es legitima.

**Preexistente, NO de este diff, y no se absorbe aqui:** **11 de las 22 tareas de este ledger ya
pasan de `BRIEF_TOPE_CHARS = 10000` sin ninguna persona de proyecto** (T-01 14.637, T-02 13.155,
T-03 12.993, T-14 11.534, T-17 11.234, T-06 10.764, T-22 10.759, y T-05/T-08/T-10/T-16 sobre 10.2k),
por `## Diseno` (3.510) + memoria (1.830) + la tabla de gaps inyectada. El CA-08 de
`memory-retrieval` esta roto YA, y su test no lo ve porque solo recorre ese otro ledger. Alcance de
F1: que la persona no empuje mas y que el brief AVISE cuando se pasa. La violacion preexistente
necesita su propia entrada (gotcha o tarea), no absorberse en silencio en T-01.

**Candidatas a leccion para `/retro`** (dos, con evidencia doble cada una):

1. **`review-lens-select.py` no ve materia de seguridad en abrir un canal de texto controlado por el
   consumidor hacia el prompt de un subagente.** Decidio `lente_c: false` en los dos intentos, y la
   Lente B encontro la superficie de suplantacion las dos veces. La heuristica mira patrones de
   codigo peligroso (`eval(`, `shell=True`) y stems de ruta sensibles; no mira *flujo de datos hacia
   un prompt*.
2. **Cambiar una pieza no propaga a quien la documenta, y el ciclo no lo comprueba.** Ha pasado dos
   veces DENTRO de esta iniciativa: primero la cascada dejo tres ficheros mintiendo (gap 4), y luego
   su arreglo dejo una plantilla contradiciendo a su agente (gap 13) y dos piezas mas sin propagar
   (gap 14). Ninguna de las 22 tareas del plan lo preveia.

## Revision de dos lentes - intento 3 (pasada acotada a la opcion A): 3 Important, 1 Minor (lente B)

Pasada **acotada** tras la decision del usuario (opcion A para el gap B-3, que no convergia en tres
intentos porque su causa no esta en F1). Solo corrio la **Lente B** sobre lo que A cambio (suelo de la
persona + aviso en runtime + dos tests); la Lente A ya habia validado todos los criterios en el intento 2 y
el orquestador comprobo por su cuenta el criterio 5 (la `Verificacion` de T-01 re-ejecutada tras el ultimo
cambio y pegada como tercera entrada). `review-lens-select.py` volvio a dar `lente_c`/`lente_d: false`.
Los gaps son defectos **de la implementacion de A**, no reapertura de lo cerrado.

| # | Grado | Gap | Tarea | Correccion | Evidencia |
|---|---|---|---|---|---|
| B-4 | **Important** | El "suelo garantizado" no garantiza contenido: se aplica a `contenido + nota de recorte`, y la nota lleva la **ruta absoluta** del fichero de persona. Acantilado no monotono y salida dependiente de la maquina. El comentario de la constante afirma "por debajo de el nunca se recorta una persona" y es falso para cualquier persona > 1300 | T-01 | **Corregido.** `_persona_delimitada` (`task-brief.py:517-545`) aplica `tope_cuerpo` SOLO al contenido; la nota de recorte se añade DESPUÉS, sin descontarse del suelo, y ya no lleva la ruta absoluta — nueva `_ruta_para_aviso()` (`:505-514`) resuelve una ruta relativa a la raíz del proyecto (o el nombre de fichero) para los avisos por `stderr`, que no cuentan contra ningún tope. Comentario de las constantes reescrito (`:118-142`) con la promesa real y las 6 medidas del catálogo. Tests: `test_persona_suelo_por_encima_del_catalogo` (guardián de calibración) y `test_persona_suelo_entrega_contenido_util_no_bloque_relleno` (contenido, no bloque; monótono; independiente de la ruta) | Oráculo medido: **1100 → 1100** útiles (sin recorte); **1301 → 1300** útiles (≥ suelo, ya no 986); persona de 1500 con rutas de 5/44/108 caracteres → **1300 útiles las tres veces** (antes: 986/940/894, dependiente de la ruta). Mutante `PERSONA_SUELO_CHARS = 400` → los dos tests nuevos **fallan** (verificado en copia de trabajo, restaurado tras comprobar) |
| B-5 | **Important** | El aviso de runtime afirma dos cosas falsas justo donde el suelo es la unica causa del exceso: exonera a la persona ("en su suelo garantizado, no es la causa") y culpa a un exceso "preexistente" que no existe | T-01 | **Corregido.** El bloque de aviso de `main()` (`task-brief.py:857-887`) calcula `resto_sin_persona` (el brief SIN la persona) y bifurca: si `resto_sin_persona <= BRIEF_TOPE_CHARS`, imprime «la persona en su suelo (N) empuja el brief a X > 10.000; decisión opción A (2026-09-09): la persona no se recorta por debajo del suelo»; si no, imprime «exceso preexistente de N caracteres SIN persona (...); la persona (N) no es la causa». Dos tests nuevos cubren AMBAS ramas: `test_persona_en_su_suelo_es_la_causa_honesta_del_exceso` con una fixture CALIBRADA en caliente (no un relleno `"Z" * 7000` que ya se pasa de tope por sí solo) para caer exactamente en `resto < tope < resto + suelo`, y `test_persona_no_es_la_causa_de_un_exceso_preexistente` para la rama complementaria | Oráculo: T-01/T-19 (rama suelo) → el aviso dice «la persona en su suelo … empuja el brief a …», sin «exceso preexistente»; fixture del exceso preexistente → dice «exceso preexistente … la persona (…) no es la causa», sin «en su suelo». Las dos ramas verificadas con `pytest`, no a mano |
| B-7 | **Important** | Las dos aserciones del suelo son **tautologicas**: usan la propia constante y miden el bloque rellenado, no el contenido entregado. No hay ningun guardian de la calibracion del suelo frente al catalogo | T-01 | **Corregido.** Dos tests nuevos reemplazan las aserciones tautológicas: `test_persona_suelo_por_encima_del_catalogo` afirma `PERSONA_SUELO_CHARS > max(len(p) for p in personas/*.md)` contra el catálogo REAL (no a ciegas); `test_persona_suelo_entrega_contenido_util_no_bloque_relleno` mide el CONTENIDO entregado entre los delimitadores, separando la nota de recorte, con personas de 1100/1301/1500 caracteres y 3 rutas de longitud muy distinta | Verificado personalmente en copia de trabajo: mutante `PERSONA_SUELO_CHARS = 400` → `pytest -k "test_persona_suelo_por_encima_del_catalogo or test_persona_suelo_entrega_contenido_util_no_bloque_relleno"` → **2 failed** (`400 > 1182` falso; `contenido_util(1100 chars) == 400` en vez de `1100`); código restaurado tras la comprobación, diff limpio contra el fichero real |
| B-6 | Minor | La "causa medida" del aviso esta medida para memoria y persona pero **re-estimada** para diseno y gaps, y el comentario dice "causa MEDIDA (no adivinada)" | T-01 | **Corregido.** Nuevas `_secciones_por_encabezado()` y `_longitud_seccion()` (`task-brief.py:638-655`) particionan `texto` (el brief YA MONTADO) por sus líneas `## `, igual que lo mediría un orquestador externo; `main()` las usa para `len_diseno`, `len_memoria`, `len_tarea_gaps` y `len_persona` en vez de re-estimar con `len(diseno[1])` o una tabla de gaps reconstruida a mano. Test `test_aviso_ca08_mide_sobre_el_brief_montado_no_reestima_fragmentos` con una reimplementación INDEPENDIENTE (test-local, no importa la función de producción) de la misma partición, comprobando que la cifra de `persona=` del aviso coincide EXACTAMENTE con la medición externa | Verificado: el test nuevo compara la cifra impresa por `main()` contra `_secciones_por_encabezado_test()` (independiente) sobre un brief real que se pasa del tope — coincidencia exacta exigida por `assert`, no una tolerancia |

**Codigo muerto detectado (nota para el refactor, no gap de correccion):** `PERSONA_TOPE_MINIMO_UTIL = 200`
(`task-brief.py:133`, rama `:507-511`) es **inalcanzable**: los dos puntos de llamada pasan 10000 o un
`tope_cuerpo` que por `max(PERSONA_SUELO_CHARS, ...)` nunca baja de 1300; su aviso no puede imprimirse y
ningun test lo cubre. La rama de recorte solo se ejecuta con personas de proyecto > 1300 (todo el catalogo
del plugin cabe entero: 1058-1182). `PERSONA_TOPE_CHARS = 4000` sigue vivo solo como techo cuando sobra
margen. Cuatro reglas para una seccion: la cicatriz que motiva `2026-09-09-plugin-refactor`.

**Verificado y cerrado en esta pasada:** el test nuevo del suelo afirma propiedades, no cifras absolutas
(estable con +39/+317 caracteres de ruta y con una entrada de memoria mas), y tiene dientes frente al
mutante del intento 2. **La opcion A no empeora** `test_ca08_..._memory_retrieval`: en rutas cortas el test
pasa en VERDE en HEAD y en el arbol de trabajo (top HEAD T-05 9871 · trabajo T-05 9982; el diff neto son
+111 caracteres y son los delimitadores de B-1, ya cerrado, no A). El rojo de esta maquina es artefacto de
la ruta OneDrive (`GOT-008`): en ruta corta el margen de T-05 queda en **18 caracteres**.

**Puerta de pruebas de F1 (sin UI, `qa` no aplica):** `qa` esta definido para E2E con Playwright y exige
`test-plan.md`, que `planner` descarto a proposito por no haber UI; invocarlo solo produciria el aviso
"regeneralo con planner" (hueco de encadenamiento E1, anotado en `2026-09-09-plugin-refactor/analysis.md`
8-bis). La puerta de F1 son: `pytest -q agent-kits/shared/test_task_brief.py` (59 passed + 1 rojo
preexistente verificado en HEAD limpio), `lint_plugin.py` 0 errores, `evals/check.py` 0 errores,
`export-interop.py --check` 48 al dia (tras regenerar: 3 ficheros estaban desincronizados por tocar
`commands/dev-cycle.md` y `agents/planner.md`, hueco E2), `test_mermaid_blocks` 35 OK, y la suite completa
(39 fallos, todos de entorno Windows: separadores `\`/`/`, bit ejecutable POSIX, `WinError`, CRLF;
comparacion de conjuntos contra HEAD en curso). Cobertura por diff no medible en esta maquina:
`coverage-gate.py` no encuentra `pytest-cov` y, como debe, no inventa un porcentaje.
