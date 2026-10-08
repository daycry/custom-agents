#!/usr/bin/env python3
"""
knowledge-index.py — índice canónico determinista sobre la taxonomía configurada
(ADR-018, `knowledge-services` T-02). Sin dependencias externas.

Opera EXCLUSIVAMENTE sobre `docs/knowledge/approved/<folder>/` (una carpeta por cada
`categories[].folder` de `.claude/knowledge-services/taxonomy.json`, o de la plantilla por
defecto del plugin si el proyecto no configura nada — ver `knowledge-schema.py`). NUNCA escanea
`docs/knowledge/candidates/**` (T-03): un candidato no aprobado no puede aparecer en el índice.
Recorre subcarpetas de cada `folder` declarado (gap 17, revisión intento 1): una entrada puede
vivir en un subdirectorio propio (p. ej. adjuntos junto al `.md`).

Decisión de alcance (sin respaldo literal en spec/design, señalada para revisión): este validador
NO toca el corpus heredado `docs/knowledge/{adr,gotchas,lessons}/` (índice manual + `knowledge-
lint.py` diferido por ADR-006 D4, que sigue vigente e intacto). `knowledge-index.py` es un
validador NUEVO, específico del flujo de candidatos/aprobados que introduce `knowledge-services`;
las entradas legadas no llevan `version` ni `enlaces` en su frontmatter y exigírselo retroactivamente
rompería ADR-001..ADR-017/GOT-.../LES-... existentes sin necesidad.

Contrato de frontmatter de una entrada aprobada:
  id (str, obligatorio) · version (int, obligatorio) · enlaces (lista opcional de ids referidos)
  · estado (obligatorio, gap 43; debe ser "aprobado" — coherente con vivir bajo `approved/`)
  · fuentes (opcional; si se declara, lista no vacía) · tags (opcional; si se declara, lista)

Alcance de la validación de frontmatter (gap 3, revisión intento 1; `estado` pasó a obligatorio
en el gap 43): este índice exige `estado` y comprueba la FORMA de `estado`/`fuentes`/`tags`
(`fuentes`/`tags` solo si el campo está presente — nunca los exige), y nunca
comprueba `evidencia` contra el `min_evidence` de su categoría (una entrada de `approved/<folder>/`
puede pertenecer a más de una `category` que comparta esa carpeta — p. ej. PATTERN y GOTCHA
comparten `gotchas/` en la plantilla por defecto — así que el `folder` por sí solo no basta para
resolver a qué categoría exacta pertenece y qué evidencia mínima le aplica). Esa comprobación
semántica, y la obligatoriedad de los campos en el momento de aprobar un candidato, son del
`knowledge-curator` (T-04), que sí conoce la categoría exacta que asignó al aprobar.

Cada error es un dict {mensaje, fichero, campo} (mismo contrato que knowledge-schema.validar).
Los atributos de compatibilidad se reexportan por `__getattr__` desde `knowledge-local.py`.
Una instalación parcial sin helper devuelve diagnóstico estructurado en API/CLI, sin traceback.

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
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

HERE = os.path.dirname(os.path.abspath(__file__))


class KnowledgeSchemaNoDisponible(Exception):
    """`knowledge-schema.py` no se pudo cargar (gap 4): degradación explícita en vez de un
    traceback crudo de `importlib` cuando el vecino no viaja junto a este fichero."""


def _cargar_knowledge_schema():
    """Carga knowledge-schema.py (T-01) desde el mismo directorio. Replicado a propósito en vez
    de un import de paquete: cada script del kit compartido es standalone (ver comentario
    celdas_md en knowledge-find.py), pero ambos ficheros viajan siempre juntos en
    agent-kits/shared/, así que cargar el vecino por ruta relativa es seguro y evita duplicar
    ~200 líneas de validación de taxonomy.json.

    Mecanismo B de ADR-016 (canónico + degradación, no respaldo copiado): si el fichero falta o
    no carga, se levanta `KnowledgeSchemaNoDisponible` con un mensaje claro — el llamador
    (`build_index`) lo convierte en un error `{fichero, campo, mensaje}` normal (exit 1), nunca en
    un traceback (gap 4; `capabilities.py` ya degradaba así a través de `_resolver`, este fichero
    no)."""
    ruta = os.path.join(HERE, "knowledge-schema.py")
    if not os.path.isfile(ruta):
        raise KnowledgeSchemaNoDisponible(f"no se encontró `{ruta}` (debería viajar junto a este fichero)")
    spec = importlib.util.spec_from_file_location("knowledge_schema", ruta)
    if spec is None or spec.loader is None:
        raise KnowledgeSchemaNoDisponible(f"no se pudo preparar la carga de `{ruta}`")
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
    except Exception as e:  # noqa: BLE001 - cualquier fallo de carga degrada, no tumba el CLI
        raise KnowledgeSchemaNoDisponible(f"{type(e).__name__}: {e}") from e
    return mod


_LOCAL_PATH = os.path.join(HERE, "knowledge-local.py")
try:
    _spec_local = importlib.util.spec_from_file_location("knowledge_local", _LOCAL_PATH)
    _LOCAL = importlib.util.module_from_spec(_spec_local)
    _spec_local.loader.exec_module(_LOCAL)
    _LOCAL_ERROR = None
except Exception as exc:
    _LOCAL = None
    _LOCAL_ERROR = f"no se pudo cargar knowledge-local.py: {type(exc).__name__}: {exc}"[:600]


def __getattr__(name):
    """Compatibility reexports delegate to the sole parser/validator owner."""
    if name in {"_recortar_comentario_inline", "_frontmatter", "_carpetas_declaradas",
                "_ruta_segura_dentro", "_validar_frontmatter_forma", "_FRONTMATTER_RE",
                "_LISTA_RE", "_ITEM_BLOQUE_RE", "_ESTADOS_VALIDOS_APROBADO", "_ID_VALIDO_RE"}:
        if _LOCAL is None:
            raise KnowledgeSchemaNoDisponible(_LOCAL_ERROR)
        return getattr(_LOCAL, name)
    raise AttributeError(name)


def _error(mensaje, fichero, campo):
    return {"mensaje": mensaje, "fichero": fichero, "campo": campo}


def build_index(root=None):
    root = root or "."
    if _LOCAL is None:
        return {}, [_error(_LOCAL_ERROR, _LOCAL_PATH, "$")]
    try:
        ks = _cargar_knowledge_schema()
    except KnowledgeSchemaNoDisponible as e:
        return {}, [_error(str(e), os.path.join(HERE, "knowledge-schema.py"), "$")]
    config, _origin, _path, errors = ks.cargar_taxonomia(root)
    if errors:
        return {}, errors
    return _LOCAL.build_index(root, config=config)


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
