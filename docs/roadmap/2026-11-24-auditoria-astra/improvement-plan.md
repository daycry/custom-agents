---
design: n/a
test-plan: n/a (sin UI)
generacion:
  inicio: 2026-11-24T16:55:00Z
  fin: 2026-11-24T17:25:00Z
  fuente: estimado        # el planner no arrancó usage-meter: estimación a juicio (degradación sin bloqueo)
  tokens_reales: { entrada: 0, salida: 0, cache_creacion: 0, cache_lectura: 0 }
  eur: null
  horas_ia: 0.5
  duracion: 30m
  ratio_usado: null
  # ventana compartida con tasks.md
plan: auditoria-astra
estado: borrador
creado: 2026-11-24
tasks: tasks.md
spec: n/a
evaluacion: n/a
rama: feat/plugin-audit-2
---

# 2026-11-24-auditoria-astra

> Corregir los hallazgos verificados de la auditoría de código del plugin hecha por gpt-6.2-astra sobre `78616e2`, por orden de riesgo.

| | |
|---|---|
| **Fecha** | 2026-11-24 |
| **Estado** | borrador |
| **Tipo** | Bugfix |
| **Prioridad** | Alta 🟠 |
| **Solicitante** | usuario del repo («crea un plan con las correcciones y las tareas detalladas») |
| **Responsable** | Codex `gpt-6.2-sol` (esfuerzo alto) implementa; Claude Opus 5.5 (esfuerzo alto) revisa |
| **Spec** | n/a: iniciativa de corrección nacida de auditoría |
| **Evaluación** | n/a: iniciativa de corrección nacida de auditoría |
| **Diseño** | n/a (sin paso de diseño) |
| **Origen** | Informe de la auditoría gpt-6.2-astra (22 hallazgos) y su verificación por Claude Opus sobre HEAD (`verif-1-11` y `verif-12-22`); informes de trabajo en el scratchpad de la sesión, no versionados |
| **Ledger** | [`tasks.md`](tasks.md): 13 tareas en 5 fases |

---

## Cuadro de mando

| Métrica | Estimado | Real | Confianza |
|--------|---------|------|-----------|
| Tiempo humano | **87,6 h** (73 h base +20 %) | 0 h | Media |
| Tiempo IA (ejecución) | **21,5 h** (17,9 h base +20 %) (+ 5,4 h supervisión) | 0 h | Baja |
| Coste total | **4.423 €** | 0 € | Media |
| Tokens IA | **7.690k** (in 6.700k / out 990k) | 0 | Baja |
| Multiplicador productividad | **×3,3** | — | — |
| Tareas | **13** | 0 hechas | — |

Las horas IA y los tokens son estimaciones aproximadas del planner (sin medición previa). El precio de tokens es el de `.claude/rates.json` (Claude Opus 5.5, verificado el 2026-10-20); el de `gpt-6.2-sol` es ⚠️ verificar.

---

## Estimación por fase

| Fase | Estimado (h humanas base) | Tokens (in / out) | Coste € (base) |
|------|-------------|-------------------|---------|
| 1 — Puertas que aprueban lo que no deben (T-01, T-02) | 11 | 1.100k / 160k | 557,00 |
| 2 — Pérdida de datos y robustez (T-03 a T-05) | 20 | 1.800k / 280k | 1.011,77 |
| 3 — Alcance y publicación (T-06, T-07) | 11 | 950k / 140k | 556,07 |
| 4 — Rendimiento de la consola (T-08) | 7 | 650k / 100k | 354,23 |
| 5 — Resto de Minor y deuda de pruebas (T-09 a T-13) | 24 | 2.200k / 310k | 1.213,81 |
| **Total** | **73 h** | **6.700k / 990k** | **3.692,88 €** (sin margen) |

El coste base es `horas × 50 €/h + tokens`. El margen de contingencia (+20 % sobre las horas humanas: 730 €) lo lleva el total del presupuesto.

---

## Presupuesto económico

**Coste = (horas × tarifa) + coste de tokens de IA.** Todos los importes en **EUR**.

