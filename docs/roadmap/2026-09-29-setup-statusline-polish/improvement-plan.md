---
design: n/a               # sin paso de diseño; la ADR de T-09 (architect) cubre el encaje de C-07
test-plan: n/a (sin UI)
riesgo: medio             # piloto de sdd-proporcional
generacion:
  inicio: 2026-09-29T20:47:59Z
  fin: 2026-09-29T20:59:00Z
  fuente: estimado        # el meter degradó: carpeta de transcripciones no disponible  # ventana compartida con improvement-plan.md
  tokens_reales: null     # sin medición; estimación a juicio
  eur: null
  horas_ia: 0.18          # estimado = duración de reloj; no derivado de tokens
  duracion: 11m
  ratio_usado: 479326     # CALIBRATION.md (mediana de 5)
---

# 2026-09-29-setup-statusline-polish

> Pulido de `/setup`, statusline y puertas: 9 puntos de la spec en una iniciativa de riesgo medio, con quick wins primero y el alta en `projects.yaml` bloqueada por una ADR.

| | |
|---|---|
| **Fecha** | 2026-09-29 |
| **Estado** | borrador |
| **Tipo** | Mejora / Bugfix / Infra |
| **Prioridad** | Media |
| **Solicitante** | usuario (vía `/pm-cycle`) |
| **Responsable** | planner → implementer |
| **Spec** | [`spec.md`](spec.md) |
| **Evaluación** | [`evaluation.md`](evaluation.md) |
| **Diseño** | n/a (ADR de T-09 para C-07) |

---

## Cuadro de mando

| Métrica | Estimado | Real | Confianza |
|--------|---------|------|-----------|
| Tiempo humano | **54,8 h** (45,7 h base +20 %) | 0 h | Baja |
| Tiempo IA (ejecución) | **14,63 h** (+ 3,66 h supervisión) | 0 h | Baja |
| Coste total (referencia humana) | **≈ 2832 €** | 0 € | Media |
| Coste con agentes | **≈ 275 €** | 0 € | Media |
| Tokens IA | **7,01 M facturables** (in 6,03 M / out 0,98 M) | 0 | Baja |
| Multiplicador productividad | **×3,0** | — | — |
| Tareas | **14** | 0 hechas | — |

> Hereda las cifras por característica de `evaluation.md` (52,8 h humanas, 14,13 h IA, ≈ 2.729 € / ≈ 266 €). **Diferencia declarada:** +2 h humanas y +0,5 h IA por T-09 (ADR de `architect`, que la evaluación no contaba). La revisión ×1,5 ya está dentro de las horas IA de cada tarea (supuesto de `sdd-proporcional`, sin calibrar).

---

## Estimación por fase

| Fase | Estimado (h humanas) | H. IA | Tokens (in / out) | Coste € (ref. humana) |
|------|------|------|-------------------|---------|
| Fase 1 — Estabilizar la suite (tests deterministas) | 4,8 | 0,99 | 408k / 66k | 246 |
| Fase 2 — Quick wins de visibilidad y puertas | 14,4 | 3,42 | 1410k / 230k | 742 |
| Fase 3 — `/doctor`: tope estricto de la línea kwipu | 3,6 | 0,72 | 297k / 48k | 185 |
| Fase 4 — ADR de diseño y `id_prefix` / `group_id` | 14,0 | 4,10 | 1690k / 275k | 726 |
| Fase 5 — Alta segura en `projects.yaml` (bloqueada por la ADR) | 14,4 | 4,50 | 1855k / 302k | 748 |
| Fase 6 — Cierre, documentación y réplica en Linux | 3,6 | 0,90 | 371k / 60k | 186 |
| **Total** | **54,8 h** | **14,63 h** | **6031k / 982k** | **2832 €** |

---

## Presupuesto económico

**Coste = (horas × tarifa) + coste de tokens de IA.** Importes en **EUR**.

### Supuestos (ajustables)

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | 50 €/h | `.claude/rates.json` |
| Modelo IA asumido | claude-opus-4-8 | `rates.json` |
| Precio tokens | 5 / 25 USD por 1M (in / out) | `rates.json`, verificado 2026-08-18 (< 90 días) |
| Tipo de cambio | 1 USD = 0,92 € | ⚠️ supuesto fijo de `rates.json` |
| Margen de contingencia | 20 % | sobre horas base humanas e IA |
| Supervisión | 25 % de las horas IA | `rates.json` |
| Ratio tokens→hora-IA | 479.326 tok/h | mediana de `CALIBRATION.md` |
| **Multiplicador de revisión (riesgo medio)** | **×1,5** sobre la implementación IA | supuesto de `sdd-proporcional` (aprobada, sin calibrar); el histórico está en ×2,2-×3,4 |
| Coste de tokens | ≈ 13,16 € por millón facturable | 89,1 € / 6,77 M de la evaluación (incluye lectura de caché) |

