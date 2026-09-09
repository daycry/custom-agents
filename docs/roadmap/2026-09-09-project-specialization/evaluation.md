---
generacion:            # PASADA 2 — RE-PRESUPUESTO. Ventana propia, sin solape con la pasada 1
  inicio: 2026-09-09T08:48:07Z
  fin: 2026-09-09T09:00:26Z
  fuente: estimado     # `usage-meter.py close` degradó: «carpeta de transcripciones no disponible» (Windows). Tokens estimados a juicio
  tokens_reales: { entrada: 92000, salida: 21000, cache_creacion: 34000, cache_lectura: 430000 }
  eur: 1.30
  horas_ia: 0.31
  duracion: 12m
  ratio_usado: 479326
  incremento: true     # NO acumula la pasada 1 (08:04:58→08:17:19) ni la reescritura de la spec (08:38:50→08:45:34)
---

# 2026-09-09-project-specialization

> Presupuesto del **tercer bucle** (especialización por proyecto), **rehecho sobre la spec final**
> tras la pasada 2 de descubrimiento. La decisión que soporta es la puerta go/no-go, y la parte que
> la soporta es la **tabla de deltas** frente al presupuesto de la pasada 1.

| | |
|---|---|
| **Fecha** | 2026-09-09 |
| **Estado** | completado |
| **Prioridad global** | Alta |
| **Solicitante** | usuario (petición del 2026-09-09; dos pasadas de descubrimiento conversacional) |
| **Spec** | [`spec.md`](spec.md) |
| **Plan** | pendiente (handoff a `planner`) |
| **Características evaluadas** | 9 (+ 2 diferidas, presupuestadas y retiradas del total) |
| **Pasada** | **2 — re-presupuesto**; sustituye a la pasada 1 (mismo artefacto, no una evaluación nueva) |

> **Análisis de origen:** [`analysis.md`](analysis.md) — única fuente del alcance.
> **Iniciativa absorbida:** [`2026-09-04-ideas-externas/analysis.md`](../2026-09-04-ideas-externas/analysis.md) (ideas 2, 3 y 4).

---

## Cuadro de mando

| Métrica | Total estimado | Confianza |
|--------|----------------|-----------|
| Esfuerzo humano | **56,4 h** (47,0 h base +20 %) | **Baja** |
| Tiempo IA (ejecución) | **4,75 h** (+ 1,19 h supervisión) | Media |
| Coste | **2.837 €** | **Baja** |
| Tokens IA | **1.898.000** (in 1.470.000 / out 428.000) | Media |
| Multiplicador productividad | **×9,5** | — |
| Características | **9** (7 heredadas + 2 nuevas; 2 diferidas fuera del total) | — |

**Por qué estas confianzas.** El **99,3 %** del coste base son horas humanas (2.350 € de 2.367 €) y
`CALIBRATION.md` aprendizaje 2 sigue diciendo literalmente que «las horas HUMANAS estimadas no se han
validado nunca»: las 8 filas medidas tienen **0 h humanas reales**. La confianza del coste **no puede
ser mejor** que la de las horas humanas, y el recorte de alcance no ha cambiado eso — de hecho el
porcentaje **empeora** (98,7 % → 99,3 %) porque las dos características nuevas son casi todo trabajo
humano. Lo contrario también está medido: las horas y tokens de **IA** se anclan en la mediana de
5 muestras reales (479.326 tok/h), y ahí la confianza sí es Media, con el aviso de que la última
muestra (`memory-retrieval`, 2026-09-08) se desvió **+66 %** en horas IA por la revisión.

---

## Resumen ejecutivo

La spec cambió de forma material: **sale F3 completa** (deriva semántica y campo «Cuándo aplica»,
antes `C-08` y `C-09`, 5 h base · 251 €) y **entran dos características nuevas** —
`pieces-registry.py` como pieza determinista dueña del registro (`C-10`) y **piezas de proyecto
multi-runtime** (`C-11`) — más **nueve CA nuevos** y **diez CA reescritos** para ser verificables de
verdad.

El resultado es contraintuitivo y es el titular de la puerta go/no-go: **recortar F3 no abarató la
iniciativa, la encareció un 25 %**. Se ahorran 5 h base y se añaden 9,5 h base en características más
2 h base en las líneas de proceso. Total: **47,0 h base · 56,4 h con margen · 2.837 € · 1.898k tokens
· 4,75 h de IA**, contra 45,0 h y 2.264 € de la pasada 1.

Lo que se compra con ese +25 % no es alcance, es **verificabilidad**: el contrato de salida de
`role-collision.py`, el `--dry-run` que hace testeable «no escribe hasta confirmar», el tope de 5
acumulado en el registro, los tres estados por hash con dueño propio y la propiedad por registro+hash
en vez de por carpeta. La pasada 1 presupuestaba las mismas capacidades con CA que no se podían
comprobar; esta las presupuesta con CA que sí.

La decisión que soporta sigue siendo **go por tramos**, con una condición **mejorada** y una
**nueva**: el esquema del registro ya tiene dueño propuesto, así que deja de ser un deber de proceso
del `planner` y pasa a ser una dependencia del grafo (`C-10` antes de `C-05`); y `C-11` arranca con su
premisa técnica **corregida a la baja** — `export-interop.py --root` **no** funciona hoy sobre un
árbol de proyecto, y está verificado abajo con su comando y su exit code.

---

## Deltas frente a la evaluación anterior (pasada 1 → pasada 2)

La puerta go/no-go se decide sobre esta tabla. Base **sin** margen para que las cifras sean
comparables línea a línea; los totales se dan en las dos formas.

| ID | Característica | Antes (h · €) | Ahora (h · €) | Δ h | Δ € | Qué la mueve |
|---|---|---|---|---|---|---|
| C-01 | Cascada de personas en el brief | 2,5 h · 126 € | 2,5 h · 126 € | **=** | **=** | Sin cambios: CA-01 a CA-04 idénticos |
| C-02 | Doc del bucle (SPECIALIZATION +EN, FLOWS, ROLES) | 3,0 h · 151 € | 3,5 h · 176 € | **+0,5** | **+25** | CA-05 amplía el contenido obligatorio del documento (los tres estados por hash y el límite explícito a F1+F2), y va ×2 idiomas |
| C-03 | `project-scan.py` — compositor de evidencia | 5,0 h · 252 € | 6,0 h · 302 € | **+1,0** | **+50** | Regla de evidencia **en dos formas** con test propio (CA-08), aviso explícito de 0 aciertos de memoria (CA-09), **segundo árbol fixture** sin `docs/knowledge/`, y privacidad (CA-27: `redactar()` + exclusión de `docs/security-scan/`) |
| C-04 | `role-collision.py` — puerta de colisión | 3,0 h · 151 € | 3,5 h · 176 € | **+0,5** | **+25** | CA-12 añade **contrato de interfaz**: exit 0/1 y una línea `pieza · disparador · motivo`, con test que parsea el formato. Cierra la incógnita de la pasada 1 → confianza Media → **Alta** |
| C-05 | `/specialize <área>` + escalera + puertas | 7,0 h · 352 € | 7,5 h · 377 € | **+0,5** | **+25** | **Pierde** el registro (se va a C-10) y **gana** `--dry-run` (CA-14), N confirmaciones para N piezas (CA-15), tope acumulado (CA-18), CA-19a/19b partidos y confirmación extra sobre el árbol del plugin (CA-17) |
| C-06 | Sección de especialización en `/doctor` | 2,5 h · 126 € | 3,0 h · 151 € | **+0,5** | **+25** | Tres estados en vez de dos, «no gestionada» como estado válido con oferta de adopción, y **mutante de hash** en el test de biyección (CA-20, CA-21) |
| C-07 | Desambiguación con `plugin-dev` | 1,5 h · 75 € | 1,5 h · 75 € | **=** | **=** | Sin cambios: CA-22 idéntico |
| C-08 | Deriva semántica + retirada | 4,0 h · 201 € | **—** | **−4,0** | **−201** | **DIFERIDA** (F3). F2 ya entrega su auditoría mecánica vía `/doctor`: no queda ningún estadio colgando |
| C-09 | Campo «Cuándo aplica» | 1,0 h · 50 € | **—** | **−1,0** | **−50** | **DIFERIDA** (F3). Sin C-08 nadie lee ese campo, y un campo que nadie consume es la pieza muerta que la iniciativa nació para evitar |
| C-10 | `pieces-registry.py` — registro, lock, hash, 3 estados, adopción | — | 5,0 h · 252 € | **+5,0** | **+252** | **NUEVA.** Script determinista con tests, dimensionado contra sus hermanos del kit. Es la pieza que hace **verificables** idempotencia (CA-25), concurrencia (CA-26), «modificada» (CA-23) y adopción (CA-24) |
| C-11 | Piezas de proyecto multi-runtime | — | 4,5 h · 227 € | **+4,5** | **+227** | **NUEVA.** Requisito del usuario. Su premisa («`--root` ya lo hace») está **medida y es falsa**: ver §Ambigüedad 2 y CA-29 |
| — | **Revisión de dos lentes** (línea propia) | 4,0 h · 202 € | 5,0 h · 252 € | **+1,0** | **+50** | Escala con las horas de característica (se mantiene el 27 % medido) y con **34 CA** frente a 28 |
| — | **Corrección post-revisión** (línea propia) | 4,0 h · 202 € | 5,0 h · 252 € | **+1,0** | **+50** | Ídem. `LES-009` y la fila del 2026-09-08: es la partida grande, no se recorta |
| | **TOTAL base** | **37,5 h · 1.888 €** | **47,0 h · 2.367 €** | **+9,5** | **+479** | |
| | **TOTAL con margen (+20 %)** | **45,0 h · 2.264 €** | **56,4 h · 2.837 €** | **+11,4** | **+573** | |
| | **Tokens** | **1.530k** | **1.898k** | **+368k** | — | +24,1 % |

