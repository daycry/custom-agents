#!/usr/bin/env python3
"""
backends/graphiti_model.py — ontología derivada de `taxonomy.json` para el adaptador `graphiti`
(graphiti-memory T-02, ADR-018 enmienda 2026-09-17, CA-13 reformulado en la enmienda 2026-09-18;
T-01-fix1: gaps #2/#4/#5/#12 de la revisión de dos lentes, intento 1).

No es el adaptador (`graphiti.py`, T-04): este módulo es PURO (sin red, sin disco, sin
`outbox.py`) y solo calcula datos a partir de la taxonomía y de `backends.graphiti.config`:

  - `tipo_entidad` / `tipos_por_categoria`: los tipos de entidad los fija el SERVIDOR Graphiti MCP
    (`config.yaml`), no el cliente. Este módulo NUNCA declara una lista de tipos de dominio: cada
    categoría de `taxonomy.json` se mapea a un tipo declarado en `backends.graphiti.config.entity_map`
    (por el usuario, contra los tipos reales de SU servidor); sin mapeo, el default es `Document`
    (el tipo más genérico del servidor de referencia, `dockers/knowledge-graphs`).
  - `proponer_entity_types_yaml`: genera el bloque `entity_types` (YAML de mano, sin PyYAML —
    mismo criterio que `skills/api-contract/scripts/openapi-lint.py`) que el usuario puede pegar en
    el `config.yaml` de SU servidor: una entrada por CATEGORÍA de `taxonomy.json` (T-01-fix1 gap
    #2) — nombre `entity_map[key]` si está declarado, si no `TitleCase(key)` (nunca un genérico
    compartido tipo `Document`, sin lista de dominio en código); dos categorías que resuelven al
    mismo nombre explícito se deduplican en una sola entrada — más los dos tipos núcleo del
    adaptador, `Knowledge` y `Evidence`. `name:` va siempre escapado (gap #4).
  - `relaciones_efectivas`: relaciones núcleo (`SUPPORTED_BY`, `SUPERSEDES`, `CONTRADICTS`, vía
    `add_triplet` en el adaptador) más las que el proyecto declare en `backends.graphiti.config.relations`,
    sin duplicar las del núcleo.
  - `cadena_supersedes`: la sucesión de versiones de un mismo linaje de `knowledge_id` como una
    cadena de relaciones `SUPERSEDES` — conserva TODAS las versiones (nunca borra ninguna) y marca
    cuál es la vigente (la última) y cuáles quedan invalidadas (todas las anteriores), CA-11.

Sin dependencias externas; solo stdlib (`json`, usado solo para escapar cadenas como escalares
YAML entre comillas dobles — un escalar `"..."` con `json.dumps` es YAML válido).
"""
import json
import re
import sys
import warnings

# Consola no UTF-8 (Windows cp1252) o tuberías: reconfigurar ANTES de leer/imprimir (GOT-005).
for _s in (sys.stdin, sys.stdout, sys.stderr):
    try: _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception: pass  # noqa: BLE001 — sin reconfigure, ya leído o None (capsys, pythonw)

# Relaciones núcleo del adaptador (design.md, "Ontología"; CA-13). Ampliables por proyecto en
# `backends.graphiti.config.relations`, nunca sustituibles: sea cual sea la config, estas tres
# relaciones siempre están disponibles vía `add_triplet` (T-04).
RELACIONES_NUCLEO = ("SUPPORTED_BY", "SUPERSEDES", "CONTRADICTS")

# Tipos núcleo del adaptador (no vienen de ninguna categoría; los define esta ontología mínima,
# no la taxonomía del proyecto): `Knowledge` (una entrada aprobada) y `Evidence` (lo que la
# respalda). Ver `proponer_entity_types_yaml`.
TIPOS_NUCLEO = (
    ("Knowledge", "Nucleo del adaptador graphiti: conocimiento aprobado con procedencia"),
    ("Evidence", "Nucleo del adaptador graphiti: evidencia que respalda un Knowledge"),
)

# Tipo del servidor al que cae una categoría sin mapeo explícito en `entity_map` (design.md,
# `CA-13`): el tipo más genérico del servidor de referencia, nunca inventado por el plugin.
TIPO_POR_DEFECTO = "Document"