### Desglose

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 45,7 h × 50 €/h | 2283 € |
| Margen de contingencia | +20 % (9,1 h) | 457 € |
| Tokens IA (todo, incl. lectura de caché) | 7,01 M facturables × 13,16 €/M | 92 € |
| **Total estimado (con margen, ref. humana)** | | **≈ 2832 €** |

**Coste con agentes (lo que se espera gastar):** 3,66 h supervisión × 50 € + 92 € de tokens = **≈ 275 €**.

**Sensibilidad a la revisión.** La evaluación da ≈ 367 € (×2,5 solo en C-07 y C-08) y ≈ 443 € (×2,5 en todo); con T-09 sumada, ≈ 380 € y ≈ 460 €.

---

## Previsión de tokens (por fase)

| Fase | Input (tok) | Output (tok) | Total (tok) | Coste € |
|------|------------|-------------|-------------|---------|
| Fase 1 | 408k | 66k | 475k | 6,24 |
| Fase 2 | 1410k | 230k | 1639k | 21,57 |
| Fase 3 | 297k | 48k | 345k | 4,54 |
| Fase 4 | 1690k | 275k | 1965k | 25,86 |
| Fase 5 | 1855k | 302k | 2157k | 28,39 |
| Fase 6 | 371k | 60k | 431k | 5,68 |
| **Total** | **6031k** | **982k** | **7013k** | **92,29 €** |

**Método:** tokens facturables = horas IA (con margen y revisión) × 479.326; reparto 86 % entrada / 14 % salida (perfil de la evaluación). Estimación, no medida.

---

## Productividad IA (humano vs. IA)

| KPI | Valor |
|-----|-------|
| Horas humanas estimadas | 54,8 h (45,7 h base +20 %) |
| Horas IA (ejecución) | 14,63 h (12,19 h base +20 %) |
| Supervisión humana | 3,66 h |
| **Horas totales (IA + supervisión)** | **18,29 h** |
| Horas ahorradas | 36,51 h |
| **Ahorro** | **66,6 %** |
| **Multiplicador de productividad** | **×3,0** |
| FTE equivalentes | 0,23 |

> Las horas IA son una estimación aproximada (supuesto), con confianza Baja por el histórico de desviaciones en configuración ajena y contratos.

---

## Resumen ejecutivo

Se cierran los 9 puntos de la spec en 6 fases y 14 tareas: primero la estabilidad de la suite (C-06, C-09b), luego los quick wins de statusline, `coverage-gate` y dashboard, después `/doctor`, y al final `id_prefix` (C-08) y el alta en `projects.yaml` (C-07). C-07 escribe en la config del stack del usuario (solo añade, con confirmación y copia de seguridad), por lo que queda **bloqueada por una ADR** que redactará `architect` (T-09). Los hooks y la statusline no hacen red; todo es stdlib y multi-runtime.

### Objetivos

- Statusline con iniciativa en curso, ruta y coste correctos (CA-01..05).
- Puertas deterministas: `coverage-gate`, dashboard, test de 200 upserts, tests de conocimiento sin `docs/knowledge/` (CA-06..08, CA-17).
- `id_prefix` elegible con avisos y alta segura en Kwipu (CA-09..15), `/doctor` con `tope_ms` estricto (CA-16).

### Decisiones del usuario (2026-09-29, «todo go»)

| Decisión | Elección | Dónde |
|---|---|---|
| 1a | El lector del dashboard acepta las dos familias de etiquetas; CA-07 revisado para `graphiti-memory` (sin tabla de coste: nulo + aviso nominal) | T-05 |
| 2c | Estado local primero; consulta al servidor solo si responde; sin conexión, «no verificado» | T-11 |
| 3a | `tope_ms` estricto con timeout duro (hilo `daemon` + `join`) | T-08 |
| C-07 | ADR nueva que autorice SOLO AÑADIR en `projects.yaml`, con confirmación y copia de seguridad (enmienda a ADR-018 / PAT-001 / constitución §4) | T-09 -> bloquea T-12, T-13 |
| C-08 | `group_id` derivado de `id_prefix` **solo en instalaciones nuevas**; las que ya tienen `group_id` implícito lo conservan y reciben aviso | T-10, T-11 |

