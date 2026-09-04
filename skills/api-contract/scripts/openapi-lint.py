#!/usr/bin/env python3
"""
openapi-lint.py — valida la estructura MÍNIMA de una spec OpenAPI 3.x y, con `--diff`, detecta
cambios ROMPEDORES entre dos versiones. SIN dependencias externas (JSON con `json` de la stdlib;
YAML con `yaml` si el proyecto lo tiene instalado y, si no, un parser YAML mínimo propio para el
subconjunto habitual de las specs — ver `parse_yaml_simple` más abajo).

Qué valida (modo normal, un fichero):
  1. `openapi: "3.x.x"` presente.
  2. `paths` no vacío.
  3. Cada operación (get/put/post/delete/options/head/patch/trace bajo un path) tiene
     `operationId`, y es ÚNICO en todo el documento.
  4. `responses` de cada operación trae al menos una 2xx y al menos una 4xx/5xx (o el comodín
     `4XX`/`5XX`/`2XX`).
  5. Cada `$ref` interno (`#/components/...`) resuelve dentro del propio documento (refs a
     ficheros externos no se seseleccionan — no es un error, se ignoran).
  6. Cada parámetro (a nivel de path o de operación) trae `schema` o `content`.
  7. Aviso (NO error): request body `type: object` sin `additionalProperties: false` — informativo,
     nunca bloquea.

Qué detecta `--diff <old> <new>` (cambios ROMPEDORES vs. informativos):
  Rompedores: path eliminado, operación (método) eliminada de un path que sigue existiendo,
  parámetro obligatorio nuevo (o que pasa de opcional a obligatorio), parámetro eliminado, campo
  de la respuesta 2xx (`application/json`) eliminado, tipo (`type`) distinto en un parámetro o en
  un campo de la respuesta, `enum` que pierde valores que antes tenía.
  Informativos (NO rompedores): path nuevo, parámetro opcional nuevo, campo de respuesta nuevo.
  La comparación de respuestas se limita a `content.application/json` (el subconjunto habitual).

Exit: 0 spec válida / diff sin cambios rompedores · 1 errores encontrados / diff con rompedores ·
2 fichero ilegible, extensión no soportada, o uso incorrecto. Nunca lanza traceback: toda excepción
de parseo se convierte en un error de exit 2 con el mensaje explicado.

Uso:
  openapi-lint.py <spec.json|spec.yaml> [--json]
  openapi-lint.py --diff <old> <new> [--json]
"""
import argparse
import json
import os
import re
import sys

# Consola Windows (cp1252) o tuberías: reconfigurar ANTES de leer o imprimir nada (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

METODOS_HTTP = ("get", "put", "post", "delete", "options", "head", "patch", "trace")

_DQ_ESCAPES = {"n": "\n", "t": "\t", '"': '"', "\\": "\\", "/": "/", "r": "\r", "b": "\b", "f": "\f"}


class YamlSimpleError(Exception):
    """El YAML pedido no cabe en el subconjunto que soporta el parser interno (sin PyYAML)."""


# =============================================== parser YAML mínimo (sin dependencias) ====

def _strip_comment(line):
    """Corta un comentario ` # ...` que empiece fuera de comillas (un `#` dentro de '...'/"..." —
    típico de `$ref: '#/components/schemas/Pet'` — NO es un comentario)."""
    in_s = in_d = False
    i = 0
    while i < len(line):
        c = line[i]
        if in_s:
            if c == "'":
                in_s = False
        elif in_d:
            if c == '"' and line[i - 1] != "\\":
                in_d = False
        else:
            if c == "'":
                in_s = True
            elif c == '"':
                in_d = True
            elif c == "#" and (i == 0 or line[i - 1] in " \t"):
                return line[:i]
        i += 1
    return line


