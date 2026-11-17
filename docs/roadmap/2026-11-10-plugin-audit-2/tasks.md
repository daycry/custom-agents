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
| Fase 2 — Retirada decidida (Kwipu, Graphiti, plugin-dev) | 0 | 4 | 0% | 0 / 32h | 0 / 7.9h | 0 / 1.98h | 0 / 2100k |
| Fase 3 — Tokens | 0 | 11 | 0% | 0 / 30h | 0 / 8.2h | 0 / 2.05h | 0 / 2260k |
| Fase 4 — Simplificación del código | 0 | 8 | 0.0% | 0 / 34.5h | 0 / 8.5h | 0 / 2.12h | 0 / 2470k |
| Fase 5 — Alcance y entrenamiento | 0 | 5 | 0% | 0 / 26h | 0 / 6.5h | 0 / 1.62h | 0 / 1800k |
| Fase 6 — Higiene del roadmap | 0 | 3 | 0% | 0 / 10h | 0 / 2.5h | 0 / 0.62h | 0 / 750k |
| **TOTAL** | **7** | **39** | **17.9%** | **0 / 148.5h** | **0 / 38.6h** | **0 / 9.65h** | **0 / 10470k** |

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
- **Tiempo IA (ejec.)**: est. 0.5h · real 63.17h (0.4h del cierre original estimado + 2.53h medidas en fix5 + 0.78h en fix6 + 1.33h en fix7 + 1.55h en fix8 + 3.22h en fix9 + 1.21h en fix10 + 0.43h en fix11 + 2.11h en fix12 + 0.95h en fix13 + 0.45h en fix14 + 1.07h en fix15 + 47.14h en fix16 `(medido)`; las ventanas de fix5 a fix15 están compartidas con T-07 y T-23; la cifra anterior, 11.42h, no sumaba las 2.11h de fix12)
- **Archivos**: `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/test_guardrail_check.py`, `agent-kits/shared/test_guardrail_differential.py` (fix5), `tests/test_native_guardrail_dispatch.py`, `docs/agents/implementer.md`, `docs/CONVENTIONS.md` · fix6: `agent-kits/shared/native-guardrail.py`, `hooks/run-hook.mjs`, `hooks/opencode-plugin.js`, `interop/opencode/plugins/custom-agents/index.js` (regenerado), `tests/test_native_guard_failclosed.py` (nuevo), `tests/hook-guard-failclosed.test.mjs` (nuevo), `docs/FLOWS.md`, `docs/en/FLOWS.md` · fix7: `agent-kits/shared/test_guardrail_fix7.py`, `agent-kits/shared/test_guardrail_differential7.py`, `tests/test_native_guard_failclosed7.py`, `tests/native-guard-adapter-failclosed.test.mjs` (nuevos), `docs/INTEROP.md`, `docs/en/INTEROP.md`, `interop/opencode/plugins/custom-agents/index.js` (regenerado), `agent-kits/shared/test_guardrail_differential.py` · fix8: `tests/test_native_guard_scan8.py` y `tests/native-guard-adapter-fix8.test.mjs` y `agent-kits/shared/test_guardrail_fix8.py` (nuevos), `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/native-guardrail.py`, `hooks/run-hook.mjs`, `hooks/opencode-plugin.js`, `interop/opencode/plugins/custom-agents/index.js` (regenerado), `agent-kits/shared/test_guardrail_differential.py`, `agent-kits/shared/test_guardrail_differential7.py`, `tests/test_native_guard_failclosed.py`, `tests/test_graphiti_security.py` (huella del lanzador), `docs/INTEROP.md`, `docs/en/INTEROP.md`, `docs/agents/implementer.md` · fix9: `agent-kits/shared/test_guardrail_fix9.py` y `tests/test_native_guard_parity9.py` y `tests/native-guard-adapter-fix9.test.mjs` (nuevos), `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/native-guardrail.py`, `hooks/opencode-plugin.js`, `interop/opencode/plugins/custom-agents/index.js` (regenerado), `agent-kits/shared/test_guardrail_differential7.py` (BAD9_PARIDAD y LEGIT9), `agent-kits/shared/test_guardrail_fix8.py` (`env -S 'echo "hola'` pasa a denegado), `docs/agents/implementer.md`, `docs/INTEROP.md`, `docs/en/INTEROP.md` · fix10: `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/native-guardrail.py`, `hooks/run-hook.mjs`, `hooks/opencode-plugin.js`, `interop/opencode/plugins/custom-agents/index.js` (regenerado), `agent-kits/shared/test_guardrail_differential7.py`, `agent-kits/shared/test_guardrail_fix10.py` (nuevo), `tests/test_native_guard_parity9.py`, `tests/opencode-realpath-fix10.test.mjs` (nuevo), `tests/native-guard-adapter-fix9.test.mjs`, `tests/test_graphiti_security.py` (huella), `docs/agents/implementer.md`, `docs/INTEROP.md`, `docs/en/INTEROP.md` · fix11: `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/test_guardrail_differential7.py`, `agent-kits/shared/test_guardrail_fix11.py` (nuevo), `hooks/opencode-plugin.js`, `interop/opencode/plugins/custom-agents/index.js` (regenerado), `tests/opencode-realpath-fix11.test.mjs` (nuevo), `docs/agents/implementer.md` · fix12: `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/test_guardrail_fix12.py` (nuevo), `agent-kits/shared/test_guardrail_fix11.py`, `agent-kits/shared/test_guardrail_differential.py`, `agent-kits/shared/test_guardrail_differential7.py`, `docs/agents/implementer.md` · fix13: `agent-kits/shared/test_guardrail_fix13.py` (nuevo), `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/test_guardrail_fix12.py`, `agent-kits/shared/test_guardrail_differential7.py`, `docs/agents/implementer.md`, `docs/roadmap/2026-11-10-plugin-audit-2/execution-history.md` · fix14: `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/test_guardrail_fix14.py` (nuevo), `agent-kits/shared/test_guardrail_fix14_corpus.py` (nuevo), `agent-kits/shared/test_guardrail_fix10.py`, `agent-kits/shared/test_guardrail_fix12.py`, `agent-kits/shared/test_guardrail_fix13.py`, `docs/agents/implementer.md` · fix14 y fix15 (declarados en fix15, gap 14): `agent-kits/shared/test_guardrail_fix14.py`, `agent-kits/shared/test_guardrail_fix14_corpus.py`, `agent-kits/shared/test_guardrail_fix15.py` y `agent-kits/shared/test_guardrail_fix15_corpus.py` (nuevos), `install/install.mjs` (fix14: `detached: true`; fix15: vigilante de señales; declarado también en T-23), `agent-kits/shared/journal-capture.py`, `agent-kits/shared/journal-io.py`, `agent-kits/shared/journal.py`, `hooks/opencode-plugin.js` (ver T-23) · fix16: `agent-kits/shared/test_guardrail_fix16.py` (nuevo), `agent-kits/shared/test_guardrail_fix16_corpus.py` (nuevo: BYPASS16, PROBES16, G1_PROBES16, LIMITE16), `agent-kits/shared/test_journal_fix16.py` (nuevo), `agent-kits/shared/test_guardrail_differential.py` y `agent-kits/shared/test_guardrail_differential7.py` (las formas que eran LIMITE y ahora se deniegan pasan a BAD6/BAD7), `agent-kits/shared/test_guardrail_fix15.py` (límites de rondas), `agent-kits/shared/native-guardrail.py` (rama barata), `docs/agents/implementer.md`, `agent-kits/shared/test_guardrail_fix17.py` y `agent-kits/shared/test_guardrail_fix17_corpus.py` (fix17: nuevos), `agent-kits/shared/test_guardrail_fix7.py`, `agent-kits/shared/test_guardrail_check.py` y `agent-kits/shared/test_guardrail_fix16.py` (fix17: las formas de «otra rama de trabajo» pasan a la lista de denegadas por la lista blanca; el arnés de fix16 acepta `locale`), `agent-kits/shared/test_guardrail_fix15.py` (fix17, gap 6: el arnés decide por el registro del shim)
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

**fix17 (intento 17, gaps 1, 2, 6, 11, 12 y 14 a 17 de T-06; el diseño del orquestador —puntos 1, 2, 3 y 6— se aplica tal cual salvo las interpretaciones j1 a j9; los puntos 4, 5 y 7 y las interpretaciones j10 a j17 están en T-23)** — `plugin-audit-2/T-06-fix17` y `T-23-fix17` (los dos marcadores se abrieron tras archivar fix16 y ANTES del RED; se cierran al terminar, tras la réplica Linux). Commits: archivo literal de fix16 `996bfae`; RED `eb8612b` (solo tests); GREEN T-06 `2d3cb88`; GREEN T-23 `4eaf573` y los que siguen en el log (`e1d0c31` arneses y `7a8dacd` rojos de la suite completa; ledger en el commit siguiente).

**RED (contra `e371259`).** `test_guardrail_fix17.py` **447 failed y 90 passed** (537; más el diferencial con bash real: **bash ejecuta git y el guardarraíl PERMITE en 177 de las 280 formas** del corpus de envoltorios, y las 3 formas que no se ejecutan —`zsh`, `ksh`, `busybox sh` no están en esta máquina— se declaran en el corpus sin exigir ejecución); `process-tree-fix17.test.mjs` **6 failed y 1 passed** (el control positivo); `hook-budget` **2 failed**. Los tests de `SessionEnd` (gap 21) y el de `uninstall` (gap 10, Linux) no pueden dar un rojo determinista: el primero mide un presupuesto de test, el segundo se ejecuta en la réplica Linux (ver T-23).

**Puntos 1 a 3 (guardarraíl).**
1. **Re-anclaje general** (gaps 1 y 2). El cuerpo del bucle de `_check_git` pasa a `_analiza_segmento(crudo, …, _reanclado)`: una orden simple se analiza entera (`_desenvuelve`, `env -S`, config, xargs, `bash -c`, git, `rm -rf`) y, si no es ya un sufijo, cada palabra de `_ANCLAS` (git, `eval`, `trap`, los 20 envoltorios de la tabla y las shells) abre un sufijo que se analiza como un segmento NUEVO y completo. Dentro de git, `_codigo_de_git` analiza como código lo que git pasa a una shell: `submodule foreach` (con o sin `--recursive`/`--quiet`, entrecomillado o no), `rebase -x|--exec` (clústeres `-ix`, `-x'…'`, `--exec=`, abreviaturas), `bisect run`, los filtros de `filter-branch`, `fetch|pull|clone|ls-remote --upload-pack` y `push --receive-pack|--exec`; los alias `!…` ya los deniega la lista blanca de configuración (`-c alias.*`, `config alias.*`). Más de 32 anclas en una orden → deny (el tope antiguo contaba solo `git`).
2. **Rama por lista blanca** (gaps 11, 12, 14, 15, 16). `_razon_cambio_rama`: con una posicional solo se permite la rama actual, `HEAD` (en `checkout`) y, en `checkout`, una ruta que existe; `-B|-C|--force-create` solo sobre la rama actual y sin punto de partida; `update-ref refs/heads/*` deny; `git rebase <upstream> <rama>` (2 posicionales o `--root <rama>`) deny; `git bisect start|reset <ref>` deny. `git checkout HEAD` a secas se permite y `implementer.md` se corrige.
3. **`rama_barata` válida** (gap 17): `_es_repositorio` exige `HEAD` + (`objects/` y `refs/`) o `commondir`; si no, recurre a `current_branch`.

