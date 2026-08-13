---
generacion:               # misma medición que improvement-plan.md (una ventana cubre ambos)
  inicio: 2026-08-12T07:51:04Z
  fin: 2026-08-12T07:53:41Z
  fuente: medido
  tokens_reales: { entrada: 8, salida: 12820, cache_creacion: 13335, cache_lectura: 1581487 }
  eur: null                 # precioTokens sin verificar (rates-verify)
  horas_ia: 0.09
  duracion: 5m
  ratio_usado: 300000       # default no calibrado
---

# Checklist de Tareas — SDD hardening (constitución · drift · G/W/T · TDD/worktrees · debug-root-cause · observabilidad)

| | |
|---|---|
| **Estado** | completado |
| **Fecha** | 2026-08-12 |
| **Plan** | [`improvement-plan.md`](./improvement-plan.md) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del plan. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador externo (p. ej. *superpowers SDD*)— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — Gobernanza (constitución) | 2 | 2 | 100% | 0 / 2,5h | 0,11 (medido) / 0,8h | 0 / 0,2h | 34k (medido) / 235k |
| Fase 2 — Specs verificables (G/W/T + drift) | 3 | 3 | 100% | 0 / 5,0h | 0,09 (medido) / 1,6h | 0 / 0,4h | 28k (medido) / 485k |
| Fase 3 — Disciplina nativa | 4 | 4 | 100% | 0 / 6,0h | 0,05 (medido) / 1,9h | 0 / 0,5h | 16k (medido) / 560k |
| Fase 3-bis — Autosuficiencia | 2 | 2 | 100% | 0 / 4,0h | 0,08 (medido) / 1,25h | 0 / 0,3h | 23k (medido) / 375k |
| Fase 4 — Ecosistema y cierre | 2 | 2 | 100% | 0 / 1,75h | 0,07 (medido) / 0,65h | 0 / 0,15h | 22k (medido) / 180k |
| **TOTAL** | **13** | **13** | **100%** | **0 / 19,25h** | **0,40 (medido) / 6,2h** | **0 / 1,55h** | **123k (medido) / 1.835k** |

> **Horas → Jira.** El worklog que imputa `jira-sync` al completar cada tarea es **Tiempo IA (ejec.) + Supervisión** (real; o estimación si no hay real), topado a la jornada configurada.
>
> Horas heredadas de [`evaluation.md`](./evaluation.md) (C-01…C-06, 14,5 h base) + delta de cierre (T-11, +0,75 h base). Esta iniciativa se ejecuta en Modo B con **medición por tarea** (usage-meter): las horas-IA reales llegarán medidas.

---

## Fase 1 — Gobernanza (constitución)

**Estado**: completado · **Estimado**: 2,5h · **Real**: — · **Coste est.**: ~131 € · **Tokens est.**: 235k

### T-01 — Plantilla y fragmento de constitución (C-01)

- **Descripción**: Crear `agent-kits/shared/templates/CONSTITUTION.template.md` (secciones: principios de código · arquitectura fijada/vetada · convenciones del equipo · seguridad; con aviso de brevedad ~1-2 páginas) y el fragmento compartido `agent-kits/shared/constitution-check.md`: "si existe `docs/CONSTITUTION.md` en el proyecto, léela antes de trabajar, respétala y cítala cuando condicione una decisión; si no existe, continúa sin ella (opt-in)".
- **Estado**: completado
- **Tiempo humano**: est. 1,5h · real —
- **Tiempo IA (ejec.)**: est. 0,5h · real — (medido)
- **Supervisión**: est. 0,15h (≈25 % IA) · real —
- **Previsión IA**: 120k in / 20k out tok · ~79 €
- **Dependencias**: ninguna
- **Archivos**: `agent-kits/shared/templates/CONSTITUTION.template.md` (nuevo), `agent-kits/shared/constitution-check.md` (nuevo), `agent-kits/shared/README.md` (filas)

**Criterios de aceptación**
- [x] La plantilla cubre las 4 secciones con ejemplos y el aviso de brevedad
- [x] El fragmento define lectura opt-in sin bloqueo y la obligación de citar el principio aplicado
- [x] README del kit shared actualizado con ambas piezas

**Subtareas**
- [x] Plantilla
- [x] Fragmento
- [x] README

**Notas**: patrón de fuente única (como estimation-defaults/confluence-optin).

### T-02 — Integración: 6 agentes, lente A y /setup (C-01)

