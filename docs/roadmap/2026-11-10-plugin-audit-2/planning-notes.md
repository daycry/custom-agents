# Informe de la enmienda del plan `2026-11-10-plugin-audit-2`

Estado final de los ficheros (sin comitear, en `docs/roadmap/2026-11-10-plugin-audit-2/`):
- `improvement-plan.md`: 21 KB.
- `tasks.md`: 59.672 bytes, 36 tareas en 6 fases. `ledger-lint.py`: 0 incoherencias y 0 avisos.
- No se ha tocado código ni otros ficheros, ni hay commits. La rama sigue siendo `fix/plugin-audit-remediation`.

Presupuesto: 135 h humanas base, 162 h con margen del 20 %, 6.750 € de horas (8.100 € con margen) y 9.620k tokens (unos 64 € con `.claude/rates.json`).

| Fase | Tareas | H. humanas | € horas | Tokens |
|---|---|---|---|---|
| 1 Defectos | T-01…T-07 | 15 | 750 | 1.090k |
| 2 Retirada decidida | T-08…T-10 | 21 | 1.050 | 1.350k |
| 3 Tokens | T-11…T-21 | 30 | 1.500 | 2.260k |
| 4 Simplificación | T-22…T-29 | 37 | 1.850 | 2.670k |
| 5 Alcance y entrenamiento | T-30…T-34 | 25 | 1.250 | 1.750k |
| 6 Higiene | T-35, T-36 | 7 | 350 | 500k |
| Total | 36 | 135 | 6.750 | 9.620k |

Sin la fase 5: 110 h, 7.870k tokens, 5.500 € (6.600 € con margen). T-30 (evaluación) no espera decisión.

## 1. Tareas que cambiaron respecto al primer plan

- T-02: ahora invoca skills por la ruta del `SKILL.md`, no por la herramienta `Skill` (ver apartado 4).
- T-03: declara que en Codex desaparece el adaptador `custom-agents-confluence-pull` y en OpenCode `/confluence-pull`; la colisión de nombre solo existe en Claude Code.
- T-13 (antes T-10, 2.1): cambia solo la numeración por la reordenación de fases.
- T-15 (cierre de `/dev-cycle`, antes T-12): ya no mueve el paso Kwipu/Graphiti de `/setup`, porque T-08 lo borra.
- T-16 (receta del kit, antes T-13): el criterio prueba la resolución sin `CLAUDE_PLUGIN_ROOT`, con raíces `.codex` y `.opencode`.
- T-19 (índice de arranque): añade la prueba de que Codex y OpenCode conservan el índice.
- T-23 (hooks, `async` y handler único): dice qué soporta cada runtime.
- T-24 (retirar shells): conserva los alias `*.sh`, que son identidades de hook en Codex y OpenCode, o declara la ruptura.
- T-26 (instalador): solo retira lo que la cobertura pruebe inalcanzable; no toca ninguna vía de instalación de Codex ni OpenCode.
- T-08 (nueva): retirada de Kwipu y Graphiti, decidida por el usuario.
- T-09 (nueva): qué hacer con el marco de `knowledge-services` sin backends.
- T-10 (nueva): `plugin-dev` sale del plugin distribuido.
- T-30 y T-31 (nuevas): evaluación de `training-data-services` frente a una exportación a posteriori, y la exportación condicionada al veredicto.
- T-32 a T-34: modos de implementación, retro y fusiones. La fusión de `/roadmap-metrics` se juntó con las skills en T-34.
- T-35 y T-36 (higiene): T-35 pasa `kwipu-metadata` y la rama `fix/graphiti-add-memory-uuid` a «cerrar o cancelar por retirada» y deja `dev-cycle-dataset` a T-31. T-36 revisa además la memoria aprobada que cita Kwipu o Graphiti.
- T-14 (2.9, «Alcance y activación»): incluye las cuatro skills de contenido, que se conservan por decisión del usuario.
- T-29 (renombrar tests): excluye los tests que T-08 y T-09 retiran y no toca `training-data-services`.
- Retirado del plan: la tarea de la statusline, la partición en satélites, la alternativa «skills de nicho no implícitas», la cancelación de `dev-cycle-dataset` y el borrado de las cuatro skills de contenido (fue una tarea durante un tiempo y se eliminó cuando el usuario las conservó).

## 2. Partición por runtime (`fichero:línea`)

- Claude Code: `install/modules.mjs:76-77` solo permite entrega selectiva en modo copia. `agent-kits/shared/modules.json` ya tiene los perfiles `core`, `developer`, `research` y `full`. `.claude-plugin/marketplace.json` lista un único plugin con `source: ./`.
- OpenCode: `install/modules.mjs:81` falla con «selective delivery is not supported by the OpenCode installer».
- Plugins nativos de Codex: `install/modules.mjs:82` entrega el bundle completo. `scripts/export-interop.py:284-338` genera un único `plugin.json` y un marketplace con un solo plugin (`.agents/plugins/marketplace.json`).
- Qué exigiría partir: un plugin y un manifiesto por satélite en Claude y Codex, copia selectiva e índice filtrado en OpenCode, y N manifiestos por release. Lo estimé en unas 10 h de mecánica.
- Conclusión: con las decisiones del usuario no queda qué partir. Solo `plugin-dev` (353 caracteres de description, unos 88 tokens por sesión, 58 KB) sería candidata, y T-10 la saca por una vía más simple (moverla a `.claude/skills/plugin-dev/`).
- No verifiqué que Claude Code o Codex acepten varios plugins con `source` en subdirectorios del mismo repositorio. Tras descartar la partición ya no hacía falta.

