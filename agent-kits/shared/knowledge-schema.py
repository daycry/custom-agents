#!/usr/bin/env python3
"""
knowledge-schema.py — validador stdlib de `.claude/knowledge-services/taxonomy.json`
(ADR-018, `knowledge-services` T-01). Sin dependencias (mismo criterio que `outbox.py`/`redact.py`):
las reglas están escritas a mano en Python, en el MISMO contrato que documenta
`agent-kits/shared/schemas/taxonomy.schema.json` (la referencia legible; este script es quien
las hace cumplir).

Contrato de `taxonomy.json` (version 1):
  version (int, obligatorio) · id_prefix (str) · utility_scoring (bool, default False)
  categories (lista, obligatoria): {key, folder, min_evidence, routing?}
  backends (dict opcional): {<id>: {type, enabled?, config?}}
  routing (por categoría, dentro de cada entrada de `categories`): {<backend_id>: true|false|"summary"}
    — solo puede citar ids declarados en `backends`; un id no declarado o una categoría SIN
    `routing` es fail-closed: no exporta a ningún backend (CA-09, CA-11).
  evidence_levels (lista opcional de str) · denylist (lista opcional de str)

Sin `taxonomy.json` en el proyecto, `cargar_taxonomia()` devuelve la plantilla por defecto del
plugin (`agent-kits/shared/templates/taxonomy.json`, embebida como respaldo si el fichero no
viaja) para que el plugin siga funcionando sin configurar nada (CA-01, CA-09).

Cada error de `validar()` es un dict `{mensaje, fichero, campo}` — el campo nombra la clave
concreta (p. ej. `categories[2].routing.<backend>`) para que `/doctor` señale fichero y campo.
Las reglas locales y sus atributos de compatibilidad se delegan mediante `__getattr__` al único
dueño `knowledge-taxonomy-local.py`; no se duplica el literal de respaldo. Su ausencia es un error
explícito (API estructurada o excepción tipada al pedir defaults/atributos), nunca defaults nuevos.

Uso:
  knowledge-schema.py <ruta-a-taxonomy.json>   # valida un fichero concreto; exit 0/1
  knowledge-schema.py --default                # valida (e imprime) la plantilla por defecto
  knowledge-schema.py --setup-id-prefix [--root R] [--id-prefix X] [--aplicar]  # /setup: id_prefix (JSON); exit 0/2
Exit codes: 0 válido · 1 con errores (se listan en stdout) · 2 uso/JSON ilegible.
"""
import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile

# Consola no UTF-8 (Windows cp1252) o tuberías: reconfigurar ANTES de leer/imprimir (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(HERE, "templates", "taxonomy.json")
PROJECT_TAXONOMY_REL = os.path.join(".claude", "knowledge-services", "taxonomy.json")

# Pure sibling: mandatory local rules, with explicit failure for partial installations.
_LOCAL_PATH = os.path.join(HERE, "knowledge-taxonomy-local.py")
try:
    _spec = importlib.util.spec_from_file_location("knowledge_taxonomy_local", _LOCAL_PATH)
    _LOCAL = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_LOCAL)
    _LOCAL_ERROR = None
except Exception as exc:
    _LOCAL = None
    _LOCAL_ERROR = f"no se pudo cargar knowledge-taxonomy-local.py: {type(exc).__name__}: {exc}"[:600]


class KnowledgeLocalNoDisponible(Exception):
    """Mandatory local rules unavailable; never silently replace validation or defaults."""


def __getattr__(name):
    """Forward compatibility attributes to the sole local owner, without copied bindings/data."""
    if name in {"_TAXONOMY_FALLBACK", "_folder_seguro", "_slug_kebab",
                "_con_id_prefix_por_defecto", "backend_ids_declarados",
                "categorias_por_backend", "categorias_por_backend_con_valor", "entradas_enrutadas"}:
        if _LOCAL is None:
            raise KnowledgeLocalNoDisponible(_LOCAL_ERROR)
        return getattr(_LOCAL, name)
    raise AttributeError(name)

VERSIONES_SOPORTADAS = (1,)
ROUTING_VALORES = (True, False, "summary")

def _error(mensaje, fichero, campo):
    return {"mensaje": mensaje, "fichero": fichero, "campo": campo}


_FOLDER_UNIDAD_RE = re.compile(r"^[A-Za-z]:")




def default_taxonomy():
    if _LOCAL is None:
        raise KnowledgeLocalNoDisponible(_LOCAL_ERROR)
    return _LOCAL.default_taxonomy(TEMPLATE_PATH)


_SLUG_NO_ALNUM_RE = re.compile(r"[^a-z0-9]+")




