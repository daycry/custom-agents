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
plan: plugin-audit-2
estado: aprobado
creado: 2026-11-10
tasks: tasks.md
analysis: analysis.md
spec: n/a
evaluacion: n/a
test-plan: n/a (sin UI)
rama: fix/plugin-audit-remediation
---

# Plan: segunda auditoría del plugin (calidad, tokens y retirada de lo que sobra)

[Ledger](tasks.md) · [Análisis de origen](analysis.md)

| Cadena | Enlace |
|---|---|
| Spec | n/a: la iniciativa nace de un informe de auditoría, no de una spec |
| Evaluación | n/a: las cifras de este plan son su propia estimación |
| Origen | [`analysis.md`](analysis.md) (hallazgos 1.x a 5, con evidencia `fichero:línea`) |
| Ledger | [`tasks.md`](tasks.md), 37 tareas en 6 fases (tope de 80 KB; las fases se archivan al cerrarse) |
| Estado | `borrador`. **La ejecución NO está autorizada**: el usuario pidió el plan, no implementarlo. No queda ninguna decisión pendiente |

## Objetivo

Dejar el plugin «perfectamente implementado y optimizado» sin sobreingeniería y sin código muerto, en tres ejes medibles:

1. **Calidad.** Cero defectos conocidos del análisis y menos código que ya no ejecuta nadie.
2. **Consumo de tokens.** Menos texto cargado por ciclo; cada tarea de tokens lleva una cifra objetivo medible con `agent-kits/shared/context-footprint.py` (tamaño de fichero, no consumo facturado).
3. **Tres runtimes.** Todo lo que se cambie funciona en Claude Code, Codex y OpenCode.

## Tres runtimes (requisito de salida de cada fase)

Restricción del usuario (2026-11-10): ninguna fase se cierra si algo deja de funcionar en alguno de los tres. Cada tarea que toque un agente, comando, skill, hook, el instalador o un manifiesto referencia la **puerta «runtimes»** de la cabecera del ledger y dice en su línea `Runtimes` qué cambia en cada uno, o «sin diferencia». La puerta reúne suites que existen hoy:

| Suite | Qué prueba |
|---|---|
| `python scripts/export-interop.py --check` | `interop/**`, `.codex-plugin/` y `.agents/plugins/` regenerados y al día |
| `tests/test_export_interop.py` | Traducción de `tools:`, skills, delegación y descriptions a Codex y OpenCode |
| `tests/test_plugin_root_resolution.py` | La receta de seis raíces resuelve el kit sin `CLAUDE_PLUGIN_ROOT` |
| `tests/test_native_role_context.py`, `test_native_guardrail_dispatch.py`, `test_native_prefilter_parity.py` | Guardarraíl nativo de Codex y OpenCode |
| `node --test tests/opencode-plugin.test.mjs` | Adaptador de hooks de OpenCode (`hooks/opencode-plugin.js`) |
| `node --test tests/codex-native-install.test.mjs tests/installer.test.mjs tests/hook-runtime.test.mjs` | Instalación nativa de Codex, instalador de copia y lanzador de hooks |

Qué cubre ya el repo y qué no (comprobado en código y tests):

