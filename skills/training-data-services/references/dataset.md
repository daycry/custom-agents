# Dataset Gold, near-duplicates y puente al Curator (training-data-services)

> Lee esto solo al llegar a los pasos 6-7 de `SKILL.md` (ensamblar el dataset, proponer un caso Gold
> a `knowledge-curator`). Los contratos ejecutables viven en los docstrings de `scripts/dedup.py`,
> `scripts/dataset-assembler.py` y `scripts/propose-from-case.py`.

## Near-duplicates (`scripts/dedup.py`, CA-10)

Sin embeddings, sin modelo y sin red: shingles de palabras + Jaccard, la técnica de duplicados de
`code-health` (la función `shingles` es una copia declarada en `agent-kits/shared/copias.json`; las
skills son standalone y no se importan entre sí).

- **Texto comparado**: el contenido VARIABLE del caso — petición + contexto + trayectoria (rol,
  contenido, herramienta y argumentos). Ni restricciones, ni métricas, ni marcas de tiempo. Cada
  shingle es un entero de 64 bits (`blake2b`), igual en todos los sistemas; el texto se descarta al
  shinglearlo.
- **Boilerplate**: un shingle presente en más de `--boilerplate` (0.5) de los casos se ignora
  (prompt de sistema, plantillas), pero solo con **20 casos o más**: por debajo no se filtra nada (lo
  que comparten dos near-duplicates entre familias no es plantilla). Sin condición de familias. Límite
  declarado: un bloque en más de la mitad de los casos es plantilla por definición. `--boilerplate 1.0`
  apaga el filtro.
- **Aviso, no decisión**: un caso que conserva menos del 20 % de sus shingles tras quitar la
  plantilla sale en `avisos` («near-duplicate no evaluable sobre la plantilla»); se compara con lo que
  le queda.
- **Umbral**: Jaccard ≥ `--umbral` (0.8), comparado con enteros; ventana de `--ventana` (3) palabras.
- **Muestreo por valor**: con más de `--presupuesto` (10⁷) shingles en total (~60 MiB de texto) se
  conserva cada shingle con hash `< r·2⁶⁴`, `r = presupuesto / total` global; df, plantilla, filtros y
  Jaccard son exactos SOBRE la muestra, no respecto al Jaccard real: el error típico de la estimación
  es `±z·√(J(1−J)/k)`, con k = shingles muestreados de la unión del par (1 000 shingles por caso y
  `r = 0.1`: k ≈ 110, ±0,076 con z = 2). La salida declara `jaccard: exacto|muestreado` y `r`. Límite:
  con `r < 1` un caso pequeño puede quedarse sin muestras (aviso; solo se agrupa con un duplicado exacto).
- **Cruce conservador** (solo con `r < 1`): en el ensamblador, un par que CRUZA train/benchmark se
  trata como near-duplicate si su Jaccard muestreado es `≥ umbral − margen` (el margen de arriba, con
  z = 2 y como mucho 0,2): el de train sale de train. Dentro de una partición manda el umbral. El
  manifiesto lo declara (`near_duplicates.cruce`, `cruces_near_duplicates`).
- **Escala**: duplicados exactos colapsados antes (huella del conjunto completo); índice PPJoin solo
  del *mid-prefix*, sondeo con el prefijo, filtro posicional y de longitud (exacto sobre los conjuntos
  comparados —la muestra, con `r < 1`—: ningún par con Jaccard ≥ umbral se pierde). El índice agrupa
  los casos de cada shingle por grupo: dentro de un grupo de m near-duplicates el coste es O(m·|x|).
  Peor caso real declarado: m casos que comparten muchos shingles del prefijo SIN llegar al umbral,
  O(m²·|x|) escaneos; texto común por debajo de la plantilla → 0 escaneos del índice. Cifras medidas
  en la Evidencia de T-07 y de la verificación fix1/fix2 del ledger. Grupos = componentes conexas,
  deterministas.
- A mano: `python3 scripts/dedup.py <docs.jsonl> [--umbral] [--ventana] [--boilerplate] [--presupuesto] [--json]`
  (una línea `{"id", "family", "text"}` por caso; exit 0 · 2 uso o JSONL ilegible).

## Ensamblar (`scripts/dataset-assembler.py`, CA-03/CA-06/CA-11/CA-12)

