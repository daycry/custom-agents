---
design: n/a               # el paso architect se hará solo antes de F3 (C-11/C-13); F1 y F2 no lo necesitan
test-plan: n/a (sin UI)
generacion:
  inicio: 2026-10-27T14:14:18Z
  fin: 2026-10-27T14:23:52Z
  fuente: medido
  fuente_id: src-d2ceb5c719af848b4c213bb2d521d0f003976923acb613d7512912ccbeb6a09e
  ventana_id: win-e20bc509ddb34b0d9d593d35104a422f
  revision_medicion: 1
  medicion_persistida: true
  tokens_reales: { entrada: 20, salida: 51792, cache_creacion: 66534, cache_lectura: 1007417 }
  eur: 1.44
  horas_ia: 0.22
  duracion: 13m
  ratio_usado: 531798.5
  avisos: ["CALIBRATION: filas marcadas (estimado) fuera de la mediana (informativo)"]
---

# 2026-10-27-plugin-optimization

> Plan de la optimización del plugin en tres frentes medidos (latencia de hooks, tokens fijos y bajo demanda, viabilidad con modelos locales): F1 detallada y lista para ejecutar; F2 y F3 diferidas, con presupuesto y esqueleto.

| | |
|---|---|
| **Fecha** | 2026-10-27 |
| **Estado** | en-progreso |
| **Tipo** | Infra / Refactor (rendimiento y tokens), con una capacidad nueva (benchmark) |
| **Prioridad** | Alta 🟠 |
| **Solicitante** | Daycry (vía `/pm-cycle`) |
| **Responsable** | `implementer` (supervisa Daycry) |
| **Spec** | [`spec.md`](spec.md) |
| **Evaluación** | [`evaluation.md`](evaluation.md) — go por tramos, decisión de la puerta del 2026-10-27 |
| **Diseño** | n/a (paso `architect` previsto solo antes de F3, tarea T-21) |

> **Alcance de ejecución hoy:** solo **F1** (T-01..T-07). **F2** (T-08..T-19) y **F3** (T-20..T-26) quedan en `borrador` y **diferidas**: su primera tarea es revalidar este plan contra `master`; hasta entonces su detalle es un esqueleto («se concreta al revalidar»). Una release por fase (`scripts/release.py`).

---

## Cuadro de mando

Total de la iniciativa (heredado de la evaluación; F1 aparte entre paréntesis).

| Métrica | Estimado | Real | Confianza |
|--------|---------|------|-----------|
| Tiempo humano | **152,4h** (127h base +20 %) · F1: **38,4h** (32h base) | 0h | Media |
| Tiempo IA (ejecución) | **61,3h** (+ 15,3h supervisión) · F1: **14,9h** (+ 3,7h) | 0h | Baja |
| Coste total (presupuesto humano + tokens) | **7.808 €** · F1: **1.966 €** | 0 € | Media |
| Coste de ejecución con agentes | **~954 €** · F1: **~232 €** | 0 € | Baja |
| Tokens IA (facturables) | **27,17M** (in 24,7M / out 2,47M) · F1: **6,6M** (in 6,0M / out 0,6M) | 0 | Baja |
| Multiplicador productividad | **×2,0** · F1: **×2,1** | — | — |
| Tareas | **26** (F1: 7 · F2: 12 · F3: 7) | 0 hechas | — |

---

## Estimación por fase

| Fase | Estimado (h, con margen) | Tokens (in / out) | Coste € |
|------|-------------|-------------------|---------|
| Fase 1 — Quick wins medibles (T-01..T-07) **— ejecutable ahora** | 38,4 | 6,0M / 600k | 1.966 |
| Fase 2 — Reestructuración, diferida (T-08..T-19): núcleo 49,8 h + opcional 19,2 h | 69,0 | 11,4M / 1,14M | 3.536 |
| Fase 3 — Modelos locales, diferida (T-20..T-26) | 45,0 | 7,3M / 730k | 2.305 |
| **Total** | **152,4h** | **24,7M / 2,47M** | **7.808 €** (F1+F2+F3 = 7.807; ±1 € de redondeo) |

