---
generacion:               # MEDIDO por usage-meter.py
  inicio: 2026-08-12T07:49:09Z
  fin: 2026-08-12T07:51:03Z
  fuente: medido
  tokens_reales: { entrada: 6, salida: 8852, cache_creacion: 9282, cache_lectura: 1154847 }
  eur: null                 # precioTokens sin verificar (rates-verify)
  horas_ia: 0.06
  duracion: 4m
  ratio_usado: 300000       # default no calibrado
---

# 2026-08-12-sdd-hardening

> SDD hardening — completar el plugin frente a superpowers, Spec Kit y Agent-Monitor: evaluación de coste/esfuerzo de las 6 características (constitución, /spec-drift, G/W/T, TDD/worktrees opt-in, debug-root-cause, doc de observabilidad) para decidir el go.

| | |
|---|---|
| **Fecha** | 2026-08-12 |
| **Estado** | en-revision 🔍 |
| **Prioridad global** | Media 🟡 |
| **Solicitante** | jmano@mediapro.tv |
| **Spec** | [`spec.md`](spec.md) |
| **Plan** | [`improvement-plan.md`](improvement-plan.md) + [`tasks.md`](tasks.md) (2026-08-12) |
| **Características evaluadas** | 8 |

---

## Cuadro de mando

| Métrica | Total estimado | Confianza |
|--------|----------------|-----------|
| Esfuerzo humano | **22,2 h** (18,5 h base +20 %) | Media |
| Tiempo IA (ejecución) | **7,1 h** (+ 1,8 h supervisión) | Media |
| Coste | **~1.150 €** | Media |
| Tokens IA | **~1,76 M** (in 1,48 M / out 0,28 M) | Baja |
| Multiplicador productividad | **×2,5** | — |
| Características | **8** | — |

> ⚠️ **Nota de confianza:** la iniciativa es casi toda **prosa sobre piezas existentes** (patrones ya rodados: fragmentos shared, opt-ins, subagentes de lente A, bucles acotados) + una skill y un command nuevos. El único código es un caso nuevo en `coverage-check.py`. El riesgo no está en el volumen sino en dos encajes: que la lente A absorba la constitución sin ruido (falsos gaps "constitucionales" de estilo) y que el TDD opt-in no se convierta en teatro (evidencia del rojo exigida en el ledger).

---

## Resumen ejecutivo

Del análisis comparativo (2026-08-12) contra superpowers, GitHub Spec Kit / LiorCohen-sdd y Claude-Code-Agent-Monitor salieron 6 gaps; el usuario eligió cerrarlos **todos** en una iniciativa. Dos de gobernanza: **C-01 constitución** del proyecto consumidor (principios permanentes que todos los agentes leen y la lente A hace cumplir) y **C-02 `/spec-drift`** (deriva spec↔código de las specs `implementada`, el `/speckit.analyze` que faltaba). Una de calidad de specs: **C-03 criterios Given/When/Then opcionales** con traducción 1:1 a tests E2E. Dos de disciplina de ingeniería en Modo B: **C-04 TDD RED-GREEN-REFACTOR y worktrees opt-in** (`.claude/dev.json`, default off; en Modo A manda superpowers) y **C-05 skill `debug-root-cause`** (4 fases con evidencia, disparada al 3.er rojo de qa antes de rendirse). Una de ecosistema: **C-06 doc de observabilidad** (usage-meter = coste con significado de negocio; Agent-Monitor = actividad en vivo; coexisten). Se presupuestan **14,5 h base (17,4 h con margen), ~900 €** y ~1,38 M tokens. Veredicto: **go** — sin dependencias externas no verificadas (todo son patrones internos ya probados); única condición: E2E de juguete para `/spec-drift` y para la puerta constitucional antes de cerrar.

---

## Requerimientos recibidos

