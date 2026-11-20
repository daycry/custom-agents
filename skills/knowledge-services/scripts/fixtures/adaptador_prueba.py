"""Adaptador de PRUEBA del marco `knowledge-services` (plugin-audit-2 T-10).

El plugin no incluye adaptadores de backend. Este fichero vive en `scripts/fixtures/` y los tests
lo cargan por el parametro `directorios` de `backends/__init__.py::cargar_adaptador` (o por
`knowledge-sync.py --backends-dir`), con `type: "adaptador-prueba"`; nunca desde `backends/`.

Implementa las 6 funciones del contrato sin red: publica en una carpeta (`cfg["dir"]`, relativa a
`cfg["_root"]`) un `<id>.md` por entrada y un `manifest.json`, con un diario `manifest.pending.json`
que hace segura la reanudacion tras un fallo a mitad. Es determinista: mismas `entries`, mismo `ops`.
Nunca toca ficheros ajenos a su manifiesto, y CONTIENE toda ruta: `dir` debe quedar dentro de `_root` y
toda ruta que salga del manifiesto (un fichero del disco, no de confianza) o de un `id` debe quedar
dentro de `dir` (realpath + commonpath); lo que se sale se ignora o se rechaza, nunca se lee, escribe
ni borra (CWE-22/73). Un adaptador propio debe copiar esta contencion.
"""
import hashlib
import json
import os
import sys
import tempfile

MANIFEST = "manifest.json"
PENDING = "manifest.pending.json"
REMEDIO = "volver a ejecutar knowledge-sync (publicacion de prueba)"


_BS = chr(92)                              # barra invertida
_EXT = _BS * 2 + "?" + _BS                   # prefijo extendido de Windows


def _real(ruta):
    """`realpath` sin el prefijo extendido de Windows (barra doble, `?`, barra), que rompe `commonpath`."""
    r = os.path.realpath(ruta)
    if r.startswith(_EXT) and not r.upper().startswith(_EXT + "UNC" + _BS):
        r = r[4:]
    return r


def _aviso(texto):
    sys.stderr.write("adaptador-prueba: %s\n" % texto)


def _escribir_texto(destino, texto):
    """Escribe `destino` sin seguir enlaces: temporal con nombre ALEATORIO y creacion exclusiva
    (`mkstemp`; un `<destino>.tmp` preexistente, aunque sea un enlace, nunca se usa), y rechaza un
    destino que sea enlace simbolico o tenga varios nombres duros (CWE-59/73)."""
    if os.path.islink(destino) or (os.path.isfile(destino) and os.stat(destino).st_nlink > 1):
        raise ValueError("destino con enlaces, no se sobrescribe: %s" % os.path.basename(destino))
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(destino), prefix=".tmp-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(texto)
        os.replace(tmp, destino)
    except BaseException:
        if os.path.exists(tmp):
            os.remove(tmp)
        raise


def _dentro(raiz, ruta):
    """`True` si `ruta` (ya resuelta) es `raiz` o cuelga de ella."""
    try:
        return os.path.commonpath([raiz, ruta]) == raiz
    except ValueError:                       # otra unidad (Windows) o mezcla absoluta/relativa
        return False


def _dir(cfg):
    base = cfg.get("dir")
    if not isinstance(base, str) or not base.strip():
        raise ValueError("`dir` obligatorio en la config del adaptador de prueba")
    raiz = _real(cfg.get("_root") or ".")
    carpeta = _real(os.path.join(raiz, base))     # una ruta absoluta sustituye a `raiz`
    if not _dentro(raiz, carpeta):
        raise ValueError("`dir` debe quedar dentro de la raiz del proyecto")
    return carpeta


def _ruta_en(d, relativa):
    """Ruta resuelta de `relativa` dentro de `d`, o `None` si se sale (o no es texto)."""
    if not isinstance(relativa, str) or not relativa:
        return None
    ruta = _real(os.path.join(d, relativa))
    return ruta if ruta != d and _dentro(d, ruta) else None


def _ruta_de_id(d, kid):
    ruta = _ruta_en(d, "%s.md" % kid)
    if ruta is None or os.path.dirname(ruta) != d:
        raise ValueError("id no admitido como nombre de fichero: %r" % (kid,))
    return ruta


def _entrada_valida(d, kid, meta):
    """`True` si la entrada del manifiesto (dato del disco) apunta a un fichero DENTRO de `d`."""
    try:
        _ruta_de_id(d, kid)
    except ValueError:
        return False
    return _ruta_en(d, meta.get("ruta") if isinstance(meta, dict) else None) is not None


def _leer(ruta):
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            datos = json.load(f)
    except (OSError, ValueError):
        return None
    return datos if isinstance(datos, dict) and isinstance(datos.get("entries"), dict) else None


def _manifest(d, incluir_pending=True):
    previo = _leer(os.path.join(d, PENDING)) if incluir_pending else None
    return previo or _leer(os.path.join(d, MANIFEST)) or {"entries": {}}


def _contenido(op_o_entry):
    return f"# {op_o_entry['id']}\nversion: {op_o_entry.get('version')}\n\n{op_o_entry.get('cuerpo', '')}"


def _hash(e):
    return hashlib.sha256(_contenido(e).encode("utf-8")).hexdigest()


