---
design: design.md
test-plan: test-plan.md
generacion:               # usage-meter.py close
  inicio: 2026-10-15T09:41:41Z
  fin: 2026-10-15T10:03:37Z
  fuente: medido
  fuente_id: src-d2ceb5c719af848b4c213bb2d521d0f003976923acb613d7512912ccbeb6a09e
  ventana_id: win-0d642e69c69348c2b05ab888c500c6dc
  revision_medicion: 1
  medicion_persistida: true
  tokens_reales: { entrada: 84, salida: 114551, cache_creacion: 425511, cache_lectura: 6785286 }
  tokens_procedencia: transcript
  tokens_cobertura: completa
  coste_procedencia: estimado_tarifa
  coste_cobertura: completa
  eur: 8.20
  horas_ia: 1.02
  duracion: 1h 1m           # duracion_reloj: 22m
  ratio_usado: 531798.5     # CALIBRATION.md (mediana de 6)
  avisos: ["CALIBRATION: 7 filas marcadas (estimado) fuera de la mediana", "tarifa verificada el 2026-08-18", "2 transcripts leídos (1 de subagente)"]
---

# 2026-10-15-panel-redesign

> Panel local de siete páginas con menú común, kanban de solo lectura, gráficos Chart.js incluidos en el plugin y registro opt-in de eventos de herramienta, en cuatro fases ejecutadas en el orden F1 → F2 → F4 → F3.

| | |
|---|---|
| **Fecha** | 2026-10-15 |
| **Estado** | borrador |
| **Tipo** | Nueva Funcionalidad |
| **Prioridad** | Media |
| **Solicitante** | Usuario del repo (conversación del 2026-10-15) |
| **Responsable** | `implementer` vía `/dev-cycle` (flujo completo) |
| **Spec** | [`spec.md`](spec.md) |
| **Evaluación** | [`evaluation.md`](evaluation.md) |
| **Diseño** | [`design.md`](design.md) — opción elegida O1+O5 (D-A1 = O1, D-A2 = O5) |

---

## Cuadro de mando

| Métrica | Estimado | Real | Confianza |
|--------|---------|------|-----------|
| Tiempo humano | **136,8h** (114h base +20 %) | 0h | Baja |
| Tiempo IA (ejecución) | **51,9h** (+ 17,0h supervisión) | 0h | Baja |
| Coste total | **≈ 7.203 €** de referencia · **≈ 1.212 €** de ejecución con agentes | 0 € | Media (precios) · Baja (horas IA) |
| Tokens IA | **27,60 M facturables** (in 23,74 M / out 3,86 M) + ~304 M de lectura de caché | 0 | Baja |
| Multiplicador productividad | **×2,0** | — | — |
| Tareas | **54** | 0 hechas | — |

---

## Estimación por fase

Orden de ejecución: **F1 → F2 → F4 → F3**. Las cifras se heredan de `evaluation.md` por fase, con dos diferencias declaradas (ver «Diferencias con la evaluación»).

| Fase | Estimado (h humanas) | Horas IA | Tokens (in / out) | Coste € (referencia) |
|------|-------------|----------|-------------------|---------|
| Fase 1 — Base común (16 tareas) | 28,8 | 10,5 | 4,80 M / 0,78 M | 1.513 |
| Fase 2 — Inicio, Iniciativas y Plan (13 tareas) | 36,0 | 10,8 | 4,94 M / 0,80 M | 1.876 |
| Fase 4 — Memoria, Catálogo y Diagnóstico (10 tareas) | 26,4 | 7,2 | 3,29 M / 0,54 M | 1.370 |
| Fase 3 — Agentes en vivo + cierre transversal (15 tareas) | 45,6 | 23,4 | 10,70 M / 1,74 M | 2.444 |
| **Total** | **136,8h** | **51,9h** | **23,74 M / 3,86 M** | **≈ 7.203 €** |

**Ejecución con agentes por fase** (supervisión × 50 €/h + tokens): F1 ≈ 255 € · F2 ≈ 261 € · F4 ≈ 190 € · F3 ≈ 506 € · **total ≈ 1.212 €**.