| ID | Característica | Requisito origen (ref.) | ¿Claro? |
|----|---------------|-------------------------|---------|
| C-01 | Constitución del consumidor | spec §Características C-01 + §Decisiones (dónde vive, quién la lee, qué contiene, enforcement por lente A) | ✅ |
| C-02 | `/spec-drift` | spec §Características C-02 + §Decisiones (comando, salida DRIFT.md) | ✅ |
| C-03 | Criterios G/W/T opcionales | spec §Características C-03 + §Decisiones ("Opcional, no obligatorio") | ✅ |
| C-04 | TDD + worktrees opt-in Modo B | spec §Características C-04 + §Decisiones (config dev.json, defaults off, solo Modo B) | ⚠️ ambiguo (evidencia del rojo: formato exacto en el ledger) |
| C-05 | Skill `debug-root-cause` | spec §Características C-05 + §Decisiones (4 fases, disparo al 3.er rojo) | ✅ |
| C-06 | Doc de observabilidad | spec §Características C-06 + §Decisiones ("documentación, no implementación") | ✅ |
| C-07 | Cadena nativa siempre por defecto | spec §Características C-07 + Decisión confirmada 3 (ampliación 2026-08-12) | ✅ |
| C-08 | Subagentes de contexto fresco (opt-in) | spec §Características C-08 + Decisión confirmada 4 (ampliación 2026-08-12) | ⚠️ ambiguo (contexto mínimo exacto del subagente) |

**Ambigüedades / información que falta:**

- **Formato de la evidencia del rojo (C-04).** ¿Salida del test pegada en el ledger, o referencia a fichero de log? Propuesta del plan: una línea por tarea (`RED: <test> falló con <error> · <fecha>`) — barata y suficiente; si el equipo quiere más, es config futura.
- **Ruido constitucional en la lente A (C-01).** Riesgo de que la lente reporte "violaciones" de estilo. Mitigación: la prosa de la lente limita los gaps constitucionales a principios EXPLÍCITOS del fichero, citando la línea violada.
- **Verificabilidad del drift en specs de prosa (C-02).** Declarada en la spec (§Supuestos): el veredicto `no verificable` existe para eso; no baja el go.

---

## Datos necesarios para una evaluación completa

- [x] **Requerimientos** completos (6 características con decisiones de diseño cerradas)
- [x] **Alcance** acotado (fuera: dashboard propio, auto-corrección de drift, G/W/T obligatorio, TDD en Modo A)
- [x] **Criterios de aceptación / éxito** (spec §Pruebas)
- [x] **Restricciones** (no duplicar superpowers, opt-in todo, degradación sin bloquear, no reinventar el monitor)
- [x] **Dependencias externas** — ninguna no verificada: todo son patrones internos ya rodados (fragmentos shared, lente A, bucles acotados, /setup, coverage-check)
- [x] **Contexto técnico** (revisión de dos lentes desplegada, /setup idempotente, coverage-check.py con tests)
- [x] **Tarifa/hora y supuestos de coste** confirmados (defaults; sin `.claude/rates.json`)

---

## Supuestos económicos (ajustables)

**Coste = (horas × tarifa) + coste de tokens de IA.** Importes en **EUR**.

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | 50 €/h | Default compartido (no existe `.claude/rates.json`) |
| Modelo IA asumido | claude-opus-4-8 | Base de la previsión de tokens |
| Precio input | 13,80 € / 1M tokens | ⚠️ verificar — supuesto de trabajo: 15 USD/M × 0,92 |
| Precio output | 69,00 € / 1M tokens | ⚠️ verificar — supuesto de trabajo: 75 USD/M × 0,92 |
| Tipo de cambio | 1 USD = 0,92 € | Default |
| Ratio de supervisión | 25 % de las horas IA | Default |
| Margen de contingencia | 20 % | Sobre horas base (humanas e IA) |