**Lectura de la tabla en cuatro líneas.**

1. **Sube todo lo que se volvió verificable.** Cinco características heredadas suben entre 0,5 h y
   1,0 h cada una (+3,0 h en total), y ninguna sube por alcance nuevo: suben porque su CA pasó de
   «se comporta bien» a «este comando da este exit code y esta línea».
2. **Bajan las dos que salen** (−5,0 h · −251 €), exactamente lo que la spec difiere.
3. **Lo que domina el delta son las dos nuevas** (+9,5 h · +479 €): entre ellas suman más que todo
   lo que se ahorró y todo lo que subió por verificabilidad.
4. **El neto es +25 %.** Quien apruebe esto debe hacerlo sabiendo que el recorte de F3 **no** es un
   ahorro: es un cambio de composición que sale más caro.

**Sigue habiendo 9 características, pero no son las mismas 9.** Coincidencia, no continuidad: salen
dos, entran dos. Cualquier comparación de «9 vs 9» sin mirar la composición es engañosa.

---

## Requerimientos recibidos

Mapa de la spec final a las características. El alcance **no se amplía**: cada `C-XX` sale de una fila
de «Dentro (esta iteración)» de la spec o de una decisión confirmada de su pasada 2.

| ID | Característica | Requisito origen (ref.) | ¿Claro? |
|----|---------------|-------------------------|---------|
| C-01 | Cascada de personas de proyecto en `task-brief.py` | spec §Alcance F1; CA-01 a CA-04 | ✅ |
| C-02 | Doc del bucle: `SPECIALIZATION.md` (+EN), FLOWS, ROLES | spec §Alcance F1; CA-05 a CA-07 | ✅ |
| C-03 | `project-scan.py` — compositor de evidencia + privacidad | spec §Flujo 1; CA-08 a CA-10, CA-27 | ✅ |
| C-04 | `role-collision.py` — puerta de colisión con contrato | spec §Flujo 2; CA-11 a CA-13 | ✅ |
| C-05 | `/specialize <área>` — escalera, `--dry-run`, N confirmaciones, tope, `tools` | spec §Flujo 3-4; CA-14 a CA-16, CA-18, CA-19a/b | ⚠️ ambiguo (**cómo se testea una puerta que vive en un comando** — ver Ambigüedad 1) |
| C-06 | Sección de especialización en `/doctor` (tres estados + biyección) | spec §Flujo 6; CA-20, CA-21 | ✅ |
| C-07 | Desambiguación con `plugin-dev` | spec §Modificado; CA-22 | ✅ |
| C-10 | `pieces-registry.py` — lock, hash, 3 estados, adopción, `GOT-003` | spec §Nuevo; CA-17, CA-23 a CA-26, CA-28 | ✅ (dueño y alcance cerrados; falta la **lista de campos**) |
| C-11 | Piezas de proyecto multi-runtime vía `export-interop.py --root` | spec §Piezas de proyecto multi-runtime; CA-28 a CA-30 | ⚠️ ambiguo (**la premisa técnica es falsa** — ver Ambigüedad 2) |
| ~~C-08~~ | ~~Deriva semántica + retirada~~ | spec §Fuera (esta iteración) | **diferida** |
| ~~C-09~~ | ~~Campo «Cuándo aplica»~~ | spec §Fuera (esta iteración) | **diferida** |

> Los IDs `C-08` y `C-09` **no se reutilizan** para las características nuevas: cada ID sigue
> significando lo mismo que en la pasada 1, para que esta evaluación y la anterior se puedan comparar
> sin traducir. De ahí que las nuevas sean `C-10` y `C-11` y que no haya `C-08`/`C-09` vivas.

**Ambigüedades / información que falta.** Todas quedan como supuestos explícitos; ninguna se cierra
inventando alcance.

1. **Una puerta que vive en un comando no se puede testear como un script** (nueva, y es la más
   material). CA-15 exige «test con lote de 3 candidatos que confirma 2 y rehúsa 1, y afirma que se
   escriben exactamente 2 piezas con sus 2 filas de registro». Un comando es **prosa para el modelo**:
   no tiene función que llamar ni exit code que afirmar. Para que CA-14 (`--dry-run`) y CA-15 (N
   confirmaciones) sean verificables, la mecánica del lote —previsualizar, aplicar la pieza *i*,
   omitir la *j*— tiene que vivir en un **script** (lo natural: `pieces-registry.py`, C-10) y el
   comando solo secuenciar. Impacto en horas: **bajo si se decide antes de abrir tareas**; alto si se
   descubre a mitad de C-05, porque mueve código entre dos características. Lo cierra el `planner`.
2. **`export-interop.py --root` no funciona hoy sobre un árbol de proyecto** (nueva; la spec lo da
   por «verificado» y **no lo está**). Lo verificado de verdad es que los tres flags existen
   (`scripts/export-interop.py:512-515` ✅). Lo que falla es el resto:

   ```
   $ python3 scripts/export-interop.py --list --root <árbol con agents/ commands/ skills/>
   ERROR: no pude leer las piezas del plugin en … ([Errno 2] … '.claude-plugin\plugin.json')
   $ echo $?
   1
   ```

   `generar(root)` (líneas 458-476) exige **cuatro ficheros que un `.claude/` de consumidor no
   tiene**: `.claude-plugin/plugin.json` (:246), `.claude-plugin/marketplace.json` (:275-276),
   `hooks/hooks.json` (:303) y `hooks/opencode-plugin.js` (:474-475). Y aunque los tuviera, **escribe
   en `interop/…` y `.codex-plugin/…`**, no en `.codex/` y `.opencode/` como pide CA-29. Es decir:
   `--root` es genérico sobre árboles **con forma de plugin**, y un proyecto especializado no la
   tiene. C-11 incluye por tanto un **modo proyecto** en `export-interop.py`, no solo una fila de
   doc. Presupuestado así (4,5 h) y con confianza **Baja**.
3. **Lista de campos de `pieces.json`.** La spec cierra la semántica (una fila por pieza, hash,
   estado, evidencia, ruta, rutas por runtime) pero no el nombre de cada campo. Ya **no** es un riesgo
   de proceso: ahora tiene dueño (`pieces-registry.py`) y un test que lo fija. Impacto: bajo.
4. **Dónde vive el tope de 5.** Se presupuesta `.claude/dev.json`; la spec lo declara supuesto.
5. **`/setup` ofrece `/specialize`.** Sin fase asignada en el checklist; se presupuesta dentro de
   C-05 (como en la pasada 1).
