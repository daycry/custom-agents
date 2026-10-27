---
generacion:
  inicio: 2026-10-27T12:00:15Z
  fin: 2026-10-27T12:11:49Z
  fuente: medido
  fuente_id: src-d2ceb5c719af848b4c213bb2d521d0f003976923acb613d7512912ccbeb6a09e
  ventana_id: win-fd680dbbb9414f288b4b28caf6b23433
  revision_medicion: 1
  medicion_persistida: true
  tokens_reales: { entrada: 3293, salida: 44807, cache_creacion: 98972, cache_lectura: 1711943 }
  eur: 1.61
  horas_ia: 0.28
  duracion: 17m
  ratio_usado: 531798.5
  avisos: ["CALIBRATION: filas marcadas (estimado) fuera de la mediana (informativo, x6)", "incluye la redacción de spec.md en la misma ventana"]
---

# 2026-10-27-plugin-optimization

> Presupuesto de la optimización del plugin en tres frentes (latencia de hooks, tokens, modelos locales) para decidir si se hace y en qué tramos.

| | |
|---|---|
| **Fecha** | 2026-10-27 |
| **Estado** | completado |
| **Prioridad global** | Alta 🟠 |
| **Solicitante** | Daycry (vía `/pm-cycle`) |
| **Spec** | [`spec.md`](spec.md) |
| **Plan** | [`improvement-plan.md`](improvement-plan.md) · [`tasks.md`](tasks.md) |
| **Características evaluadas** | 18 (+ 3 partidas de proceso, una por fase) |

---

## 📊 Cuadro de mando

| Métrica | Total estimado | Confianza |
|--------|----------------|-----------|
| Esfuerzo humano | **152,4 h** (127 h base +20 %) · núcleo sin opcionales: 133,2 h | Media |
| Tiempo IA (ejecución) | **61,3 h** (+ 15,3 h supervisión) | Baja |
| Coste (presupuesto humano + tokens) | **7.808 €** · núcleo sin opcionales: 6.823 € | Media |
| Coste de ejecución con agentes (supervisión + tokens) | **954 €** · núcleo: 830 € | Baja |
| Tokens IA | **27,17 M facturables** (in 24,7 M / out 2,47 M) + ~217 M de lectura de caché | Baja |
| Multiplicador productividad | **×2,0** | — |
| Características | **18** (14 núcleo + 4 opcionales) | — |

---

## 🧭 Resumen ejecutivo

Llegan tres auditorías medidas del 2026-10-27 con un alcance propuesto de 14 características en tres fases. La evidencia del repo confirma los hallazgos clave y pide dos ajustes: **añadir C-00** (benchmark reproducible versionado, porque «medir antes/después» es criterio de aceptación y los scripts de la auditoría solo están en el scratchpad) y **añadir C-15** (opcional): en Windows cada hook lanza un segundo Python `runtime-supervisor.py close` al salir (`hooks/run-hook.mjs:233-240`, llamado en cada `exit`), un coste que pagan TODOS los hooks y que no estaba en la lista. Se presupuesta todo en **152,4 h humanas / 7.808 €**, o **~954 € ejecutado con agentes**. La IA se estima a partir de las rondas de revisión (3 intentos por característica), siguiendo la calibración. La F1 sola (38,4 h / 1.966 €; ~232 € con agentes) elimina la mayor parte de los ~6 min de espera por sesión, y sobre todo el guard de 2,3 s en cada Bash/Edit. Recomendación: **go por tramos**.

---

## 📥 Requerimientos recibidos

| ID | Característica | Requisito origen (ref.) | ¿Claro? |
|----|---------------|-------------------------|---------|
| C-00 | Benchmark reproducible de hooks y tokens | spec §Decisiones «Medición» (añadida por el evaluator; criterio de aceptación del prompt) | ✅ |
| C-01 | Descriptions ≤ 600 conservando literales de evals; aviso del linter a 600 | spec §Alcance F1 | ✅ |
| C-02 | Prefiltro del guard nativo en node | spec §Alcance F1, ADR-023 | ✅ |
| C-03 | Statusline con una sola llamada Python y caché por mtime | spec §Alcance F1 | ✅ |
| C-04 | Timeout de SessionStart + captura de prompt con arranque aislado | spec §Alcance F1 | ⚠️ ambiguo (valor del timeout; `-I -S` depende de los imports de `journal.py`) |
| C-05 | Temporales sqlite huérfanos | spec §Alcance F1 | ✅ |
| C-06 | `session-context` en un único Python | spec §Alcance F2 | ✅ |
| C-07 | Fusión `ledger-lint-warn` + `progress-line` | spec §Alcance F2 | ✅ |
| C-08 | `mark-docs-pending` dentro de node | spec §Alcance F2 | ✅ |
| C-09 | `dev-cycle.md` núcleo + fases bajo demanda | spec §Alcance F2, ADR-008 | ✅ |
| C-10 | Memoria gobernada condicional en `knowledge-check.md` | spec §Alcance F2 | ⚠️ ambiguo (condición exacta de activación) |
| C-11 | Ids no Claude en `dev.json` + `model` en interop | spec §Alcance F3, ADR-009 | ⚠️ ambiguo (dónde vive el mapeo de modelos del consumidor) |
| C-12 | `ledger-write.py` | spec §Alcance F3 | ✅ |
| C-13 | Perfil `lite` en `dev.json` | spec §Alcance F3 | ⚠️ ambiguo (qué puede recortar) |
| C-14 | Aviso de contexto corto en `/doctor` + mínimos por tramo (ES/EN) | spec §Alcance F3 | ✅ |
| C-15 | Cierre del Job Object sin segundo Python (opcional, con spike) | hallazgo del evaluator, `hooks/run-hook.mjs:233-240,316` | ⚠️ ambiguo (viabilidad sin perder la limpieza de nietos) |
| C-16 | `review-lens-select` con una lectura por fichero (opcional) | prompt «Opcional» | ✅ |
| C-17 | Kit shared resuelto una vez por fichero (opcional) | prompt «Opcional» | ✅ |
| C-18 | `skill-index` solo con nombres en Claude Code (opcional) | prompt «Opcional» | ✅ |