```text
python3 scripts/dataset-assembler.py --benchmark <family>[,<family>…] [--umbral 0.8] [--ventana 3]
        [--boilerplate 0.5] [--presupuesto 10000000] [--conservar-duplicados] [--fecha AAAAMMDD]
        [--dry-run] [--espera-bloqueo 120] [--config <training.json>] [--project-root <dir>]
```

1. **Solo Gold**: `validation.status == "approved"` **y** `approved_by_human` exactamente `true`, leídos
   de `validation.json` EN DISCO por descriptor (nunca del índice, que es una caché). Cada versión Gold
   se lee entera (sus ocho ficheros, sin seguir enlaces, con `vNNN` y `final/` comprobados antes y
   después, como mucho 16 MiB por fichero) y tiene que pasar el esquema; lo incompleto, en curso,
   enlazado, demasiado grande o incoherente se omite con motivo.
2. **Gold atado al contenido**: `set-status approved` guarda `content_hash`; si ya no casa con los
   ficheros, el caso se excluye («Gold sin atar al contenido aprobado»). Sin `content_hash` (Gold
   anterior, o `record --approved-by-human`): se exporta con aviso «sin hash de aprobación». Límite:
   detecta cambios accidentales o del código del proyecto tras aprobar; **no protege frente a quien puede escribir el store**, que puede recalcular el hash (sha256 sin clave).
3. **Benchmark declarado**: las familias de `--benchmark` van ENTERAS a benchmark; el resto, enteras a
   train. Sin `--benchmark`, o con una familia declarada sin casos Gold, **exit 1 y no se escribe nada**.
4. **Near-duplicates**: un grupo que cruza train/benchmark saca a sus miembros de train («cruce de
   partición»); nunca al revés, ni con `--conservar-duplicados`. Dentro de una partición, los miembros
   de una cadena `supersedes_case` (el `corrected` y lo que corrige) se conservan siempre: el par
   fallo → corrección es dato de primera clase. Entre el resto del grupo se queda la versión más alta,
   salvo `--conservar-duplicados`.
5. **Dos pasadas, en streaming**: la primera lee cada Gold, calcula sus hashes y sus shingles, y no
   guarda el caso; con eso decide grupos, partición y `export_id`. La segunda relee cada caso incluido,
   comprueba que su sha256 sigue siendo el de la primera y escribe su línea. Si un caso cambió entre
   ambas, se aborta **sin** `manifest.json` (export incompleto reconocible; nada se borra). Memoria:
   la del dedup, nunca los casos ni los bytes del export: 8 B por shingle muestreado + su frecuencia
   documental (4 B) + un tramo de conteo (≤ 2²¹ shingles, ~190 MiB) + el índice del *mid-prefix*;
   cota declarada con `--presupuesto 10⁷` y casi todo compartido (pares casi iguales): ≤ ~0,9 GiB.
   El recorrido del store aplica el tope por fichero también a `metadata.json`/`validation.json` de
   TODAS las versiones (una mayor se omite con aviso).
6. **Salida** en `<root>/exports/<export_id>/` (`export_id = AAAAMMDD-<12 hex>` del hash de los casos,
   sus sha256, sus motivos y los parámetros; nunca del reloj):
   - `train.jsonl` / `benchmark.jsonl`: una línea por caso con `messages` (turnos
     `system|user|assistant|tool` con `content`, `tool_calls` y `name`; sin `ts`) y procedencia `ref`,
     `case_id`, `version`, `family`, `variant`, `outcome` y `supersedes_case` si lo tiene. Ni métricas
     ni artefactos. Cada línea se redacta al escribirse (un secreto que llegara al disco sin redactar
     no sale). Misma entrada → mismos bytes.
   - `manifest.json`, **el último**: por caso `ref`, `sha256` (y el de cada fichero), `content_hash`,
     `particion` y `motivo` de exclusión (normalizado: rutas relativas, nunca el texto de un error del
     sistema); grupos de near-duplicates, `near_duplicates` (`jaccard`, `r`), avisos deterministas,
     parámetros, `directorio` (el nombre real, con `.N` si lo hay) y el hash de cada JSONL. Los avisos
     del recorrido del store (temporales, versiones enlazadas…) cambian con el reloj: salen por
     `stderr`, nunca en el manifiesto. Todo el manifiesto se redacta antes de hashearlo (un motivo
     puede citar claves de la trayectoria). **Sin `manifest.json`, el export está incompleto.**
