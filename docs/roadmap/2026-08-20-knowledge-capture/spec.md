---
spec: knowledge-capture
descripcion: Memoria técnica de los agentes — capturar ADRs, gotchas y aprendizajes donde nacen y, sobre todo, hacer que los agentes los LEAN después.
estado: implementada     # borrador | aprobada | implementada | obsoleta
creado: 2026-08-20
actualizado: 2026-08-20
evaluacion: evaluation.md
plan: improvement-plan.md
generacion:               # usage-meter.py NO disponible en este entorno (sandbox cloud, sin transcripción local)
  inicio: 2026-08-20T07:55:00Z
  fin: 2026-08-20T08:05:00Z
  fuente: estimado        # degradación declarada: no hay medición de tokens
  tokens_reales: no-medido (sandbox)
  eur: null
  horas_ia: null
  duracion: no-medido (sandbox)
  ratio_usado: 479326     # mediana de CALIBRATION.md (referencia; no se aplicó por falta de medición)
---

# Memoria técnica de los agentes (knowledge-capture)

> **Evaluación:** [`evaluation.md`](evaluation.md)
> **Plan de implementación:** [`improvement-plan.md`](improvement-plan.md)

> **Terminología:**
> · **ADR** — *Architecture Decision Record*: registro corto de una decisión de diseño (contexto · decisión · alternativas descartadas · consecuencias), numerado e inmutable salvo por su estado.
> · **Gotcha** — trampa comprobada del proyecto: algo que falló, por qué falló y qué hacer en su lugar. Nace de una depuración real, no de una intuición.
> · **Lección** — aprendizaje de proceso, transversal a iniciativas (p. ej. "el coste se va en la revisión, no en escribir").
> · **Bucle de lectura** — el paso por el que un agente **consulta** la memoria al arrancar. Sin él, esto es un archivo muerto, no memoria.
> · **Punto de nacimiento** — el momento exacto del flujo en que el conocimiento existe y es barato de escribir (cierre de `debug-root-cause`, justificación de un flaky, puerta de decisión, retro).

## Contexto y objetivo

Hoy el plugin **produce** conocimiento técnico de calidad y lo **pierde**. El análisis previo (2026-08-20, ver **Referencias**) documentó siete huecos verificados sobre el repo:

1. **ADRs: nadie los escribe.** `documenter` solo reutiliza «los ADRs que ya haya» (`agents/documenter.md` L96) y deriva la categoría "arquitectura y decisiones" del código (L74), una vez al cierre del ciclo. Las decisiones tomadas en puertas y conversaciones —p. ej. las cinco decisiones D1-D5 de `2026-08-20-confluence-policy`— quedan enterradas en la spec de su iniciativa, sin registro transversal consultable.
2. **La bitácora del ledger es letra muerta.** La plantilla de `tasks.md` tiene una sección "Notas de implementación — *registra decisiones, desvíos y aprendizajes*": solo **4 de 12** `tasks.md` reales la conservan, y su contenido es una nota administrativa (token-diet) o nada (qa-strict). Evidencia de que **pedir papeleo por tarea no funciona**.
3. **Los aprendizajes de `/retro` quedan en silo.** `retro.md` captura material bueno (sdd-hardening: "el coste se fue en la revisión, no en escribir"; "medir cambió el diagnóstico"), pero solo los **números** fluyen a `CALIBRATION.md` (`commands/retro.md` L17). Lo cualitativo no lo lee nadie después.
4. **Anti-patrón probado: lecciones hardcodeadas.** Las «Tres lecciones de la primera calibración real (2026-08-18)» están escritas **a mano dentro del prompt** del evaluator (`agents/evaluator.md`, bloque tras P2-bis). Hoy, para que un agente aprenda algo, hay que **editarle el prompt**: exactamente el trabajo que un sistema de memoria haría con un fichero que el agente lee.
5. **`debug-root-cause` no persiste.** Sus cuatro fases producen causa raíz probada + test de regresión, pero ningún paso escribe el hallazgo: el "por qué falló" se queda en la conversación.
6. **`qa`: el flaky justificado se evapora.** `flaky-justify.json` (`agents/qa.md` L67-69) queda en `testing/raw/` como evidencia puntual; nadie consolida el patrón ("este test es inestable por X").
7. **El patrón ya existe dentro del plugin: `nemesis`.** Mantiene memoria persistente por proyecto (`docs/security-scan/`: `STATE.md` + `MEMORY.md`; la apertura lee, el cierre actualiza, con marca `Estado: [actualizado|sin cambios]`). No hay que inventar el mecanismo: hay que **generalizarlo**.

