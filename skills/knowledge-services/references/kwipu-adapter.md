# Adaptador Kwipu (`backends/markdown_export.py`, `type: "markdown-export"`)

Detalle de las derivaciones y algoritmos del único adaptador real de esta iniciativa (T-08).
Léelo al tocar `markdown_export.py` o al depurar un desfase entre `approved/` y Kwipu.

## Frontmatter exportado (CA-17)

Cada Markdown en `export_dir` lleva:

```
---
knowledge_id: mr.pattern.fast-curve-derailment
project: mr
scope: project
category: PATTERN
source: agent
confidence: medium
version: 1
hash: <sha256 hex>
---

<cuerpo de la entrada>
```

Derivaciones (ningún campo se inventa, CA-17):

- **`knowledge_id`** = `entry["id"]` tal cual — el Curator ya lo escribe con `id_prefix.` delante
  (`agents/knowledge-curator.md`), así que no hace falta recalcularlo.
- **`project`** = primer segmento de `knowledge_id` antes del primer `.` (el `id_prefix` del
  proyecto). Es el único identificador de proyecto disponible sin ampliar el contrato de adaptador
  (que solo recibe `entries`/`ops` + `cfg`, nunca la taxonomía completa ni `root`).
- **`scope`** = constante `"project"`. Esta iniciativa exporta conocimiento de UN proyecto;
  `"global"` (conocimiento compartido entre proyectos vía `projects.yaml` del stack) queda fuera de
  alcance hasta que exista una necesidad real de compartir entre proyectos.
- **`source`** = constante `"agent"`. Todo lo que llega a `approved/` pasó por
  `knowledge-curator`; hoy no hay una vía que distinga en el frontmatter de la entrada una
  aprobación "confirmada por humano" de una automática por evidencia.
- **`confidence`** = de `evidencia` (el nivel del candidato) vía la escalera POR DEFECTO del
  plugin:

  | `evidencia` | `confidence` |
  |---|---|
  | `observation`, `single_case` | `low` |
  | `validated_case`, `multiple_validated_cases` | `medium` |
  | `human_confirmed_rule` | `high` |
  | (cualquier otro valor — proyecto con `evidence_levels` propio) | `medium` (fallback documentado, no un extremo inventado) |

- **`hash`** = sha256 de `f"{knowledge_id}\n{version}\n{category}\n{cuerpo}"` — NO de los bytes
  finales del fichero (que ya incluyen este mismo hash en su frontmatter; hacerlo así evitaría la
  circularidad calculando sobre el fichero completo, así que se calcula sobre el contenido
  semántico). Estable entre corridas con la misma entrada.

## `manifest.json`

```json
{
  "version": 1,
  "entries": {
    "mr.pattern.fast-curve-derailment": {
      "ruta_relativa": "mr.pattern.fast-curve-derailment.md",
      "hash": "…",
      "version": 1,
      "category": "PATTERN"
    }
  }
}
```

Nombre de fichero: `<knowledge_id>.md`, plano bajo `export_dir` — `knowledge_id` ya cumple
`[A-Za-z0-9._-]+` (lo exige el Curator), así que es un nombre de fichero seguro sin sluggear.

## `plan`/`apply`: idempotencia y revocación

`plan(entries, cfg)` lee el `manifest.json` actual y compara sus claves contra
`{e["id"] for e in entries}`:

- Toda entrada en `entries` genera un op `upsert` (whether or not changed — escribir el mismo
  contenido es idempotente, no hace falta comparar hashes antes de decidir el op).
- Toda clave del manifest que YA NO esté en `entries` (salió de `approved/`, o dejó de enrutar a
  Kwipu) genera un op `revoke`.

`apply(ops, cfg)` escribe cada Markdown de forma atómica (tmp + `os.replace`), borra los ficheros
de los `revoke`, y reescribe `manifest.json` entero AL FINAL — un fallo a mitad de una corrida dejaría
ficheros ya escritos pero el manifest sin actualizar; la siguiente corrida reconcilia desde el
estado real de `entries` (nunca hace falta una recuperación manual).

`rebuild(entries, cfg)` es literalmente `apply(plan(entries, cfg), cfg)` — reconstruir la
proyección entera es un caso particular de sincronizar, no un camino de código aparte.

## `health`: mapeo del fixture real a `off · sano · degradado · error`

`GET <config.health.url>` (timeout `config.health.timeout_ms`), sobre un cuerpo JSON con la forma
real del bridge de Kwipu:

```json
{"status": "ok", "property_graph": {"status": "ok", ...}, "ollama": {"status": "ok", ...}}
```

| Condición | `estado` |
|---|---|
| Sin `health.url` configurada | `off` |
| Conexión rechazada / timeout / error de red | `off` |
| Respuesta no es JSON válido, o no es un objeto | `error` |
| `status == "ok"` y `property_graph.status`/`ollama.status` en `(None, "ok")` | `sano` |
| `status` en `("ok", "degraded", None)` sin cumplir lo anterior | `degradado` |
| Cualquier otro `status` | `error` |

Nunca lanza: cualquier excepción de red/parseo se captura y degrada al `estado` correspondiente.

## `verify`: desfase contra `GET /graph/snapshot`

`verify(cfg)` deriva la URL del snapshot quitando el sufijo "/health" de `config.health.url` y
añadiendo `/graph/snapshot`. Compara el `ruta_relativa` (basename) de cada entrada del
`manifest.json` local contra los nodos `type == "chunk"` del snapshot (los únicos que llevan
`file_name`; los nodos `type == "entity"` no identifican un fichero exportado).

Una entrada publicada cuyo nombre de fichero NO aparece entre los `file_name` de los nodos `chunk`
es un desfase: Kwipu aún no la indexó (o el `build_view` no se ha vuelto a correr). Cada desfase
lleva:

```json
{"knowledge_id": "mr.pattern.x", "motivo": "`mr.pattern.x.md` publicado pero no aparece en `/graph/snapshot`",
 "remedio": "reindexar: `build_view` + reiniciar `kwipu`, `kwipu-bridge`, `kwipu-mcp`"}
```

`verify` **nunca ejecuta** el remedio (CA-16): solo lo nombra. Sin red, o con el snapshot
inalcanzable, `verify` devuelve `ok: false` con un único desfase explicando el motivo de la
conexión — nunca lanza una excepción sin capturar.

## Validar contra el bridge real (fuera de los tests, opt-in del operador)

Con Kwipu corriendo en `http://127.0.0.1:8765` y un `taxonomy.json` con `backends.kwipu.enabled: true`:

```bash
python skills/knowledge-services/scripts/knowledge-sync.py --backend kwipu --root <proyecto> --check
python skills/knowledge-services/scripts/knowledge-sync.py --backend kwipu --root <proyecto> --dry-run
python skills/knowledge-services/scripts/knowledge-sync.py --backend kwipu --root <proyecto>
python skills/knowledge-services/scripts/knowledge-sync.py --backend kwipu --root <proyecto> --check
```

El último `--check` debería reportar `verify: ok` una vez Kwipu haya corrido su `build_view` sobre
`export_dir` — si sigue en desfase, el mensaje ya nombra el remedio exacto.
