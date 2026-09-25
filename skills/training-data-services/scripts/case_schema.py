#!/usr/bin/env python3
"""
case_schema.py — validador stdlib de la config `.claude/knowledge-services/training.json` y del
esquema de un CASO del case store (training-data-services T-01, design.md O1). Sin dependencias:
las reglas estan escritas a mano (mismo criterio que `agent-kits/shared/knowledge-schema.py`).

El plugin valida FORMA, nunca dominio (CA-04): `metrics` es un objeto JSON opaco calculado por el
proyecto; `context`/`constraints` tienen esquema libre salvo la lista opcional `context.refs`.

Contrato de `training.json` (version 1) — opt-in: sin fichero, la capacidad no existe (CA-01):
  version (int, obligatorio, 1) · enabled (bool, default false)
  root (str, obligatorio si enabled): raiz del case store, relativa a la raiz del proyecto o
       absoluta (sin `~`: no se expande); la elige el proyecto (el plugin no impone nombre) y NUNCA
       dentro de `<proyecto>/docs/knowledge/` (ADR-019), resuelto con realpath y sin distinguir
       mayusculas
  id_prefix (str slug, obligatorio si enabled): prefijo de `case_id` (`<id_prefix>-<family>.<variant>`)
  ids (obj opcional): family_pattern · variant_pattern (regex; default `^[a-z0-9][a-z0-9_-]*$`,
       sin puntos: el punto separa familia y variante) · version_width (int 1..6, default 3 -> v001)
  bridge_to_curator (bool, default false): un caso Gold PUEDE proponerse como candidato a
       `knowledge-curator` (nunca se aprueba solo, CA-05)
  $comment (str opcional): comentario libre; cualquier otra clave se rechaza (erratas visibles).

Contrato de un caso (lo que el recorder reparte en metadata/request/context/... de design.md):
  case_id · version (int >= 1) · family · variant       obligatorios
  request (str|obj no vacio, LITERAL)                     obligatorio
  trajectory (lista no vacia de turnos chat/SFT)          obligatorio
      turno: role in system|user|assistant|tool · content (str) · tool_calls [{name, arguments}]
      · name (obligatorio en `tool`) · ts; NUNCA chain-of-thought (claves que empiezan por
      reasoning/thinking/thought/chain_of_thought/scratchpad, sin distinguir mayusculas, a
      cualquier profundidad del turno; exentos SOLO dentro de `tool_calls[].arguments` los
      parametros de proveedor `CLAVES_PARAMETRO_PROVEEDOR`; > 50 niveles de anidamiento se
      rechaza); family/variant sin separadores, `..`, `.`, `:`, controles, espacio final ni
      nombres reservados de Windows
  validation {status, approved_by_human, approved_at?, reviewer_note?}   obligatorio
      status in pending|approved|needs_changes|rejected; approved <=> approved_by_human true
  outcome in success|failure|corrected (obligatorio); corrected exige, y solo corrected admite,
      supersedes_case = "<case_id>@v<NNN>" canonico (digitos ASCII, relleno a version_width, >= 1):
      mismo case_id, version anterior (par fallo -> correccion, CA-12)
  context (str|obj opcional; `refs`: [{"ref": "<fichero:linea|nodo>", "kind": "..."}] opcional)
  constraints (obj opcional) · metrics (obj opcional, opaco) · created_at (str opcional)
  artifacts (lista opcional de {path, hash "<algo>:<hex>", kind}; nunca contenido inline)

Mapeo DECLARADO de vocabularios externos de outcome (`OUTCOME_MAPEO`), sin ampliar el cerrado:
  graphify (`save-result`):  useful -> success · dead_end -> failure · corrected -> corrected

Cada error es `{campo, mensaje}` (el campo nombra la clave concreta, p. ej. `trajectory[2].role`).

Uso:
  case_schema.py config <training.json> [--project-root <dir>]   # exit 0 valido · 1 errores de
  case_schema.py case <caso.json> [--config <training.json>]       #   validacion · 2 uso/JSON ilegible
  (un valor de tipo inesperado es SIEMPRE un error de validacion `{campo, mensaje}` -> exit 1)
"""
import argparse
import json
import os
import re
import sys

