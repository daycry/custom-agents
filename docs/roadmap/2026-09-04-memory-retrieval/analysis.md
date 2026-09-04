---
analisis: memory-retrieval
descripcion: >
  Auditoría medida de cómo `custom-agents` gestiona la memoria y —sobre todo— cómo se RECUPERAN los
  aprendizajes, comparada con `claude-mem` (thedotmack/claude-mem), y qué reforzar. Precede a la
  spec: aquí no hay plan ni presupuesto, solo el diagnóstico con evidencia y las opciones.
estado: borrador
creado: 2026-09-04
fuente: petición del usuario (2026-09-04) tras publicar v1.16.0
---

# Memoria y recuperación de aprendizajes — diagnóstico y refuerzo

## El resumen en una frase

**Escribimos memoria muy bien y la recuperamos muy mal.** La captura está curada, fechada,
revisada y versionada; la recuperación es una intención escrita en prosa dentro de la sección
REGLAS de cinco agentes, sin índice consultable, sin búsqueda, sin inyección y sin ningún test que
compruebe que alguien la recorrió. La prueba no es una opinión: **17 de las 31 entradas de
`docs/knowledge/` no las cita ninguna pieza ejecutable del plugin**, y son exactamente las más
antiguas.

## Las tres cifras que resumen el estado

| Medida | Hoy |
|---|---|
| Tokens de memoria curada inyectados al arrancar una sesión | **0** de 872 |
| Entradas del journal (memoria episódica) desde que se construyó | **0** |
| Entradas de `docs/knowledge/` que ninguna pieza cita | **17 de 31 (55 %)** |

---

## 1. Qué tenemos, medido

### 1.1 La memoria curada — el activo

`docs/knowledge/`: **31 entradas, 108.443 caracteres (≈27.100 tokens)**, todas en `estado: aceptada`.

| Familia | Entradas | ≈Tokens | Quién escribe |
|---|---|---|---|
| `adr/` | 12 | 13.289 | `architect`, `planner`, `implementer` |
| `gotchas/` | 5 | 4.377 | `qa`, skill `debug-root-cause` |
| `lessons/` | 14 | 5.760 | `/retro` |
| `README.md` (índice, 31 filas) | 1 | 3.685 | quien añade la entrada |
| `journal/` | **0** | — | hook `SessionEnd` |

La calidad es alta y el mecanismo de promoción funciona: `propuesta` → `aceptada` la firma la
revisión de dos lentes o el usuario. Nada de esto está roto.

### 1.2 Lo que se inyecta hoy al arrancar

`hooks/session-context.sh` (evento `SessionStart`, matcher `startup|resume|compact`) compone
**3.490 caracteres ≈ 872 tokens**, y son íntegramente el **índice de piezas** del plugin —
comandos, skills y agentes con su descripción recortada. Ni una lección, ni un gotcha, ni un ADR,
ni una línea de journal.

| `source` | ≈Tokens | Índice de piezas | Roadmap activo | Journal | **Conocimiento** |
|---|---|---|---|---|---|
| `startup` | 1.105 | sí | sí | sí | **no** |
| `resume` | 1.105 | sí | sí | sí | **no** |
| `compact` | 986 | sí | sí | no | **no** |
| `clear`, `fork` | 0 | — | — | — | — |

### 1.3 El único camino de recuperación que existe

`agent-kits/shared/knowledge-check.md` — un fragmento de **prosa** que cinco agentes referencian.
Dice: comprueba si existe `docs/knowledge/`, lee su `README.md`, y abre **solo** las entradas cuya
columna «Área» toque tu tarea.

Para que un aprendizaje llegue a un agente, el modelo tiene que encadenar **seis decisiones**, todas
suyas y ninguna verificada:

1. acordarse de que la regla existe (está en su §REGLAS, no en su flujo numerado);
2. resolver la ruta del kit compartido con un `find`;
3. leer `knowledge-check.md`;
4. leer el índice — **3.685 tokens**;
5. juzgar si el «Área» de una entrada toca la tarea que tiene delante;
6. abrir el fichero.

Y hay un séptimo problema: **para los 12 ADR, el campo `area` solo existe en el índice**, no en el
fichero. Si el índice se desincroniza, el enrutado de esos 12 no se puede reconstruir.

### 1.4 Los cinco huecos, sin adornar