**Objetivo:** que el conocimiento técnico se capture **donde nace**, en **pocas entradas de calidad**, y que los agentes lo **lean al arrancar**. La prueba de que funciona no es que existan ficheros: es que las tres lecciones hardcodeadas del evaluator puedan salir del prompt y seguir aplicándose.

**Lo que importa al solicitante (Jordi):** el bucle. Escribir sin leer es archivo; el valor está en que lo aprendido condicione la siguiente ejecución.

## Decisiones de diseño

| Decisión | Elección | Motivo |
|---|---|---|
| Patrón base | **Generalizar el de `nemesis`** (`docs/security-scan/`: leer al abrir, actualizar al cerrar, marca `Estado: [actualizado\|sin cambios]`) | Ya está probado dentro del plugin y es determinista; inventar otro mecanismo sería duplicar |
| Dónde vive | **D1 — confirmada: `docs/knowledge/` único**, con `README.md` (índice), **`adr/`** (un fichero por decisión, plantilla corta), **`gotchas.md`** (fichero único) y **`LESSONS.md`** (lecciones **agrupadas por agente**) | Una raíz, no dos (`docs/adr/` aparte queda descartado): un solo sitio que leer y un solo índice que mantener. `gotchas.md` como fichero único porque el volumen esperado es bajo y así se lee de una pasada; los ADR sí van a fichero por decisión porque son inmutables y se citan por ID |
| Forma del bucle de lectura | Fragmento compartido **`knowledge-check.md`** calcado de `constitution-check.md`, que ya se referencia **idéntico** en `evaluator.md` L95, `implementer.md` L75, `qa.md` L82 y `documenter.md` L142 | Coste marginal por agente = **una línea** en su sección de reglas; el repo ya tiene el molde y la costumbre de leerlo |
| Cómo se lee sin engordar el prompt | **Progressive disclosure**: el agente lee el **índice** (una línea por entrada, con etiquetas de área) y abre **solo** la entrada aplicable a su tarea | La iniciativa `2026-08-10-token-diet` existe precisamente para no inflar el contexto; una memoria que se lee entera la desharía |
| Umbral de registro (anti-burocracia) | **ADR** solo si la decisión cierra una alternativa **y** (afecta a 2+ piezas **o** se tomó en una puerta). **Gotcha** solo si costó ≥1 ciclo de depuración **o** rompió/casi rompió una garantía del producto. Orientación: **0-2 entradas por iniciativa** | La bitácora muerta (hueco 2) demuestra que pedir registro por tarea produce relleno. Pocas entradas de calidad o nada |
| Nada por tarea | **D2 — confirmada: se retira** la sección "Notas de implementación" de la plantilla de `tasks.md`. Los `tasks.md` **nuevos nacen sin ella**; los existentes no se tocan. Lo local va junto a la tarea o al retro. **Reversible** (es una sección de plantilla, se restaura en un commit) | Mantener una sección que 8/12 borran y 4/12 dejan vacía es fingir un registro. Retirarla es la señal más clara de que el conocimiento se captura por umbral, no por trámite |
| Puntos de nacimiento | `debug-root-cause` (cierre F4 → gotcha con causa raíz probada), `qa` (flaky justificado → gotcha si es patrón), `/retro` (aprendizaje técnico → lección), puerta de decisión de `planner`/`implementer` (→ ADR) | El conocimiento es barato de escribir en el instante en que se descubre y carísimo de reconstruir después |
| Prueba del mecanismo | **Migrar las tres lecciones hardcodeadas** de `agents/evaluator.md` a `LESSONS.md` y dejar que el prompt las lea | Es la validación más honesta: si el bucle funciona, el prompt adelgaza y el comportamiento se mantiene |
| Degradación y activación | **D3 — confirmada: siempre activa, sin opt-in.** Si `docs/knowledge/` no existe, los agentes **siguen sin quejarse** (ni un aviso repetido) y la carpeta se crea **en el primer registro** | Regla del repo: las piezas opcionales degradan, no bloquean. Sin opt-in hay una superficie de config menos y la memoria es parte del funcionamiento normal, no un extra que hay que recordar encender |
| Autoría y revisión | Lo escribe el agente que lo descubre; la entrada nace con `estado: propuesta` y la valida la revisión de dos lentes o el usuario en la puerta | Evita que una conclusión errónea se convierta en doctrina que otros agentes leerán |
| Determinismo | **D4 — confirmada: DIFERIDO, no cancelado.** `knowledge-lint.py` + índice generado se hará en una iniciativa posterior. **Disparadores objetivos para retomarlo: >15 entradas en `docs/knowledge/` o la primera colisión de IDs de ADR en un lote paralelo** | La regla del repo pide scripts para cálculos y veredictos, y sigue vigente; pero con una memoria que arranca en ~10 entradas un lint valida casi nada y cuesta el 22 % del presupuesto. Se documenta el umbral para que la deuda sea explícita y con fecha de revisión, no olvido |
| Arranque con memoria real | **Backfill semilla DENTRO del alcance** (~2 h): los aprendizajes técnicos de los **5 `retro.md`** existentes → `LESSONS.md`/`gotchas.md`, y las **cinco decisiones D1-D5 de `confluence-policy`** → primeros ADR | Una memoria vacía no se lee y no permite probar el bucle. Es material ya escrito y validado: convertirlo es la forma más barata de arrancar con contenido real |

