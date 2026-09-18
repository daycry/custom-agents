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

`category` viene siempre de la entrada `approved/` de origen, donde es un campo **obligatorio**
del frontmatter (gap 113, migración documentada en `docs/knowledge/approved/README.md` para
proyectos con entradas anteriores a ese cambio) — el adaptador nunca la infiere ni la inventa.

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

Durante una publicación en curso convive un `manifest.pending.json` (mismo formato, el estado
FINAL previsto) junto al `manifest.json` ya publicado — ver diario de publicación más abajo. Su
presencia es la señal de "publicación incompleta", nunca un estado a interpretar por fuera del
adaptador.

## `plan`/`apply`: idempotencia y publicación por fichero con diario (fix3, intento 3, 2026-09-19)

`plan(entries, cfg)` lee el `manifest.json` actual y compara `hash`/existencia contra
`{e["id"] for e in entries}` (`force=True` en `--rebuild`, que fuerza `upsert` en todo):

- Toda entrada en `entries` cuyo `hash` calculado NO coincide con el del manifiesto (o que no
  existía) genera un op `upsert`.
- Toda entrada cuyo `hash` YA coincide genera un op `sin_cambios` — no lleva `cuerpo` (gap 125:
  es el campo más pesado del envelope de la outbox, y un fichero que no cambia no lo necesita).
- Toda clave del manifest que YA NO esté en `entries` (salió de `approved/`, o dejó de enrutar a
  Kwipu) genera un op `revoke`.