1. **`task-brief.py` no inyecta memoria, y en modo subagentes eso es una puerta cerrada, no una
   omisión.** El brief tiene 10 secciones (tarea, fase, persona, arquitectura, constitución,
   verificación, TDD, diseño, gaps de la revisión, contrato) y `docs/knowledge/` no es una de ellas
   — medido: `grep` sobre `task-brief.py` da un solo acierto, y es un comentario de encoding.
   Mientras `commands/dev-cycle.md:110` ordena «el subagente NO explora el repo entero: el brief y
   los ficheros que referencia», **quien escribe el código no puede alcanzar un gotcha ni
   queriendo**. Es el hueco más caro porque es el modo que el plugin promociona.
2. **No hay búsqueda.** Cero grep, cero índice consultable por máquina, cero embeddings sobre
   `adr/`, `gotchas/` y `lessons/`. El único `grep` del repo contra `docs/knowledge/` está en
   `commands/retro.md:15` y va contra el journal. El propio índice admite que
   `knowledge-lint.py` «sigue diferido, se retoma con >15 entradas»: hay **31**.
3. **El journal está a 0, y aun poblado no captura razonamiento.** El mecanismo funciona (verificado
   generando una entrada), pero `decisiones: []` y `pendientes: []` están vacías **siempre** en modo
   hook, y el `resumen` es el primer prompt del usuario recortado a 160 caracteres. Lo que persiste
   son nombres de ficheros y cambios de estado de tareas.
4. **La memoria no viaja con el plugin: viaja el método y se queda el conocimiento.** Un proyecto
   recién instalado nace con `docs/knowledge/` vacía. Y las tres lecciones de estimación que **antes
   iban garantizadas dentro del prompt del `evaluator`** (`LES-007/008/009`) se sacaron a ficheros
   que el consumidor no tendrá: se cambió una garantía por una intención.
5. **El índice —única puerta de entrada— no lo vigila nada.** Ni `lint_plugin.py` (0 aciertos de
   `knowledge`), ni ningún test. Y la asimetría es demostrable: `tests/test_roadmap_index.py` existe
   precisamente para vigilar que el índice **hermano** del roadmap tenga su fila y dentro de la
   tabla. El de memoria no tiene equivalente.

### 1.5 El patrón que lo explica todo

Los IDs **citados** son exactamente los recientes (`ADR-007…012`, `GOT-004/005`, `LES-010/012/013`,
del 2026-09-02 en adelante). Los **no citados** son exactamente los antiguos (`ADR-001…006`,
`GOT-001…003`, `LES-001…006`, del 2026-08-20).

El cableado ocurre **en el momento de escribir la entrada**, arrastrado por la iniciativa que la
produce, y **nunca después**. Una entrada que no se cableó al nacer no se cablea jamás. Y las seis
lecciones de estimación —las que más deberían pesar en cada `/pm-cycle`— están entre las que nadie
cita.

Corolario incómodo: `/retro`, que es la tubería que convierte experiencia en lección, lleva **15
días parada**. Se han cerrado 13 iniciativas después de la última fila de `CALIBRATION.md`.

---

## 2. Qué hace `claude-mem`, y en qué se parece poco a nosotros

[`thedotmack/claude-mem`](https://github.com/thedotmack/claude-mem) resuelve el problema
**contrario**: captura sin filtro y recupera con precisión.

| Dimensión | `claude-mem` | `custom-agents` |
|---|---|---|
| **Qué captura** | toda observación de uso de herramientas, más los prompts del usuario | 0-2 entradas curadas por iniciativa |
| **Cuándo** | hooks `SessionStart`, `UserPromptSubmit`, `PostToolUse`, `Stop`, `SessionEnd` | `SessionEnd` (journal) + escritura manual del agente |
| **Compresión** | resumen semántico por IA al cerrar sesión | ninguna: lo escribe una persona o un agente, en prosa |
| **Almacén** | SQLite + FTS5 (texto completo) + Chroma (vectores), en `~/.claude-mem/` | ficheros Markdown versionados en el git del proyecto |
| **Recuperación** | **tres herramientas MCP**: `search` (índice compacto, ~50-100 tokens por acierto) → `timeline` (contexto cronológico) → `get_observations(ids[])` (detalle, ~500-1.000 tokens) | prosa en §REGLAS de 5 agentes + leer un índice de 3.685 tokens |
| **Presupuesto de tokens** | explícito: filtra antes de traer, «~10× de ahorro» declarado | implícito: «no leas por leer» |
| **Ámbito** | por usuario/máquina, con proyecto como filtro; sync opcional | por proyecto, dentro de su git |
| **Curación** | ninguna — todo entra | alta: revisión de dos lentes, `estado`, fecha, fuente |
| **Auditable en revisión de código** | no | sí — es un diff |
| **Privacidad** | opt-out con etiquetas `<private>` | por construcción: solo entra lo que alguien escribe |

### Lo que hacen mejor, y por qué nos importa

**a) La recuperación es una herramienta, no una intención.** El agente *llama* a `search` y recibe
aciertos con ID y coste conocido. No tiene que acordarse de un fragmento de prosa, ni resolver una
ruta, ni juzgar una columna «Área». Nosotros tenemos scripts deterministas para todo —
`skill-index.py`, `progress-report.py`, `coverage-gate.py` — **menos para lo único que un agente
necesita consultar en cada tarea**.