### Supuestos (ajustables)

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | 50 €/h | `.claude/rates.json` |
| Modelo IA asumido | Claude Opus 5.5 | Referencia de precio: el implementador real es Codex `gpt-6.2-sol`, ⚠️ verificar su tarifa; el revisor es Opus 5.5 |
| Precio input | 4 USD / 1M tokens | Verificado el 2026-10-20; todo el input a precio estándar (sin caché: cota alta) |
| Precio output | 20 USD / 1M tokens | Verificado el 2026-10-20 |
| Tipo de cambio | 1 USD = 0,92 € | Supuesto fijo, no verificado |
| Margen de contingencia | 20 % | Sobre horas base humanas e IA |
| Supervisión | 25 % de las horas IA | `ratioSupervision` de `rates.json` |

### Desglose

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 73 h × 50 €/h | 3.650,00 € |
| Margen de contingencia | +20 % sobre desarrollo base | 730,00 € |
| Tokens IA (input) | 6.700k tok × 4 USD/M × 0,92 | 24,66 € |
| Tokens IA (output) | 990k tok × 20 USD/M × 0,92 | 18,22 € |
| **Total estimado (con margen)** | | **4.422,88 €** |

---

## Previsión de tokens (por fase)

| Fase | Input (tok) | Output (tok) | Total (tok) | Coste € |
|------|------------|-------------|-------------|---------|
| 1 | 1.100k | 160k | 1.260k | 7,00 |
| 2 | 1.800k | 280k | 2.080k | 11,77 |
| 3 | 950k | 140k | 1.090k | 6,07 |
| 4 | 650k | 100k | 750k | 4,23 |
| 5 | 2.200k | 310k | 2.510k | 13,81 |
| **Total** | **6.700k** | **990k** | **7.690k** | **42,88 €** |

**Método de estimación:** por tarea, ficheros a leer (script + tests + docs + `interop/` cuando aplica) × tamaño medio, más generación de test RED, GREEN, docs ES/EN y un bucle de revisión de Opus 5.5. Es una estimación del planner, no una medición; `usage-meter.py` medirá el real por tarea.

---

## Productividad IA (humano vs. IA)

| KPI | Valor |
|-----|-------|
| Horas humanas estimadas | 87,6 h (73 h base +20 %) |
| Horas IA (ejecución) | 21,5 h (17,9 h base +20 %), supuesto |
| Supervisión humana | 5,4 h (25 % de las horas IA base con margen) |
| **Horas totales (IA + supervisión)** | **26,8 h** |
| Horas ahorradas | 60,8 h |
| **Ahorro** | **69,4 %** |
| **Multiplicador de productividad** | **×3,3** |
| FTE equivalentes | 0,38 |

---

## Resumen ejecutivo

La auditoría de gpt-6.2-astra sobre `78616e2` dejó 22 hallazgos. Claude Opus los verificó contra HEAD: ninguno es un falso positivo, uno (el 16, rendimiento de `usage-meter`) ya está corregido en T-40 de `plugin-audit-2` y el resto sigue vivo. Con el grado reajustado, **ningún hallazgo es Critical**: 6 son Important (1, 2, 3, 6, 7 y 15) y los otros 15, Minor.

Este plan los corrige agrupados por dueño del fichero. Primero las puertas que aprueban lo que no deben (qa-gate y verdict limpio sin evidencia), después la pérdida de datos y la robustez del instalador, el alcance y la publicación, el rendimiento de la consola y, al final, los Minor. Añade una tarea propia por un hallazgo del orquestador fuera de la auditoría: tests acoplados al ledger real de una iniciativa.

### Objetivos

- Cero casos conocidos de «verde con evidencia en contra» en `qa-gate.py` y en el cierre de revisión de `ledger-write.py`, cada uno con su regresión.
- El instalador no pierde ni amplía permisos sobre la configuración del usuario y la desinstalación de OpenCode deja la configuración como estaba.
- Cada hallazgo corregido tiene un test RED previo; nada se cierra solo con prosa.
- Todo lo tocado sigue funcionando en Claude Code, Codex y OpenCode (`export-interop.py --check` y puertas de runtimes en verde).
- Ninguna prueba del repo depende del ledger real de una iniciativa.

---

## Decisión del usuario (hallazgo 4) — tomada el 2026-11-24

