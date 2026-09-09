---
generacion:            # ventana única: spec.md + evaluation.md (la spec la creó el evaluator en la misma pasada; no se duplica)
  inicio: 2026-09-09T17:56:55Z
  fin: 2026-09-09T18:07:07Z
  fuente: estimado     # `usage-meter.py close` degradó en esta máquina: «carpeta de transcripciones no disponible» (Windows). Tokens estimados a juicio por el tamaño de lo leído (analysis, task-brief.py y su suite, gotchas, plantillas, CALIBRATION) y lo escrito (spec + evaluación)
  tokens_reales: { entrada: 95000, salida: 26000, cache_creacion: 38000, cache_lectura: 520000 }
  eur: 1.44
  horas_ia: 0.33
  duracion: 10m
  ratio_usado: 479326
---

# 2026-09-09-brief-budget

> Presupuesto de las **cinco opciones combinables** del análisis `brief-budget` (presupuesto por sección del brief del
> subagente) para la **puerta go/no-go** de `/pm-cycle`: cuánto cuesta cada una, cuál conviene, en qué orden, y qué
> depende de la iniciativa vecina `plugin-refactor`.

| | |
|---|---|
| **Fecha** | 2026-09-09 |
| **Estado** | completado |
| **Prioridad global** | Alta |
| **Solicitante** | usuario (decisión del 2026-09-09 de atacar la causa en iniciativa aparte, opción B; hallazgo de la Lente B, intento 2, F1 de `project-specialization`) |
| **Spec** | [`spec.md`](spec.md) — `borrador`, derivada por el evaluator del análisis |
| **Plan** | pendiente (handoff a `planner`) |
| **Características evaluadas** | 5 (O1-O5 del análisis) + 3 líneas de proceso presupuestadas aparte |

> **Análisis de origen:** [`analysis.md`](analysis.md) — única fuente del alcance (9 secciones). Esta evaluación no lo amplía:
> lo que no está en él va aquí como riesgo o supuesto.

---

## Cuadro de mando

| Métrica | Total estimado | Confianza |
|--------|----------------|-----------|
| Esfuerzo humano | **26,4 h** (22,0 h base +20 %) | **Media** |
| Tiempo IA (ejecución) | **5,4 h** (+ 1,4 h supervisión) | **Baja** |
| Coste | **~1.340 €** (1.116,60 € base; 1.320 € horas + ~20 € tokens con margen) | **Media** |
| Tokens IA | **2,17 M facturables** (in 1,59 M / out 0,24 M / caché creación 0,34 M) + ~4,0 M lectura de caché | **Baja** |
| Multiplicador productividad | **×3,9** | — |
| Características | **5** (+ 3 líneas de proceso) | — |

---

## Resumen ejecutivo

Ha llegado un análisis medido, no una petición: 12 de 22 briefs del ledger real de `project-specialization` pasan del tope
de 10.000 caracteres (CA-08 de `memory-retrieval`) porque **seis de las siete secciones del brief no tienen presupuesto
propio** y `## Diseño` entra entera (3.510) en las 22 tareas. El análisis trae cinco opciones combinables (O1-O5) y pide
presupuestarlas sin decidir. Se presupuestan como C-01…C-05 (**16,5 h base**) más tres líneas de proceso que el histórico
del repo obliga a separar (revisión de dos lentes, corrección post-revisión y cierre: **5,5 h base**): **22,0 h base →
26,4 h con margen, ~1.340 €, 2,2 M tokens facturables**. La decisión que soporta es la puerta go/no-go y, dentro del go,
**qué opciones entran y en qué orden**, más una dependencia que **solo el usuario puede ordenar**: `plugin-refactor` propone
partir el `main()` de `task-brief.py` antes de que esta iniciativa le añada presupuestos por sección.

**Veredicto: go condicionado** — a ordenar frente a `plugin-refactor` en la puerta, a planificar C-05 desde el principio
(en `xfail` fechado) y a verificar la premisa de C-03 antes de abrir su tarea.

---

## Requerimientos recibidos

Mapa del `analysis.md` a las características evaluadas.

