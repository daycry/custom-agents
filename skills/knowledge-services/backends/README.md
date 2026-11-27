# Contrato de adaptador (`backends/<type>.py`)

`knowledge-sync.py` (T-07) es el núcleo de publicación: carga un adaptador por `type` (declarado en
`.claude/knowledge-services/taxonomy.json` → `backends.<id>.type`) y le pasa SOLO las entradas de
`docs/knowledge/approved/` que ya pasaron el filtro de `routing` (fail-closed, CA-09/CA-11). El
núcleo **nunca** menciona un backend concreto; añadir uno nuevo es un fichero nuevo en este
directorio (o en cualquier carpeta que el llamador añada a `--backends-dir`, ver CA-12), sin
tocar `knowledge-sync.py` ni `backends/__init__.py`.

## El plugin no incluye adaptadores

Desde la versión 4.0.0 este directorio solo trae el cargador (`__init__.py`) y este contrato: ningún
adaptador concreto. Instalar el plugin no habilita ni configura ningún servicio externo. Un proyecto
que quiera publicar o consultar un servicio de memoria escribe su propio adaptador (guía:
[`references/add-backend.md`](../references/add-backend.md); ejemplo: el adaptador de prueba, abajo) y lo
declara en `taxonomy.json`. La publicación sigue limitada a las entradas
aprobadas que el `routing` del proyecto autoriza.

## Autoridad y recuperación local

El Markdown local es canónico. `knowledge-find.py` recupera ADR/GOT/LES legados y entradas
válidas de `approved/` con su ID completo, versión, estado, evidencia y ruta. Query y relaciones
JSON conservan `version` del conocimiento; `--show --json` conserva `version: 1` del envelope
y añade `knowledge_version`. Las relaciones aprobadas incluyen sus enlaces declarados.

La categoría determina el tipo de consulta, independientemente de la carpeta: DECISION →
`adr`, GOTCHA/PATTERN → `gotcha`, LESSON → `leccion`; una categoría propia usa su etiqueta
normalizada. `aprobado` comparte prioridad con `aceptada`, sin cambiar su estado almacenado.
La caché SQLite es reconstruible y conserva los mismos metadatos que el recorrido plano.

La lectura local usa reglas compartidas sin cargar adaptadores ni validar conexiones.
Una configuración de servicio inválida no elimina la memoria local; una taxonomía local o
corpus aprobado inválido excluye ese corpus con diagnóstico y conserva el legado válido.
Se rechazan IDs aprobados duplicados y rutas fuera de las carpetas declaradas. Una colisión
entre legado y aprobado hace fallar `--show`/`--related` en vez de elegir el primero.
`candidates/` no participa. Validar carpeta, forma y estado no acredita aprobación humana
o semántica; esta lectura no promueve entradas ni cambia la política del Curator.

El lector común conserva etiquetas de contenido derivado y UUID en JSON, con ID y ruta
exactos dentro de sus límites. La línea compacta antepone «derivado sin autoridad» para
que el recorte no elimine esa distinción en CLI o briefs. Contratos incompletos o
identidades inseguras se descartan; aprobado describe la fuente, no el texto derivado.

Los backends son proyecciones opcionales. Una lectura externa autorizada conserva versiones
válidas; errores o respuestas incompatibles degradan a la recuperación local con motivo. El
versionado del Markdown en Git depende de la política del proyecto consumidor. Una
`respuesta_generada` declara `verificacion: no_verificada`, `autoridad: ninguna` y
`citas_por_afirmacion: false`: sus `source_nodes` son fuentes recuperadas vinculadas, no acreditan
cada afirmación ni convierten el texto generado en conocimiento aprobado.

## Nombre de fichero

`type` → `<type con "-" por "_">.py` (p. ej. `"mi-backend"` → `mi_backend.py`). Los adaptadores
cargados desde un directorio extra pueden usar además `backend_<type>.py` (p. ej. `backend_test.py`
para `type: "test"`), para no chocar de nombre con un adaptador del mismo `type` corto.

## Las 6 funciones obligatorias

