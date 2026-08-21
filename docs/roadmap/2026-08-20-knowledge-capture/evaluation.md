---
generacion:               # usage-meter.py NO disponible en este entorno (sandbox cloud, sin transcripción local)
  inicio: 2026-08-20T07:55:00Z
  fin: 2026-08-20T08:15:00Z
  fuente: estimado        # degradación declarada: no hay medición de tokens
  tokens_reales: no-medido (sandbox)
  eur: null
  horas_ia: null
  duracion: no-medido (sandbox)
  ratio_usado: 479326     # mediana de CALIBRATION.md (referencia; no se aplicó por falta de medición)
---

# 2026-08-20-knowledge-capture

> Memoria técnica de los agentes — cuánto cuesta capturar ADRs, gotchas y aprendizajes **y cerrar el bucle** para que los agentes los lean después.

| | |
|---|---|
| **Fecha** | 2026-08-20 |
| **Estado** | completado |
| **Prioridad global** | Alta |
| **Solicitante** | daycry (vía `/pm-cycle`) |
| **Spec** | [`spec.md`](spec.md) |
| **Plan** | [`improvement-plan.md`](improvement-plan.md) |
| **Características evaluadas** | 7 — 6 comprometidas + 1 diferida (C-06) |

---

## Cuadro de mando

| Métrica | Total estimado | Confianza |
|--------|----------------|-----------|
| Esfuerzo humano | **24 h** (20 h base +20 %) | Baja |
| Tiempo IA (ejecución) | **0,95 h** (+ 0,24 h supervisión) | Media |
| Coste | **≈ 1.205 €** | Baja |
| Tokens IA | **456k** con margen — 380k base (in 328k / out 52k) | Media |
| Multiplicador productividad | **×20** | — |
| Características | **6 comprometidas** (C-01…C-05 + C-07 backfill) · 1 diferida (C-06) | — |

> **Ajustado en puerta go (2026-08-20): C-06 diferido, backfill dentro, D1-D3 cerradas.** El lote pierde el lint determinista (−5 h / −250 € / −70k) y gana el **backfill semilla como característica propia C-07** (+2 h / +100 € / +35k). Recorrido de las cifras: 23 h base → **20 h**; ≈ 1.386 € → **≈ 1.205 €**; 420k → **380k**; ×21 → ×20. Umbral de registro **aprobado tal cual**; sin decisiones abiertas.

> **Por qué la confianza del coste es Baja:** el 99,6 % del importe son horas **humanas**, y `CALIBRATION.md` (aprendizaje nº 2) deja constancia de que en este proyecto **nunca se han validado**: las 5 iniciativas medidas tienen 0 h humanas reales. Además, **cuatro piezas que hay que tocar no están en la copia del repo disponible** (ver "Ambigüedades"), lo que añade incertidumbre real, no retórica.

---

## Resumen ejecutivo

El plugin **produce** conocimiento técnico bueno y lo **pierde**: nadie escribe ADRs (el `documenter` solo reutiliza «los que ya haya»), la bitácora del ledger está muerta (4 de 12 `tasks.md` la conservan, con una nota administrativa dentro), los aprendizajes de `/retro` quedan en silo porque solo los números viajan a `CALIBRATION.md`, `debug-root-cause` no persiste su causa raíz y el flaky justificado de `qa` se queda en `raw/`. La prueba más elocuente es un anti-patrón vivo: las tres lecciones de la primera calibración están **hardcodeadas en el prompt del evaluator** — hoy, para que un agente aprenda, hay que editarle el prompt. Tras la puerta se compromete un alcance de **6 características** por **20 h base (24 h con margen) ≈ 1.205 €** y **380k tokens**: el lint determinista queda **diferido** (con disparadores objetivos, no olvidado) y entra el **backfill semilla** para que la memoria arranque con contenido real. El eje de valor no es escribir: es **C-03, el bucle de lectura** — sin él esto es un archivo, no una memoria. Veredicto: **GO**, con el umbral de registro aprobado tal cual y un criterio de éxito medible (CA-07: que las lecciones salgan del prompt del evaluator y sigan aplicándose).

---

## Requerimientos recibidos

Mapa del análisis de origen (2026-08-20, huecos 1-7) a las características evaluadas.

| ID | Característica | Requisito origen (ref.) | ¿Claro? |
|----|---------------|-------------------------|---------|
| C-01 | ADR ligero (plantilla + quién/cuándo + índice) | análisis hueco 1 · spec §Decisiones, CA-01/CA-03 | ⚠️ ambiguo (D1 estructura) |
| C-02 | Registro de gotchas en los puntos de nacimiento | huecos 5 y 6 · spec §Flujo pasos 3-4, CA-05 | ⚠️ ambiguo (D1) |
| C-03 | **Bucle de lectura** + migración de las lecciones hardcodeadas | hueco 4 · spec §Decisiones (bucle), CA-02/CA-03/CA-07 | ✅ claro (es el núcleo) |
| C-04 | `/retro` con dos salidas | hueco 3 · spec CA-06 | ✅ claro |
| C-05 | Doc de la práctica (CONVENTIONS + FLOWS + espejo EN) | restricción bilingüe del repo · CA-10 | ✅ claro |
| C-06 | Índice generado + `knowledge-lint.py` (determinismo) | regla de determinismo del repo | ⏸️ **diferido** (D4: >15 entradas o 1.ª colisión de IDs) |
| C-07 | **Backfill semilla** (5 `retro.md` + decisiones D1-D5 de confluence-policy) | análisis huecos 1 y 3 · spec CA-09/CA-12 | ✅ claro (D5 cerrada: dentro) |

