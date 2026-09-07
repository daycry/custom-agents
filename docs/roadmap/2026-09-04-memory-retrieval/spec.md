---
spec: memory-retrieval
descripcion: >
  Recuperación de la memoria técnica: tres capas deterministas sobre el corpus curado
  (búsqueda compacta, grafo curado, entrada completa), inyección PRESUPUESTADA en los dos
  caminos por los que llega el contexto a un agente (brief del subagente y arranque de
  sesión), captura episódica automática a dos velocidades y una eval que prueba que el
  camino SE RECORRE. Fuente: `analysis.md` de esta carpeta.
estado: aprobada
creado: 2026-09-04
actualizado: 2026-09-04
evaluacion: evaluation.md
design: n/a
plan: improvement-plan.md
generacion:            # ventana compartida con evaluation.md · improvement-plan.md · tasks.md (se cuenta UNA vez)
  inicio: 2026-09-04T09:00:00Z
  fin: 2026-09-04T09:40:00Z
  fuente: estimado     # el usage-meter no puede leer la transcripción en este entorno: no hay medición
  tokens_reales: { entrada: 180000, salida: 60000, cache_creacion: 40000, cache_lectura: 900000 }
  eur: 2.85
  horas_ia: 0.58
  duracion: 40m
  ratio_usado: 479326
---

# Memoria técnica recuperable — tres capas, dos velocidades y un presupuesto por camino

> **Evaluación:** [`evaluation.md`](evaluation.md)
> **Plan de implementación:** [`improvement-plan.md`](improvement-plan.md)
> **Análisis de origen (entrada de esta spec):** [`analysis.md`](analysis.md)

> **Terminología:**
> - **Memoria curada** — `docs/knowledge/adr/`, `gotchas/`, `lessons/`: una entrada por fichero, con
>   `estado`, fecha, fuente, revisada y versionada en git. Es **doctrina o indicio**, según `estado`.
> - **Memoria episódica** — `docs/knowledge/journal/`: bitácora cronológica por sesión, no curada.
> - **Doctrina del plugin** — lecciones ciertas para CUALQUIER proyecto que use estos agentes
>   (`LES-001…009`, estimación y calibración). Viaja con el plugin.
> - **Memoria del proyecto** — la del consumidor. **Nace vacía, y eso es correcto.**
> - **Índice FTS5** — caché de búsqueda en `.claude/`, no versionada y **reconstruible**. No es el
>   almacén: el almacén son los ficheros Markdown en git.
> - **Acierto compacto** — una línea `ID · estado · área · titular · ruta` (~25 tokens).

## Contexto y objetivo

El análisis de esta carpeta lo resume en una frase: **escribimos memoria muy bien y la recuperamos
muy mal.** Las cifras están medidas sobre el repo en `a7a11b0..HEAD` y reproducidas al escribir esta
spec:

| Medida | Hoy | Cómo se comprueba |
|---|---|---|
| Entradas curadas | **31** (12 ADR · 5 gotchas · 14 lecciones) | `ls docs/knowledge/{adr,gotchas,lessons}/*.md \| wc -l` |
| Corpus curado | **108.443 caracteres ≈ 27.100 tokens** | suma de caracteres de las 31 + índice |
| Índice de entrada (`docs/knowledge/README.md`) | **14.741 caracteres ≈ 3.685 tokens**, 31 filas | `wc -c docs/knowledge/README.md` |
| Tokens de memoria curada inyectados al arrancar sesión | **0** de 872 | `hooks/session-context.sh` compone índice de piezas + roadmap + journal |
| Entradas del journal desde que se construyó | **0** (solo `README.md`) | `ls docs/knowledge/journal/` |
| Entradas que ninguna pieza ejecutable del plugin cita | **17 de 31 (55 %)** | `analysis.md` §1.5, medido |
| Áreas distintas en la columna «Área» del índice | **21** para 31 entradas (9 en «Estimación / calibración», el resto casi todas singleton) | `awk` sobre la columna 5 del índice |
| Tokens del brief del subagente | **1.818** (`analysis.md`); re-medido hoy sobre `changelog-brief` T-01: **7.452 caracteres ≈ 1.863 tokens** | `task-brief.py <carpeta> T-01 \| wc -c` |
| Entrada curada más grande | **10.449 caracteres ≈ 2.612 tokens** (`ADR-012`) | máximo de los 31 ficheros |
| Días desde la última fila de `CALIBRATION.md` (2026-08-20) | **15**, con 13 iniciativas cerradas después | `docs/roadmap/CALIBRATION.md` |

