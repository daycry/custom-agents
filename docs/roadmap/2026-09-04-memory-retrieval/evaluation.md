---
generacion:            # ventana compartida con spec.md · improvement-plan.md · tasks.md (se cuenta UNA vez)
  inicio: 2026-09-04T09:00:00Z
  fin: 2026-09-04T09:40:00Z
  fuente: estimado     # el usage-meter no puede leer la transcripción en este entorno: no hay medición
  tokens_reales: { entrada: 180000, salida: 60000, cache_creacion: 40000, cache_lectura: 900000 }
  eur: 2.85
  horas_ia: 0.58
  duracion: 40m
  ratio_usado: 479326
---

# 2026-09-04-memory-retrieval

> Presupuesto de la recuperación de memoria técnica: seis características, con las lecciones de
> calibración de este repo APLICADAS (que es justo lo que el análisis denuncia que nadie hace).

| | |
|---|---|
| **Fecha** | 2026-09-04 |
| **Estado** | borrador |
| **Prioridad global** | Alta |
| **Solicitante** | usuario (petición del 2026-09-04, tras publicar v1.16.0) |
| **Spec** | [`spec.md`](spec.md) |
| **Plan** | [`improvement-plan.md`](improvement-plan.md) |
| **Características evaluadas** | 6 |

---

## Cuadro de mando

| Métrica | Total estimado | Confianza |
|--------|----------------|-----------|
| Esfuerzo humano | **40,8 h** (34 h base +20 %) | **Baja** |
| Tiempo IA (ejecución) | **3,13 h** (+ 0,79 h supervisión) | Media |
| Coste | **2.050 €** | **Baja** |
| Tokens IA | **1.248.000** (in 990.000 / out 258.000) | Media |
| Multiplicador productividad | **×10,4** | — |
| Características | **6** | — |

**Por qué las confianzas son estas, y no más altas.** `CALIBRATION.md` aprendizaje 2, literal: «las
horas HUMANAS estimadas no se han validado nunca — todas las filas tienen 0 h humanas reales». El
coste de esta iniciativa es **99,5 % horas humanas** (2.040 € de 2.050 €), así que la confianza del
coste **no puede ser mejor** que la de las horas humanas: **Baja**. Lo contrario también es cierto y
está medido: el coste de **IA** es el que las 5 muestras sobrestimaron por un **orden de magnitud**
(desviaciones de tokens −97 %, −95 %, −80 %, −74 %, −66 %), y aquí va estimado con el ratio medido
del propio proyecto, así que su confianza es **Media** — no Alta, porque ninguna de las 5 muestras
llevaba SQLite ni dos hooks nuevos.

---

## Resumen ejecutivo

Ha llegado un análisis medido (`analysis.md`) que dice que este plugin **escribe memoria muy bien y
la recupera muy mal**: 31 entradas curadas (27.100 tokens) de las que **17 (55 %) no las cita
ninguna pieza ejecutable**, **0 tokens** de memoria inyectados al arrancar sesión y **0** entradas de
journal. Se presupuestan **seis características** que cierran los cinco huecos del análisis: la capa
de recuperación que falta (tres capas deterministas sobre índice FTS5 reconstruible), la **llegada**
presupuestada a los dos caminos por los que un agente recibe contexto, la **prueba** de que ese
camino se recorre, la captura episódica automática, que la doctrina viaje con el plugin y el cierre
del bucle `/retro`.

La decisión que soporta: **go**, con la Fase 1 arrancando ya y la Fase 6 tratada como parte de la
entrega y no como opcional — el análisis la declara **condición previa** («reforzar la recuperación
es afilar un grifo sin agua» mientras `/retro` esté parado: 15 días y 13 iniciativas cerradas).

---

## Requerimientos recibidos

Mapa del análisis de origen a las características evaluadas.