def _unescape_dq(s):
    out, i = [], 0
    while i < len(s):
        c = s[i]
        if c == "\\" and i + 1 < len(s):
            out.append(_DQ_ESCAPES.get(s[i + 1], s[i + 1]))
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def _find_mapping_colon(text):
    """Índice del `:` de mapeo (fuera de comillas, seguido de espacio o fin de línea) o -1."""
    in_s = in_d = False
    i = 0
    while i < len(text):
        c = text[i]
        if in_s:
            if c == "'":
                in_s = False
        elif in_d:
            if c == '"' and text[i - 1] != "\\":
                in_d = False
        else:
            if c == "'":
                in_s = True
            elif c == '"':
                in_d = True
            elif c == ":" and (i + 1 == len(text) or text[i + 1] in " \t"):
                return i
        i += 1
    return -1


def _parse_scalar(s):
    s = s.strip()
    if s == "" or s == "~" or s.lower() in ("null", "none"):
        return None
    if s.lower() == "true":
        return True
    if s.lower() == "false":
        return False
    if len(s) >= 2 and s[0] == '"' and s[-1] == '"':
        return _unescape_dq(s[1:-1])
    if len(s) >= 2 and s[0] == "'" and s[-1] == "'":
        return s[1:-1].replace("''", "'")
    if s[0] in "[{":
        val, _ = _parse_flow_value(s, 0)
        return val
    if re.fullmatch(r"[+-]?\d+", s):
        return int(s)
    if re.fullmatch(r"[+-]?(\d+\.\d*|\.\d+)([eE][+-]?\d+)?", s):
        return float(s)
    return s


def _skip_ws(s, i):
    while i < len(s) and s[i] in " \t":
        i += 1
    return i


def _parse_flow_value(s, i):
    i = _skip_ws(s, i)
    if i >= len(s):
        raise YamlSimpleError("colección flow incompleta")
    if s[i] == "[":
        return _parse_flow_seq(s, i)
    if s[i] == "{":
        return _parse_flow_map(s, i)
    if s[i] in "\"'":
        return _parse_flow_scalar_quoted(s, i)
    return _parse_flow_scalar_bare(s, i)


def _parse_flow_scalar_quoted(s, i):
    quote = s[i]
    j = i + 1
    buf = []
    while j < len(s) and s[j] != quote:
        if quote == '"' and s[j] == "\\" and j + 1 < len(s):
            buf.append(_DQ_ESCAPES.get(s[j + 1], s[j + 1]))
            j += 2
            continue
        if quote == "'" and s[j] == "'" and j + 1 < len(s) and s[j + 1] == "'":
            buf.append("'")
            j += 2
            continue
        buf.append(s[j])
        j += 1
    if j >= len(s):
        raise YamlSimpleError("cadena entrecomillada sin cerrar")
    return "".join(buf), j + 1


def _parse_flow_scalar_bare(s, i):
    start = i
    while i < len(s) and s[i] not in ",]}":
        i += 1
    return _parse_scalar(s[start:i]), i


def _parse_flow_key(s, i):
    """Como `_parse_flow_value` pero para la posición de CLAVE de un mapa flow: un escalar bare se
    corta también en `:` (si no, `{a: 1}` leería «a: 1» entero como clave — gap real, con test)."""
    i = _skip_ws(s, i)
    if i < len(s) and s[i] in "\"'":
        return _parse_flow_scalar_quoted(s, i)
    start = i
    while i < len(s) and s[i] not in ",]}:":
        i += 1
    return _parse_scalar(s[start:i]), i


def _parse_flow_seq(s, i):
    i += 1  # '['
    items = []
    i = _skip_ws(s, i)
    if i < len(s) and s[i] == "]":
        return items, i + 1
    while True:
        val, i = _parse_flow_value(s, i)
        items.append(val)
        i = _skip_ws(s, i)
        if i >= len(s):
            raise YamlSimpleError("lista flow `[...]` sin cerrar")
        if s[i] == ",":
            i = _skip_ws(s, i + 1)
            continue
        if s[i] == "]":
            return items, i + 1
        raise YamlSimpleError(f"carácter inesperado en lista flow: {s[i]!r}")


