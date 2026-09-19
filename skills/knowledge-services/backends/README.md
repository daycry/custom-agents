# Contrato de adaptador (`backends/<type>.py`)

`knowledge-sync.py` (T-07) es el único núcleo: carga un adaptador por `type` (declarado en
`.claude/knowledge-services/taxonomy.json` → `backends.<id>.type`) y le pasa SOLO las entradas de
`docs/knowledge/approved/` que ya pasaron el filtro de `routing` (fail-closed, CA-09/CA-11). El
núcleo **nunca** menciona un backend concreto; añadir uno nuevo es un fichero nuevo en este
directorio (o en cualquier carpeta que el llamador añada a `--backends-dir`, ver CA-12), sin
tocar `knowledge-sync.py` ni `backends/__init__.py`.

## Nombre de fichero

`type` → `<type con "-" por "_">.py` (p. ej. `"markdown-export"` → `markdown_export.py`). Las
fixtures de test pueden usar además `backend_<type>.py` (p. ej. `backend_test.py` para
`type: "test"`), para no chocar de nombre con un futuro adaptador real del mismo `type` corto.

## Las 6 funciones obligatorias

| Función | Firma | Qué hace | Efectos permitidos |
|---|---|---|---|
| `health` | `(cfg) -> {"estado": "off"\|"sano"\|"degradado"\|"error", "detalle": str}` | Salud/desfase de red **sin publicar nada**; nunca lanza — cualquier fallo de red/parseo degrada a un `estado` del enum, nunca a una excepción. | Solo lectura (red permitida) |
| `plan` | `(entries, cfg) -> ops` | Calcula las operaciones IDEMPOTENTES a partir de `entries` (YA filtradas por `routing`; el adaptador nunca decide enrutado). Repetir `plan` con las mismas `entries` produce el mismo `ops`. | Ninguno (puro) |
| `apply` | `(ops, cfg) -> result` | Ejecuta `ops` publicando FICHERO A FICHERO desde un staging HERMANO al destino, con un diario (`manifest.pending.json` → publica → `manifest.json`) que hace segura la reanudación tras un fallo a mitad — nunca un intercambio del árbol entero (perdería ficheros ajenos al manifiesto propio). Si falla a medias, la publicación ANTERIOR debe seguir intacta y nunca se borra nada que `apply()` no controle; el `knowledge-sync.py` que lo invoca reencola con backoff (nunca dead-letter directo por un solo fallo) y drena la outbox propia ANTES de cada sync fresco — ver `references/kwipu-adapter.md` para el algoritmo de referencia. | Escritura atómica por fichero |
| `verify` | `(cfg) -> {"ok": bool, "desfase": [...]}` | Compara el manifiesto publicado contra la fuente/destino real. Si hay desfase, **nombra el remedio en `detalle`/`desfase` sin ejecutarlo** (CA-16: el reindexado, si aplica, es responsabilidad del stack externo). | Solo lectura (red permitida) |
| `rebuild` | `(entries, cfg) -> result` | Reconstruye la proyección ENTERA desde `entries` (todas las ya enrutadas, no una lista parcial) — mismo resultado que borrar la publicación y repetir `plan`+`apply` desde cero, pero sin pasar por el staging de `knowledge-sync.py` (el propio adaptador es responsable de que sea seguro). | Escritura completa |
| `revoke` | `(knowledge_id, cfg) -> result` | Invalida/tombstone una entrada que salió de `approved/`. Puede ser un no-op DECLARADO (una función que exista y no haga nada), pero tiene que existir. | Escritura puntual (o ninguno) |

Nota de diseño (T-07, desviación documentada de la tabla de `design.md`): `rebuild` recibe
`entries` como primer parámetro (no solo `cfg`) porque reconstruir exige saber QUÉ debería
existir; el enrutado sigue siendo responsabilidad exclusiva del núcleo — `rebuild` nunca decide
qué entra, solo cómo se materializa.

## Carga y validación

`backends/__init__.py::cargar_adaptador(tipo, directorios=None)` busca el fichero, lo carga con
`importlib.util` y comprueba que las 6 funciones existen y son invocables. Un adaptador que no
cumple el contrato completo (fichero ausente, no carga, o falta una función) levanta
`AdaptadorNoDisponible` con un mensaje que nombra exactamente qué falta — `knowledge-sync.py` lo
convierte en `exit 2`, nunca en un traceback.

## Modo `resumen` (gap 83, fix1 2026-09-18)

Cada entrada que `knowledge-sync.py` pasa a `plan`/`rebuild` trae `modo: "completo"` o
`modo: "resumen"` (según `routing.<backend>` sea `true` o `"summary"` en `taxonomy.json`) — el
núcleo NUNCA decide qué es un resumen, solo marca la intención. Cada adaptador es responsable de
interpretarlo: el criterio de referencia (`markdown_export.py`, ver `references/kwipu-adapter.md`)
es "el campo `resumen` del frontmatter si existe, si no el primer párrafo del cuerpo". Un
adaptador nuevo puede definir otro criterio, pero tiene que documentarlo — nunca ignorar `modo` y
publicar siempre el cuerpo completo.

## Adaptador de fixture (CA-12)

`evals/fixtures/knowledge-services/backend_test.py` implementa el contrato completo de forma
trivial (`type: "test"`) para que los tests de `knowledge-sync.py` demuestren que un backend nuevo
no toca el núcleo: se carga pasando su carpeta en `--backends-dir`, fuera del árbol real del
plugin.