## Configuración / parámetros

| Parámetro | Clave / mecanismo | Default | Valor objetivo |
|---|---|---|---|
| Captura y bucle de lectura | Sin clave de config (D3) | — | **Siempre activos**, con degradación silenciosa si no hay `docs/knowledge/` |
| Raíz del conocimiento | Convención de ruta | — | **`docs/knowledge/`** — `README.md` (índice) · `adr/` (uno por decisión) · `gotchas.md` · `LESSONS.md` (por agente) |
| Tope orientativo por iniciativa | Regla en el fragmento | — | **0-2 entradas** (no es un límite duro; es la señal de que el umbral funciona) |
| Espejo en Confluence | `publish.exclude` de `.claude/confluence.json` | selección curada de `2026-08-20-confluence-policy` | **`docs/knowledge/**` DENTRO del espejo** — ver Dependencias |

## Arquitectura y componentes

| Pieza | Ruta | Cambio |
|---|---|---|
| Fragmento del bucle | `agent-kits/shared/knowledge-check.md` | **Nuevo** — paso "lee la memoria relevante" (molde: `constitution-check.md`) |
| Fragmento de captura | `agent-kits/shared/knowledge-write.md` | **Nuevo** — umbral + plantilla + dónde escribir |
| Plantilla de ADR | `agent-kits/shared/templates/adr.md` | **Nueva** — corta: contexto · decisión · alternativas descartadas · consecuencias · estado |
| Memoria del proyecto | `docs/knowledge/{README.md, adr/, gotchas.md, LESSONS.md}` | **Nueva** (en el proyecto consumidor; en este repo se estrena con las lecciones migradas) |
| Agentes que **leen** | `agents/evaluator.md`, `agents/planner.md`, `agents/implementer.md`, `agents/qa.md`, `agents/documenter.md` | **Modificar**: una línea de regla + el paso en su flujo |
| Agentes que **escriben** | `agents/planner.md`, `agents/implementer.md` (ADR), `agents/qa.md` (gotcha de flaky) | **Modificar**: paso condicionado al umbral |
| Skill de depuración | `skills/debug-root-cause/SKILL.md` | **Modificar**: cierre de F4 escribe el gotcha (causa raíz probada + test de regresión) |
| Retro | `commands/retro.md` | **Modificar**: dos salidas — números a `CALIBRATION.md` (como hoy), aprendizajes técnicos a `docs/knowledge/` |
| Prompt del evaluator | `agents/evaluator.md` (bloque tras P2-bis) | **Modificar**: las tres lecciones salen del prompt y se leen de `LESSONS.md` |
| Plantilla del ledger | plantilla de `tasks.md` (kit del planner) | **Modificar**: retirar la sección "Notas de implementación" (D2); los `tasks.md` existentes no se tocan |
| Memoria semilla | `docs/knowledge/adr/`, `LESSONS.md`, `gotchas.md` | **Poblar** (backfill): 5 `retro.md` + las 5 decisiones de `confluence-policy` |
| Índice + lint | `agent-kits/shared/knowledge-lint.py` + tests en `tests/` | **DIFERIDO** (D4): fuera de esta iniciativa; se retoma con >15 entradas o la primera colisión de IDs |
| Documentación | `docs/CONVENTIONS.md`, `docs/FLOWS.md` + espejos `docs/en/` | **Modificar**: la práctica, el umbral y el flujo |

Reutiliza sin tocar: el mecanismo de fragmentos compartidos, el patrón de memoria de `nemesis` y el linter del plugin.

