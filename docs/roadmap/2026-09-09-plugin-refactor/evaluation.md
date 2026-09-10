---
generacion:            # ventana de evaluation.md (la spec tiene su propio bloque; no se solapan)
  inicio: 2026-09-09T22:43:15Z
  fin: 2026-09-09T22:49:20Z
  fuente: estimado     # `usage-meter.py close` degradó en esta máquina (Windows): «carpeta de transcripciones no disponible» — es exactamente E7/C-13 de esta spec (ratio_origen: CALIBRATION.md, mediana de 5). Tokens a juicio por lo leído (analysis, plantillas, CALIBRATION, README del roadmap, recon con grep sobre 6 scripts) y lo escrito (~330 líneas); el reloj de la ventana (6m) es solo la escritura del fichero, el recon se midió en la ventana de la spec
  tokens_reales: { entrada: 85000, salida: 24000, cache_creacion: 32000, cache_lectura: 480000 }
  eur: 1.29
  horas_ia: 0.29
  duracion: 6m
  ratio_usado: 479326
---

# 2026-09-09-plugin-refactor

> Presupuesto del **refactor medido del plugin** en dos bloques — (a) refactor de código con cero cambio de
> comportamiento y (b) revisión de encadenamiento E1–E10 — para la **puerta go/no-go** de `/pm-cycle`: cuánto cuesta
> cada bloque, qué conviene, en qué orden, y qué depende de la decisión del §5 del análisis que va a `architect`.

| | |
|---|---|
| **Fecha** | 2026-09-10 |
| **Estado** | completado |
| **Prioridad global** | Alta |
| **Solicitante** | usuario (petición del 2026-09-09 tras tres rondas de corrección sobre `task-brief.py`: «una revisión de código y refactorizar… de todo el plugin») |
| **Spec** | [`spec.md`](spec.md) — `aprobada`, derivada por el evaluator del análisis |
| **Diseño** | pendiente — paso de `architect` **recomendado** (Fase 2-bis) para O1 vs O2 del §5 |
| **Plan** | [`improvement-plan.md`](improvement-plan.md) + [`tasks.md`](tasks.md) — `borrador` (2026-09-10): 22 tareas en 5 fases y 4 tramos; hereda estas horas por característica (74,0 h base tras descontar P-1 y C-13 (i) ya hechas y sumar E11 como propuesta C-14) |
| **Características evaluadas** | 13 (5 del bloque (a) + 8 del bloque (b)) + 4 líneas de proceso presupuestadas aparte |

> **Análisis de origen:** [`analysis.md`](analysis.md) — única fuente del alcance (§1–§9 y §8-bis). Esta evaluación no lo
> amplía: lo que no está en él va aquí como riesgo o supuesto. Línea base: [`code-health-baseline.json`](code-health-baseline.json).

---

## Cuadro de mando

| Métrica | Total estimado | Confianza |
|--------|----------------|-----------|
| Esfuerzo humano | **90,0 h** (75,0 h base +20 %) | **Baja** (el histórico nunca ha validado horas humanas: CALIBRATION, aprendizaje 2) |
| Tiempo IA (ejecución) | **10,9 h** (+ 2,7 h supervisión) | **Media** (memory-retrieval: IA real +66 % sobre estimado; aquí la corrección post-revisión ya va como línea propia) |
| Coste | **~4.540 €** (3.785 € base; 4.500 € horas + ~40 € tokens con margen) | **Media** |
| Tokens IA | **5,23 M facturables** (in 3,82 M / out 0,58 M / caché creación 0,84 M) + ~9,9 M lectura de caché | **Baja** |
| Multiplicador productividad | **×6,6** | — |
| Características | **13** (+ 4 líneas de proceso) | — |

---

## Resumen ejecutivo

Ha llegado un análisis medido, no una petición: 104 funciones > 30 líneas, **32 de ellas (30 %) en los cinco hotspots** que cambian cada semana, un `main()` de 160 líneas en `task-brief.py` que acaba de absorber tres rondas de corrección, y un 7,6 % de duplicación del que **la mayor parte es diseño** (scripts que viajan sueltos) y no deuda. El análisis separa lo refactorizable de lo que exige una decisión de arquitectura previa (§5) y añade diez huecos de contrato entre piezas (§8-bis) verificados en un ciclo real.

Se presupuestan **13 características en dos bloques**: (a) refactor con cero cambio de comportamiento — C-01…C-05, **28,0 h base** — y (b) encadenamiento E1–E10 — C-06…C-13, **31,0 h base** —, más cuatro líneas de proceso que el histórico del repo obliga a separar (diseño de `architect`, revisión de dos lentes por tramo, corrección post-revisión igual a la revisión, cierre: **16,0 h base**). Total **75,0 h base → 90,0 h con margen, ~4.540 €, 5,2 M tokens facturables**.

La decisión que soporta: la puerta go/no-go y, dentro del go, **qué bloque entra primero** (el (a) desbloquea `brief-budget`, que ya tiene go ordenado detrás) y **si se hace el paso de `architect`** antes de tocar copias. **Veredicto: go condicionado** — a llevar el §5 a `architect` antes de abrir C-03, a no recortar las líneas de proceso, y a que `brief-budget` y F2 de `project-specialization` esperen a que los hotspots estén partidos.

---

## Requerimientos recibidos

| ID | Característica | Requisito origen (ref.) | ¿Claro? |
|----|---------------|-------------------------|---------|
| C-01 | `task-brief.py`: `main()` 160 → 7 secciones; 4 reglas de persona en una función | analysis §3 (caso concreto), §6.3, §8; spec «Alcance (a)» | ✅ |
| C-02 | Otros 4 hotspots: 28 funciones largas → ≤ 14, ninguna nueva > 60 | analysis §3, §8 (32 → ≤ 16, medido 2026-09-10) | ✅ |
| C-03 | Copias accidentales → declaradas o eliminadas (+ patrón E9) | analysis §2 clase 3, §5, §8-bis E9, §6.4 | ⚠️ ambiguo — bloqueado por la decisión del §5; y el bloque UTF-8 listado como accidental ya es deliberado y guardado (ver abajo) |
| C-04 | Falsos positivos de TODO: 8 → 1 | analysis §4, §8, §8-bis E10 | ✅ |
| C-05 | Excluir `interop/` en `code-health` | analysis §2 clase 1, §8-bis E10 | ⚠️ ambiguo — añade un flag; el §7 dice «ni un flag». Excepción declarada en la spec (CA-07) |
| C-06 | Matriz de contratos pieza → pieza (`docs/agents/`) | analysis §8-bis método 1 y 4 | ✅ (nombre del fichero lo fija `planner`) |
| C-07 | Linter: rutas citadas existen · `/comando` citado existe · regla «al tocar X regenera Y» con puerta | analysis §8-bis método 2 (a)(b)(c) | ⚠️ (c) ambiguo — «regla de `CLAUDE.md`» no es parseable sin la matriz de C-06 |
| C-08 | E1: `test-plan: n/a (sin UI)` en `planner` → `dev-cycle` → `qa` | analysis §8-bis E1, método 3 | ✅ |
| C-09 | E2 + E3: dependientes enumerados (`interop/**`, piezas que describen) en `Archivos`, `implementer`, Lente A | analysis §8-bis E2, E3, método 4 | ✅ |
| C-10 | E4: Lente C ve flujo de texto del consumidor hacia un prompt | analysis §8-bis E4 | ⚠️ ambiguo — el patrón a detectar no está definido; riesgo de sobredisparo |
| C-11 | E5: nombre real del comando (`/custom-agents:dev-cycle`) en `/doctor` y doc viva | analysis §8-bis E5 | ⚠️ alcance de la doc no fijado (104 ficheros lo citan; se asume solo doc viva, S-5) |
| C-12 | E6: exclusiones en `scope-check.py` (`CONTINUE-HERE*.md`, `.claude/**`) | analysis §8-bis E6 | ✅ |
| C-13 | E7: `usage-meter` en Windows (carpeta con espacios) + agregado de `fuente: estimado` visible | analysis §8-bis E7 | ✅ — causa raíz de (i) localizada en el recon (abajo) |
| — | E8: guardarraíl CA-08 con `design.md` | analysis §8-bis E8 | **no se presupuesta**: es C-05 de `brief-budget` (ya evaluada) |