El objetivo es cerrar los **cinco huecos** del análisis sin tocar lo que funciona (la curación) y sin
adoptar `claude-mem`: **robarle la capa de recuperación y conservar nuestra curación.**

**Para quién:** para los agentes que trabajan con `subagentes: true`, donde `commands/dev-cycle.md:110`
ordena «el subagente NO explora el repo entero: el brief y los ficheros que referencia» — y el brief
hoy no lleva memoria, así que quien escribe el código **no puede alcanzar un gotcha ni queriendo**.

## Decisiones de diseño

Las dos preguntas que cambiaban el plan las cerró el usuario el 2026-09-04. No se re-abren.

| Decisión | Elección | Motivo |
|---|---|---|
| **Captura** | **Curada + episódica automática** | Se conserva la curación como doctrina (es la ventaja: 31 entradas revisadas valen más que 10.000 observaciones sin filtrar) y se añade una capa episódica que capture lo que HOY se pierde: decisiones del usuario, resultado de tareas, fallos diagnosticados. **NO se registra cada `PostToolUse`**: eso es ruido y coste, y destruiría la señal que nos diferencia |
| **Dependencias** | **Solo stdlib, con SQLite FTS5** | El módulo `sqlite3` es stdlib: el índice de texto completo **no añade ni una dependencia**. Sin embeddings, sin servicios, sin worker HTTP (ellos piden Node ≥ 20, Bun, uv, SQLite y un worker) |
| **Almacén** | **Ficheros Markdown en git; el índice es CACHÉ** | No se negocia: es lo que permite revisar la memoria en un PR. Para `claude-mem` la base **ES** el almacén (base corrupta = memoria perdida, y nada revisable); para nosotros es una caché reconstruible |
| **Ámbito de la 2.ª capa** | **Grafo curado, no cronología** | Su `timeline` responde «qué pasó cerca en el tiempo». Un grafo de sustitución (`ADR` sucesor/sustituido), misma iniciativa y misma área es mejor información sobre el MISMO coste de tokens |
| **Enrutado por área** | **Coincidencia normalizada, no exacta** | Medido hoy: 21 áreas distintas para 31 entradas, texto libre con `/` y acentos. Una comparación exacta de cadena no enruta nada; `--area estimacion` debe casar «Estimación / calibración» |
| **Resumen episódico por IA** | **Opt-in, escrito por el hook, degradación silenciosa** | Revisa `ADR-010`: su restricción («el contrato de `SessionEnd` ignora la salida de los hooks») es **CIERTA**, pero la conclusión era demasiado fuerte — el hook no necesita *devolver* el resumen, puede **escribirlo** |
| **Orden de ejecución** | **Recuperación → llegada → prueba → captura → doctrina → bucle** | Coste/impacto y dependencias. La captura episódica es lo más caro y lo menos cierto; la recuperación es lo que más rinde y no depende de nada |

## Configuración / parámetros

| Parámetro | Clave / mecanismo | Default | Valor objetivo |
|---|---|---|---|
| Resumen episódico por IA | `.claude/dev.json` → `sesion.resumen` | `false` (ausente) | **opt-in**: `true` lo activa; sin CLI, sin clave o `false` → journal determinista de hoy |
| Inyección de memoria al arrancar | `.claude/dev.json` → `sesion.memoria` | `true` | desactivable, como `sesion.indice` y `sesion.journal` |
| Índice FTS5 | `.claude/knowledge-index.sqlite` (+ `.gitignore`) | se crea al primer uso | **reconstruible**; hash del corpus guardado dentro |
| Log crudo del turno del usuario | `.claude/session-prompts-<session_id>.log` | se crea al primer turno | ya cubierto por `*.log` de `.gitignore` (verificado) |
| Opt-out de captura del turno | etiqueta `<private>` en el turno | — | con la etiqueta, **el log NO se toca** |
| Tope de la inyección en el brief | constante del script + test | — | **≤ 600 tokens (≤ 2.400 caracteres)** |
| Tope de la inyección al arrancar | constante del hook + test | — | **≤ 300 tokens (≤ 1.200 caracteres)**, dentro del `TOPE_CHARS = 9500` del hook |
| Coste por acierto compacto | formato de línea + test | — | **≤ 30 tokens (≤ 120 caracteres)** por acierto |

## Arquitectura y componentes

### Tres capas

**Capa 1 — Captura, a dos velocidades.**

- *Curada* (**existe; el mecanismo NO se toca**): `adr/`, `gotchas/`, `lessons/`, con `estado`,
  fecha, fuente, revisada y en git. La promoción `propuesta` → `aceptada` la firma la revisión de
  dos lentes o el usuario. Nada de esto está roto.