### CA-07 revisado

> Dadas las `evaluation.md` afectadas, cuando corre `build_dashboard.py`, entonces **las 4 con tabla de coste** aportan coste y esfuerzo no nulos (variantes `Tiempo humano`, `Coste humano a N EUR/h`, `Coste humano (N EUR/h)` e históricas, con un test por variante); **`graphiti-memory`**, sin tabla, devuelve nulo con un aviso explícito que nombra la evaluación, sin excepción; el estado se lee del frontmatter cuando no hay fila `Estado`. (sincronizado en `spec.md`, 2026-09-29).

### CA-14/CA-15 ampliados

> El `group_id` derivado de `id_prefix` rige **solo en instalaciones nuevas**. Una instalación con `group_id` implícito previo lo conserva y recibe un aviso (con test). La consulta al servidor de CA-15 es opt-in, acotada a loopback, con estado local primero y «no verificado» si no responde.

---

## Datos necesarios para un informe completo

- [x] **Requisitos funcionales** confirmados (spec aprobada y decisiones del usuario)
- [x] **Alcance** cerrado (9 puntos; fuera: `build_view`, reinicios, migraciones, otros ~74 `find`)
- [x] **Criterios de éxito** acordados (CA-01..19)
- [ ] **Accesos**: muestra anonimizada de `<stack>/kwipu/config/projects.yaml` (entra en T-09; bloquea T-12)
- [x] **Entornos** locales; sin red en hooks
- [x] **Dependencias externas** mapeadas (ADR de T-09)
- [x] **Restricciones** (stdlib, multi-runtime, sin datos personales, `docs/knowledge/` solo local)
- [x] **Tarifa/hora y supuestos** confirmados (`rates.json`)

---

## Análisis de impacto

- **`statusline/roadmap-statusline.sh`** y **`agent-kits/shared/progress-report.py`** — iniciativa en curso, `find` y coste (T-03, T-06, T-07).
- **`agent-kits/shared/doctor.py`** (hotspot nº 1) — `tope_ms` estricto (T-08).
- **`agent-kits/shared/knowledge-schema.py`** (hotspot nº 2) y **`skills/knowledge-services/backends/graphiti.py`** — derivación única de `group_id` desde `id_prefix` (T-10, T-11).
- **`skills/roadmap-dashboard/scripts/build_dashboard.py`** (hotspot) — lector de evaluaciones (T-05).
- **`skills/unit-tests/scripts/coverage-gate.py`** — separar timeout de import fallido (T-04).
- **`skills/knowledge-services/scripts/`** — script nuevo de alta en `projects.yaml` (T-12).
- **`commands/setup.md`** (5-bis, 5-sexies) — `find`, `id_prefix`, alta; regenera `interop/`.
- **Tests**: `tests/test_knowledge_find.py`, `tests/test_knowledge_index.py`, `test_backend_markdown_export.py`.

---

## Cambios arquitectónicos

- Una sola función de derivación de `group_id` y nombre desde `id_prefix`, consumida por el esquema y el adaptador (elimina 33 líneas duplicadas señaladas por `code-health`).
- Compatibilidad: el `group_id` implícito existente se conserva; la derivación nueva solo rige en instalaciones nuevas.
- El alta en `projects.yaml` sigue el contrato de la ADR de T-09: solo añade, vista previa, confirmación, copia de seguridad, escritura atómica, sin ejecutar `build_view` ni reiniciar contenedores.
- Determinismo: la selección de iniciativa en curso va en un script con tests, no en bash.

---

## Archivos a crear/modificar