**Decisiones cerradas en la puerta go (2026-08-20) y su efecto en el presupuesto:**

- **Umbral de registro — aprobado tal como está en la spec** (ADR si cierra alternativa y afecta a 2+ piezas o se tomó en puerta; gotcha si costó ≥1 ciclo de depuración; orientación 0-2 entradas por iniciativa). Sin cambio de horas; es la mitigación del riesgo nº 1 y queda fijada por decisión, no por criterio del agente de turno.
- **D1 — `docs/knowledge/` único** (`README.md` · `adr/` uno por decisión · `gotchas.md` fichero único · `LESSONS.md` por agente). **Sin cambio de horas**: era una de las dos variantes ya presupuestadas en C-01/C-02, y la elegida es la más simple de indexar.
- **D2 — Se retira la sección "Notas de implementación"** de la plantilla de `tasks.md` (los nuevos nacen sin ella; los existentes no se tocan; reversible). Sin cambio: ya estaba dentro de C-01.
- **D3 — Siempre activa, sin opt-in**, con degradación silenciosa. **−0 h netas**: se ahorra documentar la clave de `dev.json` (~0,5 h que estaban repartidas entre C-03 y C-05), pero ese margen se consume en redactar con cuidado la degradación en el fragmento, que ahora aplica a todo proyecto consumidor sin interruptor.
- **D4 — C-06 diferido** (no cancelado; disparadores: >15 entradas o 1.ª colisión de IDs de ADR en lote paralelo). **−5 h / −250 € / −70k tokens.**
- **D5 — Backfill semilla dentro**, como característica propia **C-07**. **+2 h / +100 € / +35k tokens.**
- **Neto: 23 h → 20 h base** (−13 %); ≈ 1.386 € → ≈ 1.205 €; 420k → 380k tokens.

**Por qué el backfill va como C-07 y no dentro de C-04:** tiene criterio de aceptación propio (CA-09: cada entrada trazable a su fuente, sin conclusiones añadidas), riesgo propio (distorsionar material ya validado al resumirlo) y es **prerequisito de la prueba crítica** de C-03 —el bucle debe leer memoria real, no vacía—. Meter 2 h comprometidas dentro de una característica de 1,5 h escondería la mitad del trabajo y rompería el contrato de que el `planner` hereda horas **por característica** sin re-estimar.

**Sigue sin poder verificarse aquí (declarado en la spec):** `agents/nemesis.md` (patrón de memoria a generalizar), `agents/planner.md`, `skills/debug-root-cause/SKILL.md` y la plantilla de `tasks.md` **no están** en la copia parcial del repo con la que se ha evaluado. Sus referencias vienen del análisis previo; las horas de C-01, C-02 y C-04 llevan esa incertidumbre dentro.
- **No verificable en este entorno (afecta a la confianza, declarado en la spec):** `agents/nemesis.md` (patrón de memoria a generalizar), `agents/planner.md`, `skills/debug-root-cause/SKILL.md` y la plantilla de `tasks.md` **no están** en la copia parcial del repo con la que se ha evaluado. Sus referencias vienen del análisis previo; las horas de C-01, C-02 y C-04 llevan esa incertidumbre dentro.

---

## Datos necesarios para una evaluación completa

- [x] **Requerimientos** completos y sin ambigüedades — *umbral aprobado y D1-D5 cerradas en la puerta go del 2026-08-20; no queda ninguna decisión abierta*
- [x] **Alcance** de cada característica acotado (qué entra y qué NO) — spec §Alcance
- [x] **Criterios de aceptación / éxito** por característica — CA-01 … CA-11, con CA-07 como criterio de éxito real
- [x] **Restricciones** — determinismo, degradación sin bloqueo, bilingüe EN/ES, tokens máquina en español, linter en verde
- [ ] **Dependencias externas** — *ninguna externa, pero sí internas no verificadas: 4 ficheros del repo ausentes en esta copia*
- [x] **Contexto técnico** del proyecto — repo explorado; líneas citadas en la spec
- [x] **Tarifa/hora y supuestos de coste** confirmados — `.claude/rates.json`, precios verificados el 2026-08-18

---

## Supuestos económicos (ajustables)