**Ambigüedades / información que falta:**

- **Validación de F3:** con 2,8 GB libres, esta máquina no puede correr un modelo de 32B. Los criterios de F3 se validarían aquí solo de forma estática (contratos, interop, doctor). Una prueba real con Ollama necesita otro equipo. Supuesto: validación estática + una prueba manual del usuario fuera de presupuesto.
- **Presupuesto del listado de skills:** recortar las descriptions (−2.100 tokens) puede no bastar para que las 13 skills sin descripción vuelvan a aparecer: el límite lo pone el runtime y no se ha medido. C-01 incluye medirlo en una sesión real; si no basta, haría falta un segundo recorte (fuera de presupuesto).
- **Timeout de SessionStart:** la mediana medida (14-22 s) supera cualquier timeout razonable. El timeout solo tiene sentido junto con C-06; sin C-06, hoy cortaría la retoma en esta máquina. Supuesto: C-04 fija un valor alto (≈ 30 s) y C-06 lo baja.
- Que C-02 elimine casi toda la espera depende de cuántas llamadas son Bash/Edit/Write. Supuesto: ~150 de 200, lo que da ≈ 5,7 min de los ~6 medidos.

---

## ✅ Datos necesarios para una evaluación completa

- [x] **Requerimientos** completos y sin ambigüedades (salvo C-04, C-10, C-11, C-13 y C-15, marcados)
- [x] **Alcance** de cada característica acotado (qué entra y qué NO)
- [x] **Criterios de aceptación / éxito** por característica (spec §Criterios, con [GWT])
- [x] **Restricciones** (multi-runtime, hooks exit 0, determinismo, bilingüe, release por script)
- [ ] **Dependencias externas** identificadas: falta un equipo con Ollama y ≥ 64k de contexto para validar F3 de extremo a extremo
- [x] **Contexto técnico** del proyecto disponible (repo leído)
- [x] **Tarifa/hora y supuestos de coste** confirmados (`.claude/rates.json`, precios verificados el 2026-10-20)

---

## 💶 Supuestos económicos (ajustables)

**Coste = (horas × tarifa) + coste de tokens de IA.** Importes en **EUR**.

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | 50 €/h | `.claude/rates.json` `tarifaHora` |
| Modelo IA asumido | claude-opus-5-5 | `rates.json` `modeloIA` |
| Precio input | 4,14 € / 1M tokens | Mezcla 50/50 de entrada (4 USD → 3,68 €) y creación de caché (5 USD → 4,60 €); supuesto de reparto |
| Precio output | 18,40 € / 1M tokens | 20 USD × 0,92; `verificadoEl: 2026-10-20` (< 90 días: fiable) |
| Lectura de caché | 0,184 € / 1M tokens | 0,2 USD × 0,92; volumen supuesto = 8× los facturables (no presupuestado por característica) |
| Tipo de cambio | 1 USD = 0,92 € | Supuesto fijo de `rates.json` |
| Margen de contingencia | 20 % | Sobre horas base humanas e IA |
| Supervisión | 25 % de las horas IA | `rates.json` `ratioSupervision` |
| Ratio tokens→hora-IA | 531.798,5 tok/h | Mediana de 6 muestras de `CALIBRATION.md` (no el default de 300.000) |
| Rondas de revisión | 3 intentos por característica (lentes A+B; C en C-02, C-04, C-05, C-15; D en C-02, C-03, C-06, C-07, C-15, C-16) | Retros de project-specialization y panel-redesign: la revisión cuesta más que la implementación |
| Revalidación de fase diferida | +0,5 h en F2 y F3 | Retro de project-specialization |

**Calibración aplicada (P2-bis):**

- La IA de cada característica se calcula con los tokens de implementación más 3 intentos de revisión con corrección; la revisión pesa ~60 % de los tokens. Motivo: en panel-redesign la IA se estimó en proporción a la implementación y el coste real fue la revisión.
- training-data-services (+761 % de IA) se debió a hacer bloqueante cada Minor. Supuesto: los Minor no bloquean el cierre. Si se exige «sin gaps», la cifra de IA no vale.
- Coste de proceso aparte (LES de doctrina «presupuesta el coste de proceso aparte»): una partida P-Fx por fase (CHANGELOG doble, docs espejo, interop, release, verificación en Linux).
- Se separa lo que se mide de lo que se vende (doctrina): el **presupuesto humano** (7.808 €) es la referencia de valor; el **coste de ejecución con agentes** (954 €) es lo que se espera gastar.

---

## 🔍 Evaluación por característica

### F1 — Quick wins medibles

### C-00 — Benchmark reproducible de hooks y tokens

- **Requisito origen**: spec §Decisiones «Medición»; criterio de aceptación transversal del prompt
- **Descripción**: script versionado con tests que mide la mediana (≥ 10 ejecuciones) de cada hook con payloads fixture por runtime y suma los tokens fijos por sesión (descriptions + índice) y bajo demanda (`dev-cycle.md`, `knowledge-check.md`). Sale en JSON/MD para pegarlo en el ledger antes y después de cada cambio. Parte de `t.sh`/`m.py` de la auditoría.
- **Complejidad**: Media
- **Esfuerzo**: 6 h (7,2 h con margen) · confianza Alta
- **Previsión IA**: 0,9 M in / 90k out tok · 5,38 € · 2,23 h IA con margen
- **Coste**: (7,2 h × 50) + tokens = **365 €**
- **Impacto / áreas afectadas**: `scripts/` o `agent-kits/shared/` (nuevo), `tests/`, `docs/observability.md` (+ EN)
- **Dependencias y prerequisitos**: ninguna; es requisito de todas las de rendimiento/tokens
- **Riesgos**: en esta máquina (OneDrive, poca memoria) hay mucho ruido. Mitigación: comparar medianas relativas en la misma sesión y no fijar umbrales absolutos en CI.
- **Incógnitas / preguntas abiertas**: ¿se versiona la línea base de esta máquina o solo el procedimiento?

### C-01 — Descriptions ≤ 600 caracteres

