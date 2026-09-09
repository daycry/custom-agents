---
design: design.md        # `aprobado`, opción elegida O1 (usuario, 2026-09-09) — ADR-014
generacion:
  inicio: 2026-09-09T10:53:07Z
  fin: 2026-09-09T11:13:04Z
  fuente: estimado     # `usage-meter.py close` degrado: «carpeta de transcripciones no disponible» (Windows). Tokens estimados a juicio a partir de lo leido/escrito
  tokens_reales: { entrada: 78000, salida: 34000, cache_creacion: 34000, cache_lectura: 420000 }
  eur: 1.53
  horas_ia: 0.30
  duracion: 20m
  ratio_usado: 479326
---

# 2026-09-09-project-specialization

> Plan de ejecución del **tercer bucle** (especialización por proyecto): 22 tareas en 3 fases sobre el alcance F1+F2 de la spec aprobada, con el registro `.claude/pieces.json` en la forma O1 del diseño y las cuatro condiciones del go convertidas en aristas del grafo de dependencias.

| | |
|---|---|
| **Fecha** | 2026-09-09 |
| **Estado** | en-progreso |
| **Tipo** | Nueva Funcionalidad |
| **Prioridad** | Alta |
| **Solicitante** | usuario (petición del 2026-09-09; dos pasadas de descubrimiento) |
| **Responsable** | `implementer` (cadena nativa de `/dev-cycle`) |
| **Spec** | [`spec.md`](spec.md) — `aprobada`, 9 características · 35 criterios |
| **Evaluación** | [`evaluation.md`](evaluation.md) — `completado`, pasada 2, go por tramos |
| **Diseño** | [`design.md`](design.md) — `aprobado`, opción elegida **O1** ([`ADR-014`](../../knowledge/adr/ADR-014-registro-de-piezas-agregado-con-la-pieza-como-raiz.md)) |

> **Análisis de origen:** [`analysis.md`](analysis.md) — única fuente del alcance.
> **Ledger canónico de progreso:** [`tasks.md`](tasks.md).
> **Sin `test-plan.md`:** la iniciativa no toca UI. Todo lo verificable son scripts, suites `pytest`, evals de activación y prosa; no hay pantalla que recorrer con Playwright, así que un `test-plan.md` con bloques E2E-xx sería un fichero muerto. Si en la revisión apareciese superficie de UI, se añade entonces.

---

## Cuadro de mando

| Métrica | Estimado | Real | Confianza |
|--------|---------|------|-----------|
| Tiempo humano | **56,4 h** (47,0 h base +20 %) | 0 h | **Baja** |
| Tiempo IA (ejecución) | **4,75 h** (+ 1,19 h supervisión) | 0 h | Media |
| Coste total | **2.836,61 €** | 0 € | **Baja** |
| Tokens IA | **1.898.000** (in 1.470.000 / out 428.000) | 0 | Media |
| Multiplicador productividad | **×9,5** | — | — |
| Tareas | **22** | 0 hechas | — |

Las confianzas son **las de la evaluación, heredadas sin retocar**: el 99,3 % del coste base son horas humanas y `CALIBRATION.md` (aprendizaje 2) sigue diciendo que ninguna de sus 8 filas medidas tiene horas humanas reales. Las horas y tokens de IA sí se anclan en la mediana de 5 muestras medidas (479.326 tok/h), y ahí la confianza es Media con el aviso fresco de que la última muestra (`memory-retrieval`, 2026-09-08) se desvió **+66 %** en horas IA por la revisión.

---

## Estimación por fase

Presupuesto **heredado de `evaluation.md`** (subtotales de su §Comparativa: F1 = 6,0 h · 302 € · 220k · F2 = 31,0 h · 1.560 € · 1.153k · Proceso = 10,0 h · 504 € · 525k). No se re-estima nada: las horas por característica se reparten entre las tareas que la implementan y la suma por característica cuadra al céntimo.

| Fase | Estimado (h) | Tokens (in / out) | Coste € |
|------|-------------|-------------------|---------|
| Fase 1 — Sustrato (C-01, C-02) | 6,0 | 165k / 55k | 302,02 |
| Fase 2 — Nacimiento (C-10, C-03, C-04, C-05, C-07, C-06, C-11) | 31,0 | 885k / 268k | 1.560,24 |
| Fase 3 — Revisión, corrección y cierre (líneas de proceso) | 10,0 | 420k / 105k | 504,35 |
| **Total** | **47,0 h** | **1.470k / 428k** | **2.366,61 €** |

**Por característica (herencia declarada, base sin margen):**

| Fase | Característica | Tareas | Horas | Tokens | Coste € | Igual que la evaluación |
|---|---|---|---|---|---|---|
| F1 | C-01 — cascada de personas en el brief | T-01 | 2,5 | 90k | 125,78 | ✅ 2,5 h · 126 € · 90k |
| F1 | C-02 — doc del bucle (SPECIALIZATION +EN, FLOWS, ROLES) | T-02, T-03 | 3,5 | 130k | 176,24 | ✅ 3,5 h · 176 € · 130k |
| F2 | C-10 — `pieces-registry.py` | T-04, T-05, T-06 | 5,0 | 190k | 251,71 | ✅ 5,0 h · 252 € · 190k |
| F2 | C-03 — `project-scan.py` | T-07, T-08 | 6,0 | 213k | 301,86 | ✅ 6,0 h · 302 € · 213k |
| F2 | C-04 — `role-collision.py` | T-09, T-10 | 3,5 | 138k | 176,24 | ✅ 3,5 h · 176 € · 138k |
| F2 | C-05 — `/specialize <área>` | T-11, T-12, T-13 | 7,5 | 262k | 377,35 | ✅ 7,5 h · 377 € · 262k |
| F2 | C-07 — desambiguación con `plugin-dev` | T-14 | 1,5 | 52k | 75,46 | ✅ 1,5 h · 75 € · 52k |
| F2 | C-06 — sección de especialización en `/doctor` | T-15, T-16 | 3,0 | 128k | 151,10 | ✅ 3,0 h · 151 € · 128k |
| F2 | C-11 — piezas de proyecto multi-runtime | T-17, T-18, T-19 | 4,5 | 170k | 226,52 | ✅ 4,5 h · 227 € · 170k |
| F3 | Revisión de dos lentes (línea propia) | T-20 | 5,0 | 281k | 252,32 | ✅ 5,0 h · 252 € · 281k |
| F3 | Corrección post-revisión (línea propia) | T-21, T-22 | 5,0 | 244k | 252,03 | ✅ 5,0 h · 252 € · 244k |

