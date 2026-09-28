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
  Jaccard son exactos SOBRE la muestra. La salida declara `jaccard: exacto|muestreado` y `r`. Límite:
  con `r < 1` un caso pequeño puede quedarse sin muestras (aviso; solo se agrupa con un duplicado exacto).
- **Escala**: duplicados exactos colapsados antes (huella del conjunto completo); índice PPJoin solo
  del *mid-prefix*, sondeo con el prefijo, filtro posicional y de longitud (exacto: ningún par con
  Jaccard ≥ umbral se pierde). Peor caso declarado: O(m²) solo dentro de un grupo de m near-duplicates;
  texto común por debajo de la plantilla → 0 escaneos del índice. 10⁴ casos sintéticos: cifras en la
  Evidencia de T-07 del ledger. Grupos = componentes conexas, deterministas.
- A mano: `python3 scripts/dedup.py <docs.jsonl> [--umbral] [--ventana] [--boilerplate] [--presupuesto] [--json]`
  (una línea `{"id", "family", "text"}` por caso; exit 0 · 2 uso o JSONL ilegible).

## Ensamblar (`scripts/dataset-assembler.py`, CA-03/CA-06/CA-11/CA-12)

```text
python3 scripts/dataset-assembler.py --benchmark <family>[,<family>…] [--umbral 0.8] [--ventana 3]
        [--boilerplate 0.5] [--presupuesto 10000000] [--conservar-duplicados] [--fecha AAAAMMDD]
        [--dry-run] [--config <training.json>] [--project-root <dir>]
```

1. **Solo Gold**: `validation.status == "approved"` **y** `approved_by_human` exactamente `true`, leídos
   de `validation.json` EN DISCO por descriptor (nunca del índice, que es una caché). Cada versión Gold
   se lee entera (sus ocho ficheros, sin seguir enlaces, con `vNNN` y `final/` comprobados antes y
   después, como mucho 16 MiB por fichero) y tiene que pasar el esquema; lo incompleto, en curso,
   enlazado, demasiado grande o incoherente se omite con motivo.
2. **Gold atado al contenido**: `set-status approved` guarda `content_hash`; si ya no casa con los
   ficheros, el caso se excluye («Gold sin atar al contenido aprobado»). Sin `content_hash` (Gold
   anterior, o `record --approved-by-human`): se exporta con aviso «sin hash de aprobación».
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
   la muestra del dedup, nunca los casos ni los bytes del export.
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
     `stderr`, nunca en el manifiesto. **Sin `manifest.json`, el export está incompleto.**
7. **Nada destructivo**: bajo `exports/.lock` (un ensamblador a la vez; ocupado → exit 3),
   `exports/<export_id>/` se crea con `mkdir` y cada fichero con `O_EXCL`, comprobado al crearlo y al
   cerrarlo. Si ya existe idéntico (hash en streaming), exit 0 «ya existe» sin escribir; si existe
   distinto o incompleto, se usa `<export_id>.2`, `.3`… Un fallo a mitad deja el export sin manifiesto
   y lo dice; nunca se borra nada (lo único que se retira es el temporal propio del manifiesto).
   `exports/` enlazado → exit 1. Límite declarado: un tercero con escritura en `exports/` puede hacer
   que aparezca un fichero NUEVO del ensamblador fuera; se detecta y se nombra; nunca se sobrescribe
   ni se borra nada.
8. `--dry-run` imprime el manifiesto sin escribir. Exit 0 ok o ya existente · 1 rechazo (capacidad
   apagada, sin benchmark, store manipulado, caso cambiado entre pasadas) · 2 uso, E/S o sin
   `redact.py` · 3 otro ensamblador en curso.

El plugin **no** entrena, no sirve modelos y no corre el benchmark (CA-08): el proyecto usa los JSONL
con su herramienta.

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