| ID | Característica | Requisito origen (ref.) | ¿Claro? |
|----|---------------|-------------------------|---------|
| C-01 | Presupuesto por sección (`DISENO_TOPE_CHARS`, `GAPS_TOPE_CHARS`, `VERIFICACION_TOPE_CHARS` + recorte + aviso) | `analysis.md` §4 O1; §5 «recorte por subsecciones enteras»; `GOT-008` «el tope de la sección» | claro; **los valores de las constantes no están** (se miden, no se inventan: §5) |
| C-02 | Diseño bajo demanda (`## Diseño` solo si la tarea referencia módulos del §5 de `design.md`; si no, puntero) | `analysis.md` §4 O2; §5 «O2 es mejor que O1 para esa sección» | **ambiguo**: el criterio «toca el diseño» no está definido («hay que definirlo bien o se vuelve heurística») |
| C-03 | Gaps solo de la tarea (tabla de revisión filtrada a la columna `Tarea` propia) | `analysis.md` §4 O3 | **ambiguo**: el código **ya** filtra por `Tarea == tid` y último intento (`task-brief.py:614`); lo que falta es un tope, o verificar por qué T-01 llega a 4.396 |
| C-04 | Verificación sin evidencia (solo comandos, nunca la salida pegada) | `analysis.md` §4 O4; test `:657-670` «lo pretende y no lo consigue del todo» | claro |
| C-05 | El guardarraíl deja de ser ciego (test CA-08 sobre todos los ledgers, con y sin `design.md`) | `analysis.md` §4 O5; §5 «la suite roja como estado intermedio»; §6 señales 1-2 | claro; **secuenciación obligatoria** (hoy pondría la suite en rojo) |
| — | Alcance out: no subir el tope · no recortar tarea/contrato · no tocar persona · no tocar memoria | `analysis.md` §3 | claro; recogido en `spec.md` «Fuera» con motivos |
| — | Señales de éxito (0/22, test verde, diseño no constante, 0 avisos en F2) | `analysis.md` §6 | claro; son los CA-01…CA-04 de la spec |

**Ambigüedades / información que falta:**

- **Valores de los topes nuevos.** El análisis da medianas y máximos por sección (§1) pero no fija constantes; exige medirlas
  en la máquina de trabajo con margen (`GOT-008`). Supuesto de esta evaluación: la medición ya hecha (§1) basta para
  proponerlas y el planner las fija; presupuesto **+0,5 h** en C-01 para re-medir y justificar.
- **Criterio «la tarea referencia el diseño» (C-02).** Sin definición determinista es heurística. Supuesto: casar los campos
  `Archivos`/`Dependencias` del bloque `### T-XX` contra las rutas/módulos listados en el §5 del `design.md` (estructura de la
  plantilla del architect, `agent-kits/architect/templates/design.md:97`); el 30 % del esfuerzo de C-02 es definirlo y
  probarlo con los tres casos (referencia / sin referencia / §5 ausente).
- **Premisa de C-03.** `_gaps_pendientes_de_tarea` ya devuelve solo las filas de `tid` del último intento. O el análisis midió
  un estado anterior del ledger, o los 4.396 de T-01 son filas legítimas de T-01 (que arrastró tres intentos con B-3). Se
  presupuesta C-03 como **acotar** (tope + recorte) más un test que afirme el filtro que ya existe; si se confirma que
  falta filtrar, sube a Media.
- **Tiempo de la suite con C-05.** ~3 s por brief medido hoy (T-05: 2,9 s) × ~300 briefs (32 ledgers) ≈ **15 min**. El
  análisis no lo contempla. Va como riesgo y como supuesto de la spec.
- **Estado del corpus de medición.** El ledger de `project-specialization` tiene una revisión en curso: sus gaps y
  verificaciones cambian. Las cifras «0 de 22» se validan sobre el ledger tal como esté al cerrar.

---

## Datos necesarios para una evaluación completa

- [x] **Requerimientos** completos y sin ambigüedades — con dos ambigüedades declaradas (C-02, C-03) y presupuestadas bajo supuesto
- [x] **Alcance** de cada característica acotado (qué entra y qué NO) — §3 y §4 del análisis; `spec.md` «Alcance»
- [x] **Criterios de aceptación / éxito** por característica — §6 del análisis → CA-01…CA-12 de la spec, cada uno con comando
- [x] **Restricciones** — tope invariante, contrato intocable, standalone, cp1252 (`GOT-005`), ruta/corpus (`GOT-008`)
- [x] **Dependencias externas** identificadas — `plugin-refactor` (orden), revisión en curso de `project-specialization` (corpus)
- [x] **Contexto técnico** disponible — repo leído: `task-brief.py` (840 líneas), `test_task_brief.py` (60 tests), plantilla del architect
- [x] **Tarifa/hora y supuestos de coste** confirmados — `.claude/rates.json` (verificado 2026-08-18, 22 días: fiable)

Sin bloqueantes. Lo abierto (valores de topes, criterio de C-02, premisa de C-03) lo cierra el planner con la maquinaria y
las mediciones ya disponibles; no requiere volver al usuario salvo para el orden frente a `plugin-refactor`.

---

## Supuestos económicos (ajustables)