- **Descripción**: Referenciar `constitution-check.md` desde analyst, evaluator, planner, implementer, qa y documenter (patrón `SHAREDKIT` + fallback). `commands/setup.md`: paso opt-in "¿creamos la constitución del proyecto?" (guiado desde la plantilla, idempotente). `commands/dev-cycle.md`: la **lente A** añade la constitución (si existe) a sus entradas — un diff que viole un principio **explícito** es gap de corrección **citando la línea del fichero**; lo demás se descarta como estilo.
- **Estado**: completado
- **Tiempo humano**: est. 1,0h · real —
- **Tiempo IA (ejec.)**: est. 0,3h · real — (medido)
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 80k in / 15k out tok · ~52 €
- **Dependencias**: T-01
- **Archivos**: 6 `agents/*.md`, `commands/setup.md`, `commands/dev-cycle.md`

**Criterios de aceptación**
- [x] Los 6 agentes que escriben referencian el fragmento (con fallback si no está)
- [x] `/setup` ofrece crear la constitución una vez y respeta la decisión (opt-in persistente)
- [x] La lente A limita los gaps constitucionales a principios explícitos con cita de línea

**Subtareas**
- [x] Agentes
- [x] /setup
- [x] Lente A

**Notas**: la constitución sin enforcement es un póster; la lente A es la puerta.

---

## Fase 2 — Specs verificables (G/W/T + drift)

**Estado**: completado · **Estimado**: 5,0h · **Real**: — · **Coste est.**: ~271 € · **Tokens est.**: 485k

### T-03 — Variante Given/When/Then en criterios (C-03)

- **Descripción**: Plantilla de spec (`agent-kits/evaluator/templates/spec.md`): documentar la variante `- [ ] [GWT] Dado <estado>, Cuando <acción>, Entonces <resultado observable>` junto al checkbox libre actual (opcional, no obligatorio). `agents/analyst.md` y skill `discovery`: ofrecer G/W/T cuando el criterio describa comportamiento observable. `agents/qa.md`: los criterios `[GWT]` se traducen a bloques E2E con mapeo 1:1 (el ID del criterio viaja al test-plan).
- **Estado**: completado
- **Tiempo humano**: est. 1,25h · real —
- **Tiempo IA (ejec.)**: est. 0,4h · real — (medido)
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 110k in / 20k out tok · ~66 €
- **Dependencias**: ninguna
- **Archivos**: plantilla spec, `agents/analyst.md`, `skills/discovery/SKILL.md`, `agents/qa.md`

**Criterios de aceptación**
- [x] La plantilla muestra ambas variantes y cuándo usar cada una
- [x] analyst/discovery ofrecen G/W/T solo para comportamiento observable (no lo fuerzan)
- [x] qa documenta la traducción `[GWT]` → bloque E2E con mapeo 1:1

**Subtareas**
- [x] Plantilla
- [x] analyst + discovery
- [x] qa

**Notas**: aditivo; specs existentes intactas.

### T-04 — `coverage-check.py` reconoce criterios `[GWT]` (C-03)

- **Descripción**: Caso nuevo en `agent-kits/qa/coverage-check.py`: un criterio marcado `[GWT]` cuyo ID aparece en `test-plan.md` cuenta como cubierto; sin aparición, como no cubierto. Tests de regresión: los casos existentes siguen verdes.
- **Estado**: completado
- **Tiempo humano**: est. 0,75h · real —
- **Tiempo IA (ejec.)**: est. 0,25h · real — (medido)
- **Supervisión**: est. 0,05h (≈25 % IA) · real —
- **Previsión IA**: 60k in / 10k out tok · ~38 €
- **Dependencias**: T-03 (formato del marcador)
- **Archivos**: `agent-kits/qa/coverage-check.py`, sus tests
- **Cubre (tests)**: criterio `[GWT]` cubierto/no cubierto · regresión de casos existentes

**Criterios de aceptación**
- [x] Test nuevo verde con `[GWT]` cubierto y no cubierto
- [x] Suite existente de coverage-check sin cambios de resultado

**Subtareas**
- [x] Código
- [x] Tests

**Notas**: único código Python de la iniciativa junto a T-11.

### T-05 — `/spec-drift`: deriva spec↔código (C-02)