**Coste = (horas × tarifa) + coste de tokens de IA.** Importes en **EUR**. Fuente: `.claude/rates.json`.

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | 50 €/h | `rates.json:tarifaHora` |
| Modelo IA asumido | claude-opus-4-8 | `rates.json:modeloIA` |
| Precio input | 5,00 USD / 1M tokens → **4,60 € / 1M** | Verificado el 2026-08-18 con `rates-verify` (fiable, < 90 días) |
| Precio output | 25,00 USD / 1M tokens → **23,00 € / 1M** | Ídem |
| Precio escritura de caché | 6,25 USD / 1M tokens | Ídem; entra en "tokens facturables" |
| Precio lectura de caché | 0,50 USD / 1M tokens | Ídem; no cuenta para horas, **sí** para € (aprendizaje nº 4) |
| Tipo de cambio | 1 USD = 0,92 € | ⚠️ **verificar** — `rates.json` lo declara supuesto, no dato |
| Ratio tokens→hora-IA | **479.326 tok/h** | Mediana medida de `CALIBRATION.md` (5 muestras), con precedencia sobre el default no calibrado de 300.000 |
| Ratio de supervisión | 25 % de las horas IA | `rates.json:ratioSupervision` |
| Margen de contingencia | 20 % | Sobre horas base (humanas e IA) y sobre tokens |
| Lectura de caché prevista | ~3,5M tokens | ⚠️ **supuesto** por analogía con el histórico (eran 4M antes de diferir C-06: sin script ni tests que iterar, baja) |

**Método y calibración aplicada:**

- **Horas humanas**: descomposición por fichero afectado (los de la spec §Arquitectura), tarificando decisión + edición + revisión humana.
- **Tokens**: previsión por característica, calibrada a la baja con `CALIBRATION.md` (las 5 iniciativas medidas se desviaron entre −66 % y −97 % de estimaciones hechas por analogía con código). Aprendizaje nº 5: esto es **prosa** (minutos), salvo C-06 que es **prosa + tests** (×2).
- **Horas IA**: `tokens facturables ÷ 479.326`, no "a juicio" (aprendizaje nº 1).
- **Líneas propias** para **revisión adversarial** y **coste de proceso** (aprendizajes nº 2 y nº 3). Aquí la revisión se presupuesta **alta (70k)**: se tocan 8-10 prompts de agentes y el histórico avisa de que dos hallazgos de la doble lente habrían roto una garantía del producto — cambiar prompts es exactamente ese terreno. (Eran 75k con C-06 dentro: al diferir el script y sus tests baja algo, pero **no** proporcionalmente, porque el material más delicado de revisar sigue siendo los prompts.)
- **Ironía metodológica que conviene registrar:** esta evaluación usa las tres lecciones que C-03 quiere sacar del prompt. Son útiles precisamente porque el evaluator las lee; el objetivo de la iniciativa es que las lea **de un fichero**.

---

## Evaluación por característica

### C-01 — ADR ligero (plantilla, umbral, autoría, índice)

- **Requisito origen**: análisis hueco 1; spec §Decisiones de diseño y CA-01/CA-03.
- **Descripción**: plantilla corta y fija (contexto · decisión · **alternativas descartadas** · consecuencias · estado) en `agent-kits/shared/templates/adr.md`; `planner` e `implementer` escriben un ADR cuando una decisión cruza el umbral; `documenter` los indexa en su taxonomía en vez de re-derivar decisiones del código.
- **Complejidad**: Media — la plantilla es trivial; lo difícil es el **umbral** y que la autoría no se convierta en papeleo por tarea.
- **Esfuerzo**: 4 h · confianza Media
- **Previsión IA**: 39k in / 6k out tok · ≈ 0,33 € · ~0,09 h-IA
- **Coste**: (4 h × 50 €/h) + 0,33 € = **≈ 200 €**
- **Impacto / áreas afectadas**: `agent-kits/shared/templates/adr.md` (nuevo), `agent-kits/shared/knowledge-write.md` (nuevo), `agents/planner.md`, `agents/implementer.md`, `agents/documenter.md` (L74/L96)
- **Dependencias y prerequisitos**: D1 (estructura). `agents/planner.md` **no está en la copia disponible**: su integración se estima por analogía con `implementer`.
- **Riesgos**: que se escriban ADRs de decisiones triviales (ruido que nadie leerá) o que no se escriba ninguno porque el umbral es tan alto que nunca aplica. Ambos extremos hacen inútil la característica; solo se detecta contando entradas en la primera retro.
- **Incógnitas / preguntas abiertas**: ¿el ADR es de proyecto (decisiones del producto del consumidor) o también de proceso (decisiones sobre el plugin)? Se propone **proyecto**, con las de proceso en `LESSONS.md`. ¿Quién decide el número (`NNNN`) si dos agentes escriben en paralelo? Con lotes paralelos (máx. 3) hay riesgo de colisión de IDs — resoluble con sufijo por slug o con el lint de C-06.

### C-02 — Registro de gotchas en los puntos de nacimiento