6. **El criterio de éxito es diferido por diseño** (CA-34). No es una laguna: la spec nombra el punto
   de control (las retros de las dos iniciativas siguientes) y el mecanismo (la traza «Revisión de dos
   lentes — intento N» que `tasks.md` ya deja). Se acepta por escrito, no se presupuesta como métrica.

---

## Datos necesarios para una evaluación completa

- [x] **Requerimientos** completos y sin ambigüedades — `spec.md` reescrita sobre `analysis.md`, con
  **10 decisiones confirmadas** en su pasada 2 y anti-alcance explícito
- [x] **Alcance** de cada característica acotado — «Dentro» y «Fuera (diferido)» separados de «Fuera
  (anti-alcance, nunca)», que es más de lo que suele llegar
- [x] **Criterios de aceptación / éxito** por característica — **34 `CA-XX`**, cada uno con su
  comando de verificación (eran 28 en la pasada 1)
- [ ] **Restricciones** (deadline, presupuesto, compliance) — **no hay deadline ni techo declarado**;
  se presupuesta sin restricción temporal
- [ ] **Dependencias externas** — ninguna nueva, **pero** una dependencia interna dada por buena que
  no lo está: `export-interop.py --root` sobre árbol de proyecto (Ambigüedad 2, verificado con exit 1)
- [x] **Contexto técnico** disponible — repo propio; hoy **9 agentes, 17 skills y 12 comandos**
  instalados (comprobado, y es la cifra que CA-13 usa)
- [x] **Tarifa/hora y supuestos de coste** confirmados — `.claude/rates.json`, verificado el
  2026-08-18 (22 días, < 90 ⇒ fiable)

---

## Supuestos económicos (ajustables)

**Coste = (horas × tarifa) + coste de tokens de IA.** Importes en **EUR**. Todos los valores salen de
`.claude/rates.json` y `docs/roadmap/CALIBRATION.md`; **ninguno está inventado**. Sin cambios respecto
a la pasada 1, para que el delta sea de alcance y no de parámetros.

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | **50 €/h** | `rates.json` `tarifaHora` |
| Modelo IA asumido | **claude-opus-4-8** | `rates.json` `modeloIA` |
| Precio input | **4,60 €** / 1M tokens | 5 USD/M × 0,92 · verificado el **2026-08-18** |
| Precio output | **23,00 €** / 1M tokens | 25 USD/M × 0,92 · verificado el 2026-08-18 |
| Precio creación de caché | **5,75 €** / 1M tokens | 6,25 USD/M × 0,92 |
| Precio lectura de caché | **0,46 €** / 1M tokens | 0,50 USD/M × 0,92 |
| Tipo de cambio | 1 USD = **0,92 €** | `rates.json` `tipoCambioUsdEur` — **SUPUESTO fijo, no verificado**; revisar antes de facturar |
| Ratio de supervisión | **25 %** de las horas IA | `rates.json` `ratioSupervision` |
| Margen de contingencia | **20 %** | `rates.json` `margenContingencia`; sobre horas base (humanas e IA) |
| Jornada | **8 h** | `rates.json` `horasJornada` |
| Horas por empleado-mes (FTE) | **160 h** | `rates.json` `horasMesFTE` |
| Ratio tokens → hora IA | **479.326 tok/h** | `CALIBRATION.md`, **mediana de 5 muestras medidas** (precedencia sobre el default no calibrado de 300.000) |

**Lo que NO se presupuesta, y se dice:** la **lectura de caché**. Queda fuera del cálculo de horas por
definición (`CALIBRATION.md`: mide longitud de sesión, no trabajo), pero se factura a 0,46 €/M y en
las 5 iniciativas medidas fue **la mayor parte de los 12,35 €** totales. Los **16,61 €** de tokens de
este presupuesto son por tanto una **cota inferior** del gasto real en API.

**Coste de este re-presupuesto, sin contarlo dos veces.** El bloque `generacion:` de arriba mide
**solo** la ventana de esta pasada (08:48:07 →), que **no solapa** con la de la pasada 1
(08:04:58 → 08:17:19) ni con la reescritura de la spec (08:38:50 → 08:45:34, medida en su propio
frontmatter). Lo que se anota es el **incremento** (`incremento: true`), no el acumulado: quien sume
los tres bloques obtiene el coste total de la iniciativa hasta hoy sin duplicar ninguna ventana.

---

## Las lecciones de calibración de este repo, APLICADAS

| Lección medida | Efecto en ESTA estimación |
|---|---|
| **La prosa pura se estima en minutos, no en horas** (`LES-004`; desviaciones de −96 % a −77 % en 5 muestras) | C-02 y C-07 llevan horas IA en centésimas (0,27 + 0,11 = 0,38 h). Lo que queda ahí son horas **humanas** de redacción y espejo EN. Nota honesta: al salir C-09, el lote pierde su característica más barata y el promedio por característica sube — no porque cada una cueste más |
| **Una tarea con tests reales cuesta ~×2 respecto a una de prosa** (`LES-005`; `subagent-personas`, 65.711 tokens medidos) | Las **seis** con suite nueva o ampliada (C-03, C-04, C-05, C-06, C-10, C-11) concentran **1.101k de los 1.898k tokens** (58,0 %) y **29,5 de las 47 h base**. Eran cuatro en la pasada 1 |
| **La revisión de dos lentes va como línea de presupuesto aparte** (`LES-001`, `LES-009`) | Línea propia: **5 h · 0,59 h IA · 281k tok · 252 €** |
| **La corrección post-revisión va como línea propia, igual a la de revisión** (`CALIBRATION.md` 2026-09-08: `memory-retrieval`, 3 revisiones, **38 gaps (3 Critical)**, +66 % en horas IA) | **5 h · 0,51 h IA · 244k tok · 252 €**. Las dos líneas suben de 8 h a 10 h porque escalan con las horas de característica (se mantiene el 27 %) y porque hay **34 CA** que la lente A tiene que recorrer, no 28 |
| **Una spec previa reduce el coste de implementación de forma medible** (`LES-006`; `quick-implement`, −77 %, única muestra) | Esta iniciativa tiene `analysis.md` + una spec **de segunda pasada** con 34 CA verificables y 10 decisiones cerradas: las horas IA van sin colchón de exploración. El descuento se declara respaldado por **una** muestra, no por cinco |
| **El default de 300.000 tok/h subestima el ritmo real ~1,6×** (aprendizaje 1) | Se usa la mediana medida. Con el default, los mismos 1.898k tokens darían **6,33 h IA** en vez de 3,96 h: 2,37 h que irían directas al worklog |
| **Estimar por analogía con «iniciativas con código» infla las de prosa** (aprendizaje 5) | Las 9 se clasifican en **tres tamaños**: script + suite nueva (C-03, C-04, C-10, C-11), comando/integración con tests (C-05, C-06), cambio quirúrgico o prosa (C-01, C-02, C-07) |
| **Separa lo que mides de lo que vendes** (`LES-007`) | El ×9,5 lleva su párrafo de advertencia en §Productividad, y el coste de generar este documento va aparte en `generacion:` — marcado `estimado` porque `usage-meter.py` degradó, y marcado `incremento` para no acumular la ventana de la pasada 1 |
| **Presupuesta el coste de proceso aparte** (`LES-008`) | Las dos líneas transversales son **21,3 %** de las horas base y **22,2 %** de los tokens. Se declaran como línea, no se reparten dentro de las características para que parezcan más baratas |

---

## Evaluación por característica

### C-01 — Cascada de personas de proyecto en `task-brief.py`

- **Requisito origen**: spec §Alcance F1; CA-01 a CA-04.
- **Descripción**: `--personas-dir` deja de ser **un solo directorio** (`task-brief.py`, 620 líneas;
  resolución en 481-482 y 526-528) y pasa a cascada de tres escalones:
  `.claude/personas/<tipo>.md` → `agent-kits/shared/personas/<tipo>.md` → genérico con aviso. Tipos
  extensibles más allá de los 6. Es **la característica que hace que todo lo demás sirva de algo**.
- **Complejidad**: **Media** (tres escalones, degradación con exit 0, y la garantía de que el
  comportamiento de hoy no cambie cuando el proyecto no tiene la carpeta).