F2 núcleo (T-08..T-14, T-19; sin C-15/C-17/C-18): 49,8 h · 2.552 €. F2 opcional (T-15..T-18; C-15 solo si su spike sale bien, C-17/C-18 se deciden al abrir F2): 19,2 h · 984 €. C-16 (T-14) está decidido «sí» por la puerta pero la evaluación lo contabiliza en el bloque opcional; el reparto no cambia el total.

---

## Presupuesto económico

**Coste = (horas × tarifa) + coste de tokens de IA.** Todos los importes en **EUR**. Las cifras **heredan** la evaluación por característica (`evaluation.md`); este plan solo las reparte en tareas y no las re-estima.

### Supuestos (ajustables)

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | 50 €/h | `.claude/rates.json` `tarifaHora` |
| Modelo IA asumido | claude-opus-5-5 | `rates.json` `modeloIA` |
| Precio input | 4,14 € / 1M tokens | Mezcla 50/50 de entrada (4 USD) y creación de caché (5 USD) × 0,92; supuesto de reparto |
| Precio output | 18,40 € / 1M tokens | 20 USD × 0,92; `verificadoEl: 2026-10-20` |
| Lectura de caché | 0,184 € / 1M tokens | volumen supuesto 8× los facturables; no se reparte por tarea |
| Tipo de cambio | 1 USD = 0,92 € | supuesto fijo de `rates.json` |
| Margen de contingencia | 20 % | sobre horas base humanas e IA; las horas de las tareas ya lo llevan |
| Supervisión | 25 % de las horas IA | `rates.json` `ratioSupervision` |
| Ratio tokens→hora-IA | 531.798,5 tok/h | mediana de `CALIBRATION.md` |
| Rondas de revisión | 3 intentos por característica | lentes A+B; C en C-02, C-04, C-05, C-15; D en C-02, C-03, C-06, C-07, C-15, C-16 (estimado dentro de la IA de cada tarea) |

### Desglose (toda la iniciativa)

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 127h × 50 €/h | 6.350,00 € |
| Margen de contingencia | +20 % sobre desarrollo base | 1.270,00 € |
| Tokens IA (input) | 24,7M × 4,14 €/M | 102,26 € |
| Tokens IA (output) | 2,47M × 18,40 €/M | 45,45 € |
| Lectura de caché (estimada) | ~217M × 0,184 €/M | 39,99 € |
| **Total estimado (con margen)** | | **7.807,70 €** |

Solo F1: 32h base × 50 = 1.600 € + margen 320 € + tokens 35,88 € (6,0M in 24,84 € + 0,6M out 11,04 €) + caché ~9,7 € ≈ **1.966 €**. Ejecución con agentes F1: 3,7h supervisión × 50 + ~46 € de tokens ≈ **232 €**.

---

## Previsión de tokens (por fase)

Base: claude-opus-5-5 · precios de la tabla de supuestos.

| Fase | Input (tok) | Output (tok) | Total (tok) | Coste € (solo tokens) |
|------|------------|-------------|-------------|---------|
| Fase 1 | 6,0M | 600k | 6,6M | 35,88 |
| Fase 2 | 11,4M | 1,14M | 12,54M | 68,18 |
| Fase 3 | 7,3M | 730k | 8,03M | 43,65 |
| **Total** | **24,7M** | **2,47M** | **27,17M** | **147,71** (+ ~40 € de lectura de caché) |

**Método de estimación:** el de la evaluación: ficheros a leer × tamaño medio + generación de código/tests, más 3 intentos de revisión con corrección por característica (la revisión pesa ~60 % de los tokens). Los Minor no bloquean el cierre (lección de training-data-services). Cifras de F2/F3 son previsión diferida y se recalculan al revalidar.

---

## Productividad IA (humano vs. IA)

| KPI | Toda la iniciativa | Solo F1 |
|-----|--------------------|---------|
| Horas humanas estimadas | 152,4 h (127 h base) | 38,4 h (32 h base) |
| Horas IA (ejecución) | 61,3 h (supuesto; 27,17M ÷ 531.798,5 tok/h, +20 %) | 14,9 h |
| Supervisión humana | 15,3 h (25 % de las horas IA) | 3,7 h |
| **Horas totales (IA + supervisión)** | **76,6 h** | **18,6 h** |
| Horas ahorradas | 75,8 h | 19,8 h |
| **Ahorro** | **49,7 %** | **51,6 %** |
| **Multiplicador de productividad** | **×2,0** | **×2,1** |
| FTE equivalentes *(opcional)* | 0,47 | 0,12 |