- **`Skill` (T-02).** Es de Claude Code. Codex recibe agentes sin `tools` y menciona la skill con `$custom-agents:X` (`docs/INTEROP.md:79`); OpenCode fija `skill: allow` (`scripts/export-interop.py:589`). Solución común: el cuerpo da la ruta `skills/<x>/SKILL.md`. Lo cubre `tests/test_export_interop.py`; el comportamiento real en sesión es el paso manual M-A.
- **Índice de arranque (T-20).** Ya existe una base: `tests/test_session_context.py:86` y `:134` parametrizan `claude`, `codex` y `opencode`, y `agent-kits/shared/test_skill_index.py:85` hace lo mismo. T-20 añade la aserción por runtime (Claude solo cabecera; Codex y OpenCode índice completo). Que el arranque real de Codex y OpenCode lo muestre es el paso manual M-C.
- **`async` en hooks (T-24).** `hooks/hooks.json` marca `async` en la actividad (`:34`, `:46`) y `interop/codex/hooks.json:103` solo en el grupo de actividad; `tests/test_export_interop.py` y los `.test.mjs` de Codex no mencionan `async`, así que **ninguna suite demuestra que Codex lo honre en `UserPromptSubmit`**: no se propaga hasta la verificación manual M-D. OpenCode tiene su catálogo de bindings (`hooks/opencode-plugin.js:28-34`, `post` ya es único) y su suite (`tests/opencode-plugin.test.mjs`).
- **Alias `*.sh` (T-25).** Son identidades de hook: `tests/hook-runtime.test.mjs` y `tests/opencode-plugin.test.mjs:125,179,461` las usan y `interop/codex/hooks.json` las lleva en sus comandos. Se conservan; que una instalación ya hecha siga disparando tras actualizar es el paso manual M-E.
- **Instalador (T-27).** Es la vía de OpenCode (copia) y de Codex (nativo): `tests/installer.test.mjs`, `install-auth.test.mjs` y `codex-native-install.test.mjs`. `install/install.mjs:464-470` es la detección de copia heredada de OpenCode (no es código muerto); la instalación real es el paso manual M-F.
- **Receta del kit (T-17).** `CLAUDE_PLUGIN_ROOT` solo existe en Claude Code: el criterio la prueba sin definir y con raíces `.codex`/`.opencode` (`test_plugin_root_resolution.py`).
- **Brief y referencias (T-12, T-18, T-19).** El brief es texto de `task-brief.py`; las referencias de `agent-kits/` viajan en el payload común (`install/providers.mjs:28-34`).
- **Skills y comandos retirados o fusionados (T-03, T-35).** Cambian lo exportado: un adaptador de Codex (`custom-agents-<cmd>`) y un comando de OpenCode desaparecen.
- **`plugin-dev` (T-11).** Cómo carga cada runtime una skill de proyecto no se puede probar desde el repo: paso manual M-B.

## Decisiones del usuario

**Decididas (2026-11-10), no se vuelven a proponer:**

| Decisión | Efecto en el plan |
|---|---|
| Kwipu y Graphiti se retiran YA, sin esperar a Kairos | T-08 y T-09, tareas normales. Cambio rompedor, versión mayor |
| Marco de `knowledge-services` sin backends: opción (b), se retira; la iniciativa de Kairos lo recupera del commit anotado en T-08 | T-10 |
| La partición en núcleo y satélites se descarta | Sin tarea; ver «Por qué no se parte» |
| Las cuatro skills de contenido se conservan por decisión del usuario (`voice-profile`, `content-production`, `relationship-planning`, `competitive-analysis`) | Fuera de alcance: que una auditoría futura no las vuelva a proponer. Solo reciben mejoras generales (T-15) |
| `training-data-services` se queda y se congela: nada de refactor ni endurecimiento salvo borrar código sin llamante | T-31 evalúa su destino |
| El conocimiento no se entrena: lo aporta la memoria al consultar (`docs/knowledge/` hoy, Kairos después); LoRA, como mucho, para formatos del plugin y fuera de este plan | Contexto de T-31 y T-32 |
| `dev-cycle-dataset` no se ejecuta tal como está: «superada por evaluación» | La cierra T-32 con puntero a este plan, o T-36 si T-32 no se ejecuta |
| Exportación a posteriori del entrenamiento: opción (a), **condicionada al veredicto de T-31** | T-32. Es la única puerta que queda: si T-31 concluye (a) y no halla datos irreconstruibles, se ejecuta sin volver a preguntar; si concluye (b) o (c), o halla datos irreconstruibles, se detiene y vuelve al usuario con la evidencia |
| Modos de implementación: se fusiona `lite` con `subagentes`; el modo único se aplaza | T-33; el modo único queda fuera de alcance |
| Retro fuera de la vía rápida: sí (opcional, se ofrece si el cambio superó la estimación; obligatoria en el flujo completo) | T-34 |
| Fusiones: sí a las tres (`llm-pipeline` y `data-collection` en `backend-practices`; `confluence-pull` en `confluence-publish`; `/roadmap-metrics` en `/roadmap-status --metrics`) | T-35 |
| Tres runtimes como requisito | Sección anterior |
| `.claude/knowledge-services/taxonomy.json` (cambios locales sin comitear) no se toca | Fuera de T-08; es acción del usuario |

**Pendientes:** ninguna. Solo quedan las acciones del usuario del final de este documento.

## Alcance