### Diferencias con la evaluación

| Diferencia | Efecto | Motivo |
|---|---|---|
| **C-05 (cierre transversal) pasa de F4 a F3** | F4: 36,0h → 26,4h humanas, 9,0h → 7,2h IA. F3: 36,0h → 45,6h, 21,6h → 23,4h IA. Total sin cambio | La evaluación lo sumaba a F4 «salvo que lo reparta». Con F3 ejecutada la última, el cierre (réplica Linux, `--check`, evals, multi-runtime) va con la última fase. La documentación de cada página va en su fase (T-15, T-28, T-38, T-52) |
| **Campo `- **Cerrada**:` dentro del alcance (I-02)** | +2,4h humanas (2h base), +1,2h IA (0,6h implementación + 0,6h revisión), +0,3h supervisión, +0,64 M tokens, +8,4 € en tokens → **+128 € de referencia y +23 € de ejecución**, en F2 (T-22 y T-29) | La evaluación lo dejaba fuera («re-presupuestar C-02 si architect lo pide»). `design.md` §2.4 I-02 lo incluye y el orquestador lo pide. Toca `ledger-lint.py` y, si el patrón de campos está replicado, sus copias (ADR-016) |

Sin re-estimar desde cero: el resto de horas, tokens y factores de revisión (f = 1,5 · 1,0 · 2,0 · 1,0 · 0,5) son los de la evaluación, repartidos en tareas.

---

## Presupuesto económico

**Coste = (horas × tarifa) + coste de tokens de IA.** Todos los importes en **EUR**.

### Supuestos (ajustables)

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | 50 €/h | `.claude/rates.json` `tarifaHora` |
| Modelo IA asumido | claude-opus-4-8 | `rates.json` `modeloIA` (el implementer usa `opus` por `dev.json` `modelos`) |
| Precio input | 5 USD / 1M tokens (4,60 €) | `rates.json`, verificado el 2026-08-18 (58 días) |
| Precio output | 25 USD / 1M tokens (23,00 €) | Ídem |
| Precio escritura / lectura de caché | 6,25 / 0,50 USD por 1M | Ídem |
| Tipo de cambio | 1 USD = 0,92 € | ⚠️ supuesto fijo de `rates.json`, no verificado |
| Margen de contingencia | 20 % | Sobre las horas base, humanas e IA |
| Supervisión | 25 % de las horas IA + 1h por fase de revisión manual (CA-44) | Heredado de la evaluación |
| Ratio tokens→hora-IA | 531.798,5 tok/h | Mediana de 6 muestras de `CALIBRATION.md` |
| Coste medio por token facturable | 13,16 € / 1M (incluye la lectura de caché asociada) | 354,71 € / 26,96 M de la evaluación |

### Desglose

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 114h × 50 €/h | 5.700,00 € |
| Margen de contingencia | +20 % sobre desarrollo base (22,8h) | 1.140,00 € |
| Tokens IA (input) | 1,66 M × 5 USD/M × 0,92 | 7,63 € |
| Tokens IA (escritura de caché) | 22,08 M × 6,25 USD/M × 0,92 | 126,97 € |
| Tokens IA (output) | 3,86 M × 25 USD/M × 0,92 | 88,78 € |
| Tokens IA (lectura de caché) | ~303,6 M × 0,50 USD/M × 0,92 (redondeo al total por fase) | 139,77 € |
| **Total estimado (con margen)** | | **≈ 7.203 €** |

**Coste de ejecución con agentes:** 16,98h de supervisión × 50 €/h = 848,75 € + 363,15 € de tokens = **≈ 1.212 €**.

**Sensibilidad (de la evaluación, escalada):** f = 0,7 en todo → ≈ 915 € de ejecución; f = 2,4 en todo → ≈ 1.620 €. El tope de 3 intentos por fase y los Minor al backlog son la defensa contra el caso `training-data-services` (×8).

**Coste de proceso (LES-008, aparte):** spec 1,30 € · evaluación 5,98 € · diseño 3,32 € · este plan: ver `generacion:`. No se suma al total.

---

## Previsión de tokens (por fase)