## 3. Medidas de la retirada

Medido con `wc -l` sobre el árbol versionado, HEAD `129dbeb`.

**Kwipu y Graphiti (T-08)**
- Código: 7.343 líneas (`backends/graphiti*.py` 4.646, `markdown_export.py` 1.804, `kwipu-project-add.py` 674, `_mcp_fake.py` 219), más unas 228 de `capabilities.py` (`:243-470`).
- Test: 11.779 líneas (8.408 en la skill y 3.371 en `tests/test_graphiti_model.py` y `tests/test_graphiti_security.py`).
- Fixtures: 1.811 líneas.
- Docs: 973 líneas (`kwipu-adapter.md` 479 y `docs/knowledge-services-graphiti.md` más su espejo EN 494).
- No medí las líneas que salen de `knowledge-schema.py` ni de `test_capabilities.py`; solo conté menciones (65 en `knowledge-schema.py`, 111 en `test_capabilities.py`, 267 en `test_knowledge_schema.py`).

**Marco de `knowledge-services` sin backends (T-09)**
- Código: 670 líneas (`knowledge-sync.py` 576 y `backends/__init__.py` 94).
- Lectura por backend en `knowledge-find.py:1377-1934`: 558 líneas.
- Test: unas 1.400 líneas. Es una suma de ficheros que medí por separado (`test_knowledge_sync` 800, `_replay` 108, `test_backends_init` 62, `test_manifest_publication` 110, `test_backend_verification` 124, más routing y derivative surface), no una medida única.
- Docs de la skill: 433 líneas.
- `outbox.py` (982 líneas y 918 de test) se queda: lo usan el journal, `doctor.py` y `knowledge-schema.py`.

**`training-data-services` (T-30 y T-31)**
- Total versionado: 18.992 líneas. Código 6.400 y test 11.808.
- Opción (a) retira casi todo; (b) retira unas 3.625 de código y 7.073 de test; (c) nada.
- Son medidas previas que T-30 debe confirmar.

## 4. Cómo resolví T-02 (herramienta `Skill`) para los tres runtimes

- Codex: el agente exportado no recibe `tools` y menciona la skill con `$custom-agents:X` (`docs/INTEROP.md:79`).
- OpenCode: el exportador fija `skill: allow` siempre (`scripts/export-interop.py:589`).
- Claude Code: `Skill` en `tools:` es opcional.
- Solución: el cuerpo de `implementer` y de `qa` da siempre la ruta `skills/<x>/SKILL.md` como vía que no depende de la herramienta (patrón que ya usa `nemesis`). Un test recorre `agents/*.md` y otro comprueba que los agentes generados de Codex y OpenCode conservan la ruta.
- `Skill` en `tools:` solo se añade si una prueba en sesión real de Claude Code la necesita.
- Alcance: el análisis lo daba solo para `implementer`; `qa` también declara una skill (`to-pdf`) sin `Skill`.

## 5. Hallazgos dejados fuera y evidencias que no se sostuvieron

Fuera del plan:
- 4.9 (statusline): opt-in, solo Claude Code, sin ganancia que lo justifique.
- 4.4 (módulo común `kit.py`): ADR-016 lo descartó para que las piezas viajen sueltas.
- 4.5 (partir `journal.py` y `doctor.py`): no reduce tokens ni errores.
- 2.10 (mover el paso Kwipu de `/setup`): absorbido por T-08.
- 3.1 a 3.3: descartados por las decisiones del usuario.
- 3.8: pasa a T-30 y T-31.

Evidencias con matiz (ninguna se rebatió por completo):
- 1.3: colisión de nombre solo en Claude Code; Codex ya antepone `custom-agents-` (`export-interop.py:559-572`).
- 2.9: 25 ocurrencias de «Alcance y activación», no 21.
- 4.1: 23 ficheros duplicados en un recuento rápido, 27 según el análisis.
- 4.3: la cabecera de `journal.py:260` declara la copia como «REPLICADO LITERAL … ADR-016», así que `copias.json` y el test de identidad la guardan; borrarla exige enmendar el ADR.
- 4.10: `install/install.mjs:464-470` es la detección de copia heredada de OpenCode, no código muerto.
- 4.11: hay 8 ficheros `tests/test_f4fix*.py` en `tests/`.
- 1.9: el timeout de `code-health.py` no lo reproduje.

## 6. Lo que NO pude verificar y huecos del plan

