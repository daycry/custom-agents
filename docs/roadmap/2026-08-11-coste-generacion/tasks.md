---
generacion:
  inicio: 2026-08-11T12:45:00Z
  fin: 2026-08-11T13:40:00Z
  fuente: estimado          # retroactivo: el artefacto se generó ANTES de desplegar usage-meter
  tokens_reales: null       # estimación a juicio: ~90k facturables
  eur: null                 # precioTokens sin verificar (rates-verify)
  horas_ia: 0.3
  duracion: 18m
  ratio_usado: 300000       # default no calibrado
---

# Checklist de Tareas — Coste real de generación (usage-meter) + calibración tokens→horas

| | |
|---|---|
| **Estado** | completado |
| **Fecha** | 2026-08-11 |
| **Plan** | [`improvement-plan.md`](./improvement-plan.md) |

> **⚠️ Ledger canónico de progreso.** Este fichero es la **fuente única de verdad** del avance del plan. **Cualquier** implementador —el agente `implementer`, el chat principal, o un orquestador externo (p. ej. *superpowers SDD*)— **debe** marcar aquí cada tarea (checkbox + estado) al completarla y actualizar el resumen. Los ledgers propios de otras herramientas son **espejo**, no fuente.

---

## Resumen de progreso

| Fase | Completadas | Total | Progreso | H. humanas (real/est) | H. IA ejec. (real/est) | Supervisión (real/est) | Tokens (real/est) |
|------|------------|-------|----------|-----------------------|------------------------|------------------------|-------------------|
| Fase 1 — Núcleo de medición | 3 | 3 | 100% | 0 / 5,5h | 0 / 1,75h | 0 / 0,45h | 0 / 555k |
| Fase 2 — Contrato del dato e integración | 2 | 2 | 100% | 0 / 3,0h | 0 / 1,0h | 0 / 0,25h | 0 / 325k |
| Fase 3 — Visibilidad y calibración | 2 | 2 | 100% | 0 / 3,5h | 0 / 1,15h | 0 / 0,3h | 0 / 375k |
| Fase 4 — Extrapolación y cierre | 3 | 3 | 100% | 0 / 4,75h | 0 / 1,45h | 0 / 0,4h | 0 / 515k |
| **TOTAL** | **10** | **10** | **100%** | **0 / 16,75h** | **0 / 5,35h** | **0 / 1,4h** | **0 / 1.770k** |

> **Horas → Jira.** El worklog que imputa `jira-sync` al completar cada tarea es **Tiempo IA (ejec.) + Supervisión** (real; o estimación si no hay real), topado a la jornada configurada. Ver `skills/jira-sync/SKILL.md`.
>
> Horas heredadas de [`evaluation.md`](./evaluation.md) (C-01…C-08, 16,0 h base) + delta de cierre declarado en el plan (T-10, +0,75 h base).

---

## Fase 1 — Núcleo de medición

**Estado**: completado · **Estimado**: 5,5h · **Real**: — · **Coste est.**: ~287 € · **Tokens est.**: 555k

### T-01 — Verificación empírica del formato JSONL (C-01, condición del go)

- **Descripción**: Leer transcripciones reales del entorno (`~/.claude/projects/<proyecto>/*.jsonl`): confirmar los nombres exactos de los campos de `usage` (input, output, creación de caché, lectura de caché), la codificación de la carpeta de proyecto, y cómo se distinguen las sidechains de subagentes. Documentar el hallazgo en una nota breve dentro del kit (base del parser de T-02). Si algún campo no existe tal como se asumió, ajustar el diseño ANTES de escribir código.
- **Estado**: completado
- **Tiempo humano**: est. 0,5h · real —
- **Tiempo IA (ejec.)**: est. 0,2h · real —
- **Supervisión**: est. 0,05h (≈25 % IA) · real —
- **Previsión IA**: 40k in / 6k out tok · ~26 €
- **Dependencias**: ninguna
- **Archivos**: `agent-kits/shared/usage-meter-notes.md` (nota de formato, temporal o embebida como docstring en T-02)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] Campos de `usage` confirmados contra al menos una transcripción real (con caché y sin ella)
- [x] Codificación de la carpeta de proyecto y detección de sidechains documentadas
- [x] Cualquier divergencia con la spec anotada y resuelta antes de T-02

