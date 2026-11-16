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
- **Tiempo IA (ejec.)**: est. 0.5h · real 16.03h (0.4h del cierre original estimado + 2.53h medidas en fix5 + 0.78h en fix6 + 1.33h en fix7 + 1.55h en fix8 + 3.22h en fix9 + 1.21h en fix10 + 0.43h en fix11 + 2.11h en fix12 + 0.95h en fix13 + 0.45h en fix14 + 1.07h en fix15 `(medido)`; las ventanas de fix5 a fix15 están compartidas con T-07 y T-23; la cifra anterior, 11.42h, no sumaba las 2.11h de fix12)
- **Archivos**: `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/test_guardrail_check.py`, `agent-kits/shared/test_guardrail_differential.py` (fix5), `tests/test_native_guardrail_dispatch.py`, `docs/agents/implementer.md`, `docs/CONVENTIONS.md` · fix6: `agent-kits/shared/native-guardrail.py`, `hooks/run-hook.mjs`, `hooks/opencode-plugin.js`, `interop/opencode/plugins/custom-agents/index.js` (regenerado), `tests/test_native_guard_failclosed.py` (nuevo), `tests/hook-guard-failclosed.test.mjs` (nuevo), `docs/FLOWS.md`, `docs/en/FLOWS.md` · fix7: `agent-kits/shared/test_guardrail_fix7.py`, `agent-kits/shared/test_guardrail_differential7.py`, `tests/test_native_guard_failclosed7.py`, `tests/native-guard-adapter-failclosed.test.mjs` (nuevos), `docs/INTEROP.md`, `docs/en/INTEROP.md`, `interop/opencode/plugins/custom-agents/index.js` (regenerado), `agent-kits/shared/test_guardrail_differential.py` · fix8: `tests/test_native_guard_scan8.py` y `tests/native-guard-adapter-fix8.test.mjs` y `agent-kits/shared/test_guardrail_fix8.py` (nuevos), `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/native-guardrail.py`, `hooks/run-hook.mjs`, `hooks/opencode-plugin.js`, `interop/opencode/plugins/custom-agents/index.js` (regenerado), `agent-kits/shared/test_guardrail_differential.py`, `agent-kits/shared/test_guardrail_differential7.py`, `tests/test_native_guard_failclosed.py`, `tests/test_graphiti_security.py` (huella del lanzador), `docs/INTEROP.md`, `docs/en/INTEROP.md`, `docs/agents/implementer.md` · fix9: `agent-kits/shared/test_guardrail_fix9.py` y `tests/test_native_guard_parity9.py` y `tests/native-guard-adapter-fix9.test.mjs` (nuevos), `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/native-guardrail.py`, `hooks/opencode-plugin.js`, `interop/opencode/plugins/custom-agents/index.js` (regenerado), `agent-kits/shared/test_guardrail_differential7.py` (BAD9_PARIDAD y LEGIT9), `agent-kits/shared/test_guardrail_fix8.py` (`env -S 'echo "hola'` pasa a denegado), `docs/agents/implementer.md`, `docs/INTEROP.md`, `docs/en/INTEROP.md` · fix10: `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/native-guardrail.py`, `hooks/run-hook.mjs`, `hooks/opencode-plugin.js`, `interop/opencode/plugins/custom-agents/index.js` (regenerado), `agent-kits/shared/test_guardrail_differential7.py`, `agent-kits/shared/test_guardrail_fix10.py` (nuevo), `tests/test_native_guard_parity9.py`, `tests/opencode-realpath-fix10.test.mjs` (nuevo), `tests/native-guard-adapter-fix9.test.mjs`, `tests/test_graphiti_security.py` (huella), `docs/agents/implementer.md`, `docs/INTEROP.md`, `docs/en/INTEROP.md` · fix11: `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/test_guardrail_differential7.py`, `agent-kits/shared/test_guardrail_fix11.py` (nuevo), `hooks/opencode-plugin.js`, `interop/opencode/plugins/custom-agents/index.js` (regenerado), `tests/opencode-realpath-fix11.test.mjs` (nuevo), `docs/agents/implementer.md` · fix12: `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/test_guardrail_fix12.py` (nuevo), `agent-kits/shared/test_guardrail_fix11.py`, `agent-kits/shared/test_guardrail_differential.py`, `agent-kits/shared/test_guardrail_differential7.py`, `docs/agents/implementer.md` · fix13: `agent-kits/shared/test_guardrail_fix13.py` (nuevo), `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/test_guardrail_fix12.py`, `agent-kits/shared/test_guardrail_differential7.py`, `docs/agents/implementer.md`, `docs/roadmap/2026-11-10-plugin-audit-2/execution-history.md` · fix14: `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/test_guardrail_fix14.py` (nuevo), `agent-kits/shared/test_guardrail_fix14_corpus.py` (nuevo), `agent-kits/shared/test_guardrail_fix10.py`, `agent-kits/shared/test_guardrail_fix12.py`, `agent-kits/shared/test_guardrail_fix13.py`, `docs/agents/implementer.md` · fix14 y fix15 (declarados en fix15, gap 14): `agent-kits/shared/test_guardrail_fix14.py`, `agent-kits/shared/test_guardrail_fix14_corpus.py`, `agent-kits/shared/test_guardrail_fix15.py` y `agent-kits/shared/test_guardrail_fix15_corpus.py` (nuevos), `install/install.mjs` (fix14: `detached: true`; fix15: vigilante de señales; declarado también en T-23), `agent-kits/shared/journal-capture.py`, `agent-kits/shared/journal-io.py`, `agent-kits/shared/journal.py`, `hooks/opencode-plugin.js` (ver T-23)
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

**fix15 (intento 15, gaps 1 a 4, 6 a 8, 12 y 14; el diseño del orquestador —puntos 1 a 8— se aplica tal cual salvo las interpretaciones i1 a i12)** — `plugin-audit-2/T-06-fix15` y `T-23-fix15` (los marcadores se abrieron DESPUÉS del RED, ya con el diseño de los tests hecho: la ventana medida no incluye el diseño ni el RED).