**Interpretaciones (guardarraíl).**
- **j1** La lista blanca es estricta: cambiar a OTRA rama de trabajo existente (`git checkout feature/y`, `git switch feature/y`) pasa a deny —antes `fix7 gap 8` lo declaraba permitido—; sin leer las refs no se distingue de un tag o de una remota (gaps 11 y 14). Falso deny declarado (docs/agents/implementer.md); crear una rama con `-c`/`-b` sigue permitido. Cambian 12 formas de los tests antiguos (`test_guardrail_check.py`, `_fix7.py`, `_fix16.py`): salen de las listas de permitidas y entran en las de denegadas.
- **j2** `git checkout <ruta que no existe>` se deniega (git también falla, salvo que el fichero esté borrado: se usa `-- <ruta>`); la existencia se comprueba contra el directorio actual del hook.
- **j3** `-t`/`--track` sin nombre hacia `main`/`master` (`git switch -t origin/main`) crea la rama local `main` y cambia a ella: deny (no estaba en los gaps; misma clase que el 11).
- **j4** `-p`/`--patch`/`--ours`/`--theirs` operan con ficheros: solo exentan en `checkout` (en `switch` no existen). El diferencial aleatorio halló 31 regresiones por permitirlos también en `switch` (`git switch - time -p`); corregido y añadido al corpus.
- **j5** `update-ref refs/heads/*` se deniega con cualquier rama actual (también en `main`): mueve una rama sin pasar por `branch`.
- **j6** El diseño decía «sin heredar el estado de la orden exterior»: el sufijo se analiza como segmento nuevo (sus propias asignaciones, `-S`, `-C`, `xargs`) y ADEMÁS hereda las asignaciones, `via_xargs` y el cambio de base de fuera (un superconjunto: solo analiza más; `X=1 strace git push` pasa `X` al hijo de verdad).
- **j7** `_codigo_de_git` incluye `filter-branch`, `--upload-pack` y `--receive-pack` (no estaban en el diseño; ejecutan código de shell igual que `rebase -x`).
- **j8** `git bisect good|bad|new|old|skip` no se deniegan (no sueltan HEAD sin un `start` previo, que sí se deniega con refs); límite declarado.
- **j9** `git submodule foreach` y `git rebase -x` con una forma destructiva dentro se deniegan; `git submodule foreach 'git status'`, `--recursive git pull`, `rebase -x 'make test'` y `bisect run make test` siguen permitidos (26 formas legítimas en `LEGITIMAS17`).

**Deny nuevos declarados.** Falsos deny nuevos: cambiar a otra rama de trabajo existente; `git checkout <ruta inexistente>`; `git submodule foreach 'git checkout …'`; todo lo que `git rebase -x`/`bisect run` ejecute con una forma destructiva; `echo`/`printf` con un envoltorio o shell sin comillas seguido de git destructivo (el coste declarado de fix16, ahora también con `env`, `time`, `sh`…). Deny intencionados nuevos: las 117 formas de git-que-lanza-git, las 280 de envoltorio-tras-programa-desconocido, las 54 de rama y las 9 de `rebase`/`bisect`/`update-ref`.

**Gap 6 (arneses de fix15).** `test_guardrail_fix15.py` decide «bash ejecuta git» por el REGISTRO del shim (reutiliza `_ejecutar16`, con `locale`), no por stdout; la prueba de paridad exige además que NINGUNA forma de `SIN_PARIDAD15` ejecute git (un motivo falso rompe el test); los motivos de `<( )` y `coproc` se retiran o corrigen según el registro: coproc y `<( )` SÍ ejecutan git (el motivo del dash de `sh -c` se mantiene solo donde `sh` no es bash).

**Verificaciones de fix17 (T-06 y T-23).** Diferencial contra `cb59eef` (`dif_fix17.py`): corpus de 2.690 órdenes **0 deny nuevos / 0 regresiones**; 7.056 `case` **0 / 0**; aleatorio de 60.000: **5 regresiones** (todas `git checkout <ref> … -p`, que es modo parche con ficheros, j4) y **2.854 deny nuevos** (2.430 de la lista blanca de rama, 283 de opción de envoltorio desconocida con intérprete detrás, el resto reglas ya existentes que ahora se alcanzan tras un programa desconocido); la primera pasada dio 31 regresiones (`git switch - … -p`) y halló el error de j4. 75 órdenes normales de un implementer (status, diff, commit, stash, rebase, submodule update, bisect sin refs, `uv run pytest`…): 0 denegadas. Windows (carga ajena del 95 %): guardarraíl + diferenciales con bash real (`test_guardrail_*`, 18 ficheros): **4.457 passed, 5 skipped, 0 failed** (48 min); resto de `agent-kits` y skills: 4.860 passed y 6 failed por carga (4 pasan solos, el de TLS tenía un margen de 80 ms y se corrigió, j17); `tests/`: 5.931 passed y 7 failed (la huella del lanzador —real, actualizada—, `test_console_transport` —EOF en Windows, corregido—, `test_mermaid_blocks` —no terminaba—, tres de carga que pasan solos). Suite node de Windows completa **579 tests, 570 pass, 0 fail, 8 skipped**. `gap 8` del instalador con 12 bucles de CPU (`carga13.py 12`): **5 de 5 pasadas verdes** (55,9, 74,6, 83,7, 74,7 y 60,5 s; cota de 30 s intacta). Consulta con worker lento (+1 s) por la ruta de `/doctor` (node con timeout de 10 s, codex colgado con descendiente): cb59eef **2 huérfanos**, fix17 **0** (con la máquina saturada el ayudante de `/doctor` agota sus 10 s —node arranca en 1-2 s—: da `unknown`, sin huérfanos). Test de PID reutilizado (víctima anterior al lanzamiento, padre muerto): sobrevive, y su control positivo muere. Réplica Linux: PENDIENTE_REPLICA.

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

**Estado**: borrador · **Est.**: 32h humanas · **Real**: — · 1600 € · 2100k tokens · Decidida por el usuario el 2026-11-10.

### T-08 — Retirar Kwipu y Graphiti: código, tests y configuración (decidido)

- **Descripción**: Primera mitad de la retirada decidida (la segunda, T-09, es documentación). Antes de borrar se anota en `testing/retirada.md` el commit recuperable (`git rev-parse HEAD`; hoy `129dbeb`, y la release 3.2.3). Se borran 39 ficheros de `skills/knowledge-services/` (18.287 líneas medidas: código 7.351, test 8.494, fixtures 1.963, docs 479) y `tests/test_graphiti_model.py` (418). Se edita el resto: `capabilities.py` pierde `_kwipu_*` y `_graphiti_*` (`:243-470`), `knowledge-schema.py` su validación de backends, y las claves `routing.kwipu|graphiti` salen de plantilla, schema y taxonomía por defecto. TRAMPA: `tests/test_graphiti_security.py` (2.953 líneas) NO se borra entero: guarda el escáner «ningún hook hace red» que cargan `test_hook_launcher_security.py` y `hook-budget.test.mjs`; se renombra `tests/test_hook_network_egress.py` y solo se borran sus ≈718 líneas Graphiti-específicas (clasificación por nombre de test; se revisa al ejecutar). El cliente MCP de `graphiti.py` no se extrae: sin consumidor, se recupera del commit anotado.
- **Changelog**: Cambio rompedor, versión mayor: se retiran los backends Kwipu y Graphiti; la memoria local de docs/knowledge sigue igual.
- **Estado**: borrador
- **Tiempo humano**: est. 14h · real —
- **Tiempo IA (ejec.)**: est. 3.5h · real —
- **Archivos**: **Se borran (35):** `skills/knowledge-services/backends/{graphiti,graphiti_model,graphiti_provenance,graphiti_providers,graphiti_publication,graphiti_rebuild,graphiti_scope,markdown_export}.py`, `skills/knowledge-services/scripts/{_mcp_fake,kwipu-project-add}.py`, `skills/knowledge-services/scripts/test_{backend_graphiti,backend_markdown_export,backend_markdown_read,backend_markdown_http,graphiti_*,kwipu_metadata,kwipu_project_add}.py`, `skills/knowledge-services/scripts/fixtures/graphiti/`, `skills/knowledge-services/scripts/fixtures/kwipu-*.json`, `tests/test_graphiti_model.py`. **Se divide:** `tests/test_graphiti_security.py` → `tests/test_hook_network_egress.py` (nuevo nombre). **Se editan (código y config):** `agent-kits/shared/{capabilities,knowledge-schema,knowledge-taxonomy-local}.py` (solo claves y funciones de backend; `outbox.py` solo cambia un comentario de cabecera), `agent-kits/shared/copias.json`, `agent-kits/shared/templates/taxonomy.json`, `agent-kits/shared/schemas/taxonomy.schema.json`, `skills/knowledge-services/scripts/knowledge-sync.py` (2 menciones), `skills/plugin-panel/scripts/panel_data.py`, `skills/plugin-panel/assets/{console-context,page-memoria}.js`. **Se editan (tests, 30):** `agent-kits/shared/test_{capabilities,doctor,knowledge_schema,knowledge_routing,knowledge_derivative_surface}.py`, `skills/knowledge-services/scripts/test_{knowledge_sync,backends_init,backend_verification}.py`, `skills/knowledge-category-template/scripts/test_category_template.py`, `tests/{memoria_fixture,test_audit_journal,test_audit_knowledge,test_console_encoding,test_control_center_http,test_knowledge_approved_retrieval,test_knowledge_candidates,test_knowledge_find,test_knowledge_prompt_split,test_knowledge_router,test_knowledge_router_read,test_knowledge_services,test_panel_data,test_panel_fix4,test_panel_memoria_fix1,test_private_state_dirs,test_training_data_services,test_hook_launcher_security}.py`, `tests/test_panel_memoria_ui.py`, `tests/hook-budget.test.mjs` (comentario), `interop/**` (regenerado). **No se toca:** `skills/training-data-services/**` (congelada; su clave `bridge_to_kwipu` la retira T-32 si se aprueba), `.claude/knowledge-services/taxonomy.json` (local del usuario, ver «acciones»).
- **Runtimes**: Sin diferencia por runtime en lo que se borra (Python común). En `interop/` desaparecen las menciones del agente `knowledge-curator` en Codex y OpenCode; el instalador y los manifiestos no citan los backends (0 menciones en `install/`).
- **Verificación**:
  - `git grep -il -E "graphiti|kwipu" -- agent-kits skills tests install hooks scripts evals` → solo `skills/training-data-services/**` y las menciones declaradas en `testing/retirada.md` (rojo antes: ≈75 ficheros)
  - `pytest -q tests/test_hook_network_egress.py tests/test_hook_launcher_security.py tests/test_copias_declaradas.py tests/test_knowledge_router.py tests/test_knowledge_find.py tests/test_panel_data.py tests/test_panel_memoria_fix1.py agent-kits/shared skills/knowledge-services/scripts` → verde (rojo antes: un test nuevo de `test_capabilities.py` exige que el registro ya no declare `kwipu` ni `graphiti` y que `knowledge-sync.py --backend kwipu` falle con «retirado»)
  - `node --test tests/hook-budget.test.mjs` → verde; `python -m pytest --collect-only -q tests/test_hook_network_egress.py` → el número de tests es el de antes menos los Graphiti-específicos listados en `testing/retirada.md`
  - `wc -l` antes y después, anotado en `testing/retirada.md`
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**
- [ ] No queda código ni test de Kwipu o Graphiti fuera de `skills/training-data-services/`; `knowledge-sync.py --backend kwipu|graphiti` y una taxonomía que los declare fallan con un mensaje claro («retirado en la versión X; ver CHANGELOG»).
- [ ] La suite «ningún hook hace red» sigue íntegra con su nuevo nombre (mismos tests menos los Graphiti-específicos, listados en `testing/retirada.md`) y `test_hook_launcher_security.py` y `hook-budget.test.mjs` apuntan al fichero nuevo.
- [ ] `capabilities.py` sin `_kwipu_*` ni `_graphiti_*`; `/doctor` y el panel de memoria funcionan sin backends; `copias.json` y `test_copias_declaradas.py` coherentes.
- [ ] Los tests de router (`test_knowledge_router*.py`) siguen en verde con un adaptador de prueba hasta que T-10 retire el marco.