**Subtareas**
- [x] Localizar y leer una transcripción real del entorno actual
- [x] Contrastar campos asumidos vs reales; anotar diferencias
- [x] Redactar la nota de formato para el parser

**Notas**: es la condición del veredicto go de la evaluación; barata y elimina el mayor riesgo.

### T-02 — `usage-meter.py`: start/close/status + tests (C-01)

- **Descripción**: Script determinista en `agent-kits/shared/`: `start --artefacto <ruta>` (marcador: timestamp + posición por transcripción en `.claude/usage-state.json`), `close --artefacto <ruta>` (suma `usage` de mensajes nuevos en la ventana, sidechains incluidas; emite JSON con `inicio`, `fin`, `tokens_reales` desglosado, `eur`, `horas_ia`, `ratio_usado`, `fuente`), `status` (marcadores huérfanos). Conversión € con `rates.json` (regla de fiabilidad vigente) y horas con ratio de `CALIBRATION.md` > default. `--transcript-dir` inyectable. Degradación a `fuente: estimado` sin bloquear NUNCA. Tests pytest con fixtures JSONL sintéticas.
- **Estado**: completado
- **Tiempo humano**: est. 4,0h · real —
- **Tiempo IA (ejec.)**: est. 1,2h · real —
- **Supervisión**: est. 0,3h (≈25 % IA) · real —
- **Previsión IA**: 340k in / 64k out tok · ~209 €
- **Dependencias**: T-01
- **Archivos**: `agent-kits/shared/usage-meter.py` (nuevo), `agent-kits/shared/test_usage_meter.py` (nuevo)
- **Cubre (tests)**: suma por ventana · sidechains · exclusión pre-marcador · degradación (fichero ausente, JSON corrupto, `usage` incompleto) · € fiable/no fiable · ratio CALIBRATION vs default · idempotencia del re-cierre · marcadores concurrentes

**Criterios de aceptación**
- [x] `close` suma exactamente el `usage` de los mensajes posteriores al marcador (fixtures), sidechains incluidas
- [x] Transcripción ausente/corrupta → `fuente: estimado` + aviso, exit code 0 (no bloquea)
- [x] € solo con precios fiables (`>0` y `verificadoEl` < 90 días); si no, `eur: null` + marca `⚠️ verificar`
- [x] `horas_ia = tokens_facturables ÷ ratio`; precedencia CALIBRATION.md > default, `ratio_usado` en la salida
- [x] Re-`close` del mismo artefacto sustituye (no suma); marcadores independientes por ruta
- [x] `pytest` en verde; sin rutas hardcodeadas (`--transcript-dir` + autodetección)

**Subtareas**
- [x] Marcadores y estado (`usage-state.json`)
- [x] Parser incremental por offset + agregación de sidechains
- [x] Conversiones (€, horas) con precedencias
- [x] Degradaciones y `status`
- [x] Fixtures y tests

**Notas**: núcleo de la iniciativa; patrón `worklog.py`/`qa-gate.py` (cálculo en script, no en prosa).

### T-03 — Helper de formato humano `fmt` (C-08)

- **Descripción**: Subcomando `usage-meter.py fmt <horas>` (y función importable) que convierte horas decimales al estilo Jira compacto `XhYm`: `0,53` → `32m` · `1,25` → `1h 15m` · `18,0` → `18h` · `1,53` → `1h 32m`. Omite la parte a cero; redondeo al minuto; acepta coma y punto decimal. Tests de bordes.
- **Estado**: completado
- **Tiempo humano**: est. 1,0h · real —
- **Tiempo IA (ejec.)**: est. 0,35h · real —
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 90k in / 15k out tok · ~52 €
- **Dependencias**: T-02 (vive en el mismo script)
- **Archivos**: `agent-kits/shared/usage-meter.py`, `agent-kits/shared/test_usage_meter.py`
- **Cubre (tests)**: `0→0m` · `<1 min` · horas exactas (`18→18h`) · mixtos (`1,53→1h 32m`) · coma/punto decimal

**Criterios de aceptación**
- [x] Formato exacto confirmado por el usuario: `1h 32m`, `34m`, `1h` (sin parte a cero, sin espacios entre número y unidad)
- [x] Redondeo al minuto documentado y testeado
- [x] Función única reutilizable — ningún otro artefacto reimplementa el formato a mano

**Subtareas**
- [x] Implementar `fmt` + función
- [x] Tests de bordes