**Única diferencia declarada respecto a la evaluación (no es un recorte).** La línea de **corrección post-revisión** conserva sus **5,0 h íntegras**, pero se reparte en dos tareas: **4,5 h** de corrección de gaps (T-21) y **0,5 h** de la puerta de cierre del repo (T-22: `lint_plugin.py`, suites, `export-interop.py --check`, `changelog-sync`, `retro.md` + fila en `CALIBRATION.md` — CA-31 a CA-33). El motivo es que ese trabajo existe y tiene que ser una tarea con `Verificación` propia, y la evaluación no le dio línea: inventarle horas nuevas habría inflado el total, y dejarlo sin tarea lo habría convertido en el adorno que la condición (c) del go prohíbe. Las 10,0 h de proceso siguen intactas dentro de la Fase 3 y **no financian ninguna característica**.

---

## Presupuesto económico

**Coste = (horas × tarifa) + coste de tokens de IA.** Todos los importes en **EUR**.

### Supuestos (ajustables)

Todos salen de `.claude/rates.json` y de `docs/roadmap/CALIBRATION.md`. Ninguno está inventado, y son **los mismos que usó la evaluación**, para que el plan no mueva el total por cambio de parámetros.

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | 50 €/h | `rates.json` `tarifaHora` |
| Modelo IA asumido | claude-opus-4-8 | `rates.json` `modeloIA` |
| Precio input | 4,60 € / 1M tokens | 5 USD/M × 0,92 · `verificadoEl: 2026-08-18` (< 90 días → fiable) |
| Precio output | 23,00 € / 1M tokens | 25 USD/M × 0,92 · verificado el 2026-08-18 |
| Precio creación de caché | 5,75 € / 1M tokens | 6,25 USD/M × 0,92 · **no presupuestado** (ver nota) |
| Precio lectura de caché | 0,46 € / 1M tokens | 0,50 USD/M × 0,92 · **no presupuestado** (ver nota) |
| Tipo de cambio | 1 USD = 0,92 € | `rates.json` `tipoCambioUsdEur` — **supuesto fijo, no verificado**; revisar antes de facturar |
| Ratio de supervisión | 25 % de las horas IA | `rates.json` `ratioSupervision` |
| Margen de contingencia | 20 % | `rates.json` `margenContingencia`; sobre horas base (humanas e IA) |
| Jornada / FTE | 8 h / 160 h-mes | `rates.json` `horasJornada` · `horasMesFTE` |
| Ratio tokens → hora IA | 479.326 tok/h | `CALIBRATION.md`, mediana de **5 muestras medidas** (precedencia sobre el default no calibrado de 300.000) |

**Lo que NO se presupuesta, y se dice:** la **lectura y la creación de caché**. Quedan fuera del cálculo de horas por definición (`CALIBRATION.md` mide longitud de sesión, no trabajo) y no se facturan aquí, pero en las 5 iniciativas medidas la lectura de caché fue la mayor parte del gasto real de API. Los **16,61 €** de tokens de este presupuesto son por tanto una **cota inferior**.

### Desglose

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 47,0 h × 50 €/h | 2.350,00 € |
| Margen de contingencia | +20 % sobre desarrollo base | 470,00 € |
| Tokens IA (input) | 1.470.000 tok × 4,60 €/1M | 6,76 € |
| Tokens IA (output) | 428.000 tok × 23,00 €/1M | 9,84 € |
| **Total estimado (con margen)** | | **2.836,61 €** |

El margen se aplica sobre las **horas** base (humanas e IA); los tokens van **sin** margen y se declara. Coincide al céntimo con el total de `evaluation.md` §Presupuesto total.

---

## Previsión de tokens (por fase)

Base: claude-opus-4-8 · precios de la tabla de supuestos.

| Fase | Input (tok) | Output (tok) | Total (tok) | Coste € |
|------|------------|-------------|-------------|---------|
| Fase 1 — Sustrato | 165.000 | 55.000 | 220.000 | 2,02 |
| Fase 2 — Nacimiento | 885.000 | 268.000 | 1.153.000 | 10,23 |
| Fase 3 — Revisión, corrección y cierre | 420.000 | 105.000 | 525.000 | 4,35 |
| **Total** | **1.470.000** | **428.000** | **1.898.000** | **16,61 €** |

**Método de estimación:** herencia directa de la previsión por característica de `evaluation.md`, repartida entre las tareas de cada característica en proporción a sus horas y a lo que cada una tiene que leer y escribir. La evaluación la construyó con las lecciones de calibración aplicadas: prosa en minutos (`LES-004`), una tarea con tests reales cuesta ~×2 respecto a una de prosa (`LES-005`), las seis características con suite nueva o ampliada (C-03, C-04, C-05, C-06, C-10, C-11) concentran **1.101k de los 1.898k tokens** (58,0 %), y las dos líneas de proceso van aparte (`LES-008`). Dentro de una característica el reparto lo fija el volumen de lectura: T-07 lee cuatro scripts existentes completos (`deps-inventory.py`, `code-health.py`, `coverage-gate.py`, `knowledge-find.py`) y por eso se lleva 100k de los 165k de entrada de C-03.

> **Las horas IA por tarea van redondeadas a dos decimales**; los totales de fase se calculan sobre los tokens de la fase, así que pueden diferir ±0,02 h de la suma visible de sus tareas.

---

## Productividad IA (humano vs. IA)

| KPI | Valor |
|-----|-------|
| Horas humanas estimadas | 56,4 h (47,0 h base +20 %) |
| Horas IA (ejecución) | 4,75 h (3,96 h base +20 %) |
| Supervisión humana | 1,19 h (0,99 h base +20 %) |
| **Horas totales (IA + supervisión)** | **5,94 h** |
| Horas ahorradas | 50,46 h |
| **Ahorro** | **89,5 %** |
| **Multiplicador de productividad** | **×9,5** |
| FTE equivalentes *(opcional)* | 0,32 |

> Horas mostradas **con el margen de contingencia (+20 %)** ya aplicado sobre las horas base (humanas e IA). La supervisión base es el 25 % de las horas IA (0,99 h de 3,96 h), según `rates.json`.