| Fase | Contenido | Hallazgos | Tareas |
|---|---|---|---|
| 1. Defectos | Aviso falso, invocar skills sin `Skill`, nombre duplicado, prosa, descriptions, guardarraíl, `code-health` | 1.1-1.10 | T-01…T-07 |
| 2. Retirada decidida | Kwipu y Graphiti (código y docs), marco de `knowledge-services`, `plugin-dev` fuera del plugin | 3.2 (parte), decisiones | T-08…T-11 |
| 3. Tokens | Ordenada por ahorro/esfuerzo; línea base tras la fase 2 | 2.1-2.14 (2.10 absorbida por T-08/T-09) | T-12…T-22 |
| 4. Simplificación | CI paralela, hooks, alias shell, copias, instalador, FTS5, panel, nombres de tests | 4.1-4.3, 4.6-4.8, 4.10, 4.11 | T-23…T-30 |
| 5. Alcance y entrenamiento | Evaluación y exportación de casos (T-32 condicionada a T-31), fusión `lite`/`subagentes`, retro en la vía rápida, fusiones | 3.4-3.8 | T-31…T-35 |
| 6. Higiene | Cierres, estados rancios, memoria | nivel 5 | T-36, T-37 |

La retirada va antes de tokens y simplificación para no adelgazar dos veces lo que se va a borrar (`/setup`, `/doctor`, `capabilities.py`, `knowledge-find.py`).

## Fuera de alcance

- **Revisado y justificado, no tocar:** `runtime-supervisor.py` con Job Objects, el prefiltro del guardarraíl en node, `redact.py` y `local-read.py`, `outbox.py` (lo usan el journal, `doctor.py` y `knowledge-schema.py`; su mención de Graphiti es solo un comentario), las cuatro `*-practices`, `tdd` frente a `unit-tests`, `roadmap-dashboard` frente a `plugin-panel`.
- **Se conservan por decisión del usuario:** las cuatro skills de contenido y `training-data-services` (esta, pendiente de T-31; mientras tanto congelada: `case-recorder.py`, 3.343 líneas, no se refactoriza).
- **4.4 (módulo común `kit.py`) y 4.5 (partir `journal.py` y `doctor.py`):** ADR-016 descartó el módulo común para que las piezas viajen sueltas y partir ficheros de 2.900-3.200 líneas no reduce tokens ni errores. Se reevalúan tras T-26.
- **4.9 (escáner JSON de la statusline):** opt-in y solo Claude Code; sin ganancia que lo justifique.
- **4.12 (capa bash del lanzador):** no se sostiene: `runtime-entry.sh` también ejecuta `mark-docs-pending.sh`, registrado en `hooks/hooks.json`.
- **Integración de Kairos:** otra iniciativa; se abrirá con `/pm-cycle` tras T-10. Su propuesta vive fuera del repo; aquí es dependencia. No se extrae el cliente MCP de `graphiti.py`: sin consumidor, se recupera del commit anotado en T-08.
- **Partición en satélites (3.1):** descartada.
- **Modo único de implementación «brief por tarea» (3.5):** aplazado por decisión del usuario; no hay datos de uso del lote paralelo que justifiquen perderlo. T-33 solo fusiona `lite` con `subagentes`.
- **Merge del PR #32, release, checklist M-01, ramas, migración de la taxonomía local y regeneración de PDF:** acciones del usuario.

## Por qué no se parte el plugin

`install/modules.mjs:76-82` solo admite entrega selectiva en Claude Code modo copia (perfiles `core`, `developer`, `research` y `full` en `agent-kits/shared/modules.json`); para OpenCode falla («selective delivery is not supported by the OpenCode installer») y los plugins nativos entregan el bundle completo. Las marketplaces (`.claude-plugin/marketplace.json`, `.agents/plugins/marketplace.json`) listan un solo plugin con `source: ./` y `scripts/export-interop.py:284-338` genera un único `plugin.json`. Partir exigiría un plugin y un manifiesto por satélite en Claude y Codex, copia selectiva e índice filtrado en OpenCode y N manifiestos por release (≈10 h).

Con las decisiones tomadas no queda qué partir. Solo `plugin-dev` (353 caracteres de description ≈ 88 tokens por sesión, 58 KB) sería candidata, y T-11 la saca por una vía más simple: moverla a `.claude/skills/plugin-dev/`. Comprobado en el repo: el payload de los instaladores no incluye `.claude/` (`install/providers.mjs:28-34`, `package.json` `files`), `scripts/export-skills.py:63,357` y `tests/test_export_skills.py:252` ya la excluyen del paquete portable y `.gitignore` no ignora `.claude/skills/` (`.claude/rates.json` y `jira.json` ya están versionados). Sin verificar: cómo carga cada runtime una skill de proyecto (paso manual M-B).

