---
generacion:               # usage-meter.py close degradó (sin transcripciones del worktree C:/tpd): tokens/€ ESTIMADOS a juicio
  inicio: 2026-09-28T11:52:05Z
  fin: 2026-09-28T11:55:08Z
  fuente: estimado
  tokens_reales: { entrada: 40000, salida: 45000, cache_creacion: 150000, cache_lectura: 2500000 }   # estimado
  eur: 3.23               # estimado con precioTokens de rates.json (verificado 2026-08-18) × 0,92
  horas_ia: 0.49          # 235.000 tok facturables ÷ 479326
  duracion: 3m            # reloj medido por el meter (duracion_reloj); la redacción previa corrió en la ventana de la spec
  ratio_usado: 479326     # CALIBRATION.md (mediana de 5)
---

# 2026-09-28-project-dashboard

> Evaluación y presupuesto, **por entregas**, del dashboard multi-proyecto opcional de custom-agents (emisor opt-in en el plugin + dashboard aparte), para decidir go/no-go en la puerta de `/pm-cycle`.

| | |
|---|---|
| **Fecha** | 2026-09-28 |
| **Estado** | completado |
| **Prioridad global** | Media 🟡 |
| **Solicitante** | Daycry (usuario, vía `/pm-cycle`) |
| **Spec** | [`spec.md`](spec.md) |
| **Plan** | pendiente (handoff a `planner`, recomendado tras `architect`) |
| **Características evaluadas** | 8 (en 3 entregas) |

---

## 📊 Cuadro de mando

| Métrica | Total estimado | Confianza |
|--------|----------------|-----------|
| Esfuerzo humano | **172,8 h** (144 h base +20 %; horas humanas equivalentes) | Baja (horas humanas nunca validadas en el histórico) |
| Tiempo IA (ejecución, horas-equivalentes de tokens) | **177,6 h** (148 h base +20 %) — de ellas **134,4 h de revisión + corrección** (+ 44,4 h supervisión) | Baja |
| Tiempo IA en reloj (orientativo) | **~53 h** (≈ 30 % de las horas-equivalentes) | Baja |
| Coste | **8.640 €** de valoración humana · **3.285 €** de ciclo IA real previsto (1.065 € de tokens + 2.220 € de supervisión); no se suman | Baja (valoración) / Media en tokens |
| Tokens IA | **85,1 M** facturables (in 78,9 M / out 6,2 M) + lectura de caché aparte | Baja |
| Multiplicador productividad | **×0,78** en horas-equivalentes · **×1,77** en reloj | — |
| Características | **8** (E1: 3 · E2: 2 · E3: 3) | — |

| Entrega | H humanas (con margen) | H IA (con margen) | de ellas revisión | Tokens facturables | € tokens | € ciclo IA (tokens + supervisión) |
|---|---|---|---|---|---|---|
| **E1** emisor + backend + portada + kanbans | 81,6 h | 88,8 h | 68,4 h | 42,6 M | 533 € | 1.643 € |
| **E2** revisiones/reintentos + detalles | 50,4 h | 47,4 h | 34,8 h | 22,7 M | 284 € | 877 € |
| **E3** métricas + salud + MCP | 40,8 h | 41,4 h | 31,2 h | 19,8 M | 248 € | 765 € |
| **Total** | **172,8 h** | **177,6 h** | **134,4 h** | **85,1 M** | **1.065 €** | **3.285 €** |

---

## 🧭 Resumen ejecutivo

El usuario pide un dashboard **único y opcional** con el estado de todos los proyectos que usan el plugin: un emisor opt-in en el plugin (contrato JSON versionado, envío en las puertas de los orquestadores, cola local, sin red en hooks) y un componente aparte (API con token por proyecto, SQLite con historial, UI de kanban/detalle/métricas, MCP de consulta de solo lectura). Se presupuesta en tres entregas útiles por sí solas: **E1** ya da la visión de cartera (portada y kanbans), **E2** la trazabilidad de revisiones y reintentos, **E3** métricas, salud y MCP.

La cifra que manda es la de **revisión y corrección**: 134,4 h de las 177,6 h de IA. Así lo dice el histórico: en `training-data-services` se estimaron 11,9 h de IA y ya van **46,22 h medidas con 6 de 11 tareas** (×3,9), y casi todo son rondas fixN. Veredicto recomendado: **go con condiciones**. Primero `architect` (stack, ubicación del repo, granularidad del historial, ADR). Después, **go firme solo para E1** y reevaluar E2/E3 con la retro de E1. Tope de 3 intentos de revisión por entrega.

---

## 📥 Requerimientos recibidos

Mapa de la spec a las características evaluadas.

