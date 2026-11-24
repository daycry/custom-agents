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
| Fase 3 — Tokens | 5 | 12 | 41.7% | 0 / 36h | 1.1 / 9.7h | 0 / 2.42h | 0 / 2260k |
| Fase 4 — Simplificación del código | 0 | 8 | 0.0% | 0 / 34.5h | 0 / 8.5h | 0 / 2.12h | 0 / 2470k |
| Fase 5 — Alcance y entrenamiento | 0 | 5 | 0% | 0 / 26h | 0 / 6.5h | 0 / 1.62h | 0 / 1800k |
| Fase 6 — Higiene del roadmap | 0 | 3 | 0% | 0 / 10h | 0 / 2.5h | 0 / 0.62h | 0 / 750k |
| **TOTAL** | **16** | **40** | **40.0%** | **0 / 154.5h** | **0 / 40.1h** | **0 / 10.02h** | **0 / 10470k** |

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
- **Tiempo IA (ejec.)**: est. 0.5h · real 111.45h (0.4h del cierre original estimado + 2.53h medidas en fix5 + 0.78h en fix6 + 1.33h en fix7 + 1.55h en fix8 + 3.22h en fix9 + 1.21h en fix10 + 0.43h en fix11 + 2.11h en fix12 + 0.95h en fix13 + 0.45h en fix14 + 1.07h en fix15 + 47.14h en fix16 + 45.00h en fix17 + 2.08h en fix18 `(medido; la ventana de fix18 es la misma de T-06 y de T-23, 21:22 UTC del 2026-11-17 a las 05:34 del 2026-11-18, con espera de suites)` + 0.14h en fix18d `(estimado: ventana de pared del marcador 12:01-12:17 UTC = 0.28h x 0.52, ratio IA/pared medido en fix20)` + 0.64h en fix20 `(medido, marcador T-06-fix20)` + 0.26h en fix22 `(estimado: sin marcador; ventana de pared por commits 16:04-16:36 del 2026-11-19 = 0.5h x 0.52)` + 1.55 en fix24 `(0.55 medido (marcador abierto tras el RED y parte del GREEN; el resto de la sesión, ~1.0 h, estimado))` + 1.2 en fix25 `(0.04 medido (marcador abierto tras el GREEN); resto estimado)`; las ventanas de fix5 a fix15 están compartidas con T-07 y T-23; la cifra anterior, 11.42h, no sumaba las 2.11h de fix12)
- **Archivos**: `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/test_guardrail_check.py`, `agent-kits/shared/test_guardrail_differential.py` (fix5), `tests/test_native_guardrail_dispatch.py`, `docs/agents/implementer.md`, `docs/CONVENTIONS.md` · fix6: `agent-kits/shared/native-guardrail.py`, `hooks/run-hook.mjs`, `hooks/opencode-plugin.js`, `interop/opencode/plugins/custom-agents/index.js` (regenerado), `tests/test_native_guard_failclosed.py` (nuevo), `tests/hook-guard-failclosed.test.mjs` (nuevo), `docs/FLOWS.md`, `docs/en/FLOWS.md` · fix7: `agent-kits/shared/test_guardrail_fix7.py`, `agent-kits/shared/test_guardrail_differential7.py`, `tests/test_native_guard_failclosed7.py`, `tests/native-guard-adapter-failclosed.test.mjs` (nuevos), `docs/INTEROP.md`, `docs/en/INTEROP.md`, `interop/opencode/plugins/custom-agents/index.js` (regenerado), `agent-kits/shared/test_guardrail_differential.py` · fix8: `tests/test_native_guard_scan8.py` y `tests/native-guard-adapter-fix8.test.mjs` y `agent-kits/shared/test_guardrail_fix8.py` (nuevos), `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/native-guardrail.py`, `hooks/run-hook.mjs`, `hooks/opencode-plugin.js`, `interop/opencode/plugins/custom-agents/index.js` (regenerado), `agent-kits/shared/test_guardrail_differential.py`, `agent-kits/shared/test_guardrail_differential7.py`, `tests/test_native_guard_failclosed.py`, `tests/test_graphiti_security.py` (huella del lanzador), `docs/INTEROP.md`, `docs/en/INTEROP.md`, `docs/agents/implementer.md` · fix9: `agent-kits/shared/test_guardrail_fix9.py` y `tests/test_native_guard_parity9.py` y `tests/native-guard-adapter-fix9.test.mjs` (nuevos), `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/native-guardrail.py`, `hooks/opencode-plugin.js`, `interop/opencode/plugins/custom-agents/index.js` (regenerado), `agent-kits/shared/test_guardrail_differential7.py` (BAD9_PARIDAD y LEGIT9), `agent-kits/shared/test_guardrail_fix8.py` (`env -S 'echo "hola'` pasa a denegado), `docs/agents/implementer.md`, `docs/INTEROP.md`, `docs/en/INTEROP.md` · fix10: `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/native-guardrail.py`, `hooks/run-hook.mjs`, `hooks/opencode-plugin.js`, `interop/opencode/plugins/custom-agents/index.js` (regenerado), `agent-kits/shared/test_guardrail_differential7.py`, `agent-kits/shared/test_guardrail_fix10.py` (nuevo), `tests/test_native_guard_parity9.py`, `tests/opencode-realpath-fix10.test.mjs` (nuevo), `tests/native-guard-adapter-fix9.test.mjs`, `tests/test_graphiti_security.py` (huella), `docs/agents/implementer.md`, `docs/INTEROP.md`, `docs/en/INTEROP.md` · fix11: `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/test_guardrail_differential7.py`, `agent-kits/shared/test_guardrail_fix11.py` (nuevo), `hooks/opencode-plugin.js`, `interop/opencode/plugins/custom-agents/index.js` (regenerado), `tests/opencode-realpath-fix11.test.mjs` (nuevo), `docs/agents/implementer.md` · fix12: `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/test_guardrail_fix12.py` (nuevo), `agent-kits/shared/test_guardrail_fix11.py`, `agent-kits/shared/test_guardrail_differential.py`, `agent-kits/shared/test_guardrail_differential7.py`, `docs/agents/implementer.md` · fix13: `agent-kits/shared/test_guardrail_fix13.py` (nuevo), `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/test_guardrail_fix12.py`, `agent-kits/shared/test_guardrail_differential7.py`, `docs/agents/implementer.md`, `docs/roadmap/2026-11-10-plugin-audit-2/execution-history.md` · fix14: `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/test_guardrail_fix14.py` (nuevo), `agent-kits/shared/test_guardrail_fix14_corpus.py` (nuevo), `agent-kits/shared/test_guardrail_fix10.py`, `agent-kits/shared/test_guardrail_fix12.py`, `agent-kits/shared/test_guardrail_fix13.py`, `docs/agents/implementer.md` · fix14 y fix15 (declarados en fix15, gap 14): `agent-kits/shared/test_guardrail_fix14.py`, `agent-kits/shared/test_guardrail_fix14_corpus.py`, `agent-kits/shared/test_guardrail_fix15.py` y `agent-kits/shared/test_guardrail_fix15_corpus.py` (nuevos), `install/install.mjs` (fix14: `detached: true`; fix15: vigilante de señales; declarado también en T-23), `agent-kits/shared/journal-capture.py`, `agent-kits/shared/journal-io.py`, `agent-kits/shared/journal.py`, `hooks/opencode-plugin.js` (ver T-23) · fix16: `agent-kits/shared/test_guardrail_fix16.py` (nuevo), `agent-kits/shared/test_guardrail_fix16_corpus.py` (nuevo: BYPASS16, PROBES16, G1_PROBES16, LIMITE16), `agent-kits/shared/test_journal_fix16.py` (nuevo), `agent-kits/shared/test_guardrail_differential.py` y `agent-kits/shared/test_guardrail_differential7.py` (las formas que eran LIMITE y ahora se deniegan pasan a BAD6/BAD7), `agent-kits/shared/test_guardrail_fix15.py` (límites de rondas), `agent-kits/shared/native-guardrail.py` (rama barata), `docs/agents/implementer.md`, `agent-kits/shared/test_guardrail_fix17.py` y `agent-kits/shared/test_guardrail_fix17_corpus.py` (fix17: nuevos), `agent-kits/shared/test_guardrail_fix7.py`, `agent-kits/shared/test_guardrail_check.py` y `agent-kits/shared/test_guardrail_fix16.py` (fix17: las formas de «otra rama de trabajo» pasan a la lista de denegadas por la lista blanca; el arnés de fix16 acepta `locale`), `agent-kits/shared/test_guardrail_fix15.py` (fix17, gap 6: el arnés decide por el registro del shim) · fix18: `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/test_guardrail_fix18.py`, `agent-kits/shared/test_guardrail_fix18_corpus.py`, `agent-kits/shared/test_guardrail_fix17.py`, `agent-kits/shared/test_guardrail_fix17_corpus.py`, `docs/agents/implementer.md` · fix18d: `agent-kits/shared/agent-activity-store.py`, `tests/test_agent_activity_tail.py` · fix25 (intento 20): `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/test_guardrail_fix25.py` (nuevo), `agent-kits/shared/test_guardrail_check.py`, `agent-kits/shared/test_guardrail_differential.py`, `agent-kits/shared/test_guardrail_differential7.py`, `agent-kits/shared/test_guardrail_fix17_corpus.py`, `agent-kits/shared/test_guardrail_fix18_corpus.py`, `docs/agents/implementer.md` · fix24 (intento 19): `agent-kits/shared/guardrail-check.py`, `agent-kits/shared/test_guardrail_fix24.py`, `agent-kits/shared/test_guardrail_check.py`, `agent-kits/shared/test_guardrail_fix17.py`, `agent-kits/shared/test_guardrail_fix17_corpus.py`, `agent-kits/shared/test_guardrail_fix18.py`, `agent-kits/shared/test_guardrail_fix18_corpus.py`, `docs/agents/implementer.md`, `tests/test_agent_activity_tail.py` (D2 con la cola cerca del umbral, docstring de fix20), `tests/test_agent_activity_store.py` (hijos de D2 con plazos reales)
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

**fix18, fix24 y fix25 de T-06** — archivados LITERALMENTE (bytes sin cambios: diseño k1-k13, RED, GREEN, diferenciales, lista blanca de subcomandos y de opciones, mutantes y verificaciones) en [execution-history.md](execution-history.md), sección «Archivado 2026-11-20 — T-06 fix18, fix24 y fix25» · SHA-256 `5ad46404cea7a8a4f6c643b45fd3ea9c473e34f430ea62089b4315218c88a9fa`. Se movieron el 2026-11-20 por el tope de lectura de 256 KiB, antes de la Fase 3. Cierre de la Fase 1 y deuda aceptada: trazas de los intentos 19 y 21 (abajo).

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

**T-07 fix1 a fix8** — archivado LITERALMENTE (bytes sin cambios: RED, GREEN, gaps corregidos y verificaciones) en [execution-history.md](execution-history.md), sección «Archivado 2026-11-24 — T-07 fix1 a fix8» · SHA-256 `1a2d3fc7f867a4d3012f110942bfc05ed46a660f4edd269b32fcd576ced92c0a`. Tarea cerrada; se movió el 2026-11-24 por el tope de lectura de 256 KiB.
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
- **Archivos**: **Se borran (35):** `skills/knowledge-services/backends/{graphiti,graphiti_model,graphiti_provenance,graphiti_providers,graphiti_publication,graphiti_rebuild,graphiti_scope,markdown_export}.py`, `skills/knowledge-services/scripts/{_mcp_fake,kwipu-project-add}.py`, `skills/knowledge-services/scripts/test_{backend_graphiti,backend_markdown_export,backend_markdown_read,backend_markdown_http,graphiti_*,kwipu_metadata,kwipu_project_add}.py`, `skills/knowledge-services/scripts/fixtures/graphiti/`, `skills/knowledge-services/scripts/fixtures/kwipu-*.json`, `tests/test_graphiti_model.py`. **Se divide:** `tests/test_graphiti_security.py` → `tests/test_hook_network_egress.py` (nuevo nombre). **Se editan (código y config):** `agent-kits/shared/{capabilities,knowledge-schema,knowledge-taxonomy-local}.py` (solo claves y funciones de backend; `outbox.py` solo cambia un comentario de cabecera), `agent-kits/shared/copias.json`, `agent-kits/shared/templates/taxonomy.json`, `agent-kits/shared/schemas/taxonomy.schema.json`, `skills/knowledge-services/scripts/knowledge-sync.py` (2 menciones), `skills/plugin-panel/scripts/panel_data.py`, `skills/plugin-panel/assets/{console-context,page-memoria}.js`. **Se editan (tests, 30):** `agent-kits/shared/test_{capabilities,doctor,knowledge_schema,knowledge_routing,knowledge_derivative_surface}.py`, `skills/knowledge-services/scripts/test_{knowledge_sync,backends_init,backend_verification}.py`, `skills/knowledge-category-template/scripts/test_category_template.py`, `tests/{memoria_fixture,test_audit_journal,test_audit_knowledge,test_console_encoding,test_control_center_http,test_knowledge_approved_retrieval,test_knowledge_candidates,test_knowledge_find,test_knowledge_prompt_split,test_knowledge_router,test_knowledge_router_read,test_knowledge_services,test_panel_data,test_panel_fix4,test_panel_memoria_fix1,test_private_state_dirs,test_training_data_services,test_hook_launcher_security}.py`, `tests/test_panel_memoria_ui.py`, `tests/hook-budget.test.mjs` (comentario), `interop/**` (regenerado). **Añadidos al ejecutar (nota 2026-11-19):** `skills/knowledge-services/backends/__init__.py` (mensaje «retirado»: `RETIRADOS`, `VERSION_RETIRADA`), `docs/roadmap/2026-11-10-plugin-audit-2/testing/retirada.md`, `agent-kits/shared/{knowledge-find,knowledge-local,doctor,outbox}.py` (el router deja de derivar `group_id`; comentarios), `agent-kits/shared/{test_knowledge_routing.py,fixtures/derived-read.json}` (renombrada de `graphiti-derived-read.json`), `skills/knowledge-services/{SKILL.md,backends/README.md,references/project-integration.md}` (reescritos como marco sin adaptadores: sin ello el paquete portable cita ficheros borrados), `skills/knowledge-services/scripts/test_backend_verification.py` (reescrita sobre el adaptador de prueba), `skills/knowledge-services/scripts/test_manifest_publication.py` (borrada: probaba la finalización del manifiesto Windows del adaptador Kwipu), `tests/{test_knowledge_router_read,test_audit_knowledge,test_audit_journal,test_hook_network_egress}.py`, `tests/fixtures/opencode-v2-agent-contract.json`, `skills/knowledge-category-template/scripts/test_category_template.py`, `.gitignore`. **No se toca:** `skills/training-data-services/**` (congelada; su clave `bridge_to_kwipu` la retira T-32 si se aprueba), `.claude/knowledge-services/taxonomy.json` (local del usuario, ver «acciones»). **Añadidos en fix1/fix2 (nota):** `tests/test_sync_write_gate.py` (puerta CA-05 restaurada).
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

**T-08 fix1 y fix2** — archivado LITERALMENTE (bytes sin cambios: RED, GREEN, gaps corregidos y verificaciones) en [execution-history.md](execution-history.md), sección «Archivado 2026-11-24 — T-08 fix1 y fix2» · SHA-256 `108652b2944cf5330a86bd82495ae9aad5187dffff0fcc836721b9bf89275645`. Tarea cerrada; se movió el 2026-11-24 por el tope de lectura de 256 KiB.

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

