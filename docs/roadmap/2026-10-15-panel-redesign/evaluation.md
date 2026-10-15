---
generacion:               # usage-meter.py close
  inicio: 2026-10-15T09:07:44Z
  fin: 2026-10-15T09:15:46Z
  fuente: medido
  fuente_id: src-d2ceb5c719af848b4c213bb2d521d0f003976923acb613d7512912ccbeb6a09e
  ventana_id: win-3b8ddc69720d4f18a544afc8aa2b439f
  revision_medicion: 1
  medicion_persistida: true
  tokens_reales: { entrada: 110, salida: 38957, cache_creacion: 238790, cache_lectura: 8068634 }
  tokens_procedencia: transcript
  tokens_cobertura: completa
  coste_procedencia: estimado_tarifa
  coste_cobertura: completa
  eur: 5.98
  horas_ia: 0.52
  duracion: 31m             # duracion_reloj: 8m
  ratio_usado: 531798.5     # CALIBRATION.md (mediana de 6)
  avisos: ["CALIBRATION: 7 filas marcadas (estimado) fuera de la mediana", "tarifa verificada el 2026-08-18", "3 transcripts leídos (2 de subagente)"]
---

# 2026-10-15-panel-redesign

> Rediseño del panel local en siete páginas, con kanban, gráficos Chart.js incluidos y registro de eventos de herramienta: cuánto cuesta cada una de las cuatro fases acordadas y con qué condiciones conviene arrancar. Sirve para la puerta go/no-go de `/pm-cycle` y como base del `planner`.

| | |
|---|---|
| **Fecha** | 2026-10-15 |
| **Estado** | en-revision 🔍 |
| **Prioridad global** | Media 🟡 |
| **Solicitante** | Usuario del repo (conversación del 2026-10-15) |
| **Spec** | [`spec.md`](spec.md) |
| **Design** | pendiente (architect obligatorio: D-A1, D-A2) |
| **Plan** | pendiente (handoff a planner) |
| **Características evaluadas** | 5 (cuatro fases de la spec + cierre transversal) |

---

## Cuadro de mando

| Métrica | Total estimado | Confianza |
|--------|----------------|-----------|
| Esfuerzo humano (referencia) | **134,4 h** (112 h base +20 %) | Baja |
| Tiempo IA (ejecución) | **50,7 h** (+ 16,7 h supervisión, incluida la revisión manual de cada fase) | Baja |
| Coste | **≈ 7.075 €** de referencia (6.720 € humanos + 355 € de tokens) · **≈ 1.188 €** de ejecución con agentes | Media (precios) · Baja (horas IA) |
| Tokens IA | **26,96 M facturables** (in 23,19 M / out 3,77 M) + ~297 M de lectura de caché | Baja |
| Multiplicador productividad | **×2,0** | — |
| Características | **5** | — |

---

## Resumen ejecutivo

La spec pide un panel local de siete páginas (Inicio, Iniciativas, Plan, Agentes en vivo, Memoria, Catálogo, Diagnóstico) con 44 criterios de aceptación en cuatro fases, más una ampliación del registro de actividad con eventos por herramienta en los tres runtimes. Las fases 1, 2 y 4 son trabajo de presentación sobre fuentes que ya existen y tienen tests. La **fase 3 concentra el riesgo y el 43 % de las horas IA**: un hook nuevo que corre en **cada** uso de herramienta, sobre un almacén de estado endurecido (`agent-activity-store.py`), con redacción de argumentos y tres runtimes de comportamiento ajeno. Veredicto: **go condicionado**. Las fases 1, 2 y 4 pueden planificarse en cuanto architect cierre D-A1. La fase 3 espera a D-A2 y a tres respuestas: latencia aceptable por evento (I-05), tope del historial (I-03) y evidencia citada de los eventos de herramienta de Codex (I-08).

---

## Requerimientos recibidos