| ID | Característica | Requisito origen (ref.) | ¿Claro? |
|----|---------------|-------------------------|---------|
| C-01 | Emisor base: config, contrato v1, `dashboard-sync.py`, cola, `/setup`, `/doctor`, `/dashboard-sync`, puertas, interop, ADR | spec §Arquitectura (Emisor), §Alcance E1, CA-01..CA-04 | ✅ |
| C-02 | Backend: API con token por proyecto, SQLite con historial, seguridad v1, `docker-compose` | spec D-09..D-11, §Alcance E1, CA-06..CA-08 | ⚠️ ambiguo (stack, repo, granularidad y retención del historial) |
| C-03 | UI E1: portada + kanban de iniciativas + kanban de tareas | spec §Alcance E1, CA-09, CA-10 | ⚠️ ambiguo (stack de UI) |
| C-04 | Emisor E2: secciones de revisión por intento, gaps, rondas fixN, qa, retro, calibración (contrato v1.1) | spec §Alcance E2, §Supuestos (ledgers históricos) | ⚠️ ambiguo (formato de gaps y fixN no canónico) |
| C-05 | UI + backend E2: detalle de tarea (línea de tiempo), detalle de iniciativa, resultado final | spec §Alcance E2, CA-11 | ✅ |
| C-06 | Emisor E3: salud completa + piezas/MCP (solo nombres y tipos) | spec §Alcance E3, CA-05 | ✅ |
| C-07 | UI E3: salud de la instalación + métricas globales | spec §Alcance E3 | ✅ |
| C-08 | MCP de consulta de solo lectura en el dashboard | spec §Alcance E3, CA-12 | ✅ |

**Ambigüedades / información que falta:**

- **Stack** de backend y UI (D-12): lo decide `architect`. Cambia el coste de C-02/C-03/C-05/C-07 en ±30 %.
- **Dónde vive el dashboard** (D-09). Si es un repo aparte, su ledger, su revisión y su CI viven allí. `scope-check.py` y `guardrail-check.py` asumen un único repo, así que habría que llevar dos cadenas o ajustar el flujo. Es una incógnita de proceso, no de código.
- **Granularidad y retención del historial** (D-11): el presupuesto asume versionado por entidad con hash de contenido, no un snapshot completo por envío.
- **Texto de los gaps** (spec §Supuestos): se asume resumen truncado a 200 caracteres y redactado, con la evidencia como `fichero:línea`. Si el usuario no quiere texto, C-04 baja ~2 h.
- **Formato de los ledgers históricos**: las tablas de gaps varían (34 ledgers con `Corrección`, 21 con `Correccion`, 2 con columna `Lente` y otras 4 variantes; `grep` sobre `docs/roadmap/*/tasks.md`). Las rondas fixN solo existen como prosa (`- **Tiempo IA (fixN)**: real X h (medido; …)`) en `training-data-services`, sin patrón validado por `ledger-lint`.

---

## ✅ Datos necesarios para una evaluación completa

- [x] **Requerimientos** completos y sin ambigüedades (decididos con el usuario; ambigüedades de diseño delegadas a `architect`)
- [x] **Alcance** de cada característica acotado (qué entra y qué NO)
- [x] **Criterios de aceptación / éxito** por característica (CA-01..CA-12 + criterios libres)
- [ ] **Restricciones** (deadline, presupuesto): no declaradas
- [x] **Dependencias externas** identificadas (ninguna de terceros; Headroom solo referencia)
- [ ] **Contexto técnico** del dashboard (stack, repo): pendiente de `architect`
- [x] **Tarifa/hora y supuestos de coste** confirmados (`.claude/rates.json`)

---

## 💶 Supuestos económicos (ajustables)

**Coste = (horas × tarifa) + coste de tokens de IA.** Importes en **EUR**. Se presentan **dos costes que no se suman** (LES-007, «separa lo que mides de lo que vendes»). El de **valoración** son las horas humanas equivalentes × tarifa. El **real previsto del ciclo IA** son los tokens más la supervisión humana.

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | 50 €/h | `.claude/rates.json` `tarifaHora` |
| Modelo IA asumido | claude-opus-4-8 | `rates.json` `modeloIA` |
| Precio input | 4,60 € / 1M tokens (5 USD) | `rates.json`, verificado 2026-08-18 (41 días, fiable) |
| Precio output | 23,00 € / 1M tokens (25 USD) | ídem; escritura de caché 5,75 €/M, lectura 0,46 €/M |
| Tipo de cambio | 1 USD = 0,92 € | Supuesto fijo de `rates.json`, no verificado |
| Margen de contingencia | 20 % | `rates.json` `margenContingencia`; sobre horas base humanas e IA |
| Ratio de supervisión | 25 % de las horas IA | `rates.json` `ratioSupervision` (en el histórico la supervisión real medida es 0 h: cifra conservadora) |
| Ratio tokens→hora-IA | 479.326 tok/h | `CALIBRATION.md`, mediana de 5 muestras medidas |
| € por hora-IA | 6 €/h | Medido en las ventanas fixN de `training-data-services` (5,0-6,2 €/h, lectura de caché incluida: fix1 17,80 €/2,87 h · fix3 36,17 €/7,22 h · fix5 57,78 €/9,63 h) |
| Salida por hora-IA | ~35 k tok/h | Mismas ventanas (227,1 k/7,22 h · 272,8 k/9,63 h) |
| Reloj / hora-equivalente | ~30 % | Mismas ventanas (fix3 2 h 13 m para 7,22 h · fix5 2 h 47 m para 9,63 h) |

