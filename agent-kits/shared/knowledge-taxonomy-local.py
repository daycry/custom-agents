"""Private local taxonomy rules shared by retrieval and full service validation.

No backend modules or URL/network libraries are loaded here. The full schema
wrapper supplies its existing backend validator and derived service defaults.
"""
import json
import os
import re
import sys

for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(HERE, "templates", "taxonomy.json")
PROJECT_TAXONOMY_REL = os.path.join(".claude", "knowledge-services", "taxonomy.json")
VERSIONES_SOPORTADAS = (1,)
ROUTING_VALORES = (True, False, "summary")
_FOLDER_UNIDAD_RE = re.compile(r"^[A-Za-z]:")
_SLUG_NO_ALNUM_RE = re.compile(r"[^a-z0-9]+")

# Respaldo embebido si `templates/taxonomy.json` no viaja con este fichero (instalación parcial
# o paquete portable "solo skills" — ver agent-kits/shared/README.md). El bloque de abajo (desde
# `"version": 1,` hasta el `]` del denylist) es COPIA LITERAL del contenido de
# `templates/taxonomy.json` (agent-kits/shared/copias.json, bloque `taxonomy_fallback`, ADR-016):
# la unica diferencia tolerada es `False` en vez de `false` (JSON no admite identificadores de
# Python), que la `sustitucion` del registro normaliza antes de comparar byte a byte. Ademas,
# test_knowledge_schema.py::test_default_fallback_coincide_con_el_template compara AMBOS como
# datos (no solo como texto), para que una divergencia de VALORES tambien de rojo.
_TAXONOMY_FALLBACK = { \
  "version": 1,
  "utility_scoring": False,
  "categories": [
    {
      "key": "DECISION",
      "folder": "adr",
      "min_evidence": "human_confirmed_rule",
      "routing": {"kwipu": False}
    },
    {
      "key": "PATTERN",
      "folder": "gotchas",
      "min_evidence": "multiple_validated_cases",
      "routing": {"kwipu": False}
    },
    {
      "key": "GOTCHA",
      "folder": "gotchas",
      "min_evidence": "validated_case",
      "routing": {"kwipu": False}
    },
    {
      "key": "LESSON",
      "folder": "lessons",
      "min_evidence": "single_case",
      "routing": {"kwipu": False}
    }
  ],
  "backends": {
    "kwipu": {
      "type": "markdown-export",
      "enabled": False,
      "config": {
        "export_dir": ".claude/knowledge-services/kwipu-export",
        "health": {"url": "http://127.0.0.1:8765/health", "timeout_ms": 800}
      }
    },
    "graphiti": {
      "type": "graphiti",
      "enabled": False,
      "config": {
        "mode": "shadow",
        "endpoint": "http://127.0.0.1:8001/mcp",
        "allow_remote": False,
        "provider": {"llm": "none"},
        "entity_map": {},
        "relations": [],
        "router": {"intents": {"temporal": False, "relacional": False, "evidencia": False}},
        "telemetria": False,
        "health": {"url": "http://127.0.0.1:8001/health", "timeout_ms": 3000},
        "timeout_ms": 3000,
        "concurrency": 1
      }
    }
  },
  "evidence_levels": [
    "observation",
    "single_case",
    "validated_case",
    "multiple_validated_cases",
    "human_confirmed_rule"
  ],
  "denylist": [
    "chain-of-thought",
    "conversacion cruda",
    "TODO:",
    "planes/progreso",
    "logs completos",
    "salidas enormes",
    "codigo duplicado",
    "errores triviales",
    "intentos sin aprendizaje",
    "hipotesis presentadas como hechos",
    "opiniones",
    "redundancias"
  ]
}


def _error(mensaje, fichero, campo):
    return {"mensaje": mensaje, "fichero": fichero, "campo": campo}