- **Requisito origen**: spec §Alcance F1
- **Descripción**: reescribir las 25 descriptions que pasan de 600 (exceso medido 7.584 caracteres ≈ −2.100 tokens fijos/sesión) conservando los literales de `evals/cases/`. `DESC_WARN_CHARS` baja de 1.200 a 600, se regenera interop y se actualiza CONVENTIONS ES/EN.
- **Complejidad**: Media (trabajo de redacción con riesgo de activación)
- **Esfuerzo**: 8 h (9,6 h) · confianza Media
- **Previsión IA**: 1,6 M in / 160k out tok · 9,57 € · 3,97 h IA
- **Coste**: (9,6 h × 50) + tokens = **490 €**
- **Impacto / áreas afectadas**: `agents/*.md` (architect 1.097, reviewer 1.084, analyst 1.067, documenter, knowledge-curator, evaluator), 16 `skills/*/SKILL.md`, `commands/setup.md`, `commands/doctor.md`, `scripts/lint_plugin.py:108`, `evals/cases/`, `interop/`, `docs/CONVENTIONS.md` + `docs/en/CONVENTIONS.md`
- **Dependencias y prerequisitos**: C-00 (medir tokens fijos antes/después)
- **Riesgos**: perder disparadores, porque `evals/check.py` solo comprueba literales y no la activación real. `evals/run.py`/`headless.yml` necesitan `ANTHROPIC_API_KEY`. El tope de `lint_plugin.py` también afecta a los consumidores que crean piezas.
- **Incógnitas / preguntas abiertas**: ¿basta para que las 13 skills vuelvan al listado? (medición en sesión real incluida; si no basta, hace falta un segundo recorte)

### C-02 — Prefiltro del guard nativo en node

- **Requisito origen**: spec §Alcance F1; ADR-023
- **Descripción**: `run-hook.mjs` lee `native-roles.json`, compara la identidad nativa EXACTA (`agent_type` en Claude/Codex, `agent` en OpenCode) con los roles protegidos del runtime y, si no coincide, termina sin lanzar Python. Si el mapa falta o es inválido, lanza Python como hoy. La decisión de deny sigue en `native-guardrail.py`. Es la partida de mayor retorno: ≈ 2,3 s × ~150 llamadas ≈ 5,7 min por sesión aquí.
- **Complejidad**: Media
- **Esfuerzo**: 6 h (7,2 h) · confianza Media
- **Previsión IA**: 1,4 M in / 140k out tok · 8,37 € · 3,48 h IA (lente C de seguridad en los 3 intentos)
- **Coste**: (7,2 h × 50) + tokens = **368 €**
- **Impacto / áreas afectadas**: `hooks/run-hook.mjs:72-110,194-203`, `hooks/opencode-plugin.js:138`, `agent-kits/shared/native-roles.json`, `tests/hook-guard-delivery.test.mjs`, `tests/test_hook_launcher_security.py`, ADR-023 (adenda), `interop/codex/hooks.json` (regenerado)
- **Dependencias y prerequisitos**: C-00
- **Riesgos**: **seguridad.** Si node y Python divergen al decidir qué es un rol protegido, se abre una vía de omisión. Mitigación: lista PROTECTED en una sola fuente (el JSON) y test de paridad node/Python sobre una tabla de identidades (incluye mayúsculas, prefijos, espacios y la identidad de Codex frente a la de OpenCode).
- **Incógnitas / preguntas abiertas**: ¿mover `PROTECTED` al JSON (cambio de esquema, `schema_version` 2) o duplicarlo con un test que lo ate?

### C-03 — Statusline con una sola llamada Python

- **Requisito origen**: spec §Alcance F1
- **Descripción**: hoy son 3 `python3` (9,8 s por refresco aquí, `statusline/roadmap-statusline.sh:34,72,79`). Pasa a un único script que parsea la entrada y calcula el segmento del roadmap, usa el intérprete que ya resuelve el launcher (sin el alias de WindowsApps) y guarda caché por mtime de los ledgers activos.
- **Complejidad**: Baja-Media
- **Esfuerzo**: 5 h (6 h) · confianza Media
- **Previsión IA**: 0,9 M in / 90k out tok · 5,38 € · 2,23 h IA
- **Coste**: (6 h × 50) + tokens = **305 €**
- **Impacto / áreas afectadas**: `statusline/roadmap-statusline.sh`, `agent-kits/shared/progress-report.py` (o script nuevo), `commands/setup.md` paso 5-bis, `docs/observability.md` (+ EN)
- **Dependencias y prerequisitos**: C-00
- **Riesgos**: el statusline es solo de Claude Code; la resolución del intérprete en bash sin node tiene que degradar en silencio.
- **Incógnitas / preguntas abiertas**: ¿dónde vive la caché (`.claude/` no versionado)?

### C-04 — Timeout de SessionStart y captura de prompt aislada

- **Requisito origen**: spec §Alcance F1
- **Descripción**: declarar `timeout` en SessionStart (`hooks/hooks.json`) y vigilarlo en `test_hooks_config.py`. Arrancar `journal.py capture` con `-I -S` (2,6 s por turno), siempre que sus imports lo permitan.
- **Complejidad**: Baja
- **Esfuerzo**: 2 h (2,4 h) · confianza Media
- **Previsión IA**: 0,4 M in / 40k out tok · 2,39 € · 0,99 h IA
- **Coste**: (2,4 h × 50) + tokens = **122 €**
- **Impacto / áreas afectadas**: `hooks/hooks.json`, `hooks/run-hook.mjs:203`, `agent-kits/shared/journal.py`, `interop/` (regenerado), `tests/test_hooks_config.py`
- **Dependencias y prerequisitos**: C-06 para bajar el timeout a un valor ajustado
- **Riesgos**: un timeout por debajo de la mediana actual (14-22 s) dejaría sin contexto de retoma. `-I` quita el directorio del script de `sys.path` y puede romper imports hermanos.
- **Incógnitas / preguntas abiertas**: valor del timeout (propuesta: 30 s ahora y 10 s tras C-06)

### C-05 — Temporales sqlite huérfanos