- **Requisito origen**: análisis huecos 5 y 6; spec §Flujo pasos 3-4, CA-05.
- **Descripción**: `docs/knowledge/` recoge gotchas escritos **donde el conocimiento nace**: cierre de F4 de `debug-root-cause` (causa raíz probada + enlace al test de regresión), `qa` cuando un flaky justificado es un patrón y no un accidente, y `/retro` para lo técnico. Formato corto: síntoma · causa raíz · qué hacer en su lugar · evidencia.
- **Complejidad**: Media — tres puntos de captura en tres piezas distintas, cada una con su propio cierre y su propia noción de "esto merece entrada".
- **Esfuerzo**: 4,5 h · confianza Baja *(la más afectada por las piezas ausentes: `skills/debug-root-cause/SKILL.md` no está en la copia disponible y es el punto de captura más valioso)*
- **Previsión IA**: 43k in / 7k out tok · ≈ 0,37 € · ~0,10 h-IA
- **Coste**: (4,5 h × 50 €/h) + 0,37 € = **≈ 225 €**
- **Impacto / áreas afectadas**: `skills/debug-root-cause/SKILL.md`, `agents/qa.md` (L67-69), `commands/retro.md`, `docs/knowledge/gotchas.md` (nuevo), `agent-kits/shared/knowledge-write.md`
- **Dependencias y prerequisitos**: D1; comparte el fragmento de escritura con C-01 (hacerlas en la misma fase evita escribirlo dos veces).
- **Riesgos**: **capturar sin filtro** convierte `gotchas.md` en un log; el histórico ya demuestra el fallo simétrico (la bitácora de `tasks.md`: 4/12 conservadas, contenido ~1 nota administrativa). Riesgo secundario: un gotcha mal diagnosticado se convierte en doctrina que otros agentes leerán — mitigado con `estado: propuesta` hasta validación.
- **Incógnitas / preguntas abiertas**: ¿el gotcha de un flaky vive en `knowledge/` o basta con consolidar `flaky-justify.json`? Se propone `knowledge/` solo si el patrón se repite en dos ciclos, para no registrar accidentes.

### C-03 — Bucle de lectura + migración de las lecciones hardcodeadas ⭐

- **Requisito origen**: análisis hueco 4; spec §Decisiones (bucle), CA-02/CA-03/CA-07.
- **Descripción**: fragmento compartido `knowledge-check.md` calcado de `constitution-check.md` —que ya se referencia **idéntico** en `evaluator.md` L95, `implementer.md` L75, `qa.md` L82 y `documenter.md` L142— para que los cinco agentes lean la memoria relevante al arrancar, con **progressive disclosure** (índice primero, entrada después). Y la prueba del mecanismo: **sacar las tres lecciones del prompt del evaluator** a `LESSONS.md` y comprobar que se siguen aplicando.
- **Complejidad**: **Alta** — no es escribir un fichero, es **cambiar el comportamiento de cinco agentes** y quitar de un prompt algo que hoy funciona. Es la única característica que puede causar una regresión silenciosa (que el evaluator deje de aplicar las lecciones sin que nadie lo note).
- **Esfuerzo**: 5 h · confianza Media
- **Previsión IA**: 52k in / 8k out tok · ≈ 0,44 € · ~0,13 h-IA
- **Coste**: (5 h × 50 €/h) + 0,44 € = **≈ 250 €**
- **Impacto / áreas afectadas**: `agent-kits/shared/knowledge-check.md` (nuevo), `agents/evaluator.md` (bloque tras P2-bis: se **retira**), `agents/planner.md`, `agents/implementer.md`, `agents/qa.md`, `agents/documenter.md`, `docs/knowledge/LESSONS.md` (nuevo)
- **Dependencias y prerequisitos**: necesita que exista **algo** que leer (C-01/C-02 o el backfill de D5). Con memoria vacía, el bucle no se puede probar de verdad — argumento a favor de D5.
- **Riesgos**: (a) **regresión de comportamiento**: el prompt adelgaza y el agente deja de aplicar lo aprendido; se mitiga con CA-07 como criterio explícito y ejecutando el evaluator sobre una spec de prueba; (b) **coste de contexto**: sumar un paso de lectura a cinco agentes empuja en dirección contraria a `2026-08-10-token-diet` (12,9 h invertidas en adelgazar el contexto) — se mitiga leyendo el índice y no el cuerpo; (c) **doctrina obsoleta**: una lección vieja condicionando estimaciones nuevas sin que nadie la revise.
- **Incógnitas / preguntas abiertas**: D3 (opt-in o siempre). ¿Qué lee cada agente? Propuesta: `evaluator` → `LESSONS.md`; `planner` → ADR + lecciones; `implementer` → ADR + gotchas; `qa` → gotchas; `documenter` → todo (para indexar). ¿Se declara `knowledge` en el bloque `dependencies` del frontmatter (grafo del linter)?

### C-04 — `/retro` con dos salidas