**Ambigüedades / información que falta:**

- **§5 sin decidir (C-03, E9).** O1 (copias declaradas: registro + un test) vs O2 (módulo vendorizado por el empaquetador). Se presupuesta C-03 sobre **O1** (el mecanismo ya existe: `tests/test_knowledge_index.py`) y se da el **delta de O2** (+4,0 h humanas, +0,5 h IA: generador + `--check` + resolución con la regla `find` de seis raíces). No se decide aquí.
- **Premisa matizada del §2 (clase 3):** el bloque de reconfiguración UTF-8 (`doctor.py:56` ↔ `guardrail-check.py:49` ↔ `build_dashboard.py:14` ↔ `evals/run.py:55`) **no es accidental**: `windows-console` T-01 lo replicó LITERAL a propósito (GOT-005) y está guardado por `ast` — `grep -n "CONSOLE_MARK\|snippet_al_arrancar" tests/test_console_encoding.py scripts/lint_plugin.py` devuelve el criterio en ambos. Los pares accidentales de verdad son **cuatro** (54 líneas), no ocho: `evals/check.py:110` ↔ `lint_plugin.py:906` · `task-brief.py:581` ↔ `jira-flow.py:249` · `export-skills.py:36` ↔ `jira-flow.py:83` · `code-health.py:27` ↔ `deps-inventory.py:29`. C-03 baja de complejidad por ello.
- **Tensión interna del análisis en C-05:** el §2 pide excluir `interop/` («hoy no se puede: el script no tiene `--exclude` por ruta», verificado: `grep -n add_argument skills/code-health/scripts/code-health.py` → solo `--exclude-tests`) y el §7 dice «ni un flag». La spec lo resuelve como **excepción declarada** (flag aditivo, default sin cambio) y exige una **segunda línea base** tras C-05 (S-4) para no atribuir al refactor las 118 líneas del adaptador generado.
- **C-13 (i) tiene causa raíz concreta, no descubierta en el análisis:** `usage-meter.py:87` hace `re.sub(r"[/\\.:]", "-", cwd)` y **no sustituye espacios**; el `cwd` de este repo los tiene (`OneDrive - Imagina Media…`) y la carpeta real es `~/.claude/projects/C--Users-46066917X-OneDrive---Imagina-Media-Audiovisual-S-L-claude-cowork-custom-agents`. Demostrado: la función real `_project_transcript_dir()` → `None`; la misma expresión con el espacio en la clase → `is_dir: True`. Baja la complejidad de C-13 (i) a un cambio de una línea + test; (ii) sigue siendo la parte con criterio.
- **C-07 (c)** solo es lintable si las reglas «al tocar X regenera Y» viven en un sitio parseable (la matriz de C-06). Por eso C-06 precede a C-07 y C-09.
- **C-11**: no está fijado si el usuario quiere reescribir los ~104 ficheros que citan `/dev-cycle`. Se asume **solo doc viva** (S-5), como en `sin-motor-externo`; el barrido completo sería una característica aparte (~3 h humanas más).

---

## Datos necesarios para una evaluación completa

- [x] **Requerimientos** completos y sin ambigüedades — el análisis fija alcance, señales y método; las ambigüedades quedan como supuestos S-1…S-8 de la spec
- [x] **Alcance** de cada característica acotado — dos bloques; §7 y E8/O3 fuera con motivo
- [x] **Criterios de aceptación / éxito** por característica — CA-01…CA-20 con comando
- [x] **Restricciones** — cero cambio de comportamiento en (a), contratos congelados, misma suite, línea base con los mismos flags; Windows cp1252 (GOT-005); orden frente a `brief-budget` y F2 de `project-specialization`
- [ ] **Dependencias externas** — la decisión del §5 (`architect`) **no está tomada**; bloquea C-03 y E9
- [x] **Contexto técnico** — repo accesible; línea base y medición de hotspots verificadas por el orquestador; recon propio sobre 6 scripts
- [x] **Tarifa/hora y supuestos de coste** — `.claude/rates.json` (50 €/h · Opus 4.8 · precios verificados 2026-08-18 · FX 0,92 supuesto)

---

## Supuestos económicos (ajustables)

**Coste = (horas × tarifa) + coste de tokens de IA.** Importes en **EUR**.

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | 50 €/h | `.claude/rates.json` `tarifaHora` |
| Modelo IA asumido | claude-opus-4-8 | `rates.json` `modeloIA` |
| Precio input | 5 USD / 1M (4,60 €) | verificado 2026-08-18 con `rates-verify` (23 días; fiable hasta 90) |
| Precio output | 25 USD / 1M (23,00 €) | ídem |
| Caché creación / lectura | 6,25 / 0,50 USD por 1M | ídem; la lectura de caché no cuenta para horas pero sí para € (CALIBRATION, aprendizaje 4) |
| Tipo de cambio | 1 USD = 0,92 € | **supuesto** fijo de `rates.json`, no verificado — ⚠️ verificar antes de facturar |
| Margen de contingencia | 20 % | sobre horas base humanas e IA |
| Ratio de supervisión | 25 % de las horas IA | `rates.json` `ratioSupervision` |
| Ratio tokens → hora IA | **479.326 tok/h** | mediana de 5 muestras de `docs/roadmap/CALIBRATION.md` (precedencia sobre el default 300.000 no calibrado) |
| Reparto de tokens facturables | 73 % entrada · 11 % salida · 16 % creación de caché; lectura de caché ≈ 1,9× los facturables | proporciones de la evaluación medida más parecida (`brief-budget`, mismo repo) |
| Coste de tokens por hora IA | ≈ 3,68 €/h | 0,479 M × (0,73×5 + 0,11×25 + 0,16×6,25 + 1,9×0,5) USD/M × 0,92 |
| Calibración aplicada | **memory-retrieval** (2026-09-08): IA real +66 % sobre estimado por tres revisiones (38 gaps) que el plan no presupuestaba → aquí revisión **y** corrección post-revisión como líneas propias (16 % del base); **LES-004/007/008/009**: prosa en minutos, separar medido de vendido, coste de proceso aparte, la revisión es la partida grande; **LES-005**: tareas con tests ×2 frente a prosa | `CALIBRATION.md` filas sdd-hardening … memory-retrieval; doctrina del plugin (`knowledge-find.py --doctrina --area estimacion`) |
| Horas humanas | estimación clásica «si lo hiciera un desarrollador sin IA» | **nunca validadas** en este repo (0 h humanas reales en las 8 filas) → confianza Baja; se muestran porque la plantilla y `/roadmap-metrics` las comparan |

