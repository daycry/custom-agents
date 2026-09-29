#!/usr/bin/env python3
"""
capabilities.py — registro de CAPACIDADES OPCIONALES del plugin (ADR-018 punto 7, CA-14,
`knowledge-services` T-13). Sin dependencias externas.

Cada capacidad opcional (kwipu y training hoy; graphiti despues) declara un dict
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
import json
import importlib.util
import os
import sys
import time

# Consola no UTF-8 (Windows cp1252) o tuberías: reconfigurar ANTES de leer/imprimir (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

HERE = os.path.dirname(os.path.abspath(__file__))
TAXONOMY_CONFIG_PATH = os.path.join(".claude", "knowledge-services", "taxonomy.json")


def _cargar_por_ruta(nombre, ruta):
    """Carga un script por RUTA sin dejar bytecode (#159): `/doctor` y `/setup` solo leen, y ninguna
    carga de una capacidad deja un `__pycache__` en el plugin. Restaura el flag al salir."""
    previo = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location(nombre, ruta)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        sys.dont_write_bytecode = previo


def _cargar_knowledge_schema():
    """Carga knowledge-schema.py (T-01) desde el mismo directorio. Ver la misma nota de
    knowledge-index.py: ambos ficheros viajan siempre juntos en agent-kits/shared/."""
    return _cargar_por_ruta("knowledge_schema", os.path.join(HERE, "knowledge-schema.py"))


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
    _CACHE_TRAINING.clear()
    _CACHE_TRAINING["activa"] = True                                       # #195: una lectura por evaluacion
    try:
        return _evaluar_capacidad_sin_limpiar_cache(cap, root)
    finally:
        _CACHE_TAXONOMIA.clear()
        _CACHE_TRAINING.clear()


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
# #195: la MISMA regla para `training.json` (cuya validacion ejecuta `case_schema.py`, 11-40 ms sin
# bytecode): se lee y valida UNA vez por `enumerar()`/`evaluar_capacidad()` y se reutiliza en `enabled`,
# `health`, `doctor` y el recuento. Solo memoiza con la clave `activa` (dentro de una de esas llamadas);
# fuera, cada llamada directa lee el fichero (nunca una config obsoleta).
_CACHE_TRAINING = {}


def _estado_taxonomia(root):
    """(ks, config, origen, ruta, errores) para `root`, memoizado dentro de la `_CACHE_TAXONOMIA`
    activa (solo mientras dura un `enumerar()`; ver `enumerar()` para el ciclo de vida)."""
    clave = os.path.abspath(root or ".")
    if clave not in _CACHE_TAXONOMIA:
        ks = _cargar_knowledge_schema()
        config, origen, ruta, errores = ks.cargar_taxonomia(root)
        _CACHE_TAXONOMIA[clave] = (ks, config, origen, ruta, errores)
    return _CACHE_TAXONOMIA[clave]


_PLAZO = {}


def plazo_restante(defecto):
    """#164: el tope de tiempo que una capacidad puede gastar AHORA: el MENOR entre su `defecto` y lo
    que queda del `plazo_s` de la `enumerar()` en curso (sin `plazo_s`, `defecto` tal cual; nunca < 0)."""
    hasta = _PLAZO.get("hasta")
    if hasta is None:
        return defecto
    return max(0.0, min(defecto, hasta - time.monotonic()))


def enumerar(root=None, registro=None, plazo_s=None):
    """Lista de capacidades evaluadas sobre `root` (por defecto, cwd). Recorre `registro` (por
    defecto, el registro global `REGISTRO`) sin que el orden de fallos de una capacidad afecte
    a las demas. Memoiza la lectura de `taxonomy.json` durante esta llamada (gap 22): la cache se
    vacia al entrar y al salir, asi que nunca se sirve una taxonomia obsoleta a otra llamada.
    `plazo_s` (#164, opcional): el presupuesto que le queda a quien llama (`/doctor`); una capacidad
    que tarda al evaluarse lo consulta con `plazo_restante()` y nunca se pasa de el."""
    root = root or "."
    destino = REGISTRO if registro is None else registro
    _CACHE_TAXONOMIA.clear()
    _CACHE_TRAINING.clear()
    _CACHE_TRAINING["activa"] = True                                       # #195
    _PLAZO["hasta"] = None if plazo_s is None else time.monotonic() + max(0.0, plazo_s)
    try:
        # `_evaluar_capacidad_sin_limpiar_cache`, no `evaluar_capacidad`: esta ultima vacia la
        # cache al entrar/salir (gap 32) y aqui se quiere compartirla entre TODAS las capacidades
        # de la pasada, no solo dentro de cada una.
        return [_evaluar_capacidad_sin_limpiar_cache(cap, root) for cap in destino]
    finally:
        _CACHE_TAXONOMIA.clear()
        _CACHE_TRAINING.clear()
        _PLAZO.pop("hasta", None)


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


TRAINING_CONFIG_PATH = os.path.join(".claude", "knowledge-services", "training.json")


def _cargar_case_schema():
    """`case_schema.py` de la skill `training-data-services` (fuente UNICA del esquema de
    `training.json`, T-01). skills/ y agent-kits/ son hermanos en el repo y en la instalacion del
    plugin; si la skill no viaja (paquete parcial), None y la capacidad degrada a `declarado`."""
    ruta = os.path.normpath(os.path.join(HERE, "..", "..", "skills", "training-data-services",
                                         "scripts", "case_schema.py"))
    if not os.path.isfile(ruta):
        return None
    return _cargar_por_ruta("tds_case_schema", ruta)                  # #159: sin `__pycache__`


TRAINING_PLAZO_S = 2.0   # T-10: tope del recuento del case store en `/doctor` (medido: 10^4 versiones
                         # tardan 10,7 s en caliente y > 70 s en frio en Windows; pasado el tope, PARCIAL)
_TDS = {}


def _cargar_tds():
    """`{"rec": case-recorder.py, "asm": dataset-assembler.py}` de la skill `training-data-services`
    (los lectores seguros del case store y la frescura del dataset: fuente UNICA, T-10), memoizado por
    proceso. None si la skill no viaja (paquete parcial) o no carga: el recuento degrada con aviso."""
    if "mods" not in _TDS:
        base = os.path.normpath(os.path.join(HERE, "..", "..", "skills", "training-data-services", "scripts"))
        ruta = os.path.join(base, "dataset-assembler.py")
        mods = None
        if os.path.isfile(ruta):
            try:                                # `/doctor` solo lee: ni un `__pycache__` en el plugin
                asm = _cargar_por_ruta("tds_dataset_assembler_cap", ruta)
                mods = {"rec": asm.rec, "asm": asm}
            except Exception:   # noqa: BLE001 — una skill rota no tumba /doctor ni /setup
                mods = None
        _TDS["mods"] = mods
    return _TDS["mods"]


def _estado_training(root):
    """(config|None, ruta|None, errores, validado) del `training.json` de `root`. Solo lee un JSON
    local: sin red, sin crear nada (CA-01, CA-07). `validado` es False si falta `case_schema.py`."""
    ruta = os.path.join(root or ".", TRAINING_CONFIG_PATH)
    if not os.path.isfile(ruta):
        return None, None, [], True
    cs = _cargar_case_schema()
    if cs is not None:
        config, ruta_cs, errores = cs.cargar_config(root or ".")
        return config, ruta_cs, errores, True
    try:
        with open(ruta, encoding="utf-8") as f:
            config = json.load(f)
    except (OSError, ValueError) as e:
        return None, ruta, [{"campo": "(fichero)", "mensaje": f"JSON ilegible: {e}"}], False
    if not isinstance(config, dict):
        return None, ruta, [{"campo": "(raiz)", "mensaje": "training.json debe ser un objeto JSON"}], False
    return config, ruta, [], False


def _training(root):
    """#195: `_estado_training(root)` memoizado dentro de la `enumerar()`/`evaluar_capacidad()` en curso
    (`_CACHE_TRAINING`); fuera de ellas, una lectura por llamada."""
    if not _CACHE_TRAINING.get("activa"):
        return _estado_training(root)
    clave = os.path.abspath(root or ".")
    if clave not in _CACHE_TRAINING:
        _CACHE_TRAINING[clave] = _estado_training(root)
    return _CACHE_TRAINING[clave]


def _training_enabled(root):
    config, _ruta, errores, _validado = _training(root)
    return bool(config and not errores and config.get("enabled") is True)


def _training_root(root, config):
    destino = config.get("root") or ""
    return destino if os.path.isabs(destino) else os.path.abspath(os.path.join(root or ".", destino))


def _texto(ruta):
    """#153 (CWE-150): una ruta o nombre del store en la salida de la capacidad, ESCAPADA igual que en
    la skill (`case-recorder._texto_ruta`: `ascii()` si tiene algo no ASCII o no imprimible —bidi
    U+202E, CSI U+009B—); sin la skill, la misma regla aqui."""
    tds = _cargar_tds()
    if tds is not None:
        return tds["rec"]._texto_ruta(ruta)
    texto = str(ruta)
    return texto if texto.isascii() and texto.isprintable() else ascii(texto)


def _training_health(root):
    config, ruta, errores, validado = _training(root)
    if errores:
        detalle = "; ".join(f"{e['campo']}: {e['mensaje']}" for e in errores)
        return {"estado": "error", "detalle": detalle, "fichero": _texto(ruta) if ruta else TRAINING_CONFIG_PATH}
    if not config or config.get("enabled") is not True:
        return {"estado": "deshabilitado"}
    if not validado:
        return {"estado": "declarado",
                "detalle": "sin `case_schema.py` de la skill training-data-services: config sin validar"}
    store = _training_root(root, config)
    if not os.path.isdir(store):
        return {"estado": "declarado", "root": store,
                "detalle": f"el case store `{_texto(store)}` aun no existe (lo crea el recorder al grabar)"}
    return {"estado": "ok", "root": store, "detalle": f"case store en `{_texto(store)}`"}


def _texto_recuento(res, ds):
    """Texto de `/doctor` del recuento del case store y de la frescura del dataset (T-10): lo da el
    ENSAMBLADOR (`texto_estado`, fuente unica: el mismo de `dataset-assembler.py --estado`); aqui solo
    se delega (los veredictos y su texto son de la skill)."""
    return _cargar_tds()["asm"].texto_estado(res, ds)


def _training_doctor(root):
    salud = _training_health(root)
    if salud["estado"] == "deshabilitado":
        return "training: deshabilitado (sin training.json o enabled: false)"
    if salud["estado"] == "error":
        return f"training: {salud['detalle']} — corrige `{salud['fichero']}`"
    base = f"training: {salud['estado']} — {salud.get('detalle', '')}".rstrip(" —")
    if salud["estado"] != "ok":
        return base
    tds = _cargar_tds()
    if tds is None:
        return f"{base} · recuento no disponible (sin los scripts de la skill training-data-services)"
    try:
        # M10: `estado_dataset` tiene un margen propio tras el recuento; el total (recuento + margen) no pasa
        # del tope de la capacidad ni de lo que le quede al bloque de `/doctor` (#164)
        margen = tds["asm"].MARGEN_ESTADO_S
        config = _training(root)[0] or {}             # #195: la lectura ya hecha, ANTES del plazo
        total = plazo_restante(TRAINING_PLAZO_S + margen)
        plazo = TRAINING_PLAZO_S if total >= TRAINING_PLAZO_S + margen else max(0.0, total - margen)
        # #181/N2: el `id_prefix` de training.json, EXPLICITO (sin el, la regla permisiva del recorder)
        res = tds["rec"].resumen_store(salud["root"], root or ".", plazo_s=plazo, id_prefix=config.get("id_prefix"))
        ds = tds["asm"].estado_dataset(salud["root"], res)
        texto = tds["asm"].texto_estado(res, ds)
    except Exception as e:   # noqa: BLE001 — informar nunca bloquea (CA-07)
        return f"{base} · recuento no disponible ({type(e).__name__})"
    return f"{base} · {texto}"


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
        "id": "training",
        "config_path": TRAINING_CONFIG_PATH,
        "enabled": _training_enabled,
        "health": _training_health,
        "doctor": _training_doctor,
        "setup_step": "crea `.claude/knowledge-services/training.json` con `version: 1`, "
                      "`enabled: true`, el `root` del case store (fuera de Git y de "
                      "`docs/knowledge/`) y el `id_prefix` de los casos; `bridge_to_curator` "
                      "opcional (skill `training-data-services`)",
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