- *Episódica automática* (**nueva**): un hook `UserPromptSubmit` acumula el turno del usuario en un
  log crudo **no versionado** en `.claude/`, con opt-out por etiqueta al estilo `<private>` — y con
  el opt-out puesto **el log no se toca**. Al cerrar, el hook `SessionEnd` **escribe él mismo** la
  entrada del journal con `decisiones` y `pendientes` extraídas de ese log. La extracción por IA va
  **opt-in** (`dev.json` `sesion.resumen: true`) invocando el CLI en headless como ya hace
  `evals/run.py` (`claude -p`); sin CLI, sin clave o con el opt-in apagado, **degrada al journal
  determinista de hoy y nunca bloquea**.
- *Promoción*: una entrada de journal cuyo patrón se repite entre sesiones se convierte en
  **candidata a lección** y entra por la puerta de `/retro` con `estado: propuesta`. **Esta es la
  bisagra entre las dos velocidades, y es lo que `claude-mem` no tiene**: ellos capturan sin filtro
  y nunca ascienden nada a doctrina.

**Capa 2 — Almacén e índice.**

- **Fuente de verdad: los ficheros Markdown en git.** Un ADR se revisa en un PR, tiene fecha, fuente
  y estado, y se puede rebatir.
- **Índice: SQLite FTS5 en `.claude/`, no versionado y RECONSTRUIBLE desde los ficheros.** Si falta,
  está corrupto o su hash no cuadra → se reconstruye; si no se puede reconstruir (disco de solo
  lectura, `sqlite3` sin FTS5) → **recorrido plano de los ficheros**. Nunca bloquea, nunca sale con
  código distinto de 0 por culpa del índice.

**Capa 3 — Recuperación (hoy NO existe).**

`agent-kits/shared/knowledge-find.py`, tres capas al estilo de las tres herramientas MCP de
`claude-mem` pero **deterministas**:

1. consulta → **aciertos compactos** (`ID · estado · área · titular · ruta`, ~25 tokens por acierto),
   ordenados por relevancia, con el **`estado` DELANTE** para que el lector sepa si lo que tiene en
   la mano es doctrina (`aceptada`), indicio (`propuesta`) o basura con sucesor (`obsoleta`);
2. `--related <ID>` → **grafo curado**: ADR sucesor/sustituido, misma iniciativa, misma área;
3. `--show <ID>` → la entrada completa.

Y dos puntos de **llegada**, cada uno con tope medido:

- **`task-brief.py`**: sección nueva con los aciertos del área y el tipo de la tarea, enrutada por el
  campo `- **Tipo**:` que **ya existe** en el ledger. Esto abre la puerta cerrada: con
  `subagentes: true` el brief es el ÚNICO contexto.
- **`session-context.sh`**: no el corpus (27.100 tokens no caben en `TOPE_CHARS = 9500` caracteres),
  sino los N mejores aciertos del **área de la iniciativa activa**, con tope explícito.

Y una **prueba de que el camino se recorre**: casos en `evals/` que afirmen que un agente con una
tarea de área X recibe o consulta la entrada de área X, más el test determinista que lo afirma sin
gastar tokens. **Esto no lo tiene nadie — ni nosotros ni ellos — y es la diferencia entre una
intención y una garantía.**

### Componentes: qué se reutiliza y qué es nuevo

| Pieza | Acción | Nota |
|---|---|---|
| `agent-kits/shared/knowledge-find.py` | **Nuevo** | Las tres capas + el índice FTS5 + la degradación |
| `tests/test_knowledge_find.py` | **Nuevo** | Determinismo, exit codes, topes |
| `tests/test_knowledge_index.py` | **Nuevo** | Biyección `ficheros ↔ filas` y `area` obligatoria |
| `tests/test_memory_path.py` | **Nuevo** | El camino SE RECORRE (gate barato, sin tokens) |
| `hooks/user-prompt-capture.sh` | **Nuevo** | `UserPromptSubmit`, log crudo + opt-out |
| `agent-kits/shared/task-brief.py` | Modificar | Sección 11: memoria técnica presupuestada |
| `hooks/session-context.sh` | Modificar | Bloque (4): memoria del área activa, tope propio |
| `agent-kits/shared/journal.py` | Modificar | `decisiones`/`pendientes` desde el log crudo + promoción |
| `hooks/session-journal.sh` | Modificar | Resumen opt-in por `claude -p`, degradación silenciosa |
| `agent-kits/shared/knowledge-check.md` | Modificar | El reparto por agente deja de ser solo prosa: apunta al script |
| `agent-kits/shared/doctor.py` | Modificar | Puntúa la salud de la memoria (hoy da «Instalación sana» con 0 entradas de journal) |
| `commands/retro.md` | Modificar | Se dispara al CERRAR una iniciativa, no cuando alguien se acuerda |
| `docs/knowledge/adr/`, `lessons/` | Añadir | ADR de las tres capas, revisión de `ADR-010`, lección |
| `docs/knowledge/` (mecanismo de curación) | **NO se toca** | Es el activo |