**Lo que este multiplicador NO dice** (`LES-007`, y `CALIBRATION.md` aprendizaje 2): las 56,4 h humanas **no las respalda ninguna muestra** — las 8 filas medidas tienen 0 h humanas reales, porque el trabajo lo hizo la IA con supervisión conversacional. El ×9,5 compara una **estimación** con otra **estimación anclada en medición**; no es un plazo que se pueda prometer. Las horas IA de este plan son un **supuesto**, igual que en la evaluación.

---

## Resumen ejecutivo

El plugin sabe **cómo** trabajar y no sabe **dónde** está trabajando: el brief del subagente ya tiene una casilla reservada para doctrina aplicable —la persona— y la rellena con uno de los 6 perfiles genéricos de 9 líneas del plugin. Este plan ejecuta el alcance F1+F2 de la spec aprobada para cerrar ese hueco con la gramática de los dos bucles que el repo ya tiene cerrados: un registro canónico (`.claude/pieces.json`, en la forma O1 del diseño), una puerta de entrada (`/specialize` con evidencia obligatoria, escalera de decisión y puerta de colisión) y una puerta de cierre (la sección de especialización de `/doctor`).

Son **22 tareas en 3 fases**. La Fase 1 entrega el sustrato y **rinde sola**: con la cascada de personas de tres escalones, una persona de proyecto escrita a mano ya funciona sin generador. La Fase 2 entrega el nacimiento de una pieza con su propia auditoría mecánica dentro de la misma fase. La Fase 3 es el coste de proceso —revisión de dos lentes, corrección y puerta de cierre—, que `CALIBRATION.md` obliga a presupuestar aparte y la condición (c) del go prohíbe recortar.

F3 de la spec (deriva semántica C-08 y campo «Cuándo aplica» C-09) **está diferida y no se abren tareas para ella**.

### Objetivos

- **Que la doctrina del proyecto llegue como instrucción y no como puntero**: `.claude/personas/<tipo>.md` entra entero en la casilla que hoy rellena un perfil genérico, sin sección nueva en el brief y sin presupuesto de tokens nuevo (CA-01 a CA-04).
- **Que una pieza de proyecto nazca solo con evidencia medida**: cada candidato cita `fichero:línea` del escaneo o el ID de una entrada de memoria, o no se propone (CA-08, CA-09).
- **Que no aparezca un segundo dueño de un rol que ya tiene dueño**: `role-collision.py` rechaza `test-writer`, `code-reviewer`, `security-auditor` y `doc-writer` nombrando la pieza que ya los cubre, con exit 0/1 y una línea por colisión (CA-11 a CA-13, `ADR-011`).
- **Que nada se escriba sin puerta humana ni fuera de lo que el registro reconoce como propio**: lote previsualizado con `--dry-run`, N confirmaciones para N candidatos, y propiedad por registro + hash con `dueno()` como única entrada (CA-14, CA-15, CA-17).
- **Que el bucle se pueda auditar el día siguiente**: biyección registro ↔ ficheros con mutante de hash y una línea por fila en `/doctor`, distinguiendo `gestionada` / `modificada` / `no gestionada` (CA-20, CA-21).
- **Que las piezas de proyecto no sean Claude-Code-only** sin que `/specialize` sepa de runtimes: la traducción la hace `export-interop.py` en modo proyecto (CA-28 a CA-30).

---

## Datos necesarios para un informe completo

- [x] **Requisitos funcionales** confirmados por el solicitante — `spec.md` `aprobada`, con dos pasadas de decisiones confirmadas (5 + 10 puntos) y 35 criterios de aceptación
- [x] **Alcance** cerrado — F1+F2 dentro; F3 (C-08, C-09) diferida; anti-alcance de `analysis.md` §6 cerrado con motivo
- [x] **Criterios de éxito / métricas** acordados — CA-34 con punto de control **nombrado** (las retros de las dos iniciativas siguientes) y criterio de retirada escrito
- [x] **Accesos y credenciales** — no hace falta ninguno: todo el trabajo es local sobre este repo, sin red y sin servicios de terceros
- [x] **Entornos** disponibles — Windows 11 con `.venv/Scripts` en el `PATH` (`export PATH="$PWD/.venv/Scripts:$PATH"`); consola cp1252 (`GOT-005`)
- [x] **Stakeholders** identificados — el usuario valida en la puerta del plan y en las de `/dev-cycle`
- [x] **Dependencias externas** mapeadas — **cero dependencias nuevas**: `project-scan.py` compone scripts que ya existen y `pieces-registry.py` solo usa la stdlib
- [x] **Restricciones** conocidas — `ADR-007` (deny solo con alcance de agente), `ADR-008` (skills y comandos cortos), `ADR-011` (un rol, un dueño), `GOT-003` (generador que escribe en el árbol que espeja), `GOT-005` (consola cp1252), `GOT-007` (la suite solo ve lo versionado); tope de 5 piezas por el presupuesto de `skill-index.py`
- [x] **Tarifa/hora y supuestos de coste** confirmados — `.claude/rates.json`, `precioTokens` verificado el 2026-08-18
- [ ] **Sin constitución del proyecto** — no existe `docs/CONSTITUTION.md`. No bloquea (el paso es opt-in); si se crea antes de implementar, la Lente A la incorpora a su recorrido
- [ ] **Sin `.claude/jira.json`** — Jira no está configurado en este proyecto, así que **no hay volcado de tareas a Jira** en este plan. No bloquea nada

---

## Análisis de impacto

Rutas reales del árbol, verificadas en `master` (`8e9dec7`). El impacto de C-10 nace de la tabla §5 del diseño; el resto, de las secciones «Impacto / áreas afectadas» de la evaluación.

