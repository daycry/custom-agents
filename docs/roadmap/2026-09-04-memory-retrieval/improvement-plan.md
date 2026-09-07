---
design: n/a               # sin paso de diseño del agente architect: las dos decisiones que cambiaban el plan las cerró el usuario
generacion:            # ventana compartida con spec.md · evaluation.md · tasks.md (se cuenta UNA vez)
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

> Seis fases en orden de coste/impacto y dependencias: primero la recuperación que falta, luego que
> llegue a quien trabaja, luego la prueba de que se recorre, y solo entonces capturar más.

| | |
|---|---|
| **Fecha** | 2026-09-04 |
| **Estado** | borrador |
| **Tipo** | Nueva Funcionalidad |
| **Prioridad** | Alta |
| **Solicitante** | usuario (petición del 2026-09-04, tras publicar v1.16.0) |
| **Responsable** | `planner` (plan) → `implementer` (ejecución) |
| **Spec** | [`spec.md`](spec.md) |
| **Evaluación** | [`evaluation.md`](evaluation.md) |
| **Diseño** | n/a (sin paso de diseño) |
| **Análisis de origen** | [`analysis.md`](analysis.md) |

---

## Cuadro de mando

| Métrica | Estimado | Real | Confianza |
|--------|---------|------|-----------|
| Tiempo humano | **40,8 h** (34 h base +20 %) | 0 h | **Baja** |
| Tiempo IA (ejecución) | **3,13 h** (+ 0,79 h supervisión) | 0 h | Media |
| Coste total | **2.050 €** | 0 € | **Baja** |
| Tokens IA | **1.248.000** (in 990.000 / out 258.000) | 0 | Media |
| Multiplicador productividad | **×10,4** | — | — |
| Tareas | **18** | 0 hechas | — |

> **Confianza, sin adornar.** Las horas **humanas** son las que no bajan y **ninguna muestra las ha
> validado** (`CALIBRATION.md` aprendizaje 2: las 5 filas medidas tienen 0 h humanas reales), y son
> el 99,5 % del coste — de ahí que coste y horas humanas sean **Baja**. Las horas **IA** salen de
> tokens estimados ÷ **479.326 tok/h** (mediana medida de 5 muestras), y esas 5 muestras
> sobrestimaron el coste de IA por un **orden de magnitud**: la cifra de IA es la mejor anclada de
> este documento, pero ninguna de las 5 llevaba SQLite ni dos hooks nuevos, así que **Media**.

---

## Estimación por fase

Horas = **humanas base** (sin el margen del 20 %), heredadas de la evaluación por característica.
La **revisión de dos lentes va como línea propia** (`LES-001`, `LES-009`): es donde se va el trabajo
real, y repartirla por fases fingiría que es gratis.

| Fase | Estimado (h) | Tokens (in / out) | Coste € |
|------|-------------|-------------------|---------|
| Fase 1 — Recuperación (C-01) | 9,0 | 190k / 55k | 452 |
| Fase 2 — Llegada (C-02) | 4,0 | 120k / 30k | 201 |
| Fase 3 — Prueba de que se recorre (C-03) | 4,0 | 100k / 28k | 201 |
| Fase 4 — Captura episódica (C-04) | 7,0 | 160k / 45k | 352 |
| Fase 5 — Que la doctrina viaje (C-05) | 3,0 | 90k / 25k | 151 |
| Fase 6 — Cerrar el bucle (C-06) | 3,0 | 110k / 35k | 151 |
| Revisión de dos lentes (transversal) | 4,0 | 220k / 40k | 202 |
| **Total** | **34,0 h** | **990k / 258k** | **1.710 €** (base) |

---

## Presupuesto económico

**Coste = (horas × tarifa) + coste de tokens de IA.** Todos los importes en **EUR**.

### Supuestos (ajustables)

