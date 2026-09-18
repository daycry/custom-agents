#!/usr/bin/env python3
"""
knowledge-index.py — índice canónico determinista sobre la taxonomía configurada
(ADR-018, `knowledge-services` T-02). Sin dependencias externas.

Opera EXCLUSIVAMENTE sobre `docs/knowledge/approved/<folder>/` (una carpeta por cada
`categories[].folder` de `.claude/knowledge-services/taxonomy.json`, o de la plantilla por
defecto del plugin si el proyecto no configura nada — ver `knowledge-schema.py`). NUNCA escanea
`docs/knowledge/candidates/**` (T-03): un candidato no aprobado no puede aparecer en el índice.

Decisión de alcance (sin respaldo literal en spec/design, señalada para revisión): este validador
NO toca el corpus heredado `docs/knowledge/{adr,gotchas,lessons}/` (índice manual + `knowledge-
lint.py` diferido por ADR-006 D4, que sigue vigente e intacto). `knowledge-index.py` es un
validador NUEVO, específico del flujo de candidatos/aprobados que introduce `knowledge-services`;
las entradas legadas no llevan `version` ni `enlaces` en su frontmatter y exigírselo retroactivamente
rompería ADR-001..ADR-017/GOT-.../LES-... existentes sin necesidad.

Contrato de frontmatter de una entrada aprobada:
  id (str, obligatorio) · version (int, obligatorio) · enlaces (lista opcional de ids referidos)

Cada error es un dict {mensaje, fichero, campo} (mismo contrato que knowledge-schema.validar).

Uso:
  knowledge-index.py [--root <ruta>]   # construye el índice y lista errores; exit 0/1
Exit codes: 0 índice construido sin errores · 1 con errores (taxonomía inválida o entradas
inválidas) · 2 uso.
"""
import argparse
import importlib.util
import os
import re
import sys

# Consola no UTF-8 (Windows cp1252) o tuberías: reconfigurar ANTES de leer/imprimir (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001 - ya leído, o None (capsys/pythonw)
        pass

HERE = os.path.dirname(os.path.abspath(__file__))


def _cargar_knowledge_schema():
    """Carga knowledge-schema.py (T-01) desde el mismo directorio. Replicado a propósito en vez
    de un import de paquete: cada script del kit compartido es standalone (ver comentario
    celdas_md en knowledge-find.py), pero ambos ficheros viajan siempre juntos en
    agent-kits/shared/, así que cargar el vecino por ruta relativa es seguro y evita duplicar
    ~200 líneas de validación de taxonomy.json."""
    ruta = os.path.join(HERE, "knowledge-schema.py")
    spec = importlib.util.spec_from_file_location("knowledge_schema", ruta)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _error(mensaje, fichero, campo):
    return {"mensaje": mensaje, "fichero": fichero, "campo": campo}


_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
_LISTA_RE = re.compile(r"^\[(.*)\]$")


def _frontmatter(texto):
    """Parser mínimo de frontmatter YAML-simple (solo escalares y listas [a, b] de una línea;
    suficiente para id, version, enlaces). Replicado deliberadamente en vez de importar el
    parser de knowledge-find.py (mismo criterio standalone que arriba, pero ese script cubre
    muchos más casos que no necesitamos aquí)."""
    m = _FRONTMATTER_RE.match(texto)
    if not m:
        return {}
    datos = {}
    for linea in m.group(1).splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or ":" not in linea:
            continue
        clave, _, valor = linea.partition(":")
        clave = clave.strip()
        valor = valor.strip()
        ml = _LISTA_RE.match(valor)
        if ml:
            datos[clave] = [v.strip() for v in ml.group(1).split(",") if v.strip()]
        else:
            datos[clave] = valor.strip('"').strip("'")
    return datos


def _carpetas_declaradas(config):
    """folder -> lista de categorías (una carpeta puede servir a varias categorías, p. ej.
    PATTERN y GOTCHA comparten gotchas/ en la plantilla por defecto)."""
    out = {}
    for cat in config.get("categories") or []:
        folder = cat.get("folder")
        if folder:
            out.setdefault(folder, []).append(cat.get("key"))
    return out


def build_index(root=None):
    """(indice, errores). indice: {id: {"ruta", "version", "folder", "enlaces"}}.
    errores: lista de {mensaje, fichero, campo}. Taxonomía inválida -> índice vacío y los
    errores de la taxonomía (no se intenta construir nada sobre un contrato roto)."""
    ks = _cargar_knowledge_schema()
    root = root or "."
    config, _origen, _ruta_taxonomia, errores_taxonomia = ks.cargar_taxonomia(root)
    if errores_taxonomia:
        return {}, errores_taxonomia

    base = os.path.join(root, "docs", "knowledge", "approved")
    carpetas = _carpetas_declaradas(config)

    indice = {}
    errores = []
    vistos_en = {}  # id -> primera ruta donde se vio (para el mensaje de duplicado)

    for folder in sorted(carpetas):
        d = os.path.join(base, folder)
        if not os.path.isdir(d):
            continue
        for nombre in sorted(os.listdir(d)):
            if not nombre.lower().endswith(".md") or nombre.upper() == "README.MD":
                continue
            ruta = os.path.join(d, nombre)
            try:
                with open(ruta, "r", encoding="utf-8") as f:
                    texto = f.read()
            except OSError as e:
                errores.append(_error(f"no se pudo leer: {e}", ruta, "$"))
                continue
            fm = _frontmatter(texto)
            id_ = fm.get("id")
            if not id_:
                errores.append(_error("falta `id` en el frontmatter", ruta, "id"))
                continue
            if id_ in indice:
                errores.append(_error(
                    f"id duplicado `{id_}` (ya declarado en `{vistos_en[id_]}`)", ruta, "id"))
                continue
            if "version" not in fm:
                errores.append(_error("falta `version` en el frontmatter", ruta, "version"))
                version = None
            else:
                try:
                    version = int(fm["version"])
                except (TypeError, ValueError):
                    errores.append(_error("`version` debe ser un entero", ruta, "version"))
                    version = None
            enlaces = fm.get("enlaces") or []
            if isinstance(enlaces, str):
                enlaces = [enlaces]
            indice[id_] = {"ruta": ruta, "version": version, "folder": folder, "enlaces": enlaces}
            vistos_en[id_] = ruta

    # Enlaces rotos: se resuelven una vez que TODO el índice está construido (un enlace puede
    # citar una entrada de otra carpeta que aún no se había escaneado).
    for id_, entrada in indice.items():
        for destino in entrada["enlaces"]:
            if destino not in indice:
                errores.append(_error(
                    f"enlace roto: `{id_}` cita `{destino}`, que no existe en el índice",
                    entrada["ruta"], "enlaces"))

    return indice, errores


def _construir_parser():
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument("--root", default=".", help="raíz del proyecto (default: cwd)")
    return ap


def main(argv=None):
    args = _construir_parser().parse_args(argv)
    indice, errores = build_index(args.root)
    if not errores:
        print(f"knowledge-index: {len(indice)} entrada(s), sin errores")
        return 0
    for e in errores:
        print(f"{e['fichero']}: {e['campo']}: {e['mensaje']}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