- **`agent-kits/shared/task-brief.py`** — `--personas-dir` deja de ser **un solo directorio** con default al catálogo del plugin (~línea 526) y pasa a cascada de tres escalones. Es el único cambio de F1 en código, y el que hace que todo lo demás sirva de algo.
- **`agent-kits/shared/pieces-registry.py`** (nuevo, ~400 líneas) — el dueño del registro: subcomandos y exit codes de §2.0 del diseño, hash `sha256` con `\r\n`→`\n` normalizado, cerrojo, tres estados derivados, adopción y la regla de propiedad de `GOT-003`.
- **`scripts/project-scan.py`** (nuevo) — compositor de evidencia; invoca `deps-inventory.py`, `code-health.py`, `coverage-gate.py` y `knowledge-find.py --json`, y **no** implementa escáner propio (CA-10 es un `grep` de las cuatro invocaciones).
- **`scripts/role-collision.py`** (nuevo) — la puerta que salva `ADR-011`; generaliza la heurística de disparador literal duplicado que `lint_plugin.py` ya aplica al plugin, contra el inventario **descubierto** (9 agentes, 17 skills, 12 comandos) más las filas del registro.
- **`commands/specialize.md`** (nuevo) — secuencia los tres scripts y las dos puertas humanas; **no calcula**, para que ningún CA quede verde por afirmación (`ADR-008`: el comando no puede crecer hasta ser inmantenible).
- **`agent-kits/shared/doctor.py`** (1.084 líneas) + **`agent-kits/shared/test_doctor.py`** — sección nueva de especialización: una línea por fila, tres estados, «no gestionada» como estado **válido**, y «sin registro» distinto de «registro sano».
- **`scripts/export-interop.py`** (531 líneas) + **`tests/test_export_interop.py`** (245 líneas, 17 tests, **ni un `tmp_path`**) — modo proyecto y el primer fixture de árbol temporal de esa suite.
- **`skills/plugin-dev/SKILL.md`** + **`evals/cases/skill-plugin-dev.json`** + **`evals/cases/command-specialize.json`** (nuevo) — desambiguación con negativos cruzados; `evals/check.py` ata el literal a la `description` real (`LES-011`).
- **`docs/`** — `SPECIALIZATION.md` (+ espejo `docs/en/`), sección del tercer bucle en `FLOWS.md` (+EN), filas en `agents/ROLES.md`, reglas **3 y 9** de `CONVENTIONS.md` (+EN), fila de degradación en `INTEROP.md` §4 (+EN), y filas en los dos `README.md`.
- **`tests/`** — `test_project_scan.py` y `test_role_collision.py` (nuevos), `agent-kits/shared/test_pieces_registry.py` (nuevo), `test_task_brief.py`, `test_mermaid_blocks.py` y `test_console_encoding.py` (los tres `.py` nuevos entran en su tabla `MODOS`).
- **`.gitignore`** del repo y siembra de `.claude/.gitignore` en el consumidor — `pieces-state.json` y `pieces.json.lock` fuera del control de versiones (patrón `journal.py:209-219`).
- **`commands/setup.md`** — paso nuevo: ofrecer `/specialize` al terminar y preguntar el tope de piezas.
- **`interop/`, `.codex-plugin/`, `.agents/plugins/`** — **generados**, nunca editados a mano: tocar un comando, una skill o `export-interop.py` obliga a regenerar y a que `--check` siga verde (puerta de CI y de `release.py`).

**Lo que NO se toca:** el contenido de las 6 personas del plugin (siguen siendo el último escalón de la cascada), `MEMORIA_TOPE_CHARS` de `task-brief.py`, `LIMITE_LINEAS`/`LIMITE_CHARS` de `skill-index.py` (son los que fijan el tope de 5), y la plantilla de `agent-kits/shared/knowledge-write.md` (el campo «Cuándo aplica» es C-09, diferida).

---

## Cambios arquitectónicos

La arquitectura del registro **está decidida y este plan no la rediseña**: la fija [`design.md`](design.md) (`aprobado`, **opción O1**) y la cierra [`ADR-014`](../../knowledge/adr/ADR-014-registro-de-piezas-agregado-con-la-pieza-como-raiz.md). Lo que sigue es (a) lo que el plan **hereda** y hace cumplir, y (b) las **tres decisiones que el arquitecto le dejó explícitamente** más la que exige la condición (d) del go.

### Heredado del diseño (§2.0 y §4) — contrato de `pieces-registry.py`

- **Forma O1**: `piezas[]` con `destinos[{runtime, ruta, hash}]`. La pieza es la raíz; `runtime` es un **dato** y nunca una clave del esquema (un cuarto runtime no es una migración). El tope de CA-18 es `len(piezas)`.
- **Subcomandos**: `estado <ruta>…` · `dueno <ruta>` · `registrar` · `adopt` · `listar [--json]` · `auditar` · `tope`, con `--project-dir` y `--json`.
- **Exit codes**: **0** ok · **1** hallazgos de `auditar` · **2** registro ilegible o corrupto · **3** rehusado por propiedad (`GOT-003`) · **4** registro ocupado (lock) · **5** tope superado sin confirmación.
- **Hash**: `sha256` sobre los bytes del fichero completo con `\r\n`→`\n` normalizado, guardado como `"sha256:<hex>"`, con `hash_version` en la cabecera. Contra el falso `modificada` de `core.autocrlf` (`GOT-007` caso 2).
- **Dos promesas, dos mecanismos, dos tests separados**: `temp + os.replace` para que el JSON nunca quede a medias (precedente `usage-meter.py:_save_state`) y `.lock` para serializar el leer-modificar-escribir. Lock tomado → espera acotada (~3 s) y **exit 4**; nunca escribir sin cerrojo. La **lectura no toma cerrojo**.
- **Idempotencia por bytes**: serialización canónica (piezas ordenadas por nombre, claves en orden fijo, `indent=2`, `ensure_ascii=False`) y no se escribe si los bytes no cambian → «sin cambios», exit 0. Corolario: en `pieces.json` **no entra nada volátil**; eso vive en `pieces-state.json`, ignorado.
- **`dueno(<ruta>)` como única puerta de `GOT-003`**, con índice invertido ruta→destino construido al cargar, rechazo de la misma ruta en dos piezas, nombres reservados (`pieces.json`, `pieces-state.json`, `pieces.json.lock`) y confirmación extra **anotada en la fila** si la raíz del destino tiene marcadores `agent-kits/` o `.claude-plugin/`.
- **El campo `estado` no se persiste**: se deriva comparando el hash del disco con el anotado, en cada lectura.
- **Privacidad**: `redactar()` **importado** de `journal.py:200` (nunca reimplementado — `LES-013`); una ruta bajo `docs/security-scan/` no se cita (rechazo, no redacción).
- **Determinismo fuera del prompt**: todo lo verificable baja al script; `/specialize` y `/doctor` solo secuencian. Es la mitigación que la evaluación pide en su riesgo transversal «un CA verde por afirmación».

### Decisión 1 (el arquitecto la deja al plan) — la clave del tope en `.claude/dev.json`

**Clave: `especializacion.topePiezas`, entera, default `5`.** Cierra la pregunta abierta 2 del diseño y el supuesto «Dónde vive el tope de 5» de la spec.