**Este diseño SUSTITUYE al intercambio de directorio completo** (`.prev` + swap atómico de
`export_dir`) que tenía la iniciativa hasta el intento 2: ese diseño, bajo revisión adversarial,
resultó tener dos Critical — pérdida de datos en el rollback y borrado de ficheros AJENOS a
`export_dir` (un `export_dir` compartido, o mal configurado, perdía contenido que no era suyo).
`apply(ops, cfg)` publica ahora así (gaps #126/#127/#129/#132/#134/#136/#137/#138):

1. Escribe SOLO los `upsert` en un staging HERMANO de `export_dir` (`<export_dir>.staging-<pid>`);
   los `sin_cambios` NUNCA se tocan (ni se mueven ni se reescriben — coste proporcional a los
   CAMBIOS, no al total: una pasada sin cambios ya no cuesta un rename por fichero, gap 118/136).
2. Antes de publicar nada, escribe `manifest.pending.json` en `export_dir` de forma atómica
   (tmp + `os.replace`) con el estado FINAL previsto (entries + hashes de la corrida completa).
3. Publica cada `upsert` con UN `os.replace` fichero-a-fichero desde el staging al destino —
   nunca un intercambio del árbol entero (gap 127: un `export_dir` ajeno con ficheros de otros
   proyectos, o `export_dir: "docs"`, ya no puede perder nada que no sea suyo) — y ejecuta los
   `revoke` (solo ficheros que estaban en el manifiesto PROPIO, `os.remove` best-effort; nunca
   borra un fichero que `apply()` no escribió él mismo).
4. Renombra `manifest.pending.json` -> `manifest.json` (atómico) y borra el staging.

**Caminos de fallo:**

- Fallo en (1)-(2): nada cambió en `export_dir` — el staging es hermano y se descarta, y
  `manifest.pending.json` se escribe con tmp+rename, así que un fallo a mitad de esa escritura
  tampoco deja nada a medias (gap 126: antes un `except BaseException` sin reponer perdía la
  publicación entera aunque fuera puramente `sin_cambios`).
- Fallo en (3) a mitad (p. ej. `PermissionError` porque el indexador tiene un `.md` abierto): los
  ficheros ya publicados quedan intactos, `manifest.pending.json` se conserva, y la SIGUIENTE
  corrida lo usa como manifiesto objetivo en `plan()`: los ficheros cuyo hash en disco ya coincide
  con el objetivo son `sin_cambios`, el resto vuelve a ser `upsert` — la publicación interrumpida
  se completa sola, sin recuperación manual ni reintento dentro de la misma corrida.
- `verify()` con `manifest.pending.json` presente devuelve `ok: False,
  razon: "publicacion_incompleta"` antes que cualquier otra comprobación.

`revoke()` público (para una entrada suelta que salió de `approved/`) usa el MISMO diario
(pending -> publica -> manifest.json), no un camino de código aparte. Ya no existe `.prev` ni el
intercambio de directorio: `_purgar_staging_huerfano` (antes `_reparar_publicacion`) solo limpia un
`.staging-<pid>` hermano de una corrida interrumpida, nunca reconstruye nada.

`rebuild(entries, cfg)` es literalmente `apply(plan(entries, cfg, force=True), cfg)` — reconstruir
la proyección entera es un caso particular de sincronizar (con `force=True` para que TODA entrada
sea `upsert`, no solo las que cambiaron), no un camino de código aparte.

**Contención bidireccional de `export_dir`** (`_export_dir_resuelto`, gap 127): usando
`os.path.realpath` + `os.path.normcase` (case-insensitive, resiste symlinks/junctions en
Windows), `export_dir` no puede ser el root del proyecto, un ANCESTRO del root, quedar DENTRO de
`docs/knowledge/`, ni CONTENER a `docs/knowledge/` — antes solo se comprobaba que no quedara dentro
de `docs/knowledge/approved/`, y `"docs"` o `".."` pasaban todas las validaciones.

**Caché DNS con TTL y sin acumulación de hilos** (`_dns_cache`, gaps #132/#138): cada resolución
(positiva, negativa, o "no resuelta a tiempo") expira a los `_DNS_CACHE_TTL_S` segundos — un fallo
transitorio ya no queda cacheado en negativo para siempre. El caso "colgado" (agota
`_DNS_TIMEOUT_S` sin resolver) se cachea con un TTL corto propio (`_DNS_CACHE_TTL_S_LENTO`). Un
registro `_dns_inflight` (protegido por `_dns_inflight_lock`) evita lanzar un hilo nuevo para el
mismo host mientras el anterior sigue vivo: llamadas concurrentes al mismo host lento se unen
(`join`) al hilo YA en marcha en vez de acumular uno por llamada — el hilo se arranca DENTRO de la
sección crítica del lock (si se arrancara fuera, dos llamadas concurrentes podrían intentar unirse
a un hilo que aún no ha hecho `start()`, `RuntimeError`).

**Presupuesto de tiempo de la cadena de redirecciones** (gap #137): acotada a
`_MAX_REDIRECCIONES` saltos, y el `timeout_ms` configurado se consume UNA VEZ para TODA la cadena
(no por salto) — cada hop resta del `timeout` restante del siguiente, así que una cadena de
redirecciones ya no puede multiplicar el tiempo total por el número de saltos. Cada hop revalida
el host contra el allowlist local/privado (CWE-918/601) antes de seguirlo.

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

## Modo `resumen` (gap 83, fix1 2026-09-18)

`knowledge-sync.py` decide QUÉ entradas van en `modo: "resumen"` (según `routing.<backend>:
"summary"` en `taxonomy.json`); este adaptador decide QUÉ ES un resumen — el núcleo nunca corta
texto. `_cuerpo_segun_modo()`:

1. Si la entrada trae un campo `resumen` (string no vacío) en su frontmatter, se publica tal cual.
2. Si no, se publica el PRIMER PÁRRAFO del cuerpo (hasta la primera línea en blanco).

`modo: "completo"` (default) publica el cuerpo íntegro, sin recortar.

## Validar contra el bridge real (fuera de los tests, opt-in del operador)

Con Kwipu corriendo en `http://127.0.0.1:8765` y un `taxonomy.json` con `backends.kwipu.enabled: true`
(localiza el script con el patrón de seis raíces, ver `SKILL.md` § Uso):

```bash
KSSKILL="$(find "$PWD/.claude" "$PWD/.codex" "$PWD/.opencode" "$HOME/.claude" "$HOME/.codex" "$HOME/.config/opencode" -type f -path '*skills/knowledge-services/scripts/knowledge-sync.py' 2>/dev/null | head -1)"
python3 "$KSSKILL" --backend kwipu --root <proyecto> --check
python3 "$KSSKILL" --backend kwipu --root <proyecto> --dry-run
python3 "$KSSKILL" --backend kwipu --root <proyecto>
python3 "$KSSKILL" --backend kwipu --root <proyecto> --check
```

El último `--check` debería reportar `verify: ok` una vez Kwipu haya corrido su `build_view` sobre
`export_dir` — si sigue en desfase, el mensaje ya nombra el remedio exacto. Un `verify` con
`razon: "nunca_sincronizado"` (manifest vacío/ausente) significa que todavía no se ha corrido ni
un `apply` real — no es un desfase, es que nunca se publicó nada.