## Flujo (paso a paso)

1. **Arranque de un agente** (evaluator/planner/implementer/qa/documenter): aplica `knowledge-check.md` → si `docs/knowledge/` existe, lee su `README.md` (índice corto) y abre solo las entradas cuya etiqueta de área toque su tarea. Si no existe, continúa.
2. **Durante el trabajo**, si aparece una decisión que cruza el umbral (cierra una alternativa y afecta a 2+ piezas o se tomó en puerta) → ADR `estado: propuesta` en `docs/knowledge/adr/`.
3. **Si algo falla y se depura**: `debug-root-cause` cierra F4 con causa raíz probada → gotcha (síntoma · causa raíz · qué hacer en su lugar · enlace al test de regresión).
4. **Si `qa` justifica un flaky** y es un patrón, no un accidente → gotcha con el motivo concreto.
5. **Revisión**: la doble lente (o el usuario en la puerta) valida las entradas `propuesta` → `aceptada`; lo dudoso se queda en `propuesta` y no se predica.
6. **`/retro`** separa salidas: números → `CALIBRATION.md`; aprendizajes técnicos → `LESSONS.md`/gotchas, con su marca `Estado: [actualizado|sin cambios]`.
7. **Índice**: se mantiene **a mano** en `docs/knowledge/README.md` (una línea por entrada con su etiqueta de área) para que el paso 1 tenga una tabla fresca que leer. La regeneración automática está **diferida** (D4); quien añade una entrada actualiza el índice en el mismo cambio.
8. **`documenter`**, al cierre del ciclo, **indexa** el conocimiento existente en la taxonomía en vez de re-derivarlo del código (`documenter.md` L74/L96).

## Alcance

- **Dentro (esta iteración):**
  - Plantilla de ADR corta + reglas de quién escribe y cuándo (umbral).
  - `docs/knowledge/` con índice, gotchas y lecciones; captura en los cuatro puntos de nacimiento.
  - **Bucle de lectura** (`knowledge-check.md`) en los cinco agentes, con progressive disclosure.
  - **Migración de las tres lecciones hardcodeadas** del evaluator como prueba del mecanismo.
  - `/retro` con dos salidas.
  - Retirada de la sección "Notas de implementación" de la plantilla de `tasks.md` (D2).
  - **Backfill semilla** (D5): los aprendizajes técnicos de los 5 `retro.md` existentes y las cinco decisiones D1-D5 de `confluence-policy` como primeras entradas.
  - Documentación de la práctica en `CONVENTIONS`/`FLOWS` + espejos EN.
- **Fuera (siguientes specs):**
  - **Índice generado + `knowledge-lint.py`** — **diferido** (D4), no cancelado: se retoma con >15 entradas o la primera colisión de IDs de ADR en un lote paralelo. Hasta entonces el índice se mantiene a mano.
  - Búsqueda semántica / RAG sobre el conocimiento (índice de texto y etiquetas es suficiente a esta escala).
  - Extracción automática de conocimiento por LLM sin revisión humana o de doble lente.
  - **Backfill completo** del histórico (12 iniciativas): solo entra el semilla acotado descrito arriba.
  - Memoria por usuario o entre proyectos (esto es memoria **del proyecto**).

## Manejo de errores

| Caso | Comportamiento |
|---|---|
| No existe `docs/knowledge/` | El agente **continúa sin quejarse** (ni un aviso repetido); la carpeta se crea en el primer registro. No hay opt-in que comprobar (D3) |
| Índice desactualizado respecto a las entradas | Aviso al leer y se actualiza a mano en el mismo cambio. La detección automática llega con el lint diferido (D4) |
| Una entrada contradice `docs/CONSTITUTION.md` | **Manda la constitución**; la entrada se marca `obsoleta` y se dice en voz alta. La memoria no puede derogar un principio |
| Dos entradas se contradicen entre sí | La más reciente gana y la anterior queda `obsoleta` con enlace a la nueva; nunca se borra el rastro |
| Entrada dudosa o no verificada | Se queda en `estado: propuesta` y el bucle de lectura la presenta como tal (no como doctrina) |
| El conocimiento crece hasta ser inmanejable | Señal de que el umbral falló: se revisa en la retro. El índice hace visible el volumen desde el primer día |

## Criterios de aceptación