**Calibración con el histórico del repo:** `token-diet` (prosa + script pequeño) = 10,75 h base; `coste-generacion` (script medio + 7 piezas de prosa) = 16,0 h base. Esta iniciativa es **prosa distribuida en muchas piezas pequeñas** (2 plantillas, 1 fragmento, 1 skill, 1 command, 2 configs, 6 agentes tocados ligeramente, 1 doc) + un caso de test: perfil entre ambas → 14,5 h base. El coste de tokens sigue siendo marginal (~4 %). **Primera iniciativa con coste de proceso MEDIDO**: la spec costó 14.611 tokens facturables (`fuente: medido`, 3m al ratio no calibrado) — dato real, no estimación.

---

## Evaluación por característica

### C-01 — Constitución del proyecto consumidor

- **Requisito origen**: spec §Características C-01; §Decisiones (ubicación, lectores, contenido, enforcement).
- **Descripción**: plantilla `CONSTITUTION.template.md` (shared), `/setup` la ofrece guiada (opt-in), fragmento `constitution-check.md` referenciado por los 6 agentes que escriben, y la lente A la incorpora como entrada de revisión (violación de principio explícito = gap de corrección, citando línea).
- **Complejidad**: Media · **Esfuerzo**: 2,5 h · confianza **Media**
- **Previsión IA**: 200k in / 35k out · ~5 € · **Coste**: **~131 €**
- **Impacto**: `agent-kits/shared/` (plantilla + fragmento), `commands/setup.md`, 6 `agents/*.md`, prosa lente A en `commands/dev-cycle.md`.
- **Riesgos**: ruido de la lente (mitigado: solo principios explícitos, con cita); constituciones-tomo (aviso en plantilla).

### C-02 — `/spec-drift` (deriva spec↔código)

- **Requisito origen**: spec §Características C-02; §Decisiones (comando, salida, "informar no corregir").
- **Descripción**: nuevo command de solo lectura: por cada spec `implementada` (todas o slug), subagente de contexto fresco verifica cada criterio contra el código actual → `docs/roadmap/DRIFT.md` (vigente ✓ / derivado ✗ / no verificable, con evidencia) + resumen + oferta de `/pm-cycle`.
- **Complejidad**: Media-Alta · **Esfuerzo**: 3,0 h · confianza **Media**
- **Previsión IA**: 240k in / 45k out · ~6 € · **Coste**: **~156 €**
- **Impacto**: nuevo `commands/spec-drift.md`, formato `DRIFT.md`, fila en docs/README y FLOWS diagrama 6.
- **Riesgos**: coste de tokens en repos con muchas specs (mitigado: lotes de máx. 3 en paralelo y filtro por slug); veredictos alegres (mitigado: `no verificable` obligatorio cuando no hay evidencia).

### C-03 — Criterios Given/When/Then opcionales

- **Requisito origen**: spec §Características C-03; §Decisiones (opcional, marca `[GWT]`, traducción 1:1 a E2E).
- **Descripción**: variante G/W/T en la plantilla de spec; analyst/discovery la ofrecen para comportamiento observable; qa traduce `[GWT]` a bloques E2E; `coverage-check.py` reconoce el mapeo (caso de test nuevo).
- **Complejidad**: Media · **Esfuerzo**: 2,0 h · confianza **Alta**
- **Previsión IA**: 170k in / 30k out · ~4 € · **Coste**: **~104 €**
- **Impacto**: plantilla spec, `agents/analyst.md`, skill discovery, `agents/qa.md`, `agent-kits/qa/coverage-check.py` + tests.
- **Riesgos**: mínimos; compatibilidad total con specs existentes (aditivo).

### C-04 — TDD + worktrees opt-in en Modo B