| Archivo | Acción | Propósito |
|---------|--------|-----------|
| `statusline/roadmap-statusline.sh` | Modificar | coste, `find`, línea de iniciativa en curso |
| `agent-kits/shared/progress-report.py` | Modificar | selección de iniciativa en curso |
| `agent-kits/shared/doctor.py` | Modificar | `tope_ms` estricto |
| `agent-kits/shared/knowledge-schema.py` | Modificar | `id_prefix`, derivación única, avisos |
| `skills/knowledge-services/backends/graphiti.py` | Modificar | usar la derivación única |
| `skills/roadmap-dashboard/scripts/build_dashboard.py` | Modificar | alias de etiquetas y frontmatter |
| `skills/unit-tests/scripts/coverage-gate.py` | Modificar | timeout frente a import |
| `skills/knowledge-services/scripts/kwipu-project-add.py` | Crear | alta que solo añade |
| `skills/knowledge-services/scripts/test_kwipu_project_add.py` | Crear | tests CA-09..13 |
| `commands/setup.md` | Modificar | 5-bis, `id_prefix`, 5-sexies |
| `docs/knowledge/adr/ADR-NNN-*.md` | Crear (local) | ADR de T-09; `docs/knowledge/` no se versiona |
| `interop/**` | Regenerar | `export-interop.py` |
| `docs/**, README*, CHANGELOG*` | Modificar | EN/ES |

---

## Dependencias y prerequisitos

- **T-09 (ADR) bloquea T-12 y T-13** (C-07). Puerta: el usuario acepta la ADR.
- T-12 necesita la muestra anonimizada de `projects.yaml` (T-09) y `id_prefix` (T-10, T-11).
- T-08 y T-10 tocan hotspots distintos (`doctor.py`, `knowledge-schema.py`): no paralelizar tareas sobre el mismo hotspot.
- Orden de la evaluación: C-06 → C-09b → C-03 → C-04 → C-05 → C-02 → C-01 → C-09a → C-08 → C-07.

### Tareas bloqueadas

| Tarea | Bloqueada por | Motivo |
|---|---|---|
| T-12 — C-07a | T-09 | Sin ADR aceptada no se escribe en config ajena |
| T-13 — C-07b | T-09 (y T-12) | Enganche de `/setup` sobre el script |

---

## Criterios de aceptación (global)

- [ ] CA-01..CA-19 de la spec cumplidos (CA-07 en su redacción revisada).
- [ ] `python3 agent-kits/shared/ledger-lint.py docs/roadmap/2026-09-29-setup-statusline-polish/tasks.md` → 0 errores / 0 avisos.
- [ ] Lint, evals, `export-interop.py --check` y suites en verde; réplica en Linux.
- [ ] Sin datos personales en lo versionado; `docs/knowledge/` sigue siendo solo local.

---

## Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| La ADR de T-09 no se acepta | Media | Alto | C-07 se reduce a imprimir el bloque (-8 h humanas, -3 h IA) |
| ×1,5 de revisión corto (histórico ×2,2-×3,4) | Alta | Medio | Sensibilidad publicada; medir el multiplicador real en `/retro` |
| Migración silenciosa del `group_id` | Media | Alto | Solo instalaciones nuevas + test de conservación + aviso (T-10) |
| Tres hotspots tocados (`doctor.py`, `knowledge-schema.py`, `build_dashboard.py`) | Media | Medio | Una tarea por hotspot, sin paralelizar |
| Regresión de la statusline (se ejecuta a cada refresco) | Media | Medio | CA-03 (salida idéntica), sin red ni subprocesos nuevos |
| Rojos de Windows no ven fallos de CI | Media | Medio | Réplica en Linux con CRLF normalizado (T-14) |
| Datos personales en fixtures o ejemplos | Baja | Alto | `<stack>/…`, `grep` en T-02 y T-14 |

---

## Métricas de éxito

- La statusline muestra `▶ <slug>` con varias activas y `$0.42` con locale de coma.
- El dashboard muestra coste y esfuerzo de 4 de las 5 evaluaciones afectadas; la quinta, con aviso nominal.
- 20/20 ejecuciones del test de 200 upserts en verde; ~20 tests de conocimiento verdes en un clon limpio.
- Multiplicador de revisión real registrado en `/retro` (calibra `sdd-proporcional`).

---

## Changelog del plan

| Fecha | Cambio | Autor |
|-------|--------|-------|
| 2026-09-29 | Creación del plan (piloto `sdd-proporcional`, riesgo medio) | planner |

---

## Siguiente paso

Con el **OK del plan**, `implementer` lo ejecuta fase a fase sobre `feature/setup-statusline-polish`, marcando `tasks.md`. T-09 (ADR, `architect`) puede arrancar en paralelo con las Fases 1-3; T-12 y T-13 esperan a su aceptación. `test-plan: n/a (sin UI)`: `qa` corre sus puertas deterministas.