### T-09 — Retirar Kwipu y Graphiti: documentación, ejemplos y evals (decidido)

- **Descripción**: Segunda mitad de la retirada. De los 137 ficheros con menciones: 37 se borran, 1 se divide (T-08), 96 se editan, 2 son PDF generados y 1 es config local del usuario (cifras y criterio en el plan). Aquí se borran las guías de Graphiti (ES y EN) y `kwipu-adapter.md`; se editan 38 docs y READMEs, ejemplos, `knowledge-curator`, `/setup`, `/doctor`, `phase4-knowledge-gate.md`, 3 `SKILL.md` y 3 casos de evals; los CHANGELOG declaran el cambio rompedor. ADR-020, ADR-021 y una nota en ADR-018 se proponen con `knowledge-curation.py propose`.
- **Changelog**: Se retira la documentación, los ejemplos y los pasos de /setup y /doctor de Kwipu y Graphiti.
- **Estado**: borrador
- **Tiempo humano**: est. 7h · real —
- **Tiempo IA (ejec.)**: est. 1.7h · real —
- **Dependencias**: T-08
- **Archivos**: **Se borran:** `docs/{,en/}knowledge-services-graphiti.md`, `skills/knowledge-services/references/kwipu-adapter.md`. **Docs ES y EN (38):** `README.md`, `README.es.md`, `CLAUDE.md`, `docs/{CODE_CONTEXT,CONVENTIONS,CUSTOMIZATION,FLOWS,INTEROP,MEMORY-PORTABILITY,PLUGIN-PANEL,README}.md`, `docs/en/{CODE_CONTEXT,CONVENTIONS,CUSTOMIZATION,FLOWS,INTEROP,MEMORY-PORTABILITY,PLUGIN-PANEL,README}.md`, `docs/agents/{CONTRACTS,ROLES,knowledge-curator}.md`, `docs/guides/{audit-remediation,dashboard,knowledge-categories,memory,quality-playbook,subscription-efficiency}.md`, `docs/en/guides/{audit-remediation,dashboard,knowledge-categories,memory,product}.md`, `docs/reference/product.md`, `docs/en/reference/{doctor,product}.md`. **Ejemplos y config versionada:** `docs/examples/integrations/memory.json`, `docs/examples/memory/taxonomy.json`, `.gitignore` (línea `kwipu-export/`; `*-export/` se queda). **Piezas:** `agents/knowledge-curator.md`, `commands/{setup,doctor}.md`, `agent-kits/dev-cycle/references/phase4-knowledge-gate.md`, `agent-kits/shared/{README,doctor-reference}.md`, `skills/knowledge-services/{SKILL.md,backends/README.md,references/project-integration.md}`, `skills/{knowledge-category-template,plugin-panel,training-data-services}/SKILL.md` (solo prosa), `evals/cases/{command-setup,skill-knowledge-category-template,skill-knowledge-services}.json`, `CHANGELOG.md`, `CHANGELOG.es.md`, `interop/**` (regenerado). **No se editan:** `output/pdf/custom-agents-manual-operativo.pdf` y `output/pdf/guia-resultados-calidad-custom-agents.pdf` (binarios generados; se regeneran, ver «acciones»).
- **Runtimes**: Los textos de `/setup` y `/doctor` se exportan a Codex (`command-skills/custom-agents-setup`, `custom-agents-doctor`) y a OpenCode (`commands/`): se regeneran sin los pasos; sin diferencia de conducta.
- **Verificación**:
  - `git grep -il -E "graphiti|kwipu" -- . ':!docs/roadmap' ':!docs/knowledge' ':!CHANGELOG*' ':!output' ':!interop' ':!.claude' ':!skills/training-data-services'` → vacío (rojo antes: ≈95 ficheros)
  - `python evals/check.py` → exit 0 (sin enlaces ni rutas citadas inexistentes)
  - `grep -n -i "cambio rompedor\|breaking" CHANGELOG.md CHANGELOG.es.md` → ambas lo declaran, con la versión mayor
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**
- [ ] Docs ES y EN sin menciones de Kwipu ni Graphiti, con sus espejos en el mismo cambio; `/setup` sin paso 5-sexies de Kwipu/Graphiti y `/doctor` sin sus comprobaciones.
- [ ] Los dos CHANGELOG declaran el cambio rompedor, qué se retira, cómo migrar (memoria local o Kairos) y el commit recuperable.
- [ ] ADR-020, ADR-021 y la nota de ADR-018 quedan propuestos por el servicio de memoria (no a mano).

### T-10 — Retirar el marco de knowledge-services sin backends (decidido)

- **Descripción**: Sin backends, `knowledge-services` queda como marco dormido y se retira entero; la iniciativa de Kairos lo recupera del commit anotado en T-08. Medido: `knowledge-sync.py` 576 + `backends/__init__.py` 94 de código, 1.212 de test, 469 de docs de la skill y `knowledge-find.py:1377-1934` (558 líneas de lectura por `--intent`). `outbox.py` NO es del marco: lo usan el journal, `doctor.py` y `knowledge-schema.py`, y se queda.
- **Decidido por el usuario el 2026-11-10**: opción (b): el marco se retira y la iniciativa de Kairos lo recupera del commit anotado en T-08.
- **Changelog**: Se retira el marco de publicación a backends de knowledge-services: no queda código dormido sin adaptador.
- **Estado**: borrador
- **Tiempo humano**: est. 6h · real —
- **Tiempo IA (ejec.)**: est. 1.5h · real —
- **Dependencias**: T-08
- **Archivos**: **Se borran:** `skills/knowledge-services/**` (los 10 ficheros restantes), `agent-kits/shared/fixtures/graphiti-derived-read.json`, `agent-kits/shared/test_knowledge_{derivative_surface,routing}.py`, `tests/test_knowledge_{router,router_read,services}.py`, `evals/cases/skill-knowledge-services.json`. **Se editan:** `agent-kits/shared/knowledge-find.py` (`:1377-1934`, argumentos `--intent` y `--backends-dir`), `tests/test_knowledge_{find,approved_retrieval}.py`, `tests/test_hook_network_egress.py` (se retiran los tests que vigilan `--intent` y `knowledge-sync` desde hooks), `agent-kits/shared/{capabilities.py,doctor-reference.md,modules.json,knowledge-check.md}` (`:8` y `:22`), `agent-kits/dev-cycle/references/phase4-knowledge-gate.md` (`:25-27`), `agents/knowledge-curator.md`, `commands/setup.md`, `README.md`, `docs/{FLOWS,README}.md`, `docs/en/{FLOWS,README}.md`, `docs/agents/CONTRACTS.md` (fila E18), `docs/{,en/}guides/memory.md`, `docs/en/reference/doctor.md`, `ci.yml.MANUAL-COPY`, `.github/workflows/ci.yml`, `tests/test_ci_skill_suites.py`, `interop/**` (regenerado). **No cambian:** los 10 ficheros que casan `--intent` por ser `--intento` o `--intent-to-add` (lista en el plan). **Fragmentos que cargan los agentes:** `knowledge-check-governed.md` no menciona router, intent ni backends (comprobado): no cambia con (a) ni (b); `knowledge-check.md:8,22` dice «fallo de backend» y «backends declarados»: con (b) se reescribe.
- **Runtimes**: Sin diferencia por runtime: `knowledge-sync.py` y `knowledge-find.py --intent` son Python común. En `interop/` desaparecen las menciones de la skill en el índice de OpenCode y en las skills de Codex.
- **Verificación**:
  - `pytest -q tests/test_knowledge_find.py tests/test_knowledge_approved_retrieval.py tests/test_hook_network_egress.py agent-kits/shared/test_capabilities.py tests/test_ci_skill_suites.py` → verde; `python agent-kits/shared/knowledge-find.py --contexto x` sigue devolviendo aciertos locales (rojo antes: un test fija que `--intent` ya no existe)
  - `git grep -l -e "knowledge-find.py --intent" -- . ':!docs/roadmap' ':!CHANGELOG*' ':!docs/knowledge'` → vacío; `git grep -l "knowledge-services" -- . ':!docs/roadmap' ':!CHANGELOG*' ':!docs/knowledge'` → solo menciones históricas
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**
- [ ] No queda `skills/knowledge-services/` ni lectura por backend en `knowledge-find.py` (sin `--intent` ni `--backends-dir`); `outbox.py` y el journal intactos; la suite «ningún hook hace red» conserva sus tests de red.
- [ ] ADR-018 sigue vigente (Markdown canónico) con la nota de enmienda de T-09, y los fragmentos de agentes (`knowledge-check.md:8,22`, `phase4-knowledge-gate.md:25-27`, `agents/knowledge-curator.md`) ya no citan backends.

### T-11 — Sacar plugin-dev del plugin distribuido