- **Descripción**: Nuevo `commands/spec-drift.md` (solo lectura): localizar specs `implementada` (todas o `$ARGUMENTS` slug); por cada una, subagente de contexto fresco (patrón lente A, lotes máx. 3 en paralelo, read-discipline) que verifica cada criterio de aceptación contra el código ACTUAL → veredicto `vigente ✓ / derivado ✗ / no verificable` con evidencia fichero:línea. Salida: `docs/roadmap/DRIFT.md` (fecha + tabla por spec/criterio) + resumen conversacional + oferta de `/pm-cycle` para lo derivado. Nunca toca código. Fila en docs/README y FLOWS diagrama 6.
- **Estado**: completado
- **Tiempo humano**: est. 3,0h · real —
- **Tiempo IA (ejec.)**: est. 0,95h · real — (medido)
- **Supervisión**: est. 0,25h (≈25 % IA) · real —
- **Previsión IA**: 240k in / 45k out tok · ~156 €
- **Dependencias**: T-03 (los criterios G/W/T se verifican mejor); usable sin ella
- **Archivos**: `commands/spec-drift.md` (nuevo), formato `docs/roadmap/DRIFT.md`, `docs/README.md`, `docs/FLOWS.md`

**Criterios de aceptación**
- [x] Sin specs `implementada` lo dice y termina (no inventa)
- [x] Veredicto por criterio con evidencia; `no verificable` obligatorio cuando no la hay
- [x] DRIFT.md agregado + resumen + oferta de `/pm-cycle`; cero escrituras fuera de DRIFT.md
- [x] Lotes máx. 3 subagentes; filtro por slug funciona

**Subtareas**
- [x] Command
- [x] Formato DRIFT.md
- [x] Índices/FLOWS

**Notas**: es el `/speckit.analyze` del plugin; informar → `/pm-cycle`, nunca parchear.

---

## Fase 3 — Disciplina nativa (debugging + TDD/worktrees)

**Estado**: completado · **Estimado**: 6,0h · **Real**: — · **Coste est.**: ~317 € · **Tokens est.**: 560k

### T-06 — Skill `debug-root-cause` + gancho al 3.er rojo (C-05)

- **Descripción**: Nueva `skills/debug-root-cause/SKILL.md`: método de 4 fases con evidencia obligatoria por fase — (1) reproducción mínima, (2) aislamiento de la causa con evidencia, (3) hipótesis formulada y PROBADA, (4) fix + test de regresión. Prohibido cambiar código sin hipótesis probada. `commands/dev-cycle.md`: al 3.er rojo del bucle qa→implementer, UNA pasada de la skill ANTES de parar; la pregunta al usuario llega con el diagnóstico (o con lo descartado si tampoco concluye). Invocable a demanda. Solo Modo B (en Modo A, superpowers trae systematic-debugging).
- **Estado**: completado
- **Tiempo humano**: est. 2,5h · real —
- **Tiempo IA (ejec.)**: est. 0,8h · real — (medido)
- **Supervisión**: est. 0,2h (≈25 % IA) · real —
- **Previsión IA**: 200k in / 40k out tok · ~131 €
- **Dependencias**: ninguna
- **Archivos**: `skills/debug-root-cause/SKILL.md` (nuevo), `commands/dev-cycle.md` (bucle qa), `docs/README.md`

**Criterios de aceptación**
- [x] Las 4 fases con evidencia obligatoria y la prohibición de arreglar a ciegas
- [x] El gancho del 3.er rojo ejecuta UNA pasada y presenta diagnóstico + pregunta (no alarga el bucle indefinidamente)
- [x] Regla "solo Modo B" explícita; `lint_plugin.py` verde con la skill nueva

**Subtareas**
- [x] SKILL.md
- [x] Gancho en dev-cycle
- [x] Índice + lint

**Notas**: convierte "parar y preguntar" en "diagnóstico con evidencia y luego preguntar".

### T-07 — Config `.claude/dev.json` + /setup (C-04)

- **Descripción**: Config nueva `{"tdd": false, "worktree": false}` (defaults off). `/setup` la pregunta en el onboarding (idempotente); `docs/CONVENTIONS.md` regla 9 la documenta. Valores raros/corruptos → defaults + aviso.
- **Estado**: completado
- **Tiempo humano**: est. 0,75h · real —
- **Tiempo IA (ejec.)**: est. 0,25h · real — (medido)
- **Supervisión**: est. 0,05h (≈25 % IA) · real —
- **Previsión IA**: 60k in / 10k out tok · ~38 €
- **Dependencias**: ninguna
- **Archivos**: `commands/setup.md`, `docs/CONVENTIONS.md` (regla 9)