Base: claude-opus-4-8 · precios de la tabla de supuestos.

| Fase | Input (tok) | Output (tok) | Total facturable (tok) | Coste € |
|------|------------|-------------|-------------|---------|
| Fase 1 | 4,80 M | 0,78 M | 5,58 M | 73,47 |
| Fase 2 | 4,94 M | 0,80 M | 5,74 M | 75,57 |
| Fase 4 | 3,29 M | 0,54 M | 3,83 M | 50,38 |
| Fase 3 | 10,70 M | 1,74 M | 12,44 M | 163,73 |
| **Total** | **23,74 M** | **3,86 M** | **27,60 M** | **363,15 €** |

**Método de estimación:** tokens facturables = horas IA con margen × 531.798,5 (ratio calibrado). Reparto 86 % entrada (incluida la escritura de caché) / 14 % salida, y lectura de caché ≈ 11 × facturables: perfil de la única ventana medida con desglose (`usage-meter-transcripts`), igual que la evaluación. Input y output por tarea en `tasks.md`.

---

## Productividad IA (humano vs. IA)

| KPI | Valor |
|-----|-------|
| Horas humanas estimadas | 136,8h (114h base) |
| Horas IA (ejecución) | 51,9h (43,25h base: 18,0h de implementación + 25,25h de revisión y corrección) |
| Supervisión humana | 17,0h (12,98h = 25 % de las horas IA + 4h de revisión manual por fase) |
| **Horas totales (IA + supervisión)** | **68,9h** |
| Horas ahorradas | 67,9h |
| **Ahorro** | **49,7 %** |
| **Multiplicador de productividad** | **×2,0** |
| FTE equivalentes *(opcional)* | 0,42 |

> Horas mostradas **con el margen de contingencia (+20 %)** ya aplicado. El multiplicador es bajo porque la revisión pesa más que la implementación (58 % de las horas IA) y el usuario revisa cada fase en el navegador. Las horas IA de revisión están en la tarea de cierre de cada fase (T-16, T-29, T-39, T-54).

---

## Resumen ejecutivo

Sustituye el panel de una página de `plugin-panel` y el `dashboard.html` de `roadmap-dashboard` por un único panel local de siete páginas (Inicio, Iniciativas, Plan, Agentes en vivo, Memoria, Catálogo, Diagnóstico), servido en `127.0.0.1` o exportado a carpeta, sin red y con Chart.js incluido. `plugin-panel` queda como dueño único de la presentación y `roadmap-dashboard` como proveedor de datos con `--json` y `--md` intactos (D-A1 = O1). La actividad de agentes añade un evento por herramienta, asíncrono y opt-in, que no añade latencia síncrona a quien no lo activa (D-A2 = O5). Responde a las cinco citas del usuario de la spec.

### Objetivos

- 7 páginas con el mismo menú, accesibles por teclado (WCAG 2.2 AA) y con tabla equivalente en cada gráfico: CA-32, CA-37, CA-39.
- Cero peticiones a otros orígenes en servido y exportado, y Chart.js único con hash verificado por test: CA-35, CA-36.
- Contratos `build_dashboard.py --json`, `dashboard.md` y `build_panel.py --json` iguales a sus goldens (este último solo cambia en los registros de hook nuevos): CA-28 y «No regresión».
- Ningún dato ausente pintado como 0 y ningún dato personal en la salida: CA-40, CA-41.
- Eventos de herramienta con resumen redactado, atribución solo con certeza y 0 ms síncronos añadidos en Claude y Codex: CA-16 a CA-21, I-05.

---

## Datos necesarios para un informe completo

