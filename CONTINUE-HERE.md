# CONTINUE-HERE

> **2026-09-21 — UNA SOLA RAMA EN VUELO: `feature/graphiti-memory`. Leer este bloque; el resto es histórico.**
>
> Estado del repo: PR #9 (`knowledge-services`) y PR #10 (`jira-review-comments`) **mergeadas en master**; **release
> v1.21.0 publicada** (`ac42f08`); master mezclado en `feature/graphiti-memory` (`6ce6a00`). Máquina nueva
> (usuario `47888230E`): `.venv` recreado hoy (`python -m venv .venv` + `pip install pytest pyyaml`) y
> `.claude/dev.json` restaurado a mano (`{"tdd": true, "worktree": false, "subagentes": false}`, ignorado por git).
> Sin `.claude/jira.json` → sin worklog ni comentarios Jira en esta iniciativa.
>
> **`/dev-cycle graphiti-memory completo` — Fase 2 (T-04, T-05, T-06) en bucle de revisión.** Intento 1 (20 gaps,
> #31-#50) → fix1; intento 2 (`c06e249`: 16 nuevos #51-#66, 3 Critical) → fix2 `92f1bc6` (3 Critical + 8 más con
> 25 tests en `TestGraphitiFase2Fix2`). Baseline hoy: 384 passed en las 5 rutas graphiti/knowledge.
> **Ronda `fix3` HECHA** (`6bf75a0`, 1.47h medidas; sin código de producción: tests dedicados, evidencia del ledger,
> docs de contrato; deuda #40/#60 en `design.md`, `77474ad`). **Intento 3 (último) HECHO y escrito en el ledger:
> NO CIERRA** — lentes A+B(+D)+C en paralelo: A 0 Critical (solo evidencia: #76 test SSE multilínea, #77 invariante
> «el núcleo no nombra graphiti» roto por `--propose-config`); B y C coinciden en **3 Critical**: #67 `apply()` con
> `.pending` heredado + servidor caído PUBLICA `{}` y borra el `.pending` (pérdida del manifiesto), #68 la
> reconciliación de #54 solo corre en la rama `if not ops`, #69 `add_triplet` sin `source_node_name`/`target_node_name`
> (obligatorios en el fixture real → CA-11 no observable contra el servidor real). 8 Important (#70-#77), 11 Minor
> (#78-#88), 1 descartado (rojo intermitente = mutantes de otra lente sobre el MISMO checkout: gap de proceso de la
> skill, candidata a lección). T-04/T-05/T-06 vueltas a `en-progreso`; Resumen de progreso corregido (3/10, IA 7.96h).
> **2026-09-23 18:10 — SESIÓN CERRADA A PETICIÓN DEL USUARIO. PUNTO DE REANUDACIÓN:** rama `feature/training-data-services`; Fase 1 revisión intento 2 HECHA y comiteada: 13/13 del intento 1 cerrados; 13 nuevos: 0 Critical, **3 Important de puertas del repo** (#15 description de `.claude-plugin/plugin.json` y `marketplace.json` sin la skill → `tests/test_manifests.py` 2 failed; #16 badge `skills-18`→19 en README ES/EN → `tests/test_readme_badges.py` exit 1; #17 `SKILL.md:108` cita `scripts/test_*.py` que el paquete portable no incluye → `tests/test_export_skills.py` 1 failed), 10 Minor (#18-#25). T-01..T-03 `en-progreso`; sin marcadores abiertos (`T-01-fix1` cerrado 2.87h). AL RETOMAR: `usage-meter start --artefacto training-data-services/T-01-fix2`; implementer opus con brief = sección «intento 2: Fase 1» (#15-#24; #25 del orquestador) + regla: la Verificación de cada fase incluye `pytest tests/test_manifests.py tests/test_readme_badges.py tests/test_export_skills.py tests/test_skill_size.py`; scripts solo en `scratchpad/impl-tds-f1fix2/`. Luego revisión intento 3 de 3 (ÚLTIMO; worktrees `tds-lente-<x>-i3`); si 0 Critical/Important → T-01..T-03 `completado`, Resumen 3/11 + tokens fix1/fix2, commit → Fase 2 (T-04 recorder, T-05 puerta Gold, T-06 índice) → F3 (T-07..T-09) → F4 (T-10, T-11) → qa sin UI → documenter → 4-bis → changelog → retro → PR. PR de graphiti-memory sobre master aún pendiente de abrir por el usuario (sin `gh`): https://github.com/daycry/custom-agents/compare/master...feature/graphiti-memory?expand=1 . Plugin instalado en esta máquina = 1.20.2 (sin knowledge-curator): `claude plugin update custom-agents@daycry`. Sesión: `b8053ac5-12f5-4c5d-8a31-080cc28d70a3`. **Histórico (16:40):** tds Fase 1 fix1 HECHA y subida (`9f5d0ab`: 13/13 #1-#14, 2.87h incl. corte; regla genérica de /doctor para capacidades opt-in; E20/E21). EN VUELO: revisión F1 intento 2 de 3, lentes A+B en `scratchpad/tds-lente-a-i2|b-i2` (detached `9f5d0ab`, base `7f4411c`). Después: sección «intento 2: Fase 1»; si 0 Critical/Important → T-01..T-03 `completado`, Resumen 3/11, commit → Fase 2 (T-04 recorder, T-05 Gold, T-06 índice). **Histórico:** SESIÓN REINICIADA con el implementer de `fix1` a medias: trabajo parcial en el árbol (16 ficheros, suites verdes), 0 filas del ledger rellenas, marcador `training-data-services/T-01-fix1` abierto. Implementer REANUDADO por SendMessage desde su transcripción para terminar y rellenar el ledger. Si al retomar otra vez sigue a medias: `git stash` NO (perderías el parcial); despachar un implementer nuevo con el brief de fix1 + «revisa `git diff` antes de tocar». **Histórico (18:25 UTC+2 del día anterior en el log):** tds Fase 1 revisión intento 1 HECHA (`7f4411c`): 0 Critical, 2 Important (#1 outcome no hashable crash; #2 root absoluto/caps dentro de docs/knowledge), 12 Minor (#3-#14; #9 arbitraje: regla genérica en doctor «capacidad opt-in sin config_path se omite salvo --verbose»). EN VUELO: implementer opus ronda `fix1` (marcador `training-data-services/T-01-fix1` 11:23Z). Después: cerrar marcador, puertas, commit, revisión intento 2 de 3 (`--base 7f4411c`, worktrees `tds-lente-<x>-i2`), #13 Resumen tokens; si cierra → Fase 2 (T-04..T-06). **Histórico (17:10):** training-data-services Fase 1 HECHA (`bd7a637` T-01, `b473431` T-02, `1d549fb` T-03, `ef4841f` Resumen 3/11, 0.41h). EN VUELO: revisión de dos lentes F1 intento 1 de 3, lentes A+B+D (D por `regex-en-bucle` en `case_schema.py:129`) en worktrees `scratchpad/tds-lente-a-i1|b-i1|d-i1` (detached `ef4841f`, base `bab4fb5`). Después: sección «intento 1: Fase 1» en el ledger; fixN si hay Critical/Important; Fase 2 (T-04 recorder, T-05 puerta Gold, T-06 índice) → Fase 3 (T-07 dedup, T-08 partición, T-09 ensamblador + puente curator) → Fase 4 (T-10 setup/doctor, T-11 aislamiento/interop/cierre) → qa sin UI → documenter → 4-bis → changelog → retro → PR. **Histórico (16:20):** Revisión de Graphify (github.com/Graphify-Labs/graphify) entregada al usuario: grafo determinista de código (tree-sitter, sin embeddings ni temporalidad), MCP local, `save-result`/`reflect`, hook PreToolUse. Recomendación registrada: NO reabrir graphiti-memory; seguir training-data-services con 2 ajustes en su esquema (mapeo de `outcome` desde `useful|dead_end|corrected`; `context` estructurado opcional con procedencia) — ya en el brief de T-01; proponer iniciativa futura `graphify-code-intent` (capacidad opt-in + `knowledge-find --intent codigo` + hook opcional + adaptador `save-result` → case store) DESPUÉS de los datasets, salvo que el usuario la priorice. EN VUELO: implementer opus Fase 1 T-01..T-03 de training-data-services (marcadores propios). **Histórico (15:30):** RAMA `feature/training-data-services` (desde origin/master; no depende de graphiti-memory). `/dev-cycle training-data-services completo` ARRANCADO: plan/tasks `en-progreso`. EN VUELO: implementer opus Fase 1 (T-01 esquema training.json + caso; T-02 capacidad `training` + consumo de redact.py; T-03 plantillas + ADR). Después: revisión de dos lentes F1 (intento 1 de 3), Fase 2 (T-04..T-06), Fase 3 (T-07..T-09), Fase 4 (T-10, T-11), qa sin UI, documenter, 4-bis, changelog, retro, PR. **Histórico:** INICIATIVA graphiti-memory CERRADA (`0f05117`): spec implementada, plan 10/10, qa sin UI verde (`testing/report.md`), Knowledge Gate (GOT-013, LES-018..020; 1 needs_changes), retro + CALIBRATION, CHANGELOG generado, índice del roadmap al día. **PR sobre master PENDIENTE de abrir por el usuario** (`gh` no está en esta máquina): cuerpo preparado en el scratchpad de la sesión `PR-graphiti-memory.md` y resumido en el último mensaje; URL de compare: https://github.com/daycry/custom-agents/compare/master...feature/graphiti-memory?expand=1. SIGUIENTE INICIATIVA: `training-data-services` (11 tareas, 4 fases; plan `borrador` → `en-progreso`) en rama nueva `feature/training-data-services` desde `origin/master` (no depende de graphiti-memory). Orden después: dev-cycle-dataset → brief-budget → plugin-refactor → project-specialization. Plugin instalado en esta máquina = 1.20.2 (sin `knowledge-curator`): `claude plugin update custom-agents@daycry`. **Histórico (14:30):** PLAN 10/10 CERRADO (`dc1603f`): Fase 4 micro-ronda fix3 verificada, T-09/T-10 completado. RITUAL DE CIERRE EN CURSO: plan/tasks `completado` + CHANGELOG generado (`5e5276e`); `retro.md` escrito (validada_por_usuario: pendiente) + fila en CALIBRATION.md; EN VUELO: agentes `qa` (sin UI → `testing/report.md`) y `documenter` (docs/ + candidatos de conocimiento). Después: 4-bis `knowledge-curator` sobre `docs/knowledge/candidates/pending/` (≥ 1 candidato), `retro-gate.py` exit 0, spec → `implementada`, fila del índice `docs/roadmap/README.md:46`, commit, push, PR sobre master (descripción derivada del ledger). Luego: training-data-services → dev-cycle-dataset → brief-budget → plugin-refactor → project-specialization. **Histórico (12:40):** Fase 4 revisión intento 3 (ÚLTIMO) HECHA y subida (`988aed7`): 0 Critical/Important, 10 Minor #186-#195 → BUCLE CERRADO. EN VUELO: micro-ronda `fix3` (implementer opus, marcador `graphiti-memory/T-09-fix3` 09:38Z) acotada a #186 (regresión comentarios multilínea), #190(d), #194, #193 (qa-report §5/Veredicto) + deuda declarada #187-#192 en design.md. Después (orquestador): cerrar marcador, verificar #186 con su test/mutante, T-09/T-10 `completado`, #162 (tokens F4) y #163 (criterio T-10), Resumen 10/10, commit, push → `qa` sin UI (agente qa, modo `test-plan: n/a (sin UI)`) → `documenter` → 4-bis `knowledge-curator` (1 candidato pendiente) → `changelog-sync` → `/retro` + `retro-gate.py` → spec `implementada` → PR sobre master. Nota: GOT-012 supera MAX_PATH en worktrees profundos (3 falsos rojos por lente; `core.longpaths` activo en el repo principal) → candidata a gotcha en la retro. **Histórico (11:40):** Fase 4 fix2 HECHA y subida (`e585289`: 13/13, seguridad 59 tests, console-encoding verde, 1.76h). EN VUELO: revisión Fase 4 intento 3 de 3 (ÚLTIMO), lentes A+B+C en worktrees `scratchpad/lente-a-i3|lente-b-i3|lente-c-i3` (detached `e585289`, base `a6723ec`). Después: sección «intento 3: Fase 4»; si 0 Critical/Important → T-09/T-10 `completado`, #162/#163, Resumen 10/10, qa sin UI → documenter → 4-bis → changelog-sync → /retro + retro-gate → spec implementada → PR; si quedan Important → fix corta + verificación dirigida (precedente F2/F3). **Histórico (09:45):** RETOMADO. EN VUELO: implementer opus ronda `fix2` Fase 4 (marcador `graphiti-memory/T-09-fix2` ABIERTO 07:40Z; brief = sección «intento 2: Fase 4», #168, #173-#183, #185; regla de higiene: scripts solo en `scratchpad/impl-f4fix2/` y borrado al terminar). Después: cerrar marcador, puertas (incl. `tests/test_console_encoding.py`), commit, push, revisión intento 3 de 3 (ÚLTIMO) con worktrees `lente-a-i3|lente-b-i3|lente-c-i3`. **Histórico (2026-09-22 23:05):** SESIÓN CERRADA A PETICIÓN DEL USUARIO. PUNTO DE REANUDACIÓN:** Fase 4 revisión intento 2 HECHA y comiteada: 11/11 del intento 1 cerrados; 14 nuevos: 0 Critical, **4 Important** (#168 regresión CI `tests/test_console_encoding.py` 4 failed por `_mcp_fake.py` con acentos; #173 escaneo de binarios de red no mira `subprocess` en lista dentro de scripts alcanzables + egress opt-in de journal.py como excepción a declarar; #174 comprobaciones de identidad/perdidos de #154 sin test (N3/N4 vivos); #175 puerta CA-05 evadida por invocación multilínea), 10 Minor (#176-#185). T-09/T-10 `en-progreso`; sin marcadores abiertos. AL RETOMAR: `usage-meter start --artefacto graphiti-memory/T-09-fix2`; implementer opus con brief = sección «intento 2: Fase 4» (#168, #173-#183, #185) + REGLA NUEVA para el brief: «scripts auxiliares SOLO en `scratchpad/impl-<ronda>/` y bórralos al terminar; añade `tests/test_console_encoding.py` y `tests/test_suites_no_pytest.py` a las rutas de la Verificación»; luego revisión intento 3 de 3 (ÚLTIMO; worktrees con nombre `lente-a-i3` etc., insensible a mayúsculas; una lente pesada a la vez si hay flakes) → si 0 Critical/Important: T-09/T-10 `completado`, #162 (tokens Fase 4) y #163 (criterio T-10) del orquestador, Resumen 10/10 → qa sin UI → documenter → 4-bis (1 candidato pendiente) → changelog-sync → /retro + retro-gate → spec implementada → PR sobre master; si al 3.º quedan Critical/Important → parar y preguntar (o fix corta + verificación dirigida como en F2/F3). Después: training-data-services → dev-cycle-dataset → brief-budget → plugin-refactor → project-specialization. Sesión: `b8053ac5-12f5-4c5d-8a31-080cc28d70a3`. **Histórico (20:20):** Fase 4 fix1 HECHA y subida (`92a5920`: 11/11 #154-#166, suite de seguridad 35 tests, 1.43h). EN VUELO: revisión Fase 4 intento 2 de 3, lentes A+B+C en worktrees `scratchpad/A|B|C` (detached `92a5920`, base `42448df`). Después: sección «intento 2: Fase 4»; si 0 Critical/Important → T-09/T-10 `completado`, #162/#163 (Resumen tokens, criterio T-10), qa sin UI → documenter → 4-bis (1 candidato pendiente) → changelog-sync → /retro + retro-gate → spec implementada → PR sobre master. **Histórico (19:00):** Fase 4 revisión intento 1 HECHA (`42448df`): 0 Critical, 4 Important (#154 uuid sin validar antes de add_memory; #155 puerta de hooks con agujeros: variable/inline/frontmatter; #156 espía inalcanzable; #157 CA-05 literal frágil + alcance), 10 Minor (#158-#167). T-09/T-10 `en-progreso`. EN VUELO: implementer opus ronda `fix1` Fase 4 (marcador `graphiti-memory/T-09-fix1` 16:53Z). Después: cerrar marcador, puertas, commit, revisión intento 2 de 3 (`--base 42448df`), #162/#163 del orquestador; si cierra → qa sin UI → documenter → 4-bis (1 candidato pendiente) → changelog-sync → /retro + retro-gate → spec implementada → PR. Scratchpad limpiado de scripts huérfanos (#167). **Histórico (18:15):** FASE 4 IMPLEMENTADA (`ca56f3a` T-09, `10b350c` T-10, `517ab91` Resumen 10/10) y subida. EN VUELO: revisión de dos lentes Fase 4 intento 1 de 3, lentes A+B+C en worktrees `scratchpad/A|B|C` (detached `517ab91`, base `bffb045`). Después: sección «intento 1: Fase 4» en el ledger; si 0 Critical/Important → qa sin UI → documenter → 4-bis → changelog-sync → /retro + retro-gate → spec implementada → PR sobre master. **Histórico (17:30):** RETOMADO. EN VUELO: implementer opus terminando T-09 (marcador `graphiti-memory/T-09-bis`, sección 5 guardarraíl MCP + ledger) y haciendo T-10 (marcador `T-10`, `testing/qa-report.md` sin UI, lint/evals/--check). Después: revisión de dos lentes Fase 4 (intento 1 de 3, `--base bffb045`), Resumen Fase 4, qa sin UI, documenter, 4-bis, changelog-sync, /retro + retro-gate, spec implementada, PR. **Histórico (14:35):** SESIÓN CERRADA (implementer de la Fase 4 DETENIDO a petición del usuario). PUNTO DE REANUDACIÓN:** T-09 `en-progreso` con `tests/test_graphiti_security.py` comiteado (20 passed; falta la sección 5 del brief: guardarraíl de red del cliente MCP como regresión del repo; sin RED/Verificación en el ledger todavía); T-10 `borrador` sin empezar. Marcador `graphiti-memory/T-09` CERRADO (2.06h); `usage-meter status` sin huérfanos. AL RETOMAR: despachar implementer opus para terminar T-09 (marcador `graphiti-memory/T-09-bis`, revisar el fichero existente antes de añadir) y hacer T-10 completo (brief = tasks.md Fase 4 + spec CA-01/04/05/07/14 + design.md límites; `testing/qa-report.md` sin UI; interop/lint/evals en 0), luego revisión de dos lentes Fase 4 (intento 1 de 3), qa sin UI, documenter, 4-bis, changelog-sync, /retro + retro-gate, spec implementada, PR sobre master. Después: training-data-services → dev-cycle-dataset → brief-budget → plugin-refactor → project-specialization. **Histórico:** CIERRE DE SESIÓN EN CURSO (el usuario pidió acabar la implementación y seguir más tarde):** el implementer de la Fase 4 (T-09 seguridad, T-10 interop/QA) está en vuelo con marcadores `graphiti-memory/T-09`/`T-10` propios; al terminar, el orquestador comitea/pushea y NO lanza la revisión. AL RETOMAR: (1) si T-09/T-10 están `completado` en el ledger → `usage-meter status` sin huérfanos, `scope-check --base 54d01f9`, `review-lens-select.py --base 54d01f9`, revisión de dos lentes Fase 4 intento 1 de 3 (worktrees `scratchpad/A|B|…`), Resumen Fase 4; (2) si quedaron `en-progreso` → cerrar marcadores huérfanos y re-despachar lo que falte. Después: qa sin UI → documenter → 4-bis → changelog-sync → /retro + retro-gate → spec implementada → PR. **Histórico:** FASE 3 CERRADA:** fix4 (0.64h) verificada por el orquestador (mutante #148 muere, 800 passed), T-07/T-08 `completado`, Resumen 8/10 · 16.38h IA. SIGUIENTE: Fase 4 — T-09 (`tests/test_graphiti_security.py` + `tests/test_hooks_shell.py`: sin red desde hooks, sin datos excluidos, CA-14 Ollama inválido → dead-letter) y T-10 (`testing/`, interop, lint/evals/--check en 0) → revisión de dos lentes Fase 4 (intento 1 de 3) → qa sin UI → documenter → 4-bis → changelog-sync → /retro + retro-gate → spec implementada → PR. **Histórico:** Verificación dirigida fix3 HECHA (`7681f55`): 13/15 confirmadas; 1 Important #148 (/doctor ⚠️ permanente por su recorte de 200 con remedio inerte) + 5 Minor #149-#153. EN VUELO: ronda corta `fix4` (implementer opus, marcador `graphiti-memory/T-07-fix4` ABIERTO 10:21Z). Después: cerrar marcador, puertas, reproducir escenario #148 y mutantes (orquestador, sin lentes), T-07/T-08 `completado`, #111 Resumen (Fase 3 2/2, 8/10), commit, push → Fase 4 (T-09, T-10). **Histórico:** fix3 Fase 3 HECHA y comiteada (`7b17b30`: 15/15 #133-#147, 27 tests, 1.16h, 22.59 EUR; suite 785 passed + 4 rojos Windows). EN VUELO: verificación dirigida lentes B y D en worktrees `scratchpad/B|D` (detached `7b17b30`) sobre `ffdb4cf..7b17b30`. Después: sección «Verificación dirigida fix3» en el ledger; si confirma (0 Critical/Important) → T-07/T-08 `completado`, #111 Resumen (Fase 3 2/2, total 8/10), commit, push → Fase 4 (T-09, T-10). **Histórico:** Fase 3 revisión intento 3 (ÚLTIMO) HECHA y comiteada: 0 Critical, 2 Important (#133 verificación incompleta leída como «sin desfase» por puede_leer/doctor/--check; #134 regresión: la ampliación de ventana de consultar sin except ErrorMCP devuelve 0), 13 Minor (#135-#147). **BUCLE AGOTADO → PARADO, esperando decisión del usuario.** Recomendación: ronda `fix3` acotada (#133, #134 + Minor baratos) + verificación dirigida B+D en worktrees. Si el usuario dice sí: `usage-meter start --artefacto graphiti-memory/T-07-fix3`, implementer opus con la sección intento 3 como brief, luego lentes B+D, cerrar T-07/T-08, #111 Resumen, Fase 4. Worktrees de lentes retirados. **Histórico:** RETOMADO. Push HECHO por SSH (`dab6e68` en origin). EN VUELO: revisión Fase 3 intento 3 de 3 (ÚLTIMO), lentes A+B+C+D en worktrees `scratchpad/A|B|C|D` (detached `dab6e68`), rango `b5f4eb2..dab6e68`; servidor Graphiti real APAGADO hoy. Después: fusionar → sección «intento 3» → si 0 Critical/Important: T-07/T-08 `completado`, #111 Resumen (Fase 3 2/2, 8/10), commit, Fase 4 (T-09, T-10). Si quedan Critical/Important: PARAR y preguntar. **Histórico (2026-09-21 18:40):** SESIÓN CERRADA A PETICIÓN DEL USUARIO («ves terminando, mañana seguimos»). PUNTO DE REANUDACIÓN:** Fase 3 ronda `fix2` HECHA y comiteada (último commit de hoy: `T-07-fix2/T-08-fix2`; 15/15 filas #117-#132, 27 tests, 1.11h, 19.82 EUR; marcador CERRADO, `usage-meter status` sin huérfanos). Suite 8 rutas 758 passed + 4 rojos Windows preexistentes. **PENDIENTE DE PUSH:** la rama tiene 13 commits por delante de `origin/feature/graphiti-memory`; el push falló por permisos (SSH y HTTPS autentican como `hmar12668-sketch`, sin escritura en `daycry/custom-agents`; credencial HTTPS borrada del gestor). Al retomar: `git push origin feature/graphiti-memory` con la cuenta `daycry` o tras dar acceso a `hmar12668-sketch`. **SIGUIENTE PASO DE TRABAJO:** revisión de dos lentes Fase 3 **intento 3 de 3 (ÚLTIMO)** sobre `b5f4eb2..HEAD` — `review-lens-select.py --base b5f4eb2`, worktrees `scratchpad/A|B|C|D` (`git worktree add --detach`, `core.longpaths true` ya activo), lentes con la tabla del intento 2 (#117-#132) + cierre; si 0 Critical/Important → T-07/T-08 `completado`, #111 Resumen (Fase 3 2/2, total 8/10), commit → Fase 4 (T-09 seguridad/aislamiento, T-10 interop/QA/retro) → qa sin UI → documenter → 4-bis → changelog-sync → /retro + retro-gate → spec implementada → PR sobre master. Si al 3.º quedan Critical/Important → PARAR y preguntar. `dev.json` local sigue con `modelos.implementer: opus`. OBJETIVO GLOBAL del usuario (/goal, sigue vigente): implementar TODO el roadmap pendiente en este orden: graphiti-memory → training-data-services → dev-cycle-dataset → brief-budget → plugin-refactor (T-15, T-20..T-22) → project-specialization (F2-F3). Sesión Claude Code de hoy: `b8053ac5-12f5-4c5d-8a31-080cc28d70a3` (`claude --resume <id>`). **Histórico:** Fase 3 revisión intento 2 HECHA (`b5f4eb2`): 0 Critical, 5 Important (#117 post-filtro vocabulario real, #118 versión vigente, #119 presupuesto /doctor por backend, #120 verify paginado bajo tope, #121 recall ventana), 11 Minor (#122-#132; #129 cerrado). EN VUELO: implementer `opus` ronda `fix2` (marcador `graphiti-memory/T-07-fix2` ABIERTO 15:43Z; brief = sección intento 2). Después: cerrar marcador, puertas, commit `T-07-fix2/T-08-fix2`, revisión intento 3 de 3 (ÚLTIMO; lentes en worktrees `scratchpad/A|B|C|D`), si cierra → T-07/T-08 completado, #111 Resumen, Fase 4. Si NO cierra al 3.º → PARAR y preguntar al usuario (regla dura), salvo que solo queden Minor. **Histórico:** Fase 3 fix1 HECHA y comiteada (`59d9e35`, 20/20 gaps #96-#116, 49 tests, 1.14h, 17.11 EUR; suite 8 rutas 731 passed + 4 rojos Windows). EN VUELO: revisión intento 2 de 3 — lentes A+B+C+D (D disparada por ruta `markdown_export.py`) en worktrees `scratchpad/A|B|C|D` (detached `59d9e35`). Después: fusionar → sección «intento 2» en el ledger; si 0 Critical/Important → T-07/T-08 `completado`, #111 Resumen (tokens), commit → Fase 4 (T-09, T-10); si no → fix2 + intento 3 (último). **Histórico:** FASE 3 implementada (`52c899d` T-07, `5bfdcc4` T-08, 1.13h) y REVISADA (intento 1, `c3af10d`): 2 Critical (#96 tombstone de sucesión sirve la versión vigente como invalidado; #97 router pasa config cruda sin group_id derivado → 0 sin caer a local), 7 Important, 12 Minor. T-07/T-08 `en-progreso`. EN VUELO: implementer `opus` ronda `fix1` Fase 3 (marcador `graphiti-memory/T-07-fix1` ABIERTO 14:12Z; brief = sección intento 1 del ledger, filas #96-#116 salvo #111 del orquestador). Después: cerrar marcador, reproducir puertas, commit, revisión intento 2 de 3 (lentes A+B+C en worktrees `scratchpad/A|B|C`, `core.longpaths true` ya puesto), #111 Resumen, Fase 4 (T-09, T-10). **Histórico:** FASE 2 CERRADA:** verificación dirigida (lentes B+C en worktrees separados) confirmó 21/21; 1 Important + 6 Minor nuevos (#89-#95) cerrados en `fix5` (0.51h, 5.19 EUR); T-04..T-06 `completado`, Resumen 6/10, sección «Verificación dirigida — fix4 + fix5» en el ledger, enmiendas en `design.md`. Worktrees de lentes retirados. `dev.json` mantiene `modelos.implementer: opus` para el resto de la iniciativa (decisión del orquestador). SIGUIENTE: Fase 3 (T-07 router `knowledge-find.py --intent`, T-08 capacidad `graphiti` en `capabilities.py` + setup/doctor + INTEROP) → revisión de dos lentes Fase 3 (intento 1 de 3) → Fase 4 (T-09, T-10) → qa sin UI → documenter → 4-bis → changelog-sync → /retro → cierre → PR. **Histórico:** fix4 HECHA y comiteada (`3d8e512`, 2.73h IA medidas, 22.91 EUR, marcador CERRADO): 21/22 filas `corregido (fix4)`, 47 tests nuevos, suite 5 rutas 399 passed. Fix aparte del marketplace de Codex (`policy.authentication` NONE→ON_INSTALL) en `1d4f98f` con CHANGELOG. OBJETIVO ACTIVO del usuario (/goal): implementar TODO el roadmap pendiente (orden: graphiti-memory → training-data-services → dev-cycle-dataset → brief-budget → plugin-refactor T-15/T-20..22 → project-specialization F2-F3). Graphiti (`127.0.0.1:8001`) y Kwipu LEVANTADOS por el usuario: health sano, tools/list = fixture, `add_triplet.required` real confirmado; seguimos sin escribir en el grafo real salvo decisión explícita. EN VUELO: lentes B y C (reviewer opus) en worktrees `scratchpad/lensB` y `scratchpad/lensC` (detached `3d8e512`; borrar con `git worktree remove` al acabar) sobre `1d4f98f..3d8e512`. Después: sección «Verificación dirigida fix4» en el ledger, cerrar #86/Resumen, T-04..T-06 `completado`, `Tiempo IA (fix4)` 2.73h, commit → Fase 3. Los 63 fallos de `tests/` en esta máquina son de entorno Windows (CRLF, `\`, cp1252, chmod, python3 en hooks), no regresiones. Estado previo:** el usuario CONFIRMÓ la opción 1 (ronda `fix4` + verificación dirigida). fix4 EN VUELO:** `dev.json` con `modelos.implementer: {model: opus, effort: high}` (local, ignorado), marcador `usage-meter start --artefacto graphiti-memory/T-05-fix4` ABIERTO a las 10:08Z (cerrarlo con `close` al terminar el implementer; si la sesión se corta, `usage-meter status` lo muestra huérfano), implementer despachado con brief = filas #67-#88 del ledger + reglas. Línea base antes de fix4: 327 passed, 1 skipped (5 rutas), ledger-lint 0/4, servidor Graphiti cerrado. Tras el implementer: puertas → lentes B y C en copias aisladas del árbol (scratchpad, `git worktree` no: dev.json worktree=false; copia `git archive`/`cp`) → cerrar filas, T-04..T-06 `completado`, Resumen (#86), `Tiempo IA (fix4)`, sección «verificación dirigida fix4» en el ledger, commit. **Estado previo:** PARADO A PETICIÓN DEL USUARIO tras escribir el intento 3. Decisión recomendada (registrada en el ledger, bucle
> agotado → confirmar con el usuario al retomar): **ronda `fix4` + verificación dirigida** (B y C sobre lo corregido, en
> copias aisladas del árbol), implementer con `opus` (poner `"modelos": {"implementer": "opus"}` en `.claude/dev.json`),
> marcador `usage-meter start --artefacto graphiti-memory/T-05-fix4`, brief = las 22 filas #67-#88 con sus arbitrajes +
> los repros del scratchpad de esta sesión (`repro_d1/d2b/d3/d4/d7.py`, probes `p3/p4/p5/p7/p9/p10/p11`; se pierden
> al cambiar de sesión: reproducir desde la descripción de la fila). Después: cerrar T-04..T-06, Resumen, `Tiempo IA
> (fix4)` → Fase 3 (T-07 router `knowledge-find.py --intent`, T-08 capability `graphiti`) → Fase 4 → qa sin UI →
> documenter → 4-bis → changelog-sync → /retro → cierre → PR sobre master.
> Reglas: `PATH="$PWD/.venv/Scripts:$PATH"` y `python` (+ `-p no:cacheprovider`); ningún gap `corregido` sin test
> dedicado nombrado; nada de escrituras contra el Graphiti real (`127.0.0.1:8001`); `export-interop.py` en Windows
> reescribe EOL (revertir los limpios); modelos por `model-tier.py` (implementer sonnet, reviewer opus).

---

## Histórico (2026-09-19 tarde)

> **2026-09-19 (tarde) — TRES RAMAS EN VUELO; leer este bloque antes que el resto (el resto es histórico).**
>
> **PUNTO DE REANUDACIÓN (2026-09-19, 13:30; el usuario pidió cerrar aquí tras los commits + push).**
> Consejo dado al usuario: mergear PR #9 ya; release SOLO tras verificar la ronda fix3 del fix de Jira y mergearla;
> graphiti-memory no entra en la próxima release.
>
> - **`fix/jira-review-comments`** (worktree `jira-fix`) → **PR #10 en BORRADOR sobre master** (`7f4942a`, con changelog): fix3 `c7e6b20` hecho, verificación dirigida pendiente. Revisión intento 3 (`2e71dd4`) NO cerrable por el Critical #20
>   (`aprobado`/brief miraban UNA sección por intento; un Critical cruzado `T-04/T-07` en otra fase no bloqueaba Done).
>   Decisión del orquestador: ronda `fix3` (unión de todas las filas que citan la tarea para `aprobado` y el brief;
>   publicación por sección cabecera-primero declarada) + verificación dirigida. **Siguiente paso: verificación dirigida
>   de fix3 (FXP, M2b, aceptación sobre el ledger real en `test_jira_flow.py`, Verificación de T-03)** → `changelog-sync
>   --only jira-review-comments` (Fixed) → PR sobre master (con #9 mergeado) → release.
> - **`feature/graphiti-memory`**: Fase 2 revisión intento 2 (`c06e249`, 16 nuevos, 3 Critical) → ronda fix2 `92f1bc6`
>   cierra los 3 Critical (#51 SSE por `id`, #52 multi-IP/`localhost`, #53 IPv4-mapeada) + #54-#56, #58, #62-#66 con 25
>   tests dedicados; **quedan #57 parcial (test redirect `.internal`/IMDS), #61 sin test, #59/#60 (ledger/docs: Verificaciones
>   con cifras reales, criterio de T-05, etiquetas «pre-fix1», CONVENTIONS ES/EN + esquema para `provider.model`/userinfo,
>   residual de #40 en README/design) y las 12 parciales del intento 1 (#32-#50) por cerrar en el ledger.** Siguiente:
>   ronda fix3 + intento 3 (último) con lentes A+B+C → Fase 3 (T-07, T-08) → Fase 4 → qa sin UI → documenter → 4-bis → cierre.
>   Regla: ningún gap `corregido` sin test dedicado nombrado en su Evidencia. `.claude/dev.json` (`tdd: true`) es local e
>   ignorado: si desaparece al mezclar, restaurarlo desde `ks-fix/.claude/dev.json`.
>
> 1. **`feature/knowledge-services` → PR #9 a master: CI VERDE (run 35423149251), `CLEAN MERGEABLE`, sin mergear** (el
>    merge lo decide el usuario). Worktree `C:\Users\46066917X\ks-fix`. Cinco commits de corrección de CI encima del cierre:
>    `11221b6` (hooks/«knowledge»), `1b392db` (corpus con `approved/`, gap37 agnóstico, `.claude/dev.json` fuera del índice
>    e ignorado: había entrado por error en `3dbdd88` y rompía `test_tdd_false_o_ausente_no_inyecta`), `eea751f` (fixture
>    gap37), `e8a406f` (bench p95 adaptativo, flaky), `2dca4c0` (**cabeceras «Revisión de dos lentes — intento N: …»
>    normalizadas**: con paréntesis tras N no casan con `REVISION_HDR_PATTERN` y jira-flow/task-brief no las veían; bytes de
>    control fuera del ledger). Comentario resumen en el PR. **Pendiente del usuario:** reindexar el stack Kwipu y `git stash drop stash@{0}`.
> 2. **`fix/jira-review-comments`** (worktree `C:\Users\46066917X\jira-fix`, rebasada sobre `2dca4c0`, commits `c71f484`
>    T-01+T-02 y `9437a4d` T-03+T-04, SIN push): encargo del usuario «los reviews no añaden comentarios en Jira». Causa 1:
>    nadie era dueño de `jira-flow.py --event revision|gaps` (skill decía «orquestador», dev-cycle decía «adversarial-review»,
>    review-publish decía «reviewer», ROLES decía «orquestador/implementer») → dueño único = skill `adversarial-review` §6
>    (comando completo), tabla de dev-cycle, review-publish y ROLES alineados, test `tests/test_review_jira_owner.py`. Causa 2:
>    `seccion_revision` elegía la PRIMERA sección con ese nº de intento (en ledgers multifase publicaba «sin gaps» falso) →
>    elige por tarea, cae en la última; `ledger-lint` avisa de cabeceras que no casan. Ledger
>    `docs/roadmap/2026-09-19-jira-review-comments/tasks.md` 4/4 `completado`. Revisión intento 1 (`b720a81`): 13 gaps (2 Critical:
>    la selección elegía la PRIMERA sección y `aprobado` usaba el `max()` global) → ronda fix1 (`1170af5` parser único
>    `secciones_revision`/`seleccionar_seccion` en `ledger-lint.py` usado por jira-flow y task-brief; `42e86be` docs: FLOWS ES/EN,
>    jira-sync SKILL, README/plantilla de shared, CONTRACTS E19). **En curso: intento 2 (verificación dirigida).** Después: sección de revisión en el ledger, `changelog-sync --only
>    jira-review-comments` (Fixed), push, PR (base `feature/knowledge-services` hasta que #9 se mergee; luego master).
> 3. **`feature/graphiti-memory`** (árbol principal; `4a672a4` = merge de knowledge-services con los fixes de CI):
>    `/dev-cycle graphiti-memory completo`. **Fase 1 (T-01..T-03) HECHA** (`0c70937`, `5a32012`, `7d67a4c`). **Revisión Fase 1
>    intento 1** (`2ffc69f`): 15 gaps (0 Critical, 7 Important, 8 Minor) + enmienda 2026-09-19 en `design.md` (config anidada
>    estricta, `group_id` sin default, guardarraíl local/privado, `telemetria`) + criterio `hash` movido de T-01 a T-05. Ronda
>    fix1 HECHA (`20d44a6` T-01-fix1, `3bb4bdb` T-02-fix1; 15/15 según el implementer). Intento 2 (`0073415`): 11 nuevos (3 Important) → fix2 (`e19d35a`, `b315943`). Intento 3 (`f5da093`): 11/11, 4 Minor →
>    **bucle Fase 1 CERRADO**; los 3 Minor restantes cerrados en `92cdde8`. **Fase 2 (T-04 adaptador `graphiti.py` cliente MCP,
>    T-05 plan/apply, T-06 verify/rebuild/revoke) HECHA en `616f0e3`** (33 tests con servidor MCP falso; validación en vivo SOLO
>    lectura contra `127.0.0.1:8001/mcp`; prohibido escribir en el servidor real). **En curso: revisión Fase 2 intento 1 con lentes
>    A + B(+D) + C (C a demanda del orquestador: cliente HTTP/DNS/`clear_graph`).** Siguiente: Fase 3 (T-07 router, T-08 capability) → Fase 4 (T-09, T-10) → qa sin UI →
>    documenter → 4-bis → cierre → PR apilado sobre #9. Validar en vivo contra el Graphiti real cuando exista T-04.
> 4. **Inventario de pendientes (petición 2 del usuario, ya hecho, para decidir):** brief-budget 0/6 (en-progreso, ninguna
>    iniciada), plugin-refactor 17/21 (T-15 en-progreso; T-20 revisión por tramos, T-21 corrección, T-22 cierre),
>    project-specialization 3/22, graphiti-memory 3/10 (en vuelo), dev-cycle-dataset 0/8 y training-data-services 0/11
>    (borrador, dependen de knowledge-services).
>
> Reglas de esta sesión: `PATH="$PWD/.venv/Scripts:$PATH"` y `python`; el modo auto deniega tocar el stack docker y
> `git stash drop`; agentes nuevos (`knowledge-curator`) no existen en el plugin instalado (1.20.2): despachar con
> general-purpose leyendo `agents/<nombre>.md`; `export-interop.py` en Windows reescribe los 50 ficheros con otro EOL
> (revertir los que `git diff --quiet` dé limpios).

---

## Histórico (2026-09-18 → 2026-09-19 mañana)

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
> 10/13. **Fase 4 HECHA** (7d654e2 T-10, 22d09e7 T-11, aed7584 T-12; + 32e98d8 T-08-fix4 manifiestos): **13/13**.
> Suite completa una vez: 42 rojos, todos preexistentes de Windows salvo `test_manifests` (arreglado en 32e98d8). Queda un
> `git stash@{0}` inocuo del implementer (no pudo `stash drop`: pide autorización). **Revisión Fase 4 intento 1** (c26461a):
> 0 Critical, 10 Important, 10 Minor (#141–#160; incl. #150 = arreglar el YAML de LES-016 que bloquea `release.py`).
> Ronda fix1 hecha (8c96d74..f023e56): 20/20; **`lint_plugin` 0 errores** (LES-016 arreglado). **Intento 2 Fase 4** (c7bc62d):
> 7 documentales cerrados por el orquestador (3528f11) + 9 nuevos de la Lente B (#168–#176; 2 Important en la red de hooks).
> Ronda fix2 hecha (a5a8046, 05d3bf4, bd63112): 9/9. **Intento 3 Fase 4** (fb34ac9): 9/9 cerrados + 9 nuevos (#177–#185;
> 2 Important: cita de test retirado en el ledger y regresión en `_lineas_de_codigo` del test de hooks). Decisión del
> orquestador: ronda fix3 hecha (d522234) y **verificada → bucle Fase 4 CERRADO**. Las 4 fases revisadas (185 gaps).
> **qa sin UI VERDE** (e890478: 480 passed, matriz CA-01..17 verificada, `testing/qa-report.md`+pdf). **documenter en curso**
> HECHO (baa3339: doc ya coherente; 3 candidatos en `candidates/pending/`). **Fase 4-bis en curso**: `knowledge-curator`
> no existe en el plugin instalado (1.20.2) → despachado como subagente genérico leyendo `agents/knowledge-curator.md`.
> Fase 4-bis HECHA (fc568a7: 3 aprobados en `approved/`). **Cierre Fase 6 HECHO**: plan/tasks `completado`, changelog-sync
> (Added), retro + fila CALIBRATION (estimado) + candidato de lección de proceso, retro-gate ABIERTA, spec `implementada`,
> merge origin/master limpio, **push + PR #9** (https://github.com/daycry/custom-agents/pull/9). CI 1.a pasada ROJA solo en
> Linux (`test_hooks_shell::…sin_knowledge…` prohibía la subcadena «knowledge», que ahora trae el índice de piezas): arreglado
> en `11221b6` (worktree `C:/Users/46066917X/ks-fix` sobre la rama del PR; bórralo con `git worktree remove` al acabar) y
> relanzada. **Pendiente: mezclar `11221b6` en `feature/graphiti-memory` cuando el implementer de la Fase 1 termine.**
> **knowledge-services CERRADA.** Siguiente (orden del usuario): graphiti-memory (rama `feature/graphiti-memory` desde este
> HEAD; PR apilado sobre #9) → con master estable, repaso de tareas pendientes de todos los planes → corrección de los
> comentarios de revisión en Jira (dueño único de `jira-flow.py revision/gaps`; ver memoria) →
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
> comentario con el resultado de la verificación ni de los N intentos (pistas: en aquel momento `jira-flow.py`
> eventos `revision`/`gaps` con `--intento N` eran «del orquestador» en `commands/dev-cycle.md` y a la vez
> «comentario FINAL en Jira, Paso 9» en la skill `adversarial-review`: hueco de dueño). **RESUELTO** por la
> iniciativa `docs/roadmap/2026-09-19-jira-review-comments/`: la skill `adversarial-review` es ahora el dueño
> único (Paso 7 de `jira-sync`, no Paso 9; firma `--actor reviewer`), `dev-cycle.md` ya no dice «del orquestador»
> y `tests/test_review_jira_owner.py` guardarraíla que ningún fichero vivo reabra otro dueño. Requisito
> transversal: todo debe funcionar en Claude Code, Codex y OpenCode.

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