**Notas**: pedido explícito del usuario ("0,53h no queda claro"); quick win visible en todas partes.

---

## Fase 2 — Contrato del dato e integración del ciclo

**Estado**: completado · **Estimado**: 3,0h · **Real**: — · **Coste est.**: ~157 € · **Tokens est.**: 325k

### T-04 — Bloque `generacion:` en las plantillas de artefactos (C-02)

- **Descripción**: Añadir a las plantillas de spec/evaluation (evaluator) y plan/tasks (planner) y a la sección del `tasks.md` ligero de vía rápida el bloque de frontmatter `generacion:` con `inicio`, `fin`, `tokens_reales` (desglosado in/out/caché), `eur`, `horas_ia`, `duracion` (legible, formato `XhYm` de T-03), `ratio_usado`, `fuente: medido|estimado`. Artefactos legacy sin bloque siguen siendo válidos (el lint no lo exige).
- **Estado**: completado
- **Tiempo humano**: est. 1,0h · real —
- **Tiempo IA (ejec.)**: est. 0,35h · real —
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 100k in / 15k out tok · ~52 €
- **Dependencias**: T-02, T-03
- **Archivos**: `agent-kits/evaluator/templates/spec.md`, `agent-kits/evaluator/templates/evaluation.md`, `agent-kits/planner/templates/improvement-plan.md`, `agent-kits/planner/templates/tasks.md`, `commands/dev-cycle.md` (tasks ligero)
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] Las plantillas llevan el bloque con ejemplo YAML válido y comentario de semántica (fechas = contexto; tokens = medida; horas = derivadas)
- [x] `duracion` usa el helper de T-03 (`XhYm`)
- [x] `ledger-lint.py` no marca error en artefactos sin bloque (legacy válido)

**Subtareas**
- [x] Bloque + ejemplo en cada plantilla
- [x] Nota de semántica junto al bloque

**Notas**: define el contrato del dato; sin esto no hay integración.

### T-05 — Arranque/cierre del meter en el ciclo (C-03)

- **Descripción**: Prosa en `agents/analyst.md`, `agents/evaluator.md`, `agents/planner.md` y `commands/dev-cycle.md` (vía rápida): ejecutar `usage-meter.py start` al abrir el artefacto propio y `close` al cerrarlo, volcando el JSON al bloque `generacion:` del frontmatter. Regla explícita "cerrar antes de abrir el siguiente" (el solape reparte mal el coste). Re-cierre actualiza sin duplicar. Resolución del script vía patrón `SHAREDKIT` existente.
- **Estado**: completado
- **Tiempo humano**: est. 2,0h · real —
- **Tiempo IA (ejec.)**: est. 0,65h · real —
- **Supervisión**: est. 0,15h (≈25 % IA) · real —
- **Previsión IA**: 180k in / 30k out tok · ~105 €
- **Dependencias**: T-04
- **Archivos**: `agents/analyst.md`, `agents/evaluator.md`, `agents/planner.md`, `commands/dev-cycle.md`
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] Los tres agentes del ciclo y la vía rápida arrancan y cierran el meter en los puntos correctos (abrir artefacto / darlo por terminado)
- [x] El bloque `generacion:` se escribe con el JSON del `close` (no valores inventados por el agente)
- [x] Si el meter degrada (`fuente: estimado`), el agente lo anota y CONTINÚA (nunca se bloquea el ciclo)
- [x] Regla "cerrar antes de abrir" presente en la prosa de los orquestadores (`/pm-cycle`, `/dev-cycle`)

**Subtareas**
- [x] Prosa por agente (patrón DoD existente: añadir al "ANTES DE CERRAR")
- [x] Vía rápida: medir el tasks ligero
- [x] Regla de no-solape en los orquestadores

**Notas**: con esto, todo artefacto nuevo nace medido.

---

## Fase 3 — Visibilidad y calibración

**Estado**: completado · **Estimado**: 3,5h · **Real**: — · **Coste est.**: ~184 € · **Tokens est.**: 375k

### T-06 — Coste de proceso en `/roadmap-metrics` (C-04)