---

## Evaluación por característica

### Bloque (a) — refactor de código (cero cambio de comportamiento)

### C-01 — `task-brief.py`: partir `main()` y fundir las reglas de la persona

- **Requisito origen**: analysis §3 («cuatro reglas para una sola sección… su `main()` monta siete secciones en línea»), §6.3, §8; spec CA-01/02/03/08
- **Descripción**: `main()` de 160 líneas (creció con la última corrección) pasa a las siete secciones que ya monta, cada una en su función; `PERSONA_TOPE_CHARS`, `PERSONA_SUELO_CHARS`, `PERSONA_TOPE_MINIMO_UTIL` y el margen dinámico se funden en una función con nombre. 4 funciones largas → ≤ 2. Es el prerequisito de `brief-budget` (que ya tiene go, ordenado detrás).
- **Complejidad**: **Alta** — hotspot (7 cambios/90 d, 685 líneas) que acaba de sufrir tres rondas; la suite `test_task_brief.py` es grande (> 1.000 líneas) y fija el tope CA-08, las secciones y el `_REVISION_HDR_FALLBACK`; el `--json` de `knowledge-find.py` que consume no cambia
- **Esfuerzo**: 6,0 h · confianza **Media** (alcance nítido; el riesgo es romper el tope del brief sin que la suite lo vea — GOT-009)
- **Previsión IA**: 0,6 h · 210k in / 32k out tok (+46k caché) · 2,2 €
- **Coste**: (6,0 h × 50 €) + 2,2 € = **302 €**
- **Impacto / áreas afectadas**: `agent-kits/shared/task-brief.py`; solo lectura de `agent-kits/shared/test_task_brief.py`; consumidores del brief (`/dev-cycle` modo `subagentes`) sin cambio
- **Dependencias y prerequisitos**: ninguna para arrancar; **bloquea** a `brief-budget` (mismo `main()`); en `feature/plugin-refactor`, F1 de `project-specialization` ya en `master` (919cca4)
- **Riesgos**: el tope del brief (10.000) se rompe por construcción con `design.md` (GOT-009) y la suite recorre un solo ledger: una regresión ahí pasa en verde. Mitigación: captura previa de un brief real con `## Diseño` y comparación byte a byte (CA-08)
- **Incógnitas / preguntas abiertas**: si `brief-budget` C-05 (guardarraíl sobre todos los ledgers) debería adelantarse a este refactor como red de seguridad — decisión de orden para el usuario

### C-02 — Los otros cuatro hotspots: 28 funciones largas → ≤ 14

- **Requisito origen**: analysis §3 (tabla y hotspots), §6.3, §8 («32 → ≤ 16, sin ninguna nueva > 60»); spec CA-01/02/03/08
- **Descripción**: `knowledge-find.py` (3 largas, `main()` 87; el que más cambia: 9/90 d) · `doctor.py` (8, `bloque_plugin()` 87; 942 líneas) · `lint_plugin.py` (9, `lint()` 114; 969 líneas; **es la puerta de la CI**) · `build_dashboard.py` (8, `render_html()` 93 y `scan()` 85). Un hotspot por tarea. `celdas_md` y compañía (copia guardada) no se tocan.
- **Complejidad**: **Alta** — cuatro ficheros de 600-970 líneas; `lint_plugin.py` y `doctor.py` son puertas (CI, `/doctor` exit 1) cuyos avisos y veredictos deben quedar idénticos; `build_dashboard.py` produce HTML/MD/JSON que se compara byte a byte
- **Esfuerzo**: 14,0 h · confianza **Media** (≈ 3,5 h por hotspot; la suite de cada uno existe: `test_doctor` 24 tests, `test_build_dashboard`, `test_lint_plugin`, `test_knowledge_find`)
- **Previsión IA**: 1,6 h · 560k in / 84k out tok (+123k caché) · 5,9 €
- **Coste**: (14,0 h × 50 €) + 5,9 € = **706 €**
- **Impacto / áreas afectadas**: `agent-kits/shared/knowledge-find.py`, `agent-kits/shared/doctor.py`, `scripts/lint_plugin.py`, `skills/roadmap-dashboard/scripts/build_dashboard.py`; consumidores: `task-brief.py` y `session-context.sh` (JSON de knowledge-find), CI (`lint_plugin`), `/doctor`, `/roadmap-status`/`/pm-backlog`/`/roadmap-metrics` (dashboard)
- **Dependencias y prerequisitos**: ninguna; **debe ir antes de C-07** (que añade comprobaciones a `lint_plugin.py`) y antes de **F2 de `project-specialization`** (que añade una sección a `doctor.py` y `--root` al linter: mismos ficheros)
- **Riesgos**: conflicto de rama con F2 si se solapan en el tiempo; «idéntico» en Windows debe medirse contra los fallos preexistentes de la suite, no contra «todo verde» (ver riesgos transversales); `knowledge-find.py --json` es API interna del brief
- **Incógnitas / preguntas abiertas**: reparto exacto del ≤ 16 entre los cinco (lo fija `planner` por tarea); si `lint_plugin.py` merece ir el último para que C-07 no lo toque dos veces

### C-03 — Copias accidentales → declaradas o eliminadas (+ registro del patrón E9)