- **Por qué el nombre**: `dev.json` ya agrupa por espacio de nombres con `camelCase` dentro (`revision.lenteSeguridad`, `tests.coberturaMinima`, `sesion.indice`, `sesion.resumen`). Un `topePiezas` a pelo en la raíz rompería ese patrón y dejaría sin sitio a las claves de especialización que vengan con F3; `especializacion.*` reserva el espacio sin adelantar nada.
- **Ausente = default 5**, como `revision.lenteSeguridad` (`auto`) y a diferencia de `tests.coberturaMinima` (ausente = sin gate). Aquí no hay «sin tope»: el tope existe porque lo fija la aritmética de `skill-index.py` (`LIMITE_LINEAS = 45` / `LIMITE_CHARS = 3500`), no una preferencia.
- **Quién la lee**: solo `pieces-registry.py tope` (T-04). El comando no la lee por su cuenta: pregunta al script, que es quien tiene el recuento y el test.
- **Quién la escribe**: `/setup` la pregunta en el paso nuevo (T-13) y el usuario a mano. Superar el tope no es un fallo silencioso: aviso con el motivo escrito + confirmación extra anotada en la fila (exit 5 sin confirmación).
- **Dónde se documenta**: fila de `dev.json` en la regla 9 de `CONVENTIONS.md` y su espejo EN (T-06).

### Decisión 2 (el arquitecto la deja al plan) — quién invoca `--reconstruir`

**`/doctor` lo NOMBRA; `/specialize` lo EJECUTA tras confirmación explícita.** Cierra la pregunta abierta 3 del diseño.

- **`/doctor` no ejecuta nada**: es solo lectura por contrato y ya emite «✅/⚠️/❌ + el comando que lo arregla» por línea. Ante un registro corrupto (exit 2) imprime el arreglo —`pieces-registry.py --reconstruir`— y **para ahí** (T-15). Que el diagnóstico escriba sería un rol nuevo para una pieza que existe precisamente por no escribir.
- **`/specialize` sí escribe**, así que es quien puede ofrecer la reconstrucción: al recibir exit 2 lo dice, muestra que `--reconstruir` aparta el fichero a `pieces.json.corrupto-<ts>` antes de rehacerlo desde el disco, y **exige una confirmación humana explícita** (T-11). Nunca automático: `pieces.json` es un fichero **comiteado y compartido por el equipo**, y reconstruirlo en silencio pisa el acuerdo de otra persona.
- **La implementación de `--reconstruir` vive en el script** (T-05), con su test. Las dos puertas solo lo invocan.

### Decisión 3 (el arquitecto la deja al plan) — las dos filas de la regla 9 de `CONVENTIONS.md` + espejo EN

Van en **T-06**, dentro del presupuesto de C-10, y son dos filas en la tabla «Ficheros de config/estado en `.claude/` del proyecto consumidor» (líneas ~169-188) **más las mismas dos en `docs/en/CONVENTIONS.md`** (regla bilingüe: al cambiar uno se cambia su espejo en el mismo cambio). Contenido exacto que tienen que llevar, siguiendo el patrón `jira.json`/`jira-state.json` de la misma tabla:

| Fichero | Qué es | Lo escribe | Si se corrompe/pierde |
|---|---|---|---|
| `pieces.json` | **Config** del bucle de especialización: registro canónico de piezas generadas o adoptadas, **comiteado y compartido por el equipo**, entradas ordenadas por nombre de pieza y sin nada volátil dentro (para que un conflicto de merge quede local al bloque de una pieza) | `pieces-registry.py` (vía `/specialize`) | Corrupto → se lee como vacío **con aviso** y la escritura se rehúsa (exit 2); `--reconstruir` lo aparta a `pieces.json.corrupto-<ts>` y lo rehace desde el disco, tras confirmación |
| `pieces-state.json` | **Estado** (memoria de máquina, **ignorado** en git): solo la huella del último escaneo, para que `/specialize` pueda decir «sin cambios». **No se crea vacío** | `pieces-registry.py` | Borrarlo es inocuo: el siguiente escaneo lo recrea (se pierde solo el «sin cambios» de esa corrida) |

Además, la nota de la **regla 3** («compartido vs privado») distingue **pieza de plugin** (viaja con el plugin, agnóstica de dominio) de **pieza de proyecto** (vive en el `.claude/` del consumidor, sabe de SU dominio, solo existe ahí). Los tokens que parsea la máquina —`pieces.json`, `pieces-state.json`, los nombres de estado `gestionada`/`modificada`/`no gestionada`— **quedan en español también en la doc EN**, como manda la regla bilingüe.

### Decisión 4 (condición (d) del go) — cómo aprende `export-interop.py` el modo proyecto

**Flag explícito `--project`**, no inferencia por ausencia de `.claude-plugin/`. Cierra la incógnita de C-11 y la condición (d) del go, **antes** de abrir la primera tarea de C-11, no durante.

El hecho verificado que obliga a decidir: `--root` significa hoy «la raíz del **PLUGIN**», no «cualquier árbol». Contra un `.claude/` de consumidor sale con **exit 1** pidiendo `.claude-plugin/plugin.json`, y su plan de salida escribe en `interop/` y `.codex-plugin/`, no en `.codex/`/`.opencode/`. La premisa «`--root` ya lo hace» de la spec era falsa y ya está corregida en la evaluación (§Ambigüedad 2). Tres razones para el flag:

1. **La inferencia convierte un error en un cambio de modo silencioso.** Con «si no hay `.claude-plugin/`, es un proyecto», una ruta mal escrita o un plugin a medio instalar dejarían de fallar y empezarían a **escribir en otro sitio**. Eso es exactamente la clase de fallo de `GOT-003`, y aquí sin la red del registro, porque el que escribe las variantes es `export-interop.py`, que no consulta `dueno()`.
2. **`--check` necesita saber contra qué plan comparar.** Es puerta de CI y de `release.py`: leer el modo de un flag hace que `--check` y `--check --project` sean dos veredictos distintos y explícitos, en vez de uno que depende de lo que haya en el disco.
3. **Se testea con una aserción, no con un árbol.** `--project` sobre un árbol sin `.claude-plugin/` es un caso; `--root` sin `--project` sobre ese mismo árbol **debe seguir saliendo con exit 1**, y ese es el test que impide la regresión de la inferencia. Con inferencia, el segundo caso desaparece y con él la garantía.