- **Descripción**: `roadmap-dashboard` lee el bloque `generacion:` de los artefactos de cada iniciativa y añade al informe de métricas una sección **"Coste de proceso"** (tokens/€/duración de producir spec+eval+plan+tasks) separada del coste de implementación, con total de cartera. Iniciativas sin bloque → "sin datos" (nunca 0 inventado). Duraciones en formato `XhYm`.
- **Estado**: completado
- **Tiempo humano**: est. 2,0h · real —
- **Tiempo IA (ejec.)**: est. 0,65h · real —
- **Supervisión**: est. 0,15h (≈25 % IA) · real —
- **Previsión IA**: 180k in / 30k out tok · ~105 €
- **Dependencias**: T-04 (formato del bloque; probable con bloques a mano, sin esperar a T-05)
- **Archivos**: `skills/roadmap-dashboard/` (SKILL/script según reparto actual), `commands/roadmap-metrics.md`
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] El informe muestra proceso e implementación como conceptos separados, con total de cartera
- [x] "sin datos" para artefactos sin bloque; jamás se computa 0 € como si fuera medido
- [x] Duraciones presentadas con el helper `XhYm`

**Subtareas**
- [x] Parser del bloque en el escaneo del dashboard
- [x] Sección nueva en la salida `--metrics-md`
- [x] Prosa del command

**Notas**: aquí se ve el valor: el overhead del ciclo por iniciativa, visible.

### T-07 — Ratio real tokens→hora en `/retro` → `CALIBRATION.md` (C-05)

- **Descripción**: `/retro` calcula el ratio real de la iniciativa cerrada (tokens medidos ÷ horas reales validadas) y lo escribe como columna nueva en `docs/roadmap/CALIBRATION.md` (formato aún sin estrenar: esta tarea define la columna y el nº de muestras). Prosa del evaluator: usar la mediana del histórico como ratio; sin histórico, default de `estimation-defaults.md`.
- **Estado**: completado
- **Tiempo humano**: est. 1,5h · real —
- **Tiempo IA (ejec.)**: est. 0,5h · real —
- **Supervisión**: est. 0,15h (≈25 % IA) · real —
- **Previsión IA**: 140k in / 25k out tok · ~79 €
- **Dependencias**: T-04 (necesita bloques medidos que leer)
- **Archivos**: `commands/retro.md`, `agents/evaluator.md` (lectura del ratio), formato de `docs/roadmap/CALIBRATION.md`
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] `/retro` escribe ratio + nº de muestras en `CALIBRATION.md`
- [x] El evaluator documenta la precedencia CALIBRATION (mediana) > default
- [x] Con <3 muestras, el ratio se marca "indicio, no ley" (regla ya usada en evaluaciones)

**Subtareas**
- [x] Cálculo y columna en `/retro`
- [x] Prosa de lectura en evaluator

**Notas**: cierra el bucle medir→calibrar→estimar.

---

## Fase 4 — Extrapolación a tareas y cierre

**Estado**: completado · **Estimado**: 4,75h · **Real**: — · **Coste est.**: ~248 € · **Tokens est.**: 515k

### T-08 — Medición por tarea: horas-IA medidas al worklog (C-06)

- **Descripción**: En `/dev-cycle` Modo B: marcador `usage-meter.py start --artefacto <slug>/T-XX` al arrancar cada tarea y `close` al completarla. Las horas-IA **medidas** (tokens × ratio) se escriben como "real" en la columna de `tasks.md` (con `fuente: medido`) y entran al flujo `worklog.py plan` existente (que ya prefiere real sobre estimado) — **sin tocar la aritmética** de jornada/banco. Los tokens del revisor NO van a la tarea: van al bloque de revisión ya trazado (`--attempt`/`[revisión]`, iniciativa jira-granularity). Re-cierre de tarea reabierta sustituye, no suma.
- **Estado**: completado
- **Tiempo humano**: est. 3,0h · real —
- **Tiempo IA (ejec.)**: est. 0,9h · real —
- **Supervisión**: est. 0,25h (≈25 % IA) · real —
- **Previsión IA**: 280k in / 50k out tok · ~157 €
- **Dependencias**: T-02, T-07 (ratio con el que derivar horas)
- **Archivos**: `commands/dev-cycle.md` (Modo B), `agent-kits/planner/templates/tasks.md` (columna real con fuente), `skills/jira-sync/SKILL.md` (de dónde sale la hora real)
- **Cubre (tests)**: los tests existentes de `worklog.py` siguen verdes (no se toca el script)