- **Esfuerzo**: **2,5 h** · confianza Media. **Sin cambio** frente a la pasada 1.
- **Previsión IA**: 70.000 in / 20.000 out tok · **0,78 €** · 0,19 h IA.
- **Coste**: (2,5 h × 50 €/h) + 0,78 € = **126 €**.
- **Impacto / áreas afectadas**: `agent-kits/shared/task-brief.py`, `test_task_brief.py`,
  `docs/observability.md` (+EN, si se documenta la cascada).
- **Dependencias**: **ninguna**. Por eso va primera.
- **Riesgos**: romper el camino actual de los 6 tipos (mitigado por CA-02: la suite previa sigue verde
  **sin tocar sus asserts**); contaminar stdout con el aviso de degradación en un script que compone
  el brief (patrón ya resuelto en el repo: va a `stderr`).
- **Incógnitas**: si el tope de la casilla de persona (hoy 9 líneas de facto, sin constante) debe
  hacerse explícito. La spec no lo exige.

### C-02 — Doc del bucle: `SPECIALIZATION.md` (+EN), FLOWS y ROLES

- **Requisito origen**: spec §Alcance F1; CA-05, CA-06, CA-07.
- **Descripción**: `docs/SPECIALIZATION.md` como **única puerta de entrada** del tercer bucle, con
  espejo en `docs/en/`; sección nueva en `docs/FLOWS.md` (+EN) con el diagrama; filas en
  `docs/agents/ROLES.md` con DECIDE/ESCRIBE/LEE y el invariante de dirección.
- **Complejidad**: **Baja** (prosa + espejo bilingüe; el diagrama ya está escrito en el análisis).
- **Esfuerzo**: **3,5 h** (era 3,0 h) · confianza Media. **Δ +0,5 h**: CA-05 ahora enumera **seis**
  cosas de las que el documento es fuente única — registro, escalera, las dos puertas, invariante de
  dirección, **los tres estados por hash** y **el límite explícito a F1+F2** —, y todas van ×2 idiomas.
- **Previsión IA**: 95.000 in / 35.000 out tok · **1,24 €** · 0,27 h IA.
- **Coste**: (3,5 h × 50) + 1,24 € = **176 €**.
- **Impacto / áreas afectadas**: `docs/SPECIALIZATION.md`, `docs/en/SPECIALIZATION.md`,
  `docs/FLOWS.md`, `docs/en/FLOWS.md`, `docs/agents/ROLES.md`, `docs/README.md` (+EN).
- **Dependencias**: conviene **después** de C-01 (documentar la cascada ya real), pero no la bloquea.
- **Riesgos**: espejo EN que se queda atrás (regla bilingüe); mermaid que rompe
  `tests/test_mermaid_blocks.py`. Ambos con test o linter que los caza.
- **Incógnitas**: ninguna material.

### C-03 — `project-scan.py`: la evidencia, por composición (y su privacidad)

- **Requisito origen**: spec §Flujo 1; CA-08, CA-09, CA-10 y **CA-27** (privacidad).
- **Descripción**: compone cuatro fuentes que **ya existen** —`deps-inventory.py`, `code-health.py`,
  `coverage-gate.py` y `knowledge-find.py --json`— y emite candidatos donde cada uno cita
  `fichero:línea` **o** el ID de una entrada de memoria. Nuevo en esta pasada: la regla de evidencia es
  **una de las dos formas**, no las dos; con 0 aciertos de memoria el aviso lo dice explícitamente; y
  todo lo citado pasa por `redactar()` (`agent-kits/shared/journal.py:200`, con
  `REDACTADO` en :121) y **nunca** cita nada bajo `docs/security-scan/`.
- **Complejidad**: **Alta** — no por el algoritmo, sino por las **cuatro degradaciones
  independientes** (sin git, sin gestor de paquetes en PATH, sin stack de test, `docs/knowledge/`
  vacío), cada una con su aviso y sin inventar dato, **más** el camino de redacción.
- **Esfuerzo**: **6,0 h** (era 5,0 h) · confianza Media. **Δ +1,0 h**: la regla de evidencia en dos
  formas con su test, el aviso explícito de 0 aciertos, un **segundo árbol fixture** sin
  `docs/knowledge/` (la suite de este repo no tiene hoy ese patrón para escaneos) y CA-27.
- **Previsión IA**: 165.000 in / 48.000 out tok · **1,86 €** · 0,44 h IA.
- **Coste**: (6,0 h × 50) + 1,86 € = **302 €**.
- **Impacto / áreas afectadas**: script nuevo en el kit compartido, `tests/test_project_scan.py`
  (nuevo), `tests/test_console_encoding.py` (lo descubre por `GOT-005`), doc de la pieza.
- **Dependencias**: ninguna dura; **C-05 la necesita**. Reutiliza `redactar()` de `journal.py`
  (no se reimplementa la heurística de secretos).
- **Riesgos**: que la composición se convierta en escáner propio por la puerta de atrás (mitigado por
  CA-10, que es un `grep` de las cuatro invocaciones); que los cuatro sub-scripts devuelvan formatos
  que no casan y aparezca un normalizador no presupuestado; en un consumidor sin memoria la salida es
  pobre — y hay que decirlo, no disimularlo (por eso CA-09 exige el texto del aviso).
- **Incógnitas**: cuánto tarda `code-health.py` en un repo grande. Si el escaneo se vuelve lento,
  `--baseline` y caché resuelven, pero **no están presupuestados**.

### C-04 — `role-collision.py`: la puerta que salva `ADR-011`, ahora con contrato

- **Requisito origen**: spec §Flujo 2; CA-11, CA-12, CA-13.
- **Descripción**: generaliza la heurística que `lint_plugin.py` ya aplica al plugin (dos piezas con el
  mismo disparador literal entrecomillado → aviso), comparando el candidato contra las piezas
  **realmente instaladas** (comprobado hoy: **9 agentes, 17 skills, 12 comandos**) y contra las filas
  del registro. Rechaza por nombre los cuatro clásicos —`test-writer`, `code-reviewer`,
  `security-auditor`, `doc-writer`—, que ya tienen dueño aquí. **Nuevo**: contrato de salida — exit 0
  sin colisión, exit 1 con ella, y **una línea** `pieza instalada · disparador que choca · motivo`.
- **Complejidad**: **Media** (heurística conocida, inventario descubierto con el `find` de la regla 5).
- **Esfuerzo**: **3,5 h** (era 3,0 h) · confianza **Alta** (era Media). **Δ +0,5 h** por el test que
  parsea el formato y afirma **ambos** exit codes; y **Δ confianza al alza** porque CA-12 cierra
  justo la incógnita que la pasada 1 dejaba abierta («¿exit ≠ 0 o campo JSON?»). Más trabajo definido,
  menos riesgo: es el caso de manual en el que subir horas **baja** el riesgo.
- **Previsión IA**: 105.000 in / 33.000 out tok · **1,24 €** · 0,29 h IA.
- **Coste**: (3,5 h × 50) + 1,24 € = **176 €**.
- **Impacto / áreas afectadas**: script nuevo, `tests/test_role_collision.py` (nuevo), doc.
- **Dependencias**: ninguna; **C-05 no debe entregarse sin ella** (condición del análisis: «sin ella,
  no vale construir esto»).
- **Riesgos**: falsos positivos que bloqueen piezas legítimas (el repo ya lo vivió: el linter de
  «nombre genérico» necesitó afinado en `debt-cleanup`); falsos negativos por sinónimos que no
  comparten literal. Mitigación: es **aviso + veredicto** con la puerta humana detrás, no un deny.
- **Incógnitas**: ninguna material — las cerró CA-12.

### C-05 — `/specialize <área>`: la escalera y las dos puertas

- **Requisito origen**: spec §Flujo 3-4; CA-14, CA-15, CA-16, CA-18, CA-19a, CA-19b (y CA-17
  compartido con C-10).
- **Descripción**: el comando — escalera de decisión (nada → persona → tool → skill → agente), puerta
  de colisión, **previsualización del lote completo con `--dry-run`/`--plan`**, **N confirmaciones para
  N candidatos** (confirmar una no aprueba las demás; rehusar una omite solo esa), escritura de la
  pieza vía la API de C-10, caso de eval generado con ≥ 2 positivos y 1 negativo, validación con
  `lint_plugin.py --root` (:1130) y `evals/check.py --root` (:253), **tope de 5 acumulado en el
  registro** y `tools` mínimos con la distinción estático (19a) / comportamiento (19b).
