#!/usr/bin/env python3
"""
backends/graphiti_model.py — ontología derivada de `taxonomy.json` para el adaptador `graphiti`
(graphiti-memory T-02, ADR-018 enmienda 2026-09-17, CA-13 reformulado en la enmienda 2026-09-18;
T-01-fix1: gaps #2/#4/#5/#12 de la revisión de dos lentes, intento 1; T-02-fix2: gaps
#16/#18/#20/#22 de la revisión de dos lentes, intento 2).

No es el adaptador (`graphiti.py`, T-04): este módulo es PURO (sin red, sin disco, sin
`outbox.py`) y solo calcula datos a partir de la taxonomía y de `backends.graphiti.config`:

  - `tipo_entidad` / `tipos_por_categoria`: los tipos de entidad los fija el SERVIDOR Graphiti MCP
    (`config.yaml`), no el cliente. Este módulo NUNCA declara una lista de tipos de dominio: cada
    categoría de `taxonomy.json` se mapea a un tipo declarado en `backends.graphiti.config.entity_map`
    (por el usuario, contra los tipos reales de SU servidor); sin mapeo VÁLIDO (T-02-fix2 gap #20:
    un valor ausente, vacío/blanco o no-cadena NUNCA se usa como tipo — avisa con `RuntimeWarning`
    y cae al default), el default es `Document` (el tipo más genérico del servidor de referencia,
    `dockers/knowledge-graphs`).
  - `proponer_entity_types_yaml`: genera el bloque `entity_types` (YAML de mano, sin PyYAML —
    mismo criterio que `skills/api-contract/scripts/openapi-lint.py`) que el usuario puede pegar en
    el `config.yaml` de SU servidor: una entrada por CATEGORÍA de `taxonomy.json` (T-01-fix1 gap
    #2) — nombre `entity_map[key]` si es un valor VÁLIDO, si no `TitleCase` Unicode de la propia
    `key` (T-02-fix2 gap #18: NFKC + `[^\\W_]+`, nunca un genérico compartido tipo `Document`, sin
    lista de dominio en código); dos categorías que resuelven al mismo nombre EXPLÍCITO se
    deduplican en una sola entrada, pero dos que derivan IMPLÍCITAMENTE (sin mapeo) al mismo
    nombre, o cuya `key` no aporta ningún carácter alfanumérico, son un error explícito que pide
    declarar `entity_map` para esa `key` — más los dos tipos núcleo del adaptador, `Knowledge` y
    `Evidence`. `name:` va siempre escapado (gap #4).
  - `proponer_config`: la propuesta COMPLETA (T-02-fix2 gap #16) — el bloque `entity_types` de
    arriba Y el `entity_map` que hace esos tipos EFECTIVOS al pegarlo en
    `backends.graphiti.config.entity_map` del `taxonomy.json` del proyecto; sin aplicar ese
    `entity_map`, todo episodio sigue viajando como el genérico `Document`.
  - `relaciones_efectivas`: relaciones núcleo (`SUPPORTED_BY`, `SUPERSEDES`, `CONTRADICTS`, vía
    `add_triplet` en el adaptador) más las que el proyecto declare en `backends.graphiti.config.relations`,
    sin duplicar las del núcleo.
  - `cadena_supersedes`: la sucesión de versiones de un mismo linaje de `knowledge_id` como una
    cadena de relaciones `SUPERSEDES` — conserva TODAS las versiones (nunca borra ninguna) y marca
    cuál es la vigente (la última) y cuáles quedan invalidadas (todas las anteriores), CA-11.

Sin dependencias externas; solo stdlib (`json`, usado solo para escapar cadenas como escalares
YAML entre comillas dobles — un escalar `"..."` con `json.dumps` es YAML válido; `unicodedata`
para normalizar `key`s no-ASCII antes de derivarles un `TitleCase`).
"""
import json
import re
import sys
import unicodedata
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


def _valor_entity_map(entity_map, key, quien):
    """Valor de `entity_map[key]` SOLO si es una cadena no vacía (tras `strip()`); si la clave no
    está declarada, devuelve `None` en silencio (caso normal: "sin mapeo para esta categoría"). Si
    ESTÁ declarada pero es inválida (no-cadena, o cadena vacía/blanca), avisa con `RuntimeWarning`
    y la trata como si no estuviera — NUNCA deja pasar `None`/un número/una cadena vacía como si
    fuera un tipo de entidad real (T-02-fix2 gap #20; misma tolerancia en `tipo_entidad` y en la
    propuesta `proponer_entity_types_yaml`/`proponer_config`)."""
    if key not in entity_map:
        return None
    valor = entity_map[key]
    if isinstance(valor, str) and valor.strip():
        return valor
    warnings.warn(
        f"{quien}: entity_map[{key!r}] debe ser una cadena no vacía, recibido {valor!r}; "
        "se ignora el mapeo para esta categoría",
        RuntimeWarning,
        stacklevel=3,
    )
    return None


