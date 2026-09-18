---
generacion: {fuente: estimado, tokens_reales: {entrada: 0, salida: 0, cache_creacion: 0, cache_lectura: 0}, eur: null, horas_ia: 0.0, duracion: 0m, ratio_usado: 0}
verificacion: obligatoria
---

# Checklist de Tareas - Servicios de conocimiento locales

| **Estado** | en-progreso |
|---|---|
| **Plan** | [improvement-plan.md](improvement-plan.md) |
| **Diseno** | [design.md](design.md), O1 |

> **Ledger canonico de progreso.** Esta es la fuente unica de avance; los servicios externos son espejo.
>
> **Enmienda 2026-09-17** (`ADR-018`): backends declarados + contrato de adaptador + esquema versionado + registro de capacidades + cola compartida. Cambian T-01, T-07, T-08, T-09; nace T-13. Las cifras anteriores (48h · 12 tareas) quedan en el historial de git.
>
> **Enmienda 2026-09-18** (validacion en vivo contra `dockers/knowledge-graphs`, CA-16/CA-17): Kwipu no ingiere, indexa una vista; el export va a `generated_knowledge` y el reindexado es del stack (`verify` lo detecta, no lo ejecuta); frontmatter alineado con el Knowledge Gate. Precisa T-08 y T-09 sin cambiar horas.

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervision (real/est) | Tokens (real/est) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Fase 1 - Contrato y validacion | 3 | 3 | 100% | 0 / 13h | 1.10 / 3.9h | 0 / 1.0h | ~57k / 200k |
| Fase 2 - Curacion y workflow | 0 | 3 | 0% | 0 / 14h | 0 / 4.2h | 0 / 1.1h | 0 / 210k |
| Fase 3 - Backends y Kwipu | 1 | 4 | 25% | 0 / 19h | 0.40 / 5.7h | 0 / 1.4h | ~16k / 275k |
| Fase 4 - Regresion y cierre | 0 | 3 | 0% | 0 / 10h | 0 / 3.0h | 0 / 0.7h | 0 / 130k |
| **TOTAL** | **4** | **13** | **31%** | **0 / 56h** | **1.50 / 16.8h** | **0 / 4.2h** | **~73k / 815k** |

> **Nota (gap 18, revision de dos lentes intento 1):** las horas-IA de las rondas `-fix1`/`-fix2` corresponden a sesiones de correccion COMPARTIDAS entre varias tareas (una sola ventana de `usage-meter` cubriendo T-01/T-02/T-03/T-13 a la vez); se reparten a partes iguales entre las tareas que tocaron en esa ventana (ver nota de cada tarea) en vez de contarse enteras en cada una, para no inflar el TOTAL.

## Fase 1 - Contrato y validacion

