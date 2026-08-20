---
tasks: knowledge-split
descripcion: Partir docs/knowledge/ a un fichero por entrada (gotchas/ y lessons/) con lectura selectiva vía índice, y registrar la decisión como ADR-006.
estado: en-progreso       # borrador | en-progreso | completado | cancelado
creado: 2026-08-20
actualizado: 2026-08-20
via: rapida               # vía rápida de /dev-cycle: sin spec/evaluación/plan; conserva revisión de dos lentes + suites
generacion:
  fuente: estimado        # usage-meter no disponible en este entorno (sandbox cloud)
---

# Checklist de Tareas — knowledge-split (vía rápida)

| | |
|---|---|
| **Estado** | en-progreso |
| **Fecha** | 2026-08-20 |
| **Plan** | n/a — **vía rápida** (sin spec/evaluación/plan; ledger ligero + revisión de dos lentes + verificación) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del cambio. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador externo— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

> **Decisión del usuario (2026-08-20).** Partir `docs/knowledge/gotchas.md` y `LESSONS.md` a **un fichero por entrada** (`gotchas/<slug>.md`, `lessons/<agente>-<slug>.md`) dentro de `docs/knowledge/`, por crecimiento previsible, lectura selectiva (token-diet), colisiones de escritura en paralelo (dos entradas simultáneas en un fichero compartido) y una página por entrada en Confluence. El `README.md` pasa a ser el índice de ENTRADA (una línea por entrada, enlazando al fichero individual) y `agent-kits/shared/knowledge-check.md` a lectura SELECTIVA (índice → abrir solo lo relevante). `adr/` **no cambia** (ya era un fichero por decisión). Se registra como **ADR-006**, `estado: aceptada (validada: usuario, 2026-08-20)`.

> **Nota de formato (declarada):** este ledger se recibió como una lista compacta de 4 bullets; se ha reestructurado al formato canónico (`## Fase` / `### T-XX` con bloque de criterios) sin alterar ni una palabra de su contenido, para que `ledger-lint.py` lo valide mecánicamente como el resto de ledgers ligeros del repo (mismo patrón que `2026-08-12-workflow-polish/tasks.md`).

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase única — migración y cableado | 5 | 5 | 100% | 3,7 / 3,7h | 0,15 / 0,15h | 0,05 / 0,05h | 56k / 70k |
| **TOTAL** | **5** | **5** | **100%** | **3,7 / 3,7h** | **0,15 / 0,15h** | **0,05 / 0,05h** | **56k / 70k** |

---

## Fase única — migración y cableado

**Estado**: completado · **Estimado**: 3,7h · **Real**: 3,7h (estimado) · **Coste est.**: ≈175 € · **Tokens est.**: 70k

### T-01 — Migrar las entradas a fichero por entrada

- **Descripción**: Crear `docs/knowledge/gotchas/<slug>.md` (una por cada una de las 3 gotchas actuales) y `docs/knowledge/lessons/<agente>-<slug>.md` (una por cada una de las 9 lecciones), con frontmatter por entrada (`tipo`, `area`, `estado` con su traza LITERAL actual, `fuente`). Los ficheros antiguos `gotchas.md` y `LESSONS.md` quedan como STUB de redirección de ≤5 líneas (motivo: la escritura remota no puede borrar en el disco del usuario; en proyectos consumidores nuevos los stubs no existen — las carpetas se crean directas).
- **Estado**: completado
- **Tiempo humano**: est. 0,8h · real 0,8h (estimado)
- **Tiempo IA (ejec.)**: est. 0,04h · real 0,04h (estimado)
- **Supervisión**: est. 0,01h · real 0,01h (estimado)
- **Archivos**: `docs/knowledge/gotchas/*.md` (nuevo, 3), `docs/knowledge/lessons/*.md` (nuevo, 9), `docs/knowledge/gotchas.md` (stub), `docs/knowledge/LESSONS.md` (stub)

**Criterios de aceptación**
- [x] Contenido migrado sin pérdida ni retoque (mismo texto, misma traza de validación). **Enmendado en revisión:** sufijo `— N/3` de desambiguación añadido al heading compartido de las 3 lecciones del bloque `evaluator-separa-*`/`evaluator-presupuesta-*`/`evaluator-revision-*` (necesario para diferenciar 3 ficheros que nacían del mismo heading al dividirse); cuerpo y traza siguen literales, sin retocar.
- [x] Los ficheros antiguos `gotchas.md` y `LESSONS.md` quedan como stub de redirección de ≤5 líneas.
- [x] `grep` de cada traza `validada:` devuelve exactamente las mismas que antes de migrar (mismo conteo, mismo texto). Verificado: 3 trazas gotcha (idénticas por fichero) y las 7 líneas-traza de LESSONS.md preservadas en las 9 lecciones (el bloque compartido de 3 lecciones repite su traza en cada una de las 3, íntegra, para que cada fichero quede autocontenido).