**Criterios de aceptación**
- [x] `/setup` crea/actualiza dev.json una vez y respeta la decisión
- [x] Sin dev.json todo funciona como hoy (defaults off)
- [x] Regla 9 de CONVENTIONS con el fichero nuevo

**Subtareas**
- [x] /setup
- [x] CONVENTIONS

**Notas**: mismo patrón que jira.json/confluence.json.

### T-08 — TDD opt-in en Modo B (C-04)

- **Descripción**: Con `tdd: true`, `agents/implementer.md` sigue RED-GREEN-REFACTOR por tarea: escribir el test que falla ANTES del código, registrar la **evidencia del rojo** en el ledger (una línea: `RED: <test> falló con <error> · <fecha>`), implementar hasta verde, refactorizar con tests verdes. Tareas sin código testeable (prosa/docs): se declara y se salta con nota. `commands/dev-cycle.md` lo referencia en Modo B. En Modo A no aplica.
- **Estado**: completado
- **Tiempo humano**: est. 1,75h · real —
- **Tiempo IA (ejec.)**: est. 0,55h · real — (medido)
- **Supervisión**: est. 0,15h (≈25 % IA) · real —
- **Previsión IA**: 140k in / 25k out tok · ~92 €
- **Dependencias**: T-07
- **Archivos**: `agents/implementer.md`, `commands/dev-cycle.md`

**Criterios de aceptación**
- [x] Con `tdd: true`, evidencia del ROJO en el ledger antes del verde (formato de una línea)
- [x] Tareas no testeables declaradas y saltadas con nota (sin teatro)
- [x] Con `tdd: false` o sin config, comportamiento actual intacto; regla "solo Modo B" explícita

**Subtareas**
- [x] implementer
- [x] dev-cycle

**Notas**: la evidencia del rojo es la vacuna contra el TDD-teatro.

### T-09 — Worktrees opt-in en Modo B (C-04)

- **Descripción**: Con `worktree: true`, el implementer arranca la iniciativa en un worktree aislado (`git worktree add ../<repo>-<slug> -b <rama>`), trabaja ahí y lo limpia al cerrar (merge/PR según flujo del repo). Sin git o sin soporte → aviso + rama normal (degradación). En Modo A no aplica (superpowers trae los suyos).
- **Estado**: completado
- **Tiempo humano**: est. 1,0h · real —
- **Tiempo IA (ejec.)**: est. 0,3h · real — (medido)
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 70k in / 15k out tok · ~56 €
- **Dependencias**: T-07
- **Archivos**: `agents/implementer.md`, `commands/dev-cycle.md`

**Criterios de aceptación**
- [x] Con `worktree: true`, creación/limpieza del worktree documentadas paso a paso
- [x] Degradación a rama normal con aviso si no hay soporte (nunca bloquea)
- [x] Regla "solo Modo B" explícita

**Subtareas**
- [x] implementer
- [x] dev-cycle

**Notas**: —

---

## Fase 3-bis — Autosuficiencia (nativa por defecto + subagentes)

**Estado**: completado · **Estimado**: 4,0h · **Real**: — · **Coste est.**: ~209 € · **Tokens est.**: 375k

### T-12 — Cadena nativa SIEMPRE por defecto (C-07)

- **Descripción**: Invertir la preferencia de `commands/dev-cycle.md`: la cadena nativa del plugin es EL modo por defecto en todos los casos (haya o no superpowers instalado). Superpowers solo se usa si el usuario lo pide explícitamente ("usa superpowers" o `--superpowers`); entonces aplican las reglas de coexistencia actuales (ledger canónico, transiciones del orquestador, no duplicar TDD/review). Actualizar `CLAUDE.md` (sección de orquestación), `docs/FLOWS.md` (diagrama 3) y el argument-hint del command. Documentar el cambio de comportamiento en CHANGELOG.
- **Estado**: completado
- **Tiempo humano**: est. 1,0h · real —
- **Tiempo IA (ejec.)**: est. 0,35h · real — (medido)
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 75k in / 15k out tok · ~52 €
- **Dependencias**: ninguna (conviene antes de T-13, que toca el mismo despacho)
- **Archivos**: `commands/dev-cycle.md`, `CLAUDE.md`, `docs/FLOWS.md`