def validar(config, fichero="taxonomy.json"):
    if _LOCAL is None:
        return [_error(_LOCAL_ERROR, _LOCAL_PATH, "$")]
    return _LOCAL.validar(config, fichero, backend_validator=_validar_backend_declarado)


def _validar_backend_declarado(bcfg, campo, fichero, errores):
    """Sin reglas por `type`: el plugin no incluye adaptadores (T-10), así que la validación de
    `backends.<id>` es la genérica de `knowledge-taxonomy-local.py` (objeto con `type`, `enabled`
    booleano y `config` objeto). Un adaptador que se enchufe valida su `config` por su cuenta."""
    return None


def cargar_taxonomia(root=None, fichero=None):
    if _LOCAL is None:
        return None, None, fichero, [_error(_LOCAL_ERROR, _LOCAL_PATH, "$")]
    config, origen, ruta, errores = _LOCAL.cargar_taxonomia(
        root, fichero, validator=validar, defaults=default_taxonomy)
    return config, origen, ruta, errores


# ------------------------------------------------------------------ id_prefix elegible (setup-statusline-polish T-10/T-11)
# `/setup` propone el `id_prefix` (slug de la carpeta), lo valida y lo guarda.
ID_PREFIX_RE = re.compile(r"^[a-z][a-z0-9-]*$")      # fix2 #24: empieza por letra (regla de #2)
ID_PREFIX_MAX = 64


# fix1 #2: el `id_prefix` propuesto tiene que ser texto para YAML 1.1 (empieza por letra, no
# reservada): un backend externo puede escribirlo SIN comillas en su propia configuración.
_YAML_RESERVADAS = frozenset(("y", "n", "yes", "no", "on", "off", "true", "false", "null", "~"))


def id_prefix_valido(valor):
    """`^[a-z][a-z0-9-]*$`, hasta 64 caracteres y no reservado en YAML 1.1 (fix2 #24, alineada con #2)."""
    return (isinstance(valor, str) and len(valor) <= ID_PREFIX_MAX
            and bool(ID_PREFIX_RE.match(valor)) and valor.casefold() not in _YAML_RESERVADAS)


def _texto_en_yaml(valor):
    return bool(valor) and valor[0].isalpha() and valor.casefold() not in _YAML_RESERVADAS


def proponer_id_prefix(root=None):
    """Slug kebab-case de la carpeta del proyecto, acotado a 64. Nunca propone un valor invalido
    ni compartido (fix1 #2/#3): si el slug no es texto para YAML (`2048`, `yes`…) antepone `p-`;
    si la carpeta no aporta un slug ASCII (`知識`, `проект`, `---`), `p-<8 hex del sha256 de la
    ruta absoluta normalizada>`: determinista y distinto por proyecto (antes caia a `ca` y dos
    proyectos asi compartian el mismo prefijo)."""
    ruta = os.path.abspath(root if root is not None else ".")
    slug = _LOCAL._slug_kebab(os.path.basename(ruta))[:ID_PREFIX_MAX].strip("-")
    if not slug:
        normalizada = os.path.normcase(os.path.realpath(ruta))
        return "p-" + hashlib.sha256(normalizada.encode("utf-8", "surrogatepass")).hexdigest()[:8]
    if not _texto_en_yaml(slug):
        slug = ("p-" + slug)[:ID_PREFIX_MAX].strip("-")
    return slug


def _leer_json_dict(ruta):
    """dict del JSON en `ruta`, o `None` (ausente, ilegible o de otra forma). Nunca lanza."""
    try:
        with open(ruta, "r", encoding="utf-8-sig") as f:
            datos = json.load(f)
    except (OSError, ValueError):
        return None
    return datos if isinstance(datos, dict) else None