- [x] **Requisitos funcionales** confirmados por el solicitante (spec `aprobada`, 44 CA)
- [x] **Alcance** cerrado (qué entra y qué NO entra en esta iteración)
- [x] **Criterios de éxito / métricas** acordados
- [x] **Accesos y credenciales** necesarios: ninguno (todo local)
- [x] **Entornos** disponibles: local; datos de prueba = fixtures de T-01
- [x] **Stakeholders** identificados: el usuario revisa cada fase en el navegador (M-01..M-04)
- [ ] **Dependencias externas** mapeadas: Playwright y sus navegadores no están instalados (`agent-kits/qa/runner/` sin `node_modules`): hace falta permiso del usuario para el spike T-03 y para `qa`
- [ ] **Restricciones** conocidas: I-06 (tiempo de carga y tamaño máximo de la exportación) sigue sin cifra del usuario; I-03/I-05 se toman del diseño y se confirman en T-40
- [x] **Tarifa/hora y supuestos de coste** confirmados (`.claude/rates.json`)

---

## Análisis de impacto

- **`skills/plugin-panel/scripts/`** — `build_panel.py` (CLI `--export`, retira `--html`), `serve_panel.py` (rutas de página, activos de lista blanca, nonce en todo `<script>`, API nuevas), nuevos `panel_pages.py` y `panel_data.py`.
- **`skills/plugin-panel/assets/`** — nuevo: CSS, `panel-core.js`, `panel-charts.js`, `panel-graph.js`, `page-*.js`, los cuatro JS vivos movidos desde `references/` y `vendor/chart.js/`.
- **`skills/roadmap-dashboard/scripts/build_dashboard.py`** — extrae `vista_json()` sin cambio de bytes; retira `--html` y `render_html()`.
- **`agent-kits/shared/`** — nuevo `ledger-view.py`; `ledger-lint.py` (campo `Cerrada`); `redact.py` (`anonimizar`, `Authorization: Basic`); `agent-activity.py` y `agent-activity-store.py` (eventos, ventanas, `events.json`).
- **`hooks/`** — `hooks.json` (grupos `PostToolUse`/`PostToolUseFailure` asíncronos), `run-hook.mjs` (atajo sin opt-in), `opencode-plugin.js` (binding sin `await`).
- **`scripts/export-interop.py`** e **`interop/**`** — matcher del grupo de actividad en Codex; regeneración.
- **Comandos y agentes** — `commands/plugin-catalog.md`, `commands/roadmap-status.md`, `commands/dev-cycle.md`, `agents/implementer.md`.
- **Tests** — goldens nuevos y migración de 13 suites existentes (`design.md` §5.3); huellas revisadas de `tests/test_graphiti_security.py` (launcher y almacén).
- **Docs** — `docs/PLUGIN-PANEL.md`, `docs/FLOWS.md`, `docs/observability.md` (+ espejos EN), `docs/INTEROP.md`, `docs/agents/ROLES.md`, `docs/agents/CONTRACTS.md`, `docs/PROJECT-EXTENSIONS.md` (+EN), `docs/README.md` (+EN).

---

## Cambios arquitectónicos

Se toman de [`design.md`](design.md) sin rediseñar (§4):

- **D-A1 = O1.** `plugin-panel` es el único generador HTML; `roadmap-dashboard` conserva `scan`, `--md`, `--metrics-md` y `--json` y retira el HTML. `/plugin-catalog` abre el panel (`--export <dir>` | `--serve`, `--page`); `/roadmap-status` mantiene `dashboard.md` y exporta el panel a `docs/roadmap/panel/`. Relación documentada en `ROLES.md` (ADR-011, caso «documentar explícitamente»).
- **D-A2 = O5.** `PostToolUse` (+ `PostToolUseFailure` en Claude) con `async: true`; OpenCode `execute.after` sin esperar al hijo; atajo en `run-hook.mjs` que no lanza Python sin opt-in. Atribución a `T-XX` solo por la ventana declarada de `usage-meter.py`. Almacén `events.json` (500 eventos / 256 KiB / 24 h).
- **CSP.** Servido: nonce en todas las etiquetas `<script>`. Exportado: sin JS inline, `script-src 'self' file:`; respaldo determinista con hash si el spike T-03 falla en algún motor.
- **API por debajo de 64 KiB.** `api/cartera`, `api/plan-<id16>`, `api/plan-<id16>-<T-XX>`, `api/actividad-runs`, `api/actividad-run-<key16>` (diseño) y **`api/memoria`** (añadida por este plan: el diseño no asigna ruta a la vista general de Memoria y `api/memory` solo admite `search`/`show`/`related`).
- **Catálogo y Diagnóstico en servido** llevan la instantánea del inventario de arranque incrustada, como hoy (`serve_panel.py:459-470`); no hay API nueva para ellos. Matiza el «las páginas HTML no llevan datos en modo servido» de `design.md` §2.4 I-04.
- **Memoria** reutiliza `agent-kits/shared/knowledge-view.py` (proyección ya usada por el panel, CONTRACTS E38-E42) antes que llamar a `knowledge-find`/`knowledge-curation`/`journal` por separado.
- **Decisión propuesta al Curator:** ya existe el candidato del architect (`docs/knowledge/candidates/pending/2026-10-15-plugin-panel-dueno-unico-de-la-presentacion.md`). Este plan no cierra ninguna alternativa nueva que cruce el umbral de `knowledge-write.md`; no propone candidatos propios.