Todos de `.claude/rates.json` y `docs/roadmap/CALIBRATION.md`. **Ninguno inventado.**

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | **50 €/h** | `rates.json` `tarifaHora` |
| Modelo IA asumido | **claude-opus-4-8** | `rates.json` `modeloIA` |
| Precio input | **4,60 €** / 1M tokens | 5 USD/M × 0,92 · verificado 2026-08-18 (18 días ⇒ fiable) |
| Precio output | **23,00 €** / 1M tokens | 25 USD/M × 0,92 · verificado 2026-08-18 |
| Precio creación / lectura de caché | **5,75 €** / **0,46 €** por 1M | 6,25 y 0,50 USD/M × 0,92 |
| Tipo de cambio | 1 USD = **0,92 €** | **SUPUESTO fijo, no verificado** — revisar antes de facturar |
| Ratio de supervisión | **25 %** de las horas IA | `rates.json` `ratioSupervision` |
| Margen de contingencia | **20 %** | sobre horas base (humanas e IA) |
| Jornada / FTE | **8 h** / **160 h** | `rates.json` |
| Ratio tokens → hora IA | **479.326 tok/h** | `CALIBRATION.md`, mediana de **5 muestras medidas** (no el default 300.000) |

### Desglose

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 34 h × 50 €/h | 1.700,00 € |
| Margen de contingencia | +20 % sobre desarrollo base | 340,00 € |
| Tokens IA (input) | 990.000 tok × 4,60 €/1M | 4,55 € |
| Tokens IA (output) | 258.000 tok × 23,00 €/1M | 5,93 € |
| **Total estimado (con margen)** | | **2.050,49 €** |

**Lectura de caché: no presupuestada, y se dice.** Queda fuera del cálculo de horas por definición
(`CALIBRATION.md`: mide longitud de sesión, no trabajo) pero se factura a 0,46 €/M, y en las 5
iniciativas medidas fue **la mayor parte de los 12,35 €** totales. Los 10,49 € de tokens de este plan
son una **cota inferior** del gasto real en API.

---

## Previsión de tokens (por fase)

Base: **claude-opus-4-8** · precios de la tabla de supuestos.

| Fase | Input (tok) | Output (tok) | Total (tok) | Coste € |
|------|------------|-------------|-------------|---------|
| Fase 1 — Recuperación | 190.000 | 55.000 | 245.000 | 2,14 |
| Fase 2 — Llegada | 120.000 | 30.000 | 150.000 | 1,24 |
| Fase 3 — Prueba de que se recorre | 100.000 | 28.000 | 128.000 | 1,10 |
| Fase 4 — Captura episódica | 160.000 | 45.000 | 205.000 | 1,77 |
| Fase 5 — Que la doctrina viaje | 90.000 | 25.000 | 115.000 | 0,99 |
| Fase 6 — Cerrar el bucle | 110.000 | 35.000 | 145.000 | 1,31 |
| Revisión de dos lentes (transversal) | 220.000 | 40.000 | 260.000 | 1,93 |
| **Total** | **990.000** | **258.000** | **1.248.000** | **10,49 €** |

**Método de estimación (con los anclajes medidos, no a ojo):**

1. **Anclaje.** La única muestra medida con **TDD real** de este repo es `subagent-personas`:
   **65.711 tokens facturables** para un script pequeño + 6 tests. La Fase 1 (un script con tres
   modos de salida, índice FTS5 con tres estados, dos caminos de degradación y ~25 tests) se estima
   ≈ 4× esa muestra → 245k.
2. **Regla de los tres tamaños** (`CALIBRATION.md` aprendizaje 5): prosa = minutos · prosa + tests =
   ×2 · código de producto = horas. Fases 1 y 4 son código de producto; 2, 3 y 5 mixtas; 6 es prosa
   + un disparador.
3. **Descuento por spec previa** (`LES-006`, medido: −77 % en la única muestra que tenía la spec
   escrita): esta iniciativa **tiene** spec con 25 criterios y las dos decisiones cerradas, así que
   no se presupuesta colchón de exploración. Respaldado por **una** muestra, y se declara.
4. **Revisión aparte** (`LES-001`, `LES-009`): 260k tokens, el **21 %** del total, porque en las 4
   vías rápidas medidas la revisión encontró 1-10 hallazgos cada vez y dos habrían roto una garantía
   del producto.
5. **Conversión a horas:** tokens facturables ÷ **479.326** = 2,60 h base. Con el default no
   calibrado (300.000) darían **4,16 h**: 1,56 h de diferencia que irían directas al worklog de Jira.