**b) La divulgación progresiva está presupuestada en tokens, con tres capas.** Nuestra progressive
disclosure es real en intención pero su primer escalón cuesta 3.685 tokens y devuelve 31 filas de
prosa; el suyo cuesta 50-100 tokens por acierto y devuelve IDs. Y nuestro corpus completo son 27.100
tokens: **no cabe** por el camino del hook (tope de 9.500 caracteres), así que buscar-y-luego-traer
no es una preferencia, es la única arquitectura posible.

**c) El hook que resume no necesita que Claude Code lo escuche.** `ADR-010` decidió no hacer resumen
por IA porque «el contrato oficial de `SessionEnd` ignora la salida de los hooks». La restricción es
cierta, pero la conclusión fue demasiado fuerte: `claude-mem` no *devuelve* el resumen, **lo escribe
él mismo** desde el hook. Eso convierte `decisiones: []` de limitación estructural en decisión
revisable.

**d) Capturan el turno del usuario.** Tienen `UserPromptSubmit`; nosotros no. Todo lo que decide el
usuario en una conversación —como la que originó este análisis— sobrevive solo si un agente decide
convertirlo en ADR.

### Lo que hacemos mejor, y no hay que perder

- **Señal por ruido.** 31 entradas revisadas valen más que 10.000 observaciones sin filtrar, y su
  corpus crece sin techo mientras el nuestro cabe en la cabeza de una persona.
- **Es un diff.** Un ADR se revisa en un PR, tiene fecha, fuente y estado, y se puede rebatir. Una
  observación autogenerada en un SQLite no.
- **Estado explícito.** `propuesta` / `aceptada` / `obsoleta` con sucesor: sabemos qué es doctrina y
  qué es indicio. Ellos no distinguen.
- **Cero dependencias y cero servicios.** Ellos piden Node ≥20, Bun, uv, SQLite y un worker HTTP.
  Nuestra memoria son ficheros de texto en git — y esa es la razón por la que se puede auditar.

**Conclusión: no hay que adoptar `claude-mem`. Hay que robarle la capa de recuperación y conservar
nuestra curación.** Los dos sistemas fallan en espejo: ellos tienen recuperación excelente sobre un
corpus sin curar; nosotros, un corpus curado que casi nadie recupera.

---

## 3. Qué reforzar — cinco cambios, por relación coste/impacto

### R1 — `knowledge-find.py`: la búsqueda que falta (el que más rinde)

Un script determinista, sin dependencias, que sustituya «lee el índice y decide» por «pregunta y
recibe». Contrato propuesto:

```bash
python3 knowledge-find.py --area estimacion --tipo lesson --json
python3 knowledge-find.py "transición de Jira por nombre" --limit 5
```

Devuelve **una línea por acierto** (≈20-30 tokens: `ID · estado · área · titular · ruta`), ordenada
por relevancia y con el `estado` delante para que el lector sepa si es doctrina o indicio. El detalle
se abre después, por ID, y solo el que haga falta — las tres capas de `claude-mem` con nuestro
formato. Determinista, con tests y exit codes, como el resto del repo. El índice deja de ser un
fichero que hay que leer y pasa a ser un dato que se consulta.

### R2 — Memoria en el brief: cerrar la puerta cerrada

`task-brief.py` gana una sección con **los aciertos de `knowledge-find.py`** para el área y el tipo
de la tarea (`- **Tipo**: frontend|backend|db|devops|test|docs` ya está en el ledger, así que el
enrutado existe). Con un tope explícito —del orden de 400-600 tokens, frente a los 1.818 que mide el
brief hoy— y degradación en silencio si no hay carpeta o no hay aciertos.

