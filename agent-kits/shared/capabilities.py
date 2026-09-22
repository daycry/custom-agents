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
import re
import sys

# Consola no UTF-8 (Windows cp1252) o tuberías: reconfigurar ANTES de leer/imprimir (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

# --8<-- sanear_detalle (funcion) — REPLICADO LITERAL en las CINCO copias declaradas del bloque `sanear_detalle` de agent-kits/shared/copias.json
# Gap #93 (Minor, fix5): la clase [\x00-\x1f\x7f] dejaba pasar tres familias que TAMBIEN
# falsifican una linea de log o invierten visualmente el texto de un mensaje/`causa`: los
# controles C1 (\x80-\x9f, entre ellos CSI \x9b), los separadores Unicode de linea/parrafo
# ( / , que muchos visores rompen como salto de linea) y los controles bidi
# (‪-‮ RLO/LRO..., ⁦-⁩ isolates), con los que un texto hostil del servidor
# puede reordenar lo que el humano lee sin cambiar un solo byte del resto.
_CONTROL_O_ANSI_RE = re.compile(
    r"\x1b\[[0-9;]*[A-Za-z]|[\x00-\x1f\x7f-\x9f  ‪-‮⁦-⁩]")
_SANEADO_TOPE_CHARS = 200


def _sanear_detalle(texto):
    """Recorta a 200 caracteres y sustituye caracteres de control (incluidas las secuencias ANSI
    `ESC[...`, los C1, los separadores Unicode y los controles bidi) por un espacio; ver
    comentario arriba para el porque de cada regla."""
    saneado = _CONTROL_O_ANSI_RE.sub(" ", str(texto))
    return saneado[:_SANEADO_TOPE_CHARS]
# --8<-- fin sanear_detalle (funcion)


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


def _kwipu_doctor_texto(bid, salud):
    """Linea de `/doctor` de una capacidad con backend, con la CLAVE y el DETALLE saneados
    (gap #107, CWE-117: los dos se interpolaban crudos y acaban en un log que lee un humano)."""
    return (f"{_sanear_detalle(bid)}: {_sanear_detalle(salud.get('estado', '?'))} — "
            f"{_sanear_detalle(salud.get('detalle', ''))}").rstrip(" —")


def _kwipu_doctor(root):
    salud = _kwipu_health(root)
    if salud["estado"] == "deshabilitado":
        return "kwipu: deshabilitado (backends.kwipu.enabled: false o sin declarar)"
    return _kwipu_doctor_texto("kwipu", salud)

# --- capacidad `graphiti` (graphiti-memory T-08, ADR-018) ---------------------------------------
# Una capacidad mas en el registro: ni `/setup` ni `/doctor` llevan codigo propio para ella
# (CA-14 — `doctor.py` no contiene la cadena `graphiti`). Aqui NO se hace red: el estado que se
# publica sale de la CONFIGURACION (`mode`, via el `_modo` del propio adaptador) y la comprobacion
# EN VIVO (`health()`/`verify()` del adaptador) la hace `/doctor` por su cuenta, con su presupuesto
# de tiempo — igual que con `kwipu`.

# --8<-- modo del backend (funcion publica del contrato, T-08-fix1) — REPLICADO LITERAL en las copias declaradas del bloque `modo_backend` de agent-kits/shared/copias.json
# Gap #109 (Minor, fix1 Fase 3): `capabilities.py` duplicaba el enum y el default de `mode` sin
# declararlo como copia (ADR-016) y ademas llamaba al simbolo PRIVADO `_modo` del adaptador,
# fuera del contrato E16. El adaptador expone `modo(cfg)` -funcion OPCIONAL del contrato,
# documentada en `backends/README.md`- y el respaldo de `capabilities.py` (para cuando el
# adaptador no esta instalado) es ESTE MISMO bloque, declarado en `copias.json`.
_MODOS = ("off", "shadow", "read")
_MODO_DEFAULT = "shadow"


def modo(cfg):
    """`mode` normalizado (`off`/`shadow`/`read`), default `shadow` (el mismo del esquema).
    Gap #35: antes se validaba pero nadie lo LEIA -`off` seguia sincronizando-."""
    valor = (cfg or {}).get("mode")
    return valor if valor in _MODOS else _MODO_DEFAULT
# --8<-- fin modo del backend


GRAPHITI_TYPE = "graphiti"
_GRAPHITI_ADAPTADOR_REL = ("skills", "knowledge-services", "backends", "graphiti.py")


def _graphiti_candidatos(root):
    """`[(id, declaracion)]` de TODOS los backends de `type: graphiti` de `taxonomy.json`, por
    orden de clave. Se leen AUNQUE la taxonomia traiga errores de validacion: un `graphiti` mal
    configurado tiene que salir como `degradado` con su arreglo (`_graphiti_health`), no como
    «deshabilitado» — que es justo lo contrario de lo que pasa (esta declarado y encendido)."""
    _ks, config, _origen, _ruta, _errores = _estado_taxonomia(root)
    if not config:
        return []
    backends = config.get("backends")
    if not isinstance(backends, dict):
        return []
    return [(bid, decl) for bid, decl in sorted(backends.items())
            if isinstance(decl, dict) and decl.get("type") == GRAPHITI_TYPE]


def _graphiti_habilitados(root):
    """Ids de los backends `type: graphiti` con `enabled: true` (gap #99)."""
    return [bid for bid, decl in _graphiti_candidatos(root) if decl.get("enabled") is True]