- **Requisito origen**: spec §Alcance F1
- **Descripción**: `construir_indice` borra el `.tmp` pero nunca su `-journal`, y un proceso matado por el Job Object no llega al `finally` (`knowledge-find.py:825-830`). Hay 20 parejas en `.claude/`. Se añade barrido de temporales de PIDs no vivos o de cierta antigüedad, borrado del `-journal` y, opcionalmente, aviso en `/doctor`.
- **Complejidad**: Baja
- **Esfuerzo**: 3 h (3,6 h) · confianza Alta
- **Previsión IA**: 0,5 M in / 50k out tok · 2,99 € · 1,24 h IA
- **Coste**: (3,6 h × 50) + tokens = **183 €**
- **Impacto / áreas afectadas**: `agent-kits/shared/knowledge-find.py`, `agent-kits/shared/test_knowledge_*`, `agent-kits/shared/doctor.py`
- **Dependencias y prerequisitos**: ninguna
- **Riesgos**: borrar el temporal de un proceso concurrente vivo. Mitigación: comprobar que el PID está vivo y aplicar un umbral de antigüedad.
- **Incógnitas / preguntas abiertas**: ninguna relevante

### F2 — Reestructuración

### C-06 — `session-context` en un único Python

- **Requisito origen**: spec §Alcance F2
- **Descripción**: portar `hooks/session-context.sh` (315 líneas, 12 invocaciones de `python3`, ~20 procesos, 14-22 s) a un único `session-context.py` que importa en proceso `journal`, `skill-index`, `progress-report` y `knowledge-find` (ficheros con guion, vía `importlib`). La salida por runtime tiene que ser idéntica byte a byte.
- **Complejidad**: Alta
- **Esfuerzo**: 12 h (14,4 h) · confianza Media
- **Previsión IA**: 2,4 M in / 240k out tok · 14,35 € · 5,96 h IA
- **Coste**: (14,4 h × 50) + tokens = **734 €**
- **Impacto / áreas afectadas**: `hooks/session-context.sh`, `hooks/run-hook.mjs` (modo python), `agent-kits/shared/{journal,skill-index,progress-report,knowledge-find}.py`, `tests/test_hooks_shell.py`, `tests/hook-runtime.test.mjs`, `interop/`
- **Dependencias y prerequisitos**: C-00; habilita bajar el timeout de C-04
- **Riesgos**: el estado global de los módulos importados (caché, `sys.argv`, `print`) contamina la salida; las salidas tienen que cuadrar en tres runtimes. Es la característica de F2 con más probabilidad de agotar los 3 intentos.
- **Incógnitas / preguntas abiertas**: ¿se conserva `session-context.sh` como envoltorio para quien no tenga node?

### C-07 — Hook de ledger fusionado

- **Requisito origen**: spec §Alcance F2
- **Descripción**: `ledger-lint-warn.sh` (6-8 s) y `progress-line.sh` (6-7,5 s) parsean el ledger dos veces en cada edición de `tasks.md`. Se unen en un solo Python en modo python del launcher que parsea una vez y emite los dos mensajes, conservando el debounce con lock.
- **Complejidad**: Media
- **Esfuerzo**: 6 h (7,2 h) · confianza Media
- **Previsión IA**: 1,2 M in / 120k out tok · 7,18 € · 2,98 h IA
- **Coste**: (7,2 h × 50) + tokens = **367 €**
- **Impacto / áreas afectadas**: `hooks/ledger-lint-warn.sh`, `hooks/progress-line.sh`, `hooks/hooks.json`, `hooks/run-hook.mjs`, `agent-kits/shared/ledger-lint.py`, `progress-report.py`, `tests/hook-post-preflight.test.mjs`, `interop/`
- **Dependencias y prerequisitos**: C-00
- **Riesgos**: cambiar la lista de hooks registrados afecta a `hooks.json` en los 3 runtimes y a `/doctor`.
- **Incógnitas / preguntas abiertas**: ninguna relevante

### C-08 — `mark-docs-pending` dentro de node

- **Requisito origen**: spec §Alcance F2
- **Descripción**: el hook solo crea un fichero vacío (3,6-4,6 s por Write/Edit en `docs/`). Se mueve a `run-hook.mjs` con los mismos filtros de ruta y exclusiones.
- **Complejidad**: Baja
- **Esfuerzo**: 3 h (3,6 h) · confianza Alta
- **Previsión IA**: 0,5 M in / 50k out tok · 2,99 € · 1,24 h IA
- **Coste**: (3,6 h × 50) + tokens = **183 €**
- **Impacto / áreas afectadas**: `hooks/mark-docs-pending.sh`, `hooks/run-hook.mjs`, `hooks/opencode-plugin.js`, `hooks/hooks.json`, `tests/hook-*.test.mjs`, `interop/`
- **Dependencias y prerequisitos**: ninguna
- **Riesgos**: equivalencia con el adaptador de OpenCode.
- **Incógnitas / preguntas abiertas**: ninguna

### C-09 — `dev-cycle.md` núcleo + fases bajo demanda

- **Requisito origen**: spec §Alcance F2; ADR-008
- **Descripción**: separar `commands/dev-cycle.md` (55 KB, ~15,4k tokens) en un núcleo y `references/` por fase: Fase 2 (líneas 74-374, 18,3k caracteres), ciclo Jira (3,5k) y subagentes/Knowledge Gate (2,5k), con «lee X solo al llegar a Y». `quick-implement` deja de leerlo entero. Ahorro estimado: 6-8k tokens por vía rápida. Comprobación de 0 párrafos perdidos.
- **Complejidad**: Alta
- **Esfuerzo**: 14 h (16,8 h) · confianza Media
- **Previsión IA**: 3,0 M in / 300k out tok · 17,94 € · 7,45 h IA
- **Coste**: (16,8 h × 50) + tokens = **858 €**
- **Impacto / áreas afectadas**: `commands/dev-cycle.md`, ubicación nueva de las referencias (los comandos no tienen carpeta `references/`: hay que decidir dónde viven y cómo las resuelve la regla 5 en Codex/OpenCode), `skills/quick-implement/SKILL.md`, `scripts/export-interop.py`, 6 suites que citan `dev-cycle.md` (`test_lint_plugin.py`, `test_plan_review_caller.py`, `test_project_pieces.py`, `test_review_jira_owner.py`, `test_graphiti_security.py`, `installer.test.mjs`), `tests/test_skill_size.py` (`--diet-check`), `docs/FLOWS.md` (+ EN)
- **Dependencias y prerequisitos**: C-00; requisito de C-13 (perfil `lite`)
- **Riesgos**: **regresión de comportamiento del orquestador** (una fase que no se carga cuando toca); tests que buscan frases literales; las referencias tienen que viajar a interop.
- **Incógnitas / preguntas abiertas**: ubicación de las referencias de un comando y cómo se exportan a Codex/OpenCode