**T-09 fix1 y fix2** — archivado LITERALMENTE (bytes sin cambios: RED, GREEN, gaps corregidos y verificaciones) en [execution-history.md](execution-history.md), sección «Archivado 2026-11-24 — T-09 fix1 y fix2» · SHA-256 `6d5a8876fb7626570b4cc59854d7657efc4db267354da1f4eae117686a416941`. Tarea cerrada; se movió el 2026-11-24 por el tope de lectura de 256 KiB.

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
- **Archivos**: **Se crean:** `skills/knowledge-services/scripts/fixtures/adaptador_prueba.py` (las 6 funciones, en memoria, deterministas), `skills/knowledge-services/references/add-backend.md` (guía; espejo EN si la guía entra en `docs/en/`). **Se editan:** `skills/knowledge-services/{SKILL.md,backends/README.md,references/project-integration.md}`, `skills/knowledge-services/scripts/test_{backends_init,backend_verification,knowledge_sync,knowledge_sync_replay,manifest_publication}.py` (adaptador de prueba en vez de `markdown_export`), `agent-kits/shared/capabilities.py` (solo si queda una referencia a los adaptadores retirados), `agent-kits/shared/test_capabilities.py`, `evals/cases/skill-knowledge-services.json` (description real), `docs/{,en/}guides/memory.md` (enlace a la guía), `interop/**` (regenerado). **Añadidos al ejecutar (nota 2026-11-19):** `skills/knowledge-services/scripts/test_backends_init.py` (nuevo test de la guía y de que `backends/` no trae adaptadores), `commands/{setup,doctor}.md`, `agent-kits/shared/doctor-reference.md` y `docs/en/reference/doctor.md` (citan la guía), `docs/{,en/}guides/memory.md` (enlace a la guía, W-20), `skills/knowledge-services/references/project-integration.md`. `test_manifest_publication.py` se BORRA en vez de reapuntarse: probaba la finalización del manifiesto Windows (`_retryable_manifest_error`, lector nativo con `CreateFileW`) del adaptador Kwipu; el adaptador de prueba no tiene ese comportamiento y el diario de recuperación del marco lo cubre `test_knowledge_sync_replay.py` (parcial + reanudación). El adaptador de prueba guarda su estado en una carpeta (`cfg["dir"]`), no «en memoria»: el cargador relee el módulo en cada corrida y las suites de reanudación necesitan que el estado sobreviva entre llamadas. **No se borra:** nada del marco; `outbox.py`, el journal y `knowledge-find.py --intent` quedan intactos. **Añadidos en fix1/fix2 (nota):** `skills/knowledge-services/scripts/test_adaptador_prueba_contencion.py` (contención del adaptador de prueba).
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

**T-10 fix1 y fix2** — archivado LITERALMENTE (bytes sin cambios: RED, GREEN, gaps corregidos y verificaciones) en [execution-history.md](execution-history.md), sección «Archivado 2026-11-24 — T-10 fix1 y fix2» · SHA-256 `d7950dbe26c076f0497418cd41b647a4950a8bf76ab4484ce3d646be1d900449`. Tarea cerrada; se movió el 2026-11-24 por el tope de lectura de 256 KiB.

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
- **Archivos**: `skills/plugin-dev/**` → `skills/project-extensions/**` (`SKILL.md` ≤ 200 líneas; `templates/` por runtime: agente Claude/OpenCode `.md`, agente Codex `.toml`, skill, comando, hook, tool OpenCode, entrada MCP; `references/{piece-boundaries,claude-code-contracts,tool-observation-contracts,persistent-workflows,architecture-diagnostics}.md` revisadas a genérico; `references/custom-agents-repo.md` nuevo), `agent-kits/shared/{README.md,capability-selection.md,modules.json,rationalization-table.md,skill-index.py}`, `scripts/{export-skills,lint_plugin}.py`, `tests/{test_export_skills,test_session_context}.py`, `tests/test_project_extensions_skill.py` (nuevo), `evals/cases/skill-plugin-dev.json` → `evals/cases/skill-project-extensions.json`, `evals/cases/skill-changelog-sync.json`, `.github/ISSUE_TEMPLATE/pieza-nueva.yml`, `github-templates.MANUAL-COPY/ISSUE_TEMPLATE/pieza-nueva.yml`, `hooks/session-journal.sh` (comentario), `CLAUDE.md`, `CONTRIBUTING.md`, `README.md`, `README.es.md`, `docs/{PROJECT-EXTENSIONS,CUSTOMIZATION,INSTALL,INTEGRATION-ROADMAP,README,observability}.md`, `docs/en/{PROJECT-EXTENSIONS,CUSTOMIZATION,INSTALL,INTEGRATION-ROADMAP,README,observability}.md`, `docs/agents/ROLES.md`, `docs/guides/quality-playbook.md`, `.claude-plugin/{plugin,marketplace}.json` (si listan skills), `interop/**`, `.codex-plugin/plugin.json` y `.agents/plugins/marketplace.json` (regenerados) **Añadido en fix2 (nota):** `tests/test_project_pieces.py` (aviso de línea de frontmatter sin clave) y `agent-kits/shared/project-pieces.py`.
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

**T-11 fix1 y fix2** — archivado LITERALMENTE (bytes sin cambios: RED, GREEN, gaps corregidos y verificaciones) en [execution-history.md](execution-history.md), sección «Archivado 2026-11-24 — T-11 fix1 y fix2» · SHA-256 `b98fd76e198cba3c031deadd0d9fca0740fc9a7220370430f19463088ccb9984`. Tarea cerrada; se movió el 2026-11-24 por el tope de lectura de 256 KiB.

**Criterios de aceptación**
- [x] `skills/project-extensions/` existe y `skills/plugin-dev/` no; sus disparadores son genéricos («crea un agente/skill/comando/hook», «añade un MCP al proyecto») y no citan rutas de este repo.
- [x] Crea agentes, skills, comandos, hooks, tools y MCP en la carpeta y formato de cada runtime de la tabla de `docs/PROJECT-EXTENSIONS.md`, nunca en la caché del plugin, y verifica la pieza con `project-pieces.py`.
- [x] Las reglas propias de este repo están en `references/custom-agents-repo.md` y la skill solo lo lee dentro de custom-agents; `CONTRIBUTING.md` y `CLAUDE.md` apuntan a él.

**Puerta de runtimes de la fase 2** — archivado LITERALMENTE (bytes sin cambios: RED, GREEN, gaps corregidos y verificaciones) en [execution-history.md](execution-history.md), sección «Archivado 2026-11-24 — Puerta de runtimes de la fase 2» · SHA-256 `e0692797dfc9ddb3771a97948d6c1c4ddaa938a187678b70df9fc241120e4762`. Tarea cerrada; se movió el 2026-11-24 por el tope de lectura de 256 KiB.

## Fase 3 — Tokens

**Estado**: en-progreso · **Est.**: 30h humanas · **Real**: — · 1500 € · 2260k tokens

### T-12 — TDD en el brief, skill bajo demanda (2.4)

- **Descripción**: Con `tdd: true` cada subagente carga la skill `tdd` entera (≈10 KB) aunque el brief de `task-brief.py` ya trae la sección TDD. Se mueve al brief la ley dura y el formato `RED:` y se manda abrir la skill solo ante una duda (stack concreto, `TDD n/a`). Ahorro estimado ≈ 25 K tokens por ciclo con subagentes.
- **Changelog**: El brief de cada tarea trae la regla TDD esencial y el subagente ya no carga la skill completa.
- **Estado**: completado
- **Cerrada**: 2026-11-20
- **Tiempo humano**: est. 2h · real —
- **Tiempo IA (ejec.)**: est. 0.5h · real 0.58h (medido, `plugin-audit-2/T-12`)
- **Archivos**: `agent-kits/shared/task-brief.py`, `agent-kits/shared/test_task_brief.py`, `agent-kits/dev-cycle/references/phase3-subagents.md`, `agents/implementer.md`, `skills/tdd/SKILL.md`, `docs/{,en/}TOKEN-EFFICIENCY.md`, `interop/**` (regenerado), `tests/fixtures/dev-cycle-modular-replacements.json` (nota: el paréntesis TDD de `phase3-subagents.md` cambia y su fila de sustitución pasa al hash nuevo, o `test_dev_cycle_split.py::test_no_original_paragraph_is_lost` falla), `docs/roadmap/2026-11-10-plugin-audit-2/testing/tokens.md` (nota del orquestador, 2026-11-23: registro de medidas de toda la Fase 3 que citan las Verificaciones; lo escribe el orquestador desde el informe del implementer) Fix2: `CHANGELOG.md` y `CHANGELOG.es.md` (nota bilingüe en Changed, desde Changelog).
- RED: agent-kits/shared/test_task_brief.py::test_tdd_resumido_trae_lo_esencial_y_la_skill_queda_bajo_demanda falló con AssertionError: 'Ley dura' no estaba en la sección TDD del brief (commit `e2b7cc0`) · 2026-11-20
- **Evidencia** (GREEN `a701e11`; tamaños = caracteres UTF-8 con LF de `context-footprint.py`, estimación caracteres/4, no consumo facturado):
  - Brief (`TDD_BRIEF`): sin la orden «invócala con la herramienta Skill»; trae la ley dura literal, el formato `RED: <fichero::test> falló con <error> · <AAAA-MM-DD>`, rojo por la razón correcta, qué NO es TDD y `TDD n/a: <motivo>`; cita `skills/tdd/SKILL.md` como fuente única, a abrir «solo ante una duda» (stack, `TDD n/a`). La sección pasa de 680 a 807 bytes (≤ 2 KB).
  - Medida (brief de T-12 sobre una copia del ledger, `--tdd`): implementer 29.280 + brief 7.271 + skill 10.111 = 46.662 → implementer 29.268 + brief 7.398 = 36.666: **−9.996** (≥ 8 KB). La skill (10.304, +1 párrafo que dice que el brief lleva lo esencial) ya no se carga siempre. Sin `tdd` el brief no cambia: `cmp` byte a byte de los briefs de T-12 y T-15 con `tdd: false` antes/después → idénticos.
  - `pytest -q -n 3 agent-kits/shared/test_task_brief.py` → `95 passed`; `tests/test_dev_cycle_split.py` → `11 passed`; diet-check `tdd` → 0 párrafos perdidos; puertas de tokens: vía rápida 6.012, `agents/evaluator.md` 15.465 bytes LF.
  - Interpretaciones: **k1** el brief ya traía un resumen de la ley dura y `RED:`; el rojo exigible era la orden de cargar la skill entera y lo que faltaba (razón correcta, qué no es TDD), no «sin ley dura ni `RED:`» como decía la Verificación. **k2** `test_brief_budget_auxiliares_comparten_margen_sin_recortar_criterios` no era hermético: leía el `.claude/dev.json` del checkout (`tdd: true`) y con la sección TDD +127 pasaba del tope; se hace hermético con `chdir` (en CI no hay `dev.json` y el escenario mide sin TDD). **k3** la fila «Cuándo aplica» de la skill no se reescribe (el diet-check la daría por perdida): se añade un párrafo.
- **Runtimes**: El brief es texto de `task-brief.py` que recibe el subagente en cualquier runtime.
- **Verificación**:
  - `pytest -q agent-kits/shared/test_task_brief.py -k tdd_resumido` → `passed` (rojo antes: el brief no incluye el formato `RED:` ni la ley dura)
  - `context-footprint.py --project . --file agents/implementer.md` antes/después → menos bytes (`testing/tokens.md`) · tamaño del brief generado (`task-brief.py` sobre una tarea de prueba) medido antes y después
  - puertas de runtimes (cabecera) → verde
- **Verificación ejecutada** (2026-11-20): `-k tdd_resumido` → `1 passed`; implementer 29.280 → 29.268 caracteres y brief de T-12 7.271 → 7.398 (en la Evidencia); `export-interop.py --check` → `88 ficheros al día`; `pytest -q -n 3 tests/test_export_interop.py tests/test_plugin_root_resolution.py tests/test_native_role_context.py tests/test_native_guardrail_dispatch.py tests/test_native_prefilter_parity.py` → `102 passed`; `node --test` de la cabecera, en la pasada común del cierre de la tanda (ver T-20).

**Criterios de aceptación**
- [x] El brief con `tdd: true` incluye la ley dura y el formato `RED:`; sin `tdd` no cambia.
- [x] Ninguna puerta de la skill `tdd` desaparece: sigue siendo la fuente única y el brief la cita.
- [x] Medida antes/después registrada (estimada, no consumo facturado).
- [x] Medido: agente + brief con `tdd: true` baja ≥ 8 KB (la skill ≈ 10 KB deja de cargarse; el brief gana ≤ 2 KB).

**fix2 (intento 2 de la Fase 3, gaps 9; 2026-11-23; Codex gpt-6.2-sol)**
- Changelog bilingüe en Changed desde el campo Changelog. `test_fix2_gap9_changelogs_bilingues_en_changed_y_trazados_por_tarea` verde en `04d719b` (RED `41cf29c`).

### T-13 — Tabla de lentes fuera de adversarial-review/SKILL.md (2.5)

- **Descripción**: El revisor abre `skills/adversarial-review/SKILL.md` (18,6 KB) para leer una tabla de ≈4 KB. La tabla pasa a `references/` o al prompt de la lente y el SKILL conserva el mapa. Ahorro estimado hasta ≈21 K tokens por ciclo.
- **Changelog**: El revisor lee solo la tabla de lentes que necesita, no toda la skill de revisión adversarial.
- **Estado**: completado
- **Cerrada**: 2026-11-20
- **Tiempo humano**: est. 1.5h · real —
- **Tiempo IA (ejec.)**: est. 0.4h · real 0.08h (medido, `plugin-audit-2/T-13`; su ventana se solapa con el cierre de T-12)
- **Archivos**: `skills/adversarial-review/SKILL.md`, `skills/adversarial-review/references/lentes.md` (nuevo), `agents/reviewer.md`, `docs/agents/reviewer.md`, `interop/**` (regenerado), `docs/{,en/}TOKEN-EFFICIENCY.md` (nota: regla de CLAUDE.md al cambiar la disciplina de contexto), `tests/test_rationalization_tables.py` (nota: fijaba la tabla del revisor dentro de `SKILL.md`; ahora la busca en `lentes.md` y afirma que el SKILL y el reviewer remiten a ella), `agent-kits/shared/rationalization-table.md` (nota: «Quién la lleva hoy» citaba el SKILL) Fix2: `CHANGELOG.md` y `CHANGELOG.es.md` (nota bilingüe en Changed, desde Changelog). `tests/test_phase3_review_contract.py` (contrato de la vista y revisión, índice por runtime y M-C, según tarea).
- TDD n/a: prosa (traslado de texto entre `SKILL.md` y una referencia; lo fijan el diet-check y `test_rationalization_tables.py`)
- **Evidencia** (commit `f8009e5`; caracteres UTF-8 con LF de `context-footprint.py`, estimación caracteres/4, no consumo facturado):
  - Lo que lee el revisor: `skills/adversarial-review/SKILL.md` 18.104 → `references/lentes.md` 3.012 (**−15.092** por lectura, ≤ 5 KB). El `SKILL.md` queda en 16.471 (tras T-14, 16.878) y `agents/reviewer.md` en 8.833 (+184: dice que lee solo `lentes.md`, nunca el SKILL entero; C/D abren su heurística solo si un motivo sorprende).
  - `lentes.md` lleva la graduación (Critical/Important/Minor, copia de la definición de §3, que se queda en el SKILL para la fusión) y la tabla «Racionalizaciones del REVISOR» movida tal cual; el SKILL conserva el encabezado con un puntero y la cita en «Scripts propios».
  - `python tests/test_skill_size.py --diet-check adversarial-review a701e11` → `0 párrafos perdidos`; `pytest -q tests/test_rationalization_tables.py tests/test_integration_decoupling.py tests/test_review_cycle_owner.py agent-kits/shared/test_scope_check.py` → `58 passed`; `lint_plugin.py` → `0 errores · 16 avisos` (los mismos 16 de antes); `evals/check.py` → `0 errores`.
  - Interpretación **k4**: el ledger llamaba `lentes.md` al fichero y ya existía `references/lens-prompts.md` (10.689 bytes, los prompts que la skill entrega en el despacho): meter la tabla ahí dejaba al revisor por encima de 5 KB, así que va en el `lentes.md` nuevo. «Solo la referencia de la lente» se lee como: `lentes.md` + el prompt de su lente (que le llega en el despacho) + la heurística C/D solo si hace falta.
- **Runtimes**: La referencia vive en `skills/`, que viaja sin traducir (`docs/INTEROP.md:31`); el revisor la halla con la receta de seis raíces.
- **Verificación**:
  - `context-footprint.py --project . --file skills/adversarial-review/SKILL.md` antes/después → menos bytes (`testing/tokens.md`); fichero nuevo medido aparte
  - puertas de runtimes (cabecera) → verde
- **Verificación ejecutada** (2026-11-20): `SKILL.md` 18.104 → 16.471 caracteres y `lentes.md` 3.012 medido aparte; `export-interop.py --check` → `88 ficheros al día`; las pytest de runtimes de la cabecera y `node --test`, en la pasada común del cierre de la tanda (ver T-20).

**fix1 (intento 1 de la Fase 3, gaps 1; 2026-11-23; implementado por Codex gpt-6.2-sol)**
- TDD n/a: prosa. Criterios literales conservados en el prompt de la Lente A.
- GREEN `f627de3`: `--diet-check adversarial-review a701e11`, 0 párrafos perdidos. `context-footprint.py --file agents/reviewer.md` mide 9.062 caracteres (antes 8.833).