### T-02 — Índice como puerta de entrada + lectura selectiva

- **Descripción**: `docs/knowledge/README.md` sigue siendo una línea por entrada, ahora enlazando al fichero individual, con cabecera que lo declara ÍNDICE DE ENTRADA obligado. `agent-kits/shared/knowledge-check.md` pasa a lectura SELECTIVA: leer el índice primero y abrir solo las entradas del área/agente relevante (progressive disclosure); conserva la distinción propuesta/aceptada y la degradación sin bloquear.
- **Estado**: completado
- **Tiempo humano**: est. 0,6h · real 0,6h (estimado)
- **Tiempo IA (ejec.)**: est. 0,03h · real 0,03h (estimado)
- **Supervisión**: est. 0,01h · real 0,01h (estimado)
- **Dependencias**: T-01
- **Archivos**: `docs/knowledge/README.md`, `agent-kits/shared/knowledge-check.md`

**Criterios de aceptación**
- [x] `knowledge-check.md` no ordena leer ficheros completos de área — solo la entrada relevante tras consultar el índice.
- [x] Los 5 agentes lectores siguen funcionando con sus subconjuntos (evaluator→`lessons/evaluator-*`, planner→`adr/`+`lessons/`, implementer→`adr/`+`gotchas/`, qa→`gotchas/`, documenter→todo).

### T-03 — Rutas en escritores, lectores y doc

- **Descripción**: `agent-kits/shared/knowledge-write.md` (tabla "Dónde escribe": nuevas rutas por entrada; la colisión de FICHERO desaparece también para gotchas/lessons —como en `adr/`— y la nota de colisión de `id:` se mantiene solo para ADR), los 3 escritores (`commands/retro.md` 4-bis, `skills/debug-root-cause/SKILL.md` F4, `agents/qa.md`), los 5 lectores si citan rutas literales, `docs/CONVENTIONS.md` regla 10 + espejo EN, `docs/INSTALL.md` + EN si citan la estructura, `CHANGELOG.md` `[Unreleased]` + `CHANGELOG.es.md` `[Sin publicar]`.
- **Estado**: completado
- **Tiempo humano**: est. 1,0h · real 1,0h (estimado)
- **Tiempo IA (ejec.)**: est. 0,04h · real 0,04h (estimado)
- **Supervisión**: est. 0,01h · real 0,01h (estimado)
- **Dependencias**: T-01, T-02
- **Archivos**: `agent-kits/shared/knowledge-write.md`, `commands/retro.md`, `skills/debug-root-cause/SKILL.md`, `skills/confluence-publish/SKILL.md`, `agents/qa.md`, `agents/evaluator.md`, `agents/planner.md`, `agents/implementer.md`, `agents/documenter.md`, `docs/FLOWS.md` (+EN), `docs/CONVENTIONS.md` (+EN), `docs/INSTALL.md` (+EN), `CHANGELOG.md`, `CHANGELOG.es.md`

**Criterios de aceptación**
- [x] `grep -rn "knowledge/gotchas\.md\|knowledge/LESSONS\.md"` no devuelve referencias vivas fuera de los stubs y de ledgers/retros históricos. Verificado: solo quedan CHANGELOG (entradas históricas de `knowledge-capture` + la entrada nueva de esta iniciativa), la mención descriptiva de `docs/CONVENTIONS.md`/EN sobre la migración histórica ("Prueba del mecanismo"), los roadmaps cerrados de `knowledge-capture`/`confluence-policy`, y este mismo ledger describiendo la propia migración.
- [x] Regla bilingüe respetada: espejo EN en el mismo commit para cada doc clave tocada (`docs/en/CONVENTIONS.md`, `docs/en/FLOWS.md`, `docs/en/INSTALL.md`, `CHANGELOG.md`).

### T-04 — ADR-006 + espejo verificado

- **Descripción**: `docs/knowledge/adr/ADR-006-<slug>.md`: decisión "un fichero por entrada en `gotchas/` y `lessons/`", contexto (crecimiento, lectura selectiva, colisiones, páginas Confluence), alternativas descartadas (fichero único con disparador), `estado: aceptada (validada: usuario, 2026-08-20)`; fila en el índice. Test del espejo: `tests/test_confluence_scope.py` — la fixture de `docs/knowledge/` cubre las subcarpetas nuevas (una entrada bajo `gotchas/` en alcance).
- **Estado**: completado
- **Tiempo humano**: est. 0,6h · real 0,6h (estimado)
- **Tiempo IA (ejec.)**: est. 0,01h · real 0,01h (estimado)
- **Supervisión**: est. 0,01h · real 0,01h (estimado)
- **Dependencias**: T-01, T-02, T-03
- **Archivos**: `docs/knowledge/adr/ADR-006-un-fichero-por-entrada-gotchas-y-lecciones.md` (nuevo), `docs/knowledge/README.md`, `tests/fixtures/confluence-scope/docs/knowledge/gotchas/ejemplo.md` (nuevo), `tests/test_confluence_scope.py`