6. **La creación de caché va dentro del `input`** de esta previsión y la **lectura de caché no se
   prevé** (ver arriba). No es un olvido: es el criterio de `CALIBRATION.md` y hace que el € sea una
   cota inferior.

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

> Horas **con el margen (+20 %)** ya aplicado sobre las horas base. La supervisión base es el 25 % de
> las horas IA (0,65 h); la suma por tarea del ledger da **0,66 h** por redondeo, y se usa 0,66 h
> para que plan y ledger digan lo mismo.
>
> **Lo que el ×10,4 no dice** (`LES-007`, «separa lo que mides de lo que vendes»): compara una
> **estimación** humana sin ninguna muestra validada con una **estimación anclada en medición** de
> IA. No es un plazo prometible.

---

## Resumen ejecutivo

El plugin escribe memoria bien y la recupera mal: 31 entradas curadas (27.100 tokens), **17 (55 %)
que ninguna pieza ejecutable cita**, **0** tokens de memoria inyectados al arrancar y **0** entradas
de journal. Este plan construye la capa que falta en seis fases: la **recuperación** determinista
(tres capas sobre un índice FTS5 que es caché reconstruible, no almacén), su **llegada
presupuestada** a los dos caminos por los que un agente recibe contexto, la **prueba** de que ese
camino se recorre, la **captura episódica** de lo que hoy se pierde, que la **doctrina viaje** con el
plugin y el **cierre del bucle** `/retro`. Cero dependencias nuevas: `sqlite3` es stdlib.

### Objetivos

- **Recuperación medible:** una consulta por área devuelve sus aciertos en **≤ 300 tokens** frente a
  los **3.685** que cuesta hoy leer el índice de entrada — y **≤ 30 tokens por acierto**.
- **La puerta cerrada, abierta:** el brief del subagente pasa de **0** tokens de memoria a **≤ 600**,
  sobre una línea base de 1.818 tokens de brief, con test que afirma el tope.
- **El arranque, con memoria:** de **0** de 872 tokens a **≤ 300** tokens del área activa, dentro del
  `TOPE_CHARS = 9500` del hook.
- **Garantía en vez de intención:** un test determinista que se pone **rojo** si el camino de memoria
  no se recorre, más casos en `evals/`. Esto no lo tiene nadie, ni nosotros ni `claude-mem`.
- **Journal que captura decisiones:** de `decisiones: []` **siempre** a `decisiones`/`pendientes`
  escritas por el propio hook, con opt-out de privacidad y degradación que nunca bloquea.
- **La doctrina viaja:** las 9 lecciones de estimación disponibles en un proyecto recién instalado,
  **sin engordar el prompt del `evaluator`** (`wc -c` ≤ 15.513 bytes de hoy).
- **El bucle cerrado:** `/retro` disparado al cerrar iniciativa, en vez de 15 días parado con 13
  iniciativas cerradas detrás.
- **Nada baja:** `python3 -m pytest -q` sigue en **≥ 1.175 passed**; `lint_plugin.py` y
  `evals/check.py` siguen en exit 0.

---

## Datos necesarios para un informe completo

- [x] **Requisitos funcionales** confirmados por el solicitante (las dos decisiones de diseño, 2026-09-04)
- [x] **Alcance** cerrado (§Alcance de la spec, con «Fuera» y su motivo)
- [x] **Criterios de éxito / métricas** acordados (25 criterios, 19 `[GWT]`, con tope numérico y línea base)
- [x] **Accesos y credenciales** — ninguno: todo local, ningún test con red
- [x] **Entornos** — este repo; los tests nuevos usan `tmp_path`, no el corpus real
- [x] **Stakeholders** — el usuario, en la puerta de control de cada fase
- [x] **Dependencias externas** mapeadas — **ninguna nueva** (decisión de diseño 2)
- [x] **Restricciones** — repo público, solo stdlib, degradación que nunca bloquea, ES/EN donde aplique
- [x] **Tarifa/hora y supuestos de coste** confirmados (`.claude/rates.json`)
- [ ] **Contrato oficial de `UserPromptSubmit`** verificado y fechado — **bloquea la Fase 4**, no las
      Fases 1-3