**Método de horas IA (calibrado):**

1. **Implementación** = 0,25 h-IA por hora humana base. Base: en el histórico, la implementación pura salió en torno a lo estimado (`knowledge-services` −63 %, `training-data-services` Fase 1 ≈ 0,4 h de implementación frente a 2,0 h estimadas). La desviación se fue a la revisión.
2. **Revisión + corrección, como línea propia** (LES-001, LES-009; aprendizaje 3 de `CALIBRATION.md`):
   - **×4 la implementación** en piezas con privacidad, red, cola o seguridad (C-01, C-02, C-04, C-06, C-08). Base: `installer-registro-real` (8,55 h de revisión sobre 7,28 h, 5 rondas), `session-end-durable-capture` (7 pasadas, 97 gaps), `knowledge-services` (11 rondas, 185 gaps), `training-data-services` (Fase 2: 34,45 h de fixN frente a 2,4 h estimadas).
   - **×2 la implementación** en UI (C-03, C-05, C-07), con menos superficie adversarial y la verificación en E2E de qa.
3. La cifra resultante (IA ≈ 1,03 × horas humanas base) cae en el rango de las tres últimas iniciativas con código: 0,8 (`session-end`), 1,17+ sin terminar (`training`) y 1,58 (`installer`).
4. **Escenario pesimista** (si repite el patrón de `training-data-services`, con revisión ×10): ~300 h-IA y ~1.800 € de tokens. Es la razón del tope de rondas y de la reevaluación tras E1.

**Coste de proceso (LES-008), aparte del total de la tabla:** spec y evaluación ≈ 0,9 h-IA y ~5,5 € (estimado a juicio: el meter degradó sin transcripciones, ver `generacion:` de ambos). `design.md` y plan ≈ 3 h-IA y ~18 € (estimado por analogía con `training-data-services`, que llevó `design.md`). Total ≈ **3,9 h-IA · ~24 €**.

---

## 🔍 Evaluación por característica

### C-01 — Emisor base (config, contrato v1, `dashboard-sync.py`, cola, setup/doctor, comando, puertas, interop, ADR)

- **Requisito origen**: spec §Arquitectura (Emisor), §Alcance E1, D-01..D-08, CA-01..CA-04
- **Descripción**: `.claude/dashboard.json` con token por variable de entorno, capacidad en `capabilities.py` (paso de `/setup` y fila de `/doctor` sin código específico), `dashboard-sync.py` determinista que recolecta con los lectores existentes (`build_dashboard.py --json`, `ledger-lint.py`, `progress-report.py --json`, `usage-meter.py`, resumen de `doctor.py --json`), valida contra un JSON Schema versionado, redacta con `redact.py`, envía por HTTP y encola en `outbox.py`. Añade el comando `/dashboard-sync`, una línea en las puertas de `/dev-cycle`, `/pm-cycle` y `/retro`, interop regenerada, docs ES/EN y el ADR de la etiqueta `project`.
- **Complejidad**: Alta (toca 3 orquestadores, 2 comandos, 1 capacidad, contrato y cola; mucha superficie de convenciones: bilingüe, interop, evals de activación del comando nuevo)
- **Esfuerzo**: 28,8 h humanas (24 h base) · IA 36,0 h (6,0 impl + 24,0 revisión, base 30 h) · confianza Media
- **Previsión IA**: 16,0 M in / 1,26 M out tok (17,3 M facturables) · 216 €
- **Coste**: valoración 28,8 h × 50 = **1.440 €** · ciclo IA 216 € + 9,0 h supervisión (450 €) = **666 €**
- **Impacto / áreas afectadas**: `agent-kits/shared/` (nuevo `dashboard-sync.py` + tests, `capabilities.py`, `doctor.py`), `commands/dev-cycle.md`, `commands/pm-cycle.md`, `commands/retro.md`, `commands/setup.md`, nuevo `commands/dashboard-sync.md`, `evals/cases/`, `interop/` (generado), `docs/knowledge/adr/`, `docs/` + `docs/en/`
- **Dependencias y prerequisitos**: contrato v1 cerrado con `architect` (lo consume C-02); `outbox.py` y `redact.py` ya existen
- **Riesgos**: `outbox.py` se diseñó para otra cola (knowledge). Reutilizarlo para una cola de envíos HTTP puede abrir estados intermedios sin dueño (LES-016). La red desde un orquestador tiene que respetar un tope de tiempo como el de `doctor.py` (`CAPACIDADES_PRESUPUESTO_S`) para no alargar el ciclo. Y colar un envío en un hook por comodidad rompería una regla dura.
- **Incógnitas / preguntas abiertas**: ¿el envío en la puerta es síncrono con timeout corto o siempre «encolar y drenar»?; nombre por defecto de la variable del token; número del ADR (la rama `training-data-services` ya cita ADR-019)