Lo que `--project` cambia: plan de salida `.codex/…` + `.opencode/…` en lugar de `interop/` + `.codex-plugin/`, y **tolerancia a manifiestos y hooks ausentes** (un `.claude/` de consumidor no tiene `.claude-plugin/plugin.json` ni `marketplace.json`). Lo que **no** cambia: `/specialize` sigue sin saber de runtimes, y añadir un runtime futuro sigue siendo una fila en la tabla `PROVIDERS` de `install/providers.mjs` (con `IDS` ya exportado) más su traductor. Queda registrado en **`ADR-015`** (`propuesta`).

### Restricciones de plataforma que condicionan cada tarea con código

- **Consola cp1252** (`GOT-005`): los tres `.py` nuevos (`pieces-registry.py`, `project-scan.py`, `role-collision.py`) llevan el snippet de 4 líneas que reconfigura `sys.stdin`/`sys.stdout`/`sys.stderr` a UTF-8 con `errors="replace"`, **replicado literal** (contrato standalone: el paquete portable los copia sueltos), entran en la tabla `MODOS` de `tests/test_console_encoding.py`, y **no emiten emoji ni flechas Unicode**. El `·` del contrato de salida de `role-collision.py` que exige CA-12 es representable en cp1252 y además queda cubierto por el snippet. Todo `subprocess` en modo texto fija `encoding="utf-8", errors="replace"`.
- **Puertas en Windows**: se corren con `export PATH="$PWD/.venv/Scripts:$PATH"`. Sin `flock` en Windows, el camino del cerrojo es `msvcrt` en bucle acotado y, si no se consigue, **exit 4** — nunca escribir sin cerrojo. Esa degradación se escribe, no se esconde.
- **`GOT-007`**: `tests/test_console_encoding.py` solo ve lo versionado, así que se corre **después** de `git add -N` para que los scripts nuevos entren en su descubrimiento.
- **El hook de guardia no cubre `Bash`**: `guardrail-check.py:334` aplica el chequeo de alcance solo a las herramientas de escritura; para `Bash` (línea 355) solo mira git. Está **fuera de alcance** y no se arregla aquí, pero tiene una consecuencia práctica: el alcance real del diff lo comprueba `scope-check.py` en el DoD, así que el campo **`Archivos`** de cada tarea del ledger tiene que estar completo o la puerta previa a la revisión salta con un falso positivo.

---

## Archivos a crear/modificar

| Archivo | Acción | Propósito |
|---------|--------|-----------|
| `agent-kits/shared/task-brief.py` | Modificar | Cascada de tres escalones en la resolución de personas (T-01) |
| `agent-kits/shared/test_task_brief.py` | Modificar | Casos de cascada, tipo arbitrario y degradación con exit 0 (T-01) |
| `docs/SPECIALIZATION.md` | Crear | Única puerta de entrada del tercer bucle (T-02) |
| `docs/en/SPECIALIZATION.md` | Crear | Espejo EN (T-02) |
| `docs/README.md` · `docs/en/README.md` | Modificar | Indexan el documento nuevo (T-02) |
| `docs/FLOWS.md` · `docs/en/FLOWS.md` | Modificar | Sección del tercer bucle con el diagrama de `analysis.md` §2 (T-03) |
| `docs/agents/ROLES.md` | Modificar | Fila de `/specialize` con DECIDE/ESCRIBE/LEE/no hace y el invariante de dirección (T-03) |
| `agent-kits/shared/pieces-registry.py` | Crear | El dueño del registro: contrato de §2.0 del diseño (T-04, T-05) |
| `agent-kits/shared/test_pieces_registry.py` | Crear | ~25-30 tests: hash CRLF/LF, cerrojo real, tres estados, idempotencia, adopción, `GOT-003`, tope (T-04, T-05) |
| `docs/CONVENTIONS.md` · `docs/en/CONVENTIONS.md` | Modificar | Reglas 3 y 9: dos filas del registro + nota pieza-de-plugin vs pieza-de-proyecto (T-06) |
| `.gitignore` | Modificar | `pieces-state.json` y `pieces.json.lock` fuera de git (T-06) |
| `scripts/project-scan.py` | Crear | Compositor de evidencia (T-07, T-08) |
| `tests/test_project_scan.py` | Crear | Composición, regla de evidencia en dos formas, cuatro degradaciones, privacidad (T-07, T-08) |
| `scripts/role-collision.py` | Crear | Puerta de colisión con contrato de salida (T-09, T-10) |
| `tests/test_role_collision.py` | Crear | Los cuatro nombres canónicos, inventario descubierto, contrato de exit code y formato (T-09, T-10) |
| `commands/specialize.md` | Crear | El comando: escalera, secuencia y las dos puertas humanas (T-11, T-12, T-13) |
| `evals/cases/command-specialize.json` | Crear | ≥ 2 positivos + 1 negativo, con el cruzado de `plugin-dev` (T-13, T-14) |
| `commands/setup.md` | Modificar | Paso nuevo: ofrecer `/specialize` y preguntar `especializacion.topePiezas` (T-13) |
| `skills/plugin-dev/SKILL.md` | Modificar | `description` «de ESTE plugin» + fila «qué NO hace» (T-14) |
| `evals/cases/skill-plugin-dev.json` | Modificar | Negativo cruzado recíproco (T-14) |
| `agent-kits/shared/doctor.py` | Modificar | Sección de especialización: una línea por fila, tres estados (T-15, T-16) |
| `agent-kits/shared/test_doctor.py` | Modificar | Sección nueva, «no gestionada» como no-error, biyección con mutante de hash (T-15, T-16) |
| `commands/doctor.md` · `docs/agents/` | Modificar | Documentar la sección nueva (T-15) |
| `scripts/export-interop.py` | Modificar | Modo proyecto `--project` y registro de los destinos escritos (T-17, T-19) |
| `tests/test_export_interop.py` | Modificar | Primer fixture de árbol temporal de esa suite + `--check` desincronizado (T-18) |
| `docs/INTEROP.md` · `docs/en/INTEROP.md` | Modificar | Fila de degradación §4 con el límite honesto escrito (T-19) |
| `tests/test_console_encoding.py` | Modificar | Los tres `.py` nuevos en la tabla `MODOS` (T-04, T-07, T-09) |
| `interop/` · `.codex-plugin/` · `.agents/plugins/` | Modificar (generado) | Regeneración obligatoria tras tocar comandos, skills o el traductor (T-13, T-14, T-17, T-22) |
| `CHANGELOG.md` · `CHANGELOG.es.md` | Modificar | Entradas `[Unreleased]`/`[Sin publicar]` vía `changelog-sync` (T-22) |
| `docs/knowledge/adr/ADR-015-modo-proyecto-explicito-en-export-interop.md` | Crear | Decisión 4 de este plan, `propuesta` (creado con el plan) |
| `docs/knowledge/README.md` | Modificar | Fila de `ADR-015` (creado con el plan) |