- **Requisito origen**: análisis hueco 3; spec CA-06.
- **Descripción**: `/retro` separa lo que ya hace bien (números → fila de `CALIBRATION.md`) de lo que hoy se queda en silo (aprendizajes técnicos → `LESSONS.md`/gotchas), con la marca `Estado: [actualizado|sin cambios]` del patrón `nemesis`.
- **Complejidad**: Baja — un paso más en un comando que ya tiene el material delante; el `retro.md` de sdd-hardening prueba que la materia prima existe y es buena.
- **Esfuerzo**: 1,5 h · confianza Alta
- **Previsión IA**: 17k in / 3k out tok · ≈ 0,15 € · ~0,04 h-IA
- **Coste**: (1,5 h × 50 €/h) + 0,15 € = **≈ 75 €**
- **Impacto / áreas afectadas**: `commands/retro.md` (L16-17)
- **Dependencias y prerequisitos**: C-02 (dónde escribir). Es la vía natural del **backfill** de D5: pasar los 5 `retro.md` existentes por la nueva salida.
- **Riesgos**: bajo. El único: tocar `/retro` y romper la fila de `CALIBRATION.md`, de la que depende el ratio tokens→hora de todo el sistema de estimación — cubierto por CA-06 ("sin regresión en la calibración").
- **Incógnitas / preguntas abiertas**: ¿un aprendizaje puede ir a las dos salidas (número + lección)? Se propone sí, con enlace cruzado, sin duplicar el texto.

### C-05 — Doc de la práctica (CONVENTIONS + FLOWS + espejo EN)

- **Requisito origen**: restricción bilingüe del repo; spec CA-10.
- **Descripción**: documentar dónde vive el conocimiento, el **umbral** ("qué merece registro" con ejemplos de lo que **no**), quién lee y quién escribe; en `docs/CONVENTIONS.md` y `docs/FLOWS.md`, con espejo `docs/en/` en el mismo cambio y los tokens de máquina en español.
- **Complejidad**: Baja — prosa, pero por duplicado y en dos ficheros normativos.
- **Esfuerzo**: 3 h · confianza Alta
- **Previsión IA**: 39k in / 6k out tok · ≈ 0,33 € · ~0,09 h-IA
- **Coste**: (3 h × 50 €/h) + 0,33 € = **≈ 150 €**
- **Impacto / áreas afectadas**: `docs/CONVENTIONS.md`, `docs/FLOWS.md`, `docs/en/CONVENTIONS.md`, `docs/en/FLOWS.md`, `docs/README.md`
- **Dependencias y prerequisitos**: depende de C-01 a C-04 (documenta lo que decidan). Va **al final**: documentar antes obliga a rehacer el espejo EN dos veces.
- **Riesgos**: el umbral escrito de forma vaga ("registra lo importante") reproduce la bitácora muerta. La calidad de esta característica **es** la mitigación del riesgo nº 1: si el umbral no queda operativo con ejemplos, la iniciativa fracasa aunque todo lo demás esté hecho.
- **Incógnitas / preguntas abiertas**: ¿la práctica es regla de `CONVENTIONS.md` (obligatoria) o guía de `FLOWS.md` (descriptiva)? Se propone regla en CONVENTIONS + matriz en FLOWS.

### C-06 — Índice generado + `knowledge-lint.py` (determinismo) — ⏸️ **DIFERIDO** (D4)

> **Estado tras la puerta go:** fuera del alcance comprometido, **no cancelado**. Se retoma cuando se cumpla uno de estos dos disparadores objetivos: **>15 entradas** en `docs/knowledge/` o la **primera colisión de IDs de ADR** en un lote paralelo. Hasta entonces el índice se mantiene a mano (CA-12). Se conserva aquí el presupuesto para poder retomarlo sin re-estimar: **5 h / ≈ 250 € / 70k tokens**.

- **Requisito origen**: regla de determinismo del repo ("los cálculos y veredictos van en scripts con tests y exit codes").
- **Descripción**: script con tests que valide el formato de cada entrada (campos obligatorios, `estado`, IDs únicos sin colisión), detecte índice obsoleto y lo regenere (`--index`), con exit code para CI. El juicio "¿merece registro?" sigue siendo humano; el formato y la frescura del índice dejan de serlo.
- **Complejidad**: Alta *(dentro de este lote)* — única pieza con código, tests y fixtures; se engancha a `lint_plugin.py` y a las suites de `tests/`.
- **Esfuerzo**: 5 h · confianza Baja (rango 4-7 h)
- **Previsión IA**: 60k in / 10k out tok · ≈ 0,53 € · ~0,15 h-IA *(aprendizaje nº 4: con tests, ×2 sobre una tarea de prosa)*
- **Coste**: (5 h × 50 €/h) + 0,53 € = **≈ 250 €**
- **Impacto / áreas afectadas**: `agent-kits/shared/knowledge-lint.py` (nuevo), `tests/` (nueva suite), `scripts/lint_plugin.py` (enganche), `docs/knowledge/README.md` (índice generado)
- **Dependencias y prerequisitos**: depende de C-01/C-02 (no se valida un formato que no existe) y ahora también del volumen: sin ~15 entradas no hay nada que valga la pena validar.
- **Riesgos**: **el riesgo de diferirlo** es que el índice a mano se desincronice y el bucle de lectura lea una tabla incompleta (mitigación: CA-12 y revisión en la primera retro). El riesgo de **haberlo hecho ahora** era sobre-ingeniería sobre ~10 entradas y el 22 % del presupuesto. Riesgo de coste al retomarlo: la estimación más volátil del lote (4-7 h).
- **Incógnitas / preguntas abiertas**: al retomarlo, ¿script propio o extensión de `lint_plugin.py`? Más barato lo segundo (~3 h) pero mezcla responsabilidades; se propone script propio invocado por el linter, coherente con `qa-gate`/`ledger-lint`.