def _parse_flow_map(s, i):
    i += 1  # '{'
    out = {}
    i = _skip_ws(s, i)
    if i < len(s) and s[i] == "}":
        return out, i + 1
    while True:
        i = _skip_ws(s, i)
        key, i = _parse_flow_key(s, i)
        i = _skip_ws(s, i)
        if i >= len(s) or s[i] != ":":
            raise YamlSimpleError("se esperaba ':' en mapa flow `{...}`")
        val, i = _parse_flow_value(s, i + 1)
        out[key] = val
        i = _skip_ws(s, i)
        if i >= len(s):
            raise YamlSimpleError("mapa flow `{...}` sin cerrar")
        if s[i] == ",":
            i += 1
            continue
        if s[i] == "}":
            return out, i + 1
        raise YamlSimpleError(f"carácter inesperado en mapa flow: {s[i]!r}")


def _is_seq_line(text):
    return text == "-" or text.startswith("- ") or text.startswith("-\t")


def _dash_offset(text):
    m = re.match(r"-(\s+)", text)
    return 1 + len(m.group(1)) if m else 2


def _parse_block(lines, start, indent):
    if start >= len(lines):
        return None, start
    ind, text = lines[start]
    if ind != indent:
        raise YamlSimpleError(f"indentación inesperada en {text!r} (se esperaba columna {indent})")
    if _is_seq_line(text):
        return _parse_block_seq(lines, start, indent)
    return _parse_block_map(lines, start, indent)


def _parse_block_seq(lines, start, indent):
    items = []
    i = start
    while i < len(lines) and lines[i][0] == indent and _is_seq_line(lines[i][1]):
        text = lines[i][1]
        offset = _dash_offset(text)
        rest = "" if text == "-" else text[offset:]
        if rest.strip() == "":
            i += 1
            if i < len(lines) and lines[i][0] > indent:
                val, i = _parse_block(lines, i, lines[i][0])
            else:
                val = None
            items.append(val)
        elif _find_mapping_colon(rest) != -1:
            child_col = indent + offset
            lines[i] = [child_col, rest]
            val, i = _parse_block_map(lines, i, child_col)
            items.append(val)
        else:
            items.append(_parse_scalar(rest))
            i += 1
    return items, i


def _parse_block_map(lines, start, indent):
    out = {}
    i = start
    while i < len(lines) and lines[i][0] == indent and not _is_seq_line(lines[i][1]):
        text = lines[i][1]
        colon = _find_mapping_colon(text)
        if colon == -1:
            raise YamlSimpleError(f"no se encontró ':' de mapeo en línea: {text!r}")
        key = _parse_scalar(text[:colon])
        rest = text[colon + 1:].strip()
        i += 1
        if rest == "":
            if i < len(lines) and lines[i][0] > indent:
                val, i = _parse_block(lines, i, lines[i][0])
            else:
                val = None
        elif rest[0] in "|>":
            raise YamlSimpleError("bloque escalar (`|`/`>`) no soportado por el parser interno")
        else:
            val = _parse_scalar(rest)
        out[key] = val
    return out, i


def parse_yaml_simple(text):
    """Parser YAML mínimo (sin PyYAML) para el subconjunto habitual de las specs OpenAPI: mapas y
    listas por indentación (2+ espacios, sin tabs), escalares, cadenas entrecomilladas, colecciones
    flow (`[...]`/`{...}`), `$ref`. Lanza `YamlSimpleError` ante algo fuera de ese subconjunto
    (anclas/alias, bloques `|`/`>`, multi-documento, indentación con tabs)."""
    lines = []
    for raw in text.splitlines():
        sin_comentario = _strip_comment(raw).rstrip()
        if sin_comentario.strip() in ("", "---", "..."):
            continue
        indent = len(sin_comentario) - len(sin_comentario.lstrip(" "))
        cabecera = sin_comentario[:indent]
        if "\t" in cabecera:
            raise YamlSimpleError("indentación con tabs no soportada")
        lines.append([indent, sin_comentario[indent:]])
    if not lines:
        return None
    valor, i = _parse_block(lines, 0, lines[0][0])
    if i != len(lines):
        raise YamlSimpleError(f"contenido inesperado tras la línea {i + 1} (¿multi-documento o indentación irregular?)")
    return valor