**Coste = (horas × tarifa) + coste de tokens de IA.** Importes en **EUR**. Fuente: `.claude/rates.json` (fuente única
compartida con `planner` y `jira-sync`) y `docs/roadmap/CALIBRATION.md`.

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | 50 €/h | `rates.json` `tarifaHora` |
| Modelo IA asumido | claude-opus-4-8 | `rates.json` `modeloIA` |
| Precio input | 5 USD / 1M tokens → 4,60 € | `rates.json` `precioTokens.input`, verificado 2026-08-18 con `rates-verify` (< 90 días: fiable) |
| Precio output | 25 USD / 1M tokens → 23,00 € | ídem |
| Precio creación / lectura de caché | 6,25 / 0,50 USD por 1M → 5,75 / 0,46 € | ídem; la lectura de caché no cuenta para horas pero **sí** para € (aprendizaje 4 de `CALIBRATION.md`) |
| Tipo de cambio | 1 USD = 0,92 € | `rates.json` `tipoCambioUsdEur` — **supuesto**, no verificado (`_nota_fx`) |
| Ratio de supervisión | 25 % de las horas IA | `rates.json` `ratioSupervision` |
| Margen de contingencia | 20 % | `rates.json` `margenContingencia`; sobre horas base humanas e IA (y sobre tokens para el coste con margen) |
| Ratio tokens → hora-IA | **479.326 tok/h** | mediana de 5 muestras de `CALIBRATION.md` (precedencia sobre el default 300.000 no calibrado); horas IA = tokens facturables (in + creación de caché + out) ÷ ratio |
| FTE | 160 h/mes | `rates.json` `horasMesFTE` |

**Calibración aplicada (histórico + doctrina del plugin):**

- **LES-007 / LES-008 / LES-009** (separar lo que se mide de lo que se vende · presupuestar el proceso aparte · la revisión
  es la partida grande): las horas **humanas** son «lo que se vende» (nunca validadas, aprendizaje 2 de `CALIBRATION.md`);
  las horas **IA** derivan de tokens. Revisión y corrección van como **líneas propias** (P-01, P-02).
- **Fila `memory-retrieval` (2026-09-08):** «corrección post-revisión como línea propia igual a la de revisión» → P-02 = P-01.
  Y su desviación **IA +66 %** sobre lo estimado se aplica como **confianza Baja** en tokens/horas IA, no inflando la base.
- **Fila `subagent-personas`:** «tarea con tests ≈ ×2 respecto a prosa» → todas las C-XX son código + tests; ninguna se
  presupuesta en minutos.
- **Evidencia propia del script:** F1 de `project-specialization` (la persona, ~200 líneas de `task-brief.py`) necesitó
  **tres rondas** de revisión sin converger; el mismo fichero acumula «cuatro reglas para una sección» (`plugin-refactor`
  §). Por eso P-01/P-02 pesan 4,0 h base sobre 16,5 h de características (24 %), por encima del ~10 % habitual.
- **LES-004** (prosa se mide en minutos) **no aplica**: no hay prosa pura salvo el cierre (P-03).
- `docs/knowledge/journal/` sin entrada previa de esta iniciativa: no hay pendientes de sesión anterior que heredar.

---

## Evaluación por característica

### C-01 — Presupuesto por sección (`DISENO_TOPE_CHARS`, `GAPS_TOPE_CHARS`, `VERIFICACION_TOPE_CHARS`)

- **Requisito origen**: `analysis.md` §4 O1; §5 (recorte de diseño por subsecciones enteras; medir en la máquina); `GOT-008` («el camino es el tope de la sección»)
- **Descripción**: tres constantes nuevas, cada una con recorte alineado (`_recorte_seguro`, ya existe) y aviso por stderr, calcando el patrón de `MEMORIA_TOPE_CHARS` (`task-brief.py:188-205`); el aviso de F1 (`:818-833`) se amplía con las secciones recortadas. Es la **red** para lo que quede variable tras C-02…C-04.
- **Complejidad**: **Media** — la maquinaria existe; lo que cuesta es (a) medir y justificar tres valores con margen y (b) que `## Diseño` se recorte por subsecciones enteras (`###`), no por caracteres, lo que requiere un recorte estructural sobre `_recorte_seguro` (que hoy corta por líneas).
- **Esfuerzo**: **4,0 h** base · confianza **Media** (método: 3 × [constante + recorte + aviso + test ≈ 0,8 h] + 0,5 h medición/justificación + 1,1 h recorte por subsecciones de diseño con su test de fences)
- **Previsión IA**: 260 k in / 40 k out (+ 60 k caché creación; ~0,7 M lectura de caché) · **2,78 €** · 0,75 h IA
- **Coste**: (4,0 h × 50 €) + 2,78 € = **202,78 €** base
- **Impacto / áreas afectadas**: `agent-kits/shared/task-brief.py` (constantes `:105-133`, secciones `:722-752`, `_design_elegida` `:531`, aviso `:818-833`), `agent-kits/shared/test_task_brief.py` (3-4 tests nuevos sobre `tmp_path`)
- **Dependencias y prerequisitos**: ninguna dura; **conviene después** de C-02/C-03/C-04 (así los topes se fijan sobre lo que queda variable y no sobre el problema entero). Orden frente a `plugin-refactor` (riesgo transversal R-1).
- **Riesgos**: recortar diseño a ciegas quita justo lo que la tarea necesita (§5) — mitigado por «subsecciones enteras» y por hacer C-02 antes; constantes elegidas al borde se rompen con ruta/corpus (`GOT-008`) — mitigado con margen medido y memoria presupuesta **al tope** (2.400), no en su mediana.
- **Incógnitas / preguntas abiertas**: valores concretos (propuesta de partida para el planner, a re-medir: `DISENO ≈ 1.500`, `GAPS ≈ 1.200`, `VERIFICACION ≈ 800`, de forma que fijo 1.025 + memoria 2.400 + diseño 1.500 + tarea máx 3.845 + verificación 800 + gaps 1.200 = 10.770 sin persona — **aún no cabe en el peor caso**: por eso C-01 solo no basta y C-02 es el grueso).