**Criterios de aceptación**
- [x] Con superpowers instalado y SIN petición explícita, `/dev-cycle` usa la cadena nativa (no delega)
- [x] La petición explícita (frase o `--superpowers`) activa la delegación con las reglas de coexistencia intactas
- [x] CLAUDE.md, FLOWS diagrama 3 y CHANGELOG reflejan el nuevo defecto

**Subtareas**
- [x] dev-cycle
- [x] CLAUDE.md + FLOWS
- [x] CHANGELOG

**Notas**: decisión del usuario (2026-08-12): autosuficiencia — superpowers pasa a opcional real.

### T-13 — Desarrollo por subagentes de contexto fresco, opt-in, con las 4 mecánicas (C-08)

- **Descripción**: Con `subagentes: true` en `.claude/dev.json` (clave nueva, la pregunta `/setup` junto a tdd/worktree): en la cadena nativa, `/dev-cycle` despacha cada `T-XX` a un **subagente de contexto FRESCO** (Task tool). **Las 4 mecánicas adoptadas del ciclo de superpowers (confirmadas por el usuario):** (1) el brief lo genera el **script determinista `task-brief.py`** (nuevo, en `agent-kits/shared/`, con tests): extrae de `tasks.md` + `improvement-plan.md` la descripción de la tarea + criterios + sección de arquitectura + su fase + `docs/CONSTITUTION.md` si existe (se apoya en `ledger-lint.py`: ledger válido antes de despachar); (2) **brief-only**: el subagente trabaja con el brief y los ficheros que este referencia, sin explorar el repo entero; (3) el subagente reporta **estados ricos**: `DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED` — `NEEDS_CONTEXT` = re-despacho con el contexto pedido (prohibido inventar), `BLOCKED` = escala al orquestador, `DONE_WITH_CONCERNS` = las dudas viajan a la revisión; (4) en el bucle de corrección re-evalúa el **MISMO subagente revisor** (persistente, coherente con la traza `--attempt`) y los gaps se gradúan **`Critical / Important / Minor`** (Critical/Important obligan corrección; Minor se anota sin bloquear). El orquestador valida el retorno contra los criterios, marca el ledger y conserva TODAS las puertas (dos lentes, qa-gate, medición usage-meter por tarea). Re-despacho acotado a 1 (por gap o por contexto); segundo fallo → flujo normal (implementer en contexto principal) con aviso. Combinable con `tdd` y `worktree`.
- **Estado**: completado
- **Tiempo humano**: est. 3,0h · real —
- **Tiempo IA (ejec.)**: est. 0,9h · real — (medido)
- **Supervisión**: est. 0,2h (≈25 % IA) · real —
- **Previsión IA**: 240k in / 45k out tok · ~157 €
- **Dependencias**: T-07 (dev.json), T-12 (mismo despacho); se integra con T-02 (constitución) y T-08 (TDD)
- **Archivos**: `agent-kits/shared/task-brief.py` (nuevo) + tests, `commands/dev-cycle.md`, `commands/setup.md`, `docs/CONVENTIONS.md` (regla 9), `agents/implementer.md` (nota de convivencia)
- **Cubre (tests)**: `task-brief.py` — extracción correcta de tarea+criterios+arquitectura+fase · tarea inexistente → error claro · ledger inválido → se detiene con aviso · constitución ausente → brief sin ella

**Criterios de aceptación**
- [x] El brief lo produce `task-brief.py` (determinista, testeado), no prosa del orquestador
- [x] Con `subagentes: true`, cada tarea se despacha a un subagente fresco brief-only (ni historial de tareas anteriores ni chat completo ni exploración libre del repo)
- [x] Los 4 estados de retorno documentados con su ruta cada uno; `NEEDS_CONTEXT` re-despacha con el contexto pedido en vez de inventar
- [x] El revisor del bucle de corrección es persistente y gradúa `Critical / Important / Minor` (Critical/Important obligan; Minor se anota)
- [x] El orquestador valida contra los criterios ANTES de marcar completado; re-despacho acotado a 1; segundo fallo → flujo normal con aviso
- [x] Las puertas no cambian: dos lentes + qa-gate + medición por tarea funcionan igual
- [x] Con `subagentes: false` o sin config, comportamiento actual intacto

**Subtareas**
- [x] `task-brief.py` + tests
- [x] Despacho + estados + validación en dev-cycle
- [x] Revisor persistente con severidades
- [x] /setup + CONVENTIONS
- [x] Nota en implementer

