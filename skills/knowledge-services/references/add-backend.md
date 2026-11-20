# Cómo añadir un backend a `knowledge-services`

El plugin trae el **marco** y ningún adaptador: cargador por `type`, contrato de seis funciones,
`routing` cerrado, `knowledge-sync.py` y la outbox de recuperación. Un proyecto que quiera publicar
`docs/knowledge/approved/` a un servicio de memoria propio (un servidor MCP, una API, una carpeta
sincronizada) escribe un adaptador y lo declara. Esta guía es el camino completo. Lee
[`backends/README.md`](../backends/README.md) para el contrato exacto de cada función.

Instalar el plugin o declarar un backend no conecta nada por sí solo: el backend nace
`enabled: false` y solo publica lo que `routing` autoriza y tú ejecutas.

## 1. El adaptador: un fichero con seis funciones

Nombre: el `type` con `-` por `_` → `<type>.py` (p. ej. `type: "mi-servicio"` → `mi_servicio.py`); también vale
`backend_<type>.py`. Funciones obligatorias (`FUNCIONES_OBLIGATORIAS` de `backends/__init__.py`):

| Función | Qué hace | Nunca |
|---|---|---|
| `health(cfg)` | `{"estado": "off"\|"sano"\|"degradado"\|"error", "detalle": str}` sin publicar | lanzar |
| `plan(entries, cfg)` | `ops` idempotentes desde las entradas ya enrutadas | tocar red o disco |
| `apply(ops, cfg)` | ejecuta `ops` con un diario que permita retomar | borrar lo que no controla |
| `verify(cfg)` | `{"ok", "estado", "desfase"}`; nombra el remedio sin ejecutarlo | escribir |
| `rebuild(entries, cfg)` | reconstruye la proyección entera | decidir qué entra |
| `revoke(knowledge_id, cfg)` | invalida una entrada que salió de `approved/` (puede ser un no-op declarado) | |

`cfg` es el `config` del backend en `taxonomy.json` más `_root` (la raíz absoluta del proyecto: resuelve ahí las
rutas relativas, nunca contra el cwd). Un esqueleto mínimo, sin dependencias:

```python
def health(cfg):
    return {"estado": "sano", "detalle": "sin comprobar red"}

def plan(entries, cfg):
    return [{"accion": "upsert", "id": e["id"], "cuerpo": e.get("cuerpo", "")} for e in entries]

def apply(ops, cfg):
    return {"aplicados": len(ops)}      # publica de verdad, fichero a fichero o llamada a llamada

def verify(cfg):
    return {"ok": True, "estado": "ok", "desfase": []}

def rebuild(entries, cfg):
    return apply(plan(entries, cfg), cfg)

def revoke(knowledge_id, cfg):
    return {"revocado": False}
```

Un ejemplo completo y probado, que publica en una carpeta con un diario de recuperación y **contiene sus rutas**
(`dir` dentro de `_root`; toda ruta de su manifiesto, dentro de `dir`), es
[`scripts/fixtures/adaptador_prueba.py`](../scripts/fixtures/adaptador_prueba.py); léelo antes de escribir el tuyo.

Si el servicio es un servidor MCP, el adaptador es su cliente: el plugin **no incluye un adaptador MCP genérico**.
Reglas que no se negocian:

- **Red acotada, como la constitución** (`docs/CONSTITUTION.md`): toda capacidad con red es opt-in y, por defecto,
  queda acotada a hosts locales o privados. El plugin ya no trae helper de localidad: el adaptador valida el host de
  su endpoint y rechaza el que no sea local o privado salvo opt-in explícito del proyecto en su propia config.
- **Rutas contenidas** (CWE-22/73): ninguna lectura, escritura ni borrado fuera de la carpeta que el backend declara.
  Resuelve `dir` contra `_root` y exige que quede dentro (`realpath` + `commonpath`); toda ruta que leas de un
  manifiesto o de un `id` es un dato no confiable: si sale de esa carpeta, ignórala con aviso, nunca la sigas.
- **Sin credenciales en `taxonomy.json`** (guarda el *nombre* de la variable de entorno, no el valor).
- **Sanea** lo que devuelva el servidor antes de escribirlo en un `detalle`, y trata una respuesta de «encolado» como
  no confirmada.

Las funciones OPCIONALES `puede_leer`, `consultar`, `proponer_config` y `estado_grupo` están en el README del contrato.

**Lectura (`consultar`, solo si implementas `puede_leer`).** El núcleo ya **no** acota la consulta al proyecto ni
deriva un `group_id`: te entrega la `config` declarada tal cual (más `_root`). Acotar al proyecto lo que sirve la
consulta es **responsabilidad del adaptador** (filtra por el prefijo de ID o la carpeta de tu backend); lo que
devuelves pasa después por el filtro de aciertos del router y se degrada a lo local si falla.

**Claves que `/doctor` añade a `cfg`.** `_root`, `health.timeout_ms` y `timeout_ms` recortados a unos segundos y
`max_episodes` (≤ 200): la ventana de lectura de `verify()` en un diagnóstico rápido. Un adaptador que lea muchas
entradas la respeta; si no la usa, la ignora.

## 2. Dónde vive y cómo se carga

- **Carpeta propia del proyecto** (recomendado): déjalo, por ejemplo, en `.claude/knowledge-services/adapters/` y pasa
  `--backends-dir <carpeta>` a `knowledge-sync.py` (y a `knowledge-find.py --intent`). Sobrevive a las
  actualizaciones del plugin porque no está dentro de su caché.
- **`backends/<type>.py` del plugin**: solo si trabajas en un clon o un fork del plugin; en una instalación normal
  esa carpeta es la caché y se sobrescribe al actualizar.

Un `type` sin adaptador sale con exit 2 y «adaptador no disponible … ver add-backend.md», sin traceback.
Los `type` que el plugin incluyó hasta 3.x (retirados en 4.0.0) dicen además «retirado».

## 3. Declararlo en `taxonomy.json`

Siempre apagado al principio, y con `routing` explícito por categoría (una categoría sin `routing` no sale):

```json
{
  "categories": [
    {"key": "DECISION", "folder": "adr", "min_evidence": "human_confirmed_rule",
     "routing": {"mi-servicio": false}}
  ],
  "backends": {
    "mi-servicio": {"type": "mi-servicio", "enabled": false, "config": {"dir": "salida"}}
  }
}
```

Valida el fichero con `knowledge-schema.py <ruta>`: comprueba la forma genérica (`type`, `enabled` booleano, `config`
objeto, `routing` solo a ids declarados). La `config` propia del adaptador la valida el adaptador.

## 4. Probarlo y habilitarlo

1. `knowledge-sync.py --backend mi-servicio --root . --backends-dir <carpeta> --dry-run`: muestra el `plan` sin
   aplicar nada. Contrasta ID, versión y destino.
2. Pon `enabled: true` y `routing.<id>: true` solo en las categorías que decidas, y ejecuta sin `--dry-run`.
3. `--check`: `health()` + `verify()`; «incompleto» no es un verde. `--outbox-status` enseña la cola si algo falló.
4. `/doctor` pinta la fila en vivo del backend **si su adaptador está en `backends/`**; un adaptador de carpeta propia se
   comprueba con `--check --backends-dir`.
5. Escribe tus pruebas con el patrón de las suites del marco en el repositorio del plugin
   (`test_backend_verification` y `test_knowledge_sync_replay`): cargan el adaptador por `directorios` y recorren
   plan, apply, verify y un fallo a medias.

Retirar un backend: `enabled: false` y quitar sus claves de `routing`. Los datos ya publicados no se borran solos.