- **Complejidad**: **Muy alta** — sigue siendo la más alta del lote. Cuatro formas de pieza, dos
  puertas separables, y el caso de `GOT-003` (el `.claude/` de destino puede ser **el árbol desplegado
  del propio plugin**, con rutas canónicas indistinguibles).
- **Esfuerzo**: **7,5 h** (era 7,0 h) · confianza **Baja**. **Δ +0,5 h neto**, y el neto engaña: la
  característica **pierde** toda la mecánica del registro (se va a C-10, −2 h aprox.) y **gana** las
  puertas nuevas (+2,5 h aprox.): `--dry-run` con test de árbol idéntico, el bucle de N
  confirmaciones con test de 3 candidatos (2 sí, 1 no), el tope acumulado con test de dos
  invocaciones, 19a/19b partidos y la confirmación extra sobre árbol de plugin.
- **Previsión IA**: 200.000 in / 62.000 out tok · **2,35 €** · 0,55 h IA.
- **Coste**: (7,5 h × 50) + 2,35 € = **377 €**.
- **Impacto / áreas afectadas**: `commands/specialize.md` (nuevo),
  `evals/cases/command-specialize.json` (nuevo), `commands/setup.md` (paso nuevo),
  `docs/CONVENTIONS.md` reglas 3 y 9, `docs/README.md` (+EN), `scripts/export-interop.py`
  (regeneración) e `interop/`.
- **Dependencias**: **requiere C-03, C-04 y ahora C-10** (consume su API en vez de escribir el
  registro). C-07 va pegada detrás.
- **Riesgos**: (a) **Ambigüedad 1** — si la mecánica del lote se queda en prosa del comando, CA-14 y
  CA-15 **no son testeables** y la lente A las marcará como gap; (b) `GOT-003`, la fuente más probable
  de un Critical en revisión; (c) privilegios de lo generado (`ADR-007`); (d) el comando puede crecer
  hasta ser inmantenible (`ADR-008`; `/dev-cycle` ya tuvo que bajar de 218 a 198 líneas).
- **Incógnitas**: si las evals generadas entran en la CI del consumidor o solo se validan al generar.

### C-06 — Sección de especialización en `/doctor`

- **Requisito origen**: spec §Flujo 6; CA-20, CA-21.
- **Descripción**: `doctor.py` (**1.084 líneas**, con `test_doctor.py` ya en pie) gana una sección con
  **una línea por fila del registro**: ✅ `gestionada` / ⚠️ `modificada` con su arreglo («revisa el
  diff y confirma») / ❌ fila sin fichero; y las piezas sin fila salen como **«no gestionada»**, que es
  un estado **válido** y ofrece adopción. Biyección registro ↔ ficheros con **mutante de hash**.
- **Complejidad**: **Media** (el patrón ya existe en el script; lo nuevo es el criterio de salud de
  tres estados y el mutante).
- **Esfuerzo**: **3,0 h** (era 2,5 h) · confianza Media. **Δ +0,5 h**: tres estados en vez de dos,
  «no gestionada» como no-error, y el **mutante de hash** además del mutante de fila.
- **Previsión IA**: 100.000 in / 28.000 out tok · **1,10 €** · 0,27 h IA.
- **Coste**: (3,0 h × 50) + 1,10 € = **151 €**.
- **Impacto / áreas afectadas**: `agent-kits/shared/doctor.py`, `agent-kits/shared/test_doctor.py`,
  `commands/doctor.md`, doc de `/doctor`.
- **Dependencias**: **requiere el registro de C-10** (no hay qué auditar sin filas). Ya no depende de
  C-05 para el esquema, que es una mejora del grafo respecto a la pasada 1.
- **Riesgos**: que la sección salga ✅ con el registro vacío y dé **falsa seguridad** — es exactamente
  el defecto que `memory-retrieval` encontró en `/doctor` («Instalación sana» con 0 entradas de
  journal). Mitigación: criterio explícito para «sin registro» distinto de «registro sano».
- **Incógnitas**: ninguna material — «pieza muerta» ya no se decide aquí (era C-08, diferida).

### C-07 — Desambiguación con `plugin-dev`

- **Requisito origen**: spec §Modificado; CA-22.
- **Descripción**: la `description` de `plugin-dev` promete hoy literalmente «crea un agente/skill/
  comando nuevo», que es **exactamente** el disparador de `/specialize`. Se reescribe para que diga
  «de ESTE plugin», con **negativos cruzados** en las evals de ambas piezas y fila «qué NO hace»
  apuntándose mutuamente.
- **Complejidad**: **Baja** (prosa + dos ficheros de casos), **efecto alto**: sin ella quedan dos
  meta-generadores compitiendo por la misma frase y el modelo elige mal.
- **Esfuerzo**: **1,5 h** · confianza **Alta**. **Sin cambio** frente a la pasada 1.
- **Previsión IA**: 40.000 in / 12.000 out tok · **0,46 €** · 0,11 h IA.
- **Coste**: (1,5 h × 50) + 0,46 € = **75 €**.
- **Impacto / áreas afectadas**: `skills/plugin-dev/SKILL.md`, `evals/cases/skill-plugin-dev.json`,
  `evals/cases/command-specialize.json`, `interop/` (regeneración).
- **Dependencias**: el caso de eval de `/specialize` lo crea C-05, así que va **pegada detrás**.
- **Riesgos**: que se despache como cosmética. `evals/check.py` exige que el literal case con la
  description real, así que el linter no la deja a medias (`LES-011`).
- **Incógnitas**: ninguna.

### C-10 — `pieces-registry.py`: el registro como pieza determinista (NUEVA)

- **Requisito origen**: spec §Nuevo («la pieza determinista que hace verificables la idempotencia, la
  concurrencia y "modificada" sin ponerlas en prosa del agente»); CA-17, CA-23, CA-24, CA-25, CA-26,
  CA-28.
- **Descripción**: lectura/escritura de `.claude/pieces.json` (+ `pieces-state.json`) **bajo lock**
  (`pieces.json.lock`, hermano del fichero, mismo idioma que los logs de sesión de `journal.py`),
  cálculo de hash, los **tres estados** (`gestionada` / `modificada` / `no gestionada`), **modo de
  adopción** (`--adopt`: fila con el hash **actual**, anotada `modificada` porque no hay generación de
  referencia), la **regla dura de `GOT-003`** (propiedad = registro + hash, **nunca** carpeta; rehúsa
  escribir o retirar lo que no tenga fila con hash coincidente; confirmación **extra** si el destino
  tiene marcadores `agent-kits/` o `.claude-plugin/` en su raíz) y las **filas por runtime** de CA-28.
- **Complejidad**: **Alta**. No por el algoritmo —hashear y escribir JSON es barato— sino por el
  **conjunto de propiedades que tiene que garantizar a la vez**: concurrencia sin corromper el JSON,
  idempotencia real, y una regla de propiedad cuyo fallo escribe en el árbol del propio plugin.
- **Esfuerzo**: **5,0 h** · confianza Media. **Dimensionado contra sus hermanos del kit, no a ojo**:
  los scripts deterministas de `agent-kits/shared/` miden 187-495 líneas (mediana **371**) con suites
  de 167-416 líneas y 10-44 tests. Los dos que también hacen lock o estado son los mayores del rango:
  `guardrail-check.py` (419 líneas / 326 de test / 31 tests) y `usage-meter.py` (495 / 416 / 28).
  `pieces-registry.py` cae ahí: ~400 líneas y ~25-30 tests.
- **Previsión IA**: 145.000 in / 45.000 out tok · **1,70 €** · 0,40 h IA.
- **Coste**: (5,0 h × 50) + 1,70 € = **252 €**.
- **Impacto / áreas afectadas**: `agent-kits/shared/pieces-registry.py` (nuevo),
  `agent-kits/shared/test_pieces_registry.py` (nuevo), `docs/CONVENTIONS.md` regla 9 (fila
  `pieces.json` config-comiteada / `pieces-state.json` estado-ignorado), `.gitignore`,
  `tests/test_console_encoding.py` (`GOT-005`).