| ID | Característica | Requisito origen (ref.) | ¿Claro? |
|----|---------------|-------------------------|---------|
| C-01 | Base común: multi-página, menú, Chart.js local, CSP, modos servido y exportado, accesibilidad base, aplicación de D-A1 | Spec «Fases propuestas» F1 · CA-32..CA-41, CA-43 | ⚠️ ambiguo: D-A1 abierta (quién absorbe a quién y qué comando abre el panel); I-01 (CSP con `file://`) sin probar |
| C-02 | Inicio (cifras de cartera), Iniciativas (kanban + gráficos) y Plan (kanban de tareas, detalle, avance por fase, burndown, real vs estimado, refresco vivo) | F2 · CA-01..CA-03, CA-05..CA-14 | ✅ salvo I-02 (ver abajo) |
| C-03 | Captura de eventos de herramienta + página Agentes en vivo + actividad reciente en Inicio | F3 · CA-04, CA-15..CA-21, CA-42 (eventos) | ⚠️ ambiguo: D-A2, I-03, I-05, I-07 e I-08 abiertas |
| C-04 | Memoria (vista sencilla), Catálogo sin pérdida de información y Diagnóstico | F4 · CA-22..CA-31 | ✅ salvo I-09 (de dónde sale «qué se publicó» sin red) |
| C-05 | Cierre transversal: documentación de la pieza dueña, `FLOWS.md`/`observability.md` y espejos EN, CHANGELOG ×2, `interop/` regenerado, verificación Linux | Spec «Alcance» (último punto) · CA-42, CA-44 | ✅ |

**Ambigüedades / información que falta:**

- **D-A1** (dueño de la presentación). Cambia dónde se escribe, pero no cuánto: en las dos opciones hay que dejar un solo HTML y conservar `dashboard.md` y `--json`. Se presupuesta la absorción **en `plugin-panel`**, porque ya tiene servidor, token y CSP. La otra dirección mueve el servidor y cuesta más (≈ +4 h humanas, +1 h IA). No cambia el veredicto.
- **I-02** (burndown). El recon no encuentra fechas de cierre por tarea en los ledgers (`grep` sobre `2026-10-06-project-extensions/tasks.md`: 0 resultados). Lo probable es que CA-12 termine en su rama «burndown no disponible». Se presupuesta solo esa rama más el gráfico **si** architect decide añadir la fecha al ledger. Añadirla tocaría el contrato de `ledger-lint.py` y del bloque replicado (ADR-016), y quedaría **fuera de esta estimación**.
- **I-05** (latencia por evento). Cada uso de herramienta lanza ya `node run-hook.mjs` → `python3` para los PostToolUse informativos. Añadir la captura a **todos** los PreToolUse/PostToolUse multiplica esos arranques. Sin una cifra aceptada no se puede cerrar CA-21 ni elegir entre «un proceso por evento» y «agregado al hook existente».
- **I-08** (Codex). Hay evidencia de PreToolUse/PostToolUse en `interop/codex/hooks.json`, pero no de que el payload traiga el identificador de subagente. Sin él, Codex queda como «no emite eventos de herramienta» (CA-42).
- **Nivel de riesgo.** La spec no declara `riesgo:`, y `risk-profile.py` (ADR-022) **no existe en el repo**: el ADR sigue en `propuesta`. Los multiplicadores de revisión de abajo los fija esta evaluación a partir de `CALIBRATION.md`; no salen de un perfil.

---

## Datos necesarios para una evaluación completa

- [ ] **Requerimientos** completos y sin ambigüedades (D-A1, D-A2 e I-01..I-09 abiertas)
- [x] **Alcance** de cada característica acotado (qué entra y qué NO)
- [x] **Criterios de aceptación / éxito** por característica (44 CA, 43 `[GWT]`)
- [x] **Restricciones** (sin red, stdlib, hooks exit 0, `redact.py`, opt-in, un rol un dueño)
- [ ] **Dependencias externas** identificadas: versión de Chart.js (I-01) y payloads de herramienta de Codex (I-08) sin confirmar
- [x] **Contexto técnico** del proyecto disponible (recon con líneas reales, abajo)
- [x] **Tarifa/hora y supuestos de coste** confirmados (`.claude/rates.json`)

---

## Supuestos económicos (ajustables)

