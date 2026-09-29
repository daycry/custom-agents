---
generacion:
  inicio: 2026-09-29T18:51:06Z
  fin: 2026-09-29T19:01:50Z
  fuente: estimado        # el meter degradó: carpeta de transcripciones no disponible
  tokens_reales: null     # sin medición; estimación a juicio ≈ 88k facturables (11 min × 479326 tok/h)
  eur: null
  horas_ia: 0.18          # estimado = duración de reloj (11m); no derivado de tokens
  duracion: 11m
  ratio_usado: 479326     # CALIBRATION.md (mediana de 5)
---

# 2026-09-29-setup-statusline-polish

> Pulido de `/setup`, statusline y puertas: cuánto cuesta cerrar los 9 puntos de la spec en una iniciativa de riesgo `medio` y en qué orden conviene hacerlos. Sirve para la puerta go/no-go de `/pm-cycle`.

| | |
|---|---|
| **Fecha** | 2026-09-29 |
| **Estado** | en-revision |
| **Prioridad global** | Media |
| **Solicitante** | usuario (vía `/pm-cycle`) |
| **Spec** | [`spec.md`](spec.md) |
| **Plan** | pendiente (handoff a planner) |
| **Características evaluadas** | 9 |

---

## Cuadro de mando

| Métrica | Total estimado | Confianza |
|--------|----------------|-----------|
| Esfuerzo humano | **52,8 h** (44 h base +20 %) | Baja |
| Tiempo IA (ejecución) | **14,13 h** (+ 3,53 h supervisión) | Baja |
| Coste | **≈ 2.729 €** (referencia humana 2.640 € + tokens 89 €) | Media |
| Tokens IA | **6,77 M facturables** (in 5,82 M / out 0,95 M) + ~74,5 M de lectura de caché | Baja |
| Multiplicador productividad | **×3,0** | — |
| Características | **9** | — |

> Con agentes (así se ejecutaron las cuatro últimas iniciativas), el gasto real esperado es **≈ 266 €**: 3,53 h de supervisión × 50 €/h + 89 € de tokens. La cifra de 2.729 € es la **referencia humana**, lo que se «vendería». Se muestran por separado por LES-007, que pide no mezclar lo que se mide con lo que se vende.

---

## Resumen ejecutivo

La spec reúne 9 puntos. Siete son correcciones pequeñas sobre piezas que ya existen: statusline, `coverage-gate`, `build_dashboard`, un test de tiempos, la línea kwipu de `/doctor` y fixtures de conocimiento. Los otros dos son de verdad nuevos: el alta del proyecto en el `projects.yaml` del stack (C-07) y el `id_prefix` elegible, del que derivan el nombre del proyecto y el `group_id` (C-08). **C-07 y C-08 suman el 50 % de las horas humanas y el 57 % de las horas IA**, y concentran el riesgo. La evaluación recomienda un **go condicionado**: los quick wins pueden entrar ya, y C-07/C-08 esperan a que se cierren cuatro condiciones (ver «Recomendación»). La más importante: C-07 choca con ADR-018 y con PAT-001, y hace falta una ADR antes de planificarlo.

---

## Requerimientos recibidos

| ID | Característica | Requisito origen (ref.) | ¿Claro? |
|----|---------------|-------------------------|---------|
| C-01 | Statusline: iniciativa en curso cuando hay varias activas | Alcance 1 · CA-01..03 | ⚠️ ambiguo: qué mostrar si el marcador abierto es de spec o de evaluación y todavía no hay `tasks.md` |
| C-02 | El `find` de la statusline y de `/setup` 5-bis no elige temporales de `~/.claude/jobs` | Alcance 2 · CA-04 | ✅ en su alcance (ver riesgo: el mismo patrón aparece 76 veces en el repo) |
| C-03 | Statusline: coste correcto (locale y redondeo) | Alcance 3 · CA-05 | ✅ |
| C-04 | `coverage-gate.py`: sin «no disponible» falso por el timeout de 15 s | Alcance 4 · CA-06 | ✅ |
| C-05 | `build_dashboard.py` vuelve a leer las 5 evaluaciones | Alcance 5 · CA-07 · decisión 1a | ⚠️ ambiguo: `graphiti-memory` no tiene tabla de coste (ver incógnitas) |
| C-06 | `test_tiempos_200_upserts…` determinista | Alcance 6 · CA-08 | ✅ |
| C-07 | Script de alta en `projects.yaml` (solo añade) + `/setup` 5-sexies | Alcance 7 · Flujo 1-7 · CA-09..13 | ⚠️ incógnita: la forma real de `projects.yaml`; y choca con ADR-018 y PAT-001 |
| C-08 | `id_prefix` elegible → nombre de proyecto y `group_id`, con avisos | Alcance 8 · CA-14..15 · decisión 2c | ⚠️ falta la compatibilidad con los `group_id` implícitos que ya existen |
| C-09 | Derivados: (a) `tope_ms` de la línea kwipu de `/doctor`; (b) ~20 tests a fixture | Alcance 9 · CA-16..17 · decisión 3a | ✅ (a) depende de 3a |