- **Requisito origen**: spec §Características C-04; §Decisiones (config, defaults off, solo Modo B, degradación).
- **Descripción**: `.claude/dev.json` `{tdd, worktree}` creado por `/setup`; con `tdd: true`, RED-GREEN-REFACTOR por tarea con evidencia del rojo en el ledger; con `worktree: true`, worktree por iniciativa con limpieza y degradación a rama normal.
- **Complejidad**: Media-Alta · **Esfuerzo**: 3,5 h · confianza **Media**
- **Previsión IA**: 270k in / 50k out · ~7 € · **Coste**: **~182 €**
- **Impacto**: `agents/implementer.md`, `commands/dev-cycle.md`, `commands/setup.md`, regla 9 de CONVENTIONS (config nueva).
- **Riesgos**: TDD-teatro (test trivial para "cumplir") — mitigado exigiendo la evidencia del ROJO antes del código en el ledger; interacción con worktree y OneDrive/repos raros — degradación con aviso.

### C-05 — Skill `debug-root-cause`

- **Requisito origen**: spec §Características C-05; §Decisiones (4 fases, disparo automático al 3.er rojo).
- **Descripción**: skill compartida con método de 4 fases y evidencia obligatoria por fase; `/dev-cycle` la ejecuta al 3.er rojo de qa ANTES de parar y preguntar (la pregunta llega con diagnóstico); invocable a demanda.
- **Complejidad**: Media · **Esfuerzo**: 2,5 h · confianza **Media-Alta**
- **Previsión IA**: 200k in / 40k out · ~5 € · **Coste**: **~131 €**
- **Impacto**: nueva `skills/debug-root-cause/SKILL.md`, `commands/dev-cycle.md` (bucle qa), docs/README (fila), lint verde.
- **Riesgos**: que el diagnóstico alargue el bucle sin límite — mitigado: UNA pasada de diagnóstico y luego la pregunta de siempre.

### C-07 — Cadena nativa siempre por defecto (ampliación 2026-08-12)

- **Requisito origen**: spec §Características C-07; Decisión confirmada 3 ("sin depender de superpowers").
- **Descripción**: invertir la preferencia de `/dev-cycle`: la cadena nativa es EL modo por defecto siempre; superpowers solo bajo petición explícita (o `--superpowers`), manteniendo entonces las reglas de coexistencia (ledger canónico, transiciones del orquestador). Actualizar dev-cycle, CLAUDE.md, FLOWS (diagrama 3) y doc del command.
- **Complejidad**: Baja-Media · **Esfuerzo**: 1,0 h · confianza **Alta** (es prosa de inversión de una regla existente)
- **Previsión IA**: 75k in / 15k out · ~2 € · **Coste**: **~52 €**
- **Impacto**: `commands/dev-cycle.md`, `CLAUDE.md`, `docs/FLOWS.md`, `docs/agents/` (doc del ciclo).
- **Riesgos**: usuarios que contaban con la delegación automática — mitigado: se documenta el cambio en CHANGELOG como comportamiento nuevo y el modo explícito sigue disponible.

### C-08 — Desarrollo por subagentes de contexto fresco, opt-in (ampliación 2026-08-12)

- **Requisito origen**: spec §Características C-08; Decisión confirmada 4.
- **Descripción**: `subagentes: true` en `.claude/dev.json` (default `false`; lo pregunta `/setup`): cada `T-XX` la implementa un subagente FRESCO, con las **4 mecánicas del ciclo de superpowers** (ampliación 2026-08-12): (1) brief extraído por el **script determinista `task-brief.py`** (+tests) — no prosa a mano; (2) **brief-only** (sin explorar el repo entero); (3) estados ricos `DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT / BLOCKED` (`NEEDS_CONTEXT` = re-despacho con el contexto pedido, no inventar); (4) **revisor persistente** en el bucle de corrección con severidades `Critical / Important / Minor`. El orquestador valida contra criterios, marca el ledger y conserva todas las puertas. Re-despacho acotado a 1; segundo fallo → flujo normal con aviso.
- **Complejidad**: Media-Alta · **Esfuerzo**: 3,0 h · confianza **Media** (2,0 h del diseño original + 1,0 h por las mecánicas: el script con tests es lo que suma)
- **Previsión IA**: 240k in / 45k out · ~7 € · **Coste**: **~157 €**
- **Impacto**: **nuevo** `agent-kits/shared/task-brief.py` (+tests), `commands/dev-cycle.md` (despacho + estados + revisor persistente), `commands/setup.md` y regla 9 (clave `subagentes`), `agents/implementer.md` (nota de convivencia).
- **Riesgos**: brief insuficiente → `NEEDS_CONTEXT` lo hace explícito (mejor que inventar); coste de tokens mayor por tarea (visible y calibrable con la medición por tarea — sinergia con coste-generacion); parseo de `tasks.md` en el script → se apoya en `ledger-lint.py` (ledger válido antes de despachar).
- **Incógnitas**: resueltas por las mecánicas — el contenido del brief lo define `task-brief.py` (tarea + criterios + arquitectura + fase + constitución).