### T-01 - Esquema versionado `taxonomy.schema.json`, `backends` y plantillas
- **Estado**: completado
- **Tiempo humano**: est. 5h · real -
- **Prevision IA**: 55k in / 22k out tok
- **Tiempo IA**: real 0.35h (medido; usage-meter, 0.08h T-01 + 0.105h T-01-fix1 [sesion compartida con T-13-fix1: 0.21h/2, gap 18] + 0.16h T-01-fix2 [sesion compartida T-01/T-02/T-03/T-13-fix2: 0.65h/4, mismo patron])
- **Dependencias**: ninguna
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/schemas/taxonomy.schema.json`, `agent-kits/shared/knowledge-schema.py`, `agent-kits/shared/test_knowledge_schema.py`, `agent-kits/shared/templates/taxonomy.json`, `agent-kits/shared/copias.json`, `tests/test_knowledge_index.py`, `tests/test_knowledge_candidates.py`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `docs/knowledge/adr/ADR-018-arquitectura-de-memoria-markdown-canonico-backends-declarados.md`, `docs/knowledge/README.md` (nota: fuera de la lista original; necesario para mantener la fila de ADR-018 coherente con su nuevo estado, regla 10 "quien añade/cambia una entrada actualiza la tabla en el mismo cambio"; `docs/knowledge/**` siempre en alcance de `scope-check.py`)
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_knowledge_schema.py` -> valida `taxonomy.json` (version, categorias, evidencia, `backends`, `routing`, `evidence_levels`, `denylist`) con validador stdlib; rechaza estado/tag invalidos y un `routing` que cite un backend no declarado (CA-11, CA-13); tras fix2 ademas: `id_prefix` por defecto = slug del directorio raiz (no fijo), `folder` inseguro (`..`/absoluto/unidad Windows) rechazado, `evidence_levels` vacio o no iterable rechazado sin `TypeError`, `cargar_taxonomia(root=None)` usa el cwd, `default_taxonomy()`/CLI degradan con `UnicodeDecodeError`/fichero corrupto sin traceback, `categorias_por_backend_con_valor` distingue `true` de `"summary"`
  - Salida real (fix2): `40 passed in 0.29s`
  - `RED: agent-kits/shared/test_knowledge_schema.py (con knowledge-schema.py sustituido por un stub `validar()->[]`/`main()->0`) falló con "22 failed, 1 passed" (AttributeError en `default_taxonomy`/`cargar_taxonomia`/`categorias_por_backend`, y aserciones de exit code) · 2026-09-18`
  - `RED (fix2): los 15 tests nuevos de gaps 5/7/10/12/13/14/15 fallaron contra la version pre-fix (KeyError `id_prefix`, TypeError `evidence_levels` no iterable, UnicodeDecodeError sin capturar, `cargar_taxonomia(None)` ignorando el cwd, `folder` con traversal aceptado) · 2026-09-18`
**Criterios de aceptación**
- [x] `taxonomy.json` define categorias, carpeta, evidencia minima, `backends` (id, type, config) y `routing` por categoria hacia ids declarados.
- [x] Sin `taxonomy.json`, el plugin usa su default minimo propio (DECISION/PATTERN/GOTCHA/LESSON, backend `kwipu` desactivado) sin romper nada.
- [x] Una categoria sin `routing`, o con un id no declarado, no exporta a ningun backend (fail-closed); el error nombra fichero y campo; `ADR-018` pasa a `aceptada` al cerrar.
- **Nota T-01-fix1 (correccion posterior, 2026-09-18)**: `lint_plugin.py` senalaba `_TAXONOMY_FALLBACK` (antes `DEFAULT_TAXONOMY_FALLBACK`) como constante de respaldo sin fila en `copias.json` (ADR-016) y el respaldo habia divergido del canonico (`templates/taxonomy.json`) — faltaba `backends.kwipu.config.health`. RED: `agent-kits/shared/test_knowledge_schema.py::test_default_fallback_coincide_con_el_template` fallo con `AssertionError` (diff mostraba `health` ausente) · 2026-09-18. Fix: se anadio el bloque `taxonomy_fallback` a `copias.json` (mecanismo A, ancla `"version": 1,`/`]`, sustitucion `False`->`false`), se corrigio el respaldo para que coincida byte a byte con la plantilla, y se reformateo la constante `DEFAULT_TAXONOMY_FALLBACK` -> `_TAXONOMY_FALLBACK` (unico nombre que casa a la vez con la heuristica de `lint_plugin.py`, que hace `findall` no anclado, y con el `respaldos` de `copias.json`, que exige definicion anclada al inicio de linea). GREEN: `python -m pytest -q agent-kits/shared/test_knowledge_schema.py` -> `24 passed in 0.28s`. Se detecto ademas una colision de nombre de fichero introducida por el propio T-03 (`tests/test_knowledge_index.py` sobreescribio, sin darse cuenta, un test previo de `memory-retrieval`); se restauro el original y se reubico el contenido de T-03 en `tests/test_knowledge_candidates.py` (ver nota en T-03). Verificacion final de esta ronda: `python -m pytest -q tests/test_copias_declaradas.py agent-kits/shared/test_knowledge_schema.py` -> `45 passed in 0.52s`; `python scripts/lint_plugin.py` -> solo queda el `❌` preexistente de LES-016; `agent-kits/shared/ledger-lint.py docs/roadmap/2026-09-15-knowledge-services/tasks.md` -> exit 0.
- **Nota T-01-fix2 (correccion de la revision de dos lentes, intento 1, 2026-09-18)**: gaps 5 (id_prefix fijo "ca" en vez del slug del proyecto — `design.md:57`/`taxonomy.schema.json:17`), 6 (folder sin normalizar/acotar — CWE-22), 7 (`evidence_levels` no iterable -> `TypeError`), 10 (`categorias_por_backend` colapsaba `true`/`"summary"`), 12 (`cargar_taxonomia(root=None)` ignoraba el cwd), 13 (`evidence_levels: []` aceptado pese a `minItems: 1`), 14/15 (`UnicodeDecodeError` sin capturar en `default_taxonomy`/CLI) corregidos en `knowledge-schema.py` con TDD (RED confirmado contra copia pre-fix, GREEN contra la version final). Decision sin respaldo literal en spec/design: cuando `root` es `None` o su `basename` no produce un slug usable, `id_prefix` cae a `"ca"` como ultimo recurso (no hay una raiz de la que derivar nada mejor).
- **Changelog**: El plugin ahora valida la configuración de conocimiento del proyecto (`taxonomy.json`) y sus backends declarados, con un default seguro y sensible al proyecto (sin id_prefix ni rutas de categoría inseguras heredadas del plugin) cuando el proyecto no configura nada.

### T-02 - Indice canonico y validador determinista sobre la taxonomia configurada
- **Estado**: completado
- **Tiempo humano**: est. 5h · real -
- **Tiempo IA**: real 0.55h (medido; usage-meter, 0.39h T-02 + 0.16h T-02-fix2 [sesion compartida T-01/T-02/T-03/T-13-fix2: 0.65h/4, gap 18])
- **Prevision IA**: 55k in / 22k out tok
- **Dependencias**: T-01
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/knowledge-schema.py`, `agent-kits/shared/knowledge-index.py`, `agent-kits/shared/test_knowledge_schema.py`, `agent-kits/shared/test_knowledge_index_canonico.py` (renombrado desde `agent-kits/shared/test_knowledge_index.py`, gap 1), `tests/test_knowledge_candidates.py`, `docs/knowledge/README.md`
- **Verificacion**: `python -m pytest tests agent-kits/shared -q` -> gate de CI completo, colecta sin colision de basenames (gap 1); `python -m pytest -q agent-kits/shared/test_knowledge_schema.py agent-kits/shared/test_knowledge_index_canonico.py` -> indice estable y errores con ruta/campo, dos fixtures de `taxonomy.json` distintas dan carpetas/routing distintos, symlink/traversal fuera de `approved/<folder>` rechazado, BOM tolerado, `enlaces:` en lista de bloque YAML parseado, subcarpetas recorridas, `estado`/`fuentes`/`tags` con forma invalida rechazados cuando se declaran
  - Salida real (fix2): `python -m pytest -q agent-kits/shared/test_knowledge_index_canonico.py` -> `20 passed, 1 skipped in 0.90s` (el skip es el probe de symlink cuando la plataforma/permiso no los soporta)
  - Salida real (gate CI, gap 1): ver verificacion final de la ronda al pie del ledger — `python -m pytest tests agent-kits/shared -q` ya no aborta la coleccion
  - Regresion `knowledge-find.py` (`python -m pytest -q tests/test_knowledge_find.py`): `2 failed, 70 passed in 38.12s` — confirmado PRE-EXISTENTE: mismos 2 fallos (`test_show_imprime_la_entrada_completa_tal_cual`, `test_show_json_envuelve_el_contenido_con_su_ficha`, diff de espacios finales en `LES-001`) reproducidos igual en `git stash` sobre HEAD `3f28be7` (antes de tocar T-02); no son una regresion introducida por esta tarea.
  - RED: `python -m pytest -q agent-kits/shared/test_knowledge_index_canonico.py` contra un `knowledge-index.py` stub (`build_index` devolvia `{}, []`, `main` devolvia `0`) fallo con `9 failed, 4 passed in 0.33s` (AssertionError en duplicados/version/enlaces/candidatos/CLI) · 2026-09-18. Tras implementar `build_index`/`main` reales: `13 passed in 0.72s` (GREEN).
  - `RED (fix2): los 6 tests nuevos de gaps 3/4/6/8/9/17 fallaron contra la copia pre-fix (FileNotFoundError sin degradar, id perdido por BOM, enlaces de bloque ignorados, subcarpeta no indexada, estado/fuentes invalidos sin error) · 2026-09-18`
**Criterios de aceptación**
- [x] ID duplicado, version y enlaces rotos fallan; candidatos no aparecen.
- [x] `knowledge-find.py` no se rompe.
- [x] Dos proyectos con `taxonomy.json` distintos (p. ej. el default del plugin vs. uno con categorias de dominio propio) producen carpetas y enrutado distintos sin tocar codigo.
- **Changelog**: El plugin valida y construye un indice de conocimiento aprobado por proyecto, detectando IDs duplicados, versiones ausentes, enlaces rotos, rutas fuera de la carpeta aprobada o campos de frontmatter mal formados antes de exportarlos.
- **Nota de alcance (para la revision de dos lentes)**: `knowledge-index.py` opera SOLO sobre `docs/knowledge/approved/<folder>/`, no sobre el corpus legado `docs/knowledge/{adr,gotchas,lessons}/` (ese sigue con el indice manual + `knowledge-lint.py` diferido de ADR-006 D4, sin tocar). Decision tomada sin respaldo literal en spec/design mas alla de "indice canonico determinista sobre la taxonomia configurada"; exigir `version`/`enlaces` a las entradas legadas habria roto ADR-001..ADR-017/GOT-.../LES-... existentes (no llevan esos campos). Tambien: el parser de frontmatter y la carga de `knowledge-schema.py` se resolvieron con un loader `importlib` por ruta relativa (mismo fichero, misma carpeta `agent-kits/shared/`) en vez de reimplementar toda la validacion de `taxonomy.json`; no hay import de `knowledge-find.py` (se mantiene el criterio de scripts standalone).
- **Nota T-02-fix2 (correccion de la revision de dos lentes, intento 1, 2026-09-18)**: gap 1 (Critical) resuelto renombrando `test_knowledge_index.py` -> `test_knowledge_index_canonico.py` (basename unico; el `tests/test_knowledge_index.py` preexistente vigila un contrato distinto — la biyeccion del indice manual `docs/knowledge/README.md` — y no debe tocarse). Gaps 4 (`KnowledgeSchemaNoDisponible` + degradacion en `build_index`, mecanismo B de ADR-016), 6 (contencion `os.path.realpath`/`os.path.commonpath` sobre cada ruta indexada, defensa en profundidad ademas del rechazo de `folder` inseguro en T-01), 8 (lectura con `utf-8-sig`), 9 (parser de frontmatter extendido a listas en bloque YAML) y 17 (recorrido de subcarpetas via `os.walk`) corregidos en `knowledge-index.py`. Gap 3 (Important) resuelto PARCIALMENTE aqui: se anadio validacion de FORMA para `estado` (debe ser `aprobado` si se declara), `fuentes` (lista no vacia si se declara) y `tags` (lista si se declara) — ver `_validar_frontmatter_forma`. Se delega explicitamente a T-04 (`knowledge-curator`, ver su bloque de criterios) la comprobacion semantica que este indice NO puede hacer: `evidencia` frente al `min_evidence` de la categoria EXACTA asignada al aprobar (una carpeta puede servir a mas de una categoria, p. ej. `gotchas/` sirve a PATTERN y GOTCHA con evidencia minima distinta — el `folder` no basta para desambiguar) y la obligatoriedad de los campos en el momento de aprobar un candidato (aqui son opcionales por diseno: las entradas legadas de ejemplo o escritas a mano no los llevan).

### T-03 - Estructura e ignorados de derivados
- **Estado**: completado
- **Tiempo humano**: est. 3h · real -
- **Tiempo IA**: real 0.20h (medido; usage-meter, 0.04h T-03 + 0.16h T-03-fix2 [sesion compartida T-01/T-02/T-03/T-13-fix2: 0.65h/4, gap 18])
- **Prevision IA**: 35k in / 10k out tok
- **Dependencias**: T-01
- **Tipo**: docs
- **Archivos**: `.gitignore`, `docs/knowledge/candidates/`, `docs/knowledge/approved/`, `docs/knowledge/README.md`, `tests/test_knowledge_candidates.py` (nota: fuera de la lista original; la propia `Verificacion` de esta tarea ya lo citaba, se añade aqui para que `scope-check.py` y esta tabla queden coherentes con lo que realmente se ejecuta), `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`
- **Verificacion**: `python -m pytest -q tests/test_knowledge_candidates.py` -> fuentes e indice coherentes sin derivados, incluyendo el export derivado bajo un proyecto anidado (gap 11)
  - Salida real (fix2): `7 passed in 0.16s`.
  - TDD n/a: docs/config (estructura de carpetas, README de ownership, entradas de `.gitignore`, regla 10 de CONVENTIONS); el test de integracion se escribio junto al artefacto para verificar mecanicamente la estructura, no como ciclo RED-GREEN de una unidad de codigo.
**Criterios de aceptación**
- [x] Sin arbol projects; ownership documentado; export no versionado.
- **Changelog**: El flujo de conocimiento del proyecto ahora separa claramente lo propuesto (`candidates/`) de lo aprobado (`approved/`), con las exportaciones a backends siempre excluidas del control de versiones, incluso en proyectos anidados.
- **Nota T-01-fix1 (correccion posterior, 2026-09-18)**: el fichero de test de esta tarea se creo originalmente como `tests/test_knowledge_index.py`, nombre que YA pertenecia a un test previo de `memory-retrieval` (biyeccion del indice de `docs/knowledge/README.md`, commit `5f516f8`) y quedo sobrescrito sin darse cuenta (gap encontrado al correr la suite completa de `copias.json`). Se renombro a `tests/test_knowledge_candidates.py` y se restauro el fichero original; ver tambien el `Archivos`/`Verificacion` de esta tarea, ya corregidos arriba.
- **Nota T-03-fix2 (correccion de la revision de dos lentes, intento 1, 2026-09-18)**: gap 11 (Important) — `.gitignore:76-77` no llevaba el ancla `**/` que si llevan sus vecinos (`:71-72`), asi que un export derivado bajo un proyecto anidado (p. ej. `evals/fixtures/proyecto/.claude/knowledge-services/kwipu-export/`) no quedaba ignorado. Fix: se anadio `**/` a las dos lineas de exports de backends. Gap 20 (Minor) — regla 10 de `docs/CONVENTIONS.md` (y su espejo EN) solo enumeraba `adr/`/`gotchas/`/`lessons/`; se documento `docs/knowledge/candidates/{pending,needs_changes,rejected}/` y `docs/knowledge/approved/<folder>/` como arbol nuevo, indexado por `knowledge-index.py`, distinto del indice manual, nunca mezclado. RED: `test_git_check_ignore_cubre_export_derivado_anidado` (nuevo) fallo con `returncode == 1` contra el `.gitignore` pre-fix · 2026-09-18.

## Fase 2 - Curacion y workflow

### T-04 - Agente knowledge-curator, docs y evals
- **Estado**: borrador
- **Tiempo humano**: est. 5h · real -
- **Prevision IA**: 55k in / 24k out tok
- **Dependencias**: T-01, T-02
- **Tipo**: docs
- **Archivos**: `agents/knowledge-curator.md`, `agent-kits/knowledge-curator/`, `docs/agents/knowledge-curator.md`, `docs/agents/ROLES.md`, `docs/README.md`, `CLAUDE.md`, `evals/cases/agent-knowledge-curator.json`, `interop/**`
- **Verificacion**: `python scripts/lint_plugin.py` -> frontmatter/dependencias; `python evals/check.py` -> casos de activacion
**Criterios de aceptación**
- [ ] Unico escritor de candidatos/aprobados; contradicciones y alto impacto piden usuario.
- [ ] Interop regenerado.
- [ ] **Delegado desde el gap 3 de la revision de dos lentes intento 1 (T-01/T-02)**: al aprobar un candidato, el curator conoce la categoria EXACTA asignada (algo que `knowledge-index.py` no puede inferir solo del `folder`, porque una carpeta puede servir a varias categorias) y por tanto es quien debe (a) exigir `estado`/`evidencia`/`fuentes`/`tags` como obligatorios en el momento de aprobar (el indice solo valida su FORMA cuando estan presentes, nunca su presencia), y (b) comparar `evidencia` contra el `min_evidence` de esa categoria exacta antes de mover el candidato a `approved/`.

### T-05 - Documenter propone, no promociona
- **Estado**: borrador
- **Tiempo humano**: est. 4h · real -
- **Prevision IA**: 45k in / 18k out tok
- **Dependencias**: T-04
- **Tipo**: docs
- **Archivos**: `agents/documenter.md`, `docs/agents/documenter.md`, `docs/agents/ROLES.md`, `docs/agents/CONTRACTS.md`, `evals/cases/agent-documenter.json`, `interop/**`
- **Verificacion**: `python scripts/lint_plugin.py` -> contratos/rutas; `python evals/check.py` -> activacion
**Criterios de aceptación**
- [ ] Propuesta incluye categoria, fuentes y evidencia; sin propuesta no hay fallo.
- [ ] No escribe estados ni exports.

### T-06 - Fase 4-bis Knowledge Gate
- **Estado**: borrador
- **Tiempo humano**: est. 5h · real -
- **Prevision IA**: 50k in / 20k out tok
- **Dependencias**: T-04, T-05
- **Tipo**: docs
- **Archivos**: `commands/dev-cycle.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `docs/agents/ROLES.md`, `docs/agents/CONTRACTS.md`, `evals/cases/command-dev-cycle.json`, `interop/**`
- **Verificacion**: `python scripts/export-interop.py --check` -> 0; `python evals/check.py` -> 0
**Criterios de aceptación**
- [ ] Solo tras QA/documenter; omision honesta sin candidatos.
- [ ] Kwipu no condiciona cierre.

## Fase 3 - Kwipu

### T-07 - `knowledge-sync.py`, contrato de adaptador y adaptador `test`
- **Estado**: borrador
- **Tiempo humano**: est. 7h · real -
- **Prevision IA**: 70k in / 30k out tok
- **Dependencias**: T-02, T-03, `session-end-durable-capture` T-01 (`outbox.py`)
- **Tipo**: backend
- **Archivos**: `skills/knowledge-services/scripts/knowledge-sync.py`, `skills/knowledge-services/backends/__init__.py`, `skills/knowledge-services/backends/README.md`, `skills/knowledge-services/scripts/test_knowledge_sync.py`, `evals/fixtures/knowledge-services/backend_test.py`, `.gitignore`
- **Verificacion**: `python -m pytest -q skills/knowledge-services/scripts/test_knowledge_sync.py` -> `routing` aplicado ANTES de `plan`; `--dry-run`/`--check`/`--rebuild`; staging y dead-letter via `outbox.py`; el adaptador `type: "test"` de la fixture recibe exactamente las entradas enrutadas sin tocar el nucleo (CA-12, CA-15)
**Criterios de aceptación**
- [ ] Solo approved valido; reejecucion idempotente; un error no borra la publicacion anterior.
- [ ] El contrato (`health · plan · apply · verify · rebuild · revoke`) esta documentado y un adaptador incompleto falla al cargar con mensaje claro.
- [ ] Una categoria con `routing.<id>: false` nunca llega al adaptador; `"summary"` entrega solo el resumen declarado.

### T-08 - Adaptador Kwipu (`markdown-export`) y skill
- **Estado**: borrador
- **Tiempo humano**: est. 5h · real -
- **Prevision IA**: 50k in / 20k out tok
- **Dependencias**: T-07
- **Tipo**: backend
- **Archivos**: `skills/knowledge-services/backends/markdown_export.py`, `skills/knowledge-services/scripts/test_backend_markdown_export.py`, `skills/knowledge-services/SKILL.md`, `skills/knowledge-services/references/`, `evals/cases/skill-knowledge-services.json`, `docs/README.md`, `CLAUDE.md`
- **Verificacion**: `python -m pytest -q skills/knowledge-services/scripts/test_backend_markdown_export.py` -> export con `manifest.json` y hashes estables, `health` con URL local/timeout/sano/degradado y parsea el JSON real de `GET /health` del bridge (`status`, `embed_model`, `property_graph`, `ollama`) desde una fixture grabada el 2026-09-18, `rebuild` reproduce el mismo manifiesto, `revoke` retira el fichero del export, `verify` marca desfase cuando el manifiesto no coincide con `/graph/snapshot` y nombra el remedio (`build_view` + reinicio) sin ejecutarlo
**Criterios de aceptación**
- [ ] Kwipu es un adaptador mas del contrato de T-07; nada en `knowledge-sync.py` menciona Kwipu.
- [ ] Skill corta con referencias y sin secretos; no hooks/red ni Graphiti.
- [ ] `export_dir` viene de `backends.kwipu.config`; el adaptador no ejecuta `build_view`, `docker` ni reinicios: el reindexado es del stack y `verify` solo lo detecta (CA-16).
- [ ] Cada fichero exportado lleva `project`, `scope`, `category`, `source`, `confidence` + `knowledge_id`, `version`, `hash`, derivados de la entrada y de `taxonomy.json` (CA-17).

### T-09 - Opt-in en setup y doctor a traves del registro de capacidades
- **Estado**: borrador
- **Tiempo humano**: est. 4h · real -
- **Prevision IA**: 40k in / 16k out tok
- **Dependencias**: T-08, T-13
- **Tipo**: devops
- **Archivos**: `commands/setup.md`, `commands/doctor.md`, `agent-kits/shared/doctor.py`, `agent-kits/shared/test_doctor.py`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`, `docs/INTEROP.md`, `docs/en/INTEROP.md`, `interop/**`
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_doctor.py` -> desactivado, sano, timeout, export atrasado y `taxonomy.json` invalido con fichero+campo+arreglo; `doctor.py` no contiene la cadena `kwipu` (todo llega por `capabilities.py`); `python scripts/export-interop.py --check` -> 0
**Criterios de aceptación**
- [ ] Config no sensible e idempotente; no MCP automatico.
- [ ] Fallo opcional no es error de ciclo.
- [ ] `/setup` ofrece las capacidades registradas en un solo paso y escribe `taxonomy.json` desde la plantilla si no existe (CA-14).

### T-13 - Registro de capacidades `capabilities.py`
- **Estado**: completado
- **Tiempo humano**: est. 3h · real -
- **Tiempo IA**: real 0.40h (medido; usage-meter, 0.13h T-13 + 0.105h T-13-fix1 [sesion compartida con T-01-fix1: 0.21h/2, gap 18] + 0.16h T-13-fix2 [sesion compartida T-01/T-02/T-03/T-13-fix2: 0.65h/4, mismo patron])
- **Prevision IA**: 35k in / 14k out tok
- **Dependencias**: T-01
- **Tipo**: backend
- **Archivos**: `agent-kits/shared/capabilities.py`, `agent-kits/shared/test_capabilities.py`, `agent-kits/shared/README.md`, `scripts/lint_plugin.py`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md`
- **Verificacion**: `python -m pytest -q agent-kits/shared/test_capabilities.py` -> registro con dos capacidades (`knowledge-gate`, `kwipu`) y una tercera de fixture; `enabled/health/doctor/setup_step` por capacidad; una capacidad rota degrada a `error` sin tumbar el resto; tras fix2 ademas: `registrar()` sin `id` levanta `ValueError` (no `KeyError`), `enumerar()` memoiza la lectura de `taxonomy.json` durante su propia llamada y no sirve una taxonomia obsoleta a la siguiente
  - Salida real (fix2): `14 passed in 0.21s`.
  - RED: `python -m pytest -q agent-kits/shared/test_capabilities.py` contra un `capabilities.py` stub (`REGISTRO=[]`, `registrar`/`enumerar` no-op, `main` devolvia `0`) fallo con `8 failed, 3 passed in 0.29s` (KeyError/AssertionError: sin `knowledge-gate`/`kwipu`, sin evaluacion real, CLI sin salida) · 2026-09-18. Tras implementar el registro real: `11 passed in 0.23s` (GREEN).
  - `RED (fix2): test_registrar_sin_id_levanta_valueerror (Failed: DID NOT RAISE) y test_enumerar_memoiza_la_taxonomia_por_llamada (assert 5 == 1) fallaron contra la version pre-fix (git HEAD) · 2026-09-18`
**Criterios de aceptación**
- [x] Contrato `{id, config_path, enabled, health, doctor, setup_step}` documentado; sin dependencias.
- [x] Anadir una capacidad es un registro nuevo, no una edicion de `doctor.py` (CA-14).
- **Changelog**: `/setup` y `/doctor` podran enumerar las capacidades opcionales del plugin (Knowledge Gate, Kwipu y las que se añadan despues) desde un unico registro, sin codigo especifico por capacidad, con una sola lectura de `taxonomy.json` por consulta.
- **Nota (para la revision de dos lentes)**: esta tarea NO toca `doctor.py` ni `setup.md` (integrarlos es T-09, fuera de este despacho); `capabilities.py` deja el registro listo para que T-09 solo llame a `enumerar()`. La comprobacion de red real de Kwipu (`GET /health` del bridge) queda deliberadamente fuera: aqui `kwipu.health` solo refleja si esta declarado/activado en `taxonomy.json`, delegando la comprobacion en vivo al adaptador `markdown-export` de T-08 (asi lo indica la enmienda 2026-09-18 del spec, punto 3, que separa contrato de lectura del adaptador del registro de capacidades).
- **Nota T-13-fix1 (correccion posterior, 2026-09-18)**: `lint_plugin.py` seguia listando `agent-kits/shared/capabilities.py` en `PIEZAS_PLANIFICADAS` (aviso de pieza planificada-pero-ausente) pese a que esta tarea ya lo construyo — se elimino la entrada de la lista y se anadio `scripts/lint_plugin.py` al `Archivos` de esta tarea (arriba). TDD n/a: es una lista de datos estatica, no logica nueva. Verificacion: `python scripts/lint_plugin.py` -> solo el `❌` preexistente de LES-016, sin el aviso de `capabilities.py`.
- **Nota T-13-fix2 (correccion de la revision de dos lentes, intento 1, 2026-09-18)**: gap 16 (Minor) — `registrar()` asumia `cap["id"]` y lanzaba `KeyError` sin envolver si faltaba; ahora valida explicitamente y levanta `ValueError` con mensaje claro. Gap 22 (Minor) — `enumerar()` releia y revalidaba `taxonomy.json` hasta 5 veces por llamada (`knowledge-gate` + `kwipu` cada uno por su lado, y `kwipu` ademas en `enabled`/`health`/`doctor`); se anadio una cache modulo `_CACHE_TAXONOMIA` memoizada por `root`, vaciada al entrar y al salir de `enumerar()` (nunca sobrevive entre llamadas, para no servir una taxonomia obsoleta si se edita entre dos `enumerar()`).

## Fase 4 - Regresion y cierre

### T-10 - Aislamiento, seguridad y regresion
- **Estado**: borrador
- **Tiempo humano**: est. 4h · real -
- **Prevision IA**: 40k in / 16k out tok
- **Dependencias**: T-01 a T-09, T-13
- **Tipo**: test
- **Archivos**: `tests/test_knowledge_services.py`, `tests/test_hooks_shell.py`, `tests/test_lint_plugin.py`, `evals/fixtures/`, `docs/agents/CONTRACTS.md`
- **Verificacion**: `python -m pytest -q tests/test_knowledge_services.py tests/test_hooks_shell.py tests/test_lint_plugin.py` -> export aislado y hooks sin red
**Criterios de aceptación**
- [ ] Mutantes de filtrado mueren.
- [ ] YAML corrupto y rutas maliciosas fallan de forma segura.

### T-11 - Documentacion, espejos y changelog
- **Estado**: borrador
- **Tiempo humano**: est. 3h · real -
- **Prevision IA**: 30k in / 12k out tok
- **Dependencias**: T-04 a T-10
- **Tipo**: docs
- **Archivos**: `README.md`, `README.es.md`, `docs/README.md`, `docs/en/README.md`, `docs/FLOWS.md`, `docs/en/FLOWS.md`, `docs/INTEROP.md`, `docs/en/INTEROP.md`, `docs/agents/ROLES.md`, `docs/agents/CONTRACTS.md`, `CHANGELOG.md`, `CHANGELOG.es.md`
- **Verificacion**: `python scripts/lint_plugin.py` -> 0; lectura: ES/EN comparten alcance
**Criterios de aceptación**
- [ ] Kwipu opcional/derivado; Graphiti diferido; ownership sin solape; doc del contrato de adaptador y de `backends` en ES/EN.

### T-12 - Puertas completas, QA y retro
- **Estado**: borrador
- **Tiempo humano**: est. 3h · real -
- **Prevision IA**: 20k in / 12k out tok
- **Dependencias**: T-10, T-11
- **Tipo**: test
- **Archivos**: `docs/roadmap/2026-09-15-knowledge-services/tasks.md`, `docs/roadmap/2026-09-15-knowledge-services/testing/`, `interop/**`
- **Verificacion**: `python scripts/lint_plugin.py` -> 0 · `python evals/check.py` -> 0 · `python scripts/export-interop.py --check` -> 0
**Criterios de aceptación**
- [ ] Ledger con evidencia y revision sin gaps Critical/Important.
- [ ] QA reconoce sin UI y retro abre `retro-gate.py`.

## Revisión de dos lentes — intento 1: 22 gaps (1 Critical, 10 Important, 11 Minor), lentes A+B (C y D no aplican por `review-lens-select.py`), alcance Fase 1 + T-13 (`650127a..df2e2dd`)

Puerta previa: `scope-check.py --base 650127a` -> 24 ficheros, 0 fuera de alcance, exit 0. Revisores: agente `reviewer` (tier `opus`/`high` del frontmatter), contexto fresco. Decisiones flaggeadas por el implementer: (a) indice solo sobre `approved/<folder>` -> conforme (design.md:64, ADR-006 D4); (b) `importlib` sin respaldo -> gap #4; (c) `kwipu.health` sin red en `capabilities.py` -> conforme (enmienda 2026-09-18, la red es de T-08); (d) no tocar `doctor.py`/`setup.md` -> conforme (T-09); (e) 0.21 h sumadas a dos tareas -> gap #18.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | **Critical** | `agent-kits/shared/test_knowledge_index.py` comparte basename con el preexistente `tests/test_knowledge_index.py`; sin `conftest.py`/`importmode=importlib`, el comando de CI (`python -m pytest tests agent-kits/shared -q`, `ci.yml.MANUAL-COPY:52`) aborta la coleccion entera: 0 tests ejecutados. La Verificacion de T-02 solo corre `agent-kits/shared/` y por eso es verde en local | T-02 | corregido: renombrado a `agent-kits/shared/test_knowledge_index_canonico.py` (basename unico; el `tests/test_knowledge_index.py` original queda intacto, vigila un contrato distinto); actualizada la unica referencia cruzada en `tests/test_knowledge_candidates.py:3` y la Verificacion de T-02 para incluir el gate completo | `python -m pytest tests agent-kits/shared -q` ya no aborta la coleccion (ver verificacion final del ledger) |
| 2 | Important | El enrutado positivo no tiene test: `categorias_por_backend` (`knowledge-schema.py:252-260`) solo se invoca en el camino negativo; mutante `return []` -> `37 passed` | T-01/T-02 | corregido: nuevo test `test_dos_taxonomias_con_routing_distinto_seleccionan_categorias_distintas` ejercita el camino POSITIVO de `categorias_por_backend` (una categoria SI enrutada aparece), ademas de `categorias_por_backend_con_valor` (gap 10) que expone el valor exacto (`true`/`"summary"`) | `python -m pytest -q agent-kits/shared/test_knowledge_schema.py::test_dos_taxonomias_con_routing_distinto_seleccionan_categorias_distintas` -> passed; mutante `return []` ahora falla ese test |
| 3 | Important | La Verificacion de T-01 declara «rechaza estado/tag invalidos» y nada lo implementa; el contrato de frontmatter de la entrada (spec.md:23, CA-01: `estado`, `evidencia`, `fuentes`, `relaciones`, `tags clave:valor`) se queda en `id`/`version`/`enlaces` y ninguna tarea pendiente lo declara | T-01/T-02 | corregido PARCIALMENTE + delegado: `knowledge-index.py._validar_frontmatter_forma` valida la FORMA de `estado`/`fuentes`/`tags` cuando estan presentes (no su obligatoriedad); la comprobacion semantica (evidencia >= min_evidence de la categoria EXACTA, que el `folder` no desambigua) y la obligatoriedad al aprobar se delegan explicitamente a T-04 (nuevo criterio anadido a su bloque, ver arriba) | `python -m pytest -q agent-kits/shared/test_knowledge_index_canonico.py -k gap3` -> 3 passed; criterio nuevo en el bloque T-04 |
| 4 | Important | `knowledge-index.py:44-54,104` carga `knowledge-schema.py` por ruta relativa via `importlib` sin respaldo declarado ni degradacion (ADR-016 veta el import por ruta salvo mecanismo B: canonico + respaldo en `copias.json`); sin el modulo al lado -> traceback `FileNotFoundError`. `capabilities.py` si degrada (`_resolver`) | T-02 | corregido: `_cargar_knowledge_schema()` levanta `KnowledgeSchemaNoDisponible` con mensaje claro (fichero ausente, spec/loader invalido, o excepcion durante `exec_module`); `build_index()` la atrapa y devuelve `({}, [error])` en vez de propagar (mecanismo B de ADR-016, mismo patron que `capabilities.py._resolver`) | `python -m pytest -q agent-kits/shared/test_knowledge_index_canonico.py::test_gap4_knowledge_schema_ausente_degrada_sin_traceback` -> passed; RED confirmado con `FileNotFoundError` sin envolver contra la copia pre-fix |
| 5 | Important | `id_prefix` por defecto `"ca"` (`templates/taxonomy.json:3`, `knowledge-schema.py:59`) contradice `design.md:57` y `taxonomy.schema.json:17` (default = slug del directorio del proyecto); un consumidor sin `taxonomy.json` heredaria el prefijo del plugin | T-01 | corregido: se retiro `id_prefix` fijo de `templates/taxonomy.json` y de `_TAXONOMY_FALLBACK`; `_con_id_prefix_por_defecto()` lo calcula como el slug kebab-case de `os.path.basename(root)` cuando el proyecto no lo declara, sin pisar un `id_prefix` explicito. Decision sin respaldo literal: si `root` es `None` o no produce slug usable, cae a `"ca"` como ultimo recurso (senalado en la nota T-01-fix2) | `test_id_prefix_por_defecto_es_el_slug_del_directorio_raiz`, `test_id_prefix_explicito_del_proyecto_no_se_pisa`, `test_default_template_no_declara_id_prefix_fijo` -> passed |
| 6 | Important | `folder` de categoria no se normaliza ni se acota (`knowledge-schema.py:201-202`, `knowledge-index.py:110,118`): `"../candidates/pending"` o una ruta absoluta pasan `validar` y el indice sale de `approved/` (CWE-22, path traversal por config) | T-01/T-02 | corregido en dos capas: (a) `knowledge-schema.validar()` rechaza `folder` con `..`, `/`/`\` inicial o unidad de Windows (`_folder_seguro`); (b) defensa en profundidad en `knowledge-index.build_index()` con `_ruta_segura_dentro()` (`os.path.realpath`/`os.path.commonpath`) para symlinks u otras vias que la config no controle | `test_folder_con_traversal_falla`, `test_folder_absoluto_posix_falla`, `test_folder_con_unidad_windows_falla` (capa T-01) + `test_gap6_symlink_fuera_de_la_carpeta_aprobada_falla` (capa T-02, se salta si la plataforma no soporta symlinks) -> passed/skipped |
| 7 | Important | `evidence_levels` no iterable (p. ej. `5`) -> `TypeError` en `knowledge-schema.py:205-206` en vez del error `{fichero, campo, mensaje}` que ya estaba en la lista (`:160-161`) | T-01 | corregido: `evidence_levels` valido/no-vacio/lista-de-str se calcula UNA vez antes del bucle de categorias (antes se recalculaba `config.get(...) or FALLBACK` en cada iteracion, con riesgo de `TypeError` si el valor no era falsy pero tampoco iterable) | `test_evidence_levels_no_iterable_no_lanza_typeerror` -> passed; RED reproducido con `TypeError: argument of type 'int' is not iterable` contra la copia pre-fix |
| 8 | Important | El indice no tolera BOM (`knowledge-index.py:61,70,126`): una entrada valida en `utf-8-sig` desaparece con «falta `id`» y arrastra «enlace roto» a quien la cite | T-02 | corregido: lectura de cada entrada con `encoding="utf-8-sig"` (tolera BOM y UTF-8 sin BOM por igual) | `test_gap8_entrada_con_bom_se_lee_igual` -> passed; RED con `errores` no vacio (frontmatter corrupto) contra la copia pre-fix |
| 9 | Important | El parser de frontmatter solo entiende listas inline; `enlaces:` en bloque YAML (`  - X`) queda `[]` en silencio (`knowledge-index.py:76,81-85,149`) y la deteccion de enlaces rotos pasa a no-op | T-02 | corregido: `_frontmatter()` extendido para reconocer una clave sin valor en su misma linea seguida de items `- X` indentados como lista en bloque | `test_gap9_enlaces_en_lista_de_bloque_se_parsean` -> passed; RED con `enlaces == []` (en vez de `['GOT-002']`) contra la copia pre-fix |
| 10 | Important | `categorias_por_backend` colapsa `routing: true` y `"summary"` (`knowledge-schema.py:252-260`): el consumidor (T-08) no puede distinguir «entero» de «solo resumen»; fail-open frente a `taxonomy.schema.json:78` | T-01 | corregido: nueva `categorias_por_backend_con_valor()` devuelve `(categoria, valor_de_routing)` sin colapsar `true`/`"summary"`; `categorias_por_backend()` se mantiene (delega en la nueva) para no romper consumidores existentes | `test_categorias_por_backend_con_valor_distingue_summary_de_true` -> passed |
| 11 | Important | `.gitignore:75-76` sin el ancla `**/` que llevan sus vecinos (`:70-71`): el export de un proyecto anidado (`evals/fixtures/proyecto/.claude/knowledge-services/kwipu-export/`) NO se ignora; el test (`tests/test_knowledge_candidates.py:64-70`) solo cubre la raiz | T-03 | corregido: se anadio `**/` a las dos lineas de exports de backends en `.gitignore` | `test_git_check_ignore_cubre_export_derivado_anidado` (nuevo) -> passed; RED con `returncode == 1` contra el `.gitignore` pre-fix |
| 12 | Minor | `cargar_taxonomia()` con `root=None` ignora el cwd y devuelve el default (`knowledge-schema.py:230,236`) pese al docstring; fail-open de configuracion para un llamador que omita `root` | T-01 | corregido: la resolucion de ruta ahora usa `root if root is not None else "."` de forma consistente antes de comprobar `os.path.isfile`, en vez de un atajo que saltaba directo al default cuando `root` era `None` | `test_cargar_taxonomia_root_none_usa_el_cwd` -> passed |
| 13 | Minor | `evidence_levels: []` se acepta (`:157-161`) y por ser falsy se sustituye por la escalera del plugin (`:205`); el esquema declara `minItems: 1` | T-01 | corregido: `validar()` anade un error explicito cuando `evidence_levels` es una lista vacia (antes se sustituia en silencio por el fallback) | `test_evidence_levels_vacio_falla` -> passed |
| 14 | Minor | `default_taxonomy()` promete «nunca lanza» pero no captura `UnicodeDecodeError` (`:126-132`): plantilla en UTF-16/truncada -> traceback en vez de caer al respaldo | T-01 | corregido: el `except` de `default_taxonomy()` pasa de `(OSError, json.JSONDecodeError)` a `(OSError, ValueError)` (`UnicodeDecodeError` es subclase de `ValueError`, igual que `JSONDecodeError`) | `test_default_taxonomy_con_plantilla_corrupta_cae_al_respaldo` -> passed |
| 15 | Minor | `main()` del CLI solo captura `JSONDecodeError` (`:276-284`): `OSError`/`UnicodeDecodeError` -> traceback en vez del exit 2 documentado; TOCTOU `isfile`/`open` | T-01 | corregido: se elimino el `isfile` previo (evita el TOCTOU) y el `open`+`json.load` va dentro de un unico try/except con `FileNotFoundError`, `json.JSONDecodeError` y `(OSError, UnicodeDecodeError)` -> exit 2 con mensaje, sin `isfile` redundante | `test_cli_fichero_con_encoding_invalido_exit_2`, `test_cli_ruta_es_directorio_exit_2` -> passed |
| 16 | Minor | `registrar()` asume `id` (`capabilities.py:92-94`): entrada sin `id` -> `KeyError` sin envolver en la unica puerta de extension | T-13 | corregido: `registrar()` valida `isinstance(cap, dict)` y `cap.get("id")` no vacio ANTES del bucle de comparacion, levantando `ValueError` con mensaje claro en vez de dejar que el bucle lance `KeyError` | `test_registrar_sin_id_levanta_valueerror` -> passed; RED con `Failed: DID NOT RAISE` contra `git HEAD` |
| 17 | Minor | El indice no recorre subcarpetas (`knowledge-index.py:121`, `os.listdir` de un nivel) y no avisa: `approved/adr/2026/X.md` no existe para el indice | T-02 | corregido: `build_index()` usa `os.walk()` (con `dirnames`/`filenames` ordenados) en vez de `os.listdir()`, recorriendo subcarpetas de cada `folder` declarado | `test_gap17_entrada_en_subcarpeta_se_indexa` -> passed; RED con `'ADR-030' not in indice` contra la copia pre-fix |
| 18 | Minor | Contabilidad: los mismos 0.21 h de la ronda fix1 se suman a T-01 y a T-13 (`tasks.md:35,167,27`); el TOTAL los cuenta dos veces y `/retro` propagaria el sesgo a `CALIBRATION.md` | T-01/T-13 | corregido: confirmado con `usage-meter.py status` que `T-01-fix1`/`T-13-fix1` son la MISMA ventana (`10:42:11`/`10:42:12`, 1s de diferencia) — se repartieron los 0.21h a partes iguales (0.105h cada una) en vez de sumar el total a ambas; el mismo criterio se aplico a la ronda `-fix2` (0.65h/4 entre T-01/T-02/T-03/T-13, tambien una unica ventana), documentado en la nota de "Resumen de progreso" y en cada tarea | `python agent-kits/shared/usage-meter.py status` confirma las ventanas compartidas; TOTAL de "Resumen de progreso" recalculado (1.50h en vez de 1.06h+0.65h extra sin repartir) |
| 19 | Minor | `design.md:39-44` mostraba `path`/`health` colgando del backend; esquema, plantilla y CA-16 exigen `config.export_dir` | design | **corregido por el orquestador** (ejemplo alineado: `config.export_dir`, `config.health`; Graphiti tambien bajo `config`, endpoint `/mcp` de la enmienda 2026-09-18) | este commit |
| 20 | Minor | Regla 10 de `docs/CONVENTIONS.md` («donde vive» `docs/knowledge/`) sigue enumerando solo `adr/`/`gotchas/`/`lessons/`; `candidates/` y `approved/` solo aparecen en `docs/knowledge/README.md` | T-03 | corregido: se documento `docs/knowledge/candidates/{pending,needs_changes,rejected}/` y `docs/knowledge/approved/<folder>/` en la regla 10 de `docs/CONVENTIONS.md` y su espejo `docs/en/CONVENTIONS.md`, senalando que los indexa `knowledge-index.py` y que es un arbol distinto del indice manual (nunca mezclado) | lectura de `docs/CONVENTIONS.md`/`docs/en/CONVENTIONS.md` regla 10 (espejo ES/EN al dia) |
| 21 | Minor | La plantilla reutiliza los nombres `adr`/`gotchas`/`lessons` para `approved/<folder>` conviviendo con el corpus legado del mismo nombre; riesgo de escribir en el arbol equivocado (advertido en `approved/README.md`, no en la plantilla) | T-01/T-03 | **deuda aceptada** (orquestador): el aviso vive en `approved/README.md`; T-04 (`knowledge-curator`) fija la resolucion categoria -> carpeta y lo documenta | Lente A |
| 22 | Minor | `capabilities.enumerar()` reejecuta `_cargar_knowledge_schema()` y relee `taxonomy.json` cinco veces por llamada (`capabilities.py:118-158`), en la ruta que `/doctor` invocara | T-13 | corregido: cache modulo `_CACHE_TAXONOMIA` memoizada por `os.path.abspath(root)`, vaciada al entrar y al salir de `enumerar()` (`try/finally`); `_knowledge_gate_health` y `_kwipu_backend_config` la consultan en vez de llamar a `_cargar_knowledge_schema()`+`cargar_taxonomia()` cada uno por su lado | `test_enumerar_memoiza_la_taxonomia_por_llamada` (1 sola llamada real) y `test_enumerar_no_sirve_taxonomia_obsoleta_entre_llamadas` (la cache no persiste entre llamadas) -> passed; RED con `assert 5 == 1` contra `git HEAD` |

Fuera de alcance de este intento y anotado para tareas pendientes: `.gitignore` solo cubre exports bajo `.claude/knowledge-services/*-export/` mientras CA-16 contempla `export_dir` fuera de `.claude/` (T-08); `test_sin_dependencias_externas` comprueba por `in texto` y no por AST (calidad de test, T-10).