---

## Archivos a crear/modificar

| Archivo | Acción | Propósito |
|---------|--------|-----------|
| `skills/plugin-panel/scripts/panel_pages.py` | Crear | Plantilla común y render por página (T-05) |
| `skills/plugin-panel/scripts/panel_data.py` | Crear | Proyecciones de solo lectura con ausencias `null` (T-17 en adelante) |
| `skills/plugin-panel/assets/**` | Crear / mover | CSS, JS comunes, páginas, JS vivos movidos, `vendor/chart.js/` |
| `skills/plugin-panel/scripts/build_panel.py` | Modificar | `--export`, `--page`; retira `--html` (T-08) |
| `skills/plugin-panel/scripts/serve_panel.py` | Modificar | Rutas, activos, nonce, API nuevas (T-11, T-17, T-23, T-24, T-30, T-48) |
| `skills/plugin-panel/references/panel.html` | Retirar | Sustituido por la plantilla (T-12) |
| `skills/roadmap-dashboard/scripts/build_dashboard.py` | Modificar | `vista_json()`; retira `--html` (T-13, T-14) |
| `agent-kits/shared/ledger-view.py` | Crear | Proyección pura de un `tasks.md` (T-21) |
| `agent-kits/shared/ledger-lint.py` | Modificar | Campo `Cerrada` (T-22) |
| `agent-kits/shared/redact.py` | Modificar | `anonimizar` (T-04); `Authorization: Basic` (T-42) |
| `agent-kits/shared/agent-activity.py` · `agent-activity-store.py` | Modificar | Proyección, eventos, ventanas, `events.json` (T-41..T-44) |
| `hooks/hooks.json` · `hooks/run-hook.mjs` · `hooks/opencode-plugin.js` | Modificar | Registro asíncrono, atajo, binding (T-45..T-47) |
| `scripts/export-interop.py` · `interop/**` | Modificar / regenerar | Matcher de actividad en Codex (T-45) |
| `commands/plugin-catalog.md` · `commands/roadmap-status.md` · `commands/dev-cycle.md` · `agents/implementer.md` | Modificar | Entrada del panel, redirección, `Cerrada` (T-08, T-14, T-22) |
| `tests/test_panel_*.py` (nuevos y migrados), `tests/test_panel_contract_golden.py`, `tests/fixtures/panel-redesign/**`, `tests/e2e/panel-csp-spike.mjs` | Crear / modificar | Goldens, páginas, API, spike |
| `docs/**` (ver «Análisis de impacto») | Modificar | Documentación por fase con espejos EN |

---

## Dependencias y prerequisitos

- Spec `aprobada`, evaluación con go condicionado y `design.md` `aprobado` (O1+O5): cumplido.
- **F1, F2, F4: sin más condiciones.** Cada fase depende del cierre de la anterior (T-16 → T-17, T-29 → T-30, T-39 → T-40).
- **F3 condicionada** a las cuatro condiciones de la evaluación, comprobadas en **T-40** antes de tocar el hook: (1) sección «estados intermedios y su recuperación» en `design.md`, (2) el usuario confirma I-05 (0 ms síncronos) e I-03 (500 / 256 KiB / 24 h), (3) evidencia de Codex citada con URL, (4) Lente C obligatoria en T-54.
- Playwright y sus navegadores, con permiso del usuario, para T-03 y para `qa`.