**Criterios de aceptación**
- [x] El reviewer lee solo la referencia de la lente.
- [x] La skill conserva todos los criterios y severidades (`--diet-check`: 0 párrafos perdidos).
- [x] Medido: lo que lee el revisor baja de 18,6 KB a ≤ 5 KB (≥ 13 KB menos por lectura).

**fix2 (intento 2 de la Fase 3, gaps 2 y 9; 2026-11-23; Codex gpt-6.2-sol)**
- El contrato de Lente A se comprueba en el prompt literal y el revisor (`test_intento1_gap1_lente_a_y_reviewer_piden_la_vista_de_fase`); el mutante «y `tasks.md`» cae y `cmp` confirma la restauración.
- Changelog bilingüe por tarea (`test_fix2_gap9_changelogs_bilingues_en_changed_y_trazados_por_tarea`). RED `41cf29c` · GREEN `04d719b`.

### T-14 — Freno de tokens del ledger (2.1)

- **Descripción**: `ledger-lint.py` avisa a 183.500 bytes (`UMBRAL_TAMANO_BYTES`), cuando una lectura ya cuesta ≈45 K tokens. Umbral a 40-60 KB, archivado por fase con `ledger-archive.py` (ya existe) y Lente A solo sobre la fase revisada. Ahorro [E] ≈30 K tokens por lectura.
- **Changelog**: Los ledgers avisan antes de crecer, se archivan por fase y la revisión lee solo la fase en curso.
- **Estado**: completado
- **Cerrada**: 2026-11-20
- **Tiempo humano**: est. 5h · real —
- **Tiempo IA (ejec.)**: est. 1.5h · real 0.31h (medido, `plugin-audit-2/T-14`; el GREEN de T-21 y parte de T-20 se escribieron en esta misma ventana mientras corrían las suites)
- **Archivos**: `agent-kits/shared/ledger-lint.py`, `tests/test_ledger_lint.py`, `agent-kits/shared/ledger-archive.py`, `agent-kits/shared/test_ledger_archive.py`, `commands/dev-cycle.md`, `skills/adversarial-review/SKILL.md`, `agent-kits/shared/task-brief.py`, `docs/{,en/}CONVENTIONS.md`, `docs/{,en/}TOKEN-EFFICIENCY.md`, `interop/**` (regenerado), `agent-kits/shared/test_task_brief.py` (nota: tests del modo `--fase`), `agent-kits/shared/README.md` (nota: su fila de `ledger-lint.py` decía «70 % del tope»), `tests/fixtures/dev-cycle-modular-replacements.json` (nota: el párrafo «Ledger grande» de `dev-cycle.md` cambia y su fila de sustitución pasa al hash nuevo). `ledger-archive.py` y su test no cambian: el archivado ya conservaba bytes y SHA. Fix1: `skills/adversarial-review/references/lens-prompts.md` y `agents/reviewer.md` (contrato de entrada de la Lente A); `docs/agents/CONTRACTS.md` (arista E8). Fix2: `CHANGELOG.md` y `CHANGELOG.es.md` (nota bilingüe en Changed, desde Changelog). `tests/test_phase3_review_contract.py` (contrato de la vista y revisión, índice por runtime y M-C, según tarea).
- RED: tests/test_ledger_lint.py::test_umbral_tokens_un_ledger_de_70_kb_avisa_y_nombra_ledger_archive falló con AssertionError: «ledger-lint: 0 incoherencias · 0 avisos» (un ledger de 70 KB no avisaba); ::test_umbral_tokens_por_defecto_a_60_kb_como_mucho_y_configurable falló con assert 183500 <= 60000 (commit `b69d54d`) · 2026-11-20
- RED: agent-kits/shared/test_task_brief.py::test_fase_lente_a_recibe_solo_la_fase_revisada_de_un_ledger_grande (y los 2 de `fase_lente_a`) falló con SystemExit 2: «unrecognized arguments: --fase» (commit `b69d54d`) · 2026-11-20
- RED fix1: agent-kits/shared/test_task_brief.py::test_fase_lente_a_sin_ledger_lint_entrega_el_ledger_entero falló con AssertionError (sin ledger-lint.py la vista recortaba con una copia del umbral) sobre el `task-brief.py` del commit `e8cceba` puesto en su sitio y restaurado con `cmp` (commit `2f70905`) · 2026-11-20
- **Evidencia** (GREEN `04ab577`, fix1 `9839d05`; tamaños en bytes; estimación, no consumo facturado):
  - Riesgo de cierre (fix2): `changelog-sync` saltará `plugin-audit-2` al cerrar porque el slug ya figura en la sección sin publicar (regla de idempotencia, `skills/changelog-sync/SKILL.md:103`).
  - `ledger-lint.py`: `UMBRAL_TAMANO_BYTES` 183.500 → **60.000**, configurable con `--umbral-bytes N` (y `lint(..., umbral_bytes=)`); el aviso dice «ledger de N KB (aviso a 60 KB por tokens; tope de lectura 256 KiB): archiva la historia cerrada con `python3 agent-kits/shared/ledger-archive.py <carpeta> --apply`». Un ledger de 20 KB no avisa. Este ledger (≈190 KB) pasa a avisar: esperado, no se archiva aquí.
  - `task-brief.py <carpeta> --fase <N>`: por encima del umbral, la cabecera del ledger (lo anterior a la primera `## `) + la sección `## Fase N` íntegra (todas sus tareas, criterios y verificaciones); por debajo, el ledger entero como hoy; fase inexistente → exit 1; sin `ledger-lint.py`, el ledger entero (fix1: `lint_plugin.py` daba `❌ constante de respaldo _LEDGER_FALLBACK SIN fila en copias.json (ADR-016)` por la copia del umbral; se quita la copia).
  - Medido: Lente A para el ledger de prueba de 4 fases (100.414 bytes) → 25.253 (**−75 %**); sobre una copia del ledger real (189.819): fase 1 57.123, fase 2 52.268, fase 3 21.232 (−70 % a −89 %).
  - `/dev-cycle` (cierre de fase, «Ledger grande»): OFRECE archivar — plan en seco de `ledger-archive.py` y, con OK del usuario, `--apply`; `adversarial-review` §2 manda pasar a la Lente A la vista `--fase N`; `CONVENTIONS` ES/EN y la fila de `README.md` del kit al día.
  - `pytest -q -n 3` de `tests/test_ledger_lint.py`, `test_ledger_archive.py`, `test_ledger_view.py`, `test_progress_report.py`, `tests/test_ledger_post.py`, `test_ledger_single_parser.py`, `test_ledger_write.py`, `test_audit_ledger.py`, `test_audit_briefs.py`, `test_task_brief.py`, `test_dev_cycle_split.py`, `test_skill_size.py`, `test_rationalization_tables.py`, `test_f4fix2_misc.py`, `test_token_efficiency_distribution.py`, `test_context_footprint.py`, `test_source_snapshot.py` → `417 passed, 5 skipped`; tras fix1, `-k fase_lente_a` → `4 passed` y `lint_plugin.py` → `0 errores · 16 avisos`.
  - Puertas de tokens: vía rápida 6.012 → **6.023**; `agents/evaluator.md` 15.465 bytes LF; diet-check `adversarial-review` → 0 párrafos perdidos.
  - Interpretaciones: **k5** «configurable» = `--umbral-bytes N` en la CLI y en `lint()`, no una clave de `dev.json` (`doctor.py` valida las claves de `dev.json` y no está en `Archivos`). **k6** «archivado por fase» se cumple con la oferta de `ledger-archive.py` al cerrar cada fase; no se añade un modo nuevo de archivado por fase (la Lente A ya recibe solo la fase con `--fase`). **k7** la Verificación pedía `-k umbral_tokens` con «un ledger de 70 KB no avisa» como rojo: así fue.
- **Runtimes**: Sin diferencia: script y prosa de `dev-cycle`; la Lente A es la misma.
- **Verificación**:
  - `pytest -q tests/test_ledger_lint.py -k umbral_tokens` → `passed` (rojo antes: un ledger de 70 KB no avisa)
  - `pytest -q agent-kits/shared/test_ledger_archive.py agent-kits/shared/test_task_brief.py` → verde (archivar conserva bytes y SHA)
  - puertas de runtimes (cabecera) → verde
- **Verificación ejecutada** (2026-11-20): `-k umbral_tokens` → `3 passed`; `test_ledger_archive.py` y `test_task_brief.py` dentro de los `417 passed, 5 skipped`; `export-interop.py --check` → `88 ficheros al día`; pytest de runtimes de la cabecera → `pytest -q -n 3 agent-kits/shared/test_skill_index.py tests/test_session_context.py tests/test_hooks_config.py tests/test_native_role_context.py tests/test_export_interop.py tests/test_plugin_root_resolution.py tests/test_native_guardrail_dispatch.py tests/test_native_prefilter_parity.py tests/test_kit_path_injection.py` → `204 passed` (tras el GREEN de T-20); `node --test` de la cabecera → `263 tests: 254 pass, 3 fail, 6 skipped` con la máquina cargada; los 3 rojos, aislados: `claude: session context runs without Bash` exigía la caché del índice (corregido en `e93c90c`, `9 passed` con los de guardia) y los otros dos eran plazos agotados con carga (`copied implementer … (precedence)` 16,5 s sobre 15 s; `tool activity is dispatched …` 129 s): solos, `pass`. Consola: `node --test tests/console-inventory.test.mjs tests/console-live.test.mjs` → `10 pass`; `pytest -q -n 2 tests/test_console_{snapshots,service,state,encoding}.py tests/test_audit_console.py` → `744 passed, 4 failed` con node en paralelo, y los 4 (`--lf`) → `4 passed` solos.

**fix1 (intento 1 de la Fase 3, gaps 1, 5, 6, 7 y 9; 2026-11-23; implementado por Codex gpt-6.2-sol)**
- TDD n/a: prosa (prompt y documentación).
- RED: test_fix1_fase_lente_a_ignora_encabezados_cercados falló con AssertionError (fase citada antes de la real) · 2026-11-23
- RED: test_fix1_fase_lente_a_delimita_y_neutraliza_la_cita falló con StopIteration (sin marca de inicio) · 2026-11-23
- RED: test_fix1_fase_lente_a_usa_umbral_configurable_y_bytes_crlf falló con SystemExit 2 (flag desconocido) · 2026-11-23
- RED: test_fix1_fase_lente_a_rechaza_umbral_no_positivo falló con AssertionError (sin diagnóstico de positividad) · 2026-11-23
- RED: test_fix1_umbral_tokens_mide_en_bytes_sin_redondear falló con AssertionError (aviso en KB) · 2026-11-23
- RED: test_fix1_umbral_tokens_rechaza_valores_no_positivos falló con AssertionError (exit 0) · 2026-11-23
- RED `31e26a7`; GREEN `f627de3`. `pytest -k 'fase_lente_a or fix1_umbral'` pasó. `task-brief.py … --fase 3`: 42.143 bytes LF frente a 214.452 en disco, puertas comunes presentes. Las citas conservan todo el ledger pequeño; las grandes omiten otras fases. Puertas de tokens: vía rápida 6.023 y evaluator 15.465 bytes LF.

**Criterios de aceptación**
- [x] El aviso salta en el umbral nuevo (configurable) y su texto nombra `ledger-archive.py`.
- [x] El cierre de fase del `/dev-cycle` ofrece archivar; el archivado conserva bytes y SHA.
- [x] La Lente A recibe la fase revisada, no el ledger entero, sin perder los criterios de esa fase.
- [x] Un ledger pequeño se lee igual que hoy.
- [x] Medido: el aviso del ledger salta a ≤ 60.000 bytes (hoy 183.500) y la entrada de la Lente A para 100 KB baja ≥ 50 %.

**fix2 (intento 2 de la Fase 3, gaps 1–4, 7, 9 y 10; 2026-11-23; Codex gpt-6.2-sol)**
- RED: test_fix2_gap1_cercados_y_reparto_por_fase_como_ledger_lint falló con AssertionError: tareas omitidas/sobrantes · 2026-11-23
- RED: test_fix2_gap3_marcas_del_ledger_quedan_dentro_de_la_cita falló con AssertionError: FIN repetido · 2026-11-23
- RED: test_fix2_gap4_neutraliza_encabezados_solo_fuera_de_cercados falló con AssertionError: comentario escapado · 2026-11-23
- RED: test_fix2_gap10_vista_incluye_intentos_en_orden_con_rangos_y_ahorra_50_por_ciento falló con ValueError: revisión ausente · 2026-11-23
- RED `41cf29c` · GREEN `04d719b`. La fase oculta por un cercado sin cerrar conserva exit 1 como `ledger-lint.py:593` (`test_fix2_gap1_cercado_sin_cerrar_antes_de_la_fase`).
- Verificación: rangos y dos intentos en la fase real; ahorro ≥50 % en el ledger sintético; ledger pequeño íntegro. Prosa, modo sin plan y Changed verificados.
- Puertas: pytest 490/2 omitidas; Node Linux con init 256/7 omitidas; interop 88; lint/evals 0 errores; diet 0 pérdidas; vía rápida 6.023; evaluator 15.465 bytes LF.

**fix3 (intento 3 de la Fase 3, gaps 1, 2, 4, 5, 7; 2026-11-23; Codex gpt-6.2-sol)**
- RED: test_fix3_gap2_solo_un_cercado_valido_protege_encabezados falló con AssertionError (encabezado sin escapar) · 2026-11-23
- RED: test_fix3_gap4_verificacion_con_blanco_cercado_conserva_dos_items falló con AssertionError (1 ítem en vez de 2) · 2026-11-23
- RED: test_fix3_gap4_verificacion_real_graphiti_t08_conserva_cuatro_items falló con AssertionError (1 ítem en vez de 4) · 2026-11-23
- RED: test_fix3_gap7_vista_documenta_cabecera_fase_intentos_y_rangos falló con AssertionError (faltan partes de la vista en la prosa) · 2026-11-23
- RED `457e0e8` · GREEN `4369db5`. `pytest -k 'fix3_gap or fix2_gap1_cercados_y_reparto or fix2_gap5 or fix2_gap10'` → 57 passed. Graphiti T-08 recupera los 4 ítems de `d3720a9`. `--diet-check adversarial-review ea18413` → 0 párrafos perdidos.

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
- **Estado**: completado
- **Cerrada**: 2026-11-20
- **Tiempo humano**: est. 2h · real —
- **Tiempo IA (ejec.)**: est. 0.5h · real 0.09h (medido, `plugin-audit-2/T-20`; buena parte del código se escribió en las ventanas de T-14 y T-21, ver la nota de T-14)
- **Archivos**: `hooks/session-context.py`, `agent-kits/shared/skill-index.py`, `tests/test_session_context.py`, `agent-kits/shared/test_skill_index.py`, `docs/{,en/}observability.md`, `interop/**` (regenerado), `hooks/session-context.sh` (nota: es el oráculo de paridad de `test_native_output_matches_shell_bytes`; pasa `--solo-cabecera` igual que el nativo), `tests/test_native_role_context.py` (nota: puerta de runtimes que exigía `custom-agents:planner` en el bloque de Claude; ahora exige la línea de delegación de Claude y ningún ID del runtime reclamado), `docs/{,en/}TOKEN-EFFICIENCY.md` (nota: regla de CLAUDE.md), `tests/hook-runtime.test.mjs` (nota: puerta `node --test` de la cabecera; exigía `.claude/.skill-index.cache` también en Claude, que ya no construye el listado: en Claude exige que no haya `Skills:`; commit `e93c90c`) Fix1: `tests/test_hooks_shell.py` (expectativas por runtime), `docs/{,en/}FLOWS.md` (diagrama de SessionStart). Fix2: `CHANGELOG.md` y `CHANGELOG.es.md` (nota bilingüe en Changed, desde Changelog). `tests/test_phase3_review_contract.py` (contrato de la vista y revisión, índice por runtime y M-C, según tarea).
- RED: tests/test_session_context.py::test_t20_runtime_claude_solo_trae_la_cabecera_del_indice falló con AssertionError: «Comandos:» en el bloque de Claude (índice completo) (commit `ec3eeee`) · 2026-11-20
- **Evidencia** (GREEN `650b2c3`; caracteres; estimación, no consumo facturado):
  - `skill-index.py --solo-cabecera` imprime `cabecera_sola(runtime)`: 3 líneas (la primera remite al listado nativo; las otras dos, las de `CABECERAS_RUNTIME`), sin listado; respeta `sesion.indice: false` (sin salida). `session-context.py` (y el oráculo `.sh`) lo pasan solo con `--runtime claude`.
  - Medido: índice del bloque de Claude 3.378 → 331 caracteres (**−3.047**, ≈ 762 tokens; 3.578 → 335 bytes). Codex 3.349 y OpenCode 3.499: sin cambio (`test_t20_runtime_codex_y_runtime_opencode_conservan_el_indice_completo`, que compara con `skill-index.generar(...)`).
  - Suites: `pytest -q -n 3 agent-kits/shared/test_skill_index.py tests/test_session_context.py tests/test_hooks_config.py tests/test_native_role_context.py tests/test_export_interop.py tests/test_plugin_root_resolution.py tests/test_native_guardrail_dispatch.py tests/test_native_prefilter_parity.py tests/test_kit_path_injection.py` → `204 passed` (tras el GREEN de T-20).
  - Interpretaciones: **k9** el ahorro medido es −3,0 KB, no ≈ 3,4 KB: la cifra del plan era el índice entero y se queda una cabecera de 331. **k10** la primera línea de la cabecera sola no es la del índice («comprueba si aplica una de estas piezas» apuntaba a un listado que ya no va): dice que las piezas están en el listado nativo. **k11** «se contrasta con los evals de activación»: `evals/check.py` (estático) → `0 errores`; los evals reales (`evals/run.py`, `claude -p`) y el paso manual M-C quedan para el usuario.