- **Descripción**: `plugin-dev` (691 líneas, 58 KB, 353 caracteres de description) solo sirve para desarrollar este repo; se mueve a `.claude/skills/plugin-dev/`. Verificado en el repo: el payload de los instaladores no incluye `.claude/` (`install/providers.mjs:28-34`), el paquete portable ya la excluye (`export-skills.py:63,357`) y `.gitignore` no ignora `.claude/skills/`. Sin verificar: cómo carga cada runtime una skill de proyecto (paso 0 manual M-B).
- **Changelog**: plugin-dev deja de distribuirse con el plugin y queda como skill del propio repositorio.
- **Estado**: borrador
- **Tiempo humano**: est. 5h · real —
- **Tiempo IA (ejec.)**: est. 1.2h · real —
- **Archivos**: `skills/plugin-dev/**` → `.claude/skills/plugin-dev/**`, `.claude-plugin/{plugin,marketplace}.json`, `.codex-plugin/plugin.json` y `.agents/plugins/marketplace.json` (listas de skills; estos dos últimos se regeneran), `agent-kits/shared/{README.md,capability-selection.md,modules.json,rationalization-table.md,skill-index.py}`, `scripts/{export-skills,lint_plugin}.py`, `tests/{test_export_skills,test_session_context}.py` (`:315` cita `skills/plugin-dev/references/claude-code-contracts.md`), `hooks/session-journal.sh` (comentario `:27`), `evals/README.md`, `evals/cases/{skill-plugin-dev,skill-changelog-sync}.json`, `.github/ISSUE_TEMPLATE/pieza-nueva.yml`, `github-templates.MANUAL-COPY/ISSUE_TEMPLATE/pieza-nueva.yml`, `CLAUDE.md`, `CONTRIBUTING.md`, `README.md`, `README.es.md`, `docs/{INSTALL,INTEGRATION-ROADMAP,README,observability}.md`, `docs/en/{INSTALL,INTEGRATION-ROADMAP,README,observability}.md`, `docs/agents/ROLES.md`, `docs/guides/quality-playbook.md`, `interop/**` (regenerado)
- **Runtimes**: Claude: skill de proyecto, fuera del listado de consumidores; Codex: sin skill de proyecto conocida (enlace en CONTRIBUTING.md); OpenCode: la lee de `.claude/skills/` (`docs/INTEROP.md:90`).
- **Verificación**:
  - `git grep -l "skills/plugin-dev" -- . ':!docs/roadmap' ':!docs/knowledge' ':!CHANGELOG*'` → vacío (rojo antes: 6 ficheros de código y docs)
  - `pytest -q tests/test_export_skills.py tests/test_session_context.py tests/test_export_interop.py` → verde · `python evals/check.py` → exit 0 (si exige pieza para el caso de `plugin-dev`, se mueve o elimina) · `node --test tests/installer.test.mjs` → verde (el payload no cambia)
  - puertas de runtimes (cabecera) → verde
  - lectura (manual, sesión real; M-B) → Claude Code ve `plugin-dev` en este repo y NO en un proyecto con el plugin instalado; OpenCode la lee de `.claude/skills/`; en Codex se anota dónde ve skills de proyecto

**Criterios de aceptación**
- [ ] `skills/plugin-dev/` no existe, `modules.json` no la lista y los consumidores del plugin no la reciben (instalador, marketplace, paquete portable).
- [ ] Quien desarrolla este repo la sigue teniendo en Claude Code y OpenCode por `.claude/skills/`; para Codex CONTRIBUTING.md apunta al fichero.
- [ ] Si la verificación manual falla en algún runtime, la tarea se cierra con la alternativa documentada (conservarla en `skills/` y excluirla del payload) sin cambiar nada más.

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
- **Tiempo IA (ejec.)**: est. 0.5h · real 0.55h (medido; ventana compartida con T-02..T-07) + fix5 a fix16 sin horas propias (ventanas imputadas a T-06; la de fix16 de T-23 se midió en la misma ventana)
- **Archivos**: `tests/codex-plugin-state.test.mjs` (intento 12, orquestador: la regex del test de `candidates()` acepta CRLF; en un checkout de Windows `run-hook.mjs` llega con CRLF y el test daba rojo) · `docs/roadmap/2026-11-10-plugin-audit-2/testing/perf.md` (lo escribe el orquestador con las medidas de T-07 y T-23; el guardarraíl veta `testing/` al implementer) · `ci.yml.MANUAL-COPY` y `.github/workflows/ci.yml` (idénticos, comprobado con `diff`; el paso `pip install pytest pyyaml` de `:30-31` añade `pytest-xdist`), `tests/test_ci_manual_copy.py`, `tests/test_ci_skill_suites.py`, `tests/test_suites_no_pytest.py` · añadidos por la nota de alcance: `pytest.ini` (solo registra el marcador `serie`), `tests/test_redact_fix3.py`, `tests/test_npm_payload.py` (fix4: timeout de `npm pack` 120 → 600 s), `tests/test_local_state_fix3.py` (fix4: módulo al paso serie, plazo de pared del almacén), `agent-kits/shared/test_redact.py`, `agent-kits/shared/test_plan_review_summary.py`, `tests/test_agent_activity_store.py`, `tests/test_bench_session_end.py`, `tests/opencode-plugin.test.mjs` (fix1: espera a que el hijo escriba el JSON), `tests/test_lint_plugin.py`, `tests/test_ledger_lint.py`, `tests/test_dashboard.py` (fix1: wrappers `test_suite_legada_*` de sus `main()`/`run()`) (marcados `@pytest.mark.serie`: miden tiempo de pared o dependen del orden de lecturas y fallan bajo `-n auto`; corren en un paso aparte sin xdist), `agent-kits/shared/agent-activity-store.py` (fix5), `agent-kits/shared/test_redact.py` (fix5) · fix7 (corrección de fix8, gap 9: faltaban): `agent-kits/shared/test_ledger_view.py` (paso serie), `tests/test_graphiti_security.py` (huella del lanzador) · fix8: `agent-kits/shared/test_journal_io_deadline.py` (nuevo), `agent-kits/shared/journal-io.py` (plazo inyectable solo bajo `PYTEST_CURRENT_TEST`), `agent-kits/shared/test_journal.py`, `tests/test_redact_fix3.py`, `tests/test_native_guard_failclosed.py` (prueba de plazo al paso serie), `tests/test_panel_review_panel_server.py` (2 pruebas al paso serie) · fix9: `tests/test_fix9_plazos_inyectados.py` (nuevo), `agent-kits/shared/test_journal.py` (sin aserciones de pared), `tests/test_panel_review_panel_server.py` (BODY_TIMEOUT inyectado, sin paso serie), `tests/test_redact_fix3.py` (demo ×12 por la decisión de la puerta y sonda al crecimiento real) · fix10: `agent-kits/shared/test_journal.py`, `tests/test_fix9_plazos_inyectados.py` (vigía), `tests/test_redact_fix3.py`, `agent-kits/shared/journal-io.py` y `journal-capture.py` (`settled`: espera el estado transitorio de dos enlaces), `skills/training-data-services/scripts/test_dataset_assembler.py` y `agent-kits/shared/test_knowledge_read_context.py` (rojos de réplica de tiempo de pared) · fix12: `agent-kits/shared/journal-io.py`, `agent-kits/shared/test_journal.py`, `tests/installer.test.mjs` (el test de la CLI colgada mide desde el arranque de la CLI) · fix14 y fix15 (declarados en fix15, gap 14): `install/install.mjs` (`detached: true` en `correr` y el vigilante de señales: cambio de conducta en Linux y macOS), `agent-kits/shared/journal-capture.py`, `agent-kits/shared/journal-io.py`, `agent-kits/shared/journal.py` (presupuesto por proceso y plazo desde el arranque), `agent-kits/shared/test_journal_fix14.py`, `agent-kits/shared/test_journal_fix15.py` (nuevo), `hooks/opencode-plugin.js` y `interop/opencode/plugins/custom-agents/index.js` (regenerado: opt-in de la actividad), `tests/opencode-plugin.test.mjs`, `tests/helpers/opencode-context.mjs`, `tests/installer.test.mjs` · fix16: `tests/codex-query-deadline.test.mjs` (RED 2: el plazo corre desde que el worker está listo), `tests/hook-budget.test.mjs`, `tests/opencode-plugin.test.mjs` (fixture de 120 s con sondeo), `tests/installer.test.mjs` (3 tests de registro previo), `agent-kits/shared/codex-plugin-state.mjs` (`terminateProcessTree` en paralelo, plazo desde que el worker está listo), `agent-kits/shared/journal-io.py` (mínimo en la primera espera real), `hooks/run-hook.mjs` (8 s de captura de OpenCode y 2 s de confirmación de limpieza), `install/install.mjs` (registro previo, limpieza de restos, `TIMEOUT_CAZA` 15 s), `tests/process-tree-fix17.test.mjs` (fix17: nuevo; el árbol con identidad, `queryPlan` y `runBounded`), `tests/artifact-dom-security.test.mjs` (fix17, gap 22: el navegador headless se relanza si sale con código ≠ 0), `docs/{,en/}FLOWS.md`, `docs/{,en/}INTEROP.md` y `docs/{,en/}observability.md` (fix17, gap 13: plazos reales), `tests/hook-docs-marker.test.mjs`, `tests/hook-guard-delivery.test.mjs`, `tests/test_console_transport.py` y `tests/test_mermaid_blocks.py` (fix17, gap 22: rojos de la suite completa atribuidos, ver j17)
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