### C-10 — Memoria gobernada condicional en `knowledge-check.md`

- **Requisito origen**: spec §Alcance F2
- **Descripción**: los ~7k caracteres de «Consulta de la memoria gobernada» pasan a una referencia que solo se lee si el proyecto tiene memoria gobernada activa. Lo leen 8 agentes; ahorro estimado de 10-14k tokens por ciclo.
- **Complejidad**: Media
- **Esfuerzo**: 4 h (4,8 h) · confianza Media
- **Previsión IA**: 0,8 M in / 80k out tok · 4,78 € · 1,99 h IA
- **Coste**: (4,8 h × 50) + tokens = **245 €**
- **Impacto / áreas afectadas**: `agent-kits/shared/knowledge-check.md`, referencia nueva, `tests/test_knowledge_router.py`, `tests/test_graphiti_security.py`
- **Dependencias y prerequisitos**: ninguna
- **Riesgos**: si la condición falla, un consumidor con memoria gobernada deja de consultarla sin aviso. Mitigación: condición determinista (existencia de config o directorio) comprobable en una línea.
- **Incógnitas / preguntas abiertas**: condición exacta de activación (¿`docs/knowledge/approved/`? ¿capacidad `kwipu`/`graphiti` activa?)

### F2 opcional

### C-15 — Cierre del Job Object sin segundo Python en salida limpia (con spike)

- **Requisito origen**: hallazgo del evaluator, `hooks/run-hook.mjs:233-240` (`stop()` en cada `exit`, línea 316)
- **Descripción**: en Windows cada hook paga un Python extra al salir solo para cerrar el Job Object. Spike de 2 h para decidir si el supervisor puede cerrar el job él mismo en salida limpia (o si node puede soltar el handle) sin perder la limpieza de procesos nietos. Si el spike sale bien, se implementa. Ahorro potencial: un arranque de Python por hook en Windows (~1 s aquí).
- **Complejidad**: Alta
- **Esfuerzo**: 8 h (9,6 h; incluye el spike) · confianza Baja
- **Previsión IA**: 1,6 M in / 160k out tok · 9,57 € · 3,97 h IA
- **Coste**: (9,6 h × 50) + tokens = **490 €**
- **Impacto / áreas afectadas**: `hooks/run-hook.mjs`, `hooks/runtime-supervisor.py`, `tests/test_hook_supervisor.py`, `tests/hook-budget.test.mjs`
- **Dependencias y prerequisitos**: C-00
- **Riesgos**: **alto.** El supervisor existe por los gotchas de hooks-runtime: procesos huérfanos, y el `-journal` de C-05 lo confirma. Un fallo deja procesos vivos o reintroduce bloqueos.
- **Incógnitas / preguntas abiertas**: viabilidad técnica (la decide el spike, con salida go/no-go propia)

### C-16 — `review-lens-select` con una lectura por fichero

- **Requisito origen**: prompt «Opcional»
- **Descripción**: hoy abre cada fichero dos veces (38 s con 1.081 ficheros). Pasa a una sola lectura con los dos análisis sobre el mismo contenido.
- **Complejidad**: Baja
- **Esfuerzo**: 2 h (2,4 h) · confianza Alta
- **Previsión IA**: 0,4 M in / 40k out tok · 2,39 € · 0,99 h IA
- **Coste**: (2,4 h × 50) + tokens = **122 €**
- **Impacto / áreas afectadas**: `skills/adversarial-review/scripts/review-lens-select.py` + su test
- **Dependencias y prerequisitos**: ninguna
- **Riesgos**: bajos; ya tiene tests.
- **Incógnitas / preguntas abiertas**: ninguna

### C-17 — Kit shared resuelto una vez por fichero

- **Requisito origen**: prompt «Opcional»
- **Descripción**: el `find` de 6 raíces aparece unas 80 veces (~1.200 tokens por `/dev-cycle`). Cada agente/comando lo resolvería una sola vez al principio y reutilizaría `$SHAREDKIT`.
- **Complejidad**: Media (prosa en muchos ficheros, con linter y tests acoplados a la regla 5)
- **Esfuerzo**: 4 h (4,8 h) · confianza Media
- **Previsión IA**: 0,8 M in / 80k out tok · 4,78 € · 1,99 h IA
- **Coste**: (4,8 h × 50) + tokens = **245 €**
- **Impacto / áreas afectadas**: `agents/*.md`, `commands/*.md`, fragmentos de `agent-kits/shared/*.md`, `scripts/lint_plugin.py` (regla 5), `interop/`
- **Dependencias y prerequisitos**: mejor después de C-09 (evita editar dos veces `dev-cycle.md`)
- **Riesgos**: los shells no comparten estado entre llamadas Bash, así que la variable tiene que redeclararse por bloque o pasar a una ruta resuelta por el agente. El ahorro real puede ser menor.
- **Incógnitas / preguntas abiertas**: ¿mecanismo (variable por bloque o ruta escrita por el agente)?

### C-18 — `skill-index` solo con nombres en Claude Code

- **Requisito origen**: prompt «Opcional»
- **Descripción**: en Claude Code el índice de SessionStart duplica el listado nativo. Con solo nombres (o nada) se ahorran ~650 tokens por sesión. En Codex/OpenCode se queda como está.
- **Complejidad**: Baja
- **Esfuerzo**: 2 h (2,4 h) · confianza Media
- **Previsión IA**: 0,4 M in / 40k out tok · 2,39 € · 0,99 h IA
- **Coste**: (2,4 h × 50) + tokens = **122 €**
- **Impacto / áreas afectadas**: `agent-kits/shared/skill-index.py`, `hooks/session-context.sh` (o C-06), su test
- **Dependencias y prerequisitos**: interactúa con C-01. Si tras C-01 siguen faltando skills en el listado nativo, el índice compacto es la única forma de que el modelo las conozca, y recortarlo empeora la activación.
- **Riesgos**: degradar la activación (ver dependencia).
- **Incógnitas / preguntas abiertas**: decidir después de medir C-01 en una sesión real

