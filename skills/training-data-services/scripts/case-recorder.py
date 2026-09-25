#!/usr/bin/env python3
"""
case-recorder.py — recorder determinista de casos de `training-data-services` (design.md O1).

Graba cada intento del proyecto como una VERSION inmutable del case store, en el `root` que declara
`.claude/knowledge-services/training.json` (fuera de Git y de `docs/knowledge/`, ADR-019). Opt-in:
sin config, o con `enabled: false`, se niega a grabar y no escribe nada (CA-01). El plugin valida
FORMA, nunca dominio (CA-04): las metricas llegan ya calculadas por el proyecto.

`grabar(caso, config, raiz_proyecto, approved_by_human=False)`, en este orden:
  1. redacta secretos de `request`, `context`, `constraints` y `trajectory` con
     `agent-kits/shared/redact.py` (fuente unica; sin el -> `RedaccionNoDisponible`, CA-09);
  2. valida el caso YA redactado con `case_schema.validar_caso` (con la config del proyecto);
  3. solo entonces escribe. Si algo falla antes, no se toca disco.
  - Sin `version`, se asigna la siguiente libre (mayor existente + 1); con `version` que ya
    existe -> rechazo: nunca sobrescribe (CA-02). La reserva es atomica tambien con recorders
    concurrentes: se escribe en un directorio temporal hermano (`.tmp-*`) y la version se reserva
    con `os.mkdir` del destino, que falla si existe (nunca `rename` de directorio, que en POSIX
    sustituye un directorio vacio). `metadata.json` se mueve el ULTIMO: una version sin el esta a
    medio escribir.
  - Un caso no nace `approved` (Gold) por `record` salvo con `approved_by_human=True`
    (`--approved-by-human`): la misma puerta que `set-status`, sin puerta trasera.
  - `corrected` + `supersedes_case`: la version citada debe existir en el store (CA-12).
  - Sin `validation`, el caso nace `pending`. Sin `case_id`, se construye con la config.
  - No hay operacion de borrado: rechazados y fallidos se conservan (CA-02).

Estructura (`case_schema.directorio_version`, ancho `ids.version_width`):
  <root>/cases/<family>.<variant>/v<NNN>/{metadata.json, request.json ({"request": ...}),
  context.json, constraints.json, trajectory.jsonl, metrics.json, validation.json,
  final/artifacts.json}  — JSON UTF-8 sin escapar (`ensure_ascii=False`), fin de linea LF.

Uso (exit 0 ok · 1 rechazo/validacion · 2 uso/JSON ilegible, como `case_schema.py`):
  case-recorder.py record <caso.json> [--config <training.json>] [--project-root <dir>] [--approved-by-human]
"""
import argparse
import datetime
import importlib.util
import json
import os
import sys
import tempfile

# Consola no UTF-8 (Windows cp1252) o tuberias: reconfigurar ANTES de leer/imprimir (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leido o None (capsys, pythonw)

HERE = os.path.dirname(os.path.abspath(__file__))

CAMPOS_REDACTADOS = ("request", "context", "constraints", "trajectory")
MENSAJE_GOLD = "approved exige --approved-by-human: Gold es siempre una accion humana"
PREFIJO_TEMPORAL = ".tmp-"
DIGITOS = "0123456789"


