<!--
  FRAGMENTO COMPARTIDO: cuándo y dónde escribir memoria técnica del proyecto.
  Lo referencian los agentes/skills que ESCRIBEN conocimiento en su puerta de
  decisión o punto de nacimiento: planner, implementer (ADR), debug-root-cause
  (gotcha de causa raíz), qa (gotcha de flaky-patrón), /retro (lección técnica).
  Molde: mismo patrón que constitution-check.md. Si cambias el umbral aquí,
  cambia para todos — no lo dupliques en prompts.
-->

# Escribir en `docs/knowledge/` — paso compartido

`docs/knowledge/` es la memoria técnica **del proyecto**: `README.md` (índice de entrada), `adr/`
(un fichero por decisión), `gotchas/` (un fichero por entrada) y `lessons/` (un fichero por
entrada, agrupadas por agente en el nombre). **Si la carpeta no existe, créala en el primer
registro** — no hay opt-in que comprobar (D3, spec `2026-08-20-knowledge-capture`); su ausencia
nunca bloquea el trabajo en curso. **En proyectos consumidores nuevos, `gotchas/` y `lessons/`
nacen directas** (sin los stubs `gotchas.md`/`LESSONS.md` que arrastra este repo desde antes del
split de `knowledge-split` — la escritura remota no puede borrar ficheros en el disco del usuario,
así que los stubs solo existen aquí como redirección histórica).

## Umbral de registro (anti-burocracia)

**Orientación: 0-2 entradas por iniciativa.** No es un límite duro; es la señal de que el umbral
funciona. Más de ~3 en una sola iniciativa es indicio de umbral mal calibrado — se registra en la
retro, no se ignora.

- **ADR** solo si la decisión **cierra una alternativa** Y (**afecta a 2+ piezas** O **se tomó en
  una puerta** de decisión). Ejemplos de qué **NO** merece ADR: elegir el nombre de una variable;
  decidir el orden de dos párrafos en un documento; cualquier elección que, si se revirtiera
  mañana, no obligaría a tocar una segunda pieza.
- **Gotcha** solo si costó **≥1 ciclo de depuración** O **rompió/casi rompió una garantía del
  producto**. Ejemplos de qué **NO** merece gotcha: un typo corregido al vuelo; un test que falló
  una vez por una condición de carrera del propio entorno de CI, sin repetirse; cualquier fallo
  cuya causa ya está documentada en un gotcha existente (enlaza al que ya existe, no dupliques).

## Dónde escribe cada tipo

**Nomenclatura (las tres familias, `knowledge-ids`):** `ADR-NNN-<slug>.md` · `GOT-NNN-<slug>.md` ·
`LES-NNN-<agente>-<slug>.md` — numeración secuencial de 3 dígitos, un fichero por entrada, y el
número también va en `id:` dentro del frontmatter (`id: ADR-NNN` / `id: GOT-NNN` / `id: LES-NNN`).

| Tipo | Ruta | Plantilla |
|---|---|---|
| ADR | `docs/knowledge/adr/ADR-NNN-<slug>.md`. | `agent-kits/shared/templates/adr.md` |
| Gotcha | Fichero nuevo en `docs/knowledge/gotchas/GOT-NNN-<slug>.md` (frontmatter `id`/`tipo`/`area`/`estado`/`fuente` + síntoma · causa raíz · qué hacer en su lugar · evidencia/enlace al test de regresión). | ver ejemplo en cualquier entrada existente |
| Lección | Fichero nuevo en `docs/knowledge/lessons/LES-NNN-<agente>-<slug>.md` (frontmatter `id`/`tipo`/`area`/`estado`/`fuente`), agrupada por agente en el propio nombre del fichero. | ver ejemplo en cualquier entrada existente |