def _escribir_json(ruta, datos):
    _escribir_texto(ruta, json.dumps(datos, sort_keys=True))


def health(cfg):
    try:
        d = _dir(cfg)
    except ValueError as e:
        return {"estado": "error", "detalle": str(e)}
    return {"estado": cfg.get("estado_salud", "sano"), "detalle": f"carpeta {os.path.basename(d)}"}


def _hash_en_disco(ruta):
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return hashlib.sha256(f.read().encode("utf-8")).hexdigest()
    except OSError:
        return None


def plan(entries, cfg):
    """Compara contra el CONTENIDO en disco (no contra el manifiesto): un diario pendiente que
    lista el hash nuevo no hace pasar por publicado un fichero que sigue con el contenido viejo."""
    d = _dir(cfg)
    previos = set()
    for nombre in (MANIFEST, PENDING):
        for kid, meta in (_leer(os.path.join(d, nombre)) or {"entries": {}})["entries"].items():
            ruta = _ruta_en(d, meta.get("ruta") if isinstance(meta, dict) else None)
            try:
                _ruta_de_id(d, kid)
            except ValueError:
                ruta = None
            if ruta is None:
                _aviso("entrada %r del manifiesto fuera de la carpeta de publicacion: ignorada" % (kid,))
            else:
                previos.add(kid)
    ops, vistos = [], set()
    for e in sorted(entries, key=lambda x: x["id"]):
        vistos.add(e["id"])
        h = _hash(e)
        if _hash_en_disco(_ruta_de_id(d, e["id"])) == h:
            continue
        ops.append({"accion": "upsert", "id": e["id"], "version": e.get("version"),
                    "cuerpo": e.get("cuerpo", ""), "hash": h})
    for antiguo in sorted(previos - vistos):
        ops.append({"accion": "revoke", "id": antiguo})
    return ops


def apply(ops, cfg):
    d = _dir(cfg)
    os.makedirs(d, exist_ok=True)
    objetivo = {"entries": {k: m for k, m in _manifest(d)["entries"].items()
                            if _entrada_valida(d, k, m)}}   # las hostiles no se arrastran
    for op in ops:
        _ruta_de_id(d, op["id"])             # rechaza TODO el lote antes de escribir nada
    for op in ops:
        if op["accion"] == "upsert":
            objetivo["entries"][op["id"]] = {"hash": op["hash"], "ruta": op["id"] + ".md"}
        else:
            objetivo["entries"].pop(op["id"], None)
    _escribir_json(os.path.join(d, PENDING), objetivo)  # diario: lo que se PRETENDE publicar
    for op in ops:
        destino = _ruta_de_id(d, op["id"])
        if op["accion"] == "upsert":
            _escribir_texto(destino, _contenido(op))
        elif os.path.isfile(destino):
            os.remove(destino)
    os.replace(os.path.join(d, PENDING), os.path.join(d, MANIFEST))
    return {"aplicados": len(ops), "entradas": len(objetivo["entries"])}


def verify(cfg):
    d = _dir(cfg)
    manifest = _leer(os.path.join(d, MANIFEST))
    if manifest is None:
        return {"ok": False, "estado": "incompleto", "desfase": [], "no_verificado": 0,
                "aviso": "sin publicacion local: nada que verificar", "remedio": REMEDIO}
    desfase = []
    for kid, meta in sorted(manifest["entries"].items()):
        ruta = _ruta_en(d, meta.get("ruta") if isinstance(meta, dict) else None)
        if ruta is None:
            desfase.append({"knowledge_id": kid, "motivo": "ruta fuera de la carpeta de publicacion"})
            continue
        actual = _hash_en_disco(ruta)
        if actual is None:
            desfase.append({"knowledge_id": kid, "motivo": "falta el fichero"})
            continue
        if actual != meta.get("hash"):
            desfase.append({"knowledge_id": kid, "motivo": "contenido distinto del manifiesto"})
    return {"ok": not desfase, "estado": "ok" if not desfase else "desfase", "desfase": desfase,
            "remedio": REMEDIO if desfase else None}


def rebuild(entries, cfg):
    d = _dir(cfg)
    for meta in _manifest(d, incluir_pending=False)["entries"].values():
        ruta = _ruta_en(d, meta.get("ruta") if isinstance(meta, dict) else None)
        if ruta is not None and os.path.isfile(ruta):      # fuera de `dir`: se ignora
            os.remove(ruta)
    for nombre in (MANIFEST, PENDING):
        if os.path.isfile(os.path.join(d, nombre)):
            os.remove(os.path.join(d, nombre))
    return apply(plan(entries, cfg), cfg)


def revoke(knowledge_id, cfg):
    d = _dir(cfg)
    manifest = _manifest(d, incluir_pending=False)
    meta = manifest["entries"].pop(knowledge_id, None)
    if meta is None:
        return {"revocado": False}
    ruta = _ruta_en(d, meta.get("ruta") if isinstance(meta, dict) else None)
    if ruta is not None and os.path.isfile(ruta):          # fuera de `dir`: se ignora
        os.remove(ruta)
    _escribir_json(os.path.join(d, MANIFEST), manifest)
    resultado = {"revocado": True}
    if ruta is None:
        resultado["aviso"] = "la ruta del manifiesto sale de la carpeta de publicacion: ignorada"
    return resultado
