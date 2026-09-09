---
id: ADR-014
titulo: El registro de piezas de proyecto es un agregado con la pieza como raíz — sus destinos van dentro, el runtime es un dato y no una clave del esquema, y sin registro no hay bucle
estado: propuesta
fecha: 2026-09-09
iniciativa: project-specialization
---

# ADR-014: El registro de piezas es un agregado — la pieza es la raíz, el runtime es un dato

## Contexto

La spec aprobada de `project-specialization` define la especialización por proyecto como **tercer
bucle** con la misma gramática que el ciclo y la memoria (registro canónico + puerta de entrada +
puerta de cierre), pero deja el esquema de `.claude/pieces.json` sin cerrar: su §Supuestos dice
literalmente que «lo cierra el `planner`». La evaluación corrigió eso y lo convirtió en arista del
grafo — `C-10` entra **antes** de `C-05` y `C-06` — porque con proyectos que ya tengan registro
escrito, cambiar su forma es **migración, no refactor**. Diez criterios de aceptación cuelgan de esta
decisión: CA-17 (propiedad por registro + hash), CA-18 (tope acumulado), CA-19b (`Bash`/`Write` solo
con confirmación registrada en la fila), CA-20 y CA-21 (una línea por fila en `/doctor` y biyección
registro↔ficheros con mutante de hash), CA-23 (`modificada`), CA-24 (adopción), CA-25 (idempotencia),
CA-26 (concurrencia con `.lock`) y CA-28 (una fila por ruta y runtime, cada una con su hash).

Se compararon tres opciones con los mismos siete criterios (`design.md` §3, ordenados por **coste de
la vuelta atrás**, no por coste de construcción): **O1** agregado con la pieza como raíz, **O2** dos
tablas normalizadas (`piezas` por nombre + `destinos` indexados por ruta, con el precedente literal
de `confluence-state.json`) y **O3** sin registro, con la procedencia marcada dentro del propio
fichero generado y el estado derivado de un escaneo del disco.

## Decisión

`.claude/pieces.json` es un **agregado**: una entrada por **pieza**, con sus N destinos anidados
dentro (el canónico de Claude Code más las variantes de cada runtime), y `agent-kits/shared/pieces-registry.py`
es su único dueño. La forma de una entrada es `{nombre, forma, area, origen, creada, evidencia,
confirmaciones, destinos: [{runtime, ruta, canonica, hash}]}`, con `version` y `hash_version` en la
cabecera y la regla «versión desconocida → solo lectura y aviso».

Con la misma fuerza que la elección de O1, y como **parte** de la decisión (no como apéndice), quedan
cerradas estas siete, cada una con su alternativa descartada abajo:

1. **El hash es `sha256` sobre los bytes del fichero completo con `\r\n` normalizado a `\n`**, guardado
   como `"sha256:<hex>"` y versionado por `hash_version`. Es la defensa contra el falso `modificada` de
   `GOT-007`: en `core.autocrlf=true` un `git checkout` re-materializa unos ficheros y no otros, y con
   bytes crudos toda pieza intacta se leería como modificada (ya costó una CI roja,
   `tests/test_doctrina_viaja.py:47-53`). El test lo sostiene con el mismo contenido en CRLF y en LF
   exigiendo el **mismo** hash.
2. **«Nunca corrupto» y «no perder una fila» son dos promesas con dos mecanismos y dos tests
   separados**: `temp + os.replace` (precedente `usage-meter.py:_save_state`) garantiza que el JSON
   nunca queda a medias; el `.lock` hermano serializa el leer-modificar-escribir. CA-26 pide las dos, y
   se prueban por separado: corrupción matando el proceso a mitad de escritura, y pérdida de fila con
   **dos procesos reales** (`subprocess`), no dos hilos.
3. **Lock ocupado → espera acotada (~3 s, el bucle de `journal.py`) y luego exit 4 con aviso**, nunca
   escribir sin cerrojo. La degradación silenciosa de `journal.py` es correcta para un log que solo
   **añade**; en un leer-modificar-escribir de un JSON compartido pierde la fila del otro en silencio.
   La **lectura** no toma cerrojo: el `replace` atómico hace que un lector nunca vea un fichero a medias.