### C-07 — Backfill semilla de la memoria (D5, dentro)

- **Requisito origen**: análisis huecos 1 y 3; spec CA-09 y CA-12.
- **Descripción**: poblar `docs/knowledge/` con material **ya escrito y validado**: los aprendizajes técnicos de los **5 `retro.md`** existentes → `LESSONS.md`/`gotchas.md` (agrupados por agente), y las **cinco decisiones D1-D5 de `2026-08-20-confluence-policy`** → primeros ADR con su contexto y sus alternativas descartadas. Cada entrada enlaza a su fuente; ninguna añade conclusiones que no estuvieran en ella. Se hace **usando la segunda salida de `/retro`** (C-04) en vez de a mano: así el mecanismo se estrena con datos reales.
- **Complejidad**: Baja — no hay diseño; es transformación fiel de material existente con un formato ya definido.
- **Esfuerzo**: 2 h · confianza Media
- **Previsión IA**: 30k in / 5k out tok · ≈ 0,26 € · ~0,07 h-IA
- **Coste**: (2 h × 50 €/h) + 0,26 € = **≈ 100 €**
- **Impacto / áreas afectadas**: `docs/knowledge/adr/`, `docs/knowledge/LESSONS.md`, `docs/knowledge/gotchas.md`, `docs/knowledge/README.md` (índice)
- **Dependencias y prerequisitos**: **depende de C-01/C-02** (formato y rutas) y **de C-04** (la vía por la que se escribe). Es **prerequisito de la prueba crítica de C-03**: sin memoria real, CA-07 no demuestra nada.
- **Riesgos**: **distorsión al resumir** — convertir un aprendizaje matizado en una regla tajante que luego cinco agentes leerán como doctrina. Mitigación: enlace obligatorio a la fuente y prohibición explícita de añadir conclusiones (CA-09), más el `estado: propuesta` por defecto. Riesgo secundario: seleccionar de más y arrancar ya con ruido — se acota a los 5 retro y las 5 decisiones, nada más.
- **Incógnitas / preguntas abiertas**: ninguna bloqueante. Menor: ¿las decisiones de `confluence-policy` se registran como 5 ADR separados o como 1 ADR con 5 apartados? Se propone **5 separados** (cada una cierra su propia alternativa y se cita por ID).

---

## Comparativa

| # | Característica | Complejidad | Horas | Coste € | Tokens | Prioridad | Confianza |
|---|---------------|-------------|-------|---------|--------|-----------|-----------|
| C-03 | **Bucle de lectura** + migración de lecciones ⭐ | Alta | 5 h | 250 € | 60k | Crítica 🔴 | Media |
| C-01 | ADR ligero | Media | 4 h | 200 € | 45k | Alta 🟠 | Media |
| C-02 | Registro de gotchas | Media | 4,5 h | 225 € | 50k | Alta 🟠 | Baja |
| C-07 | **Backfill semilla** *(nuevo en puerta go)* | Baja | 2 h | 100 € | 35k | Alta 🟠 | Media |
| C-04 | `/retro` con dos salidas | Baja | 1,5 h | 75 € | 20k | Media 🟡 | Alta |
| C-05 | Doc de la práctica (ES + EN) | Baja | 3 h | 150 € | 45k | Alta 🟠 | Alta |
| | **Total comprometido** | | **20 h** | **1.000 €** | **255k** | | |
| C-06 | Índice + lint determinista — ⏸️ **diferido** | Alta | *(5 h)* | *(250 €)* | *(70k)* | Baja 🟢 | Baja |

> Ordenada por lo que ayuda a decidir: primero el eje de valor (C-03), luego la captura y su contenido inicial, al final la documentación. C-06 queda **fuera del total** por estar diferido, con su presupuesto conservado entre paréntesis para retomarlo sin re-estimar. La revisión adversarial y el coste de proceso van como líneas propias en el presupuesto.

---

## Presupuesto total

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 20 h × 50 €/h | 1.000,00 € |
| Margen de contingencia | +20 % sobre desarrollo base | 200,00 € |
| Tokens IA — características | 255k (220k in / 35k out) | 1,89 € |
| Tokens IA — revisión adversarial (2 lentes) | 70k (60k in / 10k out) | 0,53 € |
| Tokens IA — coste de proceso (spec + evaluación + plan) | 55k (48k in / 7k out) | 0,40 € |
| Tokens IA — lectura de caché | ~3,5M × 0,50 USD/M ⚠️ supuesto | 1,61 € |
| Margen sobre tokens | +20 % | 0,89 € |
| **Total estimado (con margen)** | 24 h × 50 €/h + 5,32 € | **≈ 1.205 €** |
| *No comprometido — C-06 diferido* | *5 h × 50 €/h + 0,53 €* | *(≈ 250 €)* |