- **Dependencias**: **ninguna**, y eso es lo valioso: es la **raíz** del subgrafo de F2. C-05 y C-06
  la consumen.
- **Riesgos**: (a) el lock por fichero es la parte que más fácilmente queda **verde en el test y roto
  en la práctica** — el repo ya pagó esto en `debt-cleanup` (el debounce de la línea de progreso tuvo
  que rehacerse con `flock` + rename atómico), así que el test de concurrencia tiene que ser real, no
  un `assert True`; (b) en Windows no hay `flock` — el patrón atómico del repo es `rename`, y esa
  degradación hay que escribirla; (c) si la lista de campos se queda corta, C-11 (rutas por runtime)
  fuerza una migración del registro a mitad de fase.
- **Incógnitas**: si `pieces-state.json` llega a tener contenido en esta iteración o nace vacío por
  simetría con `usage-state.json`. No cambia las horas.

### C-11 — Piezas de proyecto multi-runtime (NUEVA)

- **Requisito origen**: spec §Piezas de proyecto multi-runtime (requisito explícito del usuario:
  «esto no es solo para Claude Code»); CA-28, CA-29, CA-30.
- **Descripción**: `/specialize` escribe **siempre** en formato canónico de Claude Code y **no sabe de
  runtimes**; la traducción la hace `export-interop.py --root <proyecto>`, que genera las variantes de
  `.codex/` y `.opencode/` igual que el plugin ya hace consigo mismo, y `--check` detecta la
  desincronización. El registro anota **cada ruta escrita por runtime con su propio hash**. Fila nueva
  en la tabla de degradación de `docs/INTEROP.md` §4 (+ espejo EN) con el **límite honesto** escrito.
  **Portabilidad por escalón**: persona/tool neutrales, skill viaja sin traducir (con el techo de
  1.024 caracteres de `description` que OpenCode impone), agente **exige** traducción real.
- **Complejidad**: **Alta**, y por un motivo que la spec no anticipa. Lo verificado de la premisa es
  solo que los flags existen (`scripts/export-interop.py:512-515`). Lo demás **no se sostiene** y está
  medido en §Ambigüedad 2: `generar(root)` exige cuatro ficheros que un `.claude/` de consumidor no
  tiene y **escribe en `interop/` y `.codex-plugin/`**, no en `.codex/`/`.opencode/`. C-11 incluye por
  tanto un **modo proyecto** en `export-interop.py` (plan de salida distinto + tolerancia a manifiestos
  y hooks ausentes), no solo una fila de documentación.
- **Esfuerzo**: **4,5 h** · confianza **Baja**. Reparto: **~2,0 h** el modo proyecto en
  `export-interop.py` (531 líneas hoy); **~1,5 h** los casos nuevos de `tests/test_export_interop.py`
  — que hoy tiene **245 líneas y 17 tests, todos sobre el árbol real del repo y ni un `tmp_path`**, así
  que un caso sobre árbol de proyecto **estrena patrón de fixture** en esa suite; **~0,5 h** las filas
  por runtime en el registro (apoyadas en C-10); **~0,5 h** la fila de `docs/INTEROP.md` §4 (tabla en
  las líneas 112-129, con el precedente del guardrail del `implementer` en la 127) y su espejo
  `docs/en/INTEROP.md`.
- **Previsión IA**: 130.000 in / 40.000 out tok · **1,52 €** · 0,35 h IA.
- **Coste**: (4,5 h × 50) + 1,52 € = **227 €**.
- **Impacto / áreas afectadas**: `scripts/export-interop.py`, `tests/test_export_interop.py`,
  `docs/INTEROP.md`, `docs/en/INTEROP.md`, esquema del registro (C-10), `interop/` (regeneración).
- **Dependencias**: **requiere C-10** (las filas por runtime son filas del registro). No la requiere
  C-05, y ese es precisamente el invariante: `/specialize` no sabe de runtimes.
- **Riesgos**: (a) **la premisa corregida** — si el `planner` abre tareas creyendo que `--root` ya
  vale, la fase se lleva la sorpresa en la primera tarea; (b) **el límite honesto no es un defecto, es
  la naturaleza del medio**: la puerta de confirmación humana de `/specialize` es un **comando**, y
  fuera de Claude Code un comando se traduce a *prompt* — depende de que el runtime lo **respete**, no
  de una barrera técnica. Misma clase de degradación que `docs/INTEROP.md` ya documenta para el
  guardrail del `implementer` (línea 127). Va como **riesgo escrito, no como promesa**, y CA-30 obliga
  a escribirlo en la tabla; (c) tocar `export-interop.py` obliga a regenerar `interop/` y a que
  `--check` siga verde en CI y en `release.py`.
- **Incógnitas**: si el modo proyecto es un flag nuevo (`--project`) o se infiere de la ausencia de
  `.claude-plugin/`. Inferirlo es más elegante y más frágil; lo cierra el `planner`. **Ninguna de las
  dos opciones cambia las 4,5 h.**

### Diferidas (presupuestadas en la pasada 1, fuera del total de esta)

- **C-08 — deriva semántica + retirada** (era 4,0 h · 201 € · 145k tok · complejidad Alta · confianza
  Baja). Sale por decisión de la spec: F2 ya entrega su auditoría **mecánica** vía `/doctor`, así que
  diferir la **semántica** no deja ningún estadio del ciclo de vida sin dueño. Se retoma como
  iniciativa propia cuando haya datos del criterio de éxito (CA-34).
- **C-09 — campo «Cuándo aplica»** (era 1,0 h · 50 € · 38k tok). Sale **junto con** C-08 y por el
  motivo correcto: sin el estadio que lo lee, ningún código consume ese campo. La pasada 1 lo
  recomendaba como quick win «para que F3 arranque menos vacía»; **esa recomendación queda revocada**,
  porque un campo que nadie consume es exactamente la pieza muerta que esta iniciativa nació para
  evitar. Barato no es lo mismo que útil.

> Las dos siguen presupuestadas aquí a propósito: cuando se retomen, el punto de partida es este, no
> una estimación desde cero. **Diferido, no descartado.**

---

## Comparativa

Ordenada por **fase y dependencia**, que es el orden en el que se recomienda ejecutar.

| # | Característica | Complejidad | Horas | Coste € | Tokens | Prioridad | Confianza |
|---|---------------|-------------|-------|---------|--------|-----------|-----------|
| C-01 | Cascada de personas en el brief (F1) | Media | 2,5 h | 126 € | 90k | **Crítica** | Media |
| C-02 | Doc del bucle: SPECIALIZATION + FLOWS + ROLES (F1) | Baja | 3,5 h | 176 € | 130k | Alta | Media |
| C-10 | `pieces-registry.py` — registro, lock, hash, 3 estados (F2) | **Alta** | 5,0 h | 252 € | 190k | **Crítica** | Media |
| C-03 | `project-scan.py` — compositor + privacidad (F2) | **Alta** | 6,0 h | 302 € | 213k | Alta | Media |
| C-04 | `role-collision.py` — puerta con contrato (F2) | Media | 3,5 h | 176 € | 138k | **Crítica** | **Alta** |
| C-05 | `/specialize <área>` — escalera y dos puertas (F2) | **Muy alta** | 7,5 h | 377 € | 262k | Alta | **Baja** |
| C-07 | Desambiguación con `plugin-dev` (F2) | Baja | 1,5 h | 75 € | 52k | **Crítica** | **Alta** |
| C-06 | Sección de especialización en `/doctor` (F2) | Media | 3,0 h | 151 € | 128k | Alta | Media |
| C-11 | Piezas de proyecto multi-runtime (F2) | **Alta** | 4,5 h | 227 € | 170k | Media | **Baja** |
| — | **Revisión de dos lentes** (transversal, línea propia — `LES-001`/`LES-009`) | — | 5,0 h | 252 € | 281k | — | Media |
| — | **Corrección post-revisión** (transversal, línea propia — `CALIBRATION.md` 2026-09-08) | — | 5,0 h | 252 € | 244k | — | **Baja** |
| | **Total** | | **47,0 h** (base) | **2.367 €** (base) | **1.898k** | | |