| Función | Firma | Qué hace | Efectos permitidos |
|---|---|---|---|
| `health` | `(cfg) -> {"estado": "off"\|"sano"\|"degradado"\|"error", "detalle": str}` | Salud/desfase de red **sin publicar nada**; nunca lanza — cualquier fallo de red/parseo degrada a un `estado` del enum, nunca a una excepción. | Solo lectura (red permitida) |
| `plan` | `(entries, cfg) -> ops` | Calcula las operaciones IDEMPOTENTES a partir de `entries` (YA filtradas por `routing`; el adaptador nunca decide enrutado). Repetir `plan` con las mismas `entries` produce el mismo `ops`. | Ninguno (puro) |
| `apply` | `(ops, cfg) -> result` | Ejecuta `ops`. Si falla a medias, pueden quedar archivos ya actualizados o revocados: el adaptador debe llevar un diario que permita completar el objetivo pendiente, sin rollback global, y nunca borrar nada que no controle. El `knowledge-sync.py` que lo invoca reencola con backoff (nunca dead-letter directo por un solo fallo) y drena la outbox propia ANTES de cada sync fresco. | Escritura (idempotente) |
| `verify` | `(cfg) -> {"ok": bool, "desfase": [...]}` | Compara lo publicado contra la fuente/destino real. Si hay desfase, **nombra el remedio** en `detalle`/`desfase` sin ejecutarlo (CA-16: el reindexado, si aplica, es responsabilidad del servicio externo). Los veredictos son `ok`, `incompleto`, `desfase` y `no_verificable`; solo `ok` sale con exit 0 en `--check`. | Solo lectura (red permitida) |
| `rebuild` | `(entries, cfg) -> result` | Reconstruye la proyección ENTERA desde `entries` (todas las ya enrutadas, no una lista parcial) — mismo resultado que borrar la publicación y repetir `plan`+`apply` desde cero. | Escritura completa |
| `revoke` | `(knowledge_id, cfg) -> result` | Invalida/tombstone una entrada que salió de `approved/`. Puede ser un no-op DECLARADO (una función que exista y no haga nada), pero tiene que existir. | Escritura puntual (o ninguno) |

Nota de diseño (T-07, desviación documentada de la tabla de `design.md`): `rebuild` recibe
`entries` como primer parámetro (no solo `cfg`) porque reconstruir exige saber QUÉ debería
existir; el enrutado sigue siendo responsabilidad exclusiva del núcleo — `rebuild` nunca decide
qué entra, solo cómo se materializa.

## Funciones OPCIONALES del contrato

Además de las 6 obligatorias, un adaptador puede exponer estas; el núcleo las pide con
`getattr(...)` y, si no están, sigue sin ellas (nunca son un requisito de carga).

La lectura se invoca mediante `consultar(cfg, consulta)`: `cfg` contiene la configuración del backend y
`consulta` describe la petición ya autorizada por el router. Esta función opcional devuelve resultados; no
publica ni aprueba conocimiento. La tabla siguiente define su forma y los controles del llamador.

| Función | Firma | Quién la usa | Qué significa que exista |
|---|---|---|---|
| `puede_leer` | `(cfg) -> {"puede": bool, "razon": str}` | el router de `knowledge-find.py --intent` | el backend decide si AUTORIZA una lectura ahora mismo (modo, salud, desfase). Sin `puede: true` exacto, el router no consulta |
| `consultar` | `(cfg, consulta) -> {"aciertos": [...], "descartados": int, "motivo": str}` | el router de `knowledge-find.py --intent` (T-07, CA-12) | **es lo que hace ENRUTABLE a un backend**: un adaptador sin `consultar` puede publicar pero nunca servir una consulta. `consulta` = `{"intent", "texto", "limit", "area", "tipo", "claves", "iniciativa"}`; devuelve `aciertos` (lista), `descartados` (int, lo que se descartó fail-closed) y `motivo` (str); cada acierto tiene que traer `id`, `estado`, `evidencia` y `ruta` canónica (el núcleo descarta, fail-closed, el que no las traiga) y `motivo` NO VACÍO con 0 aciertos significa «no pude servir» → el núcleo degrada a local con ese motivo a la vista (nunca lanza, igual que `health`) |
| `proponer_config` | `(taxonomy, cfg) -> dict` | `knowledge-sync.py --propose-config` | el adaptador sabe proponer su propia configuración a partir de la taxonomía del proyecto |
| `estado_grupo` | `(cfg, consultar_servidor=False) -> {"estado", "origen", "aviso"}` | `knowledge-sync.py --avisos-grupo [--consultar-servidor]` (`/setup`, CA-15) | avisa, ANTES de la primera sincronización, si el destino ya trae contenido de otro origen. Sin respuesta, `no_verificado`. Nunca bloquea (exit 0) |