El usuario la delegó en gpt-6.2-astra («lo que considere Astra»). Decisión: variante de la opción B — el texto de los turnos no se persiste nunca; en cada `UserPromptSubmit` se extraen en memoria decisiones y pendientes y solo eso (redactado y acotado) se guarda hasta confirmar el journal. Se descarta borrar el log en `SessionEnd` porque `replay`/`recover` lo necesitan para las sesiones huérfanas. Detalle en T-13.

### Opciones que se valoraron

`journal-prompt.py` conserva por defecto el texto literal de los turnos del usuario en `.claude/session-prompts-<session_id>.log` (local, no versionado, 30 días, opt-out `<private>` y `sesion.captura: false`; documentado en `ADR-010` y `ADR-013`). Choca con `docs/CONSTITUTION.md:35` («nunca se guardan conversaciones crudas»). La verificación lo reajusta a Minor y lo deja en manos del usuario. **`docs/CONSTITUTION.md` no se edita sin esta decisión.**

| Opción | Qué cambia | Coste | Efecto |
|---|---|---|---|
| **A. Excepción explícita en la Constitución** | Añadir a `docs/CONSTITUTION.md` §4 una excepción para el log local de turnos (fichero, no versionado, retención de 30 días, opt-out) y una nota en los ADR | ~1 h, solo docs ES/EN | El comportamiento actual pasa a ser política; el texto crudo sigue en disco hasta 30 días |
| **B. Borrar el log tras extraer el journal** | `SessionEnd` extrae `decisiones`/`pendientes` y elimina el log (o no lo persiste literal); toca `journal-prompt.py`, `journal.py` y los hooks | ~3 h, código + tests + `interop/` | Cumple la Constitución tal cual; se pierde la reextracción posterior desde el log |

T-13 es la tarea condicionada: no arranca sin la decisión y se estima con la opción B (la más cara).

---

## Datos necesarios para un informe completo

- [x] **Requisitos funcionales** confirmados: corregir los hallazgos verificados, con grado reajustado
- [x] **Alcance** cerrado: 21 hallazgos verificados + 1 del orquestador; el 16 queda fuera (descartado en HEAD, su residuo es de T-40)
- [x] **Criterios de éxito / métricas** acordados: test RED→GREEN por hallazgo y puertas del repo en verde
- [x] **Accesos y credenciales**: ninguno nuevo (Jira y Confluence no se tocan en vivo)
- [x] **Entornos** disponibles: Windows local y Linux (`python:3.11-slim`) para lo POSIX
- [ ] **Stakeholders**: decisión del usuario sobre el hallazgo 4 (opción A o B)
- [x] **Dependencias externas** mapeadas: `plugin-audit-2` T-40 (en curso)
- [x] **Restricciones**: tres runtimes, bilingüe ES/EN, puertas de tokens, sin cambios de rama ni commits del planner
- [x] **Tarifa/hora y supuestos de coste** confirmados con `.claude/rates.json`

---

## Análisis de impacto

- **`agent-kits/qa/qa-gate.py`** — recuentos desde `results[]` e identidad con proyecto (T-01).
- **`agent-kits/shared/ledger-write.py`, `skills/adversarial-review/`, `agents/implementer.md`** — verdict con evidencia de lentes y `Cerrada` vigente (T-02); requiere `interop/` regenerado.
- **`install/install.mjs`, `install/providers.mjs`** — escritura atómica, guardia de identidad, `0600`, retirada de la entrada de OpenCode (T-03).
- **`skills/jira-sync/`, `skills/knowledge-services/`, `agent-kits/shared/outbox.py`** — idempotencia por intención y por clave única (T-04, T-05).
- **`agent-kits/shared/scope-check.py`** — renombrados, espacios, presupuesto de llaves (T-06).
- **`scripts/release.py`, `scripts/export-interop.py`** — verificador obligatorio y misma validación en `--check` (T-07).
- **`skills/plugin-panel/`** — caché por firma del ledger (T-08).
- **`scripts/lint_plugin.py`, `hooks/run-hook.mjs`** — grupos de hooks y selección de Python (T-09).
- **Recetas de `skills/` y `commands/`** — preámbulo único de resolución de kits (T-10), con efecto en las puertas de tokens.
- **`agent-kits/shared/usage-meter.py`** — atribución por sesión (T-11).
- **Tests del repo** — fixtures sintéticos y guardia anti-acoplamiento (T-12).
- **`hooks/`, `journal-prompt.py`, `docs/CONSTITUTION.md`** — según la decisión del usuario (T-13).