> Horas **con el margen de contingencia (+20 %)** ya aplicado. Las horas IA son un supuesto y incluyen 3 intentos de revisión por característica; confianza Baja (training-data-services se desvió +761 % cuando cada Minor fue bloqueante; panel-redesign −75 %).

---

## Resumen ejecutivo

El plugin cuesta hoy unos 6 minutos de espera síncrona por sesión en esta máquina (Windows + OneDrive, 2,8 GB libres) y ~2.000 tokens fijos evitables en descriptions. F1 corta lo más caro con el menor riesgo: un benchmark reproducible (C-00), el prefiltro del guard en node que evita lanzar Python en ~150 llamadas por sesión (C-02), un timeout en SessionStart (C-04), la limpieza de temporales sqlite (C-05), el statusline con una sola llamada Python y caché (C-03) y descriptions ≤ 600 caracteres (C-01). F2 reestructura arranque, hooks de ledger y comandos grandes; F3 prepara el plugin para modelos locales de 9B-32B. Cada fase se mide antes y después y se publica en su propia release.

### Objetivos

- Benchmark versionado con mediana por hook (≥ 10 ejecuciones, payloads fixture) y tokens fijos/bajo demanda, con la línea base de esta máquina marcada como tal.
- PreToolUse sin rol protegido: **cero procesos Python** y comparación versionada antes/después con ≥ 10 muestras por variante/runtime, calentamiento descartado, control Node, dispersión y fallos (CA-01), sin cambiar una sola expectativa de las suites de guard (CA-02, CA-03). Ajuste aprobado 2026-10-29: F1 no exige un porcentaje mínimo.
- Ninguna description de agente, skill o comando > 600 caracteres; tokens fijos ≥ ~2.000 menos que la línea base.
- Statusline: como máximo un proceso Python por refresco sin cambios, servido desde caché y sin el alias `python3` de WindowsApps (CA-04).
- SessionStart con `timeout: 30` vigilado por test; temporales sqlite huérfanos limpiados y sin acumulación (CA-05).

---

## Datos necesarios para un informe completo

- [x] **Requisitos funcionales** confirmados por el solicitante (spec `aprobada`; puerta go/no-go del 2026-10-27)
- [x] **Alcance** cerrado (F1 completa; F2/F3 diferidas; fuera de alcance en la spec)
- [x] **Criterios de éxito / métricas** acordados (spec §Criterios de aceptación, con [GWT])
- [x] **Accesos y credenciales** necesarios: ninguno externo; `ANTHROPIC_API_KEY` solo si se quisiera `evals/run.py`/`headless.yml` (opcional)
- [x] **Entornos** disponibles: local Windows (poca RAM) + réplica Linux (`python:3.11-slim`) antes de cada push
- [x] **Stakeholders** identificados: Daycry valida cada puerta
- [ ] **Dependencias externas**: un equipo con Ollama y ≥ 64k de contexto para validar F3 (no hace falta hasta F3; prueba manual del usuario)
- [x] **Restricciones** conocidas: multi-runtime, hooks exit 0 e informativos, bilingüe, release por script, máquina justa de memoria (sin suites completas en local)
- [x] **Tarifa/hora y supuestos de coste** confirmados (`.claude/rates.json`)

---

## Análisis de impacto