## Retirada medida (T-08 a T-10)

Medido sobre el árbol versionado, HEAD `129dbeb`.

**Clasificación de los 137 ficheros** que mencionan Kwipu o Graphiti (`git grep -il -E "graphiti|kwipu"` excluyendo roadmap, CHANGELOG, `docs/knowledge/` e `interop/`):

| Clase | Ficheros | Dónde |
|---|---|---|
| Se borran | 37 | 34 de `skills/knowledge-services/` + `tests/test_graphiti_model.py` + las dos guías `docs/{,en/}knowledge-services-graphiti.md` |
| Se dividen | 1 | `tests/test_graphiti_security.py` (ver abajo) |
| Se editan | 96 | docs y READMEs 38, tests 31, `agent-kits/` 10, skills ajenas 6, skill `knowledge-services` 4, commands y agents 3, evals 3, `.gitignore` 1 (T-08 y T-09) |
| PDF generados | 2 | `output/pdf/*.pdf`: no se editan a mano |
| Config local del usuario | 1 | `.claude/knowledge-services/taxonomy.json` |

La skill `knowledge-services/` tiene 49 ficheros versionados: se borran 39 (18.287 líneas: código 7.351, test 8.494, fixtures 1.963, docs 479) y quedan 10 (marco: código 670, test 1.212, docs 469). Mención de `outbox.py`: solo un comentario de cabecera.

**Trampa descubierta: `tests/test_graphiti_security.py` no se puede borrar entero.** Sus 2.953 líneas contienen el escáner «ningún hook hace red» (recorrido transitivo de lo que cita `hooks/hooks.json`, mutantes, actividad), con unas 800 líneas de tests y ≈1.435 de helpers que cargan `tests/test_hook_launcher_security.py` (`:27,47,55,66`) y `tests/hook-budget.test.mjs:4`. Los tests Graphiti-específicos suman ≈718 líneas (clasificación por nombre, a revisar al ejecutar). T-08 lo renombra `tests/test_hook_network_egress.py` y retira solo esas; el borrado real de tests es por tanto ≈ 8.494 + 418 + 718 y no los 11,8 K estimados antes.

**Marco de `knowledge-services` (T-10).** Decidido (b): se borran 670 líneas de código, 1.212 de test, 469 de docs y `knowledge-find.py:1377-1934` (558). `--intent` casa en 34 ficheros; 10 son otra cosa (`--intento` de `phase3-jira.md`, `ledger-lint.py`, `task-brief.py`, `jira-sync/**`, `test_review_jira_owner.py`, y `--intent-to-add` de `COMMIT-SELECTION` y su prueba): no cambian; los 24 restantes son uso real y están en `Archivos` de T-08 (los del adaptador), T-09 (docs) y T-10. Los fragmentos que cargan los agentes: `knowledge-check-governed.md` no menciona router, intent ni backends (no cambia con (a) ni (b)); `knowledge-check.md:8,22` dice «fallo de backend» y «backends declarados» (con (b) se reescribe); `phase4-knowledge-gate.md:25-27` ya lo edita T-09. (a) habría dejado ≈2.600 líneas dormidas sin consumidor; la iniciativa de Kairos recupera el marco del commit anotado en T-08.

**ADR y memoria.** ADR-020 (Graphiti) y ADR-021 (alta Kwipu) quedan obsoletos y ADR-018 se mantiene con una nota, todo propuesto por `knowledge-curation.py propose`. La memoria aprobada que cita Kwipu o Graphiti (patrones y lecciones; no hay gotchas) la revisa T-37. Rompe a quien use esos backends: versión mayor y aviso en los dos CHANGELOG.

**`training-data-services` (T-31 y T-32).** 6.400 líneas de código y 11.808 de test. Opción (a): casi todo; (b): ≈3.625 de código y ≈7.073 de test; (c): nada. T-31 lo confirma antes de tocar nada.

## Verificación de la evidencia del análisis

