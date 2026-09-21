#!/usr/bin/env python3
"""
capabilities.py — registro de CAPACIDADES OPCIONALES del plugin (ADR-018 punto 7, CA-14,
`knowledge-services` T-13). Sin dependencias externas.

Cada capacidad opcional (kwipu hoy; graphiti, training-data-services despues) declara un dict
con el contrato:
  {id, config_path, enabled, health, doctor, setup_step}

`enabled`, `health` y `doctor` pueden ser un VALOR ESTATICO o un CALLABLE `f(root) -> valor`;
`enumerar()` los evalua sin que quien llama (`/doctor`, `/setup`) necesite saber cual es cual.
Una capacidad cuyo `enabled`/`health`/`doctor` lanza una excepcion degrada a
`{"estado": "error", "detalle": "..."}` SIN tumbar la evaluacion de las demas (fail soft, nunca
bloquea el ciclo — regla "Degradacion, no bloqueo" de CLAUDE.md).

Anadir una capacidad nueva es UNA llamada a `registrar()`; ni `/setup` ni `/doctor` necesitan
codigo especifico por capacidad (CA-14) — solo recorren `enumerar()`.

Uso:
  capabilities.py [--root <ruta>]   # lista las capacidades registradas y su estado; exit 0
"""
import argparse
import importlib.util
import os
import sys

# Consola no UTF-8 (Windows cp1252) o tuberías: reconfigurar ANTES de leer/imprimir (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

HERE = os.path.dirname(os.path.abspath(__file__))
TAXONOMY_CONFIG_PATH = os.path.join(".claude", "knowledge-services", "taxonomy.json")