- **`hooks/run-hook.mjs`** — prefiltro del guard (C-02), `-I -S` en la captura de prompts (C-04). Zona de seguridad: ADR-023.
- **`hooks/hooks.json`** — `timeout` de SessionStart (C-04); copia regenerada en `interop/codex/hooks.json`.
- **`hooks/opencode-plugin.js`** — adaptador de OpenCode: comprobar si necesita el mismo prefiltro (C-02).
- **`agent-kits/shared/native-guardrail.py` y `native-roles.json`** — fuente de los roles protegidos; no cambia la decisión de deny.
- **`agent-kits/shared/knowledge-find.py`** — barrido de temporales y borrado del `-journal` (C-05).
- **`statusline/roadmap-statusline.sh` + script Python único** — statusline (C-03).
- **`scripts/` + `tests/`** — benchmark nuevo (C-00); `scripts/lint_plugin.py` (umbral 600, C-01).
- **`agents/*.md`, `skills/*/SKILL.md`, `commands/setup.md`, `commands/doctor.md`** — reescritura de 25 descriptions (C-01).
- **`docs/observability.md`, `docs/CONVENTIONS.md` (+ espejos `docs/en/`), CHANGELOG ×2** — procedimiento del benchmark, umbral nuevo, cierre de fase.
- **`interop/**`, `.codex-plugin/`, `.agents/plugins/`** — generado; se regenera en cada tarea que toque hooks/agentes/comandos.

---

## Cambios arquitectónicos

- **Medir antes de cambiar.** C-00 es dependencia de todas las demás: tres pasadas completas correctas con muestras, fuentes, entorno y dispersión versionados caracterizan la línea base, sin declarar estabilidad uniforme. Cada mejora temporal de F1 deja un control antes/después intercalado del mismo workload, fuentes identificadas, control de arranque y dispersión/fallos; una comparación inconcluyente no acredita ahorro global ni un fallo se acepta como éxito. Sin umbrales absolutos en CI por el ruido de esta máquina. Opción 2 de T-01 aplicada por delegación expresa del usuario el 2026-10-29.
- **Prefiltro de guard en node, decisión en Python.** Node solo responde «¿esta identidad nativa exacta es un rol protegido?». La decisión de deny sigue en `native-guardrail.py`. Si el mapa no se puede leer o es inválido, se lanza Python como hoy. Propuesta por defecto (a confirmar por la revisión): no cambiar el esquema de `native-roles.json` (`schema_version` 1) y atar la lista `PROTECTED` con un test de paridad node/Python; si la revisión prefiere una sola fuente física, `schema_version` 2 con compatibilidad. Adenda a ADR-023 propuesta vía `knowledge-curation.py propose` (no se edita el ADR a mano).
- **Descriptions: contrato de longitud.** El umbral del linter baja de 1.200 a 600; los literales que exige `evals/check.py` se conservan; la activación real no se prueba en CI (sin `ANTHROPIC_API_KEY`) y se declara como riesgo.
- **Statusline en un proceso.** Un único script Python recibe la entrada, calcula modelo/coste/ctx + segmento de roadmap y guarda caché por mtime de los ledgers activos; el shell solo resuelve el intérprete (sin alias de WindowsApps) y degrada en silencio.
- **Hooks siempre exit 0 e informativos**; sin `python3` → silencio. Nada de F1 cambia esa regla.

---

## Archivos a crear/modificar (F1)

| Archivo | Acción | Propósito |
|---------|--------|-----------|
| `scripts/bench-hooks.py`, `tests/test_bench_hooks.py`, `tests/fixtures/bench-hooks/` | Crear | Benchmark reproducible (C-00) |
| `docs/observability.md`, `docs/en/observability.md` | Modificar | Procedimiento del benchmark y su lectura (C-00) |
| `docs/roadmap/2026-10-27-plugin-optimization/testing/baseline-f1.md` | Crear | Línea base de esta máquina, marcada como tal (C-00) |
| `hooks/run-hook.mjs`, `hooks/opencode-plugin.js` | Modificar | Prefiltro del guard (C-02); `-I -S` en captura (C-04) |
| `tests/hook-guard-delivery.test.mjs`, `tests/hook-guard-prefilter.test.mjs`, `tests/test_native_prefilter_parity.py` | Modificar/Crear | Paridad y no-lanzamiento de Python (C-02) |
| `hooks/hooks.json`, `tests/test_hooks_config.py` | Modificar | `timeout: 30` de SessionStart (C-04) |
| `agent-kits/shared/knowledge-find.py`, `tests/test_knowledge_find.py` | Modificar | Barrido de temporales y `-journal` (C-05) |
| `statusline/roadmap-statusline.sh`, `agent-kits/shared/statusline-render.py`, `tests/test_statusline_cache.py` | Modificar/Crear | Statusline monoproceso con caché (C-03) |
| `agents/*.md`, `skills/*/SKILL.md`, `commands/setup.md`, `commands/doctor.md` | Modificar | Descriptions ≤ 600 (C-01) |
| `scripts/lint_plugin.py`, `tests/test_lint_plugin.py`, `docs/CONVENTIONS.md`, `docs/en/CONVENTIONS.md` | Modificar | Umbral 600 (C-01) |
| `interop/**`, `.codex-plugin/**`, `.agents/plugins/**` | Regenerar | `python3 scripts/export-interop.py` |
| `CHANGELOG.md`, `CHANGELOG.es.md` | Modificar | Cierre de F1 (P-F1) |