| Resultado | Hallazgos |
|---|---|
| Confirmado | 1.1 (`progress-report.py:479-481`), 1.3, 1.5, 1.8, 2.6 (19 y 14 recetas), 4.3 (cabecera «REPLICADO LITERAL … ADR-016»), 4.7, 4.8 (`hooks.json:105-115` sin `async`), 2.14 (`export-interop.py:107`) |
| Con matiz | **1.2** también afecta a `qa`, y `Skill` solo existe en Claude. **1.3** solo en Claude (Codex antepone `custom-agents-`, `export-interop.py:559-572`). **2.9**: 25 ocurrencias, no 21. **4.1**: 23 ficheros duplicados en un recuento rápido, 27 según el análisis. **4.2**: solo 4 shells son alias de Python (`run-hook.mjs:331-345`: `session-context`, `session-journal`, `subagent-progress`, `user-prompt-capture`, 511 líneas); `mark-docs-pending.sh`, las dos guardias y los dos shells no registrados corren por `runtime-entry.sh` o son interfaz de copias locales (`run-hook.mjs:130-132`). **4.3**: ADR-016 y `copias.json` declaran esas copias. **4.10**: `install.mjs:464-470` no es código muerto. **2.10** se absorbe en T-08/T-09 |
| Coherencia T-03 y T-35 | T-03 retira el comando `/confluence-pull` y añade la regla del linter contra colisiones (fase 1); T-35 retira después la skill al fusionarla en `confluence-publish`. Ninguna hace innecesaria a la otra: T-03 corrige hoy la colisión y deja el guardarraíl, T-35 depende de T-03 para no borrar dos veces, y al terminar T-35 desaparece la invocación `/confluence-pull` (decidido) |
| No se sostiene | **4.12** (ver «fuera de alcance») |
| Sin reproducir | 1.4, 1.6, 1.7, 1.9 (timeout del auditor), 2.1-2.5, 2.7, 2.8, 2.11-2.13 (tamaños de fichero; los ahorros son estimaciones), 4.6 |
| Rebatido | Ninguno |

## Orden y dependencias

```
Fase 1 (T-01…T-07)   sin dependencias; T-23 (CI) puede adelantarse a la fase 1
Fase 2 (T-08…T-11)   T-08 → T-09 ; T-08 → T-10 ; T-11 independiente
Fase 3 (T-12…T-22)   línea base tras la fase 2; T-12, T-13, T-14 primero;
                     T-12,T-13,T-11 → T-15 → T-16 → T-17 → T-18 → T-19 ; T-18,T-19,T-11 → T-22
Fase 4 (T-23…T-30)   T-23 → T-24 → T-25 → T-27 ; T-23 → T-29 ; T-19,T-08 → T-26 → T-30
Fase 5 (T-31…T-35)   T-31 → T-32 (puerta: veredicto de T-31) ; T-33 tras T-19 ; T-34 tras T-16 ; T-35 tras T-03, T-05 y T-16
Fase 6 (T-36, T-37)  T-36 tras T-08 ; T-37 tras T-08, T-09 y T-10
```

Cada fase es una entrega revisable por separado (revisión de dos lentes al cerrarla, bucle acotado a 3) y se archiva al cerrarse.

## Orden recomendado de ejecución

1. **T-23 (CI en paralelo)**, opcional y antes de todo: abarata verificar lo demás. Copiar la CI es acción del usuario.
2. **Fase 1** (T-01…T-07), en cualquier orden; T-02 y T-03 primero si se quiere cerrar los defectos que afectan a los tres runtimes.
3. **Fase 2**: T-08 → T-09 → T-10 (retirada, con `testing/retirada.md` y el commit recuperable antes de borrar) y T-11 (`plugin-dev`) en paralelo. Línea base de tokens al terminar.
4. **T-31** (evaluación, sin código) en cuanto acabe la fase 2: su veredicto decide T-32 y no depende de nada más.
5. **Fase 3** (tokens): T-12, T-13, T-14; después T-15 → T-16 → T-17 → T-18 → T-19 → T-21, T-22; T-20 independiente.
6. **Fase 4**: T-24 → T-25 → T-27, T-29, T-26 → T-30 (el renombrado de tests va al final: es mecánico y ruidoso), T-28 libre.
7. **T-32 solo si T-31 lo permite**, T-33, T-34 y T-35 tras sus dependencias (T-19, T-16 y T-03/T-05/T-16).
8. **Fase 6**: T-36 y T-37 al cerrar; la retro de `plugin-audit-remediation` espera al merge del PR #32.