- **Requisito origen**: analysis §2 clase 3 y matiz del 2026-09-10, §5, §6.4, §8 («0 bloques sin declarar»), §8-bis E9; spec CA-05
- **Descripción**: los **cuatro** pares accidentales (54 líneas, tras reclasificar el bloque UTF-8 como deliberado y guardado) se registran y comparan con UN test (O1) o se eliminan si una pieza no los necesita; el patrón E9 (`REVISION_HDR_PATTERN` + dos `_REVISION_HDR_FALLBACK`) y `sin_vallas` (declarada, **sin guardarraíl**) entran en el mismo registro. Las copias guardadas (`celdas_md`) se registran sin cambiar de texto.
- **Complejidad**: **Media** con O1 (el mecanismo existe) · **Alta** con O2 (generador que vendoriza al empaquetar + `--check` + resolución en el árbol de trabajo con la regla `find` de seis raíces)
- **Esfuerzo**: 4,0 h (O1) · confianza **Baja** — depende de una decisión no tomada; **delta O2: +4,0 h humanas, +0,5 h IA (+202 €)**
- **Previsión IA**: 0,5 h · 175k in / 26k out tok (+38k caché) · 1,8 €
- **Coste**: (4,0 h × 50 €) + 1,8 € = **202 €** (O2: ~404 €)
- **Impacto / áreas afectadas**: `tests/` (test único de copias), `evals/check.py`, `scripts/lint_plugin.py`, `agent-kits/shared/task-brief.py`, `skills/jira-sync/scripts/jira-flow.py`, `scripts/export-skills.py`, `skills/code-health/scripts/code-health.py`, `skills/dependency-upgrade/scripts/deps-inventory.py`, `agent-kits/shared/ledger-lint.py`, `skills/changelog-sync/scripts/changelog-sync.py`; con O2 también `export-skills.py`/`export-interop.py`
- **Dependencias y prerequisitos**: **bloqueada por la decisión del §5** (`architect`, Fase 2-bis); tras C-01/C-02 (las copias cambian de línea al partir funciones)
- **Riesgos**: abrirla sin la decisión es trabajo perdido o regresión de portabilidad (conclusión del §2); con O1 el % de duplicado no baja y hay que explicarlo (no es el objetivo, §7)
- **Incógnitas / preguntas abiertas**: O1 vs O2; si `sin_vallas` debe unificarse en una sola copia canónica con fallback (patrón E9) en vez de dos copias registradas

### C-04 — Detector de TODO de `code-health.py`: 8 → 1