**Notas**: la pieza estrella de superpowers (subagent-driven development), nativa y opt-in, con sus 4 mecánicas de ciclo. Los **perfiles de dominio** (persona frontend/backend/db/devops por tipo de tarea) quedan en el backlog como spec borrador `2026-08-12-subagent-personas` (decisión del usuario). El coste extra de tokens por tarea lo hará visible la medición de coste-generacion.

---

## Fase 4 — Ecosistema y cierre

**Estado**: completado · **Estimado**: 1,75h · **Real**: — · **Coste est.**: ~93 € · **Tokens est.**: 180k

### T-10 — `docs/observability.md` + enlaces (C-06)

- **Descripción**: Documentar el posicionamiento: **usage-meter** mide coste por artefacto/tarea con significado de negocio (€, horas imputables, calibración); un **monitor de sesión** externo (p. ej. hoangsonww/Claude-Code-Agent-Monitor) mide actividad en vivo (herramientas, subagentes, kanban) vía sus propios hooks. Coexistencia: nuestros hooks son PostToolUse no bloqueantes; no chocan. Cómo instalar ambos; qué usar para qué. Enlaces desde `docs/README.md` e `docs/INSTALL.md`.
- **Estado**: completado
- **Tiempo humano**: est. 1,0h · real —
- **Tiempo IA (ejec.)**: est. 0,35h · real — (medido)
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 85k in / 15k out tok · ~52 €
- **Dependencias**: ninguna
- **Archivos**: `docs/observability.md` (nuevo), `docs/README.md`, `docs/INSTALL.md`

**Criterios de aceptación**
- [x] Posicionamiento claro (coste vs actividad) sin vender el monitor como parte del plugin
- [x] Nota de coexistencia de hooks verificable
- [x] Enlazado desde README e INSTALL

**Subtareas**
- [x] Doc
- [x] Enlaces

**Notas**: documentar, no reinventar (preferencia del usuario).

### T-11 — E2E de juguete + índices + lint (cierre, delta del plan)

- **Descripción**: (a) E2E de `/spec-drift`: spec de juguete `implementada` con un criterio que el código cumple y otro que no → DRIFT.md marca ✓/✗ y lo no verificable como tal. (b) E2E de la puerta constitucional: con una CONSTITUTION.md de juguete que veta algo, la lente A produce el gap con cita. (c) `lint_plugin.py` + suites en verde. (d) Índices: fila en `docs/roadmap/README.md`, enlaces spec↔eval↔plan, CHANGELOG. Evidencias en Notas.
- **Estado**: completado
- **Tiempo humano**: est. 0,75h · real —
- **Tiempo IA (ejec.)**: est. 0,3h · real — (medido)
- **Supervisión**: est. 0,05h (≈25 % IA) · real —
- **Previsión IA**: 70k in / 10k out tok · ~40 €
- **Dependencias**: T-01…T-10
- **Archivos**: `docs/roadmap/README.md`, `CHANGELOG.md`, artefactos de esta carpeta
- **Cubre (tests)**: E2E de los criterios de éxito 1 y 2 del plan

**Criterios de aceptación**
- [x] E2E de drift y de puerta constitucional con evidencia pegada
- [x] Lint y suites en verde
- [x] Índices y enlaces al día

**Subtareas**
- [x] E2E drift
- [x] E2E constitución
- [x] Lint + índices

**Notas**: delta no presupuestado en la evaluación (+0,75 h), declarado en el plan. **Evidencias E2E (2026-08-12):** (a) *drift*: iniciativa de juguete `calc` con spec `implementada` → verificación real: `add(2,3)==5` (CA-01 **vigente ✓**, `calc.py:1-2`); `div(4,0)` lanza `ZeroDivisionError` (CA-02 **derivado ✗**, `calc.py:4-5`); criterio de proceso → **no verificable**; `DRIFT.md` generado con los tres veredictos correctos. (b) *puerta constitucional*: subagente lente A de contexto fresco sobre una constitución de juguete que veta estado global + un diff que introduce `CACHE_GLOBAL` → detectó el gap **citando la línea literal del principio** y confirmó explícitamente no inventar principios no escritos. (c) lint del plugin sin errores nuevos; `ledger-lint` 0 incoherencias (incluye fix del choque «Fase 3»/«Fase 3-bis», test de regresión 9/9); suites: coverage-check (nuevo) OK · dashboard OK · worklog OK · qa-gate OK · usage-meter + task-brief 41/41 en pytest.