**Coste = (horas × tarifa) + coste de tokens de IA.** Importes en **EUR**.

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | 50 €/h | `.claude/rates.json` `tarifaHora` |
| Modelo IA asumido | claude-opus-4-8 | `rates.json` `modeloIA` |
| Precio input | 5 USD / 1M tokens (4,60 €) | `rates.json`, verificado el 2026-08-18 (hace 58 días: fiable, < 90) |
| Precio output | 25 USD / 1M tokens (23,00 €) | Ídem |
| Precio escritura / lectura de caché | 6,25 / 0,50 USD por 1M | Ídem |
| Tipo de cambio | 1 USD = 0,92 € | ⚠️ supuesto fijo de `rates.json`, no verificado |
| Margen de contingencia | 20 % | Sobre las horas base, humanas e IA |
| Ratio de supervisión | 25 % de las horas IA **+ 1 h por fase** de revisión manual en el navegador (CA-44) | `rates.json` `ratioSupervision`; la hora por fase es supuesto de esta evaluación |
| Ratio tokens→hora-IA | 531.798,5 tok/h | Mediana de 6 muestras medidas de `CALIBRATION.md` |
| Reparto de tokens facturables | 6 % entrada · 80 % escritura de caché · 14 % salida; lectura de caché ≈ 11 × facturables | ⚠️ Perfil de la única ventana medida con desglose en Windows (`usage-meter-transcripts`). Una sola muestra. Contraste: da ≈ 7,0 €/h IA, lo mismo que `training-data-services` midió (750 € / 105,9 h) |

**Método.** Las horas humanas son un juicio por característica, a partir del recon de ficheros y líneas reales. Las horas IA tienen dos partes: la **implementación**, también a juicio, con TDD incluido (constitución §1, LES-005), y la **revisión + corrección**, como línea propia (LES-009). Esa línea se calcula como un factor `f` sobre la implementación, calibrado con el histórico:

| Factor | Valor | Dónde se aplica | Origen en `CALIBRATION.md` |
|--------|-------|-----------------|----------------------------|
| Revisión + corrección, presentación | f = 1,0 | C-02, C-04 | `memory-retrieval` 0,7 (1,84 h sobre ≈ 2,6 h) e `installer-registro-real` 1,17 (8,55 / 7,28) |
| Revisión + corrección, servidor/CSP/contratos | f = 1,5 | C-01 | `graphiti-memory` 2,4 en contratos multi-consumidor; aquí son cuatro contratos que **no** cambian |
| Revisión + corrección, hooks + privacidad + estado | f = 2,0 | C-03 | `session-end-durable-capture` (7 pasadas, 97 gaps) y `graphiti-memory` 2,4 |
| Implementación con hooks + privacidad | ×2 | C-03 | `memory-retrieval` F4 ×2,8; `installer-registro-real` ×5 en tres runtimes (aquí no se escribe su configuración: el registro lo hace `export-interop.py`) |
| Cierre transversal | f = 0,5 | C-05 | Prosa + regeneración; LES-004 |

Tokens facturables = horas IA (con margen) × 531.798,5.

**Calibración aplicada (P2-bis).**

- **LES-009 / LES-001 (la revisión es la partida grande).** La revisión suma 24,75 h de las 42,25 h IA base (59 %). No es una holgura: es la partida que más se ha desviado en el histórico. La sensibilidad está en «Presupuesto total».
- **LES-007 / LES-008.** La referencia humana y la ejecución con agentes van en filas separadas. Las horas humanas **nunca se han validado** (aprendizaje nº 2 de `CALIBRATION.md`), así que su confianza es Baja. El coste de proceso se presupuesta aparte.
- **LES-006.** La spec llega muy madura: 44 CA con fuente, topes con `fichero:línea` y decisiones de negocio ya cerradas. Eso abarata la implementación y es lo que justifica f = 1,0 en las fases de presentación.
- **Ajuste `training-data-services`.** El objetivo «sin gaps» hizo bloqueante cada Minor y disparó ×8. Esta estimación supone **Minor al backlog** y un tope real de 3 intentos por fase. Si no se cumple, se aplica la fila «histórico ×2,4» de la sensibilidad.

**Recon (hechos que mueven la complejidad).**

- `skills/plugin-panel/scripts/build_panel.py` 814 líneas, 10 cambios en 90 días · `serve_panel.py` 507 líneas, con `activity_snapshot` de **222 líneas** en una función (`serve_panel.py:211`, `code-health`).
- `skills/roadmap-dashboard/scripts/build_dashboard.py` 1.181 líneas, **14 cambios en 90 días**: el fichero del ciclo que más se toca. Cuatro comandos lo consumen (`/roadmap-status`, `/pm-backlog`, `/roadmap-metrics`, `/roadmap-brief`), además de `confluence-publish` y `confluence-pull`.
- `agent-kits/shared/agent-activity-store.py` 273 líneas con estado firmado por HMAC, revisiones, `owner.json` y directorio privado. `hooks/opencode-plugin.js` tiene un `setup()` de **229 líneas** (`code-health`).
- Tests existentes de la zona: 13 suites, 3.684 líneas (`test_plugin_panel.py` 728, `test_dashboard.py` 632, `test_agent_activity_store.py` 433, `test_panel_review_server.py` 401…). Son la red de no regresión de CA-28 y CA-44.
- Hotspots que toca C-04 **solo en lectura**: `doctor.py` (36 cambios / 2.336 líneas), `journal.py` (27 / 2.361) y `knowledge-find.py` (21 / 1.716). La spec los usa vía `--json`, sin modificarlos. Si el diseño exige cambiarlos, sube el riesgo.