def tipo_entidad(categoria_key, config, default=TIPO_POR_DEFECTO):
    """Tipo de entidad EFECTIVO (del servidor) para una categoría de `taxonomy.json`, según
    `backends.graphiti.config.entity_map` (`config` es ese `config`, no la taxonomía entera).
    Sin mapeo para `categoria_key` (o sin `entity_map`/`config`), cae a `default`. `config` con un
    tipo distinto de `dict`/`None` (T-01-fix1 gap #12) NUNCA rompe la llamada: se avisa con
    `RuntimeWarning` y se cae a `default`, igual que sin mapeo."""
    if config is not None and not isinstance(config, dict):
        warnings.warn(
            f"tipo_entidad: 'config' debe ser un dict o None, recibido "
            f"{type(config).__name__}; se usa el default {default!r}",
            RuntimeWarning,
            stacklevel=2,
        )
        return default
    entity_map = (config or {}).get("entity_map") or {}
    if not isinstance(entity_map, dict):
        return default
    return entity_map.get(categoria_key, default)


def tipos_por_categoria(taxonomy, config):
    """`{categoria_key: tipo_efectivo}` para cada `categories[]` de `taxonomy` (el `taxonomy.json`
    completo del proyecto), resuelto contra `config` (el `backends.graphiti.config`)."""
    out = {}
    for cat in (taxonomy or {}).get("categories") or []:
        key = cat.get("key") if isinstance(cat, dict) else None
        if key:
            out[key] = tipo_entidad(key, config)
    return out


def relaciones_efectivas(config):
    """Núcleo (`RELACIONES_NUCLEO`) + las declaradas en `config["relations"]` que no estén ya en
    el núcleo, preservando el orden de declaración. `relations` ausente, no-lista o con elementos
    no-cadena se ignora (fail-safe: el núcleo sigue disponible, nunca se rompe la propuesta)."""
    extra = (config or {}).get("relations")
    if not isinstance(extra, list) or not all(isinstance(r, str) for r in extra):
        return RELACIONES_NUCLEO
    vistas = set(RELACIONES_NUCLEO)
    añadidas = []
    for r in extra:
        if r not in vistas:
            vistas.add(r)
            añadidas.append(r)
    return RELACIONES_NUCLEO + tuple(añadidas)


def _yaml_cadena(valor):
    """Escalar YAML entre comillas dobles a partir de una cadena Python — `json.dumps` de una
    cadena produce un escalar `"..."` válido tanto en JSON como en YAML (mismo subconjunto que
    usa `skills/api-contract/scripts/openapi-lint.py` para su fallback sin PyYAML)."""
    return json.dumps(valor, ensure_ascii=False)


def _titlecase_clave(key):
    """`TitleCase` de una `key` de categoría sin lista de dominio: divide por cualquier separador
    no alfanumérico (`_`, `-`, espacio, …) y capitaliza cada trozo — `"MULTI_WORD-key"` ->
    `"MultiWordKey"`. Determinista y sin diccionario de dominios (T-01-fix1 gap #2: el nombre no
    lo decide el código, lo decide `entity_map` o, en su ausencia, la propia `key`)."""
    partes = re.split(r"[^0-9A-Za-z]+", key or "")
    return "".join(parte[:1].upper() + parte[1:].lower() for parte in partes if parte)


def proponer_entity_types_yaml(taxonomy, config):
    """Bloque `entity_types:` (YAML válido, escrito a mano) para que el usuario lo pegue en el
    `config.yaml` de SU servidor Graphiti MCP (`knowledge-sync.py --backend graphiti
    --propose-config`, T-04/T-05 lo exponen como CLI; esta función solo calcula el texto).

    T-01-fix1 gap #2 (arbitraje del orquestador): UNA entrada por categoría de `taxonomy.json`,
    no por tipo efectivo agrupado — el nombre es `entity_map[key]` si el usuario lo declaró, o si
    no `_titlecase_clave(key)` (nunca un genérico compartido como `Document`, y sin lista de
    dominio en este módulo); dos categorías que resuelven al MISMO nombre (mapeadas explícitamente
    al mismo tipo) se deduplican en una sola entrada `name:`, con la descripción listando ambas
    categorías. Más los dos tipos núcleo del adaptador (`Knowledge`, `Evidence`). Orden
    determinista: alfabético por nombre, núcleo al final. `name:` y `description:` van SIEMPRE
    escapados con `_yaml_cadena` (gap #4): un nombre hostil (`"Doc: interno"`, con salto de línea,
    `"yes"`, cadena vacía, …) nunca rompe el YAML ni inyecta una entrada."""
    entity_map = (config or {}).get("entity_map")
    if not isinstance(entity_map, dict):
        entity_map = {}
    nombres_nucleo = {nombre for nombre, _ in TIPOS_NUCLEO}

    categorias_por_nombre = {}
    for cat in (taxonomy or {}).get("categories") or []:
        key = cat.get("key") if isinstance(cat, dict) else None
        if not key:
            continue
        nombre = entity_map[key] if key in entity_map else _titlecase_clave(key)
        if not isinstance(nombre, str) or nombre in nombres_nucleo:
            continue
        categorias_por_nombre.setdefault(nombre, []).append(key)

    lineas = ["entity_types:"]
    for nombre in sorted(categorias_por_nombre):
        categorias = ", ".join(sorted(categorias_por_nombre[nombre]))
        lineas.append(f"  - name: {_yaml_cadena(nombre)}")
        lineas.append(f"    description: {_yaml_cadena(f'Mapeado desde taxonomy.json: {categorias}')}")
    for nombre, descripcion in TIPOS_NUCLEO:
        lineas.append(f"  - name: {_yaml_cadena(nombre)}")
        lineas.append(f"    description: {_yaml_cadena(descripcion)}")
    return "\n".join(lineas) + "\n"