---

## Dependencias y prerequisitos

El grafo hace cumplir por **orden de tareas** las cuatro condiciones del go de F2; no quedan como deberes de proceso que alguien tenga que recordar.

| Condición del go (`evaluation.md` §Recomendación) | Cómo la impone el plan |
|---|---|
| **(a) C-10 entra antes que C-05 y C-06** | `T-11` (primera de C-05) depende de `T-05`; `T-15` (primera de C-06) depende de `T-05`. El esquema no se inventa en prosa: se fija dentro de C-10, donde hay test que lo sostiene |
| **(b) C-04 y C-07 entran en el mismo tramo que C-05** | `T-11` depende de `T-10` (contrato de la puerta de colisión ya cerrado) y `T-14` (C-07) depende de `T-13`: las tres están en la Fase 2 y ninguna puede quedarse fuera sin dejar la fase incompleta |
| **(c) Las dos líneas de proceso no se recortan** | Fase 3 propia con 10,0 h intactas y tres tareas con `Verificación` propia. La única redistribución (4,5 h + 0,5 h dentro de la línea de corrección) está declarada arriba y **no** financia ninguna característica |
| **(d) C-11 no se abre sin decidir el modo proyecto** | Decidido en este plan (§Cambios arquitectónicos, decisión 4: flag `--project`) y registrado en `ADR-015` **antes** de que `T-17` exista |

**Prerequisitos de entorno:** `.venv/Scripts` en el `PATH` para correr las puertas; `git` disponible (`code-health.py` omite hotspots con aviso si no lo hay, y la suite de codificación necesita `git ls-files`); `python3` para todo. **Nada más**: cero dependencias nuevas.

**Ruta crítica (cadena de dependencias duras más larga, 25,0 h base de las 47,0):**

`T-07 → T-08 → T-11 → T-12 → T-13 → T-14 → T-20 → T-21 → T-22`

Es decir: el compositor de evidencia y su privacidad, luego el comando con sus dos puertas y su validación, luego la desambiguación, y al final el bloque de revisión-corrección-cierre. `T-04 → T-05` (la raíz del subgrafo de F2) y `T-09 → T-10` son **paralelizables** con `T-07 → T-08`, y `T-15 → T-16` y `T-17 → T-18 → T-19` cuelgan de ramas cortas. Toda la Fase 1 (`T-01 → T-02 → T-03`, 6,0 h) es independiente de la Fase 2 y **rinde sola**: si la Fase 2 se parase, una persona de proyecto escrita a mano ya funcionaría.

---

## Criterios de aceptación (global)

Los 35 criterios de la spec están repartidos entre las tareas, cada uno en la que lo entrega. Estos son los del **plan**, que son los que se comprueban al cerrarlo:

- [ ] Los **33 criterios de F1, F2 y cierre** (CA-01 a CA-33) están cubiertos por al menos una tarea, y ninguna tarea existe sin un CA o una condición del go detrás. **CA-34 queda explícitamente abierto** (ni aprobado ni fallado): su punto de control son las retros de las dos iniciativas siguientes.
- [ ] **Ninguna tarea abierta para F3**: ni deriva semántica (C-08) ni campo «Cuándo aplica» (C-09). Verificación: `grep -n "Cuándo aplica\|deriva semántica" tasks.md` no devuelve tareas, solo la nota de alcance.
- [ ] `python3 agent-kits/shared/ledger-lint.py docs/roadmap/2026-09-09-project-specialization/tasks.md` → **exit 0**: las 22 tareas con su `Verificación`, con `verificacion: obligatoria` en el frontmatter.
- [ ] `python3 scripts/lint_plugin.py` con **0 errores** y `python3 -m pytest -q` en verde sobre la línea base de la suite (CA-31).
- [ ] `python3 scripts/export-interop.py --check` en verde tras cada tarea que toque un comando, una skill o el traductor (CA-31).
- [ ] `python3 evals/check.py` en verde, con los **negativos cruzados** `/specialize` ↔ `plugin-dev` en ambos sentidos (CA-22).
- [ ] Los tres `.py` nuevos con el snippet de consola y en la tabla `MODOS` de `tests/test_console_encoding.py` (`GOT-005`).
- [ ] Cadena de artefactos enlazada en los dos sentidos: `plan:` en `spec.md` y `design.md`, fila **Plan** en `evaluation.md`, y fila de la iniciativa **dentro de la tabla** de `docs/roadmap/README.md` (lo vigila `tests/test_roadmap_index.py`).
- [ ] `retro.md` en esta carpeta + fila en `docs/roadmap/CALIBRATION.md`: `python3 agent-kits/shared/retro-gate.py` en verde (CA-33). **Es puerta de cierre**, no un extra.
- [ ] Totales del cuadro de mando = suma de las fases = totales de `evaluation.md` (47,0 h base · 2.366,61 € base · 1.898k tokens), con la única diferencia declarada de la redistribución interna de la línea de corrección.

---

## Riesgos y mitigaciones