## Flujo (paso a paso)

**A. Un subagente implementa una tarea de área «hooks»**

1. `/dev-cycle` llama a `task-brief.py <carpeta> T-07`.
2. El brief lee `- **Tipo**: devops` y el texto de la tarea, y llama a `knowledge-find.py` con esa área.
3. `knowledge-find.py` abre `.claude/knowledge-index.sqlite`; el hash del corpus no cuadra (alguien
   añadió un ADR) → lo reconstruye desde los ficheros y responde.
4. Devuelve 3 aciertos compactos (~75 tokens). El brief los pega en su sección «Memoria técnica»,
   recortando al tope de 600 tokens si hiciera falta.
5. El subagente recibe `ADR-007 · aceptada · Hooks / implementer · …` **sin haber tenido que
   acordarse de una regla en prosa, resolver una ruta con `find` ni leer un índice de 3.685 tokens**.
6. Si necesita el detalle, ejecuta `knowledge-find.py --show ADR-007` — y solo entonces paga la
   entrada completa.

**B. Arranca una sesión**

1. `session-context.sh` compone lo de hoy (índice de piezas, roadmap, journal).
2. Añade el bloque (4): área de la iniciativa activa → N mejores aciertos, ≤ 300 tokens.
3. Recorta el total a `TOPE_CHARS = 9500` y emite. Sin memoria, sin iniciativa activa o sin
   aciertos → **no emite ese bloque** y el resto sale idéntico a hoy.

**C. Se cierra la sesión**

1. `UserPromptSubmit` ha ido acumulando los turnos del usuario en `.claude/session-prompts-<id>.log`
   (o no, si algún turno traía `<private>`).
2. `SessionEnd` escribe la entrada del journal. Con `sesion.resumen: true` y `claude` en PATH,
   extrae `decisiones` y `pendientes` con una llamada headless; si algo falla —cualquier cosa— cae
   al journal determinista de hoy **y el cierre de sesión no se entera**.
3. Un patrón que ya apareció en ≥ 2 entradas de journal se ofrece a `/retro` como candidata a
   lección con `estado: propuesta`.

## Alcance

- **Dentro (esta iteración):**
  - Las tres capas de `knowledge-find.py` con índice FTS5 reconstruible y degradación a recorrido plano.
  - El lint del índice: biyección `ficheros ↔ filas` y `area` obligatoria en cada fila.
  - Inyección presupuestada en `task-brief.py` y en `session-context.sh`, con tope y test por camino.
  - Prueba de que el camino se recorre: test determinista + casos en `evals/` + salud de memoria en `/doctor`.
  - Captura episódica: `UserPromptSubmit`, log crudo con opt-out, resumen escrito por el hook
    (opt-in + degradación) y promoción journal → candidata a lección.
  - Que la doctrina del plugin viaje como assets, sin volver a meter prosa en los prompts.
  - Cerrar el bucle: `/retro` disparado al cerrar iniciativa, doc ES/EN y las entradas de
    `docs/knowledge/` que salgan de aquí.
- **Fuera (siguientes specs):**
  - **Embeddings y vector store.** Con 31 entradas un grep bien ordenado gana: menos dependencias,
    resultado explicable y auditable. Se revisa si el corpus llega a varios cientos de entradas — y
    entonces `claude-mem` es el diseño de referencia.
  - **Captura de cada `PostToolUse`.** Decisión del usuario: ruido y coste.
  - **Sync entre máquinas o ámbito por usuario.** Nuestra memoria es por proyecto, dentro de su git.
  - **Retirar el journal.** El análisis daba dos salidas honestas (reforzarlo o retirarlo); el
    usuario eligió reforzarlo.
  - **Índice generado automáticamente en vez de a mano.** Aquí se VIGILA la biyección; generarlo es
    otra iniciativa.

## Manejo de errores

La regla del repo: **la degradación nunca bloquea.**