---

## Evaluación por característica

### C-01 — Base común (Fase 1)

- **Requisito origen**: Fases propuestas F1 · CA-32..CA-41, CA-43
- **Descripción**: generador multi-página con menú común, `aria-current` y salto al contenido. Incluye Chart.js en el plugin con procedencia (versión, origen, SHA-256) y `LICENSE`, CSP sin red en los dos modos, exportación a carpeta, rutas nuevas del servidor (páginas y recurso estático) y paleta con test de contraste. Aplica D-A1: un solo HTML y `dashboard.md`/`--json` intactos.
- **Complejidad**: Alta
- **Esfuerzo**: 24 h base → **28,8 h** · confianza Baja
- **Previsión IA**: 10,5 h (implementación 3,5 h + revisión 5,25 h con f = 1,5, × 1,2) · 4,80 M in / 0,78 M out tok facturables + 61,4 M de lectura de caché · 73,46 €
- **Coste**: (28,8 h × 50 €/h) + tokens = **1.513 €** de referencia · **255 €** de ejecución con agentes (3,62 h de supervisión + tokens)
- **Impacto / áreas afectadas**: `skills/plugin-panel/` (`build_panel.py`, `serve_panel.py`, `references/`), `skills/roadmap-dashboard/` (HTML, según D-A1), `commands/plugin-catalog.md`, `commands/roadmap-status.md`, `agent-kits/shared/copias.json`, `install/` (que el recurso JS viaje con el plugin), tests de panel y dashboard
- **Dependencias y prerequisitos**: D-A1 cerrada por architect; versión de Chart.js elegida (I-01)
- **Riesgos**:
  - **CSP con `file://` (I-01).** El HTML estático de hoy usa `script-src 'unsafe-inline'` en un `<meta>`. Con `file://`, el origen es opaco en varios navegadores, así que `'self'` puede no cubrir el `chart.umd.js` vecino. Hay que probarlo **el primer día** (*spike*), no al final. Si falla, la exportación tendría que llevar el JS en línea con hash, y el fichero único de CA-36 se complica.
  - **Golden files.** Hay que fijar `build_panel.py --json`, `build_dashboard.py --json` y `dashboard.md` **antes** de refactorizar (CA-28, «No regresión»). Sin ellos, la revisión no puede probar que el contrato no cambió.
  - **Activo minificado en el repo.** Chart.js 4 pesa ≈ 200 KB minificado. Puede chocar con `lint_plugin.py` (citas de rutas), con `tests/test_skill_size.py` y con lo que copian `export-interop.py` e `install/`.
- **Incógnitas / preguntas abiertas**: I-01, I-04 (si 64 KiB por respuesta bastan con siete páginas), I-06 (tope de la exportación)

### C-02 — Inicio, Iniciativas y Plan (Fase 2)

- **Requisito origen**: F2 · CA-01..CA-03, CA-05..CA-14
- **Descripción**: Inicio muestra las cifras de cartera con procedencia. Iniciativas muestra un kanban de solo lectura con alertas en texto y gráficos de horas y coste. Plan muestra un kanban por estado del ledger, el detalle de cada `T-XX` (criterios, `Verificación`, gaps de la última revisión, enlace «archivado»), el avance por fase, real vs estimado y el refresco vivo sin perder la tarea abierta.
- **Complejidad**: Media
- **Esfuerzo**: 28 h base → **33,6 h** · confianza Media
- **Previsión IA**: 9,6 h (implementación 4,0 h + revisión 4,0 h con f = 1,0, × 1,2) · 4,39 M in / 0,71 M out tok + 56,2 M de lectura de caché · 67,16 €
- **Coste**: (33,6 h × 50 €/h) + tokens = **1.747 €** de referencia · **237 €** de ejecución con agentes
- **Impacto / áreas afectadas**: proyección de datos reutilizada de `build_dashboard.py` (progreso, procedencia) y `progress-report.py`; lectura de secciones de revisión con el parser del bloque replicado (`ledger-lint.py`/`task-brief.py`, ADR-016); `references/` del panel
- **Dependencias y prerequisitos**: C-01
- **Riesgos**:
  - **Un tercer lector de secciones de revisión.** El detalle de tarea (CA-10) necesita las secciones «Revisión de dos lentes — intento N» y sus gaps. Si se reimplementa en vez de reutilizar el bloque replicado, nace un tercer lector que diverge. Ya hay un precedente de cabecera mal parseada (`intento N:` sin paréntesis).
  - **Cifras iguales a `--json`.** CA-01, CA-02 y CA-11 exigen las mismas cifras que `build_dashboard.py --json`, `progress-report.py` y el «Resumen de progreso» del ledger. Los tests deben comparar contra el script, no contra un oráculo copiado (lección de `usage-meter-transcripts`: 6 de 7 tests no mordían).