**fix17 (intento 17, gaps 3, 4, 5, 7, 8, 9, 10, 13, 18, 19, 20, 21 y 22; T-23 sigue `en-progreso`: falta la medida emparejada, del orquestador)** — `plugin-audit-2/T-23-fix17`; commits: los de T-06 (archivo `996bfae`, RED `eb8612b`) y `4eaf573` (GREEN T-23) más los que siguen en el log (`e1d0c31` arneses y `7a8dacd` rojos de la suite completa; ledger en el commit siguiente).
- **Árbol de procesos de Windows con identidad** (gaps 3, 5, 18 y 19; puntos 4 y 5). `terminateProcessTree(pid, presupuesto, máximo, {since, until, rootAlive})`: (a) con la raíz VIVA, `taskkill /T /F` primero; (b) el barrido CIM es respaldo, UNA proyección `ProcessId,ParentProcessId,CreationDate` y búsqueda en anchura en el cliente (no una consulta por pid), que solo acepta procesos con `CreationDate` ≥ `since` y ≥ la de su padre (si la raíz está muerta, los hijos directos además ≤ `until`) y confirma la muerte comparando pid + fecha dentro del propio script (hasta 15 s); (c) la espera NO sondea pids de víctimas (un pid reutilizado agotaba los 60 s): espera a que terminen `taskkill` (margen de 1,5 s para el barrido cuando la raíz estaba viva) y el barrido, dentro del presupuesto, que ya no tiene suelo de 1 s. **Instalador** (`install.mjs`, `correr` en Windows): el plazo lo guarda un worker, `runBounded` (`--run-bounded`, el patrón de `--query-worker`): `execFileSync` esperaba al worker, que lanza la CLI, la vigila y al expirar mata el árbol con la raíz viva; el resultado viaja por el descriptor 3. `matarArbol` queda solo para el grupo de procesos de Linux/macOS y `TIMEOUT_CAZA` desaparece. Test con PID reutilizado: un padre muerto con una víctima ANTERIOR al lanzamiento (`since` posterior) → la víctima **sobrevive**; control positivo con `since` anterior → muere (RED: la víctima moría).
- **Plazos coherentes** (gaps 4 y 20; punto 5). `queryPlan({launchedAt, readyAt, limit})`: plazo = min(listo + límite, tope exterior − 2 s de reserva), limpieza hasta tope − 200 ms; sin suelo. Con codex colgado (`codex.cmd` → node → descendiente) y un worker 3 s más lento: RED «el descendiente de codex sigue vivo» (SIGKILL exterior a mitad de la limpieza) → GREEN 0 huérfanos, en 8,1 s. OpenCode: `cleanupConfirmationMs(runtime, guard, uptimeMs)` = min(10 s, 19 s − tiempo desde el arranque del launcher), mínimo 250 ms; arranque + captura (8 s) + confirmación ≤ 20 s por construcción (test con arranques de 0 a 11 s).
- **Tests y arneses** (gaps 10, 21 y 22; punto 6). `uninstall` (Linux): el fake de codex ya no se cuelga en `remove` y el test comprueba que `uninstall` retira el manifiesto `incompleto` y lo que el instalador colocó; `SessionEnd`: los dos tests fijan `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS=4000` (el producto no cambia), el descendiente duerme 8 s y se comprueba el pid, no un marcador; `F001`: `debug-root-cause` dos causas: (a) el Edge headless sale a veces con código ≠ 0 al arrancar saturado (relanzado hasta 3 veces, aserciones intactas); (b) el borrado del perfil daba EPERM mientras el navegador lo soltaba (reintento de 15 s); `marker`: los 11 rojos de `marker …` eran `ETIMEDOUT` del tope de TEST de 5 s de `spawnSync` (node tarda 2,5-10 s en arrancar con carga) → 60 s; lo mismo en `hook-guard-delivery` (8,5 → 45 s), `hook-post-preflight` (5 → 60 s) y `hook-runtime` (3 → 30 s, con el presupuesto del anfitrión de SessionEnd a 5 s en los fixtures); además `test_console_transport` (`os.close(1)` no da EOF en Windows: se cierra el handle), `test_mermaid_blocks` (recorría `.venv` y `.pytest_cache`: no terminaba en 25 min), TLS de knowledge-services (margen de 80 ms → x4) y la huella del lanzador de `test_graphiti_security` (revisado el diff de `run-hook.mjs`).
- **Traza y docs** (gaps 7, 8, 9 y 13; punto 7). Docs y espejos EN con los plazos reales (6 s con recorte al tope exterior, 8.000 ms de OpenCode, árbol con la raíz viva): `FLOWS.md`, `INTEROP.md` y `observability.md` (+ `en/`). Comentarios antiguos («15 s», «+ 4 s») eliminados al reescribir el bloque. **Lista de commits completa de fix16** (la del ledger omitía nueve): `4052395` RED, `84c9d48` RED 2, `20e81be`, `a31169e`, `075265a`, `e3535f3`, `491fd19`, `0a18831`, `525135c`, `9cc0382`, `1169f63`, `a01654c`, `fc1474a`, `d53febe`, `a68bda9`, `1c58e64`, y del ledger `90904e7` y `cb59eef`. **Trabajo de fix16 SIN MEDIR** (gap 9): el marcador se cerró a las 15:27Z (16:27 locales); `90904e7` (ledger, 16:32), `1c58e64` (código, 17:28) y `cb59eef` (cierre con las pasadas, 20:08) son posteriores: unas 3,7 h de reloj sin medir, que no se imputan.
- **Interpretaciones j10 a j17 (T-23).** **j10** `since` es el instante de pared del lanzamiento menos 100 ms, no la `CreationDate` del PID raíz anotada con una consulta al lanzar: no hay API barata en Node (una consulta CIM cuesta 1-3 s por proceso lanzado) y el instante propio basta, porque un proceso anterior al lanzamiento no puede descender de lo que se lanza; `until` (instante de la muerte de la raíz) cierra el caso de la raíz muerta. **j11** El barrido NO va `detached`: un PowerShell sin consola (DETACHED_PROCESS) sale al instante sin ejecutar nada (medido: exit 0 en 170 ms, sin fichero escrito, frente a 1,6 s y fichero con el proceso unido al job); la limpieza debe caber antes del SIGKILL exterior (de ahí `queryPlan`). **j12** El instalador pasa por un worker en Windows (un `node` extra por cada CLI lanzada, 0,1 s en reposo y la mediana de 3,7 s con carga): es el coste de que el dueño del plazo pueda matar con la raíz viva; solo en Windows. **j13** El tope de 10 s de la confirmación de OpenCode (la desviación de 10 s de fix16, que el intento 17 pedía numerar o retirar) se CONSERVA como tope y ya no es un valor fijo: toma lo que queda de los 20 s. **j14** `queryPlan` calcula `launchedAt` como `deadlineAbsoluto − límite` (el padre pasa `Date.now() + límite`): sin cambio de protocolo con el worker. **j15** El `taskkill` de la consulta tampoco va `detached` (mismo motivo que j11). **j16** El test de `uninstall` y el de la señal siguen siendo de Linux/macOS (no hay manejadores POSIX en Windows): se ejecutan en la réplica Linux. **j17** `F001`: el Edge headless sale a veces con código ≠ 0 al arrancar con la máquina saturada y el test repite el lanzamiento (hasta 3 veces) sin tocar las aserciones del producto.

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
- **Archivos**: `docs/roadmap/2026-11-02-kwipu-metadata/tasks.md`, `docs/roadmap/2026-11-02-session-visibility/tasks.md`, `docs/roadmap/2026-11-03-knowledge-verification/tasks.md`, `docs/roadmap/2026-09-09-project-specialization/improvement-plan.md`, `docs/roadmap/2026-10-07-catalog-capabilities/improvement-plan.md`, `docs/roadmap/2026-10-31-control-center/improvement-plan.md`, `docs/roadmap/2026-09-09-brief-budget/spec.md`, `docs/roadmap/2026-11-05-audit-remediation/spec.md`, `docs/roadmap/2026-10-27-opencode-reader-fixes/`, `docs/roadmap/CALIBRATION.md`, `docs/roadmap/README.md`, `docs/roadmap/2026-09-16-dev-cycle-dataset/{spec,improvement-plan,tasks}.md` (solo si T-32 no la cierra)
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

## Revisión de dos lentes — intento 1: Fase 1 (T-23, T-02..T-07) — 1 Critical, 6 Important, 11 Minor

Diff `57fb054..HEAD`. Lentes: A+B+C+D. C la activó `review-lens-select.py` (rutas `.github/workflows/` y `session`); D la activó el orquestador porque T-07 y T-23 son tareas de rendimiento (el script dio `lente_d: false`). Las cuatro, por el agente `reviewer`.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Critical | El bucle nuevo de la CI deja sin ejecutar el `main()`/`run()` de las suites mixtas (tienen algún `def test_*` y casos solo en `__main__`): `tests/test_lint_plugin.py:561-1166`, `tests/test_ledger_lint.py:56-473`, `tests/test_dashboard.py:426-650`. `test_suites_no_pytest.py` no lo ve (A1, B1) | T-23 | corregido (2724104) | `ci.yml.MANUAL-COPY:49`; `pytest --collect-only` no llama a `main()`/`run()` |
| 2 | Important | La CI queda en rojo y el ledger no lo registra: `check-handbook.py` (`source_changed` de `docs/guides/atlassian.md`, `docs/reference/atlassian.md`, `modules.json`) y `test_f4fix2_5` (exige que el registro cerrado `2026-11-09-…/testing/tokens.md` cite los tamaños de HEAD) (A2) | T-03, T-02 | corregido (f03313f: 2a desacoplado del registro cerrado; 4fa93a8: 2b registrado como rojo conocido en T-03, acción del usuario) | `python scripts/check-handbook.py` → exit 1; `pytest tests/test_f4fix2_misc.py::test_f4fix2_5…` → 1 failed |
| 3 | Important | La verificación en Linux de T-23 da recuento y tiempo, no passed/failed; con el gap 2 «mismo resultado» no puede estar en verde (A3) | T-23 | corregido (5bb47c1: passed/failed/skipped por paso en T-23; todo rojo investigado y corregido salvo el de los PDF, acción del usuario) | `tasks.md` T-23, nota de cierre |
| 4 | Important | El guardarraíl de T-06 compara el pathspec del árbol entero de forma literal: pasan `./`, `..`, `*`, `':/*'`, `:/.`, `':(top)*'`, `':(glob)**'`, `"$PWD"`, `--pathspec-from-file` (B2, C1) | T-06 | corregido (cc08209) | `agent-kits/shared/guardrail-check.py:761,783`; sonda `check_git` → `allow` |
| 5 | Important | `--baseline` compara un informe parcial con uno completo sin decirlo y anuncia «↓ mejora» (o «↑ empeora») falsa (B3) | T-07 | corregido (02e602b) | `skills/code-health/scripts/code-health.py:631-643` |
| 6 | Important | La memoria del emparejado sigue siendo cuadrática en copias por ventana (Σ min(occ,50)² pares en un `set`); 60 copias de una plantilla grande agotan 1 GiB antes del corte por tiempo (D1) | T-07 | corregido (02e602b) | `code-health.py:344-358`; tracemalloc 75 MiB con 60×500 líneas |
| 7 | Important | `--max-seconds` no cubre `git blame`: un subproceso por TODO fuera del plazo, y el informe no sale como parcial (D2) | T-07 | corregido (02e602b) | `code-health.py:515,546`; 10 `git blame -L` = 4,59 s |
| 8 | Minor | `TOKEN-EFFICIENCY.md` ES/EN cambia en un commit de T-02 y no figura en sus `Archivos` (A4) | T-02 | corregido (4fa93a8) | commit `14adaca` |
| 9 | Minor | Falta la evidencia de la Verificación 2 de T-02 (`test_export_interop -k skill`, la ruta `SKILL.md` en lo generado) (A5) | T-02 | corregido (f03313f) | `tasks.md` T-02 |
| 10 | Minor | Las medidas de T-07 y T-23 solo constan en el ledger; `testing/perf.md` no existe (A6) | T-07, T-23 | pendiente (orquestador, al cerrar la fase) | `improvement-plan.md:199` |
| 11 | Minor | La puerta de runtimes de T-04 solo pega `export-interop --check` (A7) | T-04 | corregido (4fa93a8) | `tasks.md` T-04 |
| 12 | Minor | No hay forma de desactivar el tope por ventana desde la CLI (B4) | T-07 | corregido (02e602b) | `code-health.py:577,714-721` |
| 13 | Minor | Las carpetas ocultas versionadas salen del análisis sin el aviso de «excluidos versionados» (B5) | T-07 | corregido (02e602b) | `code-health.py:236,487` |
| 14 | Minor | Los scripts que siguen en el bucle también los corre `test_suites_no_pytest.py` bajo pytest: doble ejecución (B6, D3) | T-23 | corregido (2724104) | `ci.yml:49` + `tests/test_suites_no_pytest.py:76-81` |
| 15 | Minor | El linter de T-03 busca la colisión por carpeta, no por `name:`; un `SKILL.md` con BOM cuenta como invocable (B7) | T-03 | corregido (4b414c7) | `scripts/lint_plugin.py:667-672` |
| 16 | Minor | Falso positivo: `git checkout -bfeature` se deniega porque el clúster contiene `f` (B8) | T-06 | corregido (cc08209) | `guardrail-check.py:780` |
| 17 | Minor | Un fichero enorme no se interrumpe: `leer()`/`lineas_codigo()` sin plazo ni tamaño (D4) | T-07 | corregido (02e602b) | `code-health.py:251-254,572-579` |
| 18 | Minor | Con el tope, las 50 primeras ocurrencias pueden ser del mismo fichero y se pierde la duplicación entre ficheros; el aviso escribe el tope por defecto aunque se pase otro; con el plazo vencido en la lectura, `duplicados` da 0 % como «mínimo» (D, fuera de lente) | T-07 | corregido (02e602b) | `code-health.py:345,354,582` |