Cada fase pasa la puerta «runtimes», se revisa con dos lentes y se archiva; las verificaciones manuales (M-A…M-F) se hacen en la fase de su tarea.

## Criterios de salida por fase

| Fase | Se sale cuando |
|---|---|
| 1 | Los tests rojos iniciales pasan a verde; la puerta «runtimes» en verde; el arranque de este repo no muestra `ilegible (redirected_path)`; M-A resuelto |
| 2 | `git grep -il -E "graphiti\|kwipu"` solo devuelve lo declarado en `testing/retirada.md`; la suite «ningún hook hace red» íntegra con su nuevo nombre; `testing/retirada.md` con el commit recuperable y las líneas borradas; M-B resuelto |
| 3 | Cifra objetivo medida por tarea en `testing/tokens.md`; puertas de tokens (vía rápida ≥ 6.000, `evaluator.md` ≤ 15.513 bytes en LF, `--diet-check`) y de runtimes en verde; M-C resuelto |
| 4 | Misma conducta, demostrada por la suite que cada tarea nombra; CI replicada en Linux (`python:3.11-slim`, LF); tiempos en `testing/perf.md`; M-D, M-E y M-F resueltos |
| 5 | `testing/evaluacion-training.md` con veredicto; T-32 ejecutada solo si el veredicto es (a) sin datos irreconstruibles, o devuelta al usuario con la evidencia |
| 6 | `retro-gate.py` exit 0 o exención escrita; candidatos de memoria resueltos |

## Riesgos

| Riesgo | Prob. | Mitigación |
|---|---|---|
| **Romper Codex u OpenCode** (agentes, comandos, hooks, exportador, instalador) | Media | Puerta «runtimes» y línea `Runtimes` por tarea; solo hay ficheros generados y suites, no ejecución real: lo que ninguna suite demuestra es un paso manual (M-A…M-F) |
| **Perder una puerta al adelgazar prosa** (fase 3) | Alta | `--diet-check` por tarea, líneas base con motivo; ninguna regla se borra sin ubicarla |
| **Ahorros estimados, no consumo medido** | Alta | Cada tarea de tokens fija una cifra objetivo medible; `testing/tokens.md` separa medida de estimación |
| **Borrar un invariante de seguridad con un nombre engañoso** (`test_graphiti_security.py` guarda «ningún hook hace red») | Alta (ya ocurrió en la planificación) | T-08 lo divide, no lo borra; criterio y verificación de que la suite conserva todos sus tests genéricos |
| **Cambio rompedor por la retirada** (T-08, T-09, T-10, T-32) | Alta (decidido) | Versión mayor, aviso en ambos CHANGELOG, commit recuperable anotado, mensaje de error claro |
| **Retirar algo que usa otra pieza** (`capabilities.py` importa `training`; `outbox.py` lo usa el journal; shells con consumidores) | Media | Enumerar consumidores con `git grep` antes de borrar (hecho para T-08, T-10 y T-25) |
| **T-31 contradice la opción (a)** o halla datos irreconstruibles | Media | T-32 se detiene y vuelve al usuario con la evidencia; hasta entonces `training-data-services` congelada |
| **Verificaciones manuales sin ejecutar** (M-A…M-F) | Media | Son pasos explícitos de sus tareas; si el usuario no las hace, la tarea no se cierra con esa parte y se anota como no verificado |
| **Puerta de la vía rápida** (margen 6.000 tokens) | Media | T-16 la mejora; ninguna tarea previa la consume |
| **ADR-016** (T-26) y `copias.json` (T-08) | Media | Enmienda por `knowledge-curation.py propose`; `tests/test_copias_declaradas.py` en las dos tareas |
| **`pytest -n auto`** expone estado global | Media | Los que fallen se marcan serie con motivo; replicar la CI en Linux |
| **Plugin instalado ≠ rama** | Media | T-02 empieza con una prueba en sesión real (M-A) |

## Presupuesto

Método: horas humanas realistas por tarea (S ≈ 1,5-2 h, S-M ≈ 3 h, M ≈ 5-6 h, M-L ≈ 8-14 h); horas IA ≈ 25-35 % de las humanas; supervisión = 25 % de las horas IA; tokens = ficheros a leer × tamaño medio + generación (80 % entrada, 20 % salida). Base = punto medio sin colchón; con margen = +20 % sobre horas humanas e IA. `.claude/rates.json`: 50 €/h, tokens a 4 y 20 USD por millón (verificado el 2026-10-20), 0,92 EUR/USD (supuesto fijo). Los tokens cuestan unos 68 € en total.

