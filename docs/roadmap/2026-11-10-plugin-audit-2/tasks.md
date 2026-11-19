---
generacion:
  inicio: 2026-11-10T14:59:35Z
  fin: 2026-11-10T15:11:05Z
  fuente: medido
  fuente_id: src-d2ceb5c719af848b4c213bb2d521d0f003976923acb613d7512912ccbeb6a09e
  ventana_id: win-7439aa476c2e4d7d9e3305e4ad55af80
  revision_medicion: 1
  medicion_persistida: true
  tokens_reales: { entrada: 96, salida: 91884, cache_creacion: 111999, cache_lectura: 6949813 }
  eur: 3.48
  horas_ia: 0.38
  duracion: 23m
  ratio_usado: 531798.5
  tokens_procedencia: transcript
  tokens_cobertura: completa
  coste_procedencia: estimado_tarifa
  coste_cobertura: completa
  tarifa_verificada_el: 2026-10-20
  avisos: ["CALIBRATION: filas marcadas (estimado) fuera de la mediana (x8)"]
  # ventana compartida con improvement-plan.md
tasks: plugin-audit-2
estado: en-progreso
creado: 2026-11-10
verificacion: obligatoria
changelog: Changed
---

# Segunda auditoría del plugin: defectos, retirada, tokens, código, alcance e higiene

> Ledger canónico de progreso. Fuente única. Autorización: el usuario autorizó la ejecución del plan el 2026-11-11 («continua con la implementación de los planes»), en la rama `feat/plugin-audit-2` desde `fb3bb37` (v3.3.0). Decisiones del 2026-11-10 en el plan; no queda ninguna pendiente: la única puerta es la condición de T-32 sobre el veredicto de T-31.

[Plan](improvement-plan.md) · [Análisis](analysis.md)

> **Puertas comunes.** *Runtimes* (todo funciona en Claude Code, Codex y OpenCode; la cierra toda tarea que toque un agente, comando, skill, hook, el instalador o un manifiesto): `python scripts/export-interop.py --check` → exit 0 · `pytest -q tests/test_export_interop.py tests/test_plugin_root_resolution.py tests/test_native_role_context.py tests/test_native_guardrail_dispatch.py tests/test_native_prefilter_parity.py` → verde · `node --test tests/opencode-plugin.test.mjs tests/codex-native-install.test.mjs tests/installer.test.mjs tests/hook-runtime.test.mjs` → verde. *Tokens* (fase 3 y toda tarea sobre `agents/`, `commands/` o `skills/`): puertas de tokens (cabecera) → verde (vía rápida ≥ 6.000; `agents/evaluator.md` ≤ 15.513 bytes en LF; `--diet-check` sin párrafos perdidos). *Verificación manual*: lo que ninguna suite demuestra es un paso `lectura (manual…)` de su tarea y consta en «acciones del usuario» del plan (M-A…M-F). `context-footprint.py` estima (caracteres/4); línea base tras la fase 2.

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — Defectos | 7 | 8 | 87.5% | 0 / 16h | 0 / 5.0h | 0 / 1.25h | 0 / 1090k |
| Fase 2 — Retirada decidida (Kwipu, Graphiti, plugin-dev) | 4 | 4 | 100% | 0 / 32h | 0 / 7.9h | 0 / 1.98h | 0 / 2100k |
| Fase 3 — Tokens | 0 | 11 | 0% | 0 / 30h | 0 / 8.2h | 0 / 2.05h | 0 / 2260k |
| Fase 4 — Simplificación del código | 0 | 8 | 0.0% | 0 / 34.5h | 0 / 8.5h | 0 / 2.12h | 0 / 2470k |
| Fase 5 — Alcance y entrenamiento | 0 | 5 | 0% | 0 / 26h | 0 / 6.5h | 0 / 1.62h | 0 / 1800k |
| Fase 6 — Higiene del roadmap | 0 | 3 | 0% | 0 / 10h | 0 / 2.5h | 0 / 0.62h | 0 / 750k |
| **TOTAL** | **11** | **39** | **28.2%** | **0 / 148.5h** | **0 / 38.6h** | **0 / 9.65h** | **0 / 10470k** |

Supervisión = 25 % de las horas IA (se suma por fase). Estimaciones BASE (el +20 % está en el plan); tokens al precio de `.claude/rates.json`.

---

## Fase 1 — Defectos

**Estado**: borrador · **Est.**: 15h humanas · **Real**: — · 750 € · 1090k tokens

### T-01 — Aviso falso de progress-report (1.1)

- **Descripción**: `session-snapshot` marca como «ilegible (redirected_path)» todo lo que `docs/roadmap/` contiene y no es carpeta (`CALIBRATION.md`, `README.md`). Hay que saltar lo que no sea directorio y reservar el aviso para carpetas realmente redirigidas.
- **Changelog**: El aviso de arranque ya no acusa de ilegibles a CALIBRATION.md y README.md del roadmap.
- **Estado**: completado
- **Cerrada**: 2026-11-10
- **Tiempo humano**: est. 1.5h · real —
- **Tiempo IA (ejec.)**: est. 0.4h · real 0.1h (estimado)
- **Archivos**: `agent-kits/shared/progress-report.py` (líneas 479-481 y 495-497), `agent-kits/shared/test_progress_report.py`
- RED: test_session_archivos_sueltos_no_avisan_ni_entran_en_la_firma falló con AssertionError: ['CALIBRATION.md: tasks.md ilegible (redirected_path)', 'README.md: tasks.md ilegible (redirected_path)'] · 2026-11-10
- **Evidencia**: GREEN: `1 passed, 45 deselected`; el arreglo salta en silencio los ficheros regulares (`S_ISREG` sin redirección) antes de la firma; enlaces/junctions siguen como «redirected».
- **Runtimes**: Sin diferencia: `progress-report.py` lo ejecutan los lanzadores de los tres runtimes.
- **Verificación**:
  - `pytest -q agent-kits/shared/test_progress_report.py -k archivos_sueltos` → `1 passed` (rojo antes del arreglo: el test nuevo falla)
  - `pytest -q agent-kits/shared/test_progress_report.py` → sin regresiones
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**
- [x] Un fichero suelto en `docs/roadmap/` no genera aviso ni entra en la firma de la caché.
- [x] Una carpeta realmente redirigida sigue avisando (tests existentes intactos).

### T-02 — Invocar skills sin depender de la herramienta Skill (1.2)

- **Descripción**: El cuerpo de `implementer` ordena invocar `tdd`, `dependency-upgrade` y `debug-root-cause` y `qa` declara `to-pdf`, pero su `tools:` no incluye `Skill`, concepto solo de Claude Code. Solución común: el cuerpo da siempre la ruta `skills/<x>/SKILL.md` como vía que no depende de la herramienta (patrón de `nemesis`).
- **Changelog**: Los agentes dicen dónde leer cada skill y funcionan igual en los tres runtimes.
- **Estado**: en-progreso
- **Tiempo humano**: est. 3h · real —
- **Tiempo IA (ejec.)**: est. 0.7h · real 0.4h (estimado)
- **Archivos**: `agents/implementer.md`, `agents/qa.md`, `tests/test_agent_tools_skill.py` (nuevo), `tests/test_export_interop.py`, `tests/test_f4fix2_misc.py` (fix1), `docs/{,en/}TOKEN-EFFICIENCY.md` (el commit `14adaca` publica ahí el tamaño de implementer y el ahorro de la vía rápida; fix1, gap 8), `docs/agents/implementer.md`, `docs/agents/qa.md`, `evals/cases/agent-implementer.json`, `interop/**` (regenerado)
- **Evidencia**: GREEN: `tests/test_agent_tools_skill.py` → `12 passed` (recorre `agents/*.md`; implementer y qa llevan ahora la ruta `skills/<x>/SKILL.md` de cada skill que ordenan invocar); `Skill` NO se añade a `tools:` (el criterio no depende de ella). Puertas de runtimes: `export-interop.py --check` → `88 ficheros al día`; `pytest -q` de las 5 suites de la cabecera + `test_agent_tools_skill.py` → `112 passed`; `node --test` opencode-plugin, codex-native-install y hook-runtime → verde; `installer.test.mjs` no termina en Windows en 900 s (carga de la máquina): verificado en Linux (`python:3.11-slim`, Node 22, HEAD `14adaca`): `node --test --test-concurrency=2 tests/*.test.mjs` → `tests 537 · pass 512 · fail 0` (incluye `installer.test.mjs`, `opencode-plugin`, `codex-native-install`, `hook-runtime`).
- **Pendiente (usuario)**: M-A (sesión real de Claude Code): comprobar si un agente sin `Skill` en `tools:` puede invocar una skill; en Codex y OpenCode, que sigue la skill leyendo `skills/tdd/SKILL.md` por su ruta. Hasta entonces el 2.º criterio queda sin marcar y la tarea `en-progreso`.
- **Runtimes**: Claude: `Skill` en `tools:` opcional; Codex: agente sin `tools`, skill por `$custom-agents:X` (`docs/INTEROP.md:79`); OpenCode: `skill: allow` fijo (`scripts/export-interop.py:589`). La ruta del `SKILL.md` vale en los tres.
- **Verificación**:
  - `pytest -q tests/test_agent_tools_skill.py` → `passed` (rojo antes: implementer y qa nombran skills sin ruta del `SKILL.md`)
  - `pytest -q tests/test_export_interop.py -k skill` → los agentes generados de Codex y OpenCode conservan la ruta; `Skill` en `tools:` (si se añade) no altera `permissions` ni el agente de Codex
  - puertas de runtimes (cabecera) → verde
  - lectura (manual, sesión real; M-A) → en Claude Code se anota si un agente sin `Skill` puede invocar una skill; en Codex y OpenCode el agente sigue la skill leyendo `skills/tdd/SKILL.md` por su ruta

**Criterios de aceptación**
- [x] Todo agente cuyo cuerpo ordena invocar una skill da la ruta de su `SKILL.md`; el test recorre `agents/*.md`.
- [ ] `Skill` en `tools:` solo se añade si una prueba en sesión real de Claude Code la necesita (anotada); el criterio no depende de ella.


RED: `tests/test_agent_tools_skill.py::test_toda_skill_que_el_agente_ordena_invocar_lleva_su_ruta[implementer.md|qa.md]` falló con AssertionError: implementer.md ordena invocar [adversarial-review, debug-root-cause, dependency-upgrade, tdd, unit-tests] y qa.md [to-pdf, unit-tests] sin dar skills/<x>/SKILL.md · 2026-11-11.

**fix1 (revisión de dos lentes, intento 1: gaps 2a, 8 y 9)** — clave de medición `plugin-audit-2/T-02-fix1`.

RED: `tests/test_f4fix2_misc.py::test_f4fix2_5_the_published_figures_match_context_footprint_on_head` falló con `AssertionError: ('agents/implementer.md', '29.280', 'testing/tokens.md')`: exigía que el registro CERRADO `docs/roadmap/2026-11-09-plugin-audit-remediation/testing/tokens.md` citara los tamaños de HEAD · 2026-11-11.

GREEN (gap 2a): no es una puerta relajada, es un registro inmutable: ese fichero fija las cifras del día en que se cerró la iniciativa anterior y `CLAUDE.md` prohíbe reescribir los registros de `docs/roadmap/`; HEAD cambia con cada fase, así que compararlos solo podía fallar. El test ya no lee el registro (solo si se pide a propósito con `F4FIX2_TOKENS_MD=<ruta de un registro vivo>`) y conserva TODAS las comprobaciones de `docs/TOKEN-EFFICIENCY.md` y `docs/en/TOKEN-EFFICIENCY.md` contra HEAD y la del ahorro de la vía rápida (≥ 6.000). Test dedicado `test_f4fix2_5_does_not_read_the_closed_dated_record` (un `tokens.md` obsoleto en `testing/` no lo hace fallar). `pytest -q tests/test_f4fix2_misc.py` → `7 passed`. Gap 8: `docs/{,en/}TOKEN-EFFICIENCY.md` figuran ya en `Archivos`. TDD n/a: prosa/ledger (el gap 8 es un campo `Archivos` del ledger; no hay código que un test pueda hacer fallar; `scope-check.py` es su comprobación). Añadido en el intento 2 (gap 8).

Gap 9 (Verificación 2): `pytest -q tests/test_export_interop.py -k skill` → `5 passed, 48 deselected` (3 previos + `test_los_agentes_generados_conservan_la_ruta_skill_md_de_cada_skill[implementer|qa]`, nuevo: los agentes generados de Codex y OpenCode conservan cada `skills/<x>/SKILL.md` del cuerpo; no había ningún test que vigilara esa ruta en lo generado). TDD n/a para ese test: caracteriza lo ya generado (pasa desde el primer momento); el detector se comprueba contra una mutación en la propia prueba (sin `SKILL.md` el conjunto deja de incluir la ruta). `export-interop.py --check` → `88 ficheros al día`.

### T-03 — Comando y skill confluence-pull con el mismo nombre (1.3)

- **Descripción**: `commands/confluence-pull.md` y `skills/confluence-pull/SKILL.md` (`user-invocable: true`) comparten nombre, colisión propia de Claude Code (Codex ya antepone `custom-agents-` al adaptador, `export-interop.py:559-572`). Se borra el comando y el linter falla si un comando y una skill `user-invocable` colisionan. T-35 retirará después la skill (ver T-35).
- **Changelog**: Un solo confluence-pull: se retira el comando duplicado y el linter vigila la colisión.
- **Estado**: completado
- **Cerrada**: 2026-11-11
- **Tiempo humano**: est. 2h · real —
- **Tiempo IA (ejec.)**: est. 0.5h · real 0.4h (estimado)
- **Archivos**: `commands/confluence-pull.md` (borrar), `scripts/lint_plugin.py`, `tests/test_lint_plugin.py`, `agent-kits/shared/modules.json`, `docs/README.md`, `docs/{,en/}FLOWS.md`, `CLAUDE.md`, `evals/cases/command-confluence-pull.json`, `interop/**` (regenerado) · añadidos por la nota de alcance: `tests/test_codex_command_transport.py` (el adaptador `custom-agents-confluence-pull` ya no existe), `README.md`, `README.es.md` (fila del comando, insignia y recuento 16→15), `docs/INSTALL.md`, `docs/en/INSTALL.md`, `docs/guides/atlassian.md`, `docs/reference/atlassian.md` (citaban `/confluence-pull` como comando: el linter de citas lo avisa), `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`, `.codex-plugin/plugin.json` (lista «Comandos:»)
- **Evidencia**: GREEN: `pytest -q tests/test_lint_plugin.py -k colision_comando_skill` → `2 passed` (el error de colisión + el caso negativo con `user-invocable: false`); `python scripts/lint_plugin.py` → `10 agentes · 0 errores · 16 avisos` (los mismos 16 de antes; el error real `command confluence-pull: colisión…` desapareció al borrar el comando); `python evals/check.py` → `59 ficheros · 227 casos … 0 errores`. Puertas de runtimes: `export-interop.py --check` → `88 ficheros al día` (desaparecen los 3 ficheros del adaptador Codex y el comando de OpenCode); `pytest -q` de las 5 suites de la cabecera + `test_codex_command_transport`, `test_module_selection`, `test_install_profiles`, `test_integration_adapters`, `test_integration_decoupling`, `test_lint_plugin`, `test_readme_badges` → `172 passed, 1 skipped`; `node --test tests/module-selection.test.mjs` → `pass 6`. Una skill se considera invocable salvo `user-invocable: false` (por defecto lo es en Claude Code). `confluence-pull` se sigue invocando como skill.
- **Runtimes**: Claude: se borra el duplicado; Codex: desaparece `custom-agents-confluence-pull` (queda `$custom-agents:confluence-pull`); OpenCode: desaparece `/confluence-pull` (queda la skill).
- **Verificación**:
  - `pytest -q tests/test_lint_plugin.py -k colision_comando_skill` → `1 passed` (rojo antes)
  - `python scripts/lint_plugin.py` → 0 errores · `python evals/check.py` → exit 0
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**
- [x] `commands/confluence-pull.md` no existe y `modules.json` no lo lista.
- [x] El linter da error si un nombre de comando coincide con el de una skill `user-invocable`.
- [x] Ninguna referencia viva al comando; los registros fechados no se reescriben.


RED: `tests/test_lint_plugin.py::test_colision_comando_skill_es_error` falló con assert 0 == 1: el linter no marca la colision de commands/duplo.md con la skill invocable duplo (exit 0, 0 errores) · 2026-11-11.

**fix1 (revisión de dos lentes, intento 1: gaps 2b y 15)** — clave de medición `plugin-audit-2/T-03-fix1`.

RED: `pytest -q tests/test_lint_plugin.py -k colision` → `3 failed, 2 passed` (los tres nuevos): `test_colision_comando_skill_se_busca_por_name_y_no_por_carpeta` (una carpeta `otra-carpeta` con `name: duplo` choca con `/duplo` y el linter daba exit 0), `…_no_salta_si_name_es_otro_aunque_la_carpeta_coincida` (carpeta `duplo` con `name: distinta` daba un falso error) y `…_con_bom_y_user_invocable_false_no_cuenta_como_invocable` (el BOM escondía el frontmatter y la skill se daba por invocable) · 2026-11-11.

GREEN (gap 15): `_lint_colision_comando_skill` recorre las skills, lee con `utf-8-sig` y toma el `name:` del frontmatter (la carpeta solo si falta). `pytest -q tests/test_lint_plugin.py -k colision` → `5 passed`; `python scripts/lint_plugin.py` → `10 agentes · 0 errores · 16 avisos`.

Gap 2b — (RESUELTO por T-38, 2026-11-12: las ediciones de `output/pdf/` se regeneraron con el generador del repo y `check-handbook` y `test_npm_payload` salen en verde; ya no hay rojo conocido. Lo que sigue es el registro histórico.) ROJO CONOCIDO, pendiente de una acción del USUARIO (no se relaja la puerta ni se tocan los PDF): `python scripts/check-handbook.py` → exit 1 con
```
check-handbook: source_changed:docs/guides/atlassian.md
check-handbook: source_changed:docs/reference/atlassian.md
check-handbook: source_changed:agent-kits/shared/modules.json
```
Los tres ficheros fuente cambiaron al retirar el comando `confluence-pull` (commit `efd60b0`, esta tarea) y las ediciones del manual `output/pdf/*` no se regeneran desde el repo (no hay generador). Acción del usuario: regenerar las ediciones de `output/pdf/*` y volver a ejecutar el script. La fase 2 cambiará más fuentes del manual: conviene regenerar una sola vez al cerrar la iniciativa. Hasta entonces quedan en rojo, por esta única causa, DOS comprobaciones de la CI: el paso «Manual PDF y fuentes coherentes» (`check-handbook`) y, en el paso pytest, `tests/test_npm_payload.py::test_npm_contains_pdf_editions_linked_from_its_readme` (lee los mismos `output/pdf/*.manifest.json`; corrección del intento 2, gap 7).

### T-04 — Contradicciones de prosa en pm-cycle, dev-cycle y nemesis (1.4, 1.6, 1.7)

- **Descripción**: `pm-cycle` dice que `architect` escribe el ADR (solo lo propone); `dev-cycle` no aclara quién implementa en el perfil normal; `nemesis` declara `Agent` pero desde `/dev-cycle` no puede anidar y no tiene alternativa en serie. Se alinea la prosa con lo que ya ocurre.
- **Changelog**: Los comandos y el agente de seguridad dicen lo que hacen: el ADR se propone, el implementer implementa y nemesis tiene alternativa en serie.
- **Estado**: completado
- **Cerrada**: 2026-11-11
- **Tiempo humano**: est. 2h · real —
- **Tiempo IA (ejec.)**: est. 0.5h · real 0.2h (estimado)
- **Archivos**: `commands/pm-cycle.md`, `commands/dev-cycle.md`, `agents/nemesis.md`, `docs/agents/nemesis.md`, `docs/{,en/}FLOWS.md`, `interop/**` (regenerado)
TDD n/a: prosa de dos comandos y un agente, sin código testeable; la puerta es determinista (test_source_snapshot, test_dev_cycle_split, test_skill_size, test_context_footprint).
- **Evidencia**: Prosa, con puertas deterministas: `pytest -q agent-kits/shared/test_source_snapshot.py tests/test_dev_cycle_split.py tests/test_skill_size.py agent-kits/shared/test_context_footprint.py` → `96 passed, 1 skipped`. Ahorro de la vía rápida medido con la fórmula del test (LF): 15.066 − 9.054 = **6.012** tokens (≥ 6.000; margen estrecho, lo ensancha T-16); `agents/evaluator.md` = 15.465 bytes en LF (≤ 15.513). `--diet-check` es de `tests/test_skill_size.py` y solo recorre skills (esta tarea no toca ninguna); las comprobaciones por párrafo de `dev-cycle` son las de `test_dev_cycle_split.py::test_no_original_paragraph_is_lost` (en el `96 passed`). `export-interop.py --check` → `88 ficheros al día`. Cambios: `pm-cycle` (pasada 2 de architect) ahora dice que el ADR se PROPONE con `knowledge-curation.py propose` y lo aprueba el curator (misma redacción que `phase2-planning.md`); `dev-cycle` nombra un solo implementador (el `implementer` nativo; con el bundle copiado el agente homónimo; nunca el hilo principal) y el perfil normal implementa con el mismo `implementer`; `nemesis` gana el modo en serie (8 especialistas uno a uno, «Modo en serie» en el informe) cuando no puede despachar subagentes.
- **Runtimes**: Prosa común; se regenera en los tres (cabecera de orquestación `export-interop.py:107`); nemesis gana una alternativa en serie donde no hay anidado.
- **Verificación**:
  - `pytest -q agent-kits/shared/test_source_snapshot.py tests/test_dev_cycle_split.py tests/test_skill_size.py` → verde
  - `python scripts/lint_plugin.py --diet-check` (según `docs/CONVENTIONS.md`) → 0 párrafos perdidos
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**
- [x] `pm-cycle` repite la redacción de `phase2-planning.md` (architect propone, el curator aprueba).
- [x] `dev-cycle` nombra un solo implementador por perfil.
- [x] `nemesis` describe el modo en serie cuando no puede despachar.

**fix1 (revisión de dos lentes, intento 1: gap 11)** — puerta de runtimes completa de T-04, ejecutada sobre HEAD tras los fix1 (clave `plugin-audit-2/T-04-fix1`; prosa: TDD n/a como arriba):
- `python scripts/export-interop.py --check` → `88 ficheros al día` (exit 0).
- `pytest -q tests/test_export_interop.py tests/test_plugin_root_resolution.py tests/test_native_role_context.py tests/test_native_guardrail_dispatch.py tests/test_native_prefilter_parity.py` → `102 passed in 101.61s`.
- `node --test tests/opencode-plugin.test.mjs tests/codex-native-install.test.mjs tests/hook-runtime.test.mjs` (Windows) → `tests 68 · pass 68 · fail 0` (exit 0). `tests/installer.test.mjs` no termina en Windows por la carga de la máquina (ver T-02): su resultado consta en la verificación en Linux de T-23 (`node --test --test-concurrency=2 tests/*.test.mjs`).

### T-05 — Descriptions que mienten y temporal no portable (1.5, 1.10)

- **Descripción**: `/roadmap-metrics` y `/roadmap-brief` se declaran «solo lectura» pero escriben (`docs/roadmap/metrics.md`, `/tmp/roadmap.json`, `/tmp/metrics.md`; `/tmp` no existe en Windows nativo). La description de `plugin-panel` dispara con «dashboard» a secas, que choca con `roadmap-dashboard`.
- **Changelog**: Los comandos de informe dicen qué escriben y usan un temporal portable; plugin-panel solo se activa con disparadores con sujeto.
- **Estado**: completado
- **Cerrada**: 2026-11-11
- **Tiempo humano**: est. 1.5h · real —
- **Tiempo IA (ejec.)**: est. 0.4h · real 0.2h (estimado)
- **Archivos**: `commands/roadmap-metrics.md`, `commands/roadmap-brief.md`, `skills/plugin-panel/SKILL.md`, `evals/cases/command-roadmap-metrics.json`, `evals/cases/command-roadmap-brief.json`, `evals/cases/skill-plugin-panel.json`, `docs/agents/ROLES.md`, `interop/**` (regenerado)
TDD n/a: prosa de descriptions y de dos comandos; la puerta determinista es evals/check.py (caso nuevo) + lint_plugin.py.
- **Evidencia**: Prosa de descriptions, con puertas deterministas: `python evals/check.py` â†’ `59 ficheros Â· 227 casos (145 positivos, 82 negativos, 1 en contra) â€¦ 0 errores` (caso nuevo literal `plugin-panel-dashboard-proyecto-literal`: Â«dashboard del proyectoÂ»); `python scripts/lint_plugin.py` â†’ `10 agentes Â· 0 errores Â· 16 avisos` (los mismos de antes; sin aviso de disparador literal duplicado ni de ruta `/tmp`). `git grep "/tmp" -- commands` â†’ vacÃ­o; el brief usa `tempfile.mkdtemp(prefix="roadmap-brief-")` (portable, Windows incluido). Descriptions: `roadmap-metrics` Â«escribe un solo informe, docs/roadmap/metrics.mdÂ»; `roadmap-brief` Â«escribe docs/roadmap/brief.md (y brief.pdf si se pide)Â»; `plugin-panel` dispara con Â«dashboard del proyectoÂ», no Â«dashboardÂ» a secas (â‰¤ 1.024 caracteres). Puertas de runtimes: `export-interop.py --check` â†’ `88 ficheros al dÃ­a`; las 5 suites pytest de la cabecera + `test_agent_tools_skill.py` â†’ `112 passed`.
- **Runtimes**: Descriptions comunes; cada `description` de skill ≤ 1.024 caracteres (límite de OpenCode); el temporal portable vale en los tres.
- **Verificación**:
  - `python evals/check.py` → exit 0 (≥ 2 positivos y 1 negativo siguen casando con la description real)
  - `python scripts/lint_plugin.py` → 0 errores y sin aviso de disparador literal duplicado
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**
- [x] Las descriptions describen exactamente lo que se escribe.
- [x] El brief usa un directorio temporal obtenido del sistema (no `/tmp`).
- [x] `plugin-panel` sin el disparador «dashboard» pelado; su caso de evals se actualiza.

### T-06 — Guardarraíl: restauraciones destructivas sin denegar (1.8)