- **Incógnitas / preguntas abiertas**: I-02. Se presupuesta solo la rama «no disponible» más el gráfico condicional. Añadir fechas al ledger queda fuera.

### C-03 — Agentes en vivo y eventos de herramienta (Fase 3)

- **Requisito origen**: F3 · CA-04, CA-15..CA-21, CA-42 (eventos)
- **Descripción**: amplía el almacén de actividad con un evento por herramienta: nombre, resumen redactado del argumento, `T-XX` solo si la atribución es cierta, duración y resultado. Se captura desde PreToolUse/PostToolUse (Claude y Codex) y `execute.before/after` (OpenCode), con un historial acotado y recorte por antigüedad. Incluye la página de runs con su línea de tiempo y la actividad reciente en Inicio.
- **Complejidad**: Muy alta
- **Esfuerzo**: 30 h base → **36,0 h** · confianza Baja
- **Previsión IA**: 21,6 h (implementación 3,0 h × 2 por hooks/privacidad = 6,0 h + revisión 12,0 h con f = 2,0, × 1,2) · 9,88 M in / 1,61 M out tok + 126,4 M de lectura de caché · 151,12 €
- **Coste**: (36,0 h × 50 €/h) + tokens = **1.951 €** de referencia · **471 €** de ejecución con agentes
- **Impacto / áreas afectadas**: `agent-kits/shared/agent-activity-store.py`, `agent-activity.py`, `hooks/hooks.json` (PreToolUse/PostToolUse), `hooks/run-hook.mjs`, `hooks/opencode-plugin.js`, `agent-kits/shared/redact.py` (consumidor), `serve_panel.py` (`activity_snapshot`), `interop/` regenerado
- **Dependencias y prerequisitos**: C-01; **D-A2** diseñada y aprobada; respuestas del usuario a I-03, I-05 e I-07; evidencia **citada** de la doc de Codex para I-08 (ajuste de `installer-registro-real`: ninguna decisión que dependa de un tercero se cierra sin cita)
- **Riesgos**:
  - **Hook en cada herramienta.** Hoy el hook de actividad solo salta en SubagentStart/Stop. Pasará a correr en **cada** uso de herramienta, con un presupuesto de 2.000 ms y arranque de node + python. Una regresión de latencia aquí la nota el usuario en todas las sesiones, no solo en el panel.
  - **Concurrencia sobre estado firmado.** Herramientas en paralelo escribirán sobre el mismo historial con revisión y HMAC. Es la familia de `session-end-durable-capture`: estados intermedios sin dueño, 5 de 6 Critical (LES-016).
  - **Privacidad.** El resumen del argumento es texto libre: rutas absolutas del home, correos o secretos. Pasa por `redact.py` y se prueba con su corpus (CA-17, CA-41). La Lente C es obligatoria en esta fase.
  - **Atribución a `T-XX` sin leer transcripts (CA-18).** Puede no ser posible en algún runtime. En ese caso la salida correcta es «sin atribuir», y no hay que forzarla.
- **Incógnitas / preguntas abiertas**: D-A2, I-03, I-05, I-07, I-08

### C-04 — Memoria, Catálogo y Diagnóstico (Fase 4)