No verificado:
- No hay ejecución real de Codex ni de OpenCode: solo ficheros generados y suites.
- Que Codex honre `async` fuera del grupo de actividad.
- Que Codex ignore `.claude/skills/` (T-10) y que Claude Code no cargue `.claude/skills/` de un plugin instalado.
- Que OpenCode oculte una skill de su listado.
- Los ahorros de tokens son tamaños de fichero (caracteres/4), no consumo medido.
- 1.4, 1.6 y 1.7 salen del contrato de `tools:` y de la prosa, no de ejecución.
- La rama `docs/model-routing-discovery-2e32c1` existe (la comprobé), pero no leí su contenido; eso es T-30.
- No averigüé si hay transcripciones equivalentes en Codex y OpenCode; también es T-30.
- Si Claude Code o Codex aceptan varios plugins con `source` en subdirectorios (ya no hace falta).

Huecos del plan:
- Ubicaciones «a confirmar»: el nombre de `tests/test_copias_identidad.py` en T-25 y el de `test_knowledge_find.py` en T-27. También las referencias nuevas que crean T-15 y T-18. En el ledger final no marqué con una señal todas las que son provisionales.
- `Archivos` posiblemente incompletos:
  - Los de T-08 y T-09 están agrupados con llaves y globs y pueden dejar fuera ficheros que `scope-check.py` marcará como gap. Hay unos 20 ficheros más con menciones de Kwipu o Graphiti que no listé uno a uno.
  - T-10 no enumera todo lo que mira `plugin-dev`.
  - Los `Archivos` de las tareas de tokens de la fase 3 son orientativos.
- Para caber en 60 KB recorté el ledger: sin línea de Supervisión por tarea (queda en el resumen por fase), un criterio de aceptación por tarea salvo en T-08, T-09, T-30 y T-31, descripciones más cortas y Notas solo en T-08. En algunas tareas se pierde matiz del primer borrador.
- Supuestos: reparto 80/20 entrada/salida de tokens, cambio EUR/USD 0,92 fijo, horas IA aproximadas.

## 7. Decisiones pendientes del usuario, con recomendación

- T-09, marco de `knowledge-services`: (a) conservarlo dormido con un adaptador de prueba, o (b) retirarlo. Recomiendo (b): mantenerlo deja unas 2.600 líneas de código y test sin consumidor, y la iniciativa de Kairos lo recupera de git en unas horas.
- T-31, exportación a posteriori: depende del veredicto de T-30. Recomiendo (a), sustituir y retirar la captura en vivo. Si T-30 dice (b), se reduce; si dice (c), se cancela.
- T-32, modos de implementación: recomiendo fusionar solo `lite` con `subagentes` y aplazar el modo único (unas 4 h frente a unas 6 h, y no se pierde el lote paralelo).
- T-33, retro fuera de la vía rápida: recomiendo sí; sigue obligatoria en el flujo completo.
- T-34, fusiones y `/roadmap-metrics`: recomiendo sí a las tres piezas.

Ya decididas por el usuario el 2026-11-10: Kwipu y Graphiti se retiran ya, la partición se descarta, las cuatro skills de contenido se conservan, `training-data-services` se queda y se congela, el conocimiento no se entrena, `dev-cycle-dataset` queda «superada por evaluación» (T-31 la cierra) y los tres runtimes son requisito.

Acciones que solo puede hacer el usuario (en el plan, aparte del ledger): merge del PR #32, release como versión mayor, copia de `ci.yml.MANUAL-COPY`, checklist M-01, destino de ramas y worktrees, excepción de la constitución y abrir la iniciativa de Kairos.

---

# Informe: cierre de huecos del plan `2026-11-10-plugin-audit-2`

Ficheros (sin comitear, solo estos dos): `improvement-plan.md` (27 KB) y `tasks.md` (79.967 bytes, bajo el tope de 80 KB). `ledger-lint.py`: 0 incoherencias y 0 avisos. No quedan `{{`. No se ha tocado código ni se ha comitado nada.

Resultado: 37 tareas en 6 fases (antes 36). Se divide T-08 y se renumera desde ahí.

## 1. Tareas que cambiaron y cómo