4. **Idempotencia por bytes**: serialización canónica (piezas ordenadas por nombre, claves en orden
   fijo, `indent=2`, `ensure_ascii=False`) y no se escribe si los bytes no cambian → «sin cambios»,
   exit 0. Corolario que se acata: **en `pieces.json` no entra nada volátil** (ni `actualizado`, ni
   contadores, ni fecha de última auditoría); eso vive en `pieces-state.json`, ignorado. El `estado`
   tampoco se persiste: se deriva del hash en cada lectura.
5. **`dueno(<ruta>)` es la única puerta de `GOT-003`**: escribir o retirar exige fila con hash
   coincidente, o **exit 3** diciéndolo. Confirmación extra anotada en la fila si la raíz del destino
   tiene marcadores `agent-kits/` o `.claude-plugin/`; `pieces.json`, `pieces-state.json` y
   `pieces.json.lock` son nombres reservados, no adoptables.
6. **`runtime` es un dato, nunca una clave del esquema.** El script recibe `--destino <ruta>:<runtime-id>`
   y no valida el id contra una lista cerrada; el conocimiento de runtimes vive donde ya vive
   (`install/providers.mjs` `PROVIDERS`/`IDS`). Esto es lo que hace que un cuarto proveedor sea una fila
   de datos y **no una migración** del registro.
7. **Degradación sin bloqueo**: sin `pieces.json` → registro vacío, todo `no gestionada`, exit 0;
   corrupto → se lee como vacío **con aviso** y la escritura se rehúsa (exit 2) nombrando el arreglo
   (`--reconstruir`, que aparta el fichero a `pieces.json.corrupto-<ts>`). Privacidad: `redactar()` se
   **importa** de `journal.py:200`, no se reimplementa (`LES-013`), y una ruta bajo `docs/security-scan/`
   no se cita.

El contrato que consumen `C-05`, `C-06` y `C-11`: subcomandos `estado` · `dueno` · `registrar` ·
`adopt` · `listar [--json]` · `auditar` · `tope`, con exit codes **0** ok · **1** hallazgos de
`auditar` · **2** registro ilegible o corrupto · **3** rehusado por propiedad · **4** registro ocupado
· **5** tope superado sin confirmación.

## Alternativas descartadas

- **O2 — dos tablas normalizadas (`piezas` por nombre + `destinos` por ruta).** Era la rival real, con
  precedente en el repo (`confluence-state.json` es un manifiesto `ruta → {hash, pageId}`,
  `tests/test_confluence_scope.py:167`) y con la regla dura de `GOT-003` reducida a un `destinos.get(ruta)`:
  la forma del fichero **es** el índice. Se descarta por el criterio 4 del diseño, «mejor un estado
  inválido irrepresentable que uno detectado por auditoría»: en O1 el estado inválido **«un destino sin
  pieza dueña» es irrepresentable por construcción**, mientras que en O2 es representable y obliga a una
  **invariante extra de integridad referencial**, con su test y su mutante, dentro de un presupuesto de
  5,0 h y ~25-30 tests que ya tiene que cubrir cerrojo real, tres estados, idempotencia, adopción y
  `GOT-003`. Y por el criterio 3: en O1 el tope de CA-18 es exactamente `len(piezas)`, el recuento
  acumulado que la spec pide, **sin cálculo intermedio** ni deduplicación por nombre, y `evidencia` y
  `confirmaciones` viven una sola vez por pieza en vez de repetidas por runtime. Lo que O1 paga a cambio
  —un índice invertido ruta→destino y el rechazo de rutas duplicadas entre piezas— es una función
  encapsulada en `dueno()` y dos tests. **La decisión es reversible en la dirección que importa**: si
  algún día pesa más el *lookup* por ruta, O1 → O2 es un **aplanado determinista y sin pérdida**; el
  camino inverso solo es fiable si la referencia `pieza` está sana, así que se elige la opción que deja
  la puerta abierta.