- **Requisito origen**: F4 · CA-22..CA-31
- **Descripción**: Memoria es la vista sencilla acordada: gráfico y tabla por tipo/estado/área, bandeja del curador de solo lectura, línea de tiempo con sucesores, relaciones de una entrada a un salto, publicación por backend sin red y journal como citas. Catálogo es lo de hoy con filtros y el `--json` intacto. Diagnóstico es la proyección de `doctor --panel-json`.
- **Complejidad**: Media
- **Esfuerzo**: 22 h base → **26,4 h** · confianza Media
- **Previsión IA**: 7,2 h (implementación 3,0 h + revisión 3,0 h con f = 1,0, × 1,2) · 3,29 M in / 0,54 M out tok + 42,1 M de lectura de caché · 50,37 €
- **Coste**: (26,4 h × 50 €/h) + tokens = **1.370 €** de referencia · **190 €** de ejecución con agentes
- **Impacto / áreas afectadas**: `references/panel-memory.js` y nuevas páginas. Fuentes en solo lectura: `knowledge-find.py --json`/`--related`, `knowledge-curation.py`, `journal.py`, `doctor.py --panel-json`, manifiestos y outbox de `knowledge-services`
- **Dependencias y prerequisitos**: C-01 (la Memoria no depende de C-02 ni de C-03)
- **Riesgos**:
  - **El grafo de relaciones (CA-25).** Chart.js no dibuja grafos. Hará falta un SVG propio pequeño, con lista textual equivalente y navegable por teclado.
  - **Hotspots.** Si alguna fuente no trae lo necesario por `--json` (p. ej. la fecha de publicación de I-09), la tentación es tocar `doctor.py`, `journal.py` o `knowledge-find.py`, los tres hotspots del repo. Debe declararse «sin datos» antes que ampliar sus contratos aquí.
- **Incógnitas / preguntas abiertas**: I-09

### C-05 — Cierre transversal

- **Requisito origen**: Alcance (último punto) · CA-42, CA-44
- **Descripción**: `SKILL.md` de la pieza dueña dentro del tope de 200 líneas (ADR-008). Incluye también la retirada o redirección de la otra, `FLOWS.md` y `observability.md` con sus espejos en `docs/en/`, los dos CHANGELOG, la regeneración de `interop/` (`--check`), casos de `evals/` si cambia una `description` y la réplica Linux de CI antes del push.
- **Complejidad**: Baja
- **Esfuerzo**: 8 h base → **9,6 h** · confianza Media
- **Previsión IA**: 1,8 h (implementación 1,0 h + revisión 0,5 h, × 1,2) · 0,82 M in / 0,13 M out tok + 10,5 M de lectura de caché · 12,59 €
- **Coste**: (9,6 h × 50 €/h) + tokens = **493 €** de referencia · **35 €** de ejecución con agentes
- **Impacto / áreas afectadas**: `docs/`, `docs/en/`, `CHANGELOG.md`, `CHANGELOG.es.md`, `interop/`, `evals/cases/`
- **Dependencias y prerequisitos**: C-01..C-04. El planner puede repartirlo por fase (la documentación de cada página al cerrar su fase).
- **Riesgos**: rojos que solo salen en Linux (CRLF de los `.sh`, rutas). Ver la nota de memoria «verificar en Linux antes de push».
- **Incógnitas / preguntas abiertas**: ninguna

---

## Comparativa

| # | Característica | Complejidad | Horas | Coste € | Tokens | Prioridad | Confianza |
|---|---------------|-------------|-------|---------|--------|-----------|-----------|
| C-01 | Base común (F1) | Alta | 28,8 h | 1.513 € | 5,58 M | Alta 🟠 (bloquea al resto) | Baja |
| C-02 | Inicio, Iniciativas y Plan (F2) | Media | 33,6 h | 1.747 € | 5,11 M | Alta 🟠 (citas 1-2 del usuario) | Media |
| C-03 | Agentes en vivo + eventos (F3) | Muy alta | 36,0 h | 1.951 € | 11,49 M | Media 🟡 | Baja |
| C-04 | Memoria, Catálogo y Diagnóstico (F4) | Media | 26,4 h | 1.370 € | 3,83 M | Media 🟡 | Media |
| C-05 | Cierre transversal | Baja | 9,6 h | 493 € | 0,96 M | — | Media |
| | **Total** | | **134,4 h** | **7.075 €** | **26,96 M** | | |

Horas = referencia humana con margen; coste = referencia humana + tokens; tokens = facturables (sin lectura de caché).

**Por fase (lo que hereda el `planner`; C-05 va con F4 salvo que lo reparta):**