### C-02 — Diseño bajo demanda

- **Requisito origen**: `analysis.md` §4 O2; §5 («O2 es mejor que O1 para esa sección»); §6 señal 3 («`## Diseño` deja de ser constante»)
- **Descripción**: `## Diseño` se inyecta solo si la tarea referencia módulos del §5 «Impacto en módulos y ficheros» de `design.md`; si no, un puntero de una línea. Ataca la causa (3.510 × 22 = 77.000 caracteres inyectados cuando la mayoría de tareas no diseñan nada).
- **Complejidad**: **Alta** — hay que definir un criterio **determinista** (no heurístico) de «la tarea toca el diseño», parsear el §5 del `design.md` (tabla de la plantilla del architect) y casarlo con `Archivos`/`Dependencias` del bloque de la tarea; más el ajuste de la plantilla `agent-kits/architect/templates/design.md:97` para que el §5 sea parseable de forma estable, y los casos degradados (§5 ausente → comportamiento de hoy con aviso).
- **Esfuerzo**: **6,0 h** base · confianza **Media** (método: 1,8 h criterio + parser del §5 · 1,2 h integración en `main()` y puntero · 1,0 h plantilla del architect + doc de su §5 · 2,0 h tests de los tres casos + fences + `design.md` en borrador)
- **Previsión IA**: 380 k in / 60 k out (+ 80 k caché creación; ~1,0 M lectura) · **4,05 €** · 1,08 h IA
- **Coste**: (6,0 h × 50 €) + 4,05 € = **304,05 €** base
- **Impacto / áreas afectadas**: `agent-kits/shared/task-brief.py` (`_design_elegida` `:531`, nueva función de casado, `main()`), `agent-kits/shared/test_task_brief.py`, `agent-kits/architect/templates/design.md` (§5), `agents/architect.md` solo si cambia la instrucción de rellenar el §5 (→ regenerar `interop/` con `export-interop.py`)
- **Dependencias y prerequisitos**: el único `design.md` real del repo es el de `project-specialization` (su §5 sirve de fixture en lectura); acopla el brief a la estructura de `design.md` (riesgo R-3). Si se toca `agents/architect.md`, la puerta `export-interop.py --check` obliga a regenerar.
- **Riesgos**: criterio que se vuelve heurística (§4 «en contra») → mitigación: casado literal de rutas/módulos, con test por caso y aviso cuando el §5 no es parseable; tareas que **sí** necesitan el diseño y no lo referencian en `Archivos` (falso negativo) → mitigación: el puntero de una línea siempre queda y el planner escribe `Archivos` completos (ya es su plantilla).
- **Incógnitas / preguntas abiertas**: ¿casado por ruta de fichero, por nombre de módulo, o ambos? ¿Cuenta `Dependencias` a otras tareas que sí referencian el diseño (transitividad)? Supuesto de esta evaluación: **rutas y nombres, sin transitividad** (lo simple y determinista); la transitividad, si hace falta, es una iteración posterior.

### C-03 — Gaps solo de la tarea