**Ambigüedades / información que falta:**

- **Decisiones abiertas 1a, 2c y 3a.** Las pasó el orquestador, pero la spec no las recoge. Se evalúa con esas recomendaciones y, más abajo, se anota el coste de las alternativas. La spec debería incorporarlas antes de pasar a `aprobada`.
- **CA-07 no se puede cumplir tal como está redactado.** `docs/roadmap/2026-09-15-graphiti-memory/evaluation.md` no tiene cuadro de mando: da las horas en prosa («50h humanas…») y no da coste en €. Aceptar las dos familias de etiquetas (1a) arregla 4 de las 5 evaluaciones, no las 5. Además, las 5 declaran el estado solo en el frontmatter (`estado: completado`), sin fila `Estado`, así que el aviso «no se leyeron eval_estado…» seguirá saliendo si el lector no recurre al frontmatter.
- **C-01:** el ejemplo `▶ <slug> T-06/11 55%` presupone un ledger. Si el marcador abierto es de `spec` o de `evaluation`, como ahora mismo en esta iniciativa, la spec no dice qué mostrar.
- **C-07:** la spec lo reconoce: la forma de `projects.yaml` es desconocida hasta ver el fichero real. Sin una muestra anonimizada no se pueden diseñar las formas «reconocidas» de CA-09/11.
- **C-08:** hoy `group_id` se deriva en tiempo de carga del nombre de la carpeta (`knowledge-schema.py`) y entra en el UUID de cada episodio (`graphiti.py:_uuid_episodio`). Si pasa a derivarse de `id_prefix`, una instalación cuyo `id_prefix` explícito no coincida con la carpeta **cambiaría de `group_id` en silencio**. Un worktree como este, cuya carpeta no se llama igual que el proyecto, es un ejemplo. La spec avisa de los renombrados, pero no de este cambio de derivación.

---

## Datos necesarios para una evaluación completa

- [x] **Requerimientos** completos y sin ambigüedades — salvo lo marcado arriba
- [x] **Alcance** de cada característica acotado (qué entra y qué NO)
- [x] **Criterios de aceptación / éxito** por característica (CA-01..19, `[GWT]` en 14)
- [x] **Restricciones** (stdlib, sin red en hooks o statusline, sin datos personales, riesgo `medio`)
- [ ] **Dependencias externas** identificadas: falta una muestra anonimizada de `projects.yaml` del stack (C-07)
- [x] **Contexto técnico** del proyecto disponible (recon del repo más `code-health`)
- [x] **Tarifa/hora y supuestos de coste** confirmados (`.claude/rates.json`, precios verificados el 2026-08-18)

---

## Supuestos económicos (ajustables)

**Coste = (horas × tarifa) + coste de tokens de IA.** Importes en **EUR**.

| Parámetro | Valor | Nota |
|-----------|-------|------|
| Tarifa de desarrollo | 50 €/h | `.claude/rates.json` `tarifaHora` |
| Modelo IA asumido | claude-opus-4-8 | `rates.json` `modeloIA` |
| Precio input | 5 USD / 1M tokens (4,60 €) | `rates.json`, verificado el 2026-08-18 (hace 42 días: fiable, < 90) |
| Precio output | 25 USD / 1M tokens (23,00 €) | Ídem |
| Precio escritura / lectura de caché | 6,25 / 0,50 USD por 1M | Ídem |
| Tipo de cambio | 1 USD = 0,92 € | ⚠️ supuesto fijo de `rates.json`, no verificado |
| Margen de contingencia | 20 % | Sobre las horas base, humanas e IA |
| Ratio de supervisión | 25 % de las horas IA | `rates.json` `ratioSupervision` |
| Ratio tokens→hora-IA | 479.326 tok/h | Mediana de 5 muestras medidas de `CALIBRATION.md` |
| **Multiplicador de revisión (riesgo `medio`)** | **×1,5** sobre las horas IA de implementación | ⚠️ **Propuesta de `sdd-proporcional`, todavía sin aprobar y sin calibrar.** Supone que revisión de dos lentes + corrección = +50 % de la implementación. El histórico está por encima (ver más abajo) |
| Reparto de tokens facturables | 6 % entrada · 80 % escritura de caché · 14 % salida; lectura de caché ≈ 11 × facturables | ⚠️ Perfil de la única ventana medida con desglose en Windows (`usage-meter-transcripts`, 2026-09-10). Una sola muestra |