Esto convierte el hueco más caro en el camino más fiable: el subagente **recibe** los gotchas de su
área sin tener que buscarlos, igual que ya recibe los gaps de la última revisión.

### R3 — El índice, vigilado como su hermano

`tests/test_roadmap_index.py` existe porque una fila fuera de la tabla pasó desapercibida. El índice
de memoria necesita lo mismo, y por la misma razón: una entrada sin fila **es invisible** para el
único camino de lectura, y no hay grep de respaldo. Un test que afirme la biyección
`ficheros ↔ filas` (más `area` presente en cada fila, que para los ADR es el único sitio donde vive)
cuesta muy poco y cierra un fallo silencioso. Con R1 en el repo, el propio `knowledge-find.py` puede
ser quien lo compruebe.

### R4 — Que la doctrina viaje con el plugin

Hoy el plugin lleva el método y deja el conocimiento. Hay que separar dos cosas que hemos mezclado:

- **Memoria del proyecto** (`docs/knowledge/` del consumidor): sus decisiones, sus trampas, sus
  lecciones. Nace vacía, y eso es correcto.
- **Doctrina del plugin**: lecciones que son ciertas para cualquier proyecto que use estos agentes
  — las de estimación y calibración (`LES-001…009`) son el caso obvio. Esas deberían viajar como
  **assets del plugin** y ser el fondo sobre el que el `evaluator` estima el primer día, no algo que
  el consumidor tiene que descubrir por su cuenta. `LES-007/008/009` estaban garantizadas dentro del
  prompt y se convirtieron en punteros a ficheros inexistentes: hay que deshacer esa pérdida sin
  volver a meter prosa en los prompts.

### R5 — El journal: o captura decisiones, o se retira

Está a 0 entradas y su diseño garantiza `decisiones: []`. Dos salidas honestas, y hay que elegir una:

- **Reforzarlo** con lo que enseña `claude-mem`: un `UserPromptSubmit` que registre el turno del
  usuario, y un resumen que el propio hook escriba en disco en vez de devolverlo a Claude Code
  (`ADR-010` se revisa: la restricción del contrato es real, la conclusión era demasiado fuerte).
- **O retirarlo** y decir que la memoria episódica de este plugin es el ledger, que sí está lleno
  (28 ledgers, 740.745 caracteres) y sí se lee.

Lo que no vale es dejar una carpeta que promete bitácora y lleva 0 entradas mientras `/doctor` da la
instalación por «sana».

### Y una condición previa para todo lo demás

**`/retro` no puede seguir siendo un comando que alguien recuerda.** Es la única tubería que convierte
experiencia en lección, y lleva 15 días parada con 13 iniciativas cerradas. Mientras no se dispare al
cerrar una iniciativa, reforzar la recuperación es afilar un grifo que no tiene agua.

---

## 4. Lo que este análisis NO dice

- **No propone embeddings ni un servicio.** Con 31 entradas, un grep bien ordenado gana a un vector
  store: menos dependencias, resultado explicable y auditable. Si el corpus llegara a varios cientos
  de entradas, esa decisión se revisa — y entonces `claude-mem` es el diseño de referencia.
- **No propone capturar todo.** Nuestra ventaja es la señal, y una captura sin filtro la destruiría.
  Lo que hay que copiar es cómo se **encuentra**, no cuánto se guarda.
- **No está presupuestado.** Aquí no hay horas, ni tokens, ni orden de ejecución: eso es
  `/pm-cycle` con el `evaluator`, y este fichero es su entrada.

## 5. Procedencia de las cifras

Todo lo numérico de §1 está medido sobre el repo en `a7a11b0..HEAD` (v1.16.0 más la rama
`changelog-brief`), ejecutando los scripts y contando los ficheros — no estimado. Lo de §2 sale del
README y la documentación pública de `claude-mem`, que describe la arquitectura pero **no publica el
esquema exacto de tablas ni el modelo que resume**: donde falta el dato, el análisis lo dice en vez
de rellenarlo. Dos cosas quedan como inferencia razonada y no como medición: por qué el journal está
a 0 (el mecanismo funciona; lo más probable es que estas sesiones no corran con el plugin registrado)
y por qué la citación se correlaciona con la fecha (la correlación está medida; el mecanismo del
arrastre es lectura mía).