Los transversales los hereda `evaluation.md` §Riesgos transversales sin cambios. Aquí van **los que la planificación añade o concreta**, con la mitigación traducida a tarea.

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| **Un CA verde por afirmación** porque la mecánica del lote vive en la prosa del comando (CA-14, CA-15) | **Alta si no se respeta el contrato** | Medio | Todo lo verificable baja al script: `T-12` implementa las dos puertas contra `pieces-registry.py`, con test de árbol idéntico tras `--dry-run` y test de lote 3 (2 sí, 1 no). El comando solo secuencia |
| **El cerrojo, verde en el test y roto en la práctica** (precedente propio: el debounce de la línea de progreso se rehízo con `flock` + rename atómico en `debt-cleanup`) | Media | **Alto** | `T-05` con **dos tests separados**: corrupción (proceso muerto a mitad de escritura → JSON válido) y pérdida de fila (**dos procesos reales** con `subprocess`, no dos hilos). Prohibido un `assert True` |
| **Falso `modificada` por finales de línea** en `core.autocrlf=true` (`GOT-007` caso 2, ya costó una CI roja) | **Alta si se hashean bytes crudos** | Medio | `T-04` normaliza `\r\n`→`\n` antes de hashear, con test del **mismo contenido en CRLF y en LF exigiendo el mismo hash** |
| **Escribir en el árbol del plugin desplegado** (`GOT-003`) | Media | **Alto** | `dueno()` como única puerta con exit 3 (`T-04`), marcadores + confirmación extra anotada en la fila (`T-12`), nombres reservados, y test sobre un árbol marcado |
| **La premisa heredada de la spec que ya se cayó una vez** (`export-interop.py --root` sobre árbol de proyecto) | **Alta (ya materializado)** | Medio | Decidido en el plan (flag `--project`, `ADR-015`) y **re-comprobado con un comando** en la `Verificación` de `T-17`, que exige exit 1 sin el flag. Lección del `evaluator`: los «(verificado)» de la spec no se heredan, se re-ejecutan |
| **`project-scan.py` degenerando en escáner propio** por la puerta de atrás | Media | Medio | `T-07` con CA-10 como `grep` de las cuatro invocaciones en su `Verificación`; si los formatos de los sub-scripts no casan y aparece un normalizador, es **deuda declarada**, no horas silenciosas |
| **`/specialize` creciendo hasta ser inmantenible** (`ADR-008`; `/dev-cycle` tuvo que bajar de 218 a 198 líneas) | Media | Medio | Las tres tareas de C-05 (`T-11`, `T-12`, `T-13`) mueven el determinismo a los scripts; el comando queda como secuenciador. El linter avisa por encima de 200 líneas |
| **La sección de `/doctor` en verde con el registro vacío** (falsa seguridad — el defecto exacto que `memory-retrieval` encontró: «Instalación sana» con 0 entradas de journal) | Media | Medio | `T-16` exige criterio explícito para «sin registro» **distinto** de «registro sano», con su test |
| **`Archivos` incompleto en una tarea** → `scope-check.py` salta en el DoD con un falso positivo, porque el hook de guardia no cubre `Bash` (`guardrail-check.py:334`/`:355`) | Media | Bajo | Cada tarea del ledger lista sus ficheros reales, incluidos los **generados** (`interop/`) y los de test; se revisa al cerrar cada fase |
| **La revisión encuentra más de lo previsto** (precedente medido: `memory-retrieval`, 3 rondas, 38 gaps, 3 Critical, +66 % en horas IA) con **35 CA** que recorrer | **Alta** | Medio | Fase 3 con línea propia para revisar **y** para corregir (10,0 h, 21,3 % del base), bucle acotado a 3 por `adversarial-review`, y al 3.er rojo la skill `debug-root-cause` antes de preguntar |
| **`ADR-014` se queda en `propuesta`** si la revisión de C-10 no cierra limpia | Media | Bajo | `T-20` lo recoge: si la revisión valida C-10 contra el esquema, `ADR-014` pasa a `aceptada (validada: revisión de dos lentes, …)`; si pide un campo que no está en su decisión 6, el camino es **subir `version`**, no reinterpretar el esquema |

---

## Métricas de éxito

- **Capacidad entregada, medible el día del cierre** (es lo que CA-34 dice que se entrega): `python3 agent-kits/shared/pieces-registry.py listar --json` devuelve el registro de un árbol de prueba con sus tres estados; `/specialize --dry-run` deja el árbol idéntico; `/doctor` imprime una línea por fila. Sin esto, la fase no está.
- **Cero roles duplicados**: `role-collision.py` rechaza los cuatro nombres canónicos y `evals/check.py` mantiene en verde los negativos cruzados `/specialize` ↔ `plugin-dev`. Si el modelo elige `plugin-dev` para «crea un agente para mi proyecto», la métrica falla aunque el código funcione.
- **Coste de proceso real vs. estimado**: las 10,0 h de la Fase 3 contra lo que mida `usage-meter.py` por tarea, en `retro.md` y en la fila de `CALIBRATION.md`. Es el número que este repo lleva desviando (+66 % en la última muestra) y el que más valor tiene medir.
- **Punto de control diferido, con mecanismo ya existente** (CA-34): las retros de las **dos iniciativas siguientes** que usen al menos una persona de proyecto comparan sus intentos del bucle reviewer→implementer (traza «Revisión de dos lentes — intento N» del ledger) contra la media de las filas anteriores de `CALIBRATION.md`. **Criterio de retirada en pie**: si tras dos o tres iniciativas los intentos no bajan y siguen los mismos gaps, la capa no aporta y se retira.
- **Presupuesto del arranque intacto**: `skill-index.py` sigue por debajo de `LIMITE_LINEAS = 45` / `LIMITE_CHARS = 3500` con el tope de 5 piezas aplicado. Si el índice se infla, el tope no estaba haciendo su trabajo.

---

## Changelog del plan

| Fecha | Cambio | Autor |
|-------|--------|-------|
| 2026-09-09 | Creación del plan: 22 tareas en 3 fases sobre F1+F2, presupuesto heredado de `evaluation.md` (47,0 h base · 2.366,61 € · 1.898k tok), las cuatro condiciones del go convertidas en aristas del grafo, y las cuatro decisiones que el arquitecto y la condición (d) dejaban abiertas — cerradas: clave `especializacion.topePiezas`, `--reconstruir` nombrado por `/doctor` y ejecutado por `/specialize`, las dos filas de la regla 9 (+EN), y el modo proyecto de `export-interop.py` como flag `--project` (`ADR-015`, `propuesta`) | `planner` |

---

## Siguiente paso

Con el **OK del plan** del usuario (puerta de control), el agente **`implementer`** lo ejecuta fase a fase sobre una rama, marcando [`tasks.md`](tasks.md) como **ledger canónico** (checkbox + estado por tarea) y midiendo cada tarea con `usage-meter.py`. La revisión de dos lentes de la Fase 3 la despacha la skill `adversarial-review` (bucle acotado a 3). **No hay handoff a `qa`**: sin UI no hay `test-plan.md` que recorrer, así que el veredicto de pruebas lo dan las suites `pytest`, `lint_plugin.py`, `evals/check.py` y `export-interop.py --check` de la puerta de cierre. El cierre pasa por `changelog-sync` y por la **puerta de `/retro`** (`retro-gate.py`: sin `retro.md` + fila en `CALIBRATION.md` no hay cierre). **Jira no está configurado** en este proyecto (`.claude/jira.json` ausente), así que no hay volcado de tareas.