**Método.** Las horas humanas son un juicio por característica, a partir del recon de ficheros y líneas reales. Las horas IA de implementación también son un juicio, pero con los multiplicadores de `CALIBRATION.md` donde aplican: ×3 en C-07, que escribe en la configuración de un sistema ajeno (`installer-registro-real` dio ×5 con tres runtimes; aquí es un solo YAML), y ×2,5 en C-08, que cambia un contrato con varios consumidores (`graphiti-memory`). A eso se suma **×1,5 de revisión** y **+20 % de margen**. Tokens facturables = horas IA (con margen) × 479.326.

**Calibración aplicada (P2-bis).**

- **LES-009 / LES-001 (la revisión es la partida grande).** Aquí es explícita (×1,5). Pero el histórico reciente la sitúa entre **×2,2 y ×3,4** del total sobre la implementación: `installer-registro-real` 7,28 h de implementación + 8,55 h de revisión; `graphiti-memory` ≈ 6,6 h + ≈ 16 h. **×1,5 es optimista para C-07 y C-08.** Sensibilidad en «Presupuesto total».
- **LES-007 / LES-008.** La referencia humana y el coste de proceso con agentes van por separado. Las horas humanas **nunca se han validado** (aprendizaje nº 2 de `CALIBRATION.md`): confianza Baja.
- **LES-005.** La constitución obliga a TDD (§1): la ejecución se encarece y la revisión se abarata. Queda recogido en las horas IA de implementación.

---

## Evaluación por característica

### C-01 — Statusline: iniciativa en curso con varias activas

- **Requisito origen**: Alcance 1 · CA-01, CA-02, CA-03
- **Descripción**: con 2 o más ledgers activos, la línea pasa de «📋 N iniciativas activas» a «📋 N activas · ▶ `<slug>` T-XX/YY NN%». La iniciativa en curso sale del marcador abierto de `usage-meter`, o, si no hay, del `tasks.md` modificado más recientemente.
- **Complejidad**: Media
- **Esfuerzo**: 4 h base (4,8 h con margen) · confianza Media
- **Previsión IA**: 1,08 h · 445k in / 72k out tok · 6,81 €
- **Coste**: (4,8 h × 50 €/h) + tokens = **≈ 247 €**
- **Impacto / áreas afectadas**: `statusline/roadmap-statusline.sh` (91 líneas) y `agent-kits/shared/progress-report.py` (`cmd_active`/`activas`). La selección debe ir en el script con tests (constitución §1), no en el bash. Tests: `test_progress_report.py` y `tests/test_hooks_shell.py`.
- **Dependencias y prerequisitos**: ninguna
- **Riesgos**: coste por refresco. La statusline se ejecuta a cada refresco, así que la iniciativa en curso debe salir de leer `.claude/usage-state.json` directamente, sin lanzar `usage-meter.py status`, y solo de `docs/roadmap/*/tasks.md`. Las claves de marcador tienen dos formas en el mismo fichero (`<slug>/<artefacto>` y rutas `docs/roadmap/<fecha>-<slug>/…`), así que hay que sacar el slug de las dos.
- **Incógnitas / preguntas abiertas**: con un marcador abierto de spec o evaluación y sin ledger, ¿se muestra `▶ <slug>` sin progreso, o se ignora?

### C-02 — `find` que nunca elige un temporal de `~/.claude/jobs`

- **Requisito origen**: Alcance 2 · CA-04
- **Descripción**: excluir `*/.claude/jobs/*` y los temporales del `find … | head -1` de la statusline y de `/setup` 5-bis, prefiriendo el plugin instalado o el proyecto.
- **Complejidad**: Baja-Media
- **Esfuerzo**: 2,5 h base (3 h) · confianza Media
- **Previsión IA**: 0,72 h · 297k in / 48k out tok · 4,54 €
- **Coste**: **≈ 155 €**
- **Impacto / áreas afectadas**: `statusline/roadmap-statusline.sh:71`, `commands/setup.md:43` (5-bis). Cambiar `commands/` obliga a regenerar `interop/` (`export-interop.py`).
- **Dependencias y prerequisitos**: ninguna
- **Riesgos**: **alcance latente.** El mismo patrón `find "$PWD/.claude" … | head -1` aparece **76 veces** en `agents/`, `commands/`, `skills/`, `hooks/` y `statusline/`. La spec arregla dos. Las otras 74 conservan el defecto. Se recomienda anotarlas como deuda, no ampliar el alcance aquí.
- **Incógnitas / preguntas abiertas**: la lista exacta de temporales que se excluyen (¿solo `jobs/`, o también `%TEMP%` y `/tmp`?). El test necesita un `HOME` falso con las dos copias.