- **Requisito origen**: `analysis.md` §4 O3; §1 fila «Gaps» (T-01 = 4.396, «la tabla de los intentos de revisión entra entera»)
- **Descripción**: la sección `## Gaps pendientes de revisión` entra acotada a las filas de la propia tarea (columna `Tarea`) del último intento, y con tamaño controlado.
- **Complejidad**: **Baja** — `_gaps_pendientes_de_tarea` (`task-brief.py:595-620`) **ya** filtra por `celdas[3] == tid` y por último intento. Lo que queda es (a) un test que afirme ese filtro (hoy no lo guarda ninguno sobre un ledger con varias tareas y varios intentos) y (b) acotar el tamaño de las filas que sí son de la tarea (gaps largos con `evidencia` extensa), lo que enlaza con `GAPS_TOPE_CHARS` de C-01.
- **Esfuerzo**: **1,5 h** base · confianza **Media** (método: 0,3 h verificar la premisa sobre T-01 · 0,5 h test del filtro con fixture de dos intentos/varias tareas · 0,7 h acotado de filas largas con su test). **Sube a ~3,0 h (Media)** si se confirma que el filtro no cubre algún caso (p. ej. filas sin `Tarea` o con varias tareas en la celda).
- **Previsión IA**: 110 k in / 15 k out (+ 25 k caché creación; ~0,3 M lectura) · **1,13 €** · 0,31 h IA
- **Coste**: (1,5 h × 50 €) + 1,13 € = **76,13 €** base
- **Impacto / áreas afectadas**: `agent-kits/shared/task-brief.py` (`:595-620`, `:722-738`), `agent-kits/shared/test_task_brief.py`
- **Dependencias y prerequisitos**: verificar la premisa **antes** de abrir la tarea (comando en `spec.md` «Supuestos»); comparte constante con C-01 si entra `GAPS_TOPE_CHARS`.
- **Riesgos**: presupuestar un filtro que ya existe (trabajo muerto) — mitigado por la verificación previa; recortar un gap a medias deja una «corrección sugerida» sin su «evidencia» — mitigación: recorte por **fila entera** (nunca dentro de una fila), calcando «subsecciones enteras».
- **Incógnitas / preguntas abiertas**: ¿los 4.396 de T-01 son filas legítimas de T-01 (tres intentos con B-3) o la medición del análisis se hizo con un estado del ledger/código anterior a `:614`? Lo resuelve el comando de la spec en 1 minuto.

### C-04 — Verificación sin evidencia

- **Requisito origen**: `analysis.md` §4 O4; §1 fila «Verificación» (T-02 = 2.285, «arrastra la evidencia pegada»); test `test_task_brief.py:657-670` («lo pretende y no lo consigue del todo»)
- **Descripción**: el brief lleva los comandos del campo `Verificación`, nunca la salida pegada en el ledger (`(ejecutada … — salida: …)`, sub-listas de resultados, notas medidas). `_verificacion_de_tarea` (`:406`) ya separa `items` de `ejecutada`; lo que se cuela son ítems que **son** evidencia con forma de comando o notas largas tras el `→`.
- **Complejidad**: **Baja** — parser existente (`parse_verificacion` de `ledger-lint`, fuente única); el cambio es acotar cada ítem al `comando → resultado esperado` y descartar las colas de evidencia, con tests sobre las formas reales de T-02.
- **Esfuerzo**: **2,0 h** base · confianza **Alta** (método: 0,5 h inventario de las formas de evidencia en los ledgers reales · 0,8 h regla + integración · 0,7 h tests con fixture de T-02 real reducido)
- **Previsión IA**: 140 k in / 20 k out (+ 30 k caché creación; ~0,4 M lectura) · **1,46 €** · 0,40 h IA
- **Coste**: (2,0 h × 50 €) + 1,46 € = **101,46 €** base
- **Impacto / áreas afectadas**: `agent-kits/shared/task-brief.py` (`:406-424`, `:740-752`), `agent-kits/shared/test_task_brief.py` (`:640-750`); **no** toca `ledger-lint.py` (el parser es suyo: si hubiera que cambiarlo, el alcance crece y el test byte a byte de la copia literal lo detecta)
- **Dependencias y prerequisitos**: ninguna; si C-01 entra, `VERIFICACION_TOPE_CHARS` pasa a ser una red que casi nunca salta.
- **Riesgos**: quitar un ítem que **sí** es un comando legítimo (falso positivo) — mitigación: la regla actúa sobre la **cola** del ítem (tras el resultado esperado), nunca sobre el comando; divergencia con `ledger-lint` si el parser cambia — mitigación: la regla vive en `task-brief.py`, el parser no se toca.
- **Incógnitas / preguntas abiertas**: ¿se conserva la nota «re-ejecútala, la salida grabada es de otra sesión»? Supuesto: sí (es una línea y protege el contrato).

### C-05 — El guardarraíl deja de ser ciego