# Consola no UTF-8 (Windows cp1252) o tuberias: reconfigurar ANTES de leer/imprimir (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leido o None (capsys, pythonw)

CONFIG_REL = os.path.join(".claude", "knowledge-services", "training.json")
VERSIONES_SOPORTADAS = (1,)

VALIDATION_STATUS = ("pending", "approved", "needs_changes", "rejected")
OUTCOMES = ("success", "failure", "corrected")
OUTCOME_MAPEO = {
    # vocabulario de `graphify save-result` (futura fuente de casos) -> vocabulario cerrado
    "graphify": {"useful": "success", "dead_end": "failure", "corrected": "corrected"},
}
ROLES = ("system", "user", "assistant", "tool")
# Prefijos (comparacion case-insensitive, `-` == `_`) de claves de chain-of-thought: cubren
# `reasoning_content`, `reasoning_details`, `thoughts`, `Thinking`... y se buscan en TODO el turno
# (recursivo, incluidos `tool_calls[].arguments`), no solo en su primer nivel (fix1, gap #6).
CLAVES_COT = ("reasoning", "thinking", "thought", "chain_of_thought", "scratchpad")
# Lista blanca DECLARADA (fix2, gap #22): parametros de proveedor que empiezan por un prefijo de
# CoT pero no son razonamiento. Exentos SOLO como claves dentro de `tool_calls[].arguments` (a
# cualquier profundidad); su valor se sigue recorriendo. Fuera de `arguments` siguen prohibidos.
CLAVES_PARAMETRO_PROVEEDOR = ("reasoning_effort", "thinking_budget", "reasoning_level")
PROFUNDIDAD_MAX = 50   # mas alla, el turno se rechaza (fix2, gap #21: fail closed, no fail open)
# Nombres reservados de Windows (con o sin extension): no pueden ser `family`/`variant` (gap #20).
NOMBRES_RESERVADOS = frozenset(["con", "prn", "aux", "nul"] + [f"com{i}" for i in range(1, 10)]
                               + [f"lpt{i}" for i in range(1, 10)])
PREFIJOS_EXTENDIDOS = ("\\\\?\\UNC\\", "//?/UNC/", "\\\\?\\", "//?/", "\\\\.\\", "//./")
CLAVES_INLINE = ("content", "data", "bytes", "base64", "blob")

# Todos los patrones se evaluan con `re.fullmatch` (fix1, gap #4): con fullmatch, `$` ya no acepta
# un `\n` final y un patron del proyecto sin anclas no casa solo un prefijo.
PATRON_ID_DEFECTO = r"^[a-z0-9][a-z0-9_-]*$"
PATRON_PREFIJO = re.compile(r"[a-z0-9][a-z0-9-]*")
PATRON_HASH = re.compile(r"[a-z0-9]+:[0-9a-fA-F]+")
PATRON_REFERENCIA = re.compile(r"(\S+)@v([0-9]+)", re.ASCII)   # forma canonica: ver _validar_supersedes
VERSION_WIDTH_DEFECTO = 3
CLAVES_CONFIG = ("version", "enabled", "root", "id_prefix", "ids", "bridge_to_curator", "$comment")
CLAVES_IDS = ("family_pattern", "variant_pattern", "version_width")
ERRORES_REGEX = (re.error, OverflowError, RecursionError, MemoryError)


def _err(campo, mensaje):
    return {"campo": campo, "mensaje": mensaje}