**Criterios de aceptación**
- [x] Cada `T-XX` completada en Modo B lleva horas-IA reales **medidas** en el ledger, marcadas `fuente: medido`
- [x] El worklog de Jira imputa IA medida + supervisión por ratio (aritmética de jornada/banco intacta; tests de `worklog.py` verdes)
- [x] Tokens del bucle de revisión → bloque `[revisión]`, no a la tarea (sin doble contabilidad)
- [x] Reabrir y re-cerrar una tarea sustituye su medición (idempotencia)

**Subtareas**
- [x] Marcadores por tarea en la prosa de Modo B
- [x] Columna real/fuente en la plantilla del ledger
- [x] Encaje con la imputación (prosa jira-sync)

**Notas**: la petición literal del usuario: "extrapolar al cálculo del tiempo de las tareas… lo más real posible".

### T-09 — Ratio default + documentación (C-07)

- **Descripción**: `estimation-defaults.md`: parámetro **ratio tokens→hora** (default declarado "no calibrado — ejecutar /retro cuanto antes") + precedencia CALIBRATION > default. Documentación: regla del meter en `docs/CONVENTIONS.md`, bucle medir→calibrar en `docs/FLOWS.md` (diagrama 6), `agent-kits/shared/README.md` (fila del script nuevo).
- **Estado**: completado
- **Tiempo humano**: est. 1,0h · real —
- **Tiempo IA (ejec.)**: est. 0,35h · real —
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 90k in / 15k out tok · ~52 €
- **Dependencias**: T-02…T-08 (documenta lo construido)
- **Archivos**: `agent-kits/shared/estimation-defaults.md`, `agent-kits/shared/README.md`, `docs/CONVENTIONS.md`, `docs/FLOWS.md`
- **Cubre (tests)**: —

**Criterios de aceptación**
- [x] Ratio default documentado con su semántica y su marca de no-calibrado
- [x] FLOWS diagrama 6 refleja el bucle medir→calibrar (usage-meter → CALIBRATION → evaluator)
- [x] README del kit shared lista `usage-meter.py` con una línea de propósito

**Subtareas**
- [x] Parámetro + precedencia en estimation-defaults
- [x] CONVENTIONS, FLOWS, README

**Notas**: —

### T-10 — E2E de juguete + actualización de índices (cierre, delta del plan)

- **Descripción**: Verificación end-to-end con una iniciativa de juguete: pasar el ciclo (o simularlo con marcadores reales sobre esta misma sesión), comprobar que los artefactos llevan `generacion:` con `tokens_reales > 0` y `fuente: medido`, que `/roadmap-metrics` agrega el coste de proceso y que el formato `XhYm` aparece en todo lo presentado. Actualizar `docs/roadmap/README.md` (fila de la iniciativa) y los enlaces spec↔eval↔plan.
- **Estado**: completado
- **Tiempo humano**: est. 0,75h · real —
- **Tiempo IA (ejec.)**: est. 0,3h · real —
- **Supervisión**: est. 0,1h (≈25 % IA) · real —
- **Previsión IA**: 70k in / 10k out tok · ~40 €
- **Dependencias**: T-01…T-09
- **Archivos**: `docs/roadmap/README.md`, artefactos de esta carpeta
- **Cubre (tests)**: E2E manual del criterio de éxito 1 del plan

**Criterios de aceptación**
- [x] E2E de juguete con `tokens_reales > 0` y `fuente: medido` en los artefactos generados
- [x] `/roadmap-metrics` muestra la sección de proceso con esta iniciativa
- [x] Índice del roadmap actualizado; enlaces cruzados al día

**Subtareas**
- [x] E2E de juguete
- [x] Índices y enlaces

**Notas**: delta de cierre no presupuestado en la evaluación (+0,75 h), declarado en el plan. **Evidencia del E2E (2026-08-11):** iniciativa de juguete con marcador real sobre la sesión → `close` devolvió `fuente: medido`, `tokens_reales: {entrada: 2, salida: 165, cache_creacion: 538, cache_lectura: 324081}` (705 facturables > 0), y `/roadmap-metrics` sobre esa carpeta mostró la fila `705 tok (1/1 docs con medida, medido)`. Los artefactos de ESTA iniciativa van marcados `fuente: estimado` (retroactivo: se generaron antes de desplegar el meter) — el "medido" del criterio se demuestra con el E2E, no con ellos.
