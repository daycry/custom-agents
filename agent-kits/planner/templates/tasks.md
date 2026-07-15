<!--
  TEMPLATE: tasks.md  · usado por el agente `planner`
  Sustituye todos los {{PLACEHOLDER}}. Una fase agrupa varias tareas; cada tarea lleva ID T-XX.
  Estados (plan, fase y tarea): borrador · en-progreso · en-revision · completado · cancelado
-->

# Checklist de Tareas — {{Título del plan}}

| | |
|---|---|
| **Estado** | borrador |
| **Fecha** | {{YYYY-MM-DD}} |
| **Plan** | [`improvement-plan.md`](./improvement-plan.md) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del plan. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador externo (p. ej. *superpowers SDD*)— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — {{nombre}} | 0 | {{N}} | 0% | 0 / {{X}}h | 0 / {{X}}h | 0 / {{X}}h | 0 / {{X}} |
| Fase 2 — {{nombre}} | 0 | {{N}} | 0% | 0 / {{X}}h | 0 / {{X}}h | 0 / {{X}}h | 0 / {{X}} |
| Fase N — {{nombre}} | 0 | {{N}} | 0% | 0 / {{X}}h | 0 / {{X}}h | 0 / {{X}}h | 0 / {{X}} |
| **TOTAL** | **0** | **{{N}}** | **0%** | **0 / {{X}}h** | **0 / {{X}}h** | **0 / {{X}}h** | **0 / {{X}}** |

> **Horas → Jira.** El worklog que imputa `jira-sync` al completar cada tarea es **Tiempo IA (ejec.) + Supervisión** (real; o estimación si no hay real), topado a la jornada configurada. Ver `skills/jira-sync/SKILL.md`.

---

## Fase 1 — {{nombre}}

**Estado**: borrador · **Estimado**: {{X}}h · **Real**: — · **Coste est.**: {{X}} € · **Tokens est.**: {{X}}

<!-- ============ BLOQUE DE TAREA (copia uno por cada tarea) ============ -->

### T-01 — {{Título de la tarea}}

- **Descripción**: {{Qué hay que hacer y por qué, en 1-3 frases.}}
- **Estado**: borrador
- **Tiempo humano**: est. {{0.5}}h · real —
- **Tiempo IA (ejec.)**: est. {{X}}h · real —
- **Supervisión**: est. {{X}}h (≈25 % IA) · real —
- **Previsión IA**: {{15k}} in / {{5k}} out tok · {{X}} €
- **Dependencias**: {{ninguna / T-00 / acceso a X}}
- **Archivos**: `{{ruta}}`, `{{ruta}}`
- **Cubre (tests)**: {{si es tarea de UI: E2E-0X / M-0X del `test-plan.md`; si no aplica: —}}

**Criterios de aceptación**
- [ ] {{Criterio verificable 1}}
- [ ] {{Criterio verificable 2}}

**Subtareas**
- [ ] {{Paso 1}}
- [ ] {{Paso 2}}

**Notas**: {{decisiones, enlaces o bloqueos relevantes — opcional}}

<!-- ==================================================================== -->

### T-02 — {{Título de la tarea}}

- **Descripción**: {{...}}
- **Estado**: borrador
- **Tiempo humano**: est. {{X}}h · real —
- **Tiempo IA (ejec.)**: est. {{X}}h · real —
- **Supervisión**: est. {{X}}h (≈25 % IA) · real —
- **Previsión IA**: {{X}} in / {{X}} out tok · {{X}} €
- **Dependencias**: {{T-01}}
- **Archivos**: `{{ruta}}`

**Criterios de aceptación**
- [ ] {{Criterio 1}}
- [ ] {{Criterio 2}}

**Subtareas**
- [ ] {{Paso 1}}
- [ ] {{Paso 2}}

**Notas**: {{...}}

---

## Fase 2 — {{nombre}}

**Estado**: borrador · **Estimado**: {{X}}h · **Real**: — · **Coste est.**: {{X}} € · **Tokens est.**: {{X}}

### T-03 — {{Título de la tarea}}

- **Descripción**: {{...}}
- **Estado**: borrador
- **Tiempo humano**: est. {{X}}h · real —
- **Tiempo IA (ejec.)**: est. {{X}}h · real —
- **Supervisión**: est. {{X}}h (≈25 % IA) · real —
- **Previsión IA**: {{X}} in / {{X}} out tok · {{X}} €
- **Dependencias**: {{...}}
- **Archivos**: `{{ruta}}`

**Criterios de aceptación**
- [ ] {{Criterio 1}}

**Subtareas**
- [ ] {{Paso 1}}

**Notas**: {{...}}

---

## Fase N — Testing y validación

**Estado**: borrador · **Estimado**: {{X}}h · **Real**: — · **Coste est.**: {{X}} € · **Tokens est.**: {{X}}

### T-NN — {{Título}}

- **Descripción**: {{...}}
- **Estado**: borrador
- **Tiempo humano**: est. {{X}}h · real —
- **Tiempo IA (ejec.)**: est. {{X}}h · real —
- **Supervisión**: est. {{X}}h (≈25 % IA) · real —
- **Previsión IA**: {{X}} in / {{X}} out tok · {{X}} €
- **Dependencias**: {{tareas previas}}
- **Archivos**: `{{ruta}}`

**Criterios de aceptación**
- [ ] {{Todos los tests pasan}}
- [ ] {{Cobertura ≥ {{X}}%}}

**Subtareas**
- [ ] {{...}}

**Notas**: {{...}}

---

## Notas de implementación

_A completar durante la ejecución. Registra decisiones, desvíos de la estimación y aprendizajes._