### C-02 — Backend del dashboard (API con token por proyecto, SQLite con historial, seguridad v1, docker-compose)

- **Requisito origen**: spec D-09..D-11, §Alcance E1, CA-06..CA-08
- **Descripción**: servicio con `POST` de recepción por proyecto (token de escritura guardado con hash), consulta con token de lectura, validación de `schema_version`, SQLite particionado por proyecto con historial por entidad (hash de contenido) y vista actual, alta explícita de proyectos, bind por defecto a `127.0.0.1` en el `docker-compose`, ejemplo de proxy inverso TLS, tests de API.
- **Complejidad**: Alta (seguridad, concurrencia de escrituras en SQLite, esquema de historial que E2 necesita)
- **Esfuerzo**: 26,4 h humanas (22 h base) · IA 33,0 h (5,5 impl + 22,0 revisión, base 27,5 h) · confianza Baja (stack sin decidir)
- **Previsión IA**: 14,7 M in / 1,16 M out tok (15,8 M facturables) · 198 €
- **Coste**: valoración **1.320 €** · ciclo IA 198 € + 8,25 h supervisión (413 €) = **611 €**
- **Impacto / áreas afectadas**: repo nuevo (recomendado `custom-agents-dashboard`): API, capa de datos, `docker-compose.yml`, ejemplo de proxy, CI propia
- **Dependencias y prerequisitos**: `architect` (stack, repo, esquema de historial y retención); contrato de C-01
- **Riesgos**: un esquema de historial mal elegido en E1 obliga a migrar en E2. Si se guarda el snapshot completo por envío, el volumen crece con la frecuencia: 50 proyectos × 30 envíos/día × 300 KB ≈ 450 MB/día. La exposición externa sin TLS sería una mala configuración accidental. Y es repo nuevo sin CI.
- **Incógnitas / preguntas abiertas**: retención; rotación de tokens; ¿multi-escritor concurrente (WAL) o cola de ingesta?

### C-03 — UI E1: portada + kanban de iniciativas + kanban de tareas

- **Requisito origen**: spec §Alcance E1, CA-09, CA-10
- **Descripción**: portada con tarjeta por proyecto (iniciativas abiertas, % tareas, en revisión/bloqueadas, coste del mes, salud resumida, último envío), filtros y orden «necesita atención»; kanban de iniciativas (idea → spec aprobada → evaluada go → en implementación → en revisión → cerrada); kanban de tareas por iniciativa con carriles por fase y `cancelado` plegado. **Ajuste respecto a la propuesta:** el kanban de iniciativas pasa a E1 (solo necesita los estados de spec/evaluación/plan que ya emite C-01; ~3 h de las 22 h).
- **Complejidad**: Media
- **Esfuerzo**: 26,4 h humanas (22 h base) · IA 19,8 h (5,5 impl + 11,0 revisión, base 16,5 h) · confianza Baja (stack sin decidir)
- **Previsión IA**: 8,8 M in / 0,69 M out tok (9,5 M facturables) · 119 €
- **Coste**: valoración **1.320 €** · ciclo IA 119 € + 4,95 h supervisión (248 €) = **367 €**
- **Impacto / áreas afectadas**: UI del repo del dashboard; E2E Playwright en local (qa)
- **Dependencias y prerequisitos**: API de lectura de C-02
- **Riesgos**: el orden «necesita atención» necesita una regla explícita y testeada, no una heurística de la UI. La correspondencia estados de artefacto → columnas del kanban de iniciativas tiene casos raros: vías rápidas sin spec, `cancelado`, `obsoleta`.
- **Incógnitas / preguntas abiertas**: fórmula exacta de «necesita atención»; en E1 la tarjeta no tiene aún gaps ni intento (llegan en E2)