| Fase | Tareas | H. humanas | H. IA | Superv. | IA+sup. | Tokens | € horas | H. con margen | € con margen |
|---|---|---|---|---|---|---|---|---|---|
| 1. Defectos | 7 | 15 | 4,0 | 1,00 | 5,00 | 1.090k | 750 | 18 | 900 |
| 2. Retirada decidida | 4 | 32 | 7,9 | 1,98 | 9,88 | 2.100k | 1.600 | 38,4 | 1.920 |
| 3. Tokens | 11 | 30 | 8,2 | 2,05 | 10,25 | 2.260k | 1.500 | 36 | 1.800 |
| 4. Simplificación | 8 | 34,5 | 8,5 | 2,13 | 10,63 | 2.470k | 1.725 | 41,4 | 2.070 |
| 5. Alcance y entrenamiento | 5 | 26 | 6,5 | 1,63 | 8,13 | 1.800k | 1.300 | 31,2 | 1.560 |
| 6. Higiene | 2 | 7 | 1,7 | 0,43 | 2,13 | 500k | 350 | 8,4 | 420 |
| **TOTAL** | **37** | **144,5** | **36,8** | **9,20** | **46,00** | **10.220k** | **7.225** | **173,4** | **8.670** |

**Frente al presupuesto anterior** (36 tareas): 135 h → 144,5 h (+9,5), 9.620k → 10.220k tokens, 6.750 € → 7.225 € (8.100 € → 8.670 € con margen). Las decisiones de hoy solo cambian T-33 (4 h → 5 h: `lite` es un perfil con `execution-profile.py`, `tests/test_lite_profile.py` y 25 ficheros de docs, no solo prosa). Sube la fase 2 (21 → 32 h): T-08 pasa de 12 h a 14 h + 7 h de documentación (T-09) porque el alcance real son 137 ficheros y no 30, hay que dividir un test de seguridad y reapuntar otros dos, T-10 pasa a 6 h y T-11 a 5 h con 33 ficheros. Baja la fase 4 (37 → 34,5 h): T-25 cae a 5 h porque solo 4 de los shells son alias (511 líneas, no 860) y T-27 a 2,5 h sin el hallazgo 4.12. T-08 se parte porque su alcance pasaba de 16 h (21 h en total).

Sin la fase 5 (la parte que espera decisiones; T-31 no espera): 118,5 h, 8.420k tokens, 5.925 € (7.110 € con margen).

### Productividad IA

| Medida | Base | Con margen |
|---|---|---|
| Horas humanas equivalentes | 144,5 | 173,4 |
| Horas IA + supervisión | 46,0 | 55,2 |
| Horas ahorradas | 98,5 | 118,2 |
| Ahorro | 68,2 % | 68,2 % |
| Multiplicador | 3,1× | 3,1× |
| FTE ahorrado (160 h/mes) | 0,62 | 0,74 |

Las horas IA son estimaciones aproximadas, igual que los tokens; `usage-meter.py` medirá las reales.

## Acciones del usuario (no son tareas del ledger)

**Decisiones y gestión**
- Revisar y hacer **merge del PR #32**; este plan puede ejecutarse en una rama nueva si sigue abierto. **Autorizar la ejecución del plan**: hoy está en `borrador` y no está autorizado.
- **Release como versión mayor** con `python3 scripts/release.py X.0.0` (`--dry-run` antes): la retirada de Kwipu y Graphiti (T-08, T-09), del marco (T-10) y, si T-31 lo permite, de la captura en vivo (T-32) es un cambio rompedor. La lanza el usuario.
- Copiar `ci.yml.MANUAL-COPY` a `.github/workflows/ci.yml` tras T-23 (y tras T-08 y T-10, que cambian las rutas de test); hoy los dos ficheros son idénticos.
- Abrir la iniciativa de Kairos con `/pm-cycle` cuando T-10 esté hecho (el marco se recupera del commit anotado en T-08).
- Si T-31 concluye (b) o (c), o halla datos irreconstruibles, decidir con su evidencia qué hacer con T-32.
- **Migrar su `.claude/knowledge-services/taxonomy.json` local** (cambios sin comitear): quitar los backends `kwipu`/`graphiti` y las claves `routing` correspondientes; T-08 no lo toca. El pendiente de reindexar Kwipu deja de tener sentido.
- **Regenerar los PDF** `output/pdf/custom-agents-manual-operativo.pdf` y `output/pdf/guia-resultados-calidad-custom-agents.pdf` (mencionan Kwipu y Graphiti; no se editan a mano y viajan en el paquete npm).
- Decidir el destino de las **ramas**: `fix/graphiti-add-memory-uuid` (cerrar o cancelar por retirada), `model-routing-lab` (activa; T-31 la lee solo con `git show`), `graphiti-uuid-fix`, `sdd-proporcional`, `project-dashboard`; y de los 36 worktrees registrados.
- Decidir la **excepción «evidenciado (medida)»** de la constitución, ejecutar o anotar como no verificable la **checklist manual M-01 del instalador** y participar en las retros de T-36.