- **T-08 (antes T-08 completa):** ahora es solo código, tests y configuración de la retirada. `Archivos` pasó de unos 30 a una lista completa y verificada con `git grep` (35 ficheros a borrar, 1 a dividir y ≈45 a editar). Esfuerzo 14 h (antes 12 h).
- **T-09 (nueva):** documentación, ejemplos, `/setup`, `/doctor`, evals y CHANGELOG de la retirada: 38 docs y READMEs más piezas. 7 h. Se parte T-08 porque el alcance real era ≈21 h (>16 h).
- **T-10 (marco de `knowledge-services`, antes T-09):** `Archivos` reconstruido leyendo los usos reales de `--intent` (ver apartado 3). 6 h (antes 5 h).
- **T-11 (`plugin-dev`, antes T-10):** `Archivos` completo (33 ficheros con `plugin-dev`) y las tres suposiciones verificadas o convertidas en un paso 0 manual (apartado 3). 5 h (antes 4 h).
- **T-02:** se añade el paso manual M-A (sesión real de Claude Code y lectura por ruta en Codex y OpenCode).
- **T-12 a T-22 (tokens):** cada una gana un criterio con cifra objetivo medible. Ejemplos: T-19 `implementer.md` < 15 KB; T-16 `dev-cycle.md` ≤ 20 KB; T-14 aviso del ledger ≤ 60.000 bytes; T-18 `capability-check.md` ≤ 2 KB. T-20 añade la prueba de runtime y el paso manual M-C.
- **T-23 (CI):** se retira la ubicación provisional. No hay requirements: la CI hace `pip install pytest pyyaml` en `ci.yml.MANUAL-COPY:30-31` y `.github/workflows/ci.yml` es idéntico (`diff`). Ahí se añade `pytest-xdist`.
- **T-24 (hooks, `async`):** `Archivos` real, criterio de latencia medible con `tests/test_bench_hooks.py` y el paso manual M-D.
- **T-25 (alias shell):** CORREGIDA de alcance. Solo 4 shells son alias de Python (`hooks/run-hook.mjs:331-345`): `session-context.sh` 330 líneas, `session-journal.sh` 86, `subagent-progress.sh` 41 y `user-prompt-capture.sh` 54, en total 511 líneas. Los demás se quedan (ver apartado 3). Esfuerzo 5 h (antes 7 h). Añade el paso manual M-E.
- **T-26 (copias):** el test provisional `tests/test_copias_identidad.py` pasa al real `tests/test_copias_declaradas.py`.
- **T-27 (instalador):** solo 4.10; el 4.12 sale de la tarea porque no se sostiene (apartado 3). 2,5 h (antes 3 h). Añade el paso manual M-F.
- **T-28 (FTS5) y T-29 (`serve_panel`):** `Archivos` con las listas reales de `git grep` (11 y 28 ficheros) en vez de supuestos.
- **T-30 (renombrar tests):** se quita `docs/agents/CONTRACTS.md` (no cita nombres de test) y se añade `tests/test_hook_network_egress.py`, que tiene 28 referencias a `test_f4fix`.
- **T-31 a T-37:** solo cambian de número, salvo T-36 y T-37, cuyas dependencias se actualizan.
- Criterios de aceptación: restaurado el segundo criterio donde el recorte anterior dejó ambigüedad (T-02, T-06, T-11, T-13, T-16 a T-19, T-23 a T-25, T-27 y T-28).

## 2. Clasificación de los 137 ficheros (`git grep -il -E "graphiti|kwipu"`, fuera de roadmap, CHANGELOG, `docs/knowledge/` e `interop/`)

| Clase | Ficheros |
|---|---|
| Se borran | 37 (34 de `skills/knowledge-services/`, `tests/test_graphiti_model.py` y las 2 guías `docs/{,en/}knowledge-services-graphiti.md`) |
| Se dividen | 1 (`tests/test_graphiti_security.py`) |
| Se editan | 96 (docs y READMEs 38, tests 31, `agent-kits/` 10, skills ajenas 6, skill `knowledge-services` 4, commands y agents 3, evals 3, `.gitignore` 1) |
| PDF generados | 2 (`output/pdf/*.pdf`: no se editan a mano; acción del usuario) |
| Config local del usuario | 1 (`.claude/knowledge-services/taxonomy.json`: sale de T-08 y de sus criterios; acción del usuario) |
| **Total** | **137** |

**Reparto entre tareas.** T-08 se queda con código, tests y configuración. T-09 se queda con las guías, `kwipu-adapter.md`, los docs, los ejemplos, las piezas y los evals.

**Medido en la skill:**
- Hay 49 ficheros versionados; se borran 39 y quedan 10.
- Los 39 son 18.287 líneas: código 7.351, test 8.494, fixtures 1.963 y docs 479.
- Los 10 que quedan son el marco: código 670, test 1.212 y docs 469.

**Menciones que son solo comentario o nombre.** `outbox.py` tiene una sola mención, un comentario de cabecera; `agent-kits/shared/README.md` son filas de prosa. El detalle por fichero está en `Archivos` de T-08 y T-09.

## 3. Resultado de las verificaciones

### Punto 1 (trampa descubierta en T-08)
`tests/test_graphiti_security.py` (2.953 líneas) NO se puede borrar entero. Es el escáner «ningún hook hace red» del plugin (recorrido transitivo de lo que cita `hooks/hooks.json`, mutantes, actividad). Contiene ≈800 líneas de tests genéricos y ≈1.435 de helpers que cargan `tests/test_hook_launcher_security.py` (`:27,47,55,66`) y `tests/hook-budget.test.mjs:4`.

Los tests Graphiti-específicos suman ≈718 líneas. Esa clasificación es por nombre de test y se revisa al ejecutar. T-08 lo renombra `tests/test_hook_network_egress.py` y retira solo esas ≈718. El borrado real de tests es ≈ 8.494 + 418 + 718 y no los 11,8 K estimados antes.

### Punto 3 (`--intent` y fragmentos de agentes)
- `--intent` casa en 34 ficheros: 24 son uso real y 10 son otra cosa. Los 10 son `--intento` (`phase3-jira.md`, `ledger-lint.py`, `task-brief.py`, `jira-sync/**`, `test_review_jira_owner.py`) y `--intent-to-add` (`docs/{,en/}COMMIT-SELECTION.md` y su prueba).
- Los 24 reales están en T-08 (adaptadores y tests), T-09 (docs) y T-10 (router).
- **Fragmentos de agentes:**
  - `knowledge-check-governed.md` no menciona router, intent ni backends: no cambia con (a) ni con (b).
  - `knowledge-check.md:8,22` dice «fallo de backend» y «backends declarados»: con (b) se reescribe; con (a) no.
  - `phase4-knowledge-gate.md:25-27` menciona Kwipu, Graphiti y `knowledge-sync.py`: lo edita T-09, y con (b) se retira además el párrafo del sincronizador.
  - `agents/knowledge-curator.md:45-48,167-171` repite «filtrando por `routing.graphiti`»: lo edita T-09.