- [ ] CA-01 — Existe `agent-kits/shared/templates/adr.md` con contexto · decisión · **alternativas descartadas** · consecuencias · estado, y cabe en una pantalla.
- [ ] CA-02 — `agent-kits/shared/knowledge-check.md` y `knowledge-write.md` existen y declaran la degradación ("si no existe, continúa; nunca bloquea"), con el mismo formato que `constitution-check.md`.
- [ ] CA-03 — Los cinco agentes lectores (`evaluator`, `planner`, `implementer`, `qa`, `documenter`) referencian `knowledge-check.md` en su flujo **y** declaran el kit `agent-kits/shared` en `dependencies`.
- [ ] CA-04 — El umbral de registro está escrito en `knowledge-write.md` con ejemplos de qué **NO** merece entrada, y la orientación de 0-2 entradas por iniciativa.
- [ ] CA-05 — Los cuatro puntos de nacimiento escriben: `debug-root-cause` (cierre F4), `qa` (flaky justificado como patrón), `/retro` (aprendizaje técnico), `planner`/`implementer` (ADR en decisión de diseño).
- [ ] CA-06 — `commands/retro.md` tiene **dos salidas** explícitas y sigue escribiendo la fila de `CALIBRATION.md` exactamente como hoy (sin regresión en la calibración).
- [ ] [GWT] CA-07 — Dado el prompt de `agents/evaluator.md` **sin** el bloque de las tres lecciones y un `docs/knowledge/LESSONS.md` que las contiene, Cuando el evaluator estima una iniciativa, Entonces cita las lecciones aplicables como hoy (separar horas humanas de horas-IA, presupuestar el proceso y la revisión aparte) y el prompt ya no las contiene hardcodeadas.
- [ ] CA-08 — La plantilla de `tasks.md` ya no contiene la sección "Notas de implementación" muerta (D2) y `ledger-lint.py` sigue en verde.
- [ ] CA-09 — **Backfill semilla hecho** (D5): `docs/knowledge/` contiene, al cerrar la iniciativa, los aprendizajes técnicos de los 5 `retro.md` existentes (en `LESSONS.md`/`gotchas.md`, agrupados por agente) y las cinco decisiones D1-D5 de `confluence-policy` como ADR con su contexto y sus alternativas descartadas; cada entrada enlaza a su fuente original y ninguna añade conclusiones que no estuvieran en ella.
- [ ] CA-12 — El índice `docs/knowledge/README.md` lista **todas** las entradas existentes con su etiqueta de área y su estado (mantenido a mano mientras D4 esté diferido).
- [ ] CA-10 — `docs/CONVENTIONS.md` y `docs/FLOWS.md` documentan la práctica (dónde vive, umbral, quién lee, quién escribe) y sus espejos `docs/en/` están actualizados en el mismo cambio.
- [ ] CA-11 — `python scripts/lint_plugin.py` y las suites de `tests/` en verde.

## Pruebas

- **Inspección documental** (CA-01 a CA-06, CA-08, CA-09, CA-10, CA-12): revisión por criterio contra el fichero afectado.
- **Prueba de comportamiento del bucle** (CA-07): ejecutar el evaluator sobre una spec pequeña con el prompt adelgazado y verificar que sigue aplicando las lecciones **leídas del `LESSONS.md` poblado por el backfill**. Es la prueba **crítica**: si falla, el bucle no funciona y el resto es archivo muerto.
- **Trazabilidad del backfill** (CA-09): cada entrada semilla debe poder señalarse a su fuente (`retro.md` o spec de `confluence-policy`); una entrada sin fuente es invención, no memoria.
- **Linter del plugin** (CA-11): `lint_plugin.py` (frontmatter, grafo de dependencias) + suites existentes.
- **Prueba de no-regresión de burocracia:** al cerrar la primera iniciativa con esto activo, contar las entradas generadas. Más de ~3 por iniciativa es señal de umbral mal calibrado, y se registra en la retro.

## Dependencias con otras iniciativas

- **`2026-08-20-confluence-policy` (aprobada hoy).** Su política de espejo es una **selección curada** por rutas. `docs/knowledge/` nace después de esa lista, así que hay que **añadirla explícitamente al alcance del espejo** (es documentación de decisión y resultado, justo lo que esa política quiere publicar). Si además se implementa su staging generado, `docs/knowledge/` debe aparecer en `docs/confluence/`. **Acción:** una línea en la política; no es una característica de esta spec, pero sí un requisito de coordinación.
- **`2026-08-10-token-diet`.** El bucle de lectura suma contexto a cada ejecución de cinco agentes: la disciplina de lectura de esa iniciativa (índice antes de abrir, fragmentos con `limit`) es la que evita deshacer su trabajo.
- **`2026-08-11-coste-generacion` / `/retro`.** La calibración no se toca: los números siguen su camino a `CALIBRATION.md`.