| ID | Característica | Requisito origen (ref.) | ¿Claro? |
|----|---------------|-------------------------|---------|
| C-01 | Recuperación — `knowledge-find.py` (3 capas), índice FTS5 reconstruible, lint del índice | `analysis.md` §3 R1 + R3; huecos §1.4-2 y §1.4-5 | sí |
| C-02 | Llegada — inyección presupuestada en `task-brief.py` y `session-context.sh` | `analysis.md` §3 R2; hueco §1.4-1 (el más caro) | sí |
| C-03 | Prueba de que se recorre — casos en `evals/` + salud de memoria en `/doctor` | `analysis.md` §2 «lo que hacen mejor» (a) y (b); nadie lo tiene | sí |
| C-04 | Captura episódica — `UserPromptSubmit`, log crudo con opt-out, resumen escrito por el hook, promoción | `analysis.md` §3 R5 (rama «reforzarlo») + §2 (c) y (d); hueco §1.4-3 | **parcial** — el contrato de `UserPromptSubmit` (¿llega `session_id`?) no está verificado |
| C-05 | Que la doctrina viaje — assets del plugin vs memoria del proyecto | `analysis.md` §3 R4; hueco §1.4-4 | sí |
| C-06 | Cerrar el bucle — `/retro` disparado al cerrar, doc ES/EN, entradas de `docs/knowledge/` | `analysis.md` §3 «condición previa» | sí |

**Ambigüedades / información que falta:**

1. **Contrato de `UserPromptSubmit`** (afecta a C-04): la spec lo declara **supuesto no verificado**
   y da el plan B (nombrar el log por fecha y casar por mtime). Hay que verificarlo en la doc
   oficial **antes** de implementar y anotar la fecha, como hizo `memory-health` con `SessionEnd`.
   Esta es la razón por la que C-04 es la característica de **peor confianza**.
2. **FTS5 en el `sqlite3` del consumidor** (afecta a C-01): no se puede garantizar en la máquina
   ajena. Resuelto por diseño con el recorrido plano (CA-06), no por estimación.
3. **Formato de la promoción journal → candidata** (afecta a C-04): la spec fija la puerta
   (`/retro`, `estado: propuesta`) pero no el umbral exacto de «patrón repetido». Queda como
   decisión de implementación, con el umbral mínimo escrito en la tarea (≥ 2 entradas).
4. **Cuánto ahorra realmente la 1.ª capa frente a leer el índice** está estimado con las cifras de
   hoy (3.685 tokens de índice vs ~25 por acierto), pero **el ahorro agregado por sesión no está
   medido** y esta evaluación no lo promete.

---

## Datos necesarios para una evaluación completa

- [x] **Requerimientos** completos y sin ambigüedades — salvo las 4 de arriba, todas acotadas
- [x] **Alcance** de cada característica acotado (§Alcance de la spec, con «Fuera» explícito)
- [x] **Criterios de aceptación / éxito** por característica — 25 criterios, 19 de ellos `[GWT]`
- [x] **Restricciones** — repo público, solo stdlib, la degradación nunca bloquea, ningún test con red
- [x] **Dependencias externas** — ninguna nueva (es la decisión de diseño 2)
- [x] **Contexto técnico** — medido sobre este mismo repo
- [x] **Tarifa/hora y supuestos de coste** — `.claude/rates.json`, precios verificados el 2026-08-18
- [ ] **Contrato oficial de `UserPromptSubmit`** — **pendiente**; bloquea el arranque de la Fase 4,
      no el de las Fases 1-3

---

## Supuestos económicos (ajustables)

**Coste = (horas × tarifa) + coste de tokens de IA.** Importes en **EUR**. Todos los valores salen de
`.claude/rates.json` y `docs/roadmap/CALIBRATION.md`; **ninguno está inventado**.

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | **50 €/h** | `rates.json` `tarifaHora` |
| Modelo IA asumido | **claude-opus-4-8** | `rates.json` `modeloIA` |
| Precio input | **4,60 €** / 1M tokens | 5 USD/M × 0,92 · verificado el **2026-08-18** (18 días, < 90 ⇒ fiable) |
| Precio output | **23,00 €** / 1M tokens | 25 USD/M × 0,92 · verificado el 2026-08-18 |
| Precio creación de caché | **5,75 €** / 1M tokens | 6,25 USD/M × 0,92 |
| Precio lectura de caché | **0,46 €** / 1M tokens | 0,50 USD/M × 0,92 |
| Tipo de cambio | 1 USD = **0,92 €** | `rates.json` `tipoCambioUsdEur` — **SUPUESTO fijo, no verificado**; revisar antes de facturar |
| Ratio de supervisión | **25 %** de las horas IA | `rates.json` `ratioSupervision` |
| Margen de contingencia | **20 %** | `rates.json` `margenContingencia`; sobre horas base (humanas e IA) |
| Jornada | **8 h** | `rates.json` `horasJornada` |
| Horas por empleado-mes (FTE) | **160 h** | `rates.json` `horasMesFTE` |
| Ratio tokens → hora IA | **479.326 tok/h** | `CALIBRATION.md`, **mediana de 5 muestras medidas** (no el default no calibrado de 300.000) |