# ================================================================= carga de documentos ====

def cargar_documento(path):
    """(spec, None) o (None, mensaje-de-error). Nunca lanza."""
    if not os.path.isfile(path):
        return None, f"no existe: {path}"
    try:
        with open(path, encoding="utf-8-sig") as f:
            text = f.read()
    except OSError as e:
        return None, f"no se pudo leer {path}: {e}"
    ext = os.path.splitext(path)[1].lower()
    if ext == ".json":
        try:
            return json.loads(text), None
        except ValueError as e:
            return None, f"JSON inválido en {path}: {e}"
    if ext in (".yaml", ".yml"):
        try:
            import yaml  # PyYAML — opcional, ver módulo docstring
        except ImportError:
            yaml = None
        if yaml is not None:
            try:
                return yaml.safe_load(text), None
            except Exception as e:  # noqa: BLE001 — cualquier fallo de PyYAML se reporta igual
                return None, f"YAML inválido en {path}: {e}"
        try:
            return parse_yaml_simple(text), None
        except YamlSimpleError as e:
            return None, (f"YAML fuera del subconjunto soportado por el parser interno en {path} "
                          f"({e}) — instala PyYAML para specs más complejas")
    return None, f"extensión no soportada (usa .json/.yaml/.yml): {path}"


def resolve_pointer(doc, pointer):
    """pointer tipo '#/components/schemas/Pet'. (valor, None) o (None, mensaje)."""
    if not pointer.startswith("#/"):
        return None, "solo se resuelven referencias internas (#/...); las externas se ignoran"
    node = doc
    for parte in pointer[2:].split("/"):
        parte = parte.replace("~1", "/").replace("~0", "~")
        if isinstance(node, dict) and parte in node:
            node = node[parte]
        elif isinstance(node, list):
            try:
                node = node[int(parte)]
            except (ValueError, IndexError):
                return None, f"segmento «{parte}» no existe"
        else:
            return None, f"segmento «{parte}» no existe"
    return node, None


def iter_refs(node, ruta=""):
    if isinstance(node, dict):
        ref = node.get("$ref")
        if isinstance(ref, str):
            yield ruta, ref
        for k, v in node.items():
            if k != "$ref":
                yield from iter_refs(v, f"{ruta}/{k}")
    elif isinstance(node, list):
        for idx, v in enumerate(node):
            yield from iter_refs(v, f"{ruta}/{idx}")


def _resolve_schema(doc, schema):
    if isinstance(schema, dict) and isinstance(schema.get("$ref"), str):
        resuelto, err = resolve_pointer(doc, schema["$ref"])
        return resuelto if not err and isinstance(resuelto, dict) else {}
    return schema if isinstance(schema, dict) else {}


def _code_class(code):
    k = str(code).strip().upper()
    if re.fullmatch(r"[2-5](\d\d|XX)", k):
        return k[0]
    return None


# ============================================================================ validación ====

def _validar_parametro(p, ruta, errores):
    if not isinstance(p, dict) or "$ref" in p:
        return
    if "schema" not in p and "content" not in p:
        errores.append({"ruta": ruta, "mensaje": f"parámetro sin `schema` ni `content`: {p.get('name', '?')}"})