| Caso | Comportamiento |
|---|---|
| No existe `docs/knowledge/` | `knowledge-find.py` devuelve 0 aciertos y exit 0; el brief y el hook salen exactamente como hoy |
| Índice ausente | Se construye y se responde; `--json` trae `indice: "construido"` |
| Índice corrupto o hash que no cuadra | Se reconstruye; `indice: "reconstruido"` |
| No se puede escribir en `.claude/` o `sqlite3` sin FTS5 | **Recorrido plano de los ficheros**, `indice: "degradado"`, mismos aciertos, exit 0 |
| Consulta sin aciertos | 0 aciertos, exit 0, ni una línea de relleno (no gastar contexto para decir que no hay nada) |
| `--show <ID>` con ID inexistente | Mensaje de una línea a stderr y **exit 1** (es un error de uso, no una degradación) |
| Fila del índice sin `Área` | `tests/test_knowledge_index.py` falla nombrando el ID. Para los 12 ADR el `area` **solo** vive en el índice: perder la fila es perder el enrutado **sin poder reconstruirlo** |
| Entrada sin fila en el índice | El mismo test falla nombrando el fichero |
| Inyección que se pasaría del tope | Se recorta al tope y se dice en una línea; nunca se emite por encima |
| `<private>` en el turno del usuario | El log crudo **no se toca** (ni mtime ni tamaño) |
| `claude` no está en PATH / sin clave / `sesion.resumen` apagado | Journal determinista de hoy, exit 0, el cierre de sesión no se bloquea |
| `SessionEnd` con log crudo vacío | Entrada de journal como la de hoy (`decisiones: []` honesto, no inventado) |
| Journal con la misma `session_id` | Idempotente: se reescribe la misma entrada, no se duplica |

## Criterios de aceptación

Todos los topes son **numéricos y con la línea base de HOY al lado**. Los `[GWT]` se traducen 1:1 a
un bloque del test-plan cuando `qa` entre.

### Capa 3 — recuperación (Fase 1)

- [ ] [GWT] CA-01 — Dado el corpus de hoy (31 entradas, 21 áreas distintas), Cuando se ejecuta
  `python3 agent-kits/shared/knowledge-find.py --area estimacion --json`, Entonces devuelve las
  **9** entradas cuya área normaliza a `estimacion` (`grep -c "Estimación / calibración"
  docs/knowledge/README.md` → 9 hoy; ojo: las **6** que cita el análisis §1.5 son las *no citadas*,
  no las del área), cada acierto con `id · estado · area · titular · ruta`, la salida completa
  **≤ 300 tokens (≤ 1.200 caracteres)** y **exit 0**.
- [ ] [GWT] CA-02 — Dado el corpus de hoy, Cuando se ejecuta
  `knowledge-find.py "consola windows cp1252" --limit 5`, Entonces `GOT-005` es el primer acierto,
  hay **≤ 5** líneas, cada línea es **≤ 30 tokens (≤ 120 caracteres)** y **exit 0**.
- [ ] [GWT] CA-03 — Dado `ADR-010`, Cuando se ejecuta `knowledge-find.py --related ADR-010`,
  Entonces la salida trae el **grafo curado** (sucesor/sustituido, misma iniciativa, misma área) y
  **no** una cronología, en **≤ 400 tokens**, con **exit 0**.
- [ ] [GWT] CA-04 — Cuando se ejecuta `knowledge-find.py --show ADR-012`, Entonces sale la entrada
  completa en **≤ 2.700 tokens** (la entrada más grande hoy son 10.449 caracteres ≈ 2.612 tokens) y
  **exit 0**; con un ID inexistente, **exit 1** y una línea en stderr.
- [ ] [GWT] CA-05 — Dado `.claude/knowledge-index.sqlite` borrado, Cuando se consulta, Entonces el
  índice se construye, los aciertos son los mismos y `--json` trae `indice: "construido"`, **exit 0**.
- [ ] [GWT] CA-06 — Dado un índice de bytes basura (o un hash que no cuadra, o `.claude/` de solo
  lectura), Cuando se consulta, Entonces se reconstruye o se degrada a **recorrido plano** con los
  **mismos aciertos**, `indice: "degradado"` en el caso plano, y **exit 0 en los tres casos**.
- [ ] [GWT] CA-07 — Dado el índice de hoy, Cuando se borra una fila de `docs/knowledge/README.md`,
  Entonces `python3 -m pytest -q tests/test_knowledge_index.py` **falla nombrando el fichero sin
  fila**; y con una fila sin columna «Área», falla **nombrando el ID**.

### Llegada presupuestada (Fase 2)