**Lo que NO se presupuesta, y se dice:** la **lectura de caché**. Queda fuera del cálculo de horas por
definición (`CALIBRATION.md`: mide longitud de sesión, no trabajo), pero se factura a 0,46 €/M y en
las 5 iniciativas medidas fue **la mayor parte de los 12,35 €**. Es decir: los **10,49 €** de tokens
de esta evaluación son una **cota inferior** del gasto real en API, y así hay que leerlos.

---

## Las lecciones de calibración de este repo, APLICADAS

El análisis dice que las seis lecciones de estimación son «las que más deberían pesar en cada
`/pm-cycle`» y están entre las que nadie cita. Aquí se citan y se aplican, con el efecto que tuvieron
en la cifra.

| Lección medida | Efecto en ESTA estimación |
|---|---|
| **La prosa pura se estima en minutos, no en horas** (`LES-004`; desviaciones de −96 % a −77 % en las 5 muestras) | C-06 y la parte de doc de las demás llevan **horas IA en centésimas** (0,30 h para toda la Fase 6), no horas. Las horas humanas de esas partes son las que quedan |
| **Una tarea con tests reales cuesta ~×2 respecto a una de prosa** (`LES-005`; `subagent-personas` fue la única con TDD real: 65.711 tokens, más que las de prosa y aun así por debajo de lo estimado) | C-01 (script + FTS5 + ~25 tests) sale a **245k tokens**, ~4× la muestra de TDD real; C-03 y C-05, mixtas, a 128k y 115k |
| **La revisión de dos lentes va como línea de presupuesto aparte** (`LES-001`, `LES-009`; en las 4 vías rápidas encontró 1-10 hallazgos, dos de ellos habrían roto una garantía del producto) | Línea propia: **4 h humanas · 0,54 h IA · 260k tokens · 202 €**, el **12 %** del presupuesto base. No está repartida por fases fingiendo que es gratis |
| **Una spec previa reduce el coste de implementación de forma medible** (`LES-006`; `quick-implement`, −77 %, la única muestra con la spec ya escrita) | **Esta iniciativa la tiene**: `spec.md` con 25 criterios de aceptación y las dos decisiones de diseño cerradas por el usuario. Por eso las horas IA no llevan el colchón de exploración que llevarían sin spec — y por eso el descuento se declara respaldado por **una** muestra, no por cinco |
| **El default de 300.000 tok/h subestima el ritmo real ~1,6×** (`CALIBRATION.md` aprendizaje 1) | Se usa la **mediana medida, 479.326**. Con el default las mismas 1.248.000 tokens darían 4,16 h IA en vez de 2,60 h: la diferencia es de **1,56 h**, y saldría directa al worklog de Jira |
| **Estimar por analogía con «iniciativas con código» infla las de prosa** (`CALIBRATION.md` aprendizaje 5) | Las 6 características se clasifican en los **tres tamaños** de esa lección: código de producto (C-01, C-04), mixto (C-02, C-03, C-05) y prosa + disparador (C-06) |

---

## Evaluación por característica

### C-01 — Recuperación: `knowledge-find.py`, índice FTS5 y lint del índice

- **Requisito origen**: `analysis.md` §3 R1 + R3; huecos §1.4-2 («no hay búsqueda») y §1.4-5 («el
  índice no lo vigila nada»).