---

## Criterios de aceptación (global)

- [ ] Los 44 CA de la spec cumplidos y trazados: cada `[GWT]` en `test-plan.md` (`coverage-check.py` sin `gwt_sin_cubrir`).
- [ ] Goldens de T-01 iguales al cerrar, salvo el diff revisado de hooks en `panel.json` (T-51).
- [ ] Un solo generador HTML en el plugin (ADR-011).
- [ ] `lint_plugin.py`, `evals/check.py`, `export-interop.py --check` y las suites de CA-44 en verde al cerrar cada fase, también en la réplica Linux (T-53).
- [ ] El usuario aprueba M-01..M-04.

---

## Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| El bucle de revisión se desborda (histórico f = 2,4 a 7,8) | Alta | Alto | Revisión como línea propia por fase; tope de 3 intentos; Minor al backlog; `/retro` anota el `f` real |
| `script-src 'self' file:` no funciona en algún motor con `file://` | Media | Alto | Spike T-03 el primer día, antes de la plantilla; respaldo con hash decidido allí |
| El hook por herramienta añade latencia o pierde integridad bajo concurrencia | Media | Alto | O5 asíncrono, atajo sin opt-in (T-46), CAS y tests de concurrencia (T-43), latencia medida (T-40, T-46), Lente C (T-54) |
| Retirar `--html` rompe a un consumidor | Media | Medio | Goldens (T-01); los 13 consumidores de `dashboard.html`/`--html` en el mismo cambio (T-14); `lint_plugin.py` avisa de citas rotas |
| Un tercer lector de secciones de revisión diverge | Media | Medio | `ledger-view.py` importa los parsers de `ledger-lint.py` (T-21); la Lente A lo comprueba |
| `Cerrada` toca un bloque replicado (ADR-016) | Media | Medio | T-22 actualiza las copias declaradas en el mismo cambio; `test_copias_declaradas` |
| Huellas de `test_graphiti_security.py` cambian (launcher y almacén) | Segura | Medio | Cambios en bloques aislados; revisión explícita en T-54 |
| Datos personales en la exportación o en eventos | Baja | Alto | `redact.anonimizar` (T-04) en todo texto; grep de CA-41 en ambos modos (T-08, T-51) |
| Tamaño del activo minificado choca con linter, instalador o export | Media | Bajo | Comprobado en T-02; instalador en T-14 |
| Rojos que solo salen en Linux | Media | Bajo | Réplica de `ci.yml` con `core.autocrlf=false` (T-53) |

---

## Métricas de éxito

- Las 5 citas del usuario tienen su página aprobada en la revisión manual de la fase que las cubre (M-02: citas 1-3; M-03: cita 4; M-04: cita 5).
- 0 peticiones a otros orígenes y 0 `securitypolicyviolation` en E2E-02/E2E-04.
- Latencia síncrona añadida por herramienta medida en T-46: 0 ms en Claude y Codex con la captura desactivada y activada.
- `f` real de revisión por fase registrado en `/retro` frente al presupuestado (1,5 · 1,0 · 1,0 · 2,0).

---

## Changelog del plan

| Fecha | Cambio | Autor |
|-------|--------|-------|
| 2026-10-15 | Creación del plan: 4 fases en orden F1 → F2 → F4 → F3, 54 tareas; C-05 movido a F3 y campo `Cerrada` dentro del alcance (diferencias declaradas); `api/memoria` añadida | planner |

---

## Siguiente paso

Con el **OK del plan** del usuario (puerta de control), el agente **`implementer`** lo ejecuta fase a fase sobre la rama `feat/panel-redesign`, marcando `tasks.md` como **ledger canónico** (checkbox + estado por tarea), con TDD (`dev.json` `tdd: true`) y cobertura mínima del 90 % (`tests.coberturaMinima`). Cada fase cierra con su revisión de dos lentes y la revisión visual del usuario antes de abrir la siguiente. Al terminar, handoff a `qa` con `test-plan.md` y cierre con `documenter`.