def _avisar_request_body(body, ruta, avisos):
    content = body.get("content")
    if not isinstance(content, dict):
        return
    for media, mt in content.items():
        schema = mt.get("schema") if isinstance(mt, dict) else None
        if isinstance(schema, dict) and schema.get("type") == "object" and "additionalProperties" not in schema:
            avisos.append({"ruta": f"{ruta}/content/{media}/schema",
                           "mensaje": "objeto sin `additionalProperties: false` (opcional)"})


def validar(spec):
    """(errores, avisos) — listas de {"ruta", "mensaje"}. Nunca lanza sobre un `spec` ya cargado."""
    errores, avisos = [], []
    if not isinstance(spec, dict):
        return [{"ruta": "/", "mensaje": "el documento raíz no es un mapa/objeto"}], []
    v = spec.get("openapi")
    v = str(v) if isinstance(v, (int, float)) else v
    if not isinstance(v, str) or not re.match(r"^3\.\d+(\.\d+)?$", v):
        errores.append({"ruta": "/openapi", "mensaje": f"`openapi` ausente o no es 3.x: {spec.get('openapi')!r}"})
    paths = spec.get("paths")
    if not isinstance(paths, dict) or not paths:
        errores.append({"ruta": "/paths", "mensaje": "`paths` ausente o vacío"})
        paths = {}
    ids_vistos = {}
    for ruta_path, item in paths.items():
        if not isinstance(item, dict):
            continue
        for idx, p in enumerate(item.get("parameters") or []):
            _validar_parametro(p, f"/paths/{ruta_path}/parameters/{idx}", errores)
        for metodo in METODOS_HTTP:
            op = item.get(metodo)
            if not isinstance(op, dict):
                continue
            base = f"/paths/{ruta_path}/{metodo}"
            opid = op.get("operationId")
            if not opid or not isinstance(opid, str):
                errores.append({"ruta": f"{base}/operationId", "mensaje": "falta `operationId`"})
            elif opid in ids_vistos:
                errores.append({"ruta": f"{base}/operationId",
                                "mensaje": f"`operationId` duplicado «{opid}» (también en {ids_vistos[opid]})"})
            else:
                ids_vistos[opid] = base
            responses = op.get("responses")
            if not isinstance(responses, dict) or not responses:
                errores.append({"ruta": f"{base}/responses", "mensaje": "`responses` ausente o vacío"})
            else:
                clases = {_code_class(k) for k in responses}
                if "2" not in clases:
                    errores.append({"ruta": f"{base}/responses", "mensaje": "sin ninguna respuesta 2xx"})
                if not ({"4", "5"} & clases):
                    errores.append({"ruta": f"{base}/responses", "mensaje": "sin ninguna respuesta 4xx/5xx"})
            for idx, p in enumerate(op.get("parameters") or []):
                _validar_parametro(p, f"{base}/parameters/{idx}", errores)
            body = op.get("requestBody")
            if isinstance(body, dict):
                _avisar_request_body(body, f"{base}/requestBody", avisos)
    for ruta_ref, ref in iter_refs(spec):
        if ref.startswith("#/"):
            _, err = resolve_pointer(spec, ref)
            if err:
                errores.append({"ruta": ruta_ref, "mensaje": f"`$ref` roto «{ref}»: {err}"})
    return errores, avisos


# ==================================================================================== diff ====

def _param_key(p):
    return (p.get("name"), p.get("in")) if isinstance(p, dict) else None


def _diff_enum(old_schema, new_schema, ruta, cambios):
    oe, ne = old_schema.get("enum"), new_schema.get("enum")
    if isinstance(oe, list) and isinstance(ne, list):
        perdidos = [v for v in oe if v not in ne]
        if perdidos:
            cambios.append({"ruta": ruta, "mensaje": f"`enum` pierde valores: {perdidos}", "rompedor": True})


