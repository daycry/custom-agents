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
concreta (p. ej. `categories[2].routing.graphiti`) para que `/doctor` señale fichero y campo.

Uso:
  knowledge-schema.py <ruta-a-taxonomy.json>   # valida un fichero concreto; exit 0/1
  knowledge-schema.py --default                # valida (e imprime) la plantilla por defecto
Exit codes: 0 válido · 1 con errores (se listan en stdout) · 2 uso/JSON ilegible.
"""
import argparse
import json
import os
import sys

# Consola no UTF-8 (Windows cp1252) o tuberías: reconfigurar ANTES de leer/imprimir (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001 — ya leído, o None (capsys/pythonw)
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PATH = os.path.join(HERE, "templates", "taxonomy.json")
PROJECT_TAXONOMY_REL = os.path.join(".claude", "knowledge-services", "taxonomy.json")

VERSIONES_SOPORTADAS = (1,)
ROUTING_VALORES = (True, False, "summary")

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
  "id_prefix": "ca",
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
    "TODOs",
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


def default_taxonomy():
    """La plantilla por defecto del plugin, leída del disco si está disponible; si no, el
    respaldo embebido (mismo contenido). Nunca lanza."""
    try:
        with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return json.loads(json.dumps(_TAXONOMY_FALLBACK))


def validar(config, fichero="taxonomy.json"):
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

    backends = config.get("backends", {})
    backend_ids = set()
    if "backends" in config:
        if not isinstance(backends, dict):
            errores.append(_error("`backends` debe ser un objeto {id: {type, ...}}", fichero, "backends"))
            backends = {}
        for bid, bcfg in backends.items():
            campo = f"backends.{bid}"
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

    categories = config.get("categories")
    if categories is None:
        errores.append(_error("falta `categories`", fichero, "categories"))
    elif not isinstance(categories, list) or not categories:
        errores.append(_error("`categories` debe ser una lista no vacía", fichero, "categories"))
    else:
        vistas = set()
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
            if not cat.get("folder") or not isinstance(cat.get("folder"), str):
                errores.append(_error(f"{campo} no declara `folder`", fichero, f"{campo}.folder"))
            if not cat.get("min_evidence") or not isinstance(cat.get("min_evidence"), str):
                errores.append(_error(f"{campo} no declara `min_evidence`", fichero, f"{campo}.min_evidence"))
            evidence_levels = config.get("evidence_levels") or _TAXONOMY_FALLBACK["evidence_levels"]
            if cat.get("min_evidence") and cat["min_evidence"] not in evidence_levels:
                errores.append(_error(
                    f"{campo}.min_evidence `{cat['min_evidence']}` no está en `evidence_levels`",
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
                        if valor not in ROUTING_VALORES:
                            errores.append(_error(
                                f"{campo_r} debe ser true, false o \"summary\"", fichero, campo_r))
            # Sin `routing` declarado: fail-closed, no es un error de esquema (CA-09), solo
            # significa que la categoría no exporta a ningún backend.

    return errores


def cargar_taxonomia(root=None, fichero=None):
    """(config, origen, ruta_o_None, errores). `origen` = "proyecto" | "default".
    Si `fichero` se pasa explícito, se valida ese; si no, se busca
    `<root>/.claude/knowledge-services/taxonomy.json`. Sin fichero de proyecto → la plantilla por
    defecto (CA-01/CA-09), sin error. Con fichero de proyecto inválido → se devuelve igualmente
    (para que el llamador decida) junto con los errores."""
    ruta = fichero or (os.path.join(root or ".", PROJECT_TAXONOMY_REL) if root is not None else None)
    if ruta and os.path.isfile(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                config = json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            return None, "proyecto", ruta, [_error(f"JSON ilegible: {type(e).__name__}: {e}", ruta, "$")]
        errores = validar(config, ruta)
        return config, "proyecto", ruta, errores
    return default_taxonomy(), "default", None, []


def backend_ids_declarados(config):
    return set((config.get("backends") or {}).keys())


def categorias_por_backend(config, backend_id):
    """Categorías cuyo `routing[backend_id]` no es `false` (fail-closed por defecto: sin
    `routing` o sin la clave del backend, la categoría NO exporta)."""
    out = []
    for cat in config.get("categories") or []:
        routing = cat.get("routing") or {}
        if routing.get(backend_id, False):
            out.append(cat)
    return out


def _construir_parser():
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("ruta", nargs="?", help="ruta a un taxonomy.json a validar")
    ap.add_argument("--default", action="store_true", help="valida la plantilla por defecto del plugin")
    return ap


def main(argv=None):
    args = _construir_parser().parse_args(argv)
    if args.default:
        config = default_taxonomy()
        errores = validar(config, TEMPLATE_PATH)
    elif args.ruta:
        if not os.path.isfile(args.ruta):
            print(f"knowledge-schema: no existe `{args.ruta}`", file=sys.stderr)
            return 2
        try:
            with open(args.ruta, "r", encoding="utf-8") as f:
                config = json.load(f)
        except json.JSONDecodeError as e:
            print(f"knowledge-schema: JSON ilegible en `{args.ruta}`: {e}", file=sys.stderr)
            return 2
        errores = validar(config, args.ruta)
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