def cadena_supersedes(versiones):
    """`versiones`: lista de `{"knowledge_id": ...}` del MISMO linaje. **La vigencia es
    POSICIONAL**: la última posición de la lista es la vigente, las anteriores quedan
    invalidadas — este módulo no ordena nada; es responsabilidad del LLAMANTE entregar la lista
    ya ordenada ascendente por versión (nunca por orden lexicográfico de `knowledge_id`: `v1 <
    v10 < v2` marcaría vigente la `v2` en silencio; T-05 es quien construye esa lista ordenando
    por el campo `version`, no por el propio id).

    Devuelve `{"relaciones", "vigentes", "invalidados"}`:
      - `relaciones`: una `SUPERSEDES` por cada par consecutivo (`origen` = la más nueva,
        `destino` = la que sustituye), CA-11 — ninguna versión desaparece de aquí.
      - `vigentes`: solo la última versión (la que el router debe considerar viva).
      - `invalidados`: todas las anteriores (siguen existiendo como historia, pero no vigentes).
    `vigentes | invalidados` es siempre el conjunto completo de `knowledge_id` de entrada, y
    `vigentes ∩ invalidados` es siempre vacío: la historia se conserva entera, nunca se borra una
    versión (CA-11, `design.md`).

    T-01-fix1 gap #5/#12: entrada validada con errores explícitos (nunca `KeyError`/`AttributeError`
    de un `dict`/atributo ausente) — `versiones` debe ser `None` (equivale a `[]`) o una `list` de
    `dict` con `knowledge_id` como cadena no vacía; un `knowledge_id` REPETIDO en la misma cadena
    es un error explícito (evita `vigentes ∩ invalidados ≠ ∅` si aparece dos veces con posiciones
    distintas, y evita una `SUPERSEDES` con `origen == destino` si aparece dos veces seguidas)."""
    if versiones is None:
        versiones = []
    if not isinstance(versiones, list):
        raise TypeError(
            f"cadena_supersedes: 'versiones' debe ser una lista (o None), recibido "
            f"{type(versiones).__name__}"
        )
    ids = []
    for version in versiones:
        if not isinstance(version, dict):
            raise TypeError(
                f"cadena_supersedes: cada version debe ser un dict, recibido "
                f"{type(version).__name__}"
            )
        if "knowledge_id" not in version:
            raise ValueError("cadena_supersedes: cada version debe declarar 'knowledge_id'")
        knowledge_id = version["knowledge_id"]
        if not isinstance(knowledge_id, str) or not knowledge_id:
            raise ValueError("cadena_supersedes: 'knowledge_id' debe ser una cadena no vacia")
        ids.append(knowledge_id)

    if len(set(ids)) != len(ids):
        repetidos = sorted({kid for kid in ids if ids.count(kid) > 1})
        raise ValueError(
            f"cadena_supersedes: 'knowledge_id' repetido en la misma cadena: {repetidos}"
        )

    if not ids:
        return {"relaciones": [], "vigentes": set(), "invalidados": set()}
    relaciones = [
        {"relacion": "SUPERSEDES", "origen": nuevo, "destino": anterior}
        for anterior, nuevo in zip(ids, ids[1:])
    ]
    return {
        "relaciones": relaciones,
        "vigentes": {ids[-1]},
        "invalidados": set(ids[:-1]),
    }