def _componente_inseguro(v):
    """Motivo por el que `v` no puede ser un componente de ruta del case store (`family`,
    `variant`), o None. Independiente del patron del proyecto (CWE-22, gaps #4 y #20): el
    directorio es `<family>.<variant>`, asi que el punto es el separador reservado."""
    if "/" in v or "\\" in v:
        return "no puede contener separadores de ruta"
    if ".." in v:
        return "no puede contener `..`"
    if any(ord(c) < 32 or ord(c) == 127 for c in v):
        return "no puede contener caracteres de control"
    if "." in v:
        return "no puede contener `.` (separa family y variant en case_id y directorio)"
    if ":" in v:
        return "no puede contener `:` (flujo alternativo NTFS / unidad)"
    if v != v.rstrip(" "):
        return "no puede acabar en espacio (Windows lo recorta: colision de directorios)"
    if v.casefold() in NOMBRES_RESERVADOS:
        return "es un nombre reservado de Windows (CON, PRN, AUX, NUL, COM1-9, LPT1-9)"
    return None


def _casa(patron, valor):
    """`re.fullmatch` que nunca lanza: un patron roto (no validado) cuenta como no casar."""
    try:
        return re.fullmatch(patron, valor) is not None
    except ERRORES_REGEX:
        return False


def _canon(ruta):
    """Ruta comparable: absoluta, sin `..`, enlaces resueltos y SIN distinguir mayusculas (en
    Windows/macOS `Docs/Knowledge` es el mismo directorio; en Linux se rechaza igual: la regla
    peca de estricta, nunca de laxa)."""
    return os.path.normcase(_sin_prefijo_extendido(os.path.realpath(_sin_prefijo_extendido(ruta)))).casefold()


def _sin_prefijo_extendido(ruta):
    """Quita el prefijo de ruta extendida/dispositivo de Windows (`\\\\?\\`, `\\\\?\\UNC\\`,
    `\\\\.\\` y sus formas con `/`): `realpath` lo conserva y esquivaria la comparacion (gap #20)."""
    for p in PREFIJOS_EXTENDIDOS:
        if ruta[: len(p)].upper() == p.upper():
            resto = ruta[len(p):]
            return ("\\\\" + resto) if "UNC" in p.upper() else resto
    return ruta


def _root_en_docs_knowledge(root, raiz_proyecto):
    """True si `root` (relativo a `raiz_proyecto` o absoluto) cae en `<proyecto>/docs/knowledge/`."""
    raiz = raiz_proyecto or "."
    root = _sin_prefijo_extendido(root)
    destino = root.replace("\\", "/") if not os.path.isabs(root) else root
    destino = destino if os.path.isabs(destino) else os.path.join(raiz, destino)
    try:
        k = _canon(os.path.join(raiz, "docs", "knowledge"))
        d = _canon(destino)
    except (OSError, ValueError):
        return True   # ruta que ni siquiera se puede resolver: se rechaza (fail closed)
    return d == k or d.startswith(k.rstrip("\\/") + os.sep)


def _es_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _str_no_vacio(v):
    return isinstance(v, str) and v.strip() != ""


# ------------------------------------------------------------------ training.json