- **Requisito origen**: analysis §4, §8, §8-bis E10; spec CA-06
- **Descripción**: `TODO_RE` (`code-health.py:47-49`) acepta «palabra seguida de `(`» y con ello la prosa castellana «TODO (ADRs, …» de `confluence-scope.py:113`; además el detector se detecta a sí mismo (5 marcadores en su docstring y código) y a `journal.py:41`. Queda el real: `usage-meter.py:380` (29 días). Excluir comentarios que enumeran marcadores y el propio fichero del detector.
- **Complejidad**: **Baja** — regex y una exclusión; 14 tests existentes en la skill
- **Esfuerzo**: 2,0 h · confianza **Alta**
- **Previsión IA**: 0,25 h · 88k in / 13k out tok (+19k caché) · 0,9 €
- **Coste**: (2,0 h × 50 €) + 0,9 € = **101 €**
- **Impacto / áreas afectadas**: `skills/code-health/scripts/code-health.py`, `skills/code-health/scripts/test_code_health.py`
- **Dependencias y prerequisitos**: ninguna; conviene antes de C-01/C-02 para que la línea base compare TODO reales
- **Riesgos**: es la primera excepción declarada al «cero cambio de comportamiento» (el informe cuenta menos): debe quedar escrita en el ledger como tal; sobre-excluir esconde TODO reales en scripts que hablen de marcadores
- **Incógnitas / preguntas abiertas**: ninguna

### C-05 — `code-health.py` excluye `interop/` (rutas generadas)

- **Requisito origen**: analysis §2 clase 1 («lo que toca es excluir `interop/`… hoy no se puede»), §8-bis E10; spec CA-07 y S-4
- **Descripción**: flag aditivo de exclusión por ruta (nombre lo fija `planner`), default sin cambio; con él el par `hooks/opencode-plugin.js` ↔ `interop/opencode/plugins/custom-agents-hooks.js` (118 líneas, salida de `export-interop.py`) deja de contar. Tras cerrarla se toma una **segunda línea base**.
- **Complejidad**: **Baja** — `argparse` + filtro en el recorrido; tests
- **Esfuerzo**: 2,0 h · confianza **Alta**
- **Previsión IA**: 0,25 h · 88k in / 13k out tok (+19k caché) · 0,9 €
- **Coste**: (2,0 h × 50 €) + 0,9 € = **101 €**
- **Impacto / áreas afectadas**: `skills/code-health/scripts/code-health.py`, su test, `skills/code-health/SKILL.md` (una línea de uso: prosa de skill, permitida como excepción porque documenta el flag) y `docs/`
- **Dependencias y prerequisitos**: ninguna
- **Riesgos**: **contradice el §7** («ni un flag») — excepción declarada en la spec; comparar contra la línea base original con el flag activo daría «mejora» ficticia de 118 líneas (S-4)
- **Incógnitas / preguntas abiertas**: si el default debería excluir `interop/` (cambio de comportamiento del informe) o solo con flag (elegido: solo con flag)

### Bloque (b) — revisión de encadenamiento E1–E10 (cambia comportamiento)

### C-06 — Matriz de contratos pieza → pieza

- **Requisito origen**: analysis §8-bis método 1 («un fichero en `docs/agents/` junto a `ROLES.md`… `ROLES.md` dice quién decide y esto dice cómo se hablan») y 4; spec CA-10
- **Descripción**: una fila por arista invocador → invocado con flags, exit codes, ficheros y marcadores (`test-plan: n/a`, `interop/**`, `fuente: estimado`); cubre al menos E1–E10. Alimenta C-07 (c), C-09 y la Lente A.
- **Complejidad**: **Media** — es prosa, pero cada fila se verifica contra el código (9 agentes, 3 orquestadores, ~15 skills, ~20 scripts); el coste está en leer, no en escribir
- **Esfuerzo**: 6,0 h · confianza **Media**
- **Previsión IA**: 0,7 h · 245k in / 37k out tok (+54k caché) · 2,6 € (tokens altos por lectura)
- **Coste**: (6,0 h × 50 €) + 2,6 € = **303 €**
- **Impacto / áreas afectadas**: `docs/agents/<CONTRACTS>.md` (nuevo, solo ES como el resto de `docs/agents/`), fila en `docs/README.md` (+EN), `docs/FLOWS.md` si cambia un flujo
- **Dependencias y prerequisitos**: ninguna; **precede** a C-07 y C-09
- **Riesgos**: una matriz que nadie vigila envejece como los 6 ficheros de E3; por eso C-07 (c) la hace lintable. Formato: si se quiere parsear, hay que fijar columnas desde el principio
- **Incógnitas / preguntas abiertas**: nombre del fichero y si la tabla es la fuente parseable de C-07 (c) o hay un JSON al lado

### C-07 — Linter: rutas citadas · `/comandos` citados · reglas con puerta ejecutable

- **Requisito origen**: analysis §8-bis método 2 (a)(b)(c); spec CA-11/12/13
- **Descripción**: (a) 65 rutas de script citadas entre acentos graves en `agents/`, `commands/`, `skills/` existen (placeholders `<x>.py` tolerados); (b) 18 `/comandos` distintos citados existen como `commands/<x>.md` (tolerar `/algo`, `/nombre`, nativos `/clear`, `/agents`, `/reload-plugins`, y la forma con espacio de nombres de C-11); (c) cada regla «al tocar X regenera/actualiza Y» de `CLAUDE.md` tiene puerta ejecutable nombrada en la matriz.
- **Complejidad**: **Alta** — (a)(b) son Media; (c) es la parte con criterio y **corre en la CI**: un falso positivo bloquea releases (`release.py` corre el linter)
- **Esfuerzo**: 6,0 h · confianza **Media** ((a)(b) 3 h, (c) 3 h)
- **Previsión IA**: 0,7 h · 245k in / 37k out tok (+54k caché) · 2,6 €
- **Coste**: (6,0 h × 50 €) + 2,6 € = **303 €**
- **Impacto / áreas afectadas**: `scripts/lint_plugin.py`, `tests/test_lint_plugin.py`, `docs/CONVENTIONS.md` (+EN) si se añade regla
- **Dependencias y prerequisitos**: **después de C-02** (mismo fichero, ya partido) y **de C-06** ((c) necesita la matriz)
- **Riesgos**: avisos vs errores: como las comprobaciones de `hooks.json`, mejor nacer como aviso y subir a error tras una release limpia; (c) puede acabar siendo «cada fila de la matriz tiene una columna Puerta no vacía» — útil pero más débil de lo que suena
- **Incógnitas / preguntas abiertas**: aviso o error en la CI; cómo se enumeran las reglas de `CLAUDE.md` (S-6)

### C-08 — E1: caso sin UI resuelto en `planner`, `dev-cycle` y `qa` a la vez

- **Requisito origen**: analysis §8-bis E1 y método 3 («es la muestra de que el método funciona»); spec CA-14 y S-7
- **Descripción**: `planner` emite `test-plan: n/a (sin UI)`; `dev-cycle` Fase 3 lo lee; `qa` termina limpio y lo deja en el informe (hoy `agents/qa.md:94` pide regenerarlo con `planner` y `dev-cycle` invoca `qa` siempre: bucle que resuelve la prosa del orquestador). Esta iniciativa (sin UI) es la primera candidata a usarlo.
- **Complejidad**: **Media** — prosa en tres piezas (minutos por LES-004) + regeneración de `interop/` + casos en `evals/` + `docs/agents/*` y `FLOWS`; la dificultad es la coherencia entre las tres, exactamente lo que E3 dice que nadie comprueba
- **Esfuerzo**: 3,0 h · confianza **Media**
- **Previsión IA**: 0,35 h · 123k in / 18k out tok (+27k caché) · 1,3 €
- **Coste**: (3,0 h × 50 €) + 1,3 € = **151 €**
- **Impacto / áreas afectadas**: `agents/planner.md`, `commands/dev-cycle.md`, `agents/qa.md`, plantilla de plan del kit del planner, `docs/agents/{planner,qa}.md`, `docs/FLOWS.md` (+EN), `interop/` regenerado, `evals/cases/`
- **Dependencias y prerequisitos**: ninguna; mejor tras C-06 para que la arista quede en la matriz
- **Riesgos**: `qa-gate.py` no debe cambiar de contrato (S-7); `dev-cycle.md` está cerca de su tope de líneas (198 tras `sin-motor-externo`)
- **Incógnitas / preguntas abiertas**: dónde vive el marcador (frontmatter de `improvement-plan.md` o del ledger)

### C-09 — E2 + E3: piezas dependientes enumeradas y comprobadas

- **Requisito origen**: analysis §8-bis E2 («3 ficheros desincronizados… nadie ejecuta `--check`»), E3 (6 ficheros mintiendo), método 4; spec CA-15
- **Descripción**: `planner` mete `interop/**` (y las piezas que describen a la tocada, según la matriz) en `Archivos` de las tareas que tocan `commands/`, `agents/`, `hooks/`; `implementer` regenera con `export-interop.py`; la Lente A ejecuta `export-interop.py --check` y lo cita ✓/✗.
- **Complejidad**: **Media** — prosa en `planner.md`, plantilla de tareas, `implementer.md`, `lens-prompts.md`; `scope-check.py` debe aceptar los ficheros generados si están en `Archivos` (lo están)
- **Esfuerzo**: 3,0 h · confianza **Media**
- **Previsión IA**: 0,35 h · 123k in / 18k out tok (+27k caché) · 1,3 €
- **Coste**: (3,0 h × 50 €) + 1,3 € = **151 €**
- **Impacto / áreas afectadas**: `agents/planner.md`, `agent-kits/planner/templates/*`, `agents/implementer.md`, `skills/adversarial-review/references/lens-prompts.md`, `docs/agents/*`, `interop/` regenerado
- **Dependencias y prerequisitos**: **C-06** (la lista de dependientes sale de la matriz)
- **Riesgos**: `Archivos` crece (los ledgers ya tienen mediana 8 ficheros por tarea) y con él el brief del subagente (GOT-009); mitigación: `interop/**` como patrón, no fichero a fichero
- **Incógnitas / preguntas abiertas**: si la Lente A ejecuta el `--check` ella misma (Bash) o lo exige como evidencia del implementer

### C-10 — E4: la Lente C ve flujo de texto del consumidor hacia un prompt

- **Requisito origen**: analysis §8-bis E4 («dio `lente_c: false` tres veces… la Lente B encontró la suplantación las tres veces»); spec CA-16
- **Descripción**: `review-lens-select.py` añade una heurística: diff que introduce lectura de `.claude/**`, `dev.json`, `personas/*.md` u otro texto controlado por el consumidor en una función que compone un brief/prompt → `lente_c: true` con motivo. El caso real de F1 pasa a `true` en el test.
- **Complejidad**: **Alta** — es una heurística de flujo de datos sobre un diff, no un patrón léxico; alto riesgo de sobredisparo (cada Lente C extra cuesta una revisión) o de infradisparo (se queda en «ruta + palabra prompt»)
- **Esfuerzo**: 4,0 h · confianza **Baja** (el patrón no está definido en el análisis)
- **Previsión IA**: 0,5 h · 175k in / 26k out tok (+38k caché) · 1,8 €
- **Coste**: (4,0 h × 50 €) + 1,8 € = **202 €**
- **Impacto / áreas afectadas**: `skills/adversarial-review/scripts/review-lens-select.py` y su test, `skills/adversarial-review/SKILL.md` (una línea), `dev.json` `revision.excluir` como válvula
- **Dependencias y prerequisitos**: ninguna; conviene medir la tasa de disparo sobre los ledgers recientes antes/después
- **Riesgos**: falsos positivos que encarecen cada ciclo; una heurística que «acierta» solo el caso de F1 es un test de regresión disfrazado de detector
- **Incógnitas / preguntas abiertas**: definición operativa de «texto controlado por el consumidor» y de «acaba en un prompt» (funciones nombradas, secciones del brief, `subprocess` a `claude -p`)

### C-11 — E5: el nombre real del comando instalado como plugin

- **Requisito origen**: analysis §8-bis E5 («`/dev-cycle` da Unknown command; `/doctor` no lo comprueba»); spec CA-17 y S-5
- **Descripción**: `/doctor` informa del nombre con espacio de nombres (`/custom-agents:<cmd>`) y ⚠️ si la doc viva cita la forma corta; README ES/EN, INSTALL ES/EN, `docs/README.md` ES/EN y `CLAUDE.md` citan la forma que funciona. Los ≈ 104 ficheros con `/dev-cycle` que son registros fechados no se reescriben.
- **Complejidad**: **Media** — `doctor.py` ya lee el registro del plugin; la doc viva son ~7 ficheros con espejo EN
- **Esfuerzo**: 3,0 h · confianza **Media**
- **Previsión IA**: 0,35 h · 123k in / 18k out tok (+27k caché) · 1,3 €
- **Coste**: (3,0 h × 50 €) + 1,3 € = **151 €**
- **Impacto / áreas afectadas**: `agent-kits/shared/doctor.py` (+test), `README.md`, `README.es.md`, `docs/INSTALL.md`, `docs/en/INSTALL.md`, `docs/README.md`, `docs/en/README.md`, `CLAUDE.md`; `commands/*.md` si su prosa cita a otros comandos (C-07 (b) tolera ambas formas)
- **Dependencias y prerequisitos**: tras C-02 (mismo `doctor.py`); coordinar con C-07 (b)
- **Riesgos**: en desarrollo local (`.claude/` del repo) la forma corta sí funciona: el mensaje debe distinguir «instalado como plugin» de «bundle local» o generará ruido; alcance de la doc no fijado por el usuario (S-5)
- **Incógnitas / preguntas abiertas**: si el usuario quiere el barrido completo de los 104 ficheros (+3 h humanas, característica aparte)

### C-12 — E6: exclusiones en `scope-check.py`

- **Requisito origen**: analysis §8-bis E6 («5-6 ficheros fuera en las tres puertas del día»); spec CA-18
- **Descripción**: lista de exclusión por defecto (`CONTINUE-HERE*.md`, `.claude/**`) para lo que no es de ninguna tarea, con override en `dev.json` (`alcance.excluir`); test con mutante.
- **Complejidad**: **Baja** — `scope-check.py` ya usa `glob_to_regex`; es una lista y su lectura de `dev.json`
- **Esfuerzo**: 2,0 h · confianza **Alta**
- **Previsión IA**: 0,25 h · 88k in / 13k out tok (+19k caché) · 0,9 €
- **Coste**: (2,0 h × 50 €) + 0,9 € = **101 €**
- **Impacto / áreas afectadas**: `agent-kits/shared/scope-check.py` (+test), `docs/CONVENTIONS.md` regla 9 (+EN: nueva clave de `dev.json`), `/setup` si se ofrece la clave
- **Dependencias y prerequisitos**: ninguna
- **Riesgos**: excluir de más convierte la puerta en decorativa; la lista default debe ser mínima y la ampliación explícita
- **Incógnitas / preguntas abiertas**: si `docs/knowledge/journal/**` (lo escribe el hook, no la tarea) entra en el default

### C-13 — E7: `usage-meter` en Windows y visibilidad del agregado `fuente: estimado`

- **Requisito origen**: analysis §8-bis E7 («en Windows el meter degrada siempre… nadie lo ve agregado»); spec CA-19 y S-8
- **Descripción**: (i) `_project_transcript_dir()` (`usage-meter.py:84-94`) sustituye `/ \ . :` por `-` pero **no el espacio**; el `cwd` de este repo los tiene y por eso no encuentra `~/.claude/projects/C--Users-…-OneDrive---Imagina-Media-…`. **Demostrado en el recon**: la función real → `None`; con el espacio en la clase → `is_dir: True`. Una línea + test con `cwd` sintético. (ii) `/doctor` o `/roadmap-metrics` muestran «N de M bloques `generacion:` con `fuente: estimado`» para que la cadena de calibración vea de qué se alimenta.
- **Complejidad**: **Media** — (i) es Baja gracias a la causa raíz; (ii) recorre frontmatters de `docs/roadmap/**` (ya lo hace `build_dashboard.py`) y añade una línea con criterio
- **Esfuerzo**: 4,0 h · confianza **Media** ((i) 1 h, (ii) 3 h)
- **Previsión IA**: 0,5 h · 175k in / 26k out tok (+38k caché) · 1,8 €
- **Coste**: (4,0 h × 50 €) + 1,8 € = **202 €**
- **Impacto / áreas afectadas**: `agent-kits/shared/usage-meter.py` (+test), `agent-kits/shared/doctor.py` o `skills/roadmap-dashboard/scripts/build_dashboard.py` (+test), `docs/observability.md` (+EN)
- **Dependencias y prerequisitos**: (ii) tras C-02 si toca `doctor.py`/`build_dashboard.py`
- **Riesgos**: (i) puede haber otros caracteres que Claude Code normaliza distinto (acentos, `~`); el test debe fijar solo lo observado (espacio) y el resto degradar como hoy; **el arreglo de (i) cambia el ratio que `/retro` medirá a partir de ahora** — las 8 filas actuales de `CALIBRATION.md` son de sesiones Linux/macOS o estimadas, y la primera medida real en Windows será la de esta iniciativa
- **Incógnitas / preguntas abiertas**: dónde vive (ii): `/doctor` (salud) o `/roadmap-metrics` (métricas); ambas leen `generacion:`

### Líneas de proceso (presupuestadas aparte — LES-008/009, CALIBRATION memory-retrieval)

| ID | Línea | Horas humanas | Horas IA | Tokens (fact.) | € | Justificación |
|---|---|---|---|---|---|---|
| P-1 | Diseño §5 (`architect`, Fase 2-bis): `design.md` O1 vs O2 validado por trozos + ADR `propuesta` | 2,0 h | 0,4 h | 192k | 102 € | El análisis lo recomienda «no opcional»; sin él C-03 y E9 no se abren. `project-specialization` midió el paso en ~5 min de reloj de IA más la revisión del usuario |
| P-2 | Revisión de dos lentes **por tramo** (4 tramos: `task-brief`; otros hotspots; detector + copias; encadenamiento) | 6,0 h | 0,75 h | 360k | 303 € | CALIBRATION: «el coste está en la revisión, no en escribir»; en un refactor la Lente B es la que trabaja (§6.6) |
| P-3 | Corrección post-revisión (igual a la revisión) | 6,0 h | 0,75 h | 360k | 303 € | memory-retrieval: 38 gaps y tres tareas de cierre no presupuestadas → «línea propia igual a la de revisión» |
| P-4 | Cierre: segunda línea base, `export-interop.py --check`, `changelog-sync`, `release.py --dry-run`, `/retro` con fila en `CALIBRATION.md` | 2,0 h | 0,3 h | 144k | 101 € | Puerta de cierre de `/dev-cycle` (retro-gate); la retro de esta iniciativa será la **primera medida en Windows** si C-13 (i) entra pronto |
| | **Total proceso** | **16,0 h** | **2,2 h** | **1,06 M** | **809 €** | 21 % del base humano (`project-specialization` pasada 2: 21,3 %) |

---

## Comparativa

| # | Característica | Bloque | Complejidad | Horas | Coste € | Tokens | Prioridad | Confianza |
|---|---------------|--------|-------------|-------|---------|--------|-----------|-----------|
| C-01 | `task-brief.py`: `main()` en 7 secciones + reglas de persona | (a) | Alta | 6,0 h | 302 € | 288k | **Alta** (desbloquea `brief-budget`) | Media |
| C-02 | Otros 4 hotspots: 28 → ≤ 14 funciones largas | (a) | Alta | 14,0 h | 706 € | 767k | Alta | Media |
| C-03 | Copias accidentales → declaradas/eliminadas (+E9) | (a) | Media (O1) / Alta (O2) | 4,0 h (+4,0 O2) | 202 € (+202) | 240k | Media | **Baja** (bloqueada por §5) |
| C-04 | Detector de TODO 8 → 1 | (a) | Baja | 2,0 h | 101 € | 120k | Media | Alta |
| C-05 | Excluir `interop/` en `code-health` | (a) | Baja | 2,0 h | 101 € | 120k | Media | Alta |
| | **Subtotal (a)** | | | **28,0 h** | **1.412 €** | **1,53 M** | | |
| C-06 | Matriz de contratos pieza → pieza | (b) | Media | 6,0 h | 303 € | 336k | Alta (alimenta C-07/C-09) | Media |
| C-07 | Linter: rutas · `/comandos` · reglas con puerta | (b) | Alta | 6,0 h | 303 € | 336k | Media | Media |
| C-08 | E1 `test-plan: n/a (sin UI)` en 3 piezas | (b) | Media | 3,0 h | 151 € | 168k | Alta (bucle real) | Media |
| C-09 | E2+E3 dependientes en `Archivos` / Lente A | (b) | Media | 3,0 h | 151 € | 168k | Alta (3 desincronizados hoy) | Media |
| C-10 | E4 Lente C: flujo de texto → prompt | (b) | Alta | 4,0 h | 202 € | 240k | Media | Baja |
| C-11 | E5 nombre real del comando (`/doctor` + doc viva) | (b) | Media | 3,0 h | 151 € | 168k | Media | Media |
| C-12 | E6 exclusiones en `scope-check.py` | (b) | Baja | 2,0 h | 101 € | 120k | Media | Alta |
| C-13 | E7 `usage-meter` Windows + agregado estimado | (b) | Media | 4,0 h | 202 € | 240k | Alta (alimenta la calibración) | Media |
| | **Subtotal (b)** | | | **31,0 h** | **1.564 €** | **1,78 M** | | |
| P-1…P-4 | Líneas de proceso | — | — | 16,0 h | 809 € | 1,06 M | — | Media |
| | **Total base** | | | **75,0 h** | **3.785 €** | **4,36 M** | | |
| | **Total con margen (+20 %)** | | | **90,0 h** | **~4.540 €** | **5,23 M** | | |

---

## Presupuesto total

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 75,0 h × 50 €/h | 3.750,00 € |
| Margen de contingencia | +20 % sobre desarrollo base (15,0 h) | 750,00 € |
| Tokens IA (input) | 3,82 M tok × 5 USD/M × 0,92 | 17,57 € |
| Tokens IA (output) | 0,58 M tok × 25 USD/M × 0,92 | 13,34 € |
| Tokens IA (creación de caché) | 0,84 M tok × 6,25 USD/M × 0,92 | 4,83 € |
| Tokens IA (lectura de caché) | ~9,9 M tok × 0,50 USD/M × 0,92 | 4,55 € |
| **Total estimado (con margen)** | | **≈ 4.540 €** (4.540,29 €) |

> Tokens con margen: 10,92 h IA × 479.326 tok/h = 5,23 M facturables. Sin margen: 3.750 € + 33,6 € = **3.784 €** base.
> Delta si `architect` elige **O2** en el §5: +4,0 h humanas / +0,5 h IA → **+~245 € con margen**.

---

## Productividad IA (humano vs. IA)

| KPI | Valor |
|-----|-------|
| Horas humanas estimadas | 90,0 h (75,0 h base) |
| Horas IA (ejecución) | 10,9 h (9,1 h base) |
| Supervisión humana | 2,7 h (25 % de las horas IA) |
| **Horas totales (IA + supervisión)** | **13,6 h** |
| Horas ahorradas | 76,4 h |
| **Ahorro** | **85 %** |
| **Multiplicador de productividad** | **×6,6** |
| FTE equivalentes *(opcional)* | 0,48 |

> Horas mostradas **con el margen de contingencia (+20 %)** ya aplicado. Las horas IA son un supuesto derivado (tokens ÷ 479.326): el ratio es una cota inferior razonable (CALIBRATION) y la única muestra comparable (memory-retrieval, código + tests + hooks) salió **+66 %** sobre lo estimado; las líneas P-2/P-3 absorben esa desviación si la revisión encuentra lo que suele. Las horas humanas **no se han validado nunca** en este repo: sirven para comparar, no para prometer plazos.

---

## Recomendación

- **Veredicto**: **go condicionado** — a cuatro condiciones:
  1. **`architect` (Fase 2-bis) antes de abrir C-03** para decidir O1 vs O2 del §5; O3 descartada. Hasta entonces C-03 y el registro E9 quedan bloqueados; todo lo demás arranca.
  2. **Las líneas de proceso no se recortan** (P-2/P-3 son el 16 % del base): la única muestra comparable dice que ahí está la desviación.
  3. **Orden entre iniciativas**: C-01 antes de `brief-budget` (ya ordenado por el usuario) y C-02 antes de **F2 de `project-specialization`** (toca `doctor.py` y `lint_plugin.py`); si F2 arranca antes, C-02 se hace sobre código en movimiento y se paga dos veces.
  4. **Las dos excepciones al «cero cambio de comportamiento» del bloque (a) quedan declaradas en el ledger** (C-04 cuenta menos TODO; C-05 añade un flag aditivo) y **la comparación con la línea base usa los mismos flags** con que se tomó (segunda línea base tras C-05).
- **Quick wins** (bajo coste, alto valor): **C-04, C-05, C-12** (2 h cada una, confianza Alta) y **C-13 (i)** (una línea con causa raíz demostrada; hace medible la retro de esta misma iniciativa). **C-01** no es barata pero es la de mayor valor: desbloquea `brief-budget` y cierra la cicatriz que motivó todo.
- **Costosas / a valorar**: **C-02** (14 h, el 19 % del base: cuatro puertas del plugin refactorizadas con salida idéntica), **C-07** (6 h, (c) con criterio y corre en la CI), **C-10** (4 h, confianza Baja: heurística sin patrón definido — candidata a recortar a «detector del caso F1 + válvula `revision.excluir`» si hay que ahorrar), **C-03** si sale O2.
- **Orden sugerido**: P-1 (`architect`, en paralelo) → **C-04 → C-05** (segunda línea base) → **C-01** → C-13 (i) → **C-02** (knowledge-find → doctor → build_dashboard → lint_plugin) → C-03 (con la decisión) → **C-06** → C-08 → C-09 → C-07 → C-12 → C-11 → C-13 (ii) → C-10 → P-4. Motivo: el detector y la exclusión limpian la línea base antes de medir el refactor; `task-brief.py` desbloquea la iniciativa vecina; C-13 (i) hace que el resto de la iniciativa se mida de verdad; `lint_plugin.py` el último de los hotspots para que C-07 no lo toque dos veces; la matriz antes de todo lo que la consume.
- **Fuera de alcance recomendado**: E8 (es C-05 de `brief-budget`), el barrido de los ~104 ficheros que citan `/dev-cycle` (registros fechados), las funciones largas fuera de los cinco hotspots (`journal.py`, `jira-flow.py`, `deps-inventory.py`, `release.py`, `ledger-lint.py`…: deuda registrada para una segunda pasada con su propia línea base), y perseguir el 7,6 %.

---

## Riesgos transversales

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| **La decisión del §5 se retrasa o se salta** y C-03 se abre «para avanzar» | Media | Alto (regresión de portabilidad disfrazada de mejora; conclusión del §2) | Condición 1 del go; `planner` pone C-03 detrás de `design.md` `aprobado` como arista del grafo |
| **«Misma suite en verde» en Windows**: hay fallos preexistentes de la suite en esta máquina (memoria del proyecto), así que «todo verde» no es el criterio | Alta | Medio (una regresión se confunde con un fallo conocido) | CA-03 exige **identidad por test** (misma lista de pasan/fallan antes y después), no «verde»; captura previa de `pytest -q` como fixture del tramo; CI Linux como árbitro |
| **La revisión encuentra más de lo presupuestado** (memory-retrieval: +66 % IA, 38 gaps) | Alta | Medio (coste) | P-2 y P-3 como líneas propias; bucle acotado a 3; revisión por tramo, no por tarea |
| **Conflictos de rama con F2 de `project-specialization`** (mismo `doctor.py`, `lint_plugin.py --root`, `export-interop.py`) | Media | Alto (refactorizar dos veces; merges dolorosos) | Condición 3; `feature/plugin-refactor` corta de `master` con F1 integrada; F2 espera a C-02 |
| **`brief-budget` presiona el calendario** (go dado, ordenada detrás) | Media | Medio | C-01 primero en el orden; el resto de (a) no la bloquea |
| **Contrato roto sin que la suite lo vea** (`--json` de `knowledge-find`/`scope-check`, HTML del dashboard, brief con `## Diseño` — GOT-009) | Media | Alto | CA-08: capturas byte a byte antes del refactor sobre datos reales del repo; Lente B con esas capturas como evidencia |
| **Puertas de la CI refactorizadas** (`lint_plugin.py`) o con comprobaciones nuevas (C-07) **bloquean una release** por falso positivo | Media | Alto | C-07 nace como aviso y sube a error tras una release limpia; `release.py --dry-run` en cada tramo |
| **Línea base comparada con flags distintos** (tras C-05) → «mejora» ficticia de 118 líneas | Alta si no se controla | Medio (métrica mentirosa) | S-4: segunda línea base; el comando exacto en la `Verificación` de cada tarea |
| **Sobredisparo de la Lente C** tras C-10 encarece cada ciclo | Media | Medio | Medir la tasa sobre los últimos 5 ledgers antes/después; válvula `revision.excluir`; recortar C-10 si sube |
| **Prosa de (b) desincroniza a quien la describe** (el propio E3) | Alta | Medio | C-06 + C-09 son el remedio; hasta que existan, la Lente A revisa con esta spec y `ROLES.md` |
| **La primera medición real en Windows** (C-13 (i)) cambia el ratio de `CALIBRATION.md` | Alta | Bajo (es lo deseado, pero mueve cifras ya publicadas) | `/retro` documenta el salto; `ratio_usado` en cada `generacion:` hace el cálculo auditable |
| **Precio de tokens y FX** | Baja | Bajo (tokens son ~1 % del coste) | `rates-verify` si pasan 90 días (verificado 2026-08-18); `tipoCambioUsdEur` ⚠️ verificar antes de facturar |

---

## Siguiente paso

Para **ejecutar** lo aprobado, genera el plan detallado con el agente **`planner`** sobre esta misma carpeta (`docs/roadmap/2026-09-09-plugin-refactor/` → `improvement-plan.md` + `tasks.md`; sin `test-plan.md`: no hay UI — y es la primera candidata al marcador de C-08). El `planner` heredará las horas y costes de esta evaluación por característica — no re-estima desde cero — y actualizará la fila **Plan** de esta evaluación y el campo `plan:` de la spec al crear el plan.

**Qué se propone aprobar para planificar:**

- **Bloque (a) completo** (C-01, C-02, C-04, C-05 sin condición; **C-03 detrás de `design.md` `aprobado`** — arista del grafo, no tarea abierta).
- **Bloque (b) completo** con C-06 delante de C-07 y C-09; C-10 como la candidata a recortar si el usuario quiere ajustar coste.
- **Las cuatro líneas de proceso** (P-1…P-4) como tareas con horas propias; P-1 es el paso de `architect` (Fase 2-bis de `/pm-cycle`), que **se recomienda hacer antes de planificar** para que el plan de C-03 no sea condicional.
- **Secuencia obligatoria**: C-01 antes de `brief-budget`; C-02 antes de F2 de `project-specialization`; segunda línea base tras C-05; `lint_plugin.py` el último hotspot de C-02.
- **Transiciones**: con el go, spec → `aprobada` y esta evaluación → `completado`; con no-go, evaluación → `cancelado` (spec → `obsoleta` si se descarta).

---

## Changelog

| Fecha | Cambio |
|---|---|
| 2026-09-10 | Evaluación creada desde `analysis.md` (única fuente del alcance) tras crear `spec.md` (`borrador`): 13 características en dos bloques + 4 líneas de proceso; veredicto **go condicionado** (architect para el §5, líneas de proceso intactas, orden frente a `brief-budget` y F2, excepciones declaradas y segunda línea base). Dos hallazgos del recon incorporados: el bloque UTF-8 del §2 ya es deliberado y guardado (C-03 baja a 4 pares) y la causa raíz de E7 (i) es el espacio del `cwd` en `usage-meter.py:87`. Relanzamiento: el intento anterior murió por límite de sesión sin escribir nada. Medición degradada a `fuente: estimado` (el propio E7). |