- **Marco.** Medido: 670 líneas de código, 1.212 de test, 469 de docs y `knowledge-find.py:1377-1934` (558 líneas de lectura por `--intent`). `outbox.py` (982 líneas y 918 de test) no es del marco: lo usan el journal, `doctor.py` y `knowledge-schema.py`. Recomendación sin cambio: (b).

### Punto 4 (T-11, `plugin-dev`)
- **(i) Payload de los instaladores:** verificado.
  - No incluye `.claude/`: `PAYLOAD_CLAUDE` y `PAYLOAD_COMUN` en `install/providers.mjs:28-34`.
  - Tampoco el `files` de `package.json`.
  - `scripts/export-skills.py:63,357` y `tests/test_export_skills.py:252` ya excluyen `plugin-dev` del paquete portable.
  - `scripts/export-interop.py` solo cita `.claude/` en rutas de búsqueda.
- **(iii) Versionado de `.claude/skills/plugin-dev/`:** verificado.
  - `.gitignore` no ignora `.claude/skills/` (`git check-ignore` sin salida).
  - `.claude/` ya tiene ficheros versionados (`rates.json`, `jira.json`, `confluence.json`, `knowledge-services/taxonomy.json`).
- **(ii) Carga de skills de proyecto por runtime:** parcialmente verificado.
  - `docs/INTEROP.md:90` dice que OpenCode lee `.opencode/skills/` y también `.claude/skills/`.
  - Nada en el repo dice cómo ve Codex una skill de proyecto.
  - Tampoco se puede verificar que Claude Code no cargue `.claude/skills/` de un plugin instalado.
  - Queda como paso 0 manual M-B.
- **Qué referencia `plugin-dev`:** `git grep -l plugin-dev` da 33 ficheros fuera de la propia skill y están todos en `Archivos`. Dos puntos extra: `evals/check.py` enumera `skills/*/SKILL.md`, y un test cita `skills/plugin-dev/references/claude-code-contracts.md` (`tests/test_session_context.py:315`).

### Punto 6 (supuestos de runtimes)
- **T-20, índice de arranque:**
  - Ya cubierto: `tests/test_session_context.py:86` y `:134` parametrizan `claude`, `codex` y `opencode`, y `agent-kits/shared/test_skill_index.py:85` hace lo mismo.
  - T-20 añade la aserción por runtime; que el arranque real de Codex y OpenCode lo muestre es el manual M-C.
- **T-24, `async` en Codex:**
  - `hooks/hooks.json:34,46` y `interop/codex/hooks.json:103` solo marcan `async` en la actividad.
  - Ningún test de `test_export_interop.py` ni de los `.test.mjs` de Codex menciona `async`.
  - Nada demuestra que Codex lo honre en `UserPromptSubmit`, así que no se propaga sin M-D.
  - OpenCode tiene su catálogo de bindings (`hooks/opencode-plugin.js:28-34`) y su suite.
- **T-25, alias `*.sh`:**
  - Cubiertos por `tests/hook-runtime.test.mjs` y `tests/opencode-plugin.test.mjs:125,179,461`.
  - Que una instalación ya hecha siga disparando tras actualizar es el manual M-E.

### Hallazgos del análisis que no se sostienen o cambian de alcance
- **4.2:** solo 4 de las 9 shells son alias; hay que conservar el resto.
  - `mark-docs-pending.sh` (51 líneas) pasa por `runtime-entry.sh` y está registrado en `hooks/hooks.json`.
  - `implementer-guardrail.sh` y `architect-guardrail.sh` son guardias de copias locales.
  - `ledger-lint-warn.sh` y `progress-line.sh` están en el conjunto `known` del lanzador (`run-hook.mjs:130-132`).
- **4.12:** no se sostiene, por el mismo motivo: `runtime-entry.sh` también ejecuta `mark-docs-pending.sh`.
- **4.10:** `install.mjs:464-470` es la detección de copia heredada de OpenCode, no código muerto.

## 4. Presupuestos: nuevos frente a los anteriores

Base: 50 €/h, supervisión 25 % de las horas IA y tokens a 4/20 USD por millón. El margen es +20 %.

| Fase | Antes (h / tokens) | Ahora (h / tokens) |
|---|---|---|
| 1 Defectos | 15 / 1.090k | 15 / 1.090k |
| 2 Retirada decidida | 21 / 1.350k (3 tareas) | 32 / 2.100k (4 tareas) |
| 3 Tokens | 30 / 2.260k | 30 / 2.260k |
| 4 Simplificación | 37 / 2.670k | 34,5 / 2.470k |
| 5 Alcance y entrenamiento | 25 / 1.750k | 25 / 1.750k |
| 6 Higiene | 7 / 500k | 7 / 500k |
| **Total** | **135 h / 9.620k** | **143,5 h / 10.170k** |