- [ ] [GWT] CA-08 — Dada una tarea con `- **Tipo**: devops`, Cuando se ejecuta
  `python3 agent-kits/shared/task-brief.py <carpeta> T-XX`, Entonces el brief trae una sección
  «Memoria técnica» con los aciertos del área, esa sección es **≤ 600 tokens (≤ 2.400 caracteres)**
  y el brief completo **≤ 2.500 tokens** (línea base medida hoy: **1.818**; 7.452 caracteres en la
  re-medición de `changelog-brief` T-01), con **exit 0**.
- [ ] [GWT] CA-09 — Dado un proyecto sin `docs/knowledge/` o una tarea sin aciertos, Cuando se pide
  el brief, Entonces la salida es **idéntica a la de hoy** salvo la sección ausente, con **exit 0**
  (degradación silenciosa: ni aviso en stdout ni sección vacía).
- [ ] [GWT] CA-10 — Dada una iniciativa activa con área conocida, Cuando se ejecuta
  `echo '{"hook_event_name":"SessionStart","source":"startup"}' | bash hooks/session-context.sh`,
  Entonces el `additionalContext` trae **≤ 300 tokens (≤ 1.200 caracteres)** de memoria del área y
  el total sigue **≤ 9.500 caracteres** (`TOPE_CHARS`), con **exit 0**. Línea base de hoy: 872
  tokens, **0** de memoria curada.
- [ ] CA-11 — El reparto «qué lee cada agente» de `knowledge-check.md` deja de ser **solo prosa**:
  cada fila de su tabla nombra el comando de `knowledge-find.py` que le corresponde. *Verificación
  por lectura* — es prosa, y decir lo contrario sería fingir un test.

### Prueba de que el camino se recorre (Fase 3)

- [ ] [GWT] CA-12 — Cuando se ejecuta `python3 -m pytest -q tests/test_memory_path.py`, Entonces
  está **verde**; y Cuando se quita la inyección de `task-brief.py`, Entonces está **rojo** (el test
  se prueba con su mutante: un test que pasa con y sin la inyección no prueba nada).
- [ ] [GWT] CA-13 — Cuando se ejecuta `python3 evals/check.py`, Entonces **exit 0** con los casos
  nuevos del camino de memoria incluidos (línea base de hoy: 38 ficheros · 133 casos · 0 errores).
- [ ] [GWT] CA-14 — Dado un proyecto con 31 entradas curadas, **0** de journal y un índice inválido,
  Cuando se ejecuta `/doctor`, Entonces **NO** dice «Instalación sana», nombra las 31 curadas, dice
  que el índice no es válido y avisa de que `CALIBRATION.md` lleva **> 14 días** sin fila (hoy: 15,
  con 13 iniciativas cerradas después).

### Captura episódica (Fase 4)

- [ ] [GWT] CA-15 — Dado un turno del usuario, Cuando se dispara `UserPromptSubmit`, Entonces el
  turno queda en `.claude/session-prompts-<session_id>.log`, el fichero **no** entra en git
  (`git check-ignore` lo confirma: `*.log` ya está en `.gitignore`) y el hook sale **0**.
- [ ] [GWT] CA-16 — Dado un turno que contiene `<private>`, Cuando se dispara el hook, Entonces el
  log **no se toca** (mismo tamaño y mismo mtime) y el hook sale **0**.
- [ ] [GWT] CA-17 — Dado un log crudo con contenido, Cuando se dispara `SessionEnd`, Entonces la
  entrada del journal se escribe con `decisiones` y `pendientes` **no vacías**, y repetir con la
  misma `session_id` **no duplica** la entrada.
- [ ] [GWT] CA-18 — Dado `sesion.resumen` apagado, o `claude` fuera del PATH, o sin clave, Cuando se
  cierra la sesión, Entonces sale el journal **determinista de hoy**, exit **0**, y nada bloquea el
  cierre. (Los tres casos, por separado.)
- [ ] [GWT] CA-19 — Dado un patrón presente en ≥ 2 entradas de journal, Cuando se ejecuta `/retro`,
  Entonces aparece como **candidata a lección** con `estado: propuesta` (no como lección aceptada:
  la puerta de curación sigue siendo la revisión de dos lentes o el usuario).
- [ ] CA-20 — `ADR-010` queda **revisado, no borrado**: su restricción («el contrato de `SessionEnd`
  ignora la salida de los hooks») se mantiene como CIERTA y lo que cambia es la conclusión (el hook
  escribe en vez de devolver). Verificación por lectura del ADR.

### Que la doctrina viaje (Fase 5)