7. **Nada destructivo**: bajo `exports/.lock` (un ensamblador a la vez; si otro lo tiene, espera
   `--espera-bloqueo` s —120— y después exit 3 sin escribir nada, diciendo cuánto tardó su propia
   pasada 1 como referencia),
   `exports/<export_id>/` se crea con `mkdir` y cada fichero con `O_EXCL`, comprobado al crearlo y al
   cerrarlo. Si ya existe idéntico (hash en streaming), exit 0 «ya existe» sin escribir; si existe
   distinto o incompleto, se usa `<export_id>.2`, `.3`… Un fallo a mitad deja el export sin manifiesto
   y lo dice; nunca se borra nada (lo único que se retira es el temporal propio del manifiesto, que se
   comprueba antes de escribirle nada; el aviso solo nombra lo que sigue existiendo).
   `exports/` enlazado → exit 1. Límite declarado: un tercero con escritura en `exports/` puede hacer
   que aparezca un fichero NUEVO del ensamblador fuera; se detecta y se nombra; nunca se sobrescribe
   ni se borra nada.
8. `--dry-run` imprime el manifiesto sin escribir. Exit 0 ok o ya existente · 1 rechazo (capacidad
   apagada, sin benchmark, store manipulado, caso cambiado entre pasadas) · 2 uso, E/S o sin
   `redact.py` · 3 otro ensamblador en curso.

El plugin **no** entrena, no sirve modelos y no corre el benchmark (CA-08): el proyecto usa los JSONL
con su herramienta.

**Marca del último ensamblado (T-10 fix2, diseño D-f4).** Tras un ensamblado REAL que acaba bien
(«escrito» o «ya existe») y aún con `exports/.lock`, el ensamblador escribe `exports/.ultimo.json` =
`{version, export_id, directorio, firma, gold, creado, parametros}` (≤ 4 KiB): `directorio` es el nombre
REAL del export, `.2`…`.99` incluido (M3); `firma` = `case-recorder.firma_gold` de la **entrada** del
ensamblado —los Gold humanos con su `content_hash`, saneado: un valor que no es un sha256 cuenta como
el centinela `"!"`, nunca la cadena (M5)—, con la lectura de `validation.json` que decidió el destino de
cada versión (la de `leer_caso`, o la del recorrido si `leer_caso` la omitió; `"!transitoria"` si la
omitió por una causa transitoria, M2/M4). Un Gold excluido (sin atar, duplicado, benchmark, aviso
permanente) sigue en la firma: describe la entrada, no el resultado. Los parámetros (`--benchmark`,
`--umbral`, `--ventana`, `--boilerplate`, `--presupuesto`, `--conservar-duplicados`) NO entran en ella
(M6): la marca los guarda a título informativo. Se publica desde un `.tmp-*` propio (`O_EXCL`, `fsync`)
con `_reemplazar` del recorder, y el temporal se retira siempre; una marca existente que no es de la
pieza (enlace, enlace duro, no regular, > 4 KiB, sin el esquema) **nunca se reemplaza** ni se sigue:
aviso y el export sigue siendo válido. `--dry-run` no la escribe. Una marca que no se pudo escribir tras
un export válido: exit 0 con aviso; el siguiente ensamblado («ya existe») la reescribe. Con
ensambladores a la vez, la última marca puede describir una instantánea más vieja: el resultado es
`desactualizado` (cierto) y reensamblar lo limpia, nunca un `al_dia` falso (M13). Límite declarado (el
G3 del recorder): entre la comprobación de la marca vigente y el reemplazo, un tercero con escritura en
`exports/` puede sustituirla; el reemplazo solo cambia ese nombre.