### F3 — Modelos locales

### C-11 — Ids no Claude y `model` en interop

- **Requisito origen**: spec §Alcance F3; ADR-009
- **Descripción**: `model-tier.py` admite ids de proveedor local (hoy `MODELOS_ALIAS` + `^claude-`, líneas 43-49) y `export-interop.py` emite `model` en `interop/opencode/agents` y `interop/codex/agents/*.toml` (hoy solo `model_reasoning_effort`, línea 464) cuando haya mapeo. ADR-009 se revisa.
- **Complejidad**: Alta
- **Esfuerzo**: 10 h (12 h) · confianza Baja
- **Previsión IA**: 2,0 M in / 200k out tok · 11,96 € · 4,96 h IA
- **Coste**: (12 h × 50) + tokens = **612 €**
- **Impacto / áreas afectadas**: `agent-kits/shared/model-tier.py`, `scripts/export-interop.py`, `install/install.mjs` (posible), `tests/test_export_interop.py`, test de model-tier, `docs/INTEROP.md` (+ EN), ADR-009
- **Dependencias y prerequisitos**: decisión de diseño. `export-interop.py` es determinista y no conoce los modelos del consumidor, así que el mapeo tiene que vivir en el consumidor (instalador o `dev.json` leído en runtime). Candidato a `architect`.
- **Riesgos**: romper el determinismo de interop (`--check` es puerta de CI y de `release.py`); formatos de `model` distintos en cada runtime.
- **Incógnitas / preguntas abiertas**: formato de id (`ollama/qwen3:32b` en OpenCode frente a `model` + `model_provider` en Codex) y dónde vive el mapeo

### C-12 — `ledger-write.py`

- **Requisito origen**: spec §Alcance F3
- **Descripción**: script determinista con subcomandos para marcar el estado de una tarea, añadir la evidencia `RED:` y abrir la cabecera `## Revisión de dos lentes — intento N:`. Así el modelo no escribe formatos exactos y se eliminan los bucles de reintento de ledger-lint. Se actualiza la prosa de `implementer`, `adversarial-review`, `tdd` y `dev-cycle` para usarlo.
- **Complejidad**: Alta
- **Esfuerzo**: 12 h (14,4 h) · confianza Media
- **Previsión IA**: 2,4 M in / 240k out tok · 14,35 € · 5,96 h IA
- **Coste**: (14,4 h × 50) + tokens = **734 €**
- **Impacto / áreas afectadas**: `agent-kits/shared/` (nuevo + tests), `ledger-lint.py` (compatibilidad), `agents/implementer.md`, `skills/adversarial-review/`, `skills/tdd/`, `commands/dev-cycle.md`, `agent-kits/shared/task-brief.py`, `interop/`
- **Dependencias y prerequisitos**: C-09 (para no editar el `dev-cycle.md` monolítico); dueño único del formato: `ledger-lint` lo valida y `ledger-write` lo escribe (un rol, un dueño)
- **Riesgos**: escritura concurrente sobre `tasks.md` (subagentes en paralelo): hace falta un lock. Los ledgers de 260-520 KB obligan a reescrituras eficientes.
- **Incógnitas / preguntas abiertas**: ¿es obligatorio también para Claude o solo en perfil `lite`?

### C-13 — Perfil `lite`

- **Requisito origen**: spec §Alcance F3
- **Descripción**: `dev.json` `perfil: lite` desactiva el paralelismo y los subagentes, reduce el tope del brief (`BRIEF_TOPE_CHARS`), obliga a usar `ledger-write.py` y carga solo el núcleo de `dev-cycle`. Lo soportan `/setup` y `/doctor`.
- **Complejidad**: Media-Alta
- **Esfuerzo**: 8 h (9,6 h) · confianza Baja
- **Previsión IA**: 1,6 M in / 160k out tok · 9,57 € · 3,97 h IA
- **Coste**: (9,6 h × 50) + tokens = **490 €**
- **Impacto / áreas afectadas**: `commands/setup.md`, `commands/dev-cycle.md` (núcleo), `agent-kits/shared/task-brief.py`, `doctor.py`, `docs/CONVENTIONS.md` regla 9 (+ EN), `interop/`
- **Dependencias y prerequisitos**: C-09 y C-12
- **Riesgos**: choque con las puertas no negociables. La revisión de dos lentes y el qa-gate tienen que seguir activos; si el usuario quiere recortarlos, cambia el alcance y la constitución.
- **Incógnitas / preguntas abiertas**: qué puede recortar el perfil (ver preguntas abiertas)

### C-14 — Aviso de contexto corto en `/doctor` + mínimos por tramo

- **Requisito origen**: spec §Alcance F3
- **Descripción**: `/doctor` lee la configuración local de OpenCode/Codex (y Ollama solo si está en un host local y la capacidad está activa) y avisa ⚠️ si el contexto es menor que el mínimo del tramo. `docs/INTEROP.md` + `docs/en/INTEROP.md` documentan los tramos: 8-9B solo lectura; 32B con ≥ 64k para la vía rápida.
- **Complejidad**: Media
- **Esfuerzo**: 5 h (6 h) · confianza Media
- **Previsión IA**: 1,0 M in / 100k out tok · 5,98 € · 2,48 h IA
- **Coste**: (6 h × 50) + tokens = **306 €**
- **Impacto / áreas afectadas**: `agent-kits/shared/doctor.py`, `test_doctor.py`, `docs/INTEROP.md`, `docs/en/INTEROP.md`, `commands/doctor.md`
- **Dependencias y prerequisitos**: C-11 (saber qué modelo usa cada rol)
- **Riesgos**: los mínimos por tramo salen de la auditoría, no de una prueba real; se documentan como orientativos.
- **Incógnitas / preguntas abiertas**: validación real en un equipo con Ollama (fuera de esta máquina)

### Partidas de proceso (una por fase)