- **Requisito origen**: `analysis.md` §4 O5; §5 («la suite roja como estado intermedio»; `xfail` con motivo y fecha); §6 señales 1-2
- **Descripción**: el test del CA-08 recorre **todos** los `docs/roadmap/*/tasks.md` (32 hoy), con y sin `design.md`, en vez de solo `memory-retrieval`. Nace `xfail(strict=True)` fechado y pasa a verde como último paso. Convierte el problema en visible para siempre.
- **Complejidad**: **Media** — el test en sí es barato (parametrizar `test_task_brief.py:781` por ledger), pero tiene tres trampas: (1) **tiempo** (~3 s/brief × ~300 briefs ≈ 15 min de suite: hay que acotar sin volver a un solo ledger); (2) **Windows**: el test actual **ya falla en HEAD en esta máquina** por la ruta absoluta (`GOT-008`), luego la versión nueva debe pasar aquí, no solo en el sandbox Linux; (3) **secuenciación** con `xfail` fechado hasta que C-01…C-04 bajen los briefs.
- **Esfuerzo**: **3,0 h** base · confianza **Media** (método: 0,6 h parametrización + descubridor de ledgers · 1,0 h acotado del tiempo (marca `slow`/muestra/ledgers con `design.md` + `memory-retrieval`) · 0,6 h `xfail` fechado + paso a verde · 0,8 h verificación cruzada Windows/Linux del margen `GOT-008`)
- **Previsión IA**: 170 k in / 25 k out (+ 35 k caché creación; ~0,5 M lectura) · **1,79 €** · 0,48 h IA
- **Coste**: (3,0 h × 50 €) + 1,79 € = **151,79 €** base
- **Impacto / áreas afectadas**: `agent-kits/shared/test_task_brief.py` (`:781-800`), posiblemente `pytest.ini`/marcas si se introduce `slow`; docstring del test con la fecha de la medición
- **Dependencias y prerequisitos**: **entra en rojo primero y en verde el último** (depende de C-01…C-04); el corpus real de `project-specialization` es su fixture principal (solo lectura; su ledger cambia con la revisión en curso).
- **Riesgos**: suite lenta que nadie corre (pieza muerta) — mitigación: acotar tiempo; `xfail` que se queda para siempre — mitigación: `strict=True` + fecha + CA-09 de la spec (`grep` de `xfail` sin fecha → vacío); rojo en Windows por `GOT-008` aunque pase en CI — mitigación: margen medido en la máquina de trabajo y CA-04 exige verde **aquí**.
- **Incógnitas / preguntas abiertas**: ¿todos los ledgers o los que tienen `design.md` + `memory-retrieval` + muestra? El análisis dice «todos»; la evaluación presupuesta «todos, acotando el tiempo». Lo cierra el planner.

### Líneas de proceso (presupuestadas aparte — LES-008)

| ID | Línea | Esfuerzo base | Tokens (in / out / caché cr.) | € tokens | Método |
|----|-------|---------------|-------------------------------|----------|--------|
| P-01 | **Revisión de dos lentes** (A conformidad con spec + B corrección; C/D condicionales por `review-lens-select.py`, aquí probablemente no saltan: sin rutas sensibles) | 2,0 h | 300 k / 40 k / 60 k (~1,1 M lectura compartida con P-02/P-03) | 2,65 € | 2 lentes × 2 rondas sobre un script con historial de 3 rondas (F1); LES-009 |
| P-02 | **Corrección post-revisión** | 2,0 h | 150 k / 25 k / 30 k | 1,67 € | = P-01 (fila `memory-retrieval` de `CALIBRATION.md`) |
| P-03 | **Cierre**: `changelog-sync`, `GOT-009` → `aceptada` y nota en `GOT-008` (lo escribe quien cierra), `/retro` con ratio medido, doc de las constantes en el docstring del script | 1,5 h | 80 k / 15 k / 15 k | 1,07 € | prosa + comandos deterministas; LES-004 aplica a esta línea |
| | **Subtotal proceso** | **5,5 h** | 530 k / 80 k / 105 k | **5,39 €** | 0,25 M lectura de caché adicional imputada aquí; **1,49 h IA** |

---

## Comparativa

Ordenada por **orden de ejecución recomendado** (C-05 abre en rojo y cierra en verde; ver Recomendación).

| # | Característica | Complejidad | Horas (base) | Coste € (base) | Tokens facturables | Prioridad | Confianza |
|---|---------------|-------------|--------------|----------------|--------------------|-----------|-----------|
| C-05 | Guardarraíl sobre todos los ledgers (rojo → verde) | Media | 3,0 h | 151,79 € | 230 k | **Crítica** (sin él, todo lo demás puede volver a romperse en silencio) | Media |
| C-02 | Diseño bajo demanda | **Alta** | 6,0 h | 304,05 € | 520 k | **Alta** (el bloque mayor: 3.510 × 22) | Media |
| C-04 | Verificación sin evidencia | Baja | 2,0 h | 101,46 € | 190 k | Media (quick win) | Alta |
| C-03 | Gaps solo de la tarea | Baja | 1,5 h | 76,13 € | 150 k | Media (verificar premisa) | Media |
| C-01 | Presupuesto por sección (red) | Media | 4,0 h | 202,78 € | 360 k | Alta (garantía final) | Media |
| P-01…P-03 | Proceso (revisión · corrección · cierre) | — | 5,5 h | 280,39 € | 715 k | — | Baja |
| | **Total** | | **22,0 h** | **1.116,60 €** | **2,17 M** (+ ~4,0 M lectura de caché) | | **Media** |

---