- **Runtimes**: Solo Claude cambia; Codex y OpenCode conservan el índice completo (lo fija un test).
- **Verificación**:
  - `pytest -q tests/test_session_context.py -k runtime_claude` → `passed` (rojo antes: el bloque trae el índice completo)
  - `pytest -q agent-kits/shared/test_skill_index.py tests/test_hooks_config.py` → verde
  - lectura (manual, sesión real; M-C) → en Codex y OpenCode reales el arranque muestra el índice completo y en Claude solo la cabecera
  - puertas de runtimes (cabecera) → verde
- **Verificación ejecutada** (2026-11-20): `-k runtime_claude` → `1 passed`; `-k "runtime_codex or runtime_opencode"` → `2 passed`; `test_skill_index.py`, `test_hooks_config.py` y puertas pytest de runtimes → `pytest -q -n 3 agent-kits/shared/test_skill_index.py tests/test_session_context.py tests/test_hooks_config.py tests/test_native_role_context.py tests/test_export_interop.py tests/test_plugin_root_resolution.py tests/test_native_guardrail_dispatch.py tests/test_native_prefilter_parity.py tests/test_kit_path_injection.py` → `204 passed` (tras el GREEN de T-20); `export-interop.py --check` → `88 ficheros al día`; `node --test` de la cabecera → `263 tests: 254 pass, 3 fail, 6 skipped` con la máquina cargada; los 3 rojos, aislados: `claude: session context runs without Bash` exigía la caché del índice (corregido en `e93c90c`, `9 passed` con los de guardia) y los otros dos eran plazos agotados con carga (`copied implementer … (precedence)` 16,5 s sobre 15 s; `tool activity is dispatched …` 129 s): solos, `pass`. Consola: `node --test tests/console-inventory.test.mjs tests/console-live.test.mjs` → `10 pass`; `pytest -q -n 2 tests/test_console_{snapshots,service,state,encoding}.py tests/test_audit_console.py` → `744 passed, 4 failed` con node en paralelo, y los 4 (`--lf`) → `4 passed` solos; **M-C pendiente del usuario** (sesión real de Codex, OpenCode y Claude).

**fix1 (intento 1 de la Fase 3, gaps 3, 9 y 10; 2026-11-23; implementado por Codex gpt-6.2-sol)**
- TDD n/a: prosa (diagramas).
- RED: test_session_context_startup_indice_mas_roadmap_bajo_el_tope de la línea base falló en Linux con AssertionError (pedía Comandos: en Claude) · 2026-11-23
- RED: test_fix1_solo_cabecera_rechaza_json falló con AssertionError (exit 0 y texto plano) · 2026-11-23
- RED `31e26a7`; GREEN `f627de3`. `skill-index.py --solo-cabecera --json` rechaza la combinación con exit 2. Linux, archivo Git de GREEN y bind de solo lectura: `pytest -q tests/test_hooks_shell.py tests/test_session_context.py` → 137 passed, 1 skipped. Se verificaron la paridad .py/.sh y `sesion.indice`.

**Criterios de aceptación**
- [x] Runtime `claude`: solo cabecera; `codex` y `opencode`: índice completo como hoy, fijado por test.
- [x] `dev.json` `sesion.indice` sigue mandando y la medida del bloque (≈4,6 KB → menos) queda anotada.
- [x] Medido: en `claude` el bloque de `SessionStart` baja ≈ 3,4 KB (844 tokens); en `codex` y `opencode` no cambia (`-k "runtime_codex or runtime_opencode"`).

**fix2 (intento 2 de la Fase 3, gaps 2 y 9; 2026-11-23; Codex gpt-6.2-sol)**
- Intento 1 gap 9: `test_intento1_gap9_flujos_documentan_el_indice_por_runtime` (ES/EN). Gap 8 adicional: `test_intento1_gap8_m_c_incluye_evals_reales_de_activacion` cubre el texto de M-C, pendiente de ejecución manual.
- Changelog bilingüe por tarea (`test_fix2_gap9_changelogs_bilingues_en_changed_y_trazados_por_tarea`). RED `41cf29c` · GREEN `04d719b`.

### T-21 — Cabecera «ORQUESTA agentes» solo donde despacha (2.14)

- **Descripción**: `export-interop.py` antepone «Este comando ORQUESTA agentes…» (línea 107) a los 16 comandos exportados aunque 12 no despachan (≈600 caracteres por invocación en Codex/OpenCode). Se emite solo si el cuerpo nombra un rol.
- **Changelog**: Los comandos de Codex y OpenCode que no despachan agentes ya no llevan la cabecera de orquestación.
- **Estado**: completado
- **Cerrada**: 2026-11-20
- **Tiempo humano**: est. 1.5h · real —
- **Tiempo IA (ejec.)**: est. 0.4h · real 0.04h (medido, `plugin-audit-2/T-21`; el código se escribió en la ventana de T-14 mientras corrían sus suites, así que la medida se queda corta)
- **Archivos**: `scripts/export-interop.py`, `tests/test_export_interop.py`, `docs/INTEROP.md`, `interop/**` (regenerado), `docs/en/INTEROP.md` (nota: espejo EN, regla bilingüe), `docs/{,en/}TOKEN-EFFICIENCY.md` (nota: regla de CLAUDE.md) Fix2: `CHANGELOG.md` y `CHANGELOG.es.md` (nota bilingüe en Changed, desde Changelog).
- RED: tests/test_export_interop.py::test_cabecera_orquesta_solo_en_los_comandos_que_despachan_un_agente falló con AssertionError (15 de 15 comandos por runtime con la cabecera); ::test_cabecera_orquesta_conserva_la_misma_lista_de_roles falló (el mapa de roles en comandos que no despachan) y ::test_cabecera_orquesta_detecta_el_despacho_en_el_cuerpo con AttributeError: sin `despacha_agentes` (commit `7dbbff9`) · 2026-11-20
- **Evidencia** (GREEN `e8cceba`; caracteres; estimación, no consumo facturado):
  - `despacha_agentes(cuerpo)`: «agente `X`» o un verbo de despacho (despachar, lanzar, invocar, delegar, entregar) seguido del rol en la misma cláusula (sin `.,;:` entre medias), o `subagent_type`; nombrar un rol al describir («`planner` estima», «`lite` despacha cada tarea, sin paralelismo, al `implementer`») no cuenta. Conservan la cabecera y el mapa completo de roles: `dev-cycle`, `pm-cycle`, `retro`, `knowledge-category-check`. Los 11 restantes llevan solo «Adaptación a …» + cómo se invocan las skills.
  - Medido: 11 de 15 comandos por runtime pierden 696 (Codex, `references/command.md`) y 658 (OpenCode) caracteres: **−7.656** y **−7.238**. Los agentes exportados no cambian (`export-interop.py` regenera 88 ficheros; solo cambian los 22 de comandos).
  - `pytest -q -n 3 tests/test_export_interop.py tests/test_plugin_root_resolution.py tests/test_native_role_context.py tests/test_native_guardrail_dispatch.py tests/test_native_prefilter_parity.py tests/test_codex_command_transport.py tests/test_dev_cycle_split.py` → `137 passed, 1 skipped` (+1 fallo de T-20 en `test_native_role_context.py[claude]`, corregido en T-20); `evals/check.py` → `0 errores`.
  - Interpretación **k8**: hoy hay 15 comandos (no 16: `confluence-pull` salió en T-03), así que «12 de 16» pasa a 11 de 15; `retro` y `knowledge-category-check` conservan la cabecera porque entregan a `knowledge-curator`.
- **Runtimes**: Solo Codex y OpenCode (es el exportador); Claude sin cambio.
- **Verificación**:
  - `pytest -q tests/test_export_interop.py -k cabecera_orquesta` → `passed` (rojo antes: 16 de 16 la llevan)
  - `python scripts/export-interop.py` y luego `python scripts/export-interop.py --check` → exit 0
  - puertas de runtimes (cabecera) → verde
- **Verificación ejecutada** (2026-11-20): `-k cabecera_orquesta` → `3 passed`; `export-interop.py` → `88 ficheros escritos` y `--check` → `88 ficheros al día`; pytest de runtimes de la cabecera → `pytest -q -n 3 agent-kits/shared/test_skill_index.py tests/test_session_context.py tests/test_hooks_config.py tests/test_native_role_context.py tests/test_export_interop.py tests/test_plugin_root_resolution.py tests/test_native_guardrail_dispatch.py tests/test_native_prefilter_parity.py tests/test_kit_path_injection.py` → `204 passed` (tras el GREEN de T-20); `node --test` de la cabecera → `263 tests: 254 pass, 3 fail, 6 skipped` con la máquina cargada; los 3 rojos, aislados: `claude: session context runs without Bash` exigía la caché del índice (corregido en `e93c90c`, `9 passed` con los de guardia) y los otros dos eran plazos agotados con carga (`copied implementer … (precedence)` 16,5 s sobre 15 s; `tool activity is dispatched …` 129 s): solos, `pass`. Consola: `node --test tests/console-inventory.test.mjs tests/console-live.test.mjs` → `10 pass`; `pytest -q -n 2 tests/test_console_{snapshots,service,state,encoding}.py tests/test_audit_console.py` → `744 passed, 4 failed` con node en paralelo, y los 4 (`--lf`) → `4 passed` solos.

**fix1 (intento 1 de la Fase 3, gaps 2 y 4; 2026-11-23; implementado por Codex gpt-6.2-sol)**
- RED: test_retired_opencode_command_is_reported_and_removed_only_with_matching_marker falló con AssertionError (check devolvió 0) · 2026-11-23
- RED: test_fix1_cabecera_orquesta_reconoce_redacciones_de_despacho y test_cabecera_orquesta_solo_en_los_comandos_que_despachan_un_agente fallaron con AssertionError (despachos omitidos) · 2026-11-23
- RED `31e26a7`; GREEN `f627de3`. `pytest -k 'retired_opencode or cabecera_orquesta'` pasó. La forma simple «Despacha … al rol» ya se reconocía (línea 126 de scripts/export-interop.py en c40fd0f).
- Medido en fix1 (GREEN `f627de3`): 10 de 15 comandos pierden la cabecera tras recuperarla para `spec-drift`. Codex −6.960 caracteres (10 × 696), OpenCode −6.580 (10 × 658). El huérfano queda fuera de los comandos vigentes.
- `export-interop.py`: 88 escritos; `--check`: 88 al día. Única retirada `interop/opencode/commands/confluence-pull.md`. El borrado exige marca original y nombre coincidente.
- Puerta común `pytest -q -n 3`, suites afectadas y runtimes: 509 passed, 2 skipped. Puerta `node --test` (cuatro suites de la cabecera, Linux): 256 passed, 7 skipped, 0 fallos. `lint_plugin.py` y `evals/check.py`, 0 errores.

**Criterios de aceptación**
- [x] La cabecera aparece solo en comandos cuyo cuerpo nombra un agente despachable.
- [x] Los agentes y comandos exportados conservan su conducta (misma lista de roles).
- [x] Medido: 12 de los 16 comandos exportados pierden ≈ 600 caracteres (≈ 7,2 KB).

**fix2 (intento 2 de la Fase 3, gaps 5, 6, 8 y 9; 2026-11-23; Codex gpt-6.2-sol)**
- RED: test_fix2_gap5_distingue_despachos_de_descripciones_y_negaciones falló con AssertionError: negaciones y despachos clasificados al revés · 2026-11-23
- RED: test_fix2_gap6_check_sanea_el_nombre_obsoleto_simulado falló con AssertionError: nombre partido por un salto · 2026-11-23
- RED `41cf29c` · GREEN `04d719b`. `test_fix2_gap5_los_15_comandos_conservan_el_conjunto_despachan`: cinco por runtime. Exportación y `--check`: 88.
- Gap 8: `test_fix3_gap1_t21_conserva_medidas_y_traza_del_intento2`. Restaurada la evidencia de GREEN `e8cceba`; las cifras de `f627de3` constan en fix1.
- Changed bilingüe: `test_fix2_gap9_changelogs_bilingues_en_changed_y_trazados_por_tarea`.

**fix3 (intento 3 de la Fase 3, gaps 1, 2, 4, 5, 7; 2026-11-23; Codex gpt-6.2-sol)**
- RED: test_fix3_gap1_t21_conserva_medidas_y_traza_del_intento2 falló con AssertionError (la traza no cita el test) · 2026-11-23
- RED: test_fix3_gap5_recupera_despachos_sin_avisos_ni_descripciones falló con AssertionError (7 despachos omitidos y 2 falsos positivos) · 2026-11-23
- RED `457e0e8` · GREEN `4369db5`. `test_export_interop.py` → 102 passed. Cinco de 15 comandos por runtime conservan la cabecera. `export-interop.py` y `--check` → 88 ficheros. El test de la evidencia detectó ambas mutaciones sobre copias del ledger.

### T-22 — Reglas de este repo fuera de los agentes genéricos y qa condicional (2.8, 2.13)

- **Descripción**: Reglas propias de este repositorio (`export-interop`, `CONTRACTS.md`) viven dentro de agentes genéricos (≈4,2 KB) y `qa.md:114` (2 KB) solo aplica al QA sin UI. Las primeras pasan a `skills/project-extensions/references/custom-agents-repo.md` (solo se lee dentro de custom-agents; replanificado por el orquestador el 2026-11-23: `plugin-dev` ya no existe tras T-11 y `docs/CONSTITUTION.md` no se toca); lo segundo, a una referencia condicional.
- **Changelog**: Los agentes genéricos dejan de cargar reglas que solo valen para el repositorio del plugin.
- **Estado**: borrador
- **Tiempo humano**: est. 3h · real —
- **Tiempo IA (ejec.)**: est. 0.8h · real —
- **Dependencias**: T-18, T-19, T-11
- **Archivos**: `agents/planner.md`, `agents/implementer.md`, `agents/qa.md`, `agent-kits/qa/references/sin-ui.md` (nuevo), `skills/project-extensions/references/custom-agents-repo.md` (sustituye a `.claude/skills/plugin-dev/SKILL.md` y `docs/CONSTITUTION.md`, replanificado 2026-11-23), `docs/agents/CONTRACTS.md`, `docs/agents/planner.md`, `docs/agents/qa.md`, `interop/**` (regenerado)
- **Runtimes**: Constitución y referencias se leen igual en los tres; el consumidor no recibe reglas de este repo.
- **Verificación**:
  - `grep -n "export-interop\|CONTRACTS.md" agents/*.md` → sin coincidencias salvo un puntero a `custom-agents-repo.md`
  - `context-footprint.py --project . --file agents/qa.md` antes/después → menos bytes (`testing/tokens.md`) → ≈2 KB menos
  - puertas de runtimes (cabecera) → verde

**Criterios de aceptación**
- [ ] `planner` conserva el mecanismo E2/E3 como regla de PROYECTO (`skills/project-extensions/references/custom-agents-repo.md`), no como texto del agente genérico.
- [ ] El QA sin UI carga la referencia solo cuando aplica.
- [ ] Un proyecto consumidor no pierde ninguna puerta.
- [ ] Medido: `planner`, `implementer` y `qa` pierden ≥ 6 KB entre los tres.