### C-04 — Emisor E2: revisiones por intento, gaps, rondas fixN, qa, retro, calibración (contrato v1.1)

- **Requisito origen**: spec §Alcance E2, §Supuestos (ledgers históricos)
- **Descripción**: primero **formalizar en `ledger-lint.py`** el formato canónico de la tabla de gaps y de la línea `Tiempo IA (fixN)`, con un patrón exportado como `REVISION_HDR_PATTERN`. Después extraer, reutilizando `secciones_revision`/`filas_pendientes_de_tarea` de `jira-flow.py`, las secciones por intento (lentes, gaps con grado/estado/evidencia), las rondas fixN con coste, el veredicto de `qa-gate`, `retro.md` y la fila de `CALIBRATION.md`. Lo que no case sale como `no-verificable`.
- **Complejidad**: Alta (parser tolerante sobre ~57 ledgers con al menos 7 variantes de cabecera de gaps; formalizar un formato que hoy es prosa)
- **Esfuerzo**: 19,2 h humanas (16 h base) · IA 24,0 h (4,0 impl + 16,0 revisión, base 20 h) · confianza Baja
- **Previsión IA**: 10,7 M in / 0,84 M out tok (11,5 M facturables) · 144 €
- **Coste**: valoración **960 €** · ciclo IA 144 € + 6,0 h supervisión (300 €) = **444 €**
- **Impacto / áreas afectadas**: `agent-kits/shared/ledger-lint.py`, `dashboard-sync.py`, `skills/jira-sync/scripts/jira-flow.py` (solo si hay que exponer el parser), plantilla de ledger del planner y del implementer (línea fixN canónica), esquema del contrato
- **Dependencias y prerequisitos**: C-01; cruza con `feature/training-data-services` (sin mergear, es el ledger con más fixN). Conviene esperar a su merge para tener el caso real en `master`.
- **Riesgos**: el texto de un gap puede citar código. Hay que truncarlo, redactarlo y enviar la evidencia solo como `fichero:línea`, o no enviar texto (decisión en la puerta). Si se endurece `ledger-lint` sobre la línea fixN, puede ponerse en rojo en ledgers históricos: hay que aplicar la regla solo a ledgers nuevos o dejarla como aviso.
- **Incógnitas / preguntas abiertas**: ¿se envía el texto del gap?; ¿el formato canónico de fixN se impone por plantilla o solo se parsea?

### C-05 — UI + backend E2: detalle de tarea, detalle de iniciativa, resultado final

- **Requisito origen**: spec §Alcance E2, CA-11
- **Descripción**: endpoint de historial por tarea (reconstrucción de la evolución desde el versionado por entidad), detalle de tarea con línea de tiempo (rondas de revisión con lentes y gaps, fixN con coste, verificación dirigida, cierre) y tabla de gaps filtrable. Detalle de iniciativa: artefactos enlazados, coste real vs estimado por fase, embudo de gaps por intento y resultado final (qa, retro, calibración). Las tarjetas de portada y kanban ganan gaps Critical/Important e intento «2/3» o «fix5».
- **Complejidad**: Media-Alta
- **Esfuerzo**: 31,2 h humanas (26 h base) · IA 23,4 h (6,5 impl + 13,0 revisión, base 19,5 h) · confianza Media
- **Previsión IA**: 10,4 M in / 0,82 M out tok (11,2 M facturables) · 140 €
- **Coste**: valoración **1.560 €** · ciclo IA 140 € + 5,85 h supervisión (293 €) = **433 €**
- **Impacto / áreas afectadas**: backend (consultas de historial) y UI del dashboard; E2E
- **Dependencias y prerequisitos**: C-02 (esquema de historial), C-04 (datos)
- **Riesgos**: la reconstrucción temporal depende de que el emisor mande identidades estables. `T-XX` + iniciativa vale para las tareas, pero el número de gap solo es único dentro de un ledger.
- **Incógnitas / preguntas abiertas**: identidad estable de un gap entre envíos (número + iniciativa)

### C-06 — Emisor E3: salud completa + piezas/MCP (solo nombres y tipos)