def validar_config(cfg, raiz_proyecto=None):
    """Lista de errores `{campo, mensaje}` de un `training.json` ya parseado ([] = valido).
    `raiz_proyecto` (default: cwd) es contra la que se resuelve `root` para rechazarlo si cae
    dentro de `<proyecto>/docs/knowledge/`, sea relativo, absoluto o con otra capitalizacion."""
    if not isinstance(cfg, dict):
        return [_err("(raiz)", "training.json debe ser un objeto JSON")]
    errores = []
    for clave in cfg:
        if clave not in CLAVES_CONFIG:
            errores.append(_err(clave, f"clave desconocida (admitidas: {', '.join(CLAVES_CONFIG)})"))
    if cfg.get("version") not in VERSIONES_SOPORTADAS or not _es_int(cfg.get("version")):
        errores.append(_err("version", f"obligatorio; versiones soportadas: {VERSIONES_SOPORTADAS}"))
    enabled = cfg.get("enabled", False)
    if not isinstance(enabled, bool):
        errores.append(_err("enabled", "debe ser booleano"))
        enabled = False
    if "$comment" in cfg and not isinstance(cfg["$comment"], str):
        errores.append(_err("$comment", "debe ser texto"))
    if "bridge_to_curator" in cfg and not isinstance(cfg["bridge_to_curator"], bool):
        errores.append(_err("bridge_to_curator", "debe ser booleano"))

    if "root" in cfg or enabled:
        root = cfg.get("root")
        if not _str_no_vacio(root):
            errores.append(_err("root", "obligatorio con enabled: true (ruta del case store elegida por el proyecto)"))
        elif root.startswith("~"):
            errores.append(_err("root", "`~` no se expande: usa una ruta relativa al proyecto o absoluta explicita"))
        elif any(ord(c) < 32 for c in root):
            errores.append(_err("root", "no puede contener caracteres de control"))
        elif _root_en_docs_knowledge(root, raiz_proyecto):
            errores.append(_err("root", "el case store no puede vivir dentro de docs/knowledge/ (ADR-019)"))
    if "id_prefix" in cfg or enabled:
        pref = cfg.get("id_prefix")
        if not isinstance(pref, str) or not PATRON_PREFIJO.fullmatch(pref):
            errores.append(_err("id_prefix", "obligatorio con enabled: true; slug `^[a-z0-9][a-z0-9-]*$`"))

    ids = cfg.get("ids")
    if ids is not None:
        if not isinstance(ids, dict):
            errores.append(_err("ids", "debe ser un objeto"))
        else:
            for clave in ids:
                if clave not in CLAVES_IDS:
                    errores.append(_err(f"ids.{clave}", f"clave desconocida (admitidas: {', '.join(CLAVES_IDS)})"))
            for clave in ("family_pattern", "variant_pattern"):
                if clave in ids:
                    if not isinstance(ids[clave], str):
                        errores.append(_err(f"ids.{clave}", "regex invalida: no es una cadena"))
                        continue
                    try:
                        re.compile(ids[clave])
                    except ERRORES_REGEX as e:   # OverflowError/RecursionError tambien (gap #3)
                        errores.append(_err(f"ids.{clave}", f"regex invalida: {type(e).__name__}: {e}"))
            if "version_width" in ids:
                w = ids["version_width"]
                if not _es_int(w) or not 1 <= w <= 6:
                    errores.append(_err("ids.version_width", "entero entre 1 y 6"))
    return errores


def cargar_config(root):
    """`(config|None, ruta|None, errores)` del `training.json` del proyecto en `root`.
    Sin fichero -> `(None, None, [])`: la capacidad no esta configurada (opt-in, CA-01)."""
    ruta = os.path.join(root or ".", CONFIG_REL)
    if not os.path.isfile(ruta):
        return None, None, []
    try:
        with open(ruta, encoding="utf-8") as f:
            cfg = json.load(f)
    except (OSError, ValueError) as e:
        return None, ruta, [_err("(fichero)", f"JSON ilegible: {e}")]
    errores = validar_config(cfg, root or ".")
    return (cfg if not errores else None), ruta, errores


def patrones_id(config=None):
    ids = (config or {}).get("ids") or {}
    return (ids.get("family_pattern", PATRON_ID_DEFECTO), ids.get("variant_pattern", PATRON_ID_DEFECTO),
            ids.get("version_width", VERSION_WIDTH_DEFECTO))


# ------------------------------------------------------------------ ids

def construir_case_id(id_prefix, family, variant):
    base = f"{family}.{variant}"
    return f"{id_prefix}-{base}" if id_prefix else base


def referencia_version(case_id, version, width=VERSION_WIDTH_DEFECTO):
    return f"{case_id}@v{int(version):0{width}d}"


def directorio_version(family, variant, version, width=VERSION_WIDTH_DEFECTO):
    """Ruta RELATIVA a `<root>` de una version: `cases/<family>.<variant>/v<NNN>` (design.md).
    `ValueError` si `family`/`variant` no son un componente de ruta seguro (gap #4, CWE-22): esta
    funcion nunca devuelve una ruta que se salga de `cases/`, aunque el caso no se haya validado."""
    for nombre, v in (("family", family), ("variant", variant)):
        motivo = "debe ser texto no vacio" if not _str_no_vacio(v) else _componente_inseguro(v)
        if motivo:
            raise ValueError(f"{nombre} {v!r}: {motivo}")
    return os.path.join("cases", f"{family}.{variant}", f"v{int(version):0{width}d}")


