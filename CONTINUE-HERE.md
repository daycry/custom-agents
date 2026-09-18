# CONTINUE-HERE

> **2026-09-18 — EN CURSO: `/dev-cycle knowledge-services` (flujo completo, Fase 3) en la rama `feature/knowledge-services`**
> (ramificada de `feature/session-end-durable-capture`, que está cerrada con retro pero SIN PR/merge: el PR de esa
> iniciativa sigue pendiente; `outbox.py` solo existe en estas ramas). Objetivo del usuario (`/goal`): que el plugin,
> con Kwipu y Graphiti activados en `.claude/knowledge-services/taxonomy.json`, se integre con el stack local
> `dockers/knowledge-graphs` (bridge `127.0.0.1:8765`, Graphiti MCP `127.0.0.1:8001/mcp`) y el flujo sea correcto.
> Orden: knowledge-services completo → graphiti-memory (depende de knowledge-services `completado`).
>
> Estado del ledger `docs/roadmap/2026-09-15-knowledge-services/tasks.md`: T-01, T-02, T-03, T-13 `completado`
> (Fase 1 + registro de capacidades). **Revisión de dos lentes — intento 1** escrita (22 gaps: 1 Critical =
> colisión de basename `test_knowledge_index.py` que apaga la colección del comando de CI; 10 Important; 11 Minor;
> #19 corregido por el orquestador en `design.md`, #21 deuda aceptada). Ronda `T-XX-fix2` hecha (03071f9..72f64af).
> **Intento 2** (cf23f02): 22/22 cerrados + 12 nuevos (#23–#34; #23 corregido en e66cc32). **Ronda `T-XX-fix3`
> hecha** (bf97acd..47314a9: 11/11 cerrados). **Intento 3** (cb92ea0): 5 nuevos (#35–#39) → decisión del orquestador
> (autónomo, sin Critical, convergente): ronda `fix4` (55499be, c3e7aeb) + verificación dirigida → **bucle CERRADO**
> (ec75d4c; 39 gaps en total, 0 pendientes, #21 deuda). **Fase 2 (T-04 knowledge-curator, T-05 documenter propone,
> T-06 Fase 4-bis) HECHA** (5d03c16, db00d0f, 230a876). **Revisión Fase 2 intento 1** (4539ab2): 19 gaps (#40–#58;
> 2 Critical: `MODOS` de `curator-gate.py` y lista negra por subcadena). Ronda fix1 hecha (cfacc18..e6ef4af).
> **Intento 2 Fase 2** (6dfcd42): 19/19 cerrados, 13 nuevos (#59–#71; 2 Important: acentos en la lista negra y
> **YAML de `ci.yml` inválido en la línea 54, preexistente en master, bloquea CI**). Ronda fix2 hecha (c36707d..df20d16,
> incl. `fix(ci)` 3b6ef8e). **Intento 3 Fase 2** (c3f8bff): 13/13 cerrados, 10 nuevos (#72–#81; 72–74 cerrados por el
> orquestador) → ronda `T-04-fix3` (3dbdd88) + verificación dirigida → **bucle Fase 2 CERRADO** (d20dfab; 42 gaps,
> 0 pendientes). Progreso 7/13. **Fase 3 (T-07 knowledge-sync + contrato, T-08 adaptador Kwipu + skill, T-09
> setup/doctor) HECHA** (00cb695, cc1fc26, cecb3ac; progreso 10/13). **Revisión Fase 3 intento 1 en curso** (lentes A+B+D;
> C no aplica). **Validación EN VIVO ya hecha por el orquestador** desde `%TEMP%\ks-live-demo` contra el bridge real:
> `health` = sano, `--dry-run`/apply escriben el export con frontmatter CA-17, `--check` detecta desfase contra
> `/graph/snapshot` y nombra el remedio. Hallazgo: una entrada de `approved/` SIN `category:` se omite en silencio
> (pasado a las lentes). **El cierre físico (activar `generated_knowledge` en `projects.yaml`, exportar a
> `kwipu-data/generated/projects/<id>/`, `python -m source_manager.build_view --config kwipu/config/projects.yaml
> --output kwipu/runtime/knowledge-view-v2`, `docker compose restart kwipu kwipu-bridge kwipu-mcp`) lo DENEGÓ el
> clasificador de permisos (recurso compartido): lo ejecuta el usuario con `!`.** **Revisión Fase 3 intento 1** (87a9fef,
> lentes A+B+D): 23 gaps (#82–#104; 1 Critical = `apply` no atómico; 16 Important incl. `summary` sin implementar,
> `category` omitida en silencio, `/doctor` con red, outbox reclama envelope ajeno, 3 de seguridad: `type` traversal,
> `id` con `../`, `health.url` sin restricción de host). Ronda fix1 hecha (217875c..c27c969; T-02-fix6/T-04-fix4 los
> comiteó el orquestador). **Intento 2 Fase 3** (86b5838): 21/23 cerrados, 2 parciales (#82, #85) + 17 nuevos (#109–#125;
> Critical #109 = `--rebuild` no-op tras el fix por hash). El orquestador FIJÓ el diseño de publicación por intercambio de
> directorio (staging hermano + dos renames) en el ledger. Ronda fix2 hecha (02b9c57..36504ff). **Intento 3 Fase 3**
> (21f5f5c + anexo D 9c95f45): 17/19 cerrados; **3 Critical NUEVOS en los caminos de fallo del swap de directorio**
> (#126 rollback pierde la publicación, #127 `apply` borra todo lo ajeno en `export_dir`, incl. `export_dir: docs`,
> #128 outbox atascada permanente) + 3 Important + 8 Minor (#129–#139). **Decisión del orquestador (excede el bucle;
> revocable en el PR):** SUSTITUIR el diseño por «publicación por fichero con diario `manifest.pending.json`, sin mover
> ni borrar nada ajeno» + drenaje de la outbox; ronda fix3 hecha (656bfd8, 8385cf8, 3694629, 4b43f48) y **verificada por el
> orquestador con los probes de A/B/D → bucle Fase 3 CERRADO** (deuda Minor #140: cola crece durante el backoff). Progreso
> 10/13. **Fase 4 (T-10, T-11, T-12) despachada al `implementer`** (2026-09-19). Después: revisión de dos lentes de la Fase 4 → qa sin UI →
> documenter → Fase 4-bis → cierre (changelog-sync, /retro, retro-gate) → push + PR (T-04 curator, T-05 documenter, T-06 Fase 4-bis) → Fase 3 (T-07 sync +
> contrato, T-08 adaptador Kwipu, T-09 setup/doctor) → Fase 4 (T-10, T-11, T-12) → qa sin UI → documenter → cierre
> (changelog-sync, /retro + retro-gate) → graphiti-memory.
>
> Fixtures reales del stack grabadas el 2026-09-18 para T-08 y graphiti T-04 (health, snapshot, query, MCP
> initialize/tools-list/get_status): `C:\Users\46066917X\AppData\Local\Temp\ks-fixtures\` (regrábalas con
> `curl` si falta la carpeta; Docker debe estar levantado). Enmiendas 2026-09-18 en ambas specs (commit `c6aced3`).
> Linter: 1 ❌ PREEXISTENTE en `docs/knowledge/lessons/LES-016-*.md:5` (YAML del campo `estado`) que bloqueará
> `release.py`: arreglar antes de publicar (entrecomillar el valor). `.claude/dev.json` está sin versionar
> (`tdd: true`). Validación en vivo contra Kwipu: hacerla al cerrar T-08 (activar `generated_knowledge` en
> `projects.yaml` del stack + `build_view` + reinicio es del usuario/stack, no del plugin).
>
> **Encargos del usuario (2026-09-18, tras el goal), en este orden al terminar el ciclo:** (1) `git push` de la
> rama y **PR a master** (la rama `feature/session-end-durable-capture` viaja dentro: 49 commits sin PR); (2) con
> master estable, **repasar TODOS los planes de `docs/roadmap/`** en busca de tareas pendientes (`brief-budget`
> 0/6, `plugin-refactor` 18/22 con T-15 en-progreso, `project-specialization` 3/22, `graphiti-memory` 0/10,
> `training-data-services`, `dev-cycle-dataset`) y decidir/ejecutar; (3) **investigar por qué la revisión de dos
> lentes NO deja comentarios en las tareas de Jira**: el flujo se ejecuta entero pero el issue no recibe el
> comentario con el resultado de la verificación ni de los N intentos (pistas: `jira-flow.py` eventos `revision`/
> `gaps` con `--intento N` son «del orquestador» en `commands/dev-cycle.md` y a la vez «comentario FINAL en Jira,
> Paso 9» en la skill `adversarial-review`: posible hueco de dueño; comprobar en un proyecto consumidor con
> `.claude/jira.json` `enabled: true`, aquí no hay). Requisito transversal: todo debe funcionar en Claude Code,
> Codex y OpenCode.

> **2026-09-11 — `installer-registro-real` PUBLICADA en v1.20.0.** PR #2 mezclado en master (`0a10e7a`), release
> `e5774f8` + tag `v1.20.0` publicados, **CI de master en verde** en los dos commits (llevaba roja desde los merges
> de R2 y R3 del refactor, que integré sin comprobar el workflow: corregido en esta tanda).

> **PENDIENTE Y ES DEL USUARIO: la checklist M-01** de `docs/roadmap/2026-09-11-installer-registro-real/tasks.md`.
> Verificar en una máquina con Codex y OpenCode reales que las skills y los prompts aparecen y que el adaptador
> carga. Aquí no hay ninguno de los dos instalados.

> **EN CURSO (2026-09-11): R4 del refactor.** Rama `feature/plugin-refactor` realineada sobre master (v1.20.0).
> Tramo **R4a = T-11…T-14** en ejecución por el implementer; después revisión de dos lentes → commits → tramo
> R4b (T-15…T-19) → Fase 5 de cierre (T-20…T-22) → PR, merge y release, con verificación en contenedor Linux
> ANTES del push (lección de la tanda anterior). Matiz para T-11: el ruido de `scope-check` en ESTE repo ya lo
> quitó el `.gitignore`; lo que falta es la exclusión por defecto en el script, para proyectos consumidores.

> **En la cola detrás** (ninguno empezado): **R4 del refactor** (`docs/roadmap/2026-09-09-plugin-refactor/`,
> Fase 4, T-11…T-19 de encadenamiento E1–E11, más T-20…T-22 de cierre; el ledger sigue `en-progreso`) ·
> **brief-budget** (evaluada con go, ordenada después del refactor) · **F2/F3 de project-specialization**
> (`/specialize` y `.claude/pieces.json`, diseño aprobado en ADR-014).

> **Lección de esta sesión, para aplicarla antes del próximo push:** verificar en local comparando el CONJUNTO de
> rojos NO detecta lo que solo se rompe en CI. Cuatro fallos de hoy eran invisibles aquí (versión de Python 3.11
> frente a 3.13, permisos de `/root`, finales de línea, y `tests/test_lint_plugin.py` en modo script, que en Windows
> aborta en el caso del bit ejecutable antes de llegar a los casos nuevos). Lo que sí funcionó: un contenedor
> `python:3.11-slim` con git, `dos2unix` sobre los `.sh` y `chmod +x`, corriendo los mismos comandos de `ci.yml`.

---


Estado de trabajo en curso para retomar sin perder contexto (tras compactación o
un corte de sesión). Si estás leyendo esto al empezar una sesión: lee este
fichero ANTES de tocar nada. Bórralo (o vacíalo a "sin trabajo pendiente")
cuando la rama descrita aquí se publique y no quede nada abierto.

Última actualización: 2026-09-09 (tarde).

## Trabajo EN CURSO — tres iniciativas abiertas el 2026-09-09 (F1 INTEGRADA en `master`; rama actual `feature/plugin-refactor`)

**En `master`**: F1 de project-specialization (merge `919cca4`) y, desde el 2026-09-10, **el arreglo de `usage-meter` + los ciclos PM de
`brief-budget` y `plugin-refactor`** (merge `--no-ff` `8fee28a`, decisión del usuario; **sin push**). La rama de trabajo `feature/plugin-refactor`
apunta al merge (`reset --soft`, árbol intacto) y ahí seguirá el refactor. Los commits de la primera rama integrada: ciclo PM ·
diseño + `ADR-014` · plan + `ADR-015` · cifras re-medidas · `GOT-009` + análisis de `brief-budget` ·
análisis de `plugin-refactor` con línea base. **F1 está COMITEADA por tarea**: `a7f6bbe` T-02 · `204f333` T-03 · `74901c6` T-01 (+ ledger + los 4
ficheros reales de `interop/`). Árbol limpio salvo el journal del hook y el ruido previo.

### 1 · `docs/roadmap/2026-09-09-project-specialization/` — el tercer bucle (F1 INTEGRADA; F2/F3 pendientes)

| Artefacto | Estado |
|---|---|
| `spec.md` **aprobada** · `evaluation.md` **completado** (56,4 h · 2.837 €) · `design.md` **aprobado** (`O1`, `ADR-014`) · `improvement-plan.md` + `tasks.md` **en-progreso** | 3 fases, 22 tareas; solo **F1 (T-01…T-03)** tiene puerta abierta («go por tramos») |
| Revisión de dos lentes | intento 1: 6 Important + 6 Minor · intento 2: 1 Critical + 4 Important + 3 Minor · intento 3: todo cerrado salvo **B-3** (tope de la persona), que no convergía porque su causa no está en F1 |
| Decisión del usuario tras el 3.er intento | **opción A** (suelo `PERSONA_SUELO_CHARS = 1300` + aviso en runtime con causa por sección) — implementada y verificada: 0 personas en muñón, 12/22 briefs sobre el tope **con aviso** |
| Cierre de F1 | pasada acotada de la Lente B sobre A: 3 Important + 1 Minor (suelo sobre contenido sin ruta absoluta, aviso con atribución honesta, secciones medidas, tests con dientes: mutante `SUELO=400` → 2 failed) — corregidos y verificados por el orquestador. Suite completa 39 vs 52 en HEAD sin T-01: cero regresiones. **Mergeada en `master` `919cca4`** con nota manual en los dos CHANGELOG (`[Unreleased]`/`[Sin publicar]`), porque el ledger sigue `en-progreso` y `changelog-sync` no la derivará hasta el cierre. Plan/tasks `en-progreso`, spec `aprobada`: F2 (16 tareas) y F3 esperan su puerta |

Verificado y contrario a supuestos previos: `export-interop.py --root` = raíz del PLUGIN (falla contra un
`.claude/` de consumidor) → `C-11` es un modo `--project` (`ADR-015`). El único test rojo
(`test_ca08…memory_retrieval`) **falla igual en `HEAD` limpio** en esta máquina (`GOT-008`, ruta OneDrive).

### 2 · `docs/roadmap/2026-09-09-brief-budget/` — el presupuesto del brief está roto (PM EN CURSO)

Solo una de las siete secciones del brief tiene tope; `## Diseño` entra entero en las 22 tareas (3.510, el
35 % de `BRIEF_TOPE_CHARS = 10000`), los gaps (4.396 en T-01) y la verificación (2.285) no tienen tope.
`project-specialization` es la ÚNICA iniciativa con `design.md`, y el test del CA-08 recorre solo
`memory-retrieval`, sin diseño: nunca lo vio. Documentado en **`GOT-009`** (`propuesta`). `analysis.md`
con 5 opciones; `spec.md` **aprobada** y `evaluation.md` **completado** (26,4 h · ~1.340 €, go condicionado). **Go del usuario** el 2026-09-09; arranca DESPUÉS del refactor.

### 3 · `docs/roadmap/2026-09-09-plugin-refactor/` — refactor de TODO el plugin (GO; diseño O1 + `ADR-016`; **PLAN comiteado** `77cc78d`: 5 fases / 4 tramos / 22 tareas, 74 h base, `ADR-017` `test-plan: n/a`; **OK del plan** (usuario, 2026-09-10) con T-19/C-14 (E11) ACEPTADA; **R1 (F1: T-01…T-04) IMPLEMENTADA** (4/4; segunda línea base `code-health-baseline-2.json` con `--exclude-path interop`: 5,9 % duplicado, funciones largas 99 → 97; suite idéntica por test; `duracion_reloj` en `usage-meter`); **revisión R1 intento 1 CERRADA**: 5 Important + 10 Minor (brief byte a byte idéntico en 520 invocaciones y 40k casos de fuzz: el refactor de `task-brief` es limpio; los Important son el octavo TODO que también es prosa castellana → 8 → 0, `_parse_iso` naive que mata el `close`, `ENUMERACION_RE` que suprime TODO reales, `duracion_reloj` sin oráculo, y una subtarea «commit» marcada sin commit). Coste de la revisión MEDIDO: 9,30 €, 62 respuestas, `duracion_reloj` 37m. Corrección del intento 1 hecha (15 gaps, TODO en el repo 0, `_parse_iso` UTC, oráculo `37m`, línea base 2 con `exclude_path`). **Intento 2 verificado de forma determinista por el orquestador** (la Lente B cayó por la API): mutantes B-1/B-3/B-5/A-1 mueren; **residual Important R2-1**: `DETECTOR_PROPIO` por `realpath(__file__)` no excluye el `code-health.py` del árbol cuando el detector corre desde la caché del plugin (9 falsos positivos) y su test no mata al mutante → exclusión por FIRMA de contenido; R2-2 regla «≥ 2 marcadores» sin implementar; R2-3 límite castellano sin documentar. Intento 3 (determinista): 0 gaps, copia sobre el repo → `total: 0`, mutantes mueren. **TRAMO R1 CERRADO Y COMITEADO**: `ae32744` T-01/T-02 (code-health) · `7938187` T-03 (task-brief; CA-09 por commit) · `e194f22` T-04 (usage-meter) · ledger 4/22 con las tres trazas. Revisión medida: 9,30 € + 8,63 €. **R1 INTEGRADA en `master`** (merge `--no-ff` `ab97259`, sin push; la rama sigue en el merge). **R2 EN EJECUCIÓN** (`implementer`, F2: `knowledge-find` → `doctor` → `build_dashboard` → `lint_plugin`, 28 funciones largas → ≤ 14, salida byte a byte idéntica por script; las copias `celdas_md` entre los tres scripts NO se tocan — son R3/O1). **R2 IMPLEMENTADA** (4/4: funciones largas en los cuatro ficheros 28 → 9 = 0/1/4/4; suma de los 5 hotspots 11 ≤ 16, señal §8 cumplida; `knowledge-find --json`, `lint_plugin` y `doctor --json` idénticos a HEAD verificados por el orquestador; línea base 2: 97 → 78). **Revisión de dos lentes R2 CERRADA en el intento 1** (lentes A+B vivas, 12,16 EUR medidos): 0 Critical, 0 Important, 3 Minor de ledger corregidos; Lente B sin defectos en ~27.000 ejecuciones diferenciales HEAD/árbol. **Commits de R2 hechos** (`41d7c9d` T-05 · `cd174a0` T-06 · `119ba6c` T-07 · `e81cc99` T-08 · `0366f1b` ledger); **R2 integrada en master (`400b3fd`, `--no-ff`) y pusheada a origin** (master + feature/plugin-refactor); la rama está alineada con master (`reset --soft`). **R3 INTEGRADA EN MASTER (`bf6f50d`, `--no-ff`) Y PUSHEADA** (master + feature/plugin-refactor). **RAMA ACTIVA AHORA: `feature/installer-registro-real`** (desde master): iniciativa de vía rápida `docs/roadmap/2026-09-11-installer-registro-real/` (ledger `0dfdad1`, 6 tareas, decisiones D1–D6 en el ledger; test-plan n/a). **Tramo I1 (T-01..T-03): intento 1 (8,00 €) 2 Critical + 9 Important + 9 Minor → corregidos los 20 y verificados por las dos lentes en el intento 2 (20,13 €). El intento 2 destapó 1 Critical nuevo** (`ponerToml` solo ve la tabla como cabecera: si el usuario tiene `plugins."custom-agents@daycry".enabled = false` como clave con punto o tabla en línea, se apendiza una segunda declaración y el `config.toml` de Codex deja de parsear — reproducido con `tomllib`), **7 Important** (migrarDeCopy fuera del try; manifiesto parcial que pisa al anterior; Ctrl-C sin manifiesto; `.ps1` marcado ejecutable; `.CMD` antes que `.EXE`; escritura no atómica que trunca `settings.json`; migración que borra ficheros editados) **y 8 Minor → cerrados los 15 en el intento 3. El intento 3 (lente fresca sobre el delta, 10,51 €) destapó un Critical más de la misma familia TOML**: la rama implícita de `ponerToml` escribe `enabled` dentro de una sub-tabla declarada (`[plugins."custom-agents@daycry".env]`), así que Codex no habilita el plugin mientras el instalador dice que sí, y la segunda pasada corrompe el `config.toml` (reproducido con `tomllib`). **El orquestador ordenó una 4.ª pasada pese al tope del bucle** (es el fallo exacto que la iniciativa corrige), con arreglo estructural: **post-condición** — `ponerToml` re-analiza lo que va a escribir, comprueba el camino exacto y que no haya clave duplicada, y si falla no escribe y da error con el cambio manual; más oráculo independiente en los tests y las 5 formas × 2 pasadas. Marcador `I1-fix3`. **TRAMO I1 CERRADO Y COMMITTEADO** (`d4294ae` código T-01/T-02/T-03 · `09f62bd` ledger): 38 gaps en 4 pasadas (3 Critical, 16 Important, 19 Minor), **todos cerrados**; las 5 formas de TOML × 2 pasadas verificadas por el orquestador con `tomllib`; 103 tests de Node; scope-check limpio. **TRAMO I2: intento 1 (10,58 €) 8 Important + 7 Minor → cerrados los 15 en el intento 2, con una función única de estado efectivo que consultan `/doctor` y `status`. El intento 2 (lente fresca, 9,06 €) destapó 4 Important + 7 Minor** → implementer en **intento 3, último del bucle** (marcador `I2-fix2`). El Important de fondo (I2-1): faltaba leer `.claude/settings.local.json`, que es scope documentado `local` y está POR ENCIMA de `project`, y es donde escribe `claude plugin disable --scope local` — con el plugin apagado ahí, `/doctor` decía modo plugin y hooks ✅. También: `/doctor` se caía con un `projectPath` no-cadena; la fila de OpenCode casaba por basename; y el paso `exec` sin `cwd` graba el `projectPath` del cwd en vez del `--dir` (causa en T-02, tramo I1). **Desviación 29 rectificada**: la documentación de Claude Code SÍ fija la precedencia (Managed > command line > Project local > Shared project > User). El hilo de los 5 Important de `/doctor`/`status`: el detector no distingue «hay un apunte» de «este plugin está activo para esta raíz» (entradas de otro proyecto validan la raíz; `status` y `/doctor` se contradicen con `enabledPlugins: false`; un `custom-agents@otro: false` tumba la fila; los tests no aíslan `CLAUDE_CONFIG_DIR`). **D4 corregida en el ledger**: la ruta que fijé para OpenCode era incorrecta y la desviación 21 del implementer acertó (confirmado contra `resolvePluginSpec` de OpenCode). Después: revisión de dos lentes I2 → commits → cierre (`changelog-sync`, retro) → suite completa + workflows → push → PR a master → **el merge del PR lo hace Claude** (decisión del usuario, 2026-09-11; `gh pr merge --merge`, sin squash, con CI verde) → `release.py 1.20.0` sobre master + push del tag (dispara `release.yml`). Limpieza hecha aparte (`d719b9e`): estado local de sesión ignorado y entrada de journal versionada → `scope-check` **limpio por primera vez** (0 fuera de alcance); después revisión intento 2 → commits → tramo I2 (T-04..T-06). **Instrucción del usuario para el cierre**: suite completa + todos los workflows de `ci.yml` en local → push → PR a master (`gh pr create`) → `release.py 1.20.0` sobre master integrado + push del tag (dispara `release.yml`). Preguntar quién mezcla el PR → checklist M-01 la hace el usuario en su máquina (Codex/OpenCode). R4 del refactor (Fase 4, T-11…) queda DESPUÉS del instalador por decisión del usuario. Estado previo de R3:: `3c2cd7a` T-09 · `92514f0` T-10 · `d10a36b` ledger · `8216fc5` ADR-016 `aceptada` + design.md. Los 3 residuales R3-1..R3-3 se cerraron en la 4.ª pasada autorizada (verificados con mutantes por el orquestador; sin lente fresca en esa pasada, dicho en la traza). **Pendiente de decisión del usuario**: (1) merge `--no-ff` de R3 en master + push (como R1/R2); (2) puerta de R4 (Fase 4 E1–E11, T-11…T-19 + T-20…T-22 cierre); (3) NUEVA iniciativa `installer-registro-real` (vía rápida) tras la revisión del instalador `npx`: hoy copia el bundle a `.claude/` (sin hooks ni namespace; `/doctor` da falso positivo «hooks registrados»), en Codex no habilita el plugin (`codex plugin marketplace add` + `enabled = true` en `config.toml`), OpenCode no registra el adaptador en `opencode.json` `plugin`; UX sin banner ni checkboxes. Referencia: claude-mem (`known_marketplaces.json` + `installed_plugins.json` + `enabledPlugins`; `@clack/prompts` multiselect; `CodexCliInstaller.ts`). Contexto del tope de R3: Intento 3 (5,83 €): B-1..B-5 cerrados y verificados (orquestador + lente B fresca sobre el delta); residual **R3-1 Important** (la lista `equivalencia.categorias` no está fijada en el test: quitar categoría + entradas deja vivo el mutante) + **R3-2/R3-3 Minor** de código (sustituciones no inyectivas; `_*_FALLBACK` anotado/encadenado no detectado); R3-4/R3-5 (ledger) corregidas. Opciones: (a) cuarta pasada corta del implementer (~10-30 líneas de tests + una regex) y luego commits; (b) aceptar R3-1..R3-3 como límite conocido en `ADR-016` y committear. Recomendación: (a). Tras la decisión: `ADR-016` → `aceptada` (+ fila del índice `docs/knowledge/README.md`), commits T-09 (incluye `git add` de `copias.json` y `tests/test_copias_declaradas.py`, hoy SIN trackear) / T-10 / ledger / ADR+design, CONTINUE-HERE, puerta de R4. Historial previo: Intento 1: 6 Important + 7 Minor (7,55 €), todos corregidos (ADR-016 enmendado por el orquestador con «Tolerancias explícitas del comparador»; design.md §4 remite a él). Intento 2 (12,05 €): los 13 cerrados con mutantes; nuevos B-1 Important (corpus de `equivalencia` podable: pasa a categorías obligatorias) + B-2..B-5 Minor de código (sustituciones solo identificadores con ``, `respaldos` por copia, segunda copia en el mismo fichero, `./` en el corpus) → implementer intento 3 (marcador `plugin-refactor/R3-fix2`); N-1..N-5 de ledger/docs corregidas por el orquestador salvo N-4 (parser `_parse_horas` de ledger-lint no suma `+ N,NNh fix1`; preexistente, anotado para T-17/T-19). Al volver: verificación propia → si los 5 cierran, traza final «intento 3», `ADR-016` → `aceptada` (+ fila del índice), commits T-09/T-10/ledger/ADR → puerta de R4; si no cierran, se declara y se decide con el usuario. Nada de R3 está committeado aún (`copias.json` y `tests/test_copias_declaradas.py` sin trackear). Puerta de R3 (Fase 3, T-09..T-11: `copias.json` + `tests/test_copias_declaradas.py` + linter, O1/ADR-016): lanzar implementer con brief de `task-brief.py`; las copias `--8<--` viven hoy en `lint_plugin.py` 109-305/617-637/640-726, `doctor.py` 715-735/738-824, `knowledge-find.py` 244-264. Observaciones de la Lente B para T-19: 7 helpers cosméticos (`_construir_parser`, `_scan_rec_base`…), `dfs` era falso positivo de `code-health` (mide hasta el siguiente `def`), centinela en banda `"error"` en `doctor._calibracion_leer`. **Pendiente ajeno a R2**: `tests/test_knowledge_find.py::test_real_tokens_por_hora_trae_las_lecciones_de_estimacion_arriba` está rojo desde que `GOT-010` entró en el corpus (mismo ranking HEAD/árbol; el test espera 9 lecciones de estimación arriba y GOT-010, que habla de tokens, desplaza una) — test acoplado al contenido de `docs/knowledge/`, hermano de E11; arreglo pequeño por vía rápida o dentro de T-19. Frontmatter `tasks:`/`estado:` añadido al ledger y al plan (la plantilla del planner no lo trae; hueco para la matriz de contratos T-14))

`spec.md` **aprobada** (5 características de refactor cero-comportamiento + 8 de encadenamiento E1–E10) y
`evaluation.md` **completado**: 90,0 h con margen · ~4.540 € · go condicionado. **Siguiente paso: `architect`** (Fase 2-bis,
dos pasadas) para O1 copias declaradas vs O2 módulo vendorizado — O3 descartada —, y después `planner`. **Decisión de diseño O1** (registro de copias declaradas + un test de identidad + aviso del linter para bloques no registrados): barata,
reversible, unifica cuatro mecanismos de guardarraíl; O2 (vendorizar) descartada porque `PAYLOAD_COMUN` ya lleva `agent-kits/` entero;
O3 (copias generadas) queda como evolución de O1. C-03 se ENCOGE: no hay copias accidentales. El hallazgo E7
(usage-meter) salió del refactor y va por vía rápida (punto 4). Línea base `code-health` en la carpeta (`code-health-baseline.json`): 36 ficheros ·
14.259 líneas · 7,6 % duplicado · **105 funciones > 30 líneas** · 8 TODO (6 falsos positivos del detector).
Hallazgo que ordena todo: la duplicación grande es **deliberada** (scripts standalone que viajan sueltos,
copias byte a byte guardadas por `test_knowledge_index`) o **generada** (`interop/`); la deuda real son
las funciones largas en hotspots (`task-brief.py` `main()` 155 líneas, `knowledge-find`, `doctor`,
`lint_plugin`). **Decisión previa para `architect`**: copias declaradas vs módulo vendorizado (el import
común se descarta: rompe el standalone y el requisito multi-runtime). Pendiente: `/pm-cycle`.

### 4 · `docs/roadmap/2026-09-10-usage-meter-transcripts/` — vía rápida (CERRADA: 3/3, retro y CALIBRATION, `retro-gate` abierta)

`usage-meter.py:87` codifica el `cwd` con `[/\.:]` y Claude Code nombra la carpeta de transcripciones con
«todo carácter no alfanumérico → `-`»: en esta máquina la clave NUNCA existe y `close` degrada siempre a
`fuente: estimado` (once artefactos en dos sesiones; `CALIBRATION.md` alimentándose de juicio). Los 28 tests
inyectan `--transcript-dir`: cobertura cero de la función. Ledger ligero `a868a0a` (T-01 la línea + tests sin
inyección con oráculo de carpetas reales · T-02 `GOT-010` · **T-03 añadida por la revisión**). La revisión de dos
lentes (intento 1: 1 Critical, 6 Important, 7 Minor) destapó que la clave de carpeta era solo media causa: el
parser usa `glob("*.jsonl")` NO recursivo y Claude Code guarda los transcripts de subagentes en
`<session-id>/subagents/agent-*.jsonl` → **5 de 41 ficheros, 43,6 % de tokens sin contar, publicado como
`medido`**. La hipótesis del implementer («el JSONL del subagente no se vuelca hasta acabar el turno») es FALSA
(crece en vivo). 6 de 7 tests nuevos pasaban con el código viejo (oráculo copiado del código bajo prueba).
**`implementer` corrigiendo** (T-03 recursivo + tests que muerden + GOT-010 con la causa de dos patas). El
orquestador tiene abierto el marcador `usage-meter-transcripts/correccion` (07:03:28Z) para la evidencia
cruzando turno del criterio 4 de T-01, que solo la sesión principal puede dar. Después: revisión intento 2,
commit, `architect`. Es la pieza que hace MEDIBLE todo lo demás: por eso va antes que el `architect`.

**Cerrada el 2026-09-10** en `feature/plugin-refactor`: `cf88f35` (T-01/T-03 código: clave `[^A-Za-z0-9]` + `rglob` con dedupe) ·
`791f43f` (`GOT-010`) · `0ebcc1c` (ledger 3/3 + CHANGELOG + cifras vivas) · retro + fila en `CALIBRATION.md`. Primer coste IA
MEDIDO del proyecto en Windows (evidencia cruzando turno: 40 respuestas, 3,16 €). Regla nueva: los marcadores de
`usage-meter` abiertos con el código anterior se DESCARTAN (contarían enteros los transcripts previos: 143 € falsos).

### Orden DECIDIDO por el usuario (2026-09-09/10): cerrar F1 ✅ → usage-meter (vía rápida) ✅ → refactor (`architect` EN VUELO) → brief-budget

cerrar F1 → **refactor** (partir `main()` de `task-brief.py`) → **brief-budget** (presupuesto por secciones
sobre código limpio; al revés se refactoriza dos veces) → F2 de `project-specialization`.

### Lo aprendido hoy que aún no es doctrina (candidatas a lección, anotadas en el ledger de 1)

- `review-lens-select.py` no ve materia de seguridad en abrir un canal de texto controlado por el
  consumidor hacia el prompt de un subagente (`lente_c: false` en los tres intentos; la Lente B encontró la
  suplantación las tres veces).
- Cambiar una pieza no propaga a quien la documenta y el ciclo no lo comprueba (pasó dos veces DENTRO de
  la misma iniciativa: gaps 4, 13 y 14).
- `GOT-007` apareció **tres veces** en un día (dos del orquestador, una del implementer): toda cifra o
  evidencia se re-verifica tras el ÚLTIMO cambio, después del `git add`.
- Ruido del árbol: `.claude/.confluence-pending`, `.claude/.gitignore`, `.claude/.headroom_wrap_marker.json`,
  `CONTINUE-HERE.local.md`, `feature-pendiente.bundle` ensucian `scope-check` en CADA ciclo — borrar o ignorar,
  decisión del usuario.


## Sin trabajo en curso — lo ya cerrado

**v1.19.0 publicada** (2026-09-08, `8e9dec7`): interoperabilidad con Codex y OpenCode
+ instalador `npx` multi-proveedor, integrada con merge (`2095111`) y con la CI
arreglada en `ac1d1ef`. Las dos decisiones que este fichero dejaba abiertas el
2026-09-08 **están resueltas**: el tag `v1.18.1` existe, y el trabajo de interop ya
está comiteado y released (este fichero decía «sin commit ni rama»: era lo desfasado).

Antes de eso: `docs/roadmap/2026-09-04-sin-motor-externo/` (retira
"superpowers"/"Modo A") y `docs/roadmap/2026-09-04-memory-retrieval/` (memoria técnica
en tres capas — `ADR-013` —, captura episódica del turno con `<private>`, doctrina del
plugin que viaja con `--doctrina`, y la retro como puerta de cierre con
`retro-gate.py`).

## Dos decisiones abiertas (no bloquean nada)

1. **¿Publicar en npm?** El paquete es `@daycry/custom-agents`. **No verificado en la
   sesión del 2026-09-09** (hace falta red): si sigue sin publicar, exige
   `npm publish --access public` con la cuenta de daycry.
2. **¿Ampliar `GOT-007`?** Su lección era «corre la suite después de `git add`», pero
   el patrón real que dejó la CI roja es más amplio: **toda cifra medida y todo test
   nuevo hay que re-verificarlos después del ÚLTIMO cambio**.

## Entorno de esta máquina (Windows) — sigue aplicando

- El `python3` del PATH es el alias de la Microsoft Store: sin un intérprete real
  los hooks callan. Hay un venv en `.venv/` (ignorado por git) creado con
  `python -m venv .venv` + `cp .venv/Scripts/python.exe .venv/Scripts/python3.exe`
  + `pip install pytest`. **Antes de cualquier puerta:**
  `export PATH="$PWD/.venv/Scripts:$PATH"`.
- La suite completa deja ~36 fallos en Windows que **no** son defectos: `\` vs `/`
  en asserts de `relpath`, bit `+x` POSIX, `os.symlink` sin privilegio en el
  helper `sin_python3`, rutas con espacios en `coverage-gate`, `WinError 5` en
  evals, CRLF byte a byte en `test_knowledge_find --show`, los 6
  `test_progress_line_*`, `mark_docs_pending`/`ledger_lint_warn` y 3 de
  `test_release`. CI (Linux) los pasa. `release.py` **no** corre pytest, así que
  no bloquean el release; la puerta de verdad es CI.
- Checkout en CRLF (`core.autocrlf=true`, sin `.gitattributes`): toda comparación
  de bytes o conteo (CA-22 de `agents/evaluator.md`, copias de la doctrina) debe
  normalizar `\r\n` → `\n`, o comparar blobs del índice.
- El plugin que se carga en sesión es el de
  `~/.claude/plugins/cache/daycry/custom-agents/<versión>/`, **no** el árbol de
  trabajo: para probar piezas nuevas en vivo, `claude --plugin-dir "<ruta del repo>"`.
- Sin seguimiento y ajenos al repo: `.claude/.headroom_wrap_marker.json`,
  `CONTINUE-HERE.local.md`, `feature-pendiente.bundle` (bundle de entrega ya
  innecesario: todo está en `origin/master`). Ensucian `scope-check` y
  `release.py`; se pueden borrar o añadir al `.gitignore` — decisión de Jordi.

## Recordatorio permanente

El repo es **público**: nunca datos corporativos de Atlassian ni nada específico
de un cliente. Los tests de la captura episódica usan secretos **inventados**
(`ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ0123`, `AKIAIOSFODNN7EXAMPLE1`) para probar la
redacción; no son reales.