| ID | Qué incluye | h base (con margen) | Tokens in / out | Coste |
|----|-------------|---------------------|-----------------|-------|
| P-F1 | CHANGELOG doble, docs espejo, `export-interop.py --check`, verificación en Linux, `release.py` | 2 h (2,4 h) | 0,3 M / 30k | 122 € |
| P-F2 | Lo anterior + revalidar el plan contra `master` (+0,5 h) | 2,5 h (3 h) | 0,3 M / 30k | 152 € |
| P-F3 | Lo anterior + revalidar el plan contra `master` (+0,5 h) | 2,5 h (3 h) | 0,3 M / 30k | 152 € |

---

## ⚖️ Comparativa

| # | Característica | Complejidad | Horas (con margen) | Coste € | Tokens (facturables) | Beneficio medido/estimado | Prioridad | Confianza |
|---|---------------|-------------|-------|---------|--------|---------------------------|-----------|-----------|
| C-00 | Benchmark | Media | 7,2 h | 365 € | 0,99 M | prerequisito de aceptación | Alta 🟠 | Alta |
| C-01 | Descriptions ≤ 600 | Media | 9,6 h | 490 € | 1,76 M | −2.100 tok fijos/sesión | Alta 🟠 | Media |
| C-02 | Prefiltro guard en node | Media | 7,2 h | 368 € | 1,54 M | ≈ −5,7 min/sesión aquí | Crítica 🔴 | Media |
| C-03 | Statusline 1 Python | Baja-Media | 6 h | 305 € | 0,99 M | −2 procesos y caché por refresco (9,8 s hoy) | Alta 🟠 | Media |
| C-04 | Timeout SessionStart + captura aislada | Baja | 2,4 h | 122 € | 0,44 M | acota 14-22 s; parte de 2,6 s/turno | Alta 🟠 | Media |
| C-05 | Temporales sqlite | Baja | 3,6 h | 183 € | 0,55 M | higiene (20 parejas huérfanas) | Media 🟡 | Alta |
| C-06 | session-context 1 Python | Alta | 14,4 h | 734 € | 2,64 M | ~20 → ~2 procesos por arranque | Alta 🟠 | Media |
| C-07 | Hook de ledger fusionado | Media | 7,2 h | 367 € | 1,32 M | ≈ −6-7 s por edición de `tasks.md` | Media 🟡 | Media |
| C-08 | mark-docs en node | Baja | 3,6 h | 183 € | 0,55 M | −3,6-4,6 s por edición en `docs/` | Media 🟡 | Alta |
| C-09 | dev-cycle núcleo + fases | Alta | 16,8 h | 858 € | 3,30 M | −6-8k tok por vía rápida | Alta 🟠 | Media |
| C-10 | Memoria gobernada condicional | Media | 4,8 h | 245 € | 0,88 M | −10-14k tok por ciclo | Alta 🟠 | Media |
| C-15 | Job Object sin 2.º Python (opc.) | Alta | 9,6 h | 490 € | 1,76 M | ~−1 s por hook en Windows | Media 🟡 | Baja |
| C-16 | review-lens-select 1 lectura (opc.) | Baja | 2,4 h | 122 € | 0,44 M | ~−50 % en diffs grandes (38 s) | Baja 🟢 | Alta |
| C-17 | SHAREDKIT una vez (opc.) | Media | 4,8 h | 245 € | 0,88 M | ~−1.200 tok por `/dev-cycle` | Baja 🟢 | Media |
| C-18 | skill-index solo nombres (opc.) | Baja | 2,4 h | 122 € | 0,44 M | −650 tok/sesión | Baja 🟢 | Media |
| C-11 | Ids locales + model en interop | Alta | 12 h | 612 € | 2,20 M | habilita el tiering con modelos locales | Media 🟡 | Baja |
| C-12 | ledger-write.py | Alta | 14,4 h | 734 € | 2,64 M | elimina bucles de formato | Media 🟡 | Media |
| C-13 | Perfil lite | Media-Alta | 9,6 h | 490 € | 1,76 M | vía rápida en 32B | Media 🟡 | Baja |
| C-14 | Doctor contexto corto + INTEROP | Media | 6 h | 306 € | 1,10 M | evita truncado silencioso | Media 🟡 | Media |
| P-F1..3 | Proceso por fase | — | 8,4 h | 426 € | 0,99 M | — | — | Alta |
| | **Total** | | **152,4 h** | **7.768 €** + 40 € lectura de caché = **7.808 €** | **27,17 M** | | | |

Por fase:

| Fase | Horas humanas (margen) | Horas IA (margen) | Supervisión | Presupuesto humano + tokens | Ejecución con agentes |
|------|------------------------|-------------------|-------------|-----------------------------|-----------------------|
| F1 (C-00..C-05 + P-F1) | 38,4 h | 14,9 h | 3,7 h | 1.966 € | ~232 € |
| F2 núcleo (C-06..C-10 + P-F2) | 49,8 h | 20,4 h | 5,1 h | 2.552 € | ~317 € |
| F2 opcional (C-15..C-18) | 19,2 h | 7,9 h | 2,0 h | 984 € | ~124 € |
| F3 (C-11..C-14 + P-F3) | 45,0 h | 18,1 h | 4,5 h | 2.305 € | ~282 € |
| **Total** | **152,4 h** | **61,3 h** | **15,3 h** | **7.808 €** | **~954 €** |

---

## 💰 Presupuesto total

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 127 h × 50 €/h | 6.350,00 € |
| Margen de contingencia | +20 % sobre desarrollo base | 1.270,00 € |
| Tokens IA (input) | 24,7 M × 4,14 €/M | 102,26 € |
| Tokens IA (output) | 2,47 M × 18,40 €/M | 45,45 € |
| Lectura de caché (estimada) | ~217 M (8× facturables, supuesto) × 0,184 €/M | 39,99 € |
| **Total estimado (con margen)** | | **7.807,70 €** |
| Del cual, núcleo sin opcionales (C-15..C-18 fuera) | 133,2 h + tokens | 6.823,38 € |
| Coste de ejecución con agentes | 15,33 h supervisión × 50 € + 187,70 € tokens | **954,06 €** |

---

## ⚡ Productividad IA (humano vs. IA)

