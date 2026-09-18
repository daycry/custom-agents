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
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001 - ya leído, o None (capsys/pythonw)
        pass

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
    enabled/health/doctor se refleja como `{"estado": "error", "detalle": ...}` en ese campo."""
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
        return [evaluar_capacidad(cap, root) for cap in destino]
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