def mapear_outcome(valor, fuente=None):
    """Traduce un outcome externo al vocabulario cerrado segun `OUTCOME_MAPEO`. Sin `fuente`, solo
    acepta el vocabulario propio. Lo desconocido (o de tipo no texto) devuelve None (nunca se
    inventa un outcome ni se lanza con un valor no hashable, gap #1)."""
    if not isinstance(valor, str) or (fuente is not None and not isinstance(fuente, str)):
        return None
    if fuente is None:
        return valor if valor in OUTCOMES else None
    return (OUTCOME_MAPEO.get(fuente) or {}).get(valor)


# ------------------------------------------------------------------ caso

def _es_clave_cot(clave):
    if not isinstance(clave, str):
        return False
    norm = clave.casefold().replace("-", "_")
    return any(norm.startswith(p) for p in CLAVES_COT)


def _es_parametro_proveedor(clave):
    return isinstance(clave, str) and clave.casefold().replace("-", "_") in CLAVES_PARAMETRO_PROVEEDOR


def _buscar_cot(valor, campo, errores, profundidad=0, ruta=()):
    """Recorre `valor` (dicts, listas y `arguments` en texto JSON) y anota cada clave de CoT.
    `ruta` es la ruta ESTRUCTURAL desde el turno (claves/indices reales, no el texto de `campo`,
    que una clave podria imitar): decide si se esta dentro de `tool_calls[<j>].arguments`."""
    if profundidad > PROFUNDIDAD_MAX:
        # gap #21: fail closed — lo que no se puede recorrer no se puede garantizar libre de CoT
        errores.append(_err(campo, f"anidamiento > {PROFUNDIDAD_MAX} niveles: no se puede comprobar que no haya chain-of-thought"))
        return
    if isinstance(valor, str) and ruta and ruta[-1] == "arguments":
        try:
            valor = json.loads(valor)
        except RecursionError:
            errores.append(_err(campo, f"anidamiento > {PROFUNDIDAD_MAX} niveles: no se puede comprobar que no haya chain-of-thought"))
            return
        except ValueError:
            return
    en_arguments = len(ruta) >= 3 and ruta[0] == "tool_calls" and isinstance(ruta[1], int) and ruta[2] == "arguments"
    if isinstance(valor, dict):
        for clave, sub in valor.items():
            if _es_clave_cot(clave) and not (en_arguments and _es_parametro_proveedor(clave)):
                errores.append(_err(f"{campo}.{clave}", "prohibido: la trayectoria nunca guarda chain-of-thought"))
            else:
                _buscar_cot(sub, f"{campo}.{clave}", errores, profundidad + 1, ruta + (clave,))
    elif isinstance(valor, list):
        for j, sub in enumerate(valor):
            _buscar_cot(sub, f"{campo}[{j}]", errores, profundidad + 1, ruta + (j,))