- **O3 — sin registro: procedencia marcada en el propio fichero y estado derivado de un escaneo.** Hay
  que decir primero lo que tenía a favor, porque era mucho: era la **más simple y la más barata**
  (complejidad **Baja**, coste relativo **S**, la que menos código nuevo pedía). Cero esquema y por tanto
  **cero migración** —desaparecía el riesgo (c) que la evaluación anota sobre `C-10`—, cero cerrojo y
  cero concurrencia porque no hay fichero compartido que reescribir, cero conflictos de merge, y una
  biyección registro↔ficheros que no puede desincronizarse porque no hay registro. **Se descarta por un
  argumento de fondo, y es el decisivo**: sin fila en un registro, la confirmación de que una pieza puede
  usar `Bash`/`Write` (CA-19b) solo cabría en la marca de procedencia **dentro del propio fichero de la
  pieza**. Es decir, el permiso quedaría **autodeclarado por el mismo artefacto que gobierna**, y es
  justo el artefacto que un humano puede editar a mano. Con `ADR-007` delante —un `deny` solo vive con
  alcance de agente, y la decisión en un script determinista— eso basta para cerrar O3. El coste
  secundario, que no es el principal: rompería CA-18, CA-19b, CA-21, CA-26 y CA-28 tal como están
  escritos, y contradiría `analysis.md` §2, donde el tercer bucle se **define** por tener registro
  canónico con test de biyección, igual que `tasks.md` y `docs/knowledge/README.md`; sin él, `/doctor`
  auditaría un escaneo y no un acuerdo del equipo.
- **Hashear los bytes crudos** — caso 2 de `GOT-007`: falso `modificada` en cada `git checkout`
  (ver decisión 1). **Hashear el blob de git** (`git hash-object`) — exige `git` en PATH y el registro
  tiene que funcionar sin él. **Excluir el frontmatter o los campos generados** — obliga a un segundo
  normalizador sincronizado con el generador, y cualquier desfase se lee como `modificada`.
- **Confiar solo en el cerrojo** (sin escritura atómica) — un proceso muerto a mitad de escritura deja el
  JSON roto aunque el cerrojo fuese perfecto; es el fallo que el repo ya pagó en `debt-cleanup`.
- **Escribir sin cerrojo cuando no se consigue**, que es lo que hace `journal.py` — correcto para un log
  de *append*, incorrecto para un leer-modificar-escribir (ver decisión 3).
- **Un campo `actualizado` por fila** — rompe la idempotencia por bytes, ensucia el diff en cada corrida
  y convierte un fichero comiteado en ruido de merge.
- **Comprobar la propiedad por carpeta** («si está en `.claude/personas/` es mío») — es exactamente el
  fallo de `GOT-003`, donde un generador pisó un canónico dentro del árbol que espejaba.
- **Enumerar los runtimes en el esquema** (claves `codex`/`opencode`) — convierte cada proveedor nuevo en
  una migración del registro, que es justo lo que la decisión 6 evita.
- **Reconstruir el registro corrupto en silencio** — pisa un fichero comiteado y compartido por el equipo
  sin que nadie lo haya pedido.
- **Un fichero por pieza** (`.claude/pieces/<nombre>.json` + índice), al estilo de `ADR-006` — no se
  descarta por técnica sino por **alcance**: la spec aprobada fija `.claude/pieces.json` como fichero
  único y seis CA lo nombran por ruta, así que alinearlo con `ADR-006` sería un cambio de **spec**, no de
  diseño. Queda anotado en `design.md` §7 y no se reabre por cuenta propia.

## Consecuencias

Se gana que las dos operaciones peligrosas del bucle tengan una sola puerta cada una —`dueno()` para la
propiedad (`GOT-003`) y el par cerrojo + `replace` para la escritura— y que el tope de CA-18 sea una
propiedad legible del fichero (`len(piezas)`) en vez de un cálculo. Se renuncia al `dict.get` por ruta:
la búsqueda ruta→pieza pasa por un índice invertido construido al cargar, lo que añade la obligación de
rechazar la misma ruta en dos piezas y el cuidado de no consultar el índice sobre un registro ya mutado
en memoria. Queda condicionado a este ADR el contrato que consumen `C-05` (`/specialize`), `C-06`
(`/doctor`) y `C-11` (`export-interop.py --root`): cualquiera de los tres que necesite un campo nuevo
sube `version`, no reinterpreta el esquema. Y quedan dos filas nuevas en la regla 9 de `docs/CONVENTIONS.md`
(`pieces.json` comiteada, `pieces-state.json` ignorada) más el script nuevo en la tabla `MODOS` de
`tests/test_console_encoding.py`.

## Estado

`propuesta` — la opción **O1** la eligió el usuario en la puerta de diseño del 2026-09-09 (`design.md`
`aprobado`, `opcion_elegida: O1`); el ADR pasa a `aceptada` cuando la revisión de dos lentes valide la
implementación de `C-10` contra este esquema, y a `obsoleta` si una decisión posterior lo reemplaza.