### C-03 — Statusline: coste correcto

- **Requisito origen**: Alcance 3 · CA-05
- **Descripción**: el `$0,00` sale de `printf '%.2f'` en bash con un locale de coma decimal, que rechaza «0.42». El arreglo es `LC_NUMERIC=C` y un formato «<$0.01» para los costes positivos muy pequeños.
- **Complejidad**: Baja
- **Esfuerzo**: 1 h base (1,2 h) · confianza Alta
- **Previsión IA**: 0,27 h · 111k in / 18k out tok · 1,70 €
- **Coste**: **≈ 62 €**
- **Impacto / áreas afectadas**: `statusline/roadmap-statusline.sh:56-59`; caso nuevo en `tests/test_hooks_shell.py`
- **Dependencias y prerequisitos**: ninguna
- **Riesgos**: bajos. El test necesita un locale de coma disponible en CI (en Linux, `de_DE.UTF-8` no siempre está instalado): si no lo está, se simula o se omite con aviso.
- **Incógnitas / preguntas abiertas**: la spec pide reproducir antes de arreglar (supuesto 3); lectura del código compatible con la hipótesis.

### C-04 — `coverage-gate.py` sin «no disponible» falso

- **Requisito origen**: Alcance 4 · CA-06
- **Descripción**: `herramienta_disponible` trata un `TimeoutExpired` (arranque lento) igual que un `ImportError`. Hay que separarlos: un timeout se reintenta o queda como «no verificado», y solo un fallo de import real da «no disponible».
- **Complejidad**: Baja
- **Esfuerzo**: 1,5 h base (1,8 h) · confianza Alta
- **Previsión IA**: 0,45 h · 185k in / 30k out tok · 2,84 €
- **Coste**: **≈ 93 €**
- **Impacto / áreas afectadas**: `skills/unit-tests/scripts/coverage-gate.py:150-158` y sus tests
- **Dependencias y prerequisitos**: ninguna
- **Riesgos**: no convertir un «no verificado» en un % inventado (la guardia de la skill). El exit 2 con aviso se mantiene.
- **Incógnitas / preguntas abiertas**: ninguna relevante

### C-05 — `build_dashboard.py` vuelve a leer las evaluaciones

- **Requisito origen**: Alcance 5 · CA-07 · decisión **1a** (el lector acepta las dos familias de etiquetas)
- **Descripción**: `_scan_leer_eval` solo busca `Coste` y `Esfuerzo humano`. Las evaluaciones recientes usan `Tiempo humano`, `Coste humano a N EUR/h`, `Coste humano (50 EUR/h)` y `Tokens`. Hay que añadir alias y recurrir a `estado:` del frontmatter cuando no hay fila `Estado`.
- **Complejidad**: Baja-Media
- **Esfuerzo**: 3 h base (3,6 h) · confianza Media
- **Previsión IA**: 0,90 h · 371k in / 60k out tok · 5,68 €
- **Coste**: **≈ 186 €**
- **Impacto / áreas afectadas**: `skills/roadmap-dashboard/scripts/build_dashboard.py:313-322` (hotspot: 11 cambios en 90 días, 717 líneas); `tests/test_dashboard.py`
- **Dependencias y prerequisitos**: ninguna
- **Riesgos**: `graphiti-memory` **no tiene ninguna fila** de coste ni de esfuerzo. Ningún alias la cubre, y parsear prosa sería frágil. Además, «1,300 EUR» usa coma de miles: si alguien reutiliza `_num()` (que trata la coma como decimal), leería 1,3.
- **Incógnitas / preguntas abiertas**: para `graphiti-memory`, ¿se deriva el coste de las horas con `derivado` marcado, o se acepta el nulo con un aviso explícito? Ninguna de las dos toca la plantilla ni reescribe el registro.
- **Otras opciones de la decisión 1.** Normalizar las 5 evaluaciones ahorraría ≈ 0,5 h, pero reescribe registros fechados (CLAUDE.md lo prohíbe). Aceptar solo la familia nueva también ahorra ≈ 0,5 h, pero rompe CA-07. **Diferencia < 1 % del total: la elección no cambia el coste.**

### C-06 — Test de 200 upserts determinista