def preparar_id_prefix(root=None, id_prefix=None, aplicar=False):
    """Propone, valida y (con `aplicar`) guarda el `id_prefix` en `taxonomy.json`. Devuelve un dict
    `{ok, propuesta, id_prefix, avisos, escrito[, error]}`.
    Los avisos NUNCA bloquean. Un `id_prefix` inválido, o un `taxonomy.json` ilegible/inválido, no
    escribe nada. Sin `taxonomy.json`, `aplicar` lo crea desde la plantilla."""
    root = os.path.abspath(root if root is not None else ".")
    ruta = os.path.join(root, PROJECT_TAXONOMY_REL)
    propuesta = proponer_id_prefix(root)
    elegido = propuesta if id_prefix is None else id_prefix
    salida = {"ok": False, "propuesta": propuesta, "id_prefix": elegido, "avisos": [],
              "escrito": False}
    if not id_prefix_valido(elegido):
        salida["error"] = (f"`id_prefix` inválido ({elegido!r}): debe cumplir "
                           f"{ID_PREFIX_RE.pattern}, tener hasta {ID_PREFIX_MAX} caracteres y no "
                           f"ser una palabra reservada de YAML ({'/'.join(sorted(_YAML_RESERVADAS))})")
        return salida
    existe = os.path.isfile(ruta)
    raw = _leer_json_dict(ruta) if existe else default_taxonomy()
    if raw is None:
        salida["error"] = f"`{PROJECT_TAXONOMY_REL}` ilegible: no se modifica"
        return salida
    if existe and validar(raw, ruta):
        salida["error"] = f"`{PROJECT_TAXONOMY_REL}` no es válido: corrígelo antes (no se modifica)"
        return salida
    salida["ok"] = True
    if aplicar:
        raw["id_prefix"] = elegido
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        tmp = None
        try:
            # fix1 #18: temporal con nombre aleatorio y `O_EXCL` (`mkstemp`) en el mismo
            # directorio: ni predecible ni sigue un enlace plantado
            fd, tmp = tempfile.mkstemp(prefix=".taxonomy.", suffix=".tmp",
                                       dir=os.path.dirname(ruta))
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(raw, f, ensure_ascii=False, indent=2)
                f.write("\n")
            # `mkstemp` crea con 0600: se conservan los permisos del fichero que se reemplaza
            os.chmod(tmp, (os.stat(ruta).st_mode & 0o777) if existe else 0o644)
            os.replace(tmp, ruta)
        except OSError as e:
            if tmp is not None:
                try:
                    os.remove(tmp)
                except OSError:
                    pass
            salida.update(ok=False, error=f"no se pudo escribir `{PROJECT_TAXONOMY_REL}`: "
                                          f"{type(e).__name__}")
            return salida
        salida["escrito"] = True
    return salida






def _construir_parser():
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("ruta", nargs="?", help="ruta a un taxonomy.json a validar")
    ap.add_argument("--default", action="store_true", help="valida la plantilla por defecto del plugin")
    ap.add_argument("--setup-id-prefix", action="store_true", dest="setup_id_prefix",
                    help="propone/valida el id_prefix (JSON en stdout); con --aplicar lo guarda")
    ap.add_argument("--id-prefix", dest="id_prefix", default=None, help="id_prefix elegido")
    ap.add_argument("--aplicar", action="store_true", help="escribe taxonomy.json (con --setup-id-prefix)")
    ap.add_argument("--root", default=".", help="raiz del proyecto (con --setup-id-prefix)")
    return ap


def main(argv=None):
    args = _construir_parser().parse_args(argv)
    if _LOCAL is None:
        print(f"knowledge-schema: {_LOCAL_ERROR}", file=sys.stderr)
        return 1
    if args.setup_id_prefix:
        r = preparar_id_prefix(args.root, args.id_prefix, args.aplicar)
        print(json.dumps(r, ensure_ascii=False, indent=2))
        return 0 if r["ok"] else 2
    if args.default:
        config = default_taxonomy()
        errores = validar(config, TEMPLATE_PATH)
    elif args.ruta:
        # gap 39 (fix4): el CLI reutiliza `cargar_taxonomia(fichero=...)` en vez de tener su
        # propio `open()`/`json.load` duplicado — antes ese segundo lector abria con
        # `encoding="utf-8"` (sin `-sig`) mientras `cargar_taxonomia` ya toleraba el BOM desde el
        # gap 27, asi que el MISMO `taxonomy.json` con BOM UTF-8 pasaba por un lector y fallaba
        # por el otro segun se invocara como fichero de proyecto o por ruta explicita del CLI. Con
        # un unico lector no hay forma de que diverjan. `os.path.isfile` cubre inexistente Y
        # directorio (gap 15, TOCTOU parcial: sigue habiendo una ventana entre el check y la
        # lectura, pero `cargar_taxonomia` ya captura `OSError` alrededor del `open()`).
        if not os.path.isfile(args.ruta):
            print(f"knowledge-schema: no existe `{args.ruta}`", file=sys.stderr)
            return 2
        config, _origen, _ruta, errores = cargar_taxonomia(fichero=args.ruta)
        if config is None:
            print(f"knowledge-schema: {errores[0]['mensaje']} en `{args.ruta}`", file=sys.stderr)
            return 2
    else:
        print("knowledge-schema: falta la ruta del fichero (o usa --default)", file=sys.stderr)
        return 2

    if not errores:
        print("taxonomy.json válido")
        return 0
    for e in errores:
        print(f"{e['fichero']}: {e['campo']}: {e['mensaje']}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