- **Descripción**: las tres capas deterministas (aciertos compactos → grafo curado → entrada
  completa), el índice SQLite FTS5 en `.claude/` reconstruible con degradación a recorrido plano, y
  el test de biyección `ficheros ↔ filas` + `area` obligatoria. Es lo que convierte «lee el índice y
  decide» en «pregunta y recibe».
- **Complejidad**: Alta (tres modos de salida, tres estados del índice, dos caminos de degradación).
- **Esfuerzo**: **9 h** · confianza **Baja** (horas humanas: sin muestra validada).
- **Previsión IA**: 190.000 in / 55.000 out tok · **2,14 €** · 0,51 h IA.
- **Coste**: (9 h × 50 €/h) + 2,14 € = **452 €**.
- **Impacto / áreas afectadas**: `agent-kits/shared/knowledge-find.py` (nuevo),
  `tests/test_knowledge_find.py` (nuevo), `tests/test_knowledge_index.py` (nuevo), `.gitignore`,
  `docs/knowledge/README.md` (fila del ADR nuevo).
- **Dependencias y prerequisitos**: ninguna. **Es la única característica que no depende de nada, y
  por eso va primera.**
- **Riesgos**: FTS5 ausente en el `sqlite3` del consumidor (mitigado por diseño: CA-06); el
  enrutado por área es texto libre de **alta cardinalidad** (medido hoy: 21 áreas para 31 entradas,
  casi todas singleton), así que la relevancia puede decepcionar en las áreas de una sola entrada.
- **Incógnitas / preguntas abiertas**: cuánto ahorra de verdad frente a leer el índice de 3.685
  tokens. Se puede medir al terminar; **no se promete aquí**.

### C-02 — Llegada: inyección presupuestada en el brief y al arrancar

- **Requisito origen**: `analysis.md` §3 R2; hueco §1.4-1, declarado **el más caro**.
- **Descripción**: `task-brief.py` gana una sección con los aciertos del área y el tipo de la tarea
  (el enrutado ya existe: el campo `- **Tipo**:` del ledger), con tope de 600 tokens frente a los
  1.818 que mide el brief hoy; `session-context.sh` gana los N mejores aciertos del área de la
  iniciativa activa, con tope de 300 tokens dentro del `TOPE_CHARS = 9500` del hook.
- **Complejidad**: Media (dos puntos de inyección, dos topes, degradación silenciosa en ambos).
- **Esfuerzo**: **4 h** · confianza Baja.
- **Previsión IA**: 120.000 in / 30.000 out tok · **1,24 €** · 0,31 h IA.
- **Coste**: (4 h × 50) + 1,24 € = **201 €**.
- **Impacto / áreas afectadas**: `agent-kits/shared/task-brief.py`, `hooks/session-context.sh`,
  `agent-kits/shared/knowledge-check.md`, `agent-kits/shared/test_task_brief.py`,
  `tests/test_hooks_shell.py`.
- **Dependencias y prerequisitos**: **requiere C-01** (no hay nada que inyectar sin la capa 1).
- **Riesgos**: que la inyección desplace contexto útil del brief. Mitigación: el tope es una
  constante con test, no una intención; y la degradación deja el brief **idéntico** a hoy cuando no
  hay aciertos (CA-09).
- **Incógnitas / preguntas abiertas**: cuántos aciertos son «los N mejores» al arrancar. La spec fija
  el tope en tokens y deja N a la implementación, que es el orden correcto.

### C-03 — Prueba de que el camino se recorre

- **Requisito origen**: `analysis.md` §2 «lo que hacen mejor» (a) y (b) — la recuperación es una
  herramienta, no una intención.
- **Descripción**: `tests/test_memory_path.py` (gate determinista, sin tokens, **con mutante**),
  casos en `evals/` sobre `agent:implementer` y `agent:evaluator`, y `/doctor` puntuando la salud de
  la memoria — hoy da «Instalación sana» con 0 entradas de journal, sin contar las 31 curadas, sin
  validar el índice y sin avisar de que `CALIBRATION.md` lleva 15 días sin fila.
- **Complejidad**: Media.
- **Esfuerzo**: **4 h** · confianza **Media** (es la única característica cuyo trabajo son tests y
  un veredicto, los dos con precedente directo en el repo: `test_roadmap_index.py`, `test_doctor.py`).