def _validar_turno(i, turno, errores):
    campo = f"trajectory[{i}]"
    if not isinstance(turno, dict):
        errores.append(_err(campo, "cada turno debe ser un objeto"))
        return
    _buscar_cot(turno, campo, errores)
    rol = turno.get("role")
    if rol not in ROLES:
        errores.append(_err(f"{campo}.role", f"obligatorio; uno de {', '.join(ROLES)}"))
    if "content" in turno and not isinstance(turno["content"], str):
        errores.append(_err(f"{campo}.content", "debe ser texto"))
    calls = turno.get("tool_calls")
    if calls is not None:
        if rol != "assistant":
            errores.append(_err(f"{campo}.tool_calls", "solo en turnos `assistant`"))
        if not isinstance(calls, list):
            errores.append(_err(f"{campo}.tool_calls", "debe ser una lista"))
            calls = []
        for j, call in enumerate(calls):
            if not isinstance(call, dict) or not _str_no_vacio(call.get("name")):
                errores.append(_err(f"{campo}.tool_calls[{j}].name", "obligatorio (nombre de la herramienta)"))
            elif "arguments" in call and not isinstance(call["arguments"], (dict, str)):
                errores.append(_err(f"{campo}.tool_calls[{j}].arguments", "objeto o texto JSON"))
    if rol == "assistant" and "content" not in turno and not calls:
        errores.append(_err(f"{campo}.content", "un turno `assistant` necesita content o tool_calls"))
    if rol in ("system", "user", "tool") and "content" not in turno:
        errores.append(_err(f"{campo}.content", "obligatorio"))
    if rol == "tool" and not _str_no_vacio(turno.get("name")):
        errores.append(_err(f"{campo}.name", "obligatorio en turnos `tool`"))
    if "ts" in turno and not isinstance(turno["ts"], str):
        errores.append(_err(f"{campo}.ts", "debe ser texto ISO-8601"))


def _validar_context(ctx, errores):
    if ctx is None:
        return
    if isinstance(ctx, str):
        return
    if not isinstance(ctx, dict):
        errores.append(_err("context", "texto u objeto (esquema libre del proyecto)"))
        return
    if "refs" not in ctx:
        return
    refs = ctx["refs"]
    if not isinstance(refs, list):
        errores.append(_err("context.refs", "lista de {ref, kind}"))
        return
    for i, r in enumerate(refs):
        if not isinstance(r, dict):
            errores.append(_err(f"context.refs[{i}]", "debe ser un objeto {ref, kind}"))
            continue
        if not _str_no_vacio(r.get("ref")):
            errores.append(_err(f"context.refs[{i}].ref", "obligatorio: `fichero:linea` o id de nodo"))
        if "kind" in r and not isinstance(r["kind"], str):
            errores.append(_err(f"context.refs[{i}].kind", "debe ser texto"))


def _validar_artifacts(arts, errores):
    if arts is None:
        return
    if not isinstance(arts, list):
        errores.append(_err("artifacts", "lista de referencias {path, hash, kind}"))
        return
    for i, a in enumerate(arts):
        campo = f"artifacts[{i}]"
        if not isinstance(a, dict):
            errores.append(_err(campo, "debe ser un objeto {path, hash, kind}"))
            continue
        for clave in CLAVES_INLINE:
            if clave in a:
                errores.append(_err(f"{campo}.{clave}", "prohibido contenido inline: solo referencia con ruta y hash"))
        if not _str_no_vacio(a.get("path")):
            errores.append(_err(f"{campo}.path", "obligatorio"))
        if not isinstance(a.get("hash"), str) or not PATRON_HASH.fullmatch(a["hash"]):
            errores.append(_err(f"{campo}.hash", "obligatorio: `<algoritmo>:<hex>` (p. ej. sha256:...)"))
        if "kind" in a and not isinstance(a["kind"], str):
            errores.append(_err(f"{campo}.kind", "debe ser texto"))


def _validar_validation(val, errores):
    if not isinstance(val, dict):
        errores.append(_err("validation", "obligatorio: {status, approved_by_human}"))
        return
    status = val.get("status")
    if status not in VALIDATION_STATUS:
        errores.append(_err("validation.status", f"obligatorio; uno de {', '.join(VALIDATION_STATUS)}"))
    humano = val.get("approved_by_human", False)
    if not isinstance(humano, bool):
        errores.append(_err("validation.approved_by_human", "debe ser booleano"))
    elif status == "approved" and humano is not True:
        errores.append(_err("validation.approved_by_human", "`approved` (Gold) exige aprobacion humana explicita"))
    elif status != "approved" and humano is True:
        errores.append(_err("validation.approved_by_human", "solo puede ser true con status `approved`"))
    for clave in ("approved_at", "reviewer_note"):
        if clave in val and val[clave] is not None and not isinstance(val[clave], str):
            errores.append(_err(f"validation.{clave}", "debe ser texto"))