- **Requisito origen**: Alcance 6 · CA-08
- **Descripción**: cambiar `assertLess(t_sin_cambios, 10.0)` por una aserción sobre el número de operaciones: contar `os.replace` y escrituras con `mock`. La propiedad real (gap 136) es «0 renombrados en la pasada estable».
- **Complejidad**: Baja
- **Esfuerzo**: 1 h base (1,2 h) · confianza Alta
- **Previsión IA**: 0,27 h · 111k in / 18k out tok · 1,70 €
- **Coste**: **≈ 62 €**
- **Impacto / áreas afectadas**: `skills/knowledge-services/scripts/test_backend_markdown_export.py:1132-1149`
- **Dependencias y prerequisitos**: ninguna
- **Riesgos**: el test tiene que seguir mordiendo. Hay que comprobarlo con un mutante (un `os.replace` por fichero en la pasada estable ⇒ rojo). CA-08 pide 20 ejecuciones en bucle.
- **Incógnitas / preguntas abiertas**: ninguna

### C-07 — Alta del proyecto en `projects.yaml` (solo añade) y enganche en `/setup` 5-sexies

- **Requisito origen**: Alcance 7 · Flujo 1-7 · CA-09..CA-13 · Modelo de amenaza
- **Descripción**: script stdlib nuevo en `skills/knowledge-services/scripts/`. Reconoce formas concretas del YAML, detecta el homónimo con otra `root` (conflicto) o con la misma (no-op), muestra vista previa, pide confirmación, hace copia de seguridad y escritura atómica, valida `id_prefix` y `root` contra inyección y *traversal*, e imprime los comandos de `build_view` y de reinicio sin ejecutarlos.
- **Complejidad**: Alta
- **Esfuerzo**: 12 h base (14,4 h) · confianza Baja
- **Previsión IA**: 4,50 h (implementación 2,5 h, con el ×3 histórico por escribir en configuración ajena, × 1,5 de revisión × 1,2 de margen) · 1.855k in / 302k out tok · 28,38 €
- **Coste**: **≈ 748 €**
- **Impacto / áreas afectadas**: script nuevo + tests; `commands/setup.md` 5-sexies (regenera `interop/`); `skills/knowledge-services/SKILL.md` y `references/kwipu-adapter.md`; docs EN/ES
- **Dependencias y prerequisitos**: **C-08** (el nombre del proyecto sale de `id_prefix`); una **muestra anonimizada** del `projects.yaml` real; una **ADR** (ver riesgos)
- **Riesgos**:
  - **Conflicto con decisiones anteriores.** ADR-018 descartó el «control plane multi-proyecto (`projects.yaml`…)». PAT-001 dice que acoplar el plugin a `projects.yaml` le da «permisos y superficie de fallo que no le corresponden». La constitución §4 dice que una pieza «nunca borra ni sobrescribe lo que no ha creado», y la escritura atómica (temporal + reemplazo) **reemplaza** un fichero que el plugin no creó, aunque el contenido previo quede byte a byte igual. Añadir un bloque no es lo mismo que el *control plane* descartado, pero la tensión hay que resolverla por escrito: una ADR nueva o una enmienda a ADR-018. Supera el umbral de ADR: cierra una alternativa y afecta a 2 o más piezas.
  - **Histórico.** Es la misma familia que `installer-registro-real`: escribir en la configuración de un runtime ajeno. Allí hubo 64 gaps en 5 rondas, 4 Critical, todos de la forma «afirmar un resultado sin comprobarlo». Con ×1,5 de revisión, esta línea es la más expuesta a desviarse.
  - **Operativo.** En modo auto se deniega editar el `projects.yaml` del stack. La validación se hace sobre copias en temporales y la ejecución real la lanza el usuario.
- **Incógnitas / preguntas abiertas**: la forma exacta del YAML (lista o mapa, claves de nombre y `root`, comentarios, anclas); si `root` se escribe absoluta o relativa al stack; qué código de salida distinto de 0 se documenta para «forma no reconocida».

### C-08 — `id_prefix` elegible, derivación de nombre y `group_id`, avisos