**Subtotales por fase (base):** F1 = 6,0 h · 302 € · 220k · **rinde sola**. F2 = 31,0 h · 1.560 € ·
1.153k. Proceso = 10,0 h · 504 € · 525k. **F3 = 0** (diferida).

> Las dos últimas filas **no son características**: son las líneas que `CALIBRATION.md` obliga a poner
> aparte. Suman el **21,3 %** de las horas base, el **21,3 %** del coste base y el **27,7 %** de los
> tokens. Suben de 8 h a 10 h con las horas de característica; **recortarlas para «financiar»
> alcance es exactamente el error que este repo midió el 2026-09-08**.

---

## Presupuesto total

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 47,0 h × 50 €/h | 2.350,00 € |
| Margen de contingencia | +20 % sobre desarrollo base | 470,00 € |
| Tokens IA (input) | 1.470.000 tok × 4,60 €/1M | 6,76 € |
| Tokens IA (output) | 428.000 tok × 23,00 €/1M | 9,84 € |
| **Total estimado (con margen)** | | **2.836,61 €** |

- El margen del 20 % se aplica sobre las **horas** base (humanas e IA), como manda `rates.json`; los
  tokens van **sin** margen y se declara.
- **Lectura de caché no presupuestada** (ver §Supuestos): los 16,61 € son cota **inferior**.
- **Contra la pasada 1**: 2.263,52 € → 2.836,61 € (**+573,09 €**, +25,3 %).

---

## Productividad IA (humano vs. IA)

| KPI | Valor |
|-----|-------|
| Horas humanas estimadas | **56,4 h** (47,0 h base +20 %) |
| Horas IA (ejecución) | **4,75 h** (3,96 h base +20 %) |
| Supervisión humana | **1,19 h** (0,99 h base +20 %) |
| **Horas totales (IA + supervisión)** | **5,94 h** |
| Horas ahorradas | 50,46 h |
| **Ahorro** | **89,5 %** |
| **Multiplicador de productividad** | **×9,5** |
| FTE equivalentes | 0,32 |

> Horas mostradas **con el margen de contingencia (+20 %)** ya aplicado sobre las horas base. La
> supervisión base es el 25 % de las horas IA (0,99 h de 3,96 h), según `rates.json`.

**Lo que este multiplicador NO dice** (`LES-007`, «separa lo que mides de lo que vendes», y
`CALIBRATION.md` aprendizaje 2): las 56,4 h humanas **no las respalda ninguna muestra** — las 8 filas
medidas tienen **0 h humanas reales**, porque el trabajo lo hizo la IA con supervisión conversacional.
El ×9,5 compara una **estimación** (humano) con otra **estimación anclada en medición** (IA); no es un
plazo que se pueda prometer. Y el aviso sigue fresco: la última fila medida (`memory-retrieval`,
2026-09-08) se desvió **+66 %** en horas IA sobre lo estimado, por la revisión — que aquí ya va
presupuestada dos veces, revisar y corregir. Que el multiplicador apenas se mueva (×9,4 → ×9,5) pese a
un +25 % de presupuesto es la prueba de que **es un ratio entre dos estimaciones que escalan juntas**,
no una medida de nada.

---

## Recomendación

- **Veredicto**: **go por tramos** — F1 ya, F2 condicionada. Se mantiene el veredicto de la pasada 1,
  y **cambia una de sus condiciones a mejor**. Cuatro razones con su evidencia:
  1. **El recorte de F3 hizo la iniciativa más cara, no más barata** (+25 %). Eso no invalida el
     recorte —los motivos de la spec son buenos y F2 ya cierra su propio estadio de auditoría— pero
     **sí obliga a aprobar sabiendo el número nuevo**: 56,4 h y 2.837 €, no 45,0 h y 2.264 €. Si el
     go de la pasada 1 se dio contra un techo mental de ~2.300 €, este es el momento de decirlo.
  2. **Lo que se compra con el +25 % es verificabilidad, no alcance.** Cinco características suben
     entre 0,5 h y 1,0 h y ninguna crece de superficie: crecen de **contrato**. El caso limpio es
     C-04, que sube 0,5 h y **sube de confianza** (Media → Alta) porque CA-12 cierra la incógnita que
     la pasada 1 dejaba abierta. Un presupuesto que sube y baja el riesgo a la vez es un presupuesto
     mejor, no peor.
  3. **El grafo de dependencias mejoró.** `pieces-registry.py` (C-10) es una **raíz sin
     dependencias** que C-05 y C-06 consumen. Antes, C-06 esperaba a C-05 para tener esquema; ahora
     las dos esperan a una pieza determinista con tests. Eso es paralelizable y auditable.
  4. **El bucle trae su propio criterio de retirada** (spec §Criterio de éxito): si tras dos o tres
     iniciativas los intentos de revisión no bajan y siguen los mismos gaps, la capa se retira. La
     apuesta sigue siendo reversible, y ahora con punto de control **nombrado** (CA-34) en vez de
     vago.
- **Quick wins** (bajo coste, alto valor): **C-07** (1,5 h, 75 €, evita que dos meta-generadores se
  peleen por la misma frase) y **C-01** (2,5 h, 126 €, es la que hace útil todo lo demás y no depende
  de nada). **Ya no se recomienda C-09 como quick win**: era el más barato del lote y la pasada 1 lo
  ponía primero, pero la spec tiene razón al diferirlo — sin C-08 nadie lee ese campo.
- **Costosas / a valorar**: **C-05** (7,5 h, 377 €, complejidad Muy alta, confianza Baja) sigue siendo
  la más cara y la candidata natural a concentrar los Critical de la revisión. **C-03** (6,0 h, 302 €)
  es la segunda. **C-11** (4,5 h, 227 €) es la que **más puede desviarse en porcentaje**, porque su
  premisa venía dada por buena y no lo estaba.
- **Orden sugerido**: **C-01 → C-02** (F1, 6,0 h base) y luego **C-10 → C-03 → C-04 → C-05 → C-07 →
  C-06 → C-11** (F2, 31,0 h base). Motivos: C-01 antes de documentar; **C-10 abre F2** porque es la
  raíz del subgrafo y quien fija el esquema con tests; C-03 y C-04 antes de C-05 porque son sus
  insumos; **C-04 y C-07 son innegociables dentro de F2**; **C-06 después de C-10** (ya no espera a
  C-05); y **C-11 al final**, porque es la única cuya premisa hay que corregir antes de tocar código
  y la única que puede quedar fuera sin dejar un estadio colgando.
- **Condiciones del go de F2** (la (a) es nueva respecto a la pasada 1):
  - **(a) `C-10` entra antes que `C-05` y `C-06`.** Sustituye a la condición anterior («el `planner`
    fija el esquema de `pieces.json` antes de abrir tareas de C-05»). Es una mejora real: aquello era
    un **deber de proceso** que alguien tenía que recordar; esto es una **arista del grafo** que el
    plan hace cumplir por orden de tareas. El `planner` ya no inventa esquema en prosa — fija la lista
    de campos **dentro** de C-10, donde hay un test que la sostiene.
  - **(b) `C-04` y `C-07` entran en el mismo tramo que `C-05`**, no después. Sin cambios: el análisis
    dice de la puerta de colisión «sin ella, no vale construir esto».
  - **(c) Las dos líneas de proceso no se recortan** para financiar características. Sin cambios, y
    reforzada: hay 34 CA que la lente A tiene que recorrer, no 28.
  - **(d) NUEVA — `C-11` no se abre sin decidir cómo aprende `export-interop.py` el modo proyecto.**
    Hoy, con `--root` sobre un árbol de consumidor, el script sale con **exit 1** (§Ambigüedad 2). Que
    quede decidido en el plan, no descubierto en la primera tarea.
- **Fuera de alcance recomendado**: mantener el **anti-alcance de la spec** tal cual (`/learn`,
  `/piece-drift`, agentes de dominio en el plugin, `skills/learned/`, generar agentes por defecto,
  proponer MCP, tocar las 6 personas del plugin) y **no** abrir el backfill de «Cuándo aplica».
  **Nota:** la fila del anti-alcance que excluía las piezas de proyecto de `export-interop.py` **ya no
  aplica** — la spec la retiró y su contenido es ahora C-11.