- **Requisito origen**: spec §Alcance E3, CA-05
- **Descripción**: añadir al envío el `doctor.py --json` completo y el inventario de piezas y MCP (nombre y tipo; nunca `env`, argumentos con rutas ni URLs con credenciales), contrato v1.2.
- **Complejidad**: Media (poca lógica, pero de privacidad: cualquier fuga de `env` es grave)
- **Esfuerzo**: 9,6 h humanas (8 h base) · IA 12,0 h (2,0 impl + 8,0 revisión, base 10 h) · confianza Media
- **Previsión IA**: 5,3 M in / 0,42 M out tok (5,7 M facturables) · 72 €
- **Coste**: valoración **480 €** · ciclo IA 72 € + 3,0 h supervisión (150 €) = **222 €**
- **Impacto / áreas afectadas**: `dashboard-sync.py`, `doctor.py --json` (solo lectura), lectura de la config de MCP del runtime
- **Dependencias y prerequisitos**: C-01
- **Riesgos**: la config de MCP es distinta en cada runtime (Claude Code, Codex, OpenCode). Leerla mal en uno filtra datos o no ve nada. Aplica el aprendizaje de `installer-registro-real`: citar la doc del tercero antes de fijar la lectura.
- **Incógnitas / preguntas abiertas**: ¿inventario de MCP por runtime o solo del activo?

### C-07 — UI E3: salud de la instalación + métricas globales

- **Requisito origen**: spec §Alcance E3
- **Descripción**: vista de salud por proyecto (filas ✅/⚠️/❌ del `doctor`) y métricas globales: coste por proyecto/mes, desviación estimado/real, gaps por lente y rondas medias hasta cerrar.
- **Complejidad**: Media
- **Esfuerzo**: 19,2 h humanas (16 h base) · IA 14,4 h (4,0 impl + 8,0 revisión, base 12 h) · confianza Media
- **Previsión IA**: 6,4 M in / 0,50 M out tok (6,9 M facturables) · 86 €
- **Coste**: valoración **960 €** · ciclo IA 86 € + 3,6 h supervisión (180 €) = **266 €**
- **Impacto / áreas afectadas**: backend (agregados) y UI del dashboard
- **Dependencias y prerequisitos**: C-04 (gaps y rondas), C-06 (salud)
- **Riesgos**: las métricas heredan la calidad de los datos. Si los proyectos tienen `fuente: estimado` (meter degradado, como en este mismo worktree), la desviación real/estimado engaña si no se marca.
- **Incógnitas / preguntas abiertas**: ¿mostrar por separado lo `medido` y lo `estimado`? (recomendado: sí)

### C-08 — MCP de consulta (solo lectura) en el dashboard

- **Requisito origen**: spec §Alcance E3, CA-12
- **Descripción**: servidor MCP con 3-5 herramientas de consulta (proyectos, tareas bloqueadas, costes) sobre la API de lectura, con el token de lectura; ninguna escritura.
- **Complejidad**: Media
- **Esfuerzo**: 12,0 h humanas (10 h base) · IA 15,0 h (2,5 impl + 10,0 revisión, base 12,5 h) · confianza Media
- **Previsión IA**: 6,7 M in / 0,53 M out tok (7,2 M facturables) · 90 €
- **Coste**: valoración **600 €** · ciclo IA 90 € + 3,75 h supervisión (188 €) = **278 €**
- **Impacto / áreas afectadas**: repo del dashboard (servidor MCP, doc de alta en los runtimes)
- **Dependencias y prerequisitos**: C-02 (API de lectura)
- **Riesgos**: exponer el MCP fuera de localhost con el token compartido. Las respuestas grandes consumen contexto del agente que consulta: hay que paginar y resumir.
- **Incógnitas / preguntas abiertas**: transporte (stdio vs HTTP); ¿se registra en `/setup` del plugin o solo se documenta?

---

## ⚖️ Comparativa

Ordenada por entrega. Horas con margen. «H IA» incluye la revisión.

| # | Característica | Entrega | Complejidad | H humanas | H IA | € tokens | Tokens | Prioridad | Confianza |
|---|---------------|---------|-------------|-----------|------|---------|--------|-----------|-----------|
| C-01 | Emisor base | E1 | Alta | 28,8 h | 36,0 h | 216 € | 17,3 M | Alta 🟠 | Media |
| C-02 | Backend (API, SQLite, seguridad) | E1 | Alta | 26,4 h | 33,0 h | 198 € | 15,8 M | Alta 🟠 | Baja |
| C-03 | UI portada + kanbans | E1 | Media | 26,4 h | 19,8 h | 119 € | 9,5 M | Alta 🟠 | Baja |
| C-04 | Emisor revisiones/fixN/qa/retro | E2 | Alta | 19,2 h | 24,0 h | 144 € | 11,5 M | Media 🟡 | Baja |
| C-05 | Detalle tarea + iniciativa | E2 | Media-Alta | 31,2 h | 23,4 h | 140 € | 11,2 M | Media 🟡 | Media |
| C-06 | Emisor salud + piezas/MCP | E3 | Media | 9,6 h | 12,0 h | 72 € | 5,7 M | Baja 🟢 | Media |
| C-07 | UI salud + métricas globales | E3 | Media | 19,2 h | 14,4 h | 86 € | 6,9 M | Baja 🟢 | Media |
| C-08 | MCP de consulta | E3 | Media | 12,0 h | 15,0 h | 90 € | 7,2 M | Baja 🟢 | Media |
| | **Total** | | | **172,8 h** | **177,6 h** | **1.065 €** | **85,1 M** | | |