def validar_caso(caso, config=None):
    """Lista de errores `{campo, mensaje}` de un caso ([] = valido). Con `config` (training.json
    ya validado) comprueba ademas el prefijo y los patrones de id del proyecto."""
    if not isinstance(caso, dict):
        return [_err("(raiz)", "el caso debe ser un objeto JSON")]
    errores = []
    pat_fam, pat_var, width = patrones_id(config)
    for campo, patron in (("family", pat_fam), ("variant", pat_var)):
        v = caso.get(campo)
        if not isinstance(v, str) or not _casa(patron, v):
            errores.append(_err(campo, f"obligatorio; debe casar ENTERO con {patron}"))
        elif _componente_inseguro(v):
            errores.append(_err(campo, f"{_componente_inseguro(v)} (es un directorio del case store)"))

    version = caso.get("version")
    if not _es_int(version) or version < 1:
        errores.append(_err("version", "obligatorio; entero >= 1"))

    case_id = caso.get("case_id")
    if not _str_no_vacio(case_id):
        errores.append(_err("case_id", "obligatorio"))
    elif isinstance(caso.get("family"), str) and isinstance(caso.get("variant"), str):
        base = f"{caso['family']}.{caso['variant']}"
        if config is not None:
            esperado = construir_case_id(config.get("id_prefix"), caso["family"], caso["variant"])
            if case_id != esperado:
                errores.append(_err("case_id", f"debe ser `{esperado}` (id_prefix + family.variant)"))
        elif not (case_id == base or (case_id.endswith("-" + base)
                                      and PATRON_PREFIJO.fullmatch(case_id[: -len(base) - 1] or "?"))):
            errores.append(_err("case_id", f"debe ser `[<id_prefix>-]{base}`"))

    if "created_at" in caso and not isinstance(caso["created_at"], str):
        errores.append(_err("created_at", "debe ser texto ISO-8601"))

    req = caso.get("request")
    if not (_str_no_vacio(req) or (isinstance(req, dict) and req)):
        errores.append(_err("request", "obligatorio: peticion LITERAL (texto u objeto no vacio)"))

    _validar_context(caso.get("context"), errores)
    if "constraints" in caso and not isinstance(caso["constraints"], dict):
        errores.append(_err("constraints", "debe ser un objeto (esquema libre del proyecto)"))

    tr = caso.get("trajectory")
    if not isinstance(tr, list) or not tr:
        errores.append(_err("trajectory", "obligatorio: lista no vacia de turnos (role/content/tool_calls)"))
    else:
        for i, turno in enumerate(tr):
            _validar_turno(i, turno, errores)

    if "metrics" in caso and not isinstance(caso["metrics"], dict):
        errores.append(_err("metrics", "debe ser un objeto JSON (opaco: lo calcula el proyecto)"))

    if "validation" not in caso:
        errores.append(_err("validation", "obligatorio: {status, approved_by_human}"))
    else:
        _validar_validation(caso["validation"], errores)

    outcome = caso.get("outcome")
    if not isinstance(outcome, str):
        # gap #1: un outcome no texto (lista, dict, None...) es un error de campo, nunca un crash
        errores.append(_err("outcome", f"obligatorio, texto; uno de {', '.join(OUTCOMES)}"))
    elif outcome not in OUTCOMES:
        extra = ""
        for fuente, tabla in OUTCOME_MAPEO.items():
            if outcome in tabla:
                extra = f" (vocabulario `{fuente}`: mapea con mapear_outcome -> `{tabla[outcome]}`)"
        errores.append(_err("outcome", f"obligatorio; uno de {', '.join(OUTCOMES)}{extra}"))
    _validar_supersedes(caso, outcome, errores, width)

    _validar_artifacts(caso.get("artifacts"), errores)
    return errores