| Fase | Horas humanas | Horas IA (con margen) | Supervisión | Tokens facturables | Tokens € | Ejecución con agentes |
|------|---------------|-----------------------|-------------|--------------------|----------|-----------------------|
| F1 — Base común | 28,8 h | 10,50 h | 3,62 h | 5,58 M | 73,46 € | ≈ 255 € |
| F2 — Iniciativas y Plan | 33,6 h | 9,60 h | 3,40 h | 5,11 M | 67,16 € | ≈ 237 € |
| F3 — Agentes en vivo | 36,0 h | 21,60 h | 6,40 h | 11,49 M | 151,12 € | ≈ 471 € |
| F4 — Memoria, Catálogo, Diagnóstico + cierre | 36,0 h | 9,00 h | 3,25 h | 4,79 M | 62,96 € | ≈ 225 € |
| **Total** | **134,4 h** | **50,70 h** | **16,68 h** | **26,96 M** | **354,71 €** | **≈ 1.188 €** |

---

## Presupuesto total

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 112 h × 50 €/h | 5.600,00 € |
| Margen de contingencia | +20 % sobre desarrollo base (22,4 h) | 1.120,00 € |
| Tokens IA (input) | 1,62 M × 5 USD/M × 0,92 | 7,44 € |
| Tokens IA (escritura de caché) | 21,57 M × 6,25 USD/M × 0,92 | 124,03 € |
| Tokens IA (output) | 3,77 M × 25 USD/M × 0,92 | 86,82 € |
| Tokens IA (lectura de caché) | ~296,6 M × 0,50 USD/M × 0,92 | 136,43 € |
| **Total estimado (con margen)** | | **≈ 7.075 €** |

**Coste de ejecución con agentes (lo que se espera gastar de verdad):** 16,68 h de supervisión × 50 €/h = 833,75 € + 354,71 € de tokens = **≈ 1.188 €**.

**Coste de proceso (LES-008, línea aparte).** Spec medida: 1,30 € (0,14 h IA). Esta evaluación, medida: 5,98 € (0,52 h IA, 31m). Design, plan y retro se estiman en ≈ 0,8 h IA (≈ 425 k tokens facturables), **≈ 5,6 €**. No se suman al total de arriba.

**Sensibilidad al factor de revisión + corrección.**

| Escenario | Horas IA | Supervisión | Tokens € | Ejecución con agentes |
|-----------|----------|-------------|----------|-----------------------|
| f = 0,7 en todo (optimista, `memory-retrieval`) | 35,7 h | 12,9 h | 250 € | ≈ 896 € |
| **Mezcla de esta evaluación** (1,5 · 1,0 · 2,0 · 1,0 · 0,5) | **50,7 h** | **16,7 h** | **355 €** | **≈ 1.188 €** |
| f = 2,4 en todo (histórico `graphiti-memory`) | 71,4 h | 21,9 h | 500 € | ≈ 1.592 € |

Las horas humanas de referencia no cambian (134,4 h). Un caso como `training-data-services` (f ≈ 7,8, Minor bloqueantes) llevaría la ejecución a ≈ 3.800 €. Para evitarlo están el tope de 3 intentos y los Minor al backlog.

---

## Productividad IA (humano vs. IA)

| KPI | Valor |
|-----|-------|
| Horas humanas estimadas | 134,4 h (112 h base) |
| Horas IA (ejecución) | 50,7 h (42,25 h base: 17,5 h de implementación + 24,75 h de revisión y corrección) |
| Supervisión humana | 16,68 h (12,68 h = 25 % de las horas IA + 4 h de revisión manual por fase, CA-44) |
| **Horas totales (IA + supervisión)** | **67,38 h** |
| Horas ahorradas | 67,03 h |
| **Ahorro** | **49,9 %** |
| **Multiplicador de productividad** | **×2,0** |
| FTE equivalentes *(opcional)* | 0,42 |

> Todas las horas llevan ya el margen de contingencia (+20 %). El multiplicador es bajo frente a otras iniciativas porque la revisión pesa más que la implementación (59 % de las horas IA base). También porque el usuario revisa cada fase en el navegador, algo que la IA no hace por él. Las horas humanas de referencia no se han validado nunca: confianza Baja.

---

## Recomendación

- **Veredicto**: **go condicionado**.
  - **F1, F2 y F4: go** en cuanto architect cierre D-A1 en `design.md`.
  - **F3: go condicionado** a cuatro condiciones:
    1. D-A2 diseñada, con una sección «estados intermedios y su recuperación» (ajuste de `session-end-durable-capture`).
    2. El usuario fija la latencia aceptable por evento (I-05) y el tope del historial (I-03).
    3. La evidencia de los payloads de herramienta de Codex está citada de su doc (I-08). Sin ella, Codex se declara «no emite eventos de herramienta» y CA-42 sigue cumpliéndose.
    4. La Lente C es obligatoria en las tareas de captura.