**Nota:** la línea de revisión es la más alta de las tres iniciativas evaluadas hasta hoy (75k) y es deliberado: se modifican 8-10 prompts de agentes, y el aprendizaje nº 3 de `CALIBRATION.md` dice que ahí es donde se va el esfuerzo real (1-10 hallazgos por iniciativa, dos de ellos capaces de romper una garantía del producto).

---

## Productividad IA (humano vs. IA)

| KPI | Valor |
|-----|-------|
| Horas humanas estimadas | 24 h *(20 h base)* |
| Horas IA (ejecución) | 0,95 h *(0,79 h base)* |
| Supervisión humana | 0,24 h *(25 % de las horas IA)* |
| **Horas totales (IA + supervisión)** | **1,19 h** |
| Horas ahorradas | 22,81 h |
| **Ahorro** | **95,0 %** |
| **Multiplicador de productividad** | **×20** |
| FTE equivalentes *(opcional)* | 0,14 |

> Horas mostradas **con el margen de contingencia (+20 %)** ya aplicado sobre las horas base (humanas e IA).

**Cómo se han obtenido (y qué valen):** las horas IA salen de `456.000 tokens facturables ÷ 479.326 tok/h` (mediana medida de `CALIBRATION.md`, 5 muestras), no de un juicio. Las horas humanas sí son un juicio y **nunca se han validado en este proyecto**: el ×20 compara una medida contra una estimación. El plazo real que fija este presupuesto es la fila de horas totales: ~1,2 h de reloj de agente más supervisión.

---

## Recomendación

- **Veredicto**: **GO** (puerta cruzada el 2026-08-20). Alcance comprometido: **C-01, C-02, C-03, C-04, C-05 y C-07**. Se mantiene **CA-07 como criterio de éxito**: si las tres lecciones no pueden salir del prompt del evaluator y seguir aplicándose, la iniciativa no ha funcionado, por muchos ficheros que existan. El **umbral de registro queda aprobado tal cual** y no se relaja sin decisión explícita.
- **D4 — C-06 diferido, no cancelado**: con una memoria que arranca en ~10 entradas, un lint valida casi nada; se retoma con **>15 entradas** o la **primera colisión de IDs de ADR** en un lote paralelo, con su presupuesto ya hecho (5 h / ≈ 250 €). Contrapartida asumida: el índice se mantiene **a mano** (CA-12) y eso es deuda con fecha de revisión, no gratis.
- **D5 — backfill dentro, como C-07** (2 h / ≈ 100 €): la memoria arranca con contenido real y la prueba crítica de C-03 se hace contra material de verdad.
- **Quick wins** (bajo coste, alto valor): **C-04** (1,5 h: el material ya existe, solo hay que dejar de tirarlo), **C-07** (2 h: transformar material ya validado) y, dentro de C-03, la migración de las lecciones (lo que más valor demuestra por hora invertida).
- **Costosas / a vigilar**: **C-02** (4,5 h, la confianza más baja del lote por depender de una skill que no se ha podido inspeccionar) y **C-03** (5 h y la única que puede provocar una regresión silenciosa de comportamiento).
- **Orden sugerido**: **C-01 + C-02 (misma fase: comparten `knowledge-write.md`) → C-04 → C-07 → C-03 → C-05**. La lógica: primero el formato y las rutas; luego `/retro` con su segunda salida, **que es la vía por la que se hace el backfill** (se estrena el mecanismo en vez de escribir a mano); después C-07 llena la memoria; entonces C-03 se prueba leyendo contenido real; y C-05 documenta al final para no rehacer el espejo EN dos veces. C-03 es el eje de valor pero **no puede ir primero**: un bucle que lee una carpeta vacía no demuestra nada.
- **Fuera de alcance**: RAG/búsqueda semántica, extracción automática sin revisión, backfill completo de las 12 iniciativas (solo el semilla acotado de C-07), y memoria entre proyectos.
- **Coordinación obligatoria**: `docs/knowledge/` debe entrar en la **selección curada** del espejo de `2026-08-20-confluence-policy` (aprobada hoy, plan pendiente). Es una línea en su `exclude`/`include` — si su plan se ejecuta antes, hay que avisarlo; si se ejecuta después, esta ruta ya debe estar en su lista.

---