**Criterios de aceptación**
- [x] Suite `test_confluence_scope` en verde con el caso nuevo (fixture bajo `gotchas/` en alcance). Salida: `test_confluence_scope: 25/25 OK` (incluye la extensión de `test_status_categories_and_scope` y el set actualizado de `test_stage_creates_exact_scope_and_marker` con `knowledge/gotchas/ejemplo.md`).
- [x] `lint_plugin` 0 errores. Salida: `lint_plugin: 8 agentes · 0 errores · 3 avisos`.
- [x] Las 9 suites verdes. Salida: coverage-check OK, dashboard OK (1 aviso esperado), ledger_lint 10/10, lint_plugin 8/8, mermaid_blocks 26 OK, qa_gate 13/13, readme_badges 6 OK, worklog 13/13, confluence_scope 25/25.
- [x] `ledger-lint` 0 sobre este fichero. Salida: `ledger-lint: 0 incoherencias · 1 avisos` (aviso legacy de nombre de tabla, no bloqueante, mismo patrón que otros ledgers vía rápida).

### T-05 — IDs con nomenclatura ADR para gotchas y lecciones (extensión `knowledge-ids`)

- **Descripción**: Extensión decidida por el usuario tras cerrar T-01..T-04: renombrar (`git mv`) los 12 ficheros de `docs/knowledge/gotchas/`/`lessons/` a `GOT-NNN-<slug>.md`/`LES-NNN-<agente>-<slug>.md` (numeración cronológica: backfill de `knowledge-capture` primero, luego por orden del índice), con `id: GOT-NNN`/`id: LES-NNN` en el frontmatter (contenido intacto). Actualiza el índice `README.md` (enlaces + columna ID), `knowledge-write.md` (regla de nombrado de las 3 familias; colisión de `id:` pasa a aplicar a las 3), los globs de lectura selectiva de `knowledge-check.md` y los agentes/escritores que citaban un patrón de ruta literal, `docs/CONVENTIONS.md`+EN y `docs/FLOWS.md`+EN, la enmienda a `ADR-006`, y el punto en `CHANGELOG.md` `[1.14.0]` / `CHANGELOG.es.md` `[1.14.0]` (no en `Unreleased`: sale en la release ya preparada, sin pushear).
- **Estado**: completado
- **Tiempo humano**: est. 0,7h · real 0,7h (estimado)
- **Tiempo IA (ejec.)**: est. 0,03h · real 0,03h (estimado)
- **Supervisión**: est. 0,01h · real 0,01h (estimado)
- **Dependencias**: T-01, T-02, T-03, T-04
- **Archivos**: `docs/knowledge/gotchas/GOT-*.md` (renombrados, 3), `docs/knowledge/lessons/LES-*.md` (renombrados, 9), `docs/knowledge/README.md`, `agent-kits/shared/knowledge-write.md`, `agent-kits/shared/knowledge-check.md`, `agents/evaluator.md`, `agents/qa.md`, `commands/retro.md`, `skills/debug-root-cause/SKILL.md`, `docs/CONVENTIONS.md` (+EN), `docs/FLOWS.md` (+EN), `docs/knowledge/adr/ADR-006-*.md`, `CHANGELOG.md`, `CHANGELOG.es.md`

**Criterios de aceptación**
- [x] `git log --stat` muestra los 12 ficheros como RENAME (`git mv`, no copia+alta).
- [x] `grep` de los 12 nombres antiguos sin referencias vivas fuera de históricos/stubs (los stubs `gotchas.md`/`LESSONS.md` enlazan a las carpetas, no a ficheros con nombre antiguo — no citan `<slug>.md` viejo). **Corregido en revisión (intento 2):** el criterio no cubría un glob muerto derivado (`lessons/evaluator-*` en `docs/CONVENTIONS.md`/EN, que matcheaba 0 ficheros tras el rename) ni dos menciones de "solo el ADR"/"colisión de ID de ADR" que habían quedado desactualizadas frente a `knowledge-write.md` y la enmienda de `ADR-006`; corregidas ambas (CONVENTIONS ES+EN, `README.md`).
- [x] Los 12 ficheros llevan `id: GOT-NNN`/`id: LES-NNN` en el frontmatter.
- [x] `lint_plugin` 0 errores; las 9 suites verdes; `ledger-lint` 0 sobre este fichero.

---

## Notas de implementación

Iniciativa fast-track con 5 tareas completadas en dos pases (T-01→T-04 el mismo día; T-05 como
extensión decidida por el usuario tras la revisión de dos lentes, trabajada en
`feature/knowledge-ids` desde `master` — que ya incluye T-01→T-04 mergeadas y la release v1.14.0
preparada sin pushear). Registro cualitativo completo en `docs/knowledge/adr/ADR-006-*.md` (D2 de
`knowledge-capture`: esta sección ya no es el cajón de sastre).