## Referencias

- `agents/documenter.md` L74 (categoría "arquitectura y decisiones" derivada del código), L96 ("README existente, ADRs… reutiliza lo que ya haya; no dupliques").
- `agents/evaluator.md` bloque tras P2-bis — las «Tres lecciones de la primera calibración real (2026-08-18)» hardcodeadas en el prompt; L95 — patrón `constitution-check.md`.
- `agents/implementer.md` L75, `agents/qa.md` L82, `agents/documenter.md` L142 — el mismo paso compartido, referenciado idéntico: molde para `knowledge-check.md`.
- `agents/qa.md` L67-69 — `flaky-justify.json` como evidencia puntual en `testing/raw/`.
- `commands/retro.md` L4 y L16-17 — aprendizajes cualitativos en `retro.md`, solo los números a `CALIBRATION.md`.
- `docs/roadmap/CALIBRATION.md` §"Aprendizajes acumulados" — cinco aprendizajes que hoy solo lee el evaluator porque están **copiados** en su prompt.
- `docs/roadmap/2026-08-20-confluence-policy/spec.md` §Decisiones de diseño — las decisiones D1-D5 que quedarían sin registro transversal (caso real del hueco 1).
- Análisis previo del circuito de conocimiento, 2026-08-20 (aportado con el encargo): huecos 1-7, incluido el patrón de memoria de `nemesis` (`docs/security-scan/`: `STATE.md` + `MEMORY.md`).

## Decisiones confirmadas (revisión del usuario · 2026-08-20)

1. **Umbral de registro: aprobado tal como está escrito** en esta spec (ADR si cierra una alternativa **y** afecta a 2+ piezas o se tomó en puerta; gotcha si costó ≥1 ciclo de depuración o rompió/casi rompió una garantía; orientación 0-2 entradas por iniciativa). **Confirmado** — es la defensa contra la burocracia y no se relaja sin decisión explícita.
2. **D1 — `docs/knowledge/` único**: `README.md` (índice) · `adr/` (uno por decisión, plantilla corta) · `gotchas.md` (fichero único) · `LESSONS.md` (lecciones **por agente**). `docs/adr/` aparte queda descartado. **Confirmado.**
3. **D2 — Se retira** la sección "Notas de implementación" de la plantilla de `tasks.md`; los nuevos nacen sin ella, los existentes no se tocan, y lo local va junto a la tarea o al retro. Reversible. **Confirmado.**
4. **D3 — Siempre activa, sin opt-in**, con degradación silenciosa: si `docs/knowledge/` no existe los agentes siguen sin quejarse y la carpeta se crea al primer registro. **Confirmado.**
5. **D4 — Índice generado + `knowledge-lint.py`: DIFERIDO**, no cancelado. Se retoma cuando haya **>15 entradas** o se produzca la **primera colisión de IDs de ADR** en un lote paralelo. **Confirmado.**
6. **D5 — Backfill semilla DENTRO** del alcance (~2 h): 5 `retro.md` + las cinco decisiones D1-D5 de `confluence-policy`. **Confirmado.**

**No queda ninguna decisión abierta.** Alcance comprometido: C-01, C-02, C-03, C-04, C-05 y el backfill (C-07 en la evaluación).

## Supuestos

- El patrón de memoria de `nemesis` (`docs/security-scan/`: `STATE.md` + `MEMORY.md`, apertura lee / cierre actualiza, marca `Estado`) es tal como lo describe el análisis previo. **No se ha podido verificar de primera mano en este entorno**: `agents/nemesis.md` no está en la copia parcial del repo con la que se redactó esta spec.
- Tampoco están en la copia `agents/planner.md`, `skills/debug-root-cause/` ni la plantilla de `tasks.md` (kit del planner): las referencias a esas piezas vienen del análisis previo y **bajan la confianza** de las características que las tocan (declarado en la evaluación).
- Se asume que añadir un paso de lectura a cinco agentes es aceptable en coste de contexto **si** se lee el índice y no el cuerpo completo; si el índice crece, el supuesto se rompe y habría que paginar por área.
- El coste de esta spec y de su evaluación **no está medido**: `usage-meter.py` no está disponible en el entorno (sandbox sin transcripción local). Los bloques `generacion:` van marcados `estimado`/`no-medido`.