**Verificaciones manuales** (lo que ninguna suite del repo demuestra; cada una es un paso `lectura (manual…)` de su tarea)

| Id | Tarea | Qué comprobar en sesión real |
|---|---|---|
| M-A | T-02 | En Claude Code, si un agente con `tools:` sin `Skill` puede invocar una skill; en Codex y OpenCode, que el agente sigue la skill leyendo su `SKILL.md` por la ruta |
| M-B | T-11 | `plugin-dev` visible en este repo y no en un proyecto con el plugin instalado (Claude Code); OpenCode la lee de `.claude/skills/`; dónde ve Codex las skills de proyecto |
| M-C | T-20 | En Codex y OpenCode reales el arranque muestra el índice de piezas completo; en Claude solo la cabecera |
| M-D | T-24 | En Codex, el hook de `UserPromptSubmit` marcado `async` captura el prompt sin bloquear el turno |
| M-E | T-25 | Una instalación previa de Codex u OpenCode se actualiza y los hooks siguen disparando con los mismos nombres |
| M-F | T-27 | Instalar y desinstalar en un directorio temporal con OpenCode y Codex da el mismo manifiesto que antes |

## Método

- TDD (`tdd: true`): cada tarea de código nombra el test que debe fallar primero; las de prosa llevan su puerta determinista.
- Cada tarea que toca un agente, comando o hook regenera `interop/**` y lleva los espejos de `docs/en/`; el `Archivos` de cada tarea se comprobó con `git grep` o con existencia de fichero (las rutas nuevas llevan «(nuevo)»).
- Antes del PR se replica la CI en Linux (`python:3.11-slim`, LF); ningún rojo se acepta como «de siempre».
- Medidas en `testing/tokens.md`, `testing/perf.md` y `testing/retirada.md`; `docs/TOKEN-EFFICIENCY.md` y su espejo EN separan tamaño medido de consumo observado.

## Supuestos

Tarifa 50 €/h · supervisión 25 % de las horas IA · contingencia +20 % · FTE 160 h/mes · tokens a 4/20 USD por millón (`rates.json`, 2026-10-20; cambio 0,92 supuesto) · tokens ≈ caracteres/4 · reparto 80/20 entrada/salida supuesto.

## Changelog

- 2026-11-10: plan creado a partir de `analysis.md` (36 tareas, 6 fases). Incorpora el requisito de tres runtimes, la retirada de Kwipu y Graphiti, la partición descartada y la evaluación de `training-data-services`.
- 2026-11-10: el usuario decide las cinco pendientes: marco retirado (T-10), exportación condicionada a T-31 (T-32), `lite` fusionado con `subagentes` (T-33), retro opcional en la vía rápida (T-34), fusiones (T-35). El plan sigue en `borrador` y sin autorizar. El modo único pasa a «fuera de alcance». T-33 sube a 5 h. Corregidas las líneas `Runtimes` de T-30, T-33 y T-34, que se habían descuadrado.
- 2026-11-10: revisión de huecos (37 tareas): T-08 dividida en código y documentación, alcance real de la retirada medido (137 ficheros), `test_graphiti_security.py` dividido en vez de borrado, `Archivos` de todas las tareas comprobados, 4.2 acotado a 4 shells, 4.12 retirado, supuestos de runtimes convertidos en verificaciones manuales M-A…M-F, `.claude/knowledge-services/taxonomy.json` fuera de T-08, ledger a 80 KB.