def tipo_entidad(categoria_key, config, default=TIPO_POR_DEFECTO):
    """Tipo de entidad EFECTIVO (del servidor) para una categoría de `taxonomy.json`, según
    `backends.graphiti.config.entity_map` (`config` es ese `config`, no la taxonomía entera).
    Sin mapeo VÁLIDO para `categoria_key` (o sin `entity_map`/`config`), cae a `default`. `config`
    con un tipo distinto de `dict`/`None` (T-01-fix1 gap #12) NUNCA rompe la llamada: se avisa con
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
    valor = _valor_entity_map(entity_map, categoria_key, "tipo_entidad")
    return valor if valor is not None else default


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
    """`TitleCase` Unicode de una `key` de categoría sin lista de dominio: normaliza a NFKC
    (T-02-fix2 gap #18: una `key` en forma NFD, p. ej. `"e" + acento combinante`, produce el
    mismo resultado que su forma NFC precompuesta) y extrae cada tramo de caracteres
    alfanuméricos Unicode (`[^\\W_]+` — cualquier separador no alfanumérico, `_`, `-`, espacio,
    puntuación… se descarta; `\\W`/`\\w` en Python 3 ya cubren letras no-ASCII como `á`/`日本`),
    capitalizando cada trozo — `"MULTI_WORD-key"` -> `"MultiWordKey"`, `"decisión"` ->
    `"Decisión"`, `"日本"` -> `"日本"` (sin mayúscula/minúscula en ese alfabeto, se conserva tal
    cual). Determinista y sin diccionario de dominios: el nombre no lo decide el código, lo decide
    `entity_map` o, en su ausencia, la propia `key`. Una `key` sin ningún carácter alfanumérico
    (p. ej. `"___"`) devuelve cadena vacía — el llamante decide qué hacer con eso."""
    normalizada = unicodedata.normalize("NFKC", key or "")
    partes = re.findall(r"[^\W_]+", normalizada, flags=re.UNICODE)
    return "".join(parte[:1].upper() + parte[1:].lower() for parte in partes)


def _config_a_entity_map(config, quien):
    """`config["entity_map"]` como `dict`, o `{}` si `config` no es un `dict`/`None` — nunca deja
    propagar un `AttributeError`/`TypeError` cuando `config` llega mal formado (T-02-fix2 gap
    #22: el endurecimiento de entrada de `tipo_entidad` no llegaba a `proponer_entity_types_yaml`;
    `config` lista o `entity_map` no-`dict` degradan con `RuntimeWarning`, igual que `tipo_entidad`
    con un `config` no-`dict`)."""
    if config is not None and not isinstance(config, dict):
        warnings.warn(
            f"{quien}: 'config' debe ser un dict o None, recibido {type(config).__name__}; "
            "se ignora el entity_map declarado",
            RuntimeWarning,
            stacklevel=3,
        )
        return {}
    entity_map = (config or {}).get("entity_map")
    return entity_map if isinstance(entity_map, dict) else {}


def _entity_map_propuesto(taxonomy, entity_map_declarado, quien):
    """`{categoria_key: nombre}` para TODAS las `categories[]` de `taxonomy`: el valor de
    `entity_map_declarado[key]` si es VÁLIDO (`_valor_entity_map`, gap #20), si no el `TitleCase`
    Unicode de la propia `key` (`_titlecase_clave`, gap #18) — nunca el genérico `Document` (T-01-
    fix1 gap #2). Una `key` no-cadena es un `ValueError` explícito (gap #22: antes, `key` entera o
    lista rompía con `TypeError`/`unhashable type`); un nombre derivado vacío (`key` sin ningún
    carácter alfanumérico) o que colisiona IMPLÍCITAMENTE con el de otra `key` (ninguna de las dos
    tiene mapeo explícito) también son un `ValueError` explícito — nunca una entrada vacía ni una
    fusión accidental de dos categorías distintas (gap #18)."""
    propuesto = {}
    derivados_por_nombre = {}
    for cat in (taxonomy or {}).get("categories") or []:
        key = cat.get("key") if isinstance(cat, dict) else None
        if not key:
            continue
        if not isinstance(key, str):
            raise ValueError(
                f"{quien}: 'key' de categoría debe ser una cadena, recibido "
                f"{type(key).__name__}: {key!r}"
            )
        nombre = _valor_entity_map(entity_map_declarado, key, quien)
        if nombre is None:
            nombre = _titlecase_clave(key)
            if not nombre:
                raise ValueError(
                    f"{quien}: la categoría '{key}' no deriva ningún nombre válido; "
                    f"declara `entity_map.{key}` explícitamente"
                )
            if nombre in derivados_por_nombre and derivados_por_nombre[nombre] != key:
                raise ValueError(
                    f"{quien}: las categorías '{derivados_por_nombre[nombre]}' y '{key}' derivan "
                    f"al mismo nombre '{nombre}' sin mapeo explícito; declara `entity_map.{key}` "
                    "para desambiguar"
                )
            derivados_por_nombre[nombre] = key
        propuesto[key] = nombre
    return propuesto


def proponer_entity_types_yaml(taxonomy, config):
    """Bloque `entity_types:` (YAML válido, escrito a mano) para que el usuario lo pegue en el
    `config.yaml` de SU servidor Graphiti MCP (`knowledge-sync.py --backend graphiti
    --propose-config`, T-04/T-05 lo exponen como CLI; esta función solo calcula el texto).

    T-01-fix1 gap #2 (arbitraje del orquestador): UNA entrada por categoría de `taxonomy.json`,
    no por tipo efectivo agrupado — el nombre es `entity_map[key]` si el usuario lo declaró con un
    valor VÁLIDO (gap #20), o si no `_titlecase_clave(key)` (nunca un genérico compartido como
    `Document`, y sin lista de dominio en este módulo); dos categorías que resuelven al MISMO
    nombre EXPLÍCITO (mapeadas a mano al mismo tipo) se deduplican en una sola entrada `name:`, con
    la descripción listando ambas categorías — dos que colisionan de forma IMPLÍCITA son un error
    (gap #18, ver `_entity_map_propuesto`). Más los dos tipos núcleo del adaptador (`Knowledge`,
    `Evidence`). Orden determinista: alfabético por nombre, núcleo al final. `name:` y
    `description:` van SIEMPRE escapados con `_yaml_cadena` (gap #4): un nombre hostil (`"Doc:
    interno"`, con salto de línea, `"yes"`, …) nunca rompe el YAML ni inyecta una entrada."""
    entity_map = _config_a_entity_map(config, "proponer_entity_types_yaml")
    entity_map_efectivo = _entity_map_propuesto(taxonomy, entity_map, "proponer_entity_types_yaml")
    nombres_nucleo = {nombre for nombre, _ in TIPOS_NUCLEO}

    categorias_por_nombre = {}
    for key, nombre in entity_map_efectivo.items():
        if nombre in nombres_nucleo:
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


def proponer_config(taxonomy, config):
    """Propuesta COMPLETA para adoptar tipos de entidad por categoría (T-02-fix2 gap #16): el
    bloque `entity_types` de arriba (`proponer_entity_types_yaml`) para el `config.yaml` del
    SERVIDOR Graphiti Y el bloque `entity_map` que hay que pegar en
    `backends.graphiti.config.entity_map` del `taxonomy.json` del proyecto para que esos tipos
    sean EFECTIVOS — sin aplicar el `entity_map` devuelto aquí, `tipo_entidad`/`tipos_por_categoria`
    seguirían etiquetando toda categoría sin mapeo explícito como el genérico `Document`: los
    `entity_types` propuestos existirían en el servidor, pero ningún episodio los usaría.

    Devuelve `{"entity_types_yaml": str, "entity_map": {categoria: nombre}, "nota": str}`.
    Aplicar el `entity_map` devuelto (p. ej. `tipos_por_categoria(taxonomy, {"entity_map":
    resultado["entity_map"]})`) da EXACTAMENTE los nombres propuestos, categoría por categoría —
    ver `test_proponer_config_aplicar_entity_map_hace_tipos_por_categoria_igual_a_lo_propuesto`."""
    entity_map_declarado = _config_a_entity_map(config, "proponer_config")
    entity_map_propuesto = _entity_map_propuesto(taxonomy, entity_map_declarado, "proponer_config")
    entity_types_yaml = proponer_entity_types_yaml(taxonomy, {"entity_map": entity_map_propuesto})
    return {
        "entity_types_yaml": entity_types_yaml,
        "entity_map": entity_map_propuesto,
        "nota": (
            "Sin aplicar este `entity_map` en `backends.graphiti.config` del proyecto, todos "
            "los episodios viajan como el tipo genérico `Document` (los `entity_types` de "
            "arriba no llegan a usarse)."
        ),
    }


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