`consultar` puede añadir el campo genérico opcional `respuesta_generada`. El router
valida su forma y los bindings; no añade autoridad ni un contrato de citas por afirmación.
Los adaptadores que implementan solo las seis funciones siguen siendo compatibles.

## Carga y validación

`backends/__init__.py::cargar_adaptador(tipo, directorios=None)` busca el fichero, lo carga con
`importlib.util` y comprueba que las 6 funciones existen y son invocables. Un adaptador que no
cumple el contrato completo (fichero ausente, no carga, o falta una función) levanta
`AdaptadorNoDisponible` con un mensaje que nombra exactamente qué falta — `knowledge-sync.py` lo
convierte en `exit 2`, nunca en un traceback. Un `type` sin adaptador recibe siempre el mismo aviso
de adaptador ausente, con la guía para añadir uno; el cargador no guarda ninguna lista de tipos aparte.

## Modo `resumen` (gap 83, fix1 2026-09-18)

Cada entrada que `knowledge-sync.py` pasa a `plan`/`rebuild` trae `modo: "completo"` o
`modo: "resumen"` (según `routing.<backend>` sea `true` o `"summary"` en `taxonomy.json`) — el
núcleo NUNCA decide qué es un resumen, solo marca la intención. Cada adaptador es responsable de
interpretarlo: un criterio razonable es «el campo `resumen` del frontmatter si existe, si no el primer
párrafo del cuerpo». Un adaptador puede definir otro criterio, pero tiene que documentarlo — nunca
ignorar `modo` y publicar siempre el cuerpo completo.

## Tope duro de `/doctor` (C-09a)

`health()` y `verify()` respetan cada uno su `timeout_ms`, pero se ejecutan uno tras otro.
`/doctor` corre la sonda en un hilo `daemon` y deja de esperar a `tope_ms` + `CAPACIDAD_MARGEN_MS`
(500 ms); si no termina, la fila es ⚠️ «no comprobado». Por eso ambas funciones deben ser de SOLO
LECTURA: el hilo abandonado sigue hasta que el proceso acaba y no debe dejar escrituras a medias.

## Recuperación local compartida

`knowledge-find.py` usa el snapshot acotado de `knowledge-view.py` para legado
y aprobado. Este valida textos ya leídos mediante `knowledge-local.index_snapshot`,
sin cargar adaptadores. La CLI ordinaria declara `corpus_read` y solo conserva
la caché cuando el corpus es completo; `--view` y la consulta explícita del
panel no usan caché. Un fallo o una identidad ambigua conserva su diagnóstico.
La lectura por `--intent` mantiene la autorización del router y el respaldo
local con su motivo; estos límites no activan consultas externas.

## Adaptadores de fixture (CA-12)

- `evals/fixtures/knowledge-services/backend_test.py` implementa el contrato completo de forma
  trivial (`type: "test"`) para que los tests de `knowledge-sync.py` demuestren que un backend nuevo
  no toca el núcleo: se carga pasando su carpeta en `--backends-dir`, fuera del árbol real del plugin.
- `scripts/fixtures/adaptador_prueba.py` (`type: "adaptador-prueba"`) publica de verdad en una
  carpeta (un `.md` por entrada y un `manifest.json` con diario) y sirve de adaptador de referencia
  para las suites del marco (`test_knowledge_sync_replay.py`, `test_backend_verification.py`). Vive en
  `scripts/fixtures/` y se carga por `directorios`/`--backends-dir`, nunca desde `backends/`.