### T-40 — El plugin mueve el estado de cada tarea en todo el ciclo y el dashboard lo muestra en vivo (decidido por el usuario el 2026-11-23)

- **Descripción**: Hoy el estado de las tareas solo se mueve si el agente se acuerda. `implementer.md` pasa de `en-progreso` a `completado` sin `en-revision`. `adversarial-review` dice en prosa que con gaps las tareas «vuelven a `en-progreso`», pero ningún script lo hace. `ledger-write.py review` abre la cabecera sin tocar estados. Cuando implementa otro proveedor (Codex u OpenCode, o uno implementa y otro revisa), nada mueve el estado: en esta misma iniciativa T-12..T-21 quedaron `completado` con gaps abiertos. El usuario pide que lo haga el PLUGIN, no el orquestador ni el agente de memoria, y que el dashboard muestre en vivo todo lo que pasa. Las transiciones se escriben dentro de los scripts que el flujo ya obliga a ejecutar en los traspasos, sea cual sea el runtime o el proveedor: inicio de tarea → `en-progreso`; fin de la implementación → `en-revision`; apertura de la revisión → `en-revision`; veredicto con Critical/Important → `en-progreso`; veredicto sin Critical/Important → `completado` (con criterios marcados). Cada transición emite además un evento de actividad (tarea, de→a, runtime, rol, fuente) que la consola muestra en vivo.
- **Changelog**: Las tareas pasan solas por En marcha, En revisión y Completada en cualquier runtime, y el dashboard lo muestra en vivo.
- **Estado**: en-revision
- **Tiempo humano**: est. 6h · real —
- **Tiempo IA (ejec.)**: est. 1.5h · real —
- **Archivos**: `agent-kits/shared/ledger-write.py`, `agent-kits/shared/ledger-write.md`, `agent-kits/shared/test_ledger_write*.py`, `agent-kits/shared/usage-meter.py`, `agent-kits/shared/test_usage_meter*.py`, `agent-kits/shared/task-brief.py`, `agent-kits/shared/test_task_brief.py`, `agent-kits/shared/ledger-lint.py`, `tests/test_ledger_lint.py`, `agent-kits/shared/agent-activity.py`, `agent-kits/shared/agent-activity-store.py`, `agent-kits/shared/test_agent_activity*.py`, `hooks/` (solo el aviso de incoherencia del hook posterior a la edición del ledger), `agents/implementer.md`, `commands/dev-cycle.md`, `agent-kits/dev-cycle/references/phase3-subagents.md`, `skills/adversarial-review/SKILL.md`, `skills/adversarial-review/references/lentes.md`, `skills/quick-implement/SKILL.md`, `skills/jira-sync/` (solo si el mapeo de eventos cambia), `skills/plugin-panel/scripts/*.py` y `skills/plugin-panel/assets/*.js` (actividad y tablero), `tests/test_plugin_panel*.py`, `tests/console-*.test.mjs`, `docs/CONVENTIONS.md` + `docs/en/CONVENTIONS.md` (regla 7), `docs/FLOWS.md` + `docs/en/FLOWS.md`, `docs/agents/ROLES.md`, `docs/agents/CONTRACTS.md`, `docs/observability.md` + `docs/en/observability.md`, `docs/roadmap/2026-11-10-plugin-audit-2/tasks.md` (reconciliación de esta iniciativa con la herramienta), `interop/**` (regenerado), `skills/plugin-panel/references/control-center.md`, `tests/fixtures/dev-cycle-modular-replacements.json`, `tests/test_hook_network_egress.py` Fix1: `docs/agents/implementer.md`, `docs/guides/core-workflows.md`, `docs/en/guides/core-workflows.md`, `docs/PLUGIN-PANEL.md`, `docs/en/PLUGIN-PANEL.md`, `CLAUDE.md`, `agent-kits/shared/README.md` (contratos y guías del ciclo), `hooks/run-hook.mjs`, `tests/test_console_codex.py`, `tests/test_console_opencode.py`, `tests/fixtures/opencode-v2-agent-contract.json` (runtime en lanzadores existentes y verificación). Fix2: `skills/jira-sync/scripts/jira-flow.py` (paridad del parser de la columna Tarea). Fix3: `CHANGELOG.md` y `CHANGELOG.es.md` (notas de usuario).
- **Runtimes**: Las transiciones viven en scripts de `agent-kits/shared/` que llaman igual Claude, Codex y OpenCode; la prosa de las piezas solo deja de pedir el cambio manual. Se prueba con los tres runtimes (`--runtime claude|codex|opencode` en el evento) y con proveedores mezclados (implementa uno, revisa otro).
- **Verificación**:
  - `pytest -q agent-kits/shared/test_ledger_write*.py -k "transicion or verdict"` → `passed` (rojo antes: `review` no mueve estados y `verdict` no existe)
  - `pytest -q agent-kits/shared/test_usage_meter*.py -k estado_tarea` → `passed` (rojo antes: `start`/`close` de `<slug>/T-XX` no tocan el ledger)
  - `pytest -q tests/test_ledger_lint.py -k incoherencia_estado` → `passed` (rojo antes: `completado` con gap pendiente no avisa)
  - prueba de punta a punta con la consola arrancada (`control_center.py --project <tmp>`): transición por script → tablero y actividad la muestran en ≤ 7 s, en los tres runtimes
  - puertas de runtimes y de tokens (cabecera) → verde

**Criterios de aceptación**
- [x] Inicio de tarea (`usage-meter.py start --artefacto <slug>/T-XX`, y `task-brief.py` al despachar) → `en-progreso`, si la tarea estaba en `borrador`/`en-progreso`; nunca degrada una `completado` ni una `cancelado`.
- [x] Fin de la implementación (`usage-meter.py close` de la tarea) → `en-revision`; el implementer ya no marca `completado`.
- [x] `ledger-write.py review --tasks …` pone esas tareas en `en-revision` en la misma escritura atómica que abre la cabecera.
- [x] `ledger-write.py verdict --tasks … --attempt N --result gaps|limpio` (nuevo): `gaps` → las tareas con gap Critical/Important vuelven a `en-progreso`; `limpio` → `completado` solo si todos sus criterios están marcados (si no, exit 1 y no escribe). Lo invoca `adversarial-review` al escribir la traza.
- [x] Los estados de fase y la tabla «Resumen de progreso» se recalculan en cada transición.
- [x] Funciona igual con Claude, Codex y OpenCode y con proveedores distintos para implementar y revisar (tests parametrizados por runtime).
- [x] Cada transición emite un evento de actividad (tarea, estado anterior → nuevo, runtime, rol, fuente) sin datos personales; la consola muestra el cambio en el tablero y en Actividad en ≤ 7 s (prueba de punta a punta).
- [x] `ledger-lint` (y el hook posterior a la edición del ledger, que solo informa) avisa de incoherencias: `completado` con gap pendiente en su última revisión; revisión abierta sin veredicto con tareas en `en-progreso`; `en-progreso` con el marcador de medición ya cerrado.
- [x] Degrada sin bloquear: sin Python, ledger ilegible o lock ocupado → aviso y el ciclo sigue (la transición se reintenta en el siguiente traspaso).
- [x] Esta iniciativa se reconcilia con la propia herramienta (no a mano): T-12..T-21 quedan en el estado que les toca según su revisión.


RED: `test_transicion_review_opens_header_with_states_and_phase` falló con 0 tareas en revisión; la fase no transiciona · 2026-11-24.


RED: `test_verdict_clean_is_all_or_nothing_and_updates_summary` falló con verdict era una operación desconocida (exit 2) · 2026-11-24.


RED: `test_transicion_brief_only_writes_on_explicit_dispatch` falló con flag --dispatch no reconocido · 2026-11-24.


RED: `test_estado_tarea_handoffs_and_events` falló con flag --runtime no reconocido para los tres runtimes · 2026-11-24.


RED: `test_estado_tarea_busy_writer_is_nonblocking_and_next_handoff_recovers` falló con KeyError avisos con el writer ocupado · 2026-11-24.


RED: `test_incoherencia_estado_gap_and_open_review` falló con cero avisos ante incoherencias de estado · 2026-11-24.


RED: `test_task_transition_on_board_and_activity_within_seven_seconds` falló con meter rechazó --runtime antes de publicar tablero y actividad · 2026-11-24.


RED: `test_transicion_reconcile_uses_latest_review_without_inventing_one` falló con reconcile era una operación desconocida · 2026-11-24.

- **Verificación ejecutada** (2026-11-24): RED `df734b0` (16 failed, 2 passed). Pruebas Python de traspasos y regresión: 385 passed, 3 skipped. Puertas Python de runtimes, consola, fuentes y contexto: 346 passed, 3 skipped. Historial y consola: 344 passed, 2 skipped. Contratos y diagramas: 33 passed. Dos mutantes detectados en copia con cmp. Puerta Node de runtimes y consola (6 ficheros): 267 passed, 6 skipped, 0 failed. Tres traspasos con runtime constante y tres mezclados validados. Consola CLI aislada y tablero real en Edge, tiempos tablero/Actividad: Claude 2,556/2,928 s, Codex 2,722/3,137 s, OpenCode 2,281/2,582 s. Hook de edición: aviso visible, exit 0. Interop 88 al día; linter y evals 0 errores; dieta 0 pérdidas en ambas skills; vía rápida ahorra 6.167 tokens y evaluator 15.465 bytes LF.
- **Interpretaciones**: k1: `--dispatch` explicita que se va a despachar; la consulta sigue siendo de lectura. k2: los eventos del ledger tienen su propio historial local acotado y conservan el opt-in de los hooks. Si falla publicar actividad, queda un aviso tras el cambio canónico. k3: `reconcile` reconoce revisiones históricas y conserva el estado de tareas sin veredicto. Se entrega T-40 en revisión.
- **Fuera de Archivos inicial**: referencia de la consola (contrato de actividad); fixture de párrafos (reemplazos trazados); prueba de egreso (huella de fuente actualizada, escáner intacto).

**Fix1** · RED a30631e, 14 rojos Python y 1 Node.
RED: `test_fix1_gap1_implementer_docs_describe_plugin_owned_states` falló con faltaba en-progreso · 2026-11-24
RED: `T-40 fix1 gap 2: Activity renders a transition and keeps its row on an unchanged poll` falló con se reemplazó la fila · 2026-11-24
RED: `test_fix1_gap3_parallel_close_and_start_preserve_both_markers` falló con se perdió el marcador ajeno · 2026-11-24
RED: `test_fix1_gap4_reconcile_requires_later_verification_covering_task` falló con completado prematuro · 2026-11-24
RED: `test_fix1_gap5_start_and_dispatch_preserve_open_review` falló con reapertura indebida · 2026-11-24
RED: `test_fix1_gap6_review_rejects_summary_with_undeclared_task` falló con exit 0 · 2026-11-24
RED: `test_fix1_gap7_reconcile_writes_closing_date` falló con sin Cerrada · 2026-11-24
RED: `test_fix1_gap8_task_cell_context_does_not_participate_in_review` falló con T-03 se atribuyó · 2026-11-24
RED: `test_fix1_gap9_phase_state_uses_all_nonterminal_tasks` falló con fase en-revision · 2026-11-24
RED: `test_fix1_gap10_writer_validates_each_input_snapshot_once` falló con 4 lints · 2026-11-24
RED: `test_fix1_gap11_shared_readme_documents_runtime_handoffs` falló con faltaban operaciones · 2026-11-24

218.877 B, mediana: start 2,420 → 1,952 s; close 2,362 → 1,788 s.
`reconcile --dry-run --tasks T-23`
`{"changed":false,"dry_run":true,"input_sha256":"4a6f77ba6320df8812f5f5c6112987324caf91d34d213598558938d67090fecd","operation":"reconcile","output_sha256":"4a6f77ba6320df8812f5f5c6112987324caf91d34d213598558938d67090fecd","schema_version":1,"states":{"T-23":"en-progreso"},"status":"ok","warnings":["T-02: en-progreso con medición cerrada","T-23: en-progreso con medición cerrada","ledger de 222748 bytes (aviso a 60000 bytes por tokens; tope de lectura 262144 bytes): archiva la historia cerrada con `python3 agent-kits/shared/ledger-archive.py docs\\roadmap\\2026-11-10-plugin-audit-2 --apply`"]}`

**Fix2** · RED `e43426c`, `9d19226` · No medido: las 0.01h anotadas carecían de contadores de Codex.
RED: `test_fix2_gap1_ledger_records_verification` falló con bloque ausente · 2026-11-24
RED: `test_fix2_gap2_critical_cell_blocks_clean_verdict_brief_and_jira` falló con veredicto ok u omisión del gap · 2026-11-24
RED: `test_fix2_gap3_noop_handoff_only_reads_once` falló con parse completo; la escritura hizo 2 lints · 2026-11-24
RED: `test_fix2_gap3_meter_handoff_avoids_second_interpreter` falló con otro intérprete · 2026-11-24
RED: `test_fix2_gap4_phase_state_respects_cancellation` falló con completado/en-progreso · 2026-11-24
RED: `T-40 fix2 gap 5` falló con panel duplicado, posición y orden/ventana (3/3 mutantes; copia y cmp) · 2026-11-24
RED: `test_fix2_gap6_ledger_discloses_concurrent_doc_assertion` falló con nota ausente · 2026-11-24
RED: `test_fix2_gap7_start_reports_unsaved_marker_when_state_locked` falló con marker_saved ausente · 2026-11-24

TDD n/a: aserción de texto añadida con su doc (PLUGIN-PANEL, fix1).

Verificación fix1+fix2. pytest afectados 570 passed+2 omit.; consola Py 141+2 omit. (E2E 3/3 max. 0.681 s); node --test tests/console-live.test.mjs 8 passed, inventory 4; runtimes Py 151, Node 257+6 omit.; export-interop --check 88 al día; lint_plugin.py 0 errores/16 avisos; evals/check.py 228/0; tokens Py 96+1 omit., ahorro 6157, evaluator 15465 B LF, diet 0+0.

Medianas en s (226087 B, n=9, c34e9e0/5e397d0/af8dde3). Start cambio 0.191/0.833/0.557, sin cambio 0.203/0.587/0.337. Close cambio 0.188/0.777/0.577, sin cambio 0.202/0.561/0.359.

`reconcile --dry-run --tasks T-12..T-23,T-40` (antes de close):
`{"changed": false, "dry_run": true, "input_sha256": "2709569f8b2c9365766788fcea1bb5368698bf3d55f790d4e82eb57877a85180", "operation": "reconcile", "output_sha256": "2709569f8b2c9365766788fcea1bb5368698bf3d55f790d4e82eb57877a85180", "schema_version": 1, "states": {"T-12": "completado", "T-13": "completado", "T-14": "completado", "T-15": "borrador", "T-16": "borrador", "T-17": "borrador", "T-18": "borrador", "T-19": "borrador", "T-20": "completado", "T-21": "completado", "T-22": "borrador", "T-23": "en-progreso", "T-40": "en-progreso"}, "status": "ok", "warnings": ["T-02: en-progreso con medición cerrada", "T-23: en-progreso con medición cerrada", "ledger de 226087 bytes (aviso a 60000 bytes por tokens; tope de lectura 262144 bytes): archiva la historia cerrada con `python3 agent-kits/shared/ledger-archive.py docs/roadmap/2026-11-10-plugin-audit-2 --apply`"]}`

**Fix3** · RED `e3476b2` · GREEN `0fc4c21`, `a19989f`.

RED: `test_fix3_gap1_task_cell_whitelist` falló con T-02 omitida en `T-01..T-03` · 2026-11-24.
RED: `T-40 fix3 gap 2` falló con el panel retirado por el mutante · 2026-11-24.
RED: `test_fix3_gap4_codex_measures_window_and_project_without_duplicate_tokens` y `test_fix3_gap4_opencode_measures_completed_messages_for_project_and_window` fallaron con `estimado` · 2026-11-24.
RED: `test_fix3_gap4_missing_native_source_never_reports_measured_zero` falló con fuente o aviso incorrecto · 2026-11-24.

Codex real (`close --runtime codex`): 22483064 tokens (234651 entrada, 66397 salida, 0 creación y 22182016 lectura de caché), 0.57 h IA al ratio 531798. 123 respuestas, 1 sesión, cobertura completa. T-40 en-revision por el medidor. OpenCode v2 verificado en SQLite local y con fixtures.