- **Requisito origen**: Alcance 8 · CA-14, CA-15 · decisión **2c** (primero el estado local; después el servidor, si responde)
- **Descripción**: `/setup` propone el slug de la carpeta, lo valida (`^[a-z0-9][a-z0-9-]*$`) y lo guarda en `taxonomy.json`. De él heredan el nombre del proyecto en `projects.yaml` y el `group_id` de Graphiti, salvo que se sobrescriban. Hay dos avisos: renombrar con conocimiento ya exportado (cambian los `knowledge_id`), y `group_id` con episodios de otro origen, que primero se busca en el estado local y después en el servidor.
- **Complejidad**: Alta
- **Esfuerzo**: 10 h base (12 h) · confianza Baja
- **Previsión IA**: 3,60 h (implementación 2,0 h, con el ×2,5 histórico por contrato con varios consumidores) · 1.484k in / 242k out tok · 22,70 €
- **Coste**: **≈ 623 €**
- **Impacto / áreas afectadas**: `agent-kits/shared/knowledge-schema.py` (hotspot nº 2: 17 cambios en 90 días, 749 líneas, anidamiento 7; `_con_id_prefix_por_defecto` y la derivación de `group_id`); `skills/knowledge-services/backends/graphiti.py` (`group_id` entra en `_uuid_episodio`); consumidores de `group_id`: `capabilities.py`, `knowledge-find.py`, `doctor.py`; `commands/setup.md`; tests de `test_knowledge_schema.py`, `test_capabilities.py`, `test_backend_graphiti.py` y `tests/test_graphiti_security.py`
- **Dependencias y prerequisitos**: ninguna previa. C-07 depende de esta.
- **Riesgos**:
  - **Migración silenciosa del `group_id`.** Si la derivación pasa de «carpeta» a «`id_prefix`», las instalaciones con `group_id` implícito y un `id_prefix` distinto de la carpeta cambian de grupo, y sus episodios quedan huérfanos en Graphiti. Mitigación que debería exigir el plan: materializar el `group_id` vigente en `taxonomy.json` antes de cambiar la derivación, o aplicar la nueva derivación solo a configuraciones sin `group_id` efectivo previo. En cualquier caso, un test que lo fije.
  - **Duplicación.** `code-health` señala 33 líneas duplicadas entre `knowledge-schema.py:83` y `graphiti.py:167`. Tocar la derivación en un sitio y no en el otro es el patrón de gap que reabrió rondas en `graphiti-memory` (cada consumidor siguiente reabría el contrato).
  - **Decisión 2c.** Añade una consulta al servidor desde `/setup`: red opt-in, acotada a loopback por el adaptador; degrada a «no verificado».
- **Incógnitas / preguntas abiertas**: ¿qué «estado local» identifica el origen de los episodios (manifiesto publicado del adaptador, `outbox`)? ¿Hay una llamada MCP barata para contar los episodios de un `group_id`?
- **Otras opciones de la decisión 2.** Solo estado local (sin servidor): −1,5 h humanas, −0,3 h IA y menos riesgo, pero no detecta episodios de otra máquina. Solo servidor: −0,5 h, pero degrada más a menudo. **El delta es ≤ 3 % del total: no cambia el veredicto.**

### C-09 — Derivados: `tope_ms` de `/doctor` y tests de conocimiento a fixture

- **Requisito origen**: Alcance 9 · CA-16 (decisión **3a**: `tope_ms` estricto con timeout duro) · CA-17
- **Descripción**: (a) la línea kwipu de `/doctor` no pasa de `tope_ms` más un margen fijo. El socket ya se acota con un presupuesto único (`_urlopen_local`), pero la resolución DNS y el arranque del adaptador quedan fuera. Un timeout duro obliga a ejecutar la sonda en un hilo con `join(timeout)` y abandonarlo si no termina. (b) Unos 20 tests de `tests/test_knowledge_find.py` (69 tests) y `tests/test_knowledge_index.py` (16) dependen de `docs/knowledge/`, que ya no se versiona: pasan a un fixture (`evals/fixtures/project/docs/knowledge/` ya existe).
- **Complejidad**: Media
- **Esfuerzo**: 6 h base (7,2 h): (a) 3 h, (b) 3 h · confianza Media
- **Previsión IA**: 1,44 h · 594k in / 97k out tok · 9,08 €
- **Coste**: **≈ 369 €**
- **Impacto / áreas afectadas**: (a) `agent-kits/shared/doctor.py` (hotspot nº 1: 23 cambios en 90 días, 1.961 líneas; `_linea_capacidad`, `_cfg_con_timeout_topado`); `test_doctor.py`. (b) los dos ficheros de test y el fixture.
- **Dependencias y prerequisitos**: ninguna. (b) conviene al principio: estabiliza la suite para comparar los rojos (CA-18).
- **Riesgos**: (a) un hilo abandonado no se puede matar en Python. Tiene que ser `daemon` y no dejar escrituras a medias. `doctor.py` es el fichero que más cambia del repo. (b) Los tests que fijan «cifras de línea base» del `docs/knowledge/` real (9 entradas…) hay que reformularlos contra el fixture sin perder lo que prueban.
- **Incógnitas / preguntas abiertas**: el valor del «margen fijo documentado»; el conjunto exacto de los «~20» tests.
- **Otras opciones de la decisión 3.** Un tope blando con un margen documentado, sin hilo: −1,5 h humanas y −0,3 h IA, y menos riesgo en el hotspot, pero no garantiza el tope si falla el DNS. **Delta ≈ 3 %: no cambia el veredicto.**