- [ ] [GWT] CA-21 — Dado un proyecto **sin** `docs/knowledge/`, Cuando se ejecuta
  `knowledge-find.py --doctrina --area estimacion`, Entonces devuelve las **9** lecciones de
  estimación desde los assets del plugin, con **exit 0**; y `--area estimacion` **sin** `--doctrina`
  devuelve **0 aciertos** con exit 0 (la memoria del proyecto sigue naciendo vacía, y eso es correcto).
- [ ] [GWT] CA-22 — Cuando se mide `wc -c agents/evaluator.md`, Entonces **no supera los 15.513
  bytes de hoy**: la pérdida de `LES-007/008/009` se deshace **sin volver a meter prosa en los
  prompts** (eran garantía dentro del prompt, se convirtieron en punteros a ficheros que el
  consumidor no tiene).

### Cerrar el bucle (Fase 6) — y la condición previa

- [ ] [GWT] CA-23 — Cuando se cierra una iniciativa (plan `completado`), Entonces `/retro` se
  **dispara** en vez de depender de que alguien se acuerde, y `CALIBRATION.md` gana su fila.
- [ ] CA-24 — Doc ES/EN de lo que aplique. *Nota de alcance verificada:* `docs/en/` espeja solo
  `CONVENTIONS.md`, `FLOWS.md`, `INSTALL.md`, `README.md` y `observability.md` — **no** el roadmap;
  así que el espejo EN afecta a la doc de producto que salga de la Fase 6, no a los cuatro
  documentos de esta carpeta.
- [ ] CA-25 — **El criterio de éxito de esta spec no se cumple sin la Fase 6.** El análisis lo dice
  como condición previa: «mientras la tubería que convierte experiencia en lección esté parada,
  reforzar la recuperación es afilar un grifo sin agua». Va **al final por dependencias** (necesita
  la promoción de la Fase 4 y la salud de la Fase 3), pero una entrega que se pare en la Fase 5 está
  **incompleta**, no «entregada al 83 %».

### Los siete criterios de superioridad frente a `claude-mem`

Están aquí como **criterios**, no como marketing: cada uno con qué lo hace verdad y cómo se comprueba.

| # | Criterio | Qué lo hace verdad | Se comprueba con |
|---|---|---|---|
| 1 | **Curación con estado** | Doctrina (`aceptada`) vs indicio (`propuesta`) vs `obsoleta` con sucesor, y el `estado` va **delante** en cada acierto. Ellos no pueden decirte si un recuerdo sigue siendo verdad | CA-01, CA-02 |
| 2 | **Auditable en un PR** | La memoria es un diff con fecha, fuente y autor; el índice es caché. La suya **ES** un SQLite | CA-05, CA-06 (índice reconstruible ⇒ los ficheros son la fuente) |
| 3 | **Cero dependencias** | Solo stdlib (`sqlite3` incluido). Ellos piden Node ≥ 20, Bun, uv, SQLite y un worker HTTP | `python3 scripts/lint_plugin.py` + los tests corriendo sin instalar nada |
| 4 | **Recuperación PROBADA** | Una eval que se pone **roja** si el camino de memoria no se recorre | CA-12, CA-13 |
| 5 | **Grafo curado en vez de cronología** | Sucesor/sustituido, misma iniciativa, misma área — mejor información al mismo coste que su `timeline` | CA-03 |
| 6 | **La doctrina viaja con el plugin** | `LES-001…009` como assets del plugin: el `evaluator` estima con ese fondo **el primer día**; la memoria del proyecto sigue naciendo vacía. Ellos no distinguen doctrina de experiencia | CA-21, CA-22 |
| 7 | **Presupuesto explícito por camino** | Cada punto de inyección tiene tope **medido** y un test que lo afirma | CA-08, CA-10 (y CA-01/CA-04 en la propia recuperación) |

## Pruebas

| Qué se prueba | Tipo | Dónde |
|---|---|---|
| Las tres capas: formato, orden, topes, exit codes | Unitario determinista | `tests/test_knowledge_find.py` |
| Índice: construcción, reconstrucción por hash, corrupción, degradación plana | Unitario con `tmp_path` | `tests/test_knowledge_find.py` |
| Biyección `ficheros ↔ filas` + `area` obligatoria | Unitario barato (como `tests/test_roadmap_index.py`, que existe por la misma razón) | `tests/test_knowledge_index.py` |
| El camino SE RECORRE (brief de área X trae entrada de área X) | Unitario **con mutante** | `tests/test_memory_path.py` |
| Que el agente lo use de verdad | Eval de activación (cuesta tokens reales) | `evals/cases/agent-implementer.json`, `agent-evaluator.json` |
| Salud de la memoria en el veredicto | Unitario | `agent-kits/shared/test_doctor.py` |
| Hooks nuevos en shell | Unitario de shell | `tests/test_hooks_shell.py` |
| Que nada de lo anterior baje | Suite completa | `python3 -m pytest -q` — **1.175 passed hoy**, no debe bajar |