- **Opción de recorte, si el +25 % no pasa la puerta** (se ofrece, no se recomienda, porque C-11 es
  requisito explícito del usuario): partir **C-11** en «registro con filas por runtime + fila de
  `INTEROP.md` con el límite honesto escrito» (~1,0 h) y diferir el **modo proyecto** de
  `export-interop.py` (~3,5 h) hasta que exista un consumidor real con Codex u OpenCode instalados.
  Deja el total en **43,5 h base · 52,2 h con margen · 1.773k tokens · 2.626 €** y **no** deja ningún estadio
  colgando, porque `/specialize` ya no sabe de runtimes por diseño. Coste de la opción: la capacidad
  multi-runtime queda **declarada y no entregada**, que es justo el patrón que la spec critica.

---

## Riesgos transversales

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| **Las horas humanas no tienen ninguna muestra validada** (`CALIBRATION.md` aprendizaje 2; ahora son el **99,3 %** del coste base, peor que el 98,7 % de la pasada 1) | **Alta** | Alto | Confianza declarada **Baja** y el ×9,5 con su advertencia. Cerrar con `/retro` e intentar meter **la primera fila con horas humanas reales** del histórico. Sigue siendo el mayor agujero del presupuesto, y el recorte de alcance no lo ha tocado |
| **La revisión encuentra más de lo previsto** (precedente medido: `memory-retrieval`, 3 rondas, **38 gaps** (3 Critical), **+66 %** en horas IA) | **Alta** | Medio | Dos líneas propias (revisar **y** corregir), 21,3 % del presupuesto, subidas a 5 h + 5 h. Bucle acotado a 3 por `adversarial-review`. Con **34 CA** el recorrido de la lente A es más largo que en la pasada 1 |
| **`GOT-003`: el `.claude/` de destino puede ser el árbol desplegado del plugin** — un generador escribiendo donde él mismo espeja | **Media** | **Alto** | Propiedad por **registro + hash, nunca por carpeta** (CA-17), con dueño determinista (C-10) y confirmación **extra** si la raíz tiene marcadores `agent-kits/` o `.claude-plugin/`. Mejor cubierto que en la pasada 1, donde vivía en prosa de C-05 |
| **La premisa de C-11 era falsa y puede haber más premisas dadas por buenas** — `export-interop.py --root` sale con **exit 1** sobre un árbol de proyecto, pese a estar declarado «verificado» en la spec | **Alta** (ya materializado) | Medio | Verificado y corregido aquí, con comando y exit code. Condición (d) del go. Lección para el `planner`: los «(verificado)» de la spec se re-comprueban con un comando, no se heredan |
| **El límite honesto del multi-runtime: la puerta humana es un comando, y un comando es un *prompt* fuera de Claude Code** — depende de que el runtime lo respete, no de maquinaria | **Alta** | Medio | **Riesgo, no promesa**: CA-30 obliga a escribirlo en la tabla de degradación de `docs/INTEROP.md` §4 (+EN). Misma clase de degradación que la fila 127 ya documenta para el guardrail del `implementer`. No se «arregla» — se declara |
| **Una puerta que vive en prosa no se puede testear** (CA-14 y CA-15 exigen tests sobre el comportamiento de un comando) | **Alta** si no se decide en el plan | Medio | Ambigüedad 1: la mecánica del lote baja a script (`pieces-registry.py`) y el comando solo secuencia. Si no, los CA quedan «verdes por afirmación» y la lente A los marcará |
| **Dos meta-generadores por la misma frase** (`plugin-dev` promete literalmente «crea un agente/skill/comando nuevo») | **Alta** si C-07 no entra | Alto | C-07 con negativos **cruzados** en las evals; `evals/check.py` ata el literal a la description real (`LES-011`) |
| **El lock verde en el test y roto en la práctica** (precedente propio: el debounce de la línea de progreso tuvo que rehacerse con `flock` + rename atómico en `debt-cleanup`) | Media | **Alto** | Test de concurrencia **real** en C-10 (dos escrituras simultáneas → JSON válido con ambas filas, o la segunda esperando), y la degradación de Windows (sin `flock`) escrita |
| **Piezas generadas que inflan el arranque** (`skill-index.py`: `LIMITE_LINEAS = 45` / `LIMITE_CHARS = 3500`) | Media | Medio | Tope de 5 **acumulado en el registro** con el motivo escrito y confirmación extra al superarlo (CA-18). Mejor que la pasada 1, donde el tope era por invocación y se podía burlar llamando dos veces |
| **Privilegios de lo generado** (una pieza declara `tools`; un deny mal puesto rompe el ciclo) | Baja | **Alto** | `tools` mínimos por defecto, `Bash`/`Write` solo con confirmación **registrada en la fila**, deny **nunca** sin opt-in (`ADR-007`). CA-19a/19b separan lo estático de lo que hay que probar por comportamiento |
| **Vale poco en un proyecto sin historia** — el valor crece con la memoria acumulada | **Alta** (en consumidores nuevos) | Medio | Declarado en la spec y cubierto por CA-09: con `docs/knowledge/` vacío el escaneo funciona **solo con `fichero:línea`** y **lo dice**. En **este** repo (13 ADR, 8 gotchas, 15 lecciones) es donde más rinde |
| **El criterio de éxito es diferido**: la iniciativa entrega **capacidad**, no reducción de retrabajo demostrada | **Alta** (por diseño) | Medio | Aceptado por escrito en CA-34, con punto de control **nombrado** (las retros de las dos iniciativas siguientes) y mecanismo ya existente (la traza «Revisión de dos lentes — intento N»). Y respetar el criterio de retirada |
| `/specialize` creciendo hasta ser inmantenible (`ADR-008`; `/dev-cycle` tuvo que bajar de 218 a 198 líneas) | Media | Medio | Determinismo **fuera** del prompt: los veredictos en `project-scan.py`, `role-collision.py` y `pieces-registry.py`, con tests y exit codes; el comando solo secuencia. Esta pasada mueve **más** lógica a script que la anterior |

---

## Siguiente paso

Para **ejecutar** lo aprobado, genera el plan detallado con el agente **`planner`** (añadirá
`improvement-plan.md` + `tasks.md` a `docs/roadmap/2026-09-09-project-specialization/` y rellenará la
fila **Plan** de esta evaluación y el campo `plan:` de la spec).

Aprobación recomendada: **C-01 → C-02** (F1, 6,0 h base) y **C-10 → C-03 → C-04 → C-05 → C-07 → C-06
→ C-11** (F2, 31,0 h base), con las dos líneas de proceso repartidas por fase y las **cuatro
condiciones** del go de F2 —en especial la (a), `C-10` antes de `C-05`/`C-06`, y la (d), decidir el
modo proyecto de `export-interop.py` antes de abrir `C-11`—. **C-08 y C-09 quedan diferidas**, con su
presupuesto de la pasada 1 anotado arriba para cuando se retomen.

El `planner` **hereda** estas horas y costes por característica — no re-estima desde cero — y
**re-comprueba con un comando** los «(verificado)» que herede de la spec: uno ya se cayó.

---

## Registro de cambios de esta evaluación

| Pasada | Fecha | Qué cambió | Total |
|---|---|---|---|
| 1 | 2026-09-09 | Primer presupuesto sobre la spec de la pasada 1: 9 características en 3 fases (F1/F2/F3) + 2 líneas de proceso. Veredicto: go por tramos, F3 diferida por recomendación del evaluador | 45,0 h · 2.264 € · 1.530k tok |
| **2** | **2026-09-09** | **Re-presupuesto sobre la spec final.** Salen C-08 y C-09 (F3, diferidas en la spec). Entran **C-10** (`pieces-registry.py`) y **C-11** (multi-runtime). Cinco características heredadas suben por CA reescritos y verificables; C-04 sube de horas y **de confianza**. Las líneas de proceso escalan de 8 h a 10 h. Corregida con evidencia la premisa de `export-interop.py --root` (exit 1 sobre árbol de proyecto). Condición (a) del go **mejorada** (dependencia de grafo en vez de deber de proceso) y condición (d) **nueva** | **56,4 h · 2.837 € · 1.898k tok** |