- **Quick wins** (bajo coste, alto valor): **C-02**, la mejor relación valor/coste: responde a las citas 1 y 2 del usuario con fuentes que ya existen y tienen tests. **C-04**, el mismo patrón, pero responde a la cita 4.
- **Costosas / a valorar**: **C-03**, con el 43 % de las horas IA, el 43 % de los tokens y todo el riesgo de hooks y privacidad. **C-01**, que es costosa por necesidad: bloquea al resto y lleva la CSP con `file://`.
- **Orden sugerido**: **C-01 → C-02 → C-04 → C-03 → C-05**.
  - C-01 abre el camino y valida I-01 con un *spike* el primer día.
  - C-02 entrega lo que más pidió el usuario.
  - **C-04 adelanta a C-03** sobre el orden de la spec. No depende de ella, y así las condiciones de F3 tienen tiempo de cerrarse sin parar el ciclo.
  - Si el usuario prefiere mantener su orden (F3 antes que F4), el coste no cambia. Lo único que cambia es que F3 puede bloquear el avance.
- **Fuera de alcance recomendado**: añadir fechas de cierre por tarea al ledger para el burndown (I-02). Toca `ledger-lint.py` y el bloque replicado (ADR-016) y merece su propia spec. Si architect lo pide dentro, hay que re-presupuestar C-02.

---

## Riesgos transversales

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| **El bucle de revisión se desborda** (44 CA, CSP, servidor, WCAG 2.2 y tres runtimes; histórico f = 2,4 a 7,8) | Alta | Alto | Revisión como línea propia por fase; Minor al backlog; tope real de 3 intentos por fase; sensibilidad publicada; anotar en `/retro` el `f` real de cada fase para calibrar |
| **Latencia y concurrencia del hook por herramienta (F3)** | Media | Alto | Medir la latencia del hook actual antes de diseñar (I-05); D-A2 con estados intermedios; tests de escrituras concurrentes y de exit 0 con fallo de escritura; Lente C |
| **D-A1 rompe a un consumidor o deja dos dashboards** (`build_dashboard.py` es el hotspot del ciclo, 14 cambios / 90 d, y tiene 6 consumidores) | Media | Alto | Golden files de `--json`/`dashboard.md`/`build_panel --json` en la primera tarea; lista de consumidores en `design.md` antes de mover nada (ajuste de `graphiti-memory`) |
| **CSP con `file://` y el Chart.js local** (I-01) | Media | Medio | *Spike* en la primera tarea de F1, en Chromium y Firefox; plan B (JS en línea con hash) decidido antes de seguir |
| **Datos personales en la exportación o en eventos** (CA-41) | Baja | Alto | Fixture con home y correo falsos; `grep` sobre toda la salida en los dos modos; todo texto por `redact.py` |
| **Diferencias Windows/Linux en CI** | Media | Bajo | Réplica de `ci.yml` en contenedor con `core.autocrlf=false` antes de cada push |
| **Respuestas por encima de 64 KiB con siete páginas** (I-04) | Baja | Medio | Una respuesta por página, no un volcado único; architect fija el tope en el diseño |

---

## Siguiente paso

1. **Architect (obligatorio, lo fija la spec)**: cierra D-A1 y D-A2 en `design.md` y responde I-01, I-02, I-04, I-08 e I-09.
2. **Usuario**: fija I-03 (tope del historial), I-05 (latencia por evento), I-06 (carga y tamaño de la exportación) e I-07 (longitud del resumen).
3. **Planner**: con el diseño aprobado, genera `improvement-plan.md` y `tasks.md` en esta carpeta. Propuesta de aprobación: **C-01, C-02, C-04 y C-05 sin más condiciones que D-A1; C-03 cuando se cumplan las condiciones 1-4 de la Recomendación**, en el orden sugerido.

El `planner` hereda las horas, los tokens y los costes **por fase** de esta evaluación, incluidas las líneas de revisión y la sensibilidad, y no re-estima desde cero. Al crear el plan, actualiza la fila **Plan** de esta evaluación y el campo `plan:` de la spec.

---

## Changelog

- 2026-10-15 — Evaluación inicial (evaluator). Estado `en-revision`.