| | Antes | Ahora |
|---|---|---|
| € de horas (base) | 6.750 | 7.175 |
| € con margen del 20 % | 8.100 | 8.610 |
| H. humanas con margen | 162 | 172,2 |
| IA + supervisión (base) | 43,1 h | 45,75 h |
| € de tokens (aprox.) | 64 | 67 |
| Sin la fase 5 (la que espera decisiones) | 110 h, 5.500 € | 118,5 h, 5.925 € (7.110 € con margen) |

- La fase 2 sube por el alcance real de la retirada (137 ficheros y la división del test de seguridad), por T-10 con su lista corregida y por T-11 con 33 ficheros.
- La fase 4 baja porque T-25 cae a 5 h (511 líneas y no 860) y T-27 a 2,5 h (sin 4.12).
- El ahorro de productividad es 68,1 % (multiplicador 3,1×) con FTE 0,61 base y 0,73 con margen.
- Los criterios de salida, riesgos, decisiones y acciones del usuario están actualizados en el plan. Nuevo riesgo registrado: borrar un invariante de seguridad por un nombre engañoso (`test_graphiti_security.py`).

## 5. Huecos que SIGUEN abiertos (no se pueden cerrar desde el repo)

- Cómo cargan Codex, OpenCode y Claude Code una skill de proyecto, y que Claude Code no cargue `.claude/skills/` de un plugin instalado (M-B).
- Que Codex honre `async` en el hook de `UserPromptSubmit` (M-D).
- Que el arranque real de Codex y OpenCode muestre el índice completo y el de Claude solo la cabecera (M-C).
- Que una instalación previa de Codex u OpenCode se actualice y los hooks sigan disparando tras T-25 (M-E).
- Instalación y desinstalación reales con OpenCode y Codex tras T-27 (M-F).
- Comportamiento de un agente sin `Skill` en sesión real y lectura por ruta en Codex y OpenCode (M-A).
- Las ≈718 líneas de `test_graphiti_security.py` salen de una clasificación por nombre de test, y T-08 debe revisarlas al ejecutar. La medida de líneas es aproximada.
- `bridge_to_kwipu` es una clave de configuración de `training-data-services`; T-08 no la toca (skill congelada) y la retira T-32 si se aprueba. No verifiqué si algún test de esa skill la exige.
- No medí cuántas líneas exactas salen de `knowledge-schema.py` ni de los 31 tests editados; solo tengo el conteo de menciones.
- El `Archivos` de T-25 lista ficheros que mencionan los shells (muchos citan los que se quedan). Se indica «solo las líneas que citan los cuatro alias», pero la lista exacta de líneas se fija al ejecutar.
- `evals/check.py`: no leí cómo trata un caso de evals sin pieza; T-11 lo comprueba en su verificación (se mueve o elimina el caso).
- Los PDF del paquete (`output/pdf/*.pdf`) conservan menciones hasta que el usuario los regenere.
- La migración de `.claude/knowledge-services/taxonomy.json` (cambios locales del usuario) queda como acción del usuario.
- Hay un fichero `planning-notes.md` en la carpeta de la iniciativa que no es mío; no lo he tocado.

informe escrito

---

# Informe: decisiones del 2026-11-10 aplicadas al plan `2026-11-10-plugin-audit-2`

Ficheros (sin comitear, solo estos dos): `improvement-plan.md` (30 KB) y `tasks.md` (81.872 bytes = 79,95 KiB; el «KB» del repo es 1024 bytes, como en `ledger-lint.py`, así que cabe en el tope de 80 KB). `ledger-lint.py`: 0 incoherencias y 0 avisos. No queda ninguna línea `Decisión requerida:` ni `{{`. No se ha tocado código ni se ha comitado nada.

Estado: el plan sigue en `borrador` y su ejecución NO está autorizada. Quitado el bloqueo «por decisión» de la fase 5.

## 1. Qué cambió en cada tarea

- **T-10 (marco de `knowledge-services`):** decidido (b), el marco se retira y Kairos lo recupera del commit anotado en T-08. Se quita el criterio de la opción (a), el texto «conservar o retirar» y la nota «con (a) no cambia». Título nuevo: «Retirar el marco de knowledge-services sin backends». Esfuerzo sin cambio (6 h).
- **T-32 (exportación a posteriori del entrenamiento):** decidido (a) **condicionada** al veredicto de T-31, redactado como única puerta.
  - Si T-31 concluye (a) y no halla datos irreconstruibles, se ejecuta sin volver a preguntar.
  - Si concluye (b) o (c), o halla datos que no se pueden reconstruir después, se detiene y vuelve al usuario con la evidencia.
  - Primer criterio de aceptación nuevo: la puerta. Se eliminan las frases «si T-31 dice (b) se reduce / si dice (c) se cancela».
