<!--
  TEMPLATE: TASKS.md  ·  usado por el agente `planner`
  Sustituye todos los {{PLACEHOLDER}}. Una fase agrupa varias tareas; cada tarea lleva ID T-XX.
  Estados (plan, fase y tarea): 📝 borrador · 🚧 en-progreso · 🔍 en-revision · ✅ completado · ❌ cancelado
-->

# Checklist de Tareas — {{Título del plan}}

| | |
|---|---|
| **Estado** | 📝 borrador |
| **Fecha** | {{YYYY-MM-DD}} |
| **Plan** | [`improvement-plan.md`](./improvement-plan.md) |

---

## 📊 Resumen de progreso

| Fase | Completadas | Total | Progreso | Horas (real/est) | Tokens (real/est) |
|------|------------|-------|----------|------------------|-------------------|
| Fase 1 — {{nombre}} | 0 | {{N}} | 0% | 0 / {{X}}h | 0 / {{X}} |
| Fase 2 — {{nombre}} | 0 | {{N}} | 0% | 0 / {{X}}h | 0 / {{X}} |
| Fase N — {{nombre}} | 0 | {{N}} | 0% | 0 / {{X}}h | 0 / {{X}} |
| **TOTAL** | **0** | **{{N}}** | **0%** | **0 / {{X}}h** | **0 / {{X}}** |

---

## 🏗️ Fase 1 — {{nombre}}

**Estado**: 📝 borrador · **Estimado**: {{X}}h · **Real**: — · **Coste est.**: {{X}} € · **Tokens est.**: {{X}}

<!-- ============ BLOQUE DE TAREA (copia uno por cada tarea) ============ -->

### T-01 — {{Título de la tarea}}

- **Descripción**: {{Qué hay que hacer y por qué, en 1-3 frases.}}
- **Estado**: 📝 borrador
- **Tiempo**: est. {{0.5}}h · real —
- **Previsión IA**: {{15k}} in / {{5k}} out tok · {{X}} €
- **Dependencias**: {{ninguna / T-00 / acceso a X}}
- **Archivos**: `{{ruta}}`, `{{ruta}}`

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
- **Estado**: 📝 borrador
- **Tiempo**: est. {{X}}h · real —
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

## ⚙️ Fase 2 — {{nombre}}

**Estado**: 📝 borrador · **Estimado**: {{X}}h · **Real**: — · **Coste est.**: {{X}} € · **Tokens est.**: {{X}}

### T-03 — {{Título de la tarea}}

- **Descripción**: {{...}}
- **Estado**: 📝 borrador
- **Tiempo**: est. {{X}}h · real —
- **Previsión IA**: {{X}} in / {{X}} out tok · {{X}} €
- **Dependencias**: {{...}}
- **Archivos**: `{{ruta}}`

**Criterios de aceptación**
- [ ] {{Criterio 1}}

**Subtareas**
- [ ] {{Paso 1}}

**Notas**: {{...}}

---

## 🧪 Fase N — Testing y validación

**Estado**: 📝 borrador · **Estimado**: {{X}}h · **Real**: — · **Coste est.**: {{X}} € · **Tokens est.**: {{X}}

### T-NN — {{Título}}

- **Descripción**: {{...}}
- **Estado**: 📝 borrador
- **Tiempo**: est. {{X}}h · real —
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

## 📝 Notas de implementación

_A completar durante la ejecución. Registra decisiones, desvíos de la estimación y aprendizajes._