---

## Análisis de impacto

- **`agent-kits/shared/knowledge-find.py`** (nuevo) — las tres capas, el índice FTS5 y las dos
  degradaciones. Es la pieza central: todo lo demás la consume.
- **`agent-kits/shared/task-brief.py`** — sección nueva de memoria técnica, enrutada por
  `- **Tipo**:`, con tope propio. **No** se toca ninguna de sus 10 secciones actuales.
- **`hooks/session-context.sh`** — bloque (4) tras índice de piezas, roadmap y journal; recorte final
  a `TOPE_CHARS` intacto.
- **`hooks/user-prompt-capture.sh`** (nuevo) + **`hooks/hooks.json`** — captura del turno con opt-out.
- **`agent-kits/shared/journal.py`** y **`hooks/session-journal.sh`** — `decisiones`/`pendientes`
  desde el log crudo, resumen opt-in, promoción a candidata.
- **`agent-kits/shared/knowledge-check.md`** — el reparto por agente deja de ser solo prosa: cada
  fila nombra su comando. **El fragmento sigue siendo la fuente única**; no se duplica en prompts.
- **`agent-kits/shared/doctor.py`** — salud de la memoria en el veredicto.
- **`agent-kits/evaluator/`** — assets de doctrina (`LES-001…009`) que viajan con el plugin.
- **`commands/retro.md`**, **`commands/dev-cycle.md`** — disparador de `/retro` al cerrar iniciativa.
- **`tests/`** — `test_knowledge_find.py`, `test_knowledge_index.py`, `test_memory_path.py` (nuevos)
  + `test_hooks_shell.py`, `agent-kits/shared/test_task_brief.py`, `test_journal.py`, `test_doctor.py`.
- **`evals/cases/agent-implementer.json`**, **`agent-evaluator.json`** — casos del camino de memoria.
- **`docs/knowledge/`** — ADR de las tres capas, revisión de `ADR-010`, lección, y las filas del índice.
- **`docs/CONVENTIONS.md`** + **`docs/en/CONVENTIONS.md`** — la regla nueva, en los dos idiomas.
- **`.gitignore`** — el índice FTS5 (`*.log` ya cubre el log crudo, verificado).
- **Lo que NO se toca:** el mecanismo de curación de `docs/knowledge/` (es el activo), `CHANGELOG*.md`
  (lo genera `changelog-sync` al cerrar) y ninguna de las 10 secciones actuales del brief.

---

## Cambios arquitectónicos

1. **La fuente de verdad sigue siendo el Markdown en git; el índice es CACHÉ.** Es la diferencia
   estructural con `claude-mem`, donde la base **es** el almacén: base corrupta = memoria perdida y
   nada revisable. Aquí, índice ausente/corrupto/con hash que no cuadra → se reconstruye; si no se
   puede → recorrido plano. **Nunca sale con código ≠ 0 por culpa del índice.**
2. **Cero dependencias nuevas.** `sqlite3` con FTS5 es stdlib. Sin embeddings, sin worker, sin Node.
3. **La recuperación pasa de intención a herramienta.** Hoy un aprendizaje solo llega si el modelo
   encadena **seis decisiones** (acordarse de la regla, resolver la ruta con `find`, leer el
   fragmento, leer 3.685 tokens de índice, juzgar la columna «Área» y abrir el fichero), ninguna
   verificada. Después: **una llamada con exit code**.
4. **El `estado` va DELANTE en cada acierto** (`aceptada` / `propuesta` / `obsoleta`), para que el
   lector sepa si tiene doctrina o indicio antes de leer el titular.
5. **Grafo curado en vez de cronología** en la 2.ª capa: sucesor/sustituido, misma iniciativa, misma
   área. Mismo coste de tokens que su `timeline`, mejor información.
6. **El enrutado por área normaliza, no compara cadenas.** Medido hoy: **21 áreas distintas para 31
   entradas**, texto libre con `/` y acentos, y casi todas singleton. Una comparación exacta no
   enrutaría nada.