- **Descripción**: `guardrail-check.py` solo trata `git checkout`/`switch` como cambio de rama; `git checkout -- .`, `git restore .` y `checkout -f` pasan (deuda de F1 de la iniciativa anterior). Se añaden pocas reglas (descartan trabajo sin commit) con tests que fallan primero, sin tocar el alcance por rol (ADR-007).
- **Changelog**: El guardarraíl del implementer también deniega git checkout -- ., git restore . y checkout -f.
- **Estado**: completado
- **Cerrada**: 2026-11-14
- **Tiempo humano**: est. 2h · real —
- **Tiempo IA (ejec.)**: est. 0.5h · real 110.25h (0.4h del cierre original estimado + 2.53h medidas en fix5 + 0.78h en fix6 + 1.33h en fix7 + 1.55h en fix8 + 3.22h en fix9 + 1.21h en fix10 + 0.43h en fix11 + 2.11h en fix12 + 0.95h en fix13 + 0.45h en fix14 + 1.07h en fix15 + 47.14h en fix16 + 45.00h en fix17 + 2.08h en fix18 `(medido; la ventana de fix18 es la misma de T-06 y de T-23, 21:22 UTC del 2026-11-17 a las 05:34 del 2026-11-18, con espera de suites)`; las ventanas de fix5 a fix15 están compartidas con T-07 y T-23; la cifra anterior, 11.42h, no sumaba las 2.11h de fix12)
- **Archivos**: `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/test_guardrail_check.py`, `agent-kits/shared/test_guardrail_differential.py` (fix5), `tests/test_native_guardrail_dispatch.py`, `docs/agents/implementer.md`, `docs/CONVENTIONS.md` · fix6: `agent-kits/shared/native-guardrail.py`, `hooks/run-hook.mjs`, `hooks/opencode-plugin.js`, `interop/opencode/plugins/custom-agents/index.js` (regenerado), `tests/test_native_guard_failclosed.py` (nuevo), `tests/hook-guard-failclosed.test.mjs` (nuevo), `docs/FLOWS.md`, `docs/en/FLOWS.md` · fix7: `agent-kits/shared/test_guardrail_fix7.py`, `agent-kits/shared/test_guardrail_differential7.py`, `tests/test_native_guard_failclosed7.py`, `tests/native-guard-adapter-failclosed.test.mjs` (nuevos), `docs/INTEROP.md`, `docs/en/INTEROP.md`, `interop/opencode/plugins/custom-agents/index.js` (regenerado), `agent-kits/shared/test_guardrail_differential.py` · fix8: `tests/test_native_guard_scan8.py` y `tests/native-guard-adapter-fix8.test.mjs` y `agent-kits/shared/test_guardrail_fix8.py` (nuevos), `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/native-guardrail.py`, `hooks/run-hook.mjs`, `hooks/opencode-plugin.js`, `interop/opencode/plugins/custom-agents/index.js` (regenerado), `agent-kits/shared/test_guardrail_differential.py`, `agent-kits/shared/test_guardrail_differential7.py`, `tests/test_native_guard_failclosed.py`, `tests/test_graphiti_security.py` (huella del lanzador), `docs/INTEROP.md`, `docs/en/INTEROP.md`, `docs/agents/implementer.md` · fix9: `agent-kits/shared/test_guardrail_fix9.py` y `tests/test_native_guard_parity9.py` y `tests/native-guard-adapter-fix9.test.mjs` (nuevos), `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/native-guardrail.py`, `hooks/opencode-plugin.js`, `interop/opencode/plugins/custom-agents/index.js` (regenerado), `agent-kits/shared/test_guardrail_differential7.py` (BAD9_PARIDAD y LEGIT9), `agent-kits/shared/test_guardrail_fix8.py` (`env -S 'echo "hola'` pasa a denegado), `docs/agents/implementer.md`, `docs/INTEROP.md`, `docs/en/INTEROP.md` · fix10: `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/native-guardrail.py`, `hooks/run-hook.mjs`, `hooks/opencode-plugin.js`, `interop/opencode/plugins/custom-agents/index.js` (regenerado), `agent-kits/shared/test_guardrail_differential7.py`, `agent-kits/shared/test_guardrail_fix10.py` (nuevo), `tests/test_native_guard_parity9.py`, `tests/opencode-realpath-fix10.test.mjs` (nuevo), `tests/native-guard-adapter-fix9.test.mjs`, `tests/test_graphiti_security.py` (huella), `docs/agents/implementer.md`, `docs/INTEROP.md`, `docs/en/INTEROP.md` · fix11: `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/test_guardrail_differential7.py`, `agent-kits/shared/test_guardrail_fix11.py` (nuevo), `hooks/opencode-plugin.js`, `interop/opencode/plugins/custom-agents/index.js` (regenerado), `tests/opencode-realpath-fix11.test.mjs` (nuevo), `docs/agents/implementer.md` · fix12: `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/test_guardrail_fix12.py` (nuevo), `agent-kits/shared/test_guardrail_fix11.py`, `agent-kits/shared/test_guardrail_differential.py`, `agent-kits/shared/test_guardrail_differential7.py`, `docs/agents/implementer.md` · fix13: `agent-kits/shared/test_guardrail_fix13.py` (nuevo), `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/test_guardrail_fix12.py`, `agent-kits/shared/test_guardrail_differential7.py`, `docs/agents/implementer.md`, `docs/roadmap/2026-11-10-plugin-audit-2/execution-history.md` · fix14: `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/test_guardrail_fix14.py` (nuevo), `agent-kits/shared/test_guardrail_fix14_corpus.py` (nuevo), `agent-kits/shared/test_guardrail_fix10.py`, `agent-kits/shared/test_guardrail_fix12.py`, `agent-kits/shared/test_guardrail_fix13.py`, `docs/agents/implementer.md` · fix14 y fix15 (declarados en fix15, gap 14): `agent-kits/shared/test_guardrail_fix14.py`, `agent-kits/shared/test_guardrail_fix14_corpus.py`, `agent-kits/shared/test_guardrail_fix15.py` y `agent-kits/shared/test_guardrail_fix15_corpus.py` (nuevos), `install/install.mjs` (fix14: `detached: true`; fix15: vigilante de señales; declarado también en T-23), `agent-kits/shared/journal-capture.py`, `agent-kits/shared/journal-io.py`, `agent-kits/shared/journal.py`, `hooks/opencode-plugin.js` (ver T-23) · fix16: `agent-kits/shared/test_guardrail_fix16.py` (nuevo), `agent-kits/shared/test_guardrail_fix16_corpus.py` (nuevo: BYPASS16, PROBES16, G1_PROBES16, LIMITE16), `agent-kits/shared/test_journal_fix16.py` (nuevo), `agent-kits/shared/test_guardrail_differential.py` y `agent-kits/shared/test_guardrail_differential7.py` (las formas que eran LIMITE y ahora se deniegan pasan a BAD6/BAD7), `agent-kits/shared/test_guardrail_fix15.py` (límites de rondas), `agent-kits/shared/native-guardrail.py` (rama barata), `docs/agents/implementer.md`, `agent-kits/shared/test_guardrail_fix17.py` y `agent-kits/shared/test_guardrail_fix17_corpus.py` (fix17: nuevos), `agent-kits/shared/test_guardrail_fix7.py`, `agent-kits/shared/test_guardrail_check.py` y `agent-kits/shared/test_guardrail_fix16.py` (fix17: las formas de «otra rama de trabajo» pasan a la lista de denegadas por la lista blanca; el arnés de fix16 acepta `locale`), `agent-kits/shared/test_guardrail_fix15.py` (fix17, gap 6: el arnés decide por el registro del shim) · fix18: `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/test_guardrail_fix18.py`, `agent-kits/shared/test_guardrail_fix18_corpus.py`, `agent-kits/shared/test_guardrail_fix17.py`, `agent-kits/shared/test_guardrail_fix17_corpus.py`, `docs/agents/implementer.md` · fix18d: `agent-kits/shared/agent-activity-store.py`, `tests/test_agent_activity_tail.py`
- **Evidencia**: GREEN: `pytest -q agent-kits/shared/test_guardrail_check.py -k restauracion` → `23 passed` (15 denegaciones + 8 permitidos: `git checkout main -- <fichero>`, `checkout -b|-B`, `restore --staged`, `restore <fichero>`, `checkout <rama>`); suite completa del guardarraíl → `414 passed`. Se deniegan `git checkout -f|--force`, `checkout [--] .`, `git restore .`, `restore --worktree|-W`, `switch -f|--discard-changes` (también con `-C`, `sh -c '…'`); el mensaje dice «descarta cambios sin comitear» y apunta a `git diff <foto> -- <ficheros> | git apply -R`. `restore --staged .` (solo índice) no se deniega. Runtimes: `pytest -q tests/test_native_guardrail_dispatch.py tests/test_native_prefilter_parity.py tests/test_native_role_context.py` → `33 passed`; `node --test tests/native-guard-adapter.test.mjs` → `pass 3`; `node --test tests/hook-guard-prefilter.test.mjs` → `pass 23`; `export-interop.py --check` → `88 ficheros al día` (el guardarraíl lo sirve un único script). Alcance: `docs/CONVENTIONS.md` no describe las reglas de git del guardarraíl, no se toca; la lista de denegaciones vive en `docs/agents/implementer.md` (actualizada) y en el docstring del script.
- **Runtimes**: Una sola política (`guardrail-check.py`); `native-guardrail.py` la sirve a Codex y OpenCode (`tests/native-guard-adapter.test.mjs`).
- **Verificación**:
  - `pytest -q agent-kits/shared/test_guardrail_check.py -k restauracion` → `passed` (rojo antes)
  - `pytest -q tests/test_native_guardrail_dispatch.py` → sin regresiones
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**
- [x] Se deniegan `git checkout -- .`, `git restore .`, `git restore --worktree` y `git checkout -f`.
- [x] Siguen permitidos `git checkout main -- fichero` y `git checkout -b` (ya cubiertos).


RED: `agent-kits/shared/test_guardrail_check.py -k restauracion` falló con 15 failed, 8 passed: git checkout -- ., checkout -f, restore ., restore --worktree... devuelven None (no se deniegan) · 2026-11-11.

**fix1 a fix9 de T-06** — archivados LITERALMENTE (bytes sin cambios, cada RED, GREEN, interpretación y tabla de pasadas) en [execution-history.md](execution-history.md), sección «Archivado 2026-11-15 — T-06 fix1 a fix9» · SHA-256 `db0957254c129c41d1090bf250a64f4551a07d26d81b18e61316178a522f70b9`. Se movieron en fix13 para dejar sitio al ledger bajo el tope de lectura de 256 KiB; lo vigente (fix15) sigue abajo; fix10 a fix12 y fix13 y fix14 también están archivados (punteros siguientes).

**fix10 a fix12 de T-06** — archivados LITERALMENTE (bytes sin cambios; el condensado de fix10 y fix11, el diseño, el RED, el GREEN, las interpretaciones y el cierre de fix12) en [execution-history.md](execution-history.md), sección «Archivado 2026-11-15 — T-06 fix10 a fix12» · SHA-256 `3f174fead60b8433386988a212f9beb8d6dadb45e7b6c75aa1126618ef622ec3`. Se movieron en fix14 para dejar sitio al ledger bajo el tope de lectura de 256 KiB; lo vigente (fix15) sigue abajo; fix13 y fix14 están archivados (puntero siguiente). Las cifras íntegras de fix10 y fix11 están además en las secciones «Recuperado de 5bed9d0».

**fix13 y fix14 de T-06** — archivados LITERALMENTE (bytes sin cambios; el diseño, el RED, el GREEN, las interpretaciones i1 a i9, las mutaciones y diferenciales y el cierre con la réplica Linux de fix14, y el diseño, el RED, el GREEN y el cierre de fix13) en [execution-history.md](execution-history.md), sección «Archivado 2026-11-15 — T-06 fix13 y fix14» · SHA-256 `ea9c12d34da3e2cdaeba939a0d9290a839449d267a72aafbadc712a319250dad`. Se movieron en fix15 para dejar sitio al ledger bajo el tope de lectura de 256 KiB; lo vigente (fix15) sigue abajo. Antes de moverlos se corrigieron en su sitio las erratas del gap 14 del intento 15 (cabecera «i1 a i9», el tercer test del journal que pasa en el RED y el tamaño de 234 KiB); la errata de las filas 5 y 6 de la tabla del intento 14 (archivada) está en la traza de fix15.

**fix15 de T-06** — archivado LITERALMENTE (bytes sin cambios; el diseño, el RED `b208568`, el GREEN, las interpretaciones i1 a i12, los diferenciales, la estabilidad con carga, las mutaciones y el cierre con la réplica Linux) en [execution-history.md](execution-history.md), sección «Archivado 2026-11-16 — T-06 fix15» · SHA-256 `c51d79b662f1d86f0722e7e29d6e04a1950430fd640f78030716bbb446de47f1`. Se movió en fix16 para dejar sitio al ledger bajo el tope de lectura de 256 KiB; lo vigente (fix16) sigue abajo.

**fix16 de T-06** — archivado LITERALMENTE (bytes sin cambios) en [execution-history.md](execution-history.md), sección «Archivado 2026-11-16 — T-06 fix16» · SHA-256 `d087b5b4ffa48ce8efb6c321866c6caf0ceb9ab3fe02b6666e40793414ecfc4d`. Se movió en fix17 por el tope de lectura de 256 KiB; lo vigente (fix17) sigue abajo.

**fix17 de T-06** — archivado LITERALMENTE (bytes sin cambios) en [execution-history.md](execution-history.md), sección «Archivado 2026-11-17 — T-06 fix17» · SHA-256 `f61d57fed82cd38ec72cf97ec643b5ad030481e48059b633af25952b1ec7c385`. Se movió en fix18 por el tope de lectura de 256 KiB; lo vigente (fix18) sigue abajo.

**fix18 (intento 18, gaps 1, 2, 6, 7, 8, 9, 10, 12 y 14 de T-06 por diseño del orquestador —puntos 1, 2, 3 y 7—; 5 es LÍMITE conocido por decisión del usuario; interpretaciones k1 a k12 más abajo y en T-23)** — `plugin-audit-2/T-06-fix18` y `T-23-fix18` (marcadores abiertos a las 21:22 UTC del 2026-11-17 y cerrados tras el último commit de código `c83f1f2`; horas medidas en el campo «Tiempo IA»; lo posterior —ledger, repetición de suites y réplica Linux— se declara abajo). Commits: archivo `e90dcbb`, RED `c434202`, GREEN guardarraíl `8c3f3e8`, GREEN T-23 `887706f`, tests de /doctor y del pid reutilizado `81db702`, descuento del arranque del helper `077b168`, pin de revisión y arneses de bash real `c4139e0`, cola con seudónimos `1cd0a54`, gap 13 rebatido `b432e89`, ledger y cierre `(el commit que sigue a `c83f1f2`)`. Archivo previo (gap 17 del orquestador y tope de lectura): fix17 de T-06 y de T-23 y los intentos 1, 2, 3, 5 y 17, literales y con SHA-256 en `execution-history.md`; el ledger pasó de 170 a 146 KiB (el tope de lectura es 256 KiB).

**RED (contra `efd40db`).** `test_guardrail_fix18.py` **157 failed y 117 passed** (274; incluye bash real: **bash ejecuta git con el shim en las 129 formas malas del corpus y el guardarraíl las PERMITÍA**, comprobado con el registro del shim, con `git`, `GIT`, `Git`, `git.exe`, `GIT.EXE`, `sudo`, `doas` y `su` delante en el PATH y `type -P` de los ocho); `test_agent_activity_tail.py` **9 failed, 1 passed, 1 skipped** (sin enlaces simbólicos en Windows) y `d2[8]` con la espera REAL **1 failed** (se pierden eventos); `process-tree-fix18.test.mjs` **6 failed** (la prueba del barrido con la raíz muerta tarda 32 s y el descendiente SIGUE vivo: reproduce el gap 3); `test_statusline_scan_fix18.py` **4 failed**. Solo tests (commit `c434202`).