Decisiones del orquestador: (a) `test_f4fix2_5` se desacopla del registro fechado (CLAUDE.md: los registros de `docs/roadmap/` no se reescriben); las comprobaciones de los docs vivos `TOKEN-EFFICIENCY.md` contra HEAD se conservan. (b) `check-handbook.py`: el manual PDF no tiene generador en el repo y la fase 2 cambiará más fuentes; queda registrado como rojo conocido con acción del usuario (regenerar las ediciones), a decidir por el usuario.

## Revisión de dos lentes — intento 2: Fase 1 (T-23, T-02..T-07) — 0 Critical, 1 Important, 8 Minor

Diff `e4ff91f..HEAD` (ciclo de corrección 1). Lentes: A+B+C+D (C y D activadas por `review-lens-select.py`). Los 17 gaps del intento 1 asignados al implementer quedan `corregido` según las cuatro lentes; ninguno se reabre. El gap 10 (`testing/perf.md`) sigue con el orquestador.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | El guardarraíl sigue dejando pasar pathspecs que abarcan el árbol entero: `':'` (magia con patrón vacío), `'?*'`, `"$(git rev-parse --show-toplevel)"`, `~+`, `"$CLAUDE_PROJECT_DIR"`, `"$(realpath .)"`; y en `restore`, una ruta antes de un `--` final (`git restore . --`) no se trata como pathspec (B1, C1, C2) | T-06 | corregido (c3b096e) | `agent-kits/shared/guardrail-check.py:803,814,825,886-891`; repo git real: 0 de 3 ficheros modificados tras cada forma |
| 2 | Minor | Dos informes parciales con distinta cobertura se comparan como comparables (B2) | T-07 | corregido (b705758) | `skills/code-health/scripts/code-health.py:777` |
| 3 | Minor | Un `git blame` cortado por timeout o por `OSError` (línea de comandos de más de 32 K en Windows con muchos `-L`) devuelve `{}` sin marcar el informe parcial ni avisar (B3, D fuera de lente) | T-07 | corregido (b705758) | `code-health.py:597-600,646-648` |
| 4 | Minor | Con `--max-occ 0`, `--max-seconds` deja de acotar: el plazo no se mira dentro del doble bucle y los pares del mismo fichero no cuentan para `max_pares` (36 s con plazo de 2 s) (D1) | T-07 | corregido (b705758) | `code-health.py:376,389-393` |
| 5 | Minor | El criterio de linealidad de `redact` (razón ≤ 8 con entrada ×4) acepta O(n^1,5) y una ralentización lineal de ×6; el caso pequeño se mide en frío (A-N2, B5) | T-23 | corregido (09aeec9) | `tests/test_redact_fix3.py:245-248` |
| 6 | Minor | El detector AST de casos solo en `__main__` no ve asserts directos en el bloque, funciones pasadas por referencia ni llamadas por atributo; hoy no hay ningún caso así (B4) | T-23 | corregido (09aeec9) | `tests/test_suites_no_pytest.py:151-153,181` |
| 7 | Minor | El ledger registra el rojo del PDF como si solo afectara a `check-handbook`; también falla `test_npm_payload::test_npm_contains_pdf_editions_linked_from_its_readme` en el paso pytest (A-N1) | T-03, T-23 | corregido (09aeec9) | `tasks.md` T-03 y tabla Linux de T-23 |
| 8 | Minor | El gap 8 del intento 1 se cerró sin test ni «TDD n/a» (CONSTITUTION l.13) (A-N3) | T-02 | corregido (09aeec9) | `tasks.md` T-02 |
| 9 | Minor | (orquestador) `testing/perf.md` con las medidas de T-07 y T-23 — arrastrado del intento 1, gap 10 | T-07, T-23 | corregido (orquestador, `testing/perf.md`) | `testing/perf.md` con las tablas de T-23 y T-07 |