---

## Cambios arquitectónicos

- **Una puerta nunca aprueba con evidencia en contra.** Los recuentos se derivan de los resultados individuales; los resúmenes solo se contrastan (T-01, T-02).
- **El instalador nunca escribe in situ sobre configuración ajena.** Si no puede reemplazar atómicamente, se detiene y avisa (T-03).
- **Las altas externas llevan identidad buscable antes de enviarse** (Jira, outbox), para reconciliar en vez de repetir (T-04, T-05).
- **Fuente única de resolución de kits** (`agent-kits/shared/kit-resolution.md`) referenciada por línea desde cada receta, para no crecer en tokens (T-10).
- **Los tests no leen ledgers reales de iniciativas** (T-12).
- **ADR:** ninguna decisión de este plan cruza el umbral de `knowledge-write.md` (cierra una alternativa y afecta a 2+ piezas) salvo, quizá, T-10 (preámbulo único); lo decidirá el implementador al cerrar T-10 y, si cruza, escribirá el ADR `propuesta`.

---

## Archivos a crear/modificar

| Archivo | Acción | Propósito |
|---------|--------|-----------|
| `agent-kits/qa/qa-gate.py`, `tests/test_qa_gate.py` | Modificar | T-01 |
| `agent-kits/shared/ledger-write.py`, `test_ledger_write_transitions.py`, `skills/adversarial-review/SKILL.md`, `agents/implementer.md` | Modificar | T-02 |
| `install/install.mjs`, `install/providers.mjs`, `tests/installer.test.mjs` | Modificar | T-03 |
| `skills/jira-sync/**` | Modificar | T-04 |
| `skills/knowledge-services/scripts/knowledge-sync.py`, `agent-kits/shared/outbox.py` | Modificar | T-05 |
| `agent-kits/shared/scope-check.py` y sus tests | Modificar | T-06 |
| `scripts/release.py`, `scripts/export-interop.py` y sus tests | Modificar | T-07 |
| `skills/plugin-panel/scripts/console_service.py`, `panel_data.py` y assets | Modificar | T-08 |
| `scripts/lint_plugin.py`, `hooks/run-hook.mjs` y sus tests | Modificar | T-09 |
| `agent-kits/shared/kit-resolution.md` | Crear | T-10 |
| Recetas de `skills/` y `commands/`, `tests/test_plugin_root_resolution.py` | Modificar | T-10 |
| `agent-kits/shared/usage-meter.py` y sus tests | Modificar | T-11 |
| `tests/test_no_real_ledger_coupling.py`, `tests/fixtures/` | Crear | T-12 |
| `docs/CONSTITUTION.md` o `journal-prompt.py`/`journal.py` | Modificar | T-13, según la decisión |
| `interop/**` | Regenerar | T-02, T-09, T-10 y T-13 (opción B) |
| `CHANGELOG.md`, `CHANGELOG.es.md`, espejos `docs/en/*` | Modificar | Los dos CHANGELOG por tarea (`changelog-sync`) y cada doc con espejo |

---

## Dependencias y prerequisitos

- **`plugin-audit-2` T-40 (en curso)** cambia `ledger-write.py`, `ledger-lint.py`, `usage-meter.py`, `task-brief.py` y `jira-flow.py`. Bloquea T-02, T-04, T-11 y T-12; rebasar sobre su cierre antes de empezarlas. Su fix5 corrige además el residuo del hallazgo 16.
- T-12 depende de T-02 (mismo fichero de tests).
- T-13 depende de la decisión del usuario.
- Orden recomendado: fase 1 (T-01 puede empezar ya; T-02 espera a T-40), fases 2, 3 y 4 en paralelo si no comparten fichero, fase 5 al final. T-03, T-05, T-06, T-07, T-08, T-09 y T-10 no dependen de T-40.
- **Implementación:** Codex `gpt-6.2-sol` (esfuerzo alto) implementa; Claude Opus 5.5 (esfuerzo alto) revisa con `adversarial-review` (lentes A+B y las condicionales). Tope de 3 bucles revisor→implementador por tarea.