**Quick wins vs costosas:**

| Grupo | Características | Por qué |
|---|---|---|
| ⚡ Quick wins (bajo coste, alto valor) | **C-03** (valor visible inmediato, riesgo de revisión bajo) · **C-06** (reutiliza `doctor.py --json` y `capabilities.py`) | Menos de 20 h IA cada una y sin estado durable nuevo |
| 💸 Costosas / a valorar | **C-01** y **C-02** (imprescindibles: son la base) · **C-04** (parser tolerante + formalizar el ledger) · **C-05** (reconstrucción temporal) | Concentran la revisión adversarial: privacidad, red, cola, seguridad, historial |
| 🤔 Valor a confirmar | **C-08** (MCP) | Útil si los agentes consultarán la cartera. Si no, la UI basta y se ahorran 15 h IA |

---

## 🧮 Presupuesto total

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano equivalente, base) | 144 h × 50 €/h | 7.200 € |
| Margen de contingencia | +20 % sobre desarrollo base | 1.440 € |
| **Valoración humana (con margen)** | 172,8 h × 50 €/h | **8.640 €** |
| Tokens IA (input: entrada + escritura de caché) | 78,9 M tok (incluido en el € por hora-IA medido) | ~ |
| Tokens IA (output) | 6,2 M tok × 23 €/M ≈ 143 € (incluido en el € por hora-IA medido) | ~ |
| Tokens IA (total, lectura de caché incluida) | 177,6 h-IA × 6 €/h (medido en ventanas fixN) | 1.065 € |
| Supervisión humana | 44,4 h × 50 €/h | 2.220 € |
| **Coste real previsto del ciclo IA (con margen)** | tokens + supervisión | **3.285 €** |
| Coste de proceso (spec/eval/design/plan) | ~3,9 h-IA | ~24 € |

> El total de tokens no se desglosa por precio de input porque la mezcla entrada/escritura de caché/lectura de caché no es previsible. Se usa el **€ por hora-IA medido** (que ya la incluye), no un precio por millón aplicado a mano.

---

## ⚡ Productividad IA (humano vs. IA)

| KPI | Horas-equivalentes (tokens ÷ ratio) | Reloj (orientativo) |
|-----|-----|-----|
| Horas humanas estimadas | 172,8 h | 172,8 h |
| Horas IA (ejecución) | 177,6 h | ~53,3 h |
| Supervisión humana | 44,4 h | 44,4 h |
| **Horas totales (IA + supervisión)** | **222,0 h** | **~97,7 h** |
| Horas ahorradas | −49,2 h | ~75,1 h |
| **Ahorro** | **−28,5 %** | **~43 %** |
| **Multiplicador de productividad** | **×0,78** | **×1,77** |
| FTE equivalentes *(opcional)* | −0,31 | ~0,47 |

> Horas **con el margen de contingencia (+20 %)** ya aplicado (base: 144 h humanas, 148 h IA). Las horas-IA son **horas-equivalentes derivadas de tokens** (ratio 479.326), no reloj. En las ventanas fixN medidas, el reloj fue ~30 % de esas horas. La supervisión (25 %, `rates.json`) es conservadora: en el histórico la medida real es 0 h. Las horas humanas **nunca se han validado** (aprendizaje 2 de `CALIBRATION.md`). Por eso el multiplicador no es un argumento de venta: el gasto real es de ~3.285 € (tokens + supervisión) frente a una valoración de 8.640 €.

---

## 🎯 Recomendación

- **Veredicto**: **go con condiciones**:
  1. **`architect` antes de `planner`** (obligatorio aquí): stack de backend/UI, ubicación del dashboard (repo aparte y cómo se lleva su cadena y su CI), esquema de historial por entidad y retención, contrato v1 y el **ADR nuevo** sobre `project` como etiqueta frente a ADR-018.
  2. **Go firme solo para E1**. E2 y E3 se reevalúan con la retro de E1, que da la primera calibración de UI y backend de este plugin.
  3. **Tope de 3 intentos de revisión por entrega**. Si al tercero quedan Critical, se para y se re-decide; no se abren rondas fixN sin límite como en `training-data-services`.
  4. En la puerta, decidir si se envía **texto de gaps** o solo metadatos.