## Riesgos transversales

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| **Burocracia y ruido**: se pide papeleo y los agentes lo rellenan con relleno. Ya ocurrió: la bitácora de `tasks.md` (4/12 conservadas, contenido ~1 nota administrativa) | **Alta** | **Alto** | Umbral operativo con ejemplos de lo que **no** merece entrada; **nada por tarea** (se retira la bitácora, D2); orientación de 0-2 entradas por iniciativa; contar entradas en la primera retro y recalibrar |
| **Archivo muerto**: se escribe y nadie lee (el hueco nº 3 de hoy, repetido con otro nombre) | Media | Alto | C-03 es el eje, no un extra; CA-07 lo verifica con un comportamiento observable, no con la existencia de un fichero |
| **Regresión silenciosa** al sacar las lecciones del prompt del evaluator | Media | Alto | Ejecutar el evaluator sobre una spec de prueba antes y después; mantener el bloque en git para poder volver; CA-07 explícito |
| **Coste de contexto**: leer memoria en 5 agentes deshace parte de `token-diet` (12,9 h invertidas en adelgazar) | Media | Medio | Progressive disclosure: índice corto primero, entrada solo si aplica; medir tokens de una ejecución antes/después en la retro |
| **Doctrina obsoleta o errónea**: una entrada mal diagnosticada condiciona a los agentes que la leen | Media | Alto | `estado: propuesta` hasta validación por doble lente o usuario; la constitución manda sobre la memoria; contradicción → la más reciente gana y la anterior queda `obsoleta` con rastro |
| **Piezas no verificadas**: 4 ficheros que hay que tocar (`nemesis`, `planner`, `debug-root-cause`, plantilla de `tasks.md`) no están en la copia evaluada | Alta | Medio | Confianza rebajada en C-01/C-02/C-04; primer paso del plan: inspeccionarlos y confirmar las horas antes de ejecutar |
| **Colisión de IDs de ADR** con lotes paralelos (máx. 3 tareas) | Media | Bajo | Numeración con sufijo por slug de iniciativa. Sin el lint (C-06 diferido) la detección es manual: la primera colisión es, de hecho, uno de los dos disparadores para retomarlo |
| **Índice a mano se desincroniza** (consecuencia asumida de diferir C-06): el bucle lee una tabla incompleta y el conocimiento nuevo es invisible | Media | Medio | CA-12 (índice completo como criterio) y "quien añade entrada actualiza el índice en el mismo cambio"; contar entradas vs. filas del índice en la primera retro |
| **Distorsión en el backfill** (C-07): resumir un aprendizaje matizado como regla tajante que cinco agentes leerán como doctrina | Media | Medio | Enlace obligatorio a la fuente y prohibición de añadir conclusiones (CA-09); `estado: propuesta` por defecto; alcance acotado a 5 retro + 5 decisiones |
| Estimación de horas humanas no validada (0 h reales en las 5 filas del histórico) | Alta | Medio | Presentar el coste como comparativa entre características, no como compromiso; `/retro` al cerrar |

---

## Siguiente paso

Para **ejecutar** lo aprobado, genera el plan detallado con el agente **`planner`** (creará `improvement-plan.md` + `tasks.md` en `docs/roadmap/2026-08-20-knowledge-capture/`). **No hay decisiones pendientes**: umbral aprobado y D1-D5 cerradas en la puerta go. Orden a heredar: **C-01 + C-02 → C-04 → C-07 → C-03 → C-05** (C-06 **diferido**, con su presupuesto conservado para cuando se cumpla uno de sus disparadores). El `planner` hereda las horas y costes por característica de esta evaluación —no re-estima desde cero— y actualizará la fila **Plan** de este documento y el campo `plan:` de la spec al crear el plan. Primera tarea recomendada del plan: **inspeccionar las cuatro piezas no verificadas** y confirmar (o corregir) las horas de C-01, C-02 y C-04.

---

## Changelog

| Fecha | Cambio |
|---|---|
| 2026-08-20 | Creación de la spec (`borrador`) y de esta evaluación a partir del análisis previo del circuito de conocimiento (huecos 1-7). 6 características, veredicto go condicionado con recomendación explícita de dejar C-06 fuera y hacer el backfill semilla. Estado → `en-revision`. Medición de generación degradada a `estimado`: `usage-meter.py` no disponible en el entorno. |
| 2026-08-20 | **Puerta go: GO con la variante recomendada.** Umbral de registro aprobado tal cual; D1 (`docs/knowledge/` único: `adr/` + `gotchas.md` + `LESSONS.md` por agente), D2 (se retira la sección "Notas de implementación" de la plantilla de `tasks.md`, reversible) y D3 (siempre activa, sin opt-in, degradación silenciosa) cerradas. **D4: C-06 diferido** (disparadores: >15 entradas o 1.ª colisión de IDs) −5 h/−250 €/−70k, con presupuesto conservado; **D5: backfill semilla dentro** como característica propia **C-07** +2 h/+100 €/+35k. Totales 23 h → **20 h base** (27,6 → **24 h** con margen), ≈ 1.386 € → **≈ 1.205 €**, 420k → **380k** tokens (revisión 75k → 70k; caché 4M → 3,5M), ×21 → ×20. Nuevos criterios CA-09 (trazabilidad del backfill) y CA-12 (índice completo a mano); CA-09 anterior (lint) retirado con C-06. Orden revisado: C-01+C-02 → C-04 → C-07 → C-03 → C-05. Riesgos añadidos: índice desincronizado y distorsión en el backfill. Estado → `completado`; spec → `aprobada`. |