**Punto 1 (rama sin ambigüedad de ruta y refs/heads/* como clase).** `_razon_cambio_rama`: con una posicional sin `--` delante, una ref (`_ref_existe`: `.git/refs`, `packed-refs`, pseudo-refs, `x~1`/`x^`/`@{u}`; sin lanzar git, 0,118 ms por orden frente a 0,108 de `ae56211`) gana a una ruta homónima aunque exista el directorio; una ruta solo vale si no es ref; delante de `--` sigue siendo una ref (`checkout main --`); las rutas se resuelven contra el `cwd` del PAYLOAD (`_CTX`, que fija `decide`). `_razon_refs`: `fetch`/`pull` con refspec de destino local y `+`/`--force`/`.`, `push . …`, `push <remoto> <src>:main|master`, `worktree add -B`, `filter-branch`, `filter-repo`; `rebase` con la aridad real (`-S` no consume la palabra siguiente); `bisect` cualquier subcomando salvo `log|visualize|view|help`; `-C <dir>` se analiza con el HEAD de ese directorio. **Punto 2:** `_razon_destruye` (`submodule update|deinit --force`, `gc --prune=now|all`, `prune`, `reflog expire|delete`) y la tabla `_CODIGO_EN_GIT` ampliada (`difftool -x|--extcmd`, `grep -O|--open-files-in-pager`, `archive --exec`, `fetch-pack`/`send-pack`, `instaweb --httpd`, `filter-branch --setup`). **Punto 3:** `_commondir` valida que apunte a un directorio con `objects/` y `refs/`.

**Interpretaciones (k).**
- **k1** `git bisect run` también se deniega (el diseño dice «cualquier subcomando salvo log/visualize/view»): `git bisect run make test` y `bisect start|reset` a secas pasan a falso deny declarado; salen de `LEGITIMAS17` y `PERMITIDAS_RAMA17` (cambio de tests posteriores al RED, gap 10, trazado en k13).
- **k2** Las opciones de git cuyo valor es una orden (`difftool -x`, `grep -O`, `archive --exec`, `fetch-pack`/`send-pack`, `instaweb --httpd`) se ANALIZAN COMO CÓDIGO (como `rebase -x`), no se deniegan siempre: el diseño decía «→ deny», pero `git difftool -y -x 'diff -u'` y `git rebase -x 'make test'` son legítimos y el corpus de fix17 ya los fijaba como permitidos; con una forma destructiva dentro se deniega. `grep -O` toma el valor solo pegado (`-O<pager>`, `git grep -O v1` no lo consume).
- **k3** `git worktree add <dir> -b <rama>` sigue permitido (es el flujo de P2 del implementer): solo `-B` se deniega (el diseño decía `-b/-B`).
- **k4** `git push <remoto> <src>:main|master` se deniega aunque no fuerce (el diseño dejaba «sin forzar como hoy»): integra en la rama principal sin pasar por /dev-cycle (Fase 6); `git push origin HEAD:<rama de trabajo>` y `push -u origin <rama>` siguen permitidos.
- **k5** `-C <dir>` con HEAD en `main|master` deniega `merge|pull|rebase|cherry-pick|revert|am|commit|reset`; `cd <worktree de main> && git merge` NO se ve (el destino de un `cd` no se resuelve): límite declarado.
- **k6** Con la ref ilegible (sin repositorio, reftable, `packed-refs` > 8 MB) una rama principal con nombre de ruta se deniega y el resto sigue la regla de la ruta.
- **k7** `git merge --abort`, `git mv -f`, `git rebase --update-refs`, `git tag -f`, `git replace`, `checkout -p|--theirs` (git real los rechaza como cambio de rama) y `git web--browse` se quedan PERMITIDOS: ninguno es ruta de los gaps y las lentes los listaron como sondas.
- **k8** Añadidos tras el RED, al clasificar las formas de `lb18/` y `lc18/`: `submodule--helper` como `submodule` y la configuración de `git clone -c|--config` por la lista blanca (cierra `clone -c core.hooksPath=h`); se anotan en el corpus.
- **k9** Tests añadidos tras el RED: el diferencial con bash real del corpus malo y el de la clase LÍMITE (existe y es real: con los shims de `uv`/`chroot`/`strace` bash ejecuta git y el guardarraíl permite).
- **k13 (gap 10, cambios de test posteriores al RED).** (a) `test_guardrail_fix17.py` y su corpus: salen `git bisect run make test`, `git bisect start`, `git bisect reset`, `git bisect run sh -c 'make test'` y `git bisect run git status` de las listas de permitidas (k1); (b) `test_guardrail_fix18_corpus.py` gana las formas de k8 y k9; (c) `test_statusline_scan_fix18.py`: el caso de 8 KB tenía 8.200 B y no entraba al escáner (tope de 8.192 B): ahora `(kb*1024-300)//3` tokens; (d) `test_agent_activity_tail.py`: la tarea de la ventana es `plan/T-01` (el formato de `normalize_tarea`) y la sonda de D2 imprime el recuento y los motivos de lo perdido. Ningún umbral de producto cambia.

**Diferenciales contra `ae56211` (`dif_fix18.py`, con el corpus de 2.690 órdenes de `lb13`, los 7.056 `case` inocuos y el aleatorio de 60.000):** 2.690 → **0 deny nuevos / 0 regresiones**; 7.056 `case` → **0 / 0**; aleatorio de 60.000 → **0 regresiones y 0 deny nuevos** (los fragmentos no tocan las clases nuevas). Las 92 líneas de `lb18/p4.txt` (89 órdenes normales del implementer y 3 más): **0 deny en las 89**; las 3 restantes son `git checkout a.txt` (no existe en este directorio; deny desde j2) y `git bisect start|reset` (k1). Las formas de `lb18/` y `lc18/` que siguen permitidas, y por qué: la clase de envoltorios encadenados (LÍMITE; las 21 formas de `lb18/p1-p3` y las 8 de `LIMITE18`), `git merge --abort` y las de k7, `git checkout docs|-- docs|docs --|feature/x --` (en este directorio `docs` no es una ref; con una rama `docs` se deniegan: `RAMA_COMO_RUTA18`), `git -C ../wt2 merge|commit` y `cd ../wt2 && git merge` (el directorio no existe aquí; con él, k5).

**Deny nuevos declarados (y falsos deny).** `git bisect start|reset|good|bad|new|old|skip|run|replay|terms`; `git checkout|switch <ref con nombre de ruta>`; `git submodule update|deinit --force|-f`; `git gc --prune=now|all`; `git prune`; `git reflog expire|delete` (sin `--dry-run`); `git fetch|pull` con `+`, `--force` o `.` hacia una rama local; `git push . …` y `git push <remoto> <src>:main|master`; `git worktree add -B`; `git filter-branch|filter-repo`; `git difftool|grep|archive|fetch-pack|send-pack|instaweb` con una forma destructiva en su orden; `git clone -c <clave fuera de la lista>`; `git -C <dir en main> merge|commit|…`. **Falsos deny nuevos:** `git bisect` en cualquier forma salvo lectura, `git prune`, `git gc --prune=now`, `git reflog expire`, `git push origin HEAD:main`, `git filter-branch`, `git fetch --force origin x:rama`. Declarados en `docs/agents/implementer.md` (y la regla `-B` de fix16 quitada de la línea 70: gap 12).

**LÍMITE conocido (gap 5, decisión del usuario del 2026-11-17).** Cadenas de programas fuera de la tabla: el sufijo que se desenvuelve no se re-ancla otra vez (`uv run env -S 'strace git reset --hard'`, `uv run xargs -a f strace git restore`, `chroot / env GIT_WORK_TREE=.. chroot / git restore a.txt`, `echo a.txt | chroot / xargs chroot / git restore`, y las shells `ash`/`mksh`/`fish` como programa desconocido). Declarado en `implementer.md` con esos ejemplos; `LIMITE18` los fija como permitidos con su motivo y el diferencial con bash real prueba que son reales.

**Verificación (Windows).** `test_guardrail_fix18.py` ****288 passed** (286 + los 2 diferenciales con bash real: 129 formas malas y la clase LÍMITE; en la última pasada con carga ajena del 30-98 %: 5 diferenciales de bash real en 287 s)**; suite del guardarraíl (18 ficheros `test_guardrail_*.py` más `test_native_guardrail_dispatch.py`, `-n 4`): primera pasada (`-n 4`, 4.527 tests): 4.523 passed y 4 failed, los cuatro de bash real con `nice` y de tiempo (ver «Hallazgos»); en la pasada paralela completa de Windows (15.558 tests) fallaron `test_diferencial15[LANG-sin-definir]` (msys no creó el proceso de una forma con 11 `nice`; ahora el arnés reintenta un registro vacío y los 5 diferenciales pasan: 5 passed) y otros tres tests de plazo de pared ajenos a fix18 (abajo)..

### T-07 — code-health no termina sobre el repo completo (1.9)

- **Descripción**: El auditor reporta timeout de 300 s con `code-health.py` sobre este repo. No lo reprodujo el orquestador: se mide primero qué lo hace lento (sin exclusiones de `worktrees`, `node_modules`, `interop`, `*.sqlite`, o comparación de shingles cuadrática) y se arregla la causa, con un tope de tiempo declarado.
- **Changelog**: code-health termina en un tiempo acotado sobre repos grandes y excluye directorios generados.
- **Estado**: completado
- **Cerrada**: 2026-11-14
- **Tiempo humano**: est. 3h · real —
- **Tiempo IA (ejec.)**: est. 1h · real 0.8h (estimado) + fix5 a fix8 sin horas propias (ventanas medidas de 2.53h, 0.78h, 1.33h y 1.55h compartidas con T-06 y T-23, imputadas a T-06)
- **Archivos**: `skills/code-health/scripts/code-health.py`, `skills/code-health/scripts/test_code_health.py`, `skills/code-health/SKILL.md`, `agent-kits/shared/copias.json` (fix1: el rango del docstring de uso cambia con la línea nueva de flags)
- **Evidencia**: MEDIDA ANTES (perfil por fase sobre este repo, Windows/OneDrive; `testing/` es de qa y el guardarraíl lo veta, por eso consta aquí): `ficheros()` 3,5 s → **7.644 ficheros, 7.204 de ellos bajo `.pytest_cache`** (carpeta oculta con salida de herramientas, 3,46 M de líneas); `leer()` **446,6 s**; `lineas_codigo()` 64,3 s; `duplicados()` > 89 s y sin terminar (el perfil se cortó a los 600 s). La causa es la entrada, no un algoritmo cuadrático: `ficheros()` solo excluía `.git*` y un conjunto fijo, así que cualquier carpeta oculta de herramientas (o `worktrees/`) entraba. DESPUÉS: carpetas ocultas (`.*`), `worktrees/` y `site-packages/` fuera por defecto; topes `--max-files` (3000) y `--max-seconds` (100) con informe PARCIAL declarado (`parcial: true` + aviso con lo analizado, nunca datos inventados; `0` = sin tope). `python skills/code-health/scripts/code-health.py . --json` → exit 0 en **37 s**, 439 ficheros, 149.509 líneas, `parcial: false`. GREEN: `pytest -q skills/code-health/scripts/test_code_health.py` → `37 passed` (los 33 anteriores intactos + 4 de `-k rendimiento`; mismos resultados sobre el corpus existente). Puertas: `lint_plugin.py` 0 errores, `evals/check.py` 0 errores, `export-interop.py --check` → `88 ficheros al día`, `test_copias_declaradas` + `test_skill_size` → `68 passed`. La causa no se reprodujo como timeout de 300 s porque aquí el perfil se cortó antes; la medida demuestra que sin la exclusión el informe no cabe en el tope.
- **Evidencia (2)**: SEGUNDA CAUSA (hallada al verificar en Linux, `python:3.11-slim`, 1 GiB: el test de rendimiento fue OOM-killed, rc 137): el emparejado de `duplicados()` es cuadrático POR VENTANA, y con 120 ficheros idénticos cada ventana aparece ≈4.400 veces → ≈10 M de pares por ventana (el test tardaba 249 s en Windows y reventaba 1 GiB). Se añade el tope `max_occ` (50 ocurrencias emparejadas por ventana, `recortadas` + `parcial` + aviso). RED: `test_rendimiento_las_ventanas_repetidas_no_explotan_y_se_declaran` → `TypeError: duplicados() got an unexpected keyword argument 'max_occ'`. GREEN: `pytest -q skills/code-health/scripts/test_code_health.py` → `38 passed in 22.85s` (antes 37 en 249 s: el fixture pasa a ficheros distintos y los idénticos van en un test propio). Sobre este repo: exit 0 en **32 s**, 439 ficheros, `parcial: true` (4 ventanas recortadas; bloques duplicados 18.478 → 6.279, duplicado 5,5 % → 5,4 %: los bloques que desaparecen eran combinatoria de ventanas repetidas) con el aviso en cabecera.
- **Runtimes**: Sin diferencia: script Python de skill.
- **Verificación**:
  - `pytest -q skills/code-health/scripts/test_code_health.py -k rendimiento` → `passed` (rojo antes: un fixture con muchos ficheros supera el tope)
  - `python skills/code-health/scripts/code-health.py` sobre este repo → termina en < 120 s; medida registrada en `testing/tokens.md`
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**
- [x] La causa queda medida (perfil de tiempo por fase) antes de cambiar nada.
- [x] Hay exclusiones por defecto de directorios generados y un tope por tiempo/ficheros con aviso, nunca un resultado inventado.
- [x] Mismos resultados sobre el corpus de pruebas existente.


RED: `skills/code-health/scripts/test_code_health.py -k rendimiento` falló con 4 failed: ficheros() incluye .mypy_cache/.pytest_cache/worktrees; analizar() sin max_files/max_seconds (TypeError); CLI sin --max-files · 2026-11-11.


RED: `skills/code-health/scripts/test_code_health.py::test_rendimiento_las_ventanas_repetidas_no_explotan_y_se_declaran` falló con TypeError: duplicados() got an unexpected keyword argument max_occ (sin tope por ventana el emparejado agotaba 1 GiB con 120 ficheros identicos) · 2026-11-11.

**fix1 (revisión de dos lentes, intento 1: gaps 5, 6, 7, 12, 13, 17 y 18)** — clave de medición `plugin-audit-2/T-07-fix1`. Se añaden a `Archivos`: `skills/code-health/SKILL.md` (ya listado) y nada más.

RED: `skills/code-health/scripts/test_code_health.py -k fix1` falló con `10 failed, 38 deselected` (un test dedicado por gap): `comparar()` devolvía «↓ mejora»/«↑ empeora» entre un informe parcial y uno completo (gap 5, dos tests: función y CLI); `duplicados()` sin `max_pares`/`pares_tope`, pico de memoria de 60 copias × 500 líneas fuera de 40 MiB (gap 6, dos tests: memoria y parámetro con aviso); `git blame` sin plazo: 12 subprocesos, `edad_parcial` inexistente (gap 7); CLI sin `--max-occ` (gap 12); carpetas ocultas versionadas sin contar ni avisar (gap 13); `analizar(max_bytes=…)` y `ch.PlazoAgotado` inexistentes (gap 17); las 50 ocurrencias del mismo fichero pierden el par a↔b (gap 18 a) y `pct` 0,0 con el plazo vencido (gap 18 c) · 2026-11-11.

GREEN: `pytest -q skills/code-health/scripts` → `48 passed`. Gap 5: `comparar()` marca toda tendencia «no comparable (uno de los dos informes es parcial)» cuando `parcial` difiere, en los dos sentidos, y la CLI añade un aviso `baseline:`. Gap 6: tope TOTAL de pares (`MAX_PARES_DEFAULT` = 100.000, `--max-pairs`; este repo produce 10.033 pares con `--max-pairs 0`, así que el tope no lo toca): cada par es un entero en un `set` (antes una tupla), `pares`/`pares_tope`/`parcial` y aviso con el tope; la prueba mide con `tracemalloc` < 40 MiB (antes 75 MiB con el mismo fixture). Gap 7: UN `git blame` por fichero con varios `-L` (`edades_dias`) y plazo por fichero y por subproceso; lo no calculado se declara en `marcadores.edad_parcial` + aviso + `parcial`. Gap 12: `--max-occ N` (0 = sin tope), y el aviso cita el tope real (gap 18 b). Gap 13: `excluidos_versionados` cuenta también las carpetas ocultas con ficheros de código y el aviso las nombra. Gap 17: `--max-bytes` (default 2 MB; 0 = sin tope) omite con aviso los ficheros enormes y `lineas_codigo` lanza `PlazoAgotado` cada 2.048 líneas. Gap 18: el tope por ventana elige primero una ocurrencia por fichero; con el plazo vencido `duplicado_pct` es `null` y el informe dice «n/d». Medida: `code-health.py .` sobre este repo → termina en 76 s (`--max-pairs 0 --max-seconds 200`). SKILL.md actualizado.

**fix2 (revisión de dos lentes, intento 2: gaps 2, 3 y 4)** — clave de medición `plugin-audit-2/T-07-fix2` (el marcador se abrió desde otro directorio y el meter no pudo cerrarlo: tiempo IA estimado, ~0,6 h (estimado)). Sin ficheros nuevos en `Archivos`.

RED: `skills/code-health/scripts/test_code_health.py -k fix2` falló con `7 failed, 1 passed, 48 deselected` (el que pasa es la guarda del fichero sin versionar): `comparar()` daba tendencias reales entre dos informes parciales con 10 y 12 ficheros y la CLI no avisaba (gap 2, dos tests); un `git blame` que lanza `OSError` o `TimeoutExpired` dejaba `edad_parcial` en 0 y el informe sin `parcial` (gap 3, dos casos parametrizados), y 450 `-L` en una sola llamada (sin `BLAME_L_POR_LLAMADA`); con `max_occ=0` y 150 copias de 300 líneas el plazo de 0,3 s no cortaba (3,3 M de iteraciones; gap 4) y un fichero con 3000 líneas idénticas no activaba `pares_tope` con `max_pares=100` · 2026-11-12.

GREEN: `pytest -q skills/code-health/scripts` → `56 passed`. Gap 2: `comparar()` solo compara dos informes parciales si miden lo mismo (`resumen.ficheros` y `resumen.lineas` idénticos); la CLI distingue en el aviso `baseline:` entre parcial/completo y parciales con distinta cobertura. Gap 3: `git()` anota con `estado` si falló por corte (`cortado`: plazo u `OSError`) o por error de git (`error`: p. ej. fichero sin versionar); `edades_dias` trocea en llamadas de `BLAME_L_POR_LLAMADA` = 200 `-L` (~3 KB de argumentos, muy bajo los 32 K de Windows), recalcula el plazo por trozo y suma a `edad_parcial` las líneas de un trozo cortado o no empezado; solo el corte deja el informe parcial con aviso (el fichero sin versionar deja la edad en blanco, test dedicado). Gap 4: dentro del doble bucle el plazo se mira cada 4096 pares y los pares del mismo fichero cuentan para `max_pares` junto a los retenidos (los retenidos siguen ≤ `max_pares`); no se baja `max_occ=0` a un valor por defecto: con `0` el usuario pide medir todo y solo lo acotan el plazo y los pares. `SKILL.md` actualizado en la misma tarea.

**fix3 (revisión de dos lentes, intento 3, ciclo final: gaps 6 y 7)** — clave de medición `plugin-audit-2/T-07-fix3`. Sin ficheros nuevos en `Archivos`.

RED: `skills/code-health/scripts/test_code_health.py -k fix3` falló con `3 failed, 56 deselected`: `KeyError: 'parcial_motivos'` (gap 6: dos parciales con los mismos ficheros y líneas cortados por `--max-occ` y por `--max-pairs` no declaraban su motivo, y el informe completo tampoco) y `AssertionError: {'src/a.py:1': None, 'src/a.py:4': None}` (gap 7: un `\x0c` en una línea hace que el TODO de la línea 4 de Python quede fuera de rango en git; el `blame` del trozo fallaba entero y el TODO válido de la línea 1 perdía su edad sin marcar el informe parcial) · 2026-11-12.

GREEN: `pytest -q skills/code-health/scripts` → `59 passed`. Gap 6: el informe lleva `parcial_motivos` (lista ordenada: `max-files`, `tiempo`, `max-bytes`, `max-occ`, `max-pairs`, `tiempo-duplicados`, `edad`; vacía si es completo) y `comparar()` exige, además de la misma cobertura, los mismos motivos entre dos parciales (un informe anterior sin la clave solo es comparable con otro que tampoco la tenga); el aviso `baseline:` nombra «cobertura o motivo de parcialidad». Gap 7: un `git blame` que sale con error (no cortado) sobre un fichero VERSIONADO se reintenta línea a línea; lo que siga sin edad suma a `edad_parcial`, marca el informe parcial (`parcial_motivos: ["edad"]`) y el aviso lo cita; el fichero sin versionar sigue dejando la edad en blanco sin marcar parcial (test de fix2 intacto). `SKILL.md` actualizado en la misma tarea.

**fix4 (revisión de dos lentes, intento 4, último ciclo de la fase 1: gap 5)** — clave de medición `plugin-audit-2/T-07-fix4`. Sin ficheros nuevos en `Archivos`.

RED: `skills/code-health/scripts/test_code_health.py -k "fix4 or gap7"` falló con `3 failed, 1 passed` · 2026-11-12: `AssertionError: {'src/a.py:1': 0, 'src/a.py:4': 0, 'src/a.py:7': None}` (un `\x0c` y un `\x1c` en una línea desplazaban la numeración de `str.splitlines` frente a la de git: los TODO salían como `:4` y `:7` en vez de `:3` y `:5`, con la edad de otra línea o ninguna), `['a', 'b', 'c', 'd', 'e'] != ['a\x0cb', 'c', 'd\re']` en `leer()` y `KeyError: 'src/a.py:3'` en el test de reintento por línea.

GREEN: `pytest -q skills/code-health/scripts` → `61 passed`. `leer()` abre con `newline=""` y separa solo por `\n` (quita un `\r` final por línea y la línea vacía final), como git. El test fix3 del gap 7 (que fijaba la numeración antigua con el `\x0c`) se reescribe sobre la numeración nueva y el reintento por línea se prueba ahora con un `blame` que falla a propósito (`monkeypatch` de `ch.git`); `test_fix4_gap5_*` fija la numeración (`:1`, `:3`, `:5`, edad real en las tres y `edad_parcial == 0`) y la lectura.

**fix5 (revisión de dos lentes, intento 5: gap 8)** — clave de medición `plugin-audit-2/T-07-fix5`. Sin ficheros nuevos en `Archivos`.

RED: `skills/code-health/scripts/test_code_health.py -k fix5` falló antes del código con `1 failed, 1 passed` · 2026-11-12: `assert r["parcial"] is True` → `False` (un fichero con separador solo CR queda en una línea, con los TODO colapsados, sin aviso).

**Estado fix5 (cierre anticipado; `en-progreso`)** — hecho: gap 8 (punto 8.8): `cr_suelto()` y motivo `separador-cr` + aviso + `parcial: true`; `pytest skills/code-health/scripts` 63 passed; SKILL.md actualizado. Commits: RED `64b6fd4`, código `81038aa`. Falta: línea GREEN formal, medición `close` de `T-07-fix5`, ledger-lint y réplica.

**Cierre fix5 (ciclo fix5b, 2026-11-13)** — sin cambios de código en este ciclo (commits de fix5: RED `64b6fd4`, código `81038aa`).

GREEN: `pytest -q skills/code-health/scripts` → `63 passed in 56.55s` (Windows, 2026-11-13) y en la réplica Linux completa (`python:3.11-slim`) los tests de `skills/code-health/scripts` pasan en el paso paralelo (`11812 passed, 0 failed`) y los tres de pared en el paso serie (`55 passed`). Medición `close` de `plugin-audit-2/T-07-fix5`: ventana compartida con T-06 y T-23 (`2.53 h` IA medidas en total). Estado → `completado`.

**fix6 (revisión de dos lentes, intento 6: gap 14)** — clave de medición `plugin-audit-2/T-07-fix6`. Sin ficheros nuevos en `Archivos`.

RED: `skills/code-health/scripts/test_code_health.py -k fix6` falló antes del código con `1 failed, 1 passed` · 2026-11-13: `AssertionError: ['separador-cr']` para un fichero con `\r\r\n` y otro con un CR suelto dentro de una línea de un fichero con LF.

GREEN: commits `1cf29b3`. `cr_suelto()` solo marca un fichero con algún CR y NINGÚN LF (CR como único separador); CR-CR-LF y un CR suelto dentro de una línea de un fichero con LF no son parciales. `pytest -q skills/code-health/scripts/test_code_health.py -k fix6` → `2 passed`; suite completa del fichero → `65 collected`, sin fallos en la réplica Linux (ver T-23).

**fix7 (revisión de dos lentes, intento 7)** — clave de medición `plugin-audit-2/T-07-fix7`. La revisión no abre ningún gap sobre T-07: sin cambios de código ni de `Archivos`. Se vuelve a ejecutar su suite dentro de la réplica Linux completa de fix7 (`skills/code-health/scripts`, en el paso paralelo) y el ledger conserva el estado `completado`.

**fix8 (intento 8)** — clave de medición `plugin-audit-2/T-07-fix8`. Sin cambios propios: ningún gap del intento 8 toca `code-health`; las horas medidas de la ventana compartida se imputan a T-06.

### T-38 — Manual PDF regenerable y al día (decidido por el usuario el 2026-11-12)

- **Descripción**: `scripts/check-handbook.py` y `tests/test_npm_payload.py::test_npm_contains_pdf_editions_linked_from_its_readme` están en rojo desde T-03, porque las ediciones de `output/pdf/` fijan el hash de sus fuentes y el repo no tiene generador. El usuario exige que no quede nada en rojo («no puede quedar nada en rojo»), también los artefactos generados. Se trae a esta rama solo el generador reproducible que existe en la rama `docs/model-routing-discovery-2e32c1` (`scripts/build-handbook.py`, `scripts/handbook-render.mjs`, `scripts/handbook-runtime.mjs`, `scripts/handbook-theme.css` y `tests/test_handbook_build.py`), con lo que necesite de su `check-handbook.py`, y se regeneran las ediciones desfasadas. Desde aquí, la tarea que cambie una fuente del manual lo regenera en el mismo commit (o, si son varias de la misma fase, en una sola regeneración antes del cierre de la fase, sin dejar ningún commit de cierre en rojo).
- **Changelog**: El manual PDF se regenera con un generador reproducible del repo y su verificación vuelve a verde.
- **Estado**: completado
- **Cerrada**: 2026-11-12
- **Tiempo humano**: est. 1h · real —
- **Tiempo IA (ejec.)**: est. 1h · real 1.02h (medido)
- **Archivos**: `scripts/build-handbook.py`, `scripts/handbook-render.mjs`, `scripts/handbook-runtime.mjs`, `scripts/handbook-theme.css`, `scripts/check-handbook.py`, `tests/test_handbook_build.py`, `tests/test_handbook_integrity.py`, `output/pdf/**`, `package.json` (solo si el generador declara un script), `docs/CUSTOMIZATION.md` y su espejo EN (una línea sobre cómo regenerar), `agent-kits/shared/copias.json` (si aplica)
- **Verificación**:
  - `python scripts/check-handbook.py` → exit 0
  - `pytest -q tests/test_handbook_integrity.py tests/test_handbook_build.py tests/test_npm_payload.py` → todo passed
  - El generador no instala nada ni descarga navegadores: usa Node, Puppeteer, markdown-it y Mermaid ya instalados, por rutas explícitas

**Criterios de aceptación**
- [x] El generador está en el repo con sus tests y no amplía las dependencias de ejecución del plugin (solo herramientas de autoría opcionales).
- [x] Las ediciones de `output/pdf/` corresponden a las fuentes de HEAD y `check-handbook.py` sale en verde.
- [x] El test de npm de las ediciones PDF sale en verde.

**Evidencia (T-38, clave de medición `plugin-audit-2/T-38`)**

RED: `python scripts/check-handbook.py` → exit 1 con `source_changed:docs/guides/atlassian.md`, `source_changed:docs/reference/atlassian.md` y `source_changed:agent-kits/shared/modules.json` (el rojo actual desde T-03), y `tests/test_npm_payload.py::test_npm_contains_pdf_editions_linked_from_its_readme` con el mismo `sha256` de fuente ≠ manifiesto · 2026-11-12.

Trabajo: se traen de la rama `docs/model-routing-discovery-2e32c1` con `git show rama:ruta > ruta` SOLO `scripts/build-handbook.py`, `scripts/handbook-render.mjs`, `scripts/handbook-runtime.mjs`, `scripts/handbook-theme.css`, `tests/test_handbook_build.py` y, de los dos ficheros que ya existían aquí, las versiones de `scripts/check-handbook.py` y `tests/test_handbook_integrity.py` (los commits `ebdbf62`, `561e913`, `62ce481` y `d278ddb` de esa rama; en HEAD no habían cambiado desde la base común `ac973c2`): `check-handbook` pasa a verificar las TRES ediciones (manual operativo y las dos guías, `editions()`) con `mermaid_blocks` compartido con el generador. Adaptación mínima, sin traer nada más de esa rama: se quita `model-routing` de `CHAPTERS` (la guía `docs/guides/model-routing.md` es de otra iniciativa y no existe aquí), el test `test_T33_local_selector_chapter_is_a_required_handbook_source` de la rama (comprueba esa guía) y la aserción de `test_handbook_build` sobre esa misma fuente. `docs/CUSTOMIZATION.md` y su espejo EN ganan una frase sobre cómo regenerar (`python scripts/build-handbook.py`). El generador no instala nada ni descarga navegadores: usa por ruta explícita lo ya instalado (`~/.claude/tool-cache/to-pdf/node_modules` con puppeteer y markdown-it, el Mermaid de `~/.claude/tool-cache/emailing-manual` y el Chrome de la caché de Puppeteer); `package.json` no cambia (no declara script).

GREEN: `python scripts/build-handbook.py --edition 2026-11-12` regeneró las tres ediciones de `output/pdf/` (PDF + manifiesto) → `python scripts/check-handbook.py` → `check-handbook: PDF, LF-normalized sources, workflows and diagrams match`, exit 0; `pytest -q tests/test_handbook_integrity.py tests/test_handbook_build.py` → `30 passed` + `21 passed`; `pytest -q tests/test_npm_payload.py` → `5 passed` (incluye `test_npm_contains_pdf_editions_linked_from_its_readme`). Los PDF y manifiestos no llevan rutas absolutas, usuario ni nombres de empresa (`grep -a` sobre los seis ficheros → 0; metadatos: `Title`, `Creator`, `Producer (Skia/PDF)`, `CreationDate`). Límite honesto: el generador es sensible a la carga del equipo y de OneDrive (la primera ejecución con la máquina ocupada dio `diagram_failed:1`, otra `build_failed` al publicar sobre ficheros ya sincronizados, y una tercera con el mismo código salió bien); es una herramienta de autoría local, no de la CI, y la CI solo ejecuta `check-handbook` (determinista, stdlib). Las ediciones quedan certificadas con las fuentes de HEAD: si la fase 2 cambia fuentes del manual (`docs/guides/**`, `docs/reference/**`, `modules.json`), hay que volver a ejecutar el generador.

## Fase 2 — Retirada decidida (Kwipu, Graphiti, plugin-dev)

**Estado**: completado · **Est.**: 32h humanas · **Real**: ≈ 3.1h IA medidas (T-08 1.43 + T-09 0.4 + T-10 1.33 + T-11 0.35; las ventanas de T-08 y T-10 se solapan) · 1600 € · 2100k tokens · Decidida por el usuario el 2026-11-10. Nota de `scope-check.py`: sus 6 «criterios aprobados alterados» de T-08, T-10 y T-11 son la replanificación del usuario del 2026-11-19 (commit `21ad63f`), posterior a la base `fb3bb37`; no los ha tocado quien los cumple. Pendiente (usuario): la verificación manual M-B de T-11.

### T-08 — Retirar Kwipu y Graphiti: código, tests y configuración (decidido)

- **Descripción**: Primera mitad de la retirada decidida (la segunda, T-09, es documentación). Antes de borrar se anota en `testing/retirada.md` el commit recuperable (`git rev-parse HEAD`; hoy `129dbeb`, y la release 3.2.3). Se borran 39 ficheros de `skills/knowledge-services/` (18.287 líneas medidas: código 7.351, test 8.494, fixtures 1.963, docs 479) y `tests/test_graphiti_model.py` (418). Se edita el resto: `capabilities.py` pierde `_kwipu_*` y `_graphiti_*` (`:243-470`), `knowledge-schema.py` su validación de backends, y las claves `routing.kwipu|graphiti` salen de plantilla, schema y taxonomía por defecto. TRAMPA: `tests/test_graphiti_security.py` (2.953 líneas) NO se borra entero: guarda el escáner «ningún hook hace red» que cargan `test_hook_launcher_security.py` y `hook-budget.test.mjs`; se renombra `tests/test_hook_network_egress.py` y solo se borran sus ≈718 líneas Graphiti-específicas (clasificación por nombre de test; se revisa al ejecutar). El cliente MCP de `graphiti.py` no se extrae: sin consumidor, se recupera del commit anotado.
- **Changelog**: Cambio rompedor, versión mayor: se retiran los backends Kwipu y Graphiti; la memoria local de docs/knowledge sigue igual.
- **Estado**: completado
- **Cerrada**: 2026-11-19
- **Tiempo humano**: est. 14h · real —
- **Tiempo IA (ejec.)**: est. 3.5h · real 1.43h (medido, `plugin-audit-2/T-08`; ventana de 1h 26m compartida con el trabajo anticipado de T-10)
- **Archivos**: **Se borran (35):** `skills/knowledge-services/backends/{graphiti,graphiti_model,graphiti_provenance,graphiti_providers,graphiti_publication,graphiti_rebuild,graphiti_scope,markdown_export}.py`, `skills/knowledge-services/scripts/{_mcp_fake,kwipu-project-add}.py`, `skills/knowledge-services/scripts/test_{backend_graphiti,backend_markdown_export,backend_markdown_read,backend_markdown_http,graphiti_*,kwipu_metadata,kwipu_project_add}.py`, `skills/knowledge-services/scripts/fixtures/graphiti/`, `skills/knowledge-services/scripts/fixtures/kwipu-*.json`, `tests/test_graphiti_model.py`. **Se divide:** `tests/test_graphiti_security.py` → `tests/test_hook_network_egress.py` (nuevo nombre). **Se editan (código y config):** `agent-kits/shared/{capabilities,knowledge-schema,knowledge-taxonomy-local}.py` (solo claves y funciones de backend; `outbox.py` solo cambia un comentario de cabecera), `agent-kits/shared/copias.json`, `agent-kits/shared/templates/taxonomy.json`, `agent-kits/shared/schemas/taxonomy.schema.json`, `skills/knowledge-services/scripts/knowledge-sync.py` (2 menciones), `skills/plugin-panel/scripts/panel_data.py`, `skills/plugin-panel/assets/{console-context,page-memoria}.js`. **Se editan (tests, 30):** `agent-kits/shared/test_{capabilities,doctor,knowledge_schema,knowledge_routing,knowledge_derivative_surface}.py`, `skills/knowledge-services/scripts/test_{knowledge_sync,backends_init,backend_verification}.py`, `skills/knowledge-category-template/scripts/test_category_template.py`, `tests/{memoria_fixture,test_audit_journal,test_audit_knowledge,test_console_encoding,test_control_center_http,test_knowledge_approved_retrieval,test_knowledge_candidates,test_knowledge_find,test_knowledge_prompt_split,test_knowledge_router,test_knowledge_router_read,test_knowledge_services,test_panel_data,test_panel_fix4,test_panel_memoria_fix1,test_private_state_dirs,test_training_data_services,test_hook_launcher_security}.py`, `tests/test_panel_memoria_ui.py`, `tests/hook-budget.test.mjs` (comentario), `interop/**` (regenerado). **Añadidos al ejecutar (nota 2026-11-19):** `skills/knowledge-services/backends/__init__.py` (mensaje «retirado»: `RETIRADOS`, `VERSION_RETIRADA`), `docs/roadmap/2026-11-10-plugin-audit-2/testing/retirada.md`, `agent-kits/shared/{knowledge-find,knowledge-local,doctor,outbox}.py` (el router deja de derivar `group_id`; comentarios), `agent-kits/shared/{test_knowledge_routing.py,fixtures/derived-read.json}` (renombrada de `graphiti-derived-read.json`), `skills/knowledge-services/{SKILL.md,backends/README.md,references/project-integration.md}` (reescritos como marco sin adaptadores: sin ello el paquete portable cita ficheros borrados), `skills/knowledge-services/scripts/test_backend_verification.py` (reescrita sobre el adaptador de prueba), `skills/knowledge-services/scripts/test_manifest_publication.py` (borrada: probaba la finalización del manifiesto Windows del adaptador Kwipu), `tests/{test_knowledge_router_read,test_audit_knowledge,test_audit_journal,test_hook_network_egress}.py`, `tests/fixtures/opencode-v2-agent-contract.json`, `skills/knowledge-category-template/scripts/test_category_template.py`, `.gitignore`. **No se toca:** `skills/training-data-services/**` (congelada; su clave `bridge_to_kwipu` la retira T-32 si se aprueba), `.claude/knowledge-services/taxonomy.json` (local del usuario, ver «acciones»).
- **Runtimes**: Sin diferencia por runtime en lo que se borra (Python común). En `interop/` desaparecen las menciones del agente `knowledge-curator` en Codex y OpenCode; el instalador y los manifiestos no citan los backends (0 menciones en `install/`).
- RED: `test_registro_base_declara_knowledge_gate_y_training_sin_backends_retirados` falló con `AssertionError` (el registro aún declaraba `kwipu` y `graphiti`) y `test_backend_retirado_sale_con_mensaje_retirado_sin_traceback[kwipu-markdown-export|graphiti-graphiti|otro-kwipu]` falló con `assert 1 == 2` / «no se encontró un adaptador» (sin «retirado») · 2026-11-19 (commit `8b68ec3`)
- **Evidencia** (GREEN, commit `17402f1`; salidas reales de esta sesión):
  - `git grep -il -E "graphiti|kwipu" -- agent-kits skills tests install hooks scripts evals` → 90 ficheros antes; ahora 20: `skills/training-data-services/{SKILL.md,scripts/test_case_schema.py}` (congelada), 7 guardas declaradas en `testing/retirada.md` (`backends/__init__.py::RETIRADOS`, `test_knowledge_sync.py`, `test_capabilities.py`, `test_knowledge_schema.py`, `test_doctor.py`, `test_knowledge_router.py`, `test_hook_network_egress.py`) y 11 documentos/evals que borra T-09 (hechos en su commit: tras T-09 la lista queda en 9 ficheros).
  - `wc -l`: `skills/knowledge-services/` 49 ficheros · 20.617 líneas → 10 · 2.404; los 90 ficheros de la búsqueda sumaban 46.971 líneas y los 63 que sobreviven, 23.327; `tests/test_graphiti_security.py` 2.953 líneas · 126 tests → `tests/test_hook_network_egress.py` 1.913 · 90 (`pytest --collect-only`: `90 tests collected`; los 36 quitados, uno a uno, en `testing/retirada.md`).
  - `pytest -q tests/test_knowledge_router.py tests/test_knowledge_router_read.py skills/knowledge-services/scripts` → `152 passed, 1 skipped`; `tests/test_knowledge_find.py` → `106 passed, 2 skipped`; `tests/test_hook_network_egress.py` → `90 passed`; `tests/test_hook_launcher_security.py` → `8 passed`; `tests/test_copias_declaradas.py` → `27 passed`; `tests/test_panel_data.py` → `18 passed`; `tests/test_panel_memoria_fix1.py` → `38 passed`; `agent-kits/shared/test_{capabilities,knowledge_schema,knowledge_routing,knowledge_read_context,knowledge_portability,doctor}.py` → `47 / 84 / 41 / 36 / 21 / 233 passed (1 skipped)`; `tests/test_console_encoding.py` → `716 passed`; más `test_panel_memoria_ui` 31, `test_panel_fix4` 14, `test_audit_journal` 21, `test_audit_knowledge` 3, `test_knowledge_candidates` 7, `test_control_center_http` 22, `test_knowledge_services` 38, `test_knowledge_approved_retrieval` 68, `test_training_data_services` 15, `skills/knowledge-category-template/scripts` `44 passed, 1 skipped`.
  - `node --test tests/hook-budget.test.mjs` → `pass 14, fail 0`.
  - Límite honesto: la carpeta `agent-kits/shared` entera no cabe en el tiempo de la máquina (a 25 min iba por el 43 % sin fallos); se ejecutaron los ficheros que esta tarea toca, uno a uno. La suite completa la corre el usuario tras la fase.
  - Puertas de runtimes: `export-interop.py --check` → `88 ficheros al día`; los 5 ficheros de pytest → `101 passed` y un fallo real (`test_paquete_portable_resuelve_sus_propios_kits`: `SKILL.md` citaba `kwipu-adapter.md`), corregido reescribiendo la skill y vuelto a pasar (`1 passed`); `node --test` de los 4 ficheros → ver «Puerta de runtimes de la fase 2» (la corrida tarda más de 22 min en esta máquina).
- **Verificación**:
  - `git grep -il -E "graphiti|kwipu" -- agent-kits skills tests install hooks scripts evals` → solo `skills/training-data-services/**` y las menciones declaradas en `testing/retirada.md` (rojo antes: ≈75 ficheros)
  - `pytest -q tests/test_hook_network_egress.py tests/test_hook_launcher_security.py tests/test_copias_declaradas.py tests/test_knowledge_router.py tests/test_knowledge_find.py tests/test_panel_data.py tests/test_panel_memoria_fix1.py agent-kits/shared skills/knowledge-services/scripts` → verde (rojo antes: un test nuevo de `test_capabilities.py` exige que el registro ya no declare `kwipu` ni `graphiti` y que `knowledge-sync.py --backend kwipu` falle con «retirado»)
  - `node --test tests/hook-budget.test.mjs` → verde; `python -m pytest --collect-only -q tests/test_hook_network_egress.py` → el número de tests es el de antes menos los Graphiti-específicos listados en `testing/retirada.md`
  - `wc -l` antes y después, anotado en `testing/retirada.md`
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**
- [x] No queda código ni test de Kwipu o Graphiti fuera de `skills/training-data-services/`; `knowledge-sync.py --backend kwipu|graphiti` y una taxonomía que los declare fallan con un mensaje claro («retirado en la versión X; ver CHANGELOG»).
- [x] La suite «ningún hook hace red» sigue íntegra con su nuevo nombre (mismos tests menos los Graphiti-específicos, listados en `testing/retirada.md`) y `test_hook_launcher_security.py` y `hook-budget.test.mjs` apuntan al fichero nuevo.
- [x] `capabilities.py` sin `_kwipu_*` ni `_graphiti_*`; `/doctor` y el panel de memoria funcionan sin backends; `copias.json` y `test_copias_declaradas.py` coherentes.
- [x] Los tests de router (`test_knowledge_router*.py`) siguen en verde con un adaptador de prueba (el marco se conserva, T-10 revisada 2026-11-19).

### T-09 — Retirar Kwipu y Graphiti: documentación, ejemplos y evals (decidido)

- **Descripción**: Segunda mitad de la retirada. De los 137 ficheros con menciones: 37 se borran, 1 se divide (T-08), 96 se editan, 2 son PDF generados y 1 es config local del usuario (cifras y criterio en el plan). Aquí se borran las guías de Graphiti (ES y EN) y `kwipu-adapter.md`; se editan 38 docs y READMEs, ejemplos, `knowledge-curator`, `/setup`, `/doctor`, `phase4-knowledge-gate.md`, 3 `SKILL.md` y 3 casos de evals; los CHANGELOG declaran el cambio rompedor. ADR-020, ADR-021 y una nota en ADR-018 se proponen con `knowledge-curation.py propose`.
- **Changelog**: Se retira la documentación, los ejemplos y los pasos de /setup y /doctor de Kwipu y Graphiti.
- **Estado**: completado
- **Cerrada**: 2026-11-19
- **Tiempo humano**: est. 7h · real —
- **Tiempo IA (ejec.)**: est. 1.7h · real 0.4h (medido, `plugin-audit-2/T-09`)
- **Dependencias**: T-08
- **Archivos**: **Se borran:** `docs/{,en/}knowledge-services-graphiti.md`, `skills/knowledge-services/references/kwipu-adapter.md`. **Docs ES y EN (38):** `README.md`, `README.es.md`, `CLAUDE.md`, `docs/{CODE_CONTEXT,CONVENTIONS,CUSTOMIZATION,FLOWS,INTEROP,MEMORY-PORTABILITY,PLUGIN-PANEL,README}.md`, `docs/en/{CODE_CONTEXT,CONVENTIONS,CUSTOMIZATION,FLOWS,INTEROP,MEMORY-PORTABILITY,PLUGIN-PANEL,README}.md`, `docs/agents/{CONTRACTS,ROLES,knowledge-curator}.md`, `docs/guides/{audit-remediation,dashboard,knowledge-categories,memory,quality-playbook,subscription-efficiency}.md`, `docs/en/guides/{audit-remediation,dashboard,knowledge-categories,memory,product}.md`, `docs/reference/product.md`, `docs/en/reference/{doctor,product}.md`. **Ejemplos y config versionada:** `docs/examples/integrations/memory.json`, `docs/examples/memory/taxonomy.json`, `.gitignore` (línea `kwipu-export/`; `*-export/` se queda). **Piezas:** `agents/knowledge-curator.md`, `commands/{setup,doctor}.md`, `agent-kits/dev-cycle/references/phase4-knowledge-gate.md`, `agent-kits/shared/{README,doctor-reference}.md`, `skills/knowledge-services/{SKILL.md,backends/README.md,references/project-integration.md}`, `skills/{knowledge-category-template,plugin-panel,training-data-services}/SKILL.md` (solo prosa), `evals/cases/{command-setup,skill-knowledge-category-template,skill-knowledge-services}.json`, `CHANGELOG.md`, `CHANGELOG.es.md`, `interop/**` (regenerado). **Añadidos al ejecutar (nota 2026-11-19):** `docs/{,en/}guides/memory.md` (W-20 pasa a «Conectar un servicio de memoria propio»; W-22 deja de ser Graphiti y pasa a «Elegir y retirar integraciones», porque el generador del manual exige workflows contiguos), `docs/{,en/}reference/doctor.md` (ES en `agent-kits/shared/doctor-reference.md`), `agent-kits/shared/{README.md,doctor-reference.md}`, `docs/agents/{ROLES,CONTRACTS,knowledge-curator}.md` (filas E45 y E55 retiradas, E16/E18/E60 generalizadas), `docs/guides/{audit-remediation,dashboard,knowledge-categories,quality-playbook,subscription-efficiency}.md` (+ espejos EN), `skills/training-data-services/SKILL.md` (una frase), `tests/fixtures/opencode-v2-agent-contract.json` (descripción de `knowledge-curator`). **No se editan:** `output/pdf/custom-agents-manual-operativo.pdf` y `output/pdf/guia-resultados-calidad-custom-agents.pdf` (binarios generados; se regeneran, ver «acciones»).
- **Runtimes**: Los textos de `/setup` y `/doctor` se exportan a Codex (`command-skills/custom-agents-setup`, `custom-agents-doctor`) y a OpenCode (`commands/`): se regeneran sin los pasos; sin diferencia de conducta.
TDD n/a: documentación, ejemplos y evals sin código testeable; el rojo medible fue la búsqueda de la verificación (`git grep -il -E "graphiti|kwipu"` fuera de registros → 95 ficheros tras T-08, 7 ahora) y `evals/check.py` como puerta · 2026-11-19
- **Evidencia** (salidas reales de esta sesión):
  - `git grep -il -E "graphiti|kwipu" -- . ':!docs/roadmap' ':!docs/knowledge' ':!CHANGELOG*' ':!output' ':!interop' ':!.claude' ':!skills/training-data-services'` → 95 ficheros antes; ahora 7: las guardas de ausencia/compatibilidad declaradas en `testing/retirada.md` (`backends/__init__.py::RETIRADOS`, `test_knowledge_sync.py`, `test_capabilities.py`, `test_knowledge_schema.py`, `test_doctor.py`, `test_knowledge_router.py`, `test_hook_network_egress.py`). Ninguna doc ni eval versionada las cita; `interop/` → 0 menciones.
  - `python evals/check.py` → `59 ficheros · 226 casos (144 positivos, 82 negativos, 1 en contra) · 59 piezas del repo · 0 errores`; `python scripts/lint_plugin.py` → `0 errores · 16 avisos` (preexistentes: nombres genéricos de comando y comandos del cliente citados en las guías; los avisos de rutas citadas inexistentes de `CONTRACTS.md` desaparecen).
  - `python scripts/export-interop.py --check` → `88 ficheros al día`.
  - `grep -n -i "cambio rompedor\|breaking" CHANGELOG.md CHANGELOG.es.md` → ambos declaran el cambio rompedor con la versión mayor 4.0.0 en `[Unreleased]`/`[Sin publicar]`.
  - Memoria: `knowledge-curation.py propose` (no a mano) dejó tres candidatos en `docs/knowledge/candidates/pending/` (carpeta local, no versionada): `2026-11-19-plugin-audit-2-adr020-retirada.md` (sha256 `ab3c5054…`), `…-adr021-retirada.md` (`89e490d3…`) y `…-adr018-retirada.md` (`ccaca835…`), los tres `status: proposed`. Los ADR existentes (ADR-020 y ADR-021 ya existían como `aceptada`) los cura `knowledge-curator`; aquí no se aprueba nada.
  - Puertas de runtimes y tests que leen estas piezas: `pytest -q` de `test_capabilities`, `test_knowledge_schema`, `test_knowledge_routing`, `test_knowledge_services`, `test_knowledge_router`, `skills/knowledge-services/scripts`, `test_export_interop`, `test_plugin_root_resolution`, `test_native_role_context`, `test_native_guardrail_dispatch`, `test_native_prefilter_parity`, `test_skill_size`, `test_copias_declaradas` → `464 passed, 1 deselected` (el deselect es la prueba de la guía de T-10, que aún no existe en este commit).
  - Deuda declarada (no es un fallo de esta tarea): al editar `docs/guides/quality-playbook.md` y `docs/guides/subscription-efficiency.md`, `tests/test_user_handbooks.py::test_handbook_pdf_matches_its_markdown_edition` (2 casos) y `check-handbook.py` quedan en rojo hasta regenerar `output/pdf/` con `scripts/build-handbook.py`, que T-38 manda hacer una sola vez al cierre de la fase (al final de la fase 2, tras T-11).
- **Verificación**:
  - `git grep -il -E "graphiti|kwipu" -- . ':!docs/roadmap' ':!docs/knowledge' ':!CHANGELOG*' ':!output' ':!interop' ':!.claude' ':!skills/training-data-services'` → vacío (rojo antes: ≈95 ficheros)
  - `python evals/check.py` → exit 0 (sin enlaces ni rutas citadas inexistentes)
  - `grep -n -i "cambio rompedor\|breaking" CHANGELOG.md CHANGELOG.es.md` → ambas lo declaran, con la versión mayor
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**
- [x] Docs ES y EN sin menciones de Kwipu ni Graphiti, con sus espejos en el mismo cambio; `/setup` sin paso 5-sexies de Kwipu/Graphiti y `/doctor` sin sus comprobaciones.
- [x] Los dos CHANGELOG declaran el cambio rompedor, qué se retira, cómo migrar (memoria local o Kairos) y el commit recuperable.
- [x] ADR-020, ADR-021 y la nota de ADR-018 quedan propuestos por el servicio de memoria (no a mano).

### T-10 — Conservar el marco de knowledge-services sin adaptadores incluidos (revisado 2026-11-18)

- **Descripción** (replanificada 2026-11-19 tras la revisión del 2026-11-18): el marco de `knowledge-services` se queda **sin adaptadores incluidos**: `backends/__init__.py` (cargador por `type`, contrato de 6 funciones `health/plan/apply/verify/rebuild/revoke`, `AdaptadorNoDisponible` fail-closed, `_TIPO_VALIDO_RE`), `knowledge-sync.py` (576 líneas; `routing` fail-closed y `outbox.py`), `REGISTRO`/`registrar()` de `capabilities.py` y la lectura `knowledge-find.py --intent`/`--backends-dir` (sin backend declarado devuelve solo lo local). Hoy sus 5 suites (`test_{backends_init,backend_verification,knowledge_sync,knowledge_sync_replay,manifest_publication}.py`) se apoyan en `markdown_export` (Kwipu), que T-08 borra: se reapuntan a un **adaptador de prueba** que vive en `fixtures/` y se carga por el parámetro `directorios` del cargador (nunca desde `backends/`, para que el plugin siga sin adaptadores incluidos). Se añade la guía «Cómo añadir un backend» (contrato, convención `type → backends/<type>.py` o directorio extra, routing, config en `taxonomy.json`, verificación con `/doctor`), y la skill/`/setup`/`/doctor` dejan de prometer Kwipu o Graphiti: dicen «sin backends incluidos; ver la guía». El adaptador MCP genérico NO entra aquí: llega con la iniciativa de Kairos.
- **Decidido por el usuario el 2026-11-10**: opción (b): el marco se retira y la iniciativa de Kairos lo recupera del commit anotado en T-08.
- **Revisado por el usuario el 2026-11-18 (supersede la opción (b))**: el marco **se conserva**. El plugin debe permitir enchufar cualquier MCP de memoria externo (Kwipu, Kairos u otro) y no fijarse a Kairos. Se quedan el contrato de 6 funciones, la carga de adaptadores por `type`, el `routing` fail-closed, `knowledge-sync.py`, `outbox.py` y `REGISTRO`/`registrar()` de `capabilities.py`, sin adaptadores incluidos, con sus tests sobre el adaptador de prueba y una guía de «cómo añadir un backend». T-08 y T-09 solo quitan los adaptadores concretos de Kwipu y Graphiti. El adaptador MCP genérico (mapa de herramientas, configurable en `/setup`) llega con la iniciativa de Kairos. Orden: la retirada T-08..T-10 se adelanta y va justo después de cerrar la Fase 1. Descripción, Archivos, Verificación y criterios replanificados el 2026-11-19.
- **Changelog**: El marco de knowledge-services se conserva sin adaptadores incluidos: cualquier MCP de memoria externo se puede añadir como backend.
- **Estado**: completado
- **Cerrada**: 2026-11-19
- **Tiempo humano**: est. 6h · real —
- **Tiempo IA (ejec.)**: est. 1.5h · real 1.33h (medido, `plugin-audit-2/T-10`; su ventana se solapa con la de T-08 porque el adaptador de prueba y la reapuntada de las suites se hicieron ANTES de borrar `markdown_export`, para no dejar el árbol en rojo)
- **Dependencias**: T-08
- **Archivos**: **Se crean:** `skills/knowledge-services/scripts/fixtures/adaptador_prueba.py` (las 6 funciones, en memoria, deterministas), `skills/knowledge-services/references/add-backend.md` (guía; espejo EN si la guía entra en `docs/en/`). **Se editan:** `skills/knowledge-services/{SKILL.md,backends/README.md,references/project-integration.md}`, `skills/knowledge-services/scripts/test_{backends_init,backend_verification,knowledge_sync,knowledge_sync_replay,manifest_publication}.py` (adaptador de prueba en vez de `markdown_export`), `agent-kits/shared/capabilities.py` (solo si queda una referencia a los adaptadores retirados), `agent-kits/shared/test_capabilities.py`, `evals/cases/skill-knowledge-services.json` (description real), `docs/{,en/}guides/memory.md` (enlace a la guía), `interop/**` (regenerado). **Añadidos al ejecutar (nota 2026-11-19):** `skills/knowledge-services/scripts/test_backends_init.py` (nuevo test de la guía y de que `backends/` no trae adaptadores), `commands/{setup,doctor}.md`, `agent-kits/shared/doctor-reference.md` y `docs/en/reference/doctor.md` (citan la guía), `docs/{,en/}guides/memory.md` (enlace a la guía, W-20), `skills/knowledge-services/references/project-integration.md`. `test_manifest_publication.py` se BORRA en vez de reapuntarse: probaba la finalización del manifiesto Windows (`_retryable_manifest_error`, lector nativo con `CreateFileW`) del adaptador Kwipu; el adaptador de prueba no tiene ese comportamiento y el diario de recuperación del marco lo cubre `test_knowledge_sync_replay.py` (parcial + reanudación). El adaptador de prueba guarda su estado en una carpeta (`cfg["dir"]`), no «en memoria»: el cargador relee el módulo en cada corrida y las suites de reanudación necesitan que el estado sobreviva entre llamadas. **No se borra:** nada del marco; `outbox.py`, el journal y `knowledge-find.py --intent` quedan intactos.
- **Runtimes**: Sin diferencia por runtime: el marco es Python común; en `interop/` la skill sigue exportándose (Codex por el bundle, OpenCode por el índice).
- RED: `test_el_plugin_no_incluye_adaptadores_en_backends` falló con `AssertionError: ['__init__.py', 'graphiti.py', …]` (8 adaptadores en `backends/`) en el commit `a0a6696`, deliberadamente rojo hasta el borrado de T-08; y `test_la_guia_add_backend_existe_y_la_citan_la_skill_setup_y_doctor_sin_prometer_sustitutos` falló con `assert False` sobre `os.path.isfile(…/add-backend.md)` al retirar la guía (y pasó al restaurarla) · 2026-11-19
- **Evidencia** (salidas reales de esta sesión):
  - Orden anti-rojo: commit `a0a6696` (adaptador de prueba + `test_backends_init`, `test_backend_verification` y `test_knowledge_sync_replay` reapuntados mientras `markdown_export` seguía existiendo; el RED deliberado es el de «sin adaptadores en backends/») → commit `17402f1` (T-08, borrado) → este commit (guía, citas, test de la guía).
  - `pytest -q skills/knowledge-services/scripts agent-kits/shared/test_capabilities.py tests/test_knowledge_find.py tests/test_knowledge_router.py tests/test_knowledge_router_read.py tests/test_knowledge_services.py tests/test_hook_network_egress.py` → `434 passed, 3 skipped`.
  - `git ls-files skills/knowledge-services/backends` → `skills/knowledge-services/backends/README.md` y `skills/knowledge-services/backends/__init__.py` (nada más).
  - `knowledge-sync.py --backend viejo --check` con `type: kwipu` → «knowledge-sync: el backend «kwipu» está retirado desde la versión 4.0.0 del plugin (ver CHANGELOG) y su adaptador no disponible; para enchufar un backend propio consulta skills/knowledge-services/references/add-backend.md» y `exit=2`; con `type: graphiti`, igual; con `type: adaptador-prueba` y `--backends-dir skills/knowledge-services/scripts/fixtures` → `dry-run: 0 entrada(s) enrutada(s), 0 operacion(es)` y `exit=0`. `test_flujo_completo_plan_apply_verify_por_directorios` recorre dry-run, publicación y `--check` en verde.
  - Puertas de runtimes: `export-interop.py --check` → `88 ficheros al día`; los 6 ficheros de pytest (con `test_skill_size`) → `139 passed`; `evals/check.py` → `0 errores`; `lint_plugin.py` → `0 errores`.
  - Límite honesto: `/doctor` solo carga adaptadores de `backends/` del plugin; uno de carpeta propia se comprueba con `knowledge-sync.py --check --backends-dir` (la guía lo dice). Ampliar `/doctor` a un directorio de adaptadores del proyecto no estaba en el alcance: queda como pregunta para el usuario.
- **Verificación**:
  - `pytest -q skills/knowledge-services/scripts agent-kits/shared/test_capabilities.py tests/test_knowledge_find.py tests/test_knowledge_router.py tests/test_knowledge_router_read.py tests/test_knowledge_services.py tests/test_hook_network_egress.py` → verde (rojo antes: tras T-08 las 5 suites del marco fallan al no encontrar `markdown_export`)
  - `git ls-files skills/knowledge-services/backends` → solo `__init__.py` y `README.md` (el plugin no incluye adaptadores)
  - un `taxonomy.json` que declare `type: kwipu` o `graphiti` → `knowledge-sync.py` sale con exit 2 y el mensaje «adaptador no disponible … ver add-backend.md», sin traceback; uno que declare el adaptador de prueba por `directorios` → `plan/apply/verify` en verde
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**
- [x] El marco (cargador, contrato de 6 funciones, routing fail-closed, `knowledge-sync.py`, outbox, `REGISTRO`/`registrar()`, `knowledge-find --intent`) sigue funcionando y probado, sin ningún adaptador concreto en `backends/`.
- [x] Sus tests usan un adaptador de prueba fuera de `backends/`, cargado por `directorios`; ninguno depende de Kwipu ni de Graphiti.
- [x] Existe la guía «Cómo añadir un backend» y la skill, `/setup` y `/doctor` la citan en vez de prometer backends concretos; nada promete Kairos.

### T-11 — Generalizar plugin-dev en `project-extensions`: crear piezas en cualquier proyecto (replanificada por el usuario el 2026-11-19)

- **Descripción**: Supersede «sacar plugin-dev del plugin distribuido» (decisión del usuario 2026-11-19: sin una skill de autoría, quien usa el plugin no tiene cómo añadir agentes, skills, comandos, hooks, tools o MCP). `plugin-dev` (691 líneas) está escrita para ESTE repo (24 menciones a `lint_plugin.py`, `export-interop.py`, `agent-kits/`, CHANGELOG, `release.py`) y en un proyecto consumidor da instrucciones que no aplican. Se convierte en la skill distribuida **`project-extensions`**: crea piezas en el proyecto del usuario, en la carpeta y formato de cada runtime según la tabla de `docs/PROJECT-EXTENSIONS.md` (Claude Code `.claude/{agents,skills,commands}/`, Codex `.codex/agents/*.toml` + `.agents/skills/`, OpenCode `.opencode/{agents,commands,tools}/` + `.agents/skills/` o `.claude/skills/`; MCP en `.mcp.json`, `.codex/config.toml` u `opencode.json`), pregunta para qué runtimes, nunca escribe en la caché del plugin y al terminar comprueba con `agent-kits/shared/project-pieces.py` que la pieza aparece en el inventario (lo que ven `/work-context` y el panel). Conserva lo genérico de plugin-dev (árbol de decisión de piezas, frontmatter y tools mínimos, description con disparadores, `SKILL.md` corto + `references/`, scripts deterministas con tests, degradar sin bloquear, anti-patrones) y mueve lo propio de este repo (linter, interop, espejos EN/ES, CHANGELOG, `release.py`, `docs/agents/`, `CONTRIBUTING.md`) a `references/custom-agents-repo.md`, que solo se lee al trabajar en este repositorio. Nada va a `.claude/` del repo.
- **Changelog**: plugin-dev pasa a llamarse project-extensions y sirve en cualquier proyecto: crea agentes, skills, comandos, hooks, tools y MCP propios para Claude Code, Codex y OpenCode.
- **Estado**: completado
- **Cerrada**: 2026-11-19
- **Tiempo humano**: est. 9h · real —
- **Tiempo IA (ejec.)**: est. 2.5h · real 0.35h (medido, `plugin-audit-2/T-11`)
- **Archivos**: `skills/plugin-dev/**` → `skills/project-extensions/**` (`SKILL.md` ≤ 200 líneas; `templates/` por runtime: agente Claude/OpenCode `.md`, agente Codex `.toml`, skill, comando, hook, tool OpenCode, entrada MCP; `references/{piece-boundaries,claude-code-contracts,tool-observation-contracts,persistent-workflows,architecture-diagnostics}.md` revisadas a genérico; `references/custom-agents-repo.md` nuevo), `agent-kits/shared/{README.md,capability-selection.md,modules.json,rationalization-table.md,skill-index.py}`, `scripts/{export-skills,lint_plugin}.py`, `tests/{test_export_skills,test_session_context}.py`, `tests/test_project_extensions_skill.py` (nuevo), `evals/cases/skill-plugin-dev.json` → `evals/cases/skill-project-extensions.json`, `evals/cases/skill-changelog-sync.json`, `.github/ISSUE_TEMPLATE/pieza-nueva.yml`, `github-templates.MANUAL-COPY/ISSUE_TEMPLATE/pieza-nueva.yml`, `hooks/session-journal.sh` (comentario), `CLAUDE.md`, `CONTRIBUTING.md`, `README.md`, `README.es.md`, `docs/{PROJECT-EXTENSIONS,CUSTOMIZATION,INSTALL,INTEGRATION-ROADMAP,README,observability}.md`, `docs/en/{PROJECT-EXTENSIONS,CUSTOMIZATION,INSTALL,INTEGRATION-ROADMAP,README,observability}.md`, `docs/agents/ROLES.md`, `docs/guides/quality-playbook.md`, `.claude-plugin/{plugin,marketplace}.json` (si listan skills), `interop/**`, `.codex-plugin/plugin.json` y `.agents/plugins/marketplace.json` (regenerados)
- **Archivos añadidos al ejecutar (nota 2026-11-19)**: `skills/project-extensions/templates/*` (las 14 plantillas: agente Claude/OpenCode/Codex, skill, comando Claude/OpenCode, hook `settings.json` + script informativo, tool OpenCode, MCP Claude/Codex/OpenCode) y `references/verify-inventory.md` (nuevo: cómo localizar y leer `project-pieces.py`, para que `SKILL.md` no cite `agent-kits/`); `agent-kits/shared/copias.json` (el rango del bloque `imports_de_cabecera` de `scripts/export-skills.py` bajó una línea); `docs/guides/memory.md` y su espejo EN (W-22 pasa a «Elegir y retirar integraciones»: el generador del manual exige workflows contiguos); `output/pdf/**` (regenerado una sola vez al cierre de la fase, como manda T-38); `evals/cases/skill-project-extensions.json` (5 casos, incl. el del repo). `export-skills.py` ya NO excluye la skill: viaja en el paquete portable (con `references/custom-agents-repo.md` sin rutas `scripts/…` que no existen allí).
- **Runtimes**: La skill viaja en los tres (Claude y Codex por el bundle, OpenCode por el índice exportado). Lo que crea depende del runtime elegido por el usuario; para Codex los comandos no tienen carpeta de proyecto (se dice, no se inventa), para Claude las tools no tienen ejecutor genérico (se crea el script y se declara en el agente).
- RED: `pytest -q tests/test_project_extensions_skill.py` → `11 failed in 5.90s` (no existía `skills/project-extensions/`: falla la forma de la skill, las plantillas de los tres runtimes, la tabla de rutas, la cita desde `CONTRIBUTING.md`/`CLAUDE.md` y la ausencia de `plugin-dev`) · 2026-11-19 (commit `036a5c6`)
- **Evidencia** (GREEN; salidas reales de esta sesión):
  - `pytest -q tests/test_project_extensions_skill.py` → `11 passed`: el test rellena, en un proyecto temporal y por runtime, las plantillas de agente, skill, comando, tool y MCP en las carpetas de la tabla y `project-pieces.py --project-only --json` los inventaría con `warnings == []` y `partial == false` (Claude Code: agent, skill, command, mcp; Codex: agent, skill, mcp; OpenCode: agent, skill, command, tool-source, mcp).
  - `wc -l skills/project-extensions/SKILL.md` → `120`; `grep -c -E "lint_plugin|export-interop|release.py|agent-kits/" skills/project-extensions/SKILL.md` → `0`; `git grep -l "plugin-dev" -- . ':!docs/roadmap' ':!docs/knowledge' ':!CHANGELOG*'` → vacío.
  - `pytest -q` de `test_project_extensions_skill`, `test_export_skills`, `test_session_context`, `test_export_interop`, `test_skill_size`, `test_plugin_root_resolution`, `test_native_role_context`, `test_native_guardrail_dispatch`, `test_native_prefilter_parity`, `test_copias_declaradas`, `test_rationalization_tables` y `agent-kits/shared/test_skill_index.py` → `288 passed, 1 failed` (el fallo real: `imports_de_cabecera` de `copias.json` apuntaba a las líneas 36-45 de `export-skills.py`, que bajaron una; corregido a 35-44 → `tests/test_copias_declaradas.py` `27 passed`).
  - `python evals/check.py` → `59 ficheros · 228 casos (145 positivos, 83 negativos, 1 en contra) · 59 piezas del repo · 0 errores`; `python scripts/lint_plugin.py` → `0 errores · 16 avisos` (preexistentes); `python scripts/export-interop.py --check` → `88 ficheros al día`; `python scripts/export-skills.py --check` sobre el paquete exportado → `328 ficheros · 0 problema(s)`.
  - Manual PDF (regla de T-38, una sola regeneración al cierre de la fase): `python scripts/build-handbook.py --edition 2026-11-19` → `exit=0` y tres PDF; `python scripts/check-handbook.py` → `check-handbook: PDF, LF-normalized sources, workflows and diagrams match`, exit 0; `pytest -q tests/test_handbook_integrity.py tests/test_user_handbooks.py` → `34 passed`; `tests/test_handbook_build.py tests/test_npm_payload.py` → `26 passed`; `grep -a` de datos personales en `output/pdf/` → 0. Dos intentos previos fallaron (`workflow_sequence`: faltaba W-22; `diagram_failed:11`: etiquetas de un diagrama sin comillas) y el tercero salió bien.
  - Límite honesto del inventario: `project-pieces.py` solo lista las skills de Codex en `.agents/skills/` (Codex también lee `.codex/skills/`, verificado por el usuario en el fuente de Codex): la skill y la tabla de `docs/PROJECT-EXTENSIONS.md` recomiendan `.agents/skills/` y lo dicen. Los hooks de Codex y OpenCode no tienen plantilla (el formato cambia entre versiones): la skill los describe y manda a su documentación.
- **Verificación**:
  - `pytest -q tests/test_project_extensions_skill.py` → verde (rojo antes: no existe `skills/project-extensions/`; el test genera con las plantillas, en un proyecto temporal, un agente, una skill y un comando para cada runtime y exige que `project-pieces.py` los inventaríe sin avisos)
  - `git grep -l "plugin-dev" -- . ':!docs/roadmap' ':!docs/knowledge' ':!CHANGELOG*'` → vacío; `wc -l skills/project-extensions/SKILL.md` ≤ 200
  - `grep -c -E "lint_plugin|export-interop|release.py|agent-kits/" skills/project-extensions/SKILL.md` → 0 (lo propio del repo vive en `references/custom-agents-repo.md`)
  - `pytest -q tests/test_export_skills.py tests/test_session_context.py tests/test_export_interop.py tests/test_skill_size.py` → verde · `python evals/check.py` → exit 0 · `python scripts/lint_plugin.py` → 0 errores
  - puertas de runtimes (cabecera) → verde
  - Pendiente (usuario) — lectura (manual, sesión real; M-B) → en un proyecto con el plugin instalado, «crea un agente para revisar SQL» dispara `project-extensions` en Claude Code, Codex y OpenCode y la pieza aparece en `/work-context`

**Criterios de aceptación**
- [x] `skills/project-extensions/` existe y `skills/plugin-dev/` no; sus disparadores son genéricos («crea un agente/skill/comando/hook», «añade un MCP al proyecto») y no citan rutas de este repo.
- [x] Crea agentes, skills, comandos, hooks, tools y MCP en la carpeta y formato de cada runtime de la tabla de `docs/PROJECT-EXTENSIONS.md`, nunca en la caché del plugin, y verifica la pieza con `project-pieces.py`.
- [x] Las reglas propias de este repo están en `references/custom-agents-repo.md` y la skill solo lo lee dentro de custom-agents; `CONTRIBUTING.md` y `CLAUDE.md` apuntan a él.

**Puerta de runtimes de la fase 2** (cabecera: `export-interop.py --check` + 5 ficheros de pytest + 4 de `node --test`; corrida de cierre, sin editar nada en paralelo):

- `python scripts/export-interop.py --check` → `88 ficheros al día`.
- `pytest -q tests/test_export_interop.py tests/test_plugin_root_resolution.py tests/test_native_role_context.py tests/test_native_guardrail_dispatch.py tests/test_native_prefilter_parity.py` → verde en cada tarea (`101 passed` + el caso de `test_plugin_root_resolution` corregido en T-08; `139 passed` con `test_skill_size` en T-10; incluidos en los `288 passed` de T-11 tras corregir `copias.json`).
- `node --test tests/opencode-plugin.test.mjs tests/codex-native-install.test.mjs tests/hook-runtime.test.mjs` → `tests 200 · pass 196 · fail 0 · skipped 3` (el único «fail» de esa invocación fue `installer.test.mjs` matado por mi `timeout 1750` tras 29 min, no un fallo de la prueba).
- `node --test tests/installer.test.mjs` (a solas) → `tests 191 · pass 185 · fail 0 · skipped 6 · duration_ms 2103634 · exit=0`. Una corrida anterior de los cuatro ficheros juntos (263 tests) dio `256 pass · 1 fail · 6 skipped`; el fallo (`gap I3-1`, `ENOENT … add-backend.md`) fue mío: moví la guía a un temporal durante la corrida para demostrar el RED de T-10. Con los ficheros quietos pasa.
- Máquina lenta: con la memoria ocupada las suites de instalador tardan 23-35 min; no se ejecutó la suite completa del repo (la corre el usuario tras la fase) ni `agent-kits/shared` entero (a los 25 min iba por el 43 % sin fallos).

## Fase 3 — Tokens

**Estado**: borrador · **Est.**: 30h humanas · **Real**: — · 1500 € · 2260k tokens

### T-12 — TDD en el brief, skill bajo demanda (2.4)

- **Descripción**: Con `tdd: true` cada subagente carga la skill `tdd` entera (≈10 KB) aunque el brief de `task-brief.py` ya trae la sección TDD. Se mueve al brief la ley dura y el formato `RED:` y se manda abrir la skill solo ante una duda (stack concreto, `TDD n/a`). Ahorro estimado ≈ 25 K tokens por ciclo con subagentes.
- **Changelog**: El brief de cada tarea trae la regla TDD esencial y el subagente ya no carga la skill completa.
- **Estado**: borrador
- **Tiempo humano**: est. 2h · real —
- **Tiempo IA (ejec.)**: est. 0.5h · real —
- **Archivos**: `agent-kits/shared/task-brief.py`, `agent-kits/shared/test_task_brief.py`, `agent-kits/dev-cycle/references/phase3-subagents.md`, `agents/implementer.md`, `skills/tdd/SKILL.md`, `docs/{,en/}TOKEN-EFFICIENCY.md`, `interop/**` (regenerado)
- **Runtimes**: El brief es texto de `task-brief.py` que recibe el subagente en cualquier runtime.
- **Verificación**:
  - `pytest -q agent-kits/shared/test_task_brief.py -k tdd_resumido` → `passed` (rojo antes: el brief no incluye el formato `RED:` ni la ley dura)
  - `context-footprint.py --project . --file agents/implementer.md` antes/después → menos bytes (`testing/tokens.md`) · tamaño del brief generado (`task-brief.py` sobre una tarea de prueba) medido antes y después
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**
- [ ] El brief con `tdd: true` incluye la ley dura y el formato `RED:`; sin `tdd` no cambia.
- [ ] Ninguna puerta de la skill `tdd` desaparece: sigue siendo la fuente única y el brief la cita.
- [ ] Medida antes/después registrada (estimada, no consumo facturado).
- [ ] Medido: agente + brief con `tdd: true` baja ≥ 8 KB (la skill ≈ 10 KB deja de cargarse; el brief gana ≤ 2 KB).

### T-13 — Tabla de lentes fuera de adversarial-review/SKILL.md (2.5)

- **Descripción**: El revisor abre `skills/adversarial-review/SKILL.md` (18,6 KB) para leer una tabla de ≈4 KB. La tabla pasa a `references/` o al prompt de la lente y el SKILL conserva el mapa. Ahorro estimado hasta ≈21 K tokens por ciclo.
- **Changelog**: El revisor lee solo la tabla de lentes que necesita, no toda la skill de revisión adversarial.
- **Estado**: borrador
- **Tiempo humano**: est. 1.5h · real —
- **Tiempo IA (ejec.)**: est. 0.4h · real —
- **Archivos**: `skills/adversarial-review/SKILL.md`, `skills/adversarial-review/references/lentes.md` (nuevo), `agents/reviewer.md`, `docs/agents/reviewer.md`, `interop/**` (regenerado)
- **Runtimes**: La referencia vive en `skills/`, que viaja sin traducir (`docs/INTEROP.md:31`); el revisor la halla con la receta de seis raíces.
- **Verificación**:
  - `context-footprint.py --project . --file skills/adversarial-review/SKILL.md` antes/después → menos bytes (`testing/tokens.md`); fichero nuevo medido aparte
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**
- [ ] El reviewer lee solo la referencia de la lente.
- [ ] La skill conserva todos los criterios y severidades (`--diet-check`: 0 párrafos perdidos).
- [ ] Medido: lo que lee el revisor baja de 18,6 KB a ≤ 5 KB (≥ 13 KB menos por lectura).

### T-14 — Freno de tokens del ledger (2.1)

- **Descripción**: `ledger-lint.py` avisa a 183.500 bytes (`UMBRAL_TAMANO_BYTES`), cuando una lectura ya cuesta ≈45 K tokens. Umbral a 40-60 KB, archivado por fase con `ledger-archive.py` (ya existe) y Lente A solo sobre la fase revisada. Ahorro [E] ≈30 K tokens por lectura.
- **Changelog**: Los ledgers avisan antes de crecer, se archivan por fase y la revisión lee solo la fase en curso.
- **Estado**: borrador
- **Tiempo humano**: est. 5h · real —
- **Tiempo IA (ejec.)**: est. 1.5h · real —
- **Archivos**: `agent-kits/shared/ledger-lint.py`, `tests/test_ledger_lint.py`, `agent-kits/shared/ledger-archive.py`, `agent-kits/shared/test_ledger_archive.py`, `commands/dev-cycle.md`, `skills/adversarial-review/SKILL.md`, `agent-kits/shared/task-brief.py`, `docs/{,en/}CONVENTIONS.md`, `docs/{,en/}TOKEN-EFFICIENCY.md`, `interop/**` (regenerado)
- **Runtimes**: Sin diferencia: script y prosa de `dev-cycle`; la Lente A es la misma.
- **Verificación**:
  - `pytest -q tests/test_ledger_lint.py -k umbral_tokens` → `passed` (rojo antes: un ledger de 70 KB no avisa)
  - `pytest -q agent-kits/shared/test_ledger_archive.py agent-kits/shared/test_task_brief.py` → verde (archivar conserva bytes y SHA)
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**
- [ ] El aviso salta en el umbral nuevo (configurable) y su texto nombra `ledger-archive.py`.
- [ ] El cierre de fase del `/dev-cycle` ofrece archivar; el archivado conserva bytes y SHA.
- [ ] La Lente A recibe la fase revisada, no el ledger entero, sin perder los criterios de esa fase.
- [ ] Un ledger pequeño se lee igual que hoy.
- [ ] Medido: el aviso del ledger salta a ≤ 60.000 bytes (hoy 183.500) y la entrada de la Lente A para 100 KB baja ≥ 50 %.

### T-15 — Borrar «Alcance y activación» duplicado (2.9)

- **Descripción**: Párrafos que repiten la description antigua dentro del cuerpo (25 ocurrencias de «Alcance y activación» en `agents/`, `commands/` y `skills/`; el análisis contó 21: se clasifica pieza a pieza). Se borran los que duplican la description y se conserva lo que aporta un guardarraíl. Ahorro estimado ≈15 KB.
- **Changelog**: Los cuerpos de agentes, comandos y skills ya no repiten su propia description.
- **Estado**: borrador
- **Tiempo humano**: est. 2h · real —
- **Tiempo IA (ejec.)**: est. 0.6h · real —
- **Dependencias**: T-12, T-13, T-11
- **Archivos**: `agents/*.md`, `commands/*.md`, `skills/*/SKILL.md` (solo los párrafos «Alcance y activación»), `agent-kits/shared/test_source_snapshot.py` (líneas base de párrafos, con motivo), `docs/{,en/}TOKEN-EFFICIENCY.md`, `interop/**` (regenerado)
- **Runtimes**: Los cuerpos se copian a los agentes generados de Codex y OpenCode: se regenera y los evals de description siguen casando.
- **Verificación**:
  - `grep -rn "Alcance y activaci" agents commands skills --include=*.md` → solo los párrafos que aportan una regla que la description no tiene
  - `python agent-kits/shared/context-footprint.py --project .` antes y después → ≈15 KB menos, en `testing/tokens.md`
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**
- [ ] Ningún párrafo borrado contiene un criterio ausente de la description (revisión pieza a pieza).
- [ ] `python evals/check.py` sigue casando.
- [ ] Los reemplazos en líneas base llevan motivo.
- [ ] Medido: `context-footprint.py --project .` baja ≥ 12 KB (estimado 15 KB).

### T-16 — Cierre de /dev-cycle bajo demanda (2.11)

- **Descripción**: `dev-cycle.md` (29,5 KB) carga la Fase 6 y la tabla de transiciones desde el primer turno (≈10 KB). Pasan a `references/phase6-close.md` con «léelo solo al llegar a la Fase 6». El paso Kwipu/Graphiti de `/setup` (2.10) NO se mueve: T-08 lo borra. Mejora el margen de la vía rápida.
- **Changelog**: dev-cycle carga el cierre solo cuando llega a esa fase.
- **Estado**: borrador
- **Tiempo humano**: est. 2h · real —
- **Tiempo IA (ejec.)**: est. 0.5h · real —
- **Dependencias**: T-15
- **Archivos**: `commands/dev-cycle.md`, `agent-kits/dev-cycle/references/phase6-close.md` (nuevo), `tests/test_dev_cycle_split.py`, `docs/{,en/}FLOWS.md`, `docs/agents/ROLES.md`, `interop/**` (regenerado)
- **Runtimes**: `dev-cycle` es command-skill en Codex y comando en OpenCode; `phase6-close.md` viaja en `agent-kits/` (`install/providers.mjs:30,34`) y se lee con la 
- **Verificación**:
  - `context-footprint.py --project . --file commands/dev-cycle.md` antes y después → ≈10 KB menos (en `testing/tokens.md`)
  - `python scripts/lint_plugin.py --diet-check` → 0 párrafos perdidos
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**
- [ ] El ahorro de la vía rápida sigue ≥ 6.000 (idealmente mayor).
- [ ] Los pasos movidos dicen cuándo leerlos; `retro-gate.py` y la tabla de transiciones se leen en el cierre.
- [ ] Ninguna puerta del cierre se pierde (`--diet-check`).
- [ ] Los comandos exportados a Codex/OpenCode resuelven las referencias nuevas.
- [ ] Medido: `dev-cycle.md` baja de 29,5 KB a ≤ 20 KB y el ahorro de la vía rápida sigue ≥ 6.000.

### T-17 — Una receta del kit por pieza (2.6)

- **Descripción**: La receta que localiza el kit aparece 19 veces en 9 agentes y 14 en 9 comandos (verificado con `grep -c`). Una por pieza que derive todas las variables (`PLANKIT`, `DEVKIT`…) en vez de repetirla por paso. Ahorro medido −7,5 KB.
- **Changelog**: Cada agente y comando resuelve el kit una sola vez.
- **Estado**: borrador
- **Tiempo humano**: est. 3h · real —
- **Tiempo IA (ejec.)**: est. 0.7h · real —
- **Dependencias**: T-15, T-16
- **Archivos**: `agents/*.md`, `commands/*.md`, `agent-kits/shared/test_source_snapshot.py`, `tests/test_recipe_once.py` (nuevo), `docs/{,en/}TOKEN-EFFICIENCY.md`, `interop/**` (regenerado)
- **Runtimes**: Solo Claude define `CLAUDE_PLUGIN_ROOT`; el criterio prueba Codex/OpenCode con la variable sin definir.
- **Verificación**:
  - `pytest -q tests/test_recipe_once.py` → `passed` (rojo antes: varias piezas repiten la receta)
  - `grep -c "M=agent-kits/shared/ledger-lint.py" agents/*.md commands/*.md` → ≤ 1 por fichero
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**
- [ ] Cada pieza tiene una receta que define todas las variables que usa y solo acepta un `SHAREDKIT` absoluto.
- [ ] Resuelve SIN `CLAUDE_PLUGIN_ROOT` (variable solo de Claude Code): el test la deja sin definir y usa raíces `.codex` y `.opencode` falsas (`tests/test_plugin_root_resolution.py`).
- [ ] Medido: ≥ 7 KB menos entre agentes y comandos; ≤ 1 receta por pieza (`grep -c`).

### T-18 — Fragmentos solo si hay aciertos y capability-check mínimo (2.3, 2.12)

- **Descripción**: El agente resume la regla y además manda leer el fragmento (`knowledge-check*`, `constitution-check`): doble pago de hasta ≈28 K tokens por ciclo [E]. Se lee el fragmento solo con aciertos y se quita el puntero a `rationalization-table`. `capability-check.md` (5,7 KB) pasa a un núcleo de ≈1,8 KB.
- **Changelog**: Los agentes leen los fragmentos de conocimiento y capacidades solo cuando aplican.
- **Estado**: borrador
- **Tiempo humano**: est. 3h · real —
- **Tiempo IA (ejec.)**: est. 0.8h · real —
- **Dependencias**: T-17
- **Archivos**: `agent-kits/shared/knowledge-check.md`, `agent-kits/shared/knowledge-check-governed.md`, `agent-kits/shared/constitution-check.md`, `agent-kits/shared/capability-check.md`, `agent-kits/shared/rationalization-table.md`, `agents/implementer.md`, `agents/qa.md`, `agents/planner.md`, `agents/evaluator.md`, `docs/agents/ROLES.md`, `interop/**` (regenerado)
- **Runtimes**: Los fragmentos se leen con la receta; mismo texto en los tres; no cambia la forma de invocar skills.
- **Verificación**:
  - `git show :agents/evaluator.md | tr -d '\r' | wc -c` → ≤ 15.513 (bytes en LF)
  - `context-footprint.py --project . --file agent-kits/shared/capability-check.md` antes/después → menos bytes (`testing/tokens.md`) → núcleo ≈1,8 KB
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**
- [ ] `evaluator.md` ≤ 15.513 bytes en LF.
- [ ] La salida de capacidades sigue siendo la misma (200-300 caracteres) con el núcleo.
- [ ] Ningún agente pierde la obligación de respetar ADR/lecciones aplicables.
- [ ] Medido: `capability-check.md` ≤ 2 KB (hoy 5,7 KB) y `evaluator.md` ≤ 15.513 bytes en LF.

### T-19 — Cuerpo de implementer: núcleo + referencia del flujo clásico (2.2, parte de 2.13)

- **Descripción**: El subagente con brief carga el cuerpo entero de `implementer` (29,5 KB) con secciones que no puede usar. Núcleo corto, flujo clásico a `agent-kits/implementer/references/` (directorio nuevo) y reglas repetidas 2-5 veces, una sola vez. Ahorro [E] 24-30 K tokens por ciclo.
- **Changelog**: El implementer carga un núcleo corto y lee el flujo clásico solo cuando no hay brief.
- **Estado**: borrador
- **Tiempo humano**: est. 5h · real —
- **Tiempo IA (ejec.)**: est. 1.5h · real —
- **Dependencias**: T-12, T-18
- **Archivos**: `agents/implementer.md`, `agent-kits/implementer/references/classic-flow.md` (nuevo), `agent-kits/shared/task-brief.py`, `agent-kits/shared/test_task_brief.py`, `docs/agents/implementer.md`, `evals/cases/agent-implementer.json`, `install/providers.mjs` (solo si no copia `agent-kits/` entero), `interop/**` (regenerado)
- **Runtimes**: `agent-kits/implementer/references/` viaja en el payload común (`install/providers.mjs:34`); sin brief.
- **Verificación**:
  - `context-footprint.py --project . --file agents/implementer.md` antes/después → menos bytes (`testing/tokens.md`) → < 15 KB
  - puertas de tokens (cabecera) → verde · `pytest -q agent-kits/shared/test_task_brief.py agent-kits/shared/test_guardrail_check.py` → verde
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**
- [ ] El cuerpo de `implementer.md` baja a un núcleo (objetivo < 15 KB) que conserva DoD, Verificación, RED/GREEN y guardrails.
- [ ] Sin brief (flujo clásico) el agente sabe leer la referencia y funciona igual.
- [ ] Cada regla duplicada queda una sola vez.
- [ ] Medido: `implementer.md` < 15 KB (hoy 29,5 KB), ≥ 14 KB menos por subagente.

### T-20 — Índice de SessionStart solo en Codex y OpenCode (2.7)

- **Descripción**: En Claude Code el índice de `SessionStart` duplica el listado nativo de skills (truncado, 18 de 34) y cuesta 844 tokens por arranque y compactación. En runtime `claude` se emite solo la cabecera; Codex y OpenCode conservan el índice. Se contrasta con los evals de activación antes de cerrar.
- **Changelog**: El arranque de Claude Code ya no repite el listado de skills; Codex y OpenCode lo conservan.
- **Estado**: borrador
- **Tiempo humano**: est. 2h · real —
- **Tiempo IA (ejec.)**: est. 0.5h · real —
- **Archivos**: `hooks/session-context.py`, `agent-kits/shared/skill-index.py`, `tests/test_session_context.py`, `agent-kits/shared/test_skill_index.py`, `docs/{,en/}observability.md`, `interop/**` (regenerado)
- **Runtimes**: Solo Claude cambia; Codex y OpenCode conservan el índice completo (lo fija un test).
- **Verificación**:
  - `pytest -q tests/test_session_context.py -k runtime_claude` → `passed` (rojo antes: el bloque trae el índice completo)
  - `pytest -q agent-kits/shared/test_skill_index.py tests/test_hooks_config.py` → verde
  - lectura (manual, sesión real; M-C) → en Codex y OpenCode reales el arranque muestra el índice completo y en Claude solo la cabecera
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**
- [ ] Runtime `claude`: solo cabecera; `codex` y `opencode`: índice completo como hoy, fijado por test.
- [ ] `dev.json` `sesion.indice` sigue mandando y la medida del bloque (≈4,6 KB → menos) queda anotada.
- [ ] Medido: en `claude` el bloque de `SessionStart` baja ≈ 3,4 KB (844 tokens); en `codex` y `opencode` no cambia (`-k "runtime_codex or runtime_opencode"`).

### T-21 — Cabecera «ORQUESTA agentes» solo donde despacha (2.14)

- **Descripción**: `export-interop.py` antepone «Este comando ORQUESTA agentes…» (línea 107) a los 16 comandos exportados aunque 12 no despachan (≈600 caracteres por invocación en Codex/OpenCode). Se emite solo si el cuerpo nombra un rol.
- **Changelog**: Los comandos de Codex y OpenCode que no despachan agentes ya no llevan la cabecera de orquestación.
- **Estado**: borrador
- **Tiempo humano**: est. 1.5h · real —
- **Tiempo IA (ejec.)**: est. 0.4h · real —
- **Archivos**: `scripts/export-interop.py`, `tests/test_export_interop.py`, `docs/INTEROP.md`, `interop/**` (regenerado)
- **Runtimes**: Solo Codex y OpenCode (es el exportador); Claude sin cambio.
- **Verificación**:
  - `pytest -q tests/test_export_interop.py -k cabecera_orquesta` → `passed` (rojo antes: 16 de 16 la llevan)
  - `python scripts/export-interop.py` y luego `python scripts/export-interop.py --check` → exit 0
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**
- [ ] La cabecera aparece solo en comandos cuyo cuerpo nombra un agente despachable.
- [ ] Los agentes y comandos exportados conservan su conducta (misma lista de roles).
- [ ] Medido: 12 de los 16 comandos exportados pierden ≈ 600 caracteres (≈ 7,2 KB).

### T-22 — Reglas de este repo fuera de los agentes genéricos y qa condicional (2.8, 2.13)

- **Descripción**: Reglas propias de este repositorio (`export-interop`, `CONTRACTS.md`) viven dentro de agentes genéricos (≈4,2 KB) y `qa.md:114` (2 KB) solo aplica al QA sin UI. Las primeras pasan a `docs/CONSTITUTION.md` o a `plugin-dev` (carga solo en este repo); lo segundo, a una referencia condicional.
- **Changelog**: Los agentes genéricos dejan de cargar reglas que solo valen para el repositorio del plugin.
- **Estado**: borrador
- **Tiempo humano**: est. 3h · real —
- **Tiempo IA (ejec.)**: est. 0.8h · real —
- **Dependencias**: T-18, T-19, T-11
- **Archivos**: `agents/planner.md`, `agents/implementer.md`, `agents/qa.md`, `agent-kits/qa/references/sin-ui.md` (nuevo), `.claude/skills/plugin-dev/SKILL.md` (tras T-11), `docs/CONSTITUTION.md`, `docs/agents/CONTRACTS.md`, `docs/agents/planner.md`, `docs/agents/qa.md`, `interop/**` (regenerado)
- **Runtimes**: Constitución y referencias se leen igual en los tres; el consumidor no recibe reglas de este repo.
- **Verificación**:
  - `grep -n "export-interop\|CONTRACTS.md" agents/*.md` → sin coincidencias salvo la regla que se quede en `plugin-dev`
  - `context-footprint.py --project . --file agents/qa.md` antes/después → menos bytes (`testing/tokens.md`) → ≈2 KB menos
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**
- [ ] `planner` conserva el mecanismo E2/E3 como regla de PROYECTO (constitución/`plugin-dev`), no como texto del agente genérico.
- [ ] El QA sin UI carga la referencia solo cuando aplica.
- [ ] Un proyecto consumidor no pierde ninguna puerta.
- [ ] Medido: `planner`, `implementer` y `qa` pierden ≥ 6 KB entre los tres.

## Fase 4 — Simplificación del código

**Estado**: borrador · **Est.**: 34.5h humanas · **Real**: — · 1725 € · 2470k tokens

### T-23 — CI en paralelo y sin ejecuciones duplicadas (4.1)

- **Descripción**: La CI tarda 875 s: pytest en serie (749 s) y suites que son script y test corren dos veces (23 por recuento rápido, 27 según el análisis: se fija el número real). Se añade `pytest -n auto`, se quita el bucle donde pytest ya recoge el fichero y se publica `--durations`. Adelantable al inicio. Tras T-08 la CI pierde ≈11,8 K líneas de test de Kwipu y Graphiti.
- **Changelog**: La CI es unas 2,5 veces más rápida al paralelizar pytest y no repetir suites.
- **Estado**: en-progreso
- **Tiempo humano**: est. 2h · real —
- **Tiempo IA (ejec.)**: est. 0.5h · real 0.55h (medido; ventana compartida con T-02..T-07) + fix5 a fix16 sin horas propias (ventanas imputadas a T-06; la de fix16 y la de fix18 de T-23 se midieron en la misma ventana que las de T-06)
- **Archivos**: `tests/codex-plugin-state.test.mjs` (intento 12, orquestador: la regex del test de `candidates()` acepta CRLF; en un checkout de Windows `run-hook.mjs` llega con CRLF y el test daba rojo) · `docs/roadmap/2026-11-10-plugin-audit-2/testing/perf.md` (lo escribe el orquestador con las medidas de T-07 y T-23; el guardarraíl veta `testing/` al implementer) · `ci.yml.MANUAL-COPY` y `.github/workflows/ci.yml` (idénticos, comprobado con `diff`; el paso `pip install pytest pyyaml` de `:30-31` añade `pytest-xdist`), `tests/test_ci_manual_copy.py`, `tests/test_ci_skill_suites.py`, `tests/test_suites_no_pytest.py` · añadidos por la nota de alcance: `pytest.ini` (solo registra el marcador `serie`), `tests/test_redact_fix3.py`, `tests/test_npm_payload.py` (fix4: timeout de `npm pack` 120 → 600 s), `tests/test_local_state_fix3.py` (fix4: módulo al paso serie, plazo de pared del almacén), `agent-kits/shared/test_redact.py`, `agent-kits/shared/test_plan_review_summary.py`, `tests/test_agent_activity_store.py`, `tests/test_bench_session_end.py`, `tests/opencode-plugin.test.mjs` (fix1: espera a que el hijo escriba el JSON), `tests/test_lint_plugin.py`, `tests/test_ledger_lint.py`, `tests/test_dashboard.py` (fix1: wrappers `test_suite_legada_*` de sus `main()`/`run()`) (marcados `@pytest.mark.serie`: miden tiempo de pared o dependen del orden de lecturas y fallan bajo `-n auto`; corren en un paso aparte sin xdist), `agent-kits/shared/agent-activity-store.py` (fix5), `agent-kits/shared/test_redact.py` (fix5) · fix7 (corrección de fix8, gap 9: faltaban): `agent-kits/shared/test_ledger_view.py` (paso serie), `tests/test_graphiti_security.py` (huella del lanzador) · fix8: `agent-kits/shared/test_journal_io_deadline.py` (nuevo), `agent-kits/shared/journal-io.py` (plazo inyectable solo bajo `PYTEST_CURRENT_TEST`), `agent-kits/shared/test_journal.py`, `tests/test_redact_fix3.py`, `tests/test_native_guard_failclosed.py` (prueba de plazo al paso serie), `tests/test_panel_review_panel_server.py` (2 pruebas al paso serie) · fix9: `tests/test_fix9_plazos_inyectados.py` (nuevo), `agent-kits/shared/test_journal.py` (sin aserciones de pared), `tests/test_panel_review_panel_server.py` (BODY_TIMEOUT inyectado, sin paso serie), `tests/test_redact_fix3.py` (demo ×12 por la decisión de la puerta y sonda al crecimiento real) · fix10: `agent-kits/shared/test_journal.py`, `tests/test_fix9_plazos_inyectados.py` (vigía), `tests/test_redact_fix3.py`, `agent-kits/shared/journal-io.py` y `journal-capture.py` (`settled`: espera el estado transitorio de dos enlaces), `skills/training-data-services/scripts/test_dataset_assembler.py` y `agent-kits/shared/test_knowledge_read_context.py` (rojos de réplica de tiempo de pared) · fix12: `agent-kits/shared/journal-io.py`, `agent-kits/shared/test_journal.py`, `tests/installer.test.mjs` (el test de la CLI colgada mide desde el arranque de la CLI) · fix14 y fix15 (declarados en fix15, gap 14): `install/install.mjs` (`detached: true` en `correr` y el vigilante de señales: cambio de conducta en Linux y macOS), `agent-kits/shared/journal-capture.py`, `agent-kits/shared/journal-io.py`, `agent-kits/shared/journal.py` (presupuesto por proceso y plazo desde el arranque), `agent-kits/shared/test_journal_fix14.py`, `agent-kits/shared/test_journal_fix15.py` (nuevo), `hooks/opencode-plugin.js` y `interop/opencode/plugins/custom-agents/index.js` (regenerado: opt-in de la actividad), `tests/opencode-plugin.test.mjs`, `tests/helpers/opencode-context.mjs`, `tests/installer.test.mjs` · fix16: `tests/codex-query-deadline.test.mjs` (RED 2: el plazo corre desde que el worker está listo), `tests/hook-budget.test.mjs`, `tests/opencode-plugin.test.mjs` (fixture de 120 s con sondeo), `tests/installer.test.mjs` (3 tests de registro previo), `agent-kits/shared/codex-plugin-state.mjs` (`terminateProcessTree` en paralelo, plazo desde que el worker está listo), `agent-kits/shared/journal-io.py` (mínimo en la primera espera real), `hooks/run-hook.mjs` (8 s de captura de OpenCode; la confirmación de la limpieza toma hasta 10 s dentro de la ventana de 20 s del catálogo del adaptador), `install/install.mjs` (registro previo, limpieza de restos; ya no existe `TIMEOUT_CAZA`: la caza de restos usa el barrido con identidad; fix18: las sondas `--version` no arrancan un worker), `tests/process-tree-fix17.test.mjs` (fix17: nuevo; el árbol con identidad, `queryPlan` y `runBounded`), `tests/artifact-dom-security.test.mjs` (fix17, gap 22: el navegador headless se relanza si sale con código ≠ 0), `docs/{,en/}FLOWS.md`, `docs/{,en/}INTEROP.md` y `docs/{,en/}observability.md` (fix17, gap 13: plazos reales), `tests/hook-docs-marker.test.mjs`, `tests/hook-guard-delivery.test.mjs`, `tests/test_console_transport.py` y `tests/test_mermaid_blocks.py` (fix17, gap 22: rojos de la suite completa atribuidos, ver j17) · `tests/test_statusline_cache.py` y `tests/test_agent_activity_store.py` (suite completa tras fix17, orquestador: dos tests que medían la máquina, ver «Suite completa tras fix17») · fix18: `agent-kits/shared/agent-activity-store.py`, `agent-kits/shared/local-state.py`, `agent-kits/shared/codex-plugin-state.mjs`, `install/install.mjs`, `statusline/roadmap-statusline.sh`, `tests/test_agent_activity_store.py`, `tests/test_agent_activity_tail.py`, `tests/process-tree-fix18.test.mjs`, `tests/test_statusline_scan_fix18.py`, `tests/installer.test.mjs`, `docs/FLOWS.md`, `docs/en/FLOWS.md` · fix18b: `agent-kits/shared/test_doctor.py`, `agent-kits/shared/test_plan_review_summary.py`, `agent-kits/shared/test_guardrail_fix14.py`, `tests/session-end-budget.test.mjs` · fix18c: `skills/training-data-services/scripts/test_case_recorder.py`, `skills/training-data-services/scripts/test_dataset_assembler.py` · fix18d: `skills/knowledge-services/scripts/test_backend_graphiti.py`, `skills/knowledge-services/scripts/test_backend_markdown_read.py` · fix19: `install/mkdir-p.mjs` (nuevo), `install/install.mjs`, `install/manifest-auth.mjs`, `tests/mkdir-p-fix19.test.mjs` (nuevo), `tests/codex-staging-fix19.test.mjs` (nuevo), `tests/installer.test.mjs` (fixture del bundle copia `mkdir-p.mjs`; `cli()` crea su TEMP con `mkdirP`)
- **Evidencia**: MEDIDA (Linux `python:3.11-slim`, un contenedor `-m 1g`, 4 CPU, `git archive` en LF, mismos **11.190 tests** en las dos formas; `testing/perf.md` lo veta el guardarraíl del rol, por eso consta aquí). CI VIEJA: bucle (163 ficheros `tests/test_*.py` ejecutados como script) **163 s** + pytest en serie **1.340 s** = **1.503 s**. CI NUEVA: bucle solo con los 3 ficheros sin `def test` (`test_coverage_check`, `test_mermaid_blocks`, `test_readme_badges`) **9 s** + `pytest -n auto -m "not serie" --durations=20` **615 s** (host sin otra carga; 734 s con carga) + paso `-m serie` **55 s** = **679 s ≈ 45 %** (pytest solo: 46 %; suelo del paralelo: `test_task_brief::test_ca08…` = 131-166 s). REBATE del plan: los ficheros que el bucle repetía eran **160 de 163** (no 23/27: casi todos los `tests/test_*.py` tienen ya `def test`). `-n auto` rompió tests que miden tiempo de pared o contienden por un lock con procesos hermanos; marcados `@pytest.mark.serie` (marcador registrado en `pytest.ini`, paso aparte sin xdist): `test_redact_fix3::test_linear_cost_on_pathological_inputs`, `test_redact::test_2_2_lineal_con_muchas_comillas_y_operadores`, `test_plan_review_summary::test_state_changed_during_read`, `test_agent_activity_store::test_d2_burst…` y `::test_2_1_lifecycle_signals_survive_sustained_tool_contention…`, `test_bench_session_end::test_bench_mide_in_process…` y `::test_bench_reporta_e2e_p50…`; `tests/test_suites_no_pytest.py::test_los_tests_de_tiempo_van_en_un_paso_serie_aparte` fija la lista y el paso. Residuo conocido de ESTA máquina (no de xdist): los dos de `redact` miden `< 1,5 s` y fallan también en serie aquí (tardan 1,7 s; en el runner de GitHub pasan) → `test_redact_fix3` falla en el paso serie en este entorno. GREEN: `pytest -q tests/test_ci_manual_copy.py tests/test_ci_skill_suites.py` → `16 passed`; `tests/test_suites_no_pytest.py -k "bucle or paraleliza or incluye or tiempo or hay_suites"` → `5 passed`; `ci.yml.MANUAL-COPY` y `.github/workflows/ci.yml` idénticos. Medición de uso (usage-meter, `plugin-audit-2/T-23`, ventana compartida con T-02..T-07 porque se hicieron entrelazadas): 0,55 h IA medidas, 33 min, ≈ 7,88 € estimado por tarifa; las demás tareas llevan estimación.
- **Runtimes**: La CI sigue ejecutando `node --test` de Codex y OpenCode. Con diferencia de conducta: en Linux y macOS `correr` lanza la CLI con `detached: true` (fix14) y tras un vigilante de señales (fix15), y el adaptador de OpenCode solo lanza el handler de actividad con `sesion.actividad: true` (fix15); en Windows no cambia la conducta.
- **Verificación**:
  - `pytest -q tests/test_ci_manual_copy.py tests/test_ci_skill_suites.py tests/test_suites_no_pytest.py` → verde (rojo antes: un test exige que el bucle solo ejecute las suites sin `def test_`)
  - en Linux (`python:3.11-slim`, LF): `python -m pytest tests agent-kits/shared -n auto -q --durations=20` → mismos tests y resultado y tiempo < 50 % del serie, anotado en `testing/perf.md`

**Criterios de aceptación**
- [x] El bucle solo ejecuta los ficheros que pytest NO recoge (sin `def test_`).
- [x] `-n auto` no rompe los tests que usan puertos, `os.chdir` o ficheros compartidos (los que fallen se marcan `xdist_group`/serie, con motivo).
- [x] Se publica `--durations` en el resumen de la CI.


RED: `tests/test_suites_no_pytest.py::test_el_bucle_de_ci_solo_ejecuta_lo_que_pytest_no_recoge y ::test_la_ci_paraleliza_pytest_y_publica_durations` falló con AssertionError: el bucle itera todo tests/test_*.py (sin grep -L) y falta pip install pytest-xdist / -n auto / --durations en ci.yml · 2026-11-11.

**fix1 a fix14 de T-23** — archivado LITERALMENTE (bytes sin cambios) en [execution-history.md](execution-history.md), sección «Archivado 2026-11-16 — T-23 fix1 a fix14» · SHA-256 `915865a00e3410bb34d98c6e0764fce39c7fb0db2d0816cde2808ffa862aec3c`. Se movió en fix17 por el tope de lectura de 256 KiB; lo vigente (fix17) sigue abajo.

**fix15 de T-23** — archivado LITERALMENTE (bytes sin cambios) en [execution-history.md](execution-history.md), sección «Archivado 2026-11-16 — T-23 fix15» · SHA-256 `b23a3903f817680accd73068cb150fd44ed71e9e06e477b754a3eb7afe64e37c`. Se movió en fix16 para dejar sitio al ledger bajo el tope de lectura; lo vigente (fix16) sigue abajo.

**fix16 de T-23** — archivado LITERALMENTE (bytes sin cambios) en [execution-history.md](execution-history.md), sección «Archivado 2026-11-16 — T-23 fix16» · SHA-256 `9be0ab2e8a81513385bb906f9d5f91f5a7576e0d0e772d575ec61bcfbc911a7b`. Se movió en fix17 por el tope de lectura de 256 KiB; lo vigente (fix17) sigue abajo.

**fix17 de T-23** — archivado LITERALMENTE (bytes sin cambios; incluye la suite completa tras fix17) en [execution-history.md](execution-history.md), sección «Archivado 2026-11-17 — T-23 fix17» · SHA-256 `43584ded2e4a99e0fc2054096a3d1737322da12293518a62d55722d0bd0d6cd4`. Se movió en fix18 por el tope de lectura de 256 KiB; lo vigente (fix18) sigue abajo.

**fix18 (intento 18, gaps 3, 4, 11, 13, 14, 15 y 16 de T-23; T-23 sigue `en-progreso`: falta la medida emparejada, del orquestador)** — `plugin-audit-2/T-23-fix18`; commits: los de T-06 más `887706f` (GREEN), `81db702`, `077b168`, `c4139e0`, `1cd0a54`, `b432e89` y `a7ac91d`.
- **Árbol de procesos de Windows que actúa (gap 3, punto 4).** `terminateProcessTree` lanza el barrido por identidad FUERA del job del worker: `cmd /c start "" /b powershell -EncodedCommand …` con `detached` (medido: un PowerShell hijo normal muere cuando el worker sale —job de libuv—; con `DETACHED_PROCESS` puro sale SIN ejecutar nada; vía `start /b` escribió su fichero con el padre muerto, `det2.mjs` E). Con la raíz VIVA basta `taskkill /T` (`spawnSync`, exit 0): NO se lanza el barrido (se ahorran 1,1-1,7 s por expiración y la CPU de un PowerShell CIM que nadie espera: tras el primer arranque de este diseño, ese barrido de fondo perturbaba la prueba de plazo siguiente y dio rojo en la suite node); solo si taskkill falla se cae al barrido; con la raíz muerta el barrido sobrevive al worker. `rootAlive` y `until` salen del evento `exit` del handle de la raíz (con el handle abierto el pid no se reutiliza) en `queryWorker` y `runBoundedWorker`; el barrido comprueba pid + fecha de creación justo antes de cada `Stop-Process`, en la misma orden. Prueba de producción: raíz muerta con un descendiente vivo (que retiene stdout) y un worker que sale con 300 ms de presupuesto → el descendiente muere (RED: sigue vivo a los 32 s; GREEN: muere en 3,7 s); `runBounded` real con la raíz muerta: descendiente vivo a los +0 s y **muerto a los +14 s, 0 huérfanos**; pid reutilizado (un proceso ajeno posterior a `until`, con su hijo): **ambos sobreviven** (8 s de espera); `/doctor` real (`node codex-plugin-state.mjs --project`) con un worker +2 s lento: termina en < 10 s y 0 huérfanos (gap 14: el diseño pedía +2 s y solo se midió con +1 s; ahora es test). La traza de fix17 que decía «confirma hasta 15 s» y «`until` cubre la raíz muerta» queda corregida con esto: el barrido ya no confirma (se quitó el bucle de 15 s) y `until` lo pasan los llamadores.
- **D2 por cola de añadidos (gap 4, punto 5; decisión del usuario).** `events.tail`: `record` añade UNA línea (`id` aleatorio, `at`, la entrada) con `O_APPEND` + `fsync` bajo el cerrojo (`StateIO.append`: ausente o fichero regular sin enlaces duros ni redirigido, y el descriptor abierto es el mismo que vio `lstat`) SIN leer ni validar el anillo; el escritor que supera `TAIL_FOLD_BYTES` (8 KiB, unos 16-25 eventos) —o una señal de ciclo de vida, `count_oversize` o `fold_tail`— PLIEGA: lee el anillo y la cola, aplica las líneas en orden con su instante, publica el anillo por CAS y DESPUÉS trunca la cola (`StateIO.truncate`, con la identidad comprobada antes); las líneas ya plegadas se reconocen por su `id` en `plegado` (hasta 512) y no se duplican. `history()` y `events_document()` ven anillo + cola; una línea final sin salto de línea (caída a mitad de la escritura) se ignora y cualquier otra corrupta falla cerrado; tope de la cola 64 KiB (`state_budget`). Se conservan el CAS por firma, el fallo cerrado, `recortado`, el tope de 256 KiB y `nowait` (un intento). Medida con la espera REAL (1 s, plazo de 1,3 s, sin escala) y CARGA AJENA medida (CIM `LoadPercentage` antes/después: 15-96 %): **8 de 8 en las 10 pasadas** (`d2_sin_carga.txt`); sonda de 16: **0 perdidos en 7 de 10 pasadas y 7, 8 y 9 perdidos en las otras 3** (motivo `state_busy`: 16 escritores × la retención del cerrojo —`_base`, `fsync`— pasan de 1 s con carga ajena del 55-81 %; no es un umbral del diseño y se anota). Retención media de `record` medida en `ld18`: antes 62-99 ms con el anillo lleno; ahora no lee el anillo.
- **Costes (gaps 15 y 16, punto 6).** `correr(cmd, ["--version"])` en Windows va por `execFileSync` directo (plazo de 30 s y, si expira, barrido con la raíz muerta): **0 arranques del worker de node por sonda** (test con un `--require` que registra cada arranque de node: 1 para la orden larga y 0 para la sonda; RED: 2). Statusline: el escáner cuenta pasos (`STATUSLINE_SCAN_STEPS=400`; pasados, «no puede decidir» y pinta Python con la entrada en la clave); test por razón 2/4/8 KB: los pasos no pasan de 3× el tope y una entrada real (~150 campos) cabe en la mitad del tope.
- **Traza y docs (punto 7).** `Archivos` de T-23 corregido (gap 11: «2 s» y `TIMEOUT_CAZA` 15 s); el test de `uninstall` (gap 13) queda REBATIDO con evidencia (abajo: `uninstall` no ejecuta `marketplace remove`; solo corre en Linux/macOS y se verificó en la réplica); FLOWS y su espejo EN (cola y barrido).
- **Interpretaciones (T-23).** **k10** `terminateProcessTree` admite `{deps}` (spawn/alive inyectables) solo para los tests; el barrido no se espera con la raíz muerta porque sobrevive al worker (la espera la haría un llamador que sale justo después). **k11** las sondas `--version` de Windows usan `execFileSync` y matan el árbol tras expirar con la raíz muerta, no con el worker. **k12** `fold_tail` es una entrada pública de mantenimiento: la usan los tests para comprobar lo que el camino caliente ya no informa (un anillo corrupto se detecta al plegar, no al añadir: `record` devuelve `ok` porque el evento es duradero). Los 22 tests de `test_agent_activity_store.py` que fijan lo que un evento hace al ANILLO (recorte, retención, CAS, validación, ventanas) cargan el módulo con `TAIL_FOLD_BYTES=1` (cada `record` añade y pliega al instante: el comportamiento antiguo) y 8 de ellos cambian su aserción (`record` → `ok` y `fold_tail` informa; lista de nombres con `events.tail`; el test del anillo precargado ahora fija que la ruta de herramienta NO lee el anillo y la de ciclo de vida sí); el del CAS usa instantes de 1 s distintos (Windows redondea a 100 ns).

- **Hallazgos de la suite completa (Windows y Linux) y su causa raíz.** (1) *`/doctor`*: la suite node dio un rojo (el test de /doctor con un worker +2 s lento: 10,29 s frente a los 10 s de doctor.py): el arranque de node del propio helper (0,3-1,5 s con carga) se sumaba al tope exterior de 9 s. Arreglo de producto: el helper descuenta su arranque (`performance.now()`): tope exterior = 9 s − arranque (mínimo 3 s) y límite = tope − 3 s (1-6 s), con `outer` explícito hasta el worker (`queryPlan({outer})`); RED con arranque lento del helper (1,5 s) y worker lento (2 s): **10,04 s sin el descuento y 9 s con él**. (2) Los dos tests de /doctor y los de «worker lento» de fix16/fix17 viven en un solo fichero (`process-tree-fix17.test.mjs`): node corre los ficheros en paralelo y los cuatro miden el plazo de pared. (3) *Privacidad*: la serie del panel (`test_panel_privacy`) cazó que la primera cola guardaba `session`/`agent` en claro; ahora guarda solo los seudónimos (`run_key`, `parent_key`, `session_key`) y un test lo fija. (4) El pin de revisión de `agent-activity-store.py` en `test_graphiti_security.py` sigue a la cola (`sha256_lf` nuevo, «sin red»). (5) Los arneses de bash real (`test_guardrail_differential*.py`, `fix15`, `fix16`, `fix17`) tenían un `timeout` de 60-90 s por forma: el arranque de un proceso msys (`nice`, `env`) tiene cola larga con carga (medido: 3 `nice` encadenados tardan 0,5-3,4 s y una vez **16,7 s**), así que cinco formas con `nice` dieron rojo bajo `-n 4`; el plazo del arnés pasa a 240 s (no es un plazo del producto). (6) **Gap 13 rebatido con evidencia:** la réplica Linux hizo fallar el test nuevo («uninstall no ejecutó `marketplace remove`»): `uninstall` NO ejecuta `marketplace remove` porque el registro `daycry` es compartido (`install/providers.mjs:421-427`: solo `siYaExiste` con `--force-marketplace`; test «Shared marketplace registration survives instance uninstall»); el test fija lo que SÍ deshace (manifiesto `incompleto` y caché) y que no hay `remove`. Verificado en Linux.

**Verificación (Windows y Linux).** **Windows** (carga ajena medida por CIM durante toda la sesión: 15-98 %, típica 50-90 %): `node --test --test-concurrency=2 tests/*.test.mjs` **587 tests, 578 pass, 0 fail, 8 skipped** en la cuarta corrida completa (las tres anteriores dieron 1, 2 y 3 rojos, cada uno con su causa raíz y arreglo en «Hallazgos»: el test de /doctor con un worker +2 s, el barrido de fondo que perturbaba la prueba siguiente y los márgenes de /doctor; el rojo de `SessionEnd capture … 1.5 s` de la tercera —mediana de 1,6 s con la máquina al 98 %— no se repitió y no es de fix18); pytest paralelo de la CI (`-n 4 -m "not serie"`, 15.558 tests, 1 h 15 min) **15.554 passed, 4 failed**: `test_doctor.py::test_f3fix4_gap148_*` ×2 (el límite de 2,5 s del backend falso con la máquina al 80-98 %; pasan aislados 3 de 4 veces: **no resuelto, ajeno a fix18**), `test_plan_review_summary::test_the_plan_rereads_respect_the_guard` (plazo de pared de la lectura; pasa aislado 2 de 2) y `test_diferencial15[LANG-sin-definir]` (arreglado: el arnés reintenta el registro vacío; 5 diferenciales en verde); serie: 58 passed y 2 failed en la primera pasada (el test d2 antiguo y `test_panel_privacy`, ambos arreglados y reejecutados en verde). Con la ráfaga REAL de D2, 8 de 8 en 10 pasadas (arriba). **Réplica Linux** (`t23m:ci`, un contenedor `-m 1g --cpuset-cpus 0-3`, árbol LF por `git ls-tree` + `cat-file`, Node 22; eliminado al acabar): dos pasadas completas sobre el HEAD final y el anterior: lint, handbook, evals, interop, bench y `release.py --check` **exit 0**; node **587 tests, 556 pass, 0 fail, 31 skipped** (en la primera pasada falló el test de `uninstall` y se rebatió el gap 13); serie **60 passed**; pytest paralelo **15.551 passed, 0 failed** la primera vez y **15.550 passed, 1 failed** la segunda (`test_guardrail_fix14::test_los_separadores_son_lineales_de_64k_a_250k_sin_git[3]`: 0,25 s → 1,31 s con factor de carga 1,5-2,0 frente a la cota de 1,0 s; es la cota del test, no del producto: medida la CPU del guardarraíl sobre esa entrada, **el nuevo cuesta 0,92-0,96× el de `ae56211`**). Mediciones de coste: statusline 2/4/8 KB → **400/400/400 pasos** (el tope; antes crecían con los tokens) y 140/223/316 ms por escaneo con la máquina saturada (antes 96/271/1.594 ms); guardarraíl 0,118 ms por orden frente a 0,108 de `ae56211`; sondas `--version` del instalador 0 arranques de worker (antes 1).

**fix18b (cuatro rojos que solo aparecían con la máquina cargada; sin cambio de producto).** (1) *`test_f3fix4_gap148_*`*: causa raíz, el ayudante `_linea_graphiti` corría el adaptador REAL contra un MCP falso con 250 entradas bajo el tope duro de `/doctor` (2 s + 0,5 s) y con carga el apretón de manos más la lectura lo rebasaban («no comprobado»); el tope ya tiene sus pruebas (C-09a, gap 94, gap 124), estas prueban la clasificación. Arreglo: `tope_ms=60000` en el ayudante; `_cfg_con_timeout_topado` sigue acotando la ventana a `CAPACIDAD_VENTANA_TOPE`=200 con cualquier `tope_ms`. Mutante (la rama gap148 de `_verificacion_incompleta` desactivada con `and False`): 2 de los 4 fallan. (2) *`test_plan_review_summary.py`*: causa raíz, plazos de 0,3 a 0,4 s medidos con `time.monotonic()` real y `time.sleep` de 0,5 a 0,6 s: con carga la lectura de un plan consumía por sí sola el plazo y cambiaba el camino ejercitado. Arreglo: fixture `clock` (reloj falso que sustituye `time` en el módulo; solo avanza con `clock.advance`) en `test_the_plan_rereads_respect_the_guard`, `test_the_grace_after_an_expired_deadline_is_small_and_bounded`, `test_a_really_expired_deadline_gives_partial_with_what_was_read` y `test_sixty_four_records_fit_the_envelope`. Mutantes: sin `_guard(recheck)` en la relectura falla `rereads`; con gracia de 5 s en lugar de 0,25 s fallan `grace` y `rereads`. (3) *`test_los_separadores_son_lineales_de_64k_a_250k_sin_git`*: causa raíz, la cota absoluta (1,0 s de CPU normalizada) dependía de la carga (el tiempo de CPU del propio proceso se multiplica por 3 a 5 con otra carga: SMT y caché; el factor de referencia no lo absorbía). Arreglo: la linealidad la prueba la razón entre tallas medidas en la misma pasada (ya existente, `< 10x`) y la cota absoluta pasa a 4,0 s normalizada (en reposo 0,45 s; un cuadrático, 160 s). Mutante cuadrático (`cmd[:i].count(';')` por carácter): k=0 `2,565 s -> 34,293 s` y k=3 `1,200 s -> 15,420 s` fallan. (4) *`tests/session-end-budget.test.mjs`* («SessionEnd capture … 1.5 s»; era `todo` en Windows): causa raíz, exigía una mediana de pared < 1,5 s del launcher Node + Python y arrancar `node` cuesta 1,4 a 2,3 s con carga. La regresión que guardaba (la captura hace más trabajo del previsto: imports pesados al cerrar, trabajo por línea del log, algo cuadrático) se cuenta ahora en llamadas de función Python (`sys.setprofile`; arranque 10.186, captura 8.037 con tope 24.000 y 20.000, y la captura con el log completo no sube más de 300 respecto de un log de una línea); el tiempo de pared se imprime como dato y el cierre por el launcher sigue exigiendo que ninguna captura no cortada pierda su envelope. Mutantes: un `import` pesado (38.771 llamadas de arranque) y una llamada por línea del log (8.044 -> 8.524) fallan. **Robustez** (4 procesos `while True: pass` durante toda la serie, 5 pasadas seguidas): gap148 `4 passed` ×5 (4,7 a 10,9 s); los cuatro de plazos de `test_plan_review_summary.py` `4 passed` ×5 (38 a 142 s); `session-end-budget` `pass 3 fail 0` ×5; separadores `[3]` `1 passed` ×5 (9,2 a 11,2 s). **Otros candidatos sin tocar** (misma familia de cota de pared, no se arreglan aquí): `test_los_separadores_con_git_*` y las pruebas `_es_lineal` de prefijos en `test_guardrail_fix12.py` (cota absoluta de 2,5 s de CPU sin normalizar), los plazos de 120 s de `test_deadline_expired_*`, `test_state_changed_during_read` y `test_plan_changed_during_read` (holgados, no rojos medidos), y `tests/hook-runtime.test.mjs` («independent of slow materialization startup»: `timeout` de 30 s).

**fix18c (siete tests de `training-data-services` rojos en Windows; sin cambio de producto).** Causa raíz: tras la actualización KB5135385 (2026-11-16, con reinicio) Windows rechaza `O_CREAT|O_EXCL` a través de una junction recién creada (`FileExistsError`, errno 17, sin crear nada en el destino; `O_CREAT` simple y la lectura siguen funcionando). Los tests de ventana TOCTOU (CWE-59/367: `test_f2fix4_gap82_padre_cambiado_*` ×4, `test_f2fix5_gap98_final_se_crea_*[antes_de_final]`, `test_t09_118_*`, `test_t09_136_140_*`) suponían que el SO SIGUE la junction y crea el fichero en el destino. Arreglo: sonda única por módulo `_so_sigue_la_junction_en_o_excl()` (crea una junction temporal e intenta `O_EXCL` a través de ella). Rama «sigue»: aserciones intactas. Rama «rechaza» (aserciones reales, sin `skip`): rechazo (`Rechazo`) con «el store cambio … la reserva … queda» o «CWE-59/367 … incompleto … se conserva», `approved/` y los demás destinos idénticos byte a byte (`_foto`; ni siquiera aparece `final/`), `otro/artifacts.json` intacto, el temporal del manifiesto ni se crea (`tamanos == []`) y el árbol curado queda vacío. El resto de pruebas con junction del directorio ya pasaban. Mutantes (`case-recorder.py`, revertidos): `_abrir_exclusivo` con `open(ruta, "wb")` (escribe a través del enlace) hace fallar 4 de 6 en recorder y 2 de 2 en assembler; borrar el contenido del destino ante `FileExistsError` hace fallar 4 de 6 en recorder (en assembler el árbol curado ya está vacío: no hay nada que borrar, el mutante no es observable). Suites completas: `test_case_recorder.py` 266 passed, 9 skipped; `test_dataset_assembler.py` 143 passed, 3 skipped.

**fix18d (tres rojos de la suite completa de Windows con la máquina saturada: dos de test, uno de PRODUCTO; usage-meter `plugin-audit-2/T-06-fix18d`).** (1) *`test_fix3_gap40_*` (graphiti)*: causa raíz, el presupuesto de publicación del adaptador es `max(1, timeout_ms/1000) x 4` = 8 s con el `timeout_ms: 2000` de la clase y la carga lo agotaba (`publication_budget_exhausted`); el test comprueba UUID de tombstone/supersedes, no el presupuesto. Arreglo mínimo (decisión del usuario: Graphiti se retira en T-08..T-10): la clase `TestGraphitiFase2Fix3` pasa `timeout_ms: 30000` explícito. (2) *`test_direct_read_redacts_local_display_metadata`*: el fixture `corpus` fijaba `read.timeout_ms: 1500` y `deadline = ahora + 1,5 s` de pared (`deadline_read_agotado`); ahora `READ_BUDGET_MS = 30000` (el máximo que admite `_READ_LIMITS`); los tests de plazo (`test_dribbling_*`, `test_expired_total_query_deadline_*` con reloj falso, `test_context_deadline_cannot_expand_configured_budget`) fijan su propio valor y siguen cubriendo el comportamiento. 5 corridas seguidas bajo 4 quemadores de CPU: 5/5 verdes. (3) *D2 (`test_d2_rafaga_sobre_el_anillo_lleno_*[8]`, garantía de producto: 8 hooks en ráfaga sobre el anillo lleno, TODOS registrados dentro de `TOOL_LOCK_WAIT` 1 s real; ni el plazo ni la espera se tocan)*: reproducido y medido con una sonda por fases (8 hijos, 4 quemadores): el cerrojo se retenía **150-250 ms por escritor** (`_base` 60-180 ms + `_ignore` 50-116 ms + `_enabled` + `_clean_temps` + append 6-70 ms), porque dentro del cerrojo se LEÍAN `owner.json`, `.gitignore`, `dev.json` y se listaba el directorio, y bajo saturación abrir un fichero para leer cuesta 25-120 ms; 8 x 200 ms > 1 s, de ahí `state_busy` y `deadline_exceeded`. **Arreglo de producto** (`agent-activity-store.py`): `_prepare_tool_event` valida ANTES del cerrojo y en paralelo (propietario, `.gitignore`, inventario; 6 intentos acotados porque el listado sin cerrojo compite con el escritor que crea `events.tail` y devuelve `changed_path`); dentro del cerrojo solo se comparan las firmas `stat` de `owner.json`, `.gitignore` y `dev.json` con las de la validación previa: iguales = vale; distintas (o sin validación previa: estado creado por la propia llamada, inventario fuera de presupuesto que la limpieza arregla) = la validación completa de antes corre dentro, así un opt-out o un cambio de propietario entre medias sigue impidiendo la escritura; `_clean_temps` en el camino caliente solo si la validación previa vio temporales. La marca de tiempo de la línea se toma dentro del cerrojo (orden de la cola intacto). **Tasa de fallo de la ráfaga bajo 4 quemadores (carga ajena 50-98 %)**: antes **11 de 12** corridas rojas (1-8 eventos perdidos, `state_busy` y `deadline_exceeded`); después **12/12 verdes** y 8/8 en la última verificación, 0 eventos perdidos; con la sonda, hold de 7-40 ms y total por escritor 0,10-0,33 s. TDD: el RED es la tasa medida (la ráfaga no es determinista) más tres tests deterministas nuevos en `tests/test_agent_activity_tail.py`: `test_fix18d_el_camino_caliente_no_lee_ni_lista_bajo_el_cerrojo` (**mutante**: el código previo, `git show HEAD:` del almacén, lo hace fallar con `assert [list_names, read_bytes...] == []`), `..._si_cambia_el_propietario_entre_la_validacion_y_el_cerrojo_se_revalida_dentro` y `..._un_opt_out_entre_la_validacion_y_el_cerrojo_impide_la_escritura`. Dos regresiones halladas por las suites y corregidas: un estado recién creado no tiene `.lock` al validar antes (cae a validar bajo el cerrojo) y 12 temporales > 8 daban `state_budget` antes de limpiar (`test_cleanup_is_capped_*`; ahora cualquier fallo de la validación previa cae al camino completo). Suites en verde: `test_agent_activity_store` 242 passed/1 skipped, `test_agent_activity_tail` 16/1, `test_panel_privacy` 3, `test_panel_activity_server` 49, `test_agent_activity_git` 8, `test_local_state_fix3` 7.

**fix19 (junctions: crear DIRECTORIOS a traves de una junction falla en Windows 11 26300 con KB5135385; defecto de PRODUCTO; usage-meter `plugin-audit-2/T-23-fix19`).** Causa raiz confirmada: `mkdir link/c` -> EEXIST sin crear nada, `mkdir -p link/a/b` -> ENOENT, y `open(...,'wx')` (O_EXCL) a traves de la junction -> EEXIST; crear/leer ficheros con `w` y `realpath(link)/x` funcionan. Python tiene el mismo comportamiento (`os.mkdir`, `os.makedirs`, `Path.mkdir`: FileExistsError 17). Dos efectos en el instalador: (1) `instalarCodexNativo` (scope project) montaba el home aislado con la cache del marketplace como JUNCTION a la cache real, asi que el `codex plugin add` NATIVO (el real tambien) no podia crear `<version>/.codex-plugin` ("el plugin no se habilita"): 12 rojos (3 de `codex-native-install.test.mjs` y 9 de `installer.test.mjs`). (2) H-11 (HOME/dotfile enlazado): el instalador creaba `plugins/`, el dotfile y la clave de `installer-auth-v1` bajo un HOME enlazado, y `cli()` del test su TEMP. Opciones: (a) helper `mkdirP` (resuelve el ancestro existente mas profundo y crea el resto desde su ruta real; igual semantica que `mkdir -p`, ficheros y enlaces colgantes siguen siendo error) y (b) no montar por junction. Evidencia: (a) por si solo NO arregla (1) porque el que crea el directorio es el binario externo; (b) es necesario. Elegido: (b) + (a), una sola fuente `install/mkdir-p.mjs` (`mkdirP`, `writeFileExclusive`). Cambios: el home aislado es un directorio REAL (con `tempRoot` resuelto por `realpathSync`: `mkdtemp` a traves de un TEMP enlazado colgaba el proceso en sincrono), el `add` nativo escribe ahi y la entrada se PROMUEVE a la cache real (`cpSync` a un hermano `.new-<pid>` en la ruta real + `rename`, con vuelta atras) solo si el add tiene exito: un fallo no toca la cache del usuario (antes el nativo escribia directo en ella). Verificacion mas estricta: `installedPath` debe ser el alias aislado, directorio real (no enlace). Cambio de conducta declarado: el nativo ya no ve (ni poda) versiones antiguas de la cache real al instalar en scope project. `mkdirP` sustituye a `mkdirSync(...,{recursive:true})` en `escribirAtomico`, `saveSharedCaches`, las copias de agentes nativos y de pasos, y la clave de autenticacion (`writeFileExclusive`). Las comprobaciones de enlaces (`regularPath`, `LINKED_PATH`) corren ANTES y no se tocan: "un enlace DENTRO del proyecto sigue rechazado" pasa. **RED** (`6d259ac`): `RED: codex-staging-fix19 "el home aislado NO enlaza la cache" fallo con ENOENT: mkdir ...\custom-agents-codex-*\plugins\cache\daycry\custom-agents.22.0\.codex-plugin · 2026-11-18`; `RED: codex-staging-fix19 "tempRoot que cruza un enlace" fallo con SIGTERM tras 20 s (cuelgue sincrono, proceso hijo con plazo) · 2026-11-18`; `RED: mkdir-p-fix19 fallo con ERR_MODULE_NOT_FOUND install/mkdir-p.mjs · 2026-11-18`; ademas `installer.test.mjs` H-11 "HOME enlazado" y los 12 de Codex proyecto (suite22) estaban rojos. **GREEN**: `mkdir-p-fix19` 5 tests (4 pass, 1 skip POSIX), `codex-staging-fix19` 3/3, `codex-native-install` 11/11, `installer.test.mjs --test-name-pattern H-11` 2/2. **Mutante** (`mkdir-p.mjs` reducido a `mkdirSync({recursive})`/`writeFileSync('wx')`, revertido): `mkdir-p-fix19` 2 rojos, H-11 "HOME enlazado" rojo. Revisados sin cambio (no producto o no alcanzable): `agent-kits/shared/*.py` y `hooks/` con `makedirs`/`mkdir` (`usage-meter.py:236`, `skill-index.py:363`, `guardrail-check.py:2879`, `agent-activity-store.py:72/74`, `journal-io.py:71`, `hooks/run-hook.mjs:322`) crean a lo sumo un nivel bajo `.claude/` del proyecto y los de estado rechazan expresamente el enlace; solo fallaria con directorios NUEVOS anidados bajo una junction (HOME/dotfile enlazado), sin ruta de usuario real conocida: queda ABIERTO como riesgo documentado. `escribirAtomico` con `temporaryDir` (`wx`) tampoco se toco: su directorio lo elige el llamante y es del instalador. `interop/` y los exportadores no hacen mkdir bajo dirs de usuario (escriben bajo el repo). Los 2 rojos de `process-tree-fix17.test.mjs` quedan fuera de alcance; este cambio no los toca. Suites tras el cambio (maquina al 100 % de CPU, un `cli()` tarda minutos): `installer.test.mjs` `Codex project native` 2/2 (A/B y fallo preserva activacion; antes rojos), H-11 2/2, `export-interop --check` 88 ficheros al dia, `lint_plugin` 0 errores, `evals/check` 0 errores, `scope-check` exit 0 (0 fuera de alcance), `ledger-lint` 0 incoherencias. `B12 ... hard kill` (plazo de 30 s hasta la barrera) da rojo con el codigo ANTERIOR a fix19 igual que con el nuevo bajo esta carga: es de plazo de pared, no de este cambio. Parada del dia: de los 6 pendientes NINGUNO llego a completar (`Codex command adapters` termino sin resultado en el log y se corto `status: Codex y OpenCode`; `F3 Codex` x3 no arranco); solo pasaron antes `Codex project native` x2. Siguen PENDIENTE en maquina libre: `Codex command adapters` x2, `status: Codex y OpenCode`, `F3 Codex` x3 (mismo mecanismo) y el `installer.test.mjs` entero (43 min en la suite completa).

**fix20 (cuatro rojos aislados tras fix18d; usage-meter `plugin-audit-2/T-06-fix20`, 0,64 h IA (medido) la sesion de cierre; 2026-11-19).** (1) *`test_graphiti_security` x4*: causa = la huella SHA-256 revisada de `agent-activity-store.py` en `_CARGAS_LOCALES_REVISADAS` no se actualizo en fix18d; el diff de fix18d no anade ningun import/importlib/exec (revisado), asi que no hay carga nueva: se actualiza la huella (el escaner no se toca; los tests de mutacion siguen detectando: 5 passed). HECHO. (2) *`test_local_state_fix3` x3*: NO es regresion de fix18d (con el almacen anterior `0a98fbd^` fallan igual); la captura de ciclo de vida cuesta ~285 operaciones de fichero y con 2-15 ms por `stat` (maquina con 5-6 nucleos de 12 ocupados por OneDrive y un `node` ajeno) supera el plazo real de 1 s (`deadline_exceeded`); las pruebas miden semantica de cerrojo, asi que inyectan `CUSTOM_AGENTS_ACTIVITY_DEADLINE_SCALE` (fixture autouse, como el resto de la suite). HECHO: 7 passed. (3) *D2 `test_d2_burst_of_eight...` (`state_busy`)*: defecto de PRODUCTO de fix18d: la espera de 1 s del cerrojo se contaba desde el arranque del hook, y la validacion previa sin cerrojo cuesta 0,2-0,6 s por proceso bajo carga (sonda por fases), dejando 0,1-0,4 s a la cola; ahora `stop` se calcula al acabar la preparacion (el plazo total `TOOL_DEADLINE` sigue acotando; constantes intactas). RED: `RED: test_fix20_la_espera_del_cerrojo_cuenta_desde_que_acaba_la_preparacion_sin_cerrojo fallo con state_busy · 2026-11-18` (commit `efc3f58`); GREEN: `test_agent_activity_tail` 17 passed/1 skipped. CIERRE (2026-11-19): (a) MUTANTE de `record()`: `stop` contado desde el arranque del hook (`started + TOOL_LOCK_WAIT`) -> `test_fix20_la_espera_del_cerrojo_cuenta_desde_que_acaba_la_preparacion_sin_cerrojo` en rojo (1 failed, 2 passed en `-k "fix20 or d2 or burst"`); revertido con `git checkout`. D2 con el mutante y la maquina sin quemadores sigue en verde (3/3): solo se manifiesta con la preparacion cara, que es lo que fija el test de fix20. (b) `tests/test_agent_activity_store.py` ENTERO con la maquina sin trabajo mio: **242 passed, 1 skipped en 209 s**. (c) D2 con 4 quemadores (`python -c "while True: pass"`, PIDs registrados y matados al final, 0 restantes): **NO es 12/12**. Primera tanda sin efecto real (los lanzadores de venv murieron: 12/12 invalido, descartado); con quemadores confirmados (100 % de CPU, OneDrive ajeno al 60 % antes de empezar): 8/12, 7/11, 6/10 en tres tandas. Sonda por fases (instrumentacion temporal, revertida): sin carga cada escritor tiene preparacion 0,1-0,4 s, espera 0,01-0,8 s y retencion 12-90 ms; bajo saturacion la preparacion llega a 3-17 s (procesos sin CPU) y aparecen retenciones aisladas de 0,9-1,1 s (el que tiene el cerrojo sin CPU) que agotan la espera real de 1 s del resto -> `state_busy` en 1 de 8 escritores; el `fsync` NUNCA fue la causa (<0,1 s). Las demas rojas de esas tandas (4 de 4 en la tanda oficial) NO son del burst: fallan en el `boot()` de la preparacion del test (`capture` -> `unavailable` con escala 20, es decir 20 s sin cerrojo) con corridas de 35-72 s. TOOL_DEADLINE 1,3 s y TOOL_LOCK_WAIT 1,0 s son decision del usuario y no se tocan; la retencion ya es lo minimo (stat + append); un proceso sin CPU con el cerrojo no lo arregla ningun diseno del almacen. ABIERTO: decidir si los quemadores se reducen/bajan de prioridad en esta maquina o si el 12/12 se exige solo con la maquina en reposo (12/12 sin quemadores medido: 12 pasadas verdes en la sesion previa y 3/3 en esta). (d) `test_t10fix3_184_marca_bloqueada_no_ordena_retirarla`: x20 en reposo **20/20**; con quemadores reales 2 rojos de 7 antes del arreglo. CAUSA RAIZ (defecto del TEST, probada): el resumen `res` trae `hasta` (fin del plazo de /doctor del recuento + 0,3 s de margen propio de `estado_dataset`) y el test lo reutiliza tras dos ensamblados y un bloqueo real; con la maquina saturada pasan >1,3 s y `estado_dataset` corta con «se agoto el tope de tiempo de /doctor» en vez del motivo de la marca bloqueada. No era el `CreateFileW` share 0 ni el `PermissionError` (el fallo es `parcial` + tope de tiempo, antes de llegar a la marca) ni KB5135385. RED determinista: el test antiguo con `time.sleep(2)` tras crear `res` -> falla siempre (1 failed); con el arreglo (`res.pop("hasta", None)`: el sujeto es el REMEDIO de una marca bloqueada, no el tope de tiempo, que cubren los tests de `hasta`) y el mismo `sleep(2)` -> pasa. GREEN: x10 con quemadores reales **10/10** (una pasada de 136 s por saturacion) y x20 en reposo 20/20. (e) Puertas: `lint_plugin.py` 0 errores (16 avisos preexistentes), `export-interop.py --check` 88 ficheros al dia, `evals/check.py` 0 errores, `ledger-lint` 0 incoherencias, `scope-check` exit 0.

**fix21 (T-23: `process-tree-fix17.test.mjs` gap 3 en rojo en maquina sin trabajo propio; defecto de TEST, no de producto; usage-meter `plugin-audit-2/T-23-fix21`).** Reproduccion: 1 de 4 solo, 2 de 2 en el fichero entero (el rojo es `un huerfano legitimo ... si muere`, la espera de 10 s). Causa raiz medida: el producto NO cambio desde fix18 (`0e32b12`); fix18 convirtio el barrido de respaldo de la raiz muerta en un PowerShell CIM lanzado con `cmd /c start /b` que NADIE espera (antes, `4eaf573`, `terminateProcessTree` esperaba al barrido con `Atomics.wait`), asi que el huerfano legitimo muere cuando acaba SU PowerShell: arranque ~1 s + foto CIM 1,3-3 s en frio; 4-6 s medidos con dos barridos a la vez (como hace el test) y 3,9-13,6 s en el fichero con OneDrive al 60 % de CPU y Windows 11 26300 (KB5135385). Con 10 s de espera el test era un reloj de pared sobre algo que no es su sujeto. NO se filtro ningun proceso: en 8 pasadas aisladas y 14 del fichero el huerfano murio siempre (3,9-13,6 s). Hallazgo adicional (debilidad real del test): la asercion `alive(v)===true` de la victima anterior se evaluaba AL INSTANTE, con el barrido asincrono aun sin correr: el MUTANTE (`-ge` -> `-lt` en la comparacion de fechas de `sweepScript`) seguia en verde. Arreglo (solo el test): `barridoEsperable()` inyecta `deps.spawn` (el producto ya lo admite) y lanza el mismo PowerShell como hijo directo cuyo `exit` se espera; la asercion de supervivencia espera a que el barrido ACABE y solo entonces mira; el control positivo espera hasta 60 s y anota la latencia con `t.diagnostic`; el test de «presupuesto» sustituye el `sleep(5000)` de fix18 (menor que un barrido de 3-13 s) por la espera real; el de /doctor anota con `t.diagnostic` el total y si aparecio el flag. RED: el rojo preexistente (`✖ ... un huerfano legitimo ... si muere`, test:53). MUTANTE con el test final: `-ge` -> `-lt` en `sweepScript` -> `AssertionError: la victima es anterior al lanzamiento ... no se mata` (revertido con `git checkout`). GREEN: `node --test tests/process-tree-fix17.test.mjs` x5 consecutivas = 8 pass / 0 fail (42-55 s cada una). ABIERTO (no tocado): el test de /doctor (`gap 14`, plazo de pared de 9 s con ~1 s de margen: 7,5-8,2 s) dio rojo en 3 de 7 pasadas intermedias del fichero con la maquina ocupada (flag ausente: el CLI falso no llego a arrancar) y verde 5/5 en las finales; su sujeto ES el plazo, asi que no se relaja; sigue sensible a la carga ajena.

### T-24 — Hooks: UserPromptSubmit asíncrono, un handler post-edición, carga perezosa (4.8)

- **Descripción**: `UserPromptSubmit` es síncrono y no emite nada (`hooks/hooks.json:105-115`; 1,2-2,1 s por prompt medidos), cada edición lanza `node` por tres handlers y `SessionStart` compila 6.700 líneas de Python antes de comprobar si hay proyecto. Se marca `async`, se unen los handlers de `PostToolUse` en uno y se carga perezosamente.
- **Changelog**: Los hooks añaden menos latencia por prompt y por edición.
- **Estado**: borrador
- **Tiempo humano**: est. 5h · real —
- **Tiempo IA (ejec.)**: est. 1.2h · real —
- **Dependencias**: T-23
- **Archivos**: `hooks/hooks.json`, `hooks/run-hook.mjs`, `hooks/session-context.py`, `hooks/ledger-post.py`, `hooks/opencode-plugin.js`, `scripts/export-interop.py`, `interop/codex/hooks.json`, `interop/opencode/plugins/custom-agents/**`, `tests/{test_hooks_config,test_bench_hooks,test_session_context,test_export_interop}.py`, `tests/{opencode-plugin,hook-runtime,hook-budget}.test.mjs`, `docs/{,en/}INTEROP.md`, `docs/{,en/}observability.md`
- **Runtimes**: Claude: `async` y handler único; Codex y OpenCode: solo lo que el exportador y el adaptador soportan (ver criterio).
- **Verificación**:
  - `pytest -q tests/test_hooks_config.py -k async_prompt` → `passed` (rojo antes: `user-prompt-capture.sh` sin `async` en `hooks/hooks.json:105-115`)
  - `pytest -q tests/test_bench_hooks.py tests/test_session_context.py tests/test_export_interop.py` → verde; `node --test tests/opencode-plugin.test.mjs tests/hook-runtime.test.mjs` → verde
  - puertas de runtimes (cabecera) → verde
  - lectura (manual, sesión real; M-D) → en Codex el hook de `UserPromptSubmit` con `async` captura el prompt sin bloquear el turno; si no, el exportador no lo propaga

**Criterios de aceptación**
- [ ] Medido (`test_bench_hooks.py`): el turno ya no espera al hook de `UserPromptSubmit` en Claude (hoy 1,2-2,1 s) y una edición dispara un solo `node`.
- [ ] Codex: `interop/codex/hooks.json` solo marca `async` donde ya lo hace el exportador (`:103`, actividad); ninguna suite demuestra que lo honre en `UserPromptSubmit`: no se propaga sin M-D.
- [ ] OpenCode no cambia: su catálogo de bindings (`hooks/opencode-plugin.js:28-34`) ya tiene un `post` único y no existe `async`; `SessionStart` sin proyecto no importa módulos pesados.

### T-25 — Retirar los cuatro alias shell de hooks y apuntar sus tests al lanzador (4.2)

- **Descripción**: `hooks/run-hook.mjs:331-345` ejecuta Python para cuatro alias shell: `session-context.sh` (330 líneas), `session-journal.sh` (86), `subagent-progress.sh` (41) y `user-prompt-capture.sh` (54): 511 líneas. NO lo son `mark-docs-pending.sh` (registrado en `hooks.json`, pasa por `runtime-entry.sh`), las dos guardias de copias locales ni `ledger-lint-warn.sh`/`progress-line.sh` (en `known`, `:130-132`): se quedan. Los tests de los cuatro pasan al lanzador; los nombres `*.sh` se CONSERVAN como identidades de hook (`interop/codex/hooks.json`, `hooks/opencode-plugin.js:29-33`), o se declara la ruptura.
- **Changelog**: Los hooks ejecutan y se prueban por el mismo camino: se eliminan los scripts shell que nadie ejecuta.
- **Estado**: borrador
- **Tiempo humano**: est. 5h · real —
- **Tiempo IA (ejec.)**: est. 1.2h · real —
- **Dependencias**: T-24
- **Archivos**: `hooks/{session-context,session-journal,subagent-progress,user-prompt-capture}.sh` (borrar), `hooks/run-hook.mjs`, `tests/{test_hooks_shell,test_session_context,test_hooks_config,test_export_interop,test_ledger_post,test_memory_path,test_native_guard_launcher,test_console_encoding,test_plugin_panel}.py`, `tests/{hook-runtime,hook-budget,hook-post-preflight,opencode-plugin}.test.mjs`, `tests/fixtures/panel-redesign/bundle/hooks/**`, `agent-kits/shared/{README.md,doctor-reference.md,doctor.py,journal.py,progress-report.py,skill-index.py,test_doctor.py}`, `skills/plugin-panel/scripts/build_panel.py`, `docs/{CONVENTIONS,FLOWS,SPECIALIZATION,observability}.md`, `docs/en/{CONVENTIONS,FLOWS,SPECIALIZATION,observability}.md`, `evals/README.md`, `.gitignore`, `interop/**` (regenerado); en todos solo las líneas que citan los cuatro alias
- **Runtimes**: Los `.sh` son identidades de hook: en Codex (`interop/codex/hooks.json`) y OpenCode (`hooks/opencode-plugin.js:29-33`, `tests/opencode-plugin.test.mjs`) se conservan los nombres; renombrarlos rompería instalaciones hechas.
- **Verificación**:
  - `pytest -q tests/test_hooks_shell.py tests/test_session_context.py tests/test_hooks_config.py` → verde: los 74 casos de `test_hooks_shell.py` siguen o se sustituyen con motivo escrito; `test_session_context.py:174` (que compara con el shell) pasa a una referencia fija
  - `node --test tests/hook-runtime.test.mjs tests/opencode-plugin.test.mjs tests/hook-post-preflight.test.mjs` → verde (aceptan los nombres `*.sh`, `opencode-plugin.test.mjs:125,179,461`)
  - puertas de runtimes (cabecera) → verde
  - lectura (manual, instalación real; M-E) → una instalación previa de Codex u OpenCode se actualiza y los hooks siguen disparando con los mismos nombres

**Criterios de aceptación**
- [ ] Los cuatro `.sh` no existen y los hooks siguen funcionando en Claude, Codex y OpenCode con los mismos identificadores (`grep -c "\.sh" interop/codex/hooks.json hooks/hooks.json` igual que antes).
- [ ] Los tests cubren Windows y Linux (comillas, `-I -S`, timeouts) y los casos que afloren se arreglan en el `.py`; los cinco shells que se quedan siguen con sus tests.

### T-26 — Quitar las copias literales dentro de agent-kits/shared (4.3)

- **Descripción**: `journal.py:262-553` replica `redact.py` y `task-brief.py:662-922` replica `ledger-lint.py`, módulos que ya se importan entre sí en `agent-kits/shared`. Se borran las copias intra-`shared` (−550 líneas) y se conservan las que cruzan a `skills/`. ADR-016 y `copias.json` las declaran: se enmiendan.
- **Changelog**: journal y task-brief usan directamente redact y ledger-lint en lugar de llevar su propia copia.
- **Estado**: borrador
- **Tiempo humano**: est. 4h · real —
- **Tiempo IA (ejec.)**: est. 1h · real —
- **Dependencias**: T-19, T-08
- **Archivos**: `agent-kits/shared/copias.json`, `tests/test_copias_declaradas.py`, `agent-kits/shared/{journal,task-brief,redact,ledger-lint}.py`, `agent-kits/shared/test_{journal,task_brief}.py`, `docs/knowledge/adr/ADR-016-copias-declaradas-con-test-de-identidad.md` (enmienda vía `knowledge-curation.py propose`)
- **Verificación**:
  - `pytest -q tests/test_copias_identidad.py` → verde con el registro reducido (rojo antes: el test aún exige las copias que se borran)
  - `pytest -q agent-kits/shared/test_journal.py agent-kits/shared/test_task_brief.py agent-kits/shared/test_journal_selection.py` → verde; sin el módulo canónico → aviso, no traceback

**Criterios de aceptación**
- [ ] Las copias borradas salen de `copias.json` y queda escrita la propuesta de enmienda de ADR-016.
- [ ] Cuando el módulo canónico falta (kit suelto), journal y task-brief degradan con aviso (lo que antes cubría la copia).
- [ ] Las copias que cruzan a `skills/` siguen guardadas por el test de identidad.

### T-27 — Instalador: comprobaciones duplicadas y ramas muertas (4.10)

- **Descripción**: `install/install.mjs` (3.010 líneas) repite 5 comprobaciones de «dentro de la raíz» (`:1624-1646`); el análisis cree inalcanzables unas ramas legacy (`:466-497`), pero `:464-470` es la detección de copia heredada de OpenCode: hay que probar con cobertura cuáles están muertas. El hallazgo 4.12 (capa bash del lanzador solo para guardrails) no se sostiene: `runtime-entry.sh` también ejecuta `mark-docs-pending.sh`, registrado en `hooks/hooks.json`; queda fuera.
- **Changelog**: El instalador y el lanzador pierden código inalcanzable sin cambiar lo que instalan.
- **Estado**: borrador
- **Tiempo humano**: est. 2.5h · real —
- **Tiempo IA (ejec.)**: est. 0.7h · real —
- **Dependencias**: T-25
- **Archivos**: `install/install.mjs`, `install/providers.mjs`, `tests/{installer,install-auth,codex-native-install}.test.mjs`, `docs/{,en/}INSTALL.md`
- **Runtimes**: El instalador es la vía de Codex y OpenCode: no se retira ninguna vía de instalación.
- **Verificación**:
  - `node --test tests/installer.test.mjs tests/install-auth.test.mjs tests/codex-native-install.test.mjs` → mismos casos en verde (rojo antes: un test fija la comprobación única de raíz)
  - `node --experimental-test-coverage --test tests/installer.test.mjs` → las ramas que se retiran figuran sin cobertura; el resto se conserva
  - puertas de runtimes (cabecera) → verde
  - lectura (manual, instalación real; M-F) → instalar y desinstalar en un directorio temporal con OpenCode y Codex da el mismo manifiesto que antes

**Criterios de aceptación**
- [ ] Una sola función comprueba «dentro de la raíz»; solo se retira lo que la cobertura prueba inalcanzable.
- [ ] No se retira ninguna vía de instalación de Codex (nativo) ni de OpenCode (copia), incluida la detección de copia heredada; instalador y desinstalador dan el mismo manifiesto.

### T-28 — Borrar el índice FTS5 de knowledge-find (4.6)

- **Descripción**: El índice FTS5 (`knowledge-find.py:967-998`, `usar_indice`) no ahorra lectura ni parseo (`knowledge-index.sqlite` y sus `.tmp` aparecen en `.claude/`). Se borra tras comprobar con un test de caracterización que el orden de resultados no cambia. Hasta −280 líneas.
- **Changelog**: La búsqueda de memoria técnica ya no mantiene un índice SQLite que no acelera nada.
- **Estado**: borrador
- **Tiempo humano**: est. 5h · real —
- **Tiempo IA (ejec.)**: est. 1.2h · real —
- **Archivos**: `agent-kits/shared/{knowledge-find,doctor}.py`, `agent-kits/shared/{test_doctor,test_knowledge_view}.py`, `agent-kits/shared/{README,doctor-reference}.md`, `commands/doctor.md`, `docs/{observability,reference/doctor}.md`, `docs/en/{observability,reference/doctor}.md`, `tests/{test_knowledge_find,test_knowledge_candidates,test_memory_local_recovery}.py`, `.gitignore`, `interop/**` (regenerado)
- **Verificación**:
  - `pytest -q tests/test_knowledge_find.py -k orden_caracterizacion` → `passed` ANTES del borrado, sobre un corpus fijo (golden del orden actual)
  - el mismo test tras el borrado → `passed` y `knowledge-find.py --contexto x` sin crear `*.sqlite`; `pytest -q agent-kits/shared/test_doctor.py` → verde
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**
- [ ] El orden de resultados es idéntico (corpus de caracterización) y no se crean ficheros `.sqlite` ni `/doctor` los espera.
- [ ] El tiempo de búsqueda del corpus de ejemplo no empeora (medida anotada en `testing/perf.md`); si el golden revela otro orden o tiempo, la tarea se cancela con motivo.

### T-29 — Reducir serve_panel a servidor de revisión de plan (4.7)

- **Descripción**: Hay dos servidores HTTP de panel; `serve_panel.py` (1.575 líneas) solo aporta la revisión de plan (`console_service.py:19` lo carga como `LEGACY`). Se reduce a esa función. Hasta −600-800 líneas.
- **Changelog**: El panel conserva un servidor y un módulo mínimo para la revisión de planes.
- **Estado**: borrador
- **Tiempo humano**: est. 6h · real —
- **Tiempo IA (ejec.)**: est. 1.5h · real —
- **Dependencias**: T-23
- **Archivos**: `skills/plugin-panel/scripts/{serve_panel,console_service,build_panel,panel_data}.py`, `skills/plugin-panel/assets/page-cartera.js`, `tests/e2e/panel-csp-spike.mjs`, `tests/{test_console_encoding,test_console_service,test_panel_activity_server,test_panel_console_perf,test_panel_fix1,test_panel_fix2,test_panel_fix3,test_panel_large_roadmaps,test_panel_memoria_fix1,test_panel_memory_server,test_panel_pages,test_panel_plan_ui,test_panel_privacy,test_panel_review_panel_server,test_panel_review_server,test_panel_server}.py`, `tests/test_console_codex.py`, `tests/test_console_opencode.py`, `agent-kits/shared/README.md`, `docs/agents/CONTRACTS.md` (11 menciones), `docs/{,en/}FLOWS.md`, `docs/{,en/}PLUGIN-PANEL.md`
- **Runtimes**: La consola lee sesiones de los tres runtimes (`tests/test_console_*`).
- **Verificación**:
  - `pytest -q tests/test_panel_server.py tests/test_panel_review_server.py tests/test_panel_review_panel_server.py tests/test_panel_review_ui.py tests/test_plugin_panel.py tests/test_panel_contract_golden.py` → verde (los que cubren rutas retiradas se eliminan o reasignan con motivo)
  - `pytest -q tests/test_panel_console_perf.py tests/test_panel_privacy.py` → verde
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**
- [ ] La revisión de plan funciona igual (mismo contrato golden).
- [ ] Las rutas HTTP retiradas no las usa ninguna página ni la consola (`grep` en `panel_pages.py`).
- [ ] `wc -l skills/plugin-panel/scripts/serve_panel.py` < 800.

### T-30 — Renombrar los tests por conducta (4.11)

- **Descripción**: Entre 840 [V] y 1.275 [M] tests se llaman como la historia de la remediación (`test_f4fix2_5_*`; hay 8 ficheros `tests/test_f4fix*.py` y más funciones en otras suites) y 125 ficheros fijan prosa. Se renombran por conducta (sin cambiar aserciones) y los invariantes de prosa pasan al linter donde ya haya una puerta.
- **Changelog**: Los tests se nombran por lo que comprueban y no por la iniciativa que los creó.
- **Estado**: borrador
- **Tiempo humano**: est. 5h · real —
- **Tiempo IA (ejec.)**: est. 1.2h · real —
- **Dependencias**: T-26, T-08
- **Archivos**: `tests/test_f4fix1_kit.py`, `tests/test_f4fix1_misc.py`, `tests/test_f4fix2_{journal,kit,misc}.py`, `tests/test_f4fix3_{journal,kit,misc}.py`, `tests/test_hook_network_egress.py` (28 referencias a `test_f4fix`, tras T-08), `testing/renombrado.md` (mapa)
- **Verificación**:
  - `python -m pytest --collect-only -q tests agent-kits/shared` antes y después → mismo número de tests y mismos nodos salvo el renombrado (mapa en `testing/renombrado.md`)
  - `python -m pytest tests agent-kits/shared -n auto -q` en Linux → mismo resultado (CONTRACTS cita tests existentes)

**Criterios de aceptación**
- [ ] Cero aserciones cambiadas: el diff de cada test es solo el nombre.
- [ ] Las filas de `docs/agents/CONTRACTS.md` que citan el test antiguo se actualizan (columna Puerta).
- [ ] Ningún nombre nuevo menciona iniciativa, fase o `fixN`.

## Fase 5 — Alcance y entrenamiento

**Estado**: borrador · **Est.**: 26h humanas · **Real**: — · 1300 € · 1800k tokens · Sin bloqueo por decisión: T-32 solo se ejecuta si T-31 concluye (a).

### T-31 — Evaluar training-data-services frente a una exportación a posteriori (sin código)

- **Descripción**: Evaluación corta, sin código de producción, que lee `skills/training-data-services/` (`SKILL.md`, `case_schema.py`, `case-recorder.py`, `dataset-assembler.py`, `dedup.py`, `propose-from-case.py`) y la spec y el design de `2026-09-16-dev-cycle-dataset`, y responde con `fichero:línea`: (1) qué campos del caso no se reconstruyen después desde ledger, git, brief y transcripciones; (2) qué aporta la marca Gold humana frente a «pasó revisión y qa» y si queda como paso opcional sobre el JSONL; (3) qué del ensamblado merece conservarse (dedup por shingles, benchmark por familia, exportación sin sobrescribir) y cuántas líneas son; (4) qué necesita de la skill la rama `docs/model-routing-discovery-2e32c1` (solo `git show` de su ledger y spec); (5) de dónde sale la trayectoria en Codex y OpenCode. Veredicto: (a) sustituir y retirar la captura en vivo, (b) conservar el ensamblado y retirar el grabador, (c) dejarlo. Medida previa: la skill tiene 6.400 líneas de código y 11.808 de test; (a) las retira casi todas, (b) retira ≈3.625 de código y ≈7.073 de test, (c) ninguna.
- **Changelog**: Se documenta qué hace falta de training-data-services.
- **Estado**: borrador
- **Tiempo humano**: est. 3h · real —
- **Tiempo IA (ejec.)**: est. 0.8h · real —
- **Archivos**: `docs/roadmap/2026-11-10-plugin-audit-2/testing/evaluacion-training.md` (nuevo; solo lectura del resto)
- **Runtimes**: Pregunta 5: de dónde sale la trayectoria en Codex y OpenCode (o si el caso queda sin ella).
- **Verificación**:
  - `wc -l skills/training-data-services/scripts/*.py` → cifras por opción (a), (b), (c) en el informe
  - lectura: el informe responde los 5 puntos con `fichero:línea`, nombra el veredicto y cita `git show docs/model-routing-discovery-2e32c1:<ledger y spec>`

**Criterios de aceptación**
- [ ] Los 5 puntos tienen respuesta con evidencia y las líneas de código y de test que desaparecen en cada opción, medidas.
- [ ] El punto 5 dice, por runtime, si hay transcripción equivalente a la que lee `usage-meter.py`, o declara que el caso queda sin trayectoria.

### T-32 — Exportación a posteriori de casos de entrenamiento y retirada de la captura en vivo (opción a, condicionada a T-31)

- **Descripción**: Condición de ejecución (única puerta): solo se ejecuta si T-31 concluye (a) y no encuentra campos de un caso que no se puedan reconstruir después. Entonces, un script determinista recorre iniciativas cerradas y escribe JSONL con petición (`spec.md` y descripción de la tarea), contexto (brief de `task-brief.py`), respuesta (diff de los commits de la tarea), etiqueta de calidad (lentes y veredicto de qa del ledger) y trayectoria (transcripciones que ya lee `usage-meter.py`). Se retiran el grabador, el almacén de casos y lo que dependa: la capacidad `training` de `/setup`, `/doctor` y `capabilities.py` (36 menciones; hoy importa `case_schema.py`), la dependencia de `agents/qa.md` y la iniciativa `dev-cycle-dataset`, que se cierra como «superada por evaluación» con puntero a este plan.
- **Decidido por el usuario el 2026-11-10**: opción (a), CONDICIONADA al veredicto de T-31, que es la única puerta que queda: si T-31 concluye (a), la tarea se ejecuta sin volver a preguntar; si concluye (b) o (c), o encuentra datos que no se pueden reconstruir después, la tarea se detiene y vuelve al usuario con la evidencia.
- **Changelog**: Los casos de entrenamiento se exportan a posteriori desde el ledger y git; se retira la captura en vivo.
- **Estado**: borrador
- **Tiempo humano**: est. 10h · real —
- **Tiempo IA (ejec.)**: est. 2.5h · real —
- **Dependencias**: T-31; T-08
- **Archivos**: `skills/training-data-services/**` (nuevo `scripts/export-cases.py`; se retiran grabador, `propose-from-case.py` y almacén), `agent-kits/shared/capabilities.py`, `agent-kits/shared/test_capabilities.py`, `agent-kits/shared/doctor-reference.md`, `commands/setup.md`, `commands/doctor.md`, `agents/qa.md`, `agent-kits/shared/modules.json`, `evals/cases/skill-training-data-services.json`, `docs/roadmap/2026-09-16-dev-cycle-dataset/{spec,improvement-plan,tasks}.md`, `docs/roadmap/README.md`, `CLAUDE.md`, `docs/{,en/}README.md`, `CHANGELOG.md`, `CHANGELOG.es.md`, `interop/**` (regenerado)
- **Runtimes**: Claude: trayectoria desde las transcripciones que lee `usage-meter.py`; Codex y OpenCode: según T-31 (sin transcripción equivalente, el caso se exporta sin trayectoria).
- **Verificación**:
  - `pytest -q skills/training-data-services/scripts agent-kits/shared/test_capabilities.py agent-kits/shared/test_doctor.py` → verde (rojo antes: `export-cases.py` no existe y un test exige que `/doctor` ya no mida la capacidad `training`)
  - `python skills/training-data-services/scripts/export-cases.py --help` y sobre una iniciativa cerrada de prueba → JSONL reproducible byte a byte; `git grep -l "case-recorder" -- . ':!docs/roadmap' ':!CHANGELOG*'` → vacío
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**
- [ ] Puerta: T-31 concluye (a) sin datos irreconstruibles; si no, no se implementa nada y la tarea vuelve al usuario con la evidencia de `testing/evaluacion-training.md`.
- [ ] La exportación es determinista, no sobrescribe y marca los casos sin trayectoria (según T-31); el Gold humano queda como paso opcional si T-31 lo justifica.
- [ ] `/setup`, `/doctor`, `capabilities.py` y `qa.md` ya no citan el grabador ni la captura en vivo; `dev-cycle-dataset` queda cerrada como superada, con puntero.

### T-33 — Fusionar los modos lite y subagentes (3.5)

- **Descripción**: Hoy conviven el flujo clásico, el perfil `lite` (secuencial, techo de brief, writer obligatorio; `commands/dev-cycle.md:78-90`) y `subagentes` (lote paralelo y worktrees por tarea). `lite` pasa a ser un preajuste de `subagentes` descrito en `phase3-subagents.md`, sin prosa propia en `dev-cycle.md`; `execution-profile.py` sigue aceptando `perfil: lite` como alias. El modo único queda fuera de este plan (ver «fuera de alcance»).
- **Decidido por el usuario el 2026-11-10**: se fusiona `lite` con `subagentes`; el modo único se aplaza y queda fuera de este plan (no hay datos de uso del lote paralelo).
- **Changelog**: El perfil lite del ciclo de desarrollo pasa a ser un preajuste de subagentes.
- **Estado**: borrador
- **Tiempo humano**: est. 5h · real —
- **Tiempo IA (ejec.)**: est. 1.2h · real —
- **Dependencias**: T-19
- **Archivos**: `agent-kits/shared/{execution-profile,task-brief,doctor}.py`, `agent-kits/shared/{README,ledger-write}.md`, `agent-kits/dev-cycle/references/phase3-subagents.md`, `commands/{dev-cycle,setup,doctor}.md`, `agents/implementer.md`, `skills/{adversarial-review,tdd}/SKILL.md`, `tests/{test_lite_profile,test_native_guardrail_dispatch}.py`, `docs/{CONVENTIONS,FLOWS,INTEROP}.md`, `docs/en/{CONVENTIONS,FLOWS,INTEROP}.md`, `docs/agents/{CONTRACTS,implementer}.md`, `docs/guides/{audit-remediation,quality-playbook,subscription-efficiency}.md`, `docs/en/guides/audit-remediation.md`, `docs/{,en/}reference/core-workflows.md`, `interop/**` (regenerado)
- **Runtimes**: `dev.json` y `execution-profile.py` los leen los tres runtimes por igual; el cuerpo de `dev-cycle` se exporta a Codex (command-skill) y OpenCode (comando) y se regenera; sin diferencia de conducta.
- **Verificación**:
  - `pytest -q tests/test_lite_profile.py -k preajuste` → `passed` (rojo antes: `perfil: lite` no equivale a `subagentes: true` + secuencial + techo de brief)
  - `pytest -q tests/test_lite_profile.py tests/test_native_guardrail_dispatch.py tests/test_dev_cycle_split.py agent-kits/shared/test_task_brief.py agent-kits/shared/test_doctor.py` → verde
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**
- [ ] Un `dev.json` antiguo con `perfil: lite` sigue leyéndose sin error y produce el mismo brief y los mismos flags efectivos; `doctor.py` lo acepta.
- [ ] `commands/dev-cycle.md` ya no tiene párrafo propio de `lite` y el ahorro de la vía rápida (`test_dev_cycle_split.py`) sigue ≥ 6.000; el lote paralelo y `worktree` se conservan y el CHANGELOG declara la fusión.

### T-34 — Retro fuera de la vía rápida (3.6)

- **Descripción**: Hoy `retro-gate.py` exige `retro.md`, fila de calibración y entrevista incluso para un cambio de dos líneas. En la vía rápida la retro pasa a opcional (se ofrece si el cambio superó la estimación) y se conserva obligatoria en el flujo completo.
- **Decidido por el usuario el 2026-11-10**: sí: la retro es opcional en la vía rápida (se ofrece si el cambio superó la estimación) y sigue obligatoria en el flujo completo.
- **Changelog**: La vía rápida cierra sin entrevista de retro.
- **Estado**: borrador
- **Tiempo humano**: est. 2h · real —
- **Tiempo IA (ejec.)**: est. 0.5h · real —
- **Dependencias**: T-16
- **Archivos**: `agent-kits/shared/retro-gate.py`, `agent-kits/shared/test_retro_gate.py`, `commands/dev-cycle.md`, `agent-kits/dev-cycle/references/phase6-close.md`, `commands/retro.md`, `skills/quick-implement/SKILL.md`, `docs/{,en/}FLOWS.md`, `docs/{,en/}CONVENTIONS.md`, `interop/**` (regenerado)
- **Runtimes**: `retro-gate.py` es Python común; el cuerpo del comando se exporta a Codex y OpenCode y se regenera; sin diferencia por runtime.
- **Verificación**:
  - `pytest -q agent-kits/shared/test_retro_gate.py -k via_rapida` → `passed` (rojo antes: la vía rápida sin retro da exit ≠ 0)
  - `pytest -q tests/test_dev_cycle_split.py` → verde
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**
- [ ] Vía rápida: sin retro el gate sale 0 con aviso; flujo completo: sin retro sigue bloqueando.
- [ ] La excepción queda en el ledger (`- **Retro**: exenta (vía rápida)`).

### T-35 — Fusionar skills y plegar /roadmap-metrics (3.4, 3.7)

- **Descripción**: `llm-pipeline` y `data-collection` pasan a referencias de `backend-practices`, `confluence-pull` a modo de `confluence-publish` y `/roadmap-metrics` a `/roadmap-status --metrics` (16 → 15 comandos). Coherencia con T-03: T-03 retira solo el COMANDO `/confluence-pull` y añade la regla del linter contra colisiones; aquí desaparece también la SKILL y `confluence-publish` hereda sus disparadores. No se unen: T-03 va en la fase 1 y T-35 depende de ella.
- **Decidido por el usuario el 2026-11-10**: sí a las tres: `llm-pipeline` y `data-collection` como referencias de `backend-practices`; `confluence-pull` como modo de `confluence-publish`; `/roadmap-metrics` dentro de `/roadmap-status --metrics`.
- **Changelog**: Menos skills y un comando menos: las guías viven como referencias y las métricas se piden con /roadmap-status --metrics.
- **Estado**: borrador
- **Tiempo humano**: est. 6h · real —
- **Tiempo IA (ejec.)**: est. 1.5h · real —
- **Dependencias**: T-03, T-05, T-16
- **Archivos**: `skills/llm-pipeline/**`, `skills/data-collection/**`, `skills/backend-practices/SKILL.md`, `skills/backend-practices/references/`, `skills/confluence-pull/**`, `skills/confluence-publish/SKILL.md`, `agent-kits/shared/modules.json`, `evals/cases/skill-llm-pipeline.json`, `evals/cases/skill-data-collection.json`, `evals/cases/skill-confluence-pull.json`, `docs/README.md`, `CLAUDE.md`, `commands/roadmap-metrics.md` (borrar), `commands/roadmap-status.md`, `evals/cases/command-roadmap-metrics.json`, `docs/{,en/}FLOWS.md`, `interop/**` (regenerado)
- **Runtimes**: Codex: desaparecen `custom-agents-roadmap-metrics`, el adaptador de `confluence-pull` y las skills fusionadas; OpenCode: desaparecen `/roadmap-metrics`, `/confluence-pull` y las skills fusionadas por nombre; Claude: los mismos nombres. El contenido sobrevive en referencias y modos.
- **Verificación**:
  - `python scripts/lint_plugin.py --diet-check` → 0 párrafos perdidos · `python evals/check.py` → exit 0 · `pytest -q tests/test_skill_size.py tests/test_lint_plugin.py tests/test_export_interop.py` → verde
  - `python skills/roadmap-dashboard/scripts/build_dashboard.py --root docs/roadmap --metrics-md <tmp>` (modo `--metrics`) → mismo informe que el comando retirado
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**
- [ ] Ningún criterio de las skills fusionadas se pierde; cada `description` ≤ 1.024 caracteres; sin referencias vivas a lo retirado.
- [ ] Codex: desaparece `custom-agents-roadmap-metrics` y se redirige a `roadmap-status`; OpenCode: `/roadmap-metrics` desaparece y las skills fusionadas dejan de existir por nombre.

## Fase 6 — Higiene del roadmap

**Estado**: borrador · **Est.**: 10h humanas · **Real**: — · 500 € · 750k tokens

### T-36 — Cierres de iniciativas y estados rancios

- **Descripción**: Cerrar lo que quedó a medias: retro y estado de `session-visibility` y `knowledge-verification`; `kwipu-metadata` y la rama `fix/graphiti-add-memory-uuid` pasan a «cerrar o cancelar por retirada» (T-08); retro agrupada o exención escrita para 7 iniciativas `completado` sin retro; estados rancios de 6 planes/specs. `dev-cycle-dataset` se cierra como «superada por evaluación» (T-32 si se ejecuta; si no, aquí). La retro de `plugin-audit-remediation` espera al merge del PR #32.
- **Changelog**: El roadmap refleja el estado real.
- **Estado**: borrador
- **Tiempo humano**: est. 4h · real —
- **Tiempo IA (ejec.)**: est. 1h · real —
- **Dependencias**: T-08
- **Archivos**: `docs/roadmap/2026-11-10-plugin-audit-2/improvement-plan.md` (estado `aprobado` al autorizar la ejecución, `57fb054`; el cierre lo pasa a su estado final), `docs/roadmap/2026-11-02-kwipu-metadata/tasks.md`, `docs/roadmap/2026-11-02-session-visibility/tasks.md`, `docs/roadmap/2026-11-03-knowledge-verification/tasks.md`, `docs/roadmap/2026-09-09-project-specialization/improvement-plan.md`, `docs/roadmap/2026-10-07-catalog-capabilities/improvement-plan.md`, `docs/roadmap/2026-10-31-control-center/improvement-plan.md`, `docs/roadmap/2026-09-09-brief-budget/spec.md`, `docs/roadmap/2026-11-05-audit-remediation/spec.md`, `docs/roadmap/2026-10-27-opencode-reader-fixes/`, `docs/roadmap/CALIBRATION.md`, `docs/roadmap/README.md`, `docs/roadmap/2026-09-16-dev-cycle-dataset/{spec,improvement-plan,tasks}.md` (solo si T-32 no la cierra)
- **Verificación**:
  - `retro-gate.py` por iniciativa → exit 0 en las cerradas, o exención escrita
  - `python agent-kits/shared/ledger-lint.py docs/roadmap/<iniciativa>/tasks.md` → exit 0 en cada una tocada · `python skills/roadmap-dashboard/scripts/build_dashboard.py --root docs/roadmap --json` → sin estados contradictorios

**Criterios de aceptación**
- [ ] Las tres iniciativas con PR mergeado quedan `completado` con retro y fila.
- [ ] Las 7 restantes tienen una retro agrupada o una exención firmada por el usuario.
- [ ] Cada estado rancio se actualiza o queda con una nota fechada de por qué sigue abierto.

### T-37 — Candidatos de memoria sin curar

- **Descripción**: Hay 6 candidatos en `docs/knowledge/candidates/pending/`: `knowledge-curator` (único que aprueba o rechaza, `curator-gate.py`) los resuelve, revisa la memoria aprobada que cita Kwipu o Graphiti (PAT-001, LES-018 y otras) y propone el ADR que sustituye a ADR-020 y ADR-021.
- **Changelog**: Memoria pendiente resuelta.
- **Estado**: borrador
- **Tiempo humano**: est. 3h · real —
- **Tiempo IA (ejec.)**: est. 0.7h · real —
- **Dependencias**: T-08, T-09, T-10
- **Archivos**: `docs/knowledge/candidates/pending/*`, `docs/knowledge/approved/**`, `docs/knowledge/README.md`
- **Verificación**:
  - `ls docs/knowledge/candidates/pending | wc -l` → 0 (o solo los marcados «pide cambios» con motivo)
  - `python agent-kits/knowledge-curator/curator-gate.py` (ver `--help`) por candidato → exit 0 en los aprobados

**Criterios de aceptación**
- [ ] Cada candidato tiene decisión escrita.
- [ ] El índice `docs/knowledge/README.md` incluye los aprobados.

### T-39 — Captura de SessionEnd que no se pierde sin aviso ante un atasco de E/S (hallazgo de la revisión 8, gap 15)

- **Descripción**: La E/S acotada del journal tiene un plazo fijo de 5 s (`journal-io.py`). Si el disco se atasca más en SessionEnd, `journal_io_deadline` sube como `OSError` y `capture_end` lo traga: la sesión pierde su entrada con solo un aviso en stderr. Decidir con el usuario: reintentar, dejarla en la cola con aviso en el SessionStart siguiente, o subir el plazo (en fix8 el plazo de producción NO cambió).
- **Changelog**: Una sesión cuyo cierre coincide con un disco atascado ya no pierde su entrada del journal sin avisar.
- **Estado**: borrador
- **Tiempo humano**: est. 3h · real —
- **Tiempo IA (ejec.)**: est. 0.8h · real —
- **Archivos**: `agent-kits/shared/journal-capture.py`, `agent-kits/shared/journal-io.py`, `agent-kits/shared/test_journal.py`, `docs/FLOWS.md`, `docs/en/FLOWS.md`
- **Verificación**:
  - `pytest -q agent-kits/shared/test_journal.py -k atasco` → `passed` (rojo antes: un fsync que pasa de 5 s pierde la captura sin que `SessionStart` lo diga)
  - `python agent-kits/shared/ledger-lint.py docs/roadmap/2026-11-10-plugin-audit-2/tasks.md` → exit 0

**Criterios de aceptación**
- [ ] Un atasco de E/S de más de 5 s en SessionEnd no pierde la captura: queda en la cola o se reintenta.
- [ ] Si no se puede capturar, el siguiente SessionStart lo dice en la línea del journal.
- [ ] El plazo de producción solo cambia con una decisión escrita del usuario.

## Historial archivado

- 2026-11-17 · «Revisión de dos lentes — intento 1: Fase 1 (T-23, T-02..T-07) — 1 Critical, 6 Important, 11 Minor» → [execution-history.md](execution-history.md) · SHA-256 `96dd10df525bcf05591f40a2f518295f00dbb8645e91754ea554b1d6f810fd06`
- 2026-11-17 · «Revisión de dos lentes — intento 2: Fase 1 (T-23, T-02..T-07) — 0 Critical, 1 Important, 8 Minor» → [execution-history.md](execution-history.md) · SHA-256 `cf365ab9d3d1177b9af4ae54d0517d9a0318ba6d8656e9cfa83a5dc842d87359`
- 2026-11-17 · «Revisión de dos lentes — intento 3: Fase 1 (T-23, T-02..T-07) — 0 Critical, 2 Important, 8 Minor» → [execution-history.md](execution-history.md) · SHA-256 `185195397ddac43e49b324bfc026d929f455e1be4d46278be66738f54b310722`
- 2026-11-17 · «Revisión de dos lentes — intento 5: Fase 1 (T-06, T-07, T-23, T-38) — verificación dirigida del fix4: 5 Important, 5 Minor» → [execution-history.md](execution-history.md) · SHA-256 `bf382d611ac3a20f4c0b7b352a7a97239828c3cd18fa302349dff767b18d2f3b`
- 2026-11-14 · «Revisión de dos lentes — intento 4: Fase 1 (T-06, T-07, T-23) — verificación dirigida del ciclo final: 2 Important, 4 Minor» → [execution-history.md](execution-history.md) · SHA-256 `13284352f35a7954f4c505a3072e865f7f2a99a402bb511f6d8b4f5f42c576be`
- 2026-11-14 · «Revisión de dos lentes — intento 7: Fase 1 (T-06, T-07, T-23) — verificación dirigida del fix6: 4 Important, 15 Minor» → [execution-history.md](execution-history.md) · SHA-256 `d43914a5378d3f10b2d552fc27ff99621f17d1cddcabee8b5ee140a02c3d442f`
- 2026-11-14 · «Revisión de dos lentes — intento 8: Fase 1 (T-06, T-07, T-23) — verificación dirigida del fix7: 3 Important, 12 Minor» → [execution-history.md](execution-history.md) · SHA-256 `8f99caa7cbfcd4b2ea9c4de898ddab83ea09a2499e2d7a7fb05aa5fcb6a953b2`
- 2026-11-14 · «Revisión de dos lentes — intento 9: Fase 1 (T-06, T-07, T-23) — verificación dirigida del fix8: 2 Important, 6 Minor» → [execution-history.md](execution-history.md) · SHA-256 `1b1b64ce4682195575ef02b8c5d3959a52d6ef75f1414f85145000fd4b88c9d7`
- 2026-11-15 · «Revisión de dos lentes — intento 6: Fase 1 (T-06, T-07, T-23) — verificación dirigida del fix5: 7 Important, 9 Minor; cambio de modelo decidido por el usuario» → [execution-history.md](execution-history.md) · SHA-256 `6715d672c9310ff6f6f2982c80fde254dfc9f379b7a5f14ad09e38735c8d7c5c`
- 2026-11-15 · «Revisión de dos lentes — intento 10: Fase 1 (T-06, T-07, T-23) — verificación dirigida del fix9: 2 Important, 7 Minor» → [execution-history.md](execution-history.md) · SHA-256 `84599c0fd709810da0c69dacc4dc44dd1ed2779cbd3b43a53b2af6925d439153`
- 2026-11-15 · «Revisión de dos lentes — intento 11: Fase 1 (T-06, T-07, T-23) — verificación dirigida del fix10: 4 Important, 8 Minor» → [execution-history.md](execution-history.md) · SHA-256 `86e07fb16541591b6bbbe0316308e2176077dd1cff1e5d0b1ed5eb68a0609cd7`
- 2026-11-15 · «Revisión de dos lentes — intento 12: Fase 1 (T-06, T-07, T-23) — verificación dirigida del fix11: 2 Important, 9 Minor» → [execution-history.md](execution-history.md) · SHA-256 `9aa8dd06084d4eb2fb5f1204c3a17a37843b5ad2eef8c59912e9722cdee215ec`
- 2026-11-15 · «Revisión de dos lentes — intento 13: Fase 1 (T-06, T-07, T-23) — verificación dirigida del fix12: 1 Important, 9 Minor» → [execution-history.md](execution-history.md) · SHA-256 `5bd917906bc1b12c42fc1bb76eb25d05b7ef856d35227a9c474ee2c2a1b469f5`
- 2026-11-15 · «Revisión de dos lentes — intento 14: Fase 1 (T-06, T-07, T-23) — verificación dirigida del fix13: 2 Important, 10 Minor» → [execution-history.md](execution-history.md) · SHA-256 `8ee43f627c940b07874a61930729cf96fd1419454790d9d685ceb5a6e53c872b`
- 2026-11-16 · «Revisión de dos lentes — intento 15: Fase 1 (T-06, T-07, T-23) — verificación dirigida del fix14: 5 Important, 14 Minor» → [execution-history.md](execution-history.md) · SHA-256 `0905acd158a5004fb55fe20755648a0e31ede71994a020225cf3e526bd6579f1`
- 2026-11-16 · «Revisión de dos lentes — intento 16: Fase 1 (T-06, T-07, T-23) — verificación dirigida del fix15: 10 Important, 14 Minor» → [execution-history.md](execution-history.md) · SHA-256 `88b94bb2bf9e4044e2cffa9486dd4bc3fc18604405fe2e2b8e3cffb3d63e54ca`
- 2026-11-17 · «Revisión de dos lentes — intento 17: Fase 1 (T-06, T-07, T-23) — verificación dirigida del fix16: 5 Important, 17 Minor» → [execution-history.md](execution-history.md) · SHA-256 `fd42ff4435f07c003cf95b616aeb399d07fb7c498c48bffa59f766b7e8428f1f`


## Revisión de dos lentes — intento 18: Fase 1 (T-06, T-07, T-23) — verificación dirigida del fix17: 4 Important, 13 Minor

Lentes: A+B+C+D sobre `e371259..ae56211` (fix17 y los dos arreglos de test del orquestador tras la suite completa), dos a dos por memoria. Antes de lanzarlas, la suite completa en verde dos veces: Windows (node 579/0, pytest 15.261/0, serie 58/0) y réplica Linux (todos los pasos exit 0). Informes en el scratchpad de la sesión (`lenteA18.md` a `lenteD18.md`, sondas en `la18/`, `lb18/`, `lc18/`, `ld18/`).

**Cerrado del intento 17:**
- Gaps 1, 11, 12, 14, 15 y 16: git que lanza git (`submodule foreach`, `rebase -x`, `bisect run`, alias), `-B`, `update-ref refs/heads/*`, `rebase`/`bisect` con refs, tags, `FETCH_HEAD`, `fork/main` y SHA corto → deny; `checkout HEAD` → allow.
- Gap 17 en lo plausible: `rama_barata` exige un repositorio válido (queda el Minor 8).
- Gaps 3 y 5 con la raíz viva: `taskkill` ya filtra por fecha de creación; la víctima anterior sobrevive en producción (Lente C, 2 pasadas).
- Gaps 6, 13, 21 y 22, y `queryPlan`: Codex, `/doctor` y OpenCode caben en sus topes por construcción (Lente D).
- TDD: el RED `eb8612b` solo trae tests; reejecutado da 445 failed / 92 passed (declarado 447/90). Archivado literal (SHA-256 coincide), horas cuadran, datos personales ausentes.
- Coste del guard: p50 240-280 ms, igual que `e371259`; lineal; la lista blanca lee `.git/HEAD` una vez y no lanza git.
- 89 órdenes normales del implementer: 0 deny.
- Test de statusline reescrito (`b40614d`): sigue probando el requisito.

**Decisiones del usuario (2026-11-17):**
- **LÍMITE conocido: cadenas de programas fuera de la tabla.** El sufijo desenvuelto no se re-ancla otra vez (`uv run env -S 'strace git reset --hard'`, `uv run xargs -a f strace git restore`, shells `ash`/`mksh`/`fish` como programa desconocido). Se aplica la regla de escalado del intento 17: la clase se declara límite, no se persigue forma a forma.
- **D2 se optimiza en el producto**, no se declara límite: 8 hooks de herramienta en ráfaga sobre el anillo lleno deben caber en la espera real de 1 s con carga.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | **Regresión de fix17: rama con nombre de ruta.** Con un directorio `main` (o `master`, `origin/main`) en el cwd, `git checkout main` y `git checkout main --` → allow y git real cambia a `main`; el `--` final se quita antes de analizar y una ref delante de `--` se toma por ruta. Además se mira el cwd del proceso del guard, no el `cwd` del payload. En `e371259` se denegaban | T-06 | corregido en fix18 | A1, B3; `guardrail-check.py:2293-2298`, `:2322` |
| 2 | Important | `git submodule update [--init --recursive] --force` y `git submodule deinit -f` → allow; con git real borran los cambios sin comitear del submódulo | T-06 | corregido en fix18 | B1; `:2398`, `:2175` |
| 3 | Important | **Árbol de procesos de Windows: el barrido de respaldo no actúa en producción.** El PowerShell no `detached` muere con el worker (job de libuv) y ningún llamador pasa `until`; la raíz muerta deja un descendiente huérfano (reproducido, igual que `e371259`). Con la raíz viva, la espera de hasta 1,5 s a ese barrido no aporta (2,39 s frente a 0,65 s de `taskkill` solo). La identidad de la raíz no se comprueba cuando se da por viva (pid reutilizado → ajeno muerto en 4,7 s), y el barrido comprueba la identidad al fotografiar, no al matar. El ledger afirma «confirma hasta 15 s» y que `until` cubre la raíz muerta, cosa que solo ocurre en los tests | T-23 | corregido en fix18 | A3, B5, B6, C4, D18-3; `codex-plugin-state.mjs:29,36,41,46,58,67,79` |
| 4 | Important | **D2: la ráfaga pierde eventos con la espera real.** 2 de 48 con solo la carga ajena, 6 de 32 con 4 bucles; retención p50/p90/máx 122/340/501 ms. Causa medida: abrir para leer un fichero recién reemplazado cuesta 25-55 ms (escaneo síncrono, igual con 1 KB que con 200 KB) y cada escritor lee lo que publicó el anterior; la CPU solo suma 12-15 ms. Validar solo lo nuevo o recortar incrementalmente no lo cierra (8 de 32 perdidos). El test `d2` escalado (`b40614d`) ya no ve la pérdida | T-23 | corregido en fix18 | D18-1, A7, B7; prototipo de cola en `ld18/` (0 de 32, 0,45 s) |
| 5 | Important | Clase de envoltorios encadenados (ver decisión) | T-06 | **límite conocido** (usuario; declarado en `implementer.md` y en fix18) | A2, B2; `:2610-2617` |
| 6 | Minor | Salidas de rama o movimientos de `refs/heads/*` sin cubrir: `rebase -S main other` (el `-S` se come `main`), `bisect good|bad <ref>` tras `start` a secas (el camino que recomienda el propio mensaje de deny), `fetch +x:main` y `fetch . x:main`, `push . HEAD:main`, `push <remoto> HEAD:<rama>`, `worktree add -B main`, `-C <worktree de main> merge`, `filter-branch`, `filter-repo` | T-06 | corregido en fix18 | B4, C2; `:2287`, `:2334`, `:2368` |
| 7 | Minor | Opciones de git que ejecutan una cadena de shell sin cubrir: `difftool -x`/`--extcmd`, `grep -O`/`--open-files-in-pager`, `archive --exec`/`--remote`, `fetch-pack`/`send-pack --upload-pack`/`--receive-pack` | T-06 | corregido en fix18 | C1; `:2168-2175` |
| 8 | Minor | `_es_repositorio` acepta cualquier `commondir` sin mirar adónde apunta: `.git` con `HEAD` de otra rama y `commondir` inválido → git sube al padre y el guard cree estar en la rama de trabajo | T-06 | corregido en fix18 | C3; `:297-303` |
| 9 | Minor | `git gc --prune=now` y `git reflog expire --expire=now --all` → allow; destruyen la recuperación que el guard protege al denegar `branch -D` y `stash drop` | T-06 | corregido en fix18 (decisión del orquestador: deny, ante la duda) | C (fuera de lente) |
| 10 | Minor | Cambios en los tests tras el RED sin trazar (un legítimo retirado, dos formas del corpus, umbral 0,7 → 0,6) | T-06 | corregido en fix18 | A4 |
| 11 | Minor | `Archivos` de T-23 (`tasks.md:681`) sigue con «2 s» y «`TIMEOUT_CAZA` 15 s» | T-23 | corregido en fix18 | A5 |
| 12 | Minor | `docs/agents/implementer.md:70` mantiene la regla `-B` de fix16 junto a la de fix17, que la contradice | T-06 | corregido en fix18 | A6 |
| 13 | Minor | Gap 10 del intento 17: nada comprueba que `uninstall` ejecute `marketplace remove` | T-23 | rebatido con evidencia en fix18 (`uninstall` no ejecuta `marketplace remove`: el registro `daycry` es compartido; ver T-23 fix18) | A8 |
| 14 | Minor | Punto 5: la ruta de `/doctor` solo se midió a mano con +1 s (el diseño pedía +2 s); desviación sin numerar | T-23 | corregido en fix18 | A9 |
| 15 | Minor | `runBounded` añade un arranque de node a cada llamada del instalador a una CLI (1.071 ms frente a 75 ms) | T-23 | corregido en fix18 | D18-2 |
| 16 | Minor | Escáner de la statusline cuadrático en número de tokens por debajo del tope de 8 KB (96/271/1.594 ms con 2/4/8 KB; entrada real 30-40 ms) | T-23 | corregido en fix18 | D18-4, B |
| 17 | Minor | Restos temporales de la Lente A fuera de su carpeta (`$TEMP/sc-err.txt`, `/tmp/la18-td.txt`) | — | lo limpia el orquestador | A |

**Diseño fijado por el orquestador para fix18:**
1. **Rama por lista blanca, sin ambigüedad de ruta** (gaps 1 y 6). `checkout`/`switch` con una posicional sin `--` delante: si el nombre resuelve como ref (rama local, remota o tag; lectura barata de `.git/refs` + `packed-refs`, sin lanzar git) y no es la rama actual → deny aunque exista una ruta con ese nombre; ruta solo si no es ref, o si va tras `--`. Una ref delante de `--` es ref. Las rutas se resuelven contra el `cwd` del payload. Movimientos de `refs/heads/*` como clase: cualquier refspec con destino `refs/heads/<x>` o `<x>` en `fetch`/`push` hacia el repo local (`.`) o con `+`, `push <remoto> <src>:<rama>` con `--force`/`+` (sin forzar sigue como hoy), `worktree add -b/-B`, `-C <dir>` que cambia de repo/worktree se analiza con el HEAD de ese dir, `filter-branch`/`filter-repo` → deny. `rebase` con opciones que toman valor (`-S`, `-s`, `-X`, `--onto`, `-x`) se parsea con su aridad real. `bisect` cualquier subcomando salvo `log`/`visualize`/`view` → deny; el mensaje de deny deja de recomendar `bisect start` a secas.
2. **Subcomandos y opciones que destruyen o ejecutan shell, como clase** (gaps 2, 7 y 9). Tabla única de opciones de git cuyo valor es una orden (`-x`/`--extcmd`, `-O`/`--open-files-in-pager`, `--exec`, `--upload-pack`, `--receive-pack`, `-c core.*`/`alias.*` ya cubiertos) → deny. `submodule update --force`/`-f`, `submodule deinit -f`/`--force`, `gc --prune=now|all`, `prune`, `reflog expire|delete`, `worktree remove --force` → deny.
3. **`commondir` validado** (gap 8): debe apuntar a un directorio con `objects/` y `refs/`; si no, `rama_barata` recurre a `current_branch`.
4. **Árbol de procesos de Windows que actúa de verdad** (gap 3). El barrido de respaldo se lanza `detached` con una forma que sí ejecuta (p. ej. `powershell -NonInteractive -WindowStyle Hidden` con `windowsHide`, no `DETACHED_PROCESS` puro; mide que corre) o se hace en el propio worker antes de salir, y lo pasan todos los llamadores con `since`/`until`. Con la raíz viva se confía en `taskkill /T` (que ya filtra por fecha) y no se espera al barrido. Identidad de la raíz comprobada (pid + fecha de creación) antes de darla por viva; el barrido comprueba la identidad justo antes de cada `Stop-Process` (en la misma orden de PowerShell). Test con la raíz muerta y un descendiente vivo: 0 huérfanos en producción, no solo en el test. La traza del ledger se corrige a lo que de verdad hace.
5. **D2 por cola de añadidos** (gap 4, decisión del usuario). `record` escribe el evento en `events.tail` con `O_APPEND` + `fsync` bajo el cerrojo (sin releer el anillo), con comprobación de identidad del fichero en `StateIO`; el pliegue al anillo `events.json` lo hace el escritor que encuentra K ≥ 16 añadidos (o el ciclo de vida), a prueba de caídas (el anillo publicado por CAS antes de truncar la cola; una cola con líneas ya plegadas se reconoce por revisión y no se duplica). Todos los lectores (snapshot, panel, `history`, `count_oversize`) ven anillo + cola. Se conservan el CAS por firma, el fallo cerrado, `recortado`, el límite de tamaño y el contrato de `nowait` (Codex MCP: un intento). Test `d2` con la espera REAL de 1 s (sin escalar) y carga ajena declarada: 8 de 8, y una sonda de 16 que se anota. El test de la escala deja de tocar `TOOL_LOCK_WAIT` en los hijos.
6. **Coste** (gaps 15 y 16). `runBounded` del instalador: un solo worker por instalación o sondas `--version` fuera del worker. Statusline: escáner lineal en número de tokens (o tope que deje fuera el caso cuadrático) con test por razón 2/4/8 KB, no de pared.
7. **Traza y docs** (gaps 5, 10-14). Declarar el LÍMITE de envoltorios encadenados en `docs/agents/implementer.md` y el ledger (con los ejemplos de A2/B2) y los nuevos deny; quitar la regla `-B` de fix16 de `implementer.md:70`; trazar los cambios de test tras el RED; corregir `Archivos` de T-23; numerar la desviación de `/doctor` o medir con +2 s; test de `uninstall` → `marketplace remove`. Docs y espejos EN si cambian los plazos.

Tras este ciclo: suite completa (Windows y réplica Linux) sin rojo, intento 19 dirigido (A+B, C+D) y medida emparejada de T-23 con el equipo libre.