def _graphiti_declaracion(root):
    """`(id_del_backend, declaracion)` del backend de tipo `graphiti` que representa la capacidad.

    Gap #99 (Important, fix1 Fase 3): el desempate por la clave literal `graphiti` se aplicaba
    ANTES de mirar `enabled`, asi que la situacion NOMINAL tras `/setup` —la plantilla de fabrica
    deja `backends.graphiti` declarado y APAGADO, y el proyecto declara el suyo con otra clave y
    encendido— daba «deshabilitado» en `/doctor` mientras el router SI leia del otro. Ahora
    mandan los HABILITADOS (y entre ellos, la clave literal solo desempata); si no hay ninguno
    habilitado, se informa del primero declarado. `(None, {})` si no hay ninguno."""
    candidatos = _graphiti_candidatos(root)
    if not candidatos:
        return None, {}
    habilitados = [(bid, decl) for bid, decl in candidatos if decl.get("enabled") is True]
    preferentes = habilitados or candidatos
    for bid, decl in preferentes:
        if bid == GRAPHITI_TYPE:
            return bid, decl
    return preferentes[0]



def _graphiti_errores_de_config(root, bid):
    """Mensajes de validacion (`knowledge-schema.py`) que afectan a ESTE backend, ya formateados."""
    _ks, _config, _origen, _ruta, errores = _estado_taxonomia(root)
    prefijo = f"backends.{bid}."
    return [f"`{e['campo'][len(prefijo):]}`: {e['mensaje']}" for e in (errores or [])
            if str(e.get("campo", "")).startswith(prefijo)]

def _graphiti_modo(cfg):
    """`mode` normalizado. Se pregunta al ADAPTADOR por su funcion PUBLICA `modo(cfg)` (fuente
    unica del default y del enum, gap #109: antes se llamaba al simbolo privado `_modo`, fuera
    del contrato E16) y solo si no esta instalado se cae al respaldo local —que es la MISMA
    regla, declarada como copia en `copias.json` (bloque `modo_backend`, ADR-016)."""
    ruta = os.path.join(os.path.dirname(os.path.dirname(HERE)), *_GRAPHITI_ADAPTADOR_REL)
    try:
        spec = importlib.util.spec_from_file_location("capabilities_graphiti_adaptador", ruta)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.modo(cfg)
    except Exception:  # noqa: BLE001 — sin adaptador instalado, el respaldo declarado
        return modo(cfg)


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
    modo_backend = _graphiti_modo(cfg)
    detalles = {
        "off": "apagado por configuracion (`mode: off`): no sincroniza ni lee",
        "shadow": "sincroniza pero NO lee: el router nunca consulta el grafo en `shadow` (CA-10)",
        "read": "lectura enrutada activa: `knowledge-find.py --intent <intent>` puede servirse del "
                "grafo si el intent esta declarado en `router.intents` y `health`/`verify` acompanan",
    }
    salud = {"estado": modo_backend, "backend": bid, "detalle": detalles[modo_backend],
             "remedio": _GRAPHITI_REMEDIOS[modo_backend]}
    habilitados = _graphiti_habilitados(root)
    if len(habilitados) > 1:
        # Gap #99: varios backends `type: graphiti` encendidos a la vez son configuracion valida
        # (el router los recorre por orden de clave): se declaran TODOS para que `/doctor` pinte
        # una fila de red por cada uno, no solo por el que representa la capacidad.
        salud["backends"] = habilitados
    return salud


def _graphiti_doctor(root):
    salud = _graphiti_health(root)
    if salud["estado"] == "deshabilitado":
        return "graphiti: deshabilitado (sin backend `type: graphiti` habilitado en taxonomy.json)"
    # Gap #107 (CWE-117): la clave del backend y el `detalle` vienen de configuracion y de
    # mensajes de validacion; se sanean antes de componer la linea que lee un humano.
    backends = salud.get("backends") or [salud.get("backend") or "?"]
    # Gap #147 (Minor, fix3 Fase 3): con >= 2 backends habilitados la linea decia la lista DOS
    # veces (aqui y en la pieza que anadio #125). El encabezado se queda con el CONTEO y la lista
    # vive en su propia pieza (la que el recorte de 200 caracteres por pieza no se come).
    nombres = (", ".join("`" + _sanear_detalle(b) + "`" for b in backends) if len(backends) == 1
               else str(len(backends)) + " backends `type: graphiti`")
    # Gap #125 (Minor, fix2 Fase 3): el tope de `_sanear_detalle` es POR PIEZA, no por linea, y la
    # lista de backends habilitados es su propia pieza. Antes se concatenaba DENTRO de `detalle`
    # (`_graphiti_health`) y, en la situacion nominal del #99 (>= 2 backends habilitados), el
    # recorte de 200 caracteres del `detalle` de `read` se comia justo esa lista: la frase acababa
    # en «hay 2 backends `type: graphiti` » y se perdia lo unico que la fila anadia.
    piezas = [_sanear_detalle(salud["detalle"])]
    if len(salud.get("backends") or []) > 1:
        piezas.append(_sanear_detalle(
            "hay " + str(len(salud["backends"])) + " backends `type: graphiti` habilitados: "
            + ", ".join("`" + b + "`" for b in salud["backends"])))
    piezas.append(_sanear_detalle(salud.get("remedio", "")))
    return (f"graphiti: {nombres} en `{_sanear_detalle(salud['estado'])}` — "
            + " · ".join(p for p in piezas if p)).rstrip(" ·—").rstrip()


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