- **Quick wins** (bajo coste, alto valor): C-03, C-06
- **Costosas / a valorar**: C-01, C-02 (base imprescindible), C-04, C-05; C-08 a confirmar
- **Orden sugerido**: `architect` → **E1** (C-01 contrato primero → C-02 → C-03) → retro E1 → **E2** (C-04 formalizar el ledger → C-05) → **E3** (C-06 → C-07 → C-08). El contrato va primero porque lo consumen emisor y backend. C-04 va antes de C-05 porque la UI de revisiones no tiene de dónde leer sin él. Conviene arrancar E2 **después del merge de `feature/training-data-services`**, que aporta el ledger real con más rondas fixN.
- **Ajustes a las entregas**: el **kanban de iniciativas** pasa de «sin entrega» a **E1** (C-03, ~3 h: usa datos que E1 ya emite). La **salud resumida** de la tarjeta de portada va en E1 (C-01) y la vista completa en E3.
- **Fuera de alcance recomendado**: login/permisos (fase futura), envío desde hooks o por MCP, métricas de Headroom (futura capacidad opt-in, como `kwipu`).

---

## ⚠️ Riesgos transversales

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| La revisión se come el presupuesto (patrón `training-data-services`: ×3,9 y sin cerrar) | Alta | Alto | Revisión como línea propia (134 h de 178), tope de 3 intentos por entrega, reevaluación tras E1 |
| Fuga de datos sensibles (código citado en gaps, `env` de MCP, secretos) | Media | Alto | `redact.py`, truncado, evidencia solo `fichero:línea`, lista blanca de campos en el JSON Schema (sin `additionalProperties`), test de contrato con casos adversariales, `nemesis` en local |
| Conflicto con ADR-018 (control plane multi-proyecto rechazado) | Media | Medio | ADR nuevo antes de implementar: `project` es etiqueta del dashboard y no toca el aislamiento del plugin |
| Dos repos y una sola cadena (`scope-check`/`guardrail-check` asumen un repo) | Alta | Medio | Que `architect` decida: cadena propia en el repo del dashboard, o subcarpeta excluida del paquete del plugin |
| Formato de ledger heterogéneo (≥ 7 cabeceras de gaps, fixN en prosa) | Alta | Medio | Formalizar en `ledger-lint` para ledgers nuevos, `no-verificable` para los históricos, nunca inventar grados |
| Exposición externa mal configurada | Baja | Alto | Bind `127.0.0.1` por defecto, exposición solo con proxy TLS documentado, token de lectura obligatorio |
| Crecimiento del historial | Media | Medio | Versionado por entidad con hash, retención configurable |
| Medición degradada (`fuente: estimado`) en proyectos consumidores, como en este worktree | Alta | Bajo | Marcar `medido`/`estimado` en el contrato y en las métricas de C-07 |
| Envío que alarga el ciclo si el dashboard responde lento | Media | Bajo | Timeout corto con tope total, encolar y seguir (patrón de `doctor.py`) |

---

## ➡️ Siguiente paso

1. Puerta go/no-go del usuario sobre esta evaluación, con las condiciones de §Recomendación.
2. Si es go: **`architect`**, que produce `design.md` (stack, repo, historial, contrato v1) y el ADR nuevo en `propuesta`.
3. **`planner`** con **E1 aprobada** (C-01, C-02, C-03), que crea `improvement-plan.md` + `tasks.md` en esta carpeta, con una línea de revisión + corrección por fase heredada de esta evaluación. E2 (C-04, C-05) y E3 (C-06, C-07, C-08) quedan pendientes de reevaluación tras la retro de E1. El `planner` hereda estas horas y costes, no re-estima desde cero, y rellenará la fila **Plan** de esta evaluación y el `plan:` de la spec.

---

## 📝 Changelog

- 2026-09-28 — Creación (evaluator, `/pm-cycle` Fase 1). Spec creada en `borrador` en la misma sesión; evaluación en `en-revision`.

## Decisión (puerta go/no-go de `/pm-cycle`, 2026-09-28)

**GO del usuario**, con las condiciones de esta evaluación: (1) `architect` antes de `planner` (stack, repo, historial por entidad y retención, contrato v1, ADR frente a ADR-018); (2) go firme solo para E1 — E2 y E3 se reevalúan con la retro de E1; (3) tope de 3 intentos de revisión por entrega; (4) decidir en el diseño si se envía el texto de los gaps o solo metadatos. **Arranque diferido por decisión del usuario:** empieza cuando no quede nada pendiente del roadmap (training-data-services → arreglo de Graphiti #13 → statusline/pulido del setup → dev-cycle-dataset → brief-budget → plugin-refactor → project-specialization); hasta entonces, ni `architect` ni `planner`.