### C-06 — Doc de observabilidad (monitores externos)

- **Requisito origen**: spec §Características C-06; §Decisiones ("documentación, no implementación").
- **Descripción**: `docs/observability.md` (posicionamiento usage-meter vs monitor de sesión, coexistencia de hooks, instalación conjunta) + enlaces desde README/INSTALL.
- **Complejidad**: Baja · **Esfuerzo**: 1,0 h · confianza **Alta**
- **Previsión IA**: 85k in / 15k out · ~2 € · **Coste**: **~52 €**
- **Impacto**: nueva `docs/observability.md`, `docs/README.md`, `docs/INSTALL.md`.
- **Riesgos**: mínimos.

---

## Comparativa

| # | Característica | Complejidad | Horas (base) | Coste € | Tokens (in/out) | Prioridad | Confianza |
|---|---------------|-------------|--------------|---------|-----------------|-----------|-----------|
| C-01 | Constitución | Media | 2,5 h | ~131 € | 235k (200/35) | Alta 🟠 | Media |
| C-02 | `/spec-drift` | Media-Alta | 3,0 h | ~156 € | 285k (240/45) | Alta 🟠 | Media |
| C-03 | Criterios G/W/T | Media | 2,0 h | ~104 € | 200k (170/30) | Media 🟡 | Alta |
| C-04 | TDD + worktrees opt-in | Media-Alta | 3,5 h | ~182 € | 320k (270/50) | Media 🟡 | Media |
| C-05 | `debug-root-cause` | Media | 2,5 h | ~131 € | 240k (200/40) | Media 🟡 | Media-Alta |
| C-06 | Doc observabilidad | Baja | 1,0 h | ~52 € | 100k (85/15) | Baja 🟢 | Alta |
| C-07 | Cadena nativa siempre | Baja-Media | 1,0 h | ~52 € | 90k (75/15) | Alta 🟠 | Alta |
| C-08 | Subagentes de contexto fresco (4 mecánicas) | Media-Alta | 3,0 h | ~157 € | 285k (240/45) | Media 🟡 | Media |
| | **Total** | | **18,5 h** | **~964 €** | **~1,76 M** | | |

> El **Total** de la tabla es coste **base** (18,5 h × 50 € + ~39 € de tokens). El presupuesto con margen está abajo.

---

## Presupuesto total

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 18,5 h × 50 €/h | 925,00 € |
| Margen de contingencia | +20 % sobre desarrollo base | 185,00 € |
| Tokens IA (input) | 1,48 M tok × 13,80 €/M ⚠️ | 20,42 € |
| Tokens IA (output) | 0,28 M tok × 69,00 €/M ⚠️ | 19,32 € |
| **Total estimado (con margen)** | | **~1.150 €** |

---

## Productividad IA (humano vs. IA)

| KPI | Valor |
|-----|-------|
| Horas humanas estimadas | 22,2 h *(18,5 h base)* |
| Horas IA (ejecución) | 7,1 h *(5,9 h base; supuesto)* |
| Supervisión humana | 1,8 h *(25 % de las horas IA)* |
| **Horas totales (IA + supervisión)** | **8,9 h** |
| Horas ahorradas | 13,3 h |
| **Ahorro** | **~60 %** |
| **Multiplicador de productividad** | **×2,5** |