`views3.py`: 69 ledgers, 595 tareas, 0 cambios de bloqueo. 0 vistas de gaps pendientes cambian, 18 cambios de cobertura histórica por la regla. `forms.py`: un rango real (`panel-redesign:1955`). `l3/scripts/failopen.py` ausente: 31 celdas probadas (23 no reconocidas) y 7 casos de integración. Mutante Node 1/1 (`cmp` 0→1→0).

Medianas s (n=9, 231682 B, c34e9e0/ebd9ad6/a19989f). Start cambio 0.203/0.538/0.675, sin cambio 0.249/0.356/0.405. Close cambio 0.216/0.613/0.622, sin cambio 0.206/0.403/0.379. Start con cambio frente a fix2: −0.114 s bajo carga y +0.137 s sin suites.

Verificación: pytest afectados 544+3 omit.; runtimes/tokens 247+1 omit.; consola Python 135+2 omit. y Node 13/13; runtimes Node 256 + B02 aislado, 6 omit.; export-interop --check 88; lint_plugin 0 errores/16 avisos; evals 228/0; diet 0+0. B02 pasó aislado en base y HEAD. Dos pruebas auxiliares de cifras seguían rojas en archivos iguales a la base.

## Fase 4 — Simplificación del código

**Estado**: borrador · **Est.**: 34.5h humanas · **Real**: — · 1725 € · 2470k tokens

### T-23 — CI en paralelo y sin ejecuciones duplicadas (4.1)

- **Descripción**: La CI tarda 875 s: pytest en serie (749 s) y suites que son script y test corren dos veces (23 por recuento rápido, 27 según el análisis: se fija el número real). Se añade `pytest -n auto`, se quita el bucle donde pytest ya recoge el fichero y se publica `--durations`. Adelantable al inicio. Tras T-08 la CI pierde ≈11,8 K líneas de test de Kwipu y Graphiti.
- **Changelog**: La CI es unas 2,5 veces más rápida al paralelizar pytest y no repetir suites.
- **Estado**: en-progreso
- **Tiempo humano**: est. 2h · real —
- **Tiempo IA (ejec.)**: est. 0.5h · real 0.55h (medido; ventana compartida con T-02..T-07) + fix5 a fix16 sin horas propias (ventanas imputadas a T-06; la de fix16 y la de fix18 de T-23 se midieron en la misma ventana que las de T-06) + 0.32h en fix19 `(estimado: marcador T-23-fix19, ventana de pared 13:53-14:30 UTC = 0.61h x 0.52)` + 0.56h en fix21 `(estimado: marcador T-23-fix21, ventana de pared 09:03-10:08 UTC = 1.09h x 0.52)` + fix24 en la ventana de T-06-fix24 (la misma, imputada a T-06)
- **Archivos**: `tests/codex-plugin-state.test.mjs` (intento 12, orquestador: la regex del test de `candidates()` acepta CRLF; en un checkout de Windows `run-hook.mjs` llega con CRLF y el test daba rojo) · `docs/roadmap/2026-11-10-plugin-audit-2/testing/perf.md` (lo escribe el orquestador con las medidas de T-07 y T-23; el guardarraíl veta `testing/` al implementer) · `ci.yml.MANUAL-COPY` y `.github/workflows/ci.yml` (idénticos, comprobado con `diff`; el paso `pip install pytest pyyaml` de `:30-31` añade `pytest-xdist`), `tests/test_ci_manual_copy.py`, `tests/test_ci_skill_suites.py`, `tests/test_suites_no_pytest.py` · añadidos por la nota de alcance: `pytest.ini` (solo registra el marcador `serie`), `tests/test_redact_fix3.py`, `tests/test_npm_payload.py` (fix4: timeout de `npm pack` 120 → 600 s), `tests/test_local_state_fix3.py` (fix4: módulo al paso serie, plazo de pared del almacén), `agent-kits/shared/test_redact.py`, `agent-kits/shared/test_plan_review_summary.py`, `tests/test_agent_activity_store.py`, `tests/test_bench_session_end.py`, `tests/opencode-plugin.test.mjs` (fix1: espera a que el hijo escriba el JSON), `tests/test_lint_plugin.py`, `tests/test_ledger_lint.py`, `tests/test_dashboard.py` (fix1: wrappers `test_suite_legada_*` de sus `main()`/`run()`) (marcados `@pytest.mark.serie`: miden tiempo de pared o dependen del orden de lecturas y fallan bajo `-n auto`; corren en un paso aparte sin xdist), `agent-kits/shared/agent-activity-store.py` (fix5), `agent-kits/shared/test_redact.py` (fix5) · fix7 (corrección de fix8, gap 9: faltaban): `agent-kits/shared/test_ledger_view.py` (paso serie), `tests/test_graphiti_security.py` (huella del lanzador) · fix8: `agent-kits/shared/test_journal_io_deadline.py` (nuevo), `agent-kits/shared/journal-io.py` (plazo inyectable solo bajo `PYTEST_CURRENT_TEST`), `agent-kits/shared/test_journal.py`, `tests/test_redact_fix3.py`, `tests/test_native_guard_failclosed.py` (prueba de plazo al paso serie), `tests/test_panel_review_panel_server.py` (2 pruebas al paso serie) · fix9: `tests/test_fix9_plazos_inyectados.py` (nuevo), `agent-kits/shared/test_journal.py` (sin aserciones de pared), `tests/test_panel_review_panel_server.py` (BODY_TIMEOUT inyectado, sin paso serie), `tests/test_redact_fix3.py` (demo ×12 por la decisión de la puerta y sonda al crecimiento real) · fix10: `agent-kits/shared/test_journal.py`, `tests/test_fix9_plazos_inyectados.py` (vigía), `tests/test_redact_fix3.py`, `agent-kits/shared/journal-io.py` y `journal-capture.py` (`settled`: espera el estado transitorio de dos enlaces), `skills/training-data-services/scripts/test_dataset_assembler.py` y `agent-kits/shared/test_knowledge_read_context.py` (rojos de réplica de tiempo de pared) · fix12: `agent-kits/shared/journal-io.py`, `agent-kits/shared/test_journal.py`, `tests/installer.test.mjs` (el test de la CLI colgada mide desde el arranque de la CLI) · fix14 y fix15 (declarados en fix15, gap 14): `install/install.mjs` (`detached: true` en `correr` y el vigilante de señales: cambio de conducta en Linux y macOS), `agent-kits/shared/journal-capture.py`, `agent-kits/shared/journal-io.py`, `agent-kits/shared/journal.py` (presupuesto por proceso y plazo desde el arranque), `agent-kits/shared/test_journal_fix14.py`, `agent-kits/shared/test_journal_fix15.py` (nuevo), `hooks/opencode-plugin.js` y `interop/opencode/plugins/custom-agents/index.js` (regenerado: opt-in de la actividad), `tests/opencode-plugin.test.mjs`, `tests/helpers/opencode-context.mjs`, `tests/installer.test.mjs` · fix16: `tests/codex-query-deadline.test.mjs` (RED 2: el plazo corre desde que el worker está listo), `tests/hook-budget.test.mjs`, `tests/opencode-plugin.test.mjs` (fixture de 120 s con sondeo), `tests/installer.test.mjs` (3 tests de registro previo), `agent-kits/shared/codex-plugin-state.mjs` (`terminateProcessTree` en paralelo, plazo desde que el worker está listo), `agent-kits/shared/journal-io.py` (mínimo en la primera espera real), `hooks/run-hook.mjs` (8 s de captura de OpenCode; la confirmación de la limpieza toma hasta 10 s dentro de la ventana de 20 s del catálogo del adaptador), `install/install.mjs` (registro previo, limpieza de restos; ya no existe `TIMEOUT_CAZA`: la caza de restos usa el barrido con identidad; fix18: las sondas `--version` no arrancan un worker), `tests/process-tree-fix17.test.mjs` (fix17: nuevo; el árbol con identidad, `queryPlan` y `runBounded`), `tests/artifact-dom-security.test.mjs` (fix17, gap 22: el navegador headless se relanza si sale con código ≠ 0), `docs/{,en/}FLOWS.md`, `docs/{,en/}INTEROP.md` y `docs/{,en/}observability.md` (fix17, gap 13: plazos reales), `tests/hook-docs-marker.test.mjs`, `tests/hook-guard-delivery.test.mjs`, `tests/test_console_transport.py` y `tests/test_mermaid_blocks.py` (fix17, gap 22: rojos de la suite completa atribuidos, ver j17) · `tests/test_statusline_cache.py` y `tests/test_agent_activity_store.py` (suite completa tras fix17, orquestador: dos tests que medían la máquina, ver «Suite completa tras fix17») · fix18: `agent-kits/shared/agent-activity-store.py`, `agent-kits/shared/local-state.py`, `agent-kits/shared/codex-plugin-state.mjs`, `install/install.mjs`, `statusline/roadmap-statusline.sh`, `tests/test_agent_activity_store.py`, `tests/test_agent_activity_tail.py`, `tests/process-tree-fix18.test.mjs`, `tests/test_statusline_scan_fix18.py`, `tests/installer.test.mjs`, `docs/FLOWS.md`, `docs/en/FLOWS.md` · fix18b: `agent-kits/shared/test_doctor.py`, `agent-kits/shared/test_plan_review_summary.py`, `agent-kits/shared/test_guardrail_fix14.py`, `tests/session-end-budget.test.mjs` · fix18c: `skills/training-data-services/scripts/test_case_recorder.py`, `skills/training-data-services/scripts/test_dataset_assembler.py` · fix18d: `skills/knowledge-services/scripts/test_backend_graphiti.py`, `skills/knowledge-services/scripts/test_backend_markdown_read.py` · fix19: `install/mkdir-p.mjs` (nuevo), `install/install.mjs`, `install/manifest-auth.mjs`, `tests/mkdir-p-fix19.test.mjs` (nuevo), `tests/codex-staging-fix19.test.mjs` (nuevo), `tests/installer.test.mjs` (fixture del bundle copia `mkdir-p.mjs`; `cli()` crea su TEMP con `mkdirP`) · fix24 (intento 19): `agent-kits/shared/agent-activity-store.py`, `agent-kits/shared/local-state.py`, `agent-kits/shared/codex-plugin-state.mjs`, `install/install.mjs`, `tests/test_agent_activity_fix24.py`, `tests/process-tree-fix24.test.mjs`, `tests/install-promover-fix24.test.mjs`, `tests/session-end-budget.test.mjs`, `tests/test_hook_network_egress.py` (huella revisada), `docs/INTEROP.md`, `docs/en/INTEROP.md`
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

**fix18 a fix24 de T-23** (con fix18b, fix18c, fix18d y los rojos de suite de fix20 a fix23) — archivados LITERALMENTE (bytes sin cambios) en [execution-history.md](execution-history.md), sección «Archivado 2026-11-20 — T-23 fix18 a fix24» · SHA-256 `530a3319417d34a96ad58909359230ac9b9db8b67ea7eabe7093378ff36574fc`. Se movieron el 2026-11-20 por el tope de lectura de 256 KiB, antes de la Fase 3. T-23 sigue `en-progreso`: falta la medida emparejada con la máquina libre (orquestador).

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
- 2026-11-20 · «Revisión de dos lentes — intento 20: Fase 1 (T-06) — 3 Important, 4 Minor (corrección: fix25)» → [execution-history.md](execution-history.md) · SHA-256 `b827b7b60885d785d4df8451b84863399b01ac62cfcd76194e86912c4620851e`
- 2026-11-20 · «Revisión de dos lentes — intento 1: Fase 2 (T-08, T-09, T-10, T-11) — 4 Important, 11 Minor (corrección: fix1)» → [execution-history.md](execution-history.md) · SHA-256 `538292f9392d32ce98fe9b5a4a9311ac1847847d98bc50ac510f53639c177026`
- 2026-11-24 · «Revisión de dos lentes — intento 3: Fase 3 (T-14, T-21) — verificación del fix2: 1 Important, 7 Minor (decisión del usuario: ciclo nuevo con fix3)» → [execution-history.md](execution-history.md) · SHA-256 `11982fd6f89ef6c92a355be6179484ed9a463a2b339d6c0523b0753265c6440a`


## Revisión de dos lentes — intento 18: Fase 1 (T-06, T-07, T-23) — verificación dirigida del fix17: 4 Important, 13 Minor

Lentes A+B+C+D sobre `e371259..ae56211`: 4 Important y 13 Minor, corregidos en fix18 (gap 5 = límite conocido; gap 13 rebatido). Cuerpo completo movido literal a [testing/intento18-traza.md](testing/intento18-traza.md) (2026-11-20, tope de lectura del ledger); superado por los intentos 19-21.

## Revisión de dos lentes — intento 19: Fase 1 (T-06, T-23) — 5 Important, 20 Minor (corrección: fix24)

Lentes A+B+C+D sobre `ae56211..73f1ca6` + `c80eabb`. Informes en el scratchpad de la sesión (`lenteA19.md` a `lenteD19.md`, sondas en `lb19/`). Cada gap se verificó contra el código antes de corregirlo; dos rebatidos con evidencia (13 y 24). **Decisión del usuario (2026-11-20, «sí, aplica la lista blanca y cierra así la fase»):** la guarda de git pasa a lista blanca (gaps 4-11 y 24 cerrados por clase) y la Fase 1 se cierra con 0 Critical y 0 Important; los Minor sin corregir quedan como deuda ACEPTADA por el usuario (2026-11-20) sin abrir otro ciclo: solo el residual teórico del gap 15 (pid reutilizado con la raíz aún viva).

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | Línea cortada en `events.tail` + append posterior = línea pegada corrupta; `_read_tail` falla cerrado para siempre | T-23 | corregido en fix24 | RED `4818f4d`; `local-state.py` append + `_read_tail`; test gap1 x2 |
| 2 | Important | Regresión 2.5 e: editar `dev.json` no caduca una ventana cuyo `start` sigue en la cola | T-23 | corregido en fix24 | sello `c` por línea + `_plegar`; test gap2 con umbral real |
| 3 | Important | `history()` devuelve anillo + cola sin recortar a 500; el panel da `invalid_history` | T-23 | corregido en fix24 | `_view`; test gap3 incl. `serve_panel.activity_history` |
| 4 | Important | DWIM de remota: `git checkout main --` con `origin/main` y un directorio `main` | T-06 | corregido en fix24 (por clase: lista blanca) | lista blanca: una ruta solo vale tras `--` (cierra el DWIM por clase); git real |
| 5 | Important | Regla k5 (`-C` hacia worktree en main) no cubre `/c/…`, 8.3, `$PWD`, `"$VAR"`, `~/` | T-06 | corregido en fix24 (por clase: lista blanca) | `_expande_C` + lista blanca (`-C` irresoluble solo con lectura); control negativo 0 deny |
| 6 | Minor | Refspec con origen `@`/`HEAD@{0}` se salta la clase | T-06 | corregido en fix24 (por clase: lista blanca) | `push` solo de la rama actual (lista blanca); `@:main` y gemelos deny |
| 7 | Minor | `gc --prune=<fecha>` distinta de now/all → allow | T-06 | corregido en fix24 (por clase: lista blanca) | `gc` fuera de la lista blanca (deny por clase) |
| 8 | Minor | `checkout -` y `checkout <sha>` con fichero homónimo → allow | T-06 | corregido en fix24 (por clase: lista blanca) | `checkout`: `-`/SHA sin `--` → deny por clase |
| 9 | Minor | `git branch -m|-M` sobre/hacia la rama principal | T-06 | corregido en fix24 (por clase: lista blanca) | `branch -m|-M|-c|-C` fuera de la lista blanca |
| 10 | Minor | `git fast-import --force` resetea refs | T-06 | corregido en fix24 (por clase: lista blanca) | `fast-import` fuera de la lista blanca |
| 11 | Minor | `send-email --to-cmd|--cc-cmd|--header-cmd|--sendmail-cmd` ejecutan shell | T-06 | corregido en fix24 (por clase: lista blanca) | `send-email` fuera de la lista blanca |
| 12 | Minor | Lectores sin cerrojo ven anillo viejo + cola truncada | T-23 | corregido en fix24 | lectura cola→anillo; test con pliegue entre lecturas |
| 13 | Minor | Desfase de versiones entre runtimes (`events.tail`/`plegado`) | T-23 | descartado (rebatido) | ningún tag contiene `887706f` (v3.3.0 no lo escribe); falla cerrado, sin corrupción |
| 14 | Minor | `promoverEntradaCodex` puede borrar la única copia | T-23 | corregido en fix24 | `install.mjs` + `install-promover-fix24.test.mjs` |
| 15 | Minor | Barrido con raíz «viva» y `until=0` tras taskkill fallido | T-23 | corregido en fix24 (raíz ya muerta); residual: deuda aceptada por el usuario (2026-11-20) | `codex-plugin-state.mjs` + `process-tree-fix24.test.mjs`; residual: pid reutilizado durante los 1-4 s del CIM con la raíz aún viva (teórico, acotado por `since`, no reproducido) |
| 16 | Minor | El pliegue entra en la ráfaga y D2 nunca lo ejecuta | T-23 | test añadido en fix24 (el pliegue ya cae dentro de la ráfaga); residual: **deuda aceptada por el usuario (2026-11-20, criterio de cierre de la Fase 1)**: con 4 quemadores la variante da 10/12 (1 evento perdido en 2 tandas; captura informativa, CA-42) | `test_fix24_d2_rafaga_con_la_cola_cerca_del_umbral_el_pliegue_cae_dentro_de_la_rafaga`: 12/12 en reposo, 10/12 con 4 quemadores; plegar tras soltar el cerrojo probado y revertido (10/12, sin beneficio) |
| 17 | Minor | `cpSync` de 62 MB (+10 s) por instalación de ámbito proyecto | T-23 | corregido en fix24 | rename en el mismo volumen; copia de respaldo |
| 18 | Minor | `INTEROP.md` ES/EN describen el enlace al namespace | T-23 | corregido en fix24 | docs ES y EN |
| 19 | Minor | Ledger: tope de /doctor «9 s − arranque, 1-6 s» vs código 8 s / 1-5 s | T-23 | corregido en fix24 | nota de corrección en T-23 fix24 |
| 20 | Minor | El RED de fix20 solo pasa con la escala x20 | T-06 | corregido en fix24 | docstring + nota en T-06 fix24 |
| 21 | Minor | fix18b-4 borró la puerta de mediana de `session-end-budget` | T-23 | corregido en fix24 | restaurada en POSIX; Windows informa |
| 22 | Minor | Horas de T-06/T-23 sin fix18d, fix19, fix20, fix21, fix22 | T-06/T-23 | corregido en fix24 | sumadas (medido fix20; estimado el resto, con derivación) |
| 23 | Minor | El GREEN de fix20 está en `ae5af3a`, no en `e435cf3` | T-06 | corregido en fix24 | nota (sin reescribir historia) |
| 24 | Minor | `git bisect reset` se deniega y antes el mensaje lo recomendaba | T-06 | descartado (rebatido) | corpus fix18:39 lo exige; ningún mensaje lo recomienda; test_gap24 |
| 25 | Minor | Hijos de D2 del store heredan la escala (26 s, no el real) | T-23 | corregido en fix24 | hijos con `env` sin escala ni marca; cifras en T-23 fix24 |