### Transversal — cierre (no es una característica)

- Docs EN/ES (`docs/en/`, README y CHANGELOG bilingües), `export-interop.py`, lint, `evals/check.py`, suites y réplica en Linux (CA-18, CA-19): **3 h base (3,6 h)** · 0,90 h IA · 371k in / 60k out · 5,68 € · **≈ 186 €**.

---

## Comparativa

Ordenada por coste, de menor a mayor.

| # | Característica | Complejidad | Horas | Coste € | Tokens | Prioridad | Confianza |
|---|---------------|-------------|-------|---------|--------|-----------|-----------|
| C-03 | Coste correcto en statusline | Baja | 1,2 h | 62 € | 129k | Alta 🟠 | Alta |
| C-06 | Test de 200 upserts determinista | Baja | 1,2 h | 62 € | 129k | Alta 🟠 | Alta |
| C-04 | `coverage-gate` sin falso «no disponible» | Baja | 1,8 h | 93 € | 216k | Alta 🟠 | Alta |
| C-02 | `find` sin temporales | Baja-Media | 3 h | 155 € | 345k | Media 🟡 | Media |
| C-05 | Dashboard lee las evaluaciones | Baja-Media | 3,6 h | 186 € | 431k | Media 🟡 | Media |
| C-01 | Iniciativa en curso en statusline | Media | 4,8 h | 247 € | 518k | Media 🟡 | Media |
| C-09 | `tope_ms` de `/doctor` + fixtures | Media | 7,2 h | 369 € | 690k | Media 🟡 | Media |
| C-08 | `id_prefix` elegible y derivaciones | Alta | 12 h | 623 € | 1.726k | Media 🟡 | Baja |
| C-07 | Alta en `projects.yaml` | Alta | 14,4 h | 748 € | 2.157k | Media 🟡 | Baja |
| — | Transversal (docs, interop, Linux) | Baja | 3,6 h | 186 € | 431k | — | Media |
| | **Total** | | **52,8 h** | **2.729 €** | **6.773k** | | |

---

## Presupuesto total

| Concepto | Cálculo | Importe |
|----------|---------|---------|
| Desarrollo (humano, base) | 44 h × 50 €/h | 2.200,00 € |
| Margen de contingencia | +20 % sobre desarrollo base (8,8 h) | 440,00 € |
| Tokens IA (input) | 0,41 M × 5 USD/M × 0,92 | 1,87 € |
| Tokens IA (escritura de caché) | 5,42 M × 6,25 USD/M × 0,92 | 31,16 € |
| Tokens IA (output) | 0,95 M × 25 USD/M × 0,92 | 21,81 € |
| Tokens IA (lectura de caché) | ~74,5 M × 0,50 USD/M × 0,92 | 34,27 € |
| **Total estimado (con margen)** | | **≈ 2.729 €** |

**Coste de ejecución con agentes (lo que se espera gastar de verdad):** 3,53 h de supervisión × 50 €/h = 176,63 € + 89,10 € de tokens = **≈ 266 €**.

**Sensibilidad al multiplicador de revisión (no aprobado).**

| Escenario | Horas IA | Supervisión | Tokens € | Ejecución con agentes |
|-----------|----------|-------------|----------|-----------------------|
| ×1,5 en todo (propuesta `sdd-proporcional`) | 14,13 h | 3,53 h | 89 € | ≈ 266 € |
| ×2,5 solo en C-07 y C-08 (histórico de configuración ajena y contratos) | 19,53 h | 4,88 h | 123 € | ≈ 367 € |
| ×2,5 en todo | 23,55 h | 5,89 h | 149 € | ≈ 443 € |

Las horas humanas de referencia no cambian (52,8 h): el multiplicador solo afecta a la ejecución con IA.

---

## Productividad IA (humano vs. IA)

| KPI | Valor |
|-----|-------|
| Horas humanas estimadas | 52,8 h (44 h base) |
| Horas IA (ejecución) | 14,13 h (11,78 h base: 7,85 h de implementación + 3,93 h de revisión con ×1,5) |
| Supervisión humana | 3,53 h |
| **Horas totales (IA + supervisión)** | **17,66 h** |
| Horas ahorradas | 35,14 h |
| **Ahorro** | **66,5 %** |
| **Multiplicador de productividad** | **×3,0** |
| FTE equivalentes *(opcional)* | 0,22 |