Decisión de diseño del orquestador para el gap 1 (lección de la retro anterior: fijar el diseño, no ir caso a caso): el guardarraíl pasa de lista de bloqueo a lista de permitidos para las restauraciones que tocan el árbol de trabajo. Un pathspec se permite solo si es una ruta relativa literal sin magia (`:`), sin comodines (`*`, `?`, `[`), sin expansión de shell (`$`, `` ` ``, `~`) y que, normalizada, queda dentro del directorio actual sin ser él mismo ni la raíz; cualquier otra forma se deniega. En `restore`, los argumentos que no son opción cuentan como pathspec estén antes o después de `--`.

## Revisión de dos lentes — intento 3: Fase 1 (T-23, T-02..T-07) — 0 Critical, 2 Important, 8 Minor

Diff `5b2d379..HEAD` (ciclo de corrección 2). Lentes: A+B+C+D. Los gaps 1-9 del intento 2 quedan corregidos salvo lo que se reabre abajo con evidencia nueva. Las lentes B y D se reanudaron tras un corte de sesión.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | Una orden que termina en `\` no se analiza: `_segmentos` descarta el último segmento incompleto, y `git checkout .\`, `git restore .\` o `git checkout HEAD -- .\` salen sin deny; Git for Windows trata `.\` como `./` y descarta el árbol entero (B1) | T-06 | corregido (67ae79a, fix3) | `agent-kits/shared/guardrail-check.py:274-275`; hook `pre-tool --agent implementer` sin deny; repo de prueba: 0 de 3 ficheros modificados |
| 2 | Important | La puerta de linealidad de `redact` es intermitente: razón máxima 6,69 en una pasada frente al tope de 6,5 (D), 5,80-5,89 en Windows en reposo, 9,29 en Linux con carga, 2 rojos de 6 con carga ajena (ledger); el plan no acepta rojos intermitentes (A-N1, B4, D) | T-23 | corregido (84ec8ba, fix3) | `tests/test_redact_fix3.py:245-257,280-288`; `improvement-plan.md:279` |
| 3 | Minor | El pathspec se resuelve contra el `cwd` del hook e ignora `git -C <dir>`, `--work-tree`, `env -C` y un `cd <dir> &&` previo; en un proyecto dentro de un monorepo, `git -C .. restore proj` descarta los cambios del proyecto (C1, A fuera de lente) | T-06 | corregido (67ae79a, fix3) | `guardrail-check.py:366-369,804-814`; repo de prueba `r3` |
| 4 | Minor | El código permite lo que queda «dentro del proyecto» (`../docs/` desde un subdirectorio) y el diseño fijado decía «dentro del directorio actual»; el mensaje de denegación sigue diciendo lo segundo (A-N2) | T-06 | corregido (67ae79a, fix3) | `guardrail-check.py:806-814,857`; `test_guardrail_check.py:874-885` |
| 5 | Minor | `testing/perf.md` cita «57 s» y «45 s» como evidencia de la tarea y no están en el ledger (A-N3) | T-23 | corregido (orquestador: la línea cita su fuente, la Lente D del intento 2) | `testing/perf.md:3,22` |
| 6 | Minor | `_cobertura` compara solo `(ficheros, líneas)`: dos parciales cortados en fases distintas se comparan (mejora falsa 12,0 → 3,1 %) (B2) | T-07 | corregido (366946a, fix3) | `skills/code-health/scripts/code-health.py:808-820` |
| 7 | Minor | Un `git blame` con código ≠ 0 (p. ej. `-L` fuera de rango por un `\x0c`) se clasifica `error`, pierde las edades de todo el trozo de 200 y no marca el informe parcial (B3) | T-07 | corregido (366946a, fix3) | `code-health.py:536-537,632-633` |
| 8 | Minor | En `restore`, el valor separado de `-s`/`--source` cuenta como pathspec: `git restore --source "$BASE" src/a.py` se deniega (B5) | T-06 | corregido (67ae79a, fix3) | `guardrail-check.py:836-837` |
| 9 | Minor | El test lento de `redact` llama otra vez a `redactar(grande)` solo para obtener la salida: +9 a +18 s por pasada del paso serie (D1) | T-23 | corregido (84ec8ba, fix3) | `tests/test_redact_fix3.py:288` |

**Decisión del orquestador al agotar los tres intentos:** un ciclo final acotado, con diseño fijado antes del fix (lección de la retro anterior), sin un cuarto intento abierto. Tras el ciclo final, una sola pasada de verificación dirigida sobre los gaps 1-4 y 6-9.

- Gap 1: el analizador falla cerrado. Si una orden de shell no se puede tokenizar entera (escape final, comilla sin cerrar), toda orden `git` destructiva que contenga se deniega con motivo «orden incompleta». Nada se descarta en silencio.
- Gap 3: falla cerrado. Una restauración que toca el árbol de trabajo se deniega si la orden cambia la base (`git -C`, `--work-tree`, `--git-dir`, `env -C`/`--chdir`, o un `cd`/`pushd` anterior en la misma orden). Quien necesite otra base puede ejecutar la orden desde ese directorio.
- Gap 4: lo implementado pasa a ser el diseño (dentro del proyecto y sin ser el propio directorio, un ancestro ni la raíz; riesgo equivalente a `git restore docs/` desde la raíz). Se corrigen el mensaje de denegación y `docs/agents/implementer.md`.
- Gap 2: la puerta mide lo que quiere proteger, que es la ausencia de retroceso catastrófico (cuadrático o peor), no el tiempo de pared. Usa tiempo de CPU (`time.process_time`) y la mediana de 3 por tamaño. La entrada crece ×8: lineal ≈ 8, n^1,5 ≈ 22,6, cuadrático ≈ 64. El tope es 16, el doble del lineal. Se mide en Linux y Windows con carga ajena; sin ningún rojo en 10 ejecuciones seguidas.
- Gaps 6-9: la comparación exige la misma cobertura y los mismos motivos de parcialidad; un blame con código ≠ 0 se reintenta por línea y lo que quede sin edad marca el informe parcial con aviso; el valor separado de `-s`/`--source` no cuenta como pathspec; la salida se toma de la última medición.

## Revisión de dos lentes — intento 5: Fase 1 (T-06, T-07, T-23, T-38) — verificación dirigida del fix4: 5 Important, 5 Minor

Lentes: A+B+C+D sobre `cdcda09..HEAD` (`0fd3de2`). Motivos de C: `handbook-render.mjs:50` (`$eval` de Puppeteer, sin hallazgo) y `test_bench_session_end.py`; de D: `build-handbook.py:227` y `handbook-render.mjs:116-118` (sin hallazgo). Cerrados del intento 4: gaps 2-6 y T-38 (`check-handbook` exit 0, PDFs sin datos personales, generador idéntico al de la rama salvo lo declarado). Los rebates del implementer al diseño (×16 en vez de ×8; caso `None` con el tope por debajo del suelo) se aceptan con su evidencia. La fase **no** cierra: el salto de heredoc del gap 1 reabre evasiones que `cdcda09` denegaba. Tres lentes lo confirman por separado en bash real.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | El salto de cuerpo de heredoc oculta órdenes que bash ejecuta: `<<` aritmético (`$((1<<2))`, `let x<<=2`), here-string `<<<` detectado como `<<`, delimitador sin quitar comillas/escapes (`<<\EOF`, `<<E"OF"`); y un heredoc sin cierre solo marca incompleto el último segmento. Antes: DENY; ahora: allow | T-06 | superado (re-evaluado en el intento 6) | Lentes B y C: `guardrail-check.py:265,303-322,1022-1025`; sondas `scratchpad/lc5/probe.py`, `scratchpad/vf5/p.py`; bash real (`EXECUTED-arith`, `a.txt` restaurado) |
| 2 | Important | El cuerpo «de shell» solo se analiza si la shell es el primer token del ÚLTIMO segmento: `env bash`, `A=1 bash`, `command`/`exec`/`time`/`sudo bash`, `bash <<'EOF' 2>&1`, `bash <<EOF \| tee`, `cat <<EOF \| bash; true`, `eval "$(cat <<'EOF' …)"`, `. /dev/stdin <<EOF` → allow | T-06 | superado (re-evaluado en el intento 6) | Lentes A, B, C: `guardrail-check.py:307,312-314`; repo real: 0 de 2 ficheros modificados tras `env bash <<EOF⏎git restore .⏎EOF` |
| 3 | Important | Con delimitador sin comillas bash expande `$(…)` y los backticks del cuerpo; tratarlo como datos deja pasar `cat <<EOF⏎$(git restore .)⏎EOF` | T-06 | superado (re-evaluado en el intento 6) | Lente A: `guardrail-check.py:303-317`; repo real `scratchpad/r1` |
| 4 | Important | `_cambia_base_en` es O(N·K) sin tope (`toks[idx:]`, `realpath` por cada `cd .`): con 30 KB el hook agota su plazo y el lanzador sigue sin deny (`run-hook.mjs:405,461`). Así, `echo cd .`×6000 + `; git push --force origin master` pasa | T-06 | superado (re-evaluado en el intento 6) | Lente D: `guardrail-check.py:508,528,537,551`; hook real 6,1 s, `hook timed out` / `role guard unavailable` |
| 5 | Important | El paso `serie` pasa de 55-64 s a 586 s (1.054 tests: 761 de `test_console_encoding`, 240 de `test_agent_activity_store` y 27 de `redact_fix3`); la Verificación de T-23 («< 50 % del serie, anotado en `testing/perf.md`») deja de cumplirse | T-23 | superado (re-evaluado en el intento 6) | Lente D: `tasks.md:680,746`; `test_console_encoding` 197 s, `test_agent_activity_store` 127 s, puerta ~9 s de CPU por caso |
| 6 | Minor | Residual previo al fix4: una comilla doble impar en el cuerpo de `git commit -m "$(cat <<'EOF' …)"` deja la comilla abierta y oculta las líneas siguientes | T-06 | superado (re-evaluado en el intento 6) | Lente B (allow también en `cdcda09`) |
| 7 | Minor | Falsos denies: `cd`/`pushd`/`popd`/`chdir`/`env`/`git` como argumento cuentan como cambio de base (`echo cd; git restore …`, `git restore src/cd`) | T-06 | superado (re-evaluado en el intento 6) | Lentes A, B y D: `guardrail-check.py:548-552` |
| 8 | Minor | Un fichero con separador solo CR queda en una línea, con los TODO colapsados y sin aviso (`parcial: false`) | T-07 | superado (re-evaluado en el intento 6) | Lente B: `code-health.py:263-274` |
| 9 | Minor | Aserciones que no pueden fallar (`tc < SUELO_CPU` en la rama `None`, `tc >= 0.03/8`); el tope de 8 s de CPU de `test_2_2` deja ~2,25× de margen | T-23 | superado (re-evaluado en el intento 6) | Lente A: `test_redact_fix3.py:391,440`; `test_redact.py:656` |
| 10 | Minor | Ledger: «606 antes + 39» (el total es 606); el RED de fix4/T-38 se comiteó después del código | T-06, T-07, T-23, T-38 | superado (re-evaluado en el intento 6) | Lente A: `tasks.md:242`; `0fd3de2` frente a `f67d090`… |

**Diseño fijado por el orquestador para este ciclo.** Los gaps 1-4 y 6 tienen una sola causa: el guardarraíl acepta una orden que ha leído a medias.

1. **Invariante de cierre.** Si al terminar de tokenizar la orden COMPLETA queda algo abierto en cualquier punto (comilla, heredoc, `$(`, backtick, `((`), la orden entera se deniega si contiene cualquier `git` o un cambio de base. Ya no se mira solo el último segmento.
2. **Saltar el cuerpo es la excepción, por lista blanca.** El cuerpo de un heredoc se trata como datos SOLO si se cumplen a la vez tres condiciones:
   - (a) el delimitador está entrecomillado o escapado (`'EOF'`, `"EOF"`, `\EOF`), así que no hay expansión;
   - (b) el heredoc cierra;
   - (c) en ninguna posición de la orden completa aparece un intérprete o envoltorio: `bash`, `sh`, `zsh`, `dash`, `ksh`, `eval`, `source`, `.`, `exec`, `env`, `sudo`, `command`, `time`, `xargs`, `nohup`.

   En cualquier otro caso el cuerpo se analiza como órdenes, como hacía `cdcda09`. Fallar hacia el deny es aceptable, porque el implementer puede entrecomillar el delimitador.
3. **Reconocer `<<` como bash.** Nunca cuentan `<<<` ni un `<<` dentro de `$(( ))`, `(( ))`, `let` o comillas simples. Dentro de `"…$(…)…"` sí cuenta, porque `$(` abre un contexto nuevo. El delimitador se lee quitando comillas y barras invertidas.
4. **Cambio de base solo en posición de programa.** Se mira tras las asignaciones, las palabras de control y los envoltorios del punto 2. El recorrido es lineal: nada de `toks[idx:]` por token, y el `realpath` del cwd se calcula una sola vez por orden.
5. **Tope de entrada dentro del guard.** Por encima de N bytes o M tokens (p. ej. 16 KB / 4.000), la orden se deniega si contiene `git` o un cambio de base, ANTES del análisis caro. El guard nunca agota el plazo del lanzador. Test de punta a punta por `run-hook.mjs` con el payload de 30 KB de la Lente D → deny en < 1,5 s.
6. **Test diferencial contra bash real** (bash está en CI Linux y en Git Bash). Un corpus con TODAS las sondas de las lentes A, B y C de los intentos 4 y 5 se ejecuta en un repo temporal con centinela.
   - Toda orden que en bash real llegue a ejecutar `git restore`/`reset`/`checkout`/`push` debe salir DENY del guard.
   - Las órdenes legítimas del corpus deben salir allow: un commit con `<<'EOF'` y apóstrofos o comillas impares en el mensaje, `git -C <dir> status` y `cd <propio dir>`.
7. **Paso `serie` (gap 5).**
   - `test_console_encoding` y `test_agent_activity_store` vuelven al paso paralelo. Sus fallos de plazo se resuelven con un plazo que el test pueda inyectar (variable de entorno o parámetro), no midiendo el reloj de la máquina. Si hace falta un test del plazo real de 1,3 s, es UNO y va en serie.
   - La puerta de redact baja su coste sin perder la separación: referencia lineal sobre una entrada menor y menos muestras por ronda.
   - Objetivo: paso serie ≤ 90 s en la réplica Linux y Verificación de T-23 cumplida. El orquestador actualiza `testing/perf.md` con la réplica nueva.
8. **Minor 7-10.**
   - El 7 lo cierra el punto 4.
   - El 8 se cierra añadiendo «separador solo CR» a `parcial_motivos` cuando el fichero tiene `\r` sin `\n`.
   - El 9 se cierra quitando las aserciones tautológicas y estrechando el tope de `test_2_2`, o justificándolo en el ledger.
   - El 10 se cierra corrigiendo las cifras. El orden RED/GREEN de los commits ya publicados no se reescribe y queda anotado como deuda.

Tras este ciclo, verificación dirigida con las cuatro lentes, con el corpus diferencial como entrada. Si solo quedan Minor sin pérdida de datos, la fase cierra.

## Historial archivado

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


## Revisión de dos lentes — intento 17: Fase 1 (T-06, T-07, T-23) — verificación dirigida del fix16: 5 Important, 17 Minor

Lentes: A+B+C+D sobre `548dc3e..cb59eef`, dos a dos por memoria. El orquestador verificó las puertas (`ledger-lint` 0 incoherencias, `scope-check --base 57fb054` exit 0, `lint_plugin` 0 errores, `export-interop --check` 88, `cmp ci.yml`, `git grep` de datos personales vacío) y las 18 formas del intento 16 (deny; `git status` y `git checkout HEAD -- f.txt` siguen en allow). Carga ajena entre el 35 y el 100 % durante todas las medidas: no hubo reposo.

**Cerrado del intento 16:**
- Los gaps 1-10 (formas de env, `--` en la rama, punto fijo en palabras, `eval --`/`builtin --`, `trap`, `-oc`/`-Oc`/`-co`, `env 1=x`/`coproc`, `checkout -B main`, coste de la rama, `terminateProcessTree`, manifiesto `incompleto`).
- **TDD real.** Lente A: el RED `4052395` solo trae tests; reejecutado sobre su árbol da 380 failed y 59 passed, y el journal 4 failed. En HEAD, 596 passed.
- **Recuentos.** El diferencial 2.690 / 7.056 / 60.000, los 5.479 deny nuevos y las 357 regresiones (255 de `checkout <ref> <ruta>` y 102 de opciones de `env`) coinciden con los datos. El archivado de fix15 es literal (SHA-256). 16,03 + 47,14 = 63,17 h.
- **Rama barata.** Lente B: misma rama que git en 8 casos (repo, worktree, submódulo, subdirectorio, sin commits, HEAD suelto, inexistente, `GIT_DIR`). El guard ya no lanza git: `echo hola` p50/p95 893/1.153 → 480/649 ms con carga (Lente D). Coste lineal (cocientes 3,8-5,0 al cuadruplicar).
- **Sin falsos deny** en 52 órdenes normales de un implementer (Lente B).
- **Instalador.** `limpiarRestosCodex` no sigue uniones ni enlaces duros ni toca restos de un instalador vivo; el `incompleto` previo lo sustituye el siguiente guardado (Lentes B y C).
- **Plazos subidos.** `TIMEOUT_CAZA` de 60 s es coste real de WMI con carga, no un proceso que no muere (Lente D). Consulta nativa a 6 s: aceptada.
- **Journal.** Sin regresión: 19 de 40 > 800 ms con fix16 frente a 29 de 40 con 548dc3e, ambos con carga; no verificable en reposo.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | **Clase: git que lanza otro git.** La regla general no mira lo que va detrás de un programa que ya es git (`guardrail-check.py:2145`): `git submodule foreach [--recursive] git reset --hard` (con git real borra cambios sin comitear del submódulo), `git rebase -x 'git reset --hard'`, `git bisect run git …`. No es regresión. Verificado por el orquestador | T-06 | pendiente | Lente B: `lb17/` |
| 2 | Important | **Clase: envoltorio o shell detrás de un programa fuera de la tabla.** Solo se re-ancla en palabras `git`, y el sufijo hereda `bindings`, `via_xargs` y `base_cambiada` de la orden exterior (`:1662,1672,2143-2153,2462,2472-2488`). Pasan `uv run bash -c 'git clean -fdx'`, `chroot / sh -c 'git push --force'`, `strace -f bash -c …`, `uv run --no-project env -S 'git reset --hard'` (con git real borra el cambio; sin `uv run` da deny), `strace env GIT_WORK_TREE=.. git restore a.txt`, `strace xargs git restore`. No es regresión. Verificado por el orquestador | T-06 | pendiente | Lentes B y C (CWE-184): `lb17/`, `lc17/` |
| 3 | Important | **`terminateProcessTree` mata por `ParentProcessId` sin fecha de creación.** Windows reutiliza los PID: la función real mató a un proceso propio anterior y no descendiente. En la sesión hay 25 procesos con el padre muerto (`explorer.exe`, `OneDrive.exe`…); en 1.500 creaciones, 2 recibieron uno de esos PID. fix16 lo amplía (barrido completo y recursivo con el PID raíz) | T-23 | pendiente | Lente C (CWE-672): `codex-plugin-state.mjs:37,44-47`, `install.mjs:1282,1339` |
| 4 | Important | **El tope exterior deja huérfanos con carga.** El plazo de la consulta corre desde que el worker está listo, sin recortarse al tope exterior (suelo de 1.000 ms). Con codex colgado y 2 s de arranque lento del worker, el SIGKILL llega a 9,0 s y quedan 2 huérfanos (3 de 3); por `/doctor` (tope 10 s) basta 1 s (2 de 2). El job de libuv no protege a los nietos (`SILENT_BREAKAWAY_OK`) | T-23 | pendiente | Lentes A y D (D17-1): `codex-plugin-state.mjs:31,41,91-95,115` |
| 5 | Important | **El rojo `gap 8` del instalador es trabajo evitable.** `execFileSync` mata primero la raíz y solo queda el barrido PowerShell + CIM (3,3-4,8 s; > 20 s con CPU saturada). `taskkill /T` con la raíz viva tarda 0,86-1,14 s con 0 supervivientes | T-23 | pendiente | Lente D (D17-2): `install.mjs:1324-1339` |
| 6 | Minor | Gaps 19 y 24 del intento 16 siguen abiertos aunque el ledger los da por tratados: `test_guardrail_fix15_corpus.py:129-132` conserva motivos falsos de `SIN_PARIDAD15` y `test_guardrail_fix15.py:189-212` decide por stdout | T-06 | pendiente | Lente A (1) |
| 7 | Minor | La confirmación de limpieza a 10 s (diseño: 2 s) no está numerada entre i1-i16 | T-23 | pendiente | Lente A (2): `tasks.md:888,893`, `run-hook.mjs:455` |
| 8 | Minor | Valores viejos: `Archivos` de T-23 (`tasks.md:665`) dice 15 s y 2 s; comentarios `install.mjs:1278-1281` («15 s») y `codex-plugin-state.mjs:27,90` («+ 4 s»); la lista de commits de T-23 omite nueve | T-23 | pendiente | Lente A (3) |
| 9 | Minor | Trabajo sin medir: el marcador se cerró a las 15:27Z y `1c58e64` (código) y `cb59eef` son posteriores | T-06, T-23 | pendiente | Lente A (4) |
| 10 | Minor | El test del punto 5 solo comprueba que `uninstall` encuentra el manifiesto, no que deshace lo registrado; el fake de codex se cuelga en `marketplace remove` | T-23 | pendiente | Lente A (5) |
| 11 | Minor | `git checkout -B <otra-rama-existente> [<ref>]` se permite y le quita sus commits (equivale a `branch -f`, que se deniega). Comprobado con git real | T-06 | pendiente | Lentes A (6) y B (4): `guardrail-check.py:2238-2246` |
| 12 | Minor | Falso deny no declarado: `git checkout HEAD` a secas conserva la rama con git real, pero `implementer.md:70` dice que equivale a `--detach` | T-06 | pendiente | Lente A (7) |
| 13 | Minor | Docs y espejos EN con plazos viejos: `FLOWS.md:810`/`en/FLOWS.md:808` («3.000 ms»), `INTEROP.md:467`/`en/INTEROP.md:460` y `observability.md:168`/`en/observability.md:171` («2.200 ms» para OpenCode) | T-23 | pendiente | Lente A (8) |
| 14 | Minor | Salidas de rama sin forma de commit: tags sin `tags/`, `FETCH_HEAD`/`ORIG_HEAD`/`MERGE_HEAD`, ramas de remotos distintos de origin/upstream (`fork/main`), SHA de 4-6 caracteres. Con git real sueltan HEAD | T-06 | pendiente | Lente B (3): `:1548,2156,2219` |
| 15 | Minor | `git update-ref refs/heads/<rama> …` mueve ramas (la actual o main) con allow; solo `update-ref HEAD` se deniega | T-06 | pendiente | Lente C (3): `:2259-2282` |
| 16 | Minor | `git rebase <upstream> <rama>` cambia de rama y la reescribe; `git bisect start <malo> <bueno>` suelta HEAD. Ambos allow | T-06 | pendiente | Lente C (4) |
| 17 | Minor | Regresión de fix16: `rama_barata` acepta un `.git` sin `objects/` ni `refs/`, que git no considera repositorio; `ramaPrincipal` falla abierta | T-06 | pendiente | Lente C (5, CWE-436): `:280-281` |
| 18 | Minor | En el worker, el barrido muere por su plazo antes de hacer nada | T-23 | pendiente | Lente D (D17-3) |
| 19 | Minor | El sondeo por PID puede agotar los 60 s si Windows reutiliza el PID | T-23 | pendiente | Lente D (D17-4) |
| 20 | Minor | OpenCode puede pasar de los 20 s del catálogo (3,7 + 8 + 10 = 21,7 s) cuando la confirmación llega a su tope; lo típico son ~14 s | T-23 | pendiente | Lentes A y D (D17-5) |
| 21 | Minor | Los fixtures de `SessionEnd` se miden contra los 800 ms del producto en vez de fijar `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS` en el test | T-23 | pendiente | Lente D (D17-6) |
| 22 | Minor | Rojos de la suite node de Windows sin atribuir (`F001`, `marker`), fuera del diff. Regla del usuario: ningún rojo se acepta | T-23 | pendiente | Lente D; implementer: pasadas A (3 fail) y B (1 fail) |

**Diseño fijado por el orquestador para fix17:**

1. **Re-anclaje general** (gaps 1 y 2). En cada orden simple, cualquier palabra (decodificada, sin mayúsculas, basename, `.exe`) que sea git, un envoltorio de la tabla, una shell (`sh`, `bash`, `dash`, `zsh`, `ksh`, `busybox sh`…) o `eval` abre un sufijo que se analiza **como un segmento nuevo y completo** (sus propias asignaciones, `env -S`/`-C`, `xargs`, `bash -c`), sin heredar el estado de la orden exterior. Dentro de git, los argumentos que git pasa a una shell se analizan como código: `submodule foreach`, `rebase -x/--exec`, `bisect run`, `-c alias.*=!…`, `config alias.*` y cualquier `!` de alias. Ante una forma que no se sabe leer, deny. Si el intento 18 vuelve a encontrar envoltorios forma a forma, la clase se declara límite conocido con el usuario.
2. **Rama por lista blanca** (gaps 11, 12, 14, 15, 16). `checkout`/`switch` con una posicional: allow solo si es la rama actual o, en `checkout`, una ruta existente (o con `--` delante); cualquier otra ref (tag, `FETCH_HEAD`, `fork/main`, SHA corto) → deny. `checkout HEAD` a secas → allow y se corrige `implementer.md:70`. `-B`/`-C`/`--force-create` → deny siempre salvo que el nombre sea la rama actual sin punto de partida. `update-ref refs/heads/*` → deny. `rebase` con 2 posicionales y `bisect start|run|reset <ref>` → deny.
3. **`rama_barata` válida** (gap 17): exige `HEAD` + `objects/` + `refs/` (o `commondir` en worktree); si no, recurre a `current_branch`.
4. **Árbol de procesos de Windows** (gaps 3, 5, 18, 19). Se anota la `CreationDate` del PID raíz al lanzarlo; un hijo solo cuenta si su `CreationDate` ≥ la del padre. El dueño del temporizador hace `taskkill /T /F` con la raíz **viva** primero, y el barrido CIM queda de respaldo con plazo propio que sí actúa. El sondeo de muerte compara PID + `CreationDate`. Test con PID reutilizado (víctima anterior y no descendiente) que sobrevive. El `gap 8` del instalador pasa 5 de 5 con 12 bucles sin tocar la cota de 30 s.
5. **Plazos coherentes** (gaps 4 y 20). Plazo de la consulta = min(listo + límite, tope exterior − 2 s de reserva para la limpieza), sin suelo que pase del SIGKILL; test con codex colgado y worker lento (+2 s) sin huérfanos, también por `/doctor`. OpenCode: arranque + captura + confirmación ≤ 20 s por construcción (la confirmación toma lo que queda).
6. **Tests y arneses** (gaps 6, 10, 21, 22). Cerrar de verdad los gaps 19 y 24 del intento 16; el test de `uninstall` comprueba que deshace lo registrado y el fake de codex no se cuelga; `SessionEnd` con `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS`; `debug-root-cause` sobre `F001` y `marker` hasta arreglarlos.
7. **Traza y docs** (gaps 7, 8, 9, 13). Numerar la desviación de 10 s (o retirarla si el punto 5 la hace innecesaria), corregir valores y comentarios, lista de commits de T-23, declarar el trabajo sin medir, docs y espejos EN.

Tras este ciclo: suite completa (node y pytest en Windows) y réplica Linux sin rojo (petición explícita del usuario), medida emparejada de T-23 con el equipo libre (la hace el orquestador) y verificación dirigida de las cuatro lentes.