## Revisión de dos lentes — intento 21: Fase 1 (T-06) — verificación final de fix25: 0 Critical, 0 Important, 2 Minor (deuda aceptada); Fase 1 cerrada

Lente C dirigida sobre `8bc0009..36eb2f3` (fix25), con el criterio de cierre del usuario (2026-11-20: 0 Critical y 0 Important cierran la fase; los Minor pasan a deuda aceptada). Unas 120 órdenes probadas una a una contra `check_git` de `36eb2f3` en un repo temporal (rama `feature/x`, worktree en `main`, remoto bare), y con git 2.53 real las que pasaban el guard. Denegadas, entre otras: `--update-refs`, `--upd`, `--end-of-options`, `--into-name`, `-sours`, `-fu`, `GIT_DIR`/`GIT_WORK_TREE`/`GIT_SEQUENCE_EDITOR`, `-c sequence.editor|core.hooksPath|alias`, `push --mirror|--all|--prune|--delete|+HEAD|:main|HEAD:main|--force-with-lease`, `remote add|set-url`, `notes --ref=refs/heads/main`, `reflog delete|expire`, `submodule foreach 'git branch -f main'`, `clean -fdx`, `stash drop|clear|branch`, `branch -d main`, `switch -C`, `checkout -B`, `worktree add` sin `-b`, `rebase -x 'git branch -f main'`. Pasan el guard pero git real las rechaza sin mover nada: `fetch|pull -j --refmap=…`, `rebase -- --update-refs`, `cherry-pick --empty --update-refs`.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Minor | `HEAD:"$(git branch --show-current)"` (gap 6 del intento 20) supone que la sustitución corre en el mismo directorio que el push: `cd ../m && git -C ../r push origin HEAD:"$(git branch --show-current)"` (m = worktree en main) → allow e integra feature/x en el main remoto (CWE-863) | T-06 | deuda aceptada por el usuario (2026-11-20, criterio de cierre): cae en el límite ya declarado de `cd` hacia el worktree de la principal (k5, T-06), con el que ya se podía `cd ../m && git merge feature/x && git push origin HEAD` antes de fix25 | guardrail-check.py:2817-2819, :2945-2946; reproducido con git real |
| 2 | Minor | `-C` hacia la principal «solo lee» se apoya en `_SUB_LECTURA`, que incluye `log`/`show`/`diff --output=<fichero>`: `git log -1 --format=%H feature/x --output=.git/refs/heads/main` → allow y main se mueve (CWE-73); misma familia: `grep --open-files-in-pager=sh`, `PAGER=sh git -p log`, `help -w` | T-06 | deuda aceptada por el usuario (2026-11-20, criterio de cierre): mismo poder que el límite aceptado `echo … > .git/refs/heads/main` (la shell escribe ahí sin git) y que el de envoltorios encadenados | guardrail-check.py:2715-2717, :2629; reproducido con git real |

**Fase 1 cerrada (2026-11-20)** según el criterio del usuario: 0 Critical y 0 Important tras los intentos 19 (fix24), 20 (fix25) y 21; la deuda aceptada son los residuales de los gaps 15 y 16 del intento 19 y los gaps 1 y 2 de este intento.

## Revisión de dos lentes — intento 2: Fase 2 (T-08, T-09, T-10, T-11) — 2 Important, 5 Minor (corrección: fix2)

Lentes B+C dirigidas sobre `36eb2f3..e0e7afb`. Cada gap verificado; ninguno rebatido. RED `2ad7a6e` · GREEN `de7efe1`. Verificación: `skills/knowledge-services/scripts` 76 passed; panel+doctor+capabilities+notas 361 passed/2 skipped (+ `test_f4fix2_misc` tras fijar la cifra 11.719 de `doctor-reference.md` en TOKEN-EFFICIENCY ES/EN: 9 passed); `tests/test_sync_write_gate.py` 13 passed; `test_project_pieces`+`test_project_extensions_skill`+`test_skill_size`+`test_export_skills` 223 passed/1 skipped; `test_console_encoding -k project-` 11 passed; lint 0 errores; evals 0 errores; export-interop `--check` 88 al día; `ledger-lint` 0 incoherencias.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | Temporales del adaptador siguen enlaces (CWE-59/73) | T-10 | `mkstemp` + rechazo de destinos enlazados | tests de enlace; 76 passed |
| 2 | Important | `description` multilínea sin sangrar: verde falso | T-11 | skill + aviso en `project-pieces.py` | 2 tests + 223 passed |
| 3 | Minor | CA-05: `--backend=x` y cadenas | T-08 | normaliza y trocea la cadena | 2 mutantes muertos |
| 4 | Minor | `type` crudo en `/doctor` | T-09 | `_sanear_detalle` | RED/GREEN |
| 5 | Minor | Alcance de `/doctor` mal documentado | T-08 | doc ES/EN + fila | test de fila |
| 6 | Minor | `_tipos_retirados` degrada sin aviso | T-08 | formas literales + aviso | 9 tests |
| 7 | Minor | Adaptador rechaza `\\?\` y clave hostil bloquea | T-10 | normaliza y ignora con aviso | 2 tests |

## Revisión de dos lentes — intento 3: Fase 2 (T-08, T-10, T-11) — verificación final del fix2: 0 Critical, 0 Important, 1 Minor (deuda aceptada); Fase 2 cerrada

Lente C (+B sobre los dos Important) dirigida sobre `df2c60e..bef4844`, con el criterio de cierre del usuario (2026-11-20). Important 1 (temporales del adaptador): cerrado; sondas en Windows con hardlinks y junctions (destino, `manifest.json`, `manifest.pending.json`, `dir` y subdirectorio enlazados, `revoke`/`rebuild`): ninguna escritura ni borrado fuera de `dir`; symlink real no verificable en esta máquina (WinError 1314), cubierto por `realpath`/`islink` en lectura. Important 2 (descripción multilínea): cerrado; las 5 plantillas YAML con `:`, `#`, comillas, tabulador, línea vacía, `>-` irregular, CRLF y BOM salen completas y sin aviso; la continuación sin sangrar da `partial` con 5 avisos; 0 falsos positivos sobre 59 piezas reales del repo y 40 proyectos generados. 16 tests dirigidos verdes.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Minor | El aviso de línea sin clave no salta si la continuación sin sangrar empieza por `Palabra:` o `- ` (`_FRONTMATTER_LINE` la toma por clave o lista): verde truncado | T-11 | deuda aceptada por el usuario (2026-11-20, criterio de cierre): brecha residual del detector; la defensa principal es la regla de una sola línea de la skill | agent-kits/shared/project-pieces.py:190, :235 |

**Fase 2 cerrada (2026-11-20)** según el criterio del usuario: 0 Critical y 0 Important tras los intentos 1 (fix1), 2 (fix2) y 3; deuda aceptada: el gap 1 de este intento. Pendiente del usuario: M-B (T-11).

## Revisión de dos lentes — intento 1: Fase 3 (T-12, T-13, T-14, T-20, T-21) — tanda A: 5 Important, 5 Minor (corrección: fix1)

Lentes A+B+C+D (Claude Opus 5.5, esfuerzo alto) sobre `ab7eeb2..4893637`; C por `hooks/session-context.*` y el flujo de `phase3-subagents.md:20`, D por `scripts/export-interop.py` (D: sin hallazgos). Criterios de A: todos ✓ salvo T-14 «la Lente A recibe la fase» (✗ parcial) y T-21 en lo instalado. T-15..T-19 y T-22 siguen en borrador (tanda B).

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | El prompt literal de la Lente A sigue mandando revisar «contra `improvement-plan.md` y `tasks.md`» y `reviewer.md` lista `tasks.md`: el revisor abre el ledger entero y el ahorro no se da | T-14 | corregido (fix1, f627de3) | `skills/adversarial-review/references/lens-prompts.md:17`; `agents/reviewer.md:72` |
| 2 | Important | Huérfano `interop/opencode/commands/confluence-pull.md` (fuente retirada en T-03) con cabecera «ORQUESTA» y mapa de roles; `export-interop.py --check` no detecta generados sin fuente y el instalador copia la carpeta entera | T-21 (origen T-03) | corregido (fix1, f627de3) | `interop/opencode/commands/confluence-pull.md:8-9`; `install/providers.mjs:531` |
| 3 | Important | `tests/test_hooks_shell.py` sigue exigiendo `Comandos:`/`Agentes:`/caché del índice a `session-context.sh` en runtime `claude` (por defecto): se salta en Windows y falla en la CI de Linux | T-20 | corregido (fix1, 31e26a7) | `hooks/session-context.sh:195-196` frente a `tests/test_hooks_shell.py:270,274,278,296,930,944,1058`; reproducido |
| 4 | Important | `despacha_agentes` solo ve un rol entre acentos graves: `/spec-drift` («subagente de contexto fresco», lotes de 3) pierde la traducción a `spawn_agent`/`subagent`; tampoco ve «los agentes `x`», «Llama al `planner`», «Pasa … a `implementer`», «Despacha … al `reviewer`», «Handoff a `qa`» | T-21 | corregido (fix1, f627de3) | `scripts/export-interop.py:121-127`; `commands/spec-drift.md:19` → `False` |
| 5 | Important | `--fase` corta la sección en cualquier `## ` aunque esté dentro de un bloque cercado (y toma un `## Fase N` citado como inicio): tareas y criterios omitidos con exit 0 | T-14 | corregido (fix1, f627de3) | `agent-kits/shared/task-brief.py:1566-1567,1580-1581`; reproducido (64 KB y 70 KB CRLF) |
| 6 | Minor | La vista de fase entra en el prompt de la Lente A sin delimitadores ni `_neutraliza_encabezados` (CWE-1427) | T-14 | corregido (fix1, f627de3) | `task-brief.py:1578-1586` |
| 7 | Minor | Aviso con unidades mezcladas (`//1024` frente a `//1000`: «58 KB (aviso a 60 KB)»); umbral en texto CRLF→LF frente a `getsize`; `--fase` ignora `--umbral-bytes`; `--umbral-bytes` ≤ 0 sin validar | T-14 | corregido (fix1, f627de3) | `ledger-lint.py:912-919`; `task-brief.py:1572-1575` |
| 8 | Minor | k11: T-20 cerrada sin los evals reales de activación (`evals/run.py`) ni acción del usuario | T-20 | corregido por el orquestador (`4e3d58a`): M-C del plan los incluye | `tasks.md` (T-20, k11) |
| 9 | Minor | `FLOWS.md` (ES/EN) sigue diciendo índice completo en todos los runtimes; `--fase` falta en `agent-kits/shared/README.md` y en E8 de `CONTRACTS.md` | T-20, T-14 | corregido (fix1, f627de3) | `docs/FLOWS.md:547`; `agent-kits/shared/README.md:59`; `docs/agents/CONTRACTS.md:79` |
| 10 | Minor | `skill-index.py --solo-cabecera --json` imprime texto plano | T-20 | corregido (fix1, f627de3) | `agent-kits/shared/skill-index.py:443-445` |

## Revisión de dos lentes — intento 2: Fase 3 (T-13, T-14, T-20, T-21) — verificación del fix1: 2 Important, 8 Minor (corrección: fix2)

Lentes A+B+C (Claude Opus 5.5, esfuerzo alto) sobre `c40fd0f..e072004` (fix1 de Codex gpt-6.2-sol). D no se relanza: la Lente B midió `despacha_agentes` ampliada (lineal, 700 KB → 3,1 s). Del intento 1 quedan ✓ los gaps 2, 3, 4, 5 (escenario original), 6, 7 y 10; los gaps 1 y 9 están corregidos en contenido, pero sin test (gap 2 de abajo). Confirmado: el borrado de generados sin fuente de `export-interop.py` no sigue junctions, enlaces ni hardlinks, y el instalador no borra nada.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | `_lineas_con_fence` abre y cierra el cercado con cualquier ```/~~~ sin mirar carácter ni longitud (CommonMark), mientras `ledger-lint` sí lo hace (`sin_vallas`). Un cercado de 4 acentos con otro dentro sigue ocultando tareas y criterios con exit 0; `~~~` con ```` ```python ```` dentro deja el cercado abierto hasta el final; un cercado sin cerrar antes de `## Fase N` da exit 1 | T-14 | corregido (fix2, 04d719b; test `test_fix2_gap1_cercados_y_reparto_por_fase_como_ledger_lint`) | `agent-kits/shared/task-brief.py:267-278` (usa `:1573-1575`); reproducido (`scratchpad/probe_fase.py`) |
| 2 | Important | Los gaps 1 y 9 del intento 1 constan `corregido` sin un test dedicado que los nombre: si el prompt de la Lente A vuelve a pedir `tasks.md`, nada falla | T-13, T-14, T-20 | corregido (fix2, 04d719b; test `test_intento1_gap1_lente_a_y_reviewer_piden_la_vista_de_fase`, `test_intento1_gap9_flujos_documentan_el_indice_por_runtime`, `test_intento1_gap9_contratos_documentan_la_vista_de_fase`) | `docs/CONSTITUTION.md:13`; `skills/adversarial-review/references/lens-prompts.md:17`; `agents/reviewer.md:72-75` |
| 3 | Minor | Las marcas INICIO/FIN de la vista de fase se pueden falsificar desde el ledger (sin prefijo `> ` ni escape del literal de cierre); también cuando la vista es el ledger entero (CWE-1427) | T-14 | corregido (fix2, 04d719b; test `test_fix2_gap3_marcas_del_ledger_quedan_dentro_de_la_cita`) | `task-brief.py:1596-1598`, `:352`; reproducido (`scratchpad/lc2`) |
| 4 | Minor | `_neutraliza_encabezados` escapa también dentro de bloques de código (`# comentario` → `\# comentario`) | T-14 | corregido (fix2, 04d719b; test `test_fix2_gap4_neutraliza_encabezados_solo_fuera_de_cercados`) | `task-brief.py:352-360` |
| 5 | Minor | `despacha_agentes`: falsos positivos con negaciones y descripciones («no usa subagentes», «Sin subagentes en paralelo», «el formato de los agentes `planner` y `qa`», un bloque con `subagent_type:`, «pasa a la fase … `qa`»); falsos negativos con preguntas y gerundios («¿Despacho al `reviewer`?», «delegando al `planner`») | T-21 | corregido (fix2, 04d719b; test `test_fix2_gap5_distingue_despachos_de_descripciones_y_negaciones`) | `scripts/export-interop.py:125-131`, `:341-362`; `scratchpad/probe_desp.py` |
| 6 | Minor | `--check` imprime sin sanear el nombre de un generado obsoleto (`OBSOLETO %s`; CWE-150/117) | T-21 | corregido (fix2, 04d719b; test `test_fix2_gap6_check_sanea_el_nombre_obsoleto_simulado`) | `scripts/export-interop.py:836` → `:959` |
| 7 | Minor | El «modo sin plan» de la Lente A manda sustituir un texto que el fix1 eliminó | T-14 | corregido (fix2, 04d719b; test `test_fix2_gap7_modo_sin_plan_sustituye_el_texto_vigente_de_lente_a`) | `lens-prompts.md:18` |
| 8 | Minor | La evidencia original de T-21 (11 de 15, −7.656/−7.238, GREEN `e8cceba`) se reescribió en su sitio en vez de añadirse al bloque fix1 | T-21 | corregido (fix2, 04d719b; test `test_fix3_gap1_t21_conserva_medidas_y_traza_del_intento2`) | `tasks.md` (T-21, Evidencia) |
| 9 | Minor | Entradas de CHANGELOG como «Fixed» de funciones nunca publicadas, declaradas solo en T-21; `changelog-sync` saltará la iniciativa al cerrarla porque `plugin-audit-2` ya aparece en `[Unreleased]` | T-14, T-21 | corregido (fix2, 04d719b; test `test_fix2_gap9_changelogs_bilingues_en_changed_y_trazados_por_tarea`) | `CHANGELOG.md:14-17`, `CHANGELOG.es.md:14-17`; `skills/changelog-sync/SKILL.md:103` |
| 10 | Minor | La vista `--fase` excluye las secciones `## Revisión … intento N` de esa fase y no lleva números de línea: la Lente A abre el ledger para ver la tabla anterior o citar | T-14 | corregido (fix2, 04d719b; test `test_fix2_gap10_vista_incluye_intentos_en_orden_con_rangos_y_ahorra_50_por_ciento`) | `task-brief.py:1558-1598` |