7. **`ADR-010` se revisa, no se borra.** Su restricción —«el contrato de `SessionEnd` ignora la
   salida de los hooks»— es **cierta** y se conserva; lo que cambia es la conclusión: el hook no
   necesita *devolver* el resumen, **puede escribirlo**.
8. **Doctrina del plugin ≠ memoria del proyecto.** Las lecciones ciertas para cualquier proyecto
   viajan como assets; la memoria del consumidor sigue naciendo vacía. Se deshace la pérdida de
   `LES-007/008/009` **sin volver a meter prosa en los prompts**.
9. **Presupuesto explícito por camino.** Cada punto de inyección tiene una constante de tope y un
   test que la afirma. Un tope sin test es una intención.

---

## Archivos a crear/modificar

| Archivo | Acción | Propósito |
|---------|--------|-----------|
| `agent-kits/shared/knowledge-find.py` | Crear | Las tres capas + índice FTS5 + degradaciones |
| `tests/test_knowledge_find.py` | Crear | Formato, orden, topes, exit codes, tres estados del índice |
| `tests/test_knowledge_index.py` | Crear | Biyección `ficheros ↔ filas` + `area` obligatoria |
| `tests/test_memory_path.py` | Crear | El camino SE RECORRE (con su mutante) |
| `hooks/user-prompt-capture.sh` | Crear | `UserPromptSubmit`: log crudo + opt-out `<private>` |
| `agent-kits/evaluator/assets/doctrina/` | Crear | `LES-001…009` como doctrina que viaja con el plugin |
| `agent-kits/shared/task-brief.py` | Modificar | Sección de memoria técnica, ≤ 600 tokens, degradación silenciosa |
| `hooks/session-context.sh` | Modificar | Bloque de memoria del área activa, ≤ 300 tokens |
| `hooks/hooks.json` | Modificar | Registrar `UserPromptSubmit` |
| `hooks/session-journal.sh` | Modificar | Resumen opt-in (`claude -p`) con degradación |
| `agent-kits/shared/journal.py` | Modificar | `decisiones`/`pendientes` del log crudo + promoción |
| `agent-kits/shared/knowledge-check.md` | Modificar | El reparto por agente nombra su comando |
| `agent-kits/shared/doctor.py` | Modificar | Salud de la memoria en el veredicto |
| `commands/retro.md` | Modificar | Candidatas a lección desde el journal |
| `commands/dev-cycle.md` | Modificar | `/retro` exigido en la puerta de cierre de iniciativa |
| `agents/evaluator.md` | Modificar | Consumir la doctrina **sin crecer** (`wc -c` ≤ 15.513) |
| `docs/CONVENTIONS.md` · `docs/en/CONVENTIONS.md` | Modificar | La regla nueva, espejo ES/EN |
| `docs/knowledge/README.md` | Modificar | Filas de las entradas nuevas |
| `docs/knowledge/adr/`, `docs/knowledge/lessons/` | Crear | ADR de las tres capas, revisión de `ADR-010`, lección |
| `.gitignore` | Modificar | Índice FTS5 en `.claude/` |
| `evals/cases/agent-implementer.json` · `agent-evaluator.json` | Modificar | Casos del camino de memoria |
| `docs/roadmap/README.md` | Modificar | Fila de la iniciativa, **dentro** de la tabla |

---

## Dependencias y prerequisitos

- **Fase 1 no depende de nada.** Por eso va primera: es también la que más rinde.
- **Fase 2 requiere Fase 1** — no hay nada que inyectar sin la capa 1.
- **Fase 3 requiere Fases 1 y 2** — no se puede probar un camino que no existe.
- **Fase 4 requiere verificar el contrato oficial de `UserPromptSubmit`** (¿llega `session_id`?) en
  la doc oficial y **anotar la fecha**, como hizo `memory-health` con `SessionEnd`. Plan B escrito:
  nombrar el log por fecha y casar por mtime.
- **Fase 5 requiere Fase 1** (`--doctrina` es una bandera de la capa 1).
- **Fase 6 requiere Fases 3 y 4** (el aviso de `CALIBRATION.md` desfasado y la promoción de candidatas).
- **Ninguna fase requiere red, `claude` en el PATH ni una clave de API** para su verificación. El
  único camino que usa el CLI (`sesion.resumen`) se prueba con el subprocess **mockeado**.

