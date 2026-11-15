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
- **Tiempo IA (ejec.)**: est. 0.5h · real 11.42h (0.4h del cierre original estimado + 2.53h medidas en fix5 + 0.78h en fix6 + 1.33h en fix7 + 1.55h en fix8 + 3.22h en fix9 + 1.21h en fix10 + 0.43h en fix11 + 2.11h en fix12 `(medido)`; las ventanas de fix5 a fix12 están compartidas con T-07 y T-23)
- **Archivos**: `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/test_guardrail_check.py`, `agent-kits/shared/test_guardrail_differential.py` (fix5), `tests/test_native_guardrail_dispatch.py`, `docs/agents/implementer.md`, `docs/CONVENTIONS.md` · fix6: `agent-kits/shared/native-guardrail.py`, `hooks/run-hook.mjs`, `hooks/opencode-plugin.js`, `interop/opencode/plugins/custom-agents/index.js` (regenerado), `tests/test_native_guard_failclosed.py` (nuevo), `tests/hook-guard-failclosed.test.mjs` (nuevo), `docs/FLOWS.md`, `docs/en/FLOWS.md` · fix7: `agent-kits/shared/test_guardrail_fix7.py`, `agent-kits/shared/test_guardrail_differential7.py`, `tests/test_native_guard_failclosed7.py`, `tests/native-guard-adapter-failclosed.test.mjs` (nuevos), `docs/INTEROP.md`, `docs/en/INTEROP.md`, `interop/opencode/plugins/custom-agents/index.js` (regenerado), `agent-kits/shared/test_guardrail_differential.py` · fix8: `tests/test_native_guard_scan8.py` y `tests/native-guard-adapter-fix8.test.mjs` y `agent-kits/shared/test_guardrail_fix8.py` (nuevos), `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/native-guardrail.py`, `hooks/run-hook.mjs`, `hooks/opencode-plugin.js`, `interop/opencode/plugins/custom-agents/index.js` (regenerado), `agent-kits/shared/test_guardrail_differential.py`, `agent-kits/shared/test_guardrail_differential7.py`, `tests/test_native_guard_failclosed.py`, `tests/test_graphiti_security.py` (huella del lanzador), `docs/INTEROP.md`, `docs/en/INTEROP.md`, `docs/agents/implementer.md` · fix9: `agent-kits/shared/test_guardrail_fix9.py` y `tests/test_native_guard_parity9.py` y `tests/native-guard-adapter-fix9.test.mjs` (nuevos), `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/native-guardrail.py`, `hooks/opencode-plugin.js`, `interop/opencode/plugins/custom-agents/index.js` (regenerado), `agent-kits/shared/test_guardrail_differential7.py` (BAD9_PARIDAD y LEGIT9), `agent-kits/shared/test_guardrail_fix8.py` (`env -S 'echo "hola'` pasa a denegado), `docs/agents/implementer.md`, `docs/INTEROP.md`, `docs/en/INTEROP.md` · fix10: `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/native-guardrail.py`, `hooks/run-hook.mjs`, `hooks/opencode-plugin.js`, `interop/opencode/plugins/custom-agents/index.js` (regenerado), `agent-kits/shared/test_guardrail_differential7.py`, `agent-kits/shared/test_guardrail_fix10.py` (nuevo), `tests/test_native_guard_parity9.py`, `tests/opencode-realpath-fix10.test.mjs` (nuevo), `tests/native-guard-adapter-fix9.test.mjs`, `tests/test_graphiti_security.py` (huella), `docs/agents/implementer.md`, `docs/INTEROP.md`, `docs/en/INTEROP.md` · fix11: `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/test_guardrail_differential7.py`, `agent-kits/shared/test_guardrail_fix11.py` (nuevo), `hooks/opencode-plugin.js`, `interop/opencode/plugins/custom-agents/index.js` (regenerado), `tests/opencode-realpath-fix11.test.mjs` (nuevo), `docs/agents/implementer.md` · fix12: `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/test_guardrail_fix12.py` (nuevo), `agent-kits/shared/test_guardrail_fix11.py`, `agent-kits/shared/test_guardrail_differential.py`, `agent-kits/shared/test_guardrail_differential7.py`, `docs/agents/implementer.md`
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

**fix1 (revisión de dos lentes, intento 1: gaps 4 y 16)** — clave de medición `plugin-audit-2/T-06-fix1`.

RED: `agent-kits/shared/test_guardrail_check.py -k "pathspec or fuerza_en_un_cluster"` falló con `35 failed, 31 passed`: `git restore ./`, `..`, `../..`, `'*'`, `'**/*'`, `':/*'`, `':/.'`, `':(top)*'`, `':(glob)**'`, `':!src/a.py'`, `"$PWD"`, `"${PWD}"`, `/`, la ruta absoluta de la raíz (con y sin `/`, `/*`), `--pathspec-from-file`, `git checkout -- ./`, `HEAD -- '*'`, `HEAD -- src/..`… devuelven `None` (no se deniegan); y el falso positivo `git checkout -bfeature/y main` se denegaba por la `f` del nombre · 2026-11-11.

GREEN: `_razon_restauracion` ya no compara contra una lista literal: `_abarca_el_arbol` normaliza cada pathspec (magia corta `:/`, `:!`, `:^` y larga `:(top,glob,exclude)`; `.`/`./`/`src/..`; `..` que sale del directorio actual si lo que queda es vacío o comodines; `*`/`**`/`**/*`; `$PWD`, `${PWD}`, `$(pwd)`; ruta absoluta igual o anterior al directorio actual o a `CLAUDE_PROJECT_DIR`, con `C:/x` y `/c/x` unificados), un pathspec de SOLO exclusión se trata como «todo menos x» y `--pathspec-from-file` (cualquier prefijo ≥ `--pathspec-from`) se deniega porque el guardarraíl no ve su contenido; `restore --staged` sigue exento. Gap 16: `_cluster_con_fuerza` recorre el clúster y la letra que consume valor (`b`/`B` en checkout, `c`/`C` en switch) se lleva el resto, así que `-bfeature`/`-cfeature` pasan y `-fb`/`-fc` siguen denegados. Siguen permitidos `checkout <rama> -- <fichero>`, `restore --staged .`, `restore <fichero>`, `restore ../hermana/a.py`, `restore 'src/*.py'`. `pytest -q agent-kits/shared/test_guardrail_check.py agent-kits/shared/test_native_guardrail.py` → `703 passed`. `docs/agents/implementer.md` (línea del guardarraíl) actualizada en la misma tarea.

**fix2 (revisión de dos lentes, intento 2: gap 1)** — clave de medición `plugin-audit-2/T-06-fix2`. Diseño fijado por el orquestador: lista de PERMITIDOS, no más casos sueltos.

RED: `agent-kits/shared/test_guardrail_check.py -k fix2` falló con `28 failed, 108 passed`: `git restore ':'`, `'?*'`, `'?'`, `"$(git rev-parse --show-toplevel)"`, `~+`, `~`, `"$CLAUDE_PROJECT_DIR"`, `"$(realpath .)"`, `git restore . --`, `'src/*.py'`, `:src/a.py`, `../hermana/a.py`, la ruta absoluta y sus gemelas de `checkout --` devuelven `None` (no se deniegan) · 2026-11-12.

GREEN: `_pathspec_permitido` (sustituye a `_abarca_el_arbol`, `_pathspecs_arbol_entero`, `_parte_pathspec`, `_solo_comodines` y `_VAR_PWD`, ya sin uso): un pathspec de `checkout|restore` que toca el árbol pasa solo si es una ruta relativa literal (sin `:` inicial, sin `*?[`, sin `$`/backtick/`~` inicial, no absoluta) y, normalizada contra el directorio actual, queda dentro del proyecto (`CLAUDE_PROJECT_DIR` si contiene al directorio actual; si no, el directorio actual) sin ser el directorio actual, un ancestro ni la raíz. Rutas que salen del directorio actual: `../otro.py` desde un subdirectorio se permite si el resultado sigue dentro del proyecto; `..`, `../..` y cualquier ruta que llegue a la raíz o la rebase se deniegan; desde la raíz, todo `..` sale del proyecto y se deniega. Una `~` a mitad de token (`HEAD~1`) no es expansión de shell y pasa. En `restore` todo argumento que no es opción cuenta como pathspec antes o después de `--` (`git restore . --`); en `checkout` cuentan los de tras `--` y, sin `--` ni `-b/-B/--orphan`, los sueltos (`checkout ':'`, `checkout ~+`); `checkout . --` no se deniega porque ahí `.` es el árbol-ish y git lo rechaza. `restore --staged|-S` sigue exento (solo índice) y `--pathspec-from-file` sigue denegado. Siguen permitidos `checkout <rama>`, `HEAD~1`, `-`, `-b/-B/-bX`, `checkout -b x "$(git rev-parse HEAD)"`, `checkout <rama> -- src/a.py`, `restore src/a.py`, `restore --source=HEAD~1 src/a.py`. Tests previos que chocan con el diseño (pasan de la lista de permitidos a la de denegados; ningún assert de denegación se debilita): `restore 'src/*.py'` (comodín), `:src/a.py`, `':(top)src/a.py'`, `':/src'`, `':!src/a.py' docs/b.md` (magia), la ruta absoluta de `src/a.py` (no relativa) y `../hermana/a.py` (con el directorio actual en la raíz, `..` sale del proyecto); test nuevo con subdirectorio para el `../otro.py` permitido. `pytest -q agent-kits/shared/test_guardrail_check.py agent-kits/shared/test_native_guardrail.py` → `748 passed`. `docs/agents/implementer.md` (línea del guardarraíl) actualizada en la misma tarea.

**fix3 (revisión de dos lentes, intento 3, ciclo final: gaps 1, 3, 4 y 8)** — clave de medición `plugin-audit-2/T-06-fix3`. Diseño fijado por el orquestador, aplicado tal cual. Sin ficheros nuevos en `Archivos`.