## Revisión de dos lentes — intento 4: Fase 3 (T-14, T-21) — verificación del fix3: 0 Critical, 0 Important, 3 Minor (deuda aceptada); tanda A cerrada

Ciclo nuevo autorizado por el usuario el 2026-11-23 («fix3 corto y cierro»). Lentes A y B+C (Claude Opus 5.5, esfuerzo alto) sobre `ea18413..cd5c270` (fix3 de Codex gpt-6.2-sol). Gaps 1, 2, 4, 5 y 7 del intento 3 ✓, cada uno con su test dedicado (`docs/CONSTITUTION.md:13`); RED `457e0e8` (27 failed) antes del GREEN `4369db5`; 595 tareas reales sin diferencias no buscadas; `export-interop --check` 88 al día; `--diet-check` 0 párrafos perdidos.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Minor | `_neutraliza_encabezados` restaura parejas de cercado dentro de una lista que vuelve a la columna 0 o de un bloque HTML (`<!--`, `<pre>`), donde CommonMark no las ve como cercado: un `## Contrato de retorno` sale crudo en la cita (CWE-1427; misma clase del gap 2, se cerraría con lista blanca) | T-14 | deuda aceptada por el usuario (2026-11-23, criterio de cierre) | `agent-kits/shared/task-brief.py:361-371`; `scratchpad/r4/neut5.py` |
| 2 | Minor | La excepción de «verde» de `despacha_agentes` solo acepta `` `X` verde `` literal: «Pasa a `qa` en verde/**verde**/(verde)» → True (latente: no cambia ninguno de los 15 comandos) | T-21 | deuda aceptada por el usuario (2026-11-23, criterio de cierre) | `scripts/export-interop.py:147` |
| 3 | Minor | La excepción `nunca\b(?!\s+bloquea\s*:)` está hecha a medida de la frase del test: «Nunca degrada: despacha al `qa`» → False (latente) | T-21 | deuda aceptada por el usuario (2026-11-23, criterio de cierre) | `scripts/export-interop.py:162-163` |

**Tanda A de la Fase 3 cerrada (2026-11-24)** según el criterio del usuario: 0 Critical y 0 Important tras los intentos 1 (fix1), 2 (fix2), 3 (fix3) y 4. La deuda aceptada son los gaps 3, 6 y 8 del intento 3 y los 3 Minor de este intento. Los estados de T-12, T-13, T-14, T-20 y T-21 los reconcilia la herramienta de T-40.

## Revisión de dos lentes — intento 1: Fase 3 (T-40) — estados de tarea movidos por el plugin y consola en vivo (T-40)

**Veredicto del plugin**: gaps (T-40)
Lentes A y B (Claude Opus 5.5, esfuerzo alto; C y D no se activan por heurística, B cubre seguridad y la ruta caliente) sobre `c34e9e0..0599538` (Codex gpt-6.2-sol). Criterios 1-6, 8-10 ✓; 7 parcial. Seguridad sin hallazgos: evento con seudónimo y listas cerradas, la consola pinta con `textContent`.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | E3: `docs/agents/implementer.md` sigue describiendo que el implementer marca checkbox y estado y cierra `completado`; no está en `Archivos` | T-40 | corregido (fix1, c13853e; test `test_fix1_gap1_implementer_docs_describe_plugin_owned_states`) | `docs/agents/implementer.md:22` frente a `agents/implementer.md:102,108-110` |
| 2 | Important | JS nuevo de la consola (panel de transiciones de Actividad) sin test ni `RED:`; el E2E solo cubre la API | T-40 | corregido (fix1, c13853e; test `T-40 fix1 gap 2: Activity renders a transition and keeps its row on an unchanged poll`) | `skills/plugin-panel/assets/console-context.js:3,167-185,211`; `docs/CONSTITUTION.md:11` |
| 3 | Important | Dos `usage-meter` en paralelo pierden marcadores: `cmd_close` lee el state, lanza el traspaso (0,5-5 s) y guarda el state entero sin fusionar; un `start` de otra tarea en ese hueco desaparece (regresión) | T-40 | corregido (fix1, c13853e; test `test_fix1_gap3_parallel_close_and_start_preserve_both_markers`) | `agent-kits/shared/usage-meter.py:826,906,917`; `scratchpad/lensB-xq7/race.py` 3/3 frente al control 0/3 |
| 4 | Important | `reconcile` cierra `completado` tareas con «corregido en fixN» que ningún intento posterior verificó: en el ledger real T-23 pasaría de `en-progreso` a `completado` (contrato: sin veredicto interpretable se conserva) | T-40 | corregido (fix1, c13853e; test `test_fix1_gap4_reconcile_requires_later_verification_covering_task`) | `agent-kits/shared/ledger-write.py:224`; `ledger-lint.py:458,470` |
| 5 | Minor | `start`/`--dispatch` sacan de `en-revision` una tarea con revisión abierta (el criterio: solo desde `borrador`/`en-progreso`); el propio lint avisa la incoherencia | T-40 | corregido (fix1, c13853e; test `test_fix1_gap5_start_and_dispatch_preserve_open_review`) | `ledger-write.py:240-243` |
| 6 | Minor | `verdict` exige ids(cabecera) == `--tasks`: un `--summary` de `review` que cite otra tarea deja la revisión sin cierre posible | T-40 | corregido (fix1, c13853e; test `test_fix1_gap6_review_rejects_summary_with_undeclared_task`) | `ledger-write.py:175-177` |
| 7 | Minor | `reconcile` cierra sin `- **Cerrada**` (el burndown la lee); `verdict limpio` sí la escribe | T-40 | corregido (fix1, c13853e; test `test_fix1_gap7_reconcile_writes_closing_date`) | `ledger-write.py:228` |
| 8 | Minor | Una mención de contexto en la columna Tarea («T-21 (origen T-03)») cuenta como revisión de T-03 | T-40 | corregido (fix1, c13853e; test `test_fix1_gap8_task_cell_context_does_not_participate_in_review`) | `ledger-lint.py:454` |
| 9 | Minor | `phase_state` declara `en-revision` una fase con tareas en `borrador` (Fase 3 con T-15..T-22 sin empezar) | T-40 | corregido (fix1, c13853e; test `test_fix1_gap9_phase_state_uses_all_nonterminal_tasks`) | `ledger-write.py:127-135` |
| 10 | Minor | Coste en la ruta caliente: +1,4 s en `start` y +0,5 s en `close` con 215 KB (lint 4 veces por escritura, relee `usage-state.json`, un intérprete más) | T-40 | corregido (fix1, c13853e; test `test_fix1_gap10_writer_validates_each_input_snapshot_once`) | `ledger-write.py`, `usage-meter.py` |
| 11 | Minor | Runtime `unknown` por defecto: ninguna pieza fija `CUSTOM_AGENTS_RUNTIME`; `agent-kits/shared/README.md` (E8) no recoge `verdict`/`reconcile`/`handoff`/`--dispatch`; el ledger no pega la salida de `reconcile` | T-40 | corregido (fix1, c13853e; test `test_fix1_gap11_shared_readme_documents_runtime_handoffs`) | `ledger-write.py:319-321`; `agent-kits/shared/README.md:58-59` |


## Revisión de dos lentes — intento 2: Fase 3 (T-40) — verificación del fix1 (T-40)

**Veredicto del plugin**: gaps (T-40)
Lentes A y B (Claude Opus 5.5, esfuerzo alto) sobre `f3a8572..c0e2c02` (fix1 de Codex gpt-6.2-sol). Gaps 1-7, 9 y 11 del intento 1 ✓ con test dedicado; carrera de `usage-meter` 20+20 sin pérdidas; `reconcile` sobre las 40 tareas no cambia ningún estado (T-02 y T-23 siguen `en-progreso`); T-40 pasó a `en-revision` por `usage-meter close` (evento `source: usage-meter`, `runtime: codex`). Seguridad sin hallazgos.

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | El ledger no recoge la Verificación del fix1 (ni los tests en verde ni el `export-interop --check`, aunque el fix1 toca `agents/`, `commands/`, `hooks/`) | T-40 | corregido (fix2, ab227f7; test `test_fix2_gap1_ledger_records_verification`) | `tasks.md` (bloque fix1 de T-40, sin «passed»); criterios 5 y 6 de la Lente A |
| 2 | Important | Regresión del gap 8: `ids_de_celda_tarea` descarta en silencio las tareas tras `;`, `+`, `→` o que no abren la celda (`(T-01)`, `Fase 1 (T-01)`); `verdict limpio` cierra una tarea con un Critical pendiente y el brief/`aprobado` de jira-flow ven 0 pendientes (falla abierto) | T-40 | corregido (fix2, 9e79cad; test `test_fix2_gap2_critical_cell_blocks_clean_verdict_brief_and_jira`) | `ledger-lint.py:321-327,485,517`; `task-brief.py:795,959`; `jira-flow.py:436,600`; `scratchpad/lb40b/scripts/failopen.py` |
| 3 | Minor | Gap 10 marcado «corregido» sin llegar al objetivo: base `c34e9e0` → HEAD, `start` +0,65-0,8 s y `close` +0,7-0,9 s (ledger de 222 KB); un traspaso sin cambio cuesta 0,60 s porque valida todo | T-40 | corregido (fix2, af8dde3; test `test_fix2_gap3_meter_handoff_avoids_second_interpreter`) | `ledger-write.py:319-329`; `usage-meter.py:796-812`; `scratchpad/lb40b/scripts/bench.py` |
| 4 | Minor | `phase_state` pierde la rama `cancelado`: todas canceladas → `completado`; `borrador` + una cancelada → `en-progreso` | T-40 | corregido (fix2, 9e79cad; test `test_fix2_gap4_phase_state_respects_cancellation`) | `ledger-write.py:136-145`; `scratchpad/lb40b/scripts/phase.py` |
| 5 | Minor | El test JS del gap 2 deja vivos 3 de 7 mutantes (no retira el panel anterior, `append` frente a `prepend`, orden/ventana) | T-40 | corregido (fix2, e43426c; test `T-40 fix2 gap 5: transition-only polling replaces one leading panel with the newest 20 rows`) | `tests/console-live.test.mjs:76-113`; `console-context.js:170` |
| 6 | Minor | La aserción de PLUGIN-PANEL del test del gap 1 entró con su cambio, sin rojo; la salida de `reconcile --dry-run` pegada solo cubre T-23 | T-40 | corregido (fix2, ab227f7; test `test_fix2_gap6_ledger_discloses_concurrent_doc_assertion`) | `test_ledger_write_transitions.py:234-237`; `tasks.md` (fix1 de T-40) |
| 7 | Minor | Con el lock del state retenido > 2 s, `start` devuelve `ok` con aviso pero no guarda el marcador (el `close` posterior dirá «sin marcador») | T-40 | corregido (fix2, 9e79cad; test `test_fix2_gap7_start_reports_unsaved_marker_when_state_locked`) | `usage-meter.py:824-830` |


## Revisión de dos lentes — intento 3: Fase 3 (T-40) — verificación del fix2 (T-40)

**Veredicto del plugin**: gaps (T-40)
Lentes A y B (Claude Opus 5.5, esfuerzo alto) sobre `5e397d0..b212ae6` (fix2 de Codex gpt-6.2-sol). Los 7 gaps del intento 2 ✓ con test dedicado y rojo real (`e43426c`, `9d19226`); `reconcile` sin cambios sobre todos los ledgers; el medidor no se bloquea en 10 escenarios; ruta caliente +0,36-0,53 s sobre la base según la carga (objetivo +0,5 s); T-40 pasó a `en-revision` por `usage-meter close` (runtime codex).

| # | Grado | Gap | Tarea | Corrección | Evidencia |
|---|---|---|---|---|---|
| 1 | Important | La celda Tarea cuenta los IDs uno a uno: un rango (`T-01..T-03`, `T-01 a T-03`) solo cubre sus extremos y la tarea intermedia falla abierto (`verdict limpio` la cierra con un Critical pendiente; brief y jira-flow ven 0). La notación existe en ledgers reales. Misma clase que el gap 2 del intento 2 | T-40 | corregido (fix3, 0fc4c21; test `test_fix3_gap1_task_cell_whitelist`) | `ledger-lint.py:321-324`; `task-brief.py:795-798`; `jira-flow.py:436-439`; `docs/roadmap/2026-10-15-panel-redesign/tasks.md:1955`; `scratchpad/l3/scripts/failopen.py` |
| 2 | Minor | Mutante vivo del panel: con la firma igual, devolver `null` en vez de `host` borra las transiciones en el siguiente sondeo con actividad nueva | T-40 | corregido (fix3, e3476b2; test `T-40 fix3 gap 2: new activity keeps the unchanged transitions panel`) | `skills/plugin-panel/assets/console-context.js:167,217`; `tests/console-live.test.mjs:120-144` |
| 3 | Minor | Margen del objetivo de la ruta caliente: con la máquina cargada `start` con cambio llega a +0,53 s | T-40 | deuda aceptada por el usuario (2026-11-24: «Lista blanca + medir Codex») | `tasks.md` (fix2 de T-40); `scratchpad/la40c` |
| 4 | Minor | El fix2 se apunta «0.01h (medido)» con el marcador vacío: `usage-meter` no ve las transcripciones de Codex (busca las de Claude), así que la medida de un implementador Codex no existe | T-40 | corregido (fix3, 0fc4c21 y a19989f; test `test_fix3_gap4_codex_measures_window_and_project_without_duplicate_tokens` y fixture OpenCode) | `tasks.md` (fix2 de T-40); marcador `plugin-audit-2/T-40-fix2` con `offsets: {}` |

Decisión del usuario (2026-11-24), textual: «Lista blanca + medir Codex». Ciclo nuevo de revisión (intento 4) con fix3: la celda Tarea solo admite formas reconocidas (falla cerrado por construcción), test del mutante del panel y medición de las sesiones de Codex y OpenCode en `usage-meter`; el margen de la ruta caliente queda como deuda aceptada.