---

## Criterios de aceptación (global)

Los 25 criterios detallados, con su tope y su línea base, están en
[`spec.md` §Criterios de aceptación](spec.md#criterios-de-aceptación). Aquí, los globales del plan:

- [ ] `python3 agent-kits/shared/ledger-lint.py docs/roadmap/2026-09-04-memory-retrieval/tasks.md`
  → **exit 0** (0 incoherencias) en cada puerta de fase.
- [ ] `python3 -m pytest -q` → **≥ 1.175 passed** (línea base de hoy) en cada puerta de fase.
- [ ] `python3 scripts/lint_plugin.py` → **exit 0** (hoy: 9 agentes · 0 errores · 3 avisos).
- [ ] `python3 evals/check.py` → **exit 0** (hoy: 38 ficheros · 133 casos · 0 errores).
- [ ] `python3 agent-kits/shared/scope-check.py docs/roadmap/2026-09-04-memory-retrieval` → **exit 0**
  antes de cada revisión de dos lentes (ningún fichero fuera del alcance declarado en el ledger).
- [ ] Cada punto de inyección tiene **tope numérico** y un test que lo afirma: brief ≤ 600 tokens,
  arranque ≤ 300 tokens, acierto compacto ≤ 30 tokens.
- [ ] **Ningún test nuevo** depende de la red, de `claude` en el PATH ni de una clave de API.
- [ ] La revisión de dos lentes se supera en **≤ 3 intentos** por fase, con la traza
  «Revisión de dos lentes — intento N» en el ledger.
- [ ] **La Fase 6 está hecha.** Parar en la Fase 5 es entrega **incompleta**, no «al 83 %»
  (spec CA-25): el análisis declara el bucle `/retro` **condición previa** de que lo demás sirva.

---

## Riesgos y mitigaciones

Uno por fase, con su **plan de degradación** — y la regla del repo: **la degradación nunca bloquea.**

| Riesgo | Probabilidad | Impacto | Mitigación / degradación |
|--------|-------------|---------|--------------------------|
| **F1** — `sqlite3` sin FTS5, `.claude/` de solo lectura o índice corrupto | Media | Bajo | **Degradación:** reconstruir por hash; si no se puede escribir, **recorrido plano** de los ficheros con los mismos aciertos y `indice: "degradado"`. **Exit 0 en los tres casos** (spec CA-06) |
| **F1** — relevancia pobre en áreas de una sola entrada (21 áreas para 31 entradas, medido) | Media | Medio | Normalizar el área en vez de comparar cadenas; `--limit` y orden por relevancia; el `--related` cubre el salto entre áreas vecinas |
| **F2** — la inyección desplaza contexto útil del brief | Media | Medio | **Degradación:** tope de 600 tokens como constante con test; sin aciertos o sin `docs/knowledge/`, la salida es **idéntica a la de hoy** (CA-09), sin aviso ni sección vacía |
| **F2** — el bloque de arranque revienta el tope del hook | Baja | Medio | **Degradación:** tope propio de 300 tokens **antes** del recorte a `TOPE_CHARS = 9500` que ya existe; si el hook falla por cualquier motivo, `exit 0` sin emitir (patrón actual del fichero) |
| **F3** — la eval de activación es frágil (modelo + tokens reales) | Media | Bajo | **Degradación:** el **gate** es `tests/test_memory_path.py`, determinista y sin tokens; la eval vive donde ya viven las caras (`run.py` local / `headless.yml`), y `run.py` ya sale **2** si `claude` no está en PATH |
| **F3** — `/doctor` se vuelve alarmista y la gente lo ignora | Baja | Medio | Los avisos de memoria van como **⚠️ con el arreglo concreto**, no como ❌; solo el índice inválido y el journal a 0 con memoria presente cambian el veredicto |
| **F4** — el contrato de `UserPromptSubmit` no es el supuesto | Media | Medio | **Verificar y fechar antes de arrancar la fase.** Plan B: log nombrado por fecha, `SessionEnd` casa por mtime |
| **F4** — privacidad en repo público (el log lleva texto del usuario) | Baja | **Alto** | Log **no versionado** (`*.log` ya en `.gitignore`, verificado con `git check-ignore`), opt-out `<private>` que **no toca el log**, y ni un dato corporativo en tests ni en evals (`check.py` lo vigila) |
| **F4** — la llamada headless bloquea el cierre de sesión | Media | **Alto** | **Degradación:** opt-in apagado por defecto; cualquier fallo (sin CLI, sin clave, timeout, JSON roto) cae al journal determinista de hoy; **exit 0 siempre** |
| **F5** — duplicar las 9 lecciones (assets + `docs/knowledge/`) y desincronizarlas | Media | Medio | Una sola copia; si la copia es inevitable, un test que compare las dos, como el que ya vigila las copias manuales del repo |
| **F5** — engordar el prompt del `evaluator` al deshacer la pérdida | Media | Medio | CA-22 lo ata a `wc -c agents/evaluator.md` ≤ **15.513** bytes de hoy: si crece, el criterio falla |
| **F6** — la fase se cae del alcance por ir última | **Media** | **Alto** | Escrito como criterio (CA-25) y repetido aquí: **es la condición previa**, no un extra. «Reforzar la recuperación mientras `/retro` está parado es afilar un grifo sin agua» |
| **Transversal** — que la suite baje de 1.175 tests | Baja | Alto | `pytest -q` en la puerta de cada fase, con la línea base escrita en spec, plan y ledger |
| **Transversal** — que las horas humanas sigan sin validarse | **Alta** | Alto | Cerrar con `/retro` y meter la **primera fila con horas humanas reales** en `CALIBRATION.md` — que es justo lo que la Fase 6 desatasca |

---

## Métricas de éxito

Cada una con el **valor de hoy** al lado, para que la mejora sea comprobable y no una impresión.

| KPI | Hoy (medido) | Objetivo |
|---|---|---|
| Coste de recuperar los aciertos de un área | **3.685 tokens** (leer el índice entero) | **≤ 300 tokens** por consulta, **≤ 30** por acierto |
| Tokens de memoria curada en el brief del subagente | **0** (de 1.818) | **≤ 600**, con test que afirma el tope |
| Tokens de memoria curada al arrancar sesión | **0** (de 872) | **≤ 300** del área activa, dentro de 9.500 caracteres |
| Entradas que ninguna pieza ejecutable puede alcanzar | **17 de 31 (55 %)** | **0**: todas alcanzables por consulta, con o sin cableado en prosa |
| Tests que se ponen rojos si el camino de memoria no se recorre | **0** | **≥ 1** determinista (con su mutante) + casos en `evals/` |
| Entradas de journal con `decisiones` no vacías | **0** (garantizado por diseño en modo hook) | **> 0** con el log crudo poblado |
| Doctrina disponible en un proyecto recién instalado | **0** lecciones | **9** (`LES-001…009`) sin engordar el prompt |
| Días desde la última fila de `CALIBRATION.md` | **15** (13 iniciativas cerradas después) | **≤ 1 iniciativa cerrada** sin su fila |
| Suite / linter / evals | 1.175 passed · 0 errores · 0 errores | **no bajan** |

---

## Changelog del plan

| Fecha | Cambio | Autor |
|-------|--------|-------|
| 2026-09-04 | Creación del plan (6 fases, 18 tareas) desde `spec.md` `aprobada` y `evaluation.md`; horas y costes **heredados** por característica, sin re-estimar | `planner` |

---

## Siguiente paso

Con el **OK del plan** del usuario (puerta de control), el agente **`implementer`** lo ejecuta fase a
fase sobre una rama, marcando [`tasks.md`](tasks.md) como **ledger canónico** (checkbox + estado por
tarea) y ejecutando la `Verificación` de cada tarea al cerrarla, con su salida pegada. Al final de
cada fase: `scope-check.py` → revisión de dos lentes (≤ 3 intentos) → `ledger-lint.py` +
`pytest -q` + `lint_plugin.py` + `evals/check.py`. Cierre de la iniciativa con `documenter` (doc
ES/EN) y **`/retro`**, que es a la vez la última fase y la condición previa del valor de todo lo demás.