def _cargar_schema():
    """`case_schema.py` de la MISMA skill (fuente unica del esquema, de los ids y de las rutas)."""
    spec = importlib.util.spec_from_file_location("tds_case_schema", os.path.join(HERE, "case_schema.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cs = _cargar_schema()


class RedaccionNoDisponible(RuntimeError):
    """`agent-kits/shared/redact.py` no se encuentra: no se puede grabar ningun caso."""


class Rechazo(Exception):
    """El recorder se niega a escribir. `errores` es una lista `{campo, mensaje}`."""

    def __init__(self, mensaje, errores=None):
        self.mensaje = mensaje
        self.errores = list(errores) if errores else [{"campo": "(caso)", "mensaje": mensaje}]
        detalle = "; ".join(f"{e['campo']}: {e['mensaje']}" for e in errores) if errores else ""
        super().__init__(f"{mensaje}: {detalle}" if detalle else mensaje)


class _EntradaIlegible(Exception):
    """JSON de entrada ilegible o ausente (exit 2)."""


# ------------------------------------------------------------------ redaccion (T-02)

def _dirs_redact():
    """Donde buscar `redact.py`: el arbol del plugin (skills/ y agent-kits/ son hermanos, en el repo
    y en la instalacion) y, si el runtime lo exporta, `CLAUDE_PLUGIN_ROOT`."""
    dirs = [os.path.normpath(os.path.join(HERE, "..", "..", "..", "agent-kits", "shared"))]
    raiz = os.environ.get("CLAUDE_PLUGIN_ROOT")
    if raiz:
        dirs.append(os.path.join(raiz, "agent-kits", "shared"))
    return dirs


def cargar_redact(dirs=None):
    """Carga `redact.py` desde el primer directorio de `dirs` que lo contenga."""
    for d in dirs if dirs is not None else _dirs_redact():
        ruta = os.path.join(d, "redact.py")
        if os.path.isfile(ruta):
            spec = importlib.util.spec_from_file_location("tds_redact", ruta)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    raise RedaccionNoDisponible(
        "no se encuentra agent-kits/shared/redact.py (fuente unica de la redaccion de secretos); "
        "reinstala el plugin completo: el recorder no graba casos sin redactar")


_REDACT = None


def _redact_mod():
    """`redact.py` cargado la PRIMERA vez que se redacta (gap #8): importar este modulo nunca
    falla por su ausencia; redactar (y por tanto grabar) si, con `RedaccionNoDisponible`."""
    global _REDACT
    if _REDACT is None:
        _REDACT = cargar_redact()
    return _REDACT


def __getattr__(nombre):
    """`redactar`/`REDACTADO` son los de `redact.py` (mismo objeto, no una copia), resueltos
    perezosamente (PEP 562)."""
    if nombre in ("redactar", "REDACTADO"):
        return getattr(_redact_mod(), nombre)
    raise AttributeError(f"module {__name__!r} has no attribute {nombre!r}")


def redactar_estructura(valor):
    """Copia de `valor` con la redaccion de `redact.py` aplicada a cada cadena: valores y CLAVES
    textuales de dicts, elementos de listas, tuplas, sets y frozensets (recursivo, gap #8). Lo no
    textual no se toca; la entrada no muta. Sin `redact.py` -> `RedaccionNoDisponible`.

    Claves (fix2, gap #18): si dos claves distintas se redactan al mismo literal, la segunda y
    siguientes llevan un sufijo estable por orden de aparicion (`<clave redactada> #2`, `#3`...), y
    una clave que NO cambia al redactar conserva siempre su nombre: nunca se pierde un valor. Una
    namedtuple se reconstruye con `_make` (mismo tipo y campos)."""
    redactar_txt = _redact_mod().redactar

    def _dict(v):
        nuevas = {k: (redactar_txt(k) if isinstance(k, str) else k) for k in v}
        intactas = {k for k, n in nuevas.items() if n == k}
        out = {}
        for k, x in v.items():
            nombre = nuevas[k]
            if k not in intactas:
                n = 1
                while nombre in out or nombre in intactas:
                    n += 1
                    nombre = f"{nuevas[k]} #{n}"
            out[nombre] = _rec(x)
        return out

    def _rec(v):
        if isinstance(v, str):
            return redactar_txt(v)
        if isinstance(v, dict):
            return _dict(v)
        if isinstance(v, tuple) and hasattr(type(v), "_make"):
            return type(v)._make(_rec(x) for x in v)
        if isinstance(v, (list, tuple, set, frozenset)):
            return type(v)(_rec(x) for x in v)
        return v

    return _rec(valor)


# ------------------------------------------------------------------ config y rutas

def _ahora():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def config_activa(config, raiz_proyecto=None):
    """Comprueba que la capacidad esta configurada, es valida y esta activada; si no, `Rechazo`
    (nunca se escribe nada con la capacidad apagada, CA-01)."""
    if config is None:
        raise Rechazo("training-data-services no esta configurado: falta .claude/knowledge-services/"
                      "training.json (opt-in); no se escribe nada")
    errores = cs.validar_config(config, raiz_proyecto)
    if errores:
        raise Rechazo("training.json invalido; no se escribe nada", errores)
    if config.get("enabled") is not True:
        raise Rechazo("training-data-services desactivado (enabled: false en training.json); no se escribe nada")


def raiz_store(config, raiz_proyecto=None):
    """Ruta absoluta del case store: `root` de la config, relativo a la raiz del proyecto."""
    return os.path.abspath(os.path.join(raiz_proyecto or ".", config["root"]))


def _es_version(nombre):
    return len(nombre) > 1 and nombre[0] == "v" and all(c in DIGITOS for c in nombre[1:])


def versiones(dir_caso):
    """Versiones (enteros) presentes en `cases/<family>.<variant>/`, completas o no."""
    try:
        nombres = os.listdir(dir_caso)
    except OSError:
        return []
    return sorted(int(n[1:]) for n in nombres if _es_version(n) and os.path.isdir(os.path.join(dir_caso, n)))


def _siguiente_version(dir_caso):
    vs = versiones(dir_caso)
    return (vs[-1] + 1) if vs else 1


def _nombre_version(version, width):
    return os.path.basename(cs.directorio_version("x", "y", version, width))


# ------------------------------------------------------------------ escritura

def _json_bytes(obj):
    return (json.dumps(obj, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def _ficheros_de(caso):
    """Contenido (bytes) de cada fichero de la version salvo `metadata.json` (se escribe el ultimo,
    ya con la version reservada)."""
    val = caso["validation"]
    return {
        "request.json": _json_bytes({"request": caso["request"]}),
        "context.json": _json_bytes(caso.get("context", {})),
        "constraints.json": _json_bytes(caso.get("constraints", {})),
        "trajectory.jsonl": "".join(json.dumps(t, ensure_ascii=False) + "\n" for t in caso["trajectory"]).encode("utf-8"),
        "metrics.json": _json_bytes(caso.get("metrics", {})),
        "validation.json": _json_bytes({"status": val["status"], "approved_by_human": val.get("approved_by_human", False),
                                        "approved_at": val.get("approved_at"), "reviewer_note": val.get("reviewer_note")}),
        os.path.join("final", "artifacts.json"): _json_bytes(caso.get("artifacts", [])),
    }


def _metadata(caso):
    meta = {k: caso[k] for k in ("case_id", "family", "variant", "version")}
    meta["created_at"] = caso.get("created_at") or _ahora()
    meta["outcome"] = caso["outcome"]
    if caso.get("supersedes_case") is not None:
        meta["supersedes_case"] = caso["supersedes_case"]
    return meta


def _escribir(ruta, datos):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "wb") as f:
        f.write(datos)


def _limpiar_temporal(tmp):
    """Elimina SOLO el directorio temporal propio (`.tmp-*`) y lo que quede dentro: nunca una version."""
    if not os.path.basename(tmp).startswith(PREFIJO_TEMPORAL):
        return
    for base, dirs, fs in os.walk(tmp, topdown=False):
        for f in fs:
            try: os.remove(os.path.join(base, f))
            except OSError: pass
        for d in dirs:
            try: os.rmdir(os.path.join(base, d))
            except OSError: pass
    try: os.rmdir(tmp)
    except OSError: pass


def _reservar_y_mover(dir_caso, caso, width, auto):
    """Escribe en `.tmp-*` hermano, reserva `v<NNN>` con `os.mkdir` (falla si existe: nadie pisa a
    nadie) y mueve los ficheros; `metadata.json` el ultimo. Devuelve la ruta de la version."""
    os.makedirs(dir_caso, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix=PREFIJO_TEMPORAL, dir=dir_caso)
    try:
        ficheros = _ficheros_de(caso)
        for rel, datos in ficheros.items():
            _escribir(os.path.join(tmp, rel), datos)
        version = caso["version"]
        while True:
            destino = os.path.join(dir_caso, _nombre_version(version, width))
            try:
                os.mkdir(destino)
                break
            except FileExistsError:
                if not auto:
                    raise Rechazo(f"{cs.referencia_version(caso['case_id'], version, width)} ya existe: el recorder "
                                  "nunca sobrescribe una version (graba sin `version` para la siguiente libre)")
                version = max(version + 1, _siguiente_version(dir_caso))
        caso["version"] = version
        os.mkdir(os.path.join(destino, "final"))
        for rel in ficheros:
            os.replace(os.path.join(tmp, rel), os.path.join(destino, rel))
        _escribir(os.path.join(tmp, "metadata.json"), _json_bytes(_metadata(caso)))
        os.replace(os.path.join(tmp, "metadata.json"), os.path.join(destino, "metadata.json"))
        return destino
    finally:
        _limpiar_temporal(tmp)


def _comprobar_supersedes(caso, dir_caso, width):
    """CA-12: la version que corrige un `corrected` debe existir (se conserva junto a la correccion)."""
    sup = caso.get("supersedes_case")
    if sup is None:
        return
    m = cs.PATRON_REFERENCIA.fullmatch(sup)
    citada = os.path.join(dir_caso, _nombre_version(int(m.group(2)), width), "metadata.json")
    if not os.path.isfile(citada):
        raise Rechazo("caso invalido: no se escribe nada", [{
            "campo": "supersedes_case",
            "mensaje": f"`{sup}` no existe en el case store: un `corrected` solo corrige una version grabada"}])


def grabar(caso, config, raiz_proyecto=None, approved_by_human=False):
    """Graba `caso` como una version nueva. Devuelve `{case_id, version, ref, path}`; `Rechazo` si
    la capacidad esta apagada o el caso no vale, `RedaccionNoDisponible` sin `redact.py`. En ambos
    casos no se escribe nada."""
    config_activa(config, raiz_proyecto)
    if not isinstance(caso, dict):
        raise Rechazo("caso invalido: no se escribe nada", cs.validar_caso(caso, config))
    caso = dict(caso)
    for campo in CAMPOS_REDACTADOS:                       # 1. redactar
        if campo in caso:
            caso[campo] = redactar_estructura(caso[campo])

    val = caso.get("validation")
    if val is None:
        caso["validation"] = {"status": "pending", "approved_by_human": False}
    elif isinstance(val, dict) and val.get("status") == "approved":
        if not approved_by_human:
            raise Rechazo(MENSAJE_GOLD)
        caso["validation"] = dict(val, approved_by_human=True, approved_at=val.get("approved_at") or _ahora())
    fam, var = caso.get("family"), caso.get("variant")
    if "case_id" not in caso and isinstance(fam, str) and isinstance(var, str):
        caso["case_id"] = cs.construir_case_id(config.get("id_prefix"), fam, var)

    width = cs.patrones_id(config)[2]
    store = raiz_store(config, raiz_proyecto)
    auto = "version" not in caso
    if auto:
        try:
            dir_caso = os.path.join(store, os.path.dirname(cs.directorio_version(fam, var, 1, width)))
            caso["version"] = _siguiente_version(dir_caso)
        except (ValueError, TypeError):
            caso["version"] = 1                              # el validador dira que falla

    errores = cs.validar_caso(caso, config)               # 2. validar lo YA redactado
    if errores:
        raise Rechazo("caso invalido: no se escribe nada", errores)
    dir_caso = os.path.join(store, os.path.dirname(cs.directorio_version(fam, var, caso["version"], width)))
    _comprobar_supersedes(caso, dir_caso, width)
    destino = _reservar_y_mover(dir_caso, caso, width, auto)  # 3. escribir
    return {"case_id": caso["case_id"], "version": caso["version"],
            "ref": cs.referencia_version(caso["case_id"], caso["version"], width), "path": destino}


# ------------------------------------------------------------------ CLI

def _leer_json(ruta):
    try:
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    except RecursionError:
        raise _EntradaIlegible(f"{ruta}: {cs.ANIDAMIENTO_JSON}") from None
    except (OSError, ValueError) as e:
        raise _EntradaIlegible(f"{ruta}: JSON ilegible o fichero ausente: {e}") from None


def _config_cli(args):
    """`(config|None, raiz_proyecto)`: `--config` explicito (raiz deducida de su ruta o
    `--project-root`) o el `training.json` del proyecto (`--project-root` o cwd)."""
    if args.config:
        return _leer_json(args.config), cs._raiz_de(args.config, args.project_root)
    raiz = args.project_root or os.getcwd()
    cfg, ruta, errores = cs.cargar_config(raiz)
    if errores and any(e["campo"] == "(fichero)" for e in errores):
        raise _EntradaIlegible(f"{ruta}: {errores[0]['mensaje']}")
    if errores:
        raise Rechazo("training.json invalido; no se escribe nada", errores)
    return cfg, raiz


def _comunes(p):
    p.add_argument("--config", help="training.json del proyecto (default: <project-root>/.claude/knowledge-services/training.json)")
    p.add_argument("--project-root", help="raiz del proyecto (default: deducida de --config o cwd)")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Recorder determinista de casos (training-data-services).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_rec = sub.add_parser("record", help="graba un caso como version nueva (nunca sobrescribe)")
    p_rec.add_argument("fichero", help="caso en JSON (el formato de case_schema.py)")
    p_rec.add_argument("--approved-by-human", action="store_true",
                       help="confirmacion HUMANA explicita para grabar un caso ya `approved` (Gold)")
    _comunes(p_rec)
    args = ap.parse_args(argv)
    try:
        config, raiz = _config_cli(args)
        if args.cmd == "record":
            caso = _leer_json(args.fichero)
            print(json.dumps(grabar(caso, config, raiz, approved_by_human=args.approved_by_human), ensure_ascii=False))
        return 0
    except _EntradaIlegible as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except Rechazo as e:
        print(f"rechazado: {e.mensaje}", file=sys.stderr)
        for err in e.errores:
            print(f"  {err['campo']}: {err['mensaje']}", file=sys.stderr)
        return 1
    except RedaccionNoDisponible as e:
        print(f"rechazado: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