## Presupuesto total

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 22,0 h × 50 €/h (16,5 h características + 5,5 h proceso) | 1.100,00 € |
| Margen de contingencia | +20 % sobre desarrollo base (4,4 h) | 220,00 € |
| Tokens IA (input) | 1,59 M × 4,60 €/M (base) → 1,91 M con margen | 7,31 € → 8,78 € |
| Tokens IA (output) | 0,24 M × 23,00 €/M → 0,29 M con margen | 5,52 € → 6,62 € |
| Tokens IA (creación de caché) | 0,335 M × 5,75 €/M → 0,40 M con margen | 1,93 € → 2,31 € |
| Tokens IA (lectura de caché) | 4,0 M × 0,46 €/M → 4,8 M con margen | 1,84 € → 2,21 € |
| **Total base (sin margen)** | 1.100,00 € + 16,60 € | **1.116,60 €** |
| **Total estimado (con margen)** | 1.320,00 € + 19,92 € | **1.339,92 € ≈ 1.340 €** |

> El coste de tokens es el **1,5 %** del total: la partida que manda son las horas humanas, y son las que nunca se han
> validado en este repo (aprendizaje 2 de `CALIBRATION.md`). Si el trabajo lo hace la IA con supervisión, el coste real
> se acerca a las **6,8 h totales** del cuadro de productividad (≈ 340 € a la misma tarifa + ~20 € de tokens).

---

## Productividad IA (humano vs. IA)

| KPI | Valor |
|-----|-------|
| Horas humanas estimadas | 26,4 h (22,0 h base) |
| Horas IA (ejecución) | 5,4 h (4,52 h base = 2,165 M tokens facturables ÷ 479.326) |
| Supervisión humana | 1,4 h (25 % de las horas IA) |
| **Horas totales (IA + supervisión)** | **6,8 h** |
| Horas ahorradas | 19,6 h |
| **Ahorro** | **74 %** |
| **Multiplicador de productividad** | **×3,9** |
| FTE equivalentes *(opcional)* | 0,12 |

> Horas mostradas **con el margen de contingencia (+20 %)** ya aplicado sobre las horas base (humanas e IA). Las horas IA
> derivan de tokens con el ratio **calibrado** (479.326 tok/h, mediana de 5 muestras) — no son un juicio de reloj. La fila
> `memory-retrieval` de `CALIBRATION.md` avisa de que la IA sola se desvió **+66 %** cuando hubo tres rondas de revisión:
> si aquí pasa lo mismo, las horas IA reales rondarían **9 h**; por eso la confianza en esta fila es **Baja**.

---

## Recomendación

- **Veredicto**: **go condicionado** a tres cosas que se cierran en la puerta o en el plan, no en el código:
  1. **Ordenar frente a `plugin-refactor`** (decisión del usuario, no de esta evaluación). Si `plugin-refactor` va primero,
     `brief-budget` entra sobre un `main()` ya partido por secciones y C-01/C-02 abaratan ~1 h; si `brief-budget` va primero,
     sus funciones nuevas nacen con nombre por sección (ver `spec.md` «Supuestos») para que el refactor las mueva sin
     reescribirlas. Lo que **no** conviene es intercalarlas.
  2. **C-05 planificado desde el principio**: el test sobre todos los ledgers se escribe en la primera tarea (`xfail(strict=True)`
     fechado — es el RED de toda la iniciativa) y pasa a verde en la última.
  3. **Verificar la premisa de C-03** (1 minuto, comando en la spec) antes de abrir su tarea: si el filtro ya existe, C-03 es
     acotar + test y se queda en 1,5 h; si no, sube a 3,0 h.
- **Quick wins** (bajo coste, alto valor): **C-04** (2,0 h, confianza Alta, baja T-02 de 2.285 a ~200) y **C-03** (1,5 h, si
  la premisa se confirma).
- **Costosas / a valorar**: **C-02** (6,0 h, Alta): es el grueso y ataca la causa (el 35 % del tope en las 22 tareas); vale lo
  que cuesta porque sin ella C-01 sola **no cabe en el peor caso** (aritmética en C-01 «Incógnitas»). Descartarla obligaría a
  `DISENO_TOPE_CHARS` muy bajo y a recortar a ciegas justo lo que el análisis (§5) pide no recortar.
- **Orden sugerido**: **C-05 (rojo) → C-02 → C-04 → C-03 → C-01 → C-05 (verde)** — sigue el §4 del análisis («O5 al final pero
  planificado desde el principio, O2 + O3 el grueso, O4 si sale barato, O1 como red»): C-02 primero porque es el bloque
  mayor y define cuánto queda variable; C-04/C-03 después por baratas; C-01 al final para fijar topes **sobre lo que queda**,
  no sobre el problema entero; C-05 cierra.
- **Fuera de alcance recomendado**: lo del §3 del análisis (tope, contrato, persona, memoria) y partir `main()` (es de
  `plugin-refactor`). Si el usuario quisiera una **vía mínima**, C-05 + C-02 + C-04 (11,0 h + proceso) ya cumplen las
  señales 1-3 del §6 en la mayoría de los casos; C-01 y C-03 son la garantía del peor caso.