---

## Recomendación

- **Veredicto**: **go** — sin dependencias externas no verificadas; todo son patrones internos rodados. Condición ligera de cierre: E2E de juguete para `/spec-drift` (✓/✗/no-verificable correctos) y para la puerta constitucional (la lente A detecta una violación explícita).
- **Quick wins**: **C-06** (1,0 h), **C-03** (2,0 h, mejora directa de la cobertura criterios↔tests).
- **Costosas / a valorar**: **C-04** (la más cara y la única que cambia hábitos; por eso es opt-in con default off — su coste de adopción real lo decide cada equipo).
- **Orden sugerido**: **C-01 → C-03 → C-02 → C-05 → C-07 → C-04 → C-08 → C-06** — la constitución primero (C-02, la lente A y los subagentes la consumen), G/W/T antes que el drift, debugging barato antes que TDD, la inversión de preferencia (C-07) antes de tocar el despacho, subagentes (C-08) tras TDD/worktrees (comparten `dev.json` y se combinan), y la doc al final.
- **Fuera de alcance recomendado**: respetar el "Fuera" de la spec (dashboard propio, auto-corrección de drift, G/W/T obligatorio, TDD en Modo A).

---

## Riesgos transversales

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Lente A genera falsos gaps "constitucionales" de estilo | Media | Medio | Solo principios EXPLÍCITOS con cita de línea; lo demás se descarta como estilo (regla vigente de la lente) |
| `/spec-drift` caro en tokens con muchas specs | Media | Bajo-Medio | Lotes máx. 3, filtro por slug, y read-discipline en los subagentes |
| TDD-teatro (tests triviales para cumplir) | Media | Medio | Evidencia del ROJO obligatoria en el ledger antes del código; la lente B ya caza tests vacíos |
| Worktrees en entornos sin git decente | Baja | Bajo | Degradación a rama normal con aviso (testada en manejo de errores) |
| Solapamiento conceptual con superpowers si está instalado | Baja | Medio | Regla explícita: en Modo A mandan sus skills; lo nuevo solo aplica en Modo B |

---

## Siguiente paso

Para **ejecutar** lo aprobado, genera el plan detallado con el agente **`planner`** (rellenará `improvement-plan.md` + `tasks.md` en esta misma carpeta). Recomendación: **las 6 características** en el orden C-01 → C-03 → C-02 → C-05 → C-04 → C-06, con el E2E de juguete (drift + puerta constitucional) como condición de cierre. Las horas por característica se heredan tal cual.

---

## Changelog

- **2026-08-12** — Evaluación inicial de la spec `sdd-hardening`. 6 características, 14,5 h base (17,4 h con margen), ~900 €, ~1,38 M tokens. Veredicto: **go** (condición ligera: E2E de juguete para drift y puerta constitucional).
- **2026-08-12** — **Re-evaluación tras ampliar la spec de 6 a 8 características** (usuario: autosuficiencia sin depender de superpowers): C-07 "cadena nativa siempre por defecto" (1,0 h) y C-08 "subagentes de contexto fresco opt-in" (2,0 h). Total **17,5 h base (21,0 h con margen), ~1.090 €, ~1,68 M tokens**. Veredicto sin cambios: **go**.
- **2026-08-12** — **C-08 ampliada con las 4 mecánicas del ciclo de superpowers** (task-brief.py determinista + tests, brief-only, estados ricos, revisor persistente con severidades): 2,0 → 3,0 h. Los perfiles de dominio → backlog (`2026-08-12-subagent-personas`, spec borrador). Total **18,5 h base (22,2 h con margen), ~1.150 €, ~1,76 M tokens**. Veredicto sin cambios: **go**.