def _folder_seguro(folder):
    """True si `folder` es un nombre/ruta RELATIVA simple, sin forma de escapar de
    `docs/knowledge/approved/` cuando `knowledge-index.py` la una con `os.path.join` (gap 6,
    CWE-22): sin `..`, sin barra inicial (POSIX o Windows), sin unidad (`C:`) y sin
    contrabarra (separador de Windows; el contrato es siempre `/`, como el resto del repo)."""
    if not isinstance(folder, str) or not folder:
        return False
    if folder.startswith("/") or folder.startswith("\\"):
        return False
    if "\\" in folder:
        return False
    if _FOLDER_UNIDAD_RE.match(folder):
        return False
    partes = folder.split("/")
    return all(p not in ("", ".", "..") for p in partes)


def default_taxonomy(template_path=None):
    """La plantilla por defecto del plugin, leída del disco si está disponible; si no, el
    respaldo embebido (mismo contenido). Nunca lanza (gap 14: una plantilla con encoding
    corrupto/truncado no debe tumbar el CLI ni `cargar_taxonomia`, cae al respaldo igual que un
    fichero ilegible o JSON invalido)."""
    try:
        with open(template_path or TEMPLATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        # ValueError cubre json.JSONDecodeError y UnicodeDecodeError (ambas subclases).
        return json.loads(json.dumps(_TAXONOMY_FALLBACK))


def _slug_kebab(nombre):
    """kebab-case determinista y minimo (minusculas, alfanumericos separados por un solo `-`,
    sin guiones al borde). Cadena vacia si `nombre` no aporta ningun caracter alfanumerico."""
    if not nombre:
        return ""
    return _SLUG_NO_ALNUM_RE.sub("-", nombre.lower()).strip("-")


def _con_id_prefix_por_defecto(config, root):
    """Si `config` no declara `id_prefix`, lo rellena con el slug kebab-case del directorio del
    proyecto (`root`, design.md:57): el prefijo NUNCA es un valor fijo del plugin (gap 5) — si
    `root` no aporta un basename utilizable (`.`, `/`, ruta vacia), cae a `ca` como ultimo
    recurso documentado. No pisa un `id_prefix` explicito del proyecto.

    `root=None` usa el cwd real (gap 29), el mismo criterio que `cargar_taxonomia` ya aplica para
    localizar `taxonomy.json` (gap 12) — antes esta funcion trataba `None` como "sin raiz" y caia
    directo a `ca`, aunque `cargar_taxonomia(root=None)` SI mirase el cwd."""
    if not isinstance(config, dict) or "id_prefix" in config:
        return config
    base = os.path.basename(os.path.abspath(root if root is not None else "."))
    config["id_prefix"] = _slug_kebab(base) or "ca"
    return config


def validar(config, fichero="taxonomy.json", backend_validator=None):
    """Lista de errores `{mensaje, fichero, campo}`. [] si `config` cumple el contrato."""
    errores = []
    if not isinstance(config, dict):
        return [_error("el contenido no es un objeto JSON", fichero, "$")]

    version = config.get("version")
    if version is None:
        errores.append(_error("falta `version`", fichero, "version"))
    elif not isinstance(version, int) or isinstance(version, bool):
        errores.append(_error("`version` debe ser un entero", fichero, "version"))
    elif version not in VERSIONES_SOPORTADAS:
        errores.append(_error(
            f"`version` {version} no soportada (soportadas: {', '.join(map(str, VERSIONES_SOPORTADAS))})",
            fichero, "version"))

    if "utility_scoring" in config and not isinstance(config["utility_scoring"], bool):
        errores.append(_error("`utility_scoring` debe ser booleano", fichero, "utility_scoring"))

    if "id_prefix" in config and not isinstance(config["id_prefix"], str):
        errores.append(_error("`id_prefix` debe ser una cadena", fichero, "id_prefix"))

    for clave in ("evidence_levels", "denylist"):
        if clave in config:
            valor = config[clave]
            if not isinstance(valor, list) or not all(isinstance(x, str) for x in valor):
                errores.append(_error(f"`{clave}` debe ser una lista de cadenas", fichero, clave))
            elif clave == "evidence_levels" and not valor:
                # gap 13: el esquema exige minItems 1; `[]` pasaba en silencio y se sustituia
                # por el default del plugin mas abajo, sin avisar de que el proyecto la vacio.
                errores.append(_error("`evidence_levels` no puede estar vacía (minItems 1)", fichero, clave))

    evidence_levels_cfg = config.get("evidence_levels")
    if (isinstance(evidence_levels_cfg, list) and evidence_levels_cfg
            and all(isinstance(x, str) for x in evidence_levels_cfg)):
        evidence_levels = evidence_levels_cfg
    else:
        # gap 7: `evidence_levels` invalido (no lista, no-strings o vacio) ya quedo reportado
        # arriba; aqui se usa el default del plugin SOLO para poder seguir comprobando
        # `min_evidence` sin un `TypeError` (`5 in evidence_levels` con `evidence_levels=5`).
        evidence_levels = _TAXONOMY_FALLBACK["evidence_levels"]

    backends = config.get("backends", {})
    backend_ids = set()
    if "backends" in config:
        if not isinstance(backends, dict):
            errores.append(_error("`backends` debe ser un objeto {id: {type, ...}}", fichero, "backends"))
            backends = {}
        for bid, bcfg in backends.items():
            campo = f"backends.{bid}"
            if backend_validator is None:
                # Local retrieval needs declared IDs for routing references, not service settings.
                backend_ids.add(bid)
                continue
            if not isinstance(bcfg, dict):
                errores.append(_error(f"backend `{bid}` debe ser un objeto", fichero, campo))
                continue
            backend_ids.add(bid)
            if not bcfg.get("type"):
                errores.append(_error(f"backend `{bid}` no declara `type`", fichero, f"{campo}.type"))
            if "enabled" in bcfg and not isinstance(bcfg["enabled"], bool):
                errores.append(_error(f"backend `{bid}`: `enabled` debe ser booleano", fichero, f"{campo}.enabled"))
            if "config" in bcfg and not isinstance(bcfg["config"], dict):
                errores.append(_error(f"backend `{bid}`: `config` debe ser un objeto", fichero, f"{campo}.config"))
            elif backend_validator is not None:
                backend_validator(bcfg, campo, fichero, errores)


    categories = config.get("categories")
    if categories is None:
        errores.append(_error("falta `categories`", fichero, "categories"))
    elif not isinstance(categories, list) or not categories:
        errores.append(_error("`categories` debe ser una lista no vacía", fichero, "categories"))
    else:
        vistas = set()
        # gap 38 (fix4): dos `folder` que solo difieran en mayusculas/minusculas colapsan al MISMO
        # directorio fisico en un filesystem case-insensitive (NTFS/Windows por defecto) aunque
        # `knowledge-index.py` los trate como carpetas distintas — se detecta aqui, en la config,
        # en vez de dejar que el indice descubra el choque en tiempo de escaneo.
        folders_por_clave = {}
        for i, cat in enumerate(categories):
            campo = f"categories[{i}]"
            if not isinstance(cat, dict):
                errores.append(_error(f"{campo} debe ser un objeto", fichero, campo))
                continue
            key = cat.get("key")
            if not key or not isinstance(key, str):
                errores.append(_error(f"{campo} no declara `key`", fichero, f"{campo}.key"))
            elif key in vistas:
                errores.append(_error(f"`key` duplicada: `{key}`", fichero, f"{campo}.key"))
            else:
                vistas.add(key)
            folder = cat.get("folder")
            if not folder or not isinstance(folder, str):
                errores.append(_error(f"{campo} no declara `folder`", fichero, f"{campo}.folder"))
            elif not _folder_seguro(folder):
                # gap 6 (CWE-22): `folder` viaja tal cual hasta knowledge-index.py, que lo une a
                # `docs/knowledge/approved/`; sin esta puerta, "../candidates/pending" o una ruta
                # absoluta/con unidad Windows escapaban de `approved/` (path traversal por config).
                errores.append(_error(
                    f"{campo}.folder `{folder}` no es una ruta relativa segura "
                    "(sin `..`, sin `/` inicial, sin `\\` ni unidad de Windows)",
                    fichero, f"{campo}.folder"))
            else:
                clave = folder.casefold()
                if clave in folders_por_clave and folders_por_clave[clave] != folder:
                    errores.append(_error(
                        f"{campo}.folder `{folder}` colisiona con `{folders_por_clave[clave]}` "
                        "(difieren solo en mayusculas/minusculas; en un filesystem "
                        "case-insensitive como NTFS resuelven al mismo directorio)",
                        fichero, f"{campo}.folder"))
                else:
                    folders_por_clave.setdefault(clave, folder)
            # gap heredado (revisión Fase 2 intento 2, T-10): `min_evidence` presente pero de tipo
            # incorrecto (p. ej. un entero) disparaba DOS errores encadenados — "no declara" por el
            # `isinstance` y luego "no está en evidence_levels" porque el valor no-string tampoco
            # está en esa lista de strings. Un solo defecto de forma basta; el segundo chequeo (la
            # pertenencia a `evidence_levels`) solo tiene sentido si el valor YA es un string.
            min_evidence = cat.get("min_evidence")
            if not min_evidence or not isinstance(min_evidence, str):
                errores.append(_error(f"{campo} no declara `min_evidence`", fichero, f"{campo}.min_evidence"))
            elif min_evidence not in evidence_levels:
                errores.append(_error(
                    f"{campo}.min_evidence `{min_evidence}` no está en `evidence_levels`",
                    fichero, f"{campo}.min_evidence"))
            routing = cat.get("routing")
            if routing is not None:
                if not isinstance(routing, dict):
                    errores.append(_error(f"{campo}.routing debe ser un objeto", fichero, f"{campo}.routing"))
                else:
                    for bid, valor in routing.items():
                        campo_r = f"{campo}.routing.{bid}"
                        if bid not in backend_ids:
                            errores.append(_error(
                                f"`routing` cita el backend `{bid}`, no declarado en `backends` (fail-closed)",
                                fichero, campo_r))
                        if type(valor) is not bool and not (type(valor) is str and valor == "summary"):
                            errores.append(_error(
                                f"{campo_r} debe ser true, false o \"summary\"", fichero, campo_r))
            # Sin `routing` declarado: fail-closed, no es un error de esquema (CA-09), solo
            # significa que la categoría no exporta a ningún backend.

    return errores


def cargar_taxonomia(root=None, fichero=None, validator=None, defaults=None):
    """(config, origen, ruta_o_None, errores). `origen` = "proyecto" | "default".
    Si `fichero` se pasa explícito, se valida ese; si no, se busca
    `<root>/.claude/knowledge-services/taxonomy.json` — `root=None` (igual que el docstring
    siempre prometió) busca desde el cwd, no se salta la busqueda (gap 12: antes, `root=None`
    devolvia el default SIN mirar si el cwd tenia un `taxonomy.json` de proyecto). Sin fichero de
    proyecto → la plantilla por defecto (CA-01/CA-09), sin error. Con fichero de proyecto
    inválido → se devuelve igualmente (para que el llamador decida) junto con los errores. En
    ambos casos, si `config` no declara `id_prefix`, se rellena con el slug del `root` (gap 5); lo
    La derivación de defaults de servicio pertenece al wrapper completo `knowledge-schema.py`."""
    ruta = fichero or os.path.join(root if root is not None else ".", PROJECT_TAXONOMY_REL)
    if os.path.isfile(ruta):
        try:
            # gap 27: `utf-8-sig` tolera el BOM UTF-8 (VS Code/Notepad) sin rechazarlo como "JSON
            # ilegible"; `(OSError, ValueError)` cubre además `json.JSONDecodeError` y
            # `UnicodeDecodeError` (p. ej. `taxonomy.json` guardado en UTF-16) en vez de dejarlo
            # propagar como traceback crudo hasta `/doctor`.
            with open(ruta, "r", encoding="utf-8-sig") as f:
                config = json.load(f)
        except (OSError, ValueError) as e:
            return None, "proyecto", ruta, [_error(f"JSON ilegible: {type(e).__name__}: {e}", ruta, "$")]
        errores = (validator or validar)(config, ruta)
        _con_id_prefix_por_defecto(config, root)
        return config, "proyecto", ruta, errores
    config = (defaults or default_taxonomy)()
    _con_id_prefix_por_defecto(config, root)
    errores = []
    return config, "default", None, errores


def backend_ids_declarados(config):
    return set((config.get("backends") or {}).keys())


def categorias_por_backend(config, backend_id):
    """Categorías cuyo `routing[backend_id]` no es `false` (fail-closed por defecto: sin
    `routing` o sin la clave del backend, la categoría NO exporta)."""
    return [cat for cat, _valor in categorias_por_backend_con_valor(config, backend_id)]


def categorias_por_backend_con_valor(config, backend_id):
    """Como `categorias_por_backend`, pero devuelve pares `(categoria, valor)` — `valor` es el
    `true`/`"summary"` literal de `routing[backend_id]` (gap 2/10): sin esto, el consumidor (el
    adaptador `markdown-export` de T-08) no podia distinguir "entero" de "solo resumen" y
    `categorias_por_backend` los colapsaba a la misma lista."""
    out = []
    for cat in config.get("categories") or []:
        routing = cat.get("routing") or {}
        valor = routing.get(backend_id, False)
        if valor:
            out.append((cat, valor))
    return out


DOCUMENTAL_READ_LIMITS = {
    "timeout_ms": (5000, 30000),
    "max_request_bytes": (8192, 65536),
    "max_answer_chars": (4096, 65536),
    "max_source_nodes": (64, 1024),
    "max_response_bytes": (262144, 2097152),
    "max_snapshot_bytes": (2097152, 2097152),
}


def documental_read_options(config, fichero="taxonomy.json", campo="config"):
    """Validate opt-in documental limits and router without loading service code."""
    errors = []
    def error(path):
        errors.append(_error("opción de lectura documental inválida", fichero, campo + "." + path))
    if not isinstance(config, dict):
        error("read")
        return None, errors
    read = config.get("read", {})
    if not isinstance(read, dict):
        error("read")
        return None, errors
    for key in read:
        if key not in DOCUMENTAL_READ_LIMITS and key != "enabled":
            error("read")
    enabled = read.get("enabled", False)
    if type(enabled) is not bool:
        error("read.enabled")
    options = {"enabled": enabled}
    for key, (default, cap) in DOCUMENTAL_READ_LIMITS.items():
        value = read.get(key, default)
        if type(value) is not int or not 1 <= value <= cap:
            error("read." + key)
        options[key] = value
    router = config.get("router", {})
    if not isinstance(router, dict):
        error("router")
    else:
        if any(key not in ("intents", "default") for key in router):
            error("router")
        if "default" in router and not isinstance(router["default"], str):
            error("router.default")
        intents = router.get("intents", {})
        if not isinstance(intents, dict):
            error("router.intents")
        elif any(not isinstance(key, str) or re.fullmatch(r"[a-z][a-z0-9_-]*", key) is None
                 or type(value) is not bool for key, value in intents.items()):
            error("router.intents")
    return (None if errors else options), errors


def entradas_enrutadas(config, backend_id, indice):
    """Select already-validated approved records without files, adapters or effects.

    Publication and explicit retrieval use the same routing and summary modes.
    Returns entries, errors and IDs excluded by routing, in deterministic order.
    """
    errores = []
    for index, category in enumerate(config.get("categories") or []):
        value = (category.get("routing") or {}).get(backend_id, False)
        if type(value) is not bool and not (type(value) is str and value == "summary"):
            errores.append(_error("routing debe ser true, false o summary", "taxonomy.json",
                                  f"categories[{index}].routing.{backend_id}"))
    if errores:
        return [], errores, sorted(indice)
    valores = {cat.get("key"): valor
               for cat, valor in categorias_por_backend_con_valor(config, backend_id)}
    entradas, omitidas = [], []
    for identifier in sorted(indice):
        meta = indice[identifier]
        valor = valores.get(meta.get("category"), False)
        if not valor:
            omitidas.append(identifier)
            continue
        entradas.append({
            "id": identifier, "version": meta["version"], "folder": meta["folder"],
            "enlaces": meta["enlaces"], "category": meta.get("category"),
            "evidencia": meta.get("evidencia"), "fuentes": meta.get("fuentes") or [],
            "tags": meta.get("tags") or [], "modo": "resumen" if valor == "summary" else "completo",
            "cuerpo": meta.get("cuerpo") or "", "resumen": meta.get("resumen"), "ruta": meta["ruta"],
        })
    return entradas, [], omitidas