- **Previsión IA**: 100.000 in / 28.000 out tok · **1,10 €** · 0,27 h IA.
- **Coste**: (4 h × 50) + 1,10 € = **201 €**.
- **Impacto / áreas afectadas**: `tests/test_memory_path.py` (nuevo), `evals/cases/agent-implementer.json`,
  `evals/cases/agent-evaluator.json`, `agent-kits/shared/doctor.py`, `agent-kits/shared/test_doctor.py`.
- **Dependencias y prerequisitos**: **requiere C-01 y C-02** (no se puede probar un camino que no existe).
- **Riesgos**: que la eval de activación sea **frágil** — depende de un modelo y cuesta tokens
  reales. Mitigación explícita: el **gate** es el test determinista; la eval es la comprobación de
  comportamiento y vive donde ya viven las caras (`run.py` local / `headless.yml`).
- **Incógnitas / preguntas abiertas**: ninguna material. El formato de caso de `evals/` está fijado
  por `check.py` y hay 38 ficheros de precedente.

### C-04 — Captura episódica automática

- **Requisito origen**: `analysis.md` §3 R5 (rama «reforzarlo», la que eligió el usuario) + §2 (c) y
  (d); hueco §1.4-3.
- **Descripción**: hook `UserPromptSubmit` que acumula el turno del usuario en un log crudo **no
  versionado** en `.claude/` con opt-out `<private>`; `SessionEnd` que **escribe él mismo** la entrada
  del journal con `decisiones` y `pendientes`; extracción por IA **opt-in** (`sesion.resumen: true`,
  `claude -p` como en `evals/run.py`) que degrada al journal determinista de hoy; y la **promoción**
  journal → candidata a lección por la puerta de `/retro` con `estado: propuesta`.
- **Complejidad**: **Alta** (dos hooks, un contrato oficial sin verificar, una llamada externa
  opcional que no puede bloquear el cierre de sesión, y privacidad).
- **Esfuerzo**: **7 h** · confianza **Baja**.
- **Previsión IA**: 160.000 in / 45.000 out tok · **1,77 €** · 0,43 h IA.
- **Coste**: (7 h × 50) + 1,77 € = **352 €**.
- **Impacto / áreas afectadas**: `hooks/user-prompt-capture.sh` (nuevo), `hooks/hooks.json`,
  `hooks/session-journal.sh`, `agent-kits/shared/journal.py`, `agent-kits/shared/test_journal.py`,
  `commands/retro.md`, `docs/knowledge/adr/ADR-010…` (revisión).
- **Dependencias y prerequisitos**: **verificar el contrato de `UserPromptSubmit`** antes de
  arrancar. No depende de C-01/C-02/C-03 técnicamente, pero va **después** por coste/impacto: es la
  más cara y la menos cierta, y la recuperación rinde antes.
- **Riesgos**:
  - **Privacidad** (repo público): el log crudo lleva texto del usuario. Mitigación: no versionado
    (`*.log` ya en `.gitignore`, verificado), opt-out por etiqueta, y con el opt-out puesto **el log
    no se toca**.
  - **Bloquear el cierre de sesión** con la llamada headless. Mitigación: opt-in + degradación en
    cualquier fallo + exit 0 siempre; y el test la corre con el subprocess **mockeado**.
  - **Reabrir `ADR-010` mal**: su restricción es cierta y hay que **conservarla**; lo que se revisa
    es la conclusión. CA-20 lo fija.
- **Incógnitas / preguntas abiertas**: si llega `session_id` en el payload; el umbral exacto de
  «patrón repetido»; y —dicho con honestidad— **por qué el journal está a 0 es inferencia, no
  medición** (`analysis.md` §5), así que esta característica cierra un hueco medido
  (`decisiones: []` siempre) sobre una causa supuesta.

### C-05 — Que la doctrina viaje con el plugin