def _validar_supersedes(caso, outcome, errores, width=VERSION_WIDTH_DEFECTO):
    """gap #5: `supersedes_case` solo con `corrected` (y ahi obligatorio), apuntando a una version
    ESTRICTAMENTE anterior del MISMO `case_id` (par fallo -> correccion, CA-12 de design.md), en
    forma CANONICA (`referencia_version`: digitos ASCII, relleno a `version_width`, >= 1; gap #19)."""
    sup = caso.get("supersedes_case")
    if sup is None:
        if outcome == "corrected":
            errores.append(_err("supersedes_case", "obligatorio con outcome `corrected` (`<case_id>@v<N>` del fallo)"))
        return
    m = PATRON_REFERENCIA.fullmatch(sup) if isinstance(sup, str) else None
    if m is None:
        errores.append(_err("supersedes_case", "formato `<case_id>@v<N>`"))
        return
    anterior = int(m.group(2))
    if anterior < 1 or m.group(2) != f"{anterior:0{width}d}":
        errores.append(_err("supersedes_case", f"forma canonica `<case_id>@v{'N' * width}` (version >= 1, {width} digitos): "
                                                f"p. ej. `{referencia_version(m.group(1), max(anterior, 1), width)}`"))
        return
    if outcome != "corrected":
        errores.append(_err("supersedes_case", "solo con outcome `corrected` (un caso que corrige a otro)"))
        return
    case_id, version = caso.get("case_id"), caso.get("version")
    if isinstance(case_id, str) and m.group(1) != case_id:
        errores.append(_err("supersedes_case", f"debe apuntar al mismo case_id `{case_id}` (una version anterior)"))
    elif _es_int(version) and anterior >= version:
        errores.append(_err("supersedes_case", f"debe apuntar a una version anterior a v{version} (nunca a si mismo ni a una posterior)"))


# ------------------------------------------------------------------ CLI

def _leer_json(ruta):
    with open(ruta, encoding="utf-8") as f:
        return json.load(f)


def _imprimir(errores, ruta):
    if not errores:
        print(f"OK {ruta}")
        return 0
    for e in errores:
        print(f"{ruta}: {e['campo']}: {e['mensaje']}")
    return 1


def _raiz_de(ruta_config, explicita=None):
    """Raiz del proyecto contra la que se resuelve `root`: la explicita (`--project-root`), la que
    se deduce si el fichero esta en `<proyecto>/.claude/knowledge-services/training.json`, o cwd."""
    if explicita:
        return explicita
    absoluta = os.path.abspath(ruta_config)
    if os.path.normcase(absoluta).endswith(os.path.normcase(os.sep + CONFIG_REL)):
        return absoluta[: -len(CONFIG_REL) - 1]
    return os.getcwd()


def main(argv=None):
    ap = argparse.ArgumentParser(description="Valida training.json o un caso del case store.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_cfg = sub.add_parser("config", help="valida un training.json")
    p_cfg.add_argument("fichero")
    p_cfg.add_argument("--project-root", help="raiz del proyecto (default: deducida de la ruta o cwd)")
    p_case = sub.add_parser("case", help="valida un caso (JSON unico)")
    p_case.add_argument("fichero")
    p_case.add_argument("--config", help="training.json del proyecto (prefijo y patrones de id)")
    p_case.add_argument("--project-root", help="raiz del proyecto (default: deducida de --config o cwd)")
    args = ap.parse_args(argv)
    try:
        datos = _leer_json(args.fichero)
        config = None
        if args.cmd == "case" and args.config:
            config = _leer_json(args.config)
            errores_cfg = validar_config(config, _raiz_de(args.config, args.project_root))
            if errores_cfg:
                return _imprimir(errores_cfg, args.config)
    except (OSError, ValueError) as e:
        print(f"error: JSON ilegible o fichero ausente: {e}", file=sys.stderr)
        return 2
    if args.cmd == "config":
        return _imprimir(validar_config(datos, _raiz_de(args.fichero, args.project_root)), args.fichero)
    return _imprimir(validar_caso(datos, config), args.fichero)


if __name__ == "__main__":
    sys.exit(main())