**Frescura del dataset (`estado_dataset(store, resumen, hasta)`, T-10; D-f4).** Solo lectura, sin red y
sin leer ningún `manifest.json`: responde a «¿reensamblar ahora cambiaría la entrada del último
ensamblado?», comparando la `firma` del resumen del recorder (`resumen_store`, el MISMO recorrido y el
MISMO tope `TOPE_JSON_CASO` que la pasada 1: las omisiones permanentes —incompletas, grandes, enlaces—
son las mismas en los dos lados, M1) con la de la marca. Un export cuenta si es un directorio real de
`exports/` con un `manifest.json` regular; lo demás, en tres (#156): **en curso** (sin `manifest.json`
y modificado hace menos de la gracia, o el más reciente si otro ensamblador tiene `exports/.lock`),
**incompleto** (más viejo) y **otros** (un fichero suelto, un enlace); los nombres con `.` (la marca,
el bloqueo, temporales) no cuentan. Estados: `sin_gold`; `sin_export` (hay Gold y ningún export);
`no_verificable` (sin marca —«reensambla para registrar el último ensamblado»—, marca ajena o inválida
—«retira `exports/.ultimo.json` a mano (solo ese nombre)»—, su export ya no está completo, o `exports/`
es un enlace o no se puede listar); `al_dia` (misma firma: el mismo train/benchmark **con los parámetros
del último ensamblado**, que el texto muestra); `desactualizado` (otra firma; el motivo, por recuento:
«N Gold vigentes frente a M» o «mismo número de Gold, contenido distinto»); `parcial` («no verificado»:
el recuento se cortó o hubo un aviso transitorio —salvo que los Gold ya contados superen los de la
marca: entonces `desactualizado`, M10—). `estado_dataset` tiene un margen propio (`MARGEN_ESTADO_S` =
0,3 s tras el plazo del recuento, dentro de los 5 s del bloque) y la lectura de la marca respeta el
plazo aunque esté bloqueada (#170). La firma no ve cambios en los ficheros INMUTABLES de una versión
(el export los excluye como «sin atar»): su remedio es `case-recorder.py index check` o volver a
aprobarla.

**Umbral y `--estado` (#176).** El recuento de `/doctor` (2 s) llega a ~2 000 versiones en caliente y a
~300 en frío (medido en Windows); por encima, la frescura sale «no verificado (PARCIAL)» y se verifica
con `dataset-assembler.py --estado [--json]`: solo lectura, sin tope ni `exports/.lock`, recuento
completo y el MISMO texto que `/doctor` (~1 ms por versión en caliente, ~7 ms en frío); exit 0 `al_dia`
o `sin_gold` · 1 `desactualizado` o `sin_export` · 2 `no_verificable`, `parcial` o una config que no
lo permite. Los topes son comprobaciones ENTRE llamadas al sistema: valen para
**sistemas de ficheros locales**; una sola llamada que se bloquea (SMB colgado, un placeholder de
OneDrive sin descargar) no la acota nada (M12).

## Proponer un caso Gold al Curator (`scripts/propose-from-case.py`, CA-05)

```text
python3 scripts/propose-from-case.py <case_id> <versión> --category <KEY> [--title <texto>]
        [--tag clave:valor ...] [--config <training.json>] [--project-root <dir>]
```

- Solo con la capacidad activa (`enabled: true`) y `bridge_to_curator: true` en `training.json` (si
  no, exit 1) y solo desde un caso **Gold** leído del disco igual que en el ensamblador, atado a su
  contenido (`content_hash`; si no casa, exit 1; sin él, aviso).
- Escribe UN candidato nuevo en `docs/knowledge/candidates/pending/caso-<case_id>-v<NNN>-<10 hex>.md`
  (el sufijo, del hash de la referencia exacta: dos casos que solo difieren en acentos o mayúsculas
  no comparten nombre) con el frontmatter que pide `curator-gate.py`: `category` (de
  `.claude/knowledge-services/taxonomy.json` o de la plantilla por defecto), `evidencia:
  validated_case`, `fuentes`, `source_cases` y `tags` `clave:valor`; sin `estado`. El cuerpo: petición
  y nota del revisor en una línea cada una, **redactadas al escribir** (el candidato se versiona en
  Git), nunca la trayectoria; un `--tag` que parezca un secreto se rechaza.
- **Nunca aprueba**: no escribe en `approved/` ni pone `estado: aprobado`; decide `knowledge-curator`
  con `curator-gate.py`. Nunca sobrescribe (`O_EXCL`) ni re-propone un nombre que ya esté en
  `pending/`, `needs_changes/`, `rejected/` o `approved/`; un `pending/` enlazado → exit 1, y si se
  sustituye por un enlace durante la creación, el aviso nombra dónde quedó el candidato (nada se borra).
- Anti-leakage: el puente va en una sola dirección; nada de `docs/knowledge/` alimenta el case store
  ni el dataset. Exit 0 creado · 1 rechazo · 2 uso, taxonomía ilegible, sin `knowledge-schema.py` o sin
  `redact.py`.