def _diff_parametros(old_doc, new_doc, old_op, new_op, base, cambios):
    old_params = {_param_key(p): p for p in (old_op.get("parameters") or []) if isinstance(p, dict) and "$ref" not in p}
    new_params = {_param_key(p): p for p in (new_op.get("parameters") or []) if isinstance(p, dict) and "$ref" not in p}
    for key, np in new_params.items():
        if key is None:
            continue
        ruta = f"{base}/parameters/{key[0]}"
        op = old_params.get(key)
        if op is None:
            rompedor = bool(np.get("required"))
            cambios.append({"ruta": ruta, "rompedor": rompedor,
                            "mensaje": f"parámetro {'obligatorio' if rompedor else 'opcional'} nuevo: "
                                       f"{key[0]} (in: {key[1]})"})
            continue
        if not op.get("required") and np.get("required"):
            cambios.append({"ruta": ruta, "mensaje": f"parámetro pasa a obligatorio: {key[0]}", "rompedor": True})
        old_schema = _resolve_schema(old_doc, op.get("schema") or {})
        new_schema = _resolve_schema(new_doc, np.get("schema") or {})
        ot, nt = old_schema.get("type"), new_schema.get("type")
        if ot and nt and ot != nt:
            cambios.append({"ruta": ruta, "mensaje": f"tipo cambiado en parámetro {key[0]}: {ot} → {nt}", "rompedor": True})
        _diff_enum(old_schema, new_schema, ruta, cambios)
    for key, op in old_params.items():
        if key is not None and key not in new_params:
            cambios.append({"ruta": f"{base}/parameters/{key[0]}",
                            "mensaje": f"parámetro eliminado: {key[0]} (in: {key[1]})", "rompedor": True})


def _diff_respuestas(old_doc, new_doc, old_op, new_op, base, cambios):
    old_resp = old_op.get("responses") if isinstance(old_op.get("responses"), dict) else {}
    new_resp = new_op.get("responses") if isinstance(new_op.get("responses"), dict) else {}
    for code, old_r in old_resp.items():
        if _code_class(code) != "2" or not isinstance(old_r, dict):
            continue
        new_r = new_resp.get(code)
        if not isinstance(new_r, dict):
            continue
        ruta_base = f"{base}/responses/{code}/content/application~1json/schema/properties"
        old_schema = _resolve_schema(old_doc, ((old_r.get("content") or {}).get("application/json") or {}).get("schema") or {})
        new_schema = _resolve_schema(new_doc, ((new_r.get("content") or {}).get("application/json") or {}).get("schema") or {})
        old_props = old_schema.get("properties") if isinstance(old_schema.get("properties"), dict) else {}
        new_props = new_schema.get("properties") if isinstance(new_schema.get("properties"), dict) else {}
        for name, oprop in old_props.items():
            ruta = f"{ruta_base}/{name}"
            if name not in new_props:
                cambios.append({"ruta": ruta, "mensaje": f"campo de respuesta eliminado: {name}", "rompedor": True})
                continue
            nprop = new_props[name]
            if isinstance(oprop, dict) and isinstance(nprop, dict):
                ot, nt = oprop.get("type"), nprop.get("type")
                if ot and nt and ot != nt:
                    cambios.append({"ruta": ruta, "mensaje": f"tipo cambiado en campo {name}: {ot} → {nt}", "rompedor": True})
                _diff_enum(oprop, nprop, ruta, cambios)
        for name in new_props:
            if name not in old_props:
                cambios.append({"ruta": f"{ruta_base}/{name}", "mensaje": f"campo de respuesta nuevo (opcional): {name}",
                                "rompedor": False})


