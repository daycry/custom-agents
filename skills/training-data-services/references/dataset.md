# Dataset Gold, near-duplicates y puente al Curator (training-data-services)

> Lee esto solo al llegar a los pasos 6-7 de `SKILL.md` (ensamblar el dataset, proponer un caso Gold
> a `knowledge-curator`). Los contratos ejecutables viven en los docstrings de `scripts/dedup.py`,
> `scripts/dataset-assembler.py` y `scripts/propose-from-case.py`.

## Near-duplicates (`scripts/dedup.py`, CA-10)

Sin embeddings, sin modelo y sin red: shingles de palabras + Jaccard, la técnica de duplicados de
`code-health` (la función `shingles` es una copia declarada en `agent-kits/shared/copias.json`; las
skills son standalone y no se importan entre sí).

- **Texto comparado**: el contenido VARIABLE del caso — petición + contexto + trayectoria (rol,
  contenido, herramienta y argumentos). Ni restricciones, ni métricas, ni marcas de tiempo.
- **Boilerplate**: un shingle presente en más de `--boilerplate` (0.5) de los casos **y** en al menos 3
  familias se ignora (prompt de sistema, plantillas). Con menos de 3 familias no se filtra nada
  (conservador: más grupos, nunca menos). `--boilerplate 1.0` apaga el filtro.
- **Umbral**: Jaccard ≥ `--umbral` (0.8), comparado con enteros; ventana de `--ventana` (3) palabras.
- **Escala**: índice invertido + filtro de prefijo exacto (no compara todos los pares). 10⁴ casos
  sintéticos: ~5 s y ~225 MiB. Grupos = componentes conexas, deterministas.
- A mano: `python3 scripts/dedup.py <docs.jsonl> [--umbral] [--ventana] [--boilerplate] [--json]`
  (una línea `{"id", "family", "text"}` por caso; exit 0 · 2 uso o JSONL ilegible).

## Ensamblar (`scripts/dataset-assembler.py`, CA-03/CA-06/CA-11/CA-12)

```text
python3 scripts/dataset-assembler.py --benchmark <family>[,<family>…] [--umbral 0.8] [--ventana 3]
        [--boilerplate 0.5] [--conservar-duplicados] [--fecha AAAAMMDD] [--dry-run]
        [--config <training.json>] [--project-root <dir>]
```

1. **Solo Gold**: `validation.status == "approved"` **y** `approved_by_human` exactamente `true`, leídos
   de `validation.json` EN DISCO por descriptor (nunca del índice, que es una caché). Cada versión Gold
   se lee entera (sus ocho ficheros, sin seguir enlaces, con `vNNN` y `final/` comprobados antes y
   después) y tiene que pasar el esquema; lo incompleto, en curso, enlazado o incoherente se omite
   con aviso.
2. **Benchmark declarado**: las familias de `--benchmark` van ENTERAS a benchmark; el resto, enteras a
   train. Sin `--benchmark`, o con una familia declarada sin casos Gold, **exit 1 y no se escribe nada**.
3. **Near-duplicates**: un grupo que cruza train/benchmark saca a sus miembros de train («cruce de
   partición»); nunca al revés, ni con `--conservar-duplicados`. Dentro de una partición se queda la
   versión más alta del grupo (en un par fallo → corrección, la corrección) salvo
   `--conservar-duplicados`.
4. **Salida** en `<root>/exports/<export_id>/` (`export_id = AAAAMMDD-<12 hex del contenido>`):
   - `train.jsonl` / `benchmark.jsonl`: una línea por caso con `messages` (turnos
     `system|user|assistant|tool` con `content`, `tool_calls` y `name`; sin `ts`) y procedencia `ref`,
     `case_id`, `version`, `family`, `variant`, `outcome` y `supersedes_case` si lo tiene. Ni métricas
     ni artefactos. Misma entrada → mismos bytes.
   - `manifest.json`, **el último**: por caso `ref`, `sha256` (y el de cada fichero), `particion` y
     `motivo` de exclusión (no Gold, omitida, duplicado, cruce); grupos de near-duplicates, avisos del
     store, parámetros y el hash de cada JSONL. **Sin `manifest.json`, el export está incompleto.**
5. **Nada destructivo**: `exports/<export_id>/` se crea con `mkdir` y cada fichero con `O_EXCL`. Si ya
   existe idéntico, exit 0 «ya existe» sin escribir; si existe distinto o incompleto, se usa
   `<export_id>.2`, `.3`… Un fallo a mitad deja el export sin manifiesto y lo dice; nunca se borra
   nada (lo único que se retira es el temporal propio del manifiesto). `exports/` enlazado → exit 1.
6. `--dry-run` imprime el manifiesto sin escribir. Exit 0 ok o ya existente · 1 rechazo (capacidad
   apagada, sin benchmark, store manipulado) · 2 uso o E/S.

El plugin **no** entrena, no sirve modelos y no corre el benchmark (CA-08): el proyecto usa los JSONL
con su herramienta.

## Proponer un caso Gold al Curator (`scripts/propose-from-case.py`, CA-05)

```text
python3 scripts/propose-from-case.py <case_id> <versión> --category <KEY> [--title <texto>]
        [--tag clave:valor ...] [--config <training.json>] [--project-root <dir>]
```

- Solo con `bridge_to_curator: true` en `training.json` (si no, exit 1) y solo desde un caso **Gold**
  leído del disco igual que en el ensamblador.
- Escribe UN candidato nuevo en `docs/knowledge/candidates/pending/caso-<case_id>-v<NNN>.md` con el
  frontmatter que pide `curator-gate.py`: `category` (de `.claude/knowledge-services/taxonomy.json` o de
  la plantilla por defecto), `evidencia: validated_case`, `fuentes`, `source_cases` y `tags`
  `clave:valor`; sin `estado`. El cuerpo: petición y nota del revisor en una línea cada una, nunca la
  trayectoria.
- **Nunca aprueba**: no escribe en `approved/` ni pone `estado: aprobado`; decide `knowledge-curator`
  con `curator-gate.py`. Nunca sobrescribe (`O_EXCL`) ni re-propone un nombre que ya esté en
  `pending/`, `needs_changes/`, `rejected/` o `approved/`; un `pending/` enlazado → exit 1.
- Anti-leakage: el puente va en una sola dirección; nada de `docs/knowledge/` alimenta el case store
  ni el dataset. Exit 0 creado · 1 rechazo · 2 uso, taxonomía ilegible o sin `knowledge-schema.py`.