- **T-33 (modos):** retitulada «Fusionar los modos lite y subagentes». Se quita la opción del modo único. Alcance reescrito: `lite` pasa a preajuste de `subagentes` (secuencial, techo de brief, writer obligatorio), sin prosa propia en `dev-cycle.md`, y `execution-profile.py` sigue aceptando `perfil: lite` como alias. **Sube de 4 h a 5 h** (ver incoherencia 2). `Archivos` verificados con `git grep -w lite`: 25 ficheros más `tests/test_lite_profile.py` y `tests/test_native_guardrail_dispatch.py`.
- **T-34 (retro):** decidido que sí. Opcional en la vía rápida (se ofrece si el cambio superó la estimación), obligatoria en el flujo completo. Sin cambio de alcance.
- **T-35 (fusiones):** decididas las tres. Se añade la coherencia con T-03 (ver incoherencia 3). Sin cambio de esfuerzo (6 h).
- **T-36 (cierres):** nueva rama para `dev-cycle-dataset`. La decisión «superada por evaluación» es incondicional. Si T-32 se ejecuta, la cierra T-32; si no, la cierra T-36. Se añade su carpeta a `Archivos` de T-36.
- **Todas las líneas `Decisión requerida`:** sustituidas por «Decidido por el usuario el 2026-11-10: …» en T-10, T-32, T-33, T-34 y T-35.
- **Fase 2:** se quita «salvo T-10»; ahora está toda decidida.
- **Fase 5:** sin bloqueo por decisión; solo T-32 queda condicionada a T-31.
- **Cabecera del ledger:** «Autorización: NO autorizada» y «no queda ninguna decisión pendiente; la única puerta es la condición de T-32».
- **Aprovechado para restaurar contenido recortado:**
  - Se quitan los recortes que habían dejado cortadas las descripciones de 11 tareas, y los criterios y verificaciones que habían perdido el elemento intermedio.
  - Se corrigen líneas `Runtimes` descuadradas (ver incoherencia 1).

## 2. Presupuestos finales (50 €/h, supervisión 25 % de la IA, margen +20 %)

| Fase | Tareas | H. humanas | H. IA | Superv. | IA+sup. | Tokens | € horas | H. con margen | € con margen |
|---|---|---|---|---|---|---|---|---|---|
| 1. Defectos | 7 | 15 | 4,0 | 1,00 | 5,00 | 1.090k | 750 | 18 | 900 |
| 2. Retirada decidida | 4 | 32 | 7,9 | 1,98 | 9,88 | 2.100k | 1.600 | 38,4 | 1.920 |
| 3. Tokens | 11 | 30 | 8,2 | 2,05 | 10,25 | 2.260k | 1.500 | 36 | 1.800 |
| 4. Simplificación | 8 | 34,5 | 8,5 | 2,13 | 10,63 | 2.470k | 1.725 | 41,4 | 2.070 |
| 5. Alcance y entrenamiento | 5 | 26 | 6,5 | 1,63 | 8,13 | 1.800k | 1.300 | 31,2 | 1.560 |
| 6. Higiene | 2 | 7 | 1,7 | 0,43 | 2,13 | 500k | 350 | 8,4 | 420 |
| **TOTAL** | **37** | **144,5** | **36,8** | **9,20** | **46,00** | **10.220k** | **7.225** | **173,4** | **8.670** |

- **Respecto al borrador anterior** (143,5 h / 10.170k / 7.175 € / 8.610 € con margen): +1 h, +50k tokens y +50 €, todo de T-33.
- **Tokens:** unos 68 € en total.
- **Productividad:** 98,5 h ahorradas, 68,2 %, multiplicador 3,1×, FTE 0,62 (0,74 con margen).
- **Sin la fase 5:** 118,5 h, 8.420k tokens, 5.925 € (7.110 € con margen). T-31 (3 h, sin decisión) está en esa fase.

## 3. Lista final de acciones del usuario (ya no hay decisiones, solo acciones)

**Decisiones y gestión**
1. Revisar y hacer merge del PR #32 (este plan puede ejecutarse en una rama nueva si sigue abierto).
2. **Autorizar la ejecución del plan**: hoy está en `borrador` y no autorizado.
3. **Release como versión mayor** (`python3 scripts/release.py X.0.0`, `--dry-run` antes): la retirada de Kwipu y Graphiti (T-08, T-09), del marco (T-10) y, si T-31 lo permite, de la captura en vivo (T-32) es un cambio rompedor. La lanza el usuario.
4. Copiar `ci.yml.MANUAL-COPY` a `.github/workflows/ci.yml` tras T-23 (y tras T-08 y T-10, que cambian las rutas de test); hoy los dos ficheros son idénticos.
5. Abrir la iniciativa de Kairos con `/pm-cycle` cuando T-10 esté hecho (recupera el marco del commit anotado en T-08).
6. Si T-31 concluye (b) o (c), o halla datos irreconstruibles, decidir con su evidencia qué hacer con T-32.
7. **Migrar su `.claude/knowledge-services/taxonomy.json` local** (cambios sin comitear): quitar los backends `kwipu` y `graphiti` y sus claves `routing`. T-08 no lo toca. El pendiente de reindexar Kwipu deja de tener sentido.
8. **Regenerar los dos PDF** de `output/pdf/` (mencionan Kwipu y Graphiti; no se editan a mano y viajan en el paquete npm).
9. Decidir el destino de las ramas `fix/graphiti-add-memory-uuid` (cerrar o cancelar por retirada), `model-routing-lab` (activa; T-31 la lee solo con `git show`), `graphiti-uuid-fix`, `sdd-proporcional` y `project-dashboard`, y de los 36 worktrees registrados.
10. Decidir la excepción «evidenciado (medida)» de la constitución.
11. Ejecutar o anotar como no verificable la checklist manual M-01 del instalador, y participar en las retros de T-36.