> Todas las horas llevan ya el margen de contingencia (+20 %). Las horas IA son un juicio calibrado. El histórico muestra desviaciones de IA de +53 % a +460 % en iniciativas de configuración ajena y contratos. Por eso la confianza es Baja.

---

## Recomendación

- **Veredicto**: **go condicionado.** C-01..C-06 y C-09 pueden planificarse ya. **C-07 y C-08 solo con estas condiciones cerradas**:
  1. **ADR** (nueva, o enmienda a ADR-018) que autorice escribir, solo añadiendo, en el `projects.yaml` del stack y que concilie PAT-001 y la constitución §4 (reemplazo atómico de un fichero que el plugin no creó). Si no se acepta, C-07 se reduce a «imprimir el bloque para pegar a mano» (≈ −8 h humanas, −3 h IA).
  2. **Muestra anonimizada** de `projects.yaml` (forma, claves, comentarios) antes de que `planner` parta C-07 en tareas.
  3. **Compatibilidad del `group_id`** fijada en la spec: sin migraciones silenciosas en instalaciones con `group_id` implícito (C-08).
  4. **CA-07 reescrito** para `graphiti-memory` (derivar marcando `derivado`, o nulo con aviso) y **decisiones 1a/2c/3a** incorporadas a la spec.
- **Quick wins** (bajo coste, alto valor): **C-03, C-06, C-04**. Menos de 5 h en total. Arreglan una cifra visible cada día y dos puertas inestables. Después vienen C-05 y C-02.
- **Costosas / a valorar**: **C-07** (748 €) y **C-08** (623 €). Juntas son el 50 % del esfuerzo humano y el 57 % del IA, y concentran el riesgo de revisión.
- **Orden sugerido**: C-06 → C-09b → C-03 → C-04 → C-05 → C-02 → C-01 → C-09a → C-08 → C-07. Primero lo que estabiliza la suite (C-06 y los fixtures de C-09b hacen fiable la comparación de rojos de CA-18). Después los quick wins de visibilidad. Luego `/doctor`, que es un hotspot y va aislado. Al final C-08 y C-07, porque C-07 hereda el nombre de `id_prefix`.
- **Fuera de alcance recomendado**: las otras 74 apariciones del `find … | head -1` (anotarlas como deuda para una iniciativa propia con un *helper* común); la migración de `knowledge_id` y `group_id` existentes (ya fuera en la spec).
- **Diseño**: `architect` es opcional. Solo tendría sentido para C-07/C-08 si la ADR de la condición 1 deja abiertas 2 o más formas de encajar el alta.

---

## Riesgos transversales

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|-------------|---------|------------|
| El ×1,5 de revisión se queda corto (histórico entre ×2,2 y ×3,4 en configuración ajena y contratos) | Alta | Medio | Sensibilidad publicada (hasta ≈ 443 € con agentes); anotar en `/retro` el multiplicador real para calibrar `sdd-proporcional` |
| Tres hotspots tocados a la vez (`doctor.py`, `knowledge-schema.py`, `build_dashboard.py`) | Media | Medio | Tareas separadas por fichero, sin paralelizar sobre el mismo hotspot; revisión de dos lentes por tramo |
| Regresión en la statusline, que se ejecuta a cada refresco | Media | Medio | Salida idéntica con una sola activa (CA-03); nada de red ni de subprocesos extra; test de shell |
| Comparar rojos en Windows no ve fallos que solo salen en CI | Media | Medio | Réplica en Linux (CA-18) con normalización CRLF de los `.sh` |
| Datos personales en fixtures o ejemplos de `projects.yaml` | Baja | Alto | Ejemplos con `<stack>/…`; revisión explícita en CA-19 |
| Cambiar `commands/` sin regenerar `interop/` | Media | Bajo | `export-interop.py --check` como puerta (CA-18) |

---

## Siguiente paso

Para **ejecutar** lo aprobado, genera el plan detallado con el agente **`planner`**, que crea `improvement-plan.md` y `tasks.md` en esta carpeta. Propuesta de aprobación: **C-01..C-06 y C-09 sin condiciones; C-07 y C-08 cuando estén cerradas las condiciones 1-4**, en el orden sugerido y con C-08 antes que C-07. El `planner` hereda las horas y los costes de esta evaluación por característica, incluidas la línea de revisión (×1,5) y la sensibilidad. Al crear el plan, actualiza la fila **Plan** de esta evaluación y el campo `plan:` de la spec.