RED (`b208568`, solo tests, contra el código de 90c50cf): `test_guardrail_fix15.py` → **80 failed y 58 passed** (138 tests): 8 salidas de rama con `branch_fn` real (`GIT switch main`, `Git checkout master`, `g''it switch main`, `$'\x67it' checkout main`…; de 11 formas, 3 ya se denegaban por otra regla), 1 «`branch_fn` se consulta en cualquier orden» y 1 «no queda `re.search(r"\bgit\b")` sin `re.I`», 22 de 25 formas con git codificado dos veces (9 sondas de la Lente C y 13 aciertos de `fz`; las 3 que pasan son lecturas completas que ya se denegaban), 4 de «n rondas hasta 8» (n = 2, 3, 5 y 8) y 3 de «n ≥ 9 es lectura opaca» (el límite exacto es n + 1 rondas —n de `\` y la última de `g`—: en `5696e65` pasan a n = 2, 3, 5 y 7, y n ≥ 8 es opaca), 33 de 40 envoltorios (`flock -c`/`--command`, `nohup --`, `nice` con la ventana de seis palabras, `chrt`, `taskset`, `doas`, `winpty`, `/usr/bin/time`, `command time`, `su -c`; las 7 que pasan eran las abreviaturas de `env`, que ya se denegaban por opción desconocida con git), 1 de legítimos (`env --split 'git status'`, un falso deny que se corrige), 1 de `flock -c` como `bash -c`, 1 de la ventana de `nice`, 1 de `nohup` fuera de `_CONTROL`, 1 de la tabla (`chrt`, `taskset`, `doas`, `winpty`, `time`, `su`), 1 de límites declarados en `implementer.md` y 2 diferenciales con bash real (por locale). `test_journal_fix15.py` → **13 failed** (los 13: `_ARRANQUE`, `begin_budget(desde=)`, plazo ya agotado, sin origen, `main` de la captura y `capture-end` de `journal.py` que pasan `desde`, `capture_end` que lo pasa al presupuesto, 3 inicializaciones legítimas cortas y 3 más largas que el plazo restante). Instalador en Linux (`docker`, `t23m:ci`, Node 22, sobre el `install.mjs` de 90c50cf): **3 failed** (SIGINT y SIGTERM: «el instalador sigue vivo 3 s después»; SIGHUP: «el grupo de la CLI sigue vivo… quedó huérfano»); en Windows esos 3 tests se omiten (sin grupos POSIX). OpenCode: **3 failed** (`fix15 gap 13: activity events launch no handler` sin `dev.json`, con `actividad: false` y con `sesion` ausente) y 1 que pasa (con `actividad: true` se lanza, fija lo que no cambia). **Sin RED, declarado:** los cambios de estabilidad de los tests (el stub de Windows que responde `--version` sin node y el plazo de 10 s, los separadores intercalados con la misma referencia, `Date.now` congelado en `gap 10` y la condición en lugar de `setTimeout(150)` en `f4fix1 gap 3`) no pueden fallar a propósito: son rojos intermitentes con carga; su prueba son las pasadas con 12 bucles de CPU (abajo). Los 5 tests de actividad de OpenCode que existían (`native execution start…`, `tool activity …` ×4) pasan a un proyecto con `sesion.actividad: true` y pasan antes y después.

GREEN (`2d97794` código y tests; `ce7746c` el vigilante con `kill -9`; `3428e3e` el journal con la primera espera y `queue`, la caza de huérfanos y `until`, y el archivado de fix13 y fix14; `5696e65` los tests que matan los mutantes supervivientes; el ledger y el cierre en el commit siguiente):
1. **La rama se consulta siempre** (gap 1): `decide()` llama a `branch_fn` en toda orden Bash no vacía, sin `re.search(r"\bgit\b")`; el grep de todas las apariciones de `\bgit\b` deja solo `_ARIT_GIT_RE` (aritmética) y `_GIT_TEXTO_RE` (con `re.I`). Tests con `gc.current_branch` REAL sobre un repositorio `git init -b feature/x` (11 formas, también `GIT.EXE`, `\git`, `bash -c "GIT switch main"` y un `case` incompleto).
2. **Decodificación hasta punto fijo** (gap 2): `_aplanado` repite los escapes numéricos hasta un punto fijo con un máximo de 8 rondas (`_RONDAS_ESCAPES`; `_numerico` a nivel de módulo) y, si a la 9.ª aún cambia, lanza `_DecodificacionInestable` y `_check_git` deniega como **lectura opaca**. Las 9 sondas y los 13 aciertos de `fz` entran al corpus (`test_guardrail_fix15_corpus.py`: `DOBLE15`, `HITS15`) y deniegan. Lineal: como mucho 9 pasadas (test de coste a 250 KB).
3. **Envoltorios por tabla única** (gaps 3, 4, 6 y 7): `time` y `nohup` salen de `_CONTROL` y entran en la tabla con sus opciones y `--`; nuevas entradas `chrt`, `taskset`, `doas`, `winpty` (prefijo `-X`) y `su`; `_POSICIONALES` (duración de `timeout`, fichero de `flock`, prioridad de `chrt`, máscara de `taskset`) sustituye al caso especial; se normaliza por el nombre base (`/usr/bin/time`). `flock -c|--command` (antes o después del fichero, pegada o en cluster) y `su -c|--command|--session-command` devuelven la cadena y `_desenvuelve` la sustituye por `sh -c <cadena>`: se analiza como `bash -c` heredando la marca. Las abreviaturas de `env` se resuelven por prefijo único (`_env_larga`: `--split`, `--s`, `--split=` equivalen a `-S`; `--i` es ambigua y deniega con git). Sin la ventana `toks[:6]`: el intérprete tras una opción desconocida se busca en TODA la orden simple (lineal, test de coste).
4. **Límites declarados** (gap 8): `LIMITE15` (6 formas que bash 5.2 ejecuta y el guardarraíl no ve: `{git,} reset --hard`, `{g..g}it`, `g${x}it`, `g$()it`, `${VAR}` en `env -S`, `echo reset --hard | xargs git`) y 2 que dependen del runtime (glob y NUL crudo, solo «se permite»); `implementer.md` los nombra con un ejemplo de cada clase.
5. **Instalador sin regresión de señales** (gaps 5 y 11): `execFileSync` es síncrono y un manejador de JS no se ejecuta mientras espera (RED: con el manejador activo, SIGINT y SIGTERM no hacían nada), así que NO se reenvía desde JS: mientras espera `correr` quita los manejadores de SIGINT/SIGTERM/SIGHUP (la acción por defecto termina al instalador al instante) y lanza la CLI tras un **vigilante** de `sh` del propio grupo (`detached`): si el instalador desaparece por cualquier vía, el vigilante mata el grupo con `kill -9 -pgid` (dash no admite `--` tras la señal: el primer intento con `kill -KILL --` dejó al nieto vivo, medido en Docker). Si es la CLI la que acaba, el vigilante sale solo. `SIGHUP` se añade a las señales del manifiesto. Test (Linux/macOS): SIGINT, SIGTERM y SIGHUP al instalador con la CLI colgada → instalador y grupo muertos en menos de 3 s, sin huérfano. Gap 11: el stub de Windows responde `--version` en el propio `.cmd` y el plazo del test pasa de 2 a 10 s en Windows (la cota de 30 s no se relaja).
6. **Journal anclado al arranque** (gaps 9 y 10): `_ARRANQUE` (marca monotónica) en `journal-capture.py`, `journal.py` y `journal-io.py`; `begin_budget(desde=)` fija el límite en `desde + 0,35 s`; `capture_end(root, payload, desde=None)`, `journal-capture.py main` y `journal.py capture-end` pasan su propio `_ARRANQUE`. El presupuesto se conserva en **0,35 s** (interpretación i6). Dos añadidos tras medir con 12 bucles de CPU (i10): la PRIMERA espera de un estado transitorio del proceso dispone de al menos `_ESPERA_MINIMA` = 0,10 s aunque el arranque ya haya agotado el plazo (el resto de esperas comparte el plazo, como en fix14), y `queue()` recorre SIEMPRE las 255 primeras entradas (el límite se comprueba desde la 256: con el arranque lento una cola normal de tres carpetas lanzaba `journal_queue_budget` en `k = 0`). RED de esos dos (sobre el código de `ce7746c`): **4 failed** de `test_journal_fix15.py` (la espera mínima: plazo agotado y 3 inicializaciones cortas) y, por mutación, **3 failed** del recorrido de `queue` (3, 100 y 255 entradas con el plazo agotado) y 6 de `queue_desde_k0` en la suite del journal.
7. **Tests sin reloj frágil** (gaps 12 y 13): separadores con `c` y `g` intercalados y la misma referencia en cada repetición (pasa si alguna de las tres cumple las dos cotas); OpenCode `gap 10` con `Date.now` congelado y `f4fix1 gap 3` con la condición `captures.exit` en lugar de `setTimeout(150)` y `until(…, 120000)` (`until` acepta un plazo). El adaptador comprueba `sesion.actividad === true` de `.claude/dev.json` ANTES de lanzar `node` (eventos y herramientas; `interop/opencode/…/index.js` regenerado, `--check` 88).
8. **Traza** (gap 14): `Archivos` de T-06 y T-23 con `install/install.mjs`, el journal, OpenCode y sus tests; `Runtimes` de T-23 corregido; cabecera «i1 a i9», el tercer test del journal y el tamaño corregidos en fix14 antes de archivarlo (puntero arriba); errata de las filas 5 y 6 del intento 14 (archivado): citan `5ba1e03` (el RED) pero el test definitivo del instalador es de `079e5c4` (con el nieto identificado por puerto o línea de órdenes, i9 de fix14) y la causa probable de su rojo intermitente era el plazo de 2 s del stub de Windows (gap 11), no el PID reutilizado (la i9 de fix14 queda corregida así).

Interpretaciones: (i1) `current_branch` NO pasa a leer `.git/HEAD`: sigue siendo `git rev-parse` (hasta dos subprocesos) porque `test_guardrail_check.py` fija ese contrato (`subprocess.run` simulado, presupuesto de 0,5 s); consultarla en TODA orden Bash del rol protegido cuesta una mediana de **96 ms** por orden (15 medidas, Windows con carga de fondo), antes solo con `git` en minúsculas; si el coste molesta, la salida es una lectura directa de `.git/HEAD` con el mismo resultado (cambio de contrato de esos tests) o una consulta perezosa solo en la regla de `checkout`/`switch`; (i2) el vigilante del instalador sustituye al reenvío por manejadores JS (el diseño pedía `kill(-pid)` desde el manejador, que no puede ejecutarse con `execFileSync` esperando); consecuencia declarada: una señal MIENTRAS la CLI corre termina al instalador sin escribir el manifiesto «incompleto» (antes el manejador solo corría al volver `execFileSync`, hasta 120 s después, y con la CLI colgada nunca); (i3) `time` y `nohup` pasan de palabras de control a envoltorios: `time -z git status` (opción desconocida) deniega con git, falso deny aceptado; (i4) `su` sin `-c` no tiene programa (abre una shell: resto vacío) y con `-c` la cadena se analiza como `sh -c`; (i5) la comprobación de `sesion.actividad` del adaptador es SÍNCRONA (con lecturas asíncronas la actividad arrancaba ~500 ms después de los handlers posteriores y rompía T-47 fix1, medido) y ante cualquier duda (enlace, tamaño, JSON ilegible) delega en `agent-activity-store.py`; (i6) el presupuesto del proceso se conserva en 0,35 s, ahora desde el arranque: con 0,45 s el hijo salía en 581-628 ms y con 0,50 s en 630-842 ms (2 de 10 sobre 800), mientras que 0,35 s da 549 a 756 ms en 20 ejecuciones, 0 por encima de 800 (90c50cf, intercaladas: 593 a 1.088 ms, 3 de 20 por encima de 800); (i7) `_ARRANQUE` se toma tras los imports de la biblioteca estándar y el snippet de consola y no en la primera línea, porque `lint_plugin` exige que solo imports precedan al snippet (el arranque de Python y esos imports quedan fuera de la marca; la medida de extremo a extremo los incluye); (i8) los 3 tests de señales se omiten en Windows y su RED y GREEN son los de la réplica Linux; (i10) el plazo del proceso anclado al arranque rompía la captura con la máquina saturada: con 12 bucles de CPU el arranque del hijo (3 a 8 s de `python` más `node`) consumía los 0,35 s y la cola normal o el primer estado transitorio se omitían; por eso la primera espera recibe un mínimo de 0,10 s y `queue()` recorre las 255 primeras entradas (declarado arriba); las pruebas de fix15 del journal fijan los dos; (i11) `until` de `tests/helpers/opencode-context.mjs` pasa de 15 a 120 s por defecto (solo se agota cuando el efecto no ocurre); (i12) `matarArbol` de Windows sube el tope de la caza de huérfanos (`wmic`/PowerShell + CIM) de 15 a 90 s (`TIMEOUT_CAZA`): en la primera serie de 5 pasadas con 12 bucles `gap 8` dio 1 rojo (el nieto sobrevivía) y con el tope de 90 s dio 5 de 5 verdes (hipótesis, no demostrada: la consulta CIM tardaba más de 15 s); (i9) el corpus de envoltorios ejecuta con bash real solo lo que existe en el entorno: Git Bash de Windows carece de `flock`, `chrt`, `taskset`, `doas`, `su` y `/usr/bin/time` (el arnés lo detecta con `type -P` y lo cuenta aparte); en la réplica Linux existen `flock`, `chrt`, `taskset` y `su`.

**Diferenciales y barridos de fix15.** Punto 2, barrido G4 de `fz` (`f15/fz_g4.py`): 72.000 plantillas × 4 grafías (`g''it`, `GIT`, `$'\x67it'`, git doblemente codificado tras `eval`): se permiten **1.520 por grafía, las mismas que con git literal** (ninguna grafía permite más que `git`); muestra con **bash real de 1.000** (250 por grafía; git falso en `git`, `GIT`, `Git`, `git.exe` y `GIT.EXE`, comprobado con `type -P`): **0 ejecutan git**. Diferencial 90c50cf → fix15 (`f15/dif_fix15.py`): las 2.690 órdenes de lb13 → **0 denies nuevos y 0 regresiones**; los 7.056 `case` inocuos → **0 denies nuevos**; aleatorio de 60.000 órdenes → 1.142 denies nuevos y **862 órdenes que 90c50cf deniega y fix15 permite, todas con `env --s`/`--split`/`--spli`** (antes, opción desconocida → deny; ahora se analiza el valor de `-S`): de 18.337 órdenes con esa abreviatura, 65 deciden distinto que con `--split-string` y son artefactos de la sustitución (la abreviatura es un argumento de `git restore`, donde `--s` es un prefijo de `--staged`), no una diferencia de `env`. Punto 3: el corpus de las lentes (`ENVOLTORIOS15`, 40 formas) con bash real en dos locales: Windows, Git Bash 5.2 con `LANG` sin definir y con `C.UTF-8`: 65 formas (los 25 de git codificado dos veces —`DOBLE15` y `HITS15`— y los 40 envoltorios): bash ejecuta git en **30** y el guardarrail deniega las **30** (0 allow que ejecutan git); las otras 35 no ejecutan: **11** con el binario presente y su motivo en `SIN_PARIDAD15` (4 de `coproc`, 4 de `echo <( )` que no lee el descriptor y 3 de `winpty`, que exige una terminal) y **24** con el binario ausente en Git Bash (`flock` 6, `chrt` 4, `taskset` 4, `doas` 4, `su` 1 y `/usr/bin/time` 5; el arnés lo detecta con `type -P`; 3 de `chrt` y la de `su` llevan además su motivo en `SIN_PARIDAD15`, para Linux). En la réplica Linux (Debian, bash 5.2, util-linux) existen `flock`, `chrt`, `taskset` y `su`: el diferencial da 0 allow que ejecuten git y las 2 formas que allí no ejecutan (`sh` es dash; `flock --command=…` antes del fichero) están declaradas..

**Estabilidad con 12 bucles de CPU** (`ld13/carga.py`, 5 pasadas cada una): separadores: **5 de 5 pasadas sin rojos** (12 passed cada una, 77 a 91 s). Instalador `gap 8` en Windows (2 passed): primera serie **4 de 5** (la pasada 4 dio «la CLI colgada dejó procesos huérfanos vivos (PIDs 35796)» en 185 s, con el tope de 15 s de la caza de huérfanos: i12) y, con `TIMEOUT_CAZA` de 90 s, **5 de 5** (77 a 94 s por pasada). OpenCode (`opencode-plugin.test.mjs` y `opencode-realpath-fix10/11`, 44 tests): 3 tests lanzan el lanzador REAL (`node run-hook.mjs` y `python`: `idle captures envelope…`, `cleanup of the real launcher…` y `real adapter teardown cleans background descendants…`) y con 12 bucles sobre 12 CPU lógicas más la carga base de la máquina el hijo supera el presupuesto del hook («capture timed out»): serie A (antes de `until` de 120 s) pasada 1 con 2 rojos (esos dos) y pasada 2 con 1; serie B sin los dos primeros (`--test-skip-pattern`), 5 pasadas: la 1 con **42 de 42** y las 2 a 5 con 41 de 42 (el rojo es siempre `real adapter teardown…`, 120 s). **Es anterior a fix15:** con el árbol de 90c50cf (`until` a 120 s) `idle captures…` y `cleanup of the real launcher…` dieron rojo en 2 de 2 pasadas, `real adapter teardown…` 1 rojo de 3 (con el árbol nuevo, 1 rojo de 3) y el lanzador real dejó 0 envelopes de 4 en las dos versiones (`f15/launch_load.py`). Los dos tests que la lente identificó (`gap 10` y `f4fix1 gap 3`) pasaron en las 7 pasadas completas. **No se pudo cumplir «0 rojos» con esos tres tests en esta máquina**; se declara al orquestador.

**Journal en frío y carrera** (punto 6): hijo de SessionEnd (`python -I -S journal-capture.py`, arranque incluido, 50 K + 5 K ajenos, cola configurada fallida): 10 ejecuciones por serie y dos series alternadas con el código de 90c50cf: **90c50cf, plazo de 0,35 s desde la primera espera: 594 a 1.088 ms y 593 a 808 ms (3 de 20 por encima de los 800 ms del hook); fix15, 0,35 s desde el arranque (`_ARRANQUE`): 558 a 756 ms y 549 a 633 ms (mediana 561 a 581 ms, 0 de 20 por encima de 800)**; con el plazo anclado a 0,45 s salieron 581 a 628 ms y con 0,50 s 630 a 842 ms (2 de 10 sobre 800), por eso se conserva 0,35 s. la máquina no estaba en reposo: carga base del 38 al 42 % sin nada mío y del 70 al 79 % durante las medidas (OneDrive y Docker, ajenos a estas pruebas). Con 12 bucles de CPU sobre las 12 CPU lógicas el hijo tarda 1,0 a 3,9 s en `python -I -S journal-capture.py` (arranque incluido) y el lanzador lo corta antes (ver «Estabilidad»). La carrera legítima de dos procesos con el presupuesto real: `f15/race15b.py` (el escritor deja `.custom-agents-journal` con dos enlaces y un `.tmp-` reciente y lo termina D s después de lanzar al lector; el lector es un `python -I -S` nuevo que importa `journal-io.py`, abre el presupuesto como la captura y lee con `read_settled`; el lector arranca unos 0,15 a 0,25 s después de empezar la inicialización): con fix15 y D = 0,10 / 0,20 / 0,25 / 0,30 / 0,35 / 0,40 / 0,50 s se omite **0 de 8** en cada D y con D = 0,70 s **7 de 8** (el lector espera hasta 372 ms); con el código de 90c50cf, 0 de 8 hasta 0,50 s y 6 de 8 con 0,70 s. Declarado: la captura se OMITE (`unsafe_state`) si el estado transitorio de una inicialización legítima sigue en pie 0,35 s después del arranque del lector (en estas medidas, una inicialización de 0,55 s o más desde su comienzo) y la recupera `recover`; la omisión por duración sigue siendo la de fix14, ya sin depender de cuándo se hace la primera espera, y una primera espera nunca recibe menos de 0,10 s (i10).

**Mutaciones de fix15.** Cada mutante se aplicó a una copia del directorio y se ejecutó el subconjunto de tests (`f15/mut15.sh`): condicionar de nuevo la consulta de la rama a `\bgit\b` → **9 failed**; `_RONDAS_ESCAPES = 1` → 29 passed la primera vez (denegaba de más como opaca, así que los tests solo de «deniega» no la distinguían) y **4 failed** tras exigir que hasta 7 niveles se deniegue por git y no por opaca; sin la cadena de `flock` dentro del bucle de opciones → 11 passed y **3 failed** con las formas legítimas `flock -c 'git status' F`/`--command=`; `nohup` otra vez en `_CONTROL` → **5 failed**; la ventana `toks[:6]` → **4 failed**; sin la resolución de abreviaturas de `env` → 2 passed y **4 failed** con `env --s 'git log -1'`; journal: `begin_budget` sin origen → **8 failed**, `queue` comprobando en `k = 0` → **6 failed**, sin el mínimo de la primera espera → **7 failed**. Los 3 que sobrevivían se mataron en `5696e65`. Instalador y adaptador: su RED (arriba) es la mutación.

**Cierre fix15** — commits: RED `b208568`; código `2d97794`; vigilante `ce7746c`; ledger e informe en el commit siguiente. Réplica Linux COMPLETA de `ci.yml.MANUAL-COPY` sobre `5696e65` (`python:3.11-slim`, imagen `t23m:ci`, `--rm --name ca_imp15_full` con `timeout`, `-m 1g --cpuset-cpus 0-3`, Node 22, `git archive` en LF, Docker Desktop ya en marcha, sin tocar los contenedores del usuario): **3 failed y 14.272 passed** (71 skipped, 726 s) en el paso paralelo: `tests/test_console_encoding.py::test_las_suites_tambien_decodifican_a_sus_hijos_como_utf8` (el test nuevo `test_guardrail_fix15.py:31` capturaba un hijo en modo texto sin `encoding=`) y los 2 `test_diferencial15…` (en Debian `sh` es `dash`, que no entiende `$'…'`, y `flock --command=…` puesto antes del fichero no ejecuta la cadena: declarados en `SIN_PARIDAD15` con su motivo); los tres se corrigieron en `ba9b3ae` y la comprobación dirigida en la misma imagen (`test_console_encoding`, `test_guardrail_fix15`, `test_journal_fix15` y `test_guardrail_fix14` sin los separadores) da **1.409 passed**. El resto de pasos, en verde: linter 0 errores y 16 avisos (4 s), `check-handbook`, evals 227 casos, serie 58 passed (82 s), bench, interop al día, **`node --test` 564 tests: 539 pass, 0 fail, 25 skipped (149 s), con los 3 tests de señales de fix15 en verde**, sintaxis, JSONs y `release.py --check`; total 971 s. Windows (bash de Git): guardarraíl + diferenciales (`agent-kits/shared/test_guardrail*.py`, `test_native_guardrail.py`, `test_git_verification.py`: check 662, diferencial 574, diferencial7 856 + 5 skipped, fix10 18, fix11 33, fix12 56, fix13 180, **fix14 492, fix15 147**, fix7 122, fix8 49, fix9 68, native 227, git_verification 357) y journal + despacho nativo (`test_journal*.py` **321 passed**, 10 skipped; `tests/test_audit_journal.py` 21, `test_f4fix2_journal.py` 2, `test_f4fix3_journal.py` 6, `test_native_guardrail_dispatch.py` 14, `test_native_guard_*.py` 26 + 16 + 5 + 8 + 10): **0 failed**. Suite node completa de Windows (`node --test --test-concurrency=2 tests/*.test.mjs`, 564 tests): pasada 1 → 556 pass, **2 fail**; pasada 2 → 557 pass, **1 fail**; los 3 rojos son de `tests/codex-plugin-state.test.mjs` (`real standalone native query…`, `native query children never resolve node…` y `timeout kills non-cooperative native process…`): `cli-timeout`/`ETIMEDOUT` de la consulta nativa, cuyo tope fijo es `CODEX_QUERY_TIMEOUT_MS` = 3 s (`agent-kits/shared/codex-plugin-state.mjs`, que no se toca): con la carga de la máquina arrancar un `node` tarda más. **Anterior a fix15:** con el árbol de 90c50cf el primero da el mismo rojo con la misma carga. Con la máquina menos cargada (59 %) `codex-plugin-state.test.mjs` entero dio 10 de 10 dos veces y un rojo (2 tests) la tercera: es sensible a la carga y no es de fix15; en la réplica Linux la suite node completa da 0 fail. **No se pudo cumplir «0 fail en dos pasadas» en Windows con esta máquina**; se declara al orquestador.

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
- **Tiempo IA (ejec.)**: est. 0.5h · real 0.55h (medido; ventana compartida con T-02..T-07) + fix5 a fix15 sin horas propias (ventanas imputadas a T-06; la de fix15 de T-23 se midió en la misma ventana)
- **Archivos**: `tests/codex-plugin-state.test.mjs` (intento 12, orquestador: la regex del test de `candidates()` acepta CRLF; en un checkout de Windows `run-hook.mjs` llega con CRLF y el test daba rojo) · `docs/roadmap/2026-11-10-plugin-audit-2/testing/perf.md` (lo escribe el orquestador con las medidas de T-07 y T-23; el guardarraíl veta `testing/` al implementer) · `ci.yml.MANUAL-COPY` y `.github/workflows/ci.yml` (idénticos, comprobado con `diff`; el paso `pip install pytest pyyaml` de `:30-31` añade `pytest-xdist`), `tests/test_ci_manual_copy.py`, `tests/test_ci_skill_suites.py`, `tests/test_suites_no_pytest.py` · añadidos por la nota de alcance: `pytest.ini` (solo registra el marcador `serie`), `tests/test_redact_fix3.py`, `tests/test_npm_payload.py` (fix4: timeout de `npm pack` 120 → 600 s), `tests/test_local_state_fix3.py` (fix4: módulo al paso serie, plazo de pared del almacén), `agent-kits/shared/test_redact.py`, `agent-kits/shared/test_plan_review_summary.py`, `tests/test_agent_activity_store.py`, `tests/test_bench_session_end.py`, `tests/opencode-plugin.test.mjs` (fix1: espera a que el hijo escriba el JSON), `tests/test_lint_plugin.py`, `tests/test_ledger_lint.py`, `tests/test_dashboard.py` (fix1: wrappers `test_suite_legada_*` de sus `main()`/`run()`) (marcados `@pytest.mark.serie`: miden tiempo de pared o dependen del orden de lecturas y fallan bajo `-n auto`; corren en un paso aparte sin xdist), `agent-kits/shared/agent-activity-store.py` (fix5), `agent-kits/shared/test_redact.py` (fix5) · fix7 (corrección de fix8, gap 9: faltaban): `agent-kits/shared/test_ledger_view.py` (paso serie), `tests/test_graphiti_security.py` (huella del lanzador) · fix8: `agent-kits/shared/test_journal_io_deadline.py` (nuevo), `agent-kits/shared/journal-io.py` (plazo inyectable solo bajo `PYTEST_CURRENT_TEST`), `agent-kits/shared/test_journal.py`, `tests/test_redact_fix3.py`, `tests/test_native_guard_failclosed.py` (prueba de plazo al paso serie), `tests/test_panel_review_panel_server.py` (2 pruebas al paso serie) · fix9: `tests/test_fix9_plazos_inyectados.py` (nuevo), `agent-kits/shared/test_journal.py` (sin aserciones de pared), `tests/test_panel_review_panel_server.py` (BODY_TIMEOUT inyectado, sin paso serie), `tests/test_redact_fix3.py` (demo ×12 por la decisión de la puerta y sonda al crecimiento real) · fix10: `agent-kits/shared/test_journal.py`, `tests/test_fix9_plazos_inyectados.py` (vigía), `tests/test_redact_fix3.py`, `agent-kits/shared/journal-io.py` y `journal-capture.py` (`settled`: espera el estado transitorio de dos enlaces), `skills/training-data-services/scripts/test_dataset_assembler.py` y `agent-kits/shared/test_knowledge_read_context.py` (rojos de réplica de tiempo de pared) · fix12: `agent-kits/shared/journal-io.py`, `agent-kits/shared/test_journal.py`, `tests/installer.test.mjs` (el test de la CLI colgada mide desde el arranque de la CLI) · fix14 y fix15 (declarados en fix15, gap 14): `install/install.mjs` (`detached: true` en `correr` y el vigilante de señales: cambio de conducta en Linux y macOS), `agent-kits/shared/journal-capture.py`, `agent-kits/shared/journal-io.py`, `agent-kits/shared/journal.py` (presupuesto por proceso y plazo desde el arranque), `agent-kits/shared/test_journal_fix14.py`, `agent-kits/shared/test_journal_fix15.py` (nuevo), `hooks/opencode-plugin.js` y `interop/opencode/plugins/custom-agents/index.js` (regenerado: opt-in de la actividad), `tests/opencode-plugin.test.mjs`, `tests/helpers/opencode-context.mjs`, `tests/installer.test.mjs`
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

**fix13 (intento 13, gaps 2 y 9; T-23 sigue `en-progreso`: falta la medida emparejada, del orquestador)** — `plugin-audit-2/T-23-fix13`; commits: los de T-06 (`bc6054d` RED, `f1aa8ec` código).
- **Journal acotado de verdad** (gap 2): `initializing(path, limit)` y `settling(path, limit)` comprueban el tope DENTRO del listado (cada 256 entradas del `scandir` y cada 64 `lstat`) y devuelven False agotado el tope (`unsafe_state`; en `update` se conserva `journal_update_conflict`); `_ESPERA_MAX` baja de 0,75 s a **0,5 s** para que el hijo de SessionEnd salga con error limpio dentro de los 800 ms del hook (arranque de Python incluido). RED (`bc6054d`): 5 failed (el tope, el listado de **50 K + 5 K** sintéticos con reloj inyectado —cada entrada «cuesta» 10 µs— y el límite de 0,7 s del test de fix12). GREEN: el listado de 55.000 entradas se corta con un tiempo de reloj simulado **≤ 0,5 s + 0,05 s de margen declarado** (256 entradas de comprobación, 2,6 ms, más un `sleep` de hasta 20 ms), en `read_settled` y en `update`. La carrera legítima de dos procesos se repite con reloj inyectado (el inicializador deshace el enlace a los 0,05 / 0,3 / 0,4 s): lee bien en los tres, y con 0,8 s agota el tope con `unsafe_state`. Sin esperas de pared: nada depende de la carga de la máquina. El test de 10 K + 1 K (16 s en reposo) queda como deuda aceptada (gap 10).
- **Instalador** (gap 9): el stub de la CLI colgada apenda cada lanzamiento a `lanzamientos.txt` y crea `inicio.flag` solo la primera vez (el test mide desde el PRIMER lanzamiento; interpretación: un mismo fichero apendado cambia de `mtime` en cada lanzamiento, así que la hora del primero y la cuenta van en dos ficheros), y el test comprueba que el árbol de la CLI muere: `ping -l 3719` (Windows, consulta CIM) o `sleep 3719` (Linux, `/proc`) no quedan vivos al volver el instalador, y el `finally` mata lo que quede. **Mutante** (RED): `matarArbol` con `return` inmediato → el test FALLA con «la CLI colgada dejó procesos huérfanos vivos (PIDs …)» en 10,7 s; con el código real pasa (38 s en esta corrida con la máquina cargada por el arranque de Docker; la medida desde el arranque de la CLI queda muy por debajo de la cota de 30 s). Sin RED contra 016de94 (el árbol sí muere): se declara como regresión con su mutante.

**fix14 (intento 14, gaps 5, 6, 9 y 10; T-23 sigue `en-progreso`: falta la medida emparejada, del orquestador)** — `plugin-audit-2/T-23-fix14`; commits: los de T-06 (`5ba1e03` RED, `fce941f` código).
- **Presupuesto por proceso del journal** (gaps 9 y 10): ver el punto 6 de fix14 de T-06 (`begin_budget`/`end_budget`, 0,35 s por proceso de captura, `queue()` acotada). Evidencia del hijo de SessionEnd en frío: 0,5 s por llamada → 624 a 855 ms (50 K + 5 K, cola configurada fallida); 0,35 s por proceso → 451 a 681 ms (20 ejecuciones). La carrera legítima de dos procesos (`lb14/race.py` y `race2.py`, con `read_settled`, que conserva su tope de 0,5 s): `race.py` con D de 0,05 a 0,45 s lee bien (dt 0,07 a 0,47 s) con 0 y con 2.000 entradas y con D = 0,6 s agota con `unsafe_state` a los 0,50 a 0,51 s, igual que 82a9442; `race2.py` con 6 inicializadores × 15 rondas × 4 pasadas: `nlink` final 1 siempre, 0 pérdidas, 0 `unsafe_state` falsos (en 2 de 60 rondas hubo 2 «won» —un `replace` con el mismo contenido— y en 5 de 60 con 82a9442).
- **Instalador** (gaps 5 y 6): stub con nieto real en las dos plataformas, PIDs registrados (nada se mata por línea de órdenes), `lanzamientos === 1`, y `detached: true` en `correr` fuera de Windows (con el nieto real, `matarArbol` no mataba nada en Linux). Mutantes: `matarArbol` vacío y relanzar tras el timeout dan rojo en Windows; en Linux, el `install.mjs` anterior da rojo (PID huérfano) y el nuevo verde.

**fix15 (intento 15, gaps 5, 9, 10, 11 y 13; T-23 sigue `en-progreso`: falta la medida emparejada, del orquestador)** — `plugin-audit-2/T-23-fix15`; commits: los de T-06 (`b208568` RED, `2d97794` código, `ce7746c` vigilante).
- **Instalador** (gaps 5 y 11): vigilante de señales en `correr` (Linux y macOS; punto 5 de fix15 de T-06). RED en Linux: SIGINT y SIGTERM «el instalador sigue vivo 3 s después» y SIGHUP con el nieto huérfano; GREEN: los 3 en menos de 3 s. El stub de Windows responde `--version` sin arrancar node y el plazo del test es de 10 s (gap 11: con 12 bucles de CPU `gap 8` daba 2 de 2 rojos por `ENOENT inicio.flag`; node tarda una mediana de 3,7 s en arrancar).
- **Journal** (gaps 9 y 10): plazo de 0,35 s medido desde el arranque del proceso (`_ARRANQUE`, `begin_budget(desde=)`); una inicialización legítima que dura 0,30 s o más desde el arranque se OMITE con `unsafe_state` (la recupera `recover`; antes, con el plazo desde la primera espera, 0,40 s); carrera de dos procesos con el presupuesto real: con fix15 0 de 8 omitidas hasta una inicialización de 0,50 s y 7 de 8 con 0,70 s (idéntico a 90c50cf, 6 de 8).
- **OpenCode** (gap 13): el adaptador solo lanza el handler de actividad con `sesion.actividad: true` (comprobación síncrona en el adaptador y en su espejo regenerado); `gap 10` con `Date.now` congelado y `f4fix1 gap 3` con condición y plazo acordes a la carga.

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

## Revisión de dos lentes — intento 15: Fase 1 (T-06, T-07, T-23) — verificación dirigida del fix14: 5 Important, 14 Minor

Lentes: A+B+C+D sobre `82a9442..079e5c4`, dos a dos por memoria.

El orquestador verificó:
- las puertas: `ledger-lint` 0, `scope-check --base 57fb054` exit 0, `lint_plugin` 0 errores, `export-interop --check` 88, `check-handbook`, `cmp ci.yml` y el `git grep` de datos personales vacío;
- las formas de los gaps 1 y 2 del intento 14 y las de `GIT`/`git.exe`: todas dan deny.

**Cerrado del intento 14:**
- **Gaps 1-12.**
- **Lectura opaca.** Deniega siempre en las cuatro formas.
- **Lente C:**
  - con bash real y un shim que cubre `git`/`GIT`/`Git`/`git.exe`/`GIT.EXE` (comprobado con `type -P`), `p1`+`p2` (44) y los 31 hits del barrido dan 0 allow;
  - `fz.py` sobre 72.000 plantillas no permite ninguna forma que se deniegue con git literal;
  - un diferencial aleatorio de 60.000 órdenes no da ningún caso en que 82a9442 deniegue y HEAD permita;
  - 30.000 entradas límite (tamaño, surrogates, NUL) no dan ninguna excepción que acabe en allow.
- **Lente B.** Sus sondas pasan de 190 a 2 allow, y ninguna de las dos ejecuta git.
- **Lente A:**
  - RED solo con tests: 297 fallos con desglose exacto, 6 + 32 del cambio de contrato y 4 del journal;
  - 385 formas y `SIN_PARIDAD14` = 116;
  - el archivado de fix10-fix12 es literal (SHA `3f174fea…`);
  - `implementer.md` documenta la lectura opaca.
- **Lente D:**
  - el guard es lineal en 23 formas (de 64 K a 255 K, con git y sin git);
  - la mutación cuadrática del separador da rojo y i7 no puede enmascararla;
  - `queue()` está acotado (se pasa del plazo entre 1 y 50 ms).

**Interpretaciones del fix14:**
- Aceptadas: i1, i2, i4, i5, i6 (plazo 0,35 s; Lente D: omisión solo con una inicialización de 0,40 s o más, que recupera `recover`), i7 (sin enmascarar, gap 12), i8 e i9 (causa corregida en el gap 13).
- No aceptada: i3. La ventana de seis palabras rebaja el criterio del punto 3 del diseño (gap 6).

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | **La rama solo se consulta si aparece `git` en minúsculas.** `guardrail-check.py:2137` llama a `branch_fn` solo si encuentra `\bgit\b` sin `re.I`, en el texto crudo. Sin rama no se aplica la regla de no salir de la rama de trabajo. `GIT switch main`, `Git checkout master`, `g''it switch main` y `$'\x67it' checkout main` → allow con `decide()` real, y bash ejecuta git. Los tests no lo ven porque fijan `branch=`. Contradice el punto 2 del diseño de fix14 y lo que dice `tasks.md:245`. No es regresión | T-06 | corregido en `2d97794`: `decide()` consulta la rama siempre; tests con `gc.current_branch` real (11 formas) | Lentes A (G1) y B (gap 1) |
| 2 | Important | **git codificado dos veces dentro de una lectura incompleta.** En la región que deja un `case` fuera de la lista blanca, un `bash -c`/`eval` con `\x5c`, `\134` o `\` delante de `x67it` pasa: `_aplanado` decodifica una sola vez (`:1877-1889`). Ejemplo: `echo "$(time -p case x in *) bash -c $'\x24\x27\x5cx67it\x27 reset --hard';; esac)"`. 9 de 9 sondas ejecutan git, también `switch main`. Con esa grafía, `fz` da 16.680 allow y en una muestra de 200 hay 13 que ejecutan git. No es regresión | T-06 | corregido en `2d97794`: decodificación hasta punto fijo (8 rondas; si no, lectura opaca); 9 sondas y 13 aciertos al corpus; G4 de `fz`: 0 de 1.000 con bash real | Lente C (C1): `lc15/`, `proto15.py` |
| 3 | Important | **`flock F -c 'git reset --hard'` → allow con git literal.** `:1004-1007` mira `-c` antes de saltar el fichero de bloqueo. Es la forma canónica de flock. No es regresión | T-06 | corregido en `2d97794`: `flock -c`/`--command` y `su -c` se analizan como `bash -c` | Lente B (gap 4): `lb15/flock.sh`. Verificado por el orquestador |
| 4 | Important | **`nohup -- git reset --hard` → allow con git literal.** `nohup` está en `_CONTROL` (`:913`), que se evalúa antes que la rama de envoltorios, así que el `--` no se salta; bash lo ejecuta. No es regresión | T-06 | corregido en `2d97794`: `nohup` sale de `_CONTROL` y entra en la tabla con `--` | Lente C (C2). Verificado por el orquestador |
| 5 | Important | **Regresión del fix14 en Linux y macOS.** `install.mjs:1318` (`detached: true`) saca a la CLI del grupo de la terminal. Con el manejador de SIGINT activo, Ctrl+C no hace nada durante 120 s; sin él, la CLI queda huérfana | T-23 | corregido en `2d97794` y `ce7746c`: vigilante de señales en `correr` (Linux y macOS); 3 tests, RED y GREEN en la réplica | Lente B (gap 3): `lb15/ctrlc.mjs`. Lo anota también la Lente A |
| 6 | Minor | i3: el intérprete detrás de una opción de envoltorio desconocida solo se busca en `toks[:6]` (`:1965`). `nice -+5 -n 1 -n 1 -n 1 bash -c "g''it reset --hard"` y `nice -+5 nice nice nice nice nice bash -c …` (12 formas) ejecutan git con allow. `implementer.md:139` no menciona el tope | T-06 | corregido en `2d97794`: sin la ventana `toks[:6]` (la i3 de fix14 queda sustituida) | Lentes A (G2) y B (gap 2) |
| 7 | Minor | Envoltorios que el guard no trata y dejan pasar git literal: `chrt`, `taskset`, `doas`, `winpty`, `/usr/bin/time`. Las abreviaturas de `env` (`--split`, `--s`, `--split=`) no se reconocen como `-S` (`:1148`) | T-06 | corregido en `2d97794`: `chrt`, `taskset`, `doas`, `winpty`, `time` por ruta y las abreviaturas de `env -S` en la tabla | Lente C (C3, C6) |
| 8 | Minor | Límites no declarados en `LIMITE`/`implementer.md`: expansiones en la palabra de mando (`{git,}`, `{g..g}it`, `g${x}it`, `g$()it`, globs, `${VAR}` en `env -S`, `xargs git` con el subcomando por stdin) y un NUL crudo `g<NUL>it` (depende del runtime) | T-06 | declarado en `2d97794`: `LIMITE15` y `implementer.md` | Lentes B (gap 6) y C (C4, C5) |
| 9 | Minor | Journal: el plazo de 0,35 s empieza en la primera espera, no al arrancar el proceso. El hijo de SessionEnd en frío (50 K + 5 K, cola configurada fallida) tarda 551-1.283 ms con carga: 2 de 10 y 4 de 10 por encima de 800. El exceso es arranque e imports (192-584 ms) | T-23 | corregido en `2d97794` y `3428e3e`: plazo desde el arranque del proceso, con un mínimo para la primera espera; medidas en el ledger | Lente D (D1): `journal-io.py:104-110` |
| 10 | Minor | Una inicialización legítima de 0,40 s o más ahora da `unsafe_state` dentro de la captura y la omite (la recupera `recover`). La carrera se repitió sin presupuesto y `tasks.md:902` dice «igual que 82a9442» | T-23 | corregido en `2d97794`: declarado desde cuándo se omite (0,35 s tras el arranque) y que lo recupera `recover`; carrera con el presupuesto real medida | Lentes A (G3) y D |
| 11 | Minor | **Rojo intermitente del instalador.** En Windows, el test «gap 8» da 2 de 2 rojos («ENOENT inicio.flag») con 12 bucles de CPU. El timeout de 2 s es menor que el arranque de node (mediana 3,7 s). Es la causa probable del fallo de i9 | T-23 | corregido en `2d97794` y `3428e3e`: `--version` lo responde el `.cmd`, plazo de 10 s en Windows y caza de huérfanos de 90 s; 5 pasadas con carga: 5 de 5 | Lentes B (gap 5) y D (D3): `installer.test.mjs:1937-1953,1979,1987` |
| 12 | Minor | El test de separadores normaliza el absoluto (i7) pero mide las dos tallas en momentos distintos. Si la carga cambia entre ambas medidas puede dar rojo sin regresión (casi-rojo: 1,453 frente a 1,46). Contra 82a9442, con carga, da 4 rojos y 2 verdes | T-06 | corregido en `2d97794`: `c` y `g` intercalados con la misma referencia; 5 de 5 pasadas con carga | Lentes A (G4) y D (D2): `test_guardrail_fix14.py:177-192` |
| 13 | Minor | **Rojos intermitentes de OpenCode en Windows** (fuera del diff; no se acepta ningún rojo). `gap 10`: la firma del adaptador tiene un plazo de pared de 1.000 ms (`hooks/opencode-plugin.js:167`) y con carga tarda 1.010-1.025 ms (2 de 2 rojos). `f4fix1 gap 3`: el `until` de 15 s frente a 5 nodes en serie por turno (~18,5 s con carga, 3 de 3 rojos). Además, el adaptador lanza un `node` por cada evento de actividad aunque `sesion.actividad` esté apagado | T-23 | corregido en `2d97794` y `3428e3e`: `Date.now` congelado, condición en lugar de `setTimeout(150)`, `until` de 120 s y opt-in comprobado en el adaptador y su espejo; ver «Estabilidad» para los 3 tests del lanzador real | Lente D (D4, D5): `tests/opencode-plugin.test.mjs:608-615,658-669`, `tests/helpers/opencode-context.mjs:29-35` |
| 14 | Minor | Traza: `install.mjs` no está en `Archivos` de T-23 ni de T-06, y `Runtimes` de T-23 dice «sin diferencia de conducta». La cabecera dice «i1 a i8» y hay i9. Un tercer test del journal pasa en RED sin estar declarado. Las filas 5 y 6 citan `5bed9d0`. El ledger se declara de 231 KiB y mide 234 | T-06, T-23 | corregido en el commit del ledger: `Archivos`, `Runtimes`, cabecera, test del journal, SHA y tamaño | Lente A (G5, G6) |

**Diseño fijado por el orquestador para fix15:**

1. **La rama siempre se consulta** (gap 1).
   - Para el rol protegido, en cualquier orden Bash no vacía, `decide()` obtiene la rama con `branch_fn` sin condición. Es leer `.git/HEAD`, barato.
   - Ninguna decisión de seguridad depende de `\bgit\b` en minúsculas; se repite el grep de todas las apariciones.
   - Hay tests con `branch_fn` real (sin `branch=`) para las cuatro formas del gap.
2. **Decodificación hasta punto fijo** (gap 2).
   - `_aplanado` y la búsqueda de git en las palabras decodificadas repiten la decodificación hasta que no cambia, con un máximo de 8 rondas.
   - Si se alcanza el máximo, es lectura opaca → deny.
   - Se toma el criterio del prototipo `lc15/proto15.py`.
   - Las 9 sondas y los 13 hits confirmados entran al corpus con bash real.
   - El barrido G4 de `fz` debe dar 0 allow que ejecuten git, sobre una muestra con bash real de al menos 200.
3. **Envoltorios por tabla única** (gaps 3, 4, 6 y 7).
   - Cada envoltorio declara sus opciones con argumento, su opción de orden en cadena (`flock -c/--command`, `su -c`, `doas`/`sudo` si se tratan) y si acepta `--`.
   - Se normaliza por el nombre base (`/usr/bin/time` → `time`).
   - Hay que añadir `nohup` con `--` (y que salga de `_CONTROL` o que `_CONTROL` lo desenvuelva), `chrt`, `taskset`, `doas`, `winpty` y `time` por ruta.
   - Las abreviaturas `--split`/`--s…`/`--split=` de env equivalen a `-S`.
   - La cadena de una opción de orden se analiza como `bash -c`, heredando la marca.
   - Sin ventana `toks[:6]`: el intérprete se busca en toda la orden simple, en tiempo lineal.
   - Corpus con bash real para todas las formas de las lentes; `flock` solo donde exista, y si no, en SIN_PARIDAD con el motivo.
4. **Límites declarados** (gap 8). Las expansiones en la palabra de mando, `xargs` con subcomando por stdin y el NUL crudo van en `LIMITE` y en el modelo de amenaza de `implementer.md`, con un ejemplo de cada clase.
5. **Instalador sin regresión de señales** (gaps 5 y 11).
   - Fuera de Windows, el hijo `detached` recibe las señales del instalador. SIGINT, SIGTERM y SIGHUP del padre se reenvían al grupo (`kill(-pid)`), y al salir el padre por cualquier vía se mata el grupo vivo.
   - Test (en Linux, en la réplica): SIGINT al instalador con una CLI colgada → el instalador y todo el grupo mueren en menos de 3 s, y no queda huérfano.
   - Test del gap 8: el stub de Windows responde a `--version` sin arrancar node (el `.cmd` lo resuelve solo). El timeout del test es de 8 s o más en Windows y no se relaja la cota.
   - Verificación: 5 pasadas con 12 bucles de CPU, 0 rojos.
6. **Journal anclado al arranque** (gaps 9 y 10).
   - El plazo de proceso se mide desde el arranque del proceso de captura (marca monotónica al importar), no desde la primera espera.
   - El valor se elige para que el hijo de SessionEnd en frío salga en menos de 800 ms en reposo con 50 K + 5 K y la cola configurada fallida: 10 ejecuciones medidas en el ledger. Con carga, se declara la cifra.
   - La carrera legítima de dos procesos se repite **con** el presupuesto real, y el ledger declara desde qué duración de inicialización se omite la captura y que la recupera `recover`.
7. **Tests sin reloj frágil** (gaps 12 y 13).
   - Separadores: `c` y `g` intercalados con la misma referencia, en cada repetición.
   - OpenCode `gap 10`: `Date.now` congelado en el test.
   - OpenCode `f4fix1 gap 3`: condición en lugar del `setTimeout(150)` y `until` acorde a la carga.
   - El adaptador no lanza `node` por actividad si `sesion.actividad` está apagado; el opt-in se comprueba en el adaptador y en el espejo, regenerando interop.
   - Verificación: 5 pasadas de las suites `opencode-plugin*` y del test de separadores con 12 bucles de CPU, 0 rojos.
8. **Traza** (gap 14). `install/install.mjs` y los ficheros de OpenCode van en `Archivos` de T-23 con su nota, se corrige `Runtimes`, y también la cabecera i1-i9, el test del journal sin declarar, los SHA y el tamaño.

Tras este ciclo:
- réplica Linux completa sin rojo, incluido el test de señales;
- suite node de Windows completa sin rojo, en dos pasadas;
- medida emparejada de T-23 con el equipo libre (la hace el orquestador);
- verificación dirigida de las cuatro lentes.

Si solo quedan Minor sin pérdida de datos, la fase cierra.