def diff_specs(old, new):
    """Lista de {"ruta", "mensaje", "rompedor": bool}. `old`/`new` ya cargados (dict)."""
    cambios = []
    old_paths = old.get("paths") if isinstance(old, dict) and isinstance(old.get("paths"), dict) else {}
    new_paths = new.get("paths") if isinstance(new, dict) and isinstance(new.get("paths"), dict) else {}
    for p in old_paths:
        if p not in new_paths:
            cambios.append({"ruta": f"/paths/{p}", "mensaje": f"path eliminado: {p}", "rompedor": True})
    for p in new_paths:
        if p not in old_paths:
            cambios.append({"ruta": f"/paths/{p}", "mensaje": f"path nuevo: {p}", "rompedor": False})
    for p, old_item in old_paths.items():
        new_item = new_paths.get(p)
        if not isinstance(old_item, dict) or not isinstance(new_item, dict):
            continue
        for metodo in METODOS_HTTP:
            old_op, new_op = old_item.get(metodo), new_item.get(metodo)
            if isinstance(old_op, dict) and not isinstance(new_op, dict):
                cambios.append({"ruta": f"/paths/{p}/{metodo}",
                                "mensaje": f"operación eliminada: {metodo.upper()} {p}", "rompedor": True})
                continue
            if not isinstance(old_op, dict) or not isinstance(new_op, dict):
                continue
            base = f"/paths/{p}/{metodo}"
            _diff_parametros(old, new, old_op, new_op, base, cambios)
            _diff_respuestas(old, new, old_op, new_op, base, cambios)
    return cambios


# ========================================================================== CLI / salida ====

def evaluar(path):
    spec, err = cargar_documento(path)
    if err:
        return {"modo": "validar", "exit": 2, "errores": [{"ruta": "/", "mensaje": err}], "avisos": []}
    errores, avisos = validar(spec)
    return {"modo": "validar", "exit": (0 if not errores else 1), "errores": errores, "avisos": avisos}


def evaluar_diff(path_old, path_new):
    old, err1 = cargar_documento(path_old)
    if err1:
        return {"modo": "diff", "exit": 2, "errores": [{"ruta": "/", "mensaje": err1}], "cambios": []}
    new, err2 = cargar_documento(path_new)
    if err2:
        return {"modo": "diff", "exit": 2, "errores": [{"ruta": "/", "mensaje": err2}], "cambios": []}
    cambios = diff_specs(old, new)
    rompedores = [c for c in cambios if c["rompedor"]]
    return {"modo": "diff", "exit": (0 if not rompedores else 1), "cambios": cambios, "rompedores": len(rompedores)}


def render_md(res):
    L = []
    if res["exit"] == 2:
        L.append(f"openapi-lint: ERROR — {res['errores'][0]['mensaje']}")
        return "\n".join(L)
    if res["modo"] == "validar":
        if not res["errores"]:
            extra = f", {len(res['avisos'])} aviso(s)" if res["avisos"] else ""
            L.append(f"openapi-lint: spec VÁLIDA (0 errores{extra})")
        else:
            L.append(f"openapi-lint: spec INVÁLIDA — {len(res['errores'])} error(es)")
            for e in res["errores"]:
                L.append(f"   ❌ {e['ruta']}: {e['mensaje']}")
        for a in res["avisos"]:
            L.append(f"   ⚠️  {a['ruta']}: {a['mensaje']}")
    else:
        if not res["cambios"]:
            L.append("openapi-lint --diff: sin cambios")
        else:
            L.append(f"openapi-lint --diff: {res['rompedores']} cambio(s) ROMPEDOR(ES) de {len(res['cambios'])} total(es)")
            for c in res["cambios"]:
                L.append(f"   {'💥' if c['rompedor'] else 'ℹ️ '} {c['ruta']}: {c['mensaje']}")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Valida una spec OpenAPI 3.x o compara dos versiones (--diff).")
    ap.add_argument("spec", nargs="?", help="fichero .json/.yaml/.yml a validar")
    ap.add_argument("--diff", nargs=2, metavar=("OLD", "NEW"), help="compara OLD → NEW: cambios rompedores")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    if args.diff:
        res = evaluar_diff(*args.diff)
    elif args.spec:
        res = evaluar(args.spec)
    else:
        print("openapi-lint: uso: openapi-lint.py <spec> [--json] | --diff <old> <new> [--json]", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(render_md(res))
    return res["exit"]


if __name__ == "__main__":
    sys.exit(main())