**Colisión de ID (las tres familias, misma regla).** Con lotes paralelos, el sufijo `<slug>` evita
pisar el FICHERO de otra iniciativa que elija el mismo `NNN` (fichero por entrada en los tres
tipos, sin colisión de FICHERO), pero **no** evita que dos entradas de la misma familia terminen
con el mismo `id:` en su frontmatter (dos ficheros distintos, mismo ID) — esa colisión de ID puede
darse en paralelo real y es precisamente el disparador que reactiva el índice+lint diferido (D4 de
la spec `knowledge-capture`: >15 entradas o la primera colisión de IDs, en cualquiera de las tres
familias). Mientras tanto, si detectas una colisión de ID al añadir tu entrada, renumera la tuya y
dilo en la retro.

## Autoría, estado y revisión

- Lo escribe **el agente que lo descubre**, en el momento en que es barato escribirlo (no
  reconstruido después).
- Toda entrada nueva nace con `estado: propuesta` — la valida la revisión de dos lentes o el
  usuario en la puerta antes de convertirse en doctrina que otros agentes leerán. Mientras está en
  `propuesta`, `knowledge-check.md` la presenta a quien la lea como propuesta pendiente, no como
  doctrina aplicable sin más.
- **Formato único de traza (obligatorio, lo usan los dos promotores de abajo):**
  `estado: aceptada (validada: <promotor>, AAAA-MM-DD[, intento N])` — donde `<promotor>` es
  `revisión de dos lentes` (con `, intento N`) o `usuario` (sin intento, no aplica). No hay un
  tercer formato; si ves uno distinto en una entrada existente, es un gap de esta misma regla y se
  corrige a este formato en el mismo cambio que lo detecte.
- **Promotor 1 — Contrato de promoción (`/dev-cycle`, revisión de dos lentes).** Al cerrar el
  bucle de revisión de una iniciativa **sin gaps de corrección pendientes** (0 gaps, todos
  rebatidos con evidencia, o aceptados como deuda por el usuario), las entradas `propuesta` que
  esa iniciativa escribió se promueven a `estado: aceptada (validada: revisión de dos lentes,
  AAAA-MM-DD, intento N)`, en el mismo cambio que cierra el bucle. Si la revisión no llega a
  cerrarse limpia (3.º intento con gaps sin resolver), la entrada se queda en `propuesta` hasta que
  el usuario la valide explícitamente.
- **Promotor 2 — Validación del usuario en `/retro` (paso 4-bis).** `/retro` corre sobre
  iniciativas ya **cerradas** — después de que su propio bucle de revisión de dos lentes ya
  promovió lo que tenía que promover — así que las entradas que escribe `/retro` NO tienen un
  bucle de revisión propio que las valide. Tras escribirlas, `/retro` ofrece al usuario en una
  línea validarlas ahora mismo: si dice que sí, pasan a `estado: aceptada (validada: usuario,
  AAAA-MM-DD)`; si prefiere dejarlo para luego, se quedan en `propuesta` (siguen siendo legibles,
  `knowledge-check.md` las presenta como pendientes, no como doctrina) hasta que alguien las valide
  explícitamente más adelante.
- **Actualiza el índice `docs/knowledge/README.md` en el mismo cambio** (una línea por entrada,
  con su etiqueta de área y su estado) — el índice generado está diferido (ver `knowledge-check.md`);
  mientras tanto, quien añade una entrada la indexa a mano.
- **Trazabilidad obligatoria:** toda entrada de backfill o derivada de otro documento (`retro.md`,
  una `spec.md`) enlaza a su fuente original. Una entrada sin fuente verificable, o que añade una
  conclusión que no estaba en el material de origen, es invención, no memoria — no se escribe así.
- **Contradicciones:** si una entrada nueva contradice una existente, la más reciente gana y la
  anterior pasa a `estado: obsoleta` con enlace a la que la sustituye — nunca se borra el rastro.
  Si una entrada contradice `docs/CONSTITUTION.md`, manda la constitución: la entrada se marca
  `obsoleta` y se dice en voz alta.