| KPI | Valor |
|-----|-------|
| Horas humanas estimadas | 152,4 h (127 h base) |
| Horas IA (ejecución) | 61,3 h (51,1 h base = 27,17 M ÷ 531.798,5 tok/h) |
| Supervisión humana | 15,3 h (25 % de las horas IA) |
| **Horas totales (IA + supervisión)** | **76,6 h** |
| Horas ahorradas | 75,8 h |
| **Ahorro** | **49,7 %** |
| **Multiplicador de productividad** | **×2,0** |
| FTE equivalentes *(opcional)* | 0,47 |

> Horas mostradas **con el margen de contingencia (+20 %)** ya aplicado sobre las horas base (humanas e IA). El multiplicador es bajo a propósito: las horas IA incluyen 3 intentos de revisión por característica (calibración). En las últimas iniciativas la IA real quedó por debajo de lo estimado (panel-redesign −75 %) o muy por encima cuando se hizo bloqueante cada Minor (training-data-services +761 %). Por eso la confianza de esta fila es Baja.

---

## 🎯 Recomendación

- **Veredicto**: **go por tramos.** Go a F1 ahora. F2 núcleo, condicionada a la medición de F1 y a revalidar el plan. F3, condicionada a resolver las incógnitas de diseño de C-11/C-13 (paso `architect` recomendado) y a tener dónde validar un modelo de 32B. Opcionales de F2: C-16 sí (barata y segura); C-15 solo si su spike sale bien; C-17/C-18 se deciden con datos de C-01/C-09.
- **Quick wins** (bajo coste, alto valor): **C-02** (la mayor parte de la espera por 368 €), C-04, C-05, C-03, C-08, C-16.
- **Costosas / a valorar**: C-09 y C-06 (alto valor, riesgo de regresión del orquestador y del arranque); C-11 y C-13 (incógnitas de diseño); C-15 (riesgo alto, spike primero).
- **Orden sugerido**: C-00 → C-02 → C-04 → C-05 → C-03 → C-01 → (release F1) → C-08 → C-07 → C-10 → C-06 → C-09 → C-16 → [C-15 spike] → [C-17, C-18] → (release F2) → C-11 → C-12 → C-14 → C-13 → (release F3). Motivo: medir primero; luego lo que más espera quita al menor riesgo; C-01 al final de F1 para poder medir su efecto en el listado en una sesión real; C-09 antes que C-12/C-13/C-17 para no editar dos veces `dev-cycle.md`; C-13 al final porque depende de C-09 y C-12.
- **Fuera de alcance recomendado**: reescribir el supervisor como binario nativo, el benchmark de calidad de modelos locales y verificar «Qwen 3.5 9B».

---

## ⚠️ Riesgos transversales

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| El bucle de revisión se dispara (patrón training-data-services/graphiti) | Media | Alto | Minor no bloqueante; 3 intentos presupuestados; lente C solo donde toca; criterios cuantitativos por tarea |
| Regresión de activación al recortar descriptions (C-01, C-18) | Media | Medio | Literales de evals intactos, medir el listado en sesión real, `headless.yml` si hay secret |
| Debilitar el guard de identidad exacta (C-02, C-15) | Baja | Crítico | Test de paridad node/Python, fallback a Python ante cualquier duda, lente C obligatoria, adenda a ADR-023 |
| Tests acoplados a frases literales y a la estructura de ficheros (C-09, C-10, C-17) | Alta | Medio | Inventario de las suites afectadas en el plan; `--diet-check`; regenerar interop en la misma tarea |
| Ruido de medición en esta máquina (OneDrive, 2,8 GB libres) | Alta | Medio | Medianas relativas en la misma sesión; sin umbrales absolutos en CI; repetir en Linux |
| F3 no validable aquí de extremo a extremo (sin memoria para 32B) | Alta | Medio | Validación estática + prueba manual del usuario en otro equipo; mínimos por tramo como orientativos |
| Envejecimiento del plan entre fases (F2/F3 diferidas) | Media | Medio | +0,5 h de revalidación contra `master` al abrir cada fase (incluido) |
| Memoria del equipo durante la ejecución (las suites completas no caben con poca RAM) | Media | Medio | Suites dirigidas por tarea y suite completa en Linux/CI antes del push |

---

## ➡️ Siguiente paso

Si hay **go por tramos**, el agente **`planner`** genera `improvement-plan.md` + `tasks.md` en esta carpeta, con **F1 completa** (C-00..C-05 + P-F1) detallada. F2 y F3 quedan como fases diferidas con su presupuesto y la tarea de revalidación al abrirlas. Antes de planificar F3, recomiendo el paso opcional **`architect`** para C-11 (dónde vive el mapeo de modelos del consumidor) y C-13 (qué recorta el perfil `lite`). El `planner` hereda las horas y costes de esta evaluación por característica, rellena la fila **Plan** de esta evaluación y el campo `plan:` de la spec.

## ✅ Decisión de la puerta (2026-10-27)

El usuario aprobó en `/pm-cycle` el **go por tramos** con estas respuestas a las preguntas abiertas:

1. **Go a F1 ahora** (C-00..C-05 + P-F1). F2 y F3 quedan diferidas, cada una con una tarea de revalidación contra `master` al abrirse.
2. **Opcionales de F2:** C-16 entra. C-15 entra solo si su spike de 2 h sale bien. C-17 y C-18 se deciden al abrir F2, con los datos de C-01 y C-09.
3. **Perfil `lite` (C-13):** solo recorta paralelismo y contexto. **No** toca la revisión de dos lentes ni el `qa-gate`, así que la constitución no cambia.
4. **C-11:** paso `architect` antes de F3, para decidir el formato de ids en OpenCode y Codex y dónde vive el mapeo del consumidor.
5. **Timeout de SessionStart:** 30 s en F1 (C-04); bajar a 10 s cuando C-06 lo deje en un solo Python.
6. **Una release por fase.**
7. **F3 sin equipo con Ollama:** validación estática y prueba manual del usuario en otro equipo; los mínimos por tramo son orientativos.
8. **Benchmark (C-00):** se versionan el procedimiento y la línea base de esta máquina, marcada como tal (Windows + OneDrive, poca RAM).