- **Requisito origen**: `analysis.md` §3 R4; hueco §1.4-4 («viaja el método y se queda el conocimiento»).
- **Descripción**: separar **doctrina del plugin** (las lecciones ciertas para cualquier proyecto:
  las 9 de área «Estimación / calibración», `LES-001…009`) de la **memoria del proyecto** (que sigue
  naciendo vacía, y eso es correcto). Las primeras viajan como assets del plugin y son el fondo con
  el que el `evaluator` estima el primer día. Hay que **deshacer una pérdida real**: `LES-007/008/009`
  estaban garantizadas dentro del prompt del `evaluator` y se convirtieron en punteros a ficheros que
  el consumidor no tiene — **sin volver a meter prosa en los prompts** (CA-22 lo ata a `wc -c`).
- **Complejidad**: Media (la restricción de «no engordar el prompt» es la parte difícil).
- **Esfuerzo**: **3 h** · confianza Media.
- **Previsión IA**: 90.000 in / 25.000 out tok · **0,99 €** · 0,24 h IA.
- **Coste**: (3 h × 50) + 0,99 € = **151 €**.
- **Impacto / áreas afectadas**: `agent-kits/evaluator/` (assets de doctrina),
  `agent-kits/shared/knowledge-find.py` (`--doctrina`), `agents/evaluator.md` (sin crecer),
  `scripts/export-skills.py` (qué viaja en el paquete portable).
- **Dependencias y prerequisitos**: **requiere C-01** (`--doctrina` es una bandera de la capa 1).
- **Riesgos**: duplicar las 9 lecciones (assets del plugin **y** `docs/knowledge/` de este repo) y
  que se desincronicen. Mitigación: una sola copia y el lint que ya vigila las copias manuales del
  repo; si no se puede evitar la copia, un test que compare las dos.
- **Incógnitas / preguntas abiertas**: si las 9 de esa área son **todas** doctrina universal o
  alguna es específica de este repo. Se decide entrada por entrada al implementar; el criterio está
  escrito (¿es cierta para cualquier proyecto que use estos agentes?).

### C-06 — Cerrar el bucle: `/retro` disparado, doc y entradas de memoria

- **Requisito origen**: `analysis.md` §3, «Y una condición previa para todo lo demás».
- **Descripción**: que `/retro` se dispare al **cerrar** una iniciativa en vez de depender de que
  alguien se acuerde (hoy: **15 días parado, 13 iniciativas cerradas después** de la última fila de
  `CALIBRATION.md`), más doc ES/EN y las entradas de `docs/knowledge/` que salgan de aquí.
- **Complejidad**: **Baja** en construcción — es un disparador y prosa.
- **Esfuerzo**: **3 h** · confianza Media.
- **Previsión IA**: 110.000 in / 35.000 out tok · **1,31 €** · 0,30 h IA (prosa: **minutos**, `LES-004`).
- **Coste**: (3 h × 50) + 1,31 € = **151 €**.
- **Impacto / áreas afectadas**: `commands/retro.md`, `commands/dev-cycle.md` (cierre de iniciativa),
  `docs/CONVENTIONS.md` + `docs/en/CONVENTIONS.md`, `docs/knowledge/` (ADR + lección + fila del índice).
- **Dependencias y prerequisitos**: la promoción de **C-04** (candidatas a lección) y la salud de
  **C-03** (el aviso de `CALIBRATION.md` desfasado).
- **Riesgos**: **el riesgo de esta característica es que se caiga del alcance por ir última.** Es
  barata y es la condición previa de que todo lo demás sirva de algo: **una entrega que se pare en
  C-05 está incompleta, no «al 83 %»**.
- **Incógnitas / preguntas abiertas**: si el disparador debe **ejecutar** `/retro` o solo exigirlo en
  la puerta de cierre. Recomendación: exigirlo en la puerta (bloquea el cierre), que es el patrón que
  el repo ya usa con `qa-gate` y `ledger-lint`.

---

## Comparativa

Ordenada por **coste/impacto**, que es el orden en el que se recomienda ejecutar.