---

## Criterios de aceptación (global)

- [ ] Los 21 hallazgos verificados tienen un test RED registrado y su GREEN; el hallazgo 4 queda resuelto por la opción elegida.
- [ ] `python scripts/export-interop.py --check` → exit 0 tras la última tarea.
- [ ] `python scripts/lint_plugin.py`, `python evals/check.py` y las suites de `tests/` y `agent-kits/**` en verde en Linux (`python:3.11-slim`), no solo en Windows.
- [ ] Puertas de tokens en verde (vía rápida ≥ 6.000, `agents/evaluator.md` ≤ 15.513 bytes en LF, `--diet-check` sin párrafos perdidos) tras T-02 y T-10.
- [ ] `python agent-kits/shared/ledger-lint.py docs/roadmap/2026-11-24-auditoria-astra/tasks.md` → 0 incoherencias.
- [ ] `python agent-kits/shared/scope-check.py docs/roadmap/2026-11-24-auditoria-astra` → exit 0.
- [ ] Archivar `docs/roadmap/2026-11-10-plugin-audit-2/` no rompe ninguna prueba.

---

## Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| T-40 se retrasa o cambia `ledger-write.py` de forma incompatible con T-02 | Media | Medio | T-02, T-04, T-11 y T-12 esperan al cierre de T-40 y rebasan; T-01 y las fases 2, 3, 4 y 5 no dependen de ella |
| Endurecer `verdict` rompe flujos de `/dev-cycle` ya en curso | Media | Alto | Mantener el cierre con evidencia completa; probar el flujo feliz y publicar la regla en `adversarial-review` §6 |
| Los fallos POSIX (`0600`, `python3` sin `x`, symlinks) no se ven en Windows | Alta | Medio | Pruebas con `skip` explícito en win32 y verificación obligatoria en `python:3.11-slim` antes del push |
| T-10 (17 recetas) aumenta los tokens o dispara el linter de tamaño | Media | Medio | Fuente única con una línea por receta; puertas de tokens y `--diet-check` como criterio de aceptación |
| T-03 es grande (4 hallazgos) | Media | Medio | Partir #12 en otra tarea si el revisor lo pide |
| Sin decisión del usuario, T-13 queda bloqueada | Alta | Bajo | Es la última tarea; no bloquea el resto ni el cierre de las otras 12 |
| El precio de `gpt-6.2-sol` es desconocido | Alta | Bajo | El coste de tokens es <1,2 % del total; se marca ⚠️ verificar |

---

## Métricas de éxito

- 0 hallazgos verificados abiertos al cierre, medidos con el RED→GREEN de cada tarea.
- `qa-gate.py` y `ledger-write.py verdict` rechazan los casos reproducidos por la auditoría (informe con `failed` y revisión vacía).
- Sondeos sin cambios de la consola: 1 lectura y proyección del ledger por cambio, no por sondeo (medido antes/después en T-08).
- 0 pruebas que lean ledgers reales de iniciativas fuera de la lista blanca (T-12).
- Real vs estimado: se registra en `/retro` con el ratio tokens/hora medido.

---

## Changelog del plan

| Fecha | Cambio | Autor |
|-------|--------|-------|
| 2026-11-24 | Creación del plan: 13 tareas en 5 fases. Excluye el hallazgo 16 (descartado en HEAD; residuo en `plugin-audit-2` T-40). Hallazgo 4 pendiente de decisión del usuario | planner |
| 2026-11-24 | Decisión del hallazgo 4 (T-13) delegada por el usuario en gpt-6.2-astra: no persistir el texto de los turnos, solo la extracción mínima hasta confirmar el journal. T-13 deja de estar condicionada | orquestador |

---

## Siguiente paso

Con el **OK del plan** del usuario y su decisión sobre el hallazgo 4, el agente **`implementer`** (Codex `gpt-6.2-sol`) lo ejecuta fase a fase sobre una rama, marcando `tasks.md` como **ledger canónico**; la revisión la hace Claude Opus 5.5. Con `test-plan: n/a (sin UI)`, `qa` corre sus puertas deterministas y sale limpio sin pedir test-plan (ADR-017).