**Verificaciones manuales** (cada una es un paso `lectura (manual…)` de su tarea):

| Id | Tarea | Qué comprobar en sesión real |
|---|---|---|
| M-A | T-02 | En Claude Code, si un agente con `tools:` sin `Skill` puede invocar una skill; en Codex y OpenCode, que el agente sigue la skill leyendo su `SKILL.md` por la ruta |
| M-B | T-11 | `plugin-dev` visible en este repo y no en un proyecto con el plugin instalado (Claude Code); OpenCode la lee de `.claude/skills/`; dónde ve Codex las skills de proyecto |
| M-C | T-20 | En Codex y OpenCode reales el arranque muestra el índice completo; en Claude solo la cabecera |
| M-D | T-24 | En Codex, el hook de `UserPromptSubmit` marcado `async` captura el prompt sin bloquear el turno |
| M-E | T-25 | Una instalación previa de Codex u OpenCode se actualiza y los hooks siguen disparando con los mismos nombres |
| M-F | T-27 | Instalar y desinstalar con OpenCode y Codex en un directorio temporal da el mismo manifiesto que antes |

**Orden recomendado de ejecución** (sección nueva del plan):
1. T-23 (CI), opcional y primero.
2. Fase 1.
3. Fase 2: T-08 → T-09 → T-10, y T-11 en paralelo.
4. T-31 en cuanto acabe la fase 2.
5. Fase 3.
6. Fase 4: T-24 → T-25 → T-27, T-29, T-26 → T-30, y T-28 libre.
7. T-32 solo si T-31 lo permite; T-33, T-34 y T-35 tras sus dependencias.
8. Fase 6.

## 4. Incoherencias encontradas al aplicar las decisiones

1. **Líneas `Runtimes` descuadradas en el ledger anterior.**
   - T-30 (renombrar tests) decía algo sobre Kairos y HTTP.
   - T-33 (modos) y T-34 (retro) llevaban el texto de la skill `plugin-dev` y de las fusiones.
   - Seis tareas tenían la línea cortada en `;` (T-02, T-03, T-11, T-12, T-19 y T-35).
   - Todas reescritas.
2. **T-33 era más grande de lo presupuestado.** `lite` no es una prosa suelta: es un perfil de `dev.json` con `execution-profile.py`, `tests/test_lite_profile.py`, la validación de `doctor.py:1356` y menciones en 25 ficheros de docs, skills y agentes. Pasa a 5 h, y de ahí el +1 h del presupuesto.
3. **T-03 y T-35 (confluence-pull).**
   - **No se hace innecesaria una a la otra, y no se unen.** T-03 retira solo el COMANDO `/confluence-pull` y añade el guardarraíl del linter contra colisiones comando/skill. T-35 retira después la SKILL y su caso de evals, y `confluence-publish` hereda sus disparadores.
   - T-03 va en la fase 1 e independiente de que se fusione o no. La dependencia T-35 → T-03 ya existía y se conserva, para no borrar dos veces.
   - Consecuencia declarada en T-35 y en el plan: al terminar T-35 deja de existir la invocación `/confluence-pull` (en Claude, Codex y OpenCode).
4. **`dev-cycle-dataset`.** La decisión «superada por evaluación» es incondicional, pero T-32 solo la cerraba si se ejecuta. Ahora, si T-32 se devuelve al usuario, la cierra T-36.
5. **Tope del ledger.** Hubo que restaurar descripciones recortadas (11 tareas) y subió de 79.949 a 81.872 bytes. El ledger sigue bajo el tope de 80 KiB, pero con poco margen (48 bytes). Cuando se archive la fase 2 (la mayor) tendrá holgura.
6. **Descripciones de tareas ya cerradas por decisión.** El plan seguía diciendo «recomendada: (b)» en el apartado de la retirada medida; ahora dice «decidido (b)».
7. **Un plan, dos opciones de modo único.** El análisis (3.5) hablaba de un único modo «brief por tarea». Queda como «fuera de alcance» por falta de datos de uso del lote paralelo, y T-33 no promete ahorro de −4 KB, que era del modo único.

## 5. Pendiente que no se puede cerrar desde el repo

Sin cambios respecto al informe de huecos: las seis verificaciones manuales (M-A…M-F), la clasificación por nombre de test de las ≈718 líneas de `test_graphiti_security.py` que se revisa al ejecutar T-08, y el comportamiento de `evals/check.py` ante un caso sin pieza, que comprueba T-11.

Un dato nuevo que no he verificado: `tests/test_lite_profile.py` tiene 36 menciones de `lite`. No he comprobado si todos sus casos cubren solo el perfil o también la ruta de `subagentes`. T-33 lo revisa al escribir el test rojo `-k preajuste`.

informe escrito
