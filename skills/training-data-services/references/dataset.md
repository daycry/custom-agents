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

**Frescura del dataset para `/doctor` (`estado_dataset(store, gold, hasta, parcial)`, T-10).** Solo
lectura: un export cuenta si es un directorio real de `exports/` (sin seguir enlaces) con un
`manifest.json` regular. Lo demás se separa en tres (T-10 fix1, #156): **en curso** (directorio sin
`manifest.json` modificado hace menos de la gracia, o el más reciente si otro ensamblador tiene
`exports/.lock` tomado: se sondea sin crearlo y se suelta al instante), **incompleto** (sin
`manifest.json` y más viejo) y **otros** (un fichero suelto, un enlace). Estados: `sin_gold`,
`sin_export` (hay Gold y ningún export), `desactualizado` / `al_dia` **por contenido** (#154): los Gold
vigentes que da `resumen_store` (`case_id@version` + `content_hash`) frente a los `casos` del
`manifest.json` del último export —un Gold nuevo, uno cuyo contenido aprobado cambió o uno que dejó de
serlo lo desactualizan; re-aprobar, un `touch` o reensamblar el mismo día («ya existe») no—; con el
recuento PARCIAL solo se comprueba lo recorrido. `parcial` («no verificado»): el recorrido de
`exports/` va dentro del MISMO plazo de `/doctor` (#152) y se agotó; `no_verificable`: `exports/` es
un enlace o el manifiesto no se puede leer (tope de 16 MiB por fichero).

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
