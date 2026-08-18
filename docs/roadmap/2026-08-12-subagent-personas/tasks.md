---
generacion:               # vía rápida MEDIDA (usage-meter)
  inicio: 2026-08-12T20:57:41Z
  fin: 2026-08-12T21:07:02Z
  fuente: medido
  tokens_reales: { entrada: 1832, salida: 21132, cache_creacion: 42747, cache_lectura: 3925456 }
  eur: 2.55                  # verificado con rates-verify (Opus 4.8; incluye caché) el 2026-08-18
  horas_ia: 0.14
  duracion: 8m                 
  ratio_usado: 479326       # calibrado (mediana de CALIBRATION.md; re-derivado en la retro del 2026-08-18)
---

# Checklist de Tareas — subagent-personas (vía rápida: perfiles de dominio para el subagente fresco)

| | |
|---|---|
| **Estado** | completado |
| **Fecha** | 2026-08-12 |
| **Plan** | n/a — **vía rápida** sobre [`spec.md`](spec.md) (sin evaluación/plan; ledger ligero + revisión de dos lentes + verificación) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del plan. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador externo— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

> **Origen:** spec de backlog anotada durante sdd-hardening (C-08); implementada como vía rápida al estar sdd-hardening cerrada. Estimación gruesa de la spec: ~2,5 h base. Nota de medición: la ventana cubre la sesión principal; el consumo de los 2 subagentes de revisión puede no estar íntegro en la transcripción medida.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — Personas de dominio | 3 | 3 | 100% | 0 / 2,5h | 0,14 (medido) / 0,8h | 0 / 0,25h | 66k (medido) / 250k |
| **TOTAL** | **3** | **3** | **100%** | **0 / 2,5h** | **0,14 (medido) / 0,8h** | **0 / 0,25h** | **66k (medido) / 250k** |

---

## Fase 1 — Personas de dominio

**Estado**: completado · **Estimado**: 2,5h · **Real**: — · **Coste est.**: ~130 € · **Tokens est.**: 250k

### T-01 — Catálogo corto de personas (`agent-kits/shared/personas/`)

- **Descripción**: 6 perfiles de dominio como fragmentos de prompt (fuente única, kit shared, §3 de CONVENTIONS): `frontend`, `backend`, `db`, `devops`, `test`, `docs`. Cada persona ~10 líneas con estructura fija: qué priorizar, trampas típicas del dominio, calidad exigible y evidencia al reportar. Corto POR DISEÑO (alcance de la spec: sin catálogo estilo wshobson; personas por proyecto quedan fuera, posible v2 vía constitución).
- **Estado**: completado
- **Tipo**: docs
- **Tiempo humano**: est. 1,0h · real —
- **Tiempo IA (ejec.)**: est. 0,3h · real — (medido en la ventana global)
- **Supervisión**: est. 0,1h · real —
- **Archivos**: `agent-kits/shared/personas/*.md` (6), `agent-kits/shared/README.md`

**Criterios de aceptación**
- [x] 6 personas (dentro del rango 5-7 de la spec), cada una con las 4 secciones y sin errores técnicos (verificado por la revisión de dominio de lente B)
- [x] El catálogo completo lo fija mecánicamente un test (`test_catalogo_real_completo`: etiqueta documentada ↔ fichero existente y no vacío)

### T-02 — Inyección en el brief (`task-brief.py`, TDD)

- **Descripción**: `task-brief.py` lee el campo opcional `- **Tipo**:` del bloque de la tarea (case-insensitive; placeholders `{{…}}` = ausente; solo líneas fuera de bloques de código; validación `[a-z][a-z0-9-]*` que impide escapar del catálogo con `/` o `..`) y antepone la sección "## Persona de dominio (tipo: X)" a la tarea. Sin etiqueta → brief genérico idéntico al de sdd-hardening. Etiqueta sin persona en el catálogo o persona vacía → aviso a stderr + genérico (degradación, exit 0). Flag `--personas-dir` para tests.
- **Estado**: completado
- **Tipo**: test
- **Tiempo humano**: est. 1,0h · real —
- **Tiempo IA (ejec.)**: est. 0,4h · real — (medido en la ventana global)
- **Supervisión**: est. 0,1h · real —
- **Archivos**: `agent-kits/shared/task-brief.py`, `agent-kits/shared/test_task_brief.py`

**Criterios de aceptación**
- [x] TDD con evidencia — `RED: 6 tests de persona fallaron (SystemExit: --personas-dir desconocido; falta personas/*.md) · 2026-08-12` → GREEN 16/16; regresión de lente B con su propio rojo — `RED: test_tipo_dentro_de_fence_ignorado falló (persona db inyectada desde un fence de ejemplo) · 2026-08-12` → GREEN 17/17 (52 pytest en total)
- [x] Sin etiqueta → sin sección de persona (default intacto); etiqueta desconocida → aviso + genérico + exit 0
- [x] E2E real: ledger válido con `- **Tipo**: db` y lint ACTIVO → brief con la persona del catálogo real; traversal (`../`, `/`) bloqueado (verificado por lente B ejecutando)

### T-03 — Cableado en la cadena y documentación

- **Descripción**: campo `- **Tipo**:` opcional en la plantilla de tareas del planner (con instrucción de omitir la línea si no aplica); `agents/planner.md` — asignar tipo solo con dominio claro, sin forzarlo; `commands/dev-cycle.md` paso 1 del despacho — el brief incluye la persona; docs (`docs/agents/planner.md`, `agent-kits/shared/README.md`), CHANGELOG, spec → `implementada`, fila del roadmap actualizada.
- **Estado**: completado
- **Tipo**: docs
- **Tiempo humano**: est. 0,5h · real —
- **Tiempo IA (ejec.)**: est. 0,1h · real — (medido en la ventana global)
- **Supervisión**: est. 0,05h · real —
- **Archivos**: `agent-kits/planner/templates/tasks.md`, `agents/planner.md`, `commands/dev-cycle.md`, `docs/agents/planner.md`, `agent-kits/shared/README.md`, `CHANGELOG.md`, `docs/roadmap/README.md`, `docs/roadmap/2026-08-12-subagent-personas/spec.md`

**Criterios de aceptación**
- [x] planner ↔ dev-cycle ↔ task-brief ↔ plantilla describen el MISMO conjunto de etiquetas y el mismo default (verificado por lente A)
- [x] ledger-lint tolera el campo Tipo (verificado empíricamente); linter del plugin sin errores nuevos; 6 suites del repo + 52 pytest en verde
- [x] Revisión de dos lentes superada: 1 defecto real (Tipo dentro de fences) + 4 gaps de doc, corregidos y re-verificados