RED: `agent-kits/shared/test_guardrail_check.py -k fix3` falló antes del código con `AssertionError` en los 7 casos del gap 1 (`git checkout .\`, `git restore .\`, `git checkout HEAD -- .\`, comilla sin cerrar en `restore`/`checkout --`, `reset --hard HEAD\`, `echo ok; git restore ./\`: `decide` devolvía `None`), `JSONDecodeError: Expecting value` en sus 7 gemelos de punta a punta por el hook (`guardrail-check.py pre-tool`, JSON por stdin: salida vacía = sin deny), `AssertionError` en los casos del gap 3 (`git -C .. restore proj`, `--work-tree`, `--git-dir`, `env -C`, `env --chdir=`, `cd .. && …`, `cd .. ; …`, `pushd`, `(cd .. && …)`, `|| `: `None`), en el mensaje del gap 4 («directorio actual» en vez de «proyecto») y en el gap 8 (`git restore --source "$BASE" src/a.py` denegado por el `$`) · 2026-11-12. (Los totales exactos del rojo no se capturaron: la salida se filtró por tipo de error.)

GREEN: Gap 1: `_segmentos` devuelve `(segmentos, incompleta)` y conserva el último segmento con lo leído (escape final, comilla sin cerrar); si la orden es incompleta y ese segmento es una orden `git` de las que el guardarraíl ya trata como destructivas (`checkout|switch|restore|reset|clean|stash|branch|update-ref|push`), se deniega con «orden incompleta»; las órdenes sin git (`echo "x`, `ls src\`) y `git status\` no se deniegan. Los paréntesis sin comillas pasan a separar órdenes (`(cd x && git restore f)`, `$(git restore .)`). Gap 3: falla cerrado — `restore`/`checkout` con pathspec se deniega con «cambia la base» si hay `git -C`, `--work-tree`, `--git-dir` (también `=`), `env -C`/`--chdir`, o un `cd`/`pushd`/`popd` previo en la misma orden; `git -C <dir> status|log|diff`, `restore --staged` y `cd sub && git status` siguen permitidos. Gap 4: el mensaje de denegación dice «dentro del proyecto … sin ser el propio directorio, un ancestro ni la raíz» (lo implementado pasa a ser el diseño) y `docs/agents/implementer.md` lo recoge junto con los gaps 1, 3 y 8. Gap 8: el valor separado de `-s`/`--source` (y de un clúster que acaba en `s`, p. ej. `-qs`) no cuenta como pathspec; el pathspec real sigue validándose (`restore --source "$BASE" .` se deniega). `pytest -q agent-kits/shared/test_guardrail_check.py agent-kits/shared/test_native_guardrail.py tests/test_native_guardrail_dispatch.py` → `808 passed`.

**fix4 (revisión de dos lentes, intento 4, último ciclo de la fase 1: gaps 1, 3 y 4)** — clave de medición `plugin-audit-2/T-06-fix4`. Diseño estructural fijado por el orquestador, aplicado tal cual; sin ficheros nuevos en `Archivos` (`docs/agents/implementer.md` ya estaba).

RED: `agent-kits/shared/test_guardrail_check.py -k fix4` falló antes del código con `27 failed, 12 passed, 567 deselected` · 2026-11-12: los 7 casos de heredoc (`cat <<EOF⏎it's⏎EOF⏎git restore .`, `git commit -F - <<'EOF'⏎don't⏎EOF⏎git checkout .`, delimitador entrecomillado y con `<<-`, `bash <<EOF⏎git restore .⏎EOF`, …) y sus gemelos de punta a punta por el hook devolvían `None`/salida vacía (el apóstrofo del cuerpo abría una «comilla» que se tragaba lo siguiente); 17 formas de cambio de base (`A=1 env -C ..`, `command cd ..`, `builtin cd ..`, `{ cd ..; … }`, `if …; then cd ..; fi`, `time cd ..`, `! cd ..`, `cd .. && bash -c '…'`, `cd .. && eval '…'`, `cd`, `cd -`, `cd $X`, `popd`, …) sin deny; el `cd "<propio directorio>" && git restore src/a.py` se denegaba como cambio de base (gap 4).

GREEN: `pytest -q agent-kits/shared/test_guardrail_check.py` → todo passed (606 en total, ya con los 39 de fix4; cifra final en la tabla de la réplica Linux de T-23). Diseño aplicado: (1) `_segmentos` reconoce `<<DELIM`, `<<-DELIM`, `<<'DELIM'` y `<<"DELIM"` (no `<<<`) y, al llegar al salto de línea de la orden, salta el cuerpo hasta la línea del delimitador (`_saltar_heredocs`): el cuerpo es datos; un heredoc sin cierre marca `incompleta` (la regla del gap 1 del intento 3 deniega entonces cualquier `git` destructivo del último segmento). Única extensión al diseño, para no abrir un hueco nuevo: si la orden que lleva el heredoc es una shell (`bash <<EOF`, `sh <<'EOF'`), su cuerpo SÍ se ejecuta y se añade como segmento `bash -c <cuerpo>` para que se analice. (2) `_cambia_base_en(segmentos)` mira CADA token de CADA segmento (no solo el primero) y marca cambio de base ante `cd|pushd|popd|chdir`, `env -C|--chdir` o `git -C|--work-tree|--git-dir` en cualquier posición; `check_git` lo calcula una vez por orden y lo pasa por el parámetro `_base` a la recursión de `bash -c`/`sh -c`/`eval`, que lo hereda. Excepción (gap 4): un `cd`/`chdir` cuyo destino, resuelto con `realpath` contra el directorio de trabajo del hook (también la forma `/c/…` de Git Bash en Windows), es el propio directorio no cuenta; un destino que no se puede resolver sin ejecutar (`$X`, `~`, `-`, backtick, comodines) o `cd` sin argumento sí cuenta. `docs/agents/implementer.md` describe los dos cambios. Las sondas de los revisores (`vf/probe.py`, repo `m`) reproducen lo mismo: las formas con cambio de base deniegan y las de `-C <dir> status|log|diff` y `restore --staged` siguen permitidas.

**fix5 (revisión de dos lentes, intento 5: gaps 1, 2, 3, 4, 6, 7 y 10)** — clave de medición `plugin-audit-2/T-06-fix5`. Diseño fijado por el orquestador (puntos 1-8). Se añade a `Archivos`: `agent-kits/shared/test_guardrail_differential.py` (corpus diferencial contra bash real, punto 6 y prueba de punta a punta por el lanzador, punto 5).

RED: `agent-kits/shared/test_guardrail_check.py -k fix5` falló antes del código con `31 failed` · 2026-11-12 (heredoc aritmético `$((1<<2))`/`(( … ))`, here-string `<<<`, delimitador `<<\EOF`/`<<E"OF"`, `env bash <<EOF`, `bash <<EOF 2>&1`, `| tee`, `| bash; true`, `eval "$(cat <<'EOF' …)"`, `. /dev/stdin <<EOF`, `$(…)` y backticks en cuerpo sin comillas y dentro de `"…"`, comilla doble impar del gap 6, `git status\` incompleto con git sin deniego, tope de entrada y anidamiento profundo) y `agent-kits/shared/test_guardrail_differential.py -k "bad_ or legit"` con `67 failed` (el corpus diferencial: las sondas de las lentes A, B, C y D de los intentos 4 y 5 salían ALLOW); la propiedad «si el guardarraíl permite, bash no toca el centinela» falló con `AssertionError` y 100+ órdenes que bash real SÍ ejecutó (`restore`, `push --force`, `reset --hard`, `checkout -- .`) tras un ALLOW; `-k payload` (lanzador `run-hook.mjs` con el payload de 30 KB `echo cd .`×6000 + `git push --force`) falló con `KeyError: 'hookSpecificOutput'` (el lanzador no emite deny: plazo agotado, `role guard unavailable`).

**Estado fix5 (cierre anticipado por orden del usuario; ciclo NO terminado, tarea `en-progreso`)** — hecho: puntos 1 (invariante de cierre: orden incompleta con `git` o cambio de base se deniega entera; aviso: se deniega con cualquier `git`, de modo que `git status\` y `git log "x` pasan a deny y su test se actualizó), 2 (heredoc como datos solo con delimitador citado + cierra + sin intérprete; REBATE parcial: con delimitador sin comillas el cuerpo es texto salvo sus `$(…)` y backticks, que se analizan, en vez de analizarlo entero, porque bash no trata las comillas del cuerpo y así `git commit -F - <<EOF⏎don't…` sigue permitido; `.` solo cuenta como intérprete en posición de programa, porque `git add .` es el caso normal de un commit con heredoc), 3 (`<<<` y `<<` aritmético no son heredoc; delimitador sin comillas/barras; nota: `let x<<=2` SÍ es heredoc en bash 5.2, medido, no aritmética), 4 (recorrido lineal, `realpath` memoizado con tope 64, cambio de base solo en posición de programa, punto 8.7 cerrado), 5 (tope 4.000 palabras / 16 KB visibles / 256 KB en bruto dentro del guard; prueba de punta a punta por `run-hook.mjs` con 30 KB: deny en ~1 s en Windows, `serie`), 6 (corpus diferencial `test_guardrail_differential.py`: 72 BAD ×2 órdenes + 25 LEGIT + paridad contra bash real + propiedad «permite ⇒ centinela intacto»), y el gap 6 (comillas impares en `"$(cat <<'EOF'…)"`). `pytest agent-kits/shared/test_guardrail_check.py` 641 passed; `test_guardrail_differential.py -k "bad_ or legit"` 172 passed y `-k propiedad` verde; `export-interop --check` 88 al día. Falta: GREEN formal con la salida pegada y la medición `close` de `T-06-fix5`, `ledger-lint`/`scope-check --base 57fb054`/`lint_plugin`, la réplica Linux completa (corpus contra bash Linux incluido) y la verificación dirigida de las cuatro lentes. Commits: RED `64b6fd4`, código `d30b9d5`.

**Cierre fix5 (ciclo fix5b, 2026-11-13)** — commits: RED `2c3430b`, código `f5ae694`. Rebate del punto 2 ACEPTADO por el orquestador (delimitador sin comillas: solo se analizan `$(…)`/backticks del cuerpo, anidados incluidos; `.` como intérprete solo en posición de programa) con la condición de que con un intérprete o envoltorio en CUALQUIER posición el cuerpo se analice ENTERO: el corpus diferencial (`test_guardrail_differential.py`) añade 13 casos BAD para cada combinación —sin comillas + `eval "$(cat <<EOF …)"`, `| sh`, `| sh -s`, `bash <<EOF` con `$(echo {D})`; `$({D})` anidado en `"$(…)"`, en backticks y dentro de `$(…)` de `$(…)`; backticks anidados y escapados— y, al ejecutarlo contra bash real, encontró UN agujero real: con un intérprete y un heredoc sin comillas bash ejecuta el cuerpo YA expandido (`bash <<EOF⏎$(echo git restore .)⏎EOF`) y el guardarraíl lo permitía; ahora una sustitución en el cuerpo con intérprete deja la orden `incompleta` (se deniega entera si lleva `git` o un cambio de base). Además la prueba del lanzador con 30 KB mide el plazo contra la MISMA ruta con una orden mínima (`max(1,5 s, 2×base+1 s)`; antes `< 1,5 s` absoluto dio 3,3-5,5 s con la máquina cargada) y las capturas de subproceso del corpus llevan `encoding=` (la réplica Linux las halló en `test_console_encoding`), y un `\E` inválido de un literal de `test_guardrail_check.py` pasa a `\\E`.

GREEN: `pytest -q agent-kits/shared/test_guardrail_check.py agent-kits/shared/test_guardrail_differential.py tests/test_native_guardrail_dispatch.py` → `939 passed in 166.29s` (Windows, 2026-11-13); mismas suites en la réplica Linux completa (paso paralelo `11812 passed, 0 failed`, ver T-23); `python scripts/export-interop.py --check` → `88 ficheros al día`. Medición `close` de `plugin-audit-2/T-06-fix5`: `2.53 h` IA medidas, 29,73 € (ventana compartida con T-07 y T-23: no sumar). Estado → `completado`.


RED: `agent-kits/shared/test_guardrail_differential.py -k bad_ (fix5b, commit 2c3430b)` falló con 2 failed: bash <<EOF con $(echo git restore .) y con $(echo git push --force …) en el cuerpo se permitia (bash ejecuta el resultado de la sustitucion); los otros 13 casos nuevos (sin comillas + eval, | sh, anidados en "$(…)" y backticks) ya salian DENY · 2026-11-13.

**fix6 (revisión de dos lentes, intento 6: gaps 1-6, 8-12 y 16; cambio de modelo decidido por el usuario el 2026-11-13)** — clave de medición `plugin-audit-2/T-06-fix6`. Diseño fijado (puntos 1-8): el guardarraíl FALLA CERRADO para el rol protegido en el lanzador (`hooks/run-hook.mjs`, `native-guardrail.py`, puente de OpenCode), el cuerpo de heredoc se analiza SIEMPRE salvo dos formas exactas de `git commit`, envoltorios y cambio de base en `eval`/`source`, `_aritmetica` lineal y recorte barato previo, subcomandos del gap 11, y el corpus diferencial con TODAS las sondas del intento 6 (BAD/LEGIT/LIMITE). Se añaden a `Archivos`: `hooks/run-hook.mjs`, `hooks/opencode-plugin.js`, `agent-kits/shared/native-guardrail.py`, `tests/test_native_guard_failclosed.py` (nuevo), `interop/**` (regenerado) y los manifiestos con hash que dependan de ellos.

RED: `agent-kits/shared/test_guardrail_differential.py -k "bad6 or legit6 or aritmetica or recorte or larga or explica or forma_exacta or fuera_de_la_forma"` y `tests/test_native_guard_failclosed.py` fallaron antes del código · 2026-11-13: las sondas del intento 6 (heredoc aritmético `$[1<<2]`, `$(( "1" << 2 ))`, `${x:-<<'E'}`, ANSI-C `$'\''`, `$BASH <<'EOF'`, `EO\⏎F`, `time -p`/`nice`/`timeout`/`stdbuf`/`env -S`, `eval cd ..; git restore`, redirecciones al principio, `function f {…}`, CR como espacio, `reset --keep`, `checkout -`) se permitían; los LEGIT con `time`/`timeout` previos y heredoc con apóstrofo daban falso deny; `_aritmetica` era cuadrática; y la entrada > 64 KB y el plazo agotado devolvían `continue` («role guard unavailable») para el implementer.

GREEN: commits RED `2652b0c`, código `1cf29b3`, `c23d80b`, `f823f0d`. Diseño fijado aplicado tal cual (no hubo imposibles; las interpretaciones están al final):
1. **Falla cerrado para el rol protegido.** `hooks/run-hook.mjs` conoce el rol (`protectedRoleOf`: del payload completo o, si está truncado, de la primera clave `agent_type`/`agent` de su prefijo, con la misma política y el mismo mapa de roles de ADR-023) y, en plazo agotado, entrada > 64 KiB, error, salida inválida, `evaluator-unavailable` o intérprete ausente, DENIEGA para `implementer`/`architect` y conserva `continue` para el resto. `native-guardrail.py` hace lo mismo con `input-too-large` (`_role_of_prefix`). El puente de OpenCode (`hooks/opencode-plugin.js`) lanza un error de herramienta cuando el agente es protegido y el guard no entrega decisión; Codex y Claude Code pasan por el mismo lanzador. `interop/opencode/plugins/custom-agents/index.js` regenerado: `python scripts/export-interop.py --check` → `88 ficheros al día`. Recorte barato: por encima de 16 KB o 4.000 palabras (orden completa) se deniega ANTES de tokenizar si el texto contiene `git` (sin mayúsculas) o un cambio de base; `_aritmetica` es lineal (tabla de paréntesis por orden + búsqueda binaria de marcas). Cierra los gaps 1, 6 (plazo) y 10.
2. **Cuerpo de heredoc SIEMPRE analizado**, sin lista de intérpretes ni reglas de salto ni detección de `<<` aritmético; solo las dos formas exactas de `git commit` lo saltan (`_quitar_mensajes_de_commit`). Cierra los gaps 2, 3, 4 y 12. El mensaje de deny de un heredoc explica la salida (`herramienta de edición` + `git commit -F <fichero>`).
3. **Envoltorios** (`timeout`, `nice`, `stdbuf`, `time [-p]`, `setsid`, `sudo`, `env [-S]`, `xargs`, `ionice`, `nohup`, `command`, `exec`, `builtin`) con una sola implementación compartida por `_literal_invocation` y `_posicion_programa`; redirecciones iniciales (`2>&1 git …`, `&>f`), `function f {`, `$SHELL -c`; subcomandos del gap 11 (`reset --keep|--merge`, `checkout-index -f`, `read-tree -u|--reset`, `rm -f`, `worktree remove -f`, `checkout -|@{-1}|refs/heads/master|origin/main|master^0|MAIN`).
4. **Cambio de base** dentro de `eval` (se mira su contenido) y `source`/`.` con fichero (se asume cambio); funciones y `. <(…)` ya estaban aplanados en los segmentos. Cierra el gap 5.
5. **Modelo de amenaza** en `docs/agents/implementer.md` (nueva sección «Modelo de amenaza» y «Falla cerrado»), en `docs/FLOWS.md` y su espejo `docs/en/FLOWS.md`; `docs/CONVENTIONS.md` no cambia (no describe esta regla).
6. **Corpus diferencial**: `agent-kits/shared/test_guardrail_differential.py` pasa de 281 a 573 casos con TODAS las sondas del intento 6 (`lb6`, `lc6`, `la6`, `i6`): `BAD6` (denegadas; con paridad contra bash real salvo `SIN_PARIDAD_6`), `LIMITE` (gap 8: 22 indirecciones que bash ejecuta y el guardarraíl NO ve, con test que lo fija en las dos direcciones) y `LEGIT6` (las 14 órdenes típicas de la lente B y las de uso normal). Los casos de fix5 que contradecían el modelo se movieron a `FALSO_DENY_ACEPTADO` (precio aceptado) o a `LIMITE`.
8. **Minor**: 9 (el CR es un carácter normal; una orden con CR y `git` se deniega), 11, 12 y 16 (fila «Total» de la réplica de fix5b corregida: 12.379 / 0 / 92 / 1.032 s; `Cerrada` de T-23 quitado; deuda de orden anotada abajo; la cota del test de 30 KB vuelve a ser estrecha: `max(1,5 s, base + 0,75 s)`).

Además del diseño, para que las sondas BAD6 cerraran de verdad: los backticks se leen como bash (se quitan las barras de escape del contenido y este se lee aparte, así que una sustitución anidada con barra-backtick sigue viéndose; antes lo cubría `_expansiones`), `$'…'` ANSI-C y `$"…"` (la `$` no es de la palabra), `2>&1`/`&>f` como una palabra (el `&` ya no separaba órdenes dentro de una redirección) y la palabra `git` dentro de una aritmética `$(( … ))` la hace leer como subshell.

Verificación local (Windows, 2026-11-13): `pytest -q agent-kits/shared/test_guardrail_check.py agent-kits/shared/test_guardrail_differential.py agent-kits/shared/test_native_guardrail.py agent-kits/shared/test_git_verification.py tests/test_native_guardrail_dispatch.py tests/test_native_guard_launcher.py tests/test_native_guard_failclosed.py tests/test_native_prefilter_parity.py tests/test_export_interop.py tests/test_graphiti_security.py tests/test_agent_activity_store.py skills/code-health/scripts tests/test_redact_fix3.py -n 2 -m "not serie"` → `3039 passed, 1 skipped` más los 2 pines de hash que se actualizaron (`_LAUNCHER_NODE_HASH`, revisado: solo lee el mapa de roles local); `node --test tests/hook-guard-delivery.test.mjs` → `75 pass, 0 fail`; `node --test tests/hook-guard-failclosed.test.mjs` → `3 pass`. Cota de las órdenes hostiles (en proceso, Windows): `"(" * 8000 + push -f` 4,6 s → < 0,05 s; `echo $(("((")); × 2000` → < 0,2 s; `export GIT_0…×3000 + "g"it` (44 KB) → recorte inmediato.

**Interpretaciones y rebates (declarados, ninguno sustituye el diseño en silencio):**
- *Formas exactas, lo que las precede.* El diseño dice «precedida de `git add …` / `cd <propio directorio>` y unida con `&&`». Las 14 órdenes típicas de la lente B, que el punto 6 exige como LEGIT, incluyen `timeout 600 python -m pytest -q && git commit -am "$(cat <<'EOF' …)"`, `export X=1; … && git add -A && git commit -F - <<'EOF' …` y `time pytest && git commit …` (el gap 12). Se aplicó la forma más segura que las admite: la forma exacta puede ir tras CUALQUIER sentencia (`&&`, `||`, `;`, salto de línea) siempre que lo anterior se lea entero y sin heredocs, y esas órdenes se analizan con normalidad; lo que sigue empieza en un separador.
- *`input-unrecognized` no falla cerrado.* El lanzador deniega para el rol protegido cuando el evaluador revienta (`evaluator-unavailable`), pero conserva `continue` + diagnóstico para `input-unrecognized` (esquema de herramienta no reconocido): es el contrato documentado de `native-guardrail.py` (cabecera) y de `tests/hook-guard-delivery.test.mjs` («evaluator diagnostic reaches its native consumer»).
- *Identidad de un payload truncado.* Con más de 64 KiB solo se ve el prefijo: el rol sale de la primera clave `agent_type`/`agent` que contenga; si la clave cae más allá del prefijo, no se puede atribuir y la orden continúa (Claude Code y OpenCode la ponen antes de `tool_input`).
- *Dos casos de fix5b cambian de lista.* `bash <<EOF⏎$(echo git restore .)⏎EOF` pasa de BAD a `LIMITE`: es una indirección (el resultado de una sustitución) que `cdcda09`, la referencia del diseño, tampoco veía. `awk 'BEGIN{while((getline l)>0) system(l)}' <<'EOF'⏎git reset --hard⏎EOF` pasa de límite a BAD: su cuerpo ahora se analiza. El caso `ex <<'EOF'⏎!git reset --hard⏎EOF` se retiró del corpus: depende de que `ex` esté instalado (la réplica Linux lo detectó: bash no ejecutaba nada).
- *Deuda de orden anotada (gap 16).* El RED de `77d7ec9` se comiteó después del código y `tests/hook-guard-failclosed.test.mjs` (comportamiento del puente de OpenCode) se añadió junto al código: su RED lo cubre el test de fuente `test_el_plugin_de_opencode_deniega_si_el_guard_no_decide_para_el_rol_protegido` (rojo en `2652b0c`). Sin acción retroactiva.


**fix7 (revisión de dos lentes, intento 7: gaps 1-14; el modelo de amenaza del usuario no se reabre)** — clave de medición `plugin-audit-2/T-06-fix7`. Se añaden a `Archivos`: `agent-kits/shared/test_guardrail_fix7.py`, `agent-kits/shared/test_guardrail_differential7.py`, `tests/test_native_guard_failclosed7.py`, `tests/native-guard-adapter-failclosed.test.mjs` (todos nuevos), `docs/INTEROP.md`, `docs/en/INTEROP.md`, `interop/opencode/plugins/custom-agents/index.js` (regenerado) y `agent-kits/shared/test_guardrail_differential.py` (xargs de LIMITE a BAD6, `serie` fuera de los 3 hostiles).

RED: `agent-kits/shared/test_guardrail_fix7.py` (67 failed, 55 passed), `agent-kits/shared/test_guardrail_differential7.py -k "bad7 or legit7 or falso"` (81 failed, 96 passed), `tests/test_native_guard_failclosed7.py` (12 failed, 4 passed) y `node --test tests/native-guard-adapter-failclosed.test.mjs` (1 fail: `Missing expected rejection: custom-agents-implementer without a session id`) fallaron antes del código, commit RED `1481584` · 2026-11-14: la forma exacta con `D)`, tras `#` y 15 KB de formas (`commit-encadenado` y `formas-con-heredoc-previo` por encima de 0,3 s), `env -S 'git -C .. restore a.txt'`, `timeout --kill-after 5 30`, `--signal KILL`, `nice --adjustment 5`, `stdbuf -o L`, `sudo --user root`, `flock`, `xargs -I{} git restore {}`, `bash -c -- '…'`, `$$'\'`, `\>&`, `git checkout @{-2}|origin/HEAD`, `git switch --detach`, `source .venv/bin/activate && git restore src/a.py` (falso deny) y la clave del rol tras `tool_input` con más de 64 KiB se permitían (o fallaban en el sentido contrario).

GREEN: diseño del orquestador aplicado punto a punto (no hubo imposibles; las interpretaciones están abajo):
1. **Lista blanca a prueba de bash** (gaps 1, 2 y 11). `_quitar_mensajes_de_commit` ya no usa `finditer` con `_OPCIONES`: UNA pasada del tokenizador (`_leer` anota en `st.inicios` cada palabra `g…` que empieza una sentencia de nivel superior, fuera de comentario, comilla, heredoc y sustitución) da las posiciones; la forma se lee palabra a palabra en SU línea (`_forma_en`, sin retroceso) y su cuerpo con `_fin_de_forma`: no vale si alguna línea del cuerpo, sin tabuladores iniciales, EMPIEZA por el delimitador sin ser el cierre exacto (`D)`, `D;`, `D x`). Con el tokenizador real, `true # ok; git commit …` ya no es una forma (el `#` es un comentario). Se mantiene «no hay otro heredoc antes» (contador de cuerpos) y «lo que precede en su línea termina en `&&`, `||`, `;` o salto»; solo se intentan 64 cabeceras (`_MAX_FORMAS`). Hostiles de 16 KB: `formas-seguidas-16k`, `formas-tras-punto-y-coma`, `formas-sin-cierre`, `formas-con-heredoc-previo`, `commit-encadenado`, `commit-m-encadenado` por debajo de 0,3 s de CPU (`process_time`). Los comentarios «nunca agota el plazo» se sustituyen por lo que de verdad se cumple.
2. **Envoltorios con una sola implementación** (gaps 3, 7 y 9). `_desenvuelve` (nueva) la usan `_check_git` y `_cambia_base_en`; `_posicion_programa` desaparece y `_literal_invocation` es un envoltorio fino. `env -S` (también `-iS`, `--split-string=`) sustituye sus palabras en `toks`, así que su cambio de base y su `git` se ven. Tabla `_OPCIONES_ENVOLTORIO` por programa (cortas con valor, largas con valor, banderas, valor opcional pegado) con prefijos únicos de opciones largas: `timeout --kill-after/--signal`, `nice --adjustment/-N`, `stdbuf -i/-o/-e`, `sudo -u/--user/-g/-D…`, `xargs -a/-I/-n/…`, `ionice`, `setsid`, `flock [-w N] fichero` (nuevo en `_ENVOLTORIOS`; `flock … -c 'cadena'` es opción desconocida). Una opción DESCONOCIDA de un envoltorio detiene el desenvuelto y, en un segmento con `git`, se deniega («opción … de un envoltorio»); `command -v/-V` no cuenta (consulta, no ejecuta). `bash -c -- 'git …'` salta el `--` en `_subcomandos_shell`.
3. **`xargs` y rutas desconocidas** (gap 4): `_desenvuelve` informa de si pasó por `xargs`; `xargs … git restore|checkout|reset|clean|rm|checkout-index|read-tree` se deniega siempre (también con `-I{}` y `-r`), con un mensaje que lo nombra (mismo caso que `--pathspec-from-file`). `git stash` se deja fuera a propósito (recuperable).
4. **Regresiones del tokenizador** (gaps 5 y 6): `$$` es el PID y su segunda `$` no abre `$'…'`/`$"…"`; `&` solo es parte de una redirección si el `<`/`>` anterior no estaba escapado ni entrecomillado (`ult_redir`).
5. **Rama protegida** (gap 8): `checkout`/`switch` a `@{-N}` (cualquier N), a una ref remota (`origin/…`, `upstream/…`, `refs/remotes/…`) o con `--detach`/`-d` se deniega desde una rama de trabajo, salvo con `-b|-B|-c|-C|-t|--track` (crean la rama).
6. **Fallo cerrado completo** (gap 10): (a) con más de 64 KiB la clave del rol se busca en TODO el flujo con un escáner de regex lineal acotado a 16 MiB (`_role_of_stream` en `native-guardrail.py`; `protectedRoleOf` y `readGuardInput` en `hooks/run-hook.mjs`, que ahora retiene hasta 16 MiB y, con un rol protegido y entrada > 64 KiB, deniega sin arrancar el hijo); (b) `evaluate` separa lo que solo es validación del esquema (`input-unrecognized`) de cualquier excepción del evaluador (`evaluator-unavailable`, también la lectura de la config); (c) el puente de OpenCode usa `locate()` y lanza si el proyecto no se puede resolver (ver interpretación 1). Interop regenerado: `python scripts/export-interop.py --check` → `88 ficheros al día`.
7. **`source`/`.`** (gap 12): un fichero normal ya no cuenta como cambio de base (límite conocido, en `docs/agents/implementer.md`); `/dev/…`, `/proc/…`, `<(…)` y `-` sí, y el heredoc se sigue analizando. El mensaje de deny de la base nombra `eval` y `source <(…)`.
8. **Documentación y ledger** (gaps 13 y 14): `docs/FLOWS.md` §6c (cita y mermaid) y `docs/en/FLOWS.md`, `docs/INTEROP.md` y `docs/en/INTEROP.md` dicen fallo cerrado para el rol protegido; `docs/agents/implementer.md` (`git checkout -` ya no figura como permitido; nuevas reglas de la forma exacta, envoltorios, `xargs`, rama, `source`, fallo cerrado); el texto de deny por más de 64 KiB deja de recomendar «write files with the edit tool» (`native-guardrail.py` y el lanzador: «send a smaller payload: split the command, or the file content, into several shorter operations»).
11. **Corpus** (`test_guardrail_differential7.py`): `BAD7` (con paridad contra bash real salvo `SIN_PARIDAD_7`), `LEGIT7`, `LIMITE7` y `FALSO_DENY_ACEPTADO_7` con las sondas de las lentes A, B, C y D (`la7`, `lb7`, `lc7`, `ld7`). `echo --hard | xargs git reset` pasa de `LIMITE` a `BAD6` en el corpus de fix6 (se cubre ahora).

**Interpretaciones y rebates (declarados, ninguno sustituye el diseño en silencio):**
- *i1 — punto 6(c): `project()` nulo.* `project()` devuelve `null` por tres causas distintas: sin `sessionID`/plugin abortado, sesión sin ubicación y sesión de OTRA ubicación conocida. El diseño pide lanzar siempre con un rol protegido, pero `tests/native-guard-adapter.test.mjs:66-68` («skips foreign sessions») fija que una sesión de otra ubicación conocida NO se guarda (el plugin solo gobierna su proyecto; `hooks/opencode-plugin.js`, comentario «Session APIs may expose other locations»). Se aplicó lo que cumple las dos cosas: `locate()` distingue `{directory}`, `{foreign: true}` y `{}`; solo `{}` (no se puede saber el proyecto) lanza para un rol protegido. Tests: `tests/native-guard-adapter-failclosed.test.mjs` (los dos casos).
- *i2 — punto 6(a): dónde se busca la clave.* El lanzador entregaba al hijo como mucho 64 KiB + 1 B, así que buscarla en el hijo no basta: el lanzador retiene hasta 16 MiB, busca la clave con la misma regex y, con rol protegido y entrada > 64 KiB, emite el deny sin arrancar el hijo (el motivo dice «input over 64 KiB»). `native-guardrail.py` hace la misma búsqueda sobre su propio stdin (uso directo). Una clave forjada dentro de una cadena JSON no puede coincidir (las comillas van escapadas; `test_a_una_clave_falsificada_dentro_de_una_cadena_no_elige_el_rol`); una clave repetida en un objeto anidado solo puede endurecer el guard.
- *i3 — punto 7: qué cuenta como `source` visible.* Además de `/dev/stdin` y `<(…)` (token `<`), cuentan `/dev/…`, `/proc/…` y `-`; el heredoc se analiza siempre por el cuerpo.
- *i4 — punto 1(b) aplicado con el tokenizador, no con la heurística conservadora.* El diseño admite «`#` sin comillas en la última línea de `previo`» como caso conservador; se usó la forma exacta («según el tokenizador real»), que da el mismo resultado en las sondas y también cubre comentarios de líneas anteriores sin un falso deny.
- *i5 — corpus.* `env -iS '…'` solo está en las pruebas unitarias (`env -i` vacía `PATH` y bash no encuentra `git`); `env -S 'git --work-tree=.. restore b.txt'`, `sudo`, `xargs -0`, `git rm -rf` y `nice {D}` (sin argumentos se cuelga el `nice` de Git Bash) están en `SIN_PARIDAD_7`: se deniegan igual pero no tienen efecto reproducible en el repo de prueba.
- *i6 — gap 14: assert relajado de `test_guardrail_check.py:962`.* `razon and "descarta" in razon` pasó a `razon` en fix6 (`test_fix4_gap1_heredoc_no_traga_lo_que_sigue`): desde fix6 el cuerpo del heredoc se analiza siempre y el deny de esas órdenes viene de la propia orden destructiva o de la invariante de cierre («orden incompleta»), no solo de la razón de restauración. Queda anotado aquí; la aserción relajada solo exige el deny.
- *i7 — gap 16 (paso serie).* Las dos pruebas de plazo con `sleep` (`test_plazo_agotado_se_deniega_para_el_rol_protegido`) y los 3 hostiles por el lanzador pasan al paso paralelo (el hijo duerme 120 s y la cota es 100 s: la carga de `-n auto` no la acerca). `test_payload_de_30kb_por_el_lanzador_se_deniega_en_menos_de_1_5_s` SIGUE en serie: lleva una aserción de tiempo de pared (`max(1,5 s, base + 0,75 s)`) que la carga ajena rompería.

**fix8 (revisión de dos lentes, intento 8: gaps 1-14; el modelo de amenaza del usuario no se reabre)** — claves de medición `plugin-audit-2/T-06-fix8`, `T-07-fix8` y `T-23-fix8` (abiertas antes del RED).

RED: `test_guardrail_fix8.py` + `test_journal_io_deadline.py` (29 failed, 30 passed), `tests/test_native_guard_scan8.py` (8 failed, 2 passed), `node --test tests/native-guard-adapter-fix8.test.mjs` (3 fail, 2 pass) y `tests/test_redact_fix3.py -k fix8` (3 failed, 1 passed) fallaron antes del código · commit RED `ccb914b` · 2026-11-14.

GREEN: diseño del orquestador aplicado punto a punto (sin imposibles; interpretaciones abajo; commits `3bc278b` y `272c284`):
1. **`xargs` heredado** (gaps 1 y 2, punto 1): `check_git` recibe `_xargs` y la marca «rutas por stdin» de `_desenvuelve` se hereda al recursar en `sh|bash -c`/`eval` (sigue dentro de `env -S`): `xargs -I{} sh -c 'git restore {}'` y sus variantes, con o sin `{}`, se deniegan. `--replace`, `--eof` y `--max-lines` pasan a `_LARGAS_OPCIONALES` (valor solo pegado con `=`): `xargs --replace git restore {}` se deniega y `xargs --replace echo {}` sigue permitido. Una opción larga desconocida con git ya se denegaba.
2. **`env -S` con shlex** (gap 4, punto 3): `_trocea_s` usa `shlex.split(posix=True)`; las 4 formas del gap se deniegan y un valor ilegible es opción desconocida (deny con git). Hostil de 11,7 KB: 0,14 s → < 0,02 s de CPU.
3. **Escáner sin tope** (gap 5, punto 4): `_role_scanner`/`_role_of_stream` (`native-guardrail.py`) y `makeRoleScanner`/`readGuardInput` (`run-hook.mjs`): ventana deslizante de 1 KiB, memoria constante y sin tope; el lanzador solo retiene 64 KiB + 1 B para el hijo. 17 MiB con la clave al final: deny para `implementer` y `architect` (Claude y OpenCode, por el lanzador y por `native-guardrail.py`) y `continue` para `qa`. Huella del lanzador actualizada en `tests/test_graphiti_security.py`.
4. **OpenCode** (gap 6, punto 5): `canonical()` (`realpathSync.native`; minúsculas en win32 y darwin); un `workspaceID` presente en un solo lado no hace la sesión ajena, dos distintos sí. Interop regenerado: `export-interop.py --check` → `88 ficheros al día`.
5. **Plazo de punta a punta** (gap 3, punto 2): `test_plazo_agotado_se_deniega_para_el_rol_protegido` vuelve al paso SERIE con `dt < timeout de hooks.json − 1` (9 s, leído del fichero); mide 5,9 s (claude) y 6,3 s (opencode). No se relajó.
6. **Corpus y documentación** (gaps 7, 8, 9 y 12, puntos 6 y 8): INTEROP ES/EN corregidos (con prueba); las sondas de `lc7` (b51-b79, k84-k103, w23, w25-w28, w32, w35-w39) y las 24 de `lb7/legit2.py` clasificadas por su ejecución real: 38 BAD con paridad, 19 sin paridad, 23 LEGIT, 1 LIMITE (`trap 'cd ..' DEBUG`, ya en el modelo de amenaza de `docs/agents/implementer.md`) y 3 falsos deny (`<<"EOF"`, `<<EOF`, `<<'EOF-1'`); `nice {D}` sale de `SIN_PARIDAD_7` (BAD6 lo ejecuta con paridad); `_estado_plantilla` y `_tiene` con caché.

**Interpretaciones y rebates de fix8** (ninguno sustituye el diseño en silencio):
- *i1 — punto 3.* En vez de reescribir la lista de palabras sin rebanar, se acota: 4 troceos por invocación y 2.048 caracteres por valor (`shlex` va carácter a carácter); lo que pasa de ahí es opción desconocida (deny con git). Cubre las 4 formas y el hostil.
- *i2 — punto 5.* El enlace al proyecto se prueba con una unión (`junction`) en Windows; el nombre 8.3 y las mayúsculas de macOS no se pueden probar aquí (sin runtime).
- *i3 — punto 7.* La primera versión de la demo (×8, umbral 4) dio razón 3,7 bajo carga en la pasada 1 de Windows y se descartó: usa ×4 con un caso pequeño de 0,08 s (razón ≈ 5 frente a ≈ 1 del lineal, umbral 2) y `_medir` omite la sonda ×4 si `crecimiento` ≤ 4; cuesta unos 11 s en Windows (antes 53 s). El `inf` por tope y la segunda muestra ×4 se confirman tras `PAUSA_RONDAS`.
- *i4 — `test_journal.py::test_replay_con_recover_max_limita…`* falló UNA vez bajo la carga de otra suite (aserción de pared `< 5000 ms`) y pasa suelta; no se tocó.
- *Gap 14, rebatido sin cambio:* `git checkout FETCH_HEAD` es la misma clase que `HEAD~1`, permitida por decisión previa.

**Puerta de redact: 10 pasadas sin rojo por plataforma con carga** (`pytest tests/test_redact_fix3.py -m serie -x`, 26 tests, `HEAD` `272c284`, ambas plataformas a la vez; Linux en `python:3.11-slim` `-m 1g`, 4 CPU y 12 bucles de CPU; Windows con 6 bucles):

| Pasada | Linux (12 bucles de CPU, 4 CPU) | Segundos | Windows (6 bucles de CPU) | Segundos |
|---|---|---|---|---|
| 1 | 26 passed, 0 failed | 213 | 26 passed, 0 failed | 494 |
| 2 | 26 passed, 0 failed | 180 | 26 passed, 0 failed | 404 |
| 3 | 26 passed, 0 failed | 194 | 26 passed, 0 failed | 535 |
| 4 | 26 passed, 0 failed | 165 | 26 passed, 0 failed | 426 |
| 5 | 26 passed, 0 failed | 194 | 26 passed, 0 failed | 508 |
| 6 | 26 passed, 0 failed | 257 | 26 passed, 0 failed | 379 |
| 7 | 26 passed, 0 failed | 200 | 26 passed, 0 failed | 396 |
| 8 | 26 passed, 0 failed | 198 | 26 passed, 0 failed | 300 |
| 9 | 26 passed, 0 failed | 207 | 26 passed, 0 failed | 394 |
| 10 | 26 passed, 0 failed | 224 | 26 passed, 0 failed | 302 |

**fix9 (revisión de dos lentes, intento 9: gaps 1, 3, 4, 7 y 8; el modelo de amenaza del usuario no se reabre)** — claves de medición `plugin-audit-2/T-06-fix9` y `T-23-fix9` (abiertas antes del RED).

RED: `agent-kits/shared/test_guardrail_fix9.py` (30 failed, 38 passed), el corpus diferencial `BAD9_PARIDAD` con bash real (falla en `xargs -a <(echo .) git restore`), `tests/test_native_guard_parity9.py` (6 failed), `node --test tests/native-guard-adapter-fix9.test.mjs` (2 fail), `tests/test_fix9_plazos_inyectados.py` (2 failed) y `tests/test_redact_fix3.py` (la demo por la decisión de la puerta, con razón medida 4,78 frente al umbral 6, y 2 tests nuevos: 3 failed) fallaron antes del código · commit RED `0abe812` · 2026-11-14.

GREEN: diseño del orquestador aplicado punto a punto (interpretaciones abajo; commits `d5d3eed` y `4d8076d`):
1. **Sustitución de proceso con `xargs`** (gap 1): `_leer` trata `<(…)` y `>(…)` sin comillas como parte de la palabra que las lleva, igual que `$(…)`: el interior se lee aparte y la orden exterior sigue entera (`xargs -a <(git diff --name-only) git restore` es un solo `xargs`). Las 15 formas (`-a`, `--arg-file`, con y sin `=`, `-I{} sh -c`, `-0`…) se deniegan; `git add`, `git status` y `diff <(…) <(…)` siguen permitidos. Corpus: `BAD9_PARIDAD` (14 sondas con efecto real en bash) y `LEGIT9` (5).
2. **Escáner Python** (gap 3): la alternativa de escape vuelve a `\\.`. El test de paridad pasa 12 casos (identidades escapadas, rol no protegido, sufijo, escape inválido, clave forjada, 64 y 65 blancos, clave partida entre dos lecturas) por el lanzador y el adaptador Python en `claude` y `opencode` y exige el mismo rol.
3. **`env -S`** (gap 4): `_trocea_s` trocea como GNU env, con sus escapes (`\_` separa fuera de comillas, `\c` corta, `\t \n \v \f \r \\ \' \" \# \$`, comentario con `#` al empezar palabra). Un valor ilegible (comilla abierta, más de 2.048 caracteres o quinto troceo) se deniega SIEMPRE para el rol protegido; un escape desconocido o una barra final, solo si la orden contiene git.
4. **OpenCode** (gap 7): `canonical()` guarda el resultado por cadena (tope 64; solo cachea las resoluciones que acaban) y `location.directory` se canoniza una vez en `setup`. 8 eventos del mismo proyecto: de 16 llamadas a `realpathSync.native` a 0. Interop: 88 al día.
5. **Límite** (gap 8): el payload hostil de claves densas de 128 MiB o más agota el plazo de lectura de 4,5 s y sale `continue`; documentado en `implementer.md` e `INTEROP.md` (ES/EN).

**Interpretaciones y rebates de fix9** (ninguno sustituye el diseño en silencio):
- *i1* troceo propio (la barra cambia según comillas; no `shlex`); *i2* `-a`/`--arg-file` ya contaban: el fallo era la segmentación; *i3* `env -S 'echo "hola'` pasa a denegado (punto 4); *i4* `\#` y `\$` se permiten (`git restore '#'` es legítimo); *i5* `${VAR}` dentro de `-S` no se trata; *i6* los dos tests de cerrojo son POSIX: se ejecutan en la réplica Linux.

**fix10 (intento 10, gaps 1 a 6; condensado en fix12 sin perder cifras)** — `plugin-audit-2/T-06-fix10` y `T-23-fix10`. RED (`d502d51`, `306e2dc`): corpus con bash real `BAD10_PARIDAD` (21 formas) y `BAD10_ENV` (30 fallan en el subconjunto), `opencode-realpath-fix10.test.mjs` (3 de 4 fallan), blancos de `test_native_guard_parity9.py` y el vigía de presupuestos. GREEN (`a4ba641`, `a3a7f61`, `926a8ef`, `fcd182e`, `9b38adb`, `e13b5e5`): (1) `case` en sustituciones con pila `w/i/p/b` (`_case_palabra`); fuzz `fuzz10.py` de 54.600 órdenes, d938cab frente a HEAD: **0 regresiones**, 72 denegaciones nuevas; (2) OpenCode: misma ubicación si coinciden tras `resolve()` o `realpath`, caché de éxitos y fallos de 5 s (64 entradas), una resolución por ruta y ventana (interop 88 al día); (3) `env -S`: solo espacio y tabulador separan y un LF, VT, FF o CR suelto se deniega como forma AMBIGUA con git (coreutils 9.7 los separa y abre comentario tras `#`; 8.x no: la paridad de `BAD10_ENV` se exige solo con 8.x); (4) `[ \t\n\r]` en los dos escáneres y el lanzador. Interpretaciones: (i1) un fallo de `realpath` se cachea 5 s; (i2) el test de fix9 «se canoniza al cargar» pasa a comprobar que `setup` no la resuelve; (i3) un `case` anidado en UNA sustitución se deniega como incompleto; (i4) se aplican «solo espacio y tabulador» y «denegar si 9.x difiere».

**fix11 (intento 11, gaps 1 a 7, 9, 11 y 12; condensado en fix12 sin perder cifras)** — `plugin-audit-2/T-06-fix11` y `T-23-fix11`. RED (`b166cf2`, `3c20ec5`): `test_guardrail_fix11.py` (**29 de 47** fallan contra el código de e4b2f7f y 18 pasan; en HEAD pasan 47; el ledger decía 27 de 45), corpus con bash real `BAD11_PARIDAD` (**59** formas de `la11/`, `lb11/` y `lc11/`; el ledger decía 60), `SIN_PARIDAD_11` (**8**, solo deny; decía 7), `LEGIT11` (5), `FALSO_DENY_ACEPTADO_11` (3), `LIMITE11` (5), `test_journal.py` (4 fallan) y `opencode-realpath-fix11.test.mjs` (2 de 4). El deny de LF/VT/FF/CR sueltos en `env -S` de fix10 (`926a8ef`) **entró sin RED previo** (sus tests llegaron en `fcd182e`; se declara). GREEN (`9cff71f`, `945a4fc`, `f007327`, `f0c95ee`, `10aaf44`): (1) `case` por LISTA BLANCA dentro de `$(…)`, `<(…)`, `>(…)`: solo `case` sin comillas ni escapes («plana»), primera palabra, profundidad 0 y sin prefijos; `in` + blanco; patrones `[\w.*?/+=,:%@^~-]+` sin `esac`; `esac` primero; cualquier otra aparición deja la lectura incompleta (deny con git); fuzz `fuzz11.py` de 38.640 órdenes: **0 regresiones frente a d938cab y a 8e7c0a0**, 13.156 y 14.568 deny nuevos, todos fuera de la lista blanca (cuerpo inocuo: 0 deny nuevos); (2) coste lineal: `_empieza_orden` y `_PREFIJOS_ORDEN` fuera; 64 KB de `! `, `{ `, `then `, `if `, `time -p `, `do `: 0,08 a 0,12 s sin git y 0 s con git (antes 47 s); (3) `$'…'` se decodifica como bash; (4) journal: espera solo con un `.tmp-*` hermano reciente del mismo inodo (plantado → `unsafe_state` en < 50 ms), la rama write recibe la misma espera; (5) OpenCode: un `realpath` fallido (cacheado incluido) en cualquiera de los dos lados deja la sesión guardada (interop 88); (6) `docs/agents/implementer.md:92` corregido. Interpretaciones: (i1) `ENOENT`/`ENOTDIR` de `realpath` NO es indeterminado; (i2) `x=1 case …` no es un `case` en bash (`SIN_PARIDAD_11`); (i3) `` `true` {D} `` y `$(true) {D}` son `LIMITE11` (indirección); (i4) `esac` cierra en patrones solo si lo sigue blanco, `;` o `)`; (i5) el deny sobre formas legítimas con git inocuo queda en `FALSO_DENY_ACEPTADO_11`; (i6) `cat >( (case …) )` pasa a `SIN_PARIDAD_11` (en Linux `cat` se cuelga; `tee >(…) </dev/null` conserva la paridad).

**Cierre fix11** — commits RED `b166cf2` y `3c20ec5`; código `9cff71f`, `945a4fc`, `f007327`, `f0c95ee`, `10aaf44`; ledger `c051196` y siguiente; sonda `4872d92`. Réplica Linux COMPLETA de `ci.yml.MANUAL-COPY` sobre `4872d92` (`python:3.11-slim`, `-m 1g --cpuset-cpus 0-3`, Node 22, `git archive` en LF, ≥ 3 GB libres): **0 failed / 0 errors**: linter 0 errores · `check-handbook` · evals 227 · pytest paralelo 13.259 passed, 71 skipped (463 s) · serie 58 passed (85 s) · bench `p95=17,81 ms` · interop 88 · `node --test` 532 pass, 0 fail (89 s) · sintaxis · JSONs + `release.py --check`; 645 s. La primera réplica (`c051196`) dio un rojo (i6), corregido y repetida entera. Windows: guardarraíl 901 + fix10/fix11 65, diferencial 1.315 con bash real, journal 200 + 32, nativo 190, node OpenCode 32; la suite node completa de Windows dio 2 rojos (`run-hook candidates` por CRLF, que el orquestador corrigió en `6e41dfe`, e `installer.test.mjs`, que fix12 diagnostica). Horas medidas de fix11 `(medido)` (ventana compartida; se imputan a T-06): 0.43 h.

**fix12 (intento 12, gaps 1, 3, 4, 5, 7, 8 y 9; el diseño del orquestador se aplica tal cual)** — `plugin-audit-2/T-06-fix12` y `T-23-fix12`.

RED (`28f1308`, contra el código de a5ba181): `test_guardrail_fix12.py` (**27 de 56** fallan: 7 formas de `\c` con comilla, `\c\\`, `\x`, `\u`, `\U`; 7 de `\x{H…}`; surrogate y `main()` con fallo inyectado; el diferencial generado halla **18 divergencias** con efecto) y el corpus con bash real `BAD12_PARIDAD` (16 formas de `lb12/` y `lc12/`), `BAD12_LLAVES` (7, la paridad se salta con bash < 5.2), `SIN_PARIDAD_12` (2) y `LEGIT12` (2; en `2f16fc3` quedan 1 y 3, ver i3). **Tres ramas de deny entraron en fix11 sin RED previo** (`\U` fuera de rango, patrón vacío, separador en los estados `w`/`i`): sus 5 tests de regresión llegan ahora y **pasan contra a5ba181** porque la rama ya existía; se declara aquí (gap 7), no son un RED.

GREEN (`8105752`):
1. **`$'…'` como bash** (gaps 1 y 4): `_ansi_fin` delimita por pares `\X` (el primer `'` sin escapar cierra) y `_ansi_decodificar` decodifica DESPUÉS el contenido: `\c` aplica sobre el contenido ya delimitado (`\c\\` consume las dos barras; `\c` final queda), `\x{H…}` toma cualquier número de cifras módulo 256 y sin cifras da NUL (medido con bash 5.2.37: `$'\x{}'` y `$'\x{1F600}'` cortan la cadena). Diferencial generado con bash real desde ficheros `.sh` (22 escapes × 5 cierres × 4 formas + nombres que decodifican a `git`): **458 órdenes, 238 ejecutan git, 348 denegadas, 0 divergencias con efecto** (a5ba181: 18). `git` es una función dentro de cada script: no corre ningún git real.
2. **Fallo cerrado de la ruta heredada** (gap 3): `_destino_es_el_propio_directorio` captura `(OSError, ValueError)` (el surrogate suelto de `realpath` en POSIX es `UnicodeEncodeError`); una excepción interna de `main()` en `pre-tool` deniega con un motivo explícito (`error interno … se deniega`); un stdin que no es JSON se sigue permitiendo. Tests con `realpath` al estilo POSIX y con una excepción inyectada.
3. **Tests sin reloj de pared** (gap 5): los de coste del guardarraíl miden CPU del proceso y la razón de linealidad 16 KB → 64 KB (`grande < 8·max(chico, 0,03) + 0,05` y `grande < 1,0` s de CPU); `_tiempo` del diferencial y los `< 0.05` del journal (se cuentan las dormidas con un reloj inyectado) dejan el reloj de pared. 20 pasadas con 12 bucles de CPU, **0 rojos** (por pasada: 14 tests de coste del guardarraíl en 1,2 a 1,7 s, 11 cotas del diferencial en 25 a 37 s y 7 del journal en 48 a 63 s; la primera pasada, con el disco en frío, 139 s de journal).
4. **Docs** (gaps 8 y 9): recuentos corregidos arriba; `docs/agents/implementer.md` nombra `LIMITE11` (sustitución como palabra de mando) y el fallo cerrado de `pre-tool`.

Interpretaciones: (i1) `$'\x{}'` sin cifras da NUL como bash 5.2.37 (no pasa la barra); (i2) las cotas de coste pasan del reloj de pared (0,3 s, que en reposo daba 0,28 s) a CPU: la razón de linealidad es la que detecta lo cuadrático (47 s antes), y el absoluto sube a 1,0 s de CPU; no se quita ninguna aserción de linealidad; (i3) dos formas de `lb12` no ejecutan git en bash: `x=$'…' && … && echo '` deja la comilla abierta y sigue en `SIN_PARIDAD_12` (deny); la otra, con la secuencia de control de dos barras seguida de ` x'`, que el RED clasificó como deny sin paridad porque el código viejo la denegaba, con la delimitación correcta es una palabra y una cadena: bash no ejecuta git y el guardarraíl la permite, así que pasa a `LEGIT12` (`2f16fc3`); (i4) `test_ansi_c_delimita_primero_y_decodifica_despues` esperaba 5 donde la cuenta correcta es 4 (error de aritmética mío en el test, corregido en `8105752` con la misma intención); (i5) `"${x:-$'\x67it'}" reset --hard` (expansión de parámetros) sigue siendo límite declarado.

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
- **Tiempo IA (ejec.)**: est. 0.5h · real 0.55h (medido; ventana compartida con T-02..T-07) + fix5 a fix9 sin horas propias (ventanas imputadas a T-06)
- **Archivos**: `tests/codex-plugin-state.test.mjs` (intento 12, orquestador: la regex del test de `candidates()` acepta CRLF; en un checkout de Windows `run-hook.mjs` llega con CRLF y el test daba rojo) · `docs/roadmap/2026-11-10-plugin-audit-2/testing/perf.md` (lo escribe el orquestador con las medidas de T-07 y T-23; el guardarraíl veta `testing/` al implementer) · `ci.yml.MANUAL-COPY` y `.github/workflows/ci.yml` (idénticos, comprobado con `diff`; el paso `pip install pytest pyyaml` de `:30-31` añade `pytest-xdist`), `tests/test_ci_manual_copy.py`, `tests/test_ci_skill_suites.py`, `tests/test_suites_no_pytest.py` · añadidos por la nota de alcance: `pytest.ini` (solo registra el marcador `serie`), `tests/test_redact_fix3.py`, `tests/test_npm_payload.py` (fix4: timeout de `npm pack` 120 → 600 s), `tests/test_local_state_fix3.py` (fix4: módulo al paso serie, plazo de pared del almacén), `agent-kits/shared/test_redact.py`, `agent-kits/shared/test_plan_review_summary.py`, `tests/test_agent_activity_store.py`, `tests/test_bench_session_end.py`, `tests/opencode-plugin.test.mjs` (fix1: espera a que el hijo escriba el JSON), `tests/test_lint_plugin.py`, `tests/test_ledger_lint.py`, `tests/test_dashboard.py` (fix1: wrappers `test_suite_legada_*` de sus `main()`/`run()`) (marcados `@pytest.mark.serie`: miden tiempo de pared o dependen del orden de lecturas y fallan bajo `-n auto`; corren en un paso aparte sin xdist), `agent-kits/shared/agent-activity-store.py` (fix5), `agent-kits/shared/test_redact.py` (fix5) · fix7 (corrección de fix8, gap 9: faltaban): `agent-kits/shared/test_ledger_view.py` (paso serie), `tests/test_graphiti_security.py` (huella del lanzador) · fix8: `agent-kits/shared/test_journal_io_deadline.py` (nuevo), `agent-kits/shared/journal-io.py` (plazo inyectable solo bajo `PYTEST_CURRENT_TEST`), `agent-kits/shared/test_journal.py`, `tests/test_redact_fix3.py`, `tests/test_native_guard_failclosed.py` (prueba de plazo al paso serie), `tests/test_panel_review_panel_server.py` (2 pruebas al paso serie) · fix9: `tests/test_fix9_plazos_inyectados.py` (nuevo), `agent-kits/shared/test_journal.py` (sin aserciones de pared), `tests/test_panel_review_panel_server.py` (BODY_TIMEOUT inyectado, sin paso serie), `tests/test_redact_fix3.py` (demo ×12 por la decisión de la puerta y sonda al crecimiento real) · fix10: `agent-kits/shared/test_journal.py`, `tests/test_fix9_plazos_inyectados.py` (vigía), `tests/test_redact_fix3.py`, `agent-kits/shared/journal-io.py` y `journal-capture.py` (`settled`: espera el estado transitorio de dos enlaces), `skills/training-data-services/scripts/test_dataset_assembler.py` y `agent-kits/shared/test_knowledge_read_context.py` (rojos de réplica de tiempo de pared) · fix12: `agent-kits/shared/journal-io.py`, `agent-kits/shared/test_journal.py`, `tests/installer.test.mjs` (el test de la CLI colgada mide desde el arranque de la CLI)
- **Evidencia**: MEDIDA (Linux `python:3.11-slim`, un contenedor `-m 1g`, 4 CPU, `git archive` en LF, mismos **11.190 tests** en las dos formas; `testing/perf.md` lo veta el guardarraíl del rol, por eso consta aquí). CI VIEJA: bucle (163 ficheros `tests/test_*.py` ejecutados como script) **163 s** + pytest en serie **1.340 s** = **1.503 s**. CI NUEVA: bucle solo con los 3 ficheros sin `def test` (`test_coverage_check`, `test_mermaid_blocks`, `test_readme_badges`) **9 s** + `pytest -n auto -m "not serie" --durations=20` **615 s** (host sin otra carga; 734 s con carga) + paso `-m serie` **55 s** = **679 s ≈ 45 %** (pytest solo: 46 %; suelo del paralelo: `test_task_brief::test_ca08…` = 131-166 s). REBATE del plan: los ficheros que el bucle repetía eran **160 de 163** (no 23/27: casi todos los `tests/test_*.py` tienen ya `def test`). `-n auto` rompió tests que miden tiempo de pared o contienden por un lock con procesos hermanos; marcados `@pytest.mark.serie` (marcador registrado en `pytest.ini`, paso aparte sin xdist): `test_redact_fix3::test_linear_cost_on_pathological_inputs`, `test_redact::test_2_2_lineal_con_muchas_comillas_y_operadores`, `test_plan_review_summary::test_state_changed_during_read`, `test_agent_activity_store::test_d2_burst…` y `::test_2_1_lifecycle_signals_survive_sustained_tool_contention…`, `test_bench_session_end::test_bench_mide_in_process…` y `::test_bench_reporta_e2e_p50…`; `tests/test_suites_no_pytest.py::test_los_tests_de_tiempo_van_en_un_paso_serie_aparte` fija la lista y el paso. Residuo conocido de ESTA máquina (no de xdist): los dos de `redact` miden `< 1,5 s` y fallan también en serie aquí (tardan 1,7 s; en el runner de GitHub pasan) → `test_redact_fix3` falla en el paso serie en este entorno. GREEN: `pytest -q tests/test_ci_manual_copy.py tests/test_ci_skill_suites.py` → `16 passed`; `tests/test_suites_no_pytest.py -k "bucle or paraleliza or incluye or tiempo or hay_suites"` → `5 passed`; `ci.yml.MANUAL-COPY` y `.github/workflows/ci.yml` idénticos. Medición de uso (usage-meter, `plugin-audit-2/T-23`, ventana compartida con T-02..T-07 porque se hicieron entrelazadas): 0,55 h IA medidas, 33 min, ≈ 7,88 € estimado por tarifa; las demás tareas llevan estimación.
- **Runtimes**: Sin diferencia de conducta; la CI sigue ejecutando `node --test` de Codex y OpenCode.
- **Verificación**:
  - `pytest -q tests/test_ci_manual_copy.py tests/test_ci_skill_suites.py tests/test_suites_no_pytest.py` → verde (rojo antes: un test exige que el bucle solo ejecute las suites sin `def test_`)
  - en Linux (`python:3.11-slim`, LF): `python -m pytest tests agent-kits/shared -n auto -q --durations=20` → mismos tests y resultado y tiempo < 50 % del serie, anotado en `testing/perf.md`

**Criterios de aceptación**
- [x] El bucle solo ejecuta los ficheros que pytest NO recoge (sin `def test_`).
- [x] `-n auto` no rompe los tests que usan puertos, `os.chdir` o ficheros compartidos (los que fallen se marcan `xdist_group`/serie, con motivo).
- [x] Se publica `--durations` en el resumen de la CI.


RED: `tests/test_suites_no_pytest.py::test_el_bucle_de_ci_solo_ejecuta_lo_que_pytest_no_recoge y ::test_la_ci_paraleliza_pytest_y_publica_durations` falló con AssertionError: el bucle itera todo tests/test_*.py (sin grep -L) y falta pip install pytest-xdist / -n auto / --durations en ci.yml · 2026-11-11.

**fix1 (revisión de dos lentes, intento 1: gaps 1 y 14)** — clave de medición `plugin-audit-2/T-23-fix1`.

RED: `tests/test_suites_no_pytest.py::test_ningun_caso_de_la_ci_queda_solo_en_main` falló con AssertionError: `huecos = {tests/test_dashboard.py: [check_meter_to_dashboard, check_persistence_flags, check_snapshot_windows, run], tests/test_ledger_lint.py: [main], tests/test_lint_plugin.py: [18 funciones casos_*/caso_* y main]}` (el `main()`/`run()` de las tres suites mixtas solo colgaba de `__main__`: pytest no lo ejecuta y el bucle de la CI las saltaba por tener `def test_*`) · 2026-11-11.
RED: `tests/test_suites_no_pytest.py::test_el_bucle_de_ci_no_existe_y_nada_corre_dos_veces` falló con AssertionError: «el bucle de scripts sigue en la CI» (`for t in $(grep -LE …); python "$t"` en `ci.yml.MANUAL-COPY`: las suites-script corrían ahí y otra vez bajo `test_la_suite_script_pasa`) · 2026-11-11.

GREEN: el detector `casos_solo_desde_main` (AST: funciones no-`test*` con `assert` alcanzables desde `__main__` y desde ninguna `test*`; se recorre `tests/`, `agent-kits/shared`, `agent-kits/knowledge-curator`, `skills/*/scripts`, `evals`) lo recorre pytest en `test_ningun_caso_de_la_ci_queda_solo_en_main` y se prueba a sí mismo en `test_el_detector_ve_un_caso_que_solo_cuelga_de_main`. Las tres suites mixtas exponen su `main()`/`run()` en `def test_suite_legada_main|run()` (recomendación de la revisión; no se vuelve al bucle). Gap 14 (doble ejecución): se ELIMINA el bucle de la CI (el único ejecutor es pytest: las suites-script, por `test_la_suite_script_pasa`; las mixtas, por el wrapper) y `test_dashboard.run()` ya no llama a los 6 `test_*` que pytest recoge por su cuenta. `ci.yml.MANUAL-COPY` y `.github/workflows/ci.yml` siguen byte-idénticos (`cmp`). `pytest tests/test_suites_no_pytest.py tests/test_ci_manual_copy.py -k "not la_suite_script_pasa"` → `20 passed`; `tests/test_lint_plugin.py` → `5 passed`; `tests/test_ledger_lint.py` → `13 passed`; `tests/test_dashboard.py` → `8 passed`.

**Verificación en Linux de los fix1 (gap 3)** — `python:3.11-slim`, un contenedor `-m 1g --cpuset-cpus 0-3` (sin `--cpuset-cpus`, `-n auto` veía los núcleos del anfitrión: 16 procesos en 1 GiB, `INTERNALERROR` y 38 fallos por OOM; ese intento se descarta), árbol de `git -c core.autocrlf=false archive`, Node 22 y npm copiados de `node:22-bookworm-slim`, permisos normalizados desde el índice (un montaje de Windows los deja todos en 0777 y `hooks.json` salía ejecutable). Pasos del `ci.yml` nuevo, resultado final sobre HEAD `5bb47c1` (tras los fix1):

(Tabla de la réplica de fix1 condensada por el tope de lectura de 256 KiB del ledger: lint, evals, interop, bench, node y sintaxis en verde; paralelo 11.299 passed con el rojo conocido del PDF y 4 errors de entorno, ambos resueltos en ciclos posteriores; serie 14 passed en 64 s.)

(SUPERADO por T-38 y por el fix4: ya no hay rojo; ver la réplica Linux del fix4 más abajo. Registro histórico:) Lo que NO está en verde, con causa:
- `check-handbook` (exit 1) y `tests/test_npm_payload.py::test_npm_contains_pdf_editions_linked_from_its_readme` (`sha256` de una fuente ≠ el de `output/pdf/*.manifest.json`; el test y el script leen los mismos manifiestos): una sola causa, las ediciones `output/pdf/*` se generaron antes de que cambiaran esas fuentes. Acción del usuario: regenerar los PDF (T-03).
- Los 4 *errors* del paso paralelo (`test_npm_payload`, `npm pack` agota los 120 s del fixture en un contenedor de 1 GiB con 4 procesos): artefacto de la máquina. Aislado en un contenedor (`pytest tests/test_npm_payload.py`): `4 passed, 1 failed` (el del PDF, arriba).
- El aviso extra del linter que sale en Linux con el montaje sin normalizar (`hooks/hooks.json` ejecutable) desaparecen con los permisos del índice (`100644`).

Corrección del intento 2 (gap 7): la fila del paso pytest decía `0` fallos y solo `check-handbook` figuraba como rojo; el rojo del PDF afecta a las DOS comprobaciones, como detalla la primera viñeta (el recuento `11.299` no se ha vuelto a medir).

Primera pasada (HEAD `4fa93a8`, con `--cpuset-cpus`): `5 failed, 11299 passed, 4 errors` en el paso paralelo y `1 failed, 6 passed` en el serie, node `511 pass, 1 fail`. Cada rojo se investigó y se corrigió (RED = ese fallo observado):
1. `tests/test_f4fix1_misc.py::test_f4fix1_15…` (`41 <= 40`): la «Variación posterior» de `docs/TOKEN-EFFICIENCY.md` (T-02, commit `14adaca`) era UNA frase de 41 palabras → dos frases (commit `0fbc8b9`). Fallo real de la fase, no se veía en Windows porque nadie corría la suite entera.
2. `tests/test_copias_declaradas.py::…[docstring_uso_exit]`: el docstring de uso de `code-health.py` (T-07 fix1) ganó una línea y el rango `26-30` de `agent-kits/shared/copias.json` se desplazó → `26-31` (commit `be30291`). Regresión de mi propio fix1.
3. `agent-kits/shared/test_redact.py::test_bounded_memory_inputs_redact_without_superlinear_delay[curl_args|mysql_args]` (1,72 s y 1,60 s `< 1.5` bajo `-n auto`): test de tiempo de pared sin `@pytest.mark.serie` → marcado (test dedicado `test_los_tests_de_tiempo_de_pared_de_redact_estan_marcados_serie`, rojo antes).
4. `tests/test_redact_fix3.py::test_linear_cost_on_pathological_inputs` en el paso SERIE (`2,07 s < 1.5`, entrada de 1 MB `'--x mysql ' * n`): causa raíz medida, no subida de umbral. `redactar` es lineal (25 K → 0,30 s · 50 K → 0,60 s · 100 K → 1,52 s en `--x mysql`; `curl -u a:b` 0,47 → 0,73 → 1,72) y sostiene ≈ 0,7 MB/s en esta máquina: el umbral de 1,5 s por MB mide la VELOCIDAD del equipo, no la complejidad. Ahora cada caso se mide a 25 K y a 100 K y pasa si el grande cabe en 1,5 s o si la razón es ≤ 8 (lineal ≈ 4, cuadrático ≈ 16) y no pasa de 10 s; `test_el_criterio_de_linealidad_distingue_lineal_de_cuadratico` fija que un coste cuadrático (×16) sigue fallando (commit `3737e38`).
5. `tests/opencode-plugin.test.mjs::native adapter identifies its runtime…` (`Unexpected end of JSON input`, node `511/1`): carrera de test — el hijo crea `end-argv.json` y lo escribe después, y el test lo leía en cuanto existía. Ahora espera a que no esté vacío (también `stream-args.json`, mismo patrón); TDD n/a: carrera de temporización, sin forma determinista de reproducirla. Ese fichero entra en el `Archivos` de esta tarea.
6. `test_hooks_shell::test_todos_los_hooks_son_bash_valido_y_ejecutables`: artefacto del montaje (permisos 0777), no del repo; corregido en el script de replicación.

Segunda pasada completa (la tabla de arriba, HEAD tras los fix1): sin ningún fallo salvo el rojo conocido de los PDF. Medición de uso de los fix1 (usage-meter, ventanas solapadas, no sumables): T-23-fix1 0,82 h IA, T-06-fix1 0,79 h, T-07-fix1 0,88 h, T-02-fix1 0,51 h, T-03-fix1 0,47 h (medido).

**fix2 (revisión de dos lentes, intento 2: gaps 5, 6 y 7)** — clave de medición `plugin-audit-2/T-23-fix2`.

RED (gap 6): `tests/test_suites_no_pytest.py -k formas_que_antes` falló con `5 failed, 2 passed`: el detector `casos_solo_desde_main` devolvía `[]` para un `assert` directo en el bloque `__main__`, una función pasada por referencia (`ejecutar(caso)`), funciones en una tupla recorrida (`for f in (a, b): f()`), una llamada por atributo (`suite.caso()`) y un método (`S().caso()`); los 2 que pasan son los negativos (la misma referencia o el mismo método alcanzado desde un test) · 2026-11-12.

RED (gap 5): `tests/test_redact_fix3.py::test_el_criterio_de_linealidad_distingue_lineal_de_cuadratico` con los casos nuevos contra el `_es_lineal` anterior: `_es_lineal(0.30, 2.40)` (n^1,5, ×8) y `_es_lineal(0.20, 1.40)` (×7 en un caso «rápido») daban `True` (la razón `≤ 8` y el atajo `< 1,5 s` los aceptaban), y los `assert not` nuevos fallan · 2026-11-12.

GREEN: `pytest -q tests/test_redact_fix3.py` → `680 passed` (Windows y Linux `python:3.11-slim`, `-m 1g`, 4 CPU); `pytest -q tests/test_suites_no_pytest.py -k "not suite_script"` → `15 passed` en Windows y el fichero completo `18 passed` en Linux (en Windows el fichero completo pasa de 9 min por las suites-script, independiente de esta tarea). Gap 6: `_referencias` (sustituye a `_llamadas`) toma llamadas, referencias sueltas y atributos; `casos_solo_desde_main` añade `<__main__>` si el propio bloque lleva un `assert`; un test por forma (7 parametrizados). Hoy no hay ningún caso así en la CI (`test_ningun_caso_de_la_ci_queda_solo_en_main` sigue en verde). Gap 5: `_es_lineal` = `t_grande < 10 and t_grande <= 6,5 × max(t_chico, 0,05)`, sin atajo por tiempo absoluto; el caso pequeño se mide tras un calentamiento y como el mejor de 2, el grande con hasta 3 intentos (el ruido ajeno solo suma tiempo; un algoritmo superlinear falla los 3). Medida de las 23 entradas (25 K contra 100 K, un solo intento, calentado): razón máxima 5,89 en Windows y 9,29 en Linux (caso `"it's " * n + "mysql -pX"` bajo carga de otro proceso; el test serie sobre el árbol final: 0 rojas en 8 ejecuciones en Linux con el anfitrión en reposo y 2 rojas en 6 con una suite de Windows corriendo a la vez, es decir, el test sigue siendo sensible a la carga ajena como cualquier medida de tiempo; en la CI corre en el paso serie, sin xdist) — de ahí 6,5 y no 6: lineal es ×4, n^1,5 ×8, cuadrático ×16, y ×6,5 deja holgura al ruido de CI sin aceptar n^1,5. Gap 7 y gap 8: solo ledger (T-03, tabla Linux de T-23 y T-02), TDD n/a: prosa/ledger.

**fix3 (revisión de dos lentes, intento 3, ciclo final: gaps 2 y 9)** — clave de medición `plugin-audit-2/T-23-fix3`. Diseño fijado por el orquestador: tiempo de CPU, mediana de 3, entrada ×8, tope 16. Sin ficheros nuevos en `Archivos`.

RED: los casos del criterio nuevo contra el `_es_lineal` vigente (tope 6,5, entrada ×4) dan rojo: `_es_lineal(0.30, 2.40)` (lineal ×8) → `False`, `(0.30, 4.20)` (×14) → `False`, `(0.01, 0.70)` (bajo el suelo de ruido) → `False`; es decir, la puerta anterior rechazaba una razón lineal de ×8, que es justo lo que mide el redactor al crecer la entrada ×8 (la causa de los rojos intermitentes: 6,69 y 9,29 frente a 6,5) · 2026-11-12.

GREEN: `tests/test_redact_fix3.py`: la puerta mide `time.process_time` (CPU, no pared), mediana de 3 por tamaño, entrada pequeña = grande/8 (`CRECIMIENTO = 8`), tope `RAZON_LINEAL_MAX = 16` (lineal ≈ 8, n^1,5 ≈ 22,6, cuadrático ≈ 64) y suelo de ruido de 50 ms (el reloj de CPU de Windows tiene 15,6 ms de resolución). Dos tests nuevos demuestran la puerta con funciones REALES, no con números: `test_la_puerta_deja_pasar_una_funcion_lineal_real` (un bucle lineal, 600 k frente a 4,8 M: pasa) y `test_la_puerta_rechaza_una_funcion_cuadratica_real` (un doble bucle, n = 800 frente a 6.400, ≈ 41 M de iteraciones: razón ≈ 64, falla la puerta). Gap 9: `_mediana3` devuelve la salida de la última medición y el test de idempotencia la reutiliza: ya no se llama otra vez a `redactar(grande)` (−1 pasada de 1 MB por caso). `pytest -q tests/test_redact_fix3.py` → `682 passed`.

Estabilidad (el test lineal sobre los 23 patológicos + los dos de demostración, 10 pasadas seguidas cada plataforma; razón máxima de cada pasada frente al tope 16; un lanzador en proceso llama a las mismas funciones del test):
- Windows (reposo): 10 de 10 verdes; razones máximas 10,62 · 10,17 · 12,00 · 12,50 · 11,56 · 12,20 · 10,62 · 8,60 · 13,33 · 9,83 (máx. 13,33).
- Linux `python:3.11-slim`, `-m 1g`, con carga ajena en el mismo contenedor (4 bucles de CPU `while :; do :; done` en un anfitrión de 12 CPU): 10 de 10 verdes; razones máximas 10,07 · 10,00 · 13,57 · 9,13 · 13,23 · 12,46 · 11,58 · 11,35 · 10,25 · 12,28 (máx. 13,57).
- Límite honesto, medido: con 12 bucles (un bucle por CPU del anfitrión, saturación total más otros contenedores) el tiempo de CPU también se infla por contención de caché/SMT y el caso `'it's ' * n + mysql -pX` dio razón 19,5, `'A=1 ' * n` 19,2 y la primera pasada salió roja (16,27; tiempos 0,075 s → 1,221 s). No es un retroceso del algoritmo (el cuadrático real da ≈ 64) sino el suelo de la técnica; el tope 16 del diseño se mantiene (el margen medido con 4 bucles y en reposo es ≥ 18 %) y la saturación total de la máquina queda fuera de lo que esta puerta garantiza. Si el orquestador quiere cubrirla, la palanca es subir `RAZON_LINEAL_MAX` a 24 (sigue rechazando el cuadrático con margen ×2,7 y acepta solo hasta n^1,5 ≈ 22,6): decisión suya, no tomada aquí.


**fix4 (revisión de dos lentes, intento 4, último ciclo de la fase 1: gaps 2 y 6)** — clave de medición `plugin-audit-2/T-23-fix4`. Diseño estructural fijado por el orquestador (puerta autocalibrada con función de referencia y tamaño adaptativo hasta superar el suelo). `tests/test_npm_payload.py` se añade a `Archivos` de esta tarea (su fixture agotaba el timeout de `npm pack` en la réplica Linux, ver abajo).

RED: la puerta anterior (`_es_lineal(t_chico, t_grande)` con suelo de 50 ms) daba verde falso al cuadrático real de la revisión: `_es_lineal(0.0, 0.4062)` (`re.compile(r"x*y").search("x"*25000)`: `tc=0.0000 tg=0.4062`) → `True` porque `0.4062 <= 16 × max(0, 0.05)`; 15 de las 23 entradas patológicas quedaban bajo el suelo (no se comparaba ninguna razón) y con la máquina saturada salía rojo (16,27) · 2026-11-12. Los tests nuevos `test_la_puerta_rechaza_la_regex_cuadratica_que_antes_quedaba_bajo_el_suelo`, `test_la_puerta_rechaza_un_n_a_la_1_5_real` y `test_sin_suelo_*` no existían (y `_medir`/`SinSuelo` tampoco: `NameError`).

GREEN: `tests/test_redact_fix3.py`: `_medir(funcion, generador)` adapta el tamaño del caso pequeño (doblando desde 1.500 unidades) hasta que su CPU supera el suelo (`SUELO_CPU` 0,05 s en Linux y 0,1 s en Windows, cuyo reloj de CPU tiene 15,6 ms de resolución), con tope de tamaño (1 M de caracteres el pequeño, ×16 el grande) y de CPU gastada buscándolo (30 s: `SinSuelo` con motivo claro). En la misma pasada mide una referencia LINEAL (un recorrido por carácter, repetido hasta superar medio suelo) sobre la misma entrada, intercalada con la función, y compara `razón_redact / razón_referencia`; la carga ajena afecta igual a las dos. Mínimo de 2 muestras por ronda y hasta 3 rondas (el ruido solo suma tiempo; solo se repite el rojo, y lo superlineal de verdad sale rojo en todas). Un grande de más de 10 s se da por colgado. Tope relativo 2,5.
Rebate al diseño (con evidencia): con la entrada ×8 un n^1,5 real medía 2,37 (el de referencia mide ×8,8 por caché), por debajo del tope 2,5; la puerta lo habría aprobado. Con ×16 el n^1,5 vale 4 y el cuadrático 16 (lineal sigue ≈ 1), así que `CRECIMIENTO = 16` (la demostración con ×8 estaba en el margen del ruido). Segundo rebate: bajo el tope de tamaño, un caso inocuo (la entrada tope se procesa en menos del suelo) no puede medir razón; en vez de fallar —lo que daría rojo permanente a los casos baratos legítimos, p. ej. `"a" * n * 2`—, `_medir` devuelve `None` y el test exige que ese caso tarde menos del suelo incluso en el tamaño tope (un cuadrático con esa constante tardaría segundos a 1 MB). Las demostraciones usan funciones REALES: lineal (pasa), `n^1,5` (falla) y el cuadrático `re.compile(r"x*y").search("x"*N)` con `suelo=0,03` (falla; antes quedaba bajo el suelo), más `test_sin_suelo_alcanzado_no_se_aprueba_por_razon` y `test_sin_suelo_por_tope_de_cpu_falla_con_motivo`. Los 23 patológicos son 23 tests parametrizados (`test_linear_cost_on_pathological_inputs[k]`, marcados `serie`) con generadores por caso (`_GENERADORES`). Gap 6: las medidas con carga ajena se hicieron con carga real (ver tablas).

Estabilidad (10 pasadas seguidas por plataforma con el lanzador en proceso, que llama a las mismas `_medir`/`_es_lineal` que el test; se imprime la razón normalizada máxima de cada pasada frente al tope 2,5, el caso que la dio y los rojos):
- Windows, carga ajena real (la réplica Linux completa de la CI corriendo a la vez en Docker Desktop, 4 CPU): 10 de 10 verdes; razones normalizadas máximas por pasada 1,76 · 1,68 · 1,30 · 1,39 · 1,89 · 1,50 · 1,63 · 1,57 · 1,53 · 1,59 (máx. 1,89; cada pasada ≈ 5 min).
- Linux `python:3.11-slim`, `-m 1g`, 12 bucles de CPU `while :; do :; done` en paralelo en el mismo contenedor (saturación del anfitrión de 12 CPU) y, a la vez, las pasadas de Windows: 10 de 10 verdes; razones máximas 2,06 · 2,01 · 1,48 · 2,18 · 1,66 · 1,98 · 2,42 · 2,05 · 2,10 · 2,03 (máx. 2,42; tope 2,5; ≈ 3 min por pasada).
- Qué se midió por el camino y por qué la puerta tiene lo que tiene (cada rojo se investigó, ninguno se aceptó): (a) sin reintentos una pasada con 12 bucles dio 3,52, y con 3 rondas seguidas otra dio 5,63 (el caso `"/" * n * 2 + "mysql"`): una ráfaga de carga ajena cubría todas → 4 rondas con 5 s de pausa entre ellas (solo se repite el rojo; lo superlineal de verdad sale rojo en todas); (b) una pasada en Windows dio razón 5,6·10⁷: el reloj de CPU de Windows carga por ticks y bajo carga devolvió 0,0 para una llamada de 0,1 s → las muestras por debajo de 1/8 de lo esperado se descartan (primero a la mitad, que descartaba medidas reales en Linux saturado: `SinSuelo`; `test_una_muestra_de_cpu_a_cero_…` y `test_las_muestras_invalidas_se_descartan` fijan el criterio; sin el filtro, `ZeroDivisionError`); (c) con DOBLE saturación (12 bucles + las pasadas de Windows y otra suite) una pasada en Windows dio 2,69 en `("curl -" + "v" * 50 + " ") * (n // 25)` tras 4 rondas: carga muy por encima de «ajena» (el anfitrión entero ocupado por dos cargas); con la réplica CI como única carga las 10 pasadas salen entre 1,30 y 1,89.


Medición de uso del ciclo (usage-meter, ventanas solapadas, no sumables): `plugin-audit-2/T-06-fix4`, `T-07-fix4` y `T-38` 1,02 h IA medidas cada una; `T-23-fix4` 1,47 h IA medidas (1 h 28 min).

**Réplica Linux completa de la CI sobre el árbol final del fix4 (HEAD `5c8904a`, T-23-fix4)** — `python:3.11-slim`, un contenedor `-m 1g --cpuset-cpus 0-3`, anfitrión sin otra carga mía, árbol de `git archive HEAD` (con `core.autocrlf` del propio repo: el guardarraíl veta `git -c core.autocrlf=false`; los 1.946 ficheros de texto salieron en CRLF y se normalizaron a LF con un script antes de montarlos), permisos normalizados desde el índice (`100644`/`100755`), Node 22 de NodeSource, usuario sin privilegios, los pasos EXACTOS de `ci.yml.MANUAL-COPY`:

(Tabla de la réplica de fix4 condensada por el tope de lectura de 256 KiB del ledger: 0 fallos y 0 errores; paralelo 10.490 passed en 1.116 s, serie 1.053 passed en 586 s; el resto de pasos, exit 0.)

`test_npm_payload` (incluido el del PDF) ya no agota nada dentro del contenedor: el timeout de `npm pack` del fixture pasó de 120 a 600 s y sus 5 pruebas pasan en el paso paralelo. **No queda ningún rojo ni «de entorno»**: el del PDF (T-03) se resolvió con T-38 y los 4 *errors* de `npm pack` con el timeout.

Lo que las réplicas anteriores del fix4 encontraron en rojo, y cómo se resolvió cada uno (ninguno se aceptó como «de entorno»; todo es de tiempo de pared, que en un contenedor sobre Docker Desktop es 2-4 veces más lento que en el runner):
- `code-health::test_fix2_gap4_sin_tope_por_ventana_…` (`dur < 1,5 s` con xdist) y sus dos gemelos que miden pared → `@pytest.mark.serie`.
- `test_bench_session_end::test_bench_mide_in_process_no_solo_subproceso` (`p50 < 20 ms`; medido 31 ms en Windows y 58 ms en el contenedor, 14 ms en el runner): la propiedad es «in-process, no subproceso», así que compara la mediana in-process con la e2e (`p50 × 3 < e2e_p50`: 35×, 7× y 30× en las tres máquinas).
- `test_redact::test_bounded_memory_…[curl_args]` (1,5035 s de pared) y `test_redact::test_2_2_lineal_con_muchas_comillas_y_operadores` (2,19 s de pared en el contenedor; el cuadrático tardaba ~18 s): miden CPU (`process_time`) y el segundo con tope 8 s.
- 21 fallos y 3 *errors* en el paso paralelo de una réplica (`test_agent_activity_store`, `test_console_encoding`, `test_local_state_fix3`, `test_panel_privacy`, `test_ledger_view`, `test_local_state`): `deadline_exceeded` del plazo de pared de 1,3 s que el almacén de actividad impone a sus hooks, en un contenedor lento con 4 trabajadores; pasan todos en serie (1.060 passed, 0 failed en ese subconjunto) → esos módulos van al paso `-m serie`.
- `test_la_puerta_rechaza_la_regex_cuadratica_…`: la aserción `tc >= suelo` comparaba contra el mínimo de las muestras y no contra la primera medida.

**fix5 (revisión de dos lentes, intento 5: gaps 5, 9 y 10)** — clave de medición `plugin-audit-2/T-23-fix5`. Diseño fijado por el orquestador (punto 7): los plazos se inyectan, no se miden contra el reloj. Se añade a `Archivos`: `agent-kits/shared/agent-activity-store.py` (escala de plazos inyectable por entorno, sin cambiar los plazos reales) y `agent-kits/shared/test_redact.py`.

RED: `tests/test_agent_activity_store.py -k "inyectar or no_corren_enteros"` falló antes del código con `AttributeError: module 'agent_activity_store' has no attribute 'LIFECYCLE_DEADLINE'` (el plazo de 1,3 s y los de 1 s del almacén estaban fijos: la suite no podía inyectarlos) · 2026-11-12; el segundo test (`test_los_ficheros_de_actividad_y_consola_no_corren_enteros_en_serie`) comprueba que ni `test_agent_activity_store.py` ni `test_console_encoding.py` llevan `pytestmark = pytest.mark.serie` de fichero: contra el contenido de `HEAD` ambos lo llevan (verificado con la misma expresión regular sobre `git show HEAD:…`). Línea base medida (réplica Linux del fix4): paso serie 586 s con 1.053 tests (761 de `test_console_encoding` 197 s, 240 de `test_agent_activity_store` 127 s, 27 de `test_redact_fix3`); la Verificación de la tarea («< 50 % del serie, anotado en `testing/perf.md`») dejaba de cumplirse.

**Estado fix5 (cierre anticipado; `en-progreso`, commit `WIP fix5` 1416211)** — hecho sin medir en Linux: punto 7 parcial: `agent-activity-store.py` lee `CUSTOM_AGENTS_ACTIVITY_DEADLINE_SCALE` (1..60; sin variable, plazos reales), `test_agent_activity_store.py` y `test_console_encoding.py` sin `pytestmark` serie de fichero y con la escala inyectada (el diagnóstico previo `lx8` mostró que solo 2 tests fallaban bajo `-n auto`, ambos por ese plazo); puerta de redact: `SUELO_CPU` 0,02 s en Linux (0,1 en Windows), 1 muestra en la primera ronda, demostraciones con `SUELO_DEMO`; gap 9: quitadas las dos aserciones tautológicas (sustituidas por idempotencia al tamaño tope y `tg > tc`) y `test_2_2` baja de 8 a 6 s (punto medio geométrico entre 2,2 s lento y ~18 s cuadrático). Medida en Windows con otra carga: serie de `test_redact_fix3` antes 441 s (1 rojo: el n^1,5 dio 2,38 < 2,5 bajo carga, el demo costaba 78 s). Falta: medir el paso serie en la réplica Linux (objetivo ≤ 90 s; no comprobado), estabilidad de la puerta con el suelo nuevo (10 pasadas), decidir si la referencia lineal sobre entrada menor se hace (no se aplicó; la referencia cuesta poco frente a redact sobre el grande, sin medir), comprobar que `test_d2_burst…` (serie, falló una vez en Windows bajo carga) sigue verde, y pasar a `completado` solo con la Verificación de T-23 cumplida. testing/perf.md es del orquestador.

**Cierre fix5 (ciclo fix5b, 2026-11-13)** — commits: `50a125b`, `ce45708` y anteriores (ver `git log --grep "fix5b"`). Réplica Linux COMPLETA de `ci.yml.MANUAL-COPY` sobre `HEAD` `2c75a87` (`python:3.11-slim`, un contenedor `-m 1g --cpuset-cpus 0-3`, `git archive` normalizado a LF, permisos del índice, Node 22 de NodeSource, usuario sin privilegios; host compartido con otros contenedores ajenos):

(Tabla de la réplica de fix5b condensada por el tope de lectura de 256 KiB del ledger: 0 fallos y 0 errores en todos los pasos; paralelo 11.812 passed en 767 s; total 12.379 passed, 92 skipped, 1.032 s.)

Frente a la tabla anterior (CI vieja 1.503 s = bucle 163 s + pytest serie 1.340 s): pytest paralelo + serie = 832 s (**55 % de 1.503 s**, 62 % de 1.340 s) con 677 tests más (11.867 frente a 11.190); el paso paralelo medía 615 s con el host libre y 734 s con carga en la medida de T-23, y esta réplica corrió en un host compartido con otros contenedores ajenos (visto uno al 110 % de CPU en una medida anterior); el suelo del paralelo sigue siendo `test_task_brief::test_ca08…` (195 s, recorre todos los ledgers de `docs/roadmap/`, crece con cada iniciativa). **La Verificación literal «< 50 %» NO queda demostrada en esta máquina**: 55 % de la CI vieja medida sobre pytest+bucle, 45 % era el dato de la medida original sobre un host libre. Se deja `en-progreso` para decisión del orquestador (medir `testing/perf.md` con el host libre).

Lo que se cambió y por qué (cada rojo de las réplicas se investigó; ninguno se aceptó como «de entorno»):
- **Paso serie 172 s → 65 s**: dos causas. (1) La recolección de los 11.900 tests costaba ~70 s para ejecutar 56: el paso serie lista con `grep -rl --include='test_*.py' 'mark\.serie'` los ficheros con el marcador y solo recoge esos (`test -n "$archivos"` impide que una lista vacía recoja todo el repo; `-m serie` sigue filtrando dentro de cada fichero, así que no se pierde ninguno; `ci.yml.MANUAL-COPY` y `.github/workflows/ci.yml` idénticos; test nuevo `test_el_paso_serie_solo_recoge_los_ficheros_con_el_marcador`, RED `0e15ef9`). (2) La puerta de redact: la referencia lineal se mide sobre una base fija repetida (`BASE_REFERENCIA`, ×r y ×16r, en vez de sobre cada entrada), la idempotencia se comprueba sobre una salida pequeña y la demostración cuadrática corre una ronda.
- **`test_d2_burst…` verde** en la réplica (4,5 s) y en el paso serie completo.
- **La puerta de redact, estabilizada con 20 pasadas** (`pytest tests/test_redact_fix3.py -m serie`, 26 tests): Linux (`python:3.11-slim`, 12 bucles de CPU sobre 4 CPU) **10/10 verdes** (70-145 s por pasada) y Windows con 6 bucles de CPU **10/10 verdes** (181-304 s). Antes de llegar ahí las pasadas dieron rojo y cada rojo tuvo causa: (a) la demostración n^1,5 con reloj real daba razón 1,26/1,47/1,71/2,3 bajo carga (la separación es 4 frente a 2,5: el ruido solo la acerca) → se demuestra con un **reloj de CPU simulado** y determinista (`test_la_puerta_rechaza_un_n_a_la_1_5_simulado`: lineal = 1,00, n^1,5 = 4,00, cuadrático = 16,00 frente al umbral 2,5) y la lineal real y la regex cuadrática real reintentan hasta 3 veces; (b) `SinSuelo` por muestras de CPU «inválidas» con el divisor ÷8 en Linux → ÷64 (el reloj de Linux es de ns) y la referencia se recalibra en cada ronda; (c) referencia de Windows de 1 tick (`rc=[0.0]`) → mínimo de 0,06 s; (d) razón 3,69 y 3,89 a un caso lineal por una referencia desviada → la puerta toma el **menor de dos estimadores** (razón corregida por la referencia y razón cruda `tg/tc/16`); (e) el suelo se cruzaba con un pico y las muestras reales eran 6 veces menores → el suelo se **confirma con una segunda medida**. `test_las_muestras_invalidas_se_descartan` usa `VALIDA_DIV` y `test_una_muestra_de_cpu_a_cero…` acota la razón a `< 1000` (el bug original daba 5,6e7).
- **Fallos de la réplica completa, todos arreglados**: el pin `sha256_lf` de `agent-kits/shared/agent-activity-store.py` en `test_graphiti_security.py` (4 tests; el commit `WIP fix5` 1416211 añadió la escala de plazos, sin red ni cargas nuevas; nuevo hash comentado); capturas de subproceso en texto sin `encoding=` en el corpus diferencial (`test_console_encoding`); `bounded_memory[curl_args|mysql_args]` con tope absoluto de CPU de 1,5 s dio 1,60 y >2,5 s con carga → ahora mide la CPU del caso **relativa a una referencia lineal medida en el mismo hijo** (`RAZON_CPU_MAX = 25`; razones medidas libre 1,0-8,0 y con 12 bucles 1,0-9,5: la máquina escala a las dos); 1 fallo de `node --test` en una réplica anterior (sin registro de qué prueba) que no se repitió en las dos siguientes (`512 pass, 0 fail`) — se dejó el log de node persistido para la próxima réplica.

GREEN: `pytest -q tests/test_ci_manual_copy.py tests/test_ci_skill_suites.py tests/test_suites_no_pytest.py` → verde en la réplica Linux (los tres ficheros corren en el paso paralelo: 0 failed) y, en Windows, `test_ci_manual_copy` + `test_ci_security` + `test_ci_skill_suites` → `21 passed` y `test_suites_no_pytest -k "serie or ci or paraleliza or bucle"` → `10 passed` (incluye el test nuevo del paso serie; la suite entera no había terminado a los 31 min en Windows por sus suites-script y se cortó); réplica Linux completa: ver tabla (0 fallos en todos los pasos); `python3 scripts/export-interop.py --check` → `88 ficheros al día`. Medición `close` de `plugin-audit-2/T-23-fix5`: ventana compartida (`2.53 h` IA medidas en total entre T-06, T-07 y T-23).


RED: `pytest -m serie (réplica Linux python:3.11-slim, fix5b)` falló con el paso serie costaba 172 s (objetivo ≤ 90): 68 s de recoleccion de 11.900 tests para ejecutar 56, 48 s en las dos demostraciones de la puerta y ~42 s en los 23 casos; y la replica completa dio 7 fallos en el paralelo (pin de agent-activity-store.py, muestras invalidas con la division por plataforma, capturas de subproceso sin encoding) y 2 en el paso serie (bounded_memory con tope absoluto de CPU bajo carga) · 2026-11-13.

**fix6 (revisión de dos lentes, intento 6: gaps 7, 13, 15 y 16; decisión del usuario: la puerta de redact rechaza solo cuadrático o peor)** — clave de medición `plugin-audit-2/T-23-fix6`. Sin ficheros nuevos en `Archivos` (`agent-kits/shared/agent-activity-store.py` y `tests/test_graphiti_security.py` por el pin de hash del gap 13).

RED: `tests/test_redact_fix3.py -k "criterio or separa or mediana or peor_que or umbral"` falló antes del código con `5 failed, 1 passed` · 2026-11-13 (umbral 2,5 y `min` de las muestras: una muestra pequeña atípica volvía rojo un lineal; el cúbico se medía con la entrada ×16; `INTENTOS_DEMO` seguía reintentando) y `tests/test_agent_activity_store.py -k escala_de_plazos` con `1 failed` (la escala de plazos actuaba fuera de una suite).

GREEN: commits `1cf29b3`, `c23d80b`. Puerta de redact (`tests/test_redact_fix3.py`): la razón es la **mediana** de las razones `(t_grande / t_pequeño) / 16` de 2-3 muestras por ronda (con dos muestras de acuerdo no se toma la tercera; una segunda ronda solo si la primera dio rojo), el umbral es **6** (lineal ≈ 1, cuadrático ≈ 16; el n^1,5 ≈ 4 queda FUERA de alcance y el docstring lo dice), sin referencia lineal ni `min` de nada, sin `INTENTOS_DEMO`; sonda ×4 antes de ejecutar la entrada grande (un cúbico o peor se rechaza sin ejecutarla), pausa entre rondas de 1 s y suelo de CPU de Windows de 0,05 s (con 0,1 s una pasada tardaba 7 min); la aserción tautológica de `test_sin_suelo_alcanzado…` se sustituyó por una que puede fallar (no se midió grande y se llegó al tope de tamaño). La demostración usa el reloj REAL (lineal aceptado, `x*y` cuadrático rechazado) y las de reloj simulado fijan la lógica (mediana con una muestra atípica, cúbico sin ejecutar el ×16, n^1,5 aceptado por diseño). Gap 13: `agent-kits/shared/agent-activity-store.py` solo aplica `CUSTOM_AGENTS_ACTIVITY_DEADLINE_SCALE` con `PYTEST_CURRENT_TEST` presente (marca de test explícita que pytest exporta y heredan los subprocesos); el pin `sha256_lf` de `tests/test_graphiti_security.py` se actualizó. Gap 16: se quitó `Cerrada: 2026-11-11`, la fila «Total» de la réplica de fix5b se corrigió y el resto de la deuda queda anotada en T-06. **Medida emparejada de «< 50 %»: NO la hace este ciclo** (la ejecuta el orquestador con el host en reposo, A-B-A-B, mediana de B/A en `testing/perf.md`); T-23 sigue `en-progreso` solo por esa medida.

**Cierre fix6 (2026-11-13)** — commits: RED `2652b0c`; código `1cf29b3`, `c23d80b`, `f823f0d`; ledger `2a64ee0`. Réplica Linux COMPLETA de `ci.yml.MANUAL-COPY` sobre `HEAD` `2a64ee0` (`python:3.11-slim`, Node 22, un solo contenedor `-m 1g --cpuset-cpus 0-3`, árbol de `git ls-tree` con los blobs en LF, `HEAD` sin tocar), **0 failed / 0 errors en todos los pasos**:

(Tabla de la réplica de fix6 condensada por el tope de lectura de 256 KiB del ledger: 0 fallos y 0 errores en todos los pasos; total 12.723 passed, 92 skipped, 1.284 s.)

Frente a fix5b (paralelo 767 s, serie 65 s, total 1.032 s): el paso paralelo sube 169 s y el serie 40 s. Causas medidas, no cargadas a la carga ajena: el corpus diferencial pasa de 281 a 573 casos (cada uno copia un repo y ejecuta bash real, ~0,5 s), `tests/test_native_guard_failclosed.py` añade 26 pruebas de lanzador (~1,5 s cada una de arranque de node) y, en el paso serie, dos pruebas de plazo agotado (~5 s cada una, 4,5 s de presupuesto del lanzador) y la puerta de redact con mediana; la variación del propio host (los tests más lentos del paso paralelo son los de siempre: `test_task_brief::test_ca08…` 229 s) pone el resto. La medida de «< 50 %» no se juzga aquí: la hace el orquestador con la medida emparejada.


La primera réplica de este ciclo (sobre `c23d80b`) dio 2 rojos reales, ambos investigados y arreglados en `f823f0d` (ninguno aceptado como «de entorno»): `ex <<'EOF'` del corpus `LIMITE` depende de que `ex` esté instalado (en `python:3.11-slim` no lo está, bash no ejecutaba nada: el caso se retiró) y el e2e hostil exigía que la salida no contuviera «unavailable», pero el lanzador emite además el aviso de `branch-unavailable` cuando el directorio de prueba no es un repo git (el deny es lo que importa).

**Puerta de redact: 10 pasadas sin rojo por plataforma con carga** (`pytest tests/test_redact_fix3.py -m serie -x`, 26 tests, `HEAD` `c23d80b` + `f823f0d`; ambas plataformas a la vez):

Linux (`python:3.11-slim`, 4 CPU, **12 bucles de CPU** `while 1: pass`):

10 pasadas, 26 passed cada una, 126-244 s (tabla de fix6 condensada por el tope de lectura de 256 KiB del ledger).

Windows (Git Bash, **6 bucles de CPU**):

10 pasadas, 26 passed cada una, 246-529 s (tabla de fix6 condensada por el tope de lectura de 256 KiB del ledger).


**fix7 (revisión de dos lentes, intento 7: gaps 13 (docstring de la demo), 15 y 16; T-23 sigue `en-progreso`: solo falta la medida emparejada que hace el orquestador)** — clave de medición `plugin-audit-2/T-23-fix7`. Sin ficheros nuevos en `Archivos` (`tests/test_redact_fix3.py`, `tests/test_native_guard_failclosed.py` y `agent-kits/shared/test_guardrail_differential.py` ya estaban cubiertos por fix5-fix6).

RED: `tests/test_redact_fix3.py -k "regex_cuadratica or sonda_x4 or cuadratico_sigue"` falló antes del código (commit RED `1481584`, 2 failed) · 2026-11-14: la demostración con reloj real exigía una razón FINITA con `tope=`/`TOPE_CPU_DEMO` (no existían) y `test_un_inf_de_la_sonda_x4_necesita_confirmacion_antes_del_rojo` (la primera medida ×4 inflada 10× devolvía `inf` para un caso lineal) fallaba.

GREEN: (gap 15) `_medir` confirma un `inf` de la sonda ×4 con una SEGUNDA muestra ×4 (decide con la menor; `_prometido`) antes de dar el rojo, y acepta `tope` (el de un caso grande) y `paso` (factor de crecimiento del tamaño; un cuadrático sube ×paso² por escalón, así que el pequeño aterriza cerca del suelo y el grande no se dispara a decenas de segundos). La demostración con reloj real del cuadrático (`test_la_puerta_rechaza_la_regex_cuadratica_…`) usa `tope=TOPE_CPU_DEMO` (30 s), `paso=1.25` y `rondas=1`, y exige una razón FINITA (`math.isfinite`) y no lineal: la decide la MEDIANA, no la sonda (en Windows sale 22,5 con `tc=0,055 s`, `tg=16,8 s`). Coste de la demostración en Windows: ≈ 88 s (la regex `x*y` cuesta ≈ 16 s en el caso ×16 con el reloj de 15,6 ms); en Linux, con suelo 0,01 s, unos segundos (cifra medida en la tabla de abajo). (gap 13) la docstring de la demo dice «razón ≈ 16» en lugar de «≈ 8». (gap 16) las dos pruebas de plazo con `sleep` y los 3 hostiles por el lanzador pasan al paso paralelo (ver interpretación 7 de T-06); `test_payload_de_30kb_…` sigue en serie por su aserción de tiempo.

**Cierre fix7 (2026-11-14)** — commits: RED `1481584`; código `c4610e9` y `1230bb9`; ledger (el commit que añade este cierre). Réplica Linux COMPLETA de `ci.yml.MANUAL-COPY` (idéntica a `.github/workflows/ci.yml`: `diff -q` sin salida) sobre `HEAD` `1230bb9` (`python:3.11-slim`, Node 22, un solo contenedor `-m 1g --cpuset-cpus 0-3`, árbol de `git archive HEAD` con los blobs en LF, `HEAD` sin tocar), **0 failed / 0 errors en todos los pasos**:

(Tabla de la réplica de fix7 condensada por el tope de lectura de 256 KiB del ledger: 0 fallos y 0 errores en todos los pasos; paralelo 12.529 passed en 937 s, serie 56 passed en 82 s, node 517 passed; total 13.102 passed, 92 skipped, 1.243 s.)

Cómo se llegó a verde: la primera réplica (sobre `c4610e9`, 1.128 s) dio 5 rojos en el paso paralelo y cada uno tuvo causa o tratamiento: (a) `tests/test_graphiti_security.py` ×2: el pin `_LAUNCHER_NODE_HASH` de `hooks/run-hook.mjs` (el lanzador cambió; revisado: lee la entrada y busca la clave del rol con una regex, sin red ni procesos nuevos; pin actualizado); (b) `tests/test_console_encoding.py`: un subproceso en modo texto sin `encoding=` en el corpus 7 (corregido); (c) `agent-kits/shared/test_ledger_view.py::test_mil_tareas_…`: aserción de 2 s de pared que tardó 10 s en el paso paralelo cargado (llevaba el mismo defecto que su hermana de 5.000 filas, que ya era `serie`: pasa a serie); (d) `agent-kits/shared/test_journal.py::test_replay_con_recover_max_n_se_reparte_entre_drenaje_y_recuperacion` (`assert 2 == 3`, una sola vez en 12.530 tests): NO se pudo reproducir (0 fallos en 40 ejecuciones aisladas con 12 bucles de CPU y 6/6 sueltas con 8 bucles, y verde en la segunda réplica completa) y su código no lo toca esta iniciativa: causa NO identificada, anotada como aviso (posible dependencia de reloj/orden en el drenaje de la outbox bajo carga). La segunda réplica, con (a)-(c) corregidos, dio verde completo.

Frente a fix6 (paralelo 936 s, serie 105 s, total 1.284 s): el paralelo es igual (937 s), el serie baja 23 s (82 s: 56 pruebas en lugar de 60, porque las dos pruebas de plazo y los 3 hostiles por el lanzador salieron del paso serie, gap 16) y el total baja 41 s. El corpus diferencial pasa de 573 a 809 casos (paridad con bash real) y la demostración con reloj real del cuadrático pasa por la mediana (10,8 s en Linux, `test_la_puerta_rechaza_la_regex_cuadratica…`). La medida emparejada «< 50 %» de T-23 la hace el orquestador; T-23 sigue `en-progreso`.

**Puerta de redact: 10 pasadas sin rojo por plataforma con carga** (`pytest tests/test_redact_fix3.py -m serie -x`, 26 tests, `HEAD` `1230bb9`, ambas plataformas a la vez; la sonda ×4 se confirma con una segunda muestra y la demostración con reloj real da una razón FINITA):

(Tabla de fix7 condensada por el tope de lectura de 256 KiB del ledger: Linux 10/10 pasadas con 26 passed, 122-183 s; Windows 10/10 con 26 passed, 173-425 s.)

Horas medidas de fix7 `(medido)` (ventana compartida entre T-06, T-07 y T-23; se imputan a T-06): 1.33 h (`plugin-audit-2/T-06-fix7`), 1.33 h (`T-07-fix7`) y 1.33 h (`T-23-fix7`).

**fix8 (revisión de dos lentes, intento 8: gaps 3, 10, 11, 12, 13 y 9; T-23 sigue `en-progreso`: falta la medida emparejada, que hace el orquestador)** — clave de medición `plugin-audit-2/T-23-fix8`. Gap 9: `Archivos` completado (`test_ledger_view.py` y `tests/test_graphiti_security.py`; el «sin ficheros nuevos» de fix7 era falso).

- **Demo de redact** (gaps 10 y 11): ×4 con caso pequeño de 0,08 s y 2 muestras (11 s en Windows sin carga, antes 53 s), margen del tope 30 s ≥ 5× la muestra típica (comprobado por un test) y `inf` por tope y segunda sonda ×4 confirmados tras la pausa. Ver las 10+10 pasadas de arriba (T-06, fix8).
- **Coste del corpus** (gap 12): `_estado_plantilla` (una vez por plantilla) y `_tiene` con caché.
- **Journal** (gap 13): `journal-io.py` lee `CUSTOM_AGENTS_JOURNAL_IO_DEADLINE_SCALE` (1 a 60) solo bajo `PYTEST_CURRENT_TEST`; producción sin cambios (5 s). `test_replay_con_recover_max_n…` la usa y `test_journal_io_deadline.py` fija con un fsync de 6 s de reloj simulado que sin escala se pierde la escritura y con escala no.
- **Gap 3:** la prueba de plazo del lanzador vuelve al paso serie (ver T-06).
- **Rojo de la réplica (1 de 12.778):** `test_panel_review_panel_server.py::test_con_el_dueno_real_refresh_y_submit…` falló en el paso paralelo con `KeyError: 'review_id'`: `review_open` tiene un plazo de pared de 3 s (`BODY_TIMEOUT`) y devuelve 503 sin `review_id` si se agota bajo `-n auto`; pasa suelto (3/3). Misma clase que el resto de T-23: las dos pruebas que abren una revisión con el dueño real pasan al paso serie.

**Cierre fix8 (2026-11-14)** — commits: RED `ccb914b`; código `3bc278b`, `272c284` y `e7fa3f3`; ledger (el commit que añade este cierre). Réplica Linux COMPLETA de `ci.yml.MANUAL-COPY` (`python:3.11-slim`, un contenedor `-m 1g --cpuset-cpus 0-3`, Node 22, árbol de `git archive` en LF). La primera réplica (sobre `272c284`) dio 1 rojo (el de arriba) y un intento previo se mató por OOM (`--cpus 4` en lugar de `--cpuset-cpus 0-3`: xdist veía 16 núcleos); esta es la de `e7fa3f3`:

| Paso de la CI | Resultado | Segundos |
|---|---|---|
| Linter | exit 0, `10 agentes · 0 errores · 16 avisos` | 8 |
| `check-handbook` | exit 0 | 0 |
| Evals estáticos | exit 0, `227 casos · 0 errores` | 0 |
| pytest `-n auto -m "not serie"` | 12.776 passed, **0 failed**, 0 errors, 67 skipped | 909 |
| pytest serie | 60 passed, **0 failed** | 88 |
| Bench SessionEnd | exit 0, `p50=19.8ms`, `p95=48.4ms`, `p99=57.05ms` | 2 |
| `export-interop --check` | 88 ficheros al día | 0 |
| `node --test` | 522 pass, **0 fail**, 25 skipped | 225 |
| Sintaxis `.py` | exit 0 | 6 |
| JSONs + `release.py --check` | exit 0/0 | 1 |
| **Total** | 13.358 passed, **0 failed**, 92 skipped | **1.239** |

Horas medidas de fix8 `(medido)` (ventana compartida entre T-06, T-07 y T-23; se imputan a T-06): 1.55 h (`plugin-audit-2/T-06-fix8`, `T-07-fix8` y `T-23-fix8`).

**fix9 (revisión de dos lentes, intento 9: gaps 2, 5 y 6; T-23 sigue `en-progreso`: falta la medida emparejada, que hace el orquestador)** — clave de medición `plugin-audit-2/T-23-fix9`. RED y commits: los de T-06 (`0abe812`, `d5d3eed`, `4d8076d`).

- **Journal** (gap 2, punto 2): `test_replay_con_recover_max_limita…` ya no usa el reloj de pared: fija la escala inyectable del fix8 (60 s para la E/S), un presupuesto de trabajo de 120 s y asserta el TOPE (3 recuperadas y 3 entradas de 100 huérfanas); la aserción `dur_ms < 5000` desaparece. **Inventario de aserciones de pared de `test_journal.py`** (4, todas tratadas; un test nuevo, `test_fix9_plazos_inyectados.py`, vigila que no vuelvan): `test_replay_termina_dentro_del_presupuesto_con_0_10_100_pendientes` (`dur_ms < 5000`: quitada, las cotas por efecto `materializados <= min(n, 3)` y `restantes` se conservan), `test_replay_cerrojo_ocupado…` (`elapsed < 1.5`, POSIX: el hilo sostiene el cerrojo hasta que el test lo suelta y se comprueba que `replay` vuelve con él tomado; 60 s solo evitan colgar el test), `test_replay_con_recover_max…` (la de arriba) y `test_recover_cerrojo_ocupado…` (`elapsed < 1.0`, POSIX: mismo patrón, `recover` en un hilo). Otras dependencias del presupuesto sin aserción de duración, que no se tocan: `replay(budget_ms=100)` y `recover(budget_ms=300)` esperan 1 materializada o recuperada (holgadas: ver las pasadas) y los tests de cerrojo ocupado esperan `bloqueado`, que no depende del reloj.
- **Panel** (gap 5, punto 5): las dos pruebas que abren una revisión con el dueño real inyectan `BODY_TIMEOUT` (120 s, `monkeypatch.setattr(service, 'BODY_TIMEOUT', …)`, como `test_panel_review_server.py:227`) y vuelven al paso paralelo (sin `@pytest.mark.serie`; un test comprueba ambas cosas).
- **Demo de redact** (gap 6, punto 6): la aserción es la decisión real de la puerta, `not _es_lineal(relativa)` (umbral 6); la razón de un cuadrático es ≈ el crecimiento `c`, así que con ×4 no podía salir rojo. Configuración: ×12 (144×), caso pequeño de un tick (0,0156 s) promediado en 64 repeticiones, 3 muestras con mediana y 1 s de calentamiento. La sonda ×4 de `_medir` extrapolaba SIEMPRE al coste de ×16: ahora extrapola al crecimiento real (un test con reloj simulado lo fija). Tope de la demo 60 s (margen 5× sobre la muestra típica pesimista, ×3 = 6,7 s) y cota de coste `<= 12 s` en el test del margen. Se probaron ×8 (peor razón 8,6), ×10 (7,9 a 9,0), ×12 con 1 muestra (8,7 a 9,6), ×14 con 1 muestra (9,9 a 12,0) y ×12 con 3 muestras; la elegida se mide con la MISMA configuración que el test.

Medidas de fix9: demo de redact (Windows, sin carga, 10 ensayos) razón peor **10,90** (umbral 6; 1,5× = 9) y mejor 13,42, 3,9 a 11,7 s; test por pytest 8,5 · 10,8 · 12,7 s. Con carga: Windows (6 bucles) 10/10 verdes, 11,9 a 19,6 s; Linux (`python:3.11-slim`, `-m 1g --cpuset-cpus 0-3`, 12 bucles sobre 4 CPU, `git archive` en LF) demo 10/10 (11,4 a 90,3 s) y `test_journal.py -k replay` 20/20 (`38 passed`; Windows 20/20, `37 passed`).

**Cierre fix9 (2026-11-14)** — commits: RED `0abe812`; código `d5d3eed` y `4d8076d`; ledger `9ce621e` y el que añade este cierre. Réplica Linux COMPLETA de `ci.yml.MANUAL-COPY` (idéntica a `.github/workflows/ci.yml`: `diff -q` sin salida) sobre `4d8076d` (`python:3.11-slim`, un solo contenedor `-m 1g --cpuset-cpus 0-3`, Node 22, `git archive` con los blobs en LF, lanzada con 3,28 GB libres tras esperar a que hubiera ≥ 3 GB), **0 failed / 0 errors en todos los pasos**:

Pasos (todos exit 0): linter 0 errores · `check-handbook` · evals 227 casos · pytest paralelo 12.903 passed (510 s) · serie 58 passed (111 s) · bench `p95=18,47 ms` · interop 88 al día · `node --test` 524 pass, 25 skipped (148 s) · sintaxis · JSONs + `release.py --check`. **Total 13.485 passed, 0 failed, 92 skipped, 777 s.**

Las dos pruebas del panel que abren una revisión con el dueño real pasan en el paso paralelo (`-n auto`) a la primera: sin ellas en el paso serie (60 → 58 pruebas serie, 12.776 → 12.903 en paralelo con los tests nuevos). Windows, los mismos tests tocados: 2.157 passed (guardarraíl, diferencial con bash real y paridad), 204 (journal), 245 (panel y meta), 58 (nativo Python) y 44 node, 0 failed.

Puertas finales: `ledger-lint` 0 incoherencias; `scope-check.py … --base 57fb054` exit 0; `lint_plugin` 0 errores; `check-handbook` y `export-interop --check` al día; `ci.yml.MANUAL-COPY` idéntica a `.github/workflows/ci.yml`.

Horas medidas de fix9 `(medido)` (ventana compartida entre T-06 y T-23; se imputan a T-06): 3.22 h (`plugin-audit-2/T-06-fix9` y `T-23-fix9`).

**fix10 (intento 10, gaps 7 a 9; condensado en fix12 sin perder cifras)** — `plugin-audit-2/T-23-fix10`; commits: los de T-06. Presupuestos cortos (gap 7): `replay(budget_ms=100)` y `recover(budget_ms=300)` congelan `time.monotonic` (`_reloj_congelado`); el vigía `test_fix9_plazos_inyectados.py` comprueba por AST que ningún test con `budget_ms` < 1000 usa el reloj real, salvo los 5 de cerrojo ocupado. Comentarios de la demo (gap 8): 10,90 (mejor 13,42), 3 muestras, ×12, pesimista ×3 = 6,7 s. Carrera del journal (gap 9, `debug-root-cause`): reproducida con dos `replay(con_recover)` simultáneos (hilo con excepción en 6 y 2 de 40 rondas); causa raíz: el inicializador ganador de `.custom-agents-journal`/`.gitignore` los crea con `os.link(temporal, destino)` y el inodo tiene DOS enlaces hasta borrar el temporal, y la guarda `nlink == 1` lanzaba `unsafe_state` a `replay`/`capture` (defecto real, sin pérdida de datos); arreglo: `settled`/`read_settled` esperan a que se asiente y nunca adoptan el enlace (un enlace duro persistente sigue lanzando `unsafe_state`), 0 errores en 60 rondas (mutante sin espera: 6 y 2 de 40). Réplica Linux COMPLETA sobre `e13b5e5` (`python:3.11-slim`, `-m 1g --cpuset-cpus 0-3`, Node 22, LF, ≥ 3 GB libres), **0 failed / 0 errors**: linter 0 errores, 16 avisos (4 s) · `check-handbook` · evals 227 · pytest paralelo 13.001 passed, 71 skipped, 87 subtests (586 s) · serie 58 passed (86 s) · bench `p50=15,67 p95=19,13 p99=21,28 ms` · interop 88 · `node --test` 528 pass, 0 fail, 25 skipped (109 s) · sintaxis y JSONs + `release.py --check`; total 789 s. `env -S` frente a coreutils 9.7: 42 formas, 0 diferencias no ambiguas y 8 con LF/VT/FF/CR suelto que 9.x separa y se deniegan; 5/5 pasadas de journal con 12 bucles de CPU. Rojos de réplicas anteriores, ninguno aceptado como «de entorno»: paridad de `env -S` con 9.7; `test_dataset_assembler::…3_serializaciones` comparaba tiempos de PARED (`_medir` usa CPU con 8 repeticiones); `test_knowledge_read_context::test_refresh_…` agotó 1,2 s de pared (el proyecto pide 30 s salvo 4 tests); `rmdirSync` en `ENOTDIR` (ahora `unlink`). Windows: guardarraíl, diferencial y paridad 1.349 passed, journal 278, node 174, `test_graphiti_security`. Horas medidas de fix10 `(medido)` (ventana compartida; se imputan a T-06): 1.21 h.

**fix11 (intento 11, gaps 8 y 10; condensado en fix12)** — `plugin-audit-2/T-23-fix11`; commits: los de T-06 más `945a4fc` y `f007327`. Espera de `settled` acotada (gap 10): `journal-io.initializing(path)` es True solo con un `.tmp-*` hermano del mismo (dispositivo, inodo) y reciente (< 5 s); `settled`, `queue` y `update` esperan únicamente así (`settling`: un enlace, inicialización en curso o temporal recién borrado); un enlace duro plantado o de un inicializador muerto falla con `unsafe_state` en < 50 ms (antes 0,75 a 0,87 s, que en SessionEnd agotaban los 800 ms del hijo). Rama de escritura (gap 8): el `unsafe_state` de `IO.read` entre el `lexists` de `_asegurar_gitignore_local` y el de `write` pasa a `read_settled`; sin pérdida. RED: 4 tests de `test_journal.py` (plantado < 50 ms en `read_settled`/`queue`/`_asegurar_gitignore_local`; `.tmp-` de otro inodo; `.tmp-` viejo con reloj adelantado; rama write con la carrera simulada). La primera versión (`945a4fc`) rompió `test_audit_journal::test_first_prompts_survive_the_atomic_link_publication_window` (el ganador borra su temporal entre las dos lecturas); `settling` relee el enlace tras el escaneo (`f007327`).

**fix12 (intento 12, gaps 2, 5 y 6; T-23 sigue `en-progreso`: falta la medida emparejada, del orquestador)** — `plugin-audit-2/T-23-fix12`; commits: los de T-06 más `d3a9764` (RED), `da384fb` (journal) y `4c52705` (instalador).
- **Espera acotada en tiempo total** (gap 6): `settled` y `update` toman `_ESPERA_MAX = 0,75 s` de reloj monotónico al empezar y, pasado el tope, lanzan el `unsafe_state` original (`journal_update_conflict` en `update`): cada intento lista el directorio y 40 intentos con un `.tmp-` vivo eran 4,9 s con 10 K entradas + 1 K `.tmp-`. RED (`d3a9764`): 3 fallan (`read_settled` y `update` con reloj inyectado, 4,73 s simulados y > 10 listados; 10 K + 1 K de CPU); GREEN: pasan, con 10 K + 1 K bajo 1 s de CPU.
- **Sin reloj de pared** (gap 5): los tres `< 0.05` de `test_journal.py` cuentan las dormidas con `_reloj_inyectado` (sustituye `JIO.time` por un reloj propio; ni una dormida cuando no hay inicialización en curso).
- **Instalador en Windows** (gap 2, `debug-root-cause`): causa raíz **no** en la CLI colgada. Con `CUSTOM_AGENTS_EXEC_TIMEOUT_MS=2000` el instalador completo tardó 13 s en reposo y 36 s con 12 bucles de CPU: 7 s (30 s con carga) son la colocación de los 495 ficheros ANTES de lanzar la CLI (perfil de CPU: `rename` 3,3 s y `spawnSync` 5,1 s), y solo 5 a 6 s son el plazo de 2 s + `taskkill` + PowerShell; la cota de 30 s abarcaba el disco. El test viejo, con 12 bucles de CPU, dio rojo en 43,7 s; el nuevo mide desde que arranca el `codex` colgado (el stub marca `inicio.flag`; cota de 30 s intacta) y pasa. Interpretación: no se cambia `install.mjs` porque la hipótesis del `--version` de 15 s ×2, del shim `sh` y del árbol sin matar quedó descartada con medidas (`taskkill` + PowerShell 1,5 s).

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

## Revisión de dos lentes — intento 12: Fase 1 (T-06, T-07, T-23) — verificación dirigida del fix11: 2 Important, 9 Minor

Lentes: A+B+C+D sobre `e4b2f7f..a5ba181`, dos a dos por memoria. Más la suite node de Windows, que corrió el orquestador.

**Cerrado del intento 11:**
- Los gaps 1 a 12.
- **Lista blanca de `case`.** Fuzz de la Lente B con 67.584 órdenes: git en el cuerpo, 16 cabeceras, 11 patrones, 3 terminadores y 8 envolturas. Da 0 regresiones frente a d938cab y frente a 8e7c0a0. Las 31 formas en bash real ejecutan git y el guard las deniega.
- **Coste lineal.** `bang_64k` pasa de 97,8 s a 0,33 s. A 256 KB todo queda por debajo de 0,8 s.
- **Journal.** Un enlace duro plantado sin `.tmp-` falla en 16-124 ms.
- **OpenCode.** Un `realpath` indeterminado guarda la sesión.
- **`implementer.md:92`.** Corregido.
- **RED real.** Con el código de e4b2f7f fallan 29 tests y pasan 18; en HEAD pasan 47.

**Interpretaciones aceptadas:**
- **i1:** un `ENOENT` es una respuesta cierta. Un UNC inalcanzable da `UNKNOWN`, que es indeterminado.
- **i2:** `x=1 case …` es un error de sintaxis en bash.
- **i5:** el deny nuevo alcanza formas plausibles como `git log -- $(grep -rl case src)`. Es lo que pide el diseño: ante la duda, deny.
- **i6.**

**Rojo fuera de las lentes, en Windows.** El orquestador corrió la suite node completa.
- `tests/codex-plugin-state.test.mjs`: la regex no aceptaba CRLF. Lo corrigió el orquestador en `6e41dfe`, declarado en `Archivos` de T-23.
- `tests/installer.test.mjs`: 184 pass y 1 fail (gap 2).

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | **Regresión del fix11.** Al buscar el cierre de `$'…'`, `_ansi_c` hace que `\c` consuma un carácter más. Bash delimita la cadena por pares `\X` y decodifica `\cX` después. `echo $'\c'; git reset --hard #'` → allow, cuando en d938cab y 8e7c0a0 daba deny. Bash real ejecuta git. Lo mismo con `\c\\`, `\c\' x` y `x=$'\c' && …`. Verificado por el orquestador | T-06 | fix12 `8105752` (RED `28f1308`): `_ansi_fin` delimita por pares `\X` y `_ansi_decodificar` decodifica después; diferencial generado 0 divergencias; las formas de `lb12` entran en `BAD12_PARIDAD` | Lente B: `guardrail-check.py:424-425,509-510`; `lb12/rb2.py`, `c1`-`c5` |
| 2 | Important | Rojo en Windows: `installer.test.mjs:1909` («gap 8: una CLI colgada no bloquea el instalador»). Con `CUSTOM_AGENTS_EXEC_TIMEOUT_MS=2000`, el instalador tardó 30.163 ms (la cota es < 30.000). Pasa en Linux. La causa no está aislada | T-23 | fix12 `4c52705`: causa raíz medida (colocar los 495 ficheros, no la CLI colgada); el test mide desde el arranque del `codex` colgado, cota de 30 s intacta | Orquestador: `node --test tests/installer.test.mjs` en Windows, 184 pass y 1 fail en 1.624 s; `install/install.mjs:1294,1301,1315` |
| 3 | Minor | **Regresión del fix11, fallo abierto en la ruta heredada.** `$'\ud800'` se decodifica a un surrogate suelto. `_destino_es_el_propio_directorio` solo captura `OSError`, y en POSIX `realpath` lanza `UnicodeEncodeError`. El `except Exception` de `main()` acaba en allow. `cd $'\ud800'; git reset --hard` → allow en `guardrail-check.py pre-tool`, la única protección en modo copia; en e4b2f7f era deny. La ruta nativa falla cerrada | T-06 | fix12 `8105752`: `(OSError, ValueError)` en el destino; una excepción interna de `main()` en `pre-tool` deniega con motivo explícito | Lente C: `guardrail-check.py:1250-1253,2066`; `lc12/sur2.py` |
| 4 | Minor | `_ansi_c` no implementa `\x{H…}`, que bash 5.2 sí decodifica. `bash -c $'\x{67}it reset --hard'` → allow, y ya era así en las tres versiones. Contradice «semántica de bash» (`implementer.md:102`). Ofuscación deliberada | T-06 | fix12 `8105752`: `\x{H…}` con cualquier número de cifras módulo 256 (medido con bash 5.2.37); `BAD12_LLAVES` | Lente C: `guardrail-check.py:413-422`; `lc12/p3.sh` |
| 5 | Minor | Test intermitente: `dt < 0.3` con reloj de pared. En reposo da 0,28 s; con 12 bucles de CPU falla 2 de 3 veces (0,51 s). Los `< 0.05` de `test_journal.py:3322,3332,3342` tienen un margen parecido | T-06, T-23 | fix12 `8105752` y `d3a9764`: CPU del proceso + razón de linealidad en el guardarraíl; reloj inyectado en el journal; 20/20 pasadas con 12 bucles de CPU, 0 rojos | Lentes B y D: `test_guardrail_fix11.py:80-87,92-103` |
| 6 | Minor | Con un `.tmp-` vivo, la espera de `settling`/`initializing` vuelve a listar el directorio en cada uno de los 40 intentos. El coste deja de estar acotado a unos 0,75 s: 1,55 s con 2.000 entradas y 4,9 s con 10 K + 1 K `.tmp-`. En SessionEnd (800 ms) el hijo muere en vez de dar un error limpio. Solo en un estado anómalo | T-23 | fix12 `da384fb`: tope total de 0,75 s de reloj monotónico en `settled` y `update`; 10 K + 1 K bajo 1 s de CPU | Lente D: `journal-io.py:92-93,135,185`; `ld12/j1.py` |
| 7 | Minor | Tres ramas de deny nuevas sin RED previo ni declaración: `\U` fuera de rango, patrón vacío y separador en los estados `w`/`i`. Todas son sintaxis inválida; el defecto es de traza | T-06 | fix12 `28f1308`: 5 tests de regresión de las tres ramas; declarado en T-06 (pasan contra a5ba181, no son un RED) | Lente A: `guardrail-check.py:421,625,660`; `la12/nr.py` |
| 8 | Minor | Recuentos del ledger desfasados: `BAD11_PARIDAD` tiene 59 formas (no 60) y `SIN_PARIDAD_11` 8 (no 7). En el RED fallan 29 de 47 tests, no 27 de 45 | T-06 | fix12: recuentos corregidos en T-06 (59 y 8; 29 de 47) | Lente A: `tasks.md:368` |
| 9 | Minor | El modelo de amenaza no nombra la clase `LIMITE11`, una sustitución como palabra de mando: `$(true) git reset --hard` | T-06 | fix12 `6dc998c`: `LIMITE11` en el modelo de amenaza de `implementer.md` | Lente A: `implementer.md:100-111` |
| 10 | Minor | Un `realpath` indeterminado (EACCES, EIO, ELOOP) también guarda las sesiones ajenas durante 5 s: entre 1,0 y 1,5 s de hook por evento | T-06 | deuda aceptada (compromiso del gap 9 del intento 11: guardar de más solo ejecuta el guard) | Lente D: `opencode-plugin.js:81-94` |
| 11 | Minor | El corpus con bash real crece en 64 ejecuciones, unos 80 s más en Windows. Es el método establecido y no tiene `sleep` evitables | T-23 | deuda aceptada (solo si hay que recortar CI) | Lente D: `test_guardrail_differential7.py:437,450` |

**Avisos de método.**
- `bash.EXE -c` lanzado desde Python en Windows altera las barras invertidas. Las sondas con escapes van en ficheros `.sh`.
- En Linux, el primer test de `opencode-realpath-fix11` (`:36-53`) no discrimina, porque no hay nombres 8.3.

**Diseño fijado por el orquestador para fix12:**

1. **`$'…'` como lo lee bash** (gaps 1 y 4).
   - Primero se delimita la cadena por pares `\X`, como el lexer de bash.
   - Después se decodifica el contenido ya delimitado. `\cX` se aplica solo dentro de ese contenido.
   - Se añade `\x{H…}` con la semántica de bash 5.2.
   - Diferencial con bash real, ejecutado desde ficheros `.sh`: cada escape de bash (`\c`, `\x`, `\x{}`, `\u`, `\U`, `\0NNN`, `\e`) seguido de `'`, `\\` o `\'` y de `; git reset --hard #'`. Resultado exigido: 0 divergencias con efecto.
   - Todas las formas de `lb12` y `lc12` entran al corpus como BAD.
2. **Fallo cerrado en la ruta heredada** (gap 3).
   - `_destino_es_el_propio_directorio` captura `(OSError, ValueError)`.
   - `guardrail-check.py pre-tool` lo lanzan solo los hooks del rol protegido. Por eso, cualquier excepción interna de su `main()` deniega con un motivo explícito y nunca permite.
   - Test con el surrogate y con una excepción inyectada.
3. **Tests sin reloj de pared** (gap 5). Los umbrales de coste del guard pasan a medir CPU del proceso o una razón de linealidad entre dos tamaños. Los `< 0.05` del journal pasan a un reloj inyectado o a CPU. Verificación: 20 pasadas con 12 bucles de CPU, 0 rojos.
4. **Espera del journal acotada en tiempo** (gap 6). Un tope total con reloj monótono de unos 0,75 s, y como mucho un listado del directorio por intento acotado. Test: 10 K entradas + 1 K `.tmp-`, < 1 s.
5. **Instalador en Windows** (gap 2). Se aplica `debug-root-cause` para ver de dónde salen los 30 s con un plazo de 2 s: el `--version` de 15 s ×2, la resolución del shim `sh` en Windows o el árbol de procesos sin matar. Arreglo con test de regresión que pase en Windows y en Linux, sin relajar la cota. Después, la suite node completa en Windows debe dar 0 fail.
6. **Traza y documentación** (gaps 7, 8 y 9).
   - RED de las tres ramas de deny como tests de regresión, declarando en el ledger que llegan después.
   - Recuentos corregidos.
   - `LIMITE11` en el modelo de amenaza de `implementer.md`.

Tras este ciclo: réplica Linux completa sin rojo, suite node de Windows sin rojo, medida emparejada de T-23 con el equipo libre (la hace el orquestador) y verificación dirigida de las cuatro lentes. Si solo quedan Minor sin pérdida de datos, la fase cierra.