**Regla dura de esta spec: ningún test nuevo puede depender de la red, de `claude` en el PATH ni de
una clave de API.** El único camino que los usa (`sesion.resumen`) se prueba con el subprocess
mockeado, como ya hace `evals/test_evals.py`.

## Referencias

- [`analysis.md`](analysis.md) — **la entrada de esta spec**. §1 (lo medido), §1.4 (los cinco
  huecos), §2 (comparativa con `claude-mem`), §3 (los cinco refuerzos), §4 (lo que NO dice).
- `docs/roadmap/CALIBRATION.md` — ratio vigente 479.326 tok/h (mediana de 5 muestras) y los 5
  aprendizajes acumulados.
- `.claude/rates.json` — tarifa 50 €/h, precios verificados el 2026-08-18, `tipoCambioUsdEur` 0,92
  (declarado como **supuesto**, no dato verificado).
- `agent-kits/shared/knowledge-check.md` — el único camino de recuperación que existe hoy (prosa en
  §REGLAS de 5 agentes).
- `agent-kits/shared/task-brief.py` — 10 secciones; `docs/knowledge/` no es ninguna de ellas.
- `hooks/session-context.sh:88` — `TOPE_CHARS = 9500`.
- `commands/dev-cycle.md:110` — «el subagente NO explora el repo entero».
- `docs/knowledge/adr/ADR-010-journal-memoria-de-sesion-determinista.md` — el ADR que esta spec revisa.
- `docs/knowledge/adr/ADR-006-un-fichero-por-entrada-gotchas-y-lecciones.md` — un fichero por entrada.
- `tests/test_roadmap_index.py` — el precedente exacto del lint de índice, y la prueba de la asimetría.
- [`thedotmack/claude-mem`](https://github.com/thedotmack/claude-mem) — diseño de referencia de la
  capa de recuperación. Su documentación pública **no publica el esquema de tablas ni el modelo que
  resume**: donde falta el dato, esta spec no lo rellena.

## Decisiones confirmadas (revisión del usuario · 2026-09-04)

1. **Captura: curada + episódica automática.** Se conserva la curación como doctrina y se añade la
   capa episódica que capture lo que hoy se pierde. **NO** se registra cada `PostToolUse`: es ruido y
   coste. **Confirmado.**
2. **Dependencias: solo stdlib, con SQLite FTS5.** `sqlite3` es stdlib, así que el índice de texto
   completo no añade ni una dependencia. **Sin embeddings. Confirmado.**

## Supuestos

- **La spec previa abarata la implementación** (`LES-006`, medido: −77 % en `quick-implement`, la
  única muestra con la spec ya escrita). Esta iniciativa **la tiene**, y por eso la evaluación aplica
  ese descuento — es un supuesto respaldado por **una** muestra, no por cinco.
- **`sqlite3` con FTS5 está disponible en el Python del consumidor.** Verifica: `python3 -c "import
  sqlite3; sqlite3.connect(':memory:').execute('CREATE VIRTUAL TABLE t USING fts5(x)')"`. Si no lo
  está, el camino plano cubre el caso (CA-06) — por eso la degradación es parte de la spec y no un
  añadido.
- **La `session_id` llega en el payload de `UserPromptSubmit`.** El contrato hay que verificarlo en
  la doc oficial **antes de implementar la Fase 4** y anotar la fecha, como hizo `memory-health` con
  `SessionEnd`. Hoy **no está verificado en esta spec**; si no llega, el log se nombra por fecha y
  el `SessionEnd` casa por mtime.
- **Por qué el journal está a 0 es inferencia, no medición** (`analysis.md` §5: lo más probable es
  que esas sesiones no corrieran con el plugin registrado). La Fase 4 no depende de esa causa: el
  hueco que cierra —`decisiones: []` **siempre** en modo hook— sí está medido.
- **17 de 31 entradas sin citar y la correlación con la fecha** están medidas; el **mecanismo** del
  arrastre («se cablea al nacer y nunca después») es lectura del analista, y así lo declara §5.
- Las horas **humanas** de la evaluación **no están validadas por ninguna muestra** (`CALIBRATION.md`
  aprendizaje 2: las 5 filas tienen 0 h humanas reales). Son las que no bajan y las de peor confianza.