def _cargar_knowledge_schema():
    """Carga knowledge-schema.py (T-01) desde el mismo directorio. Ver la misma nota de
    knowledge-index.py: ambos ficheros viajan siempre juntos en agent-kits/shared/."""
    ruta = os.path.join(HERE, "knowledge-schema.py")
    spec = importlib.util.spec_from_file_location("knowledge_schema", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _resolver(valor, root):
    """Evalua un campo del contrato: si es callable, lo invoca con `root` y captura cualquier
    excepcion como error; si no, lo devuelve tal cual."""
    if not callable(valor):
        return valor, None
    try:
        return valor(root), None
    except Exception as e:  # noqa: BLE001 — una capacidad rota no puede tumbar las demas
        return None, f"{type(e).__name__}: {e}"


def evaluar_capacidad(cap, root):
    """Evalua una capacidad registrada sobre `root`. Nunca lanza: cualquier fallo en
    enabled/health/doctor se refleja como `{"estado": "error", "detalle": ...}` en ese campo.

    Gap 32 (revision intento 2): esta es la API PUBLICA (documentada, usable fuera de
    `enumerar()`); antes solo `enumerar()` vaciaba `_CACHE_TAXONOMIA`, asi que dos llamadas
    DIRECTAS a `evaluar_capacidad()` entre las que se edita `taxonomy.json` servian la taxonomia
    obsoleta a la segunda. Se vacia la cache al entrar y al salir de esta funcion tambien (mismo
    ciclo de vida que `enumerar()`: nunca sobrevive mas alla de UNA evaluacion), conservando la
    memoizacion intra-llamada entre `enabled`/`health`/`doctor` de la MISMA capacidad."""
    _CACHE_TAXONOMIA.clear()
    try:
        return _evaluar_capacidad_sin_limpiar_cache(cap, root)
    finally:
        _CACHE_TAXONOMIA.clear()


def _evaluar_capacidad_sin_limpiar_cache(cap, root):
    """Cuerpo real de `evaluar_capacidad`, sin gestionar el ciclo de vida de la cache: lo usa
    `enumerar()` para memoizar entre TODAS las capacidades de una pasada, y `evaluar_capacidad()`
    para memoizar solo entre los campos de una capacidad (gap 32)."""
    salida = {"id": cap["id"], "config_path": cap.get("config_path"), "setup_step": cap.get("setup_step")}

    enabled, err = _resolver(cap.get("enabled", False), root)
    if err:
        salida["enabled"] = False
        salida["health"] = {"estado": "error", "detalle": err}
        salida["doctor"] = f"{cap['id']}: error evaluando `enabled` ({err})"
        return salida
    salida["enabled"] = bool(enabled)

    health, err = _resolver(cap.get("health"), root)
    if err:
        salida["health"] = {"estado": "error", "detalle": err}
    elif health is None:
        salida["health"] = {"estado": "desconocido"}
    else:
        salida["health"] = health

    doctor, err = _resolver(cap.get("doctor"), root)
    salida["doctor"] = f"error: {err}" if err else doctor

    return salida


def registrar(cap, registro=None):
    """Anade (o sobrescribe, por `id`) una capacidad en `registro` (por defecto, el registro
    global `REGISTRO`). Devuelve `cap`. Cada capacidad declara el contrato de seis claves; las
    piezas que la registran (kwipu -> T-08, graphiti -> otra iniciativa) no tocan este fichero
    salvo para anadir su propia entrada.

    Gap 16 (revision intento 1): `cap` sin un `id` no vacio levanta un `ValueError` explicito
    aqui, en vez de un `KeyError`/comparacion silenciosa mas abajo en el bucle — un registro mal
    formado se detecta al registrar, no a mitad de un `enumerar()` ajeno."""
    if not isinstance(cap, dict) or not cap.get("id"):
        raise ValueError(f"capacidad invalida: falta `id` no vacio en {cap!r}")
    destino = REGISTRO if registro is None else registro
    for i, existente in enumerate(destino):
        if existente["id"] == cap["id"]:
            destino[i] = cap
            return cap
    destino.append(cap)
    return cap


# Cache de taxonomia por `enumerar()` (gap 22): evita releer/revalidar `taxonomy.json` una vez
# por capacidad (hoy knowledge-gate + kwipu la leen cada uno por su lado, y kwipu la vuelve a leer
# en enabled/health/doctor). Se llena bajo demanda por `root` y se vacia al empezar y al terminar
# cada `enumerar()` (nunca sobrevive entre llamadas: una taxonomia editada entre dos `enumerar()`
# debe verse en la siguiente).
_CACHE_TAXONOMIA = {}


def _estado_taxonomia(root):
    """(ks, config, origen, ruta, errores) para `root`, memoizado dentro de la `_CACHE_TAXONOMIA`
    activa (solo mientras dura un `enumerar()`; ver `enumerar()` para el ciclo de vida)."""
    clave = os.path.abspath(root or ".")
    if clave not in _CACHE_TAXONOMIA:
        ks = _cargar_knowledge_schema()
        config, origen, ruta, errores = ks.cargar_taxonomia(root)
        _CACHE_TAXONOMIA[clave] = (ks, config, origen, ruta, errores)
    return _CACHE_TAXONOMIA[clave]


def enumerar(root=None, registro=None):
    """Lista de capacidades evaluadas sobre `root` (por defecto, cwd). Recorre `registro` (por
    defecto, el registro global `REGISTRO`) sin que el orden de fallos de una capacidad afecte
    a las demas. Memoiza la lectura de `taxonomy.json` durante esta llamada (gap 22): la cache se
    vacia al entrar y al salir, asi que nunca se sirve una taxonomia obsoleta a otra llamada."""
    root = root or "."
    destino = REGISTRO if registro is None else registro
    _CACHE_TAXONOMIA.clear()
    try:
        # `_evaluar_capacidad_sin_limpiar_cache`, no `evaluar_capacidad`: esta ultima vacia la
        # cache al entrar/salir (gap 32) y aqui se quiere compartirla entre TODAS las capacidades
        # de la pasada, no solo dentro de cada una.
        return [_evaluar_capacidad_sin_limpiar_cache(cap, root) for cap in destino]
    finally:
        _CACHE_TAXONOMIA.clear()


# ---------------------------------------------------------------- capacidades del registro base

def _knowledge_gate_enabled(root):
    # El Knowledge Gate (validacion de taxonomy.json + indice) funciona SIEMPRE, con o sin
    # configuracion de proyecto (degrada a la plantilla por defecto del plugin, CA-01/CA-09):
    # no es una capacidad que se pueda "apagar", solo reportar su salud.
    return True


def _knowledge_gate_health(root):
    _ks, _config, _origen, ruta, errores = _estado_taxonomia(root)
    if errores:
        detalle = "; ".join(f"{e['campo']}: {e['mensaje']}" for e in errores)
        return {"estado": "error", "detalle": detalle, "fichero": ruta or TAXONOMY_CONFIG_PATH}
    return {"estado": "ok", "fichero": ruta or "(plantilla por defecto)"}


def _knowledge_gate_doctor(root):
    salud = _knowledge_gate_health(root)
    if salud["estado"] == "ok":
        return f"knowledge-gate: taxonomy.json valido ({salud['fichero']})"
    return f"knowledge-gate: {salud['detalle']} — corrige `{salud.get('fichero', TAXONOMY_CONFIG_PATH)}`"


def _kwipu_backend_config(root):
    _ks, config, _origen, _ruta, errores = _estado_taxonomia(root)
    if errores or not config:
        return {}
    return (config.get("backends") or {}).get("kwipu") or {}


def _kwipu_enabled(root):
    return bool(_kwipu_backend_config(root).get("enabled", False))


def _kwipu_health(root):
    if not _kwipu_enabled(root):
        return {"estado": "deshabilitado"}
    # La comprobacion de red real (GET /health del bridge Kwipu) la hace el adaptador
    # `markdown-export` (T-08); aqui solo se refleja que esta declarado y activado.
    return {"estado": "declarado", "detalle": "health de red la resuelve el adaptador (T-08)"}


def _kwipu_doctor(root):
    salud = _kwipu_health(root)
    if salud["estado"] == "deshabilitado":
        return "kwipu: deshabilitado (backends.kwipu.enabled: false o sin declarar)"
    return f"kwipu: {salud['estado']} — {salud.get('detalle', '')}".rstrip(" —")

# --- capacidad `graphiti` (graphiti-memory T-08, ADR-018) ---------------------------------------
# Una capacidad mas en el registro: ni `/setup` ni `/doctor` llevan codigo propio para ella
# (CA-14 — `doctor.py` no contiene la cadena `graphiti`). Aqui NO se hace red: el estado que se
# publica sale de la CONFIGURACION (`mode`, via el `_modo` del propio adaptador) y la comprobacion
# EN VIVO (`health()`/`verify()` del adaptador) la hace `/doctor` por su cuenta, con su presupuesto
# de tiempo — igual que con `kwipu`.

GRAPHITI_TYPE = "graphiti"
_GRAPHITI_ADAPTADOR_REL = ("skills", "knowledge-services", "backends", "graphiti.py")


def _graphiti_declaracion(root):
    """`(id_del_backend, declaracion)` del backend de tipo `graphiti` declarado en `taxonomy.json`:
    la clave literal `graphiti` si existe y, si no, el primero (por orden de clave) cuyo `type` sea
    `graphiti` — el backend se identifica por `type`, no por la clave (T-01-fix2). `(None, {})` si
    no hay ninguno o la taxonomia no se pudo leer.

    La declaracion se lee AUNQUE la taxonomia traiga errores de validacion: un `graphiti` mal
    configurado tiene que salir como `degradado` con su arreglo (`_graphiti_health`), no como
    «deshabilitado» — que es justo lo contrario de lo que pasa (esta declarado y encendido)."""
    _ks, config, _origen, _ruta, _errores = _estado_taxonomia(root)
    if not config:
        return None, {}
    backends = config.get("backends")
    if not isinstance(backends, dict):
        return None, {}
    candidatos = [(bid, decl) for bid, decl in sorted(backends.items())
                  if isinstance(decl, dict) and decl.get("type") == GRAPHITI_TYPE]
    if not candidatos:
        return None, {}
    for bid, decl in candidatos:
        if bid == GRAPHITI_TYPE:
            return bid, decl
    return candidatos[0]



def _graphiti_errores_de_config(root, bid):
    """Mensajes de validacion (`knowledge-schema.py`) que afectan a ESTE backend, ya formateados."""
    _ks, _config, _origen, _ruta, errores = _estado_taxonomia(root)
    prefijo = f"backends.{bid}."
    return [f"`{e['campo'][len(prefijo):]}`: {e['mensaje']}" for e in (errores or [])
            if str(e.get("campo", "")).startswith(prefijo)]

def _graphiti_modo(cfg):
    """`mode` normalizado. Se pregunta al ADAPTADOR (`_modo`, fuente unica del default y del enum)
    y solo si no esta instalado se cae a la misma regla por escrito."""
    ruta = os.path.join(os.path.dirname(os.path.dirname(HERE)), *_GRAPHITI_ADAPTADOR_REL)
    try:
        spec = importlib.util.spec_from_file_location("capabilities_graphiti_adaptador", ruta)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod._modo(cfg)
    except Exception:  # noqa: BLE001 — sin adaptador instalado, el default del esquema
        modo = (cfg or {}).get("mode")
        return modo if modo in ("off", "shadow", "read") else "shadow"


def _graphiti_enabled(root):
    _bid, decl = _graphiti_declaracion(root)
    return bool(decl.get("enabled", False))


_GRAPHITI_REMEDIOS = {
    "off": "pon `mode: \"shadow\"` en `backends.<id>.config` de `taxonomy.json` para empezar a "
           "sincronizar sin leer",
    "shadow": "cuando el grafo este poblado y `knowledge-sync.py --check` no de desfase, pon "
              "`mode: \"read\"` para que el router pueda leerlo",
    "read": "comprueba la salud real con `/doctor` (o `knowledge-sync.py --backend <id> --check`): "
            "en `read` cada consulta enrutada exige `health` sano y `verify` sin desfase",
}


def _graphiti_health(root):
    bid, decl = _graphiti_declaracion(root)
    if not decl.get("enabled", False):
        return {"estado": "deshabilitado",
                "detalle": "sin declarar o con `enabled: false` en `taxonomy.json`"}
    cfg = decl.get("config") if isinstance(decl.get("config"), dict) else {}
    faltan = [clave for clave in ("endpoint", "group_id") if not cfg.get(clave)]
    errores_config = _graphiti_errores_de_config(root, bid)
    if faltan or errores_config:
        # Declarado y habilitado pero incompleto/invalido: es un problema de CONFIGURACION, no del
        # stack externo — se nombra el campo y el fichero, nunca «deshabilitado» (esta encendido).
        detalle = "; ".join(errores_config) or (
            "habilitado sin " + ", ".join("`" + c + "`" for c in faltan))
        pendientes = faltan or [e.split("`")[1] for e in errores_config if "`" in e]
        return {"estado": "degradado", "backend": bid, "detalle": detalle,
                "remedio": f"corrige `backends.{bid}.config` en `taxonomy.json`: "
                           + ", ".join("`" + c + "`" for c in pendientes)}
    modo = _graphiti_modo(cfg)
    detalles = {
        "off": "apagado por configuracion (`mode: off`): no sincroniza ni lee",
        "shadow": "sincroniza pero NO lee: el router nunca consulta el grafo en `shadow` (CA-10)",
        "read": "lectura enrutada activa: `knowledge-find.py --intent <intent>` puede servirse del "
                "grafo si el intent esta declarado en `router.intents` y `health`/`verify` acompanan",
    }
    return {"estado": modo, "backend": bid, "detalle": detalles[modo],
            "remedio": _GRAPHITI_REMEDIOS[modo]}


def _graphiti_doctor(root):
    salud = _graphiti_health(root)
    if salud["estado"] == "deshabilitado":
        return "graphiti: deshabilitado (sin backend `type: graphiti` habilitado en taxonomy.json)"
    backend = salud.get("backend") or "?"
    return (f"graphiti: `{backend}` en `{salud['estado']}` — {salud['detalle']} · "
            f"{salud.get('remedio', '')}").rstrip(" ·")


REGISTRO = [
    {
        "id": "knowledge-gate",
        "config_path": TAXONOMY_CONFIG_PATH,
        "enabled": _knowledge_gate_enabled,
        "health": _knowledge_gate_health,
        "doctor": _knowledge_gate_doctor,
        "setup_step": "crea `.claude/knowledge-services/taxonomy.json` desde la plantilla del "
                      "plugin si el proyecto quiere categorias propias (opcional; sin el "
                      "fichero, se usa la plantilla por defecto)",
    },
    {
        "id": "kwipu",
        "config_path": TAXONOMY_CONFIG_PATH,
        "enabled": _kwipu_enabled,
        "health": _kwipu_health,
        "doctor": _kwipu_doctor,
        "setup_step": "declara `backends.kwipu.enabled: true` en `taxonomy.json` y el `export_dir` "
                      "donde el adaptador `markdown-export` escribira el export derivado",
    },
    {
        "id": "graphiti",
        "config_path": TAXONOMY_CONFIG_PATH,
        "enabled": _graphiti_enabled,
        "health": _graphiti_health,
        "doctor": _graphiti_doctor,
        "setup_step": "declara un backend `type: \"graphiti\"` con `enabled: true` en "
                      "`taxonomy.json` (`endpoint` local del servidor MCP, `group_id` propio del "
                      "proyecto, `provider` y `mode`: empieza en `shadow`); no registra ningun "
                      "servidor MCP ni toca configuracion global de Claude Code — el adaptador "
                      "habla con el endpoint declarado y nada mas",
    },
]


def _construir_parser():
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--root", default=".", help="raiz del proyecto (default: cwd)")
    return ap


def main(argv=None):
    args = _construir_parser().parse_args(argv)
    for cap in enumerar(args.root):
        estado = cap["health"].get("estado", "?") if isinstance(cap["health"], dict) else cap["health"]
        print(f"{cap['id']}: enabled={cap['enabled']} health={estado} — {cap['doctor']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