---

## Riesgos transversales

| # | Riesgo | Probabilidad | Impacto | Mitigación |
|---|--------|-------------|---------|------------|
| R-1 | **Orden con `plugin-refactor`**: partir `main()` de `task-brief.py` (155 líneas) después de añadirle presupuestos obliga a refactorizar dos veces (`plugin-refactor/analysis.md:61,121-122`) | Alta si no se ordena en la puerta | Medio (~1-2 h de retrabajo, más riesgo de regresión sobre 60 tests) | El usuario ordena las dos en la puerta; si `brief-budget` va primero, funciones con nombre por sección desde el principio; nunca intercalar |
| R-2 | **El corpus de medición cambia**: revisión en curso sobre el ledger de `project-specialization` (gaps y verificaciones se mueven); crece `docs/knowledge/` (37 entradas) | Alta | Bajo-Medio (cifras «0 de 22» y topes al borde) | Topes con margen medido y memoria presupuesta **al tope** (2.400); CA-01…CA-03 se validan sobre el ledger tal como esté al cerrar; no tocar ese ledger |
| R-3 | **Acoplar el brief a la estructura de `design.md`** (C-02): un `design.md` futuro con §5 distinto rompe el criterio en silencio | Media | Medio | Parseo del §5 de la plantilla del architect con degradación explícita (§5 ausente → inyección completa + aviso) y test del caso; la plantilla cambia en la misma iniciativa |
| R-4 | **`GOT-008` en el guardarraíl** (C-05): el test pasa en CI Linux y falla en Windows por la ruta absoluta (~250 caracteres) — hoy ya ocurre con el test de `memory-retrieval` en HEAD | Alta | Alto (la puerta que impide la regresión no se puede correr donde se trabaja) | Margen medido en la máquina de trabajo; CA-04 exige verde aquí; considerar que el test afirme `≤ BRIEF_TOPE_CHARS − margen_ruta` documentado |
| R-5 | **Suite lenta** (C-05): ~300 briefs × ~3 s ≈ 15 min → nadie la corre → pieza muerta | Alta | Medio | Marca `slow` o muestra acotada (ledgers con `design.md` + `memory-retrieval` + N al azar con semilla fija); nunca volver a un solo ledger |
| R-6 | **Bucle de revisión largo** sobre un fichero con historial (F1: 3 rondas sin converger; «cuatro reglas para una sección») | Media | Medio (+66 % IA como en `memory-retrieval`) | P-01/P-02 presupuestadas como líneas propias al 24 % de las características; funciones pequeñas con nombre; TDD con RED evidenciado por tope |
| R-7 | **`xfail` que se queda** (C-05 en fase intermedia) | Baja | Alto (guardarraíl ciego otra vez, ahora con excusa) | `strict=True` + fecha en el motivo + CA-09 (`grep` de `xfail` sin fecha → vacío) + `retro-gate` |
| R-8 | **No se mide si el subagente rinde mejor con briefs cortos** (§5 del análisis): la iniciativa respeta el CA-08, no lo demuestra | — | Bajo (es la premisa de `memory-retrieval`, no de esta) | Declarado como fuera de alcance; si algún día se cuestiona el tope, es otra iniciativa sobre la spec de `memory-retrieval` |

---

## Siguiente paso

Para **ejecutar** lo aprobado, genera el plan detallado con el agente **`planner`** sobre esta misma carpeta
(`docs/roadmap/2026-09-09-brief-budget/`, `improvement-plan.md` + `tasks.md`). Propuesta de handoff:

- **Se aprueban para planificar (si el usuario da el go):** las cinco, en el orden **C-05 (rojo) → C-02 → C-04 → C-03 → C-01 →
  C-05 (verde)**, con las tres condiciones de la Recomendación (orden frente a `plugin-refactor` decidido por el usuario;
  C-05 en la primera tarea como `xfail` fechado; premisa de C-03 verificada antes de abrir su tarea).
- **Requisitos de secuencia:** C-01 fija sus constantes **después** de C-02/C-03/C-04 (sobre lo que queda variable); si C-02
  toca `agents/architect.md`, regenerar `interop/` (`export-interop.py --check` es puerta).
- **Vía mínima** si el go es parcial: C-05 + C-02 + C-04.
- El `planner` hereda las horas y costes por característica de esta evaluación (no re-estima desde cero) y actualizará la
  fila **Plan** de esta evaluación y el campo `plan:` de la spec al crear el plan. Las líneas P-01…P-03 van al plan como
  presupuesto de proceso, no como tareas de producto.

---

## Changelog

| Fecha | Cambio |
|---|---|
| 2026-09-09 | Evaluación creada desde `analysis.md` (única fuente del alcance) junto con `spec.md` (`borrador`); estado `en-revision`; `Plan` pendiente. Medición del meter degradada a `estimado` (Windows, sin carpeta de transcripciones) |