| # | Característica | Complejidad | Horas | Coste € | Tokens | Prioridad | Confianza |
|---|---------------|-------------|-------|---------|--------|-----------|-----------|
| C-01 | Recuperación (3 capas + FTS5 + lint del índice) | Alta | 9 h | 452 € | 245k | **Crítica** | Baja |
| C-02 | Llegada (brief + arranque, presupuestada) | Media | 4 h | 201 € | 150k | **Crítica** | Baja |
| C-03 | Prueba de que se recorre (+ `/doctor`) | Media | 4 h | 201 € | 128k | Alta | **Media** |
| C-04 | Captura episódica automática | Alta | 7 h | 352 € | 205k | Media | **Baja** |
| C-05 | Que la doctrina viaje | Media | 3 h | 151 € | 115k | Alta | Media |
| C-06 | Cerrar el bucle (`/retro` disparado) | Baja | 3 h | 151 € | 145k | **Crítica** | Media |
| — | **Revisión de dos lentes** (transversal, línea propia — `LES-001`/`LES-009`) | — | 4 h | 202 € | 260k | — | Media |
| | **Total** | | **34 h** (base) | **1.710 €** (base) | **1.248k** | | |

> La fila de la revisión **no es una característica**: es la línea de presupuesto que
> `CALIBRATION.md` obliga a poner aparte porque es «donde se va el trabajo real». Son el **12 %** del
> presupuesto base y el **21 %** de los tokens.

---

## Presupuesto total

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 34 h × 50 €/h | 1.700,00 € |
| Margen de contingencia | +20 % sobre desarrollo base | 340,00 € |
| Tokens IA (input) | 990.000 tok × 4,60 €/1M | 4,55 € |
| Tokens IA (output) | 258.000 tok × 23,00 €/1M | 5,93 € |
| **Total estimado (con margen)** | | **2.050,49 €** |

- Las sumas por característica dan 10,48 € de tokens y el cálculo agregado 10,49 €: es **redondeo por
  línea**, no un descuadre.
- **Lectura de caché no presupuestada** (ver §Supuestos): los 10,49 € son cota **inferior**.
- El margen del 20 % se aplica sobre las **horas** base (humanas e IA), como manda `rates.json`; los
  tokens van sin margen y se declara.

---

## Productividad IA (humano vs. IA)

| KPI | Valor |
|-----|-------|
| Horas humanas estimadas | **40,8 h** (34 h base +20 %) |
| Horas IA (ejecución) | **3,13 h** (2,60 h base +20 %) |
| Supervisión humana | **0,79 h** (0,66 h base +20 %) |
| **Horas totales (IA + supervisión)** | **3,92 h** |
| Horas ahorradas | 36,88 h |
| **Ahorro** | **90,4 %** |
| **Multiplicador de productividad** | **×10,4** |
| FTE equivalentes | 0,23 |

> Horas mostradas **con el margen de contingencia (+20 %)** ya aplicado sobre las horas base.
> La supervisión base sale del 25 % de las horas IA (0,65 h); la **suma por tarea** del ledger da
> 0,66 h por redondeo, y se usa 0,66 h para que plan y ledger digan lo mismo.

**Lo que este multiplicador NO dice** (`CALIBRATION.md` aprendizaje 2, y `LES-007` «separa lo que
mides de lo que vendes»): las 40,8 h humanas **no están validadas por ninguna muestra** — las 5 filas
medidas tienen 0 h humanas reales porque el trabajo lo hizo la IA con supervisión conversacional. El
×10,4 es la comparación entre una **estimación** (humano) y otra **estimación anclada en medición**
(IA). No es un plazo que se pueda prometer a un cliente.

---

## Recomendación

- **Veredicto**: **go.** Tres razones, con la evidencia al lado:
  1. **El activo ya está pagado y no se está usando.** 31 entradas, 108.443 caracteres, y **17 (55 %)
     que ninguna pieza cita** — y son exactamente las más antiguas, incluidas las 6 lecciones de
     estimación que más deberían pesar. La inversión de curación existe; falta la tubería de salida.
  2. **El hueco más caro es una puerta cerrada, no una omisión.** Con `subagentes: true` el brief es
     el único contexto y no lleva memoria: quien escribe el código **no puede** alcanzar un gotcha ni
     queriendo. C-01 + C-02 son **13 h y 653 €**, el 38 % del presupuesto base, y cierran eso.
  3. **La alternativa (adoptar `claude-mem`) está descartada con motivo**: pediría Node ≥ 20, Bun, uv
     y un worker HTTP, y cambiaría un corpus auditable en un PR por un SQLite que **es** el almacén.
     Aquí se copia su capa de recuperación con **cero dependencias nuevas**.