Nota de cuadre: el «Coste est.» por fase de `tasks.md` suma horas × 50 € + tokens por tarea y excluye la lectura de caché (~11 € en F1, ~40 € en total); las horas IA por tarea suman 61,2 h (61,3 h en la evaluación por redondeo).

Los ficheros exactos de cada tarea están en su campo `Archivos` de `tasks.md` (los lee `scope-check.py`). F2/F3: se fijan al revalidar.

---

## Dependencias y prerequisitos

- **Orden F1 (el de la evaluación):** T-01 (C-00) → T-02 (C-02) → T-03 (C-04) → T-04 (C-05) → T-05 (C-03) → T-06 (C-01) → T-07 (P-F1 + release). C-00 es prerequisito de todas las de rendimiento/tokens; C-01 va al final de F1 para medir su efecto en el listado en una sesión real.
- **F2 (tras release de F1 y revalidación T-08):** C-08 → C-07 → C-10 → C-06 → C-09 → C-16 → [C-15 spike] → [C-17, C-18] → release. C-09 antes que C-12/C-13/C-17 para no editar `dev-cycle.md` dos veces; C-06 permite bajar el timeout de SessionStart a 10 s.
- **F3 (tras release de F2, revalidación T-20 y paso `architect` T-21):** C-11 → C-12 → C-14 → C-13 → release. C-13 depende de C-09 y C-12; C-14 de C-11.
- **Restricciones de ejecución:** máquina justa de RAM → cada tarea se verifica con suites **dirigidas**; la suite completa y la réplica de `ci.yml` en Linux (`python:3.11-slim`, normalizando CRLF con `git -c core.autocrlf=false archive`) se corren antes del push (T-07), no en cada tarea.

---

## Criterios de aceptación (global)

- [ ] Existe `scripts/bench-hooks.py` con tests, procedimiento documentado (ES/EN) y línea base de esta máquina versionada y marcada como tal (T-01).
- [x] CA-01: sesión sin rol protegido → PreToolUse no lanza Python; comparación versionada con ≥ 10 muestras por variante/runtime, calentamiento descartado, control Node, dispersión y fallos, sin porcentaje mínimo en F1 (T-02, tabla y recibo en `testing/t02-native-prefilter.md`).
- [ ] CA-02/CA-03: suites de guard en verde sin cambiar expectativas; con `native-roles.json` corrupto se sigue emitiendo el diagnóstico (T-02).
- [ ] `hooks/hooks.json` declara `timeout: 30` en SessionStart y `test_hooks_config.py` lo vigila (T-03).
- [ ] CA-05: temporales sqlite `*.tmp` y `*.tmp-journal` de procesos muertos se eliminan y no se acumulan tras una muerte forzada (T-04).
- [ ] CA-04: statusline sin cambios en el ledger → ≤ 1 proceso Python, servido desde caché, sin alias de WindowsApps (T-05).
- [ ] Ninguna description > 600 caracteres; `lint_plugin.py` avisa a 600; `evals/check.py` en verde; tokens fijos ≥ ~2.000 menos que la línea base (T-06).
- [ ] Docs espejo ES/EN y los dos CHANGELOG actualizados; `export-interop.py --check` en verde; réplica Linux verde; release de F1 por `scripts/release.py` (T-07).
- [ ] Cada tarea de F1 deja en el ledger la tabla antes/después del benchmark y la revisión de dos lentes (C obligatoria en T-02).

---

## Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| Node y Python divergen al decidir qué es rol protegido (vía de omisión del guard) | Baja | Crítico | Test de paridad sobre tabla de identidades (mayúsculas, prefijos, espacios, Codex vs OpenCode); fallback a Python ante cualquier duda; Lente C obligatoria; adenda a ADR-023 |
| Regresión de activación al recortar descriptions | Media | Medio | Literales de `evals/cases/` intactos; medir el listado en sesión real; `headless.yml` si hay secret; reescribir por grupos revisables |
| El bucle de revisión se dispara (patrón training-data-services/graphiti) | Media | Alto | Minor no bloquea; 3 intentos presupuestados; Lente C solo donde toca; criterios cuantitativos por tarea |
| Ruido de medición en esta máquina (OneDrive, 2,8 GB libres) | Alta | Medio | Medianas relativas en la misma sesión; línea base marcada como tal; sin umbrales absolutos en CI; repetir en Linux |
| Timeout de 30 s corta la retoma si la mediana (14-22 s) empeora | Media | Medio | Valor alto en F1; se baja a 10 s solo tras C-06; el benchmark registra el caso |
| `-I -S` rompe imports de `journal.py` en la captura | Baja | Bajo | Subtarea de comprobación previa; si falla, se descarta esa parte y se documenta |
| Borrar el temporal de un proceso vivo (C-05) | Baja | Medio | Comprobar PID vivo + umbral de antigüedad; test con proceso vivo simulado |
| Memoria del equipo durante la ejecución | Media | Medio | Suites dirigidas por tarea; suite completa en Linux/CI antes del push |
| Envejecimiento del plan entre fases (F2/F3 diferidas) | Media | Medio | Tarea de revalidación contra `master` (+0,5 h) como primera tarea de cada fase |
| F3 no validable aquí de extremo a extremo | Alta | Medio | Validación estática + prueba manual del usuario en otro equipo; mínimos por tramo orientativos |

---

## Métricas de éxito

- PreToolUse (guard) sin rol protegido: publicar el cambio de mediana acreditado; control local del 2026-10-29 **36,71–38,21 %**, sin extrapolarlo a minutos por sesión. El objetivo del **80 %** pasa a investigación posterior: requiere spike de viabilidad y revalidación de alcance, coste y aceptación antes de comprometer su implementación; no se asigna a una tarea existente de F2.
- Tokens fijos por sesión (descriptions + índice): **−~2.000** frente a la línea base; 0 descriptions > 600.
- Statusline: de 3 a 1 llamadas Python por refresco, con 0 cuando la caché sirve.
- 0 parejas `*.tmp`/`*.tmp-journal` huérfanas tras reconstruir el índice (hoy 20 en `.claude/`).
- Coste real de F1 frente a 1.966 € / 38,4 h (retro y `CALIBRATION.md` al cerrar cada fase).

---

## Changelog del plan

| Fecha | Cambio | Autor |
|-------|--------|-------|
| 2026-10-27 | Creación del plan: F1 completa (T-01..T-07) y F2/F3 diferidas (T-08..T-26) según la decisión de la puerta | planner |
| 2026-10-29 | Usuario aprueba el ajuste de CA-01: cero Python y medición transparente sin mínimo porcentual en F1; 80 % reservado a investigación posterior sin presupuesto nuevo. T-01 estabilidad y T-07 revisión/entrega siguen abiertas. Evidencia: `testing/f1-performance-adjustment-proposal.md`. | usuario («adelante», «adelante con el plan») |
| 2026-10-29 | El usuario delega la decisión sobre T-01; se elige la opción 2: línea base caracterizada con dispersión y controles intercalados por mejora, sin afirmar estabilidad uniforme ni aceptar comparaciones inconcluyentes. Presupuesto y puertas T-07 intactos. | usuario («lo que consideres mejor»); elección motivada por el agente |

---

## Siguiente paso

Con el **OK del plan** del usuario (puerta de control), el agente **`implementer`** ejecuta **F1** sobre `feat/plugin-optimization`, marcando `tasks.md` como **ledger canónico**. Al cerrar F1: handoff a `qa` (puertas deterministas; `test-plan: n/a (sin UI)`), cierre con `documenter`, retro y release de la fase. F2 y F3 no arrancan sin revalidar el plan (T-08, T-20) y, en F3, sin el paso `architect` (T-21).
