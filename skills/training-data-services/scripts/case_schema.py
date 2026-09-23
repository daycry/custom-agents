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
       absoluta; la elige el proyecto (el plugin no impone nombre) y NUNCA dentro de
       `docs/knowledge/` (ADR-019: el case store no es memoria curada)
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
      · name (obligatorio en `tool`) · ts; NUNCA chain-of-thought (reasoning/thinking/...)
  validation {status, approved_by_human, approved_at?, reviewer_note?}   obligatorio
      status in pending|approved|needs_changes|rejected; approved <=> approved_by_human true
  outcome in success|failure|corrected (obligatorio); corrected exige
      supersedes_case = "<case_id>@v<N>" (par fallo -> correccion, CA-12)
  context (str|obj opcional; `refs`: [{"ref": "<fichero:linea|nodo>", "kind": "..."}] opcional)
  constraints (obj opcional) · metrics (obj opcional, opaco) · created_at (str opcional)
  artifacts (lista opcional de {path, hash "<algo>:<hex>", kind}; nunca contenido inline)

Mapeo DECLARADO de vocabularios externos de outcome (`OUTCOME_MAPEO`), sin ampliar el cerrado:
  graphify (`save-result`):  useful -> success · dead_end -> failure · corrected -> corrected

Cada error es `{campo, mensaje}` (el campo nombra la clave concreta, p. ej. `trajectory[2].role`).

Uso:
  case_schema.py config <training.json>                  # exit 0 valido · 1 errores · 2 uso/JSON
  case_schema.py case <caso.json> [--config <training.json>]
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
CLAVES_COT = ("reasoning", "reasoning_content", "thinking", "thought", "thoughts", "chain_of_thought")
CLAVES_INLINE = ("content", "data", "bytes", "base64", "blob")

PATRON_ID_DEFECTO = r"^[a-z0-9][a-z0-9_-]*$"
PATRON_PREFIJO = re.compile(r"^[a-z0-9][a-z0-9-]*$")
PATRON_HASH = re.compile(r"^[a-z0-9]+:[0-9a-fA-F]+$")
VERSION_WIDTH_DEFECTO = 3
CLAVES_CONFIG = ("version", "enabled", "root", "id_prefix", "ids", "bridge_to_curator", "$comment")
CLAVES_IDS = ("family_pattern", "variant_pattern", "version_width")


def _err(campo, mensaje):
    return {"campo": campo, "mensaje": mensaje}


def _es_int(v):
    return isinstance(v, int) and not isinstance(v, bool)


def _str_no_vacio(v):
    return isinstance(v, str) and v.strip() != ""


# ------------------------------------------------------------------ training.json

def validar_config(cfg):
    """Lista de errores `{campo, mensaje}` de un `training.json` ya parseado ([] = valido)."""
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
    if "bridge_to_curator" in cfg and not isinstance(cfg["bridge_to_curator"], bool):
        errores.append(_err("bridge_to_curator", "debe ser booleano"))

    if "root" in cfg or enabled:
        root = cfg.get("root")
        if not _str_no_vacio(root):
            errores.append(_err("root", "obligatorio con enabled: true (ruta del case store elegida por el proyecto)"))
        else:
            norm = os.path.normpath(root.replace("\\", "/")).replace("\\", "/")
            if not os.path.isabs(root) and (norm == "docs/knowledge" or norm.startswith("docs/knowledge/")):
                errores.append(_err("root", "el case store no puede vivir dentro de docs/knowledge/ (ADR-019)"))
    if "id_prefix" in cfg or enabled:
        pref = cfg.get("id_prefix")
        if not isinstance(pref, str) or not PATRON_PREFIJO.match(pref):
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
                    try:
                        if not isinstance(ids[clave], str):
                            raise re.error("no es una cadena")
                        re.compile(ids[clave])
                    except re.error as e:
                        errores.append(_err(f"ids.{clave}", f"regex invalida: {e}"))
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
    errores = validar_config(cfg)
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
    """Ruta RELATIVA a `<root>` de una version: `cases/<family>.<variant>/v<NNN>` (design.md)."""
    return os.path.join("cases", f"{family}.{variant}", f"v{int(version):0{width}d}")


def mapear_outcome(valor, fuente=None):
    """Traduce un outcome externo al vocabulario cerrado segun `OUTCOME_MAPEO`. Sin `fuente`, solo
    acepta el vocabulario propio. Lo desconocido devuelve None (nunca se inventa un outcome)."""
    if fuente is None:
        return valor if valor in OUTCOMES else None
    return (OUTCOME_MAPEO.get(fuente) or {}).get(valor)


# ------------------------------------------------------------------ caso

def _validar_turno(i, turno, errores):
    campo = f"trajectory[{i}]"
    if not isinstance(turno, dict):
        errores.append(_err(campo, "cada turno debe ser un objeto"))
        return
    for clave in CLAVES_COT:
        if clave in turno:
            errores.append(_err(f"{campo}.{clave}", "prohibido: la trayectoria nunca guarda chain-of-thought"))
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
        if not isinstance(a.get("hash"), str) or not PATRON_HASH.match(a["hash"]):
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
        if not isinstance(v, str) or not re.match(patron, v):
            errores.append(_err(campo, f"obligatorio; debe casar con {patron}"))

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
                                      and PATRON_PREFIJO.match(case_id[: -len(base) - 1] or "?"))):
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
    if outcome not in OUTCOMES:
        extra = ""
        for fuente, tabla in OUTCOME_MAPEO.items():
            if outcome in tabla:
                extra = f" (vocabulario `{fuente}`: mapea con mapear_outcome -> `{tabla[outcome]}`)"
        errores.append(_err("outcome", f"obligatorio; uno de {', '.join(OUTCOMES)}{extra}"))
    sup = caso.get("supersedes_case")
    patron_sup = re.compile(r"^\S+@v\d+$")
    if sup is not None and (not isinstance(sup, str) or not patron_sup.match(sup)):
        errores.append(_err("supersedes_case", "formato `<case_id>@v<N>`"))
    elif outcome == "corrected" and sup is None:
        errores.append(_err("supersedes_case", "obligatorio con outcome `corrected` (`<case_id>@v<N>` del fallo)"))

    _validar_artifacts(caso.get("artifacts"), errores)
    return errores


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


def main(argv=None):
    ap = argparse.ArgumentParser(description="Valida training.json o un caso del case store.")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p_cfg = sub.add_parser("config", help="valida un training.json")
    p_cfg.add_argument("fichero")
    p_case = sub.add_parser("case", help="valida un caso (JSON unico)")
    p_case.add_argument("fichero")
    p_case.add_argument("--config", help="training.json del proyecto (prefijo y patrones de id)")
    args = ap.parse_args(argv)
    try:
        datos = _leer_json(args.fichero)
        config = None
        if args.cmd == "case" and args.config:
            config = _leer_json(args.config)
            errores_cfg = validar_config(config)
            if errores_cfg:
                return _imprimir(errores_cfg, args.config)
    except (OSError, ValueError) as e:
        print(f"error: JSON ilegible o fichero ausente: {e}", file=sys.stderr)
        return 2
    if args.cmd == "config":
        return _imprimir(validar_config(datos), args.fichero)
    return _imprimir(validar_caso(datos, config), args.fichero)


if __name__ == "__main__":
    sys.exit(main())