- **Quick wins** (bajo coste, alto valor): **C-06** (3 h, 151 €, y es la condición previa de todo lo
  demás) y **C-05** (3 h, 151 €, deshace una pérdida real de garantía del producto).
- **Costosas / a valorar**: **C-04** (7 h, 352 €) — la más cara, la de peor confianza y la única con
  un contrato oficial sin verificar. Es la candidata natural a recortar si hay que recortar: **cortar
  C-04 dejaría las Fases 1-3, 5 y 6 en pie** (27 h base, 1.358 € base) y solo perdería la captura de
  lo nuevo, no la recuperación de lo que ya hay.
- **Orden sugerido**: **C-01 → C-02 → C-03 → C-04 → C-05 → C-06** — por dependencias
  (C-02 necesita C-01; C-03 necesita C-01+C-02; C-05 necesita C-01; C-06 necesita C-03+C-04) y por
  coste/impacto (la recuperación rinde antes que la captura). **Salvedad importante:** C-06 va última
  por dependencias pero **el criterio de éxito no se cumple sin ella** — no es opcional.
- **Fuera de alcance recomendado**: embeddings y vector store (con 31 entradas un grep ordenado
  gana), captura de cada `PostToolUse` (ruido y coste), y sync entre máquinas. Los tres están en el
  §Alcance «Fuera» de la spec con su motivo.

---

## Riesgos transversales

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| **Las horas humanas no tienen ninguna muestra validada** (`CALIBRATION.md` aprendizaje 2) | **Alta** | Alto (es el 99,5 % del coste) | Declarar la confianza como **Baja** y no vender el ×10,4 como plazo. Cerrar la iniciativa con `/retro` y meter la **primera fila con horas humanas reales** en `CALIBRATION.md` — que es justamente lo que C-06 desatasca |
| Que la inyección de memoria desplace contexto útil (brief y arranque) | Media | Medio | Topes **numéricos** con test por camino (600 / 300 tokens), no intenciones; degradación que deja la salida idéntica a hoy |
| Índice corrupto o FTS5 ausente en la máquina del consumidor | Media | Bajo | El índice es **caché**: reconstrucción por hash y recorrido plano; nunca exit ≠ 0 por el índice (CA-06) |
| Contrato de `UserPromptSubmit` distinto de lo supuesto | Media | Medio | Verificar en la doc oficial **antes** de la Fase 4 y anotar la fecha (patrón de `memory-health`); plan B escrito (log por fecha + casar por mtime) |
| Privacidad en un repo público (el log crudo lleva texto del usuario) | Baja | **Alto** | Log **no versionado** (`*.log` ya en `.gitignore`, verificado con `git check-ignore`), opt-out por etiqueta, y con el opt-out puesto el log **no se toca**. Ningún dato corporativo en tests ni en evals (`check.py` lo vigila) |
| Que C-06 se caiga del alcance por ir última | **Media** | **Alto** | Escrito como criterio de aceptación (CA-25) y repetido en el plan: parar en C-05 es entrega **incompleta** |
| Que la eval de activación sea frágil (modelo + tokens reales) | Media | Bajo | El **gate** es el test determinista; la eval vive donde ya viven las caras (`run.py` local / `headless.yml`) |
| Que la suite baje de 1.175 tests | Baja | Alto | `python3 -m pytest -q` en la puerta de cada fase; la línea base está escrita en la spec y en el ledger |

---

## Siguiente paso

Plan detallado en [`improvement-plan.md`](improvement-plan.md) y ledger canónico en
[`tasks.md`](tasks.md), con las **6 características aprobadas** en el orden C-01 → C-06 y la
**revisión de dos lentes como línea propia** en cada fase. El `planner` **hereda** estas horas y
costes por característica — no re-estima desde cero — y así lo declara su §Estimación por fase.
